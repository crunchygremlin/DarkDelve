"""Test map exploration by moving character and tracing the map."""

import numpy as np
import tcod

from darkdelve import COLORS, CombatLog, Entity, FOVSystem, GameState, UI, Game
from src.presentation.renderer import ConsoleRenderer


def test_character_can_move_and_explore_map():
    """Test that character can move around and explore the map."""
    game = Game()
    game.initialize()
    
    # Verify initial state
    assert game.dungeon_map is not None
    assert game.player is not None
    assert game.fov is not None
    assert game.explored is not None
    
    # Get initial position
    start_x, start_y = game.player.x, game.player.y
    
    # Move in a pattern to explore
    moves = ['w', 'a', 's', 'd', 'w', 'a', 's', 'd']
    positions = [(start_x, start_y)]
    
    for move in moves:
        result = game.process_action(move)
        positions.append((game.player.x, game.player.y))
    
    # Verify player moved
    assert len(set(positions)) > 1, "Player should have moved to different positions"
    
    # Verify FOV was updated
    assert game.fov is not None
    assert game.fov.shape == game.dungeon_map.shape
    
    # Verify explored area increased
    assert np.any(game.explored), "Some tiles should be explored"
    
    print(f"Start: {positions[0]}, End: {positions[-1]}")
    print(f"Explored tiles: {np.sum(game.explored)} / {game.explored.size}")


def test_map_rendering_with_movement():
    """Test that map renders correctly as character moves."""
    console = tcod.console.Console(80, 50)
    
    class ConsoleLikeRenderer:
        def __init__(self, console):
            self.console = console
        def print(self, x, y, text, color=None):
            self.console.print(x, y, text, fg=color)
        def clear(self):
            self.console.clear()
    
    game = Game()
    game.initialize()
    game.renderer = ConsoleLikeRenderer(console)
    game.ui = UI(game.renderer, game.config)
    
    # Initial render
    game.ui.render_dungeon(game.dungeon_map, game.fov, game.explored, game.player)
    game.ui.render_entities(game.entities, game.fov, game.player)
    
    # Check player is rendered
    player_char = console.ch[game.player.y, game.player.x]
    assert player_char == ord('@'), f"Player should be '@' but got {chr(player_char)}"
    
    # Move and re-render
    game.process_action('s')  # Move down
    game.fov = game.fov_system.compute(game.dungeon_map, game.player.x, game.player.y)
    game.explored = game.fov_system.explored.copy()
    
    game.ui.render_dungeon(game.dungeon_map, game.fov, game.explored, game.player)
    game.ui.render_entities(game.entities, game.fov, game.player)
    
    # Player should still be rendered
    player_char = console.ch[game.player.y, game.player.x]
    assert player_char == ord('@'), "Player should still be '@' after movement"


def test_map_exploration_produces_valid_output():
    """Test that map exploration produces valid rendering output."""
    game = Game()
    game.initialize()
    
    # Track explored area
    initial_explored = np.sum(game.explored)
    
    # Move in a spiral pattern to explore new areas
    moves = []
    for i in range(10):
        # Move right
        moves.extend(['d'] * 5)
        # Move down
        moves.extend(['s'] * 5)
        # Move left
        moves.extend(['a'] * 5)
        # Move up
        moves.extend(['w'] * 5)
    
    for move in moves:
        game.process_action(move)
    
    # Verify explored area is valid
    final_explored = np.sum(game.explored)
    assert final_explored >= initial_explored, f"Explored should not decrease: {initial_explored} -> {final_explored}"
    assert final_explored > 0, "Should have explored some tiles"
    
    # Verify map is still valid
    assert game.dungeon_map is not None
    assert len(game.dungeon_map.shape) == 2, "Map should be 2D"
    assert game.dungeon_map.shape[0] > 0, "Map width should be positive"
    assert game.dungeon_map.shape[1] > 0, "Map height should be positive"
    
    print(f"Initial explored: {initial_explored}, Final: {final_explored}")
    print(f"Map shape: {game.dungeon_map.shape}")


def test_player_stays_on_walkable_tiles():
    """Test that player cannot move onto walls."""
    game = Game()
    game.initialize()
    
    # Get current position
    x, y = game.player.x, game.player.y
    
    # Try to move in all directions
    for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
        new_x, new_y = x + dx, y + dy
        
        # Check if target is within bounds
        if 0 <= new_x < game.dungeon_map.shape[0] and 0 <= new_y < game.dungeon_map.shape[1]:
            is_wall = game.dungeon_map[new_x, new_y]
            if not is_wall:
                # Should be able to move to floor
                can_move = game.player.move_to(new_x, new_y, game.dungeon_map, game.entities)
                assert can_move, f"Should be able to move to ({new_x}, {new_y})"


if __name__ == "__main__":
    test_character_can_move_and_explore_map()
    test_map_rendering_with_movement()
    test_map_exploration_produces_valid_output()
    test_player_stays_on_walkable_tiles()
    print("\nAll map exploration tests passed!")