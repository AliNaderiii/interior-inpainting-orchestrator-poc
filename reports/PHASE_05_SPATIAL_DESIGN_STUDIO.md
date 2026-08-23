# Phase 05 — Spatial Design Studio

**Status:** IMPLEMENTED AND LOCALLY VERIFIED — RELEASE BLOCKED
**Target:** `v0.3.0 — Spatial Briefs, Product-Fidelity Placement and Variant Review`
**Date:** 2026-08-23
**Scope lock:** this repository only; no code or asset is copied from the Smart Interior project or any client surface.

## 1. Mission

Evolve the controlled-inpainting reference PoC into a credible **Spatial Design Orchestrator** vertical slice for design professionals. The product must support a structured brief, explicit architecture/product locks, a catalog-faithful placement path, controlled variants, review evidence, and honest provenance.

The killer demo is deliberately narrow:

> **Hospitality Lounge + Hero Carpet/Object**

The primary product message is:

> **AI-assisted art direction, not one-click decoration.**

## 2. Multi-agent master execution prompt

The following English prompt is the working orchestration contract for Phase 05.

```text
You are a coordinated senior product-engineering council. Every lead and sub-agent must operate at the standard of a practitioner with 15+ years of relevant professional experience. Continue through research, implementation, adversarial review, debugging, testing, evidence capture, and remediation until every acceptance gate is either passed or explicitly documented as a blocker. Never fabricate results.

MISSION
Transform the existing Interior Inpainting Orchestrator reference PoC into a clean-room Spatial Design Orchestrator vertical slice centered on a Hospitality Lounge and a hero carpet/object. Preserve the deterministic protected-pixel invariant, provider neutrality, strict browser-local showcase security, bounded resources, and honest pre-contract claim boundaries.

NON-NEGOTIABLE BOUNDARIES
1. Modify only interior-inpainting-orchestrator-poc.
2. Do not copy code, assets, layout, visual language, text, or trade dress from any client, Apple, Figma, Canva, or another repository.
3. Do not claim client compatibility, partnership, production readiness, model quality, catalog fidelity, or live-provider validation unless proven by artifacts in this repository.
4. Keep Generative Concept and Catalog-faithful Placement separate in UX, schema, proof, and claims.
5. Keep browser showcase files local: no analytics, cookies, external scripts, network APIs, credentials, or upload transmission.
6. Preserve prior v1/v2 routes and do not rewrite previous release history.

AGENT COUNCIL
- Research Director: synthesize authoritative design-system, canvas-tool, accessibility, placement, and provenance research; record URLs and design implications.
- Product/Creative Workflow Lead: model a real spatial brief, scene hierarchy, architecture locks, product locks, controlled variants, critique, approval, and handoff.
- Design Systems Director: create the original Luminous Glass system; glass is limited to controls, navigation, toolbar, and inspector; canvas/content remain stable and readable.
- Accessibility Lead: verify keyboard semantics, focus order, labels, reduced transparency, reduced motion, increased contrast, 320px reflow, and non-color state cues.
- Frontend Architecture Lead: build a dependency-free professional canvas workspace with bounded local assets, responsive docked panels, contextual tools, product placement controls, variants, exports, and provenance.
- Imaging/Geometry Lead: implement deterministic quadrilateral placement, alpha compositing, occlusion order, exact protected-region restoration, placement validation, and proof metrics.
- Backend/API Lead: add provisional v3 Spatial Brief compilation and deterministic placement preview while preserving v1/v2 compatibility and strict validation.
- Security Lead: threat-model uploads, decoded dimensions, content types, CSP, object URLs, canvas exports, unsafe remote inputs, metadata, and denial-of-service paths.
- QA/Property Testing Lead: add unit, API, schema-drift, geometry, pixel-invariant, static-security, and browser tests; reproduce failures before remediation.
- Performance Lead: bound decoded pixels and subdivisions, avoid full-page blur and animated backdrop filters, and validate responsive/render behavior.
- Technical Writing/Release Lead: update README, API docs, changelog, architecture records, report, and release evidence without overstating the work.
- Red Team Reviewer: challenge every fidelity, AI, production, security, accessibility, and client-alignment claim; require correction or evidence.

IMPLEMENTATION VERTICAL SLICE
A. Spatial Brief: context, mode, objectives, narrative, palette, materials, lighting, preservation constraints, and output intent.
B. Scene Plan: architecture/opening/furniture/product regions and hard locks with clear authority.
C. Catalog-faithful Placement: immutable source asset identity, bounded upload, four-corner floor-plane placement, alpha compositing, optional occlusion ordering, and deterministic output.
D. Controlled Variants: change only approved design variables; keep product identity and protected regions stable.
E. Review Board: compare named variants, select a direction, show proof metrics, and export a local manifest/contact sheet.
F. Provenance: record compiler version, canonical brief hash, source asset hash, transform, allowed-change regions, output identity, and explicit limitations.

DESIGN ACCEPTANCE
- Canvas remains the visual center.
- Desktop workflow rail and inspector are docked; mobile becomes stacked/sheet-like without covering critical content.
- No nested glass, blur animation, or glass on long-form evidence.
- Solid fallback plus reduced-transparency, reduced-motion, and increased-contrast states.
- Primary action is solid/high-contrast; tint communicates selection only.

ENGINEERING ACCEPTANCE
- Exact zero drift outside the authorized change region in deterministic tests.
- Invalid/self-intersecting/degenerate placement geometry is rejected.
- Existing v1/v2 contracts and tests remain green.
- Exported OpenAPI equals runtime OpenAPI.
- Static validator rejects network primitives and validates CSP/local references/resource limits.
- Ruff, mypy, pytest, static validation, and hosted-browser verification pass before release.

STOP CONDITIONS
Do not tag or publish if Git metadata is unavailable, if browser verification is incomplete, if tests fail, if a boundary claim is ambiguous, or if live-provider evidence is absent but implied. Report the blocker and keep the work as an unreleased Phase 05 candidate.
```

## 3. Research synthesis

### 3.1 Control-layer glass

Official Apple 2025 design guidance treats Liquid Glass as an adaptive material for navigation and controls, not an indiscriminate content treatment. It warns against glass-on-glass and over-tinting, and centers legibility and accessibility. This directly produced the Luminous Glass rule that the canvas, evidence, code, and long-form content remain opaque.

Sources:

- https://developer.apple.com/videos/play/wwdc2025/219/
- https://developer.apple.com/videos/play/wwdc2025/356/
- https://developer.apple.com/videos/play/wwdc2025/323/
- https://developer.apple.com/forums/topics/design-topic

### 3.2 Canvas-first professional workspace

Figma UI3 documented that canvas space and workflow speed can be harmed by overly floating interfaces. Lucid and other canvas-tool guidance distinguishes fixed chrome, contextual controls, canvas content, and modal focus. The implementation therefore uses docked desktop panels and reserves floating behavior for a compact contextual tool cluster.

Sources:

- https://www.figma.com/blog/our-approach-to-designing-ui3/
- https://lucid.co/techblog/2023/08/25/design-for-canvas-based-applications
- https://medium.com/design-ibm/designing-for-canvas-tools-22ff02fb82f6

### 3.3 Unified workflow rather than disconnected generators

Canva's public Visual Suite direction reinforces the value of keeping brief, creation, iteration, and outputs within one workspace. The relevant pattern is workflow continuity—not visual imitation.

Source:

- https://www.maginative.com/article/canva-goes-all-in-on-ai-with-visual-suite-2-0-and-canva-ai/

### 3.4 Accessibility and performance

Blur must be limited, contrast must be deterministic, and solid fallbacks are mandatory. Luminous Glass includes explicit reduced transparency, reduced motion, and increased contrast states. No full-page backdrop filter or blur animation is allowed.

Additional reading:

- https://designmd.app/library/glassmorphism/
- https://axesslab.com/glassmorphism-meets-accessibility-can-frosted-glass-be-inclusive/

## 4. Architecture decisions

### ADR-05-01 — Add a new Spatial Studio surface

Keep the released `studio.html` workflow available as a legacy controlled-inpainting proof. Add a separate `spatial.html` product surface and make it the primary v0.3 preview entry point. This limits regression risk and keeps claim boundaries explicit.

### ADR-05-02 — Separate concept and placement

`Generative Concept` may change approved materials/colors through an authorized mask. `Catalog-faithful Placement` uses the supplied raster as immutable source material and applies only geometry/compositing transformations. The two modes must not share a misleading “generate” label.

### ADR-05-03 — Deterministic placement first

The first placement implementation is a bounded projective transform with alpha compositing and exact restoration outside the destination authorization. This can be tested without credentials and creates a dependable contract for later segmentation/depth providers.

### ADR-05-04 — Provenance without false standards claims

The manifest records hashes, versions, inputs, transforms, outputs, and limitations. It is a project evidence manifest, not a claim of C2PA conformance or external certification.

## 5. Security threat model additions

| Threat | Mitigation | Gate |
|---|---|---|
| Oversized product raster | Encoded byte and decoded pixel limits | API/browser tests |
| Remote asset exfiltration | Local files only; CSP `connect-src 'none'`; no URL input | static validator |
| Degenerate or self-crossing quad | Convexity, area, ordering, and normalized-coordinate validation | geometry tests |
| Placement outside scene | every corner constrained to `[0,1]` | schema tests |
| Product mutation hidden as fidelity | immutable input hash and explicit transform-only claim | proof review |
| Variant drift outside locks | authoritative post-composite restoration and pixel comparison | invariant tests |
| Canvas/browser memory pressure | bounded dimensions, bounded subdivision, object URL revocation | static/browser review |
| Glass legibility/performance | compact surfaces, solid fallbacks, no blur animation | CSS/static/browser gate |

## 6. Implemented vertical slice

### 6.1 Browser workspace

| Capability | Implementation |
|---|---|
| Spatial Brief | mode, project context, objective, atmosphere, material cues and explicit decision boundary |
| Scene Locks | architecture, openings, furniture/occlusion and hero-plane authority model |
| Placement | four draggable corners, normalized keyboard inputs, bounded local product upload, contact shadow and foreground restoration |
| Mode separation | placement runs the hero-product step; concept skips it and carries no catalog asset claim |
| Controlled variants | three named directions change approved wall polygons while keeping locks stable |
| Review | selected variant, proof metrics, explicit model-quality boundary and three local export formats |
| Provenance | canonical brief hash, source/asset identity, normalized transform, output hash, proof and limitations |
| Accessibility | semantic controls, canvas keyboard movement, focus visibility, 320/390 px responsive flow and non-color labels |
| Luminous Glass | control-only glass, opaque canvas/evidence, manual solid mode and system preference fallbacks |

Primary files:

- `site/spatial.html`
- `site/spatial.css`
- `site/spatial.js`
- `docs/LUMINOUS_GLASS_DESIGN_SYSTEM.md`
- `scripts/create_spatial_assets.py`

### 6.2 Clean-room assets

The script generated an original synthetic Hospitality Lounge, foreground occlusion layer, Contour 01 hero carpet and catalog card. The four optimized site PNGs total approximately **448 KB**.

Stable evidence identities:

- source scene: `5c6425d87509a6a23e2f4a70ba5dfba2722ed0dc5c094f7a5d4a1af4760ba036`
- hero carpet: `e87dc919e59bf63d94f28e7c0578c237a724a294427f4f46fb0e6400a92d131d`

### 6.3 Backend and contract

Added `src/inpainting_poc/spatial.py` with:

- mode-safe `SpatialDesignBrief` and `HeroAssetRef` models;
- canonical `spatial-brief-v1` compiler;
- normalized four-corner placement schema;
- convexity, ordering, bounds and minimum-area validation;
- bounded projective warp, alpha composite and contact shadow;
- authoritative source restoration outside the destination authorization;
- `placement-v1` proof with source/asset/output hashes and transform matrix.

Added routes:

- `POST /poc/v3/briefs/compile`
- `POST /poc/v3/placements/preview`

The v1 and v2 routes remain present. Candidate contract and documentation:

- `docs/openapi-v0.3.0.json`
- `docs/API_V3.md`

## 7. Completed checklist

- [x] Research and current-code audit
- [x] Multi-agent master execution prompt
- [x] Luminous Glass design-system specification
- [x] Synthetic clean-room hospitality scene and hero product assets
- [x] Spatial Studio shell and responsive workspace
- [x] Four-corner browser-local placement with proof
- [x] Controlled variants and review board
- [x] v3 Spatial Brief compiler
- [x] v3 deterministic placement endpoint
- [x] OpenAPI v0.3 export and documentation
- [x] Static, Python, accessibility-preference, responsive and browser-local verification
- [ ] Hosted GitHub Pages verification for the candidate
- [ ] Git commit/tag/release gate — blocked because `.git` metadata is unavailable

## 8. Verification record

All results below were observed locally on 2026-08-23. Python on the execution host is 3.13; the repository CI matrix remains 3.11–3.13.

| Gate | Command / method | Observed result |
|---|---|---|
| Python behavior | `pytest -q` | **30 passed in 1.23s** |
| Lint | `ruff check .` | **All checks passed** |
| Formatting | `ruff format --check .` | **45 files already formatted** |
| Types | `mypy src` | **Success; 14 source files** |
| Static security | `python scripts/validate_static_site.py` | **PASS** |
| JavaScript syntax | `node --check` on all three site scripts | **PASS** |
| OpenAPI drift | export then `pytest -q tests/test_openapi.py` | **2 passed** |
| Direct dependency audit | isolated `pip-audit -r` from project constraints | **No known vulnerabilities found** |
| Package build | `python -m pip wheel . --no-deps` | **0.3.0 wheel built; SHA-256 `64c48bd7fb5a054018f9bdbd408c195262cd526c449a69423e6c3c09b91fa8dd`** |
| Asset regeneration | script plus SHA-256 comparison | source and hero identities reproduced exactly |
| Browser desktop | Chromium 1440 × 1000 | placement workflow PASS; concept-route separation PASS; zero console errors |
| Browser responsive | Chromium 390 × 844 | no horizontal overflow; docked regions stack correctly |
| Transparency fallback | manual control in Chromium | `data-transparency=reduced`; solid surfaces active |
| Protected proof | browser and Python placement tests | **0 protected-pixel drift** |

A global-environment `pip-audit` also reported current advisories in globally installed `aiohttp` and `pip`. Neither is declared by this project. The isolated audit of the project dependency constraints resolved with no known vulnerabilities; the global environment finding remains documented rather than hidden.

Browser evidence images:

- `reports/phase05-spatial-desktop.png`
- `reports/phase05-spatial-handoff-desktop.png`
- `reports/phase05-spatial-mobile.png`

## 9. Current claim boundary

Phase 05 is an unreleased reference implementation. It does not claim a production client contract, live model quality, automatic depth/segmentation, full catalog integration, photometric material accuracy, BIM/AR support, durable external provenance certification, or production queue durability. Provider credentials are not required for deterministic evidence.

“Catalog-faithful” is deliberately narrow here: the supplied product raster is immutable source material before geometric compositing. It does not certify how a physical product will photograph, manufacture, light, drape or appear in a client-owned catalog.

## 10. Release decision

**NO-GO for tag or public deployment from this workspace.**

The implementation and local gates pass, but `.git` is absent and `git status` returns `fatal: not a git repository`. Therefore commit review, diff integrity, signed release history, CI execution, Pages artifact comparison and hosted-browser verification cannot be completed here. The candidate should remain unreleased until repository metadata is restored and the remaining gates run against the exact commit.
