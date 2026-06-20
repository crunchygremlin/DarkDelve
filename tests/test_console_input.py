"""Tests for console-mode input handling."""

import tcod

from darkdelve import Game


def test_console_key_mapping_creates_tcod_key_events():
    game = Game()

    event = game._console_key_to_event("w")

    assert event is not None
    assert event.sym == tcod.event.KeySym.W
    assert event.scancode == tcod.event.Scancode.W
