/**
 * 社内ワールドカップTOTO - Google Apps Script セットアップ
 *
 * 使い方:
 * 1. Googleスプレッドシートを新規作成
 * 2. 拡張機能 > Apps Script を開く
 * 3. このコードを貼り付けて保存
 * 4. setupTOTO() を実行 → シートが自動生成される
 */

// ============================
// 設定（胴元が変更）
// ============================
const TOTO_CONFIG = {
  entryFee: 1000,       // 参加費（円）
  houseEdge: 0.20,      // 胴元取り分（20%）
  administrator: "タロウ",
};

const ROUND_POINTS_GAS = {
  "R32": 1, "R16": 2, "QF": 4, "SF": 8, "Final": 16
};

// チーム一覧とオッズ
const TEAMS_ODDS = [
  ["ブラジル",     "🇧🇷", 4.5],
  ["フランス",     "🇫🇷", 5.0],
  ["スペイン",     "🇪🇸", 5.5],
  ["アルゼンチン", "🇦🇷", 6.0],
  ["イングランド", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", 7.0],
  ["ドイツ",       "🇩🇪", 8.0],
  ["ポルトガル",   "🇵🇹", 9.0],
  ["オランダ",     "🇳🇱", 10.0],
  ["ベルギー",     "🇧🇪", 12.0],
  ["クロアチア",   "🇭🇷", 15.0],
  ["ウルグアイ",   "🇺🇾", 18.0],
  ["メキシコ",     "🇲🇽", 20.0],
  ["アメリカ",     "🇺🇸", 25.0],
  ["モロッコ",     "🇲🇦", 35.0],
  ["日本",         "🇯🇵", 40.0],
  ["韓国",         "🇰🇷", 50.0],
];

// 試合一覧（ラウンド, 試合名, チームA, チームB）
const MATCHES_GAS = [
  ["R32", "R32-1",  "ブラジル",     "セネガル"],
  ["R32", "R32-2",  "フランス",     "モロッコ"],
  ["R32", "R32-3",  "スペイン",     "メキシコ"],
  ["R32", "R32-4",  "アルゼンチン", "オーストラリア"],
  ["R32", "R32-5",  "イングランド", "スイス"],
  ["R32", "R32-6",  "ドイツ",       "デンマーク"],
  ["R32", "R32-7",  "ポルトガル",   "チュニジア"],
  ["R32", "R32-8",  "オランダ",     "韓国"],
  ["R32", "R32-9",  "ベルギー",     "カナダ"],
  ["R32", "R32-10", "クロアチア",   "チリ"],
  ["R32", "R32-11", "ウルグアイ",   "ガーナ"],
  ["R32", "R32-12", "アメリカ",     "ナイジェリア"],
  ["R32", "R32-13", "日本",         "ポーランド"],
  ["R32", "R32-14", "コロンビア",   "コートジボワール"],
  ["R32", "R32-15", "エクアドル",   "セルビア"],
  ["R32", "R32-16", "スウェーデン", "カメルーン"],
  ["R16", "R16-1",  "TBD", "TBD"],
  ["R16", "R16-2",  "TBD", "TBD"],
  ["R16", "R16-3",  "TBD", "TBD"],
  ["R16", "R16-4",  "TBD", "TBD"],
  ["R16", "R16-5",  "TBD", "TBD"],
  ["R16", "R16-6",  "TBD", "TBD"],
  ["R16", "R16-7",  "TBD", "TBD"],
  ["R16", "R16-8",  "TBD", "TBD"],
  ["QF",  "QF-1",   "TBD", "TBD"],
  ["QF",  "QF-2",   "TBD", "TBD"],
  ["QF",  "QF-3",   "TBD", "TBD"],
  ["QF",  "QF-4",   "TBD", "TBD"],
  ["SF",  "SF-1",   "TBD", "TBD"],
  ["SF",  "SF-2",   "TBD", "TBD"],
  ["Final", "決勝", "TBD", "TBD"],
];

// ============================
// メイン：シート生成
// ============================
function setupTOTO() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  createOddsSheet(ss);
  createResultSheet(ss);
  createEntrySheet(ss);
  createRankingSheet(ss);

  SpreadsheetApp.getUi().alert("✅ TOTOシートのセットアップ完了！\n\n1. 「オッズ」シートでオッズを確認・調整\n2. 「エントリー」シートのURLを参加者に共有\n3. 「結果入力」シートに試合結果を入力していく\n4. 「ランキング」シートで順位を確認");
}

// ============================
// オッズシート
// ============================
function createOddsSheet(ss) {
  let sheet = ss.getSheetByName("オッズ");
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet("オッズ");

  sheet.getRange("A1:D1").setValues([["チーム名", "国旗", "優勝オッズ(倍)", "備考"]]);
  sheet.getRange("A1:D1").setBackground("#1a3a5c").setFontColor("white").setFontWeight("bold");

  TEAMS_ODDS.forEach((row, i) => {
    sheet.getRange(i + 2, 1, 1, 3).setValues([[row[0], row[1], row[2]]]);
  });

  sheet.setColumnWidth(1, 150);
  sheet.setColumnWidth(2, 50);
  sheet.setColumnWidth(3, 130);

  // オッズ低い順に色付け
  const dataRange = sheet.getRange(2, 3, TEAMS_ODDS.length, 1);
  dataRange.setNumberFormat("0.0");
}

// ============================
// 結果入力シート
// ============================
function createResultSheet(ss) {
  let sheet = ss.getSheetByName("結果入力");
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet("結果入力");

  sheet.getRange("A1:F1").setValues([["試合ID", "ラウンド", "チームA", "チームB", "スコアA", "スコアB"]]);
  sheet.getRange("A1:F1").setBackground("#1a3a5c").setFontColor("white").setFontWeight("bold");

  // G列ヘッダー：勝者（自動計算）
  sheet.getRange("G1").setValue("勝者（自動）").setBackground("#1a3a5c").setFontColor("white").setFontWeight("bold");

  MATCHES_GAS.forEach((row, i) => {
    const r = i + 2;
    sheet.getRange(r, 1, 1, 4).setValues([[row[1], row[0], row[2], row[3]]]);
    // 勝者：スコア入力後に自動判定（PK含む場合は手動）
    sheet.getRange(r, 7).setFormula(
      `=IF(AND(E${r}<>"",F${r}<>""),IF(E${r}>F${r},C${r},IF(E${r}<F${r},D${r},"PK")),"")`
    );
  });

  sheet.setColumnWidth(1, 80);
  sheet.setColumnWidth(2, 70);
  sheet.setColumnWidth(3, 150);
  sheet.setColumnWidth(4, 150);
  sheet.setColumnWidth(5, 80);
  sheet.setColumnWidth(6, 80);
  sheet.setColumnWidth(7, 150);

  // 勝者列に色付け
  const winnerRange = sheet.getRange(2, 7, MATCHES_GAS.length, 1);
  winnerRange.setBackground("#e8f5e9");

  // 注記
  sheet.getRange(MATCHES_GAS.length + 3, 1).setValue("※ PKの場合は「勝者（自動）」が「PK」になるので、G列に直接勝者チーム名を入力してください");
  sheet.getRange(MATCHES_GAS.length + 3, 1).setFontColor("#888888").setFontStyle("italic");
}

// ============================
// エントリーシート（参加者入力）
// ============================
function createEntrySheet(ss) {
  let sheet = ss.getSheetByName("エントリー");
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet("エントリー");

  // ヘッダー行1: ラウンド
  // ヘッダー行2: 試合ID
  // ヘッダー行3: チームA vs チームB
  // 4行目以降: 参加者名 + 各試合の予想

  sheet.getRange("A1").setValue("参加者名");
  sheet.getRange("B1").setValue("支払済");

  MATCHES_GAS.forEach((m, i) => {
    const col = i + 3;
    sheet.getRange(1, col).setValue(m[0]);             // ラウンド
    sheet.getRange(2, col).setValue(m[1]);             // 試合ID
    sheet.getRange(3, col).setValue(`${m[2]} vs ${m[3]}`); // 対戦カード
  });

  // ヘッダー装飾
  sheet.getRange(1, 1, 3, 2).setBackground("#1a3a5c").setFontColor("white").setFontWeight("bold");
  sheet.getRange(1, 3, 3, MATCHES_GAS.length).setBackground("#0d2137").setFontColor("white").setFontWeight("bold");

  // サンプル参加者（削除してOK）
  sheet.getRange("A4").setValue("（サンプル）山田花子");
  sheet.getRange("B4").setValue("✅");

  // 列幅調整
  sheet.setColumnWidth(1, 120);
  sheet.setColumnWidth(2, 70);
  for (let i = 3; i <= MATCHES_GAS.length + 3; i++) {
    sheet.setColumnWidth(i, 130);
  }

  // 行固定（スクロールしやすく）
  sheet.setFrozenRows(3);
  sheet.setFrozenColumns(2);

  // 使い方メモ
  sheet.getRange(1, MATCHES_GAS.length + 5).setValue("← 4行目以降に参加者名と各試合の予想勝者チーム名を入力してください").setFontColor("#888888");
}

// ============================
// ランキングシート（自動集計）
// ============================
function createRankingSheet(ss) {
  let sheet = ss.getSheetByName("ランキング");
  if (sheet) ss.deleteSheet(sheet);
  sheet = ss.insertSheet("ランキング");

  sheet.getRange("A1:F1").setValues([["順位", "名前", "合計ポイント", "正解数", "支払済", "賞金予測（円）"]]);
  sheet.getRange("A1:F1").setBackground("#1a3a5c").setFontColor("white").setFontWeight("bold");

  // 注記
  sheet.getRange("A3").setValue("※ このシートは「updateRanking()」を実行すると自動更新されます");
  sheet.getRange("A3").setFontColor("#888888").setFontStyle("italic");

  sheet.getRange("A5").setValue("▶ メニュー > TOTO管理 > ランキング更新 を押してください");
  sheet.getRange("A5").setFontWeight("bold").setFontColor("#1a3a5c");

  sheet.setColumnWidth(1, 60);
  sheet.setColumnWidth(2, 120);
  sheet.setColumnWidth(3, 130);
  sheet.setColumnWidth(4, 80);
  sheet.setColumnWidth(5, 80);
  sheet.setColumnWidth(6, 120);
}

// ============================
// ランキング更新（手動実行）
// ============================
function updateRanking() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const entrySheet = ss.getSheetByName("エントリー");
  const resultSheet = ss.getSheetByName("結果入力");
  const oddsSheet = ss.getSheetByName("オッズ");
  const rankSheet = ss.getSheetByName("ランキング");

  // 結果取得（試合ID → 勝者）
  const resultData = resultSheet.getDataRange().getValues();
  const resultMap = {};
  const roundMap = {};
  for (let i = 1; i < resultData.length; i++) {
    const matchId = resultData[i][0];
    const round = resultData[i][1];
    const winner = resultData[i][6];
    if (matchId && winner) {
      resultMap[matchId] = winner;
      roundMap[matchId] = round;
    }
  }

  // オッズ取得（チーム名 → オッズ）
  const oddsData = oddsSheet.getDataRange().getValues();
  const oddsMap = {};
  for (let i = 1; i < oddsData.length; i++) {
    oddsMap[oddsData[i][0]] = oddsData[i][2];
  }

  // エントリー取得
  const entryData = entrySheet.getDataRange().getValues();
  const matchIds = entryData[1].slice(2); // 行2: 試合ID
  const participants = [];

  for (let i = 3; i < entryData.length; i++) {
    const name = entryData[i][0];
    const paid = entryData[i][1];
    if (!name || name.includes("サンプル")) continue;

    let totalPoints = 0;
    let correctCount = 0;

    for (let j = 0; j < matchIds.length; j++) {
      const matchId = matchIds[j];
      const prediction = entryData[i][j + 2];
      const actualWinner = resultMap[matchId];
      const round = roundMap[matchId];

      if (prediction && actualWinner && prediction === actualWinner) {
        const basePoints = ROUND_POINTS_GAS[round] || 1;
        const odds = oddsMap[actualWinner] || 1;
        totalPoints += basePoints * odds;
        correctCount++;
      }
    }

    participants.push({ name, paid, totalPoints: Math.round(totalPoints * 10) / 10, correctCount });
  }

  participants.sort((a, b) => b.totalPoints - a.totalPoints);

  // 賞金プール計算
  const paidCount = participants.filter(p => p.paid).length;
  const prizePool = Math.floor(paidCount * TOTO_CONFIG.entryFee * (1 - TOTO_CONFIG.houseEdge));
  const prizeRatios = [0.50, 0.30, 0.20];

  // ランキングシート更新
  const dataStartRow = 7;
  rankSheet.getRange(dataStartRow, 1, Math.max(participants.length, 1), 6).clearContent();

  rankSheet.getRange("B3").setValue(`賞金プール: ${prizePool.toLocaleString()}円  (参加者${paidCount}名 × ${TOTO_CONFIG.entryFee}円 × ${(1 - TOTO_CONFIG.houseEdge) * 100}%)`);
  rankSheet.getRange("B4").setValue(`最終更新: ${new Date().toLocaleString("ja-JP")}`);

  participants.forEach((p, i) => {
    const rank = i + 1;
    const prize = rank <= 3 ? Math.floor(prizePool * prizeRatios[rank - 1]) : 0;
    const rankMedal = rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : rank;
    rankSheet.getRange(dataStartRow + i, 1, 1, 6).setValues([[
      rankMedal, p.name, p.totalPoints, p.correctCount, p.paid, prize > 0 ? prize : "-"
    ]]);
  });

  // 色付け
  if (participants.length > 0) {
    rankSheet.getRange(dataStartRow, 1, 1, 6).setBackground("#fff8dc"); // 金
    if (participants.length > 1) rankSheet.getRange(dataStartRow + 1, 1, 1, 6).setBackground("#f5f5f5"); // 銀
    if (participants.length > 2) rankSheet.getRange(dataStartRow + 2, 1, 1, 6).setBackground("#fde8d0"); // 銅
  }

  SpreadsheetApp.getUi().alert(`✅ ランキング更新完了！\n参加者: ${participants.length}名\n賞金プール: ${prizePool.toLocaleString()}円`);
}

// ============================
// カスタムメニュー追加
// ============================
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("⚽ TOTO管理")
    .addItem("🔧 初回セットアップ（シート作成）", "setupTOTO")
    .addSeparator()
    .addItem("🏆 ランキング更新", "updateRanking")
    .addToUi();
}
