from abc import ABC, abstractmethod
import asyncio
import logging
from typing import Optional

from playwright.async_api import Page, Browser, BrowserContext

from models.lead import Lead
from utils.rate_limiter import polite_delay

logger = logging.getLogger(__name__)

INDUSTRIES = ["警備", "運輸", "外食"]
TARGET_COUNT = 200


class BaseScraper(ABC):
    site_name: str = ""

    def __init__(self, semaphore: asyncio.Semaphore):
        self.semaphore = semaphore
        self.per_industry = TARGET_COUNT // len(INDUSTRIES)

    @abstractmethod
    async def scrape_industry(self, context: BrowserContext, industry: str) -> list[Lead]:
        ...

    async def enrich(self, context: BrowserContext, leads: list[Lead]) -> None:
        """詳細ページから電話番号・住所を補完する(対応サイトのみ上書き実装)"""
        return

    async def scrape(self, context: BrowserContext) -> list[Lead]:
        all_leads: list[Lead] = []

        for industry in INDUSTRIES:
            try:
                logger.info(f"[{self.site_name}] {industry} スクレイピング開始")
                leads = await self.scrape_industry(context, industry)
                leads = leads[:self.per_industry]
                all_leads.extend(leads)
                logger.info(f"[{self.site_name}] {industry}: {len(leads)}件取得")
            except Exception as e:
                logger.error(f"[{self.site_name}] {industry} でエラー: {e}")

        return all_leads[:TARGET_COUNT]

    async def safe_goto(self, page: Page, url: str, timeout: int = 30000):
        async with self.semaphore:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            await polite_delay()
