"""
Game state query for game state information.
"""
from typing import Optional, Dict, Any, List
from .base_query import BaseQuery, QueryResult
from ...domain.entities.player import Player
from ...domain.value_objects.position import Position


class GameStateQuery(BaseQuery):
    """
    Query for game state information.
    
    Implements the Query pattern for game state management and information.
    """
    
    def __init__(self, player: Player):
        """
        Initialize the game state query.
        
        Args:
            player: The player entity for game state queries
        """
        super().__init__("game_state")
        self.player = player
    
    def execute(self, *args, **kwargs) -> QueryResult:
        """
        Execute the game state query.
        
        Args:
            *args: Additional arguments (state aspect)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            QueryResult: The result of the game state query
        """
        # Check cache first
        cached_result = self.get_cached_result(*args, **kwargs)
        if cached_result:
            return cached_result
        
        state_aspect = args[0] if args else "complete"
        
        try:
            if state_aspect == "player":
                result = self.get_player_state()
            elif state_aspect == "environment":
                result = self.get_environment_state()
            elif state_aspect == "progress":
                result = self.get_progress_state()
            else:
                # Complete game state
                result = self.get_complete_game_state()
            
            self.cache_result(result)
            return result
            
        except Exception as e:
            return QueryResult(
                success=False,
                error_message=f"Failed to execute game state query: {str(e)}"
            )
    
    def get_complete_game_state(self) -> QueryResult:
        """
        Get complete game state information.
        
        Returns:
            QueryResult: Complete game state information
        """
        return QueryResult(
            success=True,
            data={
                "player_state": self.get_player_state_data(),
                "environment_state": self.get_environment_state_data(),
                "progress_state": self.get_progress_state_data()
            },
            metadata={
                "game_time": self.get_game_time(),
                "total_play_time": self.get_total_play_time(),
                "current_level": self.get_current_level(),
                "game_difficulty": self.get_game_difficulty()
            }
        )
    
    def get_player_state(self) -> QueryResult:
        """
        Get player state information.
        
        Returns:
            QueryResult: Player state information
        """
        return QueryResult(
            success=True,
            data=self.get_player_state_data(),
            metadata={
                "is_alive": self.player.is_alive(),
                "is_full_health": self.player.health >= self.player.max_health,
                "is_low_health": self.player.health <= self.player.max_health * 0.25,
                "has_equipment": self.player.has_equipment(),
                "has_consumables": self.player.has_consumables()
            }
        )
    
    def get_environment_state(self) -> QueryResult:
        """
        Get environment state information.
        
        Returns:
            QueryResult: Environment state information
        """
        return QueryResult(
            success=True,
            data=self.get_environment_state_data(),
            metadata={
                "current_area": self.get_current_area(),
                "area_difficulty": self.get_area_difficulty(),
                "nearby_dangers": self.get_nearby_dangers(),
                "available_resources": self.get_available_resources()
            }
        )
    
    def get_progress_state(self) -> QueryResult:
        """
        Get progress state information.
        
        Returns:
            QueryResult: Progress state information
        """
        return QueryResult(
            success=True,
            data=self.get_progress_state_data(),
            metadata={
                "completion_percentage": self.get_completion_percentage(),
                "remaining_content": self.get_remaining_content(),
                "next_milestone": self.get_next_milestone(),
                "progress_rate": self.get_progress_rate()
            }
        )
    
    def get_player_state_data(self) -> Dict[str, Any]:
        """
        Get player state data.
        
        Returns:
            Dict[str, Any]: Player state data
        """
        return {
            "player_id": self.player.id,
            "player_name": self.player.name,
            "level": self.player.level,
            "experience": self.player.experience,
            "health": self.player.health,
            "max_health": self.player.max_health,
            "attack_power": self.player.attack_power,
            "defense": self.player.defense,
            "speed": self.player.speed,
            "position": Position(self.player.x, self.player.y),
            "inventory_count": len(self.player.get_inventory_items()),
            "equipped_items": len([item for item in self.player.get_inventory_items() if item.is_equipped]),
            "effects": self.player.get_active_effects(),
            "status": "alive" if self.player.is_alive() else "dead"
        }
    
    def get_environment_state_data(self) -> Dict[str, Any]:
        """
        Get environment state data.
        
        Returns:
            Dict[str, Any]: Environment state data
        """
        return {
            "current_floor": self.get_current_floor(),
            "current_area": self.get_current_area(),
            "area_size": self.get_area_size(),
            "visibility_range": self.get_visibility_range(),
            "light_level": self.get_light_level(),
            "weather": self.get_weather(),
            "time_of_day": self.get_time_of_day()
        }
    
    def get_progress_state_data(self) -> Dict[str, Any]:
        """
        Get progress state data.
        
        Returns:
            Dict[str, Any]: Progress state data
        """
        return {
            "quests_completed": self.get_quests_completed(),
            "quests_active": self.get_quests_active(),
            "areas_explored": self.get_areas_explored(),
            "total_areas": self.get_total_areas(),
            "enemies_defeated": self.get_enemies_defeated(),
            "total_enemies": self.get_total_enemies(),
            "items_collected": self.get_items_collected(),
            "total_items": self.get_total_items(),
            "achievements_unlocked": self.get_achievements_unlocked(),
            "total_achievements": self.get_total_achievements()
        }
    
    def get_game_time(self) -> str:
        """
        Get current game time.
        
        Returns:
            str: Current game time
        """
        # This would typically get the actual game time
        return "12:00"
    
    def get_total_play_time(self) -> str:
        """
        Get total play time.
        
        Returns:
            str: Total play time
        """
        # This would typically get the total play time
        return "2h 30m"
    
    def get_current_level(self) -> int:
        """
        Get current level.
        
        Returns:
            int: Current level
        """
        return self.player.level
    
    def get_game_difficulty(self) -> str:
        """
        Get game difficulty.
        
        Returns:
            str: Game difficulty
        """
        # This would typically get the game difficulty
        return "normal"
    
    def get_current_floor(self) -> int:
        """
        Get current floor.
        
        Returns:
            int: Current floor
        """
        # This would typically get the current floor
        return 1
    
    def get_current_area(self) -> str:
        """
        Get current area.
        
        Returns:
            str: Current area
        """
        # This would typically get the current area
        return "starting_area"
    
    def get_area_size(self) -> Dict[str, int]:
        """
        Get area size.
        
        Returns:
            Dict[str, int]: Area size
        """
        # This would typically get the area size
        return {"width": 50, "height": 50}
    
    def get_visibility_range(self) -> int:
        """
        Get visibility range.
        
        Returns:
            int: Visibility range
        """
        # This would typically get the visibility range
        return 10
    
    def get_light_level(self) -> float:
        """
        Get light level.
        
        Returns:
            float: Light level (0.0 to 1.0)
        """
        # This would typically get the light level
        return 0.8
    
    def get_weather(self) -> str:
        """
        Get weather.
        
        Returns:
            str: Weather condition
        """
        # This would typically get the weather
        return "clear"
    
    def get_time_of_day(self) -> str:
        """
        Get time of day.
        
        Returns:
            str: Time of day
        """
        # This would typically get the time of day
        return "day"
    
    def get_quests_completed(self) -> int:
        """
        Get number of completed quests.
        
        Returns:
            int: Number of completed quests
        """
        # This would typically get the number of completed quests
        return 0
    
    def get_quests_active(self) -> int:
        """
        Get number of active quests.
        
        Returns:
            int: Number of active quests
        """
        # This would typically get the number of active quests
        return 1
    
    def get_areas_explored(self) -> int:
        """
        Get number of areas explored.
        
        Returns:
            int: Number of areas explored
        """
        # This would typically get the number of areas explored
        return 1
    
    def get_total_areas(self) -> int:
        """
        Get total number of areas.
        
        Returns:
            int: Total number of areas
        """
        # This would typically get the total number of areas
        return 10
    
    def get_enemies_defeated(self) -> int:
        """
        Get number of enemies defeated.
        
        Returns:
            int: Number of enemies defeated
        """
        # This would typically get the number of enemies defeated
        return 0
    
    def get_total_enemies(self) -> int:
        """
        Get total number of enemies.
        
        Returns:
            int: Total number of enemies
        """
        # This would typically get the total number of enemies
        return 100
    
    def get_items_collected(self) -> int:
        """
        Get number of items collected.
        
        Returns:
            int: Number of items collected
        """
        # This would typically get the number of items collected
        return 5
    
    def get_total_items(self) -> int:
        """
        Get total number of items.
        
        Returns:
            int: Total number of items
        """
        # This would typically get the total number of items
        return 50
    
    def get_achievements_unlocked(self) -> int:
        """
        Get number of achievements unlocked.
        
        Returns:
            int: Number of achievements unlocked
        """
        # This would typically get the number of achievements unlocked
        return 0
    
    def get_total_achievements(self) -> int:
        """
        Get total number of achievements.
        
        Returns:
            int: Total number of achievements
        """
        # This would typically get the total number of achievements
        return 20
    
    def get_current_area(self) -> str:
        """
        Get current area.
        
        Returns:
            str: Current area
        """
        return "starting_area"
    
    def get_area_difficulty(self) -> str:
        """
        Get area difficulty.
        
        Returns:
            str: Area difficulty
        """
        return "easy"
    
    def get_nearby_dangers(self) -> List[str]:
        """
        Get nearby dangers.
        
        Returns:
            List[str]: List of nearby dangers
        """
        return []
    
    def get_available_resources(self) -> List[str]:
        """
        Get available resources.
        
        Returns:
            List[str]: List of available resources
        """
        return ["health_potion", "mana_potion"]
    
    def get_completion_percentage(self) -> float:
        """
        Get completion percentage.
        
        Returns:
            float: Completion percentage (0.0 to 100.0)
        """
        return 5.0
    
    def get_remaining_content(self) -> Dict[str, int]:
        """
        Get remaining content.
        
        Returns:
            Dict[str, int]: Remaining content by type
        """
        return {
            "areas": 9,
            "enemies": 100,
            "items": 45,
            "quests": 0
        }
    
    def get_next_milestone(self) -> str:
        """
        Get next milestone.
        
        Returns:
            str: Next milestone
        """
        return "complete_first_quest"
    
    def get_progress_rate(self) -> str:
        """
        Get progress rate.
        
        Returns:
            str: Progress rate
        """
        return "normal"