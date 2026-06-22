"""Tile renderer for game rendering."""

from typing import Dict, List, Optional, Tuple

import tcod


class TileRenderer:
    """Render tiles for the game map."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.tileset: Optional[tcod.tileset.Tileset] = None
        self.console: Optional[tcod.Console] = None
    
    def initialize(self, tileset_path: Optional[str] = None) -> None:
        """Initialize the tile renderer."""
        if tileset_path:
            self.tileset = tcod.tileset.load_tileset(tileset_path)
        else:
            self.tileset = tcod.tileset.procedural_ascii()
        
        self.console = tcod.console.Console(self.width, self.height)
    
    def render_tile(self, x: int, y: int, char: str, color: Tuple[int, int, int]) -> None:
        """Render a single tile."""
        if self.console:
            self.console.print(x, y, char, fg=color)
    
    def render_map(self, game_map: List[List[Dict]], camera: Optional[Tuple[int, int]] = None) -> None:
        """Render the game map."""
        if not self.console:
            return
        
        for y, row in enumerate(game_map):
            for x, tile in enumerate(row):
                char = tile.get('char', '.')
                color = tile.get('color', (255, 255, 255))
                self.render_tile(x, y, char, color)
    
    def clear(self) -> None:
        """Clear the console."""
        if self.console:
            self.console.clear()
    
    def get_console(self) -> Optional[tcod.Console]:
        """Get the console for presentation."""
        return self.console