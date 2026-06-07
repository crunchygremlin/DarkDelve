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