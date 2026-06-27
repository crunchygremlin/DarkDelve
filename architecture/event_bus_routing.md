# Event Bus Routing Architecture

> Cross-cutting concern: how events flow between SOLID layers.

## Overview

DarkDelve uses an event bus (`src/application/event_system/event_bus.py`) to decouple
the domain, application, and infrastructure layers. This document describes the
event types, their routing, and which handlers subscribe to them.

## Event Bus Implementation

| Component | File | Responsibility |
|-----------|------|----------------|
| Base event | `src/shared/events/event.py` | `Event` dataclass with timestamp, type, data |
| Event handler | `src/shared/events/event_handler.py` | `EventHandler` interface |
| Event bus | `src/application/event_system/event_bus.py` | `EventBus` with pub/sub, priority, history |
| Base event | `src/application/event_system/base_event.py` | `BaseEvent` with categories and priorities |

## Event Categories

### Domain Events (internal to domain layer)

| Event Type | Publisher | Subscribers | Purpose |
|------------|-----------|-------------|---------|
| `CombatEvent` | `CombatService` | `CombatHandler`, `TelemetryHandler` | Attack resolution, damage dealt |
| `PerceptionUpdated` | `PerceptionService` | `PerceptionHandler`, AI agents | Entity perception state changed |
| `BehaviorScriptSelected` | `BehaviorEngine` | `TelemetryHandler` | AI selected a new behavior script |
| `LoyaltyChanged` | `SocialService` | `SocialHandler`, AI agents | Loyalty score crossed threshold |
| `MovementEvent` | `MovementService` | FOV system, `PerceptionHandler` | Entity moved to new position |

### Application Events (cross-layer coordination)

| Event Type | Publisher | Subscribers | Purpose |
|------------|-----------|-------------|---------|
| `ItemCreated` | `ItemFactoryService` | `LootService`, UI | New item spawned |
| `ItemPickedUp` | `GameSession` | `InventoryService`, UI, telemetry | Player picked up item |
| `LootDistributed` | `LootService` | UI, telemetry | Loot placed on level |
| `DungeonGenerated` | `DungeonMasterService` | `NarrativeService`, `LootService`, UI | New level created |
| `PuzzleSolved` | `PuzzleService` | `NarrativeService`, reward system | Player solved puzzle |
| `NarrativeHint` | `NarrativeService` | UI controller | Hint available for player |

### System Events (infrastructure and lifecycle)

| Event Type | Publisher | Subscribers | Purpose |
|------------|-----------|-------------|---------|
| `GameStarted` | `GameSession` | All services | Initialize systems |
| `GameEnded` | `GameSession` | `Highscores`, telemetry, save system | Cleanup and record |
| `ErrorEvent` | Any layer | `SystemHandler`, telemetry | Error occurred |
| `SaveGame` | `GameSession` | `SaveSystem` | Persist state |
| `LoadGame` | `GameSession` | `SaveSystem` | Restore state |

## Handler Implementations

| Handler | File | Events Handled |
|---------|------|----------------|
| `CombatHandler` | `src/application/event_system/handlers/combat_handler.py` | `CombatEvent` |
| `PlayerHandler` | `src/application/event_system/handlers/player_handler.py` | Player actions |
| `PerceptionHandler` | `src/application/event_system/handlers/perception_handler.py` | `PerceptionUpdated` |
| `SocialHandler` | `src/application/event_system/handlers/social_handler.py` | `LoyaltyChanged` |
| `SystemHandler` | `src/application/event_system/handlers/system_handler.py` | `ErrorEvent`, lifecycle |
| `TelemetryHandler` | `src/application/event_system/handlers/telemetry_handler.py` | All events (telemetry) |

## Event Flow Diagram

```
Domain Layer
    │
    ├── CombatService ──────► CombatEvent ──────────► CombatHandler
    │                                                   │
    ├── PerceptionService ─► PerceptionUpdated ─────► PerceptionHandler
    │                                                   │
    ├── SocialService ──────► LoyaltyChanged ────────► SocialHandler
    │                                                   │
    └── MovementService ───► MovementEvent ─────────► PerceptionHandler
                                                        │
Application Layer                                       │
    │                                                   │
    ├── GameSession ────────► ItemPickedUp ──────────► InventoryService
    │                                                   │
    ├── LootService ────────► LootDistributed ───────► UI
    │                                                   │
    └── DungeonMasterService ► DungeonGenerated ─────► NarrativeService
                                                        │
Infrastructure Layer                                    │
    │                                                   │
    ├── SaveSystem ◄──────── SaveGame ─────────────────┘
    │
    └── Highscores ◄─────── GameEnded ─────────────────► Telemetry
```

## Integration Points

1. **Event → Handler**: Handlers are registered with `EventBus.subscribe(event_type, handler)`
2. **Handler → Service**: Handlers call domain services to perform side effects
3. **Handler → UI**: Handlers trigger UI updates through presentation layer
4. **Telemetry**: `TelemetryHandler` subscribes to ALL events for playtest capture

## Gotchas

- Events must be immutable after publishing — do not mutate event data in handlers
- Do not create circular event chains (e.g., Event A triggers Event B which triggers Event A)
- Handler execution order is determined by `EventPriority` — do not assume FIFO ordering
- Long-running handlers should use async processing via `EventBus.publish_async()`
