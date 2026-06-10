import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import Base, engine
from app.routers import campaigns, customers, events, segments

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Xeno AI-Native Mini CRM",
    description="AI Campaign Operator for D2C brands",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
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
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connected (%s)", settings.environment)
    except Exception as exc:
        logger.error("Database connection failed on startup: %s", exc)
        if settings.environment == "production":
            raise


@app.get("/health")
def health():
    db_status = "connected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"error: {exc.__class__.__name__}"

    healthy = db_status == "connected"
    return {
        "status": "ok" if healthy else "degraded",
        "service": "xeno-crm-backend",
        "environment": settings.environment,
        "database": db_status,
    }


@app.post("/seed")
def seed_data():
    from app.seed import seed

    seed()
    return {"status": "seeded"}
