"""Tests for Hero-System RPG damage model."""
import pytest
from src.domain.value_objects.damage_model import (
    DamageInstance, DamageResult, ResistanceProfile, DamageCalculator
)


class TestDamageInstance:
    """Tests for DamageInstance dataclass."""

    def test_damage_instance_creation(self):
        """Test creating a damage instance."""
        instance = DamageInstance(
            raw_damage=20.0,
            damage_type="fire",
            source_id="player_1",
            target_id="goblin_1"
        )
        assert instance.raw_damage == 20.0
        assert instance.damage_type == "fire"
        assert instance.is_critical is False
        assert instance.is_blocked is False
        assert instance.is_dodged is False


class TestDamageResult:
    """Tests for DamageResult dataclass."""

    def test_damage_result_creation(self):
        """Test creating a damage result."""
        result = DamageResult(
            final_damage=15.0,
            was_blocked=False,
            was_dodged=False,
            was_critical=True,
            overkill=5.0,
            resistance_applied=5.0,
            resistance_type="fire"
        )
        assert result.final_damage == 15.0
        assert result.was_critical is True
        assert result.target_died is False


class TestResistanceProfile:
    """Tests for ResistanceProfile dataclass."""

    def test_default_resistance(self):
        """Test default resistance is 0."""
        profile = ResistanceProfile()
        assert profile.get_resistance("fire") == 0.0

    def test_set_resistance(self):
        """Test setting resistance."""
        profile = ResistanceProfile()
        profile.set_resistance("fire", 0.5)
        assert profile.get_resistance("fire") == 0.5

    def test_resistance_clamped(self):
        """Test resistance values are clamped to 0-1."""
        profile = ResistanceProfile()
        profile.set_resistance("fire", 1.5)
        assert profile.get_resistance("fire") == 1.0
        profile.set_resistance("ice", -0.2)
        assert profile.get_resistance("ice") == 0.0


class TestDamageCalculator:
    """Tests for DamageCalculator class."""

    def test_calculate_damage_basic(self):
        """Test basic damage calculation."""
        calc = DamageCalculator()
        result = calc.calculate_damage(
            attacker_power=20.0,
            damage_type="physical",
            defender_resistance=0.0,
            defender_armor=5.0
        )
        assert result.final_damage == 15.0
        assert result.was_blocked is False

    def test_calculate_damage_with_resistance(self):
        """Test damage calculation with resistance."""
        calc = DamageCalculator()
        result = calc.calculate_damage(
            attacker_power=20.0,
            damage_type="fire",
            defender_resistance=0.5,
            defender_armor=0.0
        )
        assert result.final_damage == 10.0
        assert result.resistance_applied == 10.0

    def test_calculate_damage_critical(self):
        """Test critical hit damage."""
        calc = DamageCalculator()
        result = calc.calculate_damage(
            attacker_power=20.0,
            damage_type="physical",
            defender_resistance=0.0,
            defender_armor=0.0,
            is_critical=True,
            critical_multiplier=1.5
        )
        assert result.final_damage == 30.0
        assert result.was_critical is True

    def test_calculate_damage_minimum(self):
        """Test that damage has minimum of 1."""
        calc = DamageCalculator()
        result = calc.calculate_damage(
            attacker_power=5.0,
            damage_type="physical",
            defender_resistance=0.0,
            defender_armor=10.0
        )
        assert result.final_damage == 1.0

    def test_calculate_with_block(self):
        """Test block reduction."""
        calc = DamageCalculator()
        result = DamageResult(
            final_damage=20.0, was_blocked=False, was_dodged=False,
            was_critical=False, overkill=0.0, resistance_applied=0.0,
            resistance_type="physical"
        )
        result = calc.calculate_with_block(result, block_chance=1.0, block_value=10.0)
        assert result.final_damage == 10.0
        assert result.was_blocked is True

    def test_calculate_with_dodge(self):
        """Test dodge chance."""
        calc = DamageCalculator()
        result = DamageResult(
            final_damage=20.0, was_blocked=False, was_dodged=False,
            was_critical=False, overkill=0.0, resistance_applied=0.0,
            resistance_type="physical"
        )
        result = calc.calculate_with_dodge(result, dodge_chance=1.0)
        assert result.final_damage == 0
        assert result.was_dodged is True