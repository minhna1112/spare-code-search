import diff_match_patch
from tree_sitter import Parser, Node
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


def rank_nodes_by_distance(nodes: List[Node], completion_line: int) -> List[Node]:
    """
    Rank nodes based on their distance to the completion line.
    """
    return sorted(nodes, key=lambda node: abs(node.start_point[0] - completion_line))


def deduplicate_nodes(nodes: List[Node]) -> List[Node]:
    """
    Deduplicate nodes based on their text content.
    """
    seen = set()
    deduplicated = []
    for node in nodes:
        if node.text.decode() not in seen:
            seen.add(node.text.decode())
            deduplicated.append(node)
    return deduplicated


# def handle_nodes_in_suffix(nodes: List[Node], completion_point: Tuple[int, int]) -> List[Node]:
#     """
#     Incrementing the start and end points of nodes in the suffix by the completion point.
#     """
#     for node in nodes:
#         new_start_line, new_start_column = node.start_point[0], node.start_point[1]
#         new_start_line += completion_point[0]
#         new_start_column += completion_point[1]
#         new_end_line, new_end_column = node.end_point[0], node.end_point[1]
#         new_end_line += completion_point[0]
#         new_end_column += completion_point[1]
#         node.start_point = (new_start_line, new_start_column)
#         node.end_point = (new_end_line, new_end_column)
#     return nodes

def find_first_and_last_nodes(nodes: List[Node]) -> Tuple[Node, Node]:
    """
    Find the first and last nodes in the list.
    """
    if not nodes:
        return None, None
    first_node = min(nodes, key=lambda node: node.start_point)
    last_node = max(nodes, key=lambda node: node.end_point)
    return first_node, last_node


class AdjustedNode:
    """
    Wrapper class for tree_sitter.Node with adjusted position information.
    """
    def __init__(self, original_node: Node, start_offset: Tuple[int, int] = (0, 0)):
        self.original_node = original_node
        self.start_offset = start_offset
    
    @property
    def start_point(self) -> Tuple[int, int]:
        return (
            self.original_node.start_point[0] + self.start_offset[0],
            self.original_node.start_point[1] + self.start_offset[1]
        )
    
    @property
    def end_point(self) -> Tuple[int, int]:
        return (
            self.original_node.end_point[0] + self.start_offset[0],
            self.original_node.end_point[1] + self.start_offset[1]
        )
    
    @property
    def text(self):
        return self.original_node.text
    
    def __getattr__(self, name):
        # Delegate other attributes to the original node
        return getattr(self.original_node, name)

def handle_nodes_in_suffix(nodes: List[Node], completion_point: Tuple[int, int]) -> List[AdjustedNode]:
    """
    Create adjusted node wrappers for nodes in the suffix with completion point offset.
    """
    return [AdjustedNode(node, completion_point) for node in nodes]

def merge_overlapping_ranges(snippets):
    """
    Merge overlapping code snippets and return consolidated line ranges.
    
    Args:
        snippets: List of snippet dicts with 'LineStart' and 'LineEnd' fields
        
    Returns:
        List of merged ranges as (start_line, end_line) tuples
    """
    if not snippets:
        return []
    
    # Extract and sort ranges by start line
    ranges = [(s['start_line'], s['end_line']) for s in snippets]
    ranges.sort(key=lambda x: x[0])
    
    merged_ranges = []
    current_start, current_end = ranges[0]
    
    for start, end in ranges[1:]:
        # Check if current range overlaps or touches the next range
        if start <= current_end + 1:  # +1 to merge adjacent ranges too
            # Extend current range
            current_end = max(current_end, end)
        else:
            # No overlap, save current range and start new one
            merged_ranges.append((current_start, current_end))
            current_start, current_end = start, end
    
    # Don't forget the last range
    merged_ranges.append((current_start, current_end))
    
    return merged_ranges


def get_merged_snippets_from_file(snippets, file_lines):
    """
    Extract merged code snippets from original file.
    
    Args:
        snippets: List of snippet dicts
        file_lines: List of strings (lines from original file)
        
    Returns:
        List of merged code snippets as strings
    """
    merged_ranges = merge_overlapping_ranges(snippets)
    merged_snippets = []
    
    for start_line, end_line in merged_ranges:
        # Convert to 0-based indexing for Python list slicing
        snippet_lines = file_lines[start_line - 1:end_line]
        merged_snippets.append('\n'.join(snippet_lines))
    
    return merged_snippets
