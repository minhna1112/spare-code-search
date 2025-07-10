"""Module for similarity search strategy that finds similar files using BM25."""

import os
from rank_bm25 import BM25Okapi
from .. import BaseSearchStrategy, CompletionPoint

class SimilaritySearch(BaseSearchStrategy):
    """Search strategy that uses BM25 to find similar files based on content"""
    
    def _prepare_bm25_str(self, s: str) -> list[str]:
        """Prepare string for BM25 by converting to lowercase and splitting into tokens"""
        return "".join(c if c.isalnum() else " " for c in s.lower()).split()
    
    def find_context_files(self, completion_point: CompletionPoint, repo_root: str) -> list[str]:
        """
        Find files that are similar to the target file using BM25
        
        Args:
            completion_point: The CompletionPoint object containing information from JSONL
            repo_root: Root directory of the repository
            
        Returns:
            List of file paths sorted by similarity score
        """
        corpus = []
        file_paths = []
        
        # Walk through the repository
        for dirpath, _, filenames in os.walk(repo_root):
            for filename in filenames:
                file_path = os.path.relpath(os.path.join(dirpath, filename), repo_root)
                
                # Skip the target file
                if file_path == completion_point.path:
                    continue
                    
                try:
                    with open(os.path.join(repo_root, file_path), 'r', encoding='utf-8') as f:
                        content = f.read()
                        corpus.append(self._prepare_bm25_str(content))
                        file_paths.append(file_path)
                except Exception:
                    continue
        
        if not corpus:
            return []
            
        # Create query from prefix and suffix
        query = self._prepare_bm25_str(completion_point.prefix + " " + completion_point.suffix)
        
        # Calculate BM25 scores
        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(query)
        
        # Sort files by score and return paths
        scored_files = list(zip(scores, file_paths))
        # Sort by score in descending order
        scored_files.sort(reverse=True)
        
        return [file_path for _, file_path in scored_files]
