# HelloCodex

HelloCodex is a GitHub Pages repository containing independent static web projects. The repository root is a simple project portal, and each project lives in its own folder under `projects/`.

## Structure

```text
/
├── index.html
├── assets/
├── .github/workflows/
├── projects/
│   ├── soccer/
│   └── college-statistics/
└── README.md
```

Each project keeps its own HTML, CSS, JavaScript, data, scripts and documentation so it can evolve independently. Project-specific GitHub Actions live in `.github/workflows/` because GitHub requires workflows at the repository level.

## Projects

### Soccer Dashboard

A lightweight European soccer dashboard with automatically refreshed completed results and partial snapshots of standings, scorers and assists. A daily GitHub Action updates the static data after validating all five leagues; see the project README for its one-time API-token setup.

Path: `/projects/soccer/`

### College Statistics

A university and major explorer using public U.S. Department of Education College Scorecard data.

The current site covers a 100-institution U.S. coverage set and bachelor's programs. Users can browse either by university or by major, then sort and filter by earnings, tuition, acceptance rate, state, and institution type. The site shows program-level 1-year and 4-year median earnings where available, plus university-level in-state tuition and acceptance rate.

The 100-school set is a practical inclusion set rather than an official or displayed ranking.

Path: `/projects/college-statistics/`

## Adding a project

1. Create a folder under `projects/`.
2. Keep project-specific code, data and scripts inside that folder.
3. Add an `index.html` and a short `README.md`.
4. Add a project card to the root `index.html`.
5. Add a repository-level workflow only when scheduled automation is genuinely needed.

Prefer simple, self-contained static projects. Introduce shared infrastructure only when multiple projects genuinely need it.

## GitHub Pages

GitHub Pages serves the repository root as the site root:

- `/` → HelloCodex project portal
- `/projects/soccer/` → Soccer Dashboard
- `/projects/college-statistics/` → College Statistics

No continuously running backend server is required. Scheduled GitHub Actions may update static project data when appropriate.
