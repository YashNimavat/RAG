"""R1: check the three Markdown deliverables and the lab notebook's text.

1. study/questions/R1_questions.md loads with the kit's own parser and passes kit.lint_questions; item counts by set
   and type; every reread line links into BOTH the short and the full file and names a book page.
2. The full lesson's Part A ids = the set=pre ids, its Part L ids = the main + interview ids, with identical wording.
3. Every relative link resolves to a file, and every #anchor resolves (GitHub rule: lower-case, punctuation removed,
   each space -> '-'; explicit <a id> anchors count too).
4. Word counts of the short and full files.
5. Copyright: no run of 15 consecutive words is shared with ANY page of the book (text compared in memory, never
   saved; a hit is reported by file and line only, never with its text).
6. The short file's single 'Try it' snippet runs and prints what its comment says.
7. Key numbers quoted in the files appear in out_r1_measure.txt.
Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/R1/r1_md_check.py "C:/Yash/New-Work/Book RAG" \
        > sources/verification/R1/out_r1_md_check.txt
"""
import contextlib
import glob
import io
import json
import os
import re
import sys
from pathlib import Path

import pymupdf

ROOT = Path(sys.argv[1])
WS = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BOOK = ROOT / "RAG_Made_Simple_The_Complete_Visual_Guide"
QF = WS / "study" / "questions" / "R1_questions.md"
SHORT = WS / "study" / "reading" / "R1_hybrid_fusion.md"
FULL = WS / "concepts" / "R1_hybrid_fusion.md"
LAB = WS / "labs" / "R1_hybrid_fusion_lab.ipynb"
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
check(QF.read_text(encoding="utf-8").startswith("<!-- kit:questions concept=R1 version=1 -->"), "question file header line")
by = {}
for q in qs:
    by.setdefault((q["set"], q["type"]), []).append(q["id"])
cnt = lambda s, t=None: sum(len(v) for (ss, tt), v in by.items() if ss == s and (t is None or tt == t))
print(f"     items: {len(qs)}; pre {cnt('pre')}; main {cnt('main')} (R {cnt('main', 'R')}, A {cnt('main', 'A')}, "
      f"T {cnt('main', 'T')}); interview {cnt('interview')}")
check(14 <= len(qs) <= 18, f"14-18 items ({len(qs)})")
check(cnt("pre") == 3, "3 set=pre items")
check(10 <= cnt("main") <= 12 and cnt("main", "R") >= 4 and cnt("main", "A") >= 4 and cnt("main", "T") >= 2,
      "10-12 set=main items with >= 4 R, >= 4 A, >= 2 T")
check(1 <= cnt("interview") <= 2, "1-2 set=interview items")
check(len({q["id"] for q in qs}) == len(qs), "ids unique")
check(all(re.fullmatch(r"R1-(PRE|[RAT])-\d\d", q["id"]) for q in qs), "ids follow <concept>-<type>-<nn> / R1-PRE-<nn>")
check(all((q["id"].split("-")[1] == q["type"]) or q["id"].startswith("R1-PRE") for q in qs), "id letter = type")
rev = next((q for q in qs if "[A, B, C]" in q["question"] and "[C, A, D]" in q["question"]), None)
check(rev is not None and "A, C, B, D" in rev["answer"]["model"], "the R1 review item (O1-Q09 lists -> A, C, B, D) is present")
check(any(q["type"] == "T" and q["set"] == "main" and re.search(r"would you add|when not", q["question"] + q["title"], re.I)
          for q in qs), "a main T item asks when NOT to use hybrid")
for q in qs:
    rr = q["answer"]["reread"]
    ok = ("../reading/R1_hybrid_fusion.md#" in rr and "../../concepts/R1_hybrid_fusion.md#" in rr
          and re.search(r"book (Ch\d+|App) p\.\d", rr))
    check(bool(ok), f"{q['id']}: reread links to short AND full file, plus a book page")
    check(len(q["hints"]) >= 2 and 2 <= len(q["answer"]["keys"]) <= 5 and 1 <= len(q["answer"]["four"]) <= 2
          and 1 <= len(q["answer"]["wrong"]) <= 3, f"{q['id']}: 2+ hints, 2-5 keys, 1-2 'for a 4', 1-3 wrong answers")
    if len(q["hints"]) == 3:
        check(q["type"] == "A", f"{q['id']}: Hint 3 only on an A item")
    qtext = q["question"].splitlines()[0]
    ends = len(re.findall(r"[.?!]\"?(?:\s|$)", qtext))
    check(ends == 1 and qtext.rstrip().rstrip('"').endswith(("?", ".")) and len(qtext.split()) <= 45,
          f"{q['id']}: one short question sentence ({len(qtext.split())} words)")
for q in qs:
    if q["set"] == "interview":
        check("ombharatiya/AI-Engineer-Interview-Questions @ e080df2" in q["question"]
              and "Copyright (c) 2026 Om, MIT License" in q["question"], f"{q['id']}: MIT notice with the verbatim question")
aiq = (ROOT / "upstream" / "AI-Engineer-Interview-Questions" / "04-rag-and-retrieval" / "questions.md").read_text(encoding="utf-8")
for q in qs:
    if q["set"] == "interview":
        verb = re.search(r'"(.+?)"', q["question"]).group(1)
        check(verb in aiq, f"{q['id']}: the quoted question is verbatim in the repo")
        ex = re.search(r'>\s*"(\*\*.+?)"\s*$', q["answer"]["preamble"], re.S | re.M)
        if ex:
            check(ex.group(1) in aiq and "MIT License" in q["answer"]["preamble"],
                  f"{q['id']}: the quoted repo answer ({len(ex.group(1).split())} words) is verbatim, with the MIT notice")

# ---------------------------------------------------------------- 2. Part A / Part L of the full lesson
full = FULL.read_text(encoding="utf-8")
partA = full[full.index("## Part A"):full.index("## Read in the book")]
partL = full[full.index("## Part L"):full.index("## Part M")]
idsA = re.findall(r"\*\*(R1-PRE-\d\d)\.\*\*", partA)
idsL = re.findall(r"^\| (R1-[RAT]-\d\d) \|", partL, re.M)
check(idsA == [q["id"] for q in qs if q["set"] == "pre"], f"Part A ids = set=pre ids ({idsA})")
check(sorted(idsL) == sorted(q["id"] for q in qs if q["set"] in ("main", "interview")),
      f"Part L ids = main + interview ids ({len(idsL)})")
qmap = {q["id"]: q["question"].splitlines()[0].strip() for q in qs}
for i in idsA:
    m = re.search(rf"\*\*{i}\.\*\* (.+)", partA)
    check(m and m.group(1).strip() == qmap[i], f"Part A {i}: same wording as the question file")
for i in idsL:
    m = re.search(rf"^\| {i} \| (.+?) \| .+\|$", partL, re.M)
    check(m and m.group(1).strip() == qmap[i], f"Part L {i}: same wording as the question file")


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


nb_md = "\n".join("".join(c["source"]) for c in json.load(open(LAB, encoding="utf-8"))["cells"] if c["cell_type"] == "markdown")
for name, path, text in (("question file", QF, None), ("short file", SHORT, None), ("full file", FULL, None),
                         ("lab notebook", LAB, nb_md)):
    text = text if text is not None else Path(path).read_text(encoding="utf-8")
    bad = []
    links = links_in(text)
    for href in links:
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        target, _, anc = href.partition("#")
        tp = (Path(path).parent / target).resolve() if target else Path(path)
        if not tp.exists():
            bad.append(f"missing file {href}")
            continue
        if anc and tp.suffix == ".md" and anc not in anchors(tp):
            bad.append(f"missing anchor {href}")
    check(not bad, f"{name}: {len(links)} links resolve (files and anchors){'' if not bad else ': ' + '; '.join(bad[:8])}")


# ---------------------------------------------------------------- 4. word counts
def words(p, strip_code=False):
    t = Path(p).read_text(encoding="utf-8")
    if strip_code:
        t = re.sub(r"```.*?```", " ", t, flags=re.S)
    return len(t.split())


print(f"     word count: short {words(SHORT)} (prose only, code blocks removed: {words(SHORT, True)}); "
      f"full {words(FULL)} (prose only: {words(FULL, True)}); question file {words(QF)}")
check(1800 <= words(SHORT) <= 3000, f"short file within 1,800-3,000 words ({words(SHORT)})")
short = SHORT.read_text(encoding="utf-8")
check(short.startswith("<!-- kit:reading concept=R1 depth=short version=1 -->"), "short file header line")
check(all(h in short for h in ("**What this is:**", "**What this is not:**", "> **Read in the book:**", "## Check yourself")),
      "short file has What this is / is not, the book box and Check yourself (FORMAT §3)")
check(re.search(r"^## \d+\. When not to use", short, re.M) is not None, "short file has a 'When not to use' section")

# ---------------------------------------------------------------- 5. 15-word overlap with the book (in memory only)
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
    lines = text.splitlines()
    hits, longest = [], 0
    for ln, line in enumerate(lines, 1):
        pass
    tk_all, line_of = [], []
    for ln, line in enumerate(lines, 1):
        t = toks(line)
        tk_all += t
        line_of += [ln] * len(t)
    for nn in range(15, 5, -1):
        found = [i for i in range(len(tk_all) - nn + 1) if hash(tuple(tk_all[i:i + nn])) in grams[nn]]
        if found:
            longest = max(longest, nn)
            if nn == 15:
                hits = sorted({line_of[i] for i in found})
            break
    check(not hits, f"{name}: no 15-word run shared with the book (longest shared run: {longest or '<6'} words)"
          + (f"; lines {hits[:10]}" if hits else ""))

# ---------------------------------------------------------------- 6. the 'Try it' snippet
blocks = re.findall(r"```python\n(.*?)```", short, flags=re.S)
check(len(blocks) == 1 and len(blocks[0].strip().splitlines()) <= 10, f"short file: one python snippet of <= 10 lines "
      f"({len(blocks)} block(s), {len(blocks[0].strip().splitlines()) if blocks else 0} lines)")
if blocks:
    exp = re.search(r"#\s*(\[.*\])\s*$", blocks[0].strip().splitlines()[-1]).group(1)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(blocks[0], {})
    check(buf.getvalue().strip() == exp, f"short file: the snippet prints {buf.getvalue().strip()} (comment says {exp})")

# ---------------------------------------------------------------- 7. key numbers appear in the measurement output
out = (HERE / "out_r1_measure.txt").read_text(encoding="utf-8")
KEY = ["0.032522", "0.032266", "0.016129", "0.015873", "0.000256", "0.9625", "9.4618", "0.2535", "0.2598", "0.0909",
       "1.2000", "0.98127", "0.97753", "1.22658", "1.6546", "0.016393", "0.018182", "total 27 of 40", "37/40",
       "MRR@10 0.708", "MRR@10 0.938", "MRR@10 1.000", "MRR@10 0.875", "dense 9/500, BM25 15/500", "0.2959",
       "0.4103", "0.8332", "0.6667, 0.3333", "0.6179, 0.3821", "0.6243", "0.6197", "0.4857", "0.5246", "0.4048",
       "C=0.7000, A=0.3344, B=0.2429", "0.5480", "0.4551", "0.3476", "0.1493", "C=8.31, A=2.72, D=1.80, B=0.58",
       "8/10, BM25 x10 -> 3/10, dense exp(10s) -> 10/10, BM25 sqrt -> 4/10",
       "0/10, BM25 x10 -> 0/10, dense exp(10s) -> 4/10, BM25 sqrt -> 2/10",
       "0/10, BM25 x10 -> 0/10, dense exp(10s) -> 5/10, BM25 sqrt -> 1/10", "Hit@4 0/8 CE@4 0/8",
       "overlap 0/5", "distinct repo-style top-5 lists over the 10 seeds = 1", "[89, 50, 48, 49, 81]", "[50, 28, 89, 48, 29]",
       "[1, 30, 37, 7, 0]", "[31, 7, 38, 30, 1]", "NaN count 97/97", "fused rank 31", "0.03252247488101534",
       "margin 0.000008", "k_rrf 60 -> 0: 5/10", "0.5 -> 0.7 (min-max): 5/10", "property holds for 10/10",
       "1/10", "13.6205", "9.2298", "0.5331", "0.5004", "4.1641", "0.8588", "'the': 80", "dense=4, bm25=1, bm25_split=None",
       "dense=3, bm25=1, bm25_split=None", "dense=4, bm25=1, bm25_split=2", "0.2041", "0.2478", "1.8858", "1.8377",
       "1.7458", "0.4643", "0.35984", "0.0830", "0.6701", "0.0496", "0.9287", "0.63767", "0.5572", "0.4219",
       "D-009: dense raw top 0.3099 -> 1.0; BM25 raw top 6.9559 -> 1.0", "D-010: dense raw top 0.5196 -> 1.0; BM25 raw top 13.2576",
       "[1, 0, 4, 2, 3]", "[0, 4, 1, 2, 3]", "1:0.03226", "0:0.03178", "0:1.20000", "2.846", "3.015", "6.930",
       "0.02885", "0.02845", "D-002=['in', 'what', 'year'", "1d58a0fa", "d4108b89"]
missing = [k for k in KEY if k not in out]
check(not missing, f"{len(KEY)} key numbers found in out_r1_measure.txt" + (f"; missing {missing}" if missing else ""))

print(f"\n{n} checks")
print("ALL PASS" if fails == 0 else f"{fails} FAIL(S)")
