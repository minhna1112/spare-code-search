from tree_sitter import Node
from typing import List, Tuple, Union
from tree_sitter_languages import get_language, get_parser

this_folder_path = __file__.rsplit('/', 1)[0] if '/' in __file__ else __file__.rsplit('\\', 1)[0]

class SymbolExtractor:
    """
    Base class for extracting symbols from code snippets.
    """
    def __init__(self, language: str):
        self.language = language
        self.tree_sitter_query = ""

    def extract_symbols(self, code_snippet: str ) -> List[Node]:
        raise NotImplementedError("Subclasses should implement this method.")

class NavigationExpressionExtractor(SymbolExtractor):
    """
    Extracts navigation expressions from code snippets.
    """
    def __init__(self, language: str):
        super().__init__(language)
        ts_query_file = f"{this_folder_path}/tree_sitter_schemes/{language}/navigation_expression.scm"
        with open(ts_query_file, 'r') as f:
            query_str = f.read()
        self.parser = get_parser(language)
        self.tree_sitter_query = get_language(language).query(query_str)

    def extract_symbols(self, code_snippet: str) -> List[Node]:
        if not code_snippet:
            return []

        tree = self.parser.parse(bytes(code_snippet, "utf8"))
        return [match[0] for match in self.tree_sitter_query.captures(tree.root_node)]

class WildIdentifierExtractor(SymbolExtractor):
    """
    Extracts wild identifiers from code snippets.
    """
    def __init__(self, language: str):
        self.language = language
        ts_query_file = f"{this_folder_path}/tree_sitter_schemes/{language}/wild_identifiers.scm"
        with open(ts_query_file, 'r') as f:
            query_str = f.read()
        self.parser = get_parser(language)
        self.tree_sitter_query = get_language(language).query(query_str)

    def extract_symbols(self, code_snippet: str) -> List[Node]:
        wild_identifiers = []
        if not code_snippet:
            return wild_identifiers
        tree = self.parser.parse(bytes(code_snippet, "utf8"))
        matches = self.tree_sitter_query.captures(tree.root_node)
        wild_identifiers = [match[0] for match in matches]
        return wild_identifiers


class FunctionAndClassExtractor:
    """
    Extracts function and class names from code snippets.
    """
    
    def __init__(self, language: str):
        self.language = language
        ts_query_file = f"{this_folder_path}/tree_sitter_schemes/{language}/function_and_class_names.scm"
        with open(ts_query_file, 'r') as f:
            query_str = f.read()
        self.parser = get_parser(language)
        self.tree_sitter_query = get_language(language).query(query_str)

    def extract_symbols(self, code_snippet: str ) -> List[Node]:
        if not code_snippet:
            return []

        tree = self.parser.parse(bytes(code_snippet, "utf8"))
        matches = self.tree_sitter_query.captures(tree.root_node)
        if not matches:
            return []
        # Extract the first capture group from each match
        function_and_class_names = [match[0] for match in matches]
        if not function_and_class_names:
            return []

        return function_and_class_names
