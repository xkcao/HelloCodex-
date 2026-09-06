#!/usr/bin/env python3
"""Refresh results and calculated standings from key-free Open Football data."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


SOURCE_ROOT = "https://raw.githubusercontent.com/openfootball/football.json/master"
DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "soccer.json"
RECENT_RESULTS = 10
STANDINGS_LIMIT = 5

LEAGUES = (
    {"id": "premier-league", "name": "Premier League", "country": "England", "file": "en.1.json"},
    {"id": "la-liga", "name": "La Liga", "country": "Spain", "file": "es.1.json"},
    {"id": "serie-a", "name": "Serie A", "country": "Italy", "file": "it.1.json"},
    {"id": "bundesliga", "name": "Bundesliga", "country": "Germany", "file": "de.1.json"},
    {"id": "ligue-1", "name": "Ligue 1", "country": "France", "file": "fr.1.json"},
)


class UpdateError(RuntimeError):
    pass


class SourceBehind(UpdateError):
    pass


def season_for(moment: datetime) -> str:
    start_year = moment.year if moment.month >= 7 else moment.year - 1
    return f"{start_year}-{(start_year + 1) % 100:02d}"


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "HelloCodex-Soccer-Updater/2.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise UpdateError(f"Could not load {url}: {error}") from error


def full_time_score(match: dict) -> tuple[int, int] | None:
    score = match.get("score")
    if isinstance(score, dict):
        score = score.get("ft")
    if not isinstance(score, list) or len(score) != 2:
        return None
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in score):
        raise UpdateError("A completed match has a malformed score")
    return score[0], score[1]


def completed_matches(payload: dict, league_id: str, today: str) -> list[dict]:
    matches = payload.get("matches")
    if not isinstance(matches, list):
        raise UpdateError(f"{league_id}: source has no match list")

    completed = []
    seen = set()
    for match in matches:
        if not isinstance(match, dict):
            raise UpdateError(f"{league_id}: malformed match entry")
        score = full_time_score(match)
        date = match.get("date")
        home = match.get("team1")
        away = match.get("team2")
        if score is None or not isinstance(date, str) or date > today:
            continue
        if not isinstance(home, str) or not home.strip() or not isinstance(away, str) or not away.strip():
            raise UpdateError(f"{league_id}: completed match has a missing team")
        key = (date, home, away)
        if key in seen:
            raise UpdateError(f"{league_id}: duplicate completed match")
        seen.add(key)
        completed.append(
            {
                "date": date,
                "time": match.get("time") if isinstance(match.get("time"), str) else "",
                "home": home.strip(),
                "away": away.strip(),
                "homeScore": score[0],
                "awayScore": score[1],
                "scorers": [],
            }
        )

    completed.sort(key=lambda match: (match["date"], match["time"], match["home"]))
    if not completed:
        raise UpdateError(f"{league_id}: source has no completed matches")
    return completed


def calculate_standings(matches: list[dict]) -> list[dict]:
    table = defaultdict(lambda: {"p": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0})
    for match in matches:
        home = table[match["home"]]
        away = table[match["away"]]
        home_goals = match["homeScore"]
        away_goals = match["awayScore"]
        home["p"] += 1
        away["p"] += 1
        home["gf"] += home_goals
        home["ga"] += away_goals
        away["gf"] += away_goals
        away["ga"] += home_goals
        if home_goals > away_goals:
            home["w"] += 1
            away["l"] += 1
        elif home_goals < away_goals:
            away["w"] += 1
            home["l"] += 1
        else:
            home["d"] += 1
            away["d"] += 1

    rows = []
    for team, stats in table.items():
        rows.append(
            {
                "team": team,
                "p": stats["p"],
                "w": stats["w"],
                "d": stats["d"],
                "l": stats["l"],
                "gd": stats["gf"] - stats["ga"],
                "pts": stats["w"] * 3 + stats["d"],
                "gf": stats["gf"],
            }
        )
    rows.sort(key=lambda row: (-row["pts"], -row["gd"], -row["gf"], row["team"]))
    for row in rows:
        del row["gf"]
    return rows[:STANDINGS_LIMIT]


def max_played(league: dict) -> int:
    rows = league.get("standings", [])
    return max((row.get("p", 0) for row in rows if isinstance(row, dict)), default=0)


def build_snapshot(current: dict, moment: datetime) -> dict:
    season = season_for(moment)
    today = moment.date().isoformat()
    current_by_id = {league["id"]: league for league in current["leagues"]}
    leagues = []
    latest_dates = []

    for config in LEAGUES:
        print(f"Fetching {config['name']}...")
        payload = fetch_json(f"{SOURCE_ROOT}/{season}/{config['file']}")
        completed = completed_matches(payload, config["id"], today)
        standings = calculate_standings(completed)
        previous = current_by_id[config["id"]]
        if max_played({"standings": standings}) < max_played(previous):
            raise SourceBehind(f"{config['id']}: public source is behind the published snapshot")
        latest_dates.append(completed[-1]["date"])
        leagues.append(
            {
                "id": config["id"],
                "name": config["name"],
                "country": config["country"],
                "results": list(reversed(completed[-RECENT_RESULTS:])),
                "standings": standings,
                "scorers": previous["scorers"],
                "assists": previous["assists"],
            }
        )

    leaders_date = current.get("leadersUpdatedThrough", "2026-09-05")
    newest_result = max(latest_dates)
    return {
        "updated": (
            f"Results and calculated standings refreshed {moment.strftime('%b %-d, %Y at %H:%M UTC')} "
            f"— latest source result {newest_result}; player leaders last verified {leaders_date}"
        ),
        "resultsUpdatedThrough": newest_result,
        "leadersUpdatedThrough": leaders_date,
        "source": "Open Football",
        "sourceUrl": "https://github.com/openfootball/football.json",
        "leagues": leagues,
    }


def validate_snapshot(payload: dict) -> None:
    leagues = payload.get("leagues")
    if not isinstance(leagues, list) or len(leagues) != len(LEAGUES):
        raise UpdateError("Snapshot must contain exactly five leagues")
    expected_ids = [league["id"] for league in LEAGUES]
    if [league.get("id") for league in leagues] != expected_ids:
        raise UpdateError("Snapshot league order or IDs are inconsistent")
    for league in leagues:
        for key in ("results", "standings", "scorers", "assists"):
            if not isinstance(league.get(key), list):
                raise UpdateError(f"{league.get('id')}: {key} must be an array")
        if not league["results"] or not league["standings"]:
            raise UpdateError(f"{league['id']}: results and standings cannot be empty")
        for row in league["standings"]:
            if row["p"] != row["w"] + row["d"] + row["l"] or row["pts"] != row["w"] * 3 + row["d"]:
                raise UpdateError(f"{league['id']}: inconsistent calculated standings")


def comparable(payload: dict) -> dict:
    return {key: value for key, value in payload.items() if key != "updated"}


def main() -> int:
    try:
        current = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        validate_snapshot(current)
        if "--validate-only" in sys.argv:
            print("Existing soccer data is valid.")
            return 0

        candidate = build_snapshot(current, datetime.now(timezone.utc))
        validate_snapshot(candidate)
        if comparable(candidate) == comparable(current):
            print("No soccer data changes detected.")
            return 0

        temporary = DATA_FILE.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(candidate, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        temporary.replace(DATA_FILE)
        print(f"Updated {DATA_FILE}")
        return 0
    except SourceBehind as error:
        print(f"No update: {error}")
        return 0
    except (OSError, KeyError, TypeError, json.JSONDecodeError, UpdateError) as error:
        print(f"Soccer update failed safely: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
