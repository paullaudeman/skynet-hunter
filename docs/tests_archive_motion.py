"""Headless check of docs/archive-motion.html: every stop settles inside the screen at two
window sizes, nothing overflows, the AWS toggle moves the token, no page errors.

    python docs/tests_archive_motion.py http://127.0.0.1:8793/archive-motion.html
"""
import sys
from playwright.sync_api import sync_playwright

url = sys.argv[1]
fails, errs = [], []
with sync_playwright() as p:
    b = p.chromium.launch()
    for w, h in [(1440, 900), (1280, 720)]:
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url); pg.evaluate("localStorage.clear()"); pg.reload()
        pg.click("#goSilent"); pg.wait_for_timeout(1500)
        n = pg.evaluate("document.querySelectorAll('.col').length")
        for i in range(n):
            if i: pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(2600)
            pg.evaluate("document.getAnimations().forEach(a=>{ if (a.effect.getTiming().iterations!==Infinity) a.finish() })")
            m = pg.evaluate("""() => { const c = document.querySelector('.col.on'), mid = c.querySelector('.band.mid'),
                 pn = c.querySelector('.panel').getBoundingClientRect(), st = document.getElementById('strip').getBoundingClientRect(),
                 t = document.getElementById('token').getBoundingClientRect();
                 return {label: c.getAttribute('aria-label'), over: mid.scrollHeight - mid.clientHeight, bottom: pn.bottom - st.bottom,
                         right: pn.right - innerWidth, left: pn.left, w: pn.width, tokenIn: t.left >= pn.left - 30 && t.left <= pn.right}; }""")
            bad = [k for k, v in (("overflow", m["over"] > 2), ("below", m["bottom"] > 0), ("offscreen", m["right"] > 1 or m["left"] < -1), ("token", not m["tokenIn"])) if v]
            print(f"{w}x{h} {i+1:02d} {m['label']:9} w={m['w']:.0f} overflow={m['over']} {'FAIL '+','.join(bad) if bad else 'ok'}")
            if bad: fails.append((w, i, bad))
            if w == 1440 and m["label"] in ("gate", "corpus"): pg.screenshot(path=f"/private/tmp/claude-501/-Users-paul-dev/8b2bbd45-8840-49ab-8ec6-d8c5ddfab078/scratchpad/am-{m['label']}.png")
        if w == 1440:
            y0 = pg.evaluate("document.getElementById('token').getBoundingClientRect().top")
            pg.keyboard.press("ArrowLeft"); pg.wait_for_timeout(2600)  # target -> grid (shared), go to a split stop
            for _ in range(4): pg.keyboard.press("ArrowLeft"); pg.wait_for_timeout(2600)
            lab = pg.evaluate("document.querySelector('.col.on').getAttribute('aria-label')")
            a = pg.evaluate("document.getElementById('token').getBoundingClientRect().top")
            pg.click("label.chk:has(#aws)"); pg.wait_for_timeout(700)
            bb = pg.evaluate("document.getElementById('token').getBoundingClientRect().top")
            lit = pg.evaluate("[...document.querySelectorAll('.col.on svg.trk path')].map(p=>p.dataset.lane+':'+p.getAttribute('class')).join(' ')")
            print(f"aws toggle at {lab}: token y {a:.0f} -> {bb:.0f}; {lit}")
            if not bb > a + 50: fails.append(("aws-toggle", lab))
            pg.keyboard.press("o"); pg.wait_for_timeout(900)
            pg.screenshot(path="/private/tmp/claude-501/-Users-paul-dev/8b2bbd45-8840-49ab-8ec6-d8c5ddfab078/scratchpad/am-whole.png")
            pg.evaluate("localStorage.clear()")
        pg.close()
    b.close()
print("page errors:", errs); print("FAILS:", fails or "none")
sys.exit(1 if fails or errs else 0)
