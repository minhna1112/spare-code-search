"""Module for local search strategy that finds files in the same directory."""

import os
from .. import BaseSearchStrategy, CompletionPoint

class LocalSearch(BaseSearchStrategy):
    """Search strategy that finds files in the same directory as the target file"""
    
    def find_context_files(self, completion_point: CompletionPoint, repo_root: str) -> list[str]:
        """
        Find all files that are in the same subdirectory as the target file
        
        Args:
            completion_point: The CompletionPoint object containing information from JSONL
            repo_root: Root directory of the repository
            
        Returns:
            List of file paths in the same directory
        """
        # Get the directory of the target file
        target_dir = os.path.dirname(completion_point.path)
        target_dir_path = os.path.join(repo_root, target_dir)
        
        # Find all files in the same directory
        context_files = []
        if os.path.exists(target_dir_path):
            for file in os.listdir(target_dir_path):
                file_path = os.path.join(target_dir, file)
                # Skip directories and the target file itself
                if not os.path.isdir(os.path.join(repo_root, file_path)) and file_path != completion_point.path:
                    context_files.append(file_path)
                    
        return context_files
