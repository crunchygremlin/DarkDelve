"""
Attack command for combat actions.
"""
from typing import Optional, Dict, Any
from .base_command import BaseCommand, CommandResult
from ...domain.entities.player import Player
from ...domain.entities.mob import Mob
from ...domain.value_objects.position import Position


class AttackCommand(BaseCommand):
    """
    Command for handling player attacks.
    
    Implements the Command pattern for combat actions.
    """
    
    def __init__(self, attacker: Player, target: Mob):
        """
        Initialize the attack command.
        
        Args:
            attacker: The player entity attacking
            target: The mob entity being attacked
        """
        super().__init__("attack")
        self.attacker = attacker
        self.target = target
        self.previous_target_health = target.health if target else 0
        self.damage_dealt = 0
    
    def execute(self, *args, **kwargs) -> CommandResult:
        """
        Execute the attack command.
        
        Args:
            *args: Additional arguments (not used)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            CommandResult: The result of the attack execution
        """
        if not self.can_execute():
            return CommandResult(
                success=False,
                error_message="Cannot execute attack command"
            )
        
        try:
            # Store previous health for undo
            self.previous_target_health = self.target.health
            
            # Execute the attack
            self.damage_dealt = self.attacker.attack(self.target)
            
            self.executed = True
            return CommandResult(
                success=True,
                data={
                    "attacker_id": self.attacker.id,
                    "target_id": self.target.id,
                    "damage_dealt": self.damage_dealt,
                    "target_remaining_health": self.target.health
                },
                metadata={
                    "attack_type": "melee",
                    "critical_hit": self.damage_dealt > self.attacker.attack_power * 1.5
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error_message=f"Failed to execute attack: {str(e)}"
            )
    
    def undo(self) -> CommandResult:
        """
        Undo the attack command.
        
        Returns:
            CommandResult: The result of the undo operation
        """
        if not self.executed:
            return CommandResult(
                success=False,
                error_message="Cannot undo unexecuted attack command"
            )
        
        try:
            # Restore target's previous health
            self.target.health = self.previous_target_health
            
            return CommandResult(
                success=True,
                data={
                    "attacker_id": self.attacker.id,
                    "target_id": self.target.id,
                    "damage_restored": self.damage_dealt,
                    "target_restored_health": self.target.health
                },
                metadata={
                    "attack_type": "melee",
                    "critical_hit": self.damage_dealt > self.attacker.attack_power * 1.5
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error_message=f"Failed to undo attack: {str(e)}"
            )
    
    def can_execute(self, *args, **kwargs) -> bool:
        """
        Check if the attack command can be executed.
        
        Args:
            *args: Additional arguments (not used)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            bool: True if the attack can be executed, False otherwise
        """
        if not self.attacker or not self.target:
            return False
        
        # Check if target is already dead
        if self.target.health <= 0:
            return False
        
        # Check if attacker is in range (assuming 5 tiles for now)
        # Use Position component instead of direct x/y attributes
        attacker_pos = self.attacker.get_component("position")
        target_pos = self.target.get_component("position")
        
        if attacker_pos and target_pos:
            distance = attacker_pos.distance_to(target_pos)
            if distance > 5:
                return False
        else:
            # If position components not available, allow the attack
            pass
        
        return True
    
    def validate_parameters(self, *args, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate attack command parameters.
        
        Args:
            *args: Additional arguments (not used)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            tuple: (is_valid, error_message) where is_valid is True if parameters are valid
        """
        if not self.attacker:
            return False, "Attacker is required"
        
        if not self.target:
            return False, "Target is required"
        
        if not isinstance(self.attacker, Player):
            return False, "Attacker must be a Player entity"
        
        if not isinstance(self.target, Mob):
            return False, "Target must be a Mob entity"
        
        return True, None