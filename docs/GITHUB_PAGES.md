# GitHub Pages Showcase

## Purpose

The `site/` directory is a static, portfolio-grade technical showcase for this reference PoC. It is intentionally separate from the FastAPI runtime:

- GitHub Pages presents architecture, security controls and executable browser-side evidence.
- FastAPI remains the backend reference implementation and runs locally, in CI tests, or on an approved application host.
- The browser Boundary Lab is deterministic and non-AI. It does not call FLUX or claim generative quality.

Expected public URL:

`https://alinaderiii.github.io/interior-inpainting-orchestrator-poc/`

## One-time owner action

After pushing the Pages implementation to `main`:

1. Open the repository on GitHub.
2. Select **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to **GitHub Actions**.
4. Open **Actions → pages** and wait for both jobs to pass:
   - `Validate and package static showcase`
   - `Deploy GitHub Pages`
5. Open the deployment URL shown by the workflow or the expected URL above.

The workflow also supports a manual run through **Actions → pages → Run workflow**.

## Deployment architecture

`.github/workflows/pages.yml` performs two least-privilege jobs:

1. `build` checks out the repository without persisted credentials, configures Pages, verifies required files and uploads only `site/`.
2. `deploy` receives `pages: write` and `id-token: write` only, targets the protected `github-pages` environment, and deploys the prepared artifact.

All official actions are pinned to full commit SHAs. The site has no package install or third-party build chain.

## Static-site security boundary

The main page declares a restrictive Content Security Policy:

- `connect-src 'none'` blocks runtime network/API calls;
- scripts, styles and images are same-origin only;
- inline scripts, inline styles, frames, objects, forms and base-URL changes are blocked;
- uploaded files are decoded locally with browser APIs and are not transmitted;
- no analytics, cookies, external fonts or third-party JavaScript are used.

Never add provider API keys, backend secrets, `.env` files or live paid-provider calls to GitHub Pages. Client-side code and Pages artifacts are public.

## Review checklist

Before sharing the URL with a client:

- [ ] `ci` passes on Python 3.11, 3.12 and 3.13.
- [ ] `pages` build and deploy jobs pass.
- [ ] The home page loads without a path suffix.
- [ ] Before/after slider and mask overlay work.
- [ ] Boundary Lab sample produces zero changed protected pixels.
- [ ] Custom image and mask remain local and produce a downloadable PNG.
- [ ] Mobile navigation and dark/light theme work.
- [ ] External source, CI, security and validation links resolve.
- [ ] No text implies that the deterministic browser demo is AI-generated.
- [ ] No live-provider capability is claimed without approved evidence.

## Local preview

From the repository root:

```bash
python -m http.server 4173 --directory site
```

Open `http://localhost:4173`.

The local preview server is for visual review only. The repository's automated tests validate local references, CSP assumptions, copied evidence assets, scope language, manifest data and pinned Pages action references.

## Rollback

To remove the public site without deleting repository history:

1. Open **Settings → Pages**.
2. Disable the Pages deployment/source.
3. Keep the source and workflow for auditability, or revert the relevant commit through the normal review process.
