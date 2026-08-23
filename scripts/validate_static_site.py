from __future__ import annotations

import json
import re
import struct
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PROJECT_PREFIX = "/interior-inpainting-orchestrator-poc/"
ALLOWED_SUFFIXES = {
    "",
    ".css",
    ".html",
    ".js",
    ".json",
    ".png",
    ".svg",
    ".txt",
    ".webmanifest",
    ".xml",
}


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []
        self.inline_violation = False
        self._inside_inline_script = False
        self._inside_style = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        self.references.extend(value for name in ("href", "src") if (value := attributes.get(name)))
        if "style" in attributes or any(name.lower().startswith("on") for name, _ in attrs):
            self.inline_violation = True
        if tag == "script" and "src" not in attributes:
            self._inside_inline_script = True
        if tag == "style":
            self._inside_style = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._inside_inline_script = False
        if tag == "style":
            self._inside_style = False

    def handle_data(self, data: str) -> None:
        if data.strip() and (self._inside_inline_script or self._inside_style):
            self.inline_violation = True


def resolve_local_reference(reference: str, html_path: Path) -> Path | None:
    split = urlsplit(reference)
    if split.scheme or split.netloc or reference.startswith(("#", "mailto:")):
        return None
    path = unquote(split.path)
    if not path:
        return None
    if path.startswith(PROJECT_PREFIX):
        return SITE / path.removeprefix(PROJECT_PREFIX)
    if path.startswith("/"):
        return SITE / path.removeprefix("/")
    return html_path.parent / path


def read_png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Invalid PNG signature: {path}")
    return struct.unpack(">II", data[16:24])


def validate() -> list[str]:
    errors: list[str] = []
    required = (
        "index.html",
        "styles.css",
        "app.js",
        ".nojekyll",
        "assets/social-preview.png",
    )
    for name in required:
        if not (SITE / name).is_file():
            errors.append(f"Missing required file: site/{name}")

    for path in SITE.rglob("*"):
        if path.is_file() and path.suffix.lower() not in ALLOWED_SUFFIXES:
            errors.append(f"Unexpected artifact type: {path.relative_to(ROOT)}")
        if path.name.lower() in {".env", "id_rsa", "id_ed25519"}:
            errors.append(f"Sensitive filename in artifact: {path.relative_to(ROOT)}")

    for html_path in SITE.glob("*.html"):
        parser = SiteParser()
        parser.feed(html_path.read_text(encoding="utf-8"))
        if parser.inline_violation:
            errors.append(f"Inline script/style/event handler in {html_path.name}")
        for reference in parser.references:
            local_path = resolve_local_reference(reference, html_path)
            if local_path is not None and not local_path.resolve().exists():
                errors.append(f"Broken local reference in {html_path.name}: {reference}")

    index = (SITE / "index.html").read_text(encoding="utf-8")
    for directive in (
        "connect-src 'none'",
        "object-src 'none'",
        "base-uri 'none'",
        "frame-ancestors 'none'",
    ):
        if directive not in index:
            errors.append(f"Missing CSP directive: {directive}")
    for claim_boundary in (
        "NON-AI LOCAL SIMULATION",
        "not generative quality",
        "Client-owned OpenAPI and JSON Schemas",
    ):
        if claim_boundary not in index:
            errors.append(f"Missing scope language: {claim_boundary}")

    javascript = (SITE / "app.js").read_text(encoding="utf-8")
    for network_api in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon("):
        if network_api in javascript:
            errors.append(f"Forbidden browser network API: {network_api}")
    for client_limit in ("MAX_BROWSER_BYTES", "MAX_BROWSER_PIXELS", "SUPPORTED_IMAGE_TYPES"):
        if client_limit not in javascript:
            errors.append(f"Missing browser resource control: {client_limit}")

    for workflow_name in ("ci.yml", "pages.yml"):
        workflow = (ROOT / ".github" / "workflows" / workflow_name).read_text(encoding="utf-8")
        action_references = re.findall(r"uses:\s+actions/[\w-]+@([^\s]+)", workflow)
        if not action_references or not all(
            re.fullmatch(r"[0-9a-f]{40}", reference) for reference in action_references
        ):
            errors.append(
                f"Every official action in {workflow_name} must be pinned to a full commit SHA"
            )

    manifest = json.loads((SITE / "manifest.webmanifest").read_text(encoding="utf-8"))
    if manifest.get("start_url") != "./":
        errors.append("Manifest start_url must remain project-relative")

    evidence_dimensions = {
        read_png_dimensions(SITE / "assets" / name)
        for name in (
            "before-synthetic.png",
            "mask-white-edit-synthetic.png",
            "after-deterministic-demo-not-ai.png",
        )
    }
    if evidence_dimensions != {(960, 640)}:
        errors.append(f"Evidence image geometry mismatch: {evidence_dimensions}")
    social_dimensions = read_png_dimensions(SITE / "assets" / "social-preview.png")
    if social_dimensions != (1200, 630):
        errors.append(f"Social preview geometry mismatch: {social_dimensions}")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Static showcase validation: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Static showcase validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
