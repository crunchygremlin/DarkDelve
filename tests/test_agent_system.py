"""
Tests for the DarkDelve agent system.

This module tests the core agent classes, actions, and state representations.
"""

import pytest
from dataclasses import dataclass
from typing import Any, Dict, Optional

# Import agent system components
import sys
sys.path.insert(0, '.')

from src.domain.agents.base import Agent, AgentType, PerceptionResult
from src.domain.agents.actions import AgentAction, ActionType, ActionResult
from src.domain.agents.state import AgentGameState, EntityState, ItemState, CombatState
from src.domain.agents.llm_agent import LLMAgent, LLMAgentConfig, RandomAgent
from src.domain.agents.commander_agent import CommanderAgent, CommanderOrder, AgentManager
from src.domain.agents.integration import AgentTurnProcessor


class TestPerceptionResult:
    """Tests for PerceptionResult dataclass."""
    
    def test_creation(self):
        """Test basic creation of PerceptionResult."""
        result = PerceptionResult(
            entity_id="test_entity",
            position=(5, 10),
            health=50,
            max_health=100
        )
        assert result.entity_id == "test_entity"
        assert result.position == (5, 10)
        assert result.health == 50
        assert result.max_health == 100
    
    def test_health_percent(self):
        """Test health percentage calculation."""
        result = PerceptionResult(
            entity_id="test",
            position=(0, 0),
            health=75,
            max_health=100
        )
        assert result.health_percent == 0.75
    
    def test_health_percent_zero_max(self):
        """Test health percentage with zero max health."""
        result = PerceptionResult(
            entity_id="test",
            position=(0, 0),
            health=0,
            max_health=0
        )
        assert result.health_percent == 0.0
    
    def test_to_prompt_context(self):
        """Test prompt context generation."""
        result = PerceptionResult(
            entity_id="player",
            position=(10, 10),
            health=100,
            max_health=100,
            visible_entities=[{"name": "goblin", "position": (12, 10)}]
        )
        context = result.to_prompt_context()
        assert "player" in context
        assert "100/100" in context


class TestAgentAction:
    """Tests for AgentAction class."""
    
    def test_move_to_action(self):
        """Test creating a move-to action."""
        action = AgentAction.move_to(5, 10)
        assert action.action_type == ActionType.MOVE_TO
        assert action.target_position == (5, 10)
    
    def test_attack_action(self):
        """Test creating an attack action."""
        action = AgentAction.attack("enemy_1")
        assert action.action_type == ActionType.ATTACK
        assert action.target_id == "enemy_1"
    
    def test_wait_action(self):
        """Test creating a wait action."""
        action = AgentAction.wait()
        assert action.action_type == ActionType.WAIT
    
    def test_is_movement(self):
        """Test movement action detection."""
        move_action = AgentAction.move_to(5, 5)
        wait_action = AgentAction.wait()
        assert move_action.is_movement() is True
        assert wait_action.is_movement() is False
    
    def test_is_combat(self):
        """Test combat action detection."""
        attack_action = AgentAction.attack("target")
        move_action = AgentAction.move_to(5, 5)
        assert attack_action.is_combat() is True
        assert move_action.is_combat() is False
    
    def test_to_game_command(self):
        """Test conversion to game command."""
        north_action = AgentAction(action_type=ActionType.MOVE_NORTH)
        wait_action = AgentAction(action_type=ActionType.WAIT)
        assert north_action.to_game_command() == 'w'
        assert wait_action.to_game_command() == 'e'


class TestActionResult:
    """Tests for ActionResult class."""
    
    def test_success_result(self):
        """Test creating a success result."""
        result = ActionResult.success_result("Action completed")
        assert result.success is True
        assert result.message == "Action completed"
    
    def test_failure_result(self):
        """Test creating a failure result."""
        result = ActionResult.failure_result("Action failed")
        assert result.success is False
        assert result.message == "Action failed"
    
    def test_no_op_result(self):
        """Test creating a no-op result."""
        result = ActionResult.no_op()
        assert result.success is True
        assert result.message == "No action taken"


class TestEntityState:
    """Tests for EntityState class."""
    
    def test_creation(self):
        """Test basic creation."""
        state = EntityState(
            entity_id="entity_1",
            name="Goblin",
            position=(5, 10),
            health=20,
            max_health=30,
            is_alive=True,
            is_commander=False,
            is_player=False
        )
        assert state.entity_id == "entity_1"
        assert state.name == "Goblin"
    
    def test_health_percent(self):
        """Test health percentage calculation."""
        state = EntityState(
            entity_id="e1",
            name="test",
            position=(0, 0),
            health=50,
            max_health=100,
            is_alive=True,
            is_commander=False,
            is_player=False
        )
        assert state.health_percent == 0.5
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        state = EntityState(
            entity_id="e1",
            name="test",
            position=(5, 10),
            health=50,
            max_health=100,
            is_alive=True,
            is_commander=False,
            is_player=False
        )
        d = state.to_dict()
        assert d["id"] == "e1"
        assert d["name"] == "test"
        assert d["position"] == (5, 10)


class TestAgentGameState:
    """Tests for AgentGameState class."""
    
    def test_creation(self):
        """Test basic creation."""
        state = AgentGameState(
            turn=1,
            depth=5,
            entities=[],
            items=[]
        )
        assert state.turn == 1
        assert state.depth == 5
    
    def test_get_entity(self):
        """Test getting an entity by ID."""
        entity = EntityState(
            entity_id="e1",
            name="test",
            position=(0, 0),
            health=10,
            max_health=10,
            is_alive=True,
            is_commander=False,
            is_player=False
        )
        state = AgentGameState(
            turn=1,
            depth=1,
            entities=[entity]
        )
        found = state.get_entity("e1")
        assert found is not None
        assert found.name == "test"
    
    def test_get_nearby_entities(self):
        """Test getting nearby entities."""
        entities = [
            EntityState("e1", "near", (10, 10), 10, 10, True, False, False),
            EntityState("e2", "far", (20, 20), 10, 10, True, False, False),
        ]
        state = AgentGameState(
            turn=1,
            depth=1,
            entities=entities,
            player_position=(10, 10)
        )
        nearby = state.get_nearby_entities(radius=5)
        assert len(nearby) == 1
        assert nearby[0].name == "near"


class TestLLMAgent:
    """Tests for LLMAgent class."""
    
    @pytest.fixture
    def mock_entity(self):
        """Create a mock entity for testing."""
        @dataclass
        class MockEntity:
            id: str = "test_entity"
            name: str = "Test Entity"
            x: int = 10
            y: int = 10
            hp: int = 100
            max_hp: int = 100
            inventory: Optional[Any] = None
        
        entity = MockEntity()
        return entity
    
    def test_creation(self, mock_entity):
        """Test LLMAgent creation."""
        agent = LLMAgent(mock_entity)
        assert agent.entity_id == "test_entity"
        assert agent.name == "Test Entity"
    
    def test_perceive(self, mock_entity):
        """Test perception method."""
        agent = LLMAgent(mock_entity)
        game_state = AgentGameState(turn=1, depth=1, entities=[], items=[])
        perception = agent.perceive(game_state)
        assert perception.entity_id == "test_entity"
        assert perception.position == (10, 10)


class TestRandomAgent:
    """Tests for RandomAgent class."""
    
    @pytest.fixture
    def mock_entity(self):
        """Create a mock entity for testing."""
        @dataclass
        class MockEntity:
            id: str = "random_entity"
            name: str = "Random Bot"
            x: int = 5
            y: int = 5
            hp: int = 50
            max_hp: int = 50
            inventory: Optional[Any] = None
        
        return MockEntity()
    
    def test_creation(self, mock_entity):
        """Test RandomAgent creation."""
        agent = RandomAgent(mock_entity)
        assert agent.entity_id == "random_entity"
    
    def test_decide_returns_action(self, mock_entity):
        """Test that decide returns a valid action."""
        agent = RandomAgent(mock_entity)
        perception = PerceptionResult(
            entity_id="random_entity",
            position=(5, 5),
            health=50,
            max_health=50
        )
        action = agent.decide(perception)
        assert isinstance(action, AgentAction)


class TestCommanderAgent:
    """Tests for CommanderAgent class."""
    
    @pytest.fixture
    def mock_entity(self):
        """Create a mock commander entity."""
        @dataclass
        class MockEntity:
            id: str = "commander_1"
            name: str = "Battle Commander"
            x: int = 0
            y: int = 0
            hp: int = 100
            max_hp: int = 100
            is_commander: bool = True
            current_command: Optional[Dict] = None
        
        return MockEntity()
    
    def test_creation(self, mock_entity):
        """Test CommanderAgent creation."""
        agent = CommanderAgent(mock_entity, home_position=(0, 0))
        assert agent.entity_id == "commander_1"
        assert agent.home_position == (0, 0)
    
    def test_add_subordinate(self, mock_entity):
        """Test adding subordinates."""
        agent = CommanderAgent(mock_entity)
        agent.add_subordinate("soldier_1")
        assert "soldier_1" in agent._subordinates
    
    def test_get_order_for_subordinate(self, mock_entity):
        """Test getting orders for subordinates."""
        agent = CommanderAgent(mock_entity)
        agent.add_subordinate("soldier_1")
        order = CommanderOrder(command="ATTACK_PLAYER", target_id="player_1")
        agent._pending_orders["soldier_1"] = order
        
        result = agent.get_order_for_subordinate("soldier_1")
        assert result is not None
        assert result.command == "ATTACK_PLAYER"


class TestAgentManager:
    """Tests for AgentManager class."""
    
    def test_register_agent(self):
        """Test registering an agent."""
        manager = AgentManager()
        
        @dataclass
        class MockEntity:
            id: str = "e1"
            name: str = "Test"
            x: int = 0
            y: int = 0
            hp: int = 10
            max_hp: int = 10
        
        entity = MockEntity()
        agent = RandomAgent(entity)
        manager.register_agent(agent)
        
        assert manager.get_agent("e1") is agent
    
    def test_unregister_agent(self):
        """Test unregistering an agent."""
        manager = AgentManager()
        
        @dataclass
        class MockEntity:
            id: str = "e1"
            name: str = "Test"
            x: int = 0
            y: int = 0
            hp: int = 10
            max_hp: int = 10
        
        entity = MockEntity()
        agent = RandomAgent(entity)
        manager.register_agent(agent)
        manager.unregister_agent("e1")
        
        assert manager.get_agent("e1") is None


class TestActionType:
    """Tests for ActionType enum."""
    
    def test_all_action_types_exist(self):
        """Test that all expected action types exist."""
        expected = [
            "MOVE_NORTH", "MOVE_SOUTH", "MOVE_EAST", "MOVE_WEST", "MOVE_TO",
            "ATTACK", "ATTACK_TARGET", "PICKUP", "USE", "EQUIP", "DROP",
            "WAIT", "CAST_SPELL", "USE_ITEM", "ISSUE_COMMAND", "HOLD_POSITION",
            "FLANK", "NONE"
        ]
        for name in expected:
            assert hasattr(ActionType, name), f"ActionType.{name} should exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])