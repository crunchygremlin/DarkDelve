"""Tests for power levels value objects."""

import pytest
from src.domain.value_objects.power_levels import (
    OffensivePower,
    DefensivePower,
    SkillSet,
    PlayerProfile,
)


class TestOffensivePower:
    """Tests for OffensivePower dataclass."""

    def test_default_values(self):
        power = OffensivePower()
        assert power.melee_strength == 0.0
        assert power.melee_precision == 0.0
        assert power.fire_magic == 0.0
        assert power.arcane_magic == 0.0

    def test_custom_values(self):
        power = OffensivePower(
            melee_strength=10.0,
            melee_precision=8.0,
            fire_magic=5.0
        )
        assert power.melee_strength == 10.0
        assert power.melee_precision == 8.0
        assert power.fire_magic == 5.0

    def test_as_dict(self):
        power = OffensivePower(melee_strength=5.0, fire_magic=3.0)
        d = power.as_dict()
        assert isinstance(d, dict)
        assert d["melee_strength"] == 5.0
        assert d["fire_magic"] == 3.0
        assert "piercing" in d

    def test_dominant_type(self):
        power = OffensivePower(
            melee_strength=5.0,
            fire_magic=10.0,
            ice_magic=3.0
        )
        assert power.dominant_type() == "fire_magic"

    def test_dominant_type_tie(self):
        power = OffensivePower(fire_magic=5.0, ice_magic=5.0)
        # max returns first found in case of tie
        assert power.dominant_type() in ["fire_magic", "ice_magic"]


class TestDefensivePower:
    """Tests for DefensivePower dataclass."""

    def test_default_values(self):
        power = DefensivePower()
        assert power.physical_armor == 0.0
        assert power.evasion == 0.0
        assert power.fire_resist == 0.0

    def test_custom_values(self):
        power = DefensivePower(
            physical_armor=15.0,
            evasion=7.0,
            fire_resist=5.0
        )
        assert power.physical_armor == 15.0
        assert power.evasion == 7.0
        assert power.fire_resist == 5.0

    def test_as_dict(self):
        power = DefensivePower(physical_armor=10.0, evasion=5.0)
        d = power.as_dict()
        assert isinstance(d, dict)
        assert d["physical_armor"] == 10.0
        assert d["evasion"] == 5.0

    def test_weakest_defense(self):
        power = DefensivePower(
            physical_armor=10.0,
            piercing_resist=8.0,
            slashing_resist=7.0,
            bludgeoning_resist=6.0,
            fire_resist=2.0,
            ice_resist=5.0,
            lightning_resist=4.0,
            poison_resist=3.0,
            arcane_resist=7.0,
            divine_resist=6.0,
            shadow_resist=5.0,
            evasion=2.5
        )
        assert power.weakest_defense() == "fire_resist"


class TestSkillSet:
    """Tests for SkillSet dataclass."""

    def test_default_values(self):
        skills = SkillSet()
        assert skills.stealth == 0.0
        assert skills.perception == 0.0
        assert skills.weapon_mastery == 0.0

    def test_custom_values(self):
        skills = SkillSet(
            stealth=8.0,
            perception=10.0,
            weapon_mastery=7.0
        )
        assert skills.stealth == 8.0
        assert skills.perception == 10.0
        assert skills.weapon_mastery == 7.0

    def test_as_dict(self):
        skills = SkillSet(stealth=5.0, perception=3.0)
        d = skills.as_dict()
        assert isinstance(d, dict)
        assert d["stealth"] == 5.0
        assert d["perception"] == 3.0
        assert "acrobatics" in d


class TestPlayerProfile:
    """Tests for PlayerProfile dataclass."""

    def test_default_values(self):
        profile = PlayerProfile()
        assert isinstance(profile.offensive_power, OffensivePower)
        assert isinstance(profile.defensive_power, DefensivePower)
        assert isinstance(profile.skills, SkillSet)
        assert profile.inventory_summary == []
        assert profile.playstyle_indicators == {}

    def test_custom_profile(self):
        profile = PlayerProfile(
            offensive_power=OffensivePower(melee_strength=10.0),
            defensive_power=DefensivePower(physical_armor=8.0),
            skills=SkillSet(perception=7.0),
            inventory_summary=["sword", "potion"],
            playstyle_indicators={"aggressive": 0.9}
        )
        assert profile.offensive_power.melee_strength == 10.0
        assert profile.defensive_power.physical_armor == 8.0
        assert profile.inventory_summary == ["sword", "potion"]

    def test_summary_for_llm(self):
        profile = PlayerProfile(
            offensive_power=OffensivePower(melee_strength=10.0, fire_magic=5.0),
            defensive_power=DefensivePower(physical_armor=8.0, fire_resist=2.0),
            skills=SkillSet(perception=7.0, sneakiness=6.0, language=4.0),
            inventory_summary=["sword", "shield", "potion"],
            playstyle_indicators={"aggressive": 0.8, "cautious": 0.2}
        )
        summary = profile.summary_for_llm()
        assert "=== PLAYER PROFILE ===" in summary
        assert "Offensive:" in summary
        assert "Defensive:" in summary
        assert "Skills:" in summary
        assert "Playstyle:" in summary
        assert "Items:" in summary