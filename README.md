# HelloCodex

HelloCodex is a GitHub Pages repository for a collection of independent static web projects. The repository root is a lightweight project portal, while each project lives in its own self-contained folder under `projects/`.

## Repository structure

```text
/
├── index.html                 # HelloCodex landing page
├── assets/
│   └── css/
│       └── site.css           # Shared/root landing-page styles
├── projects/
│   ├── soccer/
│   │   ├── index.html
│   │   ├── css/
│   │   ├── js/
│   │   ├── data/
│   │   └── README.md
│   └── college-statistics/
│       ├── index.html
│       ├── css/
│       ├── js/
│       ├── data/
│       └── README.md
└── README.md
```

## Projects

### Soccer Dashboard

The existing European soccer dashboard, including results, standings, top scorers and assists, lives at:

`/projects/soccer/`

### College Statistics

A scaffold for a future project covering university majors, salaries, employment outcomes and education statistics lives at:

`/projects/college-statistics/`

## Adding a new project

1. Create a new folder under `projects/`, for example `projects/new-project/`.
2. Add an `index.html` plus `css/`, `js/`, `data/`, and `README.md`.
3. Keep project-specific paths relative to that project folder so it remains self-contained.
4. Add a project card to the root `index.html`.
5. Reuse shared assets only when they are genuinely common across projects; otherwise keep styling and logic inside the project.

## GitHub Pages organization

GitHub Pages serves the repository root as the site root. Therefore:

- `/index.html` is the HelloCodex home page.
- `/projects/soccer/` serves `projects/soccer/index.html`.
- `/projects/college-statistics/` serves `projects/college-statistics/index.html`.

This structure lets each project evolve independently while keeping one stable GitHub Pages entry point.
