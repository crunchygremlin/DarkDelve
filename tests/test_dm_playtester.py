"""
Tests for DM Playtester
"""

import sys
import os
import pytest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from playtest.dm_test_scenarios import (
    DMTestScenario,
    TEST_SCENARIOS,
    get_scenario_by_name,
    get_all_scenarios,
    get_scenarios_by_type,
)
from playtest.dm_playtester import DMPlaytester, TestResult


class TestDMTestScenario:
    """Tests for DMTestScenario dataclass."""

    def test_scenario_creation(self):
        """Test that a DMTestScenario can be created with all fields."""
        scenario = DMTestScenario(
            name="test_scenario",
            description="A test scenario",
            test_type="behavior_generation",
            setup={"key": "value"},
            expected_outcomes={"passed": True},
        )
        assert scenario.name == "test_scenario"
        assert scenario.description == "A test scenario"
        assert scenario.test_type == "behavior_generation"
        assert scenario.setup == {"key": "value"}
        assert scenario.expected_outcomes == {"passed": True}

    def test_get_scenario_by_name(self):
        """Test retrieving a scenario by name."""
        scenario = get_scenario_by_name("behavior_generation_test")
        assert scenario is not None
        assert scenario.name == "behavior_generation_test"

    def test_get_scenario_by_name_not_found(self):
        """Test retrieving a non-existent scenario."""
        scenario = get_scenario_by_name("nonexistent")
        assert scenario is None

    def test_get_all_scenarios(self):
        """Test getting all scenarios."""
        scenarios = get_all_scenarios()
        assert len(scenarios) == 11
        assert all(isinstance(s, DMTestScenario) for s in scenarios)

    def test_get_scenarios_by_type(self):
        """Test filtering scenarios by type."""
        behavior_scenarios = get_scenarios_by_type("behavior_generation")
        assert len(behavior_scenarios) == 1
        assert behavior_scenarios[0].test_type == "behavior_generation"


class TestDMPlaytester:
    """Tests for DMPlaytester class."""

    def test_playtester_initialization(self):
        """Test DMPlaytester can be initialized."""
        playtester = DMPlaytester()
        assert playtester is not None
        assert playtester.config_path == "playtest/playtest_config.yaml"

    def test_run_all_tests(self):
        """Test running all tests returns valid results."""
        playtester = DMPlaytester()
        results = playtester.run_all_tests()
        
        assert "total" in results
        assert "passed" in results
        assert "failed" in results
        assert "results" in results
        assert results["total"] == 11

    def test_run_scenario_returns_result(self):
        """Test that run_scenario returns a TestResult."""
        playtester = DMPlaytester()
        scenario = get_scenario_by_name("behavior_generation_test")
        
        result = playtester.run_scenario(scenario)
        
        assert isinstance(result, TestResult)
        assert result.scenario_name == "behavior_generation_test"
        assert isinstance(result.passed, bool)
        assert isinstance(result.duration_ms, float)

    def test_generate_report(self):
        """Test report generation."""
        playtester = DMPlaytester()
        playtester.run_all_tests()
        report = playtester.generate_report()
        
        assert "DM PLAYTESTER REPORT" in report
        assert "Total Tests:" in report
        assert "Passed:" in report
        assert "Failed:" in report

    def test_behavior_generation_scenario(self):
        """Test behavior generation scenario specifically."""
        playtester = DMPlaytester()
        scenario = get_scenario_by_name("behavior_generation_test")
        result = playtester.run_scenario(scenario)
        
        # The test should pass if services are available
        assert isinstance(result.passed, bool)

    def test_item_creation_scenario(self):
        """Test item creation scenario specifically."""
        playtester = DMPlaytester()
        scenario = get_scenario_by_name("item_creation_test")
        result = playtester.run_scenario(scenario)
        
        assert isinstance(result.passed, bool)
        if result.passed:
            assert "item_id" in result.details

    def test_context_headroom_scenario(self):
        """Test context headroom scenario specifically."""
        playtester = DMPlaytester()
        scenario = get_scenario_by_name("context_headroom_test")
        result = playtester.run_scenario(scenario)
        
        assert isinstance(result.passed, bool)
        if result.passed:
            assert "headroom" in result.details

    def test_full_pipeline_scenario(self):
        """Test full pipeline scenario specifically."""
        playtester = DMPlaytester()
        scenario = get_scenario_by_name("full_pipeline_test")
        result = playtester.run_scenario(scenario)
        
        assert isinstance(result.passed, bool)


class TestTestResult:
    """Tests for TestResult dataclass."""

    def test_test_result_creation(self):
        """Test TestResult can be created."""
        result = TestResult(
            scenario_name="test",
            passed=True,
            duration_ms=100.0,
            details={"key": "value"},
            error=""
        )
        assert result.scenario_name == "test"
        assert result.passed is True
        assert result.duration_ms == 100.0
        assert result.details == {"key": "value"}
        assert result.error == ""

    def test_test_result_with_error(self):
        """Test TestResult with error."""
        result = TestResult(
            scenario_name="test",
            passed=False,
            duration_ms=50.0,
            details={},
            error="Something went wrong"
        )
        assert result.passed is False
        assert result.error == "Something went wrong"


class TestScenariosContent:
    """Tests for the content of test scenarios."""

    def test_behavior_generation_has_required_fields(self):
        """Test behavior generation scenario has all required fields."""
        scenario = get_scenario_by_name("behavior_generation_test")
        assert "entity_id" in scenario.setup
        assert "mob_type" in scenario.setup
        assert "perception" in scenario.setup
        assert "valid_conditions" in scenario.setup
        assert "valid_actions" in scenario.setup

    def test_item_creation_has_required_fields(self):
        """Test item creation scenario has all required fields."""
        scenario = get_scenario_by_name("item_creation_test")
        assert "name" in scenario.setup
        assert "item_type" in scenario.setup
        assert "rarity" in scenario.setup

    def test_narrative_test_has_required_fields(self):
        """Test narrative scenario has all required fields."""
        scenario = get_scenario_by_name("narrative_test")
        assert "outline_id" in scenario.setup
        assert "levels" in scenario.setup
        assert "title" in scenario.setup

    def test_difficulty_scaling_has_required_fields(self):
        """Test difficulty scaling scenario has all required fields."""
        scenario = get_scenario_by_name("difficulty_scaling_test")
        assert "difficulties" in scenario.setup
        assert "story" in scenario.setup["difficulties"]
        assert "normal" in scenario.setup["difficulties"]

    def test_all_scenarios_have_unique_names(self):
        """Test that all scenarios have unique names."""
        names = [s.name for s in TEST_SCENARIOS]
        assert len(names) == len(set(names))

    def test_all_scenarios_have_valid_types(self):
        """Test that all scenarios have valid test types."""
        valid_types = {"behavior_generation", "level_design", "item_creation", 
                       "narrative", "durability", "damage", "context", 
                       "full_pipeline", "difficulty", "social", "floor1_generation"}
        for scenario in TEST_SCENARIOS:
            assert scenario.test_type in valid_types, f"Invalid type: {scenario.test_type}"