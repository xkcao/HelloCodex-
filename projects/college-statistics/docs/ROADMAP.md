# Roadmap

## Phase 1 — Static prototype
- Normalized placeholder data
- Modular frontend architecture
- Search and filters
- Data model and source documentation

## Phase 2 — Top 100 U.S. universities
- Define an explicit inclusion/ranking methodology
- Add stable official institution identifiers
- Populate verified institution, admissions, tuition, major, salary, and employment data where available
- Add provenance and validation checks

## Phase 3 — Top 500 universities
- Expand ingestion and validation tooling
- Introduce chunked/lazy-loaded datasets if browser payload size requires it
- Add comparison and detail-page routes

## Phase 4 — All accredited U.S. universities
- Use authoritative institution universe
- Expand program/CIP coverage
- Support state/residency-specific tuition and broader outcome coverage

## Phase 5 — International expansion
- Add country-aware identifiers, currencies, degree systems, and admissions fields
- Keep shared core entities while allowing country-specific extensions

## Phase 6 — Annual automated updates
- Build scheduled ETL outside GitHub Pages
- Validate source changes and schema compatibility
- Preserve historical records
- Publish generated static JSON artifacts to the site

## Architecture checkpoints
At each phase, measure total JSON payload, parse/join time, search latency, and browser memory. Move from eager loading to dataset manifests/chunks before scale becomes a user-visible problem.
