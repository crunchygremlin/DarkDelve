import numpy as np
import json
import os
from main import find_path, llm_request_queue, llm_response_queue, enqueue_commander_prompt, process_llm_responses
from main import Entity


def test_find_path_blocked_by_entity():
    dungeon_map = np.ones((5,5), dtype=bool, order="F")
    # Place a blocking entity on the straight path
    blocker = Entity(1,0,'X',(0,0,0),'Blocker',blocks=True)
    entities = [blocker]
    start = (0,0)
    goal = (2,0)
    path = find_path(start, goal, dungeon_map, entities)
    assert path[0] == start
    assert path[-1] == goal
    # ensure path does not step on blocker
    assert (1,0) not in path[1:]


def test_enqueue_and_process_llm_cycle():
    # ensure queue is empty
    while not llm_request_queue.empty():
        llm_request_queue.get_nowait()
    while not llm_response_queue.empty():
        llm_response_queue.get_nowait()

    # create a commander and player
    player = Entity(3,3,'@',(255,255,0),'Player',blocks=True,hp=30,power=5,defense=2)
    commander = Entity(1,1,'G',(255,0,0),'TestCommander',blocks=True,hp=20,power=3,defense=1,is_commander=True)
    entities = [player, commander]

    # ensure template exists so enqueue uses it
    prompt_dir = os.path.join(os.path.dirname(__file__), os.pardir, 'prompt')
    os.makedirs(prompt_dir, exist_ok=True)
    tmpl = os.path.join(prompt_dir, 'commander_prompt.txt')
    with open(tmpl, 'w', encoding='utf-8') as f:
        f.write('JSONONLY {visible_entities}')

    enqueue_commander_prompt(commander, player, entities)
    req = llm_request_queue.get_nowait()
    assert 'prompt' in req

    # simulate a response from LLM and process it
    llm_response_queue.put({
        'commander_id': 'TestCommander',
        'commander_shout': 'CHARGE!',
        'command': 'ATTACK_PLAYER'
    })
    process_llm_responses(entities)
    assert commander.current_command is not None
    assert commander.current_command['command'] == 'ATTACK_PLAYER'
        # Removed stray end patch marker