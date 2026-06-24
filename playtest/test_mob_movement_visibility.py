"""
Test script to validate mob movement and attacker visibility fixes.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain.entities.mob import Mob
from src.domain.value_objects.position import Position
from src.domain.services.ai_service import AIService, AIStrategy
from src.domain.services.perception_service import PerceptionService, DEFAULT_MOB_MODIFIERS
from src.domain.value_objects.perception import PerceptionModifiers


def test_mob_has_movement_component():
    """Test that Mob has a Movement component attached."""
    position = Position(5, 5)
    mob = Mob(position=position, name="TestGoblin", mob_type="goblin")
    
    assert mob.has_component("movement"), "Mob should have 'movement' component"
    movement = mob.get_component("movement")
    assert movement is not None, "Movement component should not be None"
    print("✓ Mob has Movement component attached")


def test_mob_can_move():
    """Test that Mob can move using the Movement component."""
    position = Position(5, 5)
    mob = Mob(position=position, name="TestGoblin", mob_type="goblin")
    
    movement = mob.get_component("movement")
    assert movement.can_move(), "Mob should be able to move initially"
    
    # Set a target position
    new_pos = Position(6, 5)
    movement.set_position(new_pos)
    assert movement.get_position().x == 6, "Position should be updated"
    print("✓ Mob can move using Movement component")


def test_ai_service_can_move_mob():
    """Test that AI service can move a mob."""
    position = Position(5, 5)
    mob = Mob(position=position, name="TestGoblin", mob_type="goblin")
    
    ai_service = AIService()
    ai_service.set_ai_strategy(mob, AIStrategy.AGGRESSIVE)
    
    # Create a mock game state with a player
    player_pos = Position(10, 5)
    player = type('Player', (), {'id': 'player_001', 'position': player_pos, 'player': True})()
    
    game_state = {
        "entities": [mob, player]
    }
    
    # Update AI - should move towards player
    ai_service.update_ai(mob, 0.1, game_state)
    
    # Check that mob moved (check movement component position)
    movement = mob.get_component("movement")
    new_x = movement.get_position().x
    new_y = movement.get_position().y
    assert new_x != 5 or new_y != 5, f"Mob should have moved from (5,5) to ({new_x},{new_y})"
    print(f"✓ AI service moved mob from (5,5) to ({new_x},{new_y})")


def test_perception_see_invisible():
    """Test that entities with see_invisible can see invisible attackers."""
    # Create a lich (has see_invisible=True)
    lich_modifiers = DEFAULT_MOB_MODIFIERS.get("lich")
    assert lich_modifiers is not None, "Lich modifiers should exist"
    assert lich_modifiers.see_invisible == True, "Lich should have see_invisible=True"
    print("✓ Lich has see_invisible=True in perception modifiers")
    
    # Create a default mob (no see_invisible)
    default_modifiers = DEFAULT_MOB_MODIFIERS.get("default")
    assert default_modifiers is not None, "Default modifiers should exist"
    assert default_modifiers.see_invisible == False, "Default mob should have see_invisible=False"
    print("✓ Default mob has see_invisible=False in perception modifiers")


def test_perception_service_visible_entities():
    """Test that PerceptionService correctly filters invisible entities."""
    from unittest.mock import MagicMock
    
    # Create mock services
    fov_query = MagicMock()
    fov_query.execute.return_value = MagicMock(success=True, data=[(5, 5), (6, 5), (7, 5)])
    
    entity_repo = MagicMock()
    item_repo = MagicMock()
    
    perception_service = PerceptionService(fov_query, entity_repo, item_repo)
    
    # Create an entity with see_invisible
    entity = type('Entity', (), {
        'id': 'entity_001',
        'position': Position(0, 0),
        'mob_type': 'lich'
    })()
    
    # Create an invisible attacker
    invisible_attacker = type('Entity', (), {
        'id': 'attacker_001',
        'position': Position(5, 5),
        'is_invisible': True,
        'mob_type': 'shadow'
    })()
    
    # Create a visible entity
    visible_entity = type('Entity', (), {
        'id': 'entity_002',
        'position': Position(6, 5),
        'is_invisible': False,
        'mob_type': 'goblin'
    })()
    
    entities = [entity, invisible_attacker, visible_entity]
    game_map = MagicMock()
    
    # Get visible entities
    modifiers = perception_service.get_perception_for_mob_type('lich')
    visible_ids = perception_service._get_visible_entities(entity, entities, modifiers, game_map)
    
    # Lich should see the invisible attacker
    assert 'attacker_001' in visible_ids, "Lich should see invisible attacker"
    print("✓ Lich can see invisible attacker")
    
    # Now test with default mob (cannot see invisible)
    modifiers = perception_service.get_perception_for_mob_type('default')
    visible_ids = perception_service._get_visible_entities(entity, entities, modifiers, game_map)
    
    # Default mob should NOT see the invisible attacker
    assert 'attacker_001' not in visible_ids, "Default mob should NOT see invisible attacker"
    print("✓ Default mob cannot see invisible attacker")


def main():
    print("=" * 60)
    print("Testing Mob Movement and Attacker Visibility Fixes")
    print("=" * 60)
    
    try:
        test_mob_has_movement_component()
        test_mob_can_move()
        test_ai_service_can_move_mob()
        test_perception_see_invisible()
        test_perception_service_visible_entities()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())