from pydantic import BaseModel
from .constants import SUPPORTED_LANGUAGES, PYTHON, MELLUM
from typing import Literal
import os
from enum import Enum

class BaseConfig(BaseModel):
    language: Literal[SUPPORTED_LANGUAGES] = os.getenv('LANGUAGE', PYTHON)
    stage: str = os.getenv('STAGE', 'practice')
    data_root: str = os.getenv('DATA_ROOT', '/data')
    samples_root: str = os.getenv('SAMPLES_ROOT', '/samples')
    predictions_root: str = os.getenv('PREDICTIONS_ROOT', '/predictions')


class PreprocessorConfig(BaseConfig):
    """
    Configuration class for the preprocessor.
    """
    use_tokenizer: bool = True
    model_name: str = os.getenv('EVAL_MODEL_NAME', MELLUM)
    

    def __repr__(self):
        return f"PreprocessorConfig(language={self.language}, model_name={self.model_name}, stage={self.stage}, use_tokenizer={self.use_tokenizer}, data_root={self.data_root}, samples_root={self.samples_root})"
    
class PostProcessorConfig(PreprocessorConfig):
    def __repr__(self):
        return f"PostProcessorConfig(language={self.language}, model_name={self.model_name}, stage={self.stage}, use_tokenizer={self.use_tokenizer}, data_root={self.data_root}, samples_root={self.samples_root})"


