"""Tests for turn order and energy-based actor selection."""

from darkdelve import EnergySystem, Entity


def test_player_starts_before_faster_adjacent_enemy():
    player = Entity(name="Player", speed=100, hp=23, max_hp=23)
    fast_scout = Entity(name="Fast Scout", speed=120, hp=5, max_hp=5)

    energy_system = EnergySystem()
    energy_system.add_entity(player, initial_energy=100)
    energy_system.add_entity(fast_scout, initial_energy=0)

    assert energy_system.next_actor() is player
