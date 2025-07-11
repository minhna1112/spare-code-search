"""Base module for context searching functionality."""

import os
import jsonlines
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import List

# Constants for file handling
FILE_SEP_SYMBOL = "<|file_sep|>"
FILE_COMPOSE_FORMAT = "{file_sep}{file_name}\n{file_content}"
MIN_LINES = 10
MAX_LINES = 10

class CompletionPoint(BaseModel):
    """Class to hold the completion point information from a JSONL entry"""
    id: str
    repo: str
    revision: str
    path: str
    modified: List[str]
    prefix: str
    suffix: str
    archive: str

class BaseSearchStrategy(ABC):
    """Abstract base class for all search strategies"""
    @abstractmethod
    def find_context_files(self, completion_point: CompletionPoint, repo_root: str) -> list[str]:
        """
        Find relevant files based on the search strategy
        
        Args:
            completion_point: The CompletionPoint object containing information from JSONL
            repo_root: Root directory of the repository
            
        Returns:
            List of file paths that are relevant according to the strategy
        """
        pass


def trim_prefix(prefix: str) -> str:
    """Trim prefix to MAX_LINES if it's longer"""
    prefix_lines = prefix.split("\n")
    if len(prefix_lines) > MAX_LINES:
        prefix = "\n".join(prefix_lines[-MAX_LINES:])
    return prefix

def trim_suffix(suffix: str) -> str:
    """Trim suffix to MAX_LINES if it's longer"""
    suffix_lines = suffix.split("\n")
    if len(suffix_lines) > MAX_LINES:
        suffix = "\n".join(suffix_lines[:MAX_LINES])
    return suffix

class ContextSearcher(object):
    """Main class to coordinate different search strategies"""
    def __init__(self, strategy: BaseSearchStrategy, stage: str = "practice",
                 language: str = "kotlin")->None:
        self.strategy = strategy
        self.stage = stage
        self.language = language
        self.trim_prefix = True
        self.trim_suffix = True
        self.completion_points_file = self._get_completion_points_file()
        
    def _get_completion_points_file(self) -> str:
        """Get the path to the completion points file"""
        return os.path.join("data", f"{self.language}-{self.stage}.jsonl")
    
    def get_all_completion_points(self) -> list[CompletionPoint]:
        """Read all completion points from the JSONL file"""
        completion_points = []
        with jsonlines.open(self.completion_points_file) as reader:
            for obj in reader:
                completion_points.append(CompletionPoint(**obj))
        return completion_points
    
    def search(self, completion_point: CompletionPoint, repo_root: str) -> list[str]:
        """
        Execute the search using the configured strategy
        
        Args:
            completion_point: The CompletionPoint object containing information from JSONL
            repo_root: Root directory of the repository
            
        Returns:
            List of file paths found by the strategy
        """
        return self.strategy.find_context_files(completion_point, repo_root)

    def set_strategy(self, strategy: BaseSearchStrategy) -> None:
        """Change the search strategy"""
        self.strategy = strategy