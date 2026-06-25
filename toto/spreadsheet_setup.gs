/**
 * 社内ワールドカップTOTO 2026 - Google Apps Script（シンプル版）
 *
 * 【使い方】
 * 1. スプレッドシートの「拡張機能」→「Apps Script」にこのコードを貼り付けて保存
 * 2. 「setupAll」を実行して初回セットアップ
 * 3.「👥参加者マスタ」に参加者名・メールを入力してから「🎯賭け入力」を再生成
 */

// ============================
// 胴元設定（ここを変更してOK）
// ============================
const CFG = {
  administrator: "タロウ",
  maxBudget: 1000,
  betUnit: 100,
  prizeRatio: [0.50, 0.30, 0.20],
  favoriteMultiplier: 1.5,  // 強い方（オッズ低い）が勝った場合の倍率
  underdogMultiplier: 2.0,  // 弱い方（オッズ高い）が勝った場合の倍率
};

// ============================
// チームとオッズ
// ============================
const TEAMS = [
  { name: "ブラジル",         odds: 4.5  },
  { name: "フランス",         odds: 5.0  },
  { name: "スペイン",         odds: 5.5  },
  { name: "アルゼンチン",     odds: 6.0  },
  { name: "イングランド",     odds: 7.0  },
  { name: "ドイツ",           odds: 8.0  },
  { name: "ポルトガル",       odds: 9.0  },
  { name: "オランダ",         odds: 10.0 },
  { name: "ベルギー",         odds: 12.0 },
  { name: "クロアチア",       odds: 15.0 },
  { name: "ウルグアイ",       odds: 18.0 },
  { name: "メキシコ",         odds: 20.0 },
  { name: "アメリカ",         odds: 25.0 },
  { name: "モロッコ",         odds: 35.0 },
  { name: "日本",             odds: 40.0 },
  { name: "韓国",             odds: 50.0 },
  { name: "セネガル",         odds: 45.0 },
  { name: "オーストラリア",   odds: 60.0 },
  { name: "スイス",           odds: 30.0 },
  { name: "デンマーク",       odds: 35.0 },
  { name: "チュニジア",       odds: 80.0 },
  { name: "カナダ",           odds: 40.0 },
  { name: "チリ",             odds: 50.0 },
  { name: "ガーナ",           odds: 70.0 },
  { name: "ナイジェリア",     odds: 55.0 },
  { name: "ポーランド",       odds: 65.0 },
  { name: "コロンビア",       odds: 30.0 },
  { name: "コートジボワール", odds: 60.0 },
  { name: "エクアドル",       odds: 55.0 },
  { name: "セルビア",         odds: 45.0 },
  { name: "スウェーデン",     odds: 40.0 },
  { name: "カメルーン",       odds: 70.0 },
];

// ============================
// ラウンド別試合カード
// ============================
const ROUNDS = [
  {
    id: "R32", name: "ラウンド32",
    deadline: "2026-06-29 19:00",
    matches: [
      { id: "R32-01", teamA: "ブラジル",     teamB: "セネガル"         },
      { id: "R32-02", teamA: "フランス",     teamB: "モロッコ"         },
      { id: "R32-03", teamA: "スペイン",     teamB: "メキシコ"         },
      { id: "R32-04", teamA: "アルゼンチン", teamB: "オーストラリア"   },
      { id: "R32-05", teamA: "イングランド", teamB: "スイス"           },
      { id: "R32-06", teamA: "ドイツ",       teamB: "デンマーク"       },
      { id: "R32-07", teamA: "ポルトガル",   teamB: "チュニジア"       },
      { id: "R32-08", teamA: "オランダ",     teamB: "韓国"             },
      { id: "R32-09", teamA: "ベルギー",     teamB: "カナダ"           },
      { id: "R32-10", teamA: "クロアチア",   teamB: "チリ"             },
      { id: "R32-11", teamA: "ウルグアイ",   teamB: "ガーナ"           },
      { id: "R32-12", teamA: "アメリカ",     teamB: "ナイジェリア"     },
      { id: "R32-13", teamA: "日本",         teamB: "ポーランド"       },
      { id: "R32-14", teamA: "コロンビア",   teamB: "コートジボワール" },
      { id: "R32-15", teamA: "エクアドル",   teamB: "セルビア"         },
      { id: "R32-16", teamA: "スウェーデン", teamB: "カメルーン"       },
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
// 初回セットアップ（4枚のシートを作成）
// ============================
function setupAll() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  setupMasterSheet(ss);
  setupResultSheet(ss);
  setupBetSheet(ss);
  setupAdminView(ss);

  // デフォルトシート削除
  ["シート1", "Sheet1"].forEach(name => {
    const s = ss.getSheetByName(name);
    if (s && ss.getSheets().length > 1) ss.deleteSheet(s);
  });

  // onEditトリガーを設定
  setupOnEditTrigger();

  SpreadsheetApp.getUi().alert(
    "✅ セットアップ完了！\n\n" +
    "【次のステップ】\n" +
    "1.「👥参加者マスタ」に参加者名・メールを入力\n" +
    "2.「⚽TOTO管理」→「賭け入力シートを再生成」を実行\n" +
    "3.「🎯賭け入力」シートを参加者に共有"
  );
}

// ============================
// 参加者マスタシート
// ============================
function setupMasterSheet(ss) {
  let sheet = ss.getSheetByName("👥参加者マスタ");
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet("👥参加者マスタ", 0);

  sheet.getRange("A1:C1").merge()
    .setValue("👥 参加者マスタ — 名前とメールを入力してください")
    .setBackground("#1a3a5c").setFontColor("#f0c040")
    .setFontSize(13).setFontWeight("bold");

  sheet.getRange("A2:C2").setValues([["名前", "メールアドレス", "備考"]])
    .setBackground("#0d2137").setFontColor("#6a9bc0").setFontWeight("bold");

  const samples = [
    ["田中太郎", "tanaka@example.com", ""],
    ["鈴木花子", "suzuki@example.com", ""],
    ["佐藤次郎", "sato@example.com",   "（サンプル：削除してOK）"],
  ];
  sheet.getRange(3, 1, samples.length, 3).setValues(samples);

  sheet.setColumnWidth(1, 130);
  sheet.setColumnWidth(2, 220);
  sheet.setColumnWidth(3, 200);

  sheet.getRange("A7").setValue("※ 入力後「⚽TOTO管理」→「賭け入力シートを再生成」を実行してください")
    .setFontColor("#888888").setFontStyle("italic");
}

// ============================
// 結果入力シート
// ============================
function setupResultSheet(ss) {
  let sheet = ss.getSheetByName("📋結果入力");
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet("📋結果入力", 1);

  sheet.getRange("A1:G1").merge()
    .setValue("📋 結果入力 — 試合が終わったらスコアを入力")
    .setBackground("#1a3a5c").setFontColor("#f0c040")
    .setFontSize(13).setFontWeight("bold");

  sheet.getRange("A2:G2").setValues([["試合ID", "ラウンド", "チームA", "チームB", "スコアA", "スコアB", "勝者（自動）"]])
    .setBackground("#0d2137").setFontColor("#6a9bc0").setFontWeight("bold");

  let row = 3;
  ROUNDS.forEach(round => {
    // ラウンドヘッダー行
    sheet.getRange(row, 1, 1, 7).merge()
      .setValue(`── ${round.name} ──`)
      .setBackground("#0a1628").setFontColor("#8ab4d8")
      .setFontStyle("italic").setHorizontalAlignment("center");
    row++;

    round.matches.forEach(match => {
      sheet.getRange(row, 1, 1, 4).setValues([[match.id, round.id, match.teamA, match.teamB]]);
      sheet.getRange(row, 7).setFormula(
        `=IF(AND(E${row}<>"",F${row}<>""),IF(E${row}>F${row},C${row},IF(E${row}<F${row},D${row},"PK")),"")`
      );
      sheet.getRange(row, 1).setFontColor("#6a9bc0");
      sheet.getRange(row, 2).setFontColor("#8ab4d8");
      sheet.getRange(row, 3, 1, 2).setFontColor("#c0d8f0");
      sheet.getRange(row, 7).setBackground("#e8f5e9");
      row++;
    });
  });

  sheet.setColumnWidth(1, 90);
  sheet.setColumnWidth(2, 100);
  sheet.setColumnWidth(3, 160);
  sheet.setColumnWidth(4, 160);
  sheet.setColumnWidth(5, 80);
  sheet.setColumnWidth(6, 80);
  sheet.setColumnWidth(7, 160);

  sheet.getRange(row + 1, 1).setValue("※ PKの場合は勝者列（G列）に直接勝者チーム名を手入力")
    .setFontColor("#888888").setFontStyle("italic");
}

// ============================
// 賭け入力シート（全ラウンド1枚）
// ============================
function setupBetSheet(ss) {
  let sheet = ss.getSheetByName("🎯賭け入力");
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet("🎯賭け入力", 2);

  const master = ss.getSheetByName("👥参加者マスタ");
  const masterData = master.getDataRange().getValues();
  const participants = [];
  for (let i = 2; i < masterData.length; i++) {
    if (masterData[i][0] && masterData[i][0] !== "") participants.push(masterData[i][0]);
  }

  // タイトル
  const totalCols = participants.length + 4;
  sheet.getRange(1, 1, 1, totalCols).merge()
    .setValue("🎯 賭け入力 — 自分の列に賭けたいチーム名を入力（例: ブラジル）")
    .setBackground("#1a3a5c").setFontColor("#f0c040")
    .setFontSize(13).setFontWeight("bold");

  sheet.getRange(2, 1, 1, totalCols).merge()
    .setValue(`📌 1試合${CFG.betUnit}円固定・合計上限${CFG.maxBudget}円。締切を過ぎると入力できなくなります。`)
    .setBackground("#0a1628").setFontColor("#8ab4d8").setFontStyle("italic");

  // ヘッダー行
  const headerRow = ["ラウンド", "試合ID", "対戦カード", "締切", ...participants];
  sheet.getRange(3, 1, 1, headerRow.length).setValues([headerRow])
    .setBackground("#0d2137").setFontColor("#6a9bc0").setFontWeight("bold");

  // 参加者列を目立たせる
  for (let j = 0; j < participants.length; j++) {
    sheet.getRange(3, j + 5).setBackground("#1a3a5c").setFontColor("white").setHorizontalAlignment("center");
  }

  // 試合行
  let row = 4;
  ROUNDS.forEach(round => {
    // ラウンドセパレーター
    sheet.getRange(row, 1, 1, totalCols).merge()
      .setValue(`── ${round.name}　締切: ${round.deadline} ──`)
      .setBackground("#0a1628").setFontColor("#f0c040")
      .setFontStyle("italic").setHorizontalAlignment("center");
    row++;

    round.matches.forEach((match, mi) => {
      const card = match.teamA === "TBD" ? "（対戦カード未定）" : `${match.teamA} vs ${match.teamB}`;
      const rowData = [round.name, match.id, card, round.deadline];
      sheet.getRange(row, 1, 1, 4).setValues([rowData]);
      sheet.getRange(row, 1).setFontColor("#8ab4d8");
      sheet.getRange(row, 2).setFontColor("#6a9bc0");
      sheet.getRange(row, 3).setFontColor("#c0d8f0");
      sheet.getRange(row, 4).setFontColor("#aaaaaa").setFontSize(9);

      const bg = mi % 2 === 0 ? "#0d2137" : "#0a1628";
      sheet.getRange(row, 1, 1, totalCols).setBackground(bg);
      sheet.getRange(row, 1).setBackground(bg).setFontColor("#8ab4d8");
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

  // 列幅
  sheet.setColumnWidth(1, 110);
  sheet.setColumnWidth(2, 90);
  sheet.setColumnWidth(3, 200);
  sheet.setColumnWidth(4, 140);
  for (let j = 0; j < participants.length; j++) {
    sheet.setColumnWidth(j + 5, 110);
  }

  sheet.setFrozenRows(3);

  return sheet;
}

function rebuildBetSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  setupBetSheet(ss);
  SpreadsheetApp.getUi().alert("✅ 賭け入力シートを再生成しました！");
}

// ============================
// onEditトリガー：締切後ロック
// ============================
function setupOnEditTrigger() {
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === "onEditLockBet")
    .forEach(t => ScriptApp.deleteTrigger(t));

  ScriptApp.newTrigger("onEditLockBet")
    .forSpreadsheet(SpreadsheetApp.getActive())
    .onEdit()
    .create();
}

function onEditLockBet(e) {
  if (!e) return;
  const sheet = e.range.getSheet();

  // 参加者マスタが編集されたら賭け入力シートを自動更新
  if (sheet.getName() === "👥参加者マスタ") {
    const row = e.range.getRow();
    const col = e.range.getColumn();
    if (row >= 3 && col === 1) { // 名前列（A列）が変更された場合
      const ss = SpreadsheetApp.getActiveSpreadsheet();
      setupBetSheet(ss);
    }
    return;
  }

  if (sheet.getName() !== "🎯賭け入力") return;

  const row = e.range.getRow();
  const col = e.range.getColumn();
  if (row < 4 || col < 5) return; // ヘッダー行・ラウンド列は無視

  // D列（4列目）が締切時刻
  const deadlineStr = sheet.getRange(row, 4).getValue();
  if (!deadlineStr) return;

  const deadline = new Date(deadlineStr);
  const now = new Date();

  if (now > deadline) {
    e.range.setValue(e.oldValue || "");
    SpreadsheetApp.getUi().alert(`⛔ 締切（${deadlineStr}）を過ぎているため入力できません。`);
  }
}

// ============================
// 胴元ビューシート
// ============================
function setupAdminView(ss) {
  let sheet = ss.getSheetByName("📊胴元ビュー");
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet("📊胴元ビュー", 3);

  sheet.getRange("A1").setValue("「⚽TOTO管理」→「胴元ビューを更新」を実行すると最新情報が表示されます")
    .setBackground("#1a3a5c").setFontColor("#f0c040").setFontWeight("bold");
  sheet.getRange("A1:H1").merge().setHorizontalAlignment("center");
}

function updateAdminView() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const masterSheet = ss.getSheetByName("👥参加者マスタ");
  const resultSheet = ss.getSheetByName("📋結果入力");
  const betSheet    = ss.getSheetByName("🎯賭け入力");
  let   adminSheet  = ss.getSheetByName("📊胴元ビュー");

  if (!adminSheet) adminSheet = ss.insertSheet("📊胴元ビュー", 3);
  adminSheet.clearContents();
  adminSheet.clearFormats();

  // 参加者リスト
  const masterData = masterSheet.getDataRange().getValues();
  const participants = [];
  for (let i = 2; i < masterData.length; i++) {
    if (masterData[i][0] && masterData[i][0] !== "") participants.push(masterData[i][0]);
  }

  // 賭けデータ読み込み
  const betData = betSheet.getDataRange().getValues();
  const betHeaderRow = betData[2]; // 3行目（0-indexed:2）がヘッダー

  // オッズマップ（強い・弱い判定用）
  const oddsMap = {};
  TEAMS.forEach(t => { oddsMap[t.name] = t.odds; });

  // 結果マップ（試合ID → 勝者）
  const resultData = resultSheet.getDataRange().getValues();
  const winnerMap = {};
  const matchTeams = {}; // 試合ID → { teamA, teamB }
  for (let i = 2; i < resultData.length; i++) {
    const id = resultData[i][0];
    const winner = resultData[i][6];
    const tA = resultData[i][2];
    const tB = resultData[i][3];
    if (id) matchTeams[id] = { teamA: tA, teamB: tB };
    if (id && winner && winner !== "") winnerMap[id] = winner;
  }

  // 試合ごとに「強い方」を返すヘルパー（オッズが低い = 強い）
  function getFavorite(matchId) {
    const teams = matchTeams[matchId];
    if (!teams || teams.teamA === "TBD") return null;
    const oddsA = oddsMap[teams.teamA] || 999;
    const oddsB = oddsMap[teams.teamB] || 999;
    return oddsA <= oddsB ? teams.teamA : teams.teamB;
  }

  // 参加者ごとに集計
  const stats = participants.map(name => {
    const colIdx = betHeaderRow.findIndex(c => c === name);
    let totalBet = 0;
    let totalPayout = 0; // 獲得金額
    let hitCount = 0;
    const betsByRound = { R32: 0, R16: 0, QF: 0, SF: 0, Final: 0 };

    ROUNDS.forEach(round => {
      round.matches.forEach((match) => {
        const betRow = findBetRow(betData, match.id);
        if (!betRow || colIdx < 0) return;
        const bet = String(betRow[colIdx] || "").trim();
        if (!bet) return;

        totalBet += CFG.betUnit;
        betsByRound[round.id] = (betsByRound[round.id] || 0) + 1;

        const winner = winnerMap[match.id];
        if (winner && bet === winner) {
          const favorite = getFavorite(match.id);
          const multiplier = (winner === favorite) ? CFG.favoriteMultiplier : CFG.underdogMultiplier;
          totalPayout += Math.round(CFG.betUnit * multiplier);
          hitCount++;
        }
      });
    });

    return { name, totalBet, totalPayout, hitCount, betsByRound, over: totalBet > CFG.maxBudget };
  });

  let row = 1;
  const totalCols = participants.length + 4;

  // ===== セクション1: 参加者別集計 =====
  adminSheet.getRange(row, 1, 1, 8).merge()
    .setValue("【1】参加者別 賭け状況")
    .setBackground("#1a3a5c").setFontColor("#f0c040").setFontSize(13).setFontWeight("bold");
  row++;

  const sec1Header = ["名前", "合計使用額", "残り予算", "上限超過？", "獲得金額", "的中数", "R32", "R16", "QF", "SF/決勝"];
  adminSheet.getRange(row, 1, 1, sec1Header.length).setValues([sec1Header])
    .setBackground("#0d2137").setFontColor("#6a9bc0").setFontWeight("bold");
  row++;

  stats.forEach(s => {
    const remaining = CFG.maxBudget - s.totalBet;
    const overText = s.over ? "⚠️ 超過！" : "OK";
    const sfFinal = (s.betsByRound["SF"] || 0) + (s.betsByRound["Final"] || 0);
    adminSheet.getRange(row, 1, 1, 10).setValues([[
      s.name,
      `${s.totalBet}円`,
      `${remaining}円`,
      overText,
      `${s.totalPayout}円`,
      s.hitCount,
      s.betsByRound["R32"] || 0,
      s.betsByRound["R16"] || 0,
      s.betsByRound["QF"]  || 0,
      sfFinal,
    ]]);
    if (s.over) {
      adminSheet.getRange(row, 4).setFontColor("#ef5350").setFontWeight("bold");
    } else {
      adminSheet.getRange(row, 4).setFontColor("#00e676");
    }
    adminSheet.getRange(row, 1).setFontWeight("bold");
    row++;
  });

  row += 2;

  // ===== セクション2: SIM =====
  adminSheet.getRange(row, 1, 1, participants.length + 3).merge()
    .setValue("【2】SIM — このチームが勝ったら誰が何pt獲得？")
    .setBackground("#1a3a5c").setFontColor("#f0c040").setFontSize(13).setFontWeight("bold");
  row++;

  adminSheet.getRange(row, 1, 1, participants.length + 3).merge()
    .setValue("※ 強い方（オッズ低）が勝つ→1.5倍、弱い方（オッズ高）が勝つ→2倍。当たった場合の獲得金額を表示。")
    .setBackground("#0a1628").setFontColor("#8ab4d8").setFontStyle("italic");
  row++;

  const simHeader = ["ラウンド", "試合ID", "もし勝者が…", ...participants];
  adminSheet.getRange(row, 1, 1, simHeader.length).setValues([simHeader])
    .setBackground("#0d2137").setFontColor("#6a9bc0").setFontWeight("bold");
  row++;

  ROUNDS.forEach(round => {
    round.matches.forEach((match, mi) => {
      const betRow = findBetRow(betData, match.id);
      if (!betRow) return;

      const teams = match.teamA === "TBD" ? ["（未定）"] : [match.teamA, match.teamB];

      // 強い方を判定（オッズ低い = 強い）
      const oddsA = oddsMap[match.teamA] || 999;
      const oddsB = oddsMap[match.teamB] || 999;
      const favorite = match.teamA === "TBD" ? null : (oddsA <= oddsB ? match.teamA : match.teamB);

      teams.forEach((team, ti) => {
        const multiplier = (team === favorite) ? CFG.favoriteMultiplier : CFG.underdogMultiplier;
        const label = match.teamA === "TBD" ? "（未定）"
          : `${team} が勝つ（${team === favorite ? "強" : "弱"}・${multiplier}倍）`;
        const simRow = [round.name, match.id, label];

        participants.forEach(name => {
          const colIdx = betHeaderRow.findIndex(c => c === name);
          const bet = colIdx >= 0 ? String(betRow[colIdx] || "").trim() : "";
          if (bet === team) {
            simRow.push(`+${Math.round(CFG.betUnit * multiplier)}円`);
          } else if (bet !== "") {
            simRow.push("ハズレ");
          } else {
            simRow.push("-");
          }
        });

        adminSheet.getRange(row, 1, 1, simRow.length).setValues([simRow]);
        const bg = (mi * 2 + ti) % 2 === 0 ? "#0d2137" : "#0a1628";
        adminSheet.getRange(row, 1, 1, simRow.length).setBackground(bg);
        adminSheet.getRange(row, 3).setFontColor("#c0d8f0").setFontWeight("bold");
        for (let j = 0; j < participants.length; j++) {
          const cell = adminSheet.getRange(row, j + 4);
          const val = simRow[j + 3];
          if (String(val).startsWith("+")) {
            cell.setFontColor("#00e676").setFontWeight("bold");
          } else if (val === "ハズレ") {
            cell.setFontColor("#ef5350");
          } else {
            cell.setFontColor("#555555");
          }
          cell.setHorizontalAlignment("center");
        }
        row++;
      });
    });
  });

  row += 2;

  // ===== セクション3: ランキング =====
  adminSheet.getRange(row, 1, 1, 5).merge()
    .setValue("【3】ランキング（結果入力後に反映）")
    .setBackground("#1a3a5c").setFontColor("#f0c040").setFontSize(13).setFontWeight("bold");
  row++;

  const rankHeader = ["順位", "名前", "獲得金額", "的中数", "賞金予測"];
  adminSheet.getRange(row, 1, 1, rankHeader.length).setValues([rankHeader])
    .setBackground("#0d2137").setFontColor("#6a9bc0").setFontWeight("bold");
  row++;

  const totalPool = stats.reduce((sum, s) => sum + s.totalBet, 0);
  const prizePool = Math.floor(totalPool * 0.8);
  const prizes = CFG.prizeRatio.map(r => Math.floor(prizePool * r));

  const sorted = [...stats].sort((a, b) => b.totalPayout - a.totalPayout);
  sorted.forEach((s, i) => {
    const rank = i + 1;
    const medal = rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : String(rank);
    const prize = rank <= 3 ? `${prizes[rank - 1]}円` : "-";
    adminSheet.getRange(row, 1, 1, 5).setValues([[medal, s.name, `${s.totalPayout}円`, s.hitCount, prize]]);
    const bg = rank === 1 ? "#fff8dc" : rank === 2 ? "#f5f5f5" : rank === 3 ? "#fde8d0" : null;
    if (bg) adminSheet.getRange(row, 1, 1, 5).setBackground(bg);
    row++;
  });

  adminSheet.getRange(row + 1, 1).setValue(`賞金プール: ${prizePool.toLocaleString()}円（参加者合計の80%）　最終更新: ${new Date().toLocaleString("ja-JP")}`)
    .setFontColor("#8ab4d8").setFontStyle("italic");

  // 列幅
  adminSheet.setColumnWidth(1, 110);
  adminSheet.setColumnWidth(2, 90);
  adminSheet.setColumnWidth(3, 180);
  for (let j = 0; j < participants.length; j++) {
    adminSheet.setColumnWidth(j + 4, 110);
  }

  SpreadsheetApp.getUi().alert("✅ 胴元ビューを更新しました！");
}

// 賭け入力シートから試合IDの行データを返す
function findBetRow(betData, matchId) {
  for (let i = 3; i < betData.length; i++) {
    if (betData[i][1] === matchId) return betData[i];
  }
  return null;
}

// ============================
// リマインドメール送信
// ============================
function sendReminderNow() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const master = ss.getSheetByName("👥参加者マスタ");
  const data = master.getDataRange().getValues();

  const today = new Date();
  const nextRound = ROUNDS.find(r => new Date(r.deadline) >= today);
  if (!nextRound) {
    SpreadsheetApp.getUi().alert("リマインド対象のラウンドが見つかりません。");
    return;
  }

  const ssUrl = ss.getUrl();
  let sentCount = 0;

  for (let i = 2; i < data.length; i++) {
    const name = data[i][0];
    const email = data[i][1];
    if (!name || !email || !email.includes("@")) continue;

    const subject = `⚽【TOTO】${nextRound.name}の賭け締切が近づいています！`;
    const body = `${name} さん\n\n` +
      `${nextRound.name}の締切が近づいています！\n\n` +
      `📋 賭けシートはこちら:\n${ssUrl}\n\n` +
      `⏰ 締切: ${nextRound.deadline}\n` +
      `💰 「🎯賭け入力」タブを開いて、自分の列にチーム名を入力\n` +
      `📌 1試合${CFG.betUnit}円・合計上限${CFG.maxBudget}円\n\n` +
      `胴元: ${CFG.administrator}`;

    GmailApp.sendEmail(email, subject, body);
    sentCount++;
  }

  SpreadsheetApp.getUi().alert(`✅ ${sentCount}名にリマインドメールを送信しました`);
}
