"""Tests for BehaviorComponent."""

import pytest
from src.domain.components.behavior_component import BehaviorComponent
from src.domain.value_objects.behavior_script import (
    BehaviorScript, BehaviorNode, BehaviorAction, NodeType
)


class TestBehaviorComponent:
    """Tests for BehaviorComponent."""

    def test_component_type(self):
        """Test component type is correct."""
        comp = BehaviorComponent(entity_id="test_entity")
        assert comp.component_type == "behavior"

    def test_default_values(self):
        """Test default values are set correctly."""
        comp = BehaviorComponent(entity_id="test_entity")
        assert comp.entity_id == "test_entity"
        assert comp.current_script is None
        assert comp.last_action is None
        assert comp.last_evaluated_tick == 0
        assert comp.evaluation_interval == 1
        assert comp.state == {}

    def test_set_script(self):
        """Test setting a behavior script."""
        comp = BehaviorComponent(entity_id="test_entity")
        script = BehaviorScript(
            entity_id="test_entity",
            script_id="script_001",
            root_node=BehaviorNode(node_id="root", node_type=NodeType.SELECTOR)
        )
        comp.set_script(script)

        assert comp.current_script == script
        assert comp.state == {}  # State should be cleared

    def test_should_evaluate(self):
        """Test evaluation timing check."""
        comp = BehaviorComponent(entity_id="test_entity", evaluation_interval=5)
        comp.last_evaluated_tick = 10

        assert comp.should_evaluate(15) is True  # 15 - 10 >= 5
        assert comp.should_evaluate(14) is False  # 14 - 10 < 5
        assert comp.should_evaluate(10) is False  # 10 - 10 < 5

    def test_record_evaluation(self):
        """Test recording evaluation results."""
        comp = BehaviorComponent(entity_id="test_entity")
        action = BehaviorAction(action_type="attack", target="player")

        comp.record_evaluation(tick=20, action=action)

        assert comp.last_evaluated_tick == 20
        assert comp.last_action == action

    def test_record_evaluation_none_action(self):
        """Test recording evaluation with no action."""
        comp = BehaviorComponent(entity_id="test_entity")
        comp.record_evaluation(tick=25, action=None)

        assert comp.last_evaluated_tick == 25
        assert comp.last_action is None

    def test_with_custom_interval(self):
        """Test component with custom evaluation interval."""
        comp = BehaviorComponent(entity_id="test_entity", evaluation_interval=10)
        assert comp.evaluation_interval == 10

    def test_state_persistence(self):
        """Test that state persists between evaluations."""
        comp = BehaviorComponent(entity_id="test_entity")
        comp.state["custom_key"] = "custom_value"

        # State should persist
        assert comp.state["custom_key"] == "custom_value"

        # After setting a new script, state should be cleared
        script = BehaviorScript(
            entity_id="test_entity",
            script_id="script_002",
            root_node=BehaviorNode(node_id="root", node_type=NodeType.SELECTOR)
        )
        comp.set_script(script)
        assert comp.state == {}