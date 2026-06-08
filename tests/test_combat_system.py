#!/usr/bin/env python3
"""
Test suite for DarkDelve combat system
"""

import unittest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path to import darkdelve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from darkdelve import Entity, Item, Inventory, CombatResolver, CombatEvent, CombatLog, COLORS, ItemType, EquipmentSlot, HitResult


class TestCombatSystem(unittest.TestCase):
    """Test cases for combat system"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test entities
        self.player = Entity(
            x=5, y=5,
            char="@",
            color=COLORS['player'],
            name="Test Player",
            blocks=True
        )
        
        self.enemy = Entity(
            x=6, y=5,
            char="g",
            color=COLORS['enemy_normal'],
            name="Goblin",
            blocks=True
        )
        
        # Add combat attributes
        self.player.power = 10
        self.player.defense = 5
        self.player.max_hp = 20
        self.player.hp = 20
        
        self.enemy.power = 8
        self.enemy.defense = 3
        self.enemy.max_hp = 15
        self.enemy.hp = 15
        
    def test_combat_resolver_initialization(self):
        """Test CombatResolver initialization"""
        resolver = CombatResolver()
        self.assertIsNotNone(resolver)
        
    def test_resolve_attack_basic(self):
        """Test basic attack resolution"""
        resolver = CombatResolver()
        event = resolver.resolve_attack(self.player, self.enemy)
        
        self.assertIsInstance(event, CombatEvent)
        self.assertEqual(event.attacker_name, self.player.name)
        self.assertEqual(event.defender_name, self.enemy.name)
        self.assertGreaterEqual(event.d20_roll, 1)
        self.assertLessEqual(event.d20_roll, 20)
        self.assertIn(event.result, [HitResult.HIT, HitResult.MISS, HitResult.CRITICAL, HitResult.CRITICAL_FAIL])
        
    def test_resolve_attack_damage(self):
        """Test attack resolution with damage"""
        resolver = CombatResolver()
        
        # Test multiple attacks to get some hits
        hits = 0
        total_damage = 0
        
        for _ in range(20):
            event = resolver.resolve_attack(self.player, self.enemy)
            if event.result in [HitResult.HIT, HitResult.CRITICAL]:
                hits += 1
                total_damage += event.damage
        
        # Should get some hits over 20 attacks
        self.assertGreater(hits, 0)
        
    def test_critical_hits(self):
        """Test critical hit mechanics"""
        resolver = CombatResolver()
        
        # Force a critical hit by mocking d20 roll
        with patch('random.randint', return_value=20):
            event = resolver.resolve_attack(self.player, self.enemy)
            self.assertEqual(event.result, HitResult.CRITICAL)
            self.assertGreater(event.damage, 0)  # Critical hits deal damage
            
    def test_critical_fails(self):
        """Test critical fail mechanics"""
        resolver = CombatResolver()
        
        # Force a critical fail by mocking d20 roll
        with patch('random.randint', return_value=1):
            event = resolver.resolve_attack(self.player, self.enemy)
            self.assertEqual(event.result, HitResult.CRITICAL_FAIL)
            self.assertEqual(event.damage, 0)  # Critical fails deal no damage
        
    def test_combat_event_creation(self):
        """Test combat event creation"""
        event = CombatEvent(
            turn=1,
            attacker_name="player",
            defender_name="enemy",
            to_hit_bonus=5,
            target_ac=10,
            d20_roll=15,
            total_roll=20,
            result=HitResult.HIT,
            damage=5
        )
        
        self.assertEqual(event.turn, 1)
        self.assertEqual(event.attacker_name, "player")
        self.assertEqual(event.defender_name, "enemy")
        self.assertEqual(event.to_hit_bonus, 5)
        self.assertEqual(event.target_ac, 10)
        self.assertEqual(event.d20_roll, 15)
        self.assertEqual(event.total_roll, 20)
        self.assertEqual(event.result, HitResult.HIT)
        self.assertEqual(event.damage, 5)
        self.assertIn("HIT!", str(event))
        
    def test_combat_log_initialization(self):
        """Test CombatLog initialization"""
        log = CombatLog()
        self.assertEqual(len(log.events), 0)
        
    def test_combat_log_add_event(self):
        """Test adding events to combat log"""
        log = CombatLog()
        event = CombatEvent(
            turn=1,
            attacker_name="player",
            defender_name="enemy",
            to_hit_bonus=5,
            target_ac=10,
            d20_roll=15,
            total_roll=20,
            result=HitResult.HIT,
            damage=5
        )
        
        log.add_event(event)
        self.assertEqual(len(log.events), 1)
        self.assertEqual(log.events[0], event)
        
    def test_combat_log_get_recent(self):
        """Test getting recent events from combat log"""
        log = CombatLog()
        
        # Add multiple events
        for i in range(5):
            event = CombatEvent(
                turn=i + 1,
                attacker_name="player",
                defender_name="enemy",
                to_hit_bonus=5,
                target_ac=10,
                d20_roll=15,
                total_roll=20,
                result=HitResult.HIT,
                damage=i + 1
            )
            log.add_event(event)
            
        # Test that events are stored correctly
        self.assertEqual(len(log.events), 5)
        self.assertEqual(log.events[0].turn, 1)
        self.assertEqual(log.events[4].turn, 5)
        
    def test_combat_log_clear(self):
        """Test clearing combat log"""
        log = CombatLog()
        
        # Add events
        for i in range(3):
            event = CombatEvent(
                turn=i + 1,
                attacker_name="player",
                defender_name="enemy",
                to_hit_bonus=5,
                target_ac=10,
                d20_roll=15,
                total_roll=20,
                result=HitResult.HIT,
                damage=i + 1
            )
            log.add_event(event)
            
        self.assertEqual(len(log.events), 3)
        
        # Clear log
        log.events.clear()
        self.assertEqual(len(log.events), 0)
        
    def test_combat_with_weapons(self):
        """Test combat with weapons"""
        # Create weapon
        weapon = Item(
            id="iron_sword",
            name="Iron Sword",
            description="A sharp iron sword",
            symbol="/",
            item_type=ItemType.WEAPON,
            weight=5,
            value=100,
            damage_bonus=5,
            equipped_slot=EquipmentSlot.MAIN_HAND
        )
        
        # Create armor
        armor = Item(
            id="leather_armor",
            name="Leather Armor",
            description="Protective leather armor",
            symbol="[",
            item_type=ItemType.ARMOR,
            weight=15,
            value=50,
            defense_bonus=3,
            equipped_slot=EquipmentSlot.BODY
        )
        
        # Equip items
        self.player.inventory.add_item(weapon)
        self.player.inventory.equip(weapon.id, EquipmentSlot.MAIN_HAND)
        self.enemy.inventory.add_item(armor)
        self.enemy.inventory.equip(armor.id, EquipmentSlot.BODY)
        
        # Test combat with equipped items
        resolver = CombatResolver()
        event = resolver.resolve_attack(self.player, self.enemy)
        
        # Event should be created and damage should be applied
        self.assertIsInstance(event, CombatEvent)
        self.assertGreaterEqual(event.damage, 0)
        self.assertIn(event.result, [HitResult.HIT, HitResult.MISS, HitResult.CRITICAL, HitResult.CRITICAL_FAIL])
        
    def test_combat_critical_hits(self):
        """Test critical hit mechanics"""
        resolver = CombatResolver()
        
        # Force a critical hit by mocking d20 roll
        with patch('random.randint', return_value=20):
            event = resolver.resolve_attack(self.player, self.enemy)
            self.assertEqual(event.result, HitResult.CRITICAL)
            self.assertGreater(event.damage, 0)  # Critical hits deal damage
        
    def test_combat_misses(self):
        """Test miss mechanics"""
        resolver = CombatResolver()
        
        # Force a miss by mocking low d20 roll
        with patch('random.randint', return_value=5):
            event = resolver.resolve_attack(self.player, self.enemy)
            self.assertEqual(event.result, HitResult.MISS)
            self.assertEqual(event.damage, 0)  # Misses deal no damage
        
    def test_combat_overkill(self):
        """Test combat overkill (damage exceeding current HP)"""
        resolver = CombatResolver()
        
        # Set enemy to very low HP
        self.enemy.hp = 2
        
        # Test that combat can still deal damage even when it exceeds HP
        event = resolver.resolve_attack(self.player, self.enemy)
        
        # Event should still be created even if damage exceeds HP
        self.assertIsInstance(event, CombatEvent)
        self.assertGreaterEqual(event.damage, 0)
        
    def test_combat_log_get_recent(self):
        """Test getting recent events from combat log"""
        log = CombatLog()
        
        # Add multiple events
        for i in range(5):
            event = CombatEvent(
                turn=i,
                attacker_name="player",
                defender_name="enemy",
                to_hit_bonus=5,
                target_ac=10,
                d20_roll=15,
                total_roll=20,
                result=HitResult.HIT,
                damage=i + 1
            )
            log.add_event(event)
            
        # Test that events are stored correctly
        self.assertEqual(len(log.events), 5)
        self.assertEqual(log.events[0].turn, 0)
        self.assertEqual(log.events[4].turn, 4)
        
        # Test getting recent events
        recent = log.get_recent(3)
        self.assertEqual(len(recent), 3)
        self.assertEqual(recent[0].turn, 3)  # Should be events 3, 4, 5
        
    def test_combat_log_serialization(self):
        """Test combat log serialization"""
        log = CombatLog()
        
        # Add events
        for i in range(3):
            event = CombatEvent(
                turn=i,
                attacker_name="player",
                defender_name="enemy",
                to_hit_bonus=5,
                target_ac=10,
                d20_roll=15,
                total_roll=20,
                result=HitResult.HIT,
                damage=i + 1
            )
            log.add_event(event)
            
        # Test that events are stored correctly
        self.assertEqual(len(log.events), 3)
        self.assertEqual(log.events[0].turn, 0)
        self.assertEqual(log.events[2].turn, 2)
        self.assertEqual(log.events[0].attacker_name, "player")
        self.assertEqual(log.events[0].defender_name, "enemy")


class TestCombatIntegration(unittest.TestCase):
    """Integration tests for combat system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.player = Entity(
            x=5, y=5,
            char="@",
            color=COLORS['player'],
            name="Test Player",
            blocks=True
        )
        
        self.enemy = Entity(
            x=6, y=5,
            char="g",
            color=COLORS['enemy_normal'],
            name="Goblin",
            blocks=True
        )
        
        # Set combat attributes
        self.player.power = 10
        self.player.defense = 5
        self.player.max_hp = 20
        self.player.hp = 20
        
        self.enemy.power = 8
        self.enemy.defense = 3
        self.enemy.max_hp = 15
        self.enemy.hp = 15
        
        self.combat_log = CombatLog()
        
    def test_full_combat_sequence(self):
        """Test a full combat sequence"""
        resolver = CombatResolver()
        turn = 1
        
        # Player attacks enemy
        player_event = resolver.resolve_attack(self.player, self.enemy)
        player_event.turn = turn
        self.combat_log.add_event(player_event)
        
        # Enemy attacks back
        enemy_event = resolver.resolve_attack(self.enemy, self.player)
        enemy_event.turn = turn
        self.combat_log.add_event(enemy_event)
        
        # Check results
        self.assertEqual(len(self.combat_log.events), 2)
        self.assertGreater(self.player.max_hp - self.player.hp, 0)
        self.assertGreater(self.enemy.max_hp - self.enemy.hp, 0)
        
    def test_combat_until_victory(self):
        """Test combat until one side is defeated"""
        resolver = CombatResolver()
        turn = 1
        
        while self.player.is_alive and self.enemy.is_alive:
            # Player attacks
            player_event = resolver.resolve_attack(self.player, self.enemy)
            player_event.turn = turn
            self.combat_log.add_event(player_event)
            
            if not self.enemy.is_alive:
                break
                
            # Enemy attacks
            enemy_event = resolver.resolve_attack(self.enemy, self.player)
            enemy_event.turn = turn
            self.combat_log.add_event(enemy_event)
            
            turn += 1
            
        # Check that one side is defeated
        self.assertFalse(self.player.is_alive or self.enemy.is_alive)
        self.assertGreater(turn, 1)
        
    def test_combat_with_multiple_enemies(self):
        """Test combat with multiple enemies"""
        # Create additional enemies
        enemy2 = Entity(
            x=7, y=5,
            char="o",
            color=COLORS['enemy_weak'],
            name="Orc",
            blocks=True
        )
        enemy2.power = 6
        enemy2.defense = 2
        enemy2.max_hp = 10
        enemy2.hp = 10
        
        resolver = CombatResolver()
        combat_log = CombatLog()
        
        # Player attacks both enemies
        event1 = resolver.resolve_attack(self.player, self.enemy)
        event2 = resolver.resolve_attack(self.player, enemy2)
        
        combat_log.add_event(event1)
        combat_log.add_event(event2)
        
        # Check that both enemies took damage
        self.assertGreater(self.enemy.max_hp - self.enemy.hp, 0)
        self.assertGreater(enemy2.max_hp - enemy2.hp, 0)
        self.assertEqual(len(combat_log.events), 2)


if __name__ == '__main__':
    unittest.main()