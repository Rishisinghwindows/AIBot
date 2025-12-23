"""
Custom exceptions for OhGrt application.

This module provides a hierarchy of exceptions for consistent error handling
across the application.
"""

from typing import Any, Dict, Optional


class OhGrtException(Exception):
    """Base exception for all OhGrt errors."""

    def __init__(
        self,
        message: str,
        code: str = "OHGRT_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


# Authentication Errors (401, 403)
class AuthenticationError(OhGrtException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        code: str = "AUTH_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, status_code=401, details=details)


class TokenExpiredError(AuthenticationError):
    """Raised when a token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, code="TOKEN_EXPIRED")


class InvalidTokenError(AuthenticationError):
    """Raised when a token is invalid."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, code="INVALID_TOKEN")


class InsufficientPermissionsError(OhGrtException):
    """Raised when user lacks required permissions."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: Optional[str] = None,
    ):
        details = {"required_permission": required_permission} if required_permission else {}
        super().__init__(message, code="FORBIDDEN", status_code=403, details=details)


# Validation Errors (400)
class ValidationError(OhGrtException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(message, code="VALIDATION_ERROR", status_code=400, details=error_details)


class InvalidInputError(ValidationError):
    """Raised when input data is invalid."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, field=field)


class MissingParameterError(ValidationError):
    """Raised when a required parameter is missing."""

    def __init__(self, parameter: str):
        super().__init__(
            message=f"Missing required parameter: {parameter}",
            field=parameter,
        )


# Rate Limiting Errors (429)
class RateLimitExceededError(OhGrtException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        details = {"retry_after_seconds": retry_after} if retry_after else {}
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", status_code=429, details=details)
        self.retry_after = retry_after


# Resource Errors (404, 409)
class ResourceNotFoundError(OhGrtException):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
    ):
        message = f"{resource_type} not found"
        if resource_id:
            message = f"{resource_type} with id '{resource_id}' not found"
        details = {"resource_type": resource_type}
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message, code="NOT_FOUND", status_code=404, details=details)


class ResourceConflictError(OhGrtException):
    """Raised when a resource conflict occurs (e.g., duplicate)."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
    ):
        details = {"resource_type": resource_type} if resource_type else {}
        super().__init__(message, code="CONFLICT", status_code=409, details=details)


# External Service Errors (502, 503)
class ExternalServiceError(OhGrtException):
    """Raised when an external service call fails."""

    def __init__(
        self,
        service_name: str,
        message: str = "External service error",
        original_error: Optional[str] = None,
    ):
        details = {"service": service_name}
        if original_error:
            details["original_error"] = original_error
        super().__init__(
            message=f"{service_name}: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details=details,
        )


class ServiceUnavailableError(OhGrtException):
    """Raised when a service is temporarily unavailable (e.g., circuit breaker open)."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        service_name: Optional[str] = None,
        retry_after: Optional[int] = None,
    ):
        details: Dict[str, Any] = {}
        if service_name:
            details["service"] = service_name
        if retry_after:
            details["retry_after_seconds"] = retry_after
        self.retry_after = retry_after
        super().__init__(message, code="SERVICE_UNAVAILABLE", status_code=503, details=details)


# Database Errors (500)
class DatabaseError(OhGrtException):
    """Raised when a database operation fails."""

    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
    ):
        details = {"operation": operation} if operation else {}
        super().__init__(message, code="DATABASE_ERROR", status_code=500, details=details)


# Security Errors (400)
class SecurityError(OhGrtException):
    """Raised when a security validation fails."""

    def __init__(
        self,
        message: str,
        code: str = "SECURITY_ERROR",
    ):
        super().__init__(message, code=code, status_code=400)


class NonceReuseError(SecurityError):
    """Raised when a nonce is reused (replay attack prevention)."""

    def __init__(self):
        super().__init__(message="Nonce has already been used", code="NONCE_REUSED")


class TimestampExpiredError(SecurityError):
    """Raised when request timestamp is too old."""

    def __init__(self):
        super().__init__(
            message="Request timestamp expired or too far in future",
            code="TIMESTAMP_EXPIRED",
        )


class SQLInjectionError(SecurityError):
    """Raised when SQL injection is detected."""

    def __init__(self, message: str = "Potentially dangerous SQL detected"):
        super().__init__(message=message, code="SQL_INJECTION_DETECTED")


# Configuration Errors
class ConfigurationError(OhGrtException):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
    ):
        details = {"config_key": config_key} if config_key else {}
        super().__init__(message, code="CONFIG_ERROR", status_code=500, details=details)
