# DarkDelve Module Design

## Module Structure

```
src/
├── __init__.py
├── main.py                 # Entry point
├── config/
│   ├── __init__.py
│   └── config.py          # Configuration management
├── core/
│   ├── __init__.py
│   ├── game.py            # Main game controller
│   ├── game_state.py      # Game state data structures
│   └── game_loop.py       # Game loop management
├── systems/
│   ├── __init__.py
│   ├── dungeon.py         # Dungeon generation
│   ├── fov.py             # Field of view calculations
│   ├── combat.py          # Combat mechanics
│   ├── energy.py          # Action point system
│   ├── survival.py        # Survival mechanics
│   └── identification.py  # Item identification
├── content/
│   ├── __init__.py
│   ├── ollama.py          # Ollama management
│   ├── generator.py       # Content generation
│   ├── cache.py           # Content caching
│   └── mobs.py            # Monster generation
├── data/
│   ├── __init__.py
│   ├── entity.py          # Entity system
│   ├── item.py            # Item system
│   ├── inventory.py       # Inventory management
│   └── events.py          # Event system
├── ui/
│   ├── __init__.py
│   ├── ui.py              # Main UI class
│   ├── renderer.py        # Rendering system
│   └── input.py           # Input handling
├── persistence/
│   ├── __init__.py
│   ├── save.py            # Save system
│   └── highscores.py      # High scores
└── utils/
    ├── __init__.py
    ├── math.py            # Mathematical utilities
    └── logger.py          # Logging system
```

## Detailed Module Specifications

### 1. Core Module

#### `core/game.py`
```python
class Game:
    """Main game controller"""
    
    def __init__(self, config: dict):
        self.config = config
        self.state = GameState()
        self.systems = {}
        self.content_gen = None
        self.ui = None
        self.input_handler = None
        
    def initialize(self):
        """Initialize all game systems"""
        
    def run(self):
        """Main game loop"""
        
    def shutdown(self):
        """Clean shutdown"""
```

#### `core/game_state.py`
```python
@dataclass
class GameState:
    """Central game state data structure"""
    
    run_id: str
    player: Entity
    current_level: int
    dungeon: np.ndarray
    entities: List[Entity]
    inventory: Inventory
    combat_log: CombatLog
    turn: int
    energy: int
    
    def save_state(self) -> dict:
        """Serialize game state"""
        
    def load_state(self, data: dict):
        """Deserialize game state"""
```

#### `core/game_loop.py`
```python
class GameLoop:
    """Game loop and timing management"""
    
    def __init__(self, config: dict):
        self.config = config
        self.last_tick = 0
        self.accumulator = 0
        
    def update(self, delta_time: float):
        """Update game state"""
        
    def should_render(self) -> bool:
        """Check if render is needed"""
```

### 2. Systems Module

#### `systems/dungeon.py`
```python
class DungeonGenerator:
    """Procedural dungeon generation"""
    
    def __init__(self, config: dict):
        self.config = config
        self.themes = {}
        
    def generate_level(self, width: int, height: int, level: int) -> np.ndarray:
        """Generate a new dungeon level"""
        
    def apply_theme(self, dungeon: np.ndarray, theme: LevelTheme) -> np.ndarray:
        """Apply visual theme to dungeon"""
```

#### `systems/fov.py`
```python
class FOVSystem:
    """Field of view calculations"""
    
    def __init__(self, radius: int = 8):
        self.radius = radius
        
    def calculate_fov(self, dungeon: np.ndarray, x: int, y: int) -> np.ndarray:
        """Calculate field of view using raycasting"""
        
    def is_visible(self, x: int, y: int) -> bool:
        """Check if position is visible"""
```

#### `systems/combat.py`
```python
class CombatResolver:
    """Combat mechanics and resolution"""
    
    @staticmethod
    def resolve_attack(attacker: Entity, defender: Entity) -> CombatEvent:
        """Resolve combat between entities"""
        
    @staticmethod
    def calculate_damage(attacker: Entity, defender: Entity) -> int:
        """Calculate damage dealt"""
        
    @staticmethod
    def apply_damage(entity: Entity, damage: int) -> CombatEvent:
        """Apply damage to entity"""
```

#### `systems/energy.py`
```python
class EnergySystem:
    """Action point system"""
    
    def __init__(self, config: dict):
        self.config = config
        self.max_energy = 100
        self.energy_per_turn = 10
        
    def spend_energy(self, amount: int) -> bool:
        """Spend energy points"""
        
    def regenerate_energy(self):
        """Regenerate energy each turn"""
```

#### `systems/survival.py`
```python
class SurvivalSystem:
    """Survival mechanics (hunger, health, etc.)"""
    
    def __init__(self, config: dict):
        self.config = config
        
    def update_survival(self, player: Entity, turn: int):
        """Update survival mechanics"""
        
    def apply_hunger(self, player: Entity):
        """Apply hunger effects"""
```

#### `systems/identification.py`
```python
class IdentificationSystem:
    """Item identification mechanics"""
    
    def __init__(self):
        self.identification_chance = 0.1
        
    def identify_item(self, item: Item) -> bool:
        """Attempt to identify an item"""
        
    def get_identification_status(self, item: Item) -> str:
        """Get current identification status"""
```

### 3. Content Module

#### `content/ollama.py`
```python
class EmbeddedOllama:
    """Manages local Ollama instance"""
    
    def __init__(self, model: str = "qwen2.5-coder:7b-instruct"):
        self.model = model
        self.process = None
        self.base_url = "http://127.0.0.1:11434"
        
    def start(self) -> bool:
        """Start Ollama instance"""
        
    def stop(self):
        """Stop Ollama instance"""
        
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate content using LLM"""
```

#### `content/generator.py`
```python
class ContentGenerator:
    """LLM-based content generation"""
    
    def __init__(self, ollama: EmbeddedOllama, cache: ContentCache, config: dict):
        self.ollama = ollama
        self.cache = cache
        self.config = config
        
    def generate_mob_name(self, tier: MobTier) -> str:
        """Generate monster name"""
        
    def generate_item_description(self, item: Item) -> str:
        """Generate item description"""
        
    def generate_level_theme(self, level: int) -> LevelTheme:
        """Generate level theme"""
```

#### `content/cache.py`
```python
class ContentCache:
    """SQLite-based content caching"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        
    def get_cached_content(self, prompt_hash: str) -> Optional[str]:
        """Get cached content"""
        
    def cache_content(self, prompt_hash: str, content: str):
        """Cache content"""
        
    def clear_cache(self):
        """Clear all cached content"""
```

#### `content/mobs.py`
```python
class MobRoster:
    """Monster templates and generation"""
    
    def __init__(self, config: dict):
        self.config = config
        self.templates = {}
        
    def load_templates(self):
        """Load monster templates"""
        
    def generate_mob(self, tier: MobTier, level: int) -> MobTemplate:
        """Generate monster based on tier and level"""
```

### 4. Data Module

#### `data/entity.py`
```python
@dataclass
class Entity:
    """Game entity (player, monsters, items)"""
    
    x: int
    y: int
    name: str
    glyph: str
    color: Tuple[int, int, int]
    blocks: bool = False
    fighter: Optional[Fighter] = None
    ai: Optional[AI] = None
    
    def move(self, dx: int, dy: int, dungeon: np.ndarray) -> bool:
        """Move entity"""
        
    def take_damage(self, damage: int) -> CombatEvent:
        """Apply damage to entity"""
```

#### `data/item.py`
```python
@dataclass
class Item:
    """Game item"""
    
    id: str
    name: str
    description: str
    glyph: str
    color: Tuple[int, int, int]
    item_type: ItemType
    equipment_slot: Optional[EquipmentSlot] = None
    identified: bool = False
    effects: Dict[str, Any] = field(default_factory=dict)
```

#### `data/inventory.py`
```python
@dataclass
class Inventory:
    """Player inventory management"""
    
    items: List[Item] = field(default_factory=list)
    capacity: int = 26
    
    def add_item(self, item: Item) -> bool:
        """Add item to inventory"""
        
    def remove_item(self, item: Item) -> bool:
        """Remove item from inventory"""
        
    def get_item(self, index: int) -> Optional[Item]:
        """Get item by index"""
```

#### `data/events.py`
```python
@dataclass
class CombatEvent:
    """Combat event data"""
    
    turn: int
    attacker: str
    defender: str
    damage: int
    message: str
    
@dataclass
class CombatLog:
    """Combat event log"""
    
    events: List[CombatEvent] = field(default_factory=list)
    
    def add_event(self, event: CombatEvent):
        """Add combat event"""
        
    def get_recent(self, count: int) -> List[CombatEvent]:
        """Get recent events"""
```

### 5. UI Module

#### `ui/ui.py`
```python
class UI:
    """Main UI management"""
    
    def __init__(self, console: tcod.Console, config: dict):
        self.console = console
        self.config = config
        self.renderer = None
        self.input_handler = None
        
    def render_game(self, game_state: GameState):
        """Render complete game state"""
        
    def handle_input(self) -> InputAction:
        """Handle user input"""
```

#### `ui/renderer.py`
```python
class Renderer:
    """Game rendering system"""
    
    def __init__(self, console: tcod.Console, config: dict):
        self.console = console
        self.config = config
        
    def render_dungeon(self, dungeon: np.ndarray, fov: np.ndarray):
        """Render dungeon map"""
        
    def render_entities(self, entities: List[Entity], fov: np.ndarray):
        """Render entities"""
        
    def render_ui(self, player: Entity, game_state: GameState):
        """Render UI elements"""
```

#### `ui/input.py`
```python
class InputHandler:
    """Input handling system"""
    
    def __init__(self, config: dict):
        self.config = config
        self.keymap = {}
        
    def handle_input(self) -> InputAction:
        """Process input and return action"""
        
    def is_key_pressed(self, key: tcod.Key) -> bool:
        """Check if key is pressed"""
```

### 6. Persistence Module

#### `persistence/save.py`
```python
class SaveSystem:
    """Game state persistence"""
    
    def __init__(self, save_path: Path):
        self.save_path = save_path
        
    def save_game(self, game_state: GameState) -> bool:
        """Save game state"""
        
    def load_game(self, save_file: str) -> Optional[GameState]:
        """Load game state"""
        
    def list_saves(self) -> List[str]:
        """List available saves"""
```

#### `persistence/highscores.py`
```python
class HighScores:
    """High score management"""
    
    def __init__(self, score_path: Path):
        self.score_path = score_path
        
    def add_score(self, player_name: str, score: int, level: int):
        """Add high score"""
        
    def get_top_scores(self, limit: int = 10) -> List[dict]:
        """Get top scores"""
        
    def save_scores(self):
        """Save scores to file"""
```

### 7. Utils Module

#### `utils/math.py`
```python
def clamp(value: int, min_val: int, max_val: int) -> int:
    """Clamp value between min and max"""
    
def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """Manhattan distance heuristic"""
    
def random_chance(probability: float) -> bool:
    """Check random chance"""
```

#### `utils/logger.py`
```python
import logging

class GameLogger:
    """Game logging system"""
    
    def __init__(self, log_path: Path):
        self.setup_logging(log_path)
        
    def setup_logging(self, log_path: Path):
        """Setup logging configuration"""
        
    def log_game_event(self, event: str, **kwargs):
        """Log game event"""
```

## Module Dependencies

```
main.py
├── config/config.py
├── core/
│   ├── game.py
│   ├── game_state.py
│   └── game_loop.py
├── systems/
│   ├── dungeon.py
│   ├── fov.py
│   ├── combat.py
│   ├── energy.py
│   ├── survival.py
│   └── identification.py
├── content/
│   ├── ollama.py
│   ├── generator.py
│   ├── cache.py
│   └── mobs.py
├── data/
│   ├── entity.py
│   ├── item.py
│   ├── inventory.py
│   └── events.py
├── ui/
│   ├── ui.py
│   ├── renderer.py
│   └── input.py
├── persistence/
│   ├── save.py
│   └── highscores.py
└── utils/
    ├── math.py
    └── logger.py
```

## Integration Points

1. **Game System**: Core game controller that manages all systems
2. **Content Integration**: Content generator provides dynamic content to game systems
3. **UI Integration**: UI renders game state and handles input
4. **Persistence Integration**: Save system persists game state
5. **Configuration Integration**: All modules use shared configuration