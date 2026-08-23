class InpaintingError(Exception):
    """Base domain error safe for internal mapping."""


class InvalidImageError(InpaintingError):
    pass


class InvalidMaskError(InpaintingError):
    pass


class ProviderError(InpaintingError):
    pass


class ProviderUnavailableError(ProviderError):
    pass


class ProviderTimeoutError(ProviderError):
    pass
