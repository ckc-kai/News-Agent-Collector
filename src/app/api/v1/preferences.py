from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.repositories.user import UserRepository
from src.app.dependencies import get_db
from src.app.models.user import UserDomainPreference
from src.app.schemas.user import UserPreferenceUpdate, UserProfile

router = APIRouter(prefix="/users/{user_id}/preferences", tags=["preferences"])


@router.get("", response_model=UserProfile)
async def get_preferences(
    user_id: str,
    session: AsyncSession = Depends(get_db),
):
    repo = UserRepository(session)
    user = await repo.get_with_preferences(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("")
async def update_preferences(
    user_id: str,
    data: UserPreferenceUpdate,
    session: AsyncSession = Depends(get_db),
):
    repo = UserRepository(session)
    user = await repo.get_with_preferences(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update scalar fields
    if data.global_depth_fallback is not None:
        user.global_depth_fallback = data.global_depth_fallback
    if data.exploration_rate is not None:
        user.exploration_rate = data.exploration_rate
    if data.delivery_frequency is not None:
        user.delivery_frequency = data.delivery_frequency
    if data.delivery_time is not None:
        user.delivery_time = data.delivery_time
    if data.delivery_timezone is not None:
        user.delivery_timezone = data.delivery_timezone
    if data.delivery_channel is not None:
        user.delivery_channel = data.delivery_channel
    if data.seed_topics is not None:
        user.seed_topics = data.seed_topics
    if data.trusted_sources is not None:
        user.trusted_sources = data.trusted_sources
    if data.excluded_sources is not None:
        user.excluded_sources = data.excluded_sources
    if data.blocked_domains is not None:
        user.blocked_domains = data.blocked_domains

    # Update domain preferences if provided
    if data.domains is not None:
        # Clear existing and recreate
        user.domain_preferences.clear()
        await session.flush()

        for dp in data.domains:
            pref = UserDomainPreference(
                user_id=user.id,
                domain_id=dp.domain_id,
                weight=dp.weight,
                depth_preference=dp.depth_preference,
                is_explicit=True,
            )
            session.add(pref)

    await session.flush()
    user = await repo.get_with_preferences(user_id)
    return UserProfile.model_validate(user)
