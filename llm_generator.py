"""
LLM Prompt Templates - Optimized for Ollama + qwen2.5-coder:7b-instruct
Compact prompts designed for 8k context window
"""

from ollama_client import OllamaClient, get_ollama_client
import json
from typing import Dict, List, Optional, Any


class PromptTemplates:
    """Roguelike-specific prompt templates"""
    
    # MOB GENERATION - Optimized for Ollama
    MOB_GENERATION = """You are a roguelike game designer. Generate 8 unique enemies.

Format ONLY as JSON (no other text):
{
  "mobs": [
    {
      "name": "enemy_name",
      "symbol": "single_char",
      "tier": "minion|soldier|elite",
      "hp": int,
      "power": int,
      "defense": int,
      "skills": ["skill1", "skill2"],
      "description": "one line"
    }
  ]
}

Tiers: minion(weak), soldier(normal), elite(tough). Vary difficulty."""
    
    # ITEM GENERATION - Compact format
    ITEM_GENERATION = """Generate 10 roguelike items (common to rare).

Format ONLY as JSON:
{
  "items": [
    {
      "name": "item_name",
      "type": "weapon|armor|potion|scroll|misc",
      "rarity": "common|uncommon|rare|legendary",
      "damage": 0,
      "defense": 0,
      "description": "short"
    }
  ]
}"""
    
    # LEVEL DESIGN - Theme-based
    LEVEL_DESIGN = """Generate a dungeon level theme.

Format ONLY as JSON:
{
  "theme": "name",
  "difficulty": 1-10,
  "description": "short",
  "room_count": int,
  "trap_density": 0.0-1.0,
  "treasure_density": 0.0-1.0,
  "ambient": "short description"
}"""
    
    # COMBAT NARRATION - Flavor text
    COMBAT_NARRATION = """Describe a combat result in ONE sentence (roguelike style).

Context: {context}

Generate ONE vivid, brief combat description. NO OTHER TEXT."""
    
    # MOB BEHAVIOR - AI decisions
    MOB_BEHAVIOR = """Given a mob's stats, decide its action.

Mob: {mob_name} (HP: {hp}/{max_hp})
Player: (HP: {player_hp}/{player_max_hp})
Distance: {distance} tiles

Choose action:
1. ATTACK - Close and attack
2. RETREAT - Move away
3. HEAL - Use ability to recover
4. DEFEND - Prepare defense

Respond ONLY with: "ACTION: [action]" and nothing else."""


class LLMContentGenerator:
    """Generate game content using Ollama"""
    
    def __init__(self, client: Optional[OllamaClient] = None):
        self.client = client or get_ollama_client()
        self.templates = PromptTemplates()
    
    def generate_mobs(self, theme: str = "dungeon") -> Optional[List[Dict]]:
        """Generate mob roster for level"""
        prompt = f"Theme: {theme}\n\n{self.templates.MOB_GENERATION}"
        
        result = self.client.generate_json(prompt, cache_key=f"mobs_{theme}")
        
        if result and "mobs" in result:
            return result["mobs"]
        
        return None
    
    def generate_items(self, theme: str = "generic") -> Optional[List[Dict]]:
        """Generate items for level"""
        prompt = f"Theme: {theme}\n\n{self.templates.ITEM_GENERATION}"
        
        result = self.client.generate_json(prompt, cache_key=f"items_{theme}")
        
        if result and "items" in result:
            return result["items"]
        
        return None
    
    def generate_level_theme(self, level_num: int) -> Optional[Dict]:
        """Generate level design theme"""
        prompt = f"Level {level_num}\n\n{self.templates.LEVEL_DESIGN}"
        
        result = self.client.generate_json(
            prompt,
            cache_key=f"level_theme_{level_num}"
        )
        
        return result
    
    def generate_combat_narration(
        self,
        attacker: str,
        defender: str,
        damage: int,
        hit_type: str = "normal"
    ) -> str:
        """Generate combat flavor text"""
        context = f"{attacker} hits {defender} for {damage} damage ({hit_type})"
        prompt = self.templates.COMBAT_NARRATION.format(context=context)
        
        return self.client.generate(prompt, cache_key=f"combat_{attacker}_{defender}_{damage}")
    
    def generate_mob_action(
        self,
        mob_name: str,
        mob_hp: int,
        mob_max_hp: int,
        player_hp: int,
        player_max_hp: int,
        distance: int
    ) -> str:
        """Generate mob AI decision"""
        prompt = self.templates.MOB_BEHAVIOR.format(
            mob_name=mob_name,
            hp=mob_hp,
            max_hp=mob_max_hp,
            player_hp=player_hp,
            player_max_hp=player_max_hp,
            distance=distance
        )
        
        response = self.client.generate(prompt)
        
        # Parse response
        if "ATTACK" in response:
            return "ATTACK"
        elif "RETREAT" in response:
            return "RETREAT"
        elif "HEAL" in response:
            return "HEAL"
        elif "DEFEND" in response:
            return "DEFEND"
        else:
            return "ATTACK"  # Default


# Example usage functions
def demo_mob_generation() -> None:
    """Demo mob generation"""
    gen = LLMContentGenerator()
    
    print("🎲 Generating Mobs...")
    mobs = gen.generate_mobs("goblin_fortress")
    
    if mobs:
        print("✓ Generated mobs:")
        for mob in mobs:
            print(f"  - {mob.get('name', '?')} ({mob.get('tier', '?')})")
    else:
        print("✗ Failed to generate mobs")


def demo_item_generation() -> None:
    """Demo item generation"""
    gen = LLMContentGenerator()
    
    print("🎲 Generating Items...")
    items = gen.generate_items("ancient_temple")
    
    if items:
        print("✓ Generated items:")
        for item in items[:3]:
            print(f"  - {item.get('name', '?')} ({item.get('rarity', '?')})")
    else:
        print("✗ Failed to generate items")


def demo_level_theme() -> None:
    """Demo level theme generation"""
    gen = LLMContentGenerator()
    
    print("🎲 Generating Level Theme...")
    theme = gen.generate_level_theme(1)
    
    if theme:
        print(f"✓ Level Theme: {theme.get('theme', '?')}")
        print(f"  Description: {theme.get('description', '?')}")
    else:
        print("✗ Failed to generate level theme")


def demo_combat_narration() -> None:
    """Demo combat narration"""
    gen = LLMContentGenerator()
    
    print("🎲 Generating Combat Narration...")
    narration = gen.generate_combat_narration("Player", "Goblin Scout", 7, "critical")
    
    print(f"✓ Narration: {narration}")


if __name__ == "__main__":
    from ollama_client import check_ollama_status
    
    print("═" * 60)
    print("OLLAMA STATUS CHECK")
    print("═" * 60)
    
    status = check_ollama_status()
    print(f"Available: {status['available']}")
    print(f"Host: {status['host']}")
    print(f"Model: {status['model']}")
    
    if not status['available']:
        print(f"\n⚠️  {status.get('warning', 'Ollama not available')}")
        print("\nTo start Ollama with qwen2.5-coder:")
        print("  ollama run qwen2.5-coder:7b-instruct")
    else:
        print("\n✓ Ollama is ready!")
        print("\nDEMO: Generating content...")
        print("═" * 60)
        
        demo_mob_generation()
        print()
        demo_item_generation()
        print()
        demo_level_theme()
        print()
        demo_combat_narration()
