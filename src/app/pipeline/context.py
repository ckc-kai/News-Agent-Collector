import uuid
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class PipelineContext:
    """Shared state for a single pipeline run."""

    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=datetime.utcnow)
    db_session: AsyncSession | None = None

    # Stats collected by each stage
    stats: dict[str, int] = field(default_factory=dict)
    # Errors collected (non-fatal)
    errors: list[dict] = field(default_factory=list)

    def record_stat(self, stage: str, key: str, value: int) -> None:
        self.stats[f"{stage}.{key}"] = value

    def record_error(self, stage: str, message: str, detail: str = "") -> None:
        self.errors.append({
            "stage": stage,
            "message": message,
            "detail": detail,
            "timestamp": datetime.utcnow().isoformat(),
        })
