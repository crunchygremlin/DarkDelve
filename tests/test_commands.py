import numpy as np
from main import Entity, interpret_commander_action


def test_retreat_command_targets_home():
    player = Entity(5,5,'@',(255,255,0),'Player',blocks=True)
    commander = Entity(2,2,'G',(255,0,0),'C',blocks=True,is_commander=True)
    commander.home_position = (2,2)
    commander.current_command = {'command': 'RETREAT_TO_ROOM'}
    action, target = interpret_commander_action(commander, player, np.ones((10,10), dtype=bool), [player, commander])
    assert action == 'RETREAT'
    assert target == (2,2)


def test_defend_command_targets_home():
    player = Entity(5,5,'@',(255,255,0),'Player',blocks=True)
    commander = Entity(2,2,'G',(255,0,0),'C',blocks=True,is_commander=True)
    commander.home_position = (2,2)
    commander.current_command = {'command': 'DEFEND_COMMANDER'}
    action, target = interpret_commander_action(commander, player, np.ones((10,10), dtype=bool), [player, commander])
    assert action == 'DEFEND'
    assert target == (2,2)


def test_hold_position_waits():
    player = Entity(5,5,'@',(255,255,0),'Player',blocks=True)
    commander = Entity(2,2,'G',(255,0,0),'C',blocks=True,is_commander=True)
    commander.current_command = {'command': 'HOLD_POSITION'}
    action, target = interpret_commander_action(commander, player, np.ones((10,10), dtype=bool), [player, commander])
    assert action == 'WAIT'
    assert target is None
