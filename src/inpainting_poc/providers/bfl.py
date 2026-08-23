from __future__ import annotations

import asyncio
import base64
import time
from io import BytesIO
from urllib.parse import urlsplit

import httpx
import numpy as np
from PIL import Image

from ..errors import ProviderError, ProviderTimeoutError, ProviderUnavailableError
from ..imaging import ImageLimits, decode_image_rgb
from ..models import ProviderRequest, ProviderResult


class BFLFluxFillProvider:
    name = "black-forest-labs"
    _submit_url = "https://api.bfl.ai/v1/flux-pro-1.0-fill"

    def __init__(
        self,
        *,
        api_key: str,
        result_hosts: tuple[str, ...],
        deadline_seconds: float = 120.0,
        max_result_bytes: int = 20 * 1024 * 1024,
        max_pixels: int = 20_000_000,
        api_client: httpx.AsyncClient | None = None,
        download_client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("BFL API key is required")
        if not result_hosts:
            raise ValueError("At least one approved BFL result host is required")
        self._result_hosts = frozenset(host.lower() for host in result_hosts)
        self._deadline_seconds = deadline_seconds
        self._result_limits = ImageLimits(max_bytes=max_result_bytes, max_pixels=max_pixels)
        timeout = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0)
        self._api_client = api_client or httpx.AsyncClient(
            headers={"x-key": api_key, "accept": "application/json"}, timeout=timeout
        )
        # Never attach x-key to a signed result URL on another host.
        self._download_client = download_client or httpx.AsyncClient(timeout=timeout)
        self._owns_api_client = api_client is None
        self._owns_download_client = download_client is None

    @staticmethod
    def _encode_rgb(image: np.ndarray) -> str:
        buffer = BytesIO()
        Image.fromarray(image, mode="RGB").save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    @staticmethod
    def _encode_mask(mask: np.ndarray) -> str:
        buffer = BytesIO()
        Image.fromarray(mask, mode="L").save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    @staticmethod
    def _validate_https_url(url: str, allowed_hosts: frozenset[str]) -> str:
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.hostname.lower() not in allowed_hosts
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in {None, 443}
        ):
            raise ProviderError("Provider returned a URL outside the approved host policy")
        return url

    async def inpaint(self, request: ProviderRequest) -> ProviderResult:
        payload = {
            "prompt": request.prompt,
            "image": self._encode_rgb(request.image_rgb),
            "mask": self._encode_mask(request.hard_mask),
            "steps": 50,
            "guidance": 30,
            "output_format": "png",
            "safety_tolerance": 2,
        }
        started = time.monotonic()
        try:
            response = await self._api_client.post(self._submit_url, json=payload)
            response.raise_for_status()
            body = response.json()
            provider_request_id = str(body["id"])
            polling_url = self._validate_https_url(
                str(body["polling_url"]), frozenset({"api.bfl.ai"})
            )
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise ProviderUnavailableError("BFL submit request failed") from exc
        except (httpx.HTTPStatusError, KeyError, TypeError, ValueError) as exc:
            raise ProviderError("BFL submit response was not usable") from exc

        delay = 0.5
        while True:
            remaining = self._deadline_seconds - (time.monotonic() - started)
            if remaining <= 0:
                raise ProviderTimeoutError("BFL generation exceeded the approved deadline")
            await asyncio.sleep(min(delay, remaining))
            try:
                poll = await self._api_client.get(polling_url)
                poll.raise_for_status()
                poll_body = poll.json()
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                raise ProviderUnavailableError("BFL polling failed") from exc
            except (httpx.HTTPStatusError, ValueError) as exc:
                raise ProviderError("BFL polling response was not usable") from exc

            status = str(poll_body.get("status", ""))
            if status == "Ready":
                try:
                    result_url = self._validate_https_url(
                        str(poll_body["result"]["sample"]), self._result_hosts
                    )
                except (KeyError, TypeError) as exc:
                    raise ProviderError("BFL result URL was missing") from exc
                result_bytes = await self._download_bounded(result_url)
                image = decode_image_rgb(result_bytes, self._result_limits)
                return ProviderResult(
                    image_rgb=image,
                    provider=self.name,
                    model="flux-pro-1.0-fill",
                    request_id=provider_request_id,
                )
            if status in {"Error", "Failed"}:
                raise ProviderError("BFL generation failed")
            if status not in {"Pending", "Request Moderated", "Content Moderated"}:
                raise ProviderError("BFL returned an unknown generation state")
            delay = min(delay * 1.5, 2.0)

    async def _download_bounded(self, url: str) -> bytes:
        try:
            async with self._download_client.stream("GET", url) as response:
                response.raise_for_status()
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > self._result_limits.max_bytes:
                    raise ProviderError("Provider result exceeds the byte limit")
                chunks: list[bytes] = []
                size = 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > self._result_limits.max_bytes:
                        raise ProviderError("Provider result exceeds the byte limit")
                    chunks.append(chunk)
                return b"".join(chunks)
        except ProviderError:
            raise
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
            raise ProviderUnavailableError("BFL result download failed") from exc
        except ValueError as exc:
            raise ProviderError("Provider result headers were invalid") from exc

    async def aclose(self) -> None:
        if self._owns_api_client:
            await self._api_client.aclose()
        if self._owns_download_client:
            await self._download_client.aclose()
