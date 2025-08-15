from preprocessor import Preprocessor
from configs.base import PreprocessorConfig, PostProcessorConfig
from configs.zoekt import QueryGeneratorConfig
from datapoint import DataPoint, Prediction
from zoekt_query_generator.query_generator import ZoektQueryGenerator
from post_processor import PostProcessor
from logging import getLogger
import os
import jsonlines
from typing import List, Tuple, Dict, Any, Optional
from tqdm import tqdm
from context_searcher import QueryPoint, ZoektSearchRequester
from configs.zoekt import SearchConfig

logger = getLogger(__name__)


class Runner:
    """
    Main runner class to execute the preprocessor with the given configuration.
    """
    
    def __init__(self, 
                 preprocessor_config: PreprocessorConfig,
                 query_generator_config: QueryGeneratorConfig,
                 search_config: SearchConfig,
                 postprocessor_config: PostProcessorConfig) -> None:
        self.config: PreprocessorConfig = preprocessor_config
        self.preprocessor: Preprocessor = Preprocessor(preprocessor_config)
        self.query_generator: ZoektQueryGenerator = ZoektQueryGenerator(query_generator_config)
        self.search_requester: ZoektSearchRequester = ZoektSearchRequester(search_config)
        self.post_processor: PostProcessor = PostProcessor(postprocessor_config, self.preprocessor)
        self.completion_points_file: str = os.path.join(
            preprocessor_config.data_root, 
            f"{preprocessor_config.language}-{preprocessor_config.stage}.jsonl"
        )
        self.query_saved_file: str = os.path.join(
            query_generator_config.queries_root, 
            f"{preprocessor_config.language}-{preprocessor_config.stage}-queries.jsonl"
        )
        self.completion_points: List[DataPoint] = self.load_completion_points()
    
    def load_completion_points(self) -> List[DataPoint]:
        """
        Load completion points from the JSONL file.
        """
        completion_points: List[DataPoint] = []
        with jsonlines.open(self.completion_points_file, 'r') as reader:
            for datapoint_dict in reader:
                completion_points.append(DataPoint(**datapoint_dict))
        return completion_points
    
    def write_predictions(self, predictions: List[Prediction], output_file: str = "predictions.jsonl") -> None:
        """
        Write predictions to a JSONL file.
        """
        with jsonlines.open(output_file, 'w') as writer:
            for prediction in predictions:
                writer.write(prediction.dict()) if isinstance(prediction, Prediction) else writer.write(prediction)
        logger.info(f"Predictions written to {output_file}")
        
    def save_queries(self, queries: List[QueryPoint]) -> None:
        """
        Save generated queries to a JSONL file.
        """
        with jsonlines.open(self.query_saved_file, 'w') as writer:
            for query in queries:
                writer.write(query.dict())
        logger.info(f"Queries saved to {self.query_saved_file}")

    def preprocess(self, datapoint: DataPoint) -> DataPoint:
        """
        Run the preprocessor on the given datapoint.
        """
        original_code: str = self.preprocessor.get_original_code(datapoint.dict())
        incomplete_code: str = self.preprocessor.generate_incomplete_code(datapoint.dict())
        diff: str = self.preprocessor.generate_diff(datapoint.dict())
        completion_point: Tuple[int, int] = self.preprocessor.detect_completion_point(datapoint.dict())
        
        # Update datapoint with computed values
        datapoint.completion_point = completion_point
        datapoint.diff = diff
        return datapoint

    def generate_queries(self, datapoint: DataPoint) -> Dict[str, str]:
        """
        Generate query candidates from the given datapoint.
        """
        queries: Dict[str, str] = self.query_generator.construct_query_candidates_from_datapoint(datapoint)
        return queries

    def run(self, datapoint: DataPoint) -> Tuple[QueryPoint, Prediction]:
        """
        Run the complete pipeline on a single datapoint.
        
        Returns:
            Tuple containing the generated query point and the prediction result
        """
        # Preprocess the datapoint
        processed_datapoint: DataPoint = self.preprocess(datapoint)
        
        # Generate queries
        query_candidates: Dict[str, str] = self.generate_queries(processed_datapoint)
        # print(f"Generated queries: {query_candidates}")
        
        # Create query point
        query_point: QueryPoint = QueryPoint(candidates=query_candidates) if query_candidates else QueryPoint(candidates={})
        logger.info(f"Generated query point: {query_point}")
        
        # Search for context
        search_results: Dict[str, Any] = self.search_requester.zoekt_search_on_query_point(query_point)
        
        # Post-process search results
        prediction: Prediction = self.post_processor.postprocess(processed_datapoint, search_results)

        return query_point, prediction

    def run_all(self) -> None:
        """
        Run the complete pipeline on all completion points.
        """
        completion_points: List[DataPoint] = self.load_completion_points()
        all_queries: List[QueryPoint] = []
        all_predictions: List[Prediction] = []
        
        logger.info(f"Running pipeline on {len(completion_points)} completion points.")
        
        for datapoint in tqdm(completion_points, desc="Processing datapoints"):
            # try:
                query_point, prediction = self.run(datapoint)
                all_queries.append(query_point)
                all_predictions.append(prediction)
            # except Exception as e:
            #     logger.error(f"Error processing datapoint {datapoint.id}: {e}")
            #     # Add empty results for failed datapoints to maintain alignment
            #     all_queries.append(QueryPoint(candidates={}))
            #     all_predictions.append(Prediction())
        
        # Save results
        self.save_queries(all_queries)
        predictions_output_file: str = os.path.join(
            self.config.predictions_root, 
            f"{self.config.language}-{self.config.stage}-predictions.jsonl"
        )
        self.write_predictions(all_predictions, output_file=predictions_output_file)

    def search_from_saved_queries(self) -> None:
        """
        Load saved queries and perform searches on them.
        """
        query_points: List[QueryPoint] = []
        
        try:
            with jsonlines.open(self.query_saved_file, 'r') as f:
                logger.info(f"Loading queries from {self.query_saved_file}")
                for query_data in f:
                    if query_data is None or not query_data.get('candidates'):
                        logger.warning("Empty query point found, skipping.")
                        query_points.append(QueryPoint(candidates={}))
                        continue
                    query_points.append(QueryPoint(**query_data))
        except FileNotFoundError:
            logger.error(f"Query file not found: {self.query_saved_file}")
            return
        except Exception as e:
            logger.error(f"Error loading queries: {e}")
            return
        
        # Perform searches
        for query_point in tqdm(query_points, desc="Searching queries"):
            try:
                self.search_requester.zoekt_search_on_query_point(query_point)
            except Exception as e:
                logger.error(f"Error searching query point: {e}")
        
        logger.info(f"Total successful searches: {self.search_requester.num_successful_searches}")
        logger.info(f"Total failed searches: {self.search_requester.num_failed_searches}")


if __name__ == "__main__":
    # Load the configuration
    config: PreprocessorConfig = PreprocessorConfig()
    query_generator_config: QueryGeneratorConfig = QueryGeneratorConfig()
    search_config: SearchConfig = SearchConfig()
    post_processor_config: PostProcessorConfig = PostProcessorConfig()
    
    # Create a runner instance and run it
    runner: Runner = Runner(config, query_generator_config, search_config, post_processor_config)
    runner.run_all()
    # Alternative: runner.search_from_saved_queries()