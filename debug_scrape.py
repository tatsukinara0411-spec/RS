#!/usr/bin/env python3
"""
URLパターン調査 v2
- enゲージ: 正しいURL確認済み、HTML構造調査
- 求人ボックス: 正しいパス調査
- マイナビバイト: ホームページHTMLからURL構造解析
"""
import asyncio
import glob as _glob
import logging
import os
import re

from playwright.async_api import async_playwright

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

HEADLESS = os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() != "false"


async def get_page(context, url, wait="domcontentloaded", sleep_sec=0, timeout=30000):
    page = await context.new_page()
    try:
        resp = await page.goto(url, wait_until=wait, timeout=timeout)
        status = resp.status if resp else "?"
        if sleep_sec:
            await asyncio.sleep(sleep_sec)
        title = await page.title()
        html = await page.content()
        return page, status, title, html
    except Exception as e:
        await page.close()
        return None, "ERR", str(e), ""


def save_html(name, html):
    safe = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
    fname = f"debug_{safe}.html"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(html[:100000])
    logger.info(f"  HTML保存: {fname} ({len(html)}bytes)")
    return fname


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

        # ===== enゲージ: HTML構造調査 =====
        logger.info("===== enゲージ HTML構造調査 =====")
        url = "https://en-gage.net/user/search/?searchKey=%E8%AD%A6%E5%82%99&pref=13"
        page, status, title, html = await get_page(context, url, sleep_sec=4)
        logger.info(f"  {status} | {title[:60]}")
        if page:
            # 全セレクタ調査
            for sel in [
                ".company-list__item", ".company-card", ".company-item",
                "[class*='CompanyItem']", "[class*='companyItem']",
                "[class*='company-list']", "[class*='companyList']",
                "[class*='Company']", "[class*='SearchResult']",
                "[class*='result']", "[class*='Result']",
                "article", ".card", "li.list__item", "ul li",
                "[class*='Card']", "[class*='Item']",
            ]:
                els = await page.query_selector_all(sel)
                if els and 2 < len(els) < 200:
                    txt = await els[0].inner_text()
                    logger.info(f"  セレクタ '{sel}': {len(els)}件 | 最初: {txt[:100]}")
            # 件数を確認
            m = re.search(r'[\d,]+\s*社', html)
            if m:
                logger.info(f"  件数: {m.group(0)}")
            # HTML先頤65000字を印刺して構造確認
            logger.info(f"  HTML先頤65000: {html[:500]}")
            await page.close()
        save_html("engage_user_search_keibii", html)

        # 遷移先URLも調査
        url2 = "https://en-gage.net/user/search/?searchKey=%E9%81%8B%E8%BC%B8&pref=13"
        page2, status2, title2, html2 = await get_page(context, url2, sleep_sec=4)
        logger.info(f"  運輸: {status2} | {len(html2)}bytes")
        if page2:
            for sel in ["[class*='Item']", "[class*='Card']", "article", "ul li"]:
                els = await page2.query_selector_all(sel)
                if els and 2 < len(els) < 200:
                    txt = await els[0].inner_text()
                    logger.info(f"  '{sel}': {len(els)}件 | {txt[:100]}")
                    break
            await page2.close()
        save_html("engage_user_search_unsou", html2)

        # ===== 求人ボックス: 正しいパス調査 =====
        logger.info("===== 求人ボックス URL調査 =====")
        kyujin_urls = [
            "https://kyujin-box.com/",
            "https://kyujin-box.com/jobs/search?q=%E8%AD%A6%E5%82%99&l=%E6%9D%B1%E4%BA%AC%E9%83%BD",
            "https://kyujin-box.com/search?q=%E8%AD%A6%E5%82%99&l=%E6%9D%B1%E4%BA%AC%E9%83%BD",
            "https://kyujin-box.com/job/?q=%E8%AD%A6%E5%82%99&l=%E6%9D%B1%E4%BA%AC%E9%83%BD",
            "https://kyujin-box.com/jobs/?q=%E8%AD%A6%E5%82%99&l=%E6%9D%B1%E4%BA%AC%E9%83%BD",
        ]
        for url in kyujin_urls:
            page, status, title, html = await get_page(context, url, sleep_sec=2)
            logger.info(f"  {status} | {title[:70]} | {url[-50:]}")
            if page:
                # リンクを収集して正しいURL候補を探す
                links = await page.query_selector_all("a[href*='job'], a[href*='search'], a[href*='find']")
                for link in links[:10]:
                    href = await link.get_attribute("href")
                    txt = (await link.inner_text()).strip()[:40]
                    if href:
                        logger.info(f"    リンク: {href} | {txt}")
                await page.close()
            safe_name = f"kyujin_{url[-40:].replace('/', '_').replace('?', '_').replace('&', '_').replace('=', '_').replace('%', '_').replace(':', '_')}"
            save_html(safe_name, html)

        # ===== マイナビバイト: ホームページから検索URLを找す =====
        logger.info("===== マイナビバイト URL調査 =====")
        mynavi_urls = [
            "https://baito.mynavi.jp/",
            "https://baito.mynavi.jp/pref13/",
            "https://baito.mynavi.jp/tokyo/",
            "https://baito.mynavi.jp/list/?keyword=%E8%AD%A6%E5%82%99&pref_code=13",
            "https://baito.mynavi.jp/list/?keyword=%E8%AD%A6%E5%82%99&area=13",
            "https://baito.mynavi.jp/list/?keyword=%E8%AD%A6%E5%82%99",
        ]
        for url in mynavi_urls:
            page, status, title, html = await get_page(context, url, sleep_sec=2)
            logger.info(f"  {status} | {title[:60]} | {url}")
            if page and status == 200:
                # 検索フォームや求人カードを調査
                for sel in [
                    "form", "input[name*='kw']", "input[name*='keyword']",
                    "input[name*='word']", "a[href*='/list/']",
                ]:
                    els = await page.query_selector_all(sel)
                    if els:
                        for el in els[:3]:
                            tag = await el.get_attribute("name") or await el.get_attribute("action") or await el.get_attribute("href") or ""
                            logger.info(f"  '{sel}' 候補: {tag[:80]}")
                        break
                await page.close()
            safe_name = f"mynavi_{url[-50:].replace('/', '_').replace('?', '_').replace('&', '_').replace('=', '_').replace('%', '_').replace(':', '_')}"
            save_html(safe_name, html)

        await context.close()
        await browser.close()

    logger.info("===== 調査完了 =====")


if __name__ == "__main__":
    asyncio.run(main())
