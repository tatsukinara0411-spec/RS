# セットアップ手順

## 1. Google Cloud 設定

### 1-1. プロジェクト作成
1. [Google Cloud Console](https://console.cloud.google.com/) を開く
2. 「プロジェクトを作成」→ 名前を入力（例: `teleapo-leads`）→「作成」

### 1-2. APIを有効化
1. 左メニュー「APIとサービス」→「ライブラリ」
2. 「Google Sheets API」を検索 → 「有効にする」
3. 「Google Drive API」を検索 → 「有効にする」

### 1-3. サービスアカウント作成
1. 「APIとサービス」→「認証情報」→「認証情報を作成」→「サービスアカウント」
2. 名前を入力（例: `teleapo-scraper`）→「作成して続行」
3. ロールは「編集者」または「基本 > 編集者」→「完了」

### 1-4. JSONキーのダウンロード
1. 作成したサービスアカウントをクリック
2. 「キー」タブ →「鍵を追加」→「新しい鍵を作成」→「JSON」→「作成」
3. JSONファイルがダウンロードされる

## 2. GitHub Secrets 設定

1. GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」
2. 「New repository secret」で以下を追加:

| Secret名 | 値 |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | ダウンロードしたJSONファイルの**全文**をそのままペースト |
| `GOOGLE_SPREADSHEET_ID` | （省略可）既存スプレッドシートのID。省略すると自動作成 |

## 3. 動作確認

### GitHub Actions で手動実行
1. リポジトリの「Actions」タブ
2. 「テレアポリード 週次収集」→「Run workflow」→「Run workflow」

### ローカルで実行（開発時）
```bash
# 依存関係インストール
pip install -r requirements.txt
playwright install chromium

# 設定ファイルをコピー
cp .env.example .env
# .env を編集して GOOGLE_CREDS_PATH などを設定

# テスト実行（Sheetsへの書き込みなし）
python main.py --dry-run

# 本番実行
python main.py --run-now
```

## 4. スプレッドシートの確認

初回実行後、ログに以下のようなURLが表示されます:
```
✅ スプレッドシートURL: https://docs.google.com/spreadsheets/d/XXXX/edit
```

スプレッドシートは毎週新しいタブ（例: `2026-W24`）に追記されます。

## 5. 自動実行スケジュール

- 毎週**月曜日 8:00 JST** に自動実行
- 300件（各サイト100件）を目標に収集
- 重複企業は自動的にスキップ
