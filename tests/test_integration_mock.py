import unittest
import numpy as np
from main import enqueue_commander_prompt, llm_request_queue, llm_response_queue, process_llm_responses, interpret_commander_action, find_path, Entity


def test_mock_integration_turn():
    # Setup minimal map and entities
    dungeon_map = np.ones((10,10), dtype=bool, order="F")
    player = Entity(5,5,'@',(255,255,0),'Player',blocks=True,hp=30,power=5,defense=2)
    commander = Entity(2,2,'G',(255,0,0),'MockCommander',blocks=True,hp=20,power=4,defense=1,is_commander=True)
    entities = [player, commander]

    # Ensure queues are empty
    while not llm_request_queue.empty():
        llm_request_queue.get_nowait()
    while not llm_response_queue.empty():
        llm_response_queue.get_nowait()

    # Enqueue a prompt (the worker is not running in tests)
    enqueue_commander_prompt(commander, player, entities)
    req = llm_request_queue.get_nowait()
    assert 'prompt' in req

    # Mock a successful LLM response into the response queue
    llm_response_queue.put({
        'commander_id': 'MockCommander',
        'commander_shout': 'CHARGE!',
        'command': 'ATTACK_PLAYER'
    })

    # Process response and interpret action
    process_llm_responses(entities)
    assert commander.current_command is not None
    action, target = interpret_commander_action(commander, player, dungeon_map, entities)
    assert action == 'ATTACK'
    assert target == (player.x, player.y)

    # Engine computes path and executes one movement step
    path = find_path((commander.x, commander.y), target, dungeon_map, entities)
    assert len(path) >= 2
    next_step = path[1]
    commander.move_to(next_step[0], next_step[1], dungeon_map, entities)
    assert (commander.x, commander.y) == next_step
