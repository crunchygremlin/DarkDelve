"""Dependency injection container."""

from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar

from src.application_factory import ApplicationFactory

T = TypeVar('T')


class DIContainer:
    """Simple dependency injection container."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self._factory = ApplicationFactory(config_path)
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
    
    def register_singleton(self, name: str, factory: Callable[[], Any]) -> None:
        """Register a singleton factory."""
        self._factories[name] = factory
    
    def register_instance(self, name: str, instance: Any) -> None:
        """Register an existing instance."""
        self._services[name] = instance
    
    def get(self, name: str) -> Any:
        """Get a service by name."""
        if name in self._services:
            return self._services[name]
        
        if name in self._factories:
            self._services[name] = self._factories[name]()
            return self._services[name]
        
        # Use factory defaults
        return self._create_from_factory(name)
    
    def _create_from_factory(self, name: str) -> Any:
        """Create a service from the application factory."""
        factory_methods = {
            'config': self._factory.load_config,
            'renderer': self._factory.create_renderer,
            'ollama': self._factory.create_ollama_service,
            'cache': self._factory.create_cache_service,
            'save_system': self._factory.create_save_system,
            'highscores': self._factory.create_highscores,
            'entity_repository': self._factory.create_entity_repository,
            'item_repository': self._factory.create_item_repository,
        }
        
        if name in factory_methods:
            return factory_methods[name]()
        
        raise KeyError(f"Unknown service: {name}")
    
    def has(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._services or name in self._factories


# Global container instance
_container: Optional[DIContainer] = None


def get_container(config_path: Optional[Path] = None) -> DIContainer:
    """Get the global container instance."""
    global _container
    if _container is None:
        _container = DIContainer(config_path)
    return _container