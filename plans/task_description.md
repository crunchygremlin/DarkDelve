# Task: Combat Balance Broken — Abyssal Guardian (and boss-tier mobs) unbeatable

## Task ID: CB-001
## Complexity: SYSTEM
## Goal
Rebalance the combat system so boss-tier monsters (exemplified by "Abyssal Guardian")
are challenging but BEATABLE: the player must have a viable hit chance against them,
and they must not auto-hit the player every turn. Also fix the combat-event logging
inconsistency where hits are recorded as misses.

## Evidence (logs/combat_damage_8b6e2599.json)
- Player (Adventurer) attack rolls: 12-20. Against normal mobs (DV 7: Cave Rat,
  Dungeon Guard, Giant Spider, Spider Queen) the player HITS (flavor "HIT!"/"CRITICAL HIT", damage applied).
- Against Abyssal Guardian (DV 23) the player ALWAYS MISSES (rolls 12-20 < 23).
- Abyssal Guardian attack rolls: 37-46. Player DV: 19-22. AG ALWAYS HITS (frequent CRITs).
- Normal mobs DV ~7; AG DV 23 (~3x). AG attack 37-46 vs player attack 12-20 (~2-3x).
- Combat summary reports total_hits: 0, yet many events have damage>0 and
  "HIT!"/"CRITICAL HIT!" flavor -> `hit`/`event_type` disagree with `damage`/flavor.

## Suspected Root Cause
1. calculate_attack_value (src/domain/services/combat_factors.py:104) includes
   get_power(attacker) // 2. Boss mobs have power 50-75 (content.db templates) -> +25-37
   attack; player power ~10-20 -> +5-10. The power//2 term dominates and creates a
   ~25-37 point attack gap between tiers -> high-tier mobs unhittable & always-hitting.
2. calculate_defense_value (combat_factors.py:115) scales with defense/level; boss DV (23)
   far exceeds player attack (12-20).
3. Resolution uses TWO systems: `result` (HIT/MISS) from combat_factors `atk_total >= dv`,
   while `damage` comes from FuzionDamageCalculator. Logged `hit`/`event_type` disagree
   with `damage`/flavor -> investigate darkdelve.CombatResolver.resolve_attack (darkdelve.py:1000),
   Game.attack (darkdelve.py:3171), CombatDamageLog.record_event (combat_damage_log.py:51).

## Files to investigate / likely edit
- src/domain/services/combat_factors.py (attack/defense formulas - primary rebalance)
- src/domain/value_objects/combat_config.py (BASE_DV=6, DEFENSE_COMPRESSION=0.4)
- darkdelve.py (CombatResolver.resolve_attack, CombatEvent, Game.attack)
- src/infrastructure/persistence/combat_damage_log.py (hit/event_type logging)
- src/domain/entities/mob.py (mob stats + combat_*_modifier defaults)
- src/application/services/dynamic_difficulty_service.py (difficulty scaling)
- cache/content.db (boss stat templates: power/defense/tier)
- logs/combat_damage_8b6e2599.json (evidence)

## Acceptance Criteria
- Player has a reasonable hit chance (target ~25-50%) vs boss-tier mobs at level.
- Boss-tier mobs do NOT auto-hit the player every turn (player dodges sometimes).
- Combat-event `hit`/`event_type` accurately reflect `damage`/flavor (summary total_hits>0 on hits).
- All existing tests pass; add/extend tests for rebalanced formulas + logging fix.
- No regression to normal (non-boss) mob combat.

## Scope / Constraints
- Only perform the work outlined here. Do not refactor unrelated systems.
- These instructions supersede any conflicting general instructions.
