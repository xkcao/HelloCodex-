# College Statistics

A self-contained HelloCodex project for exploring university and major statistics.

## Structure

- `index.html` — project UI and semantic page structure
- `css/styles.css` — responsive visual design
- `js/app.js` — data loading, search, filtering, and rendering
- `data/colleges.json` — placeholder college/major records

## Current data

This initial version intentionally uses fictional placeholder data. The sample records demonstrate the expected data shape for:

- universities
- majors
- median salary
- employment rate
- tuition
- acceptance rate

The UI is separated from the dataset so future updates can replace `data/colleges.json` with verified data without restructuring the application.

## Running locally

Because the page loads JSON with `fetch()`, serve the project through a local HTTP server rather than opening `index.html` directly from the filesystem. It also works as-is when deployed through GitHub Pages.
