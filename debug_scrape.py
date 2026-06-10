"""
デバッグ用スクリプト: 各サイトの実際のHTML構造を出力する
"""
import asyncio
import glob


async def debug_site(context, url: str, site_name: str, wait: str = "domcontentloaded"):
    print(f"\n{'='*60}")
    print(f"サイト: {site_name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    page = await context.new_page()
    try:
        await page.goto(url, wait_until=wait, timeout=30000)
        await asyncio.sleep(3)

        title = await page.title()
        print(f"ページタイトル: {title}")

        text = await page.inner_text("body")
        print(f"\n本文（先頭1000文字）:\n{text[:1000]}")

        for selector in ["li", "article", ".item", "[class*='item']", "[class*='card']",
                         "[class*='list']", "[class*='result']", "[class*='job']", "[class*='company']"]:
            els = await page.query_selector_all(selector)
            if 2 < len(els) < 200:
                print(f"\nセレクタ '{selector}': {len(els)}件")
                sample = await els[0].inner_text()
                print(f"  サンプル: {sample[:150]!r}")

        html = await page.content()
        fname = f"debug_{site_name}.html"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"\nHTML全文を {fname} に保存（{len(html)}文字）")

    except Exception as e:
        print(f"エラー: {e}")
    finally:
        await page.close()


async def main():
    from playwright.async_api import async_playwright
    candidates = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")
    executable = candidates[0] if candidates else None

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=executable,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        context = await browser.new_context(
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        )

        await debug_site(context, "https://baito.mynavi.jp/list/?kw=%E8%AD%A6%E5%82%99&area%5B%5D=130000&p=1", "mynavi")
        await debug_site(context, "https://kyujinbox.com/jobs?location=%E6%9D%B1%E4%BA%AC%E9%83%BD&job=%E8%AD%A6%E5%82%99&page=1", "kyujinbox")
        await debug_site(context, "https://en-gage.net/company/search/?keyword=%E8%AD%A6%E5%82%99&prefecture=%E6%9D%B1%E4%BA%AC%E9%83%BD", "engage", wait="networkidle")

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
