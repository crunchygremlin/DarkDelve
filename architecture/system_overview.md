# DarkDelve System Architecture

## High-Level Architecture

DarkDelve follows a SOLID layered architecture with clear separation of concerns across multiple layers.

```
┌─────────────────────────────────────────────────────────────┐
│                 Presentation Layer                          │
│         Views │ Controllers │ Renderers │ UI Components     │
├─────────────────────────────────────────────────────────────┤
│                Application Layer                            │
│    Commands │ Queries │ Game Session │ Event System         │
├─────────────────────────────────────────────────────────────┤
│                  Domain Layer                               │
│    Entities │ Components │ Value Objects │ Services         │
├─────────────────────────────────────────────────────────────┤
│                Infrastructure Layer                          │
│   Repositories │ External Services │ Persistence │ Config   │
├─────────────────────────────────────────────────────────────┤
│                  Shared Layer                               │
│    Interfaces │ Exceptions │ Utils │ Events              │
├─────────────────────────────────────────────────────────────┤
│                  External Dependencies                       │
│    TCOD (libtcod)    │    NumPy    │    PyYAML    │    Ollama   │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Status

✅ **Phase 1: Foundation Setup** - Completed
✅ **Phase 2: Domain Layer** - Completed
✅ **Phase 3: Application Layer** - Completed
✅ **Phase 4: Infrastructure Layer** - Completed
✅ **Phase 5: Presentation Layer** - Completed
🔄 **Phase 6: Integration and Testing** - In Progress (DM improvements integrated)
⏳ **Phase 7: Optimization and Documentation** - Pending

## Core Components

### 1. Domain Layer ✅ COMPLETED
- **Entities**: Player, Mob, Item base classes
- **Components**: Combat, Movement, Inventory, AI, Equipment
- **Value Objects**: Position, Stats, CombatEvent, InventorySlot, CombatConfig
- **Services**: Combat, Movement, Inventory, AI, Survival (Fuzion d10 DV/AV combat model - monsters, items, skills (weapon_mastery/armor_mastery/tactical_awareness), level, and difficulty factors now integrated via src/domain/services/combat_factors.py single source of truth)

### 2. Application Layer ✅ COMPLETED
- **Commands**: Move, Attack, Pickup, Use, Equip, Drop with undo/redo
- **Queries**: FOV, Combat, Inventory, Entity, Game State with caching
- **Game Session**: Complete session management with state persistence
- **Event System**: Comprehensive event bus with handlers

### 3. Infrastructure Layer ✅ COMPLETED
- **Repositories**: Entity, Item repositories
- **External Services**: Ollama, Cache services
- **Persistence**: Save system, High scores
- **Configuration**: Config loader

### 4. Presentation Layer ✅ COMPLETED
- **Views**: Game view
- **Controllers**: Input controller
- **Renderers**: Tile renderer, main renderer

### 5. Shared Layer ✅ COMPLETED
- **Interfaces**: Repository, Service, Renderer interfaces
- **Exceptions**: Domain, Application, Infrastructure exceptions
- **Utils**: Math utilities
- **Events**: Event, Handler, Bus implementations

### 6. Workflow Layer ✅ COMPLETED
 - **Workflow Controller**: Orchestrates pipeline stages (orchestrator → architect → coder → playtester → debugger)
 - **Pipeline Engine**: Manages stage execution and mode delegation
 - **Task Classification**: Automatic complexity detection (simple, moderate, complex, critical)
 - **Conditional Execution**: Dynamic stage triggering based on task complexity and results

### 7. Map Rendering & Viewport System ✅ COMPLETED
 - **Viewport Camera System**: Centers player character on screen with camera offset tracking
 - **Dynamic Viewport Adjustment**: Camera clamps to map bounds to prevent rendering outside dungeon
 - **Player Visibility Guarantee**: Player character always rendered within console bounds
 - **Entity Rendering with Camera**: All entities rendered relative to camera position

## Data Flow

1. **User Input**: Presentation layer captures user input
2. **Command Processing**: Application layer processes commands
3. **Domain Logic**: Domain layer handles business rules
4. **Infrastructure Access**: Infrastructure layer manages external services
5. **Event Handling**: Event system coordinates component communication
6. **State Management**: Game session maintains consistent state
7. **Query Processing**: Application layer responds to data requests
8. **Presentation Update**: UI layer updates based on state changes

## Local Ollama Player AI Playtest Data Flow

The local playtesting subsystem is intentionally isolated from core game logic.
It treats [`darkdelve.py`](../darkdelve.py:1) as a console application and drives
it through the same stdin/stdout contract used by a human playtester. This flow is
implemented in [`ollama_playtester.py`](../ollama_playtester.py:1) and
[`player_agent.py`](../player_agent.py:1).

```
ollama_playtester.py
├── Popen launches darkdelve.py with piped stdin/stdout/stderr
├── ConsoleFrameParser scrapes \033[H\033[2J ASCII frames
├── PlayerAgent builds Survive & Explore prompt + persona + 5-turn history
├── Ollama /api/generate payload includes "format": "json"
├── JSON response is validated against macro_goal/reasoning/action/telemetry_notes
├── action is injected as one line into game stdin
└── TelemetryStore.append() writes every turn to playtest/playtest_telemetry.json
```

Crash and non-zero-exit records include the final parsed map frame and stderr
tail so local LLM experiments remain debuggable without modifying the game loop.

## Key Design Patterns

### SOLID Architecture Patterns
- **Single Responsibility**: Each layer has a single responsibility
- **Open/Closed**: Components are open for extension, closed for modification
- **Liskov Substitution**: Base classes can be substituted with derived classes
- **Interface Segregation**: Specific interfaces for specific purposes
- **Dependency Inversion**: High-level modules depend on abstractions

### Implementation Patterns
- **Command Pattern**: For game actions (move, attack, pickup, etc.)
- **Query Pattern**: For data retrieval (FOV, inventory, game state)
- **Event Bus Pattern**: For decoupled communication between components
- **Factory Pattern**: For creating game sessions and entities
- **Repository Pattern**: For data access abstraction
- **Strategy Pattern**: For different game mechanics and algorithms
- **Observer Pattern**: For event handling and state notifications
- **Component Composition**: For entity functionality

## Performance Considerations

- **LLM Calls**: Minimize through caching and batching
- **FOV Calculations**: Optimized raycasting algorithm
- **Rendering**: Efficient tile-based rendering
- **Memory Management**: Proper cleanup of temporary objects

## Extensibility Points

### Domain Layer
- **New Entity Types**: Extend base entity classes
- **New Components**: Add component types to entities
- **New Services**: Implement domain services for new mechanics
- **Value Objects**: Create new value objects for game data

### Application Layer
- **New Commands**: Add command classes for new actions
- **New Queries**: Create query classes for new data needs
- **Session Types**: Extend game session factory for new game modes
- **Event Handlers**: Add handlers for new event types

### Infrastructure Layer
- **New Repositories**: Add data access layers for new data types
- **External Services**: Integrate new third-party services
- **Persistence Systems**: Add new storage backends
- **Configuration Sources**: Support new configuration formats

### Presentation Layer
- **New Views**: Add UI views for new game features
- **New Controllers**: Create input controllers for new controls
- **New Renderers**: Add rendering systems for new visual elements
- **UI Components**: Create reusable UI components

### Shared Layer
- **New Interfaces**: Define new abstractions for extensibility
- **New Exceptions**: Add exception types for new error conditions
- **New Utilities**: Create utility functions for common operations
- **New Events**: Define new event types for system communication
