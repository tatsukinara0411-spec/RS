#!/usr/bin/env python3
"""
デバッグ v5 - 最終確認
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
            headless=HEADLESS, executable_path=executable,
            args=["--no-sandbox", "--disable-setuid-sandbox",
                  "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            locale="ja-JP", timezone_id="Asia/Tokyo",
            viewport={"width": 1280, "height": 800},
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"),
        )

        # ===== マイナビバイト: shopの親要素と住所クラスを特定 =====
        logger.info("===== マイナビバイト 住所・カード構造調査 =====")
        page, status, title, html = await get_page(
            context, "https://baito.mynavi.jp/tokyo/keibi/", sleep_sec=2)
        logger.info(f"  {status} | {title[:60]}")
        if page:
            # shop要素の最初を取得してその親要素のクラスを調べる
            shops = await page.query_selector_all("[class*='shop']")
            logger.info(f"  shop要素数: {len(shops)}")
            if shops:
                # 最初のshop要素
                el = shops[0]
                txt = (await el.inner_text()).strip()
                cls = await el.get_attribute("class")
                logger.info(f"  shop[0] class={cls} | {txt[:50]}")
                # 親を辿ってカード要素を探す
                for i in range(5):
                    parent = await el.evaluate_handle("el => el.parentElement")
                    pcls = await parent.get_attribute("class")
                    ptag = await parent.evaluate("el => el.tagName")
                    logger.info(f"  親[{i}] tag={ptag} class={pcls}")
                    el = parent

            # 住所候補クラスを探す
            addr_sels = [
                "[class*='area']", "[class*='place']", "[class*='location']",
                "[class*='address']", "[class*='station']", "[class*='access']",
                "[class*='pref']", "[class*='city']",
            ]
            for sel in addr_sels:
                els = await page.query_selector_all(sel)
                if els:
                    txt = (await els[0].inner_text()).strip()
                    logger.info(f"  住所候補 '{sel}': {len(els)}件 | {txt[:60]}")

            # ページネーション: 次ページURL
            next_links = await page.query_selector_all(".pagination a, [class*='next'], [class*='pager'] a")
            for link in next_links[:5]:
                href = await link.get_attribute("href")
                txt = (await link.inner_text()).strip()[:20]
                logger.info(f"  ページネーション: {href} | {txt}")

            await page.close()
        save_html("mynavi_keibi_v5", html)

        # ===== enゲージ: script内JSONと実際のリスト要素を探す =====
        logger.info("===== enゲージ script JSONと求人リスト調査 =====")
        url = "https://en-gage.net/user/search/?searchKey=%E8%AD%A6%E5%82%99&pref=13"
        page, status, title, html = await get_page(context, url, sleep_sec=6)
        logger.info(f"  {status} | len={len(html)}")
        if page:
            # script内のJSONを探す (Next.js __NEXT_DATA__ など)
            scripts = await page.query_selector_all("script")
            for i, s in enumerate(scripts):
                content_s = await s.inner_text()
                if '株式会社' in content_s or '会社名' in content_s or 'companyName' in content_s:
                    logger.info(f"  script[{i}]に会社名データあり: {content_s[:500]}")
                    break

            # 株式会社を含む要素を探す
            all_els = await page.query_selector_all("*")
            kaisha_found = 0
            for el in all_els[:2000]:
                try:
                    txt = await el.evaluate("el => el.childNodes.length === 1 && el.firstChild.nodeType === 3 ? el.firstChild.nodeValue : ''")
                    if txt and ('株式会社' in txt or '有限会社' in txt):
                        cls = await el.get_attribute("class") or ""
                        tag = await el.evaluate("el => el.tagName")
                        logger.info(f"  会社名発見: tag={tag} class={cls} | {txt[:60]}")
                        kaisha_found += 1
                        if kaisha_found >= 5:
                            break
                except:
                    pass

            if kaisha_found == 0:
                # HTMLから直接検索
                m = re.findall(r'株式会社[^<"]{0,30}', html)
                logger.info(f"  HTML内の株式会社: {m[:10]}")

            await page.close()
        save_html("engage_v5", html)

        # ===== 求人ボックス: 検索URLを探す =====
        logger.info("===== 求人ボックス 検索URL調査 =====")
        page, status, title, html = await get_page(
            context, "https://xn--pckua2a7gp15o89zb.com/", sleep_sec=3)
        logger.info(f"  {status} | {title[:60]}")
        if page:
            # 検索フォームを探す
            forms = await page.query_selector_all("form")
            for i, form in enumerate(forms[:3]):
                action = await form.get_attribute("action") or ""
                method = await form.get_attribute("method") or ""
                logger.info(f"  form[{i}] action={action} method={method}")
                inputs = await form.query_selector_all("input")
                for inp in inputs[:5]:
                    name = await inp.get_attribute("name") or ""
                    itype = await inp.get_attribute("type") or ""
                    logger.info(f"    input name={name} type={itype}")

            # 全リンクから検索っぽいURLを探す
            links = await page.query_selector_all("a")
            for link in links:
                href = await link.get_attribute("href") or ""
                if href and ('search' in href or 'jobs' in href or 'q=' in href or 'keyword' in href):
                    txt = (await link.inner_text()).strip()[:30]
                    logger.info(f"  検索リンク: {href[:80]} | {txt}")

            await page.close()
        save_html("kyujin_jobseeker_v5", html)

        # 求人ボックス: 別のURLパターンを試す
        kyujin_try = [
            "https://xn--pckua2a7gp15o89zb.com/?q=%E8%AD%A6%E5%82%99&l=%E6%9D%B1%E4%BA%AC%E9%83%BD",
            "https://xn--pckua2a7gp15o89zb.com/search?q=%E8%AD%A6%E5%82%99&l=%E6%9D%B1%E4%BA%AC%E9%83%BD",
            "https://xn--pckua2a7gp15o89zb.com/job?q=%E8%AD%A6%E5%82%99&l=%E6%9D%B1%E4%BA%AC%E9%83%BD",
            "https://xn--pckua2a7gp15o89zb.com/jobs/%E8%AD%A6%E5%82%99/%E6%9D%B1%E4%BA%AC%E9%83%BD/",
        ]
        for url in kyujin_try:
            page, status, title, html = await get_page(context, url, sleep_sec=1)
            logger.info(f"  {status} | {title[:50]} | {url[-50:]}")
            if page:
                if status == 200:
                    for sel in ["[class*='result']", "[class*='job']", "article",
                                "[class*='list']", "[class*='card']"]:
                        els = await page.query_selector_all(sel)
                        if els and len(els) > 3:
                            txt = (await els[0].inner_text()).strip()
                            logger.info(f"    '{sel}': {len(els)}件 | {txt[:80]}")
                            break
                await page.close()

        await context.close()
        await browser.close()
    logger.info("===== 調査完了 =====")


if __name__ == "__main__":
    asyncio.run(main())
