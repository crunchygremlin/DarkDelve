#!/usr/bin/env python3
"""
MCP Playtest: Test inventory "D" key functionality for dropping items.

This script uses the command layer directly (DropCommand)
which is what the "D" key triggers internally in show_inventory().

Tests:
1. Drop a regular item from inventory
2. Drop an equipped item (should fail with message)
3. Drop a consumable item
4. Drop a weapon
5. Drop an armor piece
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
from src.application.game_commands.drop_command import DropCommand


@dataclass
class TestCase:
    name: str
    passed: bool = False
    error: str = ""
    details: dict = field(default_factory=dict)


def run_tests() -> List[TestCase]:
    results: List[TestCase] = []

    # ------------------------------------------------------------------
    # TEST 1: Drop a regular item from inventory
    # ------------------------------------------------------------------
    t1 = TestCase(name="Drop regular item from inventory")
    try:
        player = Player(position=Position(0, 0), name="Tester")
        item = Item(
            item_id="misc_coin",
            name="Gold Coin",
            item_type="misc",
            description="A shiny coin.",
            value=1,
            weight=0.01,
        )
        player.add_item_to_inventory("misc_coin")

        cmd = DropCommand(player=player, item=item)
        result = cmd.execute()

        t1.passed = result.success and len(player.inventory.get_items()) == 0
        t1.details = {
            "success": result.success,
            "error": result.error_message,
            "item_dropped": len(player.inventory.get_items()) == 0,
            "data": result.data,
        }
        if not t1.passed:
            t1.error = f"DropCommand failed or item not dropped: {result.error_message}"
    except Exception as e:
        t1.error = f"{e}\n{traceback.format_exc()}"
    results.append(t1)

    # ------------------------------------------------------------------
    # TEST 2: Drop an equipped item (should fail)
    # ------------------------------------------------------------------
    t2 = TestCase(name="Drop equipped item (should fail)")
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
        # Equip the sword - need to set equipped=True on item to match runtime behavior
        player.equipment.equip_item("main_hand", sword)
        sword.equipped = True  # Set equipped flag as runtime does

        cmd = DropCommand(player=player, item=sword)
        result = cmd.execute()

        # Should fail because item is equipped
        t2.passed = not result.success
        t2.details = {
            "success": result.success,
            "error": result.error_message,
            "item_still_equipped": player.equipment.get_equipped_item("main_hand") == "sword_001",
            "data": result.data,
        }
        if result.success:
            t2.error = "Equipped item should not be droppable"
    except Exception as e:
        t2.error = f"{e}\n{traceback.format_exc()}"
    results.append(t2)

    # ------------------------------------------------------------------
    # TEST 3: Drop a consumable item (potion)
    # ------------------------------------------------------------------
    t3 = TestCase(name="Drop consumable item (potion)")
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

        cmd = DropCommand(player=player, item=potion)
        result = cmd.execute()

        t3.passed = result.success and len(player.inventory.get_items()) == 0
        t3.details = {
            "success": result.success,
            "error": result.error_message,
            "item_dropped": len(player.inventory.get_items()) == 0,
            "data": result.data,
        }
        if not t3.passed:
            t3.error = f"DropCommand failed or item not dropped: {result.error_message}"
    except Exception as e:
        t3.error = f"{e}\n{traceback.format_exc()}"
    results.append(t3)

    # ------------------------------------------------------------------
    # TEST 4: Drop a weapon
    # ------------------------------------------------------------------
    t4 = TestCase(name="Drop weapon from inventory")
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

        cmd = DropCommand(player=player, item=sword)
        result = cmd.execute()

        t4.passed = result.success and len(player.inventory.get_items()) == 0
        t4.details = {
            "success": result.success,
            "error": result.error_message,
            "item_dropped": len(player.inventory.get_items()) == 0,
            "data": result.data,
        }
        if not t4.passed:
            t4.error = f"DropCommand failed or item not dropped: {result.error_message}"
    except Exception as e:
        t4.error = f"{e}\n{traceback.format_exc()}"
    results.append(t4)

    # ------------------------------------------------------------------
    # TEST 5: Drop an armor piece
    # ------------------------------------------------------------------
    t5 = TestCase(name="Drop armor from inventory")
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

        cmd = DropCommand(player=player, item=armor)
        result = cmd.execute()

        t5.passed = result.success and len(player.inventory.get_items()) == 0
        t5.details = {
            "success": result.success,
            "error": result.error_message,
            "item_dropped": len(player.inventory.get_items()) == 0,
            "data": result.data,
        }
        if not t5.passed:
            t5.error = f"DropCommand failed or item not dropped: {result.error_message}"
    except Exception as e:
        t5.error = f"{e}\n{traceback.format_exc()}"
    results.append(t5)

    return results


def main():
    print("=" * 70)
    print("MCP PLAYTEST: Inventory 'D' Key Functionality (Drop)")
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

    def _serialize_details(details):
        """Convert details dict to JSON-serializable format."""
        if not isinstance(details, dict):
            return details
        result = {}
        for k, v in details.items():
            if hasattr(v, 'to_dict'):
                result[k] = v.to_dict()
            elif hasattr(v, '__dict__'):
                # Handle Position and similar objects
                if hasattr(v, 'x') and hasattr(v, 'y'):
                    result[k] = {"x": v.x, "y": v.y}
                else:
                    result[k] = v.__dict__
            else:
                result[k] = v
        return result

    # Write structured telemetry
    telemetry = {
        "test_suite": "inventory_drop_key_mcp",
        "passed": passed,
        "failed": failed,
        "total": len(results),
        "tests": [
            {"name": t.name, "passed": t.passed, "error": t.error, "details": _serialize_details(t.details)}
            for t in results
        ],
    }
    # Also serialize the data field in details if present
    for test in telemetry["tests"]:
        if "details" in test and isinstance(test["details"], dict):
            if "data" in test["details"] and test["details"]["data"] is not None:
                test["details"]["data"] = _serialize_details(test["details"]["data"])
    out_path = "playtest/telemetry_inventory_drop_key.json"
    with open(out_path, "w") as f:
        json.dump(telemetry, f, indent=2)
    print(f"Telemetry written to {out_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())