from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Campaign, Segment
from app.schemas import (
    CampaignAnalytics,
    CampaignCreate,
    CampaignRecommend,
    CampaignResponse,
    CampaignSend,
    MessageGenerateRequest,
    MessageGenerateResponse,
)
from app.services.ai import generate_message, recommend_campaign
from app.services.analytics import get_campaign_analytics
from app.services.campaigns import send_campaign
from app.services.segmentation import evaluate_segment_by_id

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignResponse, status_code=201)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)):
    if payload.segment_id:
        segment = db.query(Segment).filter(Segment.id == payload.segment_id).first()
        if not segment:
            raise HTTPException(status_code=404, detail="Segment not found")
    campaign = Campaign(**payload.model_dump())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.get("", response_model=list[CampaignResponse])
def list_campaigns(db: Session = Depends(get_db)):
    return db.query(Campaign).order_by(Campaign.created_at.desc()).all()


@router.post("/send")
async def send_campaign_endpoint(payload: CampaignSend, db: Session = Depends(get_db)):
    try:
        result = await send_campaign(db, payload.campaign_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/recommend")
def recommend_campaign_endpoint(payload: CampaignRecommend, db: Session = Depends(get_db)):
    audience_size = 0
    if payload.segment_id:
        try:
            customers = evaluate_segment_by_id(db, payload.segment_id)
            audience_size = len(customers)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    return recommend_campaign(payload.goal, audience_size)


@router.post("/generate-message", response_model=MessageGenerateResponse)
def generate_message_endpoint(payload: MessageGenerateRequest):
    result = generate_message(
        payload.customer_name,
        payload.goal,
        payload.brand_tone,
        payload.channel.value,
    )
    return MessageGenerateResponse(**result)


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: UUID, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.get("/{campaign_id}/analytics", response_model=CampaignAnalytics)
def campaign_analytics(campaign_id: UUID, db: Session = Depends(get_db)):
    try:
        return get_campaign_analytics(db, campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
