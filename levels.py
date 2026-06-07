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