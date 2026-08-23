from __future__ import annotations

import hashlib
from dataclasses import dataclass
from io import BytesIO

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from .errors import InvalidImageError, InvalidMaskError
from .models import MaskArtifact

_ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


@dataclass(frozen=True, slots=True)
class ImageLimits:
    max_bytes: int = 10 * 1024 * 1024
    max_pixels: int = 20_000_000


def _open_single_frame(data: bytes, limits: ImageLimits, *, mask: bool) -> Image.Image:
    error = InvalidMaskError if mask else InvalidImageError
    label = "Mask" if mask else "Image"
    if not data or len(data) > limits.max_bytes:
        raise error(f"{label} byte size is outside the allowed range")
    try:
        image = Image.open(BytesIO(data))
        if image.format not in _ALLOWED_FORMATS:
            raise error(f"Unsupported {label.lower()} format")
        if getattr(image, "n_frames", 1) != 1:
            raise error(f"Animated or multi-frame {label.lower()} is not allowed")
        width, height = image.size
        if width <= 0 or height <= 0 or width * height > limits.max_pixels:
            raise error(f"Decoded {label.lower()} dimensions exceed limits")
        image.load()
        return ImageOps.exif_transpose(image)
    except error:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise error(f"Invalid {label.lower()} data") from exc


def decode_image_rgb(data: bytes, limits: ImageLimits) -> np.ndarray:
    image = _open_single_frame(data, limits, mask=False).convert("RGB")
    return np.asarray(image, dtype=np.uint8).copy()


def decode_image_rgba(data: bytes, limits: ImageLimits) -> np.ndarray:
    """Decode a bounded product raster while preserving or synthesizing alpha."""
    image = _open_single_frame(data, limits, mask=False).convert("RGBA")
    return np.asarray(image, dtype=np.uint8).copy()


def decode_mask_gray(
    data: bytes, expected_size: tuple[int, int], limits: ImageLimits
) -> np.ndarray:
    image = _open_single_frame(data, limits, mask=True).convert("L")
    if image.size != expected_size:
        raise InvalidMaskError("Mask dimensions must exactly match the normalized image")
    return np.asarray(image, dtype=np.uint8).copy()


def process_mask(
    gray: np.ndarray,
    *,
    threshold: int = 127,
    close_radius: int = 0,
    feather_radius: int = 5,
    max_coverage: float = 0.95,
) -> MaskArtifact:
    if gray.ndim != 2 or gray.dtype != np.uint8:
        raise InvalidMaskError("Mask must be an 8-bit single-channel array")
    if not 0 <= threshold <= 255:
        raise InvalidMaskError("Mask threshold is invalid")

    hard: np.ndarray = np.where(gray > threshold, 255, 0).astype(np.uint8)
    if close_radius > 0:
        size = 2 * close_radius + 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
        hard = np.asarray(cv2.morphologyEx(hard, cv2.MORPH_CLOSE, kernel), dtype=np.uint8)

    coverage = float(np.count_nonzero(hard)) / float(hard.size)
    if coverage <= 0.0:
        raise InvalidMaskError("Mask contains no editable pixels")
    if coverage > max_coverage:
        raise InvalidMaskError("Mask covers more than the allowed editable area")

    if feather_radius > 0:
        kernel_size = 2 * feather_radius + 1
        blurred = cv2.GaussianBlur(
            hard.astype(np.float32) / 255.0,
            (kernel_size, kernel_size),
            sigmaX=0,
            borderType=cv2.BORDER_REPLICATE,
        )
        # Feather inward only. Pixels outside the hard authorization mask remain exact.
        alpha = np.where(hard > 0, blurred, 0.0).astype(np.float32)
    else:
        alpha = (hard.astype(np.float32) / 255.0).astype(np.float32)

    return MaskArtifact(hard=hard, alpha=alpha, coverage_ratio=coverage)


def composite_preserving_unmasked(
    original_rgb: np.ndarray,
    generated_rgb: np.ndarray,
    mask: MaskArtifact,
) -> np.ndarray:
    if original_rgb.shape != generated_rgb.shape:
        raise InvalidImageError("Provider output dimensions do not match the source image")
    if original_rgb.ndim != 3 or original_rgb.shape[2] != 3:
        raise InvalidImageError("Expected RGB arrays")
    if mask.hard.shape != original_rgb.shape[:2] or mask.alpha.shape != original_rgb.shape[:2]:
        raise InvalidMaskError("Mask geometry does not match image geometry")

    alpha = mask.alpha[..., None]
    blended = (
        np.rint(
            original_rgb.astype(np.float32) * (1.0 - alpha)
            + generated_rgb.astype(np.float32) * alpha
        )
        .clip(0, 255)
        .astype(np.uint8)
    )
    protected = mask.hard == 0
    blended[protected] = original_rgb[protected]
    return np.asarray(blended, dtype=np.uint8)


def encode_png(rgb: np.ndarray) -> bytes:
    if rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[2] != 3:
        raise InvalidImageError("Expected an 8-bit RGB image")
    output = BytesIO()
    Image.fromarray(rgb, mode="RGB").save(output, format="PNG", optimize=False)
    return output.getvalue()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
