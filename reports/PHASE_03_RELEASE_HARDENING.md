# Phase 03 — Release Hardening and Portfolio Closure

**Date:** 2026-08-23

**Status:** `PASS_LOCAL / RELEASE_CANDIDATE`

**Target version:** `v0.2.0`

## Executive result

Phase 02 public acceptance is closed. Phase 03 aligns the static security claims with actual browser behavior, records public release evidence, synchronizes the showcase with the v2 API and prepares repeatable release and branch-safety guidance.

All work remains inside `interior-inpainting-orchestrator-poc`. No file, workflow, setting, branch or commit in `Smart-Interior-Decor-Recommendation-Platform` was changed.

## Delivered hardening

### Honest CSP boundary

- Removed meta-delivered `frame-ancestors` from every Pages entry point because browsers ignore that directive outside an HTTP response header.
- Retained `connect-src 'none'`, same-origin scripts/styles, bounded local image sources, `object-src 'none'`, `base-uri 'none'` and `form-action 'none'`.
- Updated the static validator and tests to reject any future attempt to restore an ineffective meta `frame-ancestors` claim.
- Documented the GitHub Pages response-header limitation and the headers required on a configurable host.

### Public release closure

- Added `reports/PHASE_02_PUBLIC_RELEASE_VERIFICATION.md`.
- Recorded public commit, CI and Pages run identifiers.
- Recorded byte-identical hosted artifact hashes.
- Recorded hosted Chromium workflow evidence and owner acceptance.
- Marked the original showcase validation report as a historical snapshot.

### Release material

- Added `CHANGELOG.md`.
- Added `docs/RELEASE_V0.2.0.md` as release-note source.
- Added `docs/BRANCH_RULESET.md` with staged, low-lockout branch protection guidance.
- Linked the release material from `README.md`.

### Showcase synchronization

- Updated the architecture narrative to describe Style Intent and the bounded v2 lifecycle.
- Replaced the primary architecture code sample with `POST /poc/v2/jobs`.
- Kept the synchronous `/poc/v1/inpaint` route visible as the compatibility path.

## Validation result

Machine-readable output is recorded in [`phase-03-validation.txt`](phase-03-validation.txt).

| Gate | Result |
|---|---:|
| Ruff format | PASS |
| Ruff lint | PASS |
| Strict mypy | PASS — 13 source files |
| pytest | PASS — 24 tests |
| Static showcase validator | PASS |
| JavaScript syntax | PASS |
| Desktop Chromium workflow | PASS |
| Mobile Chromium workflow | PASS |
| Unexpected console errors | 0 |
| Browser page errors | 0 |
| Failed requests | 0 |
| Protected pixels | 534,801 |
| Protected drift | 0 |

Both browser profiles completed `Intent → Mask → Preview → Verify`, enabled the PNG download control and restricted requests to the static-site origin. Removing the ineffective CSP directive eliminated the two known console warnings observed in the Phase 02 hosted baseline.

## Remaining owner/release actions

1. Push the independently reviewable Phase 03 commit.
2. Require CI and Pages to pass for the new commit.
3. Repeat hosted byte and Chromium smoke verification.
4. Create annotated tag `v0.2.0` on the hardened release commit.
5. Publish GitHub Release notes from `docs/RELEASE_V0.2.0.md`.
6. Enable Stage A branch rules from `docs/BRANCH_RULESET.md`.
7. Use Python 3.11–3.13 for local development; Python 3.14 remains intentionally unsupported until added to CI and dependency validation.

No history rewrite, commit amend or force push is required.
