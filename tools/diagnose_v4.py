#!/usr/bin/env python3
"""診断v6: マイナビバイト ss-17/ss-18 の中身、ページ送りの形式、「他の店舗」カードの社名欄を確認する。"""
import asyncio, glob
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
        for u in ["/tokyo/ss-17/", "/tokyo/ss-18/", "/tokyo/ss-1/"]:
            await pg.goto("https://baito.mynavi.jp" + u, wait_until="load", timeout=40000); await asyncio.sleep(2)
            out.append(f"## {u} {pg.url} | {await pg.title()}")
            hs = await pg.eval_on_selector_all("a[href]", "els => els.map(e => [e.getAttribute('href'), (e.innerText||'').trim().replace(/\\s+/g,' ').slice(0,20)])")
            ssm = sorted({f"{h} « {t}" for h, t in hs if h and "/ssm-" in h and u.strip('/').split('/')[-1] in h})[:25]
            pages = sorted({h for h, t in hs if h and ("pageNo" in h or "/pg" in h or "page" in h.lower())})[:6]
            out.append("  ssm: " + " || ".join(ssm))
            out.append("  pages: " + " || ".join(pages))
            for c in (await pg.query_selector_all(".tabJobOfferCard"))[:6]:
                n = await c.query_selector(".shopName"); w = await c.query_selector(".shopNameWrap")
                nt = (await n.inner_text()).replace("\n", "⏎") if n else "-"
                wt = (await w.inner_text()).replace("\n", "⏎") if w else "-"
                out.append(f"  shopName={nt[:40]} | wrap={wt[:50]}")
        emit("MYNAVI_V6", out)
        await b.close()

asyncio.run(main())
