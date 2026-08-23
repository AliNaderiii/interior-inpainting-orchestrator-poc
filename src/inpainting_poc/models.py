from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    request_id: str


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"] = "ok"
    provider: str


@dataclass(frozen=True, slots=True)
class MaskArtifact:
    hard: np.ndarray
    alpha: np.ndarray
    coverage_ratio: float


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    image_rgb: np.ndarray
    hard_mask: np.ndarray
    prompt: str


@dataclass(frozen=True, slots=True)
class ProviderResult:
    image_rgb: np.ndarray
    provider: str
    model: str
    request_id: str | None = None


class InpaintMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    mask_coverage: float = Field(ge=0, le=1)
    input_sha256: str
    output_sha256: str
