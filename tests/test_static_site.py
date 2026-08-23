from __future__ import annotations

import json
import re
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PROJECT_PREFIX = "/interior-inpainting-orchestrator-poc/"


class ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []
        self.inline_scripts = 0
        self.inline_styles = 0
        self.event_handlers: list[str] = []
        self._inside_script_without_src = False
        self._inside_style = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        for name in ("href", "src"):
            if value := attributes.get(name):
                self.references.append(value)
        self.event_handlers.extend(name for name, _ in attrs if name.lower().startswith("on"))
        if attributes.get("style") is not None:
            self.inline_styles += 1
        if tag == "script" and "src" not in attributes:
            self._inside_script_without_src = True
        if tag == "style":
            self._inside_style = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._inside_script_without_src = False
        if tag == "style":
            self._inside_style = False

    def handle_data(self, data: str) -> None:
        if self._inside_script_without_src and data.strip():
            self.inline_scripts += 1
        if self._inside_style and data.strip():
            self.inline_styles += 1


def _local_path(reference: str, html_path: Path) -> Path | None:
    split = urlsplit(reference)
    if split.scheme or split.netloc or reference.startswith(("#", "mailto:")):
        return None
    decoded = unquote(split.path)
    if not decoded:
        return None
    if decoded.startswith(PROJECT_PREFIX):
        return SITE / decoded.removeprefix(PROJECT_PREFIX)
    if decoded.startswith("/"):
        return SITE / decoded.removeprefix("/")
    return html_path.parent / decoded


def test_static_pages_have_resolvable_local_references() -> None:
    for html_path in SITE.glob("*.html"):
        parser = ReferenceParser()
        parser.feed(html_path.read_text(encoding="utf-8"))
        missing = [
            reference
            for reference in parser.references
            if (path := _local_path(reference, html_path)) is not None
            and not path.resolve().exists()
        ]
        assert not missing, f"Missing references in {html_path.name}: {missing}"


def test_site_enforces_a_no_network_runtime_boundary() -> None:
    for html_path in SITE.glob("*.html"):
        html = html_path.read_text(encoding="utf-8")
        parser = ReferenceParser()
        parser.feed(html)
        assert "connect-src 'none'" in html
        assert "object-src 'none'" in html
        assert "base-uri 'none'" in html
        assert "form-action 'none'" in html
        assert "frame-ancestors" not in html
        assert parser.inline_scripts == 0
        assert parser.inline_styles == 0
        assert not parser.event_handlers

    pages_documentation = (ROOT / "docs" / "GITHUB_PAGES.md").read_text(encoding="utf-8")
    assert "cannot enforce `frame-ancestors`" in pages_documentation

    forbidden_network_apis = ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon(")
    for javascript_path in SITE.glob("*.js"):
        javascript = javascript_path.read_text(encoding="utf-8")
        assert not any(api in javascript for api in forbidden_network_apis)

    app_javascript = (SITE / "app.js").read_text(encoding="utf-8")
    studio_javascript = (SITE / "studio.js").read_text(encoding="utf-8")
    assert "MAX_BROWSER_BYTES" in app_javascript
    assert "MAX_BROWSER_PIXELS" in app_javascript
    assert 'new Set(["image/png", "image/jpeg", "image/webp"])' in app_javascript
    assert "MAX_BYTES" in studio_javascript
    assert "MAX_PIXELS" in studio_javascript
    assert 'new Set(["image/png", "image/jpeg", "image/webp"])' in studio_javascript


def test_showcase_assets_and_honest_scope_are_preserved() -> None:
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert "NON-AI LOCAL SIMULATION" in html
    assert "not generative quality" in html
    assert "approved credentials, region, budget, and acceptance criteria" in html
    assert "Client-owned OpenAPI and JSON Schemas" in html
    assert "POST /poc/v2/jobs" in html
    assert 'href="studio.html"' in html

    asset_names = (
        "before-synthetic.png",
        "mask-white-edit-synthetic.png",
        "after-deterministic-demo-not-ai.png",
    )
    for name in asset_names:
        site_asset = SITE / "assets" / name
        documentation_asset = ROOT / "docs" / "assets" / name
        assert (
            sha256(site_asset.read_bytes()).digest()
            == sha256(documentation_asset.read_bytes()).digest()
        )

    with (
        Image.open(SITE / "assets" / asset_names[0]) as source,
        Image.open(SITE / "assets" / asset_names[1]) as mask,
        Image.open(SITE / "assets" / asset_names[2]) as result,
    ):
        assert source.size == mask.size == result.size == (960, 640)


def test_pages_manifest_and_workflow_are_hardened() -> None:
    manifest = json.loads((SITE / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["start_url"] == "./"
    assert manifest["icons"][0]["src"] == "icons/favicon.svg"
    assert (SITE / ".nojekyll").exists()
    social_preview = SITE / "assets" / "social-preview.png"
    assert social_preview.is_file()
    with Image.open(social_preview) as image:
        assert image.size == (1200, 630)

    workflows: dict[str, str] = {}
    for name in ("ci.yml", "pages.yml"):
        workflow = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        workflows[name] = workflow
        action_references = re.findall(r"uses:\s+actions/[\w-]+@([^\s]+)", workflow)
        assert action_references
        assert all(re.fullmatch(r"[0-9a-f]{40}", reference) for reference in action_references)
        assert "persist-credentials: false" in workflow

    assert "pages: write" in workflows["pages.yml"]
    assert "id-token: write" in workflows["pages.yml"]
