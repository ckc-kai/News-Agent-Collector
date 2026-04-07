import logging
from datetime import datetime

from src.app.pipeline.base import PipelineStage
from src.app.pipeline.context import PipelineContext
from src.app.schemas.article import NormalizedArticle

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Runs pipeline stages sequentially, collecting stats and handling errors."""

    def __init__(self):
        self._stages: list[PipelineStage] = []

    def add_stage(self, stage: PipelineStage) -> "PipelineOrchestrator":
        self._stages.append(stage)
        return self

    async def run(
        self, articles: list[NormalizedArticle], context: PipelineContext | None = None
    ) -> list[NormalizedArticle]:
        context = context or PipelineContext()
        logger.info(
            "Pipeline run %s started with %d articles and %d stages",
            context.run_id,
            len(articles),
            len(self._stages),
        )

        result = articles
        for stage in self._stages:
            stage_start = datetime.utcnow()
            input_count = len(result)

            try:
                result = await stage.process(result, context)
            except Exception as e:
                context.record_error(stage.name, str(e))
                logger.exception("Pipeline stage %s failed", stage.name)
                # Continue with what we have rather than aborting
                continue

            elapsed = (datetime.utcnow() - stage_start).total_seconds()
            context.record_stat(stage.name, "input_count", input_count)
            context.record_stat(stage.name, "output_count", len(result))
            logger.info(
                "Stage [%s]: %d → %d articles (%.2fs)",
                stage.name,
                input_count,
                len(result),
                elapsed,
            )

        logger.info(
            "Pipeline run %s completed: %d articles, %d errors",
            context.run_id,
            len(result),
            len(context.errors),
        )
        return result
