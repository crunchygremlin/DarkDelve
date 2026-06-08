"""
Inventory query for inventory-related information.
"""
from typing import Optional, Dict, Any, List
from .base_query import BaseQuery, QueryResult
from ...domain.entities.player import Player
from ...domain.entities.item import Item


class InventoryQuery(BaseQuery):
    """
    Query for inventory-related information.
    
    Implements the Query pattern for inventory management and information.
    """
    
    def __init__(self, player: Player):
        """
        Initialize the inventory query.
        
        Args:
            player: The player entity for inventory queries
        """
        super().__init__("inventory")
        self.player = player
    
    def execute(self, *args, **kwargs) -> QueryResult:
        """
        Execute the inventory query.
        
        Args:
            *args: Additional arguments (item filter)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            QueryResult: The result of the inventory query
        """
        # Check cache first
        cached_result = self.get_cached_result(*args, **kwargs)
        if cached_result:
            return cached_result
        
        item_filter = args[0] if args else None
        
        try:
            if item_filter:
                # Filtered inventory information
                result = self.get_filtered_inventory(item_filter)
            else:
                # Complete inventory information
                result = self.get_complete_inventory()
            
            self.cache_result(result)
            return result
            
        except Exception as e:
            return QueryResult(
                success=False,
                error_message=f"Failed to execute inventory query: {str(e)}"
            )
    
    def get_complete_inventory(self) -> QueryResult:
        """
        Get complete inventory information.
        
        Returns:
            QueryResult: Complete inventory information
        """
        inventory_items = self.player.get_inventory_items()
        
        # Calculate inventory statistics
        total_items = len(inventory_items)
        total_weight = sum(item.weight for item in inventory_items)
        equipment_count = sum(1 for item in inventory_items if item.is_equipment)
        consumable_count = sum(1 for item in inventory_items if item.is_consumable)
        
        # Group items by type
        items_by_type = {}
        for item in inventory_items:
            item_type = item.item_type
            if item_type not in items_by_type:
                items_by_type[item_type] = []
            items_by_type[item_type].append({
                "id": item.id,
                "name": item.name,
                "count": self.player.get_item_count(item),
                "weight": item.weight
            })
        
        return QueryResult(
            success=True,
            data={
                "total_items": total_items,
                "total_weight": total_weight,
                "equipment_count": equipment_count,
                "consumable_count": consumable_count,
                "items_by_type": items_by_type,
                "equipped_items": self.get_equipped_items_info()
            },
            metadata={
                "inventory_capacity": self.player.inventory_capacity,
                "is_full": total_items >= self.player.inventory_capacity,
                "weight_capacity": self.player.weight_capacity,
                "over_weight": total_weight > self.player.weight_capacity
            }
        )
    
    def get_filtered_inventory(self, item_filter: str) -> QueryResult:
        """
        Get filtered inventory information.
        
        Args:
            item_filter: Filter string (e.g., "weapon", "armor", "potion")
            
        Returns:
            QueryResult: Filtered inventory information
        """
        inventory_items = self.player.get_inventory_items()
        
        # Apply filter
        filtered_items = []
        for item in inventory_items:
            if item_filter.lower() in item.item_type.lower() or item_filter.lower() in item.name.lower():
                filtered_items.append({
                    "id": item.id,
                    "name": item.name,
                    "type": item.item_type,
                    "count": self.player.get_item_count(item),
                    "weight": item.weight,
                    "equipped": item.is_equipped
                })
        
        return QueryResult(
            success=True,
            data={
                "filter": item_filter,
                "filtered_items": filtered_items,
                "total_filtered": len(filtered_items)
            },
            metadata={
                "total_items": len(inventory_items),
                "filter_percentage": (len(filtered_items) / len(inventory_items)) * 100 if inventory_items else 0
            }
        )
    
    def get_equipped_items_info(self) -> List[Dict]:
        """
        Get equipped items information.
        
        Returns:
            List[Dict]: List of equipped items
        """
        equipped_items = []
        
        # Get all equipment slots
        equipment_slots = ["weapon", "armor", "helmet", "boots", "gloves", "amulet", "ring"]
        
        for slot in equipment_slots:
            equipped_item = self.player.get_equipped_item(slot)
            if equipped_item:
                equipped_items.append({
                    "slot": slot,
                    "item_id": equipped_item.id,
                    "item_name": equipped_item.name,
                    "item_type": equipped_item.item_type,
                    "attack_bonus": equipped_item.attack_bonus,
                    "defense_bonus": equipped_item.defense_bonus,
                    "health_bonus": equipped_item.health_bonus,
                    "speed_bonus": equipped_item.speed_bonus
                })
        
        return equipped_items
    
    def get_item_info(self, item_id: str) -> QueryResult:
        """
        Get specific item information.
        
        Args:
            item_id: ID of the item to query
            
        Returns:
            QueryResult: Item information
        """
        item = self.player.get_item_by_id(item_id)
        if not item:
            return QueryResult(
                success=False,
                error_message=f"Item with ID {item_id} not found"
            )
        
        return QueryResult(
            success=True,
            data={
                "item_id": item.id,
                "item_name": item.name,
                "item_type": item.item_type,
                "description": item.description,
                "weight": item.weight,
                "value": item.value,
                "count": self.player.get_item_count(item),
                "equipped": item.is_equipped,
                "is_equipment": item.is_equipment,
                "is_consumable": item.is_consumable,
                "is_droppable": item.is_droppable,
                "is_pickupable": item.is_pickupable,
                "is_usable": item.is_usable
            },
            metadata={
                "attack_bonus": item.attack_bonus,
                "defense_bonus": item.defense_bonus,
                "health_bonus": item.health_bonus,
                "speed_bonus": item.speed_bonus,
                "effect": item.effect
            }
        )
    
    def get_inventory_value(self) -> int:
        """
        Calculate total inventory value.
        
        Returns:
            int: Total value of all items in inventory
        """
        inventory_items = self.player.get_inventory_items()
        total_value = sum(item.value * self.player.get_item_count(item) for item in inventory_items)
        return total_value
    
    def get_healing_items(self) -> List[Dict]:
        """
        Get all healing items in inventory.
        
        Returns:
            List[Dict]: List of healing items
        """
        inventory_items = self.player.get_inventory_items()
        healing_items = []
        
        for item in inventory_items:
            if item.is_consumable and item.effect and "heal" in item.effect.lower():
                healing_items.append({
                    "item_id": item.id,
                    "item_name": item.name,
                    "healing_amount": int(item.effect.split("+")[1]) if "+" in item.effect else 0,
                    "count": self.player.get_item_count(item)
                })
        
        return healing_items