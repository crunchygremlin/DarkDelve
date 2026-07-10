# FZ-001: Redesign DarkDelve Systems Around Fuzion Concepts & Skills

**Task ID:** FZ-001
**Classification:** SYSTEM (core character / skill / combat engine redesign across layers)
**Source Ruleset:** `/home/danny/Downloads/fuzion1.pdf` (Generic Fuzion, Rev 5.02)
**Date:** 2026-07-10
**Owner:** Orchestrator -> Architect -> Orchestrator -> Coder -> Orchestrator -> Play Tester -> Orchestrator

## 1. Goal

Replace DarkDelve's current D&D-style 6-stat model (STR/DEX/CON/INT/WIS/CHA with
`(v-10)//2` modifiers, HP/mana, AC) with the **Fuzion** roleplaying model from the
PDF, and integrate Fuzion's **skills** as the primary mechanism for combat and
non-combat resolution.

The codebase ALREADY contains a *partial* Fuzion migration that must be **extended and
unified**, not replaced or conflicted:
- `src/domain/value_objects/combat_config.py` — `DIE_SIDES=10`, `BASE_DV=6`, `DEFENSE_COMPRESSION=0.4`
- `src/shared/utils/dice.py` — weapon dice parser `"NdS+M"`
- `src/domain/services/combat_factors.py` — "single source of truth" for AV/DV/damage; currently maps
  a `weapon_mastery`/`armor_mastery`/`tactical_awareness` skill trio + `Mob_Skill_Bonus_Map`
- `tests/test_fuzion_combat.py` — existing Fuzion combat tests that MUST keep passing

The redesign must keep these working and fold the Fuzion **10 Primary Characteristics**,
**Derived Characteristics**, **Option-Point skills (9 categories)**, and the **Hits/Stun/DC damage
model** into a coherent, data-driven architecture.

## 2. Fuzion Concepts To Integrate (from the PDF)

1. **10 Primary Characteristics** in 4 groups:
   - Mental: INT, WILL, PRE
   - Combat: TECH, REF, DEX
   - Physical: CON, STR, BODY
   - Movement: MOVE
   (Replaces the 6 D&D stats. WILL/PRE/TECH/BODY/MOVE are new; WIS/CHA dropped or mapped.)
2. **Derived Characteristics** (formulas):
   - Stun = BODY x 5
   - Hits = BODY x 5
   - Stun Defense (SD) = CON x 2
   - Recovery (REC) = STR + CON
   - Run = MOVE x 2 ; Sprint = MOVE x 3 ; Leap/Swim = MOVE x 1
   - Optional: ED = CON x 2, END = CON x 10, SPD = REF/2, RES = WILL x 3, HUM = WILL x 10
3. **Option Points (OP) & Characteristic Points (CP)** — point-buy creation.
   CP: 1 pt = 1 level of a Primary Characteristic. Campaign CP totals: 20 (Everyday) .. 90+ (Superheroic).
   OP: 1 OP = 1 level of a Skill; 100 money units = 1 OP.
4. **Skills (9 categories)** — Fighting, Ranged Weapon, Awareness, Control, Body,
   Social, Technique, Performance, Education. Each skill used as `CHAR + SKILL + die roll`
   vs a Difficulty Value (DV) or opponent's `CHAR + SKILL + die`. Bought 1 OP/level.
   Everyman skills (Perception, Concentration, Education, Persuasion, Athletics, Teaching,
   Local Expert, Hand-to-Hand, Evasion) start at level 2 free.
5. **Combat resolution** — Attack Value `AV = CHAR + SKILL + die` vs Defense Value `DV`.
   Two dice options already partially present: Interlock (1D10 + DV roll) — keep as the default.
   HERO option (3D6 + flat 10 DV) optional. Crit = natural max die (d10==10 open-ends).
6. **Damage model** — Damage Class (DC) = number of D6 rolled.
   - Melee fists = STR in DC of **Stun**; kick = +1 DC (Stun), -1 to hit.
   - Hits (lethal), Stun (non-lethal), SDP (inanimate), Kills (massive/tough).
   - Armor: Killing Defense [KD] stops Hits; Stun Defense [SD] stops Stun; Energy Defense [ED].
   - Aimed shots (head x2, stomach/vitals x1.5), Knockback, Damage Scaling between DC/Kills.
7. **Talents, Perks, Complications, Gear** (optional / phased).
8. **Rule of X** for campaign power caps (Attack: Dmg+REF+Skill <= X; Defense: Hits/5+Def/5+DEX+Skill <= X).

## 3. Current DarkDelve Files (read these before designing)

| File | Current Role | Fuzion Change |
|------|--------------|----------------|
| `src/domain/value_objects/stats.py` | D&D 6-stat `Stats` dataclass, `(v-10)//2` mods, HP/mana, AC | Replace with Fuzion `PrimaryCharacteristics` (10) + `DerivedCharacteristics` |
| `src/domain/value_objects/combat_config.py` | Fuzion d10 config | Extend with DV/AV constants, DC tables, Rule-of-X |
| `src/shared/utils/dice.py` | `"NdS+M"` parser | Keep; add DC-from-weapon helper |
| `src/domain/services/combat_factors.py` | Fuzion AV/DV/damage "single source of truth"; `weapon_mastery/armor_mastery/tactical_awareness` + `Mob_Skill_Bonus_Map` | Re-map skills to Fuzion 9 categories; AV = CHAR+SKILL+die; DV includes SD |
| `src/domain/services/combat_service.py` | Orchestrates attack: `calculate_attack_value`, `calculate_defense_value`, `calculate_damage`; crit from d10==10 | Keep structure; route through new Fuzion stats/skills |
| `src/domain/components/combat.py` | Legacy `Combat` component (attack_power, defense, damage, crit) | Supersede by Fuzion stats; keep for compat or remove per design |
| `src/domain/components/damage_calculator.py` | Hero-System damage wrapper | Replace with Fuzion DC/Hits/Stun model |
| `src/domain/entities/player.py` | `Stats()`, health=100, mana=50, attack_power=10 | Init Fuzion characteristics; Hits/Stun from BODY; drop mana or map to END |
| `src/domain/entities/entity.py` | Base `Entity` component system | No change needed; stats become Fuzion |
| `src/domain/entities/mob.py` | Mob templates (skills list, armor_value, defense, power) | Skills -> Fuzion skill names; stats -> Fuzion characteristics |
| `architecture/entity_ai_system.md` | Existing `SkillSet`/`PowerLevels` design (weapon_mastery etc.) | Align skill names to Fuzion categories |
| `architecture/dungeon_item_systems.md` | Item stats / skill integration | Align item DCs, KD/SD, skill gating |
| `plans/proposals/stat_system_overhaul_proposal.md` | GATED D&D-style proposal — DO NOT implement as-is | Note: wrong model (D&D not Fuzion); new design supersedes conceptually |
| `architecture/gotchas.md` | Known pitfalls (defense_value vs defense_value property, armor_value double-count) | Honor these; do not regress |
| `tests/test_fuzion_combat.py` | Existing Fuzion combat tests | MUST keep passing; extend with skill/derived-stat tests |

## 4. Design Constraints

- **SOLID layered architecture** preserved (domain/application/infrastructure/presentation).
- **No file read > 500 lines at once** (architecture rule).
- **All new/changed files need tests** (repo rule). Existing tests must stay green.
- **Backward compatibility:** keep public APIs used by `darkdelve.py`, commands, queries,
  event handlers working (or provide a clear migration shim). Save-format compatibility
  for `infrastructure/persistence/save_system.py` must be addressed (migration or version bump).
- **Data-driven:** skill lists, DC tables, characteristic caps should live in config
  (`config/` YAML/JSON) not hardcoded, matching the existing `StatConfig` intent.
- **Phased delivery:** the design doc must propose phases (e.g. P1 characteristics+derived,
  P2 skills+combat_factors re-map, P3 damage model, P4 items/mobs migration,
  P5 talents/perks/rule-of-X, P6 AI/skill alignment) with tests per phase.

## 5. Deliverable

Architect MUST produce `plans/FZ-001_design.md` containing:
- Fuzion-to-DarkDelve concept mapping table
- New/changed file list with responsibilities
- Data model (dataclasses) for `PrimaryCharacteristics`, `DerivedCharacteristics`, `SkillSet` (9 categories), `FuzionCombatConfig`
- Combat resolution algorithm (AV/DV, dice options, crit, aimed shots, knockback)
- Damage algorithm (DC, Hits/Stun/SDP/Kills, KD/SD/ED, scaling)
- Migration plan for player/mob/item/save with phase breakdown
- Test plan (unit + playtest)
- Risks & gotchas carried forward

Architect returns control to Orchestrator. DO NOT implement.
