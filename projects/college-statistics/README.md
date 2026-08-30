# College Statistics

A simple static GitHub Pages explorer for comparing universities and bachelor's programs using public College Scorecard data.

## Current scope

The live site currently covers a 10-university U.S. pilot.

It shows:

- university name, location, in-state tuition, and acceptance rate;
- bachelor's programs by 4-digit CIP field of study;
- 1-year and 4-year median earnings where College Scorecard publishes them;
- a university-card summary called **Median across bachelor's programs**, calculated from that university's available 1-year program earnings.

Missing values are shown as `—`; they are not estimated.

## How the site is organized

- `index.html` — page structure
- `css/` — project styling
- `js/app.js` — rendering and interaction
- `js/api.js` — loads and joins browser-ready JSON
- `js/filters.js` and `js/search.js` — filtering/search
- `data/` — live browser-ready JSON
- `data/imported/` — dated source snapshots used for validation/debugging
- `config/` — seed university list
- `scripts/` — College Scorecard import, validation, and promotion scripts
- `docs/` — concise data/source/ingestion/roadmap notes

## Data flow

```text
College Scorecard API
        ↓
dated staging snapshots
        ↓
validation
        ↓
bachelor's-only promotion
        ↓
live JSON in data/
        ↓
GitHub Pages frontend
```

The GitHub Action in `.github/workflows/college-scorecard-seed.yml` runs this pipeline and commits refreshed data back to `main`.

## Important interpretation notes

- Earnings are indicators from College Scorecard field-of-study data, not guaranteed salaries for every graduate.
- The site keeps 1-year and 4-year earnings separate.
- In-state tuition is shown when available.
- Acceptance rate and tuition are institution-level values.
- The university-card earnings number is derived from program-level data; it is not a separate official university-wide earnings metric.
- Employment rates and rankings are not currently shown because there is no simple, consistent source in the present pipeline.

## Local development

Because the app loads JSON with `fetch()`, run it through a local HTTP server rather than opening `index.html` directly from the filesystem.

The project intentionally stays static and simple. Scale the university list and data coverage before adding more architecture.