"""Parser for LLM-generated floor 1 descriptions.

Extracts entity and feature hints from natural language descriptions
and applies them to Floor1Data to influence spawning.
"""

import re
import random
from typing import Dict, Any
from src.application.services.floor1_generator import Floor1Data, Den, PatrolRoute


# Keyword to creature type mapping (sorted by length for greedy matching)
MONSTER_KEYWORDS = {
    "giant spider": "giant_spider",
    "spider queen": "spider_queen",
    "spider": "giant_spider",
    "web": "giant_spider",
    "dungeon guard": "dungeon_guard",
    "sergeants": "guard_sergeant",
    "sergeant": "guard_sergeant",
    "patrol": "dungeon_guard",
    "guard": "dungeon_guard",
    "cave rat": "cave_rat",
    "rat king": "rat_king",
    "nest": "cave_rat",
    "rat": "cave_rat",
    "cave bat": "cave_bat",
    "bat": "cave_bat",
    "troll scavenger": "troll_scavenger",
    "troll": "troll_scavenger",
    "fungal creeper": "fungal_creeper",
    "mushroom": "fungal_creeper",
    "fungus": "fungal_creeper",
    "creeper": "fungal_creeper",
}

FEATURE_KEYWORDS = {
    "corpses": "corpse",
    "remains": "corpse",
    "bones": "corpse",
    "corpse": "corpse",
    "web": "den",
    "nest": "den",
    "den": "den",
    "stairs": "stairs",
    "passage": "corridor",
    "corridor": "corridor",
    "watch": "patrol",
    "patrol": "patrol",
}


def parse_floor1_description(description, floor1_data, dungeon_map, config):
    """Parse an LLM description and modify Floor1Data based on extracted hints."""
    if not description or not description.strip():
        return floor1_data

    desc_lower = description.lower()
    monster_counts = _extract_monster_counts(desc_lower)
    feature_counts = _extract_feature_counts(desc_lower)

    _add_dens_from_description(floor1_data, monster_counts, dungeon_map, config)
    _add_roaming_from_description(floor1_data, monster_counts, dungeon_map, config)
    _add_corpses_from_description(floor1_data, feature_counts, dungeon_map, config)
    _add_patrols_from_description(floor1_data, feature_counts, config)

    return floor1_data


def _extract_monster_counts(desc_lower):
    """Count monster keyword occurrences in description."""
    counts = {}
    desc_lower = desc_lower.lower()
    sorted_keywords = sorted(MONSTER_KEYWORDS.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        creature_type = MONSTER_KEYWORDS[keyword]
        # Use word boundary but also match plural forms (e.g. "spiders" matches "spider")
        pattern = r'\b' + re.escape(keyword) + r's?\b'
        occurrences = len(re.findall(pattern, desc_lower))
        if occurrences > 0:
            counts[creature_type] = counts.get(creature_type, 0) + occurrences
    return counts


def _extract_feature_counts(desc_lower):
    """Count feature keyword occurrences in description."""
    counts = {}
    desc_lower = desc_lower.lower()
    for keyword, feature_type in FEATURE_KEYWORDS.items():
        # Use word boundary but also match plural forms
        pattern = r'\b' + re.escape(keyword) + r's?\b'
        occurrences = len(re.findall(pattern, desc_lower))
        if occurrences > 0:
            counts[feature_type] = counts.get(feature_type, 0) + occurrences
    return counts


def _add_dens_from_description(floor1_data, monster_counts, dungeon_map, config):
    """Add extra dens based on monster mentions (2+ mentions = extra den)."""
    width = config["dungeon"]["width"]
    height = config["dungeon"]["height"]
    existing_path_set = set(floor1_data.main_path)
    den_creatures = {"giant_spider", "cave_rat", "cave_bat", "fungal_creeper"}
    # Protect entrance area (top 5 rows) and stairs area (bottom 5 rows)
    min_y = 5
    max_y = height - 5
    # Limit extra dens to avoid entity count overflow
    max_extra_dens = 2
    added = 0

    for creature_type, count in monster_counts.items():
        if creature_type not in den_creatures or count < 2:
            continue
        if added >= max_extra_dens:
            break
        for _ in range(50):
            x = random.randint(3, width - 6)
            y = random.randint(min_y, max_y)
            if not dungeon_map[x, y] and (x, y) not in existing_path_set:
                too_close = any(
                    abs(x - d.center[0]) + abs(y - d.center[1]) < 8
                    for d in floor1_data.dens
                )
                if not too_close:
                    # Don't carve rooms - just place den on existing floor
                    floor1_data.dens.append(Den(
                        center=(x, y),
                        radius=2,
                        creature_type=creature_type,
                        count=random.randint(2, 3),
                    ))
                    added += 1
                    break


def _add_roaming_from_description(floor1_data, monster_counts, dungeon_map, config):
    """Add extra roaming spawns for mentioned monster types."""
    width = config["dungeon"]["width"]
    height = config["dungeon"]["height"]
    existing_path_set = set(floor1_data.main_path)
    roaming_creatures = {"troll_scavenger", "cave_bat", "fungal_creeper", "cave_rat"}
    # Limit extra roaming spawns
    max_extra_roaming = 2
    added = 0

    for creature_type, count in monster_counts.items():
        if creature_type not in roaming_creatures:
            continue
        if added >= max_extra_roaming:
            break
        extra = min(count - 1, 2)
        for _ in range(extra):
            if added >= max_extra_roaming:
                break
            for _ in range(50):
                x = random.randint(1, width - 2)
                y = random.randint(5, height - 2)  # Protect entrance area
                if not dungeon_map[x, y] and (x, y) not in existing_path_set:
                    min_dist = min(abs(x - px) + abs(y - py) for px, py in floor1_data.main_path)
                    if min_dist > 3:
                        floor1_data.roaming_spawns.append((x, y, creature_type))
                        added += 1
                        break


def _add_corpses_from_description(floor1_data, feature_counts, dungeon_map, config):
    """Add extra corpse positions if corpses are mentioned."""
    if "corpse" not in feature_counts:
        return
    width = config["dungeon"]["width"]
    height = config["dungeon"]["height"]
    # Limit extra corpses
    max_extra_corpses = 1
    added = 0
    for _ in range(min(feature_counts["corpse"], max_extra_corpses)):
        for _ in range(50):
            x = random.randint(1, width - 2)
            y = random.randint(5, height - 2)  # Protect entrance area
            if not dungeon_map[x, y] and (x, y) not in floor1_data.corpses:
                floor1_data.corpses.append((x, y))
                added += 1
                break


def _add_patrols_from_description(floor1_data, feature_counts, config):
    """Add extra patrol routes if patrols are mentioned."""
    if "patrol" not in feature_counts or len(floor1_data.main_path) < 10:
        return
    # Only use waypoints from the middle section of the path (avoid entrance area)
    path_len = len(floor1_data.main_path)
    start_idx = path_len // 5  # Skip first 20% (entrance area)
    end_idx = path_len * 4 // 5  # Skip last 20% (stairs area)
    usable_path = floor1_data.main_path[start_idx:end_idx]
    if len(usable_path) < 4:
        return
    segment_size = len(usable_path) // (len(floor1_data.patrol_routes) + 1)
    waypoints = [
        usable_path[idx]
        for idx in range(0, len(usable_path), max(1, segment_size // 3))
    ]
    if len(waypoints) >= 2:
        floor1_data.patrol_routes.append(PatrolRoute(
            waypoints=waypoints,
            guard_types=["dungeon_guard"],
        ))
