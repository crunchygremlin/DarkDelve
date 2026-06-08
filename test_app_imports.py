#!/usr/bin/env python3
"""
Test script to verify application layer imports work correctly.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_app_imports():
    """Test application layer imports."""
    print("Testing application layer imports...")
    
    # Test application imports with absolute imports
    try:
        from application.game_commands.base_command import BaseCommand, CommandResult
        print("✅ Game base commands imported successfully")
    except ImportError as e:
        print(f"❌ Game base commands import failed: {e}")
    
    try:
        from application.game_commands.move_command import MoveCommand
        print("✅ Move command imported successfully")
    except ImportError as e:
        print(f"❌ Move command import failed: {e}")
    
    try:
        from application.game_commands.attack_command import AttackCommand
        print("✅ Attack command imported successfully")
    except ImportError as e:
        print(f"❌ Attack command import failed: {e}")
    
    try:
        from application.game_commands.pickup_command import PickupCommand
        print("✅ Pickup command imported successfully")
    except ImportError as e:
        print(f"❌ Pickup command import failed: {e}")
    
    try:
        from application.game_commands.use_command import UseCommand
        print("✅ Use command imported successfully")
    except ImportError as e:
        print(f"❌ Use command import failed: {e}")
    
    try:
        from application.game_commands.equip_command import EquipCommand
        print("✅ Equip command imported successfully")
    except ImportError as e:
        print(f"❌ Equip command import failed: {e}")
    
    try:
        from application.game_commands.drop_command import DropCommand
        print("✅ Drop command imported successfully")
    except ImportError as e:
        print(f"❌ Drop command import failed: {e}")
    
    print("Application layer import test completed!")

if __name__ == "__main__":
    test_app_imports()