from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Intervention
from backend.schemas import InterventionOut

router = APIRouter(prefix="/protocols", tags=["protocols"])


@router.get("/", response_model=list[InterventionOut])
def list_interventions(
    tier: int | None = Query(None),
    db: Session = Depends(get_db),
):
    stmt = select(Intervention)
    if tier is not None:
        stmt = stmt.where(Intervention.tier == tier)
    stmt = stmt.order_by(Intervention.tier.asc(), Intervention.name.asc())
    return db.execute(stmt).scalars().all()
