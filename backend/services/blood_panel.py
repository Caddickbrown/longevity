import csv
import io
from datetime import datetime

REQUIRED_COLUMNS = {"Test", "Value", "Unit", "Reference Range", "Date"}

TEST_NAME_MAP = {
    "Testosterone": "testosterone_nmol_l",
    "Free Testosterone": "free_testosterone_nmol_l",
    "SHBG": "shbg_nmol_l",
    "Haemoglobin": "haemoglobin_g_l",
    "HbA1c": "hba1c_mmol_mol",
    "Ferritin": "ferritin_ug_l",
    "Vitamin D": "vitamin_d_nmol_l",
    "CRP": "crp_mg_l",
    "TSH": "tsh_miu_l",
}


class BloodPanelParseError(Exception):
    pass


def parse_blood_panel_csv(content: str) -> list[dict]:
    """
    Parse a Medichecks/Thriva-style CSV blood panel export.

    Expected columns: Test, Value, Unit, Reference Range, Date

    Returns a list of dicts with keys: source, metric, value, unit, recorded_at.
    Skips rows where Value is empty or non-numeric.
    Raises BloodPanelParseError if CSV is malformed (missing required columns).
    """
    reader = csv.DictReader(io.StringIO(content))

    if reader.fieldnames is None:
        raise BloodPanelParseError("CSV is empty or has no header row")

    actual_columns = set(reader.fieldnames)
    missing = REQUIRED_COLUMNS - actual_columns
    if missing:
        raise BloodPanelParseError(
            f"CSV is missing required columns: {', '.join(sorted(missing))}"
        )

    results = []
    for row in reader:
        raw_value = row["Value"].strip()
        if not raw_value:
            continue

        try:
            value = float(raw_value)
        except ValueError:
            continue

        test_name = row["Test"].strip()
        unit = row["Unit"].strip()
        date_str = row["Date"].strip()

        # Map to canonical metric name
        if test_name in TEST_NAME_MAP:
            metric = TEST_NAME_MAP[test_name]
        else:
            safe_name = test_name.lower().replace(" ", "_")
            safe_unit = unit.lower().replace("/", "_").replace(" ", "_")
            metric = f"{safe_name}_{safe_unit}" if safe_unit else safe_name

        recorded_at = datetime.strptime(date_str, "%Y-%m-%d")

        results.append({
            "source": "blood_panel",
            "metric": metric,
            "value": value,
            "unit": unit,
            "recorded_at": recorded_at,
        })

    return results
