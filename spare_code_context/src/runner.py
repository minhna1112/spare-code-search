from preprocessor import Preprocessor
from configs.base import PreprocessorConfig
from datapoint import DataPoint, Prediction
from logging import getLogger
import os
import jsonlines
from typing import List
from tqdm import tqdm


logger = getLogger(__name__)



class Runner:
    """
    Main runner class to execute the preprocessor with the given configuration.
    """
    def __init__(self, preprocessor_config: PreprocessorConfig):
        self.config = preprocessor_config
        self.preprocessor = Preprocessor(preprocessor_config)
        self.completion_points_file = os.path.join(preprocessor_config.data_root, f"{preprocessor_config.language}-{preprocessor_config.stage}.jsonl")

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
    
    def run(self, datapoint: DataPoint):
        """
        Run the preprocessor on the given datapoint.
        """
        original_code = self.preprocessor.get_original_code(datapoint.dict())
        incomplete_code = self.preprocessor.generate_incomplete_code(datapoint.dict())
        diff = self.preprocessor.generate_diff(datapoint.dict())
        completion_point = self.preprocessor.detect_completion_point(datapoint.dict())

        output = {
            "original_code": original_code,
            "incomplete_code": incomplete_code,
            "diff": diff,
            "completion_point": completion_point
        }

        logger.info(f"Processed datapoint: {datapoint.id}")
        logger.debug(f"Output: {output}")

        return output
    
    
    def run_all(self):
        """
        Run the preprocessor on all completion points.
        """
        completion_points = self.load_completion_points()
        results = []
        logger.info(f"Running preprocessor on {len(completion_points)} completion points.")
        for datapoint in tqdm(completion_points):
            result = self.run(datapoint)
            results.append(result)
        
        predictions = []
        for result in tqdm(results):
            logger.debug(f"Result: {result}")
            prediction = Prediction(
                context = "a",
                prefix = "b",
                suffix = "c"
            )
            predictions.append(prediction)

        self.write_predictions(predictions, output_file=os.path.join(self.config.predictions_root, f"{self.config.language}-{self.config.stage}-predictions.jsonl"))


if __name__ == "__main__":
   
    # Load the configuration
    config = PreprocessorConfig()
    
    # Create a runner instance and run it
    runner = Runner(config)
    results = runner.run_all()
    
    