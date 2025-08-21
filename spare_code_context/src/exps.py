from runner import Runner, Preprocessor, PreprocessorConfig, ZoektQueryGenerator, ZoektSearchRequester, PostProcessor, QueryPoint, QueryGeneratorConfig, SearchConfig, PostProcessorConfig
from typing import List, Dict
import os
import jsonlines

from logging import getLogger

logger = getLogger(__name__)
class ExperimentRunner(Runner):

    def __init__(self, config: PreprocessorConfig, query_generator_config: QueryGeneratorConfig, search_config: SearchConfig, post_processor_config: PostProcessorConfig):
        super().__init__(config, query_generator_config, search_config, post_processor_config)
        self.QUERY_DESCRIPTIONS = {
            "functions_classes_naive": "functions_classes_naive.jsonl",
            "functions_classes_or": "functions_classes_or.jsonl", 
            "functions_classes_top5": "functions_classes_top5.jsonl",
            "functions_classes_top4": "functions_classes_top4.jsonl",
            "functions_classes_top3": "functions_classes_top3.jsonl",
            "functions_classes_regex": "functions_classes_regex.jsonl",
            "navigation_naive": "navigation_naive.jsonl",
            "navigation_unpacked": "navigation_unpacked.jsonl",
            "navigation_unpacked_or": "navigation_unpacked_or.jsonl",
            "navigation_unpacked_top5": "navigation_unpacked_top5.jsonl",
            "navigation_unpacked_top4": "navigation_unpacked_top4.jsonl",
            "navigation_unpacked_top3": "navigation_unpacked_top3.jsonl",
            "navigation_regex": "navigation_regex.jsonl",
            "identifiers_naive": "identifiers_naive.jsonl",
            "identifiers_or": "identifiers_or.jsonl",
            "identifiers_top5": "identifiers_top5.jsonl",
            "identifiers_top4": "identifiers_top4.jsonl",
            "identifiers_top3": "identifiers_top3.jsonl",
            "identifiers_regex": "identifiers_regex.jsonl"
        }

    def save_queries(self, queries: List[QueryPoint]) -> None:
        """
        Save queries to multiple JSONL files. Each file corresponds to a predefined query description.
        """
        # Fixed dictionary of all possible query descriptions
        
        
        # Create file paths
        base_dir = os.path.dirname(self.query_saved_file)
        query_files = {
            description: os.path.join(base_dir, filename)
            for description, filename in self.QUERY_DESCRIPTIONS.items()
        }
        
        # Initialize all files (open writers for each description)
        writers = {}
        for description, filepath in query_files.items():
            writers[description] = jsonlines.open(filepath, 'w')
        
        try:
            # Iterate through each completion point and query point pair
            for i, (query_point, completion_point) in enumerate(zip(queries, self.completion_points)):
                for description in self.QUERY_DESCRIPTIONS.keys():
                    # Get query for this description (empty string if not present)
                    # print(query_point)
                    query = query_point.get(description, "")
                    
                    # Create entry for this datapoint
                    query_entry = {
                        "datapoint_id": completion_point.id,
                        "repo": completion_point.repo,
                        "revision": completion_point.revision,
                        "query": query,
                    }
                    
                    # Write to the corresponding file
                    writers[description].write(query_entry)
        
        finally:
            # Close all writers
            for writer in writers.values():
                writer.close()
        
        # logger.info(sf"Queries saved to {len(query_files)} files:")
        for description, filepath in query_files.items():
            logger.info(f"  - {description}: {filepath}")

    def preprocess_and_generate_queries(self) -> None:
        """
        Preprocess the data points and generate queries.
        """
        processed_datapoints = [self.preprocess(dp) for dp in self.completion_points]
        queries = []
        queries.extend(self.generate_queries(dp) for dp in processed_datapoints)

        # Save the generated queries
        self.save_queries(queries)
        
        logger.info("Queries generated and saved successfully.")
        
    def load_saved_queries_and_find_all_common_datapoints(self) -> List[QueryPoint]:
        """
        Load saved queries and find all common data points between each types of queries.
        Returns a list of QueryPoint objects where each contains all query types for a datapoint.
        """
        logger = logging.getLogger(__name__)
        
        base_dir = os.path.dirname(self.query_saved_file)
        
        # Dictionary to store all queries by datapoint_id
        datapoint_queries: Dict[str, Dict[str, str]] = {}
        
        # Load queries from all files
        for description, filename in self.QUERY_DESCRIPTIONS.items():
            filepath = os.path.join(base_dir, filename)
            
            if not os.path.exists(filepath):
                logger.warning(f"Query file not found: {filepath}")
                continue
                
            try:
                with jsonlines.open(filepath, 'r') as reader:
                    for entry in reader:
                        datapoint_id = entry.get("datapoint_id")
                        query = entry.get("query", "")
                        
                        if datapoint_id not in datapoint_queries:
                            datapoint_queries[datapoint_id] = {}
                        
                        datapoint_queries[datapoint_id][description] = query
                        
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
                continue
        
        # Find datapoints that have queries in ALL query types (common datapoints)
        if not datapoint_queries:
            logger.warning("No queries loaded from files")
            return []
        
        # Get datapoint IDs that appear in all query types
        all_query_types = set(self.QUERY_DESCRIPTIONS.keys())
        common_datapoint_ids = []
        
        for datapoint_id, queries in datapoint_queries.items():
            available_query_types = set(queries.keys())
            if all_query_types.issubset(available_query_types):
                common_datapoint_ids.append(datapoint_id)
        
        logger.info(f"Found {len(common_datapoint_ids)} common datapoints out of {len(datapoint_queries)} total")
        
        # Create QueryPoint objects for common datapoints
        common_query_points = []
        for datapoint_id in sorted(common_datapoint_ids):  # Sort for consistent ordering
            query_candidates = datapoint_queries[datapoint_id]
            if not any([v == "" for k, v in query_candidates.items()]):
                query_point = QueryPoint(candidates=query_candidates)
                common_query_points.append(query_point)

        # Save common query points to a file
        common_query_file = os.path.join(self.query_generator.config.queries_root, "common_queries.jsonl")
        with jsonlines.open(common_query_file, 'w') as writer:
            for query_point in common_query_points:
                writer.write(query_point.dict())
        
        return common_query_points
  
if __name__ == "__main__":
    """
    Main entry point for running the experiment.
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize the experiment runner with configurations
    config = PreprocessorConfig()
    query_generator_config = QueryGeneratorConfig()
    search_config = SearchConfig()
    post_processor_config = PostProcessorConfig()
    
    runner = ExperimentRunner(config, query_generator_config, search_config, post_processor_config)
    
    # Save queries to multiple files
    runner.preprocess_and_generate_queries()
    
    # Load saved queries and find common datapoints
    common_query_points = runner.load_saved_queries_and_find_all_common_datapoints()