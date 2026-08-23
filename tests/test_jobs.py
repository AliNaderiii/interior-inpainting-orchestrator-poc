from __future__ import annotations

import asyncio
from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from inpainting_poc.errors import (
    IdempotencyConflictError,
    JobCapacityError,
    JobNotReadyError,
)
from inpainting_poc.imaging import ImageLimits
from inpainting_poc.jobs import InMemoryJobManager
from inpainting_poc.models import JobView
from inpainting_poc.orchestrator import InpaintingOrchestrator
from inpainting_poc.providers.demo import DeterministicDemoProvider


def png_bytes(array: np.ndarray, mode: str) -> bytes:
    output = BytesIO()
    Image.fromarray(array, mode=mode).save(output, format="PNG")
    return output.getvalue()


def inputs(*, empty_mask: bool = False) -> tuple[bytes, bytes]:
    image = np.full((36, 48, 3), 110, dtype=np.uint8)
    mask = np.zeros((36, 48), dtype=np.uint8)
    if not empty_mask:
        mask[8:28, 12:38] = 255
    return png_bytes(image, "RGB"), png_bytes(mask, "L")


def manager(*, max_records: int = 4) -> InMemoryJobManager:
    orchestrator = InpaintingOrchestrator(
        DeterministicDemoProvider(),
        ImageLimits(max_bytes=1_000_000, max_pixels=100_000),
    )
    return InMemoryJobManager(
        orchestrator,
        max_records=max_records,
        max_concurrency=1,
        ttl_seconds=60,
    )


async def wait_terminal(jobs: InMemoryJobManager, job_id: str) -> JobView:
    for _ in range(20):
        view = await jobs.get_view(job_id)
        if view.status in {"succeeded", "failed", "expired"}:
            return view
        await asyncio.sleep(0)
    raise AssertionError("Job did not reach a terminal state")


async def test_job_lifecycle_returns_result_and_reuses_idempotent_submission() -> None:
    jobs = manager()
    image, mask = inputs()
    try:
        accepted = await jobs.submit(
            image_bytes=image,
            mask_bytes=mask,
            compiled_prompt="warm minimal wall finish",
            intent_sha256="a" * 64,
            idempotency_key="render-request-001",
        )
        terminal = await wait_terminal(jobs, accepted.job_id)
        result, metadata = await jobs.get_result(accepted.job_id)
        reused = await jobs.submit(
            image_bytes=image,
            mask_bytes=mask,
            compiled_prompt="warm minimal wall finish",
            intent_sha256="a" * 64,
            idempotency_key="render-request-001",
        )
    finally:
        await jobs.close()

    assert terminal.status == "succeeded"
    assert terminal.progress == 100
    assert terminal.metadata == metadata
    assert result.startswith(b"\x89PNG")
    assert reused.reused is True
    assert reused.job_id == accepted.job_id


async def test_job_idempotency_key_rejects_a_different_payload() -> None:
    jobs = manager()
    image, mask = inputs()
    try:
        await jobs.submit(
            image_bytes=image,
            mask_bytes=mask,
            compiled_prompt="first direction",
            intent_sha256=None,
            idempotency_key="render-request-002",
        )
        with pytest.raises(IdempotencyConflictError):
            await jobs.submit(
                image_bytes=image,
                mask_bytes=mask,
                compiled_prompt="different direction",
                intent_sha256=None,
                idempotency_key="render-request-002",
            )
    finally:
        await jobs.close()


async def test_job_failure_is_captured_without_exposing_a_result() -> None:
    jobs = manager()
    image, mask = inputs(empty_mask=True)
    try:
        accepted = await jobs.submit(
            image_bytes=image,
            mask_bytes=mask,
            compiled_prompt="test invalid mask",
            intent_sha256=None,
            idempotency_key=None,
        )
        terminal = await wait_terminal(jobs, accepted.job_id)
        with pytest.raises(JobNotReadyError):
            await jobs.get_result(accepted.job_id)
    finally:
        await jobs.close()

    assert terminal.status == "failed"
    assert terminal.failure is not None
    assert terminal.failure.code == "InvalidMaskError"
    assert terminal.metadata is None


async def test_bounded_job_store_fails_closed_at_capacity() -> None:
    jobs = manager(max_records=1)
    image, mask = inputs()
    try:
        first = await jobs.submit(
            image_bytes=image,
            mask_bytes=mask,
            compiled_prompt="first",
            intent_sha256=None,
            idempotency_key=None,
        )
        await wait_terminal(jobs, first.job_id)
        with pytest.raises(JobCapacityError, match="capacity"):
            await jobs.submit(
                image_bytes=image,
                mask_bytes=mask,
                compiled_prompt="second",
                intent_sha256=None,
                idempotency_key=None,
            )
    finally:
        await jobs.close()
