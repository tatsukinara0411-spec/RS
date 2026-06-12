import os
import logging
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from models.lead import Lead
from utils.credentials import load_service_account_info

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_TITLE = "テレアポリスト"
HEADER = ["会社名", "住所", "電話番号", "業種", "ソース", "収集日時"]


def _get_client() -> gspread.Client:
    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    creds_path = os.environ.get("GOOGLE_CREDS_PATH", "./credentials/service_account.json")

    if creds_json:
        info = load_service_account_info(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)

    return gspread.authorize(creds)


def _get_or_create_spreadsheet(client: gspread.Client) -> gspread.Spreadsheet:
    spreadsheet_id = os.environ.get("GOOGLE_SPREADSHEET_ID")
    if spreadsheet_id:
        return client.open_by_key(spreadsheet_id)

    # 既存のスプレッドシートを検索
    try:
        return client.open(SPREADSHEET_TITLE)
    except gspread.SpreadsheetNotFound:
        pass

    # 新規作成
    ss = client.create(SPREADSHEET_TITLE)
    logger.info(f"スプレッドシートを新規作成しました: {ss.url}")
    print(f"\n✅ スプレッドシートURL: {ss.url}\n")

    # サービスアカウントが作成したシートは共有しないと人間が開けない
    share_email = os.environ.get("GOOGLE_SHARE_EMAIL")
    if share_email:
        ss.share(share_email, perm_type="user", role="writer", notify=True)
        logger.info(f"{share_email} に編集権限を付与しました")
    else:
        logger.warning(
            "GOOGLE_SHARE_EMAIL が未設定です。作成されたスプレッドシートはサービスアカウント"
            "しか開けません。シークレットに自分のGmailアドレスを登録してください。"
        )
    return ss


def _get_or_create_sheet(ss: gspread.Spreadsheet, tab_name: str) -> gspread.Worksheet:
    try:
        ws = ss.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=tab_name, rows=500, cols=10)
        ws.append_row(HEADER)
        logger.info(f"新しいシートタブを作成: {tab_name}")
    return ws


def write_leads(leads: list[Lead], dry_run: bool = False) -> str:
    if not leads:
        logger.info("書き込むリードがありません")
        return ""

    week_tab = datetime.now().strftime("%Y-W%W")

    if dry_run:
        logger.info(f"[DRY RUN] {len(leads)}件をシート '{week_tab}' に書き込む予定")
        for lead in leads[:3]:
            logger.info(f"  - {lead.company_name} | {lead.address} | {lead.phone} | {lead.industry}")
        return "dry_run"

    client = _get_client()
    ss = _get_or_create_spreadsheet(client)
    ws = _get_or_create_sheet(ss, week_tab)

    rows = [
        [
            lead.company_name,
            lead.address,
            lead.phone or "",
            lead.industry,
            lead.source_site,
            lead.collected_at,
        ]
        for lead in leads
    ]
    ws.append_rows(rows, value_input_option="USER_ENTERED")
    logger.info(f"{len(leads)}件をスプレッドシート '{week_tab}' に書き込みました")
    return ss.url
