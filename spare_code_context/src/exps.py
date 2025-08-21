from runner import Runner, Preprocessor, PreprocessorConfig, ZoektQueryGenerator, ZoektSearchRequester, PostProcessor, QueryPoint, QueryGeneratorConfig, SearchConfig, PostProcessorConfig
from typing import List, Dict
import os
import jsonlines
class ExperimentRunner(Runner):

    def __init__(self, config: PreprocessorConfig, query_generator_config: QueryGeneratorConfig, search_config: SearchConfig, post_processor_config: PostProcessorConfig):
        super().__init__(config, query_generator_config, search_config, post_processor_config)

    def save_queries(self, queries: List[QueryPoint]) -> None:
        """
        Save queries to multiple JSONL files. Each file corresponds to a predefined query description.
        """
        # Fixed dictionary of all possible query descriptions
        QUERY_DESCRIPTIONS = {
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
        
        # Create file paths
        base_dir = os.path.dirname(self.query_saved_file)
        query_files = {
            description: os.path.join(base_dir, filename)
            for description, filename in QUERY_DESCRIPTIONS.items()
        }
        
        # Initialize all files (open writers for each description)
        writers = {}
        for description, filepath in query_files.items():
            writers[description] = jsonlines.open(filepath, 'w')
        
        try:
            # Iterate through each completion point and query point pair
            for i, (query_point, completion_point) in enumerate(zip(queries, self.completion_points)):
                for description in QUERY_DESCRIPTIONS.keys():
                    # Get query for this description (empty string if not present)
                    print(query_point)
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
        
        logger.info(f"Queries saved to {len(query_files)} files:")
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