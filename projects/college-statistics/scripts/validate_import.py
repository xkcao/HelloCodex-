#!/usr/bin/env python3
"""Validate one staged College Scorecard snapshot before promotion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot_dir", type=Path)
    args = parser.parse_args()

    base = args.snapshot_dir
    required_files = ["manifest.json", "universities.json", "tuition.json", "admissions.json", "raw.json"]
    errors: list[str] = []
    for name in required_files:
        require((base / name).exists(), f"Missing {name}", errors)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    universities = load(base / "universities.json")
    tuition = load(base / "tuition.json")
    admissions = load(base / "admissions.json")
    manifest = load(base / "manifest.json")

    ids = [row.get("university_id") for row in universities]
    require(len(ids) == len(set(ids)), "Duplicate university_id values", errors)
    require(len(universities) == manifest.get("seed_count"), "University count does not match manifest seed_count", errors)

    known = set(ids)
    for row in universities:
        uid = row.get("university_id")
        require(isinstance(uid, str) and uid.startswith("us-ipeds-"), f"Invalid university_id: {uid}", errors)
        require(bool(row.get("name")), f"Missing university name for {uid}", errors)
        require(row.get("country") == "US", f"Unexpected country for {uid}", errors)
        require(bool((row.get("external_ids") or {}).get("ipeds_unitid")), f"Missing IPEDS UNITID for {uid}", errors)
        require(row.get("source") == "College Scorecard", f"Unexpected university source for {uid}", errors)

    for dataset_name, rows in (("tuition", tuition), ("admissions", admissions)):
        for row in rows:
            uid = row.get("university_id")
            require(uid in known, f"{dataset_name} references unknown university_id {uid}", errors)
            require(row.get("source") == "College Scorecard", f"Unexpected {dataset_name} source for {uid}", errors)
            require("year" in row, f"{dataset_name} missing year field for {uid}", errors)

    for row in tuition:
        require(row.get("residency") in {"in_state", "out_of_state"}, f"Invalid tuition residency for {row.get('university_id')}", errors)
        value = row.get("tuition")
        require(isinstance(value, (int, float)) and value >= 0, f"Invalid tuition value for {row.get('university_id')}", errors)

    for row in admissions:
        value = row.get("acceptance_rate")
        require(value is None or (isinstance(value, (int, float)) and 0 <= value <= 100), f"Invalid acceptance rate for {row.get('university_id')}", errors)

    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validation passed for {len(universities)} universities in {base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
