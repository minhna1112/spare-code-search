from pydantic import BaseModel
from .constants import SUPPORTED_LANGUAGES, PYTHON, MELLUM
from typing import Literal
import os


class BaseConfig(BaseModel):
    language: Literal[SUPPORTED_LANGUAGES] = os.getenv('LANGUAGE', PYTHON)
    stage: str = os.getenv('STAGE', 'practice')
    data_root = os.getenv('DATA_ROOT', 'data')
    samples_root = os.getenv('SAMPLES_ROOT', 'samples')

    

class PreprocessorConfig(BaseConfig):
    """
    Configuration class for the preprocessor.
    """
    use_tokenizer: bool = True
    model_name: str = os.getenv('EVAL_MODEL_NAME', MELLUM)
    

    def __repr__(self):
        return f"PreprocessorConfig(language={self.language}, model_name={self.model_name}, stage={self.stage}, use_tokenizer={self.use_tokenizer}, data_root={self.data_root}, samples_root={self.samples_root})"

class SearchConfig:
    """
    Configuration class for search settings.
    """
    def __init__(self, language: str = "python", model_name: str = "mistralai/Codestral-22B-v0.1"):
        self.language = language
        self.model_name = model_name

    def __repr__(self):
        return f"SearchConfig(language={self.language}, model_name={self.model_name})"