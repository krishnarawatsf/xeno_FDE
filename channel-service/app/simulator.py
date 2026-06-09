"""Simulates messaging lifecycle with probabilistic outcomes."""

import asyncio
import logging
import random
import uuid
from datetime import datetime

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

DELIVERY_RATE = 0.90
OPEN_RATE = 0.70
CLICK_RATE = 0.30

CONVERSION_RATE = 0.15

DELAY_DELIVERED = (0.5, 2.0)
DELAY_OPENED = (1.0, 3.0)
DELAY_CLICKED = (2.0, 5.0)
DELAY_CONVERTED = (1.0, 3.0)


async def _emit_callback(
    callback_url: str,
    campaign_id: str,
    customer_id: str,
    channel: str,
    event_type: str,
    suffix: str,
):
    idempotency_key = f"{campaign_id}:{customer_id}:{channel}:{event_type}:{suffix}"
    payload = {
        "campaign_id": campaign_id,
        "customer_id": customer_id,
        "event_type": event_type,
        "channel": channel,
        "idempotency_key": idempotency_key,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {"simulated": True, "service": "channel-stub"},
    }

    base = callback_url.rstrip("/")
    url = base if base.endswith("/events/callback") else f"{base}/events/callback"
    max_retries = 3

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code < 500:
                    logger.info("Callback %s → %s (%s)", event_type, resp.status_code, idempotency_key)
                    return
        except Exception as e:
            logger.warning("Callback attempt %d failed: %s", attempt + 1, e)
            await asyncio.sleep(0.5 * (attempt + 1))


async def simulate_message_lifecycle(
    campaign_id: str,
    customer_id: str,
    channel: str,
    message: str,
    callback_url: str | None = None,
):
    """Simulate delivery → open → click lifecycle with async callbacks."""
    cb_url = callback_url or settings.crm_callback_url
    run_id = uuid.uuid4().hex[:8]

    await asyncio.sleep(random.uniform(*DELAY_DELIVERED))

    if random.random() < DELIVERY_RATE:
        await _emit_callback(cb_url, campaign_id, customer_id, channel, "delivered", run_id)

        await asyncio.sleep(random.uniform(*DELAY_OPENED))

        if random.random() < OPEN_RATE:
            await _emit_callback(cb_url, campaign_id, customer_id, channel, "opened", run_id)

            await asyncio.sleep(random.uniform(*DELAY_CLICKED))

            if random.random() < CLICK_RATE:
                await _emit_callback(cb_url, campaign_id, customer_id, channel, "clicked", run_id)

                await asyncio.sleep(random.uniform(*DELAY_CONVERTED))

                if random.random() < CONVERSION_RATE:
                    await _emit_callback(
                        cb_url, campaign_id, customer_id, channel, "converted", run_id
                    )
    else:
        await _emit_callback(cb_url, campaign_id, customer_id, channel, "failed", run_id)
