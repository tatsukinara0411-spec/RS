#!/usr/bin/env python3
"""
各求人サイトの現在のHTML構造を診断してログに出す。
スクレイパーをサイト変更に合わせて作り直すための調査用。

出力:
  - ページタイトル・最終URL
  - 繰り返し出現するクラス名（カード候補の発見）
  - 既存セレクターのヒット数
  - tel:リンク数、詳細リンクのサンプル
  - 最初のカード候補のouterHTML（抜粋）
"""
import asyncio
import glob
import sys

from playwright.async_api import async_playwright

# (サイト名, URL, 描画待ち秒, 既存セレクター候補)
SITES = [
    ("マイナビバイト", "https://baito.mynavi.jp/tokyo/keibi/", 3,
     [".tabJobOfferCard", ".shopNameWrap", "[class*='JobOfferCard']", "article"]),
    ("enゲージ", "https://en-gage.net/user/search/?searchKey=%E8%AD%A6%E5%82%99&pref=13", 11,
     ["li.row.row--company", "[class*='row--company']", ".md_card", "article"]),
    ("求人BOX", "https://xn--pckua2a7gp15o89zb.com/%E8%AD%A6%E5%82%99%E3%81%AE%E4%BB%95%E4%BA%8B-%E6%9D%B1%E4%BA%AC%E9%83%BD", 3,
     [".p-result_card", "[class*='result_card']", "article"]),
    ("バイトル", "https://www.baitoru.com/tokyo/kensakuWord/%E8%AD%A6%E5%82%99/", 3,
     [".item-list__item", ".js-select-item", "[class*='job-item']", "article"]),
    ("Workin", "https://workin.jp/search/results?s%5Bkeyword%5D=%E8%AD%A6%E5%82%99&s%5Barea_ids%5D%5B%5D=13", 3,
     [".p-job-list__item", ".job-list__item", "[class*='job']", "article"]),
    ("ジョブメドレー", "https://job.jmedley.com/search/?pref_ids%5B%5D=13&keyword=%E8%AD%A6%E5%82%99", 3,
     [".c-job-list__item", ".job-item", "[class*='job']", "article"]),
    ("スタンバイ", "https://jp.stanby.com/search/?q=%E8%AD%A6%E5%82%99&location=%E6%9D%B1%E4%BA%AC%E9%83%BD", 4,
     ["[class*='JobCard']", "[class*='job-card']", ".result-item", "article"]),
]

REPEAT_JS = """
() => {
  const counts = {};
  document.querySelectorAll('*').forEach(el => {
    const c = el.getAttribute && el.getAttribute('class');
    if (c && c.trim()) counts[c] = (counts[c]||0)+1;
  });
  return Object.entries(counts).filter(([k,v]) => v >= 5)
    .sort((a,b) => b[1]-a[1]).slice(0, 20)
    .map(([k,v]) => v + '  ' + k);
}
"""


async def diagnose(context, name, url, wait_s, selectors):
    print(f"\n{'='*70}\n[{name}] {url}\n{'='*70}")
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=40000)
        await asyncio.sleep(wait_s)

        title = await page.title()
        final_url = page.url
        print(f"TITLE: {title}")
        print(f"FINAL_URL: {final_url}")

        for sel in selectors:
            try:
                n = len(await page.query_selector_all(sel))
            except Exception as e:
                n = f"ERR({e})"
            print(f"  SELECTOR {sel!r}: {n}")

        print("--- 繰り返しクラス (count>=5, 上位20) ---")
        try:
            rows = await page.evaluate(REPEAT_JS)
            for r in rows:
                print("  " + r)
        except Exception as e:
            print(f"  repeat-scan ERR: {e}")

        tel = len(await page.query_selector_all("a[href^='tel:']"))
        print(f"TEL_LINKS: {tel}")

        # 最初のカード候補のouterHTMLを抜粋
        first = None
        for sel in selectors:
            els = await page.query_selector_all(sel)
            if els:
                first = els[0]
                print(f"--- 最初の {sel!r} の outerHTML (先頭1800字) ---")
                break
        if first:
            html = await first.evaluate("el => el.outerHTML")
            print(html[:1800])
            print(f"--- innerText ---")
            txt = await first.inner_text()
            print(txt[:600])
        else:
            body = await page.evaluate("() => document.body.innerText")
            print("--- カード候補なし。body innerText 先頭800字 ---")
            print(body[:800])

    except Exception as e:
        print(f"[{name}] LOAD ERROR: {e}")
    finally:
        await page.close()


async def main():
    async with async_playwright() as p:
        candidates = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")
        executable = candidates[0] if candidates else None
        browser = await p.chromium.launch(
            headless=True,
            executable_path=executable,
            args=["--no-sandbox", "--disable-setuid-sandbox",
                  "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            locale="ja-JP", timezone_id="Asia/Tokyo",
            viewport={"width": 1280, "height": 900},
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"),
        )
        for name, url, wait_s, selectors in SITES:
            try:
                await diagnose(context, name, url, wait_s, selectors)
            except Exception as e:
                print(f"[{name}] 予期せぬエラー: {e}")
        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
