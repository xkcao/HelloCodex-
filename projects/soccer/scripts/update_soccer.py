#!/usr/bin/env python3
"""Refresh the static soccer dashboard from football-data.org."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


API_ROOT = "https://api.football-data.org/v4"
DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "soccer.json"
REQUEST_DELAY_SECONDS = 6.5
RECENT_RESULTS = 10
LEADER_LIMIT = 5

LEAGUES = (
    {"id": "premier-league", "name": "Premier League", "country": "England", "code": "PL"},
    {"id": "la-liga", "name": "La Liga", "country": "Spain", "code": "PD"},
    {"id": "serie-a", "name": "Serie A", "country": "Italy", "code": "SA"},
    {"id": "bundesliga", "name": "Bundesliga", "country": "Germany", "code": "BL1"},
    {"id": "ligue-1", "name": "Ligue 1", "country": "France", "code": "FL1"},
)


class UpdateError(RuntimeError):
    pass


class FootballDataClient:
    def __init__(self, token: str) -> None:
        self.token = token
        self.request_count = 0

    def get(self, path: str) -> dict:
        if self.request_count:
            time.sleep(REQUEST_DELAY_SECONDS)
        self.request_count += 1

        request = urllib.request.Request(
            f"{API_ROOT}{path}",
            headers={
                "X-Auth-Token": self.token,
                "X-Unfold-Goals": "true",
                "User-Agent": "HelloCodex-Soccer-Updater/1.0",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            raise UpdateError(f"API request failed for {path}: {error}") from error


def integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise UpdateError(f"Expected an integer for {label}")
    return value


def compress_scorers(match: dict, expected_goals: int) -> list[str]:
    goals = match.get("goals")
    if not isinstance(goals, list) or len(goals) != expected_goals:
        return []

    ordered_names: list[str] = []
    for goal in goals:
        scorer = goal.get("scorer") or {}
        name = scorer.get("name")
        if not isinstance(name, str) or not name.strip():
            return []
        if goal.get("type") == "OWN_GOAL":
            name = f"{name} (own goal)"
        ordered_names.append(name.strip())

    counts = Counter(ordered_names)
    emitted: set[str] = set()
    result: list[str] = []
    for name in ordered_names:
        if name in emitted:
            continue
        emitted.add(name)
        result.append(f"{name} ×{counts[name]}" if counts[name] > 1 else name)
    return result


def build_results(payload: dict, league_id: str) -> list[dict]:
    finished = [match for match in payload.get("matches", []) if match.get("status") == "FINISHED"]
    finished.sort(key=lambda match: match.get("utcDate", ""), reverse=True)
    if not finished:
        raise UpdateError(f"{league_id}: API returned no completed matches")

    results = []
    for match in finished[:RECENT_RESULTS]:
        score = (match.get("score") or {}).get("fullTime") or {}
        home_score = integer(score.get("home"), f"{league_id} home score")
        away_score = integer(score.get("away"), f"{league_id} away score")
        home = (match.get("homeTeam") or {}).get("name")
        away = (match.get("awayTeam") or {}).get("name")
        if not home or not away or home_score < 0 or away_score < 0:
            raise UpdateError(f"{league_id}: malformed completed match")
        results.append(
            {
                "home": home,
                "away": away,
                "homeScore": home_score,
                "awayScore": away_score,
                "scorers": compress_scorers(match, home_score + away_score),
            }
        )
    return results


def build_standings(payload: dict, league_id: str) -> list[dict]:
    total = next((item for item in payload.get("standings", []) if item.get("type") == "TOTAL"), None)
    table = (total or {}).get("table")
    if not isinstance(table, list) or len(table) < LEADER_LIMIT:
        raise UpdateError(f"{league_id}: standings are missing or incomplete")

    standings = []
    for entry in table[:LEADER_LIMIT]:
        team = (entry.get("team") or {}).get("name")
        row = {
            "team": team,
            "p": integer(entry.get("playedGames"), f"{league_id} played"),
            "w": integer(entry.get("won"), f"{league_id} wins"),
            "d": integer(entry.get("draw"), f"{league_id} draws"),
            "l": integer(entry.get("lost"), f"{league_id} losses"),
            "gd": integer(entry.get("goalDifference"), f"{league_id} goal difference"),
            "pts": integer(entry.get("points"), f"{league_id} points"),
        }
        if not team or row["p"] != row["w"] + row["d"] + row["l"]:
            raise UpdateError(f"{league_id}: inconsistent standings row")
        standings.append(row)
    return standings


def build_leaders(payload: dict) -> tuple[list[dict], list[dict]]:
    raw = payload.get("scorers")
    if not isinstance(raw, list):
        return [], []

    scorers = []
    assist_candidates = []
    for entry in raw:
        player = (entry.get("player") or {}).get("name")
        team = (entry.get("team") or {}).get("name")
        goals = entry.get("goals")
        assists = entry.get("assists")
        if player and team and isinstance(goals, int):
            scorers.append({"player": player, "team": team, "goals": goals})
        if player and team and isinstance(assists, int) and assists > 0:
            assist_candidates.append({"player": player, "team": team, "assists": assists})

    scorers.sort(key=lambda item: (-item["goals"], item["player"]))
    assist_candidates.sort(key=lambda item: (-item["assists"], item["player"]))
    return scorers[:LEADER_LIMIT], assist_candidates[:LEADER_LIMIT]


def build_snapshot(client: FootballDataClient) -> dict:
    leagues = []
    for config in LEAGUES:
        code = config["code"]
        print(f"Fetching {config['name']}...")
        matches = client.get(f"/competitions/{code}/matches?status=FINISHED")
        standings = client.get(f"/competitions/{code}/standings")
        leaders = client.get(f"/competitions/{code}/scorers?limit={LEADER_LIMIT}")
        scorers, assists = build_leaders(leaders)
        leagues.append(
            {
                "id": config["id"],
                "name": config["name"],
                "country": config["country"],
                "results": build_results(matches, config["id"]),
                "standings": build_standings(standings, config["id"]),
                "scorers": scorers,
                "assists": assists,
            }
        )
    return {"leagues": leagues}


def validate_existing(payload: dict) -> None:
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


def main() -> int:
    try:
        current = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        validate_existing(current)
        if "--validate-only" in sys.argv:
            print("Existing soccer data is valid.")
            return 0

        token = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
        if not token:
            raise UpdateError("FOOTBALL_DATA_TOKEN is not configured")

        candidate = build_snapshot(FootballDataClient(token))
        validate_existing(candidate)
        if candidate["leagues"] == current["leagues"]:
            print("No soccer data changes detected.")
            return 0

        candidate["updated"] = (
            "Automatically verified "
            + datetime.now(timezone.utc).strftime("%b %-d, %Y at %H:%M UTC")
            + " — completed matches only"
        )
        temporary = DATA_FILE.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(candidate, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        temporary.replace(DATA_FILE)
        print(f"Updated {DATA_FILE}")
        return 0
    except (OSError, json.JSONDecodeError, UpdateError) as error:
        print(f"Soccer update failed safely: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
