from configs.base import PostProcessorConfig
class PostProcessor:
    def __init__(self, config: PostProcessorConfig) -> None:
        self.model_name = config.model_name
        self.language = config.language
        self.config = config

