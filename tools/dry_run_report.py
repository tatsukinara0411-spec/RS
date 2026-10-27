#!/usr/bin/env python3
"""
修正確認用の試運転（シートには書き込まない・Googleマップも使わない）。
マイナビバイトと求人BOXを各業種30件まで取得し、件数・業種・社名・電話番号の様子を注記に出す。
"""
import asyncio, collections, glob, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.async_api import async_playwright
from scrapers.mynavi_baito import MynaviBaitoScraper
from scrapers.kyujinbox import KyujinboxScraper

PER = int(os.environ.get("DRY_PER_INDUSTRY", "30"))


def emit(title, lines):
    msg = "\n".join(lines)[:6000].replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::notice title={title}::{msg}")


async def main():
    async with async_playwright() as p:
        cand = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")
        b = await p.chromium.launch(headless=True, executable_path=cand[0] if cand else None,
                                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        ctx = await b.new_context(locale="ja-JP", timezone_id="Asia/Tokyo", viewport={"width": 1280, "height": 800},
                                  user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        sem = asyncio.Semaphore(3)
        for cls in (MynaviBaitoScraper, KyujinboxScraper):
            s = cls(sem)
            s.per_industry = PER
            leads = await s.scrape(ctx)
            if cls is KyujinboxScraper:
                await s.enrich(ctx, leads[:40])
            ind = collections.Counter(l.industry for l in leads)
            names = collections.Counter(l.company_name for l in leads)
            bad = [l.company_name for l in leads if "他の店舗" in l.company_name or "\n" in l.company_name]
            lines = [f"件数 {len(leads)} / 重複社名の種類 {len(names)}",
                     f"業種内訳 {dict(ind)}",
                     f"社名に余計な文字: {len(bad)}件",
                     f"代表番号(phone) {sum(bool(l.phone) for l in leads)}件 / 求人ページ番号(listing_phone) {sum(bool(l.listing_phone) for l in leads)}件"]
            seen = set()
            for l in leads:
                key = l.industry
                if list(seen).count(key) >= 0 and sum(1 for x in seen if x[0] == key) < 3:
                    seen.add((key, l.company_name))
                    lines.append(f"  [{l.industry}] {l.company_name[:35]} | {l.address[:25]} | {l.listing_phone}")
            emit(f"DRYRUN_{s.site_name}", lines)
        await b.close()

asyncio.run(main())
