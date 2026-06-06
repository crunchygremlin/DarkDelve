# AI Overview

## Project Summary

This project is an AI-driven roguelike game engine, utilizing a local Large Language Model (LLM) for decision-making and interactive elements. The core features include:

1. **Local LLM Worker**: A background thread that continuously processes prompts from the request queue and sends them to an LLM endpoint.
2. **Game Entities**: Represents game entities such as players, monsters, and commanders with properties like position, health, power, etc.
3. **Pathfinding**: Implements pathfinding using the A* algorithm to navigate the game map.
4. **Command Handling**: Interprets commands from the LLM response and updates game entities accordingly.

## Key Components

- `local_llm_worker`: Manages LLM requests and responses.
- `start_llm_worker`: Starts the background LLM worker.
- `validate_llm_response`: Validates and normalizes LLM responses.
- `is_blocked`: Checks if a position is blocked by any entity.
- `get_neighbors`: Generates neighboring positions for movement.
- `heuristic`: Computes heuristic distance between two points.
- `find_path`: Finds the shortest path using A* algorithm.
- `enqueue_commander_prompt`: Enqueues prompts from commanders for LLM processing.
- `interpret_commander_action`: Interprets actions from LLM responses.
- `get_llm_metrics`: Retrieves metrics related to LLM requests and responses.
- `process_llm_responses`: Processes LLM responses and updates game entities.

## Dependencies

The following dependencies are required:

- Python 3.8 or later
- numpy
- tcod
- urllib.request
- json
- os
- logging
- heapq
- math
- time
- threading
- queue

To run the project, execute `python main.py` in the terminal.

## Usage Instructions

1. **Install Dependencies**: Run `pip install -r requirements.txt`.
2. **Start Game**: Execute `python main.py`.

For more detailed information and setup instructions, refer to the README file.