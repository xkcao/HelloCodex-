# Data Sources

## Current production source

The live College Statistics pilot uses the U.S. Department of Education **College Scorecard**.

Current uses:

- institution identity and location;
- in-state tuition;
- acceptance rate;
- field-of-study / CIP program records;
- 1-year, 4-year, and 5-year median earnings where available.

The frontend currently displays 1-year and 4-year program earnings.

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
2. Preserve the original source payload in staging when practical.
3. Never invent missing values.
4. Keep retrieval metadata so data can be refreshed or debugged later.
5. Avoid adding complex cross-source mappings until a user-facing feature actually needs them.