from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.repositories.user import UserRepository
from src.app.dependencies import get_db
from src.app.models.user import User, UserDomainPreference
from src.app.schemas.user import QuickUserCreate, UserCreate, UserProfile

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/quick", response_model=UserProfile, status_code=201)
async def quick_create_user(
    data: QuickUserCreate,
    session: AsyncSession = Depends(get_db),
):
    """Simple onboarding: pick interests, equal weights, default depth."""
    user = User(
        name=data.name,
        global_depth_fallback="L2",
        exploration_rate=0.15,
        onboarding_completed=True,
    )
    session.add(user)
    await session.flush()

    for interest in data.interests:
        pref = UserDomainPreference(
            user_id=user.id,
            domain_id=interest,
            weight=0.5,
            depth_preference="L2",
            is_explicit=True,
        )
        session.add(pref)

    await session.flush()
    repo = UserRepository(session)
    user = await repo.get_with_preferences(user.id)
    return user


@router.delete("/me/interests/{domain_id}", status_code=204)
async def delete_interest(
    domain_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Remove a domain interest for the current user."""
    result = await session.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="No user found")

    repo = UserRepository(session)
    deleted = await repo.delete_domain_preference(user.id, domain_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Interest not found")


@router.post("/me/interests", status_code=201)
async def add_interest(
    request_body: dict,
    session: AsyncSession = Depends(get_db),
):
    """Add a new domain interest for the current user."""
    domain_id = request_body.get("domain_id", "").strip()
    if not domain_id:
        raise HTTPException(status_code=400, detail="domain_id is required")

    result = await session.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="No user found")

    # Check if already exists
    repo = UserRepository(session)
    existing = await repo.update_domain_preference(user.id, domain_id)
    if existing:
        raise HTTPException(status_code=409, detail="Interest already exists")

    pref = UserDomainPreference(
        user_id=user.id,
        domain_id=domain_id,
        weight=0.5,
        depth_preference="L2",
        is_explicit=True,
    )
    session.add(pref)
    await session.flush()
    return {"domain_id": domain_id, "weight": 0.5}


@router.get("/me", response_model=UserProfile)
async def get_current_user(
    session: AsyncSession = Depends(get_db),
):
    """Get the single user (personal tool mode)."""
    result = await session.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="No user found. Complete onboarding first.")
    repo = UserRepository(session)
    return await repo.get_with_preferences(user.id)


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
