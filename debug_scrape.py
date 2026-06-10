"""
デバッグ用: 各サイトの正しいURL・セレクタを調査する
"""
import asyncio
import glob


TEST_URLS = [
    # マイナビバイト
    ("mynavi_1", "https://baito.mynavi.jp/kanto/tokyo/", "domcontentloaded"),
    ("mynavi_2", "https://baito.mynavi.jp/kanto/tokyo/?jobtype[]=0601", "domcontentloaded"),
    ("mynavi_3", "https://baito.mynavi.jp/list/?kw=%E8%AD%A6%E5%82%99&pref=13", "domcontentloaded"),
    ("mynavi_4", "https://baito.mynavi.jp/?kw=%E8%AD%A6%E5%82%99&area=13&p=1", "domcontentloaded"),
    # enゲージ（求人検索）
    ("engage_1", "https://en-gage.net/s/?job_keyword=%E8%AD%A6%E5%82%99&prefecture=13", "networkidle"),
    ("engage_2", "https://en-gage.net/search/?keyword=%E8%AD%A6%E5%82%99&area=13", "networkidle"),
    ("engage_3", "https://en-gage.net/", "networkidle"),
    # 求人ボックス
    ("kyujin_1", "https://kyujinbox.com/", "domcontentloaded"),
    ("kyujin_2", "https://xn--dckl4bvb2124eshi.jp/", "domcontentloaded"),
    ("kyujin_3", "https://kyujin-box.com/", "domcontentloaded"),
]


async def check_url(context, name, url, wait):
    page = await context.new_page()
    try:
        await page.goto(url, wait_until=wait, timeout=20000)
        await asyncio.sleep(2)
        title = await page.title()
        text = await page.inner_text("body")
        html = await page.content()

        print(f"\n[{name}] {url}")
        print(f"  タイトル: {title}")
        print(f"  本文先頭: {text[:200].replace(chr(10), ' ')!r}")

        # リスト要素の数を確認
        for sel in ["li", "article", ".job", "[class*='job']", "[class*='item']", "[class*='result']"]:
            els = await page.query_selector_all(sel)
            if 3 < len(els) < 500:
                sample = (await els[0].inner_text())[:80]
                print(f"  {sel}: {len(els)}件 例={sample!r}")

        # HTMLを保存
        with open(f"debug_{name}.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  HTML保存: debug_{name}.html ({len(html)}文字)")

    except Exception as e:
        print(f"[{name}] エラー: {e}")
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
        for name, url, wait in TEST_URLS:
            await check_url(context, name, url, wait)

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
