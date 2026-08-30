# College Statistics Data Model

The live site uses a small set of normalized JSON files joined in the browser by stable IDs.

## Live files

### `universities.json`
One record per institution, keyed by `university_id`.

U.S. Scorecard institutions use IDs like:

```text
us-ipeds-166027
```

The IPEDS UNITID is also retained as an external identifier.

### `majors.json`
One record per shared 4-digit CIP field of study, keyed by `major_id`.

Example:

```text
cip4-1107
```

### `university-major.json`
Connects a university to a bachelor's field of study.

Current live scope is `credential_level: 3` / Bachelor's Degree only.

### `salaries.json`
Despite the historical filename, this file stores College Scorecard earnings indicators by university + major:

- `earnings_1yr`
- `earnings_4yr`
- `earnings_5yr` when available

The frontend displays 1-year and 4-year values. Missing values remain `null`.

### `tuition.json`
One institution-level display value per university. The live site uses in-state tuition when available.

### `admissions.json`
Institution-level admissions data. The live site currently uses acceptance rate.

### `metadata.json`
Small dataset-level description: status, source, scope, generation date, and notes.

## Runtime join

`js/api.js` loads only the files used by the current page and joins them using `university_id` and `major_id`.

The UI then groups matching program records by university.

## Derived university summary

The university-card value **Median across bachelor's programs** is calculated in the browser from the available program-level `earnings_1yr` values for that university. It is a convenience summary, not an official university-wide Scorecard metric.

## Rules

Keep the model practical:

- use stable IDs;
- keep missing values as `null`;
- do not guess unavailable statistics;
- keep institution facts separate from program facts;
- preserve source information;
- do not create placeholder files for possible future features;
- add new files only when the website actually needs them.

The staging area in `data/imported/` may contain more detail than the live files. At Top-100 scale, large program payloads are temporary during the workflow; the repository keeps compact audit metadata plus browser-ready JSON.
