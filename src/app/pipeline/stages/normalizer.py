import uuid

from src.app.core.utils import canonicalize_url, content_hash, clean_html
from src.app.pipeline.base import PipelineStage
from src.app.pipeline.context import PipelineContext
from src.app.schemas.article import RawArticle, NormalizedArticle


class NormalizerStage(PipelineStage):
    """Converts RawArticle objects to NormalizedArticle schema."""

    @property
    def name(self) -> str:
        return "normalizer"

    async def process(
        self, articles: list, context: PipelineContext
    ) -> list[NormalizedArticle]:
        normalized = []
        for article in articles:
            # Accept both RawArticle and NormalizedArticle (idempotent)
            if isinstance(article, NormalizedArticle):
                normalized.append(article)
                continue

            raw: RawArticle = article
            cleaned_content = clean_html(raw.raw_content) if raw.raw_content else ""

            normalized.append(
                NormalizedArticle(
                    id=str(uuid.uuid4()),
                    source_adapter=raw.source_adapter,
                    source_url=raw.source_url,
                    canonical_url=canonicalize_url(raw.source_url),
                    content_hash=content_hash(cleaned_content) if cleaned_content else None,
                    title=clean_html(raw.title).strip(),
                    authors=raw.authors,
                    published_at=raw.published_at,
                    raw_content=cleaned_content,
                    language=raw.language,
                    media_type=raw.media_type,
                    # domain, tags, importance, summaries are set by later stages
                )
            )

        context.record_stat(self.name, "normalized", len(normalized))
        return normalized
