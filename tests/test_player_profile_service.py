"""Tests for player profile service."""

import pytest
from unittest.mock import MagicMock

from src.domain.services.player_profile_service import PlayerProfileService
from src.domain.value_objects.power_levels import (
    PlayerProfile, OffensivePower, DefensivePower, SkillSet
)
from src.domain.entities.player import Player
from src.domain.value_objects.position import Position
from src.domain.value_objects.stats import Stats


class TestPlayerProfileService:
    """Tests for PlayerProfileService class."""
    
    def test_init(self):
        """Test PlayerProfileService initialization."""
        service = PlayerProfileService()
        assert service._entity_repository is None
        
        repo = MagicMock()
        service = PlayerProfileService(repo)
        assert service._entity_repository == repo
    
    def test_build_profile(self):
        """Test building a player profile."""
        service = PlayerProfileService()
        
        player = Player(position=Position(0, 0))
        player.stats.strength = 14
        player.stats.dexterity = 12
        player.stats.constitution = 12
        player.stats.intelligence = 10
        player.stats.wisdom = 8
        player.stats.charisma = 10
        
        profile = service.build_profile(player)
        
        assert isinstance(profile, PlayerProfile)
        assert isinstance(profile.offensive_power, OffensivePower)
        assert isinstance(profile.defensive_power, DefensivePower)
        assert isinstance(profile.skills, SkillSet)
    
    def test_compute_offensive_power(self):
        """Test computing offensive power."""
        service = PlayerProfileService()
        
        player = Player(position=Position(0, 0))
        player.stats.strength = 16
        player.stats.dexterity = 14
        player.stats.intelligence = 12
        
        power = service._compute_offensive_power(player)
        
        assert power.melee_strength == 16 * 2  # STR * 2
        assert power.melee_precision == 14 * 1.5  # DEX * 1.5
        assert power.fire_magic == 12 * 1.0  # INT * 1.0
    
    def test_compute_defensive_power(self):
        """Test computing defensive power."""
        service = PlayerProfileService()
        
        player = Player(position=Position(0, 0))
        player.stats.constitution = 14
        player.stats.dexterity = 12
        player.stats.wisdom = 10
        player.stats.intelligence = 8
        
        power = service._compute_defensive_power(player)
        
        assert power.physical_armor == 14 * 1.0  # CON * 1.0
        assert power.evasion == 12 * 2.0  # DEX * 2.0
    
    def test_compute_skills(self):
        """Test computing skills."""
        service = PlayerProfileService()
        
        player = Player(position=Position(0, 0))
        player.stats.dexterity = 14
        player.stats.wisdom = 12
        player.stats.charisma = 10
        player.stats.strength = 8
        player.stats.intelligence = 6
        
        skills = service._compute_skills(player)
        
        assert skills.perception == 12 * 2.0  # WIS * 2.0
        assert skills.stealth == 14 * 1.0 + 12 * 0.5  # DEX * 1.0 + WIS * 0.5
        assert skills.sneakiness == 14 * 1.5 + 10 * 0.5  # DEX * 1.5 + CHA * 0.5
    
    def test_compute_playstyle(self):
        """Test computing playstyle indicators."""
        service = PlayerProfileService()
        
        player = Player(position=Position(0, 0))
        
        playstyle = service._compute_playstyle(player)
        
        assert isinstance(playstyle, dict)
        assert "aggressive" in playstyle
        assert "cautious" in playstyle
    
    def test_get_profile_summary(self):
        """Test getting profile summary for LLM."""
        service = PlayerProfileService()
        
        player = Player(position=Position(0, 0))
        player.stats.strength = 14
        player.stats.dexterity = 12
        player.stats.constitution = 12
        player.stats.intelligence = 10
        player.stats.wisdom = 8
        player.stats.charisma = 10
        
        summary = service.get_profile_summary(player)
        
        assert "=== PLAYER PROFILE ===" in summary
        assert "Offensive:" in summary
        assert "Defensive:" in summary
        assert "Skills:" in summary


class TestOffensivePowerCalculations:
    """Tests for offensive power calculations."""
    
    def test_melee_strength_calculation(self):
        """Test melee strength calculation."""
        service = PlayerProfileService()
        
        player = Player(position=Position(0, 0))
        player.stats.strength = 16
        
        power = service._compute_offensive_power(player)
        
        assert power.melee_strength == 32  # 16 * 2
    
    def test_fire_magic_calculation(self):
        """Test fire magic calculation."""
        service = PlayerProfileService()
        
        player = Player(position=Position(0, 0))
        player.stats.intelligence = 14
        
        power = service._compute_offensive_power(player)
        
        assert power.fire_magic == 14  # INT * 1.0
    
    def test_arcane_magic_calculation(self):
        """Test arcane magic calculation."""
        service = PlayerProfileService()
        
        player = Player(position=Position(0, 0))
        player.stats.intelligence = 12
        
        power = service._compute_offensive_power(player)
        
        assert power.arcane_magic == 18  # INT * 1.5
    
    def test_divine_magic_calculation(self):
        """Test divine magic calculation."""
        service = PlayerProfileService()
        
        player = Player(position=Position(0, 0))
        player.stats.wisdom = 14
        
        power = service._compute_offensive_power(player)
        
        # Also check defensive for divine resist
        defense = service._compute_defensive_power(player)
        assert defense.divine_resist == 14 * 0.8  # WIS * 0.8


class TestDefensivePowerCalculations:
    """Tests for defensive power calculations."""
    
    def test_physical_armor_calculation(self):
        """Test physical armor calculation."""
        service = PlayerProfileService()
        
        player = Player(position=Position(0, 0))
        player.stats.constitution = 14
        
        power = service._compute_defensive_power(player)
        
        assert power.physical_armor == 14  # CON * 1.0
    
    def test_evasion_calculation(self):
        """Test evasion calculation."""
        service = PlayerProfileService()
        
        player = Player(position=Position(0, 0))
        player.stats.dexterity = 15
        
        power = service._compute_defensive_power(player)
        
        assert power.evasion == 30  # DEX * 2.0
    
    def test_lightning_resist_calculation(self):
        """Test lightning resist calculation."""
        service = PlayerProfileService()
        
        player = Player(position=Position(0, 0))
        player.stats.dexterity = 10
        player.stats.wisdom = 10
        
        power = service._compute_defensive_power(player)
        
        assert power.lightning_resist == 10 * 0.3 + 10 * 0.3  # DEX * 0.3 + WIS * 0.3


class TestSkillSetCalculations:
    """Tests for skill set calculations."""
    
    def test_perception_skill(self):
        """Test perception skill calculation."""
        service = PlayerProfileService()
        
        player = Player(position=Position(0, 0))
        player.stats.wisdom = 15
        
        skills = service._compute_skills(player)
        
        assert skills.perception == 30  # WIS * 2.0
    
    def test_persuasion_skill(self):
        """Test persuasion skill calculation."""
        service = PlayerProfileService()
        
        player = Player(position=Position(0, 0))
        player.stats.charisma = 16
        
        skills = service._compute_skills(player)
        
        assert skills.persuasion == 32  # CHA * 2.0
    
    def test_investigation_skill(self):
        """Test investigation skill calculation."""
        service = PlayerProfileService()
        
        player = Player(position=Position(0, 0))
        player.stats.intelligence = 14
        player.stats.wisdom = 12
        
        skills = service._compute_skills(player)
        
        assert skills.investigation == 14 * 1.5 + 12 * 0.5  # INT * 1.5 + WIS * 0.5
    
    def test_weapon_mastery_skill(self):
        """Test weapon mastery skill calculation."""
        service = PlayerProfileService()
        
        player = Player(position=Position(0, 0))
        player.stats.strength = 14
        player.stats.dexterity = 12
        
        skills = service._compute_skills(player)
        
        assert skills.weapon_mastery == 14 + 12  # STR + DEX