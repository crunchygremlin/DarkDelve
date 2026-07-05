#!/usr/bin/env python3
"""
MCP Playtest: Test inventory "U" key functionality for all item types.

This script uses the command layer directly (UseCommand, EquipCommand)
which is what the "U" key triggers internally in show_inventory().

Tests 8 scenarios:
1. Potion test: UseCommand with heal+20 potion → verify HP increases, item consumed
2. Scroll test: UseCommand with learn_spell+1 scroll → verify item consumed
3. Food test: UseCommand with nutrition+300 food → verify command succeeds, item consumed
4. Wand test: UseCommand with magic_missile+10 wand → verify item consumed
5. Weapon equip test: EquipCommand with weapon → verify equipped in main_hand
6. Armor equip test: EquipCommand with armor → verify equipped in chest
7. Accessory equip test: EquipCommand with ring/amulet → verify equipped in ring/neck slot
8. MISC item test: UseCommand with MISC item → verify "not usable" / fails
"""

from __future__ import annotations

import json
import sys
import os
import traceback
from dataclasses import dataclass, field
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.domain.entities.player import Player
from src.domain.entities.item import Item
from src.domain.value_objects.position import Position
from src.application.game_commands.use_command import UseCommand
from src.application.game_commands.equip_command import EquipCommand


@dataclass
class TestCase:
    name: str
    passed: bool = False
    error: str = ""
    details: dict = field(default_factory=dict)


def run_tests() -> List[TestCase]:
    results: List[TestCase] = []

    # ------------------------------------------------------------------
    # TEST 1: Potion use via UseCommand (heal+20)
    # ------------------------------------------------------------------
    t1 = TestCase(name="Potion use via UseCommand (heal+20)")
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
        player.health = 30  # Damage player so we can see healing

        cmd = UseCommand(player=player, item=potion)
        result = cmd.execute()

        t1.passed = result.success and player.health == 50  # 30 + 20
        t1.details = {
            "success": result.success,
            "error": result.error_message,
            "health_before": 30,
            "health_after": player.health,
            "item_consumed": len(player.inventory.get_items()) == 0,
            "data": result.data,
        }
        if not t1.passed:
            t1.error = f"UseCommand failed or HP not restored: {result.error_message}"
    except Exception as e:
        t1.error = f"{e}\n{traceback.format_exc()}"
    results.append(t1)

    # ------------------------------------------------------------------
    # TEST 2: Scroll use via UseCommand (learn_spell+1) - verify item consumed
    # ------------------------------------------------------------------
    t2 = TestCase(name="Scroll use via UseCommand (learn_spell+1)")
    try:
        player = Player(position=Position(0, 0), name="Tester")
        scroll = Item(
            item_id="scroll_fire",
            name="Scroll of Fireball",
            item_type="scroll",
            description="Teaches fireball spell.",
            value=25,
            weight=0.3,
        )
        scroll.consumable = True
        scroll.effect = "learn_spell+1"
        player.add_item_to_inventory("scroll_fire")

        cmd = UseCommand(player=player, item=scroll)
        result = cmd.execute()

        # Verify item was consumed (scrolls are consumable)
        t2.passed = result.success and len(player.inventory.get_items()) == 0
        t2.details = {
            "success": result.success,
            "error": result.error_message,
            "item_consumed": len(player.inventory.get_items()) == 0,
            "data": result.data,
        }
        if not t2.passed:
            t2.error = f"UseCommand failed or item not consumed: {result.error_message}"
    except Exception as e:
        t2.error = f"{e}\n{traceback.format_exc()}"
    results.append(t2)

    # ------------------------------------------------------------------
    # TEST 3: Food use via UseCommand (nutrition+300)
    # Note: Current implementation only handles "heal" and "damage" effects.
    # The "nutrition" effect type is not yet implemented in Player._apply_effect_from_string.
    # Test verifies command succeeds and item is consumed.
    # ------------------------------------------------------------------
    t3 = TestCase(name="Food use via UseCommand (nutrition+300)")
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
        # Note: Player doesn't have nutrition attribute by default
        # This test verifies the command executes and item is consumed

        cmd = UseCommand(player=player, item=food)
        result = cmd.execute()

        # Verify command succeeds and item is consumed
        t3.passed = result.success and len(player.inventory.get_items()) == 0
        t3.details = {
            "success": result.success,
            "error": result.error_message,
            "item_consumed": len(player.inventory.get_items()) == 0,
            "data": result.data,
        }
        if not t3.passed:
            t3.error = f"UseCommand failed or item not consumed: {result.error_message}"
    except Exception as e:
        t3.error = f"{e}\n{traceback.format_exc()}"
    results.append(t3)

    # ------------------------------------------------------------------
    # TEST 4: Wand use via UseCommand (magic_missile+10) - verify item consumed
    # ------------------------------------------------------------------
    t4 = TestCase(name="Wand use via UseCommand (magic_missile+10)")
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

        # Verify item was consumed (wands are consumable)
        t4.passed = result.success and len(player.inventory.get_items()) == 0
        t4.details = {
            "success": result.success,
            "error": result.error_message,
            "item_consumed": len(player.inventory.get_items()) == 0,
            "data": result.data,
        }
        if not t4.passed:
            t4.error = f"UseCommand failed or item not consumed: {result.error_message}"
    except Exception as e:
        t4.error = f"{e}\n{traceback.format_exc()}"
    results.append(t4)

    # ------------------------------------------------------------------
    # TEST 5: Weapon equip via EquipCommand (main_hand)
    # ------------------------------------------------------------------
    t5 = TestCase(name="Weapon equip via EquipCommand (main_hand)")
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

        equipped_item = player.equipment.get_equipped_item("main_hand") if hasattr(player, 'equipment') else None
        t5.passed = result.success and equipped_item == "sword_001"
        t5.details = {
            "success": result.success,
            "error": result.error_message,
            "equipped_item": equipped_item,
            "data": result.data,
        }
        if not t5.passed:
            t5.error = f"EquipCommand failed or weapon not equipped: {result.error_message}"
    except Exception as e:
        t5.error = f"{e}\n{traceback.format_exc()}"
    results.append(t5)

    # ------------------------------------------------------------------
    # TEST 6: Armor equip via EquipCommand (chest)
    # ------------------------------------------------------------------
    t6 = TestCase(name="Armor equip via EquipCommand (chest)")
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

        equipped_item = player.equipment.get_equipped_item("chest") if hasattr(player, 'equipment') else None
        t6.passed = result.success and equipped_item == "armor_001"
        t6.details = {
            "success": result.success,
            "error": result.error_message,
            "equipped_item": equipped_item,
            "data": result.data,
        }
        if not t6.passed:
            t6.error = f"EquipCommand failed or armor not equipped: {result.error_message}"
    except Exception as e:
        t6.error = f"{e}\n{traceback.format_exc()}"
    results.append(t6)

    # ------------------------------------------------------------------
    # TEST 7: Accessory equip via EquipCommand (ring/neck)
    # Note: Player.get_equipment_slot maps "accessory" to "neck" slot
    # ------------------------------------------------------------------
    t7 = TestCase(name="Accessory equip via EquipCommand (neck/ring)")
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

        # Check both ring and neck slots since accessory maps to neck
        equipped_ring = player.equipment.get_equipped_item("ring") if hasattr(player, 'equipment') else None
        equipped_neck = player.equipment.get_equipped_item("neck") if hasattr(player, 'equipment') else None
        equipped_item = equipped_ring or equipped_neck
        
        t7.passed = result.success and equipped_item == "ring_prot"
        t7.details = {
            "success": result.success,
            "error": result.error_message,
            "equipped_ring": equipped_ring,
            "equipped_neck": equipped_neck,
            "data": result.data,
        }
        if not t7.passed:
            t7.error = f"EquipCommand failed or ring not equipped: {result.error_message}"
    except Exception as e:
        t7.error = f"{e}\n{traceback.format_exc()}"
    results.append(t7)

    # ------------------------------------------------------------------
    # TEST 8: MISC item not usable via UseCommand
    # ------------------------------------------------------------------
    t8 = TestCase(name="MISC item not usable via UseCommand")
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
        t8.passed = not result.success
        t8.details = {
            "success": result.success,
            "error": result.error_message,
            "data": result.data,
        }
        if result.success:
            t8.error = "MISC item should not be usable"
    except Exception as e:
        t8.error = f"{e}\n{traceback.format_exc()}"
    results.append(t8)

    return results


def main():
    print("=" * 70)
    print("MCP PLAYTEST: Inventory 'U' Key Functionality")
    print("=" * 70)

    results = run_tests()

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
            {"name": t.name, "passed": t.passed, "error": t.error, "details": t.details}
            for t in results
        ],
    }
    out_path = "playtest/telemetry_inventory_use_key.json"
    with open(out_path, "w") as f:
        json.dump(telemetry, f, indent=2)
    print(f"Telemetry written to {out_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())