from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models import CampaignStatus, Channel, EventType


# Customers
class CustomerCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None


class CustomerResponse(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# Orders
class OrderCreate(BaseModel):
    customer_id: UUID
    amount: float
    status: str = "completed"


class OrderResponse(BaseModel):
    id: UUID
    customer_id: UUID
    amount: float
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# Segments
class SegmentCreate(BaseModel):
    name: str
    definition_json: dict
    is_ai_generated: bool = False


class SegmentAISuggest(BaseModel):
    natural_language: str = Field(..., examples=["High value customers in the last 30 days"])


class SegmentEvaluate(BaseModel):
    segment_id: UUID | None = None
    definition_json: dict | None = None


class SegmentResponse(BaseModel):
    id: UUID
    name: str
    definition_json: dict
    is_ai_generated: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# Campaigns
class CampaignCreate(BaseModel):
    name: str
    goal: str | None = None
    segment_id: UUID | None = None
    message_template: str
    channel_mix: list[str] = Field(default_factory=lambda: ["email"])


class CampaignSend(BaseModel):
    campaign_id: UUID


class CampaignRecommend(BaseModel):
    goal: str
    segment_id: UUID | None = None


class CampaignResponse(BaseModel):
    id: UUID
    name: str
    goal: str | None
    segment_id: UUID | None
    message_template: str
    channel_mix: list
    status: CampaignStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignAnalytics(BaseModel):
    campaign_id: UUID
    name: str
    status: CampaignStatus
    funnel: dict[str, int]
    rates: dict[str, float]
    channel_breakdown: dict[str, dict[str, int]]
    insights: list[str]


# Events
class EventCallback(BaseModel):
    campaign_id: UUID
    customer_id: UUID
    event_type: EventType
    channel: str | None = None
    idempotency_key: str
    timestamp: datetime | None = None
    metadata: dict | None = None


class MessageGenerateRequest(BaseModel):
    customer_name: str
    goal: str
    brand_tone: str = "friendly and professional"
    channel: Channel = Channel.EMAIL


class MessageGenerateResponse(BaseModel):
    message: str
    channel: str
    personalization_notes: str
