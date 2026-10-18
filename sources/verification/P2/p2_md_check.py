"""P2: check the two study-kit Markdown files of 2026-10-18 (question file and short reading file).

1. study/questions/P2_questions.md loads with the kit's own parser and passes kit.lint_questions; the 17 ids of the
   build spec, in their sets and types; the kept Part L ids; FORMAT field rules (hints, 2-5 keys, 1-2 'for a 4',
   1-3 wrong answers, Hint 3 only on A items, one short question sentence); at most 2 external items; the interview
   item P2-R-07 is verbatim (repo heading of Q45), carries the MIT notice, its quoted repo paragraphs are exact
   substrings of the pinned repo file, the repo's answer comes before our check, and our check names both
   corrections (the unsourced "10x", one-pipeline pool = BEIR's pool bias -> pool BM25 and dense).
2. The data inside the items is recomputed from the toy corpus (postings, AND, OR, postings read) or matched to the
   measured output (S6 MiniLM order, K2 tie flip, K4 pool demo); the toy documents quoted in both files equal the
   corpus file.
3. Every reread line links into the short reading file AND the full lesson and names a book page; each item's
   reread names a reading section that the build spec says teaches it.
4. Every relative link in both files resolves to a file, and every #anchor resolves (GitHub rule: lower-case,
   punctuation removed, each space -> '-'); also every link from any other workspace .md file INTO these files.
5. The reading file's shape (FORMAT §3): header, What this is / is not, the book box with the spec's pages, one
   numbered section per lesson step 1-12 in the spec's order, '13. When not to use it', 'Check yourself';
   1,800-3,000 words of prose (code blocks removed); house-style beats.
6. Book pages: every 'ChN p.x/y' cited exists (y = the chapter's page count); the cited pages hold the short phrases
   the paraphrases rely on (each < 15 words; checked in memory, never printed); 'inverted' and 'qrel' never appear.
7. Copyright: no run of 15 consecutive words is shared with ANY page of the book (text compared in memory, never
   saved; a hit is reported by file and line only, never with its text).
8. Numbers: every decimal number, and every integer >= 10, in the two files matches a number printed by
   p2_measure.py or p2_kit_measure.py (or P2_FACTS), or is on the EXTERNAL (dated research facts) or DERIVED
   (arithmetic shown in the text) list below. Verbatim repo quotes ('> "...' lines) are checked in step 1 instead.
9. The coach-banned phrases of the build spec are absent from both files.
10. `uv run python study/quiz.py --check` passes for P2_questions.md.
Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P2/p2_md_check.py "C:/Yash/New-Work/Book RAG" \
        > sources/verification/P2/out_p2_md_check.txt
"""
import glob
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import pymupdf

ROOT = Path(sys.argv[1])
WS = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BOOK = ROOT / "RAG_Made_Simple_The_Complete_Visual_Guide"
QF = WS / "study" / "questions" / "P2_questions.md"
SHORT = WS / "study" / "reading" / "P2_ir_framing.md"
FULL = WS / "concepts" / "P2_ir_framing.md"
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
check(qtext_all.startswith("<!-- kit:questions concept=P2 version=1 -->"), "question file header line")
ids = [q["id"] for q in qs]
qd = {q["id"]: q for q in qs}
SPEC = {  # id: (set, taught-in steps) from the build spec's table
    "P2-PRE-01": ("pre", [1, 2]), "P2-PRE-02": ("pre", [5]),
    "P2-R-01": ("main", [2]), "P2-R-02": ("main", [3, 10]), "P2-R-03": ("main", [5]), "P2-R-04": ("main", [8, 9]),
    "P2-R-05": ("main", [10]), "P2-R-06": ("main", [1]),
    "P2-A-01": ("main", [5]), "P2-A-02": ("main", [3]), "P2-A-03": ("main", [2, 8]), "P2-A-04": ("main", [6]),
    "P2-A-05": ("main", [10]), "P2-A-06": ("review", [7]),
    "P2-T-01": ("main", [3, 10, 12]), "P2-T-02": ("main", [10]),
    "P2-R-07": ("interview", [3, 10, 12]),
}
check(sorted(ids) == sorted(SPEC) and len(ids) == 17, f"the 17 ids of the build spec, no more, no less ({len(ids)})")
check(len(set(ids)) == len(ids), "ids unique")
check(all(qd[i]["set"] == s for i, (s, _) in SPEC.items() if i in qd), "each id is in the spec's set (pre/main/review/interview)")
check(all(re.fullmatch(r"P2-(PRE|[RAT])-\d\d", i) for i in ids), "ids follow P2-<type>-<nn> / P2-PRE-<nn>")
check(all(q["id"].split("-")[1] == q["type"] or q["id"].startswith("P2-PRE") for q in qs), "id letter = type")
check(ids[:2] == ["P2-PRE-01", "P2-PRE-02"] and [i for i in ids if "PRE" in i] == ids[:2], "the 2 set=pre items come first, in order")
by = defaultdict(list)
for q in qs:
    by[(q["set"], q["type"])].append(q["id"])
cnt = lambda s, t=None: sum(len(v) for (ss, tt), v in by.items() if ss == s and (t is None or tt == t))
print(f"     items: {len(qs)}; pre {cnt('pre')}; main {cnt('main')} (R {cnt('main', 'R')}, A {cnt('main', 'A')}, "
      f"T {cnt('main', 'T')}); review {cnt('review')}; interview {cnt('interview')}")
partL = full[full.index("## Part L"):full.index("## Part M")]
kept = [f"P2-R-0{k}" for k in range(1, 5)] + [f"P2-A-0{k}" for k in range(1, 4)] + ["P2-T-01"]
check(all(i in ids and qd[i]["set"] == "main" and re.search(rf"\*\*{i}\.?\*\*", partL) for i in kept),
      "the full lesson's Part L ids P2-R-01..04, P2-A-01..03, P2-T-01 are kept as set=main")
MEANING = {  # a phrase of each kept Part L item that the kit item must keep (same meaning)
    "P2-R-01": ("similarity and relevance", "similarity and relevance"),
    "P2-R-02": ("one line of a qrels file", "one line of a qrels file"),
    "P2-R-03": ("inverted index", "inverted index"), "P2-R-04": ("set recall", "first relevant rank"),
    "P2-A-01": ("build_index(docs)", "build_index(docs)"), "P2-A-02": ("why do sea levels rise", "why do sea levels rise"),
    "P2-A-03": ("from 3 to 6", "set precision"), "P2-T-01": ("legal team", "30"),
}
check(all(a.lower() in qd[i]["question"].lower() and b.lower() in qd[i]["question"].lower() and a.lower() in partL.lower()
          for i, (a, b) in MEANING.items()), "each kept Part L item keeps its meaning (key phrase in both)")
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
INTERVIEW = {"P2-R-07": ("AIQ-04-Q45", "04-rag-and-retrieval/questions.md", 45)}
for qid, (src, relp, num) in INTERVIEW.items():
    q = qd[qid]
    repo = (AIQ / relp).read_text(encoding="utf-8")
    check(q["source"] == src and q["set"] == "interview" and q["type"] == "R", f"{qid}: set=interview, source={src}")
    check("ombharatiya/AI-Engineer-Interview-Questions @ e080df2" in q["question"] and f"`{relp}`" in q["question"]
          and "Copyright (c) 2026 Om, MIT License" in q["question"], f"{qid}: MIT notice with the verbatim question")
    verb = re.match(r'"(.+)"', q["question"].splitlines()[0]).group(1)
    check(f"### {num}. {verb}" in repo, f"{qid}: the quoted question is verbatim in the repo (heading of Q{num})")
    pre = q["answer"]["preamble"]
    quotes = [l[l.index('"') + 1:l.rindex('"')] for l in pre.splitlines() if re.match(r'^>\s*"', l)]
    check(len(quotes) >= 2 and all(x in repo for x in quotes) and "Copyright (c) 2026 Om, MIT License" in pre
          and pre.index("The repo's answer") < pre.index("Our check of that answer"),
          f"{qid}: the {len(quotes)} quoted repo paragraphs ({sum(len(x.split()) for x in quotes)} words) are verbatim, "
          f"with the MIT notice, before our check")
    ours = pre[pre.index("Our check of that answer"):]
    check("10× faster" in ours and "no source" in ours and "pool bias" in ours and "BM25 **and** dense" in ours
          and "Judged@k" in ours, f"{qid}: our check names both corrections (unsourced 10x; one-pipeline pool = BEIR pool bias -> pool BM25 and dense)")
    check(bool(q["answer"]["model"]) and "both a keyword (BM25) and a dense retriever" in q["answer"]["model"],
          f"{qid}: our own model answer follows the repo's answer and pools both retrievers")
print("     note: the interview question is verbatim; the one-sentence rule is not applied to it")

# ---------------------------------------------------------------- 2. the data inside the items
corpus = json.loads((HERE / "p2_toy_corpus.json").read_text(encoding="utf-8"))
DOCS = corpus["docs"]
tok = lambda t: re.findall(r"[a-z0-9]+", t.lower())
index = defaultdict(set)
for d, t in DOCS.items():
    for w in set(tok(t)):
        index[w].add(d)
post = {w: sorted(v) for w, v in index.items()}
check(len(post) == 88 and sum(map(len, post.values())) == 114, "toy index recomputed: 88 terms, 114 postings (S3)")
a04 = qd["P2-A-04"]["question"]
lists = dict(re.findall(r"^(\w+)\s*→\s*(.+)$", a04, re.M))
check({k: [x.strip() for x in v.split(",")] for k, v in lists.items()} == {w: post[w] for w in ("climate", "of", "the")},
      "P2-A-04: the three postings lists in the question equal the toy index (climate, of, the)")
AND = sorted(set(post["climate"]) & set(post["of"]) & set(post["the"]))
OR = sorted(set(post["climate"]) | set(post["of"]) | set(post["the"]))
read = sum(len(post[w]) for w in ("climate", "of", "the"))
m04 = qd["P2-A-04"]["answer"]["model"]
check(AND == ["d02"] and f"OR  = {', '.join(OR)}" in m04 and f"= {read}" in m04 and read == 9,
      f"P2-A-04: answer recomputed (AND {AND}, OR {len(OR)} docs, postings read {read})")
r06 = qd["P2-R-06"]["answer"]
check(post["carbon"] == ["d01", "d06"] and post["dioxide"] == ["d01", "d06"] and "`carbon` → d01, d06" in r06["four"][0],
      "P2-R-06: 'carbon dioxide' hits exactly d01 and d06 in the toy index")
mo = (HERE / "out_p2_measure.txt").read_text(encoding="utf-8")
ko = (HERE / "out_p2_kit_measure.txt").read_text(encoding="utf-8")
s6q1 = re.findall(r"(d\d\d) [\d.]+", re.search(r"^q1: (d02 0\.8402.*)$", mo, re.M).group(1))
check(", ".join(s6q1) in qd["P2-A-03"]["question"], f"P2-A-03: MiniLM q1 order equals S6 ({', '.join(s6q1)})")
check("run=['d06', 'd09'] scores=[1, 1] first relevant rank=2 RR=0.50" in ko
      and "run=['d09', 'd06'] scores=[1, 1] first relevant rank=1 RR=1.00" in ko
      and "d09, d06    first relevant rank 1    RR 1.00" in qd["P2-A-06"]["answer"]["model"], "P2-A-06: the tie flip matches K2")
check("'q1': ['d01', 'd02', 'd08']" in ko and "MiniLM   q1 top4=['d02', 'd01', 'd04', 'd03'] judged@4=2/4 P@4 full=0.500 pooled=0.250 recall full=0.667 pooled=1.000" in ko
      and "d02, d01, d04, d03" in qd["P2-A-05"]["question"] and "0.500" in qd["P2-A-05"]["answer"]["model"]
      and "0.250" in qd["P2-A-05"]["answer"]["model"] and "1.000" in qd["P2-A-05"]["answer"]["model"],
      "P2-A-05: pool, MiniLM top 4 and P@4 / recall match K4")
grades = {(r["qid"], r["did"]): r["grade"] for r in corpus["qrels"]}
check(all(grades.get(("q1", d), 0) == g for d, g in (("d01", 2), ("d02", 0), ("d08", 0), ("d03", 1), ("d09", 1))),
      "P2-A-05: the grades in the question equal the toy qrels")
docline = lambda text: dict(re.findall(r"^(d\d\d)  (.+?)\s*$", text, re.M))
check(docline(qd["P2-A-02"]["question"]) == DOCS, "P2-A-02: the ten documents in the question equal the toy corpus")
check(docline(short) == DOCS, "reading §1: the ten toy documents equal the toy corpus")
check(grades[("q2", "d04")] == 2 and grades[("q2", "d05")] == 1 and sum(1 for (qq, _), g in grades.items() if qq == "q2" and g) == 2,
      "P2-A-02: reference labels d04 = 2, d05 = 1, all others 0 (S7)")

# ---------------------------------------------------------------- 3. reread lines


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
    ok = ("../reading/P2_ir_framing.md#" in rr and "../../concepts/P2_ir_framing.md#" in rr
          and re.search(r"book (Ch\d+|App) p\.\d", rr))
    check(bool(ok), f"{q['id']}: reread links to the short AND the full file, plus a book page")
    steps = SPEC[q["id"]][1]
    linked = re.findall(r"\.\./reading/P2_ir_framing\.md#([\w-]+)", rr)
    check(all(step_anchor.get(s) in linked for s in steps),
          f"{q['id']}: reread names every short section the spec says teaches it (steps {steps})")


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
check(not bad_in, f"{inbound} links from other workspace files into the two P2 kit files resolve" + (f": {bad_in}" if bad_in else ""))

# ---------------------------------------------------------------- 5. reading file shape and length


def words(text, strip_code=False):
    if strip_code:
        text = re.sub(r"```.*?```", " ", text, flags=re.S)
    return len(text.split())


print(f"     word count: reading file {words(short)} (prose only, code blocks removed: {words(short, True)}); "
      f"question file {words(qtext_all)}")
check(1800 <= words(short, True) <= 3000, f"reading file prose within 1,800-3,000 words ({words(short, True)})")
check(short.startswith("<!-- kit:reading concept=P2 depth=short version=1 -->"), "reading file header line")
check(all(h in short for h in ("**What this is:**", "**What this is not:**", "> **Read in the book:**", "## Check yourself")),
      "reading file has What this is / is not, the book box and Check yourself (FORMAT §3)")
box = re.search(r"> \*\*Read in the book:\*\*(.+)", short).group(1)
check(all(p in box for p in ("Ch1 p.8/14", "Ch3 p.1/14", "Ch13 p.1–2/13", "Ch22 p.4–7/19", "p.12/19")),
      "book box names Ch1 p.8/14, Ch3 p.1/14, Ch13 p.1-2/13, Ch22 p.4-7/19 and p.12/19")
STEP_WORDS = {1: ("need",), 2: ("similarity", "relevance"), 3: ("judges", "qrels"), 4: ("meanings", "relevance"),
              5: ("inverted index",), 6: ("boolean", "postings read"), 7: ("ranking", "candidates", "ties"),
              8: ("cut at k", "precision", "recall"), 9: ("set quality", "ranking quality"),
              10: ("incomplete", "noisy"), 11: ("real pdf",), 12: ("project", "test collection")}
titles = [t for t, _ in short_heads]
numbered = [t for t in titles if re.match(r"\d+\.", t)]
check([int(t.split(".")[0]) for t in numbered] == list(range(1, 14)), f"sections ## 1. ... ## 13. in order ({len(numbered)})")
check(all(all(w in numbered[s - 1].lower() for w in ws) for s, ws in STEP_WORDS.items()),
      "sections 1-12 follow the spec's step order (each title names its step)")
check(numbered[12].lower().endswith("when not to use it") and titles[-1] == "Check yourself",
      "section 13 is 'When not to use it', then 'Check yourself'")
beats = [len(re.findall(b, short)) for b in (r"\*\*The setup\.\*\*", r"\*\*The result\b", r"\*\*What this means\.\*\*",
                                               r"\*\*For your project:\*\*")]
check(all(b >= 12 for b in beats), f"house style beats per section: setup {beats[0]}, result {beats[1]}, means {beats[2]}, project {beats[3]}")
check("(../questions/P2_questions.md)" in short, "Check yourself links the question file")
counts = re.search(r"(\d+) cold questions before reading, (\d+) after, (\d+) for a later review, and (\d+) interview", short)
check(counts and tuple(map(int, counts.groups())) == (cnt("pre"), cnt("main"), cnt("review"), cnt("interview")),
      "Check yourself states the right item counts per set")

# ---------------------------------------------------------------- 6. book pages and the phrases the paraphrases rely on
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
        for p in range(int(m.group(2)), int(m.group(3) or m.group(2)) + 1):
            cites.add((m.group(1), p, int(m.group(4))))
    for m in re.finditer(r"\b(Ch\d+) p\.\d+(?:–\d+)?/\d+ and p\.(\d+)(?:–(\d+))?/(\d+)", text):
        for p in range(int(m.group(2)), int(m.group(3) or m.group(2)) + 1):
            cites.add((m.group(1), p, int(m.group(4))))
badc = [c for c in sorted(cites) if c[0] not in docs or len(docs[c[0]]) != c[2] or not 1 <= c[1] <= c[2]]
check(not badc, f"{len(cites)} distinct book pages cited; each exists with the right page count" + (f"; bad: {badc}" if badc else ""))
flat = lambda ch, p: " ".join(toks(docs[ch][p - 1]))
PHRASES = [  # (chapter, page, short phrase) each < 15 words; the claim it supports is in the reading or question file
    ("Ch1", 8, "main cause of climate change"), ("Ch1", 8, "directly relevant"),
    ("Ch3", 1, "does not always mean"), ("Ch3", 1, "footer"),
    ("Ch13", 1, "none of them names paris"), ("Ch13", 2, "rough proxy for relevance"),
    ("Ch12", 3, "index at the back"), ("Ch12", 3, "which pages mention"),
    ("Ch22", 4, "context relevance"), ("Ch22", 4, "precision at k"), ("Ch22", 4, "relevant or not relevant"),
    ("Ch22", 5, "all relevant documents in the knowledge base"),
    ("Ch22", 6, "how well it was ranked"), ("Ch22", 6, "first correct result"), ("Ch22", 7, "same documents"),
    ("Ch22", 12, "expected relevant documents"), ("Ch22", 12, "reference answer"),
    ("App", 20, "post retrieval filter"),
]
miss = [f"{c} p.{p}" for c, p, ph in PHRASES if " ".join(toks(ph)) not in flat(c, p)]
check(not miss, f"{len(PHRASES)} short phrases found on the cited pages (checked in memory)" + (f"; missing on {miss}" if miss else ""))
allbook = "\n".join("\n".join(pages) for pages in docs.values()).lower()
check("inverted" not in allbook and "qrel" not in allbook, "the book never says 'inverted' or 'qrel' (as the reading file states)")

# ---------------------------------------------------------------- 7. 15-word overlap with the book (in memory only)
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

# ---------------------------------------------------------------- 8. numbers are traceable
outs = {"p2_measure": mo, "p2_kit_measure": ko, "P2_FACTS": (HERE / "P2_FACTS.md").read_text(encoding="utf-8")}
NUM = re.compile(r"(?<![\w.,/])(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?![\w/])")
pool = set()
for t in outs.values():
    for m in re.finditer(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?", t):
        pool.add(m.group(0).replace(",", ""))
pool_f = [float(s) for s in pool]
EXTERNAL = {  # research phase_01 Concept P2 §1/§5 (sources read 2026-10-17); they are not ours
    "6.4": "BEIR Table 4 Hole@10 BM25 [P2-13]", "2.8": "BEIR Hole@10 docT5query", "14.4": "BEIR Hole@10 ANCE",
    "30.6": "BEIR Hole@10 DPR", "31.8": "BEIR Hole@10 TAS-B", "0.654": "BEIR ANCE nDCG@10 before",
    "0.735": "BEIR ANCE nDCG@10 after judging holes", "0.656": "BEIR BM25 nDCG@10 before", "0.668": "BEIR BM25 after",
    "0.776": "IIR §8.5 prints kappa 0.776 [P2-8]", "0.8": "IIR kappa threshold good", "0.67": "IIR kappa threshold fair",
}
DERIVED = {  # arithmetic shown next to each in the text, or the item's own data
    "42": "50 - 8 (shown)", "0.650": "1 - 0.350 (shown)", "30": "the item's own data (30 questions)",
}
unmatched = {}
for name, path in (("question file", QF), ("reading file", SHORT)):
    text = Path(path).read_text(encoding="utf-8")
    text = "\n".join(l for l in text.splitlines() if not re.match(r'^>\s*"', l))           # verbatim repo quotes (step 1)
    text = re.sub(r"\]\([^)]*\)", "]", text)                                                 # link targets
    text = re.sub(r"\b(Ch\d+|App) p\.\d+(?:–\d+)?/\d+", " ", text)                           # book pages
    text = re.sub(r"\bp\.\d+(?:–\d+)?/\d+", " ", text)
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b|\b(?:19|20)\d\d\b", " ", text)                     # dates, years
    text = re.sub(r"\b\d+\.\d+\.\d+\b", " ", text)                                           # versions (rank_bm25 0.2.2)
    text = re.sub(r"\b[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+\b|§[\d.]+|\b[SKQEDO]\d+\b|#\d+|e080df2|question \d+", " ", text)
    for m in NUM.finditer(text):
        s = m.group(0).replace(",", "")
        x = float(s)
        if "." not in s and x < 10:
            continue
        if s in EXTERNAL or s in DERIVED:
            continue
        d = len(s.split(".")[1]) if "." in s else 0
        ok = (s in pool or any(abs(y - x) <= 0.5 * 10 ** -d + 1e-12 for y in pool_f)) if d else s in pool
        if not ok:
            unmatched.setdefault(m.group(0), set()).add(name)
check(not unmatched, "every decimal and every integer >= 10 matches a printed value (p2_measure, p2_kit_measure, "
      "P2_FACTS) or the EXTERNAL / DERIVED list" + (f"; unmatched: {unmatched}" if unmatched else ""))
KEY = ["0.8402", "0.6342", "0.2469", "0.5804", "88", "114", "71", "119", "8 of 50", "0.333", "0.667", "1,868", "8,107",
       "213", "0.350", "0.200", "0.933", "0.567", "0.500", "0.250", "0.7759", "384", "44"]
miss_out = [k for k in KEY if not any(k in t or k.replace(",", "") in t for t in outs.values())]
check(not miss_out, f"{len(KEY)} key numbers are printed by the measurement scripts or P2_FACTS" + (f"; missing {miss_out}" if miss_out else ""))
miss_md = [k for k in KEY if k != "8 of 50" and not any(k in t for t in (qtext_all, short))]
check(not miss_md and "8 relevant pairs out of 50" in short, "each key number is quoted in the question or reading file"
      + (f"; not quoted: {miss_md}" if miss_md else ""))

# ---------------------------------------------------------------- 9. coach-banned phrases (build spec)
BANNED = ["share of queries", "fraction of queries", "a guide says", "sixth", "add a pdf", "adding a document",
          "new document", "another pdf", "tenant", "300 pdf", "without reading", "half noise", "0.729", "three stages"]
hits = {p.name: [w for w in BANNED if w in p.read_text(encoding="utf-8").lower()] for p in (QF, SHORT)}
check(not any(hits.values()), f"none of the {len(BANNED)} coach-banned phrases appears ({hits})")

# ---------------------------------------------------------------- 10. the kit's own format check
r = subprocess.run([sys.executable, str(WS / "study" / "quiz.py"), "--check"], capture_output=True, text=True,
                   encoding="utf-8", cwd=str(WS))
line = next((l for l in r.stdout.splitlines() if "P2_questions.md" in l), "")
print("     quiz.py --check: " + " | ".join(l.strip() for l in r.stdout.splitlines() if l.strip()))
check(line.strip().startswith("OK") and "17 questions" in line, f"study/quiz.py --check passes for P2 ({line.strip()})")
check(r.returncode == 0, f"study/quiz.py --check exits 0 for all files (exit {r.returncode})")

print(f"\n{n} checks")
print("ALL PASS" if fails == 0 else f"{fails} FAIL(S)")
