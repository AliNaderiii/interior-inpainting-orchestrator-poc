# PoC Scope and Boundaries

## Purpose

Demonstrate engineering readiness for deterministic image/mask handling, provider isolation and secure orchestration before client contracts are available.

## Included

- Provisional multipart FastAPI endpoint under `/poc/`.
- Strict byte/pixel/format checks.
- EXIF normalization and RGB canonicalization.
- White-edit/black-preserve mask processing.
- Inward feathering and exact protected-pixel restoration.
- Deterministic non-AI local provider.
- Optional BFL FLUX.1 Fill submit/poll/result adapter.
- Tests and CI baseline.

## Explicitly not claimed

- Compatibility with the client's finalized API contract.
- Production readiness.
- Vision-LLM implementation.
- Actual interior-staging quality from the deterministic demo.
- Account-level availability, quota or retention posture for any provider.
- Frontend scope.

## Conversion after award

1. Import and diff the client OpenAPI/schema baseline.
2. Run requirements and threat-model gates.
3. Replace `/poc/` contract with client-owned routes/models.
4. Confirm provider/model/account/region.
5. Add Vision structured-output adapter and evaluation set.
6. Integrate authorized storage, jobs, observability and deployment.
