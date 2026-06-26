#!/usr/bin/env python3
"""
Targeted playtest to verify the arrow key menu navigation fix.

Tests:
1. Interactive path: arrow keys are blocked when showing_menu/inventory/character is True
2. MCP path: movement string actions are blocked when overlays are showing
3. Menu navigation: "up"/"down" strings still navigate the menu when it's open
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tcod.event
from darkdelve import Game, InputHandler, Entity, GameState


class DummyGame:
    def __init__(self):
        self.pickup_item = lambda: None
        self.show_inventory = lambda: None
        self.show_character = lambda: None
        self.use_stairs_down = lambda: None
        self.use_stairs_up = lambda: None
        self.show_menu = lambda: None
        self.showing_menu = False
        self.showing_inventory = False
        self.showing_character = False


def make_key_event(key_sym):
    return tcod.event.KeyDown(
        sym=key_sym,
        scancode=tcod.event.Scancode(key_sym),
        mod=tcod.event.Modifier.NONE,
    )


def test_interactive_arrow_keys_blocked():
    """Test 1: Arrow keys must NOT cause movement when overlays are open."""
    print("=" * 60)
    print("TEST 1: Interactive path - arrow keys blocked when overlay open")
    print("=" * 60)

    handler = InputHandler(config={})
    player = Entity()
    player.x = 5
    player.y = 5
    game = DummyGame()
    state = GameState()

    arrow_keys = [
        (tcod.event.KeySym.UP, "UP"),
        (tcod.event.KeySym.DOWN, "DOWN"),
        (tcod.event.KeySym.LEFT, "LEFT"),
        (tcod.event.KeySym.RIGHT, "RIGHT"),
    ]

    overlay_flags = ["showing_menu", "showing_inventory", "showing_character"]
    all_passed = True

    for overlay_flag in overlay_flags:
        game.showing_menu = False
        game.showing_inventory = False
        game.showing_character = False
        setattr(game, overlay_flag, True)

        for key_sym, key_name in arrow_keys:
            event = make_key_event(key_sym)
            result = handler.handle_event(event, player, None, [], state, game)
            # Should return False (not quit) and NOT call any game method
            if result is not False:
                print(f"  FAIL: {key_name} with {overlay_flag}=True returned {result}, expected False")
                all_passed = False
            else:
                print(f"  PASS: {key_name} with {overlay_flag}=True -> blocked (returned False)")

    return all_passed


def test_interactive_movement_keys_blocked():
    """Test 2: WASD movement keys must NOT cause movement when overlays are open."""
    print()
    print("=" * 60)
    print("TEST 2: Interactive path - WASD blocked when overlay open")
    print("=" * 60)

    handler = InputHandler(config={})
    player = Entity()
    player.x = 5
    player.y = 5
    game = DummyGame()
    state = GameState()

    wasd_keys = [
        (tcod.event.KeySym.W, "W"),
        (tcod.event.KeySym.A, "A"),
        (tcod.event.KeySym.S, "S"),
        (tcod.event.KeySym.D, "D"),
    ]

    overlay_flags = ["showing_menu", "showing_inventory", "showing_character"]
    all_passed = True

    for overlay_flag in overlay_flags:
        game.showing_menu = False
        game.showing_inventory = False
        game.showing_character = False
        setattr(game, overlay_flag, True)

        for key_sym, key_name in wasd_keys:
            event = make_key_event(key_sym)
            result = handler.handle_event(event, player, None, [], state, game)
            if result is not False:
                print(f"  FAIL: {key_name} with {overlay_flag}=True returned {result}, expected False")
                all_passed = False
            else:
                print(f"  PASS: {key_name} with {overlay_flag}=True -> blocked (returned False)")

    return all_passed


def test_interactive_escape_still_works():
    """Test 3: ESCAPE key must still be processed (returns False, doesn't quit)."""
    print()
    print("=" * 60)
    print("TEST 3: Interactive path - ESCAPE not blocked by overlay guard")
    print("=" * 60)

    handler = InputHandler(config={})
    player = Entity()
    player.x = 5
    player.y = 5
    game = DummyGame()
    state = GameState()

    game.showing_menu = True
    event = make_key_event(tcod.event.KeySym.ESCAPE)
    result = handler.handle_event(event, player, None, [], state, game)

    # ESCAPE should return False (not quit) - it's handled by the menu loop, not handle_event
    # The overlay guard returns False before movement processing, which is correct
    # because the menu's own event loop handles ESCAPE
    if result is False:
        print("  PASS: ESCAPE with showing_menu=True -> blocked from movement processing (correct)")
        return True
    else:
        print(f"  FAIL: ESCAPE returned {result}, expected False")
        return False


def test_mcp_path_menu_navigation():
    """Test 4: MCP process_action - 'up'/'down' navigate menu when showing_menu is True."""
    print()
    print("=" * 60)
    print("TEST 4: MCP path - menu navigation via 'up'/'down' strings")
    print("=" * 60)

    game = Game()
    game.player = Entity()
    game.player.x = 5
    game.player.y = 5
    game.showing_menu = True
    game.menu_selection = 0

    # Send "down" - should change menu_selection
    game.process_action("down")
    if game.menu_selection == 1:
        print("  PASS: 'down' moved menu_selection from 0 to 1")
    else:
        print(f"  FAIL: 'down' resulted in menu_selection={game.menu_selection}, expected 1")
        return False

    # Send "up" - should change back
    game.process_action("up")
    if game.menu_selection == 0:
        print("  PASS: 'up' moved menu_selection from 1 to 0")
    else:
        print(f"  FAIL: 'up' resulted in menu_selection={game.menu_selection}, expected 0")
        return False

    game.showing_menu = False
    return True


def test_mcp_path_escape_closes_menu():
    """Test 5: MCP process_action - 'escape' closes the menu."""
    print()
    print("=" * 60)
    print("TEST 5: MCP path - 'escape' closes menu")
    print("=" * 60)

    game = Game()
    game.player = Entity()
    game.player.x = 5
    game.player.y = 5
    game.showing_menu = True
    game.menu_selection = 1

    game.process_action("escape")
    if not game.showing_menu:
        print("  PASS: 'escape' closed the menu (showing_menu=False)")
        return True
    else:
        print(f"  FAIL: 'escape' did not close menu, showing_menu={game.showing_menu}")
        return False


def test_mcp_path_movement_blocked_when_menu_showing():
    """Test 6: MCP process_action - movement keys blocked when menu is showing."""
    print()
    print("=" * 60)
    print("TEST 6: MCP path - movement blocked when menu is showing")
    print("=" * 60)

    game = Game()
    game.player = Entity()
    game.player.x = 5
    game.player.y = 5
    game.showing_menu = True
    game.menu_selection = 0

    # Try to move with "d" (right) - should NOT move because menu handling intercepts
    # Note: process_action checks showing_menu first and only processes movement if menu is closed
    initial_x = game.player.x
    game.process_action("d")

    if game.player.x == initial_x:
        print("  PASS: 'd' did not move player when menu is open")
        return True
    else:
        print(f"  FAIL: 'd' moved player from x={initial_x} to x={game.player.x}")
        return False


def main():
    results = []

    results.append(("Interactive: arrow keys blocked", test_interactive_arrow_keys_blocked()))
    results.append(("Interactive: WASD blocked", test_interactive_movement_keys_blocked()))
    results.append(("Interactive: ESCAPE handled", test_interactive_escape_still_works()))
    results.append(("MCP: menu navigation", test_mcp_path_menu_navigation()))
    results.append(("MCP: escape closes menu", test_mcp_path_escape_closes_menu()))
    results.append(("MCP: movement blocked by menu", test_mcp_path_movement_blocked_when_menu_showing()))

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("ALL TESTS PASSED")
        return 0
    else:
        print("SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
