"""Tests for behavior script value objects."""

import pytest
from src.domain.value_objects.behavior_script import (
    NodeType,
    ConditionType,
    ActionType,
    BehaviorCondition,
    BehaviorAction,
    BehaviorNode,
    BehaviorScript,
    MOB_BEHAVIOR_CATALOG,
)


class TestNodeType:
    """Tests for NodeType enum."""

    def test_selector_value(self):
        assert NodeType.SELECTOR.value == "selector"

    def test_sequence_value(self):
        assert NodeType.SEQUENCE.value == "sequence"

    def test_condition_value(self):
        assert NodeType.CONDITION.value == "condition"

    def test_action_value(self):
        assert NodeType.ACTION.value == "action"

    def test_parallel_value(self):
        assert NodeType.PARALLEL.value == "parallel"


class TestConditionType:
    """Tests for ConditionType enum."""

    def test_can_see_player(self):
        assert ConditionType.CAN_SEE_PLAYER.value == "can_see_player"

    def test_health_below(self):
        assert ConditionType.HEALTH_BELOW.value == "health_below"

    def test_loyalty_above(self):
        assert ConditionType.LOYALTY_ABOVE.value == "loyalty_above"

    def test_has_item(self):
        assert ConditionType.HAS_ITEM.value == "has_item"


class TestActionType:
    """Tests for ActionType enum."""

    def test_attack_value(self):
        assert ActionType.ATTACK.value == "attack"

    def test_flee_value(self):
        assert ActionType.FLEE.value == "flee"

    def test_patrol_value(self):
        assert ActionType.PATROL.value == "patrol"

    def test_follow_leader_value(self):
        assert ActionType.FOLLOW_LEADER.value == "follow_leader"


class TestBehaviorCondition:
    """Tests for BehaviorCondition dataclass."""

    def test_default_values(self):
        condition = BehaviorCondition(condition_type="can_see_player")
        assert condition.condition_type == "can_see_player"
        assert condition.operator == "=="
        assert condition.value is True
        assert condition.parameters == {}

    def test_custom_operator(self):
        condition = BehaviorCondition(
            condition_type="health_below",
            operator="<",
            value=0.5
        )
        assert condition.operator == "<"
        assert condition.value == 0.5

    def test_with_parameters(self):
        condition = BehaviorCondition(
            condition_type="has_item",
            parameters={"item_id": "sword_001"}
        )
        assert condition.parameters == {"item_id": "sword_001"}


class TestBehaviorAction:
    """Tests for BehaviorAction dataclass."""

    def test_default_values(self):
        action = BehaviorAction(action_type="attack")
        assert action.action_type == "attack"
        assert action.target is None
        assert action.parameters == {}

    def test_with_target(self):
        action = BehaviorAction(
            action_type="attack",
            target="player"
        )
        assert action.target == "player"

    def test_with_parameters(self):
        action = BehaviorAction(
            action_type="use_item",
            target="self",
            parameters={"item_id": "potion_001"}
        )
        assert action.parameters == {"item_id": "potion_001"}


class TestBehaviorNode:
    """Tests for BehaviorNode dataclass."""

    def test_leaf_node_with_action(self):
        action = BehaviorAction(action_type="wait")
        node = BehaviorNode(
            node_id="wait_node",
            node_type="action",
            action=action
        )
        assert node.node_id == "wait_node"
        assert node.node_type == "action"
        assert node.action.action_type == "wait"
        assert node.children == []

    def test_composite_node_with_children(self):
        child1 = BehaviorNode(node_id="child1", node_type="condition")
        child2 = BehaviorNode(node_id="child2", node_type="action")
        node = BehaviorNode(
            node_id="selector",
            node_type="selector",
            children=[child1, child2],
            priority=10
        )
        assert len(node.children) == 2
        assert node.priority == 10

    def test_node_with_conditions(self):
        condition = BehaviorCondition(condition_type="can_see_player")
        node = BehaviorNode(
            node_id="conditional_action",
            node_type="condition",
            conditions=[condition]
        )
        assert len(node.conditions) == 1


class TestBehaviorScript:
    """Tests for BehaviorScript dataclass."""

    def test_basic_script(self):
        root = BehaviorNode(node_id="root", node_type="selector")
        script = BehaviorScript(
            entity_id="goblin_001",
            script_id="goblin_idle",
            root_node=root
        )
        assert script.entity_id == "goblin_001"
        assert script.script_id == "goblin_idle"
        assert script.version == 1
        assert script.created_at == 0.0

    def test_script_with_valid_types(self):
        root = BehaviorNode(node_id="root", node_type="selector")
        script = BehaviorScript(
            entity_id="wolf_001",
            script_id="wolf_hunt",
            root_node=root,
            valid_conditions=["can_see_player", "health_below"],
            valid_actions=["attack", "flee"]
        )
        assert "can_see_player" in script.valid_conditions
        assert "attack" in script.valid_actions


class TestMobBehaviorCatalog:
    """Tests for MOB_BEHAVIOR_CATALOG."""

    def test_goblin_catalog(self):
        assert "goblin" in MOB_BEHAVIOR_CATALOG
        goblin = MOB_BEHAVIOR_CATALOG["goblin"]
        assert "can_see_player" in goblin["conditions"]
        assert "attack" in goblin["actions"]

    def test_goblin_king_catalog(self):
        assert "goblin_king" in MOB_BEHAVIOR_CATALOG
        king = MOB_BEHAVIOR_CATALOG["goblin_king"]
        assert "ally_health_below" in king["conditions"]
        assert "promote_minion" in king["actions"]

    def test_wolf_catalog(self):
        assert "wolf" in MOB_BEHAVIOR_CATALOG
        wolf = MOB_BEHAVIOR_CATALOG["wolf"]
        assert "can_smell_player" in wolf["conditions"]

    def test_spider_catalog(self):
        assert "spider" in MOB_BEHAVIOR_CATALOG
        spider = MOB_BEHAVIOR_CATALOG["spider"]
        assert "environment_danger_above" in spider["conditions"]
        assert "hide" in spider["actions"]

    def test_mercenary_catalog(self):
        assert "mercenary" in MOB_BEHAVIOR_CATALOG
        merc = MOB_BEHAVIOR_CATALOG["mercenary"]
        assert "trade" in merc["actions"]

    def test_undead_catalog(self):
        assert "undead" in MOB_BEHAVIOR_CATALOG
        undead = MOB_BEHAVIOR_CATALOG["undead"]
        assert "attack" in undead["actions"]

    def test_default_catalog(self):
        assert "default" in MOB_BEHAVIOR_CATALOG
        default = MOB_BEHAVIOR_CATALOG["default"]
        assert len(default["conditions"]) == 4
        assert len(default["actions"]) == 4