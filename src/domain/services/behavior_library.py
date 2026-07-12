"""Behavior Library for caching and reusing behavior scripts."""

import json
import os
from typing import Dict, Optional
from src.domain.value_objects.behavior_script import BehaviorScript


class BehaviorLibrary:
    """Library for selecting, authoring, and caching behavior scripts."""

    def __init__(
        self,
        content_repository=None,
        persist_path: str = "cache/behavior_library.json"
    ):
        self._repo = content_repository
        self._persist_path = persist_path
        self._entries: Dict[str, BehaviorScript] = self._load()

    def select_script(self, mob_type: str, situation: str) -> Optional[BehaviorScript]:
        """Select a script from the library.
        
        Args:
            mob_type: The mob type to select for
            situation: The situation context
            
        Returns:
            BehaviorScript if found, None otherwise
        """
        # Try exact mob_type match first, then "default"
        for key in (mob_type, "default"):
            if key in self._entries:
                return self._entries[key]
        return None

    def author_script(
        self,
        dm_agent,
        mob_type: str,
        situation: str
    ) -> Optional[BehaviorScript]:
        """Generate and store a new behavior script via LLM.
        
        Args:
            dm_agent: DungeonMasterAgent for LLM generation
            mob_type: The mob type
            situation: The situation context
            
        Returns:
            BehaviorScript if successful, None otherwise
        """
        # dm_agent generates a new BehaviorScript
        script = dm_agent.generate_behavior_script(
            entity_id=f"library_{mob_type}",
            mob_type=mob_type,
            perception=None,
            social_context=situation,
            valid_conditions=["can_see_player", "can_hear_player", "health_below"],
            valid_actions=["attack", "flee", "patrol", "wait"]
        )
        if script:
            self._entries[mob_type] = script
            self._persist()
        return script

    def get_fallback(self, mob_type: str) -> BehaviorScript:
        """Get a fallback script that never returns None.
        
        Uses BehaviorScriptService.create_default_script which is pure (no I/O).
        
        Args:
            mob_type: The mob type
            
        Returns:
            A valid BehaviorScript
        """
        from src.domain.services.behavior_script_service import BehaviorScriptService
        svc = BehaviorScriptService(action_dispatcher=None)
        return svc.create_default_script(mob_type, f"{mob_type}_fallback")

    def _load(self) -> Dict[str, BehaviorScript]:
        """Load entries from persist_path JSON file."""
        if not os.path.exists(self._persist_path):
            return {}
        try:
            with open(self._persist_path, "r") as f:
                data = json.load(f)
            entries = {}
            for key, script_data in data.items():
                # Reconstruct BehaviorScript from dict
                from src.domain.services.behavior_script_service import BehaviorScriptService
                svc = BehaviorScriptService(action_dispatcher=None)
                entries[key] = svc.parse_script_from_json(script_data)
            return entries
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _persist(self) -> None:
        """Write entries to persist_path JSON file."""
        os.makedirs(os.path.dirname(self._persist_path), exist_ok=True)
        data = {}
        for key, script in self._entries.items():
            data[key] = script.to_dict()
        with open(self._persist_path, "w") as f:
            json.dump(data, f, indent=2)