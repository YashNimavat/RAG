"""I4: check the two study-kit Markdown files of 2026-10-18 (question file and short reading file).

1. study/questions/I4_questions.md loads with the kit's own parser and passes kit.lint_questions; the 17 ids of the
   build spec, in their sets and types; FORMAT field rules (2 hints, Hint 3 only on A items, 2-5 key points, 1-2
   'for a 4', 1-3 wrong answers, one short question sentence); at most 2 external items; the interview item I4-R-07
   quotes AIQ-04 Q4's heading and answer verbatim (every quoted line is an exact substring of the pinned repo file),
   carries the MIT notice, and the repo's answer comes before ours; our model answer adds propositions.
2. The data inside the items is recomputed with the definitions of i4_kit_measure.py (splitter, words/stem/STOP,
   PRONOUN_START, the 97 v0 chunks, any_overlap, Wilson): I4-A-01's propositions (ids, align, resolved names,
   pronouns, parent), I4-A-03's dedup and RR, I4-A-04's word set and align, I4-A-05's intervals, I4-A-02's sums,
   and the p.29 sentences quoted in I4-A-01. Needs the climate PDF; prints SKIPPED without it.
3. Every reread line links into BOTH the short reading file and the HTML lesson (a step anchor) and names a book
   page; each item's reread names the reading section(s) and lesson step(s) the spec says teach it.
4. Every relative link in both files resolves, with its #anchor (GitHub rule for .md; for the lesson, the ids in
   the HTML file if it exists, else the step anchors of the build spec §2); links from other workspace .md files
   into these files resolve too.
5. The reading file's shape (FORMAT §3): header, What this is / is not, the book box (Ch4 p.4-12/15 + a not
   re-opened line), the 13 fixed section headings in order, then 'Check yourself'; the four house-style beats in
   sections 1-12; 1,800-3,000 words of prose (code blocks removed); the honesty labels.
6. Book pages: every 'ChN p.x/y' cited is Ch4 with y = 15 and a page from the research's list; the page-exists and
   15-word copyright checks need the book PDF and print SKIPPED (book not present) when it is missing. A 15-word
   check against the upstream notebook (cell sources) runs instead.
7. Numbers: every decimal, and every integer >= 10, in the two files is printed in out_i4_kit_measure.txt or
   written in I4_FACTS.md, or is on the DERIVED (arithmetic shown in the text) list below.
8. The coach-banned phrases of the build spec are absent from both files.
9. `uv run python study/quiz.py --check` passes.

Local only: no API call, no network. Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I4/i4_md_check.py ["<Book RAG>"] [<AIQ questions.md>] \
        > sources/verification/I4/out_i4_md_check.txt
<Book RAG> defaults to the folder above rag_learning/. The interview file defaults to
<Book RAG>/upstream/AI-Engineer-Interview-Questions/04-rag-and-retrieval/questions.md (@ e080df2).
"""
import hashlib
import html
import json
import math
import re
import subprocess
import sys
from pathlib import Path

WS = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else WS.parent
AIQ = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "upstream" / "AI-Engineer-Interview-Questions" / "04-rag-and-retrieval" / "questions.md"
BOOK = ROOT / "RAG_Made_Simple_The_Complete_Visual_Guide"
PDF = ROOT / "upstream" / "RAG_Techniques" / "data" / "Understanding_Climate_Change.pdf"
UPNB = ROOT / "upstream" / "RAG_Techniques" / "all_rag_techniques" / "proposition_chunking.ipynb"
QF = WS / "study" / "questions" / "I4_questions.md"
SHORT = WS / "study" / "reading" / "I4_proposition_chunking.md"
LESSON = WS / "study" / "lessons" / "I4_propositions.html"
fails = n = skips = 0


def check(ok, label):
    global fails, n
    n += 1
    fails += not ok
    print(("PASS " if ok else "FAIL ") + label)


def skip(label):
    global skips
    skips += 1
    print("SKIPPED " + label)


# ---------------------------------------------------------------- 1. question file
sys.path.insert(0, str(WS / "study"))
import kit  # noqa: E402

qs = kit.parse_questions(QF)
qtext = QF.read_text(encoding="utf-8")
short = SHORT.read_text(encoding="utf-8")
problems = kit.lint_questions(QF)
check(not problems, f"kit.lint_questions: {problems or 'no problems'}")
check(qtext.startswith("<!-- kit:questions concept=I4 version=1 -->"), "question file header line")
SPEC = {  # id: (set, reading sections, lesson anchors) from the build spec §6 table and §2 steps
    "I4-PRE-01": ("pre", [1], ["dilution"]),
    "I4-R-01": ("main", [2], ["proposition"]),
    "I4-R-02": ("main", [6], ["anchor"]),
    "I4-R-03": ("main", [8], ["grade"]),
    "I4-R-04": ("main", [3], ["decontext"]),
    "I4-R-05": ("main", [7], ["align"]),
    "I4-R-06": ("review", [9], ["score"]),
    "I4-R-07": ("interview", [2, 6, 11], ["proposition", "cost"]),
    "I4-A-01": ("main", [2, 3, 6], ["decontext", "anchor"]),
    "I4-A-02": ("main", [11], ["cost"]),
    "I4-A-03": ("main", [9], ["score"]),
    "I4-A-04": ("main", [7], ["align"]),
    "I4-A-05": ("review", [7], ["align"]),
    "I4-T-01": ("main", [10, 13], ["relations"]),
    "I4-T-02": ("main", [7, 12], ["align", "project"]),
    "I4-T-03": ("main", [5, 12], ["prompt"]),
    "I4-T-04": ("review", [12, 9], ["project"]),
}
ids = [q["id"] for q in qs]
qd = {q["id"]: q for q in qs}
check(sorted(ids) == sorted(SPEC) and len(ids) == 17, f"the 17 ids of the build spec, no more, no less ({len(ids)})")
check(len(set(ids)) == len(ids), "ids unique")
check(all(qd[i]["set"] == s for i, (s, _, _) in SPEC.items() if i in qd), "each id is in the spec's set (pre/main/review/interview)")
check(all(re.fullmatch(r"I4-(PRE|[RAT])-\d\d", i) for i in ids), "ids follow I4-<type>-<nn> / I4-PRE-<nn>")
check(all(q["id"].split("-")[1] == q["type"] or q["id"].startswith("I4-PRE") for q in qs), "id letter = type")
check(ids[0] == "I4-PRE-01" and qd["I4-PRE-01"]["type"] == "R", "the set=pre item comes first (type R)")
cnt = lambda s: sum(q["set"] == s for q in qs)
print(f"     items: {len(qs)}; pre {cnt('pre')}; main {cnt('main')} (R {sum(q['set'] == 'main' and q['type'] == 'R' for q in qs)}, "
      f"A {sum(q['set'] == 'main' and q['type'] == 'A' for q in qs)}, T {sum(q['set'] == 'main' and q['type'] == 'T' for q in qs)}); "
      f"review {cnt('review')}; interview {cnt('interview')}")
blocks = dict((re.search(r"id=(\S+)", h).group(1), (h, b)) for h, b in re.findall(r"<!-- q (.*?) -->(.*?)<!-- /q -->", qtext, re.S))
bad_fmt = []
for q in qs:
    h, b = blocks[q["id"]]
    ok = ("<summary>Hint 1</summary>" in b and "<summary>Hint 2</summary>" in b
          and ("<summary>Hint 3</summary>" not in b or q["type"] == "A")
          and 2 <= len(q["answer"]["keys"]) <= 5 and 1 <= len(q["answer"]["four"]) <= 2 and 1 <= len(q["answer"]["wrong"]) <= 3
          and b.count("<details>") == len(q["hints"]) + 1)
    if q["set"] != "interview":
        first = q["question"].splitlines()[0]
        bare = re.sub(r'"[^"]*"', '"…"', first)                              # a quoted proposition is data, not a sentence end
        ok = ok and len(re.findall(r"[.?!]\"?(?:\s|$)", bare)) == 1 and first.rstrip().endswith(("?", ".")) and len(first.split()) <= 45
    if not ok:
        bad_fmt.append(q["id"])
check(not bad_fmt, f"FORMAT field rules on every item: Hint 1+2, Hint 3 only on A, 2-5 keys, 1-2 'for a 4', 1-3 wrong, "
      f"no nested details, one short question sentence ({bad_fmt or 'all 17'})")
h3 = [q["id"] for q in qs if len(q["hints"]) == 3]
print(f"     Hint 3 on: {h3}")
check(sum(1 for q in qs if q["source"]) <= 2, f"at most 2 external items ({sum(1 for q in qs if q['source'])})")
MC = {"MC-006": ["I4-R-03", "I4-T-02"], "MC-001": ["I4-A-02"]}
check(all(any(mc in w for w in qd[i]["answer"]["wrong"]) for mc, its in MC.items() for i in its),
      "MC-006 is named where an LLM grade is trusted as truth (R-03, T-02); MC-001 where tokens are confused (A-02)")

r07 = qd["I4-R-07"]
check(r07["source"] == "AIQ-04-Q4" and r07["set"] == "interview" and r07["type"] == "R", "I4-R-07: set=interview, type R, source=AIQ-04-Q4")
check("ombharatiya/AI-Engineer-Interview-Questions @ e080df2" in r07["question"] and "`04-rag-and-retrieval/questions.md`" in r07["question"]
      and "Copyright (c) 2026 Om, MIT License" in r07["question"], "I4-R-07: the question carries the MIT notice and the pinned commit")
pre = r07["answer"]["preamble"]
quoted = [l[2:] for l in pre.splitlines() if l.startswith("> ") and not l.startswith("> **The repo's answer")]
if AIQ.exists():
    aiq = AIQ.read_text(encoding="utf-8")
    print(f"     interview file: {AIQ.name}, {len(aiq):,} chars, sha256 {hashlib.sha256(AIQ.read_bytes()).hexdigest()[:16]}... (read as text only)")
    verb = re.match(r'"(.+)"', r07["question"].splitlines()[0]).group(1)
    check(f"### 4. {verb}" in aiq, "I4-R-07: the quoted question is the repo's Q4 heading, verbatim")
    q4 = aiq[aiq.index("### 4. "):aiq.index("### 5. ")]
    check(len(quoted) >= 8 and all(x in q4 for x in quoted),
          f"I4-R-07: all {len(quoted)} quoted lines ({sum(len(x.split()) for x in quoted)} words) are exact substrings of Q4's answer")
    body = [l for l in q4.split("<b>Answer</b></summary>", 1)[1].split("</details>", 1)[0].splitlines() if l.strip()]
    check(body == quoted, f"I4-R-07: the quote is Q4's whole answer, line by line ({len(body)} non-empty lines)")
else:
    skip(f"I4-R-07 verbatim checks: the interview file was not found at {AIQ} (not fetched)")
check("Copyright (c) 2026 Om, MIT License" in pre and pre.index("> **The repo's answer") < pre.index("**Our check of that answer:**"),
      "I4-R-07: the repo's answer, with its notice, comes before our check and our model answer")
m07 = r07["answer"]["model"]
check(all(w in m07 for w in ("Proposition chunking", "decontextualisation", "parent", "66", "1,433", "source_ids", "faithfulness")),
      "I4-R-07: our model answer adds propositions (decontextualisation, parent return, cost 66 vs 1,433, source_ids, faithfulness)")

# ---------------------------------------------------------------- 2. the data inside the items (kit-measure definitions)
if PDF.exists():
    import pymupdf
    sys.path.insert(0, str(WS / "sources" / "verification" / "corrections"))
    import contracts_check as cc  # noqa: E402

    pdf_bytes = PDF.read_bytes()
    pages = [p.get_text() for p in pymupdf.open(PDF)]
    DOC = "\n".join(pages)
    md06 = (WS / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
    md07 = (WS / "07_SAMPLE_LESSON.md").read_text(encoding="utf-8")
    cc.RECIPE_06 = cc.code_blocks(cc.section(md06, "5.3 Corpus freezing"), "python")[0]
    manifest06 = cc.build_manifest("climate", pages, pdf_bytes, {**cc.PARSER, "version": pymupdf.VersionBind}, cc.CLEANING_NONE)
    STARTS = [r["doc_char_start"] for r in manifest06["docs"][0]["page_table"]]
    _core, chunking, _ = cc.load_07_modules(md07)
    chunks = [{"seq": c.seq, "char_start": c.char_start, "char_end": c.char_end}
              for c in chunking.chunk_document("climate", manifest06["snapshot_id"], pages,
                                               chunking.ChunkerConfig(name="recursive", size=1000, overlap=200, scope="per_page"))]
    TEXTS = {"climate": DOC}
    print(f"     corpus: sha256 {hashlib.sha256(pdf_bytes).hexdigest()[:12]}..., {len(pages)} pages, {len(DOC):,} chars, {len(chunks)} chunks")

    SENT_END = re.compile(r'[.!?]["”)\]]?(?=\s|$)')                       # i4_kit_measure.py, verbatim
    LINE_END = re.compile(r'[.!?:]["”)\]]?\s*$')

    def split_page(t):
        units, buf, pos = [], None, 0
        for ln in t.split("\n"):
            a, s = pos, ln.strip()
            pos += len(ln) + 1
            if not s:
                continue
            a2 = a + len(ln) - len(ln.lstrip())
            b2 = a + len(ln.rstrip())
            if buf is None and not LINE_END.search(s) and s[0].isupper() and len(s) < 80:
                units.append(("h", a2, b2))
                continue
            if buf is None:
                buf = a2
            for mt in SENT_END.finditer(ln):
                e = a + mt.end()
                if e <= buf:
                    continue
                units.append(("s", buf, e))
                buf = None
                rest = ln[mt.end():]
                if rest.strip():
                    buf = a + mt.end() + len(rest) - len(rest.lstrip())
        if buf is not None:
            units.append(("s", buf, len(t.rstrip())))
        return units

    UNITS = {}
    for pn, t in enumerate(pages, 1):
        for i, (k, a, b) in enumerate(split_page(t)):
            UNITS[f"{pn}:{i}"] = {"page": pn, "kind": k, "da": STARTS[pn - 1] + a, "db": STARTS[pn - 1] + b, "text": t[a:b]}
    STOP = set("""a an the is are was were be been being of in on at to for and or but with by as from that this these those
it its their them they such which who whom whose than then there here into over under about also can may might will would
should could has have had do does did not no nor so very via per each every all both other another some any many much more
most less least only just up down out off our your his her he she we you i if while when where what how why""".split())

    def stem(w):
        for suf in ("ing", "ed", "es", "s", "e"):
            if w.endswith(suf) and len(w) - len(suf) >= 3:
                return w[: -len(suf)]
        return w

    def words(t):
        t = re.sub(r"-\s*\n\s*", "-", t.lower())
        return {stem(w) for w in re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", t) if (len(w) > 1 or w.isdigit()) and w not in STOP}

    PRONOUN_START = re.compile(r"^(it|its|they|their|them|this|these|those|that|he|she|his|her|such)\b", re.I)
    nsent = sum(u["kind"] == "s" for u in UNITS.values())
    check(nsent == 621 and len(UNITS) == 907 and len(chunks) == 97, f"splitter and chunker reproduce K1/K3: {nsent} sentences, {len(UNITS)} units, {len(chunks)} chunks")

    def check_prop(text, sids, resolved):
        us = [UNITS[i] for i in sids]
        a, b = min(u["da"] for u in us), max(u["db"] for u in us)
        pg = us[0]["page"]
        before = DOC[STARTS[pg - 1]:a]
        res_ok = all(words(nm) <= words(before) for nm in resolved)
        allowed = set().union(*(words(u["text"]) for u in us)) | (set().union(set(), *(words(nm) for nm in resolved)) if res_ok else set())
        W = words(text)
        contain = [c["seq"] for c in chunks if c["char_start"] <= a and b <= c["char_end"]]
        return {"span": (a, b), "align": len(W & allowed) / len(W), "unsupported": sorted(W - allowed), "parents": contain,
                "resolved_ok": res_ok, "pronoun": bool(PRONOUN_START.match(text)), "one_page": len({u["page"] for u in us}) == 1}

    # I4-A-01: the quoted p.29 units and the model answer's propositions
    a01q = qd["I4-A-01"]["question"]
    quoted_units = dict(re.findall(r"^\[(29:\d)\] (?:\(heading\) )?(.+)$", a01q, re.M))
    check(all(re.sub(r"\s+", " ", UNITS[k]["text"]) == v for k, v in quoted_units.items()) and sorted(quoted_units) == ["29:6", "29:7", "29:8", "29:9"]
          and UNITS["29:6"]["kind"] == "h", "I4-A-01: the four p.29 units in the question equal the splitter's units 29:6-29:9 (29:6 a heading)")
    rows = re.findall(r"^(.+?\.)\s+\| \[([\d:, ]+)\] \|(.*)$", qd["I4-A-01"]["answer"]["model"], re.M)
    res = [check_prop(t, [s.strip() for s in ids_.split(",")], [x.strip() for x in r.split(",") if x.strip()]) for t, ids_, r in rows]
    for (t, ids_, r), x in zip(rows, res):
        print(f"     A-01 [{ids_}] align={x['align']:.3f} parents={x['parents']} resolved_ok={x['resolved_ok']} pronoun={x['pronoun']} | {t}")
    check(len(rows) == 8 and all(x["align"] == 1.0 and x["parents"] == [84] and x["resolved_ok"] and not x["pronoun"] and x["one_page"] for x in res)
          and sum(bool(r.strip()) for _, _, r in rows) == 3,
          "I4-A-01: the 8 model propositions: ids exist, align 1.000, no pronoun start, resolved names found earlier on p.29, one parent (chunk 84)")
    wrong = check_prop("Governments impose penalties for non-compliance.", ["29:8"], [])
    check(wrong["align"] < 1 and "government" in wrong["unsupported"], f"I4-A-01 wrong answer 2: 'Governments impose…' has align {wrong['align']:.3f} < 1 (unsupported {wrong['unsupported']})")
    check(bool(PRONOUN_START.match("This includes tracking emissions, verifying data, and imposing penalties.")), "I4-A-01 wrong answer 1 starts with a pronoun")

    # I4-A-03: the made-up list, its parents and the gold
    TUT = {p["prop_id"]: p for p in (json.loads(l) for l in (HERE / "i4_tutor_props.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}
    a03 = re.findall(r"^(\d)\s+(p\d\d-\d\d)\s+(\d+)\s+(.+)$", qd["I4-A-03"]["question"], re.M)
    par = []
    for rk, pid, pa, txt in a03:
        x = check_prop(TUT[pid]["text"], TUT[pid]["source_ids"], TUT[pid]["resolved"])
        par.append((x["parents"], int(pa), TUT[pid]["text"].startswith(txt.rstrip(". ").rstrip(",").rstrip("…").rstrip(".").strip()), x["span"]))
    check(len(a03) == 6 and all(p == [q] for p, q, _, _ in par) and all(t for _, _, t, _ in par),
          "I4-A-03: the 6 listed propositions exist in the tutor set, with the texts shown and exactly one parent each (as listed)")
    gold = [[[("climate", UNITS["10:16"]["da"], UNITS["10:16"]["db"])]]]
    relp = [c["seq"] for c in chunks if cc.rel(("climate", c["char_start"], c["char_end"]), gold, TEXTS)]
    check(relp == [28], f"I4-A-03: sentence 10:16 overlaps (any_overlap) only chunk {relp}")
    dedup = []
    for _, q_, _, _ in par:
        if q_ not in dedup:
            dedup.append(q_)
    rr_a = next(1 / i for i, p in enumerate(dedup, 1) if p in relp)
    top4 = len({q_ for _, q_, _, _ in par[:4]})
    rr_b = next(1 / i for i, (_, _, _, sp) in enumerate(par, 1) if cc.rel(("climate", *sp), gold, TEXTS))
    m03 = qd["I4-A-03"]["answer"]["model"]
    check(dedup == [27, 68, 28, 29] and f"{rr_a:.3f}" == "0.333" and top4 == 3 and rr_b == 0.25
          and "[27, 68, 28, 29]" in m03 and "0.333" in m03 and "3 distinct parents" in m03 and "0.25" in m03,
          f"I4-A-03: recomputed dedup {dedup}, arm (a) RR {rr_a:.3f}, {top4} distinct parents in the top 4, arm (b) RR {rr_b}")

    # I4-A-04: the word set and align of the wrong-year proposition (planted x-02)
    x02 = check_prop("The Paris Agreement was adopted in 2016.", ["10:7"], [])
    W02 = words("The Paris Agreement was adopted in 2016.")
    m04 = qd["I4-A-04"]["answer"]["model"]
    check(W02 == {"pari", "agreement", "adopt", "2016"} and f"{x02['align']:.3f}" == "0.750" and x02["unsupported"] == ["2016"]
          and "{pari, agreement, adopt, 2016}" in m04 and "0.750" in m04,
          f"I4-A-04: W(p) = {sorted(W02)}, align {x02['align']:.3f}, unsupported {x02['unsupported']} (as in the answer)")
    check(re.sub(r"\s+", " ", UNITS["10:7"]["text"]) in qd["I4-A-04"]["question"], "I4-A-04: the 10:7 sentence in the question equals the splitter's unit")

    # I4-A-05: Wilson intervals; I4-A-02: sums
    w = {f"{x}/{m}": cc.wilson(x, m) for x, m in ((27, 30), (57, 60), (54, 60))}
    a05 = qd["I4-A-05"]["question"] + qd["I4-A-05"]["answer"]["model"]
    check(all(f"[{lo:.3f}, {hi:.3f}]" in a05 for lo, hi in w.values()) and w["57/60"][0] >= 0.85 > w["27/30"][0],
          "I4-A-05: the three Wilson intervals recompute (cc.wilson), and only 57/60 clears 0.85")
    m02 = qd["I4-A-02"]["answer"]["model"]
    check(33 + 1400 == 1433 and 33 + 33 == 66 and "33 + 1,400 = 1,433" in m02 and "33 +    33 =    66" in m02,
          "I4-A-02: 33 + 1,400 = 1,433 and 33 + 33 = 66 as written")
else:
    skip(f"step 2 (data recomputed from the climate PDF): the PDF was not found at {PDF}")

# ---------------------------------------------------------------- 3. reread lines


def slug(t):
    t = re.sub(r"`", "", t).strip().lower()
    t = re.sub(r"[^\w\s-]", "", t)
    return t.replace(" ", "-")


def headings(path):
    out, seen_h, fence = [], {}, False
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*$", line)
        if m:
            s = slug(re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", m.group(2)))
            k = seen_h.get(s, -1) + 1
            seen_h[s] = k
            out.append((len(m.group(1)), m.group(2), s if k == 0 else f"{s}-{k}"))
    return out


def anchors(path):
    return {a for _, _, a in headings(path)} | set(re.findall(r'<a id="([^"]+)"', Path(path).read_text(encoding="utf-8")))


STEP_ANCHORS = ["answer", "theory", "glance", "dilution", "proposition", "decontext", "units", "prompt", "anchor", "align",
                "grade", "score", "relations", "cost", "project", "repo", "research", "book", "verify", "apply", "check"]
if LESSON.exists():
    lesson_ids = set(re.findall(r'\bid="([^"]+)"', LESSON.read_text(encoding="utf-8")))
    missing_steps = [a for a in STEP_ANCHORS if a not in lesson_ids]
    check(not missing_steps, f"the lesson {LESSON.name} exists and has the {len(STEP_ANCHORS)} step anchors of spec §2" + (f"; missing {missing_steps}" if missing_steps else ""))
else:
    lesson_ids = set(STEP_ANCHORS)
    print(f"     note: {LESSON.name} is not written yet (the tutor writes it); lesson anchors are taken from the build spec §2 list")

short_heads = [(t, a) for lvl, t, a in headings(SHORT) if lvl == 2]
step_anchor = {int(re.match(r"(\d+)\.", t).group(1)): a for t, a in short_heads if re.match(r"\d+\.", t)}
bad_rr, miss = [], []
for q in qs:
    rr = q["answer"]["reread"]
    if not ("../reading/I4_proposition_chunking.md#" in rr and "../lessons/I4_propositions.html#" in rr and re.search(r"book Ch4 p\.\d", rr)):
        bad_rr.append(q["id"])
    linked = re.findall(r"\.\./reading/I4_proposition_chunking\.md#([\w-]+)", rr)
    les = re.findall(r"\.\./lessons/I4_propositions\.html#([\w-]+)", rr)
    if not (all(step_anchor.get(s) in linked for s in SPEC[q["id"]][1]) and all(a in les for a in SPEC[q["id"]][2])):
        miss.append(q["id"])
check(not bad_rr, f"every reread links the reading file AND the lesson, and names a book page ({bad_rr or 'all 17'})")
check(not miss, f"every reread names the reading section(s) and lesson step(s) that teach the item ({miss or 'all 17'})")


# ---------------------------------------------------------------- 4. links and anchors
def links_in(text):
    body, fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if not fence:
            body.append(line)
    return re.findall(r"\]\(([^)\s]+)\)", "\n".join(body))


def bad_links(path, text):
    bad, links = [], links_in(text)
    for href in links:
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        target, _, anc = href.partition("#")
        tp = (Path(path).parent / target).resolve() if target else Path(path)
        if tp == LESSON.resolve():
            if anc and anc not in lesson_ids:
                bad.append(f"missing lesson anchor {href}")
            if not LESSON.exists() and anc:
                continue
        if not tp.exists() and tp != LESSON.resolve():
            bad.append(f"missing file {href}")
        elif tp.exists() and anc and tp.suffix == ".md" and anc not in anchors(tp):
            bad.append(f"missing anchor {href}")
    return links, bad


for name, path in (("question file", QF), ("reading file", SHORT)):
    links, bad = bad_links(path, Path(path).read_text(encoding="utf-8"))
    n_les = sum("I4_propositions.html" in h for h in links)
    check(not bad, f"{name}: {len(links)} links resolve ({sum('#' in h for h in links)} with #anchors; {n_les} into the lesson)"
          + ("" if not bad else ": " + "; ".join(bad[:8])))
inbound, bad_in = 0, []
MINE = {SHORT.resolve(), QF.resolve()}
for md in WS.rglob("*.md"):
    if md.resolve() in MINE or ".venv" in md.parts or "AI Eval" in md.parts:
        continue
    for href in links_in(md.read_text(encoding="utf-8", errors="ignore")):
        target, _, anc = href.partition("#")
        if not target or href.startswith("http"):
            continue
        tp = (md.parent / target).resolve()
        if tp in MINE:
            inbound += 1
            if anc and anc not in anchors(tp):
                bad_in.append(f"{md.relative_to(WS)} -> {href}")
check(not bad_in, f"{inbound} links from other workspace .md files into the two I4 kit files resolve" + (f": {bad_in}" if bad_in else ""))
if LESSON.exists():
    lt = LESSON.read_text(encoding="utf-8")
    into = re.findall(r'href="([^"]*I4_proposition_chunking\.md#[^"]+)"', lt)
    bad_l = [h for h in into if h.split("#", 1)[1] not in anchors(SHORT)]
    check(not bad_l, f"the lesson's {len(into)} links into the reading file's sections resolve" + (f": {bad_l}" if bad_l else ""))

# ---------------------------------------------------------------- 5. reading file shape, length and labels


def nwords(text):
    return len(re.sub(r"```.*?```", " ", text, flags=re.S).split())


print(f"     word count: reading file {nwords(short)} prose words (code blocks removed; {len(short.split())} with them); "
      f"question file {len(qtext.split())}")
check(1800 <= nwords(short) <= 3000, f"reading file prose within 1,800-3,000 words ({nwords(short)})")
check(short.startswith("<!-- kit:reading concept=I4 depth=short version=1 -->"), "reading file header line")
check(all(h in short for h in ("**What this is:**", "**What this is not:**", "> **Read in the book:**", "## Check yourself")),
      "reading file has What this is / is not, the book box and Check yourself (FORMAT §3)")
box = short[short.index("> **Read in the book:**"):].split("\n\n", 1)[0]
check("Ch4 p.4–12/15" in box and "not re-opened" in box and "UNVERIFIED" in box,
      "book box names Ch4 p.4–12/15 and says the pages were not re-opened in this session (UNVERIFIED)")
FIXED = ["1. One vector for many facts", "2. What a proposition is", "3. Decontextualisation: names instead of pronouns",
         "4. Number the sentences first", "5. The prompt and the output schema", "6. Every proposition points back to its source",
         "7. Checking the rewrite: alignment and its blind spots", "8. The quality grade is a filter", "9. Three ways to score propositions",
         "10. What atomic facts lose", "11. What it costs", "12. Proposition chunking in your project", "13. When not to use it", "Check yourself"]
check([t for t, _ in short_heads] == FIXED, f"the 14 '## ' headings are exactly the spec's, in order ({len(short_heads)})")
secs = {int(s.split(".")[0]): s for s in re.split(r"^## ", short, flags=re.M)[1:] if re.match(r"\d+\.", s)}
BEATS = (r"\*\*The setup\.\*\*", r"\*\*The result\*\*|\*\*The result\.\*\*", r"\*\*What this means\.\*\*", r"\*\*For your project:\*\*")
nobeat = [k for k in range(1, 13) if not all(re.search(b, secs[k]) for b in BEATS)]
check(not nobeat, f"sections 1-12 each have the four beats setup → result → what it means → for your project ({nobeat or 'all 12'})")
counts = re.search(r"(\d+) cold question before reading, (\d+) after, (\d+) for a later review, and (\d+) interview", short)
check("(../questions/I4_questions.md)" in short and counts and tuple(map(int, counts.groups())) == (cnt("pre"), cnt("main"), cnt("review"), cnt("interview")),
      "Check yourself links the question file and states the right item counts per set")
check(all("hand-written by the tutor" in t.lower() or "hand-written*: the 40" in t.lower() for t in (short, qtext))
      and all("made-up order" in t.lower() for t in (short, qtext)) and all("ASSUMED" in t for t in (short, qtext)),
      "honesty labels in both files: tutor hand-written propositions, made-up orders, ASSUMED token sizes")
check("no llm has written a proposition" in short.lower() and "no llm has written a proposition" in qtext.lower(),
      "both files say that no LLM has written a proposition yet")

# ---------------------------------------------------------------- 6. book pages; copyright
RESEARCH_PAGES = set(range(4, 14))                                          # research I4 §1: Ch4 p.4-13/15
cites = set()
for text in (qtext, short):
    for m in re.finditer(r"\b(Ch\d+|App|Intro) p\.(\d+)(?:–(\d+))?/(\d+)", text):
        for p in range(int(m.group(2)), int(m.group(3) or m.group(2)) + 1):
            cites.add((m.group(1), p, int(m.group(4))))
    for m in re.finditer(r"\b(Ch\d+) p\.\d+(?:–\d+)?/\d+ and p\.(\d+)(?:–(\d+))?/(\d+)", text):
        for p in range(int(m.group(2)), int(m.group(3) or m.group(2)) + 1):
            cites.add((m.group(1), p, int(m.group(4))))
for m in re.finditer(r"(?<!Ch4 )\bp\.(\d+)(?:–(\d+))?/15\b", short):
    for p in range(int(m.group(1)), int(m.group(2) or m.group(1)) + 1):
        cites.add(("Ch4", p, 15))
badc = [c for c in sorted(cites) if c[0] != "Ch4" or c[2] != 15 or c[1] not in RESEARCH_PAGES]
check(not badc, f"{len(cites)} distinct book pages cited, all Ch4 …/15 and on the research's page list (p.4–13/15)" + (f"; bad: {badc}" if badc else ""))
TOK = re.compile(r"[a-z0-9]+")


def toks(t):
    t = t.lower().replace("’", "").replace("'", "").replace("‘", "")
    return TOK.findall(t)


def longest_shared(text, grams):
    tk_all, line_of = [], []
    for ln, line in enumerate(text.splitlines(), 1):
        t = toks(line)
        tk_all += t
        line_of += [ln] * len(t)
    for nn in range(15, 5, -1):
        found = [i for i in range(len(tk_all) - nn + 1) if hash(tuple(tk_all[i:i + nn])) in grams[nn]]
        if found:
            return nn, sorted({line_of[i] for i in found}) if nn == 15 else []
    return 0, []


def gramset(token_lists):
    g = {nn: set() for nn in range(6, 16)}
    for tk in token_lists:
        for nn in g:
            for i in range(len(tk) - nn + 1):
                g[nn].add(hash(tuple(tk[i:i + nn])))
    return g


if BOOK.exists() and any(BOOK.glob("*.pdf")):
    import pymupdf
    book_tokens = [toks(pg.get_text()) for f in sorted(BOOK.glob("*.pdf")) for pg in pymupdf.open(f)]
    grams = gramset(book_tokens)
    print(f"     book: {len(book_tokens)} pages (held in memory only)")
    for name, text in (("question file", qtext), ("reading file", short)):
        ln, hits = longest_shared(text, grams)
        check(not hits, f"{name}: no 15-word run shared with the book (longest: {ln or '<6'} words)" + (f"; lines {hits[:10]}" if hits else ""))
else:
    skip("(book not present): the book page-exists check and the 15-word copyright check against the book; "
         f"looked in {BOOK}")
if UPNB.exists():
    nb = json.loads(UPNB.read_text(encoding="utf-8"))
    grams = gramset([toks("".join(c["source"])) for c in nb["cells"]])
    for name, text in (("question file", qtext), ("reading file", short)):
        ln, hits = longest_shared(text, grams)
        check(not hits, f"{name}: no 15-word run shared with the upstream notebook's cells (longest: {ln or '<6'} words)"
              + (f"; lines {hits[:10]}" if hits else ""))
else:
    skip(f"15-word check against the upstream notebook: not found at {UPNB}")

# ---------------------------------------------------------------- 7. numbers are traceable
outs = {"out_i4_kit_measure": (HERE / "out_i4_kit_measure.txt").read_text(encoding="utf-8"),
        "I4_FACTS": (HERE / "I4_FACTS.md").read_text(encoding="utf-8")}
NUM = re.compile(r"(?<![\w.,/])(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?![\w/])")
pool = set()
for t in outs.values():
    for m in re.finditer(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?", t):
        pool.add(m.group(0).replace(",", ""))
DERIVED = {  # arithmetic shown next to each number in the text, or an item's own data
    "84": "I4-A-01: the parent chunk of the p.29 propositions (recomputed in step 2)",
    "0.25": "I4-A-03: arm (b) RR = 1/4 (shown; recomputed in step 2)",
    "100": "I4-A-02 wrong answer: 100 characters per proposition (the wrong idea's own number)",
    "140000": "I4-A-02 wrong answer: 1,400 x 100 (the wrong idea's arithmetic)",
    "8.6": "8.63 days rounded (K9)",
    "0.80": "I4-T-02: the item's own data (hand-checked faithfulness 0.80, from the build spec's item list)",
}
unmatched = {}
for name, text in (("question file", qtext), ("reading file", short)):
    text = "\n".join(l for l in text.splitlines() if not l.startswith(">"))                 # verbatim repo quote (step 1), book box
    text = re.sub(r"\]\([^)]*\)", "]", text)                                                 # link targets
    text = re.sub(r"\b(Ch\d+|App) p\.\d+(?:–\d+)?/\d+|\bp\.\d+(?:–\d+)?/\d+", " ", text)      # book pages
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b|\b(?:19|20)\d\d\b", " ", text)                     # dates, years
    text = re.sub(r"\b\d+\.\d+\.\d+\b", " ", text)                                           # versions
    text = re.sub(r"\b\d+:\d+\b", " ", text)                                                 # unit ids page:i
    text = re.sub(r"@\d+|\b[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9.]+)+\b|§[\d.]+|\b[KSDCLIP]\d+\b|#\d+|e080df2|cells? \d+(?:[–, ]+\d+)*(?: and \d+)?", " ", text)
    for m in NUM.finditer(text):
        s = m.group(0).replace(",", "")
        x = float(s)
        if "." not in s and x < 10:
            continue
        if s in DERIVED or s in pool:
            continue
        unmatched.setdefault(m.group(0), set()).add(name)
check(not unmatched, "every decimal and every integer >= 10 in both files is printed in out_i4_kit_measure.txt, written in I4_FACTS.md, "
      f"or on the DERIVED list ({len(DERIVED)} entries)" + (f"; unmatched: {unmatched}" if unmatched else ""))
KEY = ["0.577", "0.667", "0.400", "0.750", "1.54", "2.25", "0.333", "0.500", "0.863", "0.744", "1,433", "199,650", "1,725,450",
       "8.63", "14.4", "3,858", "682", "621", "286", "907"]
check(all(k in outs["out_i4_kit_measure"] or k.replace(",", "") in outs["out_i4_kit_measure"] for k in KEY)
      and all(any(k in t for t in (qtext, short)) for k in KEY),
      f"{len(KEY)} key numbers are printed by the kit measure and quoted in the question or reading file")

# ---------------------------------------------------------------- 8. coach-banned phrases
BANNED = ["a guide says", "well above zero", "narrow positive band", "who is right", "sixth", "add a pdf", "adding a document",
          "new document", "another pdf", "tenant", "300 pdf"]
hits = {nm: [w for w in BANNED if w in t.lower()] for nm, t in (("questions", qtext), ("reading", short))}
check(not any(hits.values()), f"none of the {len(BANNED)} coach-banned phrases appears ({hits})")
check("transfer_seed_bank" not in qtext and "transfer_seed_bank" not in short, "the hidden seed bank is not referenced")

# ---------------------------------------------------------------- 9. the kit's own format check
r = subprocess.run([sys.executable, str(WS / "study" / "quiz.py"), "--check"], capture_output=True, text=True, encoding="utf-8", cwd=str(WS))
line = next((l for l in r.stdout.splitlines() if "I4_questions.md" in l), "")
check(line.strip().startswith("OK") and "17 questions" in line, f"study/quiz.py --check passes for I4 ({line.strip()})")
check(r.returncode == 0, f"study/quiz.py --check exits 0 for all files (exit {r.returncode}; {r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''})")

print(f"\n{n - fails}/{n} checks passed, {fails} failed, {skips} skipped")
sys.exit(0 if fails == 0 else 1)
