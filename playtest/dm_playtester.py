"""
DM Playtester
Runs automated tests for Dungeon Master functionality.
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from playtest.dm_test_scenarios import DMTestScenario, TEST_SCENARIOS, get_scenario_by_name


@dataclass
class TestResult:
    """Result of a single test scenario."""
    scenario_name: str
    passed: bool
    duration_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    error: str = ""


class DMPlaytester:
    """Automated playtester for DM systems."""

    def __init__(self, config_path: str = "playtest/playtest_config.yaml"):
        self.config_path = config_path
        self.results: List[TestResult] = []
        self._setup_services()

    def _setup_services(self):
        """Set up the services needed for testing."""
        # Import services lazily to avoid import errors if dependencies missing
        try:
            from src.domain.services.context_manager import ContextManager
            from src.domain.services.item_factory_service import ItemFactoryService
            from src.domain.services.loot_service import LootService
            from src.domain.services.narrative_service import NarrativeService
            from src.domain.services.puzzle_service import PuzzleService
            from src.domain.services.dungeon_master_service import DungeonMasterService
            from src.domain.services.level_design_service import LevelDesignService
            from src.domain.value_objects.llm_logging import LLMLogger
            
            self.context_manager = ContextManager()
            self.item_factory_service = ItemFactoryService()
            self.loot_service = LootService()
            self.narrative_service = NarrativeService()
            self.puzzle_service = PuzzleService()
            self.llm_logger = LLMLogger()
            # LevelDesignService requires llm_logger
            self.level_design_service = LevelDesignService(llm_logger=self.llm_logger)
            self.dungeon_master_service = DungeonMasterService(level_design_service=self.level_design_service)
            self.services_available = True
        except ImportError as e:
            self.services_available = False
            self.import_error = str(e)

    def run_all_tests(self) -> dict:
        """Run all DM test scenarios, return results."""
        results = {
            "total": len(TEST_SCENARIOS),
            "passed": 0,
            "failed": 0,
            "results": []
        }
        
        for scenario in TEST_SCENARIOS:
            result = self.run_scenario(scenario)
            self.results.append(result)
            results["results"].append({
                "name": result.scenario_name,
                "passed": result.passed,
                "duration_ms": result.duration_ms,
                "error": result.error
            })
            if result.passed:
                results["passed"] += 1
            else:
                results["failed"] += 1
        
        return results

    def run_scenario(self, scenario: DMTestScenario) -> TestResult:
        """Run a single test scenario."""
        start_time = time.time()
        
        try:
            if scenario.test_type == "behavior_generation":
                result = self.run_behavior_generation_test(scenario)
            elif scenario.test_type == "level_design":
                result = self.run_level_design_test(scenario)
            elif scenario.test_type == "item_creation":
                result = self.run_item_creation_test(scenario)
            elif scenario.test_type == "narrative":
                result = self.run_narrative_test(scenario)
            elif scenario.test_type == "durability":
                result = self.run_durability_test(scenario)
            elif scenario.test_type == "damage":
                result = self.run_damage_calculation_test(scenario)
            elif scenario.test_type == "context":
                result = self.run_context_headroom_test(scenario)
            elif scenario.test_type == "full_pipeline":
                result = self.run_full_pipeline_test(scenario)
            elif scenario.test_type == "difficulty":
                result = self.run_difficulty_scaling_test(scenario)
            elif scenario.test_type == "social":
                result = self.run_loyalty_test(scenario)
            elif scenario.test_type == "floor1_generation":
                result = self.run_floor1_generation_test(scenario)
            else:
                result = {"passed": False, "error": f"Unknown test type: {scenario.test_type}"}
            
            passed = result.get("passed", False)
            error = result.get("error", "")
            details = {k: v for k, v in result.items() if k not in ("passed", "error")}
            
        except Exception as e:
            passed = False
            # Include full traceback with line numbers for debugging
            error = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            details = {}
        
        duration_ms = (time.time() - start_time) * 1000
        return TestResult(
            scenario_name=scenario.name,
            passed=passed,
            duration_ms=duration_ms,
            details=details,
            error=error
        )

    def run_floor1_generation_test(self, scenario: DMTestScenario) -> dict:
        """Run floor 1 generation test: verify entities, positions, and constraints."""
        try:
            from darkdelve import Game
            game = Game()
            game.initialize()
            
            entities = game.entities
            player = game.player
            
            # Check guards exist
            guards = [e for e in entities if e.name == 'Dungeon Guard']
            sergeants = [e for e in entities if e.name == 'Guard Sergeant']
            
            # Check dens exist (spider queens or rat kings = den leaders)
            den_leaders = [e for e in entities if e.name in ('Spider Queen', 'Rat King')]
            
            # Check no two blocking entities share a position
            blocking = [e for e in entities if e.blocks]
            positions = [(e.x, e.y) for e in blocking]
            no_overlaps = len(positions) == len(set(positions))
            
            # Check all entities on floor tiles
            no_wall_spawns = True
            for e in entities:
                if 0 <= e.x < game.dungeon_map.shape[0] and 0 <= e.y < game.dungeon_map.shape[1]:
                    if game.dungeon_map[e.x, e.y]:  # True = wall
                        no_wall_spawns = False
                        break
            
            # Check monsters weaker than player
            monsters_weaker = True
            for e in entities:
                if e is player:
                    continue
                if e.max_hp > player.max_hp + 5 or e.power > player.power:
                    monsters_weaker = False
                    break
            
            passed = (
                len(guards) > 0 and
                len(sergeants) > 0 and
                len(den_leaders) > 0 and
                no_overlaps and
                no_wall_spawns and
                monsters_weaker
            )
            
            return {
                "passed": passed,
                "guards_count": len(guards),
                "sergeants_count": len(sergeants),
                "den_leaders_count": len(den_leaders),
                "no_overlaps": no_overlaps,
                "no_wall_spawns": no_wall_spawns,
                "monsters_weaker": monsters_weaker,
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}

    def run_behavior_generation_test(self, scenario: DMTestScenario) -> dict:
        """Run behavior generation test."""
        if not self.services_available:
            return {"passed": False, "error": f"Services not available: {self.import_error}"}
        
        # Create perception status
        from src.domain.value_objects.perception import PerceptionStatus
        perception = PerceptionStatus(
            entity_id=scenario.setup["entity_id"],
            **scenario.setup["perception"]
        )
        
        # Verify perception was created correctly
        passed = (
            perception.entity_id == scenario.setup["entity_id"] and
            perception.can_see_player == scenario.setup["perception"]["can_see_player"]
        )
        
        return {
            "passed": passed,
            "perception_created": True,
            "entity_id": perception.entity_id,
        }

    def run_level_design_test(self, scenario: DMTestScenario) -> dict:
        """Run level design test."""
        if not self.services_available:
            return {"passed": False, "error": f"Services not available: {self.import_error}"}
        
        # Create a simple level design
        from src.domain.value_objects.difficulty import DungeonLevel, DifficultyMode, Room
        
        level = DungeonLevel(
            level_number=scenario.setup["level_number"],
            difficulty=DifficultyMode.NORMAL,
            width=80,
            height=40,
            rooms=[],
            corridors=[],
            mobs=[],
            items=[],
            traps=[],
            exits=[],
            narrative_id=f"narrative_{scenario.setup['level_number']}",
        )
        
        return {
            "passed": level.level_number == scenario.setup["level_number"],
            "level_created": True,
            "level_number": level.level_number,
        }

    def run_item_creation_test(self, scenario: DMTestScenario) -> dict:
        """Run item creation test."""
        if not self.services_available:
            return {"passed": False, "error": f"Services not available: {self.import_error}"}
        
        item = self.item_factory_service.create_item(
            name=scenario.setup["name"],
            item_type=scenario.setup["item_type"],
            rarity=scenario.setup["rarity"],
            powers=scenario.setup.get("powers", []),
            modifiers=scenario.setup.get("modifiers", []),
            level_origin=scenario.setup.get("level_origin", 1),
        )
        
        expected = scenario.expected_outcomes
        passed = (
            hasattr(item, "item_id") and
            item.rarity == expected.get("rarity_is_rare", "rare") and
            item.stats.damage > 0
        )
        
        return {
            "passed": passed,
            "item_id": item.item_id,
            "name": item.name,
            "rarity": item.rarity,
            "damage": item.stats.damage,
        }

    def run_narrative_test(self, scenario: DMTestScenario) -> dict:
        """Run narrative test."""
        if not self.services_available:
            return {"passed": False, "error": f"Services not available: {self.import_error}"}
        
        from src.domain.value_objects.narrative import StoryOutline, LevelNarrative
        
        levels = [
            LevelNarrative(
                level_number=l["level_number"],
                title=l["title"],
                description=f"Level {l['level_number']}",
                hints_dropped=l.get("hints_dropped", [])
            )
            for l in scenario.setup["levels"]
        ]
        
        outline = StoryOutline(
            outline_id=scenario.setup["outline_id"],
            title=scenario.setup["title"],
            theme=scenario.setup["theme"],
            difficulty=scenario.setup["difficulty"],
            total_levels=scenario.setup["total_levels"],
            levels=levels,
            bosses=[],
            key_items=[],
            opening_narrative="Start",
            closing_narrative="End",
        )
        
        hints_1 = outline.get_hints_for_level(1)
        hints_3 = outline.get_hints_for_level(3)
        
        expected = scenario.expected_outcomes
        passed = (
            hints_1 == expected.get("hints_for_level_1", []) and
            hints_3 == expected.get("hints_for_level_3", [])
        )
        
        return {
            "passed": passed,
            "outline_id": outline.outline_id,
            "hints_level_1": hints_1,
            "hints_level_3": hints_3,
        }

    def run_loyalty_test(self, scenario: DMTestScenario) -> dict:
        """Run loyalty test."""
        if not self.services_available:
            return {"passed": False, "error": f"Services not available: {self.import_error}"}
        
        from src.domain.services.social_service import SocialService
        
        social_service = SocialService()
        structure = social_service.create_structure(
            structure_type=scenario.setup["structure_type"],
            leader_id=scenario.setup["leader_id"],
            member_ids=scenario.setup["member_ids"]
        )
        
        # Set base loyalty
        social_service.seed_loyalty(structure.structure_id, scenario.setup["base_loyalty"])
        
        # Process a gift
        result = social_service.process_gift(
            giver_id=scenario.setup["leader_id"],
            receiver_id=scenario.setup["member_ids"][0],
            item_value=scenario.setup["gift_value"],
            tick=0
        )
        
        loyalty = social_service.get_loyalty(scenario.setup["member_ids"][0])
        
        expected = scenario.expected_outcomes
        passed = (
            structure is not None and
            loyalty.loyalty_score >= expected.get("loyalty_after_gift", 0.75) - 0.01
        )
        
        return {
            "passed": passed,
            "structure_created": structure is not None,
            "initial_loyalty": scenario.setup["base_loyalty"],
            "loyalty_after_gift": loyalty.loyalty_score,
        }

    def run_durability_test(self, scenario: DMTestScenario) -> dict:
        """Run durability test."""
        if not self.services_available:
            return {"passed": False, "error": f"Services not available: {self.import_error}"}
        
        from src.domain.components.item_durability import ItemDurability
        
        durability = ItemDurability()
        durability.condition = 1.0
        
        # Apply damage
        durability.degrade(scenario.setup["damage_amount"] / scenario.setup["initial_durability"])
        
        expected = scenario.expected_outcomes
        passed = (
            abs(durability.condition - expected.get("after_damage_condition", 0.4)) < 0.01 and
            durability.is_degraded() == expected.get("is_degraded", True)
        )
        
        return {
            "passed": passed,
            "initial_condition": 1.0,
            "after_damage_condition": durability.condition,
            "is_degraded": durability.is_degraded(),
        }

    def run_damage_calculation_test(self, scenario: DMTestScenario) -> dict:
        """Run damage calculation test."""
        if not self.services_available:
            return {"passed": False, "error": f"Services not available: {self.import_error}"}
        
        from src.domain.components.damage_calculator import DamageComponent
        
        calc = DamageComponent()
        all_passed = True
        
        for tc in scenario.setup["test_cases"]:
            result = calc.calculate_damage(
                attacker_power=tc["attacker_power"],
                damage_type="physical",
                defender_resistance=tc["defender_resistance"],
                defender_armor=tc["defender_armor"],
            )
            if not (tc["expected_min"] <= result.final_damage <= tc["expected_max"]):
                all_passed = False
        
        return {
            "passed": all_passed,
            "minimum_damage_is_1": True,
        }

    def run_context_headroom_test(self, scenario: DMTestScenario) -> dict:
        """Run context headroom test."""
        if not self.services_available:
            return {"passed": False, "error": f"Services not available: {self.import_error}"}
        
        self.context_manager.set_system_prompt(scenario.setup["system_prompt"])
        for msg in scenario.setup["messages"]:
            self.context_manager.add_message(msg["role"], msg["content"])
        
        usage = self.context_manager.get_context_usage()
        
        return {
            "passed": usage.headroom_tokens > 0,
            "system_tokens": usage.system_prompt_tokens,
            "history_tokens": usage.conversation_history_tokens,
            "headroom": usage.headroom_tokens,
        }

    def run_full_pipeline_test(self, scenario: DMTestScenario) -> dict:
        """Run full pipeline test."""
        if not self.services_available:
            return {"passed": False, "error": f"Services not available: {self.import_error}"}
        
        from src.domain.value_objects.difficulty import DungeonMasterPlan, DifficultyMode
        
        plan = self.dungeon_master_service.create_plan(
            difficulty=DifficultyMode.NORMAL,
            total_levels=scenario.setup["total_levels"],
            theme=scenario.setup["theme"],
            story_outline=[],
            boss_chain=[],
            key_items=[],
            player_power_target=scenario.setup.get("player_power_target", {}),
        )
        
        return {
            "passed": plan is not None and plan.total_levels == scenario.setup["total_levels"],
            "plan_created": plan is not None,
            "total_levels": plan.total_levels if plan else 0,
        }

    def run_difficulty_scaling_test(self, scenario: DMTestScenario) -> dict:
        """Run difficulty scaling test."""
        if not self.services_available:
            return {"passed": False, "error": f"Services not available: {self.import_error}"}
        
        from src.domain.value_objects.difficulty import DifficultyMode
        
        scaling_factors = {}
        loot_modifiers = {}
        
        for diff in scenario.setup["difficulties"]:
            mode = DifficultyMode(diff)
            scaling_factors[diff] = self.dungeon_master_service.get_scaling_factor(mode)
            loot_modifiers[diff] = self.dungeon_master_service.get_loot_modifier(mode)
        
        expected = scenario.expected_outcomes
        passed = (
            scaling_factors.get("story") == expected["story_scaling"] and
            scaling_factors.get("normal") == expected["normal_scaling"] and
            scaling_factors.get("hard") == expected["hard_scaling"] and
            scaling_factors.get("nightmare") == expected["nightmare_scaling"]
        )
        
        return {
            "passed": passed,
            "scaling_factors": scaling_factors,
            "loot_modifiers": loot_modifiers,
        }

    def generate_report(self) -> str:
        """Generate human-readable test report."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        lines = [
            "=" * 60,
            "DM PLAYTESTER REPORT",
            "=" * 60,
            f"Total Tests: {total}",
            f"Passed: {passed}",
            f"Failed: {failed}",
            f"Pass Rate: {passed/total*100:.1f}%" if total > 0 else "N/A",
            "",
            "-" * 60,
            "DETAILED RESULTS",
            "-" * 60,
        ]
        
        for result in self.results:
            status = "PASS" if result.passed else "FAIL"
            lines.append(f"[{status}] {result.scenario_name} ({result.duration_ms:.1f}ms)")
            if result.error:
                lines.append(f"       Error: {result.error}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)


def main():
    """Main entry point for running DM playtester."""
    playtester = DMPlaytester()
    results = playtester.run_all_tests()
    report = playtester.generate_report()
    print(report)
    
    # Return exit code based on results
    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())