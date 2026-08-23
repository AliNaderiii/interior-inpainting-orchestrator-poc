from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from .config import Settings
from .errors import InpaintingError
from .imaging import ImageLimits
from .models import ErrorBody, HealthResponse
from .orchestrator import InpaintingOrchestrator
from .providers.base import InpaintingProvider
from .providers.bfl import BFLFluxFillProvider
from .providers.demo import DeterministicDemoProvider


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
    app.state.settings = settings
    app.state.provider = provider
    app.state.orchestrator = InpaintingOrchestrator(
        provider=provider,
        limits=ImageLimits(
            max_bytes=settings.max_upload_bytes,
            max_pixels=settings.max_pixels,
        ),
    )
    try:
        yield
    finally:
        await provider.aclose()


app = FastAPI(
    title="Interior Inpainting Orchestrator — Reference PoC",
    version="0.1.0",
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
    body = ErrorBody(
        code=exc.__class__.__name__,
        message=str(exc),
        request_id=request.state.request_id,
    )
    return JSONResponse(status_code=422, content=body.model_dump())


@app.get("/health/live", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    return HealthResponse(provider=request.app.state.provider.name)


async def _read_bounded(upload: UploadFile, max_bytes: int) -> bytes:
    data = await upload.read(max_bytes + 1)
    if len(data) > max_bytes:
        from .errors import InvalidImageError

        raise InvalidImageError("Upload exceeds the encoded byte limit")
    return data


@app.post(
    "/poc/v1/inpaint",
    responses={
        200: {"content": {"image/png": {}}},
        422: {"model": ErrorBody},
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
        from .errors import InvalidImageError

        raise InvalidImageError("Prompt exceeds the configured limit")
    allowed = {"image/jpeg", "image/png", "image/webp", "application/octet-stream"}
    if image.content_type not in allowed or mask.content_type not in allowed:
        from .errors import InvalidImageError

        raise InvalidImageError("Unsupported upload content type")
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
