#!/usr/bin/env python3
"""
Manual playtest — controls the game directly by pressing keys.
This is where the IDE LLM drives the game through MCP-like commands:
rendering frames, reading state, and sending key inputs.

Run with: python -m pytest tests/test_manual_playtest.py -v -s
Or standalone: python tests/test_manual_playtest.py
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
            "Monsters should follow when player moves away"
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
        player_moves = 0
        monster_moves = 0
        last_monster_pos = target['position']

        # Run 30 turns where player waits
        print("Running 30 wait turns...")
        for i in range(30):
            pt.press("e")
            player_moves += 1  # Player acted every turn

            # Check if our target monster moved
            m = pt.find_monster(target['char'])
            if m and m['position'] != last_monster_pos:
                monster_moves += 1
                last_monster_pos = m['position']

        print(f"\nPlayer acted: {player_moves} times")
        print(f"Monster moved: {monster_moves} times")
        print(f"Ratio: {player_moves / max(1, monster_moves):.1f}x")

        # Player should act at least 2x as often as the monster
        # (since player speed=100, monster speed=50-80)
        self.assertGreater(
            player_moves / max(1, monster_moves), 1.5,
            "Player should move at least 1.5x as often as monsters"
        )
        print(f"✓ Player is {player_moves / max(1, monster_moves):.1f}x faster than monster")

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
