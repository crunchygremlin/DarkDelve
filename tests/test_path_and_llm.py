import numpy as np
from main import find_path, validate_llm_response


def test_find_path_simple():
    # 5x5 fully walkable map
    dungeon_map = np.ones((5,5), dtype=bool, order="F")
    entities = []
    start = (0,0)
    goal = (4,4)
    path = find_path(start, goal, dungeon_map, entities)
    assert path[0] == start
    assert path[-1] == goal
    assert len(path) > 1


def test_validate_llm_response_valid():
    resp = {"commander_shout": "Charge!", "command": "ATTACK_PLAYER"}
    v = validate_llm_response(resp)
    assert v["command"] == "ATTACK_PLAYER"
    assert v["commander_shout"] == "Charge!"


def test_validate_llm_response_invalid():
    resp = {"commander_shout": "Hmm", "command": "SOME_INVALID"}
    v = validate_llm_response(resp)
    assert v["command"] == "ATTACK_PLAYER"

