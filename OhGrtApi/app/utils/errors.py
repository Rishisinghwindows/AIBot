class ServiceError(Exception):
    """Base service exception."""


class ExternalServiceUnavailable(ServiceError):
    """Raised when an upstream dependency cannot be reached."""


class ValidationError(ServiceError):
    """Raised when user input is invalid."""
