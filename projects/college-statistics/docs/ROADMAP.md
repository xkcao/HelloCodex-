# Roadmap

The project should stay useful and simple. Expand data coverage first; add architecture only when the current static approach becomes limiting.

## Current — 10-university real-data pilot

- Real College Scorecard institution and field-of-study data
- Bachelor's programs only in the live site
- University-first browsing with expandable major tables
- 1-year and 4-year program earnings
- In-state tuition and acceptance rate
- Search and filters
- Automated import, validation, and promotion through GitHub Actions

## Next — roughly 100 U.S. universities

- Define a clear inclusion method for the university list
- Expand the seed/config list
- Reuse the same import and promotion pipeline
- Keep bachelor's-only scope unless another degree level becomes useful
- Check payload size and browsing performance after expansion

The goal is for 10 → 100 schools to be mainly a data/configuration change, not a redesign.

## Later — broader U.S. coverage

If the 100-school version remains useful:

- expand to more institutions;
- improve program coverage and naming where necessary;
- consider additional indicators only when a reliable source exists;
- add chunked data loading only if browser performance actually requires it.

## Optional future features

Possible additions, not commitments:

- university or major comparison views;
- historical earnings/cost trends;
- additional degree levels;
- employment/job-outlook context from a suitable source;
- international universities.

## Guiding rule

Do not build for hypothetical scale too early. Keep GitHub Pages + static JSON as long as it works well, and solve concrete problems one at a time.