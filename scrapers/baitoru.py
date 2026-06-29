import logging
import re
from datetime import datetime

from playwright.async_api import BrowserContext

from models.lead import Lead
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://www.baitoru.com"

INDUSTRY_KEYWORDS = {
    "警備": "警備",
    "運輸": "ドライバー",
    "外食": "飲食",
    "販売": "販売",
    "介護": "介護",
    "建設": "建設",
}

PHONE_RE = re.compile(r"0\d{1,4}-\d{1,4}-\d{3,4}")


class BaitoruScraper(BaseScraper):
    site_name = "バイトル"

    async def scrape_industry(self, context: BrowserContext, industry: str) -> list[Lead]:
        leads: list[Lead] = []
        keyword = INDUSTRY_KEYWORDS.get(industry, industry)

        for page_no in range(1, 21):
            if len(leads) >= self.per_industry:
                break

            if page_no == 1:
                url = f"{BASE_URL}/tokyo/kensakuWord/{keyword}/"
            else:
                url = f"{BASE_URL}/tokyo/kensakuWord/{keyword}/?pg={page_no}"

            page = await context.new_page()
            try:
                await self.safe_goto(page, url)

                cards = await page.query_selector_all(".item-list__item")
                if not cards:
                    cards = await page.query_selector_all(".js-select-item")
                if not cards:
                    cards = await page.query_selector_all("[class*='job-item']")
                if not cards:
                    cards = await page.query_selector_all("article")

                if not cards:
                    logger.warning(f"[バイトル] カードなし: {url}")
                    break

                logger.info(f"[バイトル] {industry} p{page_no}: {len(cards)}件")

                for card in cards:
                    if len(leads) >= self.per_industry:
                        break
                    lead = await self._parse_card(card, industry, url)
                    if lead:
                        leads.append(lead)

                next_btn = await page.query_selector(f"a[href*='pg={page_no + 1}']")
                if not next_btn:
                    next_btn = await page.query_selector(".pagination__next:not([aria-disabled])")
                if not next_btn:
                    break

            except Exception as e:
                logger.error(f"[バイトル] エラー {url}: {e}")
                break
            finally:
                await page.close()

        return leads

    async def _parse_card(self, card, industry: str, source_url: str) -> Lead | None:
        try:
            text = await card.inner_text()
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if not lines:
                return None

            company_name = ""
            corp_keywords = ["株式会社", "有限会社", "合同会社", "一般社団", "医療法人", "社会福祉"]
            for line in lines:
                if any(k in line for k in corp_keywords):
                    company_name = line
                    break
            if not company_name:
                for line in lines[1:4]:
                    if 2 <= len(line) <= 60 and "円" not in line and "時" not in line:
                        company_name = line
                        break

            if not company_name:
                return None

            address = next((l for l in lines if l.startswith("東京都")), "東京都")
            address = address.split("　")[0].split(" ")[0][:80]

            phone = ""
            phone_el = await card.query_selector("a[href^='tel:']")
            if phone_el:
                href = await phone_el.get_attribute("href")
                phone = href.replace("tel:", "").strip() if href else ""
            if not phone:
                m = PHONE_RE.search(text)
                if m:
                    phone = m.group(0)

            return Lead(
                company_name=company_name,
                address=address,
                phone=phone,
                industry=industry,
                source_site="バイトル",
                source_url=source_url,
                collected_at=datetime.now().isoformat(),
            )
        except Exception as e:
            logger.debug(f"[バイトル] カード解析エラー: {e}")
            return None
