import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.constants import DepthLevel
from src.app.feedback.handlers import WeightDelta
from src.app.models.user import User, UserDomainPreference

logger = logging.getLogger(__name__)

_DEPTH_ORDER = [DepthLevel.L1, DepthLevel.L2, DepthLevel.L3]


class PreferenceUpdater:
    """Applies weight deltas to user domain preferences.

    Clamps weights to [0.0, 1.0] and shifts depth within L1-L3.
    """

    async def apply(
        self, session: AsyncSession, user_id: str, delta: WeightDelta
    ) -> None:
        # Handle domain blocking
        if delta.block_domain:
            await self._block_domain(session, user_id, delta.domain_id)
            return

        # Find the domain preference
        stmt = select(UserDomainPreference).where(
            UserDomainPreference.user_id == user_id,
            UserDomainPreference.domain_id == delta.domain_id,
        )
        result = await session.execute(stmt)
        pref = result.scalar_one_or_none()

        if not pref:
            # Create an inferred preference if it doesn't exist
            pref = UserDomainPreference(
                user_id=user_id,
                domain_id=delta.domain_id,
                weight=0.5,
                depth_preference=DepthLevel.L2,
                is_explicit=False,
            )
            session.add(pref)

        # Apply weight change
        if delta.weight_change != 0:
            pref.weight = max(0.0, min(1.0, pref.weight + delta.weight_change))
            pref.is_explicit = False  # Mark as system-adjusted

        # Apply depth shift
        if delta.depth_shift != 0:
            current_idx = _DEPTH_ORDER.index(pref.depth_preference) if pref.depth_preference in _DEPTH_ORDER else 1
            new_idx = max(0, min(2, current_idx + delta.depth_shift))
            pref.depth_preference = _DEPTH_ORDER[new_idx]

        await session.flush()
        logger.info(
            "Updated preference for user %s, domain %s: weight=%.2f, depth=%s",
            user_id,
            delta.domain_id,
            pref.weight,
            pref.depth_preference,
        )

    async def _block_domain(
        self, session: AsyncSession, user_id: str, domain_id: str
    ) -> None:
        """Set domain weight to 0 and add to blocked_domains list."""
        # Update weight to 0
        stmt = select(UserDomainPreference).where(
            UserDomainPreference.user_id == user_id,
            UserDomainPreference.domain_id == domain_id,
        )
        result = await session.execute(stmt)
        pref = result.scalar_one_or_none()
        if pref:
            pref.weight = 0.0

        # Add to user's blocked_domains
        user = await session.get(User, user_id)
        if user:
            blocked = user.blocked_domains or []
            if domain_id not in blocked:
                user.blocked_domains = blocked + [domain_id]

        await session.flush()
        logger.info("Blocked domain %s for user %s", domain_id, user_id)
