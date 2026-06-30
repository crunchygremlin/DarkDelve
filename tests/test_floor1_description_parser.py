"""Tests for floor 1 LLM description parser."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from src.application.services.floor1_description_parser import (
    parse_floor1_description,
    _extract_monster_counts,
    _extract_feature_counts,
    MONSTER_KEYWORDS,
    FEATURE_KEYWORDS,
)
from src.application.services.floor1_generator import Floor1Generator, Floor1Data


@pytest.fixture
def config():
    return {
        'dungeon': {'width': 60, 'height': 40},
        'floor1': {
            'corpse_chance': 0.5,
            'guard_patrol_count': 3,
            'den_count': 4,
            'roaming_creature_count': 5,
            'main_path_width': 3,
        }
    }


@pytest.fixture
def base_floor1_data(config):
    gen = Floor1Generator(config)
    return gen.generate()


class TestExtractMonsterCounts:

    def test_spider_mention(self):
        desc = "A spider den webs across the chamber. The spider guards its prey."
        counts = _extract_monster_counts(desc)
        assert "giant_spider" in counts
        assert counts["giant_spider"] >= 2

    def test_guard_mention(self):
        desc = "Guard patrols march between watch posts. A sergeant commands them."
        counts = _extract_monster_counts(desc)
        assert "dungeon_guard" in counts
        assert "guard_sergeant" in counts

    def test_multiple_types(self):
        desc = "Spiders weave webs. Guards patrol the corridor. Rats scurry in the dark."
        counts = _extract_monster_counts(desc)
        assert "giant_spider" in counts
        assert "dungeon_guard" in counts
        assert "cave_rat" in counts

    def test_empty_description(self):
        counts = _extract_monster_counts("")
        assert len(counts) == 0

    def test_no_monsters(self):
        desc = "A cold stone corridor descends into darkness."
        counts = _extract_monster_counts(desc)
        assert len(counts) == 0

    def test_rat_king_mention(self):
        desc = "The rat king rules the nest. Many cave rats serve him."
        counts = _extract_monster_counts(desc)
        assert "rat_king" in counts
        assert "cave_rat" in counts


class TestExtractFeatureCounts:

    def test_corpse_mention(self):
        desc = "Corpses of adventurers lie scattered. Their bones tell a grim tale."
        counts = _extract_feature_counts(desc)
        assert "corpse" in counts

    def test_stairs_mention(self):
        desc = "The stairs down are guarded. The stairwell is dark."
        counts = _extract_feature_counts(desc)
        assert "stairs" in counts

    def test_patrol_mention(self):
        desc = "Guard patrols march. Watch posts are everywhere."
        counts = _extract_feature_counts(desc)
        assert "patrol" in counts

    def test_empty_description(self):
        counts = _extract_feature_counts("")
        assert len(counts) == 0


class TestParseFloor1Description:

    def test_empty_description_returns_unchanged(self, base_floor1_data, config):
        original_dens = len(base_floor1_data.dens)
        result = parse_floor1_description("", base_floor1_data, base_floor1_data.dungeon_map, config)
        assert len(result.dens) == original_dens

    def test_none_description_returns_unchanged(self, base_floor1_data, config):
        original_dens = len(base_floor1_data.dens)
        result = parse_floor1_description(None, base_floor1_data, base_floor1_data.dungeon_map, config)
        assert len(result.dens) == original_dens

    def test_spider_mention_adds_den(self, base_floor1_data, config):
        desc = "The spider den is everywhere. Spiders web across every chamber. Giant spiders lurk in shadows."
        original_dens = len(base_floor1_data.dens)
        result = parse_floor1_description(desc, base_floor1_data, base_floor1_data.dungeon_map, config)
        assert len(result.dens) >= original_dens

    def test_corpse_mention_adds_corpses(self, base_floor1_data, config):
        desc = "Corpses of fallen adventurers litter the floor. Their remains tell grim tales. Bones everywhere."
        original_corpses = len(base_floor1_data.corpses)
        result = parse_floor1_description(desc, base_floor1_data, base_floor1_data.dungeon_map, config)
        assert len(result.corpses) >= original_corpses

    def test_patrol_mention_adds_patrol(self, base_floor1_data, config):
        desc = "Guard patrols march endlessly. Patrol routes cover every corridor. Watch posts everywhere."
        original_patrols = len(base_floor1_data.patrol_routes)
        result = parse_floor1_description(desc, base_floor1_data, base_floor1_data.dungeon_map, config)
        assert len(result.patrol_routes) >= original_patrols

    def test_result_is_floor1_data(self, base_floor1_data, config):
        desc = "A standard dungeon entrance."
        result = parse_floor1_description(desc, base_floor1_data, base_floor1_data.dungeon_map, config)
        assert isinstance(result, Floor1Data)

    def test_map_bounds_respected(self, base_floor1_data, config):
        desc = "Spiders everywhere. Corpses everywhere. Patrols everywhere."
        result = parse_floor1_description(desc, base_floor1_data, base_floor1_data.dungeon_map, config)
        for den in result.dens:
            assert 0 <= den.center[0] < config["dungeon"]["width"]
            assert 0 <= den.center[1] < config["dungeon"]["height"]
