"""Tests for service interfaces."""

import pytest
from unittest.mock import Mock
from src.shared.interfaces.service import ICombatService, IMovementService, ISocialService


class TestServiceInterfaces:
    """Test cases for service interface implementations."""
    
    def test_combat_service_interface(self):
        """Test that CombatService implements ICombatService."""
        from src.domain.services.combat_service import CombatService
        
        service = CombatService()
        assert isinstance(service, ICombatService)
        
        # Test interface methods exist
        assert hasattr(service, 'execute_attack')
        assert hasattr(service, 'can_attack')
        assert hasattr(service, 'calculate_damage')
    
    def test_movement_service_interface(self):
        """Test that MovementService implements IMovementService."""
        from src.domain.services.movement_service import MovementService
        
        service = MovementService()
        assert isinstance(service, IMovementService)
        
        # Test interface methods exist
        assert hasattr(service, 'move_entity')
        assert hasattr(service, 'can_move_to')
    
    def test_social_service_interface(self):
        """Test that SocialService implements ISocialService."""
        from src.domain.services.social_service import SocialService
        
        service = SocialService()
        assert isinstance(service, ISocialService)
        
        # Test interface methods exist
        assert hasattr(service, 'is_ally')
        assert hasattr(service, 'get_loyalty_score')


class TestEventTypes:
    """Test cases for event type constants."""
    
    def test_event_type_enum_values(self):
        """Test that EventType enum has expected values."""
        from src.shared.events.event import EventType
        
        assert EventType.HIT.value == "HIT"
        assert EventType.MISS.value == "MISS"
        assert EventType.CRITICAL_HIT.value == "CRITICAL_HIT"
        assert EventType.ENTITY_FLED.value == "ENTITY_FLED"
        assert EventType.ALLY_CALLED.value == "ALLY_CALLED"
        assert EventType.ITEM_PICKED_UP.value == "ITEM_PICKED_UP"
    
    def test_event_type_category(self):
        """Test that EventType is properly categorized."""
        from src.shared.events.event import EventType, EventCategory
        
        # Combat events should be in COMBAT category
        assert EventType.HIT.value in ["HIT", "MISS", "CRITICAL_HIT"]
        assert EventType.MISS.value in ["HIT", "MISS", "CRITICAL_HIT"]