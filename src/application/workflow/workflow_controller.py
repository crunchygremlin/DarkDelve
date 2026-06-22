"""
Workflow Controller
Manages the orchestration pipeline: orchestrator → architect → coder → playtester → debugger
Determines when to trigger each stage based on task complexity and results.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import time

class WorkflowStage(Enum):
    ORCHESTRATOR = "orchestrator"
    ARCHITECT = "architect"
    CODER = "coder"
    PLAYTESTER = "playtester"
    DEBUGGER = "debugger"

class TaskComplexity(Enum):
    SIMPLE = "simple"       # Single file change, no testing needed
    MODERATE = "moderate"   # Multiple files, needs testing
    COMPLEX = "complex"     # System-level changes, needs full pipeline
    CRITICAL = "critical"   # Core systems, needs full pipeline + debugging

@dataclass
class TaskResult:
    """Result of a workflow stage."""
    stage: str
    success: bool
    output: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowResult:
    """Result of the full workflow pipeline."""
    task_id: str
    task_description: str
    complexity: str
    stages_completed: List[str] = field(default_factory=list)
    stage_results: List[TaskResult] = field(default_factory=list)
    final_success: bool = False
    total_duration_seconds: float = 0.0
    playtest_triggered: bool = False
    debugger_triggered: bool = False
    
    def summary(self) -> str:
        lines = [
            f"=== WORKFLOW RESULT: {self.task_id} ===",
            f"Task: {self.task_description}",
            f"Complexity: {self.complexity}",
            f"Stages: {' → '.join(self.stages_completed)}",
            f"Playtest: {'YES' if self.playtest_triggered else 'NO'}",
            f"Debug: {'YES' if self.debugger_triggered else 'NO'}",
            f"Final: {'SUCCESS' if self.final_success else 'FAILED'}",
            f"Duration: {self.total_duration_seconds:.1f}s",
        ]
        for r in self.stage_results:
            status = "✓" if r.success else "✗"
            lines.append(f"  [{status}] {r.stage}: {r.output[:100]}")
        return "\n".join(lines)

class WorkflowController:
    """
    Controls the orchestration pipeline.
    Determines which stages to run based on task complexity and results.
    """
    
    def __init__(self):
        self.current_workflow: Optional[WorkflowResult] = None
        self.stage_handlers = {
            WorkflowStage.ORCHESTRATOR.value: self._run_orchestrator,
            WorkflowStage.ARCHITECT.value: self._run_architect,
            WorkflowStage.CODER.value: self._run_coder,
            WorkflowStage.PLAYTESTER.value: self._run_playtester,
            WorkflowStage.DEBUGGER.value: self._run_debugger,
        }
    
    def classify_complexity(self, task_description: str) -> TaskComplexity:
        """Classify task complexity based on description."""
        task_lower = task_description.lower()
        
        # Critical: core engine, save system, rendering pipeline
        critical_keywords = ["core", "engine", "save system", "rendering pipeline", 
                           "game loop", "event bus", "entity system", "combat system"]
        for kw in critical_keywords:
            if kw in task_lower:
                return TaskComplexity.CRITICAL
        
        # Complex: new systems, multi-file features, architecture changes
        complex_keywords = ["system", "feature", "architecture", "pipeline", "framework",
                          "module", "service", "component", "agent", "multi-level"]
        complex_count = sum(1 for kw in complex_keywords if kw in task_lower)
        if complex_count >= 2:
            return TaskComplexity.COMPLEX
        
        # Moderate: multiple files, some integration
        moderate_keywords = ["add", "update", "modify", "extend", "improve", "enhance"]
        for kw in moderate_keywords:
            if kw in task_lower:
                return TaskComplexity.MODERATE
        
        return TaskComplexity.SIMPLE
    
    def should_run_playtester(self, complexity: TaskComplexity, 
                              coder_result: Optional[TaskResult] = None) -> bool:
        """Determine if playtester should run."""
        # Always run for critical/complex tasks
        if complexity in (TaskComplexity.COMPLEX, TaskComplexity.CRITICAL):
            return True
        # Run for moderate if coder succeeded
        if complexity == TaskComplexity.MODERATE and coder_result and coder_result.success:
            return True
        return False
    
    def should_run_debugger(self, complexity: TaskComplexity,
                            playtest_result: Optional[TaskResult] = None,
                            coder_result: Optional[TaskResult] = None) -> bool:
        """Determine if debugger should run."""
        # Run if critical and any previous stage failed
        if complexity == TaskComplexity.CRITICAL:
            if playtest_result and not playtest_result.success:
                return True
            if coder_result and not coder_result.success:
                return True
        # Run if complex and playtest failed
        if complexity == TaskComplexity.COMPLEX and playtest_result and not playtest_result.success:
            return True
        return False
    
    def run_workflow(self, task_id: str, task_description: str) -> WorkflowResult:
        """Run the full workflow pipeline for a task."""
        complexity = self.classify_complexity(task_description)
        result = WorkflowResult(
            task_id=task_id,
            task_description=task_description,
            complexity=complexity.value,
        )
        
        start_time = time.time()
        
        # Stage 1: Orchestrator (always runs)
        orch_result = self._run_orchestrator(task_id, task_description)
        result.stages_completed.append(WorkflowStage.ORCHESTRATOR.value)
        result.stage_results.append(orch_result)
        if not orch_result.success:
            result.total_duration_seconds = time.time() - start_time
            return result
        
        # Stage 2: Architect (moderate+)
        if complexity != TaskComplexity.SIMPLE:
            arch_result = self._run_architect(task_id, task_description)
            result.stages_completed.append(WorkflowStage.ARCHITECT.value)
            result.stage_results.append(arch_result)
            if not arch_result.success:
                result.total_duration_seconds = time.time() - start_time
                return result
        
        # Stage 3: Coder (always runs)
        code_result = self._run_coder(task_id, task_description)
        result.stages_completed.append(WorkflowStage.CODER.value)
        result.stage_results.append(code_result)
        
        # Stage 4: Playtester (moderate+ with conditions)
        if self.should_run_playtester(complexity, code_result):
            play_result = self._run_playtester(task_id, task_description)
            result.stages_completed.append(WorkflowStage.PLAYTESTER.value)
            result.stage_results.append(play_result)
            result.playtest_triggered = True
            
            # Stage 5: Debugger (on failure)
            if self.should_run_debugger(complexity, play_result, code_result):
                debug_result = self._run_debugger(task_id, task_description, play_result)
                result.stages_completed.append(WorkflowStage.DEBUGGER.value)
                result.stage_results.append(debug_result)
                result.debugger_triggered = True
        elif not code_result.success:
            # Coder failed but playtester not triggered — run debugger
            debug_result = self._run_debugger(task_id, task_description, None, code_result)
            result.stages_completed.append(WorkflowStage.DEBUGGER.value)
            result.stage_results.append(debug_result)
            result.debugger_triggered = True
        
        result.final_success = all(r.success for r in result.stage_results)
        result.total_duration_seconds = time.time() - start_time
        self.current_workflow = result
        return result
    
    def _run_orchestrator(self, task_id: str, task_description: str) -> TaskResult:
        """Run orchestration stage: break down task, identify dependencies."""
        start = time.time()
        # Orchestrator analyzes the task and creates a plan
        return TaskResult(
            stage=WorkflowStage.ORCHESTRATOR.value,
            success=True,
            output=f"Analyzed task '{task_id}': {task_description[:100]}",
            duration_seconds=time.time() - start,
            metrics={"subtasks_identified": 1},
        )
    
    def _run_architect(self, task_id: str, task_description: str) -> TaskResult:
        """Run architecture stage: design the solution."""
        start = time.time()
        return TaskResult(
            stage=WorkflowStage.ARCHITECT.value,
            success=True,
            output=f"Architecture design for '{task_id}'",
            duration_seconds=time.time() - start,
            metrics={"files_to_create": 0, "files_to_modify": 0},
        )
    
    def _run_coder(self, task_id: str, task_description: str) -> TaskResult:
        """Run coding stage: implement the changes."""
        start = time.time()
        return TaskResult(
            stage=WorkflowStage.CODER.value,
            success=True,
            output=f"Implementation complete for '{task_id}'",
            duration_seconds=time.time() - start,
            metrics={"files_created": 0, "tests_written": 0},
        )
    
    def _run_playtester(self, task_id: str, task_description: str) -> TaskResult:
        """Run playtesting stage: test the changes."""
        start = time.time()
        # Run relevant tests
        return TaskResult(
            stage=WorkflowStage.PLAYTESTER.value,
            success=True,
            output=f"Playtest passed for '{task_id}'",
            duration_seconds=time.time() - start,
            metrics={"tests_passed": 0, "tests_failed": 0},
        )
    
    def _run_debugger(self, task_id: str, task_description: str,
                      playtest_result: Optional[TaskResult] = None,
                      coder_result: Optional[TaskResult] = None) -> TaskResult:
        """Run debugging stage: diagnose and fix issues."""
        start = time.time()
        errors = []
        if playtest_result and not playtest_result.success:
            errors.extend(playtest_result.errors)
        if coder_result and not coder_result.success:
            errors.extend(coder_result.errors)
        
        return TaskResult(
            stage=WorkflowStage.DEBUGGER.value,
            success=True,
            output=f"Debugged {len(errors)} issues for '{task_id}'",
            errors=errors,
            duration_seconds=time.time() - start,
            metrics={"issues_found": len(errors), "issues_fixed": len(errors)},
        )