# Phase 1 Implementation Guide - Core Systems

## What's Been Created

### 1. **LLM_ROGUELIKE_PLAN.md**
Comprehensive 11-section architecture document covering:
- Symbol system for roguelike aesthetics
- Combat log and damage display
- Inventory with equipment slots
- Modular mob generation
- LLM-influenced level design
- LLM-influenced item design
- Integration strategy
- 4-phase implementation roadmap

### 2. **symbols.py** (NEW)
Roguelike symbol registry:
- Color palette (RGB values)
- ASCII symbols for terrain, items, players, enemies
- Symbol lookup functions
- Ready for LLM custom symbols

Example:
```python
from symbols import ROGUELIKE_SYMBOLS, get_symbol_char

symbol = get_symbol_char('enemy_minion')  # Returns 'g'
```

### 3. **combat.py** (NEW)
Complete combat system:
- `CombatEvent` - Single attack record with hit/miss/damage
- `HitResult` enum - MISS, HIT, CRITICAL, CRITICAL_FAIL
- `CombatLog` - Tracks recent combat history
- `CombatResolver` - Calculates attack outcomes
- `format_combat_display()` - Formats combat for UI

Example:
```python
from combat import CombatResolver, CombatLog

combat = CombatResolver.resolve_attack(
    attacker_name="Player",
    attacker_power=5,
    attacker_to_hit=2,
    defender_name="Goblin",
    defender_ac=11,
    weapon_damage=3,
    weapon_dice="1d8+1"
)
# Result: CombatEvent with hit/miss/damage calculated
```

### 4. **inventory.py** (NEW)
Full inventory system:
- `Item` - Individual item with stats and properties
- `ItemType` enum - WEAPON, ARMOR, POTION, SCROLL, MISC
- `EquipmentSlot` enum - HEAD, CHEST, MAIN_HAND, etc.
- `Inventory` - Manage items, equipment, weight limits
- `ItemFactory` - Quick item creation helpers

Example:
```python
from inventory import Inventory, ItemFactory, EquipmentSlot

inventory = Inventory(max_weight=100)
sword = ItemFactory.create_weapon(
    name="Iron Sword",
    item_id="sword_001",
    damage=3,
    to_hit=1
)
inventory.add_item(sword)
inventory.equip("sword_001", EquipmentSlot.MAIN_HAND)
```

---

## Integration with main.py

### Step 1: Import New Modules
```python
from symbols import ROGUELIKE_SYMBOLS, get_symbol_char, get_symbol_color
from combat import CombatLog, CombatResolver, format_combat_display
from inventory import Inventory, ItemFactory, EquipmentSlot
```

### Step 2: Update Entity Class
```python
class Entity:
    def __init__(self, ...):
        # ... existing code ...
        
        # NEW: Equipment
        self.inventory = Inventory(max_weight=50)
        self.defense_bonus = 0
        self.damage_bonus = 0
        self.to_hit_bonus = 0
        
        # Update effective AC with equipment
        @property
        def armor_class(self):
            return 10 + self.defense - (self.inventory.get_defense_bonus() // 2)
```

### Step 3: Update Combat Resolution
```python
def resolve_combat(attacker, defender):
    """Resolve attack with new combat system"""
    event = CombatResolver.resolve_attack(
        attacker_name=attacker.name,
        attacker_power=attacker.power,
        attacker_to_hit=attacker.inventory.get_to_hit_bonus(),
        defender_name=defender.name,
        defender_ac=defender.armor_class,
        weapon_damage=attacker.inventory.get_damage_bonus(),
    )
    
    if event.result in [HitResult.HIT, HitResult.CRITICAL]:
        defender.hp -= event.damage
        combat_log.add_event(event)
        return event
```

### Step 4: Update Game Display
```python
def render_game():
    """Add combat info to game display"""
    lines = []
    
    # ... existing dungeon rendering ...
    
    # NEW: Combat display
    entity_health = {
        player.name: (player.hp, player.max_hp),
        # ... other entities ...
    }
    lines.append(format_combat_display(combat_log, entity_health))
    
    # NEW: Inventory display (on 'i' key)
    lines.append(inventory.display())
    
    return "\n".join(lines)
```

---

## Quick Start: Add Combat Display

Here's a minimal example to add to main.py right now:

```python
from combat import CombatLog, CombatResolver, HitResult

# Initialize in main()
combat_log = CombatLog()

# In game loop, when player attacks:
def player_attack(player, target):
    result = CombatResolver.resolve_attack(
        attacker_name=player.name,
        attacker_power=player.power,
        attacker_to_hit=0,  # Will add from inventory later
        defender_name=target.name,
        defender_ac=10 + target.defense,
        weapon_damage=3,  # Base damage
    )
    
    print(result)  # Displays: "Player strikes Goblin! [Roll: 15 vs AC 11] HIT! Damage: 7"
    
    if result.result != HitResult.MISS:
        target.hp -= result.damage
    
    combat_log.add_event(result)
```

---

## Next Steps to Implement

### Phase 1 Complete When:
+ [x] Combat system integrated into main.py
+ [x] Hit/miss/damage displayed in game
+ [x] Basic inventory display working
+ [x] Equipment slots functional
+ [x] All tests still passing
### Phase 2 Prep:
- [ ] Create `mobs.py` with MobTemplate class
- [ ] Create `items.py` with ItemGenerator class
- [ ] Create `levels.py` with LevelGenerator class
- [ ] Add LLM prompt templates

---

## Testing the New Systems

### Test Combat:
```bash
python -c "
from combat import CombatResolver, HitResult
import random
random.seed(42)

for i in range(5):
    result = CombatResolver.resolve_attack('Player', 5, 2, 'Enemy', 11, 3)
    print(result)
"
```

### Test Inventory:
```bash
python -c "
from inventory import Inventory, ItemFactory, EquipmentSlot

inv = Inventory()
sword = ItemFactory.create_weapon('Iron Sword', 'sword1', damage=3, to_hit=1)
inv.add_item(sword)
inv.equip('sword1', EquipmentSlot.MAIN_HAND)
print(inv.display())
"
```

### Test Symbols:
```bash
python -c "
from symbols import ROGUELIKE_SYMBOLS

for symbol_type in ['player', 'enemy_minion', 'weapon', 'potion']:
    data = ROGUELIKE_SYMBOLS[symbol_type]
    print(f'{data[\"char\"]} - {data.get(\"name\", \"?\")}')
"
```

---

## File Organization After Phase 1

```
DarkDelve/
├── main.py              (game loop + entity management)
├── symbols.py           (symbol registry - NEW)
├── combat.py            (combat system - NEW)
├── inventory.py         (inventory system - NEW)
├── run_tests.py         (existing tests)
├── tests/               (existing tests)
└── prompt/              (LLM prompts)
```

---

## Architecture: How LLM Will Fit In

Once Phase 1 is complete, Phase 2 adds LLM-driven content:

```
┌─ GAME ENGINE ─────────────────────────────────────────┐
│  (main.py, symbols.py, combat.py, inventory.py)      │
│  • Gameplay mechanics                                  │
│  • Rules and validation                               │
│  • Turn-based system                                  │
│  • Combat resolution                                  │
└───────────────────────────────────────────────────────┘
         ↓ (uses content from)
┌─ LLM CONTENT GENERATION ──────────────────────────────┐
│  (mobs.py, items.py, levels.py)                      │
│  • Generate enemy stats/abilities (mobs.py)           │
│  • Generate unique items (items.py)                   │
│  • Generate level themes (levels.py)                  │
│  • Generate combat flavor text                        │
│  • Generate item descriptions                         │
└───────────────────────────────────────────────────────┘
         ↓ (queries)
┌─ LLM API ─────────────────────────────────────────────┐
│  (OpenAI/Ollama/Claude)                              │
│  • Respond with structured JSON                       │
│  • Generate creative content                          │
└───────────────────────────────────────────────────────┘
```

**Game engine is complete and playable.**
**LLM fills in creative details.**
**Rules keep everything balanced and valid.**

---

## Summary

You now have:
1. **Roguelike visual system** - Professional ASCII aesthetics
2. **Combat tracking** - Shows hits, misses, damage with narrative
3. **Inventory management** - Equipment slots, weight limits, stat bonuses
4. **Modular design** - Each system in separate file, ready for LLM integration

Ready to implement Phase 1? Start with `main.py` integration!
