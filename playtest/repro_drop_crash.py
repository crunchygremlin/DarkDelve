"""
Minimal reproduction script for T-2026-0630-001.

Bug: DropCommand crashes with
    AttributeError: 'Entity' object has no attribute 'get_item_count'

Root cause:
    - darkdelve.py instantiates self.player as a local @dataclass Entity
      (defined at darkdelve.py:763), NOT as src.domain.entities.player.Player.
    - That local Entity class has no get_item_count / drop_item / use_item /
      add_item / remove_effect methods.
    - DropCommand.__init__ (drop_command.py:29) calls player.get_item_count(item)
      at construction time, which immediately crashes.
    - UseCommand has the identical pattern (use_command.py:28).

This script imports the SAME local Entity class used at runtime and exercises
DropCommand against it, reproducing the exact crash without needing a live
pygame session.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the runtime-local Entity from darkdelve (the one self.player actually is)
# darkdelve.py is a top-level script (not a package), so import it by path.
# Ensure the repo root is on sys.path so `src.*` imports inside darkdelve resolve.
import importlib.util

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_DARKDELVE_PATH = os.path.join(_REPO_ROOT, "darkdelve.py")
_spec = importlib.util.spec_from_file_location("darkdelve_runtime", _DARKDELVE_PATH)
_darkdelve = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_darkdelve)

Entity = _darkdelve.Entity
Item = _darkdelve.Item
ItemType = _darkdelve.ItemType
Inventory = _darkdelve.Inventory

# Import the command under test
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from src.application.game_commands.drop_command import DropCommand
from src.application.game_commands.use_command import UseCommand


def build_runtime_player():
    """Mimic darkdelve.py:create_player at line 2330."""
    player = Entity(
        x=0, y=0,
        char="@", color=(255, 255, 255),
        name="Tester",
        blocks=True,
        hp=20, max_hp=20,
        power=5, defense=2, speed=100,
        inventory=Inventory(max_weight=100),
    )
    # Give the player an item via the runtime Inventory API
    sword = Item(
        id="sword_001",
        name="Steel Sword",
        item_type=ItemType.WEAPON,
        description="A sharp steel sword.",
        value=50,
        weight=3,
    )
    player.inventory.add_item(sword)
    return player, sword


def test_drop_command_crashes():
    player, sword = build_runtime_player()
    print(f"type(player) = {type(player).__module__}.{type(player).__qualname__}")
    print(f"has get_item_count? {hasattr(player, 'get_item_count')}")
    print(f"has drop_item?      {hasattr(player, 'drop_item')}")

    try:
        cmd = DropCommand(player=player, item=sword)
        result = cmd.execute()
        print(f"UNEXPECTED SUCCESS: {result}")
        return False
    except AttributeError as exc:
        print(f"REPRODUCED CRASH (DropCommand): {exc}")
        return True


def test_use_command_crashes():
    player, _ = build_runtime_player()
    # Use a potion (ItemType.POTION is always consumable) with a heal effect
    potion = Item(
        id="potion_heal",
        name="Health Potion",
        item_type=ItemType.POTION,
        description="Restores 20 HP.",
        value=10,
        weight=1,
        special_effect="heal",
        effect_strength=20,
    )
    player.inventory.add_item(potion)

    try:
        cmd = UseCommand(player=player, item=potion)
        result = cmd.execute()
        print(f"UNEXPECTED SUCCESS: {result}")
        return False
    except AttributeError as exc:
        print(f"REPRODUCED CRASH (UseCommand): {exc}")
        return True


if __name__ == "__main__":
    drop_ok = test_drop_command_crashes()
    use_ok = test_use_command_crashes()

    print()
    print("=" * 60)
    if drop_ok and use_ok:
        print("RESULT: Both commands crash against the runtime Entity.")
        print("CONFIRMED ROOT CAUSE: runtime Entity lacks the Player-only")
        print("  get_item_count / drop_item / use_item / add_item methods.")
        sys.exit(0)
    else:
        print("RESULT: Reproduction did not crash — investigate.")
        sys.exit(1)
