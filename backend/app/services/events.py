"""Idempotent event processor for channel callbacks."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Campaign, CampaignStatus, Event, EventType

logger = logging.getLogger(__name__)

EVENT_ORDER = {
    EventType.SENT: 0,
    EventType.DELIVERED: 1,
    EventType.FAILED: 1,
    EventType.OPENED: 2,
    EventType.CLICKED: 3,
    EventType.CONVERTED: 4,
}


def process_event(
    db: Session,
    campaign_id: UUID,
    customer_id: UUID,
    event_type: EventType,
    idempotency_key: str,
    channel: str | None = None,
    metadata: dict | None = None,
    timestamp: datetime | None = None,
) -> tuple[Event | None, bool]:
    """
    Process an incoming event with idempotency.
    Returns (event, is_duplicate).
    """
    existing = (
        db.query(Event).filter(Event.idempotency_key == idempotency_key).first()
    )
    if existing:
        logger.info("Duplicate event ignored: %s", idempotency_key)
        return existing, True

    event = Event(
        campaign_id=campaign_id,
        customer_id=customer_id,
        event_type=event_type,
        channel=channel,
        idempotency_key=idempotency_key,
        metadata_json=metadata,
        timestamp=timestamp or datetime.utcnow(),
    )

    try:
        db.add(event)
        db.commit()
        db.refresh(event)
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(Event).filter(Event.idempotency_key == idempotency_key).first()
        )
        return existing, True

    _maybe_update_campaign_status(db, campaign_id)
    return event, False


def _maybe_update_campaign_status(db: Session, campaign_id: UUID) -> None:
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign or campaign.status not in (CampaignStatus.SENDING, CampaignStatus.SENT):
        return

    sent_count = (
        db.query(Event)
        .filter(Event.campaign_id == campaign_id, Event.event_type == EventType.SENT)
        .count()
    )
    terminal_count = (
        db.query(Event)
        .filter(
            Event.campaign_id == campaign_id,
            Event.event_type.in_([EventType.DELIVERED, EventType.FAILED]),
        )
        .count()
    )

    if sent_count > 0 and terminal_count >= sent_count:
        campaign.status = CampaignStatus.COMPLETED
        db.commit()
