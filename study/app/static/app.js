"use strict";
/* RAG study kit: route map, reader, quiz, due list, stats. Talks to study/app/server.py. */

const app = document.getElementById("app");
const $ = (sel, el = document) => el.querySelector(sel);
const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];
let OV = null;          // last /api/overview
let dirty = false;      // an answer is typed but not saved
let lastHash = location.hash;

const TYPE = { R: "Recall", A: "Application", T: "Transfer" };
const SET = { pre: "Before reading", main: "", review: "Review", interview: "Interview" };
const CAP = [4, 3, 2, 1];
const LEVEL = ["not started", "L1 exposed", "L2 recall", "L3 applied", "L4 transfer", "L5 retained"];

const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const md = s => marked.parse(String(s ?? ""), { gfm: true });
const mdi = s => marked.parseInline(String(s ?? ""), { gfm: true });
const scoreBadge = s => s == null ? '<span class="muted">–</span>' : `<span class="score s${s}">${s}</span>`;
const store = {
  get(k, d) { try { return localStorage.getItem(k) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* private window */ } },
};

async function api(path, body) {
  const opt = body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
  const r = await fetch(path, opt);
  const j = await r.json().catch(() => ({ error: r.statusText }));
  if (!r.ok || j.error) throw new Error(j.error || r.statusText);
  return j;
}
async function fetchText(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`Could not open ${path} (${r.status})`);
  return r.text();
}
async function overview() { OV = await api("/api/overview"); badge(); return OV; }
function toast(msg) {
  const t = document.createElement("div");
  t.className = "toast"; t.textContent = msg; t.setAttribute("role", "status");
  document.body.append(t); setTimeout(() => t.remove(), 2000);
}
function badge() {
  const n = OV ? OV.due.length : 0;
  $("#dueBadge").innerHTML = n ? `<span class="badge">${n}</span>` : "";
}

/* Mirrors kit.score_from_ticks (FORMAT.md §2.4). The server recomputes it on save. */
function scoreFromTicks(kh, kt, fh, ft, wh, hint, assisted) {
  if (assisted) return [0, "answer opened without an attempt (assisted) → 0"];
  let base, why;
  if (kh <= 0) [base, why] = [0, "no key point"];
  else if (kh < kt / 2) [base, why] = [1, `${kh}/${kt} key points (under half)`];
  else if (kh < kt) [base, why] = [2, `${kh}/${kt} key points`];
  else if (ft && fh >= ft) [base, why] = [4, "all key points + the 'for a 4' points"];
  else [base, why] = [3, "all key points"];
  if (wh) { if (base > 1) why += "; but a common wrong answer → max 1"; base = Math.min(base, 1); }
  const cap = CAP[hint] ?? 1;
  if (base > cap) { why += `; hint ${hint} seen → max ${cap}`; base = cap; }
  return [base, why];
}

/* ---------------------------------------------------------------- links and markdown */

function slug(t) {
  return t.trim().toLowerCase().replace(/[^\p{L}\p{N}\s_-]/gu, "").replace(/\s/g, "-");
}
function resolvePath(base, rel) {
  let r = rel; try { r = decodeURIComponent(rel); } catch { /* keep raw */ }
  const parts = base.split("/"); parts.pop();
  let up = 0;
  for (const seg of r.split("/")) {
    if (seg === "..") { if (parts.length) parts.pop(); else up++; }
    else if (seg !== "." && seg !== "") parts.push(seg);
  }
  return "../".repeat(up) + parts.join("/");
}
function absPath(target) {
  const root = (OV ? OV.root : "").replace(/\\/g, "/").split("/");
  const t = target.split("/");
  while (t[0] === "..") { t.shift(); root.pop(); }
  return root.concat(t).join("/");
}
const vscodeHref = target => "vscode://file/" + encodeURI(absPath(target));
function bookHref(ch, page) {
  const f = ch === "App" ? "Appendix.pdf" : ch === "Intro" ? "intro.pdf" : `chapter ${ch.slice(2)}.pdf`;
  return `/book/${encodeURIComponent(f)}#page=${page}`;
}
function fixLink(a, base) {
  const href = a.getAttribute("href") || "";
  if (/^(https?:|mailto:)/i.test(href)) { a.target = "_blank"; a.rel = "noopener"; return; }
  if (/^(vscode:|\/book\/|#\/)/.test(href)) return;
  if (href.startsWith("#")) {
    const id = decodeURIComponent(href.slice(1));
    a.href = `#/read/${base}?a=${encodeURIComponent(id)}`;
    a.addEventListener("click", e => { e.preventDefault(); scrollToId(id); });
    return;
  }
  const [p, frag] = href.split("#");
  const target = resolvePath(base, p);
  const book = target.match(/RAG_Made_Simple_The_Complete_Visual_Guide\/(.+\.pdf)$/i);
  if (book) { a.href = `/book/${encodeURIComponent(book[1])}`; a.target = "_blank"; return; }
  if (/\.md$/i.test(target) && !target.startsWith("../")) {
    a.href = `#/read/${target}${frag ? "?a=" + encodeURIComponent(frag) : ""}`;
    return;
  }
  a.href = vscodeHref(target);
  a.title = "Opens in VS Code";
}
const BOOK_RE = /\b(?:(Ch\d{1,2}|App|Intro)\s*)?p\.\s?(\d{1,3})(?:\s*[–-]\s*\d{1,3})?(?:\/\d{1,3})?/g;
function linkBooks(root) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode: n => n.parentElement.closest("a,code,pre,textarea,summary") ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT,
  });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  for (const node of nodes) {
    const s = node.nodeValue;
    if (!/p\.\s?\d/.test(s)) continue;
    let cur = null, last = 0, changed = false;
    const out = [];
    s.replace(BOOK_RE, (m, ch, page, off) => {
      if (ch) cur = ch;
      if (!cur || (!ch && !m.includes("/"))) return m;   // a bare "p.10" is a corpus page, not the book
      out.push(document.createTextNode(s.slice(last, off)));
      const a = document.createElement("a");
      a.className = "book"; a.href = bookHref(cur, page); a.target = "_blank";
      a.title = "Open the book PDF at this page"; a.textContent = m;
      out.push(a); last = off + m.length; changed = true;
      return m;
    });
    if (!changed) continue;
    out.push(document.createTextNode(s.slice(last)));
    node.replaceWith(...out);
  }
}
function foldParts(root) {
  const kids = [...root.children];
  for (let i = 0; i < kids.length; i++) {
    const el = kids[i];
    if (el.tagName === "H2" && /^Part [ALM]\b/.test(el.textContent.trim())) {
      const d = document.createElement("details");
      d.className = "fold";
      const sum = document.createElement("summary");
      sum.textContent = `${el.textContent.trim()}: contains quiz answers. Open it after the quiz.`;
      el.before(d); d.append(sum, el);
      while (kids[i + 1] && kids[i + 1].tagName !== "H2") d.append(kids[++i]);
    }
  }
}
function enhance(root, base, opts = {}) {
  const seen = {};
  $$("h1,h2,h3,h4,h5,h6", root).forEach(hd => {
    let s = slug(hd.textContent);
    if (s in seen) { seen[s]++; s = `${s}-${seen[s]}`; } else seen[s] = 0;
    hd.id = s;
  });
  if (opts.fold) foldParts(root);
  // "🧭 Coach:" notes are for the AI tutor; fold each one so offline reading stays clean.
  $$("blockquote", root).filter(q => /^🧭\s*Coach/.test(q.textContent.trim())).forEach(q => {
    const d = document.createElement("details");
    d.className = "coach";
    d.innerHTML = "<summary>Tutor note (for sessions with Claude)</summary>";
    q.before(d); d.append(q);
  });
  $$("a[href]", root).forEach(a => fixLink(a, base));
  $$("img[src]", root).forEach(img => {
    const s = img.getAttribute("src");
    if (!/^(https?:|data:)/.test(s)) img.src = "/api/doc?path=" + encodeURIComponent(resolvePath(base, s));
  });
  linkBooks(root);
}
function scrollToId(id) {
  const el = document.getElementById(id) || document.getElementById(slug(id));
  if (!el) return;
  for (let d = el.closest("details"); d; d = d.parentElement.closest("details")) d.open = true;
  el.scrollIntoView({ block: "start" });
}

/* ---------------------------------------------------------------- shared bits */

const byId = id => OV.concepts.find(c => c.id === id);
const isRead = c => Boolean(c.ticks.read_short || c.ticks.read_full);
const hasMaterial = c => Boolean(c.short || c.full);
const started = c => Object.values(c.ticks).some(Boolean) || c.attempts > 0;

function chips(c) {
  const out = [`<span class="tier" title="E essential · U useful · S specialised">${esc(c.tier)}</span>`];
  if (!hasMaterial(c) && c.phase >= 1) out.push('<span class="chip">not written yet</span>');
  if (c.short) out.push('<span class="chip on">short</span>');
  if (c.full) out.push('<span class="chip on">full</span>');
  if (c.q_count) out.push(`<span class="chip on">${c.q_count} Q</span>`);
  if (isRead(c)) out.push('<span class="chip done">read</span>');
  if (c.level >= 1) out.push(`<span class="chip ${c.level >= 3 ? "done" : ""}" title="Self-checked level">L${c.level}</span>`);
  if (c.schedule) out.push(c.schedule.due
    ? `<span class="chip due">due${c.schedule.overdue_days ? ` +${c.schedule.overdue_days}d` : ""}</span>`
    : `<span class="chip" title="Next review">next ${c.schedule.next_review.slice(5)}</span>`);
  if (c.last_score != null) out.push(scoreBadge(c.last_score));
  return out.join("");
}
function plain(s) { const d = document.createElement("div"); d.innerHTML = mdi(s); return d.textContent; }

function nextSteps(c) {
  const read = [c.short && `<a href="#/read/${c.short}">short reading file</a>`, c.full && `<a href="#/read/${c.full}">full lesson</a>`].filter(Boolean).join(" or the ");
  return `<ol class="stack" style="padding-left:1.2em;margin:0">
    <li>Read the ${read || "lesson (not written yet)"}.</li>
    <li>Read the book pages: <span class="md">${mdi(c.book || "none listed")}</span></li>
    ${c.labs.length ? `<li>Do the lab: ${c.labs.map(l => `<a href="${vscodeHref(l)}">${esc(l.split("/").pop())}</a>`).join(", ")} (opens in VS Code).</li>` : ""}
    <li>${c.q_count ? `Take the quiz, closed book. Best done the next day.` : "Questions are not written yet."}</li></ol>`;
}

/* ---------------------------------------------------------------- views */

let filter = store.get("kit-filter", "all");

async function viewHome() {
  const o = await overview();
  const t = o.tiles;
  let next;
  if (o.due.length) {
    const c = byId(o.due[0]);
    next = `<section class="next" aria-label="Do first"><div class="eyebrow">Do first</div>
      <h2>${o.due.length} review${o.due.length > 1 ? "s" : ""} due today</h2>
      <p>${o.due.map(id => `<a href="#/c/${id}">${id}</a>`).join(", ")}. Reviews come before new reading: recalling something makes it stick, and a weak result tells you what to reread.</p>
      <div class="row"><a class="btn primary" href="#/quiz/${c.id}/next">Start review: ${c.id}</a><a class="btn" href="#/due">All due</a></div></section>`;
  } else if (o.next_new) {
    const c = byId(o.next_new);
    next = `<section class="next" aria-label="Next concept"><div class="eyebrow">Next concept</div>
      <h2>${c.id} · ${esc(c.title)}</h2>${nextSteps(c)}
      <div class="row"><a class="btn primary" href="#/c/${c.id}">Open ${c.id}</a></div></section>`;
  } else next = "";
  const f = [["all", "All"], ["questions", "Has questions"], ["started", "Started"], ["due", "Due"]];
  const keep = c => filter === "all" || (filter === "questions" && c.q_count) || (filter === "started" && started(c)) || (filter === "due" && c.schedule?.due);
  const phases = o.phases.map(p => {
    const cs = o.concepts.filter(c => c.phase === p.n);
    const shown = cs.filter(keep);
    if (!shown.length) return "";
    const read = cs.filter(isRead).length;
    const cls = cs.every(c => c.level >= 2) ? "complete" : cs.some(started) ? "started" : "";
    return `<section class="phase ${cls}" aria-label="Phase ${p.n}"><div class="dot">${p.n}</div><div class="pbody">
      <div class="phead"><h2>Phase ${p.n} · ${esc(p.name)}</h2><span class="muted">${read}/${cs.length} read</span>
      <span class="bar" aria-hidden="true"><i style="width:${cs.length ? 100 * read / cs.length : 0}%"></i></span></div>
      <div class="concepts">${shown.map(c => `<a class="c ${hasMaterial(c) || c.phase === 0 ? "" : "empty"}" href="#/c/${c.id}">
        <span class="id">${esc(c.id)}</span><span><span class="t">${esc(c.title)}</span><span class="sub">${esc(plain(c.failure))}</span></span>
        <span class="chips">${chips(c)}</span></a>`).join("")}</div></div></section>`;
  }).join("");
  const mean = t.mean == null ? "–" : `${t.mean.toFixed(1)}<span class="muted" style="font-size:.9rem"> / 4</span>`;
  app.innerHTML = `
    <header class="stack"><div class="eyebrow">Ask My Technical PDFs · ${o.today}</div><h1>Your RAG route</h1>
      <p class="muted">Phases 1–12 of the curriculum. Each concept: read, then the book pages, then a closed-book quiz the next day. Scores are self-checked against the key points.</p></header>
    <section class="tiles" aria-label="Summary">
      <div class="tile"><b>${t.with_reading}/${t.concepts_total}</b><span>concepts with reading</span></div>
      <div class="tile"><b>${t.with_questions}</b><span>question sets</span></div>
      <div class="tile"><b>${t.read}</b><span>concepts you have read</span></div>
      <div class="tile"><b>${t.answers}</b><span>answers saved</span></div>
      <div class="tile"><b>${mean}</b><span>average score${t.good != null ? ` · ${Math.round(100 * t.good)}% scored 3+` : ""}</span></div>
      <div class="tile ${t.due ? "warn" : ""}"><b>${t.due}</b><span>reviews due</span></div>
      <div class="tile ${t.sure_wrong ? "bad" : ""}"><b>${t.sure_wrong}</b><span>"sure" but scored 0–1</span></div>
    </section>
    ${next}
    <div class="filters" role="group" aria-label="Filter">${f.map(([k, l]) => `<button class="pill" data-f="${k}" aria-pressed="${filter === k}">${l}</button>`).join("")}</div>
    <div class="route">${phases || '<p class="muted">Nothing matches this filter.</p>'}</div>`;
  $$("[data-f]").forEach(b => b.onclick = () => { filter = b.dataset.f; store.set("kit-filter", filter); viewHome(); });
}

async function viewConcept(cid) {
  if (!OV) await overview();
  const c = await api(`/api/concept?id=${encodeURIComponent(cid)}`);
  const phase = OV.phases.find(p => p.n === c.phase);
  const step = (field, title, body, enabled = true) => `
    <div class="step ${enabled ? "" : "disabled"}"><input type="checkbox" data-tick="${field}" ${c.ticks[field] ? "checked" : ""} ${enabled ? "" : "disabled"} aria-label="${esc(title)}: done">
      <div><b>${title}</b><div class="muted">${body}</div></div><div class="muted mono">${c.ticks[field] || ""}</div></div>`;
  const sets = c.q_sets || {};
  const sched = c.schedule;
  const lastQ = c.last || {};
  app.innerHTML = `
    <div class="row"><a href="#/">← Route</a><span class="muted">/ Phase ${c.phase} · ${esc(phase?.name || "")}</span></div>
    <header class="stack"><div class="row"><span class="eyebrow">${esc(c.id)}</span><span class="tier">${esc(c.tier)}</span>
      ${c.tutor_status && c.tutor_status !== "not_started" ? `<span class="chip" title="From progress/concept_tracker.csv (tutor-graded)">tutor: ${esc(c.tutor_status)}</span>` : ""}
      <span class="chip ${c.level >= 3 ? "done" : ""}" title="Self-checked level">${LEVEL[c.level]} (self)</span></div>
      <h1>${esc(c.title)}</h1></header>
    <div class="card"><dl class="kv">
      <dt>Fixes</dt><dd class="md">${mdi(c.failure)}</dd>
      <dt>Needs first</dt><dd class="md">${mdi(c.pre || "–")}</dd>
      <dt>Book</dt><dd class="md" id="bookline">${mdi(c.book || "–")}</dd>
      <dt>Project</dt><dd class="md">${mdi(c.proj || "–")}</dd></dl></div>
    <section class="stack"><h2>Do these in order</h2><div class="steps">
      ${c.visual ? step("read_short", `1 · Read the <a href="/lesson/${encodeURIComponent(c.visual)}?mode=short">visual lesson, Short</a>`,
          `One page with interactive charts and a one-minute check.${c.short ? ` Text version: <a href="#/read/${c.short}">short reading file</a>.` : ""}`)
        + step("read_full", `1 · or the <a href="/lesson/${encodeURIComponent(c.visual)}?mode=full">visual lesson, Full</a>`,
          `Adds the exact formula, a hand computation, edge cases and checks.${c.full ? ` Text version: <a href="#/read/${c.full}">full lesson</a> with the lab.` : ""}`) : `
      ${c.short ? step("read_short", `1 · Read the <a href="#/read/${c.short}">short reading file</a>`, "Book-first explanation in plain English.") : ""}
      ${c.full ? step("read_full", `${c.short ? "1 · or" : "1 ·"} Read the <a href="#/read/${c.full}">full lesson</a>`, "Parts B–K. Parts A, L and M hold quiz answers, so they stay folded.") : ""}`}
      ${!c.short && !c.full ? step("read_short", "1 · Read the lesson", "Not written yet.", false) : ""}
      ${step("book", "2 · Read the book pages", `<span class="md">${mdi(c.book || "none listed")}</span>`)}
      ${c.labs.length ? step("lab", "3 · Do the lab", c.labs.map(l => `<a href="${vscodeHref(l)}">${esc(l)}</a>`).join(", ") + " (opens in VS Code)") : ""}
      ${c.notebook ? `<div class="step"><span aria-hidden="true">✓</span><div><b>${c.labs.length ? 4 : 3} · Verify it yourself</b>
        <div class="muted"><a href="${vscodeHref(c.notebook)}">${esc(c.notebook.split("/").pop())}</a> rebuilds every number and chart of the lesson (opens in VS Code; Run All on the .venv kernel).</div></div><div></div></div>` : ""}
      ${c.tool ? `<div class="step"><span aria-hidden="true">⚙</span><div><b>${(c.labs.length ? 4 : 3) + (c.notebook ? 1 : 0)} · Use it on your own data</b>
        <div class="muted"><code>uv run python ${esc(c.tool)} --docs "your folder" --questions your_questions.jsonl</code> · <a href="${vscodeHref(c.tool)}">open the tool</a></div></div><div></div></div>` : ""}
      <div class="step"><span aria-hidden="true">✎</span><div><b>${(c.labs.length ? 4 : 3) + (c.notebook ? 1 : 0) + (c.tool ? 1 : 0)} · Quiz, closed book</b>
        <div class="muted">${c.q_count ? `${c.q_count} questions. Best taken the day after reading.` : "Questions not written yet."}</div></div><div></div></div>
    </div>
    ${c.q_count ? `<div class="row">
      <a class="btn primary" href="#/quiz/${c.id}/next">${Object.keys(lastQ).length ? "Review quiz (weakest first)" : "Start the quiz"}</a>
      ${sets.pre ? `<a class="btn" href="#/quiz/${c.id}/pre">Pre-test (before reading)</a>` : ""}
      ${sets.interview ? `<a class="btn" href="#/quiz/${c.id}/interview">Interview questions</a>` : ""}
      <a class="btn" href="#/quiz/${c.id}/all">All questions</a>
      <a class="btn ghost" href="#/read/${c.questions}">Question file</a></div>` : ""}
    </section>
    <div class="grid2">
      <section class="card stack"><h3>Review schedule</h3>${sched ? `
        <dl class="kv"><dt>Next review</dt><dd><b>${sched.next_review}</b> ${sched.due ? '<span class="chip due">due</span>' : ""}</dd>
        <dt>Interval</dt><dd>${sched.interval} day${sched.interval > 1 ? "s" : ""}, on the ladder 1 → 3 → 7 → 14 → 30 → 60</dd>
        <dt>Started</dt><dd>${sched.start}</dd><dt>Last review</dt><dd>${sched.last_review}</dd></dl>
        ${sched.history.length ? `<div class="tablewrap"><table><thead><tr><th>Day</th><th class="num">Lowest</th><th>Interval</th></tr></thead><tbody>
          ${sched.history.map(h => `<tr><td>${h.date}</td><td class="num">${scoreBadge(h.lowest)}</td><td>${h.from} → ${h.to}</td></tr>`).join("")}</tbody></table></div>` : ""}
        <p class="muted">The lowest score of a review day decides the step: 3+ moves up, 2 repeats, 0–1 drops back to 1 day.</p>`
        : '<p class="muted">Starts when you tick "read", or when you answer the first quiz.</p>'}</section>
      <section class="card stack"><h3>Questions</h3>${c.questions.length ? `<div class="tablewrap"><table>
        <thead><tr><th>Item</th><th>Type</th><th class="num">Last</th><th>When</th></tr></thead><tbody>
        ${c.questions.map(q => `<tr><td class="mono">${esc(q.id)}</td><td>${TYPE[q.type]}${SET[q.set] ? ` · ${SET[q.set]}` : ""}</td>
          <td class="num">${scoreBadge(lastQ[q.id]?.score)}</td><td class="muted">${lastQ[q.id]?.date || ""}</td></tr>`).join("")}
        </tbody></table></div>` : '<p class="muted">None yet.</p>'}</section>
    </div>
    ${c.history.length ? `<section class="card stack"><h3>Your answers</h3>${[...c.history].reverse().slice(0, 40).map(a => `
      <details><summary>${scoreBadge(a.score)} <span class="mono">${esc(a.qid)}</span> · ${a.date} · sure ${a.confidence ?? "–"}${a.hint_level ? ` · hint ${a.hint_level}` : ""}${a.assisted ? " · assisted" : ""}</summary>
      <div class="yours" style="margin-top:8px">${esc(a.answer) || "<em>(nothing written)</em>"}</div><p class="muted">${esc(a.why || "")}</p></details>`).join("")}</section>` : ""}`;
  enhance($("#bookline"), "x.md");
  $$(".step .muted").forEach(el => linkBooks(el));
  $$("[data-tick]").forEach(box => box.onchange = async () => {
    await api("/api/tick", { concept: c.id, field: box.dataset.tick, on: box.checked });
    toast(box.checked ? "Ticked" : "Unticked");
    await overview(); viewConcept(c.id);
  });
}

async function viewRead(path, anchor) {
  if (!OV) await overview();
  const src = await fetchText(`/api/doc?path=${encodeURIComponent(path)}`);
  const c = OV.concepts.find(x => x.short === path || x.full === path || x.questions === path);
  const isFull = /^concepts\//.test(path) || path === "07_SAMPLE_LESSON.md";
  const field = c && (c.short === path ? "read_short" : c.full === path ? "read_full" : null);
  app.innerHTML = `
    <div class="row"><a href="${c ? `#/c/${c.id}` : "#/"}">← ${c ? `${esc(c.id)} · ${esc(c.title)}` : "Route"}</a><span class="spacer"></span>
      ${field ? `<button id="markRead" class="${c.ticks[field] ? "" : "primary"}">${c.ticks[field] ? `Read on ${c.ticks[field]} ✓` : "Mark as read"}</button>` : ""}
      ${c && c.q_count ? `<a class="btn" href="#/quiz/${c.id}/next">Quiz</a>` : ""}
      <a class="btn ghost" href="${vscodeHref(path)}" title="Open the source file in VS Code">Edit in VS Code</a></div>
    ${isFull ? '<p class="notice">Full lesson. Parts A, L and M contain the quiz answers, so they are folded. Read Parts B–K, then take the quiz.</p>' : ""}
    <div class="reader"><nav class="toc" id="toc" aria-label="Contents"></nav><article class="md card" id="doc"></article></div>`;
  const doc = $("#doc");
  doc.innerHTML = md(src);
  enhance(doc, path, { fold: isFull });
  $("#toc").innerHTML = '<div class="eyebrow" style="margin-bottom:6px">Contents</div>' +
    $$("h2,h3", doc).map(hd => `<a class="${hd.tagName.toLowerCase()}" href="#/read/${path}?a=${encodeURIComponent(hd.id)}" data-id="${hd.id}">${esc(hd.textContent)}</a>`).join("");
  $$("#toc a").forEach(a => a.onclick = e => { e.preventDefault(); scrollToId(a.dataset.id); });
  if (field) $("#markRead").onclick = async () => {
    await api("/api/tick", { concept: c.id, field, on: !c.ticks[field] });
    toast(c.ticks[field] ? "Unticked" : "Marked as read. Quiz tomorrow for the best effect.");
    await overview(); viewRead(path, "");
  };
  if (anchor) setTimeout(() => scrollToId(anchor), 0);
}

async function viewQuiz(cid, mode) {
  if (!OV) await overview();
  const c = byId(cid);
  const { questions } = await api(`/api/quiz?id=${encodeURIComponent(cid)}&mode=${encodeURIComponent(mode)}`);
  if (!questions.length) {
    app.innerHTML = `<div class="row"><a href="#/c/${cid}">← ${esc(cid)}</a></div><p class="notice">No questions in this set yet.</p>`;
    return;
  }
  showQuestion({ i: 0, results: [], mode }, questions, c);
}

function showQuestion(S, qs, c) {
  const q = qs[S.i];
  const st = { hint: 0, conf: null };
  const hintLabel = () => st.hint < q.hints.length ? `Hint ${st.hint + 1} (then max ${CAP[st.hint + 1]})` : "No more hints";
  app.innerHTML = `
    <div class="quiz">
      <div class="row"><a href="#/c/${c.id}">← ${esc(c.id)} · ${esc(c.title)}</a><span class="spacer"></span><span class="muted">Question ${S.i + 1} of ${qs.length}</span></div>
      <div class="progress" aria-hidden="true"><i style="width:${100 * S.i / qs.length}%"></i></div>
      <div class="card stack">
        <div class="qhead"><span class="chip mono">${esc(q.id)}</span><span class="chip on">${TYPE[q.type] || q.type}</span>${SET[q.set] ? `<span class="chip">${SET[q.set]}</span>` : ""}</div>
        <div class="qtext md" id="qtext">${md(q.question)}</div>
        ${q.template ? `<div class="template md">${mdi(q.template)}</div>` : ""}
        <div id="hints" class="stack"></div>
        <label for="ans" class="muted">Your answer: closed book, in your own words</label>
        <textarea id="ans" placeholder="Write your answer…  (Ctrl+Enter to check)"></textarea>
        <div class="conf" role="group" aria-label="How sure are you?"><span class="muted">How sure are you?</span>
          <button class="pill" data-conf="1" aria-pressed="false">1 · guessing</button>
          <button class="pill" data-conf="2" aria-pressed="false">2 · fairly sure</button>
          <button class="pill" data-conf="3" aria-pressed="false">3 · sure</button></div>
        <div class="row" id="actions">
          <button class="primary" id="check" disabled>Check my answer</button>
          <button id="hintBtn" ${q.hints.length ? "" : "disabled"}>${hintLabel()}</button>
          <span class="spacer"></span><button class="ghost" id="idk">I don't know: show me</button></div>
      </div>
      <div id="reveal"></div>
    </div>`;
  enhance($("#qtext"), q.file);
  const ans = $("#ans"), check = $("#check");
  const ready = () => { check.disabled = !(ans.value.trim() && st.conf); };
  ans.oninput = () => { dirty = Boolean(ans.value.trim()); ready(); };
  ans.onkeydown = e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey) && !check.disabled) check.click(); };
  $$("[data-conf]").forEach(b => b.onclick = () => {
    st.conf = Number(b.dataset.conf);
    $$("[data-conf]").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
    ready();
  });
  $("#hintBtn").onclick = () => {
    if (st.hint >= q.hints.length) return;
    st.hint++;
    const div = document.createElement("div");
    div.className = "hint";
    div.innerHTML = `<b>Hint ${st.hint}</b> <span class="muted">(max score now ${CAP[st.hint]})</span><div class="md">${md(q.hints[st.hint - 1])}</div>`;
    enhance(div, q.file);
    $("#hints").append(div);
    $("#hintBtn").textContent = hintLabel();
    $("#hintBtn").disabled = st.hint >= q.hints.length;
  };
  check.onclick = () => reveal(S, qs, c, q, st, false);
  $("#idk").onclick = () => reveal(S, qs, c, q, st, true);
  ans.focus();
}

function reveal(S, qs, c, q, st, assisted) {
  const a = q.answer;
  const ans = $("#ans");
  ans.readOnly = true;
  $$("#actions button, [data-conf]").forEach(b => b.disabled = true);
  const list = (items, kind) => items.map((t, i) => `<label><input type="checkbox" data-kind="${kind}" value="${i}"><span class="md">${mdi(t)}</span></label>`).join("");
  $("#reveal").innerHTML = `
    <div class="card reveal">
      <div class="compare">
        <div class="stack"><div class="eyebrow">Your answer · sure ${st.conf ?? "–"}</div><div class="yours">${esc(ans.value) || "<em>(nothing written)</em>"}</div></div>
        <div class="stack"><div class="eyebrow">Model answer</div><div class="md" id="model"></div></div>
      </div>
      ${assisted ? '<p class="notice">You opened the answer without an attempt, so this counts as assisted: score 0. It comes back in your next review.</p>' : `
      <div class="stack"><div><b>Tick only what your answer really says.</b> <span class="muted">Be strict: when you have Claude again, a sample of these is re-graded.</span></div>
        <div class="checks" id="keys">${list(a.keys, "key")}</div>
        ${a.four.length ? `<b>For a 4, your answer also has</b><div class="checks">${list(a.four, "four")}</div>` : ""}
        ${a.wrong.length ? `<b>Did your answer say any of these?</b><div class="checks wrong">${list(a.wrong, "wrong")}</div>` : ""}</div>`}
      <div class="result" id="result" aria-live="polite"></div>
      ${a.reread ? `<div class="md" id="reread"><b>If you missed it, reread:</b> ${mdi(a.reread)}</div>` : ""}
      <div class="row"><button class="primary" id="save">${S.i + 1 < qs.length ? "Save and next" : "Save and finish"}</button></div>
    </div>`;
  $("#model").innerHTML = md([a.preamble, a.model].filter(Boolean).join("\n\n"));
  enhance($("#reveal"), q.file);
  const count = kind => $$(`input[data-kind="${kind}"]:checked`).map(x => Number(x.value));
  const update = () => {
    const [s, why] = scoreFromTicks(count("key").length, a.keys.length, count("four").length, a.four.length, count("wrong").length, st.hint, assisted);
    $("#result").innerHTML = `${scoreBadge(s)}<div><b>Score ${s} / 4</b><div class="muted">${esc(why)}</div></div>`;
  };
  $$("#reveal input[type=checkbox]").forEach(x => x.onchange = update);
  update();
  $("#save").onclick = async () => {
    $("#save").disabled = true;
    try {
      const row = await api("/api/attempt", {
        qid: q.id, concept: q.concept, answer: ans.value, confidence: st.conf, hint_level: st.hint, assisted,
        key_hit: count("key"), four_hit: count("four"), wrong_hit: count("wrong"),
      });
      dirty = false;
      S.results.push({ q, row });
      S.i++;
      if (S.i < qs.length) showQuestion(S, qs, c); else summary(S, c);
    } catch (e) { $("#save").disabled = false; toast("Not saved: " + e.message); }
  };
  $("#reveal").scrollIntoView({ block: "start", behavior: "smooth" });
}

async function summary(S, c) {
  await overview();
  const d = await api(`/api/concept?id=${encodeURIComponent(c.id)}`);
  const rows = S.results.map(r => r.row);
  const mean = rows.reduce((s, r) => s + r.score, 0) / rows.length;
  const low = Math.min(...rows.map(r => r.score));
  const sureWrong = rows.filter(r => r.confidence === 3 && r.score <= 1).length;
  const weak = S.results.filter(r => r.row.score <= 2);
  app.innerHTML = `
    <div class="quiz">
      <div class="row"><a href="#/c/${c.id}">← ${esc(c.id)} · ${esc(c.title)}</a></div>
      <header class="stack"><div class="eyebrow">Quiz done · ${esc(S.mode)}</div><h1>${rows.length} answers saved</h1></header>
      <section class="tiles">
        <div class="tile"><b>${mean.toFixed(1)}</b><span>average / 4</span></div>
        <div class="tile ${low <= 1 ? "bad" : low === 2 ? "warn" : "now"}"><b>${low}</b><span>lowest: this sets the next review</span></div>
        <div class="tile ${sureWrong ? "bad" : ""}"><b>${sureWrong}</b><span>"sure" but scored 0–1</span></div>
        <div class="tile"><b>${d.schedule ? d.schedule.next_review : "–"}</b><span>next review of ${esc(c.id)}</span></div>
      </section>
      ${sureWrong ? '<p class="notice">You felt sure and were wrong. That is the pattern to watch: when you feel sure, check one key point against the reading before moving on.</p>' : ""}
      <section class="card stack"><h3>Results</h3><div class="tablewrap"><table>
        <thead><tr><th>Item</th><th>Type</th><th class="num">Sure</th><th class="num">Score</th><th>Why</th></tr></thead><tbody>
        ${rows.map(r => `<tr><td class="mono">${esc(r.qid)}</td><td>${TYPE[r.type]}</td><td class="num">${r.confidence ?? "–"}</td><td class="num">${scoreBadge(r.score)}</td><td class="muted">${esc(r.why)}</td></tr>`).join("")}
        </tbody></table></div></section>
      ${weak.length ? `<section class="card stack" id="rereads"><h3>Reread these, then retry tomorrow</h3>
        ${weak.map(r => `<div class="md" data-file="${esc(r.q.file)}"><b class="mono">${esc(r.q.id)}</b> → ${mdi(r.q.answer.reread || "the lesson")}</div>`).join("")}</section>` : ""}
      <div class="row"><a class="btn primary" href="#/c/${c.id}">Back to ${esc(c.id)}</a><a class="btn" href="#/">Route</a><a class="btn" href="#/stats">My stats</a></div>
    </div>`;
  $$("#rereads [data-file]").forEach(el => enhance(el, el.dataset.file));
}

async function viewDue() {
  const o = await overview();
  const due = o.due.map(byId);
  const soon = o.concepts.filter(c => c.schedule && !c.schedule.due).sort((a, b) => a.schedule.next_review.localeCompare(b.schedule.next_review));
  const row = c => `<a class="c" href="#/c/${c.id}"><span class="id">${esc(c.id)}</span><span><span class="t">${esc(c.title)}</span>
    <span class="sub">next review ${c.schedule.next_review} · interval ${c.schedule.interval}d</span></span><span class="chips">${chips(c)}</span></a>`;
  app.innerHTML = `
    <header class="stack"><div class="eyebrow">${o.today}</div><h1>Reviews</h1>
      <p class="muted">Review closed book. A review is 5 questions, weakest first, with at least 1 Application or Transfer item in every 3.</p></header>
    <section class="stack"><h2>Due now</h2>${due.length ? `<div class="concepts">${due.map(row).join("")}</div>
      <div class="row"><a class="btn primary" href="#/quiz/${due[0].id}/next">Start: ${esc(due[0].id)}</a></div>` : '<p class="muted">Nothing due. Read the next concept, or take a quiz on one you have read.</p>'}</section>
    <section class="stack"><h2>Coming up</h2>${soon.length ? `<div class="concepts">${soon.map(row).join("")}</div>` : '<p class="muted">No reviews scheduled yet.</p>'}</section>`;
}

function hbar(label, v, max, valText) {
  const pct = v == null ? 0 : Math.max(2, 100 * v / max);
  const tone = v == null ? "" : v / max >= 0.75 ? "hi" : v / max >= 0.5 ? "mid" : "lo";
  return `<div class="hbar"><span>${label}</span><span class="track" aria-hidden="true"><span class="fill ${tone}" style="display:block;width:${pct}%"></span></span><span class="val">${valText}</span></div>`;
}

async function viewStats() {
  const [s] = await Promise.all([api("/api/stats"), overview()]);
  const fmt = g => g.n ? `${g.mean.toFixed(1)} / 4 · ${Math.round(100 * g.good)}% 3+ · n=${g.n}` : "no answers";
  const c3 = s.by_conf["3"];
  let verdict = '<p class="muted">Answer at least 5 questions marked "sure" to see your calibration.</p>';
  if (c3.n >= 5) verdict = c3.mean >= 3
    ? `<p>When you say "sure", you average <b>${c3.mean.toFixed(1)}</b>. Your confidence is earning its keep.</p>`
    : `<p class="notice">When you say "sure", you average <b>${c3.mean.toFixed(1)} / 4</b>, and only ${Math.round(100 * c3.good)}% reach 3. Treat "sure" as a signal to check one key point, not as a reason to skip.</p>`;
  const concepts = Object.entries(s.concepts).sort((a, b) => (a[1].mean ?? 9) - (b[1].mean ?? 9));
  const maxDay = Math.max(1, ...s.activity.map(d => d.n));
  app.innerHTML = `
    <header class="stack"><div class="eyebrow">Self-checked</div><h1>My stats</h1>
      <p class="muted">Everything here is computed from progress/study_attempts.jsonl. Scores come from your ticks against the key points (FORMAT.md §2.4).</p></header>
    <section class="tiles">
      <div class="tile"><b>${s.total}</b><span>answers</span></div>
      <div class="tile"><b>${s.overall.n ? s.overall.mean.toFixed(1) : "–"}</b><span>average / 4</span></div>
      <div class="tile"><b>${s.overall.n ? Math.round(100 * s.overall.good) + "%" : "–"}</b><span>scored 3 or 4</span></div>
      <div class="tile ${s.sure_wrong.length ? "bad" : ""}"><b>${s.sure_wrong.length}</b><span>"sure" but 0–1</span></div>
      <div class="tile"><b>${s.assisted}</b><span>assisted (answer opened first)</span></div>
    </section>
    <div class="grid2">
      <section class="card stack"><h2>Confidence vs score</h2>
        <div class="hbars">${hbar("1 · guessing", s.by_conf["1"].mean, 4, fmt(s.by_conf["1"]))}${hbar("2 · fairly sure", s.by_conf["2"].mean, 4, fmt(s.by_conf["2"]))}${hbar("3 · sure", c3.mean, 4, fmt(c3))}</div>${verdict}</section>
      <section class="card stack"><h2>By question type</h2>
        <div class="hbars">${["R", "A", "T"].map(t => hbar(TYPE[t], s.by_type[t].mean, 4, fmt(s.by_type[t]))).join("")}</div>
        <p class="muted">Hints used: ${[1, 2, 3].map(h => `hint ${h}: ${s.by_hint[h] || 0}`).join(" · ")}</p></section>
    </div>
    <section class="card stack"><h2>By concept (weakest first)</h2>${concepts.length ? `<div class="tablewrap"><table>
      <thead><tr><th>Concept</th><th class="num">Answers</th><th class="num">Average</th><th class="num">3+</th><th>Last</th></tr></thead><tbody>
      ${concepts.map(([id, g]) => `<tr><td><a href="#/c/${id}">${esc(id)}</a> <span class="muted">${esc(byId(id)?.title || "")}</span></td><td class="num">${g.n}</td>
        <td class="num">${g.mean?.toFixed(1) ?? "–"}</td><td class="num">${g.good != null ? Math.round(100 * g.good) + "%" : "–"}</td><td class="muted">${g.last}</td></tr>`).join("")}
      </tbody></table></div>` : '<p class="muted">No answers yet.</p>'}</section>
    <div class="grid2">
      <section class="card stack"><h2>Sure, but wrong</h2>${s.sure_wrong.length ? [...s.sure_wrong].reverse().map(a => `
        <details><summary>${scoreBadge(a.score)} <span class="mono">${esc(a.qid)}</span> · ${a.date}</summary><div class="yours" style="margin-top:8px">${esc(a.answer)}</div></details>`).join("")
        : '<p class="muted">None so far.</p>'}</section>
      <section class="card stack"><h2>Wrong ideas you ticked</h2>${s.mistakes.length ? `<div class="tablewrap"><table><tbody>
        ${s.mistakes.map(m => `<tr><td class="num">${m.n}×</td><td><a href="#/c/${m.concept}">${esc(m.concept)}</a></td><td class="md">${mdi(m.text)}</td></tr>`).join("")}</tbody></table></div>`
        : '<p class="muted">None ticked yet.</p>'}
        ${Object.keys(s.mc).length ? `<p class="muted">Misconception log hits: ${Object.entries(s.mc).map(([k, v]) => `${k} ×${v}`).join(" · ")}</p>` : ""}</section>
    </div>
    <section class="card stack"><h2>Weakest questions right now</h2>${s.weakest.length ? `<div class="tablewrap"><table>
      <thead><tr><th>Item</th><th class="num">Last</th><th>When</th><th></th></tr></thead><tbody>
      ${s.weakest.map(a => `<tr><td class="mono">${esc(a.qid)}</td><td class="num">${scoreBadge(a.score)}</td><td class="muted">${a.date}</td><td><a href="#/quiz/${a.concept}/next">retry ${esc(a.concept)}</a></td></tr>`).join("")}
      </tbody></table></div>` : '<p class="muted">Nothing below 3.</p>'}</section>
    <section class="card stack"><h2>Activity</h2>${s.activity.length ? `<div class="days" role="img" aria-label="Answers per day">
      ${s.activity.map(d => `<i title="${d.date}: ${d.n} answers, average ${d.mean}" style="height:${Math.max(4, 76 * d.n / maxDay)}px"></i>`).join("")}</div>
      <p class="muted">${s.activity.length} study day${s.activity.length > 1 ? "s" : ""}, from ${s.activity[0].date} to ${s.activity.at(-1).date}.</p>` : '<p class="muted">No activity yet.</p>'}</section>
    <div class="row"><button id="export">Download my data (JSON)</button></div>`;
  $("#export").onclick = async () => {
    const data = await api("/api/export");
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: `study_export_${OV.today}.json` });
    a.click(); URL.revokeObjectURL(url);
  };
}

async function viewHelp() {
  if (!OV) await overview();
  app.innerHTML = `<article class="md card" id="help"></article>`;
  const src = await fetchText("/api/doc?path=study/README.md").catch(() => "# How to use\n\nSee `study/README.md`.");
  $("#help").innerHTML = md(src);
  enhance($("#help"), "study/README.md");
}

/* ---------------------------------------------------------------- router, theme */

const ROUTES = [
  [/^#\/c\/([^/?#]+)$/, m => viewConcept(decodeURIComponent(m[1]))],
  [/^#\/read\/([^?]+)(?:\?a=(.*))?$/, m => viewRead(decodeURIComponent(m[1]), m[2] ? decodeURIComponent(m[2]) : "")],
  [/^#\/quiz\/([^/]+)\/(\w+)$/, m => viewQuiz(decodeURIComponent(m[1]), m[2])],
  [/^#\/stats$/, () => viewStats()],
  [/^#\/due$/, () => viewDue()],
  [/^#\/help$/, () => viewHelp()],
  [/^(#\/?)?$/, () => viewHome()],
];

async function render() {
  const hash = location.hash;
  if (dirty && hash !== lastHash) {
    if (!confirm("Your answer is not saved yet. Leave this question?")) { history.replaceState(null, "", lastHash || "#/"); return; }
    dirty = false;
  }
  lastHash = hash;
  const nav = hash.startsWith("#/stats") ? "stats" : hash.startsWith("#/due") ? "due" : hash.startsWith("#/help") ? "help" : "home";
  $$("[data-nav]").forEach(a => {
    if (a.dataset.nav === nav) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
  });
  for (const [re, fn] of ROUTES) {
    const m = hash.match(re);
    if (!m) continue;
    if (!hash.includes("?a=")) window.scrollTo(0, 0);
    try { await fn(m); } catch (e) { app.innerHTML = `<div class="error">${esc(e.message)}</div><p><a href="#/">Back to the route</a></p>`; }
    return;
  }
  app.innerHTML = '<div class="error">Page not found.</div><p><a href="#/">Back to the route</a></p>';
}

const THEMES = ["auto", "light", "dark"];
function applyTheme(t) {
  if (t === "auto") document.documentElement.removeAttribute("data-theme");
  else document.documentElement.setAttribute("data-theme", t);
  $("#theme").textContent = `Theme: ${t}`;
}
let theme = store.get("kit-theme", "auto");
applyTheme(theme);
$("#theme").onclick = () => { theme = THEMES[(THEMES.indexOf(theme) + 1) % 3]; store.set("kit-theme", theme); applyTheme(theme); };
window.addEventListener("beforeunload", e => { if (dirty) { e.preventDefault(); e.returnValue = ""; } });
window.addEventListener("hashchange", render);
render();
