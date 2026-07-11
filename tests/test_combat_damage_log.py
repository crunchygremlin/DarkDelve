#!/usr/bin/env python3
"""
Tests for CombatDamageLog persistence.
"""

import unittest
import sys
import os
import json
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.persistence.combat_damage_log import CombatDamageLog, DamageEntry
from darkdelve import CombatEvent, HitResult, Entity


class TestDamageEntry(unittest.TestCase):
    """Test DamageEntry dataclass creation."""
    
    def test_damage_entry_creation(self):
        entry = DamageEntry(
            timestamp="2026-06-27T05:18:10.858Z",
            turn=1,
            attacker_name="Player",
            defender_name="Goblin",
            damage=8,
            hit=True,
            critical=False,
            event_type="hit",
            flavor_text="Player attacks Goblin! HIT! Damage: 8"
        )
        self.assertEqual(entry.attacker_name, "Player")
        self.assertEqual(entry.damage, 8)
        self.assertTrue(entry.hit)
        self.assertFalse(entry.critical)
    
    def test_damage_entry_asdict(self):
        entry = DamageEntry(
            timestamp="2026-06-27T05:18:10.858Z",
            turn=0,
            attacker_name="Player",
            defender_name="Goblin",
            damage=0,
            hit=False,
            critical=False,
            event_type="miss",
            flavor_text="Player attacks Goblin... MISS!"
        )
        d = entry.__dict__
        self.assertEqual(d["event_type"], "miss")
        self.assertEqual(d["damage"], 0)
        self.assertFalse(d["hit"])


class TestCombatDamageLogRecordEvent(unittest.TestCase):
    """Test recording events into the log."""
    
    def setUp(self):
        self.log = CombatDamageLog(output_dir=tempfile.mkdtemp())
    
    def tearDown(self):
        shutil.rmtree(self.log.output_dir, ignore_errors=True)
    
    def _make_event(self, attacker_name="Player", defender_name="Goblin",
                    result=HitResult.HIT, damage=5, turn=1):
        return CombatEvent(
            turn=turn,
            attacker_name=attacker_name,
            defender_name=defender_name,
            to_hit_bonus=2,
            target_ac=12,
            d20_roll=13,
            total_roll=15,
            result=result,
            damage=damage,
        )
    
    def _make_entity(self, name, x=0, y=0):
        return Entity(
            x=x, y=y, char="@", color=(255, 255, 0),
            name=name, blocks=True, hp=20, max_hp=20,
            power=5, defense=2, speed=100,
        )
    
    def test_record_hit(self):
        event = self._make_event(result=HitResult.HIT, damage=8)
        attacker = self._make_entity("Player")
        defender = self._make_entity("Goblin")
        
        self.log.record_event(event, attacker, defender)
        
        self.assertEqual(len(self.log.entries), 1)
        self.assertEqual(self.log.entries[0].damage, 8)
        self.assertTrue(self.log.entries[0].hit)
        self.assertFalse(self.log.entries[0].critical)
        self.assertEqual(self.log.entries[0].event_type, "hit")
    
    def test_record_miss(self):
        event = self._make_event(result=HitResult.MISS, damage=0)
        attacker = self._make_entity("Player")
        defender = self._make_entity("Goblin")
        
        self.log.record_event(event, attacker, defender)
        
        self.assertEqual(len(self.log.entries), 1)
        self.assertEqual(self.log.entries[0].damage, 0)
        self.assertFalse(self.log.entries[0].hit)
        self.assertEqual(self.log.entries[0].event_type, "miss")
    
    def test_record_critical(self):
        event = self._make_event(result=HitResult.CRITICAL, damage=16)
        attacker = self._make_entity("Player")
        defender = self._make_entity("Orc")
        
        self.log.record_event(event, attacker, defender)
        
        self.assertEqual(len(self.log.entries), 1)
        self.assertTrue(self.log.entries[0].critical)
        self.assertTrue(self.log.entries[0].hit)
        self.assertEqual(self.log.entries[0].event_type, "critical")
        self.assertEqual(self.log.entries[0].damage, 16)
    
    def test_record_critical_fail(self):
        event = self._make_event(result=HitResult.CRITICAL_FAIL, damage=0)
        attacker = self._make_entity("Player")
        defender = self._make_entity("Dragon")
        
        self.log.record_event(event, attacker, defender)
        
        self.assertEqual(len(self.log.entries), 1)
        self.assertFalse(self.log.entries[0].hit)
        self.assertEqual(self.log.entries[0].event_type, "critical_fail")
    
    def test_record_out_of_range(self):
        event = self._make_event(result=HitResult.MISS, damage=0)
        event.out_of_range = True
        attacker = self._make_entity("Player")
        defender = self._make_entity("Bat")
        
        self.log.record_event(event, attacker, defender)
        
        self.assertEqual(len(self.log.entries), 1)
        self.assertEqual(self.log.entries[0].event_type, "out_of_range")
    
    def test_record_multiple_events(self):
        attacker = self._make_entity("Player")
        defender = self._make_entity("Goblin")
        
        for i in range(5):
            event = self._make_event(result=HitResult.HIT, damage=3, turn=i)
            self.log.record_event(event, attacker, defender)
        
        self.assertEqual(len(self.log.entries), 5)
    
    def test_timestamp_is_iso_8601(self):
        event = self._make_event()
        attacker = self._make_entity("Player")
        defender = self._make_entity("Goblin")
        
        self.log.record_event(event, attacker, defender)
        
        ts = self.log.entries[0].timestamp
        # Should contain 'T' and end with 'Z' (ISO 8601 UTC)
        self.assertIn("T", ts)
        self.assertTrue(ts.endswith("Z"))
    
    def test_flavor_text_is_neutral_perspective(self):
        event = self._make_event(result=HitResult.HIT, damage=5)
        attacker = self._make_entity("Player")
        defender = self._make_entity("Goblin")
        
        self.log.record_event(event, attacker, defender)
        
        # Neutral perspective uses third-person: "attacks" not "Player attacks"
        self.assertIn("attacks Goblin", self.log.entries[0].flavor_text)


class TestCombatDamageLogExport(unittest.TestCase):
    """Test JSON export functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log = CombatDamageLog(output_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _make_event(self, attacker_name="Player", defender_name="Goblin",
                    result=HitResult.HIT, damage=5, turn=1):
        return CombatEvent(
            turn=turn,
            attacker_name=attacker_name,
            defender_name=defender_name,
            to_hit_bonus=2,
            target_ac=12,
            d20_roll=13,
            total_roll=15,
            result=result,
            damage=damage,
        )
    
    def _make_entity(self, name):
        return Entity(
            x=0, y=0, char="@", color=(255, 255, 0),
            name=name, blocks=True, hp=20, max_hp=20,
            power=5, defense=2, speed=100,
        )
    
    def test_export_creates_file(self):
        event = self._make_event()
        self.log.record_event(event, self._make_entity("Player"), self._make_entity("Goblin"))
        
        path = self.log.export_to_json(session_id="test123")
        
        self.assertTrue(os.path.exists(path))
        self.assertIn("combat_damage_test123.json", path)
    
    def test_export_valid_json(self):
        event = self._make_event()
        self.log.record_event(event, self._make_entity("Player"), self._make_entity("Goblin"))
        
        path = self.log.export_to_json(session_id="test456")
        
        with open(path) as f:
            data = json.load(f)
        
        self.assertIn("session_id", data)
        self.assertIn("total_entries", data)
        self.assertIn("exported_at", data)
        self.assertIn("summary", data)
        self.assertIn("entries", data)
        self.assertEqual(data["session_id"], "test456")
        self.assertEqual(data["total_entries"], 1)
    
    def test_export_entries_have_all_fields(self):
        event = self._make_event(result=HitResult.CRITICAL, damage=12)
        self.log.record_event(event, self._make_entity("Player"), self._make_entity("Orc"))
        
        path = self.log.export_to_json(session_id="test789")
        
        with open(path) as f:
            data = json.load(f)
        
        entry = data["entries"][0]
        required_fields = ["timestamp", "turn", "attacker_name", "defender_name",
                          "damage", "hit", "critical", "event_type", "flavor_text"]
        for field in required_fields:
            self.assertIn(field, entry, f"Missing field: {field}")
    
    def test_export_empty_log(self):
        path = self.log.export_to_json(session_id="empty_test")
        
        with open(path) as f:
            data = json.load(f)
        
        self.assertEqual(data["total_entries"], 0)
        self.assertEqual(data["entries"], [])
        self.assertEqual(data["summary"]["total_events"], 0)
    
    def test_export_creates_directory(self):
        new_dir = os.path.join(self.temp_dir, "new_subdir")
        log = CombatDamageLog(output_dir=new_dir)
        event = self._make_event()
        log.record_event(event, self._make_entity("Player"), self._make_entity("Goblin"))
        
        path = log.export_to_json(session_id="dir_test")
        
        self.assertTrue(os.path.exists(new_dir))
        self.assertTrue(os.path.exists(path))
    
    def test_export_json_is_human_readable(self):
        """Verify indent=2 formatting."""
        event = self._make_event()
        self.log.record_event(event, self._make_entity("Player"), self._make_entity("Goblin"))
        
        path = self.log.export_to_json(session_id="readable_test")
        
        with open(path) as f:
            content = f.read()
        
        # Should have indentation (indent=2)
        self.assertIn('  "session_id"', content)


class TestCombatDamageLogSummary(unittest.TestCase):
    """Test summary statistics calculation."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log = CombatDamageLog(output_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _make_event(self, attacker_name="Player", defender_name="Goblin",
                    result=HitResult.HIT, damage=5, turn=1):
        return CombatEvent(
            turn=turn,
            attacker_name=attacker_name,
            defender_name=defender_name,
            to_hit_bonus=2,
            target_ac=12,
            d20_roll=13,
            total_roll=15,
            result=result,
            damage=damage,
        )
    
    def _make_entity(self, name):
        return Entity(
            x=0, y=0, char="@", color=(255, 255, 0),
            name=name, blocks=True, hp=20, max_hp=20,
            power=5, defense=2, speed=100,
        )
    
    def test_summary_empty_log(self):
        summary = self.log.get_summary()
        
        self.assertEqual(summary["total_damage_dealt"], 0)
        self.assertEqual(summary["total_hits"], 0)
        self.assertEqual(summary["total_misses"], 0)
        self.assertEqual(summary["total_events"], 0)
    
    def test_summary_mixed_events(self):
        # 3 hits, 1 miss, 1 critical
        self.log.record_event(
            self._make_event(attacker_name="Player", defender_name="Goblin", result=HitResult.HIT, damage=5, turn=0),
            self._make_entity("Player"), self._make_entity("Goblin")
        )
        self.log.record_event(
            self._make_event(attacker_name="Player", defender_name="Goblin", result=HitResult.HIT, damage=3, turn=1),
            self._make_entity("Player"), self._make_entity("Goblin")
        )
        self.log.record_event(
            self._make_event(attacker_name="Player", defender_name="Goblin", result=HitResult.MISS, damage=0, turn=2),
            self._make_entity("Player"), self._make_entity("Goblin")
        )
        self.log.record_event(
            self._make_event(attacker_name="Player", defender_name="Orc", result=HitResult.CRITICAL, damage=12, turn=3),
            self._make_entity("Player"), self._make_entity("Orc")
        )
        self.log.record_event(
            self._make_event(attacker_name="Goblin", defender_name="Player", result=HitResult.HIT, damage=4, turn=4),
            self._make_entity("Goblin"), self._make_entity("Player")
        )
        
        summary = self.log.get_summary()
        
        self.assertEqual(summary["total_damage_dealt"], 24)  # 5+3+0+12+4
        self.assertEqual(summary["total_hits"], 4)           # CHANGED 3 -> 4 (3 HIT + 1 CRITICAL)
        self.assertEqual(summary["total_misses"], 1)
        self.assertEqual(summary["total_critical_hits"], 1)
        self.assertEqual(summary["total_events"], 5)
        self.assertIn("Player", summary["unique_attackers"])
        self.assertIn("Goblin", summary["unique_attackers"])
        self.assertIn("Goblin", summary["unique_defenders"])
        self.assertIn("Player", summary["unique_defenders"])
    
    def test_summary_only_misses(self):
        for i in range(3):
            self.log.record_event(
                self._make_event(result=HitResult.MISS, damage=0, turn=i),
                self._make_entity("Player"), self._make_entity("Bat")
            )
        
        summary = self.log.get_summary()
        
        self.assertEqual(summary["total_damage_dealt"], 0)
        self.assertEqual(summary["total_hits"], 0)
        self.assertEqual(summary["total_misses"], 3)

    def test_critical_counted_in_total_hits(self):
        event = self._make_event(result=HitResult.CRITICAL, damage=12, turn=0)
        self.log.record_event(event, self._make_entity("Player"), self._make_entity("Orc"))
        summary = self.log.get_summary()
        self.assertEqual(summary["total_hits"], 1)

    def test_hit_event_is_consistent(self):
        event = self._make_event(result=HitResult.HIT, damage=5, turn=0)
        self.log.record_event(event, self._make_entity("Player"), self._make_entity("Goblin"))
        summary = self.log.get_summary()
        self.assertEqual(summary["total_hits"], 1)
        self.assertEqual(len(self.log.entries), 1)
        self.assertTrue(self.log.entries[0].hit)
        self.assertEqual(self.log.entries[0].event_type, "hit")


class TestCombatDamageLogClear(unittest.TestCase):
    """Test clearing the log."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log = CombatDamageLog(output_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_clear_empties_entries(self):
        event = CombatEvent(
            turn=0, attacker_name="Player", defender_name="Goblin",
            to_hit_bonus=2, target_ac=12, d20_roll=13, total_roll=15,
            result=HitResult.HIT, damage=5,
        )
        entity = Entity(
            x=0, y=0, char="@", color=(255, 255, 0),
            name="Player", blocks=True, hp=20, max_hp=20,
            power=5, defense=2, speed=100,
        )
        
        self.log.record_event(event, entity, entity)
        self.assertEqual(len(self.log.entries), 1)
        
        self.log.clear()
        self.assertEqual(len(self.log.entries), 0)


class TestIntegrationWithGame(unittest.TestCase):
    """Test that Game.attack() records to combat_damage_log."""
    
    def setUp(self):
        from darkdelve import Game
        self.game = Game()
        self.game.combat_damage_log = CombatDamageLog(output_dir=tempfile.mkdtemp())
    
    def tearDown(self):
        shutil.rmtree(self.game.combat_damage_log.output_dir, ignore_errors=True)
    
    def test_attack_records_to_damage_log(self):
        """Game.attack() should add an entry to combat_damage_log."""
        player = Entity(
            x=0, y=0, char="@", color=(255, 255, 0),
            name="Player", blocks=True, hp=20, max_hp=20,
            power=5, defense=2, speed=100,
        )
        goblin = Entity(
            x=1, y=0, char="g", color=(100, 200, 100),
            name="Goblin", blocks=True, hp=10, max_hp=10,
            power=3, defense=1, speed=100,
        )
        self.game.player = player
        self.game.combat_log = type('obj', (object,), {
            'events': [],
            'add_event': lambda self, e: self.events.append(e),
            'get_recent': lambda self, n: self.events[-n:],
        })()
        
        # Mock CombatResolver to return a known event
        from darkdelve import CombatResolver, CombatEvent, HitResult
        original_resolve = CombatResolver.resolve_attack
        mock_event = CombatEvent(
            turn=0, attacker_name="Player", defender_name="Goblin",
            to_hit_bonus=2, target_ac=12, d20_roll=15, total_roll=17,
            result=HitResult.HIT, damage=6,
        )
        CombatResolver.resolve_attack = staticmethod(lambda a, b: mock_event)
        
        try:
            self.game.attack(player, goblin)
        finally:
            CombatResolver.resolve_attack = original_resolve
        
        # Verify combat_damage_log has the entry
        self.assertEqual(len(self.game.combat_damage_log.entries), 1)
        self.assertEqual(self.game.combat_damage_log.entries[0].attacker_name, "Player")
        self.assertEqual(self.game.combat_damage_log.entries[0].defender_name, "Goblin")
        self.assertEqual(self.game.combat_damage_log.entries[0].damage, 6)
        self.assertTrue(self.game.combat_damage_log.entries[0].hit)


if __name__ == '__main__':
    unittest.main(verbosity=2)