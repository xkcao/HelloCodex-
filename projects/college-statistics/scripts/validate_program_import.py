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
    earnings_count = 0
    debt_count = 0
    completions_count = 0

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
        if not title:
            errors.append(f"Row {index}: missing program title")
        if not program_id:
            errors.append(f"Row {index}: missing program_id")

        key = (uid, str(cip), str(credential))
        if key in seen:
            errors.append(f"Duplicate program identity {key}")
        seen.add(key)

        if row.get("metric_year") is not None:
            errors.append(
                f"Row {index}: metric_year must remain null until cohort mapping is explicit"
            )
        if row.get("source") != "College Scorecard":
            errors.append(f"Row {index}: unexpected source")
        if not isinstance(row.get("source_payload"), dict):
            errors.append(f"Row {index}: source_payload missing")

        earnings_count += row.get("median_earnings") is not None
        debt_count += row.get("median_debt") is not None
        completions_count += row.get("annual_completions") is not None

    expected_universities = manifest.get("seed_count")
    if expected_universities is not None and len(university_ids) != expected_universities:
        errors.append(
            f"Expected records for {expected_universities} universities; found {len(university_ids)}"
        )

    if audit.get("unique_program_id_count") != len(seen):
        errors.append("audit unique_program_id_count does not match validated identities")
    if audit.get("university_count") != len(university_ids):
        errors.append("audit university_count does not match programs.json")
    if audit.get("records_with_median_earnings") != earnings_count:
        errors.append("audit earnings count does not match programs.json")
    if audit.get("records_with_median_debt") != debt_count:
        errors.append("audit debt count does not match programs.json")
    if audit.get("records_with_annual_completions") != completions_count:
        errors.append("audit completions count does not match programs.json")
    if audit.get("records_missing_program_id") != 0:
        errors.append("audit reports records missing program_id")

    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors[:100]:
            print(f"- {error}", file=sys.stderr)
        if len(errors) > 100:
            print(f"- ... {len(errors) - 100} more errors", file=sys.stderr)
        return 1

    print(
        f"Validation passed for {len(programs)} field-of-study records across "
        f"{len(university_ids)} universities; {earnings_count} records contain median earnings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
