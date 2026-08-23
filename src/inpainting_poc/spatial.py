from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Literal

import cv2
import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .errors import InvalidImageError, InvalidIntentError
from .imaging import ImageLimits, decode_image_rgb, decode_image_rgba, encode_png, sha256_hex

SpatialMode = Literal["catalog-faithful-placement", "generative-concept"]
ProjectContext = Literal["boutique-hotel", "hospitality-lounge", "retail-gallery"]
Atmosphere = Literal["ember", "mineral", "nocturne"]
MaterialCue = Literal["boucle", "bronze", "limewash", "smoked-oak"]
PreservationLock = Literal["architecture-shell", "existing-furniture", "openings"]
AllowedChange = Literal["hero-floor-plane", "wall-tone-polygons"]

_HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SPACE = re.compile(r"\s+")
SPATIAL_BRIEF_COMPILER_VERSION: Literal["spatial-brief-v1"] = "spatial-brief-v1"
PLACEMENT_RENDERER_VERSION: Literal["placement-v1"] = "placement-v1"


class HeroAssetRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=64)
    sha256: str
    mutation_policy: Literal["transform-only"] = "transform-only"

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        clean = _SPACE.sub(" ", value).strip()
        if not clean:
            raise ValueError("Asset name must contain visible characters")
        return clean

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        normalized = value.lower()
        if not _HEX_SHA256.fullmatch(normalized):
            raise ValueError("Asset SHA-256 must contain 64 lowercase hexadecimal characters")
        return normalized


class SpatialDesignBrief(BaseModel):
    """Provisional spatial decision contract; not a client-owned production schema."""

    model_config = ConfigDict(extra="forbid")

    project_context: ProjectContext = "hospitality-lounge"
    intervention_mode: SpatialMode
    objective: str = Field(min_length=20, max_length=240)
    atmosphere: Atmosphere = "mineral"
    material_cues: list[MaterialCue] = Field(default_factory=list, max_length=4)
    preserve: list[PreservationLock] = Field(default_factory=list, max_length=3)
    allowed_changes: list[AllowedChange] = Field(default_factory=list, min_length=1, max_length=2)
    hero_asset: HeroAssetRef | None = None

    @field_validator("objective")
    @classmethod
    def normalize_objective(cls, value: str) -> str:
        clean = _SPACE.sub(" ", value).strip()
        if not 20 <= len(clean) <= 240:
            raise ValueError("Objective must contain 20 to 240 normalized characters")
        return clean

    @field_validator("material_cues", "preserve", "allowed_changes")
    @classmethod
    def deduplicate_lists(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))

    @model_validator(mode="after")
    def validate_mode_boundary(self) -> SpatialDesignBrief:
        if self.intervention_mode == "catalog-faithful-placement":
            if self.hero_asset is None:
                raise ValueError("Catalog-faithful placement requires a hashed hero asset")
            if "hero-floor-plane" not in self.allowed_changes:
                raise ValueError(
                    "Catalog-faithful placement requires hero-floor-plane authorization"
                )
        elif self.hero_asset is not None:
            raise ValueError("Generative concept must not carry a catalog-fidelity asset claim")
        return self


class CompiledSpatialBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")

    compiler_version: Literal["spatial-brief-v1"] = SPATIAL_BRIEF_COMPILER_VERSION
    brief_sha256: str
    provider_guidance: str
    decision_contract: list[str]
    claim_boundary: str


def compile_spatial_brief(brief: SpatialDesignBrief) -> CompiledSpatialBrief:
    """Compile a canonical brief into explicit guidance and non-negotiable decisions."""

    decision_contract = [
        f"Project context: {brief.project_context}",
        f"Intervention mode: {brief.intervention_mode}",
        f"Preserve exactly: {', '.join(brief.preserve) if brief.preserve else 'no declared locks'}",
        f"Allowed change regions: {', '.join(brief.allowed_changes)}",
    ]
    if brief.intervention_mode == "catalog-faithful-placement":
        assert brief.hero_asset is not None
        decision_contract.append(
            f"Hero asset {brief.hero_asset.name} is immutable source material identified by "
            f"SHA-256 {brief.hero_asset.sha256}"
        )
        mode_guidance = (
            "Place the supplied catalog raster on the authorized hero floor plane. "
            "Do not regenerate, recolor, retouch, relight, or reinterpret product pixels. "
            "Only projective geometry, bounded contact shadow, and foreground occlusion "
            "order are allowed."
        )
    else:
        decision_contract.append("Do not make catalog-fidelity or specified-product claims")
        mode_guidance = (
            "Develop a generative surface concept only inside the authorized wall-tone polygons. "
            "Treat the result as exploratory art direction, not product-fidelity evidence."
        )

    materials = (
        ", ".join(brief.material_cues) if brief.material_cues else "no additional material cue"
    )
    provider_guidance = (
        f"{mode_guidance} Objective: {brief.objective}. "
        f"Atmosphere: {brief.atmosphere}. Material cues: {materials}. "
        "The declared locks and allowed-change regions are the final geometric authority."
    )
    canonical = json.dumps(brief.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return CompiledSpatialBrief(
        brief_sha256=hashlib.sha256(canonical.encode()).hexdigest(),
        provider_guidance=provider_guidance,
        decision_contract=decision_contract,
        claim_boundary=(
            "Provisional reference guidance only; it does not prove client compatibility, "
            "live model quality, photometric material accuracy, or production readiness."
        ),
    )


class NormalizedPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)


class PlacementSpec(BaseModel):
    """Corner order is top-left, top-right, bottom-right, bottom-left."""

    model_config = ConfigDict(extra="forbid")

    corners: list[NormalizedPoint] = Field(min_length=4, max_length=4)
    shadow_strength: float = Field(default=0.18, ge=0.0, le=0.35)

    @model_validator(mode="after")
    def validate_convex_floor_plane(self) -> PlacementSpec:
        points = [(point.x, point.y) for point in self.corners]
        if not (points[0][0] < points[1][0] and points[3][0] < points[2][0]):
            raise ValueError("Placement corners must follow TL, TR, BR, BL order")
        if not (max(points[0][1], points[1][1]) < min(points[2][1], points[3][1])):
            raise ValueError("Top placement edge must remain above the bottom edge")

        signed_crosses: list[float] = []
        for index in range(4):
            a = points[index]
            b = points[(index + 1) % 4]
            c = points[(index + 2) % 4]
            signed_crosses.append((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]))
        if any(abs(value) < 1e-4 for value in signed_crosses):
            raise ValueError("Placement plane is degenerate")
        if not (
            all(value > 0 for value in signed_crosses) or all(value < 0 for value in signed_crosses)
        ):
            raise ValueError("Placement plane must be convex and non-self-intersecting")

        area = 0.0
        for index in range(4):
            x1, y1 = points[index]
            x2, y2 = points[(index + 1) % 4]
            area += x1 * y2 - x2 * y1
        if abs(area) / 2 < 0.035:
            raise ValueError("Placement plane is below the minimum authorized area")
        return self


class PlacementProof(BaseModel):
    model_config = ConfigDict(extra="forbid")

    renderer_version: Literal["placement-v1"] = PLACEMENT_RENDERER_VERSION
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    authorized_coverage: float = Field(gt=0, lt=1)
    protected_pixel_count: int = Field(ge=0)
    protected_pixel_drift: int = Field(ge=0)
    changed_authorized_pixels: int = Field(ge=0)
    source_sha256: str
    asset_sha256: str
    output_sha256: str
    transform: list[float] = Field(min_length=9, max_length=9)
    claim_boundary: str


@dataclass(frozen=True, slots=True)
class PlacementOutput:
    png_bytes: bytes
    proof: PlacementProof


class DeterministicPlacementOrchestrator:
    """Bounded projective placement with authoritative protected-pixel restoration."""

    def __init__(self, limits: ImageLimits) -> None:
        self._limits = limits

    def run(
        self,
        *,
        source_bytes: bytes,
        asset_bytes: bytes,
        spec: PlacementSpec,
    ) -> PlacementOutput:
        source = decode_image_rgb(source_bytes, self._limits)
        asset = decode_image_rgba(asset_bytes, self._limits)
        if asset.shape[0] < 2 or asset.shape[1] < 2:
            raise InvalidImageError("Product asset must be at least 2 by 2 pixels")

        height, width = source.shape[:2]
        asset_height, asset_width = asset.shape[:2]
        source_quad = np.asarray(
            [
                [0, 0],
                [asset_width - 1, 0],
                [asset_width - 1, asset_height - 1],
                [0, asset_height - 1],
            ],
            dtype=np.float32,
        )
        destination_quad = np.asarray(
            [[point.x * (width - 1), point.y * (height - 1)] for point in spec.corners],
            dtype=np.float32,
        )
        transform = np.asarray(cv2.getPerspectiveTransform(source_quad, destination_quad))

        warped_rgb = np.asarray(
            cv2.warpPerspective(
                asset[..., :3],
                transform,
                (width, height),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(0, 0, 0),
            ),
            dtype=np.uint8,
        )
        warped_alpha = (
            np.asarray(
                cv2.warpPerspective(
                    asset[..., 3],
                    transform,
                    (width, height),
                    flags=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_CONSTANT,
                    borderValue=0,
                ),
                dtype=np.uint8,
            ).astype(np.float32)
            / 255.0
        )

        authorization = np.zeros((height, width), dtype=np.uint8)
        cv2.fillConvexPoly(authorization, np.rint(destination_quad).astype(np.int32), 255)
        source_float = source.astype(np.float32)
        composed = source_float.copy()

        if spec.shadow_strength > 0:
            shadow = (
                cv2.GaussianBlur(
                    (warped_alpha * 255.0).astype(np.uint8),
                    (0, 0),
                    sigmaX=max(1.0, min(width, height) / 220.0),
                    borderType=cv2.BORDER_REPLICATE,
                ).astype(np.float32)
                / 255.0
            )
            shadow *= authorization.astype(np.float32) / 255.0
            shadow_alpha = shadow[..., None] * spec.shadow_strength
            composed *= 1.0 - shadow_alpha * 0.52

        alpha = warped_alpha[..., None]
        composed = composed * (1.0 - alpha) + warped_rgb.astype(np.float32) * alpha
        output = np.rint(composed).clip(0, 255).astype(np.uint8)

        protected = authorization == 0
        output[protected] = source[protected]
        protected_drift = int(
            np.count_nonzero(np.any(output[protected] != source[protected], axis=1))
        )
        if protected_drift != 0:
            raise InvalidImageError("Protected-pixel restoration invariant failed")
        changed_authorized = int(
            np.count_nonzero(np.any(output[authorization > 0] != source[authorization > 0], axis=1))
        )
        if changed_authorized == 0:
            raise InvalidImageError("Product placement produced no changed authorized pixels")

        encoded = encode_png(output)
        authorized_pixels = int(np.count_nonzero(authorization))
        return PlacementOutput(
            png_bytes=encoded,
            proof=PlacementProof(
                width=width,
                height=height,
                authorized_coverage=authorized_pixels / float(width * height),
                protected_pixel_count=int(width * height - authorized_pixels),
                protected_pixel_drift=protected_drift,
                changed_authorized_pixels=changed_authorized,
                source_sha256=sha256_hex(source_bytes),
                asset_sha256=sha256_hex(asset_bytes),
                output_sha256=sha256_hex(encoded),
                transform=[round(float(value), 8) for value in transform.reshape(-1)],
                claim_boundary=(
                    "Transform-only raster placement evidence; not a manufacturing, photometric, "
                    "client-contract, or live-model quality certification."
                ),
            ),
        )


def parse_placement_spec(value: str) -> PlacementSpec:
    try:
        return PlacementSpec.model_validate_json(value)
    except (ValueError, TypeError) as exc:
        raise InvalidIntentError("Placement spec does not match the provisional v3 schema") from exc
