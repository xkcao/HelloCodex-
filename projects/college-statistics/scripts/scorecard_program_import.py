#!/usr/bin/env python3
"""Import College Scorecard field-of-study data for the configured seed universities.

Uses one batched API request for all UNITIDs, preserves raw program payloads, and
writes normalized program records plus a compact audit summary.
"""

from __future__ import annotations

import argparse
import collections
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


def nested_value(record: dict, dotted_key: str):
    if dotted_key in record:
        return record[dotted_key]
    current = record
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def first_value(record: dict, *paths):
    for path in paths:
        candidate = nested_value(record, path)
        if candidate not in (None, "", "PrivacySuppressed", "NA"):
            return candidate
    return None


def number_or_none(candidate):
    if candidate in (None, "", "PrivacySuppressed", "NA"):
        return None
    try:
        return float(candidate) if "." in str(candidate) else int(candidate)
    except (TypeError, ValueError):
        return candidate


def fetch_schools(unitids: list[str], api_key: str) -> list[dict]:
    params = {
        "id": ",".join(unitids),
        "_fields": ",".join(FIELDS),
        "_per_page": "100",
        "api_key": api_key,
    }
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url, headers={"User-Agent": "HelloCodex-College-Statistics/1.0"}
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.load(response)
    results = payload.get("results", [])
    returned = {str(record.get("id")) for record in results}
    missing = sorted(set(unitids) - returned)
    if missing:
        raise RuntimeError(
            f"Missing Scorecard program results for UNITIDs: {', '.join(missing)}"
        )
    return results


def credential_parts(program: dict) -> tuple[int | str | None, str | None]:
    credential = nested_value(program, "credential")
    if isinstance(credential, dict):
        return credential.get("level"), credential.get("title")
    return (
        first_value(program, "credential.level", "credential_level"),
        first_value(program, "credential.title", "credential_title"),
    )


def normalize_program(unitid: str, school_name: str | None, program: dict) -> dict:
    cip = first_value(program, "code", "cip_code", "cipcode")
    credential_level, credential_title = credential_parts(program)
    title = first_value(program, "title", "cip_title")

    earnings_1yr = number_or_none(
        first_value(program, "earnings.1_yr.overall_median_earnings")
    )
    earnings_4yr = number_or_none(
        first_value(program, "earnings.4_yr.overall_median_earnings")
    )
    earnings_5yr = number_or_none(
        first_value(program, "earnings.5_yr.overall_median_earnings")
    )
    student_debt = number_or_none(
        first_value(program, "debt.staff_grad_plus.all.all_inst.median")
    )
    awards_1 = number_or_none(first_value(program, "counts.ipeds_awards1"))
    awards_2 = number_or_none(first_value(program, "counts.ipeds_awards2"))

    uid = f"us-ipeds-{unitid}"
    cip_text = str(cip) if cip is not None else None
    credential_id = str(credential_level) if credential_level is not None else None
    program_id = (
        f"{uid}-cip4-{cip_text}-cred-{credential_id}"
        if cip_text and credential_id
        else None
    )

    return {
        "program_id": program_id,
        "university_id": uid,
        "university_name": school_name,
        "cip4_code": cip_text,
        "title": title,
        "credential_level": credential_level,
        "credential_title": credential_title,
        "median_earnings_1yr": earnings_1yr,
        "median_earnings_4yr": earnings_4yr,
        "median_earnings_5yr": earnings_5yr,
        "median_student_debt": student_debt,
        "ipeds_awards_count_1": awards_1,
        "ipeds_awards_count_2": awards_2,
        "source": "College Scorecard",
        "source_release": "latest",
        "metric_year": None,
        "population_note": (
            "Field-of-study earnings/debt measures based on federal aid/tax records "
            "describe covered students and should not automatically be generalized "
            "to all graduates."
        ),
        "source_payload": program,
    }


def compact_record(row: dict) -> dict:
    return {
        key: row.get(key)
        for key in (
            "program_id",
            "university_id",
            "university_name",
            "cip4_code",
            "title",
            "credential_level",
            "credential_title",
            "median_earnings_1yr",
            "median_earnings_4yr",
            "median_earnings_5yr",
            "median_student_debt",
            "ipeds_awards_count_1",
            "ipeds_awards_count_2",
        )
    }


def flatten_key_paths(obj, prefix="") -> set[str]:
    paths: set[str] = set()
    if isinstance(obj, dict):
        for key, child in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            paths.add(path)
            paths.update(flatten_key_paths(child, path))
    elif isinstance(obj, list) and obj:
        paths.update(flatten_key_paths(obj[0], prefix))
    return paths


def build_audit(programs: list[dict], unitids: list[str]) -> dict:
    by_university = collections.Counter(row["university_id"] for row in programs)
    by_credential = collections.Counter(
        f"{row.get('credential_level')} - {row.get('credential_title')}" for row in programs
    )
    unique_ids = {row.get("program_id") for row in programs if row.get("program_id")}
    unique_cips = {row.get("cip4_code") for row in programs if row.get("cip4_code")}
    source_paths: set[str] = set()
    for row in programs[:100]:
        source_paths.update(flatten_key_paths(row.get("source_payload", {})))

    return {
        "program_count": len(programs),
        "unique_program_id_count": len(unique_ids),
        "unique_cip4_count": len(unique_cips),
        "university_count": len(by_university),
        "expected_university_count": len(unitids),
        "records_with_earnings_1yr": sum(row.get("median_earnings_1yr") is not None for row in programs),
        "records_with_earnings_4yr": sum(row.get("median_earnings_4yr") is not None for row in programs),
        "records_with_earnings_5yr": sum(row.get("median_earnings_5yr") is not None for row in programs),
        "records_with_student_debt": sum(row.get("median_student_debt") is not None for row in programs),
        "records_with_ipeds_awards_1": sum(row.get("ipeds_awards_count_1") is not None for row in programs),
        "records_with_ipeds_awards_2": sum(row.get("ipeds_awards_count_2") is not None for row in programs),
        "records_missing_program_id": sum(not row.get("program_id") for row in programs),
        "records_by_university": dict(sorted(by_university.items())),
        "records_by_credential_level": dict(sorted(by_credential.items())),
        "source_field_paths_sample": sorted(source_paths),
        "sample_records": [compact_record(row) for row in programs[:20]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--snapshot", default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    parser.add_argument("--api-key", default=None)
    args = parser.parse_args()

    seeds = load_json(args.seed)
    unitids = [str(seed["unitid"]) for seed in seeds]
    api_key = args.api_key or os.getenv("COLLEGE_SCORECARD_API_KEY") or DEMO_KEY

    print(f"Fetching field-of-study data for {len(unitids)} universities in one request")
    schools = fetch_schools(unitids, api_key)
    programs: list[dict] = []
    for school in schools:
        unitid = str(school["id"])
        school_name = nested_value(school, "school.name")
        source_programs = nested_value(school, PROGRAM_FIELD) or []
        if not isinstance(source_programs, list):
            raise RuntimeError(f"Expected {PROGRAM_FIELD} list for UNITID {unitid}")
        programs.extend(
            normalize_program(unitid, school_name, program)
            for program in source_programs
            if isinstance(program, dict)
        )

    output_dir = args.output_root / args.snapshot
    retrieved_at = dt.datetime.now(dt.timezone.utc).isoformat()
    audit = build_audit(programs, unitids)

    write_json(output_dir / "raw.json", {
        "source": "College Scorecard",
        "endpoint": BASE_URL,
        "retrieved_at": retrieved_at,
        "fields": FIELDS,
        "records": schools,
    })
    write_json(output_dir / "programs.json", programs)
    write_json(output_dir / "audit.json", audit)
    write_json(output_dir / "manifest.json", {
        "source": "College Scorecard Field of Study",
        "source_url": "https://collegescorecard.ed.gov/data/",
        "retrieved_at": retrieved_at,
        "snapshot": args.snapshot,
        "seed_count": len(seeds),
        "program_count": len(programs),
        "unitids": unitids,
        "request_mode": "batched-unitids",
        "unit_of_analysis": "IPEDS UNITID + four-digit CIP code + credential level",
        "year_policy": "Metric-specific cohort/reporting years remain unresolved in this staging snapshot; latest is not treated as one calendar year.",
        "promotion_status": "staging-only",
        "generated_files": ["programs.json", "raw.json", "audit.json"],
    })

    print(
        f"Wrote {len(programs)} staged records; "
        f"1yr earnings={audit['records_with_earnings_1yr']}, "
        f"4yr earnings={audit['records_with_earnings_4yr']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
