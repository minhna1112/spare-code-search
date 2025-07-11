"""Module for local search strategy that finds files in the same directory."""

import os
from .. import BaseSearchStrategy, CompletionPoint

class LocalSearch(BaseSearchStrategy):
    """Search strategy that finds files in the same directory as the target file"""
    
    def __init__(self, level: int = 0) -> None:
        """
        Initialize the LocalSearch strategy
        
        Args:
            level: The search level.
                  0: Same directory only (default)
                  -1: Parent directory and its subdirectories
                  -2: Grandparent directory and its subdirectories, etc.
        """
        super().__init__()
        self.level = level
    
    def find_context_files(self, completion_point: CompletionPoint, repo_root: str) -> list[str]:
        """
        Find files based on the configured search level
        
        Args:
            completion_point: The CompletionPoint object containing information from JSONL
            repo_root: Root directory of the repository
            
        Returns:
            List of file paths in the search scope based on level
        """
        target_path = completion_point.path
        
        # Get the directory path based on level
        current_dir = os.path.dirname(target_path)
        for _ in range(abs(self.level)):
            current_dir = os.path.dirname(current_dir)
            # Stop if we reach the root
            if not current_dir:
                break
                
        search_root = os.path.join(repo_root, current_dir if current_dir else '')
        
        # Find all files in the search scope
        context_files = []
        if os.path.exists(search_root):
            for dirpath, _, filenames in os.walk(search_root):
                for filename in filenames:
                    file_path = os.path.relpath(os.path.join(dirpath, filename), repo_root)
                    # Skip directories and the target file itself
                    if file_path != completion_point.path:
                        context_files.append(file_path)
                        
        return context_files
