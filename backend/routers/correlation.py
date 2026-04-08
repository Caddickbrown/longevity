from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.correlation import compute_correlation

router = APIRouter(prefix="/correlation", tags=["correlation"])


@router.get("/")
def get_correlation(
    metric: str = Query(...),
    from_date: str | None = Query(None),  # YYYY-MM-DD, defaults to 90 days ago
    to_date: str | None = Query(None),    # YYYY-MM-DD, defaults to today
    db: Session = Depends(get_db),
):
    try:
        to = date.fromisoformat(to_date) if to_date else date.today()
        from_ = date.fromisoformat(from_date) if from_date else to - timedelta(days=90)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")

    if from_ > to:
        raise HTTPException(status_code=400, detail="from_date must be before to_date")

    return compute_correlation(metric, from_, to, db)
