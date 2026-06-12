import logging
from datetime import datetime

from playwright.async_api import BrowserContext

from models.lead import Lead
from scrapers.base import BaseScraper
from utils.fingerprint import is_tokyo_23ward

logger = logging.getLogger(__name__)

INDUSTRY_PATHS = {
    "警備": "keibi",
    "運輸": "unso",
    "外食": "gaishoku",
}

BASE_URL = "https://baito.mynavi.jp"


class MynaviBaitoScraper(BaseScraper):
    site_name = "マイナビバイト"

    async def scrape_industry(self, context: BrowserContext, industry: str) -> list[Lead]:
        leads: list[Lead] = []
        path = INDUSTRY_PATHS.get(industry, industry)

        for page_no in range(1, 12):
            if len(leads) >= self.per_industry:
                break

            if page_no == 1:
                url = f"{BASE_URL}/tokyo/{path}/"
            else:
                url = f"{BASE_URL}/tokyo/{path}/?pageNo={page_no}"

            page = await context.new_page()
            try:
                await self.safe_goto(page, url)

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
            name_el = await card.query_selector(".shopNameWrap")
            company_name = (await name_el.inner_text()).strip() if name_el else ""
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
                collected_at=datetime.now().isoformat(),
            )
        except Exception as e:
            logger.debug(f"[マイナビバイト] カード解析エラー: {e}")
            return None
