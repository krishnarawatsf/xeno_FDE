import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import EventCallback
from app.services.events import process_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/callback")
def event_callback(payload: EventCallback, db: Session = Depends(get_db)):
    event, is_duplicate = process_event(
        db,
        campaign_id=payload.campaign_id,
        customer_id=payload.customer_id,
        event_type=payload.event_type,
        idempotency_key=payload.idempotency_key,
        channel=payload.channel,
        metadata=payload.metadata,
        timestamp=payload.timestamp,
    )
    return {
        "status": "duplicate" if is_duplicate else "processed",
        "event_id": str(event.id) if event else None,
    }
