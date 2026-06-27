# Task: Persistent Combat Damage Log

**Task ID:** T-2026-06-27-001
**Complexity:** MULTI_FILE
**Pipeline:** Orchestrator → Architect → Coder → Playtester

## Goal

Add a persistent combat damage log that records every hit, miss, and critical hit with timestamps, attacker name, target name, and damage amount. The log should be written to a JSON file at the end of each game session.

## Requirements

1. **New file:** `src/infrastructure/persistence/combat_damage_log.py`
   - A `CombatDamageLog` class that stores combat events in memory
   - Each event records: timestamp, attacker_name, target_name, damage, hit, critical, event_type
   - Method to export to JSON file
   - Method to get summary stats (total damage dealt/received, hit count, miss count, critical count)

2. **Integration points:**
   - Wire into `darkdelve.py` `Game` class — instantiate `CombatDamageLog` on game init
   - Call log method in `Game.attack()` after each `CombatEvent` is resolved
   - Call log method in `Game.add_combat_message()` for all combat events
   - Write JSON file on game end (in `Game.cleanup()` or equivalent)

3. **New test file:** `tests/test_combat_damage_log.py`
   - Test event recording
   - Test JSON export
   - Test summary stats calculation
   - Test empty log handling

4. **Output location:** `logs/combat_damage_{session_id}.json` (session_id = timestamp or game ID)

## Constraints

- Must not break existing `combat_message_log` or `CombatEvent` system
- JSON format must be human-readable (indent=2)
- Timestamps in ISO 8601 format
- File writes should be atomic (write to temp then rename, or use `json.dump` directly)

## Existing code to reference

- `darkdelve.py` — `Game` class, `CombatEvent`, `HitResult`, `Game.attack()`, `Game.add_combat_message()`
- `src/domain/services/combat_service.py` — `CombatService.execute_attack()` already creates `CombatEvent` objects
- `src/domain/value_objects/combat_event.py` — `CombatEvent` and `CombatEventType` definitions
