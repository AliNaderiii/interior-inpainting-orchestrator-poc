from __future__ import annotations

import pytest
from pydantic import ValidationError

from inpainting_poc.errors import InvalidIntentError
from inpainting_poc.intent import StyleIntent, compile_intent


def test_style_intent_compiler_is_deterministic_and_explainable() -> None:
    intent = StyleIntent(
        style="japandi",
        room_type="living-room",
        palette=["#D9C7A3", "#F4F0E8", "#D9C7A3"],
        materials=["wood", "stone", "wood"],
        preserve_semantics=["window frames", "existing floor"],
        notes="Use quiet, natural contrast.",
    )

    first = compile_intent(intent, user_prompt="Make the wall feel lighter")
    second = compile_intent(intent, user_prompt="Make the wall feel lighter")

    assert first == second
    assert first.compiler_version == "intent-v1"
    assert first.intent_sha256 == second.intent_sha256
    assert "japandi" in first.prompt
    assert "#D9C7A3, #F4F0E8" in first.prompt
    assert "hard mask is the final geometric authority" in first.prompt
    assert len(first.segments) >= 5


def test_style_intent_rejects_unknown_fields_and_invalid_palette() -> None:
    with pytest.raises(ValidationError):
        StyleIntent.model_validate(
            {
                "style": "japandi",
                "palette": ["beige"],
                "unsupported": "must fail closed",
            }
        )


def test_compiler_enforces_configured_prompt_budget() -> None:
    intent = StyleIntent(style="industrial", notes="Concrete and dark metal accents")

    with pytest.raises(InvalidIntentError, match="character limit"):
        compile_intent(intent, max_chars=80)
