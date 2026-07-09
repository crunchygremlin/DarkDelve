# FUZION-AC-001 Implementation Design (Detailed Plan) — REVISED

- **Task ID:** FUZION-AC-001
- **Mode:** Architect (DESIGN ONLY — no source changes in this step)
- **Date:** 2026-07-09 (revised pass)
- **Status:** Revised to resolve 6 blocking defects + should-fix items flagged by Orchestrator re-eval.
- **Source concept doc:** `plans/FUZION-AC-001_design.md`

---

## 1. Goal

Replace DarkDelve's broken `d20 + (10 + defense + equipment)` Armor‑Class system with a Fuzion‑inspired, `d10`‑based **Attack Value (AV_atk) vs Defense Value (DV_def)** model plus a separate **Armor Value (AV_armor)** damage‑absorption layer, implemented IDENTICALLY in both `darkdelve.py` `CombatResolver` and `src/domain/services/combat_service.py` so the two combat systems no longer diverge.

**Approved defaults (from `plans/FUZION-AC-001_design.md` §10):**
1. **TN model** (not opposed rolls): `atk = d10 + reflex_mod + power//2 + to_hit_bonus` vs `DV = BASE_DV + reflex_mod + int(defense*0.4) + dodge_bonus`.
2. **Critical does NOT ignore Armor Value** (`CRIT_IGNORES_AV = False`).
3. **MIN_DMG = 1** (always at least 1 chip damage).
4. **BASE_DV = 6** (gives ~50% hit for equal foes).
5. **Defense compression `defense * 0.4`** approved.
6. **Keep deprecated `armor_class` AND `target_ac`/`d20_roll` aliases** for one release to limit test churn (this revision makes that explicit and mandatory).

---

## 2. Files to Create

| Path | Purpose |
|------|---------|
| `src/domain/value_objects/combat_config.py` | Central tuning constants: `BASE_DV=6`, `MIN_DMG=1`, `CRIT_IGNORES_AV=False`, `DIE_SIDES=10`, `DEFENSE_COMPRESSION=0.4`. |
| `src/shared/utils/dice.py` | `parse_dice(weapon_dice) -> (num, size, mod)` helper shared by BOTH combat implementations (avoids circular import; `combat_service.py` must NOT import `darkdelve`). |
| `tests/test_fuzion_combat.py` | Unit tests for new to‑hit/DV math, damage clamping order, and legacy alias coexistence. |

---

## 3. Files to Modify

> **IMPORTANT — TWO `CombatEvent` classes (defect #7):** There are TWO different `CombatEvent` classes.
> - **(A)** `darkdelve.py` dataclass (fields: `turn, attacker_name, defender_name, to_hit_bonus, target_ac, d20_roll, total_roll, result, damage, flavor_text, out_of_range`). **This is the ONLY one modified by this plan.**
> - **(B)** `src/domain/value_objects/combat_event.py` (fields: `event_type, source_id, target_id, damage, message, ...`) used by `CombatService`. **NOT modified, NOT in scope.** Do not confuse them; the `target_ac`→`target_dv` rename applies ONLY to (A).
>
> **The 4 existing test suites below MUST still pass UNCHANGED (defect #1):** `tests/test_combat_system.py`, `tests/test_combat_messages.py`, `tests/test_combat_damage_log.py`, `tests/test_regression_monster_movement_fov_combat.py`. They construct `darkdelve.CombatEvent` with `target_ac=`/`d20_roll=` kwargs, so those names MUST remain REAL dataclass fields this release.

| Path | Lines (verified) | Change |
|------|------------------|--------|
| `darkdelve.py` | 793‑795 (`Entity.armor_class`) | Add `defense_value` property; keep `armor_class` as deprecated alias returning `defense_value`. |
| `darkdelve.py` | 801‑803 (`Entity.to_hit_bonus`) | Unchanged (still weapon `to_hit_bonus`). |
| `darkdelve.py` | 635‑636 (`Inventory.get_defense_bonus`) | Document as **Armor Value** source; add `get_armor_value()` alias returning same value. (`get_damage_bonus` 638, `get_to_hit_bonus` 642 nearby, unchanged.) |
| `darkdelve.py` | 359‑426 (`CombatEvent` dataclass & `__str__`) | **Keep `target_ac` and `d20_roll` as REAL fields (defaults 0). ADD `target_dv` and `d10_roll` as REAL fields (defaults 0).** Update `__str__` roll text to show `DV {target_dv}`. |
| `darkdelve.py` | 964‑1046 (`CombatResolver.resolve_attack`) | Rewrite per §4.3 (d10, DV, AV, `parse_dice`). Populate BOTH old and new roll fields for alias parity. |
| `darkdelve.py` | 2046‑2047 (UI status line) | Change `AC {armor_class}` → `DV {defense_value} AV {armor_value}`. |
| `darkdelve.py` | 3582 (debug panel) | Same as above (approximate line). |
| `darkdelve.py` | 391 (`CombatEvent.__str__` roll text) | Change `vs AC {self.target_ac}` → `vs DV {self.target_dv}`. |
| `darkdelve.py` | 646 (`MobTemplate` dataclass) | Add `armor_value: int = 0` field. (NOTE: line 1414 is a `create_default_roster()` *call* that instantiates `MobTemplate`, NOT the class definition.) |
| `src/domain/services/combat_service.py` | 171‑251 (4 methods) | Rewrite per §4.4: `calculate_attack_roll`, `calculate_defense_value` (RENAMED from `calculate_defense_roll`), `calculate_damage` (adds `weapon_dice`), `is_critical_hit` (KEEP `attacker` param). Add module‑level `_reflex_mod` helper. |
| `src/domain/services/combat_service.py` | 83‑97 (`execute_attack` orchestration) | Rewrite per §4.4 orchestration: call renamed `calculate_defense_value`, use `>=` (not `>`), pass `weapon_dice` to `calculate_damage`, crit from same d10. Add `weapon_dice: str = "1d6"` param to `execute_attack`. |
| `src/domain/value_objects/stats.py` | ~62‑65 (`get_armor_class`) | Add `get_defense_value()` using `BASE_DV + dex_mod + int(defense*0.4)`; keep `get_armor_class` alias. (approximate line) |
| `src/domain/entities/item.py` | 26‑28 (`attack_bonus`, `defense_bonus`, `health_bonus`) | `defense_bonus` documented as Armor Value; add `armor_value` property returning `defense_bonus`. |
| `src/domain/components/combat.py` | 142‑150 (`get_bonus_defense`) | Rename to `get_armor_value()` (keep `get_bonus_defense` as alias) returning sum of `defense_bonus`. |
| `architecture/INDEX.md` | inventory section | Add `combat_config.py` and `src/shared/utils/dice.py`; note combat overhaul. |
| `architecture/gotchas.md` | add entry | "Fuzion AC clamp order: clamp AFTER crit & AV subtraction, BEFORE CombatEvent". |

---

## 4. Pseudocode

### 4.1 `src/domain/value_objects/combat_config.py`
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class CombatConfig:
    DIE_SIDES: int = 10
    BASE_DV: int = 6
    MIN_DMG: int = 1
    CRIT_IGNORES_AV: bool = False
    DEFENSE_COMPRESSION: float = 0.4

COMBAT_CONFIG = CombatConfig()
```

### 4.1b `src/shared/utils/dice.py`  (NEW — defect #6)
```python
import re
from typing import Tuple

def parse_dice(weapon_dice: str) -> Tuple[int, int, int]:
    # Parse "NdS+M" / "NdS" / "N" / "NdS-M" into (num, size, mod).
    # Returns (num_dice, dice_size, flat_modifier).
    s = (weapon_dice or "1d6").strip().lower()
    m = re.fullmatch(r"(\d+)\s*d\s*(\d+)\s*([+-]\s*\d+)?", s)
    if not m:
        try:
            return 0, 0, int(s)          # bare flat number -> modifier only
        except ValueError:
            return 1, 6, 0               # ultimate fallback
    num = int(m.group(1))
    size = int(m.group(2))
    mod = int(m.group(3).replace(" ", "")) if m.group(3) else 0
    return num, size, mod
```

### 4.2 `Entity.defense_value` property (darkdelve.py ~793)
```python
@property
def defense_value(self) -> int:
    from src.domain.value_objects.combat_config import COMBAT_CONFIG
    stats = getattr(self, 'stats', None)
    if stats is None:
        reflex = 0
    elif hasattr(stats, 'get_modifier'):           # Stats object (defect #8 defensive)
        reflex = stats.get_modifier('dexterity')
    else:                                          # dict-like stats (tests)
        reflex = (stats.get('dex', 10) - 10) // 2
    comp_def = int(self.defense * COMBAT_CONFIG.DEFENSE_COMPRESSION)
    dodge = getattr(self, 'dodge_bonus', 0)
    return COMBAT_CONFIG.BASE_DV + reflex + comp_def + dodge

@property
def armor_class(self) -> int:
    # DEPRECATED alias – remove after one release
    return self.defense_value

@property
def armor_value(self) -> int:
    if self.inventory:
        return self.inventory.get_defense_bonus()
    return 0
```

### 4.3 `CombatResolver.resolve_attack` (darkdelve.py ~964)
```python
@staticmethod
def resolve_attack(attacker, defender, weapon_dice="1d6", max_range=1) -> CombatEvent:
    from src.domain.value_objects.combat_config import COMBAT_CONFIG
    from src.shared.utils.dice import parse_dice
    distance = abs(attacker.x - defender.x) + abs(attacker.y - defender.y)
    if distance > max_range:
        return CombatEvent(turn=0, attacker_name=attacker.name, defender_name=defender.name,
                           to_hit_bonus=attacker.to_hit_bonus,
                           target_ac=defender.defense_value, target_dv=defender.defense_value,
                           d20_roll=0, d10_roll=0, total_roll=0,
                           result=HitResult.MISS, damage=0, out_of_range=True)
    d10 = random.randint(1, COMBAT_CONFIG.DIE_SIDES)
    # Defensive reflex (mirrors existing resolve_attack @ darkdelve.py:992)
    stats = getattr(attacker, 'stats', None)
    if stats is None:
        reflex_atk = 0
    elif hasattr(stats, 'get_modifier'):
        reflex_atk = stats.get_modifier('dexterity')
    else:
        reflex_atk = (stats.get('dex', 10) - 10) // 2
    base = attacker.power // 2
    atk_total = d10 + reflex_atk + base + attacker.to_hit_bonus
    dv = defender.defense_value
    if d10 == COMBAT_CONFIG.DIE_SIDES:
        result = HitResult.CRITICAL
    elif d10 == 1:
        result = HitResult.CRITICAL_FAIL
    elif atk_total >= dv:                      # >= matches darkdelve original (line 1005)
        result = HitResult.HIT
    else:
        result = HitResult.MISS
    damage = 0
    if result in (HitResult.HIT, HitResult.CRITICAL):
        num, size, mod = parse_dice(weapon_dice)
        damage = sum(random.randint(1, size) for _ in range(num)) + mod + (attacker.power // 2) + attacker.damage_bonus
        if result == HitResult.CRITICAL:
            damage *= 2
        av = defender.armor_value
        if result == HitResult.CRITICAL and COMBAT_CONFIG.CRIT_IGNORES_AV:
            av = 0
        damage = max(COMBAT_CONFIG.MIN_DMG, damage - av)
        if hasattr(defender, 'max_hp') and defender.max_hp > 0:
            defender_is_player = getattr(defender, 'inventory', None) is not None and hasattr(defender, 'xp')
            attacker_is_player = getattr(attacker, 'inventory', None) is not None and hasattr(attacker, 'xp')
            if defender_is_player:
                damage = clamp_monster_damage(damage, defender.max_hp)
            elif attacker_is_player:
                damage = clamp_player_damage(damage, defender.max_hp)
    return CombatEvent(turn=0, attacker_name=attacker.name, defender_name=defender.name,
                       to_hit_bonus=attacker.to_hit_bonus,
                       target_ac=dv, target_dv=dv,            # both populated for alias parity
                       d20_roll=d10, d10_roll=d10,
                       total_roll=atk_total, result=result, damage=damage)
```

### 4.4 `src/domain/services/combat_service.py` (parallel rewrite — ALIGNED math)

**Module-level helper (add near top of file, after imports):**
```python
def _reflex_mod(entity) -> int:
    stats = getattr(entity, 'stats', None)
    if stats is None:
        return 0
    if hasattr(stats, 'get_modifier'):
        return stats.get_modifier('dexterity')
    return (stats.get('dex', 10) - 10) // 2
```

**Method rewrites (replace lines 171‑251 bodies):**
```python
def calculate_attack_roll(self, attacker) -> int:
    from src.domain.value_objects.combat_config import COMBAT_CONFIG
    d10 = random.randint(1, COMBAT_CONFIG.DIE_SIDES)
    self._last_d10 = d10                      # stored so crit uses the SAME d10
    base = getattr(attacker, 'attack_power', getattr(attacker, 'power', 0)) // 2
    return d10 + _reflex_mod(attacker) + base + attacker.get_equipped_attack_bonus()

def calculate_defense_value(self, target) -> int:   # RENAMED from calculate_defense_roll
    from src.domain.value_objects.combat_config import COMBAT_CONFIG
    comp_def = int(target.defense * COMBAT_CONFIG.DEFENSE_COMPRESSION)
    return COMBAT_CONFIG.BASE_DV + _reflex_mod(target) + comp_def + getattr(target, 'dodge_bonus', 0)

def calculate_damage(self, attacker, target, weapon_dice: str = "1d6") -> int:
    from src.domain.value_objects.combat_config import COMBAT_CONFIG
    from src.shared.utils.dice import parse_dice
    num, size, mod = parse_dice(weapon_dice)
    base = sum(random.randint(1, size) for _ in range(num)) + mod
    base += getattr(attacker, 'attack_power', getattr(attacker, 'power', 0)) // 2
    base += attacker.get_equipped_damage_bonus()
    av = target.get_equipped_defense_bonus()        # Armor Value
    return max(COMBAT_CONFIG.MIN_DMG, base - av)    # NOTE: no crit doubling here

def is_critical_hit(self, attacker) -> bool:        # KEEP attacker param (caller @ :95 unchanged)
    from src.domain.value_objects.combat_config import COMBAT_CONFIG
    return getattr(self, '_last_d10', 0) == COMBAT_CONFIG.DIE_SIDES
```

**Orchestration rewrite (replace `execute_attack` body lines 83‑97):**
```python
# Calculate attack roll (stores self._last_d10 for the crit check)
attack_roll = self.calculate_attack_roll(attacker)
# Calculate DEFENSE VALUE (renamed from calculate_defense_roll; update caller @ :85)
defense_value = self.calculate_defense_value(target)
# Hit test: use >= to match darkdelve.resolve_attack (was >)
hit = attack_roll >= defense_value
if hit:
    # Damage (weapon dice parsed inside; crit doubling done below)
    damage = self.calculate_damage(attacker, target, weapon_dice)
    # Critical determined from the SAME d10 used for the attack roll (caller unchanged)
    critical = self.is_critical_hit(attacker)
    if critical:
        damage *= 2
    target.health -= damage
    # ... remainder of existing HIT branch (event creation, defeat check, return) unchanged ...
else:
    # ... existing MISS branch unchanged ...
```
Also change `execute_attack` signature to: `def execute_attack(self, attacker: Player, target: Mob, weapon_dice: str = "1d6") -> Dict[str, Any]:` (default keeps existing callers working).

### 4.5 `CombatEvent` field handling (darkdelve.py ~359) — defect #1 fix
```python
@dataclass
class CombatEvent:
    turn: int = 0
    attacker_name: str = ""
    defender_name: str = ""
    to_hit_bonus: int = 0
    target_ac: int = 0          # DEPRECATED alias field — KEPT AS REAL FIELD this release
    d20_roll: int = 0           # DEPRECATED alias field — KEPT AS REAL FIELD this release
    total_roll: int = 0
    result: HitResult = HitResult.MISS
    target_dv: int = 0          # NEW field
    d10_roll: int = 0           # NEW field
    damage: int = 0
    flavor_text: str = ""
    out_of_range: bool = False
```
- **All fields have defaults** so the 4 existing suites (which pass `target_ac`/`d20_roll` and omit `target_dv`/`d10_roll`) construct successfully.
- `target_ac`/`d20_roll` are REAL fields (NOT properties) — this is mandatory so the 4 existing test constructors do not raise `TypeError`.
- `__str__` roll text (line 391) becomes: `roll_text = f"[Roll: {self.total_roll} vs DV {self.target_dv}]"`.

---

## 5. Import Statements

```python
# In darkdelve.py (top, with other src imports)
from src.domain.value_objects.combat_config import COMBAT_CONFIG
from src.shared.utils.dice import parse_dice

# In src/domain/services/combat_service.py
from src.domain.value_objects.combat_config import COMBAT_CONFIG
from src.shared.utils.dice import parse_dice

# In src/domain/value_objects/stats.py
from src.domain.value_objects.combat_config import COMBAT_CONFIG

# In tests/test_fuzion_combat.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.domain.value_objects.combat_config import COMBAT_CONFIG, CombatConfig
from src.shared.utils.dice import parse_dice
from darkdelve import Entity, Inventory, Item, ItemType, CombatResolver, HitResult, CombatEvent
```

---

## 6. Test Plan

`tests/test_fuzion_combat.py` (exact assertions):

```python
import unittest
from unittest.mock import Mock
from src.domain.value_objects.combat_config import COMBAT_CONFIG
from src.shared.utils.dice import parse_dice
from darkdelve import Entity, Inventory, Item, ItemType, CombatResolver, HitResult, CombatEvent

class TestFuzionCombat(unittest.TestCase):
    def make_player(self, dex=10, power=6, def_bonus=0, to_hit=0):
        # Item constructor signature: Item(item_id, name, item_type, symbol="?", weight=1, value=0, damage_bonus=0, defense_bonus=0, to_hit_bonus=0, ...)
        # => Item("w","wpn",ItemType.WEAPON) sets item_id="w", name="wpn", item_type=ItemType.WEAPON (valid, 3 positional args)
        e = Entity()
        e.stats = {'str':10,'dex':dex,'con':10,'int':10,'wis':10,'cha':10}
        e.power = power
        e.defense = 2
        e.inventory = Inventory()
        if def_bonus or to_hit:
            w = Item("w","wpn",ItemType.WEAPON); w.to_hit_bonus=to_hit; w.defense_bonus=def_bonus
            e.inventory.add_item(w); e.inventory.equip(w.id, __import__('darkdelve').EquipmentSlot.MAIN_HAND)
        return e

    def test_defense_value_baseline(self):
        p = self.make_player(dex=10, power=6)
        self.assertEqual(p.defense_value, 6)
        self.assertEqual(p.armor_class, 6)

    def test_armor_value_from_equipment(self):
        p = self.make_player(def_bonus=5)
        self.assertEqual(p.armor_value, 5)

    def test_hit_probability_range(self):
        atk = self.make_player(dex=14, power=6, to_hit=2)
        dfn = self.make_player(dex=8, defense=2)
        for _ in range(20):
            ev = CombatResolver.resolve_attack(atk, dfn)
            self.assertIn(ev.result, (HitResult.HIT, HitResult.CRITICAL))

    def test_ac_41_foe_now_hittable(self):
        foe = self.make_player(dex=10, power=6, def_bonus=25)
        foe.defense = 6
        player = self.make_player(dex=14, power=6, to_hit=2)
        hits = 0
        for _ in range(100):
            ev = CombatResolver.resolve_attack(player, foe)
            if ev.result in (HitResult.HIT, HitResult.CRITICAL): hits += 1
        self.assertGreater(hits, 80)

    def test_damage_absorbs_av(self):
        atk = self.make_player(power=10)
        dfn = self.make_player(def_bonus=25)
        ev = CombatResolver.resolve_attack(atk, dfn, weapon_dice="5d6")
        self.assertGreaterEqual(ev.damage, COMBAT_CONFIG.MIN_DMG)

    def test_combat_event_renamed_fields(self):
        # Defect #1: old names remain REAL fields, so populate BOTH pairs and assert equality.
        ev = CombatEvent(target_ac=5, d20_roll=3, target_dv=5, d10_roll=3)
        self.assertEqual(ev.target_ac, 5)
        self.assertEqual(ev.d20_roll, 3)
        self.assertEqual(ev.target_dv, 5)
        self.assertEqual(ev.d10_roll, 3)

    def test_parse_dice(self):
        self.assertEqual(parse_dice("2d6+3"), (2, 6, 3))
        self.assertEqual(parse_dice("1d10"), (1, 10, 0))
        self.assertEqual(parse_dice("4"), (0, 0, 4))

if __name__ == '__main__':
    unittest.main()
```

Run: `python -m pytest tests/test_fuzion_combat.py -v`

**Regression guarantee (CORRECTED — design defect fixed):** The 4 existing suites (`test_combat_system.py`, `test_combat_messages.py`, `test_combat_damage_log.py`, `test_regression_monster_movement_fov_combat.py`) CANNOT pass UNCHANGED. They encode d20-specific assertions (critical at roll 20, `armor_class > 12`, and a MISS premise that is impossible under the d10 system). The Coder is **AUTHORIZED** to apply the precise legacy-test edits enumerated in §6.1 as part of implementation. After those 6 edits, all 4 suites pass. `tests/test_combat_system.py::test_resolve_attack_basic` (asserts `event.d20_roll` between 1 and 20) STILL PASSES unchanged because `d20_roll` is now populated with the d10 value (1–10 ≤ 20). `test_combat_messages.py`, `test_combat_damage_log.py`, and the out_of_range / HIT-or-CRITICAL regression tests need NO changes (they construct `CombatEvent` with the still-real `target_ac`/`d20_roll` fields or accept HIT/CRITICAL).


### 6.1 Required legacy-test updates (Coder is authorized to apply these exact edits)

The following 6 edits are REQUIRED for the 4 legacy suites to pass under the d10 system. Apply verbatim.

**a. `tests/test_combat_system.py` — `test_critical_hits` (line 87):**
- Change `patch('random.randint', return_value=20)` → `patch('random.randint', return_value=10)`
- Change comment `"Force a critical hit by mocking d20 roll"` → `"Force a critical hit by mocking d10 roll (natural 10 = critical in d10 system)"`
- Assertion `self.assertEqual(event.result, HitResult.CRITICAL)` then holds because d10==10.

**b. `tests/test_combat_system.py` — `test_combat_critical_hits` (line 243):**
- Change `patch('random.randint', return_value=20)` → `patch('random.randint', return_value=10)`
- Change comment `"Force a critical hit by mocking d20 roll"` → `"Force a critical hit by mocking d10 roll (natural 10 = critical in d10 system)"`

**c. `tests/test_combat_system.py` — `test_combat_misses` (lines 248-254):**
- Inside this test only, set `self.enemy.defense = 10` (dv becomes `6 + int(10*0.4) = 4` → 10).
- Change mock `patch('random.randint', return_value=5)` → `patch('random.randint', return_value=2)` (d10=2 → atk_total = 2+0+5+0 = 7 < 10 → MISS, and d10≠1 so not crit-fail).
- Update comment `"Force a miss by mocking low d20 roll"` → `"Force a miss: low non-1 d10 vs raised defender DV=10"`.
- Keep assertions `assertEqual(event.result, HitResult.MISS)` and `assertEqual(event.damage, 0)`.
- Do NOT change `self.enemy.defense` in `setUp` — only inside this one test, to avoid affecting sibling tests.

**d. `tests/test_combat_system.py` — `test_player_has_starting_gear_equipped` (lines 512-514):**
- Replace `self.assertGreater(player.armor_class, 12, "Player AC too low - starting armor not equipped")` with `self.assertGreater(player.armor_value, 0, "Player armor_value too low - starting armor not equipped")`.
- Rationale: in the new model, equipped armor contributes to Armor Value (AV), not the DV directly; `armor_value > 0` correctly verifies starting armor is equipped.
- Keep the `damage_bonus` and `to_hit_bonus` assertions unchanged.

**e. `tests/test_regression_monster_movement_fov_combat.py` — `test_weak_attacker_can_still_hit` (line 311, assertion at 315):**
- Change `patch('random.randint', return_value=20)` → `return_value=10`.
- Change comment `"Roll 20 (natural 20) always hits"` → `"Roll 10 (natural 10) is critical in d10 system"`.
- Assertion `self.assertEqual(event.result, HitResult.CRITICAL)` then holds.

**f. `tests/test_regression_monster_movement_fov_combat.py` — `test_to_hit_with_no_power_attribute` (line 332, assertion at 336):**
- Change `patch('random.randint', return_value=20)` → `return_value=10`.
- Change comment `"Roll 20 should still hit (natural 20 always hits)"` → `"Roll 10 (natural 10) is critical in d10 system"`.

**No-change tests (do NOT edit):**
- `tests/test_combat_system.py::test_resolve_attack_basic` (asserts `event.d20_roll` between 1 and 20) — passes unchanged.
- `tests/test_combat_messages.py`, `tests/test_combat_damage_log.py` — no changes.
- `test_regression_monster_movement_fov_combat.py` out_of_range / HIT-or-CRITICAL tests — no changes.


---

## 7. Integration Notes

- **Two `CombatEvent` classes (defect #7):** Only `darkdelve.CombatEvent` is touched. `src/domain/value_objects/combat_event.py` (used by `CombatService`) is out of scope and unchanged.
- **`CombatResolver.resolve_attack`** is called by the game loop in `darkdelve.py` (search `resolve_attack`). New signature identical; callers see `target_dv` in logs. Both old and new roll fields are populated for one-release display parity.
- **`combat_service.py`** used by agent/LLM systems. Rewritten to the SAME formula as `darkdelve` (single d10 vs DV, crit = d10==10, `>=`, weapon dice via `parse_dice`, AV subtracted). `calculate_defense_roll` is RENAMED to `calculate_defense_value` and the caller at `combat_service.py:85` is updated. `is_critical_hit(attacker)` keeps its signature; only its caller at `:95` is preserved.
- **`parse_dice`** lives in `src/shared/utils/dice.py` (new) so both modules import it without a `combat_service`→`darkdelve` circular import.
- UI surfaces (`render_ui` status line ~2047, debug panel ~3582) read `armor_class`; they will now show `DV`/`AV`. Update strings as listed.
- `clamp_monster_damage` / `clamp_player_damage` calls remain **after** AV subtraction and crit, preserving `architecture/gotchas.md` "Damage Cap Clamping Order".
- `MobTemplate` (`darkdelve.py:646` — class def; line 1414 is a roster *usage*) gains `armor_value: int = 0` so monsters can have AV without equipment.
- **Attribute mapping (math parity):** darkdelve `power` ↔ combat_service `attack_power`; darkdelve `damage_bonus`/`to_hit_bonus` ↔ combat_service `get_equipped_damage_bonus()`/`get_equipped_attack_bonus()`. The FORMULA is identical in both; only the attribute accessors differ per codebase.

---

## 8. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Clamp order broken (gotchas.md) | Med | High | Keep clamp AFTER AV subtraction & crit, BEFORE `CombatEvent` |
| 4 existing test suites break on `CombatEvent` constructor | **Was High** | High | **FIXED:** `target_ac`/`d20_roll` kept as REAL fields this release; `test_combat_event_renamed_fields` populates both pairs |
| `combat_service` caller still calls old `calculate_defense_roll` | High | High | **FIXED:** rename to `calculate_defense_value` AND update caller at `combat_service.py:85` |
| `is_critical_hit(attacker)` caller breaks | High | High | **FIXED:** keep `attacker` param; only body changed to read `self._last_d10` |
| Two combat systems diverge (math) | High | High | **RESOLVED:** both now use IDENTICAL formula — single d10 vs DV, crit = (d10==DIE_SIDES), hit = `atk_total >= dv`, damage = `parse_dice(weapon_dice)` + power//2 + dmg_bonus, then `max(MIN_DMG, dmg - AV)`. No separate crit roll. |
| `parse_dice` undefined | High | High | **FIXED:** added to `src/shared/utils/dice.py` and imported by both |
| `defense * 0.4` makes foes too weak/strong | Med | Med | Expose `DEFENSE_COMPRESSION` in `combat_config.py`; confirm via playtest |
| UI shows confusing new numbers | Low | Low | Update status line & debug panel text |
| `stats` may be dict or Stats object | Med | Med | Defensive `_reflex_mod`/`hasattr` pattern in both §4.2 and §4.3/§4.4 |
| Legacy tests assert old AC values | **Was Low (false assumption)** | High | **CORRECTED:** 6 legacy tests CANNOT pass unchanged (crit at d20=20, `armor_class>12`, impossible MISS premise). Coder is AUTHORIZED to apply the 6 exact edits in §6.1. After edits, all 4 suites pass. |

**Architecture doc updates required (implementation step, not yet done):**
- `architecture/INDEX.md`: add `src/domain/value_objects/combat_config.py` and `src/shared/utils/dice.py` to inventory.
- `architecture/gotchas.md`: add "Fuzion AC clamp order" entry.
- `architecture/system_overview.md`: mark combat layer status updated.

---

*End of implementation design (revised). No source files were modified in this step.*
