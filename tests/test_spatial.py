import json
from io import BytesIO

import cv2
import numpy as np
import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from PIL import Image
from pydantic import ValidationError

from inpainting_poc.api import app
from inpainting_poc.imaging import ImageLimits, decode_image_rgb
from inpainting_poc.spatial import (
    DeterministicPlacementOrchestrator,
    PlacementSpec,
    SpatialDesignBrief,
    compile_spatial_brief,
)

ASSET_SHA256 = "a" * 64
VALID_CORNERS = [
    {"x": 0.20, "y": 0.48},
    {"x": 0.78, "y": 0.48},
    {"x": 0.90, "y": 0.91},
    {"x": 0.08, "y": 0.91},
]


def png_bytes(array: np.ndarray, mode: str) -> bytes:
    output = BytesIO()
    Image.fromarray(array, mode=mode).save(output, format="PNG")
    return output.getvalue()


def placement_brief() -> SpatialDesignBrief:
    return SpatialDesignBrief(
        project_context="hospitality-lounge",
        intervention_mode="catalog-faithful-placement",
        objective=(
            "Anchor the hospitality lounge with the supplied hero carpet while keeping the "
            "architecture, openings, and existing furniture exact."
        ),
        atmosphere="mineral",
        material_cues=["limewash", "bronze"],
        preserve=["architecture-shell", "openings", "existing-furniture"],
        allowed_changes=["wall-tone-polygons", "hero-floor-plane"],
        hero_asset={
            "name": "Contour 01",
            "sha256": ASSET_SHA256,
            "mutation_policy": "transform-only",
        },
    )


def test_spatial_brief_compiler_is_deterministic_and_mode_explicit() -> None:
    first = compile_spatial_brief(placement_brief())
    second = compile_spatial_brief(placement_brief())

    assert first == second
    assert first.compiler_version == "spatial-brief-v1"
    assert first.brief_sha256
    assert "Do not regenerate, recolor, retouch, relight, or reinterpret" in first.provider_guidance
    assert ASSET_SHA256 in " ".join(first.decision_contract)
    assert "does not prove client compatibility" in first.claim_boundary


def test_spatial_brief_rejects_cross_mode_fidelity_claims() -> None:
    with pytest.raises(ValidationError, match="must not carry a catalog-fidelity asset claim"):
        SpatialDesignBrief(
            intervention_mode="generative-concept",
            objective=(
                "Explore the authorized wall surface for an editorial hospitality atmosphere."
            ),
            preserve=["architecture-shell"],
            allowed_changes=["wall-tone-polygons"],
            hero_asset={"name": "Misleading asset", "sha256": ASSET_SHA256},
        )


def test_placement_spec_rejects_self_crossing_and_tiny_planes() -> None:
    with pytest.raises(ValidationError, match="above the bottom edge"):
        PlacementSpec(
            corners=[VALID_CORNERS[0], VALID_CORNERS[2], VALID_CORNERS[1], VALID_CORNERS[3]]
        )
    with pytest.raises(ValidationError, match="minimum authorized area"):
        PlacementSpec(
            corners=[
                {"x": 0.40, "y": 0.50},
                {"x": 0.51, "y": 0.50},
                {"x": 0.52, "y": 0.60},
                {"x": 0.39, "y": 0.60},
            ]
        )


def test_deterministic_placement_preserves_every_protected_pixel() -> None:
    source = np.full((120, 180, 3), [112, 124, 121], dtype=np.uint8)
    source[:, :35] = [68, 78, 76]
    asset = np.zeros((44, 72, 4), dtype=np.uint8)
    asset[..., :3] = [192, 113, 67]
    asset[..., 3] = 255
    cv2.circle(asset, (36, 22), 13, (228, 196, 128, 255), thickness=-1)
    spec = PlacementSpec(corners=VALID_CORNERS, shadow_strength=0.18)
    limits = ImageLimits(max_bytes=1_000_000, max_pixels=100_000)
    orchestrator = DeterministicPlacementOrchestrator(limits)

    output = orchestrator.run(
        source_bytes=png_bytes(source, "RGB"),
        asset_bytes=png_bytes(asset, "RGBA"),
        spec=spec,
    )
    decoded = decode_image_rgb(output.png_bytes, limits)
    quad = np.rint(
        np.asarray(
            [[point.x * 179, point.y * 119] for point in spec.corners],
            dtype=np.float32,
        )
    ).astype(np.int32)
    authorization = np.zeros(source.shape[:2], dtype=np.uint8)
    cv2.fillConvexPoly(authorization, quad, 255)

    assert np.array_equal(decoded[authorization == 0], source[authorization == 0])
    assert np.any(decoded[authorization > 0] != source[authorization > 0])
    assert output.proof.protected_pixel_drift == 0
    assert output.proof.changed_authorized_pixels > 0
    assert output.proof.source_sha256 != output.proof.output_sha256
    assert len(output.proof.transform) == 9


async def test_v3_spatial_brief_and_placement_endpoints(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("INPAINT_PROVIDER", "demo")
    source = np.full((96, 144, 3), [116, 126, 121], dtype=np.uint8)
    asset = np.zeros((36, 58, 4), dtype=np.uint8)
    asset[..., :3] = [38, 73, 75]
    asset[..., 3] = 255
    cv2.rectangle(asset, (8, 8), (50, 28), (217, 179, 105, 255), thickness=3)
    placement = json.dumps({"corners": VALID_CORNERS, "shadow_strength": 0.15})

    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client,
    ):
        compiled = await client.post("/poc/v3/briefs/compile", json=placement_brief().model_dump())
        preview = await client.post(
            "/poc/v3/placements/preview",
            files={
                "source": ("lounge.png", png_bytes(source, "RGB"), "image/png"),
                "asset": ("carpet.png", png_bytes(asset, "RGBA"), "image/png"),
            },
            data={"placement": placement},
        )

    assert compiled.status_code == 200
    assert compiled.json()["compiler_version"] == "spatial-brief-v1"
    assert preview.status_code == 200
    assert preview.headers["content-type"] == "image/png"
    assert preview.headers["cache-control"] == "no-store"
    assert preview.headers["x-poc-renderer"] == "placement-v1"
    assert preview.headers["x-poc-protected-drift"] == "0"
    proof = json.loads(preview.headers["x-poc-placement-proof"])
    assert proof["protected_pixel_drift"] == 0
    assert proof["asset_sha256"] == preview.headers["x-poc-asset-sha256"]
