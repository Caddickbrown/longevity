from backend.models import BiomarkerReading
from backend.database import Base


def test_biomarker_table_exists(db):
    tables = Base.metadata.tables.keys()
    assert "biomarker_readings" in tables
