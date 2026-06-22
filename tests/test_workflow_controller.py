"""Tests for the workflow controller."""

import pytest
from src.application.workflow import (
    WorkflowController, TaskComplexity, WorkflowStage,
    TaskResult, WorkflowResult,
)

class TestTaskComplexityClassification:
    def test_simple_task(self):
        controller = WorkflowController()
        assert controller.classify_complexity("Fix typo in README") == TaskComplexity.SIMPLE
    
    def test_moderate_task(self):
        controller = WorkflowController()
        assert controller.classify_complexity("Add new feature to inventory") == TaskComplexity.MODERATE
    
    def test_complex_task(self):
        controller = WorkflowController()
        result = controller.classify_complexity("Implement multi-level dungeon system with DM agent")
        assert result in (TaskComplexity.COMPLEX, TaskComplexity.CRITICAL)
    
    def test_critical_task(self):
        controller = WorkflowController()
        result = controller.classify_complexity("Rewrite core game loop and save system")
        assert result == TaskComplexity.CRITICAL

class TestPlaytesterTrigger:
    def test_playtest_always_for_complex(self):
        controller = WorkflowController()
        assert controller.should_run_playtester(TaskComplexity.COMPLEX) is True
    
    def test_playtest_always_for_critical(self):
        controller = WorkflowController()
        assert controller.should_run_playtester(TaskComplexity.CRITICAL) is True
    
    def test_playtest_for_moderate_if_coder_succeeds(self):
        controller = WorkflowController()
        coder_result = TaskResult(stage="coder", success=True, output="OK")
        assert controller.should_run_playtester(TaskComplexity.MODERATE, coder_result) is True
    
    def test_no_playtest_for_moderate_if_coder_fails(self):
        controller = WorkflowController()
        coder_result = TaskResult(stage="coder", success=False, output="FAIL")
        assert controller.should_run_playtester(TaskComplexity.MODERATE, coder_result) is False
    
    def test_no_playtest_for_simple(self):
        controller = WorkflowController()
        assert controller.should_run_playtester(TaskComplexity.SIMPLE) is False

class TestDebuggerTrigger:
    def test_debug_for_critical_on_playtest_failure(self):
        controller = WorkflowController()
        play_result = TaskResult(stage="playtester", success=False, output="FAIL", errors=["test failed"])
        assert controller.should_run_debugger(TaskComplexity.CRITICAL, play_result) is True
    
    def test_debug_for_complex_on_playtest_failure(self):
        controller = WorkflowController()
        play_result = TaskResult(stage="playtester", success=False, output="FAIL", errors=["test failed"])
        assert controller.should_run_debugger(TaskComplexity.COMPLEX, play_result) is True
    
    def test_no_debug_for_simple(self):
        controller = WorkflowController()
        assert controller.should_run_debugger(TaskComplexity.SIMPLE) is False
    
    def test_debug_for_critical_on_coder_failure(self):
        controller = WorkflowController()
        code_result = TaskResult(stage="coder", success=False, output="FAIL", errors=["build error"])
        assert controller.should_run_debugger(TaskComplexity.CRITICAL, None, code_result) is True

class TestWorkflowExecution:
    def test_simple_workflow(self):
        controller = WorkflowController()
        result = controller.run_workflow("test-001", "Fix typo in README")
        assert result.final_success is True
        assert WorkflowStage.ORCHESTRATOR.value in result.stages_completed
        assert WorkflowStage.CODER.value in result.stages_completed
        assert result.playtest_triggered is False
    
    def test_complex_workflow(self):
        controller = WorkflowController()
        result = controller.run_workflow("test-002", "Implement multi-level dungeon system")
        assert result.final_success is True
        assert result.playtest_triggered is True
    
    def test_workflow_summary(self):
        controller = WorkflowController()
        result = controller.run_workflow("test-003", "Add item creation system")
        summary = result.summary()
        assert "test-003" in summary
        assert "SUCCESS" in summary

class TestPipeline:
    def test_default_stages(self):
        from src.application.workflow import Pipeline
        pipeline = Pipeline()
        enabled = pipeline.get_enabled_stages()
        assert "orchestrator" in enabled
        assert "coder" in enabled
        assert "playtester" not in enabled  # disabled by default
    
    def test_enable_stage(self):
        from src.application.workflow import Pipeline
        pipeline = Pipeline()
        pipeline.enable_stage("playtester")
        assert "playtester" in pipeline.get_enabled_stages()
    
    def test_disable_stage(self):
        from src.application.workflow import Pipeline
        pipeline = Pipeline()
        pipeline.disable_stage("architect")
        assert "architect" not in pipeline.get_enabled_stages()
    
    def test_execution_report(self):
        from src.application.workflow import Pipeline
        pipeline = Pipeline()
        pipeline.log_execution("orchestrator", {"success": True, "output": "OK"})
        report = pipeline.get_execution_report()
        assert "orchestrator" in report