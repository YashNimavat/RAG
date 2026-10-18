// Browser tests for study/lessons/I5_contextual_headers.html (Playwright + Chromium).
// Run from rag_learning/:  NODE_PATH=<global node_modules> node sources/verification/I5/i5_lesson_test.js [kit-base-url]
// Saved output: sources/verification/I5/out_i5_lesson_test.txt
// Without a kit URL it opens the page as a file (the offline view). With one (e.g. http://127.0.0.1:8765) it also
// checks the study-kit view: fonts load from /lesson/fonts/, kit links become routes, book links go to /book/.
const { chromium } = require("playwright");
const path = require("path");

const WS = path.resolve(__dirname, "..", "..", "..");
const FILE = "file://" + path.join(WS, "study", "lessons", "I5_contextual_headers.html");
const KIT = process.argv[2] || "";
const STYLES = ["reader", "hyper", "notebook", "textbook", "editor", "minimal", "catalogue"];
let pass = 0, fail = 0;
function check(name, ok, detail = "") {
  if (ok) pass++; else fail++;
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail ? "  — " + detail : ""}`);
}

(async () => {
  const browser = await chromium.launch();
  const errors = [];
  const newPage = async (opts = {}) => {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, ...opts });
    const p = await ctx.newPage();
    p.on("console", m => { if (m.type() === "error") errors.push(m.text()); });
    p.on("pageerror", e => errors.push(String(e)));
    return p;
  };

  // ---------------------------------------------------------------- structure, depth, panel
  let p = await newPage();
  await p.goto(FILE);
  check("title is a 2-4 word name", (await p.title()) === "Contextual Chunk Headers");
  const tocIds = await p.$$eval("#toc a", as => as.map(a => a.getAttribute("href").slice(1)));
  const missing = await p.evaluate(ids => ids.filter(i => !document.getElementById(i)), tocIds);
  check("every contents link has a target", missing.length === 0, missing.join(","));
  check("contents has 20 links (3 + 14 steps + 3)", tocIds.length === 20, String(tocIds.length));
  const spec = ["anon", "fields", "tree", "path", "assign", "info", "dilute", "trunc", "measure", "llm", "cache", "claims", "repo", "beyond"];
  check("step ids match the build spec", JSON.stringify(tocIds.slice(3, 17)) === JSON.stringify(spec));
  check("theory has 12 linked ideas", (await p.$$eval("#theory .chain > li", l => l.length)) === 12);
  const goBad = await p.$$eval("#theory .go", as => as.filter(a => !document.getElementById(a.getAttribute("href").slice(1))).length);
  check("every theory link resolves", goBad === 0);
  check("Short hides the Full parts", await p.$eval("#repo", e => getComputedStyle(e).display === "none"));
  await p.click('.top .seg button[data-depth="full"]');
  check("Full shows the Full parts", await p.$eval("#repo", e => getComputedStyle(e).display !== "none"));
  await p.click('.top .seg button[data-depth="short"]');
  await p.click('#rulePick button[data-rule="major"]');
  check("a content toggle does not change the reading depth", (await p.evaluate(() => document.documentElement.dataset.depth)) === "short");
  await p.click("#sidepos");
  check("⇆ moves the panel right", (await p.evaluate(() => document.documentElement.dataset.side)) === "right");
  await p.click("#sidepos");
  await p.keyboard.press("t");
  check("T hides the panel", (await p.evaluate(() => document.documentElement.dataset.toc)) === "hidden");
  await p.keyboard.press("t");
  check("T shows it again", (await p.evaluate(() => document.documentElement.dataset.toc)) === "shown");
  await p.evaluate(() => window.scrollTo(0, 3000)); await p.waitForTimeout(300);
  check("↑ button appears after scrolling", await p.$eval("#totop", e => e.classList.contains("show")));
  await p.click('#toc a[href="#beyond"]'); await p.waitForTimeout(200);
  check("a Full-only contents link switches to Full", (await p.evaluate(() => document.documentElement.dataset.depth)) === "full");
  check("kit-only links are removed offline", (await p.$$(".kitonly")).length === 0);
  check("kit links become plain paths offline", (await p.$$("a[data-kit]")).length === 0);
  const book = await p.$$eval("a[data-book]", as => as.map(a => a.href));
  check("book links point at Chapter 7 pages", book.length >= 6 && book.every(h => /chapter%207\.pdf#page=\d+$/.test(h)), String(book.length));
  check("no placeholder left", !(await p.content()).includes("{{"));

  // ---------------------------------------------------------------- charts and interactive parts
  check("heading chart: one bar group per page", (await p.$$eval("#treeChart rect title", t => t.length)) >= 33);
  check("heading chart marks 14 reused-name pages", (await p.$$eval("#treeChart text", t => t.filter(x => x.textContent === "▲").length)) === 14);
  check("magnet chart draws 3 lines", (await p.$$eval("#magnetChart polyline", l => l.length)) === 3);
  const expect = {
    "68|start": ["Chapter 15: Climate Change and Technology › Carbon Capture and Utilization › Direct Air Capture (DAC)", "✗"],
    "68|major": ["Chapter 16: Global Cooperation and Governance › International Agreements › Paris Agreement", "✓"],
    "27|start": ["Understanding Climate Change › Chapter 6: Global and Local Climate Action<", "✗"],
    "27|major": ["International Collaboration › Paris Agreement", "✓"],
    "34|start": ["Emerging Technologies › Blockchain for Climate Action", "✓"],
    "34|major": ["Policy and Governance › Integrated Climate Policies", "✗"],
    "34|all": ["| Bioengineering | Policy and Governance | Integrated Climate Policies | International Cooperation", "✓"]};
  for (const [k, [txt, mark]] of Object.entries(expect)) {
    const [c, r] = k.split("|");
    await p.click(`#chPick button[data-ch="${c}"]`); await p.click(`#rulePick button[data-rule="${r}"]`);
    const html = await p.$eval("#ruleRead", e => e.innerHTML.replace(/&amp;/g, "&"));
    check(`rule explorer: chunk ${c}, ${r}`, html.includes(txt) && html.includes(mark));
  }
  check("rule explorer bar has the chunk's segments", (await p.$$eval("#chBar span", s => s.length)) === 5);
  check("share default s = 0.112", (await p.textContent("#shareRead")).includes("0.112"));
  await p.$eval("#cTok", e => { e.value = 64; e.dispatchEvent(new Event("input")); });
  check("share on a 400-character chunk = 0.229", (await p.textContent("#shareRead")).includes("0.229"));
  check("truncation: 27 + 182 = 209 fits", /27 \+ 182 = 209.*fits/.test(await p.textContent("#truncRead")));
  await p.click('#truncPick button[data-h="100"]');
  check("truncation: 100 + 182 = 282, last 26 cut", /282.*over by 26.*last 26/.test(await p.textContent("#truncRead")));
  check("truncation ruler shades the cut tail", (await p.$$("#ruler .cut")).length === 1);
  let cost = await p.textContent("#costRead");
  check("cost: Haiku uncached $0.1367 and cached $0.0261", cost.includes("$0.1367") && cost.includes("$0.0261") && cost.includes("5.2×"));
  await p.selectOption("#cM", "groq");
  cost = await p.textContent("#costRead");
  check("cost: Groq cached $0.0542 and the TPM refusal", cost.includes("$0.0542") && cost.includes("refused"));
  await p.selectOption("#cM", "haiku"); await p.fill("#cD", "400"); await p.$eval("#cD", e => e.dispatchEvent(new Event("input")));
  check("cost: a prefix below 512 tokens is not cached", (await p.textContent("#costRead")).includes("below the 512-token minimum"));
  check("cache key: chunk-only key serves 96 of 97", (await p.textContent("#keyRead")).includes("96 of 97"));
  await p.click('#keyPick button[data-key="full"]');
  check("cache key: full key serves 0 of 97", (await p.textContent("#keyRead")).includes("0 of 97"));
  check("vendor numbers: −2.0 points, −35.1%", /-2\.0 points.*-35\.1%/.test(await p.textContent("#vRead")));
  check("checklist has H1-H12", (await p.$$("#checklist input")).length === 12);
  await p.check('#checklist input[data-i="3"]'); await p.reload();
  check("a checklist tick is remembered", await p.isChecked('#checklist input[data-i="3"]'));
  for (let i = 0; i < 3; i++) {
    await p.check(`input[name=q${i}][value="1"]`);
    check(`quick check ${i + 1}: the right answer is marked right`, await p.$eval(`#fb${i}`, e => e.classList.contains("ok")));
  }
  await p.check("input[name=q0][value=\"0\"]");
  check("quick check: a wrong answer is marked wrong", await p.$eval("#fb0", e => e.classList.contains("no")));
  await p.close();

  // ---------------------------------------------------------------- every theme, light and dark, phone width
  for (const [w, h] of [[390, 844], [1280, 900]]) {
    for (const st of STYLES) for (const col of ["light", "dark"]) for (const depth of ["short", "full"]) {
      if (w === 1280 && depth === "short") continue;
      const q = await newPage({ viewport: { width: w, height: h } });
      await q.goto(`${FILE}?style=${st}&color=${col}&mode=${depth}`);
      const over = await q.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      check(`${w}px ${st} ${col} ${depth}: no sideways scroll`, over <= 0, `overflow ${over}px`);
      await q.context().close();
    }
  }
  const d = await newPage({ viewport: { width: 390, height: 844 } });
  await d.goto(FILE);
  await d.click("#menu");
  check("phone: ☰ opens the drawer", await d.evaluate(() => document.body.classList.contains("side-open")));
  await d.click("#answer .lede", { force: true });
  check("phone: tapping the page closes it", !(await d.evaluate(() => document.body.classList.contains("side-open"))));
  await d.context().close();

  // ---------------------------------------------------------------- the study-kit view
  if (KIT) {
    const k = await newPage();
    const fontOk = [];
    k.on("response", r => { if (r.url().includes("/lesson/fonts/")) fontOk.push(r.status()); });
    await k.goto(`${KIT}/lesson/I5_contextual_headers.html?style=reader`);
    await k.waitForTimeout(800);
    check("kit: reading fonts load from /lesson/fonts/", fontOk.length > 0 && fontOk.every(s => s === 200), JSON.stringify(fontOk));
    check("kit: ⌂ goes to the route page", (await k.getAttribute("#home", "href")) === "/#/");
    check("kit: course links are routes", (await k.$$eval(".kitonly", as => as.map(a => a.getAttribute("href")))).join(" ") === "/#/c/I5 /#/c/I4 /#/c/I6");
    check("kit: quiz link is a route", (await k.getAttribute('a[data-kit="#/quiz/I5/next"]', "href")) === "/#/quiz/I5/next");
    check("kit: book links go to /book/", (await k.$$eval("a[data-book]", as => as.every(a => a.getAttribute("href").startsWith("/book/")))));
    await k.close();
  }

  check("no console errors or page errors", errors.length === 0, errors.slice(0, 3).join(" | "));
  console.log(`\n${pass} passed, ${fail} failed`);
  await browser.close();
  process.exit(fail ? 1 : 0);
})();
