import diff_match_patch
from tree_sitter import Parser
import tree_sitter
from tree_sitter_languages import get_language, get_parser
from transformers import AutoTokenizer
from typing import List, Tuple
import os
from configs.constants import MELLUM

def extract_diff(incomplete_code, original_code) -> str:
    """
    Extract the diff from the original code.
    """
    dmp = diff_match_patch.diff_match_patch()
    # Create a diff between the original code and the incomplete code
    diffs = dmp.diff_lineMode(original_code, incomplete_code, deadline=None)
    # Convert the diffs to a single diff string
    diffs = "\n".join([diff[1] for diff in diffs if diff[0] != 0])
    return diffs

def extract_patch(original_code, incomplete_code) -> str:
    """
    Extract the patch from the original code.
    """
    dmp = diff_match_patch.diff_match_patch()
    
    diffs = dmp.patch_make(original_code, incomplete_code)
    # Convert the patches to a single patch string
    patches = dmp.patch_toText(diffs)
    return patches

def code_to_tree(code: str, parser: Parser) -> tree_sitter.Tree:
    """
    Convert code to a tree using tree-sitter.
    """
    tree = parser.parse(bytes(code, 'utf-8'))
    return tree

def code_to_tokens(code: str | list[str], tokenizer: AutoTokenizer) -> list[int]:
    """
    Convert code to tokens using the tokenizer
    """
    if isinstance(code, list):
        return [token for snippet in code for token in tokenizer.encode(snippet)]
    return tokenizer.encode(code)

def get_tokenizer_name_from_model(model_name: str, language: str) -> str:
    """
    Get the tokenizer name from the model name and language.
    """
    if model_name.startswith(MELLUM):
        """Handle Mellum model names"""
        return f"{model_name}{language}"
    return f"{model_name}"