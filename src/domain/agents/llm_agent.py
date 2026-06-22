"""
LLM-based agent implementation for DarkDelve.

This module provides an agent that uses a local LLM (via Ollama)
to make decisions based on game state.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import json
import random

from .base import Agent, AgentType, PerceptionResult
from .actions import AgentAction, ActionType, ActionResult

if TYPE_CHECKING:
    from .state import AgentGameState


@dataclass
class LLMAgentConfig:
    """Configuration for LLM agent."""
    model: str = "qwen2.5-coder:7b-instruct"
    endpoint: str = "http://127.0.0.1:11434"
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 512
    timeout: float = 30.0
    system_prompt: Optional[str] = None
    
    def __post_init__(self):
        self.endpoint = self.endpoint.rstrip("/")


class LLMAgent(Agent):
    """
    Agent that uses a local LLM for decision making.
    
    This agent perceives the game state, constructs a prompt for the LLM,
    and parses the response to determine an action.
    """
    
    DEFAULT_SYSTEM_PROMPT = """You are an AI agent in a roguelike dungeon. Your goal is to survive and explore.
Respond with JSON only:
{
  "action": "MOVE_NORTH|MOVE_SOUTH|MOVE_EAST|MOVE_WEST|ATTACK|PICKUP|WAIT|NONE",
  "target_id": "entity_id or null",
  "target_position": [x, y] or null,
  "reasoning": "brief explanation"
}"""
    
    def __init__(
        self,
        entity: Any,
        agent_type: AgentType = AgentType.NPC,
        name: Optional[str] = None,
        config: Optional[LLMAgentConfig] = None
    ):
        super().__init__(entity, agent_type, name)
        self.config = config or LLMAgentConfig()
        self._history: List[Dict[str, Any]] = []
    
    def perceive(self, game_state: "AgentGameState") -> PerceptionResult:
        """Perceive the current game state."""
        # Get nearby entities and items
        nearby_entities = game_state.get_nearby_entities(radius=15)
        visible_items = [
            i for i in game_state.visible_items
            if i.position and self._distance(self.entity.x, self.entity.y, i.position) <= 15
        ]
        
        return PerceptionResult(
            entity_id=self.entity_id,
            position=(self.entity.x, self.entity.y),
            visible_entities=[e.to_dict() for e in nearby_entities],
            visible_items=[i.to_dict() for i in visible_items],
            health=self.entity.hp,
            max_health=self.entity.max_hp,
            inventory=self.entity.inventory.to_dict() if self.entity.inventory else None,
            game_state=game_state.to_prompt_context(),
        )
    
    def decide(self, perception: PerceptionResult) -> AgentAction:
        """Make a decision using the LLM."""
        # Build prompt from perception
        prompt = self._build_prompt(perception)
        
        # Get LLM response
        response = self._query_llm(prompt)
        
        # Parse response
        action = self._parse_response(response)
        
        # Record in history
        self._history.append({
            "perception": perception.to_prompt_context(),
            "response": response,
            "action": action.to_dict() if hasattr(action, 'to_dict') else str(action)
        })
        self._history = self._history[-10:]  # Keep last 10 turns
        
        return action
    
    def execute(self, action: AgentAction, game_context: Dict[str, Any]) -> ActionResult:
        """Execute an action."""
        # For now, return the action for the game to execute
        # The game will handle actual execution
        return ActionResult(
            success=True,
            message=f"Action {action.action_type.name} queued for execution",
            action=action
        )
    
    def _build_prompt(self, perception: PerceptionResult) -> str:
        """Build a prompt from the perception result."""
        lines = [
            self.config.system_prompt or self.DEFAULT_SYSTEM_PROMPT,
            "",
            "Current state:",
            perception.to_prompt_context(),
        ]
        
        if self._history:
            lines.append("\nRecent history:")
            for h in self._history[-3:]:
                lines.append(f"  Action: {h.get('action', 'unknown')}")
        
        return "\n".join(lines)
    
    def _query_llm(self, prompt: str) -> str:
        """Query the LLM for a response."""
        try:
            import requests
            
            payload = {
                "model": self.config.model,
                "prompt": prompt,
                "stream": False,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "num_predict": self.config.max_tokens,
            }
            
            response = requests.post(
                f"{self.config.endpoint}/api/generate",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "{}")
        except Exception as e:
            print(f"LLM query failed: {e}")
        
        return "{}"
    
    def _parse_response(self, response: str) -> AgentAction:
        """Parse LLM response into an action."""
        try:
            data = json.loads(response)
            action_str = data.get("action", "NONE")
            target_id = data.get("target_id")
            target_pos = data.get("target_position")
            
            # Map action string to ActionType
            action_map = {
                "MOVE_NORTH": ActionType.MOVE_NORTH,
                "MOVE_SOUTH": ActionType.MOVE_SOUTH,
                "MOVE_EAST": ActionType.MOVE_EAST,
                "MOVE_WEST": ActionType.MOVE_WEST,
                "ATTACK": ActionType.ATTACK,
                "ATTACK_TARGET": ActionType.ATTACK_TARGET,
                "PICKUP": ActionType.PICKUP,
                "WAIT": ActionType.WAIT,
                "NONE": ActionType.NONE,
            }
            
            action_type = action_map.get(action_str, ActionType.NONE)
            
            return AgentAction(
                action_type=action_type,
                target_id=target_id if target_id else None,
                target_position=tuple(target_pos) if target_pos else None,
            )
        except json.JSONDecodeError:
            return AgentAction(action_type=ActionType.NONE)
    
    def _distance(self, x1: int, y1: int, x2: int, y2: int) -> int:
        """Calculate Manhattan distance."""
        return abs(x1 - x2) + abs(y1 - y2)


class RandomAgent(Agent):
    """
    A simple agent that makes random decisions.
    
    Useful for testing and as a baseline for comparison.
    """
    
    def __init__(self, entity: Any, agent_type: AgentType = AgentType.NPC, name: Optional[str] = None):
        super().__init__(entity, agent_type, name)
        self._possible_actions = [
            ActionType.MOVE_NORTH, ActionType.MOVE_SOUTH,
            ActionType.MOVE_EAST, ActionType.MOVE_WEST,
            ActionType.ATTACK, ActionType.PICKUP,
            ActionType.WAIT
        ]
    
    def perceive(self, game_state: "AgentGameState") -> PerceptionResult:
        """Perceive the current game state."""
        from .state import PerceptionResult
        
        return PerceptionResult(
            entity_id=self.entity_id,
            position=(self.entity.x, self.entity.y),
            visible_entities=[e.to_dict() for e in game_state.visible_entities],
            visible_items=[i.to_dict() for i in game_state.visible_items],
            health=self.entity.hp,
            max_health=self.entity.max_hp,
        )
    
    def decide(self, perception: PerceptionResult) -> AgentAction:
        """Make a random decision."""
        # Simple random decision making
        if perception.visible_entities and random.random() < 0.3:
            # Attack a visible entity
            target = random.choice(perception.visible_entities)
            return AgentAction(
                action_type=ActionType.ATTACK,
                target_id=target.get("id")
            )
        elif perception.visible_items and random.random() < 0.3:
            # Move towards an item
            item = random.choice(perception.visible_items)
            pos = item.get("position", (0, 0))
            return AgentAction(
                action_type=ActionType.MOVE_TO,
                target_position=pos
            )
        else:
            # Random movement or wait
            return AgentAction(action_type=random.choice(self._possible_actions))
    
    def execute(self, action: AgentAction, game_context: Dict[str, Any]) -> ActionResult:
        """Execute an action."""
        return ActionResult(
            success=True,
            message=f"Random action {action.action_type.name} executed",
            action=action
        )