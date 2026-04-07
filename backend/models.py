from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class BiomarkerReading(Base):
    __tablename__ = "biomarker_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(50))  # garmin | manual | import
    metric: Mapped[str] = mapped_column(String(100), index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(50))
    recorded_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    tier: Mapped[int] = mapped_column(Integer)          # 1, 2, or 3
    evidence_grade: Mapped[str] = mapped_column(String(1))  # A, B, or C
    cost_tier: Mapped[int] = mapped_column(Integer)     # 1=£, 2=££, 3=£££
    mechanism: Mapped[str] = mapped_column(Text)
    references: Mapped[str] = mapped_column(Text, default="")  # newline-separated URLs
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ProtocolEntry(Base):
    __tablename__ = "protocol_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    intervention_id: Mapped[int] = mapped_column(Integer, index=True)
    date: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    complied: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
