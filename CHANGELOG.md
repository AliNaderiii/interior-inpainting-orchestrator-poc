# Changelog

All notable changes to this reference implementation are recorded here. The project follows semantic versioning for its public PoC surface; a version does not imply compatibility with an undisclosed client contract.

## [0.2.0] — 2026-08-23

### Added

- Bounded, in-memory job API:
  - `POST /poc/v2/jobs`
  - `GET /poc/v2/jobs/{job_id}`
  - `GET /poc/v2/jobs/{job_id}/result`
- Deterministic `StyleIntent` compiler at `POST /poc/v2/intents/compile`.
- Job idempotency, payload-conflict detection, bounded concurrency, record capacity and TTL.
- Readiness endpoint at `GET /health/ready`.
- Exported and drift-tested OpenAPI document at `docs/openapi-v0.2.0.json`.
- Visual Restyle Studio with `Intent → Mask → Preview → Verify` workflow.
- Browser-local mask paint/erase tools, API-shaped payload explanation and deterministic job simulation.
- API, compiler, lifecycle, OpenAPI and expanded static-security tests.

### Preserved

- Synchronous compatibility route at `POST /poc/v1/inpaint`.
- Exact restoration of original pixels outside the aligned hard mask.
- Provider-neutral orchestration and opt-in BFL adapter.
- No-cost deterministic provider as the default test mode.

### Security and operational boundaries

- Browser Studio has no API/provider calls and does not transmit uploaded files.
- GitHub Pages entry points enforce a no-network runtime through meta CSP.
- The ineffective meta-delivered `frame-ancestors` directive was removed and the hosting limitation documented explicitly.
- The job manager is deliberately non-durable; production queue, persistence, auth, rate limiting and observability remain separate gates.
- Live provider quality remains unevaluated without approved credentials, region, budget and acceptance criteria.

### Verification

- `24` tests passed on Python 3.11, 3.12 and 3.13 in GitHub Actions run `32639806882`.
- GitHub Pages validation and deployment passed in run `32639806902`.
- Hosted static artifacts were byte-identical to commit `12b2b9f48ec06be7448afd2385f2e925e445abf9` before the release-hardening follow-up.
- Hosted Chromium smoke completed the Studio workflow with `534,801` protected pixels and zero protected-pixel drift.

## [0.1.0] — 2026-08-23

### Added

- Initial FastAPI reference PoC and synchronous inpainting route.
- Deterministic demo provider and mocked BFL FLUX.1 Fill protocol adapter.
- Image/mask normalization, bounded decoding and exact protected-pixel compositing.
- Python 3.11–3.13 CI matrix, security documentation and synthetic evidence.
- Dependency-free GitHub Pages technical showcase and Boundary Lab.
