"""Correlates biomarker readings against protocol compliance."""
import logging
from datetime import date, datetime, timedelta
from typing import Any

from scipy.stats import pearsonr
from sqlalchemy import Integer, func, select
from sqlalchemy.orm import Session

from backend.models import BiomarkerReading, ProtocolEntry

logger = logging.getLogger(__name__)


def _date_range(from_date: date, to_date: date) -> list[date]:
    days = (to_date - from_date).days + 1
    return [from_date + timedelta(days=i) for i in range(days)]


def compute_correlation(
    metric: str,
    from_date: date,
    to_date: date,
    db: Session,
) -> dict[str, Any]:
    """
    Returns daily {date, value, compliance} joined data plus Pearson r.

    compliance = number of protocols marked complied on that day.
    """
    # Biomarker readings: average per day if multiple exist
    biomarker_rows = db.execute(
        select(
            func.date(BiomarkerReading.recorded_at).label("day"),
            func.avg(BiomarkerReading.value).label("value"),
        )
        .where(BiomarkerReading.metric == metric)
        .where(BiomarkerReading.recorded_at >= datetime.combine(from_date, datetime.min.time()))
        .where(BiomarkerReading.recorded_at <= datetime.combine(to_date, datetime.max.time()))
        .group_by(func.date(BiomarkerReading.recorded_at))
    ).all()

    # Compliance: count of complied=True entries per day
    compliance_rows = db.execute(
        select(
            ProtocolEntry.date.label("day"),
            func.sum(ProtocolEntry.complied.cast(Integer)).label("compliance"),
        )
        .where(ProtocolEntry.date >= str(from_date))
        .where(ProtocolEntry.date <= str(to_date))
        .group_by(ProtocolEntry.date)
    ).all()

    biomarker_by_day = {row.day: row.value for row in biomarker_rows}
    compliance_by_day = {row.day: int(row.compliance or 0) for row in compliance_rows}

    data = []
    for d in _date_range(from_date, to_date):
        day_str = str(d)
        value = biomarker_by_day.get(day_str)
        compliance = compliance_by_day.get(day_str, 0)
        if value is not None:
            data.append({"date": day_str, "value": value, "compliance": compliance})

    # Pearson r requires at least 2 paired points
    pearson_r = None
    p_value = None
    if len(data) >= 2:
        values = [d["value"] for d in data]
        compliances = [d["compliance"] for d in data]
        if len(set(values)) > 1 and len(set(compliances)) > 1:
            r, p = pearsonr(values, compliances)
            pearson_r = round(float(r), 4)
            p_value = round(float(p), 4)

    return {
        "metric": metric,
        "from_date": str(from_date),
        "to_date": str(to_date),
        "data": data,
        "pearson_r": pearson_r,
        "p_value": p_value,
    }
