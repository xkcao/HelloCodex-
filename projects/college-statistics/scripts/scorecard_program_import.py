#!/usr/bin/env python3
"""Fetch College Scorecard field-of-study data for the seed universities.

This is a staging importer. It preserves the source program payload while exposing
stable institution + CIP4 + credential identifiers for later normalization.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "https://api.data.gov/ed/collegescorecard/v1/schools.json"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEED = ROOT / "config" / "scorecard_seed_universities.json"
DEFAULT_OUTPUT_ROOT = ROOT / "data" / "imported" / "college-scorecard-programs"
DEMO_KEY = "DEMO_KEY"
PROGRAM_FIELD = "latest.programs.cip_4_digit"
FIELDS = ["id", "school.name", PROGRAM_FIELD]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def fetch_school(unitid: str, api_key: str) -> dict:
    params = {"id": unitid, "_fields": ",".join(FIELDS), "api_key": api_key}
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "HelloCodex-College-Statistics/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.load(response)
    results = payload.get("results", [])
    if len(results) != 1:
        raise RuntimeError(f"Expected one Scorecard result for UNITID {unitid}; got {len(results)}")
    return results[0]


def value(record: dict, key: str):
    if key in record:
        return record[key]
    current = record
    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def first_present(record: dict, *keys):
    for key in keys:
        if key in record and record[key] is not None:
            return record[key]
    return None


def normalize_program(unitid: str, school_name: str | None, program: dict) -> dict:
    cip = first_present(program, "code", "cip_code", "cipcode")
    credential = first_present(program, "credential.level", "credential_level", "credential")
    title = first_present(program, "title", "cip_title")

    # Scorecard has changed earnings labels over time. Keep a conservative set of
    # aliases and retain source_payload so new source fields are never discarded.
    median_earnings = first_present(
        program,
        "earnings.median_earnings",
        "earnings.1_yr.overall_median_earnings",
        "earnings.1_yr.earnings_median",
    )
    median_debt = first_present(
        program,
        "debt.median_debt",
        "debt.all.all_inst.median",
        "debt.median_debt.completers.overall",
    )

    uid = f"us-ipeds-{unitid}"
    cip_text = str(cip) if cip is not None else None
    credential_text = str(credential) if credential is not None else None
    program_id = None
    if cip_text and credential_text:
        program_id = f"{uid}-cip4-{cip_text}-cred-{credential_text}"

    return {
        "program_id": program_id,
        "university_id": uid,
        "university_name": school_name,
        "cip4_code": cip_text,
        "title": title,
        "credential_level": credential,
        "median_earnings": median_earnings,
        "median_debt": median_debt,
        "source": "College Scorecard",
        "source_release": "latest",
        "metric_year": None,
        "population_note": "Earnings and debt metrics by field of study describe federally aided students when derived from federal aid/tax records; they should not be assumed to represent all graduates.",
        "source_payload": program,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--snapshot", default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    parser.add_argument("--api-key", default=None)
    args = parser.parse_args()

    api_key = args.api_key or os.getenv("COLLEGE_SCORECARD_API_KEY") or DEMO_KEY
    seeds = load_json(args.seed)
    raw_records = []
    programs = []

    for seed in seeds:
        unitid = str(seed["unitid"])
        print(f"Fetching field-of-study data for {unitid} — {seed['name']}")
        school = fetch_school(unitid, api_key)
        raw_records.append(school)
        school_name = value(school, "school.name")
        source_programs = value(school, PROGRAM_FIELD) or []
        if not isinstance(source_programs, list):
            raise RuntimeError(f"Expected {PROGRAM_FIELD} list for UNITID {unitid}")
        for program in source_programs:
            if isinstance(program, dict):
                programs.append(normalize_program(unitid, school_name, program))

    output_dir = args.output_root / args.snapshot
    retrieved_at = dt.datetime.now(dt.timezone.utc).isoformat()
    write_json(output_dir / "raw.json", {
        "source": "College Scorecard",
        "endpoint": BASE_URL,
        "retrieved_at": retrieved_at,
        "fields": FIELDS,
        "records": raw_records,
    })
    write_json(output_dir / "programs.json", programs)
    write_json(output_dir / "manifest.json", {
        "source": "College Scorecard Field of Study",
        "source_url": "https://collegescorecard.ed.gov/data/",
        "retrieved_at": retrieved_at,
        "snapshot": args.snapshot,
        "seed_count": len(seeds),
        "program_count": len(programs),
        "unitids": [str(seed["unitid"]) for seed in seeds],
        "unit_of_analysis": "IPEDS UNITID + four-digit CIP code + credential level",
        "year_policy": "metric_year remains null until each metric is mapped to its documented cohort/reporting period; 'latest' must not be treated as a single calendar year.",
        "promotion_status": "staging-only",
    })
    print(f"Wrote {len(programs)} staged program records to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
