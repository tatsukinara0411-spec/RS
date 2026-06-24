// ============================
// 初期化
// ============================

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("administrator").textContent = CONFIG.administrator;
  document.getElementById("last-updated").textContent = CONFIG.lastUpdated;
  document.getElementById("entry-fee").textContent = CONFIG.entryFee.toLocaleString() + "円";
  document.getElementById("participant-count").textContent = PARTICIPANTS.length + "名";

  const prizePool = Math.floor(PARTICIPANTS.length * CONFIG.entryFee * (1 - CONFIG.houseEdge));
  document.getElementById("prize-pool").textContent = prizePool.toLocaleString() + "円";

  renderRanking(prizePool);
  renderBracket();
  renderOdds();
});

// ============================
// ポイント計算
// ============================

function calcPoints(participant) {
  let total = 0;
  let correct = 0;
  for (const match of MATCHES) {
    if (match.winner && participant.predictions[match.id]) {
      if (participant.predictions[match.id] === match.winner) {
        const base = ROUND_POINTS[match.round] || 1;
        const oddsEntry = ODDS.find(o => o.team === match.winner);
        const multiplier = oddsEntry ? oddsEntry.odds : 1;
        total += base * multiplier;
        correct++;
      }
    }
  }
  return { total: Math.round(total * 10) / 10, correct };
}

// ============================
// ランキング描画
// ============================

function renderRanking(prizePool) {
  const scores = PARTICIPANTS.map(p => {
    const { total, correct } = calcPoints(p);
    return { name: p.name, total, correct };
  });

  scores.sort((a, b) => b.total - a.total);

  const tbody = document.getElementById("ranking-body");

  if (scores.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:#4a6a8a;padding:32px;">まだ参加者がいません</td></tr>`;
    return;
  }

  tbody.innerHTML = scores.map((s, i) => {
    const rank = i + 1;
    const badgeClass = rank <= 3 ? `rank-${rank}` : "rank-other";
    const prize = rank <= 3
      ? Math.floor(prizePool * CONFIG.prizeRatio[rank - 1]).toLocaleString() + "円"
      : "-";
    return `
      <tr>
        <td><span class="rank-badge ${badgeClass}">${rank}</span></td>
        <td>${s.name}</td>
        <td class="points">${s.total}pt</td>
        <td>${s.correct}問</td>
        <td class="prize-est">${prize}</td>
      </tr>`;
  }).join("");
}

// ============================
// ブラケット描画
// ============================

function renderBracket() {
  const rounds = [
    { key: "R32",   label: "R32",    ids: MATCHES.filter(m => m.round === "R32").map(m => m.id) },
    { key: "R16",   label: "R16",    ids: MATCHES.filter(m => m.round === "R16").map(m => m.id) },
    { key: "QF",    label: "準々決勝", ids: MATCHES.filter(m => m.round === "QF").map(m => m.id) },
    { key: "SF",    label: "準決勝",  ids: MATCHES.filter(m => m.round === "SF").map(m => m.id) },
    { key: "Final", label: "決勝",    ids: MATCHES.filter(m => m.round === "Final").map(m => m.id) },
  ];

  const bracket = document.getElementById("bracket");

  const bracketDiv = document.createElement("div");
  bracketDiv.className = "bracket";

  for (const round of rounds) {
    const col = document.createElement("div");
    col.className = "round-col";

    const header = document.createElement("div");
    header.className = "round-header";
    header.textContent = round.label;
    col.appendChild(header);

    const matchCount = round.ids.length;

    for (const id of round.ids) {
      const match = MATCHES.find(m => m.id === id);
      const wrapper = document.createElement("div");
      wrapper.className = "match-wrapper";
      wrapper.style.minHeight = `${Math.max(60, 480 / matchCount)}px`;

      const card = document.createElement("div");
      card.className = "match-card";

      const teams = [
        { name: match.teamA, score: match.scoreA },
        { name: match.teamB, score: match.scoreB },
      ];

      for (const t of teams) {
        const teamDiv = document.createElement("div");
        const isTBD = t.name === "TBD" || !t.name;
        const isWinner = match.winner && match.winner === t.name;
        const isLoser = match.winner && match.winner !== t.name && !isTBD;

        teamDiv.className = "team" + (isTBD ? " tbd" : isWinner ? " winner" : isLoser ? " loser" : "");

        const oddsEntry = ODDS.find(o => o.team === t.name);
        const flagSpan = oddsEntry ? `<span class="flag">${oddsEntry.flag}</span>` : "";

        teamDiv.innerHTML = `
          <span>${flagSpan}${isTBD ? "未定" : t.name}</span>
          ${t.score !== null ? `<span class="score">${t.score}</span>` : ""}
        `;
        card.appendChild(teamDiv);
      }

      wrapper.appendChild(card);
      col.appendChild(wrapper);
    }

    bracketDiv.appendChild(col);
  }

  bracket.appendChild(bracketDiv);
}

// ============================
// オッズ描画
// ============================

function renderOdds() {
  const sorted = [...ODDS].sort((a, b) => a.odds - b.odds);
  const grid = document.getElementById("odds-grid");

  grid.innerHTML = sorted.map(o => `
    <div class="odds-card ${o.tier === "favorite" ? "favorite" : o.tier === "underdog" ? "underdog" : ""}">
      <div class="team-name">${o.flag} ${o.team}</div>
      <div class="odds-value">${o.odds}倍</div>
      <div class="odds-label">優勝オッズ</div>
    </div>
  `).join("");
}
