# Data Ingestion

The College Statistics project uses a small GitHub Actions pipeline to refresh its College Scorecard data.

## Current flow

```text
College Scorecard API
        ↓
100-school coverage selection
        ↓
institution + field-of-study import
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

## Top-100 selection

`select_top100.py` builds a reproducible 100-school coverage set.

It keeps the small configured base seed, then fills remaining slots with College Scorecard institutions that are:

- public or private nonprofit;
- bachelor's-predominant;
- at least 3,000 undergraduate students;
- reporting an admission rate.

Eligible schools are ordered by lowest available College Scorecard admission rate until the target count is reached.

This is an inclusion rule for coverage, not an official ranking and not a rank displayed by the site.

The selected list is stored under:

```text
data/imported/college-scorecard-selection/YYYY-MM-DD/
```

## Institution import

`scorecard_import.py` fetches institution-level data for the selected schools and writes a dated snapshot under:

```text
data/imported/college-scorecard/YYYY-MM-DD/
```

This includes normalized university, tuition, admissions, manifest, and a relatively small institution source response.

## Program import

`scorecard_program_import.py` fetches College Scorecard field-of-study data for the same schools.

The Scorecard unit is institution + 4-digit CIP field + credential level. The temporary import keeps multiple credential levels, but the live website promotes only:

```text
credential_level == 3  # Bachelor's Degree
```

At 100 schools, the temporary raw/program files are larger than GitHub's 100 MB per-file limit. They are therefore generated, validated, summarized, and used during the Action run but are not committed to the repository.

Compact program audit metadata is committed under:

```text
data/imported/college-scorecard-programs-summary/YYYY-MM-DD/
```

## Validation

The validators check basic integrity such as IDs, duplicates, expected institutions, field presence, value ranges, and program outcome coverage.

The goal is not perfect research-grade normalization. The goal is to catch obvious pipeline errors before data reaches the website.

## Promotion

`promote_bachelors.py` converts validated temporary program data into the browser-ready files in `data/`.

Current promotion choices:

- bachelor's programs only;
- 4-digit CIP fields shared across universities;
- 1-year, 4-year, and 5-year earnings retained when available;
- in-state tuition used as the displayed tuition value when available;
- acceptance rate kept at institution level;
- missing values remain `null`;
- employment and rankings are left empty.

## API key

The current workflow can run with api.data.gov's `DEMO_KEY`. A personal key can be supplied through the `COLLEGE_SCORECARD_API_KEY` environment variable or GitHub Actions secret if rate limits become a problem.

Never commit a personal API key.

## Refreshing data

The GitHub Action runs when relevant selection/import/workflow files change and can also be started manually with `workflow_dispatch`.

For local testing from `projects/college-statistics/`, run the same sequence with a chosen snapshot date and the generated selection file.

## Simplicity rule

Keep only what is useful to the static site or to debugging the pipeline. Large raw program payloads are temporary at Top-100 scale; compact audit metadata and browser-ready JSON are enough for the repository.
