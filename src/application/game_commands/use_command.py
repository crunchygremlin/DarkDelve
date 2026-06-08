"""
Use command for item usage.
"""
from typing import Optional, Dict, Any
from .base_command import BaseCommand, CommandResult
from ...domain.entities.player import Player
from ...domain.entities.item import Item


class UseCommand(BaseCommand):
    """
    Command for handling item usage actions.
    
    Implements the Command pattern for item consumption/usage.
    """
    
    def __init__(self, player: Player, item: Item):
        """
        Initialize the use command.
        
        Args:
            player: The player entity using the item
            item: The item entity to be used
        """
        super().__init__("use")
        self.player = player
        self.item = item
        self.previous_item_count = player.get_item_count(item) if player else 0
        self.item_consumed = False
    
    def execute(self, *args, **kwargs) -> CommandResult:
        """
        Execute the use command.
        
        Args:
            *args: Additional arguments (not used)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            CommandResult: The result of the use execution
        """
        if not self.can_execute():
            return CommandResult(
                success=False,
                error_message="Cannot execute use command"
            )
        
        try:
            # Store previous item count for undo
            self.previous_item_count = self.player.get_item_count(self.item)
            
            # Execute the item usage
            self.item_consumed = self.player.use_item(self.item)
            
            if not self.item_consumed:
                return CommandResult(
                    success=False,
                    error_message="Failed to use item"
                )
            
            self.executed = True
            return CommandResult(
                success=True,
                data={
                    "player_id": self.player.id,
                    "item_id": self.item.id,
                    "item_name": self.item.name,
                    "item_type": self.item.item_type,
                    "effect_applied": self.item.effect
                },
                metadata={
                    "previous_item_count": self.previous_item_count,
                    "current_item_count": self.player.get_item_count(self.item)
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error_message=f"Failed to execute use: {str(e)}"
            )
    
    def undo(self) -> CommandResult:
        """
        Undo the use command.
        
        Returns:
            CommandResult: The result of the undo operation
        """
        if not self.executed or not self.item_consumed:
            return CommandResult(
                success=False,
                error_message="Cannot undo unexecuted or failed use command"
            )
        
        try:
            # Restore item count (if consumable)
            if self.item.is_consumable:
                # Add the item back to inventory
                for _ in range(self.previous_item_count - self.player.get_item_count(self.item)):
                    self.player.add_item(self.item)
            
            # Remove any effects that were applied
            if self.item.effect:
                self.player.remove_effect(self.item.effect)
            
            return CommandResult(
                success=True,
                data={
                    "player_id": self.player.id,
                    "item_id": self.item.id,
                    "item_name": self.item.name,
                    "item_type": self.item.item_type,
                    "effect_removed": self.item.effect
                },
                metadata={
                    "previous_item_count": self.previous_item_count,
                    "current_item_count": self.player.get_item_count(self.item)
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error_message=f"Failed to undo use: {str(e)}"
            )
    
    def can_execute(self, *args, **kwargs) -> bool:
        """
        Check if the use command can be executed.
        
        Args:
            *args: Additional arguments (not used)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            bool: True if the use can be executed, False otherwise
        """
        if not self.player or not self.item:
            return False
        
        # Check if player has the item
        if self.player.get_item_count(self.item) <= 0:
            return False
        
        # Check if item is usable
        if not self.item.is_usable:
            return False
        
        # Check if item has an effect
        if not self.item.effect:
            return False
        
        return True
    
    def validate_parameters(self, *args, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate use command parameters.
        
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