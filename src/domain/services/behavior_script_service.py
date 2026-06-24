"""Behavior script service for evaluating behavior trees."""

from typing import Optional, Dict, Any, List, Tuple
import time
import uuid

from src.domain.value_objects.behavior_script import (
    BehaviorScript, BehaviorNode, BehaviorCondition, BehaviorAction,
    ConditionType, ActionType, NodeType, MOB_BEHAVIOR_CATALOG
)
from src.domain.value_objects.perception import PerceptionStatus
from src.domain.value_objects.social import LoyaltyState


__all__ = ["BehaviorScriptService"]


class BehaviorScriptService:
    """
    Service for evaluating BehaviorScripts against PerceptionStatus to determine actions.
    
    This service walks behavior trees and evaluates conditions against
    perception and entity state.
    """
    
    def __init__(self, action_dispatcher: Optional[Any] = None):
        """
        Initialize the BehaviorScriptService.
        
        Args:
            action_dispatcher: Optional callback for executing actions
        """
        self._action_dispatcher = action_dispatcher
    
    def evaluate_script(
        self,
        script: BehaviorScript,
        perception: PerceptionStatus,
        entity_state: Dict[str, Any]
    ) -> Optional[BehaviorAction]:
        """
        Evaluate a behavior script and return the action to take.
        
        Args:
            script: The behavior script to evaluate
            perception: Current perception status
            entity_state: Current entity state dict
            
        Returns:
            Optional[BehaviorAction]: The action to execute, or None
        """
        if not script.root_node:
            return None
        
        # For multi-step plans, update plan memory with current perception
        if script.is_plan:
            self._update_plan_memory(script, perception, entity_state)
        
        return self._evaluate_node(script.root_node, perception, entity_state, script.plan_memory)
    
    def _evaluate_node(
        self,
        node: BehaviorNode,
        perception: PerceptionStatus,
        entity_state: Dict[str, Any]
    ) -> Optional[BehaviorAction]:
        """
        Recursively evaluate a behavior tree node.
        
        Args:
            node: The node to evaluate
            perception: Current perception status
            entity_state: Current entity state dict
            
        Returns:
            Optional[BehaviorAction]: The action to execute, or None
        """
        # Handle both string and NodeType enum
        if isinstance(node.node_type, NodeType):
            node_type = node.node_type.value
        else:
            node_type = node.node_type.lower()
        
        if node_type == NodeType.ACTION.value:
            # Check conditions for action node (empty conditions = always pass)
            if not node.conditions or self._evaluate_conditions(node.conditions, perception, entity_state):
                return node.action
            return None
        
        elif node_type == NodeType.CONDITION.value:
            # Condition nodes don't produce actions, but check if conditions pass
            if self._evaluate_conditions(node.conditions, perception, entity_state):
                # If this is a leaf condition, return None
                return None
            return None
        
        elif node_type == NodeType.SELECTOR.value:
            # Try children in order until one succeeds
            for child in node.children:
                result = self._evaluate_node(child, perception, entity_state)
                if result is not None:
                    return result
            return None
        
        elif node_type == NodeType.SEQUENCE.value:
            # Run all children in order, fail if any fails
            for child in node.children:
                result = self._evaluate_node(child, perception, entity_state)
                if result is None:
                    # Action failed, sequence fails
                    return None
            return None
        
        elif node_type == NodeType.PARALLEL.value:
            # Run all children, return first action
            for child in node.children:
                result = self._evaluate_node(child, perception, entity_state)
                if result is not None:
                    return result
            return None
        
        return None
    
    def _evaluate_conditions(
        self,
        conditions: List[BehaviorCondition],
        perception: PerceptionStatus,
        entity_state: Dict[str, Any],
        plan_memory: Dict[str, Any] = None
    ) -> bool:
        """
        Evaluate a list of conditions.
        
        Args:
            conditions: List of conditions to evaluate
            perception: Current perception status
            entity_state: Current entity state dict
            plan_memory: Plan memory for multi-step plans
            
        Returns:
            bool: True if all conditions pass
        """
        if plan_memory is None:
            plan_memory = {}
        
        for condition in conditions:
            if not self._evaluate_condition(condition, perception, entity_state, plan_memory):
                return False
        return True
    
    def _evaluate_condition(
        self,
        condition: BehaviorCondition,
        perception: PerceptionStatus,
        entity_state: Dict[str, Any],
        plan_memory: Dict[str, Any] = None
    ) -> bool:
        """
        Evaluate a single condition against perception and state.
        
        Args:
            condition: The condition to evaluate
            perception: Current perception status
            entity_state: Current entity state dict
            plan_memory: Plan memory for multi-step plans
            
        Returns:
            bool: True if condition passes
        """
        if plan_memory is None:
            plan_memory = {}
        
        condition_type = condition.condition_type.lower()
        value = self._get_condition_value(condition_type, perception, entity_state, condition, plan_memory)
        
        # Apply operator
        operator = condition.operator
        expected = condition.value
        
        result = False
        if operator == "==":
            result = value == expected
        elif operator == "!=":
            result = value != expected
        elif operator == ">":
            result = value > expected
        elif operator == ">=":
            result = value >= expected
        elif operator == "<":
            result = value < expected
        elif operator == "<=":
            result = value <= expected
        
        # Log condition evaluation failure
        if not result:
            print(f"[BehaviorScriptService] Condition '{condition_type}' failed: value={value}, operator={operator}, expected={expected}")
        
        return result
    
    def _update_plan_memory(
        self,
        script: BehaviorScript,
        perception: PerceptionStatus,
        entity_state: Dict[str, Any]
    ) -> None:
        """
        Update plan memory for multi-step plans.
        
        Stores relevant state information for tracking progress across turns.
        
        Args:
            script: The behavior script (plan) being executed
            perception: Current perception status
            entity_state: Current entity state dict
        """
        memory = script.plan_memory
        
        # Track current step
        if "current_step" not in memory:
            memory["current_step"] = 0
        
        # Track last search position
        if perception.player_last_known_position:
            memory["last_search_pos"] = perception.player_last_known_position
        
        # Track attack count
        if "attack_count" not in memory:
            memory["attack_count"] = 0
        if entity_state.get("in_combat", False):
            memory["attack_count"] += 1
        
        # Track health for emergency detection
        memory["current_health"] = entity_state.get("health_pct", 1.0)
        
        # Track visible threats count
        memory["visible_threats"] = len(perception.visible_threats)
        
        # Track if player was seen/heard
        memory["player_seen"] = perception.can_see_player
        memory["player_heard"] = perception.can_hear_player
        
        # Update last known player position
        if perception.can_see_player and perception.player_last_known_position:
            memory["last_known_player_pos"] = perception.player_last_known_position
    
    def _get_condition_value(
        self,
        condition_type: str,
        perception: PerceptionStatus,
        entity_state: Dict[str, Any],
        condition: BehaviorCondition,
        plan_memory: Dict[str, Any] = None
    ) -> Any:
        """
        Extract the relevant value from perception/state for a condition.
        
        Args:
            condition_type: Type of condition
            perception: Current perception status
            entity_state: Current entity state dict
            condition: The condition object (for accessing value/parameters)
            plan_memory: Plan memory for multi-step plans
            
        Returns:
            Any: The condition value
        """
        if plan_memory is None:
            plan_memory = {}
        
        if condition_type == "can_see_player":
            return perception.can_see_player
        
        elif condition_type == "can_hear_player":
            return perception.can_hear_player
        
        elif condition_type == "can_smell_player":
            return perception.can_smell_player
        
        elif condition_type == "health_below":
            return entity_state.get("health_pct", 1.0)
        
        elif condition_type == "health_above":
            return entity_state.get("health_pct", 1.0)
        
        elif condition_type == "loyalty_above":
            loyalty = entity_state.get("loyalty", LoyaltyState("unknown", "unknown"))
            if isinstance(loyalty, LoyaltyState):
                return loyalty.loyalty_score
            return 0.0
        
        elif condition_type == "loyalty_below":
            loyalty = entity_state.get("loyalty", LoyaltyState("unknown", "unknown"))
            if isinstance(loyalty, LoyaltyState):
                return loyalty.loyalty_score
            return 1.0
        
        elif condition_type == "has_item":
            has_items = entity_state.get("has_items", [])
            item_id = condition.parameters.get("item_id") if condition.parameters else None
            if item_id:
                return item_id in has_items
            return len(has_items) > 0
        
        elif condition_type == "ally_nearby":
            ally_count = entity_state.get("ally_count", 0)
            return ally_count > 0
        
        elif condition_type == "ally_health_below":
            ally_health = entity_state.get("ally_health_status", "healthy")
            return ally_health in ["wounded", "critical"]
        
        elif condition_type == "player_distance_below":
            return perception.player_distance_estimate
        
        elif condition_type == "in_combat":
            return entity_state.get("in_combat", False)
        
        elif condition_type == "environment_danger_above":
            return perception.environment_danger
        
        elif condition_type == "has_orders":
            orders = entity_state.get("orders", [])
            return len(orders) > 0
        
        elif condition_type == "is_leader":
            return entity_state.get("is_leader", False)
        
        elif condition_type == "is_guard":
            return entity_state.get("is_guard", False)
        
        elif condition_type == "wealth_above":
            return entity_state.get("wealth", 0)
        
        elif condition_type == "custom_flag":
            flag_name = condition.parameters.get("flag") if condition.parameters else None
            if flag_name:
                return perception.custom_flags.get(flag_name, False)
            return False
        
        # Check plan_memory for tracked values
        elif condition_type == "attack_count_above":
            return plan_memory.get("attack_count", 0)
        
        elif condition_type == "visible_threats_above":
            return plan_memory.get("visible_threats", 0)
        
        return False
    
    def validate_script(
        self,
        script: BehaviorScript,
        mob_type: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate that a script only uses conditions/actions from the mob's catalog.
        
        Args:
            script: The script to validate
            mob_type: The mob type for catalog lookup
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, list of errors)
        """
        errors = []
        
        # Get the catalog for this mob type
        catalog = MOB_BEHAVIOR_CATALOG.get(mob_type, MOB_BEHAVIOR_CATALOG.get("default", {}))
        valid_conditions = set(catalog.get("conditions", []))
        valid_actions = set(catalog.get("actions", []))
        
        # Collect all conditions and actions from the script
        all_conditions, all_actions = self._collect_node_conditions_actions(script.root_node)
        
        # Validate conditions
        for cond in all_conditions:
            if cond not in valid_conditions:
                errors.append(f"Invalid condition '{cond}' for mob type '{mob_type}'")
        
        # Validate actions
        for action in all_actions:
            if action not in valid_actions:
                errors.append(f"Invalid action '{action}' for mob type '{mob_type}'")
        
        return len(errors) == 0, errors
    
    def _collect_node_conditions_actions(
        self,
        node: BehaviorNode
    ) -> Tuple[List[str], List[str]]:
        """
        Collect all condition types and action types from a behavior tree.
        
        Args:
            node: The root node to collect from
            
        Returns:
            Tuple[List[str], List[str]]: (conditions, actions)
        """
        conditions = []
        actions = []
        
        if node.conditions:
            conditions.extend([c.condition_type for c in node.conditions])
        
        if node.action:
            actions.append(node.action.action_type)
        
        if node.children:
            for child in node.children:
                child_conds, child_acts = self._collect_node_conditions_actions(child)
                conditions.extend(child_conds)
                actions.extend(child_acts)
        
        return conditions, actions
    
    def create_default_script(
        self,
        mob_type: str,
        entity_id: str
    ) -> BehaviorScript:
        """
        Create a basic default behavior script for a mob type.
        
        Args:
            mob_type: The mob type
            entity_id: The entity ID
            
        Returns:
            BehaviorScript: A default behavior script
        """
        # Create a simple selector with basic actions
        root = BehaviorNode(
            node_id="root",
            node_type=NodeType.SELECTOR,
            children=[
                BehaviorNode(
                    node_id="combat_node",
                    node_type=NodeType.ACTION,
                    conditions=[
                        BehaviorCondition(condition_type="can_see_player"),
                        BehaviorCondition(condition_type="health_above", value=0.3)
                    ],
                    action=BehaviorAction(action_type="attack", target="player")
                ),
                BehaviorNode(
                    node_id="flee_node",
                    node_type=NodeType.ACTION,
                    conditions=[
                        BehaviorCondition(condition_type="health_below", value=0.3)
                    ],
                    action=BehaviorAction(action_type="flee", target="player")
                ),
                BehaviorNode(
                    node_id="patrol_node",
                    node_type=NodeType.ACTION,
                    action=BehaviorAction(action_type="patrol")
                )
            ]
        )
        
        return BehaviorScript(
            entity_id=entity_id,
            script_id=f"{mob_type}_default_{uuid.uuid4().hex[:8]}",
            root_node=root,
            valid_conditions=["can_see_player", "health_below", "health_above"],
            valid_actions=["attack", "flee", "patrol"],
            created_at=time.time()
        )
    
    def parse_script_from_json(
        self,
        json_data: dict
    ) -> BehaviorScript:
        """
        Parse LLM-generated JSON into a BehaviorScript.
        
        Args:
            json_data: Dictionary containing script data
            
        Returns:
            BehaviorScript: The parsed behavior script
        """
        entity_id = json_data.get("entity_id", "unknown")
        script_id = json_data.get("script_id", f"parsed_{uuid.uuid4().hex[:8]}")
        
        # Parse root node
        root_data = json_data.get("root_node", {})
        root_node = self._parse_node_from_json(root_data)
        
        return BehaviorScript(
            entity_id=entity_id,
            script_id=script_id,
            root_node=root_node,
            valid_conditions=json_data.get("valid_conditions", []),
            valid_actions=json_data.get("valid_actions", []),
            created_at=json_data.get("created_at", time.time()),
            version=json_data.get("version", 1)
        )
    
    def _parse_node_from_json(self, node_data: dict) -> BehaviorNode:
        """
        Parse a node from JSON data.
        
        Args:
            node_data: Dictionary containing node data
            
        Returns:
            BehaviorNode: The parsed node
        """
        # Parse conditions
        conditions = []
        for c in node_data.get("conditions", []):
            conditions.append(BehaviorCondition(
                condition_type=c.get("condition_type", ""),
                operator=c.get("operator", "=="),
                value=c.get("value", True),
                parameters=c.get("parameters", {})
            ))
        
        # Parse action
        action = None
        if "action" in node_data:
            action_data = node_data["action"]
            action = BehaviorAction(
                action_type=action_data.get("action_type", ""),
                target=action_data.get("target"),
                parameters=action_data.get("parameters", {})
            )
        
        # Parse children
        children = []
        for child_data in node_data.get("children", []):
            children.append(self._parse_node_from_json(child_data))
        
        return BehaviorNode(
            node_id=node_data.get("node_id", f"node_{uuid.uuid4().hex[:8]}"),
            node_type=node_data.get("node_type", NodeType.ACTION),
            priority=node_data.get("priority", 0),
            conditions=conditions,
            action=action,
            children=children,
            description=node_data.get("description", "")
        )