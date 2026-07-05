# T-2026-0630-005 Description Panel Design Document

## Goal

Add a right-side item description panel to the inventory UI in `darkdelve.py` that displays the selected item's stats, description, and tags using box-drawing characters and word-wrapping.

---

## Files to Create

None (all changes are modifications to existing files)

---

## Files to Modify

### 1. `darkdelve.py` (lines 3395-3418) — `render_inventory()` method
**Line range to replace:** 3395-3418 (the entire `render_inventory` method)

### 2. `darkdelve.py` (after line 3418) — Add new helper method `_render_item_description()`
**Insert after:** line 3418 (after `render_inventory` method ends)

### 3. `tests/test_inventory_description_panel.py` (after line 77) — Add two new test methods
**Insert after:** line 77 (after `test_use_key_handler_exists` method)

---

## Pseudocode

### New Helper Method: `_render_item_description`

```python
def _render_item_description_panel(self, x: int, y: int, width: int, item) -> None:
    """
    Render the item description panel at position (x, y) with given width.
    
    Args:
        x: Left column of panel (e.g., 60)
        y: Top row of panel (e.g., 4)
        width: Panel width in characters (e.g., 55)
        item: Item object to describe
    """
    # Box-drawing characters
    TL = "┌"
    TR = "┐"
    BL = "└"
    BR = "┘"
    H = "─"
    V = "│"
    T_DOWN = "┬"
    T_UP = "┴"
    T_RIGHT = "├"
    T_LEFT = "┤"
    
    # Colors
    border_color = COLORS['text_dim']
    title_color = COLORS['gold']
    label_color = COLORS['text']
    value_color = COLORS['text']
    desc_color = COLORS['text_dim']
    tag_color = COLORS['text']
    magic_color = COLORS['magic']
    
    # 1. Top border
    self.renderer.print(x, y, TL + H * (width - 2) + TR, border_color)
    
    # 2. Item name (truncated to fit)
    name = item.display_name(self.player.identified_types if self.player else set())
    name_display = name[:width - 4]  # Leave space for borders and padding
    self.renderer.print(x, y + 1, f"{V} {name_display:<{width-4}} {V}", title_color)
    
    # 3. Separator
    self.renderer.print(x, y + 2, T_RIGHT + H * (width - 2) + T_LEFT, border_color)
    
    # 4. Stats section
    row = y + 3
    
    # Type
    item_type_str = item.item_type.value if hasattr(item.item_type, 'value') else str(item.item_type)
    self.renderer.print(x, row, f"{V} Type: {item_type_str:<{width-10}} {V}", label_color)
    row += 1
    
    # Value
    self.renderer.print(x, row, f"{V} Value: {item.value} gold{' ' * (width - 15 - len(str(item.value)))} {V}", label_color)
    row += 1
    
    # Weight
    self.renderer.print(x, row, f"{V} Weight: {item.weight}{' ' * (width - 13 - len(str(item.weight)))} {V}", label_color)
    row += 1
    
    # Combat stats (only if any > 0)
    if item.damage_bonus > 0 or item.to_hit_bonus > 0 or item.defense_bonus > 0:
        stat_parts = []
        if item.damage_bonus > 0:
            stat_parts.append(f"+{item.damage_bonus} DMG")
        if item.to_hit_bonus > 0:
            stat_parts.append(f"+{item.to_hit_bonus} HIT")
        if item.defense_bonus > 0:
            stat_parts.append(f"+{item.defense_bonus} DEF")
        stat_str = ", ".join(stat_parts)
        self.renderer.print(x, row, f"{V} Stats: {stat_str:<{width - 12}} {V}", label_color)
        row += 1
    
    # Effect
    if item.special_effect:
        effect_str = f"{item.special_effect}+{item.effect_strength}" if item.effect_strength > 0 else item.special_effect
        self.renderer.print(x, row, f"{V} Effect: {effect_str:<{width - 13}} {V}", magic_color)
        row += 1
    
    # 5. Description separator
    self.renderer.print(x, row, T_RIGHT + H * (width - 2) + T_LEFT, border_color)
    row += 1
    
    # 6. Description text (word-wrapped)
    desc = item.description or "No description available."
    words = desc.split()
    line = ""
    for word in words:
        if len(line) + len(word) + 1 > width - 6:  # -6 for borders and padding
            self.renderer.print(x, row, f"{V} {line:<{width-4}} {V}", desc_color)
            row += 1
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        self.renderer.print(x, row, f"{V} {line:<{width-4}} {V}", desc_color)
        row += 1
    
    # 7. Tags
    tags = []
    if item.item_type.value in ("potion", "scroll", "food"):
        tags.append("Usable")
    if hasattr(item, 'consumable') and item.consumable:
        tags.append("Consumable")
    if item.item_type.value in ("weapon", "armor", "accessory"):
        tags.append("Equippable")
    if item.equipped:
        tags.append("Equipped")
    
    if tags:
        tag_str = "  ".join(f"[{t}]" for t in tags)
        self.renderer.print(x, row, f"{V} {tag_str:<{width-4}} {V}", tag_color)
        row += 1
    
    # 8. Bottom border
    self.renderer.print(x, row, BL + H * (width - 2) + BR, border_color)
```

### Modified Method: `render_inventory`

```python
def render_inventory(self):
    """Render the inventory screen with left panel (list) and right panel (description)."""
    self.renderer.clear()
    
    inv = self.player.inventory if self.player and self.player.inventory else None
    
    # Panel positions
    left_x = 2
    desc_x = 60
    panel_width = 55
    
    # Header
    if inv:
        header = f"═ INVENTORY (Weight: {inv.get_total_weight()}/{inv.max_weight}) ═"
    else:
        header = "═ INVENTORY ═"
    self.renderer.print(left_x, 2, header, COLORS['text'])
    
    lines_y = 4
    
    # Equipped section
    self.renderer.print(left_x, lines_y, "▼ EQUIPPED:", COLORS['gold'])
    lines_y += 1
    
    if inv:
        for slot in EquipmentSlot:
            item = inv.equipment.get(slot) if inv.equipment else None
            if item:
                emoji = get_item_emoji(item.item_type.value, item.name)
                line = f"  {emoji} {slot.value:12} : {item.display_name(self.player.identified_types)}"
            else:
                line = f"  {'  '} {slot.value:12} : [empty]"
            self.renderer.print(left_x, lines_y, line, COLORS['text'])
            lines_y += 1
    
    lines_y += 1
    self.renderer.print(left_x, lines_y, "▼ BACKPACK:", COLORS['gold'])
    lines_y += 1
    
    if inv and inv.items:
        for idx, item in enumerate(inv.items):
            status = " (E)" if item.equipped else ""
            prefix = "▶ " if idx == self.inventory_selection else "  "
            emoji = get_item_emoji(item.item_type.value, item.name)
            line = f"{prefix}{emoji} {item.display_name(self.player.identified_types)}{status}"
            color = COLORS['gold'] if idx == self.inventory_selection else COLORS['text']
            self.renderer.print(left_x, lines_y, line, color)
            lines_y += 1
    else:
        self.renderer.print(left_x, lines_y, "  (empty)", COLORS['text_dim'])
        lines_y += 1
    
    # Right panel: description for selected item
    if inv:
        item = inv.get_item(self.inventory_selection)
        if item:
            self._render_item_description(desc_x, 4, panel_width, item)
    
    # Footer controls
    controls_y = 48
    self.renderer.print(left_x, controls_y, "[ENTER] Equip/Unequip  [U] Use  [D] Drop  [ESC/I] Close", COLORS['text_dim'])
    
    self.renderer.present()
```

---

## Import Statements

The following import is **already present** at line 41 of `darkdelve.py`:
```python
from src.presentation.item_emoji import get_item_emoji
```

No new imports needed. The `COLORS` dict is already defined at module level (lines 270-292).

---

## Test Plan

### File: `tests/test_inventory_description_panel.py`

Add these two test methods after `test_use_key_handler_exists` (after line 77):

```python
    def test_render_item_description_method_exists(self):
        """Verify _render_item_description method exists on Game class."""
        import inspect
        mod = self._import_runtime()
        self.assertTrue(hasattr(mod.Game, '_render_item_description'))
        sig = inspect.signature(mod.Game._render_item_description)
        params = list(sig.parameters.keys())
        # Should have: self, x, y, width, item
        self.assertEqual(params, ['self', 'x', 'y', 'width', 'item'])
        # Check type hints
        self.assertEqual(sig.parameters['x'].annotation, int)
        self.assertEqual(sig.parameters['y'].annotation, int)
        self.assertEqual(sig.parameters['width'].annotation, int)

    def test_render_inventory_calls_description_panel(self):
        """Verify render_inventory calls _render_item_description for selected item."""
        import inspect
        mod = self._import_runtime()
        source = inspect.getsource(mod.Game.render_inventory)
        self.assertIn('_render_item_description', source)
        self.assertIn('desc_x', source)
        self.assertIn('panel_width', source)
```

---

## Integration Notes

1. **`render_inventory()`** is called from `show_inventory()` (line 3259) in a loop while `self.showing_inventory` is True.

2. **`_render_item_description()`** is a new private method on the `Game` class. It uses:
   - `self.renderer.print(x, y, text, color)` — existing renderer method
   - `self.player.identified_types` — for item identification display
   - `COLORS` dict — module-level constant
   - `get_item_emoji()` — already imported from `src.presentation.item_emoji`

3. **Panel layout** (console is 120 cols per `config/game.yaml`):
   - Left panel: columns 2–55 (inventory list)
   - Right panel: columns 60–114 (description box, width=55)
   - Gap: column 56–59 (4 columns spacing)

4. **Item fields used** (all exist on `Item` dataclass):
   - `name`, `item_type`, `value`, `weight`
   - `damage_bonus`, `to_hit_bonus`, `defense_bonus`
   - `special_effect`, `effect_strength`
   - `description`, `equipped`, `consumable` (property)

5. **No changes** to `Item`, `Inventory`, `EquipmentSlot`, or `ItemType` — all required fields already exist.

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Box-drawing characters (┌┐└┘├┤┬┴─│) render incorrectly in some terminals | Use only basic box-drawing chars (all in CP437/Unicode). The project uses `tcod` renderer which supports Unicode. |
| Description panel exceeds console height (48 rows used) | Panel starts at row 4; max height ~44 rows. Description word-wraps. Footer at row 48. Safe for 50+ row consoles. |
| `item.description` is None or empty | Handled: falls back to "No description available." |
| `self.player` is None when panel renders | Guarded: `self.player.identified_types if self.player else set()` |
| Word-wrapping breaks on very long words | Long words exceeding `width-6` will overflow border slightly; acceptable for roguelike UI. |
| Performance impact on inventory screen | Negligible: only renders once per frame when inventory is open. No loops over large datasets. |
| Existing inventory navigation (UP/DOWN/ENTER/D/U/ESC) breaks | No changes to key handling in `show_inventory()`; only rendering is modified. |

---

## Architecture Doc Updates (Post-Implementation)

After implementation, update:
- `architecture/INDEX.md` — No new files created (only modifications)
- `architecture/gotchas.md` — Add note: "Box-drawing characters in `_render_item_description` require Unicode-capable terminal/renderer"
- `architecture/module_design.md` — No new modules

---

## Completion Criteria

- [ ] `render_inventory()` replaced with two-panel layout
- [ ] `_render_item_description(self, x: int, y: int, width: int, item)` method added
- [ ] Description panel shows: name, type, value, weight, combat stats, effect, description (word-wrapped), tags
- [ ] `get_item_emoji()` used for item icons in left panel
- [ ] Two new tests added to `tests/test_inventory_description_panel.py`
- [ ] All existing tests pass
- [ ] No other files modified
