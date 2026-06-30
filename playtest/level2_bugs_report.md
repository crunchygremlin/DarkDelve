# Playtest Report: T-2026-0629-002 — Explored Tiles Persist + Level 2 Monster Balance

**Date:** 2026-06-29
**Reporter:** Play Tester (automated investigation)
**Scope:** Issue 1 (explored tiles persist across levels), Issue 2 (level 2 monsters one-shot player)

---

## Issue 1: Explored Tiles Persist Across Levels

### Root Cause — CONFIRMED

**File:** `darkdelve.py`, lines 2738-2739 (`_generate_standard_level`)

```python
self.fov = self.fov_system.compute(self.dungeon_map, self.player.x, self.player.y)
self.explored = self.fov_system.explored.copy()
```

**Mechanism:**

1. `FOVSystem.compute()` (line 1088-1112) only resets `self.explored` when the map shape changes:
   ```python
   if self.explored is None or self.explored.shape != dungeon_map.shape:
       self.explored = np.zeros(dungeon_map.shape, dtype=bool)
   ```
2. Both level 1 and level 2 use the same map dimensions (80x43 from `config/game.yaml` lines 116, 111).
3. When `generate_level(2)` runs `_generate_standard_level()`, it creates a new `dungeon_map` with the same shape.
4. `fov_system.compute()` sees the shape hasn't changed, so it does NOT reset `explored`.
5. `self.explored = self.fov_system.explored.copy()` copies the stale level-1 explored data.
6. Result: Level 1's explored (dimmed) tiles appear on level 2.

**Same pattern exists in:**
- `_generate_floor1()` at line 2477-2478
- `build_map_from_description()` at line 2537-2540
- `redesign_floor()` at line 2867-2868

**Fix:** Reset both `self.explored` and `self.fov_system.explored` to `np.zeros(dungeon_map.shape, dtype=bool)` at the start of `_generate_standard_level()` and `_generate_floor1()`, before calling `fov_system.compute()`.

---

## Issue 2: Level 2 Monsters One-Shot the Player

### Root Cause — CONFIRMED

**Player stats (warrior class):**
- `max_hp = hp_per_level(10) + con(13) = 23 HP` (line 2264-2265)
- `AC = 10 + defense(2) + equipment_bonus` ≈ 17 (with chain mail + shield)
- Confirmed by test files: `tests/test_energy_system.py` line 7, `tests/test_regression_monster_movement_fov_combat.py` line 34

**Monster generation for depth > 1:**

**File:** `darkdelve.py`, line 2586
```python
roster = self.content_generator.generate_monster_roster(self.current_theme.monster_theme, depth)
```

**Problem 1: LLM-generated monsters have unbounded stats**

`generate_monster_roster()` (line 1205-1221) calls the LLM with a prompt asking for 8 monsters. The LLM response is parsed via `add_mobs_from_dict()` (line 642-683) which directly uses the LLM-provided `hp`, `power`, and `defense` values with NO clamping or scaling based on depth.

When `dm_enabled=False` (no LLM available), the fallback `create_default_roster()` is used, which produces balanced monsters:
- Goblin Scout: hp=5, power=2
- Goblin Soldier: hp=10, power=3
- Goblin Elite: hp=15, power=4
- Goblin Warlord: hp=30, power=6

But when `dm_enabled=True`, the LLM can generate monsters with arbitrary stats (e.g., `power=20+`), leading to damage like `1d6 + 20//2 = 1d6 + 10` = up to 16 per hit. Multiple monsters hitting in one turn can easily deal 66+ damage.

**Problem 2: No difficulty scaling applied**

The `config/game.yaml` defines difficulty scaling (lines 141-148):
```yaml
difficulty:
  scaling:
    story: 0.5
    normal: 1.0
    hard: 1.5
    nightmare: 2.0
    ironman: 3.0
```

But this scaling is NEVER applied to monster stats in `_generate_standard_level()`. The only "scaling" is speed-based (lines 2646-2654), which makes monsters slower but does nothing about their damage output.

**Problem 3: Monster count is random 8-15 with no depth-based control**

Line 2634: `for _ in range(random.randint(8, 15))` — no scaling with depth.

**Evidence from combat logs:**

Session `3c8394c5` (floor 1) shows balanced combat:
- Monster hits on player: 2-7 damage (consistent with power 1-3 monsters)
- Player AC 17 frequently causes misses

The "Void Demon" appears in the attacker list — this is an LLM-generated monster not in the default roster, confirming that LLM-generated content can produce arbitrarily powerful enemies.

### Recommended Fixes

1. **Clamp LLM-generated monster stats** in `add_mobs_from_dict()` based on depth:
   - `hp`: clamp to `[5, 5 + depth * 3]`
   - `power`: clamp to `[2, 2 + depth]`
   - `defense`: clamp to `[0, depth]`

2. **Apply difficulty scaling** from config to monster stats in `_generate_standard_level()`:
   ```python
   difficulty_scale = self.config.get('difficulty', {}).get('scaling', {}).get('normal', 1.0)
   monster_hp = int(template.hp * difficulty_scale)
   monster_power = int(template.power * difficulty_scale)
   ```

3. **Scale monster count with depth**: `random.randint(5 + depth, 10 + depth)` instead of fixed `random.randint(8, 15)`.

4. **Add a safety check**: If `dm_enabled=False` and no LLM response cached, use `create_default_roster()` with depth-based scaling instead of allowing unbounded LLM values.

---

## Summary

| Issue | Root Cause | Severity | Fix Complexity |
|-------|-----------|----------|----------------|
| Explored tiles persist | `FOVSystem.explored` not reset when map shape unchanged | Medium | 1 line per method |
| Monsters one-shot player | LLM-generated monster stats unbounded, no difficulty scaling | High | ~20 lines in `add_mobs_from_dict` + `_generate_standard_level` |

## Files Examined

- `darkdelve.py` — Game class, FOVSystem, ContentGenerator, combat resolution
- `config/game.yaml` — Map dimensions, difficulty scaling config, class stats
- `src/application/services/floor1_spawner.py` — Floor 1 monster templates
- `logs/combat_damage_3c8394c5.json` — Combat telemetry from floor 1
