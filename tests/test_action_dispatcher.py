"""Tests for ActionDispatcher."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.domain.services.action_dispatcher import ActionDispatcher
from src.domain.value_objects.behavior_script import BehaviorAction, ActionType
from src.domain.value_objects.position import Position
class TestActionDispatcher:
    """Test cases for ActionDispatcher."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_combat_service = Mock()
        self.mock_movement_service = Mock()
        self.mock_social_service = Mock()
        self.mock_event_bus = Mock()
        
        self.dispatcher = ActionDispatcher(
            combat_service=self.mock_combat_service,
            movement_service=self.mock_movement_service,
            social_service=self.mock_social_service,
            event_bus=self.mock_event_bus
        )
        
        # Create test entities
        self.attacker = Mock()
        self.attacker.id = "attacker_1"
        self.attacker.name = "Attacker"
        self.attacker.position = Position(5, 5)
        self.attacker.is_alive = Mock(return_value=True)
        
        self.target = Mock()
        self.target.id = "target_1"
        self.target.name = "Target"
        self.target.position = Position(8, 8)
        self.target.is_alive = Mock(return_value=True)
        
        self.all_entities = [self.attacker, self.target]
    
    def test_attack_action_success(self):
        """Test successful attack action."""
        action = BehaviorAction(
            action_type=ActionType.ATTACK.value,
            target="target_1"
        )
        
        # Mock combat service response
        self.mock_combat_service.execute_attack.return_value = {
            "success": True,
            "damage": 10,
            "hit": True,
            "critical": False,
            "target_health": 90
        }
        
        result = self.dispatcher.execute(self.attacker, action, self.all_entities)
        
        assert result["success"] is True
        assert "Attacked" in result["message"]
        assert result["damage"] == 10
        assert result["hit"] is True
        self.mock_combat_service.execute_attack.assert_called_once_with(self.attacker, self.target)
    
    def test_attack_action_no_target(self):
        """Test attack action with no target."""
        action = BehaviorAction(
            action_type=ActionType.ATTACK.value,
            target=None
        )
        
        result = self.dispatcher.execute(self.attacker, action, self.all_entities)
        
        assert result["success"] is False
        assert "No target specified" in result["message"]
        self.mock_combat_service.execute_attack.assert_not_called()
    
    def test_attack_action_target_not_found(self):
        """Test attack action with target not found."""
        action = BehaviorAction(
            action_type=ActionType.ATTACK.value,
            target="nonexistent_target"
        )
        
        result = self.dispatcher.execute(self.attacker, action, self.all_entities)
        
        assert result["success"] is False
        assert "not found" in result["message"]
        self.mock_combat_service.execute_attack.assert_not_called()
    
    def test_attack_action_target_too_far(self):
        """Test attack action with target too far away."""
        # Move target far away
        self.target.position = Position(20, 20)
        
        action = BehaviorAction(
            action_type=ActionType.ATTACK.value,
            target="target_1"
        )
        
        result = self.dispatcher.execute(self.attacker, action, self.all_entities)
        
        assert result["success"] is False
        assert "too far away" in result["message"]
        self.mock_combat_service.execute_attack.assert_not_called()
    
    def test_flee_action_success(self):
        """Test successful flee action."""
        action = BehaviorAction(
            action_type=ActionType.FLEE.value,
            target="attacker_1"
        )
        
        # Mock movement service
        self.mock_movement_service.can_move_to.return_value = True
        self.mock_movement_service.move_entity.return_value = True
        
        result = self.dispatcher.execute(self.attacker, action, self.all_entities)
        
        assert result["success"] is True
        assert "Fled" in result["message"]
        self.mock_movement_service.can_move_to.assert_called()
        self.mock_movement_service.move_entity.assert_called()
    
    def test_flee_action_no_threat(self):
        """Test flee action with no threat."""
        # Only attacker in entities
        single_entity = [self.attacker]
        
        action = BehaviorAction(
            action_type=ActionType.FLEE.value,
            target="attacker_1"
        )
        
        result = self.dispatcher.execute(self.attacker, action, single_entity)
        
        assert result["success"] is False
        assert "No threat" in result["message"]
        self.mock_movement_service.can_move_to.assert_not_called()
    
    def test_patrol_action_with_points(self):
        """Test patrol action with patrol points."""
        # Mock AI component with patrol points
        mock_ai = Mock()
        mock_ai.patrol_points = [Position(10, 10), Position(15, 15)]
        self.attacker.get_component = Mock(return_value=mock_ai)
        
        action = BehaviorAction(
            action_type=ActionType.PATROL.value
        )
        
        # Mock movement service
        self.mock_movement_service.can_move_to.return_value = True
        self.mock_movement_service.move_entity.return_value = True
        
        result = self.dispatcher.execute(self.attacker, action, self.all_entities)
        
        assert result["success"] is True
        assert "Moving to patrol point" in result["message"]
        self.mock_movement_service.can_move_to.assert_called()
        self.mock_movement_service.move_entity.assert_called()
    
    def test_patrol_action_no_points(self):
        """Test patrol action without patrol points (should wander)."""
        # Mock AI component without patrol points
        mock_ai = Mock()
        mock_ai.patrol_points = []
        self.attacker.get_component = Mock(return_value=mock_ai)
        
        action = BehaviorAction(
            action_type=ActionType.PATROL.value
        )
        
        # Mock movement service
        self.mock_movement_service.can_move_to.return_value = True
        self.mock_movement_service.move_entity.return_value = True
        
        result = self.dispatcher.execute(self.attacker, action, self.all_entities)
        
        assert result["success"] is True
        assert "Wandering" in result["message"]
        self.mock_movement_service.can_move_to.assert_called()
        self.mock_movement_service.move_entity.assert_called()
    
    def test_move_to_action_success(self):
        """Test successful move_to action."""
        action = BehaviorAction(
            action_type=ActionType.MOVE_TO.value,
            parameters={"position": {"x": 10, "y": 10}}
        )
        
        # Mock movement service
        self.mock_movement_service.can_move_to.return_value = True
        self.mock_movement_service.move_entity.return_value = True
        
        result = self.dispatcher.execute(self.attacker, action, self.all_entities)
        
        assert result["success"] is True
        assert "Moved to" in result["message"]
        self.mock_movement_service.can_move_to.assert_called()
        self.mock_movement_service.move_entity.assert_called()
    
    def test_move_to_action_blocked(self):
        """Test move_to action with blocked position."""
        action = BehaviorAction(
            action_type=ActionType.MOVE_TO.value,
            parameters={"position": {"x": 10, "y": 10}}
        )
        
        # Mock movement service to return False for can_move_to
        self.mock_movement_service.can_move_to.return_value = False
        
        result = self.dispatcher.execute(self.attacker, action, self.all_entities)
        
        assert result["success"] is False
        assert "blocked" in result["message"] or "out of bounds" in result["message"]
        self.mock_movement_service.can_move_to.assert_called()
        self.mock_movement_service.move_entity.assert_not_called()
    
    def test_wait_action(self):
        """Test wait action."""
        action = BehaviorAction(
            action_type=ActionType.WAIT.value
        )
        
        result = self.dispatcher.execute(self.attacker, action, self.all_entities)
        
        assert result["success"] is True
        assert "Waiting" in result["message"]
    
    def test_gift_item_action_success(self):
        """Test successful gift item action."""
        action = BehaviorAction(
            action_type=ActionType.GIFT_ITEM.value,
            target="target_1",
            target_item_id="item_1"
        )
        
        # Mock social service
        self.mock_social_service.process_gift.return_value = {"success": True}
        
        # Mock entity inventories
        self.attacker.inventory = Mock()
        self.attacker.inventory.get_items.return_value = ["item_1"]
        self.attacker.inventory.remove_item = Mock()
        self.attacker.inventory.add_item = Mock()
        
        self.target.inventory = Mock()
        self.target.inventory.get_items.return_value = []
        self.target.inventory.remove_item = Mock()
        self.target.inventory.add_item = Mock()
        
        result = self.dispatcher.execute(self.attacker, action, self.all_entities)
        
        assert result["success"] is True
        assert "Gave item" in result["message"]
        self.mock_social_service.process_gift.assert_called_once_with(
            "attacker_1", "target_1", 10.0, 0
        )
    
    def test_gift_item_action_no_item(self):
        """Test gift item action with no item."""
        action = BehaviorAction(
            action_type=ActionType.GIFT_ITEM.value,
            target="target_1"
        )
        
        # Mock entity with empty inventory
        self.attacker.inventory = Mock()
        self.attacker.inventory.get_items.return_value = []
        
        result = self.dispatcher.execute(self.attacker, action, self.all_entities)
        
        assert result["success"] is False
        assert "No item to give" in result["message"]
    
    def test_unknown_action_type(self):
        """Test unknown action type."""
        action = BehaviorAction(
            action_type="UNKNOWN_ACTION"
        )
        
        result = self.dispatcher.execute(self.attacker, action, self.all_entities)
        
        assert result["success"] is False
        assert "Unknown action type" in result["message"]
    
    def test_event_publishing_on_attack(self):
        """Test that events are published on successful attack."""
        action = BehaviorAction(
            action_type=ActionType.ATTACK.value,
            target="target_1"
        )
        
        # Mock combat service response
        self.mock_combat_service.execute_attack.return_value = {
            "success": True,
            "damage": 10,
            "hit": True,
            "critical": False,
            "target_health": 90
        }
        
        result = self.dispatcher.execute(self.attacker, action, self.all_entities)
        
        # Check that event bus was called
        self.mock_event_bus.publish_event.assert_called()
        # Should be called with HIT event type
        call_args = self.mock_event_bus.publish_event.call_args
        assert call_args[0][0] == "HIT"
    
    def test_event_publishing_on_flee(self):
        """Test that events are published on successful flee."""
        action = BehaviorAction(
            action_type=ActionType.FLEE.value,
            target="attacker_1"
        )
        
        # Mock movement service
        self.mock_movement_service.can_move_to.return_value = True
        self.mock_movement_service.move_entity.return_value = True
        
        result = self.dispatcher.execute(self.attacker, action, self.all_entities)
        
        # Check that event bus was called
        self.mock_event_bus.publish_event.assert_called()
        # Should be called with entity_fled event type
        call_args = self.mock_event_bus.publish_event.call_args
        assert call_args[0][0] == "entity_fled"
    
    def test_is_ally_check(self):
        """Test ally detection."""
        # Mock social components
        mock_social1 = Mock()
        mock_social1.structure_id = "structure_1"
        mock_social1.is_leader = False
        
        mock_social2 = Mock()
        mock_social2.structure_id = "structure_1"
        mock_social2.is_leader = False
        
        self.attacker.get_component = Mock(return_value=mock_social1)
        self.target.get_component = Mock(return_value=mock_social2)
        
        assert self.dispatcher._is_ally(self.attacker, self.target) is True
    
    def test_is_ally_different_structures(self):
        """Test ally detection with different social structures."""
        # Mock social components with different structures
        mock_social1 = Mock()
        mock_social1.structure_id = "structure_1"
        mock_social1.is_leader = False
        
        mock_social2 = Mock()
        mock_social2.structure_id = "structure_2"
        mock_social2.is_leader = False
        
        self.attacker.get_component = Mock(return_value=mock_social1)
        self.target.get_component = Mock(return_value=mock_social2)
        
        assert self.dispatcher._is_ally(self.attacker, self.target) is False
    
    def test_can_give_orders_leader(self):
        """Test can_give_orders for leader."""
        # Mock leader social component
        mock_social = Mock()
        mock_social.is_leader = True
        self.attacker.get_component = Mock(return_value=mock_social)
        
        assert self.dispatcher._can_give_orders(self.attacker) is True
    
    def test_can_give_orders_non_leader(self):
        """Test can_give_orders for non-leader."""
        # Mock non-leader social component
        mock_social = Mock()
        mock_social.is_leader = False
        mock_social.can_give_orders = Mock(return_value=False)
        self.attacker.get_component = Mock(return_value=mock_social)
        
        assert self.dispatcher._can_give_orders(self.attacker) is False