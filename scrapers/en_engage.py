import asyncio
import logging
from datetime import datetime

from playwright.async_api import BrowserContext as Browser

from models.lead import Lead
from scrapers.base import BaseScraper
from utils.fingerprint import is_tokyo_23ward

logger = logging.getLogger(__name__)

# enゲージ 業種キーワード
INDUSTRY_KEYWORDS = {
    "警備": "警備",
    "運輸": "運輸・物流",
    "外食": "飲食・外食",
}

BASE_URL = "https://en-gage.net"


class EnEngageScraper(BaseScraper):
    site_name = "enゲージ"

    async def scrape_industry(self, browser: Browser, industry: str) -> list[Lead]:
        leads: list[Lead] = []
        keyword = INDUSTRY_KEYWORDS.get(industry, industry)

        for page_num in range(1, 10):
            if len(leads) >= 35:
                break

            url = (
                f"{BASE_URL}/company/search/"
                f"?keyword={keyword.replace(' ', '+')}"
                f"&prefecture=東京都"
                f"&page={page_num}"
            )
            page = await browser.new_page()
            try:
                # React SPA のため networkidle 待機
                await page.goto(url, wait_until="networkidle", timeout=45000)

                # 企業カード
                cards = await page.query_selector_all(
                    ".company-list__item, [class*='companyList'] li, .company-card, [class*='company-item']"
                )

                if not cards:
                    # 別のセレクタを試す
                    cards = await page.query_selector_all("article, .card, [data-company]")

                if not cards:
                    logger.warning(f"[enゲージ] カードが見つかりません: {url}")
                    break

                for card in cards:
                    if len(leads) >= 35:
                        break
                    lead = await self._parse_card(card, industry, url)
                    if lead:
                        leads.append(lead)

            except Exception as e:
                logger.error(f"[enゲージ] エラー {url}: {e}")
                break
            finally:
                await page.close()

        return leads

    async def _parse_card(self, card, industry: str, source_url: str) -> Lead | None:
        try:
            # 会社名
            name_el = await card.query_selector(
                ".company-name, h2, h3, [class*='companyName'], [class*='company-name']"
            )
            company_name = (await name_el.inner_text()).strip() if name_el else ""

            # 住所
            addr_el = await card.query_selector(
                ".address, .location, [class*='address'], [class*='location'], .prefecture"
            )
            address = (await addr_el.inner_text()).strip() if addr_el else ""

            # enゲージの住所は都道府県のみの場合あり → 東京都を含む
            if "東京" not in address or not company_name:
                return None

            # 電話番号
            phone = ""
            phone_el = await card.query_selector("a[href^='tel:'], .tel, .phone, [class*='tel']")
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
                source_site="enゲージ",
                source_url=source_url,
                collected_at=datetime.now().isoformat(),
            )
        except Exception as e:
            logger.debug(f"[enゲージ] カード解析エラー: {e}")
            return None
