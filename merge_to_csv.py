# merge_to_csv.py
"""
STEP C: Merge all structured DR JSON files into a single CSV
Works on Windows & Linux
"""

import json
from pathlib import Path
import pandas as pd

STRUCTURED_DIR = Path("data/structured")
OUTPUT_DIR = Path("data/analytics")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = OUTPUT_DIR / "defect_reports.csv"


def flatten_record(rec):
    """
    Convert one structured JSON record into a flat dict (1 row)
    """
    row = {}

    row["case_id"] = rec.get("case_id")
    row["source_file"] = rec.get("source_file")
    row["processed_ts"] = rec.get("processed_ts")

    extracted = rec.get("extracted", {})

    for field, obj in extracted.items():

        # life field is nested
        if field == "life" and isinstance(obj.get("value"), dict):
            row["life_hours"] = obj["value"].get("hours")
            row["life_cycles"] = obj["value"].get("cycles")
            continue

        # approvals are nested
        if field == "approvals":
            for role, info in (obj or {}).items():
                if info:
                    row[f"approval_{role}_name"] = info.get("name")
                    row[f"approval_{role}_date"] = info.get("date")
            continue

        # normal fields
        if isinstance(obj, dict):
            row[field] = obj.get("value")
        else:
            row[field] = obj

    return row


def main():
    rows = []

    json_files = sorted(STRUCTURED_DIR.glob("*.json"))
    if not json_files:
        print("No structured JSON files found.")
        return

    for jf in json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            rows.append(flatten_record(data))
        except Exception as e:
            print(f"Skipping {jf.name}: {e}")

    df = pd.DataFrame(rows)

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ CSV created: {OUTPUT_CSV}")
    print(f"Total records: {len(df)}")
    print("\nColumns:")
    print(list(df.columns))


if __name__ == "__main__":
    main()
