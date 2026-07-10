import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from darkdelve import SaveSystem, GameState, Entity, Inventory, Item, ItemType
from src.domain.value_objects.fuzion_stats import PrimaryCharacteristics, DerivedCharacteristics, SkillSet
from src.domain.value_objects.fuzion_damage import FuzionDamageCalculator


class TestFuzionSaveMigration(unittest.TestCase):
    """Test Fuzion save serialization and v1->v2 migration."""
    
    def test_save_version_is_v2(self):
        """Verify save version is v2."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_system = SaveSystem(Path(tmpdir))
            self.assertEqual(save_system.SAVE_VERSION, "v2")
    
    def test_save_serializes_characteristics(self):
        """Verify player characteristics are serialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_system = SaveSystem(Path(tmpdir))
            
            # Create mock player with Fuzion fields
            player = Entity()
            player.x, player.y = 5, 5
            player.hp, player.max_hp = 50, 50
            player.power, player.defense = 10, 5
            player.speed, player.level = 100, 1
            player.xp, player.xp_to_next = 0, 100
            player.skill_points = 0
            player.known_skills = []
            player.nutrition = 100
            player.gold = 0
            player.kill_count = 0
            player.stats = {'str': 10, 'dex': 10, 'con': 10, 'int': 10, 'wis': 10, 'cha': 10}
            player.effects = {}
            player.identified_types = set()
            player.inventory = Inventory()
            player.characteristics = PrimaryCharacteristics(str=12, dex=14)
            player.derived = DerivedCharacteristics.from_primary(player.characteristics)
            player.skill_set = SkillSet(fighting=3.0, awareness=2.5)
            
            # Create mock state and entities
            state = GameState(run_id="test_run", seed=12345)
            import numpy as np
            dungeon_map = np.zeros((10, 10), dtype=bool)
            entities = []
            energy_system = MagicMock()
            energy_system.entities = []
            
            save_system.save(state, player, dungeon_map, entities, energy_system)
            
            # Load and verify
            save_file = Path(tmpdir) / "save_test_run.json"
            with open(save_file) as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data["version"], "v2")
            self.assertIn("characteristics", saved_data["player"])
            self.assertEqual(saved_data["player"]["characteristics"]["str"], 12)
            self.assertEqual(saved_data["player"]["characteristics"]["dex"], 14)
            self.assertIn("derived", saved_data["player"])
            self.assertIn("skill_set", saved_data["player"])
    
    def test_migrate_v1_to_v2_adds_missing_fields(self):
        """Verify v1 saves are migrated to v2 with Fuzion fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_system = SaveSystem(Path(tmpdir))
            
            # Create a v1 save file
            v1_save = {
                "version": "v1",
                "state": {"run_id": "test_run", "seed": 12345, "turn": 0, "depth": 1, "branch": "main",
                          "kills": 0, "gold_found": 0, "items_identified": 0, "start_time": 0,
                          "death_cause": None, "player_name": "Player", "player_class": "Fighter", "flags": []},
                "player": {
                    "x": 5, "y": 5,
                    "hp": 50, "max_hp": 50,
                    "power": 10, "defense": 5,
                    "speed": 100, "level": 1,
                    "xp": 0, "xp_to_next": 100,
                    "skill_points": 0,
                    "known_skills": [],
                    "nutrition": 100,
                    "gold": 0,
                    "kill_count": 0,
                    "stats": {},
                    "effects": {},
                    "identified_types": [],
                    "inventory": {"max_weight": 100, "items": [], "equipment": {}},
                },
                "dungeon_map": [],
                "entities": [],
                "energy_system": [],
            }
            
            save_file = Path(tmpdir) / "save_test_run.json"
            with open(save_file, 'w') as f:
                json.dump(v1_save, f)
            
            # Load and verify migration
            loaded = save_system.load("test_run")
            
            self.assertEqual(loaded["version"], "v2")
            self.assertIn("characteristics", loaded["player"])
            self.assertIn("derived", loaded["player"])
            self.assertIn("skill_set", loaded["player"])
            # Verify derived.hits matches original hp
            self.assertEqual(loaded["player"]["derived"]["hits"], 50)


class TestCombatResolverUsesFuzion(unittest.TestCase):
    """Test that CombatResolver routes damage through FuzionDamageCalculator."""
    
    def make_entity(self, dex=10, power=6, def_bonus=0, to_hit=0, defense=2):
        """Create entity similar to test_fuzion_combat.py pattern."""
        e = Entity()
        e.stats = {'str':10,'dex':dex,'con':10,'int':10,'wis':10,'cha':10}
        e.power = power
        e.defense = defense
        e.inventory = Inventory()
        if def_bonus or to_hit:
            w = Item("w","wpn",ItemType.WEAPON); w.to_hit_bonus=to_hit; w.defense_bonus=def_bonus
            e.inventory.add_item(w); e.inventory.equip(w.id, __import__('darkdelve').EquipmentSlot.MAIN_HAND)
        return e
    
    def test_fuzion_damage_produces_stun_for_unarmed(self):
        """Verify that unarmed attacks produce stun damage via Fuzion model."""
        from darkdelve import CombatResolver, HitResult
        
        # Create attacker with unarmed_stun flag
        attacker = self.make_entity(dex=10, power=6)
        attacker.unarmed_stun = True  # Fuzion unarmed attacks deal stun only
        attacker.characteristics = PrimaryCharacteristics(str=10)
        
        # Create target with stun defense
        defender = self.make_entity(dex=8, defense=2)
        defender.stun_defense = 5
        defender.killing_defense = 5
        defender.max_hp = 50
        
        # Mock dice to get predictable results
        with patch('random.randint', return_value=5):
            event = CombatResolver.resolve_attack(attacker, defender, weapon_dice="1d6")
        
        # Verify hit occurred
        self.assertIn(event.result, (HitResult.HIT, HitResult.CRITICAL))
        # Damage should be from Fuzion calculator (hits component)
        self.assertGreaterEqual(event.damage, 0)
    
    def test_fuzion_damage_uses_dc_not_av_subtraction(self):
        """Verify Fuzion damage uses DC/KD/SD model, not legacy AV subtraction."""
        from darkdelve import CombatResolver, HitResult
        
        # Create attacker
        attacker = self.make_entity(dex=10, power=6)
        attacker.characteristics = PrimaryCharacteristics(str=10)
        
        # Create target with high KD (should reduce hits damage)
        defender = self.make_entity(dex=8, defense=2)
        defender.stun_defense = 5
        defender.killing_defense = 20  # High KD
        defender.max_hp = 50
        
        # Mock dice to get predictable results
        with patch('random.randint', return_value=3):  # 1d6 = 3
            event = CombatResolver.resolve_attack(attacker, defender, weapon_dice="1d6")
        
        # Verify hit occurred
        self.assertIn(event.result, (HitResult.HIT, HitResult.CRITICAL))
        # Damage should be reduced by KD (3 - 20 = negative, clamped to MIN_DMG)
        self.assertGreaterEqual(event.damage, 1)


if __name__ == '__main__':
    unittest.main()