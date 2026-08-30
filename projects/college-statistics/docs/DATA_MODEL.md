# College Statistics Data Model

The project uses stable IDs and normalized JSON files so independent datasets can be updated without rewriting the frontend.

## Core entities

### `universities.json`
One record per institution. Primary key: `university_id`.

Fields: `university_id`, `name`, `short_name`, `state`, `city`, `country`, `type`, `website`, `enrollment`, `established`, `logo`.

### `majors.json`
One record per canonical major/program subject. Primary key: `major_id`.

Fields: `major_id`, `name`, `category`, `cip_code`, `stem`, `description`.

### `university-major.json`
Many-to-many relationship between universities and majors.

Fields: `university_id`, `major_id`, `degree_level`, `available`.

## Fact datasets

### `salaries.json`
University-major outcome facts by year/source: `median_salary`, `early_salary`, `mid_salary`.

### `employment.json`
University-major outcome facts by year/source: `employment_rate`, `unemployment_rate`, `graduate_school_rate`.

### `tuition.json`
Institution-level tuition facts by year/source. Supports future residency and currency dimensions.

### `admissions.json`
Institution-level admissions facts by year/source: acceptance rate, test scores, GPA, and deadline.

### `rankings.json`
Institution rankings by provider and year. A provider is a dimension, not a hard-coded frontend assumption, so multiple ranking sources can coexist.

### `metadata.json`
Schema version, current dataset year, supported countries, generation date, and dataset status.

## Join strategy

The browser loads datasets independently. `js/api.js` joins them at runtime using `university_id` and `major_id`. Future ETL jobs can generate exactly the same files from external sources.

## Historical data

Do not overwrite past observations when adding annual data. Add records with a new `year` and retain `source`. UI modules can later select latest values or render trends.

## Scale rules

- IDs must be stable and never depend on display names.
- Missing values should be `null`, never guessed.
- Every externally sourced fact should include `source` and `year`.
- Country-specific fields should be optional or isolated instead of changing core IDs.
- Prefer canonical identifiers when available, such as IPEDS UnitID and CIP codes, while preserving internal IDs for joins.
