"""Domain layer exceptions."""

from typing import Any


class DomainException(Exception):
    """Base exception for domain layer errors."""
    
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EntityNotFoundException(DomainException):
    """Raised when an entity cannot be found."""
    pass


class ComponentNotFoundException(DomainException):
    """Raised when a component cannot be found on an entity."""
    pass


class InvalidStateException(DomainException):
    """Raised when an entity is in an invalid state for the requested operation."""
    pass


class CombatErrorException(DomainException):
    """Raised when a combat operation fails."""
    pass


class InventoryFullException(DomainException):
    """Raised when an inventory is full and cannot accept more items."""
    pass