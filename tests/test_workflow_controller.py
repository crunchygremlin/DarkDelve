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

class TestDebuggerTrigger:
    """Tests for debugger trigger logic (playtester removed)."""
    def test_debug_for_critical_on_coder_failure(self):
        controller = WorkflowController()
        code_result = TaskResult(stage="coder", success=False, output="FAIL", errors=["build error"])
        assert controller.should_run_debugger(TaskComplexity.CRITICAL, None, code_result) is True
    
    def test_debug_for_complex_on_coder_failure(self):
        controller = WorkflowController()
        code_result = TaskResult(stage="coder", success=False, output="FAIL", errors=["build error"])
        assert controller.should_run_debugger(TaskComplexity.COMPLEX, None, code_result) is True
    
    def test_no_debug_for_simple_on_success(self):
        controller = WorkflowController()
        code_result = TaskResult(stage="coder", success=True, output="OK")
        assert controller.should_run_debugger(TaskComplexity.SIMPLE, None, code_result) is False
    
    def test_no_debug_for_moderate_on_success(self):
        controller = WorkflowController()
        code_result = TaskResult(stage="coder", success=True, output="OK")
        assert controller.should_run_debugger(TaskComplexity.MODERATE, None, code_result) is False

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
        assert result.playtest_triggered is False  # Playtester removed
    
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
        pipeline.enable_stage("debugger")
        assert "debugger" in pipeline.get_enabled_stages()
    
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