# PoC Validation Report

- Validation date (UTC): 2026-08-23T10:48:47Z
- Status: **PASS_WITH_RISK — pre-contract reference PoC only**
- Public backend baseline commit: `346cd5260ac30df587f76419b59d2fbe6ab1ad2f`.
- Environment: Python 3.13.14, Ruff 0.16.4, mypy 1.20.2, pytest 9.0.3.
- This report preserves the eight-test backend baseline evidence. The later GitHub Pages extension adds four static-site/security tests; see `SHOWCASE_VALIDATION_REPORT.md`.

## Verified

| Check | Result | Evidence |
|---|---|---|
| Ruff format | PASS | `docs/validation/ruff-format.txt` |
| Ruff lint | PASS | `docs/validation/ruff-check.txt` |
| Strict mypy | PASS, 11 source files | `docs/validation/mypy.txt` |
| Unit/API/provider-protocol tests | PASS, 8 tests | `docs/validation/pytest.txt` |
| Python compileall | PASS | command recorded below |
| Protected pixel proof | PASS, 0 changed protected pixels | `docs/validation/protected-pixel-proof.txt` |
| Limited secret-marker review | PASS, 0 candidates | `docs/validation/secret-name-review.txt` |

## Reproducible commands

```bash
ruff format --check .
ruff check .
mypy
pytest -q -m 'not live_provider'
python -m compileall -q src tests scripts
```

## Explicitly unverified

- No live BFL/FLUX.1 Fill request was made; provider behavior is tested with `httpx.MockTransport` only.
- No Gemini/OpenAI Vision adapter exists because the client JSON Schema has not been supplied.
- No client OpenAPI contract compatibility is claimed.
- No Docker image build/scan was run in this environment.
- No release-grade SCA/SAST/SBOM or Git-history secret scan was run.
- No authentication, tenant isolation, durable idempotency, object storage, queue or production deployment is implemented.
- The visual artifact is procedural and non-generative; it is not an AI-quality benchmark.

## Risks carried forward

1. Provider endpoint/model/account/region/retention must be revalidated after client access.
2. Client contract may require different mask semantics, upload format and async job behavior.
3. The Docker base image tag must be pinned to a verified digest during release engineering.
4. Full security/operations controls depend on the client architecture and are not part of this PoC.

## Gate decision

The backend baseline is suitable for a public engineering portfolio and has passed live-repository CI review. The later static showcase remains subject to its separate GitHub Pages deployment gate. Neither surface is suitable for production deployment or a claim of completed client scope.
