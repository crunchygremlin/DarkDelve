"""
Event handler interface and implementation.
"""
from typing import Any, Dict, List, Optional, Callable
from abc import ABC, abstractmethod
from .base_event import Event, EventCategory, EventPriority


class EventHandler(ABC):
    """
    Abstract base class for event handlers.
    
    Implements the Observer pattern for handling events.
    """
    
    def __init__(self, handler_id: str, event_types: List[str]):
        """
        Initialize the event handler.
        
        Args:
            handler_id: Unique identifier for the handler
            event_types: List of event types this handler can process
        """
        self.handler_id = handler_id
        self.event_types = event_types
        self.enabled = True
        self.priority = EventPriority.NORMAL
    
    @abstractmethod
    def handle_event(self, event: Event) -> bool:
        """
        Handle an event.
        
        Args:
            event: The event to handle
            
        Returns:
            bool: True if the event was handled successfully, False otherwise
        """
        pass
    
    def can_handle(self, event: Event) -> bool:
        """
        Check if this handler can handle the given event.
        
        Args:
            event: The event to check
            
        Returns:
            bool: True if the handler can handle the event, False otherwise
        """
        return (
            self.enabled and
            event.event_type in self.event_types and
            not event.is_handled()
        )
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the handler.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.enabled = enabled
    
    def is_enabled(self) -> bool:
        """
        Check if the handler is enabled.
        
        Returns:
            bool: True if the handler is enabled, False otherwise
        """
        return self.enabled
    
    def set_priority(self, priority: int) -> None:
        """
        Set the handler priority.
        
        Args:
            priority: Handler priority
        """
        self.priority = priority
    
    def get_priority(self) -> int:
        """
        Get the handler priority.
        
        Returns:
            int: Handler priority
        """
        return self.priority


class LambdaEventHandler(EventHandler):
    """
    Event handler that uses a lambda function for handling events.
    
    Provides a flexible way to create event handlers without implementing a class.
    """
    
    def __init__(self, handler_id: str, event_types: List[str], handler_func: Callable[[Event], bool]):
        """
        Initialize the lambda event handler.
        
        Args:
            handler_id: Unique identifier for the handler
            event_types: List of event types this handler can process
            handler_func: Function to call when handling an event
        """
        super().__init__(handler_id, event_types)
        self.handler_func = handler_func
    
    def handle_event(self, event: Event) -> bool:
        """
        Handle an event using the lambda function.
        
        Args:
            event: The event to handle
            
        Returns:
            bool: True if the event was handled successfully, False otherwise
        """
        try:
            return self.handler_func(event)
        except Exception as e:
            print(f"Error in lambda handler {self.handler_id}: {e}")
            return False


class CompositeEventHandler(EventHandler):
    """
    Event handler that combines multiple handlers.
    
    Allows multiple handlers to be treated as a single handler.
    """
    
    def __init__(self, handler_id: str, event_types: List[str], handlers: List[EventHandler]):
        """
        Initialize the composite event handler.
        
        Args:
            handler_id: Unique identifier for the handler
            event_types: List of event types this handler can process
            handlers: List of handlers to combine
        """
        super().__init__(handler_id, event_types)
        self.handlers = handlers
    
    def handle_event(self, event: Event) -> bool:
        """
        Handle an event by delegating to all child handlers.
        
        Args:
            event: The event to handle
            
        Returns:
            bool: True if any handler handled the event successfully
        """
        success = False
        for handler in self.handlers:
            if handler.can_handle(event):
                if handler.handle_event(event):
                    success = True
                    if event.is_handled():
                        break
        return success
    
    def add_handler(self, handler: EventHandler) -> None:
        """
        Add a handler to the composite.
        
        Args:
            handler: Handler to add
        """
        self.handlers.append(handler)
    
    def remove_handler(self, handler_id: str) -> bool:
        """
        Remove a handler from the composite.
        
        Args:
            handler_id: ID of the handler to remove
            
        Returns:
            bool: True if handler was removed, False otherwise
        """
        for i, handler in enumerate(self.handlers):
            if handler.handler_id == handler_id:
                self.handlers.pop(i)
                return True
        return False
    
    def get_handlers(self) -> List[EventHandler]:
        """
        Get all handlers in the composite.
        
        Returns:
            List[EventHandler]: List of handlers
        """
        return self.handlers.copy()


class ConditionalEventHandler(EventHandler):
    """
    Event handler that only handles events if a condition is met.
    
    Provides conditional logic for event handling.
    """
    
    def __init__(self, handler_id: str, event_types: List[str], condition_func: Callable[[Event], bool], 
                 handler_func: Callable[[Event], bool]):
        """
        Initialize the conditional event handler.
        
        Args:
            handler_id: Unique identifier for the handler
            event_types: List of event types this handler can process
            condition_func: Function to check if the handler should process the event
            handler_func: Function to call when handling an event
        """
        super().__init__(handler_id, event_types)
        self.condition_func = condition_func
        self.handler_func = handler_func
    
    def handle_event(self, event: Event) -> bool:
        """
        Handle an event only if the condition is met.
        
        Args:
            event: The event to handle
            
        Returns:
            bool: True if the event was handled successfully, False otherwise
        """
        if not self.condition_func(event):
            return False
        
        try:
            return self.handler_func(event)
        except Exception as e:
            print(f"Error in conditional handler {self.handler_id}: {e}")
            return False


class LoggingEventHandler(EventHandler):
    """
    Event handler that logs events.
    
    Provides debugging and monitoring capabilities.
    """
    
    def __init__(self, handler_id: str = "logger", event_types: List[str] = None, 
                 log_level: str = "INFO"):
        """
        Initialize the logging event handler.
        
        Args:
            handler_id: Unique identifier for the handler
            event_types: List of event types to log (None for all)
            log_level: Logging level ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        """
        super().__init__(handler_id, event_types or ["*"])
        self.log_level = log_level
    
    def handle_event(self, event: Event) -> bool:
        """
        Log the event.
        
        Args:
            event: The event to log
            
        Returns:
            bool: True if the event was logged successfully
        """
        try:
            import logging
            
            # Create logger if it doesn't exist
            logger = logging.getLogger(f"event_handler_{self.handler_id}")
            logger.setLevel(getattr(logging, self.log_level))
            
            # Create handler if it doesn't exist
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
            
            # Log the event
            message = f"Event: {event.event_type} from {event.source}"
            if event.data:
                message += f" | Data: {event.data}"
            
            logger.log(getattr(logging, self.log_level), message)
            return True
            
        except Exception as e:
            print(f"Error in logging handler {self.handler_id}: {e}")
            return False