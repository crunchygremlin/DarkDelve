"""
Pipeline execution engine.
Manages the actual execution of workflow stages using mode delegation.
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

@dataclass
class PipelineConfig:
    """Configuration for the pipeline."""
    auto_playtest: bool = True
    auto_debug: bool = True
    max_retries: int = 3
    test_command: str = "python -m pytest tests/ --tb=short -q"
    playtest_command: str = "python playtest/run_playtest.py --levels 3 --turns 100"
    context_budget_tokens: int = 8192
    
@dataclass
class StageConfig:
    """Configuration for a single pipeline stage."""
    stage: str
    mode: str
    enabled: bool = True
    retry_on_failure: bool = False
    timeout_seconds: int = 300
    parameters: Dict[str, Any] = field(default_factory=dict)

class Pipeline:
    """
    Executes the workflow pipeline by delegating to appropriate modes.
    """
    
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.stage_configs: List[StageConfig] = self._default_stages()
        self.execution_log: List[Dict[str, Any]] = []
    
    def _default_stages(self) -> List[StageConfig]:
        """Define default pipeline stages."""
        return [
            StageConfig(
                stage="orchestrator",
                mode="orchestrator",
                parameters={"analyze_dependencies": True, "break_down": True},
            ),
            StageConfig(
                stage="architect",
                mode="architect",
                enabled=False,  # Enabled by controller for moderate+ tasks
                parameters={"design_patterns": True, "integration_points": True},
            ),
            StageConfig(
                stage="coder",
                mode="code",
                parameters={"run_tests": True, "update_todos": True},
            ),
            StageConfig(
                stage="playtester",
                mode="play-testor",
                enabled=False,  # Enabled by controller
                parameters={"collect_telemetry": True, "analyze_results": True},
            ),
            StageConfig(
                stage="debugger",
                mode="debug",
                enabled=False,  # Enabled by controller on failure
                parameters={"analyze_errors": True, "suggest_fixes": True},
            ),
        ]
    
    def get_stage_config(self, stage: str) -> Optional[StageConfig]:
        """Get configuration for a specific stage."""
        for sc in self.stage_configs:
            if sc.stage == stage:
                return sc
        return None
    
    def enable_stage(self, stage: str, **parameters):
        """Enable a pipeline stage with optional parameter overrides."""
        sc = self.get_stage_config(stage)
        if sc:
            sc.enabled = True
            sc.parameters.update(parameters)
    
    def disable_stage(self, stage: str):
        """Disable a pipeline stage."""
        sc = self.get_stage_config(stage)
        if sc:
            sc.enabled = False
    
    def get_enabled_stages(self) -> List[str]:
        """Get list of enabled stages in order."""
        return [sc.stage for sc in self.stage_configs if sc.enabled]
    
    def log_execution(self, stage: str, result: Dict[str, Any]):
        """Log a pipeline execution."""
        self.execution_log.append({
            "stage": stage,
            "timestamp": time.time(),
            "result": result,
        })
    
    def get_execution_report(self) -> str:
        """Generate a report of the pipeline execution."""
        lines = ["=== PIPELINE EXECUTION REPORT ==="]
        for entry in self.execution_log:
            status = "✓" if entry["result"].get("success") else "✗"
            lines.append(f"  [{status}] {entry['stage']}: {entry['result'].get('output', 'N/A')[:80]}")
        return "\n".join(lines)