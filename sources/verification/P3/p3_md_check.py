"""P3: check the three Markdown deliverables of 2026-10-17 and the lab notebook's text.

1. study/questions/P3_questions.md loads with the kit's own parser and passes kit.lint_questions; item counts by set
   and type; the kept ids; every reread line links into BOTH the short and the full file and names a book page;
   one short question sentence (interview items are verbatim and exempt); the interview item is verbatim with its notice.
2. The full lesson's Part A ids = the set=pre ids, its Part L ids = the main + review + interview ids, same wording.
3. Every relative link resolves to a file, and every #anchor resolves (GitHub rule: lower-case, punctuation removed,
   each space -> '-'). Also every link from any other workspace .md file INTO the P3 files.
4. Strings other checkers rely on are still in the full lesson (R1 links, coach_sources.py, r1_sources.py), and the
   lab's references (lesson D.3, H.1 task numbers) still match the lesson.
5. Word counts; the short file's shape (FORMAT §3); house-style beats in the full lesson.
6. Copyright: no run of 15 consecutive words is shared with ANY page of the book (text compared in memory, never
   saved; a hit is reported by file and line only, never with its text).
7. The short file's single 'Try it' snippet runs and prints what its comments say.
8. Every number with 3 or more decimals in the three files matches (at its own precision) a number printed by
   p3_measure.py, p3_kit_measure.py or R1's r1_measure.py, or is on the DERIVED list below (arithmetic shown in the text).
Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P3/p3_md_check.py "C:/Yash/New-Work/Book RAG" \
        > sources/verification/P3/out_p3_md_check.txt
"""
import contextlib
import glob
import io
import json
import re
import sys
from pathlib import Path

import pymupdf

ROOT = Path(sys.argv[1])
WS = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BOOK = ROOT / "RAG_Made_Simple_The_Complete_Visual_Guide"
QF = WS / "study" / "questions" / "P3_questions.md"
SHORT = WS / "study" / "reading" / "P3_bm25.md"
FULL = WS / "concepts" / "P3_bm25.md"
LAB = WS / "labs" / "P3_bm25_lab.ipynb"
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
problems = kit.lint_questions(QF)
check(not problems, f"kit.lint_questions: {problems or 'no problems'}")
check(QF.read_text(encoding="utf-8").startswith("<!-- kit:questions concept=P3 version=1 -->"), "question file header line")
by = {}
for q in qs:
    by.setdefault((q["set"], q["type"]), []).append(q["id"])
cnt = lambda s, t=None: sum(len(v) for (ss, tt), v in by.items() if ss == s and (t is None or tt == t))
print(f"     items: {len(qs)}; pre {cnt('pre')}; main {cnt('main')} (R {cnt('main', 'R')}, A {cnt('main', 'A')}, "
      f"T {cnt('main', 'T')}); review {cnt('review')}; interview {cnt('interview')}")
ids = [q["id"] for q in qs]
check(15 <= len(qs) <= 18, f"15-18 items ({len(qs)})")
check(3 <= cnt("pre") <= 5 and [i for i in ids if "PRE" in i] == [f"P3-PRE-0{k}" for k in range(1, cnt("pre") + 1)],
      "3-5 set=pre items, P3-PRE-01 ... in order")
check(cnt("main", "R") >= 4 and cnt("main", "A") >= 4 and cnt("main", "T") >= 2, "set=main has >= 4 R, >= 4 A, >= 2 T")
check(1 <= cnt("interview") <= 2, "1-2 set=interview items")
check(len(set(ids)) == len(ids), "ids unique")
check(all(re.fullmatch(r"P3-(PRE|[RAT])-\d\d", i) for i in ids), "ids follow P3-<type>-<nn> / P3-PRE-<nn>")
check(all(q["id"].split("-")[1] == q["type"] or q["id"].startswith("P3-PRE") for q in qs), "id letter = type")
kept = [f"P3-R-0{k}" for k in range(1, 5)] + [f"P3-A-0{k}" for k in range(1, 5)] + ["P3-T-01"]
check(all(i in ids for i in kept) and all(next(q for q in qs if q["id"] == i)["set"] == "main" for i in kept),
      "the 2026-10-08 Part L ids P3-R-01..04, P3-A-01..04, P3-T-01 are kept as set=main")
qd = {q["id"]: q for q in qs}
check("P3-T-02" in qd and "getUserId" in qd["P3-T-02"]["question"] and qd["P3-T-02"]["set"] == "main",
      "P3-T-02 is the code-identifier scenario (getUserId / get_user_id), written for the kit")
coach_src = (WS / "sources" / "verification" / "coach" / "coach_sources.py").read_text(encoding="utf-8")
SEED_WORDS = json.loads(re.search(r'\("concepts/P3_bm25\.md", (\[[^\]]*\]), "S2"\)', coach_src).group(1))  # read, not copied
seen = {p.name + "/" + p.parent.name: [w for w in SEED_WORDS if w in p.read_text(encoding="utf-8").lower()]
        for p in (QF, SHORT, FULL)}
check(not any(seen.values()), f"no coach-seed S2 wording in the question, short or full file ({seen})")
check(any(q["type"] == "T" and q["set"] == "main" and "BM25 alone" in q["question"] for q in qs),
      "a main T item asks when NOT to use BM25 alone")
check("P3-A-01" in qd and "1.243333" in qd["P3-A-01"]["answer"]["model"], "P3-A-01 model answer = 1.243333 (S4)")
for q in qs:
    rr = q["answer"]["reread"]
    ok = ("../reading/P3_bm25.md#" in rr and "../../concepts/P3_bm25.md#" in rr and re.search(r"book (Ch\d+|App) p\.\d", rr))
    check(bool(ok), f"{q['id']}: reread links to short AND full file, plus a book page")
    check(len(q["hints"]) >= 2 and 2 <= len(q["answer"]["keys"]) <= 5 and 1 <= len(q["answer"]["four"]) <= 2
          and 1 <= len(q["answer"]["wrong"]) <= 3, f"{q['id']}: 2+ hints, 2-5 keys, 1-2 'for a 4', 1-3 wrong answers")
    if len(q["hints"]) == 3:
        check(q["type"] == "A", f"{q['id']}: Hint 3 only on an A item")
    qtext = q["question"].splitlines()[0]
    if q["set"] != "interview":
        ends = len(re.findall(r"[.?!]\"?(?:\s|$)", qtext))
        check(ends == 1 and qtext.rstrip().rstrip('"').endswith(("?", ".")) and len(qtext.split()) <= 45,
              f"{q['id']}: one short question sentence ({len(qtext.split())} words)")
aiq = (ROOT / "upstream" / "AI-Engineer-Interview-Questions" / "04-rag-and-retrieval" / "questions.md").read_text(encoding="utf-8")
for q in qs:
    if q["set"] == "interview":
        check("ombharatiya/AI-Engineer-Interview-Questions @ e080df2" in q["question"]
              and "Copyright (c) 2026 Om, MIT License" in q["question"], f"{q['id']}: MIT notice with the verbatim question")
        verb = re.search(r'"(.+?)"', q["question"]).group(1)
        check(f"### 12. {verb}" in aiq, f"{q['id']}: the quoted question is verbatim in the repo (heading of Q12)")
        quotes = re.findall(r'^>\s*"(\*\*.+?)"\s*$', q["answer"]["preamble"], re.M)
        check(len(quotes) == 2 and all(x in aiq for x in quotes) and "MIT License" in q["answer"]["preamble"],
              f"{q['id']}: the {len(quotes)} quoted repo paragraphs ({sum(len(x.split()) for x in quotes)} words) are verbatim, "
              f"with the MIT notice")
        print(f"     note: the interview question is verbatim and has two sentences; the one-sentence rule is not applied to it")

# ---------------------------------------------------------------- 2. Part A / Part L of the full lesson
full = FULL.read_text(encoding="utf-8")
partA = full[full.index("## Part A"):full.index("## Read in the book")]
partL = full[full.index("## Part L"):full.index("## Part M")]
idsA = re.findall(r"\*\*(P3-PRE-\d\d)\.\*\*", partA)
idsL = re.findall(r"^\| (P3-[RAT]-\d\d) \|", partL, re.M)
check(idsA == [q["id"] for q in qs if q["set"] == "pre"], f"Part A ids = set=pre ids ({idsA})")
check(sorted(idsL) == sorted(q["id"] for q in qs if q["set"] in ("main", "review", "interview")),
      f"Part L ids = main + review + interview ids ({len(idsL)})")
qmap = {q["id"]: q["question"].splitlines()[0].strip() for q in qs}
for i in idsA:
    m = re.search(rf"\*\*{i}\.\*\* (.+)", partA)
    check(m and m.group(1).strip() == qmap[i], f"Part A {i}: same wording as the question file")
for i in idsL:
    m = re.search(rf"^\| {i} \| (.+?) \| .+\|$", partL, re.M)
    check(m and m.group(1).strip() == qmap[i], f"Part L {i}: same wording as the question file")
check(not re.search(r"P3-A[1-5]\b", full[:full.index("## Verification log")]),
      "no old Part A ids (P3-A1 ... P3-A5) left in the full lesson (the Verification log records the mapping)")


# ---------------------------------------------------------------- 3. links and anchors
def slug(t):
    t = re.sub(r"`", "", t).strip().lower()
    t = re.sub(r"[^\w\s-]", "", t)              # keeps letters/digits/underscore (unicode) and hyphens
    return t.replace(" ", "-")


def anchors(path):
    text = Path(path).read_text(encoding="utf-8")
    out, seen, fence = set(), {}, False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = re.match(r"^#{1,6}\s+(.*?)\s*$", line)
        if m:
            s = slug(re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", m.group(1)))
            k = seen.get(s, -1) + 1
            seen[s] = k
            out.add(s if k == 0 else f"{s}-{k}")
    out |= set(re.findall(r'<a id="([^"]+)"', text))
    return out


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


nb = json.load(open(LAB, encoding="utf-8"))
nb_md = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "markdown")
for name, path, text in (("question file", QF, None), ("short file", SHORT, None), ("full file", FULL, None),
                         ("lab notebook", LAB, nb_md)):
    text = text if text is not None else Path(path).read_text(encoding="utf-8")
    links, bad = bad_links(path, text)
    check(not bad, f"{name}: {len(links)} links resolve (files and anchors){'' if not bad else ': ' + '; '.join(bad[:8])}")
inbound, bad_in = 0, []
P3_FILES = {FULL.resolve(), SHORT.resolve(), QF.resolve()}
for md in WS.rglob("*.md"):
    if md.resolve() in P3_FILES or "AI Eval" in md.parts or ".venv" in md.parts:
        continue
    t = md.read_text(encoding="utf-8", errors="ignore")
    for href in links_in(t):
        target, _, anc = href.partition("#")
        if not target or href.startswith("http"):
            continue
        tp = (md.parent / target).resolve()
        if tp in P3_FILES:
            inbound += 1
            if anc and anc not in anchors(tp):
                bad_in.append(f"{md.relative_to(WS)} -> {href}")
check(not bad_in, f"{inbound} links from other workspace files into the P3 files resolve" + (f": {bad_in}" if bad_in else ""))

# ---------------------------------------------------------------- 4. strings other checkers and the lab rely on
for s, who in (("### D.3 BM25 exactly as `rank_bm25` 0.2.2 computes it", "R1 full link #d3-bm25-exactly-as-rank_bm25-022-computes-it"),
               ("### H.2 Repo reading guide: `fusion_retrieval.ipynb` cell 17", "R1 full link, r1_sources.py"),
               ("the fused ranking silently becomes vector-only", "r1_sources.py (kept, now with the alignment caveat)"),
               ("avgdl over all chunks", "coach_sources.py S2 P3 D.1"),
               ("floor      = epsilon × mean of idf over ALL terms", "coach_sources.py S2 P3 D.3 floor"),
               ("### D.4 Saturation (k1) and length normalisation (b)", "coach_sources.py S2 P3 D.4"),
               ("At dl = avgdl and f = 1, the tf part is exactly 1 for **any** k1", "coach_sources.py P3 reserve"),
               ("**J2. Every score is zero on a tiny test corpus.**", "coach_sources.py P3 reserve J2")):
    check(s in full, f"full lesson keeps {s[:60]!r} ({who})")
h2 = full[full.index("### H.2"):full.index("### H.3")]
check("five chunks nearest to the **empty string**" in h2 and "[89, 50, 48, 49, 81]" in h2,
      "H.2 answer 4 corrected: the repo's fusion returns the chunks nearest to the empty string (R1 S11)")
d3 = full[full.index("### D.3"):full.index("### D.4")]
check("ln( (N − n + 0.5) / (n + 0.5) )" in d3 and "strictly negative only" in d3 and "An unknown term adds 0" in d3
      and "twice" in d3, "lab Tasks 2-3 cite 'lesson D.3': D.3 still has the IDF, the floor rule, unknown and repeated terms")
labtasks = re.findall(r"^## Task (\d): (.+)$", nb_md, re.M)
h1 = full[full.index("### H.1"):full.index("### H.2")]
rows = re.findall(r"^\| (\d) \| (.+?) \|", h1, re.M)
check([t for t, _ in labtasks] == [r for r, _ in rows] == [str(k) for k in range(1, 8)],
      f"H.1 lists the lab's 7 tasks in the lab's order ({len(labtasks)} lab tasks, {len(rows)} rows)")
pairs = {"1": ("tokenizer", "tok_norm"), "2": ("by hand", "by eye"), "3": ("numpy", "numpy"), "4": ("saturation", "saturation"),
         "5": ("cr-08", "cr-08"), "6": ("climate pdf", "climate pdf"), "7": ("debugging", "debugging")}
lt, rw = dict(labtasks), dict(rows)
check(all(a in lt[k].lower() and b in rw[k].lower() for k, (a, b) in pairs.items()),
      "each H.1 row describes the same task as the lab heading")
check("Part H.1" in nb_md and "D.3" in nb_md, "the lab still points at the lesson's H.1 and D.3")

# ---------------------------------------------------------------- 5. word counts, shape, beats
def words(p, strip_code=False):
    t = Path(p).read_text(encoding="utf-8")
    if strip_code:
        t = re.sub(r"```.*?```", " ", t, flags=re.S)
    return len(t.split())


print(f"     word count: short {words(SHORT)} (prose only, code blocks removed: {words(SHORT, True)}); "
      f"full {words(FULL)} (prose only: {words(FULL, True)}); question file {words(QF)}")
check(1800 <= words(SHORT, True) <= 3000, f"short file prose within 1,800-3,000 words ({words(SHORT, True)})")
short = SHORT.read_text(encoding="utf-8")
check(short.startswith("<!-- kit:reading concept=P3 depth=short version=1 -->"), "short file header line")
check(all(h in short for h in ("**What this is:**", "**What this is not:**", "> **Read in the book:**", "## Check yourself")),
      "short file has What this is / is not, the book box and Check yourself (FORMAT §3)")
check(re.search(r"^## \d+\. When not to use", short, re.M) is not None, "short file has a 'When not to use' section")
book_box = re.search(r"> \*\*Read in the book:\*\*(.+)", short).group(1)
check(all(p in book_box for p in ("Ch12 p.1–2/14", "p.5–6/14", "App p.14/23", "p.17/23", "p.18/23", "p.22/23", "Ch13 p.5/13")),
      "short file's book box names Ch12, the four glossary pages and Ch13 p.5/13")
teach = full[full.index("## Part B"):full.index("## Part L")]
beats = {b: teach.count(b) for b in ("**The setup.**", "**The result**", "**What this means.**", "**For your project:**")}
check(min(beats.values()) >= 10, f"house style: four beats in Parts B-K {beats}")
check(full.count("🧭 Coach:") - 1 <= 11, f"coach notes: {full.count('🧭 Coach:') - 1} (R1 has 11)")
check("91 windows" in full and "97 chunks" in full and "91 windows" in short and "97 chunks" in short,
      "the full lesson and the short file both name the two chunk sets")

# ---------------------------------------------------------------- 6. 15-word overlap with the book (in memory only)
TOK = re.compile(r"[a-z0-9]+")


def toks(t):
    t = t.lower().replace("\u2019", "").replace("'", "").replace("\u2018", "")
    return TOK.findall(t)


book_tokens = []
for f in sorted(glob.glob(str(BOOK / "*.pdf"))):
    for pg in pymupdf.open(f):
        book_tokens.append(toks(pg.get_text()))
grams = {nn: set() for nn in range(6, 16)}
for tk in book_tokens:
    for nn in grams:
        for i in range(len(tk) - nn + 1):
            grams[nn].add(hash(tuple(tk[i:i + nn])))
print(f"     book: {len(book_tokens)} pages, {sum(map(len, book_tokens)):,} words (held in memory only)")
for name, path, text in (("question file", QF, None), ("short file", SHORT, None), ("full file", FULL, None),
                         ("lab notebook text", LAB, nb_md)):
    text = text if text is not None else Path(path).read_text(encoding="utf-8")
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

# ---------------------------------------------------------------- 7. the 'Try it' snippet
blocks = re.findall(r"```python\n(.*?)```", short, flags=re.S)
check(len(blocks) == 1 and len(blocks[0].strip().splitlines()) <= 10, f"short file: one python snippet of <= 10 lines "
      f"({len(blocks)} block(s), {len(blocks[0].strip().splitlines()) if blocks else 0} lines)")
if blocks:
    exp = [re.search(r"#\s*(.+?)\s*$", l).group(1) for l in blocks[0].splitlines() if l.lstrip().startswith("print(")]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(blocks[0], {})
    got = buf.getvalue().strip().splitlines()
    check(got == exp, f"short file: the snippet prints {got} (its comments say {exp})")

# ---------------------------------------------------------------- 8. numbers: every value with >= 3 decimals is measured or DERIVED
outs = {"p3_measure": (HERE / "out_p3_measure.txt").read_text(encoding="utf-8"),
        "p3_kit_measure": (HERE / "out_p3_kit_measure.txt").read_text(encoding="utf-8"),
        "r1_measure": (HERE.parent / "R1" / "out_r1_measure.txt").read_text(encoding="utf-8")}
NUM = re.compile(r"(?<![\w.])-?\d+\.\d+(?:e-?\d+)?")
pool = {}
for k, t in outs.items():
    for m in NUM.finditer(t):
        pool.setdefault(m.group(0), k)
pool_f = [(float(s), k) for s, k in pool.items()]
# Values computed by hand in the text (the arithmetic is shown next to each), not printed by a script.
DERIVED = {      # each one appears next to its arithmetic in the text; none is printed by a script
    "1.075": "F step 3: 0.25 + 0.75 x 1.1", "3.6125": "F step 4: 2 + 1.6125", "1.8375": "F step 6: K for d2",
    "2.6125": "P3-A-01: 1 + K for eu in d0", "1.9375": "P3-A-05: 1 + 0.9375",
    "2.625": "P3-A-03: K at b = 0.75, dl = 2 avgdl", "3.625": "P3-A-03: 1 + 2.625",
    "2.0625": "P3-A-03: K at b = 0.375, dl = 2 avgdl", "3.0625": "P3-A-03: 1 + 2.0625", "1.375": "P3-A-03: 1 - 0.375 + 0.75",
    "1.792": "P3-A-01 wrong answer: ln 6, the textbook idf",
}
unmatched = {}
for name, path in (("question file", QF), ("short file", SHORT), ("full file", FULL)):
    for m in NUM.finditer(Path(path).read_text(encoding="utf-8").replace("−", "-")):
        s = m.group(0)
        d = len(s.split(".")[1].split("e")[0])
        if d < 3 or s in DERIVED:
            continue
        x = float(s)
        ok = any(abs(y - x) <= 0.5 * 10 ** -d + 1e-12 or abs(abs(y) - abs(x)) <= 0.5 * 10 ** -d + 1e-12 for y, _ in pool_f)
        if not ok:
            unmatched.setdefault(s, set()).add(name)
check(not unmatched, f"every number with >= 3 decimals in the 3 files matches a printed value "
      f"(p3_measure, p3_kit_measure, r1_measure) or the DERIVED list" + (f"; unmatched: {unmatched}" if unmatched else ""))
KEY = ["0.813546", "1.938496", "1.243333", "0.758434", "0.765846", "0.587787", "1.299283", "0.272442", "3.577948",
       "0.838237", "-1.945910", "4.099885", "5.062271", "4.880348", "1.671968", "3.649768", "1.412504",
       "2.8904", "6.5917", "1.8871", "1.1756", "0.428571", "0.007752", "2.6276", "2.1134", "1.8392", "3.6807",
       "5.7608", "-0.080472", "[90, 89, 88, 87, 86]", "184 (23.0%)", "1.1e-13", "2.173913", "2.496256", "0.829243",
       "0.495899", "1.847298"]
miss = [k for k in KEY if not any(k in t for t in outs.values())]
check(not miss, f"{len(KEY)} key numbers are printed by the measurement scripts" + (f"; missing {miss}" if miss else ""))
miss_md = [k for k in KEY if not any(k.replace("-", "−") in Path(p).read_text(encoding="utf-8") or k in Path(p).read_text(encoding="utf-8")
                                     for p in (QF, SHORT, FULL))]
check(not miss_md, f"each key number is quoted in at least one of the three files" + (f"; not quoted: {miss_md}" if miss_md else ""))

print(f"\n{n} checks")
print("ALL PASS" if fails == 0 else f"{fails} FAIL(S)")
