"""
Event bus for managing event handling and distribution.
"""
from typing import Any, Dict, List, Optional, Callable
import threading
import heapq
from queue import Queue, Empty
from datetime import datetime
import time

from .base_event import Event, EventCategory, EventPriority
from .event_handler import EventHandler


class EventBus:
    """
    Central event bus for managing event handling and distribution.
    
    Implements the Publisher-Subscriber pattern for event-driven architecture.
    """
    
    def __init__(self, max_queue_size: int = 10000, enable_async: bool = False):
        """
        Initialize the event bus.
        
        Args:
            max_queue_size: Maximum number of events to queue
            enable_async: Enable asynchronous event processing
        """
        self.max_queue_size = max_queue_size
        self.enable_async = enable_async
        
        # Event storage
        self.event_queue: List[Event] = []
        self.event_history: List[Event] = []
        self.max_history = 1000
        
        # Handler management
        self.handlers: Dict[str, List[EventHandler]] = {}
        self.handler_priorities: Dict[str, int] = {}
        
        # Threading for async processing
        self.processing_thread = None
        self.stop_processing = False
        self.event_queue_mutex = threading.Lock()
        self.processing_mutex = threading.Lock()
        
        # Statistics
        self.stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "handlers_registered": 0,
            "processing_time": 0.0
        }
        
        # Start async processing if enabled
        if self.enable_async:
            self.start_async_processing()
    
    def register_handler(self, handler: EventHandler) -> bool:
        """
        Register an event handler.
        
        Args:
            handler: The handler to register
            
        Returns:
            bool: True if handler was registered successfully, False otherwise
        """
        try:
            # Register handler for each event type
            for event_type in handler.event_types:
                if event_type not in self.handlers:
                    self.handlers[event_type] = []
                
                # Check if handler already exists
                for existing_handler in self.handlers[event_type]:
                    if existing_handler.handler_id == handler.handler_id:
                        return False
                
                self.handlers[event_type].append(handler)
            
            # Update handler priority
            self.handler_priorities[handler.handler_id] = handler.get_priority()
            self.stats["handlers_registered"] += 1
            
            return True
            
        except Exception as e:
            print(f"Error registering handler {handler.handler_id}: {e}")
            return False
    
    def unregister_handler(self, handler_id: str, event_type: Optional[str] = None) -> bool:
        """
        Unregister an event handler.
        
        Args:
            handler_id: ID of the handler to unregister
            event_type: Optional event type to unregister from (None for all)
            
        Returns:
            bool: True if handler was unregistered successfully, False otherwise
        """
        try:
            if event_type:
                # Unregister from specific event type
                if event_type in self.handlers:
                    self.handlers[event_type] = [
                        h for h in self.handlers[event_type] 
                        if h.handler_id != handler_id
                    ]
                    
                    # Remove empty event types
                    if not self.handlers[event_type]:
                        del self.handlers[event_type]
            else:
                # Unregister from all event types
                for event_type in list(self.handlers.keys()):
                    self.handlers[event_type] = [
                        h for h in self.handlers[event_type] 
                        if h.handler_id != handler_id
                    ]
                    
                    # Remove empty event types
                    if not self.handlers[event_type]:
                        del self.handlers[event_type]
            
            # Remove from priorities
            if handler_id in self.handler_priorities:
                del self.handler_priorities[handler_id]
            
            return True
            
        except Exception as e:
            print(f"Error unregistering handler {handler_id}: {e}")
            return False
    
    def publish_event(self, event: Event) -> bool:
        """
        Publish an event to the event bus.
        
        Args:
            event: The event to publish
            
        Returns:
            bool: True if event was published successfully, False otherwise
        """
        try:
            # Add timestamp if not present
            if event.timestamp is None:
                event.timestamp = datetime.now()
            
            # Add to queue
            with self.event_queue_mutex:
                if len(self.event_queue) >= self.max_queue_size:
                    # Remove oldest event if queue is full
                    heapq.heappop(self.event_queue)
                
                # Add event to priority queue
                heapq.heappush(self.event_queue, (-event.priority, event))
                
                # Add to history
                self.event_history.append(event)
                if len(self.event_history) > self.max_history:
                    self.event_history.pop(0)
            
            # Update statistics
            self.stats["events_published"] += 1
            
            return True
            
        except Exception as e:
            print(f"Error publishing event {event.event_id}: {e}")
            self.stats["events_failed"] += 1
            return False
    
    def publish_event_by_type(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
        category: Optional['EventCategory'] = None
    ) -> bool:
        """
        Publish an event by string type identifier.
        
        This is a convenience method for publishing events with just a type string,
        useful for backward compatibility and simple event publishing.
        
        Args:
            event_type: String identifier for the event type
            data: Optional data payload for the event
            category: Optional event category (defaults to SYSTEM)
            
        Returns:
            bool: True if event was published successfully, False otherwise
        """
        from .base_event import EventCategory
        from src.shared.events.event import EventType
        
        event = Event(
            category=category or EventCategory.SYSTEM,
            event_type=EventType(event_type) if event_type in [e.value for e in EventType] else None,
            data=data or {}
        )
        return self.publish_event(event)
    
    def publish_event_sync(self, event: Event) -> bool:
        """
        Publish and process an event synchronously.
        
        Args:
            event: The event to publish and process
            
        Returns:
            bool: True if event was processed successfully, False otherwise
        """
        try:
            # Publish the event
            if not self.publish_event(event):
                return False
            
            # Process the event immediately
            return self.process_event(event)
            
        except Exception as e:
            print(f"Error in sync event processing: {e}")
            return False
    
    def process_event(self, event: Event) -> bool:
        """
        Process a single event.
        
        Args:
            event: The event to process
            
        Returns:
            bool: True if event was processed successfully, False otherwise
        """
        start_time = time.time()
        success = False
        
        try:
            # Get handlers for this event type
            handlers = self.handlers.get(event.event_type, [])
            
            # Sort handlers by priority
            sorted_handlers = sorted(
                handlers,
                key=lambda h: h.get_priority(),
                reverse=True
            )
            
            # Process event with each handler
            for handler in sorted_handlers:
                if handler.can_handle(event):
                    if handler.handle_event(event):
                        success = True
                        if event.is_handled():
                            break
            
            # Update statistics
            self.stats["events_processed"] += 1
            if not success:
                self.stats["events_failed"] += 1
            
            return success
            
        except Exception as e:
            print(f"Error processing event {event.event_id}: {e}")
            self.stats["events_failed"] += 1
            return False
        
        finally:
            # Update processing time
            self.stats["processing_time"] += time.time() - start_time
    
    def process_events_async(self) -> None:
        """
        Process events asynchronously in a separate thread.
        """
        while not self.stop_processing:
            try:
                # Get next event from queue
                with self.event_queue_mutex:
                    if self.event_queue:
                        _, event = heapq.heappop(self.event_queue)
                    else:
                        event = None
                
                if event:
                    # Process the event
                    self.process_event(event)
                else:
                    # No events, wait a bit
                    time.sleep(0.01)
                    
            except Exception as e:
                print(f"Error in async event processing: {e}")
                time.sleep(0.1)
    
    def start_async_processing(self) -> None:
        """
        Start asynchronous event processing.
        """
        if not self.enable_async:
            return
        
        self.stop_processing = False
        self.processing_thread = threading.Thread(
            target=self.process_events_async,
            daemon=True
        )
        self.processing_thread.start()
    
    def stop_async_processing(self) -> None:
        """
        Stop asynchronous event processing.
        """
        self.stop_processing = True
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
    
    def get_event_history(self, event_type: Optional[str] = None, 
                         limit: int = 100) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Optional event type filter
            limit: Maximum number of events to return
            
        Returns:
            List[Event]: List of events
        """
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events[-limit:]
    
    def get_handlers(self, event_type: Optional[str] = None) -> List[EventHandler]:
        """
        Get registered handlers.
        
        Args:
            event_type: Optional event type filter
            
        Returns:
            List[EventHandler]: List of handlers
        """
        if event_type:
            return self.handlers.get(event_type, [])
        else:
            # Return all handlers (deduplicated)
            all_handlers = set()
            for handlers in self.handlers.values():
                all_handlers.update(handlers)
            return list(all_handlers)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get event bus statistics.
        
        Returns:
            Dict[str, Any]: Event bus statistics
        """
        return {
            "events_published": self.stats["events_published"],
            "events_processed": self.stats["events_processed"],
            "events_failed": self.stats["events_failed"],
            "handlers_registered": self.stats["handlers_registered"],
            "processing_time": self.stats["processing_time"],
            "queue_size": len(self.event_queue),
            "history_size": len(self.event_history),
            "handlers_count": len(self.handler_priorities),
            "async_enabled": self.enable_async
        }
    
    def clear_queue(self) -> None:
        """Clear the event queue."""
        with self.event_queue_mutex:
            self.event_queue.clear()
    
    def clear_history(self) -> None:
        """Clear the event history."""
        self.event_history.clear()
    
    def reset_statistics(self) -> None:
        """Reset event bus statistics."""
        self.stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "handlers_registered": 0,
            "processing_time": 0.0
        }
    
    def shutdown(self) -> None:
        """Shutdown the event bus."""
        self.stop_async_processing()
        self.clear_queue()
        self.clear_history()
        self.reset_statistics()
    
    def __del__(self):
        """Cleanup when event bus is destroyed."""
        self.shutdown()