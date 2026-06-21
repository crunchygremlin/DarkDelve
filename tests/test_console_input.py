"""Tests for console-mode input handling."""

import sys
import warnings

import pytest
import tcod

from darkdelve import Game
from src.presentation.renderer import ConsoleRenderer


class _FakeStdin:
    def __init__(self, text: str):
        self.text = text

    def isatty(self) -> bool:
        return False

    def readline(self) -> str:
        return self.text


def test_console_key_mapping_creates_tcod_key_events():
    game = Game()

    event = game._console_key_to_event("w")

    assert event is not None
    assert event.sym == tcod.event.KeySym.W
    assert event.scancode == tcod.event.Scancode.W


def test_console_key_mapping_creates_wait_event_for_e():
    game = Game()

    event = game._console_key_to_event("e")

    assert event is not None
    assert event.sym == tcod.event.KeySym.E
    assert event.scancode == tcod.event.Scancode.E


@pytest.mark.parametrize(
    ("key", "expected_sym"),
    [
        (",", tcod.event.KeySym.COMMA),
        (".", tcod.event.KeySym.PERIOD),
        ("e", tcod.event.KeySym.E),
    ],
)
def test_console_key_mapping_creates_action_events(key, expected_sym):
    game = Game()

    event = game._console_key_to_event(key)

    assert event is not None
    assert event.sym == expected_sym


@pytest.mark.parametrize(
    ("key", "expected_sym"),
    [
        ("\x1b[A", tcod.event.KeySym.UP),
        ("\x1b[B", tcod.event.KeySym.DOWN),
        ("\x1b[C", tcod.event.KeySym.RIGHT),
        ("\x1b[D", tcod.event.KeySym.LEFT),
    ],
)
def test_console_key_mapping_handles_arrow_escape_sequences(key, expected_sym):
    game = Game()

    event = game._console_key_to_event(key)

    assert event is not None
    assert event.sym == expected_sym


def test_console_event_wait_does_not_poll_sdl_events(monkeypatch):
    game = Game()
    game.renderer = ConsoleRenderer(tcod.console.Console(1, 1))
    monkeypatch.setattr(sys, "stdin", _FakeStdin("w\n"))

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        events = game._wait_for_events()

    assert len(events) == 1
    assert isinstance(events[0], tcod.event.KeyDown)
    assert events[0].sym == tcod.event.KeySym.W
    sdl_warnings = [
        warning
        for warning in caught
        if "Events polled before SDL was initialized" in str(warning.message)
    ]
    assert sdl_warnings == []


def test_console_event_wait_maps_arrow_escape_sequence(monkeypatch):
    game = Game()
    game.renderer = ConsoleRenderer(tcod.console.Console(1, 1))
    monkeypatch.setattr(sys, "stdin", _FakeStdin("\x1b[A\n"))

    events = game._wait_for_events()

    assert len(events) == 1
    assert isinstance(events[0], tcod.event.KeyDown)
    assert events[0].sym == tcod.event.KeySym.UP


def test_inventory_screen_uses_game_event_wait(monkeypatch):
    game = Game()
    game.renderer = ConsoleRenderer(tcod.console.Console(1, 1))
    game.showing_inventory = True
    calls = []

    def fake_wait_for_events():
        calls.append("waited")
        return [
            tcod.event.KeyDown(
                scancode=tcod.event.Scancode.ESCAPE,
                sym=tcod.event.KeySym.ESCAPE,
                mod=tcod.event.Modifier.NONE,
            )
        ]

    monkeypatch.setattr(game, "render_inventory", lambda: None)
    monkeypatch.setattr(game, "_wait_for_events", fake_wait_for_events)

    game.show_inventory()

    assert calls == ["waited"]
    assert game.showing_inventory is False


def test_menu_ignores_unknown_keys_and_exits_on_escape(monkeypatch):
    game = Game()
    game.renderer = ConsoleRenderer(tcod.console.Console(1, 1))
    game.showing_menu = True
    calls = []
    events = iter(
        [
            [
                tcod.event.KeyDown(
                    scancode=tcod.event.Scancode.W,
                    sym=tcod.event.KeySym.W,
                    mod=tcod.event.Modifier.NONE,
                )
            ],
            [
                tcod.event.KeyDown(
                    scancode=tcod.event.Scancode.ESCAPE,
                    sym=tcod.event.KeySym.ESCAPE,
                    mod=tcod.event.Modifier.NONE,
                )
            ],
        ]
    )

    def fake_wait_for_events():
        calls.append("waited")
        return next(events)

    monkeypatch.setattr(game, "render_menu", lambda menu_options: calls.append("rendered"))
    monkeypatch.setattr(game, "_wait_for_events", fake_wait_for_events)

    game.show_menu()

    assert calls == ["rendered", "waited", "rendered", "waited"]
    assert game.showing_menu is False


def test_menu_uses_arrow_keys_for_navigation(monkeypatch):
    game = Game()
    game.renderer = ConsoleRenderer(tcod.console.Console(1, 1))
    game.showing_menu = True
    calls = []
    events = iter(
        [
            [
                tcod.event.KeyDown(
                    scancode=tcod.event.Scancode.UP,
                    sym=tcod.event.KeySym.UP,
                    mod=tcod.event.Modifier.NONE,
                )
            ],
            [
                tcod.event.KeyDown(
                    scancode=tcod.event.Scancode.ESCAPE,
                    sym=tcod.event.KeySym.ESCAPE,
                    mod=tcod.event.Modifier.NONE,
                )
            ],
        ]
    )

    def fake_wait_for_events():
        calls.append("waited")
        return next(events)

    monkeypatch.setattr(game, "render_menu", lambda menu_options: calls.append("rendered"))
    monkeypatch.setattr(game, "_wait_for_events", fake_wait_for_events)

    game.show_menu()

    assert calls == ["rendered", "waited", "rendered", "waited"]
    assert game.menu_selection == 2
