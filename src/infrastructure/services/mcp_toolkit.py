"""MCP Toolkit for LLM-driven game manipulation.

This module provides a set of tools that the LLM can invoke to interact
with the game state, create entities, query the map, and update configuration.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import json
import os
import time


@dataclass
class ToolResult:
    """Result of a tool invocation."""
    success: bool
    value: Any = None
    error: str = ""


class MCPToolkit:
    """A collection of tools for LLM interaction with the game."""

    def __init__(self, game: Optional[Any] = None, config_path: str = "llm_state.json"):
        self.game = game
        self.config_path = config_path
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        """Ensure the live config file exists."""
        if not os.path.exists(self.config_path):
            self._write_config({})

    def _read_config(self) -> Dict[str, Any]:
        """Read the live config file."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_config(self, data: Dict[str, Any]) -> None:
        """Write to the live config file."""
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)

    # --- Tool: create_mob ---
    def create_mob(self, mob_type: str, position: Tuple[int, int], name: Optional[str] = None) -> ToolResult:
        """Create a new monster at the specified position."""
        if self.game is None:
            return ToolResult(success=False, error="Game instance not available")

        try:
            from src.domain.entities.mob import Mob
            from src.domain.value_objects.position import Position

            pos = Position(position[0], position[1])
            mob = Mob(position=pos, name=name or mob_type, mob_type=mob_type)
            self.game.add_entity(mob)
            return ToolResult(success=True, value={"id": mob.id, "name": mob.name})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    # --- Tool: add_item ---
    def add_item(self, entity_id: str, item_id: str, position: Optional[Tuple[int, int]] = None) -> ToolResult:
        """Add an item to an entity's inventory or spawn it on the map."""
        if self.game is None:
            return ToolResult(success=False, error="Game instance not available")

        try:
            entity = self.game.get_entity(entity_id)
            if entity is None:
                return ToolResult(success=False, error=f"Entity {entity_id} not found")

            # Check if entity has inventory
            if hasattr(entity, "inventory") and entity.inventory:
                entity.inventory.add_item(item_id)
                return ToolResult(success=True, value={"item_id": item_id, "added_to": entity_id})
            else:
                return ToolResult(success=False, error=f"Entity {entity_id} has no inventory")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    # --- Tool: modify_stat ---
    def modify_stat(self, entity_id: str, stat: str, delta: int) -> ToolResult:
        """Modify a stat on an entity (e.g., health, strength)."""
        if self.game is None:
            return ToolResult(success=False, error="Game instance not available")

        try:
            entity = self.game.get_entity(entity_id)
            if entity is None:
                return ToolResult(success=False, error=f"Entity {entity_id} not found")

            # Handle health specially
            if stat == "health":
                entity.health = max(0, entity.health + delta)
                return ToolResult(success=True, value={"health": entity.health})
            elif stat == "max_health":
                entity.max_health = max(1, entity.max_health + delta)
                return ToolResult(success=True, value={"max_health": entity.max_health})
            elif hasattr(entity, "stats") and hasattr(entity.stats, stat):
                setattr(entity.stats, stat, getattr(entity.stats, stat) + delta)
                return ToolResult(success=True, value={stat: getattr(entity.stats, stat)})
            else:
                return ToolResult(success=False, error=f"Stat {stat} not found on entity {entity_id}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    # --- Tool: request_map_section ---
    def request_map_section(self, x: int, y: int, width: int, height: int) -> ToolResult:
        """Request a section of the dungeon map."""
        if self.game is None:
            return ToolResult(success=False, error="Game instance not available")

        try:
            # Get the dungeon map
            dungeon_map = getattr(self.game, "dungeon_map", None)
            if dungeon_map is None:
                return ToolResult(success=False, error="No dungeon map available")

            # Extract the requested section
            section = []
            for dy in range(height):
                row = []
                for dx in range(width):
                    px, py = x + dx, y + dy
                    if 0 <= py < len(dungeon_map) and 0 <= px < len(dungeon_map[0]):
                        row.append(dungeon_map[py][px])
                    else:
                        row.append(False)
                section.append(row)

            return ToolResult(success=True, value={"section": section, "x": x, "y": y, "width": width, "height": height})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    # --- Tool: write_live_config ---
    def write_live_config(self, key: str, value: Any) -> ToolResult:
        """Write a key-value pair to the live config file."""
        try:
            config = self._read_config()
            config[key] = value
            self._write_config(config)
            return ToolResult(success=True, value={key: value})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    # --- Tool: read_live_config ---
    def read_live_config(self, key: Optional[str] = None) -> ToolResult:
        """Read from the live config file, optionally for a specific key."""
        try:
            config = self._read_config()
            if key:
                return ToolResult(success=True, value=config.get(key))
            return ToolResult(success=True, value=config)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    # --- Tool: list_entities ---
    def list_entities(self) -> ToolResult:
        """List all entities in the game."""
        if self.game is None:
            return ToolResult(success=False, error="Game instance not available")

        try:
            entities = []
            for e in self.game.entities:
                entities.append({
                    "id": e.id,
                    "name": e.name,
                    "position": (e.x, e.y) if hasattr(e, "x") and hasattr(e, "y") else None,
                    "type": type(e).__name__,
                })
            return ToolResult(success=True, value=entities)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    # --- Tool: send_message ---
    def send_message(self, message: str, recipient: Optional[str] = None) -> ToolResult:
        """Send a message to the player or log it."""
        if self.game is None:
            return ToolResult(success=False, error="Game instance not available")

        try:
            if hasattr(self.game, "message"):
                self.game.message(message, recipient)
            return ToolResult(success=True, value={"message": message})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# Tool registry for MCP
TOOL_REGISTRY: Dict[str, callable] = {
    "create_mob": MCPToolkit.create_mob,
    "add_item": MCPToolkit.add_item,
    "modify_stat": MCPToolkit.modify_stat,
    "request_map_section": MCPToolkit.request_map_section,
    "write_live_config": MCPToolkit.write_live_config,
    "read_live_config": MCPToolkit.read_live_config,
    "list_entities": MCPToolkit.list_entities,
    "send_message": MCPToolkit.send_message,
}


def invoke_tool(toolkit: MCPToolkit, tool_name: str, **kwargs) -> ToolResult:
    """Invoke a tool by name with the given arguments."""
    if tool_name not in TOOL_REGISTRY:
        return ToolResult(success=False, error=f"Unknown tool: {tool_name}")
    return TOOL_REGISTRY[tool_name](toolkit, **kwargs)