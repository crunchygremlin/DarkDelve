import pytest
from unittest.mock import MagicMock

import tcod.event

# Import the classes from the project
from darkdelve import InputHandler, Entity, GameState


class DummyGame:
    """A minimal mock game object with the methods used by InputHandler."""

    def __init__(self):
        self.pickup_item = MagicMock(name="pickup_item")
        self.show_inventory = MagicMock(name="show_inventory")
        self.show_character = MagicMock(name="show_character")
        self.use_stairs_down = MagicMock(name="use_stairs_down")
        self.use_stairs_up = MagicMock(name="use_stairs_up")
        self.show_menu = MagicMock(name="show_menu")


@pytest.fixture
def dummy_player():
    # Create a simple Entity with required attributes for movement logic
    player = Entity()
    player.x = 5
    player.y = 5
    return player


@pytest.fixture
def dummy_state():
    # GameState is not used directly in InputHandler.handle_event, but we provide a placeholder
    return GameState()


@pytest.fixture
def dummy_game():
    return DummyGame()


@pytest.fixture
def handler():
    # InputHandler only needs the config dictionary; an empty dict is sufficient for the tests
    return InputHandler(config={})


def make_key_event(key_sym):
    """Utility to create a tcod KeyDown event for a given key symbol."""
    return tcod.event.KeyDown(key_sym)


def test_quit_event_returns_true(handler, dummy_player, dummy_game, dummy_state):
    quit_event = tcod.event.Quit()
    result = handler.handle_event(quit_event, dummy_player, None, [], dummy_state, dummy_game)
    assert result is True


@pytest.mark.parametrize(
    "key_sym,method_name",
    [
        (tcod.event.K_PERIOD, "pickup_item"),
        (tcod.event.K_COMMA, "pickup_item"),
        (tcod.event.K_g, "pickup_item"),
        (tcod.event.K_i, "show_inventory"),
        (tcod.event.K_c, "show_character"),
        (tcod.event.K_greater, "use_stairs_down"),
        (tcod.event.K_less, "use_stairs_up"),
        (tcod.event.K_ESCAPE, "show_menu"),
    ],
)
def test_action_keys_invoke_game_methods(handler, dummy_player, dummy_game, dummy_state, key_sym, method_name):
    event = make_key_event(key_sym)
    result = handler.handle_event(event, dummy_player, None, [], dummy_state, dummy_game)
    # Action keys should return False (continue game loop)
    assert result is False
    # The corresponding method on the dummy game should have been called exactly once
    getattr(dummy_game, method_name).assert_called_once()


@pytest.mark.parametrize(
    "key_sym",
    [
        tcod.event.K_w,
        tcod.event.K_a,
        tcod.event.K_s,
        tcod.event.K_d,
        tcod.event.K_UP,
        tcod.event.K_DOWN,
        tcod.event.K_LEFT,
        tcod.event.K_RIGHT,
        tcod.event.K_SPACE,
    ],
)
def test_movement_and_wait_keys_do_not_call_game_methods(handler, dummy_player, dummy_game, dummy_state, key_sym):
    event = make_key_event(key_sym)
    result = handler.handle_event(event, dummy_player, None, [], dummy_state, dummy_game)
    # Movement and wait keys should simply return False without invoking any game method
    assert result is False
    # Ensure none of the action methods were called
    for method in [
        dummy_game.pickup_item,
        dummy_game.show_inventory,
        dummy_game.show_character,
        dummy_game.use_stairs_down,
        dummy_game.use_stairs_up,
        dummy_game.show_menu,
    ]:
        method.assert_not_called()
