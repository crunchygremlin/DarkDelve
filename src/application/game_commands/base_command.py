"""
Base command class for the application layer command pattern.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class CommandResult:
    """Result of a command execution."""
    success: bool
    data: Optional[Any] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseCommand(ABC):
    """
    Abstract base class for all game commands.
    
    Implements the Command pattern for handling game actions.
    """
    
    def __init__(self, command_id: str):
        """
        Initialize the command.
        
        Args:
            command_id: Unique identifier for the command
        """
        self.command_id = command_id
        self.executed = False
        self.result: Optional[CommandResult] = None
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> CommandResult:
        """
        Execute the command.
        
        Args:
            *args: Command-specific arguments
            **kwargs: Command-specific keyword arguments
            
        Returns:
            CommandResult: The result of the execution
        """
        pass
    
    @abstractmethod
    def undo(self) -> CommandResult:
        """
        Undo the command execution.
        
        Returns:
            CommandResult: The result of the undo operation
        """
        pass
    
    def can_execute(self, *args, **kwargs) -> bool:
        """
        Check if the command can be executed.
        
        Args:
            *args: Command-specific arguments
            **kwargs: Command-specific keyword arguments
            
        Returns:
            bool: True if the command can be executed, False otherwise
        """
        return True
    
    def validate_parameters(self, *args, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate command parameters.
        
        Args:
            *args: Command-specific arguments
            **kwargs: Command-specific keyword arguments
            
        Returns:
            tuple: (is_valid, error_message) where is_valid is True if parameters are valid
        """
        return True, None