from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Intervention, ProtocolExplanation
from backend.schemas import ProtocolExplanationOut
from backend.services.teaching import TeachingError, generate_explanation

router = APIRouter(prefix="/teaching", tags=["teaching"])


@router.get("/", response_model=list[dict])
def list_explanations(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Intervention, ProtocolExplanation)
        .outerjoin(ProtocolExplanation, Intervention.id == ProtocolExplanation.intervention_id)
        .order_by(Intervention.tier, Intervention.name)
    ).all()
    return [
        {
            "intervention_id": i.id,
            "name": i.name,
            "tier": i.tier,
            "evidence_grade": i.evidence_grade,
            "has_explanation": exp is not None,
            "difficulty": exp.difficulty if exp else None,
        }
        for i, exp in rows
    ]


@router.get("/{intervention_id}", response_model=ProtocolExplanationOut)
def get_explanation(intervention_id: int, db: Session = Depends(get_db)):
    exp = db.execute(
        select(ProtocolExplanation).where(ProtocolExplanation.intervention_id == intervention_id)
    ).scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="No explanation generated yet for this protocol")
    return exp


@router.post("/generate/{intervention_id}", response_model=ProtocolExplanationOut, status_code=201)
def generate_for_intervention(intervention_id: int, db: Session = Depends(get_db)):
    intervention = db.get(Intervention, intervention_id)
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    try:
        data = generate_explanation(intervention)
    except TeachingError as e:
        raise HTTPException(status_code=503, detail=str(e))

    existing = db.execute(
        select(ProtocolExplanation).where(ProtocolExplanation.intervention_id == intervention_id)
    ).scalar_one_or_none()

    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        db.commit()
        db.refresh(existing)
        return existing

    exp = ProtocolExplanation(intervention_id=intervention_id, **data)
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


@router.post("/generate-all")
def generate_all(db: Session = Depends(get_db)):
    interventions = db.execute(select(Intervention)).scalars().all()
    existing_ids = set(
        db.execute(select(ProtocolExplanation.intervention_id)).scalars().all()
    )
    generated = 0
    skipped = 0
    errors = []

    for intervention in interventions:
        if intervention.id in existing_ids:
            skipped += 1
            continue
        try:
            data = generate_explanation(intervention)
            db.add(ProtocolExplanation(intervention_id=intervention.id, **data))
            db.commit()
            generated += 1
        except TeachingError as e:
            errors.append({"intervention": intervention.name, "error": str(e)})
            if "ANTHROPIC_API_KEY" in str(e):
                break  # No point continuing without key

    return {"generated": generated, "skipped": skipped, "errors": errors}
