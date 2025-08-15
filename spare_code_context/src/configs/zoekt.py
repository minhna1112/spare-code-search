import sys; sys.path.append(".")
from configs.base import BaseConfig
from configs.constants import NUM_CONTEXT_LINES
from enum import Enum
import os

class IdentifiersExtractionStrategy(Enum):
    FUNCTIONS_AND_CLASSES = 'functions_and_classes'
    NAVIGATION_EXPRESSION = 'navigation_expression'
    ALL_IDENTIFIERS = 'all_identifiers'

class QueryReference(Enum):
    DIFF = 'diff'
    DIFF_PREFIX = 'diff_prefix'
    DIFF_SUFFIX = 'diff_suffix'
    DIFF_PREFIX_AND_SUFFIX = 'diff_prefix_and_suffix'
    
class QueryGeneratorConfig(BaseConfig):
    """
    Configuration class for the query generator.
    """
    query_reference: QueryReference = QueryReference.DIFF
    max_terms: int = 6
    use_temporal_context: bool = True
    case_sensitive: bool = True
    identifiers_extraction_strategy: IdentifiersExtractionStrategy = IdentifiersExtractionStrategy.FUNCTIONS_AND_CLASSES
    queries_root: str = os.path.join(os.getenv('QUERIES_ROOT', '/queries'))

    def __repr__(self):
        return f"QueryGeneratorConfig(query_reference={self.query_reference}, max_terms={self.max_terms}, use_temporal_context={self.use_temporal_context}, case_sensitive={self.case_sensitive}, identifiers_extraction_strategy={self.identifiers_extraction_strategy})"

class SearchConfig(BaseConfig):
    """
    Configuration class for search settings.
    """
    num_context_lines: int = os.getenv('NUM_CONTEXT_LINES', NUM_CONTEXT_LINES)
    max_results: int = os.getenv('MAX_RESULTS', 10)
    max_retries: int = os.getenv('MAX_RETRIES', 3)
    retry_delay: float = os.getenv('RETRY_DELAY', 0.2)
    zoekt_url: str = os.getenv('ZOEKT_URL', 'http://localhost:6070/api/search')
    max_candidates_used: int = os.getenv('MAX_CANDIDATES_USED', 10)
