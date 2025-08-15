from preprocessor import Preprocessor
from configs.base import PreprocessorConfig
from configs.zoekt import QueryGeneratorConfig
from datapoint import DataPoint, Prediction
from zoekt_query_generator.query_generator import ZoektQueryGenerator
from logging import getLogger
import os
import jsonlines
from typing import List
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
                 search_config: SearchConfig = SearchConfig):
        self.config = preprocessor_config
        self.preprocessor = Preprocessor(preprocessor_config)
        self.query_generator = ZoektQueryGenerator(query_generator_config)
        self.search_requester = ZoektSearchRequester(search_config)
        self.completion_points_file = os.path.join(preprocessor_config.data_root, f"{preprocessor_config.language}-{preprocessor_config.stage}.jsonl")
        self.query_saved_file = os.path.join(query_generator_config.queries_root, f"{preprocessor_config.language}-{preprocessor_config.stage}-queries.jsonl")

    def load_completion_points(self) -> List[DataPoint]:
        """
        Load completion points from the JSONL file.
        """
        completion_points = []
        with jsonlines.open(self.completion_points_file, 'r') as reader:
            for datapoint in reader:
                completion_points.append(DataPoint(**datapoint))
        return completion_points
    
    def write_predictions(self, predictions: List[Prediction], output_file: str = "predictions.jsonl"):
        """
        Write predictions to a JSONL file.
        """
        with jsonlines.open(output_file, 'w') as writer:
            for prediction in predictions:
                writer.write(prediction.dict())
        logger.info(f"Predictions written to {output_file}")
        
    def save_queries(self, queries: List[str]):
        """
        Save generated queries to a JSONL file.
        """
        with jsonlines.open(self.query_saved_file, 'w') as writer:
            for query in queries:
                writer.write({"candidates": query})
        logger.info(f"Queries saved to {self.query_saved_file}")
    
    def run(self, datapoint: DataPoint):
        """
        Run the preprocessor on the given datapoint.
        """
        original_code = self.preprocessor.get_original_code(datapoint.dict())
        incomplete_code = self.preprocessor.generate_incomplete_code(datapoint.dict())
        diff = self.preprocessor.generate_diff(datapoint.dict())
        completion_point = self.preprocessor.detect_completion_point(datapoint.dict())
        datapoint.completion_point = completion_point
        datapoint.diff = diff

        queries = self.query_generator.construct_query_candidates_from_datapoint(datapoint)
        return queries
    
    
    def run_all(self):
        """
        Run the preprocessor on all completion points.
        """
        completion_points = self.load_completion_points()
        results = []
        queries = []
        logger.info(f"Running preprocessor on {len(completion_points)} completion points.")
        for datapoint in tqdm(completion_points):
            queries.append(self.run(datapoint))
            
        predictions = []

        self.write_predictions(predictions, output_file=os.path.join(self.config.predictions_root, f"{self.config.language}-{self.config.stage}-predictions.jsonl"))
        self.save_queries(queries)
        
    def search_all(self):
        query_points = []
        with jsonlines.open(self.query_saved_file, 'r') as f:
            logger.info(f"Loading queries from {self.query_saved_file}")
            for query_point in f:
                if query_point is None or not query_point.get('candidates'):
                    logger.warning("Empty query point found, skipping.")
                    query_points.append(QueryPoint(candidates={}))
                    continue
                query_points.append(QueryPoint(**query_point))
        for query_point in query_points:
            self.search_requester.zoekt_search_on_query_point(query_point)
        print(f"Total successful searches: {self.search_requester.num_successful_searches}")
        print(f"Total failed searches: {self.search_requester.num_failed_searches}")


if __name__ == "__main__":
   
    # Load the configuration
    config = PreprocessorConfig()
    query_generator_config = QueryGeneratorConfig()
    search_config = SearchConfig()
    # Create a runner instance and run it
    runner = Runner(config, query_generator_config, search_config)
    results = runner.run_all()
    results = runner.search_all()
    
