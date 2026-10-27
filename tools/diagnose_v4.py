#!/usr/bin/env python3
"""診断v4: マイナビバイトの職種別URL（ss-/ssm-形式）と検索URLを調べる。結果は注記に出す。"""
import asyncio, glob, re
from playwright.async_api import async_playwright


def emit(title, lines):
    msg = "\n".join(lines)[:6000].replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::notice title={title}::{msg}")


async def links(page, pat):
    hs = await page.eval_on_selector_all(
        "a[href]", "els => els.map(e => [e.getAttribute('href'), (e.innerText||'').trim().replace(/\\s+/g,' ').slice(0,30)])")
    out, seen = [], set()
    for h, t in hs:
        if h and re.search(pat, h) and h not in seen:
            seen.add(h); out.append(f"{h} « {t}")
    return out


async def cards_summary(page):
    cs = await page.query_selector_all(".tabJobOfferCard")
    out = [f"cards={len(cs)}"]
    for c in cs[:5]:
        n = await c.query_selector(".shopName")
        name = (await n.inner_text()).strip() if n else ""
        t = (await c.inner_text()).strip().replace("\n", " ")[:70]
        out.append(f"  {name[:30]} | {t}")
    return out


async def main():
    async with async_playwright() as p:
        cand = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")
        b = await p.chromium.launch(headless=True, executable_path=cand[0] if cand else None,
                                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        ctx = await b.new_context(locale="ja-JP", timezone_id="Asia/Tokyo", viewport={"width": 1280, "height": 900},
                                  user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        pg = await ctx.new_page()
        for i, u in enumerate(["https://baito.mynavi.jp/tokyo/", "https://baito.mynavi.jp/tokyo/all/",
                               "https://baito.mynavi.jp/shokushu/", "https://baito.mynavi.jp/tokyo/ss-9/"]):
            try:
                await pg.goto(u, wait_until="domcontentloaded", timeout=40000); await asyncio.sleep(3)
                ls = await links(pg, r"/ss-\d+|/ssm-\d+|shokushu|/kd-\d+")
                emit(f"MYNAVI_SS_{i}", [f"{u} -> {pg.url}"] + ls[:120])
            except Exception as e:
                emit(f"MYNAVI_SS_{i}", [f"ERR {u} {e}"])
        res = []
        for u in ["https://baito.mynavi.jp/tokyo/?freeWord=警備",
                  "https://baito.mynavi.jp/tokyo/all/?freeWord=警備",
                  "https://baito.mynavi.jp/tokyo/fw-警備/",
                  "https://baito.mynavi.jp/tokyo/all/?keyword=警備"]:
            try:
                await pg.goto(u, wait_until="domcontentloaded", timeout=40000); await asyncio.sleep(3)
                res.append(f"{u} -> {pg.url} | {await pg.title()}")
                res += await cards_summary(pg)
            except Exception as e:
                res.append(f"ERR {u} {e}")
        emit("MYNAVI_SEARCH", res)
        # 検索フォームの構造
        try:
            await pg.goto("https://baito.mynavi.jp/tokyo/all/", wait_until="domcontentloaded", timeout=40000); await asyncio.sleep(3)
            forms = await pg.eval_on_selector_all("form", "fs => fs.map(f => (f.getAttribute('action')||'') + ' :: ' + Array.from(f.querySelectorAll('input[name],select[name]')).map(i=>i.name).join(','))")
            emit("MYNAVI_FORMS", forms[:20])
        except Exception as e:
            emit("MYNAVI_FORMS", [f"ERR {e}"])
        await b.close()

asyncio.run(main())
