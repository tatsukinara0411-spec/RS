import asyncio
import logging
import re
from datetime import datetime

from playwright.async_api import BrowserContext

from models.lead import Lead
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://xn--pckua2a7gp15o89zb.com"

INDUSTRY_KEYWORDS = {
    "警備": "警備",
    "運輸": "ドライバー",
    "外食": "飲食",
    "販売": "販売",
    "介護": "介護",
    "建設": "建設",
}

LABELED_PHONE_RE = re.compile(r"(?:TEL|ＴＥＬ|電話番号|電話)[：:]?\s*(0\d{1,4}-\d{1,4}-\d{3,4})")
UAID_RE = re.compile(r"[?&]uaid=([0-9a-z]+)")


class KyujinboxScraper(BaseScraper):
    site_name = "求人BOX"

    async def scrape_industry(self, context: BrowserContext, industry: str) -> list[Lead]:
        leads: list[Lead] = []
        keyword = INDUSTRY_KEYWORDS.get(industry, industry)

        for page_no in range(1, 21):
            if len(leads) >= self.per_industry:
                break

            url = f"{BASE_URL}/{keyword}の仕事-東京都"
            if page_no > 1:
                url += f"?pg={page_no}"

            page = await context.new_page()
            try:
                await self.safe_goto(page, url)
                await asyncio.sleep(2)

                cards = await page.query_selector_all(".p-result_card")
                if not cards:
                    logger.warning(f"[求人BOX] 検索結果カードなし: {url}")
                    break

                for card in cards:
                    if len(leads) >= self.per_industry:
                        break
                    lead = await self._parse_card(card, industry, url)
                    if lead:
                        leads.append(lead)

                next_btn = await page.query_selector(f"a[href*='pg={page_no + 1}']")
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
            text = await card.inner_text()
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if len(lines) < 2:
                return None

            company_name = lines[1]
            if not company_name or len(company_name) > 60 or "円" in company_name:
                return None

            address = next((l for l in lines if l.startswith("東京都")), "東京都")
            address = address.split(" / ")[0].strip()

            detail_url = ""
            hrefs = await card.eval_on_selector_all(
                "a[href*='uaid=']", "els => els.map(e => e.getAttribute('href'))"
            )
            for h in hrefs:
                m = UAID_RE.search(h or "")
                if m:
                    detail_url = f"{BASE_URL}/jb/{m.group(1)}"
                    break

            return Lead(
                company_name=company_name,
                address=address,
                phone="",
                industry=industry,
                source_site="求人BOX",
                source_url=source_url,
                detail_url=detail_url,
                collected_at=datetime.now().isoformat(),
            )
        except Exception as e:
            logger.debug(f"[求人BOX] カード解析エラー: {e}")
            return None

    async def enrich(self, context: BrowserContext, leads: list[Lead]) -> None:
        targets = [l for l in leads if l.detail_url]
        logger.info(f"[求人BOX] 詳細ページ補完開始: {len(targets)}件")
        done = 0
        found_phone = 0

        for lead in targets:
            page = await context.new_page()
            try:
                await page.goto(lead.detail_url, wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(1.5)
                body = await page.evaluate("() => document.body.innerText")

                m = LABELED_PHONE_RE.search(body)
                if m:
                    lead.phone = m.group(1)
                    found_phone += 1

                full_addr = await self._extract_address(page)
                if full_addr:
                    lead.address = full_addr
            except Exception as e:
                logger.debug(f"[求人BOX] 詳細補完エラー {lead.detail_url}: {e}")
            finally:
                await page.close()

            done += 1
            if done % 20 == 0:
                logger.info(f"[求人BOX] 詳細ページ補完 {done}/{len(targets)}件 (電話番号 {found_phone}件)")

        logger.info(f"[求人BOX] 詳細ページ補完完了: {done}件中 電話番号 {found_phone}件")

    async def _extract_address(self, page) -> str:
        try:
            addr = await page.evaluate(
                """() => {
                    for (const dt of document.querySelectorAll('dt')) {
                        if (!dt.innerText.includes('勤務地')) continue;
                        const dd = dt.nextElementSibling;
                        if (!dd) continue;
                        for (const line of dd.innerText.split('\\n')) {
                            const t = line.trim();
                            if (t.startsWith('東京都') && /\\d/.test(t)) return t.slice(0, 100);
                        }
                        for (const line of dd.innerText.split('\\n')) {
                            const t = line.trim();
                            if (t.startsWith('東京都')) return t.slice(0, 100);
                        }
                    }
                    return '';
                }"""
            )
            return (addr or "").strip()
        except Exception:
            return ""
