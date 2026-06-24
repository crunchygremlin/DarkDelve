# DarkDelve SOLID Architecture Design

## Overview

This document presents a modular architecture for DarkDelve that adheres to SOLID design principles. The architecture breaks down the monolithic codebase into focused, maintainable modules that are easy to understand, test, and extend - particularly suitable for development with local LLM models like Qwen 7b Coder.

## SOLID Principles Applied

### Single Responsibility Principle (SRP)
Each module has one reason to change and handles a single aspect of the system.

### Open/Closed Principle (OCP)
Modules are open for extension but closed for modification through interfaces and abstractions.

### Liskov Substitution Principle (LSP)
Subtypes are substitutable for their base types through proper interface design.

### Interface Segregation Principle (ISP)
Clients should not depend on interfaces they don't use - small, focused interfaces.

### Dependency Inversion Principle (DIP)
High-level modules depend on abstractions, not low-level modules.

## Modular Architecture

```
src/
├── __init__.py
├── main.py                    # Application entry point
├── domain/                    # Domain layer (core business logic)
│   ├── __init__.py
│   ├── entities/             # Entity definitions
│   │   ├── __init__.py
│   │   ├── entity.py         # Base entity
│   │   ├── player.py         # Player entity
│   │   ├── mob.py            # Monster entities
│   │   └── item.py           # Item entities
│   ├── components/           # Component system
│   │   ├── __init__.py
│   │   ├── component.py      # Base component
│   │   ├── combat.py         # Combat component
│   │   ├── movement.py       # Movement component
│   │   ├── inventory.py      # Inventory component
│   │   └── ai.py             # AI component
│   ├── value_objects/        # Value objects
│   │   ├── __init__.py
│   │   ├── position.py       # Position value object
│   │   ├── stats.py          # Stats value object
│   │   └── combat_event.py   # Combat event value object
│   └── services/              # Domain services
│       ├── __init__.py
│       ├── combat_service.py  # Combat domain logic
│       ├── movement_service.py # Movement domain logic
│       └── inventory_service.py # Inventory domain logic
├── application/               # Application layer (use cases)
│   ├── __init__.py
│   ├── game_commands/         # Game commands
│   │   ├── __init__.py
│   │   ├── move_command.py   # Move command
│   │   ├── attack_command.py  # Attack command
│   │   ├── pickup_command.py # Pickup command
│   │   └── use_command.py    # Use command
│   ├── game_queries/         # Game queries
│   │   ├── __init__.py
│   │   ├── fov_query.py      # FOV query
│   │   ├── combat_query.py   # Combat query
│   │   └── inventory_query.py # Inventory query
│   ├── game_session.py       # Game session management
│   └── event_system.py      # Event system
├── infrastructure/           # Infrastructure layer (external concerns)
│   ├── __init__.py
│   ├── repositories/         # Data repositories
│   │   ├── __init__.py
│   │   ├── entity_repository.py # Entity repository
│   │   ├── item_repository.py   # Item repository
│   │   └── game_repository.py   # Game state repository
│   ├── external/             # External services
│   │   ├── __init__.py
│   │   ├── ollama_service.py  # Ollama service
│   │   ├── tcod_service.py     # TCOD rendering service
│   │   └── cache_service.py   # Cache service
│   ├── persistence/          # Persistence
│   │   ├── __init__.py
│   │   ├── save_system.py     # Save system
│   │   └── highscore_system.py # High score system
│   └── configuration/        # Configuration
│       ├── __init__.py
│       ├── config_loader.py   # Configuration loader
│       └── settings.py       # Settings management
├── presentation/             # Presentation layer (UI)
│   ├── __init__.py
│   ├── views/                # UI views
│   │   ├── __init__.py
│   │   ├── game_view.py      # Main game view
│   │   ├── inventory_view.py  # Inventory view
│   │   └── log_view.py       # Event log view
│   ├── controllers/          # UI controllers
│   │   ├── __init__.py
│   │   ├── input_controller.py # Input controller
│   │   └── ui_controller.py  # UI controller
│   └── renderers/           # Renderers
│       ├── __init__.py
│       ├── tile_renderer.py  # Tile-based renderer
│       ├── entity_renderer.py # Entity renderer
│       └── ui_renderer.py    # UI element renderer
└── shared/                   # Shared utilities
    ├── __init__.py
    ├── interfaces/           # Shared interfaces
    │   ├── __init__.py
    │   ├── repository.py     # Repository interface
    │   ├── service.py        # Service interface
    │   └── renderer.py       # Renderer interface
    ├── exceptions/           # Custom exceptions
    │   ├── __init__.py
    │   ├── domain_exceptions.py
    │   ├── application_exceptions.py
    │   └── infrastructure_exceptions.py
    ├── utils/                # Utilities
    │   ├── __init__.py
    │   ├── math_utils.py     # Mathematical utilities
    │   ├── file_utils.py      # File utilities
    │   └── logging_utils.py   # Logging utilities
    └── events/              # Event system
        ├── __init__.py
        ├── event.py          # Base event
        ├── event_handler.py  # Event handler
        └── event_bus.py      # Event bus
```

## Detailed Module Architecture

### 1. Domain Layer

#### Entities
```python
# domain/entities/entity.py
from abc import ABC, abstractmethod
from typing import Optional, List
from ..shared.interfaces.service import ServiceInterface

class Entity(ABC):
    """Base entity class"""
    
    def __init__(self, entity_id: str, name: str):
        self.id = entity_id
        self.name = name
        self.components = {}
        
    def add_component(self, component_type: type, component):
        """Add a component to the entity"""
        self.components[component_type] = component
        
    def get_component(self, component_type: type):
        """Get a component from the entity"""
        return self.components.get(component_type)
        
    def remove_component(self, component_type: type):
        """Remove a component from the entity"""
        if component_type in self.components:
            del self.components[component_type]
```

#### Components
```python
# domain/components/combat.py
from typing import Optional, List
from ..shared.interfaces.service import ServiceInterface
from ..value_objects.combat_event import CombatEvent

class CombatComponent:
    """Combat behavior component"""
    
    def __init__(self, attack_power: int, defense: int, max_hp: int):
        self.attack_power = attack_power
        self.defense = defense
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.attack_cooldown = 0
        
    def take_damage(self, damage: int) -> CombatEvent:
        """Apply damage to entity"""
        self.current_hp = max(0, self.current_hp - damage)
        return CombatEvent(
            attacker_id="",
            defender_id="",
            damage=damage,
            message=f"Deals {damage} damage"
        )
        
    def can_attack(self) -> bool:
        """Check if entity can attack"""
        return self.attack_cooldown <= 0
```

#### Value Objects
```python
# domain/value_objects/position.py
from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class Position:
    """Immutable position value object"""
    
    x: int
    y: int
    
    def __add__(self, other: 'Position') -> 'Position':
        """Add two positions"""
        return Position(self.x + other.x, self.y + other.y)
        
    def distance_to(self, other: 'Position') -> int:
        """Calculate distance to another position"""
        return abs(self.x - other.x) + abs(self.y - other.y)
```

#### Domain Services
```python
# domain/services/combat_service.py
from typing import List, Optional
from ..entities.entity import Entity
from ..components.combat import CombatComponent
from ..value_objects.combat_event import CombatEvent

class CombatService:
    """Domain service for combat logic"""
    
    def resolve_combat(self, attacker: Entity, defender: Entity) -> List[CombatEvent]:
        """Resolve combat between two entities"""
        events = []
        
        attacker_combat = attacker.get_component(CombatComponent)
        defender_combat = defender.get_component(CombatComponent)
        
        if not attacker_combat or not defender_combat:
            return events
            
        if not attacker_combat.can_attack():
            return events
            
        # Calculate damage
        damage = max(1, attacker_combat.attack_power - defender_combat.defense)
        
        # Apply damage
        event = defender_combat.take_damage(damage)
        event.attacker_id = attacker.id
        event.defender_id = defender.id
        events.append(event)
        
        # Set attack cooldown
        attacker_combat.attack_cooldown = 2
        
        return events
```

### 2. Application Layer

#### Commands
```python
# application/game_commands/move_command.py
from typing import Optional
from ..domain.entities.entity import Entity
from ..domain.value_objects.position import Position
from ..shared.events.event import Event

class MoveCommand:
    """Command for moving entities"""
    
    def __init__(self, entity_id: str, target_position: Position):
        self.entity_id = entity_id
        self.target_position = target_position
        
    def execute(self, game_session) -> Optional[Event]:
        """Execute the move command"""
        entity = game_session.get_entity(self.entity_id)
        if not entity:
            return None
            
        # Check if move is valid
        if game_session.is_valid_move(entity, self.target_position):
            entity.position = self.target_position
            return MoveEvent(entity.id, self.target_position)
            
        return None
```

#### Queries
```python
# application/game_queries/fov_query.py
from typing import List, Set
from ..domain.entities.entity import Entity
from ..domain.value_objects.position import Position

class FOVQuery:
    """Query for field of view calculations"""
    
    def __init__(self, observer_position: Position, radius: int):
        self.observer_position = observer_position
        self.radius = radius
        
    def execute(self, entities: List[Entity]) -> Set[str]:
        """Execute FOV query"""
        visible_entities = set()
        
        for entity in entities:
            if self.observer_position.distance_to(entity.position) <= self.radius:
                visible_entities.add(entity.id)
                
        return visible_entities
```

#### Event System
```python
# application/event_system.py
from typing import Dict, List, Callable
from ..shared.events.event import Event
from ..shared.events.event_handler import EventHandler

class EventSystem:
    """Application event system"""
    
    def __init__(self):
        self.handlers: Dict[type, List[EventHandler]] = {}
        
    def register_handler(self, event_type: type, handler: EventHandler):
        """Register an event handler"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        
    def emit(self, event: Event):
        """Emit an event"""
        event_type = type(event)
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                handler.handle(event)
```

### 3. Infrastructure Layer

#### Repositories
```python
# infrastructure/repositories/entity_repository.py
from typing import List, Optional
from ..shared.interfaces.repository import RepositoryInterface
from ...domain.entities.entity import Entity

class EntityRepository(RepositoryInterface[Entity]):
    """Repository for entity persistence"""
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        
    def save(self, entity: Entity) -> None:
        """Save an entity"""
        self.entities[entity.id] = entity
        
    def find_by_id(self, entity_id: str) -> Optional[Entity]:
        """Find entity by ID"""
        return self.entities.get(entity_id)
        
    def find_all(self) -> List[Entity]:
        """Find all entities"""
        return list(self.entities.values())
        
    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID"""
        if entity_id in self.entities:
            del self.entities[entity_id]
            return True
        return False
```

#### External Services
```python
# infrastructure/external/ollama_service.py
from typing import Optional, Dict, Any
import requests
from ...domain.services.content_service import ContentService

class OllamaService(ContentService):
    """Service for Ollama integration"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:11434"):
        self.base_url = base_url
        
    def generate_content(self, prompt: str, model: str = "qwen2.5-coder:7b-instruct") -> Optional[str]:
        """Generate content using Ollama"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.RequestException:
            return None
```

#### Persistence
```python
# infrastructure/persistence/save_system.py
from typing import Optional
import json
from pathlib import Path
from ...domain.services.game_state_service import GameStateService

class SaveSystem(GameStateService):
    """System for game state persistence"""
    
    def __init__(self, save_path: Path):
        self.save_path = save_path
        
    def save_game(self, game_state: dict) -> bool:
        """Save game state to file"""
        try:
            with open(self.save_path / "save.json", "w") as f:
                json.dump(game_state, f, indent=2)
            return True
        except (IOError, json.JSONEncodeError):
            return False
            
    def load_game(self) -> Optional[dict]:
        """Load game state from file"""
        try:
            with open(self.save_path / "save.json", "r") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return None
```

### 4. Presentation Layer

#### Views
```python
# presentation/views/game_view.py
from typing import List
from ..controllers.input_controller import InputController
from ...domain.entities.entity import Entity

class GameView:
    """Main game view"""
    
    def __init__(self, input_controller: InputController):
        self.input_controller = input_controller
        
    def render(self, entities: List[Entity], game_map: List[List[str]]):
        """Render the game view"""
        # Render game map
        for y, row in enumerate(game_map):
            for x, tile in enumerate(row):
                self._render_tile(x, y, tile)
                
        # Render entities
        for entity in entities:
            self._render_entity(entity)
            
    def handle_input(self):
        """Handle user input"""
        return self.input_controller.get_input()
```

#### Controllers
```python
# presentation/controllers/input_controller.py
from typing import Optional
import tcod

class InputController:
    """Controller for user input"""
    
    def __init__(self):
        self.keymap = {
            tcod.Key.K_w: "move_up",
            tcod.Key.K_s: "move_down",
            tcod.Key.K_a: "move_left",
            tcod.Key.K_d: "move_right",
            tcod.Key.K_i: "inventory",
            tcod.Key.K_ESCAPE: "quit"
        }
        
    def get_input(self) -> Optional[str]:
        """Get user input"""
        key = tcod.console.wait_for_keypress(flush=True)
        return self.keymap.get(key.vk)
```

#### Renderers
```python
# presentation/renderers/tile_renderer.py
from typing import List, Tuple
import tcod

class TileRenderer:
    """Renderer for game tiles"""
    
    def __init__(self, console: tcod.Console):
        self.console = console
        self.tile_colors = {
            '.': (50, 50, 50),  # Floor
            '#': (100, 100, 100),  # Wall
            ' ': (0, 0, 0)   # Empty
        }
        
    def render_map(self, game_map: List[List[str]]):
        """Render the game map"""
        for y, row in enumerate(game_map):
            for x, tile in enumerate(row):
                color = self.tile_colors.get(tile, (0, 0, 0))
                self.console.print(x, y, tile, color)
```

### 5. Shared Layer

#### Interfaces
```python
# shared/interfaces/repository.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')

class RepositoryInterface(ABC, Generic[T]):
    """Interface for repositories"""
    
    @abstractmethod
    def save(self, entity: T) -> None:
        """Save an entity"""
        pass
        
    @abstractmethod
    def find_by_id(self, entity_id: str) -> Optional[T]:
        """Find entity by ID"""
        pass
        
    @abstractmethod
    def find_all(self) -> List[T]:
        """Find all entities"""
        pass
        
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID"""
        pass
```

#### Event System
```python
# shared/events/event.py
from dataclasses import dataclass
from typing import Any

@dataclass
class Event:
    """Base event class"""
    
    timestamp: float
    event_type: str
    data: Any = None
    
    def __post_init__(self):
        if self.timestamp == 0:
            import time
            self.timestamp = time.time()
```

## SOLID Design Benefits

### Single Responsibility Principle
- Each module has a single, well-defined responsibility
- Entities focus on data and basic behavior
- Components handle specific behaviors
- Services manage business logic
- Repositories handle data persistence

### Open/Closed Principle
- New features can be added without modifying existing code
- Components can be extended with new behaviors
- Services can be replaced with implementations
- Commands can be added without changing command system

### Liskov Substitution Principle
- All entity implementations can be substituted for the base entity
- Repository implementations can be substituted for the repository interface
- Service implementations can be substituted for the service interface

### Interface Segregation Principle
- Small, focused interfaces prevent unnecessary dependencies
- Clients depend only on the interfaces they need
- Clear separation of concerns between layers

### Dependency Inversion Principle
- High-level modules depend on abstractions, not concrete implementations
- Domain layer has no dependencies on infrastructure layer
- Application layer depends on domain abstractions
- Presentation layer depends on application abstractions

## Integration Patterns

### Dependency Injection
```python
# Main application setup
class Application:
    def __init__(self):
        # Infrastructure
        self.entity_repository = EntityRepository()
        self.ollama_service = OllamaService()
        
        # Domain
        self.combat_service = CombatService()
        
        # Application
        self.event_system = EventSystem()
        self.game_session = GameSession(
            entity_repository=self.entity_repository,
            combat_service=self.combat_service,
            event_system=self.event_system
        )
        
        # Presentation
        self.input_controller = InputController()
        self.game_view = GameView(self.input_controller)
```

### Event-Driven Architecture
```python
# Event-driven communication
class GameSession:
    def __init__(self, event_system: EventSystem):
        self.event_system = event_system
        
    def handle_combat(self, attacker: Entity, defender: Entity):
        # Use domain service
        events = self.combat_service.resolve_combat(attacker, defender)
        
        # Emit events
        for event in events:
            self.event_system.emit(event)
```

## Testing Strategy

### Unit Testing
- Each module can be tested independently
- Mock external dependencies for isolated testing
- Test domain logic without infrastructure concerns

### Integration Testing
- Test interactions between modules
- Verify dependency injection works correctly
- Test event-driven communication

### System Testing
- Test complete game functionality
- Test with real external dependencies when available
- Performance testing with LLM integration

## Migration Strategy

### Phase 1: Infrastructure Layer
1. Extract configuration management
2. Create repository interfaces
3. Implement external service abstractions

### Phase 2: Domain Layer
1. Extract entity definitions
2. Create component system
3. Implement domain services

### Phase 3: Application Layer
1. Create command/query system
2. Implement event system
3. Build application services

### Phase 4: Presentation Layer
1. Extract UI components
2. Implement controllers and renderers
3. Create view system

### Phase 5: Integration
1. Wire all layers together
2. Test complete functionality
3. Refactor and optimize

This SOLID architecture provides a maintainable, extensible foundation for DarkDelve that can be easily understood and implemented by an LLM assistant while maintaining clean separation of concerns and testability.

## Recent Architecture Improvements (2026)

### Dependency Inversion Principle (DIP) Enhancements

The following improvements have been made to strengthen the Dependency Inversion Principle:

1. **Service Interfaces** (`src/shared/interfaces/service.py`)
   - `ICombatService`: Interface for combat operations
   - `IMovementService`: Interface for movement operations
   - `ISocialService`: Interface for social operations
   - These interfaces allow domain services to depend on abstractions rather than concrete implementations

2. **Concrete Service Implementations**
   - `CombatService` now implements `ICombatService`
   - `MovementService` now implements `IMovementService`
   - `SocialService` now implements `ISocialService`

3. **ActionDispatcher Refactoring**
   - Now depends on service interfaces (`ICombatService`, `IMovementService`, `ISocialService`)
   - Uses dependency injection for all service dependencies
   - Flee logic extracted to dedicated `FleeStrategy` service

### Event System Standardization

1. **EventType Enum** (`src/shared/events/event.py`)
   - Standardized event type constants: `HIT`, `MISS`, `CRITICAL_HIT`, `ENTITY_FLED`, `ALLY_CALLED`, `ITEM_PICKED_UP`, etc.
   - Type-safe event publishing through `EventBus.publish_event_by_type()`

2. **EventBus Enhancement**
   - Added `publish_event_by_type()` method for convenient string-based event publishing
   - Maintains backward compatibility with existing event system

### New Services

1. **FleeStrategy** (`src/domain/services/flee_strategy.py`)
   - Encapsulates flee behavior logic
   - Separates concerns from `ActionDispatcher`
   - Improves testability and maintainability

### Testing Improvements

- Added `tests/test_flee_strategy.py` for FleeStrategy unit tests
- Added `tests/test_service_interfaces.py` for interface compliance tests
- Updated existing tests to use new event publishing methods

### SOLID Compliance Verification

| Principle | Status | Notes |
|-----------|--------|-------|
| SRP | ✅ | Each service has a single responsibility |
| OCP | ✅ | New node types can be added via strategy pattern |
| LSP | ✅ | All service implementations follow their interfaces |
| ISP | ✅ | Interfaces are small and focused |
| DIP | ✅ | High-level modules depend on abstractions |