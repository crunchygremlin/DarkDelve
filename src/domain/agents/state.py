"""
Game state representation for agents.

This module provides data classes that represent the game state
in a format suitable for agent perception and decision-making.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class EntityState:
    """State of a single entity in the game."""
    entity_id: str
    name: str
    position: tuple[int, int]
    health: int
    max_health: int
    is_alive: bool
    is_commander: bool
    is_player: bool
    symbol: str = "@"
    color: Optional[tuple[int, int, int]] = None
    
    @property
    def health_percent(self) -> float:
        """Return health as a percentage."""
        if self.max_health <= 0:
            return 0.0
        return max(0.0, min(1.0, self.health / self.max_health))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.entity_id,
            "name": self.name,
            "position": self.position,
            "health": self.health,
            "max_health": self.max_health,
            "is_alive": self.is_alive,
            "is_commander": self.is_commander,
            "is_player": self.is_player,
        }


@dataclass
class ItemState:
    """State of an item in the game."""
    item_id: str
    name: str
    item_type: str
    position: tuple[int, int]
    symbol: str = "?"
    value: int = 0
    is_pickable: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.item_id,
            "name": self.name,
            "type": self.item_type,
            "position": self.position,
            "symbol": self.symbol,
            "value": self.value,
        }


@dataclass
class CombatState:
    """State of combat between entities."""
    attacker_id: str
    defender_id: str
    damage: int
    hit: bool
    critical: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "attacker": self.attacker_id,
            "defender": self.defender_id,
            "damage": self.damage,
            "hit": self.hit,
            "critical": self.critical,
        }


@dataclass
class AgentGameState:
    """
    Complete game state snapshot for agent perception.
    
    This class provides a read-only view of the game state that agents
    can use to make decisions. It's designed to be easily serializable
    and suitable for LLM prompts.
    """
    turn: int
    depth: int
    entities: List[EntityState] = field(default_factory=list)
    items: List[ItemState] = field(default_factory=list)
    player: Optional[EntityState] = None
    player_position: Optional[tuple[int, int]] = None
    visible_entities: List[EntityState] = field(default_factory=list)
    visible_items: List[ItemState] = field(default_factory=list)
    explored_tiles: Set[tuple[int, int]] = field(default_factory=set)
    combat_log: List[CombatState] = field(default_factory=list)
    game_flags: Set[str] = field(default_factory=set)
    
    def get_entity(self, entity_id: str) -> Optional[EntityState]:
        """Get an entity by ID."""
        for entity in self.entities:
            if entity.entity_id == entity_id:
                return entity
        return None
    
    def get_entities_at_position(self, x: int, y: int) -> List[EntityState]:
        """Get all entities at a specific position."""
        return [e for e in self.entities if e.position == (x, y)]
    
    def get_nearby_entities(self, radius: int = 5) -> List[EntityState]:
        """Get entities within a radius of the player."""
        if not self.player_position:
            return []
        px, py = self.player_position
        return [
            e for e in self.entities
            if abs(e.position[0] - px) <= radius and abs(e.position[1] - py) <= radius
        ]
    
    def to_prompt_context(self) -> str:
        """Convert game state to a text context for prompts."""
        lines = [
            f"Turn: {self.turn} | Depth: {self.depth}",
            f"Player: {self.player.name if self.player else 'Unknown'} at {self.player_position or 'unknown'}",
            f"HP: {self.player.health}/{self.player.max_health}" if self.player else "HP: unknown",
        ]
        
        if self.visible_entities:
            lines.append("\nVisible entities:")
            for e in self.visible_entities:
                rel_pos = (e.position[0] - self.player_position[0], 
                          e.position[1] - self.player_position[1]) if self.player_position else e.position
                lines.append(f"  {e.name} at {rel_pos} HP:{e.health}/{e.max_health}")
        
        if self.visible_items:
            lines.append("\nVisible items:")
            for i in self.visible_items:
                rel_pos = (i.position[0] - self.player_position[0],
                          i.position[1] - self.player_position[1]) if self.player_position else i.position
                lines.append(f"  {i.name} at {rel_pos}")
        
        return "\n".join(lines)