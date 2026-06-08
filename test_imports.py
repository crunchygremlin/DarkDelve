#!/usr/bin/env python3
"""
Test script to verify all imports work correctly.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test all imports."""
    print("Testing imports...")
    
    # Test domain imports
    try:
        from src.domain.entities.player import Player
        from src.domain.entities.mob import Mob
        from src.domain.entities.item import Item
        from src.domain.entities.entity import Entity
        print("✅ Domain entities imported successfully")
    except ImportError as e:
        print(f"❌ Domain entities import failed: {e}")
    
    try:
        from src.domain.value_objects.position import Position
        from src.domain.value_objects.stats import Stats
        from src.domain.value_objects.combat_event import CombatEvent, CombatEventType
        from src.domain.value_objects.inventory_slot import InventorySlot
        print("✅ Domain value objects imported successfully")
    except ImportError as e:
        print(f"❌ Domain value objects import failed: {e}")
    
    try:
        from src.domain.components.component import Component
        from src.domain.components.combat import Combat
        from src.domain.components.movement import Movement
        from src.domain.components.inventory import Inventory
        from src.domain.components.ai import AI
        from src.domain.components.equipment import Equipment
        print("✅ Domain components imported successfully")
    except ImportError as e:
        print(f"❌ Domain components import failed: {e}")
    
    try:
        from src.domain.services.combat_service import CombatService
        from src.domain.services.movement_service import MovementService
        from src.domain.services.inventory_service import InventoryService
        from src.domain.services.ai_service import AIService
        from src.domain.services.survival_service import SurvivalService
        print("✅ Domain services imported successfully")
    except ImportError as e:
        print(f"❌ Domain services import failed: {e}")
    
    # Test application imports
    try:
        from src.application.game_commands.base_command import BaseCommand, CommandResult
        from src.application.game_commands.move_command import MoveCommand
        from src.application.game_commands.attack_command import AttackCommand
        from src.application.game_commands.pickup_command import PickupCommand
        from src.application.game_commands.use_command import UseCommand
        from src.application.game_commands.equip_command import EquipCommand
        from src.application.game_commands.drop_command import DropCommand
        print("✅ Game commands imported successfully")
    except ImportError as e:
        print(f"❌ Game commands import failed: {e}")
    
    try:
        from src.application.game_queries.base_query import BaseQuery, QueryResult
        from src.application.game_queries.fov_query import FOVQuery
        from src.application.game_queries.combat_query import CombatQuery
        from src.application.game_queries.entity_query import EntityQuery
        from src.application.game_queries.inventory_query import InventoryQuery
        from src.application.game_queries.game_state_query import GameStateQuery
        print("✅ Game queries imported successfully")
    except ImportError as e:
        print(f"❌ Game queries import failed: {e}")
    
    try:
        from src.application.game_session.game_session import GameSession
        from src.application.game_session.game_session_factory import GameSessionFactory
        print("✅ Game session imported successfully")
    except ImportError as e:
        print(f"❌ Game session import failed: {e}")
    
    try:
        from src.application.event_system.base_event import Event, EventCategory
        from src.application.event_system.event_handler import EventHandler
        from src.application.event_system.event_bus import EventBus
        from src.application.event_system.handlers.combat_handler import CombatEventHandler
        from src.application.event_system.handlers.player_handler import PlayerEventHandler
        from src.application.event_system.handlers.system_handler import SystemEventHandler
        print("✅ Event system imported successfully")
    except ImportError as e:
        print(f"❌ Event system import failed: {e}")
    
    print("Import test completed!")

if __name__ == "__main__":
    test_imports()