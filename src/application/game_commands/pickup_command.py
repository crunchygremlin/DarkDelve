"""
Pickup command for item collection.
"""
from typing import Optional, Dict, Any
from .base_command import BaseCommand, CommandResult
from ...domain.entities.player import Player
from ...domain.entities.item import Item
from ...domain.value_objects.position import Position


class PickupCommand(BaseCommand):
    """
    Command for handling item pickup actions.
    
    Implements the Command pattern for item collection.
    """
    
    def __init__(self, player: Player, item: Item):
        """
        Initialize the pickup command.
        
        Args:
            player: The player entity picking up the item
            item: The item entity to be picked up
        """
        super().__init__("pickup")
        self.player = player
        self.item = item
        self.previous_item_position = Position(item.x, item.y)
        self.picked_up = False
    
    def execute(self, *args, **kwargs) -> CommandResult:
        """
        Execute the pickup command.
        
        Args:
            *args: Additional arguments (not used)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            CommandResult: The result of the pickup execution
        """
        if not self.can_execute():
            return CommandResult(
                success=False,
                error_message="Cannot execute pickup command"
            )
        
        try:
            # Store previous position for undo
            self.previous_item_position = Position(self.item.x, self.item.y)
            
            # Execute the pickup
            self.picked_up = self.player.pickup_item(self.item)
            
            if not self.picked_up:
                return CommandResult(
                    success=False,
                    error_message="Failed to pickup item (inventory may be full)"
                )
            
            self.executed = True
            return CommandResult(
                success=True,
                data={
                    "player_id": self.player.id,
                    "item_id": self.item.id,
                    "item_name": self.item.name,
                    "item_type": self.item.item_type
                },
                metadata={
                    "pickup_position": self.previous_item_position,
                    "inventory_slot": self.player.get_item_slot(self.item)
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error_message=f"Failed to execute pickup: {str(e)}"
            )
    
    def undo(self) -> CommandResult:
        """
        Undo the pickup command.
        
        Returns:
            CommandResult: The result of the undo operation
        """
        if not self.executed or not self.picked_up:
            return CommandResult(
                success=False,
                error_message="Cannot undo unexecuted or failed pickup command"
            )
        
        try:
            # Remove item from player's inventory and place it back
            self.player.drop_item(self.item)
            self.item.x = self.previous_item_position.x
            self.item.y = self.previous_item_position.y
            
            return CommandResult(
                success=True,
                data={
                    "player_id": self.player.id,
                    "item_id": self.item.id,
                    "item_name": self.item.name,
                    "item_type": self.item.item_type
                },
                metadata={
                    "pickup_position": self.previous_item_position,
                    "inventory_slot": None
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error_message=f"Failed to undo pickup: {str(e)}"
            )
    
    def can_execute(self, *args, **kwargs) -> bool:
        """
        Check if the pickup command can be executed.
        
        Args:
            *args: Additional arguments (not used)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            bool: True if the pickup can be executed, False otherwise
        """
        if not self.player or not self.item:
            return False
        
        # Check if player is adjacent to item (assuming 1 tile distance)
        player_pos = Position(self.player.x, self.player.y)
        item_pos = Position(self.item.x, self.item.y)
        distance = player_pos.distance_to(item_pos)
        
        if distance > 1:
            return False
        
        # Check if item is pickupable
        if not self.item.is_pickupable:
            return False
        
        return True
    
    def validate_parameters(self, *args, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate pickup command parameters.
        
        Args:
            *args: Additional arguments (not used)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            tuple: (is_valid, error_message) where is_valid is True if parameters are valid
        """
        if not self.player:
            return False, "Player is required"
        
        if not self.item:
            return False, "Item is required"
        
        if not isinstance(self.player, Player):
            return False, "Player must be a Player entity"
        
        if not isinstance(self.item, Item):
            return False, "Item must be an Item entity"
        
        return True, None