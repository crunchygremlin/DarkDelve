"""Regression tests for map rendering stability and visual output."""

import os
from pathlib import Path
from unittest.mock import patch

import numpy as np
import tcod

from darkdelve import COLORS, Entity, FOVSystem, UI
from src.presentation.renderer import ConsoleRenderer


def test_fov_uses_dungeon_x_y_coordinates_for_off_diagonal_player():
    """FOV must be centered on the player's dungeon [x, y], not swapped."""
    dungeon_map = np.zeros((6, 5), dtype=bool)

    fov = FOVSystem(radius=2).compute(dungeon_map, player_x=4, player_y=1)

    assert fov[4, 1]
    assert fov[3, 1]
    assert fov[4, 0]
    assert not fov[0, 0]


def test_console_renderer_present_does_not_print_a_full_frame():
    """The console renderer should not visibly refresh by dumping the console."""
    renderer = ConsoleRenderer(tcod.console.Console(5, 3))

    with patch("builtins.print") as mocked_print:
        renderer.present()

    mocked_print.assert_not_called()


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
