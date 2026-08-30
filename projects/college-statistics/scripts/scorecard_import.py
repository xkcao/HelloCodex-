#!/usr/bin/env python3
"""Fetch a small College Scorecard seed set and normalize it into staging JSON.

Uses one batched API request for all configured UNITIDs so the seed workflow remains
well below DEMO_KEY rate limits.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "https://api.data.gov/ed/collegescorecard/v1/schools.json"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEED = ROOT / "config" / "scorecard_seed_universities.json"
DEFAULT_OUTPUT_ROOT = ROOT / "data" / "imported" / "college-scorecard"
DEMO_KEY = "DEMO_KEY"
FIELDS = ["id","school.name","school.city","school.state","school.school_url","school.ownership","latest.student.size","latest.cost.tuition.in_state","latest.cost.tuition.out_of_state","latest.admissions.admission_rate.overall","latest.admissions.sat_scores.average.overall","latest.admissions.act_scores.midpoint.cumulative"]
OWNERSHIP = {1: "Public", 2: "Private nonprofit", 3: "Private for-profit"}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle: return json.load(handle)

def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False); handle.write("\n")

def fetch_schools(unitids: list[str], api_key: str) -> list[dict]:
    params = {"id": ",".join(unitids), "_fields": ",".join(FIELDS), "_per_page": "100", "api_key": api_key}
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent":"HelloCodex-College-Statistics/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response: payload = json.load(response)
    results = payload.get("results", [])
    returned = {str(row.get("id")) for row in results}
    missing = sorted(set(unitids) - returned)
    if missing: raise RuntimeError(f"Missing Scorecard results for UNITIDs: {', '.join(missing)}")
    return results

def field_value(record: dict, dotted_key: str):
    if dotted_key in record: return record[dotted_key]
    current = record
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current: return None
        current = current[part]
    return current

def percent(value): return None if value is None else round(float(value)*100,2)
def university_id(unitid: str) -> str: return f"us-ipeds-{unitid}"

def normalize(records: list[dict]):
    universities, tuition, admissions = [], [], []
    for record in records:
        unitid=str(record["id"]); uid=university_id(unitid); ownership=field_value(record,"school.ownership")
        universities.append({"university_id":uid,"name":field_value(record,"school.name"),"short_name":None,"state":field_value(record,"school.state"),"city":field_value(record,"school.city"),"country":"US","type":OWNERSHIP.get(ownership,"Unknown"),"website":field_value(record,"school.school_url"),"enrollment":field_value(record,"latest.student.size"),"established":None,"logo":None,"external_ids":{"ipeds_unitid":unitid},"source":"College Scorecard"})
        for residency,key in (("in_state","latest.cost.tuition.in_state"),("out_of_state","latest.cost.tuition.out_of_state")):
            value=field_value(record,key)
            if value is not None: tuition.append({"university_id":uid,"tuition":value,"currency":"USD","residency":residency,"source":"College Scorecard","year":None,"source_release":"latest","source_field":key})
        admissions.append({"university_id":uid,"acceptance_rate":percent(field_value(record,"latest.admissions.admission_rate.overall")),"sat_midpoint":field_value(record,"latest.admissions.sat_scores.average.overall"),"act_midpoint":field_value(record,"latest.admissions.act_scores.midpoint.cumulative"),"gpa_average":None,"application_deadline":None,"source":"College Scorecard","year":None,"source_release":"latest"})
    return universities,tuition,admissions

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--seed",type=Path,default=DEFAULT_SEED); parser.add_argument("--output-root",type=Path,default=DEFAULT_OUTPUT_ROOT); parser.add_argument("--snapshot",default=dt.datetime.now(dt.timezone.utc).date().isoformat()); parser.add_argument("--api-key",default=None); args=parser.parse_args()
    api_key=args.api_key or os.getenv("COLLEGE_SCORECARD_API_KEY") or DEMO_KEY; using_demo=api_key==DEMO_KEY
    if using_demo: print("Using api.data.gov DEMO_KEY with one batched seed request.",file=sys.stderr)
    seeds=load_json(args.seed); unitids=[str(seed["unitid"]) for seed in seeds]; print(f"Fetching {len(unitids)} institutions in one request")
    raw_records=fetch_schools(unitids,api_key); universities,tuition,admissions=normalize(raw_records); output_dir=args.output_root/args.snapshot; retrieved_at=dt.datetime.now(dt.timezone.utc).isoformat()
    write_json(output_dir/"raw.json",{"source":"College Scorecard","endpoint":BASE_URL,"retrieved_at":retrieved_at,"fields":FIELDS,"records":raw_records}); write_json(output_dir/"universities.json",universities); write_json(output_dir/"tuition.json",tuition); write_json(output_dir/"admissions.json",admissions)
    write_json(output_dir/"manifest.json",{"source":"College Scorecard","source_url":"https://collegescorecard.ed.gov/data/","retrieved_at":retrieved_at,"snapshot":args.snapshot,"seed_count":len(seeds),"unitids":unitids,"request_mode":"batched-unitids","generated_files":["universities.json","tuition.json","admissions.json","raw.json"],"promotion_status":"staging-only","api_key_mode":"demo" if using_demo else "personal","notes":"Scorecard latest fields can represent different underlying cohort years. Year remains null until mapped from the official data dictionary/cohort map."})
    print(f"Wrote staging snapshot to {output_dir}"); return 0

if __name__=="__main__": raise SystemExit(main())
