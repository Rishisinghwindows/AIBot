"""
Unit tests for custom exceptions.
"""

import pytest

from app.exceptions import (
    OhGrtException,
    AuthenticationError,
    TokenExpiredError,
    InvalidTokenError,
    ValidationError,
    RateLimitExceededError,
    ResourceNotFoundError,
    ExternalServiceError,
    DatabaseError,
    SQLInjectionError,
)


class TestOhGrtException:
    """Tests for base OhGrtException."""

    def test_basic_exception(self):
        """Test basic exception creation."""
        exc = OhGrtException("Test error")

        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.code == "OHGRT_ERROR"
        assert exc.status_code == 500

    def test_exception_with_details(self):
        """Test exception with additional details."""
        details = {"field": "test", "value": 123}
        exc = OhGrtException("Test error", details=details)

        assert exc.details == details

    def test_to_dict(self):
        """Test converting exception to dictionary."""
        exc = OhGrtException("Test error", code="TEST_CODE", details={"key": "value"})
        result = exc.to_dict()

        assert result["error"] == "TEST_CODE"
        assert result["message"] == "Test error"
        assert result["details"] == {"key": "value"}


class TestAuthenticationError:
    """Tests for authentication errors."""

    def test_default_authentication_error(self):
        """Test default authentication error."""
        exc = AuthenticationError()

        assert exc.message == "Authentication failed"
        assert exc.code == "AUTH_ERROR"
        assert exc.status_code == 401

    def test_custom_authentication_error(self):
        """Test custom authentication error."""
        exc = AuthenticationError("Custom auth error")

        assert exc.message == "Custom auth error"

    def test_token_expired_error(self):
        """Test token expired error."""
        exc = TokenExpiredError()

        assert exc.code == "TOKEN_EXPIRED"
        assert exc.status_code == 401

    def test_invalid_token_error(self):
        """Test invalid token error."""
        exc = InvalidTokenError()

        assert exc.code == "INVALID_TOKEN"
        assert exc.status_code == 401


class TestValidationError:
    """Tests for validation errors."""

    def test_basic_validation_error(self):
        """Test basic validation error."""
        exc = ValidationError("Invalid input")

        assert exc.message == "Invalid input"
        assert exc.code == "VALIDATION_ERROR"
        assert exc.status_code == 400

    def test_validation_error_with_field(self):
        """Test validation error with field name."""
        exc = ValidationError("Invalid email", field="email")

        assert exc.details["field"] == "email"


class TestRateLimitExceededError:
    """Tests for rate limit errors."""

    def test_rate_limit_error(self):
        """Test rate limit exceeded error."""
        exc = RateLimitExceededError()

        assert exc.code == "RATE_LIMIT_EXCEEDED"
        assert exc.status_code == 429

    def test_rate_limit_with_retry_after(self):
        """Test rate limit error with retry_after."""
        exc = RateLimitExceededError(retry_after=60)

        assert exc.retry_after == 60
        assert exc.details["retry_after_seconds"] == 60


class TestResourceNotFoundError:
    """Tests for resource not found errors."""

    def test_basic_not_found(self):
        """Test basic resource not found."""
        exc = ResourceNotFoundError("User")

        assert "User not found" in exc.message
        assert exc.status_code == 404

    def test_not_found_with_id(self):
        """Test resource not found with ID."""
        exc = ResourceNotFoundError("User", resource_id="123")

        assert "123" in exc.message
        assert exc.details["resource_id"] == "123"


class TestExternalServiceError:
    """Tests for external service errors."""

    def test_external_service_error(self):
        """Test external service error."""
        exc = ExternalServiceError("OpenWeather", "API timeout")

        assert "OpenWeather" in exc.message
        assert exc.status_code == 502

    def test_external_service_with_original_error(self):
        """Test external service error with original error."""
        exc = ExternalServiceError(
            "GitHub",
            "Request failed",
            original_error="Connection refused",
        )

        assert exc.details["original_error"] == "Connection refused"


class TestDatabaseError:
    """Tests for database errors."""

    def test_database_error(self):
        """Test database error."""
        exc = DatabaseError("Connection failed")

        assert exc.code == "DATABASE_ERROR"
        assert exc.status_code == 500

    def test_database_error_with_operation(self):
        """Test database error with operation."""
        exc = DatabaseError("Insert failed", operation="insert")

        assert exc.details["operation"] == "insert"


class TestSQLInjectionError:
    """Tests for SQL injection errors."""

    def test_sql_injection_error(self):
        """Test SQL injection error."""
        exc = SQLInjectionError()

        assert exc.code == "SQL_INJECTION_DETECTED"
        assert exc.status_code == 400

    def test_sql_injection_custom_message(self):
        """Test SQL injection error with custom message."""
        exc = SQLInjectionError("DROP TABLE detected")

        assert "DROP TABLE" in exc.message
