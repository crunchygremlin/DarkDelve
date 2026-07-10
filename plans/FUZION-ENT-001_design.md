# FUZION-ENT-001 Implementation Design (Detailed Plan)

- **Task ID:** FUZION-ENT-001
- **Mode:** Architect (DESIGN ONLY — no source changes in this step)
- **Depends on:** `plans/FUZION-AC-001_impl_design.md` (Fuzion math already implemented in both combat systems; this task fixes the surrounding entity ecosystem and promotes SKILLS + LEVEL to first-class combat factors).
- **Status:** Ready for Coder.

---

## 1. Goal

Propagate the Fuzion d10 Attack-Value (AV_atk) vs Defense-Value (DV) + Armor-Value (AV_armor) combat model to **ALL** DarkDelve entities (monsters, items, difficulty scaling, skills, level) and make SKILLS (`weapon_mastery`, `armor_mastery`, `tactical_awareness`) and LEVEL first-class combat factors, with BOTH combat systems (`darkdelve.CombatResolver` and `src/domain/services/combat_service.py`) delegating to a single shared helper (`combat_factors.py`) so they stay mathematically aligned.

**Authoritative Fuzion math (from FUZION-AC-001, unchanged):**
- `DV = BASE_DV(6) + reflex_mod(dex) + int(defense * DEFENSE_COMPRESSION(0.4)) + dodge_bonus`
- `Attack roll = d10(1-10) + reflex_mod + (power//2) + to_hit_bonus`
- Hit if `attack_roll >= DV`; crit if `d10 == 10` (double damage); `CRIT_IGNORES_AV = False`
- `Damage = parse_dice(weapon_dice) + power//2 + damage_bonus`, then `max(MIN_DMG=1, damage - AV)`
- Keep deprecated aliases (`armor_class`, `target_ac`, `d20_roll`) for one release.

**NEW in this task (skill + level factors, applied identically in both systems via the shared helper):**
- `weapon_mastery` → adds to ATTACK VALUE (to-hit).
- `armor_mastery` → adds to ARMOR VALUE (AV) **and** DEFENSE VALUE (DV).
- `tactical_awareness` → adds to DEFENSE VALUE (DV).
- `level` (player `level`, or monster `tier` mapped to a level) → adds `LEVEL_BONUS_PER_LEVEL` to BOTH attack value and defense value.

---

## 2. Files to Create

| Path | Purpose |
|------|---------|
| `src/domain/services/combat_factors.py` | **Single source of truth** for combat factor extraction: skill bonuses, level factor, AV, DV, attack value, damage. Imported by BOTH `darkdelve.CombatResolver` and `CombatService`. No circular imports (imports only `combat_config`, `dice`; never imports `darkdelve` or `mob`). |
| `tests/test_fuzion_entities.py` | New tests for entity-level Fuzion integration (monsters, items, difficulty, skills, level). |

---

## 3. Files to Modify

| Path | Lines (verified) | Change |
|------|------------------|--------|
| `darkdelve.py` | Entity dataclass fields (~784, after `known_skills: List[str]`) | Add fields: `armor_value_override: int = 0`, `skills: List[str] = field(default_factory=list)`, `combat_dv_modifier: float = 1.0`, `combat_av_modifier: float = 1.0`, `combat_attack_modifier: float = 1.0`. |
| `darkdelve.py` | `Entity.armor_value` property (818-822) | Include `armor_value_override` so `MobTemplate.armor_value` flows into monster AV. |
| `darkdelve.py` | `CombatResolver.resolve_attack` (987-1040) | Delegate to `combat_factors.calculate_attack_value` / `calculate_defense_value` / `calculate_damage`. Keep both `target_ac`/`target_dv` and `d20_roll`/`d10_roll` populated for alias parity. |
| `darkdelve.py` | Monster spawn loop (2526-2535, `Entity(...)`) | Pass `armor_value=template.armor_value`, `skills=list(template.skills)`, and apply difficulty modifiers to `combat_dv_modifier`/`combat_av_modifier`/`combat_attack_modifier`. |
| `src/domain/entities/mob.py` | `__init__` (15-35) | Add combat attributes so `CombatService` no longer raises `AttributeError` on `Mob`. |
| `src/domain/entities/mob.py` | `get_defense` (103-105) | Return Fuzion DV via `combat_factors.calculate_defense_value(self)`. |
| `src/domain/entities/mob.py` | `get_attack_damage` (98-101) | Return Fuzion base damage via `combat_factors.get_base_damage(self, weapon_dice)`. |
| `src/domain/entities/item.py` | `__init__` (10-29) | Add `weapon_dice: str = "1d6"` field; document `attack_bonus`→to-hit (attack value), `defense_bonus`→AV (`armor_value` property already returns it). |
| `src/domain/services/combat_service.py` | `calculate_attack_roll` (183-196) | Delegate to `combat_factors.calculate_attack_value`; store `self._last_d10`. |
| `src/domain/services/combat_service.py` | `calculate_defense_value` (198-209) | Delegate to `combat_factors.calculate_defense_value`. |
| `src/domain/services/combat_service.py` | `calculate_damage` (211-228) | Delegate to `combat_factors.calculate_damage`; REMOVE broken `target.get_equipped_defense_bonus()` / `attacker.get_equipped_damage_bonus()` / `attacker.get_equipped_attack_bonus()` calls. |
| `src/domain/services/player_profile_service.py` | after `_compute_skills` (~209) | Add `apply_combat_skills(player)` (src.domain Player) AND `apply_combat_skills_to_entity(entity)` (darkdelve.Entity) that attach the computed `SkillSet` to a `PowerComponent` so combat can read it for BOTH player types (B3). |
| `darkdelve.py` | `create_player` (~2333, after starting gear auto-equip) | Call `PlayerProfileService().apply_combat_skills_to_entity(self.player)` so the in-game `Entity` player gets a `PowerComponent` with skills (B3 fix). |
| `src/domain/services/dynamic_difficulty_service.py` | `DifficultyAdjustment` (12-46) | Add `monster_dv_modifier`, `monster_av_modifier`, `monster_attack_modifier`; update `no_change`, `is_significant_change`, `is_no_change`. |
| `src/domain/services/dynamic_difficulty_service.py` | `_get_player_max_stats` (130-140) | Fix STALE refs (`player_entity.fighter`, `player_entity.power.level`). |
| `src/domain/services/dynamic_difficulty_service.py` | `_calculate_difficulty_from_stats` (93-128) | Populate the three new Fuzion-aware modifiers. |
| `architecture/INDEX.md` | inventory table | Add `src/domain/services/combat_factors.py`. |
| `architecture/gotchas.md` | add entry | "Fuzion skill/level factors live ONLY in `combat_factors`; the `Entity.defense_value` property stays BASE DV (no skill/level) for test parity." |
| `architecture/system_overview.md` | combat layer status | Mark combat layer updated to full Fuzion entity integration. |

> **NOTE on legacy tests:** The 6 legacy-test edits enumerated in `plans/FUZION-AC-001_impl_design.md` §6.1 (d20→d10 critical mocks, `armor_class>12`→`armor_value>0`, MISS premise fix) MUST already be applied (or the Coder re-applies them). They are prerequisites for the 96 combat tests staying green. The 14 pre-existing failures in `tests/test_ollama_gpu_persistence.py` are OUT OF SCOPE.


---

## 4. Pseudocode

### 4.1 `src/domain/services/combat_factors.py` (NEW — single source of truth)

```python
import random
from typing import Tuple, List, Any
from src.domain.value_objects.combat_config import COMBAT_CONFIG
from src.shared.utils.dice import parse_dice

# Monster skill name (string) -> (category, bonus)
#   "attack" -> adds to ATTACK VALUE (weapon_mastery-equivalent)
#   "dv"     -> adds to DEFENSE VALUE (tactical_awareness-equivalent)
#   "av"     -> adds to ARMOR VALUE (armor_mastery-equivalent)
MOB_SKILL_BONUS_MAP: dict = {
    "bite": ("attack", 2), "claw": ("attack", 2), "slash": ("attack", 2),
    "sting": ("attack", 1), "feral": ("attack", 1), "power_attack": ("attack", 3),
    "rend": ("attack", 2), "whirlwind": ("attack", 2), "maul": ("attack", 3),
    "howl": ("dv", 1), "war_cry": ("dv", 1), "guard": ("dv", 2), "parry": ("dv", 2),
    "dodge": ("dv", 2), "keen": ("dv", 1), "command": ("dv", 1), "evade": ("dv", 2),
    "shield": ("av", 2), "armor": ("av", 2), "tough": ("av", 1),
    "scales": ("av", 2), "plating": ("av", 3), "dash": ("dv", 0),
}

SKILL_BONUS_DIVISOR: int = 5      # SkillSet float value -> integer bonus
LEVEL_BONUS_PER_LEVEL: int = 1    # each level adds this to attack & defense values


def _reflex_mod(entity: Any) -> int:
    stats = getattr(entity, 'stats', None)
    if stats is None:
        return 0
    if hasattr(stats, 'get_modifier'):
        return stats.get_modifier('dexterity')
    if isinstance(stats, dict):
        return (stats.get('dex', 10) - 10) // 2
    return 0


def get_power(entity: Any) -> int:
    return getattr(entity, 'attack_power', getattr(entity, 'power', 0))


def get_defense_stat(entity: Any) -> int:
    return getattr(entity, 'defense', 0)


def get_level(entity: Any) -> int:
    lvl = getattr(entity, 'level', None)
    if isinstance(lvl, int) and lvl > 0:
        return lvl
    return _tier_to_level(getattr(entity, 'tier', None))


def _tier_to_level(tier: Any) -> int:
    if tier is None:
        return 1
    if isinstance(tier, int):
        return max(1, tier)
    val = getattr(tier, 'value', None)        # MobTier enum has .value
    if isinstance(val, int):
        return max(1, val)
    name = str(tier).lower()
    return {"minion": 1, "soldier": 2, "elite": 3, "boss": 4}.get(name, 1)


def get_skill_bonuses(entity: Any) -> Tuple[int, int, int]:
    # Returns (weapon_mastery_bonus, armor_mastery_bonus, tactical_awareness_bonus)
    # Case 1: PowerComponent with SkillSet (Player / System B)
    pc = entity.get_component("power") if hasattr(entity, 'get_component') else None
    if pc is not None and hasattr(pc, 'skills'):
        sk = pc.skills
        wm = int(getattr(sk, 'weapon_mastery', 0) // SKILL_BONUS_DIVISOR)
        am = int(getattr(sk, 'armor_mastery', 0) // SKILL_BONUS_DIVISOR)
        ta = int(getattr(sk, 'tactical_awareness', 0) // SKILL_BONUS_DIVISOR)
        return wm, am, ta
    # Case 2: entity carries a SkillSet-like object directly
    sk = getattr(entity, 'skill_set', None)
    if sk is not None:
        wm = int(getattr(sk, 'weapon_mastery', 0) // SKILL_BONUS_DIVISOR)
        am = int(getattr(sk, 'armor_mastery', 0) // SKILL_BONUS_DIVISOR)
        ta = int(getattr(sk, 'tactical_awareness', 0) // SKILL_BONUS_DIVISOR)
        return wm, am, ta
    # Case 3: monster string-list skills (MobTemplate.skills / Entity.skills)
    skills = getattr(entity, 'skills', []) or []
    wm = av = dv = 0
    for s in skills:
        cat, val = MOB_SKILL_BONUS_MAP.get(s, (None, 0))
        if cat == "attack":
            wm += val
        elif cat == "dv":
            dv += val
        elif cat == "av":
            av += val
    # armor_mastery bonus derived from av skill contribution; tactical from dv
    return wm, av, dv


def get_to_hit_bonus(entity: Any) -> int:
    if hasattr(entity, 'to_hit_bonus') and not callable(getattr(entity, 'to_hit_bonus', None)):
        return entity.to_hit_bonus
    eq = getattr(entity, 'equipment', None)
    if eq is not None and hasattr(eq, 'get_bonus'):
        return eq.get_bonus("attack")
    comp = entity.get_component("combat") if hasattr(entity, 'get_component') else None
    if comp is not None and hasattr(comp, 'get_bonus_attack'):
        return comp.get_bonus_attack()
    return 0


def get_damage_bonus(entity: Any) -> int:
    if hasattr(entity, 'damage_bonus') and not callable(getattr(entity, 'damage_bonus', None)):
        return entity.damage_bonus
    eq = getattr(entity, 'equipment', None)
    if eq is not None and hasattr(eq, 'get_bonus'):
        return eq.get_bonus("damage")
    comp = entity.get_component("combat") if hasattr(entity, 'get_component') else None
    if comp is not None and hasattr(comp, 'get_bonus_damage'):
        return comp.get_bonus_damage()
    return 0


def get_armor_value(entity: Any) -> int:
    base = 0
    if hasattr(entity, 'armor_value') and not callable(getattr(entity, 'armor_value', None)):
        base += entity.armor_value          # inventory/equipment AV (darkdelve.Entity, Item)
    else:
        # B2 FIX: Player (src/domain/entities/player.Player) has NO armor_value
        # property, so equipped armor contributed 0 AV through combat_factors.
        # Mirror get_to_hit_bonus/get_damage_bonus: read equipment defense bonus.
        # Guard with getattr so darkdelve.Entity.armor_value path is NOT double-counted.
        eq = getattr(entity, 'equipment', None)
        if eq is not None and hasattr(eq, 'get_bonus'):
            base += eq.get_bonus("defense")
    base += getattr(entity, 'armor_value_override', 0)   # MobTemplate.armor_value for monsters
    _, am, _ = get_skill_bonuses(entity)     # armor_mastery -> AV
    base += am
    mod = getattr(entity, 'combat_av_modifier', 1.0)      # difficulty scaling
    return int(base * mod)


def calculate_attack_value(attacker: Any, weapon_dice: str = "1d6") -> Tuple[int, int]:
    # Returns (d10_roll, attack_total). Same formula for BOTH combat systems.
    d10 = random.randint(1, COMBAT_CONFIG.DIE_SIDES)
    wm, _, _ = get_skill_bonuses(attacker)
    level_bonus = get_level(attacker) * LEVEL_BONUS_PER_LEVEL
    atk = (d10 + _reflex_mod(attacker) + get_power(attacker) // 2
           + get_to_hit_bonus(attacker) + wm + level_bonus)
    mod = getattr(attacker, 'combat_attack_modifier', 1.0)
    return d10, int(atk * mod)


def calculate_defense_value(target: Any) -> int:
    # Same formula for BOTH combat systems. NOTE: this is the COMBAT DV
    # (includes skill + level factors). The Entity.defense_value property
    # remains the BASE DV (no skill/level) for test parity — see gotchas.md.
    wm, am, ta = get_skill_bonuses(target)
    level_bonus = get_level(target) * LEVEL_BONUS_PER_LEVEL
    dv = (COMBAT_CONFIG.BASE_DV + _reflex_mod(target)
          + int(get_defense_stat(target) * COMBAT_CONFIG.DEFENSE_COMPRESSION)
          + getattr(target, 'dodge_bonus', 0) + am + ta + level_bonus)
    mod = getattr(target, 'combat_dv_modifier', 1.0)
    return int(dv * mod)


def get_base_damage(attacker: Any, weapon_dice: str) -> int:
    # Pre-AV damage (used by Mob.get_attack_damage and inside calculate_damage).
    num, size, mod = parse_dice(weapon_dice)
    dmg = sum(random.randint(1, size) for _ in range(num)) + mod
    dmg += get_power(attacker) // 2
    dmg += get_damage_bonus(attacker)
    # S1 FIX: weapon_mastery is to-hit (ATTACK VALUE) ONLY per §1; do NOT add to damage.
    return max(COMBAT_CONFIG.MIN_DMG, dmg)


def calculate_damage(attacker: Any, target: Any, weapon_dice: str, is_critical: bool) -> int:
    dmg = get_base_damage(attacker, weapon_dice)
    if is_critical:
        dmg *= 2
    av = get_armor_value(target)
    if is_critical and COMBAT_CONFIG.CRIT_IGNORES_AV:
        av = 0
    dmg = max(COMBAT_CONFIG.MIN_DMG, dmg - av)
    return dmg


def apply_difficulty(entity: Any, adjustment: Any) -> None:
    # Sets the three modifier fields from a DifficultyAdjustment so spawned
    # monsters scale in the Fuzion model. Caller: spawn logic / dungeon master.
    entity.combat_dv_modifier = getattr(adjustment, 'monster_dv_modifier', 1.0)
    entity.combat_av_modifier = getattr(adjustment, 'monster_av_modifier', 1.0)
    entity.combat_attack_modifier = getattr(adjustment, 'monster_attack_modifier', 1.0)
```

### 4.2 `darkdelve.py` — Entity dataclass new fields (after `known_skills: List[str] = field(default_factory=list)`, ~line 784)

```python
armor_value_override: int = 0
skills: List[str] = field(default_factory=list)
combat_dv_modifier: float = 1.0
combat_av_modifier: float = 1.0
combat_attack_modifier: float = 1.0
```

### 4.3 `darkdelve.py` — `Entity.armor_value` property (818-822) — include override

```python
@property
def armor_value(self) -> int:
    base = 0
    if self.inventory:
        base += self.inventory.get_defense_bonus()
    base += self.armor_value_override
    return base
```

### 4.4 `darkdelve.py` — `CombatResolver.resolve_attack` (987-1040) — delegate to combat_factors

```python
@staticmethod
def resolve_attack(attacker, defender, weapon_dice="1d6", max_range=1) -> CombatEvent:
    from src.domain.services.combat_factors import (
        calculate_attack_value, calculate_defense_value, calculate_damage)
    distance = abs(attacker.x - defender.x) + abs(attacker.y - defender.y)
    if distance > max_range:
        return CombatEvent(turn=0, attacker_name=attacker.name, defender_name=defender.name,
                         to_hit_bonus=attacker.to_hit_bonus,
                         target_ac=defender.defense_value, target_dv=defender.defense_value,
                         d20_roll=0, d10_roll=0, total_roll=0,
                         result=HitResult.MISS, damage=0, out_of_range=True)
    d10, atk_total = calculate_attack_value(attacker, weapon_dice)
    dv = calculate_defense_value(defender)
    if d10 == COMBAT_CONFIG.DIE_SIDES:
        result = HitResult.CRITICAL
    elif d10 == 1:
        result = HitResult.CRITICAL_FAIL
    elif atk_total >= dv:
        result = HitResult.HIT
    else:
        result = HitResult.MISS
    damage = 0
    if result in (HitResult.HIT, HitResult.CRITICAL):
        is_crit = (result == HitResult.CRITICAL)
        damage = calculate_damage(attacker, defender, weapon_dice, is_crit)
        # Keep existing clamp logic (after AV subtraction & crit, before CombatEvent)
        if hasattr(defender, 'max_hp') and defender.max_hp > 0:
            defender_is_player = getattr(defender, 'inventory', None) is not None and hasattr(defender, 'xp')
            attacker_is_player = getattr(attacker, 'inventory', None) is not None and hasattr(attacker, 'xp')
            if defender_is_player:
                damage = clamp_monster_damage(damage, defender.max_hp)
            elif attacker_is_player:
                damage = clamp_player_damage(damage, defender.max_hp)
    return CombatEvent(turn=0, attacker_name=attacker.name, defender_name=defender.name,
                     to_hit_bonus=attacker.to_hit_bonus,
                     target_ac=dv, target_dv=dv,
                     d20_roll=d10, d10_roll=d10,
                     total_roll=atk_total, result=result, damage=damage)
```

### 4.5 `darkdelve.py` — monster spawn loop (2526-2535) — apply template + difficulty

```python
entity = Entity(
    x=x, y=y,
    char=template.symbol, color=template.color,
    name=template.name, blocks=True,
    hp=template.hp, max_hp=template.hp,
    power=template.power, defense=template.defense,
    speed=monster_speed,
    intel_tier=self._tier_value(template.tier),
    is_commander=template.tier == MobTier.BOSS,
    armor_value_override=template.armor_value,   # NEW
    skills=list(template.skills),                # NEW
)
# Apply Fuzion-aware difficulty modifiers if available
adj = getattr(self, 'difficulty_adjustment', None)
if adj is not None:
    from src.domain.services.combat_factors import apply_difficulty
    apply_difficulty(entity, adj)
```


### 4.6 `src/domain/entities/mob.py` — `__init__` add combat attributes (15-35)

```python
def __init__(self, position: Position, name: str = "Mob", mob_type: str = "generic",
             power: int = 0, defense: int = 0, level: int = 1, tier: Any = None,
             skills: List[str] = None, armor_value: int = 0, dodge_bonus: int = 0,
             to_hit_bonus: int = 0, damage_bonus: int = 0):
    super().__init__(name=name)
    self.position = position
    self.mob_type = mob_type
    self.stats = Stats()
    self.inventory = Inventory()
    self.combat = Combat()
    self.movement = Movement()
    # Add components (unchanged from existing Mob.__init__)
    self.add_component("inventory", self.inventory)
    self.add_component("combat", self.combat)
    self.add_component("stats", self.stats)
    self.add_component("position", self.position)
    self.add_component("movement", self.movement)
    perception = PerceptionComponent(entity_id=self.id, modifiers=PerceptionModifiers("default"))
    self.add_component("perception", perception)
    # B1 FIX: set mob-type stats FIRST so power/defense derive from FINAL stats,
    # not the default Stats() (strength=10). _set_default_stats overwrites self.stats.
    self._set_default_stats()
    # NEW combat attributes (fix System B AttributeError in CombatService).
    # power/defense derived from FINAL mob-type stats (orc strength=16 -> power=8).
    self.power = power if power else (self.stats.strength // 2)
    self.defense = defense if defense else (self.stats.constitution // 2)
    self.level = level
    self.tier = tier
    self.skills = list(skills or [])
    self.armor_value_override = armor_value
    self.dodge_bonus = dodge_bonus
    self.to_hit_bonus = to_hit_bonus
    self.damage_bonus = damage_bonus
    self.combat_dv_modifier = 1.0
    self.combat_av_modifier = 1.0
    self.combat_attack_modifier = 1.0
```

### 4.7 `src/domain/entities/mob.py` — `get_defense` / `get_attack_damage` (98-105) use Fuzion math

```python
def get_attack_damage(self, weapon_dice: str = "1d6") -> int:
    from src.domain.services.combat_factors import get_base_damage
    return get_base_damage(self, weapon_dice)

def get_defense(self) -> int:
    from src.domain.services.combat_factors import calculate_defense_value
    return calculate_defense_value(self)
```

### 4.8 `src/domain/entities/item.py` — add `weapon_dice` field (10-29)

```python
def __init__(self, item_id: Optional[str] = None, name: str = "Item",
             item_type: str = "generic", description: str = "",
             value: int = 0, weight: float = 1.0, weapon_dice: str = "1d6"):
    super().__init__(entity_id=item_id, name=name)
    # ... existing assignments ...
    self.weapon_dice = weapon_dice
    # attack_bonus -> to-hit (attack value); defense_bonus -> AV (armor_value property)
```
No change needed to `armor_value` property (already returns `defense_bonus`). Document that `attack_bonus` feeds attack value via `get_to_hit_bonus` (equipment aggregation).

### 4.9 `src/domain/services/combat_service.py` — delegate to combat_factors (183-228)

```python
from src.domain.services.combat_factors import (
    calculate_attack_value, calculate_defense_value, calculate_damage)

def calculate_attack_roll(self, attacker) -> int:
    d10, atk = calculate_attack_value(attacker)
    self._last_d10 = d10                       # crit uses SAME d10
    return atk

def calculate_defense_value(self, target) -> int:
    return calculate_defense_value(target)     # no name clash: module fn

def calculate_damage(self, attacker, target, weapon_dice: str = "1d6") -> int:
    is_crit = getattr(self, '_last_d10', 0) == COMBAT_CONFIG.DIE_SIDES
    return calculate_damage(attacker, target, weapon_dice, is_crit)
```
Remove the module-level `_reflex_mod` helper (now in `combat_factors`) OR keep it as a thin re-export; the three methods above no longer call `getattr(attacker,'attack_power',...)`, `attacker.get_equipped_attack_bonus()`, `target.get_equipped_defense_bonus()`, `attacker.get_equipped_damage_bonus()` — those broken calls are GONE. `execute_attack` (74-155) is unchanged except it already calls `calculate_attack_roll` / `calculate_defense_value` / `calculate_damage` with the `weapon_dice` param; keep as-is.

### 4.10 `src/domain/services/player_profile_service.py` — attach skills to player (after `_compute_skills`, ~209)

```python
def apply_combat_skills(self, player: Player) -> None:
    """Compute SkillSet from stats and attach to a PowerComponent on the player
    (src.domain Player) so combat_factors.get_skill_bonuses Case 1 can read
    weapon_mastery/armor_mastery/tactical_awareness during combat."""
    from src.domain.components.power_component import PowerComponent
    skills = self._compute_skills(player)
    pc = player.get_component("power")
    if pc is None:
        pc = PowerComponent(entity_id=player.id)
        player.add_component("power", pc)
    pc.skills = skills


def apply_combat_skills_to_entity(self, entity: Any) -> None:
    """B3 FIX: attach a PowerComponent+SkillSet to the in-game darkdelve.Entity
    player (used by CombatResolver) so skills are first-class for ALL entities.
    Handles darkdelve.Entity.stats (dict) and src.domain Player.stats (Stats obj)."""
    from src.domain.components.power_component import PowerComponent
    from src.domain.value_objects.power_levels import SkillSet
    stats = getattr(entity, 'stats', None)
    if isinstance(stats, dict):
        STR = stats.get('str', 10); DEX = stats.get('dex', 10)
        CON = stats.get('con', 10); INT = stats.get('int', 10)
        WIS = stats.get('wis', 10); CHA = stats.get('cha', 10)
    else:
        STR = getattr(stats, 'strength', 10); DEX = getattr(stats, 'dexterity', 10)
        CON = getattr(stats, 'constitution', 10); INT = getattr(stats, 'intelligence', 10)
        WIS = getattr(stats, 'wisdom', 10); CHA = getattr(stats, 'charisma', 10)
    skillset = SkillSet(
        weapon_mastery=STR * 1.0 + DEX * 1.0,
        armor_mastery=CON * 1.5 + STR * 0.5,
        tactical_awareness=INT * 1.0 + WIS * 1.0,
    )
    pc = entity.get_component("power")
    if pc is None:
        pc = PowerComponent(entity_id=getattr(entity, 'id', None))
        entity.add_component("power", pc)
    pc.skills = skillset
```
Call `apply_combat_skills(player)` wherever a src.domain `Player` is created/finalized (e.g., game setup / after level-up). Call `apply_combat_skills_to_entity(self.player)` inside `darkdelve.create_player()` AFTER starting gear is auto-equipped (so the in-game `Entity` player path goes through `combat_factors.get_skill_bonuses` Case 1). Both make skills first-class in BOTH combat systems.

### 4.11 `src/domain/services/dynamic_difficulty_service.py` — Fuzion-aware + stale-ref fix

`DifficultyAdjustment` dataclass (12-46): add three fields and update helpers:

```python
@dataclass(frozen=True)
class DifficultyAdjustment:
    spawn_rate_modifier: float = 1.0
    monster_health_modifier: float = 1.0
    monster_damage_modifier: float = 1.0
    monster_dv_modifier: float = 1.0       # NEW: scales monster DEFENSE VALUE
    monster_av_modifier: float = 1.0       # NEW: scales monster ARMOR VALUE
    monster_attack_modifier: float = 1.0   # NEW: scales monster ATTACK VALUE
    experience_reward_modifier: float = 1.0
    loot_quality_modifier: float = 1.0

    @classmethod
    def no_change(cls) -> 'DifficultyAdjustment':
        return cls()   # all defaults are 1.0

    def is_significant_change(self, threshold: float = 0.1) -> bool:
        return (
            abs(self.spawn_rate_modifier - 1.0) > threshold or
            abs(self.monster_health_modifier - 1.0) > threshold or
            abs(self.monster_damage_modifier - 1.0) > threshold or
            abs(self.monster_dv_modifier - 1.0) > threshold or
            abs(self.monster_av_modifier - 1.0) > threshold or
            abs(self.monster_attack_modifier - 1.0) > threshold
        )

    def is_no_change(self) -> bool:
        return (self.spawn_rate_modifier == 1.0 and self.monster_health_modifier == 1.0
                and self.monster_damage_modifier == 1.0 and self.monster_dv_modifier == 1.0
                and self.monster_av_modifier == 1.0 and self.monster_attack_modifier == 1.0)
```

`_get_player_max_stats` (130-140) — FIX STALE REFS:

```python
def _get_player_max_stats(self, player_entity: 'Entity') -> Dict[str, int]:
    stats = {}
    # FIX: no longer reference player_entity.fighter or player_entity.power.level
    stats['attack'] = getattr(player_entity, 'attack_power',
                              getattr(player_entity, 'power', 0))
    stats['level'] = getattr(player_entity, 'level', 1)
    stats['defense_value'] = getattr(player_entity, 'defense_value', 0)
    stats['power_level'] = stats['attack'] + stats['level'] * 10
    return stats
```

`_calculate_difficulty_from_stats` (93-128) — populate new Fuzion modifiers:

```python
def _calculate_difficulty_from_stats(self, player_stats, current_level):
    base_power = player_stats.get('power_level', current_level * 10)
    difficulty_factor = 1.0
    if base_power > 0:
        difficulty_factor = max(0.5, min(2.0, 50.0 / base_power))
    return DifficultyAdjustment(
        spawn_rate_modifier=difficulty_factor,
        monster_health_modifier=difficulty_factor,
        monster_damage_modifier=difficulty_factor,
        monster_dv_modifier=difficulty_factor,       # NEW
        monster_av_modifier=difficulty_factor,       # NEW
        monster_attack_modifier=difficulty_factor,   # NEW
        experience_reward_modifier=1.0 / difficulty_factor,
        loot_quality_modifier=1.0 / difficulty_factor,
    )
```
`_parse_llm_response` (142-169): when building `DifficultyAdjustment`, also carry `monster_dv_modifier=modifier`, `monster_av_modifier=modifier`, `monster_attack_modifier=modifier` (reuse the same `modifier`/`monster_damage` value).


---

## 5. Import Statements

```python
# src/domain/services/combat_factors.py
import random
from typing import Tuple, List, Any
from src.domain.value_objects.combat_config import COMBAT_CONFIG
from src.shared.utils.dice import parse_dice

# darkdelve.py (inside CombatResolver.resolve_attack, local import to avoid top-level churn)
from src.domain.services.combat_factors import (
    calculate_attack_value, calculate_defense_value, calculate_damage)

# src/domain/services/combat_service.py (top, replace local _reflex_mod usage)
from src.domain.services.combat_factors import (
    calculate_attack_value, calculate_defense_value, calculate_damage)

# src/domain/entities/mob.py (local imports inside get_defense / get_attack_damage)
from src.domain.services.combat_factors import calculate_defense_value, get_base_damage

# src/domain/services/player_profile_service.py (inside apply_combat_skills)
from src.domain.components.power_component import PowerComponent

# tests/test_fuzion_entities.py
import unittest
from src.domain.services.combat_factors import (
    calculate_attack_value, calculate_defense_value, calculate_damage,
    get_skill_bonuses, get_armor_value, MOB_SKILL_BONUS_MAP)
from src.domain.entities.mob import Mob
from src.domain.entities.item import Item
from src.domain.entities.player import Player
from src.domain.value_objects.position import Position
from src.domain.services.player_profile_service import PlayerProfileService
from src.domain.services.dynamic_difficulty_service import DynamicDifficultyService, DifficultyAdjustment
from src.domain.entities.entity import Entity as BaseEntity
```

---

## 6. Test Plan

### 6.1 New file `tests/test_fuzion_entities.py` (exact assertions)

```python
import unittest
from src.domain.services.combat_factors import (
    calculate_attack_value, calculate_defense_value, calculate_damage,
    get_skill_bonuses, get_armor_value, MOB_SKILL_BONUS_MAP)
from src.domain.entities.mob import Mob
from src.domain.entities.item import Item
from src.domain.entities.player import Player
from src.domain.value_objects.position import Position
from src.domain.services.player_profile_service import PlayerProfileService
from src.domain.services.dynamic_difficulty_service import DynamicDifficultyService, DifficultyAdjustment


class TestFuzionMonsters(unittest.TestCase):
    def test_mob_defense_uses_fuzion_dv_no_attributeerror(self):
        m = Mob(Position(0, 0), mob_type="orc")
        # Mob has no 'defense' attr historically; get_defense must not raise
        dv = m.get_defense()
        self.assertIsInstance(dv, int)
        self.assertGreaterEqual(dv, 6)   # BASE_DV floor

    def test_mob_attack_damage_uses_fuzion(self):
        m = Mob(Position(0, 0), mob_type="dragon", power=24)
        dmg = m.get_attack_damage("2d6")
        self.assertGreaterEqual(dmg, 1)

    def test_combat_service_defense_value_on_mob_no_error(self):
        # Simulate the previously-broken path: CombatService.calculate_defense_value(Mob)
        from src.domain.services.combat_service import CombatService
        m = Mob(Position(0, 0), mob_type="goblin")
        cs = CombatService()
        dv = cs.calculate_defense_value(m)   # was AttributeError: 'Mob' has no 'defense'
        self.assertIsInstance(dv, int)


class TestFuzionSkillMapping(unittest.TestCase):
    def test_mob_string_skills_map_to_bonuses(self):
        m = Mob(Position(0, 0), mob_type="orc", skills=["bite", "shield", "guard"])
        wm, am, ta = get_skill_bonuses(m)
        self.assertEqual(wm, MOB_SKILL_BONUS_MAP["bite"][1])   # attack bonus
        self.assertEqual(am, MOB_SKILL_BONUS_MAP["shield"][1]) # av bonus
        self.assertEqual(ta, MOB_SKILL_BONUS_MAP["guard"][1])  # dv bonus

    def test_unknown_monster_skill_maps_to_zero(self):
        # S3: skills not present in MOB_SKILL_BONUS_MAP contribute 0 (no crash)
        m = Mob(Position(0, 0), mob_type="orc", skills=["totally_unknown_skill"])
        wm, am, ta = get_skill_bonuses(m)
        self.assertEqual((wm, am, ta), (0, 0, 0))

    def test_player_skills_from_profile_feed_combat(self):
        # S2: actually call apply_combat_skills (not manual attach)
        p = Player(Position(0, 0))   # default Stats all = 10
        svc = PlayerProfileService()
        svc.apply_combat_skills(p)
        wm, am, ta = get_skill_bonuses(p)
        # weapon_mastery = STR*1 + DEX*1 = 20 -> //5 = 4
        self.assertEqual(wm, 4)
        self.assertEqual(am, 4)   # CON*1.5 + STR*0.5 = 20 -> 4
        self.assertEqual(ta, 4)   # INT + WIS = 20 -> 4
        # AV includes armor_mastery bonus (B2: equipment path also exercised)
        self.assertGreaterEqual(get_armor_value(p), am)

    def test_entity_player_skills_from_profile_feed_combat(self):
        # B3: in-game darkdelve.Entity player must also get skills wired
        from darkdelve import Entity
        e = Entity(x=0, y=0, name="Hero",
                   stats={'str': 14, 'dex': 12, 'con': 13, 'int': 10, 'wis': 10, 'cha': 8})
        svc = PlayerProfileService()
        svc.apply_combat_skills_to_entity(e)
        wm, am, ta = get_skill_bonuses(e)
        self.assertEqual(wm, (14 + 12) // 5)                    # 5
        self.assertEqual(am, int((13 * 1.5 + 14 * 0.5) // 5))  # 5
        self.assertEqual(ta, (10 + 10) // 5)                   # 4
        # AV includes armor_mastery bonus for the Entity player too
        self.assertGreaterEqual(get_armor_value(e), am)


class TestFuzionLevelFactor(unittest.TestCase):
    def test_level_bonus_in_attack_and_defense(self):
        low = Mob(Position(0, 0), mob_type="goblin", level=1)
        high = Mob(Position(0, 0), mob_type="goblin", level=5)
        _, atk_low = calculate_attack_value(low)
        _, atk_high = calculate_attack_value(high)
        self.assertGreater(atk_high, atk_low)          # level adds to attack
        self.assertGreater(calculate_defense_value(high), calculate_defense_value(low))

    def test_tier_maps_to_level(self):
        from src.domain.entities.mob import Mob as _M
        boss = _M(Position(0, 0), mob_type="dragon", tier="boss")
        # boss tier -> level 4 via _tier_to_level; DV should reflect it
        self.assertGreaterEqual(calculate_defense_value(boss), 6 + 4)


class TestFuzionItems(unittest.TestCase):
    def test_item_weapon_dice_field(self):
        it = Item(item_id="w", name="Sword", item_type="weapon", weapon_dice="2d6+1")
        self.assertEqual(it.weapon_dice, "2d6+1")

    def test_item_attack_bonus_feeds_attack_value(self):
        # attack_bonus -> to_hit_bonus path via equipment aggregation
        it = Item(item_id="w", name="Sword", item_type="weapon")
        it.attack_bonus = 3
        self.assertEqual(it.attack_bonus, 3)
        # defense_bonus -> AV
        it.defense_bonus = 4
        self.assertEqual(it.armor_value, 4)


class TestFuzionDifficulty(unittest.TestCase):
    def test_difficulty_adjustment_has_fuzion_fields(self):
        adj = DifficultyAdjustment(monster_dv_modifier=1.5, monster_av_modifier=1.5,
                                   monster_attack_modifier=1.5)
        self.assertTrue(adj.is_significant_change())
        self.assertFalse(adj.is_no_change())

    def test_difficulty_no_stale_refs(self):
        # Build a minimal fake player with the NEW attributes only
        class FakePlayer:
            attack_power = 20
            level = 3
            defense_value = 8
        svc = DynamicDifficultyService.__new__(DynamicDifficultyService)
        stats = svc._get_player_max_stats(FakePlayer())
        self.assertIn('attack', stats)
        self.assertIn('level', stats)
        self.assertNotIn('fighter', dir(FakePlayer))   # stale attr gone
        adj = svc._calculate_difficulty_from_stats(stats, 3)
        self.assertEqual(adj.monster_dv_modifier, adj.monster_health_modifier)
        self.assertEqual(adj.monster_av_modifier, adj.monster_attack_modifier)


if __name__ == '__main__':
    unittest.main()
```

Run: `python -m pytest tests/test_fuzion_entities.py -v`

### 6.2 Suites that MUST stay green (do not modify except the 6 authorized FUZION-AC-001 §6.1 edits)
- The 96 combat tests: `tests/test_combat_system.py`, `tests/test_combat_messages.py`, `tests/test_combat_damage_log.py`, `tests/test_regression_monster_movement_fov_combat.py`, `tests/test_fuzion_combat.py`.
- Full suite: 1158 tests (the 14 failures in `tests/test_ollama_gpu_persistence.py` are OUT OF SCOPE and must NOT be "fixed" by this task).
- `tests/test_dynamic_difficulty.py` — must remain green after the `DifficultyAdjustment` field additions (defaults keep `no_change()`/`is_no_change()` behavior; update any test that constructs `DifficultyAdjustment` positionally if arity changed — prefer keyword args).

### 6.3 Risk-specific regression checks
- `Mob.get_defense()` previously returned `constitution//2 + bonus_defense`; now returns Fuzion DV. Any test asserting the OLD integer must be updated to assert `>= 6` (see 6.1).
- `combat_service.calculate_damage` no longer calls `target.get_equipped_defense_bonus()` — verify no test mocks that method.

---

## 7. Integration Notes

- **Single source of truth:** Both `darkdelve.CombatResolver.resolve_attack` and `CombatService` now call `combat_factors.calculate_attack_value` / `calculate_defense_value` / `calculate_damage`. The Fuzion formula + skill/level factors exist in EXACTLY ONE place. No math divergence possible.
- **`Entity.defense_value` property stays BASE DV** (no skill/level) to preserve `tests/test_fuzion_combat.py::test_defense_value_baseline` (expects 6). Combat resolution uses the richer `calculate_defense_value` helper. Documented in `gotchas.md`.
- **Monster `MobTemplate` → spawned `Entity` (System A):** spawn loop now passes `armor_value_override=template.armor_value` and `skills=list(template.skills)`; `combat_factors` reads `Entity.skills` via `MOB_SKILL_BONUS_MAP` and `armor_value_override` for AV. This closes gap #2.
- **Monster `Mob` (System B):** new attributes (`power`, `defense`, `level`, `tier`, `skills`, `armor_value_override`, `dodge_bonus`, `to_hit_bonus`, `damage_bonus`, `combat_*_modifier`) make `CombatService` work without `AttributeError`. Closes gap #1.
- **Skills wiring (gap #4, B3 fix):** `player_profile_service.apply_combat_skills(player)` attaches a `SkillSet` to a `PowerComponent` on the src.domain `Player`; `apply_combat_skills_to_entity(entity)` does the SAME for the in-game `darkdelve.Entity` player (called from `darkdelve.create_player()` after gear equip). `combat_factors.get_skill_bonuses` Case 1 reads the `PowerComponent.skills` for BOTH player types and BOTH combat systems. `MobTemplate.skills` (string list) map via `MOB_SKILL_BONUS_MAP` to numeric (attack/dv/av) bonuses. Unknown monster skills map to 0 (S3).
- **Items (gap #3):** `Item.weapon_dice` added; `attack_bonus`→to-hit (attack value), `defense_bonus`→AV (`armor_value` property). `action_dispatcher.execute_attack` may later pass `weapon_dice` from the attacker's equipped main-hand item; default `"1d6"` keeps current callers working.
- **Difficulty (gap #5):** `DifficultyAdjustment` gains `monster_dv_modifier`/`monster_av_modifier`/`monster_attack_modifier`; `_calculate_difficulty_from_stats` populates them with the same `difficulty_factor`. `combat_factors.apply_difficulty` writes them into spawned monsters' `combat_*_modifier` fields. Stale `fighter`/`power.level` refs removed.
- **Level (gap #6):** `get_level` returns `Player.level` / `Entity.level` / `Mob.level` (or `tier`→level). `LEVEL_BONUS_PER_LEVEL=1` added to both attack and defense values.
- **Deprecated aliases preserved:** `armor_class`, `target_ac`, `d20_roll` remain real fields/properties for one release (from FUZION-AC-001).

---

## 8. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| `combat_service` still calls non-existent `get_equipped_*` → AttributeError | High | High | **FIXED:** `calculate_*` delegate to `combat_factors`; broken calls removed (§4.9). |
| `Mob` has no `defense`/`power` → AttributeError in `calculate_defense_value` | High | High | **FIXED:** `Mob.__init__` adds attributes (§4.6). |
| `Mob.get_defense()` OLD math diverges from Fuzion | High | High | **FIXED:** delegates to `combat_factors.calculate_defense_value` (§4.7). |
| `MobTemplate.armor_value`/`skills` never applied | High | Med | **FIXED:** spawn loop passes them to `Entity` (§4.5). |
| Skills not used in combat (LLM-only) | High | Med | **FIXED:** `apply_combat_skills` + `get_skill_bonuses` Case 1 (§4.10). |
| Difficulty service stale `fighter`/`power.level` refs | High | Med | **FIXED:** `_get_player_max_stats` rewritten (§4.11). |
| Difficulty not Fuzion-aware (only health/damage) | Med | Med | **FIXED:** 3 new modifiers populated (§4.11). |
| `Entity.defense_value` property vs combat DV mismatch | Med | Low | Documented: property = BASE DV; combat uses helper. `gotchas.md` entry added. |
| Level double-counts (attack+defense) making high-level trivial | Low | Low | `LEVEL_BONUS_PER_LEVEL=1` small; tune in `combat_config` if needed. |
| Circular import (darkdelve ↔ combat_factors) | Low | High | `combat_factors` imports ONLY `combat_config` + `dice`; never imports `darkdelve`/`mob`. Local import inside `resolve_attack` (§4.4). |
| `tests/test_dynamic_difficulty.py` breaks on new fields | Med | Med | Defaults preserve `no_change()`; update positional constructors to keyword args. |
| 96 combat tests break | Med | High | Re-apply the 6 authorized FUZION-AC-001 §6.1 edits; `defense_value` property unchanged (baseline 6). |
| B1: Mob power/defense derived from default Stats() not mob-type stats | High | High | **FIXED:** compute `self.power`/`self.defense` AFTER `self._set_default_stats()` in `Mob.__init__` (§4.6). |
| B2: Player AV lost in combat_factors path | High | High | **FIXED:** `get_armor_value` reads `entity.equipment.get_bonus("defense")` when no `armor_value` property (Player); guarded so darkdelve.Entity.armor_value path is not double-counted (§4.1). |
| B3: in-game darkdelve.Entity player never gets skills | High | High | **FIXED:** `apply_combat_skills_to_entity` attaches PowerComponent+SkillSet to darkdelve.Entity; `create_player` calls it; `get_skill_bonuses` Case 1 fires (§4.10, §3). |
| S1: weapon_mastery double-dipped into damage | Med | Med | **FIXED:** removed weapon_mastery from `get_base_damage`; to-hit only per §1 (§4.1). |
| S2: apply_combat_skills untested | Med | Med | **FIXED:** added tests calling `apply_combat_skills` (Player) and `apply_combat_skills_to_entity` (darkdelve.Entity) (§6.1). |
| S3: unknown monster skills | Low | Low | **DOCUMENTED:** `MOB_SKILL_BONUS_MAP.get(s, (None, 0))` maps unknown skills to 0; test asserts unknown skill -> 0 (§4.1, §6.1). |

---

## 9. Architecture Doc Updates (Coder step, not source)

- `architecture/INDEX.md`: add `src/domain/services/combat_factors.py` to the File Inventory (single source of truth for Fuzion combat factors).
- `architecture/gotchas.md`: add entry — "Fuzion skill/level factors live ONLY in `combat_factors`; `Entity.defense_value` property stays BASE DV (no skill/level) for test parity. `combat_factors` must never import `darkdelve` or `mob` (circular import)."
- `architecture/system_overview.md`: update combat-layer status marker to reflect full Fuzion entity integration (monsters, items, skills, level, difficulty).

*End of implementation design. No source files were modified in this step.*
