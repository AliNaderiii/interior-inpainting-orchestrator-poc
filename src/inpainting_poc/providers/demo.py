from __future__ import annotations

import hashlib

import numpy as np

from ..models import ProviderRequest, ProviderResult


class DeterministicDemoProvider:
    """Non-generative provider used only to demonstrate masks and compositing."""

    name = "deterministic-demo"

    async def inpaint(self, request: ProviderRequest) -> ProviderResult:
        digest = hashlib.sha256(request.prompt.encode("utf-8")).digest()
        palettes = np.array(
            [
                [78, 112, 120],
                [135, 102, 82],
                [92, 122, 103],
                [118, 105, 137],
                [145, 125, 94],
            ],
            dtype=np.int16,
        )
        base = palettes[digest[0] % len(palettes)]
        height, width, _ = request.image_rgb.shape
        yy, xx = np.indices((height, width), dtype=np.int16)
        weave = ((xx // 5 + yy // 5) % 2) * 5
        broad = ((xx // 31 + yy // 23) % 3) - 1
        texture = np.empty_like(request.image_rgb)
        for channel in range(3):
            values = base[channel] + weave + broad * (channel + 2)
            texture[..., channel] = np.clip(values, 0, 255).astype(np.uint8)
        return ProviderResult(
            image_rgb=texture,
            provider=self.name,
            model="procedural-texture-v1-not-ai",
        )

    async def aclose(self) -> None:
        return None
