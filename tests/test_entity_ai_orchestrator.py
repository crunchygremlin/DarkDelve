"""Tests for EntityAIOrchestrator."""

import pytest
from unittest.mock import MagicMock, Mock
from src.domain.services.entity_ai_orchestrator import EntityAIOrchestrator
from src.domain.value_objects.perception import PerceptionStatus
from src.domain.value_objects.behavior_script import BehaviorScript, BehaviorNode, NodeType
from src.domain.value_objects.llm_logging import LLMLogger


class TestEntityAIOrchestrator:
    """Tests for EntityAIOrchestrator."""

    def test_init(self):
        """Test orchestrator initialization."""
        perception_service = Mock()
        behavior_service = Mock()
        social_service = Mock()
        player_profile_service = Mock()
        llm_logger = Mock()

        orchestrator = EntityAIOrchestrator(
            perception_service=perception_service,
            behavior_service=behavior_service,
            social_service=social_service,
            player_profile_service=player_profile_service,
            llm_logger=llm_logger,
            event_bus=None
        )

        assert orchestrator.perception_service == perception_service
        assert orchestrator.behavior_service == behavior_service
        assert orchestrator.social_service == social_service
        assert orchestrator.player_profile_service == player_profile_service
        assert orchestrator._tick == 0

    def test_tick_increments(self):
        """Test that tick increments correctly."""
        orchestrator = EntityAIOrchestrator(
            perception_service=Mock(),
            behavior_service=Mock(),
            social_service=Mock(),
            player_profile_service=Mock(),
            llm_logger=Mock(),
            event_bus=None
        )

        orchestrator.tick([], Mock(), Mock(), [])
        assert orchestrator.current_tick == 1

        orchestrator.tick([], Mock(), Mock(), [])
        assert orchestrator.current_tick == 2

    def test_tick_updates_perception(self):
        """Test that perception is updated for entities."""
        perception_service = Mock()
        perception_service.compute_perception.return_value = PerceptionStatus(entity_id="entity_1")

        behavior_service = Mock()
        social_service = Mock()
        player_profile_service = Mock()
        llm_logger = Mock()

        orchestrator = EntityAIOrchestrator(
            perception_service=perception_service,
            behavior_service=behavior_service,
            social_service=social_service,
            player_profile_service=player_profile_service,
            llm_logger=llm_logger,
            event_bus=None
        )

        # Create mock entity with perception component
        entity = Mock()
        entity.id = "entity_1"
        entity.get_component.return_value = Mock(
            modifiers=Mock(),
            update_status=Mock()
        )
        entity.get_component.side_effect = lambda name: Mock(
            modifiers=Mock(),
            update_status=Mock()
        ) if name == "perception" else None

        orchestrator.tick([entity], Mock(), Mock(), [])

        perception_service.compute_perception.assert_called_once()

    def test_tick_evaluates_behaviors(self):
        """Test that behaviors are evaluated."""
        perception_service = Mock()
        behavior_service = Mock()
        behavior_service.evaluate_script.return_value = None

        social_service = Mock()
        player_profile_service = Mock()
        llm_logger = Mock()

        orchestrator = EntityAIOrchestrator(
            perception_service=perception_service,
            behavior_service=behavior_service,
            social_service=social_service,
            player_profile_service=player_profile_service,
            llm_logger=llm_logger,
            event_bus=None
        )

        # Create mock entity with behavior and perception components
        entity = Mock()
        entity.id = "entity_1"

        perception_comp = Mock()
        perception_comp.current_status = PerceptionStatus(entity_id="entity_1")

        behavior_comp = Mock()
        behavior_comp.current_script = BehaviorScript(
            entity_id="entity_1",
            script_id="script_001",
            root_node=BehaviorNode(node_id="root", node_type=NodeType.SELECTOR)
        )
        behavior_comp.should_evaluate.return_value = True

        def get_component_side_effect(name):
            if name == "perception":
                return perception_comp
            elif name == "behavior":
                return behavior_comp
            return None

        entity.get_component.side_effect = get_component_side_effect

        orchestrator.tick([entity], Mock(), Mock(), [])

        behavior_service.evaluate_script.assert_called_once()

    def test_build_entity_state(self):
        """Test building entity state dict."""
        orchestrator = EntityAIOrchestrator(
            perception_service=Mock(),
            behavior_service=Mock(),
            social_service=Mock(),
            player_profile_service=Mock(),
            llm_logger=Mock(),
            event_bus=None
        )

        entity = Mock()
        entity.health_pct = 0.75
        entity.in_combat = True

        social_comp = Mock()
        social_comp.is_leader = False
        social_comp.role = "guard"
        social_comp.personal_wealth = 100.0
        social_comp.loyalty = Mock(loyalty_score=0.8)

        state = orchestrator._build_entity_state(entity, social_comp)

        assert state["health_pct"] == 0.75
        assert state["in_combat"] is True
        assert state["is_leader"] is False
        assert state["is_guard"] is True
        assert state["wealth"] == 100.0
        assert state["loyalty_score"] == 0.8

    def test_build_entity_state_no_social(self):
        """Test building entity state without social component."""
        orchestrator = EntityAIOrchestrator(
            perception_service=Mock(),
            behavior_service=Mock(),
            social_service=Mock(),
            player_profile_service=Mock(),
            llm_logger=Mock(),
            event_bus=None
        )

        entity = Mock()
        entity.health_pct = 1.0
        entity.in_combat = False

        state = orchestrator._build_entity_state(entity, None)

        assert state["health_pct"] == 1.0
        assert state["in_combat"] is False
        assert state["is_leader"] is False
        assert state["wealth"] == 0.0

    def test_check_social_events(self):
        """Test checking for social events."""
        perception_service = Mock()
        behavior_service = Mock()
        social_service = Mock()
        social_service.check_desertion.return_value = False
        social_service.check_betrayal.return_value = False

        player_profile_service = Mock()
        llm_logger = Mock()

        orchestrator = EntityAIOrchestrator(
            perception_service=perception_service,
            behavior_service=behavior_service,
            social_service=social_service,
            player_profile_service=player_profile_service,
            llm_logger=llm_logger,
            event_bus=None
        )

        entity = Mock()
        entity.id = "entity_1"
        entity.get_component.return_value = Mock(
            loyalty=Mock(minion_id="entity_1")
        )

        orchestrator._check_social_events([entity])

        social_service.check_desertion.assert_called_once()
        social_service.check_betrayal.assert_called_once()

    def test_handle_desertion_with_event_bus(self):
        """Test desertion handling with event bus."""
        event_bus = Mock()

        orchestrator = EntityAIOrchestrator(
            perception_service=Mock(),
            behavior_service=Mock(),
            social_service=Mock(),
            player_profile_service=Mock(),
            llm_logger=Mock(),
            event_bus=event_bus
        )

        entity = Mock()
        entity.id = "entity_1"

        orchestrator._handle_desertion(entity)

        event_bus.publish.assert_called_once_with("minion_deserted", {"entity_id": "entity_1"})

    def test_handle_betrayal_with_event_bus(self):
        """Test betrayal handling with event bus."""
        event_bus = Mock()

        orchestrator = EntityAIOrchestrator(
            perception_service=Mock(),
            behavior_service=Mock(),
            social_service=Mock(),
            player_profile_service=Mock(),
            llm_logger=Mock(),
            event_bus=event_bus
        )

        entity = Mock()
        entity.id = "entity_1"

        orchestrator._handle_betrayal(entity)

        event_bus.publish.assert_called_once_with("minion_betrayed", {"entity_id": "entity_1"})