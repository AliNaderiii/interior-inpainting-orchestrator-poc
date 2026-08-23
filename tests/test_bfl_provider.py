from io import BytesIO

import httpx
import numpy as np
from PIL import Image

from inpainting_poc.models import ProviderRequest
from inpainting_poc.providers.bfl import BFLFluxFillProvider


def output_png() -> bytes:
    buffer = BytesIO()
    Image.fromarray(np.full((8, 10, 3), 77, dtype=np.uint8), mode="RGB").save(buffer, format="PNG")
    return buffer.getvalue()


async def test_bfl_submit_poll_and_separate_unsigned_download_client() -> None:
    calls: list[tuple[str, str, str | None]] = []

    def api_handler(request: httpx.Request) -> httpx.Response:
        calls.append(("api", request.method, request.headers.get("x-key")))
        if request.method == "POST":
            return httpx.Response(
                200,
                json={"id": "req-1", "polling_url": "https://api.bfl.ai/v1/get_result?id=req-1"},
            )
        return httpx.Response(
            200,
            json={
                "status": "Ready",
                "result": {"sample": "https://results.example.test/signed/output.png"},
            },
        )

    def download_handler(request: httpx.Request) -> httpx.Response:
        calls.append(("download", request.method, request.headers.get("x-key")))
        return httpx.Response(200, content=output_png(), headers={"content-type": "image/png"})

    api_client = httpx.AsyncClient(
        transport=httpx.MockTransport(api_handler), headers={"x-key": "test-secret"}
    )
    download_client = httpx.AsyncClient(transport=httpx.MockTransport(download_handler))
    provider = BFLFluxFillProvider(
        api_key="test-secret",
        result_hosts=("results.example.test",),
        deadline_seconds=3,
        api_client=api_client,
        download_client=download_client,
    )
    request = ProviderRequest(
        image_rgb=np.zeros((8, 10, 3), dtype=np.uint8),
        hard_mask=np.pad(np.full((4, 6), 255, dtype=np.uint8), ((2, 2), (2, 2))),
        prompt="replace sofa",
    )

    result = await provider.inpaint(request)
    await api_client.aclose()
    await download_client.aclose()

    assert result.image_rgb.shape == (8, 10, 3)
    assert result.request_id == "req-1"
    assert [call[0] for call in calls] == ["api", "api", "download"]
    assert calls[-1][2] is None, "BFL key must never be sent to the signed result host"
