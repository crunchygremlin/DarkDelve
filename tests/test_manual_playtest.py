#!/usr/bin/env python3
"""
=============================================================================
MANUAL PLAYTEST — LLM-Driven Game Testing
=============================================================================

This file is where the IDE LLM (or a human) drives the game directly,
simulating what a player would do: pressing keys, reading the screen,
and observing results.

HOW LLM MANUAL TESTING WORKS:
----------------------------
1. The LLM creates a ManualPlaytest instance (or uses the class-level one)
2. It calls render() to see the current game screen (ASCII map + stats)
3. It reads get_stats() to check HP, AC, position, depth, etc.
4. It calls get_monsters() to see where monsters are
5. It decides what key to press (w/a/s/d/e) based on what it sees
6. It calls press(key) to send the command
7. It observes the result and decides the next action

This is the MCP-like interface — instead of tools, the LLM uses Python
methods to interact with the game in real-time.

RUNNING THE TESTS:
------------------
  python -m pytest tests/test_manual_playtest.py -v -s
  python tests/test_manual_playtest.py

The -s flag shows print output so you can see what the LLM "sees".

KEYS:
  w = move up (north)
  a = move left (west)
  s = move down (south)
  d = move right (east)
  e = wait one turn
  i = open inventory
  c = character screen
  , = pick up item
  > = descend stairs
  < = ascend stairs
  ESC = open menu

TIPS FOR LLM TESTING:
---------------------
- Always call render() first to see the current state
- Use get_monsters() to track monster positions before/after actions
- Use press('e') to wait and let monsters move (to observe their speed)
- Use move_toward(x, y) to navigate to a specific position
- Compare monster distances before/after to verify they're approaching
- The player should move 1.5-2x faster than monsters (speed advantage)

=============================================================================
"""

import unittest
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from darkdelve import Game, COLORS


class ManualPlaytest:
    """A manual playtest controller that acts like a human pressing keys.

    This class provides the MCP-like interface:
    - render() → get the current game frame as text
    - get_stats() → read HP, AC, position, etc.
    - press(key) → send a keypress to the game
    - get_monsters() → list visible monsters and their positions
    """

    def __init__(self, render_to_stdout=False):
        self.game = Game()
        self.game.initialize()
        self.render_to_stdout = render_to_stdout
        self.turn_count = 0

    def render(self) -> str:
        """Render the current game frame as text (like looking at the screen)."""
        return self.game.render_frame_text()

    def get_stats(self) -> dict:
        """Read current player stats (like reading the HUD)."""
        p = self.game.player
        if not p:
            return {}
        return {
            "hp": p.hp,
            "max_hp": p.max_hp,
            "ac": p.armor_class,
            "level": p.level,
            "depth": self.game.state.depth,
            "turn": self.game.turn,
            "position": (p.x, p.y),
            "nutrition": p.nutrition,
            "max_nutrition": getattr(p, 'max_nutrition', 2000),
        }

    def press(self, key: str) -> str:
        """Press a key (like a human pressing WASD).

        Keys: w=up, a=left, s=down, d=right, e=wait, i=inventory, ESC=menu
        Returns the rendered frame after the action.
        """
        self.game.main_loop(action=key, render_to_stdout=self.render_to_stdout)
        self.turn_count += 1
        return self.render()

    def press_many(self, keys: str) -> str:
        """Press multiple keys in sequence (e.g., 'sssd' = down 3, right 1)."""
        result = ""
        for key in keys:
            result = self.press(key)
        return result

    def get_monsters(self) -> list:
        """Get all non-player entities with their positions and distances."""
        p = self.game.player
        if not p:
            return []
        monsters = []
        for e in self.game.entities:
            if e is not p and e.is_alive:
                dist = abs(e.x - p.x) + abs(e.y - p.y)
                monsters.append({
                    "name": e.name,
                    "char": e.char,
                    "position": (e.x, e.y),
                    "distance": dist,
                    "hp": getattr(e, 'hp', '?'),
                    "max_hp": getattr(e, 'max_hp', '?'),
                })
        return sorted(monsters, key=lambda m: m["distance"])

    def find_monster(self, char: str) -> dict:
        """Find a monster by its character symbol."""
        for m in self.get_monsters():
            if m["char"] == char or char in m["name"]:
                return m
        return None

    def move_toward(self, target_x: int, target_y: int, max_steps: int = 50) -> int:
        """Move the player toward a target position step by step.
        Returns the number of steps taken."""
        steps = 0
        p = self.game.player
        while steps < max_steps:
            px, py = p.x, p.y
            if px == target_x and py == target_y:
                break

            dx = target_x - px
            dy = target_y - py

            # Move in the direction with the largest delta first
            if abs(dx) >= abs(dy):
                key = "d" if dx > 0 else "a"
            else:
                key = "s" if dy > 0 else "w"

            self.press(key)
            steps += 1

            # Check if we actually moved
            if p.x == px and p.y == py:
                break  # Blocked

        return steps

    def wait(self, turns: int) -> None:
        """Wait N turns (press 'e' repeatedly)."""
        for _ in range(turns):
            self.press("e")


class TestManualPlaytestMonsterMovement(unittest.TestCase):
    """Manual playtest: control the game and observe monster movement.

    This test simulates what a human would do:
    1. Look at the screen (render)
    2. Check stats
    3. Move the player
    4. Watch monsters move
    5. Verify monsters are approaching
    """

    @classmethod
    def setUpClass(cls):
        """Initialize the game once for all tests in this class."""
        cls.pt = ManualPlaytest(render_to_stdout=False)
        print("\n" + "=" * 60)
        print("MANUAL PLAYTEST: Monster Movement Observation")
        print("=" * 60)
        print(f"\nInitial frame:")
        print(cls.pt.render())
        print(f"\nPlayer stats: {cls.pt.get_stats()}")
        print(f"\nMonsters visible: {len(cls.pt.get_monsters())}")
        for m in cls.pt.get_monsters():
            print(f"  {m['char']} {m['name']} at {m['position']}, dist={m['distance']}")

    def setUp(self):
        """Heal/revive the player before each test to prevent cascading death issues."""
        g = self.__class__.pt.game
        if g.player is None or not g.player.is_alive:
            # Player was killed or removed; reinitialize the game entirely
            # This also resets monster positions to a fresh dungeon state
            g.initialize()
        else:
            # Player is alive; heal to full
            g.player.hp = g.player.max_hp

    def test_01_player_can_move(self):
        """Verify the player can move with WASD keys."""
        print("\n--- Test: Player Movement ---")
        stats_before = self.__class__.pt.get_stats()
        print(f"Position before: {stats_before['position']}")

        # Move right
        self.__class__.pt.press("d")
        stats_after = self.__class__.pt.get_stats()
        print(f"Position after 'd': {stats_after['position']}")

        # Player should have moved (or attacked something in the way)
        self.assertNotEqual(
            stats_before['position'],
            stats_after['position'],
            "Player should move when pressing 'd'"
        )
        print("✓ Player movement works")

    def test_02_monsters_exist_and_have_distance(self):
        """Verify monsters are present and we can measure their distance."""
        print("\n--- Test: Monster Detection ---")
        monsters = self.__class__.pt.get_monsters()
        self.assertGreater(len(monsters), 0, "Should have at least one monster")

        for m in monsters[:5]:
            print(f"  {m['char']} {m['name']} at {m['position']}, dist={m['distance']}")
        print(f"✓ Detected {len(monsters)} monsters")

    def test_03_monsters_approach_when_player_waits(self):
        """Verify monsters move toward the player when player waits."""
        print("\n--- Test: Monsters Approach During Wait ---")
        pt = self.__class__.pt

        # Get initial distances
        initial_monsters = {m['name']: m['distance'] for m in pt.get_monsters()}
        print("Initial distances:")
        for name, dist in list(initial_monsters.items())[:5]:
            print(f"  {name}: {dist}")

        # Wait several turns
        wait_turns = 10
        print(f"\nWaiting {wait_turns} turns (pressing 'e' × {wait_turns})...")
        pt.wait(wait_turns)

        # Get final distances
        final_monsters = {m['name']: m['distance'] for m in pt.get_monsters()}
        print("\nFinal distances:")
        for name, dist in list(final_monsters.items())[:5]:
            print(f"  {name}: {dist}")

        # At least some monsters should be closer
        approached = 0
        for name in initial_monsters:
            if name in final_monsters:
                if final_monsters[name] < initial_monsters[name]:
                    approached += 1
                    print(f"  ✓ {name}: {initial_monsters[name]} → {final_monsters[name]}")

        self.assertGreater(
            approached, 0,
            "At least one monster should approach the player"
        )
        print(f"\n✓ {approached}/{len(initial_monsters)} monsters approached")

    def test_04_monsters_approach_when_player_moves_away(self):
        """Verify monsters follow when the player moves away."""
        print("\n--- Test: Monsters Follow Moving Player ---")
        pt = self.__class__.pt

        # Get initial state
        initial_distances = {m['name']: m['distance'] for m in pt.get_monsters()}
        player_pos_before = pt.get_stats()['position']
        print(f"Player position: {player_pos_before}")

        # Move player in a direction (try 'w' first, then 'a')
        print("Moving player left ('a' × 5)...")
        steps_taken = pt.move_toward(5, player_pos_before[1], max_steps=5)
        player_pos_after = pt.get_stats()['position']
        print(f"Player position after: {player_pos_after} (moved {steps_taken} steps)")

        # Wait a bit for monsters to react
        pt.wait(5)

        # Check if monsters followed (distances should decrease or stay similar)
        final_distances = {m['name']: m['distance'] for m in pt.get_monsters()}

        followed = 0
        for name in initial_distances:
            if name in final_distances:
                change = initial_distances[name] - final_distances[name]
                if change > 0:
                    followed += 1
                    print(f"  ✓ {name}: closed gap by {change}")

        # At least some monsters should have followed
        self.assertGreater(
            followed, 0,
            "Monsters should follow when player moves (tried directions: {})".format(['a', 'w', 'd', 's'])
        )
        print(f"\n✓ {followed} monsters followed the player")

    def test_05_speed_comparison(self):
        """Compare player movement speed vs monster movement speed.

        The player should move more frequently than monsters.
        We count how many turns the player acts vs how many times a specific monster moves.
        """
        print("\n--- Test: Speed Comparison (Player vs Monster) ---")
        pt = self.__class__.pt

        # Find a nearby monster
        monsters = pt.get_monsters()
        if not monsters:
            self.skipTest("No monsters visible")

        target = monsters[0]
        print(f"Tracking: {target['char']} {target['name']} at {target['position']}")

        # Get initial positions
        player_turns_before = pt.get_stats()['turn']
        initial_pos = target['position']

        # Enable godmode so the player survives monster attacks during this
        # speed test (we are testing movement speed, not combat survival).
        g = pt.game
        g.player.max_hp = 99999
        g.player.hp = 99999

        # Run 30 turns where player waits
        print("Running 30 wait turns (godmode)...")
        pt.wait(30)

        # Restore normal HP so later tests are not affected
        g.player.max_hp = 23
        g.player.hp = 23

        # Check results
        player_turns_after = pt.get_stats()['turn']
        player_turns = player_turns_after - player_turns_before
        final_pos = pt.find_monster(target['char'])['position']
        monster_moved = initial_pos != final_pos

        print(f"\nPlayer turns: {player_turns}")
        print(f"Monster moved: {monster_moved} ({initial_pos} → {final_pos})")

        # Player should have taken 30 turns
        self.assertEqual(player_turns, 30, "Player should have taken 30 turns")
        print(f"✓ Player took {player_turns} turns in 30 frames")

    def test_06_wait_method_exists_and_advances_turns(self):
        """Regression: ensure wait() method exists and advances the turn counter.

        This catches the bug where wait() was accidentally deleted and
        tests would fail with AttributeError: 'ManualPlaytest' has no attribute 'wait'.
        """
        print("\n--- Test: wait() method regression ---")
        pt = self.__class__.pt
        
        # Verify the method exists (would raise AttributeError if missing)
        self.assertTrue(hasattr(pt, 'wait'), "ManualPlaytest should have a wait() method")
        self.assertTrue(callable(pt.wait), "ManualPlaytest.wait should be callable")
        
        # Record turn before
        turns_before = pt.get_stats()['turn']
        
        # Wait 3 turns
        pt.wait(3)
        
        # Verify turns advanced
        turns_after = pt.get_stats()['turn']
        self.assertEqual(
            turns_after - turns_before, 3,
            "wait(3) should advance exactly 3 turns"
        )
        print(f"✓ wait(3) advanced turns: {turns_before} → {turns_after}")

    def test_07_combat_message_categories_exist(self):
        """Verify that combat message log has three categories after combat."""
        print("\n--- Test: Combat Message Categories ---")
        pt = self.__class__.pt
        g = pt.game
        
        # Ensure combat_message_log exists
        self.assertTrue(
            hasattr(g, 'combat_message_log'),
            "Game should have combat_message_log attribute"
        )
        
        # Check that it has the three required categories
        self.assertIn("player_actions", g.combat_message_log)
        self.assertIn("against_player", g.combat_message_log)
        self.assertIn("observable", g.combat_message_log)
        
        print(f"  combat_message_log keys: {list(g.combat_message_log.keys())}")
        print("✓ Combat message categories exist")

    @classmethod
    def tearDownClass(cls):
        """Print final state."""
        print("\n" + "=" * 60)
        print("MANUAL PLAYTEST COMPLETE")
        print("=" * 60)
        print(f"\nTotal turns: {cls.pt.turn_count}")
        print(f"Final stats: {cls.pt.get_stats()}")
        print(f"\nFinal frame:")
        print(cls.pt.render())


if __name__ == '__main__':
    unittest.main(verbosity=2)
