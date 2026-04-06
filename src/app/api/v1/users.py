from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.repositories.user import UserRepository
from src.app.dependencies import get_db
from src.app.models.user import User, UserDomainPreference
from src.app.schemas.user import UserCreate, UserProfile

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserProfile, status_code=201)
async def create_user(
    data: UserCreate,
    session: AsyncSession = Depends(get_db),
):
    user = User(
        email=data.email,
        name=data.name,
        global_depth_fallback=data.global_depth_fallback,
        exploration_rate=data.exploration_rate,
        delivery_frequency=data.delivery_frequency,
        delivery_time=data.delivery_time,
        delivery_timezone=data.delivery_timezone,
        delivery_channel=data.delivery_channel,
        seed_topics=data.seed_topics,
        trusted_sources=data.trusted_sources,
        excluded_sources=data.excluded_sources,
        onboarding_completed=True,
    )
    session.add(user)
    await session.flush()

    # Create domain preferences
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

    # Reload with preferences
    repo = UserRepository(session)
    user = await repo.get_with_preferences(user.id)
    return user


@router.get("/{user_id}", response_model=UserProfile)
async def get_user(
    user_id: str,
    session: AsyncSession = Depends(get_db),
):
    repo = UserRepository(session)
    user = await repo.get_with_preferences(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
