# DarkDelve Module Design

## SOLID Architecture Module Structure

```
src/
├── __init__.py
├── main.py                 # Entry point
├── application_factory.py # Application factory
├── di_container.py        # Dependency injection container
├── domain/               # ✅ COMPLETED
│   ├── __init__.py
│   ├── entities/         # Entity classes
│   │   ├── __init__.py
│   │   ├── entity.py     # Base entity
│   │   ├── player.py     # Player entity
│   │   └── mob.py        # Monster entity
│   ├── components/       # Component system
│   │   ├── __init__.py
│   │   ├── component.py  # Base component
│   │   ├── combat.py     # Combat component
│   │   ├── movement.py   # Movement component
│   │   ├── inventory.py  # Inventory component
│   │   ├── ai.py         # AI component
│   │   └── equipment.py  # Equipment component
│   ├── value_objects/    # Immutable data
│   │   ├── __init__.py
│   │   ├── position.py   # Position coordinates
│   │   ├── stats.py      # Character stats
│   │   ├── combat_event.py # Combat events
│   │   └── inventory_slot.py # Inventory slots
│   ├── services/         # Domain services
│   │   ├── __init__.py
│   │   ├── combat_service.py
│   │   ├── movement_service.py
│   │   ├── inventory_service.py
│   │   ├── ai_service.py
│   │   └── survival_service.py
│   └── __init__.py
├── application/          # ✅ COMPLETED
│   ├── __init__.py
│   ├── game_commands/    # Command pattern
│   │   ├── __init__.py
│   │   ├── base_command.py
│   │   ├── move_command.py
│   │   ├── attack_command.py
│   │   ├── pickup_command.py
│   │   ├── use_command.py
│   │   ├── equip_command.py
│   │   └── drop_command.py
│   ├── game_queries/     # Query pattern
│   │   ├── __init__.py
│   │   ├── base_query.py
│   │   ├── fov_query.py
│   │   ├── combat_query.py
│   │   ├── inventory_query.py
│   │   ├── entity_query.py
│   │   └── game_state_query.py
│   ├── game_session/     # Session management
│   │   ├── __init__.py
│   │   ├── game_session.py
│   │   └── game_session_factory.py
│   ├── event_system/     # Event system
│   │   ├── __init__.py
│   │   ├── base_event.py
│   │   ├── event_handler.py
│   │   ├── event_bus.py
│   │   └── handlers/
│   │       ├── __init__.py
│   │       ├── combat_handler.py
│   │       ├── player_handler.py
│   │       └── system_handler.py
│   └── __init__.py
├── infrastructure/       # ✅ COMPLETED
│   ├── __init__.py
│   ├── repositories/     # Data access
│   │   ├── __init__.py
│   │   ├── entity_repository.py
│   │   ├── item_repository.py
│   │   └── __init__.py
│   ├── external/         # External services
│   │   ├── __init__.py
│   │   ├── ollama_service.py
│   │   ├── cache_service.py
│   │   └── __init__.py
│   ├── persistence/      # Persistence layer
│   │   ├── __init__.py
│   │   ├── save_system.py
│   │   ├── highscores.py
│   │   └── __init__.py
│   ├── configuration/    # Configuration
│   │   ├── __init__.py
│   │   ├── config_loader.py
│   │   └── __init__.py
│   └── __init__.py
├── presentation/        # ✅ COMPLETED
│   ├── __init__.py
│   ├── renderer.py
│   ├── views/           # UI views
│   │   ├── __init__.py
│   │   └── views.py
│   ├── controllers/     # Input controllers
│   │   ├── __init__.py
│   │   ├── input_controller.py
│   │   └── __init__.py
│   └── renderers/      # Rendering system
│       ├── __init__.py
│       ├── tile_renderer.py
│       └── __init__.py
├── shared/              # ✅ COMPLETED
│   ├── __init__.py
│   ├── interfaces/     # Abstract interfaces
│   │   ├── __init__.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   └── renderer.py
│   ├── exceptions/      # Exception hierarchy
│   │   ├── __init__.py
│   │   ├── domain_exceptions.py
│   │   ├── application_exceptions.py
│   │   └── infrastructure_exceptions.py
│   ├── utils/          # Utility functions
│   │   ├── __init__.py
│   │   ├── math_utils.py
│   │   └── __init__.py
│   └── events/         # Event definitions
│       ├── __init__.py
│       ├── event.py
│       └── __init__.py
└── tests/              # Test suite
    ├── unit/           # Unit tests
    ├── integration/    # Integration tests
    └── system/         # System tests
```

## Implementation Status

✅ **Phase 1: Foundation Setup** - Completed
✅ **Phase 2: Domain Layer** - Completed
✅ **Phase 3: Application Layer** - Completed
✅ **Phase 4: Infrastructure Layer** - Completed
✅ **Phase 5: Presentation Layer** - Completed
✅ **Phase 6: Integration and Testing** - Completed
⏳ **Phase 7: Optimization and Documentation** - Pending

## Local Ollama Playtest Subsystem

The local playtest subsystem is root-level tooling rather than core game code so
it can be added, tested, and removed without refactoring [`darkdelve.py`](../darkdelve.py:1).

```
player_agent.py
├── OllamaConfig                 # endpoint/model/temperature/top_p/num_predict/timeout/retries
├── PlayerDecision               # validated macro_goal/reasoning/action/telemetry_notes
├── PlayerAgent
│   ├── build_system_prompt()    # Survive & Explore baseline + persona + JSON schema
│   ├── build_user_prompt()      # frame, stats, and recent 5-turn history
│   ├── request_ollama()         # POST /api/generate with "format": "json"
│   ├── sanitize_json_response() # fence extraction, object extraction, Python literal fallback
│   ├── validate_response()      # string fields and action in w/a/s/d/e/i
│   └── record_turn()            # keep only the last five decisions

ollama_playtester.py
├── PlaytestConfig               # YAML/CLI runtime settings
├── ConsoleFrameParser           # split \033[H\033[2J frames and extract stats
├── TelemetryStore               # atomic JSON append to playtest/playtest_telemetry.json
└── OllamaPlaytester             # Popen loop, action injection, crash logging

+playtest/instruction_bus.py
+├── PlaytestInstructions         # enabled/target/setup/push payload
+├── InstructionBus               # atomic JSON load/save and clear_push()
+├── target_matches()             # deterministic scoped target matching
+└── format_instruction_prompt()  # setup/push text for prompt injection
+```

Built-in personas are `Default`, `Aggressive Stress-Tester`, and `Boundary
Pushing Explorer`. Invalid or malformed model responses must never be injected
as arbitrary text: validate, log the issue in telemetry, and fall back to the
safe wait action `e`.

## Detailed Module Specifications

### 1. Domain Layer ✅ COMPLETED

#### Entities
- **`entity.py`**: Base entity class with component system
- **`player.py`**: Player entity with combat, movement, and inventory
- **`mob.py`**: Monster entity with AI and combat capabilities

#### Components
- **`component.py`**: Base component class with lifecycle management
- **`combat.py`**: Combat mechanics and damage calculation
- **`movement.py`**: Movement and position management
- **`inventory.py`**: Item management and equipment
- **`ai.py`**: AI behavior and decision making
- **`equipment.py`**: Equipment management and stat modifications

#### Value Objects
- **`position.py`**: Immutable position coordinates
- **`stats.py`**: Character statistics and attributes
- **`combat_event.py`**: Combat event data structure
- **`inventory_slot.py`**: Inventory slot management

#### Services
- **`combat_service.py`**: Combat domain logic
- **`movement_service.py`**: Movement domain logic
- **`inventory_service.py`**: Inventory management logic
- **`ai_service.py`**: AI domain logic
- **`survival_service.py`**: Survival mechanics domain logic

### 2. Application Layer ✅ COMPLETED

#### Commands
- **`base_command.py`**: Abstract command class with undo/redo support
- **`move_command.py`**: Player movement command
- **`attack_command.py`**: Combat attack command
- **`pickup_command.py`**: Item pickup command
- **`use_command.py`**: Item usage command
- **`equip_command.py`**: Equipment management command
- **`drop_command.py`**: Item drop command

#### Queries
- **`base_query.py`**: Abstract query class with caching
- **`fov_query.py`**: Field of view calculations
- **`combat_query.py`**: Combat information and statistics
- **`inventory_query.py`**: Inventory management queries
- **`entity_query.py`**: Entity information queries
- **`game_state_query.py`**: Comprehensive game state queries

#### Game Session
- **`game_session.py`**: Complete session management with state persistence
- **`game_session_factory.py`**: Factory for creating different session types

#### Event System
- **`base_event.py`**: Event class with categories and priorities
- **`event_handler.py`**: Handler interfaces and implementations
- **`event_bus.py`**: Event bus with async/sync processing
- **`handlers/combat_handler.py`**: Combat event handling
- **`handlers/player_handler.py`**: Player event handling
- **`handlers/system_handler.py`**: System event handling

### 3. Infrastructure Layer ✅ COMPLETED

#### Repositories
- **`entity_repository.py`**: Entity data access
- **`item_repository.py`**: Item data access

#### External Services
- **`ollama_service.py`**: Ollama LLM integration
- **`cache_service.py`**: SQLite content caching

#### Persistence
- **`save_system.py`**: Game save/load management
- **`highscores.py`**: High scores persistence

#### Configuration
- **`config_loader.py`**: YAML configuration loading

### 4. Presentation Layer ✅ COMPLETED

#### Renderer
- **`renderer.py`**: Main game renderer with ConsoleRenderer
- **`tile_renderer.py`**: Tile-based rendering system

#### Controllers
- **`input_controller.py`**: Input handling and key bindings

### 5. Shared Layer ✅ COMPLETED

#### Interfaces
- **`repository.py`**: Repository pattern interface
- **`service.py`**: Service interface
- **`renderer.py`**: Renderer interface

#### Exceptions
- **`domain_exceptions.py`**: Domain layer exceptions
- **`application_exceptions.py`**: Application layer exceptions
- **`infrastructure_exceptions.py`**: Infrastructure layer exceptions

#### Utils
- **`math_utils.py`**: Math utility functions (clamp, heuristic, distance)

#### Events
- **`event.py`**: Event class and EventCategory enum
- **`event_handler.py`**: EventHandler interface
- **`event_bus.py`**: EventBus implementation

## Module Dependencies

### SOLID Architecture Dependencies

```
main.py
├── application_factory.py    # Application factory
├── di_container.py           # Dependency injection container
├── domain/                   # Domain layer (core business logic)
│   ├── entities/             # Entity definitions
│   ├── components/           # Component system
│   ├── value_objects/        # Immutable data
│   └── services/             # Domain services
├── application/              # Application layer (use cases)
│   ├── game_commands/        # Command pattern
│   ├── game_queries/         # Query pattern
│   ├── game_session/         # Session management
│   └── event_system/         # Event handling
├── infrastructure/           # Infrastructure layer (external concerns)
│   ├── repositories/         # Data access
│   ├── external/             # External services
│   ├── persistence/          # Persistence
│   └── configuration/        # Configuration
├── presentation/             # Presentation layer (UI)
│   ├── views/                # UI views
│   ├── controllers/          # Input controllers
│   └── renderers/           # Rendering system
└── shared/                   # Shared utilities
    ├── interfaces/           # Abstract interfaces
    ├── exceptions/            # Exception hierarchy
    ├── utils/                # Utility functions
    └── events/               # Event definitions
```

### Dependency Flow

```
Presentation Layer
    ↓ (depends on)
Application Layer
    ↓ (depends on)
Domain Layer
    ↓ (depends on)
Infrastructure Layer
    ↓ (depends on)
Shared Layer
```

### Integration Points

1. **Command Processing**: Application layer processes user input through commands
2. **Query Handling**: Application layer responds to data requests through queries
3. **Event Communication**: Event system coordinates communication between layers
4. **Repository Pattern**: Infrastructure layer provides data access through repositories
5. **Dependency Injection**: DI container manages dependencies between layers
6. **Interface Segregation**: Each layer depends on abstractions, not implementations
7. **Session Management**: Game session coordinates state across all layers
8. **Configuration Management**: Shared configuration provides consistent settings

### Key Design Principles

- **Single Responsibility**: Each layer has a single, well-defined responsibility
- **Open/Closed**: Components are open for extension, closed for modification
- **Liskov Substitution**: Base classes can be substituted with derived classes
- **Interface Segregation**: Clients depend on specific interfaces, not general ones
- **Dependency Inversion**: High-level modules depend on abstractions, not low-level modules
