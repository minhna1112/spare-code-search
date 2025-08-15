from configs.zoekt import QueryGeneratorConfig, QueryReference
from typing import List, Tuple, Dict
from tree_sitter import Node
from datapoint import DataPoint
from configs.constants import SEPARATOR_COMMENT
from utils import code_to_tree, handle_nodes_in_suffix, find_first_and_last_nodes, deduplicate_nodes, rank_nodes_by_distance, AdjustedNode

from zoekt_query_generator.symbols_extractor import FunctionAndClassExtractor, NavigationExpressionExtractor, WildIdentifierExtractor

class ZoektQueryGenerator:
    """
    Generates Zoekt queries based on the provided configuration.
    """

    def __init__(self, config: QueryGeneratorConfig):
        self.config = config
        self.function_and_class_extractor = FunctionAndClassExtractor(config.language)
        self.navigation_expression_extractor = NavigationExpressionExtractor(config.language)
        self.wild_identifier_extractor = WildIdentifierExtractor(config.language)

    def find_all_nodes(self, datapoint: DataPoint) -> List[Node | AdjustedNode]:
        """
        Find all relevant nodes in the given datapoint.
        """
        function_and_class_nodes, navigation_expression_nodes, wild_identifier_nodes = [], [], []
        diff_prefix, diff_suffix = datapoint.diff.split(SEPARATOR_COMMENT, 1)
        diff = datapoint.diff.replace(SEPARATOR_COMMENT, "")
        
        for code in [diff, diff_prefix]:
            function_and_class_nodes.extend(self.function_and_class_extractor.extract_symbols(code))
            navigation_expression_nodes.extend(self.navigation_expression_extractor.extract_symbols(code))
            wild_identifier_nodes.extend(self.wild_identifier_extractor.extract_symbols(code))
            
        # Handle suffix nodes
        function_and_class_nodes.extend(handle_nodes_in_suffix(function_and_class_nodes, datapoint.completion_point))
        navigation_expression_nodes.extend(handle_nodes_in_suffix(navigation_expression_nodes, datapoint.completion_point))
        wild_identifier_nodes.extend(handle_nodes_in_suffix(wild_identifier_nodes, datapoint.completion_point))

        # Deduplicate nodes
        function_and_class_nodes = deduplicate_nodes(function_and_class_nodes)
        navigation_expression_nodes = deduplicate_nodes(navigation_expression_nodes)
        wild_identifier_nodes = deduplicate_nodes(wild_identifier_nodes)

        return {
            "function_and_class_nodes": function_and_class_nodes,
            "navigation_expression_nodes": navigation_expression_nodes,
            "wild_identifier_nodes": wild_identifier_nodes
        }

    def process_function_and_class_nodes(self, function_and_class_nodes: List[Node | AdjustedNode], repo_name: str, completion_point: Tuple[int, int]) -> List[Tuple[str, str]]:
        candidates = []
        # rank nodes by distance to completion line
        if not function_and_class_nodes:
            return candidates
        function_and_class_nodes = rank_nodes_by_distance(function_and_class_nodes, 
                                                          completion_point[0])
        # filter to max terms
        function_and_class_nodes = function_and_class_nodes[:self.config.max_terms]
        
        # 1. Naive query with all functions/classes (ranked by distance)
        naive_query = " ".join(node.text.decode() for node in function_and_class_nodes)
        candidates.append((f"{naive_query} r:{repo_name}", "functions_classes_naive"))

        # 2. OR logic version
        or_query = " or ".join(node.text.decode() for node in function_and_class_nodes)
        candidates.append((f"{or_query} r:{repo_name}", "functions_classes_or"))

        # 3. Reduced terms variants
        for max_terms in [5, 4, 3]:
            if len(function_and_class_nodes) > max_terms:
                reduced_query = " ".join(node.text.decode() for node in function_and_class_nodes[:max_terms])
                candidates.append((f"{reduced_query} r:{repo_name}", f"functions_classes_top{max_terms}"))

        # 4. Regex query (first to last)
        if len(function_and_class_nodes) >= 2:
            first_func, last_func = find_first_and_last_nodes(function_and_class_nodes)
            regex_query = f"{first_func.text.decode()}.*{last_func.text.decode()}"
            candidates.append((f"{regex_query} r:{repo_name}", "functions_classes_regex"))

        return candidates

    def process_navigation_expressions_nodes(self, navigation_expressions: List[Node | AdjustedNode], repo_name: str, completion_point: Tuple[int, int]) -> List[Tuple[str, str]]:

        # rank nodes by distance to completion line
        if not navigation_expressions:
            return []
        navigation_expressions = rank_nodes_by_distance(navigation_expressions,
                                                        completion_point[0])
        first_expr, last_expr = find_first_and_last_nodes(navigation_expressions)
        # filter to max terms
        navigation_expressions = navigation_expressions[:self.config.max_terms]
        navigation_expressions_text = [node.text.decode() for node in navigation_expressions]
        # Process navigation expressions
        def handle_navigation_expression(expr: str) -> str:
            s = "".join(c if c.isalnum() else " " for c in expr)
            s = ".".join(s.strip().replace("\n", " ").replace("  ", " ").split())
            s = s.lower() if not self.config.case_sensitive else s
            return s
        
        processed_nav = [handle_navigation_expression(expr) for expr in navigation_expressions_text if expr.strip()]
        candidates = []
        # 1. Naive query with navigation expressions
        naive_nav_query = " ".join(processed_nav)
        candidates.append((f"{naive_nav_query} r:{repo_name}", "navigation_naive"))
            
        # 2. Unpacked navigation expressions
        unpacked_identifiers = []
        for expr in processed_nav:
            unpacked_identifiers.extend(expr.split("."))
        unpacked_identifiers = list(set(unpacked_identifiers))  # Remove duplicates
        
        if unpacked_identifiers:
            unpacked_query = " ".join(unpacked_identifiers[:self.config.max_terms])
            candidates.append((f"{unpacked_query} r:{repo_name}", "navigation_unpacked"))
            
            # 3. OR logic for unpacked
            or_unpacked_query = " or ".join(unpacked_identifiers[:self.config.max_terms])
            candidates.append((f"{or_unpacked_query} r:{repo_name}", "navigation_unpacked_or"))
            
            # 4. Reduced terms for unpacked
            for max_terms in [5, 4, 3]:
                if len(unpacked_identifiers) > max_terms:
                    reduced_unpacked = " ".join(unpacked_identifiers[:max_terms])
                    candidates.append((f"{reduced_unpacked} r:{repo_name}", f"navigation_unpacked_top{max_terms}"))
        
        # 5. Regex query for navigation
        if first_expr and last_expr:
            first_id = first_expr.text.decode().split(".")[0]
            last_id = last_expr.text.decode().split(".")[-1]
            nav_regex_query = f"{first_id}.*{last_id}"
            candidates.append((f"{nav_regex_query} r:{repo_name}", "navigation_regex"))
        return candidates

    def process_wild_identifiers(self, wild_identifiers: List[Node | AdjustedNode], 
                                 repo_name: str,
                                 completion_point: Tuple[int, int]) -> List[Tuple[str, str]]:
        candidates = []
        if not wild_identifiers:
            return []
        first_id, last_id = find_first_and_last_nodes(wild_identifiers)
        wild_identifiers = [node.text.decode() for node in wild_identifiers]
        # rank by occurrence
        wild_identifiers = sorted(set(wild_identifiers), key=wild_identifiers.count, reverse=True)
        ranked_identifiers = wild_identifiers[:self.config.max_terms]
        
        # 1. Naive query with all identifiers
        if ranked_identifiers:
            naive_id_query = " ".join(ranked_identifiers)
            candidates.append((f"{naive_id_query} r:{repo_name}", "identifiers_naive"))
            
            # 2. OR logic version
            or_id_query = " or ".join(ranked_identifiers)
            candidates.append((f"{or_id_query} r:{repo_name}", "identifiers_or"))
            
            # 3. Reduced terms variants
            for max_terms in [5, 4, 3]:
                if len(ranked_identifiers) > max_terms:
                    reduced_id_query = " ".join(ranked_identifiers[:max_terms])
                    candidates.append((f"{reduced_id_query} r:{repo_name}", f"identifiers_top{max_terms}"))
            
            # 4. Regex query
            if first_id and last_id:
                id_regex_query = f"{first_id.text.decode()}.*{last_id.text.decode()}"
                candidates.append((f"{id_regex_query} r:{repo_name}", "identifiers_regex"))
                
        return candidates


    def construct_query_candidates_from_datapoint(self, datapoint: DataPoint, 
                                                ) -> Dict:
        """
        Generate multiple query candidates based on the code snippet and configuration.
        Returns list of (query, description) tuples ordered by priority.
        NO FALLBACKS - only generates queries for the specified strategy.
        """
        queries = {}
        candidates = []
        # Temporal context adjustment
        repo_name = "-".join([datapoint.repo.replace("/", "__"), datapoint.revision])
        if self.config.use_temporal_context:
            repo_name = repo_name.split("-")[0]

        all_nodes = self.find_all_nodes(datapoint)
        candidates.extend(self.process_function_and_class_nodes(
            all_nodes["function_and_class_nodes"], repo_name, datapoint.completion_point))
        candidates.extend(self.process_navigation_expressions_nodes(
            all_nodes["navigation_expression_nodes"], repo_name, datapoint.completion_point))
        candidates.extend(self.process_wild_identifiers(
            all_nodes["wild_identifier_nodes"], repo_name, datapoint.completion_point))

        for query, description in candidates:
            queries[description] = query

        return queries

