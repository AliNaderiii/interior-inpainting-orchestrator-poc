# GitHub Pages Showcase

## Purpose

The `site/` directory is a static, portfolio-grade technical showcase for this reference PoC. It is intentionally separate from the FastAPI runtime:

- GitHub Pages presents architecture, security controls, an illustrative cinematic narrative and executable browser-side evidence.
- FastAPI remains the backend reference implementation and runs locally, in CI tests, or on an approved application host.
- The cinematic lounge frames are original illustrative art-direction assets, not deterministic evidence, live-model output or client work.
- The browser Boundary Lab, Visual Restyle Studio and Spatial Design Studio are deterministic and non-AI. They do not call FLUX or claim generative quality.
- Spatial Studio demonstrates brief structure, authored scene locks, transform-only product placement, controlled variants and local proof exports.

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

Every HTML entry point declares a restrictive Content Security Policy. `index.html`, `studio.html` and `spatial.html` explicitly disable all runtime connections:

- `connect-src 'none'` blocks runtime network/API calls;
- scripts and styles are same-origin; images are limited to same-origin and local `data:`/`blob:` sources;
- inline scripts, inline styles, objects, forms and base-URL changes are blocked;
- uploaded files are decoded locally with browser APIs and are not transmitted;
- no analytics, cookies, external fonts or third-party JavaScript are used.

### Frame-policy limitation

A CSP delivered through a `<meta>` element cannot enforce `frame-ancestors`. GitHub Pages does not provide repository-controlled custom response headers, so this deployment does **not** claim HTTP-level clickjacking protection. The ignored directive is intentionally omitted to avoid a false security signal and browser console errors.

This is a low-impact limitation for the current read-only showcase because it has no authentication, session, payment, provider call or sensitive form state. If the experience moves to a configurable host, set response headers such as:

```http
Content-Security-Policy: frame-ancestors 'none'
X-Frame-Options: DENY
```

Never add provider API keys, backend secrets, `.env` files or live paid-provider calls to GitHub Pages. Client-side code and Pages artifacts are public.

## Review checklist

Before sharing the URL with a client:

- [ ] `ci` passes on Python 3.11, 3.12 and 3.13.
- [ ] `pages` build and deploy jobs pass.
- [ ] The home page loads without a path suffix.
- [ ] The cinematic story reversibly advances through `Atmosphere → Analyze → Place → Prove`.
- [ ] The cinematic frames remain explicitly labelled illustrative and separate from executable evidence.
- [ ] The static chapter sequence remains readable with reduced motion and with JavaScript disabled.
- [ ] Before/after slider and mask overlay work.
- [ ] Boundary Lab sample produces zero changed protected pixels.
- [ ] Visual Restyle Studio completes `Intent → Mask → Preview → Verify`.
- [ ] Spatial Design Studio completes `Brief → Locks → Placement → Variants → Handoff`.
- [ ] Product-plane handles and numeric coordinates work; invalid planes are not accepted.
- [ ] Variant selection reports zero protected drift and exports PNG, contact sheet and JSON manifest locally.
- [ ] Catalog-faithful and Generative Concept mode boundaries remain explicit.
- [ ] Studio paint/erase tools, structured prompt explanation and job timeline work.
- [ ] Custom image, mask and product assets remain local and produce downloadable artifacts.
- [ ] Browser developer tools show no outbound runtime requests after static assets load.
- [ ] Mobile navigation, dark/light theme, reduced transparency and reduced motion states work.
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
