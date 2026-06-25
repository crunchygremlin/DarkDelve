"""
Base Agent classes and interfaces for the DarkDelve agent system.

This module defines the core abstractions that all agents implement,
including the Agent base class, AgentType enum, and PerceptionResult.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.entity import Entity


class AgentType(Enum):
    """Enumeration of agent types in the game."""
    PLAYER = auto()
    NPC = auto()
    COMMANDER = auto()
    MONSTER = auto()


@dataclass
class PerceptionResult:
    """
    Result of an agent's perception of the game state.
    
    This is a read-only snapshot of relevant game information
    that an agent can use to make decisions.
    """
    entity_id: str
    position: tuple[int, int]
    visible_entities: List[Dict[str, Any]] = field(default_factory=list)
    visible_items: List[Dict[str, Any]] = field(default_factory=list)
    health: int = 100
    max_health: int = 100
    inventory: Optional[Dict[str, Any]] = None
    game_state: Optional[Dict[str, Any]] = None
    fov: Optional[List[List[bool]]] = None
    dungeon_map: Optional[List[List[bool]]] = None
    player_position: Optional[tuple[int, int]] = None
    
    @property
    def health_percent(self) -> float:
        """Return health as a percentage (0.0 to 1.0)."""
        if self.max_health <= 0:
            return 0.0
        return max(0.0, min(1.0, self.health / self.max_health))
    
    def to_prompt_context(self) -> str:
        """Convert perception to a text context for LLM prompts."""
        lines = [
            f"Entity: {self.entity_id} at {self.position}",
            f"Health: {self.health}/{self.max_health} ({self.health_percent:.0%})",
        ]
        
        if self.visible_entities:
            lines.append("Visible entities:")
            for e in self.visible_entities[:5]:
                lines.append(f"  - {e.get('name', 'unknown')} at {e.get('position', 'unknown')}")
        
        if self.visible_items:
            lines.append("Visible items:")
            for i in self.visible_items[:5]:
                lines.append(f"  - {i.get('name', 'unknown')}")
        
        return "\n".join(lines)


class Agent(ABC):
    """
    Abstract base class for all agents in the game.
    
    Agents are autonomous entities that can perceive the game state,
    make decisions, and execute actions. They integrate with the EnergySystem
    for turn-based execution.
    """
    
    def __init__(
        self,
        entity: "Entity",
        agent_type: AgentType = AgentType.NPC,
        name: Optional[str] = None
    ):
        self.entity = entity
        self.agent_type = agent_type
        self.name = name or entity.name if entity else "Agent"
        self._last_perception: Optional[PerceptionResult] = None
        self._last_action: Optional["AgentAction"] = None
    
    @property
    def entity_id(self) -> str:
        """Return the entity's unique identifier."""
        return self.entity.id if self.entity else ""
    
    @property
    def is_alive(self) -> bool:
        """Check if the agent's entity is alive."""
        return self.entity.is_alive if self.entity else False
    
    @abstractmethod
    def perceive(self, game_state: "AgentGameState") -> PerceptionResult:
        """
        Perceive the current game state.
        
        Args:
            game_state: The current game state snapshot
            
        Returns:
            A PerceptionResult containing relevant game information
        """
        pass
    
    @abstractmethod
    def decide(self, perception: PerceptionResult) -> "AgentAction":
        """
        Make a decision based on the perceived state.
        
        Args:
            perception: The result of the agent's perception
            
        Returns:
            An AgentAction to execute
        """
        pass
    
    def execute(self, action: "AgentAction", game_context: Dict[str, Any]) -> "ActionResult":
        """
        Execute an action in the game context.
        
        Args:
            action: The action to execute
            game_context: Context needed to execute the action
            
        Returns:
            The result of the action execution
        """
        # Default implementation - subclasses should override
        return ActionResult(
            success=False,
            message="Execute not implemented for this agent type"
        )
    
    def act(self, game_state: "AgentGameState", game_context: Dict[str, Any]) -> "ActionResult":
        """
        Perform one complete action cycle: perceive, decide, execute.
        
        This is the main entry point for agent behavior.
        
        Args:
            game_state: The current game state
            game_context: Additional context for action execution
            
        Returns:
            The result of the action
        """
        perception = self.perceive(game_state)
        self._last_perception = perception
        
        action = self.decide(perception)
        self._last_action = action
        
        result = self.execute(action, game_context)
        return result
    
    def get_last_perception(self) -> Optional[PerceptionResult]:
        """Return the last perception result."""
        return self._last_perception
    
    def get_last_action(self) -> Optional["AgentAction"]:
        """Return the last action taken."""
        return self._last_action