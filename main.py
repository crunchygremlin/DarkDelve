import numpy as np
from pathfinding import check_dungeon_map

def find_path(start, end, dungeon_map):
    # Implement path finding logic here
    return []

if __name__ == "__main__":
    dungeon_map = np.array([
        [0, 1, 1],
        [0, 0, 0],
        [1, 0, 0]
    ])
    start = (0, 0)
    end = (2, 2)
    
    path = find_path(start, end, dungeon_map)
    print("Path:", path)