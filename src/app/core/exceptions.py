class NewsAgentError(Exception):
    """Base exception for all News Agent errors."""


class SourceError(NewsAgentError):
    """Raised when a source adapter encounters an error."""

    def __init__(self, source_name: str, message: str):
        self.source_name = source_name
        super().__init__(f"[{source_name}] {message}")


class SourceRateLimitError(SourceError):
    """Raised when a source's daily budget is exhausted."""


class SourceUnavailableError(SourceError):
    """Raised when a source fails health check or is unreachable."""


class PipelineError(NewsAgentError):
    """Raised when a pipeline stage fails."""

    def __init__(self, stage_name: str, message: str):
        self.stage_name = stage_name
        super().__init__(f"Pipeline stage [{stage_name}]: {message}")


class SummarizationError(NewsAgentError):
    """Raised when LLM summarization fails."""


class RecommendationError(NewsAgentError):
    """Raised when the recommendation engine fails."""


class UserNotFoundError(NewsAgentError):
    """Raised when a user is not found."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User not found: {user_id}")
