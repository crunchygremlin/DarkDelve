"""Main renderer for the game."""

from typing import Any, Dict, List, Optional, Tuple

import tcod

from src.presentation.renderers.tile_renderer import TileRenderer


class Renderer:
    """Main game renderer."""
    
    COLORS: Dict[str, Tuple[int, int, int]] = {
        'player': (255, 255, 0),
        'wall': (80, 80, 80),
        'floor': (100, 100, 100),
        'door': (150, 100, 50),
        'gold': (255, 215, 0),
        'blood': (200, 0, 0),
        'poison': (0, 200, 0),
        'magic': (150, 100, 255),
        'water': (100, 150, 255),
        'fire': (255, 100, 0),
        'item': (200, 200, 100),
        'enemy_weak': (100, 200, 100),
        'enemy_normal': (100, 150, 200),
        'enemy_tough': (200, 100, 100),
        'enemy_boss': (255, 0, 0),
        'equipment': (150, 150, 150),
        'text': (220, 220, 220),
        'text_dim': (150, 150, 150),
        'hp_high': (0, 255, 0),
        'hp_med': (255, 255, 0),
        'hp_low': (255, 0, 0),
    }
    
    def __init__(self, width: int = 80, height: int = 50):
        self.width = width
        self.height = height
        self.tile_renderer: Optional[TileRenderer] = None
        self._root_console: Optional[tcod.Console] = None
    
    def initialize(self, tileset_path: Optional[str] = None) -> None:
        """Initialize the renderer."""
        self.tile_renderer = TileRenderer(self.width, self.height)
        self.tile_renderer.initialize(tileset_path)
        
        self._root_console = tcod.console.Console(self.width, self.height)
    
    def print(self, x: int, y: int, text: str, color: Tuple[int, int, int]) -> None:
        """Print text at position."""
        if self._root_console:
            self._root_console.print(x, y, text, fg=color)
    
    def render(self, game_state: Any) -> None:
        """Render the game state."""
        if not self._root_console or not self.tile_renderer:
            return
        
        self._root_console.clear()
        
        # Render map
        if hasattr(game_state, 'game_map'):
            self._render_map(game_state.game_map)
        
        # Render entities
        if hasattr(game_state, 'entities'):
            self._render_entities(game_state.entities)
        
        # Render UI
        if hasattr(game_state, 'player'):
            self._render_hud(game_state.player)
    
    def _render_map(self, game_map: Any) -> None:
        """Render the game map."""
        if not self.tile_renderer:
            return
        
        for y, row in enumerate(game_map):
            for x, tile in enumerate(row):
                if isinstance(tile, dict):
                    char = tile.get('char', '.')
                    color = tile.get('color', self.COLORS['floor'])
                else:
                    char = getattr(tile, 'symbol', '.')
                    color = self.COLORS['floor']
                
                self.tile_renderer.render_tile(x, y, char, color)
    
    def _render_entities(self, entities: List[Any]) -> None:
        """Render game entities."""
        if not self.tile_renderer:
            return
        
        for entity in entities:
            x, y = getattr(entity, 'x', 0), getattr(entity, 'y', 0)
            char = getattr(entity, 'symbol', '@')
            color = self.COLORS['player']
            self.tile_renderer.render_tile(x, y, char, color)
    
    def _render_hud(self, player: Any) -> None:
        """Render the heads-up display."""
        if not self._root_console:
            return
        
        hp = getattr(player, 'hp', 0)
        max_hp = getattr(player, 'max_hp', 1)
        hp_color = self.COLORS['hp_high'] if hp > max_hp * 0.7 else self.COLORS['hp_low']
        
        self._root_console.print(1, 0, f"HP: {hp}/{max_hp}", fg=hp_color)
    
    def present(self) -> None:
        """Present the rendered frame."""
        if self._root_console:
            tcod.console_flush()
    
    def clear(self) -> None:
        """Clear the screen."""
        if self._root_console:
            self._root_console.clear()


class ConsoleRenderer(Renderer):
    """Console-based renderer for backward compatibility."""
    
    def __init__(self, width: int = 80, height: int = 50):
        super().__init__(width, height)


def create_renderer(width: int = 80, height: int = 50) -> Renderer:
    """Factory function to create a renderer."""
    return Renderer(width, height)
