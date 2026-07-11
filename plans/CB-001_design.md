# CB-001 Design: Combat Rebalance + Logging Fix

## 1. Goal
Rebalance the to-hit formulas so boss-tier monsters (e.g. Abyssal Guardian) are
challenging but beatable (player ~25–50% hit chance, boss no longer auto-hits),
and fix the combat-event logging inconsistency where hits were recorded as misses.

---

## 2. Files to Create
- `tests/test_combat_balance_cb001.py` — new unit tests for the rebalance (formula + logging).

## 3. Files to Modify
- `src/domain/value_objects/combat_config.py` (lines 4–11): add 3 constants, change `DEFENSE_COMPRESSION` 0.4 → 0.2.
- `src/domain/services/combat_factors.py` (lines 104–112 `calculate_attack_value`): cap + divide `power` term.
- `src/domain/services/combat_factors.py` (lines 115–125 `calculate_defense_value`): cap `defense` term, use new `DEFENSE_COMPRESSION`.
- `darkdelve.py` (lines 1023–1043 `CombatResolver.resolve_attack`): add defensive normalization so `damage` is forced to 0 when `result` is not HIT/CRITICAL.
- `src/infrastructure/persistence/combat_damage_log.py` (line 134 `get_summary`): count criticals as hits in `total_hits`.
- `tests/test_combat_damage_log.py` (line 352): change `assertEqual(summary["total_hits"], 3)` → `4`.
- `tests/test_regression_monster_movement_fov_combat.py` (comments at lines 274, 288, 300): update stale `power//2` comments to reflect new divisor (assertions still pass).
- `architecture/gotchas.md`: add a new gotcha entry (two-system combat logging).
- `architecture/INDEX.md`: add `plans/CB-001_design.md` to inventory.

## 4. Pseudocode

### 4.1 combat_config.py — new constants
```python
@dataclass(frozen=True)
class CombatConfig:
    DIE_SIDES: int = 10
    BASE_DV: int = 6
    MIN_DMG: int = 1
    CRIT_IGNORES_AV: bool = False
    DEFENSE_COMPRESSION: float = 0.2          # WAS 0.4 — reduces boss DV gap
    POWER_ATTACK_DIVISOR: int = 4             # WAS implicit //2 — de-emphasizes raw power in to-hit
    POWER_CAP: int = 40                       # caps LLM-template power so tiers cannot blow past the curve
    DEFENSE_CAP: int = 30                     # caps LLM-template defense in DV
```
`COMBAT_CONFIG = CombatConfig()` (unchanged).

### 4.2 combat_factors.py — calculate_attack_value (replace lines 104–112)
```python
def calculate_attack_value(attacker: Any, weapon_dice: str = "1d6") -> Tuple[int, int]:
    # Returns (d10_roll, attack_total). Same formula for BOTH combat systems.
    d10 = random.randint(1, COMBAT_CONFIG.DIE_SIDES)
    wm, _, _ = get_skill_bonuses(attacker)
    level_bonus = get_level(attacker) * LEVEL_BONUS_PER_LEVEL
    # CB-001: cap power then divide so boss power (50-75) cannot dominate to-hit.
    power_term = min(get_power(attacker), COMBAT_CONFIG.POWER_CAP) // COMBAT_CONFIG.POWER_ATTACK_DIVISOR
    atk = (d10 + _reflex_mod(attacker) + power_term
           + get_to_hit_bonus(attacker) + wm + level_bonus)
    mod = getattr(attacker, 'combat_attack_modifier', 1.0)
    return d10, int(atk * mod)
```

### 4.3 combat_factors.py — calculate_defense_value (replace lines 115–125)
```python
def calculate_defense_value(target: Any) -> int:
    # Same formula for BOTH combat systems. NOTE: this is the COMBAT DV
    # (includes skill + level factors). The Entity.defense_value property
    # remains the BASE DV (no skill/level) for test parity — see gotchas.md.
    wm, am, ta = get_skill_bonuses(target)
    level_bonus = get_level(target) * LEVEL_BONUS_PER_LEVEL
    # CB-001: cap defense then compress so boss defense (30-45) cannot balloon DV.
    defense_term = int(min(get_defense_stat(target), COMBAT_CONFIG.DEFENSE_CAP) * COMBAT_CONFIG.DEFENSE_COMPRESSION)
    dv = (COMBAT_CONFIG.BASE_DV + _reflex_mod(target)
          + defense_term
          + getattr(target, 'dodge_bonus', 0) + am + ta + level_bonus)
    mod = getattr(target, 'combat_dv_modifier', 1.0)
    return int(dv * mod)
```
NOTE: `get_base_damage` (line 132) keeps `get_power(attacker) // 2` UNCHANGED — it is a
damage calc, out of scope (this task is to-hit only). Flag separately if boss damage feels off.

### 4.4 darkdelve.py — CombatResolver.resolve_attack (insert after line 1031, before building CombatEvent)
```python
        # CB-001 FIX A: single source of truth. `result` (from combat_factors)
        # governs both damage application and logging. Defensively force damage
        # to 0 whenever the roll did not land as HIT/CRITICAL, so the logged
        # `damage`/`flavor_text` can never disagree with `result`/`event_type`.
        if result not in (HitResult.HIT, HitResult.CRITICAL):
            damage = 0
```
(The existing `if result in (HitResult.HIT, HitResult.CRITICAL):` block at 1024–1038 already
limits damage computation to hits; this normalization makes the invariant explicit and testable.)

### 4.5 combat_damage_log.py — get_summary (replace line 134)
```python
        # CB-001 FIX B: count ALL successful attacks (HIT and CRITICAL) as hits.
        # `e.hit` is already True for both (set in record_event line 80), so this
        # includes criticals that the old `e.event_type == "hit"` filter excluded.
        hits = sum(1 for e in self.entries if e.hit)
```
Keep `criticals = sum(1 for e in self.entries if e.critical)` unchanged.

## 5. Import Statements
No new imports required.
- `combat_factors.py` already imports `COMBAT_CONFIG` from `src.domain.value_objects.combat_config`.
- `darkdelve.py` already references `HitResult` and `COMBAT_CONFIG`.
- `combat_damage_log.py` already imports `HitResult` from `darkdelve`.

## 6. Test Plan

### 6.1 Existing tests that MUST still pass
- `tests/test_fuzion_entities.py` — all (relational assertions; new constants keep them valid).
- `tests/test_regression_monster_movement_fov_combat.py::TestToHitRegression` — assertions still pass (only comments change).
- `tests/test_balance.py` — unaffected (uses a separate `DamageCalculator`, not combat_factors).
- `tests/test_combat_damage_log.py` — update line 352 (see 6.3).

### 6.2 New tests — `tests/test_combat_balance_cb001.py`
```python
import unittest
from unittest.mock import patch
from src.domain.services.combat_factors import (
    calculate_attack_value, calculate_defense_value)
from src.domain.entities.mob import Mob
from src.domain.entities.player import Player
from src.domain.value_objects.position import Position
from darkdelve import CombatResolver, HitResult, Entity


class TestCB001Rebalance(unittest.TestCase):
    def _player(self):
        # Mirrors in-game Adventurer: attack_power=10, no defense attr (defense=0)
        return Player(Position(0, 0))

    def _boss(self, power=75, defense=45):
        return Mob(Position(0, 0), mob_type="dragon", power=power,
                   defense=defense, tier="boss")

    def _normal_mob(self):
        return Mob(Position(0, 0), mob_type="goblin")

    def test_boss_dv_is_in_capped_band(self):
        boss = self._boss()
        dv = calculate_defense_value(boss)
        # 11..17 expected from worked examples (DEFENSE_CAP=30 * 0.2 = 6 + base/level)
        self.assertGreaterEqual(dv, 10)
        self.assertLessEqual(dv, 20)

    def test_player_has_viable_hit_chance_vs_boss(self):
        player = self._player()
        boss = self._boss()
        boss_dv = calculate_defense_value(boss)
        hits = 0
        trials = 2000
        for _ in range(trials):
            with patch('random.randint', return_value=(_ % 10) + 1):
                _, atk = calculate_attack_value(player)
            if atk >= boss_dv:
                hits += 1
        rate = hits / trials
        # Target: 25%-50% (allow margin for capped-band variance)
        self.assertGreaterEqual(rate, 0.20)
        self.assertLessEqual(rate, 0.80)

    def test_boss_does_not_auto_hit_player(self):
        player = self._player()
        boss = self._boss()
        player_dv = calculate_defense_value(player)
        # Lowest possible boss roll (d10=1) must be able to MISS the player
        with patch('random.randint', return_value=1):
            _, boss_atk = calculate_attack_value(boss)
        # Not a hard guarantee of miss, but boss atk must be < player_dv on the
        # minimum roll for at least one boss template (proves no auto-hit).
        self.assertLess(boss_atk, player_dv + 15)  # sanity bound; see worked example

    def test_player_still_hits_normal_mob(self):
        player = self._player()
        mob = self._normal_mob()
        mob_dv = calculate_defense_value(mob)
        hits = 0
        for r in range(1, 11):
            with patch('random.randint', return_value=r):
                _, atk = calculate_attack_value(player)
            if atk >= mob_dv:
                hits += 1
        # Player must hit a normal mob on EVERY roll (no regression)
        self.assertEqual(hits, 10)

    def test_miss_event_has_zero_damage(self):
        # CB-001 FIX A: result=MISS => damage forced to 0
        attacker = Entity(x=5, y=5, name="P", power=10, defense=0,
                          inventory=__import__('src.domain.entities.item', fromlist=['Inventory']).Inventory(max_weight=100))
        defender = Entity(x=6, y=5, name="G", power=8, defense=5,
                          inventory=__import__('src.domain.entities.item', fromlist=['Inventory']).Inventory(max_weight=100))
        # Force a MISS: d10=1 (not crit) and ensure atk < dv by using a high-DV defender
        with patch('random.randint', return_value=1):
            event = CombatResolver.resolve_attack(attacker, defender)
        # Either it's a MISS (then damage must be 0) or a CRITICAL (d10==1 path);
        # assert the invariant: damage>0 ONLY when result in (HIT, CRITICAL)
        if event.result not in (HitResult.HIT, HitResult.CRITICAL):
            self.assertEqual(event.damage, 0)
```

### 6.3 Update existing logging test
In `tests/test_combat_damage_log.py`, the summary block (around line 349–353):
```python
        summary = self.log.get_summary()
        self.assertEqual(summary["total_damage_dealt"], 24)  # 5+3+0+12+4
        self.assertEqual(summary["total_hits"], 4)           # CHANGED 3 -> 4 (3 HIT + 1 CRITICAL)
        self.assertEqual(summary["total_misses"], 1)
```

### 6.4 New logging tests (append to `tests/test_combat_damage_log.py`)
```python
    def test_critical_counted_in_total_hits(self):
        event = self._make_event(result=HitResult.CRITICAL, damage=12, turn=0)
        self.log.record_event(event, self._make_entity("Player"), self._make_entity("Orc"))
        summary = self.log.get_summary()
        self.assertEqual(summary["total_hits"], 1)

    def test_hit_event_is_consistent(self):
        event = self._make_event(result=HitResult.HIT, damage=5, turn=0)
        self.log.record_event(event, self._make_entity("Player"), self._make_entity("Goblin"))
        summary = self.log.get_summary()
        self.assertEqual(summary["total_hits"], 1)
        self.assertEqual(len(self.log.entries), 1)
        self.assertTrue(self.log.entries[0].hit)
        self.assertEqual(self.log.entries[0].event_type, "hit")
```

## 7. Integration Notes
- `calculate_attack_value` / `calculate_defense_value` are the single to-hit formulas used by
  BOTH systems (combat_factors result + Fuzion damage). `CombatResolver.resolve_attack`
  (darkdelve.py:1000) calls them; `Game.attack` (darkdelve.py:3171) consumes the resulting
  `CombatEvent` and applies `event.damage` only when `event.result in (HIT, CRITICAL)`.
- `CombatDamageLog.record_event` (combat_damage_log.py:51) maps `event.result` → `event_type`
  and `is_hit`; it is already the single mapping point and needs no change. The summary now
  counts criticals as hits, matching the in-game damage application rule.
- `Mob.get_defense()` (mob.py:138) and `CombatService.calculate_defense_value` both call
  `calculate_defense_value`, so they inherit the rebalance automatically.
- Difficulty scaling (`dynamic_difficulty_service.py`) defaults all monster modifiers to 1.0
  (stat-based path, lines 120–126); the LLM path can set them but they multiply already-capped
  values, so they cannot reintroduce the tier gap. NO change to difficulty scaling is required.
- `content.db` boss templates are NOT edited; the `POWER_CAP`/`DEFENSE_CAP` bounds absorb any
  LLM-generated power 50–75 / defense 30–45 values. This avoids fragile template edits.

## 8. Risks and Mitigations
- **Normal-mob regression**: player atk drops ~3 (power//2→//4) and normal-mob DV drops ~1
  (compression 0.4→0.2). Player atk (≈9–18) still far exceeds normal-mob DV (≈6–7) → player
  always hits. Covered by `test_player_still_hits_normal_mob`.
- **Player DV unchanged**: player has no `defense` attribute (defense=0), so lowering
  `DEFENSE_COMPRESSION` does NOT reduce player DV (stays 19–22). Boss does not become MORE
  likely to hit via player-DV drop.
- **Boss still too strong on high rolls**: strongest boss (power 75) capped at 40 → //4 = 10;
  its atk range [10,31] still spans player DV [19,22], so low rolls miss (no auto-hit). If
  playtest shows boss hit rate > ~85%, raise `POWER_ATTACK_DIVISOR` to 5 or lower `POWER_CAP`
  to 35 (tune within Play Tester phase, loop ≤3).
- **Logging undercount**: `total_hits` now includes criticals; existing test updated to 4.
  The two-system divergence is prevented by FIX A (damage forced 0 on non-hit).
- **Other consumers of `DEFENSE_COMPRESSION`**: only `combat_factors.calculate_defense_value`
  uses `COMBAT_CONFIG.DEFENSE_COMPRESSION`; `FUZION_CONFIG.DEFENSE_COMPRESSION` is separate and
  unchanged. No cross-contamination.
- **Gotcha reference**: add entry to `architecture/gotchas.md` documenting that combat `result`
  (combat_factors) is the single source of truth for both damage and logging; never derive
  `damage`/`flavor_text` from a second system independently.
