# Changelog

All notable changes to this reference implementation are recorded here. The project follows semantic versioning for its public PoC surface; a version does not imply compatibility with an undisclosed client contract.

## [Unreleased] — 0.3.0 candidate

### Added

- Full-screen cinematic landing hero and reversible `Atmosphere → Analyze → Place → Prove` 2.5D scrollytelling sequence.
- Two original aligned Hospitality Lounge frames for concept atmosphere and spatial-analysis transitions, plus a reproducible cinematic Open Graph preview.
- Scroll-linked camera, scene crossfade, lock map, product-plane transition and proof HUD using local assets, CSS perspective and `requestAnimationFrame` scheduling.
- Static no-JavaScript and reduced-motion chapter flows, reduced-transparency solids, increased-contrast styling and keyboard-safe mobile-menu dismissal.
- Five-stage Spatial Design Studio: `Brief → Scene Locks → Hero Placement → Variant Review → Handoff`.
- Original **Luminous Glass** control-layer design system with solid fallback, reduced transparency, reduced motion and increased contrast states.
- Clean-room synthetic Hospitality Lounge and Contour 01 hero-carpet assets generated from a repository script.
- Browser-local four-corner perspective placement, bounded local product upload, contact shadow, foreground occlusion order and keyboard-accessible coordinate controls.
- Controlled three-direction review set, selected-output PNG, contact sheet and project-local JSON proof manifest exports.
- Provisional `SpatialDesignBrief` compiler at `POST /poc/v3/briefs/compile`.
- Deterministic transform-only placement preview at `POST /poc/v3/placements/preview`.
- Placement geometry validation, alpha compositing, proof headers and exact authoritative restoration outside the destination plane.
- Exported candidate OpenAPI document at `docs/openapi-v0.3.0.json` plus `docs/API_V3.md`.

### Preserved

- All v1 and v2 routes and behavior.
- Exact protected-pixel restoration invariant.
- No-cost deterministic default provider and optional BFL adapter.
- Browser showcase no-network runtime boundary.
- Prior Visual Restyle Studio as a focused mask-authoring proof.

### Boundaries

- Cinematic lounge frames are illustrative art-direction assets, not client work, live-model output or deterministic evidence.
- The cinematic landing uses no autoplay video, WebGL dependency, third-party runtime, analytics or browser network call.
- The Spatial Studio browser renders are deterministic reference evidence, not AI model output.
- Generative Concept and Catalog-faithful Placement are separate modes and claims.
- “Catalog-faithful” means immutable source raster plus allowed geometric compositing in this PoC; it is not photometric, manufacturing or catalog certification.
- Automatic depth, segmentation, provider quality, client contract compatibility, production queues and durable provenance remain open gates.
- No release, tag or deployment may be created while Git metadata and hosted release gates are unavailable.

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
