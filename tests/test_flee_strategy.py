"""Tests for FleeStrategy service."""

import pytest
from unittest.mock import Mock
from src.domain.services.flee_strategy import FleeStrategy
from src.domain.value_objects.position import Position


class TestFleeStrategy:
    """Test cases for FleeStrategy class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.flee_strategy = FleeStrategy(flee_distance=5)
    
    def test_init_default_distance(self):
        """Test FleeStrategy initialization with default distance."""
        strategy = FleeStrategy()
        assert strategy.flee_distance == 5
    
    def test_init_custom_distance(self):
        """Test FleeStrategy initialization with custom distance."""
        strategy = FleeStrategy(flee_distance=10)
        assert strategy.flee_distance == 10
    
    def test_calculate_flee_position(self):
        """Test flee position calculation."""
        entity = Mock()
        entity.position = Position(10, 10)
        
        threat = Mock()
        threat.position = Position(8, 8)
        
        flee_pos = self.flee_strategy.calculate_flee_position(entity, threat)
        
        assert flee_pos is not None
        # Should flee away from threat (opposite direction)
        assert flee_pos.x > entity.position.x
        assert flee_pos.y > entity.position.y
    
    def test_calculate_flee_position_same_position(self):
        """Test flee position when entity and threat are at same position."""
        entity = Mock()
        entity.position = Position(10, 10)
        
        threat = Mock()
        threat.position = Position(10, 10)
        
        flee_pos = self.flee_strategy.calculate_flee_position(entity, threat)
        
        assert flee_pos is not None
        # Should pick a default direction
        assert flee_pos.x == 15
        assert flee_pos.y == 10
    
    def test_calculate_flee_position_missing_position(self):
        """Test flee position when entity or threat lacks position."""
        entity = Mock()
        entity.position = Position(10, 10)
        
        threat = Mock()
        threat.position = None  # Has position but it's None
        
        flee_pos = self.flee_strategy.calculate_flee_position(entity, threat)
        assert flee_pos is None
    
    def test_find_threat(self):
        """Test finding the nearest threat."""
        entity = Mock()
        entity.id = "entity_1"
        entity.position = Position(10, 10)
        
        threat1 = Mock()
        threat1.id = "threat_1"
        threat1.position = Position(12, 12)
        threat1.is_alive = Mock(return_value=True)
        
        threat2 = Mock()
        threat2.id = "threat_2"
        threat2.position = Position(20, 20)
        threat2.is_alive = Mock(return_value=True)
        
        all_entities = [entity, threat1, threat2]
        
        found_threat = self.flee_strategy.find_threat(entity, all_entities)
        
        assert found_threat == threat1  # Closer threat
    
    def test_find_threat_no_threats(self):
        """Test finding threat when none exist."""
        entity = Mock()
        entity.id = "entity_1"
        entity.position = Position(10, 10)
        
        all_entities = [entity]
        
        found_threat = self.flee_strategy.find_threat(entity, all_entities)
        assert found_threat is None
    
    def test_find_threat_ignores_dead_entities(self):
        """Test that dead entities are not considered threats."""
        entity = Mock()
        entity.id = "entity_1"
        entity.position = Position(10, 10)
        
        dead_threat = Mock()
        dead_threat.id = "dead_threat"
        dead_threat.position = Position(12, 12)
        dead_threat.is_alive = Mock(return_value=False)
        
        all_entities = [entity, dead_threat]
        
        found_threat = self.flee_strategy.find_threat(entity, all_entities)
        assert found_threat is None
    
    def test_execute_flee_success(self):
        """Test successful flee execution."""
        entity = Mock()
        entity.id = "entity_1"
        entity.position = Position(10, 10)
        entity.name = "TestEntity"
        
        threat = Mock()
        threat.position = Position(12, 12)
        threat.name = "TestThreat"
        
        movement_service = Mock()
        movement_service.can_move_to = Mock(return_value=True)
        movement_service.move_entity = Mock(return_value=True)
        
        event_bus = Mock()
        
        result = self.flee_strategy.execute_flee(
            entity, threat, movement_service, event_bus
        )
        
        assert result["success"] is True
        assert "Fled" in result["message"]
        movement_service.move_entity.assert_called_once()
    
    def test_execute_flee_blocked_position(self):
        """Test flee execution when position is blocked."""
        entity = Mock()
        entity.id = "entity_1"
        entity.position = Position(10, 10)
        
        threat = Mock()
        threat.position = Position(12, 12)
        
        movement_service = Mock()
        movement_service.can_move_to = Mock(return_value=False)
        
        result = self.flee_strategy.execute_flee(entity, threat, movement_service)
        
        assert result["success"] is False
        assert "blocked" in result["message"].lower()
    
    def test_execute_flee_cannot_move(self):
        """Test flee execution when movement fails."""
        entity = Mock()
        entity.id = "entity_1"
        entity.position = Position(10, 10)
        
        threat = Mock()
        threat.position = Position(12, 12)
        
        movement_service = Mock()
        movement_service.can_move_to = Mock(return_value=True)
        movement_service.move_entity = Mock(return_value=False)
        
        result = self.flee_strategy.execute_flee(entity, threat, movement_service)
        
        assert result["success"] is False
        assert "could not move" in result["message"].lower()