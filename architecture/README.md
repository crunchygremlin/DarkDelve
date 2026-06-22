# DarkDelve Architecture Documentation

This folder contains architecture documentation for refactoring the monolithic DarkDelve codebase into a modular structure suitable for development with local LLM models (Qwen 7b Coder).

## Overview

DarkDelve is a traditional roguelike game with local LLM content generation. The current monolithic implementation is challenging to maintain and extend. This architecture provides a clear, modular structure that can be easily understood and implemented by an LLM assistant.

## Directory Structure

```
architecture/
├── README.md                    # This file
├── system_overview.md          # High-level system architecture
├── module_design.md            # Detailed module specifications
├── implementation_guide.md      # Step-by-step refactoring guide
├── coding_standards.md         # Coding standards and patterns
├── api_interfaces.md           # Module interfaces and contracts
└── gotchas.md                  # Repeated development pitfalls and fixes
```

The root also contains the local Ollama playtesting subsystem. It includes a
file-based operator instruction bus so persistent `setup` and one-shot `push`
instructions can be injected into Player AI, Dungeon Master/content, and commander
prompts without mixing the operator instruction channel with the game window.
 
The root also contains the local Ollama playtesting subsystem:

```
player_agent.py                 # Prompt builder, Ollama JSON contract, validation
ollama_playtester.py            # Subprocess console scraper and action injector
playtest/
├── README.md                   # Usage and telemetry format
├── playtest_config.yaml        # Default endpoint/model/persona settings
└── telemetry/                  # Runtime telemetry directory
```

## Target Environment

- **Hardware**: NVIDIA 1080ti on Kubuntu
- **LLM**: Ollama with Qwen 7b Coder model
- **Development**: Local coding environment
- **Constraints**: Code should be understandable and implementable by a 7b parameter model

## Key Principles

1. **Modularity**: Clear separation of concerns
2. **Simplicity**: Easy to understand and modify
3. **Consistency**: Uniform coding patterns
4. **Testability**: Each module should be independently testable
5. **Extensibility**: Easy to add new features

## Next Steps

1. Review system overview
2. Understand module design
3. Follow implementation guide
4. Apply coding standards
5. Use API interfaces for integration