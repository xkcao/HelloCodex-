const tabs = document.querySelector("#leagueTabs");
const results = document.querySelector("#results");
const standings = document.querySelector("#standings");
const scorers = document.querySelector("#scorers");
const assists = document.querySelector("#assists");
const status = document.querySelector("#dataStatus");

let data;

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function scorerGoalCount(items) {
  return items.reduce((total, item) => {
    const multiplier = item.match(/×\s*(\d+)/);
    return total + (multiplier ? Number(multiplier[1]) : 1);
  }, 0);
}

function formatScorers(match) {
  const totalGoals = match.homeScore + match.awayScore;
  const items = Array.isArray(match.scorers) ? match.scorers : [];

  if (totalGoals === 0) return "No goals";

  if (items.length === 0) {
    return '<span class="data-note">Scorers not available</span>';
  }

  const names = items.map(escapeHtml).join(", ");
  if (scorerGoalCount(items) !== totalGoals) {
    return `${names}<span class="data-note">Incomplete scorer list</span>`;
  }

  return names;
}

function renderResults(league) {
  const body = league.results
    .map(
      (match) => `
        <tr>
          <td>${escapeHtml(match.home)}</td>
          <td><span class="score">${match.homeScore}–${match.awayScore}</span></td>
          <td>${escapeHtml(match.away)}</td>
          <td>${formatScorers(match)}</td>
        </tr>
      `
    )
    .join("");

  results.innerHTML = `
    <h2>Recent verified results <span class="pill">${escapeHtml(league.country)}</span></h2>
    <table class="results-table">
      <thead>
        <tr><th>Home</th><th>Score</th><th>Away</th><th>Scorers</th></tr>
      </thead>
      <tbody>${body}</tbody>
    </table>
  `;
}

function renderStandings(league) {
  const body = league.standings
    .map(
      (team, index) => `
        <tr>
          <td>${index + 1}</td>
          <td>${escapeHtml(team.team)}</td>
          <td>${team.p}</td>
          <td class="secondary-stat">${team.w}</td>
          <td class="secondary-stat">${team.d}</td>
          <td class="secondary-stat">${team.l}</td>
          <td>${team.gd}</td>
          <td><strong>${team.pts}</strong></td>
        </tr>
      `
    )
    .join("");

  standings.innerHTML = `
    <h2>Standings snapshot <span class="pill">Top ${league.standings.length} shown</span></h2>
    <table class="standings-table">
      <thead>
        <tr>
          <th>#</th><th>Team</th><th>P</th>
          <th class="secondary-stat">W</th>
          <th class="secondary-stat">D</th>
          <th class="secondary-stat">L</th>
          <th>GD</th><th>Pts</th>
        </tr>
      </thead>
      <tbody>${body}</tbody>
    </table>
  `;
}

function renderLeaders(element, title, items, valueKey) {
  if (!items.length) {
    element.innerHTML = `
      <h2>${title} <span class="pill">Partial data</span></h2>
      <p class="empty">No sufficiently verified ${title.toLowerCase()} data is available for this snapshot.</p>
    `;
    return;
  }

  const body = items
    .map(
      (item) => `
        <tr>
          <td>${escapeHtml(item.player)}</td>
          <td>${escapeHtml(item.team)}</td>
          <td><strong>${item[valueKey]}</strong></td>
        </tr>
      `
    )
    .join("");

  element.innerHTML = `
    <h2>${title} <span class="pill">Partial list</span></h2>
    <table class="leaders-table">
      <thead>
        <tr><th>Player</th><th>Club</th><th>${valueKey === "goals" ? "Goals" : "Assists"}</th></tr>
      </thead>
      <tbody>${body}</tbody>
    </table>
  `;
}

function renderLeague(league) {
  renderResults(league);
  renderStandings(league);
  renderLeaders(scorers, "Leading scorers", league.scorers, "goals");
  renderLeaders(assists, "Assist leaders", league.assists, "assists");

  document.querySelectorAll(".league-tabs button").forEach((button) => {
    const active = button.dataset.id === league.id;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });

  history.replaceState(null, "", `#${league.id}`);
}

function validateData(payload) {
  if (!payload || !Array.isArray(payload.leagues) || payload.leagues.length === 0) {
    throw new Error("Soccer data has no leagues");
  }

  const issues = [];
  const ids = new Set();

  payload.leagues.forEach((league) => {
    if (!league.id || ids.has(league.id)) throw new Error("League IDs must be unique");
    ids.add(league.id);

    ["results", "standings", "scorers", "assists"].forEach((key) => {
      if (!Array.isArray(league[key])) {
        throw new Error(`${league.id}: ${key} must be an array`);
      }
    });

    league.standings.forEach((team) => {
      if (team.p !== team.w + team.d + team.l) {
        issues.push(`${league.id}: games played mismatch for ${team.team}`);
      }
      if (team.pts !== team.w * 3 + team.d) {
        issues.push(`${league.id}: points mismatch for ${team.team}`);
      }
    });
  });

  if (issues.length) console.warn("Soccer data validation warnings:", issues);
}

function selectFromHash() {
  const id = location.hash.slice(1);
  return data.leagues.find((league) => league.id === id) || data.leagues[0];
}

fetch("data/soccer.json")
  .then((response) => {
    if (!response.ok) throw new Error("Could not load data");
    return response.json();
  })
  .then((payload) => {
    validateData(payload);
    data = payload;
    status.textContent = payload.updated;

    tabs.innerHTML = payload.leagues
      .map(
        (league) =>
          `<button type="button" aria-pressed="false" data-id="${escapeHtml(league.id)}">${escapeHtml(league.name)}</button>`
      )
      .join("");

    tabs.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button) return;
      const league = data.leagues.find((item) => item.id === button.dataset.id);
      if (league) renderLeague(league);
    });

    window.addEventListener("hashchange", () => renderLeague(selectFromHash()));
    renderLeague(selectFromHash());
  })
  .catch((error) => {
    console.error(error);
    status.textContent = "Data unavailable";
    document.querySelector(".grid").innerHTML =
      '<div class="card wide empty">Could not load soccer data.</div>';
  });
