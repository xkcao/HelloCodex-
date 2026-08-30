# Roadmap

The project should stay useful and simple. Expand data coverage first; add architecture only when the current static approach becomes limiting.

## Current — 100-school real-data coverage

- 100 U.S. institutions selected by a documented, reproducible coverage rule
- Real College Scorecard institution and field-of-study data
- Bachelor's programs only in the live site
- University-first browsing with expandable major tables
- 1-year and 4-year program earnings
- In-state tuition and acceptance rate
- Search and filters
- Automated selection, import, validation, and promotion through GitHub Actions
- Compact repository staging: very large program raw files are validated during the workflow but not committed

The 100-school set is a coverage set, not an official ranking.

## Next — improve the 100-school experience

Before expanding again, use the current site and solve concrete usability/data issues that appear.

Possible near-term work:

- verify that searching/filtering remains comfortable with 100 schools;
- improve school selection methodology only if obvious institutions are missing;
- improve major naming/grouping where 4-digit CIP labels are awkward;
- review missing earnings coverage and clarify labels where needed;
- monitor browser payload and load time.

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
