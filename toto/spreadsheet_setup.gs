/**
 * 社内ワールドカップTOTO 2026 - Google Apps Script
 * シート構成: 2枚（🎯賭け入力 / ⚙️管理）
 */

// ============================
// 胴元設定
// ============================
const CFG = {
  administrator: "タロウ",
  maxBudget: 1000,
  betUnit: 100,
  prizeRatio: [0.50, 0.30, 0.20],
  favoriteMultiplier: 1.5,
  underdogMultiplier: 2.0,
};

// ============================
// チームとオッズ（オッズ低い = 強い方）
// ============================
const TEAMS = [
  { name: "ブラジル",              odds: 4.5  },
  { name: "フランス",              odds: 5.0  },
  { name: "スペイン",              odds: 5.5  },
  { name: "アルゼンチン",          odds: 6.0  },
  { name: "イングランド",          odds: 7.0  },
  { name: "ドイツ",                odds: 8.0  },
  { name: "ポルトガル",            odds: 9.0  },
  { name: "オランダ",              odds: 10.0 },
  { name: "ベルギー",              odds: 12.0 },
  { name: "クロアチア",            odds: 15.0 },
  { name: "ウルグアイ",            odds: 18.0 },
  { name: "メキシコ",              odds: 20.0 },
  { name: "アメリカ",              odds: 22.0 },
  { name: "コロンビア",            odds: 25.0 },
  { name: "ノルウェー",            odds: 28.0 },
  { name: "オーストリア",          odds: 30.0 },
  { name: "スイス",                odds: 30.0 },
  { name: "モロッコ",              odds: 32.0 },
  { name: "コートジボワール",      odds: 35.0 },
  { name: "スウェーデン",          odds: 38.0 },
  { name: "日本",                  odds: 40.0 },
  { name: "カナダ",                odds: 40.0 },
  { name: "セネガル",              odds: 45.0 },
  { name: "エクアドル",            odds: 48.0 },
  { name: "アルジェリア",          odds: 50.0 },
  { name: "韓国",                  odds: 50.0 },
  { name: "パラグアイ",            odds: 60.0 },
  { name: "オーストラリア",        odds: 65.0 },
  { name: "ガーナ",                odds: 70.0 },
  { name: "DRコンゴ",              odds: 90.0 },
  { name: "エジプト",              odds: 90.0 },
  { name: "南アフリカ",            odds: 150.0 },
  { name: "ボスニア・ヘルツェゴビナ", odds: 150.0 },
  { name: "カーボベルデ",          odds: 200.0 },
];

// ============================
// ラウンド別試合カード（実際の対戦カード）
// ============================
const ROUNDS = [
  {
    id: "R32", name: "ラウンド32",
    deadline: "2026-06-28 22:00",
    matches: [
      { id: "R32-01", teamA: "南アフリカ",            teamB: "カナダ",               deadline: "2026-06-28 22:00" },
      { id: "R32-02", teamA: "ブラジル",              teamB: "日本",                 deadline: "2026-06-29 22:00" },
      { id: "R32-03", teamA: "ドイツ",                teamB: "パラグアイ",           deadline: "2026-06-29 22:00" },
      { id: "R32-04", teamA: "オランダ",              teamB: "モロッコ",             deadline: "2026-06-29 22:00" },
      { id: "R32-05", teamA: "コートジボワール",      teamB: "ノルウェー",           deadline: "2026-06-30 22:00" },
      { id: "R32-06", teamA: "フランス",              teamB: "スウェーデン",         deadline: "2026-06-30 22:00" },
      { id: "R32-07", teamA: "メキシコ",              teamB: "エクアドル",           deadline: "2026-06-30 22:00" },
      { id: "R32-08", teamA: "イングランド",          teamB: "DRコンゴ",             deadline: "2026-07-01 22:00" },
      { id: "R32-09", teamA: "ベルギー",              teamB: "セネガル",             deadline: "2026-07-01 22:00" },
      { id: "R32-10", teamA: "アメリカ",              teamB: "ボスニア・ヘルツェゴビナ", deadline: "2026-07-01 22:00" },
      { id: "R32-11", teamA: "スペイン",              teamB: "オーストリア",         deadline: "2026-07-02 22:00" },
      { id: "R32-12", teamA: "ポルトガル",            teamB: "クロアチア",           deadline: "2026-07-02 22:00" },
      { id: "R32-13", teamA: "スイス",                teamB: "アルジェリア",         deadline: "2026-07-02 22:00" },
      { id: "R32-14", teamA: "オーストラリア",        teamB: "エジプト",             deadline: "2026-07-03 22:00" },
      { id: "R32-15", teamA: "アルゼンチン",          teamB: "カーボベルデ",         deadline: "2026-07-03 22:00" },
      { id: "R32-16", teamA: "コロンビア",            teamB: "ガーナ",               deadline: "2026-07-03 22:00" },
    ]
  },
  {
    id: "R16", name: "ラウンド16",
    deadline: "2026-07-04 19:00",
    matches: [
      { id: "R16-01", teamA: "TBD", teamB: "TBD" },
      { id: "R16-02", teamA: "TBD", teamB: "TBD" },
      { id: "R16-03", teamA: "TBD", teamB: "TBD" },
      { id: "R16-04", teamA: "TBD", teamB: "TBD" },
      { id: "R16-05", teamA: "TBD", teamB: "TBD" },
      { id: "R16-06", teamA: "TBD", teamB: "TBD" },
      { id: "R16-07", teamA: "TBD", teamB: "TBD" },
      { id: "R16-08", teamA: "TBD", teamB: "TBD" },
    ]
  },
  {
    id: "QF", name: "準々決勝",
    deadline: "2026-07-09 19:00",
    matches: [
      { id: "QF-01", teamA: "TBD", teamB: "TBD" },
      { id: "QF-02", teamA: "TBD", teamB: "TBD" },
      { id: "QF-03", teamA: "TBD", teamB: "TBD" },
      { id: "QF-04", teamA: "TBD", teamB: "TBD" },
    ]
  },
  {
    id: "SF", name: "準決勝",
    deadline: "2026-07-14 19:00",
    matches: [
      { id: "SF-01", teamA: "TBD", teamB: "TBD" },
      { id: "SF-02", teamA: "TBD", teamB: "TBD" },
    ]
  },
  {
    id: "Final", name: "決勝",
    deadline: "2026-07-19 19:00",
    matches: [
      { id: "Final-01", teamA: "TBD", teamB: "TBD" },
    ]
  },
];

// 管理シート内のセクション開始行
const ADMIN_MASTER_ROW  = 1;   // 参加者マスタ開始行
const ADMIN_RESULT_ROW  = 36;  // 結果入力開始行（マスタ最大30名 + 余白）
const ADMIN_VIEW_ROW    = 120; // 胴元ビュー開始行

// ============================
// カスタムメニュー
// ============================
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("⚽ TOTO管理")
    .addItem("🔧 初回セットアップ", "setupAll")
    .addItem("🔄 賭け入力シートを再生成", "rebuildBetSheet")
    .addSeparator()
    .addItem("📊 胴元ビューを更新", "updateAdminView")
    .addSeparator()
    .addItem("📢 リマインドメール送信", "sendReminderNow")
    .addToUi();
}

// ============================
// 初回セットアップ（2枚のシートを作成）
// ============================
function setupAll() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  setupBetSheet(ss);
  setupAdminSheet(ss);

  ["シート1", "Sheet1"].forEach(name => {
    const s = ss.getSheetByName(name);
    if (s && ss.getSheets().length > 1) ss.deleteSheet(s);
  });

  setupOnEditTrigger();

  SpreadsheetApp.getUi().alert(
    "✅ セットアップ完了！\n\n" +
    "【次のステップ】\n" +
    "1.「⚙️管理」シートの上部に参加者名を入力\n" +
    "2.「⚽TOTO管理」→「賭け入力シートを再生成」を実行\n" +
    "3.「🎯賭け入力」シートを参加者に共有（⚙️管理は共有しない）"
  );
}

// ============================
// 賭け入力シート（全ラウンド1枚 + 合計表示）
// ============================
function setupBetSheet(ss) {
  let sheet = ss.getSheetByName("🎯賭け入力");
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet("🎯賭け入力", 0);

  // 参加者リストを管理シートから取得
  const adminSheet = ss.getSheetByName("⚙️管理");
  const participants = getParticipantList(ss);
  const oddsMap = {};
  TEAMS.forEach(t => { oddsMap[t.name] = t.odds; });

  const totalCols = Math.max(participants.length + 4, 5);

  // タイトル行
  sheet.getRange(1, 1, 1, totalCols).merge()
    .setValue("🎯 賭け入力 — 自分の列にチーム名を入力（例: ブラジル）")
    .setBackground("#1a3a5c").setFontColor("#f0c040")
    .setFontSize(13).setFontWeight("bold");

  // ルール行
  sheet.getRange(2, 1, 1, totalCols).merge()
    .setValue(`📌 1試合${CFG.betUnit}円固定・上限${CFG.maxBudget}円｜強い方が勝つ→1.5倍、弱い方が勝つ→2倍｜締切を過ぎると入力不可`)
    .setBackground("#0a1628").setFontColor("#8ab4d8").setFontStyle("italic").setFontSize(10);

  // ヘッダー行
  const headerRow = ["ラウンド", "試合ID", "対戦カード", "締切", ...participants];
  sheet.getRange(3, 1, 1, headerRow.length).setValues([headerRow])
    .setBackground("#0d2137").setFontColor("#6a9bc0").setFontWeight("bold");
  for (let j = 0; j < participants.length; j++) {
    sheet.getRange(3, j + 5).setBackground("#1a3a5c").setFontColor("#f0c040")
      .setHorizontalAlignment("center").setFontWeight("bold");
  }

  // 試合行
  let row = 4;
  ROUNDS.forEach(round => {
    sheet.getRange(row, 1, 1, totalCols).merge()
      .setValue(`── ${round.name}　締切: ${round.deadline} ──`)
      .setBackground("#0a1628").setFontColor("#f0c040")
      .setFontStyle("italic").setHorizontalAlignment("center");
    row++;

    round.matches.forEach((match, mi) => {
      let card, matchDeadline;
      if (match.teamA === "TBD") {
        card = "（対戦カード未定）";
        matchDeadline = match.deadline || round.deadline;
      } else {
        const oddsA = oddsMap[match.teamA] || 999;
        const oddsB = oddsMap[match.teamB] || 999;
        const favA = oddsA <= oddsB;
        const labelA = `${match.teamA}(${favA ? "★強" : "弱"}・${favA ? CFG.favoriteMultiplier : CFG.underdogMultiplier}倍)`;
        const labelB = `${match.teamB}(${!favA ? "★強" : "弱"}・${!favA ? CFG.favoriteMultiplier : CFG.underdogMultiplier}倍)`;
        card = `${labelA} vs ${labelB}`;
        matchDeadline = match.deadline || round.deadline;
      }
      sheet.getRange(row, 1, 1, 4).setValues([[round.name, match.id, card, matchDeadline]]);
      const bg = mi % 2 === 0 ? "#0d2137" : "#0a1628";
      sheet.getRange(row, 1, 1, totalCols).setBackground(bg);
      sheet.getRange(row, 1).setFontColor("#8ab4d8");
      sheet.getRange(row, 2).setFontColor("#6a9bc0");
      sheet.getRange(row, 3).setFontColor("#c0d8f0");
      sheet.getRange(row, 4).setFontColor("#aaaaaa").setFontSize(9);
      for (let j = 0; j < participants.length; j++) {
        sheet.getRange(row, j + 5)
          .setFontColor("#f0c040").setFontWeight("bold").setHorizontalAlignment("center");
      }
      row++;
    });
  });

  const lastMatchRow = row - 1;

  // ── 合計表示 ──
  row++; // 空白行
  sheet.getRange(row, 1, 1, totalCols).merge()
    .setValue("── 賭け状況まとめ ──")
    .setBackground("#1a3a5c").setFontColor("#f0c040")
    .setFontStyle("italic").setHorizontalAlignment("center");
  row++;

  // 合計使用額
  sheet.getRange(row, 1, 1, 4).setValues([["", "", "合計使用額（円）", ""]]);
  sheet.getRange(row, 3).setFontColor("#6a9bc0").setFontWeight("bold").setHorizontalAlignment("right");
  for (let j = 0; j < participants.length; j++) {
    const col = j + 5;
    const colLetter = columnToLetter(col);
    // 4行目〜lastMatchRow行の間でチーム名が入力されているセルを数える × 100
    sheet.getRange(row, col)
      .setFormula(`=COUNTA(${colLetter}4:${colLetter}${lastMatchRow})*${CFG.betUnit}`)
      .setFontColor("#f0c040").setFontWeight("bold").setHorizontalAlignment("center")
      .setBackground("#0d2137");
  }
  sheet.getRange(row, 1, 1, totalCols).setBackground("#0d2137");
  row++;

  // 残り予算
  sheet.getRange(row, 1, 1, 4).setValues([["", "", "残り予算（円）", ""]]);
  sheet.getRange(row, 3).setFontColor("#6a9bc0").setFontWeight("bold").setHorizontalAlignment("right");
  for (let j = 0; j < participants.length; j++) {
    const col = j + 5;
    const prevRowRef = columnToLetter(col) + (row - 1);
    sheet.getRange(row, col)
      .setFormula(`=${CFG.maxBudget}-${prevRowRef}`)
      .setFontWeight("bold").setHorizontalAlignment("center")
      .setBackground("#0a1628");
    // 残り予算がマイナスなら赤色（条件付き書式は別途設定）
  }
  sheet.getRange(row, 1, 1, totalCols).setBackground("#0a1628");

  // 列幅
  sheet.setColumnWidth(1, 110);
  sheet.setColumnWidth(2, 90);
  sheet.setColumnWidth(3, 200);
  sheet.setColumnWidth(4, 140);
  for (let j = 0; j < participants.length; j++) sheet.setColumnWidth(j + 5, 120);

  sheet.setFrozenRows(3);
  return sheet;
}

function rebuildBetSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  setupBetSheet(ss);
  SpreadsheetApp.getUi().alert("✅ 賭け入力シートを再生成しました！");
}

// ============================
// 管理シート（参加者マスタ + 結果入力 を1枚に統合）
// ============================
function setupAdminSheet(ss) {
  let sheet = ss.getSheetByName("⚙️管理");
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet("⚙️管理", 1);

  // ── セクション1: 参加者マスタ ──
  let r = ADMIN_MASTER_ROW;
  sheet.getRange(r, 1, 1, 3).merge()
    .setValue("【1】👥 参加者マスタ — 名前とメールアドレスを入力")
    .setBackground("#1a3a5c").setFontColor("#f0c040").setFontSize(13).setFontWeight("bold");
  r++;
  sheet.getRange(r, 1, 1, 3).setValues([["名前", "メールアドレス", "備考"]])
    .setBackground("#0d2137").setFontColor("#6a9bc0").setFontWeight("bold");
  r++;
  const samples = [
    ["田中太郎", "tanaka@example.com", ""],
    ["鈴木花子", "suzuki@example.com", ""],
    ["佐藤次郎", "sato@example.com",   "（サンプル：削除してOK）"],
  ];
  sheet.getRange(r, 1, samples.length, 3).setValues(samples);
  r += samples.length;
  sheet.getRange(r + 1, 1).setValue("※ 入力後「⚽TOTO管理」→「賭け入力シートを再生成」を実行")
    .setFontColor("#888888").setFontStyle("italic");

  sheet.setColumnWidth(1, 130);
  sheet.setColumnWidth(2, 220);
  sheet.setColumnWidth(3, 200);

  // ── セクション2: 結果入力 ──
  r = ADMIN_RESULT_ROW;
  sheet.getRange(r, 1, 1, 7).merge()
    .setValue("【2】📋 結果入力 — 試合が終わったらスコアを入力（G列の勝者は自動計算）")
    .setBackground("#1a3a5c").setFontColor("#f0c040").setFontSize(13).setFontWeight("bold");
  r++;
  sheet.getRange(r, 1, 1, 7).setValues([["試合ID", "ラウンド", "チームA", "チームB", "スコアA", "スコアB", "勝者（自動）"]])
    .setBackground("#0d2137").setFontColor("#6a9bc0").setFontWeight("bold");
  r++;

  ROUNDS.forEach(round => {
    sheet.getRange(r, 1, 1, 7).merge()
      .setValue(`── ${round.name} ──`)
      .setBackground("#0a1628").setFontColor("#8ab4d8")
      .setFontStyle("italic").setHorizontalAlignment("center");
    r++;
    round.matches.forEach(match => {
      sheet.getRange(r, 1, 1, 4).setValues([[match.id, round.id, match.teamA, match.teamB]]);
      sheet.getRange(r, 7).setFormula(
        `=IF(AND(E${r}<>"",F${r}<>""),IF(E${r}>F${r},C${r},IF(E${r}<F${r},D${r},"PK")),"")`
      ).setBackground("#e8f5e9");
      r++;
    });
  });

  sheet.getRange(r + 1, 1).setValue("※ PKの場合は勝者列（G列）に直接勝者チーム名を手入力")
    .setFontColor("#888888").setFontStyle("italic");

  sheet.setColumnWidth(4, 170); // チームB列は長い名前があるので広げる
  sheet.setColumnWidth(7, 170);

  sheet.getRange(ADMIN_VIEW_ROW, 1).setValue("← 「⚽TOTO管理」→「胴元ビューを更新」を実行するとここに集計が表示されます")
    .setFontColor("#888888").setFontStyle("italic");

  return sheet;
}

// ============================
// onEditトリガー
// ============================
function setupOnEditTrigger() {
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === "onEditLockBet")
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger("onEditLockBet").forSpreadsheet(SpreadsheetApp.getActive()).onEdit().create();
}

function onEditLockBet(e) {
  if (!e) return;
  const sheet = e.range.getSheet();

  // 管理シートの参加者マスタ（A列）が編集されたら賭け入力を自動再生成
  if (sheet.getName() === "⚙️管理") {
    const row = e.range.getRow();
    const col = e.range.getColumn();
    if (row >= ADMIN_MASTER_ROW + 2 && row < ADMIN_RESULT_ROW && col === 1) {
      setupBetSheet(SpreadsheetApp.getActiveSpreadsheet());
    }
    return;
  }

  if (sheet.getName() !== "🎯賭け入力") return;
  const row = e.range.getRow();
  const col = e.range.getColumn();
  if (row < 4 || col < 5) return;

  const deadlineVal = sheet.getRange(row, 4).getValue();
  if (!deadlineVal) return;
  const deadline = new Date(deadlineVal);
  const now = new Date();
  if (now > deadline) {
    e.range.setValue(e.oldValue || "");
    SpreadsheetApp.getUi().alert(`⛔ 締切（${deadlineVal}）を過ぎているため入力できません。`);
  }
}

// ============================
// 胴元ビュー更新
// ============================
function updateAdminView() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const adminSheet = ss.getSheetByName("⚙️管理");
  const betSheet   = ss.getSheetByName("🎯賭け入力");

  if (!adminSheet || !betSheet) {
    SpreadsheetApp.getUi().alert("❌ シートが見つかりません。setupAllを実行してください。");
    return;
  }

  // 胴元ビューエリアをクリア
  const lastRow = adminSheet.getLastRow();
  if (lastRow >= ADMIN_VIEW_ROW) {
    adminSheet.getRange(ADMIN_VIEW_ROW, 1, lastRow - ADMIN_VIEW_ROW + 1, 15).clearContent().clearFormat();
  }

  const participants = getParticipantList(ss);
  const betData = betSheet.getDataRange().getValues();
  const betHeaderRow = betData[2];
  const oddsMap = {};
  TEAMS.forEach(t => { oddsMap[t.name] = t.odds; });

  // 結果マップ
  const adminData = adminSheet.getDataRange().getValues();
  const winnerMap = {};
  const matchTeamsMap = {};
  for (let i = ADMIN_RESULT_ROW; i < adminData.length; i++) {
    const id = adminData[i][0];
    if (!id || String(id).startsWith("──")) continue;
    const winner = adminData[i][6];
    matchTeamsMap[id] = { teamA: adminData[i][2], teamB: adminData[i][3] };
    if (winner && winner !== "") winnerMap[id] = winner;
  }

  function getFavorite(matchId) {
    const t = matchTeamsMap[matchId];
    if (!t || t.teamA === "TBD") return null;
    return (oddsMap[t.teamA] || 999) <= (oddsMap[t.teamB] || 999) ? t.teamA : t.teamB;
  }

  const stats = participants.map(name => {
    const colIdx = betHeaderRow.findIndex(c => c === name);
    let totalBet = 0, totalPayout = 0, hitCount = 0;
    const betsByRound = {};
    ROUNDS.forEach(round => {
      round.matches.forEach(match => {
        const betRow = findBetRow(betData, match.id);
        if (!betRow || colIdx < 0) return;
        const bet = String(betRow[colIdx] || "").trim();
        if (!bet) return;
        totalBet += CFG.betUnit;
        betsByRound[round.id] = (betsByRound[round.id] || 0) + 1;
        const winner = winnerMap[match.id];
        if (winner && bet === winner) {
          const fav = getFavorite(match.id);
          totalPayout += Math.round(CFG.betUnit * (winner === fav ? CFG.favoriteMultiplier : CFG.underdogMultiplier));
          hitCount++;
        }
      });
    });
    return { name, totalBet, totalPayout, hitCount, betsByRound, over: totalBet > CFG.maxBudget };
  });

  let row = ADMIN_VIEW_ROW;

  // タイトル
  adminSheet.getRange(row, 1, 1, 10).merge()
    .setValue("【3】📊 胴元ビュー　最終更新: " + new Date().toLocaleString("ja-JP"))
    .setBackground("#1a3a5c").setFontColor("#f0c040").setFontSize(13).setFontWeight("bold");
  row++;

  // ── 参加者別集計 ──
  adminSheet.getRange(row, 1, 1, 10).merge()
    .setValue("▶ 参加者別 賭け状況")
    .setBackground("#0d2137").setFontColor("#8ab4d8").setFontWeight("bold");
  row++;
  adminSheet.getRange(row, 1, 1, 10).setValues([["名前","合計使用額","残り予算","上限超過？","獲得金額","的中数","R32","R16","QF","SF/決勝"]])
    .setBackground("#0a1628").setFontColor("#6a9bc0").setFontWeight("bold");
  row++;
  stats.forEach(s => {
    const sfFinal = (s.betsByRound["SF"] || 0) + (s.betsByRound["Final"] || 0);
    adminSheet.getRange(row, 1, 1, 10).setValues([[
      s.name, `${s.totalBet}円`, `${CFG.maxBudget - s.totalBet}円`,
      s.over ? "⚠️ 超過！" : "OK",
      `${s.totalPayout}円`, s.hitCount,
      s.betsByRound["R32"] || 0, s.betsByRound["R16"] || 0,
      s.betsByRound["QF"] || 0, sfFinal
    ]]);
    adminSheet.getRange(row, 4).setFontColor(s.over ? "#ef5350" : "#00e676").setFontWeight("bold");
    row++;
  });

  row += 2;

  // ── SIM ──
  adminSheet.getRange(row, 1, 1, participants.length + 3).merge()
    .setValue("▶ SIM — このチームが勝ったら誰が何円獲得？（強い方→1.5倍、弱い方→2倍）")
    .setBackground("#0d2137").setFontColor("#8ab4d8").setFontWeight("bold");
  row++;
  adminSheet.getRange(row, 1, 1, participants.length + 3)
    .setValues([["ラウンド", "試合ID", "もし勝者が…", ...participants]])
    .setBackground("#0a1628").setFontColor("#6a9bc0").setFontWeight("bold");
  row++;

  ROUNDS.forEach(round => {
    round.matches.forEach((match, mi) => {
      const betRow = findBetRow(betData, match.id);
      if (!betRow) return;
      const teams = match.teamA === "TBD" ? ["（未定）"] : [match.teamA, match.teamB];
      const oddsA = oddsMap[match.teamA] || 999;
      const oddsB = oddsMap[match.teamB] || 999;
      const favorite = match.teamA === "TBD" ? null : (oddsA <= oddsB ? match.teamA : match.teamB);

      teams.forEach((team, ti) => {
        const mult = (team === favorite) ? CFG.favoriteMultiplier : CFG.underdogMultiplier;
        const label = match.teamA === "TBD" ? "（未定）" : `${team}（${team === favorite ? "強" : "弱"}・${mult}倍）`;
        const simRow = [round.name, match.id, label];
        participants.forEach(name => {
          const colIdx = betHeaderRow.findIndex(c => c === name);
          const bet = colIdx >= 0 ? String(betRow[colIdx] || "").trim() : "";
          simRow.push(bet === team ? `+${Math.round(CFG.betUnit * mult)}円` : bet !== "" ? "ハズレ" : "-");
        });
        adminSheet.getRange(row, 1, 1, simRow.length).setValues([simRow]);
        const bg = (mi * 2 + ti) % 2 === 0 ? "#0d2137" : "#0a1628";
        adminSheet.getRange(row, 1, 1, simRow.length).setBackground(bg);
        for (let j = 0; j < participants.length; j++) {
          const v = simRow[j + 3];
          adminSheet.getRange(row, j + 4)
            .setFontColor(String(v).startsWith("+") ? "#00e676" : v === "ハズレ" ? "#ef5350" : "#555555")
            .setFontWeight(String(v).startsWith("+") ? "bold" : "normal")
            .setHorizontalAlignment("center");
        }
        row++;
      });
    });
  });

  row += 2;

  // ── ランキング ──
  adminSheet.getRange(row, 1, 1, 5).merge()
    .setValue("▶ ランキング（結果入力後に反映）")
    .setBackground("#0d2137").setFontColor("#8ab4d8").setFontWeight("bold");
  row++;
  adminSheet.getRange(row, 1, 1, 5).setValues([["順位","名前","獲得金額","的中数","賞金予測"]])
    .setBackground("#0a1628").setFontColor("#6a9bc0").setFontWeight("bold");
  row++;
  const totalPool = stats.reduce((sum, s) => sum + s.totalBet, 0);
  const prizePool = Math.floor(totalPool * 0.8);
  const prizes = CFG.prizeRatio.map(r => Math.floor(prizePool * r));
  [...stats].sort((a, b) => b.totalPayout - a.totalPayout).forEach((s, i) => {
    const rank = i + 1;
    const medal = rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : String(rank);
    adminSheet.getRange(row, 1, 1, 5).setValues([[medal, s.name, `${s.totalPayout}円`, s.hitCount, rank <= 3 ? `${prizes[rank-1]}円` : "-"]]);
    const bg = rank === 1 ? "#fff8dc" : rank === 2 ? "#f5f5f5" : rank === 3 ? "#fde8d0" : null;
    if (bg) adminSheet.getRange(row, 1, 1, 5).setBackground(bg);
    row++;
  });
  adminSheet.getRange(row + 1, 1).setValue(`賞金プール: ${prizePool.toLocaleString()}円（全賭け金の80%）`)
    .setFontColor("#8ab4d8").setFontStyle("italic");

  SpreadsheetApp.getUi().alert("✅ 胴元ビューを更新しました！");
}

// ============================
// ユーティリティ
// ============================
function getParticipantList(ss) {
  const adminSheet = ss.getSheetByName("⚙️管理");
  if (!adminSheet) return [];
  const data = adminSheet.getDataRange().getValues();
  const participants = [];
  const dataStart = ADMIN_MASTER_ROW + 2 - 1; // 0-indexed
  const dataEnd   = ADMIN_RESULT_ROW - 1;     // 0-indexed
  for (let i = dataStart; i < Math.min(dataEnd, data.length); i++) {
    if (data[i][0] && String(data[i][0]).trim() !== "") participants.push(String(data[i][0]).trim());
  }
  return participants;
}

function findBetRow(betData, matchId) {
  for (let i = 3; i < betData.length; i++) {
    if (betData[i][1] === matchId) return betData[i];
  }
  return null;
}

function columnToLetter(col) {
  let letter = "";
  while (col > 0) {
    const rem = (col - 1) % 26;
    letter = String.fromCharCode(65 + rem) + letter;
    col = Math.floor((col - 1) / 26);
  }
  return letter;
}

// ============================
// リマインドメール送信
// ============================
function sendReminderNow() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const adminSheet = ss.getSheetByName("⚙️管理");
  const data = adminSheet.getDataRange().getValues();
  const today = new Date();
  const nextRound = ROUNDS.find(r => new Date(r.deadline) >= today);
  if (!nextRound) { SpreadsheetApp.getUi().alert("リマインド対象のラウンドが見つかりません。"); return; }
  const ssUrl = ss.getUrl();
  let sentCount = 0;
  const dataStart = ADMIN_MASTER_ROW + 2 - 1;
  const dataEnd   = ADMIN_RESULT_ROW - 1;
  for (let i = dataStart; i < Math.min(dataEnd, data.length); i++) {
    const name = data[i][0];
    const email = data[i][1];
    if (!name || !email || !String(email).includes("@")) continue;
    GmailApp.sendEmail(email,
      `⚽【TOTO】${nextRound.name}の賭け締切が近づいています！`,
      `${name} さん\n\n${nextRound.name}の締切が近づいています！\n\n📋 賭けシートはこちら:\n${ssUrl}\n\n⏰ 締切: ${nextRound.deadline}\n💰「🎯賭け入力」タブを開いて、自分の列にチーム名を入力\n\n胴元: ${CFG.administrator}`
    );
    sentCount++;
  }
  SpreadsheetApp.getUi().alert(`✅ ${sentCount}名にリマインドメールを送信しました`);
}

// ============================
// GAS Web App：HTML or JSON配信
// ============================
function doGet(e) {
  const params = e && e.parameter ? e.parameter : {};
  if (params.data === "1") {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const data = getPublicData(ss);
    return ContentService.createTextOutput(JSON.stringify(data)).setMimeType(ContentService.MimeType.JSON);
  }
  return HtmlService.createHtmlOutputFromFile("index")
    .setTitle("⚽ 社内ワールドカップTOTO 2026")
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function getPublicData(ss) {
  const adminSheet = ss.getSheetByName("⚙️管理");
  const betSheet   = ss.getSheetByName("🎯賭け入力");

  const participants = getParticipantList(ss);

  // 結果マップ
  const adminData = adminSheet.getDataRange().getValues();
  const matches = [];
  const winnerMap = {};
  for (let i = ADMIN_RESULT_ROW; i < adminData.length; i++) {
    const id = adminData[i][0];
    if (!id || String(id).startsWith("──") || String(id).startsWith("【") || String(id).startsWith("▶")) continue;
    const roundId = adminData[i][1];
    const teamA   = adminData[i][2];
    const teamB   = adminData[i][3];
    const scoreA  = adminData[i][4];
    const scoreB  = adminData[i][5];
    const winner  = adminData[i][6] || null;
    if (roundId && teamA && !String(teamA).startsWith("──")) {
      matches.push({ id, round: roundId, teamA, teamB, scoreA: scoreA || null, scoreB: scoreB || null, winner });
      if (winner) winnerMap[id] = winner;
    }
  }

  const betData = betSheet.getDataRange().getValues();
  const betHeaderRow = betData[2];
  const oddsMap = {};
  TEAMS.forEach(t => { oddsMap[t.name] = t.odds; });

  const stats = participants.map(name => {
    const colIdx = betHeaderRow.findIndex(c => c === name);
    const bets = {};
    let totalBet = 0, totalPayout = 0, hitCount = 0;
    ROUNDS.forEach(round => {
      round.matches.forEach(match => {
        const betRow = findBetRow(betData, match.id);
        if (!betRow || colIdx < 0) return;
        const bet = String(betRow[colIdx] || "").trim();
        if (!bet) return;
        bets[match.id] = bet;
        totalBet += 100;
        const winner = winnerMap[match.id];
        if (winner && bet === winner) {
          const oddsA = oddsMap[match.teamA] || 999;
          const oddsB = oddsMap[match.teamB] || 999;
          const fav = oddsA <= oddsB ? match.teamA : match.teamB;
          totalPayout += Math.round(100 * (winner === fav ? 1.5 : 2.0));
          hitCount++;
        }
      });
    });
    return { name, bets, totalBet, totalPayout, hitCount };
  });
  stats.sort((a, b) => b.totalPayout - a.totalPayout);

  const totalPool = stats.reduce((sum, s) => sum + s.totalBet, 0);
  const prizePool = Math.floor(totalPool * 0.8);

  return {
    updatedAt: new Date().toLocaleString("ja-JP"),
    administrator: CFG.administrator,
    prizePool,
    participants: stats,
    matches,
    rounds: ROUNDS.map(r => ({ id: r.id, name: r.name, deadline: r.deadline })),
  };
}
