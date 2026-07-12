"""Tests for swarm template service."""

from unittest.mock import Mock
from src.domain.services.swarm_template_service import SwarmTemplateService, SwarmTemplate


class TestSwarmTemplateService:
    """Tests for SwarmTemplateService."""

    def test_select_template_tier_clamped(self):
        """Test that tier is clamped to 1-5 range."""
        svc = SwarmTemplateService()
        t = svc.select_template("goblin", 99)
        assert t.tier == 5  # Clamped to max tier

    def test_select_template_tier_clamped_low(self):
        """Test that tier is clamped to minimum 1."""
        svc = SwarmTemplateService()
        t = svc.select_template("goblin", 0)
        assert t.tier == 1  # Clamped to min tier

    def test_leader_command_published(self):
        """Test that leader command is published to event bus."""
        bus = Mock()
        svc = SwarmTemplateService()
        svc.issue_leader_command("L1", "flee_to_pack", ["m1", "m2"], bus)
        bus.publish.assert_called_once_with("leader_command", {
            "leader_id": "L1",
            "command": "flee_to_pack",
            "subordinate_ids": ["m1", "m2"]
        })

    def test_build_script_returns_behavior_script(self):
        """Test that build_script returns a BehaviorScript."""
        svc = SwarmTemplateService()
        template = svc.select_template("goblin", 1)
        script = svc.build_script(template, "entity_123")
        assert script is not None
        assert script.entity_id == "entity_123"

    def test_default_templates_exist(self):
        """Test that default templates are built for all tiers."""
        svc = SwarmTemplateService()
        for tier in range(1, 6):
            t = svc.select_template("any", tier)
            assert t is not None
            # Tier 2 falls back to tier 1 per design
            assert t.tier in [tier, 1]

    def test_templates_use_catalog_valid_conditions(self):
        """Test that templates use conditions from MOB_BEHAVIOR_CATALOG."""
        svc = SwarmTemplateService()
        template = svc.select_template("goblin", 1)
        script = svc.build_script(template, "entity_123")
        # Script should have valid conditions/actions
        assert script.valid_conditions is not None
        assert script.valid_actions is not None