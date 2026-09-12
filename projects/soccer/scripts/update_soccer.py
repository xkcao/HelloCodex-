#!/usr/bin/env python3
"""Refresh results and calculated standings from key-free Open Football data."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


SOURCE_ROOT = "https://raw.githubusercontent.com/openfootball/football.json/master"
DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "soccer.json"
RECENT_RESULTS = 10
STANDINGS_LIMIT = 5
DOWNLOAD_ATTEMPTS = 4
RETRY_DELAYS_SECONDS = (2, 5, 10)

LEAGUES = (
    {"id": "premier-league", "name": "Premier League", "country": "England", "file": "en.1.json"},
    {"id": "la-liga", "name": "La Liga", "country": "Spain", "file": "es.1.json"},
    {"id": "serie-a", "name": "Serie A", "country": "Italy", "file": "it.1.json"},
    {"id": "bundesliga", "name": "Bundesliga", "country": "Germany", "file": "de.1.json"},
    {"id": "ligue-1", "name": "Ligue 1", "country": "France", "file": "fr.1.json"},
)


class UpdateError(RuntimeError):
    pass


def season_for(moment: datetime) -> str:
    start_year = moment.year if moment.month >= 7 else moment.year - 1
    return f"{start_year}-{(start_year + 1) % 100:02d}"


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "HelloCodex-Soccer-Updater/2.0"},
    )
    last_error: Exception | None = None

    for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code not in (408, 429) and error.code < 500:
                raise UpdateError(f"Could not load {url}: HTTP {error.code}") from error
            last_error = error
        except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as error:
            last_error = error

        if attempt < DOWNLOAD_ATTEMPTS:
            delay = RETRY_DELAYS_SECONDS[attempt - 1]
            print(
                f"Download attempt {attempt} of {DOWNLOAD_ATTEMPTS} failed; "
                f"retrying in {delay} seconds...",
                file=sys.stderr,
            )
            time.sleep(delay)

    raise UpdateError(
        f"Could not load {url} after {DOWNLOAD_ATTEMPTS} attempts: {last_error}"
    ) from last_error


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


def source_is_behind(previous: dict, completed: list[dict], standings: list[dict]) -> bool:
    latest_date = completed[-1]["date"]
    previous_date = previous.get("resultsUpdatedThrough")
    if isinstance(previous_date, str) and latest_date < previous_date:
        return True

    previous_count = previous.get("completedMatchCount")
    if isinstance(previous_count, int) and len(completed) < previous_count:
        return True

    return max_played({"standings": standings}) < max_played(previous)


def build_snapshot(current: dict, moment: datetime) -> dict:
    season = season_for(moment)
    today = moment.date().isoformat()
    current_by_id = {league["id"]: league for league in current["leagues"]}
    leagues = []
    changed_leagues = []

    for config in LEAGUES:
        print(f"Fetching {config['name']}...")
        payload = fetch_json(f"{SOURCE_ROOT}/{season}/{config['file']}")
        completed = completed_matches(payload, config["id"], today)
        standings = calculate_standings(completed)
        previous = current_by_id[config["id"]]
        if source_is_behind(previous, completed, standings):
            print(f"Keeping {config['name']}: public source is behind the published snapshot")
            leagues.append(previous)
            continue

        latest_date = completed[-1]["date"]
        leaders_date = previous["leadersUpdatedThrough"]
        updated_league = {
            "id": config["id"],
            "name": config["name"],
            "country": config["country"],
            "resultsUpdatedThrough": latest_date,
            "completedMatchCount": len(completed),
            "leadersUpdatedThrough": leaders_date,
            "source": "Open Football",
            "sourceUrl": "https://github.com/openfootball/football.json",
            "results": list(reversed(completed[-RECENT_RESULTS:])),
            "standings": standings,
            "scorers": previous["scorers"],
            "assists": previous["assists"],
        }
        leagues.append(updated_league)
        if updated_league != previous:
            changed_leagues.append(config["name"])

    if not changed_leagues:
        return current

    return {
        "updated": (
            f"Automatically refreshed {moment.strftime('%b %-d, %Y at %H:%M UTC')} "
            f"— updated {', '.join(changed_leagues)}; player leaders are dated snapshots"
        ),
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
        league_id = league.get("id")
        for key in ("results", "standings", "scorers", "assists"):
            if not isinstance(league.get(key), list):
                raise UpdateError(f"{league_id}: {key} must be an array")
        if not league["results"] or not league["standings"]:
            raise UpdateError(f"{league_id}: results and standings cannot be empty")
        if len(league["standings"]) != STANDINGS_LIMIT:
            raise UpdateError(f"{league_id}: standings must contain exactly {STANDINGS_LIMIT} teams")
        for match in league["results"]:
            if not isinstance(match, dict):
                raise UpdateError(f"{league_id}: result must be an object")
            if not all(isinstance(match.get(key), str) and match[key].strip() for key in ("home", "away")):
                raise UpdateError(f"{league_id}: result has a missing team")
            for key in ("homeScore", "awayScore"):
                value = match.get(key)
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    raise UpdateError(f"{league_id}: result has a malformed score")
            if not isinstance(match.get("scorers"), list):
                raise UpdateError(f"{league_id}: result scorers must be an array")
            date = match.get("date")
            if date is not None:
                try:
                    datetime.strptime(date, "%Y-%m-%d")
                except (TypeError, ValueError) as error:
                    raise UpdateError(f"{league_id}: result has a malformed date") from error
        standing_teams = set()
        for row in league["standings"]:
            team = row.get("team")
            if not isinstance(team, str) or not team.strip() or team in standing_teams:
                raise UpdateError(f"{league_id}: standings teams must be present and unique")
            standing_teams.add(team)
            for key in ("p", "w", "d", "l", "gd", "pts"):
                if isinstance(row.get(key), bool) or not isinstance(row.get(key), int):
                    raise UpdateError(f"{league_id}: standings {key} must be an integer")
            if row["p"] != row["w"] + row["d"] + row["l"] or row["pts"] != row["w"] * 3 + row["d"]:
                raise UpdateError(f"{league_id}: inconsistent calculated standings")
        for key, value_key in (("scorers", "goals"), ("assists", "assists")):
            for leader in league[key]:
                if not all(isinstance(leader.get(field), str) and leader[field].strip() for field in ("player", "team")):
                    raise UpdateError(f"{league_id}: malformed {key} entry")
                value = leader.get(value_key)
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    raise UpdateError(f"{league_id}: malformed {key} total")
        for key in ("resultsUpdatedThrough", "leadersUpdatedThrough"):
            value = league.get(key)
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except (TypeError, ValueError) as error:
                raise UpdateError(f"{league_id}: {key} must be YYYY-MM-DD") from error
        count = league.get("completedMatchCount")
        if count is not None and (isinstance(count, bool) or not isinstance(count, int) or count < 0):
            raise UpdateError(f"{league_id}: completedMatchCount must be a non-negative integer")


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
    except (OSError, KeyError, TypeError, json.JSONDecodeError, UpdateError) as error:
        print(f"Soccer update failed safely: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
