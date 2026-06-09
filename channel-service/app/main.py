import asyncio
import logging
from uuid import UUID

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.simulator import simulate_message_lifecycle

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Xeno Channel Service",
    description="Stubbed messaging channel microservice",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SendRequest(BaseModel):
    campaign_id: str
    customer_id: str
    channel: str
    message: str
    callback_url: str | None = None


class SendResponse(BaseModel):
    status: str
    message_id: str
    channel: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "xeno-channel-service"}


@app.post("/send", response_model=SendResponse)
async def send_message(payload: SendRequest):
    """Accept a message and simulate async delivery lifecycle."""
    message_id = f"msg_{payload.campaign_id[:8]}_{payload.customer_id[:8]}"

    asyncio.create_task(
        simulate_message_lifecycle(
            campaign_id=payload.campaign_id,
            customer_id=payload.customer_id,
            channel=payload.channel,
            message=payload.message,
            callback_url=payload.callback_url,
        )
    )

    return SendResponse(
        status="accepted",
        message_id=message_id,
        channel=payload.channel,
    )
