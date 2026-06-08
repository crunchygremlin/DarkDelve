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
🔄 **Phase 4: Infrastructure Layer** - In Progress
⏳ **Phase 5: Presentation Layer** - Pending
⏳ **Phase 6: Integration and Testing** - Pending
⏳ **Phase 7: Optimization and Documentation** - Pending

## Core Components

### 1. Domain Layer ✅ COMPLETED
- **Entities**: Player, Mob, Item base classes
- **Components**: Combat, Movement, Inventory, AI, Equipment
- **Value Objects**: Position, Stats, CombatEvent, InventorySlot
- **Services**: Combat, Movement, Inventory, AI, Survival

### 2. Application Layer ✅ COMPLETED
- **Commands**: Move, Attack, Pickup, Use, Equip, Drop with undo/redo
- **Queries**: FOV, Combat, Inventory, Entity, Game State with caching
- **Game Session**: Complete session management with state persistence
- **Event System**: Comprehensive event bus with handlers

### 3. Infrastructure Layer 🔄 IN PROGRESS
- **Repositories**: Entity, Item, Game, Cache repositories
- **External Services**: Ollama, TCOD, Cache, HTTP services
- **Persistence**: Save system, High scores, Migration system

### 4. Presentation Layer ⏳ PENDING
- **Views**: Game, Inventory, Log, Menu views
- **Controllers**: Input, UI, Game controllers
- **Renderers**: Tile, Entity, UI, FOV renderers

### 5. Shared Layer ✅ COMPLETED
- **Interfaces**: Repository, Service, Renderer interfaces
- **Exceptions**: Domain, Application, Infrastructure exceptions
- **Utils**: Math, File, Logging utilities
- **Events**: Event, Handler, Bus implementations

## Data Flow

1. **User Input**: Presentation layer captures user input
2. **Command Processing**: Application layer processes commands
3. **Domain Logic**: Domain layer handles business rules
4. **Infrastructure Access**: Infrastructure layer manages external services
5. **Event Handling**: Event system coordinates component communication
6. **State Management**: Game session maintains consistent state
7. **Query Processing**: Application layer responds to data requests
8. **Presentation Update**: UI layer updates based on state changes

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