"""Tests for floor 1 generation."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from src.application.services.floor1_generator import Floor1Generator, Floor1Data
from src.application.services.floor1_spawner import Floor1Spawner, MONSTER_TEMPLATES


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


class TestFloor1Generator:
    
    def test_generate_returns_floor1_data(self, config):
        gen = Floor1Generator(config)
        data = gen.generate()
        assert isinstance(data, Floor1Data)
    
    def test_main_path_is_clear(self, config):
        gen = Floor1Generator(config)
        data = gen.generate()
        
        # All positions in main path should be floor (False)
        for x, y in data.main_path:
            assert data.dungeon_map[x, y] == False
    
    def test_entrance_and_stairs_exist(self, config):
        gen = Floor1Generator(config)
        data = gen.generate()
        
        assert data.entrance is not None
        assert data.stair_down is not None
        assert data.entrance != data.stair_down
    
    def test_dens_placed(self, config):
        gen = Floor1Generator(config)
        data = gen.generate()
        
        assert len(data.dens) > 0
        assert len(data.dens) <= config['floor1']['den_count']
    
    def test_patrol_routes_created(self, config):
        gen = Floor1Generator(config)
        data = gen.generate()
        
        assert len(data.patrol_routes) > 0
    
    def test_stairs_reachable(self, config):
        """Verify path exists from entrance to stairs."""
        gen = Floor1Generator(config)
        data = gen.generate()
        
        # Import pathfinding
        from darkdelve import find_path
        
        path = find_path(data.entrance, data.stair_down, data.dungeon_map, [])
        assert len(path) > 1  # Should have actual path


class TestFloor1Spawner:
    
    @pytest.fixture
    def mock_player(self):
        player = MagicMock()
        player.speed = 100
        player.x = 30
        player.y = 2
        return player
    
    def test_spawn_all_returns_entities(self, mock_player, config):
        from src.application.services.floor1_generator import Floor1Generator
        
        gen = Floor1Generator(config)
        floor1_data = gen.generate()
        
        spawner = Floor1Spawner(mock_player, config)
        entities = spawner.spawn_all(floor1_data, None)
        
        assert len(entities) > 0
    
    def test_guard_patrols_spawned(self, mock_player, config):
        from src.application.services.floor1_generator import Floor1Generator
        
        gen = Floor1Generator(config)
        floor1_data = gen.generate()
        
        spawner = Floor1Spawner(mock_player, config)
        entities = spawner._spawn_guard_patrols(floor1_data)
        
        guards = [e for e in entities if e.name in ('Dungeon Guard', 'Guard Sergeant')]
        assert len(guards) >= 2  # At least one patrol of 2
    
    def test_den_creatures_spawned(self, mock_player, config):
        from src.application.services.floor1_generator import Floor1Generator
        
        gen = Floor1Generator(config)
        floor1_data = gen.generate()
        
        spawner = Floor1Spawner(mock_player, config)
        entities = spawner._spawn_den_creatures(floor1_data)
        
        creatures = [e for e in entities if e.name in ('Giant Spider', 'Spider Queen', 'Cave Rat', 'Rat King')]
        assert len(creatures) >= 2
    
    def test_monsters_weaker_than_player(self, mock_player, config):
        """All monsters should be weaker than starting player."""
        from src.application.services.floor1_generator import Floor1Generator
        
        mock_player.hp = 15
        mock_player.power = 5
        
        gen = Floor1Generator(config)
        floor1_data = gen.generate()
        
        spawner = Floor1Spawner(mock_player, config)
        entities = spawner.spawn_all(floor1_data, None)
        
        for entity in entities:
            assert entity.max_hp <= mock_player.hp + 5
            assert entity.power <= mock_player.power
    
    def test_corpses_have_loot(self, mock_player, config):
        from src.application.services.floor1_generator import Floor1Generator
        
        gen = Floor1Generator(config)
        floor1_data = gen.generate()
        
        spawner = Floor1Spawner(mock_player, config)
        entities = spawner._spawn_corpses(floor1_data)
        
        for entity in entities:
            if hasattr(entity, 'is_corpse') and entity.is_corpse:
                assert hasattr(entity, 'loot')
                # Some corpses may have empty loot list, that's ok


class TestMonsterTemplates:
    
    def test_all_templates_exist(self):
        required = [
            'dungeon_guard', 'guard_sergeant',
            'giant_spider', 'spider_queen',
            'cave_rat', 'rat_king',
            'troll_scavenger', 'fungal_creeper', 'cave_bat',
        ]
        for key in required:
            assert key in MONSTER_TEMPLATES
    
    def test_stats_are_low(self):
        """All floor 1 monsters should have low stats."""
        for key, template in MONSTER_TEMPLATES.items():
            assert template['hp'] <= 15, f"{key} has too much HP"
            assert template['power'] <= 3, f"{key} has too much power"

class TestFloor1ToFloor2Transition:
    
    def test_floor1_to_floor2_transition(self, config):
        """Verify descending from floor 1 to floor 2 works without crashes."""
        from darkdelve import Game
        
        game = Game()
        game.initialize()
        
        # Verify we are on floor 1
        assert game.state.depth == 1
        
        # Generate floor 2
        game.generate_level(2, "main")
        
        # Verify floor 2 has entities
        assert len(game.entities) > 0, "Floor 2 should have entities"
        
        # Verify floor 2 has a valid map
        assert game.dungeon_map is not None, "Floor 2 should have a dungeon map"
        assert game.dungeon_map.shape[0] > 0, "Floor 2 map should have width"
        assert game.dungeon_map.shape[1] > 0, "Floor 2 map should have height"
        
        # Verify depth updated
        assert game.state.depth == 2, "State depth should be 2 after transition"
        
        # Verify player still exists and is alive
        assert game.player is not None, "Player should exist on floor 2"
        assert game.player.is_alive, "Player should be alive on floor 2"
