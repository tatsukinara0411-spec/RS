#!/usr/bin/env python3
"""詳細ページ調査 v2: 電話番号・住所の取得方法と正しいカードセレクタを特定する"""
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
                if (dd) out.push('DT:' + dt.innerText.trim().slice(0,16) + ' => ' + dd.innerText.trim().slice(0,100));
            });
            document.querySelectorAll('th').forEach(th => {
                const td = th.parentElement && th.parentElement.querySelector('td');
                if (td) out.push('TH:' + th.innerText.trim().slice(0,16) + ' => ' + td.innerText.trim().slice(0,100));
            });
            return out;
        }"""
    )
    print(f"[dt/dd th/td 全{len(pairs)}組]")
    for h in pairs[:20]:
        print("   ", h.replace("\n", " "))

    body = await page.evaluate("() => document.body.innerText")
    lines = [l.strip() for l in body.split("\n") if INTEREST.search(l)]
    print(f"[本文の住所/電話っぽい行] {len(lines)}行:")
    for l in lines[:12]:
        print("   ", l[:110])


async def investigate_mynavi(context):
    print("\n########## マイナビバイト ##########")
    page = await context.new_page()
    await page.goto("https://baito.mynavi.jp/tokyo/keibi/", wait_until="domcontentloaded")
    await asyncio.sleep(3)
    cards = await page.query_selector_all(".tabJobOfferCard")
    print(f"カード数: {len(cards)}")
    links = []
    for card in cards[:4]:
        hrefs = await card.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))")
        for h in hrefs:
            if h and re.search(r"/cl-\d+/job-\d+", h):
                links.append(h)
                break
    print("詳細リンク:", links)
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

    # 検索結果の本命カードを特定するため、主要ブロックのクラス名を一覧表示
    classes = await page.evaluate(
        """() => {
            const seen = {};
            document.querySelectorAll('main *, body *').forEach(el => {
                const c = el.className;
                if (typeof c === 'string' && /job|Job|cassette|Cassette|result|Result|card|Card/.test(c)) {
                    c.split(/\\s+/).forEach(cls => { if (cls) seen[cls] = (seen[cls]||0)+1; });
                }
            });
            return Object.entries(seen).sort((a,b)=>b[1]-a[1]).slice(0,30);
        }"""
    )
    print("クラス名出現数:", classes)

    # 候補セレクタごとの件数と、最初のカードの中身
    for sel in [".p-jobCassette", "[class*='jobCassette']", ".p-result_card", "[class*='searchResult']",
                "section[class*='job']", "li[class*='job']", "article"]:
        els = await page.query_selector_all(sel)
        if els:
            first_text = (await els[0].inner_text())[:120].replace("\n", " | ")
            print(f"セレクタ {sel}: {len(els)}件 | 1件目: {first_text}")

    # 本命らしきカードから詳細リンクを取り直す
    hrefs = await page.eval_on_selector_all(
        "a[href*='/jb/'], a[href*='/jbi/']",
        "els => els.slice(0,10).map(e => e.getAttribute('href'))"
    )
    print("ページ内 /jb/ /jbi/ リンク:", hrefs[:10])
    await page.close()

    if hrefs:
        url = hrefs[0] if hrefs[0].startswith("http") else "https://xn--pckua2a7gp15o89zb.com" + hrefs[0]
        p = await context.new_page()
        try:
            await p.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(3)
            await dump_detail(p, "求人BOX詳細(検索結果側)")
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
    if rows:
        html = await rows[0].evaluate("el => el.outerHTML.slice(0, 900)")
        print("1件目のHTML(先頭900字):")
        print(html)
        ancestor = await rows[0].evaluate("el => { const a = el.closest('a'); return a ? a.getAttribute('href') : '(aの祖先なし)'; }")
        print("祖先のaタグ:", ancestor)

    # ページ全体のリンクから企業/求人ページらしきもの
    hrefs = await page.eval_on_selector_all(
        "a[href]",
        """els => {
            const out = [];
            for (const e of els) {
                const h = e.getAttribute('href') || '';
                if (/company|work|saiyo|recruit/.test(h)) out.push(h);
                if (out.length >= 10) break;
            }
            return out;
        }"""
    )
    print("企業/求人っぽいリンク:", hrefs)
    await page.close()


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
