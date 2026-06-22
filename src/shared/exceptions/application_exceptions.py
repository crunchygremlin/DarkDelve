"""Application layer exceptions."""

from typing import Any


class ApplicationException(Exception):
    """Base exception for application layer errors."""
    
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class CommandException(ApplicationException):
    """Raised when a command fails to execute."""
    pass


class QueryException(ApplicationException):
    """Raised when a query fails."""
    pass


class SessionException(ApplicationException):
    """Raised when session operations fail."""
    pass


class ValidationException(ApplicationException):
    """Raised when validation fails."""
    pass