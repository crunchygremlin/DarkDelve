"""Swarm Template Service for group behavior templates by intelligence tier."""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from src.domain.value_objects.behavior_script import BehaviorScript, BehaviorNode, BehaviorCondition, BehaviorAction, NodeType


INTELLIGENCE_TIERS = {1: "bestial", 2: "simple", 3: "tactical", 4: "cunning", 5: "brilliant"}


@dataclass
class SwarmTemplate:
    """A swarm behavior template."""
    template_id: str
    tier: int
    description: str
    root_node: BehaviorNode


class SwarmTemplateService:
    """Service for managing swarm behavior templates by intelligence tier."""

    def __init__(self):
        self._templates: Dict[int, List[SwarmTemplate]] = self._build_default_templates()

    def _build_default_templates(self) -> Dict[int, List[SwarmTemplate]]:
        """Build default templates for each intelligence tier."""
        templates = {}
        
        # Tier 1: bestial - simple surround behavior
        templates[1] = [SwarmTemplate(
            template_id="surround_player",
            tier=1,
            description="Surround and attack player",
            root_node=BehaviorNode(
                node_id="root",
                node_type=NodeType.SELECTOR,
                children=[
                    BehaviorNode(
                        node_id="attack_check",
                        node_type=NodeType.ACTION,
                        conditions=[BehaviorCondition(condition_type="can_see_player")],
                        action=BehaviorAction(action_type="attack", target="player")
                    ),
                    BehaviorNode(
                        node_id="patrol",
                        node_type=NodeType.ACTION,
                        action=BehaviorAction(action_type="patrol")
                    )
                ]
            )
        )]
        
        # Tier 3: tactical - flee to pack behavior
        templates[3] = [SwarmTemplate(
            template_id="flee_to_pack",
            tier=3,
            description="Flee when low health, regroup with pack",
            root_node=BehaviorNode(
                node_id="root",
                node_type=NodeType.SELECTOR,
                children=[
                    BehaviorNode(
                        node_id="flee_check",
                        node_type=NodeType.ACTION,
                        conditions=[BehaviorCondition(condition_type="health_below", value=0.3)],
                        action=BehaviorAction(action_type="flee", target="player")
                    ),
                    BehaviorNode(
                        node_id="follow_leader",
                        node_type=NodeType.ACTION,
                        action=BehaviorAction(action_type="follow_leader")
                    ),
                    BehaviorNode(
                        node_id="patrol",
                        node_type=NodeType.ACTION,
                        action=BehaviorAction(action_type="patrol")
                    )
                ]
            )
        )]
        
        # Tier 4: cunning - flee to stronger mob
        templates[4] = [SwarmTemplate(
            template_id="flee_to_stronger_mob",
            tier=4,
            description="Flee to stronger ally when weak",
            root_node=BehaviorNode(
                node_id="root",
                node_type=NodeType.SELECTOR,
                children=[
                    BehaviorNode(
                        node_id="flee_check",
                        node_type=NodeType.ACTION,
                        conditions=[BehaviorCondition(condition_type="health_below", value=0.5)],
                        action=BehaviorAction(action_type="flee", target="player")
                    ),
                    BehaviorNode(
                        node_id="move_to_strongest",
                        node_type=NodeType.ACTION,
                        action=BehaviorAction(action_type="move_to", target="strongest_ally")
                    ),
                    BehaviorNode(
                        node_id="patrol",
                        node_type=NodeType.ACTION,
                        action=BehaviorAction(action_type="patrol")
                    )
                ]
            )
        )]
        
        # Tier 5: brilliant - coordinate ambush
        templates[5] = [SwarmTemplate(
            template_id="coordinate_ambush",
            tier=5,
            description="Call allies and coordinate ambush attack",
            root_node=BehaviorNode(
                node_id="root",
                node_type=NodeType.SELECTOR,
                children=[
                    BehaviorNode(
                        node_id="call_allies",
                        node_type=NodeType.ACTION,
                        action=BehaviorAction(action_type="call_allies")
                    ),
                    BehaviorNode(
                        node_id="attack",
                        node_type=NodeType.ACTION,
                        conditions=[BehaviorCondition(condition_type="can_see_player")],
                        action=BehaviorAction(action_type="attack", target="player")
                    ),
                    BehaviorNode(
                        node_id="follow_leader",
                        node_type=NodeType.ACTION,
                        action=BehaviorAction(action_type="follow_leader")
                    )
                ]
            )
        )]
        
        # Ensure all tiers have at least one template
        for tier in range(1, 6):
            if tier not in templates:
                templates[tier] = templates[1]  # fallback to tier 1
        
        return templates

    def select_template(self, mob_type: str, intelligence_tier: int) -> SwarmTemplate:
        """Select a template for the given mob type and intelligence tier.
        
        Args:
            mob_type: The mob type
            intelligence_tier: Intelligence tier (1-5)
            
        Returns:
            A SwarmTemplate
        """
        tier = max(1, min(5, intelligence_tier))
        pool = self._templates.get(tier, self._templates[1])
        return pool[0]

    def build_script(self, template: SwarmTemplate, entity_id: str) -> BehaviorScript:
        """Build a BehaviorScript from a template.
        
        Deep-copies the template root node and tags with entity_id.
        
        Args:
            template: The template to build from
            entity_id: The entity ID to assign
            
        Returns:
            A BehaviorScript
        """
        # Deep copy the root node
        root_copy = self._deep_copy_node(template.root_node)
        
        return BehaviorScript(
            entity_id=entity_id,
            script_id=f"{template.template_id}_{entity_id}",
            root_node=root_copy,
            valid_conditions=["can_see_player", "can_hear_player", "health_below"],
            valid_actions=["attack", "flee", "patrol", "follow_leader", "call_allies", "move_to"],
            created_at=time.time(),
            is_plan=True,
            plan_name=template.template_id
        )

    def _deep_copy_node(self, node: BehaviorNode) -> BehaviorNode:
        """Deep copy a BehaviorNode."""
        # Recursively copy children
        children = [self._deep_copy_node(c) for c in node.children]
        
        # Copy conditions
        conditions = [
            BehaviorCondition(
                condition_type=c.condition_type,
                operator=c.operator,
                value=c.value,
                parameters=c.parameters.copy()
            )
            for c in node.conditions
        ]
        
        # Copy action
        action = None
        if node.action:
            action = BehaviorAction(
                action_type=node.action.action_type,
                target=node.action.target,
                target_item_id=node.action.target_item_id,
                parameters=node.action.parameters.copy()
            )
        
        return BehaviorNode(
            node_id=node.node_id,
            node_type=node.node_type,
            priority=node.priority,
            conditions=conditions,
            action=action,
            children=children,
            description=node.description
        )

    def issue_leader_command(
        self,
        leader_id: str,
        command: str,
        subordinate_ids: List[str],
        event_bus
    ) -> None:
        """Issue a leader command via event bus.
        
        Args:
            leader_id: The leader entity ID
            command: The command string
            subordinate_ids: List of subordinate entity IDs
            event_bus: The event bus to publish to
        """
        if event_bus:
            event_bus.publish("leader_command", {
                "leader_id": leader_id,
                "command": command,
                "subordinate_ids": subordinate_ids
            })