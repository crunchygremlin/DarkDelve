"""Behavior script value objects for the Entity AI system."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

__all__ = [
    "NodeType",
    "ConditionType",
    "ActionType",
    "BehaviorCondition",
    "BehaviorAction",
    "BehaviorNode",
    "BehaviorScript",
    "MOB_BEHAVIOR_CATALOG",
]


class NodeType(Enum):
    """Types of behavior tree nodes."""
    SELECTOR = "selector"      # tries children in order until one succeeds
    SEQUENCE = "sequence"     # runs all children in order, fails if any fails
    CONDITION = "condition"   # checks a condition, no action
    ACTION = "action"         # performs an action
    PARALLEL = "parallel"     # runs all children simultaneously


class ConditionType(Enum):
    """Types of conditions that can be evaluated in behavior trees."""
    CAN_SEE_PLAYER = "can_see_player"
    CAN_HEAR_PLAYER = "can_hear_player"
    HEALTH_BELOW = "health_below"
    HEALTH_ABOVE = "health_above"
    HAS_ITEM = "has_item"
    ALLY_NEARBY = "ally_nearby"
    ALLY_HEALTH_BELOW = "ally_health_below"
    PLAYER_DISTANCE_BELOW = "player_distance_below"
    LOYALTY_ABOVE = "loyalty_above"
    LOYALTY_BELOW = "loyalty_below"
    IN_COMBAT = "in_combat"
    ENVIRONMENT_DANGER_ABOVE = "environment_danger_above"
    HAS_ORDERS = "has_orders"
    IS_LEADER = "is_leader"
    IS_GUARD = "is_guard"
    WEALTH_ABOVE = "wealth_above"
    CUSTOM_FLAG = "custom_flag"


class ActionType(Enum):
    """Types of actions that can be executed in behavior trees."""
    ATTACK = "attack"
    FLEE = "flee"
    PATROL = "patrol"
    USE_ITEM = "use_item"
    CALL_ALLIES = "call_allies"
    TRADE = "trade"
    FOLLOW_LEADER = "follow_leader"
    GUARD_POSITION = "guard_position"
    PICKUP_ITEM = "pickup_item"
    GIFT_ITEM = "gift_item"
    PROMOTE_MINION = "promote_minion"
    GIVE_ORDERS = "give_orders"
    WAIT = "wait"
    SEARCH = "search"
    HIDE = "hide"
    BLOCK = "block"
    HEAL_ALLY = "heal_ally"


@dataclass
class BehaviorCondition:
    """A condition node in a behavior tree."""
    condition_type: str  # ConditionType value
    operator: str = "=="  # "==", ">", "<", "!=", ">=", "<="
    value: Any = True
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BehaviorAction:
    """An action node in a behavior tree."""
    action_type: str  # ActionType value
    target: Optional[str] = None  # "player", "nearest_enemy", "leader", entity_id
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BehaviorNode:
    """A node in a behavior tree."""
    node_id: str
    node_type: str  # NodeType value
    priority: int = 0
    conditions: List[BehaviorCondition] = field(default_factory=list)
    action: Optional[BehaviorAction] = None
    children: List['BehaviorNode'] = field(default_factory=list)
    description: str = ""


@dataclass
class BehaviorScript:
    """A complete behavior script for an entity."""
    entity_id: str
    script_id: str
    root_node: BehaviorNode
    valid_conditions: List[str] = field(default_factory=list)
    valid_actions: List[str] = field(default_factory=list)
    created_at: float = 0.0
    version: int = 1


# Catalog of conditions/actions per mob type
MOB_BEHAVIOR_CATALOG: Dict[str, Dict[str, List[str]]] = {
    "goblin": {
        "conditions": [
            "can_see_player", "can_hear_player", "health_below", "ally_nearby",
            "player_distance_below", "loyalty_above", "loyalty_below", "in_combat",
            "has_orders", "is_leader", "is_guard", "wealth_above"
        ],
        "actions": [
            "attack", "flee", "patrol", "call_allies", "follow_leader",
            "guard_position", "pickup_item", "gift_item", "give_orders", "wait", "search"
        ]
    },
    "goblin_king": {
        "conditions": [
            "can_see_player", "can_hear_player", "health_below", "ally_nearby",
            "player_distance_below", "loyalty_above", "loyalty_below", "in_combat",
            "has_orders", "is_leader", "is_guard", "wealth_above", "ally_health_below"
        ],
        "actions": [
            "attack", "flee", "patrol", "call_allies", "follow_leader",
            "guard_position", "pickup_item", "gift_item", "promote_minion",
            "give_orders", "wait", "search", "trade"
        ]
    },
    "wolf": {
        "conditions": [
            "can_see_player", "can_hear_player", "can_smell_player", "health_below",
            "ally_nearby", "player_distance_below", "in_combat", "is_leader"
        ],
        "actions": [
            "attack", "flee", "patrol", "call_allies", "follow_leader", "search", "wait"
        ]
    },
    "spider": {
        "conditions": [
            "can_see_player", "can_hear_player", "health_below", "ally_nearby",
            "player_distance_below", "in_combat", "environment_danger_above"
        ],
        "actions": [
            "attack", "flee", "patrol", "wait", "hide", "search"
        ]
    },
    "mercenary": {
        "conditions": [
            "can_see_player", "can_hear_player", "health_below", "ally_nearby",
            "player_distance_below", "loyalty_above", "loyalty_below", "in_combat",
            "has_orders", "is_leader", "wealth_above"
        ],
        "actions": [
            "attack", "flee", "patrol", "call_allies", "follow_leader",
            "guard_position", "trade", "wait", "search"
        ]
    },
    "undead": {
        "conditions": [
            "can_see_player", "can_hear_player", "health_below", "ally_nearby",
            "player_distance_below", "in_combat", "has_orders", "is_leader"
        ],
        "actions": [
            "attack", "patrol", "follow_leader", "guard_position", "wait", "search"
        ]
    },
    "default": {
        "conditions": ["can_see_player", "can_hear_player", "health_below", "in_combat"],
        "actions": ["attack", "flee", "patrol", "wait"]
    }
}