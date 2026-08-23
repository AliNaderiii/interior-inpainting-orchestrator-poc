# Phase 02 — Public Release Verification

**Date:** 2026-08-23

**Status:** `PASS_PUBLIC`

**Verified commit:** `12b2b9f48ec06be7448afd2385f2e925e445abf9`

## Executive result

The Phase 02 release was pushed to public `main`, passed the complete GitHub Actions matrix, deployed successfully to GitHub Pages and completed a real hosted Chromium workflow smoke test. The repository owner subsequently accepted the public Phase 02 experience manually.

This report closes the public CI, Pages, hosted-artifact and manual-acceptance gates that remained open in the local implementation report. It does not close production queue, client contract or live-provider acceptance gates.

## Git verification

| Control | Verified value |
|---|---|
| Public repository | `AliNaderiii/interior-inpainting-orchestrator-poc` |
| Default branch | `main` |
| HEAD | `12b2b9f48ec06be7448afd2385f2e925e445abf9` |
| Parent | `3b55daf950df2a9a757d5bccfbf298c61500dad9` |
| Delivery | Fast-forward |
| Commit title | `feat(orchestrator): add job API and visual restyle studio` |
| Published diff | 3,434 additions; 61 deletions |

The published commit is attributed to the repository owner. It is unsigned; published history must not be rewritten merely to add a signature.

## GitHub Actions verification

### CI

- Run: [32639806882](https://github.com/AliNaderiii/interior-inpainting-orchestrator-poc/actions/runs/32639806882)
- Head SHA: `12b2b9f48ec06be7448afd2385f2e925e445abf9`
- Event: `push`
- Conclusion: `success`

| Job | Conclusion |
|---|---:|
| Python 3.11 | PASS |
| Python 3.12 | PASS |
| Python 3.13 | PASS |

The Python 3.11 job also passed Ruff lint, Ruff format, strict mypy, static showcase validation and JavaScript syntax checks. Every runtime completed 24 tests.

### GitHub Pages

- Run: [32639806902](https://github.com/AliNaderiii/interior-inpainting-orchestrator-poc/actions/runs/32639806902)
- Head SHA: `12b2b9f48ec06be7448afd2385f2e925e445abf9`
- Event: `push`
- Conclusion: `success`

| Job | Conclusion |
|---|---:|
| Validate and package static showcase | PASS |
| Deploy GitHub Pages | PASS |

## Hosted artifact integrity

The hosted files were downloaded after deployment and compared byte-for-byte with raw files at the verified commit.

| Artifact | Equality | Hosted SHA-256 |
|---|---:|---|
| `index.html` | IDENTICAL | `505b51fb9f1035aac62172cb4ec18788b77f2dd3586a42c0ec9cdc54973da11e` |
| `studio.html` | IDENTICAL | `77e6f542797739d6baf6ad503978066df05b2f83c4ab8360c1645bff367c6d07` |
| `styles.css` | IDENTICAL | `8302149bf45d449fe2e58e079e91f593e45bf74f3b57ad57812ce92503a1c4b4` |
| `studio.css` | IDENTICAL | `43896340c89db00f068890218bc6efb3c4d58a3766572e731ca7779bb5274c11` |
| `app.js` | IDENTICAL | `cb6a7eac4b9702b7238d9fcdf9e6d0f699a9655b15a7eb2113be884eeeecf173` |
| `studio.js` | IDENTICAL | `cb68f706722801f5f68f5f42ec0e373f3e4a043694d120c2a3fa81a133cc450c` |
| `manifest.webmanifest` | IDENTICAL | `ffb508c90c3e000568311e91cb752fe1d7b0343f14576582421335a168e38757` |
| `sitemap.xml` | IDENTICAL | `1d623d5bb517e349884a2e35e9140062ced0abe49c066413243e61be3ede51f6` |
| `assets/before-synthetic.png` | IDENTICAL | `e9f9cf9a2feb358282c63a0bb88b8d7c56f64e1d9b4c3f62f41e65b96e83c213` |
| `assets/mask-white-edit-synthetic.png` | IDENTICAL | `afa0e0faf25674ce1b5edd1a79a6fb33c8f608867c44ff38f41d88928ed3d163` |

Both public entry points returned HTTP 200. Hosted `studio.js` used the correct JavaScript content type and all inspected assets reported the deployment timestamp.

## Hosted browser workflow

A clean Chromium session opened the public showcase and Studio, selected the three workflow steps, executed the deterministic job and inspected the result.

| Check | Result |
|---|---:|
| Home HTTP status | 200 |
| Studio HTTP status | 200 |
| Sample geometry | 960 × 640 |
| Mask coverage | 12.96% |
| Default intent identity | `e23725591163` |
| Protected pixels | 534,801 |
| Protected-pixel drift | 0 |
| Editable pixels changed | 79,599 |
| Download control | Enabled after success |
| Failed requests | 0 |
| Runtime page errors | 0 |
| Unexpected console errors | 0 |
| Requested hosts | `alinaderiii.github.io` only |

Browser proof:

```text
PASS · every protected pixel is byte-identical.
```

The smoke test observed the known browser warning that `frame-ancestors` is ignored when delivered through meta CSP. Phase 03 removes that ineffective directive and documents the GitHub Pages response-header limitation instead of claiming a control the host cannot enforce.

## Manual owner acceptance

The repository owner confirmed the public Phase 02 release after reviewing the hosted experience. This closes the manual public-acceptance gate.

## Remaining boundaries

- The public Studio remains deterministic, browser-local and non-AI.
- Live BFL execution remains credential-, region-, budget- and acceptance-dependent.
- The v2 manager remains bounded, in-memory and non-durable.
- Client-owned OpenAPI/JSON Schema conformance remains unavailable until those contracts are supplied.
- `main` was unprotected at verification time; staged ruleset guidance is provided in `docs/BRANCH_RULESET.md`.
