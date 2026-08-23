# Provisional Spatial Design API — v3

**Status:** released v0.3.0 reference contract
**Compatibility:** v1 synchronous inpainting and v2 jobs remain available
**OpenAPI:** [`openapi-v0.3.0.json`](openapi-v0.3.0.json)

## Boundary

The v3 surface demonstrates two deterministic product capabilities:

1. compile a structured spatial brief into explicit provider guidance and a canonical SHA-256 identity;
2. place a supplied raster asset on a validated four-corner plane while restoring every pixel outside that plane from the source image.

This is a provisional reference schema. It is not a client-owned contract and does not prove live model quality, photometric material accuracy, manufacturing identity, C2PA conformance, production durability, or compatibility with an undisclosed API.

## Routes

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/poc/v3/briefs/compile` | Canonicalize and explain a `SpatialDesignBrief` |
| `POST` | `/poc/v3/placements/preview` | Deterministic transform-only product placement |

Existing v1/v2 routes remain documented in [`API_V2.md`](API_V2.md).

## Spatial brief compiler

### Request

```json
{
  "project_context": "hospitality-lounge",
  "intervention_mode": "catalog-faithful-placement",
  "objective": "Anchor the hospitality lounge with the supplied hero carpet while preserving the architecture and specified furniture.",
  "atmosphere": "mineral",
  "material_cues": ["limewash", "bronze"],
  "preserve": ["architecture-shell", "openings", "existing-furniture"],
  "allowed_changes": ["wall-tone-polygons", "hero-floor-plane"],
  "hero_asset": {
    "name": "Contour 01",
    "sha256": "e87dc919e59bf63d94f28e7c0578c237a724a294427f4f46fb0e6400a92d131d",
    "mutation_policy": "transform-only"
  }
}
```

### Mode boundary

- `catalog-faithful-placement` requires a hashed `hero_asset` and `hero-floor-plane` authorization.
- `generative-concept` rejects a `hero_asset` because attaching catalog-fidelity identity to a generative concept would be misleading.
- Compiler output always includes an explicit claim boundary.

### Response

The response contains:

- `compiler_version: spatial-brief-v1`;
- `brief_sha256` over canonical sorted JSON;
- `provider_guidance` with mode-specific constraints;
- ordered `decision_contract` statements;
- `claim_boundary`.

The compiler does not call a model.

## Deterministic product placement

`POST /poc/v3/placements/preview` accepts multipart fields:

- `source`: JPEG, PNG, or WebP scene raster;
- `asset`: JPEG, PNG, or WebP product raster; PNG/WebP alpha is preserved;
- `placement`: JSON-encoded `PlacementSpec`.

The same configured encoded-byte and decoded-pixel limits used by the inpainting pipeline apply to both rasters.

### Placement specification

Corner order is strict: top-left, top-right, bottom-right, bottom-left.

```json
{
  "corners": [
    {"x": 0.245, "y": 0.635},
    {"x": 0.790, "y": 0.635},
    {"x": 0.920, "y": 0.930},
    {"x": 0.105, "y": 0.930}
  ],
  "shadow_strength": 0.18
}
```

Coordinates are normalized to `[0, 1]`. The validator rejects:

- values outside scene bounds;
- incorrect corner order;
- top edges below bottom edges;
- degenerate planes;
- self-intersecting or non-convex planes;
- planes smaller than the minimum normalized area;
- shadow strength outside `[0, 0.35]`.

### Rendering invariant

The renderer:

1. decodes both images under explicit resource bounds;
2. computes a projective transform from the complete product raster to the destination plane;
3. warps RGB and alpha separately;
4. applies a bounded contact shadow inside the authorized plane;
5. alpha-composites the asset;
6. restores the source raster exactly wherever the destination authorization is black;
7. calculates proof metrics and returns a metadata-stripped PNG.

The postcondition is:

```text
output[protected] == source[protected]
```

A non-zero protected drift raises a domain error rather than returning the raster.

### Response headers

| Header | Meaning |
|---|---|
| `x-poc-renderer` | deterministic renderer version (`placement-v1`) |
| `x-poc-protected-drift` | changed protected pixels; must be `0` |
| `x-poc-asset-sha256` | SHA-256 of encoded asset input |
| `x-poc-placement-proof` | compact JSON proof record |
| `cache-control` | `no-store` |
| `x-request-id` | request correlation identifier |

The proof record includes source/asset/output hashes, transform matrix, authorized coverage, protected count, changed authorized count, and an explicit claim boundary.

## Security and production gaps

The reference API intentionally does not include authentication, tenant authorization, persistent object storage, durable queues, audit retention, distributed rate limiting, provider spend controls, automatic segmentation/depth, malware scanning, or client-specific policy. These remain pre-production gates.
