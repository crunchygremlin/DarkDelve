"""
Drop command for item management.
"""
from typing import Optional, Dict, Any
from .base_command import BaseCommand, CommandResult
from ...domain.entities.player import Player
from ...domain.entities.item import Item
from ...domain.value_objects.position import Position


def _get_player_position(player) -> Position:
    """Return the player's position, handling both domain Player (.position)
    and runtime Entity (.x/.y) attribute layouts."""
    if hasattr(player, 'position') and isinstance(player.position, Position):
        return player.position
    x = getattr(player, 'x', 0)
    y = getattr(player, 'y', 0)
    return Position(x, y)


class DropCommand(BaseCommand):
    """
    Command for handling item dropping actions.

    Implements the Command pattern for dropping items.
    """

    def __init__(self, player: Player, item: Item):
        """
        Initialize the drop command.

        Args:
            player: The player entity dropping the item
            item: The item entity to be dropped
        """
        super().__init__("drop")
        self.player = player
        self.item = item
        self.previous_item_count = player.get_item_count(item) if player else 0
        self.dropped = False

    def execute(self, *args, **kwargs) -> CommandResult:
        """
        Execute the drop command.

        Args:
            *args: Additional arguments (not used)
            **kwargs: Additional keyword arguments (not used)

        Returns:
            CommandResult: The result of the drop execution
        """
        if not self.can_execute():
            return CommandResult(
                success=False,
                error_message="Cannot execute drop command"
            )

        try:
            # Store previous item count for undo
            self.previous_item_count = self.player.get_item_count(self.item)

            # Execute the drop
            self.dropped = self.player.drop_item(self.item)

            if not self.dropped:
                return CommandResult(
                    success=False,
                    error_message="Failed to drop item"
                )

            self.executed = True
            drop_pos = _get_player_position(self.player)
            return CommandResult(
                success=True,
                data={
                    "player_id": self.player.id,
                    "item_id": self.item.id,
                    "item_name": self.item.name,
                    "item_type": self.item.item_type,
                    "drop_position": drop_pos,
                },
                metadata={
                    "previous_item_count": self.previous_item_count,
                    "current_item_count": self.player.get_item_count(self.item)
                }
            )

        except Exception as e:
            return CommandResult(
                success=False,
                error_message=f"Failed to execute drop: {str(e)}"
            )

    def undo(self) -> CommandResult:
        """
        Undo the drop command.

        Returns:
            CommandResult: The result of the undo operation
        """
        if not self.executed or not self.dropped:
            return CommandResult(
                success=False,
                error_message="Cannot undo unexecuted or failed drop command"
            )

        try:
            # Add the item back to player's inventory
            self.player.add_item(self.item)

            # Reset item position to player's position
            drop_pos = _get_player_position(self.player)
            if hasattr(self.item, 'x') and hasattr(self.item, 'y'):
                self.item.x = drop_pos.x
                self.item.y = drop_pos.y
            elif hasattr(self.item, 'position'):
                self.item.position = drop_pos

            return CommandResult(
                success=True,
                data={
                    "player_id": self.player.id,
                    "item_id": self.item.id,
                    "item_name": self.item.name,
                    "item_type": self.item.item_type,
                    "drop_position": drop_pos,
                },
                metadata={
                    "previous_item_count": self.previous_item_count,
                    "current_item_count": self.player.get_item_count(self.item)
                }
            )

        except Exception as e:
            return CommandResult(
                success=False,
                error_message=f"Failed to undo drop: {str(e)}"
            )

    def can_execute(self, *args, **kwargs) -> bool:
        """
        Check if the drop command can be executed.

        Args:
            *args: Additional arguments (not used)
            **kwargs: Additional keyword arguments (not used)

        Returns:
            bool: True if the drop can be executed, False otherwise
        """
        if not self.player or not self.item:
            return False

        # Check if player has the item
        if self.player.get_item_count(self.item) <= 0:
            return False

        # Check if item is droppable
        if not self.item.is_droppable:
            return False

        return True

    def validate_parameters(self, *args, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate drop command parameters.

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
