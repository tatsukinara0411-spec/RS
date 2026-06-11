#!/usr/bin/env python3
"""
URLパターン調査 v4 - 最終確認
- mynavi /tokyo/keibi/ の正しいカードセレクタ
- engage .md_cardの中身確認
- kyujinbox.com 求職者URLテスト
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

        # ===== マイナビバイト: /tokyo/keibi/ のカード構造 =====
        logger.info("===== マイナビバイト /tokyo/keibi/ セレクタ調査 =====")
        page, status, title, html = await get_page(
            context, "https://baito.mynavi.jp/tokyo/keibi/", sleep_sec=2
        )
        logger.info(f"  {status} | {title[:60]}")
        if page:
            # jobを含むクラスの詳細調査
            job_els = await page.query_selector_all("[class*='job']")
            logger.info(f"  [class*='job'] 全{len(job_els)}件")

            # 実際の求人カードに絞り込む
            card_sels = [
                ".p-joblist-item", ".p-job-list__item", ".job-list__item",
                ".p-list-unit", ".p-list-item", ".job-card",
                "[class*='joblist-item']", "[class*='job-item']",
                "[class*='p-job']", "[class*='listItem']",
                "[class*='jobcard']", "[class*='jobCard']",
            ]
            for sel in card_sels:
                els = await page.query_selector_all(sel)
                if els:
                    txt = await els[0].inner_text()
                    logger.info(f"  '{sel}': {len(els)}件 | {txt[:120]}")

            # 会社名候補を探す
            company_sels = [
                ".p-company-name", ".company-name", "[class*='company']",
                ".p-store-name", "[class*='store']", "[class*='shop']",
            ]
            for sel in company_sels:
                els = await page.query_selector_all(sel)
                if els:
                    txt = await els[0].inner_text()
                    logger.info(f"  会社名 '{sel}': {len(els)}件 | {txt[:60]}")
                    break

            # ページネーションの次ページURLパターンも調査
            next_links = await page.query_selector_all("a[href*='/tokyo/keibi/']")
            for link in next_links[:5]:
                href = await link.get_attribute("href")
                txt = (await link.inner_text()).strip()[:30]
                if href and ('p=' in href or 'page' in href or href.endswith('/2')):
                    logger.info(f"  次ページ候補: {href} | {txt}")

            await page.close()
        save_html("mynavi_keibi", html)

        # ===== enゲージ: md_cardの中身確認 =====
        logger.info("===== enゲージ .md_card調査 =====")
        url = "https://en-gage.net/user/search/?searchKey=%E8%AD%A6%E5%82%99&pref=13"
        page, status, title, html = await get_page(context, url, sleep_sec=5)
        logger.info(f"  {status} | len={len(html)}")
        if page:
            # .md_cardの中身を調査
            cards = await page.query_selector_all(".md_card")
            logger.info(f"  .md_card: {len(cards)}件")
            for i, card in enumerate(cards[:5]):
                txt = (await card.inner_text()).strip()
                logger.info(f"  card[{i}]: {txt[:200]}")

            # .cardContentも確認
            contents = await page.query_selector_all(".cardContent")
            logger.info(f"  .cardContent: {len(contents)}件")
            for i, c in enumerate(contents[:3]):
                txt = (await c.inner_text()).strip()
                logger.info(f"  content[{i}]: {txt[:200]}")

            # ページネーション調査
            next_links = await page.query_selector_all("a[href*='page'], .pagination a, [class*='page']")
            logger.info(f"  ページネーション候補: {len(next_links)}件")
            for link in next_links[:3]:
                href = await link.get_attribute("href")
                txt = (await link.inner_text()).strip()[:20]
                logger.info(f"    {href} | {txt}")

            # 件数
            body = await page.inner_text("body")
            m = re.search(r'(\d+)\s*社', body)
            if m:
                logger.info(f"  件数: {m.group(0)}")

            await page.close()
        save_html("engage_keibi_final", html)

        # ===== 求人ボックス求職者サイト =====
        logger.info("===== 求人ボックス 求職者サイト調査 =====")
        kyujin_urls = [
            "https://xn--pckua2a7gp15o89zb.com/",  # 求人ボックス.com
            "https://xn--pckua2a7gp15o89zb.com/jobs?q=%E8%AD%A6%E5%82%99&l=%E6%9D%B1%E4%BA%AC%E9%83%BD",
            "https://xn--pckua2a7gp15o89zb.com/jobs?q=%E8%AD%A6%E5%82%99+%E3%82%A2%E3%83%AB%E3%83%90%E3%82%A4ト&l=%E6%9D%B1%E4%BA%AC%E9%83%BD",
        ]
        for url in kyujin_urls:
            page, status, title, html = await get_page(context, url, sleep_sec=2)
            logger.info(f"  {status} | {title[:70]} | {url[-50:]}")
            if page and status == 200:
                # 求人カードセレクタ
                for sel in [".result-item", ".job-item", "article",
                            "[class*='result']", "[class*='job']", "[class*='Item']",
                            "[class*='card']", "[class*='list-item']"]:
                    els = await page.query_selector_all(sel)
                    if els and len(els) > 2:
                        txt = await els[0].inner_text()
                        logger.info(f"  '{sel}': {len(els)}件 | {txt[:150]}")
                        break
                # 会社名候補
                for sel in ["[class*='company']", "[class*='corp']", ".job-company"]:
                    els = await page.query_selector_all(sel)
                    if els:
                        txt = await els[0].inner_text()
                        logger.info(f"  会社名 '{sel}': {len(els)}件 | {txt[:80]}")
                        break
                await page.close()
            safe = re.sub(r'[^a-zA-Z0-9_]', '_', url[-40:])
            save_html(f"kyujin_jobseeker_{safe}", html)

        await context.close()
        await browser.close()

    logger.info("===== 調査完了 =====")


if __name__ == "__main__":
    asyncio.run(main())
