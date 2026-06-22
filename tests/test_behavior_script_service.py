"""Tests for behavior script service."""

import pytest
from unittest.mock import MagicMock
import time

from src.domain.services.behavior_script_service import BehaviorScriptService
from src.domain.value_objects.behavior_script import (
    BehaviorScript, BehaviorNode, BehaviorCondition, BehaviorAction,
    NodeType, ConditionType, ActionType, MOB_BEHAVIOR_CATALOG
)
from src.domain.value_objects.perception import PerceptionStatus


class TestBehaviorScriptService:
    """Tests for BehaviorScriptService class."""
    
    def test_init(self):
        """Test BehaviorScriptService initialization."""
        service = BehaviorScriptService()
        assert service._action_dispatcher is None
        
        dispatcher = MagicMock()
        service = BehaviorScriptService(dispatcher)
        assert service._action_dispatcher == dispatcher
    
    def test_evaluate_script_with_action_node(self):
        """Test evaluating a script with an action node."""
        service = BehaviorScriptService()
        
        action = BehaviorAction(action_type="wait")
        node = BehaviorNode(
            node_id="wait_node",
            node_type=NodeType.ACTION,
            action=action
        )
        script = BehaviorScript(
            entity_id="test_entity",
            script_id="test_script",
            root_node=node
        )
        
        perception = PerceptionStatus(entity_id="test_entity")
        entity_state = {}
        
        result = service.evaluate_script(script, perception, entity_state)
        
        assert result is not None
        assert result.action_type == "wait"
    
    def test_evaluate_script_with_selector(self):
        """Test evaluating a script with a selector node."""
        service = BehaviorScriptService()
        
        # First child fails condition (can_see_player=True but perception has False), second succeeds
        action1 = BehaviorAction(action_type="attack")
        node1 = BehaviorNode(
            node_id="node1",
            node_type=NodeType.ACTION,
            conditions=[BehaviorCondition(condition_type="can_see_player", value=True)],
            action=action1
        )
        
        action2 = BehaviorAction(action_type="patrol")
        node2 = BehaviorNode(
            node_id="node2",
            node_type=NodeType.ACTION,
            action=action2
        )
        
        root = BehaviorNode(
            node_id="root",
            node_type=NodeType.SELECTOR,
            children=[node1, node2]
        )
        
        script = BehaviorScript(
            entity_id="test_entity",
            script_id="test_script",
            root_node=root
        )
        
        perception = PerceptionStatus(entity_id="test_entity", can_see_player=False)
        entity_state = {}
        
        result = service.evaluate_script(script, perception, entity_state)
        
        assert result is not None
        assert result.action_type == "patrol"
    
    def test_evaluate_script_with_sequence(self):
        """Test evaluating a script with a sequence node."""
        service = BehaviorScriptService()
        
        action1 = BehaviorAction(action_type="attack")
        node1 = BehaviorNode(
            node_id="node1",
            node_type=NodeType.ACTION,
            conditions=[BehaviorCondition(condition_type="can_see_player", value=True)],
            action=action1
        )
        
        action2 = BehaviorAction(action_type="wait")
        node2 = BehaviorNode(
            node_id="node2",
            node_type=NodeType.ACTION,
            action=action2
        )
        
        root = BehaviorNode(
            node_id="root",
            node_type=NodeType.SEQUENCE,
            children=[node1, node2]
        )
        
        script = BehaviorScript(
            entity_id="test_entity",
            script_id="test_script",
            root_node=root
        )
        
        perception = PerceptionStatus(entity_id="test_entity", can_see_player=True)
        entity_state = {}
        
        result = service.evaluate_script(script, perception, entity_state)
        
        # Sequence returns None (no action from sequence itself)
        assert result is None
    
    def test_evaluate_condition_can_see_player_true(self):
        """Test evaluating can_see_player condition when true."""
        service = BehaviorScriptService()
        
        condition = BehaviorCondition(condition_type="can_see_player")
        perception = PerceptionStatus(entity_id="test", can_see_player=True)
        
        result = service._evaluate_condition(condition, perception, {})
        
        assert result is True
    
    def test_evaluate_condition_can_see_player_false(self):
        """Test evaluating can_see_player condition when false."""
        service = BehaviorScriptService()
        
        condition = BehaviorCondition(condition_type="can_see_player")
        perception = PerceptionStatus(entity_id="test", can_see_player=False)
        
        result = service._evaluate_condition(condition, perception, {})
        
        assert result is False
    
    def test_evaluate_condition_health_below(self):
        """Test evaluating health_below condition."""
        service = BehaviorScriptService()
        
        condition = BehaviorCondition(condition_type="health_below", operator="<", value=0.5)
        perception = PerceptionStatus(entity_id="test")
        
        # Test with health below threshold (0.3 < 0.5 should be True)
        result = service._evaluate_condition(condition, perception, {"health_pct": 0.3})
        assert result is True
        
        # Test with health above threshold (0.7 < 0.5 should be False)
        result = service._evaluate_condition(condition, perception, {"health_pct": 0.7})
        assert result is False
    
    def test_evaluate_condition_loyalty_above(self):
        """Test evaluating loyalty_above condition."""
        service = BehaviorScriptService()
        
        condition = BehaviorCondition(condition_type="loyalty_above", operator=">", value=0.7)
        perception = PerceptionStatus(entity_id="test")
        
        from src.domain.value_objects.social import LoyaltyState
        loyalty = LoyaltyState(minion_id="test", leader_id="leader", loyalty_score=0.8)
        
        # loyalty_score (0.8) > value (0.7) should be True
        result = service._evaluate_condition(condition, perception, {"loyalty": loyalty})
        assert result is True
        
        # Test with loyalty below threshold
        loyalty2 = LoyaltyState(minion_id="test2", leader_id="leader", loyalty_score=0.5)
        result = service._evaluate_condition(condition, perception, {"loyalty": loyalty2})
        assert result is False
    
    def test_evaluate_condition_in_combat(self):
        """Test evaluating in_combat condition."""
        service = BehaviorScriptService()
        
        condition = BehaviorCondition(condition_type="in_combat")
        perception = PerceptionStatus(entity_id="test")
        
        result = service._evaluate_condition(condition, perception, {"in_combat": True})
        assert result is True
        
        result = service._evaluate_condition(condition, perception, {"in_combat": False})
        assert result is False


class TestValidateScript:
    """Tests for script validation."""
    
    def test_validate_script_valid_goblin(self):
        """Test validating a valid goblin script."""
        service = BehaviorScriptService()
        
        action = BehaviorAction(action_type="attack")
        node = BehaviorNode(
            node_id="root",
            node_type=NodeType.ACTION,
            conditions=[BehaviorCondition(condition_type="can_see_player")],
            action=action
        )
        script = BehaviorScript(
            entity_id="goblin_1",
            script_id="goblin_script",
            root_node=node
        )
        
        is_valid, errors = service.validate_script(script, "goblin")
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_script_invalid_condition(self):
        """Test validating a script with invalid condition."""
        service = BehaviorScriptService()
        
        action = BehaviorAction(action_type="attack")
        node = BehaviorNode(
            node_id="root",
            node_type=NodeType.ACTION,
            conditions=[BehaviorCondition(condition_type="invalid_condition")],
            action=action
        )
        script = BehaviorScript(
            entity_id="goblin_1",
            script_id="goblin_script",
            root_node=node
        )
        
        is_valid, errors = service.validate_script(script, "goblin")
        
        assert is_valid is False
        assert "invalid_condition" in errors[0]
    
    def test_validate_script_invalid_action(self):
        """Test validating a script with invalid action."""
        service = BehaviorScriptService()
        
        action = BehaviorAction(action_type="invalid_action")
        node = BehaviorNode(
            node_id="root",
            node_type=NodeType.ACTION,
            action=action
        )
        script = BehaviorScript(
            entity_id="goblin_1",
            script_id="goblin_script",
            root_node=node
        )
        
        is_valid, errors = service.validate_script(script, "goblin")
        
        assert is_valid is False
        assert "invalid_action" in errors[0]


class TestCreateDefaultScript:
    """Tests for creating default scripts."""
    
    def test_create_default_script(self):
        """Test creating a default script."""
        service = BehaviorScriptService()
        
        script = service.create_default_script("goblin", "goblin_001")
        
        assert isinstance(script, BehaviorScript)
        assert script.entity_id == "goblin_001"
        assert "goblin" in script.script_id
        assert script.root_node is not None
    
    def test_create_default_script_has_children(self):
        """Test that default script has child nodes."""
        service = BehaviorScriptService()
        
        script = service.create_default_script("wolf", "wolf_001")
        
        assert len(script.root_node.children) >= 2


class TestParseScriptFromJson:
    """Tests for parsing scripts from JSON."""
    
    def test_parse_script_from_json(self):
        """Test parsing a script from JSON data."""
        service = BehaviorScriptService()
        
        json_data = {
            "entity_id": "test_entity",
            "script_id": "test_script",
            "root_node": {
                "node_id": "root",
                "node_type": "action",
                "action": {
                    "action_type": "wait"
                }
            },
            "valid_conditions": ["can_see_player"],
            "valid_actions": ["wait"]
        }
        
        script = service.parse_script_from_json(json_data)
        
        assert script.entity_id == "test_entity"
        assert script.script_id == "test_script"
        assert script.root_node.node_type == "action"
        assert script.root_node.action.action_type == "wait"
    
    def test_parse_script_with_conditions(self):
        """Test parsing a script with conditions."""
        service = BehaviorScriptService()
        
        json_data = {
            "entity_id": "test_entity",
            "script_id": "test_script",
            "root_node": {
                "node_id": "root",
                "node_type": "action",
                "conditions": [
                    {"condition_type": "can_see_player", "operator": "==", "value": True}
                ],
                "action": {
                    "action_type": "attack",
                    "target": "player"
                }
            }
        }
        
        script = service.parse_script_from_json(json_data)
        
        assert len(script.root_node.conditions) == 1
        assert script.root_node.conditions[0].condition_type == "can_see_player"
        assert script.root_node.action.target == "player"


class TestMobBehaviorCatalog:
    """Tests for MOB_BEHAVIOR_CATALOG."""
    
    def test_catalog_contains_goblin(self):
        """Test that catalog contains goblin entry."""
        assert "goblin" in MOB_BEHAVIOR_CATALOG
        goblin = MOB_BEHAVIOR_CATALOG["goblin"]
        assert "can_see_player" in goblin["conditions"]
        assert "attack" in goblin["actions"]
    
    def test_catalog_contains_wolf(self):
        """Test that catalog contains wolf entry."""
        assert "wolf" in MOB_BEHAVIOR_CATALOG
        wolf = MOB_BEHAVIOR_CATALOG["wolf"]
        assert "can_smell_player" in wolf["conditions"]
    
    def test_catalog_contains_spider(self):
        """Test that catalog contains spider entry."""
        assert "spider" in MOB_BEHAVIOR_CATALOG
        spider = MOB_BEHAVIOR_CATALOG["spider"]
        assert "environment_danger_above" in spider["conditions"]
        assert "hide" in spider["actions"]
    
    def test_catalog_contains_default(self):
        """Test that catalog contains default entry."""
        assert "default" in MOB_BEHAVIOR_CATALOG
        default = MOB_BEHAVIOR_CATALOG["default"]
        assert len(default["conditions"]) == 4
        assert len(default["actions"]) == 4