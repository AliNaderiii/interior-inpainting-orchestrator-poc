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
