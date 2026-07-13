"""Application service for coordinating dynamic difficulty adjustment."""

from typing import Optional
from dataclasses import dataclass

from src.domain.services.dynamic_difficulty_service import DynamicDifficultyService, DifficultyAdjustment
from src.application.event_system.event_bus import EventBus
from src.application.event_system.base_event import Event, EventCategory
from src.application.game_session.game_session import GameSession
from src.domain.entities.entity import Entity


@dataclass
class LevelChangedEventData:
    """Event data for level change events."""
    old_level: int
    new_level: int
    player_entity: Optional['Entity'] = None


@dataclass
class DifficultyAdjustedEventData:
    """Event data for difficulty adjusted events."""
    level_number: int
    adjustment: DifficultyAdjustment


class ApplicationDynamicDifficultyService:
    """Application service that coordinates dynamic difficulty adjustment."""

    def __init__(
        self,
        domain_service: 'DynamicDifficultyService',
        event_bus: 'EventBus',
        game_session: 'GameSession'
    ):
        self.domain_service = domain_service
        self.event_bus = event_bus
        self.game_session = game_session
        self._register_event_handlers()

    def _register_event_handlers(self):
        """Register for level change events and difficulty adjusted events."""
        from ..event_system.event_handler import EventHandler
        
        # Handler for level change events
        class LevelChangeHandler(EventHandler):
            def __init__(self, service_instance):
                super().__init__("difficulty_service_level_change", ["level_change"])
                self.service = service_instance
            
            def handle_event(self, event) -> bool:
                old_level = event.data.get('old_level')
                new_level = event.data.get('new_level')
                if old_level is not None and new_level is not None:
                    self.service.handle_level_change(old_level, new_level)
                    return True
                return False
        
        # Handler for difficulty adjusted events (for logging/UI updates)
        class DifficultyAdjustedHandler(EventHandler):
            def __init__(self, service_instance):
                super().__init__("difficulty_service_difficulty_adjusted", ["difficulty_adjusted"])
                self.service = service_instance
            
            def handle_event(self, event) -> bool:
                # Log the difficulty adjustment for debugging/UI
                level_number = event.data.get('level_number')
                adjustment = event.data.get('adjustment')
                if level_number is not None and adjustment is not None:
                    # Example logging - can be extended for UI updates, achievements, etc.
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"Difficulty adjusted for level {level_number}: {adjustment}")
                    return True
                return False
        
        # Register handlers
        level_change_handler = LevelChangeHandler(self)
        difficulty_adjusted_handler = DifficultyAdjustedHandler(self)
        self.event_bus.register_handler(level_change_handler)
        self.event_bus.register_handler(difficulty_adjusted_handler)

    def handle_level_change(self, old_level: int, new_level: int):
        """Handle level change events by triggering difficulty evaluation."""
        player_entity = self.game_session.player
        if player_entity is None:
            return

        # Evaluate and adjust difficulty using 50% of player stats
        adjustment = self.domain_service.evaluate_and_adjust_difficulty(
            player_entity=player_entity,
            current_level=new_level
        )

        # Apply adjustment to level generation services
        self._apply_difficulty_adjustment(adjustment, new_level)