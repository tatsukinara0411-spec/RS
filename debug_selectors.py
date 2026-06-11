#!/usr/bin/env python3
"""DOM構造調査: enゲージ・求人BOXのセレクタを特定する"""
import asyncio
import logging
import os
import re

from playwright.async_api import async_playwright

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

HEADLESS = os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() != "false"


async def dump_classes(page, label: str):
    classes = await page.evaluate("""
        () => {
            const counter = {};
            document.querySelectorAll('[class]').forEach(el => {
                el.className.split(/\\s+/).forEach(c => {
                    if (c) counter[c] = (counter[c] || 0) + 1;
                });
            });
            return Object.entries(counter).sort((a,b)=>b[1]-a[1]).slice(0,30);
        }
    """)
    logger.info(f"[{label}] 上位クラス名:")
    for cls, cnt in classes:
        logger.info(f"  .{cls}: {cnt}件")


async def try_selectors(page, label: str, selectors: list):
    for sel in selectors:
        try:
            els = await page.query_selector_all(sel)
            if els:
                txt = (await els[0].inner_text())[:120].replace("\n", " ")
                logger.info(f"[{label}] ✓ '{sel}': {len(els)}件 | {txt}")
        except Exception as e:
            logger.debug(f"[{label}] '{sel}': {e}")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS,
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
        logger.info("=" * 60)
        logger.info("求人ボックス")
        page = await context.new_page()
        url = "https://xn--pckua2a7gp15o89zb.com/?q=%E8%AD%A6%E5%82%99&l=%E6%9D%B1%E4%BA%AC%E9%83%BD"
        try:
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            logger.info(f"ステータス: {resp.status if resp else '?'} | タイトル: {await page.title()}")

            await dump_classes(page, "求人BOX")

            await try_selectors(page, "求人BOX", [
                "article", "li", ".result-item", "[class*='result']",
                "[class*='Result']", "[class*='job']", "[class*='Job']",
                "[class*='item']", "[class*='Item']", "[class*='card']",
                "[class*='Card']", "[class*='list']", "[class*='List']",
                "section", ".box", ".Box",
            ])

            await try_selectors(page, "求人BOX 会社名", [
                "[class*='company']", "[class*='Company']",
                "[class*='corp']", "[class*='employer']",
                "[class*='name']", "[class*='Name']",
                "h2", "h3", "h4",
            ])

            html = await page.content()
            with open("debug_kyujinbox_new.html", "w", encoding="utf-8") as f:
                f.write(html)
            logger.info(f"HTML保存: debug_kyujinbox_new.html ({len(html)} bytes)")

        except Exception as e:
            logger.error(f"求人BOX エラー: {e}")
        finally:
            await page.close()

        # ===== enゲージ =====
        logger.info("=" * 60)
        logger.info("enゲージ")
        page = await context.new_page()
        url = "https://en-gage.net/user/search/?searchKey=%E8%AD%A6%E5%82%99&pref=13"
        try:
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)
            logger.info(f"ステータス: {resp.status if resp else '?'} | タイトル: {await page.title()}")

            await dump_classes(page, "enゲージ")

            await try_selectors(page, "enゲージ", [
                "li.row", "li[class*='row']", ".row--company",
                "[class*='company']", "[class*='Company']",
                "article", ".card", "[class*='card']", "[class*='Card']",
                "[class*='list']", "[class*='List']", "[class*='item']",
                "[class*='Item']", "li", "section",
            ])

            await try_selectors(page, "enゲージ 会社名", [
                "[class*='name']", "[class*='Name']",
                "[class*='corp']", "h2", "h3", "h4",
                "a[href*='/user/']", "a[href*='/company/']",
            ])

            html = await page.content()
            with open("debug_engage_new.html", "w", encoding="utf-8") as f:
                f.write(html)
            logger.info(f"HTML保存: debug_engage_new.html ({len(html)} bytes)")

        except Exception as e:
            logger.error(f"enゲージ エラー: {e}")
        finally:
            await page.close()

        await context.close()
        await browser.close()

    logger.info("完了")


if __name__ == "__main__":
    asyncio.run(main())
