"""
Survival service for handling survival mechanics and environmental effects.
"""
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from ..entities.player import Player
from ..entities.mob import Mob
from ..entities.item import Item
from ..components.inventory import Inventory
from ..value_objects.position import Position
from ..value_objects.stats import Stats
from typing import Any


class SurvivalStatus(Enum):
    """Survival status types."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"
    DEAD = "dead"


class EnvironmentalHazard(Enum):
    """Environmental hazard types."""
    NONE = "none"
    COLD = "cold"
    HEAT = "heat"
    POISON = "poison"
    HUNGER = "hunger"
    THIRST = "thirst"
    FATIGUE = "fatigue"
    DISEASE = "disease"


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


class SurvivalService:
    """
    Service for handling survival mechanics and environmental effects.
    
    Implements the Service pattern for survival management.
    """
    
    def __init__(self):
        """Initialize the survival service."""
        self.survival_events: List[Dict[str, Any]] = []
        self.environmental_effects: Dict[str, Dict[str, Any]] = {}
        self.survival_status: Dict[str, SurvivalStatus] = {}
        self.hazard_levels: Dict[str, EnvironmentalHazard] = {}
        self.survival_timers: Dict[str, Dict[str, float]] = {}
        self.temperature_zones: Dict[Tuple[int, int], float] = {}
        self.food_sources: List[Dict[str, Any]] = []
        self.water_sources: List[Dict[str, Any]] = []
        self.shelter_locations: List[Dict[str, Any]] = []
        
        # Initialize default survival parameters
        self.default_survival_params = {
            "hunger_rate": 0.1,  # Hunger per minute
            "thirst_rate": 0.15,  # Thirst per minute
            "fatigue_rate": 0.05,  # Fatigue per minute
            "temperature_base": 20.0,  # Base temperature (Celsius)
            "cold_damage_rate": 0.2,  # Damage per minute in extreme cold
            "heat_damage_rate": 0.3,  # Damage per minute in extreme heat
            "poison_damage_rate": 0.1,  # Damage per minute when poisoned
            "disease_damage_rate": 0.15  # Damage per minute when diseased
        }
    
    def update_survival(self, player: Player, delta_time: float, environment: Dict[str, Any]) -> None:
        """
        Update survival status for a player.
        
        Args:
            player: The player to update survival for
            delta_time: Time since last update
            environment: Current environment information
        """
        # Update survival timers
        self.update_survival_timers(player, delta_time)
        
        # Apply environmental effects
        self.apply_environmental_effects(player, environment, delta_time)
        
        # Update survival status
        self.update_survival_status(player)
        
        # Record survival event
        event = {
            "event_type": "survival_update",
            "player_id": player.id,
            "player_name": player.name,
            "survival_status": self.survival_status.get(player.id, SurvivalStatus.GOOD).value,
            "timestamp": self.get_current_timestamp()
        }
        self.survival_events.append(event)
    
    def update_survival_timers(self, player: Player, delta_time: float) -> None:
        """
        Update survival timers for a player.
        
        Args:
            player: The player to update timers for
            delta_time: Time since last update
        """
        player_id = player.id
        
        if player_id not in self.survival_timers:
            self.survival_timers[player_id] = {
                "hunger": 0.0,
                "thirst": 0.0,
                "fatigue": 0.0,
                "poison": 0.0,
                "disease": 0.0
            }
        
        # Update timers
        self.survival_timers[player_id]["hunger"] += self.default_survival_params["hunger_rate"] * delta_time
        self.survival_timers[player_id]["thirst"] += self.default_survival_params["thirst_rate"] * delta_time
        self.survival_timers[player_id]["fatigue"] += self.default_survival_params["fatigue_rate"] * delta_time
        
        # Clamp timers
        for timer in self.survival_timers[player_id]:
            self.survival_timers[player_id][timer] = clamp(self.survival_timers[player_id][timer], 0.0, 100.0)
    
    def apply_environmental_effects(self, player: Player, environment: Dict[str, Any], delta_time: float) -> None:
        """
        Apply environmental effects to a player.
        
        Args:
            player: The player to apply effects to
            environment: Current environment information
            delta_time: Time since last update
        """
        # Get current hazard level
        current_hazard = self.get_environmental_hazard(player, environment)
        self.hazard_levels[player.id] = current_hazard
        
        # Apply hazard effects
        if current_hazard == EnvironmentalHazard.COLD:
            self.apply_cold_effect(player, delta_time)
        elif current_hazard == EnvironmentalHazard.HEAT:
            self.apply_heat_effect(player, delta_time)
        elif current_hazard == EnvironmentalHazard.POISON:
            self.apply_poison_effect(player, delta_time)
        elif current_hazard == EnvironmentalHazard.HUNGER:
            self.apply_hunger_effect(player, delta_time)
        elif current_hazard == EnvironmentalHazard.THIRST:
            self.apply_thirst_effect(player, delta_time)
        elif current_hazard == EnvironmentalHazard.FATIGUE:
            self.apply_fatigue_effect(player, delta_time)
        elif current_hazard == EnvironmentalHazard.DISEASE:
            self.apply_disease_effect(player, delta_time)
    
    def get_environmental_hazard(self, player: Player, environment: Dict[str, Any]) -> EnvironmentalHazard:
        """
        Get environmental hazard for a player.
        
        Args:
            player: The player to get hazard for
            environment: Current environment information
            
        Returns:
            EnvironmentalHazard: Current hazard level
        """
        # Check for immediate hazards
        if environment.get("poisoned", False):
            return EnvironmentalHazard.POISON
        
        # Check temperature
        temperature = environment.get("temperature", self.default_survival_params["temperature_base"])
        if temperature < 0:
            return EnvironmentalHazard.COLD
        elif temperature > 40:
            return EnvironmentalHazard.HEAT
        
        # Check survival timers
        if player.id in self.survival_timers:
            timers = self.survival_timers[player.id]
            if timers["hunger"] > 80:
                return EnvironmentalHazard.HUNGER
            elif timers["thirst"] > 80:
                return EnvironmentalHazard.THIRST
            elif timers["fatigue"] > 80:
                return EnvironmentalHazard.FATIGUE
            elif timers["disease"] > 0:
                return EnvironmentalHazard.DISEASE
        
        return EnvironmentalHazard.NONE
    
    def apply_cold_effect(self, player: Player, delta_time: float) -> None:
        """
        Apply cold effect to a player.
        
        Args:
            player: The player to apply effect to
            delta_time: Time since last update
        """
        damage = self.default_survival_params["cold_damage_rate"] * delta_time
        player.health -= damage
        
        # Record survival event
        event = {
            "event_type": "cold_damage",
            "player_id": player.id,
            "damage": damage,
            "timestamp": self.get_current_timestamp()
        }
        self.survival_events.append(event)
    
    def apply_heat_effect(self, player: Player, delta_time: float) -> None:
        """
        Apply heat effect to a player.
        
        Args:
            player: The player to apply effect to
            delta_time: Time since last update
        """
        damage = self.default_survival_params["heat_damage_rate"] * delta_time
        player.health -= damage
        
        # Record survival event
        event = {
            "event_type": "heat_damage",
            "player_id": player.id,
            "damage": damage,
            "timestamp": self.get_current_timestamp()
        }
        self.survival_events.append(event)
    
    def apply_poison_effect(self, player: Player, delta_time: float) -> None:
        """
        Apply poison effect to a player.
        
        Args:
            player: The player to apply effect to
            delta_time: Time since last update
        """
        damage = self.default_survival_params["poison_damage_rate"] * delta_time
        player.health -= damage
        
        # Update poison timer
        if player.id in self.survival_timers:
            self.survival_timers[player.id]["poison"] += delta_time
        
        # Record survival event
        event = {
            "event_type": "poison_damage",
            "player_id": player.id,
            "damage": damage,
            "timestamp": self.get_current_timestamp()
        }
        self.survival_events.append(event)
    
    def apply_hunger_effect(self, player: Player, delta_time: float) -> None:
        """
        Apply hunger effect to a player.
        
        Args:
            player: The player to apply effect to
            delta_time: Time since last update
        """
        # Hunger reduces health and stamina
        health_damage = 0.1 * delta_time
        stamina_damage = 0.2 * delta_time
        
        player.health -= health_damage
        player.stats.stamina = max(0, player.stats.stamina - stamina_damage)
        
        # Record survival event
        event = {
            "event_type": "hunger_effect",
            "player_id": player.id,
            "health_damage": health_damage,
            "stamina_damage": stamina_damage,
            "timestamp": self.get_current_timestamp()
        }
        self.survival_events.append(event)
    
    def apply_thirst_effect(self, player: Player, delta_time: float) -> None:
        """
        Apply thirst effect to a player.
        
        Args:
            player: The player to apply effect to
            delta_time: Time since last update
        """
        # Thirst reduces health and mana
        health_damage = 0.15 * delta_time
        mana_damage = 0.25 * delta_time
        
        player.health -= health_damage
        player.stats.mana = max(0, player.stats.mana - mana_damage)
        
        # Record survival event
        event = {
            "event_type": "thirst_effect",
            "player_id": player.id,
            "health_damage": health_damage,
            "mana_damage": mana_damage,
            "timestamp": self.get_current_timestamp()
        }
        self.survival_events.append(event)
    
    def apply_fatigue_effect(self, player: Player, delta_time: float) -> None:
        """
        Apply fatigue effect to a player.
        
        Args:
            player: The player to apply effect to
            delta_time: Time since last update
        """
        # Fatigue reduces health and speed
        health_damage = 0.05 * delta_time
        speed_reduction = 0.1 * delta_time
        
        player.health -= health_damage
        player.stats.speed = max(1, player.stats.speed - speed_reduction)
        
        # Record survival event
        event = {
            "event_type": "fatigue_effect",
            "player_id": player.id,
            "health_damage": health_damage,
            "speed_reduction": speed_reduction,
            "timestamp": self.get_current_timestamp()
        }
        self.survival_events.append(event)
    
    def apply_disease_effect(self, player: Player, delta_time: float) -> None:
        """
        Apply disease effect to a player.
        
        Args:
            player: The player to apply effect to
            delta_time: Time since last update
        """
        # Disease reduces health and all stats
        damage = self.default_survival_params["disease_damage_rate"] * delta_time
        player.health -= damage
        
        # Reduce all stats
        for stat in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            current_value = getattr(player.stats, stat)
            reduction = 0.05 * delta_time
            setattr(player.stats, stat, max(1, current_value - reduction))
        
        # Update disease timer
        if player.id in self.survival_timers:
            self.survival_timers[player.id]["disease"] += delta_time
        
        # Record survival event
        event = {
            "event_type": "disease_effect",
            "player_id": player.id,
            "damage": damage,
            "timestamp": self.get_current_timestamp()
        }
        self.survival_events.append(event)
    
    def update_survival_status(self, player: Player) -> None:
        """
        Update survival status for a player.
        
        Args:
            player: The player to update status for
        """
        player_id = player.id
        
        # Check if player is dead
        if player.health <= 0:
            self.survival_status[player_id] = SurvivalStatus.DEAD
            return
        
        # Calculate survival score
        survival_score = self.calculate_survival_score(player)
        
        # Determine status based on score
        if survival_score >= 90:
            self.survival_status[player_id] = SurvivalStatus.EXCELLENT
        elif survival_score >= 70:
            self.survival_status[player_id] = SurvivalStatus.GOOD
        elif survival_score >= 50:
            self.survival_status[player_id] = SurvivalStatus.FAIR
        elif survival_score >= 30:
            self.survival_status[player_id] = SurvivalStatus.POOR
        else:
            self.survival_status[player_id] = SurvivalStatus.CRITICAL
    
    def calculate_survival_score(self, player: Player) -> float:
        """
        Calculate survival score for a player.
        
        Args:
            player: The player to calculate score for
            
        Returns:
            float: Survival score (0-100)
        """
        score = 100.0
        
        # Health contribution
        health_percentage = (player.health / player.max_health) * 100
        score += health_percentage * 0.3
        
        # Survival timers contribution
        if player.id in self.survival_timers:
            timers = self.survival_timers[player.id]
            # Hunger and thirst reduce score
            score -= timers["hunger"] * 0.2
            score -= timers["thirst"] * 0.2
            # Fatigue reduces score
            score -= timers["fatigue"] * 0.1
            # Poison and disease heavily reduce score
            score -= timers["poison"] * 0.3
            score -= timers["disease"] * 0.4
        
        # Environmental hazard contribution
        if player.id in self.hazard_levels:
            hazard = self.hazard_levels[player.id]
            if hazard == EnvironmentalHazard.COLD:
                score -= 20
            elif hazard == EnvironmentalHazard.HEAT:
                score -= 25
            elif hazard == EnvironmentalHazard.POISON:
                score -= 30
            elif hazard == EnvironmentalHazard.HUNGER:
                score -= 15
            elif hazard == EnvironmentalHazard.THIRST:
                score -= 20
            elif hazard == EnvironmentalHazard.FATIGUE:
                score -= 10
            elif hazard == EnvironmentalHazard.DISEASE:
                score -= 35
        
        return clamp(score, 0.0, 100.0)
    
    def consume_food(self, player: Player, food_item: Item) -> bool:
        """
        Consume food to reduce hunger.
        
        Args:
            player: The player consuming food
            food_item: The food item to consume
            
        Returns:
            bool: True if food was consumed, False otherwise
        """
        if not food_item.is_consumable or "food" not in food_item.item_type:
            return False
        
        # Reduce hunger
        if player.id in self.survival_timers:
            self.survival_timers[player.id]["hunger"] = max(0, self.survival_timers[player.id]["hunger"] - 30)
        
        # Apply food effects
        if food_item.effect:
            if "heal" in food_item.effect:
                heal_amount = int(food_item.effect.split("+")[1]) if "+" in food_item.effect else 10
                player.health = min(player.max_health, player.health + heal_amount)
        
        # Record survival event
        event = {
            "event_type": "food_consumed",
            "player_id": player.id,
            "item_id": food_item.id,
            "item_name": food_item.name,
            "timestamp": self.get_current_timestamp()
        }
        self.survival_events.append(event)
        
        return True
    
    def drink_water(self, player: Player, water_item: Item) -> bool:
        """
        Drink water to reduce thirst.
        
        Args:
            player: The player drinking water
            water_item: The water item to drink
            
        Returns:
            bool: True if water was drunk, False otherwise
        """
        if not water_item.is_consumable or "water" not in water_item.item_type:
            return False
        
        # Reduce thirst
        if player.id in self.survival_timers:
            self.survival_timers[player.id]["thirst"] = max(0, self.survival_timers[player.id]["thirst"] - 40)
        
        # Apply water effects
        if water_item.effect:
            if "heal" in water_item.effect:
                heal_amount = int(water_item.effect.split("+")[1]) if "+" in water_item.effect else 5
                player.health = min(player.max_health, player.health + heal_amount)
        
        # Record survival event
        event = {
            "event_type": "water_consumed",
            "player_id": player.id,
            "item_id": water_item.id,
            "item_name": water_item.name,
            "timestamp": self.get_current_timestamp()
        }
        self.survival_events.append(event)
        
        return True
    
    def take_shelter(self, player: Player, shelter_position: Position) -> bool:
        """
        Take shelter from environmental hazards.
        
        Args:
            player: The player taking shelter
            shelter_position: Position of shelter
            
        Returns:
            bool: True if shelter was taken, False otherwise
        """
        # Check if position has shelter
        has_shelter = any(
            shelter["position"] == shelter_position 
            for shelter in self.shelter_locations
        )
        
        if has_shelter:
            # Reduce environmental effects
            if player.id in self.survival_timers:
                self.survival_timers[player_id]["fatigue"] = max(0, self.survival_timers[player_id]["fatigue"] - 20)
            
            # Record survival event
            event = {
                "event_type": "shelter_taken",
                "player_id": player.id,
                "shelter_position": shelter_position,
                "timestamp": self.get_current_timestamp()
            }
            self.survival_events.append(event)
            
            return True
        
        return False
    
    def get_survival_status(self, player: Player) -> SurvivalStatus:
        """
        Get survival status for a player.
        
        Args:
            player: The player to get status for
            
        Returns:
            SurvivalStatus: Current survival status
        """
        return self.survival_status.get(player.id, SurvivalStatus.GOOD)
    
    def get_survival_timers(self, player: Player) -> Dict[str, float]:
        """
        Get survival timers for a player.
        
        Args:
            player: The player to get timers for
            
        Returns:
            Dict[str, float]: Survival timers
        """
        return self.survival_timers.get(player.id, {})
    
    def get_survival_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get survival events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List[Dict[str, Any]]: Survival events
        """
        return self.survival_events[-limit:]
    
    def get_current_timestamp(self) -> str:
        """
        Get current timestamp.
        
        Returns:
            str: Current timestamp
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def clear_survival_events(self) -> None:
        """Clear all survival events."""
        self.survival_events.clear()
    
    def add_food_source(self, position: Position, food_type: str, nutrition_value: float) -> None:
        """
        Add a food source to the world.
        
        Args:
            position: Position of food source
            food_type: Type of food
            nutrition_value: Nutrition value
        """
        self.food_sources.append({
            "position": position,
            "food_type": food_type,
            "nutrition_value": nutrition_value,
            "available": True
        })
    
    def add_water_source(self, position: Position, water_type: str, purity: float) -> None:
        """
        Add a water source to the world.
        
        Args:
            position: Position of water source
            water_type: Type of water
            purity: Water purity (0-1)
        """
        self.water_sources.append({
            "position": position,
            "water_type": water_type,
            "purity": purity,
            "available": True
        })
    
    def add_shelter_location(self, position: Position, shelter_type: str, protection_level: float) -> None:
        """
        Add a shelter location to the world.
        
        Args:
            position: Position of shelter
            shelter_type: Type of shelter
            protection_level: Protection level (0-1)
        """
        self.shelter_locations.append({
            "position": position,
            "shelter_type": shelter_type,
            "protection_level": protection_level,
            "available": True
        })
    
    def find_nearest_food_source(self, player: Player) -> Optional[Dict[str, Any]]:
        """
        Find the nearest food source to a player.
        
        Args:
            player: The player to find food for
            
        Returns:
            Optional[Dict[str, Any]]: Nearest food source or None
        """
        if not self.food_sources:
            return None
        
        nearest_source = None
        min_distance = float('inf')
        
        for source in self.food_sources:
            if source["available"]:
                distance = player.position.distance_to(source["position"])
                if distance < min_distance:
                    min_distance = distance
                    nearest_source = source
        
        return nearest_source
    
    def find_nearest_water_source(self, player: Player) -> Optional[Dict[str, Any]]:
        """
        Find the nearest water source to a player.
        
        Args:
            player: The player to find water for
            
        Returns:
            Optional[Dict[str, Any]]: Nearest water source or None
        """
        if not self.water_sources:
            return None
        
        nearest_source = None
        min_distance = float('inf')
        
        for source in self.water_sources:
            if source["available"]:
                distance = player.position.distance_to(source["position"])
                if distance < min_distance:
                    min_distance = distance
                    nearest_source = source
        
        return nearest_source
    
    def find_nearest_shelter(self, player: Player) -> Optional[Dict[str, Any]]:
        """
        Find the nearest shelter to a player.
        
        Args:
            player: The player to find shelter for
            
        Returns:
            Optional[Dict[str, Any]]: Nearest shelter or None
        """
        if not self.shelter_locations:
            return None
        
        nearest_shelter = None
        min_distance = float('inf')
        
        for shelter in self.shelter_locations:
            if shelter["available"]:
                distance = player.position.distance_to(shelter["position"])
                if distance < min_distance:
                    min_distance = distance
                    nearest_shelter = shelter
        
        return nearest_shelter