# GitHub Pages Showcase Validation Report

**Date:** 2026-08-23
**Status:** `PASS_WITH_DEPLOYMENT_GATE`
**Scope:** Static showcase, browser Boundary Lab, Pages workflow and repository integration

## Executive result

The static showcase is ready for owner review and GitHub Pages deployment. Local quality gates pass. Public deployment remains intentionally unverified until the repository owner pushes the changes, enables **Settings → Pages → Source: GitHub Actions**, and the hosted `pages` workflow succeeds.

This report does not change the main PoC's `PASS_WITH_RISK` status and does not validate live FLUX execution or generative visual quality.

## Implemented surface

- Responsive portfolio-grade technical landing page
- Dark/light theme and mobile navigation
- Canvas before/after comparison with authorized-mask overlay
- Browser-local image and mask Boundary Lab
- Exact protected-pixel evidence calculation and downloadable PNG
- Architecture, API, security, CI and engineering-honesty sections
- Social preview, favicon, manifest, sitemap, robots and 404 assets
- Least-privilege GitHub Pages workflow with full-SHA action pins
- Four automated static-site/security tests integrated into the Python matrix

## Local validation evidence

Machine-readable command output and asset hashes are recorded in `docs/validation/showcase-validation.txt`.

| Check | Result |
|---|---:|
| JavaScript syntax (`node --check site/app.js`) | PASS |
| Static asset HTTP availability | PASS |
| Local HTML reference resolution | PASS |
| CSP/no-network boundary assertions | PASS |
| No inline script/style/event handlers | PASS |
| Documentation/site artifact hash equality | PASS |
| Synthetic image/mask/result geometry | PASS — 960 × 640 |
| Pages action references pinned to 40-character SHAs | PASS |
| Targeted credential-pattern review | PASS — 0 candidates |
| Pages artifact symlink review | PASS — 0 symlinks |
| Ruff lint | PASS |
| Ruff format check | PASS — 26 files |
| Strict mypy | PASS — 11 source files |
| pytest | PASS — 12 tests |

Local runtime used for the combined validation: Python 3.13.14. The public CI workflow remains responsible for repeating all 12 tests on Python 3.11, 3.12 and 3.13 after push.

## Security review

- Pages artifact scope is limited to `site/`.
- The static page has `connect-src 'none'`; no runtime API request path exists.
- No analytics, cookies, third-party JavaScript, third-party CSS or external font runtime is present.
- Browser uploads use `File`, `blob:` URLs and Canvas locally.
- Browser processing is restricted to PNG/JPEG/WebP, 12 MB encoded bytes and four megapixels to reduce UI resource risk.
- Provider credentials and paid-provider calls are absent from the Pages artifact.
- Pages build has read-only repository contents access.
- Only the deploy job receives `pages: write` and `id-token: write`.
- Checkout disables credential persistence.
- Checkout, configure-pages, upload-pages-artifact and deploy-pages are pinned to reviewed release commit SHAs.

## Claim integrity

The site repeatedly distinguishes these categories:

1. **Demonstrated:** deterministic mask authority, protected-pixel restoration, provider-neutral boundaries, mocked BFL protocol behavior, local tests and security controls.
2. **Browser simulation:** local deterministic recoloring used only to demonstrate the boundary invariant.
3. **Open production gates:** client contracts, approved provider/model/region, credentials, budget, deployment target and live visual-quality acceptance.

The browser output is visibly watermarked `NON-AI LOCAL SIMULATION` and the site does not describe it as an AI result.

## Open deployment gate

The following evidence cannot exist until owner action occurs on GitHub:

- hosted Pages workflow run URL and conclusion;
- final public deployment URL response;
- hosted browser smoke test;
- hosted mobile/device review;
- public `pages` badge status.

After deployment, record the workflow run ID and hosted smoke-test result in this report or a follow-up evidence file.
