"""
Base query class for the application layer query pattern.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass


@dataclass
class QueryResult:
    """Result of a query execution."""
    success: bool
    data: Optional[Any] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    cached: bool = False


class BaseQuery(ABC):
    """
    Abstract base class for all game queries.
    
    Implements the Query pattern for retrieving game information.
    """
    
    def __init__(self, query_id: str):
        """
        Initialize the query.
        
        Args:
            query_id: Unique identifier for the query
        """
        self.query_id = query_id
        self.result: Optional[QueryResult] = None
        self.cache_enabled = True
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> QueryResult:
        """
        Execute the query.
        
        Args:
            *args: Query-specific arguments
            **kwargs: Query-specific keyword arguments
            
        Returns:
            QueryResult: The result of the query execution
        """
        pass
    
    def get_cached_result(self, *args, **kwargs) -> Optional[QueryResult]:
        """
        Get cached result if available.
        
        Args:
            *args: Query-specific arguments
            **kwargs: Query-specific keyword arguments
            
        Returns:
            Optional[QueryResult]: Cached result if available, None otherwise
        """
        if not self.cache_enabled:
            return None
        
        # Simple caching mechanism - in a real implementation, this would use a proper cache
        if self.result and self.result.success:
            return self.result
        
        return None
    
    def cache_result(self, result: QueryResult) -> None:
        """
        Cache the query result.
        
        Args:
            result: The query result to cache
        """
        if self.cache_enabled:
            self.result = result
    
    def clear_cache(self) -> None:
        """Clear the cached result."""
        self.result = None
    
    def set_cache_enabled(self, enabled: bool) -> None:
        """
        Enable or disable caching for this query.
        
        Args:
            enabled: True to enable caching, False to disable
        """
        self.cache_enabled = enabled