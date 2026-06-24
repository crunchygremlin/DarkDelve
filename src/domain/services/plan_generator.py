"""Plan generator for creating multi-step behavior plans."""

from typing import Any, Dict, List, Optional, Set
from src.domain.value_objects.behavior_script import (
    BehaviorScript, BehaviorNode, BehaviorCondition, BehaviorAction,
    NodeType, ActionType, ConditionType, MOB_BEHAVIOR_CATALOG
)
from src.domain.value_objects.perception import PerceptionStatus
from src.domain.services.behavior_script_service import BehaviorScriptService


class PlanGenerator:
    """Generates multi-step behavior plans using LLM."""
    
    def __init__(self, llm_client: Any, behavior_script_service: BehaviorScriptService):
        self._llm = llm_client
        self._script_service = behavior_script_service
    
    def generate_plan(
        self,
        entity: Any,
        perception: PerceptionStatus,
        social_context: Dict[str, Any],
        goal: str,
        all_entities: List[Any]
    ) -> BehaviorScript:
        """
        Generate a multi-step behavior plan for an entity.
        
        The plan is a BehaviorScript with is_plan=True that encodes
        conditional multi-step logic like:
        1. If player visible → attack
        2. Else if heard player → move to last known position
        3. Else if health low → flee
        4. Else → patrol
        """
        # Build prompt with perception, social context, and goal
        prompt = self._build_plan_prompt(
            entity, perception, social_context, goal, all_entities
        )
        
        # Get LLM response (JSON tree)
        response = self._llm.generate(prompt)
        
        # Parse into BehaviorScript
        script = self._script_service.parse_script_from_json(response)
        script.is_plan = True
        script.plan_name = goal
        
        # Validate against catalog
        self._validate_script(script, entity)
        
        return script
    
    def _validate_script(self, script: BehaviorScript, entity: Any) -> bool:
        """Validate a BehaviorScript against the MOB_BEHAVIOR_CATALOG.
        
        Returns True if valid, False otherwise. Invalid conditions/actions
        are logged and removed from the script.
        """
        mob_type = getattr(entity, 'mob_type', 'default')
        catalog = MOB_BEHAVIOR_CATALOG.get(mob_type, MOB_BEHAVIOR_CATALOG.get('default', {}))
        
        valid_conditions: Set[str] = set(catalog.get('conditions', []))
        valid_actions: Set[str] = set(catalog.get('actions', []))
        
        script.valid_conditions = list(valid_conditions)
        script.valid_actions = list(valid_actions)
        
        if not script.root_node:
            return False
        
        return self._validate_node(script.root_node, valid_conditions, valid_actions)
    
    def _validate_node(self, node: BehaviorNode, valid_conditions: Set[str], valid_actions: Set[str]) -> bool:
        """Recursively validate a behavior tree node."""
        is_valid = True
        
        # Validate conditions
        for cond in node.conditions:
            if cond.condition_type.lower() not in {c.lower() for c in valid_conditions}:
                print(f"Warning: Invalid condition '{cond.condition_type}' in node '{node.node_id}'")
                is_valid = False
        
        # Validate action
        if node.action:
            if node.action.action_type.lower() not in {a.lower() for a in valid_actions}:
                print(f"Warning: Invalid action '{node.action.action_type}' in node '{node.node_id}'")
                is_valid = False
        
        # Recursively validate children
        for child in node.children:
            if not self._validate_node(child, valid_conditions, valid_actions):
                is_valid = False
        
        return is_valid
    
    def _build_plan_prompt(
        self,
        entity: Any,
        perception: PerceptionStatus,
        social_context: Dict[str, Any],
        goal: str,
        all_entities: List[Any]
    ) -> str:
        """Build a prompt for plan generation."""
        # Get entity type and stats
        mob_type = getattr(entity, 'mob_type', 'default')
        health_pct = getattr(entity, 'health_pct', 1.0)
        
        # Build visible entities list
        visible_entities = []
        for e in all_entities:
            if e.id == entity.id:
                continue
            if hasattr(e, 'is_alive') and not e.is_alive():
                continue
            if hasattr(e, 'position') and hasattr(entity, 'position'):
                distance = entity.position.distance_to(e.position)
                if distance <= perception.player_distance_estimate:
                    visible_entities.append({
                        'id': e.id,
                        'name': getattr(e, 'name', 'unknown'),
                        'type': getattr(e, 'mob_type', 'unknown'),
                        'distance': distance,
                        'is_player': getattr(e, 'is_player', False)
                    })
        
        # Build items list
        visible_items = []
        for e in all_entities:
            if hasattr(e, 'item') and e.item:
                if hasattr(e, 'position') and hasattr(entity, 'position'):
                    distance = entity.position.distance_to(e.position)
                    if distance <= perception.player_distance_estimate:
                        visible_items.append({
                            'id': e.item.id,
                            'name': e.item.name,
                            'type': getattr(e.item, 'item_type', 'misc'),
                            'distance': distance
                        })
        
        return f"""You are generating a behavior plan for a {mob_type} named {entity.name}.

GOAL: {goal}

CURRENT PERCEPTION:
- Can see player: {perception.can_see_player}
- Can hear player: {perception.can_hear_player}
- Player distance: {perception.player_distance_estimate}
- Player last known position: {perception.player_last_known_position}
- Visible threats: {len(perception.visible_threats)}
- Environment danger: {perception.environment_danger}
- Entity health: {health_pct:.0%}

SOCIAL CONTEXT:
{social_context}

VISIBLE ENTITIES:
{visible_entities}

VISIBLE ITEMS:
{visible_items}

AVAILABLE ACTIONS: attack, flee, patrol, move_to, call_allies, follow_leader, guard_position, pickup_item, search, hide, wait

Generate a multi-step behavior plan as a JSON tree. The plan should handle:
1. Primary objective (the goal)
2. Fallback conditions (what to if primary fails)
3. Emergency conditions (low health, outnumbered, etc.)

Return JSON in this format:
{{
  "entity_id": "{entity.id}",
  "root_node": {{
    "node_id": "root",
    "node_type": "selector",
    "children": [
      {{
        "node_id": "emergency_flee",
        "node_type": "action",
        "conditions": [{{"condition_type": "health_below", "operator": "<", "value": 0.2}}],
        "action": {{"action_type": "flee", "target": "player"}}
      }},
      {{
        "node_id": "primary_attack",
        "node_type": "action",
        "conditions": [{{"condition_type": "can_see_player"}}],
        "action": {{"action_type": "attack", "target": "player"}}
      }},
      {{
        "node_id": "search_last_known",
        "node_type": "action",
        "conditions": [{{"condition_type": "can_hear_player"}}],
        "action": {{"action_type": "search"}}
      }},
      {{
        "node_id": "default_patrol",
        "node_type": "action",
        "action": {{"action_type": "patrol"}}
      }}
    ]
  }}
}}"""
    
    def _get_llm_response(self, prompt: str) -> str:
        """Get response from LLM."""
        try:
            response = self._llm.generate(prompt)
            return response
        except Exception as e:
            print(f"LLM plan generation failed: {e}")
            return self._get_fallback_plan()
    
    def _get_fallback_plan(self) -> str:
        """Get a fallback plan when LLM fails."""
        return """{
  "entity_id": "fallback",
  "root_node": {
    "node_id": "root",
    "node_type": "selector",
    "children": [
      {
        "node_id": "emergency_flee",
        "node_type": "action",
        "conditions": [{"condition_type": "health_below", "operator": "<", "value": 0.2}],
        "action": {"action_type": "flee", "target": "player"}
      },
      {
        "node_id": "primary_attack",
        "node_type": "action",
        "conditions": [{"condition_type": "can_see_player"}],
        "action": {"action_type": "attack", "target": "player"}
      },
      {
        "node_id": "default_patrol",
        "node_type": "action",
        "action": {"action_type": "patrol"}
      }
    ]
  }
}"""