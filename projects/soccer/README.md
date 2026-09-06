# Soccer Dashboard

A lightweight GitHub Pages dashboard for recent results and league snapshots across the Premier League, La Liga, Serie A, Bundesliga and Ligue 1.

## What the site shows

- The 10 most recent completed results available for each league
- A top-five standings snapshot calculated from completed results
- Dated leading-scorer and assist snapshots
- Explicit messages when scorer or assist details are unavailable
- Scorer-list warnings when the listed goals do not account for the final score

The selected league is stored in the page URL, so refreshing or sharing the link preserves the selection.

## Structure

- `index.html` — page structure
- `css/styles.css` — responsive project styling
- `js/app.js` — data loading, validation, rendering and interactions
- `data/soccer.json` — soccer data used by the dashboard
- `scripts/update_soccer.py` — dependency-free public-data updater and validator
- `../../.github/workflows/refresh-soccer.yml` — daily and manual GitHub Actions workflow

The project remains self-contained and framework-free. GitHub Pages serves the dashboard, while GitHub Actions updates its static JSON; no continuously running backend or database is required.

## Automatic updates

The `Refresh soccer data` workflow runs daily at 7:17 AM in the `America/Los_Angeles` timezone, so daylight saving time is handled automatically. It can also be run manually from the repository's **Actions** tab.

The updater downloads the current-season JSON files from the public-domain [Open Football](https://github.com/openfootball/football.json) project. No account, API token, repository secret or manual activation is required. It calculates standings from completed results using points, goal difference and goals scored. This is a transparent calculated snapshot; official league ordering can differ when competition-specific tie-break rules apply.

Player-leader data is not available in this source, so the updater preserves the last manually verified scorer and assist snapshots and displays their date instead of pretending they were refreshed.

The workflow has write access only to repository contents, using GitHub's automatically supplied workflow credential. If a download fails, a league is missing, a score is malformed, or the public source is behind the published snapshot, the updater leaves `data/soccer.json` unchanged. It fetches and validates the complete five-league candidate before writing. When data has not changed, it creates no commit.

## Data rules

Both automated and manual updates follow the same rules:

1. Include completed matches only.
2. Use source-provided values; never estimate missing data.
3. Preserve dated scorer and assist snapshots until a reliable key-free source is available.
4. Keep the `updated` description accurate.
5. Treat standings, scorers and assists as snapshots and label their scope accurately.
6. Use an empty array for an unavailable section.
7. Validate the entire snapshot before publishing.

Run a local structure check without calling the API:

```bash
python3 projects/soccer/scripts/update_soccer.py --validate-only
```

## Data shape

Each league uses this structure:

```json
{
  "updated": "Verified date, time and coverage note",
  "leagues": [
    {
      "id": "premier-league",
      "name": "Premier League",
      "country": "England",
      "results": [],
      "standings": [],
      "scorers": [],
      "assists": []
    }
  ]
}
```

A result contains `home`, `away`, `homeScore`, `awayScore` and a `scorers` array. A standings entry contains `team`, `p`, `w`, `d`, `l`, `gd` and `pts`.
