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


class ProtocolExplanationOut(BaseModel):
    id: int
    intervention_id: int
    explanation: str
    why_it_matters: str
    how_to_implement: str
    sources: list[dict]
    difficulty: str
    generated_at: datetime

    model_config = {"from_attributes": True}


class ConversationMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class JournalEntryCreate(BaseModel):
    date: str  # YYYY-MM-DD
    body: str = ""
    tags: list[str] = []
    mood: int | None = None
    energy: int | None = None


class JournalEntryOut(JournalEntryCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BeliefSnapshotCreate(BaseModel):
    title: str
    body: str
    tags: list[str] = []


class BeliefSnapshotOut(BeliefSnapshotCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ResearchDigestOut(BaseModel):
    id: int
    generated_at: datetime
    source: str
    summary: str
    interventions_mentioned: list[str]
    raw_response: str

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
