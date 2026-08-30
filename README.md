# HelloCodex

HelloCodex is a GitHub Pages repository containing independent static web projects. The repository root is a simple project portal, and each project lives in its own folder under `projects/`.

## Structure

```text
/
├── index.html
├── assets/
├── projects/
│   ├── soccer/
│   └── college-statistics/
└── README.md
```

Each project keeps its own HTML, CSS, JavaScript, data, and documentation so it can evolve independently.

## Projects

### Soccer Dashboard

European soccer dashboard with results, standings, scorers, and assists.

Path: `/projects/soccer/`

### College Statistics

A university and major explorer using public U.S. Department of Education College Scorecard data.

The current pilot covers 10 U.S. universities and bachelor's programs. It shows program-level 1-year and 4-year median earnings where available, plus university-level in-state tuition and acceptance rate. The university cards also show a derived median across that university's available bachelor's-program 1-year earnings.

Path: `/projects/college-statistics/`

## Adding a project

1. Create a folder under `projects/`.
2. Keep project-specific code and data inside that folder.
3. Add an `index.html` and a short `README.md`.
4. Add a project card to the root `index.html`.

Prefer simple, self-contained static projects. Introduce shared infrastructure only when multiple projects genuinely need it.

## GitHub Pages

GitHub Pages serves the repository root as the site root:

- `/` → HelloCodex project portal
- `/projects/soccer/` → Soccer Dashboard
- `/projects/college-statistics/` → College Statistics

No backend server is required for the current projects.