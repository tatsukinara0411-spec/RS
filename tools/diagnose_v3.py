#!/usr/bin/env python3
"""
スクレイパー診断 v3: マイナビバイトの社名・業種URL、求人BOXの広告行・電話番号の出所を調べる。
結果は GitHub Actions の注記(annotation)として出力する（ログを開かなくても実行結果画面で読める）。
"""
import asyncio
import glob
import re

from playwright.async_api import async_playwright

OUT = []


def emit(title, lines):
    msg = "\n".join(lines)[:6000]
    msg = msg.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::notice title={title}::{msg}")


async def mynavi(context):
    lines = []
    page = await context.new_page()
    try:
        await page.goto("https://baito.mynavi.jp/tokyo/", wait_until="domcontentloaded", timeout=40000)
        await asyncio.sleep(3)
        links = await page.eval_on_selector_all(
            "a[href]", "els => els.map(e => [e.getAttribute('href'), (e.innerText||'').trim().slice(0,25)])")
        seen = set()
        for h, t in links:
            if any(k in t for k in ["警備", "ドライバー", "配送", "飲食", "販売", "介護", "建設", "土木"]) and h not in seen:
                seen.add(h)
                lines.append(f"LINK {h} « {t}")
            if len(seen) >= 30:
                break
    except Exception as e:
        lines.append(f"ERR top {e}")
    finally:
        await page.close()
    emit("MYNAVI_LINKS", lines)

    for path in ["keibi", "unso", "gaishoku"]:
        lines = []
        page = await context.new_page()
        try:
            url = f"https://baito.mynavi.jp/tokyo/{path}/"
            await page.goto(url, wait_until="domcontentloaded", timeout=40000)
            await asyncio.sleep(3)
            lines.append(f"REQ {url} -> FINAL {page.url}")
            lines.append(f"TITLE {await page.title()}")
            cards = await page.query_selector_all(".tabJobOfferCard")
            lines.append(f"cards={len(cards)}")
            for c in cards[:4]:
                for sel in [".shopName", ".shopNameWrap", "[class*='shopName']", "[class*='company']"]:
                    el = await c.query_selector(sel)
                    if el:
                        t = (await el.inner_text()).strip().replace("\n", "⏎")
                        lines.append(f"  {sel} = {t[:60]}")
                html = await c.inner_html()
                m = re.findall(r'class="([^"]*(?:shop|company|name|title|job)[^"]*)"', html, re.I)
                lines.append("  classes: " + ", ".join(sorted(set(m))[:20]))
                lines.append("  ---")
        except Exception as e:
            lines.append(f"ERR {path} {e}")
        finally:
            await page.close()
        emit(f"MYNAVI_{path}", lines)


async def kyujinbox(context):
    base = "https://xn--pckua2a7gp15o89zb.com"
    lines = []
    detail = []
    page = await context.new_page()
    try:
        url = f"{base}/警備の仕事-東京都"
        await page.goto(url, wait_until="domcontentloaded", timeout=40000)
        await asyncio.sleep(3)
        cards = await page.query_selector_all(".p-result_card")
        lines.append(f"cards={len(cards)}")
        for c in cards[:12]:
            cls = await c.get_attribute("class")
            txt = (await c.inner_text()).strip().split("\n")
            txt = [t.strip() for t in txt if t.strip()][:4]
            pr = await c.query_selector("[class*='pr'], [class*='PR'], [class*='ad'], [class*='sponsor']")
            prc = (await pr.get_attribute("class")) if pr else ""
            lines.append(f"[{cls}] PRel={prc} | " + " / ".join(x[:40] for x in txt))
            hrefs = await c.eval_on_selector_all("a[href*='uaid=']", "els => els.map(e => e.getAttribute('href'))")
            m = re.search(r"[?&]uaid=([0-9a-z]+)", (hrefs or [""])[0] or "")
            if m and len(detail) < 4:
                detail.append(f"{base}/jb/{m.group(1)}")
    except Exception as e:
        lines.append(f"ERR {e}")
    finally:
        await page.close()
    emit("KYUJINBOX_CARDS", lines)

    lines = []
    for d in detail:
        page = await context.new_page()
        try:
            await page.goto(d, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            body = await page.evaluate("() => document.body.innerText")
            lines.append(f"URL {d} -> {page.url[:80]}")
            for m in re.finditer(r"0\d{1,4}-\d{1,4}-\d{3,4}", body):
                s = max(0, m.start() - 40)
                lines.append("  TEL: " + body[s:m.end() + 30].replace("\n", "⏎"))
            for lab in ["会社名", "企業名", "事業所", "会社情報", "応募先"]:
                i = body.find(lab)
                if i >= 0:
                    lines.append(f"  [{lab}] " + body[i:i + 80].replace("\n", "⏎"))
        except Exception as e:
            lines.append(f"ERR {d} {e}")
        finally:
            await page.close()
    emit("KYUJINBOX_DETAIL", lines)


async def main():
    async with async_playwright() as p:
        candidates = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")
        browser = await p.chromium.launch(
            headless=True, executable_path=candidates[0] if candidates else None,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            locale="ja-JP", timezone_id="Asia/Tokyo", viewport={"width": 1280, "height": 900},
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
        )
        await mynavi(context)
        await kyujinbox(context)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
