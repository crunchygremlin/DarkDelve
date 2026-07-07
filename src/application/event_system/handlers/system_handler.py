"""
System event handler for processing system-related events.
"""
from typing import Dict, Any, Optional
from ..base_event import Event, EventCategory
from ..event_handler import EventHandler
from src.application.services.dynamic_difficulty_service import ApplicationDynamicDifficultyService


class SystemEventHandler(EventHandler):
    """
    Event handler for system-related events.

    Handles system events like errors, warnings, and game state changes.
    """

    def __init__(self, handler_id: str = "system_handler"):
        """
        Initialize the system event handler.

        Args:
            handler_id: Unique identifier for the handler
        """
        super().__init__(
            handler_id,
            [
                EventCategory.SYSTEM_ERROR,
                EventCategory.SYSTEM_WARNING,
                EventCategory.SYSTEM_INFO,
                EventCategory.SYSTEM_DEBUG,
                EventCategory.GAME_START,
                EventCategory.GAME_PAUSE,
                EventCategory.GAME_RESUME,
                EventCategory.GAME_END,
                EventCategory.GAME_SAVE,
                EventCategory.GAME_LOAD
            ]
        )

    def handle_event(self, event: Event) -> bool:
        """
        Handle a system event.

        Args:
            event: The system event to handle

        Returns:
            bool: True if the event was handled successfully, False otherwise
        """
        try:
            event_type = event.event_type

            if event_type == EventCategory.SYSTEM_ERROR:
                return self.handle_system_error(event)
            elif event_type == EventCategory.SYSTEM_WARNING:
                return self.handle_system_warning(event)
            elif event_type == EventCategory.SYSTEM_INFO:
                return self.handle_system_info(event)
            elif event_type == EventCategory.SYSTEM_DEBUG:
                return self.handle_system_debug(event)
            elif event_type == EventCategory.GAME_START:
                return self.handle_game_start(event)
            elif event_type == EventCategory.GAME_PAUSE:
                return self.handle_game_pause(event)
            elif event_type == EventCategory.GAME_RESUME:
                return self.handle_game_resume(event)
            elif event_type == EventCategory.GAME_END:
                return self.handle_game_end(event)
            elif event_type == EventCategory.GAME_SAVE:
                return self.handle_game_save(event)
            elif event_type == EventCategory.GAME_LOAD:
                return self.handle_game_load(event)
            else:
                return False

        except Exception as e:
            print(f"Error in system handler {self.handler_id}: {e}")
            return False

    def handle_system_error(self, event: Event) -> bool:
        """
        Handle system error event.

        Args:
            event: The system error event

        Returns:
            bool: True if handled successfully
        """
        error_message = event.data.get('message', 'Unknown error')
        error_code = event.data.get('code', 'UNKNOWN')
        source = event.data.get('source', 'unknown')

        print(f"SYSTEM ERROR [{error_code}]: {error_message} (source: {source})")

        # Add error handling logic here
        # - Log error to file
        # - Notify user
        # - Attempt recovery
        # - Update error statistics

        return True

    def handle_system_warning(self, event: Event) -> bool:
        """
        Handle system warning event.

        Args:
            event: The system warning event

        Returns:
            bool: True if handled successfully
        """
        warning_message = event.data.get('message', 'Unknown warning')
        warning_code = event.data.get('code', 'UNKNOWN')
        source = event.data.get('source', 'unknown')

        print(f"SYSTEM WARNING [{warning_code}]: {warning_message} (source: {source})")

        # Add warning handling logic here
        # - Log warning
        # - Notify user
        # - Monitor situation

        return True

    def handle_system_info(self, event: Event) -> bool:
        """
        Handle system info event.

        Args:
            event: The system info event

        Returns:
            bool: True if handled successfully
        """
        info_message = event.data.get('message', 'Unknown info')
        source = event.data.get('source', 'unknown')

        print(f"SYSTEM INFO: {info_message} (source: {source})")

        # Add info handling logic here
        # - Log info
        # - Update statistics

        return True

    def handle_system_debug(self, event: Event) -> bool:
        """
        Handle system debug event.

        Args:
            event: The system debug event

        Returns:
            bool: True if handled successfully
        """
        debug_message = event.data.get('message', 'Unknown debug')
        source = event.data.get('source', 'unknown')

        print(f"SYSTEM DEBUG: {debug_message} (source: {source})")

        # Add debug handling logic here
        # - Log debug info
        # - Only log if debug mode is enabled

        return True

    def handle_game_start(self, event: Event) -> bool:
        """
        Handle game start event.

        Args:
            event: The game start event

        Returns:
            bool: True if handled successfully
        """
        session_id = event.data.get('session_id', 'unknown')
        player_name = event.data.get('player_name', 'unknown')

        print(f"GAME START: Session {session_id}, Player {player_name}")

        # Add game start logic here
        # - Initialize game state
        # - Start systems
        # - Load initial content

        return True

    def handle_game_pause(self, event: Event) -> bool:
        """
        Handle game pause event.

        Args:
            event: The game pause event

        Returns:
            bool: True if handled successfully
        """
        session_id = event.data.get('session_id', 'unknown')
        reason = event.data.get('reason', 'unknown')

        print(f"GAME PAUSED: Session {session_id} (reason: {reason})")

        # Add game pause logic here
        # - Pause game systems
        # - Save current state
        # - Show pause menu

        return True

    def handle_game_resume(self, event: Event) -> bool:
        """
        Handle game resume event.

        Args:
            event: The game resume event

        Returns:
            bool: True if handled successfully
        """
        session_id = event.data.get('session_id', 'unknown')

        print(f"GAME RESUMED: Session {session_id}")

        # Add game resume logic here
        # - Resume game systems
        # - Restore game state
        # - Hide pause menu

        return True

    def handle_game_end(self, event: Event) -> bool:
        """
        Handle game end event.

        Args:
            event: The game end event

        Returns:
            bool: True if handled successfully
        """
        session_id = event.data.get('session_id', 'unknown')
        player_name = event.data.get('player_name', 'unknown')
        final_score = event.data.get('final_score', 0)

        print(f"GAME END: Session {session_id}, Player {player_name}, Score: {final_score}")

        # Add game end logic here
        # - Save final state
        # - Calculate final score
        # - Show end screen
        # - Clean up resources

        return True

    def handle_game_save(self, event: Event) -> bool:
        """
        Handle game save event.

        Args:
            event: The game save event

        Returns:
            bool: True if handled successfully
        """
        session_id = event.data.get('session_id', 'unknown')
        save_name = event.data.get('save_name', 'unknown')
        save_time = event.data.get('save_time', 'unknown')

        print(f"GAME SAVED: Session {session_id}, Save: {save_name}, Time: {save_time}")

        # Add game save logic here
        # - Serialize game state
        # - Write to storage
        # - Update save metadata

        return True

    def handle_game_load(self, event: Event) -> bool:
        """
        Handle game load event.

        Args:
            event: The game load event

        Returns:
            bool: True if handled successfully
        """
        session_id = event.data.get('session_id', 'unknown')
        save_name = event.data.get('save_name', 'unknown')
        load_time = event.data.get('load_time', 'unknown')

        print(f"GAME LOADED: Session {session_id}, Save: {save_name}, Time: {load_time}")

        # Add game load logic here
        # - Read from storage
        # - Deserialize game state
        # - Restore game state

        return True


class SystemHandler:
    """Handles system-level events including level changes for dynamic difficulty."""

    def __init__(self, event_bus: 'EventBus', dynamic_difficulty_service: Optional['ApplicationDynamicDifficultyService'] = None):
        self.event_bus = event_bus
        self.dynamic_difficulty_service = dynamic_difficulty_service
        self._register_handlers()

    def _register_handlers(self):
        """Register event handlers for level change events."""
        from ..event_handler import EventHandler
        
        # Create a handler for level change events
        class LevelChangeHandler(EventHandler):
            def __init__(self, system_handler_instance):
                super().__init__("system_handler_level_change", ["level_change"])
                self.system_handler = system_handler_instance
            
            def handle_event(self, event) -> bool:
                # Expect event.data to have 'old_level' and 'new_level'
                old_level = event.data.get('old_level')
                new_level = event.data.get('new_level')
                if old_level is not None and new_level is not None:
                    self.system_handler.handle_level_change(old_level, new_level)
                    return True
                return False
        
        # Register the handler with the event bus
        level_change_handler = LevelChangeHandler(self)
        self.event_bus.register_handler(level_change_handler)

    def handle_level_change(self, old_level: int, new_level: int):
        """Handle level change events by triggering difficulty evaluation."""
        if self.dynamic_difficulty_service is None:
            return

        # Delegate to the application service for dynamic difficulty
        self.dynamic_difficulty_service.handle_level_change(old_level, new_level)