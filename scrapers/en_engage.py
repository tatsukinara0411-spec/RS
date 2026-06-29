import asyncio
import logging
from datetime import datetime

from playwright.async_api import BrowserContext

from models.lead import Lead
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

INDUSTRY_KEYWORDS = {
    "警備": "警備",
    "運輸": "運輸",
    "外食": "飲食",
    "販売": "販売",
    "介護": "介護",
    "建設": "建設",
}

BASE_URL = "https://en-gage.net"


class EnEngageScraper(BaseScraper):
    site_name = "enゲージ"

    async def scrape_industry(self, context: BrowserContext, industry: str) -> list[Lead]:
        leads: list[Lead] = []
        keyword = INDUSTRY_KEYWORDS.get(industry, industry)

        for page_no in range(1, 21):
            if len(leads) >= self.per_industry:
                break

            if page_no == 1:
                url = f"{BASE_URL}/user/search/?searchKey={keyword}&pref=13"
            else:
                url = f"{BASE_URL}/user/search/?searchKey={keyword}&pref=13&page={page_no}"

            page = await context.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(10)  # SPA描画を十分待つ

                # 結果件数ログ
                count_text = await page.evaluate(
                    "() => { const s = document.querySelector('section'); return s ? s.innerText.substring(0,100) : ''; }"
                )
                logger.info(f"[enゲージ] section: {count_text[:80]}")

                # 企業カード候補（優先順）
                rows = await page.query_selector_all("li.row.row--company")
                if not rows:
                    rows = await page.query_selector_all("[class*='row--company']")
                if not rows:
                    rows = await page.query_selector_all(".md_card .cardContent")
                if not rows:
                    rows = await page.query_selector_all(".md_card")

                logger.info(f"[enゲージ] カード数: {len(rows)} | {url}")

                if not rows:
                    logger.warning(f"[enゲージ] カードなし: {url}")
                    break

                for row in rows:
                    if len(leads) >= self.per_industry:
                        break
                    lead = await self._parse_row(row, industry, url)
                    if lead:
                        leads.append(lead)

                next_btn = await page.query_selector(f"a[href*='page={page_no + 1}']")
                if not next_btn:
                    break

            except Exception as e:
                logger.error(f"[enゲージ] エラー {url}: {e}")
                break
            finally:
                await page.close()

        return leads

    async def _parse_row(self, row, industry: str, source_url: str) -> Lead | None:
        try:
            company_name = (await row.inner_text()).strip()
            if not company_name or len(company_name) > 80:
                return None
            company_name = company_name.split("\n")[0].strip()
            if not company_name:
                return None

            address = "東京都"
            phone = ""
            phone_el = await row.query_selector("a[href^='tel:']")
            if phone_el:
                href = await phone_el.get_attribute("href")
                phone = href.replace("tel:", "").strip() if href else ""

            return Lead(
                company_name=company_name,
                address=address,
                phone=phone,
                industry=industry,
                source_site="enゲージ",
                source_url=source_url,
                collected_at=datetime.now().isoformat(),
            )
        except Exception as e:
            logger.debug(f"[enゲージ] 行解析エラー: {e}")
            return None
