# DarkDelve System Architecture

## High-Level Architecture

DarkDelve follows a layered architecture with clear separation between game logic, content generation, and user interface.

```
┌─────────────────────────────────────────────────────────────┐
│                    Game Layer (Game class)                   │
├─────────────────────────────────────────────────────────────┤
│  Game Logic  │  Content Gen  │  UI/Input  │  Persistence  │
│  Systems     │  Systems      │  Systems   │  Systems      │
├─────────────────────────────────────────────────────────────┤
│                  Core Data Structures                        │
├─────────────────────────────────────────────────────────────┤
│                  External Dependencies                       │
│    TCOD (libtcod)    │    NumPy    │    PyYAML    │    Ollama   │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Game Engine Layer
- **Game**: Main game controller and state manager
- **GameState**: Central game state data structure
- **GameLoop**: Core game loop and timing

### 2. Game Logic Systems
- **DungeonGenerator**: Procedural dungeon generation
- **FOVSystem**: Field of view calculations
- **CombatResolver**: Combat mechanics and resolution
- **EnergySystem**: Action point system
- **SurvivalSystem**: Hunger, health, and survival mechanics
- **IdentificationSystem**: Item identification mechanics

### 3. Content Generation Systems
- **EmbeddedOllama**: Local LLM instance management
- **ContentGenerator**: LLM-based content generation
- **ContentCache**: SQLite-based caching system
- **MobRoster**: Monster templates and generation

### 4. Data Structures
- **Entity**: Player and mobile entities
- **Item**: Item system and inventory
- **Inventory**: Player inventory management
- **CombatLog**: Combat event tracking
- **HighScores**: Score tracking and persistence

### 5. UI/Input Systems
- **UI**: Rendering and display management
- **InputHandler**: Input processing and mapping

### 6. Persistence Systems
- **SaveSystem**: Game state persistence
- **HighScores**: Score persistence

## Data Flow

1. **Game Loop**: Game class manages the main loop
2. **Input Processing**: InputHandler processes player input
3. **State Updates**: Game logic systems update game state
4. **Content Generation**: ContentGenerator creates dynamic content
5. **Rendering**: UI renders the game state
6. **Persistence**: SaveSystem persists game state

## Key Design Patterns

- **Entity Component System**: For game entities
- **Observer Pattern**: For event handling
- **Strategy Pattern**: For different game mechanics
- **Factory Pattern**: For content generation
- **Singleton Pattern**: For global managers (where appropriate)

## Performance Considerations

- **LLM Calls**: Minimize through caching and batching
- **FOV Calculations**: Optimized raycasting algorithm
- **Rendering**: Efficient tile-based rendering
- **Memory Management**: Proper cleanup of temporary objects

## Extensibility Points

- **Content Generation**: Easy to add new LLM prompts
- **Game Mechanics**: Modular system design
- **UI Components**: Separate rendering layers
- **Save Formats**: Abstracted persistence layer
- **Configuration**: YAML-based configuration system