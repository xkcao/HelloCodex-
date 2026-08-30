# College Statistics

A static GitHub Pages project designed as a scalable, data-first college and major statistics explorer.

## Architecture

- `index.html` — semantic UI shell only
- `css/main.css` — global layout and visual foundations
- `css/components.css` — dashboard component styles
- `js/app.js` — application orchestration/rendering
- `js/api.js` — independent data loading and joins
- `js/filters.js` — filter logic
- `js/search.js` — search logic
- `js/router.js` — reserved detail-page routing boundary
- `js/charts.js` — reserved chart boundary
- `js/compare.js` — reserved comparison boundary
- `js/utils.js` — shared formatting/statistical helpers
- `data/` — normalized, independently replaceable datasets
- `config/` — seed/configuration files for repeatable imports
- `scripts/` — source ingestion and validation scripts
- `assets/` — project-local logos/icons
- `docs/` — data model, sources, ingestion, and roadmap

## Data status

The live dashboard still uses fictional placeholder records. They demonstrate the schema and preserve the current prototype experience; they are not real university statistics.

A first real-data staging pipeline now exists for U.S. Department of Education College Scorecard institution data. It intentionally writes to `data/imported/` rather than replacing the live files until the imported records and related major/outcome joins are validated.

## First ingestion pipeline

The seed pipeline covers 10 U.S. universities identified by IPEDS UNITID and normalizes institution identity, tuition, and admissions fields.

```bash
export COLLEGE_SCORECARD_API_KEY="your-key-here"
python3 scripts/scorecard_import.py
python3 scripts/validate_import.py data/imported/college-scorecard/YYYY-MM-DD
```

Do not commit API keys. See `docs/INGESTION.md` for the staging and promotion rules.

## Design principles

1. Stable IDs instead of joining on names.
2. Universities and majors are independent entities connected by a relationship dataset.
3. Salary, employment, tuition, admissions, and rankings remain separate facts with source/year metadata.
4. No business logic lives in HTML.
5. Missing production data should be `null`, never guessed.
6. The browser-facing schema should remain stable even when future ETL/source pipelines change.
7. Historical records should be appended by year rather than overwritten.
8. Source data should be imported reproducibly and validated before promotion to live JSON.

See `docs/DATA_MODEL.md`, `docs/DATA_SOURCES.md`, `docs/INGESTION.md`, and `docs/ROADMAP.md` before adding production data.

## Local development

The project loads JSON with `fetch()`, so run it through an HTTP server rather than opening `index.html` directly from the filesystem. GitHub Pages serves it correctly without a backend.
