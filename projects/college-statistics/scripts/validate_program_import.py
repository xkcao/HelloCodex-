#!/usr/bin/env python3
"""Validate a staged College Scorecard field-of-study snapshot and audit summary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot_dir", type=Path)
    args = parser.parse_args()

    base = args.snapshot_dir
    errors: list[str] = []
    for name in ("manifest.json", "programs.json", "raw.json", "audit.json"):
        if not (base / name).exists():
            errors.append(f"Missing {name}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    manifest = load(base / "manifest.json")
    programs = load(base / "programs.json")
    audit = load(base / "audit.json")

    if manifest.get("program_count") != len(programs):
        errors.append("manifest program_count does not match programs.json length")
    if audit.get("program_count") != len(programs):
        errors.append("audit program_count does not match programs.json length")
    if not programs:
        errors.append("No field-of-study records were imported")

    seen = set()
    university_ids = set()
    counters = {
        "records_with_earnings_1yr": 0,
        "records_with_earnings_4yr": 0,
        "records_with_earnings_5yr": 0,
        "records_with_student_debt": 0,
        "records_with_ipeds_awards_1": 0,
        "records_with_ipeds_awards_2": 0,
    }

    field_map = {
        "records_with_earnings_1yr": "median_earnings_1yr",
        "records_with_earnings_4yr": "median_earnings_4yr",
        "records_with_earnings_5yr": "median_earnings_5yr",
        "records_with_student_debt": "median_student_debt",
        "records_with_ipeds_awards_1": "ipeds_awards_count_1",
        "records_with_ipeds_awards_2": "ipeds_awards_count_2",
    }

    for index, row in enumerate(programs):
        uid = row.get("university_id")
        cip = row.get("cip4_code")
        credential = row.get("credential_level")
        title = row.get("title")
        program_id = row.get("program_id")

        if not isinstance(uid, str) or not uid.startswith("us-ipeds-"):
            errors.append(f"Row {index}: invalid university_id")
        else:
            university_ids.add(uid)
        if not cip:
            errors.append(f"Row {index}: missing CIP4 code")
        if credential is None:
            errors.append(f"Row {index}: missing credential level")
        if not isinstance(credential, (int, str)):
            errors.append(f"Row {index}: credential_level must be scalar")
        if not title:
            errors.append(f"Row {index}: missing program title")
        if not program_id:
            errors.append(f"Row {index}: missing program_id")

        key = (uid, str(cip), str(credential))
        if key in seen:
            errors.append(f"Duplicate program identity {key}")
        seen.add(key)

        if row.get("metric_year") is not None:
            errors.append(f"Row {index}: metric_year must remain null until cohort mapping is explicit")
        if row.get("source") != "College Scorecard":
            errors.append(f"Row {index}: unexpected source")
        if not isinstance(row.get("source_payload"), dict):
            errors.append(f"Row {index}: source_payload missing")

        for audit_key, record_key in field_map.items():
            counters[audit_key] += row.get(record_key) is not None

    expected_universities = manifest.get("seed_count")
    if expected_universities is not None and len(university_ids) != expected_universities:
        errors.append(
            f"Expected records for {expected_universities} universities; found {len(university_ids)}"
        )

    if audit.get("unique_program_id_count") != len(seen):
        errors.append("audit unique_program_id_count does not match validated identities")
    if audit.get("university_count") != len(university_ids):
        errors.append("audit university_count does not match programs.json")
    if audit.get("records_missing_program_id") != 0:
        errors.append("audit reports records missing program_id")
    for audit_key, count in counters.items():
        if audit.get(audit_key) != count:
            errors.append(f"audit {audit_key} does not match programs.json")

    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors[:100]:
            print(f"- {error}", file=sys.stderr)
        if len(errors) > 100:
            print(f"- ... {len(errors) - 100} more errors", file=sys.stderr)
        return 1

    print(
        f"Validation passed for {len(programs)} records across {len(university_ids)} universities; "
        f"1yr earnings={counters['records_with_earnings_1yr']}, "
        f"4yr earnings={counters['records_with_earnings_4yr']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
