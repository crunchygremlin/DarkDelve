"""Tests for PowerComponent."""

import pytest
from src.domain.components.power_component import PowerComponent
from src.domain.value_objects.power_levels import OffensivePower, DefensivePower, SkillSet


class TestPowerComponent:
    """Tests for PowerComponent."""

    def test_component_type(self):
        """Test component type is correct."""
        comp = PowerComponent(entity_id="test_entity")
        assert comp.component_type == "power"

    def test_default_values(self):
        """Test default values are set correctly."""
        comp = PowerComponent(entity_id="test_entity")
        assert comp.entity_id == "test_entity"
        assert isinstance(comp.offensive, OffensivePower)
        assert isinstance(comp.defensive, DefensivePower)
        assert isinstance(comp.skills, SkillSet)

    def test_get_attack_power(self):
        """Test getting attack power for a damage type."""
        comp = PowerComponent(
            entity_id="test_entity",
            offensive=OffensivePower(melee_strength=10.0, fire_magic=15.0)
        )
        assert comp.get_attack_power("melee_strength") == 10.0
        assert comp.get_attack_power("fire_magic") == 15.0
        assert comp.get_attack_power("nonexistent") == 0.0

    def test_get_defense_power(self):
        """Test getting defense power for a damage type."""
        comp = PowerComponent(
            entity_id="test_entity",
            defensive=DefensivePower(
                physical_armor=5.0,
                fire_resist=8.0,
                slashing_resist=3.0
            )
        )
        assert comp.get_defense_power("physical_armor") == 5.0
        assert comp.get_defense_power("fire_resist") == 8.0
        assert comp.get_defense_power("slashing_resist") == 3.0

    def test_get_skill(self):
        """Test getting skill level."""
        comp = PowerComponent(
            entity_id="test_entity",
            skills=SkillSet(perception=0.8, stealth=0.6, weapon_mastery=0.9)
        )
        assert comp.get_skill("perception") == 0.8
        assert comp.get_skill("stealth") == 0.6
        assert comp.get_skill("weapon_mastery") == 0.9
        assert comp.get_skill("nonexistent") == 0.0

    def test_with_custom_power_levels(self):
        """Test component with custom power levels."""
        offensive = OffensivePower(
            melee_strength=20.0,
            slashing=15.0,
            fire_magic=10.0
        )
        defensive = DefensivePower(
            physical_armor=12.0,
            fire_resist=5.0,
            evasion=8.0
        )
        skills = SkillSet(
            perception=1.0,
            weapon_mastery=0.75
        )
        comp = PowerComponent(
            entity_id="warrior",
            offensive=offensive,
            defensive=defensive,
            skills=skills
        )
        assert comp.offensive.melee_strength == 20.0
        assert comp.defensive.physical_armor == 12.0
        assert comp.skills.perception == 1.0

    def test_dominant_attack_type(self):
        """Test getting dominant attack type."""
        comp = PowerComponent(
            entity_id="test_entity",
            offensive=OffensivePower(fire_magic=20.0, melee_strength=10.0)
        )
        # dominant_type returns the type with highest value
        assert comp.offensive.dominant_type() == "fire_magic"

    def test_weakest_defense(self):
        """Test getting weakest defense type."""
        # Set all values to non-zero to properly test the method
        comp = PowerComponent(
            entity_id="test_entity",
            defensive=DefensivePower(
                physical_armor=10.0,
                piercing_resist=8.0,
                slashing_resist=5.0,
                bludgeoning_resist=7.0,
                fire_resist=2.0,
                ice_resist=3.0,
                lightning_resist=4.0,
                poison_resist=5.0,
                arcane_resist=6.0,
                divine_resist=7.0,
                shadow_resist=8.0,
                evasion=9.0
            )
        )
        # fire_resist is 2.0, which is the lowest
        assert comp.defensive.weakest_defense() == "fire_resist"