# FZ-001 Design: Redesign DarkDelve Systems Around Fuzion Concepts & Skills

**Task ID:** FZ-001
**Owner:** Architect -> Orchestrator -> Coder -> Play Tester
**Supersedes:** `plans/proposals/stat_system_overhaul_proposal.md` (D&D model — DO NOT implement that proposal; FZ-001 is the canonical Fuzion redesign).

---

## 1. Goal

Replace DarkDelve's D&D 6-stat model with the Fuzion 10 Primary Characteristics + Derived
Characteristics + 9-category Skills model, and re-route combat/damage resolution through a
data-driven Fuzion engine, while keeping all existing public APIs and tests green via explicit
migration shims.

---

## 2. Fuzion -> DarkDelve Concept Mapping Table

| Fuzion Concept | Fuzion Group | DarkDelve Mapping | Notes |
|---|---|---|---|
| INT | Mental | `PrimaryCharacteristics.int` | unchanged from D&D INT |
| WILL | Mental | `PrimaryCharacteristics.will` | NEW; absorbs D&D WIS |
| PRE | Mental | `PrimaryCharacteristics.pre` | NEW; absorbs D&D CHA |
| TECH | Combat | `PrimaryCharacteristics.tech` | NEW; governs Technique skills / armor use |
| REF | Combat | `PrimaryCharacteristics.ref` | NEW; primary defense & Fighting to-hit |
| DEX | Combat | `PrimaryCharacteristics.dex` | unchanged from D&D DEX; governs Ranged |
| CON | Physical | `PrimaryCharacteristics.con` | unchanged; drives SD/REC/ED/END |
| STR | Physical | `PrimaryCharacteristics.str` | unchanged; drives REC, melee DC, knockback |
| BODY | Physical | `PrimaryCharacteristics.body` | NEW; drives Hits/Stun (replaces HP) |
| MOVE | Movement | `PrimaryCharacteristics.move` | NEW; drives Run/Sprint/Leap |
| Stun | Derived | `DerivedCharacteristics.stun = body*5` | replaces mana-adjacent pool; non-lethal |
| Hits | Derived | `DerivedCharacteristics.hits = body*5` | replaces `health`/`max_health` |
| Stun Defense (SD) | Derived | `DerivedCharacteristics.sd = con*2` | stops Stun damage |
| Recovery (REC) | Derived | `DerivedCharacteristics.rec = str+con` | per-turn healing |
| Run / Sprint / Leap | Derived | `move*2 / move*3 / move*1` | movement ranges |
| ED / END / SPD / RES / HUM | Derived (optional) | `con*2 / con*10 / ref//2 / will*3 / will*10` | optional, config-gated |
| Option Points (OP) | Creation | `SkillSet` levels (1 OP = 1 level) | data-driven in `config/fuzion.yaml` |
| Characteristic Points (CP) | Creation | `PrimaryCharacteristics` point-buy | `config/fuzion.yaml` caps |
| 9 Skill Categories | Skills | `SkillSet` (9 float fields) | see §4 |
| AV = CHAR+SKILL+die | Combat | `combat_factors.calculate_attack_value` | re-mapped |
| DV | Combat | `combat_factors.calculate_defense_value` | re-mapped, includes REF |
| Damage Class (DC) | Damage | `FuzionDamageCalculator` | # of D6 |
| Hits/Stun/SDP/Kills | Damage | `FuzionDamageResult` | replaces Hero-System model |
| KD / SD / ED | Armor | `target.killing_defense / stun_defense / energy_defense` | from armor config |
| Aimed shots / Knockback / Rule of X | Combat | config-driven constants | P3/P5 |

**D&D -> Fuzion legacy shim:** `Stats` (D&D) is retained as a DEPRECATED compatibility facade.
`Player.stats` and `darkdelve.Entity.stats` continue to work: the D&D `dexterity` field is fed by
Fuzion `ref`, `wisdom` by `will`, `charisma` by `pre`. `Stats.get_modifier('dexterity')` returns
`(ref-10)//2` so existing callers (e.g. `combat_factors._reflex_mod`) stay correct.

---

## 3. New / Changed File List

### 3.1 Files to CREATE

| File | Responsibility |
|---|---|
| `src/domain/value_objects/fuzion_stats.py` | `PrimaryCharacteristics`, `DerivedCharacteristics`, `SkillSet` (9 cats), `EVERYMAN_SKILLS` helper |
| `src/domain/value_objects/fuzion_damage.py` | `FuzionDamageResult`, `FuzionDamageCalculator` (DC/Hits/Stun/KD/SD/ED/Knockback) |
| `src/domain/services/fuzion_skill_service.py` | Resolve skill bonuses from `SkillSet` / mob string-skills into (attack,dv,av) |
| `config/fuzion.yaml` | Skill categories, governing-char map, DC tables, everyman skills, aimed-shot mults, Rule-of-X caps, dice mode, characteristic caps |
| `tests/test_fuzion_stats.py` | Unit tests for characteristics/derived/skills |
| `tests/test_fuzion_damage.py` | Unit tests for DC/Hits/Stun/KD/SD/ED/knockback |
| `tests/test_fuzion_skill_service.py` | Unit tests for skill re-map (player + mob) |
| `tests/test_fuzion_migration.py` | Backward-compat shim tests (Stats facade, save migrate) |

### 3.2 Files to MODIFY

| File | Lines | Change |
|---|---|---|
| `src/domain/value_objects/combat_config.py` | 1-11 | Add `FuzionCombatConfig` frozen dataclass + `FUZION_CONFIG` instance; KEEP `CombatConfig`/`COMBAT_CONFIG` for test compat |
| `src/domain/value_objects/stats.py` | 1-163 | Keep `Stats` as deprecated facade over `PrimaryCharacteristics`; add `to_primary()`/`from_primary()`; keep `get_modifier` |
| `src/domain/services/combat_factors.py` | 10-92, 137-179 | Re-map `MOB_SKILL_BONUS_MAP` to Fuzion categories; `get_skill_bonuses` reads `SkillSet` via `fuzion_skill_service`; keep numeric formula shape |
| `src/domain/services/combat_service.py` | 67-215 | Route `calculate_damage` through `FuzionDamageCalculator` in P3; keep `execute_attack` signature |
| `src/domain/components/damage_calculator.py` | 1-65 | Wrap `FuzionDamageCalculator` instead of Hero-System `DamageCalculator` |
| `src/domain/entities/player.py` | 12-30, 20-24, 371-386 | Add `self.characteristics = PrimaryCharacteristics()`; derive `health`/`max_health` from `hits`; keep `stats` shim; `to_dict` includes characteristics |
| `src/domain/entities/mob.py` | 22, 39-53, 55-92 | Use `PrimaryCharacteristics`; map mob-type stats to Fuzion; `skills` -> Fuzion category strings; `health` from `hits` |
| `src/domain/value_objects/power_levels.py` | 64-90 | Replace `SkillSet` weapon_mastery/armor_mastery/tactical_awareness with 9 Fuzion categories (keep class name `SkillSet` for compat) |
| `src/application/services/player_profile_service.py` | 205-243 | Build 9-category `SkillSet` from Fuzion characteristics |
| `darkdelve.py` | 754-841, 994-1031 | Keep `Entity.defense_value`/`armor_value` working with both dict and object stats; `CombatResolver` uses Fuzion damage in P3 (keeps `CombatEvent` fields) |
| `src/infrastructure/persistence/save_system.py` | 18-42 | Bump save version; add `migrate_v1_to_v2(state)` for characteristics/skills |
| `architecture/INDEX.md` | 72-99 | Add FZ-001 design + new files to inventory |
| `architecture/gotchas.md` | end | Add Fuzion pitfall (governing-char mapping, defense_value vs combat DV) |
| `tests/test_fuzion_combat.py` | 1-70 | EXTEND (do not break) with skill/derived-stat tests |

---

## 4. Data Models (dataclasses)

```python
# src/domain/value_objects/fuzion_stats.py
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass(frozen=True)
class PrimaryCharacteristics:
    int: int = 10
    will: int = 10
    pre: int = 10
    tech: int = 10
    ref: int = 10
    dex: int = 10
    con: int = 10
    str: int = 10
    body: int = 10
    move: int = 10

    def __post_init__(self) -> None:
        for name, val in self.__dict__.items():
            if not isinstance(val, int) or val < 0:
                raise ValueError(f"{name} must be a non-negative int")

    def modifier(self, char: str) -> int:
        # Backward-compat D&D-style modifier; new code uses raw values.
        return (getattr(self, char, 10) - 10) // 2

    def to_dict(self) -> Dict[str, int]:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, d: Dict[str, int]) -> "PrimaryCharacteristics":
        return cls(**{k: d.get(k, 10) for k in cls.__dataclass_fields__})

@dataclass(frozen=True)
class DerivedCharacteristics:
    stun: int = 50
    hits: int = 50
    sd: int = 20          # Stun Defense
    rec: int = 20         # Recovery
    run: int = 20
    sprint: int = 30
    leap: int = 10
    ed: int = 20          # Energy Defense (optional)
    end: int = 100        # Endurance (optional)
    spd: int = 5          # Speed (optional)
    res: int = 30         # Presence/Res (optional)
    hum: int = 100        # Humanity (optional)

    @classmethod
    def from_primary(cls, pc: PrimaryCharacteristics) -> "DerivedCharacteristics":
        return cls(
            stun=pc.body * 5,
            hits=pc.body * 5,
            sd=pc.con * 2,
            rec=pc.str + pc.con,
            run=pc.move * 2,
            sprint=pc.move * 3,
            leap=pc.move * 1,
            ed=pc.con * 2,
            end=pc.con * 10,
            spd=pc.ref // 2,
            res=pc.will * 3,
            hum=pc.will * 10,
        )

@dataclass
class SkillSet:
    # 9 Fuzion skill categories (level = OP spent)
    fighting: float = 0.0
    ranged_weapon: float = 0.0
    awareness: float = 0.0
    control: float = 0.0
    body: float = 0.0
    social: float = 0.0
    technique: float = 0.0
    performance: float = 0.0
    education: float = 0.0

    def level(self, category: str) -> float:
        return getattr(self, category, 0.0)

    def as_dict(self) -> Dict[str, float]:
        return {f: getattr(self, f) for f in self.__dataclass_fields__}

    @classmethod
    def everyman(cls) -> "SkillSet":
        # Everyman skills start at level 2 free (per PDF).
        from src.domain.value_objects.fuzion_stats import EVERYMAN_DEFAULT
        return cls(**EVERYMAN_DEFAULT)
```

```python
# src/domain/value_objects/combat_config.py  (ADD, keep existing CombatConfig)
from dataclasses import dataclass

@dataclass(frozen=True)
class FuzionCombatConfig:
    DIE_SIDES: int = 10
    BASE_DV: int = 6
    DEFENSE_COMPRESSION: float = 0.4
    CRIT_DIE_MAX: int = 10            # natural max => open-end / +1 DC
    SKILL_BONUS_DIVISOR: int = 5      # float skill level -> int bonus
    LEVEL_BONUS_PER_LEVEL: int = 1
    EVERYMAN_SKILL_LEVEL: int = 2
    MIN_DMG: int = 1
    DICE_MODE: str = "interlock"      # or "hero" (3d6 + flat 10 DV)
    HERO_DV_FLAT: int = 10
    KNOCKBACK_DIVISOR: int = 5
    AIMED_HEAD_MULT: float = 2.0
    AIMED_VITALS_MULT: float = 1.5
    RULE_OF_X_ATTACK: int = 20        # campaign cap (config-overridable)
    RULE_OF_X_DEFENSE: int = 20

FUZION_CONFIG = FuzionCombatConfig()
```

```python
# src/domain/value_objects/fuzion_damage.py
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class FuzionDamageResult:
    hits: int = 0          # lethal body damage
    stun: int = 0          # non-lethal stun damage
    sdp: int = 0           # structural damage (inanimate)
    kills: int = 0         # massive/tough damage
    knockback: int = 0     # tiles pushed
    aimed_location: str = "body"

class FuzionDamageCalculator:
    # see §6 for algorithm
    ...
```

---

## 5. Combat Resolution Algorithm (AV / DV, dice, crit, aimed, knockback)

### 5.1 Governing characteristic per skill category (data-driven in `config/fuzion.yaml`)
```
fighting: ref
ranged_weapon: dex
awareness: int
control: will
body: str
social: pre
technique: tech
performance: pre
education: int
```

### 5.2 Pseudocode

```python
# src/domain/services/fuzion_skill_service.py
from src.domain.value_objects.fuzion_stats import PrimaryCharacteristics, SkillSet
from src.domain.value_objects.combat_config import FUZION_CONFIG as C

# config/fuzion.yaml -> SKILL_TO_BONUS: category -> "attack"|"dv"|"av"
# config/fuzion.yaml -> MOB_SKILL_MAP: mob_skill_str -> (category, bonus)

def get_skill_bonuses(entity: Any) -> Tuple[int, int, int]:
    # Returns (attack_bonus, dv_bonus, av_bonus)
    sk = _resolve_skillset(entity)          # SkillSet or None
    if sk is not None:
        return _bonuses_from_skillset(sk)
    # mob string-list path
    skills = getattr(entity, 'skills', []) or []
    atk = dv = av = 0
    for s in skills:
        cat, bonus = MOB_SKILL_MAP.get(s, (None, 0))
        kind = SKILL_TO_BONUS.get(cat, None)
        if kind == "attack": atk += bonus
        elif kind == "dv": dv += bonus
        elif kind == "av": av += bonus
    return atk, dv, av

def _resolve_skillset(entity):
    pc = entity.get_component("power") if hasattr(entity, 'get_component') else None
    if pc is not None and hasattr(pc, 'skills'): return pc.skills
    if hasattr(entity, 'skill_set') and entity.skill_set: return entity.skill_set
    if hasattr(entity, 'characteristics') and hasattr(entity, 'skills'):
        # build transient SkillSet from mapped mob skills (handled by MOB_SKILL_MAP)
        return None
    return None

def _bonuses_from_skillset(sk: SkillSet) -> Tuple[int, int, int]:
    d = sk.as_dict()
    atk = int((d['fighting'] + d['ranged_weapon']) // C.SKILL_BONUS_DIVISOR)
    dv  = int((d['awareness'] + d['control']) // C.SKILL_BONUS_DIVISOR)
    av  = int((d['technique'] + d['body']) // C.SKILL_BONUS_DIVISOR)
    return atk, dv, av

def governing_char(entity, category: str) -> int:
    pc = getattr(entity, 'characteristics', None)
    if pc is None:
        # legacy dict stats shim
        return _legacy_char(entity, category)
    return getattr(pc, GOVERNING_CHAR_MAP[category], 10)
```

```python
# src/domain/services/combat_factors.py  (MODIFY calculate_attack_value / calculate_defense_value)
def calculate_attack_value(attacker, weapon_dice="1d6", skill_category="fighting"):
    d10 = random.randint(1, C.DIE_SIDES)
    char = governing_char(attacker, skill_category)
    sk_atk, _, _ = get_skill_bonuses(attacker)
    level_bonus = get_level(attacker) * C.LEVEL_BONUS_PER_LEVEL
    atk = (d10 + char + sk_atk + get_to_hit_bonus(attacker)
           + get_power(attacker)//2 + level_bonus)
    mod = getattr(attacker, 'combat_attack_modifier', 1.0)
    return d10, int(atk * mod)

def calculate_defense_value(target):
    _, sk_dv, _ = get_skill_bonuses(target)
    level_bonus = get_level(target) * C.LEVEL_BONUS_PER_LEVEL
    ref = _reflex_char(target)            # REF (or legacy dex) raw value
    dv = (C.BASE_DV + (ref - 10)//2
          + int(get_defense_stat(target) * C.DEFENSE_COMPRESSION)
          + getattr(target, 'dodge_bonus', 0) + sk_dv + level_bonus)
    mod = getattr(target, 'combat_dv_modifier', 1.0)
    return int(dv * mod)
```

### 5.3 Dice options
- **Interlock (default):** `1d10 + DV`. Crit when `d10 == CRIT_DIE_MAX` (10) -> open-end (re-roll, add).
- **HERO option:** `3d6 + flat HERO_DV_FLAT (10)`. Selected by `FUZION_CONFIG.DICE_MODE`.

### 5.4 Aimed shots
`aimed_location` in `{"head":2.0, "vitals":1.5, "body":1.0}` (from config). Multiplies final
damage roll before defenses.

### 5.5 Knockback
`knockback = (attacker.str + result.hits) // C.KNOCKBACK_DIVISOR`. Applied by caller (combat_service)
to push target along attack vector.

---

## 6. Damage Algorithm (DC, Hits/Stun/SDP/Kills, KD/SD/ED, scaling)

### 6.1 Pseudocode

```python
# src/domain/value_objects/fuzion_damage.py
import random
from src.domain.value_objects.combat_config import FUZION_CONFIG as C

class FuzionDamageCalculator:
    def calculate(self, attacker, target, weapon_dc: int,
                  damage_type: str = "physical",
                  is_critical: bool = False,
                  aimed_location: str = "body") -> FuzionDamageResult:
        dc = max(1, int(weapon_dc))
        if is_critical:
            dc += 1                      # open-end: one extra d6
        raw = sum(random.randint(1, 6) for _ in range(dc))
        mult = AIMED_MULTS.get(aimed_location, 1.0)
        raw = int(raw * mult)
        # Melee fists deal Stun only (STR in DC of Stun); others deal Hits.
        is_stun_only = getattr(attacker, 'unarmed_stun', False)
        hits = 0 if is_stun_only else raw
        stun = raw
        # Defenses
        kd = getattr(target, 'killing_defense', 0)   # from armor (KD)
        sd = getattr(target, 'stun_defense', 0)      # target DerivedCharacteristics.sd
        ed = getattr(target, 'energy_defense', 0)
        if damage_type == "energy":
            hits = max(0, hits - ed); stun = max(0, stun - ed)
        else:
            hits = max(0, hits - kd)
        stun = max(0, stun - sd)
        knockback = (getattr(attacker, 'characteristics', _legacy_pc(attacker)).str + hits) // C.KNOCKBACK_DIVISOR
        return FuzionDamageResult(hits=max(C.MIN_DMG, hits) if (hits>0 or not is_stun_only) else 0,
                                  stun=max(0, stun), sdp=0, kills=0,
                                  knockback=knockback, aimed_location=aimed_location)
```

### 6.2 DC source
Weapon DC lives in `config/fuzion.yaml` keyed by item type (e.g. `sword: 4`, `fist: 3`, `bow: 5`).
`parse_dice` (dice.py) stays for legacy; a new helper `dc_from_weapon(item_type)` reads the table.
Fists DC = `STR` mapped to a DC band (config: `fist_dc_per_str`).

### 6.3 Scaling / Rule of X (P5)
Campaign cap: `AttackPower = DamageDC + REF + Skill <= RULE_OF_X_ATTACK`;
`DefensePower = Hits/5 + Def/5 + DEX + Skill <= RULE_OF_X_DEFENSE`. Enforced at character creation
and level-up (config-driven, no hardcode).

---

## 7. Migration Plan (Phased, tests per phase)

### P1 — Characteristics + Derived (no behavior change to combat)
- Add `fuzion_stats.py` (`PrimaryCharacteristics`, `DerivedCharacteristics`, `SkillSet`).
- `Player.__init__`: `self.characteristics = PrimaryCharacteristics()`; `self.derived = DerivedCharacteristics.from_primary(...)`.
  `self.max_health = self.derived.hits`; `self.health = self.derived.hits`; drop `mana` (map to `end` optional).
- `Mob._set_default_stats`: set Fuzion characteristics; `health = DerivedCharacteristics.from_primary(pc).hits`.
- Keep `Stats` shim so `player.stats.get_modifier('dexterity')` works (dex->ref).
- **Tests:** `test_fuzion_stats.py` (derived formulas, modifier, from_dict/to_dict).
- **Compat:** existing `test_fuzion_combat.py` still green (defense_value uses dex/ref shim).

### P2 — Skills + combat_factors re-map
- Replace `SkillSet` fields with 9 categories (keep class name).
- `combat_factors.get_skill_bonuses` -> `fuzion_skill_service.get_skill_bonuses`.
- Re-map `MOB_SKILL_BONUS_MAP` -> `config/fuzion.yaml` `MOB_SKILL_MAP` (category, bonus).
- `player_profile_service` builds 9-category `SkillSet`.
- **Tests:** `test_fuzion_skill_service.py` (player SkillSet -> bonuses; mob strings -> bonuses).
- **Compat:** players in tests have no skills -> bonuses 0 -> `test_fuzion_combat.py` green.

### P3 — Damage model
- Add `fuzion_damage.py`; `damage_calculator.py` wraps it; `combat_service.calculate_damage` routes through it.
- `CombatResolver` (darkdelve.py) uses `FuzionDamageCalculator` for `damage` (still int `hits`).
- `CombatEvent` keeps `target_ac/target_dv/d20_roll/d10_roll` fields.
- **Tests:** `test_fuzion_damage.py` (DC roll, KD/SD/ED subtraction, crit +1 DC, aimed mult, knockback).
- **Compat:** `test_damage_absorbs_av` only asserts `>= MIN_DMG` -> green.

### P4 — Items / Mobs migration
- `config/fuzion.yaml`: per-item-type DC, KD/SD/ED values, skill gating (min category level to equip).
- `Item` (darkdelve.py) gains `dc`, `kd`, `sd`, `ed`, `required_skill` fields (optional, default 0/None).
- Mob templates use Fuzion characteristics + category skill strings.
- **Tests:** `test_fuzion_migration.py` (item DC lookup, mob skill->category mapping).

### P5 — Talents / Perks / Rule-of-X
- `config/fuzion.yaml`: talents/perks list, Rule-of-X caps.
- Enforce caps in `Player` creation/level-up.
- **Tests:** cap enforcement unit tests.

### P6 — AI / Skill alignment
- `architecture/entity_ai_system.md` `SkillSet` reference updated to 9 categories.
- `BehaviorEngine` `has_skill` checks 9-category `SkillSet`.
- **Tests:** AI condition `has_skill` with Fuzion category.

---

## 8. Test Plan

### 8.1 Unit tests (exact code)

```python
# tests/test_fuzion_stats.py
import unittest
from src.domain.value_objects.fuzion_stats import (
    PrimaryCharacteristics, DerivedCharacteristics, SkillSet)

class TestFuzionStats(unittest.TestCase):
    def test_derived_from_primary(self):
        pc = PrimaryCharacteristics(body=10, con=10, str=10, ref=10, move=10, will=10)
        d = DerivedCharacteristics.from_primary(pc)
        self.assertEqual(d.hits, 50)
        self.assertEqual(d.stun, 50)
        self.assertEqual(d.sd, 20)
        self.assertEqual(d.rec, 20)
        self.assertEqual(d.run, 20)
        self.assertEqual(d.sprint, 30)

    def test_modifier_backward_compat(self):
        pc = PrimaryCharacteristics(ref=14)
        self.assertEqual(pc.modifier('ref'), 2)

    def test_skillset_everyman(self):
        sk = SkillSet.everyman()
        self.assertEqual(sk.awareness, 2)

    def test_round_trip_dict(self):
        pc = PrimaryCharacteristics(int=12)
        self.assertEqual(PrimaryCharacteristics.from_dict(pc.to_dict()).int, 12)
```

```python
# tests/test_fuzion_damage.py
import unittest
from unittest.mock import patch
from src.domain.value_objects.fuzion_damage import FuzionDamageCalculator

class FakeTarget:
    killing_defense = 5
    stun_defense = 5
    energy_defense = 0
    characteristics = type('PC', (), {'str': 10})()

class TestFuzionDamage(unittest.TestCase):
    def test_dc_subtracts_kd(self):
        calc = FuzionDamageCalculator()
        with patch('random.randint', return_value=4):   # 3d6 -> 12
            r = calc.calculate(FakeTarget(), FakeTarget(), weapon_dc=3)
        self.assertEqual(r.hits, 12 - 5)
        self.assertEqual(r.stun, 12 - 5)

    def test_crit_adds_dc(self):
        calc = FuzionDamageCalculator()
        with patch('random.randint', return_value=3):
            r = calc.calculate(FakeTarget(), FakeTarget(), weapon_dc=2, is_critical=True)
        # 3d6=9, crit +1d6=3 -> 12
        self.assertEqual(r.hits, 12 - 5)

    def test_aimed_head_double(self):
        calc = FuzionDamageCalculator()
        with patch('random.randint', return_value=3):
            r = calc.calculate(FakeTarget(), FakeTarget(), weapon_dc=2, aimed_location="head")
        self.assertEqual(r.hits, int(9 * 2) - 5)
```

```python
# tests/test_fuzion_skill_service.py
import unittest
from src.domain.value_objects.fuzion_stats import SkillSet
from src.domain.services.fuzion_skill_service import get_skill_bonuses

class TestSkillService(unittest.TestCase):
    def test_player_skillset_bonuses(self):
        sk = SkillSet(fighting=10, ranged_weapon=0, awareness=5, control=0, technique=5, body=0)
        # atk=(10+0)//5=2 ; dv=(5+0)//5=1 ; av=(5+0)//5=1
        self.assertEqual(get_skill_bonuses(_fake_with(sk)), (2, 1, 1))

    def test_mob_string_skills(self):
        mob = _fake_mob(["bite", "dodge", "scales"])
        atk, dv, av = get_skill_bonuses(mob)
        self.assertGreater(atk, 0)
        self.assertGreater(dv, 0)
        self.assertGreater(av, 0)
```

### 8.2 Playtest plan
- Headless in-process playtest (`MCPPlaytester`, `auto_initialize=False`): spawn player + orc,
  run 50 attack actions, assert no exceptions, hp decreases, defeat event fires.
- Assert `CombatEvent.target_dv`/`d10_roll` populated; assert save/load round-trips characteristics.
- Keep `playtest/telemetry_*.json` regression: compare hit-rate band before/after P3.

---

## 9. Integration Notes

- `CombatService` (combat_service.py) keeps `execute_attack(attacker, target, weapon_dice)` signature;
  internally calls `calculate_attack_value`/`calculate_defense_value` (combat_factors) and
  `FuzionDamageCalculator.calculate` (P3+). Crit uses `d10 == CRIT_DIE_MAX` (unchanged from current `DIE_SIDES`).
- `darkdelve.CombatResolver.resolve_attack` remains the public API used by tests; it delegates to the
  same `combat_factors` functions, so behavior is preserved. `CombatEvent` field names unchanged.
- `Player`/`Mob` store `characteristics` + `derived`; `stats` (D&D) is a deprecated shim for legacy
  callers (`combat_factors._reflex_mod`, `Entity.defense_value`). New code reads `characteristics`.
- `SkillSet` class name preserved (power_levels.py) but fields changed to 9 categories; any code
  reading `weapon_mastery` must move to `fighting`/`ranged_weapon`. `player_profile_service` updated.
- `config/fuzion.yaml` is the single source for skill categories, governing-char map, DC tables,
  everyman skills, aimed multipliers, Rule-of-X caps, dice mode. No hardcoding in domain code.
- Save format: `save_system.save` bumps version to `v2`; `migrate_v1_to_v2` adds
  `characteristics`/`skills` and derives `health` from `hits`. Old saves load via migration shim.

---

## 10. Risks & Gotchas Carried Forward

1. **defense_value vs combat DV** (gotchas.md): `Entity.defense_value` property is the BASE DV
   (no skill/level); `combat_factors.calculate_defense_value` is the COMBAT DV (with skill/level).
   Keep both; do not regress `test_defense_value_baseline` (must equal 6 for dex=10/def=2).
2. **armor_value double-count** (gotchas.md / B2 fix): Player has no `armor_value` attr; equipment
   defense read via `equipment.get_bonus("defense")`. Do NOT add `armor_value` to Player while also
   reading equipment — would double-count. `get_armor_value` already guards this; preserve.
3. **Fuzion AV uses governing characteristic, not raw DEX.** Ensure `GOVERNING_CHAR_MAP` is
   data-driven; a mob using `fighting` must pull `ref`, not `dex`. NEW pitfall added to gotchas.md.
4. **Crit semantics:** current code doubles damage on `d10==10`; Fuzion crit = open-end (+1 DC).
   P3 switches to +1 DC. Keep `CombatEvent.d10_roll` populated so tests relying on it stay green.
5. **Legacy `Stats` shim:** must keep `get_modifier('dexterity')` returning `(ref-10)//2`. If removed,
   `combat_factors._reflex_mod` and `Entity.defense_value` break. Keep until a later cleanup phase.
6. **Save compatibility:** bump version + migration; never silently drop `stats` dict from old saves.
7. **FZ-001 supersedes `stat_system_overhaul_proposal.md`** (D&D model). Do NOT implement that proposal.
8. **No file read > 500 lines** honored during design; coder must likewise chunk large files.

---

## 11. Import Statements (collected)

```python
# fuzion_stats.py
from dataclasses import dataclass, field
from typing import Dict, Any

# combat_config.py (add)
from dataclasses import dataclass

# fuzion_damage.py
import random
from dataclasses import dataclass
from typing import Any, Tuple
from src.domain.value_objects.combat_config import FUZION_CONFIG

# fuzion_skill_service.py
from typing import Any, Tuple
from src.domain.value_objects.fuzion_stats import PrimaryCharacteristics, SkillSet
from src.domain.value_objects.combat_config import FUZION_CONFIG as C

# combat_factors.py (modify)
from src.domain.services.fuzion_skill_service import get_skill_bonuses
from src.domain.value_objects.combat_config import FUZION_CONFIG as C

# combat_service.py (modify)
from src.domain.value_objects.fuzion_damage import FuzionDamageCalculator

# damage_calculator.py (modify)
from ..value_objects.fuzion_damage import FuzionDamageCalculator, FuzionDamageResult

# player.py / mob.py (modify)
from src.domain.value_objects.fuzion_stats import PrimaryCharacteristics, DerivedCharacteristics, SkillSet
```

---

## 12. Architecture Doc Updates

- `architecture/INDEX.md`: add rows for `fuzion_stats.py`, `fuzion_damage.py`, `fuzion_skill_service.py`,
  `config/fuzion.yaml`, `tests/test_fuzion_*.py`, and `plans/FZ-001_design.md`. Update routing keyword
  "stat / skill" to point at FZ-001 (not the gated proposal).
- `architecture/gotchas.md`: append pitfall #3 (governing-char mapping) and note FZ-001 supersedes the
  D&D proposal.
- `architecture/entity_ai_system.md`: update `SkillSet` reference (§5) to 9 Fuzion categories.
