from runner import Runner, Preprocessor, PreprocessorConfig, ZoektQueryGenerator, ZoektSearchRequester, PostProcessor, QueryPoint, QueryGeneratorConfig, SearchConfig, PostProcessorConfig
from typing import List, Dict
import os
import jsonlines
from tqdm import tqdm
from datapoint import DataPoint, Prediction

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
        
    def load_saved_queries_and_find_all_common_datapoints(self) -> List[QueryPoint]:
        """
        Load saved queries and find all common data points between each types of queries.
        Returns a list of QueryPoint objects where each contains all query types for a datapoint.
        """
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
                logger.error(f"Error reading {filepath}: {e}")
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

    def search_and_postprocess_from_common_queries(self) -> None:
        """
        Load common queries, perform searches for each query type, and save results to separate files.
        """
        # Load common queries
        common_query_file = os.path.join(self.query_generator.config.queries_root, "common_queries.jsonl")
        
        if not os.path.exists(common_query_file):
            logger.error(f"Common queries file not found: {common_query_file}")
            return
            
        common_query_points: List[QueryPoint] = []
        try:
            with jsonlines.open(common_query_file, 'r') as reader:
                for query_data in reader:
                    common_query_points.append(QueryPoint(**query_data))
        except Exception as e:
            logger.error(f"Error loading common queries: {e}")
            return
            
        logger.info(f"Loaded {len(common_query_points)} common query points")
        
        # Create result files for each query type
        results_dir = os.path.join(self.config.predictions_root, "query_type_results")
        os.makedirs(results_dir, exist_ok=True)
        
        result_files = {
            description: os.path.join(results_dir, f"results_{description}")
            for description in self.QUERY_DESCRIPTIONS.keys()
        }
        
        # Initialize writers for each query type
        result_writers = {}
        for description, filepath in result_files.items():
            result_writers[description] = jsonlines.open(filepath, 'w')
        
        try:
            # Process each query point
            for i, query_point in enumerate(tqdm(common_query_points, desc="Processing common queries")):
                # Get corresponding datapoint
                if i < len(self.completion_points):
                    datapoint = self.completion_points[i]
                    processed_datapoint = self.preprocess(datapoint)
                else:
                    logger.warning(f"No datapoint found for query point {i}")
                    continue
                
                # Process each query type separately
                for description in self.QUERY_DESCRIPTIONS.keys():
                    query_text = query_point.candidates.get(description, "")
                    
                    if not query_text:
                        # Save empty result for missing queries
                        result_entry = {
                            "datapoint_id": processed_datapoint.id,
                            "repo": processed_datapoint.repo,
                            "revision": processed_datapoint.revision,
                            "path": processed_datapoint.path,
                            "query_type": description,
                            "query": "",
                            "search_successful": False,
                            "context": "",
                            "prefix": processed_datapoint.prefix,
                            "suffix": processed_datapoint.suffix
                        }
                        result_writers[description].write(result_entry)
                        continue
                    
                    try:
                        # Create single-query QueryPoint for this specific query type
                        single_query_point = QueryPoint(candidates={description: query_text})
                        
                        # Perform search
                        search_results = self.search_requester.zoekt_search_on_query_point(single_query_point)
                        
                        # Post-process results
                        prediction = self.post_processor.postprocess(processed_datapoint, search_results)
                        
                        # Create result entry
                        result_entry = {
                            "datapoint_id": processed_datapoint.id,
                            "repo": processed_datapoint.repo,
                            "revision": processed_datapoint.revision,
                            "path": processed_datapoint.path,
                            "query_type": description,
                            "query": query_text,
                            "search_successful": True,
                            "context": prediction.context if hasattr(prediction, 'context') else prediction.get('context', ''),
                            "prefix": prediction.prefix if hasattr(prediction, 'prefix') else prediction.get('prefix', ''),
                            "suffix": prediction.suffix if hasattr(prediction, 'suffix') else prediction.get('suffix', ''),
                            "num_results": len(search_results.get('results', [])) if search_results else 0
                        }
                        
                        result_writers[description].write(result_entry)
                        
                    except Exception as e:
                        logger.error(f"Error processing query type {description} for datapoint {processed_datapoint.id}: {e}")
                        
                        # Save error result
                        result_entry = {
                            "datapoint_id": processed_datapoint.id,
                            "repo": processed_datapoint.repo,
                            "revision": processed_datapoint.revision,
                            "path": processed_datapoint.path,
                            "query_type": description,
                            "query": query_text,
                            "search_successful": False,
                            "error": str(e),
                            "context": "",
                            "prefix": processed_datapoint.prefix,
                            "suffix": processed_datapoint.suffix
                        }
                        result_writers[description].write(result_entry)
        
        finally:
            # Close all writers
            for writer in result_writers.values():
                writer.close()
        
        logger.info(f"Search and post-processing completed. Results saved to:")
        for description, filepath in result_files.items():
            logger.info(f"  - {description}: {filepath}")
        
        # Print statistics
        logger.info(f"Total successful searches: {self.search_requester.num_successful_searches}")
        logger.info(f"Total failed searches: {self.search_requester.num_failed_searches}")

    def analyze_query_type_performance(self) -> None:
        """
        Analyze the performance of different query types from the saved results.
        """
        results_dir = os.path.join(self.config.predictions_root, "query_type_results")
        
        if not os.path.exists(results_dir):
            logger.error(f"Results directory not found: {results_dir}")
            return
        
        performance_stats = {}
        
        for description in self.QUERY_DESCRIPTIONS.keys():
            result_file = os.path.join(results_dir, f"results_{description}")
            
            if not os.path.exists(result_file):
                logger.warning(f"Result file not found: {result_file}")
                continue
            
            stats = {
                "total_queries": 0,
                "successful_searches": 0,
                "non_empty_contexts": 0,
                "average_context_length": 0,
                "total_context_length": 0
            }
            
            try:
                with jsonlines.open(result_file, 'r') as reader:
                    for entry in reader:
                        stats["total_queries"] += 1
                        
                        if entry.get("search_successful", False):
                            stats["successful_searches"] += 1
                        
                        context = entry.get("context", "")
                        if context and context.strip():
                            stats["non_empty_contexts"] += 1
                            stats["total_context_length"] += len(context)
                
                if stats["non_empty_contexts"] > 0:
                    stats["average_context_length"] = stats["total_context_length"] / stats["non_empty_contexts"]
                
                performance_stats[description] = stats
                
            except Exception as e:
                logger.error(f"Error analyzing {result_file}: {e}")
        
        # Save performance analysis
        analysis_file = os.path.join(results_dir, "performance_analysis.jsonl")
        with jsonlines.open(analysis_file, 'w') as writer:
            for query_type, stats in performance_stats.items():
                analysis_entry = {
                    "query_type": query_type,
                    **stats,
                    "success_rate": stats["successful_searches"] / stats["total_queries"] if stats["total_queries"] > 0 else 0,
                    "context_rate": stats["non_empty_contexts"] / stats["total_queries"] if stats["total_queries"] > 0 else 0
                }
                writer.write(analysis_entry)
        
        logger.info(f"Performance analysis saved to: {analysis_file}")
        
        # Print summary
        logger.info("Query Type Performance Summary:")
        for query_type, stats in performance_stats.items():
            success_rate = stats["successful_searches"] / stats["total_queries"] if stats["total_queries"] > 0 else 0
            context_rate = stats["non_empty_contexts"] / stats["total_queries"] if stats["total_queries"] > 0 else 0
            logger.info(f"  {query_type}: {success_rate:.2%} success, {context_rate:.2%} with context, avg length: {stats['average_context_length']:.1f}")

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
    
    # Step 1: Save queries to multiple files
    runner.preprocess_and_generate_queries()
    
    # Step 2: Load saved queries and find common datapoints
    common_query_points = runner.load_saved_queries_and_find_all_common_datapoints()
    
    # Step 3: Search and post-process from common queries
    runner.search_and_postprocess_from_common_queries()
    
    # Step 4: Analyze performance of different query types
    runner.analyze_query_type_performance()