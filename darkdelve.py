#!/usr/bin/env python3
"""
DarkDelve - A Traditional Roguelike with Local LLM Content Generation
Single-file implementation with embedded Ollama management.
"""

import sys
import os
import json
import random
import time
import uuid
import sqlite3
import hashlib
import subprocess
import threading
import queue
import platform
import urllib.request
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Set
from enum import Enum
from pathlib import Path

import tcod
import numpy as np
import yaml
import requests

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG_PATH = Path(__file__).parent / "config" / "game.yaml"
ASSETS_PATH = Path(__file__).parent / "assets"
VENDOR_PATH = Path(__file__).parent / "vendor"
CACHE_PATH = Path(__file__).parent / "cache"
SAVES_PATH = Path(__file__).parent / "saves"
HIGHSCORES_PATH = Path(__file__).parent / "highscores.json"

def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

CONFIG = load_config()

# =============================================================================
# UTILITIES
# =============================================================================

def clamp(value: int, min_val: int, max_val: int) -> int:
    return max(min_val, min(value, max_val))

def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# =============================================================================
# EMBEDDED OLLAMA MANAGEMENT
# =============================================================================

class EmbeddedOllama:
    """Manages local Ollama instance as child process"""
    
    def __init__(self, model: str = "qwen2.5-coder:7b-instruct"):
        self.model = model
        self.process: Optional[subprocess.Popen] = None
        self.base_url = "http://127.0.0.1:11434"
        self.ollama_path = self._find_or_install_ollama()
        self._started = False
    
    def _find_or_install_ollama(self) -> str:
        # Check vendor directory for bundled binary
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        if system == "linux":
            binary_name = "ollama_linux_x64"
        elif system == "darwin":
            binary_name = "ollama_macos_arm64" if machine == "arm64" else "ollama_macos_x64"
        elif system == "windows":
            binary_name = "ollama_windows_x64.exe"
        else:
            binary_name = "ollama"
        
        vendor_binary = VENDOR_PATH / binary_name
        if vendor_binary.exists():
            return str(vendor_binary)
        
        # Check PATH
        import shutil
        path_binary = shutil.which("ollama")
        if path_binary:
            return path_binary
        
        # Fallback - will fail gracefully
        return "ollama"
    
    def start(self) -> bool:
        if self._started:
            return True
        
        try:
            self.process = subprocess.Popen(
                [self.ollama_path, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            return self._wait_ready(timeout=30)
        except Exception as e:
            print(f"Failed to start Ollama: {e}")
            return False
    
    def _wait_ready(self, timeout: int = 30) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
                if resp.status_code == 200:
                    self._started = True
                    return True
            except:
                pass
            time.sleep(0.5)
        return False
    
    def ensure_model(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = [m.get('name', '') for m in resp.json().get('models', [])]
                if any(self.model in m for m in models):
                    return True
            
            # Pull model
            print(f"Pulling model {self.model}...")
            resp = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model},
                timeout=300
            )
            return resp.status_code == 200
        except Exception as e:
            print(f"Model check failed: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> str:
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
                "num_predict": kwargs.get("num_predict", 1024),
            }
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=kwargs.get("timeout", 30)
            )
            if resp.status_code == 200:
                return resp.json().get('response', '').strip()
        except Exception as e:
            print(f"Generation error: {e}")
        return ""
    
    def generate_json(self, prompt: str, **kwargs) -> Optional[dict]:
        response = self.generate(prompt, **kwargs)
        if not response:
            return None
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        return None
    
    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            self._started = False

# =============================================================================
# CONTENT CACHE (SQLite)
# =============================================================================

class ContentCache:
    """Persistent SQLite cache for LLM generations"""
    
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self._init_db()
    
    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS generations (
                key TEXT PRIMARY KEY,
                prompt_hash TEXT,
                response TEXT,
                model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                use_count INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()
    
    def get(self, key: str, prompt: str) -> Optional[str]:
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        row = self.conn.execute(
            "SELECT response FROM generations WHERE key=? AND prompt_hash=?",
            (key, prompt_hash)
        ).fetchone()
        if row:
            self.conn.execute(
                "UPDATE generations SET use_count=use_count+1 WHERE key=?", (key,)
            )
            self.conn.commit()
            return row[0]
        return None
    
    def set(self, key: str, prompt: str, response: str, model: str):
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        self.conn.execute(
            "INSERT OR REPLACE INTO generations (key, prompt_hash, response, model) VALUES (?,?,?,?)",
            (key, prompt_hash, response, model)
        )
        self.conn.commit()

# =============================================================================
# SYMBOLS & COLORS
# =============================================================================

COLORS = {
    'player': (255, 255, 0),
    'wall': (80, 80, 80),
    'floor': (100, 100, 100),
    'door': (150, 100, 50),
    'gold': (255, 215, 0),
    'blood': (200, 0, 0),
    'poison': (0, 200, 0),
    'magic': (150, 100, 255),
    'water': (100, 150, 255),
    'fire': (255, 100, 0),
    'item': (200, 200, 100),
    'enemy_weak': (100, 200, 100),
    'enemy_normal': (100, 150, 200),
    'enemy_tough': (200, 100, 100),
    'enemy_boss': (255, 0, 0),
    'equipment': (150, 150, 150),
    'text': (220, 220, 220),
    'text_dim': (150, 150, 150),
    'hp_high': (0, 255, 0),
    'hp_med': (255, 255, 0),
    'hp_low': (255, 0, 0),
}

ROGUELIKE_SYMBOLS = {
    'floor': {'char': '.', 'color': COLORS['floor'], 'walkable': True},
    'wall': {'char': '#', 'color': COLORS['wall'], 'walkable': False},
    'door': {'char': '+', 'color': COLORS['door'], 'walkable': True},
    'stair_down': {'char': '>', 'color': COLORS['gold'], 'walkable': True},
    'stair_up': {'char': '<', 'color': COLORS['gold'], 'walkable': True},
    'player': {'char': '@', 'color': COLORS['player'], 'walkable': False},
    'weapon': {'char': '/', 'color': COLORS['item']},
    'armor': {'char': '[', 'color': COLORS['equipment']},
    'potion': {'char': '!', 'color': COLORS['poison']},
    'scroll': {'char': '?', 'color': COLORS['magic']},
    'gold': {'char': '$', 'color': COLORS['gold']},
    'food': {'char': ',', 'color': COLORS['item']},
    'enemy_minion': {'char': 'g', 'color': COLORS['enemy_weak']},
    'enemy_soldier': {'char': 's', 'color': COLORS['enemy_normal']},
    'enemy_elite': {'char': 'E', 'color': COLORS['enemy_tough']},
    'enemy_boss': {'char': 'B', 'color': COLORS['enemy_boss']},
}

def get_symbol(symbol_type: str) -> dict:
    return ROGUELIKE_SYMBOLS.get(symbol_type, ROGUELIKE_SYMBOLS['floor'])

# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class HitResult(Enum):
    MISS = 0
    HIT = 1
    CRITICAL = 2
    CRITICAL_FAIL = 3

class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    POTION = "potion"
    SCROLL = "scroll"
    FOOD = "food"
    MISC = "misc"

class EquipmentSlot(Enum):
    HEAD = "head"
    CHEST = "chest"
    HANDS = "hands"
    LEGS = "legs"
    FEET = "feet"
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"

class MobTier(Enum):
    MINION = "minion"
    SOLDIER = "soldier"
    ELITE = "elite"
    BOSS = "boss"

class SkillType(Enum):
    PASSIVE = "passive"
    ACTIVE = "active"

@dataclass
class CombatEvent:
    turn: int
    attacker_name: str
    defender_name: str
    to_hit_bonus: int
    target_ac: int
    d20_roll: int
    total_roll: int
    result: HitResult
    damage: int = 0
    flavor_text: str = ""
    
    def __str__(self) -> str:
        roll_text = f"[Roll: {self.total_roll} vs AC {self.target_ac}]"
        if self.result == HitResult.CRITICAL:
            return f"{self.attacker_name} strikes critically! {roll_text} CRITICAL HIT! Damage: {self.damage}"
        elif self.result == HitResult.HIT:
            return f"{self.attacker_name} attacks! {roll_text} HIT! Damage: {self.damage}"
        elif self.result == HitResult.MISS:
            return f"{self.attacker_name} attacks... {roll_text} MISS!"
        elif self.result == HitResult.CRITICAL_FAIL:
            return f"{self.attacker_name} attempts strike... {roll_text} CRITICAL MISS!"
        return f"Combat: {self.attacker_name} vs {self.defender_name}"

@dataclass
class CombatLog:
    events: List[CombatEvent] = field(default_factory=list)
    max_history: int = 20
    turn_counter: int = 0
    
    def add_event(self, event: CombatEvent):
        event.turn = self.turn_counter
        self.events.append(event)
        if len(self.events) > self.max_history:
            self.events.pop(0)
    
    def get_recent(self, count: int = 5) -> List[CombatEvent]:
        return self.events[-count:]
    
    def new_turn(self):
        self.turn_counter += 1

@dataclass
class Item:
    id: str
    name: str
    item_type: ItemType
    symbol: str
    weight: int
    value: int
    damage_bonus: int = 0
    defense_bonus: int = 0
    to_hit_bonus: int = 0
    encumbrance: int = 0
    special_effect: Optional[str] = None
    effect_strength: int = 0
    description: str = ""
    equipped: bool = False
    equipped_slot: Optional[EquipmentSlot] = None
    identified: bool = False
    appearance: str = ""  # Unidentified appearance
    
    def get_stat_string(self) -> str:
        stats = []
        if self.damage_bonus > 0:
            stats.append(f"+{self.damage_bonus} DMG")
        if self.to_hit_bonus > 0:
            stats.append(f"+{self.to_hit_bonus} HIT")
        if self.defense_bonus > 0:
            stats.append(f"+{self.defense_bonus} DEF")
        if self.special_effect:
            stats.append(f"{self.special_effect}")
        return " [" + ", ".join(stats) + "]" if stats else ""
    
    def display_name(self, identified_types: Set[str]) -> str:
        if self.identified or self.item_type in (ItemType.POTION, ItemType.SCROLL) and self.id in identified_types:
            return f"{self.name}{self.get_stat_string()}"
        return self.appearance or f"unidentified {self.item_type.value}"

@dataclass
class Inventory:
    items: List[Item] = field(default_factory=list)
    max_weight: int = 100
    equipment: Dict[EquipmentSlot, Optional[Item]] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.equipment:
            self.equipment = {slot: None for slot in EquipmentSlot}
    
    def add_item(self, item: Item) -> bool:
        if self.get_total_weight() + item.weight > self.max_weight:
            return False
        self.items.append(item)
        return True
    
    def remove_item(self, item_id: str) -> bool:
        for i, item in enumerate(self.items):
            if item.id == item_id:
                if item.equipped:
                    self.unequip(item_id)
                self.items.pop(i)
                return True
        return False
    
    def find_item(self, item_id: str) -> Optional[Item]:
        for item in self.items:
            if item.id == item_id:
                return item
        return None
    
    def equip(self, item_id: str, slot: EquipmentSlot) -> bool:
        item = self.find_item(item_id)
        if not item:
            return False
        
        valid_slots = self._get_valid_slots_for_item(item)
        if slot not in valid_slots:
            return False
        
        if self.equipment[slot] is not None:
            old_item = self.equipment[slot]
            old_item.equipped = False
            old_item.equipped_slot = None
        
        item.equipped = True
        item.equipped_slot = slot
        self.equipment[slot] = item
        return True
    
    def unequip(self, item_id: str) -> bool:
        item = self.find_item(item_id)
        if not item or not item.equipped:
            return False
        if item.equipped_slot:
            self.equipment[item.equipped_slot] = None
        item.equipped = False
        item.equipped_slot = None
        return True
    
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
        return []
    
    def get_total_weight(self) -> int:
        return sum(item.weight for item in self.items)
    
    def get_defense_bonus(self) -> int:
        return sum(item.defense_bonus for item in self.equipment.values() if item and item.equipped)
    
    def get_damage_bonus(self) -> int:
        weapon = self.equipment[EquipmentSlot.MAIN_HAND]
        return weapon.damage_bonus if weapon and weapon.equipped else 0
    
    def get_to_hit_bonus(self) -> int:
        weapon = self.equipment[EquipmentSlot.MAIN_HAND]
        return weapon.to_hit_bonus if weapon and weapon.equipped else 0

@dataclass
class MobTemplate:
    name: str
    symbol: str
    color: Tuple[int, int, int]
    tier: MobTier
    hp: int
    power: int
    defense: int
    speed: int = 100
    skills: List[str] = field(default_factory=list)
    loot_table: List[Dict] = field(default_factory=list)
    description: str = ""
    ai_type: str = "aggressive"

@dataclass
class MobRoster:
    mobs: Dict[str, MobTemplate] = field(default_factory=dict)
    tier_distribution: Dict[MobTier, float] = field(default_factory=lambda: {
        MobTier.MINION: 0.4,
        MobTier.SOLDIER: 0.35,
        MobTier.ELITE: 0.2,
        MobTier.BOSS: 0.05,
    })
    
    def add_mob(self, mob_id: str, template: MobTemplate):
        self.mobs[mob_id] = template
    
    def add_mobs_from_dict(self, mobs_list: List[Dict]):
        # Mapping numeric indices to string names as a safety fallback
        numeric_tier_map = {1: "minion", 2: "soldier", 3: "elite", 4: "boss"}
        
        color_map = {
            "minion": (100, 200, 100),
            "soldier": (100, 150, 200),
            "elite": (200, 100, 100),
            "boss": (255, 0, 0),
        }
        
        for i, mob_data in enumerate(mobs_list):
            # FIX 1: Safely handle raw integers or strings coming from the AI model
            raw_tier = mob_data.get("tier", "minion")
            if isinstance(raw_tier, int):
                tier_str = numeric_tier_map.get(raw_tier, "minion")
            else:
                tier_str = str(raw_tier).lower()
                
            try:
                tier = MobTier(tier_str)
            except ValueError:
                tier = MobTier.MINION
            
            # FIX 2: Safely convert symbol to string and handle empty structures
            raw_symbol = str(mob_data.get("symbol", "?"))
            symbol = raw_symbol[0] if raw_symbol else "?"
                
            template = MobTemplate(
                name=mob_data.get("name", f"Enemy {i}"),
                symbol=symbol,
                color=color_map.get(tier_str, (150, 150, 150)),
                tier=tier,
                hp=int(mob_data.get("hp", 5)),
                power=int(mob_data.get("power", 2)),
                defense=int(mob_data.get("defense", 0)),
                speed=int(mob_data.get("speed", 100)),
                skills=mob_data.get("skills", []),
                description=mob_data.get("description", ""),
                ai_type=mob_data.get("ai_type", "aggressive"),
            )
            self.add_mob(template.name.lower().replace(" ", "_"), template)
    
    def spawn_random(self, count: int = 1) -> List[MobTemplate]:
        if not self.mobs:
            return []
        mobs = []
        for _ in range(count):
            tier = random.choices(
                list(self.tier_distribution.keys()),
                weights=list(self.tier_distribution.values())
            )[0]
            candidates = [m for m in self.mobs.values() if m.tier == tier]
            if candidates:
                mobs.append(random.choice(candidates))
        return mobs


@dataclass
class LevelTheme:
    name: str
    difficulty: int
    description: str
    room_count: int
    trap_density: float
    treasure_density: float
    ambient_description: str
    tile_set: str = "stone"
    monster_theme: str = "goblin"
    loot_theme: str = "martial"
    hazards: List[str] = field(default_factory=list)
    boss: Dict = field(default_factory=dict)

@dataclass
class Entity:
    x: int
    y: int
    char: str
    color: Tuple[int, int, int]
    name: str
    blocks: bool = True
    hp: int = 10
    max_hp: int = 10
    power: int = 3
    defense: int = 1
    speed: int = 100
    intel_tier: int = 1
    is_commander: bool = False
    home_position: Tuple[int, int] = (0, 0)
    current_command: Optional[Dict] = None
    pending_command: bool = False
    
    # Player-specific
    inventory: Optional[Inventory] = None
    stats: Dict[str, int] = field(default_factory=lambda: {
        'str': 10, 'dex': 10, 'con': 10, 'int': 10, 'wis': 10, 'cha': 10
    })
    level: int = 1
    xp: int = 0
    xp_to_next: int = 100
    skill_points: int = 0
    known_skills: List[str] = field(default_factory=list)
    nutrition: int = 1000
    max_nutrition: int = 2000
    gold: int = 0
    kill_count: int = 0
    identified_types: Set[str] = field(default_factory=set)
    flags: Set[str] = field(default_factory=set)
    
    # Status effects
    effects: Dict[str, int] = field(default_factory=dict)  # effect -> duration
    
    @property
    def is_alive(self) -> bool:
        return self.hp > 0
    
    @property
    def armor_class(self) -> int:
        base_ac = 10 + self.defense
        if self.inventory:
            equipment_bonus = self.inventory.get_defense_bonus()
            return base_ac + equipment_bonus
        return base_ac
    
    @property
    def to_hit_bonus(self) -> int:
        if self.inventory:
            return self.inventory.get_to_hit_bonus()
        return 0
    
    @property
    def damage_bonus(self) -> int:
        if self.inventory:
            return self.inventory.get_damage_bonus()
        return 0
    
    def move_to(self, x: int, y: int, dungeon_map: np.ndarray, entities: List['Entity']) -> bool:
        if 0 <= x < dungeon_map.shape[0] and 0 <= y < dungeon_map.shape[1]:
            if dungeon_map[x, y]:
                if not any(e.blocks for e in entities if e.x == x and e.y == y and e is not self):
                    self.x = x
                    self.y = y
                    return True
        return False
    
    def move_towards(self, target_x: int, target_y: int, dungeon_map: np.ndarray, entities: List['Entity']):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = max(abs(dx), abs(dy))
        if distance > 0:
            step_x = int(round(dx / distance))
            step_y = int(round(dy / distance))
            self.move_to(self.x + step_x, self.y + step_y, dungeon_map, entities)
    
    def apply_effect(self, effect: str, duration: int):
        self.effects[effect] = duration
    
    def tick_effects(self):
        to_remove = []
        for effect, duration in self.effects.items():
            self.effects[effect] = duration - 1
            if self.effects[effect] <= 0:
                to_remove.append(effect)
        for effect in to_remove:
            del self.effects[effect]

# =============================================================================
# COMBAT SYSTEM
# =============================================================================

class CombatResolver:
    @staticmethod
    def resolve_attack(
        attacker: Entity,
        defender: Entity,
        weapon_dice: str = "1d6"
    ) -> CombatEvent:
        d20_roll = random.randint(1, 20)
        total_roll = d20_roll + attacker.to_hit_bonus
        
        if d20_roll == 20:
            result = HitResult.CRITICAL
        elif d20_roll == 1:
            result = HitResult.CRITICAL_FAIL
        elif total_roll >= defender.armor_class:
            result = HitResult.HIT
        else:
            result = HitResult.MISS
        
        damage = 0
        if result in [HitResult.HIT, HitResult.CRITICAL]:
            try:
                parts = weapon_dice.replace('d', ' ').split()
                num_dice = int(parts[0])
                dice_size = int(parts[1])
                modifier = int(parts[2]) if len(parts) > 2 else 0
            except:
                num_dice, dice_size, modifier = 1, 6, 0
            
            damage = sum(random.randint(1, dice_size) for _ in range(num_dice))
            damage += modifier + (attacker.power // 2) + attacker.damage_bonus
            
            if result == HitResult.CRITICAL:
                damage *= 2
        
        return CombatEvent(
            turn=0,
            attacker_name=attacker.name,
            defender_name=defender.name,
            to_hit_bonus=attacker.to_hit_bonus,
            target_ac=defender.armor_class,
            d20_roll=d20_roll,
            total_roll=total_roll,
            result=result,
            damage=damage,
        )

# =============================================================================
# ENERGY-BASED TURN SYSTEM
# =============================================================================

class EnergySystem:
    def __init__(self):
        self.entities: List[Dict] = []  # {entity, energy, speed}
        self.turn_count = 0
    
    def add_entity(self, entity: Entity, speed: int = None):
        if speed is None:
            speed = entity.speed
        self.entities.append({"entity": entity, "energy": 0, "speed": speed})
    
    def remove_entity(self, entity: Entity):
        self.entities = [e for e in self.entities if e["entity"] is not entity]
    
    def next_actor(self) -> Optional[Entity]:
        while True:
            for e in self.entities:
                e["energy"] += e["speed"]
            
            actors = [e for e in self.entities if e["energy"] >= 100 and e["entity"].is_alive]
            if not actors:
                continue
            
            actor = max(actors, key=lambda e: e["energy"])
            actor["energy"] -= 100
            return actor["entity"]
    
    def get_player_turn_fraction(self, player: Entity) -> float:
        for e in self.entities:
            if e["entity"] is player:
                return e["energy"] / 100.0
        return 0.0

# =============================================================================
# DUNGEON GENERATION
# =============================================================================

def tunnel_between(start: Tuple[int, int], end: Tuple[int, int]):
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:
        for x in range(min(x1, x2), max(x1, x2) + 1):
            yield x, y1
        for y in range(min(y1, y2), max(y1, y2) + 1):
            yield x2, y
    else:
        for y in range(min(y1, y2), max(y1, y2) + 1):
            yield x1, y
        for x in range(min(x1, x2), max(x1, x2) + 1):
            yield x, y2

class DungeonGenerator:
    def __init__(self, config: dict):
        self.config = config
        self.dungeon_config = config['dungeon']
    
    def generate_level(self, depth: int, branch: str = "main", theme: LevelTheme = None) -> Tuple[np.ndarray, List[Entity], Tuple[int, int], Tuple[int, int]]:
        width = self.dungeon_config['width']
        height = self.dungeon_config['height']
        max_rooms = self.dungeon_config['max_rooms']
        room_min = self.dungeon_config['room_min_size']
        room_max = self.dungeon_config['room_max_size']
        
        dungeon_map = np.zeros((width, height), dtype=bool, order="F")
        rooms = []
        entities = []
        player_start = (width // 2, height // 2)
        stair_down = None
        stair_up = None
        
        for r in range(max_rooms):
            w = random.randint(room_min, room_max)
            h = random.randint(room_min, room_max)
            x = random.randint(0, width - w - 1)
            y = random.randint(0, height - h - 1)
            x1, y1, x2, y2 = x, y, x + w, y + h
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            overlap = False
            for rx1, ry1, rx2, ry2, _, _ in rooms:
                if x1 < rx2 and x2 > rx1 and y1 < ry2 and y2 > ry1:
                    overlap = True
                    break
            if overlap:
                continue
            
            dungeon_map[x1+1:x2, y1+1:y2] = True
            
            if len(rooms) == 0:
                player_start = (center_x, center_y)
            else:
                prev_center = (rooms[-1][4], rooms[-1][5])
                for tx, ty in tunnel_between(prev_center, (center_x, center_y)):
                    dungeon_map[tx, ty] = True
            
            rooms.append((x1, y1, x2, y2, center_x, center_y))
        
        # Place stairs
        if len(rooms) >= 2:
            stair_room = rooms[-1]
            stair_down = (stair_room[4], stair_room[5])
            stair_up = (rooms[0][4], rooms[0][5])
        
        return dungeon_map, entities, player_start, stair_down, stair_up

# =============================================================================
# PATHFINDING
# =============================================================================

def find_path(start: Tuple[int, int], goal: Tuple[int, int], dungeon_map: np.ndarray, entities: List[Entity]) -> List[Tuple[int, int]]:
    from heapq import heappush, heappop
    
    blocked = set()
    for e in entities:
        if e.blocks and e.is_alive:
            blocked.add((e.x, e.y))
    
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}
    
    while open_set:
        current = heappop(open_set)[1]
        
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return list(reversed(path))
        
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            neighbor = (current[0] + dx, current[1] + dy)
            
            if not (0 <= neighbor[0] < dungeon_map.shape[0] and 0 <= neighbor[1] < dungeon_map.shape[1]):
                continue
            if not dungeon_map[neighbor[0], neighbor[1]]:
                continue
            if neighbor in blocked and neighbor != goal:
                continue
            
            tentative_g = g_score[current] + (1.414 if abs(dx) + abs(dy) == 2 else 1)
            
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + heuristic(neighbor, goal)
                f_score[neighbor] = f
                heappush(open_set, (f, neighbor))
    
    return [start]

# =============================================================================
# FOV SYSTEM
# =============================================================================

class FOVSystem:
    def __init__(self, radius: int = 8):
        self.radius = radius
        self.explored = None
    
    def compute(self, dungeon_map: np.ndarray, player_x: int, player_y: int) -> np.ndarray:
        # Initialize our explored fog-of-war tracking array if it doesn't exist
        if self.explored is None or self.explored.shape != dungeon_map.shape:
            self.explored = np.zeros(dungeon_map.shape, dtype=bool)
        
        # FIX: Convert dungeon_map to a clean boolean 2D NumPy array for transparency.
        # True means light passes through (walkable/floor), False means it's blocked (walls).
        transparency_array = dungeon_map.astype(bool)
        
        # Ensure our player position integer lookups fit within the array dimensions
        height, width = dungeon_map.shape
        safe_x = max(0, min(int(player_x), width - 1))
        safe_y = max(0, min(int(player_y), height - 1))
        
        # Modern tcod expects the 2D boolean array directly as the first argument.
        # IMPORTANT: Since dungeon_map is row-major (y, x), we must pass the pov as (y, x)
        fov = tcod.map.compute_fov(
            transparency=transparency_array,
            pov=(safe_y, safe_x), 
            radius=self.radius, 
            algorithm=tcod.constants.FOV_BASIC
        )
        
        self.explored |= fov
        return fov


# =============================================================================
# CONTENT GENERATION (LLM)
# =============================================================================

class ContentGenerator:
    def __init__(self, ollama: EmbeddedOllama, cache: ContentCache, config: dict):
        self.ollama = ollama
        self.cache = cache
        self.config = config
        self.llm_config = config['llm']
    
    def _generate_cached(self, key: str, prompt: str, parser) -> Any:
        if self.llm_config.get('cache_enabled', True):
            cached = self.cache.get(key, prompt)
            if cached:
                try:
                    return parser(json.loads(cached))
                except:
                    pass
        
        result = self.ollama.generate_json(
            prompt,
            temperature=self.llm_config.get('temperature', 0.7),
            top_p=self.llm_config.get('top_p', 0.9),
            num_predict=self.llm_config.get('num_predict', 1024),
            timeout=self.llm_config.get('timeout', 30)
        )
        
        if result and self.llm_config.get('cache_enabled', True):
            self.cache.set(key, prompt, json.dumps(result), self.llm_config.get('model', 'unknown'))
        
        if result:
            return parser(result)
        return None
    
    def generate_level_theme(self, depth: int, branch: str = "main") -> LevelTheme:
        prompt = f"""Generate a roguelike level theme for depth {depth} in the {branch} branch.
        
        Return JSON:
        {{
          "name": "theme name",
          "description": "atmospheric description",
          "tile_set": "cave|ruins|crypt|fungal|crystal|abyssal",
          "room_types": ["standard", "vault", "shrine", "shop"],
          "monster_theme": "goblin|undead|demon|beast|elemental|abyssal",
          "loot_theme": "martial|arcane|divine|primal",
          "hazards": ["traps", "lava", "gas", "darkness"],
          "boss": {{"name": "", "abilities": []}}
        }}"""
        
        def parse(data):
            return LevelTheme(
                name=data.get("name", f"Level {depth}"),
                difficulty=min(10, depth + 1),
                description=data.get("description", ""),
                room_count=5 + depth,
                trap_density=min(1.0, depth * 0.05),
                treasure_density=max(0.1, 1.0 - depth * 0.05),
                ambient_description=data.get("ambient", ""),
                tile_set=data.get("tile_set", "stone"),
                monster_theme=data.get("monster_theme", "goblin"),
                loot_theme=data.get("loot_theme", "martial"),
                hazards=data.get("hazards", []),
                boss=data.get("boss", {})
            )
        
        result = self._generate_cached(f"level_{depth}_{branch}", prompt, parse)
        if result:
            return result
        
        # Fallback
        return LevelTheme(
            name=f"Level {depth}",
            difficulty=min(10, depth + 1),
            description="A mysterious dungeon level.",
            room_count=5 + depth,
            trap_density=min(1.0, depth * 0.05),
            treasure_density=max(0.1, 1.0 - depth * 0.05),
            ambient_description="The air grows colder as you descend.",
            tile_set="stone",
            monster_theme="goblin",
            loot_theme="martial",
            hazards=["traps"],
            boss={"name": "Boss", "abilities": []}
        )
    
    def generate_monster_roster(self, theme: str, depth: int) -> MobRoster:
        prompt = f"""Create 8 monsters for a {theme} level at depth {depth}.
        Mix of tiers: 3 minion, 3 soldier, 1 elite, 1 boss.
        Each: name, symbol (ASCII), tier, hp, power, defense, speed, skills[], ai_type.
        Return JSON: {{"mobs": [...]}}"""
        
        def parse(data):
            roster = MobRoster()
            roster.add_mobs_from_dict(data.get("mobs", []))
            return roster
        
        result = self._generate_cached(f"monsters_{theme}_{depth}", prompt, parse)
        if result:
            return result
        
        # Fallback
        return create_default_roster()
    
    def generate_items(self, theme: str, count: int = 15) -> List[Item]:
        prompt = f"""Generate {count} items for {theme} theme.
        Types: weapon, armor, potion, scroll, food, misc.
        Rarities: common, uncommon, rare, epic, legendary.
        Include: name, type, rarity, damage, defense, to_hit, weight, value, description, special, appearance.
        Return JSON: {{"items": [...]}}"""
        
        def parse(data):
            items = []
            for i, item_data in enumerate(data.get("items", [])):
                item_type_str = item_data.get("type", "misc")
                try:
                    item_type = ItemType(item_type_str)
                except ValueError:
                    item_type = ItemType.MISC
                
                symbol_map = {
                    ItemType.WEAPON: '/', ItemType.ARMOR: '[', ItemType.POTION: '!',
                    ItemType.SCROLL: '?', ItemType.FOOD: ',', ItemType.MISC: '*'
                }
                
                item = Item(
                    id=f"{theme}_{item_data.get('name', f'item_{i}').lower().replace(' ', '_')}",
                    name=item_data.get("name", f"Item {i}"),
                    item_type=item_type,
                    symbol=item_data.get("symbol", symbol_map.get(item_type, '*')),
                    weight=item_data.get("weight", 1),
                    value=item_data.get("value", 10),
                    damage_bonus=item_data.get("damage", 0),
                    defense_bonus=item_data.get("defense", 0),
                    to_hit_bonus=item_data.get("to_hit", 0),
                    special_effect=item_data.get("special"),
                    effect_strength=item_data.get("strength", 0),
                    description=item_data.get("description", ""),
                    appearance=item_data.get("appearance", ""),
                )
                items.append(item)
            return items
        
        result = self._generate_cached(f"items_{theme}", prompt, parse)
        if result:
            return result
        
        # Fallback items
        return create_default_items(theme)

def create_default_roster() -> MobRoster:
    roster = MobRoster()
    mobs = [
        MobTemplate("Goblin Scout", "g", (100, 200, 100), MobTier.MINION, 5, 2, 0, 120, ["dash"], ai_type="aggressive"),
        MobTemplate("Goblin Soldier", "s", (100, 200, 100), MobTier.SOLDIER, 10, 3, 1, 100, ["shield"], ai_type="tactical"),
        MobTemplate("Goblin Elite", "G", (200, 100, 100), MobTier.ELITE, 15, 4, 2, 90, ["power_attack", "parry"], ai_type="tactical"),
        MobTemplate("Goblin Warlord", "W", (255, 0, 0), MobTier.BOSS, 30, 6, 3, 80, ["war_cry", "whirlwind", "command"], ai_type="tactical"),
    ]
    for mob in mobs:
        roster.add_mob(mob.name.lower().replace(" ", "_"), mob)
    return roster

def create_default_items(theme: str) -> List[Item]:
    items = [
        Item("Iron Longsword", "iron_longsword", ItemType.WEAPON, "/", 5, 50, damage_bonus=3, to_hit_bonus=1, description="A reliable blade."),
        Item("Steel Dagger", "steel_dagger", ItemType.WEAPON, "/", 2, 30, damage_bonus=2, to_hit_bonus=2, description="Light and quick."),
        Item("Apprentice Staff", "apprentice_staff", ItemType.WEAPON, "/", 3, 40, damage_bonus=1, to_hit_bonus=0, special_effect="spell_power", effect_strength=2, description="Channels magic."),
        Item("Iron Mace", "iron_mace", ItemType.WEAPON, "/", 6, 45, damage_bonus=3, to_hit_bonus=0, description="Crushing force."),
        Item("Chain Mail", "chain_mail", ItemType.ARMOR, "[", 15, 60, defense_bonus=3, encumbrance=2, description="Interlinked rings."),
        Item("Leather Armor", "leather_armor", ItemType.ARMOR, "[", 8, 40, defense_bonus=2, encumbrance=1, description="Supple protection."),
        Item("Scale Mail", "scale_mail", ItemType.ARMOR, "[", 12, 55, defense_bonus=3, encumbrance=2, description="Overlapping scales."),
        Item("Robe", "robe", ItemType.ARMOR, "[", 3, 20, defense_bonus=1, encumbrance=0, description="Mage's garment."),
        Item("Wooden Shield", "wooden_shield", ItemType.ARMOR, "[", 5, 25, defense_bonus=2, encumbrance=1, description="Basic block."),
        Item("Holy Symbol", "holy_symbol", ItemType.MISC, "*", 1, 30, special_effect="turn_undead", effect_strength=2, description="Divine focus."),
        Item("Lockpicks (5)", "lockpicks_5", ItemType.MISC, "*", 1, 20, description="For opening locks."),
        Item("Ration (3)", "ration_3", ItemType.FOOD, ",", 2, 10, special_effect="nutrition", effect_strength=300, description="Travel food."),
        Item("Healing Potion", "healing_potion", ItemType.POTION, "!", 1, 50, special_effect="heal", effect_strength=20, description="Restores health."),
        Item("Spellbook: Fire", "spellbook_fire", ItemType.SCROLL, "?", 1, 100, special_effect="learn_spell", effect_strength=1, description="Teaches fireball."),
    ]
    return items

# =============================================================================
# IDENTIFICATION SYSTEM
# =============================================================================

class IdentificationSystem:
    def __init__(self):
        self.identified_types: Set[str] = set()
    
    def identify_type(self, type_id: str):
        self.identified_types.add(type_id)
    
    def identify_item(self, item: Item):
        item.identified = True
        self.identify_type(item.id)
    
    def get_display_name(self, item: Item) -> str:
        if item.identified or item.id in self.identified_types:
            return f"{item.name}{item.get_stat_string()}"
        return item.appearance or f"unidentified {item.item_type.value}"

# =============================================================================
# SURVIVAL SYSTEM (HUNGER)
# =============================================================================

class SurvivalSystem:
    def __init__(self, config: dict):
        self.config = config['gameplay']
    
    def tick(self, player: Entity):
        player.nutrition -= self.config.get('base_nutrition_per_turn', 1)
        player.nutrition = clamp(player.nutrition, 0, self.config.get('max_nutrition', 2000))
        
        if player.nutrition <= 0:
            player.hp -= 1
        elif player.nutrition <= self.config.get('starving_threshold', 200):
            player.apply_effect("starving", 10)
    
    def eat(self, player: Entity, food_value: int):
        player.nutrition = clamp(player.nutrition + food_value, 0, self.config.get('max_nutrition', 2000))

# =============================================================================
# GAME STATE
# =============================================================================

@dataclass
class GameState:
    run_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    seed: int = field(default_factory=lambda: random.randint(0, 2**32-1))
    turn: int = 0
    depth: int = 1
    branch: str = "main"
    kills: int = 0
    gold_found: int = 0
    items_identified: int = 0
    start_time: float = field(default_factory=time.time)
    death_cause: Optional[str] = None
    player_name: str = "Adventurer"
    player_class: str = "warrior"
    flags: Set[str] = field(default_factory=set)
    
    def calculate_score(self) -> int:
        base = self.depth * 100 + self.kills * 10 + self.gold_found
        time_bonus = max(0, 10000 - int(time.time() - self.start_time))
        return base + time_bonus
    
    def on_death(self, cause: str):
        self.death_cause = cause

# =============================================================================
# HIGH SCORES
# =============================================================================

class HighScores:
    def __init__(self, path: Path):
        self.path = path
        self.scores: List[Dict] = []
        self.load()
    
    def load(self):
        if self.path.exists():
            try:
                with open(self.path) as f:
                    self.scores = json.load(f)
            except:
                self.scores = []
    
    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self.scores, f, indent=2)
    
    def add(self, state: GameState):
        entry = {
            "name": state.player_name,
            "class": state.player_class,
            "score": state.calculate_score(),
            "depth": state.depth,
            "kills": state.kills,
            "turns": state.turn,
            "cause": state.death_cause,
            "date": time.strftime("%Y-%m-%d %H:%M"),
            "seed": state.seed,
        }
        self.scores.append(entry)
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        self.scores = self.scores[:20]
        self.save()
    
    def get_display(self) -> List[str]:
        lines = ["═ HIGH SCORES ═"]
        for i, entry in enumerate(self.scores[:10], 1):
            lines.append(f"{i:2}. {entry['name']:12} {entry['class']:8} {entry['score']:6}  D:{entry['depth']:2}  {entry['date']}")
        return lines

# =============================================================================
# SAVE/LOAD
# =============================================================================

class SaveSystem:
    def __init__(self, path: Path):
        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)
    
    def save(self, state: GameState, player: Entity, dungeon_map: np.ndarray, entities: List[Entity], energy_system: EnergySystem):
        save_data = {
            "version": CONFIG['game']['version'],
            "state": {
                "run_id": state.run_id,
                "seed": state.seed,
                "turn": state.turn,
                "depth": state.depth,
                "branch": state.branch,
                "kills": state.kills,
                "gold_found": state.gold_found,
                "items_identified": state.items_identified,
                "start_time": state.start_time,
                "death_cause": state.death_cause,
                "player_name": state.player_name,
                "player_class": state.player_class,
                "flags": list(state.flags),
            },
            "player": {
                "x": player.x, "y": player.y,
                "hp": player.hp, "max_hp": player.max_hp,
                "power": player.power, "defense": player.defense,
                "speed": player.speed, "level": player.level,
                "xp": player.xp, "xp_to_next": player.xp_to_next,
                "skill_points": player.skill_points,
                "known_skills": player.known_skills,
                "nutrition": player.nutrition,
                "gold": player.gold,
                "kill_count": player.kill_count,
                "stats": player.stats,
                "effects": player.effects,
                "identified_types": list(player.identified_types),
                "inventory": self._serialize_inventory(player.inventory),
            },
            "dungeon_map": dungeon_map.tolist(),
            "entities": [self._serialize_entity(e) for e in entities if e is not player],
            "energy_system": [{"entity": self._serialize_entity(e["entity"]), "energy": e["energy"], "speed": e["speed"]} for e in energy_system.entities],
        }
        
        save_file = self.path / f"save_{state.run_id}.json"
        with open(save_file, 'w') as f:
            json.dump(save_data, f)
    
    def _serialize_inventory(self, inv: Inventory) -> Dict:
        return {
            "max_weight": inv.max_weight,
            "items": [self._serialize_item(item) for item in inv.items],
            "equipment": {slot.value: self._serialize_item(item) if item else None for slot, item in inv.equipment.items()},
        }
    
    def _serialize_item(self, item: Item) -> Dict:
        return {
            "id": item.id, "name": item.name, "item_type": item.item_type.value,
            "symbol": item.symbol, "weight": item.weight, "value": item.value,
            "damage_bonus": item.damage_bonus, "defense_bonus": item.defense_bonus,
            "to_hit_bonus": item.to_hit_bonus, "encumbrance": item.encumbrance,
            "special_effect": item.special_effect, "effect_strength": item.effect_strength,
            "description": item.description, "equipped": item.equipped,
            "equipped_slot": item.equipped_slot.value if item.equipped_slot else None,
            "identified": item.identified, "appearance": item.appearance,
        }
    
    def _serialize_entity(self, entity: Entity) -> Dict:
        return {
            "x": entity.x, "y": entity.y, "char": entity.char,
            "color": entity.color, "name": entity.name, "blocks": entity.blocks,
            "hp": entity.hp, "max_hp": entity.max_hp, "power": entity.power,
            "defense": entity.defense, "speed": entity.speed,
            "intel_tier": entity.intel_tier, "is_commander": entity.is_commander,
            "home_position": entity.home_position, "effects": entity.effects,
        }
    
    def load(self, run_id: str) -> Optional[Dict]:
        save_file = self.path / f"save_{run_id}.json"
        if save_file.exists():
            with open(save_file) as f:
                return json.load(f)
        return None
    
    def delete(self, run_id: str):
        save_file = self.path / f"save_{run_id}.json"
        if save_file.exists():
            save_file.unlink()

# =============================================================================
# AI SYSTEMS
# =============================================================================

def interpret_commander_action(commander: Entity, player: Entity, dungeon_map: np.ndarray, entities: List[Entity]) -> Tuple[str, Optional[Tuple[int, int]]]:
    if not commander.current_command:
        return "WAIT", None
    
    cmd = commander.current_command.get("command", "WAIT")
    
    if cmd == "ATTACK_PLAYER":
        return "ATTACK", (player.x, player.y)
    elif cmd == "DEFEND_COMMANDER":
        return "DEFEND", commander.home_position
    elif cmd == "RETREAT_TO_ROOM":
        return "RETREAT", commander.home_position
    elif cmd == "HOLD_POSITION":
        return "WAIT", None
    elif cmd == "FLANK_LEFT":
        return "FLANK", "LEFT"
    elif cmd == "FLANK_RIGHT":
        return "FLANK", "RIGHT"
    else:
        return "WAIT", None

def validate_llm_response(response: Dict) -> Dict:
    valid_commands = ["ATTACK_PLAYER", "DEFEND_COMMANDER", "RETREAT_TO_ROOM", "HOLD_POSITION", "FLANK_LEFT", "FLANK_RIGHT", "DEFAULT_ATTACK", "WAIT"]
    command = response.get("command", "DEFAULT_ATTACK")
    if command not in valid_commands:
        command = "ATTACK_PLAYER"
    shout = response.get("commander_shout", "CHAAAARGE!")
    return {"command": command, "commander_shout": shout}

# =============================================================================
# LLM INTEGRATION
# =============================================================================

llm_request_queue = queue.Queue()
llm_response_queue = queue.Queue()
llm_metrics = {"requests": 0, "responses": 0, "total_latency_ms": 0.0}

def local_llm_worker(ollama: EmbeddedOllama):
    while True:
        try:
            prompt_data = llm_request_queue.get()
            if prompt_data is None:
                break
            
            response = ollama.generate_json(
                prompt_data["prompt"],
                temperature=0.7,
                top_p=0.9,
                num_predict=512,
                timeout=10
            )
            
            if response:
                validated = validate_llm_response(response)
                llm_response_queue.put({
                    "commander_id": prompt_data["commander_id"],
                    "commander_shout": validated["commander_shout"],
                    "command": validated["command"],
                    "request_ts": prompt_data.get("ts", time.time()),
                    "response_ts": time.time()
                })
            else:
                llm_response_queue.put({
                    "commander_id": prompt_data["commander_id"],
                    "commander_shout": "The AI brain stumbles!",
                    "command": "DEFAULT_ATTACK",
                    "request_ts": prompt_data.get("ts", time.time()),
                    "response_ts": time.time()
                })
        except Exception as e:
            llm_response_queue.put({
                "commander_id": "SYSTEM",
                "commander_shout": "The AI brain stumbles!",
                "command": "DEFAULT_ATTACK"
            })
        finally:
            llm_request_queue.task_done()

def enqueue_commander_prompt(commander: Entity, player: Entity, entities: List[Entity]):
    visible_entities = [e for e in entities if e.is_alive and abs(e.x - commander.x) <= 15 and abs(e.y - commander.y) <= 15]
    
    visible_str = json.dumps([
        {"name": e.name, "x": e.x, "y": e.y, "hp": e.hp, "max_hp": e.max_hp, "is_commander": e.is_commander}
        for e in visible_entities
    ])
    
    prompt = f"""You are a {commander.name} commanding forces in a dungeon. Analyze and respond with JSON.

Your Status:
- Position: [{commander.x}, {commander.y}]
- HP: {commander.hp} / {commander.max_hp}

Player Location: [{player.x}, {player.y}] (HP: {player.hp}/{player.max_hp})

Visible Entities:
{visible_str}

Tactical Options:
1. ATTACK_PLAYER - Move aggressively toward the player to strike
2. HOLD_POSITION - Stay put and defend your ground
3. RETREAT_TO_ROOM - Fall back to your home position [{commander.home_position[0]}, {commander.home_position[1]}]
4. DEFEND_COMMANDER - Hold the center position

Response Format (JSON only):
{{
  "commander_shout": "Your battle cry here",
  "command": "ATTACK_PLAYER|HOLD_POSITION|RETREAT_TO_ROOM|DEFEND_COMMANDER"
}}"""
    
    req = {
        "commander_id": commander.name,
        "prompt": prompt,
        "ts": time.time()
    }
    llm_request_queue.put(req)
    global llm_metrics
    llm_metrics["requests"] += 1

def process_llm_responses(entities: List[Entity]):
    while not llm_response_queue.empty():
        try:
            response = llm_response_queue.get_nowait()
            
            global llm_metrics
            llm_metrics["responses"] += 1
            if "request_ts" in response and "response_ts" in response:
                latency = (response["response_ts"] - response["request_ts"]) * 1000
                llm_metrics["total_latency_ms"] += latency
            
            commander_id = response.get("commander_id")
            commander = None
            for e in entities:
                if e.is_commander and e.name == commander_id:
                    commander = e
                    break
            
            if commander:
                commander.current_command = {
                    "command": response["command"],
                    "shout": response["commander_shout"]
                }
        except queue.Empty:
            break

def get_llm_metrics() -> Dict:
    avg_latency = 0.0
    if llm_metrics["responses"] > 0:
        avg_latency = llm_metrics["total_latency_ms"] / llm_metrics["responses"]
    return {
        "requests": llm_metrics["requests"],
        "responses": llm_metrics["responses"],
        "avg_latency_ms": avg_latency,
        "total_latency_ms": llm_metrics["total_latency_ms"]
    }

# =============================================================================
# UI RENDERING
# =============================================================================

class UI:
    def __init__(self, console: tcod.console.Console, config: dict):
        self.console = console
        self.config = config
        self.display_config = config['display']
        self.map_width = config['dungeon']['width']
        self.map_height = config['dungeon']['height']
        self.ui_y = self.map_height + 1
    
    def render_dungeon(self, dungeon_map: np.ndarray, fov: np.ndarray, explored: np.ndarray):
        # NumPy shapes are structured as (height, width) or (rows, columns)
        height, width = dungeon_map.shape
        
        for y in range(height):
            for x in range(width):
                # FIX 1: Look up array values using row-major coordinate structure [y, x]
                if fov[y, x]:
                    if dungeon_map[y, x]:
                        # Print to screen console using normal column/row coordinates (x, y)
                        self.console.print(x, y, ".", COLORS['floor'])
                    else:
                        self.console.print(x, y, "#", COLORS['wall'])
                elif explored[y, x]:
                    if dungeon_map[y, x]:
                        self.console.print(x, y, ".", (50, 50, 50))
                    else:
                        self.console.print(x, y, "#", (30, 30, 30))
    
    def render_entities(self, entities: List[Entity], fov: np.ndarray):
        for entity in entities:
            # Prevent crashes if entity position goes out of bounds
            height, width = fov.shape
            if 0 <= entity.x < width and 0 <= entity.y < height:
                # Render entity code should go here
                pass  # Placeholder for entity rendering logic
    
    def render_combat_log(self, combat_log):
        if combat_log.events:
            recent = combat_log.get_recent(3)
            for i, event in enumerate(recent):
                self.console.print(0, self.ui_y + 5 + i, f"  {event}", COLORS['text'])
    
    def render_ui(self, player, state, combat_log, turn):
        metrics = get_llm_metrics()
        self.console.print(0, self.ui_y + 4, f"LLM: {metrics['responses']}/{metrics['requests']}  Avg: {metrics['avg_latency_ms']:.0f}ms", COLORS['magic'])
        
        # Combat log
        self.render_combat_log(combat_log)
        
        # Controls
        self.console.print(0, self.ui_y + 8, "WASD=Move  I=Inv  C=Char  ,=Pickup  >=Down  <=Up  ESC=Menu", COLORS['text_dim'])

# =============================================================================
# INPUT HANDLING
# =============================================================================

class InputHandler:
    def __init__(self, config: dict):
        self.config = config
    
    def handle_event(self, event: tcod.event.Event, player: Entity, dungeon_map: np.ndarray, entities: List[Entity], state: GameState, game: 'Game') -> bool:
        if isinstance(event, tcod.event.Quit):
            return True  # Quit game
        
        if isinstance(event, tcod.event.KeyDown):
            key = event.sym
            
            # Movement
            dx, dy = 0, 0
            if key == tcod.event.KeySym.W: dy = -1
            elif key == tcod.event.KeySym.S: dy = 1
            elif key == tcod.event.KeySym.A: dx = -1
            elif key == tcod.event.KeySym.D: dx = 1
            elif key == tcod.event.KeySym.UP: dy = -1
            elif key == tcod.event.KeySym.DOWN: dy = 1
            elif key == tcod.event.KeySym.LEFT: dx = -1
            elif key == tcod.event.KeySym.RIGHT: dx = 1
            elif key == tcod.event.KeySym.PERIOD:  # Pickup
                game.pickup_item()
                return False
            elif key == tcod.event.KeySym.COMMA:  # Pickup (alternative)
                game.pickup_item()
                return False
            elif key == tcod.event.KeySym.G:  # Pickup
                game.pickup_item()
                return False
            elif key == tcod.event.KeySym.I:  # Inventory
                game.show_inventory()
                return False
            elif key == tcod.event.KeySym.C:  # Character
                game.show_character()
                return False
            elif key == tcod.event.KeySym.GREATER:  # Stairs down
                game.use_stairs_down()
                return False
            elif key == tcod.event.KeySym.LESS:  # Stairs up
                game.use_stairs_up()
                return False
            elif key == tcod.event.KeySym.ESCAPE:  # Menu
                game.show_menu()
                return False
            elif key == tcod.event.KeySym.SPACE:  # Wait
                dx, dy = 0, 0
            else:
                return False
            
            # Execute movement
            if dx != 0 or dy != 0:
                new_x = player.x + dx
                new_y = player.y + dy
                
                # Check for entity at target
                target_entity = None
                for e in entities:
                    if e.is_alive and e.x == new_x and e.y == new_y and e.blocks:
                        target_entity = e
                        break
                
                if target_entity:
                    # Attack
                    game.attack(player, target_entity)
                else:
                    # Move
                    player.move_to(new_x, new_y, dungeon_map, entities)
            
            return False
        
        return False

# =============================================================================
# MAIN GAME CLASS
# =============================================================================

class Game:
    def __init__(self):
        self.config = CONFIG
        self.running = True
        self.state = GameState()
        self.player: Optional[Entity] = None
        self.dungeon_map: Optional[np.ndarray] = None
        self.entities: List[Entity] = []
        self.energy_system = EnergySystem()
        self.fov_system = FOVSystem(radius=8)
        self.combat_log = CombatLog()
        self.dungeon_generator = DungeonGenerator(self.config)
        self.content_generator = None
        self.ollama: Optional[EmbeddedOllama] = None
        self.cache: Optional[ContentCache] = None
        self.save_system = SaveSystem(SAVES_PATH)
        self.highscores = HighScores(HIGHSCORES_PATH)
        self.identification = IdentificationSystem()
        self.survival = SurvivalSystem(self.config)
        self.current_theme: Optional[LevelTheme] = None
        self.stair_down_pos: Optional[Tuple[int, int]] = None
        self.stair_up_pos: Optional[Tuple[int, int]] = None
        self.fov: Optional[np.ndarray] = None
        self.explored: Optional[np.ndarray] = None
        self.turn = 0
        self.screen_width = self.config['display']['width']
        self.screen_height = self.config['display']['height']
        self.console: Optional[tcod.console.Console] = None
        self.context: Optional[tcod.context.Context] = None
        self.ui: Optional[UI] = None
        self.input_handler: Optional[InputHandler] = None
        self.llm_thread: Optional[threading.Thread] = None
        self.showing_inventory = False
        self.showing_character = False
        self.showing_menu = False
        self.menu_selection = 0
        self.message_log: List[str] = []
    
    def initialize(self):
        # Initialize Ollama
        self.ollama = EmbeddedOllama(self.config['llm']['model'])
        if not self.ollama.start():
            self.add_message("Warning: Could not start Ollama. Using fallback content.")
        elif self.config['llm'].get('auto_pull_model', True):
            if not self.ollama.ensure_model():
                self.add_message("Warning: Could not ensure model. Using fallback content.")
        
        # Initialize cache
        self.cache = ContentCache(CACHE_PATH / "content.db")
        
        # Initialize content generator
        self.content_generator = ContentGenerator(self.ollama, self.cache, self.config)
        
        # Start LLM worker thread
        self.llm_thread = threading.Thread(target=local_llm_worker, args=(self.ollama,), daemon=True)
        self.llm_thread.start()
        
        # Initialize tcod
        tileset_path = ASSETS_PATH / "tilesets" / self.config['display']['tileset']
        if not tileset_path.exists():
            raise FileNotFoundError(f"Tileset not found: {tileset_path}")
        
        try:
            # For DejaVu 10x10 bitmap font (320x80), try with 16 columns and 8 rows
            tileset = tcod.tileset.load_tilesheet(str(tileset_path), 16, 8, tcod.tileset.CHARMAP_TCOD)
        except Exception as e:
            raise RuntimeError(f"Failed to load tileset {tileset_path}: {e}")
        
        self.console = tcod.console.Console(self.screen_width, self.screen_height)
        
        self.context = tcod.context.new_terminal(
            width=self.screen_width,
            height=self.screen_height,
            tileset=tileset,
            title="DarkDelve",
            vsync=True,
        )
        
        self.ui = UI(self.console, self.config)
        self.input_handler = InputHandler(self.config)
        
        # New game or load
        self.new_game()
    
    def new_game(self):
        # Character creation would go here
        self.create_player()
        self.generate_level(1, "main")
        self.turn = 0
        self.state.turn = 0
        self.add_message("Welcome to DarkDelve! Press ESC for menu.")
    
    def create_player(self):
        class_config = self.config['classes'][self.state.player_class]
        
        self.player = Entity(
            x=0, y=0,
            char="@", color=COLORS['player'],
            name=self.state.player_name,
            blocks=True,
            hp=class_config['hp_per_level'] + class_config['stats']['con'],
            max_hp=class_config['hp_per_level'] + class_config['stats']['con'],
            power=5, defense=2, speed=100,
            intel_tier=3, is_commander=False,
            stats=class_config['stats'].copy(),
            level=1, xp=0, xp_to_next=100,
            skill_points=0,
            nutrition=self.config['gameplay']['max_nutrition'],
            max_nutrition=self.config['gameplay']['max_nutrition'],
            inventory=Inventory(max_weight=100),
        )
        
        # Add starting gear
        for gear_id in class_config['start_gear']:
            item = self.create_item_by_id(gear_id)
            if item:
                self.player.inventory.add_item(item)
                # Auto-equip
                if item.item_type in (ItemType.WEAPON, ItemType.ARMOR):
                    slots = self.player.inventory._get_valid_slots_for_item(item)
                    if slots:
                        self.player.inventory.equip(item.id, slots[0])
    
    def create_item_by_id(self, item_id: str) -> Optional[Item]:
        # Check default items
        default_items = create_default_items("martial")
        for item in default_items:
            if item.id == item_id:
                return item
        return None
    
    def generate_level(self, depth: int, branch: str):
        self.state.depth = depth
        self.state.branch = branch
        
        # Generate theme
        self.current_theme = self.content_generator.generate_level_theme(depth, branch)
        self.add_message(f"Entering {self.current_theme.name}: {self.current_theme.description}")
        
        # Generate dungeon
        self.dungeon_map, _, player_start, stair_down, stair_up = self.dungeon_generator.generate_level(depth, branch, self.current_theme)
        self.stair_down_pos = stair_down
        self.stair_up_pos = stair_up
        
        # Generate monsters
        roster = self.content_generator.generate_monster_roster(self.current_theme.monster_theme, depth)
        
        # Spawn entities
        self.entities = [self.player]
        self.player.x, self.player.y = player_start
        self.player.home_position = player_start
        
        # Spawn monsters in rooms
        for _ in range(random.randint(8, 15)):
            template = random.choice(list(roster.mobs.values()))
            # Find valid spawn position
            for _ in range(50):
                x = random.randint(1, self.dungeon_map.shape[0] - 2)
                y = random.randint(1, self.dungeon_map.shape[1] - 2)
                if self.dungeon_map[x, y] and not any(e.x == x and e.y == y for e in self.entities):
                    entity = Entity(
                        x=x, y=y,
                        char=template.symbol, color=template.color,
                        name=template.name, blocks=True,
                        hp=template.hp, max_hp=template.hp,
                        power=template.power, defense=template.defense,
                        speed=template.speed,
                        intel_tier=self._tier_value(template.tier),
                        is_commander=template.tier == MobTier.BOSS,
                    )
                    entity.home_position = (x, y)
                    self.entities.append(entity)
                    break
        
        # Generate items
        items = self.content_generator.generate_items(self.current_theme.loot_theme, 10)
        for item in items:
            for _ in range(20):
                x = random.randint(1, self.dungeon_map.shape[0] - 2)
                y = random.randint(1, self.dungeon_map.shape[1] - 2)
                if self.dungeon_map[x, y] and not any(e.x == x and e.y == y for e in self.entities):
                    entity = Entity(
                        x=x, y=y,
                        char=item.symbol, color=item.color if hasattr(item, 'color') else COLORS['item'],
                        name=item.name, blocks=False,
                        hp=1, max_hp=1, power=0, defense=0,
                        speed=0, intel_tier=0, is_commander=False,
                    )
                    entity.item = item
                    self.entities.append(entity)
                    break
        
        # Initialize energy system
        self.energy_system = EnergySystem()
        for entity in self.entities:
            self.energy_system.add_entity(entity)
        
        # Initialize FOV
        self.fov = self.fov_system.compute(self.dungeon_map, self.player.x, self.player.y)
        self.explored = self.fov_system.explored.copy()
    
    def _tier_value(self, tier: MobTier) -> int:
        return {"minion": 1, "soldier": 2, "elite": 3, "boss": 4}.get(tier.value, 1)
    
    def run(self):
        self.initialize()
        
        try:
            while self.running and self.player.is_alive:
                self.main_loop()
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
    
    def main_loop(self):
        # Get next actor
        actor = self.energy_system.next_actor()
        if not actor:
            return
        
        if actor is self.player:
            self.turn += 1
            self.state.turn = self.turn
            self.combat_log.new_turn()
            
            # Render
            self.render()
            
            # Handle input
            for event in tcod.event.wait():
                if self.input_handler.handle_event(event, self.player, self.dungeon_map, self.entities, self.state, self):
                    self.running = False
                    break
            
            if not self.running:
                return
            
            # Process player turn effects
            self.player.tick_effects()
            if self.config['gameplay'].get('hunger_enabled', True):
                self.survival.tick(self.player)
            
            # Check for level up
            self.check_level_up()
            
        else:
            # Monster turn
            self.monster_turn(actor)
            actor.tick_effects()
        
        # Process LLM responses
        process_llm_responses(self.entities)
        
        # Execute commander actions
        for entity in self.entities:
            if entity.is_alive and entity.is_commander and entity.current_command:
                action, target = interpret_commander_action(entity, self.player, self.dungeon_map, self.entities)
                if action == "ATTACK" and target:
                    path = find_path((entity.x, entity.y), target, self.dungeon_map, self.entities)
                    if len(path) > 1:
                        entity.move_to(path[1][0], path[1][1], self.dungeon_map, self.entities)
                        if path[1] == (self.player.x, self.player.y):
                            self.attack(entity, self.player)
                elif action == "RETREAT" and target:
                    path = find_path((entity.x, entity.y), target, self.dungeon_map, self.entities)
                    if len(path) > 1:
                        entity.move_to(path[1][0], path[1][1], self.dungeon_map, self.entities)
                elif action == "DEFEND" and target:
                    path = find_path((entity.x, entity.y), target, self.dungeon_map, self.entities)
                    if len(path) > 1:
                        entity.move_to(path[1][0], path[1][1], self.dungeon_map, self.entities)
        
        # Update FOV
        self.fov = self.fov_system.compute(self.dungeon_map, self.player.x, self.player.y)
        self.explored = self.fov_system.explored.copy()
        
        # Check win/lose
        if not self.player.is_alive:
            self.game_over()
    
    def monster_turn(self, entity: Entity):
        if not entity.is_alive:
            return
        
        # Simple AI for non-commanders
        if not entity.is_commander:
            dist = max(abs(entity.x - self.player.x), abs(entity.y - self.player.y))
            if dist <= 15:
                entity.move_towards(self.player.x, self.player.y, self.dungeon_map, self.entities)
                if max(abs(entity.x - self.player.x), abs(entity.y - self.player.y)) <= 1:
                    self.attack(entity, self.player)
        else:
            # Commander - enqueue LLM prompt
            enqueue_commander_prompt(entity, self.player, self.entities)
    
    def attack(self, attacker: Entity, defender: Entity):
        event = CombatResolver.resolve_attack(attacker, defender)
        self.combat_log.add_event(event)
        self.add_message(str(event))
        
        if event.result in (HitResult.HIT, HitResult.CRITICAL):
            defender.hp -= event.damage
            if defender.hp <= 0:
                defender.hp = 0
                self.on_kill(attacker, defender)
    
    def on_kill(self, killer: Entity, victim: Entity):
        self.add_message(f"{victim.name} is slain!")
        if killer is self.player:
            self.state.kills += 1
            # XP gain
            xp_gain = victim.max_hp + victim.power * 2
            self.player.xp += xp_gain
            self.add_message(f"Gained {xp_gain} XP.")
            
            # Loot
            if hasattr(victim, 'template') and victim.template.loot_table:
                for loot in victim.template.loot_table:
                    if random.random() < loot.get('probability', 0.5):
                        item = self.create_item_by_id(loot.get('item_id', ''))
                        if item:
                            self.drop_item(item, victim.x, victim.y)
    
    def check_level_up(self):
        while self.player.xp >= self.player.xp_to_next:
            self.player.xp -= self.player.xp_to_next
            self.player.level += 1
            self.player.xp_to_next = int(self.player.xp_to_next * 1.5)
            self.player.skill_points += 1
            self.player.max_hp += self.config['classes'][self.state.player_class]['hp_per_level']
            self.player.hp = self.player.max_hp
            self.add_message(f"Level up! You are now level {self.player.level}!")
    
    def pickup_item(self):
        for entity in self.entities:
            if entity is not self.player and hasattr(entity, 'item') and entity.x == self.player.x and entity.y == self.player.y:
                if self.player.inventory.add_item(entity.item):
                    self.add_message(f"Picked up {entity.item.name}.")
                    self.entities.remove(entity)
                else:
                    self.add_message("Inventory full!")
                break
    
    def drop_item(self, item: Item, x: int, y: int):
        entity = Entity(x=x, y=y, char=item.symbol, color=COLORS['item'], name=item.name, blocks=False, hp=1, max_hp=1)
        entity.item = item
        self.entities.append(entity)
    
    def use_stairs_down(self):
        if self.stair_down_pos and self.player.x == self.stair_down_pos[0] and self.player.y == self.stair_down_pos[1]:
            self.generate_level(self.state.depth + 1, self.state.branch)
            self.add_message("You descend deeper into the dungeon...")
    
    def use_stairs_up(self):
        if self.stair_up_pos and self.player.x == self.stair_up_pos[0] and self.player.y == self.stair_up_pos[1]:
            if self.state.depth > 1:
                self.generate_level(self.state.depth - 1, self.state.branch)
                self.add_message("You climb back up...")
            else:
                self.add_message("You escape the dungeon! Victory!")
                self.victory()
    
    def show_inventory(self):
        self.showing_inventory = True
        while self.showing_inventory:
            self.render_inventory()
            for event in tcod.event.wait():
                if isinstance(event, tcod.event.KeyDown):
                    if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.I):
                        self.showing_inventory = False
                    elif event.sym == tcod.event.KeySym.UP:
                        pass  # Scroll up
                    elif event.sym == tcod.event.KeySym.DOWN:
                        pass  # Scroll down
                    elif event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER):
                        pass  # Use/equip item
    
    def show_character(self):
        self.showing_character = True
        while self.showing_character:
            self.render_character()
            for event in tcod.event.wait():
                if isinstance(event, tcod.event.KeyDown):
                    if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.C):
                        self.showing_character = False
    
    def show_menu(self):
        self.showing_menu = True
        self.menu_selection = 0
        menu_options = ["Resume", "Save & Quit", "Quit (No Save)"]
        
        while self.showing_menu:
            self.render_menu(menu_options)
            for event in tcod.event.wait():
                if isinstance(event, tcod.event.KeyDown):
                    if event.sym == tcod.event.KeySym.ESCAPE:
                        self.showing_menu = False
                    elif event.sym == tcod.event.KeySym.UP:
                        self.menu_selection = (self.menu_selection - 1) % len(menu_options)
                    elif event.sym == tcod.event.KeySym.DOWN:
                        self.menu_selection = (self.menu_selection + 1) % len(menu_options)
                    elif event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER):
                        if self.menu_selection == 0:
                            self.showing_menu = False
                        elif self.menu_selection == 1:
                            self.save_and_quit()
                        elif self.menu_selection == 2:
                            self.quit_no_save()
    
    def save_and_quit(self):
        self.save_system.save(self.state, self.player, self.dungeon_map, self.entities, self.energy_system)
        if self.config['gameplay'].get('score_on_quit', True):
            self.highscores.add(self.state)
        self.add_message("Game saved.")
        self.running = False
        self.showing_menu = False
    
    def quit_no_save(self):
        self.running = False
        self.showing_menu = False
    
    def game_over(self):
        self.add_message("*** YOU DIED ***")
        self.state.on_death("Unknown")
        self.highscores.add(self.state)
        self.save_system.delete(self.state.run_id)
        self.render()
        time.sleep(3)
        self.running = False
    
    def victory(self):
        self.add_message("*** VICTORY! You escaped the dungeon! ***")
        self.state.on_death("Victory")
        self.highscores.add(self.state)
        self.save_system.delete(self.state.run_id)
        self.render()
        time.sleep(3)
        self.running = False
    
    def render(self):
        self.console.clear()
        self.ui.render_dungeon(self.dungeon_map, self.fov, self.explored)
        self.ui.render_entities(self.entities, self.fov)
        self.ui.render_ui(self.player, self.state, self.combat_log, self.turn)
        self.context.present(self.console)
    
    def render_inventory(self):
        self.console.clear()
        lines = [f"═ INVENTORY (Weight: {self.player.inventory.get_total_weight()}/{self.player.inventory.max_weight}) ═", ""]
        lines.append("▼ EQUIPPED:")
        for slot in EquipmentSlot:
            item = self.player.inventory.equipment[slot]
            if item:
                lines.append(f"  {slot.value:12} : {item.display_name(self.player.identified_types)}")
            else:
                lines.append(f"  {slot.value:12} : [empty]")
        
        lines.append("\n▼ BACKPACK:")
        if self.player.inventory.items:
            for item in self.player.inventory.items:
                status = " (E)" if item.equipped else ""
                lines.append(f"  □ {item.display_name(self.player.identified_types)}{status}")
        else:
            lines.append("  (empty)")
        
        for i, line in enumerate(lines):
            self.console.print(2, 2 + i, line, COLORS['text'])
        
        self.context.present(self.console)
    
    def render_character(self):
        self.console.clear()
        lines = [
            f"═ CHARACTER ═",
            f"Name: {self.player.name}",
            f"Class: {self.config['classes'][self.state.player_class]['name']}",
            f"Level: {self.player.level}  XP: {self.player.xp}/{self.player.xp_to_next}",
            f"HP: {self.player.hp}/{self.player.max_hp}",
            f"",
            f"Stats:",
            f"  STR: {self.player.stats['str']}  DEX: {self.player.stats['dex']}  CON: {self.player.stats['con']}",
            f"  INT: {self.player.stats['int']}  WIS: {self.player.stats['wis']}  CHA: {self.player.stats['cha']}",
            f"",
            f"Combat:",
            f"  Power: {self.player.power}  Defense: {self.player.defense}  AC: {self.player.armor_class}",
            f"  To-Hit: +{self.player.to_hit_bonus}  Damage: +{self.player.damage_bonus}",
            f"",
            f"Skills: {', '.join(self.player.known_skills) if self.player.known_skills else 'None'}",
            f"Skill Points: {self.player.skill_points}",
            f"",
            f"Gold: {self.player.gold}  Kills: {self.player.kill_count}",
            f"Nutrition: {self.player.nutrition}/{self.player.max_nutrition}",
        ]
        
        for i, line in enumerate(lines):
            self.console.print(2, 2 + i, line, COLORS['text'])
        
        self.context.present(self.console)
    
    def render_menu(self, options: List[str]):
        self.console.clear()
        self.console.print(self.screen_width // 2 - 10, self.screen_height // 2 - 3, "═ MENU ═", COLORS['gold'])
        for i, option in enumerate(options):
            color = COLORS['gold'] if i == self.menu_selection else COLORS['text']
            prefix = "> " if i == self.menu_selection else "  "
            self.console.print(self.screen_width // 2 - 10, self.screen_height // 2 - 1 + i, f"{prefix}{option}", color)
        self.context.present(self.console)
    
    def add_message(self, msg: str):
        self.message_log.append(msg)
        if len(self.message_log) > 100:
            self.message_log.pop(0)
        print(msg)
    
    def cleanup(self):
        if self.ollama:
            self.ollama.stop()
        if self.context:
            self.context.__exit__(None, None, None)

# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    # Set random seed if provided
    if CONFIG['game']['seed'] is not None:
        random.seed(CONFIG['game']['seed'])
        np.random.seed(CONFIG['game']['seed'])
    
    game = Game()
    game.run()

if __name__ == "__main__":
    main()