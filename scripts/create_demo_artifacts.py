from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from inpainting_poc.imaging import ImageLimits
from inpainting_poc.orchestrator import InpaintingOrchestrator
from inpainting_poc.providers.demo import DeterministicDemoProvider


def to_png(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


async def main() -> None:
    out = Path("demo-artifacts")
    out.mkdir(exist_ok=True)

    width, height = 960, 640
    x = np.linspace(0, 1, width, dtype=np.float32)
    y = np.linspace(0, 1, height, dtype=np.float32)[:, None]
    room = np.empty((height, width, 3), dtype=np.uint8)
    room[..., 0] = np.clip(225 - 35 * y + 12 * x, 0, 255).astype(np.uint8)
    room[..., 1] = np.clip(218 - 25 * y + 8 * x, 0, 255).astype(np.uint8)
    room[..., 2] = np.clip(205 - 15 * y + 4 * x, 0, 255).astype(np.uint8)
    before = Image.fromarray(room, mode="RGB")
    draw = ImageDraw.Draw(before)
    draw.rectangle((70, 70, 890, 500), outline=(125, 110, 95), width=6)
    draw.line((70, 500, 890, 500), fill=(105, 90, 78), width=8)
    draw.rectangle((150, 140, 355, 330), fill=(165, 190, 210), outline=(90, 110, 125), width=4)
    draw.rectangle((605, 140, 810, 330), fill=(165, 190, 210), outline=(90, 110, 125), width=4)
    draw.rectangle((300, 360, 660, 500), fill=(122, 105, 92), outline=(75, 65, 58), width=4)

    mask = Image.new("L", (width, height), color=0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((270, 335, 690, 525), radius=30, fill=255)

    before_bytes = to_png(before)
    mask_bytes = to_png(mask)
    orchestrator = InpaintingOrchestrator(
        DeterministicDemoProvider(), ImageLimits(max_bytes=10_000_000, max_pixels=2_000_000)
    )
    result = await orchestrator.run(
        image_bytes=before_bytes,
        mask_bytes=mask_bytes,
        prompt="warm modern sofa texture demo",
    )
    (out / "before.png").write_bytes(before_bytes)
    (out / "mask-white-edit.png").write_bytes(mask_bytes)
    (out / "after-deterministic-demo-not-ai.png").write_bytes(result.png_bytes)
    (out / "README.txt").write_text(
        "These artifacts demonstrate deterministic masking and exact protected-pixel "
        "compositing. The result is procedural and is NOT an AI generation or quality benchmark.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    asyncio.run(main())
