# FUZION-ENT-001 — Propagate Fuzion AV/DV Combat Model to All Entities

## Classification
SYSTEM (core combat integration across monsters, items, difficulty factors, skills, and level; touches both combat systems and the entity/component layer).

## Goal
Ensure EVERY combatant entity in DarkDelve uses the Fuzion-inspired d10 Attack-Value vs Defense-Value (DV) + Armor Value (AV) model consistently, and that the model treats SKILLS (weapon_mastery, armor_mastery, tactical_awareness) and LEVEL as first-class combat factors. Integrate: monsters, items, difficulty factors, skills, level.

## Background
FUZION-AC-001 replaced the d20+AC system in `darkdelve.py` `CombatResolver` and `src/domain/services/combat_service.py` with the d10 DV/AV model. The surrounding entity ecosystem was NOT updated:

- `src/domain/entities/mob.py` `Mob.get_defense()` / `get_attack_damage()` still use OLD `constitution//2` math.
- `combat_service.py` `calculate_defense_value(target)` reads `target.defense` — but `Mob` (System B) has NO `defense` attribute -> AttributeError at runtime. The two combat systems diverge.
- `darkdelve.py` `MobTemplate.armor_value` (added in FUZION-AC-001) is never applied to spawned monster AV.
- `MobTemplate.skills` (string list) is never used in combat.
- Skills (`weapon_mastery`, `armor_mastery`, `tactical_awareness`) are computed in `player_profile_service.py` but only feed LLM profile text, not combat math.
- `dynamic_difficulty_service.py` scales only monster HP/damage, not DV/AV/attack, and references stale `player_entity.power.level` / `fighter` attributes.
- `darkdelve.py` `Entity.level` is not used in combat math (user: "level is a more important factor in standard rogue").
- Items have `armor_value` but `attack_bonus`/`defense_bonus` integration into AV/attack should be verified; consider adding `weapon_dice`.

## Scope (Architect must design all of these)
1. MONSTERS (both entity systems):
   - System A (`darkdelve.py`): wire `MobTemplate.armor_value` and `MobTemplate.skills` into the spawned `Entity` (AV + skill-based bonuses).
   - System B (`src/domain/entities/mob.py`): replace OLD `get_defense()`/`get_attack_damage()` with Fuzion DV/AV; add `defense`, `power`, `to_hit_bonus`, `damage_bonus`, `armor_value`, `defense_value` to `Mob` so `combat_service.py` works without AttributeError.
2. ITEMS: verify/extend `Item.armor_value` and `attack_bonus`/`defense_bonus` feed AV/attack; add `weapon_dice` field if needed for damage resolution.
3. DIFFICULTY FACTORS: make `dynamic_difficulty_service.py` scale monster DV/AV/attack (Fuzion-aware), not just HP/damage; fix stale references.
4. SKILLS: wire `weapon_mastery` -> attack value, `armor_mastery` -> AV/DV, `tactical_awareness` -> DV in BOTH combat systems. Define how `MobTemplate.skills` (string list) map to numeric skill bonuses.
5. LEVEL: add `player.level` (and monster tier/level) as a factor in attack/defense values per user intent.

## Constraints
- Keep BOTH combat systems (darkdelve.CombatResolver and combat_service.CombatService) mathematically aligned (single source of truth via combat_config + shared helpers like parse_dice).
- Keep deprecated aliases (`armor_class`, `target_ac`, `d20_roll`) for one release.
- Do NOT break the 96 passing combat tests / 1158 full-suite tests. New behavior MUST be covered by new tests.
- Respect architecture docs; update INDEX.md / gotchas.md / system_overview.md as needed.

## Documents the Architect MUST read (with why)
1. `plans/FUZION-AC-001_impl_design.md` — authoritative Fuzion math (DV = BASE_DV + reflex_mod + int(defense*0.4) + dodge; AV absorption; MIN_DMG floor; crit = d10==10; parse_dice). All entities must converge on this.
2. `darkdelve.py` lines 652-666 (`MobTemplate`), 754-834 (`Entity` with defense_value/armor_value/to_hit_bonus/damage_bonus), 964-1046 (`CombatResolver.resolve_attack`). Shows System A's Fuzion implementation and monster stat origin.
3. `src/domain/entities/mob.py` (full) — System B Mob with OLD `get_defense()`/`get_attack_damage()`.
4. `src/domain/entities/item.py` (full) — Item armor_value/attack_bonus/defense_bonus.
5. `src/domain/entities/player.py` (full) — Player level, attack_power, equipment, take_damage (OLD math).
6. `src/domain/services/combat_service.py` (full) — System B combat; reads target.defense/attacker.power -> breaks on Mob.
7. `src/domain/components/power_component.py` + `src/domain/value_objects/power_levels.py` — SkillSet (weapon_mastery/armor_mastery/tactical_awareness) definitions.
8. `src/domain/services/player_profile_service.py` (lines ~170-210) — how skills are currently computed from stats (LLM only).
9. `src/domain/services/dynamic_difficulty_service.py` (full) — DifficultyAdjustment; scales HP/damage only; stale refs.
10. `src/application/services/content_seeder.py` (monster section) — how monsters are seeded with skills/power/defense/tier.
11. `architecture/system_overview.md`, `architecture/INDEX.md`, `architecture/gotchas.md` — for doc upkeep.

## Deliverable
A design doc at `plans/FUZION-ENT-001_design.md` specifying exact changes per file, pseudocode for DV/AV computation including skill & level factors, how `MobTemplate.skills` map to numeric bonuses, difficulty integration, and a test plan. Must keep both combat systems aligned and all existing tests green.
