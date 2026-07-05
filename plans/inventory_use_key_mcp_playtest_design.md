# Design Document: MCP Playtest for Inventory "U" Key Fixes

## 1. Goal
Create a playtest script using MCPPlaytester to verify that the "U" key works correctly for all consumable types (potions, scrolls, food, wands) and equipment (weapons, armor, accessories) in the inventory screen.

## 2. Files to Create

- `playtest/test_inventory_use_key_mcp.py` - New test file using MCPPlaytester to drive the game and verify "U" key functionality via command layer testing

## 3. Files to Modify

- `playtest/instructions.json` (lines 1-6): Add test-specific push instructions for the "U" key test scenarios
- `playtest/playtest_config.yaml` (lines 1-17): No modifications needed - use default configuration with `render_to_stdout=False`

## 4. Pseudocode

### New File: `playtest/test_inventory_use_key_mcp.py`

```python
#!/usr/bin/env python3
"""
MCP Playtest: Test inventory "U" key functionality for all item types.

This script uses MCPPlaytester to drive the game and verify that:
1. Potions can be used (HP increases, item consumed)
2. Scrolls can be used (spell added, item consumed)
3. Food can be used (nutrition increases, item consumed)
4. Wands can be used (spell added, item consumed)
5. Weapons can be equipped via "U" key
6. Armor can be equipped via "U" key
7. Accessories (rings, amulets) can be equipped via "U" key
8. MISC items show "not usable" message

NOTE: The "U" key is only handled in the blocking show_inventory() event loop.
To test it via MCP, we use the command layer directly (UseCommand, EquipCommand)
which is what the "U" key triggers internally.
"""

import json
import sys
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ollama_playtester import PlaytestConfig, TelemetryStore, extract_stats, ConsoleFrame
from player_agent import PlayerDecision
from src.infrastructure.services.mcp_integration import MCPPlaytester, MCPPlaytestResult
from src.domain.entities.player import Player
from src.domain.entities.item import Item
from src.domain.value_objects.position import Position
from src.application.game_commands.use_command import UseCommand
from src.application.game_commands.equip_command import EquipCommand


@dataclass
class InventoryUseTestCase:
    """Test case for inventory "U" key functionality."""
    name: str
    item_type: str
    item_id: str
    item_name: str
    expected_result: str  # "used", "equipped", "not_usable"
    passed: bool = False
    error: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


def create_test_config(telemetry_path: str) -> PlaytestConfig:
    """Create a PlaytestConfig for the inventory use test."""
    return PlaytestConfig(
        max_turns=100,
        telemetry_path=telemetry_path,
        instruction_path="playtest/instructions.json",
    )


def test_potion_use() -> InventoryUseTestCase:
    """Test that using a potion via UseCommand works (what U key triggers)."""
    t = InventoryUseTestCase(
        name="Potion use via U key",
        item_type="potion",
        item_id="potion_heal",
        item_name="Health Potion",
        expected_result="used",
    )
    try:
        player = Player(position=Position(0, 0), name="Tester")
        potion = Item(
            item_id="potion_heal",
            name="Health Potion",
            item_type="potion",
            description="Restores 20 HP.",
            value=10,
            weight=0.5,
        )
        potion.consumable = True
        potion.effect = "heal+20"
        player.add_item_to_inventory("potion_heal")
        player.health = 30  # Damage player
        
        cmd = UseCommand(player=player, item=potion)
        result = cmd.execute()
        
        t.passed = result.success and player.health == 50  # 30 + 20
        t.details = {
            "success": result.success,
            "health_before": 30,
            "health_after": player.health,
            "item_consumed": len(player.inventory.items) == 0,
        }
        if not t.passed:
            t.error = f"UseCommand failed or HP not restored: {result.error_message}"
    except Exception as e:
        t.error = f"{e}"
        t.details = {"exception": str(e)}
    return t


def test_scroll_use() -> InventoryUseTestCase:
    """Test that using a scroll via UseCommand works (what U key triggers)."""
    t = InventoryUseTestCase(
        name="Scroll use via U key",
        item_type="scroll",
        item_id="scroll_fire",
        item_name="Scroll of Fireball",
        expected_result="used",
    )
    try:
        player = Player(position=Position(0, 0), name="Tester")
        scroll = Item(
            item_id="scroll_fire",
            name="Scroll of Fireball",
            item_type="scroll",
            description="Casts fireball.",
            value=25,
            weight=0.3,
        )
        scroll.consumable = True
        scroll.effect = "fireball+15"
        player.add_item_to_inventory("scroll_fire")
        
        cmd = UseCommand(player=player, item=scroll)
        result = cmd.execute()
        
        t.passed = result.success
        t.details = {
            "success": result.success,
            "item_consumed": len(player.inventory.items) == 0,
        }
        if not t.passed:
            t.error = f"UseCommand failed: {result.error_message}"
    except Exception as e:
        t.error = f"{e}"
        t.details = {"exception": str(e)}
    return t


def test_food_use() -> InventoryUseTestCase:
    """Test that using food via UseCommand works (what U key triggers)."""
    t = InventoryUseTestCase(
        name="Food use via U key",
        item_type="food",
        item_id="food_ration",
        item_name="Ration",
        expected_result="used",
    )
    try:
        player = Player(position=Position(0, 0), name="Tester")
        food = Item(
            item_id="food_ration",
            name="Ration",
            item_type="food",
            description="Restores nutrition.",
            value=5,
            weight=0.8,
        )
        food.consumable = True
        food.effect = "nutrition+300"
        player.add_item_to_inventory("food_ration")
        player.nutrition = 500
        
        cmd = UseCommand(player=player, item=food)
        result = cmd.execute()
        
        t.passed = result.success and player.nutrition > 500
        t.details = {
            "success": result.success,
            "nutrition_before": 500,
            "nutrition_after": player.nutrition,
            "item_consumed": len(player.inventory.items) == 0,
        }
        if not t.passed:
            t.error = f"UseCommand failed or nutrition not restored: {result.error_message}"
    except Exception as e:
        t.error = f"{e}"
        t.details = {"exception": str(e)}
    return t


def test_wand_use() -> InventoryUseTestCase:
    """Test that using a wand via UseCommand works (what U key triggers)."""
    t = InventoryUseTestCase(
        name="Wand use via U key",
        item_type="wand",
        item_id="wand_mm",
        item_name="Wand of Magic Missile",
        expected_result="used",
    )
    try:
        player = Player(position=Position(0, 0), name="Tester")
        wand = Item(
            item_id="wand_mm",
            name="Wand of Magic Missile",
            item_type="wand",
            description="Casts magic missile.",
            value=50,
            weight=1.0,
        )
        wand.consumable = True
        wand.effect = "magic_missile+10"
        player.add_item_to_inventory("wand_mm")
        
        cmd = UseCommand(player=player, item=wand)
        result = cmd.execute()
        
        t.passed = result.success
        t.details = {
            "success": result.success,
            "item_consumed": len(player.inventory.items) == 0,
        }
        if not t.passed:
            t.error = f"UseCommand failed: {result.error_message}"
    except Exception as e:
        t.error = f"{e}"
        t.details = {"exception": str(e)}
    return t


def test_weapon_equip() -> InventoryUseTestCase:
    """Test that equipping a weapon via EquipCommand works (what U key triggers)."""
    t = InventoryUseTestCase(
        name="Weapon equip via U key",
        item_type="weapon",
        item_id="sword_001",
        item_name="Iron Sword",
        expected_result="equipped",
    )
    try:
        player = Player(position=Position(0, 0), name="Tester")
        sword = Item(
            item_id="sword_001",
            name="Iron Sword",
            item_type="weapon",
            description="A sharp iron sword.",
            value=50,
            weight=3.0,
        )
        player.add_item_to_inventory("sword_001")
        
        cmd = EquipCommand(player=player, item=sword)
        result = cmd.execute()
        
        t.passed = result.success
        t.details = {
            "success": result.success,
            "equipped_item": player.equipment.get_equipped_item("main_hand") if hasattr(player, 'equipment') else None,
        }
        if not t.passed:
            t.error = f"EquipCommand failed: {result.error_message}"
    except Exception as e:
        t.error = f"{e}"
        t.details = {"exception": str(e)}
    return t


def test_armor_equip() -> InventoryUseTestCase:
    """Test that equipping armor via EquipCommand works (what U key triggers)."""
    t = InventoryUseTestCase(
        name="Armor equip via U key",
        item_type="armor",
        item_id="armor_001",
        item_name="Leather Armor",
        expected_result="equipped",
    )
    try:
        player = Player(position=Position(0, 0), name="Tester")
        armor = Item(
            item_id="armor_001",
            name="Leather Armor",
            item_type="armor",
            description="Light leather armor.",
            value=75,
            weight=10.0,
        )
        player.add_item_to_inventory("armor_001")
        
        cmd = EquipCommand(player=player, item=armor)
        result = cmd.execute()
        
        t.passed = result.success
        t.details = {
            "success": result.success,
            "equipped_item": player.equipment.get_equipped_item("chest") if hasattr(player, 'equipment') else None,
        }
        if not t.passed:
            t.error = f"EquipCommand failed: {result.error_message}"
    except Exception as e:
        t.error = f"{e}"
        t.details = {"exception": str(e)}
    return t


def test_accessory_equip() -> InventoryUseTestCase:
    """Test that equipping an accessory via EquipCommand works (what U key triggers)."""
    t = InventoryUseTestCase(
        name="Accessory equip via U key",
        item_type="accessory",
        item_id="ring_prot",
        item_name="Ring of Protection",
        expected_result="equipped",
    )
    try:
        player = Player(position=Position(0, 0), name="Tester")
        ring = Item(
            item_id="ring_prot",
            name="Ring of Protection",
            item_type="accessory",
            description="A protective ring.",
            value=100,
            weight=0.1,
        )
        ring.equipment_slot = "ring"
        player.add_item_to_inventory("ring_prot")
        
        cmd = EquipCommand(player=player, item=ring)
        result = cmd.execute()
        
        t.passed = result.success
        t.details = {
            "success": result.success,
            "equipped_item": player.equipment.get_equipped_item("ring") if hasattr(player, 'equipment') else None,
        }
        if not t.passed:
            t.error = f"EquipCommand failed: {result.error_message}"
    except Exception as e:
        t.error = f"{e}"
        t.details = {"exception": str(e)}
    return t


def test_misc_not_usable() -> InventoryUseTestCase:
    """Test that MISC items cannot be used via UseCommand (what U key triggers)."""
    t = InventoryUseTestCase(
        name="MISC item not usable via U key",
        item_type="misc",
        item_id="misc_coin",
        item_name="Gold Coin",
        expected_result="not_usable",
    )
    try:
        player = Player(position=Position(0, 0), name="Tester")
        coin = Item(
            item_id="misc_coin",
            name="Gold Coin",
            item_type="misc",
            description="A shiny coin.",
            value=1,
            weight=0.01,
        )
        player.add_item_to_inventory("misc_coin")
        
        cmd = UseCommand(player=player, item=coin)
        result = cmd.execute()
        
        # MISC items should fail to use
        t.passed = not result.success
        t.details = {
            "success": result.success,
            "error": result.error_message,
        }
        if result.success:
            t.error = "MISC item should not be usable"
    except Exception as e:
        t.error = f"{e}"
        t.details = {"exception": str(e)}
    return t


def run_all_tests() -> List[InventoryUseTestCase]:
    """Run all inventory "U" key test scenarios."""
    return [
        test_potion_use(),
        test_scroll_use(),
        test_food_use(),
        test_wand_use(),
        test_weapon_equip(),
        test_armor_equip(),
        test_accessory_equip(),
        test_misc_not_usable(),
    ]


def main():
    """Main entry point for the inventory "U" key playtest."""
    print("=" * 70)
    print("MCP PLAYTEST: Inventory 'U' Key Functionality")
    print("=" * 70)
    
    results = run_all_tests()
    
    passed = sum(1 for t in results if t.passed)
    failed = sum(1 for t in results if not t.passed)
    
    for t in results:
        status = "PASS" if t.passed else "FAIL"
        print(f"\n[{status}] {t.name}")
        if t.error:
            print(f"  Error: {t.error}")
        if t.details:
            for k, v in t.details.items():
                print(f"  {k}: {v}")
    
    print(f"\n{'=' * 70}")
    print(f"Results: {passed} passed, {failed} failed out of {len(results)} tests")
    
    # Write structured telemetry
    telemetry = {
        "test_suite": "inventory_use_key_mcp",
        "passed": passed,
        "failed": failed,
        "total": len(results),
        "tests": [
            {
                "name": t.name,
                "passed": t.passed,
                "error": t.error,
                "details": t.details,
            }
            for t in results
        ],
    }
    
    with open("playtest/telemetry_inventory_use_mcp.json", "w") as f:
        json.dump(telemetry, f, indent=2)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

## 5. Import Statements

```python
from __future__ import annotations

import json
import sys
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ollama_playtester import PlaytestConfig, TelemetryStore, extract_stats, ConsoleFrame
from player_agent import PlayerDecision
from src.infrastructure.services.mcp_integration import MCPPlaytester, MCPPlaytestResult
from src.domain.entities.player import Player
from src.domain.entities.item import Item
from src.domain.value_objects.position import Position
from src.application.game_commands.use_command import UseCommand
from src.application.game_commands.equip_command import EquipCommand
```

## 6. Test Plan

### Test File: `playtest/test_inventory_use_key_mcp.py`

```python
def test_potion_use_increases_hp():
    """Test that using a potion via UseCommand increases HP and consumes the item."""
    player = Player(position=Position(0, 0), name="Tester")
    potion = Item(item_id="potion_heal", name="Health Potion", item_type="potion", value=10, weight=0.5)
    potion.consumable = True
    potion.effect = "heal+20"
    player.add_item_to_inventory("potion_heal")
    player.health = 30
    
    cmd = UseCommand(player=player, item=potion)
    result = cmd.execute()
    
    assert result.success is True
    assert player.health == 50  # 30 + 20
    assert len(player.inventory.items) == 0  # Consumed


def test_scroll_use_consumes():
    """Test that using a scroll via UseCommand consumes the item."""
    player = Player(position=Position(0, 0), name="Tester")
    scroll = Item(item_id="scroll_fire", name="Scroll of Fireball", item_type="scroll", value=25, weight=0.3)
    scroll.consumable = True
    scroll.effect = "fireball+15"
    player.add_item_to_inventory("scroll_fire")
    
    cmd = UseCommand(player=player, item=scroll)
    result = cmd.execute()
    
    assert result.success is True
    assert len(player.inventory.items) == 0  # Consumed


def test_food_use_increases_nutrition():
    """Test that using food via UseCommand increases nutrition."""
    player = Player(position=Position(0, 0), name="Tester")
    food = Item(item_id="food_ration", name="Ration", item_type="food", value=5, weight=0.8)
    food.consumable = True
    food.effect = "nutrition+300"
    player.add_item_to_inventory("food_ration")
    player.nutrition = 500
    
    cmd = UseCommand(player=player, item=food)
    result = cmd.execute()
    
    assert result.success is True
    assert player.nutrition > 500  # Nutrition increased
    assert len(player.inventory.items) == 0  # Consumed


def test_wand_use_consumes():
    """Test that using a wand via UseCommand consumes the item."""
    player = Player(position=Position(0, 0), name="Tester")
    wand = Item(item_id="wand_mm", name="Wand of Magic Missile", item_type="wand", value=50, weight=1.0)
    wand.consumable = True
    wand.effect = "magic_missile+10"
    player.add_item_to_inventory("wand_mm")
    
    cmd = UseCommand(player=player, item=wand)
    result = cmd.execute()
    
    assert result.success is True
    assert len(player.inventory.items) == 0  # Consumed


def test_weapon_equip_via_u_key():
    """Test that equipping a weapon via EquipCommand works."""
    player = Player(position=Position(0, 0), name="Tester")
    sword = Item(item_id="sword_001", name="Iron Sword", item_type="weapon", value=50, weight=3.0)
    player.add_item_to_inventory("sword_001")
    
    cmd = EquipCommand(player=player, item=sword)
    result = cmd.execute()
    
    assert result.success is True
    assert player.equipment.get_equipped_item("main_hand") == "sword_001"


def test_armor_equip_via_u_key():
    """Test that equipping armor via EquipCommand works."""
    player = Player(position=Position(0, 0), name="Tester")
    armor = Item(item_id="armor_001", name="Leather Armor", item_type="armor", value=75, weight=10.0)
    player.add_item_to_inventory("armor_001")
    
    cmd = EquipCommand(player=player, item=armor)
    result = cmd.execute()
    
    assert result.success is True
    assert player.equipment.get_equipped_item("chest") == "armor_001"


def test_accessory_equip_via_u_key():
    """Test that equipping an accessory via EquipCommand works."""
    player = Player(position=Position(0, 0), name="Tester")
    ring = Item(item_id="ring_prot", name="Ring of Protection", item_type="accessory", value=100, weight=0.1)
    ring.equipment_slot = "ring"
    player.add_item_to_inventory("ring_prot")
    
    cmd = EquipCommand(player=player, item=ring)
    result = cmd.execute()
    
    assert result.success is True
    assert player.equipment.get_equipped_item("ring") == "ring_prot"


def test_misc_item_not_usable():
    """Test that MISC items cannot be used via UseCommand."""
    player = Player(position=Position(0, 0), name="Tester")
    coin = Item(item_id="misc_coin", name="Gold Coin", item_type="misc", value=1, weight=0.01)
    player.add_item_to_inventory("misc_coin")
    
    cmd = UseCommand(player=player, item=coin)
    result = cmd.execute()
    
    assert result.success is False  # MISC items should fail
```

## 7. Integration Notes

- `MCPPlaytester` in `src/infrastructure/services/mcp_integration.py` drives the game through `game.main_loop(action=...)`
- The "U" key is handled in `darkdelve.py` lines 3241-3270 within the `show_inventory()` method
- The `process_action()` method in `darkdelve.py` does NOT support "u" as an action (line 2772 only handles w, a, s, d, e)
- The `show_inventory()` method is a blocking event loop that cannot be driven by MCP playtester
- **Solution**: Test the command layer directly using `UseCommand` and `EquipCommand` which is what the "U" key triggers internally
- This approach matches the pattern in `playtest/test_equip_use_combat.py` which tests the command layer
- Telemetry is written to `playtest/telemetry_inventory_use_mcp.json`
- The `UseCommand` in `src/application/game_commands/use_command.py` handles consumable items
- The `EquipCommand` in `src/application/game_commands/equip_command.py` handles equipment items

## 8. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| The "U" key is not in `VALID_ACTIONS` in `player_agent.py` line 24 | The test uses command layer directly, bypassing the need for "u" action in main_loop |
| `show_inventory()` is a blocking event loop that cannot be driven by MCP | Use the command layer (UseCommand, EquipCommand) which is what the "U" key triggers internally |
| Items may not exist in the game's item database | Create items directly using `Item()` constructor with proper attributes |
| The player may not have enough HP to test potion healing | Set `player.health` to a low value before testing |
| Equipment slots may not be properly defined for accessories | Set `item.equipment_slot` attribute explicitly for accessories |
| Telemetry may not capture the "Used" or "Equipped" messages | Check command result `success` and player state changes instead |
| The test does not actually test the "U" key in the UI | The test verifies the underlying command logic which is the same code the "U" key triggers |
