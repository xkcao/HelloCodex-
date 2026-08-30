#!/usr/bin/env python3
"""Build a reproducible 100-school College Scorecard coverage set.

This is an inclusion rule, not a published ranking. It keeps the existing seed
institutions, then fills the remaining slots with selective, substantial U.S.
public/private-nonprofit bachelor's-granting institutions using College Scorecard
admission rate as a simple proxy.
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
DEFAULT_BASE_SEED = ROOT / "config" / "scorecard_seed_universities.json"
DEFAULT_OUTPUT_ROOT = ROOT / "data" / "imported" / "college-scorecard-selection"
DEMO_KEY = "DEMO_KEY"
FIELDS = [
    "id",
    "school.name",
    "school.city",
    "school.state",
    "school.ownership",
    "school.degrees_awarded.predominant",
    "latest.student.size",
    "latest.admissions.admission_rate.overall",
]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def value(record: dict, dotted_key: str):
    if dotted_key in record:
        return record[dotted_key]
    current = record
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def fetch_candidates(api_key: str, pages: int = 3) -> list[dict]:
    rows: list[dict] = []
    for page in range(pages):
        params = {
            "school.ownership": "1,2",
            "school.degrees_awarded.predominant": "3",
            "latest.student.size__range": "3000..",
            "latest.admissions.admission_rate.overall__range": "0..1",
            "_fields": ",".join(FIELDS),
            "_sort": "latest.admissions.admission_rate.overall:asc",
            "_per_page": "100",
            "_page": str(page),
            "api_key": api_key,
        }
        url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(
            url, headers={"User-Agent": "HelloCodex-College-Statistics/1.0"}
        )
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.load(response)
        page_rows = payload.get("results", [])
        rows.extend(page_rows)
        if len(page_rows) < 100:
            break
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-seed", type=Path, default=DEFAULT_BASE_SEED)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--snapshot", default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    parser.add_argument("--target", type=int, default=100)
    parser.add_argument("--api-key", default=None)
    args = parser.parse_args()

    if args.target < 1:
        raise SystemExit("target must be positive")

    api_key = args.api_key or os.getenv("COLLEGE_SCORECARD_API_KEY") or DEMO_KEY
    base = load_json(args.base_seed)
    chosen: list[dict] = []
    seen: set[str] = set()

    for row in base:
        unitid = str(row["unitid"])
        if unitid not in seen:
            chosen.append({"unitid": unitid, "name": row["name"], "selection": "base-seed"})
            seen.add(unitid)

    candidates = fetch_candidates(api_key)
    for row in candidates:
        if len(chosen) >= args.target:
            break
        unitid = str(row.get("id"))
        if not unitid or unitid in seen:
            continue
        chosen.append({
            "unitid": unitid,
            "name": value(row, "school.name"),
            "selection": "scorecard-selectivity-proxy",
        })
        seen.add(unitid)

    if len(chosen) != args.target:
        raise RuntimeError(f"Expected {args.target} selected institutions, found {len(chosen)}")

    output_dir = args.output_root / args.snapshot
    write_json(output_dir / "universities.json", chosen)
    write_json(output_dir / "manifest.json", {
        "snapshot": args.snapshot,
        "count": len(chosen),
        "source": "College Scorecard",
        "ranking_status": "coverage-set-not-ranking",
        "method": (
            "Keep configured base seed, then fill to target with public/private-nonprofit "
            "bachelor's-predominant institutions with at least 3,000 undergraduate students, "
            "ordered by lowest available College Scorecard admission rate."
        ),
        "target": args.target,
        "base_seed_count": len(base),
    })
    print(f"Selected {len(chosen)} institutions into {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
