# Data Sources

## Current production source

The live College Statistics site uses the U.S. Department of Education **College Scorecard**.

Current uses:

- institution identity and location;
- in-state tuition;
- acceptance rate;
- field-of-study / CIP program records;
- 1-year, 4-year, and 5-year median earnings where available.

The frontend currently displays 1-year and 4-year program earnings.

## Top-100 coverage rule

The current 100-school set is a practical coverage set, not an official ranking.

The selector keeps the small configured base seed, then fills remaining slots with public/private-nonprofit, bachelor's-predominant institutions with at least 3,000 undergraduate students, ordered by lowest available College Scorecard admission rate.

The selection rule is deliberately simple and reproducible. It can be adjusted later if the resulting coverage is not useful.

## Interpretation

College Scorecard earnings are useful comparison indicators, but they should not be read as guaranteed salaries for all graduates. Coverage can differ by program and some values are unavailable or privacy-suppressed.

The site therefore:

- shows missing values as `—`;
- does not estimate missing earnings;
- keeps 1-year and 4-year earnings separate;
- labels tuition as in-state tuition;
- treats acceptance rate and tuition as institution-level values;
- treats earnings as program-level values.

The university-card **Median across bachelor's programs** is calculated from available 1-year program earnings and is not a separate official Scorecard university metric.

## Staging policy

Preserve enough source/audit information to reproduce and debug the pipeline, but do not force very large raw files into GitHub.

At Top-100 scale, the full field-of-study raw and normalized staging files exceed GitHub's per-file limit. They are generated and validated during the Action run, then discarded after browser-ready JSON and compact audit metadata are produced.

## Possible future sources

Only add another source when it supports a clear website feature.

- **IPEDS** — institution/completion data and broader federal education statistics.
- **BLS** — occupation-level wages and job outlook; not university-specific.
- **U.S. Census Bureau** — broader labor-market or geographic context.
- **Official university sources / Common Data Set** — institution-specific details when a standardized federal field is insufficient.

## Not currently used

- Employment rate by university + major is not currently displayed.
- Rankings are not currently displayed.

Both require a sufficiently consistent source/definition before they should return to the UI.

## Source rules

Keep source handling simple:

1. Prefer official public sources.
2. Never invent missing values.
3. Keep retrieval/selection/audit metadata so data can be refreshed or debugged later.
4. Preserve large raw payloads only when practical.
5. Avoid complex cross-source mappings until a user-facing feature actually needs them.
