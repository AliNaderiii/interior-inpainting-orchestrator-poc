from __future__ import annotations

from typing import Protocol

from ..models import ProviderRequest, ProviderResult


class InpaintingProvider(Protocol):
    name: str

    async def inpaint(self, request: ProviderRequest) -> ProviderResult:
        """Return an RGB image with the same geometry as the request image."""
        ...

    async def aclose(self) -> None:
        """Release network resources."""
        ...
