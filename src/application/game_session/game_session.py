"""
Game session management for the application layer.
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json

from ..game_commands.base_command import BaseCommand, CommandResult
from ..game_queries.base_query import BaseQuery, QueryResult
from ...domain.entities.player import Player
from ...domain.entities.mob import Mob
from ...domain.entities.item import Item
from ...domain.value_objects.position import Position


@dataclass
class SessionState:
    """Represents the state of a game session."""
    session_id: str
    player_id: str
    current_level: int = 1
    current_area: str = "starting_area"
    game_time: str = "12:00"
    total_play_time: str = "0h 0m"
    is_paused: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class GameSession:
    """
    Manages a game session with state, commands, and queries.
    
    Implements the Session pattern for game state management.
    """
    
    def __init__(self, player: Player, session_id: Optional[str] = None):
        """
        Initialize the game session.
        
        Args:
            player: The player entity for this session
            session_id: Optional session ID (will be generated if not provided)
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.player = player
        self.state = SessionState(
            session_id=self.session_id,
            player_id=player.id
        )
        
        # Command and query history
        self.command_history: List[BaseCommand] = []
        self.query_history: List[BaseQuery] = []
        
        # Session-specific data
        self.entities: List[Any] = []
        self.items: List[Item] = []
        self.events: List[Dict[str, Any]] = []
        
        # Session configuration
        self.config = {
            "auto_save": True,
            "save_interval": 300,  # 5 minutes
            "max_history": 1000,
            "enable_undo": True,
            "max_undo_steps": 50
        }
        
        # Statistics
        self.statistics = {
            "commands_executed": 0,
            "queries_executed": 0,
            "enemies_defeated": 0,
            "items_collected": 0,
            "areas_explored": 1,
            "play_time": 0
        }
    
    def execute_command(self, command: BaseCommand, *args, **kwargs) -> CommandResult:
        """
        Execute a command within the session.
        
        Args:
            command: The command to execute
            *args: Command arguments
            **kwargs: Command keyword arguments
            
        Returns:
            CommandResult: The result of the command execution
        """
        try:
            # Execute the command
            result = command.execute(*args, **kwargs)
            
            # Add to history if successful
            if result.success:
                self.command_history.append(command)
                self.statistics["commands_executed"] += 1
                
                # Limit history size
                if len(self.command_history) > self.config["max_history"]:
                    self.command_history.pop(0)
                
                # Update last updated time
                self.state.last_updated = datetime.now()
                
                # Auto-save if enabled
                if self.config["auto_save"]:
                    self.save_state()
            
            return result
            
        except Exception as e:
            return CommandResult(
                success=False,
                error_message=f"Failed to execute command: {str(e)}"
            )
    
    def execute_query(self, query: BaseQuery, *args, **kwargs) -> QueryResult:
        """
        Execute a query within the session.
        
        Args:
            query: The query to execute
            *args: Query arguments
            **kwargs: Query keyword arguments
            
        Returns:
            QueryResult: The result of the query execution
        """
        try:
            # Execute the query
            result = query.execute(*args, **kwargs)
            
            # Add to history
            self.query_history.append(query)
            self.statistics["queries_executed"] += 1
            
            # Limit history size
            if len(self.query_history) > self.config["max_history"]:
                self.query_history.pop(0)
            
            # Update last updated time
            self.state.last_updated = datetime.now()
            
            return result
            
        except Exception as e:
            return QueryResult(
                success=False,
                error_message=f"Failed to execute query: {str(e)}"
            )
    
    def undo_command(self) -> CommandResult:
        """
        Undo the last executed command.
        
        Returns:
            CommandResult: The result of the undo operation
        """
        if not self.config["enable_undo"]:
            return CommandResult(
                success=False,
                error_message="Undo is disabled for this session"
            )
        
        if not self.command_history:
            return CommandResult(
                success=False,
                error_message="No commands to undo"
            )
        
        # Get the last command
        last_command = self.command_history.pop()
        
        try:
            # Undo the command
            result = last_command.undo()
            
            if result.success:
                # Update statistics
                self.statistics["commands_executed"] -= 1
                
                # Update last updated time
                self.state.last_updated = datetime.now()
                
                # Auto-save if enabled
                if self.config["auto_save"]:
                    self.save_state()
            
            return result
            
        except Exception as e:
            return CommandResult(
                success=False,
                error_message=f"Failed to undo command: {str(e)}"
            )
    
    def add_entity(self, entity: Any) -> None:
        """
        Add an entity to the session.
        
        Args:
            entity: The entity to add
        """
        self.entities.append(entity)
        self.add_event("entity_added", {"entity_id": entity.id, "entity_type": type(entity).__name__})
    
    def remove_entity(self, entity_id: str) -> bool:
        """
        Remove an entity from the session.
        
        Args:
            entity_id: ID of the entity to remove
            
        Returns:
            bool: True if entity was removed, False otherwise
        """
        for i, entity in enumerate(self.entities):
            if hasattr(entity, 'id') and entity.id == entity_id:
                self.entities.pop(i)
                self.add_event("entity_removed", {"entity_id": entity_id})
                return True
        return False
    
    def add_item(self, item: Item) -> None:
        """
        Add an item to the session.
        
        Args:
            item: The item to add
        """
        self.items.append(item)
        self.statistics["items_collected"] += 1
        self.add_event("item_added", {"item_id": item.id, "item_name": item.name})
    
    def remove_item(self, item_id: str) -> bool:
        """
        Remove an item from the session.
        
        Args:
            item_id: ID of the item to remove
            
        Returns:
            bool: True if item was removed, False otherwise
        """
        for i, item in enumerate(self.items):
            if item.id == item_id:
                self.items.pop(i)
                self.add_event("item_removed", {"item_id": item_id})
                return True
        return False
    
    def add_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Add an event to the session.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.events.append(event)
        
        # Limit event history
        if len(self.events) > 1000:
            self.events.pop(0)
    
    def get_events(self, event_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get events from the session.
        
        Args:
            event_type: Optional event type filter
            limit: Maximum number of events to return
            
        Returns:
            List[Dict[str, Any]]: List of events
        """
        events = self.events
        
        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
        
        return events[-limit:]
    
    def save_state(self) -> Dict[str, Any]:
        """
        Save the current session state.
        
        Returns:
            Dict[str, Any]: The saved state
        """
        state = {
            "session_id": self.session_id,
            "player_id": self.player.id,
            "state": {
                "current_level": self.state.current_level,
                "current_area": self.state.current_area,
                "game_time": self.state.game_time,
                "total_play_time": self.state.total_play_time,
                "is_paused": self.state.is_paused,
                "is_active": self.state.is_active,
                "created_at": self.state.created_at.isoformat(),
                "last_updated": self.state.last_updated.isoformat()
            },
            "statistics": self.statistics,
            "metadata": self.state.metadata
        }
        
        # Save to file or database
        # For now, we'll just return the state
        return state
    
    def load_state(self, state: Dict[str, Any]) -> bool:
        """
        Load a session state.
        
        Args:
            state: The state to load
            
        Returns:
            bool: True if state was loaded successfully, False otherwise
        """
        try:
            self.state.current_level = state["state"]["current_level"]
            self.state.current_area = state["state"]["current_area"]
            self.state.game_time = state["state"]["game_time"]
            self.state.total_play_time = state["state"]["total_play_time"]
            self.state.is_paused = state["state"]["is_paused"]
            self.state.is_active = state["state"]["is_active"]
            self.state.created_at = datetime.fromisoformat(state["state"]["created_at"])
            self.state.last_updated = datetime.fromisoformat(state["state"]["last_updated"])
            self.statistics = state["statistics"]
            self.state.metadata = state["metadata"]
            
            self.add_event("state_loaded", {"session_id": self.session_id})
            return True
            
        except Exception as e:
            self.add_event("state_load_failed", {"error": str(e)})
            return False
    
    def pause(self) -> None:
        """Pause the game session."""
        self.state.is_paused = True
        self.add_event("session_paused", {"session_id": self.session_id})
    
    def resume(self) -> None:
        """Resume the game session."""
        self.state.is_paused = False
        self.add_event("session_resumed", {"session_id": self.session_id})
    
    def end(self) -> None:
        """End the game session."""
        self.state.is_active = False
        self.state.is_paused = False
        self.add_event("session_ended", {"session_id": self.session_id})
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get session information.
        
        Returns:
            Dict[str, Any]: Session information
        """
        return {
            "session_id": self.session_id,
            "player_id": self.player.id,
            "player_name": self.player.name,
            "state": self.state,
            "statistics": self.statistics,
            "config": self.config,
            "entity_count": len(self.entities),
            "item_count": len(self.items),
            "event_count": len(self.events)
        }
    
    def update_play_time(self, delta_seconds: int) -> None:
        """
        Update play time.

        Args:
            delta_seconds: Seconds to add to play time
        """
        self.statistics["play_time"] += delta_seconds

        # Update total play time string
        hours = self.statistics["play_time"] // 3600
        minutes = (self.statistics["play_time"] % 3600) // 60
        self.state.total_play_time = f"{hours}h {minutes}m"

    def publish_level_change_event(self, old_level: int, new_level: int):
        """Publish a level change event to the event bus."""
        from ..event_system.base_event import Event
        
        event = Event(
            event_type="level_change",
            source="game_session",
            data={
                "old_level": old_level,
                "new_level": new_level,
                "player_entity": self.player  # Assuming player is an Entity
            }
        )
        self.event_bus.publish_event(event)

    def advance_level(self):
        """Advance the player to the next level."""
        old_level = self.state.current_level
        new_level = old_level + 1
        self.state.current_level = new_level
        # Publish level change event
        self.publish_level_change_event(old_level, new_level)