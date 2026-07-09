# FUZION-AC-001 — Fuzion-Inspired To-Hit & Armor System for DarkDelve

- **Task ID:** FUZION-AC-001
- **Mode:** Architect (DESIGN ONLY — no source changes)
- **Date:** 2026-07-09
- **Status:** Draft for human/Orchestrator review (NOT implemented)
- **Reference:** Fuzion RPG (R. Talsorian Games). Design guide URL was unreachable
  (network blocked; direct + archive 404). Mechanics below are reconstructed from
  internal knowledge of the Fuzion/Interlock family. Assumptions are flagged in
  Appendix A.

---

## 1. Goal

Replace DarkDelve's `d20 + (10 + defense + equipment)` Armor-Class system with a
Fuzion-inspired, `d10`-based, `STAT + SKILL` Attack/Defense-Value model plus a
separate Armor Value (damage-absorption) layer, in order to eliminate AC ballooning
(e.g. AC 41 vs roll 20 still missing) and restore sensible, scalable hit probabilities.

---

## 2. Current DarkDelve Combat System (Analysis)

All references are to `darkdelve.py` (single-file legacy module).

### 2.1 To-hit & AC (the broken part)
- `Entity.armor_class` property — [`darkdelve.py`](darkdelve.py:794)
  ```
  base_ac = 10 + self.defense
  return base_ac + self.inventory.get_defense_bonus()   # equipment defense bonus ADDED to hit TN
  ```
- `Entity.to_hit_bonus` property — [`darkdelve.py`](darkdelve.py:802)
  ```
  return self.inventory.get_to_hit_bonus()   # weapon to_hit_bonus, else 0
  ```
- `CombatResolver.resolve_attack` — [`darkdelve.py`](darkdelve.py:966)
  ```
  d20_roll    = random.randint(1, 20)
  base_to_hit = attacker.power // 2
  dex_mod     = (attacker.stats['dex'] - 10) // 2
  total_roll  = d20_roll + base_to_hit + dex_mod + attacker.to_hit_bonus
  # nat 20 -> CRITICAL, nat 1 -> CRITICAL_FAIL
  # HIT if total_roll >= defender.armor_class else MISS
  ```
- `Inventory.get_defense_bonus` — [`darkdelve.py`](darkdelve.py:635): sum of
  `item.defense_bonus` for all equipped items. This is added straight into the hit TN.
- `Inventory.get_to_hit_bonus` / `get_damage_bonus` — [`darkdelve.py`](darkdelve.py:642):
  weapon-only bonuses.

### 2.2 Damage
```
base   = weapon_dice_roll + (attacker.power // 2) + attacker.damage_bonus
if CRITICAL: base *= 2
# clamp AFTER crit, BEFORE CombatEvent   (see architecture/gotchas.md "Damage Cap Clamping Order")
```

### 2.3 Data structures involved
- `Entity` — [`darkdelve.py`](darkdelve.py:748): fields `power` (default 3),
  `defense` (default 1), `stats` dict (`str/dex/con/int/wis/cha`, default 10),
  `inventory: Optional[Inventory]`, `level`, `xp`.
- `Item` — [`darkdelve.py`](darkdelve.py:448): `damage_bonus`, `defense_bonus`,
  `to_hit_bonus`, `encumbrance` (currently unused for combat math).
- `CombatEvent` — [`darkdelve.py`](darkdelve.py:360): fields `to_hit_bonus`,
  `target_ac`, `d20_roll`, `total_roll`, `result`, `damage`.
- `HitResult` enum — [`darkdelve.py`](darkdelve.py:321): MISS, HIT, CRITICAL, CRITICAL_FAIL.
- UI surfaces AC: status line [`darkdelve.py`](darkdelve.py:2047) `AC {armor_class}`;
  debug panel [`darkdelve.py`](darkdelve.py:3582) `AC: {player.armor_class}`;
  combat log [`darkdelve.py`](darkdelve.py:391) `[Roll: {total_roll} vs AC {target_ac}]`.

### 2.4 Root cause of the scaling bug
The hit TN is `10 + defense + equipment_defense`. The constant `10` plus an
*unbounded* equipment/defense contribution grows the TN far faster than the attacker's
offense, which is `d20(1..20) + power//2(small) + dex_mod(small) + weapon_to_hit(small)`.
The `d20` only spans 20, so once `defense + equipment` exceeds ~`10 + power//2 + bonuses`,
hits become mathematically near-impossible. Observed: Player AC 41, attacking with
total ~20–21 vs AC 25 and AC 41 → both MISS. Armor currently makes you *harder to hit*
rather than *harder to hurt*, which is the core design flaw Fuzion avoids.

---

## 3. Fuzion RPG Mechanics Summary (internal knowledge; assumptions flagged)

> These are reconstructed from memory of the Fuzion system (used in Talsorian's
> *Bubblegum Crisis*, * Teenagers from Outer Space*, and the generic Fuzion ruleset).
> Flagged assumptions are listed in Appendix A.

1. **Die:** Action resolution uses a **d10**, not d20.
2. **Attributes + Skills:** Core stats (REF, INT, BODY, TECH, COOL, ATTR, LUCK, EMP, MA)
   combine with Skills. A roll is `d10 + STAT + SKILL`.
3. **Target Number (TN):** Many actions are resolved by rolling `d10 + STAT + SKILL`
   and comparing to a TN set by the situation or the opponent.
4. **Opposed rolls:** Combat "to hit" is classically an **opposed roll**:
   `Attacker: d10 + REF + WeaponSkill` vs `Defender: d10 + REF + Dodge`. Higher total
   wins; the margin is the degree of success.
5. **Armor Value (AV) vs Damage Value (DV):** Armor does **not** make you harder to hit.
   Instead, when hit, `Damage Taken = DV(weapon) - AV(armor)`. Heavy armor may impose a
   **REF penalty (encumbrance)**, lowering both your attack and dodge.
6. **Criticals:** Rolling a **10** (max) can produce a critical (extra effect / max
   damage); rolling a **1** (min) is a fumble. Some variants require a confirm roll;
   the simplest form treats 10 = crit, 1 = fumble directly.

**Key insight for DarkDelve:** Because *both* attacker and defender use `STAT + SKILL`
of comparable magnitude, their numbers track together as characters level — avoiding
the one-sided inflation seen with a flat `+10 + defense` AC.

---

## 4. Concept Mapping (Fuzion -> DarkDelve)

| Fuzion concept            | DarkDelve source                                   | Proposed role |
|---------------------------|----------------------------------------------------|---------------|
| REF (reflex attribute)    | `Entity.stats['dex']` -> `dex_mod = (dex-10)//2`   | Reflex mod for attack & dodge |
| Weapon Skill              | `Entity.power`                                     | Attack proficiency (grows on level-up) |
| Dodge Skill               | `Entity.defense`                                   | Dodge proficiency (DV contributor) |
| Equipment to-hit          | `Item.to_hit_bonus` (via `Inventory.get_to_hit_bonus`) | Added to attack roll |
| Equipment damage          | `Item.damage_bonus`                                | Added to damage |
| Armor (protection)        | `Item.defense_bonus` (via `Inventory.get_defense_bonus`) | **Reinterpreted as Armor Value (AV)** — absorbs damage, NOT added to hit TN |
| Encumbrance               | `Item.encumbrance` (currently unused)              | **New:** REF penalty -> lowers DV & ATK for heavy armor (Fuzion tradeoff) |
| —                         | (no existing field)                                | `dodge_bonus` per-item (optional, light armor/shields) |
| Target Number             | old `armor_class`                                  | **Replaced by** `defense_value` (DV) |

Mobs: `MobTemplate` already carries `power` and `defense` ([`darkdelve.py`](darkdelve.py:647)),
so they feed the same formulas. Mobs have **no inventory**, so their AV = 0 unless we add
an `armor_value` field to `MobTemplate` (recommended for armored foes).

---

## 5. Proposed New System (Recommended: TN model)

We recommend a **single-roll-vs-TN** model (not full opposed rolls) for three reasons:
(a) it preserves the existing single-RNG `resolve_attack` structure (easier migration),
(b) a roguelike resolves many attacks per turn — opposed rolls double RNG calls and
complicate the `CombatEvent` log, and (c) it still captures Fuzion's core fix because
the TN (`DV`) and the attack roll are both `STAT + SKILL` scaled. The opposed-roll
variant is documented in 5.6 as an alternative.

### 5.1 New derived values (replace `armor_class`)

```
BASE_DV = 6            # tuning constant (small; replaces the old flat +10)
MIN_DMG = 1            # minimum damage on a connecting hit (optional; see 5.3)

def reflex_mod(e) -> int:
    base = (e.stats['dex'] - 10) // 2
    enc  = sum(item.encumbrance for item in equipped_items(e) if item)
    return base - enc          # heavy armor LOWERS reflex (Fuzion encumbrance)

def attack_value_roll(attacker) -> int:
    return random.randint(1, 10) + reflex_mod(attacker) + attacker.power + attacker.to_hit_bonus

def defense_value(defender) -> int:     # the TN to beat
    return BASE_DV + reflex_mod(defender) + defender.defense + defender.dodge_bonus

def armor_value(defender) -> int:       # damage absorbed
    if defender.inventory:
        return defender.inventory.get_defense_bonus()   # Item.defense_bonus now = AV
    return getattr(defender, 'armor_value', 0)          # MobTemplate.armor_value
```

### 5.2 To-hit resolution

```
d10        = random.randint(1, 10)
atk        = d10 + reflex_mod(attacker) + attacker.power + attacker.to_hit_bonus
dv         = defense_value(defender)
margin     = atk - dv

if d10 == 10:   result = CRITICAL        # max die
elif d10 == 1:  result = CRITICAL_FAIL   # min die (fumble)
elif margin >= 0: result = HIT
else:             result = MISS
```

Hit probability for equal foes (power == defense, dex 10, no encumbrance, no bonuses):
`P(hit) = P(d10 >= BASE_DV) = (11 - BASE_DV)/10`. With `BASE_DV = 6` this is **50%** —
a fair baseline. A foe with `defense` 2 above your `power` drops you to `P(d10>=8)=30%`;
2 below rises to `P(d10>=4)=70%`. The `d10` (span 10) now *dominates* the outcome instead
of being swamped by a ballooning constant.

### 5.3 Damage & Armor Value

```
if result in (HIT, CRITICAL):
    raw = weapon_dice_roll + (attacker.power // 2) + attacker.damage_bonus
    if result == CRITICAL:
        raw *= 2                      # or use max-dice; tunable
    taken = max(MIN_DMG, raw - armor_value(defender))   # AV absorbs damage
    # clamp AFTER AV subtraction, BEFORE CombatEvent (preserves gotchas.md order)
    taken = clamp(taken, defender)
else:
    taken = 0
```

Note: armor now reduces *damage*, never the hit chance. A heavily armored foe is easy to
*hit* but hard to *hurt* — the intended Fuzion behavior and the fix for the AC-41 problem.

### 5.4 Criticals & fumbles
- `d10 == 10` -> CRITICAL: double damage (or max weapon dice). Optional: ignore AV on a
  clean crit ("armor-piercing") — tunable flag `CRIT_IGNORES_AV`.
- `d10 == 1` -> CRITICAL_FAIL: automatic miss; optional side effect (drop weapon, stumble
  status `effects['stumble'] = 1`). Keep side effects minimal in v1.

### 5.5 Worked example (reproduces the bug, then fixes it)

Old system (observed): Player L2, AC 41, power ~6. Attacks Zombie.
`total = d20(20) + 3 + 0 + 0 = 23 < AC 25` -> MISS; `total = 21 < AC 41` -> MISS.

New system (post-migration stats, illustrative):
- Player: `power=6`, `dex=14` -> `reflex_mod=2`, `to_hit_bonus=+2`, no encumbrance.
  `atk = d10 + 2 + 6 + 2 = d10 + 10` -> range **11..20**.
- Zombie (light foe): `defense=2`, `dex=8` -> `reflex_mod=-1`, `dodge_bonus=0`.
  `dv = 6 + (-1) + 2 + 0 = 7`. Hit if `d10+10 >= 7` -> **always hits**.
- "AC 41 armored foe" from old log, re-mapped: its old `defense+equip=31` is split —
  `defense` re-tuned to **6** (DV side) and the rest becomes **AV = 25** (armor side).
  `dv = 6 + 0 + 6 = 12`; `atk` range 11..20 -> hit if `d10 >= 2` -> **90% hit chance**,
  but `taken = max(1, raw - 25)` -> damage is tiny. Result: you CAN hit the armored foe
  (fixing the frustration) but must bypass/penetrate its AV to actually hurt it. That is
  the correct, solvable design.

### 5.6 Alternative: opposed-roll variant (not recommended for v1)
```
atk = d10 + reflex_mod(attacker) + attacker.power + attacker.to_hit_bonus
def = d10 + reflex_mod(defender) + defender.defense + defender.dodge_bonus
margin = atk - def
HIT if margin >= 0; CRITICAL if atk's d10 == 10; CRITICAL_FAIL if attacker's d10 == 1
```
Pros: purest Fuzion feel, naturally symmetric. Cons: 2x RNG, `CombatEvent` must store both
rolls, harder to log/debug, and `defense_value` TN can't be shown on the UI status line.
Defer to a later phase if desired.

---

## 6. Benefits

1. **Fixes the scaling bug.** Hit chance is driven by `d10` variance and the
   `power`-vs-`defense` margin, not by an unbounded `10 + defense + equipment` constant.
2. **Armor no longer blocks hits.** `Item.defense_bonus` becomes Armor Value (damage
   soak), so equipping plate doesn't make enemies mathematically unable to land blows.
3. **Stat symmetry.** Attacker and defender both use `reflex_mod + proficiency`, so they
   scale together as levels rise — no single axis runs away.
4. **Encumbrance gains meaning.** `Item.encumbrance` finally affects combat (lowers REF),
   giving heavy-vs-light armor a real tradeoff (Fuzion signature).
5. **Smaller, more readable numbers.** DV in the ~6–20 band vs old AC 41; easier for
   players and for UI.
6. **Criticals stay meaningful** on the d10 max/min, preserving excitement with less swing.

---

## 7. Drawbacks / Costs

1. **Full combat rewrite.** `CombatResolver.resolve_attack`, `Entity.armor_class`,
   `CombatEvent` fields, and all UI strings referencing `AC`/`target_ac`/`d20_roll` change.
2. **Rebalance pass mandatory.** Existing `power`/`defense` and item `defense_bonus` values
   were tuned for the d20+AC math. A straight formula swap without re-tuning will feel
   wrong (see 9.3). This is the largest effort.
3. **UI changes.** Status line and debug panel must show `DV` and `AV` instead of `AC`;
   combat log format changes.
4. **Test churn.** Tests asserting on `armor_class`, `target_ac`, `d20_roll` break and must
   be rewritten (or shimmed during transition).
5. **Save/telemetry drift.** Playtest telemetry keys (`target_ac`, etc.) change meaning;
   historical logs become non-comparable.

---

## 8. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Rebalance produces trivial or impossible fights | High | High | Define conversion heuristic (9.3); run playtest sweep at Depth 1–5 before merge |
| `armor_class` referenced elsewhere (status, debug, LLM prompts) missed | Med | Med | Grep all `armor_class`/`target_ac`/`d20_roll` refs; keep a deprecated property alias during transition |
| Encumbrance values unknown / un-tuned | Med | Low | Start with `encumbrance_penalty = total_encumbrance // 2`; expose as config constant |
| Clamping order broken (gotchas.md) | Med | High | Keep clamp AFTER AV subtraction & crit, BEFORE `CombatEvent` (unchanged pipeline order) |
| `CombatEvent` consumers (log, LLM) break on renamed fields | Med | Med | Add `d10_roll`/`target_dv` fields; keep old fields one release as optional |
| Mobs have no AV -> armored monsters can't be modeled | Low | Low | Add `armor_value` to `MobTemplate` (default 0) |
| Human rejects d10 / wants opposed rolls | Low | High | 5.6 documents opposed variant as fallback |

---

## 9. Implementation Plan Outline (FUTURE — not executed in this design phase)

> The following is a blueprint for the Coder phase. No code is written now.

### 9.1 Files to modify (legacy `darkdelve.py`)
- [`darkdelve.py`](darkdelve.py:794) `Entity.armor_class` -> add `defense_value` &
  `armor_value` properties; keep `armor_class` as deprecated alias returning `defense_value`.
- [`darkdelve.py`](darkdelve.py:966) `CombatResolver.resolve_attack` -> rewrite per 5.2/5.3.
- [`darkdelve.py`](darkdelve.py:360) `CombatEvent` -> rename `d20_roll`->`d10_roll`,
  `target_ac`->`target_dv`; keep old names optional for one release.
- [`darkdelve.py`](darkdelve.py:391) `CombatEvent.__str__` -> `[Roll: {d10_roll} vs DV {target_dv}]`.
- [`darkdelve.py`](darkdelve.py:635) `Inventory.get_defense_bonus` -> document as AV source
  (semantics unchanged; just no longer added to hit TN).
- [`darkdelve.py`](darkdelve.py:447) `Item` -> optionally add `dodge_bonus`; `encumbrance`
  gains combat meaning.
- [`darkdelve.py`](darkdelve.py:647) `MobTemplate` -> add `armor_value: int = 0`.
- [`darkdelve.py`](darkdelve.py:2047) status line -> `DV {dv}  AV {av}`.
- [`darkdelve.py`](darkdelve.py:3582) debug panel -> add `DV`/`AV`.

### 9.2 Pseudocode sketches (design intent for Coder)
```
# Entity (replace armor_class block)
@property
def defense_value(self) -> int:
    return BASE_DV + self.reflex_mod + self.defense + getattr(self, 'dodge_bonus', 0)

@property
def armor_value(self) -> int:
    if self.inventory:
        return self.inventory.get_defense_bonus()
    return getattr(self, 'armor_value', 0)

@property
def reflex_mod(self) -> int:
    enc = sum(i.encumbrance for i in (self.inventory.equipment.values() if self.inventory else []) if i)
    return (self.stats['dex'] - 10)//2 - enc

# CombatResolver.resolve_attack (core)
d10 = random.randint(1, 10)
atk = d10 + attacker.reflex_mod + attacker.power + attacker.to_hit_bonus
dv  = defender.defense_value
if d10 == 10: result = HitResult.CRITICAL
elif d10 == 1: result = HitResult.CRITICAL_FAIL
elif atk >= dv: result = HitResult.HIT
else: result = HitResult.MISS
# damage per 5.3, clamp after AV, before CombatEvent
```

### 9.3 Migration / rebalance heuristic (must be tuned via playtest)
- Keep `power` semantics; ensure player `power` and monster `defense` grow at similar
  per-level rates so margins stay in `[-4, +4]`.
- **Compress old `defense`:** old `defense` values were inflated by the `+10` base. Map
  new `defense = round(old_defense * 0.4)` as a starting point, then playtest-tune.
- **Split old equipment `defense_bonus`:** ~30% becomes `dodge_bonus` (DV), ~70% becomes
  retained `defense_bonus` (now AV). Heavy armor gets high AV + high `encumbrance`.
- Set `BASE_DV = 6` (tunable in `config/`). Validate equal-foe hit rate ~50%.

### 9.4 UI changes
- Status line: `HP x/y  DV z  AV w  Level ...`
- Debug panel: add `DV`/`AV` lines; keep `Power`/`Defense` raw stats.
- Combat log: `[Roll: {d10_roll} vs DV {target_dv}] HIT!` etc.

### 9.5 Test approach (for Coder phase)
- Unit test `defense_value`/`armor_value` for player (with inventory) and mob (no inventory).
- Property test: for equal power/defense, `P(hit)` with `BASE_DV=6` is ~0.5 over 5000 rolls.
- Regression: a defender with `armor_value` high enough should yield `taken == MIN_DMG`
  (or 0) but still be HIT-able (result != MISS) — directly asserts the AC-41 bug is fixed.
- Clamp-order test: critical + AV + clamp produces value within `[MIN_DMG, max_hp//5]`.

---

## 10. Open Questions for Human Review

1. Accept `d10` + TN model (5.2), or prefer full opposed rolls (5.6)?
2. Should a critical ignore Armor Value (`CRIT_IGNORES_AV`)? (More satisfying, less realistic.)
3. `MIN_DMG = 1` (always chip damage) or `0` (armor can fully negate)? 
4. Confirm `BASE_DV = 6` as the tuning anchor, or prefer a different baseline.
5. Approve the `defense * 0.4` compression heuristic, or supply hand-tuned values?
6. OK to keep a deprecated `armor_class` alias for one release to limit test churn?

---

## Appendix A — Assumptions & References

- **Assumption A1:** Fuzion uses d10 + STAT + SKILL vs TN / opposed; AV absorbs DV.
  (Reconstructed from memory; the official guide at talsorian.com was unreachable.)
- **Assumption A2:** `REF` maps to DarkDelve `dex`; `WeaponSkill` to `power`; `Dodge` to
  `defense`. These are the closest existing analogues; a future skill system could refine.
- **Assumption A3:** `Item.encumbrance` is intended as a combat REF penalty (Fuzion style).
  Currently it is computed/stored but unused in `resolve_attack`.
- **Assumption A4:** `BASE_DV = 6` yields acceptable baseline hit rates; must be confirmed
  by playtest after rebalance.
- **Reference:** architecture/gotchas.md "Damage Cap Clamping Order" — clamp MUST remain
  after crit & AV subtraction, before `CombatEvent` construction.
- **Reference:** [`darkdelve.py`](darkdelve.py:964) `CombatResolver`, [`darkdelve.py`](darkdelve.py:748) `Entity`,
  [`darkdelve.py`](darkdelve.py:531) `Inventory`, [`darkdelve.py`](darkdelve.py:447) `Item`, [`darkdelve.py`](darkdelve.py:647) `MobTemplate`.

*End of design document. No source files were modified.*
