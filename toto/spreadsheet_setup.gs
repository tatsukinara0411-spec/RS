/**
 * 社内ワールドカップTOTO 2026 - Google Apps Script
 *
 * 【使い方】
 * 1. スプレッドシートの「拡張機能」→「Apps Script」にこのコードを貼り付けて保存
 * 2. onOpen() を実行して権限を許可
 * 3. スプレッドシートの「⚽ TOTO管理」メニューから「初回セットアップ」を実行
 */

// ============================
// 胴元設定（ここを変更してOK）
// ============================
const CFG = {
  administrator: "タロウ",       // 胴元の名前
  maxBudget: 1000,               // 参加者1人あたりの上限（円）
  maxPerMatch: 100,              // 1試合あたりの上限（円）
  betUnit: 100,                  // 賭け単位（円）
  prizeRatio: [0.50, 0.30, 0.20], // 1位・2位・3位の賞金配分
  reminderHour: 9,               // リマインドメール送信時刻（9時）
};

// ============================
// チームとオッズ
// ============================
const TEAMS = [
  { name: "ブラジル",       flag: "🇧🇷", odds: 4.5  },
  { name: "フランス",       flag: "🇫🇷", odds: 5.0  },
  { name: "スペイン",       flag: "🇪🇸", odds: 5.5  },
  { name: "アルゼンチン",   flag: "🇦🇷", odds: 6.0  },
  { name: "イングランド",   flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", odds: 7.0  },
  { name: "ドイツ",         flag: "🇩🇪", odds: 8.0  },
  { name: "ポルトガル",     flag: "🇵🇹", odds: 9.0  },
  { name: "オランダ",       flag: "🇳🇱", odds: 10.0 },
  { name: "ベルギー",       flag: "🇧🇪", odds: 12.0 },
  { name: "クロアチア",     flag: "🇭🇷", odds: 15.0 },
  { name: "ウルグアイ",     flag: "🇺🇾", odds: 18.0 },
  { name: "メキシコ",       flag: "🇲🇽", odds: 20.0 },
  { name: "アメリカ",       flag: "🇺🇸", odds: 25.0 },
  { name: "モロッコ",       flag: "🇲🇦", odds: 35.0 },
  { name: "日本",           flag: "🇯🇵", odds: 40.0 },
  { name: "韓国",           flag: "🇰🇷", odds: 50.0 },
  { name: "セネガル",       flag: "🇸🇳", odds: 45.0 },
  { name: "オーストラリア", flag: "🇦🇺", odds: 60.0 },
  { name: "スイス",         flag: "🇨🇭", odds: 30.0 },
  { name: "デンマーク",     flag: "🇩🇰", odds: 35.0 },
  { name: "チュニジア",     flag: "🇹🇳", odds: 80.0 },
  { name: "カナダ",         flag: "🇨🇦", odds: 40.0 },
  { name: "チリ",           flag: "🇨🇱", odds: 50.0 },
  { name: "ガーナ",         flag: "🇬🇭", odds: 70.0 },
  { name: "ナイジェリア",   flag: "🇳🇬", odds: 55.0 },
  { name: "ポーランド",     flag: "🇵🇱", odds: 65.0 },
  { name: "コロンビア",     flag: "🇨🇴", odds: 30.0 },
  { name: "コートジボワール",flag: "🇨🇮", odds: 60.0 },
  { name: "エクアドル",     flag: "🇪🇨", odds: 55.0 },
  { name: "セルビア",       flag: "🇷🇸", odds: 45.0 },
  { name: "スウェーデン",   flag: "🇸🇪", odds: 40.0 },
  { name: "カメルーン",     flag: "🇨🇲", odds: 70.0 },
];

// ============================
// ラウンド別試合カード
// ============================
const ROUNDS = [
  {
    id: "R32", name: "ラウンド32", tab: "🏟️R32",
    matchDate: "2026-06-29",  // 試合開始日（リマインド用）
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
    id: "R16", name: "ラウンド16", tab: "🏟️R16",
    matchDate: "2026-07-04",
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
    id: "QF", name: "準々決勝", tab: "⚡QF",
    matchDate: "2026-07-09",
    matches: [
      { id: "QF-01", teamA: "TBD", teamB: "TBD" },
      { id: "QF-02", teamA: "TBD", teamB: "TBD" },
      { id: "QF-03", teamA: "TBD", teamB: "TBD" },
      { id: "QF-04", teamA: "TBD", teamB: "TBD" },
    ]
  },
  {
    id: "SF", name: "準決勝", tab: "🔥SF",
    matchDate: "2026-07-14",
    matches: [
      { id: "SF-01", teamA: "TBD", teamB: "TBD" },
      { id: "SF-02", teamA: "TBD", teamB: "TBD" },
    ]
  },
  {
    id: "Final", name: "決勝", tab: "🏆決勝",
    matchDate: "2026-07-19",
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
    .addItem("🔧 初回セットアップ（全シート作成）", "setupAll")
    .addSeparator()
    .addItem("🏆 ランキング更新", "updateRanking")
    .addItem("📊 賭け一覧＆SIM更新", "updateBetSummarySheet")
    .addSeparator()
    .addItem("📢 今すぐリマインドメール送信", "sendReminderNow")
    .addItem("⏰ リマインド自動送信を設定", "setupReminderTrigger")
    .addSeparator()
    .addItem("➕ 次のラウンドの賭けシートを追加", "addNextRoundSheet")
    .addToUi();
}

// ============================
// 初回セットアップ
// ============================
function setupAll() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  setupMasterSheet(ss);
  setupOddsSheet(ss);
  setupResultSheet(ss);
  setupRankingSheet(ss);
  setupR32BetSheet(ss);   // まずR32だけ作る

  // 不要なデフォルトシートを削除
  const defaultSheet = ss.getSheetByName("シート1");
  if (defaultSheet && ss.getSheets().length > 1) ss.deleteSheet(defaultSheet);

  SpreadsheetApp.getUi().alert(
    "✅ セットアップ完了！\n\n" +
    "【次のステップ】\n" +
    "1.「👥参加者マスタ」に参加者の名前とメールを入力\n" +
    "2.「🏟️R32」シートを参加者に共有して賭けを入力してもらう\n" +
    "3. 試合が終わったら「📋結果入力」にスコアを入力\n" +
    "4.「⚽TOTO管理」→「ランキング更新」でポイント集計\n" +
    "5. 次のラウンドになったら「次のラウンドの賭けシートを追加」"
  );
}

// ============================
// 参加者マスタシート
// ============================
function setupMasterSheet(ss) {
  let sheet = ss.getSheetByName("👥参加者マスタ");
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet("👥参加者マスタ", 0);

  // タイトル
  sheet.getRange("A1:F1").merge()
    .setValue("⚽ 社内ワールドカップTOTO 2026 — 参加者マスタ")
    .setBackground("#1a3a5c").setFontColor("#f0c040")
    .setFontSize(14).setFontWeight("bold")
    .setHorizontalAlignment("center");

  // 設定情報
  sheet.getRange("A2").setValue(`胴元: ${CFG.administrator}　|　上限: ${CFG.maxBudget}円　|　1試合最大: ${CFG.maxPerMatch}円　|　賭け単位: ${CFG.betUnit}円`);
  sheet.getRange("A2:F2").merge().setFontColor("#8ab4d8").setBackground("#0d2137");

  // ヘッダー
  const headers = ["名前", "メールアドレス", "使用済み(円)", "残り予算(円)", "獲得ポイント", "備考"];
  sheet.getRange("A3:F3").setValues([headers])
    .setBackground("#1a3a5c").setFontColor("white").setFontWeight("bold");

  // サンプルデータ（削除してOK）
  const samples = [
    ["田中太郎", "tanaka@example.com", 0, CFG.maxBudget, 0, ""],
    ["鈴木花子", "suzuki@example.com", 0, CFG.maxBudget, 0, ""],
    ["佐藤次郎", "sato@example.com",   0, CFG.maxBudget, 0, "（サンプル：削除してOK）"],
  ];
  sheet.getRange(4, 1, samples.length, 6).setValues(samples);

  // D列（残り予算）は自動計算
  for (let i = 4; i <= 20; i++) {
    sheet.getRange(i, 4).setFormula(`=IF(A${i}="","",${CFG.maxBudget}-C${i})`);
  }

  sheet.getRange("C4:E20").setNumberFormat("0");
  sheet.setColumnWidth(1, 120);
  sheet.setColumnWidth(2, 200);
  sheet.setColumnWidth(3, 120);
  sheet.setColumnWidth(4, 120);
  sheet.setColumnWidth(5, 130);
  sheet.setColumnWidth(6, 180);

  // 注記
  sheet.getRange("A22").setValue("※ 名前とメールアドレスを入力してください。使用済み・ポイントは「ランキング更新」で自動計算されます。");
  sheet.getRange("A22").setFontColor("#888888").setFontStyle("italic");
}

// ============================
// オッズシート
// ============================
function setupOddsSheet(ss) {
  let sheet = ss.getSheetByName("📊オッズ");
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet("📊オッズ", 1);

  sheet.getRange("A1:D1").setValues([["チーム名", "国旗", "オッズ(倍)", "※低いほど強い"]])
    .setBackground("#1a3a5c").setFontColor("white").setFontWeight("bold");

  const sorted = [...TEAMS].sort((a, b) => a.odds - b.odds);
  sorted.forEach((t, i) => {
    sheet.getRange(i + 2, 1, 1, 3).setValues([[t.name, t.flag, t.odds]]);
  });

  sheet.getRange(2, 3, sorted.length, 1).setNumberFormat("0.0");
  sheet.setColumnWidth(1, 160);
  sheet.setColumnWidth(2, 50);
  sheet.setColumnWidth(3, 120);
  sheet.setColumnWidth(4, 180);

  sheet.getRange("A22").setValue("※ オッズは胴元が自由に変更できます。低いほど強いチーム（当たっても少ないポイント）。");
  sheet.getRange("A22").setFontColor("#888888").setFontStyle("italic");
}

// ============================
// 結果入力シート
// ============================
function setupResultSheet(ss) {
  let sheet = ss.getSheetByName("📋結果入力");
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet("📋結果入力", 2);

  sheet.getRange("A1:G1").setValues([["試合ID", "ラウンド", "チームA", "チームB", "スコアA", "スコアB", "勝者（自動）"]])
    .setBackground("#1a3a5c").setFontColor("white").setFontWeight("bold");

  let row = 2;
  ROUNDS.forEach(round => {
    round.matches.forEach(match => {
      sheet.getRange(row, 1, 1, 4).setValues([[match.id, round.id, match.teamA, match.teamB]]);
      sheet.getRange(row, 7).setFormula(
        `=IF(AND(E${row}<>"",F${row}<>""),IF(E${row}>F${row},C${row},IF(E${row}<F${row},D${row},"PK")),"")`
      );
      row++;
    });
  });

  sheet.getRange(2, 7, row - 2, 1).setBackground("#e8f5e9");

  sheet.setColumnWidth(1, 90);
  sheet.setColumnWidth(2, 80);
  sheet.setColumnWidth(3, 150);
  sheet.setColumnWidth(4, 150);
  sheet.setColumnWidth(5, 80);
  sheet.setColumnWidth(6, 80);
  sheet.setColumnWidth(7, 150);

  sheet.getRange(row + 1, 1).setValue("※ PKの場合は勝者列（G列）に直接勝者チーム名を手入力してください");
  sheet.getRange(row + 1, 1).setFontColor("#888888").setFontStyle("italic");
}

// ============================
// ランキングシート
// ============================
function setupRankingSheet(ss) {
  let sheet = ss.getSheetByName("🏆ランキング");
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet("🏆ランキング", 3);

  sheet.getRange("A1:G1").merge()
    .setValue("🏆 ポイントランキング")
    .setBackground("#1a3a5c").setFontColor("#f0c040")
    .setFontSize(14).setFontWeight("bold")
    .setHorizontalAlignment("center");

  sheet.getRange("A2").setValue("「⚽TOTO管理」→「ランキング更新」を押すと最新の集計結果が表示されます");
  sheet.getRange("A2:G2").merge().setFontColor("#8ab4d8").setBackground("#0d2137").setHorizontalAlignment("center");

  const headers = ["順位", "名前", "獲得ポイント", "使用済み(円)", "残り予算(円)", "的中数", "賞金予測(円)"];
  sheet.getRange("A4:G4").setValues([headers])
    .setBackground("#1a3a5c").setFontColor("white").setFontWeight("bold");

  sheet.setColumnWidth(1, 60);
  sheet.setColumnWidth(2, 120);
  sheet.setColumnWidth(3, 130);
  sheet.setColumnWidth(4, 120);
  sheet.setColumnWidth(5, 120);
  sheet.setColumnWidth(6, 80);
  sheet.setColumnWidth(7, 130);
}

// ============================
// 賭けシート作成（ラウンド別）
// ============================
function createBetSheet(ss, round) {
  let sheet = ss.getSheetByName(round.tab);
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet(round.tab);

  // タイトル
  sheet.getRange("A1:B1").merge()
    .setValue(`${round.name} — 賭けシート`)
    .setBackground("#1a3a5c").setFontColor("#f0c040")
    .setFontSize(13).setFontWeight("bold");

  sheet.getRange("C1").setValue(`締切: ${round.matchDate} 試合開始前`)
    .setFontColor("#8ab4d8").setBackground("#0d2137");

  // 使い方
  sheet.getRange("A2:D2").merge()
    .setValue(`📌 自分の列に「賭けたいチーム名」を入力（例: ブラジル）。空欄=賭けなし。1試合${CFG.betUnit}円固定、合計上限${CFG.maxBudget}円`)
    .setFontColor("#c0d8f0").setBackground("#0a1628").setFontStyle("italic");

  // ヘッダー行3: 試合情報ラベル
  sheet.getRange("A3").setValue("試合ID").setBackground("#0d2137").setFontColor("#6a9bc0").setFontWeight("bold");
  sheet.getRange("B3").setValue("対戦カード").setBackground("#0d2137").setFontColor("#6a9bc0").setFontWeight("bold");

  // 参加者名を取得してC列以降に配置
  const master = ss.getSheetByName("👥参加者マスタ");
  const masterData = master.getDataRange().getValues();
  const participants = [];
  for (let i = 3; i < masterData.length; i++) {
    if (masterData[i][0] && masterData[i][0] !== "") {
      participants.push(masterData[i][0]);
    }
  }

  // 参加者ヘッダー（C列以降）
  participants.forEach((name, j) => {
    const col = j + 3;
    sheet.getRange(3, col).setValue(name)
      .setBackground("#1a3a5c").setFontColor("white").setFontWeight("bold")
      .setHorizontalAlignment("center");
  });

  // 試合行（4行目以降）
  round.matches.forEach((match, i) => {
    const row = i + 4;
    const card = match.teamA === "TBD" ? "（対戦カード未定）" : `${match.teamA} vs ${match.teamB}`;

    sheet.getRange(row, 1).setValue(match.id).setBackground("#0a1628").setFontColor("#6a9bc0");
    sheet.getRange(row, 2).setValue(card).setBackground("#0a1628").setFontColor("#c0d8f0");

    // 参加者の賭け金入力欄
    participants.forEach((_, j) => {
      const col = j + 3;
      const cell = sheet.getRange(row, col);
      cell.setBackground("#0d2137").setHorizontalAlignment("center");
      // バリデーション：100円単位、最大100円
      const rule = SpreadsheetApp.newDataValidation()
        .requireValueInList(["", "100"], true)
        .setAllowInvalid(false)
        .build();
      // 100円固定なのでドロップダウンより数値入力の方がシンプル
      // → 手入力に変更（0か100のみ有効とする注記を付ける）
    });

    // 行の色分け（奇数・偶数）
    if (i % 2 === 0) {
      sheet.getRange(row, 1, 1, participants.length + 2).setBackground("#0d2137");
    } else {
      sheet.getRange(row, 1, 1, participants.length + 2).setBackground("#0a1628");
    }
    sheet.getRange(row, 1).setBackground("#0a1628").setFontColor("#6a9bc0");
    sheet.getRange(row, 2).setFontColor("#c0d8f0");
    for (let j = 0; j < participants.length; j++) {
      sheet.getRange(row, j + 3).setHorizontalAlignment("center").setFontColor("#f0c040").setFontWeight("bold");
    }
  });

  // 合計行
  const totalRow = round.matches.length + 4;
  sheet.getRange(totalRow, 1, 1, 2).merge().setValue("合計使用額（円）")
    .setBackground("#1a3a5c").setFontColor("white").setFontWeight("bold");

  participants.forEach((_, j) => {
    const col = j + 3;
    const colLetter = columnToLetter(col);
    // チーム名が入っているセル数 × 100円
    sheet.getRange(totalRow, col)
      .setFormula(`=COUNTA(${colLetter}4:${colLetter}${totalRow - 1})*${CFG.betUnit}`)
      .setBackground("#1a3a5c").setFontColor("#f0c040").setFontWeight("bold")
      .setHorizontalAlignment("center");
  });

  // 列幅調整
  sheet.setColumnWidth(1, 90);
  sheet.setColumnWidth(2, 200);
  for (let j = 0; j < participants.length; j++) {
    sheet.setColumnWidth(j + 3, 100);
  }

  // 行固定
  sheet.setFrozenRows(3);

  // 注記
  const noteRow = totalRow + 2;
  sheet.getRange(noteRow, 1, 1, 4).merge()
    .setValue("📌 入力ルール：自分の列に賭けたいチーム名を入力（例: ブラジル / フランス）。空欄=賭けなし。1試合100円固定。合計上限1,000円。")
    .setFontColor("#6a9bc0").setFontStyle("italic");

  return sheet;
}

function setupR32BetSheet(ss) {
  createBetSheet(ss, ROUNDS[0]);
}

// ============================
// 次のラウンドのシートを追加
// ============================
function addNextRoundSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ui = SpreadsheetApp.getUi();

  const roundNames = ROUNDS.map(r => r.name);
  const existing = ss.getSheets().map(s => s.getName());

  const nextRound = ROUNDS.find(r => !existing.includes(r.tab));
  if (!nextRound) {
    ui.alert("全ラウンドのシートが既に作成されています。");
    return;
  }

  // R32以外はTBDを実際のチーム名に更新するよう促す
  if (nextRound.id !== "R32") {
    const res = ui.alert(
      `${nextRound.name}の賭けシートを作成します。\n\n` +
      "⚠️ 作成前に「📋結果入力」シートで前のラウンドの結果を入力し、" +
      "対戦カード（TBD）を実際のチーム名に更新することをお勧めします。\n\n続けますか？",
      SpreadsheetApp.getUi().ButtonSet.YES_NO
    );
    if (res !== SpreadsheetApp.getUi().Button.YES) return;
  }

  createBetSheet(ss, nextRound);
  ui.alert(`✅ ${nextRound.name}の賭けシートを作成しました！\n締切: ${nextRound.matchDate}試合開始前`);
}

// ============================
// ランキング更新
// ============================
function updateRanking() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const masterSheet = ss.getSheetByName("👥参加者マスタ");
  const resultSheet = ss.getSheetByName("📋結果入力");
  const oddsSheet   = ss.getSheetByName("📊オッズ");
  const rankSheet   = ss.getSheetByName("🏆ランキング");

  // 結果取得（試合ID → 勝者）
  const resultData = resultSheet.getDataRange().getValues();
  const winnerMap = {};
  const roundOfMatch = {};
  for (let i = 1; i < resultData.length; i++) {
    const id = resultData[i][0];
    const round = resultData[i][1];
    const winner = resultData[i][6];
    if (id && winner) {
      winnerMap[id] = winner;
      roundOfMatch[id] = round;
    }
  }

  // オッズ取得
  const oddsData = oddsSheet.getDataRange().getValues();
  const oddsMap = {};
  for (let i = 1; i < oddsData.length; i++) {
    if (oddsData[i][0]) oddsMap[oddsData[i][0]] = oddsData[i][2];
  }

  // ラウンドポイント
  const roundPts = { R32: 1, R16: 2, QF: 4, SF: 8, Final: 16 };

  // 参加者リスト
  const masterData = masterSheet.getDataRange().getValues();
  const participants = [];
  for (let i = 3; i < masterData.length; i++) {
    const name = masterData[i][0];
    if (!name || name === "") continue;
    participants.push({ name, email: masterData[i][1], row: i + 1 });
  }

  // 各参加者のポイント・使用額を集計
  const results = participants.map(p => {
    let totalPoints = 0;
    let totalBet = 0;
    let hitCount = 0;

    ROUNDS.forEach(round => {
      const betSheet = ss.getSheetByName(round.tab);
      if (!betSheet) return;

      const betData = betSheet.getDataRange().getValues();
      // 3行目がヘッダー（参加者名）、4行目以降が試合
      const headerRow = betData[2];
      const colIdx = headerRow.findIndex(c => c === p.name);
      if (colIdx < 0) return;

      round.matches.forEach((match, mi) => {
        const betRow = betData[mi + 3]; // 4行目以降
        if (!betRow) return;
        // セルにはチーム名を入力（例: "ブラジル"）、空欄は賭けなし
        const betValue = String(betRow[colIdx]).trim();
        if (!betValue) return;

        totalBet += CFG.betUnit; // 1試合 = 100円固定

        const winner = winnerMap[match.id];
        if (!winner) return;

        if (betValue === winner) {
          const basePt = roundPts[round.id] || 1;
          const odds = oddsMap[winner] || 1;
          totalPoints += Math.round(CFG.betUnit * basePt * odds * 10) / 10;
          hitCount++;
        }
      });
    });

    return { name: p.name, totalPoints, totalBet, hitCount };
  });

  // ソート
  results.sort((a, b) => b.totalPoints - a.totalPoints);

  // 総使用額でプール計算（全参加者のtotalBet合計）
  const totalPool = results.reduce((sum, r) => sum + r.totalBet, 0);
  const prizePool = Math.floor(totalPool * 0.8); // 胴元20%
  const prizes = [0.50, 0.30, 0.20].map(r => Math.floor(prizePool * r));

  // ランキングシート更新
  const dataStart = 5;
  rankSheet.getRange(dataStart, 1, Math.max(results.length + 5, 10), 7).clearContent().setBackground(null);

  rankSheet.getRange("A3").setValue(`賞金プール: ${prizePool.toLocaleString()}円　|　最終更新: ${new Date().toLocaleString("ja-JP")}`);
  rankSheet.getRange("A3:G3").merge().setFontColor("#8ab4d8").setBackground("#0d2137").setHorizontalAlignment("center");

  results.forEach((r, i) => {
    const rank = i + 1;
    const medal = rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : rank;
    const prize = rank <= 3 ? prizes[rank - 1] : "-";
    const remaining = CFG.maxBudget - r.totalBet;

    rankSheet.getRange(dataStart + i, 1, 1, 7).setValues([[
      medal, r.name, r.totalPoints, r.totalBet, remaining, r.hitCount, prize
    ]]);

    // 色分け
    const bg = rank === 1 ? "#fff8dc" : rank === 2 ? "#f5f5f5" : rank === 3 ? "#fde8d0" : null;
    if (bg) rankSheet.getRange(dataStart + i, 1, 1, 7).setBackground(bg);
  });

  // マスタシートも更新
  participants.forEach((p, i) => {
    const r = results.find(x => x.name === p.name);
    if (!r) return;
    masterSheet.getRange(p.row, 3).setValue(r.totalBet);      // 使用済み
    masterSheet.getRange(p.row, 5).setValue(r.totalPoints);   // ポイント
  });

  SpreadsheetApp.getUi().alert(
    `✅ ランキング更新完了！\n参加者: ${results.length}名\n賞金プール: ${prizePool.toLocaleString()}円`
  );
}

// ============================
// リマインドメール送信
// ============================
function sendReminderNow() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const master = ss.getSheetByName("👥参加者マスタ");
  const data = master.getDataRange().getValues();

  // 次の締切ラウンドを取得
  const today = new Date();
  const nextRound = ROUNDS.find(r => {
    const d = new Date(r.matchDate);
    return d >= today;
  });

  if (!nextRound) {
    SpreadsheetApp.getUi().alert("リマインド対象のラウンドが見つかりません。");
    return;
  }

  const ssUrl = ss.getUrl();
  let sentCount = 0;

  for (let i = 3; i < data.length; i++) {
    const name = data[i][0];
    const email = data[i][1];
    if (!name || !email || !email.includes("@")) continue;

    const subject = `⚽【TOTO】${nextRound.name}の賭けを忘れずに！締切: ${nextRound.matchDate}`;
    const body = `${name} さん\n\n` +
      `ワールドカップTOTOの${nextRound.name}の締切が近づいています！\n\n` +
      `📋 賭けシートはこちら:\n${ssUrl}\n\n` +
      `⏰ 締切: ${nextRound.matchDate} 試合開始前\n` +
      `💰 賭け方: 「${nextRound.tab}」タブを開いて、自分の名前の列に賭けたいチーム名を入力（例: ブラジル）\n` +
      `📌 1試合最大${CFG.maxPerMatch}円、合計上限${CFG.maxBudget}円\n\n` +
      `胴元: ${CFG.administrator}`;

    GmailApp.sendEmail(email, subject, body);
    sentCount++;
  }

  SpreadsheetApp.getUi().alert(`✅ ${sentCount}名にリマインドメールを送信しました（対象: ${nextRound.name}）`);
}

// ============================
// リマインド自動トリガー設定
// ============================
function setupReminderTrigger() {
  // 既存のトリガー削除
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === "autoReminder")
    .forEach(t => ScriptApp.deleteTrigger(t));

  // 毎日9時に実行（試合前日に当たる日にメール送信）
  ScriptApp.newTrigger("autoReminder")
    .timeBased()
    .everyDays(1)
    .atHour(CFG.reminderHour)
    .create();

  SpreadsheetApp.getUi().alert(
    `✅ 毎日${CFG.reminderHour}時に自動チェックするトリガーを設定しました。\n` +
    "試合前日の朝9時に参加者へリマインドメールが自動送信されます。"
  );
}

function autoReminder() {
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(today.getDate() + 1);
  const tomorrowStr = Utilities.formatDate(tomorrow, "Asia/Tokyo", "yyyy-MM-dd");

  const targetRound = ROUNDS.find(r => r.matchDate === tomorrowStr);
  if (targetRound) {
    sendReminderNow();
  }
}

// ============================
// 賭け一覧＆SIMシート
// ============================
function updateBetSummarySheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const masterSheet = ss.getSheetByName("👥参加者マスタ");
  const oddsSheet   = ss.getSheetByName("📊オッズ");

  // 参加者リスト
  const masterData = masterSheet.getDataRange().getValues();
  const participants = [];
  for (let i = 3; i < masterData.length; i++) {
    const name = masterData[i][0];
    if (name && name !== "") participants.push(name);
  }

  // オッズマップ
  const oddsData = oddsSheet.getDataRange().getValues();
  const oddsMap = {};
  for (let i = 1; i < oddsData.length; i++) {
    if (oddsData[i][0]) oddsMap[oddsData[i][0]] = oddsData[i][2];
  }

  const roundPts = { R32: 1, R16: 2, QF: 4, SF: 8, Final: 16 };

  // シート準備
  let sheet = ss.getSheetByName("📊賭け一覧＆SIM");
  if (!sheet) sheet = ss.insertSheet("📊賭け一覧＆SIM");
  sheet.clearContents();
  sheet.clearFormats();

  // ===== セクション1: 誰がどこに賭けているか一覧 =====
  let row = 1;

  sheet.getRange(row, 1, 1, participants.length + 3).merge()
    .setValue("📋 賭け一覧 — 誰がどの試合に賭けているか")
    .setBackground("#1a3a5c").setFontColor("#f0c040")
    .setFontSize(13).setFontWeight("bold");
  row++;

  // ヘッダー行
  const header1 = ["ラウンド", "試合ID", "対戦カード", ...participants];
  sheet.getRange(row, 1, 1, header1.length).setValues([header1])
    .setBackground("#0d2137").setFontColor("#6a9bc0").setFontWeight("bold");
  row++;

  // 各ラウンドの賭け内容を出力
  ROUNDS.forEach(round => {
    const betSheet = ss.getSheetByName(round.tab);
    if (!betSheet) return;

    const betData = betSheet.getDataRange().getValues();
    const headerRow = betData[2]; // 3行目（0-indexed: 2）

    round.matches.forEach((match, mi) => {
      const betRow = betData[mi + 3]; // 4行目以降
      if (!betRow) return;

      const card = match.teamA === "TBD" ? "（未定）" : `${match.teamA} vs ${match.teamB}`;
      const rowData = [round.name, match.id, card];

      participants.forEach(name => {
        const colIdx = headerRow.findIndex(c => c === name);
        const val = colIdx >= 0 && betRow[colIdx] ? betRow[colIdx] : "";
        rowData.push(val);
      });

      sheet.getRange(row, 1, 1, rowData.length).setValues([rowData]);

      // 行の背景色
      const bg = mi % 2 === 0 ? "#0d2137" : "#0a1628";
      sheet.getRange(row, 1, 1, rowData.length).setBackground(bg);
      sheet.getRange(row, 1).setFontColor("#8ab4d8");
      sheet.getRange(row, 2).setFontColor("#6a9bc0");
      sheet.getRange(row, 3).setFontColor("#c0d8f0");
      for (let j = 0; j < participants.length; j++) {
        const cell = sheet.getRange(row, j + 4);
        cell.setFontColor("#f0c040").setFontWeight("bold").setHorizontalAlignment("center");
      }
      row++;
    });
  });

  row += 2;

  // ===== セクション2: SIM — あるチームが勝ったら各自いくら獲得？ =====
  sheet.getRange(row, 1, 1, participants.length + 3).merge()
    .setValue("🎲 SIM — 各試合の勝者ごとに獲得ポイント試算")
    .setBackground("#1a3a5c").setFontColor("#f0c040")
    .setFontSize(13).setFontWeight("bold");
  row++;

  sheet.getRange(row, 1, 1, participants.length + 3).merge()
    .setValue("※ 現在の賭け内容をもとに「もしこのチームが勝ったら」を試算。ポイント = 100円 × ラウンド倍率 × オッズ")
    .setBackground("#0a1628").setFontColor("#8ab4d8").setFontStyle("italic");
  row++;

  const header2 = ["ラウンド", "試合ID", "もし勝者が…", ...participants];
  sheet.getRange(row, 1, 1, header2.length).setValues([header2])
    .setBackground("#0d2137").setFontColor("#6a9bc0").setFontWeight("bold");
  row++;

  ROUNDS.forEach(round => {
    const betSheet = ss.getSheetByName(round.tab);
    if (!betSheet) return;

    const betData = betSheet.getDataRange().getValues();
    const headerRow = betData[2];
    const basePt = roundPts[round.id] || 1;

    round.matches.forEach((match, mi) => {
      const betRow = betData[mi + 3];
      if (!betRow) return;

      const teams = match.teamA === "TBD" ? ["（未定）"] : [match.teamA, match.teamB];

      teams.forEach((team, ti) => {
        const simRow = [round.name, match.id, team === "（未定）" ? "（未定）" : `${team} が勝つ`];
        const odds = oddsMap[team] || 1;

        participants.forEach(name => {
          const colIdx = headerRow.findIndex(c => c === name);
          const bet = colIdx >= 0 ? String(betRow[colIdx] || "").trim() : "";
          if (bet === team) {
            const pts = Math.round(CFG.betUnit * basePt * odds * 10) / 10;
            simRow.push(`+${pts}pt`);
          } else if (bet !== "" && bet !== team) {
            simRow.push("ハズレ");
          } else {
            simRow.push("-");
          }
        });

        sheet.getRange(row, 1, 1, simRow.length).setValues([simRow]);

        const bg = (mi * 2 + ti) % 2 === 0 ? "#0d2137" : "#0a1628";
        sheet.getRange(row, 1, 1, simRow.length).setBackground(bg);
        sheet.getRange(row, 1).setFontColor("#8ab4d8");
        sheet.getRange(row, 2).setFontColor("#6a9bc0");
        sheet.getRange(row, 3).setFontColor("#c0d8f0").setFontWeight("bold");

        for (let j = 0; j < participants.length; j++) {
          const cell = sheet.getRange(row, j + 4);
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

  // 列幅調整
  sheet.setColumnWidth(1, 110);
  sheet.setColumnWidth(2, 90);
  sheet.setColumnWidth(3, 180);
  for (let j = 0; j < participants.length; j++) {
    sheet.setColumnWidth(j + 4, 100);
  }

  sheet.setFrozenRows(2);

  SpreadsheetApp.getUi().alert("✅ 賭け一覧＆SIMシートを更新しました！");
}

// ============================
// ユーティリティ
// ============================
function columnToLetter(col) {
  let letter = "";
  while (col > 0) {
    const rem = (col - 1) % 26;
    letter = String.fromCharCode(65 + rem) + letter;
    col = Math.floor((col - 1) / 26);
  }
  return letter;
}
