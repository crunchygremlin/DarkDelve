"""Social component for managing entity social state."""

from dataclasses import dataclass, field
from typing import Optional, List, Any
from src.domain.components.component import Component
from src.domain.value_objects.social import LoyaltyState

__all__ = ["SocialComponent"]


@dataclass
class SocialComponent(Component):
    """Component that manages an entity's social state."""
    entity_id: str = ""
    structure_id: Optional[str] = None
    rank: int = 99  # 0=leader, higher=lower rank
    role: str = "minion"  # "leader", "guard", "minion", "scout", "worker", "drone"
    loyalty: Optional[LoyaltyState] = None
    is_leader: bool = False
    personal_wealth: float = 0.0
    desired_items: List[str] = field(default_factory=list)

    @property
    def component_type(self) -> str:
        return "social"

    def can_give_orders(self) -> bool:
        """Check if this entity can give orders to others."""
        return self.is_leader or self.role in ("guard", "captain", "alpha")

    def will_follow_orders(self) -> bool:
        """Check if this entity will follow orders."""
        if self.is_leader:
            return True
        if self.loyalty is None:
            return True  # no loyalty system = default follow
        return self.loyalty.will_follow_orders()

    def update(self, delta_time: float, entity: Any) -> None:
        """Update component state (called each frame)."""
        pass  # Social state is updated via events by the orchestrator