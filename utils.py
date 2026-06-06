import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_info(message):
    logger.info(message)

def log_error(message):
    logger.error(message)

def safe_division(num, denom):
    if denom == 0:
        return None
    return num / denom

def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

# Add debug statements to trace the values of variables
def check_dungeon_map(dungeon_map):
    if dungeon_map is None:
        log_error("dungeon_map is None")
    elif not isinstance(dungeon_map, np.ndarray):
        log_error(f"dungeon_map is not a numpy array: {type(dungeon_map)}")

# Add heuristic function
def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def get_neighbors(x, y, dungeon_map, entities):
    neighbors = []
    directions = [(0, 1), (1, 0), (-1, 0), (0, -1)]
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < dungeon_map.shape[0] and 0 <= ny < dungeon_map.shape[1]:
            if not is_blocked(nx, ny, entities):
                neighbors.append((nx, ny))
    return neighbors

def is_blocked(x, y, entities, ignore_entity=None):
    for entity in entities:
        if entity != ignore_entity and entity.x == x and entity.y == y:
            return True
    return False