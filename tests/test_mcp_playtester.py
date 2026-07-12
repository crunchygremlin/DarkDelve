"""Tests for MCP playtester."""

from unittest.mock import Mock
from types import SimpleNamespace
from player_agent import MCPPlayerAgent, PlayerDecision, SAFE_FALLBACK_ACTION, VALID_ACTIONS


class TestMCPPlaytester:
    """Tests for MCPPlaytester."""

    def test_mcp_playtester_runs_with_fake_game(self):
        """Test MCP playtester runs with fake game."""
        from ollama_playtester import MCPPlaytester, PlaytestResult
        
        game = Mock()
        game.state = SimpleNamespace(game_over=False)
        game.process_action = Mock()
        game.turn = 0
        game.player = Mock()
        game.player.hp = 100
        game.render_frame_text = Mock(return_value="frame text")
        
        agent = Mock()
        agent.decide.return_value = PlayerDecision(
            macro_goal="g",
            reasoning="r",
            action="e",
            telemetry_notes="n",
        )
        
        pt = MCPPlaytester(game, agent=agent, max_turns=3)
        res = pt.run()
        
        assert res.turns == 3
        assert game.process_action.call_count == 3
        assert res.status == "done"

    def test_mcp_player_agent_returns_valid_action(self):
        """Test MCP player agent returns valid action."""
        tk = Mock()
        tk.list_entities.return_value = []
        agent = MCPPlayerAgent(tk)
        d = agent.decide()
        assert d.action in VALID_ACTIONS

    def test_mcp_player_agent_safe_action_default(self):
        """Test MCP player agent uses safe action by default."""
        agent = MCPPlayerAgent()
        d = agent.decide()
        assert d.action == SAFE_FALLBACK_ACTION

    def test_mcp_player_agent_records_turn(self):
        """Test MCP player agent records turn in history."""
        agent = MCPPlayerAgent()
        agent.decide()
        assert len(agent.history) == 1


class TestMCPPlayerAgent:
    """Tests for MCPPlayerAgent class."""

    def test_safe_policy_returns_safe_action(self):
        """Test safe policy returns configured safe action."""
        agent = MCPPlayerAgent(safe_action="w")
        action = agent._safe_policy([])
        assert action == "w"

    def test_decide_returns_player_decision(self):
        """Test decide returns PlayerDecision instance."""
        agent = MCPPlayerAgent()
        d = agent.decide()
        assert isinstance(d, PlayerDecision)
        assert d.macro_goal == "MCP auto-play"
        assert d.reasoning == "MCP toolkit policy"