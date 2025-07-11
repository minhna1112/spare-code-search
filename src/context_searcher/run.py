import argparse

from .locality import LocalSearch
from .recency import RecencySearch
from .similarity import SimilaritySearch
import jsonlines
import os
from tqdm import tqdm
from . import ContextSearcher,  FILE_COMPOSE_FORMAT, FILE_SEP_SYMBOL, trim_prefix, trim_suffix
# Set up argument parser
parser = argparse.ArgumentParser(description="Run context search experiments")
parser.add_argument("--stage", type=str, default="practice", help="Stage of the project")
parser.add_argument("--lang", type=str, default="kotlin", help="Programming language")
parser.add_argument("--strategy", type=str, default="local",
                    choices=["local", "recent", "similarity"],
                    help="Context search strategy to use")
parser.add_argument("--trim-prefix", action="store_true",
                    help="Trim the prefix to MAX_LINES")
parser.add_argument("--trim-suffix", action="store_true",
                    help="Trim the suffix to MAX_LINES")

args = parser.parse_args()

# Select the appropriate strategy
if args.strategy == "local":
    strategy = LocalSearch()
elif args.strategy == "recent":
    strategy = RecencySearch()
else:  # similarity
    strategy = SimilaritySearch()

# Initialize the context searcher with the selected strategy
searcher = ContextSearcher(
    strategy=strategy,
    stage=args.stage,
    language=args.lang
)

# Process all completion points
completion_points = searcher.get_all_completion_points()
for point in tqdm(completion_points, desc="Processing completion points"):
    # Get repository root based on the archive name
    repo_root = os.path.join(
        "data",
        f"repositories-{args.lang}-{args.stage}",
        point.archive.replace(".zip", "")
    )
    
    # Find context files using the selected strategy
    context_files = searcher.search(point, repo_root)
    
    # Apply trimming if requested
    if args.trim_prefix:
        point.prefix = trim_prefix(point.prefix)
    if args.trim_suffix:
        point.suffix = trim_suffix(point.suffix)
    
    def process_file(file_path: str) -> str | None:
        """Process a single file and return its formatted content"""
        try:
            with open(os.path.join(repo_root, file_path), 'r', encoding='utf-8') as f:
                content = f.read()
                return FILE_COMPOSE_FORMAT.format(
                    file_sep=FILE_SEP_SYMBOL,
                    file_name=file_path,
                    file_content=content
                )
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    # Process all found files
    contexts = [
        ctx for ctx in (process_file(file_path) for file_path in context_files)
        if ctx is not None
    ]
    
    # Save prediction to file
    prediction = {
        "context": "".join(contexts)
    }
    
    predictions_file = os.path.join(
        "predictions",
        f"{args.lang}-{args.stage}-{args.strategy}.jsonl"
    )
    os.makedirs(os.path.dirname(predictions_file), exist_ok=True)
    with jsonlines.open(predictions_file, mode='a') as writer:
        writer.write(prediction)