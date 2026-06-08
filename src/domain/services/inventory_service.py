"""
Inventory service for handling inventory operations and management.
"""
from typing import List, Dict, Any, Optional, Tuple
from ..entities.player import Player
from ..entities.item import Item
from ..components.inventory import Inventory
from ..components.equipment import Equipment
from typing import Any


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


def distance_between(pos1: Any, pos2: Any) -> float:
    """Calculate distance between two positions."""
    return ((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2) ** 0.5


class InventoryService:
    """
    Service for handling inventory operations and management.
    
    Implements the Service pattern for inventory management.
    """
    
    def __init__(self):
        """Initialize the inventory service."""
        self.inventory_events: List[Dict[str, Any]] = []
        self.item_templates: Dict[str, Dict[str, Any]] = {}
        self.setup_item_templates()
    
    def setup_item_templates(self) -> None:
        """Setup basic item templates."""
        self.item_templates = {
            "sword": {
                "name": "Sword",
                "item_type": "weapon",
                "description": "A sharp blade",
                "value": 100,
                "weight": 2.0,
                "attack_bonus": 5,
                "defense_bonus": 0,
                "health_bonus": 0,
                "speed_bonus": 0,
                "equippable": True,
                "stackable": False,
                "is_weapon": True,
                "is_armor": False,
                "is_consumable": False
            },
            "shield": {
                "name": "Shield",
                "item_type": "armor",
                "description": "A sturdy wooden shield",
                "value": 50,
                "weight": 3.0,
                "attack_bonus": 0,
                "defense_bonus": 3,
                "health_bonus": 0,
                "speed_bonus": 0,
                "equippable": True,
                "stackable": False,
                "is_weapon": False,
                "is_armor": True,
                "is_consumable": False
            },
            "health_potion": {
                "name": "Health Potion",
                "item_type": "consumable",
                "description": "A red potion that restores health",
                "value": 25,
                "weight": 0.5,
                "attack_bonus": 0,
                "defense_bonus": 0,
                "health_bonus": 0,
                "speed_bonus": 0,
                "equippable": False,
                "stackable": True,
                "is_weapon": False,
                "is_armor": False,
                "is_consumable": True,
                "effect": "heal+25"
            },
            "gold_coin": {
                "name": "Gold Coin",
                "item_type": "currency",
                "description": "A shiny gold coin",
                "value": 1,
                "weight": 0.1,
                "attack_bonus": 0,
                "defense_bonus": 0,
                "health_bonus": 0,
                "speed_bonus": 0,
                "equippable": False,
                "stackable": True,
                "is_weapon": False,
                "is_armor": False,
                "is_consumable": False
            }
        }
    
    def add_item_to_inventory(self, player: Player, item: Item, quantity: int = 1) -> bool:
        """
        Add an item to the player's inventory.
        
        Args:
            player: The player to add item to
            item: The item to add
            quantity: Quantity of the item to add
            
        Returns:
            bool: True if item was added, False otherwise
        """
        if not self.can_add_item(player, item, quantity):
            return False
        
        # Add item to inventory
        player.inventory.add_item(item, quantity)
        
        # Record inventory event
        event = {
            "event_type": "item_added",
            "player_id": player.id,
            "item_id": item.id,
            "item_name": item.name,
            "quantity": quantity,
            "timestamp": self.get_current_timestamp()
        }
        self.inventory_events.append(event)
        
        return True
    
    def remove_item_from_inventory(self, player: Player, item: Item, quantity: int = 1) -> bool:
        """
        Remove an item from the player's inventory.
        
        Args:
            player: The player to remove item from
            item: The item to remove
            quantity: Quantity of the item to remove
            
        Returns:
            bool: True if item was removed, False otherwise
        """
        if not self.can_remove_item(player, item, quantity):
            return False
        
        # Remove item from inventory
        player.inventory.remove_item(item, quantity)
        
        # Record inventory event
        event = {
            "event_type": "item_removed",
            "player_id": player.id,
            "item_id": item.id,
            "item_name": item.name,
            "quantity": quantity,
            "timestamp": self.get_current_timestamp()
        }
        self.inventory_events.append(event)
        
        return True
    
    def can_add_item(self, player: Player, item: Item, quantity: int = 1) -> bool:
        """
        Check if an item can be added to the player's inventory.
        
        Args:
            player: The player to check
            item: The item to add
            quantity: Quantity of the item to add
            
        Returns:
            bool: True if item can be added, False otherwise
        """
        # Check if inventory has space
        if not player.inventory.has_space_for(item, quantity):
            return False
        
        return True
    
    def can_remove_item(self, player: Player, item: Item, quantity: int = 1) -> bool:
        """
        Check if an item can be removed from the player's inventory.
        
        Args:
            player: The player to check
            item: The item to remove
            quantity: Quantity of the item to remove
            
        Returns:
            bool: True if item can be removed, False otherwise
        """
        # Check if player has the item
        if not player.inventory.has_item(item, quantity):
            return False
        
        return True
    
    def equip_item(self, player: Player, item: Item) -> bool:
        """
        Equip an item on the player.
        
        Args:
            player: The player to equip item on
            item: The item to equip
            
        Returns:
            bool: True if item was equipped, False otherwise
        """
        if not item.equippable:
            return False
        
        if not player.inventory.has_item(item, 1):
            return False
        
        # Equip the item
        player.equipment.equip_item(item)
        
        # Record inventory event
        event = {
            "event_type": "item_equipped",
            "player_id": player.id,
            "item_id": item.id,
            "item_name": item.name,
            "timestamp": self.get_current_timestamp()
        }
        self.inventory_events.append(event)
        
        return True
    
    def unequip_item(self, player: Player, item: Item) -> bool:
        """
        Unequip an item from the player.
        
        Args:
            player: The player to unequip item from
            item: The item to unequip
            
        Returns:
            bool: True if item was unequipped, False otherwise
        """
        if not item.equippable:
            return False
        
        if not player.equipment.is_equipped(item):
            return False
        
        # Unequip the item
        player.equipment.unequip_item(item)
        
        # Record inventory event
        event = {
            "event_type": "item_unequipped",
            "player_id": player.id,
            "item_id": item.id,
            "item_name": item.name,
            "timestamp": self.get_current_timestamp()
        }
        self.inventory_events.append(event)
        
        return True
    
    def use_item(self, player: Player, item: Item, target: Optional[Any] = None) -> bool:
        """
        Use an item.
        
        Args:
            player: The player using the item
            item: The item to use
            target: Optional target for the item
            
        Returns:
            bool: True if item was used, False otherwise
        """
        if not item.is_usable:
            return False
        
        if not player.inventory.has_item(item, 1):
            return False
        
        # Use the item
        success = item.use(player, target)
        
        if success:
            # Remove item from inventory if consumable
            if item.is_consumable:
                player.inventory.remove_item(item, 1)
            
            # Record inventory event
            event = {
                "event_type": "item_used",
                "player_id": player.id,
                "item_id": item.id,
                "item_name": item.name,
                "target_id": target.id if target else None,
                "timestamp": self.get_current_timestamp()
            }
            self.inventory_events.append(event)
        
        return success
    
    def get_inventory_value(self, player: Player) -> int:
        """
        Calculate the total value of all items in inventory.
        
        Args:
            player: The player to calculate inventory value for
            
        Returns:
            int: Total value of inventory items
        """
        total_value = 0
        for item, quantity in player.inventory.get_all_items():
            total_value += item.value * quantity
        return total_value
    
    def get_inventory_weight(self, player: Player) -> float:
        """
        Calculate the total weight of all items in inventory.
        
        Args:
            player: The player to calculate inventory weight for
            
        Returns:
            float: Total weight of inventory items
        """
        total_weight = 0
        for item, quantity in player.inventory.get_all_items():
            total_weight += item.weight * quantity
        return total_weight
    
    def get_equipped_items(self, player: Player) -> List[Item]:
        """
        Get all equipped items.
        
        Args:
            player: The player to get equipped items for
            
        Returns:
            List[Item]: List of equipped items
        """
        return player.equipment.get_equipped_items()
    
    def get_equipped_item_by_slot(self, player: Player, slot: str) -> Optional[Item]:
        """
        Get equipped item by slot.
        
        Args:
            player: The player to get equipped item for
            slot: Equipment slot name
            
        Returns:
            Optional[Item]: Equipped item or None
        """
        return player.equipment.get_item_by_slot(slot)
    
    def get_inventory_stats(self, player: Player) -> Dict[str, Any]:
        """
        Get inventory statistics.
        
        Args:
            player: The player to get inventory stats for
            
        Returns:
            Dict[str, Any]: Inventory statistics
        """
        items = player.inventory.get_all_items()
        total_items = sum(quantity for _, quantity in items)
        total_weight = sum(item.weight * quantity for item, quantity in items)
        total_value = sum(item.value * quantity for item, quantity in items)
        
        # Count by type
        items_by_type = {}
        for item, quantity in items:
            if item.item_type not in items_by_type:
                items_by_type[item.item_type] = 0
            items_by_type[item.item_type] += quantity
        
        # Count equipped items
        equipped_items = len(self.get_equipped_items(player))
        
        return {
            "total_items": total_items,
            "total_weight": total_weight,
            "total_value": total_value,
            "equipped_items": equipped_items,
            "items_by_type": items_by_type,
            "capacity_used": player.inventory.get_used_capacity(),
            "capacity_total": player.inventory.get_total_capacity(),
            "weight_capacity_used": total_weight,
            "weight_capacity_total": player.inventory.get_weight_capacity()
        }
    
    def find_items_by_type(self, player: Player, item_type: str) -> List[Item]:
        """
        Find items by type.
        
        Args:
            player: The player to search in
            item_type: Type of items to find
            
        Returns:
            List[Item]: List of matching items
        """
        matching_items = []
        for item, quantity in player.inventory.get_all_items():
            if item.item_type == item_type:
                matching_items.extend([item] * quantity)
        return matching_items
    
    def find_items_by_name(self, player: Player, name: str) -> List[Item]:
        """
        Find items by name.
        
        Args:
            player: The player to search in
            name: Name of items to find
            
        Returns:
            List[Item]: List of matching items
        """
        matching_items = []
        for item, quantity in player.inventory.get_all_items():
            if name.lower() in item.name.lower():
                matching_items.extend([item] * quantity)
        return matching_items
    
    def sort_inventory(self, player: Player, sort_by: str = "name", reverse: bool = False) -> List[Tuple[Item, int]]:
        """
        Sort inventory by specified criteria.
        
        Args:
            player: The player to sort inventory for
            sort_by: Sort criteria ("name", "type", "value", "weight")
            reverse: Whether to sort in reverse order
            
        Returns:
            List[Tuple[Item, int]]: Sorted list of items and quantities
        """
        items = player.inventory.get_all_items()
        
        if sort_by == "name":
            return sorted(items, key=lambda x: x[0].name.lower(), reverse=reverse)
        elif sort_by == "type":
            return sorted(items, key=lambda x: x[0].item_type.lower(), reverse=reverse)
        elif sort_by == "value":
            return sorted(items, key=lambda x: x[0].value, reverse=reverse)
        elif sort_by == "weight":
            return sorted(items, key=lambda x: x[0].weight, reverse=reverse)
        else:
            return items
    
    def create_item_from_template(self, template_name: str, custom_properties: Optional[Dict[str, Any]] = None) -> Optional[Item]:
        """
        Create an item from a template.
        
        Args:
            template_name: Name of the template
            custom_properties: Custom properties to override
            
        Returns:
            Optional[Item]: Created item or None
        """
        if template_name not in self.item_templates:
            return None
        
        template = self.item_templates[template_name].copy()
        
        # Apply custom properties
        if custom_properties:
            template.update(custom_properties)
        
        # Create item
        item = Item(
            name=template["name"],
            item_type=template["item_type"],
            description=template["description"],
            value=template["value"],
            weight=template["weight"]
        )
        
        # Set additional properties
        item.attack_bonus = template.get("attack_bonus", 0)
        item.defense_bonus = template.get("defense_bonus", 0)
        item.health_bonus = template.get("health_bonus", 0)
        item.speed_bonus = template.get("speed_bonus", 0)
        item.equippable = template.get("equippable", False)
        item.stackable = template.get("stackable", False)
        item.is_weapon = template.get("is_weapon", False)
        item.is_armor = template.get("is_armor", False)
        item.is_consumable = template.get("is_consumable", False)
        item.effect = template.get("effect", "")
        
        return item
    
    def get_inventory_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get inventory events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List[Dict[str, Any]]: Inventory events
        """
        return self.inventory_events[-limit:]
    
    def get_current_timestamp(self) -> str:
        """
        Get current timestamp.
        
        Returns:
            str: Current timestamp
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def clear_inventory_events(self) -> None:
        """Clear all inventory events."""
        self.inventory_events.clear()
    
    def add_item_template(self, template_name: str, template_data: Dict[str, Any]) -> None:
        """
        Add a new item template.
        
        Args:
            template_name: Name of the template
            template_data: Template data
        """
        self.item_templates[template_name] = template_data
    
    def get_item_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all item templates.
        
        Returns:
            Dict[str, Dict[str, Any]]: Item templates
        """
        return self.item_templates.copy()