# LLM-Driven Roguelike Architecture Plan
## Implementation Guide for qwen2.5-coder:7b-instruct

**Status**: Plan Document for LLM Implementation  
**Target Model**: qwen2.5-coder:7b-instruct (8k context, 1080Ti)  
**Execution Environment**: Local Ollama Server  

## Vision
Transform DarkDelve into a game engine where the LLM fills in all creative details (symbols, mobs, items, level themes) while the game provides the structural framework for gameplay.

---

## IMPLEMENTATION INSTRUCTIONS FOR LLM

This document serves as the specification for implementing the complete roguelike system. Follow each section in order, implementing the code exactly as specified.

**Important Notes for LLM Implementation**:
- All new files should be well-commented for clarity
- Maintain consistency with existing code style (already in main.py)
- All imports must be included
- Include docstrings for all functions and classes
- Test each component before moving to next
- Preserve existing functionality - only add new systems

---

## PHASE 1: CORE SYSTEMS (Implementation Priority)

### 1.1 Symbol System (symbols.py - ALREADY PROVIDED)
**Status**: COMPLETE - File created, ready to use

**What it provides**:
- `ROGUELIKE_SYMBOLS` dictionary with all game symbols
- Color constants (RGB tuples)
- Helper functions: `get_symbol()`, `get_symbol_char()`, `get_symbol_color()`

**Implementation required**: NONE - Use as-is

---

### 1.2 Combat System (combat.py - ALREADY PROVIDED)
**Status**: COMPLETE - File created, ready to use

**Classes to implement in main.py**:
```python
from combat import CombatLog, CombatResolver, HitResult, format_combat_display

# In main():
combat_log = CombatLog()

# When player attacks enemy:
event = CombatResolver.resolve_attack(
    attacker_name=player.name,
    attacker_power=player.power,
    attacker_to_hit=equipment_bonus,
    defender_name=enemy.name,
    defender_ac=enemy_armor_class,
    weapon_damage=weapon_bonus,
    weapon_dice="1d8+1"
)

# Log and apply damage
combat_log.add_event(event)
if event.result != HitResult.MISS:
    enemy.hp -= event.damage

# Display combat info
print(event)  # Auto-formats the message
```

**Integration needed in main.py**:
- Import combat module
- Create `combat_log` instance
- Call `CombatResolver.resolve_attack()` during combat
- Display results using `format_combat_display()`

---

### 1.3 Inventory System (inventory.py - ALREADY PROVIDED)
**Status**: COMPLETE - File created, ready to use

**Update Entity class in main.py**:
```python
class Entity:
    def __init__(self, ...):
        # ... existing code ...
        
        # ADD THIS:
        from inventory import Inventory
        self.inventory = Inventory(max_weight=50)
    
    @property
    def armor_class(self):
        """Calculate effective AC with equipment bonuses"""
        base_ac = 10 + self.defense
        equipment_bonus = self.inventory.get_defense_bonus()
        return base_ac - (equipment_bonus // 2)
```

**Test inventory integration**:
```python
# In game loop on 'i' key press:
print(player.inventory.display())
```

---

### 1.4 Item System (items.py - TO BE CREATED)

**File**: `items.py`

**Implement these classes**:

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

class ItemRarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    LEGENDARY = "legendary"

@dataclass
class LootDrop:
    """Loot table entry"""
    item_name: str
    item_type: str
    rarity: ItemRarity
    probability: float  # 0.0 to 1.0
    min_count: int = 1
    max_count: int = 1

class ItemGenerator:
    """Generate items using Ollama"""
    
    def __init__(self):
        from ollama_client import get_ollama_client
        self.client = get_ollama_client()
    
    def generate_items(self, theme: str, count: int = 10) -> List[Dict]:
        """Generate items for a level theme
        
        Returns:
            List of item dictionaries with:
            - name, type, rarity, damage, defense, description
        """
        prompt = f"""Generate {count} roguelike items for a '{theme}' level.
        
Include mix of: common, uncommon, rare, legendary.
Formats: weapon, armor, potion, scroll, misc.

Respond ONLY with JSON:
{{
  "items": [
    {{
      "name": "Item Name",
      "type": "weapon|armor|potion|scroll|misc",
      "rarity": "common|uncommon|rare|legendary",
      "damage": 0,
      "defense": 0,
      "description": "one sentence",
      "special": "optional special effect"
    }}
  ]
}}"""
        
        result = self.client.generate_json(prompt, cache_key=f"items_{theme}")
        return result.get("items", []) if result else []
```

**Integration with mobs**:
```python
# When mob dies, generate loot:
if mob.is_dead:
    loot = ItemGenerator().generate_items(level_theme)
    for item_data in loot:
        # Create Item from data and add to level
        pass
```

---

### 1.5 Mob System (mobs.py - PARTIALLY PROVIDED)

**File**: `mobs.py` (needs completion)

**Implement missing class**:

```python
class LevelMobRoster:
    """Manages all mobs for current level"""
    
    def __init__(self, level_theme: str):
        self.theme = level_theme
        self.generator = MobGenerator(level_theme)
        self.roster: Optional[MobRoster] = None
        self.spawned_mobs = {}
    
    def initialize(self) -> bool:
        """Generate mob roster from Ollama
        
        Returns:
            True if successful, False if fallback used
        """
        self.roster = self.generator.generate_roster()
        
        if self.roster is None:
            # Fallback to defaults
            self.roster = create_default_roster()
            return False
        
        return True
    
    def spawn_mobs(self, count: int, x_range: tuple, y_range: tuple) -> List:
        """Spawn mobs in level at random positions
        
        Args:
            count: Number of mobs to spawn
            x_range: (min_x, max_x)
            y_range: (min_y, max_y)
        
        Returns:
            List of Entity objects
        """
        mobs = []
        for _ in range(count):
            template = random.choice(list(self.roster.mobs.values()))
            
            # Create Entity from template
            entity = Entity(
                x=random.randint(*x_range),
                y=random.randint(*y_range),
                char=template.symbol,
                color=template.color,
                name=template.name,
                blocks=True,
                hp=template.hp,
                power=template.power,
                defense=template.defense,
                intel_tier=tier_value(template.tier),
                is_commander=template.tier == MobTier.BOSS,
            )
            entity.template = template  # Keep reference
            mobs.append(entity)
        
        return mobs
```

---

### 1.6 Level Design System (levels.py - TO BE CREATED)

**File**: `levels.py`

**Implement**:

```python
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class LevelTheme:
    name: str
    difficulty: int  # 1-10
    description: str
    room_count: int
    trap_density: float  # 0.0-1.0
    treasure_density: float
    ambient_description: str

class LevelGenerator:
    """Generate level themes using Ollama"""
    
    def __init__(self):
        from ollama_client import get_ollama_client
        self.client = get_ollama_client()
    
    def generate_theme(self, level_num: int) -> Optional[LevelTheme]:
        """Generate theme for a level
        
        Args:
            level_num: The dungeon level (1-N)
        
        Returns:
            LevelTheme object or None
        """
        prompt = f"""Create a roguelike dungeon level theme for level {level_num}.

Respond ONLY with JSON:
{{
  "name": "theme name",
  "difficulty": {min(10, level_num + 1)},
  "description": "one sentence",
  "room_count": {5 + level_num},
  "trap_density": 0.{level_num * 10},
  "treasure_density": 0.{(10 - level_num) * 10},
  "ambient": "atmospheric description"
}}"""
        
        result = self.client.generate_json(
            prompt,
            cache_key=f"level_theme_{level_num}"
        )
        
        if result:
            return LevelTheme(**result)
        
        return None
```

---
