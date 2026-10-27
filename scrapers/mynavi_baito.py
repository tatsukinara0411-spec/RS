import logging
from datetime import datetime

from playwright.async_api import BrowserContext

from models.lead import Lead
from scrapers.base import BaseScraper
from utils.fingerprint import is_tokyo_23ward

logger = logging.getLogger(__name__)

# 2026年10月時点の職種カテゴリ番号（旧形式の /tokyo/keibi/ などは全件ページ /tokyo/all/ に転送され、
# 業種で絞り込めていなかった）。調べ方: tools/diagnose_v3.py を参照。
INDUSTRY_PATHS = {
    "警備": "ss-18",         # 警備・清掃・ビル管理
    "運輸": "ss-12",         # 配送・引越・ドライバー
    "外食": "ss-1",          # 飲食・フード
    "販売": "ss-3",          # 販売・接客・サービス
    "介護": "ss-9/ssm-117",  # 医療・介護・保育 のうち介護
    "建設": "ss-17",         # 工場・倉庫・建築・土木（工場・倉庫は業種判定で振り分け）
}

BASE_URL = "https://baito.mynavi.jp"


class MynaviBaitoScraper(BaseScraper):
    site_name = "マイナビバイト"

    async def scrape_industry(self, context: BrowserContext, industry: str) -> list[Lead]:
        leads: list[Lead] = []
        path = INDUSTRY_PATHS.get(industry, industry)

        for page_no in range(1, 21):
            if len(leads) >= self.per_industry:
                break

            if page_no == 1:
                url = f"{BASE_URL}/tokyo/{path}/"
            else:
                url = f"{BASE_URL}/tokyo/{path}/?pageNo={page_no}"

            page = await context.new_page()
            try:
                await self.safe_goto(page, url)
                if "/all/" in page.url:
                    logger.error(f"[マイナビバイト] 業種ページが全件ページに転送されました（カテゴリ番号の変更）: {url}")
                    break

                cards = await page.query_selector_all(".tabJobOfferCard")
                if not cards:
                    logger.warning(f"[マイナビバイト] カードなし: {url}")
                    break

                for card in cards:
                    if len(leads) >= self.per_industry:
                        break
                    lead = await self._parse_card(card, industry, url)
                    if lead:
                        leads.append(lead)

                next_btn = await page.query_selector(f"a[href*='pageNo={page_no + 1}']")
                if not next_btn:
                    break

            except Exception as e:
                logger.error(f"[マイナビバイト] エラー {url}: {e}")
                break
            finally:
                await page.close()

        return leads

    async def _parse_card(self, card, industry: str, source_url: str) -> Lead | None:
        try:
            # .shopNameWrap には「他の店舗」ボタンの文字が混ざるため .shopName を使う
            name_el = await card.query_selector(".shopName") or await card.query_selector(".shopNameWrap")
            company_name = (await name_el.inner_text()).strip() if name_el else ""
            company_name = company_name.replace("他の店舗", "")
            company_name = " ".join(company_name.split())
            if not company_name:
                return None

            addr_el = await card.query_selector("[class*='place']")
            if not addr_el:
                addr_el = await card.query_selector("[class*='station']")
            address = (await addr_el.inner_text()).strip() if addr_el else "東京都"

            if not is_tokyo_23ward(address):
                address = f"東京都 {address}"

            phone = ""
            phone_el = await card.query_selector("a[href^='tel:']")
            if phone_el:
                href = await phone_el.get_attribute("href")
                phone = href.replace("tel:", "").strip() if href else ""

            return Lead(
                company_name=company_name,
                address=address,
                phone=phone,
                industry=industry,
                source_site="マイナビバイト",
                source_url=source_url,
                job_text=" ".join((await card.inner_text()).split())[:400],
                collected_at=datetime.now().isoformat(),
            )
        except Exception as e:
            logger.debug(f"[マイナビバイト] カード解析エラー: {e}")
            return None
