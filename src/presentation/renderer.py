"""
Renderer module for DarkDelve.

This module provides abstract and concrete renderer implementations for the game.
It allows for different rendering backends (console, graphical) to be used interchangeably.
"""

from abc import ABC, abstractmethod
from pathlib import Path
import sys
import tcod
import numpy as np
from typing import Optional, Tuple, Any

# Import configuration - will be passed as parameter


class Renderer(ABC):
    """Abstract base class for all renderer implementations."""

    @abstractmethod
    def clear(self) -> None:
        """Clear the rendering surface."""
        pass

    @abstractmethod
    def print(self, x: int, y: int, text: str, color: Optional[Tuple[int, int, int]] = None) -> None:
        """Print text at the specified position with optional color."""
        pass

    @abstractmethod
    def present(self) -> None:
        """Present the rendered content to the display."""
        pass


class ConsoleRenderer(Renderer):
    """Renderer that uses tcod.console.Console for text-based output."""

    def __init__(self, console: tcod.console.Console, config: dict = None):
        """Initialize with a tcod console instance."""
        self._console = console
        self.config = config or {}

    def clear(self) -> None:
        """Clear the console."""
        self._console.clear()

    def print(self, x: int, y: int, text: str, color: Optional[Tuple[int, int, int]] = None) -> None:
        """Print text at the specified position with optional color."""
        if color is not None:
            self._console.print(x, y, text, fg=color)
        else:
            self._console.print(x, y, text)

    def present(self) -> None:
        """Draw the offscreen console into the terminal without scrolling."""
        frame = "\n".join(
            "".join(chr(int(ch)) if int(ch) else " " for ch in row)
            for row in self._console.ch
        )
        sys.stdout.write(f"\033[H\033[2J{frame}\033[0m\n")
        sys.stdout.flush()


class GraphicalRenderer(Renderer):
    """Renderer that uses tcod.console.Console with graphical context."""

    def __init__(self, console: tcod.console.Console, context: tcod.context.Context, config: dict = None):
        """Initialize with a tcod console and context instance."""
        self._console = console
        self._context = context
        self.config = config or {}

    def clear(self) -> None:
        """Clear the console."""
        self._console.clear()

    def print(self, x: int, y: int, text: str, color: Optional[Tuple[int, int, int]] = None) -> None:
        """Print text at the specified position with optional color."""
        if color is not None:
            self._console.print(x, y, text, fg=color)
        else:
            self._console.print(x, y, text)

    def present(self) -> None:
        """Present the console content to the graphical context."""
        self._context.present(self._console)


def create_renderer(config: dict, renderer_type: str = 'console') -> Renderer:
    """
    Factory function to create the appropriate renderer based on configuration.

    Args:
        config: Game configuration dictionary
        renderer_type: Type of renderer to create ('console' or 'graphical')

    Returns:
        A Renderer instance

    Raises:
        ValueError: If the renderer type is not supported
    """
    screen_width = config['display']['width']
    screen_height = config['display']['height']

    if renderer_type == 'console':
        console = tcod.console.Console(screen_width, screen_height)
        return ConsoleRenderer(console, config)

    elif renderer_type == 'graphical':
        # Load tileset
        tileset_path = Path(config['display']['tileset'])
        if not tileset_path:
            raise ValueError("Tileset path not configured for graphical renderer")

        if not tileset_path.is_absolute():
            project_root = Path(__file__).resolve().parents[2]
            tileset_path = project_root / "assets" / "tilesets" / tileset_path

        # Load the tileset
        tileset = tcod.tileset.load_tilesheet(
            str(tileset_path),
            16, 8, tcod.tileset.CHARMAP_TCOD
        )

        # Create console and context
        console = tcod.console.Console(screen_width, screen_height)
        context = tcod.context.new_terminal(
            columns=screen_width,
            rows=screen_height,
            tileset=tileset,
            title="DarkDelve",
            vsync=True,
        )

        return GraphicalRenderer(console, context, config)

    else:
        raise ValueError(f"Unknown renderer type: {renderer_type}")
