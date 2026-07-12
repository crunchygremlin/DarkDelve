"""Entity AI Orchestrator for coordinating the AI pipeline each game tick."""

from typing import Dict, List, Optional, Any
from src.domain.services.perception_service import PerceptionService
from src.domain.services.behavior_script_service import BehaviorScriptService
from src.domain.services.social_service import SocialService
from src.domain.services.player_profile_service import PlayerProfileService
from src.domain.value_objects.llm_logging import LLMLogger
from src.domain.services.swarm_template_service import SwarmTemplateService

__all__ = ["EntityAIOrchestrator"]


class EntityAIOrchestrator:
    """Orchestrates the full AI pipeline each game tick."""

    def __init__(
        self,
        perception_service: PerceptionService,
        behavior_service: BehaviorScriptService,
        social_service: SocialService,
        player_profile_service: PlayerProfileService,
        llm_logger: LLMLogger,
        event_bus=None,
        swarm_template_service=None,
    ):
        self.perception_service = perception_service
        self.behavior_service = behavior_service
        self.social_service = social_service
        self.player_profile_service = player_profile_service
        self.llm_logger = llm_logger
        self.event_bus = event_bus
        self._swarm_template_service = swarm_template_service or SwarmTemplateService()
        self._tick = 0

    def tick(self, entities, player, game_map, items):
        """Main AI tick — called each game frame."""
        self._tick += 1

        # 1. Update perception for all entities with perception components
        self._update_perception(entities, player, game_map, items)

        # 2. Assign swarm templates to groups with leaders
        self._assign_swarm_templates(entities)

        # 3. Evaluate behavior scripts
        actions = self._evaluate_behaviors(entities)

        # 4. Check for desertions/betrayals
        self._check_social_events(entities)

        return actions

    def _assign_swarm_templates(self, entities):
        """Assign swarm templates to groups with leaders."""
        for entity in entities:
            social_comp = entity.get_component("social")
            behavior_comp = entity.get_component("behavior")
            
            if not social_comp or not behavior_comp:
                continue
            
            # If this entity is a leader and has no script, assign a template
            if social_comp.is_leader and behavior_comp.current_script is None:
                template = self._swarm_template_service.select_template(
                    mob_type=getattr(entity, 'mob_type', 'default'),
                    intelligence_tier=entity.intel_tier
                )
                script = self._swarm_template_service.build_script(template, entity.id)
                behavior_comp.set_script(script)
                
                # Issue leader command if player detected
                if self.event_bus:
                    self._swarm_template_service.issue_leader_command(
                        leader_id=entity.id,
                        command="guard",
                        subordinate_ids=social_comp.subordinate_ids,
                        event_bus=self.event_bus
                    )

    def _update_perception(self, entities, player, game_map, items):
        """Update perception for all entities with perception components."""
        for entity in entities:
            comp = entity.get_component("perception")
            if comp and comp.modifiers:
                status = self.perception_service.compute_perception(
                    entity, entities, items, game_map
                )
                comp.update_status(status, self._tick)

    def _evaluate_behaviors(self, entities) -> List[Dict[str, Any]]:
        """Evaluate behavior scripts for all entities."""
        actions = []
        for entity in entities:
            behavior_comp = entity.get_component("behavior")
            perception_comp = entity.get_component("perception")
            social_comp = entity.get_component("social")

            if not behavior_comp or not behavior_comp.current_script:
                continue
            if not behavior_comp.should_evaluate(self._tick):
                continue

            perception = perception_comp.current_status if perception_comp else None
            if not perception:
                continue

            entity_state = self._build_entity_state(entity, social_comp)
            action = self.behavior_service.evaluate_script(
                behavior_comp.current_script, perception, entity_state
            )
            behavior_comp.record_evaluation(self._tick, action)
            if action:
                actions.append({"entity": entity, "action": action})

        return actions

    def _build_entity_state(self, entity, social_comp) -> Dict[str, Any]:
        """Build entity state dict for behavior evaluation."""
        state = {
            "health_pct": getattr(entity, 'health_pct', 1.0),
            "in_combat": getattr(entity, 'in_combat', False),
            "ally_count": 0,
            "enemy_count": 0,
            "is_leader": False,
            "is_guard": False,
            "wealth": 0.0,
            "orders": [],
            "nearby_ally_health": "unknown",
        }
        if social_comp:
            state["is_leader"] = social_comp.is_leader
            state["is_guard"] = social_comp.role == "guard"
            state["wealth"] = social_comp.personal_wealth
            if social_comp.loyalty:
                state["loyalty_score"] = social_comp.loyalty.loyalty_score
        return state

    def _check_social_events(self, entities):
        """Check for desertion/betrayal events."""
        for entity in entities:
            social_comp = entity.get_component("social")
            if social_comp and social_comp.loyalty:
                if self.social_service.check_desertion(social_comp.loyalty.minion_id):
                    self._handle_desertion(entity)
                if self.social_service.check_betrayal(social_comp.loyalty.minion_id):
                    self._handle_betrayal(entity)

    def _handle_desertion(self, entity):
        """Handle a minion deserting."""
        if self.event_bus:
            self.event_bus.publish("minion_deserted", {"entity_id": entity.id})

    def _handle_betrayal(self, entity):
        """Handle a minion betraying."""
        if self.event_bus:
            self.event_bus.publish("minion_betrayed", {"entity_id": entity.id})

    @property
    def current_tick(self) -> int:
        """Return the current tick number."""
        return self._tick