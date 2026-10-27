#!/usr/bin/env python3
"""診断v5: マイナビバイトの職種カテゴリ番号（/tokyo/ss-N/）の中身を調べる。結果は注記に出す。"""
import asyncio, glob, re
from playwright.async_api import async_playwright


def emit(title, lines):
    msg = "\n".join(lines)[:6000].replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::notice title={title}::{msg}")


async def main():
    async with async_playwright() as p:
        cand = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")
        b = await p.chromium.launch(headless=True, executable_path=cand[0] if cand else None,
                                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        ctx = await b.new_context(locale="ja-JP", timezone_id="Asia/Tokyo", viewport={"width": 1280, "height": 900},
                                  user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        pg = await ctx.new_page()
        out = []
        for n in range(1, 21):
            u = f"https://baito.mynavi.jp/tokyo/ss-{n}/"
            try:
                await pg.goto(u, wait_until="load", timeout=40000); await asyncio.sleep(2)
                cs = await pg.query_selector_all(".tabJobOfferCard")
                first = ""
                if cs:
                    first = (await cs[0].inner_text()).strip().replace("\n", " ")[:50]
                out.append(f"ss-{n} -> {pg.url.replace('https://baito.mynavi.jp','')} | {(await pg.title())[:40]} | cards={len(cs)} | {first}")
            except Exception as e:
                out.append(f"ss-{n} ERR {str(e)[:80]}")
        emit("MYNAVI_SS_LIST", out)
        out = []
        for s in ["keibi", "driver", "kaigo", "food", "seizou"]:
            try:
                await pg.goto(f"https://baito.mynavi.jp/shokushu/{s}/", wait_until="load", timeout=40000); await asyncio.sleep(2)
                hs = await pg.eval_on_selector_all("a[href]", "els => els.map(e => [e.getAttribute('href'), (e.innerText||'').trim().replace(/\\s+/g,' ').slice(0,25)])")
                got = [f"{h} « {t}" for h, t in hs if h and "tokyo" in h and ("ss-" in h)][:8]
                out.append(f"## {s}: " + " || ".join(got))
            except Exception as e:
                out.append(f"## {s} ERR {str(e)[:80]}")
        emit("MYNAVI_SHOKUSHU", out)
        await b.close()

asyncio.run(main())
