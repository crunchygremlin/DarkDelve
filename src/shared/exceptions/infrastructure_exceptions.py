"""Infrastructure layer exceptions."""

from typing import Any


class InfrastructureException(Exception):
    """Base exception for infrastructure layer errors."""
    
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class RepositoryException(InfrastructureException):
    """Raised when repository operations fail."""
    pass


class ConfigurationException(InfrastructureException):
    """Raised when configuration loading or validation fails."""
    pass


class PersistenceException(InfrastructureException):
    """Raised when persistence operations fail."""
    pass


class ExternalServiceException(InfrastructureException):
    """Raised when external service calls fail."""
    pass


class CacheException(InfrastructureException):
    """Raised when cache operations fail."""
    pass