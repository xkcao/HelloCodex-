#!/usr/bin/env python3
"""Validate a staged College Scorecard field-of-study snapshot."""

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
    for name in ("manifest.json", "programs.json", "raw.json"):
        if not (base / name).exists():
            errors.append(f"Missing {name}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    manifest = load(base / "manifest.json")
    programs = load(base / "programs.json")

    if manifest.get("program_count") != len(programs):
        errors.append("program_count does not match programs.json length")
    if not programs:
        errors.append("No field-of-study records were imported")

    seen = set()
    for index, row in enumerate(programs):
        uid = row.get("university_id")
        cip = row.get("cip4_code")
        credential = row.get("credential_level")
        title = row.get("title")
        if not isinstance(uid, str) or not uid.startswith("us-ipeds-"):
            errors.append(f"Row {index}: invalid university_id")
        if not cip:
            errors.append(f"Row {index}: missing CIP4 code")
        if credential is None:
            errors.append(f"Row {index}: missing credential level")
        if not title:
            errors.append(f"Row {index}: missing program title")
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

    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors[:100]:
            print(f"- {error}", file=sys.stderr)
        if len(errors) > 100:
            print(f"- ... {len(errors) - 100} more errors", file=sys.stderr)
        return 1

    print(f"Validation passed for {len(programs)} field-of-study records in {base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
