"""
Move command for player movement.
"""
from typing import Optional, Tuple
from .base_command import BaseCommand, CommandResult
from ...domain.entities.player import Player
from ...domain.value_objects.position import Position


class MoveCommand(BaseCommand):
    """
    Command for handling player movement.
    
    Implements the Command pattern for player movement actions.
    """
    
    def __init__(self, player: Player, target_position: Position):
        """
        Initialize the move command.
        
        Args:
            player: The player entity to move
            target_position: The target position to move to
        """
        super().__init__("move")
        self.player = player
        self.target_position = target_position
        self.previous_position = Position(player.x, player.y)
    
    def execute(self, *args, **kwargs) -> CommandResult:
        """
        Execute the move command.
        
        Args:
            *args: Additional arguments (not used)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            CommandResult: The result of the move execution
        """
        if not self.can_execute():
            return CommandResult(
                success=False,
                error_message="Cannot execute move command"
            )
        
        try:
            # Store previous position for undo
            self.previous_position = Position(self.player.x, self.player.y)
            
            # Execute the move
            self.player.move_to(self.target_position.x, self.target_position.y)
            
            self.executed = True
            return CommandResult(
                success=True,
                data={
                    "player_id": self.player.id,
                    "from_position": self.previous_position,
                    "to_position": self.target_position
                },
                metadata={
                    "move_distance": self.previous_position.distance_to(self.target_position)
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error_message=f"Failed to execute move: {str(e)}"
            )
    
    def undo(self) -> CommandResult:
        """
        Undo the move command.
        
        Returns:
            CommandResult: The result of the undo operation
        """
        if not self.executed:
            return CommandResult(
                success=False,
                error_message="Cannot undo unexecuted move command"
            )
        
        try:
            # Move player back to previous position
            self.player.move_to(self.previous_position.x, self.previous_position.y)
            
            return CommandResult(
                success=True,
                data={
                    "player_id": self.player.id,
                    "from_position": self.target_position,
                    "to_position": self.previous_position
                },
                metadata={
                    "move_distance": self.target_position.distance_to(self.previous_position)
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error_message=f"Failed to undo move: {str(e)}"
            )
    
    def can_execute(self, *args, **kwargs) -> bool:
        """
        Check if the move command can be executed.
        
        Args:
            *args: Additional arguments (not used)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            bool: True if the move can be executed, False otherwise
        """
        if not self.player or not self.target_position:
            return False
        
        # Check if player is not moving to the same position
        if self.player.x == self.target_position.x and self.player.y == self.target_position.y:
            return False
        
        # Additional validation can be added here (e.g., check if target position is valid)
        return True
    
    def validate_parameters(self, *args, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate move command parameters.
        
        Args:
            *args: Additional arguments (not used)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            tuple: (is_valid, error_message) where is_valid is True if parameters are valid
        """
        if not self.player:
            return False, "Player is required"
        
        if not self.target_position:
            return False, "Target position is required"
        
        if not isinstance(self.target_position, Position):
            return False, "Target position must be a Position object"
        
        return True, None