"""Module for hybrid search strategy that combines locality and recency."""

from .. import BaseSearchStrategy, CompletionPoint
from ..locality import LocalSearch
from ..recency import RecencySearch

class HybridSearch(BaseSearchStrategy):
    """Search strategy that combines local and recency strategies"""
    
    def __init__(self) -> None:
        self.local_strategy = LocalSearch()
        self.recency_strategy = RecencySearch()
    
    def find_context_files(self, completion_point: CompletionPoint, repo_root: str) -> list[str]:
        """
        Find files that are both in the same directory AND were modified recently
        
        Args:
            completion_point: The CompletionPoint object containing information from JSONL
            repo_root: Root directory of the repository
            
        Returns:
            List of file paths that satisfy both locality and recency criteria
        """
        # Get files from both strategies
        local_files = set(self.local_strategy.find_context_files(completion_point, repo_root))
        recent_files = set(self.recency_strategy.find_context_files(completion_point, repo_root))
        
        # Try to get the intersection first
        intersection = local_files.intersection(recent_files)
        
        # If intersection is empty, fallback to recent files
        return list(intersection) if intersection else list(recent_files)
