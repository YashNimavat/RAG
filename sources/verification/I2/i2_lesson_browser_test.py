"""Browser tests for study/lessons/I2_structure_chunking.html (Playwright + the pre-installed Chromium).

Run from rag_learning/:  uv run --with playwright python sources/verification/I2/i2_lesson_browser_test.py
Optional: CHROMIUM=/path/to/chrome. Opens the page as a plain file (offline). Prints one PASS/FAIL line per test.
"""
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
PAGE = (ROOT / "study" / "lessons" / "I2_structure_chunking.html").as_uri()
STYLES = ["reader", "hyper", "notebook", "textbook", "editor", "minimal", "catalogue"]
EXE = os.environ.get("CHROMIUM") or ("/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
                                      if Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome").exists() else None)
fails, n = 0, 0


def check(ok, label):
    global fails, n
    n += 1
    fails += not ok
    print(("PASS " if ok else "FAIL ") + label)


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=EXE) if EXE else p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    errors, external, fonts = [], [], []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("request", lambda r: external.append(r.url) if not r.url.startswith(("file:", "data:", "about:")) else
            (fonts.append(r.url) if r.url.endswith(".woff2") else None))
    page.goto(PAGE)
    page.wait_for_timeout(300)

    # structure
    hrefs = page.eval_on_selector_all("#toc a", "as => as.map(a => a.getAttribute('href'))")
    missing = [h for h in hrefs if not page.query_selector(h)]
    check(not missing, f"all {len(hrefs)} contents links have a target {missing}")
    for sid in ["answer", "theory", "formulas"] + [f"s{i}" for i in range(1, 14)] + ["f1", "f2", "f3", "f4", "verify", "apply", "llmops", "check", "sources"]:
        check(page.query_selector("#" + sid) is not None, f"section #{sid} exists")
    check(page.eval_on_selector_all("svg.chart", "s => s.every(x => x.querySelector('title') && x.querySelector('desc'))"),
          "every chart SVG has a title and a description")
    check("NB_BADGE" not in page.content() and "TOOL_EXAMPLE" not in page.content(), "no unfilled placeholders")

    # depth
    page.click(".seg button[data-depth=short]")
    check(page.eval_on_selector_all("section.full", "s => s.every(x => getComputedStyle(x).display === 'none')"), "Short hides the Full sections")
    page.click(".seg button[data-depth=full]")
    check(page.eval_on_selector_all("section.full", "s => s.every(x => getComputedStyle(x).display !== 'none')"), "Full shows the Full sections")
    page.click(".seg button[data-depth=short]")
    page.click("#toc a[href='#f2']")
    check(page.evaluate("document.documentElement.dataset.depth") == "full", "a Full-only contents link switches to Full")
    page.click(".seg button[data-depth=short]")

    # step 1 ruler
    read = lambda: page.inner_text("#rulerRead")
    check("keep them together" in read() and "pages 1–2" in read(), "ruler pp.1–2, L3: Coal kept with its body")
    page.click("#rulerArm button[data-a=v0]")
    check("splits them" in read(), "ruler pp.1–2, v0: Coal split from its body")
    page.click("#rulerPages button[data-p=b]")
    check("splits it" in read(), "ruler pp.12–13, v0: PPP sentence split")
    page.click("#rulerArm button[data-a=L3]")
    check("hold it whole" in read() and "26,553" in read() and "across the page break" in read(), "ruler pp.12–13, L3: PPP whole, across the break")
    page.click("#rulerArm button[data-a=L4]")
    check("hold it whole" in read() and "26,752" in read(), "ruler pp.12–13, L4: PPP whole in the PPP sub-section")

    # step 4 rules
    check("282" in page.inner_text("#ruleTab") and page.eval_on_selector_all("#ruleTree li.gone", "x => x.length") == 0, "rule explorer: size + bold finds 282, nothing missed")
    page.click("#ruleMode button[data-r=size]")
    t = page.inner_text("#ruleTab")
    check("90" in t and page.eval_on_selector_all("#ruleTree li.gone", "x => x.length") == 8, "rule explorer: size only finds 90; Chapter 6 loses its 8 sub-sections")
    check("Paris Agreement" in page.inner_text("#ruleTree li.gone:nth-of-type(4)") or
          page.eval_on_selector_all("#ruleTree li.gone", "x => x.some(l => l.textContent.startsWith('Paris Agreement'))"), "rule explorer: Paris Agreement is among the missed")

    # tables
    check(page.eval_on_selector_all("#repTab tr", "x => x.length") == 11, "11 repeated titles")
    check(page.eval_on_selector_all("#inspTab tr", "x => x.length") == 10, "10 inspected chunks")

    # step 8 histogram
    check(page.eval_on_selector_all("#histArm button", "x => x.length") == 6 and "117 chunks" in page.inner_text("#histRead"), "histogram: 6 arms, L3 117 chunks by default")
    page.click("#histArm button[data-h=L4]")
    check("209 chunks" in page.inner_text("#histRead") and "187 / 338 / 636" in page.inner_text("#histRead"), "histogram: L4 209 chunks, 187/338/636")
    page.click("#histArm button[data-h=v0]")
    check("97 chunks" in page.inner_text("#histRead"), "histogram: v0 97 chunks")

    # step 9 calculator
    def setv(sel, v):
        page.eval_on_selector(sel, "(e, v) => { e.value = v; e.dispatchEvent(new Event('input')); }", str(v))
    setv("#bsL", 2300); setv("#bsC", 1000)
    r = page.inner_text("#bsRead")
    check("n = ⌈2300 / 1000⌉ = 3" in r and "1000 + 1000 + 300" in r and "767 + 766 + 767" in r, f"balanced split 2,300 / 1,000: {r[:90]}")
    setv("#bsL", 1004)
    r = page.inner_text("#bsRead")
    check("1000 + 4" in r and "502 + 502" in r, "balanced split 1,004: cap-filling 1000 + 4, balanced 502 + 502")
    setv("#bsL", 1935)
    check("968 + 967" in page.inner_text("#bsRead") or "967 + 968" in page.inner_text("#bsRead"), "balanced split 1,935: ideal 967.5 each")

    # step 13
    check("8/8" in page.inner_text("#retTab") and page.eval_on_selector_all("#retTab tbody tr", "x => x.length") == 6, "retrieval table: 6 arms at fixed k")
    page.click("#retMode button[data-m=r]")
    check("0.917" in page.inner_text("#retTab") and "0.708" in page.inner_text("#retTab"), "retrieval table: MRR view shows 0.917 and 0.708")
    page.click("#retMode button[data-m=b]")
    check("6/8" in page.inner_text("#retTab"), "retrieval table: budget view shows the control's 6/8")

    # checklist + quick check
    check(page.eval_on_selector_all("#checklist input", "x => x.length") == 11, "checklist has S1–S11")
    page.click("#checklist input[data-i='2']")
    page.reload(); page.wait_for_timeout(200)
    check(page.is_checked("#checklist input[data-i='2']"), "checklist tick survives a reload")
    page.click("#checklist input[data-i='2']")
    for i, ok in enumerate([0, 1, 1]):
        page.click(f"input[name=q{i}][value='{(ok + 1) % 3}']")
        bad = "no" in page.get_attribute(f"#fb{i}", "class")
        page.click(f"input[name=q{i}][value='{ok}']")
        check(bad and "ok" in page.get_attribute(f"#fb{i}", "class"), f"quick check {i + 1}: wrong then right feedback")

    # controls
    page.evaluate("document.activeElement && document.activeElement.blur()")
    page.keyboard.press("t")
    check(page.evaluate("document.documentElement.dataset.toc") == "hidden", "T hides the contents")
    page.keyboard.press("t")
    check(page.evaluate("document.documentElement.dataset.toc") == "shown", "T shows the contents")
    page.click("#sidepos")
    check(page.evaluate("document.documentElement.dataset.side") == "right", "⇆ moves the contents right")
    page.click("#sidepos")
    page.evaluate("window.scrollTo(0, 3000)"); page.wait_for_timeout(200)
    check("show" in page.get_attribute("#totop", "class"), "↑ appears after scrolling")
    page.click("#color")
    check(page.evaluate("document.documentElement.dataset.theme") == "dark", "dark mode toggles")
    page.select_option("#style", "reader")
    page.reload(); page.wait_for_timeout(300)
    check(page.evaluate("document.documentElement.dataset.style") == "reader" and page.evaluate("document.documentElement.dataset.theme") == "dark",
          "theme and colour survive a reload")
    page.wait_for_timeout(300)
    check(any("literata" in f for f in fonts), "Literata loads from fonts/ (offline)")
    page.select_option("#style", "notebook"); page.click("#color")

    # phone width, every style, light and dark, Short and Full
    phone = browser.new_context(viewport={"width": 390, "height": 844})
    pp = phone.new_page()
    pp.on("pageerror", lambda e: errors.append(str(e)))
    worst = []
    for st in STYLES:
        for col in ("light", "dark"):
            for depth in ("short", "full"):
                pp.goto(f"{PAGE}?style={st}&color={col}&mode={depth}")
                pp.wait_for_timeout(120)
                over = pp.evaluate("document.documentElement.scrollWidth - innerWidth")
                if over > 0:
                    worst.append((st, col, depth, over))
    check(not worst, f"no sideways scroll at 390 px in 7 styles × 2 colours × 2 depths {worst[:4]}")
    pp.goto(PAGE)
    pp.click("#menu")
    check(pp.evaluate("document.body.classList.contains('side-open')"), "phone: Contents opens the drawer")
    pp.click("#main", position={"x": 300, "y": 400})
    check(not pp.evaluate("document.body.classList.contains('side-open')"), "phone: tapping the page closes the drawer")

    check(not external, f"no network request outside file: {external[:3]}")
    check(not errors, f"no console or page errors {errors[:3]}")
    browser.close()

print(f"\n{n - fails}/{n} PASS" + ("" if not fails else f" · {fails} FAIL"))
sys.exit(1 if fails else 0)
