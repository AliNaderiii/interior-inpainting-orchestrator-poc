# Phase 02 — Job API, Style Intent and Visual Restyle Studio

**Date:** 2026-08-23

**Repository:** `interior-inpainting-orchestrator-poc`

**Status:** `PASS_LOCAL / RELEASE_CANDIDATE`

**Version:** `0.2.0`

## Executive result

A new vertical slice was implemented entirely inside this repository. It adds a bounded job-based API alongside the existing synchronous route, a deterministic and explainable Style Intent compiler, and a browser-local Visual Restyle Studio for product/workflow evidence.

All local quality, API, static-site and supported-Python matrix gates pass. Public Git/Actions/Pages status is a separate release gate and is not implied by this local report. No file, workflow, branch, setting or commit in `Smart-Interior-Decor-Recommendation-Platform` was changed.

## Scope delivered

### Backend contract

- Preserved `POST /poc/v1/inpaint` for synchronous compatibility.
- Added `POST /poc/v2/intents/compile`.
- Added `POST /poc/v2/jobs` with `202 Accepted`.
- Added `GET /poc/v2/jobs/{job_id}`.
- Added `GET /poc/v2/jobs/{job_id}/result`.
- Added `GET /health/ready` while preserving `/health/live`.
- Added `Location`, `Retry-After`, `Cache-Control: no-store` and request-ID response behavior.
- Exported and drift-tested `docs/openapi-v0.2.0.json`.

### Style Intent and explainability

- Controlled style, room type, palette, material and semantic-preservation fields.
- Fail-closed Pydantic validation with unknown fields forbidden.
- Deterministic `intent-v1` prompt compiler.
- Ordered prompt segments for explanation.
- Canonical SHA-256 intent identity.
- Explicit statement that semantic prompt instructions do not replace mask authority.

### Bounded job lifecycle

- Lifecycle: `queued → running → succeeded | failed → expired`.
- Bounded record capacity and concurrent execution.
- Configurable TTL.
- Idempotent replay when a key and payload fingerprint match.
- `409 IdempotencyConflictError` when the same key is reused for another payload.
- Safe domain failures and redacted unexpected failures.
- Shutdown cancellation.
- Deliberately in-memory and non-durable implementation.

### Visual Restyle Studio

Added `site/studio.html`, `site/studio.css` and `site/studio.js` as a clean-room, dependency-free interface:

1. **Design intent:** six controlled directions, room, palette, bounded materials, semantic preservation and notes.
2. **Authorized zone:** source upload, aligned-mask import, paint/erase tools, brush control and mask-coverage evidence.
3. **Run and inspect:** API-shaped payload, local lifecycle simulation, deterministic output, proof metrics and downloadable PNG.

The browser compiler follows the same prompt-segment order and canonical intent hashing semantics as backend `intent-v1`. The output renderer applies an exact final outside-mask restore and reports protected-pixel drift.

## Evidence and claim boundaries

Three evidence classes remain separate:

1. **Repository orchestration evidence:** automated API, lifecycle, imaging and provider-protocol tests.
2. **Browser deterministic evidence:** local, non-AI workflow and protected-pixel demonstration.
3. **Real-provider evidence:** not executed in this phase; requires approved BFL credentials, region/model, budget and acceptance criteria.

The Studio does not contact FastAPI, BFL or any external service. It is not presented as a generative-quality benchmark.

## Security controls reviewed

- `connect-src 'none'` on all HTML entry points.
- Same-origin static assets only; no third-party JavaScript, CSS, font, analytics or tracking.
- No inline scripts, inline styles or event-handler attributes.
- Browser inputs restricted to PNG/JPEG/WebP, 12 MB and four megapixels.
- API encoded-byte and decoded-pixel limits retained.
- Job records, concurrency and TTL bounded.
- Provider result URLs remain HTTPS-only and host-allowlisted.
- GitHub Actions remain least-privilege and official actions stay pinned to full commit SHAs.
- Project-scoped `pip-audit .` found no known vulnerabilities.
- Targeted credential-pattern review found one intentional `test-secret` mock-provider fixture and zero actionable credential candidates; the Pages artifact contains zero symlinks.

## Automated validation

Machine-readable output is recorded in [`phase-02-validation.txt`](phase-02-validation.txt).

| Gate | Result |
|---|---:|
| Ruff format | PASS — 34 files |
| Ruff lint | PASS |
| Strict mypy | PASS — 13 source files |
| pytest on CPython 3.11.16 | PASS — 24 tests |
| pytest on CPython 3.12.14 | PASS — 24 tests |
| pytest on CPython 3.13.14 | PASS — 24 tests |
| Static showcase validator | PASS |
| JavaScript syntax: `app.js` | PASS |
| JavaScript syntax: `studio.js` | PASS |
| OpenAPI export drift | PASS, enforced by test |
| Project dependency audit | PASS — no known vulnerabilities |
| Local API v2 runtime smoke | PASS |
| Static HTTP asset smoke | PASS |

The API runtime smoke verified liveness, readiness, Style Intent compilation, `202` job acceptance, successful polling, PNG retrieval and idempotent replay against the deterministic provider.

## Main files added or changed

- `src/inpainting_poc/intent.py`
- `src/inpainting_poc/jobs.py`
- `src/inpainting_poc/api.py`
- `src/inpainting_poc/models.py`
- `src/inpainting_poc/errors.py`
- `src/inpainting_poc/config.py`
- `tests/test_intent.py`
- `tests/test_jobs.py`
- `tests/test_api.py`
- `tests/test_openapi.py`
- `site/studio.html`
- `site/studio.css`
- `site/studio.js`
- `docs/API_V2.md`
- `docs/openapi-v0.2.0.json`
- `scripts/export_openapi.py`

## Open gates before public release

- Perform a manual visual/accessibility review of Studio on desktop and mobile browsers.
- Review the complete repository diff in an authenticated Git worktree.
- Create and push one independently reviewable phase commit.
- Require all public CI matrix jobs and Pages deployment jobs to pass.
- Smoke-test the hosted `studio.html` and confirm the no-network boundary in browser developer tools.
- Do not claim production durability, client-contract compatibility or real-provider quality without their separate gates.

## Rollback

The new surface is isolated by version and file boundary:

- API consumers can continue using `/poc/v1/inpaint`.
- The Studio is a separate static entry point linked from the existing showcase.
- Reverting the phase commit would remove v2 and Studio changes together without changing any other repository.
