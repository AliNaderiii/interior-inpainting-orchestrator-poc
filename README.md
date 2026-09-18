# Interior Inpainting Orchestrator — Deterministic Image Processing Backend

[![CI](https://github.com/AliNaderiii/interior-inpainting-orchestrator-poc/actions/workflows/ci.yml/badge.svg)](https://github.com/AliNaderiii/interior-inpainting-orchestrator-poc/actions/workflows/ci.yml)
[![GitHub Pages](https://github.com/AliNaderiii/interior-inpainting-orchestrator-poc/actions/workflows/pages.yml/badge.svg)](https://github.com/AliNaderiii/interior-inpainting-orchestrator-poc/actions/workflows/pages.yml)
[![Python](https://img.shields.io/badge/Python-3.11--3.13-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

![Interior Inpainting Orchestrator — controlled edits and verifiable boundaries](site/assets/social-preview.png)

A focused, security-conscious reference implementation demonstrating the deterministic portion of an interior-staging inpainting backend:

- FastAPI boundary (provisional PoC contract only)
- Pydantic v2 request metadata
- Pillow/OpenCV/NumPy image normalization and mask processing
- exact preservation of pixels outside the authorized hard mask
- provider-neutral async inpainting interface
- deterministic local demo provider for zero-cost tests
- optional Black Forest Labs FLUX.1 Fill adapter
- synchronous `v1` compatibility route plus a bounded job-based `v2` API
- provisional `v3` Spatial Brief compiler and deterministic transform-only product placement
- deterministic, explainable `StyleIntent → prompt` and `SpatialDesignBrief → decision contract` compilers
- bounded uploads, prompts, product assets, placement planes, job records, concurrency, polling, retries and result downloads
- idempotent job submission with payload-conflict detection
- unit, property-oriented, lifecycle, API and exported-OpenAPI drift tests
- non-root Docker image and CI baseline
- portfolio-grade static showcase with cinematic 2.5D scrollytelling, a browser-local Boundary Lab, legacy mask Studio and Spatial Design Studio

> **Live showcase:** [Open the GitHub Pages experience](https://alinaderiii.github.io/interior-inpainting-orchestrator-poc/) — inspect the evidence or open the [Spatial Design Studio](https://alinaderiii.github.io/interior-inpainting-orchestrator-poc/spatial.html) for the browser-local `Brief → Locks → Placement → Variants → Handoff` vertical slice. The prior [Visual Restyle Studio](https://alinaderiii.github.io/interior-inpainting-orchestrator-poc/studio.html) remains available as focused mask-authoring evidence.

> **Scope:** Portfolio reference implementation focused on deterministic mask handling and protected-pixel compositing. Provider adapters are modular and swappable.

> **Release status:** `v0.3.0` is the current stable public release, adding Spatial Briefs, transform-only product placement, variant review and a cinematic landing experience. The release was promoted only after owner approval, multi-version CI, GitHub Pages deployment and hosted-browser verification. See the [changelog](CHANGELOG.md), [Phase 05 report](reports/PHASE_05_SPATIAL_DESIGN_STUDIO.md) and [Phase 06 report](reports/PHASE_06_CINEMATIC_SPATIAL_SHOWCASE.md).

## GitHub Pages showcase

The `site/` directory is a dependency-free static technical showcase designed for GitHub Pages. It includes:

- an accessible, responsive, dark/light portfolio experience;
- an original full-screen cinematic hero and reversible `Atmosphere → Analyze → Place → Prove` scroll story using local aligned frames and CSS perspective;
- static sequential fallbacks for reduced-motion and no-JavaScript contexts, plus solid reduced-transparency and increased-contrast states;
- an interactive before/after and authorized-mask inspector;
- a browser-local image + mask boundary lab with downloadable PNG output;
- the prior Visual Restyle Studio with structured intent, mask drawing/import, deterministic job simulation, explainable prompt and protected-pixel evidence;
- a five-stage Spatial Design Studio with structured brief, scene locks, four-corner hero placement, controlled variants, review selection and local proof exports;
- the original, accessible Luminous Glass control system with solid, reduced-transparency, reduced-motion and increased-contrast states;
- architecture, security, CI evidence and explicit open-risk sections;
- no analytics, cookies, external scripts, API calls or uploaded-file transmission;
- a restrictive Content Security Policy with outbound connections disabled.

GitHub Pages serves static files only—it does **not** run the FastAPI backend or hold provider credentials. Browser labs are clearly labelled deterministic and non-AI; the cinematic lounge frames are separately labelled illustrative and are not represented as live-model or deterministic evidence. See [`docs/GITHUB_PAGES.md`](docs/GITHUB_PAGES.md) for deployment and review instructions.

Preview it locally:

```bash
python -m http.server 4173 --directory site
```

Then open `http://localhost:4173`.

## Security posture

- No arbitrary remote image URLs are accepted by the PoC API.
- Uploads are limited by encoded bytes and decoded megapixels.
- Animated/multi-frame images are rejected.
- EXIF orientation is normalized and metadata is stripped from output.
- White mask pixels are editable; black pixels are protected.
- Final compositing restores original pixels outside the hard mask exactly.
- Provider credentials are read only from environment variables.
- Returned provider URLs are HTTPS-only and host-allowlisted.
- Live provider tests are excluded from normal CI.

## Quick start

```bash
python -m venv .venv
# Linux/macOS/Git Bash: source .venv/bin/activate
# Windows PowerShell:   .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
pytest -q
uvicorn inpainting_poc.api:app --reload
```

Open `http://localhost:8000/docs`.

## API surface — v0.3.0

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/health/live` | Process/provider liveness |
| `GET` | `/health/ready` | Bounded job-store capacity snapshot |
| `POST` | `/poc/v1/inpaint` | Backward-compatible synchronous inpaint |
| `POST` | `/poc/v2/intents/compile` | Deterministically compile and explain a `StyleIntent` |
| `POST` | `/poc/v2/jobs` | Accept a bounded asynchronous job and return `202` |
| `GET` | `/poc/v2/jobs/{job_id}` | Poll lifecycle, progress, metadata or safe failure |
| `GET` | `/poc/v2/jobs/{job_id}/result` | Retrieve the successful PNG result |
| `POST` | `/poc/v3/briefs/compile` | Canonicalize and explain a provisional Spatial Design Brief |
| `POST` | `/poc/v3/placements/preview` | Deterministic projective product placement with exact protected restoration |

The generated v0.3.0 contract is committed at [`docs/openapi-v0.3.0.json`](docs/openapi-v0.3.0.json). v2 lifecycle semantics remain in [`docs/API_V2.md`](docs/API_V2.md); the provisional Spatial Design surface is documented in [`docs/API_V3.md`](docs/API_V3.md). Regenerate the schema after API changes with:

```bash
python scripts/export_openapi.py
```

A test fails if the exported contract drifts from the runtime schema.

### Synchronous compatibility route

`POST /poc/v1/inpaint` accepts multipart fields:

- `image`: JPEG/PNG/WebP input;
- `mask`: aligned grayscale/RGB mask; white means edit, black means preserve;
- `prompt`: 1–1000 characters.

It returns a PNG. The default provider creates a deterministic colored texture in the editable region so mask alignment and compositing can be verified without a paid model.

### Job-based route

`POST /poc/v2/jobs` accepts `image`, `mask`, an optional free-form `prompt`, and an optional JSON-encoded `intent` multipart field. At least one of `prompt` or `intent` is required. An optional `Idempotency-Key` header must contain 8–128 safe ASCII characters.

The response supplies `Location`, `Retry-After`, no-store caching and links for polling and result retrieval. Lifecycle states are:

```text
queued → running → succeeded | failed → expired
```

The reference manager is deliberately **in-memory and non-durable**. Records, concurrent executions and TTL are bounded; shutdown cancels outstanding work. This demonstrates API lifecycle and safety behavior, not production queue persistence.

### Structured Style Intent

`StyleIntent` supports a controlled style, room type, palette, material cues, semantic-preservation notes and a short additional direction. Compiler `intent-v1` produces:

- a deterministic provider prompt;
- an ordered list of explainable prompt segments;
- a SHA-256 hash of the canonical intent.

Semantic preservation text is guidance only. The aligned hard mask and final compositing invariant remain the geometric authority.

### Spatial Brief and product placement — provisional v3

`SpatialDesignBrief` separates two intervention modes:

- `generative-concept`: exploratory art direction inside approved surface regions; no catalog-fidelity claim;
- `catalog-faithful-placement`: a hashed product raster is immutable source material and only projective geometry, bounded contact shadow and foreground occlusion order may change.

`POST /poc/v3/placements/preview` validates a normalized TL/TR/BR/BL quadrilateral, rejects degenerate or self-intersecting geometry, performs bounded OpenCV perspective placement and restores the source exactly outside the authorized destination plane. The PNG response carries a proof header with source/asset/output hashes, transform, coverage and protected-pixel drift.

In this reference PoC, “catalog-faithful” means **no mutation of the supplied source raster before geometric compositing**. It does not certify photometric appearance, physical material properties, manufacturing identity, client catalog compatibility or live-provider performance.

## Live FLUX.1 Fill

Set:

```bash
INPAINT_PROVIDER=bfl
BFL_API_KEY=...
BFL_RESULT_HOSTS=delivery-us1.bfl.ai,delivery-eu1.bfl.ai
```

The result host list must match the hosts actually returned for the approved BFL account/region. Do not loosen it to arbitrary HTTPS hosts. Live use requires account validation, budget approval and updated provider-contract tests.

## Deterministic mask/compositing proof

| Synthetic input | White = editable mask | Deterministic output (not AI) |
|---|---|---|
| ![Synthetic room input](docs/assets/before-synthetic.png) | ![White edit mask](docs/assets/mask-white-edit-synthetic.png) | ![Deterministic compositing result](docs/assets/after-deterministic-demo-not-ai.png) |

This artifact demonstrates geometry, mask polarity, inward feathering and exact restoration of protected pixels. It is deliberately **not** presented as an AI generation or visual-quality benchmark.

Regenerate it with:

```bash
python scripts/create_demo_artifacts.py
```

Temporary artifacts are written to `demo-artifacts/`; the approved synthetic documentation copies live in `docs/assets/`.

## Next step after contract award

Replace the provisional PoC API with the client-owned OpenAPI/schema baseline, run contract discovery, confirm the primary provider/model/region, and execute the approved security and delivery gates.

## License

MIT. Provider services and model outputs remain subject to their own terms, acceptable-use policies and commercial licensing.
