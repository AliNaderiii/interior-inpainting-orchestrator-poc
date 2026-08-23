import asyncio
import json
from io import BytesIO

import numpy as np
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from PIL import Image

from inpainting_poc.api import app


def png_bytes(array: np.ndarray, mode: str) -> bytes:
    output = BytesIO()
    Image.fromarray(array, mode=mode).save(output, format="PNG")
    return output.getvalue()


async def test_health_and_demo_inpaint(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("INPAINT_PROVIDER", "demo")
    image = np.full((48, 64, 3), 100, dtype=np.uint8)
    mask = np.zeros((48, 64), dtype=np.uint8)
    mask[12:36, 16:48] = 255

    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client,
    ):
        health = await client.get("/health/live")
        response = await client.post(
            "/poc/v1/inpaint",
            files={
                "image": ("room.png", png_bytes(image, "RGB"), "image/png"),
                "mask": ("mask.png", png_bytes(mask, "L"), "image/png"),
            },
            data={"prompt": "minimal warm seating"},
        )

    assert health.status_code == 200
    assert health.json() == {"status": "ok", "provider": "deterministic-demo"}
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-poc-model"].endswith("not-ai")
    assert response.headers["x-request-id"]


async def test_invalid_mask_returns_stable_error(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("INPAINT_PROVIDER", "demo")
    image = np.full((20, 20, 3), 100, dtype=np.uint8)
    empty_mask = np.zeros((20, 20), dtype=np.uint8)

    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client,
    ):
        response = await client.post(
            "/poc/v1/inpaint",
            files={
                "image": ("room.png", png_bytes(image, "RGB"), "image/png"),
                "mask": ("mask.png", png_bytes(empty_mask, "L"), "image/png"),
            },
            data={"prompt": "test"},
        )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "InvalidMaskError"
    assert body["request_id"]


async def test_v2_intent_compiler_endpoint_is_transparent(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("INPAINT_PROVIDER", "demo")
    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client,
    ):
        response = await client.post(
            "/poc/v2/intents/compile",
            json={
                "style": "warm-minimal",
                "room_type": "living-room",
                "palette": ["#E9DDC8", "#6E5946"],
                "materials": ["wood", "plaster"],
                "preserve_semantics": ["window frames"],
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["compiler_version"] == "intent-v1"
    assert body["intent_sha256"]
    assert "warm-minimal" in body["prompt"]
    assert "hard mask is the final geometric authority" in body["prompt"]


async def test_v2_job_lifecycle_and_idempotent_replay(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("INPAINT_PROVIDER", "demo")
    image = np.full((40, 56, 3), 105, dtype=np.uint8)
    mask = np.zeros((40, 56), dtype=np.uint8)
    mask[10:32, 14:44] = 255
    files = {
        "image": ("room.png", png_bytes(image, "RGB"), "image/png"),
        "mask": ("mask.png", png_bytes(mask, "L"), "image/png"),
    }
    intent = json.dumps(
        {
            "style": "japandi",
            "palette": ["#D8C8AA"],
            "materials": ["wood", "stone"],
        }
    )
    headers = {"Idempotency-Key": "api-render-0001"}

    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client,
    ):
        created = await client.post(
            "/poc/v2/jobs",
            files=files,
            data={"intent": intent, "prompt": "Keep the finish quiet"},
            headers=headers,
        )
        job_id = created.json()["job_id"]
        terminal = None
        for _ in range(20):
            terminal = await client.get(f"/poc/v2/jobs/{job_id}")
            if terminal.json()["status"] in {"succeeded", "failed"}:
                break
            await asyncio.sleep(0)
        result = await client.get(f"/poc/v2/jobs/{job_id}/result")
        replayed = await client.post(
            "/poc/v2/jobs",
            files=files,
            data={"intent": intent, "prompt": "Keep the finish quiet"},
            headers=headers,
        )
        readiness = await client.get("/health/ready")

    assert created.status_code == 202
    assert created.headers["location"] == f"/poc/v2/jobs/{job_id}"
    assert terminal is not None
    assert terminal.json()["status"] == "succeeded"
    assert terminal.json()["metadata"]["provider"] == "deterministic-demo"
    assert result.status_code == 200
    assert result.headers["content-type"] == "image/png"
    assert replayed.status_code == 202
    assert replayed.json()["reused"] is True
    assert replayed.json()["job_id"] == job_id
    assert readiness.json()["status"] == "ready"
    assert readiness.json()["max_concurrency"] == 2


async def test_v2_job_rejects_idempotency_conflict(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("INPAINT_PROVIDER", "demo")
    image = np.full((24, 24, 3), 100, dtype=np.uint8)
    mask = np.zeros((24, 24), dtype=np.uint8)
    mask[5:19, 5:19] = 255
    files = {
        "image": ("room.png", png_bytes(image, "RGB"), "image/png"),
        "mask": ("mask.png", png_bytes(mask, "L"), "image/png"),
    }
    headers = {"Idempotency-Key": "api-render-0002"}

    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client,
    ):
        first = await client.post(
            "/poc/v2/jobs",
            files=files,
            data={"prompt": "first direction"},
            headers=headers,
        )
        conflict = await client.post(
            "/poc/v2/jobs",
            files=files,
            data={"prompt": "different direction"},
            headers=headers,
        )

    assert first.status_code == 202
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "IdempotencyConflictError"
