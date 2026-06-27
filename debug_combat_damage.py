#!/usr/bin/env python3
"""
Debug script to verify the full player combat loop.
Tests: player creation, weapon equip, monster spawn, attack resolution, damage application.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from darkdelve import (
    Game, Entity, CombatResolver, CombatEvent, HitResult, COLORS,
    Item, Inventory, ItemType, EquipmentSlot
)


def test_player_creation():
    """Test that player is created with expected stats."""
    print("=" * 60)
    print("TEST 1: Player Creation")
    print("=" * 60)

    game = Game()
    game.initialize()

    player = game.player
    print(f"  Player name: {player.name}")
    print(f"  Player HP: {player.hp}/{player.max_hp}")
    print(f"  Player power: {player.power}")
    print(f"  Player defense: {player.defense}")
    print(f"  Player speed: {player.speed}")
    print(f"  Player to_hit_bonus: {player.to_hit_bonus}")
    print(f"  Player damage_bonus: {player.damage_bonus}")
    print(f"  Player armor_class: {player.armor_class}")

    # Check inventory
    if player.inventory:
        items = player.inventory.items
        print(f"  Inventory items ({len(items)}):")
        for item in items:
            eq_status = " [EQUIPPED]" if item.equipped else ""
            print(f"    - {item.name} ({item.id}){eq_status} dmg_bonus={item.damage_bonus}")
    else:
        print("  Inventory: None")

    # Check equipped slots
    if player.inventory:
        print(f"  Equipped slots:")
        for slot, item in player.inventory.equipment.items():
            if item:
                print(f"    {slot}: {item.name} (dmg_bonus={item.damage_bonus})")
            else:
                print(f"    {slot}: empty")

    return game


def test_weapon_equip():
    """Test equipping a weapon and checking damage_bonus."""
    print("\n" + "=" * 60)
    print("TEST 2: Weapon Equip")
    print("=" * 60)

    game = Game()
    game.initialize()

    player = game.player

    # Create a weapon
    sword = Item(
        id="iron_sword",
        name="Iron Sword",
        description="A sharp iron sword",
        symbol="/",
        item_type=ItemType.WEAPON,
        weight=5,
        value=100,
        damage_bonus=5,
        to_hit_bonus=2,
        equipped_slot=EquipmentSlot.MAIN_HAND
    )

    print(f"  Before equip - damage_bonus: {player.damage_bonus}, to_hit_bonus: {player.to_hit_bonus}")

    # Add and equip
    player.inventory.add_item(sword)
    slots = player.inventory._get_valid_slots_for_item(sword)
    print(f"  Valid slots for sword: {slots}")
    if slots:
        player.inventory.equip(sword.id, slots[0])
        print(f"  Equipped sword in slot: {slots[0]}")

    print(f"  After equip - damage_bonus: {player.damage_bonus}, to_hit_bonus: {player.to_hit_bonus}")

    return game


def test_combat_resolver():
    """Direct combat resolver test with various scenarios."""
    print("\n" + "=" * 60)
    print("TEST 3: CombatResolver Direct Test (unarmed)")
    print("=" * 60)

    # Create player WITHOUT weapon
    player = Entity(
        x=0, y=0, char="@", color=(255, 255, 0),
        name="Player", blocks=True,
        hp=20, max_hp=20, power=5, defense=2, speed=100,
        inventory=Inventory(max_weight=100)
    )

    # Create a weak monster
    monster = Entity(
        x=1, y=0, char="g", color=(100, 200, 100),
        name="Goblin", blocks=True,
        hp=10, max_hp=10, power=2, defense=1, speed=100,
        inventory=Inventory(max_weight=100)
    )

    print(f"  Player: power={player.power}, damage_bonus={player.damage_bonus}, to_hit_bonus={player.to_hit_bonus}")
    print(f"  Monster: hp={monster.hp}/{monster.max_hp}, armor_class={monster.armor_class}")

    # Simulate 20 attacks
    hits = 0
    total_damage = 0
    for i in range(20):
        event = CombatResolver.resolve_attack(player, monster)
        if event.result in (HitResult.HIT, HitResult.CRITICAL):
            hits += 1
            total_damage += event.damage
            print(f"    Attack {i+1}: {event.result.name} - Damage: {event.damage} - Monster HP: {monster.hp}/{monster.max_hp}")
            monster.hp -= event.damage
            if monster.hp <= 0:
                print(f"    ** Monster DIED on attack {i+1}! **")
                break
        else:
            print(f"    Attack {i+1}: {event.result.name}")

    if monster.hp > 0:
        print(f"  Summary: {hits} hits, {total_damage} total damage, monster survived with {monster.hp} HP")
    else:
        print(f"  Summary: {hits} hits, {total_damage} total damage, monster KILLED")


def test_full_game_attack():
    """Test full Game.attack() loop with weapon."""
    print("\n" + "=" * 60)
    print("TEST 4: Full Game.attack() Loop (with weapon)")
    print("=" * 60)

    game = Game()
    game.initialize()

    player = game.player

    # Equip a weapon
    sword = Item(
        id="iron_sword",
        name="Iron Sword",
        description="A sharp iron sword",
        symbol="/",
        item_type=ItemType.WEAPON,
        weight=5,
        value=100,
        damage_bonus=5,
        to_hit_bonus=2,
        equipped_slot=EquipmentSlot.MAIN_HAND
    )
    player.inventory.add_item(sword)
    slots = player.inventory._get_valid_slots_for_item(sword)
    if slots:
        player.inventory.equip(sword.id, slots[0])

    # Create adjacent monster
    monster = Entity(
        x=player.x + 1, y=player.y, char="g", color=(100, 200, 100),
        name="Goblin", blocks=True,
        hp=10, max_hp=10, power=2, defense=1, speed=100,
        inventory=Inventory(max_weight=100)
    )

    print(f"  Player: power={player.power}, damage_bonus={player.damage_bonus}, to_hit_bonus={player.to_hit_bonus}")
    print(f"  Monster: hp={monster.hp}/{monster.max_hp}, armor_class={monster.armor_class}")

    # Attack 10 times
    for i in range(10):
        initial_hp = monster.hp
        game.attack(player, monster)
        damage_dealt = initial_hp - monster.hp
        print(f"    Attack {i+1}: Monster HP {initial_hp} -> {monster.hp} (damage: {damage_dealt})")
        if monster.hp <= 0:
            print(f"    ** Monster DIED on attack {i+1}! **")
            break


def test_no_weapon_vs_with_weapon():
    """Compare damage output with and without weapon."""
    print("\n" + "=" * 60)
    print("TEST 5: No Weapon vs With Weapon Comparison")
    print("=" * 60)

    # Without weapon
    player_no_wpn = Entity(
        x=0, y=0, char="@", color=(255, 255, 0),
        name="Player", blocks=True,
        hp=20, max_hp=20, power=5, defense=2, speed=100,
        inventory=Inventory(max_weight=100)
    )

    # With weapon
    player_wpn = Entity(
        x=0, y=0, char="@", color=(255, 255, 0),
        name="Player", blocks=True,
        hp=20, max_hp=20, power=5, defense=2, speed=100,
        inventory=Inventory(max_weight=100)
    )
    sword = Item(
        id="iron_sword", name="Iron Sword", description="Sword", symbol="/",
        item_type=ItemType.WEAPON, weight=5, value=100,
        damage_bonus=5, to_hit_bonus=2, equipped_slot=EquipmentSlot.MAIN_HAND
    )
    player_wpn.inventory.add_item(sword)
    slots = player_wpn.inventory._get_valid_slots_for_item(sword)
    if slots:
        player_wpn.inventory.equip(sword.id, slots[0])

    monster_template = dict(
        x=1, y=0, char="g", color=(100, 200, 100),
        name="Goblin", blocks=True,
        hp=10, max_hp=10, power=2, defense=1, speed=100,
        inventory=Inventory(max_weight=100)
    )

    for label, player in [("NO WEAPON", player_no_wpn), ("WITH WEAPON (+5 dmg)", player_wpn)]:
        monster = Entity(**monster_template)
        hits = 0
        total_dmg = 0
        attacks_to_kill = 0
        for i in range(50):
            event = CombatResolver.resolve_attack(player, monster)
            if event.result in (HitResult.HIT, HitResult.CRITICAL):
                hits += 1
                total_dmg += event.damage
                monster.hp -= event.damage
            if monster.hp <= 0:
                attacks_to_kill = i + 1
                break
        if attacks_to_kill == 0:
            print(f"  {label}: {hits} hits, {total_dmg} dmg, monster survived with {monster.hp} HP after 50 attacks")
        else:
            print(f"  {label}: {hits} hits, {total_dmg} dmg, killed in {attacks_to_kill} attacks")


def test_starting_gear_auto_equip():
    """Test if starting gear is auto-equipped correctly."""
    print("\n" + "=" * 60)
    print("TEST 6: Starting Gear Auto-Equip")
    print("=" * 60)

    game = Game()
    game.initialize()

    player = game.player
    print(f"  Player class: {game.state.player_class}")

    # Check what was supposed to be auto-equipped
    class_config = game.config['classes'][game.state.player_class]
    start_gear = class_config.get('start_gear', [])
    print(f"  Start gear IDs from config: {start_gear}")

    # Check what's actually in inventory and equipped
    print(f"  Inventory items:")
    for item in player.inventory.items:
        eq = " [EQUIPPED]" if item.equipped else ""
        print(f"    - {item.name} ({item.id}){eq}")

    print(f"  Equipped slots:")
    for slot, item in player.inventory.equipment.items():
        if item:
            print(f"    {slot}: {item.name}")
        else:
            print(f"    {slot}: empty")

    print(f"  Final stats: to_hit_bonus={player.to_hit_bonus}, damage_bonus={player.damage_bonus}")


if __name__ == "__main__":
    test_player_creation()
    test_weapon_equip()
    test_combat_resolver()
    test_full_game_attack()
    test_no_weapon_vs_with_weapon()
    test_starting_gear_auto_equip()

    print("\n" + "=" * 60)
    print("DEBUG COMPLETE")
    print("=" * 60)
