#!/usr/bin/env python3
"""Import College Scorecard field-of-study data from the official bulk download.

The field-of-study bulk file is preferable to per-school API calls for scaling.
This script filters that file to the configured seed UNITIDs and writes a staged,
source-preserving normalized snapshot.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEED = ROOT / "config" / "scorecard_seed_universities.json"
DEFAULT_OUTPUT_ROOT = ROOT / "data" / "imported" / "college-scorecard-programs"
DOWNLOAD_URL = "https://ed-public-download.scorecard.network/downloads/Most-Recent-Cohorts-Field-of-Study_06102026.zip"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def first_present(record: dict, *keys):
    for key in keys:
        value = record.get(key)
        if value not in (None, "", "PrivacySuppressed", "NA"):
            return value
    return None


def number_or_none(value):
    if value in (None, "", "PrivacySuppressed", "NA"):
        return None
    try:
        if "." in str(value):
            return float(value)
        return int(value)
    except (TypeError, ValueError):
        return value


def normalize_program(row: dict) -> dict:
    unitid = str(first_present(row, "UNITID", "unitid") or "")
    cip = first_present(row, "CIPCODE", "CIPCODE4", "cipcode", "code")
    title = first_present(row, "CIPDESC", "CIPTITLE", "cipdesc", "title")
    credential = first_present(row, "CREDDESC", "CREDLEV", "credential", "credential_level")

    earnings_raw = first_present(
        row,
        "EARN_MDN_1YR",
        "EARN_MDN_4YR",
        "EARN_MDN_HI_1YR",
        "EARN_MDN_LO_1YR",
    )
    debt_raw = first_present(
        row,
        "DEBT_ALL_STGP_ANY_MDN",
        "DEBT_ALL_STGP_EVAL_MDN",
        "DEBT_MDN",
    )
    awards_raw = first_present(row, "IPEDSCOUNT1", "IPEDSCOUNT2", "IPEDSCOUNT", "COUNT_ED")

    uid = f"us-ipeds-{unitid}"
    cip_text = str(cip) if cip is not None else None
    credential_text = str(credential) if credential is not None else None
    program_id = None
    if cip_text and credential_text:
        safe_cred = credential_text.lower().replace(" ", "-").replace("/", "-")
        program_id = f"{uid}-cip4-{cip_text}-cred-{safe_cred}"

    return {
        "program_id": program_id,
        "university_id": uid,
        "university_name": first_present(row, "INSTNM", "institution_name"),
        "cip4_code": cip_text,
        "title": title,
        "credential_level": credential,
        "median_earnings": number_or_none(earnings_raw),
        "median_debt": number_or_none(debt_raw),
        "annual_completions": number_or_none(awards_raw),
        "source": "College Scorecard",
        "source_release": "Most Recent Data by Field of Study (2026-06-10 release)",
        "metric_year": None,
        "population_note": "Field-of-study earnings and debt measures derived from federal aid/tax records describe federally aided students and should not automatically be generalized to all graduates.",
        "source_payload": row,
    }


def download_csv_rows(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "HelloCodex-College-Statistics/1.0"})
    with urllib.request.urlopen(request, timeout=180) as response:
        archive_bytes = response.read()
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if not csv_names:
            raise RuntimeError("No CSV file found in College Scorecard field-of-study ZIP")
        # The official most-recent archive currently contains one primary CSV.
        csv_name = max(csv_names, key=lambda name: archive.getinfo(name).file_size)
        with archive.open(csv_name) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            reader = csv.DictReader(text)
            for row in reader:
                yield csv_name, row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--snapshot", default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    parser.add_argument("--download-url", default=DOWNLOAD_URL)
    args = parser.parse_args()

    seeds = load_json(args.seed)
    wanted = {str(seed["unitid"]) for seed in seeds}
    matched_rows = []
    csv_name = None

    print("Downloading official College Scorecard Most Recent Data by Field of Study ZIP")
    for current_csv, row in download_csv_rows(args.download_url):
        csv_name = current_csv
        unitid = str(row.get("UNITID") or row.get("unitid") or "")
        if unitid in wanted:
            matched_rows.append(row)

    found_unitids = {str(row.get("UNITID") or row.get("unitid") or "") for row in matched_rows}
    missing = sorted(wanted - found_unitids)
    if missing:
        print(f"Warning: no field-of-study rows found for UNITIDs: {', '.join(missing)}")

    programs = [normalize_program(row) for row in matched_rows]
    output_dir = args.output_root / args.snapshot
    retrieved_at = dt.datetime.now(dt.timezone.utc).isoformat()

    write_json(output_dir / "raw.json", {
        "source": "College Scorecard Most Recent Data by Field of Study",
        "download_url": args.download_url,
        "archive_csv": csv_name,
        "retrieved_at": retrieved_at,
        "records": matched_rows,
    })
    write_json(output_dir / "programs.json", programs)
    write_json(output_dir / "manifest.json", {
        "source": "College Scorecard Field of Study",
        "source_url": "https://collegescorecard.ed.gov/data/",
        "download_url": args.download_url,
        "retrieved_at": retrieved_at,
        "snapshot": args.snapshot,
        "seed_count": len(seeds),
        "program_count": len(programs),
        "unitids": sorted(wanted),
        "unitids_with_program_rows": sorted(found_unitids),
        "unit_of_analysis": "IPEDS UNITID + four-digit CIP code + credential level",
        "year_policy": "metric_year remains null until each metric is mapped to its documented cohort/reporting period; the most-recent file may combine metrics from different underlying periods.",
        "promotion_status": "staging-only",
    })
    print(f"Wrote {len(programs)} staged program records to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
