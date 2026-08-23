# Release v0.2.0 — Job API and Visual Restyle Studio

## Release position

`v0.2.0` is a public reference-PoC release. It demonstrates a controlled product workflow and a versioned asynchronous API without claiming production durability, undisclosed client-contract compatibility or live-model visual quality.

## Highlights

- **Structured design direction:** deterministic, explainable `StyleIntent → prompt` compilation with canonical SHA-256 identity.
- **Job-shaped API:** bounded acceptance, polling, result retrieval, idempotent replay and safe failure states.
- **Compatibility:** the synchronous `/poc/v1/inpaint` route remains available.
- **Visual Restyle Studio:** an offline `Intent → Mask → Preview → Verify` browser experience.
- **Boundary proof:** exact restoration of every original pixel outside the authorized hard mask.
- **Security:** bounded input decoding, provider URL allowlisting, no-network Pages runtime and full-SHA GitHub Action pins.

## Public verification

| Evidence | Result |
|---|---|
| Source baseline | `12b2b9f48ec06be7448afd2385f2e925e445abf9` |
| CI | [run 32639806882](https://github.com/AliNaderiii/interior-inpainting-orchestrator-poc/actions/runs/32639806882) — PASS |
| Pages | [run 32639806902](https://github.com/AliNaderiii/interior-inpainting-orchestrator-poc/actions/runs/32639806902) — PASS |
| Python matrix | 3.11 / 3.12 / 3.13 — 24 tests each |
| Hosted Studio | [open](https://alinaderiii.github.io/interior-inpainting-orchestrator-poc/studio.html) |
| Protected-pixel browser proof | 534,801 protected; 0 drift |

## API surface

```text
GET  /health/live
GET  /health/ready
POST /poc/v1/inpaint
POST /poc/v2/intents/compile
POST /poc/v2/jobs
GET  /poc/v2/jobs/{job_id}
GET  /poc/v2/jobs/{job_id}/result
```

The machine-readable contract is committed at [`openapi-v0.2.0.json`](openapi-v0.2.0.json).

## Explicit non-claims

This release does not claim:

- a durable or distributed production queue;
- authentication, authorization or tenant isolation;
- compatibility with client schemas that have not been supplied;
- live FLUX/BFL quality, latency or cost acceptance;
- a production retention, privacy or observability design.

## Upgrade and rollback

No migration is required for v1 PoC consumers. The v2 manager is non-durable and starts empty with each process. Reverting the v0.2.0 phase commits restores the v0.1.0 surface; no persistent records require rollback.

## Review material

- [API v2 guide](API_V2.md)
- [GitHub Pages boundary](GITHUB_PAGES.md)
- [Phase 02 implementation report](../reports/PHASE_02_JOB_API_AND_VISUAL_STUDIO.md)
- [Public release verification](../reports/PHASE_02_PUBLIC_RELEASE_VERIFICATION.md)
- [Changelog](../CHANGELOG.md)
