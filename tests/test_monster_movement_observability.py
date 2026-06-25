#!/usr/bin/env python3
"""
Test suite for monster movement observability.
Tests that monsters move toward the player consistently using the Game class directly.
"""

import unittest
import numpy as np
import sys
import os

# Add the parent directory to the path to import darkdelve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from darkdelve import (
    Game, Entity, COLORS, EnergySystem, CombatLog, FOVSystem,
    Inventory, ItemType, EquipmentSlot, GameState
)


class TestMonsterMovementObservability(unittest.TestCase):
    """Test cases for monster movement toward player"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a game instance
        self.game = Game()
        
    def _create_test_dungeon(self, width=80, height=43):
        """Create a simple test dungeon with a corridor and room layout"""
        # Start with all walls (True = wall)
        dungeon_map = np.ones((width, height), dtype=bool)
        
        # Create a main room (center)
        room_x1, room_y1 = 30, 15
        room_x2, room_y2 = 50, 25
        dungeon_map[room_x1:room_x2+1, room_y1:room_y2+1] = False
        
        # Create a corridor leading up from the room
        corridor_x = 40
        for y in range(5, 16):
            dungeon_map[corridor_x, y] = False
        
        return dungeon_map
    
    def _get_monster(self):
        """Find the monster entity in the game"""
        for e in self.game.entities:
            if e is not self.game.player and e.is_alive:
                return e
        return None
    
    def _distance(self, e1, e2):
        """Calculate Manhattan distance between two entities"""
        return abs(e1.x - e2.x) + abs(e1.y - e2.y)
    
    def _create_player(self, x, y):
        """Create a player entity with proper inventory and high HP"""
        return Entity(
            x=x, y=y,
            char="@", color=COLORS['player'],
            name="Test Player",
            blocks=True,
            hp=1000, max_hp=1000, power=5, defense=2, speed=100,
            stats={'str': 10, 'dex': 10, 'con': 10, 'int': 10, 'wis': 10, 'cha': 10},
            nutrition=1000, max_nutrition=2000,
            inventory=Inventory(max_weight=100),
        )
    
    def _create_monster(self, x, y):
        """Create a monster entity"""
        return Entity(
            x=x, y=y,
            char='g',
            color=COLORS['enemy_normal'],
            name="Test Goblin",
            blocks=True,
            hp=10, max_hp=10, power=3, defense=1, speed=100,
        )
    
    def _setup_game_for_movement_test(self, player_x, player_y, monster_x, monster_y):
        """Set up the game state for movement testing without Ollama"""
        # Set up basic game state
        self.game.player = self._create_player(player_x, player_y)
        
        # Create monster
        monster = self._create_monster(monster_x, monster_y)
        
        # Set up dungeon map
        self.game.dungeon_map = self._create_test_dungeon()
        
        # Set up entities
        self.game.entities = [self.game.player, monster]
        
        # Set up energy system
        self.game.energy_system = EnergySystem()
        self.game.energy_system.add_entity(self.game.player, initial_energy=100)
        self.game.energy_system.add_entity(monster, initial_energy=0)
        
        # Set up other game state
        self.game.fov_system = FOVSystem(radius=15)
        self.game.fov = self.game.fov_system.compute(self.game.dungeon_map, player_x, player_y)
        self.game.explored = self.game.fov_system.explored.copy()
        self.game.combat_log = CombatLog()
        self.game.turn = 0
        self.game.state = GameState()
        
        return monster
    
    def test_monster_moves_toward_player_open_space(self):
        """Test that a monster moves toward the player in open space"""
        # Set up game
        player_x, player_y = 40, 20
        monster_x, monster_y = 45, 20
        monster = self._setup_game_for_movement_test(player_x, player_y, monster_x, monster_y)
        
        # Track positions
        positions = []
        initial_distance = self._distance(monster, self.game.player)
        positions.append((monster.x, monster.y, self._distance(monster, self.game.player)))
        
        print(f"\n=== Test: Monster moves toward player in open space ===")
        print(f"Initial positions: Player({player_x}, {player_y}), Monster({monster_x}, {monster_y})")
        print(f"Initial distance: {initial_distance}")
        
        # Run multiple turns
        max_turns = 50
        monster_moved = False
        
        for i in range(max_turns):
            self.game.main_loop(action='e', render_to_stdout=False)
            
            current_dist = self._distance(monster, self.game.player)
            positions.append((monster.x, monster.y, current_dist))
            
            if monster.x != monster_x or monster.y != monster_y:
                monster_moved = True
            
            if current_dist < initial_distance:
                print(f"Turn {i+1}: Monster moved to ({monster.x}, {monster.y}), distance={current_dist}")
        
        print(f"\nMovement trace:")
        for i, (x, y, d) in enumerate(positions):
            print(f"  Turn {i}: Monster at ({x}, {y}), distance={d}")
        
        # Verify monster moved
        self.assertTrue(monster_moved, "Monster should have moved from initial position")
        
        # Verify distance decreased over time (monster is approaching)
        final_distance = positions[-1][2]
        print(f"\nFinal distance: {final_distance}")
        self.assertLess(final_distance, initial_distance, 
                       "Monster should be closer to player after movement")
    
    def test_monster_navigates_corridor_toward_player(self):
        """Test that a monster navigates through a corridor toward the player"""
        # Create a dungeon with a corridor
        dungeon_map = np.ones((80, 43), dtype=bool)
        
        # Create a room on the left
        for x in range(10, 25):
            for y in range(15, 30):
                dungeon_map[x, y] = False
        
        # Create a room on the right
        for x in range(55, 70):
            for y in range(15, 30):
                dungeon_map[x, y] = False
        
        # Create a corridor connecting them
        corridor_y = 22
        for x in range(25, 55):
            dungeon_map[x, corridor_y] = False
        
        # Set up game - place monster close enough for AI to activate (within 15 tiles)
        player_x, player_y = 45, 22
        monster_x, monster_y = 32, 22  # Distance = 13, within AI activation range
        
        self.game.player = self._create_player(player_x, player_y)
        monster = self._create_monster(monster_x, monster_y)
        
        self.game.dungeon_map = dungeon_map
        self.game.entities = [self.game.player, monster]
        
        self.game.energy_system = EnergySystem()
        self.game.energy_system.add_entity(self.game.player, initial_energy=100)
        self.game.energy_system.add_entity(monster, initial_energy=0)
        
        self.game.fov_system = FOVSystem(radius=15)
        self.game.fov = self.game.fov_system.compute(self.game.dungeon_map, player_x, player_y)
        self.game.explored = self.game.fov_system.explored.copy()
        self.game.combat_log = CombatLog()
        self.game.turn = 0
        self.game.state = GameState()
        
        # Track positions
        positions = []
        initial_distance = self._distance(monster, self.game.player)
        positions.append((monster.x, monster.y, self._distance(monster, self.game.player)))
        
        print(f"\n=== Test: Monster navigates corridor toward player ===")
        print(f"Initial positions: Player({player_x}, {player_y}), Monster({monster_x}, {monster_y})")
        print(f"Initial distance: {initial_distance}")
        
        # Run multiple turns
        max_turns = 100
        monster_moved = False
        
        for i in range(max_turns):
            self.game.main_loop(action='e', render_to_stdout=False)
            
            current_dist = self._distance(monster, self.game.player)
            positions.append((monster.x, monster.y, current_dist))
            
            if monster.x != monster_x or monster.y != monster_y:
                monster_moved = True
            
            if current_dist < initial_distance:
                print(f"Turn {i+1}: Monster moved to ({monster.x}, {monster.y}), distance={current_dist}")
        
        print(f"\nMovement trace:")
        for i, (x, y, d) in enumerate(positions):
            print(f"  Turn {i}: Monster at ({x}, {y}), distance={d}")
        
        # Verify monster moved
        self.assertTrue(monster_moved, "Monster should have moved from initial position")
        
        # Verify distance decreased
        final_distance = positions[-1][2]
        print(f"\nFinal distance: {final_distance}")
        self.assertLess(final_distance, initial_distance,
                       "Monster should be closer to player after navigating corridor")
    
    def test_monster_moves_toward_player_with_obstacles(self):
        """Test that a monster navigates around obstacles to reach the player"""
        # Create a dungeon with obstacles
        dungeon_map = np.ones((80, 43), dtype=bool)
        
        # Create a large room
        for x in range(20, 60):
            for y in range(10, 33):
                dungeon_map[x, y] = False
        
        # Create a wall barrier in the middle
        wall_x = 40
        for y in range(15, 30):
            dungeon_map[wall_x, y] = True
        
        # Create a gap in the wall at y=22
        dungeon_map[wall_x, 22] = False
        
        # Set up game
        player_x, player_y = 45, 22
        monster_x, monster_y = 35, 22
        
        self.game.player = self._create_player(player_x, player_y)
        monster = self._create_monster(monster_x, monster_y)
        
        self.game.dungeon_map = dungeon_map
        self.game.entities = [self.game.player, monster]
        
        self.game.energy_system = EnergySystem()
        self.game.energy_system.add_entity(self.game.player, initial_energy=100)
        self.game.energy_system.add_entity(monster, initial_energy=0)
        
        self.game.fov_system = FOVSystem(radius=15)
        self.game.fov = self.game.fov_system.compute(self.game.dungeon_map, player_x, player_y)
        self.game.explored = self.game.fov_system.explored.copy()
        self.game.combat_log = CombatLog()
        self.game.turn = 0
        self.game.state = GameState()
        
        # Track positions
        positions = []
        initial_distance = self._distance(monster, self.game.player)
        positions.append((monster.x, monster.y, self._distance(monster, self.game.player)))
        
        print(f"\n=== Test: Monster navigates around obstacles ===")
        print(f"Initial positions: Player({player_x}, {player_y}), Monster({monster_x}, {monster_y})")
        print(f"Initial distance: {initial_distance}")
        print(f"Wall at x=40, gap at y=22")
        
        # Run multiple turns
        max_turns = 100
        monster_moved = False
        
        for i in range(max_turns):
            self.game.main_loop(action='e', render_to_stdout=False)
            
            current_dist = self._distance(monster, self.game.player)
            positions.append((monster.x, monster.y, current_dist))
            
            if monster.x != monster_x or monster.y != monster_y:
                monster_moved = True
            
            if current_dist < initial_distance:
                print(f"Turn {i+1}: Monster moved to ({monster.x}, {monster.y}), distance={current_dist}")
        
        print(f"\nMovement trace:")
        for i, (x, y, d) in enumerate(positions):
            print(f"  Turn {i}: Monster at ({x}, {y}), distance={d}")
        
        # Verify monster moved
        self.assertTrue(monster_moved, "Monster should have moved from initial position")
        
        # Verify distance decreased
        final_distance = positions[-1][2]
        print(f"\nFinal distance: {final_distance}")
        self.assertLess(final_distance, initial_distance,
                       "Monster should be closer to player after navigating around obstacles")


class TestMonsterCorridorNavigation(unittest.TestCase):
    """Test cases for monster navigating through corridors"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.game = Game()
    
    def _distance(self, e1, e2):
        """Calculate Manhattan distance between two entities"""
        return abs(e1.x - e2.x) + abs(e1.y - e2.y)
    
    def _create_player(self, x, y):
        """Create a player entity with proper inventory and high HP"""
        return Entity(
            x=x, y=y,
            char="@", color=COLORS['player'],
            name="Test Player",
            blocks=True,
            hp=1000, max_hp=1000, power=5, defense=2, speed=100,
            stats={'str': 10, 'dex': 10, 'con': 10, 'int': 10, 'wis': 10, 'cha': 10},
            nutrition=1000, max_nutrition=2000,
            inventory=Inventory(max_weight=100),
        )
    
    def _create_monster(self, x, y):
        """Create a monster entity"""
        return Entity(
            x=x, y=y,
            char='g',
            color=COLORS['enemy_normal'],
            name="Test Goblin",
            blocks=True,
            hp=10, max_hp=10, power=3, defense=1, speed=100,
        )
    
    def test_monster_in_room_navigates_to_corridor_player(self):
        """Test monster in a room navigates toward player in a corridor"""
        # Create a dungeon with a room and corridor
        dungeon_map = np.ones((80, 43), dtype=bool)
        
        # Create a room
        for x in range(25, 55):
            for y in range(10, 33):
                dungeon_map[x, y] = False
        
        # Create a corridor extending right
        corridor_x = 55
        for y in range(15, 30):
            dungeon_map[corridor_x, y] = False
        
        # Extend corridor further
        for x in range(55, 70):
            dungeon_map[x, 22] = False
        
        # Set up game - place monster close enough for AI to activate
        player_x, player_y = 58, 22
        monster_x, monster_y = 53, 22
        
        self.game.player = self._create_player(player_x, player_y)
        monster = self._create_monster(monster_x, monster_y)
        
        self.game.dungeon_map = dungeon_map
        self.game.entities = [self.game.player, monster]
        
        self.game.energy_system = EnergySystem()
        self.game.energy_system.add_entity(self.game.player, initial_energy=100)
        self.game.energy_system.add_entity(monster, initial_energy=0)
        
        self.game.fov_system = FOVSystem(radius=15)
        self.game.fov = self.game.fov_system.compute(self.game.dungeon_map, player_x, player_y)
        self.game.explored = self.game.fov_system.explored.copy()
        self.game.combat_log = CombatLog()
        self.game.turn = 0
        self.game.state = GameState()
        
        # Track positions
        positions = []
        initial_distance = self._distance(monster, self.game.player)
        positions.append((monster.x, monster.y, self._distance(monster, self.game.player)))
        
        print(f"\n=== Test: Monster in room navigates to corridor player ===")
        print(f"Initial positions: Player({player_x}, {player_y}), Monster({monster_x}, {monster_y})")
        print(f"Initial distance: {initial_distance}")
        
        # Run multiple turns
        max_turns = 100
        monster_moved = False
        
        for i in range(max_turns):
            self.game.main_loop(action='e', render_to_stdout=False)
            
            current_dist = self._distance(monster, self.game.player)
            positions.append((monster.x, monster.y, current_dist))
            
            if monster.x != monster_x or monster.y != monster_y:
                monster_moved = True
            
            if current_dist < initial_distance:
                print(f"Turn {i+1}: Monster moved to ({monster.x}, {monster.y}), distance={current_dist}")
        
        print(f"\nMovement trace:")
        for i, (x, y, d) in enumerate(positions):
            print(f"  Turn {i}: Monster at ({x}, {y}), distance={d}")
        
        # Verify monster moved
        self.assertTrue(monster_moved, "Monster should have moved from initial position")
        
        # Verify distance decreased
        final_distance = positions[-1][2]
        print(f"\nFinal distance: {final_distance}")
        self.assertLess(final_distance, initial_distance,
                       "Monster should be closer to player after navigating through corridor")


if __name__ == '__main__':
    unittest.main(verbosity=2)