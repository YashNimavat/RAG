"""Test study/tools/structure_fit_check.py against I2_FACTS (Corpus D) and a synthetic zoo of small PDFs.

1. Corpus D vs I2_FACTS: snapshot, fonts and body size (S1-S3), heading counts size only vs size + bold (S4), alignment
   (S5-S6), repeated titles and section lengths (S7), page-break failures (S8), chunk arms (S9), balanced split (S10),
   invariants (S11), the inspection sample (S13), the seed buckets (S14), the checklist and the recommendation.
2. Chunk for chunk: the tool's headings and chunks equal i2_structure.py's (the reference) for v0, L2, L3, L4 and
   L4 + merge; the tool is standalone (it does not import i2_structure).
3. The zoo: small PDFs made with PyMuPDF in a temp folder, one rule each: bold body-size headings, a wrapped heading,
   a running header on every page (and one with a page number), two-column pages (across the columns and column by
   column), an outline via set_toc (matching and not matching), image-only pages (one, and all), numbered headings
   (levels that disagree and agree), a bold lead-in and a bold full sentence inside paragraphs, a ruled table, blank pages.
   Each asserts the checklist verdicts and the recommendation.
4. Rules in isolation: alignment fails closed, the recommendation rule order, an eval item that crosses a page, an eval
   set over two PDFs (matched by doc_id).
5. CLI: the example report and inspection sheet byte for byte, a second run byte-identical, --json, --help, a path in
   the Windows "Book RAG/upstream/..." layout (with a space), exit 2 and a clear message for each bad input; the tool
   imports no network client and hard-codes no path.

No API calls, no network. Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I2/i2_tool_test.py ["<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"]
    (or set RAG_PDF). Saved output: sources/verification/I2/out_i2_tool_test.txt
"""
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]                                           # rag_learning/
TOOL = WS / "study" / "tools" / "structure_fit_check.py"
EX = WS / "study" / "tools" / "examples"
SEEDS = EX / "climate_seed_spans.jsonl"
D_SHA = "1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669"
_default = WS.parent / "upstream" / "RAG_Techniques" / "data" / "Understanding_Climate_Change.pdf"
PDF = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("RAG_PDF") or _default)
sys.path.insert(0, str(TOOL.parent))
sys.path.insert(0, str(HERE))
import structure_fit_check as sf                               # noqa: E402
import i2_structure as S                                       # noqa: E402

RESULTS = []


def same(got, exp, tol):
    if isinstance(exp, (list, tuple)):
        return isinstance(got, (list, tuple)) and len(got) == len(exp) and all(same(g, e, tol) for g, e in zip(got, exp))
    if exp is None or isinstance(exp, (str, bool, dict)) or got is None:
        return got == exp
    return abs(float(got) - float(exp)) <= tol


def check(name, got, exp, tol=0.0):
    ok = same(got, exp, tol)
    RESULTS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}: got {got!r} | expected {exp!r}")
    return ok


def raises(fn, exc):
    try:
        fn()
    except exc:
        return True
    except Exception:  # noqa: BLE001
        return False
    return False


def verdicts(r):
    return " ".join(f"{x['id']} {x['verdict']}" for x in r["checklist"])


def V(r, cid):
    return next(x["verdict"] for x in r["checklist"] if x["id"] == cid)


def arm(r, name):
    s = r["arms"][name]
    return [s["n"], s["min"], s["median"], s["max"], s["mean"], s["multi_page"], s["hist"]]


TMP = Path(tempfile.mkdtemp(prefix="i2tool_"))
if hashlib.sha256(PDF.read_bytes()).hexdigest() != D_SHA:
    print(f"FAIL  the PDF is not Corpus D (sha256 differs): {PDF.name}")
    sys.exit(1)
DDIR = TMP / "Book RAG" / "upstream" / "RAG_Techniques" / "data"     # the Windows layout, with a space in it
DDIR.mkdir(parents=True)
DPDF = DDIR / "Understanding_Climate_Change.pdf"
shutil.copyfile(PDF, DPDF)

# ---------------------------------------------------------------- 1 Corpus D vs I2_FACTS
print("=== 1 Corpus D vs I2_FACTS")
res = sf.run_check([DPDF], cap=1000, split_level="auto", min_chars=400, sample=10, seed=0, evalset=SEEDS, doc_ids=["climate"])
r = res["files"][0]
check("1 S1 pages, doc_text characters, snapshot_id", [r["pages"], r["chars"], r["snapshot_id"]], [33, 72593, "ea07572562ac"])
check("1 S1 no outline; tagged (StructTreeRoot, Marked true); creator", [r["toc"], r["tagged"], r["marked"], r["creator"]], [[], True, True, "Microsoft® Word 2021"])
check("1 S3 font histogram (size, bold, characters)", [(f["size"], f["bold"], f["chars"]) for f in r["fonts"]],
      [(24.0, True, 28), (18.0, True, 855), (13.56, True, 1666), (12.0, True, 4057), (12.0, False, 63762), (11.04, False, 0)])
check("1 S3 body size 12.0; spans per size", [r["body"], r["spans_by_size"]], [12.0, {12.0: 1006, 13.56: 68, 18.0: 22, 24.0: 1}])
check("1 S4 text lines / all-bold lines / bold lines with > 1 span", [r["lines"]["text"], r["lines"]["bold"], r["lines"]["bold_multi_span"]], [1097, 283, 0])
check("1 S4 headings: size only 90 vs size + bold 282", [r["n_heads"]["size"], r["n_heads"]["size+bold"]], [90, 282])
check("1 S4 per level 1/21/68/192 (size only 1/21/68)", [r["levels"]["size+bold"], r["levels"]["size"]], [{1: 1, 2: 21, 3: 68, 4: 192}, {1: 1, 2: 21, 3: 68}])
check("1 S4 size only misses 192 of 282", len(r["missed_by_size"]), 192)
check("1 S4 one wrapped heading joined (p.7 Chapter 5)", [(w["page"], w["title"]) for w in r["wrapped"]],
      [(7, "Chapter 5: The Role of Technology in Climate Change Mitigation")])
check("1 S4 filters remove 0 bold lines; no line repeats on >= 3 pages", [len(r["filtered_long"]), r["repeated_lines"]], [0, []])
check("1 S5 dict lines rebuild get_text() on 33 of 33 pages", [r["rebuild_ok"], r["rebuild_differ"]], [33, []])
check("1 S6 aligned 282 of 282, each on its own page", [r["aligned"], len(r["align_failed"]), r["on_own_page"]], [282, 0, 282])
coal = next(h for h in r["outline"] if h["title"] == "Coal")
check("1 S6 'Coal' L4 p.1 at doc [2418, 2423)", [coal["level"], coal["page"], coal["start"], coal["end"]], [4, 1, 2418, 2423])
check("1 S6 first headings at 0, 30, 467, 1072, 1621, 1658", [h["start"] for h in r["outline"][:6]], [0, 30, 467, 1072, 1621, 1658])
check("1 S7 11 repeated titles (22 headings)", [r["n_repeated_titles"], len(r["repeated_titles"])], [11, 22])
paris = [x["path"][1:] for x in r["repeated_titles"] if x["title"] == "Paris Agreement"]
check("1 S7 Paris Agreement: two different paths", paris,
      [["Chapter 6: Global and Local Climate Action", "International Collaboration", "Paris Agreement"],
       ["Chapter 16: Global Cooperation and Governance", "International Agreements", "Paris Agreement"]])
sec = r["sections"]
check("1 S7 section lengths L2 / L3 / L4 (n, min, median, max, mean)",
      [[sec[k][x] for x in ("n", "min", "median", "max", "mean")] for k in (2, 3, 4)],
      [[21, 1591, 3336, 6058, 3455.4], [68, 549, 1033.5, 1898, 1041.3], [192, 243, 334, 636, 336.5]])
check("1 auto split level = L3 (median 1,033.5 >= 400; L4 334 < 400)", [r["split_level"], r["auto"], r["chosen_arm"]], [3, True, "L3"])
check("1 S8 16 orphaned headings", r["orphans"], ["1->2", "2->3", "3->4", "4->5", "5->6", "6->7", "7->8", "8->9", "10->11", "11->12",
                                                 "17->18", "18->19", "20->21", "27->28", "30->31", "31->32"])
check("1 S8 8 mid-sentence cuts", r["cuts"], ["12->13", "14->15", "15->16", "16->17", "21->22", "22->23", "24->25", "28->29"])
check("1 S8 24 of 32 page breaks do not end in . ! ? : or a quote", r["nonterminal_breaks"], 24)
check("1 S9 v0 per-page 1000/200", arm(r, "v0 per-page 1000/200"), [97, 393, 935, 1000, 857.9, 0, [0, 0, 0, 1, 0, 9, 13, 5, 3, 66]])
check("1 S9 cross-page control", arm(r, "cross-page recursive 1000/200"), [92, 755, 962.5, 999, 954.8, 41, [0, 0, 0, 0, 0, 0, 0, 1, 1, 90]])
check("1 S9 L2: 86 chunks", arm(r, "L2"), [86, 644, 843.5, 1000, 844.1, 29, [0, 0, 0, 0, 0, 0, 9, 27, 17, 33]])
check("1 S9 L3: 117 chunks, 187 / 619 / 997", arm(r, "L3"), [117, 187, 619, 997, 620.5, 27, [0, 1, 0, 18, 16, 18, 29, 15, 6, 14]])
check("1 S9 L4: 209 chunks", arm(r, "L4"), [209, 187, 338, 636, 347.3, 24, [0, 1, 40, 143, 19, 2, 4, 0, 0, 0]])
check("1 S9 L4 + merge<400: 139 chunks, 70 merged", arm(r, "L4 + merge<400") + [r["arms"]["L4 + merge<400"]["merged"]],
      [139, 187, 545, 772, 522.3, 25, [0, 1, 7, 36, 19, 17, 34, 25, 0, 0], 70])
check("1 S9 L3 size-only headings: the same 117 chunks", [arm(r, "L3, size-only headings")[0], r["size_only_same"]], [117, True])
l3 = r["_arms"]["L3"]
check("1 S9 L3 pieces per section: 25 one-piece, 92 in two-piece sections", [sum(c["pieces"] == 1 for c in l3), sum(c["pieces"] == 2 for c in l3)], [25, 92])
d_text = "\n".join(pymupdf.open(DPDF)[i].get_text() for i in range(33))
H = r["_heads"]
us3 = sf.units(d_text, H, 3)
guard = sf.heading_guard(d_text, H)
over = sorted([u for u in us3 if 1000 < u["b"] - u["a"] <= 2000], key=lambda u: u["b"] - u["a"])
check("1 S10 71 L3 units, 46 over the cap", [len(us3), sum(u["b"] - u["a"] > 1000 for u in us3)], [71, 46])
check("1 S10 shortest over the cap: Advocacy and Activism 1,004 -> 341 + 663",
      [over[0]["path"][-1], over[0]["b"] - over[0]["a"], [b - a for a, b in sf.balanced_split(d_text, over[0]["a"], over[0]["b"], 1000, guard)]],
      ["Advocacy and Activism", 1004, [341, 663]])
big = max(us3, key=lambda u: u["b"] - u["a"])
check("1 S10 longest: Greenhouse Gases 1,935 -> 990 + 945",
      [big["path"][-1], big["b"] - big["a"], [b - a for a, b in sf.balanced_split(d_text, big["a"], big["b"], 1000, guard)]],
      ["Greenhouse Gases", 1935, [990, 945]])
check("1 S11 0 invariant violations in every structure arm", {n: sum(v.values()) for n, v in r["invariants"].items()},
      {n: 0 for n in r["invariants"]})
check("1 S11 L3 tiles the document (no overlap)", sum(1 for x, y in zip(l3, l3[1:]) if y["a"] < x["b"]), 0)
check("1 S12 'Coal' + its first body line in one L3 chunk (pages 1-2), not in v0",
      [[(i, [p for p, _, _ in c["page_segments"]]) for i, c in enumerate(l3) if c["a"] <= 2418 and d_text.find("Coal is the most", 2423) + 30 <= c["b"]],
       any(c["a"] <= 2418 and d_text.find("Coal is the most", 2423) + 30 <= c["b"] for c in r["_arms"]["v0 per-page 1000/200"])],
      [[(3, [1, 2])], False])
check("1 page breaks kept whole: v0 0/16 and 0/8, L3 16/16 and 8/8",
      [r["kept_whole"]["v0 per-page 1000/200"], r["kept_whole"]["L3"]], [{"orphans": 0, "cuts": 0}, {"orphans": 16, "cuts": 8}])
smp = r["sample"]
check("1 S13 inspection sample (seed 0): chunks 5, 33, 49, 51, 53, 62, 65, 97, 108, 113", [x["id"] for x in smp], [5, 33, 49, 51, 53, 62, 65, 97, 108, 113])
check("1 S13 10 of 10 start at a heading and end at a sentence", [sum(x["starts_heading"] for x in smp), sum(x["ends_sentence"] for x in smp)], [10, 10])
check("1 S13 pieces 2/2: chunks 65 and 108; across a page break: 51, 62, 97, 108",
      [[x["id"] for x in smp if x["piece"] == 2], [x["id"] for x in smp if len(x["pages"]) > 1]], [[65, 108], [51, 62, 97, 108]])
ev = r["evalset"]
check("1 S14 8 answerable seeds, 2 unanswerable skipped", [len(ev["rows"]), len(ev["unanswerable"])], [8, 2])
check("1 S14 single-segment quotes that match the snapshot: 11 (as in out_i2_measure S14)", ev["quotes_ok"], 11)
check("1 S14 straddles_v0 0 of 8, crosses_page 0 of 8", [sum(x["straddles_v0"] for x in ev["rows"]), sum(x["crosses_page"] for x in ev["rows"])], [0, 0])
check("1 S14 groups per seed (D-005, D-006, D-007 have 2)", [x["groups"] for x in ev["rows"]], [1, 1, 1, 1, 2, 2, 2, 1])
check("1 checklist on D", verdicts(r), "S1 PASS S2 PASS S3 PASS S4 MANUAL S5 MANUAL S6 PASS S7 PASS S8 PASS S9 WARN S10 MANUAL S11 PASS")
rec = r["recommendation"]
check("1 recommendation: typography route at L3", [rec["main"].startswith("Typography route"), "L3" in rec["main"]], [True, True])
check("1 notes: duplicate titles -> section_path / I5; empty boundary bucket", [any("section_path" in n and "I5" in n for n in rec["notes"]),
                                                                              any("0 of 8 items straddle" in n for n in rec["notes"])], [True, True])
r2 = sf.run_check([DPDF], split_level="2", doc_ids=["climate"])["files"][0]
r4 = sf.run_check([DPDF], split_level="4", doc_ids=["climate"])["files"][0]
check("1 --split-level 2 and 4 pick those arms; auto is off", [r2["chosen_arm"], r2["auto"], r4["chosen_arm"], r4["arms"]["L4"]["n"]], ["L2", False, "L4", 209])
check("1 --min-chars 300 makes auto pick L4 (median 334)", sf.run_check([DPDF], min_chars=300, sample=0)["files"][0]["split_level"], 4)

# ---------------------------------------------------------------- 2 chunk for chunk vs i2_structure.py
print("=== 2 chunk for chunk vs i2_structure.py")
doc = pymupdf.open(DPDF)
pages = S.page_texts(doc)
starts = S.page_starts(pages)
T = "\n".join(pages)
HS = S.add_paths(S.align(T, S.detect_headings(doc, "size+bold")))
check("2 doc_text identical", d_text == T, True)
check("2 headings identical (page, level, title, lines, offsets, path)", [{k: h[k] for k in HS[0]} for h in r["_heads"]] == HS, True)
for lv, mc, name in ((2, 0, "L2"), (3, 0, "L3"), (4, 0, "L4"), (4, 400, "L4 + merge<400")):
    ref = S.structure_chunks(T, HS, starts, lv, 1000, mc)
    check(f"2 {name}: every chunk equal (a, b, text, path, merged, piece, pieces, page_segments)", [len(ref), r["_arms"][name] == ref], [len(ref), True])
ref0 = S.v0_chunks(pages, starts)
check("2 v0: the same 97 chunks", [(c["a"], c["b"], c["text"]) for c in r["_arms"]["v0 per-page 1000/200"]] == [(c["a"], c["b"], c["text"]) for c in ref0], True)
Hso = S.add_paths(S.align(T, S.detect_headings(doc, "size")))
check("2 L3 size-only: equal", r["_arms"]["L3, size-only headings"] == S.structure_chunks(T, Hso, starts, 3, 1000, 0), True)
check("2 the tool is standalone (no import of i2_structure or sources/)",
      [n for n in ("i2_structure", "sources") if re.search(rf"^\s*(import|from)\s+\S*{n}", TOOL.read_text(encoding="utf-8"), re.M)], [])

# ---------------------------------------------------------------- 3 the zoo
print("=== 3 the zoo (small PDFs made with PyMuPDF)")
ZOO = TMP / "zoo"
ZOO.mkdir()
WORDS = ("river water flows through the valley and feeds farms towns forests wetlands lakes the delta the sea people "
         "measure depth speed and quality every season to plan for floods droughts and change").split()


def para(seed, n_sent=4):
    out = []
    for k in range(n_sent):
        w = [WORDS[(seed * 7 + k * 5 + j * 3) % len(WORDS)] for j in range(11 + (seed + k) % 5)]
        out.append(" ".join(w).capitalize() + ".")
    return " ".join(out)


class Pdf:
    """A tiny layout engine: headings and wrapped paragraphs down the page, a new page when full."""

    def __init__(self, header=None):
        self.doc, self.header, self.page, self.y = pymupdf.open(), header, None, 0
        self.new_page()

    def new_page(self):
        self.page = self.doc.new_page()
        self.y = 60
        if self.header:
            self.page.insert_text((72, 36), self.header(len(self.doc)), fontsize=11, fontname="hebo")

    def line(self, text, size=11, bold=False, x=72, gap=None):
        if self.y > 780:
            self.new_page()
        self.page.insert_text((x, self.y), text, fontsize=size, fontname="hebo" if bold else "helv")
        self.y += gap if gap is not None else size * 1.45

    def head(self, text, size, gap_before=10):
        self.y += gap_before
        self.line(text, size, True)
        self.y += 2

    def para(self, text, width=88):
        for ln in textwrap.wrap(text, width):
            self.line(ln)
        self.y += 8

    def lead_in(self, bold, rest):
        if self.y > 780:
            self.new_page()
        tw = pymupdf.TextWriter(self.page.rect)
        tw.append((72, self.y), bold, font=pymupdf.Font("hebo"), fontsize=11)
        tw.append(tw.last_point, " " + rest, font=pymupdf.Font("helv"), fontsize=11)
        tw.write_text(self.page)
        self.y += 11 * 1.45 + 8

    def save(self, name, toc=None):
        if toc:
            self.doc.set_toc(toc)
        p = ZOO / name
        self.doc.save(p)
        return p


def river_book(pdf, chapters=3, subs=3, wrapped=False, sub_size=11, chap_size=15, title_size=20, numbered=False):
    """Title, chapters, bold body-size sub-headings, ~360-character paragraphs."""
    pdf.head("A Field Guide to Rivers" if not numbered else "Rivers Handbook", title_size, 0)
    toc = [[1, "A Field Guide to Rivers", 1]]
    k = 0
    for c in range(1, chapters + 1):
        title = f"{c} Chapter Topic {c}" if numbered else f"Chapter {c}: River Topic {c}"
        if wrapped and c == 2:
            pdf.head("Chapter 2: A Long Chapter Title About Rivers That", chap_size)
            pdf.y -= 2 + 10 - 4
            pdf.line("Needs Two Lines", chap_size, True)
            title = "Chapter 2: A Long Chapter Title About Rivers That Needs Two Lines"
        else:
            pdf.head(title, chap_size)
        toc.append([2, title, len(pdf.doc)])
        pdf.para(para(k := k + 1, 3))
        for s in range(1, subs + 1):
            st = f"{c}.{s} Section {c} {s}" if numbered else f"Stream Part {c}{s}"
            pdf.head(st, sub_size, 4)
            if numbered:
                pdf.para(para(k := k + 1, 3))
                pdf.head(f"{c}.{s}.1 Detail {c} {s}", 11, 4)
            pdf.para(para(k := k + 1, 3))
    return toc


def zoo(name, build, **kw):
    pdf = Pdf(kw.pop("header", None))
    toc = build(pdf)
    return sf.run_check([pdf.save(name, kw.pop("toc", None) or None)], sample=kw.pop("sample", 5), **kw)["files"][0]


# 3a bold body-size headings
za = zoo("bold_body.pdf", lambda p: river_book(p))
check("3a bold body-size headings: size only 1/3, size + bold 1/3/9", [za["levels"]["size"], za["levels"]["size+bold"]], [{1: 1, 2: 3}, {1: 1, 2: 3, 3: 9}])
check("3a size only misses 9 of 13 -> S4 MANUAL; S2, S3 PASS", [len(za["missed_by_size"]), V(za, "S4"), V(za, "S2"), V(za, "S3")], [9, "MANUAL", "PASS", "PASS"])
check("3a auto picks L2 (sub-sections are short); 0 invariant violations", [za["split_level"], sum(sum(v.values()) for v in za["invariants"].values())], [2, 0])
check("3a no outline, not tagged -> S5 WARN; recommendation: typography route at L2",
      [V(za, "S5"), za["recommendation"]["main"].startswith("Typography route"), "L2" in za["recommendation"]["main"]], ["WARN", True, True])
check("3a verdicts", verdicts(za), "S1 PASS S2 PASS S3 PASS S4 MANUAL S5 WARN S6 PASS S7 PASS S8 PASS S9 PASS S10 MANUAL S11 PASS")

# 3b a wrapped heading
zb = zoo("wrapped.pdf", lambda p: river_book(p, wrapped=True))
check("3b the wrapped chapter heading is one heading (2 lines joined)", [(w["title"], w["lines"]) for w in zb["wrapped"]],
      [("Chapter 2: A Long Chapter Title About Rivers That Needs Two Lines", 2)])
check("3b still 3 chapters, all aligned (S6 PASS)", [zb["levels"]["size+bold"].get(2), zb["aligned"], V(zb, "S6")], [3, 13, "PASS"])
check("3b the joined title is the path of its sections", any(c["path"][1:2] == ["Chapter 2: A Long Chapter Title About Rivers That Needs Two Lines"]
                                                           for c in zb["_arms"]["L2"]), True)

# 3c running header on every page; 3d the same header with a page number
build_long = lambda p: river_book(p, chapters=6, subs=4)
zc = zoo("running_header.pdf", build_long, header=lambda n: "Riverside Press Review")
check("3c running header (bold, every page) is excluded; numbered sub-headings are not mistaken for one; S8 PASS", [zc["pages"] >= 3, [x["text"] for x in zc["repeated_lines"]], V(zc, "S8")],
      [True, ["Riverside Press Review"], "PASS"])
check("3c it is not a heading", any(h["title"] == "Riverside Press Review" for h in zc["outline"]), False)
zd = zoo("page_header.pdf", build_long, header=lambda n: f"Riverside Review page {n}")
check("3d a header with a page number: S8 WARN, named in the evidence, note in the recommendation",
      [V(zd, "S8"), "Riverside Review page" in next(x["evidence"] for x in zd["checklist"] if x["id"] == "S8"),
       any("running header" in n for n in zd["recommendation"]["notes"])], ["WARN", True, True])


# 3e two columns, read across the columns; 3f column by column
def two_col(p, interleave):
    p.head("Two Column Report", 16, 0)
    p.para(para(1, 4))
    left = [f"Left column line {i} says the river level rose again." for i in range(24)]
    right = [f"Right column line {i} says the gauge was read twice." for i in range(24)]
    y0 = p.y
    if interleave:
        for i in range(24):
            p.page.insert_text((60, y0 + 14 * i), left[i], fontsize=9, fontname="helv")
            p.page.insert_text((315, y0 + 14 * i), right[i], fontsize=9, fontname="helv")
    else:
        for i in range(24):
            p.page.insert_text((60, y0 + 14 * i), left[i], fontsize=9, fontname="helv")
        for i in range(24):
            p.page.insert_text((315, y0 + 14 * i), right[i], fontsize=9, fontname="helv")
    p.y = y0 + 14 * 24 + 10
    p.head("Closing Notes", 11, 4)
    p.para(para(2, 4))


ze = zoo("two_column_across.pdf", lambda p: two_col(p, True))
check("3e two columns read across: right-to-left jumps -> S7 FAIL; recommendation: fix reading order first (C1)",
      [ze["layout"]["max_jumps"] >= 2, V(ze, "S7"), ze["recommendation"]["main"].startswith("Fix reading order first")], [True, "FAIL", True])
zf = zoo("two_column_blocks.pdf", lambda p: two_col(p, False))
check("3f two columns read column by column: two-column page, 1 jump (last right line -> next heading) -> S7 WARN, note", [zf["layout"]["two_col_pages"], zf["layout"]["max_jumps"], V(zf, "S7"),
                                                                                     any("column by column" in n for n in zf["recommendation"]["notes"])], [[1], 1, "WARN", True])

# 3g an outline (set_toc) that matches; 3h one that does not
pg = Pdf()
toc = river_book(pg)
toc += [[3, f"Stream Part {c}{s}", 1] for c in (1, 2, 3) for s in (1, 2, 3)]
zg = sf.run_check([pg.save("outline.pdf", toc)], sample=5)["files"][0]
check("3g outline present (13 entries, all match) -> S5 PASS; recommendation: use the outline",
      [len(zg["toc"]), zg["toc_matched"], V(zg, "S5"), zg["recommendation"]["main"].startswith("Use the outline as the heading source")], [13, 13, "PASS", True])
ph = Pdf()
river_book(ph)
zh = sf.run_check([ph.save("outline_other.pdf", [[1, "Introduction", 1], [1, "Methods", 1], [1, "Results", 1]])], sample=5)["files"][0]
check("3h outline that does not match the headings -> S5 WARN; typography route", [zh["toc_matched"], V(zh, "S5"), zh["recommendation"]["main"].startswith("Typography")],
      [0, "WARN", True])


# 3i one image-only page; 3j every page image-only
def image_page(doc):
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 60, 80), False)
    pix.clear_with(180)
    doc.new_page().insert_image(pymupdf.Rect(72, 72, 520, 760), pixmap=pix)


pi = Pdf()
river_book(pi)
image_page(pi.doc)
zi = sf.run_check([pi.save("scan_page.pdf")], sample=5)["files"][0]
check("3i one page without a text layer (the last of 3): S1 WARN (image-only), note; route still typography",
      [zi["pages"], zi["no_text"], V(zi, "S1"), any("no text layer" in n for n in zi["recommendation"]["notes"]), zi["recommendation"]["main"].startswith("Typography")],
      [3, [{"page": 3, "images": 1}], "WARN", True, True])
dj = pymupdf.open()
for _ in range(3):
    image_page(dj)
dj.save(ZOO / "scan_all.pdf")
zj = sf.run_check([ZOO / "scan_all.pdf"])["files"][0]
check("3j every page image-only: S1 FAIL, S2 FAIL, S3 FAIL; recommendation: no structure, use v1.0 recursive",
      [V(zj, "S1"), V(zj, "S2"), V(zj, "S3"), zj["recommendation"]["main"].startswith("No structure: use v1.0 recursive"), zj["body"]], ["FAIL", "FAIL", "FAIL", True, None])

# 3k numbered headings whose depth the typography flattens; 3l numbered headings that agree with the levels
zk = zoo("numbered_flat.pdf", lambda p: river_book(p, numbered=True))
check("3k numbered: depths 1, 2, 3 but sizes give L2, L3, L3 -> S3 WARN; recommendation: structure unclear, use numbering",
      [zk["numbering"]["depth_to_levels"], zk["numbering"]["consistent"], V(zk, "S3"), zk["recommendation"]["main"].startswith("Structure unclear (S3)"),
       "numbering depth" in zk["recommendation"]["main"]], [{1: [2], 2: [3], 3: [3]}, False, "WARN", True, True])
zl = zoo("numbered_ok.pdf", lambda p: river_book(p, numbered=True, sub_size=13.5))
check("3l numbered with distinct sizes: depth 1 -> L2, 2 -> L3, 3 -> L4, consistent -> S3 PASS",
      [zl["numbering"]["depth_to_levels"], zl["numbering"]["consistent"], V(zl, "S3"), zl["recommendation"]["main"].startswith("Typography")],
      [{1: [2], 2: [3], 3: [4]}, True, "PASS", True])


# 3m a bold lead-in phrase inside a paragraph line, and a whole bold line that ends with a full stop
def lead(p):
    toc = river_book(p, chapters=2, subs=2)
    p.lead_in("Note.", "the gauge readings below were taken at dawn and checked against the log book twice.")
    p.line("Always check the gauge before you paddle out.", 11, True)
    p.para(para(40, 3))
    return toc


zm = zoo("lead_in.pdf", lead)
titles = [h["title"] for h in zm["outline"]]
check("3m the bold lead-in 'Note.' line is not a heading (the line is not all bold)", any(t.startswith("Note.") for t in titles), False)
check("3m the bold full sentence is removed by the filter (final '.')", [zm["filtered_long"], "Always check the gauge before you paddle out." in titles],
      [["Always check the gauge before you paddle out."], False])
check("3m headings unchanged: 1 + 2 + 4", zm["levels"]["size+bold"], {1: 1, 2: 2, 3: 4})


# 3n a ruled table; 3o blank pages
def table(p):
    river_book(p, chapters=1, subs=2)
    y0 = p.y + 10
    for i in range(5):
        for j in range(3):
            rect = pymupdf.Rect(72 + 150 * j, y0 + 20 * i, 222 + 150 * j, y0 + 20 * (i + 1))
            p.page.draw_rect(rect, color=(0, 0, 0), width=0.8)
            p.page.insert_text((rect.x0 + 4, rect.y1 - 6), f"cell {i}-{j}", fontsize=9, fontname="helv")
    p.y = y0 + 110


zn = zoo("table.pdf", table)
check("3n a ruled table: find_tables finds it -> S11 WARN, note 'Tables found'",
      [sum(zn["layout"]["tables"].values()) >= 1, V(zn, "S11"), any(n.startswith("Tables found") for n in zn["recommendation"]["notes"])], [True, "WARN", True])
dz = pymupdf.open()
dz.new_page()
dz.new_page()
dz.save(ZOO / "blank.pdf")
zo = sf.run_check([ZOO / "blank.pdf"])["files"][0]
check("3o blank pages: no crash, S1 FAIL, no headings, no chunks", [V(zo, "S1"), zo["n_heads"]["size+bold"], zo["arms"]["L1"]["n"], zo["sample"]],
      ["FAIL", 0, 0, []])

rendered = []
for zp in sorted(ZOO.glob("*.pdf")):
    try:
        zr = sf.run_check([zp], sample=3)
        rendered.append(bool(sf.render_report(zr)) and bool(sf.render_sheet(zr)) and bool(json.loads(sf.to_json(zr))))
    except Exception as e:  # noqa: BLE001
        rendered.append(f"{zp.name}: {e!r}")
check("3 report, sheet and JSON render for every zoo PDF (15)", rendered, [True] * 15)

# ---------------------------------------------------------------- 4 rules in isolation
print("=== 4 rules in isolation")
fake = [{"page": 1, "block": 0, "last_line": 0, "level": 1, "size": 20.0, "lines": ["Not In The Text"], "title": "Not In The Text"}]
ok_, failed = sf.align("Some text\nHeading\nbody", fake + [{**fake[0], "lines": ["Heading"], "title": "Heading"}])
check("4 alignment fails closed: the missing heading is reported, the cursor does not move", [[f["title"] for f in failed], [h["start"] for h in ok_]],
      [["Not In The Text"], [10]])
base = {"S1": "PASS", "S2": "PASS", "S3": "PASS", "S4": "PASS", "S5": "WARN", "S6": "PASS", "S7": "PASS", "S8": "PASS", "S9": "PASS", "S10": "MANUAL", "S11": "PASS"}


def fake_r(**kw):
    return {"checklist": [{"id": k, "verdict": v} for k, v in {**base, **kw}.items()], "split_level": 3, "auto": True,
            "sections": {3: {"median": 1033.5}}, "n_repeated_titles": 0, "sample": [], "evalset": None, "chosen_arm": "L3", "arms": {}}


R = lambda **kw: sf.recommend(fake_r(**kw), 400)["main"]
check("4 recommendation rule order (S1 > S7 > S6 > S5 > S2-S4 > unclear)",
      [R(S1="FAIL", S7="FAIL").startswith("No structure"), R(S7="FAIL", S6="FAIL").startswith("Fix reading order"),
       R(S6="FAIL", S5="PASS").startswith("Do not use yet"), R(S5="PASS", S3="WARN").startswith("Use the outline"),
       R().startswith("Typography route"), R(S4="MANUAL").startswith("Typography route"), R(S2="WARN").startswith("Structure unclear (S2)")], [True] * 7)
check("4 S10 pre-check under 8/10 -> 'Do not measure yet' note", any(n.startswith("Do not measure yet") for n in sf.recommend(fake_r(S10="WARN"), 400)["notes"]), True)
p12, p13 = pages[11], pages[12]
a12 = p12.find("Public-\nprivate partnerships")
e13 = p13.find("climate solutions.") + len("climate solutions.")
cross = TMP / "cross.jsonl"
cross.write_text(json.dumps({"qid": "X-1", "category": "cross-page", "answerable": True, "evidence_groups": [{"group_id": "g1", "alternatives": [
    {"alt_id": "g1a", "segments": [{"doc_id": "climate", "page": 12, "char_start": a12, "char_end": len(p12)},
                                   {"doc_id": "climate", "page": 13, "char_start": 0, "char_end": e13}]}]}]}) + "\n", encoding="utf-8")
rx = sf.run_check([DPDF], sample=0, evalset=cross, doc_ids=["climate"])["files"][0]
row = rx["evalset"]["rows"][0]
check("4 the PPP sentence (pp.12->13) as an eval item: straddles_v0, crosses_page, whole in one L3 chunk",
      [row["straddles_v0"], row["crosses_page"], row["whole_in_structure"], row["pages"]], [True, True, True, [12, 13]])
check("4 a non-empty boundary bucket changes the note", any("1 of 1 items straddle" in n for n in rx["recommendation"]["notes"]), True)
two = TMP / "two.jsonl"
two.write_text(json.dumps({"qid": "Z-1", "answerable": True, "evidence_groups": [{"alternatives": [{"segments": [
    {"doc_id": "bold_body", "page": 1, "char_start": 0, "char_end": 20}], "quote": "A Field Guide to Riv"}]}]}) + "\n", encoding="utf-8")
rt = sf.run_check([ZOO / "bold_body.pdf", ZOO / "wrapped.pdf"], evalset=two, sample=2)
check("4 two PDFs: segments matched by doc_id (file stem); the other file lists the item as another document's",
      [[len(f["evalset"]["rows"]) for f in rt["files"]], rt["files"][1]["evalset"]["other_doc"], rt["files"][0]["evalset"]["quotes_ok"]], [[1, 0], ["Z-1"], 1])
check("4 two PDFs: the report has one recommendation per file", sf.render_report(rt).count("**Recommendation for `"), 2)
check("4 bad options raise ValueError", [raises(lambda: sf.run_check([DPDF], cap=0), ValueError), raises(lambda: sf.run_check([DPDF], split_level="5"), ValueError),
                                         raises(lambda: sf.run_check([DPDF], sample=-1), ValueError), raises(lambda: sf.run_check([DPDF], min_chars=-1), ValueError),
                                         raises(lambda: sf.run_check([DPDF], doc_ids=["a", "b"]), ValueError)], [True] * 5)
(TMP / "empty_dir").mkdir()
check("4 bad paths raise", [raises(lambda: sf.find_pdfs([TMP / "nope.pdf"]), FileNotFoundError), raises(lambda: sf.find_pdfs([TMP / "empty_dir"]), ValueError)], [True, True])

# ---------------------------------------------------------------- 5 CLI
print("=== 5 CLI")
env = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def cli(*args):
    return subprocess.run([sys.executable, str(TOOL), *map(str, args)], capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(WS))


outs = []
for n in (1, 2):
    cp = cli("--pdf", DPDF, "--doc-ids", "climate", "--evalset", SEEDS, "--out", TMP / f"r{n}.md", "--sheet", TMP / f"s{n}.md")
    outs.append((cp.returncode, (TMP / f"r{n}.md").read_bytes() if (TMP / f"r{n}.md").exists() else b"", (TMP / f"s{n}.md").read_bytes() if (TMP / f"s{n}.md").exists() else b""))
check("5 the CLI (Windows-layout path with a space) exits 0 and equals the saved example report",
      [outs[0][0], outs[0][1] == (EX / "climate_structure_report.md").read_bytes()], [0, True])
check("5 the inspection sheet equals the saved example sheet", outs[0][2] == (EX / "climate_structure_sheet.md").read_bytes(), True)
check("5 a second run is byte-identical (report and sheet)", [outs[0][1] == outs[1][1], outs[0][2] == outs[1][2]], [True, True])
check("5 the stdout summary lists S1-S11 and the recommendation", [cp.stdout.count(" S") >= 11, "recommendation: Typography route" in cp.stdout], [True, True])
check("5 the report names files, never their folders", [str(TMP) in outs[0][1].decode("utf-8"), "Book RAG" in outs[0][1].decode("utf-8")], [False, False])
cp = cli("--pdf", DPDF, "--json", "-", "--sample", "3")
js = json.loads(cp.stdout) if cp.returncode == 0 else {}
check("5 --json - prints JSON (no chunk text; chunks with offsets and paths)", [cp.returncode, js["files"][0]["chunks"][3]["a"], "text" in js["files"][0]["chunks"][0],
                                                                                 len(js["files"][0]["sample"]), "text" in js["files"][0]["sample"][0]], [0, 1621, False, 3, False])
cp = cli("--help")
check("5 --help exits 0 and names every option", [cp.returncode] + [o in cp.stdout for o in ("--pdf", "--cap", "--split-level", "--min-chars", "--sample", "--seed",
                                                                                            "--evalset", "--out", "--sheet", "--json")], [0] + [True] * 10)
cp = cli("--pdf", ZOO / "bold_body.pdf")
check("5 without --out the report goes to stdout", [cp.returncode, cp.stdout.startswith("# Structure fit check")], [0, True])
(TMP / "notes.txt").write_text("not a pdf", encoding="utf-8")
(TMP / "garbage.pdf").write_text("this is not a PDF", encoding="utf-8")
(TMP / "bad.jsonl").write_text('{"qid": "A", "evidence_groups": []}\nnot json\n', encoding="utf-8")
(TMP / "nogroups.jsonl").write_text('{"qid": "A"}\n', encoding="utf-8")
(TMP / "range.jsonl").write_text(json.dumps({"qid": "R-1", "answerable": True, "evidence_groups": [{"alternatives": [{"segments": [
    {"doc_id": "x", "page": 99, "char_start": 0, "char_end": 5}]}]}]}) + "\n", encoding="utf-8")
bad = [("a missing PDF", ("--pdf", TMP / "nope.pdf"), "no such file"),
       ("a .txt file", ("--pdf", TMP / "notes.txt"), "not a PDF"),
       ("a file that is not a PDF inside", ("--pdf", TMP / "garbage.pdf"), "cannot open"),
       ("an eval set with a bad line", ("--pdf", ZOO / "bold_body.pdf", "--evalset", TMP / "bad.jsonl"), "line 2"),
       ("an eval set without evidence_groups", ("--pdf", ZOO / "bold_body.pdf", "--evalset", TMP / "nogroups.jsonl"), "evidence_groups"),
       ("an eval segment outside the PDF", ("--pdf", ZOO / "bold_body.pdf", "--evalset", TMP / "range.jsonl"), "outside the page text"),
       ("a missing eval set", ("--pdf", ZOO / "bold_body.pdf", "--evalset", TMP / "none.jsonl"), "eval set not found"),
       ("--cap 0", ("--pdf", ZOO / "bold_body.pdf", "--cap", "0"), "--cap"),
       ("--sample -1", ("--pdf", ZOO / "bold_body.pdf", "--sample", "-1"), "--sample"),
       ("--doc-ids count mismatch", ("--pdf", ZOO / "bold_body.pdf", "--doc-ids", "a,b"), "--doc-ids"),
       ("--split-level 5 (argparse)", ("--pdf", ZOO / "bold_body.pdf", "--split-level", "5"), "invalid choice"),
       ("no --pdf (argparse)", ("--cap", "500"), "--pdf")]
for label, args, msg in bad:
    cp = cli(*args)
    check(f"5 bad input, {label}: exit 2 with a clear message", [cp.returncode, msg in cp.stderr, cp.stdout == ""], [2, True, True])
src = TOOL.read_text(encoding="utf-8")
check("5 the tool imports no network or API client", [w for w in ("requests", "urllib", "http", "socket", "groq", "cohere", "anthropic", "langsmith", "dotenv", "openai")
                                                      if re.search(rf"^\s*(import|from)\s+{re.escape(w)}", src, re.M)], [])
check("5 the tool imports only the standard library and PyMuPDF",
      sorted({(n.module if isinstance(n, ast.ImportFrom) else a.name).split(".")[0] for n in ast.walk(ast.parse(src)) if isinstance(n, (ast.Import, ast.ImportFrom))
              for a in (n.names if isinstance(n, ast.Import) else [n])} - set(sys.stdlib_module_names)), ["fitz", "pymupdf"])
tree = ast.parse(src)
doc_node = tree.body[0].value
literals = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and n is not doc_node]
check("5 no hard-coded path in the code (the docstring's usage example aside)",
      [s for s in literals if re.search(r"[A-Za-z]:[/\\]|/tmp|/home/|Book RAG|\.env", s)], [])

shutil.rmtree(TMP, ignore_errors=True)
n_ok = sum(ok for _, ok in RESULTS)
print(f"\n{n_ok}/{len(RESULTS)} tool checks passed")
sys.exit(0 if n_ok == len(RESULTS) else 1)
