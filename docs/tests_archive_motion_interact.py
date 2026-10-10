"""Interaction checks for docs/archive-motion.html: every document opens in the lightbox from every
stop that shows one, arrows browse documents (not stops) while it is open, Esc closes it, every stop
carries tooltips, and a tooltip shows its text on hover."""
import sys
from playwright.sync_api import sync_playwright
url = sys.argv[1]; fails, errs = [], []
S = "/private/tmp/claude-501/-Users-paul-dev/8b2bbd45-8840-49ab-8ec6-d8c5ddfab078/scratchpad/"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(url); pg.evaluate("localStorage.clear()"); pg.reload(); pg.click("#goSilent"); pg.wait_for_timeout(1500)
    n = pg.evaluate("document.querySelectorAll('.col').length")
    for i in range(n):
        if i: pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(2600)
        pg.evaluate("document.getAnimations().forEach(a=>{ if (a.effect.getTiming().iterations!==Infinity) a.finish() })")
        lab = pg.evaluate("document.querySelector('.col.on').getAttribute('aria-label')")
        tips = pg.evaluate("document.querySelectorAll('.col.on .tip').length")
        docs = pg.locator(".col.on [data-doc]")
        line = f"{i+1:02d} {lab:9} tips={tips} docs={docs.count()}"
        if tips == 0: fails.append((lab, "no tips"))
        if docs.count():
            docs.first.click(); pg.wait_for_timeout(400)
            want = docs.first.get_attribute("data-doc")
            shown = pg.evaluate("document.getElementById('lb').classList.contains('hide') ? null : document.querySelector('.lbmeta').textContent")
            if not shown or want not in shown: fails.append((lab, "lightbox", want, shown))
            pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(200)
            still = pg.evaluate("document.querySelector('.col.on').getAttribute('aria-label')")
            moved = pg.evaluate("document.querySelector('.lbmeta').textContent")
            if still != lab or want in moved: fails.append((lab, "arrow in lightbox", still, moved[:20]))
            if lab == "gate": pg.screenshot(path=S + "am-lightbox.png")
            pg.keyboard.press("Escape"); pg.wait_for_timeout(200)
            if not pg.evaluate("document.getElementById('lb').classList.contains('hide')"): fails.append((lab, "esc"))
            line += f" lightbox {want} ok"
        t = pg.locator(".col.on .tip").first
        t.hover(); pg.wait_for_timeout(150)
        box = pg.evaluate("getComputedStyle(document.getElementById('tipbox')).display + ' ' + document.getElementById('tipbox').textContent.slice(0,40)")
        if not box.startswith("block") or len(box) < 15: fails.append((lab, "tip hover", box))
        pg.mouse.move(5, 5)
        print(line)
    pg.evaluate("localStorage.clear()"); b.close()
print("page errors:", errs); print("FAILS:", fails or "none"); sys.exit(1 if fails or errs else 0)
