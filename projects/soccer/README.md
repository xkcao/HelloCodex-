# Soccer Dashboard

A lightweight GitHub Pages dashboard for recent verified results and partial league snapshots across the Premier League, La Liga, Serie A, Bundesliga and Ligue 1.

## What the site shows

- Recent completed results included in the latest verified update
- A clearly labeled standings snapshot rather than a full league table
- Partial leading-scorer and assist lists
- Explicit messages when sufficiently verified data is unavailable
- Scorer-list warnings when the listed goals do not account for the final score

The selected league is stored in the page URL, so refreshing or sharing the link preserves the selection.

## Structure

- `index.html` — page structure
- `css/styles.css` — responsive project styling
- `js/app.js` — data loading, validation, rendering and interactions
- `data/soccer.json` — soccer data used by the dashboard

The project remains self-contained and framework-free so it can evolve independently without adding build or hosting complexity.

## Data rules

When updating `data/soccer.json`:

1. Include completed matches only.
2. Verify each value; never guess.
3. Leave an unavailable statistic empty rather than filling it with an estimate.
4. Keep the `updated` description accurate and include the verification time.
5. Treat standings, scorers and assists as partial snapshots unless the data explicitly contains every league entry.
6. Use an empty array for an unavailable section.
7. Run a consistency review before publishing.

The browser performs lightweight checks when the file loads. Missing or duplicate league IDs and malformed section arrays stop rendering and show the data-unavailable state. Games-played or points inconsistencies produce console warnings without hiding otherwise usable data.

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
