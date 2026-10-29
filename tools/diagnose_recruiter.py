#!/usr/bin/env python3
"""
診断：求人の詳細ページに採用担当者の名前がどのくらい載っているかを数える。
リポジトリが公開のため、注記には件数と「型」だけを出し、名前そのものは ◯◯ に伏せる。
"""
import asyncio, glob, re
from collections import Counter
from playwright.async_api import async_playwright

KB = "https://xn--pckua2a7gp15o89zb.com"
KB_WORDS = ["警備", "ドライバー", "飲食", "販売", "介護", "建設"]
MN_PATHS = ["ss-18", "ss-12", "ss-1", "ss-3", "ss-9/ssm-117", "ss-17"]
NAME = r"([一-龥々]{1,4}(?:\s?[一-龥々ぁ-んァ-ヶ]{1,4})?)"
PATS = [
    ("採用担当：名前", re.compile(r"採用担当(?:者)?\s*[：:／/]\s*" + NAME)),
    ("担当（者）：名前", re.compile(r"(?<!採用)担当(?:者)?\s*[：:／/]\s*" + NAME)),
    ("（担当 名前）", re.compile(r"[（(]\s*担当(?:者)?\s*[：:／/]?\s*" + NAME + r"\s*[)）]")),
    ("名前まで（お気軽に）", re.compile(NAME + r"\s*(?:まで|宛)(?:お気軽に|ご連絡|お電話)")),
]
GENERIC = {"人事", "人事部", "採用", "総務", "本部", "店長", "担当", "係", "事務局", "センター", "営業", "管理", "責任者", "採用係"}


def emit(title, lines):
    msg = "\n".join(lines)[:6000].replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::notice title={title}::{msg}")


def classify(body):
    hits = []
    for label, p in PATS:
        for m in p.finditer(body):
            name = m.group(1).strip()
            if name in GENERIC or any(g in name for g in ("人事", "採用", "総務", "部", "課", "係", "店長", "センター")):
                continue
            s = max(0, m.start() - 8)
            ctx = body[s:m.end() + 6].replace(name, "◯" * len(name)).replace("\n", " ")
            hits.append((label, ctx))
    return hits


async def scan(ctx, site, urls):
    page = await ctx.new_page()
    n = found = 0
    kinds = Counter()
    samples = []
    for u in urls:
        try:
            await page.goto(u, wait_until="domcontentloaded", timeout=25000)
            await asyncio.sleep(1.2)
            body = await page.evaluate("() => document.body.innerText")
        except Exception:
            continue
        n += 1
        h = classify(body)
        if h:
            found += 1
            kinds[h[0][0]] += 1
            if len(samples) < 8:
                samples.append(f"  例: [{h[0][0]}] …{h[0][1]}…")
    await page.close()
    pct = f"{found / n * 100:.0f}%" if n else "-"
    return [f"{site}: 詳細ページ {n}件中 担当者名らしきもの {found}件（{pct}）", f"  型の内訳 {dict(kinds)}"] + samples


async def main():
    async with async_playwright() as p:
        cand = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")
        b = await p.chromium.launch(headless=True, executable_path=cand[0] if cand else None,
                                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        ctx = await b.new_context(locale="ja-JP", timezone_id="Asia/Tokyo", viewport={"width": 1280, "height": 900},
                                  user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        pg = await ctx.new_page()
        kb_urls = []
        for w in KB_WORDS:
            try:
                await pg.goto(f"{KB}/{w}の仕事-東京都", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
                hrefs = await pg.eval_on_selector_all(".p-result_card a[href*='uaid=']", "els => els.map(e => e.getAttribute('href'))")
                ids = []
                for h in hrefs:
                    m = re.search(r"[?&]uaid=([0-9a-z]+)", h or "")
                    if m and m.group(1) not in ids:
                        ids.append(m.group(1))
                kb_urls += [f"{KB}/jb/{i}" for i in ids[:10]]
            except Exception:
                pass
        mn_urls = []
        for path in MN_PATHS:
            try:
                await pg.goto(f"https://baito.mynavi.jp/tokyo/{path}/", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
                hrefs = await pg.eval_on_selector_all(".tabJobOfferCard a[href*='/job-']", "els => els.map(e => e.getAttribute('href'))")
                seen = []
                for h in hrefs:
                    if h and h not in seen:
                        seen.append(h)
                mn_urls += ["https://baito.mynavi.jp" + h if h.startswith("/") else h for h in seen[:5]]
            except Exception:
                pass
        await pg.close()
        out = await scan(ctx, "求人BOX", kb_urls)
        out += await scan(ctx, "マイナビバイト", mn_urls)
        emit("RECRUITER", out)
        await b.close()

asyncio.run(main())
