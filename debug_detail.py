#!/usr/bin/env python3
"""詳細ページ調査 v4: 求人BOXの検索結果カード構造と詳細ページの会社情報を確認"""
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
        print(f"検索結果カード数: {len(cards)}")

        detail_links = []
        for i, card in enumerate(cards[:3]):
            text = (await card.inner_text())[:250].replace("\n", " | ")
            print(f"\n--- カード{i+1}: {text}")
            hrefs = await card.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))")
            print("リンク:", hrefs[:4])
            data_href = await card.evaluate("el => el.getAttribute('data-href') || (el.querySelector('[data-href]') ? el.querySelector('[data-href]').getAttribute('data-href') : null)")
            print("data-href:", data_href)
            for h in (hrefs or []) + ([data_href] if data_href else []):
                if h and ("/jb/" in h or "/jbi/" in h):
                    detail_links.append(h)
                    break

        # 2ページ目のURL形式
        next_hrefs = await page.eval_on_selector_all(
            "a[rel='next'], .p-pager a, [class*='pager'] a, [class*='pagination'] a",
            "els => els.slice(0,6).map(e => e.getAttribute('href'))"
        )
        print("\nページ送りリンク:", next_hrefs)
        await page.close()

        print("\n詳細リンク:", detail_links)
        for href in detail_links[:2]:
            url = href if href.startswith("http") else "https://xn--pckua2a7gp15o89zb.com" + href
            pg = await context.new_page()
            try:
                await pg.goto(url, wait_until="domcontentloaded")
                await asyncio.sleep(3)
                print(f"\n===== 詳細: {url}")
                body = await pg.evaluate("() => document.body.innerText")
                phones = list(dict.fromkeys(PHONE_RE.findall(body)))
                print("電話番号候補:", phones[:6])

                pairs = await pg.evaluate(
                    """() => {
                        const out = [];
                        document.querySelectorAll('dt').forEach(dt => {
                            const dd = dt.nextElementSibling;
                            if (dd) out.push(dt.innerText.trim().slice(0,14) + ' => ' + dd.innerText.trim().slice(0,130));
                        });
                        return out;
                    }"""
                )
                for pr in pairs:
                    if re.search(r"勤務地|会社|社名|住所|所在地|連絡|応募", pr):
                        print("  ", pr.replace("\n", " ")[:160])

                # 会社情報セクションの見出し直後
                for kw in ["会社情報", "企業情報", "会社概要", "応募先", "問い合わせ"]:
                    idx = body.find(kw)
                    if idx != -1:
                        print(f"  [{kw}] 周辺:", body[idx:idx+220].replace("\n", " / ")[:220])
            except Exception as e:
                print("エラー:", e)
            finally:
                await pg.close()

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
