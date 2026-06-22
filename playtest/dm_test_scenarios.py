"""
DM Test Scenarios for Playtester
Tests the Dungeon Master Agent and related systems.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class DMTestScenario:
    """A test scenario for DM functionality."""
    name: str
    description: str
    test_type: str  # "behavior_generation", "level_design", "item_creation", "narrative", "full_pipeline"
    setup: dict
    expected_outcomes: dict


# Define all test scenarios
TEST_SCENARIOS: List[DMTestScenario] = [
    DMTestScenario(
        name="behavior_generation_test",
        description="Create a goblin with perception status, verify DM generates valid behavior script",
        test_type="behavior_generation",
        setup={
            "entity_id": "goblin_001",
            "mob_type": "goblin",
            "perception": {
                "can_see_player": True,
                "can_hear_player": False,
                "player_noise_level": 0.5,
                "player_distance_estimate": 5.0,
                "visible_threats": [],
                "visible_allies": [],
                "visible_items": [],
                "environment_danger": 0.3,
                "light_level": 0.8,
            },
            "social_context": "Goblin minion in goblin_kingdom structure, loyalty 0.5",
            "valid_conditions": ["player_visible", "health_below", "loyalty_above"],
            "valid_actions": ["move_to", "attack", "give_item", "increase_loyalty"],
        },
        expected_outcomes={
            "has_script_id": True,
            "has_root_node": True,
            "root_is_selector": True,
            "has_children": True,
        }
    ),
    DMTestScenario(
        name="level_design_test",
        description="Provide PlayerProfile, verify DM generates valid level layout",
        test_type="level_design",
        setup={
            "player_profile": {
                "level": 5,
                "stats": {"strength": 12, "dexterity": 14, "constitution": 10},
                "power_levels": {"melee_strength": 15, "evasion": 8},
                "skills": ["weapon_mastery", "stealth"],
            },
            "level_number": 3,
            "theme": "goblin_warren",
        },
        expected_outcomes={
            "has_description": True,
            "has_entities": True,
            "has_items": True,
            "entities_count": 5,
        }
    ),
    DMTestScenario(
        name="item_creation_test",
        description="Create item via ItemFactory, verify stats are balanced",
        test_type="item_creation",
        setup={
            "name": "Flaming Sword",
            "item_type": "sword",
            "rarity": "rare",
            "powers": ["fire"],
            "modifiers": ["sharp"],
            "level_origin": 5,
        },
        expected_outcomes={
            "has_item_id": True,
            "has_name": True,
            "rarity_is_rare": True,
            "damage_positive": True,
            "durability_reasonable": True,
        }
    ),
    DMTestScenario(
        name="narrative_test",
        description="Create StoryOutline, verify hints chain across levels",
        test_type="narrative",
        setup={
            "outline_id": "test_dungeon_001",
            "title": "The Goblin King's Lair",
            "theme": "goblin_warren",
            "difficulty": "normal",
            "total_levels": 5,
            "levels": [
                {"level_number": 1, "title": "Entrance", "hints_dropped": ["goblin_shamans_use_fire"]},
                {"level_number": 2, "title": "War Room", "hints_dropped": ["king_has_been_fleed"]},
                {"level_number": 3, "title": "Treasure Chamber", "hints_dropped": ["boss_weakness_fire"]},
            ],
        },
        expected_outcomes={
            "has_outline_id": True,
            "hints_for_level_1": ["goblin_shamans_use_fire"],
            "hints_for_level_3": ["goblin_shamans_use_fire", "king_has_been_fleed", "boss_weakness_fire"],
        }
    ),
    DMTestScenario(
        name="loyalty_test",
        description="Create social structure, verify loyalty modifications work",
        test_type="social",
        setup={
            "structure_type": "goblin_kingdom",
            "leader_id": "goblin_king_001",
            "member_ids": ["goblin_001", "goblin_002", "goblin_003"],
            "base_loyalty": 0.5,
            "gift_value": 25,
            "expected_loyalty_after_gift": 0.75,  # 0.5 + (25 * 0.01) = 0.75
        },
        expected_outcomes={
            "structure_created": True,
            "initial_loyalty": 0.5,
            "loyalty_after_gift": 0.75,
        }
    ),
    DMTestScenario(
        name="durability_test",
        description="Create item, apply damage, verify degradation curve",
        test_type="durability",
        setup={
            "item_type": "sword",
            "initial_durability": 100,
            "degradation_threshold": 0.5,
            "damage_amount": 60,
        },
        expected_outcomes={
            "initial_condition": 1.0,
            "after_damage_condition": 0.4,
            "is_degraded": True,
            "can_repair": True,
        }
    ),
    DMTestScenario(
        name="damage_calculation_test",
        description="Test DamageCalculator with various resistance/armor combos",
        test_type="damage",
        setup={
            "test_cases": [
                {"attacker_power": 20, "defender_resistance": 0.2, "defender_armor": 5, "expected_min": 10, "expected_max": 15},
                {"attacker_power": 10, "defender_resistance": 0.5, "defender_armor": 10, "expected_min": 1, "expected_max": 5},
                {"attacker_power": 30, "defender_resistance": 0.0, "defender_armor": 0, "expected_min": 30, "expected_max": 30},
            ]
        },
        expected_outcomes={
            "all_cases_pass": True,
            "minimum_damage_is_1": True,
        }
    ),
    DMTestScenario(
        name="context_headroom_test",
        description="Verify ContextManager tracks tokens correctly",
        test_type="context",
        setup={
            "max_tokens": 8192,
            "system_prompt": "You are a helpful assistant.",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
        },
        expected_outcomes={
            "system_tokens_estimated": True,
            "history_tokens_estimated": True,
            "headroom_calculated": True,
            "can_fit_check_works": True,
        }
    ),
    DMTestScenario(
        name="full_pipeline_test",
        description="DM generates level + items + mobs + narrative in one go",
        test_type="full_pipeline",
        setup={
            "difficulty": "normal",
            "total_levels": 3,
            "theme": "goblin_warren",
            "player_power_target": {"melee_strength": 15, "evasion": 10},
        },
        expected_outcomes={
            "dungeon_generated": True,
            "levels_count": 3,
            "items_placed": True,
            "mobs_placed": True,
            "narrative_attached": True,
        }
    ),
    DMTestScenario(
        name="difficulty_scaling_test",
        description="Same level generated at different difficulties",
        test_type="difficulty",
        setup={
            "level_number": 1,
            "theme": "goblin_warren",
            "difficulties": ["story", "normal", "hard", "nightmare"],
        },
        expected_outcomes={
            "story_scaling": 0.5,
            "normal_scaling": 1.0,
            "hard_scaling": 1.5,
            "nightmare_scaling": 2.0,
            "loot_modifiers_correct": True,
        }
    ),
]


def get_scenario_by_name(name: str) -> Optional[DMTestScenario]:
    """Get a test scenario by name."""
    for scenario in TEST_SCENARIOS:
        if scenario.name == name:
            return scenario
    return None


def get_all_scenarios() -> List[DMTestScenario]:
    """Get all test scenarios."""
    return TEST_SCENARIOS


def get_scenarios_by_type(test_type: str) -> List[DMTestScenario]:
    """Get all scenarios of a specific type."""
    return [s for s in TEST_SCENARIOS if s.test_type == test_type]