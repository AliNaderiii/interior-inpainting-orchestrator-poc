from __future__ import annotations

import json
import re
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, cast

from fastapi import FastAPI, File, Form, Header, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .config import Settings
from .errors import (
    IdempotencyConflictError,
    InpaintingError,
    InvalidImageError,
    InvalidIntentError,
    JobCapacityError,
    JobExpiredError,
    JobNotFoundError,
    JobNotReadyError,
)
from .imaging import ImageLimits
from .intent import CompiledIntent, StyleIntent, compile_intent
from .jobs import InMemoryJobManager
from .models import ErrorBody, HealthResponse, JobAccepted, JobView, ReadyResponse
from .orchestrator import InpaintingOrchestrator
from .providers.base import InpaintingProvider
from .providers.bfl import BFLFluxFillProvider
from .providers.demo import DeterministicDemoProvider

_ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/octet-stream",
}
_IDEMPOTENCY_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")


def _build_provider(settings: Settings) -> InpaintingProvider:
    if settings.provider == "demo":
        return DeterministicDemoProvider()
    return BFLFluxFillProvider(
        api_key=settings.bfl_api_key or "",
        result_hosts=settings.bfl_result_hosts,
        deadline_seconds=settings.provider_deadline_seconds,
        max_pixels=settings.max_pixels,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings.from_env()
    settings.validate()
    provider = _build_provider(settings)
    orchestrator = InpaintingOrchestrator(
        provider=provider,
        limits=ImageLimits(
            max_bytes=settings.max_upload_bytes,
            max_pixels=settings.max_pixels,
        ),
    )
    jobs = InMemoryJobManager(
        orchestrator,
        max_records=settings.job_max_records,
        max_concurrency=settings.job_max_concurrency,
        ttl_seconds=settings.job_ttl_seconds,
    )
    app.state.settings = settings
    app.state.provider = provider
    app.state.orchestrator = orchestrator
    app.state.jobs = jobs
    try:
        yield
    finally:
        await jobs.close()
        await provider.aclose()


app = FastAPI(
    title="Interior Inpainting Orchestrator — Reference PoC",
    version="0.2.0",
    description=(
        "Provisional controlled-inpainting API with deterministic local evidence, "
        "structured style intent and a bounded non-durable job lifecycle."
    ),
    lifespan=lifespan,
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id[:128]
    response = await call_next(request)
    response.headers["x-request-id"] = request.state.request_id
    return response


@app.exception_handler(InpaintingError)
async def domain_error_handler(request: Request, exc: InpaintingError) -> JSONResponse:
    status_code = 422
    if isinstance(exc, JobNotFoundError):
        status_code = 404
    elif isinstance(exc, (JobNotReadyError, IdempotencyConflictError)):
        status_code = 409
    elif isinstance(exc, JobExpiredError):
        status_code = 410
    elif isinstance(exc, JobCapacityError):
        status_code = 503
    body = ErrorBody(
        code=exc.__class__.__name__,
        message=str(exc),
        request_id=request.state.request_id,
    )
    headers = {"cache-control": "no-store"}
    if status_code == 503:
        headers["retry-after"] = "2"
    return JSONResponse(status_code=status_code, content=body.model_dump(), headers=headers)


@app.get("/health/live", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    return HealthResponse(provider=request.app.state.provider.name)


@app.get("/health/ready", response_model=ReadyResponse)
async def ready(request: Request) -> ReadyResponse:
    active, max_records, max_concurrency = await request.app.state.jobs.snapshot()
    return ReadyResponse(
        provider=request.app.state.provider.name,
        active_jobs=active,
        max_records=max_records,
        max_concurrency=max_concurrency,
    )


async def _read_bounded(upload: UploadFile, max_bytes: int) -> bytes:
    data = await upload.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise InvalidImageError("Upload exceeds the encoded byte limit")
    return data


def _validate_upload_types(image: UploadFile, mask: UploadFile) -> None:
    if image.content_type not in _ALLOWED_CONTENT_TYPES:
        raise InvalidImageError("Unsupported image upload content type")
    if mask.content_type not in _ALLOWED_CONTENT_TYPES:
        raise InvalidImageError("Unsupported mask upload content type")


def _parse_intent(value: str | None) -> StyleIntent | None:
    if value is None:
        return None
    try:
        return StyleIntent.model_validate_json(value)
    except (ValidationError, ValueError) as exc:
        raise InvalidIntentError("Style intent does not match the provisional schema") from exc


def _validate_idempotency_key(value: str | None) -> str | None:
    if value is None:
        return None
    if not _IDEMPOTENCY_KEY.fullmatch(value):
        raise InvalidIntentError("Idempotency-Key must contain 8-128 safe ASCII characters")
    return value


@app.post("/poc/v2/intents/compile", response_model=CompiledIntent, tags=["v2 jobs"])
async def compile_style_intent(request: Request, intent: StyleIntent) -> CompiledIntent:
    settings: Settings = request.app.state.settings
    return compile_intent(intent, max_chars=settings.max_prompt_chars)


@app.post(
    "/poc/v2/jobs",
    response_model=JobAccepted,
    status_code=202,
    tags=["v2 jobs"],
    responses={
        409: {"model": ErrorBody, "description": "Idempotency-Key payload conflict"},
        422: {"model": ErrorBody, "description": "Invalid upload, mask, prompt, or intent"},
        503: {"model": ErrorBody, "description": "Bounded job store is at capacity"},
    },
)
async def create_job(
    request: Request,
    response: Response,
    image: Annotated[UploadFile, File()],
    mask: Annotated[UploadFile, File()],
    prompt: Annotated[str | None, Form(max_length=1_000)] = None,
    intent: Annotated[str | None, Form(max_length=2_000)] = None,
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key", max_length=128),
    ] = None,
) -> JobAccepted:
    settings: Settings = request.app.state.settings
    _validate_upload_types(image, mask)
    image_bytes = await _read_bounded(image, settings.max_upload_bytes)
    mask_bytes = await _read_bounded(mask, settings.max_upload_bytes)
    style_intent = _parse_intent(intent)
    clean_prompt = " ".join((prompt or "").split())
    if style_intent is None and not clean_prompt:
        raise InvalidIntentError("A prompt or structured style intent is required")
    if len(clean_prompt) > settings.max_prompt_chars:
        raise InvalidIntentError("Prompt exceeds the configured character limit")

    compiled: CompiledIntent | None = None
    if style_intent is not None:
        compiled = compile_intent(
            style_intent,
            user_prompt=clean_prompt or None,
            max_chars=settings.max_prompt_chars,
        )
        final_prompt = compiled.prompt
    else:
        final_prompt = clean_prompt

    jobs = cast(InMemoryJobManager, request.app.state.jobs)
    accepted = await jobs.submit(
        image_bytes=image_bytes,
        mask_bytes=mask_bytes,
        compiled_prompt=final_prompt,
        intent_sha256=compiled.intent_sha256 if compiled else None,
        idempotency_key=_validate_idempotency_key(idempotency_key),
    )
    response.headers["location"] = accepted.links.status
    response.headers["cache-control"] = "no-store"
    response.headers["retry-after"] = "1"
    return accepted


@app.get(
    "/poc/v2/jobs/{job_id}",
    response_model=JobView,
    tags=["v2 jobs"],
    responses={404: {"model": ErrorBody}},
)
async def get_job(request: Request, job_id: str) -> JobView:
    jobs = cast(InMemoryJobManager, request.app.state.jobs)
    return await jobs.get_view(job_id)


@app.get(
    "/poc/v2/jobs/{job_id}/result",
    tags=["v2 jobs"],
    responses={
        200: {"content": {"image/png": {}}},
        404: {"model": ErrorBody},
        409: {"model": ErrorBody},
        410: {"model": ErrorBody},
    },
)
async def get_job_result(request: Request, job_id: str) -> Response:
    jobs = cast(InMemoryJobManager, request.app.state.jobs)
    png_bytes, metadata = await jobs.get_result(job_id)
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "x-poc-provider": metadata.provider,
            "x-poc-model": metadata.model,
            "x-poc-metadata": json.dumps(metadata.model_dump(), separators=(",", ":")),
            "cache-control": "no-store",
        },
    )


@app.post(
    "/poc/v1/inpaint",
    tags=["v1 synchronous"],
    responses={
        200: {"content": {"image/png": {}}},
        422: {"model": ErrorBody, "description": "Invalid upload, mask, or prompt"},
    },
)
async def inpaint(
    request: Request,
    image: Annotated[UploadFile, File()],
    mask: Annotated[UploadFile, File()],
    prompt: Annotated[str, Form(min_length=1, max_length=1_000)],
) -> Response:
    settings: Settings = request.app.state.settings
    if len(prompt) > settings.max_prompt_chars:
        raise InvalidImageError("Prompt exceeds the configured limit")
    _validate_upload_types(image, mask)
    image_bytes = await _read_bounded(image, settings.max_upload_bytes)
    mask_bytes = await _read_bounded(mask, settings.max_upload_bytes)
    output = await request.app.state.orchestrator.run(
        image_bytes=image_bytes,
        mask_bytes=mask_bytes,
        prompt=prompt,
    )
    metadata = output.metadata.model_dump()
    return Response(
        content=output.png_bytes,
        media_type="image/png",
        headers={
            "x-poc-provider": output.metadata.provider,
            "x-poc-model": output.metadata.model,
            "x-poc-metadata": json.dumps(metadata, separators=(",", ":")),
            "cache-control": "no-store",
        },
    )
