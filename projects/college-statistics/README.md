# College Statistics

A simple static GitHub Pages explorer for comparing universities and bachelor's programs using public College Scorecard data.

## Current scope

The live site covers a 100-institution U.S. coverage set.

It shows:

- university name, location, in-state tuition, and acceptance rate;
- bachelor's programs by 4-digit CIP field of study;
- 1-year and 4-year median earnings where College Scorecard publishes them;
- a university-card summary called **Median across bachelor's programs**, calculated from that university's available 1-year program earnings.

Missing values are shown as `—`; they are not estimated.

The 100-school set is an inclusion/coverage set, not a displayed ranking. The selector keeps the original seed schools and fills the remaining slots with public/private-nonprofit bachelor's-predominant institutions with at least 3,000 undergraduate students, ordered by lowest available College Scorecard admission rate.

## Project structure

- `index.html` — page structure
- `css/` — styling
- `js/` — loading, search/filtering, and rendering
- `data/` — live browser-ready JSON
- `data/imported/` — compact dated selection, institution, and audit metadata
- `config/` — small base seed list
- `scripts/` — selection, import, validation, and promotion
- `docs/` — concise data/source/ingestion/roadmap notes

There are no placeholder modules or datasets for hypothetical future features. New files should be added only when a real feature needs them.

## Data flow

```text
College Scorecard API
        ↓
100-school selection
        ↓
institution + field-of-study import
        ↓
validation
        ↓
bachelor's-only promotion
        ↓
live JSON in data/
        ↓
GitHub Pages frontend
```

The GitHub Action in `.github/workflows/college-scorecard-seed.yml` runs this pipeline and commits refreshed browser-ready data back to `main`.

## Interpretation notes

- Earnings are indicators from College Scorecard field-of-study data, not guaranteed salaries for every graduate.
- The site keeps 1-year and 4-year earnings separate.
- In-state tuition is shown when available.
- Acceptance rate and tuition are institution-level values.
- The university-card earnings number is derived from program-level data; it is not a separate official university-wide earnings metric.
- Employment rates and rankings are not currently implemented because there is no simple, consistent source in the present pipeline.
- The Top-100 coverage set should not be interpreted as an official ranking.

## Scale and staging

At 100 schools, the temporary field-of-study raw/program snapshots exceed GitHub's 100 MB per-file limit. The workflow validates and promotes those files during the Action run, then commits only compact audit metadata plus the browser-ready JSON needed by the static site.

## Local development

Because the app loads JSON with `fetch()`, run it through a local HTTP server rather than opening `index.html` directly from the filesystem.

The project intentionally stays static and simple. Add more architecture only when the current browser experience or data size creates a concrete problem.
