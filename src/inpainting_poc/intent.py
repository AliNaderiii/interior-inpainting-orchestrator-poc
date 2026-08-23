from __future__ import annotations

import hashlib
import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .errors import InvalidIntentError

StyleName = Literal[
    "contemporary",
    "industrial",
    "japandi",
    "modern-calm",
    "scandinavian",
    "warm-minimal",
]
RoomType = Literal[
    "bedroom",
    "dining-room",
    "home-office",
    "kitchen",
    "living-room",
]
MaterialName = Literal["concrete", "glass", "metal", "plaster", "stone", "textile", "wood"]

_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
_SPACE = re.compile(r"\s+")
COMPILER_VERSION: Literal["intent-v1"] = "intent-v1"


class StyleIntent(BaseModel):
    """Structured design direction; geometry remains governed by the hard mask."""

    model_config = ConfigDict(extra="forbid")

    style: StyleName
    room_type: RoomType = "living-room"
    palette: list[str] = Field(default_factory=list, max_length=5)
    materials: list[MaterialName] = Field(default_factory=list, max_length=4)
    preserve_semantics: list[str] = Field(default_factory=list, max_length=6)
    notes: str | None = Field(default=None, max_length=240)

    @field_validator("palette")
    @classmethod
    def validate_palette(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            if not _HEX_COLOR.fullmatch(value):
                raise ValueError("Palette entries must use #RRGGBB")
            upper = value.upper()
            if upper not in normalized:
                normalized.append(upper)
        return normalized

    @field_validator("materials")
    @classmethod
    def deduplicate_materials(cls, values: list[MaterialName]) -> list[MaterialName]:
        return list(dict.fromkeys(values))

    @field_validator("preserve_semantics")
    @classmethod
    def normalize_preserve_semantics(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            clean = _SPACE.sub(" ", value).strip()
            if not 2 <= len(clean) <= 60:
                raise ValueError("Preserve labels must contain 2 to 60 characters")
            if clean not in normalized:
                normalized.append(clean)
        return normalized

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = _SPACE.sub(" ", value).strip()
        return clean or None


class CompiledIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    compiler_version: Literal["intent-v1"] = COMPILER_VERSION
    prompt: str
    segments: list[str]
    intent_sha256: str


def _normalize_freeform(value: str | None) -> str | None:
    if value is None:
        return None
    clean = _SPACE.sub(" ", value).strip()
    return clean or None


def compile_intent(
    intent: StyleIntent,
    *,
    user_prompt: str | None = None,
    max_chars: int = 1_000,
) -> CompiledIntent:
    """Compile transparent, deterministic style metadata into a provider prompt."""

    segments = [
        f"Restyle the authorized region of this {intent.room_type} in a {intent.style} direction"
    ]
    if intent.palette:
        segments.append(f"Use a restrained palette centered on {', '.join(intent.palette)}")
    if intent.materials:
        segments.append(f"Prefer these material cues: {', '.join(intent.materials)}")
    if intent.preserve_semantics:
        segments.append(
            "Keep the visual identity of these elements where they intersect the edit: "
            + ", ".join(intent.preserve_semantics)
        )
    if intent.notes:
        segments.append(f"Additional design direction: {intent.notes}")
    if freeform := _normalize_freeform(user_prompt):
        segments.append(f"User direction: {freeform}")
    segments.append(
        "Generate a coherent interior finish only; the hard mask is the final geometric authority"
    )
    prompt = ". ".join(segments) + "."
    if len(prompt) > max_chars:
        raise InvalidIntentError("Compiled prompt exceeds the configured character limit")

    canonical = json.dumps(intent.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return CompiledIntent(
        prompt=prompt,
        segments=segments,
        intent_sha256=hashlib.sha256(canonical.encode()).hexdigest(),
    )
