"""Level design service for LLM-driven level generation and item seeding."""

from typing import Dict, List, Optional, Tuple, Any

from src.domain.value_objects.power_levels import PlayerProfile
from src.domain.value_objects.map_access import MapAccessRequest
from src.domain.value_objects.llm_logging import LLMLogger


__all__ = ["LevelDesignService"]


# Social structure scenarios
SOCIAL_STRUCTURE_SCENARIOS = [
    {
        "type": "goblin_kingdom",
        "description": "A hierarchical goblin tribe with a king, guards, and minions. King distributes wealth to maintain loyalty.",
        "min_mobs": 5,
        "max_mobs": 12,
        "loyalty_sensitive": True
    },
    {
        "type": "wolf_pack",
        "description": "A pack of wolves led by an alpha. Strength-based hierarchy with pack hunting tactics.",
        "min_mobs": 4,
        "max_mobs": 8,
        "loyalty_sensitive": False
    },
    {
        "type": "spider_hive",
        "description": "A spider queen with workers and drones. Hive mind shares perception. Instinctual, no loyalty.",
        "min_mobs": 6,
        "max_mobs": 15,
        "loyalty_sensitive": False
    },
    {
        "type": "mercenary_band",
        "description": "A group of mercenaries with a captain. Contract-based. Can be bribed to switch sides.",
        "min_mobs": 3,
        "max_mobs": 8,
        "loyalty_sensitive": True
    },
    {
        "type": "undead_court",
        "description": "A lich commanding knights and skeletons. Fear-based control through domination magic.",
        "min_mobs": 5,
        "max_mobs": 12,
        "loyalty_sensitive": False
    },
    {
        "type": "merchant_guild",
        "description": "A guildmaster with merchants and guards. Trade-based, wealth-driven, non-combat focused.",
        "min_mobs": 3,
        "max_mobs": 6,
        "loyalty_sensitive": True
    }
]


class LevelDesignService:
    """
    Service for LLM-driven level design and item seeding.
    
    This service handles map access requests, generates level layouts,
    places mobs and items appropriate to player strength, and selects
    social structure scenarios.
    """
    
    def __init__(self, llm_logger: LLMLogger, ollama_service: Any = None):
        """
        Initialize the LevelDesignService.
        
        Args:
            llm_logger: Logger for LLM calls
            ollama_service: Optional LLM service for generation
        """
        self._llm_logger = llm_logger
        self._ollama_service = ollama_service
    
    def request_map_access(self, request: MapAccessRequest) -> bool:
        """
        Grant or deny map access based on reason.
        
        Args:
            request: The map access request
            
        Returns:
            bool: True if access granted
        """
        # Grant access for valid reasons
        valid_reasons = ["level_creation", "spell_clairvoyance", "commander_coordination", "debug"]
        
        if request.reason in valid_reasons:
            request.granted = True
            return True
        
        request.granted = False
        return False
    
    def generate_level_layout(
        self,
        player_profile: PlayerProfile,
        level_number: int,
        map_access: List[List[int]]
    ) -> Dict[str, Any]:
        """
        Generate level configuration (rooms, corridors, items, mobs).
        
        Args:
            player_profile: Player profile for balancing
            level_number: The level number
            map_access: 2D array representing map access/visibility
            
        Returns:
            Dict[str, Any]: Level configuration
        """
        # Build prompt for LLM
        prompt = self._build_level_prompt(player_profile, level_number)
        
        # Try to use LLM if available
        if self._ollama_service:
            try:
                response = self._ollama_service.generate(prompt)
                return self._parse_level_response(response)
            except Exception:
                pass
        
        # Fallback: generate basic level
        return self._generate_fallback_level(player_profile, level_number)
    
    def generate_mob_placement(
        self,
        player_profile: PlayerProfile,
        rooms: List[Dict]
    ) -> List[Dict]:
        """
        Place mobs appropriate to player strength.
        
        Args:
            player_profile: Player profile for balancing
            rooms: List of room configurations
            
        Returns:
            List[Dict]: List of mob placements
        """
        placements = []
        player_power = player_profile.offensive_power.melee_strength if player_profile else 10
        
        for room in rooms:
            # Determine mob count based on room size and player power
            room_size = room.get("size", "medium")
            if room_size == "large":
                mob_count = min(8, max(3, int(player_power / 5)))
            elif room_size == "small":
                mob_count = min(3, max(1, int(player_power / 10)))
            else:
                mob_count = min(5, max(2, int(player_power / 7)))
            
            # Select appropriate mob types
            mob_types = self._select_mob_types(player_power, mob_count)
            
            for i, mob_type in enumerate(mob_types):
                placements.append({
                    "type": mob_type,
                    "position": room.get("position", (5, 5)),
                    "room_id": room.get("id", "unknown")
                })
        
        return placements
    
    def generate_item_seeding(
        self,
        player_profile: PlayerProfile,
        rooms: List[Dict]
    ) -> List[Dict]:
        """
        Place items that complement or challenge the player.
        
        Args:
            player_profile: Player profile for balancing
            rooms: List of room configurations
            
        Returns:
            List[Dict]: List of item placements
        """
        placements = []
        
        for room in rooms:
            # Place 1-2 items per room
            item_count = 1 if len(rooms) > 3 else 2
            
            for i in range(item_count):
                item_type = self._select_item_type(player_profile)
                placements.append({
                    "type": item_type,
                    "position": room.get("position", (5, 5)),
                    "room_id": room.get("id", "unknown")
                })
        
        return placements
    
    def select_social_structure(
        self,
        player_profile: PlayerProfile,
        level_number: int
    ) -> str:
        """
        Pick a social structure scenario for the level.
        
        Args:
            player_profile: Player profile
            level_number: Current level number
            
        Returns:
            str: The selected social structure type
        """
        # Cycle through structures based on level number
        index = level_number % len(SOCIAL_STRUCTURE_SCENARIOS)
        return SOCIAL_STRUCTURE_SCENARIOS[index]["type"]
    
    def _build_level_prompt(
        self,
        player_profile: PlayerProfile,
        level_number: int
    ) -> str:
        """
        Build LLM prompt for level generation.
        
        Args:
            player_profile: Player profile
            level_number: Current level number
            
        Returns:
            str: The prompt string
        """
        off = player_profile.offensive_power if player_profile else None
        off_power = off.dominant_type() if off else "melee"
        
        return f"""
Player Profile:
- Dominant power type: {off_power}
- Level: {level_number}

Generate a roguelike dungeon level with:
1. Room layout and connections
2. Monster placements appropriate to player strength
3. Item placements (weapons, armor, consumables)
4. Special features (traps, secrets, exits)

Return JSON with keys: description, rooms, entities, items.
"""
    
    def _build_item_prompt(
        self,
        player_profile: PlayerProfile,
        room_count: int
    ) -> str:
        """
        Build LLM prompt for item seeding.
        
        Args:
            player_profile: Player profile
            room_count: Number of rooms
            
        Returns:
            str: The prompt string
        """
        return f"""
Generate {room_count} items for a roguelike dungeon.
Player profile: {player_profile.summary_for_llm() if player_profile else 'Unknown'}

Return JSON with keys: items (list of item objects with type, name, description).
"""
    
    def _parse_level_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into level config.
        
        Args:
            response: Raw LLM response string
            
        Returns:
            Dict[str, Any]: Parsed level configuration
        """
        import json
        
        try:
            # Try to extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except Exception:
            pass
        
        # Return default structure
        return {
            "description": "A generic dungeon level",
            "rooms": [],
            "entities": [],
            "items": []
        }
    
    def _generate_fallback_level(
        self,
        player_profile: PlayerProfile,
        level_number: int
    ) -> Dict[str, Any]:
        """
        Generate a basic fallback level when LLM is unavailable.
        
        Args:
            player_profile: Player profile
            level_number: Current level number
            
        Returns:
            Dict[str, Any]: Basic level configuration
        """
        return {
            "description": f"Level {level_number}: A basic dungeon",
            "rooms": [
                {"id": "room_1", "position": (0, 0), "size": "medium"},
                {"id": "room_2", "position": (10, 0), "size": "small"}
            ],
            "entities": [],
            "items": []
        }
    
    def _select_mob_types(
        self,
        player_power: float,
        count: int
    ) -> List[str]:
        """
        Select appropriate mob types for player power level.
        
        Args:
            player_power: Player's offensive power
            count: Number of mobs needed
            
        Returns:
            List[str]: List of mob type names
        """
        if player_power < 20:
            return ["goblin"] * count
        elif player_power < 40:
            return ["goblin", "orc"][:count] if count <= 2 else ["goblin", "orc", "goblin"]
        else:
            return ["orc", "dragon"][:count] if count <= 2 else ["orc", "dragon", "orc"]
    
    def _select_item_type(self, player_profile: PlayerProfile) -> str:
        """
        Select an appropriate item type for the player.
        
        Args:
            player_profile: Player profile
            
        Returns:
            str: Item type name
        """
        return "potion"  # Default to healing potion
    
    def get_available_structures(self) -> List[Dict[str, Any]]:
        """
        Get the 6 social structure scenarios with descriptions.
        
        Returns:
            List[Dict[str, Any]]: List of structure scenarios
        """
        return [dict(s) for s in SOCIAL_STRUCTURE_SCENARIOS]