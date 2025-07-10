"""Module for recency search strategy that finds recently modified files."""

from .. import BaseSearchStrategy, CompletionPoint

class RecencySearch(BaseSearchStrategy):
    """Search strategy that uses recently modified files"""
    
    def find_context_files(self, completion_point: CompletionPoint, repo_root: str) -> list[str]:
        """
        Find files that were modified in the same commit
        
        Args:
            completion_point: The CompletionPoint object containing information from JSONL
            repo_root: Root directory of the repository
            
        Returns:
            List of recently modified file paths, excluding the target file
        """
        # Filter out the target file from modified files
        return [
            path for path in completion_point.modified
            if path != completion_point.path
        ]
        
        return context_files
