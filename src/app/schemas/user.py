from pydantic import BaseModel, Field

from src.app.core.constants import DepthLevel, DeliveryFrequency, DeliveryChannel


class DomainPreferenceInput(BaseModel):
    domain_id: str
    weight: float = Field(default=0.5, ge=0.0, le=1.0)
    depth_preference: DepthLevel = DepthLevel.L2


class UserCreate(BaseModel):
    email: str | None = None
    name: str | None = None
    domains: list[DomainPreferenceInput] = Field(min_length=1)
    global_depth_fallback: DepthLevel = DepthLevel.L2
    exploration_rate: float = Field(default=0.15, ge=0.0, le=1.0)
    delivery_frequency: DeliveryFrequency = DeliveryFrequency.DAILY
    delivery_time: str = "08:00"
    delivery_timezone: str = "UTC"
    delivery_channel: DeliveryChannel = DeliveryChannel.IN_APP
    seed_topics: list[str] = Field(default_factory=list)
    trusted_sources: list[str] = Field(default_factory=list)
    excluded_sources: list[str] = Field(default_factory=list)


class UserPreferenceUpdate(BaseModel):
    domains: list[DomainPreferenceInput] | None = None
    global_depth_fallback: DepthLevel | None = None
    exploration_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    delivery_frequency: DeliveryFrequency | None = None
    delivery_time: str | None = None
    delivery_timezone: str | None = None
    delivery_channel: DeliveryChannel | None = None
    seed_topics: list[str] | None = None
    trusted_sources: list[str] | None = None
    excluded_sources: list[str] | None = None
    blocked_domains: list[str] | None = None


class DomainPreferenceResponse(BaseModel):
    domain_id: str
    weight: float
    depth_preference: str
    is_explicit: bool

    model_config = {"from_attributes": True}


class UserProfile(BaseModel):
    id: str
    email: str | None
    name: str | None
    global_depth_fallback: str
    exploration_rate: float
    delivery_frequency: str
    delivery_time: str
    delivery_timezone: str
    delivery_channel: str
    seed_topics: list[str]
    trusted_sources: list[str]
    excluded_sources: list[str]
    blocked_domains: list[str]
    onboarding_completed: bool
    domain_preferences: list[DomainPreferenceResponse]

    model_config = {"from_attributes": True}
