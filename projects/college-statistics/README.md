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
- `assets/` — project-local logos/icons
- `docs/` — data model, sources, and roadmap

## Data status

All current records are fictional placeholders. They demonstrate the schema and preserve the existing prototype experience; they are not real university statistics.

## Design principles

1. Stable IDs instead of joining on names.
2. Universities and majors are independent entities connected by a relationship dataset.
3. Salary, employment, tuition, admissions, and rankings remain separate facts with source/year metadata.
4. No business logic lives in HTML.
5. Missing production data should be `null`, never guessed.
6. The browser-facing schema should remain stable even when future ETL/source pipelines change.
7. Historical records should be appended by year rather than overwritten.

See `docs/DATA_MODEL.md`, `docs/DATA_SOURCES.md`, and `docs/ROADMAP.md` before adding production data.

## Local development

The project loads JSON with `fetch()`, so run it through an HTTP server rather than opening `index.html` directly from the filesystem. GitHub Pages serves it correctly without a backend.
