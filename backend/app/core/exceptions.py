from typing import Any, Dict, Optional


class SentinelException(Exception):
    """Base exception for all SENTINEL-related errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class DatabaseException(SentinelException):
    """Exception raised for database operations failure."""

    def __init__(
        self, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, code="DATABASE_ERROR", details=details)


class EntityNotFoundException(SentinelException):
    """Exception raised when a requested resource is not found."""

    def __init__(
        self,
        entity_name: str,
        entity_id: Any,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        message = f"{entity_name} with identity '{entity_id}' not found."
        super().__init__(message, code="NOT_FOUND", details=details)


class EntityAlreadyExistsException(SentinelException):
    """Exception raised when attempting to create a resource that already exists."""

    def __init__(
        self,
        entity_name: str,
        entity_id: Any,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        message = f"{entity_name} with identity '{entity_id}' already exists."
        super().__init__(message, code="ALREADY_EXISTS", details=details)


class ValidationException(SentinelException):
    """Exception raised when input validation fails."""

    def __init__(
        self, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class ExternalServiceException(SentinelException):
    """Exception raised when an third-party API (GitHub, Jira) fails."""

    def __init__(
        self,
        service_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            f"{service_name} API Error: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            details=details,
        )


class AuthenticationException(SentinelException):
    """Exception raised when authentication fails."""

    def __init__(
        self, message: str = "Invalid credentials", details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, code="UNAUTHENTICATED", details=details)


class AuthorizationException(SentinelException):
    """Exception raised when a user is authenticated but not authorized."""

    def __init__(
        self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, code="FORBIDDEN", details=details)
