#!/usr/bin/env python3
"""Import College Scorecard field-of-study data for the seed universities.

Uses one batched API request for all configured UNITIDs and preserves each raw
program payload while exposing stable institution + CIP4 + credential identities.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL="https://api.data.gov/ed/collegescorecard/v1/schools.json"
ROOT=Path(__file__).resolve().parents[1]
DEFAULT_SEED=ROOT/"config"/"scorecard_seed_universities.json"
DEFAULT_OUTPUT_ROOT=ROOT/"data"/"imported"/"college-scorecard-programs"
DEMO_KEY="DEMO_KEY"
PROGRAM_FIELD="latest.programs.cip_4_digit"
FIELDS=["id","school.name",PROGRAM_FIELD]

def load_json(path:Path):
    with path.open("r",encoding="utf-8") as h:return json.load(h)

def write_json(path:Path,payload):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8") as h:json.dump(payload,h,indent=2,ensure_ascii=False);h.write("\n")

def value(record,key):
    if key in record:return record[key]
    cur=record
    for part in key.split("."):
        if not isinstance(cur,dict) or part not in cur:return None
        cur=cur[part]
    return cur

def first_present(record,*keys):
    for key in keys:
        if record.get(key) not in (None,"","PrivacySuppressed","NA"):return record[key]
    return None

def number_or_none(v):
    if v in (None,"","PrivacySuppressed","NA"):return None
    try:return float(v) if "." in str(v) else int(v)
    except (TypeError,ValueError):return v

def fetch_schools(unitids,api_key):
    params={"id":",".join(unitids),"_fields":",".join(FIELDS),"_per_page":"100","api_key":api_key}
    url=f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    req=urllib.request.Request(url,headers={"User-Agent":"HelloCodex-College-Statistics/1.0"})
    with urllib.request.urlopen(req,timeout=90) as resp:payload=json.load(resp)
    results=payload.get("results",[])
    returned={str(r.get("id")) for r in results};missing=sorted(set(unitids)-returned)
    if missing:raise RuntimeError(f"Missing Scorecard program results for UNITIDs: {', '.join(missing)}")
    return results

def normalize_program(unitid,school_name,program):
    cip=first_present(program,"code","cip_code","cipcode")
    credential=first_present(program,"credential.level","credential_level","credential")
    title=first_present(program,"title","cip_title")
    earnings=first_present(program,"earnings.median_earnings","earnings.1_yr.overall_median_earnings","earnings.1_yr.earnings_median")
    debt=first_present(program,"debt.median_debt","debt.all.all_inst.median","debt.median_debt.completers.overall")
    awards=first_present(program,"counts.ipeds_awards1","counts.ipeds_awards2","counts.ipeds_awards")
    uid=f"us-ipeds-{unitid}";cip_text=str(cip) if cip is not None else None;cred_text=str(credential) if credential is not None else None
    pid=f"{uid}-cip4-{cip_text}-cred-{cred_text}" if cip_text and cred_text else None
    return {"program_id":pid,"university_id":uid,"university_name":school_name,"cip4_code":cip_text,"title":title,"credential_level":credential,"median_earnings":number_or_none(earnings),"median_debt":number_or_none(debt),"annual_completions":number_or_none(awards),"source":"College Scorecard","source_release":"latest","metric_year":None,"population_note":"Field-of-study earnings and debt metrics derived from federal aid/tax records describe federally aided students and should not automatically be generalized to all graduates.","source_payload":program}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--seed",type=Path,default=DEFAULT_SEED);p.add_argument("--output-root",type=Path,default=DEFAULT_OUTPUT_ROOT);p.add_argument("--snapshot",default=dt.datetime.now(dt.timezone.utc).date().isoformat());p.add_argument("--api-key",default=None);a=p.parse_args()
    seeds=load_json(a.seed);unitids=[str(s["unitid"]) for s in seeds];api_key=a.api_key or os.getenv("COLLEGE_SCORECARD_API_KEY") or DEMO_KEY
    print(f"Fetching field-of-study data for {len(unitids)} universities in one request")
    schools=fetch_schools(unitids,api_key);programs=[]
    for school in schools:
        unitid=str(school["id"]);school_name=value(school,"school.name");source_programs=value(school,PROGRAM_FIELD) or []
        if not isinstance(source_programs,list):raise RuntimeError(f"Expected {PROGRAM_FIELD} list for UNITID {unitid}")
        programs.extend(normalize_program(unitid,school_name,p) for p in source_programs if isinstance(p,dict))
    out=a.output_root/a.snapshot;retrieved=dt.datetime.now(dt.timezone.utc).isoformat()
    write_json(out/"raw.json",{"source":"College Scorecard","endpoint":BASE_URL,"retrieved_at":retrieved,"fields":FIELDS,"records":schools});write_json(out/"programs.json",programs)
    write_json(out/"manifest.json",{"source":"College Scorecard Field of Study","source_url":"https://collegescorecard.ed.gov/data/","retrieved_at":retrieved,"snapshot":a.snapshot,"seed_count":len(seeds),"program_count":len(programs),"unitids":unitids,"request_mode":"batched-unitids","unit_of_analysis":"IPEDS UNITID + four-digit CIP code + credential level","year_policy":"metric_year remains null until each metric is mapped to its documented cohort/reporting period; latest must not be treated as one calendar year.","promotion_status":"staging-only"})
    print(f"Wrote {len(programs)} staged program records to {out}");return 0

if __name__=="__main__":raise SystemExit(main())
