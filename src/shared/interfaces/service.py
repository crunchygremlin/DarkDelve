"""Service interface for domain services."""

from abc import ABC, abstractmethod
from typing import Any


class Service(ABC):
    """Base service interface."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the service."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up service resources."""
        pass