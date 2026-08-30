#!/usr/bin/env python3
"""Promote a validated College Scorecard snapshot into website-ready JSON.

Scope stays intentionally simple: bachelor's programs only. One-year median
earnings is the primary earnings indicator when available. Missing values stay null.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write(path: Path, payload):
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot")
    args = parser.parse_args()

    institution_dir = DATA / "imported" / "college-scorecard" / args.snapshot
    program_dir = DATA / "imported" / "college-scorecard-programs" / args.snapshot

    universities = load(institution_dir / "universities.json")
    tuition_rows = load(institution_dir / "tuition.json")
    admissions = load(institution_dir / "admissions.json")
    programs = load(program_dir / "programs.json")

    bachelors = [row for row in programs if row.get("credential_level") == 3]

    major_by_id = {}
    relationships = []
    salaries = []

    for row in bachelors:
        cip = str(row["cip4_code"]).zfill(4)
        major_id = f"cip4-{cip}"
        major_by_id.setdefault(major_id, {
            "major_id": major_id,
            "name": row.get("title") or f"CIP {cip}",
            "category": "College Scorecard field of study",
            "cip_code": cip,
            "stem": None,
            "description": None,
        })
        relationships.append({
            "university_id": row["university_id"],
            "major_id": major_id,
            "credential_level": 3,
            "credential_title": "Bachelor's Degree",
            "available": True,
            "source": "College Scorecard",
        })
        earnings_1yr = row.get("median_earnings_1yr")
        earnings_4yr = row.get("median_earnings_4yr")
        earnings_5yr = row.get("median_earnings_5yr")
        salaries.append({
            "university_id": row["university_id"],
            "major_id": major_id,
            "median_salary": earnings_1yr,
            "earnings_1yr": earnings_1yr,
            "earnings_4yr": earnings_4yr,
            "earnings_5yr": earnings_5yr,
            "currency": "USD",
            "source": "College Scorecard",
            "source_release": "latest",
        })

    tuition_by_university = {}
    for row in tuition_rows:
        uid = row["university_id"]
        current = tuition_by_university.get(uid)
        if current is None or row.get("residency") == "in_state":
            tuition_by_university[uid] = {
                "university_id": uid,
                "tuition": row.get("tuition"),
                "currency": "USD",
                "residency": row.get("residency"),
                "source": "College Scorecard",
            }

    write(DATA / "universities.json", universities)
    write(DATA / "majors.json", sorted(major_by_id.values(), key=lambda r: r["name"]))
    write(DATA / "university-major.json", relationships)
    write(DATA / "salaries.json", salaries)
    write(DATA / "tuition.json", list(tuition_by_university.values()))
    write(DATA / "admissions.json", admissions)

    count = len(universities)
    write(DATA / "metadata.json", {
        "schema_version": "1.2.1",
        "status": "Real federal data",
        "current_year": 2026,
        "countries": ["US"],
        "generated_at": args.snapshot,
        "source": "College Scorecard",
        "scope": f"{count}-university bachelor's-degree coverage set",
        "notes": (
            "Earnings are approximate indicators from College Scorecard. The displayed university "
            "earnings summary is derived from available bachelor's-program values. Tuition shown is "
            "in-state tuition when available. Missing values are left blank. The university set is a "
            "coverage set, not a displayed ranking."
        ),
    })

    populated_1yr = sum(row["earnings_1yr"] is not None for row in salaries)
    populated_4yr = sum(row["earnings_4yr"] is not None for row in salaries)
    print(
        f"Promoted {len(universities)} universities, {len(major_by_id)} majors, "
        f"and {len(relationships)} bachelor's program records; "
        f"1yr earnings={populated_1yr}, 4yr earnings={populated_4yr}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
