import asyncio
import logging
import re
from datetime import datetime

from playwright.async_api import BrowserContext as Browser

from models.lead import Lead
from scrapers.base import BaseScraper
from utils.fingerprint import is_tokyo_23ward

logger = logging.getLogger(__name__)

# 求人BOX 業種コード (URLパラメータ調査値)
INDUSTRY_PARAMS = {
    "警備": "警備",
    "運輸": "運輸・交通・物流・倉庫",
    "外食": "外食・フード",
}

BASE_URL = "https://kyujinbox.com"


class KyujinboxScraper(BaseScraper):
    site_name = "求人BOX"

    async def scrape_industry(self, browser: Browser, industry: str) -> list[Lead]:
        leads: list[Lead] = []
        keyword = INDUSTRY_PARAMS.get(industry, industry)

        for page_num in range(1, 10):
            if len(leads) >= 35:
                break

            url = (
                f"{BASE_URL}/jobs?location=東京都&job={keyword}&page={page_num}"
            )
            page = await browser.new_page()
            try:
                await self.safe_goto(page, url)

                # 求人カード一覧を取得
                cards = await page.query_selector_all(".result-item, .job-list-item, [class*='result']")

                if not cards:
                    # セレクタが変わった場合のフォールバック
                    content = await page.content()
                    if "件が見つかりました" not in content and "の求人" not in content:
                        logger.warning(f"[求人BOX] ページに求人が見つかりません: {url}")
                        break

                for card in cards:
                    if len(leads) >= 35:
                        break
                    lead = await self._parse_card(card, industry, url)
                    if lead:
                        leads.append(lead)

            except Exception as e:
                logger.error(f"[求人BOX] ページ取得エラー {url}: {e}")
            finally:
                await page.close()

        return leads

    async def _parse_card(self, card, industry: str, source_url: str) -> Lead | None:
        try:
            # 会社名
            name_el = await card.query_selector(".job-name, .company-name, h2, h3, .name")
            company_name = (await name_el.inner_text()).strip() if name_el else ""

            # 住所
            addr_el = await card.query_selector(".job-detail-location, .address, .location, [class*='location']")
            address = (await addr_el.inner_text()).strip() if addr_el else ""

            # 東京23区フィルタ
            if not address or not is_tokyo_23ward(address):
                return None

            if not company_name:
                return None

            # 電話番号（求人サイトでは非表示が多い）
            phone = ""
            phone_el = await card.query_selector("a[href^='tel:'], .tel, .phone")
            if phone_el:
                href = await phone_el.get_attribute("href")
                if href and href.startswith("tel:"):
                    phone = href.replace("tel:", "").strip()
                else:
                    phone = (await phone_el.inner_text()).strip()

            return Lead(
                company_name=company_name,
                address=address,
                phone=phone,
                industry=industry,
                source_site="求人BOX",
                source_url=source_url,
                collected_at=datetime.now().isoformat(),
            )
        except Exception as e:
            logger.debug(f"[求人BOX] カード解析エラー: {e}")
            return None
