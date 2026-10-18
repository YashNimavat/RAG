"""P4: check the study-kit files of 2026-10-18 (question file, short reading file, and the HTML lesson's text).

1. study/questions/P4_questions.md loads with the kit's own parser and passes kit.lint_questions; the 21 ids of the
   research plan (phase_01_prerequisites.md, Concept P4 §3), in their sets and types; FORMAT field rules (2 hints,
   Hint 3 only on A items, 2-5 key points, 1-2 'for a 4', 1-3 wrong answers); at most 2 external items; the interview
   item P4-R-08 quotes AIQ-04 Q15 verbatim with the MIT notice, its quoted paragraphs are exact substrings of the
   pinned repo file, and the repo's answer comes before ours; the tutor-reserved Q11 is not used.
2. Every reread line links into the short reading file and names a book page; each item's reread names the reading
   section(s) the plan says teaches it.
3. Every relative link in the two Markdown files resolves, with its #anchor (GitHub rule); links from other
   workspace .md files into them resolve too.
4. The reading file's shape (FORMAT §3): header, What this is / is not, the book box, sections 1-13 in the lesson's
   step order, then 'Check yourself'; 'The answer first' in every numbered section 1-12.
5. Book pages: every 'ChN p.x/y' / 'App p.x/y' cited in the three files exists (y = the file's page count); short
   phrases the paraphrases rely on are on the cited pages (checked in memory, never printed).
6. Copyright: no run of 15 consecutive words is shared with ANY page of the book (in memory; reported by line only).
7. Numbers: every decimal, and every integer >= 10, in the three files matches a value printed by p4_measure.py or
   p4_kit_measure.py or written in P4_FACTS, or is on the EXTERNAL (dated research facts) / DERIVED list below.
8. The coach-banned phrases (seed S2 and S3 wording) are absent from the three files.
9. `uv run python study/quiz.py --check` passes.
Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P4/p4_md_check.py "C:/Yash/New-Work/Book RAG" \
        > sources/verification/P4/out_p4_md_check.txt
"""
import glob
import html
import re
import subprocess
import sys
from pathlib import Path

import pymupdf

ROOT = Path(sys.argv[1])
WS = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BOOK = ROOT / "RAG_Made_Simple_The_Complete_Visual_Guide"
QF = WS / "study" / "questions" / "P4_questions.md"
SHORT = WS / "study" / "reading" / "P4_embeddings.md"
LESSON = WS / "study" / "lessons" / "P4_embeddings.html"
AIQ = ROOT / "upstream" / "AI-Engineer-Interview-Questions" / "04-rag-and-retrieval" / "questions.md"
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
raw_html = LESSON.read_text(encoding="utf-8")
main_html = raw_html.split('<main id="main">', 1)[1].split("</main>", 1)[0]
lesson_text = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<svg.*?</svg>", " ", main_html, flags=re.S)))
problems = kit.lint_questions(QF)
check(not problems, f"kit.lint_questions: {problems or 'no problems'}")
check(qtext.startswith("<!-- kit:questions concept=P4 version=1 -->"), "question file header line")
SPEC = {  # id: (set, reading sections that teach it) from the research plan §3 (Short §)
    "P4-PRE-01": ("pre", [2]), "P4-PRE-02": ("pre", [4]), "P4-PRE-03": ("pre", [3]),
    "P4-R-01": ("main", [2]), "P4-R-02": ("main", [4]), "P4-R-03": ("main", [8]), "P4-R-04": ("main", [7]),
    "P4-R-05": ("main", [3]), "P4-R-06": ("main", [4, 5]), "P4-R-07": ("main", [5]), "P4-R-08": ("interview", [7]),
    "P4-A-01": ("main", [2]), "P4-A-02": ("main", [2, 3]), "P4-A-03": ("main", [1]), "P4-A-04": ("main", [3]),
    "P4-A-05": ("main", [6]), "P4-A-06": ("main", [10]), "P4-A-07": ("main", [11]),
    "P4-T-01": ("main", [3, 5]), "P4-T-02": ("main", [11]), "P4-T-03": ("main", [10]),
}
ids = [q["id"] for q in qs]
qd = {q["id"]: q for q in qs}
check(sorted(ids) == sorted(SPEC) and len(ids) == 21, f"the 21 ids of the plan, no more, no less ({len(ids)})")
check(len(set(ids)) == len(ids), "ids unique")
check(all(qd[i]["set"] == s for i, (s, _) in SPEC.items() if i in qd), "each id is in the plan's set")
check(all(q["id"].split("-")[1] == q["type"] or q["id"].startswith("P4-PRE") for q in qs), "id letter = type")
check(ids[:3] == ["P4-PRE-01", "P4-PRE-02", "P4-PRE-03"], "the 3 set=pre items come first, in order")
blocks = re.findall(r"<!-- q (.*?) -->(.*?)<!-- /q -->", qtext, re.S)
hint_ok = all(("<summary>Hint 1</summary>" in b and "<summary>Hint 2</summary>" in b)
              and ("<summary>Hint 3</summary>" not in b or "type=A" in h) for h, b in blocks)
check(hint_ok and len(blocks) == 21, "every item has Hint 1 and Hint 2; Hint 3 only on A items")
check(all(2 <= len(q["answer"]["keys"]) <= 5 for q in qs), "2-5 key points per item")
check(all(1 <= len(q["answer"]["four"]) <= 2 for q in qs), "1-2 'for a 4' points per item")
check(all(1 <= len(q["answer"]["wrong"]) <= 3 for q in qs), "1-3 common wrong answers per item")
check(sum(1 for q in qs if q.get("source")) <= 2, f"at most 2 external items ({sum(1 for q in qs if q.get('source'))})")
aiq = AIQ.read_text(encoding="utf-8")
heading = "Many embedding models tell you to prefix queries and documents differently, or to pass a task instruction. Why, and what goes wrong if you ignore it?"
r08 = qd["P4-R-08"]
check(f"### 15. {heading}" in aiq and heading in r08["question"], "P4-R-08 quotes the repo's Q15 heading verbatim")
check("Copyright (c) 2026 Om, MIT License" in r08["question"] and "e080df2" in r08["question"] and qd["P4-R-08"].get("source") == "AIQ-04-Q15",
      "P4-R-08 carries the MIT notice, the pinned commit and source=AIQ-04-Q15")
quoted = re.findall(r"^> (.+)$", blocks[ids.index("P4-R-08")][1], re.M)
check(len(quoted) >= 2 and all(p in aiq for p in quoted), f"P4-R-08: the {len(quoted)} quoted paragraphs are exact substrings of the repo file")
b08 = blocks[ids.index("P4-R-08")][1]
check(b08.find("> Because retrieval") < b08.find("**Model answer:**"), "P4-R-08: the repo's answer comes before ours")
check("Q11" not in qtext and "AIQ-04-Q11" not in qtext, "the tutor-reserved AIQ-04 Q11 is not used")

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


short_heads = [(t, a) for lvl, t, a in headings(SHORT) if lvl == 2]
step_anchor = {int(re.match(r"(\d+)\.", t).group(1)): a for t, a in short_heads if re.match(r"\d+\.", t)}
bad_rr, miss_steps = [], []
for q in qs:
    rr = q["answer"]["reread"]
    if not ("../reading/P4_embeddings.md#" in rr and re.search(r"book (Ch\d+|App) p\.\d", rr)):
        bad_rr.append(q["id"])
    linked = re.findall(r"\.\./reading/P4_embeddings\.md#([\w-]+)", rr)
    if not all(step_anchor.get(s) in linked for s in SPEC[q["id"]][1]):
        miss_steps.append(q["id"])
check(not bad_rr, f"every reread links the short reading file and names a book page ({bad_rr or 'all 21'})")
check(not miss_steps, f"every reread names the reading section(s) the plan says teach it ({miss_steps or 'all 21'})")


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
    check(not bad, f"{name}: {len(links)} links resolve ({sum('#' in h for h in links)} with #anchors)" + ("" if not bad else ": " + "; ".join(bad[:8])))
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
check(not bad_in, f"{inbound} links from other workspace files into the two P4 kit files resolve" + (f": {bad_in}" if bad_in else ""))
kit_paths = re.findall(r'data-path="rag_learning/([^"]+)"', raw_html)
missing_kit = [p for p in kit_paths if not (WS / p).exists()]
check(not missing_kit, f"the lesson's {len(kit_paths)} study-kit file links point at existing files" + (f": {missing_kit}" if missing_kit else ""))

# ---------------------------------------------------------------- 4. reading file shape


def words(text):
    return len(re.sub(r"```.*?```", " ", text, flags=re.S).split())


print(f"     word count: reading file {words(short)} (code blocks removed); question file {len(qtext.split())}; lesson text {len(lesson_text.split())}")
check(1800 <= words(short) <= 3600, f"reading file prose about 1,800-3,000 words, allowing 20% over for the measured tables ({words(short)})")
check(short.startswith("<!-- kit:reading concept=P4 depth=short version=1 -->"), "reading file header line")
check(all(h in short for h in ("**What this is:**", "**What this is not:**", "> **Read in the book:**", "## Check yourself")),
      "reading file has What this is / is not, the book box and Check yourself (FORMAT §3)")
STEP_WORDS = {1: ("bugs",), 2: ("arrow",), 3: ("normalise", "direction"), 4: ("one score",), 5: ("closeness",), 6: ("limit",),
              7: ("label",), 8: ("bi-encoder", "cross-encoder"), 9: ("probability",), 10: ("smaller",), 11: ("choosing", "cost"),
              12: ("defaults", "checks")}
titles = [t for t, _ in short_heads]
numbered = [t for t in titles if re.match(r"\d+\.", t)]
check([int(t.split(".")[0]) for t in numbered] == list(range(1, 14)), f"sections ## 1. ... ## 13. in order ({len(numbered)})")
check(all(all(w in numbered[s - 1].lower() for w in ws) for s, ws in STEP_WORDS.items()), "sections 1-12 follow the lesson's step order")
check(numbered[12].lower().startswith("13. when not") and titles[-1] == "Check yourself", "section 13 is 'When not to ...', then 'Check yourself'")
secs = re.split(r"^## ", short, flags=re.M)[1:]
check(sum("**The answer first:**" in s for s in secs if re.match(r"\d+\.", s) and int(s.split(".")[0]) <= 11) == 11,
      "sections 1-11 each open with 'The answer first' (12 is the defaults table)")
check("study/questions/P4_questions.md" in short, "Check yourself names the question file")

# ---------------------------------------------------------------- 5. book pages and phrases
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
for text in (qtext, short, lesson_text):
    for m in re.finditer(r"\b(Ch\d+|App) p\.(\d+)(?:–(\d+))?/(\d+)", text):
        for p in range(int(m.group(2)), int(m.group(3) or m.group(2)) + 1):
            cites.add((m.group(1), p, int(m.group(4))))
    for m in re.finditer(r"\b(Ch\d+) p\.\d+(?:–\d+)?/\d+ and p\.(\d+)(?:–(\d+))?/(\d+)", text):
        for p in range(int(m.group(2)), int(m.group(3) or m.group(2)) + 1):
            cites.add((m.group(1), p, int(m.group(4))))
badc = [c for c in sorted(cites) if c[0] not in docs or len(docs[c[0]]) != c[2] or not 1 <= c[1] <= c[2]]
check(not badc, f"{len(cites)} distinct book pages cited; each exists with the right page count" + (f"; bad: {badc}" if badc else ""))
for chap, page in re.findall(r'data-book="([^"]+)" data-page="(\d+)"', raw_html):
    key = "App" if chap == "Appendix.pdf" else "Ch" + chap.split()[-1].replace(".pdf", "")
    if key not in docs or not 1 <= int(page) <= len(docs[key]):
        badc.append((chap, page))
check(not badc, "every data-book link in the lesson opens an existing page")
flat = lambda ch, p: " ".join(toks(docs[ch][p - 1]))
PHRASES = [  # (chapter, page, a few words the paraphrase relies on; each < 15 words)
    ("Ch1", 5, "list of numbers"), ("Ch1", 6, "carbon dioxide"), ("Ch1", 6, "faiss"), ("Ch1", 8, "same"),
    ("Ch6", 1, "question"), ("Ch12", 8, "cosine"), ("Ch13", 6, "bi encoder"), ("Ch13", 6, "cross encoder"),
    ("Ch13", 9, "milliseconds"), ("App", 15, "cosine similarity"), ("App", 15, "standard"), ("App", 16, "embedding"),
    ("App", 14, "cosine"), ("App", 13, "asymmetry"),
]
miss = [f"{c} p.{p}" for c, p, ph in PHRASES if " ".join(toks(ph)) not in flat(c, p)]
check(not miss, f"{len(PHRASES)} short phrases found on the cited pages (checked in memory)" + (f"; missing on {miss}" if miss else ""))
ch1 = " ".join(" ".join(toks(p)) for p in docs["Ch1"])
check("cosine" not in ch1, "Ch1 never says 'cosine' (the lesson's book check)")

# ---------------------------------------------------------------- 6. 15-word overlap with the book (in memory only)
book_tokens = [toks(pg) for pages in docs.values() for pg in pages]
grams = {nn: set() for nn in range(6, 16)}
for tk in book_tokens:
    for nn in grams:
        for i in range(len(tk) - nn + 1):
            grams[nn].add(hash(tuple(tk[i:i + nn])))
print(f"     book: {len(book_tokens)} pages, {sum(map(len, book_tokens)):,} words (held in memory only)")
for name, text in (("question file", qtext), ("reading file", short), ("lesson text", lesson_text)):
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
outs = {"p4_measure": (HERE / "out_p4_measure.txt").read_text(encoding="utf-8"),
        "p4_kit_measure": (HERE / "out_p4_kit_measure.txt").read_text(encoding="utf-8"),
        "P4_FACTS": (HERE / "P4_FACTS.md").read_text(encoding="utf-8"),
        "embed_fit_check example": (WS / "study" / "tools" / "examples" / "climate_embed_report.md").read_text(encoding="utf-8"),
        "verify notebook run": (HERE / "out_p4_verify_nb_run.txt").read_text(encoding="utf-8")}
NUM = re.compile(r"(?<![\w.,/])(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?![\w/])")
pool = set()
for t in outs.values():
    for m in re.finditer(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?", t):
        pool.add(m.group(0).replace(",", ""))
pool_f = [float(s) for s in pool]
EXTERNAL = {  # research phase_01 Concept P4 §1/§5 (sources read 2026-10-17) and the local MiniLM model card
    "65": "SBERT: about 65 hours [P4-1]", "1024": "MiniLM card: batch 1,024 [P4-16]", "1536": "Cohere default dimension [P4-7]",
    "58": "MTEB datasets [P4-3]", "112": "MTEB languages", "500": "MMTEB tasks [P4-4]", "560": "MMTEB best public model, 560M",
    "14": "MRL up to 14x [P4-5]", "96": "Cohere texts per call [P4-7]", "78.1": "DPR NQ top-20 dot [P4-2]", "76.1": "DPR NQ top-20 L2",
    "19": "DPR beats BM25 by 9-19 points", "0.12": "third-party Cohere price (UNVERIFIED) [P4-12]", "512": "Cohere output_dimension option",
    "10000": "SBERT: 10,000 sentences", "1000000": "a million chunks (formula example)", "10000000": "slider maximum",
}
DERIVED = {  # arithmetic shown next to each in the text, or the item's own toy data
    "0.434": "1 - 0.8/1.4142 (shown)", "0.4343": "same, 4 decimals", "0.3675": "1 - 0.8944/1.4142 (converter)", "0.8944": "sqrt(0.8) (shown)",
    "0.293": "1 - 1/sqrt(2) (shown)", "1.4142": "sqrt(2)", "2.8284": "2 x 1.4142 (wrong-answer arithmetic)", "104.17": "10,000 / 96 (shown)",
    "0.30": "2.5 x 0.12 (shown)", "12.3": "12.288 rounded", "4.4": "4.38 rounded", "4.1": "4.12 rounded", "0.333": "1/3 (shown)",
    "0.3333": "1/3", "0.03": "0.0289 rounded", "0.25": "0.2500 rounded", "1.83": "1.8284 rounded", "11.06": "11.056 rounded", "3.27": "3.272 rounded",
    "2.05": "2.048730 rounded", "3.27 ": "", "2.36": "2.363580 rounded", "3.47": "3.474059 rounded", "6144": "1536 x 4 (shown)",
    "0.8": "2 - 2 x 0.6 (shown)", "0.6": "the item's data", "20": "the item's toy data (dot 20)", "25": "toy arithmetic 9 + 16",
    "16": "toy arithmetic 8 x 2", "18": "toy dot 18", "250": "the item's data (250 tokens per chunk)", "2500000": "10,000 x 250 (shown)",
    "300": "the item's / S7 token position", "280": "the item's data (token 280)", "400": "S7 passage tokens", "3600": "-",
    "12.288": "2M x 1536 x 4 (shown)", "3.072": "2M x 1536 (shown)", "0.384": "2M x 1536 / 8 (shown)", "2.048": "2M x 256 x 4 (shown)",
    "105": "ceil(10,000/96) (shown)", "2000000": "the item's data", "0.39": "0.3917 rounded", "0.98": "0.9759, 0.9820 rounded / dup threshold",
    "0.83": "0.8343 rounded", "0.9": "a recommendation threshold", "0.771": "0.7707 rounded", "0.869": "0.8690 rounded", "0.511": "0.5108 rounded",
    "0.642": "0.6417 rounded", "0.326": "0.3256 rounded", "0.484": "0.4842 rounded", "0.207": "0.2069 rounded", "0.404": "0.4035 rounded",
    "1.000": "unit length", "100": "S3: 100 questions", "0.0": "max difference 0.0", "0.5": "a threshold in the text", "0.7": "a value in a wrong idea",
    "0.75": "chart tick", "24": "-", "1.5": "toy playground length", "2.4": "toy playground length", "55": "toy angle", "45": "toy angle", "53": "slider default",
    "60": "chord angle", "80": "0.8 as a percentage (a wrong idea)", "104": "10,000 / 96 = 104.17 (shown)", "2000": "2,000,000 (the item's data)", "2.40": "toy playground length readout", "30": "notebook runtime, rounded up from the run log", "256128": "the CLI argument --dims 256,128", "90": "chord angle", "180": "chord angle", "4.375": "-", "4.125": "-", "11": "1 + 10 passes (shown)", "51": "1 + 50",
}
unmatched = {}
for name, text in (("question file", qtext), ("reading file", short), ("lesson text", lesson_text)):
    text = "\n".join(l for l in text.splitlines() if not l.startswith("> "))                  # verbatim repo quotes (step 1)
    text = re.sub(r"\]\([^)]*\)", "]", text)
    text = re.sub(r"\b(Ch\d+|App) p\.\d+(?:–\d+)?/\d+", " ", text)
    text = re.sub(r"\bp\.\d+(?:–\d+)?/\d+", " ", text)
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b|\b(?:19|20)\d\d\b", " ", text)                     # dates, years
    text = re.sub(r"\b\d+\.\d+\.\d+\b", " ", text)                                           # versions
    text = re.sub(r"\b[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9.]+)+\b|§[\d.]+|\b[SKQEDOCMRIPXV]\d+\b|#\d+|e080df2|1110a243\S*|cells? \d+(?:, \d+)*(?: and \d+)?|L\d+", " ", text)
    text = re.sub(r"\b\d+(?:st|nd|th)\b|\b\d+-d\b|\b\d+×|\b\d+ × \d+(?: = [\d,]+)?|\bv\d(?:\.\d)?\b", " ", text)
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
check(not unmatched, "every decimal and every integer >= 10 matches a printed value (p4_measure, p4_kit_measure, P4_FACTS) "
      "or the EXTERNAL / DERIVED list" + (f"; unmatched: {unmatched}" if unmatched else ""))
KEY = ["0.708", "0.4606", "0.4386", "0.4775", "0.8436", "0.5196", "0.019276", "0.284787", "2.1719", "-0.5357",
       "-1.4737", "0.358", "0.750", "0.583", "0.760", "0.8590", "0.3906", "0.2903", "7.0697", "-4.361", "-3.321", "0.82"]
miss_out = [k for k in KEY if not any(k in t for t in outs.values())]
check(not miss_out, f"{len(KEY)} key numbers are printed by the measurement scripts" + (f"; missing {miss_out}" if miss_out else ""))
norm_minus = lambda t: t.replace("−", "-")
miss_md = [k for k in KEY if not any(k.lstrip("-") in norm_minus(t) for t in (qtext, short, lesson_text))]
check(not miss_md, "each key number is quoted in the lesson, reading or question file" + (f"; not quoted: {miss_md}" if miss_md else ""))

# ---------------------------------------------------------------- 8. coach-banned phrases
BANNED = ["a guide says", "well above zero", "narrow positive band", "who is right", "sixth", "add a pdf", "adding a document",
          "new document", "another pdf", "tenant", "300 pdf"]
hits = {nm: [w for w in BANNED if w in t.lower()] for nm, t in (("questions", qtext), ("reading", short), ("lesson", lesson_text))}
check(not any(hits.values()), f"none of the {len(BANNED)} coach-banned phrases appears ({hits})")

# ---------------------------------------------------------------- 9. the kit's own format check
r = subprocess.run([sys.executable, str(WS / "study" / "quiz.py"), "--check"], capture_output=True, text=True, encoding="utf-8", cwd=str(WS))
line = next((l for l in r.stdout.splitlines() if "P4_questions.md" in l), "")
check(line.strip().startswith("OK") and "21 questions" in line, f"study/quiz.py --check passes for P4 ({line.strip()})")
check(r.returncode == 0, f"study/quiz.py --check exits 0 for all files (exit {r.returncode})")

print(f"\n{n - fails}/{n} checks passed")
sys.exit(0 if fails == 0 else 1)
