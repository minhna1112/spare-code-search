from pydantic import BaseModel
from .constants import SUPPORTED_LANGUAGES, PYTHON, MELLUM, FILE_SEP, NUM_CONTEXT_LINES
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
    top_k_file: int = 1
    top_k_matches: int = 5
    merge_overlapping: bool = True
    use_whole_prefix: bool = False
    use_whole_suffix: bool = False
    use_diff_prefix: bool = True
    use_diff_suffix: bool = True
    max_tokens: int = os.getenv('MAX_TOKENS', 8192) #8192 is from Mellum-4b-sft
    max_reserved_tokens: int = os.getenv('MAX_RESERVED_TOKENS', 512) # reserved tokens for the model to generate
    file_separator: str = os.getenv('FILE_SEPARATOR', FILE_SEP)
    num_context_lines: int = os.getenv('NUM_CONTEXT_LINES', NUM_CONTEXT_LINES)

    def __repr__(self):
        return f"PostProcessorConfig(language={self.language}, model_name={self.model_name}, stage={self.stage}, use_tokenizer={self.use_tokenizer}, data_root={self.data_root}, samples_root={self.samples_root})"


