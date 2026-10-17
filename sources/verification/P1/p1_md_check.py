"""P1: check the two study-kit Markdown files of 2026-10-18 (question file and short reading file).

1. study/questions/P1_questions.md loads with the kit's own parser and passes kit.lint_questions; the 21 ids of the
   build spec, in their sets and types; the kept Part L ids; FORMAT field rules (hints, 2-5 keys, 1-2 'for a 4',
   1-3 wrong answers, Hint 3 only on A items, one short question sentence); P1-A-04 uses max_completion_tokens;
   both interview items are verbatim (repo heading), carry the MIT notice, and their quoted repo paragraphs are
   exact substrings of the pinned repo file; at most 2 external items; no coach-seed S1 wording.
2. Every reread line links into the short reading file AND the full lesson and names a book page; each item's
   reread names the lesson step the build spec says teaches it.
3. Every relative link in both files resolves to a file, and every #anchor resolves (GitHub rule: lower-case,
   punctuation removed, each space -> '-'); also every link from any other workspace .md file INTO these files.
4. The reading file's shape (FORMAT §3): header, What this is / is not, the book box with the spec's pages, one
   numbered section per lesson step 1-12 in order, 'When not to count exactly', 'Check yourself'; 1,800-3,000
   words of prose (code blocks removed).
5. Book pages: every 'ChN p.x/y' cited exists (y = the chapter's page count); the cited pages hold the short
   phrases the paraphrases rely on (each < 15 words; checked in memory, never printed).
6. Copyright: no run of 15 consecutive words is shared with ANY page of the book (text compared in memory, never
   saved; a hit is reported by file and line only, never with its text).
7. Numbers: every decimal number, and every integer >= 10, in the two files matches a number printed by
   p1_measure.py, p1_strawberry.py, p1_kit_measure.py or the O2 report, or is on the DATED (provider fact, read
   2026-10-17) or DERIVED (arithmetic shown in the text) list below.
8. `uv run python study/quiz.py --check` passes for P1_questions.md.
Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P1/p1_md_check.py "C:/Yash/New-Work/Book RAG" \
        > sources/verification/P1/out_p1_md_check.txt
"""
import glob
import json
import re
import subprocess
import sys
from pathlib import Path

import pymupdf

ROOT = Path(sys.argv[1])
WS = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BOOK = ROOT / "RAG_Made_Simple_The_Complete_Visual_Guide"
QF = WS / "study" / "questions" / "P1_questions.md"
SHORT = WS / "study" / "reading" / "P1_llm_fundamentals.md"
FULL = WS / "concepts" / "P1_llm_fundamentals.md"
AIQ = ROOT / "upstream" / "AI-Engineer-Interview-Questions"
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
qtext_all = QF.read_text(encoding="utf-8")
short = SHORT.read_text(encoding="utf-8")
full = FULL.read_text(encoding="utf-8")
problems = kit.lint_questions(QF)
check(not problems, f"kit.lint_questions: {problems or 'no problems'}")
check(qtext_all.startswith("<!-- kit:questions concept=P1 version=1 -->"), "question file header line")
ids = [q["id"] for q in qs]
qd = {q["id"]: q for q in qs}
SPEC = {  # id: (set, taught-in steps from the build spec's table)
    "P1-PRE-01": ("pre", [1]), "P1-PRE-02": ("pre", [3]), "P1-PRE-03": ("pre", [7]),
    "P1-R-01": ("main", [1]), "P1-R-02": ("main", [6, 7]), "P1-R-03": ("main", [8]), "P1-R-04": ("main", [5]),
    "P1-R-05": ("main", [2, 3]), "P1-R-06": ("main", [7]),
    "P1-A-01": ("main", [3]), "P1-A-02": ("main", [10]), "P1-A-03": ("main", [8]), "P1-A-04": ("main", [7]),
    "P1-A-05": ("main", [10]), "P1-A-06": ("main", [4]), "P1-A-07": ("main", [11]),
    "P1-T-01": ("main", [3, 4, 5]), "P1-T-02": ("main", [8, 9, 10]), "P1-T-03": ("review", [7]),
    "P1-R-07": ("interview", [7]), "P1-R-08": ("interview", [7]),
}
check(sorted(ids) == sorted(SPEC) and len(ids) == 21, f"the 21 ids of the build spec, no more, no less ({len(ids)})")
check(len(set(ids)) == len(ids), "ids unique")
check(all(qd[i]["set"] == s for i, (s, _) in SPEC.items() if i in qd), "each id is in the spec's set (pre/main/review/interview)")
check(all(re.fullmatch(r"P1-(PRE|[RAT])-\d\d", i) for i in ids), "ids follow P1-<type>-<nn> / P1-PRE-<nn>")
check(all(q["id"].split("-")[1] == q["type"] or q["id"].startswith("P1-PRE") for q in qs), "id letter = type")
check([i for i in ids if "PRE" in i] == ["P1-PRE-01", "P1-PRE-02", "P1-PRE-03"] and ids[:3] == ["P1-PRE-01", "P1-PRE-02", "P1-PRE-03"],
      "the 3 set=pre items come first, in order")
by = {}
for q in qs:
    by.setdefault((q["set"], q["type"]), []).append(q["id"])
cnt = lambda s, t=None: sum(len(v) for (ss, tt), v in by.items() if ss == s and (t is None or tt == t))
print(f"     items: {len(qs)}; pre {cnt('pre')}; main {cnt('main')} (R {cnt('main', 'R')}, A {cnt('main', 'A')}, "
      f"T {cnt('main', 'T')}); review {cnt('review')}; interview {cnt('interview')}")
partL = full[full.index("## Part L"):full.index("## Part M")]
kept = [f"P1-R-0{k}" for k in range(1, 5)] + [f"P1-A-0{k}" for k in range(1, 5)] + ["P1-T-01"]
check(all(i in ids and qd[i]["set"] == "main" and re.search(rf"\*\*{i}\.?\*\*", partL) for i in kept),
      "the full lesson's Part L ids P1-R-01..04, P1-A-01..04, P1-T-01 are kept as set=main")
a04 = qd["P1-A-04"]["question"]
check("max_completion_tokens=12" in a04 and "max_tokens=" not in a04.replace("max_completion_tokens=", ""),
      "P1-A-04 is rewritten with max_completion_tokens (no max_tokens= in its code)")
check("finish_reason is not None" in a04 and "max_tokens=12" in partL, "P1-A-04 keeps the meaning of Part L's item (cap 12, the finish_reason assert)")
for q in qs:
    check(len(q["hints"]) >= 2 and 2 <= len(q["answer"]["keys"]) <= 5 and 1 <= len(q["answer"]["four"]) <= 2
          and 1 <= len(q["answer"]["wrong"]) <= 3, f"{q['id']}: 2+ hints, 2-5 keys, 1-2 'for a 4', 1-3 wrong answers")
    if len(q["hints"]) == 3:
        check(q["type"] == "A", f"{q['id']}: Hint 3 only on an A item")
    first = q["question"].splitlines()[0]
    if q["set"] != "interview":
        ends = len(re.findall(r"[.?!]\"?(?:\s|$)", first))
        check(ends == 1 and first.rstrip().endswith(("?", ".")) and len(first.split()) <= 45,
              f"{q['id']}: one short question sentence ({len(first.split())} words)")
check(sum(1 for q in qs if q["source"]) <= 2, f"at most 2 external items ({sum(1 for q in qs if q['source'])})")
INTERVIEW = {"P1-R-07": ("AIQ-08-Q14", "08-inference-and-production/questions.md", 14),
             "P1-R-08": ("AIQ-02-Q42", "02-llm-fundamentals/questions.md", 42)}
for qid, (src, rel, num) in INTERVIEW.items():
    q = qd[qid]
    repo = (AIQ / rel).read_text(encoding="utf-8")
    check(q["source"] == src and q["set"] == "interview" and q["type"] == "R", f"{qid}: set=interview, source={src}")
    check("ombharatiya/AI-Engineer-Interview-Questions @ e080df2" in q["question"] and f"`{rel}`" in q["question"]
          and "Copyright (c) 2026 Om, MIT License" in q["question"], f"{qid}: MIT notice with the verbatim question")
    verb = re.match(r'"(.+)"', q["question"].splitlines()[0]).group(1)
    check(f"### {num}. {verb}" in repo, f"{qid}: the quoted question is verbatim in the repo (heading of Q{num})")
    pre = q["answer"]["preamble"]
    quotes = [l[l.index('"') + 1:l.rindex('"')] for l in pre.splitlines() if re.match(r'^>\s*"', l)]
    check(len(quotes) >= 2 and all(x in repo for x in quotes) and "Copyright (c) 2026 Om, MIT License" in pre
          and pre.index("The repo's answer") < pre.index("Our check of that answer"),
          f"{qid}: the {len(quotes)} quoted repo paragraphs ({sum(len(x.split()) for x in quotes)} words) are verbatim, "
          f"with the MIT notice, before our check")
    check(bool(q["answer"]["model"]), f"{qid}: our own model answer follows the repo's answer")
print("     note: the two interview questions are verbatim and longer than one sentence; the one-sentence rule is not applied")
coach_src = (WS / "sources" / "verification" / "coach" / "coach_sources.py").read_text(encoding="utf-8")
SEED_WORDS = json.loads(re.search(r'\("concepts/P1_llm_fundamentals\.md", (\[[^\]]*\]), "S1"\)', coach_src).group(1))  # read, not copied
seen = {p.name: [w for w in SEED_WORDS if w in p.read_text(encoding="utf-8").lower()] for p in (QF, SHORT)}
check(not any(seen.values()), f"no coach-seed S1 wording ({len(SEED_WORDS)} words) in the question or reading file ({seen})")
check(all(w not in (qtext_all + short) for w in ("Does any T change the top token", "12,800 tokens")),
      "no coach-reserve P1 wording (top-token flashcard, the whole-PDF skip-retrieval item)")

# ---------------------------------------------------------------- 2. reread lines


def slug(t):
    t = re.sub(r"`", "", t).strip().lower()
    t = re.sub(r"[^\w\s-]", "", t)
    return t.replace(" ", "-")


def headings(path):
    text = Path(path).read_text(encoding="utf-8")
    out, seen_h, fence = [], {}, False
    for line in text.splitlines():
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


short_heads = [(t, a) for lvl, t, a in headings(SHORT) if lvl == 2]
step_anchor = {int(re.match(r"(\d+)\.", t).group(1)): a for t, a in short_heads if re.match(r"\d+\.", t)}
for q in qs:
    rr = q["answer"]["reread"]
    ok = ("../reading/P1_llm_fundamentals.md#" in rr and "../../concepts/P1_llm_fundamentals.md#" in rr
          and re.search(r"book (Ch\d+|App) p\.\d", rr))
    check(bool(ok), f"{q['id']}: reread links to the short AND the full file, plus a book page")
    steps = SPEC[q["id"]][1]
    linked = re.findall(r"\.\./reading/P1_llm_fundamentals\.md#([\w-]+)", rr)
    check(any(step_anchor.get(s) in linked for s in steps),
          f"{q['id']}: reread names a short section the spec says teaches it (steps {steps})")


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
        if not tp.exists():
            bad.append(f"missing file {href}")
        elif anc and tp.suffix == ".md" and anc not in anchors(tp):
            bad.append(f"missing anchor {href}")
    return links, bad


for name, path in (("question file", QF), ("reading file", SHORT)):
    links, bad = bad_links(path, Path(path).read_text(encoding="utf-8"))
    anc_links = [h for h in links if "#" in h and not h.startswith("http")]
    check(not bad, f"{name}: {len(links)} links resolve ({len(anc_links)} with #anchors)" + ("" if not bad else ": " + "; ".join(bad[:8])))
inbound, bad_in = 0, []
MINE = {SHORT.resolve(), QF.resolve()}
for md in WS.rglob("*.md"):
    if md.resolve() in MINE or "AI Eval" in md.parts or ".venv" in md.parts:
        continue
    t = md.read_text(encoding="utf-8", errors="ignore")
    for href in links_in(t):
        target, _, anc = href.partition("#")
        if not target or href.startswith("http"):
            continue
        tp = (md.parent / target).resolve()
        if tp in MINE:
            inbound += 1
            if anc and anc not in anchors(tp):
                bad_in.append(f"{md.relative_to(WS)} -> {href}")
check(not bad_in, f"{inbound} links from other workspace files into the two P1 kit files resolve" + (f": {bad_in}" if bad_in else ""))

# ---------------------------------------------------------------- 4. reading file shape and length


def words(text, strip_code=False):
    if strip_code:
        text = re.sub(r"```.*?```", " ", text, flags=re.S)
    return len(text.split())


print(f"     word count: reading file {words(short)} (prose only, code blocks removed: {words(short, True)}); "
      f"question file {words(qtext_all)}")
check(1800 <= words(short, True) <= 3000, f"reading file prose within 1,800-3,000 words ({words(short, True)})")
check(short.startswith("<!-- kit:reading concept=P1 depth=short version=1 -->"), "reading file header line")
check(all(h in short for h in ("**What this is:**", "**What this is not:**", "> **Read in the book:**", "## Check yourself")),
      "reading file has What this is / is not, the book box and Check yourself (FORMAT §3)")
box = re.search(r"> \*\*Read in the book:\*\*(.+)", short).group(1)
check(all(p in box for p in ("Ch1 p.12–13/14", "Ch2 p.9/11", "Ch4 p.5/15", "Ch22 p.8/19", "p.14–15/19")),
      "book box names Ch1 p.12-13/14, Ch2 p.9/11, Ch4 p.5/15, Ch22 p.8/19 and p.14-15/19")
STEP_WORDS = {1: ("tokenizer", "ids"), 2: ("bpe",), 3: ("characters per token", "4"), 4: ("right tokenizer", "traps"),
              5: ("embedder", "254"), 6: ("budget", "window"), 7: ("reasoning", "output cap"), 8: ("temperature",),
              9: ("provider",), 10: ("price", "output"), 11: ("time", "tokens per minute"), 12: ("decisions",)}
titles = [t for t, _ in short_heads]
numbered = [t for t in titles if re.match(r"\d+\.", t)]
check([int(t.split(".")[0]) for t in numbered] == list(range(1, 14)), f"sections ## 1. ... ## 13. in order ({len(numbered)})")
check(all(all(w in numbered[s - 1].lower() for w in ws) for s, ws in STEP_WORDS.items()),
      "sections 1-12 follow the lesson's step order (each title names its step)")
check(numbered[12].lower().endswith("when not to count exactly") and titles[-1] == "Check yourself",
      "section 13 is 'When not to count exactly', then 'Check yourself'")
check(short.count("**The setup.**") >= 10 and short.count("**What this means.**") >= 10 and short.count("**For your project:**") >= 10,
      f"house style beats: setup {short.count('**The setup.**')}, means {short.count('**What this means.**')}, "
      f"project {short.count('**For your project:**')}")
check("[../questions/P1_questions.md]" in short or "(../questions/P1_questions.md)" in short, "Check yourself links the question file")

# ---------------------------------------------------------------- 5. book pages and the phrases the paraphrases rely on
TOK = re.compile(r"[a-z0-9]+")


def toks(t):
    t = t.lower().replace("\u2019", "").replace("'", "").replace("\u2018", "")
    return TOK.findall(t)


docs = {}
for f in sorted(glob.glob(str(BOOK / "*.pdf"))):
    stem = Path(f).stem
    key = "App" if stem == "Appendix" else ("Ch" + stem.split()[-1] if stem.startswith("chapter") else stem)
    docs[key] = [pg.get_text() for pg in pymupdf.open(f)]
cites = set()
for text in (qtext_all, short):
    for m in re.finditer(r"\b(Ch\d+|App) p\.(\d+)(?:–(\d+))?/(\d+)", text):
        cites.add((m.group(1), int(m.group(2)), int(m.group(4))))
        if m.group(3):
            cites.add((m.group(1), int(m.group(3)), int(m.group(4))))
    for m in re.finditer(r"\b(Ch\d+|App) p\.(\d+)/(\d+)–p\.(\d+)/(\d+)", text):
        cites.add((m.group(1), int(m.group(4)), int(m.group(5))))
badc = [c for c in sorted(cites) if c[0] not in docs or len(docs[c[0]]) != c[2] or not 1 <= c[1] <= c[2]]
check(not badc, f"{len(cites)} distinct book pages cited; each exists with the right page count" + (f"; bad: {badc}" if badc else ""))
flat = lambda ch, p: " ".join(toks(docs[ch][p - 1]))
PHRASES = [  # (chapter, page, short phrase) each < 15 words; the claim it supports is in the reading file
    ("Ch1", 12, "overkill when"), ("Ch1", 12, "context window"),
    ("Ch1", 13, "only one llm call per query"), ("Ch1", 13, "embedding is cheap"),
    ("Ch2", 9, "charged per token"), ("Ch2", 9, "one time cost"),
    ("Ch4", 5, "without exceeding its context window"),
    ("Ch22", 8, "different random seeds"),
    ("Ch22", 14, "output tokens for the answer"), ("Ch22", 14, "time to first token"),
    ("Ch22", 15, "increases both latency and cost"),
    ("Ch12", 6, "tokeniz"),
]
miss = [f"{c} p.{p}" for c, p, ph in PHRASES if " ".join(toks(ph)) not in flat(c, p) and ph not in docs[c][p - 1].lower()]
check(not miss, f"{len(PHRASES)} short phrases found on the cited pages (checked in memory)" + (f"; missing on {miss}" if miss else ""))
temp_hits = sum(len(re.findall(r"temperature", "\n".join(pages), re.I)) for pages in docs.values())
check(temp_hits == 13, f"the book uses 'temperature' {temp_hits} times (the reading file says 13, all about climate)")

# ---------------------------------------------------------------- 6. 15-word overlap with the book (in memory only)
book_tokens = [toks(pg) for pages in docs.values() for pg in pages]
grams = {nn: set() for nn in range(6, 16)}
for tk in book_tokens:
    for nn in grams:
        for i in range(len(tk) - nn + 1):
            grams[nn].add(hash(tuple(tk[i:i + nn])))
print(f"     book: {len(book_tokens)} pages, {sum(map(len, book_tokens)):,} words (held in memory only)")
for name, path in (("question file", QF), ("reading file", SHORT)):
    text = Path(path).read_text(encoding="utf-8")
    tk_all, line_of = [], []
    for ln, line in enumerate(text.splitlines(), 1):
        t = toks(line)
        tk_all += t
        line_of += [ln] * len(t)
    hits, longest = [], 0
    for nn in range(15, 5, -1):
        found = [i for i in range(len(tk_all) - nn + 1) if hash(tuple(tk_all[i:i + nn])) in grams[nn]]
        if found:
            longest = max(longest, nn)
            if nn == 15:
                hits = sorted({line_of[i] for i in found})
            break
    check(not hits, f"{name}: no 15-word run shared with the book (longest shared run: {longest or '<6'} words)"
          + (f"; lines {hits[:10]}" if hits else ""))

# ---------------------------------------------------------------- 7. numbers are traceable
outs = {"p1_measure": (HERE / "out_p1_measure.txt").read_text(encoding="utf-8"),
        "p1_strawberry": (HERE / "out_p1_strawberry.txt").read_text(encoding="utf-8"),
        "p1_kit_measure": (HERE / "out_p1_kit_measure.txt").read_text(encoding="utf-8"),
        "O2 report": (WS / "progress" / "O2_smoke_test_2026-10-08.json").read_text(encoding="utf-8")}
NUM = re.compile(r"(?<![\w.,/])(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?:e-?\d+)?(?![\w/])")
pool = set()
for t in outs.values():                                   # loose on purpose: '157/180.5/217', 'prefix254'
    for m in re.finditer(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?(?:e-?\d+)?", t.replace("−", "-")):
        pool.add(m.group(0).replace(",", ""))
pool_f = []
for s in pool:
    try:
        pool_f.append(float(s))
    except ValueError:
        pass
DATED = {  # provider facts read 2026-10-17 (research phase_01 §1 [P1-n]; LLMOPS_FOUNDATION §6.2); they change
    "0.075": "Groq input $/1M [P1-1]", "0.30": "Groq output $/1M [P1-1]", "0.037": "Groq cached input $/1M [P1-1]",
    "0.10": "Haiku 5.5 input $/1M [P1-16]", "0.50": "Haiku 5.5 output $/1M [P1-16]",
    "131072": "gpt-oss-20b window on Groq [P1-1]", "65536": "gpt-oss-20b max output on Groq [P1-1]",
    "1024": "Groq default max_completion_tokens [P1-3]", "128": "Cohere embed-v4.0 128k (docs) [P1-17]",
    "1e-8": "Groq converts T = 0 to 1e-8 [P1-4]", "15": "Petrov et al. 2023: up to 15x more tokens [P1-12]",
    "30": "Claude newer tokenizers about 30% more tokens [P1-15]", "0.3": "Cohere chat default temperature (foundation §2.7)",
    "8000": "8K TPM, plan row UNVERIFIED (K7 assumption)", "200000": "200K TPD, plan row UNVERIFIED (foundation §6.3)",
    "10": "AIQ Q42 quote: 10x budget (marked UNVERIFIED)", "100": "100 calls / 100 queries (the item's own data)",
    "1000": "1,000 characters / 1,000 tokens (the item's own data)", "300": "300 tokens (the item's own data)",
    "2000": "2,000 characters (the item's own data)", "55": "55 calls (the item's own data)", "13": "13 uses of 'temperature' (S-src)",
    "40": "40% error rule (lesson Part K)", "1000000": "per 1M tokens",
}
DERIVED = {  # arithmetic shown next to each in the text
    "362": "2000 / 5.52", "314": "2000 / 6.37", "434": "2000 / 4.61", "500": "2000 / 4", "181": "1000 / 5.52",
    "100000": "100 x 1000", "30000": "100 x 300", "130000": "100,000 + 30,000 (wrong answer)",
    "73.2": "976 x 0.075", "153.6": "512 x 0.30", "226.8": "73.2 + 153.6", "0.0002268": "226.8 / 1e6",
    "22680": "100 x 226.8 (wrong answer)", "2.718": "e^1", "2.117": "e^0.75", "1.284": "e^0.25", "0.607": "e^-0.5",
    "6.726": "sum of the four", "0.75": "1.5 / 2", "0.266": "0.532 / 2 (wrong answer)", "5.8": "23 / 4",
    "68": "67.7% rounded", "19": "23 - 4 (P1_FACTS §2)", "150": "rough range 150-220 for 157-217", "220": "rough range",
    "86": "842 / 976 (also K8)",
}
unmatched = {}
for name, path in (("question file", QF), ("reading file", SHORT)):
    text = Path(path).read_text(encoding="utf-8").replace("−", "-")
    text = re.sub(r"\]\([^)]*\)", "]", text)                                          # link targets
    text = re.sub(r"\b(Ch\d+|App) p\.\d+(?:–\d+)?/\d+(?:–p\.\d+/\d+)?", " ", text)     # book pages
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b|\b20(?:16|23|25|26)\b", " ", text)           # dates, years
    text = re.sub(r"\b[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+\b|§[\d.]+|\b[SKQEDO]\d+\b|#\d+|e080df2|cell \d+|question \d+", " ", text)
    text = re.sub(r"\b(gpt-oss-\d+b|gpt-4o-mini|gpt-3\.5-turbo|embed-v4\.0|cl100k|o200k|[Hh]aiku 5\.5|Claude 5\.5|P\d|M4|C5|D-\d+)\b", " ", text)
    for m in NUM.finditer(text):
        s = m.group(0).replace(",", "")
        x = float(s)
        if "." not in s and "e" not in s and x < 10:
            continue
        if s in DATED or s in DERIVED:
            continue
        d = len(s.split(".")[1]) if "." in s else 0
        ok = s in pool or any(abs(y - x) <= 0.5 * 10 ** -d + 1e-12 for y in pool_f) if d else s in pool
        if not ok:
            unmatched.setdefault(m.group(0), set()).add(name)
check(not unmatched, "every decimal and every integer >= 10 matches a printed value (p1_measure, p1_strawberry, "
      "p1_kit_measure, O2 report) or the DATED / DERIVED list" + (f"; unmatched: {unmatched}" if unmatched else ""))
KEY = ["5.57", "4.61", "6.37", "5.52", "0.98", "3.39", "1.000000", "201088", "1091", "976", "842", "107", "1559",
       "1.19%", "0.000227", "0.0227", "67.7%", "0.0354", "72.4%", "155,900", "19.5", "85,745", "10.7", "0.532", "0.404"]
miss_out = [k for k in KEY if not any(k in t or k.replace(",", "") in t for t in outs.values())]
check(not miss_out, f"{len(KEY)} key numbers are printed by the measurement scripts" + (f"; missing {miss_out}" if miss_out else ""))
miss_md = [k for k in KEY if not any(k in t or (k.isdigit() and f"{int(k):,}" in t) for t in (qtext_all, short))]
check(not miss_md, "each key number is quoted in the question or reading file" + (f"; not quoted: {miss_md}" if miss_md else ""))

# ---------------------------------------------------------------- 8. the kit's own format check
r = subprocess.run([sys.executable, str(WS / "study" / "quiz.py"), "--check"], capture_output=True, text=True,
                   encoding="utf-8", cwd=str(WS))
line = next((l for l in r.stdout.splitlines() if "P1_questions.md" in l), "")
print("     quiz.py --check: " + " | ".join(l.strip() for l in r.stdout.splitlines() if l.strip()))
check(r.returncode == 0 and line.startswith("OK") and "21 questions" in line, f"study/quiz.py --check passes for P1 ({line.strip()})")

print(f"\n{n} checks")
print("ALL PASS" if fails == 0 else f"{fails} FAIL(S)")
