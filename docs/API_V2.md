# Job API and Style Intent — Reference Contract v0.2.0

## Status and boundary

This is a provisional reference contract. It demonstrates a versioned asynchronous workflow while preserving `POST /poc/v1/inpaint`. It is not a claim of compatibility with an undisclosed client contract.

The v2 manager is bounded, in-memory and non-durable. A process restart loses every job and result. A production implementation requires an approved queue, persistence model, authentication/authorization design, rate limits, observability and deployment topology.

## Routes

| Method | Path | Success | Notes |
|---|---|---:|---|
| `POST` | `/poc/v2/intents/compile` | `200` | JSON `StyleIntent` to deterministic prompt |
| `POST` | `/poc/v2/jobs` | `202` | Multipart job acceptance |
| `GET` | `/poc/v2/jobs/{job_id}` | `200` | Poll status and metadata |
| `GET` | `/poc/v2/jobs/{job_id}/result` | `200 image/png` | Available only after success |
| `GET` | `/health/ready` | `200` | Provider and bounded-capacity snapshot |

The machine-readable contract is [`openapi-v0.2.0.json`](openapi-v0.2.0.json).

## StyleIntent

```json
{
  "style": "japandi",
  "room_type": "living-room",
  "palette": ["#D8C8AA", "#6D7163"],
  "materials": ["wood", "stone"],
  "preserve_semantics": ["window frames", "existing floor"],
  "notes": "Keep finishes matte and restrained."
}
```

Controlled values:

- `style`: `contemporary`, `industrial`, `japandi`, `modern-calm`, `scandinavian`, `warm-minimal`;
- `room_type`: `bedroom`, `dining-room`, `home-office`, `kitchen`, `living-room`;
- `materials`: `concrete`, `glass`, `metal`, `plaster`, `stone`, `textile`, `wood`;
- `palette`: up to five `#RRGGBB` colors;
- `materials`: up to four values;
- `preserve_semantics`: up to six normalized labels, each 2–60 characters;
- `notes`: optional, normalized and limited to 240 characters;
- unknown fields are rejected.

Compiler `intent-v1` returns the compiled prompt, each explainable segment and a SHA-256 hash of the canonical intent. It is deterministic and does not call a language model.

> `preserve_semantics` affects prompt meaning only. It cannot authorize or protect geometry. The aligned hard mask and exact final compositing remain authoritative.

## Compile an intent

```bash
curl --fail-with-body \
  -H 'Content-Type: application/json' \
  --data '{"style":"japandi","room_type":"living-room","materials":["wood","stone"]}' \
  http://localhost:8000/poc/v2/intents/compile
```

## Submit a job

```bash
curl --fail-with-body \
  -H 'Idempotency-Key: room-edit-0001' \
  -F 'image=@room.png;type=image/png' \
  -F 'mask=@mask.png;type=image/png' \
  -F 'intent={"style":"japandi","room_type":"living-room","materials":["wood","stone"]}' \
  -F 'prompt=Keep the material transition quiet' \
  http://localhost:8000/poc/v2/jobs
```

At least one of `intent` or `prompt` is required. `intent` is a JSON-encoded multipart text field. The optional `Idempotency-Key` must contain 8–128 safe ASCII characters.

Representative acceptance response:

```json
{
  "job_id": "7f00d937-d473-4961-9620-b65aec3732cb",
  "status": "queued",
  "reused": false,
  "compiled_prompt": "Restyle the authorized region ...",
  "intent_sha256": "e7f0...",
  "links": {
    "status": "/poc/v2/jobs/7f00d937-d473-4961-9620-b65aec3732cb",
    "result": "/poc/v2/jobs/7f00d937-d473-4961-9620-b65aec3732cb/result"
  }
}
```

The service also sets:

- `Location`: relative status URL;
- `Retry-After: 1`;
- `Cache-Control: no-store`;
- `X-Request-ID`: supplied safe request identifier or a generated UUID.

## Poll and retrieve

```bash
curl --fail-with-body http://localhost:8000/poc/v2/jobs/JOB_ID
curl --fail-with-body --output result.png http://localhost:8000/poc/v2/jobs/JOB_ID/result
```

Lifecycle:

```text
queued → running → succeeded | failed → expired
```

A failed job exposes a safe domain failure. Unexpected exceptions are logged server-side and returned as `InternalJobError` without internal details.

## Idempotency

The fingerprint covers encoded image bytes, mask bytes and the final compiled prompt.

- Same key + same fingerprint: the existing job is returned with `reused: true`.
- Same key + different fingerprint: `409 IdempotencyConflictError`.
- No key: each accepted request creates a distinct job.
- Keys disappear when expired records are purged or the process restarts.

This is reference behavior, not a durable cross-process idempotency guarantee.

## Error taxonomy

| HTTP | Code | Meaning |
|---:|---|---|
| `404` | `JobNotFoundError` | Unknown or purged job identifier |
| `409` | `JobNotReadyError` | Result requested before success |
| `409` | `IdempotencyConflictError` | Key reused with different payload |
| `410` | `JobExpiredError` | Result TTL elapsed |
| `422` | image/mask/intent domain code | Invalid or unsafe input |
| `503` | `JobCapacityError` | Bounded store unavailable or full |

Domain error responses contain only `code`, `message` and `request_id`; they use `Cache-Control: no-store`. Capacity responses add `Retry-After: 2`.

## Default resource controls

| Environment variable | Default | Purpose |
|---|---:|---|
| `MAX_UPLOAD_BYTES` | `10485760` | Encoded limit applied independently to image and mask |
| `MAX_PIXELS` | `20000000` | Decoded geometry limit |
| `MAX_PROMPT_CHARS` | `1000` | Final compiled prompt budget |
| `JOB_MAX_RECORDS` | `32` | Maximum in-memory records |
| `JOB_MAX_CONCURRENCY` | `2` | Maximum concurrent executions |
| `JOB_TTL_SECONDS` | `900` | Record/result lifetime from acceptance |

See [`.env.example`](../.env.example) for the full non-secret configuration template.
