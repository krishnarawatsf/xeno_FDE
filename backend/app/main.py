import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import campaigns, customers, events, segments

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Xeno AI-Native Mini CRM",
    description="AI Campaign Operator for D2C brands",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router)
app.include_router(segments.router)
app.include_router(campaigns.router)
app.include_router(events.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "service": "xeno-crm-backend"}


@app.post("/seed")
def seed_data():
    from app.seed import seed

    seed()
    return {"status": "seeded"}
