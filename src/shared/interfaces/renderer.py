"""Renderer interface for rendering system."""

from abc import ABC, abstractmethod
from typing import Any


class Renderer(ABC):
    """Base renderer interface."""
    
    @abstractmethod
    def initialize(self, width: int, height: int) -> None:
        """Initialize the renderer with dimensions."""
        pass
    
    @abstractmethod
    def render(self, context: Any) -> None:
        """Render the given context."""
        pass
    
    @abstractmethod
    def present(self) -> None:
        """Present the rendered frame."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up renderer resources."""
        pass