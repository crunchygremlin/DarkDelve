"""Tests for Entity AI configuration loader."""

import os
import tempfile
import pytest
from src.infrastructure.configuration.entity_ai_config_loader import EntityAIConfigLoader


class TestEntityAIConfigLoader:
    """Tests for EntityAIConfigLoader class."""

    def test_load_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        assert loader.config is not None
        assert "mob_types" in loader.config
        assert "social_structures" in loader.config
        assert "loyalty" in loader.config
        assert "perception" in loader.config
        assert "behavior" in loader.config

    def test_default_config_when_file_missing(self):
        """Test default config returned when file doesn't exist."""
        loader = EntityAIConfigLoader("nonexistent_path.yaml")
        assert loader.config == {
            "mob_types": {},
            "social_structures": {},
            "loyalty": {},
            "perception": {},
            "behavior": {},
        }

    def test_get_mob_type_returns_correct_data(self):
        """Test get_mob_type returns correct mob data."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        goblin = loader.get_mob_type("goblin")
        assert goblin["display_name"] == "Goblin"
        assert goblin["health"] == 15
        assert goblin["speed"] == 1.0

    def test_get_mob_type_missing_returns_empty(self):
        """Test get_mob_type returns empty dict for missing type."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        result = loader.get_mob_type("nonexistent")
        assert result == {}

    def test_get_perception_modifiers(self):
        """Test get_perception_modifiers returns correct data."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        modifiers = loader.get_perception_modifiers("goblin")
        assert modifiers["sight_range"] == 6.0
        assert modifiers["hearing_range"] == 14.0
        assert modifiers["darkvision"] is False

    def test_get_power_offsets(self):
        """Test get_power_offsets returns correct data."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        offsets = loader.get_power_offsets("goblin")
        assert offsets["melee_strength"] == 2.0
        assert offsets["melee_precision"] == 1.0

    def test_get_skill_offsets(self):
        """Test get_skill_offsets returns correct data."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        offsets = loader.get_skill_offsets("goblin")
        assert offsets["sneakiness"] == 2.0
        assert offsets["intimidation"] == 1.0

    def test_get_behavior_catalog_name(self):
        """Test get_behavior_catalog_name returns correct catalog."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        assert loader.get_behavior_catalog_name("goblin") == "goblin"
        assert loader.get_behavior_catalog_name("goblin_king") == "goblin_king"
        assert loader.get_behavior_catalog_name("wolf") == "wolf"

    def test_get_default_role(self):
        """Test get_default_role returns correct role."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        assert loader.get_default_role("goblin") == "minion"
        assert loader.get_default_role("goblin_king") == "leader"
        assert loader.get_default_role("spider") == "worker"

    def test_get_base_loyalty(self):
        """Test get_base_loyalty returns correct value."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        assert loader.get_base_loyalty("goblin") == 0.5
        assert loader.get_base_loyalty("goblin_king") == 0.5
        assert loader.get_base_loyalty("spider") == 1.0
        assert loader.get_base_loyalty("lich") == 1.0

    def test_is_leader(self):
        """Test is_leader returns correct boolean."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        assert loader.is_leader("goblin_king") is True
        assert loader.is_leader("lich") is True
        assert loader.is_leader("goblin") is False
        assert loader.is_leader("wolf") is False

    def test_get_all_structure_types(self):
        """Test get_all_structure_types returns all types."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        types = loader.get_all_structure_types()
        assert "goblin_kingdom" in types
        assert "wolf_pack" in types
        assert "spider_hive" in types
        assert "mercenary_band" in types
        assert "undead_court" in types
        assert "merchant_guild" in types

    def test_loyalty_config_values(self):
        """Test loyalty config values are correct."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        loyalty = loader.get_loyalty_config()
        assert loyalty["min_value"] == 0.0
        assert loyalty["max_value"] == 1.0
        assert loyalty["desertion_threshold"] == 0.1
        assert loyalty["betrayal_threshold"] == 0.05
        assert loyalty["fanatic_threshold"] == 0.9
        assert loyalty["gift_loyalty_per_gold"] == 0.01
        assert loyalty["combat_alongside_boost"] == 0.02
        assert loyalty["leader_fled_penalty"] == -0.15
        assert loyalty["promotion_boost"] == 0.2
        assert loyalty["order_boost"] == 0.01
        assert loyalty["no_share_penalty"] == -0.02

    def test_get_social_structure(self):
        """Test get_social_structure returns correct data."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        structure = loader.get_social_structure("goblin_kingdom")
        assert structure["display_name"] == "Goblin Kingdom"
        assert structure["leader_type"] == "goblin_king"
        assert "goblin" in structure["member_types"]
        assert structure["loyalty_sensitive"] is True
        assert structure["wealth_driven"] is True

    def test_get_mob_types(self):
        """Test get_mob_types returns all mob types."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        mob_types = loader.get_mob_types()
        assert "goblin" in mob_types
        assert "goblin_king" in mob_types
        assert "wolf" in mob_types
        assert "spider" in mob_types
        assert "bat" in mob_types
        assert "mercenary" in mob_types
        assert "undead" in mob_types
        assert "lich" in mob_types

    def test_get_social_structures(self):
        """Test get_social_structures returns all structures."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        structures = loader.get_social_structures()
        assert "goblin_kingdom" in structures
        assert "wolf_pack" in structures
        assert "spider_hive" in structures

    def test_get_perception_config(self):
        """Test get_perception_config returns correct values."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        perception = loader.get_perception_config()
        assert perception["default_sight_range"] == 8.0
        assert perception["default_hearing_range"] == 8.0
        assert perception["memory_duration_ticks"] == 300
        assert perception["recalc_interval_ticks"] == 1

    def test_get_behavior_config(self):
        """Test get_behavior_config returns correct values."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        behavior = loader.get_behavior_config()
        assert behavior["default_evaluation_interval"] == 1
        assert behavior["max_script_depth"] == 5
        assert behavior["max_children_per_node"] == 10
        assert behavior["default_timeout_ms"] == 5000

    def test_get_structure_config(self):
        """Test get_structure_config returns correct data."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        structure = loader.get_structure_config("wolf_pack")
        assert structure["display_name"] == "Wolf Pack"
        assert structure["leader_type"] == "wolf"
        assert structure["strength_based"] is True

    def test_bat_perception_has_echolocation(self):
        """Test bat has echolocation and darkvision."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        perception = loader.get_perception_modifiers("bat")
        assert perception["echolocation_range"] == 14.0
        assert perception["darkvision"] is True

    def test_spider_has_vibration_sense(self):
        """Test spider has vibration sense and ignores walls."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        perception = loader.get_perception_modifiers("spider")
        assert perception["vibration_range"] == 10.0
        assert perception["ignore_walls_vibration"] is True

    def test_lich_has_see_invisible(self):
        """Test lich has see_invisible ability."""
        loader = EntityAIConfigLoader("config/entity_ai.yaml")
        perception = loader.get_perception_modifiers("lich")
        assert perception["see_invisible"] is True
        assert perception["magic_sense_range"] == 15.0