"""I5: check the two study-kit Markdown files of 2026-10-18 (question file and short reading file).

1. study/questions/I5_questions.md loads with the kit's own parser and passes kit.lint_questions; the 19 ids of the
   build spec (I5_BUILD_SPEC.md §4), in their sets and types; FORMAT field rules (hints 1-2, Hint 3 only on A items,
   2-5 keys, 1-2 'for a 4', 1-3 wrong answers, one short question sentence); at most 2 external items; the
   interview item I5-R-07 is verbatim (repo heading of Q17), carries the MIT notice, its quoted repo paragraphs are
   exact substrings of the pinned repo file, the repo's answer comes before our check, and our check adds the
   Corpus D finding (title constant: 1 distinct header of 97; the heading rule matters: chunk 68).
   The data inside the A items is recomputed (A-01 truncation, A-02 cost, A-04 change, A-06 share) or matched to the
   measured output (A-03 Paris paths, A-05 chunk 68 paths).
2. Every reread line links into the reading file AND the HTML lesson and names a book page 'Ch7 p.x/11'; each
   item's reread names the reading section(s) AND the lesson step id(s) that the build spec says teach it.
3. Every relative link and #anchor in both files resolves (GitHub rule for .md; id="..." attributes for .html). If
   the lesson does not exist yet, its link checks are reported as PENDING (counted as skipped). Also every link from
   any other workspace .md file INTO these two files.
4. The reading file's shape (FORMAT §3, build spec §3/§5): header line, title, What this is / is not, the book box,
   the 13 numbered headings exactly as the spec, then 'Check yourself' linking the question file with the right
   counts; 1,800-3,000 words of prose (code blocks removed); house-style beats; the MiniLM rule (no MiniLM number
   for the header arms; 'run the verify notebook').
5. Book checks (each cited page exists; 15-word copyright) only if <Book RAG>/RAG_Made_Simple_The_Complete_Visual_Guide
   exists; otherwise SKIPPED with the reason. The form of every book cite (Ch7 p.x/11) is checked either way.
6. Copyright against the AIQ repo file: no run of 15 consecutive words outside the marked verbatim quotes (the
   '> "..."' lines, the quoted question line and the notice) is shared with the pinned file.
7. Numbers: every decimal and every integer >= 10 in the two files matches a number in out_i5_kit_measure.txt or
   I5_FACTS.md, or is on the EXTERNAL / DERIVED list below (each with its source). Verbatim repo quotes are checked
   in step 1 instead.
8. The coach-banned phrases of the build spec §0.5 are absent from both files.
9. `uv run python study/quiz.py --check` passes for I5_questions.md.
Run from rag_learning/ (the "Book RAG" folder is optional; default: the workspace's parent):
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I5/i5_md_check.py ["C:/Yash/New-Work/Book RAG"] \
        > sources/verification/I5/out_i5_md_check.txt
"""
import glob
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

WS = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else WS.parent
BOOK = ROOT / "RAG_Made_Simple_The_Complete_Visual_Guide"
QF = WS / "study" / "questions" / "I5_questions.md"
SHORT = WS / "study" / "reading" / "I5_contextual_headers.md"
LESSON = WS / "study" / "lessons" / "I5_contextual_headers.html"
AIQ = ROOT / "upstream" / "AI-Engineer-Interview-Questions"
AIQ_FILE = AIQ / "04-rag-and-retrieval" / "questions.md"
n = fails = skips = 0


def check(ok, label):
    global fails, n
    n += 1
    fails += not ok
    print(("PASS " if ok else "FAIL ") + label)


def skip(label, reason):
    global skips, n
    n += 1
    skips += 1
    print(f"SKIPPED {label}: {reason}")


# ---------------------------------------------------------------- 1. question file
sys.path.insert(0, str(WS / "study"))
import kit  # noqa: E402

qs = kit.parse_questions(QF)
qtext_all = QF.read_text(encoding="utf-8")
short = SHORT.read_text(encoding="utf-8")
ko = (HERE / "out_i5_kit_measure.txt").read_text(encoding="utf-8")
facts = (HERE / "I5_FACTS.md").read_text(encoding="utf-8")
problems = kit.lint_questions(QF)
check(not problems, f"kit.lint_questions: {problems or 'no problems'}")
check(qtext_all.startswith("<!-- kit:questions concept=I5 version=1 -->\n"
                           "# I5 questions: contextual chunk headers and contextual retrieval\n"),
      "question file header line and title (spec §4)")
ids = [q["id"] for q in qs]
qd = {q["id"]: q for q in qs}
SPEC = {  # id: (type, set, taught-in steps) from the build spec §4
    "I5-PRE-01": ("R", "pre", [1]), "I5-PRE-02": ("R", "pre", [6]),
    "I5-R-01": ("R", "main", [1]), "I5-R-02": ("R", "main", [6]), "I5-R-03": ("R", "main", [2]),
    "I5-R-04": ("R", "main", [2]), "I5-R-05": ("R", "main", [12]), "I5-R-06": ("R", "main", [11]),
    "I5-A-01": ("A", "main", [8]), "I5-A-02": ("A", "main", [10, 11]), "I5-A-03": ("A", "main", [4]),
    "I5-A-04": ("A", "main", [12, 9]), "I5-A-05": ("A", "main", [5]), "I5-A-06": ("A", "review", [7]),
    "I5-T-01": ("T", "main", [7, 9]), "I5-T-02": ("T", "main", [11]), "I5-T-03": ("T", "main", [10]),
    "I5-T-04": ("T", "main", [9]),
    "I5-R-07": ("R", "interview", [1, 6, 10]),
}
STEP_ID = {1: "anon", 2: "fields", 3: "tree", 4: "path", 5: "assign", 6: "info", 7: "dilute", 8: "trunc",
           9: "measure", 10: "llm", 11: "cache", 12: "claims"}
check(sorted(ids) == sorted(SPEC) and len(ids) == 19, f"the 19 ids of the build spec, no more, no less ({len(ids)})")
check(len(set(ids)) == len(ids), "ids unique")
check(all(qd[i]["type"] == t and qd[i]["set"] == s for i, (t, s, _) in SPEC.items() if i in qd),
      "each id has the spec's type and set (pre/main/review/interview)")
check(all(re.fullmatch(r"I5-(PRE|[RAT])-\d\d", i) for i in ids), "ids follow I5-<type>-<nn> / I5-PRE-<nn>")
check(all(q["id"].split("-")[1] == q["type"] or q["id"].startswith("I5-PRE") for q in qs), "id letter = type")
check(ids[:2] == ["I5-PRE-01", "I5-PRE-02"] and [i for i in ids if "PRE" in i] == ids[:2],
      "the 2 set=pre items come first, in order")
by = defaultdict(list)
for q in qs:
    by[(q["set"], q["type"])].append(q["id"])
cnt = lambda s, t=None: sum(len(v) for (ss, tt), v in by.items() if ss == s and (t is None or tt == t))
print(f"     items: {len(qs)}; pre {cnt('pre')} (R {cnt('pre', 'R')}); main {cnt('main')} (R {cnt('main', 'R')}, "
      f"A {cnt('main', 'A')}, T {cnt('main', 'T')}); review {cnt('review')} (A {cnt('review', 'A')}); "
      f"interview {cnt('interview')} (R {cnt('interview', 'R')})")
for q in qs:
    check(len(q["hints"]) >= 2 and 2 <= len(q["answer"]["keys"]) <= 5 and 1 <= len(q["answer"]["four"]) <= 2
          and 1 <= len(q["answer"]["wrong"]) <= 3, f"{q['id']}: 2+ hints, 2-5 keys ({len(q['answer']['keys'])}), "
          f"1-2 'for a 4' ({len(q['answer']['four'])}), 1-3 wrong answers ({len(q['answer']['wrong'])})")
    if len(q["hints"]) == 3:
        check(q["type"] == "A", f"{q['id']}: Hint 3 only on an A item")
    first = q["question"].splitlines()[0]
    if q["set"] != "interview":
        ends = len(re.findall(r"[.?!]\"?(?:\s|$)", first))
        check(ends == 1 and first.rstrip().endswith(("?", ".")) and len(first.split()) <= 45,
              f"{q['id']}: one short question sentence ({len(first.split())} words), data after it")
check(all(len(q["hints"]) == 3 for q in qs if q["type"] == "A"), "every A item has a Hint 3 (worked step)")
check(sum(1 for q in qs if q["source"]) <= 2 and [q["id"] for q in qs if q["source"]] == ["I5-R-07"],
      f"at most 2 external items; only I5-R-07 is external ({sum(1 for q in qs if q['source'])})")
INTERVIEW = {"I5-R-07": ("AIQ-04-Q17", "04-rag-and-retrieval/questions.md", 17)}
VERB_Q = "Explain contextual retrieval. What problem does it solve, and how does late chunking relate?"
NOTICE = ("*From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md` "
          "(question 17), Copyright (c) 2026 Om, MIT License.*")
quotes_all = []
for qid, (src, relp, num) in INTERVIEW.items():
    q = qd[qid]
    repo = (AIQ / relp).read_text(encoding="utf-8")
    check(q["source"] == src and q["set"] == "interview" and q["type"] == "R", f"{qid}: set=interview, source={src}")
    lines = q["question"].splitlines()
    check(lines[0] == f'"{VERB_Q}"' and lines[1] == NOTICE,
          f"{qid}: the question field is the spec's verbatim question, then the spec's MIT notice line")
    check(f"### {num}. {VERB_Q}" in repo, f"{qid}: the quoted question is verbatim in the repo (heading of Q{num})")
    pre = q["answer"]["preamble"]
    quotes = [l[l.index('"') + 1:l.rindex('"')] for l in pre.splitlines() if re.match(r'^>\s*"', l)]
    quotes_all += quotes
    q17 = repo[repo.index(f"### {num}."):repo.index(f"### {num + 1}.")]
    check(len(quotes) >= 2 and all(x in q17 for x in quotes) and "Copyright (c) 2026 Om, MIT License" in pre,
          f"{qid}: the {len(quotes)} quoted repo paragraphs ({sum(len(x.split()) for x in quotes)} words) are exact "
          f"substrings of Q{num} in the pinned file, with the MIT notice")
    check("unconditionally" in " ".join(quotes), f"{qid}: the quote includes the 'unconditionally' recommendation our check corrects")
    check(pre.index("The repo's answer") < pre.index("Our check of that answer") and bool(q["answer"]["model"]),
          f"{qid}: the repo's answer comes first, then our check, then **Model answer:**")
    ours = pre[pre.index("Our check of that answer"):]
    check("1 distinct title header of 97" in ours and "chunk 68" in ours and "84 of 97" in ours
          and "Chapter 15" in ours and "Chapter 16" in ours,
          f"{qid}: our check adds the Corpus D finding (title constant 1 of 97; heading rule matters on chunk 68)")
print("     note: the interview question is verbatim; the one-sentence rule is not applied to it")

# the data inside the A items
paths = dict(re.findall(r"Paris Agreement heading (p\.\d+) path: (.+)", ko))
m03 = qd["I5-A-03"]["answer"]["model"]
check(all(re.search(rf"^{re.escape(p)}\s+{re.escape(v)}\s*$", m03, re.M) for p, v in paths.items()) and len(paths) == 2,
      "I5-A-03: both Paris paths in the answer equal K3's measured paths")
check(all(re.search(rf"^{re.escape(p)}\s+{re.escape(v)}\s*$", short, re.M) for p, v in paths.items()),
      "reading §4: both Paris paths equal K3's measured paths")
c68 = re.search(r"chunk 68 p\.23 \[50756,51413\) start: (.+)\n\s+majority: (.+)", ko)
m05 = qd["I5-A-05"]["answer"]["model"]
check(c68 and f"Understanding Climate Change › {c68.group(1)}" in m05 and f"Understanding Climate Change › {c68.group(2)}" in m05,
      "I5-A-05: start and majority paths of chunk 68 equal K4")
c34 = re.search(r"chunk 34 p\.12 \[25535,26463\) start: (.+)\n\s+majority: (.+)", ko)
check(c34 and "Blockchain for Climate Action" in c34.group(1) and "Integrated Climate Policies" in c34.group(2)
      and "Blockchain for Climate Action" in short and "Integrated Climate Policies" in short
      and "chunk 34" in qd["I5-A-05"]["answer"]["four"][0],
      "chunk 34 counter-case (K4): start names blockchain, majority does not; taught in the reading and in I5-A-05's 'for a 4'")
check(182 + 27 == 209 and 182 + 100 - 256 == 26 and "209 ≤ 256" in qd["I5-A-01"]["answer"]["model"]
      and "over by 26" in qd["I5-A-01"]["answer"]["model"] and "182 + 100 = 282 -> over by 26" in ko,
      "I5-A-01: 209 fits, 282 is over by 26 (recomputed; equals K6)")
D, nn, cp, o, pin, pout = 12840, 97, 250, 200, 0.10, 0.50
unc = nn * (D + cp) * pin / 1e6 + nn * o * pout / 1e6
cac = D * pin * 1.25 / 1e6 + (nn - 1) * D * pin * 0.1 / 1e6 + nn * cp * pin / 1e6 + nn * o * pout / 1e6
m02 = qd["I5-A-02"]["answer"]["model"]
check(f"${unc:.4f}" in m02 and f"${cac:.4f}" in m02 and f"{unc / cac:.1f}×" in m02
      and f"uncached USD {unc:.4f}; cached (write 1.25x once, read 0.1x) USD {cac:.4f}; ratio {unc / cac:.1f}x" in ko,
      f"I5-A-02: cost recomputed (uncached ${unc:.4f}, cached ${cac:.4f}, {unc / cac:.1f}x) and equal to K11")
check(f"{(3.7 - 5.7) / 5.7 * 100:.1f}%" == "-35.1%" and "−35.1%" in qd["I5-A-04"]["answer"]["model"]
      and "absolute -2.0 points, relative -35.1%" in ko, "I5-A-04: −2.0 points / −35.1% recomputed and equal to K15")
check(f"{19 / 170:.3f}" == "0.112" and f"{19 / 83:.3f}" == "0.229" and "0.112" in qd["I5-A-06"]["answer"]["model"]
      and "0.229" in qd["I5-A-06"]["answer"]["model"] and "s = 0.229" in ko, "I5-A-06: s = 0.112 / 0.229 recomputed and equal to K6")

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
    text = Path(path).read_text(encoding="utf-8")
    if Path(path).suffix == ".html":
        return set(re.findall(r'\bid="([^"$]+)"', text))
    return {a for _, _, a in headings(path)} | set(re.findall(r'<a id="([^"]+)"', text))


short_heads = [(t, a) for lvl, t, a in headings(SHORT) if lvl == 2]
step_anchor = {int(re.match(r"(\d+)\.", t).group(1)): a for t, a in short_heads if re.match(r"\d+\.", t)}
for q in qs:
    rr = q["answer"]["reread"]
    ok = ("../reading/I5_contextual_headers.md#" in rr and "../lessons/I5_contextual_headers.html#" in rr
          and re.search(r"book Ch7 p\.\d+(?:–\d+)?/11", rr))
    check(bool(ok), f"{q['id']}: reread links to the reading file AND the lesson, plus a book page Ch7 p.x/11")
    steps = SPEC[q["id"]][2]
    linked = re.findall(r"\.\./reading/I5_contextual_headers\.md#([\w-]+)", rr)
    lesson_ids = re.findall(r"\.\./lessons/I5_contextual_headers\.html#([\w-]+)", rr)
    check(all(step_anchor.get(s) in linked for s in steps) and all(STEP_ID[s] in lesson_ids for s in steps),
          f"{q['id']}: reread names the reading section(s) and lesson step(s) the spec says teach it (§{steps})")


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
    bad, pending, links = [], [], links_in(text)
    for href in links:
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        target, _, anc = href.partition("#")
        tp = (Path(path).parent / target).resolve() if target else Path(path)
        if tp == LESSON.resolve() and not tp.exists():
            pending.append(href)
        elif not tp.exists():
            bad.append(f"missing file {href}")
        elif anc and tp.suffix in (".md", ".html") and anc not in anchors(tp):
            bad.append(f"missing anchor {href}")
    return links, bad, pending


for name, path in (("question file", QF), ("reading file", SHORT)):
    links, bad, pending = bad_links(path, Path(path).read_text(encoding="utf-8"))
    anc_links = [h for h in links if "#" in h and not h.startswith("http")]
    html_links = [h for h in links if ".html" in h]
    if pending:
        skip(f"{name}: {len(pending)} links into the HTML lesson", "PENDING: study/lessons/I5_contextual_headers.html "
             "does not exist yet (written in parallel); rerun when it does")
    check(not bad, f"{name}: {len(links) - len(pending)} links resolve ({len(anc_links)} with #anchors; "
          f"{len(html_links)} into the lesson, checked against its id=\"...\" attributes)" + ("" if not bad else ": " + "; ".join(bad[:8])))
if LESSON.exists():
    lids = anchors(LESSON)
    miss_ids = [i for i in STEP_ID.values() if i not in lids]
    check(not miss_ids, f"the lesson has the 12 step ids of spec §3 ({', '.join(STEP_ID.values())})"
          + (f"; missing {miss_ids}" if miss_ids else ""))
else:
    skip("the lesson's 12 step ids", "PENDING: the lesson file does not exist yet")
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
check(not bad_in, f"{inbound} links from other workspace .md files into the two I5 kit files resolve" + (f": {bad_in}" if bad_in else ""))


# ---------------------------------------------------------------- 4. reading file shape and length
def words(text, strip_code=False):
    if strip_code:
        text = re.sub(r"```.*?```", " ", text, flags=re.S)
    return len(text.split())


print(f"     word count: reading file {words(short)} (prose only, code blocks removed: {words(short, True)}); "
      f"question file {words(qtext_all)}")
check(1800 <= words(short, True) <= 3000, f"reading file prose within 1,800-3,000 words ({words(short, True)})")
check(short.startswith("<!-- kit:reading concept=I5 depth=short version=1 -->\n"
                       "# I5: Contextual chunk headers and contextual retrieval\n"), "reading file header line and title (spec §5)")
check(all(h in short for h in ("**What this is:**", "**What this is not:**", "## Check yourself")),
      "reading file has What this is / is not and Check yourself (FORMAT §3)")
check("> **Read in the book:** Ch7 p.1–2/11, then p.4–9/11. Read after §2." in short, "book box as the spec gives it")
SPEC_HEADS = ["1. A chunk loses its context", "2. Where the header goes: embed_text, not text",
              "3. Get the headings from the PDF", "4. The path, not the leaf", "5. Which heading a chunk gets",
              "6. The information test: a constant title adds nothing", "7. Dilution and the header magnet",
              "8. Truncation: the tail is cut", "9. Measuring it on your questions",
              "10. LLM-written contexts and the cost ladder", "11. Prompt caching, cache keys and wrong contexts",
              "12. Reading the vendor numbers", "13. When not to use it", "Check yourself"]
SPEC_ANCH = ["1-a-chunk-loses-its-context", "2-where-the-header-goes-embed_text-not-text", "3-get-the-headings-from-the-pdf",
             "4-the-path-not-the-leaf", "5-which-heading-a-chunk-gets", "6-the-information-test-a-constant-title-adds-nothing",
             "7-dilution-and-the-header-magnet", "8-truncation-the-tail-is-cut", "9-measuring-it-on-your-questions",
             "10-llm-written-contexts-and-the-cost-ladder", "11-prompt-caching-cache-keys-and-wrong-contexts",
             "12-reading-the-vendor-numbers", "13-when-not-to-use-it"]
check([t for t, _ in short_heads] == SPEC_HEADS, "the ## headings are exactly the spec's 1-13 + Check yourself, in order")
check([a for _, a in short_heads][:13] == SPEC_ANCH, "their GitHub anchors equal the spec's §3 anchor list")
bodies = re.split(r"^## ", short, flags=re.M)[1:]
beats = {b: sum(1 for s in bodies[:12] if re.search(p, s)) for b, p in
         (("setup", r"\*\*The setup\.\*\*"), ("result", r"\*\*The result\b"), ("means", r"\*\*What this means\.\*\*"),
          ("project", r"\*\*For your project:\*\*"))}
check(all(v == 12 for v in beats.values()), f"house style: sections 1-12 each have setup / result / what this means / for your project ({beats})")
check(len(re.findall(r"\*\*The tempting wrong idea:\*\*", short)) >= 3, "the tempting wrong idea vs the right one, at least 3 times")
check("(../questions/I5_questions.md)" in short, "Check yourself links the question file")
counts = re.search(r"(\d+) cold questions before reading, (\d+) after, (\d+) for a later review, and (\d+) interview", short)
check(counts and tuple(map(int, counts.groups())) == (cnt("pre"), cnt("main"), cnt("review"), cnt("interview")),
      "Check yourself states the right item counts per set")
both = qtext_all + "\n" + short
mini = [l for l in both.splitlines() if re.search(r"margin|Kendall|τ", l) and re.search(r"\b0\.\d+|[+−-]\d\.\d+", l)
        and "half-width" not in l]
check("SKIPPED" in ko.split("=== K16")[1] and "run the verify notebook" in short and not mini,
      "MiniLM rule: K16 was skipped, the reading says 'run the verify notebook', and no margin/τ number is stated"
      + (f"; lines {mini[:3]}" if mini else ""))

# ---------------------------------------------------------------- 5. book pages and copyright (book needed)
cites = set()
for text in (qtext_all, short):
    for m in re.finditer(r"\b(Ch\d+|App|Intro) p\.(\d+)(?:–(\d+))?/(\d+)", text):
        for p in range(int(m.group(2)), int(m.group(3) or m.group(2)) + 1):
            cites.add((m.group(1), p, int(m.group(4))))
    for m in re.finditer(r"\b(Ch\d+) p\.\d+(?:–\d+)?/\d+(?:,| and| then) p\.(\d+)(?:–(\d+))?/(\d+)", text):
        for p in range(int(m.group(2)), int(m.group(3) or m.group(2)) + 1):
            cites.add((m.group(1), p, int(m.group(4))))
SPEC_PAGES = {1, 2, 4, 5, 6, 7, 8, 9}     # spec §0.3: p.1-2, 4, 4-7, 7, 8, 8-9 of Ch7 (11 pages)
check(all(c[0] == "Ch7" and c[2] == 11 and c[1] in SPEC_PAGES for c in cites) and cites,
      f"{len(cites)} distinct book pages cited, all Ch7 p.x/11 within the spec's page list {sorted(SPEC_PAGES)}")
TOK = re.compile(r"[a-z0-9]+")


def toks(t):
    t = t.lower().replace("\u2019", "").replace("'", "").replace("\u2018", "")
    return TOK.findall(t)


def shared_runs(text, grams, n_=15):
    tk_all, line_of = [], []
    for ln, line in enumerate(text.splitlines(), 1):
        t = toks(line)
        tk_all += t
        line_of += [ln] * len(t)
    hits, longest = [], 0
    for k in range(n_, 5, -1):
        found = [i for i in range(len(tk_all) - k + 1) if hash(tuple(tk_all[i:i + k])) in grams[k]]
        if found:
            longest = k
            if k == n_:
                hits = sorted({line_of[i] for i in found})
            break
    return hits, longest


def gram_sets(token_lists):
    g = {k: set() for k in range(6, 16)}
    for tk in token_lists:
        for k in g:
            for i in range(len(tk) - k + 1):
                g[k].add(hash(tuple(tk[i:i + k])))
    return g


if BOOK.exists():
    import pymupdf
    docs = {}
    for f in sorted(glob.glob(str(BOOK / "*.pdf"))):
        stem = Path(f).stem
        key = "App" if stem == "Appendix" else ("Ch" + stem.split()[-1] if stem.startswith("chapter") else stem)
        docs[key] = [pg.get_text() for pg in pymupdf.open(f)]
    badc = [c for c in sorted(cites) if c[0] not in docs or len(docs[c[0]]) != c[2] or not 1 <= c[1] <= c[2]]
    check(not badc, f"each cited book page exists with the right page count" + (f"; bad: {badc}" if badc else ""))
    bg = gram_sets([toks(pg) for pages in docs.values() for pg in pages])
    for name, path in (("question file", QF), ("reading file", SHORT)):
        hits, longest = shared_runs(Path(path).read_text(encoding="utf-8"), bg)
        check(not hits, f"{name}: no 15-word run shared with the book (longest: {longest or '<6'} words)"
              + (f"; lines {hits[:10]}" if hits else ""))
else:
    reason = f"book folder not present ({BOOK}); Ch7 pages are UNVERIFIED in this session (I5_FACTS §2)"
    skip("each cited book page exists with the right page count", reason)
    skip("question file: no 15-word run shared with the book", reason)
    skip("reading file: no 15-word run shared with the book", reason)

# ---------------------------------------------------------------- 6. 15-word overlap with the AIQ file (outside marked quotes)
aiq = AIQ_FILE.read_text(encoding="utf-8")
ag = gram_sets([toks(aiq)])


def unquoted(text):
    out = []
    for l in text.splitlines():
        if re.match(r'^>\s*"', l) or l.startswith("*From ombharatiya/") or l.startswith("> **The repo's answer"):
            continue
        l = l.replace(f'"{VERB_Q}"', " ")
        out.append(l)
    return "\n".join(out)


for name, path in (("question file", QF), ("reading file", SHORT)):
    hits, longest = shared_runs(unquoted(Path(path).read_text(encoding="utf-8")), ag)
    check(not hits, f"{name}: outside the marked verbatim quotes, no 15-word run shared with the AIQ file "
          f"(longest: {longest or '<6'} words)" + (f"; lines {hits[:10]}" if hits else ""))

# ---------------------------------------------------------------- 7. numbers are traceable
NUM = re.compile(r"(?<![\w.,/])(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?![\w/])")
pool = set()
for t in (ko, facts):
    for m in re.finditer(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?", t):
        pool.add(m.group(0).replace(",", ""))
pool_f = [float(s) for s in pool]
EXTERNAL = {  # not printed by our scripts; each with its source
    "0.10": "Haiku 5.5 input price, study/tools/examples/prices_2026-10-17.json",
    "0.50": "Haiku 5.5 output price, study/tools/examples/prices_2026-10-17.json",
}
DERIVED = {  # arithmetic shown next to each in the text, or the item's own data
    "0.1270": "I5-A-02: 97 x 13,090 x 0.10 / 10^6 (shown)", "0.0097": "I5-A-02: 97 x 200 x 0.50 / 10^6 (shown)",
    "0.0016": "I5-A-02: 12,840 x 0.10 x 1.25 / 10^6 (shown)", "0.0123": "I5-A-02: 96 x 12,840 x 0.10 x 0.1 / 10^6 (shown)",
    "0.0024": "I5-A-02: 97 x 250 x 0.10 / 10^6 (shown)", "0.0137": "I5-A-02 wrong answer: 0.1 x 0.1367 (shown)",
    "170": "I5-A-06: 19 + 151 (shown)", "83": "I5-A-06: 19 + 64 (shown)", "0.126": "I5-A-06 wrong answer: 19 / 151 (shown)",
    "0.02": "I5-A-04: 2.0 points as a fraction (shown)", "0.11": "I5-A-03: 0.112 rounded (K6)",
    "20": "I5-T-04's own data (+20 points); recall@20 / top 20 (Anthropic's k, I5_FACTS §2)",
    "35": "'35%' / '35 points': Anthropic's relative figure rounded (K15 -35.1%)",
    "49": "'49%': AIQ's ~49% (K15 -49.1%)", "67": "'67%': AIQ's ~67% (K15 -66.7%)",
}
unmatched = {}
for name, path in (("question file", QF), ("reading file", SHORT)):
    text = Path(path).read_text(encoding="utf-8")
    text = "\n".join(l for l in text.splitlines() if not re.match(r'^>\s*"', l))           # verbatim repo quotes (step 1)
    text = re.sub(r"\]\([^)]*\)", "]", text)                                                 # link targets
    text = re.sub(r"\b(Ch\d+|App) p\.\d+(?:–\d+)?/\d+", " ", text)                           # book pages
    text = re.sub(r"\bp\.\d+(?:–\d+)?/\d+", " ", text)
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b|\b(?:19|20)\d\d\b", " ", text)                     # dates, years
    text = re.sub(r"\b\d+\.\d+\.\d+\b", " ", text)                                           # versions
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
check(not unmatched, "every decimal and every integer >= 10 matches a number in out_i5_kit_measure.txt or I5_FACTS.md, "
      f"or the EXTERNAL ({len(EXTERNAL)}) / DERIVED ({len(DERIVED)}) list" + (f"; unmatched: {unmatched}" if unmatched else ""))
KEY = ["31 of 97", "46 of 97", "0 of 97", "94 of 97", "84 of 97", "0.68", "257", "0.8565", "0.106", "0.112", "0.229",
       "209", "282", "29 of 97", "0.938", "0.124", "0.0124", "13,090", "0.1367", "0.0261", "96 of 97", "3,412",
       "35.1%", "49.1%", "66.7%", "87.15", "4.72", "0.92206234"]
miss_out = [k for k in KEY if not any(k in t or k.replace(",", "") in t for t in (ko, facts))]
check(not miss_out, f"{len(KEY)} key numbers of spec §3 are printed by i5_kit_measure.py or listed in I5_FACTS"
      + (f"; missing {miss_out}" if miss_out else ""))
miss_md = [k for k in KEY if k not in short]
check(not miss_md, "each key number is quoted in the reading file" + (f"; not quoted: {miss_md}" if miss_md else ""))

# ---------------------------------------------------------------- 8. coach-banned phrases (build spec §0.5)
BANNED = ["share of queries", "fraction of queries", "a guide says", "sixth", "add a pdf", "adding a document",
          "new document", "another pdf", "tenant", "300 pdf", "without reading", "half noise", "0.729", "three stages"]
hits = {p.name: [w for w in BANNED if w in p.read_text(encoding="utf-8").lower()] for p in (QF, SHORT)}
check(not any(hits.values()), f"none of the {len(BANNED)} coach-banned phrases appears ({hits})")

# ---------------------------------------------------------------- 9. the kit's own format check
r = subprocess.run([sys.executable, str(WS / "study" / "quiz.py"), "--check"], capture_output=True, text=True,
                   encoding="utf-8", cwd=str(WS))
line = next((l for l in r.stdout.splitlines() if "I5_questions.md" in l), "")
print("     quiz.py --check: " + " | ".join(l.strip() for l in r.stdout.splitlines() if l.strip()))
check(line.strip().startswith("OK") and "19 questions" in line, f"study/quiz.py --check passes for I5 ({line.strip()})")
check(r.returncode == 0, f"study/quiz.py --check exits 0 for all files (exit {r.returncode})")

print(f"\n{n} checks: {n - fails - skips} passed / {fails} failed / {skips} skipped")
print(("ALL PASS" if fails == 0 else f"{fails} FAIL(S)") + (f" ({skips} skipped, reasons above)" if skips else ""))
