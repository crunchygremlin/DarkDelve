"""Dungeon Master Agent for LLM-powered game management."""

import json
import time
import uuid
from typing import Dict, List, Optional, Any
from src.domain.value_objects.behavior_script import BehaviorScript
from src.domain.value_objects.perception import PerceptionStatus
from src.domain.value_objects.social import SocialStructure
from src.domain.value_objects.power_levels import PlayerProfile
from src.domain.value_objects.llm_logging import (
    LLMLogger, LLMCallLog, ContextWindowDiagnostics, estimate_tokens
)
from src.domain.services.level_design_service import LevelDesignService

__all__ = ["DungeonMasterAgent"]


class DungeonMasterAgent:
    """
    LLM-powered dungeon master that:
    - Generates behavior scripts for entities based on their perception status
    - Designs levels and seeds items based on player profile
    - Manages social structures and loyalty
    - Requests full map access when needed
    """

    def __init__(
        self,
        ollama_service,
        level_design_service: LevelDesignService,
        llm_logger: LLMLogger,
        social_service=None,
    ):
        self.agent_id = "dungeon_master"
        self.ollama = ollama_service
        self.level_design = level_design_service
        self.logger = llm_logger
        self.social_service = social_service
        self._model_name = "gpt-oss"  # Default model
        self._temperature = 0.7  # Default temperature

    def set_model(self, model_name: str, temperature: float = 0.7):
        """Set the model to use for generation."""
        self._model_name = model_name
        self._temperature = temperature

    def get_performance_report(self) -> str:
        """Get a performance report from the logger."""
        return self.logger.get_performance_report()

    def generate_behavior_script(
        self,
        entity_id: str,
        mob_type: str,
        perception: PerceptionStatus,
        social_context: str,
        valid_conditions: List[str],
        valid_actions: List[str],
    ) -> Optional[BehaviorScript]:
        """Generate a behavior script for an entity via LLM."""
        prompt = self._build_behavior_prompt(
            entity_id, mob_type, perception, social_context,
            valid_conditions, valid_actions
        )
        
        # Estimate tokens and check headroom
        prompt_tokens = self.logger.estimate_prompt_tokens(prompt)
        headroom_diag = self.logger.check_headroom(prompt)
        
        start = time.time()
        try:
            response = self.ollama.generate(prompt)
            latency = (time.time() - start) * 1000
            response_tokens = estimate_tokens(response)
            script = self._parse_behavior_response(entity_id, response, valid_conditions, valid_actions)
            
            # Calculate context after the call
            context_after = headroom_diag.max_context_tokens - headroom_diag.headroom_tokens + response_tokens
            
            self.logger.log_call(LLMCallLog(
                call_id=str(uuid.uuid4()),
                timestamp=start,
                context="behavior_generation",
                entity_id=entity_id,
                prompt_summary=prompt[:200],
                response_summary=response[:200],
                latency_ms=latency,
                tokens_used=prompt_tokens + response_tokens,
                success=True,
                behavior_script_id=script.script_id if script else None,
                prompt_tokens=prompt_tokens,
                response_tokens=response_tokens,
                context_before_tokens=headroom_diag.max_context_tokens - headroom_diag.headroom_tokens,
                context_after_tokens=context_after,
                context_headroom=headroom_diag.max_context_tokens - context_after,
                model=self._model_name,
                temperature=self._temperature,
            ))
            return script
        except Exception as e:
            latency = (time.time() - start) * 1000
            self.logger.log_call(LLMCallLog(
                call_id=str(uuid.uuid4()),
                timestamp=start,
                context="behavior_generation",
                entity_id=entity_id,
                prompt_summary=prompt[:200],
                response_summary="",
                latency_ms=latency,
                tokens_used=prompt_tokens,
                success=False,
                error=str(e),
                prompt_tokens=prompt_tokens,
                model=self._model_name,
                temperature=self._temperature,
            ))
            return None

    def design_level(
        self,
        player_profile: PlayerProfile,
        level_number: int,
        map_data: Optional[List[List[int]]] = None,
    ) -> Dict[str, Any]:
        """Design a level via LLM based on player profile."""
        prompt = self.level_design._build_level_prompt(player_profile, level_number)
        
        # Estimate tokens and check headroom
        prompt_tokens = self.logger.estimate_prompt_tokens(prompt)
        headroom_diag = self.logger.check_headroom(prompt)
        
        start = time.time()
        try:
            response = self.ollama.generate(prompt)
            latency = (time.time() - start) * 1000
            response_tokens = estimate_tokens(response)
            level_config = self.level_design._parse_level_response(response)
            
            # Calculate context after the call
            context_after = headroom_diag.max_context_tokens - headroom_diag.headroom_tokens + response_tokens
            
            self.logger.log_call(LLMCallLog(
                call_id=str(uuid.uuid4()),
                timestamp=start,
                context="level_design",
                entity_id=None,
                prompt_summary=prompt[:200],
                response_summary=response[:200],
                latency_ms=latency,
                tokens_used=prompt_tokens + response_tokens,
                success=True,
                prompt_tokens=prompt_tokens,
                response_tokens=response_tokens,
                context_before_tokens=headroom_diag.max_context_tokens - headroom_diag.headroom_tokens,
                context_after_tokens=context_after,
                context_headroom=headroom_diag.max_context_tokens - context_after,
                model=self._model_name,
                temperature=self._temperature,
            ))
            return level_config
        except Exception as e:
            latency = (time.time() - start) * 1000
            self.logger.log_call(LLMCallLog(
                call_id=str(uuid.uuid4()),
                timestamp=start,
                context="level_design",
                entity_id=None,
                prompt_summary=prompt[:200],
                response_summary="",
                latency_ms=latency,
                tokens_used=prompt_tokens,
                success=False,
                error=str(e),
                prompt_tokens=prompt_tokens,
                model=self._model_name,
                temperature=self._temperature,
            ))
            return {}

    def _build_behavior_prompt(
        self, entity_id, mob_type, perception, social_context,
        valid_conditions, valid_actions
    ) -> str:
        """Build the behavior generation prompt for the LLM."""
        perception_summary = f"""
- Can see player: {perception.can_see_player}
- Can hear player: {perception.can_hear_player}
- Player noise level: {perception.player_noise_level:.1f}
- Player distance estimate: {perception.player_distance_estimate:.1f}
- Visible threats: {len(perception.visible_threats)}
- Visible allies: {len(perception.visible_allies)}
- Visible items: {len(perception.visible_items)}
- Environment danger: {perception.environment_danger:.1f}
- Light level: {perception.light_level:.1f}
- Time since player seen: {perception.time_since_player_seen:.1f}s
"""
        return f"""You are the dungeon master for a roguelike game. Generate a behavior script for an entity.

ENTITY: {entity_id} (type: {mob_type})

PERCEPTION STATUS:
{perception_summary}

SOCIAL CONTEXT:
{social_context}

AVAILABLE CONDITIONS: {', '.join(valid_conditions)}
AVAILABLE ACTIONS: {', '.join(valid_actions)}

Respond with a JSON behavior tree. Use this exact format:
{{
  "script_id": "script_{entity_id}",
  "root": {{
    "node_id": "root",
    "node_type": "selector",
    "priority": 0,
    "children": [
      {{
        "node_id": "combat_check",
        "node_type": "sequence",
        "priority": 10,
        "conditions": [{{"condition_type": "can_see_player", "operator": "==", "value": true}}],
        "action": {{"action_type": "attack", "target": "player"}}
      }},
      {{
        "node_id": "investigate",
        "node_type": "sequence",
        "priority": 5,
        "conditions": [{{"condition_type": "can_hear_player", "operator": "==", "value": true}}],
        "action": {{"action_type": "search", "target": "player_last_known_position"}}
      }},
      {{
        "node_id": "patrol",
        "node_type": "action",
        "priority": 0,
        "action": {{"action_type": "patrol"}}
      }}
    ]
  }}
}}

Respond with ONLY the JSON, no other text."""

    def _parse_behavior_response(
        self, entity_id, response, valid_conditions, valid_actions
    ) -> Optional[BehaviorScript]:
        """Parse LLM response into a BehaviorScript."""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start < 0 or end <= 0:
                return None
            data = json.loads(response[start:end])
            data["entity_id"] = entity_id
            from src.domain.services.behavior_script_service import BehaviorScriptService
            svc = BehaviorScriptService(action_dispatcher=None)
            return svc.parse_script_from_json(data)
        except Exception:
            return None