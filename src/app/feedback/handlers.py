"""Feedback handlers with exact weight deltas from PRD Section 10.6.

Each handler computes a weight delta for the article's domain.
"""

from dataclasses import dataclass

from src.app.core.constants import FeedbackType


@dataclass
class WeightDelta:
    domain_id: str
    weight_change: float  # +/- change to apply
    depth_shift: int  # -1, 0, or +1 (shift toward L1/L3)
    block_domain: bool = False


# PRD Section 10.6 weight deltas
_WEIGHT_DELTAS: dict[str, float] = {
    FeedbackType.THUMBS_UP: +0.05,
    FeedbackType.THUMBS_DOWN: -0.05,
    FeedbackType.MORE_LIKE_THIS: +0.05,
    FeedbackType.LESS_OF_THIS: -0.05,
    FeedbackType.NOT_RELEVANT: -0.10,
    FeedbackType.NEVER_SHOW_DOMAIN: 0.0,  # Handled as block
}


def compute_delta(
    feedback_type: str, article_domain: str, value: float | None = None
) -> WeightDelta:
    """Compute the preference weight delta for a feedback action."""

    if feedback_type == FeedbackType.NEVER_SHOW_DOMAIN:
        return WeightDelta(
            domain_id=article_domain,
            weight_change=0.0,
            depth_shift=0,
            block_domain=True,
        )

    if feedback_type == FeedbackType.TOO_TECHNICAL:
        return WeightDelta(
            domain_id=article_domain,
            weight_change=0.0,
            depth_shift=-1,  # Shift toward simpler (L1/L2)
        )

    if feedback_type == FeedbackType.TOO_BASIC:
        return WeightDelta(
            domain_id=article_domain,
            weight_change=0.0,
            depth_shift=+1,  # Shift toward deeper (L2/L3)
        )

    if feedback_type == FeedbackType.STAR_RATING and value is not None:
        # PRD: (rating - 3) * 0.03
        return WeightDelta(
            domain_id=article_domain,
            weight_change=(value - 3) * 0.03,
            depth_shift=0,
        )

    # Standard weight delta
    weight_change = _WEIGHT_DELTAS.get(feedback_type, 0.0)
    return WeightDelta(
        domain_id=article_domain,
        weight_change=weight_change,
        depth_shift=0,
    )
