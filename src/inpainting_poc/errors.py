class InpaintingError(Exception):
    """Base domain error safe for internal mapping."""


class InvalidImageError(InpaintingError):
    pass


class InvalidMaskError(InpaintingError):
    pass


class InvalidIntentError(InpaintingError):
    pass


class JobError(InpaintingError):
    pass


class JobNotFoundError(JobError):
    pass


class JobNotReadyError(JobError):
    pass


class JobExpiredError(JobError):
    pass


class JobCapacityError(JobError):
    pass


class IdempotencyConflictError(JobError):
    pass


class ProviderError(InpaintingError):
    pass


class ProviderUnavailableError(ProviderError):
    pass


class ProviderTimeoutError(ProviderError):
    pass
