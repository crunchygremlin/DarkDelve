"""
MCP Map Tools - Register map-building tools for playtester/DM use.

Extends the existing MCPToolkit with map building capabilities.
"""

import json
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.infrastructure.services.mcp_toolkit import MCPToolkit, ToolResult, TOOL_REGISTRY
from src.domain.services.map_builder import MapBuilder


class MCPMapTools:
    """
    Extended MCP toolkit with map building tools.

    Provides tools for:
    - Building maps from descriptions (LLM or procedural)
    - Modifying existing maps
    - Validating maps
    - Getting/setting map state
    """

    def __init__(self, game: Any = None, llm_map_generator: Any = None):
        self.game = game
        self.llm_generator = llm_map_generator
        self._map_builder: Optional[MapBuilder] = None

    # --- Tool: build_map_procedural ---
    def build_map_procedural(
        self,
        width: int = 60,
        height: int = 40,
        room_count: int = 6,
        seed: Optional[int] = None,
    ) -> ToolResult:
        """
        Build a procedural dungeon map.

        Args:
            width: Map width
            height: Map height
            room_count: Number of rooms
            seed: Random seed for reproducibility

        Returns:
            ToolResult with map data or error
        """
        if self.game is None:
            return ToolResult(success=False, error="Game instance not available")

        try:
            builder = MapBuilder(width=width, height=height)
            builder.generate_procedural(room_count=room_count, seed=seed)

            success = builder.apply_to_game(self.game)
            if not success:
                validation = builder.validate_map()
                return ToolResult(
                    success=False,
                    error=f"Map validation failed: {validation['errors']}"
                )

            self._map_builder = builder
            map_data = builder.get_map_data()

            # Update FOV and explored
            if hasattr(self.game, 'fov_system'):
                self.game.fov = self.game.fov_system.compute(
                    self.game.dungeon_map,
                    self.game.player.x,
                    self.game.player.y
                )
                self.game.explored = self.game.fov_system.explored.copy()

            return ToolResult(
                success=True,
                value={
                    "message": f"Built procedural map: {room_count} rooms",
                    "map_data": map_data,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    # --- Tool: build_map_from_description ---
    def build_map_from_description(
        self,
        description: str,
        depth: int = 1,
    ) -> ToolResult:
        """
        Build a dungeon map from a natural language description.

        Uses LLM if available, falls back to procedural generation.

        Args:
            description: Natural language description of the map
            depth: Dungeon depth for difficulty scaling

        Returns:
            ToolResult with map data or error
        """
        if self.game is None:
            return ToolResult(success=False, error="Game instance not available")

        try:
            width = self.game.config['dungeon']['width']
            height = self.game.config['dungeon']['height']

            if self.llm_generator:
                builder, used_llm = self.llm_generator.generate_map(
                    description=description,
                    width=width,
                    height=height,
                    depth=depth,
                )
                if builder:
                    success = builder.apply_to_game(self.game)
                    if success:
                        self._map_builder = builder
                        return ToolResult(
                            success=True,
                            value={
                                "message": f"Built map from description (LLM={used_llm})",
                                "map_data": builder.get_map_data(),
                                "used_llm": used_llm,
                            }
                        )

            # Fallback to procedural
            builder = MapBuilder(width=width, height=height)
            builder.generate_procedural()
            success = builder.apply_to_game(self.game)
            if success:
                self._map_builder = builder
                return ToolResult(
                    success=True,
                    value={
                        "message": "Built map from procedural fallback",
                        "map_data": builder.get_map_data(),
                        "used_llm": False,
                    }
                )

            return ToolResult(success=False, error="Failed to build any map")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    # --- Tool: modify_map ---
    def modify_map(self, commands: List[Dict[str, Any]]) -> ToolResult:
        """
        Apply modification commands to the current map.

        Commands format:
        [
            {"action": "create_room", "x": 5, "y": 5, "width": 10, "height": 8},
            {"action": "create_corridor", "start": [15, 9], "end": [25, 9]},
            {"action": "place_entity", "x": 7, "y": 7, "type": "goblin"},
            {"action": "create_stair_down", "x": 25, "y": 14},
        ]

        Args:
            commands: List of modification commands

        Returns:
            ToolResult with success/failure
        """
        if self.game is None:
            return ToolResult(success=False, error="Game instance not available")

        if self._map_builder is None:
            # Create builder from current game state
            self._map_builder = MapBuilder(
                width=self.game.dungeon_map.shape[0],
                height=self.game.dungeon_map.shape[1],
            )
            self._map_builder.dungeon_map = self.game.dungeon_map.copy()

        try:
            for cmd in commands:
                action = cmd.get("action")

                if action == "create_room":
                    self._map_builder.create_room(
                        x=cmd["x"], y=cmd["y"],
                        width=cmd["width"], height=cmd["height"],
                    )
                elif action == "create_corridor":
                    self._map_builder.create_corridor(
                        start=tuple(cmd["start"]),
                        end=tuple(cmd["end"]),
                        width=cmd.get("width", 1),
                    )
                elif action == "create_stair_down":
                    self._map_builder.create_stair_down(cmd["x"], cmd["y"])
                elif action == "create_stair_up":
                    self._map_builder.create_stair_up(cmd["x"], cmd["y"])
                elif action == "place_entity":
                    self._map_builder.place_entity(
                        x=cmd["x"], y=cmd["y"],
                        entity_type=cmd["type"],
                        name=cmd.get("name"),
                    )
                else:
                    return ToolResult(success=False, error=f"Unknown action: {action}")

            # Validate after all modifications
            validation = self._map_builder.validate_map()
            if not validation["valid"]:
                return ToolResult(
                    success=False,
                    error=f"Modified map failed validation: {validation['errors']}"
                )

            # Apply to game
            success = self._map_builder.apply_to_game(self.game)
            if not success:
                return ToolResult(success=False, error="Failed to apply modified map")

            return ToolResult(
                success=True,
                value={"message": f"Applied {len(commands)} map modifications"}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    # --- Tool: validate_current_map ---
    def validate_current_map(self) -> ToolResult:
        """
        Validate the current game map for connectivity and reachability.

        Returns:
            ToolResult with validation results
        """
        if self.game is None:
            return ToolResult(success=False, error="Game instance not available")

        if self.game.dungeon_map is None:
            return ToolResult(success=False, error="No map to validate")

        try:
            builder = MapBuilder(
                width=self.game.dungeon_map.shape[0],
                height=self.game.dungeon_map.shape[1],
            )
            builder.dungeon_map = self.game.dungeon_map.copy()

            # Detect rooms and corridors from map
            # (Simple flood-fill room detection)
            visited = set()
            for x in range(builder.width):
                for y in range(builder.height):
                    if not builder.dungeon_map[x, y] and (x, y) not in visited:
                        # Found a new room area - flood fill
                        room_tiles = []
                        queue = [(x, y)]
                        while queue:
                            cx, cy = queue.pop(0)
                            if (cx, cy) in visited:
                                continue
                            if cx < 0 or cx >= builder.width or cy < 0 or cy >= builder.height:
                                continue
                            if builder.dungeon_map[cx, cy]:
                                continue
                            visited.add((cx, cy))
                            room_tiles.append((cx, cy))
                            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                                queue.append((cx + dx, cy + dy))

                        if room_tiles:
                            min_x = min(t[0] for t in room_tiles)
                            min_y = min(t[1] for t in room_tiles)
                            max_x = max(t[0] for t in room_tiles)
                            max_y = max(t[1] for t in room_tiles)
                            builder.rooms.append(type('Room', (), {
                                'x': min_x, 'y': min_y,
                                'width': max_x - min_x + 1,
                                'height': max_y - min_y + 1,
                                'center': ((min_x + max_x) // 2, (min_y + max_y) // 2),
                            }))

            validation = builder.validate_map()
            return ToolResult(
                success=validation["valid"],
                value=validation,
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    # --- Tool: get_map_state ---
    def get_map_state(self) -> ToolResult:
        """
        Get the current map state (dimensions, room count, stair positions).

        Returns:
            ToolResult with map state summary
        """
        if self.game is None:
            return ToolResult(success=False, error="Game instance not available")

        if self.game.dungeon_map is None:
            return ToolResult(success=False, error="No map loaded")

        try:
            height, width = self.game.dungeon_map.shape
            floor_count = int(np.sum(~self.game.dungeon_map))
            wall_count = int(np.sum(self.game.dungeon_map))

            return ToolResult(
                success=True,
                value={
                    "width": width,
                    "height": height,
                    "floor_tiles": floor_count,
                    "wall_tiles": wall_count,
                    "stair_down": self.game.stair_down_pos,
                    "stair_up": self.game.stair_up_pos,
                    "entity_count": len(self.game.entities) if hasattr(self.game, 'entities') else 0,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# --- Register tools in the global TOOL_REGISTRY ---
def register_map_tools():
    """Register map building tools into the global TOOL_REGISTRY."""
    # These are registered as bound methods when an instance is created
    # For the static registry, we register wrapper functions
    TOOL_REGISTRY["build_map_procedural"] = _build_map_procedural_wrapper
    TOOL_REGISTRY["build_map_from_description"] = _build_map_from_description_wrapper
    TOOL_REGISTRY["modify_map"] = _modify_map_wrapper
    TOOL_REGISTRY["validate_current_map"] = _validate_current_map_wrapper
    TOOL_REGISTRY["get_map_state"] = _get_map_state_wrapper


# Module-level wrappers that delegate to a global instance
_global_map_tools_instance: Optional[MCPMapTools] = None


def _set_global_map_tools_instance(instance: MCPMapTools):
    """Set the global instance for wrapper functions."""
    global _global_map_tools_instance
    _global_map_tools_instance = instance


def _build_map_procedural_wrapper(toolkit: MCPToolkit, **kwargs) -> ToolResult:
    if _global_map_tools_instance is None:
        return ToolResult(success=False, error="Map tools not initialized")
    return _global_map_tools_instance.build_map_procedural(**kwargs)


def _build_map_from_description_wrapper(toolkit: MCPToolkit, **kwargs) -> ToolResult:
    if _global_map_tools_instance is None:
        return ToolResult(success=False, error="Map tools not initialized")
    return _global_map_tools_instance.build_map_from_description(**kwargs)


def _modify_map_wrapper(toolkit: MCPToolkit, **kwargs) -> ToolResult:
    if _global_map_tools_instance is None:
        return ToolResult(success=False, error="Map tools not initialized")
    return _global_map_tools_instance.modify_map(**kwargs)


def _validate_current_map_wrapper(toolkit: MCPToolkit, **kwargs) -> ToolResult:
    if _global_map_tools_instance is None:
        return ToolResult(success=False, error="Map tools not initialized")
    return _global_map_tools_instance.validate_current_map(**kwargs)


def _get_map_state_wrapper(toolkit: MCPToolkit, **kwargs) -> ToolResult:
    if _global_map_tools_instance is None:
        return ToolResult(success=False, error="Map tools not initialized")
    return _global_map_tools_instance.get_map_state(**kwargs)
