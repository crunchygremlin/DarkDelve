"""
Integration module for the agent system.

This module provides utilities to connect the agent system with
the existing EnergySystem, LLM infrastructure, and game components.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import sys
import threading
import queue
import time
import traceback

if TYPE_CHECKING:
    from .base import Agent
    from .state import AgentGameState
    from ..entities.entity import Entity


@dataclass
class AgentTurnContext:
    """Context provided to agents during their turn."""
    entity: Any
    game_state: "AgentGameState"
    dungeon_map: Any
    entities: List[Any]
    player: Optional[Any]
    energy_system: Any
    fov: Any
    combat_log: Any
    config: Dict[str, Any]


class AgentTurnProcessor:
    """
    Processes agent turns in integration with the EnergySystem.
    
    This class bridges the gap between the EnergySystem's turn-based
    execution and the agent system's decision-making.
    """
    
    def __init__(self, game: Any):
        """
        Initialize the turn processor.
        
        Args:
            game: The Game instance to process turns for
        """
        self.game = game
        self._llm_queue: Optional[queue.Queue] = None
        self._llm_response_queue: Optional[queue.Queue] = None
    
    def set_llm_queues(self, request_queue: queue.Queue, response_queue: queue.Queue):
        """Set the LLM queues for async processing."""
        self._llm_queue = request_queue
        self._llm_response_queue = response_queue
    
    def process_actor_turn(self, actor: Any, agent: Optional["Agent"]) -> bool:
        """
        Process a single actor's turn.
        
        Args:
            actor: The entity taking its turn
            agent: The agent controlling the actor (if any)
            
        Returns:
            True if the turn was processed, False otherwise
        """
        try:
            # If no agent, use default AI
            if not agent:
                return self._process_default_ai_turn(actor)
            
            # Build game state for agent
            game_state = self._build_agent_game_state()
            game_context = self._build_game_context()
            
            # Let agent act
            result = agent.act(game_state, game_context)
            
            # Execute the action
            return self._execute_agent_action(actor, result.action if result else None)
        except Exception as e:
            # Include full traceback with line numbers for debugging
            error_msg = f"Error in process_actor_turn for {actor.name if hasattr(actor, 'name') else 'unknown'}: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            print(error_msg, file=sys.stderr)
            raise
    
    def _build_agent_game_state(self) -> "AgentGameState":
        """Build an AgentGameState from the current game state."""
        from .state import AgentGameState, EntityState, ItemState
        
        try:
            # Build entity states
            entities = []
            for e in self.game.entities:
                entities.append(EntityState(
                    entity_id=e.id,
                    name=e.name,
                    position=(e.x, e.y),
                    health=e.hp,
                    max_health=e.max_hp,
                    is_alive=e.is_alive,
                    is_commander=getattr(e, 'is_commander', False),
                    is_player=e is self.game.player,
                    symbol=getattr(e, 'char', '@'),
                ))
            
            # Build item states
            items = []
            for e in self.game.entities:
                if hasattr(e, 'item') and e.item:
                    items.append(ItemState(
                        item_id=e.item.id,
                        name=e.item.name,
                        item_type=getattr(e.item, 'item_type', 'misc').value,
                        position=(e.x, e.y),
                        symbol=getattr(e.item, 'symbol', '?'),
                        value=getattr(e.item, 'value', 0),
                    ))
            
            # Get visible entities and items
            visible_entities = []
            visible_items = []
            if self.game.fov is not None:
                for e in self.game.entities:
                    # Explicit bool conversion to avoid NumPy array truth ambiguity
                    # Use .item() to safely extract scalar from numpy array
                    try:
                        fov_value = self.game.fov[e.x, e.y]
                        # Handle case where indexing might return an array instead of scalar
                        if hasattr(fov_value, 'item'):
                            fov_value = fov_value.item()
                        if bool(fov_value):
                            visible_entities.append(EntityState(
                                entity_id=e.id,
                                name=e.name,
                                position=(e.x, e.y),
                                health=e.hp,
                                max_health=e.max_hp,
                                is_alive=e.is_alive,
                                is_commander=getattr(e, 'is_commander', False),
                                is_player=e is self.game.player,
                            ))
                    except (IndexError, ValueError):
                        # Skip entities with invalid positions
                        continue
        except Exception as e:
            # Include full traceback with line numbers for debugging
            error_msg = f"Error in _build_agent_game_state: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            print(error_msg, file=sys.stderr)
            raise
        
        return AgentGameState(
            turn=self.game.turn,
            depth=self.game.state.depth,
            entities=entities,
            items=items,
            player=self._get_player_state(),
            player_position=(self.game.player.x, self.game.player.y) if self.game.player else None,
            visible_entities=visible_entities,
            visible_items=visible_items,
        )
    
    def _get_player_state(self) -> Optional["EntityState"]:
        """Get the player's entity state."""
        from .state import EntityState
        
        if not self.game.player:
            return None
        p = self.game.player
        return EntityState(
            entity_id=p.id,
            name=p.name,
            position=(p.x, p.y),
            health=p.hp,
            max_health=p.max_hp,
            is_alive=p.is_alive,
            is_commander=False,
            is_player=True,
        )
    
    def _build_game_context(self) -> Dict[str, Any]:
        """Build additional context for action execution."""
        return {
            "dungeon_map": self.game.dungeon_map,
            "entities": self.game.entities,
            "player": self.game.player,
            "config": self.game.config,
        }
    
    def _process_default_ai_turn(self, actor: Any) -> bool:
        """Process a turn for an entity without an agent."""
        # Use existing monster AI logic
        if hasattr(self.game, 'monster_turn'):
            self.game.monster_turn(actor)
            return True
        return False
    
    def _execute_agent_action(self, actor: Any, action: Optional["AgentAction"]) -> bool:
        """Execute an action from an agent."""
        from .actions import ActionType
        
        if not action:
            return False
        
        # Handle movement
        if action.is_movement() and self.game.dungeon_map is not None:
            return self._execute_movement(actor, action)
        
        # Handle combat
        if action.is_combat():
            return self._execute_combat(actor, action)
        
        # Handle other actions
        if action.action_type == ActionType.PICKUP:
            if hasattr(self.game, 'pickup_item'):
                return self.game.pickup_item()
        
        if action.action_type == ActionType.WAIT:
            return True
        
        return False
    
    def _execute_movement(self, actor: Any, action: "AgentAction") -> bool:
        """Execute a movement action."""
        from .actions import ActionType
        
        if self.game.dungeon_map is None:
            return False
        
        dx, dy = 0, 0
        if action.action_type == ActionType.MOVE_NORTH:
            dy = -1
        elif action.action_type == ActionType.MOVE_SOUTH:
            dy = 1
        elif action.action_type == ActionType.MOVE_EAST:
            dx = 1
        elif action.action_type == ActionType.MOVE_WEST:
            dx = -1
        elif action.action_type == ActionType.MOVE_TO and action.target_position:
            dx = action.target_position[0] - actor.x
            dy = action.target_position[1] - actor.y
            # Normalize
            if dx != 0 or dy != 0:
                dist = (dx**2 + dy**2) ** 0.5
                dx = int(dx / dist)
                dy = int(dy / dist)
        
        # Check for target entity
        new_x = actor.x + dx
        new_y = actor.y + dy
        
        target_entity = None
        for e in self.game.entities:
            if e is not actor and e.is_alive and e.x == new_x and e.y == new_y and e.blocks:
                target_entity = e
                break
        
        if target_entity:
            self.game.attack(actor, target_entity)
            return True
        elif self.game.dungeon_map is not None:
            return actor.move_to(new_x, new_y, self.game.dungeon_map, self.game.entities)
        
        return False
    
    def _execute_combat(self, actor: Any, action: "AgentAction") -> bool:
        """Execute a combat action."""
        if not action.target_id:
            return False
        
        # Find target
        target = None
        for e in self.game.entities:
            if e.id == action.target_id and e.is_alive:
                target = e
                break
        
        if target:
            self.game.attack(actor, target)
            return True
        return False


def create_agent_game_state_snapshot(game: Any) -> "AgentGameState":
    """
    Create a snapshot of the game state for agent perception.
    
    This is a convenience function for creating AgentGameState instances.
    """
    from .state import AgentGameState, EntityState, ItemState
    
    try:
        entities = []
        for e in game.entities:
            entities.append(EntityState(
                entity_id=e.id,
                name=e.name,
                position=(e.x, e.y),
                health=e.hp,
                max_health=e.max_hp,
                is_alive=e.is_alive,
                is_commander=getattr(e, 'is_commander', False),
                is_player=e is game.player,
            ))
        
        items = []
        for e in game.entities:
            if hasattr(e, 'item') and e.item:
                items.append(ItemState(
                    item_id=e.item.id,
                    name=e.item.name,
                    item_type=getattr(e.item, 'item_type', 'misc').value,
                    position=(e.x, e.y),
                ))
        
        visible_entities = []
        visible_items = []
        # Populate visibility lists only when the field‑of‑view map is available.
        if game.fov is not None:
            for e in game.entities:
                # Explicit bool conversion to avoid NumPy array truth ambiguity
                # Use .item() to safely extract scalar from numpy array
                try:
                    fov_value = game.fov[e.x, e.y]
                    # Handle case where indexing might return an array instead of scalar
                    if hasattr(fov_value, 'item'):
                        fov_value = fov_value.item()
                    if bool(fov_value):
                        visible_entities.append(EntityState(
                            entity_id=e.id,
                            name=e.name,
                            position=(e.x, e.y),
                            health=e.hp,
                            max_health=e.max_hp,
                            is_alive=e.is_alive,
                            is_commander=getattr(e, 'is_commander', False),
                            is_player=e is game.player,
                        ))
                        # If the entity carries an item, include it in the visible items list.
                        if hasattr(e, 'item') and e.item:
                            visible_items.append(ItemState(
                                item_id=e.item.id,
                                name=e.item.name,
                                item_type=getattr(e.item, 'item_type', 'misc').value,
                                position=(e.x, e.y),
                            ))
                except (IndexError, ValueError):
                    # Skip entities with invalid positions
                    continue
    except Exception as e:
        # Include full traceback with line numbers for debugging
        error_msg = f"Error in create_agent_game_state_snapshot: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        raise
    
    return AgentGameState(
        turn=game.turn,
        depth=game.state.depth,
        entities=entities,
        items=items,
        player_position=(game.player.x, game.player.y) if game.player else None,
        visible_entities=visible_entities,
        visible_items=visible_items,
    )
