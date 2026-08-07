"""
国税庁法人番号公表システムWeb-API を使って屋号・掲載名から法人番号と法人名を補完する。
NTA_API_KEY 環境変数（アプリケーションID）が未設定の場合はスキップ。

APIの利用登録（無料）: https://www.houjin-bangou.nta.go.jp/apiriyou/

重要な仕様（v4 /name エンドポイント）:
  - パラメータ名は `id`（`appId` ではない）
  - `type` は応答形式: 01=CSV/Shift-JIS, 02=CSV/Unicode, 12=XML/Unicode
  - 検索方式は `mode`: 1=前方一致, 2=部分一致
  - JSON出力は無いためXML(type=12)を取得してパースする

精度方針:
  - 掲載名（屋号）から「法人名」部分だけを抽出して検索する
  - 抽出できない（法人格を含まない）純粋な屋号はスキップ（空欄のまま）
  - 「掲載名が登録法人名で始まる」もしくは「抽出名と登録名が完全一致」する候補のみ採用
  - 複数該当時は住所（市区町村）で絞り込み、それでも一意にならなければ空欄
"""
import asyncio
import logging
import os
import re
import unicodedata
import xml.etree.ElementTree as ET

import aiohttp

logger = logging.getLogger(__name__)

NTA_URL = "https://api.houjin-bangou.nta.go.jp/4/name"

# 法人格キーワード（前方・後方どちらにも出現しうる）
CORP_KEYWORDS = [
    "株式会社", "有限会社", "合同会社", "合資会社", "合名会社",
    "一般社団法人", "一般財団法人", "公益社団法人", "公益財団法人",
    "医療法人社団", "医療法人財団", "医療法人", "社会福祉法人", "学校法人",
    "宗教法人", "特定非営利活動法人", "独立行政法人", "国立大学法人",
]


def _norm(s: str) -> str:
    """全角→半角・空白除去・小文字化で比較用に正規化。"""
    return "".join(unicodedata.normalize("NFKC", s or "").split()).lower()


def _clean(raw: str) -> str:
    """括弧内・注記を除去して掲載名を掃除する。"""
    s = unicodedata.normalize("NFKC", raw or "")
    # 括弧で囲まれた部分を除去
    s = re.sub(r"[（(【\[＜<「『][^）)】\]＞>」』]*[）)】\]＞>」』]", " ", s)
    # 注記記号以降を切り捨て
    for mk in ["※", "/", "／", "\\", "｜", "|"]:
        s = s.split(mk)[0]
    return " ".join(s.split())


def extract_seed(cleaned: str) -> str:
    """掃除済み掲載名から検索の種となる法人名を抽出。無ければ空文字。"""
    tokens = cleaned.split()
    for i, tok in enumerate(tokens):
        for kw in CORP_KEYWORDS:
            if tok == kw and i + 1 < len(tokens):
                return kw + tokens[i + 1]          # 例: 「株式会社 ○○」
            if tok.startswith(kw) and len(tok) > len(kw):
                return tok                          # 例: 「株式会社○○」
            if tok.endswith(kw) and len(tok) > len(kw):
                return tok                          # 例: 「○○株式会社」
    return ""


def _extract_city(raw: str) -> str:
    """住所から東京都の市区町村を抽出（絞り込み用）。"""
    s = unicodedata.normalize("NFKC", raw or "")
    m = re.search(r"東京都\s*([^\s0-9]+?[区市町村])", s)
    return m.group(1) if m else ""


def _select(raw: str, candidates: list) -> tuple[str, str]:
    """候補 [(num, name, pref, city), ...] から最も確からしい1件を選ぶ。"""
    cleaned = _clean(raw)
    seed = extract_seed(cleaned)
    if not seed:
        return "", ""
    full = _norm(cleaned)
    nseed = _norm(seed)

    passed = [
        c for c in candidates
        if _norm(c[1]) == nseed or (full and full.startswith(_norm(c[1])))
    ]
    if not passed:
        return "", ""
    if len(passed) == 1:
        return passed[0][0], passed[0][1]

    # 複数該当 → 住所の市区町村で絞り込み
    city = _extract_city(raw)
    if city:
        cm = [c for c in passed if city in (c[2] + c[3])]
        if len(cm) == 1:
            return cm[0][0], cm[0][1]
        if cm:
            passed = cm

    # 完全一致が1件だけならそれ
    exact = [c for c in passed if _norm(c[1]) == nseed]
    if len(exact) == 1:
        return exact[0][0], exact[0][1]

    # 一意に決められない → 誤登録を避けて空欄
    return "", ""


def _parse_corporations(xml_text: str) -> list:
    """NTA APIのXML応答を [(num, name, pref, city), ...] にパース。"""
    out = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.debug(f"XMLパース失敗: {e}")
        return out

    def _local(tag: str) -> str:
        return tag.split("}")[-1]

    def _child(el, name: str) -> str:
        for c in el:
            if _local(c.tag) == name:
                return (c.text or "").strip()
        return ""

    for el in root.iter():
        if _local(el.tag) != "corporation":
            continue
        num = _child(el, "corporateNumber")
        name = _child(el, "name")
        pref = _child(el, "prefectureName")
        city = _child(el, "cityName")
        if num and name:
            out.append((num, name, pref, city))
    return out


async def _lookup_one(
    session: aiohttp.ClientSession, company_name: str, address: str, app_id: str
) -> tuple[str, str]:
    """(corporate_number, legal_name) を返す。未取得は空文字。"""
    cleaned = _clean(company_name)
    seed = extract_seed(cleaned)
    if not seed:
        return "", ""   # 法人格を含まない純粋な屋号はスキップ

    params = {
        "id": app_id,
        "name": seed,
        "type": "12",   # XML / Unicode
        "mode": "1",    # 前方一致
    }
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with session.get(NTA_URL, params=params, timeout=timeout) as resp:
            if resp.status != 200:
                logger.debug(f"NTA APIエラー status={resp.status} ({seed})")
                return "", ""
            raw = await resp.read()
        xml_text = raw.decode("utf-8", errors="replace")
        candidates = _parse_corporations(xml_text)
        if not candidates:
            return "", ""
        return _select(company_name, candidates)
    except Exception as e:
        logger.debug(f"法人番号取得エラー ({seed}): {e}")
        return "", ""


async def enrich_with_corporate_numbers(leads: list, concurrency: int = 3) -> int:
    """
    corporate_number が空のリードに対して法人番号と法人名を補完する。
    補完できた件数を返す。
    """
    app_id = os.environ.get("NTA_API_KEY", "")
    if not app_id:
        logger.info("[法人番号] NTA_API_KEY が未設定のためスキップ")
        return 0

    targets = [l for l in leads if not l.corporate_number]
    if not targets:
        return 0

    logger.info(f"[法人番号] 国税庁API検索開始: {len(targets)}件")
    found = 0
    sem = asyncio.Semaphore(concurrency)

    async def _do(session: aiohttp.ClientSession, lead) -> None:
        nonlocal found
        async with sem:
            await asyncio.sleep(0.15)
            num, legal = await _lookup_one(session, lead.company_name, lead.address, app_id)
            if num:
                lead.corporate_number = num
                if legal:
                    lead.legal_name = legal
                found += 1

    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[_do(session, l) for l in targets])

    logger.info(f"[法人番号] 完了: {len(targets)}件中 {found}件 取得")
    return found
