from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from inpainting_poc.errors import InvalidMaskError
from inpainting_poc.imaging import (
    ImageLimits,
    composite_preserving_unmasked,
    decode_image_rgb,
    decode_mask_gray,
    process_mask,
)


def png_bytes(array: np.ndarray, mode: str) -> bytes:
    output = BytesIO()
    Image.fromarray(array, mode=mode).save(output, format="PNG")
    return output.getvalue()


def test_composite_preserves_every_unmasked_pixel_exactly() -> None:
    original = np.full((64, 96, 3), [20, 40, 60], dtype=np.uint8)
    generated = np.full_like(original, [240, 180, 90])
    gray = np.zeros((64, 96), dtype=np.uint8)
    gray[16:48, 24:72] = 255
    mask = process_mask(gray, close_radius=0, feather_radius=5)

    output = composite_preserving_unmasked(original, generated, mask)

    protected = mask.hard == 0
    assert np.array_equal(output[protected], original[protected])
    assert np.any(output[~protected] != original[~protected])


def test_mask_requires_exact_geometry() -> None:
    limits = ImageLimits(max_bytes=1_000_000, max_pixels=100_000)
    mask = np.zeros((10, 11), dtype=np.uint8)
    with pytest.raises(InvalidMaskError, match="exactly match"):
        decode_mask_gray(png_bytes(mask, "L"), (10, 10), limits)


def test_empty_and_excessive_masks_are_rejected() -> None:
    with pytest.raises(InvalidMaskError, match="no editable"):
        process_mask(np.zeros((20, 20), dtype=np.uint8))
    with pytest.raises(InvalidMaskError, match="allowed editable area"):
        process_mask(np.full((20, 20), 255, dtype=np.uint8))


def test_decode_normalizes_to_rgb_and_is_repeatable() -> None:
    rgba = np.zeros((12, 17, 4), dtype=np.uint8)
    rgba[..., :3] = [10, 20, 30]
    rgba[..., 3] = 127
    data = png_bytes(rgba, "RGBA")
    limits = ImageLimits(max_bytes=100_000, max_pixels=1_000)

    first = decode_image_rgb(data, limits)
    second = decode_image_rgb(data, limits)

    assert first.shape == (12, 17, 3)
    assert first.dtype == np.uint8
    assert np.array_equal(first, second)
