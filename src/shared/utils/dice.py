import re
from typing import Tuple

def parse_dice(weapon_dice: str) -> Tuple[int, int, int]:
    # Parse "NdS+M" / "NdS" / "N" / "NdS-M" into (num, size, mod).
    # Returns (num_dice, dice_size, flat_modifier).
    s = (weapon_dice or "1d6").strip().lower()
    m = re.fullmatch(r"(\d+)\s*d\s*(\d+)\s*([+-]\s*\d+)?", s)
    if not m:
        try:
            return 0, 0, int(s)          # bare flat number -> modifier only
        except ValueError:
            return 1, 6, 0               # ultimate fallback
    num = int(m.group(1))
    size = int(m.group(2))
    mod = int(m.group(3).replace(" ", "")) if m.group(3) else 0
    return num, size, mod