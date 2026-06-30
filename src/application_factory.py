"""Application factory for creating game instances."""

from pathlib import Path
from typing import Optional

from src.infrastructure.configuration.config_loader import ConfigLoader
from src.infrastructure.external.cache_service import CacheService
from src.infrastructure.external.ollama_service import OllamaService
from src.infrastructure.persistence.highscores import HighScores
from src.infrastructure.persistence.save_system import SaveSystem
from src.infrastructure.repositories.entity_repository import EntityRepository
from src.infrastructure.repositories.item_repository import ItemRepository
from src.presentation.renderer import Renderer


class ApplicationFactory:
    """Factory for creating game application instances."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_loader = ConfigLoader(config_path)
        self._config = None
    
    def load_config(self) -> dict:
        """Load configuration."""
        if self._config is None:
            self._config = self.config_loader.load()
        return self._config
    
    def create_renderer(self) -> Renderer:
        """Create a renderer instance."""
        config = self.load_config()
        width = config.get('screen.width', 80)
        height = config.get('screen.height', 50)
        return Renderer(width, height)
    
    def create_ollama_service(self) -> OllamaService:
        """Create an Ollama service instance."""
        config = self.load_config()
        model = config.get('llm.model', 'qwen2.5-coder:7b-instruct')
        return OllamaService(model=model)
    
    def create_cache_service(self, cache_path: Optional[Path] = None) -> CacheService:
        """Create a cache service instance."""
        path = cache_path or Path("cache/content.db")
        return CacheService(path)
    
    def create_save_system(self, saves_path: Optional[Path] = None) -> SaveSystem:
        """Create a save system instance."""
        path = saves_path or Path("saves")
        return SaveSystem(path)
    
    def create_highscores(self, highscores_path: Optional[Path] = None) -> HighScores:
        """Create a high scores instance."""
        path = highscores_path or Path("highscores.json")
        return HighScores(path)
    
    def create_entity_repository(self) -> EntityRepository:
        """Create an entity repository instance."""
        return EntityRepository()
    
    def create_item_repository(self) -> ItemRepository:
        """Create an item repository instance."""
        return ItemRepository()

    def create_content_repository(self, conn=None, db_path=None) -> Any:
        """Create a ContentRepository instance.
        
        Args:
            conn: An existing sqlite3.Connection to reuse.
            db_path: Path to content.db (used only if conn is None, for backward compat).
        """
        from src.infrastructure.repositories.content_repository import ContentRepository
        if conn:
            return ContentRepository(conn)
        # Fallback: open own connection (not recommended for production)
        import sqlite3
        path = db_path or Path("cache/content.db")
        conn = sqlite3.connect(str(path), check_same_thread=False)
        return ContentRepository(conn)