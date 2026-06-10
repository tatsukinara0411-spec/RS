import asyncio
import logging
from datetime import datetime

from playwright.async_api import BrowserContext as Browser

from models.lead import Lead
from scrapers.base import BaseScraper
from utils.fingerprint import is_tokyo_23ward
from utils.rate_limiter import polite_delay

logger = logging.getLogger(__name__)

# マイナビバイト 業種キーワード（検索ボックス使用）
INDUSTRY_KEYWORDS = {
    "警備": "警備",
    "運輸": "運輸 ドライバー",
    "外食": "飲食 外食",
}

BASE_URL = "https://baito.mynavi.jp"


class MynaviBaitoScraper(BaseScraper):
    site_name = "マイナビバイト"

    async def scrape_industry(self, browser: Browser, industry: str) -> list[Lead]:
        leads: list[Lead] = []
        keyword = INDUSTRY_KEYWORDS.get(industry, industry)

        for page_num in range(1, 10):
            if len(leads) >= 35:
                break

            # エリア: 東京都23区 area=13001xx 系 または keyword検索
            url = (
                f"{BASE_URL}/list/"
                f"?kw={keyword.replace(' ', '+')}"
                f"&area%5B%5D=130000"  # 東京都
                f"&p={page_num}"
            )
            page = await browser.new_page()
            try:
                await self.safe_goto(page, url, timeout=45000)

                # 求人カード
                cards = await page.query_selector_all(
                    ".job-list__item, .p-job-list__item, [class*='joblist'] li, .search-result-item"
                )

                if not cards:
                    logger.warning(f"[マイナビバイト] カードが見つかりません: {url}")
                    break

                for card in cards:
                    if len(leads) >= 35:
                        break
                    lead = await self._parse_card(card, industry, url)
                    if lead:
                        leads.append(lead)

                # 次ページ確認
                next_btn = await page.query_selector("a.pagination__next, .next a, [class*='next']")
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
            # 会社名
            name_el = await card.query_selector(
                ".company-name, .p-job-list__company, [class*='company'], .shop-name"
            )
            company_name = (await name_el.inner_text()).strip() if name_el else ""

            # 住所・勤務地
            addr_el = await card.query_selector(
                ".work-place, .p-job-list__place, [class*='place'], [class*='location'], .address"
            )
            address = (await addr_el.inner_text()).strip() if addr_el else ""

            # 東京23区フィルタ
            if not is_tokyo_23ward(address) or not company_name:
                return None

            # 電話番号（通常は非表示）
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
                collected_at=datetime.now().isoformat(),
            )
        except Exception as e:
            logger.debug(f"[マイナビバイト] カード解析エラー: {e}")
            return None
