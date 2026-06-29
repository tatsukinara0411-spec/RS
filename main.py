#!/usr/bin/env python3
"""
テレアポリード自動収集システム
毎週月曜日のGitHub Actionsで実行される。
"""
import asyncio
import argparse
import logging
import os
import sys

from playwright.async_api import async_playwright

from scrapers.mynavi_baito import MynaviBaitoScraper
from scrapers.en_engage import EnEngageScraper
from scrapers.kyujinbox import KyujinboxScraper
from scrapers.baitoru import BaitoruScraper
from storage.database import init_db, deduplicate, mark_seen_pair
from storage.sheets import write_leads
from models.lead import Lead
from utils.credentials import load_service_account_info, CredentialsError
from utils.places import enrich_with_places
from utils.corporate_number import enrich_with_corporate_numbers

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def run_scrape(dry_run: bool = False):
    logger.info("=== テレアポリード収集 開始 ===")

    if not dry_run and os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON") is not None:
        load_service_account_info(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

    init_db()

    semaphore = asyncio.Semaphore(int(os.environ.get("SCRAPE_CONCURRENCY", "2")))

    scrapers = [
        MynaviBaitoScraper(semaphore),
        EnEngageScraper(semaphore),
        KyujinboxScraper(semaphore),
        BaitoruScraper(semaphore),
    ]

    headless = os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() != "false"

    async with async_playwright() as p:
        import glob as _glob
        candidates = _glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")
        executable = candidates[0] if candidates else None

        browser = await p.chromium.launch(
            headless=headless,
            executable_path=executable,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        context = await browser.new_context(
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )

        tasks = [scraper.scrape(context) for scraper in scrapers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_leads: list[Lead] = []
        site_names = ["マイナビバイト", "enゲージ", "求人BOX", "バイトル"]
        for site, result in zip(site_names, results):
            if isinstance(result, Exception):
                logger.error(f"[{site}] スクレイピング失敗: {result}")
            else:
                logger.info(f"[{site}] 取得: {len(result)}件")
                all_leads.extend(result)

        unique_leads = deduplicate(all_leads)
        logger.info(f"重複除外後: {len(unique_leads)}件 (元: {len(all_leads)}件)")

        dedup_keys = [(l.company_name, l.address, l.collected_at, l.source_site) for l in unique_leads]

        for scraper in scrapers:
            site_leads = [l for l in unique_leads if l.source_site == scraper.site_name]
            if site_leads:
                try:
                    await scraper.enrich(context, site_leads)
                except Exception as e:
                    logger.error(f"[{scraper.site_name}] 詳細補完でエラー: {e}")

        await context.close()
        await browser.close()

    await enrich_with_places(unique_leads)
    await enrich_with_corporate_numbers(unique_leads)

    url = write_leads(unique_leads, dry_run=dry_run)

    if not dry_run:
        for name, addr, collected_at, source_site in dedup_keys:
            mark_seen_pair(name, addr, collected_at, source_site)

    logger.info(f"=== 完了: {len(unique_leads)}件を書き込みました ===")
    if url and url != "dry_run":
        logger.info(f"スプレッドシート: {url}")

    return len(unique_leads)


def main():
    parser = argparse.ArgumentParser(description="テレアポリード自動収集")
    parser.add_argument("--dry-run", action="store_true", help="Sheetsへの書き込みをスキップ")
    parser.add_argument("--run-now", action="store_true", help="即時実行")
    args = parser.parse_args()

    try:
        count = asyncio.run(run_scrape(dry_run=args.dry_run))
    except CredentialsError as err:
        print(f"\n❌ Google認証情報エラー\n\n{err}\n", file=sys.stderr)
        sys.exit(1)
    sys.exit(0 if count >= 0 else 1)


if __name__ == "__main__":
    main()
