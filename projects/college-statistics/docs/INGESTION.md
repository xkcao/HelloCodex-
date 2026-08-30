# Data Ingestion

The College Statistics project uses a small GitHub Actions pipeline to refresh its College Scorecard pilot data.

## Current flow

```text
College Scorecard API
        ↓
institution + field-of-study snapshots
        ↓
validation
        ↓
bachelor's-only promotion
        ↓
live JSON in data/
```

The workflow is defined in:

```text
.github/workflows/college-scorecard-seed.yml
```

## Seed universities

`config/scorecard_seed_universities.json` contains 10 institutions identified by IPEDS UNITID.

They are a test set, not a ranking or permanent top-10 list.

## Institution import

`scorecard_import.py` fetches institution-level data and writes a dated snapshot under:

```text
data/imported/college-scorecard/YYYY-MM-DD/
```

This includes raw source data plus normalized university, tuition, admissions, and manifest files.

## Program import

`scorecard_program_import.py` fetches College Scorecard field-of-study data for the same schools and writes:

```text
data/imported/college-scorecard-programs/YYYY-MM-DD/
```

The Scorecard unit is institution + 4-digit CIP field + credential level.

The staging dataset keeps multiple credential levels, but the live website currently promotes only:

```text
credential_level == 3  # Bachelor's Degree
```

## Validation

The validators check basic integrity such as IDs, duplicates, expected institutions, field presence, value ranges, and program outcome coverage.

The goal is not perfect research-grade normalization. The goal is to catch obvious pipeline errors before data reaches the website.

## Promotion

`promote_bachelors.py` converts validated staging data into the small browser-ready files in `data/`.

Current promotion choices:

- bachelor's programs only;
- 4-digit CIP fields shared across universities;
- 1-year, 4-year, and 5-year earnings retained when available;
- in-state tuition used as the displayed tuition value when available;
- acceptance rate kept at institution level;
- missing values remain `null`;
- employment and rankings are left empty.

## API key

For this small seed pipeline, the scripts can use `DEMO_KEY`. A personal api.data.gov key can be supplied through the `COLLEGE_SCORECARD_API_KEY` environment variable or GitHub Actions secret when scaling up.

Never commit a personal API key.

## Refreshing data

The GitHub Action runs when relevant importer/workflow files change and can also be started manually with `workflow_dispatch`.

For local testing from `projects/college-statistics/`, the scripts can also be run directly.

Example:

```bash
python3 scripts/scorecard_import.py --snapshot 2026-08-30
python3 scripts/validate_import.py data/imported/college-scorecard/2026-08-30
python3 scripts/scorecard_program_import.py --snapshot 2026-08-30
python3 scripts/validate_program_import.py data/imported/college-scorecard-programs/2026-08-30
python3 scripts/promote_bachelors.py 2026-08-30
```

## Simplicity rule

Staging can stay detailed for debugging, but the live website data should remain small and understandable. Do not add another transformation layer unless scaling or a concrete feature requires it.