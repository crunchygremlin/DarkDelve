"""
Dynamic Mob Generation System - Uses Ollama to create unique enemy types
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import random
from ollama_client import get_ollama_client


class MobTier(Enum):
    MINION = "minion"
    SOLDIER = "soldier"
    ELITE = "elite"
    BOSS = "boss"


@dataclass
class MobTemplate:
    """Template for spawning enemies"""
    name: str
    symbol: str
    color: tuple  # (r, g, b)
    tier: MobTier
    
    # Stats
    hp: int
    power: int
    defense: int
    speed: int = 2
    
    # Abilities
    skills: List[str] = field(default_factory=list)
    
    # Loot
    loot_table: List[Dict[str, Any]] = field(default_factory=list)
    
    # Flavor
    description: str = ""
    ai_type: str = "aggressive"  # aggressive, defensive, tactical
    
    def __str__(self) -> str:
        return f"{self.name} (Tier: {self.tier.value})"


class MobRoster:
    """Collection of available mobs for current level"""
    
    def __init__(self):
        self.mobs: Dict[str, MobTemplate] = {}
        self.tier_distribution = {
            MobTier.MINION: 0.4,
            MobTier.SOLDIER: 0.35,
            MobTier.ELITE: 0.2,
            MobTier.BOSS: 0.05,
        }
    
    def add_mob(self, mob_id: str, template: MobTemplate) -> None:
        """Add mob template to roster"""
        self.mobs[mob_id] = template
    
    def add_mobs_from_dict(self, mobs_list: List[Dict]) -> None:
        """Add multiple mobs from LLM-generated data"""
        color_map = {
            "minion": (100, 200, 100),
            "soldier": (100, 150, 200),
            "elite": (200, 100, 100),
            "boss": (255, 0, 0),
        }
        
        for i, mob_data in enumerate(mobs_list):
            tier_str = mob_data.get("tier", "minion").lower()
            try:
                tier = MobTier(tier_str)
            except ValueError:
                tier = MobTier.MINION
            
            template = MobTemplate(
                name=mob_data.get("name", f"Enemy {i}"),
                symbol=mob_data.get("symbol", "?")[0],  # Take first char
                color=color_map.get(tier_str, (150, 150, 150)),
                tier=tier,
                hp=mob_data.get("hp", 5),
                power=mob_data.get("power", 2),
                defense=mob_data.get("defense", 0),
                speed=mob_data.get("speed", 2),
                skills=mob_data.get("skills", []),
                description=mob_data.get("description", ""),
                ai_type=mob_data.get("ai_type", "aggressive"),
            )
            
            self.add_mob(template.name.lower().replace(" ", "_"), template)
    
    def spawn_random(self, count: int = 1) -> List[MobTemplate]:
        """Spawn random mobs based on tier distribution"""
        if not self.mobs:
            return []
        
        mobs = []
        for _ in range(count):
            # Choose tier based on distribution
            tier = random.choices(
                list(self.tier_distribution.keys()),
                weights=list(self.tier_distribution.values())
            )[0]
            
            # Pick random mob of that tier
            candidates = [m for m in self.mobs.values() if m.tier == tier]
            if candidates:
                mobs.append(random.choice(candidates))
        
        return mobs
    
    def get_by_name(self, name: str) -> Optional[MobTemplate]:
        """Get mob by name"""
        name_key = name.lower().replace(" ", "_")
        return self.mobs.get(name_key)
    
    def get_by_tier(self, tier: MobTier) -> List[MobTemplate]:
        """Get all mobs of a specific tier"""
        return [m for m in self.mobs.values() if m.tier == tier]


class MobGenerator:
    """Generate mobs using Ollama"""
    
    def __init__(self, theme: str = "dungeon"):
        self.client = get_ollama_client()
        self.theme = theme
        self.roster: Optional[MobRoster] = None
    
    def generate_roster(self) -> Optional[MobRoster]:
        """Generate complete mob roster for level"""
        prompt = f"""You are a roguelike game designer. Create 8 unique enemies for a '{self.theme}' level.

Requirements:
- Vary tiers: 2-3 minion, 2-3 soldier, 2 elite, 1 boss
- Use single ASCII characters for symbols
- Keep names short (1-2 words)
- Include simple skills

Respond ONLY with valid JSON:
{{
  "mobs": [
    {{
      "name": "Enemy Name",
      "symbol": "e",
      "tier": "minion|soldier|elite|boss",
      "hp": 5,
      "power": 3,
      "defense": 1,
      "speed": 2,
      "skills": ["skill1", "skill2"],
      "description": "brief description",
      "ai_type": "aggressive|defensive|tactical"
    }}
  ]
}}"""

        cache_key = f"roster_{self.theme}"
        result = self.client.generate_json(prompt, cache_key=cache_key)
        
        if result and "mobs" in result:
            self.roster = MobRoster()
            self.roster.add_mobs_from_dict(result["mobs"])
            return self.roster
        
        return None


# Default fallback mobs (if LLM unavailable)
def create_default_roster() -> MobRoster:
    """Create default roster when Ollama is unavailable"""
    roster = MobRoster()
    
    mobs = [
        MobTemplate(
            name="Goblin Scout",
            symbol="g",
            color=(100, 200, 100),
            tier=MobTier.MINION,
            hp=5,
            power=2,
            defense=0,
            skills=["dash"],
            description="Quick and sneaky",
            ai_type="aggressive",
        ),
        MobTemplate(
            name="Goblin Soldier",
            symbol="s",
            color=(100, 200, 100),
            tier=MobTier.SOLDIER,
            hp=10,
            power=3,
            defense=1,
            skills=["shield"],
            description="Disciplined fighter",
            ai_type="tactical",
        ),
        MobTemplate(
            name="Goblin Elite",
            symbol="G",
            color=(200, 100, 100),
            tier=MobTier.ELITE,
            hp=15,
            power=4,
            defense=2,
            skills=["power_attack", "parry"],
            description="Veteran warrior",
            ai_type="tactical",
        ),
        MobTemplate(
            name="Goblin Warlord",
            symbol="W",
            color=(255, 0, 0),
            tier=MobTier.BOSS,
            hp=30,
            power=6,
            defense=3,
            skills=["war_cry", "whirlwind", "command"],
            description="Legendary leader",
            ai_type="tactical",
        ),
    ]
    
    for mob in mobs:
        roster.add_mob(mob.name.lower().replace(" ", "_"), mob)
    
    return roster
