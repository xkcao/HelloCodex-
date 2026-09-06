# Soccer Dashboard

A lightweight GitHub Pages dashboard for recent results and league snapshots across the Premier League, La Liga, Serie A, Bundesliga and Ligue 1.

## What the site shows

- The 10 most recent completed results returned for each league
- A top-five standings snapshot
- Partial leading-scorer and assist lists when the source provides them
- Explicit messages when scorer or assist details are unavailable
- Scorer-list warnings when the listed goals do not account for the final score

The selected league is stored in the page URL, so refreshing or sharing the link preserves the selection.

## Structure

- `index.html` — page structure
- `css/styles.css` — responsive project styling
- `js/app.js` — data loading, validation, rendering and interactions
- `data/soccer.json` — soccer data used by the dashboard
- `scripts/update_soccer.py` — dependency-free API updater and validator
- `../../.github/workflows/refresh-soccer.yml` — daily and manual GitHub Actions workflow

The project remains self-contained and framework-free. GitHub Pages serves the dashboard, while GitHub Actions updates its static JSON; no continuously running backend or database is required.

## Automatic updates

The `Refresh soccer data` workflow runs daily at 14:17 UTC, which is 6:17 AM Pacific Standard Time or 7:17 AM Pacific Daylight Time. It can also be run manually from the repository's **Actions** tab.

The updater uses the football-data.org v4 API and its competition codes `PL`, `PD`, `SA`, `BL1` and `FL1`. It retrieves completed matches, total standings and leaders for all five leagues. Requests are deliberately spaced to remain below the free-plan rate limit.

One repository secret is required:

1. Create a free API token at [football-data.org](https://www.football-data.org/client/register).
2. In GitHub, open **Settings → Secrets and variables → Actions**.
3. Add a repository secret named `FOOTBALL_DATA_TOKEN` containing the token.
4. Open **Actions → Refresh soccer data → Run workflow** once to confirm the setup.

The workflow has write access only to repository contents. If the token is absent, an API request fails, any league is missing, a completed score is malformed, or standings are incomplete, the updater exits without changing `data/soccer.json`. It fetches and validates the complete five-league snapshot before writing. When the data has not changed, it creates no commit.

## Data rules

Both automated and manual updates follow the same rules:

1. Include completed matches only.
2. Use source-provided values; never estimate missing data.
3. Leave unavailable scorer or assist details empty.
4. Keep the `updated` description accurate.
5. Treat standings, scorers and assists as partial snapshots.
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
