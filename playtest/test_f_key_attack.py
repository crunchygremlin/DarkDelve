#!/usr/bin/env python3
"""
Playtest: Press F to attack adjacent monster and capture screen.

Tests:
1. Does action="f" via main_loop trigger a player attack?
2. Does bump-attack (move into monster) work?
3. Does direct game.attack() work?
4. Are combat messages visible in rendered frame?
5. Does monster HP decrease / monster die?
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from darkdelve import Game


def find_adjacent_monster(game):
    """Find a monster at Manhattan distance == 1 from the player."""
    for entity in game.entities:
        if (entity.is_alive and entity.blocks and entity is not game.player and
            abs(entity.x - game.player.x) + abs(entity.y - game.player.y) == 1):
            return entity
    return None


def find_nearest_monster(game):
    """Find the nearest alive monster to the player (Manhattan distance)."""
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
    """Move player one step toward target. Returns the action key used."""
    action = ""
    if target.x > game.player.x:
        action = "d"
    elif target.x < game.player.x:
        action = "a"
    elif target.y > game.player.y:
        action = "s"
    elif target.y < game.player.y:
        action = "w"
    if action:
        game.main_loop(action=action, render_to_stdout=False)
    return action


def direction_toward(player, target):
    """Return the wasd key to step from player toward target."""
    if target.x > player.x:
        return "d"
    elif target.x < player.x:
        return "a"
    elif target.y > player.y:
        return "s"
    elif target.y < player.y:
        return "w"
    return ""


def approach_monster(game, max_steps=30):
    """Move toward nearest monster until adjacent. Returns adjacent monster or None."""
    target = find_adjacent_monster(game)
    if target:
        return target
    t, d = find_nearest_monster(game)
    if not t:
        return None
    moves = 0
    while not find_adjacent_monster(game) and moves < max_steps:
        if not t.is_alive:
            t, _ = find_nearest_monster(game)
            if not t:
                return None
        move_toward(game, t)
        moves += 1
    return find_adjacent_monster(game)


def count_player_attacks_in_log(game, player_name="Adventurer"):
    """Count combat log events where the player is the attacker."""
    count = 0
    for event in game.combat_log.events:
        if getattr(event, 'attacker_name', '') == player_name:
            count += 1
    return count


def run_playtest():
    print("=" * 70)
    print("PLAYTEST: F-Key Attack & Bump Attack")
    print("=" * 70)

    # ── Step 1: Initialize ──
    print("\n[1] Initializing game...")
    game = Game()
    game.initialize()
    player_name = game.player.name
    print(f"    Player: '{player_name}' at ({game.player.x}, {game.player.y})")
    print(f"    Player HP: {game.player.hp}/{game.player.max_hp}")

    # ── Step 2: Initial frame ──
    print("\n[2] Capturing initial frame...")
    frame_before = game.render_frame_text()
    lines_before = frame_before.split('\n')
    print(f"    Frame: {len(lines_before[0]) if lines_before else 0}x{len(lines_before)}")
    # Show dungeon area (lines 0-10) and UI area (last 6 lines)
    print(f"\n--- INITIAL FRAME (dungeon + UI) ---")
    for i, line in enumerate(lines_before[:11]):
        print(f"  {i:2d}: {line}")
    print(f"  ... ({len(lines_before) - 17} lines omitted) ...")
    for i in range(len(lines_before) - 6, len(lines_before)):
        print(f"  {i:2d}: {lines_before[i]}")
    print("--- END INITIAL FRAME ---")

    # ── Step 3: Find monsters ──
    monsters = [e for e in game.entities if e.is_alive and e.blocks and e is not game.player]
    print(f"\n[3] Found {len(monsters)} alive monsters")
    for m in monsters[:5]:
        dist = abs(m.x - game.player.x) + abs(m.y - game.player.y)
        print(f"    '{m.name}' at ({m.x},{m.y}) HP={m.hp}/{m.max_hp} dist={dist}")

    # ── Step 4: Approach a monster ──
    print("\n[4] Approaching nearest monster...")
    target = approach_monster(game)
    if not target:
        print("    FATAL: No monsters found or reachable!")
        return False
    print(f"    Adjacent to: '{target.name}' at ({target.x},{target.y}) HP={target.hp}/{target.max_hp}")
    print(f"    Player at: ({game.player.x},{game.player.y})")

    # ── Step 5: Test action="f" via main_loop ──
    print(f"\n[5] Testing action='f' via main_loop...")
    target = find_adjacent_monster(game)
    if not target:
        target = approach_monster(game)
        if not target:
            print("    FATAL: No adjacent monster for f-key test!")
            return False

    target_id = id(target)
    hp_before_f = target.hp
    player_attacks_before = count_player_attacks_in_log(game, player_name)
    game.main_loop(action="f", render_to_stdout=False)
    # Re-find same entity by id
    target_ref = None
    for e in game.entities:
        if id(e) == target_id:
            target_ref = e
            break
    hp_after_f = target_ref.hp if target_ref else -1
    player_attacks_after = count_player_attacks_in_log(game, player_name)
    f_key_worked = player_attacks_after > player_attacks_before
    print(f"    Target HP before: {hp_before_f}, after: {hp_after_f}")
    print(f"    Player attacks in log: {player_attacks_before} → {player_attacks_after}")
    print(f"    RESULT: f-key {'WORKED' if f_key_worked else 'DID NOT WORK'}")
    if not f_key_worked:
        print(f"    BUG: process_action() does not handle 'f' key")

    # ── Step 6: Test direct game.attack() ──
    print(f"\n[6] Testing direct game.attack(player, target)...")
    target = find_adjacent_monster(game)
    if not target:
        target = approach_monster(game)
        if not target:
            print("    FATAL: No adjacent monster!")
            return False

    target_id = id(target)
    hp_before_direct = target.hp
    player_attacks_before = count_player_attacks_in_log(game, player_name)
    print(f"    Target: '{target.name}' at ({target.x},{target.y}) HP={target.hp}/{target.max_hp}")
    game.attack(game.player, target)
    hp_after_direct = target.hp
    player_attacks_after = count_player_attacks_in_log(game, player_name)
    direct_worked = player_attacks_after > player_attacks_before
    direct_hp_decreased = hp_after_direct < hp_before_direct
    print(f"    HP: {hp_before_direct} → {hp_after_direct}, alive={target.is_alive}")
    print(f"    Player attacks in log: {player_attacks_before} → {player_attacks_after}")
    print(f"    RESULT: Direct attack {'WORKED' if direct_worked else 'DID NOT WORK'}")
    if direct_worked and not direct_hp_decreased:
        print(f"    NOTE: Attack registered but HP unchanged (MISS roll)")

    # ── Step 7: Test bump-attack ──
    print(f"\n[7] Testing bump-attack (move into monster)...")
    target = find_adjacent_monster(game)
    if not target:
        target = approach_monster(game)
        if not target:
            print("    FATAL: No adjacent monster!")
            return False

    target_id = id(target)
    hp_before_bump = target.hp
    attack_dir = direction_toward(game.player, target)
    player_attacks_before = count_player_attacks_in_log(game, player_name)
    print(f"    Target: '{target.name}' at ({target.x},{target.y}) HP={target.hp}/{target.max_hp}")
    print(f"    Player at ({game.player.x},{game.player.y}), bump dir='{attack_dir}'")
    game.main_loop(action=attack_dir, render_to_stdout=False)
    # Re-find same entity by id
    target_ref = None
    for e in game.entities:
        if id(e) == target_id:
            target_ref = e
            break
    hp_after_bump = target_ref.hp if target_ref else -1
    is_alive_bump = target_ref.is_alive if target_ref else False
    player_attacks_after = count_player_attacks_in_log(game, player_name)
    bump_worked = player_attacks_after > player_attacks_before
    bump_hp_decreased = hp_after_bump < hp_before_bump
    print(f"    HP: {hp_before_bump} → {hp_after_bump}, alive={is_alive_bump}")
    print(f"    Player attacks in log: {player_attacks_before} → {player_attacks_after}")
    print(f"    RESULT: Bump attack {'WORKED' if bump_worked else 'DID NOT WORK'}")
    if bump_worked and not bump_hp_decreased:
        print(f"    NOTE: Attack registered but HP unchanged (MISS roll)")

    # ── Step 8: Multiple bump-attacks to verify damage ──
    print(f"\n[8] Multiple bump-attacks to verify combat damage...")
    total_hits = 0
    total_misses = 0
    total_kills = 0
    for i in range(15):
        target = find_adjacent_monster(game)
        if not target:
            target = approach_monster(game)
            if not target:
                print(f"    All monsters dead after {i} rounds!")
                break

        target_id = id(target)
        attack_dir = direction_toward(game.player, target)
        if not attack_dir:
            move_toward(game, target)
            continue

        hp_before = target.hp
        player_attacks_before = count_player_attacks_in_log(game, player_name)
        game.main_loop(action=attack_dir, render_to_stdout=False)
        player_attacks_after = count_player_attacks_in_log(game, player_name)

        if player_attacks_after > player_attacks_before:
            # Find same entity by id
            target_ref = None
            for e in game.entities:
                if id(e) == target_id:
                    target_ref = e
                    break
            if target_ref and target_ref.is_alive:
                if target_ref.hp < hp_before:
                    total_hits += 1
                else:
                    total_misses += 1
            else:
                total_hits += 1
                total_kills += 1

    print(f"    Hits: {total_hits}, Misses: {total_misses}, Kills: {total_kills}")
    bump_damage_works = total_hits > 0
    print(f"    RESULT: Bump-attack damage {'WORKED' if bump_damage_works else 'DID NOT WORK'}")

    # ── Step 9: Render frame after attacks ──
    print("\n[9] Frame after attacks:")
    frame_after = game.render_frame_text()
    lines_after = frame_after.split('\n')
    print(f"\n--- FRAME AFTER ATTACKS ---")
    for i, line in enumerate(lines_after[:11]):
        print(f"  {i:2d}: {line}")
    print(f"  ... ({len(lines_after) - 17} lines omitted) ...")
    for i in range(len(lines_after) - 6, len(lines_after)):
        print(f"  {i:2d}: {lines_after[i]}")
    print("--- END FRAME ---")

    # ── Step 10: Combat messages in frame ──
    attack_keywords = ["HIT", "MISS", "CRITICAL", "Damage", "slain", "attacks!", "attempts"]
    found_messages = []
    for line in lines_after:
        for kw in attack_keywords:
            if kw.lower() in line.lower():
                found_messages.append(line.strip())
                break
    print(f"\n[10] Combat messages in frame: {len(found_messages)}")
    for msg in found_messages[:5]:
        print(f"    > {msg}")

    # ── Step 11: Combat log ──
    print(f"\n[11] Combat log ({len(game.combat_log.events)} events), last 5:")
    for event in game.combat_log.get_recent(5):
        print(f"    > {event}")

    # ── Step 12: Monster state ──
    alive = [e for e in game.entities if e.is_alive and e.blocks and e is not game.player]
    dead = [e for e in game.entities if not e.is_alive and e.blocks and e is not game.player]
    print(f"\n[12] Monsters: {len(alive)} alive, {len(dead)} dead")

    # ── Verification ──
    print("\n" + "=" * 70)
    print("VERIFICATION RESULTS")
    print("=" * 70)

    print(f"  [ {'PASS' if f_key_worked else 'FAIL'} ] action='f' via main_loop triggers attack")
    if not f_key_worked:
        print(f"       BUG: process_action() missing 'f' handler (line ~2402 darkdelve.py)")

    print(f"  [ {'PASS' if direct_worked else 'FAIL'} ] Direct game.attack() produces combat event")
    print(f"  [ {'PASS' if bump_worked else 'FAIL'} ] Bump-attack produces combat event")
    print(f"  [ {'PASS' if bump_damage_works else 'FAIL'} ] Bump-attack deals HP damage (hits={total_hits})")

    all_frame_text = frame_before + frame_after
    has_attack_msg = any(kw.lower() in all_frame_text.lower() for kw in attack_keywords)
    print(f"  [ {'PASS' if has_attack_msg else 'FAIL'} ] Combat messages visible in rendered frame")

    has_combat_events = len(game.combat_log.events) > 0
    print(f"  [ {'PASS' if has_combat_events else 'FAIL'} ] Combat log has events ({len(game.combat_log.events)})")
    print(f"  [ {'PASS' if game.player.is_alive else 'FAIL'} ] Player still alive")

    combat_works = direct_worked and bump_damage_works and has_combat_events
    print(f"\n  COMBAT SYSTEM:  {'PASS' if combat_works else 'FAIL'}")
    print(f"  F-KEY ACTION:   {'PASS' if f_key_worked else 'FAIL (BUG: process_action missing \"f\" handler)'}")
    print("=" * 70)

    return combat_works


if __name__ == "__main__":
    try:
        result = run_playtest()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
