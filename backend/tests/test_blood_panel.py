import io
import pytest

from backend.services.blood_panel import BloodPanelParseError, parse_blood_panel_csv

SAMPLE_CSV = """\
Test,Value,Unit,Reference Range,Date
Testosterone,18.5,nmol/L,8.64 - 29.0,2026-01-15
Free Testosterone,0.38,nmol/L,0.2 - 0.62,2026-01-15
SHBG,32,nmol/L,18.3 - 54.1,2026-01-15
Haemoglobin,148,g/L,130 - 170,2026-01-15
HbA1c,36,mmol/mol,20 - 41,2026-01-15
Ferritin,85,ug/L,30 - 400,2026-01-15
Vitamin D,72,nmol/L,50 - 175,2026-01-15
CRP,0.4,mg/L,0 - 5,2026-01-15
TSH,1.8,mIU/L,0.27 - 4.2,2026-01-15
"""

CSV_WITH_NON_NUMERIC = """\
Test,Value,Unit,Reference Range,Date
Testosterone,18.5,nmol/L,8.64 - 29.0,2026-01-15
CRP,pending,mg/L,0 - 5,2026-01-15
TSH,,mIU/L,0.27 - 4.2,2026-01-15
"""

CSV_MISSING_COLUMNS = """\
Test,Value,Unit,Date
Testosterone,18.5,nmol/L,2026-01-15
"""


# --- Unit tests for parse_blood_panel_csv ---

def test_parse_returns_correct_metric_names():
    results = parse_blood_panel_csv(SAMPLE_CSV)
    metrics = {r["metric"] for r in results}
    assert "testosterone_nmol_l" in metrics
    assert "free_testosterone_nmol_l" in metrics
    assert "shbg_nmol_l" in metrics
    assert "haemoglobin_g_l" in metrics
    assert "hba1c_mmol_mol" in metrics
    assert "ferritin_ug_l" in metrics
    assert "vitamin_d_nmol_l" in metrics
    assert "crp_mg_l" in metrics
    assert "tsh_miu_l" in metrics


def test_parse_returns_correct_values():
    results = parse_blood_panel_csv(SAMPLE_CSV)
    by_metric = {r["metric"]: r for r in results}
    assert by_metric["testosterone_nmol_l"]["value"] == 18.5
    assert by_metric["crp_mg_l"]["value"] == 0.4
    assert by_metric["ferritin_ug_l"]["value"] == 85.0


def test_parse_returns_correct_source_and_unit():
    results = parse_blood_panel_csv(SAMPLE_CSV)
    for r in results:
        assert r["source"] == "blood_panel"
    by_metric = {r["metric"]: r for r in results}
    assert by_metric["testosterone_nmol_l"]["unit"] == "nmol/L"


def test_parse_correct_recorded_at():
    from datetime import datetime
    results = parse_blood_panel_csv(SAMPLE_CSV)
    for r in results:
        assert r["recorded_at"] == datetime(2026, 1, 15, 0, 0, 0)


def test_parse_skips_non_numeric_values():
    results = parse_blood_panel_csv(CSV_WITH_NON_NUMERIC)
    # "pending" and empty should be skipped; only testosterone survives
    assert len(results) == 1
    assert results[0]["metric"] == "testosterone_nmol_l"


def test_parse_raises_on_missing_columns():
    with pytest.raises(BloodPanelParseError, match="missing required columns"):
        parse_blood_panel_csv(CSV_MISSING_COLUMNS)


def test_parse_returns_all_nine_rows():
    results = parse_blood_panel_csv(SAMPLE_CSV)
    assert len(results) == 9


# --- Integration tests via HTTP ---

def test_import_valid_csv_returns_inserted(client):
    file_bytes = SAMPLE_CSV.encode("utf-8")
    response = client.post(
        "/blood-panel/import",
        files={"file": ("panel.csv", file_bytes, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted"] == 9
    assert data["skipped"] == 0


def test_import_duplicate_data_returns_skipped(client):
    file_bytes = SAMPLE_CSV.encode("utf-8")
    # First upload
    client.post(
        "/blood-panel/import",
        files={"file": ("panel.csv", file_bytes, "text/csv")},
    )
    # Second upload of same data
    response = client.post(
        "/blood-panel/import",
        files={"file": ("panel.csv", file_bytes, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["skipped"] == 9
    assert data["inserted"] == 0


def test_import_rejects_non_csv(client):
    response = client.post(
        "/blood-panel/import",
        files={"file": ("data.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400


def test_import_malformed_csv_returns_422(client):
    bad_csv = CSV_MISSING_COLUMNS.encode("utf-8")
    response = client.post(
        "/blood-panel/import",
        files={"file": ("panel.csv", bad_csv, "text/csv")},
    )
    assert response.status_code == 422
