#!/usr/bin/env python3
"""詳細ページ調査 v3: 電話番号ボタンのクリック・求人BOX正しい検索URL・enゲージ詳細URL"""
import asyncio
import glob as _glob
import re

from playwright.async_api import async_playwright

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

PHONE_RE = re.compile(r"0\d{1,4}[-(]?\d{1,4}[-)]?\d{3,4}")
ADDR_RE = re.compile(r"(〒\d{3}-?\d{4}|東京都.{1,40}\d)")


async def investigate_mynavi(context):
    print("\n########## マイナビバイト: 電話番号を表示ボタン ##########")
    page = await context.new_page()
    await page.goto("https://baito.mynavi.jp/tokyo/keibi/", wait_until="domcontentloaded")
    await asyncio.sleep(3)
    hrefs = await page.eval_on_selector_all(
        ".tabJobOfferCard a[href]", "els => els.map(e => e.getAttribute('href'))"
    )
    links = [h for h in hrefs if h and re.search(r"/cl-\d+/job-\d+", h)]
    await page.close()

    for href in dict.fromkeys(links)[:2] if isinstance(links, dict) else list(dict.fromkeys(links))[:2]:
        url = "https://baito.mynavi.jp" + href
        p = await context.new_page()
        try:
            await p.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(3)

            btns = await p.query_selector_all("text=電話番号を表示")
            print(f"\n===== {url}")
            print(f"電話番号を表示ボタン: {len(btns)}個")
            if btns:
                try:
                    await btns[0].click()
                    await asyncio.sleep(2)
                except Exception as e:
                    print("クリック失敗:", e)

            tels = await p.eval_on_selector_all(
                "a[href^='tel:']", "els => els.map(e => e.getAttribute('href'))"
            )
            print("tel:リンク:", tels[:5])
            body = await p.evaluate("() => document.body.innerText")
            phones = PHONE_RE.findall(body)
            print("本文の電話番号らしき文字列:", list(dict.fromkeys(phones))[:8])
            addrs = [l.strip()[:90] for l in body.split("\n") if ADDR_RE.search(l)]
            print("番地まである住所らしき行:", addrs[:6])
            # 勤務地ラベル周辺
            sec = await p.evaluate(
                """() => {
                    const out = [];
                    document.querySelectorAll('h2,h3,h4,dt,th,div,span').forEach(el => {
                        const t = (el.innerText||'').trim();
                        if (t === '勤務地' || t === '住所' || t === '勤務地住所') {
                            const sib = el.nextElementSibling || el.parentElement;
                            if (sib) out.push(t + ' => ' + sib.innerText.trim().slice(0,120));
                        }
                    });
                    return out.slice(0,6);
                }"""
            )
            print("勤務地/住所ラベル周辺:", sec)
        except Exception as e:
            print("エラー:", e)
        finally:
            await p.close()


async def investigate_kyujinbox(context):
    print("\n########## 求人BOX: 正しい検索URL ##########")
    for url in [
        "https://xn--pckua2a7gp15o89zb.com/警備の仕事-東京都",
        "https://xn--pckua2a7gp15o89zb.com/警備の仕事?l=東京都",
    ]:
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(3)
            print(f"\n----- {url}")
            print("最終URL:", page.url)
            title = await page.title()
            print("タイトル:", title[:60])

            classes = await page.evaluate(
                """() => {
                    const seen = {};
                    document.querySelectorAll('section,li,article,div').forEach(el => {
                        const c = el.className;
                        if (typeof c === 'string' && /p-job|p-result|p-search|cassette/i.test(c)) {
                            c.split(/\\s+/).forEach(cls => { if (cls) seen[cls] = (seen[cls]||0)+1; });
                        }
                    });
                    return Object.entries(seen).sort((a,b)=>b[1]-a[1]).slice(0,20);
                }"""
            )
            print("クラス名出現数:", classes)

            # 検索結果カードらしきものの中身を1件
            for sel in [".p-jobCassette", "[class*='p-job_'], [class*='p-job ']", "section[class*='job']"]:
                els = await page.query_selector_all(sel)
                if els:
                    t = (await els[0].inner_text())[:200].replace("\n", " | ")
                    print(f"セレクタ {sel}: {len(els)}件 | 1件目: {t}")
                    hrefs = await els[0].eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))")
                    print("  リンク:", hrefs[:3])
                    break
        except Exception as e:
            print("エラー:", e)
        finally:
            await page.close()


async def investigate_engage(context):
    print("\n########## enゲージ: work_idから詳細ページ ##########")
    page = await context.new_page()
    await page.goto("https://en-gage.net/user/search/?searchKey=警備&pref=13", wait_until="domcontentloaded")
    await asyncio.sleep(10)
    hrefs = await page.eval_on_selector_all(
        "a[href*='work_id=']", "els => els.slice(0,5).map(e => e.getAttribute('href'))"
    )
    ids = []
    for h in hrefs:
        m = re.search(r"work_id=(\d+)", h or "")
        if m:
            ids.append(m.group(1))
    ids = list(dict.fromkeys(ids))
    print("work_id:", ids[:5])
    await page.close()

    for wid in ids[:2]:
        for pattern in [
            f"https://en-gage.net/user/work/detail/?work_id={wid}",
        ]:
            p = await context.new_page()
            try:
                await p.goto(pattern, wait_until="domcontentloaded")
                await asyncio.sleep(8)
                print(f"\n----- {pattern}")
                print("最終URL:", p.url)
                title = await p.title()
                print("タイトル:", title[:80])
                body = await p.evaluate("() => document.body.innerText")
                phones = PHONE_RE.findall(body)
                print("電話番号らしき文字列:", list(dict.fromkeys(phones))[:6])
                # 会社名・所在地・住所まわり
                lines = body.split("\n")
                for i, l in enumerate(lines):
                    if re.search(r"(会社名|所在地|住所|企業情報|勤務地)", l.strip()[:6]):
                        ctx_lines = " / ".join(x.strip()[:60] for x in lines[i:i+3])
                        print("  ", ctx_lines[:150])
            except Exception as e:
                print("エラー:", e)
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
