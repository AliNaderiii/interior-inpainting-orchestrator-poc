import json
from pathlib import Path

from inpainting_poc.api import app

ROOT = Path(__file__).resolve().parents[1]
EXPORTED = ROOT / "docs" / "openapi-v0.2.0.json"


def test_exported_openapi_matches_runtime_schema() -> None:
    assert json.loads(EXPORTED.read_text(encoding="utf-8")) == app.openapi()


def test_openapi_exposes_versioned_job_and_compatibility_contracts() -> None:
    schema = app.openapi()
    paths = schema["paths"]
    assert schema["info"]["version"] == "0.2.0"
    assert {
        "/poc/v1/inpaint",
        "/poc/v2/intents/compile",
        "/poc/v2/jobs",
        "/poc/v2/jobs/{job_id}",
        "/poc/v2/jobs/{job_id}/result",
        "/health/live",
        "/health/ready",
    }.issubset(paths)

    create_responses = paths["/poc/v2/jobs"]["post"]["responses"]
    assert {"202", "409", "422", "503"}.issubset(create_responses)
    result_content = paths["/poc/v2/jobs/{job_id}/result"]["get"]["responses"]["200"]["content"]
    assert "image/png" in result_content
