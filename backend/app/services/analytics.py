"""Campaign analytics and funnel metrics."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Campaign, Event, EventType
from app.services.ai import generate_insights


def get_campaign_analytics(db: Session, campaign_id: UUID) -> dict:
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise ValueError("Campaign not found")

    events = db.query(Event).filter(Event.campaign_id == campaign_id).all()

    funnel = {
        "sent": 0,
        "delivered": 0,
        "failed": 0,
        "opened": 0,
        "clicked": 0,
        "converted": 0,
    }

    channel_breakdown: dict[str, dict[str, int]] = {}

    for event in events:
        et = event.event_type.value
        if et in funnel:
            funnel[et] += 1

        ch = event.channel or "unknown"
        if ch not in channel_breakdown:
            channel_breakdown[ch] = {
                "sent": 0,
                "delivered": 0,
                "failed": 0,
                "opened": 0,
                "clicked": 0,
                "converted": 0,
            }
        if et in channel_breakdown[ch]:
            channel_breakdown[ch][et] += 1

    sent = funnel["sent"]
    delivered = funnel["delivered"]
    opened = funnel["opened"]
    clicked = funnel["clicked"]

    rates = {
        "delivery_rate": delivered / sent if sent > 0 else 0,
        "open_rate": opened / delivered if delivered > 0 else 0,
        "click_rate": clicked / opened if opened > 0 else 0,
        "conversion_rate": funnel["converted"] / clicked if clicked > 0 else 0,
    }

    insights = generate_insights(funnel, rates)

    return {
        "campaign_id": campaign.id,
        "name": campaign.name,
        "status": campaign.status,
        "funnel": funnel,
        "rates": rates,
        "channel_breakdown": channel_breakdown,
        "insights": insights,
    }
