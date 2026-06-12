#!/usr/bin/env python3
"""詳細ページ調査スクリプト: 各サイトの求人詳細ページに電話番号・住所がどう載っているか確認する"""
import asyncio
import glob as _glob
import re

from playwright.async_api import async_playwright

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

INTEREST = re.compile(r"(〒|東京都.{2,30}(区|市)|電話|TEL|tel)")


async def dump_detail(page, label: str):
    print(f"\n===== {label}: {page.url}")
    tels = await page.eval_on_selector_all(
        "a[href^='tel:']", "els => els.map(e => e.getAttribute('href') + ' | ' + e.innerText.trim())"
    )
    print(f"[tel:リンク] {tels[:5]}")

    pairs = await page.evaluate(
        """() => {
            const out = [];
            document.querySelectorAll('dt').forEach(dt => {
                const dd = dt.nextElementSibling;
                if (dd) out.push(dt.innerText.trim().slice(0,20) + ' => ' + dd.innerText.trim().slice(0,80));
            });
            document.querySelectorAll('th').forEach(th => {
                const td = th.parentElement && th.parentElement.querySelector('td');
                if (td) out.push(th.innerText.trim().slice(0,20) + ' => ' + td.innerText.trim().slice(0,80));
            });
            return out;
        }"""
    )
    hits = [p for p in pairs if re.search(r"勤務地|所在地|住所|電話|アクセス|会社", p)]
    print(f"[dt/dd th/td] {len(pairs)}組中、関連 {len(hits)}組:")
    for h in hits[:12]:
        print("   ", h.replace("\n", " "))

    body = await page.evaluate("() => document.body.innerText")
    lines = [l.strip() for l in body.split("\n") if INTEREST.search(l)]
    print(f"[本文の住所/電話っぽい行] {len(lines)}行:")
    for l in lines[:12]:
        print("   ", l[:100])


async def investigate_mynavi(context):
    print("\n########## マイナビバイト ##########")
    page = await context.new_page()
    await page.goto("https://baito.mynavi.jp/tokyo/keibi/", wait_until="domcontentloaded")
    await asyncio.sleep(3)
    cards = await page.query_selector_all(".tabJobOfferCard")
    print(f"カード数: {len(cards)}")
    links = []
    for card in cards[:3]:
        hrefs = await card.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))")
        print("カード内リンク:", [h for h in hrefs[:5]])
        for h in hrefs:
            if h and "/job/" in h or (h and re.search(r"/\d{6,}", h or "")):
                links.append(h)
                break
    await page.close()

    for href in links[:2]:
        url = href if href.startswith("http") else "https://baito.mynavi.jp" + href
        p = await context.new_page()
        try:
            await p.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(3)
            await dump_detail(p, "マイナビ詳細")
        except Exception as e:
            print("詳細ページエラー:", e)
        finally:
            await p.close()


async def investigate_kyujinbox(context):
    print("\n########## 求人BOX ##########")
    page = await context.new_page()
    await page.goto("https://xn--pckua2a7gp15o89zb.com/?q=警備&l=東京都", wait_until="domcontentloaded")
    await asyncio.sleep(3)
    cards = await page.query_selector_all(".p-jobPickUp")
    print(f"カード数: {len(cards)}")
    links = []
    for card in cards[:3]:
        hrefs = await card.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))")
        print("カード内リンク:", hrefs[:5])
        if hrefs:
            links.append(hrefs[0])
    await page.close()

    for href in links[:2]:
        url = href if href.startswith("http") else "https://xn--pckua2a7gp15o89zb.com" + href
        p = await context.new_page()
        try:
            await p.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(3)
            await dump_detail(p, "求人BOX詳細")
        except Exception as e:
            print("詳細ページエラー:", e)
        finally:
            await p.close()


async def investigate_engage(context):
    print("\n########## enゲージ ##########")
    page = await context.new_page()
    await page.goto("https://en-gage.net/user/search/?searchKey=警備&pref=13", wait_until="domcontentloaded")
    await asyncio.sleep(10)
    rows = await page.query_selector_all("li.row.row--company, [class*='row--company'], .md_card")
    print(f"カード数: {len(rows)}")
    links = []
    for row in rows[:3]:
        hrefs = await row.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))")
        print("カード内リンク:", hrefs[:5])
        if hrefs:
            links.append(hrefs[0])
    await page.close()

    for href in links[:2]:
        url = href if href.startswith("http") else "https://en-gage.net" + href
        p = await context.new_page()
        try:
            await p.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(8)
            await dump_detail(p, "enゲージ詳細")
        except Exception as e:
            print("詳細ページエラー:", e)
        finally:
            await p.close()


async def main():
    async with async_playwright() as p:
        candidates = _glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")
        executable = candidates[0] if candidates else None
        browser = await p.chromium.launch(
            headless=True,
            executable_path=executable,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            locale="ja-JP", timezone_id="Asia/Tokyo",
            viewport={"width": 1280, "height": 800}, user_agent=UA,
        )
        for fn in (investigate_mynavi, investigate_kyujinbox, investigate_engage):
            try:
                await fn(context)
            except Exception as e:
                print(f"{fn.__name__} エラー: {e}")
        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
