"""Behavior component for managing entity behavior scripts."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from src.domain.components.component import Component
from src.domain.value_objects.behavior_script import BehaviorScript, BehaviorAction

__all__ = ["BehaviorComponent"]


@dataclass
class BehaviorComponent(Component):
    """Component that manages an entity's behavior script."""
    entity_id: str = ""
    current_script: Optional[BehaviorScript] = None
    last_action: Optional[BehaviorAction] = None
    last_evaluated_tick: int = 0
    evaluation_interval: int = 1  # ticks between evaluations
    state: Dict[str, Any] = field(default_factory=dict)

    @property
    def component_type(self) -> str:
        return "behavior"

    def set_script(self, script: BehaviorScript):
        """Set the current behavior script."""
        self.current_script = script
        self.state.clear()

    def should_evaluate(self, tick: int) -> bool:
        """Check if the script should be evaluated this tick."""
        return (tick - self.last_evaluated_tick) >= self.evaluation_interval

    def record_evaluation(self, tick: int, action: Optional[BehaviorAction]):
        """Record the evaluation result."""
        self.last_evaluated_tick = tick
        self.last_action = action

    def update(self, delta_time: float, entity: Any) -> None:
        """Update component state (called each frame)."""
        pass  # Behavior is evaluated via record_evaluation() by the orchestrator