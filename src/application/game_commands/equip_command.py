"""
Equip command for equipment management.
"""
from typing import Optional, Dict, Any
from .base_command import BaseCommand, CommandResult
from ...domain.entities.player import Player
from ...domain.entities.item import Item


class EquipCommand(BaseCommand):
    """
    Command for handling equipment actions.
    
    Implements the Command pattern for equipping items.
    """
    
    def __init__(self, player: Player, item: Item):
        """
        Initialize the equip command.
        
        Args:
            player: The player entity equipping the item
            item: The item entity to be equipped
        """
        super().__init__("equip")
        self.player = player
        self.item = item
        self.previous_equipped_item = None
        self.equipped = False
    
    def execute(self, *args, **kwargs) -> CommandResult:
        """
        Execute the equip command.
        
        Args:
            *args: Additional arguments (not used)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            CommandResult: The result of the equip execution
        """
        if not self.can_execute():
            return CommandResult(
                success=False,
                error_message="Cannot execute equip command"
            )
        
        try:
            # Store previously equipped item for undo
            equipment_slot = self.player.get_equipment_slot(self.item)
            if equipment_slot:
                self.previous_equipped_item = self.player.get_equipped_item(equipment_slot)
            
            # Execute the equip
            self.equipped = self.player.equip_item(self.item)
            
            if not self.equipped:
                return CommandResult(
                    success=False,
                    error_message="Failed to equip item"
                )
            
            self.executed = True
            return CommandResult(
                success=True,
                data={
                    "player_id": self.player.id,
                    "item_id": self.item.id,
                    "item_name": self.item.name,
                    "item_type": self.item.item_type,
                    "equipment_slot": self.player.get_equipment_slot(self.item)
                },
                metadata={
                    "previous_equipped_item": self.previous_equipped_item.id if self.previous_equipped_item else None,
                    "stat_changes": self.calculate_stat_changes()
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error_message=f"Failed to execute equip: {str(e)}"
            )
    
    def undo(self) -> CommandResult:
        """
        Undo the equip command.
        
        Returns:
            CommandResult: The result of the undo operation
        """
        if not self.executed or not self.equipped:
            return CommandResult(
                success=False,
                error_message="Cannot undo unexecuted or failed equip command"
            )
        
        try:
            # Unequip the current item
            self.player.unequip_item(self.item)
            
            # Re-equip the previous item if it existed
            if self.previous_equipped_item:
                self.player.equip_item(self.previous_equipped_item)
            
            return CommandResult(
                success=True,
                data={
                    "player_id": self.player.id,
                    "item_id": self.item.id,
                    "item_name": self.item.name,
                    "item_type": self.item.item_type,
                    "equipment_slot": None
                },
                metadata={
                    "previous_equipped_item": self.previous_equipped_item.id if self.previous_equipped_item else None,
                    "stat_changes": self.calculate_stat_changes()
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error_message=f"Failed to undo equip: {str(e)}"
            )
    
    def can_execute(self, *args, **kwargs) -> bool:
        """
        Check if the equip command can be executed.
        
        Args:
            *args: Additional arguments (not used)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            bool: True if the equip can be executed, False otherwise
        """
        if not self.player or not self.item:
            return False
        
        # Check if player has the item
        if self.player.get_item_count(self.item) <= 0:
            return False
        
        # Check if item is equipment
        if not self.item.is_equipment:
            return False
        
        # Check if item has an equipment slot
        if not self.player.get_equipment_slot(self.item):
            return False
        
        return True
    
    def validate_parameters(self, *args, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate equip command parameters.
        
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
    
    def calculate_stat_changes(self) -> Dict[str, int]:
        """
        Calculate stat changes from equipping the item.
        
        Returns:
            Dict[str, int]: Dictionary of stat changes
        """
        stat_changes = {}
        
        if self.item.attack_bonus:
            stat_changes["attack"] = self.item.attack_bonus
        
        if self.item.defense_bonus:
            stat_changes["defense"] = self.item.defense_bonus
        
        if self.item.health_bonus:
            stat_changes["health"] = self.item.health_bonus
        
        if self.item.speed_bonus:
            stat_changes["speed"] = self.item.speed_bonus
        
        return stat_changes