"""Test that runtime player Entity has Fuzion fields for save/load round-trip."""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock

from darkdelve import SaveSystem, GameState, Entity, Inventory, Item, ItemType, Game
from src.domain.value_objects.fuzion_stats import PrimaryCharacteristics, DerivedCharacteristics, SkillSet


class TestFuzionRuntimePlayerFields(unittest.TestCase):
    """Test that player created via Game.create_player() has Fuzion fields."""

    def test_player_has_characteristics_after_create(self):
        """Verify that runtime player has characteristics attribute after creation."""
        # Create a game and call create_player
        game = Game()
        game.state = GameState()
        game.state.player_class = "warrior"
        game.state.player_name = "TestPlayer"
        
        # Mock the config to avoid full initialization
        game.config = {
            'classes': {
                'warrior': {
                    'hp_per_level': 10,
                    'stats': {'str': 12, 'dex': 10, 'con': 12, 'int': 10, 'wis': 10, 'cha': 10},
                    'start_gear': []
                }
            },
            'gameplay': {'max_nutrition': 2000}
        }
        
        game.create_player()
        
        # Verify Fuzion fields exist
        self.assertTrue(hasattr(game.player, 'characteristics'), "Player should have characteristics attribute")
        self.assertTrue(hasattr(game.player, 'derived'), "Player should have derived attribute")
        self.assertTrue(hasattr(game.player, 'skill_set'), "Player should have skill_set attribute")
        
        # Verify types
        self.assertIsInstance(game.player.characteristics, PrimaryCharacteristics)
        self.assertIsInstance(game.player.derived, DerivedCharacteristics)
        self.assertIsInstance(game.player.skill_set, SkillSet)

    def test_player_characteristics_body_default(self):
        """Verify that player characteristics.body has default value of 10."""
        game = Game()
        game.state = GameState()
        game.state.player_class = "warrior"
        game.state.player_name = "TestPlayer"
        game.config = {
            'classes': {
                'warrior': {
                    'hp_per_level': 10,
                    'stats': {'str': 12, 'dex': 10, 'con': 12, 'int': 10, 'wis': 10, 'cha': 10},
                    'start_gear': []
                }
            },
            'gameplay': {'max_nutrition': 2000}
        }
        
        game.create_player()
        
        # Verify default body value
        self.assertEqual(game.player.characteristics.body, 10)

    def test_save_load_round_trip_preserves_characteristics(self):
        """Verify that characteristics survive save/load round-trip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_system = SaveSystem(Path(tmpdir))
            
            # Create a game and player
            game = Game()
            game.state = GameState(run_id="test_fuzion_rt")
            game.state.player_class = "warrior"
            game.state.player_name = "TestPlayer"
            game.config = {
                'classes': {
                    'warrior': {
                        'hp_per_level': 10,
                        'stats': {'str': 12, 'dex': 10, 'con': 12, 'int': 10, 'wis': 10, 'cha': 10},
                        'start_gear': []
                    }
                },
                'gameplay': {'max_nutrition': 2000}
            }
            
            game.create_player()
            
            # Modify characteristics to non-default value
            game.player.characteristics = PrimaryCharacteristics(str=14, dex=12, body=15)
            game.player.derived = DerivedCharacteristics.from_primary(game.player.characteristics)
            
            # Save
            import numpy as np
            dungeon_map = np.zeros((10, 10), dtype=bool)
            entities = []
            energy_system = MagicMock()
            energy_system.entities = []
            
            save_system.save(game.state, game.player, dungeon_map, entities, energy_system)
            
            # Load and verify
            save_file = Path(tmpdir) / "save_test_fuzion_rt.json"
            with open(save_file) as f:
                saved_data = json.load(f)
            
            # Verify characteristics were serialized
            self.assertIn("characteristics", saved_data["player"])
            self.assertEqual(saved_data["player"]["characteristics"]["str"], 14)
            self.assertEqual(saved_data["player"]["characteristics"]["dex"], 12)
            self.assertEqual(saved_data["player"]["characteristics"]["body"], 15)
            
            # Verify derived was serialized
            self.assertIn("derived", saved_data["player"])
            self.assertEqual(saved_data["player"]["derived"]["hits"], 75)  # body * 5
            
            # Verify skill_set was serialized
            self.assertIn("skill_set", saved_data["player"])

    def test_save_load_round_trip_preserves_skill_set(self):
        """Verify that skill_set survives save/load round-trip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_system = SaveSystem(Path(tmpdir))
            
            # Create a game and player
            game = Game()
            game.state = GameState(run_id="test_skill_rt")
            game.state.player_class = "warrior"
            game.state.player_name = "TestPlayer"
            game.config = {
                'classes': {
                    'warrior': {
                        'hp_per_level': 10,
                        'stats': {'str': 12, 'dex': 10, 'con': 12, 'int': 10, 'wis': 10, 'cha': 10},
                        'start_gear': []
                    }
                },
                'gameplay': {'max_nutrition': 2000}
            }
            
            game.create_player()
            
            # Modify skill_set
            game.player.skill_set = SkillSet(fighting=5.0, awareness=4.0, body=3.0)
            
            # Save
            import numpy as np
            dungeon_map = np.zeros((10, 10), dtype=bool)
            entities = []
            energy_system = MagicMock()
            energy_system.entities = []
            
            save_system.save(game.state, game.player, dungeon_map, entities, energy_system)
            
            # Load and verify
            save_file = Path(tmpdir) / "save_test_skill_rt.json"
            with open(save_file) as f:
                saved_data = json.load(f)
            
            # Verify skill_set was serialized with custom values
            self.assertIn("skill_set", saved_data["player"])
            self.assertEqual(saved_data["player"]["skill_set"]["fighting"], 5.0)
            self.assertEqual(saved_data["player"]["skill_set"]["awareness"], 4.0)
            self.assertEqual(saved_data["player"]["skill_set"]["body"], 3.0)


if __name__ == '__main__':
    unittest.main()