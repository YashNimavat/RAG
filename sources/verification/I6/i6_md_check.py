"""I6: check the study-kit Markdown files of 2026-10-18 (question file, short reading file) and, when it exists,
the HTML lesson's text.

1. study/questions/I6_questions.md loads with the kit's own parser and passes kit.lint_questions; the 17 ids of the
   build spec (I6_BUILD_SPEC.md §4) with their types and sets; FORMAT field rules (Hint 1 + Hint 2, Hint 3 only on
   A items, 2-5 key points, 1-2 'for a 4', 1-3 wrong answers, one short question sentence); at most 2 external
   items; the interview item I6-R-06 quotes AIQ-04 Q45 verbatim with the MIT notice, its quoted repo paragraphs are
   exact substrings of the pinned repo file, the repo's answer comes before our check, and our check names the echo
   (0.777) and the K9 near-copies.
2. The data inside the items is recomputed: I6-A-02's new 8-vector table (max and sum rankings, sums, that the two
   rankings differ and that it is not the lesson's K3 toy); I6-A-01 sizes; I6-A-03 break-even; I6-A-04 K_vec;
   I6-A-05 flags against tau and the K9 values.
3. Every reread line links the short reading file AND the HTML lesson step and names a book page 'Ch11 p.x/13';
   each names the reading section(s) and lesson step(s) the spec says teach it.
4. Every relative link in the two files resolves, with its #anchor (GitHub rule for .md, element ids for .html);
   links into the not-yet-written lesson print PENDING. Links from other workspace .md files into the two files.
5. The reading file's shape (FORMAT §3, spec §5): header, What this is / is not, the book box, sections 1-11 in the
   lesson's step order, '12. When not to use it', 'Check yourself'; 1,800-3,000 words of prose (code blocks
   removed); house-style beats; the spec §10 labels.
6. Book pages: if the book folder is missing (it is not in the build container) the page checks and the whole-book
   15-word check print SKIPPED; otherwise every 'Ch11 p.x/13' exists and no 15-word run is shared with the book.
7. Copyright: no run of 15 consecutive words is shared with the climate PDF or the upstream RAG_Techniques
   notebooks and scripts (verbatim interview quotes excepted; text compared in memory, hits reported by line only).
8. Numbers: every decimal and every integer >= 10 in the files (and in the lesson, when present) matches a number
   printed in out_i6_kit_measure.txt or I6_FACTS.md, or is on the EXTERNAL (spec §7) or DERIVED list below; the
   spec §8 key numbers are printed by the measurement and quoted in at least one file.
9. The spec §9 banned phrases are absent; no Claude model identifier strings.
10. `uv run python study/quiz.py --check` passes for I6_questions.md.
Run from rag_learning/ (ROOT holds upstream/ and, on Yash's machine, the book folder):
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I6/i6_md_check.py "C:/Yash/New-Work/Book RAG" \
        > sources/verification/I6/out_i6_md_check.txt
"""
import glob
import html
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
QF = WS / "study" / "questions" / "I6_questions.md"
SHORT = WS / "study" / "reading" / "I6_doc_augmentation.md"
LESSON = WS / "study" / "lessons" / "I6_doc_augmentation.html"
AIQ_DIR = ROOT / "upstream" / "AI-Engineer-Interview-Questions"
AIQ = AIQ_DIR / "04-rag-and-retrieval" / "questions.md"
RT = ROOT / "upstream" / "RAG_Techniques"
PDF = RT / "data" / "Understanding_Climate_Change.pdf"
fails = n = pend = skip = 0


def check(ok, label):
    global fails, n
    n += 1
    fails += not ok
    print(("PASS " if ok else "FAIL ") + label)


def pending(label):
    global pend
    pend += 1
    print("PENDING " + label)


def skipped(label):
    global skip
    skip += 1
    print("SKIPPED " + label)


# ---------------------------------------------------------------- 1. question file
sys.path.insert(0, str(WS / "study"))
import kit  # noqa: E402

qs = kit.parse_questions(QF)
qtext = QF.read_text(encoding="utf-8")
short = SHORT.read_text(encoding="utf-8")
HAVE_LESSON = LESSON.exists()
if HAVE_LESSON:
    raw_html = LESSON.read_text(encoding="utf-8")
    body = raw_html.split('<main id="main">', 1)[1].split("</main>", 1)[0] if '<main id="main">' in raw_html else raw_html
    body = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", body, flags=re.S)
    lesson_text = html.unescape(re.sub(r"<[^>]+>", " ", body))
    lesson_ids = set(re.findall(r'\bid="([^"]+)"', raw_html))
else:
    raw_html = lesson_text = ""
    lesson_ids = set()
    pending(f"the HTML lesson {LESSON.relative_to(WS)} does not exist yet: lesson link, anchor, number and wording checks wait for it")

problems = kit.lint_questions(QF)
check(not problems, f"kit.lint_questions: {problems or 'no problems'}")
check(qtext.startswith("<!-- kit:questions concept=I6 version=1 -->"), "question file header line")
SPEC = {  # id: (type, set, taught-in steps) from I6_BUILD_SPEC.md §4
    "I6-PRE-01": ("R", "pre", [1]), "I6-PRE-02": ("R", "pre", [2]),
    "I6-R-01": ("R", "main", [5, 6, 7]), "I6-R-02": ("R", "main", [5, 8]), "I6-R-03": ("R", "main", [6]),
    "I6-R-04": ("R", "main", [2, 10]), "I6-R-05": ("R", "review", [7]), "I6-R-06": ("R", "interview", [4, 9]),
    "I6-A-01": ("A", "main", [5, 10]), "I6-A-02": ("A", "main", [6]), "I6-A-03": ("A", "main", [10]),
    "I6-A-04": ("A", "main", [6]), "I6-A-05": ("A", "main", [9]), "I6-A-06": ("A", "review", [8]),
    "I6-T-01": ("T", "main", [9, 12]), "I6-T-02": ("T", "main", [5, 8]), "I6-T-03": ("T", "review", [10]),
}
STEP_ID = {1: "shape", 2: "lanes", 3: "generate", 4: "clean", 5: "designs", 6: "search", 7: "score", 8: "guard",
           9: "leak", 10: "cost", 11: "upstream", 12: "project"}
ids = [q["id"] for q in qs]
qd = {q["id"]: q for q in qs}
check(sorted(ids) == sorted(SPEC) and len(ids) == 17, f"the 17 ids of the build spec, no more, no less ({len(ids)})")
check(len(set(ids)) == len(ids), "ids unique")
check(all(qd[i]["type"] == t and qd[i]["set"] == s for i, (t, s, _) in SPEC.items() if i in qd),
      "each id has the spec's type and set (pre/main/review/interview)")
check(all(re.fullmatch(r"I6-(PRE|[RAT])-\d\d", i) for i in ids), "ids follow I6-<type>-<nn> / I6-PRE-<nn>")
check(ids[:2] == ["I6-PRE-01", "I6-PRE-02"], "the 2 set=pre items come first, in order")
cnt = lambda s: sum(1 for q in qs if q["set"] == s)
print(f"     items: {len(qs)}; pre {cnt('pre')}; main {cnt('main')}; review {cnt('review')}; interview {cnt('interview')}")
blocks = dict((re.search(r"id=(\S+)", h).group(1), b) for h, b in re.findall(r"<!-- q (.*?) -->(.*?)<!-- /q -->", qtext, re.S))
bad_fmt = []
for q in qs:
    b = blocks.get(q["id"], "")
    ok = ("<summary>Hint 1</summary>" in b and "<summary>Hint 2</summary>" in b
          and ("<summary>Hint 3</summary>" not in b or q["type"] == "A")
          and 2 <= len(q["answer"]["keys"]) <= 5 and 1 <= len(q["answer"]["four"]) <= 2 and 1 <= len(q["answer"]["wrong"]) <= 3
          and b.count("<details>") == len(q["hints"]) + 1)
    if q["set"] != "interview":
        first = q["question"].splitlines()[0]
        ends = len(re.findall(r"[.?!]\"?(?:\s|$)", first))
        ok = ok and ends == 1 and first.rstrip().endswith(("?", ".")) and len(first.split()) <= 45
    if not ok:
        bad_fmt.append(q["id"])
check(not bad_fmt, f"FORMAT rules per item: Hint 1+2, Hint 3 only on A, 2-5 keys, 1-2 'for a 4', 1-3 wrong answers, "
      f"no nested details, one short question sentence ({bad_fmt or 'all 17'})")
check(sum(1 for q in qs if q["source"]) <= 2, f"at most 2 external items ({sum(1 for q in qs if q['source'])})")
check(all(re.search(r"\bMC-00[236]\b", " ".join(qd[i]["answer"]["wrong"])) for i in ("I6-PRE-01", "I6-PRE-02", "I6-R-04", "I6-A-05")),
      "the matching misconception ids are named (MC-002 matrix, MC-003 stages, MC-006 uncalibrated threshold)")

# interview item
repo = AIQ.read_text(encoding="utf-8")
lic = next(AIQ_DIR.glob("LICENSE*")).read_text(encoding="utf-8")
check("MIT License" in lic and "Copyright (c) 2026 Om" in lic, "AIQ licence file: MIT, Copyright (c) 2026 Om")
r06 = qd["I6-R-06"]
check(r06["source"] == "AIQ-04-Q45" and r06["set"] == "interview" and r06["type"] == "R", "I6-R-06: set=interview, source=AIQ-04-Q45")
check("ombharatiya/AI-Engineer-Interview-Questions @ e080df2" in r06["question"] and "`04-rag-and-retrieval/questions.md`" in r06["question"]
      and "Copyright (c) 2026 Om, MIT License" in r06["question"], "I6-R-06: MIT notice with the verbatim question")
verb = re.match(r'"(.+)"', r06["question"].splitlines()[0]).group(1)
check(f"### 45. {verb}" in repo, f"I6-R-06: the quoted question is verbatim in the repo (heading of Q45 at line "
      f"{repo[:repo.index('### 45. ')].count(chr(10)) + 1})")
pre = r06["answer"]["preamble"]
quotes = [l[l.index('"') + 1:l.rindex('"')] for l in pre.splitlines() if re.match(r'^>\s*"', l)]
check(len(quotes) >= 2 and all(x in repo for x in quotes) and "Copyright (c) 2026 Om, MIT License" in pre
      and pre.index("The repo's answer") < pre.index("Our check of that answer"),
      f"I6-R-06: the {len(quotes)} quoted repo paragraphs ({sum(len(x.split()) for x in quotes)} words) are exact substrings "
      f"of the pinned file, with the MIT notice, before our check")
check(any("echo the chunk's vocabulary" in x for x in quotes), "I6-R-06: the quoted answer includes the 'echo the chunk's vocabulary' point")
ours = pre[pre.index("Our check of that answer"):]
check(all(s in ours for s in ("0.777", "0.9869", "0.9653", "0.9368", "0.547", "0.7054")),
      "I6-R-06: our check names the echo (0.777), the K9 near-copies and the de-leaked result")
check(bool(r06["answer"]["model"]) and "leak(i)" in r06["answer"]["model"], "I6-R-06: our own model answer follows and names leak(i)")
print("     note: the interview question is verbatim; the one-sentence rule is not applied to it")

# ---------------------------------------------------------------- 2. data inside the items
ko = (HERE / "out_i6_kit_measure.txt").read_text(encoding="utf-8")
facts = (HERE / "I6_FACTS.md").read_text(encoding="utf-8")
a02 = qd["I6-A-02"]
rows = re.findall(r"^v(\d)\s+([XYZ])\s+(question|chunk)\s+(\d\.\d+)\s*$", a02["question"], re.M)
own, scores = {}, []
for _, p, _, s in rows:
    own.setdefault(p, []).append(float(s))
    scores.append(float(s))
mx = {p: max(v) for p, v in own.items()}
sm = {p: round(sum(v), 2) for p, v in own.items()}
omax = sorted(mx, key=lambda p: -mx[p])
osum = sorted(sm, key=lambda p: -sm[p])
m02 = a02["answer"]["model"]
k3 = [float(x) for x in re.findall(r"\d\.\d+", re.search(r"^Vectors \(kind, parent, score\): (.+)$", facts, re.M).group(1))]
check(len(rows) == 8 and len(own) == 3 and scores == sorted(scores, reverse=True), f"I6-A-02: 8 vectors over 3 parents, in rank order ({len(rows)})")
check(omax != osum, f"I6-A-02: max and sum rankings differ (max {omax}, sum {osum})")
check(f"max: {', '.join(omax)}" in m02 and f"sum: {', '.join(osum)}" in m02 and all(f"{v:.2f}" in m02 for v in sm.values()),
      f"I6-A-02: the model answer equals the recomputed rankings and sums {sm}")
win = osum[0]
check(win != omax[0] and len(own[win]) == max(map(len, own.values())) and f"{win} wins under sum only because it owns {len(own[win])} vectors" in m02,
      f"I6-A-02: the sum winner {win} is not the max winner and has the most vectors ({len(own[win])})")
check(sorted(scores) != sorted(k3), "I6-A-02: the table is new, not the lesson's K3 toy")
m01 = qd["I6-A-01"]["answer"]["model"]
check(f"{97 * 6:,}" in m01 and f"{97 * 5:,}" in m01 and f"{582 * 1536 * 4:,}" in m01 and f"{485 * 1536 * 4:,}" in m01
      and "3,575,808" in ko and "2,979,840" in ko, "I6-A-01: 582 / 485 vectors and 3,575,808 / 2,979,840 bytes recomputed and printed by K4")
m03 = qd["I6-A-03"]["answer"]["model"]
check(f"= {97 * 2}" in m03 and f"= {97 * 30:,}" in m03 and "exceed 194 a month" in ko and "exceed 2,910 a month" in ko,
      "I6-A-03: 194 and 2,910 recomputed and printed by K10")
check(f"= {4 * 11}" in qd["I6-A-04"]["answer"]["model"] and "max 11; bound k(n+1) = 44" in ko,
      "I6-A-04: K_vec = 4 x 11 = 44 recomputed; the measured need (max 11) matches K6")
a05 = qd["I6-A-05"]
data05 = dict(re.findall(r"^(D-\d{3})\s+(\d\.\d{4})\s*$", a05["question"], re.M))
tau = 0.7054
flag = [i for i, v in data05.items() if float(v) >= tau]
nofl = [i for i, v in data05.items() if float(v) < tau]
k9 = {i: v for i, v in re.findall(r"^(D-\d{3})\s+leak_cos=(\d\.\d{4})", ko, re.M)}
check(len(data05) == 5 and all(k9.get(i) == v for i, v in data05.items()) and f"cos = {tau}" in ko,
      "I6-A-05: the five leak_cos values and tau equal K9")
m05 = a05["answer"]["model"]
check(all(i in m05.split("not flagged")[0] for i in flag) and all(i in m05.split("not flagged")[1].split("\n")[0] for i in nofl),
      f"I6-A-05: flagged {flag}, not flagged {nofl} recomputed")

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


short_heads = [(t, a) for lvl, t, a in headings(SHORT) if lvl == 2]
step_anchor = {int(re.match(r"(\d+)\.", t).group(1)): a for t, a in short_heads if re.match(r"\d+\.", t)}
bad_rr, miss_steps = [], []
for q in qs:
    rr = q["answer"]["reread"]
    if not ("../reading/I6_doc_augmentation.md#" in rr and "../lessons/I6_doc_augmentation.html#" in rr
            and re.search(r"book Ch11 p\.\d+(?:–\d+)?/13\b", rr)):
        bad_rr.append(q["id"])
    linked = re.findall(r"\.\./reading/I6_doc_augmentation\.md#([\w-]+)", rr)
    lsteps = re.findall(r"\.\./lessons/I6_doc_augmentation\.html#([\w-]+)", rr)
    steps = SPEC[q["id"]][2]
    if not (all(step_anchor.get(s) in linked for s in steps) and all(STEP_ID[s] in lsteps for s in steps)):
        miss_steps.append(q["id"])
check(not bad_rr, f"every reread links the short reading file AND the lesson step and names a book page Ch11 p.x/13 ({bad_rr or 'all 17'})")
check(not miss_steps, f"every reread names the reading section(s) and lesson step(s) the spec says teach it ({miss_steps or 'all 17'})")


# ---------------------------------------------------------------- 4. links and anchors
def links_in(text):
    body_lines, fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if not fence:
            body_lines.append(line)
    return re.findall(r"\]\(([^)\s]+)\)", "\n".join(body_lines))


lesson_links = []
for name, path in (("question file", QF), ("reading file", SHORT)):
    bad, links, waiting = [], links_in(Path(path).read_text(encoding="utf-8")), 0
    for href in links:
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        target, _, anc = href.partition("#")
        tp = (Path(path).parent / target).resolve() if target else Path(path)
        if tp == LESSON.resolve():
            lesson_links.append((name, anc))
            if not HAVE_LESSON:
                waiting += 1
                continue
            if anc and anc not in lesson_ids:
                bad.append(f"missing lesson id {href}")
        elif not tp.exists():
            bad.append(f"missing file {href}")
        elif anc and tp.suffix == ".md" and anc not in anchors(tp):
            bad.append(f"missing anchor {href}")
    check(not bad, f"{name}: {len(links) - waiting} links resolve ({sum('#' in h for h in links)} with #anchors in all)"
          + ("" if not bad else ": " + "; ".join(bad[:8])))
needed_ids = sorted({a for _, a in lesson_links})
if HAVE_LESSON:
    check(set(needed_ids) <= lesson_ids, f"the lesson has the {len(needed_ids)} step ids the files link to ({needed_ids})")
    kit_paths = re.findall(r'data-path="rag_learning/([^"]+)"', raw_html)
    missing_kit = [p for p in kit_paths if not (WS / p).exists()]
    planned = set(re.findall(r"`((?:study|sources)/[^`]+)`", (HERE / "I6_BUILD_SPEC.md").read_text(encoding="utf-8")))
    later = [p for p in missing_kit if p in planned or ("study/tools/examples/" + p.split("/")[-1]) in planned]
    check(not set(missing_kit) - set(later), f"the lesson's {len(kit_paths)} study-kit file links point at existing files"
          + (f": {sorted(set(missing_kit) - set(later))}" if set(missing_kit) - set(later) else ""))
    if later:
        pending(f"lesson links to spec §1 files another helper is still building: {later}")
else:
    pending(f"{len(lesson_links)} links into the lesson (ids {needed_ids}) wait for {LESSON.name}")
inbound, bad_in = 0, []
MINE = {SHORT.resolve(), QF.resolve()}
for md in WS.rglob("*.md"):
    if md.resolve() in MINE or "AI Eval" in md.parts or ".venv" in md.parts:
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
check(not bad_in, f"{inbound} links from other workspace files into the two I6 kit files resolve" + (f": {bad_in}" if bad_in else ""))


# ---------------------------------------------------------------- 5. reading file shape
def words(text):
    return len(re.sub(r"```.*?```", " ", text, flags=re.S).split())


print(f"     word count: reading file {words(short)} (code blocks removed; {len(short.split())} with code); "
      f"question file {len(qtext.split())}; lesson text {len(lesson_text.split()) if HAVE_LESSON else 'n/a'}")
check(1800 <= words(short) <= 3000, f"reading file prose within 1,800-3,000 words ({words(short)})")
check(short.startswith("<!-- kit:reading concept=I6 depth=short version=1 -->"), "reading file header line")
check(all(h in short for h in ("**What this is:**", "**What this is not:**", "## Check yourself")),
      "reading file has What this is / is not and Check yourself (FORMAT §3)")
check("> **Read in the book:** Ch11 p.1/13, p.6–11/13 (per 04; not re-opened in the build session)" in short,
      "the book box names Ch11 p.1/13, p.6-11/13, per 04, not re-opened (spec §5)")
STEP_WORDS = {1: ("questions", "statements"), 2: ("index time", "query time"), 3: ("one call", "n questions"),
              4: ("clean", "own chunk"), 5: ("three designs", "parent"), 6: ("unique parents",), 7: ("span", "never the question"),
              8: ("keyword", "number"), 9: ("leakage",), 10: ("costs", "hyde"), 11: ("repo",)}
titles = [t for t, _ in short_heads]
numbered = [t for t in titles if re.match(r"\d+\.", t)]
check([int(t.split(".")[0]) for t in numbered] == list(range(1, 13)), f"sections ## 1. ... ## 12. in order ({len(numbered)})")
check(len(numbered) >= 11 and all(all(w in numbered[s - 1].lower() for w in ws) for s, ws in STEP_WORDS.items()),
      "sections 1-11 follow the lesson's steps 1-11 (each title names its step)")
check(len(numbered) == 12 and numbered[11] == "12. When not to use it" and titles[-1] == "Check yourself",
      "section 12 is 'When not to use it' (step 12), then 'Check yourself'")
secs = {int(s.split(".")[0]): s for s in re.split(r"^## ", short, flags=re.M)[1:] if re.match(r"\d+\.", s)}
beats = {b: sum(b in s for s in secs.values()) for b in ("**The answer first:**", "**The result", "**What this means.**", "**For your project:**")}
check(beats["**The answer first:**"] == 12 and beats["**The result"] >= 8 and beats["**What this means.**"] >= 8 and beats["**For your project:**"] >= 9,
      f"house-style beats: answer first in all 12 sections; result / what this means / for your project {list(beats.values())[1:]}")
check("(../questions/I6_questions.md)" in short and "study/questions/I6_questions.md" in short.split("## Check yourself")[1],
      "Check yourself names and links the question file")
counts = re.search(r"(\d+) cold questions before reading, (\d+) after, (\d+) for a later review, and (\d+) interview", short)
check(bool(counts) and tuple(map(int, counts.groups())) == (cnt("pre"), cnt("main"), cnt("review"), cnt("interview")),
      "Check yourself states the right item counts per set")
LABELS = {  # label: alternatives, each a tuple of words that must all appear
    "stand-in pack": [("stand-in",)], "written by Claude helpers": [("Claude helpers",)],
    "blind to the eval set": [("never saw the eval set",), ("blind to the eval set",)],
    "seeds LLM-drafted, not human-verified": [("LLM-drafted", "not human-verified")],
    "book pages per 04, not re-opened": [("per 04", "not re-opened")],
    "MiniLM rebuilt from an ONNX export, parity checked against P4": [("ONNX", "P4")]}
for nm, t in (("reading file", short), ("question file", qtext)):
    miss = [k for k, alts in LABELS.items() if not any(all(w in t for w in ws) for ws in alts)]
    check(not miss, f"{nm} carries the spec §10 labels" + (f"; missing {miss}" if miss else ""))

# ---------------------------------------------------------------- 6. book pages (book not in the build container)
TOK = re.compile(r"[a-z0-9]+")


def toks(t):
    t = t.lower().replace("\u2019", "").replace("'", "").replace("\u2018", "")
    return TOK.findall(t)


def text_lines(text, drop=lambda ln: False):
    tk_all, line_of = [], []
    for ln, line in enumerate(text.splitlines(), 1):
        if drop(line):
            continue
        t = toks(line)
        tk_all += t
        line_of += [ln] * len(t)
    return tk_all, line_of


def shared_runs(tk_all, line_of, grams):
    for nn in range(15, 5, -1):
        found = [i for i in range(len(tk_all) - nn + 1) if hash(tuple(tk_all[i:i + nn])) in grams[nn]]
        if found:
            return nn, (sorted({line_of[i] for i in found}) if nn == 15 else [])
    return 0, []


quote_line = lambda line: bool(re.match(r'^>\s*"', line))          # the verbatim interview quotes (MIT, checked in step 1)
FILES = [("question file", qtext), ("reading file", short)] + ([("lesson text", lesson_text)] if HAVE_LESSON else [])
cites = set()
for _, text in FILES:
    for m in re.finditer(r"\b(Ch\d+|App|Intro) p\.(\d+)(?:–(\d+))?/(\d+)", text):
        for p in range(int(m.group(2)), int(m.group(3) or m.group(2)) + 1):
            cites.add((m.group(1), p, int(m.group(4))))
    for m in re.finditer(r"\b(Ch\d+) p\.\d+(?:–\d+)?/\d+, p\.(\d+)(?:–(\d+))?/(\d+)", text):
        for p in range(int(m.group(2)), int(m.group(3) or m.group(2)) + 1):
            cites.add((m.group(1), p, int(m.group(4))))
check(cites and all(c[0] == "Ch11" and c[2] == 13 and 1 <= c[1] <= 13 for c in cites),
      f"{len(cites)} distinct book pages cited, all in Ch11 of 13 pages: {sorted(p for _, p, _ in cites)}")
if not BOOK.is_dir():
    skipped(f"book folder {BOOK.name} not found under ROOT: page-exists and phrase checks run on Yash's machine")
    skipped("whole-book 15-word overlap check runs on Yash's machine")
else:
    docs = {}
    for f in sorted(glob.glob(str(BOOK / "*.pdf"))):
        stem = Path(f).stem
        key = "App" if stem == "Appendix" else ("Ch" + stem.split()[-1] if stem.startswith("chapter") else stem)
        docs[key] = [pg.get_text() for pg in pymupdf.open(f)]
    badc = [c for c in sorted(cites) if c[0] not in docs or len(docs[c[0]]) != c[2] or not 1 <= c[1] <= c[2]]
    check(not badc, f"{len(cites)} distinct book pages cited; each exists with the right page count" + (f"; bad: {badc}" if badc else ""))
    if HAVE_LESSON:
        badl = [(c, p) for c, p in re.findall(r'data-book="([^"]+)" data-page="(\d+)"', raw_html)
                if ("Ch" + c.split()[-1].replace(".pdf", "")) not in docs or not 1 <= int(p) <= len(docs["Ch" + c.split()[-1].replace(".pdf", "")])]
        check(not badl, "every data-book link in the lesson opens an existing page" + (f"; bad {badl}" if badl else ""))
    flat = lambda ch, pages: " ".join(" ".join(toks(docs[ch][p - 1])) for p in pages)
    PHRASES = [  # (chapter, pages, a word the per-04 page notes rely on) -- 04's notes, never re-opened in the build session
        ("Ch11", [1], "question"), ("Ch11", [6], "question"), ("Ch11", [8], "question"), ("Ch11", [9, 10], "hyde"), ("Ch11", [11], "question"),
    ]
    miss = [f"{c} p.{pp}" for c, pp, ph in PHRASES if c in docs and " ".join(toks(ph)) not in flat(c, pp)]
    check(not miss, f"{len(PHRASES)} words of 04's page notes found on the cited pages (in memory)" + (f"; missing on {miss}" if miss else ""))
    bgrams = {nn: set() for nn in range(6, 16)}
    book_tokens = [toks(pg) for pages in docs.values() for pg in pages]
    for tk in book_tokens:
        for nn in bgrams:
            for i in range(len(tk) - nn + 1):
                bgrams[nn].add(hash(tuple(tk[i:i + nn])))
    print(f"     book: {len(book_tokens)} pages, {sum(map(len, book_tokens)):,} words (held in memory only)")
    for name, text in FILES:
        longest, hits = shared_runs(*text_lines(text, quote_line), bgrams)
        check(not hits, f"{name}: no 15-word run shared with the book (longest shared run: {longest or '<6'} words)" + (f"; lines {hits[:10]}" if hits else ""))

# ---------------------------------------------------------------- 7. 15-word overlap with the climate PDF and the upstream code
src_pages = [pg.get_text() for pg in pymupdf.open(PDF)]
nb_files = sorted((RT / "all_rag_techniques").glob("*.ipynb"))
for nb in nb_files:
    cells = json.loads(nb.read_text(encoding="utf-8")).get("cells", [])
    for c in cells:
        src_pages.append("".join(c.get("source", [])))
        for o in c.get("outputs", []):
            src_pages.append("".join(o.get("text", [])) + "".join(o.get("data", {}).get("text/plain", [])))
py_files = [RT / "helper_functions.py"] + sorted((RT / "all_rag_techniques_runnable_scripts").glob("*.py"))
src_pages += [p.read_text(encoding="utf-8", errors="ignore") for p in py_files if p.exists()]
grams = {nn: set() for nn in range(6, 16)}
for tk in map(toks, src_pages):
    for nn in grams:
        for i in range(len(tk) - nn + 1):
            grams[nn].add(hash(tuple(tk[i:i + nn])))
print(f"     sources: the climate PDF ({len(pymupdf.open(PDF))} pages), {len(nb_files)} notebooks, {len(py_files)} scripts (held in memory only)")
for name, text in FILES:
    longest, hits = shared_runs(*text_lines(text, quote_line), grams)
    check(not hits, f"{name}: no 15-word run shared with the climate PDF or the upstream notebooks/scripts "
          f"(longest shared run: {longest or '<6'} words)" + (f"; lines {hits[:10]}" if hits else ""))

# ---------------------------------------------------------------- 8. numbers are traceable
outs = {"out_i6_kit_measure": ko, "I6_FACTS": facts}
OPTIONAL = {  # outputs of the parallel I6 pieces (spec §1); used for the lesson's counts only when they exist (as P4 did)
    "verify notebook run": HERE / "out_i6_verify_nb_run.txt", "tool test": HERE / "out_i6_tool_test.txt",
    "tool example report": WS / "study" / "tools" / "examples" / "climate_i6_report.md"}
lesson_extra = {k: p.read_text(encoding="utf-8") for k, p in OPTIONAL.items() if p.exists()}
print(f"     number sources: out_i6_kit_measure.txt, I6_FACTS.md; for the lesson also: {sorted(lesson_extra) or 'none yet'}")
NUM = re.compile(r"(?<![\w.,/])(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?![\w/])")
pool = set()
for t in outs.values():
    for m in re.finditer(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?", t):
        pool.add(m.group(0).replace(",", ""))
pool_f = [float(s) for s in pool]
pool_l = set(pool)
for t in lesson_extra.values():
    for m in re.finditer(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?", t):
        pool_l.add(m.group(0).replace(",", ""))
pool_lf = [float(s) for s in pool_l]
EXTERNAL = {  # I6_BUILD_SPEC §7: dated research facts (phase_04_indexing.md, Concept I6 §5, sources read 2026-10-17)
    "21.8": "doc2query MRR@10 [I6-S1]", "18.6": "BM25 MRR@10", "61": "doc2query ms", "55": "BM25 ms", "36.8": "re-ranking leaderboard",
    "27.2": "docTTTTTquery MRR@10 [I6-S2]", "64": "docTTTTTquery ms", "27.7": "best non-BERT", "80": "samples per passage",
    "40": "first 40 used / upstream 'at least 40'", "20": "about $20", "70": "Doc2Query-- 70th percentile [I6-S3]", "16": "Doc2Query-- 16% (UNVERIFIED)",
    "30": "30% faster (UNVERIFIED)", "48": "48% smaller (UNVERIFIED)", "42": "HyPE 'up to 42' pp (claimed) [I6-S4]", "45": "HyPE 'up to 45' pp",
    "8000": "Groq TPM (plan UNVERIFIED)", "200000": "Groq TPD", "0.075": "Groq input $/M", "0.30": "Groq output $/M",
    "0.10": "Haiku input $/M", "0.50": "Haiku output $/M",
}
DERIVED = {  # arithmetic shown next to each in the text, or an item's own made-up data
    # I6-A-02's toy table (made-up scores) and its sums: X 0.64 + 0.58 = 1.22; Y 0.78 + 0.40 = 1.18; Z 0.71 + 0.69 + 0.67 + 0.62 = 2.69
    "0.78": "A-02 toy", "0.71": "A-02 toy", "0.69": "A-02 toy", "0.67": "A-02 toy", "0.64": "A-02 toy", "0.62": "A-02 toy",
    "0.58": "A-02 toy", "0.40": "A-02 toy", "1.22": "A-02 sum X", "1.18": "A-02 sum Y", "2.69": "A-02 sum Z",
    "6144": "1,536 x 4 bytes per vector (A-01 Hint 3)",
    "0.736": "1 - 0.264 (A-06)", "67": "91 - 24 (A-06)", "74": "0.736 as a percentage, rounded (A-06)",
    "50": "T-03's own data (50 queries a day); also K5's 50 of 91",
}
NUMFILES = [("question file", qtext), ("reading file", short)]
unmatched_md, unmatched_lesson = {}, {}
for name, text in FILES:
    text = "\n".join(l for l in text.splitlines() if not quote_line(l))                       # verbatim repo quotes (step 1)
    text = re.sub(r"\]\([^)]*\)", "]", text)                                                 # link targets
    text = re.sub(r"\b(Ch\d+|App|Intro) p\.\d+(?:–\d+)?/\d+", " ", text)                     # book pages
    text = re.sub(r"\bp\.\d+(?:–\d+)?/\d+", " ", text)
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b|\b(?:19|20)\d\d\b", " ", text)                     # dates, years
    text = re.sub(r"\b\d+\.\d+\.\d+\b", " ", text)                                           # versions
    text = re.sub(r"\b[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9.]+)+\b|§[\d.]+|\b[SKQEDOCMRIPXVAH]\d+\b|#\d+|e080df2|cells? \d+(?:, \d+)*(?: and \d+)?|L\d+(?:–L\d+)?|question \d+", " ", text)
    text = re.sub(r"\b\d+(?:st|nd|th)\b|\b\d+-d\b|\b\d+×|\b\d+ × \d+(?: = [\d,]+)?|\bv\d(?:\.\d)?\b", " ", text)
    for m in NUM.finditer(text):
        s = m.group(0).replace(",", "")
        x = float(s)
        if "." not in s and x < 10:
            continue
        if s in EXTERNAL or s in DERIVED:
            continue
        d = len(s.split(".")[1]) if "." in s else 0
        P, PF = (pool_l, pool_lf) if name == "lesson text" else (pool, pool_f)
        ok = (s in P or any(abs(y - x) <= 0.5 * 10 ** -d + 1e-12 for y in PF)) if d else s in P
        if not ok:
            (unmatched_lesson if name == "lesson text" else unmatched_md).setdefault(m.group(0), set()).add(name)
check(not unmatched_md, "question + reading files: every decimal and every integer >= 10 matches a value printed in out_i6_kit_measure.txt "
      "or I6_FACTS.md, or the EXTERNAL / DERIVED list" + (f"; unmatched: {unmatched_md}" if unmatched_md else ""))
if HAVE_LESSON:
    check(not unmatched_lesson, "lesson text: every decimal and every integer >= 10 is traceable the same way"
          + (f"; unmatched: {unmatched_lesson}" if unmatched_lesson else ""))
else:
    pending("lesson text number check waits for the lesson")
KEY = ["0.708", "0.781", "0.653", "0.547", "0.9869", "0.886", "0.777", "0.264", "0.7054", "0.7939", "0.5351", "582", "485",
       "3,575,808", "596,096", "4,271", "42.5%", "0.0061", "0.0148", "194", "627.9", "671.0"]
miss_out = [k for k in KEY if not (k in ko or k.replace(",", "") in ko or k in facts)]
check(not miss_out, f"{len(KEY)} spec §8 key numbers are printed by the measurement (or written in I6_FACTS)" + (f"; missing {miss_out}" if miss_out else ""))
miss_md = [k for k in KEY if not any(k in t for _, t in FILES)]
check(not miss_md, "each key number is quoted in the lesson, reading or question file" + (f"; not quoted: {miss_md}" if miss_md else ""))
keynums = set()
for q in qs:
    for line in q["answer"]["keys"] + q["answer"]["four"]:
        keynums |= {m for m in re.findall(r"\d+\.\d+|\d{1,3}(?:,\d{3})+|\b\d{2,}\b", line)}
keynums -= set(DERIVED) | {"0.71", "0.64", "1,536"}
miss_kn = sorted(k for k in keynums if k not in short)
check(not miss_kn, f"every number in a key point or 'for a 4' point ({len(keynums)}) also appears in the reading file"
      + (f"; missing {miss_kn}" if miss_kn else ""))

# ---------------------------------------------------------------- 9. banned phrases, model identifiers
BANNED = ["a guide says", "well above zero", "narrow positive band", "who is right", "sixth", "add a pdf", "adding a document",
          "new document", "another pdf", "tenant", "300 pdf"]
hits = {nm: [w for w in BANNED if w in t.lower()] for nm, t in FILES}
check(not any(hits.values()), f"none of the {len(BANNED)} spec §9 banned phrases appears ({hits})")
MODEL_ID = re.compile(r"claude-(?:opus|sonnet|haiku|instant|\d)[\w.-]*|\b(?:opus|sonnet|haiku)[ -]?\d", re.I)
own_files = FILES + [("this check script", Path(__file__).read_text(encoding="utf-8").replace(MODEL_ID.pattern, ""))]
mid = {nm: MODEL_ID.findall(t) for nm, t in own_files}
check(not any(mid.values()), f"no Claude model identifier strings in the files ({ {k: v for k, v in mid.items() if v} or 'none' })")

# ---------------------------------------------------------------- 10. the kit's own format check
r = subprocess.run([sys.executable, str(WS / "study" / "quiz.py"), "--check"], capture_output=True, text=True, encoding="utf-8", cwd=str(WS))
line = next((l for l in r.stdout.splitlines() if "I6_questions.md" in l), "")
print("     quiz.py --check: " + " | ".join(l.strip() for l in r.stdout.splitlines() if l.strip()))
check(line.strip().startswith("OK") and "17 questions" in line, f"study/quiz.py --check passes for I6 ({line.strip()})")
check(r.returncode == 0, f"study/quiz.py --check exits 0 for all files (exit {r.returncode})")

print(f"\n{n - fails}/{n} checks passed; {fails} failed; {pend} PENDING; {skip} SKIPPED")
print("ALL PASS" + (" (except PENDING/SKIPPED)" if pend or skip else "") if fails == 0 else f"{fails} FAIL(S)")
sys.exit(0 if fails == 0 else 1)
