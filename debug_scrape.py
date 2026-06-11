#!/usr/bin/env python3
"""
URLパターン調査 v3
- mynavi tokyoページの詳細構造調査
- engageのReact HTML調査
- kyujin-boxのリンク調査
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
        f.write(html)
    logger.info(f"  HTML保存: {fname} ({len(html)}bytes)")


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

        # ===== マイナビバイト: tokyoページの構造調査 =====
        logger.info("===== マイナビバイト /tokyo/ 調査 =====")
        page, status, title, html = await get_page(context, "https://baito.mynavi.jp/tokyo/", sleep_sec=2)
        logger.info(f"  {status} | {title[:60]}")
        if page:
            # 求亿リンク構造を調査
            links = await page.query_selector_all("a[href*='keibii'], a[href*='seikyu'], a[href*='keibi'], a[href*='keigo']")
            logger.info(f"  警備リンク: {len(links)}件")

            # 業種リンクを探す
            all_links = await page.query_selector_all("a[href*='/tokyo/']")
            logger.info(f"  /tokyo/を含むリンク: {len(all_links)}件")
            for link in all_links[:20]:
                href = await link.get_attribute("href")
                txt = (await link.inner_text()).strip()[:30]
                if href and ('/keibi' in href or '/unso' in href or '/gaishoku' in href or 'job' in href):
                    logger.info(f"    {href} | {txt}")

            # 全リンクのパターンを確認
            all_links2 = await page.query_selector_all("a")
            hrefs = set()
            for link in all_links2:
                href = await link.get_attribute("href")
                if href and 'baito.mynavi.jp' in href and any(x in href for x in ['job', 'keibi', 'keigo', 'unso', 'gaishoku', 'shoku', 'gyoshu', 'type', 'cond']):
                    hrefs.add(href)
            for h in sorted(hrefs)[:20]:
                logger.info(f"    求人リンク候補: {h}")

            # カードセレクタも調査
            for sel in [".p-joblist-item", ".job-list__item", ".p-job-list__item",
                        "article", ".p-list-unit", "[class*='joblist']",
                        "[class*='job-list']", "[class*='p-list']"]:
                els = await page.query_selector_all(sel)
                if els and len(els) > 2:
                    txt = await els[0].inner_text()
                    logger.info(f"  カード候補 '{sel}': {len(els)}件 | {txt[:100]}")
                    break

            await page.close()
        save_html("mynavi_tokyo", html)

        # 業種別URLパターンを試す
        logger.info("===== マイナビバイト 業種別URL試行 =====")
        mynavi_try = [
            "https://baito.mynavi.jp/tokyo/keigo/",
            "https://baito.mynavi.jp/tokyo/keibi/",
            "https://baito.mynavi.jp/tokyo/unso/",
            "https://baito.mynavi.jp/tokyo/gaishoku/",
            "https://baito.mynavi.jp/kanto/tokyo/keigo/",
            "https://baito.mynavi.jp/kanto/tokyo/unso/",
            "https://baito.mynavi.jp/search/?kw=%E8%AD%A6%E5%82%99&area=tokyo",
            "https://baito.mynavi.jp/list/?kw=%E8%AD%A6%E5%82%99&areaId=13",
            "https://baito.mynavi.jp/list/?keyword=%E8%AD%A6%E5%82%99&areaId=13",
        ]
        for url in mynavi_try:
            page, status, title, html = await get_page(context, url)
            if status == 200:
                if page:
                    for sel in [".p-joblist-item", ".job-list__item", "article",
                                "[class*='job']", "[class*='list-item']"]:
                        els = await page.query_selector_all(sel)
                        if els and len(els) > 2:
                            txt = await els[0].inner_text()
                            logger.info(f"  {url} | '{sel}': {len(els)}件 | {txt[:80]}")
                            break
                    else:
                        logger.info(f"  {url} | 200 だがカードなし")
                    await page.close()
            else:
                logger.info(f"  {status} | {url}")
            safe = re.sub(r'[^a-zA-Z0-9_]', '_', url[-40:])
            save_html(f"mynavi_try_{safe}", html)

        # ===== enゲージ: HTMLの詳細構造を印刺 =====
        logger.info("===== enゲージ HTML詳細調査 =====")
        url = "https://en-gage.net/user/search/?searchKey=%E8%AD%A6%E5%82%99&pref=13"
        page, status, title, html = await get_page(context, url, sleep_sec=5)
        logger.info(f"  {status} | len={len(html)}")
        if page:
            # ページ内の全テキストを印刺
            body_text = await page.inner_text("body")
            logger.info(f"  BODY先頯1000文字: {body_text[:1000]}")

            # クラス属性を持つ全要素を調査
            all_els = await page.query_selector_all("[class]")
            class_counts = {}
            for el in all_els[:500]:
                cls = await el.get_attribute("class")
                if cls:
                    for c in cls.split():
                        class_counts[c] = class_counts.get(c, 0) + 1
            top_classes = sorted(class_counts.items(), key=lambda x: -x[1])[:30]
            logger.info(f"  上位クラス: {top_classes}")

            await page.close()
        save_html("engage_debug_detail", html)

        # ===== kyujin-box: ホームページから求職者向けURLを探す =====
        logger.info("===== kyujin-box ホームページリンク調査 =====")
        page, status, title, html = await get_page(context, "https://kyujin-box.com/", sleep_sec=2)
        logger.info(f"  {status} | {title}")
        if page:
            # 全リンクを調査
            all_links = await page.query_selector_all("a")
            logger.info(f"  全リンク数: {len(all_links)}")
            for link in all_links:
                href = await link.get_attribute("href")
                txt = (await link.inner_text()).strip()[:40]
                if href:
                    logger.info(f"    {href[:80]} | {txt}")
            await page.close()
        save_html("kyujin_home", html)

        await context.close()
        await browser.close()

    logger.info("===== 調査完了 =====")


if __name__ == "__main__":
    asyncio.run(main())
