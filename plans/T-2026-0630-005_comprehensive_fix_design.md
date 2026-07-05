# T-2026-0630-005 Comprehensive Fix Design Document

## Goal

Fix the 3 missing features from the original T-2026-0630-005 implementation: (B) Drop bug fix - add 'd' key handler to show_inventory, (C) Use bug fix - add 'u' key handler to show_inventory, (D) Accessory slots - add RING/NECK to EquipmentSlot enum, ACCESSORY to ItemType enum, and slot mapping in _get_valid_slots_for_item, plus add missing imports for damage caps and emoji functions.

---

## Files to Create

None - all changes are modifications to existing files.

---

## Files to Modify

1. **`darkdelve.py`** (multiple sections):
   - Lines 35-36: Add imports for damage caps and emoji functions
   - Lines 328-336: `EquipmentSlot` enum — add `RING` and `NECK` slots
   - Lines 319-326: `ItemType` enum — add `ACCESSORY = "accessory"`
   - Lines 582-599: `Inventory._get_valid_slots_for_item()` — add ring/neck mapping for ACCESSORY items
   - Lines 890-957: `CombatResolver.resolve_attack()` — add damage clamping logic
   - Lines 3099-3129: `Game.show_inventory()` — add 'd' and 'u' key handlers
   - Lines 3205-3267: `Game.render_inventory()` — verify it uses the new imports (already uses get_item_emoji)

2. **`tests/test_inventory_description_panel.py`** (lines 65-77):
   - Update test assertions to verify the new key handlers exist

---

## Pseudocode

### 1. Import Statements (darkdelve.py, after line 35)

```python
# Import damage balance clamping
from src.domain.value_objects.damage_caps import clamp_monster_damage, clamp_player_damage

# Import emoji lookup tables
from src.presentation.item_emoji import get_item_emoji
from src.presentation.monster_emoji import get_monster_emoji
```

### 2. EquipmentSlot Enum (darkdelve.py, lines 328-336)

```python
class EquipmentSlot(Enum):
    HEAD = "head"
    CHEST = "chest"
    BODY = "chest"
    HANDS = "hands"
    LEGS = "legs"
    FEET = "feet"
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    RING = "ring"
    NECK = "neck"
```

### 3. ItemType Enum (darkdelve.py, lines 319-326)

```python
class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    POTION = "potion"
    SCROLL = "scroll"
    CONSUMABLE = "potion"
    FOOD = "food"
    ACCESSORY = "accessory"
    MISC = "misc"
```

### 4. Inventory._get_valid_slots_for_item() (darkdelve.py, lines 582-599)

```python
def _get_valid_slots_for_item(self, item: Item) -> List[EquipmentSlot]:
    if item.item_type == ItemType.WEAPON:
        return [EquipmentSlot.MAIN_HAND, EquipmentSlot.OFF_HAND]
    elif item.item_type == ItemType.ARMOR:
        name_lower = item.name.lower()
        if "helm" in name_lower or "hat" in name_lower or "cap" in name_lower:
            return [EquipmentSlot.HEAD]
        elif "chest" in name_lower or "mail" in name_lower or "armor" in name_lower or "plate" in name_lower or "robe" in name_lower or "shirt" in name_lower:
            return [EquipmentSlot.CHEST]
        elif "glove" in name_lower or "gauntlet" in name_lower or "hand" in name_lower:
            return [EquipmentSlot.HANDS]
        elif "leg" in name_lower or "pant" in name_lower or "greave" in name_lower:
            return [EquipmentSlot.LEGS]
        elif "boot" in name_lower or "shoe" in name_lower or "sandal" in name_lower:
            return [EquipmentSlot.FEET]
        elif "shield" in name_lower:
            return [EquipmentSlot.OFF_HAND]
    elif item.item_type == ItemType.ACCESSORY:
        name_lower = item.name.lower()
        if "ring" in name_lower:
            return [EquipmentSlot.RING]
        elif "amulet" in name_lower or "necklace" in name_lower or "pendant" in name_lower:
            return [EquipmentSlot.NECK]
    return []
```

### 5. CombatResolver.resolve_attack() (darkdelve.py, lines 890-957)

Add clamping logic after damage calculation (after line 945, before line 947):

```python
# At the end of resolve_attack, before `return CombatEvent(...)`:
# Apply balance clamping
if hasattr(defender, 'max_hp') and defender.max_hp > 0:
    # Check if attacker is the player (player attacking monster → floor)
    # Check if defender is the player (monster attacking player → cap)
    # We determine "is player" by checking for a flag or inventory presence
    attacker_is_player = getattr(attacker, 'inventory', None) is not None and hasattr(attacker, 'xp')
    defender_is_player = getattr(defender, 'inventory', None) is not None and hasattr(defender, 'xp')
    
    if defender_is_player:
        # Monster attacking player → cap damage
        damage = clamp_monster_damage(damage, defender.max_hp)
    elif attacker_is_player:
        # Player attacking monster → floor damage
        damage = clamp_player_damage(damage, defender.max_hp)
```

### 6. Game.show_inventory() (darkdelve.py, lines 3099-3129)

Add 'd' and 'u' key handlers after the ENTER handler (after line 3128):

```python
elif event.sym == tcod.event.KeySym.D:
    # Drop selected item
    if self.player and self.player.inventory:
        item = self.player.inventory.get_item(self.inventory_selection)
        if item:
            if item.equipped:
                self.add_message("Unequip the item before dropping it.")
            else:
                # Remove from inventory and place on ground
                self.player.inventory.remove_item(item.id)
                self.drop_item(item, self.player.x, self.player.y)
                self.add_message(f"Dropped {item.name}.")
                # Adjust selection if needed
                item_count = len(self.player.inventory.items)
                if item_count > 0 and self.inventory_selection >= item_count:
                    self.inventory_selection = item_count - 1

elif event.sym == tcod.event.KeySym.U:
    # Use selected item
    if self.player and self.player.inventory:
        item = self.player.inventory.get_item(self.inventory_selection)
        if item:
            if item.item_type.value in ("potion", "scroll", "food"):
                # Use consumable
                result = self.player.use_item(item)
                if result:
                    self.add_message(f"Used {item.name}.")
                    # Adjust selection if needed
                    item_count = len(self.player.inventory.items)
                    if item_count > 0 and self.inventory_selection >= item_count:
                        self.inventory_selection = item_count - 1
                else:
                    self.add_message(f"Cannot use {item.name}.")
            else:
                self.add_message(f"{item.name} is not usable.")
```

### 7. Game.render_inventory() (darkdelve.py, lines 3205-3267)

Already uses `get_item_emoji` - verify imports are present. No code changes needed.

---

## Import Statements

```python
# At top of darkdelve.py, after line 35 (after CombatDamageLog import):
from src.domain.value_objects.damage_caps import clamp_monster_damage, clamp_player_damage
from src.presentation.item_emoji import get_item_emoji
from src.presentation.monster_emoji import get_monster_emoji
```

---

## Test Plan

### Updated Test File: `tests/test_inventory_description_panel.py`

The existing tests already verify:
- EquipmentSlot has RING and NECK
- Inventory has ring and neck slots
- Ring items map to RING slot
- Amulet items map to NECK slot
- ItemType has ACCESSORY
- show_inventory has KeySym.D handler
- show_inventory has KeySym.U handler
- _render_item_description method exists
- render_inventory calls _render_item_description

No new test file needed - the existing test file already covers all the missing features. The tests will pass once the implementation is complete.

---

## Integration Notes

1. **Damage clamping** integrates into `CombatResolver.resolve_attack()` which is called by `Game.attack()`. The clamping is transparent to the rest of the system — the `CombatEvent.damage` field is already clamped.

2. **Drop/Use key handlers** integrate into `Game.show_inventory()` which is the modal inventory loop. The handlers call existing `Entity.drop_item()` and `Entity.use_item()` methods, plus `Game.drop_item()` for ground placement.

3. **Accessory slots** integrate into the existing `EquipmentSlot` enum and `Inventory` equipment dict. The `render_inventory` method already iterates over all enum values, so new slots appear automatically.

4. **Emojis** are presentation-only. They don't affect game logic. The `get_item_emoji()` and `get_monster_emoji()` functions are called during rendering only.

5. **Description panel** is rendered alongside the existing inventory list. It reads from the selected item's fields (name, type, value, weight, stats, description) which already exist on the `Item` dataclass.

---

## Risks and Mitigations

### Risk 1: Damage cap makes high-level monsters trivial
**Mitigation**: The cap is `max_hp // 5`, meaning the player can survive at least 5 hits from any monster. For floor 1, monsters deal 1-3 damage vs cap of 20, so the cap has no effect on floor 1. It only prevents one-shots on deeper floors.

### Risk 2: Damage floor makes boss fights too fast
**Mitigation**: The floor is `monster.max_hp // 4`, ensuring ≤4 hits. For a boss with 200 HP, floor = 50. If the player's normal hit is 60, the floor doesn't activate. It only boosts damage when the player would otherwise deal very low damage.

### Risk 3: Emoji rendering in console mode
**Mitigation**: The console renderer uses a tileset. Emojis may not render as glyphs in all terminals. The emoji strings are used as prefixes in text panels (inventory, descriptions) where the terminal handles Unicode. The map view still uses ASCII `char` for entities.

### Risk 4: Player detection in resolve_attack
**Mitigation**: The heuristic `hasattr(attacker, 'inventory') and hasattr(attacker, 'xp')` correctly identifies the player Entity (which has both) vs mobs (which don't have `xp`). This is consistent with the existing codebase patterns.

### Risk 5: Ring/neck slots not populated by existing items
**Mitigation**: Existing items don't have `item_type=ACCESSORY`, so they won't auto-equip to ring/neck. New items need to be created with `ItemType.ACCESSORY` and names containing "ring"/"amulet"/"necklace" to map to the new slots. This is backward-compatible.

### Risk 6: Drop/use key handlers conflict with existing controls
**Mitigation**: 'd' and 'u' are not currently bound in the inventory screen. The existing bindings are ESC/I (close), UP/DOWN (navigate), ENTER (equip). Adding 'd' and 'u' is safe.

---

## Architecture Doc Updates

After implementation, update:
- `architecture/gotchas.md` — add entry about damage cap clamping order (must be after critical multiplication, before CombatEvent creation)
- `architecture/INDEX.md` — add new files: `damage_caps.py`, `item_emoji.py`, `monster_emoji.py` (already created)
- `architecture/module_design.md` — add new modules to Domain and Presentation layers

---

## Completion Criteria

- [ ] All 3 missing features implemented in darkdelve.py
- [ ] Missing imports added at top of darkdelve.py
- [ ] EquipmentSlot enum has RING and NECK
- [ ] ItemType enum has ACCESSORY
- [ ] _get_valid_slots_for_item maps ACCESSORY items to RING/NECK
- [ ] CombatResolver.resolve_attack applies damage clamping
- [ ] show_inventory has 'd' key handler for drop
- [ ] show_inventory has 'u' key handler for use
- [ ] render_inventory uses get_item_emoji (already done)
- [ ] tests/test_inventory_description_panel.py passes all tests
