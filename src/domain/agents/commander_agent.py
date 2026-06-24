"""
Commander agent implementation for DarkDelve.

This module provides a specialized agent for commanding NPCs
and managing tactical decisions in combat.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import json
import random

from .base import Agent, AgentType, PerceptionResult
from .actions import AgentAction, ActionType, ActionResult
from .state import AgentGameState

if TYPE_CHECKING:
    from ..entities.entity import Entity


@dataclass
class CommanderOrder:
    """Represents an order issued by a commander."""
    command: str
    target_id: Optional[str] = None
    target_position: Optional[tuple[int, int]] = None
    shout: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "target_id": self.target_id,
            "target_position": self.target_position,
            "shout": self.shout,
        }


class CommanderAgent(Agent):
    """
    Agent for commanding NPCs in tactical combat.
    
    Commanders issue orders to their subordinates and make
    tactical decisions based on the battlefield state.
    """
    
    VALID_COMMANDS = [
        "ATTACK_PLAYER",
        "DEFEND_COMMANDER",
        "RETREAT_TO_ROOM",
        "HOLD_POSITION",
        "FLANK_LEFT",
        "FLANK_RIGHT",
        "DEFAULT_ATTACK",
        "WAIT"
    ]
    
    def __init__(
        self,
        entity: Any,
        agent_type: AgentType = AgentType.COMMANDER,
        name: Optional[str] = None,
        home_position: Optional[tuple[int, int]] = None
    ):
        super().__init__(entity, agent_type, name)
        self.home_position = home_position or (entity.x, entity.y)
        self._subordinates: List[str] = []
        self._pending_orders: Dict[str, CommanderOrder] = {}
    
    def perceive(self, game_state: "AgentGameState") -> PerceptionResult:
        """Perceive the current game state."""
        from .base import PerceptionResult
        
        # Get nearby entities
        nearby = game_state.get_nearby_entities(radius=20)
        
        return PerceptionResult(
            entity_id=self.entity_id,
            position=(self.entity.x, self.entity.y),
            visible_entities=[e.to_dict() for e in nearby],
            visible_items=[],
            health=self.entity.hp,
            max_health=self.entity.max_hp,
            game_state=game_state.to_prompt_context(),
        )
    
    def decide(self, perception: PerceptionResult) -> AgentAction:
        """Make a tactical decision."""
        # Simple tactical AI for commanders
        player = None
        enemies = []
        
        for e in perception.visible_entities:
            if e.get("is_player"):
                player = e
            elif e.get("is_alive") and not e.get("is_commander"):
                enemies.append(e)
        
        # If player is visible, attack
        if player:
            return AgentAction(
                action_type=ActionType.ATTACK,
                target_id=player.get("id"),
            )
        
        # If enemies are visible, move towards them
        if enemies:
            target = enemies[0]
            pos = target.get("position", (0, 0))
            return AgentAction(
                action_type=ActionType.MOVE_TO,
                target_position=tuple(pos),
            )
        
        # Otherwise, hold position or patrol
        return AgentAction(action_type=ActionType.HOLD_POSITION)
    
    def execute(self, action: AgentAction, game_context: Dict[str, Any]) -> ActionResult:
        """Execute a tactical action."""
        # Store the current command for subordinates to interpret
        if action.action_type == ActionType.ISSUE_COMMAND:
            command = action.parameters.get("command", "WAIT")
            self._pending_orders[action.target_id] = CommanderOrder(
                command=command,
                target_id=action.target_id,
                target_position=action.target_position,
            )
            return ActionResult(
                success=True,
                message=f"Issued order: {command}",
                action=action
            )
        
        # Store the action for the game to interpret
        self.entity.current_command = {
            "command": action.action_type.name,
            "target_id": action.target_id,
            "target_position": action.target_position,
        }
        
        return ActionResult(
            success=True,
            message=f"Command {action.action_type.name} issued",
            action=action
        )
    
    def get_order_for_subordinate(self, subordinate_id: str) -> Optional[CommanderOrder]:
        """Get the pending order for a subordinate."""
        return self._pending_orders.pop(subordinate_id, None)
    
    def add_subordinate(self, entity_id: str):
        """Add a subordinate to command."""
        if entity_id not in self._subordinates:
            self._subordinates.append(entity_id)
    
    def clear_orders(self):
        """Clear all pending orders."""
        self._pending_orders.clear()


class AgentManager:
    """
    Manager for all agents in the game.
    
    This class coordinates agent actions and integrates with the
    EnergySystem for turn-based execution.
    """
    
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._entity_to_agent: Dict[str, Agent] = {}
    
    def register_agent(self, agent: Agent) -> None:
        """Register an agent with the manager."""
        self._agents[agent.entity_id] = agent
        if agent.entity:
            self._entity_to_agent[agent.entity_id] = agent
    
    def unregister_agent(self, entity_id: str) -> None:
        """Unregister an agent."""
        agent = self._agents.pop(entity_id, None)
        if agent and agent.entity:
            self._entity_to_agent.pop(agent.entity_id, None)
    
    def get_agent_for_entity(self, entity: Any) -> Optional[Agent]:
        """Get the agent controlling an entity."""
        return self._agents.get(getattr(entity, 'id', ''))
    
    def get_agent(self, entity_id: str) -> Optional[Agent]:
        """Get an agent by entity ID."""
        return self._agents.get(entity_id)
    
    def process_turn(self, actor: Any, game_state: "AgentGameState", 
                     game_context: Dict[str, Any]) -> Optional[ActionResult]:
        """
        Process one turn for an actor with an agent.
        
        Args:
            actor: The entity taking its turn
            game_state: Current game state
            game_context: Additional context for action execution
            
        Returns:
            The result of the agent's action, or None if no agent
        """
        agent = self.get_agent_for_entity(actor)
        if not agent:
            return None
        
        if not actor.is_alive:
            return ActionResult(success=False, message="Entity is dead")
        
        return agent.act(game_state, game_context)
    
    def get_all_agents(self) -> List[Agent]:
        """Get all registered agents."""
        return list(self._agents.values())
    
    def clear(self):
        """Clear all agents."""
        self._agents.clear()
        self._entity_to_agent.clear()