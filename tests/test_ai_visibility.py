"""Tests for AI visibility-based attack behavior."""

import pytest
from unittest.mock import MagicMock
from src.domain.components.ai import AI
from src.domain.components.perception_component import PerceptionComponent
from src.domain.value_objects.perception import PerceptionStatus
from src.domain.value_objects.position import Position


class TestAIVisibilityCheck:
    """Tests for AI checking visibility before attacking."""
    
    def test_can_see_target_returns_true_when_perception_shows_player(self):
        """Test that _can_see_target returns True when perception component shows player visible."""
        ai = AI()
        ai.target_id = "player_1"
        
        # Create entity with perception component
        entity = MagicMock()
        entity.position = Position(0, 0)
        
        # Mock get_component to return perception component
        perception_comp = MagicMock()
        perception_comp.current_status = PerceptionStatus(
            entity_id="mob_1",
            can_see_player=True
        )
        entity.get_component.return_value = perception_comp
        
        entity_pos = Position(0, 0)
        
        result = ai._can_see_target(entity, entity_pos)
        assert result is True
    
    def test_can_see_target_returns_false_when_perception_hides_player(self):
        """Test that _can_see_target returns False when perception component shows player not visible."""
        ai = AI()
        ai.target_id = "player_1"
        
        # Create entity with perception component
        entity = MagicMock()
        entity.position = Position(0, 0)
        
        # Mock get_component to return perception component with player not visible
        perception_comp = MagicMock()
        perception_comp.current_status = PerceptionStatus(
            entity_id="mob_1",
            can_see_player=False
        )
        entity.get_component.return_value = perception_comp
        
        entity_pos = Position(0, 0)
        
        result = ai._can_see_target(entity, entity_pos)
        assert result is False
    
    def test_can_see_target_falls_back_to_distance_when_no_perception(self):
        """Test that _can_see_target falls back to distance check when no perception component."""
        ai = AI()
        ai.target_id = "player_1"
        ai.vision_range = 10
        
        # Create entity without perception component
        entity = MagicMock()
        entity.position = Position(0, 0)
        entity.get_component.return_value = None
        
        # Mock _get_entity_position to return a position within range
        ai._get_entity_position = MagicMock(return_value=Position(5, 5))
        
        entity_pos = Position(0, 0)
        
        result = ai._can_see_target(entity, entity_pos)
        assert result is True
    
    def test_can_see_target_returns_false_when_no_perception_and_out_of_range(self):
        """Test that _can_see_target returns False when no perception and out of range."""
        ai = AI()
        ai.target_id = "player_1"
        ai.vision_range = 5
        
        # Create entity without perception component
        entity = MagicMock()
        entity.position = Position(0, 0)
        entity.get_component.return_value = None
        
        # Mock _get_entity_position to return a position out of range
        ai._get_entity_position = MagicMock(return_value=Position(20, 20))
        
        entity_pos = Position(0, 0)
        
        result = ai._can_see_target(entity, entity_pos)
        assert result is False
    
    def test_handle_chasing_state_switches_to_searching_when_not_visible(self):
        """Test that chasing state switches to searching when target not visible."""
        ai = AI()
        ai.target_id = "player_1"
        ai.behavior_state = "chasing"
        
        # Create entity with perception component showing player not visible
        entity = MagicMock()
        entity.position = Position(0, 0)
        
        perception_comp = MagicMock()
        perception_comp.current_status = PerceptionStatus(
            entity_id="mob_1",
            can_see_player=False
        )
        entity.get_component.return_value = perception_comp
        
        entity_pos = Position(0, 0)
        delta_time = 0.1
        
        ai._handle_chasing_state(delta_time, entity, entity_pos)
        
        # Should have switched to searching state
        assert ai.behavior_state == "searching"
    
    def test_handle_chasing_state_attacks_when_visible_and_in_range(self):
        """Test that chasing state attacks when target visible and in range."""
        ai = AI()
        ai.target_id = "player_1"
        ai.behavior_state = "chasing"
        ai.attack_range = 1
        
        # Create entity with perception component showing player visible
        entity = MagicMock()
        entity.position = Position(0, 0)
        
        perception_comp = MagicMock()
        perception_comp.current_status = PerceptionStatus(
            entity_id="mob_1",
            can_see_player=True
        )
        entity.get_component.return_value = perception_comp
        
        # Mock _get_entity_position to return position in range
        ai._get_entity_position = MagicMock(return_value=Position(0, 0))
        
        entity_pos = Position(0, 0)
        delta_time = 0.1
        
        # Mock _attack_target to track if called
        ai._attack_target = MagicMock()
        
        ai._handle_chasing_state(delta_time, entity, entity_pos)
        
        # Should have called attack
        ai._attack_target.assert_called_once_with(entity, "player_1")
    
    def test_aggressive_ai_clears_target_when_not_visible(self):
        """Test that aggressive AI clears target when not visible."""
        ai = AI()
        ai.target_id = "player_1"
        ai.ai_type = "aggressive"
        
        # Create entity with perception component showing player not visible
        entity = MagicMock()
        entity.position = Position(0, 0)
        
        perception_comp = MagicMock()
        perception_comp.current_status = PerceptionStatus(
            entity_id="mob_1",
            can_see_player=False
        )
        entity.get_component.return_value = perception_comp
        
        entity_pos = Position(0, 0)
        delta_time = 0.1
        
        ai._update_aggressive_ai(delta_time, entity, entity_pos)
        
        # Target should be cleared and state should be idle
        assert ai.target_id is None
        assert ai.behavior_state == "idle"
    
    def test_aggressive_ai_chases_when_visible(self):
        """Test that aggressive AI chases when target is visible."""
        ai = AI()
        ai.target_id = "player_1"
        ai.ai_type = "aggressive"
        ai.behavior_state = "chasing"  # Start in chasing state
        
        # Create entity with perception component showing player visible
        entity = MagicMock()
        entity.position = Position(0, 0)
        
        perception_comp = MagicMock()
        perception_comp.current_status = PerceptionStatus(
            entity_id="mob_1",
            can_see_player=True
        )
        entity.get_component.return_value = perception_comp
        
        # Mock _get_entity_position to return position in range
        ai._get_entity_position = MagicMock(return_value=Position(5, 5))
        
        entity_pos = Position(0, 0)
        delta_time = 0.1
        
        ai._update_aggressive_ai(delta_time, entity, entity_pos)
        
        # Should still be in chasing state (not cleared)
        assert ai.behavior_state == "chasing"