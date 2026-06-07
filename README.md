# DarkDelve

A traditional roguelike with local LLM content generation. Single binary, no external dependencies.

## Features

- **Traditional roguelike gameplay**: Turn-based, grid-based, permadeath, procedural generation
- **Local LLM integration**: Uses Ollama (qwen2.5-coder:7b) for dynamic content generation
- **Embedded Ollama**: Game manages Ollama subprocess automatically
- **Persistent caching**: SQLite cache for LLM generations survives restarts
- **Character classes**: Warrior, Rogue, Mage, Cleric with unique skills
- **Energy-based turn system**: Speed-based scheduling like classic roguelikes
- **Full inventory/equipment**: Weight management, equipment slots, identification minigame
- **Hunger/food clock**: Classic survival pressure
- **Multi-level dungeon**: 26 levels with branches (Catacombs, Abyss)
- **Save/Load**: Save on quit, permadeath on death
- **High scores**: Local leaderboard
- **Single binary distribution**: PyInstaller build with bundled Ollama

## Quick Start

### Prerequisites
- Python 3.9+
- pip packages: `tcod numpy pyyaml requests`

### Development Run
```bash
# Install dependencies
pip install -r requirements.txt

# Run directly
python darkdelve.py
```

### Build Standalone Executable
```bash
# Install PyInstaller
pip install pyinstaller

# Build (downloads Ollama binaries automatically)
python build.py

# Run the executable
./dist/darkdelve
```

## Controls

| Key | Action |
|-----|--------|
| WASD / Arrow Keys | Move / Attack |
| Space | Wait |
| `,` / `g` | Pick up item |
| `i` | Inventory |
| `c` | Character screen |
| `>` | Descend stairs |
| `<` | Ascend stairs |
| `ESC` | Menu (Save & Quit / Quit) |

## Gameplay

### Character Classes
- **Warrior**: High HP, melee combat, shield block
- **Rogue**: High DEX, backstab, evasion, trap disarm
- **Mage**: Spells (fireball, blink, shield), low HP
- **Cleric**: Healing, turn undead, divine strike

### Systems
- **Combat**: d20-based with AC, critical hits, damage dice
- **Identification**: Potions/scrolls unidentified until used or identified
- **Hunger**: Nutrition decreases each turn; starvation causes damage
- **Permadeath**: Death deletes save; high score recorded
- **Progression**: XP from kills, level up for HP and skill points

### LLM Content Generation
The game uses a local Ollama instance to generate:
- Level themes (atmosphere, hazards, tile sets)
- Monster rosters (unique enemies per level)
- Items (weapons, armor, potions, scrolls with special effects)

All generations are cached in SQLite for instant reuse.

## Configuration

Edit `config/game.yaml` to customize:
- Display settings (resolution, tileset)
- Dungeon parameters (size, rooms, depth)
- LLM settings (model, temperature, timeout)
- Gameplay toggles (permadeath, hunger, identification)
- Class stats and starting gear

## Project Structure

```
DarkDelve/
├── darkdelve.py          # Main game (single file)
├── build.py              # Build script
├── config/
│   └── game.yaml         # All configuration
├── assets/
│   └── tilesets/         # Font tilesheet
├── vendor/               # Bundled Ollama binaries (gitignored)
├── cache/                # LLM generation cache (gitignored)
├── saves/                # Save files (gitignored)
├── highscores.json       # Leaderboard
├── requirements.txt      # Python dependencies
└── README.md
```

## Distribution

The build script creates a standalone executable with:
- Bundled Ollama binary for the platform
- Config, assets, and vendor directories
- No installation required - just run the binary

## License

MIT License - See LICENSE file for details.