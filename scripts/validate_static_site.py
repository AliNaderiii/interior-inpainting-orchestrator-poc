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
    ".jpg",
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
        "studio.html",
        "studio.css",
        "studio.js",
        "spatial.html",
        "spatial.css",
        "spatial.js",
        "cinematic.css",
        "cinematic.js",
        ".nojekyll",
        "assets/social-preview.png",
        "assets/spatial-lounge-source.png",
        "assets/spatial-lounge-occlusion.png",
        "assets/spatial-hero-carpet.png",
        "assets/spatial-product-card.png",
        "assets/cinematic-lounge-concept.jpg",
        "assets/cinematic-lounge-analysis.jpg",
    )
    for name in required:
        if not (SITE / name).is_file():
            errors.append(f"Missing required file: site/{name}")

    for path in SITE.rglob("*"):
        if path.is_file() and path.suffix.lower() not in ALLOWED_SUFFIXES:
            errors.append(f"Unexpected artifact type: {path.relative_to(ROOT)}")
        if path.name.lower() in {".env", "id_rsa", "id_ed25519"}:
            errors.append(f"Sensitive filename in artifact: {path.relative_to(ROOT)}")

    csp_directives = (
        "connect-src 'none'",
        "object-src 'none'",
        "base-uri 'none'",
        "form-action 'none'",
    )
    for html_path in SITE.glob("*.html"):
        html = html_path.read_text(encoding="utf-8")
        parser = SiteParser()
        parser.feed(html)
        for directive in csp_directives:
            if directive not in html:
                errors.append(f"Missing CSP directive in {html_path.name}: {directive}")
        if "frame-ancestors" in html:
            errors.append(
                "Ineffective frame-ancestors directive must not be delivered by meta in "
                f"{html_path.name}"
            )
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
        "form-action 'none'",
    ):
        if directive not in index:
            errors.append(f"Missing CSP directive: {directive}")
    for claim_boundary in (
        "NON-AI LOCAL SIMULATION",
        "not generative quality",
        "Client-owned OpenAPI and JSON Schemas",
        "POST /poc/v2/jobs",
        "Enter Spatial Studio",
        'href="spatial.html"',
        "SCROLL-DIRECTED SPATIAL STORY",
        "Illustrative concept frame",
    ):
        if claim_boundary not in index:
            errors.append(f"Missing scope language: {claim_boundary}")

    pages_documentation = (ROOT / "docs" / "GITHUB_PAGES.md").read_text(encoding="utf-8")
    if "cannot enforce `frame-ancestors`" not in pages_documentation:
        errors.append("Missing honest documentation of the GitHub Pages frame-policy limitation")

    javascript = (SITE / "app.js").read_text(encoding="utf-8")
    studio_javascript = (SITE / "studio.js").read_text(encoding="utf-8")
    spatial_javascript = (SITE / "spatial.js").read_text(encoding="utf-8")
    spatial_html = (SITE / "spatial.html").read_text(encoding="utf-8")
    spatial_css = (SITE / "spatial.css").read_text(encoding="utf-8")
    cinematic_javascript = (SITE / "cinematic.js").read_text(encoding="utf-8")
    cinematic_css = (SITE / "cinematic.css").read_text(encoding="utf-8")
    for javascript_path in SITE.glob("*.js"):
        browser_code = javascript_path.read_text(encoding="utf-8")
        for network_api in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon("):
            if network_api in browser_code:
                errors.append(
                    f"Forbidden browser network API in {javascript_path.name}: {network_api}"
                )
    for client_limit in ("MAX_BROWSER_BYTES", "MAX_BROWSER_PIXELS", "SUPPORTED_IMAGE_TYPES"):
        if client_limit not in javascript:
            errors.append(f"Missing browser resource control: {client_limit}")
    for studio_limit in ("MAX_BYTES", "MAX_PIXELS", "SUPPORTED_TYPES"):
        if studio_limit not in studio_javascript:
            errors.append(f"Missing studio resource control: {studio_limit}")
    for spatial_limit in (
        "MAX_PRODUCT_BYTES",
        "MAX_PRODUCT_PIXELS",
        "URL.revokeObjectURL",
        "lastProtectedDrift",
    ):
        if spatial_limit not in spatial_javascript:
            errors.append(f"Missing spatial resource/proof control: {spatial_limit}")

    for marker in (
        "Catalog-faithful placement",
        "Generative concept",
        "HERO PLANE · EDITABLE",
        "No provider call · no upload transmission",
        "does not claim live model quality",
        "Reference boundary",
    ):
        if marker not in spatial_html:
            errors.append(f"Missing Spatial Studio boundary/workflow marker: {marker}")

    for fallback in (
        "@supports not ((backdrop-filter:",
        "prefers-reduced-transparency",
        "prefers-reduced-motion",
        "prefers-contrast: more",
        'html[data-transparency="reduced"]',
    ):
        if fallback not in spatial_css:
            errors.append(f"Missing Luminous Glass fallback: {fallback}")
    if "transition: backdrop-filter" in spatial_css or "transition: blur" in spatial_css:
        errors.append("Luminous Glass must not animate blur or backdrop-filter")

    for cinematic_control in (
        "requestAnimationFrame",
        'matchMedia("(prefers-reduced-motion: reduce)")',
        "data-cinematic-active",
        "passive: true",
    ):
        if cinematic_control not in cinematic_javascript:
            errors.append(f"Missing cinematic motion/performance control: {cinematic_control}")
    for cinematic_fallback in (
        "prefers-reduced-motion: reduce",
        "prefers-reduced-transparency: reduce",
        "prefers-contrast: more",
        "@supports not ((backdrop-filter:",
    ):
        if cinematic_fallback not in cinematic_css:
            errors.append(f"Missing cinematic accessibility fallback: {cinematic_fallback}")
    if "infinite" in cinematic_css or "autoplay" in index:
        errors.append("Cinematic showcase must not contain unbounded motion or autoplay media")
    if "transition: backdrop-filter" in cinematic_css or "transition: blur" in cinematic_css:
        errors.append("Cinematic showcase must not animate blur or backdrop-filter")

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
    if (SITE / "assets" / "social-preview.png").stat().st_size > 500_000:
        errors.append("Social preview exceeds 500 KB performance budget")

    spatial_dimensions = {
        name: read_png_dimensions(SITE / "assets" / name)
        for name in (
            "spatial-lounge-source.png",
            "spatial-lounge-occlusion.png",
            "spatial-hero-carpet.png",
            "spatial-product-card.png",
        )
    }
    expected_spatial_dimensions = {
        "spatial-lounge-source.png": (1200, 800),
        "spatial-lounge-occlusion.png": (1200, 800),
        "spatial-hero-carpet.png": (720, 440),
        "spatial-product-card.png": (1400, 900),
    }
    if spatial_dimensions != expected_spatial_dimensions:
        errors.append(f"Spatial asset geometry mismatch: {spatial_dimensions}")

    for name in ("cinematic-lounge-concept.jpg", "cinematic-lounge-analysis.jpg"):
        cinematic_path = SITE / "assets" / name
        cinematic_bytes = cinematic_path.read_bytes()
        if not cinematic_bytes.startswith(b"\xff\xd8"):
            errors.append(f"Invalid cinematic JPEG signature: {name}")
        if len(cinematic_bytes) > 500_000:
            errors.append(f"Cinematic frame exceeds 500 KB performance budget: {name}")

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
