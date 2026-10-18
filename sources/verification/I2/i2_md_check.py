"""I2: check the study-kit Markdown files of 2026-10-18 (question file and short reading file).

1. study/questions/I2_questions.md loads with the kit's own parser and passes kit.lint_questions; the 20 ids of the
   plan below (research phase_04_indexing.md, Concept I2 §3 titles + extra items so that every lesson step #s1-#s13
   is tested by a main item), in their sets and types; FORMAT field rules (2 hints, Hint 3 only on A items, 2-5 key
   points, 1-2 'for a 4', 1-3 wrong answers); at most 2 external items; the interview item I2-T-03 quotes AIQ-04 Q4
   verbatim with the MIT notice, its quoted paragraphs are exact substrings of the pinned repo file, the repo's answer
   comes before ours, and our answer carries the I2-E8 correction (no consistent winner; the heading path is I5).
2. Every reread line links the short reading file, the HTML lesson (#sN) and names a book page; each item's reread
   names the reading section(s) and lesson step(s) the plan assigns to it; the main items together test #s1-#s13.
3. Every relative link in the two files resolves, with its #anchor (GitHub rule). Links into the HTML lesson are
   checked against its ids if the file exists, else against the id list of I2_BUILD_SPEC.md §3.
4. The reading file's shape (FORMAT §3): header, What this is / is not, the book box (marked not re-opened),
   sections 1-14 in the lesson's Short order, 14 = 'When not to use it', then 'Check yourself'; 'The answer first' in
   sections 1-13; 1,800-3,000 words without code blocks.
5. Page references: every book page is written 'ChN p.x/y' or 'ChN p.x–y/y' and is one of the four pages of research
   §1 (per 04/07; not re-opened); no other 'p.N' form appears (corpus pages are written 'page N').
6. Numbers: every decimal, and every integer >= 10, in both files matches a value in I2_FACTS.md or
   out_i2_measure.txt, or is on the FORMULA / TOY list below (each with its reason).
7. No run of 15 consecutive words is shared with AIQ-04 Q4's answer outside the quoted preamble.
8. The coach-banned phrases (the P2/P4 lists plus the wording of the C1/C4/C7 seeds and the C2/C4 reserves that sit
   near I2) are absent, and no run of 10 consecutive words is shared with sources/coach/transfer_seed_bank.md
   (read in memory only; nothing from it is printed).
9. `uv run python study/quiz.py --check` passes.

Run from the workspace root (the AIQ file is the pinned raw download of ombharatiya/AI-Engineer-Interview-Questions
@ e080df2; pass its path, or set I2_AIQ):
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I2/i2_md_check.py [path/to/04-rag-and-retrieval/questions.md] \
        > sources/verification/I2/out_i2_md_check.txt
"""
import os
import re
import subprocess
import sys
from pathlib import Path

WS = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
QF = WS / "study" / "questions" / "I2_questions.md"
SHORT = WS / "study" / "reading" / "I2_structure_chunking.md"
LESSON = WS / "study" / "lessons" / "I2_structure_chunking.html"
SEEDS = WS / "sources" / "coach" / "transfer_seed_bank.md"
AIQ_CANDIDATES = [Path(a) for a in sys.argv[1:2]] + ([Path(os.environ["I2_AIQ"])] if os.environ.get("I2_AIQ") else []) + [
    Path("/tmp/claude-0/dl/repo/aiq/questions.md"),
    WS.parent / "upstream" / "AI-Engineer-Interview-Questions" / "04-rag-and-retrieval" / "questions.md"]
fails = 0
n = 0


def check(ok, label):
    global fails, n
    n += 1
    fails += not ok
    print(("PASS " if ok else "FAIL ") + label)


# ---------------------------------------------------------------- 1. question file
sys.path.insert(0, str(WS / "study"))
import kit  # noqa: E402

qs = kit.parse_questions(QF)
qtext = QF.read_text(encoding="utf-8")
short = SHORT.read_text(encoding="utf-8")
problems = kit.lint_questions(QF)
check(not problems, f"kit.lint_questions: {problems or 'no problems'}")
check(qtext.startswith("<!-- kit:questions concept=I2 version=1 -->"), "question file header line")

# id: (set, reading sections that teach it, lesson steps it tests)
SPEC = {
    "I2-PRE-01": ("pre", [1], [1]), "I2-PRE-02": ("pre", [2, 4], [2]),
    "I2-R-01": ("main", [2], [2]), "I2-R-02": ("main", [3], [3]), "I2-R-03": ("main", [7, 11], [7]),
    "I2-R-04": ("main", [6], [6]), "I2-R-05": ("main", [1, 10], [1, 10]), "I2-R-06": ("main", [6, 5], [6]),
    "I2-R-07": ("main", [8, 4], [8, 4]), "I2-R-08": ("main", [12], [12]),
    "I2-A-01": ("main", [4, 5], [4]), "I2-A-02": ("main", [9], [9]), "I2-A-03": ("main", [11, 8], [11]),
    "I2-A-04": ("main", [7, 5], [7]), "I2-A-05": ("main", [5, 4], [5]), "I2-A-06": ("main", [9, 7], [9]),
    "I2-A-07": ("main", [13], [13]),
    "I2-T-01": ("main", [2, 5, 14], [5, 12]), "I2-T-02": ("main", [13, 10], [13]),
    "I2-T-03": ("interview", [13, 14, 7], [13]),
}
RESEARCH_TITLES = {  # research §3 title -> item
    "Which span-dict field and which bit tell you a span is bold?": "I2-R-01",
    "Why is the body font size estimated by character count, not by span count?": "I2-R-02",
    "Why can a structure-aware chunk contain its own heading but not its parent headings?": "I2-R-03",
    "What does a Markdown header splitter lose that the course chunker keeps?": "I2-R-04",
    "6 line records": "I2-A-01", "2,300 characters": "I2-A-02", "no section crossing": "I2-A-03",
    "Paris Agreement": "I2-A-04",
    "Corpus T has two-column papers with numbered, bold, body-size headings and a PDF outline": "I2-T-01",
    "v1.1 wins on the boundary bucket but loses on factual-single-span": "I2-T-02",
}
ids = [q["id"] for q in qs]
qd = {q["id"]: q for q in qs}
check(sorted(ids) == sorted(SPEC) and 17 <= len(ids) <= 21, f"the {len(SPEC)} ids of the plan, no more, no less ({len(ids)}; brief: 17-21)")
check(len(set(ids)) == len(ids), "ids unique")
check(all(qd[i]["set"] == s for i, (s, _, _) in SPEC.items() if i in qd), "each id is in the plan's set")
check(all(q["id"].split("-")[1] == q["type"] or q["id"].startswith("I2-PRE") for q in qs), "id letter = type")
check(ids[:2] == ["I2-PRE-01", "I2-PRE-02"] and sum(q["set"] == "pre" for q in qs) == 2, "the 2 set=pre items come first, in order")
types = {t: sum(1 for q in qs if q["type"] == t and q["set"] == "main") for t in "RAT"}
check(types["R"] >= 4 and types["A"] >= 4 and types["T"] >= 2, f"main items cover research §3's 4 R / 4 A / 2 T at least ({types})")
title_miss = [t for t, i in RESEARCH_TITLES.items() if t.split(" (")[0] not in qd.get(i, {}).get("question", "")
              and not (i == "I2-A-01" and "line" in qd.get(i, {}).get("question", "")
                       or i == "I2-A-03" and "section crossing" in qd.get(i, {}).get("question", ""))]
check(not title_miss, f"each research §3 title is asked by its item ({title_miss or 'all 10'})")
blocks = re.findall(r"<!-- q (.*?) -->(.*?)<!-- /q -->", qtext, re.S)
hint_ok = all(("<summary>Hint 1</summary>" in b and "<summary>Hint 2</summary>" in b)
              and ("<summary>Hint 3</summary>" not in b or "type=A" in h) for h, b in blocks)
check(hint_ok and len(blocks) == len(SPEC), "every item has Hint 1 and Hint 2; Hint 3 only on A items")
check(all(2 <= len(q["answer"]["keys"]) <= 5 for q in qs), "2-5 key points per item")
check(all(1 <= len(q["answer"]["four"]) <= 2 for q in qs), "1-2 'for a 4' points per item")
check(all(1 <= len(q["answer"]["wrong"]) <= 3 for q in qs), "1-3 common wrong answers per item")
ext = [q["id"] for q in qs if q.get("source")]
check(len(ext) <= 2 and [q["id"] for q in qs if q["set"] == "interview"] == ["I2-T-03"],
      f"exactly one interview item, at most 2 external items ({ext})")
aiq_path = next((p for p in AIQ_CANDIDATES if p.exists()), None)
check(aiq_path is not None, f"the pinned AIQ file is readable ({aiq_path})")
aiq = aiq_path.read_text(encoding="utf-8") if aiq_path else ""
q4_head = "What chunking strategies do you know, and how do you pick one?"
q4_block = aiq.split(f"### 4. {q4_head}", 1)[1].split("\n### 5.", 1)[0] if f"### 4. {q4_head}" in aiq else ""
t03 = qd["I2-T-03"]
check(bool(q4_block) and q4_head in t03["question"], "I2-T-03 quotes the repo's Q4 heading verbatim")
check("Copyright (c) 2026 Om, MIT License" in t03["question"] and "e080df2" in t03["question"]
      and "04-rag-and-retrieval/questions.md" in t03["question"] and t03.get("source") == "AIQ-04-Q4",
      "I2-T-03 carries the MIT notice, the pinned commit, the path and source=AIQ-04-Q4")
b03 = blocks[ids.index("I2-T-03")][1]
quoted = re.findall(r"^> (.+)$", b03, re.M)
check(len(quoted) >= 3 and all(p in q4_block for p in quoted), f"I2-T-03: the {len(quoted)} quoted lines are exact substrings of the repo's Q4 answer")
check(b03.find("> - **Structure-aware**") >= 0 and b03.find("> - **Structure-aware**") < b03.find("**Model answer:**"),
      "I2-T-03: the repo's answer (with its Structure-aware bullet) comes before ours")
model03 = t03["answer"]["model"].lower()
check("no consistent winner" in model03 and "i5" in model03 and "inconclusive" in model03,
      "I2-T-03: our answer states the I2-E8 correction (no consistent winner; the heading path is I5's claim; inconclusive here)")
check(not re.search(r"\bQ1[34]\b|AIQ-04-Q1[34]", qtext + short), "AIQ-04 Q13 (a coach seed) and Q14 are not used")

# ---------------------------------------------------------------- 2. reread lines


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


SPEC_IDS = ["answer", "theory", "formulas"] + [f"s{i}" for i in range(1, 14)] + ["f1", "f2", "f3", "f4", "verify", "apply", "llmops", "check", "sources"]
if LESSON.exists():
    lesson_ids = set(re.findall(r'\bid="([^"]+)"', LESSON.read_text(encoding="utf-8")))
    lesson_src = f"the lesson file's ids ({len(lesson_ids)})"
else:
    lesson_ids = set(SPEC_IDS)
    lesson_src = "I2_BUILD_SPEC §3's id list (the lesson HTML does not exist yet)"
short_heads = [(t, a) for lvl, t, a in headings(SHORT) if lvl == 2]
step_anchor = {int(re.match(r"(\d+)\.", t).group(1)): a for t, a in short_heads if re.match(r"\d+\.", t)}
bad_rr, miss_sec, miss_step = [], [], []
for q in qs:
    rr = q["answer"]["reread"]
    if not ("../reading/I2_structure_chunking.md#" in rr and "../lessons/I2_structure_chunking.html#s" in rr
            and re.search(r"book Ch\d+ p\.\d", rr)):
        bad_rr.append(q["id"])
    linked = re.findall(r"\.\./reading/I2_structure_chunking\.md#([\w-]+)", rr)
    if not all(step_anchor.get(s) in linked for s in SPEC[q["id"]][1]):
        miss_sec.append(q["id"])
    lsteps = re.findall(r"\.\./lessons/I2_structure_chunking\.html#s(\d+)", rr)
    if sorted(map(int, lsteps)) != sorted(SPEC[q["id"]][2]):
        miss_step.append(q["id"])
check(not bad_rr, f"every reread links the reading file, the lesson (#sN) and a book page ({bad_rr or f'all {len(qs)}'})")
check(not miss_sec, f"every reread names the reading section(s) the plan assigns ({miss_sec or f'all {len(qs)}'})")
check(not miss_step, f"every reread names exactly the lesson step(s) the plan assigns ({miss_step or f'all {len(qs)}'})")
covered = sorted({s for i, (st, _, steps) in SPEC.items() if st == "main" for s in steps})
check(covered == list(range(1, 14)), f"main items test every lesson step #s1-#s13 ({covered})")
print("     items: " + " · ".join(f"{i} {qd[i]['type']}/{qd[i]['set']} s{','.join(map(str, SPEC[i][2]))}" for i in ids))


# ---------------------------------------------------------------- 3. links and anchors
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
            if anc not in lesson_ids:
                bad.append(f"missing lesson id {href}")
            continue
        if not tp.exists():
            bad.append(f"missing file {href}")
        elif anc and tp.suffix == ".md" and anc not in anchors(tp):
            bad.append(f"missing anchor {href}")
    return links, bad


for name, path in (("question file", QF), ("reading file", SHORT)):
    links, bad = bad_links(path, Path(path).read_text(encoding="utf-8"))
    nl = sum("I2_structure_chunking.html#" in h for h in links)
    check(not bad, f"{name}: {len(links)} links resolve ({sum('#' in h for h in links)} with #anchors; {nl} lesson ids checked against {lesson_src})"
          + ("" if not bad else ": " + "; ".join(bad[:8])))
inbound, bad_in = 0, []
MINE = {SHORT.resolve(), QF.resolve()}
for md in WS.rglob("*.md"):
    if md.resolve() in MINE or ".venv" in md.parts or "upstream" in md.parts:
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
check(not bad_in, f"{inbound} links from other workspace files into the two I2 kit files resolve" + (f": {bad_in}" if bad_in else ""))


# ---------------------------------------------------------------- 4. reading file shape
def words(text):
    return len(re.sub(r"```.*?```", " ", text, flags=re.S).split())


wc = words(short)
print(f"     word count: reading file {wc} (code blocks removed); question file {len(qtext.split())}")
check(1800 <= wc <= 3000, f"reading file is 1,800-3,000 words without code blocks ({wc})")
check(short.startswith("<!-- kit:reading concept=I2 depth=short version=1 -->"), "reading file header line")
box = next((l for l in short.splitlines() if l.startswith("> **Read in the book:**")), "")
check(all(h in short for h in ("**What this is:**", "**What this is not:**", "## Check yourself")) and box
      and "not re-opened in this session" in box and "per 04/07" in box,
      "reading file has What this is / is not, the book box (per 04/07; not re-opened in this session) and Check yourself")
STEP_WORDS = {1: ("failure",), 2: ("inside the pdf", "bold"), 3: ("body size",), 4: ("headings", "size"), 5: ("error modes", "repeat"),
              6: ("aligning",), 7: ("section tree", "breadcrumb"), 8: ("split level",), 9: ("balanced", "merging"),
              10: ("continuation",), 11: ("invariants",), 12: ("eye inspection",), 13: ("measuring", "inconclusive")}
titles = [t for t, _ in short_heads]
numbered = [t for t in titles if re.match(r"\d+\.", t)]
check([int(t.split(".")[0]) for t in numbered] == list(range(1, 15)), f"sections ## 1. ... ## 14. in order ({len(numbered)})")
check(all(all(w in numbered[s - 1].lower() for w in ws) for s, ws in STEP_WORDS.items()),
      "sections 1-13 follow the lesson's Short path (failure ... measuring: inconclusive)")
check(numbered[13].lower().startswith("14. when not") and titles[-1] == "Check yourself", "section 14 is 'When not to use it', then 'Check yourself'")
secs = re.split(r"^## ", short, flags=re.M)[1:]
check(sum("**The answer first:**" in s for s in secs if re.match(r"\d+\.", s) and int(s.split(".")[0]) <= 13) == 13,
      "sections 1-13 each open with 'The answer first'")
check("study/questions/I2_questions.md" in short.split("## Check yourself", 1)[1], "Check yourself names the question file")
check("inconclusive" in secs[12].lower() and "0 of 8" in secs[12], "§13 states the verdict (inconclusive) and the empty boundary bucket (0 of 8)")

# ---------------------------------------------------------------- 5. page references
ALLOWED = {("Ch7", "1–2", "11"), ("Ch7", "8", "11"), ("Ch9", "10–11", "14"), ("Ch14", "4–5", "13")}
refs, badp, stray = [], [], []
for name, text in (("questions", qtext), ("reading", short)):
    for m in re.finditer(r"\b(Ch\d+|App|Intro) p\.(\d+(?:–\d+)?)/(\d+)", text):
        refs.append((m.group(1), m.group(2), m.group(3)))
        if (m.group(1), m.group(2), m.group(3)) not in ALLOWED:
            badp.append(f"{name}: {m.group(0)}")
    for m in re.finditer(r"\bpp?\.\s?\d", text):
        pre = text[max(0, m.start() - 6):m.start()]
        if not re.search(r"(Ch\d+|App|Intro) $", pre):
            stray.append(f"{name}: …{text[max(0, m.start() - 10):m.end() + 6]!r}")
    for m in re.finditer(r"\b(Ch\d+) p\.\d+-\d+/", text):
        badp.append(f"{name}: hyphen instead of en dash {m.group(0)}")
check(not badp, f"{len(refs)} book page references, all well-formed and among research §1's four pages" + (f"; bad: {badp}" if badp else ""))
check(not stray, "no other 'p.N' form (corpus pages are written 'page N')" + (f"; stray: {stray[:6]}" if stray else ""))
nore = [q["id"] for q in qs if "not re-opened" not in q["answer"]["reread"]]
check(not nore, f"every reread marks its book page 'not re-opened' ({nore or 'all'})")

# ---------------------------------------------------------------- 6. numbers are traceable
srcs = {"I2_FACTS": (HERE / "I2_FACTS.md").read_text(encoding="utf-8"),
        "out_i2_measure": (HERE / "out_i2_measure.txt").read_text(encoding="utf-8")}
NUM = re.compile(r"(?<![\w.,/])(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?![\w/])")
pool = set()
for t in srcs.values():
    for m in re.finditer(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?", t):
        pool.add(m.group(0).replace(",", ""))
FORMULA = {  # computed next to where it appears
    "585": "290 + 295 (S7 lengths; A-06 and reading §9)", "892": "290 + 295 + 307 (a wrong answer's arithmetic)",
    "1254": "585 + 307 + 362 = 290 + 295 + 307 + 362 (A-06 self-check)",
    "766.7": "2300 / 3 (A-02)", "767": "2300 / 3 rounded (A-02)", "766": "2300 - 2 x 767 (A-02)",
    "1533": "2 x 2300 / 3 (A-02, second ideal cut)", "383": "half a piece, 766.7 / 2 (A-02)", "1150": "2300 / 2 (a wrong answer)",
    "100": "100% = every title aligned (T-01)",
}
TOY = {  # made-up data, labelled toy in the item
    "2300": "A-02's section length (research §3 title)", "2.3": "a numbered-heading example ('2.3 Methods')",
    "900": "A-03 toy ranges", "2100": "A-03 toy ranges", "2600": "A-03 toy ranges", "1500": "A-03 toy ranges",
    "2200": "A-03 toy ranges", "300": "A-02 naive 1,000 + 1,000 + 300 (research §3 title)", "600": "A-03 fixed c3 length", "500": "A-03 fixed c4 length",
}
unmatched, toy_used = {}, set()
for name, text in (("question file", qtext), ("reading file", short)):
    text = "\n".join(l for l in text.splitlines() if not l.startswith(("> ", ">")))       # verbatim AIQ quote, book box
    text = re.sub(r"\]\([^)]*\)", "]", text)
    text = re.sub(r"\b(Ch\d+|App) p\.\d+(?:–\d+)?/\d+", " ", text)
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b|\b(?:19|20)\d\d\b", " ", text)                     # dates, years
    text = re.sub(r"\b\d+\.\d+\.\d+\b", " ", text)                                           # versions
    text = re.sub(r"\b[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9.]+)+\b|§[\d.]+|\b[SKQEDOCMRIPXVT]\d+\b|#s?\d+|e080df2|ea07572562ac|L\d+", " ", text)
    text = re.sub(r"\b\d+(?:st|nd|th)\b|\bv\d(?:\.\d)?\b|\bper \d\d(?:/\d\d)?\b", " ", text)
    for m in NUM.finditer(text):
        s = m.group(0).replace(",", "")
        x = float(s)
        if "." not in s and x < 10:
            continue
        if s in FORMULA or s in TOY:
            toy_used.add(s)
            continue
        if s not in pool:
            unmatched.setdefault(m.group(0), set()).add(name)
check(not unmatched, "every decimal and every integer >= 10 is in I2_FACTS / out_i2_measure or on the FORMULA / TOY list"
      + (f"; unmatched: {unmatched}" if unmatched else f" ({len(toy_used)} FORMULA/TOY values used)"))
KEY = ["192 of 282", "68.1%", "63,762", "90.6%", "282 of 282", "[2418, 2423)", "2424", "1,004", "341", "663", "990", "945",
       "3,432", "0.708", "0.625", "0.917", "620.5", "857.9", "117", "209", "139", "0 of 8", "33 of 33"]
miss_src = [k for k in KEY if not any(k in t or k.replace(",", "") in t for t in srcs.values())]
miss_md = [k for k in KEY if k not in short and k not in qtext]
check(not miss_src and not miss_md, f"{len(KEY)} key numbers are printed by the run and quoted in the kit files"
      + (f"; not in sources {miss_src}; not quoted {miss_md}" if miss_src or miss_md else ""))

# ---------------------------------------------------------------- 7. no 15-word run shared with the AIQ answer
TOK = re.compile(r"[a-z0-9]+")


def toks(t):
    return TOK.findall(t.lower().replace("’", "").replace("'", ""))


def shared_run(text, ref_tokens, nn):
    grams = {tuple(ref_tokens[i:i + nn]) for i in range(len(ref_tokens) - nn + 1)}
    tk, line_of = [], []
    for ln, line in enumerate(text.splitlines(), 1):
        t = toks(line)
        tk += t
        line_of += [ln] * len(t)
    return sorted({line_of[i] for i in range(len(tk) - nn + 1) if tuple(tk[i:i + nn]) in grams})


aiq_tokens = toks(q4_block)
for name, text in (("question file", qtext), ("reading file", short)):
    outside = "\n".join("" if l.startswith(">") else l for l in text.splitlines())
    hits = shared_run(outside, aiq_tokens, 15)
    check(not hits, f"{name}: no 15-word run shared with AIQ-04 Q4's answer outside the quoted preamble" + (f"; lines {hits[:10]}" if hits else ""))

# ---------------------------------------------------------------- 8. coach-banned phrases and hidden seeds
BANNED = ["a guide says", "well above zero", "narrow positive band", "who is right", "sixth", "add a pdf", "adding a document",
          "new document", "another pdf", "tenant", "300 pdf", "share of queries", "fraction of queries", "without reading",
          "half noise", "three stages", "silently corrupted", "gibberish", "badly parsed", "parse corruption", "chile",
          "zero rows", "non-terminating", "two companies", "harvey", "defined term", "q48", "q50"]
hits = {nm: [w for w in BANNED if w in t.lower()] for nm, t in (("questions", qtext), ("reading", short))}
check(not any(hits.values()), f"none of the {len(BANNED)} coach-banned phrases appears ({hits})")
seed_tokens = toks(SEEDS.read_text(encoding="utf-8")) if SEEDS.exists() else []
for name, text in (("question file", qtext), ("reading file", short)):
    hs = shared_run(text, seed_tokens, 10)
    check(bool(seed_tokens) and not hs, f"{name}: no 10-word run shared with the coach's seed bank (held in memory, not printed)"
          + (f"; lines {hs[:10]}" if hs else ""))

# ---------------------------------------------------------------- 9. the kit's own format check
r = subprocess.run([sys.executable, str(WS / "study" / "quiz.py"), "--check"], capture_output=True, text=True, encoding="utf-8", cwd=str(WS))
line = next((l for l in r.stdout.splitlines() if "I2_questions.md" in l), "")
check(line.strip().startswith("OK") and f"{len(SPEC)} questions" in line, f"study/quiz.py --check passes for I2 ({line.strip()})")
check(r.returncode == 0, f"study/quiz.py --check exits 0 for all files (exit {r.returncode}; {r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''})")

print(f"\n{n - fails}/{n} checks passed")
sys.exit(0 if fails == 0 else 1)
