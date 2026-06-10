#!/usr/bin/env python3
"""
URLパターン調査用デバッグスクリプト
各サイトの正しいURL・セレクタを確認する
"""
import asyncio
import glob as _glob
import logging
import os

from playwright.async_api import async_playwright

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

HEADLESS = os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() != "false"


async def fetch(context, url: str, wait: str = "domcontentloaded", timeout: int = 30000):
    page = await context.new_page()
    try:
        resp = await page.goto(url, wait_until=wait, timeout=timeout)
        status = resp.status if resp else "?"
        title = await page.title()
        content = await page.content()
        return status, title, content
    except Exception as e:
        return "ERR", str(e), ""
    finally:
        await page.close()


async def main():
    candidates = _glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")
    executable = candidates[0] if candidates else None

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS,
            executable_path=executable,
            args=["--no-sandbox", "--disable-setuid-sandbox",
                  "--disable-blink-features=AutomationControlled"],
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

        # ===== 求人ボックス =====
        logger.info("===== 求人ボックス (kyujin-box.com) =====")
        kyujin_urls = [
            "https://kyujin-box.com/jobs?q=%E8%AD%A6%E5%82%99&l=%E6%9D%B1%E4%BA%AC%E9%83%BD",  # 警備 東京都
            "https://kyujin-box.com/jobs?q=%E9%81%8B%E8%BC%B8&l=%E6%9D%B1%E4%BA%AC%E9%83%BD",  # 運輸 東京都
            "https://kyujin-box.com/jobs?q=%E9%A3%B2%E9%A3%9F&l=%E6%9D%B1%E4%BA%AC%E9%83%BD",  # 飲食 東京都
            "https://kyujin-box.com/jobs?q=警備&l=東京都",
            "https://kyujin-box.com/",
        ]
        for url in kyujin_urls:
            status, title, html = await fetch(context, url)
            logger.info(f"[kyujin] {status} | {title[:60]} | {url}")
            if html and status != "ERR":
                # セレクタ候補を確認
                page = await context.new_page()
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    # 求人カードのセレクタを探す
                    selectors = [
                        ".result-item", ".job-list-item", ".job-item",
                        "article", ".c-result-item", "[class*='result-item']",
                        ".Box", "li.item", ".list-item",
                    ]
                    for sel in selectors:
                        els = await page.query_selector_all(sel)
                        if els:
                            logger.info(f"  セレクタ '{sel}': {len(els)}件")
                            # 最初の要素のテキストを確認
                            txt = await els[0].inner_text()
                            logger.info(f"  最初の要素: {txt[:100]}")
                            break

                    # 会社名・住所っぽい要素を探す
                    for sel in [".company", ".corp-name", ".job-company",
                                "[class*='company']", "[class*='corp']"]:
                        els = await page.query_selector_all(sel)
                        if els:
                            txt = await els[0].inner_text()
                            logger.info(f"  会社名候補 '{sel}': {txt[:60]}")
                            break

                except Exception as e:
                    logger.error(f"  詳細取得エラー: {e}")
                finally:
                    await page.close()
            # Save HTML
            if html:
                fname = f"debug_kyujin_{url[-20:].replace('/', '_').replace('?','_').replace('&','_')}.html"
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(html[:50000])
                logger.info(f"  HTML保存: {fname} ({len(html)}bytes)")

        # ===== マイナビバイト =====
        logger.info("===== マイナビバイト =====")
        mynavi_urls = [
            "https://baito.mynavi.jp/list/?kw=%E8%AD%A6%E5%82%99&area%5B%5D=130000&p=1",
            "https://baito.mynavi.jp/list/?kw=警備&area[]=130000",
            "https://baito.mynavi.jp/cond/area-13/",
            "https://baito.mynavi.jp/cond/area-13/job-06001/",  # 警備
            "https://baito.mynavi.jp/list-all/pref13/",
            "https://baito.mynavi.jp/search/?kw=警備&pref=13",
            "https://baito.mynavi.jp/",
        ]
        for url in mynavi_urls:
            status, title, html = await fetch(context, url)
            logger.info(f"[mynavi] {status} | {title[:60]} | {url}")
            if html and status not in ("ERR", 404):
                # 求人カードセレクタ
                page = await context.new_page()
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    selectors = [
                        ".p-joblist-item", ".job-list__item", ".p-job-list__item",
                        "article", ".jobInfo", ".job_unit", "li.item",
                        "[class*='job-list']", "[class*='jobList']",
                    ]
                    for sel in selectors:
                        els = await page.query_selector_all(sel)
                        if els:
                            logger.info(f"  セレクタ '{sel}': {len(els)}件")
                            txt = await els[0].inner_text()
                            logger.info(f"  最初: {txt[:100]}")
                            break
                except Exception as e:
                    logger.error(f"  詳細取得エラー: {e}")
                finally:
                    await page.close()
            if html:
                fname = f"debug_mynavi_{url[-25:].replace('/', '_').replace('?','_').replace('&','_').replace('[','_').replace(']','_')}.html"
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(html[:50000])
                logger.info(f"  HTML保存: {fname} ({len(html)}bytes)")

        # ===== enゲージ =====
        logger.info("===== enゲージ =====")
        engage_urls = [
            "https://en-gage.net/user/search/?searchKey=警備&pref=13",
            "https://en-gage.net/user/search/?searchKey=警備&prefecture=13",
            "https://en-gage.net/company/search/?keyword=警備&prefecture=13",
            "https://en-gage.net/company/?area=13&industry=301",
            "https://en-gage.net/",
        ]
        for url in engage_urls:
            # domcontentloaded を使う（networkidle はタイムアウトするため）
            status, title, html = await fetch(context, url, wait="domcontentloaded", timeout=30000)
            logger.info(f"[engage] {status} | {title[:60]} | {url}")
            if html and status not in ("ERR", 404):
                page = await context.new_page()
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(3)  # JS描画待ち
                    selectors = [
                        ".company-list__item", ".company-card",
                        "[class*='CompanyItem']", "[class*='company-list']",
                        "article", ".card", "li.list__item",
                        "[class*='companyCard']",
                    ]
                    for sel in selectors:
                        els = await page.query_selector_all(sel)
                        if els:
                            logger.info(f"  セレクタ '{sel}': {len(els)}件")
                            txt = await els[0].inner_text()
                            logger.info(f"  最初: {txt[:100]}")
                            break
                    content = await page.content()
                    # 件数表示を確認
                    import re
                    m = re.search(r'(\d+)社?件', content)
                    if m:
                        logger.info(f"  件数表示: {m.group(0)}")
                except Exception as e:
                    logger.error(f"  詳細取得エラー: {e}")
                finally:
                    await page.close()
            if html:
                fname = f"debug_engage_{url[-25:].replace('/', '_').replace('?','_').replace('&','_').replace('=','_')}.html"
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(html[:50000])
                logger.info(f"  HTML保存: {fname} ({len(html)}bytes)")

        await context.close()
        await browser.close()

    logger.info("===== 調査完了 =====")


if __name__ == "__main__":
    asyncio.run(main())
