
from transformers import AutoTokenizer
from utils import extract_diff, get_parser, code_to_tree, code_to_tokens, get_tokenizer_name_from_model
from configs.constants import SEPARATOR_COMMENT
from configs.base import PreprocessorConfig
from datapoint import DataPoint
from typing import Dict, Tuple
import os

from logging import getLogger

logger = getLogger(__name__)

class Preprocessor:
    def __init__(self, config: PreprocessorConfig)-> None:
        self.parser = get_parser(config.language)
        self.tokenizer_name = get_tokenizer_name_from_model(config.model_name, config.language)
        self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name) if config.use_tokenizer else None
        self.config = config

    def get_original_file_path(self, datapoint: DataPoint | Dict) -> str:
        """
        Get the original file path from the datapoint.
        """
        repo_path = os.path.join(self.config.data_root, f"repositories-{self.config.language}-{self.config.stage}", "-".join([datapoint["repo"].replace("/", "__"), datapoint['revision']]))
        file_path = repo_path + "/" + datapoint['path']
        logger.debug(f"Original file path: {file_path}")
        return file_path

    def get_original_code(self, datapoint: DataPoint | Dict) -> str:

        file_path = self.get_original_file_path(datapoint)
        with open(file_path, 'r') as file:
            content = file.read()
        return content

    @staticmethod
    def generate_incomplete_code(datapoint: DataPoint | Dict) -> str:
        """
        Generate the incomplete code from the datapoint.
        """
        datapoint = datapoint.dict() if isinstance(datapoint, DataPoint) else datapoint
        incomplete_code = SEPARATOR_COMMENT.join([datapoint['prefix'], datapoint['suffix']])
        return incomplete_code

    def generate_diff(self, datapoint: DataPoint | Dict) -> str:
        original_code = self.get_original_code(datapoint)
        incomplete_code = self.generate_incomplete_code(datapoint)
        diff = extract_diff(incomplete_code, original_code)
        return diff

    def detect_completion_point(self, datapoint: DataPoint | Dict) -> tuple[int, int]:
        """
        Detect the completion point by taking the end point of the prefix.
        """
        tree = self.parser.parse(bytes(datapoint["prefix"], "utf8"))
        # Find the end point of the prefix
        if not tree.root_node.children:
            return tree.root_node.end_point
        # The completion point is the end point of the last child node
        last_child = tree.root_node.children[-1]
        return last_child.end_point

    def detect_completion_point_in_diff(self, datapoint: DataPoint | Dict) -> tuple[int, int]:
        """
        Detect the completion point by taking the end point of the prefix.
        """
        diff = self.generate_diff(datapoint)
        diff_prefix, _ = self.extract_diff_prefix_and_suffix(diff)
        tree = self.parser.parse(bytes(diff_prefix, "utf8"))
        # Find the end point of the prefix
        if not tree.root_node.children:
            return tree.root_node.end_point
        # The completion point is the end point of the last child node
        last_child = tree.root_node.children[-1]
        return last_child.end_point

    def count_tokens(self, code: str | list[str]) -> int:
        """
        Count the number of tokens in the code.
        """
        if self.tokenizer:
            tokens = code_to_tokens(code, self.tokenizer)
            return len(tokens)
        return 0

    @staticmethod
    def extract_diff_prefix_and_suffix(diff: str) -> tuple[str, str]:
        """
        Separate the prefix and suffix from the diff.
        """
        splitted = diff.split(SEPARATOR_COMMENT)
        if len(splitted) < 2:
            return splitted[0], ""
        return splitted[0], splitted[1]
