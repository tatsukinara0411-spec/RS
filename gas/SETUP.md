# セットアップ手順

## 1. Google スプレッドシートを作成

1. [Google Drive](https://drive.google.com) を開く
2. 「新規」→「Google スプレッドシート」で新しいシートを作成
3. シート名は何でも OK（例：「営業進捗ログ」）
4. URL の `/d/` と `/edit` の間の文字列が **スプレッドシートID**
   - 例: `https://docs.google.com/spreadsheets/d/【ここ】/edit`

## 2. Google Apps Script を設定

1. スプレッドシートを開き、メニュー「拡張機能」→「Apps Script」をクリック
2. 左側のファイル一覧から `コード.gs` を選択し、**`Code.gs` の内容を全て貼り付け**
3. 「＋」ボタンで新しい HTML ファイルを追加、ファイル名を `index` にして **`index.html` の内容を貼り付け**
4. `Code.gs` の上部にある設定欄を編集：

```js
const SPREADSHEET_ID = 'ここにスプレッドシートIDを入力';
const SLACK_WEBHOOK_URL = 'ここにSlack Webhook URLを入力（後述）';
const APP_URL = ''; // デプロイ後に入力
```

## 3. Web App としてデプロイ

1. Apps Script エディタ右上「デプロイ」→「新しいデプロイ」
2. 種類：「ウェブアプリ」を選択
3. 設定：
   - 説明：「営業進捗ダッシュボード」
   - 次のユーザーとして実行：「自分」
   - アクセスできるユーザー：「全員」（社内のみにする場合は「組織内の全員」）
4. 「デプロイ」をクリック → **Web App URL をコピー**
5. `Code.gs` の `APP_URL` と `index.html` の `GAS_URL` にコピーした URL を貼り付け
6. 再度「デプロイ」→「デプロイを管理」→「編集」→「デプロイ」で更新

## 4. Slack Incoming Webhook を設定

1. [Slack API](https://api.slack.com/apps) → 「Create New App」
2. 「From scratch」→ アプリ名を入力、ワークスペースを選択
3. 「Incoming Webhooks」→「Activate Incoming Webhooks」をON
4. 「Add New Webhook to Workspace」→ 通知を送るチャンネルを選択
5. 表示された Webhook URL を `Code.gs` の `SLACK_WEBHOOK_URL` に貼り付け

## 5. Slack User ID を設定

各メンバーの Slack User ID を取得：
- Slack でメンバーのプロフィールを開く
- 「︙」メニュー → 「メンバーIDをコピー」（例: `U0123ABCDEF`）

`Code.gs` の `MEMBERS` 内の各メンバーの `slackId` に入力：

```js
{ name: '吉岡（たま）', slackId: 'U0123ABCDEF' },
```

## 6. 18時リマインダーのトリガーを設定

1. Apps Script エディタで「トリガー」アイコン（時計マーク）をクリック
2. 「トリガーを追加」をクリック
3. 設定：
   - 実行する関数：`sendSlackReminder`
   - イベントのソース：「時間主導型」
   - 時間ベースのトリガーのタイプ：「日付ベースのタイマー」
   - 時刻：「午後6時〜7時」
4. 保存

または Apps Script エディタで `setupTrigger()` 関数を手動実行しても OK。

## 7. 動作確認

1. Web App URL をスマホで開き、チーム・メンバー・KPI を選んで入力 → 保存
2. スプレッドシートの「log」シートに行が追加されることを確認
3. Apps Script エディタで `sendSlackReminder()` を手動実行し、Slack に通知が届くことを確認
