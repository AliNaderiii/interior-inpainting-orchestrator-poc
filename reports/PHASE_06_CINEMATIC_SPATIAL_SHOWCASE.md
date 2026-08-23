# Phase 06 — Cinematic Spatial Showcase

**Status:** LOCAL IMPLEMENTATION + VALIDATION COMPLETE · RELEASE NO-GO
**Date:** 2026-08-23
**Scope:** public GitHub Pages showcase only; Spatial Studio remains a productivity-focused tool surface
**Change boundary:** this repository only

## 1. Objective

Add a cinematic, scroll-directed presentation layer that communicates the Spatial Design Orchestrator as a premium design-technology product without compromising the browser-local security boundary, deterministic evidence, accessibility, performance or honest claims.

The chosen interaction model is:

> **A scroll-scrubbed spatial story with 3D depth cues and local cinematic frames—not an always-running background video.**

The story follows four product decisions:

1. Atmosphere
2. Analyze
3. Place
4. Prove

## 2. Multi-agent execution brief

```text
Act as a coordinated senior immersive-web council. Every lead and reviewer must work at the standard of a practitioner with 15+ years of relevant experience. Continue through research, clean-room design, implementation, adversarial review, browser profiling, accessibility verification, static-security validation and remediation.

MISSION
Upgrade the public showcase into a cinematic scroll experience that makes the Spatial Design Orchestrator feel dimensional, art-directed and memorable. Keep the actual Spatial Studio fast, docked, precise and tool-first.

AGENTS
- Immersive Creative Director: own visual narrative, pacing, framing, type scale and cinematic restraint.
- Scrollytelling Director: map scroll progress to four understandable product decisions.
- 3D/Motion Lead: create camera push, depth layers, product-plane motion and lighting transitions using local progressive enhancement.
- Frontend Performance Lead: keep motion transform/opacity based, schedule JS in requestAnimationFrame, avoid frame-sequence bloat and prevent layout thrash.
- Accessibility Lead: supply reduced-motion static flow, readable overlays, semantic chapter content, keyboard-safe navigation and contrast review.
- Security Lead: preserve connect-src 'none', local assets, no external libraries, no analytics and no remote media.
- Product Truth Reviewer: label cinematic frames as illustrative; never present them as live provider or deterministic evidence.
- QA Lead: test desktop, 390px mobile, reduced motion, no-JS fallback, console errors, local references and horizontal overflow.

NON-NEGOTIABLES
1. Do not copy layouts, assets, text, transitions or trade dress from Dribbble, Webflow, Draftly or any client.
2. Use the references only to extract general interaction principles.
3. Keep the existing Boundary Lab and deterministic proof available.
4. Do not add a mandatory autoplay video, third-party runtime, WebGL dependency, smooth-scroll hijacking or cursor replacement.
5. The scroll experience must be reversible: scrolling upward reverses the visual state.
6. Reduced-motion users receive a stable image and sequential content, not disabled information.
7. The cinematic frames are illustrative art-direction assets and must be explicitly separated from executable evidence.
8. Do not tag or deploy while Git metadata is unavailable.
```

## 3. Reference audit

### Dribbble

Reviewed:

- https://dribbble.com/
- https://dribbble.com/shots/20924971-Landing-page-with-scroll-based-video-and-3D
- https://dribbble.com/tags/cinematic_web
- https://dribbble.com/tags/parallax-scrolling

Useful principle: high-impact landing pages tell a progressive story. Depth maps, 3D models and scroll-scrubbed media work when each transition reveals product meaning. The visual itself is not enough.

Rejected pattern: copying a shot composition or using ornamental motion without a product decision.

### Webflow cinematic gallery

Reviewed:

- https://webflow.com/made-in-webflow/cinematic

Useful principles:

- full-bleed media with decisive typography;
- reveal pacing rather than displaying every message simultaneously;
- product/video experiences organized as chapters;
- strong first frame before motion begins.

Rejected pattern: third-party embeds or cloning community templates.

### Draftly

Reviewed:

- https://www.draftly.space/
- https://www.draftly.space/about
- https://www.draftly.space/3d-builder

Useful principles:

- convert a cinematic timeline into scroll progress;
- preserve a fixed portal while the world behind it changes;
- product injection becomes a distinct narrative moment;
- scroll forward and backward maps naturally to timeline direction;
- frame extraction can mimic 3D without requiring WebGL.

Rejected for this repository:

- hundreds of video frames, because they would inflate a small static PoC;
- generated runtime services, because CSP blocks network access;
- claims that a frame sequence is literal real-time 3D.

### Standards and implementation references

- MDN Scroll-driven animation timelines:
  https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Scroll-driven_animations/Timelines
- Codrops practical scroll-driven animations:
  https://tympanus.net/codrops/2024/01/17/a-practical-introduction-to-scroll-driven-animations-with-css-scroll-and-view/
- web.dev video performance:
  https://web.dev/learn/performance/video-performance

Resulting engineering principles:

- prefer native scroll progress and transform/opacity animation;
- use `requestAnimationFrame` only for the custom crossfade/perspective state;
- keep the base document readable when advanced animation support is absent;
- honor `prefers-reduced-motion` in both CSS and JavaScript;
- if a real video is added later, require poster, muted/playsinline behavior, pause control, visibility pausing, lazy loading and mobile/reduced-motion fallbacks;
- do not make a background video the initial LCP dependency.

## 4. Design decision

### ADR-06-01 — Use 2.5D cinematic depth instead of mandatory WebGL

The showcase will use two aligned local cinematic frames, CSS perspective layers, a real product raster plane, camera push and scroll-linked lighting. This creates spatial depth with a smaller attack surface and better static-host compatibility than a new 3D runtime.

The result is described as **3D depth / 2.5D scrollytelling**, not as a full interactive BIM or photoreal digital twin.

### ADR-06-02 — No autoplay video in this iteration

The user requested video or image change while scrolling. Scroll-scrubbed local images provide the desired cinematic response while avoiding autoplay policy failures, continuous motion, mobile data cost and inaccessible unpausable playback.

A future real-video gate is documented, but not implied as implemented.

### ADR-06-03 — Showcase and Studio remain distinct

The public landing page may be cinematic. The Spatial Studio remains a stable professional workspace. This prevents storytelling motion from slowing repeated production tasks.

## 5. Asset provenance

Two original local frames were generated specifically for this clean-room showcase:

- `site/assets/cinematic-lounge-concept.jpg`
- `site/assets/cinematic-lounge-analysis.jpg`

They are illustrative concept frames. They are not outputs from the repository's deterministic provider, do not demonstrate a live model, and are not client work.

## 6. Acceptance gates

- [x] Reference research and design decision
- [x] Original local cinematic concept frame
- [x] Original aligned analysis/digital-twin frame
- [x] Full-screen cinematic hero
- [x] Four-chapter sticky scroll experience
- [x] CSS perspective product-plane transition
- [x] Reduced-motion static sequence
- [x] No-JavaScript readable fallback
- [x] Existing evidence/lab preserved
- [x] Static validator and tests extended
- [x] Desktop/mobile browser verification
- [x] Report completion and release decision

## 7. Implemented experience

### Cinematic landing hero

`site/index.html` now opens with a full-viewport Hospitality Lounge composition, responsive art direction, high-contrast product messaging, two direct calls to action and an explicit local label:

> Illustrative concept frame — atmosphere only—not deterministic or live-model evidence.

The header receives a dark translucent control layer only while the hero or cinematic story is in view. No blur property is animated, and reduced-transparency users receive an opaque surface.

### Reversible scroll narrative

`site/cinematic.js` converts native document scroll into a bounded `0..1` timeline scheduled through `requestAnimationFrame`. The four states are reversible and communicate product decisions rather than ornamental effects:

1. `Atmosphere` — brief authority and material intent;
2. `Analyze` — aligned spatial-analysis frame, lock map, floor grid and scan;
3. `Place` — immutable local product raster enters as a CSS-perspective plane;
4. `Prove` — motion resolves into handoff language, source-match proof and project-local identifiers.

The camera uses transform-only movement. Frame, grid, product and proof transitions use opacity and transforms. The implementation does not hijack scrolling and contains no smooth-scroll library, cursor replacement, WebGL runtime, video element or autoplay media.

### Progressive fallbacks

- `prefers-reduced-motion: reduce`: sticky animation is replaced by one stable frame and four sequential readable cards.
- JavaScript disabled: the same four-card information architecture remains visible through the absence of `data-cinematic-ready`.
- `prefers-reduced-transparency: reduce`: glass controls and the cinematic header become solid.
- `prefers-contrast: more`: copy, vignette and borders are strengthened.
- Unsupported `backdrop-filter`: solid backgrounds remain available through `@supports not`.
- Mobile: the scroll story remains active at 390 px; type, scene crop, product plane and chapter layout are independently composed. The 320 px overflow gate also passes.

### Evidence separation

The former executable comparison remains available as a distinct **Evidence Portal** after the cinematic narrative. Illustrative JPGs are not reused as test output. The deterministic compare slider, Boundary Lab, legacy Restyle Studio and Spatial Studio remain intact.

## 8. Files added or materially changed

- `site/index.html` — cinematic hero, four-chapter story and evidence portal.
- `site/cinematic.css` — hero composition, dark control layer, perspective scene, mobile layout and accessibility/no-JS fallbacks.
- `site/cinematic.js` — reversible scroll timeline and chapter state.
- `site/assets/cinematic-lounge-concept.jpg` — original 1376 × 768 illustrative atmosphere frame, 120,667 bytes.
- `site/assets/cinematic-lounge-analysis.jpg` — original aligned 1376 × 768 spatial-analysis frame, 143,410 bytes.
- `site/app.js` — keyboard `Escape` dismissal and focus return for mobile navigation.
- `scripts/validate_static_site.py` — cinematic file, JPEG signature, size-budget, no-network, motion and fallback gates.
- `.github/workflows/ci.yml`, `.github/workflows/pages.yml` — syntax-check every `site/*.js` file, including Spatial and cinematic runtimes.
- `tests/test_static_site.py` — frame dimensions, claim boundaries, scroll implementation and accessibility assertions.
- `scripts/create_social_preview.py`, `site/assets/social-preview.png` — reproducible 1200 × 630 cinematic Open Graph card (248,503 bytes).
- `README.md`, `CHANGELOG.md`, `docs/GITHUB_PAGES.md` — candidate scope, boundaries and review instructions.

Asset SHA-256:

```text
cinematic-lounge-concept.jpg  088ed2d9fff1041a1814419c8bca285d21f3d139fd2cf90f29d359e21c6ec1d2
cinematic-lounge-analysis.jpg 3a2b30b910c021f6160a4bd3564f0bf0010f176dbf8525790ac8e68e168fd9ae
```

## 9. Verification results

### Static, Python and packaging gates

| Gate | Result |
|---|---|
| Full test suite | **31 passed in 1.89 s** |
| Ruff lint | **All checks passed** |
| Ruff format | **46 files already formatted** |
| mypy | **Success; 14 source files** |
| Static showcase validator | **PASS** |
| JavaScript syntax, every `site/*.js` | **PASS** |
| Wheel build | **PASS**, `interior_inpainting_orchestrator_poc-0.3.0-py3-none-any.whl` |
| Wheel SHA-256 | `2aa1893f6878e7f77ef73b418911e4f5526c0b362dffd306da3f1bc8420be5ff` |
| Direct dependency audit | **No known vulnerabilities found** |

The dependency declarations did not change in Phase 06. The audit was nevertheless rerun against the project's eight direct runtime constraints rather than the unrelated global environment.

### Local Chromium gates

| Scenario | Result |
|---|---|
| Desktop hero and all four chapters, 1440 × 1000 | **PASS** |
| Scroll forward and backward restores chapter/analysis state | **PASS** |
| Mobile hero and all chapters, 390 × 844 | **PASS** |
| Narrow 320 × 720 horizontal overflow | **0 px overflow** |
| Desktop/mobile console and page errors | **0** |
| Reduced motion static sequence | **PASS** |
| JavaScript-disabled static sequence | **PASS** |
| Reduced transparency solid controls/header | **PASS** |
| Increased contrast copy state | **PASS** |
| Keyboard skip link | **PASS** |
| Mobile menu Enter / Escape / focus return | **PASS** |
| Spatial placement workflow through handoff | **PASS**, `protected drift = 0 px` |
| Spatial Generative Concept route skips placement | **PASS** |

### Local performance observation

A headless Chromium run against the local static server produced:

| Measurement | Local result |
|---|---:|
| Largest Contentful Paint | 328 ms |
| Cumulative Layout Shift | 0 |
| Long tasks observed during load | 1 |
| DOMContentLoaded | 153 ms |
| Load event | 306 ms |
| Static resources | 10 |
| Transfer bytes | 535,550 |
| Decoded body bytes | 532,550 |

These values are local regression evidence, not field or hosted performance claims. Hosted Pages metrics remain a release gate after deployment.

## 10. Visual evidence

- `reports/phase06-cinematic-hero.png`
- `reports/phase06-cinematic-analysis.png`
- `reports/phase06-cinematic-placement.png`
- `reports/phase06-cinematic-proof.png`
- `reports/phase06-cinematic-mobile-hero.png`
- `reports/phase06-mobile-analysis.png`
- `reports/phase06-mobile-placement.png`
- `reports/phase06-mobile-proof.png`
- `reports/phase06-cinematic-reduced-motion.png`
- `reports/phase06-cinematic-no-js.png`

The four desktop decision captures are 1440 × 1000. Mobile captures are 390 × 844. The screenshots are review artifacts, not product output or client work.

## 11. Security and truth review

- CSP remains `connect-src 'none'`; cinematic JavaScript contains no network API.
- Every runtime asset is repository-local.
- No analytics, cookies, remote font, third-party script, iframe or provider credential was introduced.
- Cinematic JPG files are signature-checked and capped below 500 KB by the validator.
- Existing browser upload byte/pixel limits and object-URL revocation remain unchanged.
- The invariant `protected_pixel_drift == 0` remains tested and was reverified through the browser workflow.
- All new public-facing claims distinguish illustrative art direction from executable deterministic evidence.
- No file in `Smart-Interior-Decor-Recommendation-Platform` was read for copying or modified during implementation.

## 12. Residual gates and decision

### Locally accepted

The Phase 06 implementation satisfies the requested cinematic, spatial, scroll-responsive and clean-room experience. The page visibly changes scene analysis, camera, geometry, product plane and proof state with scroll while remaining useful on mobile and in reduced-motion/no-JavaScript contexts.

### Still blocked

- The workspace has no `.git` metadata, so no commit, diff review, tag or release can be created here.
- The new candidate has not been deployed to GitHub Pages; hosted path, cache, CSP console, Web Vitals and action provenance are unverified.
- Final visual approval from the repository owner is still required.
- Live-provider quality, production queues, automatic depth/segmentation and client-contract compatibility remain outside this phase.

### Release decision

> **Phase 06 local implementation: PASS. `v0.3.0` publication: NO-GO.**

`v0.2.0` remains the stable public release. Continue to Git/Release Candidate operations only after owner approval and restoration of Git metadata, then rerun CI, Pages deployment and hosted-browser verification against the exact candidate commit.
