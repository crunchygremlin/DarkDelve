# Stat System Overhaul Proposal

**Status:** PROPOSED — DO NOT IMPLEMENT WITHOUT HUMAN SIGN-OFF
**Date:** 2026-06-24
**Author:** Architect Mode (OWL)

---

## 1. Goals

- **Unified Stat Model** — Centralize all character attributes (STR, DEX, CON, INT, WIS, CHA) and derive derived values (HP, AC, Attack Bonus, Damage Bonus, Speed, etc.) from them.
- **Ability‑Stat Mapping** — Define clear formulas that map primary stats to combat and gameplay abilities:
  - Melee attack bonus = `STR // 2 + proficiency`
  - Ranged attack bonus = `DEX // 2 + proficiency`
  - Spellcasting = `INT` or `WIS` depending on class
  - AC = `10 + DEX // 2 + armor_bonus`
  - HP = `10 + CON // 2 + class_hp_per_level`
  - Speed = `10 + DEX // 4` (energy increment per tick)
- **Extensible Design** — Allow future addition of new stats or abilities without touching core combat logic.
- **Data‑Driven Configuration** — Store stat‑to‑ability relationships in a JSON/YAML config that can be loaded at runtime, enabling easy tweaking and balancing.
- **Compatibility Layer** — Preserve existing API for legacy code (e.g., `Entity.power`, `Entity.defense`) while routing through the new system.

## 2. Current Problems

- Stats are scattered: `power`, `defense`, `speed` are raw fields on `Entity` with no unifying system.
- Derived values (AC, to-hit, damage) are computed ad-hoc in multiple places (`Entity.armor_class`, `Entity.to_hit_bonus`, `CombatResolver.resolve_attack`).
- Monster templates use raw `defense` and `power` values that are unbalanced (cached roster has defense 4-30, resulting in AC 14-40).
- No stat scaling with level or class.
- Combat formulas are hardcoded in `CombatResolver` with no external configuration.

## 3. High‑Level Design

```
┌─────────────────────────────────────────────────────┐
│                     Entity                          │
│  ┌───────────────────────────────────────────────┐  │
│  │              StatContainer                     │  │
│  │  ┌─────────────┐    ┌──────────────────────┐  │  │
│  │  │  BaseStats   │───▶│   DerivedStats        │  │  │
│  │  │  str, dex,   │    │   hp, ac, attack_bonus│  │  │
│  │  │  con, int,   │    │   damage_bonus, speed │  │  │
│  │  │  wis, cha    │    │   to_hit_mod          │  │  │
│  │  └─────────────┘    └──────────────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  StatConfig (JSON/YAML)                             │
│  ┌─────────────────────────────────────────────┐    │
│  │  formulas:                                  │    │
│  │    ac: "10 + dex//2 + armor_bonus"          │    │
│  │    hp: "10 + con//2 + class_hp_per_level"   │    │
│  │    attack_bonus: "str//2 + proficiency"     │    │
│  │    speed: "10 + dex//4"                     │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  LegacyAdapter                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │  power  → DerivedStats.attack_bonus         │    │
│  │  defense → DerivedStats.ac - 10             │    │
│  │  speed  → DerivedStats.speed                │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### 3.1 BaseStats Dataclass
```python
@dataclass
class BaseStats:
    str: int = 10
    dex: int = 10
    con: int = 10
    int: int = 10
    wis: int = 10
    cha: int = 10
    level: int = 1
    proficiency_bonus: int = 2
```

### 3.2 DerivedStats Dataclass
```python
@dataclass
class DerivedStats:
    max_hp: int = 10
    ac: int = 10
    attack_bonus: int = 0
    damage_bonus: int = 0
    speed: int = 10
    to_hit_mod: int = 0
```

### 3.3 StatConfig Schema (YAML)
```yaml
formulas:
  max_hp: "class_hp_per_level + (con - 10) // 2"
  ac: "10 + (dex - 10) // 2 + armor_bonus"
  attack_bonus: "(str - 10) // 2 + proficiency_bonus"
  damage_bonus: "(str - 10) // 2"
  speed: "10 + (dex - 10) // 4"
  to_hit_mod: "(str - 10) // 2 + proficiency_bonus + weapon_to_hit"

classes:
  warrior:
    hp_per_level: 12
    proficiency_bonus: 2
  rogue:
    hp_per_level: 8
    proficiency_bonus: 2
  mage:
    hp_per_level: 6
    proficiency_bonus: 2
```

### 3.4 StatContainer
```python
class StatContainer:
    def __init__(self, base: BaseStats, config: StatConfig, class_name: str = "warrior"):
        self.base = base
        self.config = config
        self.class_name = class_name
        self._derived: Optional[DerivedStats] = None

    @property
    def derived(self) -> DerivedStats:
        if self._derived is None:
            self._derived = self._compute()
        return self._derived

    def _compute(self) -> DerivedStats:
        # Evaluate formulas from config using base stats
        ...
```

## 4. Migration Plan

1. **Phase 1 — Introduce StatContainer alongside existing fields**
   - Add `StatContainer` to `Entity` as optional field
   - Keep `power`, `defense`, `speed` working via LegacyAdapter
   - Write tests for StatContainer calculations

2. **Phase 2 — Refactor combat to use DerivedStats**
   - Update `CombatResolver` to use `attacker.stats.derived.attack_bonus`
   - Update `Entity.armor_class` to use `self.stats.derived.ac`
   - Update `EnergySystem` to use `self.stats.derived.speed`

3. **Phase 3 — Migrate monster templates**
   - Replace raw `defense`/`power` with `BaseStats` in monster templates
   - Rebalance cached roster values

4. **Phase 4 — Remove legacy fields**
   - Remove `power`, `defense`, `speed` from `Entity`
   - Remove LegacyAdapter

## 5. Files Affected

| File | Change |
|------|--------|
| `src/domain/entities/entity.py` | Add `stats: StatContainer` field |
| `src/domain/entities/mob.py` | Use `BaseStats` in templates |
| `src/domain/entities/player.py` | Initialize `StatContainer` on creation |
| `darkdelve.py` | Refactor `CombatResolver`, `EnergySystem`, `Entity.armor_class` |
| `src/domain/components/combat.py` | Update combat formulas |
| `src/domain/value_objects/stats.py` | New file: `BaseStats`, `DerivedStats`, `StatConfig`, `StatContainer` |
| `config/stat_formulas.yaml` | New file: stat formula definitions |
| `tests/test_stat_system.py` | New file: comprehensive stat tests |

## 6. Risks

- **Balance regression** — New formulas may make game too easy/hard. Mitigation: extensive playtesting after Phase 2.
- **Save compatibility** — Old saves use raw fields. Mitigation: migration script in Phase 3.
- **Scope creep** — This is a large refactor. Mitigation: phased approach with tests at each phase.

---

**DO NOT IMPLEMENT WITHOUT HUMAN SIGN-OFF**
