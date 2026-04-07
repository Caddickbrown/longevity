from datetime import datetime

from pydantic import BaseModel


class BiomarkerReadingCreate(BaseModel):
    source: str
    metric: str
    value: float
    unit: str
    recorded_at: datetime


class BiomarkerReadingOut(BiomarkerReadingCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class InterventionOut(BaseModel):
    id: int
    name: str
    tier: int
    evidence_grade: str
    cost_tier: int
    mechanism: str
    references: str
    started_at: datetime | None
    ended_at: datetime | None

    model_config = {"from_attributes": True}


class ProtocolEntryCreate(BaseModel):
    intervention_id: int
    date: str  # YYYY-MM-DD
    complied: bool
    notes: str = ""


class ProtocolEntryOut(ProtocolEntryCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
