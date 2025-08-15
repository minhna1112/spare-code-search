import sys; sys.path.append(".")
from configs.base import BaseConfig
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
    
