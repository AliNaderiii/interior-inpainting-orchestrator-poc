from io import BytesIO

import numpy as np
from PIL import Image

from inpainting_poc.imaging import ImageLimits, decode_image_rgb
from inpainting_poc.orchestrator import InpaintingOrchestrator
from inpainting_poc.providers.demo import DeterministicDemoProvider


def png_bytes(array: np.ndarray, mode: str) -> bytes:
    output = BytesIO()
    Image.fromarray(array, mode=mode).save(output, format="PNG")
    return output.getvalue()


async def test_orchestrator_is_deterministic_and_preserves_protected_region() -> None:
    original = np.zeros((80, 120, 3), dtype=np.uint8)
    original[..., 0] = np.arange(120, dtype=np.uint8)
    original[..., 1] = 80
    original[..., 2] = 160
    gray_mask = np.zeros((80, 120), dtype=np.uint8)
    gray_mask[20:60, 35:85] = 255
    image_data = png_bytes(original, "RGB")
    mask_data = png_bytes(gray_mask, "L")
    limits = ImageLimits(max_bytes=1_000_000, max_pixels=100_000)
    orchestrator = InpaintingOrchestrator(DeterministicDemoProvider(), limits)

    first = await orchestrator.run(
        image_bytes=image_data, mask_bytes=mask_data, prompt="modern sofa"
    )
    second = await orchestrator.run(
        image_bytes=image_data, mask_bytes=mask_data, prompt="modern sofa"
    )

    assert first.png_bytes == second.png_bytes
    output = decode_image_rgb(first.png_bytes, limits)
    assert np.array_equal(output[gray_mask == 0], original[gray_mask == 0])
    assert first.metadata.provider == "deterministic-demo"
    assert first.metadata.model.endswith("not-ai")
