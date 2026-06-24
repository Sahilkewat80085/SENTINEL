from typing import Generic, TypeVar

from app.core.exceptions import SentinelException

T = TypeVar("T")


class ServiceResult(Generic[T]):
    """Monadic/wrapper return type for services to return either a success value or a failure exception."""

    def __init__(
        self,
        value: T | None = None,
        error: SentinelException | None = None,
        is_success: bool = True,
    ) -> None:
        self._value = value
        self._error = error
        self._is_success = is_success

    @property
    def value(self) -> T:
        """Returns the success value. Raises ValueError if this is a failure result."""
        if not self._is_success:
            raise ValueError(
                f"Cannot retrieve value from a failed ServiceResult: {self._error}"
            )
        # Type casting helper, since we know it's not None on success
        return self._value  # type: ignore[return-value]

    @property
    def error(self) -> SentinelException:
        """Returns the failure exception. Raises ValueError if this is a success result."""
        if self._is_success:
            raise ValueError("Cannot retrieve error from a successful ServiceResult")
        assert self._error is not None
        return self._error

    @property
    def is_success(self) -> bool:
        """Returns True if the result is successful."""
        return self._is_success

    @property
    def is_failure(self) -> bool:
        """Returns True if the result is a failure."""
        return not self._is_success

    @classmethod
    def success(cls, value: T) -> "ServiceResult[T]":
        """Factory method to create a successful result."""
        return cls(value=value, is_success=True)

    @classmethod
    def failure(cls, error: SentinelException) -> "ServiceResult[T]":
        """Factory method to create a failed result."""
        return cls(error=error, is_success=False)

    def __repr__(self) -> str:
        if self._is_success:
            return f"ServiceResult(Success: {self._value})"
        return f"ServiceResult(Failure: {self._error})"
