// ============================================================
// 設定（ここを変更してください）
// ============================================================
const SPREADSHEET_ID = '1yeOJ2TtCMxYdsM3IrJzYt6mSTMiYPp-sMIHoIo7q-yQ'; // 営業進捗ログ
const SLACK_WEBHOOK_URL = ''; // Slack Incoming Webhook URL を入力
const APP_URL = ''; // デプロイ後の Web App URL を入力

// ============================================================
// メンバーマスタ（Slack User ID は Slack プロフィールから取得）
// ============================================================
const MEMBERS = {
  'ソリューション': [
    { name: '下川',  slackId: '' },
    { name: '寒川',  slackId: '' },
    { name: '堀江',  slackId: '' },
  ],
  'カスタマーサクセス': [
    { name: '吉岡（たま）', slackId: '' },
    { name: 'ゾンハン',     slackId: '' },
    { name: '畠山',         slackId: '' },
    { name: 'なな',         slackId: '' },
    { name: '前田',         slackId: '' },
    { name: '中野',         slackId: '' },
  ],
  'テレマーケティング': [
    { name: '島田',   slackId: '' },
    { name: '城市',   slackId: '' },
    { name: '長谷川', slackId: '' },
  ],
};

// KPI 定義（デイリー入力対象）
const KPIS = {
  'ソリューション': ['複数プラン提案数（社単UP）', 'プレゼン金額（バジェットUP）万円', '他媒体提案数（ミックス）', '新規受注件数'],
  'カスタマーサクセス': ['現S有効接触', '現Sヒアリング', '落ちS接触', '新規プレ数', '目標獲得社数'],
  'テレマーケティング': ['有効接触件数', 'ニーズありパス件数', 'パス後受注件数'],
};

// KGI 定義（週次・月次・Q で集計）
const KGIS = {
  'ソリューション': ['新規受注件数', 'プレゼン金額（バジェットUP）万円'],
  'カスタマーサクセス': ['目標獲得社数', '新規プレ数'],
  'テレマーケティング': ['パス後受注件数', 'ニーズありパス件数'],
};

// ============================================================
// Web App エントリポイント
// ============================================================
function doGet(e) {
  const action = e && e.parameter && e.parameter.action;

  if (action === 'fetch') {
    return fetchEntries(e.parameter);
  }

  // フロントエンド HTML を配信
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('営業進捗ダッシュボード')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const result = saveEntry(data);
    return ContentService
      .createTextOutput(JSON.stringify({ ok: true, id: result }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, error: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// ============================================================
// データ保存
// ============================================================
function saveEntry(data) {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  let sheet = ss.getSheetByName('log');
  if (!sheet) {
    sheet = ss.insertSheet('log');
    sheet.appendRow(['id', 'date', 'team', 'member', 'kpi', 'target', 'actual', 'note', 'timestamp']);
    sheet.setFrozenRows(1);
  }
  const id = Date.now();
  sheet.appendRow([
    id,
    data.date,
    data.team,
    data.member,
    data.kpi,
    data.target !== undefined ? data.target : '',
    data.actual,
    data.note || '',
    new Date().toISOString(),
  ]);
  return id;
}

// ============================================================
// データ取得・集計
// ============================================================
function fetchEntries(params) {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName('log');

  if (!sheet || sheet.getLastRow() < 2) {
    return jsonResponse({ entries: [], members: MEMBERS, kpis: KPIS, kgis: KGIS });
  }

  const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, 9).getValues();
  let entries = rows.map(r => ({
    id: r[0], date: r[1], team: r[2], member: r[3],
    kpi: r[4], target: r[5] === '' ? null : Number(r[5]),
    actual: Number(r[6]), note: r[7],
  }));

  // フィルタ
  if (params.team) entries = entries.filter(e => e.team === params.team);
  if (params.member) entries = entries.filter(e => e.member === params.member);

  // 期間集計
  const period = params.period || 'daily';
  const aggregated = aggregate(entries, period);

  return jsonResponse({ entries: aggregated, members: MEMBERS, kpis: KPIS, kgis: KGIS });
}

function aggregate(entries, period) {
  const keyFn = {
    daily:     e => String(e.date).slice(0, 10),
    weekly:    e => getWeekKey(String(e.date).slice(0, 10)),
    monthly:   e => String(e.date).slice(0, 7),
    quarterly: e => getQuarterKey(String(e.date).slice(0, 10)),
  }[period] || (e => String(e.date).slice(0, 10));

  const map = {};
  entries.forEach(e => {
    const k = keyFn(e);
    const mk = `${e.member}__${e.kpi}`;
    if (!map[k]) map[k] = {};
    if (!map[k][mk]) map[k][mk] = { member: e.member, kpi: e.kpi, actual: 0, target: null, count: 0, notes: [] };
    map[k][mk].actual += e.actual;
    if (e.target !== null) map[k][mk].target = (map[k][mk].target || 0) + e.target;
    map[k][mk].count++;
    if (e.note) map[k][mk].notes.push(e.note);
  });

  // フラット化
  const result = [];
  Object.keys(map).sort().reverse().forEach(period => {
    Object.values(map[period]).forEach(d => {
      result.push({ period, ...d });
    });
  });
  return result;
}

function getWeekKey(dateStr) {
  const d = new Date(dateStr);
  const jan1 = new Date(d.getFullYear(), 0, 1);
  const week = Math.ceil(((d - jan1) / 86400000 + jan1.getDay() + 1) / 7);
  return `${d.getFullYear()}-W${String(week).padStart(2, '0')}`;
}

function getQuarterKey(dateStr) {
  const d = new Date(dateStr);
  const q = Math.ceil((d.getMonth() + 1) / 3);
  return `${d.getFullYear()}-Q${q}`;
}

function jsonResponse(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

// ============================================================
// Slack リマインダー（毎日 18:00 に時間トリガーで実行）
// ============================================================
function sendSlackReminder() {
  const today = Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd');
  const dayOfWeek = new Date().getDay();

  // 土日はスキップ
  if (dayOfWeek === 0 || dayOfWeek === 6) return;

  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName('log');

  // 今日入力済みのメンバーを取得
  const inputtedMembers = new Set();
  if (sheet && sheet.getLastRow() >= 2) {
    const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, 9).getValues();
    rows.forEach(r => {
      if (String(r[1]).slice(0, 10) === today) inputtedMembers.add(r[3]);
    });
  }

  // 未入力メンバーを抽出
  const missing = [];
  Object.values(MEMBERS).forEach(members => {
    members.forEach(m => {
      if (!inputtedMembers.has(m.name)) {
        missing.push(m);
      }
    });
  });

  if (missing.length === 0) {
    postToSlack('✅ 本日の進捗入力が全員完了しています！お疲れ様でした。');
    return;
  }

  const mentions = missing.map(m => m.slackId ? `<@${m.slackId}>` : m.name).join(' ');
  const message = [
    `⏰ *本日の進捗入力リマインダー（${today}）*`,
    '',
    `まだ入力が完了していないメンバーがいます：`,
    mentions,
    '',
    `📲 入力はこちら → ${APP_URL}`,
  ].join('\n');

  postToSlack(message);
}

function postToSlack(text) {
  if (!SLACK_WEBHOOK_URL) return;
  UrlFetchApp.fetch(SLACK_WEBHOOK_URL, {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify({ text }),
  });
}

// ============================================================
// セットアップ用ヘルパー（初回のみ手動実行）
// ============================================================
function setupTrigger() {
  // 既存のトリガーを削除
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === 'sendSlackReminder') {
      ScriptApp.deleteTrigger(t);
    }
  });
  // 毎日 18:00〜19:00 に実行
  ScriptApp.newTrigger('sendSlackReminder')
    .timeBased()
    .everyDays(1)
    .atHour(18)
    .create();
  Logger.log('トリガーを設定しました');
}
