import asyncio
import logging
from datetime import datetime

from playwright.async_api import BrowserContext

from models.lead import Lead
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://xn--pckua2a7gp15o89zb.com"

INDUSTRY_KEYWORDS = {
    "警備": "警備",
    "運輸": "運輸 ドライバー",
    "外食": "飲食 外食",
}


class KyujinboxScraper(BaseScraper):
    site_name = "求人BOX"

    async def scrape_industry(self, context: BrowserContext, industry: str) -> list[Lead]:
        leads: list[Lead] = []
        keyword = INDUSTRY_KEYWORDS.get(industry, industry)

        for page_no in range(1, 8):
            if len(leads) >= 35:
                break

            if page_no == 1:
                url = f"{BASE_URL}/?q={keyword}&l=東京都"
            else:
                url = f"{BASE_URL}/?q={keyword}&l=東京都&page={page_no}"

            page = await context.new_page()
            try:
                await self.safe_goto(page, url)
                await asyncio.sleep(1)

                cards = await page.query_selector_all("[class*='result-item'], [class*='job-item'], [class*='ResultItem']")
                if not cards:
                    cards = await page.query_selector_all("article")

                if not cards:
                    logger.warning(f"[求人BOX] カードなし: {url}")
                    break

                for card in cards:
                    if len(leads) >= 35:
                        break
                    lead = await self._parse_card(card, industry, url)
                    if lead:
                        leads.append(lead)

                next_btn = await page.query_selector(f"a[href*='page={page_no + 1}'], .pagination a[rel='next']")
                if not next_btn:
                    break

            except Exception as e:
                logger.error(f"[求人BOX] エラー {url}: {e}")
                break
            finally:
                await page.close()

        return leads

    async def _parse_card(self, card, industry: str, source_url: str) -> Lead | None:
        try:
            name_el = await card.query_selector(
                "[class*='company'], [class*='corp'], [class*='employer'], .company-name"
            )
            company_name = (await name_el.inner_text()).strip() if name_el else ""
            if not company_name:
                h_el = await card.query_selector("h2, h3")
                if h_el:
                    company_name = (await h_el.inner_text()).strip()
            if not company_name:
                return None

            addr_el = await card.query_selector(
                "[class*='location'], [class*='address'], [class*='place'], [class*='area']"
            )
            address = (await addr_el.inner_text()).strip() if addr_el else "東京都"
            if not address:
                address = "東京都"

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
                source_site="求人BOX",
                source_url=source_url,
                collected_at=datetime.now().isoformat(),
            )
        except Exception as e:
            logger.debug(f"[求人BOX] カード解析エラー: {e}")
            return None
