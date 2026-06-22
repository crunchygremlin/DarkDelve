"""
Agent System for DarkDelve

This module provides a generic agent system that allows AI agents to:
1. Perceive the game state (read-only access to relevant game information)
2. Make decisions based on that state
3. Execute actions in the game
4. Communicate with the game through a well-defined interface

The agent system is designed to be generic enough to work for players, NPCs,
commanders, etc., and integrates with the existing EnergySystem for turn-based
execution.
"""

from .base import Agent, AgentType, PerceptionResult
from .actions import AgentAction, ActionType, ActionResult
from .state import AgentGameState, EntityState, ItemState, CombatState
from .llm_agent import LLMAgent, LLMAgentConfig, RandomAgent
from .commander_agent import CommanderAgent

__all__ = [
    # Base types
    "Agent",
    "AgentType",
    "PerceptionResult",
    # Actions
    "AgentAction",
    "ActionType",
    "ActionResult",
    # State
    "AgentGameState",
    "EntityState",
    "ItemState",
    "CombatState",
    # Implementations
    "LLMAgent",
    "LLMAgentConfig",
    "RandomAgent",
    "CommanderAgent",
]