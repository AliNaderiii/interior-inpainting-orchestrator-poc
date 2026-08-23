from __future__ import annotations

import asyncio
import hashlib
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from .errors import (
    IdempotencyConflictError,
    InpaintingError,
    JobCapacityError,
    JobExpiredError,
    JobNotFoundError,
    JobNotReadyError,
)
from .models import (
    InpaintMetadata,
    JobAccepted,
    JobFailure,
    JobLinks,
    JobStatus,
    JobView,
)
from .orchestrator import InpaintingOrchestrator

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _JobRecord:
    job_id: str
    status: JobStatus
    progress: int
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    fingerprint: str
    compiled_prompt: str
    intent_sha256: str | None
    idempotency_key: str | None
    result_png: bytes | None = None
    metadata: InpaintMetadata | None = None
    failure: JobFailure | None = None
    task: asyncio.Task[None] | None = None


class InMemoryJobManager:
    """Bounded, non-durable PoC job lifecycle with idempotent submission."""

    def __init__(
        self,
        orchestrator: InpaintingOrchestrator,
        *,
        max_records: int,
        max_concurrency: int,
        ttl_seconds: int,
    ) -> None:
        self._orchestrator = orchestrator
        self._max_records = max_records
        self._max_concurrency = max_concurrency
        self._ttl = timedelta(seconds=ttl_seconds)
        self._records: dict[str, _JobRecord] = {}
        self._idempotency: dict[str, tuple[str, str]] = {}
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._closed = False

    @property
    def max_records(self) -> int:
        return self._max_records

    @property
    def max_concurrency(self) -> int:
        return self._max_concurrency

    async def submit(
        self,
        *,
        image_bytes: bytes,
        mask_bytes: bytes,
        compiled_prompt: str,
        intent_sha256: str | None,
        idempotency_key: str | None,
    ) -> JobAccepted:
        fingerprint = self._fingerprint(image_bytes, mask_bytes, compiled_prompt)
        async with self._lock:
            if self._closed:
                raise JobCapacityError("Job manager is shutting down")
            self._expire_records(datetime.now(UTC))
            self._purge_expired_records()
            if idempotency_key and idempotency_key in self._idempotency:
                known_fingerprint, known_job_id = self._idempotency[idempotency_key]
                if known_fingerprint != fingerprint:
                    raise IdempotencyConflictError(
                        "Idempotency-Key was already used with a different request"
                    )
                record = self._records.get(known_job_id)
                if record is not None:
                    return self._accepted(record, reused=True)

            if len(self._records) >= self._max_records:
                raise JobCapacityError("The bounded PoC job store is at capacity; retry later")

            now = datetime.now(UTC)
            job_id = str(uuid.uuid4())
            record = _JobRecord(
                job_id=job_id,
                status="queued",
                progress=5,
                created_at=now,
                updated_at=now,
                expires_at=now + self._ttl,
                fingerprint=fingerprint,
                compiled_prompt=compiled_prompt,
                intent_sha256=intent_sha256,
                idempotency_key=idempotency_key,
            )
            self._records[job_id] = record
            if idempotency_key:
                self._idempotency[idempotency_key] = (fingerprint, job_id)
            record.task = asyncio.create_task(
                self._execute(
                    record,
                    image_bytes=image_bytes,
                    mask_bytes=mask_bytes,
                    prompt=compiled_prompt,
                ),
                name=f"inpaint-job-{job_id}",
            )
            return self._accepted(record, reused=False)

    async def get_view(self, job_id: str) -> JobView:
        async with self._lock:
            record = self._require_record(job_id)
            self._expire_record(record, datetime.now(UTC))
            return self._view(record)

    async def get_result(self, job_id: str) -> tuple[bytes, InpaintMetadata]:
        async with self._lock:
            record = self._require_record(job_id)
            self._expire_record(record, datetime.now(UTC))
            if record.status == "expired":
                raise JobExpiredError("Job result has expired")
            if record.status != "succeeded" or record.result_png is None or record.metadata is None:
                raise JobNotReadyError(
                    f"Job result is not available while status is {record.status}"
                )
            return record.result_png, record.metadata

    async def snapshot(self) -> tuple[int, int, int]:
        async with self._lock:
            self._expire_records(datetime.now(UTC))
            active = sum(
                record.status in {"queued", "running"} for record in self._records.values()
            )
            return active, self._max_records, self._max_concurrency

    async def close(self) -> None:
        async with self._lock:
            self._closed = True
            tasks = [record.task for record in self._records.values() if record.task is not None]
        for task in tasks:
            if not task.done():
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute(
        self,
        record: _JobRecord,
        *,
        image_bytes: bytes,
        mask_bytes: bytes,
        prompt: str,
    ) -> None:
        try:
            async with self._semaphore:
                if datetime.now(UTC) >= record.expires_at:
                    record.status = "expired"
                    record.progress = 0
                    record.updated_at = datetime.now(UTC)
                    return
                record.status = "running"
                record.progress = 25
                record.updated_at = datetime.now(UTC)
                output = await self._orchestrator.run(
                    image_bytes=image_bytes,
                    mask_bytes=mask_bytes,
                    prompt=prompt,
                )
                record.result_png = output.png_bytes
                record.metadata = output.metadata
                record.status = "succeeded"
                record.progress = 100
                record.updated_at = datetime.now(UTC)
        except asyncio.CancelledError:
            raise
        except InpaintingError as exc:
            record.failure = JobFailure(code=exc.__class__.__name__, message=str(exc))
            record.status = "failed"
            record.progress = 100
            record.updated_at = datetime.now(UTC)
        except Exception:
            logger.exception("Unhandled inpainting job failure", extra={"job_id": record.job_id})
            record.failure = JobFailure(code="InternalJobError", message="Job failed safely")
            record.status = "failed"
            record.progress = 100
            record.updated_at = datetime.now(UTC)

    def _require_record(self, job_id: str) -> _JobRecord:
        record = self._records.get(job_id)
        if record is None:
            raise JobNotFoundError("Unknown job identifier")
        return record

    def _expire_records(self, now: datetime) -> None:
        for record in self._records.values():
            self._expire_record(record, now)

    def _purge_expired_records(self) -> None:
        expired_ids = [
            job_id for job_id, record in self._records.items() if record.status == "expired"
        ]
        for job_id in expired_ids:
            record = self._records.pop(job_id)
            if record.idempotency_key:
                self._idempotency.pop(record.idempotency_key, None)

    @staticmethod
    def _expire_record(record: _JobRecord, now: datetime) -> None:
        if now < record.expires_at or record.status == "expired":
            return
        record.status = "expired"
        record.progress = 0
        record.result_png = None
        record.metadata = None
        record.failure = None
        record.updated_at = now
        if record.task is not None and not record.task.done():
            record.task.cancel()

    @staticmethod
    def _fingerprint(image_bytes: bytes, mask_bytes: bytes, prompt: str) -> str:
        digest = hashlib.sha256()
        for value in (image_bytes, mask_bytes, prompt.encode()):
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value)
        return digest.hexdigest()

    @staticmethod
    def _links(job_id: str) -> JobLinks:
        base = f"/poc/v2/jobs/{job_id}"
        return JobLinks(status=base, result=f"{base}/result")

    def _accepted(self, record: _JobRecord, *, reused: bool) -> JobAccepted:
        return JobAccepted(
            job_id=record.job_id,
            status=record.status,
            reused=reused,
            compiled_prompt=record.compiled_prompt,
            intent_sha256=record.intent_sha256,
            links=self._links(record.job_id),
        )

    def _view(self, record: _JobRecord) -> JobView:
        return JobView(
            job_id=record.job_id,
            status=record.status,
            progress=record.progress,
            created_at=record.created_at,
            updated_at=record.updated_at,
            expires_at=record.expires_at,
            metadata=record.metadata,
            failure=record.failure,
            links=self._links(record.job_id),
        )
