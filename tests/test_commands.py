import unittest
import numpy as np
from main import Entity, interpret_commander_action

class TestCommanderCommands(unittest.TestCase):

    def test_retreat_command_targets_home(self):
        player = Entity(5,5,'@',(255,255,0),'Player',blocks=True)
        commander = Entity(2,2,'G',(255,0,0),'C',blocks=True,is_commander=True)
        commander.home_position = (2,2)
        commander.current_command = {'command': 'RETREAT_TO_ROOM'}
        action, target = interpret_commander_action(commander, player, np.ones((10,10), dtype=bool), [player, commander])

        self.assertEqual(action, 'RETREAT')
        self.assertEqual(target, (2,2))

    def test_defend_command_targets_home(self):
        player = Entity(5,5,'@',(255,255,0),'Player',blocks=True)
        commander = Entity(2,2,'G',(255,0,0),'C',blocks=True,is_commander=True)
        commander.home_position = (2,2)
        commander.current_command = {'command': 'DEFEND_COMMANDER'}
        action, target = interpret_commander_action(commander, player, np.ones((10,10), dtype=bool), [player, commander])

        self.assertEqual(action, 'DEFEND')
        self.assertEqual(target, (2,2))

    def test_hold_position_waits(self):
        player = Entity(5,5,'@',(255,255,0),'Player',blocks=True)
        commander = Entity(2,2,'G',(255,0,0),'C',blocks=True,is_commander=True)
        commander.current_command = {'command': 'HOLD_POSITION'}
        action, target = interpret_commander_action(commander, player, np.ones((10,10), dtype=bool), [player, commander])

        self.assertEqual(action, 'WAIT')
        self.assertIsNone(target)
