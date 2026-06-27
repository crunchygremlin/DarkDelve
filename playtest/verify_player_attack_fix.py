#!/usr/bin/env python3
"""
Playtest script to verify player attack fix.

Tests:
1. Combat log rendering is visible on screen (not off-screen)
2. Status bar shows combat messages
3. Player attacks adjacent monsters (via bump-attack = moving toward monster)
4. Monster HP decreases after attacks
5. Monsters die after sufficient attacks
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from darkdelve import Game

def find_adjacent_monster(game):
    """Find a monster adjacent to the player."""
    for entity in game.entities:
        if (entity.is_alive and entity.blocks and entity is not game.player and
            abs(entity.x - game.player.x) <= 1 and abs(entity.y - game.player.y) <= 1):
            return entity
    return None

def find_nearest_monster(game):
    """Find the nearest monster to the player."""
    nearest = None
    nearest_dist = float('inf')
    for entity in game.entities:
        if entity.is_alive and entity.blocks and entity is not game.player:
            dist = abs(entity.x - game.player.x) + abs(entity.y - game.player.y)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = entity
    return nearest, nearest_dist

def move_toward(game, target):
    """Move player one step toward target. Returns action or ''."""
    dx = 0
    dy = 0
    if target.x > game.player.x:
        dx = 1
    elif target.x < game.player.x:
        dx = -1
    elif target.y > game.player.y:
        dy = 1
    elif target.y < game.player.y:
        dy = -1

    action = ""
    if dx == 1:
        action = "d"
    elif dx == -1:
        action = "a"
    elif dy == 1:
        action = "s"
    elif dy == -1:
        action = "w"

    if action:
        game.main_loop(action=action, render_to_stdout=False)
    return action

def run_playtest():
    print("=" * 70)
    print("PLAYTEST: Verify Player Attack Fix")
    print("=" * 70)

    game = Game()

    # Use default display config: dungeon.height=43, display.height=50
    # -> ui_y=44, combat log at ui_y+5=49 (last line of 50-line console)
    # Do NOT reduce display height below dungeon.height or UI goes off-screen

    print("[1] Initializing game...")
    game.initialize()
    print(f"    Player position: ({game.player.x}, {game.player.y})")
    print(f"    Player HP: {game.player.hp}/{game.player.max_hp}")
    print(f"    Entities count: {len(game.entities)}")
    print(f"    Display: {game.config['display']['width']}x{game.config['display']['height']}")
    print(f"    Dungeon: {game.config['dungeon']['width']}x{game.config['dungeon']['height']}")
    print(f"    UI y position: {game.ui.ui_y}")

    # Capture initial frame
    print("\n[2] Capturing initial frame...")
    frame = game.render_frame_text()
    initial_lines = frame.split('\n')
    print(f"    Frame dimensions: {len(initial_lines[0]) if initial_lines else 0} x {len(initial_lines)}")

    # Print initial frame (all lines)
    print(f"\n--- INITIAL FRAME (all {len(initial_lines)} lines) ---")
    for i, line in enumerate(initial_lines):
        print(f"  {i:2d}: {line}")
    print("--- END INITIAL FRAME ---")

    # Find initial monster state
    monsters = [e for e in game.entities if e.is_alive and e.blocks and e is not game.player]
    print(f"\n[3] Found {len(monsters)} alive monsters")
    for m in monsters[:5]:
        print(f"    Monster '{m.name}' at ({m.x}, {m.y}) HP={m.hp}/{m.max_hp}")

    # Find adjacent monster or move toward nearest
    target = find_adjacent_monster(game)
    if target:
        print(f"\n[4] Found adjacent monster: '{target.name}' at ({target.x}, {target.y}) HP={target.hp}/{target.max_hp}")
    else:
        print("\n[4] No adjacent monster. Moving toward nearest...")
        target, dist = find_nearest_monster(game)
        if target:
            print(f"    Nearest monster: '{target.name}' at ({target.x}, {target.y}) distance={dist}")
            moves = 0
            while not find_adjacent_monster(game) and moves < 20:
                move_toward(game, target)
                moves += 1
                if not target.is_alive:
                    target, _ = find_nearest_monster(game)
                    if not target:
                        break
            print(f"    Moved {moves} steps toward target")
            target = find_adjacent_monster(game)
            if target:
                print(f"    Now adjacent to: '{target.name}' at ({target.x}, {target.y}) HP={target.hp}/{target.max_hp}")
        else:
            print("    ERROR: No monsters found on map!")
            return False

    if not target:
        print("    ERROR: Could not find a monster to attack!")
        return False

    # Record initial HP
    initial_target_hp = target.hp
    target_name = target.name
    print(f"\n[5] Target monster '{target_name}' initial HP: {target.hp}/{target.max_hp}")

    # Attack the monster by moving into it (bump attack)
    print("\n[6] ATTACKING target (moving into monster)...")
    attack_dir = ""
    if target.x > game.player.x:
        attack_dir = "d"
    elif target.x < game.player.x:
        attack_dir = "a"
    elif target.y > game.player.y:
        attack_dir = "s"
    elif target.y < game.player.y:
        attack_dir = "w"

    print(f"    Moving direction: '{attack_dir}'")
    game.main_loop(action=attack_dir, render_to_stdout=False)

    # Render frame after attack
    frame_after_attack = game.render_frame_text()
    lines_after = frame_after_attack.split('\n')

    print(f"\n--- FRAME AFTER ATTACK (all {len(lines_after)} lines) ---")
    for i, line in enumerate(lines_after):
        print(f"  {i:2d}: {line}")
    print("--- END FRAME AFTER ATTACK ---")

    # Check for attack messages in visible output
    attack_keywords = ["HIT", "MISS", "CRITICAL", "damage", "slain", "killed", "attack", "You hit", "You kill"]
    found_messages = []
    for line in lines_after:
        for kw in attack_keywords:
            if kw.lower() in line.lower():
                found_messages.append(line.strip())
                break

    print(f"\n[7] Attack messages found in visible frame: {len(found_messages)}")
    for msg in found_messages:
        print(f"    > {msg}")

    # Check combat log events
    print(f"\n[8] Combat log events: {len(game.combat_log.events)}")
    for event in game.combat_log.get_recent(5):
        print(f"    > {event}")

    # Check monster HP after first attack (re-find by name)
    target_after = None
    for entity in game.entities:
        if entity.name == target_name and entity.is_alive:
            target_after = entity
            break

    if target_after:
        print(f"\n[9] Monster '{target_name}' HP after first attack: {target_after.hp}/{target_after.max_hp}")
        hp_decreased = target_after.hp < initial_target_hp
        print(f"    HP decreased: {hp_decreased}")
    else:
        print(f"\n[9] Monster '{target_name}' DIED after first attack (or killed by another entity)")
        hp_decreased = True

    # Continue attacking until dead
    attack_count = 1
    current_target = target_after
    while current_target and current_target.is_alive and attack_count < 20:
        attack_dir = ""
        if current_target.x > game.player.x:
            attack_dir = "d"
        elif current_target.x < game.player.x:
            attack_dir = "a"
        elif current_target.y > game.player.y:
            attack_dir = "s"
        elif current_target.y < game.player.y:
            attack_dir = "w"

        if not attack_dir:
            break

        game.main_loop(action=attack_dir, render_to_stdout=False)
        attack_count += 1
        if current_target.is_alive:
            print(f"    Attack {attack_count}: '{current_target.name}' HP = {current_target.hp}/{current_target.max_hp}")
        else:
            print(f"    Attack {attack_count}: '{current_target.name}' DIED!")

    # Final frame
    print(f"\n[10] Total attacks: {attack_count}")
    frame_final = game.render_frame_text()
    lines_final = frame_final.split('\n')

    print(f"\n--- FINAL FRAME (all {len(lines_final)} lines) ---")
    for i, line in enumerate(lines_final):
        print(f"  {i:2d}: {line}")
    print("--- END FINAL FRAME ---")

    # Check final combat log
    print(f"\n[11] Final combat log events ({len(game.combat_log.events)} total):")
    for event in game.combat_log.get_recent(10):
        print(f"    > {event}")

    # Check message log
    print(f"\n[12] Message log ({len(game.message_log)} messages):")
    for msg in game.message_log[-10:]:
        print(f"    > {msg}")

    # Verify success criteria
    print("\n" + "=" * 70)
    print("VERIFICATION RESULTS")
    print("=" * 70)

    # Criterion 1: Attack messages visible in rendered frame text
    all_frame_text = frame_after_attack + frame_final
    has_attack_msg = any(kw.lower() in all_frame_text.lower() for kw in attack_keywords)
    print(f"  [ {'PASS' if has_attack_msg else 'FAIL'} ] Attack messages visible in rendered frame")

    # Criterion 2: Monster HP decreased or died
    monster_died = (not current_target or not current_target.is_alive) if current_target else True
    print(f"  [ {'PASS' if monster_died else 'FAIL'} ] Monster died after attacks (died={monster_died})")

    # Criterion 3: Combat log has events
    has_combat_events = len(game.combat_log.events) > 0
    print(f"  [ {'PASS' if has_combat_events else 'FAIL'} ] Combat log has events ({len(game.combat_log.events)} events)")

    # Criterion 4: Combat log text visible on screen
    ui_y = getattr(game.ui, 'ui_y', None)
    combat_log_visible = False
    combat_area = ""
    if ui_y is not None and ui_y + 5 < len(lines_final):
        combat_area = '\n'.join(lines_final[ui_y + 2:ui_y + 7])
        combat_log_visible = len(combat_area.strip()) > 0
    print(f"  [ {'PASS' if combat_log_visible else 'FAIL'} ] Combat log text visible at ui_y+2..+6 (ui_y={ui_y})")
    if combat_area:
        print(f"    Combat area content:")
        for line in combat_area.split('\n'):
            print(f"      | {line}")

    # Criterion 5: Kill count increased
    print(f"  [INFO ] Player kills: {game.state.kills}")

    # Criterion 6: Player is still alive
    player_alive = game.player.is_alive
    print(f"  [ {'PASS' if player_alive else 'FAIL'} ] Player still alive")

    success = has_attack_msg and monster_died and has_combat_events
    print(f"\n  OVERALL: {'PASS' if success else 'FAIL'}")
    print("=" * 70)

    return success

if __name__ == "__main__":
    try:
        result = run_playtest()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
