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
import traceback
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Set
from enum import Enum
from pathlib import Path

import tcod
import numpy as np
import yaml
import requests

# Import renderer classes
from src.presentation.renderer import create_renderer

# Import combat damage log
from src.infrastructure.persistence.combat_damage_log import CombatDamageLog

# Import damage balance clamping
from src.domain.value_objects.damage_caps import clamp_monster_damage, clamp_player_damage

# Import Fuzion combat system
from src.domain.value_objects.combat_config import COMBAT_CONFIG
from src.shared.utils.dice import parse_dice

# Import emoji lookup tables
from src.presentation.item_emoji import get_item_emoji
from src.presentation.monster_emoji import get_monster_emoji

# Import agent system
from src.domain.agents import (
    Agent, AgentType, AgentManager, LLMAgent, LLMAgentConfig, RandomAgent, CommanderAgent
)
from src.domain.agents.integration import AgentTurnProcessor, AgentTurnContext
from src.domain.agents.state import AgentGameState, EntityState, ItemState

# Import DM LLM integration
from src.domain.value_objects.llm_logging import LLMLogger, LLMCallLog
from src.domain.value_objects.llm_observability import recent_ui_entries
from src.domain.value_objects.perception import PerceptionStatus
from src.domain.services.behavior_script_service import BehaviorScriptService
from src.domain.agents.dungeon_master_agent import DungeonMasterAgent
from src.domain.services.level_design_service import LevelDesignService
from src.infrastructure.external.ollama_service import OllamaService
from src.application.services.llm_worker import llm_worker_func

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
    CONSUMABLE = "potion"
    FOOD = "food"
    WAND = "wand"
    ACCESSORY = "accessory"
    MISC = "misc"

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
    turn: int = 0
    attacker_name: str = ""
    defender_name: str = ""
    to_hit_bonus: int = 0
    target_ac: int = 0          # DEPRECATED alias field — KEPT AS REAL FIELD this release
    d20_roll: int = 0           # DEPRECATED alias field — KEPT AS REAL FIELD this release
    total_roll: int = 0
    result: HitResult = HitResult.MISS
    target_dv: int = 0          # NEW field
    d10_roll: int = 0           # NEW field
    damage: int = 0
    flavor_text: str = ""
    out_of_range: bool = False
    
    def __str__(self, perspective: str = "neutral") -> str:
        """
        Generate a human-readable combat message.
        
        Args:
            perspective: One of "attacker_is_player", "defender_is_player", "neutral"
            - "attacker_is_player": Player is the attacker (first-person language)
            - "defender_is_player": Player is the defender (second-person language)
            - "neutral": Neither is player (third-person language)
        """
        if getattr(self, 'out_of_range', False):
            if perspective == "attacker_is_player":
                return f"Player is out of range to attack {self.defender_name}!"
            elif perspective == "defender_is_player":
                return f"{self.attacker_name} is out of range to attack you!"
            else:
                return f"{self.attacker_name} is out of range to attack {self.defender_name}!"
        
        roll_text = f"[Roll: {self.total_roll} vs DV {self.target_dv}]"
        
        if self.result == HitResult.CRITICAL:
            if perspective == "attacker_is_player":
                return f"Player strikes {self.defender_name} critically! {roll_text} CRITICAL HIT! Damage: {self.damage}"
            elif perspective == "defender_is_player":
                return f"{self.attacker_name} lands a critical hit on you! {roll_text} CRITICAL HIT! Damage: {self.damage}"
            else:
                return f"{self.attacker_name} strikes {self.defender_name} critically! {roll_text} CRITICAL HIT! Damage: {self.damage}"
        
        elif self.result == HitResult.HIT:
            if perspective == "attacker_is_player":
                return f"Player attacks {self.defender_name}! {roll_text} HIT! Damage: {self.damage}"
            elif perspective == "defender_is_player":
                return f"{self.attacker_name} attacks player! {roll_text} HIT! Damage: {self.damage}"
            else:
                return f"{self.attacker_name} attacks {self.defender_name}! {roll_text} HIT! Damage: {self.damage}"
        
        elif self.result == HitResult.MISS:
            if perspective == "attacker_is_player":
                return f"Player attacks {self.defender_name}... {roll_text} MISS!"
            elif perspective == "defender_is_player":
                return f"{self.attacker_name} attacks player... {roll_text} MISS!"
            else:
                return f"{self.attacker_name} attacks {self.defender_name}... {roll_text} MISS!"
        
        elif self.result == HitResult.CRITICAL_FAIL:
            if perspective == "attacker_is_player":
                return f"Player attempts to strike {self.defender_name}... {roll_text} CRITICAL MISS!"
            elif perspective == "defender_is_player":
                return f"{self.attacker_name} attempts to strike player... {roll_text} CRITICAL MISS!"
            else:
                return f"{self.attacker_name} attempts to strike {self.defender_name}... {roll_text} CRITICAL MISS!"
        
        # Fallback
        return f"Combat: {self.attacker_name} vs {self.defender_name}"

@dataclass
class CombatLog:
    events: List[CombatEvent] = field(default_factory=list)
    max_history: int = 20
    turn_counter: int = 0
    
    def add_event(self, event: CombatEvent):
        if event.turn == 0:
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
    symbol: str = "?"
    weight: int = 1
    value: int = 0
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
    effects: Dict[str, int] = field(default_factory=dict)
    glyph: Optional[str] = None
    color: Tuple[int, int, int] = (255, 255, 255)
    equipment_slot: Optional[EquipmentSlot] = None
    # Fuzion fields
    dc: int = 0                             # Damage Class
    kd: int = 0                             # Killing Defense
    sd: int = 0                             # Stun Defense
    ed: int = 0                             # Energy Defense
    required_skill: Optional[str] = None      # Required skill category to equip/use
    
    def __post_init__(self):
        if self.glyph is not None:
            self.symbol = self.glyph
        else:
            # Set symbol based on item_type if not overridden by glyph
            if self.item_type == ItemType.POTION:
                self.symbol = "!"
            elif self.item_type == ItemType.WEAPON:
                self.symbol = "/"
            elif self.item_type == ItemType.ARMOR:
                self.symbol = "["
            elif self.item_type == ItemType.FOOD:
                self.symbol = ","
            elif self.item_type == ItemType.MISC:
                self.symbol = "*"
            elif self.item_type == ItemType.SCROLL:
                self.symbol = "?"
        if self.equipment_slot is not None:
            self.equipped_slot = self.equipment_slot
    
    def get_stat_string(self) -> str:
        stats = []
        if (self.damage_bonus or 0) > 0:
            stats.append(f"+{self.damage_bonus} DMG")
        if (self.to_hit_bonus or 0) > 0:
            stats.append(f"+{self.to_hit_bonus} HIT")
        if (self.defense_bonus or 0) > 0:
            stats.append(f"+{self.defense_bonus} DEF")
        if self.special_effect:
            stats.append(f"{self.special_effect}")
        return " [" + ", ".join(stats) + "]" if stats else ""
    
    def display_name(self, identified_types: Set[str]) -> str:
        if self.identified or self.item_type in (ItemType.POTION, ItemType.SCROLL) and self.id in identified_types:
            return f"{self.name}{self.get_stat_string()}"
        return self.appearance or f"unidentified {self.item_type.value}"

    # -- T-2026-0630-001: properties used by DropCommand / UseCommand --
    @property
    def is_droppable(self) -> bool:
        """Items are droppable unless they are equipped."""
        return not self.equipped

    @property
    def is_usable(self) -> bool:
        """Items are usable if they have a special_effect defined."""
        return self.special_effect is not None

    @property
    def consumable(self) -> bool:
        """A consumable item disappears when used (potions, scrolls, food, wands)."""
        return self.item_type in (ItemType.POTION, ItemType.SCROLL, ItemType.FOOD, ItemType.WAND)

    @property
    def effect(self) -> str:
        """Return the effect string in 'heal+XX' format for UseCommand."""
        if self.special_effect and self.effect_strength:
            return f"{self.special_effect}+{self.effect_strength}"
        return self.special_effect or ""

@dataclass
class Inventory:
    items: List[Item] = field(default_factory=list)
    max_weight: int = 100
    equipment: Dict[EquipmentSlot, Optional[Item]] = field(default_factory=dict)
    capacity: int = 26
    
    def __post_init__(self):
        if not self.equipment:
            self.equipment = {slot: None for slot in EquipmentSlot}
    
    def _weight_value(self, value) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def add_item(self, item: Item) -> bool:
        if item is None:
            return False
        if len(self.items) >= self.capacity:
            return False
        if self.get_total_weight() + self._weight_value(item.weight) > self.max_weight:
            return False
        self.items.append(item)
        return True
    
    def remove_item(self, item_id: str) -> bool:
        for i, item in enumerate(self.items):
            if isinstance(item_id, Item) and item is item_id or not isinstance(item_id, Item) and item.id == item_id:
                if item.equipped:
                    self.unequip(item.id)
                self.items.pop(i)
                return True
        return False
    
    def find_item(self, item_id: str) -> Optional[Item]:
        for item in self.items:
            if item.id == item_id:
                return item
        return None
    
    def get_item(self, index: int) -> Optional[Item]:
        if 0 <= index < len(self.items):
            return self.items[index]
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
        elif item.item_type == ItemType.ACCESSORY:
            name_lower = item.name.lower()
            if "ring" in name_lower:
                return [EquipmentSlot.RING]
            elif "amulet" in name_lower or "necklace" in name_lower or "pendant" in name_lower:
                return [EquipmentSlot.NECK]
        return []
    
    def get_total_weight(self) -> int:
        return sum(self._weight_value(item.effects.get("weight", item.weight)) for item in self.items)
    
    def get_defense_bonus(self) -> int:
        return sum((item.defense_bonus or 0) for item in self.equipment.values() if item and item.equipped)
    
    def get_damage_bonus(self) -> int:
        weapon = self.equipment[EquipmentSlot.MAIN_HAND]
        return (weapon.damage_bonus or 0) if weapon and weapon.equipped else 0
    
    def get_to_hit_bonus(self) -> int:
        weapon = self.equipment[EquipmentSlot.MAIN_HAND]
        return (weapon.to_hit_bonus or 0) if weapon and weapon.equipped else 0

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
    armor_value: int = 0

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
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    x: int = 0
    y: int = 0
    char: str = "@"
    color: Tuple[int, int, int] = (255, 255, 255)
    name: str = "Unknown"
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
    item: Optional["Item"] = None
    
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
    armor_value_override: int = 0
    skills: List[str] = field(default_factory=list)
    combat_dv_modifier: float = 1.0
    combat_av_modifier: float = 1.0
    combat_attack_modifier: float = 1.0
    nutrition: int = 1000
    max_nutrition: int = 2000
    gold: int = 0
    kill_count: int = 0
    identified_types: Set[str] = field(default_factory=set)
    flags: Set[str] = field(default_factory=set)
    
    # Status effects
    effects: Dict[str, int] = field(default_factory=dict)  # effect -> duration
    components: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_alive(self) -> bool:
        return self.hp > 0
    
    @property
    def defense_value(self) -> int:
        stats = getattr(self, 'stats', None)
        if stats is None:
            reflex = 0
        elif hasattr(stats, 'get_modifier'):           # Stats object (defect #8 defensive)
            reflex = stats.get_modifier('dexterity')
        else:                                          # dict-like stats (tests)
            reflex = (stats.get('dex', 10) - 10) // 2
        comp_def = int(self.defense * COMBAT_CONFIG.DEFENSE_COMPRESSION)
        dodge = getattr(self, 'dodge_bonus', 0)
        return COMBAT_CONFIG.BASE_DV + reflex + comp_def + dodge

    @property
    def armor_class(self) -> int:
        # DEPRECATED alias – remove after one release
        return self.defense_value

    @property
    def armor_value(self) -> int:
        base = 0
        if self.inventory:
            base += self.inventory.get_defense_bonus()
        base += self.armor_value_override
        return base
    
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
            # FIX: Check if it's a floor (False), not a wall (True)
            if not dungeon_map[x, y]:
                if not any(e.blocks for e in entities if e.x == x and e.y == y and e is not self):
                    self.x = x
                    self.y = y
                    return True
        return False
    
    def move(self, dx: int, dy: int, dungeon_map: np.ndarray, entities: List['Entity'] = None) -> bool:
        """Legacy delta-movement helper used by older tests and callers."""
        target_x = min(max(self.x + dx, 0), dungeon_map.shape[0] - 1)
        target_y = min(max(self.y + dy, 0), dungeon_map.shape[1] - 1)
        return self.move_to(target_x, target_y, dungeon_map, entities or [])
    
    def distance_to(self, other: 'Entity') -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)
    
    def add_component(self, name: str, component: Any) -> None:
        self.components[name] = component
    
    def get_component(self, name: str) -> Optional[Any]:
        return self.components.get(name)
    
    def remove_component(self, name: str) -> bool:
        return self.components.pop(name, None) is not None
    
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

    # -- T-2026-0630-001: inventory methods used by DropCommand / UseCommand --

    def get_item_count(self, item) -> int:
        """Return the number of items in inventory matching the given item or item id."""
        if not hasattr(self, 'inventory') or self.inventory is None:
            return 0
        item_id = item.id if hasattr(item, 'id') else str(item)
        return sum(1 for i in self.inventory.items if i.id == item_id)

    def add_item(self, item) -> bool:
        """Add an item to this entity's inventory. Returns True on success."""
        if not hasattr(self, 'inventory') or self.inventory is None:
            return False
        return self.inventory.add_item(item)

    def drop_item(self, item) -> bool:
        """Remove an item from inventory (drop it). Returns True if the item was present."""
        if not hasattr(self, 'inventory') or self.inventory is None:
            return False
        item_id = item.id if hasattr(item, 'id') else str(item)
        if self.get_item_count(item_id) <= 0:
            return False
        return self.inventory.remove_item(item_id)

    def use_item(self, item) -> bool:
        """Use an item: apply all effect types, remove consumables. Returns True on success."""
        if not hasattr(self, 'inventory') or self.inventory is None:
            return False
        item_id = item.id if hasattr(item, 'id') else str(item)
        if self.get_item_count(item_id) <= 0:
            return False

        # Apply effects from item
        effect_str = item.effect if hasattr(item, 'effect') and item.effect else ""
        if effect_str:
            self._apply_effect_from_string(effect_str, item)

        # Remove consumable items from inventory
        if hasattr(item, 'consumable') and item.consumable:
            self.inventory.remove_item(item_id)

        return True

    def _apply_effect_from_string(self, effect_str: str, item: Any = None) -> None:
        """Apply an effect from a string format like 'heal+20' or 'nutrition+300'.
        
        Args:
            effect_str: Effect string in format 'type+value'
            item: The item being used (optional, for extracting spell names)
        """
        if "+" not in effect_str:
            return
            
        parts = effect_str.split("+")
        effect_type = parts[0]
        try:
            value = int(parts[1])
        except (ValueError, IndexError):
            return
            
        if effect_type == "heal":
            self.hp = min(self.hp + value, self.max_hp)
        elif effect_type == "nutrition":
            self.nutrition = min(self.nutrition + value, self.max_nutrition)
        elif effect_type == "learn_spell":
            # Add spell to known skills (value indicates spell level or just a flag)
            spell_name = "Unknown Spell"
            if item and hasattr(item, 'name'):
                # Extract spell name from item name if it follows "Spellbook: X" pattern
                if item.name.startswith("Spellbook: "):
                    spell_name = item.name.replace("Spellbook: ", "")
                elif item.name.startswith("Scroll: "):
                    spell_name = item.name.replace("Scroll: ", "")
                else:
                    spell_name = item.name
            if spell_name not in self.known_skills:
                self.known_skills.append(spell_name)
        elif effect_type == "turn_undead":
            # Apply turn undead effect as a status effect with duration based on value
            self.effects["turn_undead"] = value * 5  # Duration in turns
        elif effect_type == "magic_missile":
            # Magic missile effect - could be used to cast the spell
            # For now, add as a known skill/spell
            if "Magic Missile" not in self.known_skills:
                self.known_skills.append("Magic Missile")
        elif effect_type == "spell_power":
            # Increase spell power (could be temporary or permanent)
            # For now, apply as a temporary effect
            self.effects["spell_power"] = value * 10  # Duration in turns

    def remove_effect(self, effect: str) -> bool:
        """Remove an effect from this entity's active effects dict."""
        if hasattr(self, 'effects') and isinstance(self.effects, dict):
            if effect in self.effects:
                del self.effects[effect]
                return True
        return False

# =============================================================================
# COMBAT SYSTEM
# =============================================================================

class CombatResolver:
    @staticmethod
    def resolve_attack(attacker, defender, weapon_dice="1d6", max_range=1) -> CombatEvent:
        from src.domain.services.combat_factors import (
            calculate_attack_value, calculate_defense_value)
        from src.domain.value_objects.fuzion_damage import FuzionDamageCalculator
        distance = abs(attacker.x - defender.x) + abs(attacker.y - defender.y)
        if distance > max_range:
            return CombatEvent(turn=0, attacker_name=attacker.name, defender_name=defender.name,
                             to_hit_bonus=attacker.to_hit_bonus,
                             target_ac=defender.defense_value, target_dv=defender.defense_value,
                             d20_roll=0, d10_roll=0, total_roll=0,
                             result=HitResult.MISS, damage=0, out_of_range=True)
        d10, atk_total = calculate_attack_value(attacker, weapon_dice)
        dv = calculate_defense_value(defender)
        if d10 == COMBAT_CONFIG.DIE_SIDES:
            result = HitResult.CRITICAL
        elif d10 == 1:
            result = HitResult.CRITICAL_FAIL
        elif atk_total >= dv:
            result = HitResult.HIT
        else:
            result = HitResult.MISS
        damage = 0
        if result in (HitResult.HIT, HitResult.CRITICAL):
            is_crit = (result == HitResult.CRITICAL)
            # P3 FIX: Route damage through FuzionDamageCalculator
            # Convert weapon_dice (e.g., "1d6") to weapon_dc (number of d6)
            num_dice, _, _ = parse_dice(weapon_dice)
            weapon_dc = max(1, num_dice)
            fuzion_result = FuzionDamageCalculator().calculate(attacker, defender, weapon_dc, is_critical=is_crit)
            damage = fuzion_result.hits
            if hasattr(defender, 'max_hp') and defender.max_hp > 0:
                defender_is_player = getattr(defender, 'inventory', None) is not None and hasattr(defender, 'xp')
                attacker_is_player = getattr(attacker, 'inventory', None) is not None and hasattr(attacker, 'xp')
                if defender_is_player:
                    damage = clamp_monster_damage(damage, defender.max_hp)
                elif attacker_is_player:
                    damage = clamp_player_damage(damage, defender.max_hp)
        # CB-001 FIX A: single source of truth. `result` (from combat_factors)
        # governs both damage application and logging. Defensively force damage
        # to 0 whenever the roll did not land as HIT/CRITICAL, so the logged
        # `damage`/`flavor_text` can never disagree with `result`/`event_type`.
        if result not in (HitResult.HIT, HitResult.CRITICAL):
            damage = 0
        return CombatEvent(turn=0, attacker_name=attacker.name, defender_name=defender.name,
                         to_hit_bonus=attacker.to_hit_bonus,
                         target_ac=dv, target_dv=dv,
                         d20_roll=d10, d10_roll=d10,
                         total_roll=atk_total, result=result, damage=damage)

# =============================================================================
# ENERGY-BASED TURN SYSTEM
# =============================================================================

class EnergySystem:
    def __init__(self):
        self.entities: List[Dict] = []  # {entity, energy, speed}
        self.turn_count = 0
    
    def add_entity(self, entity: Entity, speed: int = None, initial_energy: int = 0):
        if speed is None:
            speed = entity.speed
        self.entities.append({"entity": entity, "energy": initial_energy, "speed": speed})
    
    def remove_entity(self, entity: Entity):
        self.entities = [e for e in self.entities if e["entity"] is not entity]
    
    def next_actor(self, skip_entity=None) -> Optional[Entity]:
        actors = [e for e in self.entities if e["energy"] >= 100 and e["entity"].is_alive and e["entity"] is not skip_entity]
        if not actors:
            return None
        # Pick the fastest actor among those eligible.
        # Speed determines turn order: faster actors always go first.
        # When speeds are equal, pick randomly to ensure fairness.
        # Energy is only an eligibility threshold (>= 100 to act).
        # This creates natural speed-based turn frequency:
        # - Player (speed=100) acts every frame (gains 100, spends 100)
        # - Minion (speed=50) acts every 2 frames (gains 50/frame, needs 100)
        max_speed = max(e["speed"] for e in actors)
        top_actors = [e for e in actors if e["speed"] == max_speed]
        actor = random.choice(top_actors)
        actor["energy"] -= 100
        return actor["entity"]

    def tick_energy(self) -> None:
        """Increment energy for all entities once per game tick.

        Energy accumulates without cap. Faster actors build up energy
        faster and get more turns. When an actor is picked, 100 energy
        is deducted. This naturally creates speed-based turn frequency:
        - Player (speed=100): gains 100/frame, acts every frame
        - Minion (speed=50): gains 50/frame, acts every 2 frames
        """
        for e in self.entities:
            e["energy"] += e["speed"]
    
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
        
        # Start with all walls (True), then carve out rooms and corridors
        dungeon_map = np.ones((width, height), dtype=bool, order="F")
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
            
            # Carve out the room (set to False = floor)
            # Use x1:x2+1 and y1:y2+1 to ensure the center is always carved
            dungeon_map[x1:x2+1, y1:y2+1] = False
            
            if len(rooms) == 0:
                player_start = (center_x, center_y)
            else:
                prev_center = (rooms[-1][4], rooms[-1][5])
                for tx, ty in tunnel_between(prev_center, (center_x, center_y)):
                    dungeon_map[tx, ty] = False
            
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
            if dungeon_map[neighbor[0], neighbor[1]]:  # Wall = blocked, skip
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
        
        # DarkDelve dungeon maps are indexed as dungeon_map[x, y].
        # True means blocked/wall, False means walkable/floor. tcod expects
        # transparency arrays in the same [x, y] order, so invert the map directly.
        transparency_array = ~dungeon_map
        
        # dungeon_map.shape is (num_x, num_y) — first index is x, second is y.
        num_x, num_y = dungeon_map.shape
        safe_x = max(0, min(int(player_x), num_x - 1))
        safe_y = max(0, min(int(player_y), num_y - 1))
        
        # tcod's pov argument is (row, column) = (x, y) for our array layout.
        fov = tcod.map.compute_fov(
            transparency=transparency_array,
            pov=(safe_x, safe_y),
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
    SAVE_VERSION = "v2"
    
    def __init__(self, path: Path):
        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)
    
    def save(self, state: GameState, player: Entity, dungeon_map: np.ndarray, entities: List[Entity], energy_system: EnergySystem):
        save_data = {
            "version": self.SAVE_VERSION,
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
            "player": self._serialize_player(player),
            "dungeon_map": dungeon_map.tolist(),
            "entities": [self._serialize_entity(e) for e in entities if e is not player],
            "energy_system": [{"entity": self._serialize_entity(e["entity"]), "energy": e["energy"], "speed": e["speed"]} for e in energy_system.entities],
        }
        
        save_file = self.path / f"save_{state.run_id}.json"
        with open(save_file, 'w') as f:
            json.dump(save_data, f)
    
    def _serialize_player(self, player: Entity) -> Dict:
        """Serialize player with Fuzion fields."""
        data = {
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
        }
        # P4 FIX: Serialize Fuzion fields
        if hasattr(player, 'characteristics') and player.characteristics is not None:
            data["characteristics"] = player.characteristics.to_dict()
        if hasattr(player, 'derived') and player.derived is not None:
            data["derived"] = {
                "stun": player.derived.stun,
                "hits": player.derived.hits,
                "sd": player.derived.sd,
                "rec": player.derived.rec,
                "run": player.derived.run,
                "sprint": player.derived.sprint,
                "leap": player.derived.leap,
                "ed": player.derived.ed,
                "end": player.derived.end,
                "spd": player.derived.spd,
                "res": player.derived.res,
                "hum": player.derived.hum,
            }
        if hasattr(player, 'skill_set') and player.skill_set is not None:
            data["skill_set"] = player.skill_set.as_dict()
        return data
    
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
        data = {
            "x": entity.x, "y": entity.y, "char": entity.char,
            "color": entity.color, "name": entity.name, "blocks": entity.blocks,
            "hp": entity.hp, "max_hp": entity.max_hp, "power": entity.power,
            "defense": entity.defense, "speed": entity.speed,
            "intel_tier": entity.intel_tier, "is_commander": entity.is_commander,
            "home_position": entity.home_position, "effects": entity.effects,
        }
        # P4 FIX: Serialize Fuzion fields for entities
        if hasattr(entity, 'characteristics') and entity.characteristics is not None:
            data["characteristics"] = entity.characteristics.to_dict()
        if hasattr(entity, 'derived') and entity.derived is not None:
            data["derived"] = {
                "stun": entity.derived.stun,
                "hits": entity.derived.hits,
                "sd": entity.derived.sd,
                "rec": entity.derived.rec,
                "run": entity.derived.run,
                "sprint": entity.derived.sprint,
                "leap": entity.derived.leap,
                "ed": entity.derived.ed,
                "end": entity.derived.end,
                "spd": entity.derived.spd,
                "res": entity.derived.res,
                "hum": entity.derived.hum,
            }
        if hasattr(entity, 'skill_set') and entity.skill_set is not None:
            data["skill_set"] = entity.skill_set.as_dict()
        return data
    
    def load(self, run_id: str) -> Optional[Dict]:
        save_file = self.path / f"save_{run_id}.json"
        if save_file.exists():
            with open(save_file) as f:
                data = json.load(f)
            # P4 FIX: Migrate v1 saves to v2
            if data.get("version") == "v1":
                data = self.migrate_v1_to_v2(data)
            return data
        return None
    
    def migrate_v1_to_v2(self, state: Dict) -> Dict:
        """Migrate v1 save format to v2 with Fuzion fields."""
        player_data = state.get("player", {})
        # Add characteristics if missing
        if "characteristics" not in player_data:
            player_data["characteristics"] = {"int": 10, "will": 10, "pre": 10, "tech": 10, "ref": 10, "dex": 10, "con": 10, "str": 10, "body": 10, "move": 10}
        # Add derived if missing - derive health from hits
        if "derived" not in player_data:
            hits = player_data.get("hp", 50)
            player_data["derived"] = {
                "stun": hits,
                "hits": hits,
                "sd": 20,
                "rec": 20,
                "run": 20,
                "sprint": 30,
                "leap": 10,
                "ed": 20,
                "end": 100,
                "spd": 5,
                "res": 30,
                "hum": 100,
            }
        # Add skill_set if missing
        if "skill_set" not in player_data:
            player_data["skill_set"] = {"fighting": 2.0, "ranged_weapon": 2.0, "awareness": 2.0, "control": 2.0, "body": 2.0, "social": 2.0, "technique": 2.0, "performance": 2.0, "education": 2.0}
        state["player"] = player_data
        state["version"] = "v2"
        return state
    
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
    def __init__(self, renderer, config: dict):
        self.renderer = renderer
        self.config = config
        self.display_config = config['display']
        self.map_width = config['dungeon']['width']
        self.map_height = config['dungeon']['height']
        self.console_width = self.display_config.get("width", self.display_config.get("screen_width", self.map_width))
        self.console_height = self.display_config.get("height", self.display_config.get("screen_height", self.map_height))
        # UI area starts at the bottom of the map area, but must fit within console_height
        # Reserve 8 rows for UI: status bar, help text, 3 combat message lines, 3 combat log
        # Layout:
        #   ui_y + 0: status bar (HP, AC, Level, Depth, Turn, Gold, Nutrition)
        #   ui_y + 1: help text
        #   ui_y + 2: Player Actions message line
        #   ui_y + 3: Actions Against Player message line
        #   ui_y + 4: Observable/Ambient message line
        #   ui_y + 5: Combat log line 1
        #   ui_y + 6: Combat log line 2
        #   ui_y + 7: Combat log line 3
        if self.console_height > self.map_height + 8:
            self.ui_y = self.map_height + 1
        else:
            # Ensure UI fits within console_height - reserve 8 rows for UI elements
            self.ui_y = max(0, self.console_height - 8)
        # Ensure ui_y is at least map_height to keep UI below map area
        self.ui_y = max(self.ui_y, self.map_height)
        # Camera offset for viewport - centers on player
        self.camera_x = 0
        self.camera_y = 0
    
    def _render_text(self, x: int, y: int, text: str, color):
        """Render text character by character to avoid tile rendering issues"""
        for i, char in enumerate(text):
            self.renderer.print(x + i, y, char, color)
    
    def update_camera(self, player_x: int, player_y: int, dungeon_map: np.ndarray):
        """Update camera to center on player position."""
        # Center the camera on the player
        self.camera_x = player_x - self.console_width // 2
        self.camera_y = player_y - self.console_height // 2
        
        # Clamp camera to map bounds
        self.camera_x = max(0, min(self.camera_x, dungeon_map.shape[0] - self.console_width))
        self.camera_y = max(0, min(self.camera_y, dungeon_map.shape[1] - self.console_height))
    
    def render_dungeon(self, dungeon_map: np.ndarray, fov: np.ndarray, explored: np.ndarray, player=None):
        # DarkDelve's generated maps are indexed as dungeon_map[x, y].
        width, height = dungeon_map.shape
        
        # Update camera to center on player if player is provided
        if player is not None:
            self.update_camera(player.x, player.y, dungeon_map)
        
        for y in range(height):
            for x in range(width):
                # Apply camera offset to get screen coordinates
                screen_x = x - self.camera_x
                screen_y = y - self.camera_y
                
                # Only render if within console bounds
                if screen_x < 0 or screen_x >= self.console_width:
                    continue
                if screen_y < 0 or screen_y >= self.console_height:
                    continue
                    
                # Keep rendering safe if a caller passes differently shaped arrays.
                if y >= fov.shape[1] or x >= fov.shape[0]:
                    continue
                if y >= explored.shape[1] or x >= explored.shape[0]:
                    continue
                    
                # Skip stair positions — they are rendered separately
                if hasattr(self, 'stair_down_pos') and self.stair_down_pos and x == self.stair_down_pos[0] and y == self.stair_down_pos[1]:
                    continue
                if hasattr(self, 'stair_up_pos') and self.stair_up_pos and x == self.stair_up_pos[0] and y == self.stair_up_pos[1]:
                    continue
                
                # Use explicit bool conversion to avoid NumPy array truth ambiguity
                if bool(fov[x, y]):
                    if dungeon_map[x, y]:  # True = wall
                        self.renderer.print(screen_x, screen_y, "#", COLORS['wall'])
                    else:  # False = floor
                        self.renderer.print(screen_x, screen_y, ".", COLORS['floor'])
                elif bool(explored[x, y]):
                    if dungeon_map[x, y]:  # True = wall
                        self.renderer.print(screen_x, screen_y, "#", (30, 30, 30))
                    else:  # False = floor
                        self.renderer.print(screen_x, screen_y, ".", (50, 50, 50))
    
    def render_stairs(self, dungeon_map: np.ndarray, fov: np.ndarray, explored: np.ndarray, player=None,
                      stair_down_pos=None, stair_up_pos=None):
        """Render stairs - only visible when in FOV or explored."""
        width, height = dungeon_map.shape
        
        # Update camera to center on player if player is provided
        if player is not None:
            self.update_camera(player.x, player.y, dungeon_map)
        
        # Render stairs - only visible when in FOV or explored
        if stair_down_pos:
            sx, sy = stair_down_pos
            if 0 <= sx < width and 0 <= sy < height:
                # Check if stairs are in FOV or explored
                in_fov = bool(fov[sx, sy]) if fov is not None and sx < fov.shape[0] and sy < fov.shape[1] else False
                is_explored = bool(explored[sx, sy]) if explored is not None and sx < explored.shape[0] and sy < explored.shape[1] else False
                
                if in_fov or is_explored:
                    screen_x = sx - self.camera_x
                    screen_y = sy - self.camera_y
                    if 0 <= screen_x < self.console_width and 0 <= screen_y < self.console_height:
                        self.renderer.print(screen_x, screen_y, ">", COLORS['gold'])
        
        if stair_up_pos:
            sx, sy = stair_up_pos
            if 0 <= sx < width and 0 <= sy < height:
                # Check if stairs are in FOV or explored
                in_fov = bool(fov[sx, sy]) if fov is not None and sx < fov.shape[0] and sy < fov.shape[1] else False
                is_explored = bool(explored[sx, sy]) if explored is not None and sx < explored.shape[0] and sy < explored.shape[1] else False
                
                if in_fov or is_explored:
                    screen_x = sx - self.camera_x
                    screen_y = sy - self.camera_y
                    if 0 <= screen_x < self.console_width and 0 <= screen_y < self.console_height:
                        self.renderer.print(screen_x, screen_y, "<", COLORS['gold'])
    
    def render_entities(self, entities: List[Entity], fov: np.ndarray, player=None):
        # DarkDelve's FOV arrays are indexed as fov[x, y].
        height, width = fov.shape[1], fov.shape[0]
        player_x = getattr(player, "x", None)
        player_y = getattr(player, "y", None)
        visible_entities: List[Entity] = []
        player_entity = None

        for entity in entities:
            if 0 <= entity.x < width and 0 <= entity.y < height:
                # Skip dead entities — they should not be rendered.
                if hasattr(entity, 'is_alive') and not entity.is_alive:
                    continue
                # Only render entities in field of view, the player, or entities sharing the player's tile.
                at_player_position = (
                    player is not None
                    and player_x is not None
                    and player_y is not None
                    and entity.x == player_x
                    and entity.y == player_y
                )
                # Explicit bool conversion for NumPy array element
                if bool(fov[entity.x, entity.y]) or entity is player or at_player_position:
                    if entity is player:
                        player_entity = entity
                    else:
                        visible_entities.append(entity)

        if player_entity is None and player is not None:
            render_player_x = getattr(player, "x", None)
            render_player_y = getattr(player, "y", None)
            if render_player_x is not None and render_player_y is not None and 0 <= render_player_x < width and 0 <= render_player_y < height:
                player_entity = player

        for entity in visible_entities:
            # Apply camera offset to get screen coordinates
            screen_x = entity.x - self.camera_x
            screen_y = entity.y - self.camera_y
            # Only render if within console bounds
            if 0 <= screen_x < self.console_width and 0 <= screen_y < self.console_height:
                self.renderer.print(screen_x, screen_y, entity.char, entity.color)
        if player_entity is not None:
            # Apply camera offset for player
            screen_x = player_entity.x - self.camera_x
            screen_y = player_entity.y - self.camera_y
            if 0 <= screen_x < self.console_width and 0 <= screen_y < self.console_height:
                self.renderer.print(screen_x, screen_y, player_entity.char, player_entity.color)
    
    def render_combat_log(self, combat_log):
        events = getattr(combat_log, "events", [])
        if events:
            recent = combat_log.get_recent(3)
            for i, event in enumerate(recent):
                # Render combat log at ui_y + 5, 6, 7 (below the 3 message lines)
                self._render_text(0, self.ui_y + 5 + i, f"  {event}"[:self.console_width], COLORS['text'])

    def render_combat_messages(self, game):
        """
        Render three categorized combat message lines.
        
        Reads from game.combat_message_log which is a dict with keys:
          - "player_actions": list of str (most recent last)
          - "against_player": list of str (most recent last)
          - "observable": list of str (most recent last)
        
        Each line shows the most recent message in its category.
        If no message exists, show an empty line.
        """
        combat_msgs = getattr(game, "combat_message_log", None)
        if combat_msgs is None:
            # Fallback: render nothing if attribute doesn't exist
            return
        
        # Line 1: Player Actions (ui_y + 2) - yellow/bright color
        player_actions = combat_msgs.get("player_actions", [])
        if player_actions:
            msg = player_actions[-1]
            prefix = "[YOU] "
            self._render_text(0, self.ui_y + 2, (prefix + msg)[:self.console_width], COLORS['hp_high'])
        else:
            self._render_text(0, self.ui_y + 2, "[YOU] "[:self.console_width], COLORS['text_dim'])
        
        # Line 2: Actions Against Player (ui_y + 3) - red color
        against_player = combat_msgs.get("against_player", [])
        if against_player:
            msg = against_player[-1]
            prefix = "[ATK] "
            self._render_text(0, self.ui_y + 3, (prefix + msg)[:self.console_width], COLORS['hp_low'])
        else:
            self._render_text(0, self.ui_y + 3, "[ATK] "[:self.console_width], COLORS['text_dim'])
        
        # Line 3: Observable/Ambient (ui_y + 4) - dim color
        observable = combat_msgs.get("observable", [])
        if observable:
            msg = observable[-1]
            prefix = "[OBS] "
            self._render_text(0, self.ui_y + 4, (prefix + msg)[:self.console_width], COLORS['text'])
        else:
            self._render_text(0, self.ui_y + 4, "[OBS] "[:self.console_width], COLORS['text_dim'])

    def render_ui(self, player, state, combat_log, turn, game=None):
        metrics = get_llm_metrics()
        hp = getattr(player, "hp", "?")
        max_hp = getattr(player, "max_hp", "?")
        level = getattr(player, "level", "?")
        depth = getattr(state, "depth", "?")
        try:
            defense_value = player.defense_value
            armor_value = player.armor_value
        except AttributeError:
            defense_value = getattr(player, "defense_value", "?")
            armor_value = getattr(player, "armor_value", "?")
        status = (
            f"HP {hp}/{max_hp}  DV {defense_value} AV {armor_value}  "
            f"Level {level}  Depth {depth}  Turn {turn}  "
            f"Gold {getattr(player, 'gold', 0)}  Nutrition {getattr(player, 'nutrition', 0)}/{getattr(player, 'max_nutrition', 0)}"
        )
        self._render_text(0, self.ui_y, status[:self.console_width], COLORS['text'])
        self._render_text(0, self.ui_y + 1, "WASD=Move  E=Wait  I=Inv  C=Char  ,=Pickup  >=Down  <=Up  ESC=Menu", COLORS['text_dim'])

        if game is not None:
            self.render_combat_messages(game)

        # Combat log at ui_y + 5, 6, 7
        self.render_combat_log(combat_log)
        
        # LLM activity feed (if DM enabled)
        if game is not None and getattr(game, 'dm_enabled', False) and getattr(game, 'llm_logger', None):
            recent = game.llm_logger.get_recent_entries(3)
            for i, entry in enumerate(recent):
                status = "OK" if entry.success else "FAIL"
                self._render_text(0, self.console_height - 4 + i,
                    f"DM T{entry.turn_number} {entry.call_type} {entry.latency_ms:.0f}ms {status}",
                    COLORS['gold'])

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

            # When a UI overlay (menu, inventory, character) is showing, the
            # overlay's own event loop owns all key input.  Do not process
            # movement or action keys here or the player will move/act while
            # the overlay is open.
            if game.showing_menu or game.showing_inventory or game.showing_character:
                return False

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
            elif key in (tcod.event.KeySym.SPACE, tcod.event.KeySym.E):  # Wait
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
                elif dungeon_map is not None:
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
        self.combat_damage_log = CombatDamageLog()
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
        self.context: Optional[tcod.context.Context] = None
        self.renderer: Optional[Renderer] = None
        self.ui: Optional[UI] = None
        self.input_handler: Optional[InputHandler] = None
        self.llm_thread: Optional[threading.Thread] = None
        self.showing_inventory = False
        self.showing_character = False
        self.showing_menu = False
        self.menu_selection = 0
        self.message_log: List[str] = []
        self.combat_message_log: Dict[str, List[str]] = {
            "player_actions": [],
            "against_player": [],
            "observable": [],
        }
        
        # Agent system integration
        self.agent_manager = AgentManager()
        self.turn_processor: Optional[AgentTurnProcessor] = None
        
        # DM LLM integration
        self.dm_enabled = False
        self.llm_logger: Optional[LLMLogger] = None
        self.dm_agent: Optional[DungeonMasterAgent] = None
        self.llm_request_queue: Optional[queue.Queue] = None
        self.llm_response_queue: Optional[queue.Queue] = None
        self.llm_max_calls = 5
        self.llm_calls_this_turn = 0
    
    @property
    def console(self):
        """Backward-compatible access to the underlying tcod console."""
        if self.renderer is not None and hasattr(self.renderer, '_console'):
            return self.renderer._console
        return None
    
    def initialize(self):
        # Keep display dimensions in sync when tests or callers override config.
        self.config['display'].setdefault('width', CONFIG['display']['width'])
        self.config['display'].setdefault('height', CONFIG['display']['height'])
        self.config['display'].setdefault('renderer', CONFIG['display']['renderer'])
        self.config['display'].setdefault('tileset', CONFIG['display']['tileset'])
        self.config['dungeon'].setdefault('width', CONFIG['dungeon']['width'])
        self.config['dungeon'].setdefault('height', CONFIG['dungeon']['height'])
        self.config['dungeon'].setdefault('max_rooms', CONFIG['dungeon']['max_rooms'])
        self.config['dungeon'].setdefault('room_min_size', CONFIG['dungeon']['room_min_size'])
        self.config['dungeon'].setdefault('room_max_size', CONFIG['dungeon']['room_max_size'])
        self.screen_width = self.config['display']['width']
        self.screen_height = self.config['display']['height']
        
        # Rebuild the dungeon generator after config overrides so tests and callers
        # that construct Game() then replace game.config do not use stale defaults.
        self.dungeon_generator = DungeonGenerator(self.config)
        
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
        
        # Initialize agent turn processor
        self.turn_processor = AgentTurnProcessor(self)
        self.turn_processor.set_llm_queues(llm_request_queue, llm_response_queue)
        
        # Initialize DM LLM integration
        dm_config = self.config.get('dungeon_master', {})
        self.dm_enabled = dm_config.get('enabled', False)
        self.llm_logger = LLMLogger(log_path=dm_config.get('log_path', 'logs/llm_activity.json'))
        self.llm_request_queue = queue.Queue(maxsize=50)
        self.llm_response_queue = queue.Queue(maxsize=50)
        self.llm_max_calls = dm_config.get('max_calls_per_turn', 5)
        self.llm_calls_this_turn = 0
        
        if self.dm_enabled:
            ollama_service = OllamaService(base_url=dm_config.get('ollama_endpoint', 'http://localhost:11434'))
            level_design = LevelDesignService(self.llm_logger, ollama_service)
            self.dm_agent = DungeonMasterAgent(ollama_service, level_design, self.llm_logger)
            self.llm_worker = threading.Thread(target=llm_worker_func, args=(
                self.llm_request_queue, self.llm_response_queue,
                self.dm_agent, self.llm_logger, self.llm_max_calls
            ), daemon=True)
            self.llm_worker.start()
        
        # Initialize tcod
        tileset_path = ASSETS_PATH / "tilesets" / self.config['display']['tileset']
        if not tileset_path.exists():
            raise FileNotFoundError(f"Tileset not found: {tileset_path}")
        
        # Create appropriate renderer based on config.
        self.renderer = create_renderer(self.config, self.config['display']['renderer'])
        
        # Keep context for compatibility with other parts of the code
        if hasattr(self.renderer, '_context'):
            self.context = self.renderer._context
        else:
            self.context = None
        
        self.ui = UI(self.renderer, self.config)
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
        
        
        # P4 FIX: Attach Fuzion fields to runtime player Entity for save/load round-trip
        from src.domain.value_objects.fuzion_stats import PrimaryCharacteristics, DerivedCharacteristics, SkillSet
        self.player.characteristics = PrimaryCharacteristics()
        self.player.derived = DerivedCharacteristics.from_primary(self.player.characteristics)
        self.player.skill_set = SkillSet.everyman()
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
        
        # Apply Fuzion combat skills to player entity
        from src.domain.services.player_profile_service import PlayerProfileService
        svc = PlayerProfileService()
        svc.apply_combat_skills_to_entity(self.player)
    
    def create_item_by_id(self, item_id: str) -> Optional[Item]:
        # Check default items with case-insensitive lookup.
        # Config uses "iron_longsword" format, items use "Iron Longsword".
        def _normalize(s: str) -> str:
            return s.lower().replace(" ", "_").replace("(", "").replace(")", "")
        target = _normalize(item_id)
        default_items = create_default_items("martial")
        for item in default_items:
            if _normalize(item.id) == target:
                return item
        return None
    
    def generate_level(self, depth: int, branch: str):
        self.state.depth = depth
        self.state.branch = branch
        
        # Use specialized floor 1 generator for entrance level
        if depth == 1:
            self._generate_floor1()
        else:
            self._generate_standard_level(depth, branch)
    
    def _generate_floor1(self):
        """Generate floor 1 (dungeon entrance) with specialized layout."""
        from src.application.services.floor1_generator import Floor1Generator
        from src.application.services.floor1_spawner import Floor1Spawner
        
        # Generate floor data
        floor1_gen = Floor1Generator(self.config)
        floor1_data = floor1_gen.generate()
        
        # Apply map
        self.dungeon_map = floor1_data.dungeon_map
        self.stair_down_pos = floor1_data.stair_down
        self.stair_up_pos = floor1_data.entrance  # Go back up = entrance
        
        # Place player at entrance
        self.player.x, self.player.y = floor1_data.entrance
        self.player.home_position = floor1_data.entrance
        
        # Spawn entities
        spawner = Floor1Spawner(self.player, self.config, self.dungeon_map)
        self.entities = [self.player]
        self.entities.extend(spawner.spawn_all(floor1_data, None))
        
        # Generate minimal items (most loot is in dens)
        items = self.content_generator.generate_items("martial", 5)
        for item in items:
            for _ in range(20):
                x = random.randint(1, self.dungeon_map.shape[0] - 2)
                y = random.randint(1, self.dungeon_map.shape[1] - 2)
                # Only place on floor, not on entities, and not on main path
                main_path_set = set(floor1_data.main_path)
                if (not self.dungeon_map[x, y]
                        and not any(e.x == x and e.y == y for e in self.entities)
                        and (x, y) not in main_path_set):
                    entity = Entity(
                        x=x, y=y,
                        char=item.symbol, color=COLORS['item'],
                        name=item.name, blocks=False,
                        hp=1, max_hp=1, power=0, defense=0,
                        speed=0, intel_tier=0, is_commander=False,
                    )
                    entity.item = item
                    self.entities.append(entity)
                    break

        # Register AI agents for floor 1 monsters
        for entity in self.entities:
            if entity is self.player:
                continue
            if getattr(entity, 'is_commander', False):
                agent = CommanderAgent(entity, home_position=(entity.x, entity.y))
            else:
                agent = RandomAgent(entity, agent_type=AgentType.MONSTER)
            self.agent_manager.register_agent(agent)
        
        # Request behavior scripts from LLM for non-player entities
        if self.dm_enabled and self.config.get('dungeon_master', {}).get('enable_behavior_generation', True):
            for entity in self.entities:
                if entity is self.player:
                    continue
                if not hasattr(entity, 'behavior_script'):
                    perception = self._get_perception_for_entity(entity)
                    self.llm_request_queue.put({
                        'type': 'behavior',
                        'entity_id': entity.id,
                        'mob_type': getattr(entity, 'mob_type', 'default'),
                        'perception': perception.as_dict() if perception else {},
                        'social_context': '',
                        'valid_conditions': ['can_see_player', 'can_hear_player', 'health_below', 'in_combat'],
                        'valid_actions': ['attack', 'flee', 'patrol', 'wait'],
                        'turn_number': self.turn,
                        'prompt_summary': f'Behavior for {entity.name}',
                    })

        # Initialize energy system
        self.energy_system = EnergySystem()
        for entity in self.entities:
            initial_energy = 100 if entity is self.player else 0
            self.energy_system.add_entity(entity, initial_energy=initial_energy)
        
        # Initialize FOV - reset explored state for new level
        self.fov_system.explored = None
        self.fov = self.fov_system.compute(self.dungeon_map, self.player.x, self.player.y)
        self.explored = self.fov_system.explored.copy()
        
        self.add_message("You enter the dungeon entrance. The air smells of damp stone and something rotten.")
    
    def _generate_standard_level(self, depth: int, branch: str):
        """Generate standard dungeon level (depth > 1)."""
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
        
        # Ensure player starts on a walkable position
        if self.dungeon_map[player_start[0], player_start[1]]:
            print(f"WARNING: Player start position {player_start} is a wall, finding walkable position...")
            # Find the nearest walkable position
            found_walkable = False
            for radius in range(1, 20):
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        new_x, new_y = player_start[0] + dx, player_start[1] + dy
                        if (0 <= new_x < self.dungeon_map.shape[0] and
                            0 <= new_y < self.dungeon_map.shape[1] and
                            not self.dungeon_map[new_x, new_y]):
                            player_start = (new_x, new_y)
                            print(f"Found walkable position: {player_start}")
                            found_walkable = True
                            break
                    if found_walkable:
                        break
                if found_walkable:
                    break
            
            # If no walkable position found, search the entire map
            if not found_walkable:
                print("WARNING: Could not find walkable position near start, searching entire map...")
                for x in range(self.dungeon_map.shape[0]):
                    for y in range(self.dungeon_map.shape[1]):
                        if not self.dungeon_map[x, y]:
                            player_start = (x, y)
                            print(f"Found walkable position: {player_start}")
                            found_walkable = True
                            break
                    if found_walkable:
                        break
            
            # If still no walkable position, carve a floor at the player's position
            if not found_walkable:
                print("WARNING: No walkable positions found, carving floor at player position...")
                self.dungeon_map[player_start[0], player_start[1]] = False
        
        self.player.x, self.player.y = player_start
        self.player.home_position = player_start
        
        # Spawn monsters in rooms
        for _ in range(random.randint(8, 15)):
            template = random.choice(list(roster.mobs.values()))
            # Find valid spawn position
            for _ in range(50):
                x = random.randint(1, self.dungeon_map.shape[0] - 2)
                y = random.randint(1, self.dungeon_map.shape[1] - 2)
                # FIX: Spawn monsters on floors (False), not walls (True)
                if not self.dungeon_map[x, y] and not any(e.x == x and e.y == y for e in self.entities):
                    # Apply speed scaling based on tier:
                    # Player speed = 100. Monsters are slower to give player advantage.
                    # Minion: 50% of player speed, Soldier: 60%, Elite: 70%, Boss: 80%
                    # Use the HIGHER of: tier-based speed, or template speed
                    tier_speed_scale = {
                        MobTier.MINION: 0.50,
                        MobTier.SOLDIER: 0.60,
                        MobTier.ELITE: 0.70,
                        MobTier.BOSS: 0.80,
                    }
                    speed_scale = tier_speed_scale.get(template.tier, 0.50)
                    tier_based_speed = max(1, int(self.player.speed * speed_scale))
                    monster_speed = max(template.speed, tier_based_speed)

                    entity = Entity(
                        x=x, y=y,
                        char=template.symbol, color=template.color,
                        name=template.name, blocks=True,
                        hp=template.hp, max_hp=template.hp,
                        power=template.power, defense=template.defense,
                        speed=monster_speed,
                        intel_tier=self._tier_value(template.tier),
                        is_commander=template.tier == MobTier.BOSS,
                        armor_value_override=template.armor_value,
                        skills=list(template.skills),
                    )
                    entity.home_position = (x, y)
                    self.entities.append(entity)
                    # Apply Fuzion-aware difficulty modifiers if available
                    adj = getattr(self, 'difficulty_adjustment', None)
                    if adj is not None:
                        from src.domain.services.combat_factors import apply_difficulty
                        apply_difficulty(entity, adj)
                    
                    # Assign agent to monster
                    if template.tier == MobTier.BOSS:
                        agent = CommanderAgent(entity, home_position=(x, y))
                    else:
                        agent = RandomAgent(entity, agent_type=AgentType.MONSTER)
                    self.agent_manager.register_agent(agent)
                    break
        
        # Generate items
        items = self.content_generator.generate_items(self.current_theme.loot_theme, 10)
        for item in items:
            for _ in range(20):
                x = random.randint(1, self.dungeon_map.shape[0] - 2)
                y = random.randint(1, self.dungeon_map.shape[1] - 2)
                # FIX: Spawn items on floors (False), not walls (True)
                if not self.dungeon_map[x, y] and not any(e.x == x and e.y == y for e in self.entities):
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

        # Register AI agents for floor 1 monsters
        for entity in self.entities:
            if entity is self.player:
                continue
            if getattr(entity, 'is_commander', False):
                agent = CommanderAgent(entity, home_position=(entity.x, entity.y))
            else:
                agent = RandomAgent(entity, agent_type=AgentType.MONSTER)
            self.agent_manager.register_agent(agent)

        # Initialize energy system
        self.energy_system = EnergySystem()
        for entity in self.entities:
            initial_energy = 100 if entity is self.player else 0
            self.energy_system.add_entity(entity, initial_energy=initial_energy)
        
        # Initialize FOV - reset explored state for new level
        self.fov_system.explored = None
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
        except Exception as e:
            # Print full traceback with line numbers for debugging
            print(f"\n\n=== GAME CRASHED ===")
            print(f"Error: {e}")
            print(f"\nTraceback:")
            traceback.print_exc()
            print(f"=== END CRASH ===\n")
        finally:
            self.cleanup()

    def main_loop(
        self,
        action: Optional[str] = None,
        render_to_stdout: bool = True,
        frame_text: Optional[str] = None,
    ) -> Optional[str]:
        try:
            # Advance energy for all actors once per tick, then process all ready actors
            self.energy_system.tick_energy()

            # Process all actors that have enough energy (player + monsters)
            # The player acts first if ready, then all monsters in energy order
            actors_processed = 0
            max_actors_per_tick = len(self.entities) * 2  # safety limit
            player_acted_this_frame = False

            while actors_processed < max_actors_per_tick:
                # Skip the player on subsequent iterations to prevent duplicate picks
                skip = self.player if player_acted_this_frame else None
                actor = self.energy_system.next_actor(skip_entity=skip)
                if not actor:
                    break

                if actor is self.player:
                    player_acted_this_frame = True
                    self.turn += 1
                    self.state.turn = self.turn
                    self.combat_log.new_turn()

                    # Render before input so the agent sees the current state.
                    if frame_text is None:
                        frame_text = self.render_frame_text()
                    if render_to_stdout:
                        self.renderer.present()

                    if action is None:
                        # Handle input
                        events = self._wait_for_events()
                        for event in events:
                            if self.input_handler.handle_event(event, self.player, self.dungeon_map, self.entities, self.state, self):
                                self.running = False
                                break
                    else:
                        if self.process_action(action):
                            self.running = False

                    if not self.running:
                        return frame_text

                    # Process player turn effects
                    self.player.tick_effects()
                    if self.config['gameplay'].get('hunger_enabled', True):
                        self.survival.tick(self.player)

                    # Check for level up
                    self.check_level_up()

                    actors_processed += 1
                else:
                    # Monster turn - use agent system if available, otherwise default AI
                    agent = self.agent_manager.get_agent_for_entity(actor)
                    if agent and self.turn_processor:
                        # Use AgentTurnProcessor for agent-controlled entities
                        self.turn_processor.process_actor_turn(actor, agent)
                    else:
                        # Fall back to default AI
                        self.monster_turn(actor)
                    actor.tick_effects()
                    actors_processed += 1

            # Render after all monster turns so the player can see movement
            if render_to_stdout and actors_processed > 0:
                self.renderer.present()

            # Process LLM responses (for DM LLM integration)
            if self.dm_enabled:
                self.llm_calls_this_turn = 0  # reset per turn
                self._process_llm_responses()

            # Process LLM responses (for commander entities that use the legacy system)
            process_llm_responses(self.entities)

            # Execute commander actions (for commanders using the legacy LLM system)
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

            return frame_text
        except Exception as e:
            # Print full traceback with line numbers for debugging
            print(f"\n\n=== ERROR IN MAIN LOOP (turn {self.turn}) ===")
            print(f"Error: {e}")
            print(f"\nTraceback:")
            traceback.print_exc()
            print(f"=== END ERROR ===\n")
            self.running = False
            raise

    def process_action(self, action: str) -> bool:
        """Apply one library-supplied action without blocking for input.

        This mirrors the safe subset of [`InputHandler.handle_event()`](darkdelve.py:1701)
        that is useful for automated playtests. The ``i`` inventory action is
        intentionally treated as a no-op here so the library driver never enters
        the blocking inventory screen without a second input event.
        """

        normalized = (action or "").strip().lower()
        if not normalized:
            return False

        if normalized in {"\x03", "\x04", "\x1b"}:
            self.running = False
            return True

        if self.player is None:
            return False

        # Open menu action
        if normalized == "m":
            self.show_menu()
            return False

        # Handle menu navigation if menu is showing
        if self.showing_menu:
            if normalized in {"\x1b", "escape"}:
                self.showing_menu = False
                return False
            elif normalized in {"\x1b[a", "up"}:
                self.menu_selection = (self.menu_selection - 1) % 3
                return False
            elif normalized in {"\x1b[b", "down"}:
                self.menu_selection = (self.menu_selection + 1) % 3
                return False
            elif normalized in {"\r", "\n", "enter", " "}:
                if self.menu_selection == 0:
                    self.showing_menu = False
                elif self.menu_selection == 1:
                    self.save_and_quit()
                elif self.menu_selection == 2:
                    self.quit_no_save()
                return False

        if normalized in {"w", "a", "s", "d", "e", " ", "\r", "\n"}:
            dx, dy = 0, 0
            if normalized == "w":
                dy = -1
            elif normalized == "s":
                dy = 1
            elif normalized == "a":
                dx = -1
            elif normalized == "d":
                dx = 1

            if dx or dy:
                new_x = self.player.x + dx
                new_y = self.player.y + dy
                target_entity = None
                for entity in self.entities:
                    if (
                        entity is not self.player
                        and entity.is_alive
                        and entity.x == new_x
                        and entity.y == new_y
                        and entity.blocks
                    ):
                        target_entity = entity
                        break

                if target_entity:
                    self.attack(self.player, target_entity)
                elif self.dungeon_map is not None:
                    self.player.move_to(new_x, new_y, self.dungeon_map, self.entities)
            return False

        if normalized in {",", "."}:
            self.pickup_item()
            return False

        if normalized == ">":
            self.use_stairs_down()
            return False

        if normalized == "<":
            self.use_stairs_up()
            return False

        return False

    def _console_text(self) -> str:
        """Return the current renderer console as plain text."""

        # Try both _console (TileRenderer) and _root_console (ConsoleRenderer)
        console = getattr(self.renderer, "_console", None)
        if console is None:
            console = getattr(self.renderer, "_root_console", None)
        if console is None:
            return ""

        visible_width = console.width
        visible_height = console.height
        return "\n".join(
            "".join(chr(int(ch)) if int(ch) else " " for ch in row[:visible_width])
            for row in console.ch[:visible_height]
        )

    def _render_to_console(self) -> None:
        """Render the active game view into the current renderer console."""

        if self.renderer is None or self.ui is None:
            return
        if self.dungeon_map is None or self.fov is None or self.explored is None:
            return

        self.renderer.clear()
        self.ui.render_dungeon(self.dungeon_map, self.fov, self.explored, self.player)
        self.ui.render_entities(self.entities, self.fov, self.player)
        self.ui.render_stairs(self.dungeon_map, self.fov, self.explored, self.player,
                              stair_down_pos=self.stair_down_pos, stair_up_pos=self.stair_up_pos)
        self.ui.render_ui(self.player, self.state, self.combat_log, self.turn, self)

    def render_frame_text(self) -> str:
        """Render the current view and return it as plain text without presenting."""

        self._render_to_console()
        return self._console_text()

    def _uses_console_renderer(self) -> bool:
        return hasattr(self.renderer, "_root_console") and not hasattr(self.renderer, "_context")

    def _wait_for_events(self) -> List[Any]:
        """Return blocking input events for the active renderer backend."""
        if self._uses_console_renderer():
            return self._wait_for_console_input()
        return tcod.event.wait()

    def _console_key_to_event(self, key: str) -> Optional[tcod.event.KeyDown]:
        keymap = {
            "w": (tcod.event.Scancode.W, tcod.event.KeySym.W),
            "a": (tcod.event.Scancode.A, tcod.event.KeySym.A),
            "s": (tcod.event.Scancode.S, tcod.event.KeySym.S),
            "d": (tcod.event.Scancode.D, tcod.event.KeySym.D),
            "e": (tcod.event.Scancode.E, tcod.event.KeySym.E),
            "i": (tcod.event.Scancode.I, tcod.event.KeySym.I),
            "u": (tcod.event.Scancode.U, tcod.event.KeySym.U),
            "c": (tcod.event.Scancode.C, tcod.event.KeySym.C),
            "g": (tcod.event.Scancode.G, tcod.event.KeySym.G),
            ",": (tcod.event.Scancode.COMMA, tcod.event.KeySym.COMMA),
            ".": (tcod.event.Scancode.PERIOD, tcod.event.KeySym.PERIOD),
            ">": (tcod.event.Scancode.PERIOD, tcod.event.KeySym.GREATER),
            "<": (tcod.event.Scancode.COMMA, tcod.event.KeySym.LESS),
            " ": (tcod.event.Scancode.SPACE, tcod.event.KeySym.SPACE),
            "\r": (tcod.event.Scancode.RETURN, tcod.event.KeySym.RETURN),
            "\n": (tcod.event.Scancode.RETURN, tcod.event.KeySym.RETURN),
            # Standard arrow keys (CSI sequences)
            "\x1b[A": (tcod.event.Scancode.UP, tcod.event.KeySym.UP),
            "\x1b[B": (tcod.event.Scancode.DOWN, tcod.event.KeySym.DOWN),
            "\x1b[C": (tcod.event.Scancode.RIGHT, tcod.event.KeySym.RIGHT),
            "\x1b[D": (tcod.event.Scancode.LEFT, tcod.event.KeySym.LEFT),
            # Application mode arrow keys (SS3 sequences)
            "\x1bOA": (tcod.event.Scancode.UP, tcod.event.KeySym.UP),
            "\x1bOB": (tcod.event.Scancode.DOWN, tcod.event.KeySym.DOWN),
            "\x1bOC": (tcod.event.Scancode.RIGHT, tcod.event.KeySym.RIGHT),
            "\x1bOD": (tcod.event.Scancode.LEFT, tcod.event.KeySym.LEFT),
            # Additional variants
            "\x1b[1;5A": (tcod.event.Scancode.UP, tcod.event.KeySym.UP),   # Ctrl+Up
            "\x1b[1;5B": (tcod.event.Scancode.DOWN, tcod.event.KeySym.DOWN), # Ctrl+Down
            "\x1b[1;5C": (tcod.event.Scancode.RIGHT, tcod.event.KeySym.RIGHT), # Ctrl+Right
            "\x1b[1;5D": (tcod.event.Scancode.LEFT, tcod.event.KeySym.LEFT),  # Ctrl+Left
            "\x1b": (tcod.event.Scancode.ESCAPE, tcod.event.KeySym.ESCAPE),
        }
        if key not in keymap:
            # Debug: log unknown keys
            print(f"DEBUG: Unknown key sequence: {repr(key)}")
            return None
        scancode, sym = keymap[key]
        return tcod.event.KeyDown(scancode=scancode, sym=sym, mod=tcod.event.Modifier.NONE)

    def _read_console_key(self) -> str:
        if sys.stdin.isatty():
            import select
            import termios
            import tty
            import os

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                # Read first byte
                key = os.read(fd, 1).decode('utf-8', errors='ignore')
                if key == "\x1b":
                    # Read all available bytes immediately (non-blocking)
                    # Use a short timeout loop to catch the full escape sequence
                    import time
                    start_time = time.time()
                    while time.time() - start_time < 0.2:  # 200ms total timeout
                        ready, _, _ = select.select([fd], [], [], 0.01)
                        if ready:
                            more = os.read(fd, 1).decode('utf-8', errors='ignore')
                            if more:
                                key += more
                            else:
                                break
                        # If we have a complete escape sequence, break early
                        if key.endswith(('A', 'B', 'C', 'D', 'H', 'F', '~')) and len(key) >= 3:
                            break
                    # If we still only have \x1b, try one more blocking read
                    if key == "\x1b":
                        ready, _, _ = select.select([fd], [], [], 0.1)
                        if ready:
                            more = os.read(fd, 1).decode('utf-8', errors='ignore')
                            if more:
                                key += more
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return key

        key = sys.stdin.readline().rstrip("\r\n")
        if not key:
            return "\x04"
        return key

    def _wait_for_console_input(self) -> List[Any]:
        key = self._read_console_key()

        if key in ("\x03", "\x04"):
            return [tcod.event.Quit()]

        event = self._console_key_to_event(key)
        return [event] if event else []

    def _get_perception_for_entity(self, entity: Entity) -> Optional[PerceptionStatus]:
        """Build a PerceptionStatus for an entity based on its surroundings."""
        if self.dungeon_map is None or self.fov is None:
            return None
        
        # Check if entity is visible to player
        visible = bool(self.fov[entity.x, entity.y]) if entity.x < self.fov.shape[0] and entity.y < self.fov.shape[1] else False
        
        # Find player distance
        player_dist = max(abs(entity.x - self.player.x), abs(entity.y - self.player.y))
        
        # Find visible threats and allies
        visible_threats = []
        visible_allies = []
        visible_items = []
        
        for e in self.entities:
            if e is entity or not e.is_alive:
                continue
            dist = max(abs(entity.x - e.x), abs(entity.y - e.y))
            if dist <= 8:  # Perception range
                if e is self.player:
                    visible_threats.append(e.id)
                elif e.is_commander:
                    visible_allies.append(e.id)
        
        return PerceptionStatus(
            entity_id=entity.id,
            can_see_player=visible,
            can_hear_player=player_dist <= 12,
            player_distance_estimate=float(player_dist),
            visible_threats=visible_threats,
            visible_allies=visible_allies,
            visible_items=visible_items,
            environment_danger=0.0,
            light_level=1.0,
        )
    
    def _process_llm_responses(self):
        """Process LLM responses from the response queue."""
        while not self.llm_response_queue.empty():
            try:
                result = self.llm_response_queue.get_nowait()
                entity_id = result.get('entity_id')
                for entity in self.entities:
                    if getattr(entity, 'id', None) == entity_id:
                        if result.get('success') and result.get('behavior_script'):
                            entity.behavior_script = result['behavior_script']
                        break
            except Exception:
                break
    
    def _fallback_monster_ai(self, entity: Entity):
        """Fallback AI for monsters when no behavior script is available."""
        if not entity.is_alive:
            return
        
        dist = max(abs(entity.x - self.player.x), abs(entity.y - self.player.y))
        if dist <= 15:
            entity.move_towards(self.player.x, self.player.y, self.dungeon_map, self.entities)
            if max(abs(entity.x - self.player.x), abs(entity.y - self.player.y)) <= 1:
                self.attack(entity, self.player)

    def monster_turn(self, entity: Entity):
        if not entity.is_alive:
            return
        
        # Check for behavior script first
        if hasattr(entity, 'behavior_script') and entity.behavior_script:
            perception = self._get_perception_for_entity(entity)
            entity_state = {'health_pct': entity.hp / entity.max_hp if entity.max_hp > 0 else 1.0, 'in_combat': True}
            action = BehaviorScriptService().evaluate_script(entity.behavior_script, perception, entity_state)
            if action:
                self._execute_entity_action(entity, action)
                return
        
        # Fallback to default AI
        self._fallback_monster_ai(entity)
    
    def _execute_entity_action(self, entity: Entity, action):
        """Execute an action from a behavior script."""
        if not action:
            return
        
        action_type = action.action_type if hasattr(action, 'action_type') else str(action)
        
        if action_type == 'attack':
            self.attack(entity, self.player)
        elif action_type == 'flee':
            # Move away from player
            dx = entity.x - self.player.x
            dy = entity.y - self.player.y
            entity.move_to(entity.x + dx, entity.y + dy, self.dungeon_map, self.entities)
        elif action_type == 'patrol':
            # Simple patrol - move randomly
            entity.move_towards(self.player.x, self.player.y, self.dungeon_map, self.entities)
        elif action_type == 'wait':
            pass  # Do nothing
        elif action_type == 'search':
            # Move toward player's last known position
            if self.player:
                entity.move_towards(self.player.x, self.player.y, self.dungeon_map, self.entities)
        else:
            # Unknown action, use fallback
            self._fallback_monster_ai(entity)
    
    def attack(self, attacker: Entity, defender: Entity):
        event = CombatResolver.resolve_attack(attacker, defender)
        self.combat_log.add_event(event)
        self.combat_damage_log.record_event(event, attacker, defender)
        
        # Determine perspective for message routing
        if attacker is self.player:
            perspective = "attacker_is_player"
        elif defender is self.player:
            perspective = "defender_is_player"
        else:
            perspective = "neutral"
        
        # Route to categorized combat message system
        self.add_combat_message(event, attacker, defender, perspective)
        
        # Also add to general message_log for backward compatibility
        self.add_message(str(event))
        
        if event.result in (HitResult.HIT, HitResult.CRITICAL):
            defender.hp -= event.damage
            if defender.hp <= 0:
                defender.hp = 0
                self.on_kill(attacker, defender)
    
    def add_combat_message(self, event: CombatEvent, attacker: Entity, defender: Entity, perspective: str):
        """
        Route a combat event to the appropriate categorized message line.
        
        Args:
            event: The CombatEvent that occurred
            attacker: The attacking Entity
            defender: The defending Entity
            perspective: One of "attacker_is_player", "defender_is_player", "neutral"
        """
        # Initialize combat_message_log if it doesn't exist
        if not hasattr(self, "combat_message_log"):
            self.combat_message_log = {
                "player_actions": [],
                "against_player": [],
                "observable": [],
            }
        
        # Generate the perspective-aware message
        msg = event.__str__(perspective)
        
        if attacker is self.player:
            # Player is attacking — goes to "player_actions" line
            self.combat_message_log["player_actions"].append(msg)
        elif defender is self.player:
            # Player is being attacked — goes to "against_player" line
            self.combat_message_log["against_player"].append(msg)
        else:
            # Neither is player — only show if attacker is visible in FOV
            if self.fov is not None:
                if (0 <= attacker.x < self.fov.shape[0] and
                    0 <= attacker.y < self.fov.shape[1]):
                    if bool(self.fov[attacker.x, attacker.y]):
                        self.combat_message_log["observable"].append(msg)
        
        # Trim to max 20 entries per category
        for key in self.combat_message_log:
            if len(self.combat_message_log[key]) > 20:
                self.combat_message_log[key] = self.combat_message_log[key][-20:]
    
    def on_kill(self, killer: Entity, victim: Entity):
        self.add_message(f"{victim.name} is slain!")
        # Make the victim non-blocking so player can move into the space
        victim.blocks = False
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
            if entity is not self.player and hasattr(entity, 'item') and entity.item is not None and entity.x == self.player.x and entity.y == self.player.y:
                if self.player.inventory.add_item(entity.item):
                    self.add_message(f"Picked up {entity.item.name}.")
                    self.entities.remove(entity)
                    self.energy_system.remove_entity(entity)
                    return True
                else:
                    self.add_message("Inventory full!")
                    return False
        self.add_message("There is nothing here to pick up.")
        return False

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
        self.inventory_selection = 0
        while self.showing_inventory:
            self.render_inventory()
            for event in self._wait_for_events():
                if isinstance(event, tcod.event.KeyDown):
                    if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.I):
                        self.showing_inventory = False
                        break  # break out of event loop after closing inventory
                    elif event.sym == tcod.event.KeySym.UP:
                        if self.player and self.player.inventory:
                            item_count = len(self.player.inventory.items)
                            if item_count > 0:
                                self.inventory_selection = (self.inventory_selection - 1) % item_count
                    elif event.sym == tcod.event.KeySym.DOWN:
                        if self.player and self.player.inventory:
                            item_count = len(self.player.inventory.items)
                            if item_count > 0:
                                self.inventory_selection = (self.inventory_selection + 1) % item_count
                    elif event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER):
                        if self.player and self.player.inventory:
                            item = self.player.inventory.get_item(self.inventory_selection)
                            if item:
                                if item.equipped:
                                    self.player.inventory.unequip(item.id)
                                else:
                                    slots = self.player.inventory._get_valid_slots_for_item(item)
                                    if slots:
                                        self.player.inventory.equip(item.id, slots[0])

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
                        # Use/Equip selected item
                        if self.player and self.player.inventory:
                            item = self.player.inventory.get_item(self.inventory_selection)
                            if item:
                                if item.item_type in (ItemType.POTION, ItemType.SCROLL, ItemType.FOOD, ItemType.WAND):
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
                                elif item.item_type in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
                                    # Equip/unequip equipment
                                    if item.equipped:
                                        self.player.inventory.unequip(item.id)
                                        self.add_message(f"Unequipped {item.name}.")
                                    else:
                                        slots = self.player.inventory._get_valid_slots_for_item(item)
                                        if slots:
                                            self.player.inventory.equip(item.id, slots[0])
                                            self.add_message(f"Equipped {item.name}.")
                                        else:
                                            self.add_message(f"Cannot equip {item.name}.")
                                else:
                                    self.add_message(f"{item.name} is not usable.")
    
    def show_character(self):
        self.showing_character = True
        while self.showing_character:
            self.render_character()
            for event in self._wait_for_events():
                if isinstance(event, tcod.event.KeyDown):
                    if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.C):
                        self.showing_character = False
                    elif event.sym in (tcod.event.KeySym.UP, tcod.event.KeySym.DOWN,
                                        tcod.event.KeySym.LEFT, tcod.event.KeySym.RIGHT,
                                        tcod.event.KeySym.W, tcod.event.KeySym.S,
                                        tcod.event.KeySym.A, tcod.event.KeySym.D):
                        pass  # Arrow/WASD reserved for future character sheet navigation
    
    def show_menu(self):
        self.showing_menu = True
        self.menu_selection = 0
        menu_options = ["Resume", "Save & Quit", "Quit (No Save)"]
        
        while self.showing_menu:
            self.render_menu(menu_options)
            for event in self._wait_for_events():
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
        self.renderer.clear()
        self.ui.render_dungeon(self.dungeon_map, self.fov, self.explored, self.player)
        self.ui.render_entities(self.entities, self.fov, self.player)
        self.ui.render_ui(self.player, self.state, self.combat_log, self.turn, self)
        
        self.renderer.present()
    
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
    
    def _safe_int(self, value) -> int:
        """
        Safely convert a value to int, handling None, int, and string values.
        
        For strings, extracts the first numeric value found (e.g., '1d8 + 4 slashing' -> 1).
        Returns 0 for None, empty strings, or strings with no numbers.
        
        Args:
            value: Value to convert (None, int, or str)
            
        Returns:
            Integer value or 0 if conversion not possible
        """
        if value is None:
            return 0
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            if not value.strip():
                return 0
            # Extract first number from string (handles dice notation like '1d8 + 4 slashing')
            import re
            match = re.search(r'\d+', value)
            if match:
                return int(match.group())
            return 0
        # Fallback for other types
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    def _render_item_description(self, x: int, y: int, width: int, item) -> None:
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
        damage_bonus = self._safe_int(item.damage_bonus)
        to_hit_bonus = self._safe_int(item.to_hit_bonus)
        defense_bonus = self._safe_int(item.defense_bonus)
        
        if damage_bonus > 0 or to_hit_bonus > 0 or defense_bonus > 0:
            stat_parts = []
            if damage_bonus > 0:
                stat_parts.append(f"+{damage_bonus} DMG")
            if to_hit_bonus > 0:
                stat_parts.append(f"+{to_hit_bonus} HIT")
            if defense_bonus > 0:
                stat_parts.append(f"+{defense_bonus} DEF")
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
    
    def render_character(self):
        self.renderer.clear()
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
            f"  Power: {self.player.power}  Defense: {self.player.defense}  DV: {self.player.defense_value} AV: {self.player.armor_value}",
            f"  To-Hit: +{self.player.to_hit_bonus}  Damage: +{self.player.damage_bonus}",
            f"",
            f"Skills: {', '.join(self.player.known_skills) if self.player.known_skills else 'None'}",
            f"Skill Points: {self.player.skill_points}",
            f"",
            f"Gold: {self.player.gold}  Kills: {self.player.kill_count}",
            f"Nutrition: {self.player.nutrition}/{self.player.max_nutrition}",
        ]
        
        for i, line in enumerate(lines):
            self.renderer.print(2, 2 + i, line, COLORS['text'])
        
        # Present using the renderer
        self.renderer.present()
    
    def render_menu(self, options: List[str]):
        self.renderer.clear()
        self.renderer.print(self.screen_width // 2 - 10, self.screen_height // 2 - 3, "═ MENU ═", COLORS['gold'])
        for i, option in enumerate(options):
            color = COLORS['gold'] if i == self.menu_selection else COLORS['text']
            prefix = "> " if i == self.menu_selection else "  "
            self.renderer.print(self.screen_width // 2 - 10, self.screen_height // 2 - 1 + i, f"{prefix}{option}", color)
        
        # Only present if using graphical rendering
        self.renderer.present()
    
    def add_message(self, msg: str):
        self.message_log.append(msg)
        if len(self.message_log) > 100:
            self.message_log.pop(0)
        print(msg)
    
    def cleanup(self):
        # Export combat damage log
        if hasattr(self, 'combat_damage_log'):
            try:
                log_path = self.combat_damage_log.export_to_json(self.state.run_id)
                print(f"Combat damage log written to: {log_path}")
            except Exception as e:
                print(f"Warning: Could not export combat damage log: {e}")
        
        if self.ollama:
            self.ollama.stop()
        if self.context:
            self.context.__exit__(None, None, None)

    def _compute_difficulty_adjustment(self, level_record) -> float:
        """Compute difficulty adjustment based on level performance.
        
        Args:
            level_record: Dict with monsters_killed, total_monsters, damage_taken, close_calls
            
        Returns:
            1.3 for dominated (ratio > 0.9), 0.8 for struggled (ratio < 0.5),
            1.1 for managed (ratio >= 0.5, damage < 40), 1.0 for no data
        """
        if not level_record:
            return 1.0
        
        monsters_killed = level_record.get("monsters_killed", 0)
        total_monsters = level_record.get("total_monsters", 1)
        damage_taken = level_record.get("damage_taken", 0)
        
        if total_monsters == 0:
            return 1.0
        
        ratio = monsters_killed / total_monsters
        
        if ratio > 0.9:
            return 1.3  # Dominated - significantly harder
        elif ratio < 0.5:
            return 0.8  # Struggled - easier
        elif damage_taken < 40:
            return 1.1  # Managed - slightly harder
        return 1.0

    def _compute_performance_summary(self, level_record) -> str:
        """Compute performance summary string.
        
        Args:
            level_record: Dict with monsters_killed, total_monsters, damage_taken, close_calls, turns_taken
            
        Returns:
            Summary string like "dominated 8/8", "struggled 1/8", or "No previous level data."
        """
        if not level_record:
            return "No previous level data."
        
        monsters_killed = level_record.get("monsters_killed", 0)
        total_monsters = level_record.get("total_monsters", 1)
        damage_taken = level_record.get("damage_taken", 0)
        
        if total_monsters == 0:
            return "No previous level data."
        
        ratio = monsters_killed / total_monsters
        
        if ratio > 0.9:
            return f"Player dominated. {monsters_killed}/{total_monsters} monsters defeated."
        elif ratio < 0.5:
            return f"Player struggled. {monsters_killed}/{total_monsters} monsters defeated."
        return f"Player managed. {monsters_killed}/{total_monsters} monsters defeated."

    def _build_narrative_continuity(self, levels) -> str:
        """Build narrative continuity string from level history.
        
        Args:
            levels: List of level records
            
        Returns:
            Narrative string for the next level
        """
        if not levels:
            return "First level -- no previous narrative."
        
        # Get the last level
        last_level = levels[-1]
        theme_name = last_level.get("theme_name", "previous depths")
        depth = last_level.get("depth", 1)
        
        # Build history summary
        history = ", ".join(
            f"{rec.get('theme_name', 'Unknown')}" 
            for rec in levels[-3:]
        )
        
        # Determine direction based on depth
        if depth >= 5:
            direction = "face the deepest horrors"
        else:
            direction = "Escalate"
        
        return f"Previous levels: {history}. {direction}."

    def _build_dm_evolution_context(self, depth: int) -> Optional[Dict[str, Any]]:
        """Build context for DM evolution.
        
        Args:
            depth: Target level depth
            
        Returns:
            Dict with evolution context or None if no levels
        """
        if not hasattr(self, 'dm_context') or not self.dm_context.get("levels"):
            return None
        
        levels = self.dm_context.get("levels", [])
        
        # Get the last level record for difficulty adjustment
        last_level = levels[-1] if levels else {}
        
        return {
            "previous_levels": levels[-3:],  # Last 3 levels
            "performance_summary": self._compute_performance_summary(last_level),
            "difficulty_adjustment": self._compute_difficulty_adjustment(last_level),
            "narrative_continuity": self._build_narrative_continuity(levels),
            "target_depth": depth,
        }

    def _record_level_performance(self) -> None:
        """Record level performance to dm_context."""
        if not hasattr(self, 'dm_context') or self.dm_context is None:
            return
        
        record = {
            "depth": self.state.depth,
            "theme_name": self.current_theme.name if hasattr(self, 'current_theme') and self.current_theme else "Unknown",
            "monster_theme": self.current_theme.monster_theme if hasattr(self, 'current_theme') and self.current_theme else "unknown",
            "monsters_killed": self.dm_context.get("current_level_kills", 0),
            "total_monsters": self.dm_context.get("total_level_monsters", 0),
            "turns_taken": self.turn - self.dm_context.get("current_level_start_turn", self.turn),
            "damage_taken": self.dm_context.get("current_level_damage_taken", 0),
            "close_calls": self.dm_context.get("current_level_close_calls", 0),
            "difficulty_rating": self.current_theme.difficulty if hasattr(self, 'current_theme') and self.current_theme else 3.0,
        }
        
        self.dm_context["levels"].append(record)
        # Keep only last 10
        self.dm_context["levels"] = self.dm_context["levels"][-10:]
        
        # Reset counters for next level
        self.dm_context["current_level_kills"] = 0
        self.dm_context["current_level_damage_taken"] = 0
        self.dm_context["current_level_close_calls"] = 0
        self.dm_context["current_level_start_turn"] = self.turn

# =============================================================================
# INSTRUCTION PROMPT HELPER
# =============================================================================

INSTRUCTION_PATH = Path(__file__).parent / "playtest" / "instructions.json"


def load_instruction_prompt(target: str) -> str:
    """Load and format playtest instructions for the specified target."""
    from playtest.instruction_bus import InstructionBus

    bus = InstructionBus(path=INSTRUCTION_PATH)
    return bus.get_prompt_text(target)


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="DarkDelve - A Traditional Roguelike")
    parser.add_argument("--playtest", action="store_true", help="Run in AI playtest mode")
    parser.add_argument("--turns", type=int, default=500, help="Max turns for playtest mode")
    args = parser.parse_args()

    # Set random seed if provided
    if CONFIG['game']['seed'] is not None:
        random.seed(CONFIG['game']['seed'])
        np.random.seed(CONFIG['game']['seed'])

    playtest_config = CONFIG.get('playtest', {})
    playtest_enabled = args.playtest or playtest_config.get('enabled', False)
    
    if playtest_enabled:
        from src.infrastructure.services.mcp_integration import MCPPlaytester
        from ollama_playtester import PlaytestConfig
        game = Game()
        game.initialize()
        config = PlaytestConfig(max_turns=args.turns)
        playtester = MCPPlaytester(
            game=game,
            config=config,
            config_path=playtest_config.get('config_path'),
            auto_initialize=False,
        )
        result = playtester.run()
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0 if result.status in {'exit', 'max_turns'} else 1

    game = Game()
    game.run()

if __name__ == "__main__":
    main()
