#!/usr/bin/env python3
"""Summarize a staged College Scorecard program import into a small diagnostic JSON."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def load(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write(path: Path, payload) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def is_present(value):
    return value not in (None, "", "PrivacySuppressed", "NA")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot_dir", type=Path)
    args = parser.parse_args()

    programs = load(args.snapshot_dir / "programs.json")
    key_counts = Counter()
    non_null_key_counts = Counter()
    university_counts = Counter()
    title_counts = Counter()
    credential_counts = Counter()
    normalized_non_null = Counter()
    example_by_university = {}
    key_examples = defaultdict(list)

    for row in programs:
        university_counts[row.get("university_name") or row.get("university_id")] += 1
        title_counts[row.get("title")] += 1
        credential_counts[str(row.get("credential_level"))] += 1
        for field in ("median_earnings", "median_debt", "annual_completions"):
            if is_present(row.get(field)):
                normalized_non_null[field] += 1

        source = row.get("source_payload") or {}
        for key, value in source.items():
            key_counts[key] += 1
            if is_present(value):
                non_null_key_counts[key] += 1
                if len(key_examples[key]) < 3:
                    key_examples[key].append(value)

        ukey = row.get("university_name") or row.get("university_id")
        if ukey not in example_by_university:
            example_by_university[ukey] = {
                "program_id": row.get("program_id"),
                "cip4_code": row.get("cip4_code"),
                "title": row.get("title"),
                "credential_level": row.get("credential_level"),
                "median_earnings": row.get("median_earnings"),
                "median_debt": row.get("median_debt"),
                "annual_completions": row.get("annual_completions"),
                "source_payload": source,
            }

    interesting_tokens = ("earn", "debt", "count", "award", "cred", "cip", "title")
    interesting_keys = [
        key for key in key_counts
        if any(token in key.lower() for token in interesting_tokens)
    ]
    interesting_keys.sort()

    diagnostic = {
        "program_count": len(programs),
        "normalized_non_null_counts": dict(normalized_non_null),
        "program_counts_by_university": dict(university_counts),
        "credential_counts": dict(credential_counts),
        "interesting_source_fields": {
            key: {
                "rows_containing_key": key_counts[key],
                "non_null_rows": non_null_key_counts[key],
                "examples": key_examples[key],
            }
            for key in interesting_keys
        },
        "all_source_field_names": sorted(key_counts),
        "sample_program_by_university": example_by_university,
    }
    write(args.snapshot_dir / "diagnostics.json", diagnostic)
    print(f"Wrote diagnostics for {len(programs)} programs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
