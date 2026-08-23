from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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


class ReadyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ready"] = "ready"
    provider: str
    active_jobs: int = Field(ge=0)
    max_records: int = Field(gt=0)
    max_concurrency: int = Field(gt=0)


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


JobStatus = Literal["queued", "running", "succeeded", "failed", "expired"]


class JobLinks(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    result: str


class JobAccepted(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: JobStatus
    reused: bool
    compiled_prompt: str
    intent_sha256: str | None = None
    links: JobLinks


class JobFailure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class JobView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    metadata: InpaintMetadata | None = None
    failure: JobFailure | None = None
    links: JobLinks
