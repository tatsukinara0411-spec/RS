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
  { name: "ブラジル",                 odds: 4.5   },
  { name: "フランス",                 odds: 5.0   },
  { name: "スペイン",                 odds: 5.5   },
  { name: "アルゼンチン",             odds: 6.0   },
  { name: "イングランド",             odds: 7.0   },
  { name: "ドイツ",                   odds: 8.0   },
  { name: "ポルトガル",               odds: 9.0   },
  { name: "オランダ",                 odds: 10.0  },
  { name: "ベルギー",                 odds: 12.0  },
  { name: "クロアチア",               odds: 15.0  },
  { name: "ウルグアイ",               odds: 18.0  },
  { name: "メキシコ",                 odds: 20.0  },
  { name: "アメリカ",                 odds: 22.0  },
  { name: "コロンビア",               odds: 25.0  },
  { name: "ノルウェー",               odds: 28.0  },
  { name: "オーストリア",             odds: 30.0  },
  { name: "スイス",                   odds: 30.0  },
  { name: "モロッコ",                 odds: 32.0  },
  { name: "コートジボワール",         odds: 35.0  },
  { name: "スウェーデン",             odds: 38.0  },
  { name: "日本",                     odds: 40.0  },
  { name: "カナダ",                   odds: 40.0  },
  { name: "セネガル",                 odds: 45.0  },
  { name: "エクアドル",               odds: 48.0  },
  { name: "アルジェリア",             odds: 50.0  },
  { name: "韓国",                     odds: 50.0  },
  { name: "パラグアイ",               odds: 60.0  },
  { name: "オーストラリア",           odds: 65.0  },
  { name: "ガーナ",                   odds: 70.0  },
  { name: "DRコンゴ",                 odds: 90.0  },
  { name: "エジプト",                 odds: 90.0  },
  { name: "南アフリカ",               odds: 150.0 },
  { name: "ボスニア・ヘルツェゴビナ", odds: 150.0 },
  { name: "カーボベルデ",             odds: 200.0 },
];

// ============================
// ラウンド別試合カード
// ============================
const ROUNDS = [
  {
    id: "R32", name: "ラウンド32",
    deadline: "2026-07-03 22:00",
    matches: [
      { id: "R32-01", teamA: "ブラジル",    teamB: "セネガル",        deadline: "2026-06-28 22:00" },
      { id: "R32-02", teamA: "フランス",    teamB: "モロッコ",        deadline: "2026-06-28 22:00" },
      { id: "R32-03", teamA: "スペイン",    teamB: "メキシコ",        deadline: "2026-06-29 22:00" },
      { id: "R32-04", teamA: "アルゼンチン",teamB: "オーストラリア",  deadline: "2026-06-29 22:00" },
      { id: "R32-05", teamA: "イングランド",teamB: "スイス",          deadline: "2026-06-29 22:00" },
      { id: "R32-06", teamA: "ドイツ",      teamB: "デンマーク",      deadline: "2026-06-30 22:00" },
      { id: "R32-07", teamA: "ポルトガル",  teamB: "チュニジア",      deadline: "2026-06-30 22:00" },
      { id: "R32-08", teamA: "オランダ",    teamB: "韓国",            deadline: "2026-06-30 22:00" },
      { id: "R32-09", teamA: "ベルギー",    teamB: "カナダ",          deadline: "2026-07-01 22:00" },
      { id: "R32-10", teamA: "クロアチア",  teamB: "チリ",            deadline: "2026-07-01 22:00" },
      { id: "R32-11", teamA: "ウルグアイ",  teamB: "ガーナ",          deadline: "2026-07-01 22:00" },
      { id: "R32-12", teamA: "アメリカ",    teamB: "ナイジェリア",    deadline: "2026-07-02 22:00" },
      { id: "R32-13", teamA: "日本",        teamB: "ポーランド",      deadline: "2026-07-02 22:00" },
      { id: "R32-14", teamA: "コロンビア",  teamB: "コートジボワール",deadline: "2026-07-02 22:00" },
      { id: "R32-15", teamA: "エクアドル",  teamB: "セルビア",        deadline: "2026-07-03 22:00" },
      { id: "R32-16", teamA: "スウェーデン",teamB: "カメルーン",      deadline: "2026-07-03 22:00" },
    ]
  },
  {
    id: "R16", name: "ラウンド16",
    deadline: "2026-07-04 19:00",
    matches: [
      { id: "R16-01", teamA: "TBD", teamB: "TBD", deadline: "2026-07-04 19:00" },
      { id: "R16-02", teamA: "TBD", teamB: "TBD", deadline: "2026-07-04 19:00" },
      { id: "R16-03", teamA: "TBD", teamB: "TBD", deadline: "2026-07-04 19:00" },
      { id: "R16-04", teamA: "TBD", teamB: "TBD", deadline: "2026-07-04 19:00" },
      { id: "R16-05", teamA: "TBD", teamB: "TBD", deadline: "2026-07-04 19:00" },
      { id: "R16-06", teamA: "TBD", teamB: "TBD", deadline: "2026-07-04 19:00" },
      { id: "R16-07", teamA: "TBD", teamB: "TBD", deadline: "2026-07-04 19:00" },
      { id: "R16-08", teamA: "TBD", teamB: "TBD", deadline: "2026-07-04 19:00" },
    ]
  },
  {
    id: "QF", name: "準々決勝",
    deadline: "2026-07-09 19:00",
    matches: [
      { id: "QF-01", teamA: "TBD", teamB: "TBD", deadline: "2026-07-09 19:00" },
      { id: "QF-02", teamA: "TBD", teamB: "TBD", deadline: "2026-07-09 19:00" },
      { id: "QF-03", teamA: "TBD", teamB: "TBD", deadline: "2026-07-09 19:00" },
      { id: "QF-04", teamA: "TBD", teamB: "TBD", deadline: "2026-07-09 19:00" },
    ]
  },
  {
    id: "SF", name: "準決勝",
    deadline: "2026-07-14 19:00",
    matches: [
      { id: "SF-01", teamA: "TBD", teamB: "TBD", deadline: "2026-07-14 19:00" },
      { id: "SF-02", teamA: "TBD", teamB: "TBD", deadline: "2026-07-14 19:00" },
    ]
  },
  {
    id: "Final", name: "決勝",
    deadline: "2026-07-19 19:00",
    matches: [
      { id: "Final-01", teamA: "TBD", teamB: "TBD", deadline: "2026-07-19 19:00" },
    ]
  },
];

// 管理シート内のセクション開始行
const ADMIN_MASTER_ROW = 1;
const ADMIN_RESULT_ROW = 36;
const ADMIN_VIEW_ROW   = 120;

// 賭け入力シートの行定数
const BET_PROGRESS_ROW = 3;   // 進捗サマリー開始行
const BET_HEADER_ROW   = 10;  // 列ヘッダー行
const BET_MATCH_ROW    = 11;  // 試合データ開始行

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
// 初回セットアップ
// ============================
function setupAll() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  setupAdminSheet(ss);
  setupBetSheet(ss);
  ["シート1", "Sheet1"].forEach(name => {
    const s = ss.getSheetByName(name);
    if (s && ss.getSheets().length > 1) ss.deleteSheet(s);
  });
  setupOnEditTrigger();
  SpreadsheetApp.getUi().alert(
    "✅ セットアップ完了！\n\n" +
    "【次のステップ】\n" +
    "1.「⚙️管理」シート上部に参加者名を入力\n" +
    "   → 入力するだけで賭け入力シートに自動反映されます\n" +
    "2.「🎯賭け入力」シートを参加者に共有\n" +
    "   （⚙️管理 は胴元のみ。共有しない）"
  );
}

// ============================
// 既存の賭けデータを保存
// ============================
function saveBetData(betSheet) {
  if (!betSheet) return {};
  const data = betSheet.getDataRange().getValues();
  if (data.length < BET_HEADER_ROW) return {};
  const headerRow = data[BET_HEADER_ROW - 1]; // 0-indexed
  const saved = {}; // { matchId: { participantName: teamName } }
  for (let i = BET_MATCH_ROW - 1; i < data.length; i++) {
    const matchId = data[i][1];
    if (!matchId || String(matchId).startsWith("──") || String(matchId).startsWith("—")) continue;
    saved[matchId] = {};
    for (let j = 4; j < headerRow.length; j++) {
      const name = String(headerRow[j] || "").trim();
      const bet  = String(data[i][j] || "").trim();
      if (name && bet) saved[matchId][name] = bet;
    }
  }
  return saved;
}

// ============================
// 賭け入力シート（進捗サマリー + ドロップダウン付き）
// ============================
function setupBetSheet(ss) {
  const oddsMap = {};
  TEAMS.forEach(t => { oddsMap[t.name] = t.odds; });

  const participants = getParticipantList(ss);

  // 既存の賭けデータを保存
  const existingSheet = ss.getSheetByName("🎯賭け入力");
  const savedBets = saveBetData(existingSheet);

  if (existingSheet) ss.deleteSheet(existingSheet);
  const sheet = ss.insertSheet("🎯賭け入力", 0);

  const totalCols = Math.max(participants.length + 4, 5);

  // ── 行1: タイトル ──
  sheet.getRange(1, 1, 1, totalCols).merge()
    .setValue("🎯 賭け入力シート — 自分の列のセルを選んでチームを選択してください")
    .setBackground("#1a3a5c").setFontColor("#f0c040").setFontSize(13).setFontWeight("bold");

  // ── 行2: ルール ──
  sheet.getRange(2, 1, 1, totalCols).merge()
    .setValue("📌 1試合100円固定・上限1,000円｜★強が勝つ→1.5倍、弱が勝つ→2倍｜締切を過ぎると入力不可")
    .setBackground("#0a1628").setFontColor("#8ab4d8").setFontStyle("italic").setFontSize(10);

  // ── 行3〜7: 進捗サマリー ──
  // 行3: ラベル行（参加者名）
  const summaryLabel = ["", "", "📊 進捗サマリー", "", ...participants];
  sheet.getRange(BET_PROGRESS_ROW, 1, 1, summaryLabel.length).setValues([summaryLabel])
    .setBackground("#0d2137").setFontColor("#6a9bc0").setFontWeight("bold");
  sheet.getRange(BET_PROGRESS_ROW, 3).setFontColor("#f0c040");
  for (let j = 0; j < participants.length; j++) {
    sheet.getRange(BET_PROGRESS_ROW, j + 5)
      .setFontColor("#f0c040").setFontWeight("bold").setHorizontalAlignment("center");
  }

  // 行4: 入力済み試合数（後でフォーミュラ挿入）
  sheet.getRange(4, 3).setValue("入力済み試合数").setFontColor("#6a9bc0").setHorizontalAlignment("right");
  sheet.getRange(4, 1, 1, totalCols).setBackground("#0a1628");

  // 行5: 的中数（updateAdminView実行時に更新）
  sheet.getRange(5, 3).setValue("的中数 🎯").setFontColor("#6a9bc0").setHorizontalAlignment("right");
  sheet.getRange(5, 1, 1, totalCols).setBackground("#0d2137");
  for (let j = 0; j < participants.length; j++) {
    sheet.getRange(5, j + 5).setValue("—").setFontColor("#4a6a8a").setHorizontalAlignment("center");
  }

  // 行6: 獲得金額（updateAdminView実行時に更新）
  sheet.getRange(6, 3).setValue("獲得金額（円）💰").setFontColor("#6a9bc0").setHorizontalAlignment("right");
  sheet.getRange(6, 1, 1, totalCols).setBackground("#0a1628");
  for (let j = 0; j < participants.length; j++) {
    sheet.getRange(6, j + 5).setValue("—").setFontColor("#4a6a8a").setHorizontalAlignment("center");
  }

  // 行7: 合計使用額
  sheet.getRange(7, 3).setValue("合計使用額（円）").setFontColor("#6a9bc0").setHorizontalAlignment("right");
  sheet.getRange(7, 1, 1, totalCols).setBackground("#0d2137");

  // 行8: 残り予算
  sheet.getRange(8, 3).setValue("残り予算（円）").setFontColor("#6a9bc0").setHorizontalAlignment("right");
  sheet.getRange(8, 1, 1, totalCols).setBackground("#0a1628");

  // 行9: 状況
  sheet.getRange(9, 3).setValue("状況").setFontColor("#6a9bc0").setHorizontalAlignment("right");
  sheet.getRange(9, 1, 1, totalCols).setBackground("#0d2137");

  // ── 行8: 列ヘッダー ──
  const headerRow = ["ラウンド", "試合ID", "対戦カード（★強=1.5倍/弱=2倍）", "締切", ...participants];
  sheet.getRange(BET_HEADER_ROW, 1, 1, headerRow.length).setValues([headerRow])
    .setBackground("#1a3a5c").setFontColor("#6a9bc0").setFontWeight("bold");
  sheet.getRange(BET_HEADER_ROW, 3).setFontColor("#aaaaaa");
  for (let j = 0; j < participants.length; j++) {
    sheet.getRange(BET_HEADER_ROW, j + 5)
      .setFontColor("#f0c040").setFontWeight("bold").setHorizontalAlignment("center");
  }

  // ── 行9〜: 試合行 ──
  let row = BET_MATCH_ROW;
  ROUNDS.forEach(round => {
    // ラウンドセパレーター
    sheet.getRange(row, 1, 1, totalCols).merge()
      .setValue(`── ${round.name}　締切: ${round.deadline} ──`)
      .setBackground("#0a1628").setFontColor("#f0c040")
      .setFontStyle("italic").setHorizontalAlignment("center");
    row++;

    round.matches.forEach((match, mi) => {
      const matchDeadline = match.deadline || round.deadline;
      let card;
      const validTeams = [];

      if (match.teamA === "TBD") {
        card = "（対戦カード未定）";
      } else {
        const oddsA = oddsMap[match.teamA] || 999;
        const oddsB = oddsMap[match.teamB] || 999;
        const favA  = oddsA <= oddsB;
        card = `${favA ? "★" : ""}${match.teamA}(${favA ? "強" : "弱"}) vs ${!favA ? "★" : ""}${match.teamB}(${!favA ? "強" : "弱"})`;
        validTeams.push(match.teamA, match.teamB);
      }

      sheet.getRange(row, 1, 1, 4).setValues([[round.name, match.id, card, matchDeadline]]);
      const bg = mi % 2 === 0 ? "#0d2137" : "#0a1628";
      sheet.getRange(row, 1, 1, totalCols).setBackground(bg);
      sheet.getRange(row, 1).setFontColor("#8ab4d8");
      sheet.getRange(row, 2).setFontColor("#6a9bc0");
      sheet.getRange(row, 3).setFontColor(match.teamA === "TBD" ? "#4a6a8a" : "#c0d8f0");
      sheet.getRange(row, 4).setFontColor("#aaaaaa").setFontSize(9);

      // 参加者列にドロップダウンを設定
      for (let j = 0; j < participants.length; j++) {
        const cell = sheet.getRange(row, j + 5);
        cell.setFontColor("#f0c040").setFontWeight("bold").setHorizontalAlignment("center");
        if (validTeams.length === 2) {
          const rule = SpreadsheetApp.newDataValidation()
            .requireValueInList(validTeams, true)
            .setAllowInvalid(false)
            .build();
          cell.setDataValidation(rule);
        }
      }
      row++;
    });
  });

  const lastMatchRow = row - 1;

  // ── 進捗サマリーのフォーミュラを挿入 ──
  for (let j = 0; j < participants.length; j++) {
    const col = j + 5;
    const colL = columnToLetter(col);
    // 入力済み試合数
    sheet.getRange(4, col)
      .setFormula(`=COUNTA(${colL}${BET_MATCH_ROW}:${colL}${lastMatchRow})`)
      .setFontColor("#f0c040").setFontWeight("bold").setHorizontalAlignment("center");
    // 合計使用額（行7）
    sheet.getRange(7, col)
      .setFormula(`=${colL}4*${CFG.betUnit}`)
      .setFontColor("#f0c040").setFontWeight("bold").setHorizontalAlignment("center");
    // 残り予算（行8）
    sheet.getRange(8, col)
      .setFormula(`=${CFG.maxBudget}-${colL}7`)
      .setFontWeight("bold").setHorizontalAlignment("center");
    // 状況（行9）
    sheet.getRange(9, col)
      .setFormula(`=IF(${colL}8<0,"⚠️超過",IF(${colL}4=0,"未入力",IF(${colL}8=0,"✅満額","入力中")))`)
      .setHorizontalAlignment("center").setFontWeight("bold");
  }

  // 条件付き書式：残り予算がマイナスなら赤
  if (participants.length > 0) {
    const startCol = columnToLetter(5);
    const endCol   = columnToLetter(4 + participants.length);
    const rules = sheet.getConditionalFormatRules();
    rules.push(
      SpreadsheetApp.newConditionalFormatRule()
        .whenNumberLessThan(0)
        .setBackground("#3c1010").setFontColor("#ef5350")
        .setRanges([sheet.getRange(`${startCol}8:${endCol}8`)])
        .build()
    );
    sheet.setConditionalFormatRules(rules);
  }

  // ── 既存の賭けデータを復元 ──
  if (Object.keys(savedBets).length > 0) {
    const sheetData = sheet.getDataRange().getValues();
    const hRow = sheetData[BET_HEADER_ROW - 1];
    for (let i = BET_MATCH_ROW - 1; i < sheetData.length; i++) {
      const matchId = String(sheetData[i][1] || "").trim();
      if (!matchId || !savedBets[matchId]) continue;
      for (let j = 4; j < hRow.length; j++) {
        const name = String(hRow[j] || "").trim();
        if (name && savedBets[matchId][name]) {
          sheet.getRange(i + 1, j + 1).setValue(savedBets[matchId][name]);
        }
      }
    }
  }

  // 列幅
  sheet.setColumnWidth(1, 100);
  sheet.setColumnWidth(2, 85);
  sheet.setColumnWidth(3, 230);
  sheet.setColumnWidth(4, 135);
  for (let j = 0; j < participants.length; j++) sheet.setColumnWidth(j + 5, 120);

  sheet.setFrozenRows(BET_HEADER_ROW); // 行8まで固定
  return sheet;
}

function rebuildBetSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  setupBetSheet(ss);
  SpreadsheetApp.getUi().alert("✅ 賭け入力シートを再生成しました！（既存の賭けデータは引き継がれています）");
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
    .setValue("【1】👥 参加者マスタ — 名前を入力すると賭け入力シートに自動反映されます")
    .setBackground("#1a3a5c").setFontColor("#f0c040").setFontSize(13).setFontWeight("bold");
  r++;
  sheet.getRange(r, 1, 1, 3).setValues([["名前", "メールアドレス（任意）", "備考"]])
    .setBackground("#0d2137").setFontColor("#6a9bc0").setFontWeight("bold");
  r++;
  // サンプルデータ（削除してOK）
  const samples = [
    ["田中太郎", "tanaka@example.com", "（サンプル）"],
    ["鈴木花子", "suzuki@example.com", "（サンプル）"],
    ["佐藤次郎", "sato@example.com",   "（サンプル）"],
  ];
  sheet.getRange(r, 1, samples.length, 3).setValues(samples).setFontColor("#888888");
  r += samples.length;
  sheet.getRange(r + 1, 1)
    .setValue("↑ A列に名前を入力するだけで賭け入力シートに自動で列が追加されます")
    .setFontColor("#f0c040").setFontStyle("italic");

  sheet.setColumnWidth(1, 130);
  sheet.setColumnWidth(2, 220);
  sheet.setColumnWidth(3, 200);

  // ── セクション2: 結果入力 ──
  r = ADMIN_RESULT_ROW;
  sheet.getRange(r, 1, 1, 7).merge()
    .setValue("【2】📋 結果入力 — 試合終了後にスコアを入力（G列の勝者は自動計算）")
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
      sheet.getRange(r, 1).setFontColor("#6a9bc0");
      sheet.getRange(r, 3, 1, 2).setFontColor("#c0d8f0");
      sheet.getRange(r, 7)
        .setFormula(`=IF(AND(E${r}<>"",F${r}<>""),IF(E${r}>F${r},C${r},IF(E${r}<F${r},D${r},"PK")),"")`)
        .setBackground("#e8f5e9");
      r++;
    });
  });
  sheet.getRange(r + 1, 1)
    .setValue("※ PKの場合は勝者列（G列）に直接チーム名を手入力してください")
    .setFontColor("#888888").setFontStyle("italic");

  sheet.setColumnWidth(3, 160);
  sheet.setColumnWidth(4, 180);
  sheet.setColumnWidth(7, 160);

  // ── セクション3: 胴元ビュー（プレースホルダー） ──
  sheet.getRange(ADMIN_VIEW_ROW, 1)
    .setValue("← 「⚽TOTO管理」→「胴元ビューを更新」を実行するとここに集計が表示されます")
    .setFontColor("#888888").setFontStyle("italic");

  return sheet;
}

// ============================
// onEditトリガー設定
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

  // 管理シートの参加者マスタ（A列）が編集されたら賭け入力を自動再生成
  if (sheet.getName() === "⚙️管理") {
    const row = e.range.getRow();
    const col = e.range.getColumn();
    if (row >= ADMIN_MASTER_ROW + 2 && row < ADMIN_RESULT_ROW && col === 1) {
      setupBetSheet(SpreadsheetApp.getActiveSpreadsheet());
    }
    return;
  }

  // 賭け入力シートの締切チェック
  if (sheet.getName() !== "🎯賭け入力") return;
  const row = e.range.getRow();
  const col = e.range.getColumn();
  if (row < BET_MATCH_ROW || col < 5) return;

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
function updateAdminView(silent) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const adminSheet = ss.getSheetByName("⚙️管理") || ss.getSheetByName("管理");
  // 胴元ビューシートが別にある場合はそちらに書き込む
  const viewSheet  = ss.getSheets().find(s => s.getName().includes("胴元ビュー")) || adminSheet;
  const betSheet   = ss.getSheetByName("🎯賭け入力") || ss.getSheetByName("賭け入力");

  if (!betSheet) {
    if (!silent) SpreadsheetApp.getUi().alert("❌ 賭け入力シートが見つかりません。");
    return;
  }

  // 胴元ビューシートをクリア
  viewSheet.clearContents();
  viewSheet.clearFormats();

  const participants = getParticipantList(ss);
  const betData = betSheet.getDataRange().getValues();
  const betHeaderRow = betData[BET_HEADER_ROW - 1];
  const oddsMap = {};
  TEAMS.forEach(t => { oddsMap[t.name] = t.odds; });

  // 結果入力シートから勝者を取得
  const resultSheet2 = ss.getSheetByName("結果入力") || adminSheet;
  const resultData2  = resultSheet2.getDataRange().getValues();
  const winnerMap = {};
  const matchTeamsMap = {};
  ROUNDS.forEach(round => {
    round.matches.forEach(match => {
      matchTeamsMap[match.id] = { teamA: match.teamA, teamB: match.teamB };
    });
  });
  for (let i = 0; i < resultData2.length; i++) {
    const id     = String(resultData2[i][0] || "").trim();
    const winner = String(resultData2[i][6] || "").trim();
    if (id && winner) winnerMap[id] = winner;
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

  let row = 1;

  viewSheet.getRange(row, 1, 1, 11).merge()
    .setValue("📊 胴元ビュー　最終更新: " + new Date().toLocaleString("ja-JP"))
    .setBackground("#1a3a5c").setFontColor("#f0c040").setFontSize(13).setFontWeight("bold");
  row++;

  // 参加者別集計
  viewSheet.getRange(row, 1, 1, 11).merge()
    .setValue("▶ 参加者別 賭け状況")
    .setBackground("#0d2137").setFontColor("#8ab4d8").setFontWeight("bold");
  row++;
  viewSheet.getRange(row, 1, 1, 11)
    .setValues([["名前","合計使用額","獲得金額","損益","上限超過？","的中数","R32","R16","QF","SF/決勝","状況"]])
    .setBackground("#0a1628").setFontColor("#6a9bc0").setFontWeight("bold");
  row++;
  stats.forEach(s => {
    const sfFinal = (s.betsByRound["SF"] || 0) + (s.betsByRound["Final"] || 0);
    const net = s.totalPayout - s.totalBet;
    const netStr = net > 0 ? `+${net}円` : `${net}円`;
    const status = s.hitCount === 0 ? "未的中" : net > 0 ? "✅ 黒字" : "🔴 赤字";
    viewSheet.getRange(row, 1, 1, 11).setValues([[
      s.name, `${s.totalBet}円`, `${s.totalPayout}円`, netStr,
      s.over ? "⚠️ 超過！" : "OK", s.hitCount,
      s.betsByRound["R32"] || 0, s.betsByRound["R16"] || 0,
      s.betsByRound["QF"]  || 0, sfFinal, status
    ]]);
    viewSheet.getRange(row, 4).setFontColor(net > 0 ? "#00e676" : net < 0 ? "#ef5350" : "#888888").setFontWeight("bold");
    viewSheet.getRange(row, 5).setFontColor(s.over ? "#ef5350" : "#00e676").setFontWeight("bold");
    viewSheet.getRange(row, 11).setFontColor(net > 0 ? "#00e676" : net < 0 ? "#ef5350" : "#888888").setFontWeight("bold");
    row++;
  });

  row += 2;

  // SIM
  viewSheet.getRange(row, 1, 1, participants.length + 3).merge()
    .setValue("▶ SIM — このチームが勝ったら誰が何円獲得？")
    .setBackground("#0d2137").setFontColor("#8ab4d8").setFontWeight("bold");
  row++;
  viewSheet.getRange(row, 1, 1, participants.length + 3)
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
        const label = match.teamA === "TBD" ? "（未定）" : `${team}（${team === favorite ? "★強" : "弱"}・${mult}倍）`;
        const simRow = [round.name, match.id, label];
        participants.forEach(name => {
          const colIdx = betHeaderRow.findIndex(c => c === name);
          const bet = colIdx >= 0 ? String(betRow[colIdx] || "").trim() : "";
          simRow.push(bet === team ? `+${Math.round(CFG.betUnit * mult)}円` : bet !== "" ? "ハズレ" : "-");
        });
        viewSheet.getRange(row, 1, 1, simRow.length).setValues([simRow]);
        const bg = (mi * 2 + ti) % 2 === 0 ? "#0d2137" : "#0a1628";
        viewSheet.getRange(row, 1, 1, simRow.length).setBackground(bg);
        for (let j = 0; j < participants.length; j++) {
          const v = simRow[j + 3];
          viewSheet.getRange(row, j + 4)
            .setFontColor(String(v).startsWith("+") ? "#00e676" : v === "ハズレ" ? "#ef5350" : "#555555")
            .setFontWeight(String(v).startsWith("+") ? "bold" : "normal")
            .setHorizontalAlignment("center");
        }
        row++;
      });
    });
  });

  row += 2;

  // ランキング
  viewSheet.getRange(row, 1, 1, 5).merge()
    .setValue("▶ ランキング（結果入力後に反映）")
    .setBackground("#0d2137").setFontColor("#8ab4d8").setFontWeight("bold");
  row++;
  viewSheet.getRange(row, 1, 1, 5)
    .setValues([["順位","名前","獲得金額","的中数","賞金予測"]])
    .setBackground("#0a1628").setFontColor("#6a9bc0").setFontWeight("bold");
  row++;
  const totalPool = stats.reduce((sum, s) => sum + s.totalBet, 0);
  const prizePool  = Math.floor(totalPool * 0.8);
  const prizes     = CFG.prizeRatio.map(r => Math.floor(prizePool * r));
  [...stats].sort((a, b) => b.totalPayout - a.totalPayout).forEach((s, i) => {
    const rank  = i + 1;
    const medal = rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : String(rank);
    viewSheet.getRange(row, 1, 1, 5).setValues([
      [medal, s.name, `${s.totalPayout}円`, s.hitCount, rank <= 3 ? `${prizes[rank-1]}円` : "-"]
    ]);
    const bg = rank === 1 ? "#fff8dc" : rank === 2 ? "#f5f5f5" : rank === 3 ? "#fde8d0" : null;
    if (bg) viewSheet.getRange(row, 1, 1, 5).setBackground(bg);
    row++;
  });
  viewSheet.getRange(row + 1, 1)
    .setValue(`賞金プール: ${prizePool.toLocaleString()}円（全賭け金の80%）`)
    .setFontColor("#8ab4d8").setFontStyle("italic");

  // 賭け入力シートの的中数・獲得金額も更新
  updateBetSheetResults(ss, betSheet, stats);

  if (!silent) SpreadsheetApp.getUi().alert("✅ 胴元ビューを更新しました！\n賭け入力シートの的中数・獲得金額も更新しました。");
}

// ============================
// 賭け入力シートの的中数・獲得金額を更新
// ============================
function updateBetSheetResults(ss, betSheet, stats) {
  if (!betSheet) return;
  const headerRow = betSheet.getRange(BET_HEADER_ROW, 1, 1, betSheet.getLastColumn()).getValues()[0];

  stats.forEach(s => {
    const col = headerRow.findIndex(c => c === s.name);
    if (col < 0) return;
    const colIdx = col + 1; // 1-indexed
    betSheet.getRange(5, colIdx).setValue(s.hitCount)
      .setFontColor(s.hitCount > 0 ? "#00c853" : "#4a6a8a")
      .setFontWeight("bold").setHorizontalAlignment("center");
    betSheet.getRange(6, colIdx).setValue(s.totalPayout)
      .setFontColor(s.totalPayout > 0 ? "#f0c040" : "#4a6a8a")
      .setFontWeight("bold").setHorizontalAlignment("center");
  });
}

// ============================
// ユーティリティ
// ============================
function getParticipantList(ss) {
  const betSheet = ss.getSheetByName("🎯賭け入力") || ss.getSheetByName("賭け入力");
  if (!betSheet) return [];
  const lastCol = betSheet.getLastColumn();
  if (lastCol < 2) return [];
  const headerRow = betSheet.getRange(BET_HEADER_ROW, 1, 1, lastCol).getValues()[0];
  const participants = [];
  // Col A = ラウンド, Col B = 試合ID, Col C = 対戦カード, Col D = 締切, Col E+ = 参加者名
  const SKIP_COLS = 4; // skip first 4 columns
  for (let i = SKIP_COLS; i < headerRow.length; i++) {
    const name = String(headerRow[i] || "").trim();
    if (name && !name.includes("/") && !name.startsWith("（")) participants.push(name);
  }
  return participants;
}

function findBetRow(betData, matchId) {
  for (let i = BET_MATCH_ROW - 1; i < betData.length; i++) {
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

// リマインドメール送信
// ブラウザ側から試合結果を受け取ってスプシに保存
// ============================
function saveMatchResults(results) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  // 「結果入力」または「⚙️管理」シートを探す
  const resultSheet = ss.getSheetByName("結果入力") || ss.getSheetByName("⚙️管理");
  if (!resultSheet) return { ok: false, error: "結果入力シートが見つかりません" };

  const data = resultSheet.getDataRange().getValues();
  let updatedCount = 0;

  results.forEach(r => {
    for (let i = 0; i < data.length; i++) {
      const teamA = String(data[i][2] || "").trim();
      const teamB = String(data[i][3] || "").trim();
      if (!teamA || teamA === "TBD" || teamA === "チームA") continue;
      if (teamA !== r.teamA || teamB !== r.teamB) continue;
      const row = i + 1;
      if (r.scoreA !== null) resultSheet.getRange(row, 5).setValue(r.scoreA);
      if (r.scoreB !== null) resultSheet.getRange(row, 6).setValue(r.scoreB);
      updatedCount++;
      break;
    }
  });

  try { updateAdminView(true); } catch(e) {}
  return { ok: true, updated: updatedCount };
}

// ============================
function sendReminderNow() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const adminSheet = ss.getSheetByName("⚙️管理");
  const data = adminSheet.getDataRange().getValues();
  const today = new Date();
  const nextRound = ROUNDS.find(r => new Date(r.deadline) >= today);
  if (!nextRound) {
    SpreadsheetApp.getUi().alert("リマインド対象のラウンドが見つかりません。");
    return;
  }
  const ssUrl      = ss.getUrl();
  const dashboardUrl = "https://script.google.com/macros/s/AKfycbzdlrcAClF8-fvxlzG3S_6f_5qZspqE8bY9Hi42kqEmHoFVv2Cmg3McIOU3lT63NT-6ug/exec";
  let sentCount = 0;
  const start = ADMIN_MASTER_ROW + 2 - 1;
  const end   = ADMIN_RESULT_ROW - 1;
  for (let i = start; i < Math.min(end, data.length); i++) {
    const name  = String(data[i][0] || "").trim();
    const email = String(data[i][1] || "").trim();
    if (!name || !email || !email.includes("@")) continue;
    GmailApp.sendEmail(email,
      `⚽【TOTO】${nextRound.name}の賭け締切が近づいています！`,
      `${name} さん\n\n${nextRound.name}の締切が近づいています！\n\n📋 賭けシートはこちら:\n${ssUrl}\n\n🏆 順位・結果ダッシュボード:\n${dashboardUrl}\n\n⏰ 締切: ${nextRound.deadline}\n💰「🎯賭け入力」タブを開いて、自分の列でチームを選択\n\n胴元: ${CFG.administrator}`
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
  const adminSheet  = ss.getSheetByName("⚙️管理");
  const betSheet    = ss.getSheetByName("🎯賭け入力");
  // 結果入力シートが別にある場合はそちらを優先
  const resultSheet = ss.getSheetByName("結果入力") || adminSheet;

  const participants = getParticipantList(ss);
  const resultData   = resultSheet.getDataRange().getValues();

  // 結果入力シートからmatchId→{scoreA,scoreB,winner}マップを作成
  const resultMap = {};
  for (let i = 0; i < resultData.length; i++) {
    const id     = String(resultData[i][0] || "").trim();
    const teamA  = String(resultData[i][2] || "").trim();
    const winner = String(resultData[i][6] || "").trim();
    if (!id || !teamA || teamA === "チームA" || teamA === "TBD") continue;
    resultMap[id] = {
      scoreA: resultData[i][4] || null,
      scoreB: resultData[i][5] || null,
      winner: winner || null,
    };
  }

  // ROUNDSを正とした試合リストを生成
  const matches   = [];
  const winnerMap = {};
  ROUNDS.forEach(round => {
    round.matches.forEach(match => {
      const res = resultMap[match.id] || {};
      const winner = res.winner || null;
      matches.push({
        id: match.id, round: round.id,
        teamA: match.teamA, teamB: match.teamB,
        scoreA: res.scoreA || null, scoreB: res.scoreB || null, winner,
      });
      if (winner) winnerMap[match.id] = winner;
    });
  });

  const betData      = betSheet.getDataRange().getValues();
  const betHeaderRow = betData[BET_HEADER_ROW - 1];
  const oddsMap      = {};
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
    updatedAt:     new Date().toLocaleString("ja-JP"),
    administrator: CFG.administrator,
    prizePool,
    participants:  stats,
    matches,
    rounds: ROUNDS.map(r => ({ id: r.id, name: r.name, deadline: r.deadline })),
  };
}
