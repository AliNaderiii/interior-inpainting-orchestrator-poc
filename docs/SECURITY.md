# Security Notes

## Implemented PoC controls

- No user-supplied remote URL fetch at the public endpoint.
- Encoded byte and decoded pixel limits.
- Only JPEG, PNG and WebP single-frame inputs.
- Exact mask/image dimension match.
- Empty and excessive masks rejected.
- Metadata stripped from PNG output.
- Provider API key never sent to signed result host.
- Poll and result URLs require HTTPS, approved host, no credentials and standard TLS port.
- Result download is streamed with a hard byte limit.
- Prompt and variant settings are bounded.
- Output uses `Cache-Control: no-store`.

## Remaining before production

- Client authn/authz and tenant ownership.
- Rate limits, durable idempotency and paid-cost quotas.
- SSRF defense with controlled DNS/IP resolution if any client contract permits URLs.
- Durable jobs, storage, retention and deletion.
- Provider retention/training/account review.
- Secret manager/workload identity.
- SAST/SCA/container/IaC/SBOM evidence on release commit.
- Threat-model and penetration testing against client architecture.
- Content policy and abuse response.

Report vulnerabilities privately. Do not attach private images, credentials or signed URLs to issues.
