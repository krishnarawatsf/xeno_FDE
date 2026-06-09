from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Segment
from app.schemas import (
    CustomerResponse,
    SegmentAISuggest,
    SegmentCreate,
    SegmentEvaluate,
    SegmentResponse,
)
from app.services.ai import suggest_segment_from_nl
from app.services.segmentation import evaluate_segment, evaluate_segment_by_id

router = APIRouter(prefix="/segments", tags=["segments"])


@router.post("", response_model=SegmentResponse, status_code=201)
def create_segment(payload: SegmentCreate, db: Session = Depends(get_db)):
    segment = Segment(**payload.model_dump())
    db.add(segment)
    db.commit()
    db.refresh(segment)
    return segment


@router.get("", response_model=list[SegmentResponse])
def list_segments(db: Session = Depends(get_db)):
    return db.query(Segment).order_by(Segment.created_at.desc()).all()


@router.post("/ai-suggest")
def ai_suggest_segment(payload: SegmentAISuggest):
    definition = suggest_segment_from_nl(payload.natural_language)
    return {
        "name": payload.natural_language[:80],
        "definition_json": definition,
        "is_ai_generated": definition.get("is_ai_generated", True),
    }


@router.post("/evaluate", response_model=list[CustomerResponse])
def evaluate_segment_endpoint(payload: SegmentEvaluate, db: Session = Depends(get_db)):
    try:
        if payload.segment_id:
            customers = evaluate_segment_by_id(db, payload.segment_id)
        elif payload.definition_json:
            customers = evaluate_segment(db, payload.definition_json)
        else:
            raise HTTPException(status_code=400, detail="Provide segment_id or definition_json")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return customers
