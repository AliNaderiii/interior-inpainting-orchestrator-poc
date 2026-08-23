from __future__ import annotations

from dataclasses import dataclass

from .imaging import (
    ImageLimits,
    composite_preserving_unmasked,
    decode_image_rgb,
    decode_mask_gray,
    encode_png,
    process_mask,
    sha256_hex,
)
from .models import InpaintMetadata, ProviderRequest
from .providers.base import InpaintingProvider


@dataclass(frozen=True, slots=True)
class InpaintOutput:
    png_bytes: bytes
    metadata: InpaintMetadata


class InpaintingOrchestrator:
    def __init__(self, provider: InpaintingProvider, limits: ImageLimits) -> None:
        self._provider = provider
        self._limits = limits

    async def run(self, *, image_bytes: bytes, mask_bytes: bytes, prompt: str) -> InpaintOutput:
        original = decode_image_rgb(image_bytes, self._limits)
        height, width, _ = original.shape
        gray_mask = decode_mask_gray(mask_bytes, (width, height), self._limits)
        mask = process_mask(gray_mask)
        generated = await self._provider.inpaint(
            ProviderRequest(image_rgb=original, hard_mask=mask.hard, prompt=prompt)
        )
        final = composite_preserving_unmasked(original, generated.image_rgb, mask)
        encoded = encode_png(final)
        return InpaintOutput(
            png_bytes=encoded,
            metadata=InpaintMetadata(
                provider=generated.provider,
                model=generated.model,
                width=width,
                height=height,
                mask_coverage=mask.coverage_ratio,
                input_sha256=sha256_hex(image_bytes),
                output_sha256=sha256_hex(encoded),
            ),
        )
