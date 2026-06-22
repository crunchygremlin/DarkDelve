"""
Agent Action system for DarkDelve.

This module defines the action types that agents can perform,
the AgentAction class, and the ActionResult class.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class ActionType(Enum):
    """Enumeration of possible agent actions."""
    # Movement
    MOVE_NORTH = auto()
    MOVE_SOUTH = auto()
    MOVE_EAST = auto()
    MOVE_WEST = auto()
    MOVE_TO = auto()  # Move to specific coordinates
    
    # Combat
    ATTACK = auto()
    ATTACK_TARGET = auto()  # Attack specific target
    
    # Interaction
    PICKUP = auto()
    USE = auto()
    EQUIP = auto()
    DROP = auto()
    
    # Wait
    WAIT = auto()
    
    # Special
    CAST_SPELL = auto()
    USE_ITEM = auto()
    
    # Commander-specific
    ISSUE_COMMAND = auto()
    HOLD_POSITION = auto()
    FLANK = auto()
    
    # Fallback
    NONE = auto()


@dataclass
class AgentAction:
    """
    Represents an action an agent wants to perform.
    
    Actions are data objects that can be validated and executed
    by the game system.
    """
    action_type: ActionType
    target_id: Optional[str] = None  # For attacking specific entities
    target_position: Optional[tuple[int, int]] = None  # For movement
    target_item_id: Optional[str] = None  # For item interactions
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def move_to(cls, x: int, y: int) -> "AgentAction":
        """Create a move-to action."""
        return cls(action_type=ActionType.MOVE_TO, target_position=(x, y))
    
    @classmethod
    def move_direction(cls, dx: int, dy: int) -> "AgentAction":
        """Create a directional movement action."""
        if dx == 0 and dy == -1:
            return cls(action_type=ActionType.MOVE_NORTH)
        elif dx == 0 and dy == 1:
            return cls(action_type=ActionType.MOVE_SOUTH)
        elif dx == 1 and dy == 0:
            return cls(action_type=ActionType.MOVE_EAST)
        elif dx == -1 and dy == 0:
            return cls(action_type=ActionType.MOVE_WEST)
        return cls(action_type=ActionType.MOVE_TO, target_position=(dx, dy))
    
    @classmethod
    def attack(cls, target_id: str) -> "AgentAction":
        """Create an attack action."""
        return cls(action_type=ActionType.ATTACK, target_id=target_id)
    
    @classmethod
    def pickup(cls) -> "AgentAction":
        """Create a pickup action."""
        return cls(action_type=ActionType.PICKUP)
    
    @classmethod
    def wait(cls) -> "AgentAction":
        """Create a wait action."""
        return cls(action_type=ActionType.WAIT)
    
    @classmethod
    def hold_position(cls) -> "AgentAction":
        """Create a hold position action."""
        return cls(action_type=ActionType.HOLD_POSITION)
    
    def is_movement(self) -> bool:
        """Check if this action is a movement action."""
        return self.action_type in (
            ActionType.MOVE_NORTH, ActionType.MOVE_SOUTH,
            ActionType.MOVE_EAST, ActionType.MOVE_WEST,
            ActionType.MOVE_TO
        )
    
    def is_combat(self) -> bool:
        """Check if this action is a combat action."""
        return self.action_type in (ActionType.ATTACK, ActionType.ATTACK_TARGET)
    
    def to_game_command(self) -> Optional[str]:
        """
        Convert to a simple game command string.
        
        Returns a single character command suitable for the game's
        input handler (e.g., 'w', 'a', 's', 'd', 'e').
        """
        direction_map = {
            ActionType.MOVE_NORTH: 'w',
            ActionType.MOVE_SOUTH: 's',
            ActionType.MOVE_EAST: 'd',
            ActionType.MOVE_WEST: 'a',
            ActionType.WAIT: 'e',
        }
        return direction_map.get(self.action_type)


@dataclass
class ActionResult:
    """
    Result of executing an agent action.
    
    Contains information about whether the action succeeded,
    any messages generated, and additional data.
    """
    success: bool
    message: str = ""
    action: Optional[AgentAction] = None
    data: Dict[str, Any] = field(default_factory=dict)
    feedback: Optional[str] = None  # LLM feedback for the agent
    
    @classmethod
    def success_result(cls, message: str = "Action succeeded", **kwargs) -> "ActionResult":
        """Create a successful result."""
        return cls(success=True, message=message, **kwargs)
    
    @classmethod
    def failure_result(cls, message: str = "Action failed", **kwargs) -> "ActionResult":
        """Create a failed result."""
        return cls(success=False, message=message, **kwargs)
    
    @classmethod
    def no_op(cls) -> "ActionResult":
        """Create a no-op result."""
        return cls(success=True, message="No action taken")