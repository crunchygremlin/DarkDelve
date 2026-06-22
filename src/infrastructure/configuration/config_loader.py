"""Configuration loading and management."""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from src.shared.exceptions.infrastructure_exceptions import ConfigurationException


class ConfigLoader:
    """Load and manage game configuration."""
    
    DEFAULT_CONFIG: Dict[str, Any] = {
        "screen": {"width": 80, "height": 50},
        "game": {"name": "DarkDelve", "version": "1.0.0"},
        "llm": {"model": "qwen2.5-coder:7b-instruct", "temperature": 0.7},
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from file or return defaults."""
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception as e:
                raise ConfigurationException(
                    f"Failed to load config: {e}",
                    {"path": str(self.config_path)}
                )
        else:
            self._config = self.DEFAULT_CONFIG.copy()
        
        # Merge with defaults
        self._merge_defaults()
        return self._config
    
    def _merge_defaults(self) -> None:
        """Merge loaded config with defaults."""
        for key, value in self.DEFAULT_CONFIG.items():
            if key not in self._config:
                self._config[key] = value
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in self._config[key]:
                        self._config[key][sub_key] = sub_value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def validate(self) -> bool:
        """Validate the configuration."""
        required_keys = ["screen", "game"]
        for key in required_keys:
            if key not in self._config:
                return False
        return True