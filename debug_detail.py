#!/usr/bin/env python3
"""詳細ページ調査 v5: 求人BOXのカードクリックで電話番号が取れるか確認"""
import asyncio
import glob as _glob
import re

from playwright.async_api import async_playwright

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

PHONE_RE = re.compile(r"0\d{1,4}-\d{1,4}-\d{3,4}")


async def main():
    async with async_playwright() as p:
        candidates = _glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")
        executable = candidates[0] if candidates else None
        browser = await p.chromium.launch(
            headless=True, executable_path=executable,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            locale="ja-JP", timezone_id="Asia/Tokyo",
            viewport={"width": 1280, "height": 800}, user_agent=UA,
        )

        page = await context.new_page()
        await page.goto("https://xn--pckua2a7gp15o89zb.com/警備の仕事-東京都", wait_until="domcontentloaded")
        await asyncio.sleep(3)

        cards = await page.query_selector_all(".p-result_card")
        print(f"カード数: {len(cards)}")

        for i in (0, 1, 2):
            if i >= len(cards):
                break
            cards = await page.query_selector_all(".p-result_card")
            card = cards[i]
            company_line = (await card.inner_text()).split("\n")
            company_line = [l.strip() for l in company_line if l.strip()]
            print(f"\n--- カード{i+1}: {company_line[:3]}")

            popup = None
            try:
                async with context.expect_page(timeout=6000) as pinfo:
                    await card.click()
                popup = await pinfo.value
            except Exception:
                pass

            if popup:
                try:
                    await popup.wait_for_load_state("domcontentloaded", timeout=15000)
                except Exception:
                    pass
                await asyncio.sleep(3)
                print("→ 新しいタブ:", popup.url[:120])
                try:
                    body = await popup.evaluate("() => document.body.innerText")
                    phones = list(dict.fromkeys(PHONE_RE.findall(body)))
                    print("   電話番号候補:", phones[:6])
                    addrs = [l.strip()[:90] for l in body.split("\n") if re.search(r"東京都.{1,40}\d", l)]
                    print("   番地住所候補:", addrs[:4])
                except Exception as e:
                    print("   読み取りエラー:", e)
                await popup.close()
            else:
                await asyncio.sleep(3)
                print("→ 同一ページ。現在URL:", page.url[:120])
                preview = await page.query_selector("[class*='preview'], [class*='Preview'], [class*='detail']")
                if preview:
                    text = await preview.inner_text()
                    phones = list(dict.fromkeys(PHONE_RE.findall(text)))
                    print("   プレビュー内 電話番号候補:", phones[:6])
                    addrs = [l.strip()[:90] for l in text.split("\n") if re.search(r"東京都.{1,40}\d", l)]
                    print("   プレビュー内 番地住所候補:", addrs[:4])
                else:
                    body = await page.evaluate("() => document.body.innerText")
                    phones = list(dict.fromkeys(PHONE_RE.findall(body)))
                    print("   ページ全体 電話番号候補:", phones[:6])
                if page.url and "の仕事" not in page.url:
                    await page.go_back()
                    await asyncio.sleep(2)

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
