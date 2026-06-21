"""Regression tests for map rendering stability and visual output."""

import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import tcod

from darkdelve import COLORS, CombatLog, Entity, FOVSystem, GameState, UI
from src.presentation.renderer import ConsoleRenderer


def test_fov_uses_dungeon_x_y_coordinates_for_off_diagonal_player():
    """FOV must be centered on the player's dungeon [x, y], not swapped."""
    dungeon_map = np.zeros((6, 5), dtype=bool)

    fov = FOVSystem(radius=2).compute(dungeon_map, player_x=4, player_y=1)

    assert fov[4, 1]
    assert fov[3, 1]
    assert fov[4, 0]
    assert not fov[0, 0]


def test_console_renderer_present_writes_terminal_frame_without_print():
    """The console renderer should draw a stable terminal frame without print()."""
    console = tcod.console.Console(5, 3)
    console.print(2, 1, "@")
    renderer = ConsoleRenderer(console)

    with patch("builtins.print") as mocked_print, patch("sys.stdout.write") as mocked_write, patch("sys.stdout.flush") as mocked_flush:
        renderer.present()

    mocked_print.assert_not_called()
    mocked_write.assert_called_once()
    mocked_flush.assert_called_once()
    output = mocked_write.call_args.args[0]
    assert "\033[H\033[2J" in output
    assert "\033[0m\n" in output
    assert "@" in output


def test_console_renderer_present_clips_to_terminal_size(monkeypatch):
    """Console output must not exceed terminal size, or wide terminals will wrap."""
    console = tcod.console.Console(10, 4)
    console.print(9, 3, "@")
    renderer = ConsoleRenderer(console, {"display": {"width": 10, "height": 4}})
    monkeypatch.setattr("shutil.get_terminal_size", lambda fallback: (5, 2))

    with patch("sys.stdout.write") as mocked_write, patch("sys.stdout.flush") as mocked_flush:
        renderer.present()

    mocked_flush.assert_called_once()
    output = mocked_write.call_args.args[0]
    frame = output.split("\033[H\033[2J", 1)[1].split("\033[0m\n", 1)[0]
    lines = frame.splitlines()

    assert len(lines) == 2
    assert all(len(line) == 5 for line in lines)
    assert "@" not in frame


def test_ui_status_panel_fits_below_map():
    """Status and controls should render inside the configured console height."""
    console = tcod.console.Console(80, 50)

    class ConsoleLikeRenderer:
        def print(self, x, y, text, color=None):
            console.print(x, y, text, fg=color)

    config = {
        "display": {"width": 80, "height": 50},
        "dungeon": {"width": 80, "height": 43},
    }
    ui = UI(renderer=ConsoleLikeRenderer(), config=config)
    player = Entity(hp=7, max_hp=10, level=2, gold=5, nutrition=10, max_nutrition=20)
    state = GameState(depth=3)
    game = SimpleNamespace(message_log=["Welcome to DarkDelve!"])

    ui.render_ui(player, state, CombatLog(), turn=12, game=game)

    assert ui.ui_y == 44
    status = "".join(chr(int(ch)) if int(ch) else " " for ch in console.ch[ui.ui_y]).rstrip()
    controls = "".join(chr(int(ch)) if int(ch) else " " for ch in console.ch[ui.ui_y + 1]).rstrip()
    messages = "".join(chr(int(ch)) if int(ch) else " " for ch in console.ch[ui.ui_y + 2]).rstrip()

    assert "HP 7/10" in status
    assert "Depth 3" in status
    assert "WASD=Move" in controls
    assert "Welcome to DarkDelve!" in messages


def test_render_entities_keeps_player_visible_over_item_on_same_tile():
    """Items on the player's tile must not overwrite the player glyph."""
    console = tcod.console.Console(5, 3)

    class ConsoleLikeRenderer:
        def print(self, x, y, text, color):
            console.print(x, y, text, fg=color)

    player = Entity(x=2, y=1, char="@", color=COLORS["player"], name="Player")
    item = Entity(x=2, y=1, char="/", color=COLORS["item"], name="Item")
    fov = np.ones((5, 3), dtype=bool)

    ui = UI(
        renderer=ConsoleLikeRenderer(),
        config={"display": {"width": 5, "height": 3}, "dungeon": {"width": 5, "height": 3}},
    )

    ui.render_entities([player, item], fov, player)

    assert console.ch[player.y, player.x] == ord("@")


def test_rendered_map_screenshot_keeps_off_diagonal_player_visible(tmp_path):
    """Create a headless Linux screenshot of the rendered map and verify it."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"

    width = 12
    height = 8
    dungeon_map = np.zeros((width, height), dtype=bool)
    player = Entity(
        x=8,
        y=3,
        char="@",
        color=COLORS["player"],
        name="Player",
        blocks=True,
        hp=10,
        max_hp=10,
    )

    fov = FOVSystem(radius=3).compute(dungeon_map, player.x, player.y)
    explored = fov.copy()

    class ConsoleLikeRenderer:
        def __init__(self, console):
            self.console = console

        def print(self, x, y, text, color):
            self.console.print(x, y, text, fg=color)

    console = tcod.console.Console(width, height)
    ui = UI(
        renderer=ConsoleLikeRenderer(console),
        config={
            "display": {"width": width, "height": height},
            "dungeon": {"width": width, "height": height},
        },
    )

    ui.render_dungeon(dungeon_map, fov, explored)
    ui.render_entities([player], fov, player)

    tileset_path = Path(__file__).parents[1] / "assets" / "tilesets" / "proper_ascii_tileset.png"
    tileset = tcod.tileset.load_tilesheet(
        str(tileset_path),
        16,
        8,
        tcod.tileset.CHARMAP_TCOD,
    )
    context = tcod.context.new(columns=width, rows=height, tileset=tileset)

    try:
        context.present(console)
        screenshot_path = tmp_path / "rendered-map.png"
        context.save_screenshot(str(screenshot_path))

        assert screenshot_path.exists()
        assert screenshot_path.stat().st_size > 0
        assert console.ch[player.y, player.x] == ord("@")
        assert fov[player.x, player.y]
    finally:
        context.__exit__(None, None, None)
