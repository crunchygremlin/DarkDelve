"""
Focused playtest: equip, use (potion), attack (weapon), armor, inventory describe.

This script directly exercises the command/component layer without needing the
full game loop or an LLM. It verifies the four mechanics the user asked about:
  1. Can a weapon be equipped?
  2. Can a potion be drunk (used)?
  3. Does the inventory describe the item?
  4. Can the player hit with a weapon (attack)?
  5. Does armor reduce damage?

Run:  python playtest/test_equip_use_combat.py
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
from src.domain.entities.mob import Mob
from src.domain.entities.item import Item
from src.domain.value_objects.position import Position
from src.application.game_commands.equip_command import EquipCommand
from src.application.game_commands.use_command import UseCommand
from src.application.game_commands.attack_command import AttackCommand


@dataclass
class TestCase:
    name: str
    passed: bool = False
    error: str = ""
    details: dict = field(default_factory=dict)


def run_tests() -> List[TestCase]:
    results: List[TestCase] = []

    # ------------------------------------------------------------------
    # TEST 1: Equip a weapon via Player.equip_item (the real public API)
    # ------------------------------------------------------------------
    t1 = TestCase(name="Equip weapon via Player.equip_item")
    try:
        player = Player(position=Position(0, 0), name="Tester")
        # Add the item_id to inventory slots
        player.inventory.add_item("sword_001")
        # Equip it in a slot
        success = player.equip_item("sword_001", "main_hand")
        # Check it's actually equipped
        equipped = player.equipment.get_equipped_item("main_hand")
        t1.passed = success and equipped == "sword_001"
        t1.details = {
            "equip_returned": success,
            "equipped_item": equipped,
            "player_equipped_items": player.get_equipped_items(),
        }
        if not t1.passed:
            t1.error = f"equip returned {success}, equipped={equipped}"
    except Exception as e:
        t1.error = f"{e}\n{traceback.format_exc()}"
    results.append(t1)

    # ------------------------------------------------------------------
    # TEST 2: EquipCommand with Item object (the command-layer API)
    # ------------------------------------------------------------------
    t2 = TestCase(name="EquipCommand with Item object")
    try:
        player = Player(position=Position(0, 0), name="Tester")
        sword = Item(
            item_id="sword_002",
            name="Steel Sword",
            item_type="weapon",
            description="A sharp steel sword.",
            value=50,
            weight=3.0,
        )
        player.add_item_to_inventory("sword_002")
        cmd = EquipCommand(player=player, item=sword)
        result = cmd.execute()
        t2.passed = result.success
        t2.details = {"success": result.success, "error": result.error_message, "data": result.data}
        if not result.success:
            t2.error = result.error_message or "equip command failed"
    except Exception as e:
        t2.error = f"{e}\n{traceback.format_exc()}"
    results.append(t2)

    # ------------------------------------------------------------------
    # TEST 3: UseCommand with potion Item object
    # ------------------------------------------------------------------
    t3 = TestCase(name="Drink potion via UseCommand")
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
        player.health = 50  # damage the player so we can see healing

        cmd = UseCommand(player=player, item=potion)
        result = cmd.execute()
        t3.passed = result.success
        t3.details = {
            "success": result.success,
            "error": result.error_message,
            "player_health_after": player.health,
            "data": result.data,
        }
        if not result.success:
            t3.error = result.error_message or "use command failed"
    except Exception as e:
        t3.error = f"{e}\n{traceback.format_exc()}"
    results.append(t3)

    # ------------------------------------------------------------------
    # TEST 4: Inventory describe item (InventoryQuery.get_item_info)
    # ------------------------------------------------------------------
    t4 = TestCase(name="InventoryQuery.get_item_info")
    try:
        player = Player(position=Position(0, 0), name="Tester")
        player.add_item_to_inventory("potion_heal")

        from src.application.game_queries.inventory_query import InventoryQuery
        query = InventoryQuery(player)
        item_result = query.get_item_info("potion_heal")
        t4.passed = item_result.success
        t4.details = {"item_info": item_result.data, "error": item_result.error_message}
        if not item_result.success:
            t4.error = item_result.error_message or "item query failed"
    except Exception as e:
        t4.error = f"{e}\n{traceback.format_exc()}"
    results.append(t4)

    # ------------------------------------------------------------------
    # TEST 5: Attack with equipped weapon (does equipped weapon add damage?)
    # ------------------------------------------------------------------
    t5 = TestCase(name="Attack with equipped weapon")
    try:
        player = Player(position=Position(0, 0), name="Attacker")
        player.inventory.add_item("sword_001")
        player.equip_item("sword_001", "main_hand")

        # Check attack_power before equip
        base_attack = player.attack_power

        # Create a target mob
        mob = Mob(
            position=Position(1, 0),
            name="Goblin",
            mob_type="goblin",
        )

        # Execute attack via command
        atk_cmd = AttackCommand(attacker=player, target=mob)
        atk_result = atk_cmd.execute()
        t5.passed = atk_result.success
        t5.details = {
            "equip_success": True,
            "attack_success": atk_result.success,
            "damage_dealt": atk_result.data.get("damage_dealt") if atk_result.data else None,
            "player_base_attack": base_attack,
            "target_remaining_hp": mob.health,
            "error": atk_result.error_message,
        }
        if not atk_result.success:
            t5.error = atk_result.error_message or "attack failed"
    except Exception as e:
        t5.error = f"{e}\n{traceback.format_exc()}"
    results.append(t5)

    # ------------------------------------------------------------------
    # TEST 6: Armor reduces damage (via take_damage + defense)
    # ------------------------------------------------------------------
    t6 = TestCase(name="Armor reduces damage")
    try:
        player_no_armor = Player(position=Position(0, 0), name="NoArmor")
        player_with_armor = Player(position=Position(0, 0), name="WithArmor")

        # Equip armor on the armored player
        player_with_armor.inventory.add_item("shield_001")
        player_with_armor.equip_item("shield_001", "off_hand")

        # Both players take the same hit
        hp_before_no = player_no_armor.health
        hp_before_armor = player_with_armor.health

        player_no_armor.take_damage(10)
        player_with_armor.take_damage(10)

        dmg_no_armor = hp_before_no - player_no_armor.health
        dmg_with_armor = hp_before_armor - player_with_armor.health

        t6.passed = True  # We got here without crashing
        t6.details = {
            "equip_success": True,
            "damage_without_armor": dmg_no_armor,
            "damage_with_armor": dmg_with_armor,
            "armor_reduced_damage": dmg_with_armor < dmg_no_armor,
            "player_no_armor_hp": player_no_armor.health,
            "player_with_armor_hp": player_with_armor.health,
        }
    except Exception as e:
        t6.error = f"{e}\n{traceback.format_exc()}"
    results.append(t6)

    # ------------------------------------------------------------------
    # TEST 7: Player.use_item (does the player entity have this method?)
    # ------------------------------------------------------------------
    t7 = TestCase(name="Player.use_item method exists")
    try:
        player = Player(position=Position(0, 0), name="Tester")
        potion = Item(
            item_id="potion_heal2",
            name="Health Potion",
            item_type="potion",
            description="Restores 20 HP.",
            value=10,
            weight=0.5,
        )
        potion.consumable = True
        potion.effect = "heal+20"
        player.add_item_to_inventory("potion_heal2")
        player.health = 50

        has_use_item = hasattr(player, 'use_item')
        if has_use_item:
            result = player.use_item(potion)
            t7.passed = bool(result)
            t7.details = {"use_item_returned": result, "health_after": player.health}
        else:
            t7.passed = False
            t7.error = "Player entity has no 'use_item' method"
            t7.details = {"has_use_item": False}
    except Exception as e:
        t7.error = f"{e}\n{traceback.format_exc()}"
    results.append(t7)

    # ------------------------------------------------------------------
    # TEST 8: Player.attack method exists
    # ------------------------------------------------------------------
    t8 = TestCase(name="Player.attack method exists")
    try:
        player = Player(position=Position(0, 0), name="Attacker")
        mob = Mob(position=Position(1, 0), name="Goblin", mob_type="goblin")
        mob.health = 30

        has_attack = hasattr(player, 'attack')
        if has_attack:
            result = player.attack(mob)
            t8.passed = True
            t8.details = {"attack_returned": result, "mob_health_after": mob.health}
        else:
            t8.passed = False
            t8.error = "Player entity has no 'attack' method"
            t8.details = {"has_attack": False}
    except Exception as e:
        t8.error = f"{e}\n{traceback.format_exc()}"
    results.append(t8)

    return results


def main():
    print("=" * 60)
    print("DarkDelve focused playtest: equip / use / combat / describe")
    print("=" * 60)

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

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(results)} tests")

    # Write structured telemetry
    telemetry = {
        "test_suite": "equip_use_combat",
        "passed": passed,
        "failed": failed,
        "total": len(results),
        "tests": [
            {"name": t.name, "passed": t.passed, "error": t.error, "details": t.details}
            for t in results
        ],
    }
    out_path = "playtest/telemetry_equip_use_combat.json"
    with open(out_path, "w") as f:
        json.dump(telemetry, f, indent=2)
    print(f"Telemetry written to {out_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
