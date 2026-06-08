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
        from domain.entities.player import Player
        from domain.entities.mob import Mob
        from domain.entities.item import Item
        from domain.entities.entity import Entity
        print("✅ Domain entities imported successfully")
    except ImportError as e:
        print(f"❌ Domain entities import failed: {e}")
    
    try:
        from domain.value_objects.position import Position
        from domain.value_objects.stats import Stats
        from domain.value_objects.combat_event import CombatEvent, CombatEventType
        from domain.value_objects.inventory_slot import InventorySlot
        print("✅ Domain value objects imported successfully")
    except ImportError as e:
        print(f"❌ Domain value objects import failed: {e}")
    
    try:
        from domain.components.component import Component
        from domain.components.combat import Combat
        from domain.components.movement import Movement
        from domain.components.inventory import Inventory
        from domain.components.ai import AI
        from domain.components.equipment import Equipment
        print("✅ Domain components imported successfully")
    except ImportError as e:
        print(f"❌ Domain components import failed: {e}")
    
    try:
        from domain.services.combat_service import CombatService
        from domain.services.movement_service import MovementService
        from domain.services.inventory_service import InventoryService
        from domain.services.ai_service import AIService
        from domain.services.survival_service import SurvivalService
        print("✅ Domain services imported successfully")
    except ImportError as e:
        print(f"❌ Domain services import failed: {e}")
    
    # Test application imports
    try:
        from application.game_commands.base_command import BaseCommand, CommandResult
        from application.game_commands.move_command import MoveCommand
        from application.game_commands.attack_command import AttackCommand
        from application.game_commands.pickup_command import PickupCommand
        from application.game_commands.use_command import UseCommand
        from application.game_commands.equip_command import EquipCommand
        from application.game_commands.drop_command import DropCommand
        print("✅ Game commands imported successfully")
    except ImportError as e:
        print(f"❌ Game commands import failed: {e}")
    
    try:
        from application.game_queries.base_query import BaseQuery, QueryResult
        from application.game_queries.fov_query import FOVQuery
        from application.game_queries.combat_query import CombatQuery
        from application.game_queries.entity_query import EntityQuery
        from application.game_queries.inventory_query import InventoryQuery
        from application.game_queries.game_state_query import GameStateQuery
        print("✅ Game queries imported successfully")
    except ImportError as e:
        print(f"❌ Game queries import failed: {e}")
    
    try:
        from application.game_session.game_session import GameSession
        from application.game_session.game_session_factory import GameSessionFactory
        print("✅ Game session imported successfully")
    except ImportError as e:
        print(f"❌ Game session import failed: {e}")
    
    try:
        from application.event_system.base_event import Event, EventCategory
        from application.event_system.event_handler import EventHandler
        from application.event_system.event_bus import EventBus
        from application.event_system.handlers.combat_handler import CombatEventHandler
        from application.event_system.handlers.player_handler import PlayerEventHandler
        from application.event_system.handlers.system_handler import SystemEventHandler
        print("✅ Event system imported successfully")
    except ImportError as e:
        print(f"❌ Event system import failed: {e}")
    
    print("Import test completed!")

if __name__ == "__main__":
    test_imports()