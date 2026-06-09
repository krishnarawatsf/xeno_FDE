"""Campaign orchestration — send to channel service."""

import logging
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Campaign, CampaignStatus, Event, EventType
from app.services.events import process_event
from app.services.segmentation import evaluate_segment_by_id

logger = logging.getLogger(__name__)


async def send_campaign(db: Session, campaign_id: UUID) -> dict:
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise ValueError("Campaign not found")

    if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.SCHEDULED):
        raise ValueError(f"Campaign cannot be sent in status: {campaign.status}")

    if not campaign.segment_id:
        raise ValueError("Campaign has no segment attached")

    customers = evaluate_segment_by_id(db, campaign.segment_id)
    if not customers:
        raise ValueError("Segment matched zero customers")

    campaign.status = CampaignStatus.SENDING
    db.commit()

    channels = campaign.channel_mix or ["email"]
    sent_count = 0
    errors = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for customer in customers:
            for channel in channels:
                payload = {
                    "campaign_id": str(campaign_id),
                    "customer_id": str(customer.id),
                    "channel": channel,
                    "message": campaign.message_template.replace(
                        "{{name}}", customer.name
                    ),
                    "callback_url": settings.normalized_crm_callback_url,
                }

                try:
                    resp = await client.post(
                        f"{settings.normalized_channel_service_url}/send",
                        json=payload,
                    )
                    resp.raise_for_status()
                    process_event(
                        db,
                        campaign_id=campaign_id,
                        customer_id=customer.id,
                        event_type=EventType.SENT,
                        idempotency_key=f"{campaign_id}:{customer.id}:{channel}:sent",
                        channel=channel,
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error("Channel send failed: %s", e)
                    process_event(
                        db,
                        campaign_id=campaign_id,
                        customer_id=customer.id,
                        event_type=EventType.FAILED,
                        idempotency_key=f"{campaign_id}:{customer.id}:{channel}:send_failed",
                        channel=channel,
                        metadata={"error": str(e), "stage": "send"},
                    )
                    errors.append({"customer_id": str(customer.id), "error": str(e)})

    campaign.status = CampaignStatus.SENT
    db.commit()

    return {
        "campaign_id": str(campaign_id),
        "status": campaign.status.value,
        "recipients": len(customers),
        "messages_sent": sent_count,
        "channels": channels,
        "errors": errors,
    }
