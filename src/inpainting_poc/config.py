from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    provider: str = "demo"
    max_upload_bytes: int = 10 * 1024 * 1024
    max_pixels: int = 20_000_000
    max_prompt_chars: int = 1_000
    request_timeout_seconds: float = 60.0
    provider_deadline_seconds: float = 120.0
    bfl_api_key: str | None = None
    bfl_result_hosts: tuple[str, ...] = ()

    @classmethod
    def from_env(cls) -> Settings:
        hosts = tuple(
            item.strip().lower()
            for item in os.getenv("BFL_RESULT_HOSTS", "").split(",")
            if item.strip()
        )
        return cls(
            provider=os.getenv("INPAINT_PROVIDER", "demo").strip().lower(),
            max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024))),
            max_pixels=int(os.getenv("MAX_PIXELS", "20000000")),
            max_prompt_chars=int(os.getenv("MAX_PROMPT_CHARS", "1000")),
            request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "60")),
            provider_deadline_seconds=float(os.getenv("PROVIDER_DEADLINE_SECONDS", "120")),
            bfl_api_key=os.getenv("BFL_API_KEY"),
            bfl_result_hosts=hosts,
        )

    def validate(self) -> None:
        if self.provider not in {"demo", "bfl"}:
            raise ValueError("INPAINT_PROVIDER must be 'demo' or 'bfl'")
        if self.max_upload_bytes <= 0 or self.max_pixels <= 0:
            raise ValueError("Image limits must be positive")
        if not 1 <= self.max_prompt_chars <= 10_000:
            raise ValueError("MAX_PROMPT_CHARS must be between 1 and 10000")
        if self.provider == "bfl" and not self.bfl_api_key:
            raise ValueError("BFL_API_KEY is required when INPAINT_PROVIDER=bfl")
        if self.provider == "bfl" and not self.bfl_result_hosts:
            raise ValueError("BFL_RESULT_HOSTS is required when INPAINT_PROVIDER=bfl")
