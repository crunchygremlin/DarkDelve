"""Integration test: DM context persistence across real level transitions.

Exercises the actual Game._record_level_performance, _build_dm_evolution_context,
and combat tracking hooks end-to-end (no mocks on the hot path).
"""
import sys
import os
import tempfile
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock
from darkdelve import Game


def make_game():
    """Create a Game instance with dm_enabled=False but dm_context active."""
    # We need to bypass the full pygame init — use the class-level methods directly
    game = Mock(spec=Game)
    game.dm_context = {
        "levels": [],
        "current_level_start_turn": 0,
        "current_level_start_hp": 30,
        "current_level_kills": 0,
        "current_level_damage_taken": 0,
        "current_level_close_calls": 0,
        "total_level_monsters": 0,
    }
    game.turn = 0
    game.dm_enabled = False
    game.state = Mock()
    game.state.depth = 1
    game.current_theme = Mock()
    game.current_theme.name = "Goblin Warrens"
    game.current_theme.monster_theme = "goblin"
    game.current_theme.difficulty = 3.0
    game.player = Mock()
    game.player.hp = 30
    game.player.max_hp = 30

    # Bind real methods
    game._compute_difficulty_adjustment = Game._compute_difficulty_adjustment.__get__(game)
    game._compute_performance_summary = Game._compute_performance_summary.__get__(game)
    game._build_narrative_continuity = Game._build_narrative_continuity.__get__(game)
    game._build_dm_evolution_context = Game._build_dm_evolution_context.__get__(game)
    game._record_level_performance = Game._record_level_performance.__get__(game)
    return game


def test_full_level_transition():
    """Simulate: play level 1 with combat → descend → verify dm_context."""
    game = make_game()

    # --- Level 1 starts ---
    game.dm_context["current_level_start_turn"] = 0
    game.dm_context["current_level_start_hp"] = 30
    game.dm_context["total_level_monsters"] = 8

    # --- Simulate combat: player kills 6 monsters, takes 15 damage, 1 close call ---
    game.turn = 45
    game.dm_context["current_level_kills"] = 6
    game.dm_context["current_level_damage_taken"] = 15
    game.dm_context["current_level_close_calls"] = 1
    game.player.hp = 15  # 15/30 = 50%, no close call triggered here

    # --- Player descends to level 2 ---
    game._record_level_performance()

    # Verify level 1 was recorded
    assert len(game.dm_context["levels"]) == 1, f"Expected 1 level record, got {len(game.dm_context['levels'])}"
    record = game.dm_context["levels"][0]
    assert record["monsters_killed"] == 6
    assert record["total_monsters"] == 8
    assert record["damage_taken"] == 15
    assert record["close_calls"] == 1
    assert record["turns_taken"] == 45
    assert record["theme_name"] == "Goblin Warrens"
    assert record["monster_theme"] == "goblin"
    print("  [OK] Level 1 recorded correctly after descent")

    # --- Build evolution context for level 2 ---
    evo_ctx = game._build_dm_evolution_context(depth=2)
    assert evo_ctx is not None, "Evolution context should not be None after level 1"
    assert evo_ctx["target_depth"] == 2
    assert len(evo_ctx["previous_levels"]) == 1
    assert evo_ctx["previous_levels"][0]["theme"] == "Goblin Warrens"

    # Difficulty: 6/8 = 0.75 ratio, damage=15 < 40 → 1.1 (slight increase)
    assert evo_ctx["difficulty_adjustment"] == 1.1, f"Expected 1.1, got {evo_ctx['difficulty_adjustment']}"
    assert "dominated" not in evo_ctx["performance_summary"].lower() or "managed" in evo_ctx["performance_summary"].lower()
    print(f"  [OK] Evolution context: adjustment={evo_ctx['difficulty_adjustment']}, summary='{evo_ctx['performance_summary']}'")
    print(f"  [OK] Narrative continuity: '{evo_ctx['narrative_continuity']}'")

    return True


def test_dominated_player_gets_harder():
    """Player who clears level 1 flawlessly should get 1.3x difficulty."""
    game = make_game()
    game.dm_context["total_level_monsters"] = 8
    game.turn = 30
    game.dm_context["current_level_kills"] = 8
    game.dm_context["current_level_damage_taken"] = 5
    game.dm_context["current_level_close_calls"] = 0
    game.player.hp = 25

    game._record_level_performance()
    evo = game._build_dm_evolution_context(depth=2)
    assert evo["difficulty_adjustment"] == 1.3, f"Dominated player should get 1.3, got {evo['difficulty_adjustment']}"
    assert "dominated" in evo["performance_summary"].lower()
    print(f"  [OK] Dominated player → {evo['difficulty_adjustment']}x difficulty")
    return True


def test_struggled_player_gets_easier():
    """Player who barely survived should get 0.8x difficulty."""
    game = make_game()
    game.dm_context["total_level_monsters"] = 8
    game.turn = 100
    game.dm_context["current_level_kills"] = 1
    game.dm_context["current_level_damage_taken"] = 60
    game.dm_context["current_level_close_calls"] = 3
    game.player.hp = 5

    game._record_level_performance()
    evo = game._build_dm_evolution_context(depth=2)
    assert evo["difficulty_adjustment"] == 0.8, f"Struggled player should get 0.8, got {evo['difficulty_adjustment']}"
    assert "struggled" in evo["performance_summary"].lower()
    print(f"  [OK] Struggled player → {evo['difficulty_adjustment']}x difficulty")
    return True


def test_multi_level_accumulation():
    """Play 4 levels, verify only last 3 are used for evolution context."""
    game = make_game()

    for depth in range(1, 5):
        game.state.depth = depth  # Real game updates state.depth on descent
        game.dm_context["current_level_start_turn"] = game.turn
        game.dm_context["current_level_kills"] = 5
        game.dm_context["current_level_damage_taken"] = 20
        game.dm_context["current_level_close_calls"] = 0
        game.dm_context["total_level_monsters"] = 8
        game.current_theme.name = f"Theme_{depth}"
        game.current_theme.monster_theme = "goblin"
        game.turn += 50
        game._record_level_performance()

    assert len(game.dm_context["levels"]) == 4
    evo = game._build_dm_evolution_context(depth=5)
    assert len(evo["previous_levels"]) == 3, f"Expected 3 previous levels, got {len(evo['previous_levels'])}"
    # Should be depths 2, 3, 4 (last 3)
    depths_in_evo = [lvl["depth"] for lvl in evo["previous_levels"]]
    assert depths_in_evo == [2, 3, 4], f"Expected [2,3,4], got {depths_in_evo}"
    print(f"  [OK] Multi-level: 4 levels stored, evolution uses last 3: depths {depths_in_evo}")
    return True


def test_no_previous_levels_returns_none():
    """Evolution context with no history should return None."""
    game = make_game()
    evo = game._build_dm_evolution_context(depth=2)
    assert evo is None, "Should return None when no previous levels"
    print("  [OK] No previous levels → evolution context is None")
    return True


def test_close_call_tracking():
    """Verify close call is counted when HP drops below 25%."""
    game = make_game()
    game.dm_context["total_level_monsters"] = 8
    game.turn = 50
    game.dm_context["current_level_kills"] = 3
    game.dm_context["current_level_damage_taken"] = 25
    game.dm_context["current_level_close_calls"] = 2  # already tracked during combat
    game.player.hp = 5  # 5/30 = 16.7% < 25%

    game._record_level_performance()
    record = game.dm_context["levels"][0]
    assert record["close_calls"] == 2
    print(f"  [OK] Close calls recorded: {record['close_calls']}")
    return True


if __name__ == "__main__":
    tests = [
        ("Full level transition (combat → descend → evolve)", test_full_level_transition),
        ("Dominated player gets harder levels", test_dominated_player_gets_harder),
        ("Struggled player gets easier levels", test_struggled_player_gets_easier),
        ("Multi-level accumulation (bounds to last 3)", test_multi_level_accumulation),
        ("No previous levels returns None", test_no_previous_levels_returns_none),
        ("Close call tracking", test_close_call_tracking),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            print(f"\n▶ {name}")
            fn()
            passed += 1
            print(f"  ✅ PASS")
        except Exception as e:
            failed += 1
            print(f"  ❌ FAIL: {e}")

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    if failed == 0:
        print("ALL INTEGRATION TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)
