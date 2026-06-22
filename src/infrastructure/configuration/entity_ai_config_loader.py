"""Entity AI configuration loader."""

import os
from typing import Any, Dict, Optional


class EntityAIConfigLoader:
    """Loads and provides access to entity AI configuration."""

    def __init__(self, config_path: str = "config/entity_ai.yaml"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.config_path):
            import yaml
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
        else:
            self.config = self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        return {
            "mob_types": {},
            "social_structures": {},
            "loyalty": {},
            "perception": {},
            "behavior": {},
        }

    def get_mob_type(self, mob_type: str) -> Dict[str, Any]:
        return self.config.get("mob_types", {}).get(mob_type, {})

    def get_mob_types(self) -> Dict[str, Any]:
        return self.config.get("mob_types", {})

    def get_social_structure(self, structure_type: str) -> Dict[str, Any]:
        return self.config.get("social_structures", {}).get(structure_type, {})

    def get_social_structures(self) -> Dict[str, Any]:
        return self.config.get("social_structures", {})

    def get_loyalty_config(self) -> Dict[str, Any]:
        return self.config.get("loyalty", {})

    def get_perception_config(self) -> Dict[str, Any]:
        return self.config.get("perception", {})

    def get_behavior_config(self) -> Dict[str, Any]:
        return self.config.get("behavior", {})

    def get_perception_modifiers(self, mob_type: str) -> Dict[str, Any]:
        mob = self.get_mob_type(mob_type)
        return mob.get("perception", {})

    def get_power_offsets(self, mob_type: str) -> Dict[str, float]:
        mob = self.get_mob_type(mob_type)
        return mob.get("power_offsets", {})

    def get_skill_offsets(self, mob_type: str) -> Dict[str, float]:
        mob = self.get_mob_type(mob_type)
        return mob.get("skill_offsets", {})

    def get_behavior_catalog_name(self, mob_type: str) -> str:
        mob = self.get_mob_type(mob_type)
        return mob.get("behavior_catalog", "default")

    def get_default_role(self, mob_type: str) -> str:
        mob = self.get_mob_type(mob_type)
        return mob.get("default_role", "minion")

    def get_base_loyalty(self, mob_type: str) -> float:
        mob = self.get_mob_type(mob_type)
        return mob.get("base_loyalty", 0.5)

    def is_leader(self, mob_type: str) -> bool:
        mob = self.get_mob_type(mob_type)
        return mob.get("is_leader", False)

    def get_structure_config(self, structure_type: str) -> Dict[str, Any]:
        return self.get_social_structure(structure_type)

    def get_all_structure_types(self) -> list:
        return list(self.config.get("social_structures", {}).keys())