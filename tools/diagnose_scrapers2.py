#!/usr/bin/env python3
"""
スクレイパー診断 v2: 詳細ページ構造と、壊れた媒体の正しい検索URLを調査する。
"""
import asyncio
import glob
import re

from playwright.async_api import async_playwright


async def dump_links(page, keywords):
    """ページ内のaリンクから keywords を含むものを抽出して返す。"""
    hrefs = await page.eval_on_selector_all(
        "a[href]", "els => els.map(e => ({h:e.getAttribute('href'), t:(e.innerText||'').trim().slice(0,20)}))"
    )
    out = []
    seen = set()
    for item in hrefs:
        h = item.get("h") or ""
        if any(k in h for k in keywords) and h not in seen:
            seen.add(h)
            out.append(f"{h}   « {item.get('t','')}")
        if len(out) >= 25:
            break
    return out


async def main():
    async with async_playwright() as p:
        candidates = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")
        executable = candidates[0] if candidates else None
        browser = await p.chromium.launch(
            headless=True, executable_path=executable,
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

        # ① マイナビ: 業種カテゴリURL調査 + 詳細ページ構造
        print("\n######## マイナビ: トップのカテゴリリンク ########")
        page = await context.new_page()
        try:
            await page.goto("https://baito.mynavi.jp/tokyo/", wait_until="domcontentloaded", timeout=40000)
            await asyncio.sleep(3)
            for l in await dump_links(page, ["/tokyo/", "shokushu", "job", "keibi", "kategori", "cat"]):
                print("  " + l)
        except Exception as e:
            print("  ERR", e)
        finally:
            await page.close()

        print("\n######## マイナビ: 詳細ページの電話番号・住所 ########")
        page = await context.new_page()
        try:
            await page.goto("https://baito.mynavi.jp/tokyo/keibi/", wait_until="domcontentloaded", timeout=40000)
            await asyncio.sleep(3)
            card = await page.query_selector(".tabJobOfferCard a[href*='/job-']")
            href = await card.get_attribute("href") if card else None
            print("  detail href:", href)
            if href:
                dp = await context.new_page()
                await dp.goto("https://baito.mynavi.jp" + href, wait_until="domcontentloaded", timeout=40000)
                await asyncio.sleep(3)
                body = await dp.evaluate("() => document.body.innerText")
                # 電話番号・住所らしき行を抽出
                for line in body.split("\n"):
                    t = line.strip()
                    if re.search(r"0\d{1,4}-\d{1,4}-\d{3,4}", t) or t.startswith("〒") or ("東京都" in t and re.search(r"\d", t)):
                        print("  >>", t[:90])
                # 会社名・事業者情報ラベル周辺
                idx = body.find("事業者")
                if idx > 0:
                    print("  [事業者周辺]", body[idx:idx+120].replace("\n", " / "))
                await dp.close()
        except Exception as e:
            print("  ERR", e)
        finally:
            await page.close()

        # ② 求人BOX: 詳細ページ電話番号
        print("\n######## 求人BOX: 詳細ページ構造 ########")
        page = await context.new_page()
        try:
            await page.goto("https://xn--pckua2a7gp15o89zb.com/%E8%AD%A6%E5%82%99%E3%81%AE%E4%BB%95%E4%BA%8B-%E6%9D%B1%E4%BA%AC%E9%83%BD",
                            wait_until="domcontentloaded", timeout=40000)
            await asyncio.sleep(3)
            hrefs = await page.eval_on_selector_all(
                "a[href*='uaid=']", "els => els.map(e => e.getAttribute('href'))")
            uaid = ""
            for h in hrefs:
                m = re.search(r"[?&]uaid=([0-9a-z]+)", h or "")
                if m:
                    uaid = m.group(1); break
            print("  uaid:", uaid)
            if uaid:
                dp = await context.new_page()
                durl = "https://xn--pckua2a7gp15o89zb.com/jb/" + uaid
                await dp.goto(durl, wait_until="domcontentloaded", timeout=40000)
                await asyncio.sleep(2)
                body = await dp.evaluate("() => document.body.innerText")
                print("  detail url:", durl, "| title:", await dp.title())
                for line in body.split("\n"):
                    t = line.strip()
                    if re.search(r"(TEL|電話|℡)", t) or re.search(r"0\d{1,4}-\d{1,4}-\d{3,4}", t) or (t.startswith("東京都") and re.search(r"\d", t)):
                        print("  >>", t[:90])
                await dp.close()
        except Exception as e:
            print("  ERR", e)
        finally:
            await page.close()

        # ③ 壊れた媒体の正しい検索URL発見（トップページのリンク調査）
        for name, top, kws in [
            ("ジョブメドレー", "https://job-medley.com/", ["search", "ans", "cs", "pref", "tokyo", "13"]),
            ("Workin", "https://workin.jp/", ["search", "list", "area", "tokyo", "13", "kensaku", "jobs"]),
            ("スタンバイ", "https://jp.stanby.com/", ["search", "tokyo", "q=", "kw", "jobs", "result"]),
            ("バイトル", "https://www.baitoru.com/", ["kanto", "tokyo", "list", "job", "kensaku"]),
        ]:
            print(f"\n######## {name}: トップ {top} ########")
            page = await context.new_page()
            try:
                await page.goto(top, wait_until="domcontentloaded", timeout=40000)
                await asyncio.sleep(3)
                print("  TITLE:", await page.title(), "| URL:", page.url)
                for l in await dump_links(page, kws):
                    print("  " + l)
            except Exception as e:
                print("  ERR", e)
            finally:
                await page.close()

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
