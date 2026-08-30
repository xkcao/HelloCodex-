# Data Ingestion

The first production-data pipeline uses the U.S. Department of Education College Scorecard API as a staging source for institution-level records.

## Why staging first

The live website still uses fictional placeholder records because its current table also depends on major-level salary and employment data. Replacing only the university rows would break those joins. Real source data is therefore imported into `data/imported/college-scorecard/<snapshot>/` first, validated, and promoted to the live datasets only when the related records are ready.

## Seed set

`config/scorecard_seed_universities.json` contains 10 institutions identified by IPEDS UNITID. These are not a permanent "top 10" ranking. They are a small test set for proving IDs, source mappings, null handling, validation, and repeatable updates before scaling to 100+ schools.

## Authentication

For the small 10-school seed import, the script defaults to api.data.gov's public `DEMO_KEY`. This is intended only for initial exploration and has much lower rate limits than a personal key.

Run the seed import with no setup:

```bash
python3 scripts/scorecard_import.py
```

For repeated runs or larger datasets, obtain your own api.data.gov key and keep it out of the repository:

```bash
export COLLEGE_SCORECARD_API_KEY="your-key-here"
python3 scripts/scorecard_import.py
```

You can also override the key for a single run with `--api-key`. Never commit a personal API key.

## Fetch

From `projects/college-statistics/` run:

```bash
python3 scripts/scorecard_import.py
```

The importer uses the API's `latest` institution-level fields and writes a dated snapshot containing:

- `raw.json` — source response retained for audit/debugging
- `universities.json` — normalized university identity records
- `tuition.json` — normalized in-state/out-of-state tuition records
- `admissions.json` — normalized admissions records
- `manifest.json` — retrieval metadata, source URL, selected UNITIDs, API-key mode, and promotion status

Use a fixed snapshot name when reproducing an import:

```bash
python3 scripts/scorecard_import.py --snapshot 2026-08-30
```

## Validate

```bash
python3 scripts/validate_import.py data/imported/college-scorecard/2026-08-30
```

Validation checks stable IDs, duplicate IDs, references, source metadata, tuition values, and acceptance-rate ranges.

## Important year rule

College Scorecard `latest` fields may correspond to different underlying reporting/cohort years. The importer deliberately writes `year: null` rather than inventing a year. Before staged records are promoted into production, map each metric to its correct cohort/reporting year using the official College Scorecard data dictionary and cohort map.

## Stable university IDs

For U.S. institutions imported from Scorecard, the project uses:

```text
us-ipeds-<UNITID>
```

Example: `us-ipeds-166027`.

The federal UNITID is also retained under `external_ids.ipeds_unitid`. This keeps the internal ID globally namespaced while preserving the authoritative source identifier for future joins with IPEDS and other U.S. education datasets.

## Promotion rule

Do not copy staged files directly over the live `data/*.json` files. Promotion should happen only after:

1. validation passes;
2. field/cohort years are resolved;
3. joins to majors and outcome datasets are defined;
4. the frontend has been tested against the new records;
5. source metadata is preserved.

The next milestone is to run this seed import successfully, inspect the real output, and then design the first field-of-study import for majors/outcomes.
