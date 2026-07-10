"""Player profile service for building player profiles from player state."""

from typing import Dict, List, Any, Optional

from src.domain.value_objects.power_levels import (
    PlayerProfile, OffensivePower, DefensivePower, SkillSet
)
from src.domain.entities.player import Player


__all__ = ["PlayerProfileService"]


class PlayerProfileService:
    """
    Service for building PlayerProfile from player state for LLM consumption.
    
    This service computes power levels and skills from player stats and equipment.
    """
    
    def __init__(self, entity_repository: Any = None):
        """
        Initialize the PlayerProfileService.
        
        Args:
            entity_repository: Optional repository for entity data access
        """
        self._entity_repository = entity_repository
    
    def build_profile(self, player: Player) -> PlayerProfile:
        """
        Build a full profile from player state.
        
        Args:
            player: The player entity
            
        Returns:
            PlayerProfile: The computed player profile
        """
        offensive_power = self._compute_offensive_power(player)
        defensive_power = self._compute_defensive_power(player)
        skills = self._compute_skills(player)
        playstyle = self._compute_playstyle(player)
        
        # Get inventory summary
        inventory_summary = player.get_inventory_items() if hasattr(player, 'get_inventory_items') else []
        
        return PlayerProfile(
            offensive_power=offensive_power,
            defensive_power=defensive_power,
            skills=skills,
            inventory_summary=inventory_summary,
            playstyle_indicators=playstyle
        )
    
    def _compute_offensive_power(self, player: Player) -> OffensivePower:
        """
        Compute offensive power from player stats and equipment.
        
        Args:
            player: The player entity
            
        Returns:
            OffensivePower: Computed offensive power
        """
        stats = player.stats if hasattr(player, 'stats') else None
        STR = stats.strength if stats else 10
        DEX = stats.dexterity if stats else 10
        INT = stats.intelligence if stats else 10
        WIS = stats.wisdom if stats else 10
        CHA = stats.charisma if stats else 10
        
        # Get weapon bonuses
        weapon_bonus = 0
        fire_bonus = 0
        ice_bonus = 0
        lightning_bonus = 0
        poison_bonus = 0
        arcane_bonus = 0
        divine_bonus = 0
        shadow_bonus = 0
        slashing_bonus = 0
        piercing_bonus = 0
        bludgeoning_bonus = 0
        
        if hasattr(player, 'equipment') and player.equipment:
            equipped = player.equipment.get_equipped_items() if hasattr(player.equipment, 'get_equipped_items') else {}
            weapon = equipped.get('weapon')
            if weapon:
                weapon_bonus = getattr(weapon, 'damage_bonus', 0)
                slashing_bonus = getattr(weapon, 'slashing_bonus', 0)
                piercing_bonus = getattr(weapon, 'piercing_bonus', 0)
                bludgeoning_bonus = getattr(weapon, 'bludgeoning_bonus', 0)
                fire_bonus = getattr(weapon, 'fire_bonus', 0)
                ice_bonus = getattr(weapon, 'ice_bonus', 0)
                lightning_bonus = getattr(weapon, 'lightning_bonus', 0)
                poison_bonus = getattr(weapon, 'poison_bonus', 0)
                arcane_bonus = getattr(weapon, 'arcane_bonus', 0)
                divine_bonus = getattr(weapon, 'divine_bonus', 0)
                shadow_bonus = getattr(weapon, 'shadow_bonus', 0)
        
        return OffensivePower(
            melee_strength=STR * 2 + weapon_bonus,
            melee_precision=DEX * 1.5 + weapon_bonus,
            piercing=DEX * 1.0 + piercing_bonus,
            slashing=STR * 1.0 + slashing_bonus,
            bludgeoning=STR * 1.5 + bludgeoning_bonus,
            fire_magic=INT * 1.0 + fire_bonus,
            ice_magic=INT * 0.8 + ice_bonus,
            lightning_magic=INT * 1.0 + lightning_bonus,
            poison_magic=INT * 0.7 + WIS * 0.3 + poison_bonus,
            arcane_magic=INT * 1.5 + arcane_bonus,
            divine_magic=WIS * 1.5 + divine_bonus,
            shadow_magic=INT * 0.8 + CHA * 0.5 + shadow_bonus
        )
    
    def _compute_defensive_power(self, player: Player) -> DefensivePower:
        """
        Compute defensive power from player stats and equipment.
        
        Args:
            player: The player entity
            
        Returns:
            DefensivePower: Computed defensive power
        """
        stats = player.stats if hasattr(player, 'stats') else None
        STR = stats.strength if stats else 10
        DEX = stats.dexterity if stats else 10
        CON = stats.constitution if stats else 10
        INT = stats.intelligence if stats else 10
        WIS = stats.wisdom if stats else 10
        CHA = stats.charisma if stats else 10
        
        # Get armor bonuses
        armor_bonus = 0
        armor_penalty = 0
        fire_resist = 0
        ice_resist = 0
        lightning_resist = 0
        poison_resist = 0
        arcane_resist = 0
        divine_resist = 0
        shadow_resist = 0
        
        if hasattr(player, 'equipment') and player.equipment:
            equipped = player.equipment.get_equipped_items() if hasattr(player.equipment, 'get_equipped_items') else {}
            armor = equipped.get('armor')
            if armor:
                armor_bonus = getattr(armor, 'armor_bonus', 0)
                armor_penalty = getattr(armor, 'penalty', 0)
                fire_resist = getattr(armor, 'fire_resist', 0)
                ice_resist = getattr(armor, 'ice_resist', 0)
                lightning_resist = getattr(armor, 'lightning_resist', 0)
                poison_resist = getattr(armor, 'poison_resist', 0)
                arcane_resist = getattr(armor, 'arcane_resist', 0)
                divine_resist = getattr(armor, 'divine_resist', 0)
                shadow_resist = getattr(armor, 'shadow_resist', 0)
        
        return DefensivePower(
            physical_armor=CON * 1.0 + armor_bonus,
            piercing_resist=armor_bonus * 0.5 + CON * 0.3,
            slashing_resist=armor_bonus * 0.5 + CON * 0.3,
            bludgeoning_resist=armor_bonus * 0.5 + CON * 0.4,
            fire_resist=WIS * 0.5 + fire_resist,
            ice_resist=WIS * 0.5 + ice_resist,
            lightning_resist=DEX * 0.3 + WIS * 0.3 + lightning_resist,
            poison_resist=CON * 0.5 + poison_resist,
            arcane_resist=INT * 0.5 + WIS * 0.5 + arcane_resist,
            divine_resist=WIS * 0.8 + divine_resist,
            shadow_resist=CHA * 0.3 + WIS * 0.5 + shadow_resist,
            evasion=DEX * 2.0 - armor_penalty
        )
    
    def _compute_skills(self, player: Player) -> SkillSet:
        """
        Compute skills from player stats.
        
        Args:
            player: The player entity
            
        Returns:
            SkillSet: Computed skills
        """
        stats = player.stats if hasattr(player, 'stats') else None
        STR = stats.strength if stats else 10
        DEX = stats.dexterity if stats else 10
        CON = stats.constitution if stats else 10
        INT = stats.intelligence if stats else 10
        WIS = stats.wisdom if stats else 10
        CHA = stats.charisma if stats else 10
        
        return SkillSet(
            sneakiness=DEX * 1.5 + CHA * 0.5,
            stealth=DEX * 1.0 + WIS * 0.5,
            acrobatics=DEX * 1.5 + STR * 0.5,
            perception=WIS * 2.0,
            investigation=INT * 1.5 + WIS * 0.5,
            intimidation=STR * 1.0 + CHA * 1.0,
            persuasion=CHA * 2.0,
            deception=CHA * 1.5 + INT * 0.5,
            language=INT * 1.0 + CHA * 1.0,
            arcane_knowledge=INT * 2.0,
            survival=WIS * 1.5 + CON * 0.5,
            medicine=WIS * 1.5 + INT * 0.5,
            weapon_mastery=STR * 1.0 + DEX * 1.0,
            armor_mastery=CON * 1.5 + STR * 0.5,
            tactical_awareness=INT * 1.0 + WIS * 1.0
         )
     
    def apply_combat_skills(self, player: Player) -> None:
        """Compute SkillSet from stats and attach to a PowerComponent on the player
        (src.domain Player) so combat_factors.get_skill_bonuses Case 1 can read
        weapon_mastery/armor_mastery/tactical_awareness during combat."""
        from src.domain.components.power_component import PowerComponent
        skills = self._compute_skills(player)
        pc = player.get_component("power")
        if pc is None:
            pc = PowerComponent(entity_id=player.id)
            player.add_component("power", pc)
        pc.skills = skills

    
    def apply_combat_skills_to_entity(self, entity: Any) -> None:
        """B3 FIX: attach a PowerComponent+SkillSet to the in-game darkdelve.Entity
        player (used by CombatResolver) so skills are first-class for ALL entities.
        Handles darkdelve.Entity.stats (dict) and src.domain Player.stats (Stats obj)."""
        from src.domain.components.power_component import PowerComponent
        from src.domain.value_objects.power_levels import SkillSet
        stats = getattr(entity, 'stats', None)
        if isinstance(stats, dict):
            STR = stats.get('str', 10); DEX = stats.get('dex', 10)
            CON = stats.get('con', 10); INT = stats.get('int', 10)
            WIS = stats.get('wis', 10); CHA = stats.get('cha', 10)
        else:
            STR = getattr(stats, 'strength', 10); DEX = getattr(stats, 'dexterity', 10)
            CON = getattr(stats, 'constitution', 10); INT = getattr(stats, 'intelligence', 10)
            WIS = getattr(stats, 'wisdom', 10); CHA = getattr(stats, 'charisma', 10)
        skillset = SkillSet(
            weapon_mastery=STR * 1.0 + DEX * 1.0,
            armor_mastery=CON * 1.5 + STR * 0.5,
            tactical_awareness=INT * 1.0 + WIS * 1.0,
        )
        pc = entity.get_component("power")
        if pc is None:
            pc = PowerComponent(entity_id=getattr(entity, 'id', None))
            entity.add_component("power", pc)
        pc.skills = skillset

    
    def _compute_playstyle(self, player: Player) -> Dict[str, float]:
        """
        Analyze combat history to determine playstyle.
        
        Args:
            player: The player entity
            
        Returns:
            Dict[str, float]: Playstyle indicators
        """
        # Default playstyle - would be computed from actual combat history
        return {
            "aggressive": 0.5,
            "cautious": 0.3,
            "explorer": 0.7,
            "social": 0.4
        }
    
    def get_profile_summary(self, player: Player) -> str:
        """
        Get LLM-friendly text summary of player profile.
        
        Args:
            player: The player entity
            
        Returns:
            str: Text summary for LLM
        """
        profile = self.build_profile(player)
        return profile.summary_for_llm()