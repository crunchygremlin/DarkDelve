"""
Game session factory for creating game sessions.
"""
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

from .game_session import GameSession, SessionState
from ...domain.entities.player import Player


class GameSessionFactory:
    """
    Factory for creating game sessions.
    
    Implements the Factory pattern for creating game sessions with proper initialization.
    """
    
    def __init__(self):
        """Initialize the game session factory."""
        self.default_config = {
            "auto_save": True,
            "save_interval": 300,  # 5 minutes
            "max_history": 1000,
            "enable_undo": True,
            "max_undo_steps": 50,
            "difficulty": "normal",
            "starting_area": "starting_area",
            "starting_level": 1,
            "enable_tutorial": True,
            "game_speed": 1.0
        }
    
    def create_session(self, player: Player, config: Optional[Dict[str, Any]] = None) -> GameSession:
        """
        Create a new game session.
        
        Args:
            player: The player entity for the session
            config: Optional configuration overrides
            
        Returns:
            GameSession: The created game session
        """
        # Merge default config with provided config
        final_config = self.default_config.copy()
        if config:
            final_config.update(config)
        
        # Create session with unique ID
        session_id = str(uuid.uuid4())
        session = GameSession(player, session_id)
        
        # Apply configuration
        session.config.update(final_config)
        
        # Initialize session state
        session.state.current_level = final_config["starting_level"]
        session.state.current_area = final_config["starting_area"]
        session.state.metadata = {
            "difficulty": final_config["difficulty"],
            "created_at": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        # Add session creation event
        session.add_event("session_created", {
            "session_id": session_id,
            "player_id": player.id,
            "player_name": player.name,
            "config": final_config
        })
        
        return session
    
    def create_quick_session(self, player: Player) -> GameSession:
        """
        Create a quick game session with minimal configuration.
        
        Args:
            player: The player entity for the session
            
        Returns:
            GameSession: The created quick game session
        """
        quick_config = {
            "auto_save": False,
            "save_interval": 60,  # 1 minute
            "max_history": 100,
            "enable_undo": False,
            "max_undo_steps": 10,
            "difficulty": "easy",
            "starting_area": "tutorial_area",
            "starting_level": 1,
            "enable_tutorial": True,
            "game_speed": 2.0
        }
        
        return self.create_session(player, quick_config)
    
    def create_hardcore_session(self, player: Player) -> GameSession:
        """
        Create a hardcore game session with permadeath.
        
        Args:
            player: The player entity for the session
            
        Returns:
            GameSession: The created hardcore game session
        """
        hardcore_config = {
            "auto_save": False,
            "save_interval": 0,  # No auto-save
            "max_history": 50,
            "enable_undo": False,
            "max_undo_steps": 0,
            "difficulty": "hard",
            "starting_area": "hardcore_area",
            "starting_level": 1,
            "enable_tutorial": False,
            "game_speed": 1.0,
            "permadeath": True,
            "limited_saves": 3
        }
        
        return self.create_session(player, hardcore_config)
    
    def create_story_session(self, player: Player, story_mode: str = "normal") -> GameSession:
        """
        Create a story-focused game session.
        
        Args:
            player: The player entity for the session
            story_mode: Story mode ("normal", "exploration", "narrative")
            
        Returns:
            GameSession: The created story game session
        """
        story_config = {
            "auto_save": True,
            "save_interval": 180,  # 3 minutes
            "max_history": 2000,
            "enable_undo": True,
            "max_undo_steps": 100,
            "difficulty": "normal",
            "starting_area": "story_area",
            "starting_level": 1,
            "enable_tutorial": True,
            "game_speed": 1.0,
            "story_mode": story_mode,
            "enable_cutscenes": True,
            "dialogue_focus": True
        }
        
        return self.create_session(player, story_config)
    
    def create_multiplayer_session(self, player: Player, game_mode: str = "cooperative") -> GameSession:
        """
        Create a multiplayer game session.
        
        Args:
            player: The player entity for the session
            game_mode: Game mode ("cooperative", "competitive", "team")
            
        Returns:
            GameSession: The created multiplayer game session
        """
        multiplayer_config = {
            "auto_save": True,
            "save_interval": 600,  # 10 minutes
            "max_history": 5000,
            "enable_undo": False,
            "max_undo_steps": 0,
            "difficulty": "normal",
            "starting_area": "multiplayer_area",
            "starting_level": 1,
            "enable_tutorial": False,
            "game_speed": 1.0,
            "multiplayer_mode": game_mode,
            "max_players": 4,
            "pvp_enabled": game_mode == "competitive"
        }
        
        return self.create_session(player, multiplayer_config)
    
    def create_custom_session(self, player: Player, custom_config: Dict[str, Any]) -> GameSession:
        """
        Create a custom game session with user-defined configuration.
        
        Args:
            player: The player entity for the session
            custom_config: Custom configuration dictionary
            
        Returns:
            GameSession: The created custom game session
        """
        # Validate custom config
        validated_config = self.validate_config(custom_config)
        
        return self.create_session(player, validated_config)
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize a configuration dictionary.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Dict[str, Any]: Validated and normalized configuration
        """
        validated = self.default_config.copy()
        
        # Validate and apply custom settings
        for key, value in config.items():
            if key in validated:
                # Type validation
                if key in ["auto_save", "enable_undo", "enable_tutorial", "enable_cutscenes"]:
                    validated[key] = bool(value)
                elif key in ["save_interval", "max_history", "max_undo_steps", "starting_level", "max_players"]:
                    validated[key] = int(value)
                elif key in ["game_speed"]:
                    validated[key] = float(value)
                elif key in ["difficulty", "starting_area", "story_mode", "multiplayer_mode"]:
                    validated[key] = str(value)
                else:
                    validated[key] = value
        
        return validated
    
    def get_session_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available session templates.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of session templates
        """
        return {
            "default": {
                "name": "Default Session",
                "description": "Standard game session with balanced settings",
                "config": self.default_config
            },
            "quick": {
                "name": "Quick Session",
                "description": "Fast-paced session with minimal features",
                "config": {
                    "auto_save": False,
                    "save_interval": 60,
                    "max_history": 100,
                    "enable_undo": False,
                    "max_undo_steps": 10,
                    "difficulty": "easy",
                    "starting_area": "tutorial_area",
                    "starting_level": 1,
                    "enable_tutorial": True,
                    "game_speed": 2.0
                }
            },
            "hardcore": {
                "name": "Hardcore Session",
                "description": "Permadeath mode with no saves",
                "config": {
                    "auto_save": False,
                    "save_interval": 0,
                    "max_history": 50,
                    "enable_undo": False,
                    "max_undo_steps": 0,
                    "difficulty": "hard",
                    "starting_area": "hardcore_area",
                    "starting_level": 1,
                    "enable_tutorial": False,
                    "game_speed": 1.0,
                    "permadeath": True,
                    "limited_saves": 3
                }
            },
            "story": {
                "name": "Story Session",
                "description": "Story-focused gameplay with enhanced narrative",
                "config": {
                    "auto_save": True,
                    "save_interval": 180,
                    "max_history": 2000,
                    "enable_undo": True,
                    "max_undo_steps": 100,
                    "difficulty": "normal",
                    "starting_area": "story_area",
                    "starting_level": 1,
                    "enable_tutorial": True,
                    "game_speed": 1.0,
                    "story_mode": "normal",
                    "enable_cutscenes": True,
                    "dialogue_focus": True
                }
            },
            "multiplayer": {
                "name": "Multiplayer Session",
                "description": "Multiplayer session with cooperative or competitive gameplay",
                "config": {
                    "auto_save": True,
                    "save_interval": 600,
                    "max_history": 5000,
                    "enable_undo": False,
                    "max_undo_steps": 0,
                    "difficulty": "normal",
                    "starting_area": "multiplayer_area",
                    "starting_level": 1,
                    "enable_tutorial": False,
                    "game_speed": 1.0,
                    "multiplayer_mode": "cooperative",
                    "max_players": 4,
                    "pvp_enabled": False
                }
            }
        }
    
    def get_session_info(self, session: GameSession) -> Dict[str, Any]:
        """
        Get information about a session.
        
        Args:
            session: The session to get information about
            
        Returns:
            Dict[str, Any]: Session information
        """
        return {
            "session_id": session.session_id,
            "player_id": session.player.id,
            "player_name": session.player.name,
            "state": session.state,
            "statistics": session.statistics,
            "config": session.config,
            "entity_count": len(session.entities),
            "item_count": len(session.items),
            "event_count": len(session.events),
            "command_count": len(session.command_history),
            "query_count": len(session.query_history)
        }