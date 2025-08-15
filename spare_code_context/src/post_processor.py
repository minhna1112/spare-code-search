from configs.base import PostProcessorConfig
from configs.constants import SEPARATOR_COMMENT
import os
from preprocessor import DataPoint, Preprocessor
from utils import get_merged_snippets_from_file
class PostProcessor:
    def __init__(self, config: PostProcessorConfig, preprocessor: Preprocessor) -> None:
        self.config = config
        self.preprocessor = preprocessor

    def compose_context(self, file_name, content):
        return self.config.file_separator + file_name + "\n" + content

    def get_line_infos(self, line_matches):
        return [
            {
                'start_line': match['LineNumber'] - self.config.num_context_lines - 1,
                'end_line': match['LineNumber'] + self.config.num_context_lines,
            }
            for match in line_matches[:self.config.top_k_matches]
        ]

    def count_tokens(self, code: str | list[str], 
                     ) -> int:
        """
        Count the number of tokens in the code.
        """
        return self.preprocessor.count_tokens(code)
 
    def postprocess_search_results(
        self,
        search_results: dict,
        total_max_context_tokens: int = 4096,
    ) -> dict:
        """
        Postprocess the search results to extract relevant information.
        """
        if 'Result' not in search_results or 'Files' not in search_results['Result'] or search_results['Result']['FileCount'] == 0:
            print("No search results found or no files in the results.")
            return {"context": ""}

        max_context_tokens = total_max_context_tokens // self.config.top_k_file
        remaining_context_tokens = total_max_context_tokens
        files = search_results['Result']['Files']
        processed_contexts = []

        for file in files[:self.config.top_k_file]:
            file_path = os.path.join(self.config.data_root,f'repositories-{self.config.language}-{self.config.stage}',file['Repository'], file['FileName'])
            with open(file_path, 'r') as f:
                file_content = f.read()
            context_str = self.compose_context(file['FileName'], file_content)
            file_num_tokens = self.count_tokens(context_str)

            if file_num_tokens <= max_context_tokens and remaining_context_tokens - file_num_tokens >= 0:
                remaining_context_tokens -= file_num_tokens
                processed_contexts.append({"context": context_str})
                continue

            line_infos = self.get_line_infos(file['LineMatches'])
            lines = file_content.splitlines()

            if not self.config.merge_overlapping:
                for info in line_infos:
                    snippet = "\n".join(lines[info['start_line']-1:info['end_line']-1])
                    context_str = self.compose_context(file['FileName'], snippet)
                    num_tokens = self.count_tokens(context_str)
                    if num_tokens <= max_context_tokens and remaining_context_tokens - num_tokens >= 0:
                        remaining_context_tokens -= num_tokens
                        processed_contexts.append({"context": context_str})
            else:
                merged_snippets = get_merged_snippets_from_file(line_infos, lines)
                for snippet in merged_snippets:
                    context_str = self.compose_context(file['FileName'], snippet)
                    num_tokens = self.count_tokens(context_str)
                    if num_tokens <= max_context_tokens and remaining_context_tokens - num_tokens >= 0:
                        remaining_context_tokens -= num_tokens
                        processed_contexts.append({"context": context_str})

        return {"context": "\n".join([c['context'] for c in processed_contexts])}

    def postprocess(self, datapoint: DataPoint,  search_results: dict) -> list[dict]:
        prefix = ""
        suffix = ""
        datapoint = datapoint.dict() if isinstance(datapoint, DataPoint) else datapoint
        if self.config.use_whole_prefix and self.config.use_whole_suffix:
            suffix = datapoint['suffix']
            prefix = datapoint['prefix']

        if self.config.use_diff_prefix and self.config.use_diff_suffix:
            prefix = datapoint['diff'].split(SEPARATOR_COMMENT)[0]
            suffix = datapoint['diff'].split(SEPARATOR_COMMENT)[1]

        num_token_from_prefix_and_suffix = self.count_tokens(prefix + suffix)
        possible_context_tokens = self.config.max_tokens - num_token_from_prefix_and_suffix - self.config.max_reserved_tokens # reserved tokens for the model to generate
        
        postprocessed_results = {"context": ""}
        postprocessed_results = self.postprocess_search_results(
            search_results, 
            total_max_context_tokens=possible_context_tokens
        )
        postprocessed_results['prefix'] = prefix
        postprocessed_results['suffix'] = suffix
        return postprocessed_results