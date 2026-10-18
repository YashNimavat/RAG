"""Build study/notebooks/I2_structure_chunking_verify.ipynb: the "verify it yourself" notebook for I2 (structure-aware chunking).

The notebook rebuilds every measured number and chart of the I2 lesson (study/lessons/I2_structure_chunking.html) from
code, one section per fact block S1-S14 of sources/verification/I2/I2_FACTS.md, and compares each value with the
lesson's value in a `check(...)` line. Expected values are copied from I2_FACTS.md and out_i2_measure.txt; nothing else.

The notebook is self-contained: it re-implements the rules of i2_structure.py inline (it lives in study/ and must not
import from sources/). This builder tests that claim: when it can find the climate PDF, it executes the notebook's
"rules" cells and compares their headings and chunks with i2_structure.py for every arm (v0, cross-page, L2, L3, L4,
L4 + merge, L3 size-only). Any difference stops the build.

Retrieval (S14) uses sentence-transformers/all-MiniLM-L6-v2 from the local cache; if it is not cached, the ONNX export
of the same model when I2_MINILM_ONNX names its directory and onnxruntime imports; otherwise that section prints
SKIPPED (counted apart from passes).

No Groq, Cohere or Claude call, no .env read, no network.

Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I2/i2_build_verify_nb.py
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I2/i2_verify_nb_run.py \
        > sources/verification/I2/out_i2_verify_nb_run.txt                              # executes it, saves outputs
PDF: the RAG_PDF environment variable, else the P4 notebook's default locations.
"""
import os
import sys
from pathlib import Path
from textwrap import dedent

import nbformat as nbf

HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]                                           # rag_learning/
OUT = WS / "study" / "notebooks" / "I2_structure_chunking_verify.ipynb"

CELLS = []
RULES = []                                                     # sources of the cells tagged "rules" (for the self-test)


def md(s):
    CELLS.append(nbf.v4.new_markdown_cell(dedent(s).strip()))


def code(s, rules=False):
    src = dedent(s).strip()
    cell = nbf.v4.new_code_cell(src)
    if rules:
        cell.metadata["tags"] = ["rules"]
        RULES.append(src)
    CELLS.append(cell)


# =====================================================================================================================
md(r"""
# I2 · Verify it yourself: structure-aware chunking

**What this is:** a notebook that rebuilds every measured number and chart of the I2 lesson from real code: the font sizes inside the climate PDF, the headings they give, the section tree, the chunks at three split levels, the invariants, and the retrieval table.
**What this is not:** the apply-it tool (`study/tools/structure_fit_check.py`, which runs the same checks on *your* PDFs) or the quiz. It makes **no API call**: no Groq, no Cohere, no Claude.

**How to use it.** Run all cells from the top (VS Code: *Run All*). The sections follow the lesson and the fact blocks S1–S14 of `I2_FACTS.md`. Each one has:
- a short note on what it verifies;
- a code cell that **computes** the values;
- `check(...)` lines: `PASS` means the code produced the number the lesson shows, `FAIL` means it did not;
- an interactive chart where one is worth seeing. Hover for values.

The last cell counts the checks.

**The running example.** Corpus D, `Understanding_Climate_Change.pdf` (33 pages), frozen as the PyMuPDF 1.26.7 snapshot `ea07572562ac`: the page texts joined with `"\n"`. Every chunk is a slice `[a, b)` of that one string. The main path splits at **L3 (section)** with a cap of **1,000 characters** and no overlap; L2, L4 and L4 + merge are the comparison arms; v0 (per page, 1,000/200) is the baseline.

**The rules are written out here, not imported.** The cells marked *The rules* are a copy of `sources/verification/I2/i2_structure.py` (the builder of this notebook checks that they give the same headings and chunks). Change a rule and re-run to see what moves.

**Retrieval.** Section 14 uses MiniLM (`all-MiniLM-L6-v2`) from the local cache. If it is not cached, it uses the ONNX export of the same model when the `I2_MINILM_ONNX` environment variable names its folder; otherwise it prints `SKIPPED`. The 8 answerable draft questions are `llm-draft` items: every rank is an **observation, never an evaluation result**.

**Where the expected values come from.** `sources/verification/I2/I2_FACTS.md` §1 (S1–S14) and `out_i2_measure.txt`.
""")

code(r'''
# Setup: imports, paths, the PDF, the snapshot and the shared helpers. Run this cell first.
import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")          # models may load from the local cache only: no network
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

import hashlib
import importlib.metadata as md
import json
import math
import random
import statistics as st
import sys
import time
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pymupdf                                        # pinned 1.26.7
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

pio.renderers.default = "plotly_mimetype"             # small outputs that VS Code draws
warnings.filterwarnings("ignore", message="IProgress not found")
T0 = time.time()


def find_workspace():
    here = Path.cwd().resolve()
    for p in (here, *here.parents):
        if (p / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").is_file() and (p / "study").is_dir():
            return p
    raise FileNotFoundError("Open this notebook from inside rag_learning/.")


def find_pdf():
    """RAG_PDF if set; else the default locations of the P4 notebook (upstream/RAG_Techniques/data/ next to rag_learning/)."""
    if os.environ.get("RAG_PDF"):
        p = Path(os.environ["RAG_PDF"])
        if not p.is_file():
            raise FileNotFoundError(f"RAG_PDF is set but is not a file: {p}")
        return p
    rel = Path("upstream") / "RAG_Techniques" / "data" / "Understanding_Climate_Change.pdf"
    for p in (Path("C:/Yash/New-Work/Book RAG") / rel, WS.parent / rel, WS / rel):
        if p.is_file():
            return p
    raise FileNotFoundError("Climate PDF not found: set RAG_PDF to Understanding_Climate_Change.pdf")


WS = find_workspace()
PDF = find_pdf()
print("workspace:", WS)
print("pdf:", PDF)
print("python", sys.version.split()[0], {p: md.version(p) for p in ("pymupdf", "numpy", "plotly")})

# ---------------------------------------------------------------- check(): computed value vs the lesson's value
CHECKS, SKIPPED = [], []
T3 = 5e-4                                             # tolerance for values the lesson prints with 3 decimals
T4 = 5e-5                                             # ... with 4 decimals


def _plain(x):
    if isinstance(x, np.generic):
        x = x.item()
    if isinstance(x, np.ndarray):
        x = x.tolist()
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    return x


def _same(got, exp, tol):
    got, exp = _plain(got), _plain(exp)
    if got is None or exp is None:
        return got is None and exp is None
    if isinstance(got, dict) or isinstance(exp, dict):
        return (isinstance(got, dict) and isinstance(exp, dict) and got.keys() == exp.keys()
                and all(_same(got[k], exp[k], tol) for k in got))
    if isinstance(got, list) or isinstance(exp, list):
        return (isinstance(got, list) and isinstance(exp, list) and len(got) == len(exp)
                and all(_same(g, e, tol) for g, e in zip(got, exp)))
    if isinstance(got, (str, bool)) or isinstance(exp, (str, bool)):
        return got == exp
    return abs(float(got) - float(exp)) <= tol


def _show(x, limit=220):
    s = repr(_plain(x))
    return s if len(s) <= limit else s[:limit] + " …"


def check(name, got, expected, tol=0.0):
    """PASS when the computed value equals the lesson's value (numbers within `tol`)."""
    ok = _same(got, expected, tol)
    CHECKS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}: got {_show(got)}  |  lesson {_show(expected)}"
          + (f"  (tolerance {tol:g})" if tol else ""))


def skip(name, reason):
    SKIPPED.append((name, reason))
    print(f"SKIPPED  {name}: {reason}")


# ---------------------------------------------------------------- chart style (light surface, fixed colour order, as P4)
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
BLUE, ORANGE, AQUA, RED = "#2a78d6", "#eb6834", "#1baf7a", "#c8323c"
pio.templates["i2"] = go.layout.Template(layout=dict(
    font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', size=13, color=INK2),
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, colorway=[BLUE, ORANGE, AQUA],
    xaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    yaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=INK2)),
    title=dict(x=0, xanchor="left", font=dict(size=15, color=INK)),
    margin=dict(l=70, r=30, t=90, b=60), hoverlabel=dict(font_size=12)))
pio.templates.default = "i2"

# ---------------------------------------------------------------- the PDF and the frozen snapshot (06 §5.3)
check("environment: pymupdf version (pinned)", md.version("pymupdf"), "1.26.7")
RAW = PDF.read_bytes()
check("corpus: PDF sha256", hashlib.sha256(RAW).hexdigest(), "1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669")
check("corpus: PDF bytes", len(RAW), 206372)
doc = pymupdf.open(PDF)
pages = [p.get_text() for p in doc]                   # the snapshot's page texts
DICTS = [p.get_text("dict") for p in doc]             # the same pages as span dicts (read once, used by every rule)
T = "\n".join(pages)                                  # doc_text: every chunk is a slice T[a:b]
print(f"\nsetup done in {time.time() - T0:.1f} s: {len(doc)} pages, doc_text {len(T):,} characters")
''')

# =====================================================================================================================
md(r"""
## 1 · The snapshot, and which structure the PDF itself offers

**What this verifies** (lesson step 1 and `#s6`; I2_FACTS S1). The page count, the length of `doc_text`, and the **snapshot id** recomputed with the 06 §5.3 recipe (`snapshot-v1 | parser | options | cleaning | page_join | climate:<sha256 of doc_text>`). Then the three places structure could come from before we guess it from fonts: the outline (`get_toc()`, empty here), the tag tree (`StructTreeRoot`, present: the PDF is tagged) and the producer (Word 2021).
""")
code(r'''
tsha = hashlib.sha256(T.encode()).hexdigest()
parts = ["snapshot-v1", f"parser=pymupdf@{pymupdf.VersionBind}", "options=" + json.dumps({}, sort_keys=True),
         "cleaning=none", "page_join=\\n", f"climate:{tsha}"]
SNAP = hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]
print("recipe:", " | ".join(parts[:-1]), "| climate:" + tsha[:12] + "…")
check("S1 pages, doc_text characters", [len(doc), len(T)], [33, 72593])
check("S1 doc_text sha256 (first 12)", tsha[:12], "5106772efa77")
check("S1 snapshot_id (06 §5.3 recipe)", SNAP, "ea07572562ac")

cat = doc.pdf_catalog()
check("S1 outline: doc.get_toc()", doc.get_toc(), [])
check("S1 catalog: StructTreeRoot is present (tagged PDF)", doc.xref_get_key(cat, "StructTreeRoot")[0], "xref")
check("S1 catalog: MarkInfo", list(doc.xref_get_key(cat, "MarkInfo")), ["dict", "<</Marked true>>"])
check("S1 producer: metadata creator", doc.metadata.get("creator"), "Microsoft® Word 2021")
''')

# =====================================================================================================================
md(r"""
## 2 · Inside the PDF: one span dict, and the flag bits

**What this verifies** (lesson `#s2`; I2_FACTS S2). `page.get_text("dict")` gives blocks → lines → **spans**; a span is a run of text in one font. The first three spans of page 1: the title, the Chapter 1 heading and the first body line. Their keys, size, font, bounding box, and the `flags` number, decoded bit by bit (1 superscript, 2 italic, 4 serif, 8 monospaced, 16 bold). Bold is `flags & 16`; PyMuPDF also reports synthetic bold as `char_flags & 8`, and the rules accept either.
""")
code(r'''
FLAG_BITS = {1: "superscript", 2: "italic", 4: "serif", 8: "monospaced", 16: "bold"}


def flag_names(flags):
    return [name for bit, name in FLAG_BITS.items() if flags & bit]


first = [s for b in DICTS[0]["blocks"] for line in b.get("lines", []) for s in line["spans"]][:3]
for s in first:
    print(f"   text={s['text']!r}\n      size={s['size']:.2f} flags={s['flags']} = {' + '.join(f'{b} {n}' for b, n in FLAG_BITS.items() if s['flags'] & b)}"
          f" -> {flag_names(s['flags'])}, char_flags={s['char_flags']}, font={s['font']}, bbox=({', '.join(f'{v:.1f}' for v in s['bbox'])})")
title, chap, body = first
check("S2 span keys (besides text)", sorted(k for k in title if k != "text"),
      ["alpha", "ascender", "bbox", "bidi", "char_flags", "color", "descender", "flags", "font", "origin", "size"])
check("S2 title span: text, size, flags, char_flags, font",
      [title["text"], round(title["size"], 2), title["flags"], title["char_flags"], title["font"]],
      ["Understanding Climate Change ", 24.0, 20, 24, "TimesNewRomanPS-BoldMT"])
check("S2 title span bbox (1 decimal)", [round(v, 1) for v in title["bbox"]], [72.0, 73.1, 403.4, 99.6])
check("S2 title flags 20 = 16 bold + 4 serif", flag_names(title["flags"]), ["serif", "bold"])
check("S2 chapter span: text, size, flags", [chap["text"], round(chap["size"], 2), chap["flags"]],
      ["Chapter 1: Introduction to Climate Change ", 18.0, 20])
check("S2 body span: size, flags (serif only), char_flags, font",
      [round(body["size"], 2), body["flags"], body["char_flags"], body["font"]], [12.0, 4, 16, "TimesNewRomanPSMT"])
check("S2 bold bit: title, chapter, body", [bool(s["flags"] & 16) for s in first], [True, True, False])
''')

# =====================================================================================================================
md(r"""
## The rules, part 1: from spans to heading lines

These functions are the reference rules (`i2_structure.py`), written out. They read the cached `DICTS` instead of re-parsing the PDF.
- **Bold** = `flags & 16` or `char_flags & 8`.
- **Body size** = the size holding the **most characters** (character-weighted, not span-weighted).
- **Levels by size rank:** every bold size above the body is a level, largest = 1. With the `size+bold` rule, an all-bold line **at the body size** gets the next level.
- **Filters:** at most 12 words, no final `. ! ?`, not on 3 or more pages (running headers). These thresholds are project choices `[P]`, not measured optima.
- **Joining:** consecutive heading lines of the same level in one block are one heading (a wrapped title).
""")
code(r'''
# The rules, part 1 (= i2_structure.py: is_bold, line_records, size_histogram, body_size, detect_headings)
import math
from collections import Counter, defaultdict

BOLD_FLAG = 16          # span["flags"] bit 4 (PyMuPDF TEXT_FONT_BOLD)
BOLD_CHAR_FLAG = 8      # span["char_flags"] bit for synthetic bold
MAX_WORDS = 12          # [P] a heading line has at most 12 words
REPEAT_PAGES = 3        # [P] a line on >= 3 pages is a running header/footer, never a heading
END_PUNCT = ".!?"


def is_bold(span):
    return bool(span["flags"] & BOLD_FLAG) or bool(span.get("char_flags", 0) & BOLD_CHAR_FLAG)


def line_records(dicts):
    """One record per text line: page, block, line, raw text, max size, all-bold, number of non-blank spans."""
    out = []
    for pno, d in enumerate(dicts, 1):
        for bno, block in enumerate(d["blocks"]):
            for lno, line in enumerate(block.get("lines", [])):
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans:
                    continue
                out.append({"page": pno, "block": bno, "line": lno,
                            "raw": "".join(s["text"] for s in line["spans"]),
                            "size": round(max(s["size"] for s in spans), 2),
                            "bold": all(is_bold(s) for s in spans),
                            "spans": len(spans)})
    return out


def size_histogram(dicts):
    """Characters (stripped span text) per (rounded size, bold)."""
    h = Counter()
    for d in dicts:
        for block in d["blocks"]:
            for line in block.get("lines", []):
                for s in line["spans"]:
                    h[(round(s["size"], 2), is_bold(s))] += len(s["text"].strip())
    return h


def body_size(dicts):
    per_size = Counter()
    for (size, _bold), n in size_histogram(dicts).items():
        per_size[size] += n
    return per_size.most_common(1)[0][0]


def detect_headings(dicts, rule="size+bold", max_words=MAX_WORDS):
    """Heading lines -> headings with levels (rule "size" or "size+bold"), filtered and joined."""
    lines = line_records(dicts)
    b = body_size(dicts)
    bigger = sorted({r["size"] for r in lines if r["size"] > b + 0.5 and r["bold"]}, reverse=True)
    level_of = {s: i + 1 for i, s in enumerate(bigger)}
    body_level = len(bigger) + 1
    pages_of_text = defaultdict(set)
    for r in lines:
        pages_of_text[r["raw"].strip()].add(r["page"])

    def level(r):
        t = r["raw"].strip()
        if not r["bold"] or len(t.split()) > max_words or t[-1] in END_PUNCT:
            return None
        if len(pages_of_text[t]) >= REPEAT_PAGES:
            return None
        if r["size"] in level_of:
            return level_of[r["size"]]
        if rule == "size+bold" and abs(r["size"] - b) <= 0.5:
            return body_level
        return None

    heads = []
    for r in lines:
        lv = level(r)
        if lv is None:
            continue
        prev = heads[-1] if heads else None
        if (prev and prev["level"] == lv and prev["page"] == r["page"] and prev["block"] == r["block"]
                and prev["last_line"] == r["line"] - 1):
            prev["lines"].append(r["raw"])
            prev["spans"].append(r["spans"])
            prev["last_line"] = r["line"]
            prev["title"] = " ".join(x.strip() for x in prev["lines"])
            continue
        heads.append({"page": r["page"], "block": r["block"], "last_line": r["line"], "level": lv,
                      "size": r["size"], "lines": [r["raw"]], "spans": [r["spans"]], "title": r["raw"].strip()})
    return heads
''', rules=True)

# =====================================================================================================================
md(r"""
## 3 · The body size comes from character counts

**What this verifies** (lesson `#s3`; I2_FACTS S3). Characters per (size, bold) over the whole PDF. 90.6% of the characters are 12 pt regular, so the body size is **12.0**. Counting spans instead would also pick 12 here, but a character count is the safe rule: a page of short bold labels can out-count long body spans. The 11.04 pt Calibri spans are blank.

The chart is the **font ladder**: every size the PDF uses, with its characters (log scale, so the 28-character title is visible next to 63,762 body characters).
""")
code(r'''
H = size_histogram(DICTS)
total = sum(H.values())
ROWS = sorted(H.items(), key=lambda kv: (-kv[0][0], not kv[0][1]))
for (size, bold), n in ROWS:
    print(f"   size {size:5.2f} bold={str(bold):5} chars {n:6d} ({100 * n / total:.1f}%)")
check("S3 characters per (size, bold), largest size first",
      [[size, bold, n] for (size, bold), n in ROWS],
      [[24.0, True, 28], [18.0, True, 855], [13.56, True, 1666], [12.0, True, 4057], [12.0, False, 63762], [11.04, False, 0]])
check("S3 shares, % (1 decimal)", [round(100 * n / total, 1) for _, n in ROWS], [0.0, 1.2, 2.4, 5.8, 90.6, 0.0])
BODY = body_size(DICTS)
check("S3 body size (most characters)", BODY, 12.0)
spans_by_size = Counter(round(s["size"], 2) for d in DICTS for b in d["blocks"] for line in b.get("lines", [])
                        for s in line["spans"] if s["text"].strip())
check("S3 non-blank spans per size", dict(sorted(spans_by_size.items())), {12.0: 1006, 13.56: 68, 18.0: 22, 24.0: 1})

labels = [f"{size:g} pt {'bold' if bold else 'regular'}" for (size, bold), _ in ROWS if _ > 0]
vals = [n for _, n in ROWS if n > 0]
role = {24.0: "title (L1)", 18.0: "chapter (L2)", 13.56: "section (L3)"}
fig = go.Figure(go.Bar(
    y=labels, x=vals, orientation="h",
    marker=dict(color=[BLUE if b else ORANGE for (s, b), n in ROWS if n > 0], line=dict(width=2, color=SURFACE)),
    text=[f"{n:,} chars ({100 * n / total:.1f}%) · " + (role.get(s) or ("sub-section (L4), size+bold rule only" if b else "body"))
          for (s, b), n in ROWS if n > 0], textposition="outside",
    hovertemplate="%{y}: %{x:,} characters<extra></extra>"))
fig.update_layout(title="S3 · The font ladder of Corpus D: one body size (12 pt), three bigger bold sizes, and bold at body size",
                  height=380, showlegend=False, xaxis=dict(title="characters (log scale)", type="log", range=[1, 5.6]),
                  yaxis=dict(autorange="reversed"), margin=dict(r=220))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 4 · Headings: size only vs size + bold

**What this verifies** (lesson `#s4` and `#s5`; I2_FACTS S4). The two detectors on the same lines:
- **size only** (what `pymupdf4llm`'s `IdentifyHeaders` does): levels only for sizes above the body → **90** headings (L1 1, L2 21, L3 68);
- **size + bold**: bold lines at the body size become L4 → **282** headings (… + **L4 192**). Size only misses **192 of 282 (68.1%)**.

Then the error modes the filters and the joining handle: the Chapter 5 title wraps onto a second line (22 level-2 lines → 21 headings); the 15 hyphenated headings are each **one span** (the research's "three runs" worry does not occur in PyMuPDF); the filters remove nothing on this PDF, and no line repeats on 3 or more pages.
""")
code(r'''
LINES = line_records(DICTS)
bold_lines = [r for r in LINES if r["bold"]]
check("S4 text lines, all-bold lines, bold lines with more than one span",
      [len(LINES), len(bold_lines), sum(r["spans"] > 1 for r in bold_lines)], [1097, 283, 0])
DET = {rule: detect_headings(DICTS, rule) for rule in ("size", "size+bold")}
for rule, hs in DET.items():
    print(f"   {rule:9}: {len(hs)} headings, per level {dict(sorted(Counter(x['level'] for x in hs).items()))}")
check("S4 size only: headings, per level", [len(DET["size"]), dict(sorted(Counter(x["level"] for x in DET["size"]).items()))],
      [90, {1: 1, 2: 21, 3: 68}])
check("S4 size + bold: headings, per level", [len(DET["size+bold"]), dict(sorted(Counter(x["level"] for x in DET["size+bold"]).items()))],
      [282, {1: 1, 2: 21, 3: 68, 4: 192}])
missed = len(DET["size+bold"]) - len(DET["size"])
check("S4 missed by size only: count, % of 282", [missed, round(100 * missed / len(DET["size+bold"]), 1)], [192, 68.1])

wrapped = [x for x in DET["size+bold"] if len(x["lines"]) > 1]
print("   joined:", [(x["page"], x["lines"]) for x in wrapped])
check("S4 joined wrap: (page, title)", [(x["page"], x["title"]) for x in wrapped],
      [(7, "Chapter 5: The Role of Technology in Climate Change Mitigation")])
check("S4 level-2 lines before joining -> level-2 headings", [sum(1 for r in bold_lines if r["size"] == 18.0),
      sum(x["level"] == 2 for x in DET["size+bold"])], [22, 21])

hy = [x for x in DET["size+bold"] if "-" in x["title"]]
check("S4 hyphen headings (title, page)", [(x["title"], x["page"]) for x in hy],
      [("Next-Generation Solar Technologies", 7), ("Community-Based Conservation", 10), ("Public-Private Partnerships", 12),
       ("Ex-Situ Conservation", 14), ("Nature-Based Solutions", 14), ("Climate-Resilient Conservation", 14),
       ("Heat-Related Illnesses", 15), ("Vector-Borne Diseases", 15), ("Climate-Smart Healthcare", 16),
       ("Gender-Responsive Policies", 20), ("Climate-Resilient Design", 25), ("Nature-Based Solutions", 26),
       ("Climate-Resilient Agriculture", 27), ("Cross-Sector Collaboration", 30), ("Community-Based Solutions", 30)])
check("S4 hyphen headings: count; each one span", [len(hy), all(x["spans"] == [1] for x in hy)], [15, True])
long_bold = [r for r in bold_lines if len(r["raw"].split()) > MAX_WORDS or r["raw"].strip()[-1] in END_PUNCT]
pages_per_line = defaultdict(set)
for r in LINES:
    pages_per_line[r["raw"].strip()].add(r["page"])
check("S4 removed by the filters (> 12 words or final . ! ?); lines on >= 3 pages",
      [len(long_bold), [t for t, p in pages_per_line.items() if len(p) >= REPEAT_PAGES]], [0, []])
''')

# =====================================================================================================================
md(r"""
## 5 · Same text, same order

**What this verifies** (lesson `#s6`; I2_FACTS S5). For each page, the `dict` lines, each followed by `"\n"`, rebuild `page.get_text()` **exactly**. This is what lets a heading line found in the span dicts be found again, at an exact offset, in the snapshot text. If this failed on some page (a two-column page, say), alignment on that page would not be trustworthy.
""")
code(r'''
same, differ = 0, []
for pno, d in enumerate(DICTS):
    built = "".join("".join(s["text"] for s in line["spans"]) + "\n" for b in d["blocks"] for line in b.get("lines", []))
    if built == pages[pno]:
        same += 1
    else:
        differ.append(pno + 1)
check("S5 pages rebuilt exactly from dict lines + '\\n'; pages that differ", [same, len(doc), differ], [33, 33, []])
''')

# =====================================================================================================================
md(r"""
## The rules, part 2: offsets, paths and sections

- **Align** each heading to `doc_text` with a moving cursor and `str.find`; a wrapped heading's second line must follow with only whitespace between. A heading that is not found **stops** the build (fail closed): no guessed offsets.
- **Path** (breadcrumb): the titles of the open headings, kept on a stack.
- **Section** of a heading: from its start to the start of the next heading of the same or a higher level.
- **Pages:** page *p* starts at `starts[p-1]`; the join character `"\n"` belongs to the page before it.
""")
code(r'''
# The rules, part 2 (= i2_structure.py: page_starts, page_of, align, add_paths, section_ranges)
def page_starts(pages):
    starts, pos = [], 0
    for t in pages:
        starts.append(pos)
        pos += len(t) + 1
    return starts


def page_of(starts, pos):
    """1-based page of a document offset (the join character belongs to the page before it)."""
    lo, hi = 0, len(starts) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if starts[mid] <= pos:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1


def align(doc_text, heads):
    """Moving cursor + find: give every heading an exact [start, end) in doc_text. Fail closed if one is missing."""
    cur = 0
    for h in heads:
        pos = doc_text.find(h["lines"][0], cur)
        if pos < 0:
            raise ValueError(f"heading not found after offset {cur}: {h['title']!r}")
        end = pos + len(h["lines"][0])
        for ln in h["lines"][1:]:
            nxt = doc_text.find(ln, end)
            if nxt < 0 or doc_text[end:nxt].strip():
                raise ValueError(f"wrapped heading line not adjacent: {h['title']!r}")
            end = nxt + len(ln)
        h["start"], h["end"] = pos, end
        cur = end
    return heads


def add_paths(heads):
    stack = []
    for h in heads:
        while stack and stack[-1]["level"] >= h["level"]:
            stack.pop()
        stack.append(h)
        h["path"] = [x["title"] for x in stack]
    return heads


def section_ranges(heads, n, level):
    """Section of h at a given level: [start(h), start(next heading with level <= level(h)))."""
    out = []
    for i, h in enumerate(heads):
        if h["level"] != level:
            continue
        end = n
        for g in heads[i + 1:]:
            if g["level"] <= h["level"]:
                end = g["start"]
                break
        out.append((h["start"], end, h))
    return out
''', rules=True)

# =====================================================================================================================
md(r"""
## 6 · Aligning every heading to the snapshot

**What this verifies** (lesson `#s6`; I2_FACTS S6). All **282 of 282** headings get an exact offset, each on its own page. The worked case is **"Coal"**: an L4 heading on page 1 at `[2418, 2423)`; page 1's text ends at 2424, and its body text (`Coal is the most carbon-intensive…`) starts on page 2. That is one of the 16 orphaned headings of section 8.
""")
code(r'''
starts = page_starts(pages)
HEADS = add_paths(align(T, detect_headings(DICTS, "size+bold")))
check("S6 aligned headings; all inside their own page", [len(HEADS), all(page_of(starts, x["start"]) == x["page"] for x in HEADS)],
      [282, True])
coal = next(x for x in HEADS if x["title"] == "Coal")
print(f"   'Coal': level {coal['level']}, page {coal['page']}, doc [{coal['start']}, {coal['end']}), "
      f"then {T[coal['end']:coal['end'] + 40]!r}")
check("S6 'Coal': level, page, doc [start, end), end of page 1", [coal["level"], coal["page"], coal["start"], coal["end"], starts[1] - 1],
      [4, 1, 2418, 2423, 2424])
after = "\n\nCoal is the most carbon-intensive"
check("S6 'Coal': the text after it", T[coal["end"]:coal["end"] + len(after)], after)
check("S6 first 6 headings (level, title, offset)", [(x["level"], x["title"], x["start"]) for x in HEADS[:6]],
      [(1, "Understanding Climate Change", 0), (2, "Chapter 1: Introduction to Climate Change", 30), (3, "Historical Context", 467),
       (3, "Modern Observations", 1072), (2, "Chapter 2: Causes of Climate Change", 1621), (3, "Greenhouse Gases", 1658)])
''')

# =====================================================================================================================
md(r"""
## 7 · The section tree, and 11 titles that repeat

**What this verifies** (lesson `#s7`; I2_FACTS S7). **11 titles appear twice** (22 headings). A title alone is not an address: "Paris Agreement" sits under Chapter 6 > International Collaboration on p.10 and under Chapter 16 > International Agreements on p.23. The **path** tells them apart, which is why every chunk carries one. Then the Chapter 6 tree with section lengths, and the length statistics at L2, L3 and L4 (characters from a heading to the next heading of the same or a higher level).
""")
code(r'''
titles = Counter(x["title"] for x in HEADS)
REP = sorted(t for t, n in titles.items() if n > 1)
rep_rows = [(x["title"], x["page"], x["level"]) for t in REP for x in HEADS if x["title"] == t]
for t, p, lv in rep_rows:
    x = next(h for h in HEADS if h["title"] == t and h["page"] == p)
    print(f"   {t!r:32} p.{p:<2} L{lv}: {' > '.join(x['path'][1:])}")
check("S7 repeated titles: count, headings", [len(REP), len(rep_rows)], [11, 22])
check("S7 repeated titles (title, page, level)", rep_rows,
      [("Carbon Capture and Utilization", 8, 3), ("Carbon Capture and Utilization", 23, 3), ("Carbon Utilization", 8, 4),
       ("Carbon Utilization", 23, 4), ("International Agreements", 6, 4), ("International Agreements", 23, 3),
       ("International Collaboration", 10, 3), ("International Collaboration", 16, 4), ("Marine Ecosystems", 5, 4),
       ("Marine Ecosystems", 13, 4), ("Nature-Based Solutions", 14, 4), ("Nature-Based Solutions", 26, 3),
       ("Paris Agreement", 10, 4), ("Paris Agreement", 23, 4), ("Policy and Governance", 12, 3), ("Policy and Governance", 18, 4),
       ("Research and Innovation", 7, 3), ("Research and Innovation", 16, 4), ("Smart Grids", 8, 4), ("Smart Grids", 22, 4),
       ("Youth Engagement", 13, 4), ("Youth Engagement", 32, 4)])
check("S7 the two 'Paris Agreement' paths", [x["path"][1:] for x in HEADS if x["title"] == "Paris Agreement"],
      [["Chapter 6: Global and Local Climate Action", "International Collaboration", "Paris Agreement"],
       ["Chapter 16: Global Cooperation and Governance", "International Agreements", "Paris Agreement"]])

CH6 = "Chapter 6: Global and Local Climate Action"
tree = []
for i, x in enumerate(HEADS):
    if x["path"][1:2] == [CH6]:
        nxt = next((g["start"] for g in HEADS[i + 1:] if g["level"] <= x["level"]), len(T))
        tree.append((x["level"], x["title"], nxt - x["start"], x["page"]))
        print(f"   {'  ' * (x['level'] - 2)}L{x['level']} {x['title']}  ({nxt - x['start']} chars, p.{x['page']})")
check("S7 Chapter 6 tree (level, title, characters, page)", tree,
      [(2, CH6, 2728, 10), (3, "International Collaboration", 695, 10),
       (4, "United Nations Framework Convention on Climate Change (UNFCCC)", 348, 10), (4, "Paris Agreement", 318, 10),
       (3, "National Strategies", 913, 10), (4, "Carbon Pricing", 290, 10), (4, "Renewable Energy Targets", 295, 10),
       (4, "Emission Reduction Regulations", 307, 10), (3, "Local and Community Initiatives", 1076, 10),
       (4, "Urban Climate Action", 362, 10), (4, "Community-Based Conservation", 346, 10), (4, "Education and Awareness", 335, 11)])
SEC = {}
for lv in (2, 3, 4):
    ln = [b - a for a, b, _ in section_ranges(HEADS, len(T), lv)]
    SEC[lv] = [len(ln), min(ln), st.median(ln), max(ln), round(sum(ln) / len(ln), 1)]
check("S7 L2 sections: count, min, median, max, mean", SEC[2], [21, 1591, 3336, 6058, 3455.4])
check("S7 L3 sections: count, min, median, max, mean", SEC[3], [68, 549, 1033.5, 1898, 1041.3])
check("S7 L4 sections: count, min, median, max, mean", SEC[4], [192, 243, 334, 636, 336.5])
''')

# =====================================================================================================================
md(r"""
## 8 · What page-by-page chunking breaks

**What this verifies** (lesson step 1 `#s1` and `#s10`; I2_FACTS S8; closes research I2-E7). On the PyMuPDF text:
- **16 orphaned headings:** the page ends in a detected heading, so its body starts on the next page (a per-page chunker can only put the heading at the end of one chunk and its text in another);
- **8 mid-sentence cuts:** the page ends without `. ! ? :` or a quote, and the next page starts in lower case.

The same pages as LAB_FACTS §7 (measured there on PyPDFLoader text).
""")
code(r'''
orphan, cut = [], []
for p in range(len(pages) - 1):
    tail = pages[p].rstrip()
    last_line = tail.split("\n")[-1].strip()
    if any(x["page"] == p + 1 and x["title"].endswith(last_line) and T[x["end"]:starts[p + 1]].strip() == "" for x in HEADS):
        orphan.append(f"{p + 1}->{p + 2}")
    nxt = pages[p + 1].lstrip()
    if tail and tail[-1] not in '.!?:"' and nxt[:1].islower():
        cut.append(f"{p + 1}->{p + 2}")
print("   orphaned headings:", orphan)
print("   mid-sentence cuts:", cut)
check("S8 orphaned headings: count, page breaks", [len(orphan), orphan],
      [16, ["1->2", "2->3", "3->4", "4->5", "5->6", "6->7", "7->8", "8->9", "10->11", "11->12", "17->18", "18->19", "20->21",
            "27->28", "30->31", "31->32"]])
check("S8 mid-sentence cuts: count, page breaks", [len(cut), cut],
      [8, ["12->13", "14->15", "15->16", "16->17", "21->22", "22->23", "24->25", "28->29"]])
check("S8 page breaks not ending in . ! ? : or a quote (of 32)",
      [sum(1 for p in range(len(pages) - 1) if pages[p].rstrip()[-1:] not in '.!?:"'), len(pages) - 1], [24, 32])
''')

# =====================================================================================================================
md(r"""
## The rules, part 3: units, the balanced split, merge, and the baselines

- **Units at a split level:** a boundary at every heading of level ≤ the split level, **except** a heading that directly follows another heading: **a heading never ends a unit or a chunk; it glues forward** to the text it introduces. Each unit carries the path of its last split-level heading.
- **Balanced split:** a unit longer than the cap C is cut into n = ⌈ℓ/C⌉ pieces of about ℓ/n each. Each cut goes to a **sentence-ending line break** within half a piece of the ideal point, else to the nearest line break; never inside or right after a heading. No overlap.
- **Merge** (optional): two adjacent units both shorter than `min_chars`, with the same parent and together ≤ C, become one.
- **v0** (the baseline): the 07 recursive splitter (`"\n\n"`, `"\n"`, `" "`), 1,000/200, **per page**. The **cross-page control** is the same splitter over the whole `doc_text`.
- **page_segments:** the pages a chunk covers, as `(page, a, b)` pieces that rebuild `[a, b)`.
""")
code(r'''
# The rules, part 3 (= i2_structure.py: recursive splitter, v0, cross-page control, units, merge, balanced split, chunks)
import math

SEPARATORS = ("\n\n", "\n", " ")    # the v0 / 07 H.1 recursive separators


def _split_spans(text, start, end, seps, size):
    """07 H.1: recursively cut [start, end) into pieces of <= size chars, preferring early separators."""
    if end - start <= size:
        return [(start, end)]
    if not seps:
        return [(s, s + 1) for s in range(start, end)]
    sep, rest = seps[0], seps[1:]
    pieces, i = [], start
    while i < end:
        j = text.find(sep, i, end)
        if j == -1:
            pieces.append((i, end))
            break
        pieces.append((i, j + len(sep)))
        i = j + len(sep)
    out = []
    for a, b in pieces:
        out.extend([(a, b)] if b - a <= size else _split_spans(text, a, b, rest, size))
    return out


def recursive_spans(text, size, overlap):
    """07 H.1 recursive_chunks: greedy merge up to size; the next chunk restarts with whole trailing pieces <= overlap."""
    if not text:
        return []
    spans, cur = [], []
    for p in _split_spans(text, 0, len(text), SEPARATORS, size):
        if cur and p[1] - cur[0][0] > size:
            spans.append((cur[0][0], cur[-1][1]))
            keep = []
            for q in reversed(cur):
                if cur[-1][1] - q[0] <= overlap:
                    keep.insert(0, q)
                else:
                    break
            cur = keep
            while cur and p[1] - cur[0][0] > size:
                cur.pop(0)
        cur.append(p)
    if cur:
        spans.append((cur[0][0], cur[-1][1]))
    return spans


def page_segments(starts, n, a, b):
    segs = []
    ends = [s - 1 for s in starts[1:]] + [n]          # page p covers [start_p, start_{p+1}) incl. its join char
    for p, (s, e) in enumerate(zip(starts, ends), 1):
        e_incl = e + 1 if p < len(starts) else e
        lo, hi = max(a, s), min(b, e_incl)
        if lo < hi:
            segs.append((p, lo, hi))
    return segs


def v0_chunks(pages, starts, size=1000, overlap=200):
    """v0: the recursive splitter per page, as document offsets."""
    out = []
    for pi, page in enumerate(pages):
        for a, b in recursive_spans(page, size, overlap):
            if page[a:b].strip():
                out.append({"a": starts[pi] + a, "b": starts[pi] + b, "text": page[a:b], "page": pi + 1})
    return out


def recursive_doc_chunks(doc_text, size=1000, overlap=200):
    """The cross-page control: the same recursive splitter over the whole doc_text (no page scope)."""
    return [{"a": a, "b": b, "text": doc_text[a:b]} for a, b in recursive_spans(doc_text, size, overlap)
            if doc_text[a:b].strip()]


def units(doc_text, heads, split_level):
    """Split-level units. A heading that directly follows another heading (only whitespace between) is glued forward."""
    bounds = [0]
    prev_end = None
    for h in heads:
        if h["level"] > split_level:
            prev_end = h["end"]
            continue
        glued = prev_end is not None and not doc_text[prev_end:h["start"]].strip()
        if not glued and h["start"] > 0:
            bounds.append(h["start"])
        prev_end = h["end"]
    bounds.append(len(doc_text))
    out = []
    for a, b in zip(bounds, bounds[1:]):
        if b > a:
            inside = [h for h in heads if a <= h["start"] < b]
            last_split = [h for h in inside if h["level"] <= split_level]
            owner = last_split[-1] if last_split else None
            if owner is None:                              # unit opens with deeper headings or body text
                before = [h for h in heads if h["start"] < a]
                owner = before[-1] if before else None
            out.append({"a": a, "b": b, "path": list(owner["path"]) if owner else [], "merged": False})
    return out


def merge_small(doc_text, us, cap, min_chars, split_level):
    """While two adjacent units are both below min_chars, share their parent path and fit the cap, merge them."""
    changed = True
    us = [dict(u) for u in us]
    while changed:
        changed = False
        for i in range(len(us) - 1):
            x, y = us[i], us[i + 1]
            parent_x, parent_y = x["path"][:split_level - 1], y["path"][:split_level - 1]
            if (x["b"] - x["a"] < min_chars and y["b"] - y["a"] < min_chars and parent_x == parent_y
                    and y["b"] - x["a"] <= cap):
                us[i] = {"a": x["a"], "b": y["b"], "path": parent_x if parent_x else x["path"], "merged": True}
                del us[i + 1]
                changed = True
                break
    return us


def heading_guard(text, heads):
    """Cut positions that would end a chunk inside a heading or right after one (before its body starts)."""
    bad = set()
    for h in heads:
        e = h["end"]
        while e < len(text) and text[e].isspace():
            e += 1
        bad.update(range(h["start"] + 1, e + 1))
    return bad


def _best_cut(text, prev, b, ideal, cap, forbidden, room, slack):
    """End of the piece that starts at prev: a sentence-ending line break within `slack` of the ideal point wins,
    else the nearest line break (a space if no line break fits); the piece fits the cap, the rest fits `room`."""
    for sep in ("\n", " "):
        cands, i = [], prev
        while True:
            j = text.find(sep, i, b)
            if j < 0:
                break
            p = j + 1
            if prev < p < b and p - prev <= cap and b - p <= room and p not in forbidden:
                cands.append(p)
            i = j + 1
        if cands:
            clean = [p for p in cands if sep == "\n" and text[:p].rstrip()[-1:] in ".!?" and abs(p - ideal) <= slack]
            pool = clean or cands
            return min(pool, key=lambda p: (abs(p - ideal), p))
    return min(prev + cap, b)                  # no usable separator at all: a hard cut


def balanced_split(text, a, b, cap, forbidden=frozenset()):
    """n = ceil(len/cap) pieces of about len/n each; no overlap. If a piece would still exceed the cap, try n + 1."""
    length = b - a
    if length <= cap:
        return [(a, b)]
    n = math.ceil(length / cap)
    while True:
        cuts = [a]
        for i in range(1, n):
            cuts.append(_best_cut(text, cuts[-1], b, a + length * i / n, cap, forbidden, (n - i) * cap, length / (2 * n)))
        cuts.append(b)
        pieces = list(zip(cuts, cuts[1:]))
        if all(0 < y - x <= cap for x, y in pieces):
            return pieces
        n += 1


def structure_chunks(doc_text, heads, starts, split_level, cap=1000, min_chars=0):
    us = units(doc_text, heads, split_level)
    if min_chars:
        us = merge_small(doc_text, us, cap, min_chars, split_level)
    guard = heading_guard(doc_text, heads)
    chunks = []
    for u in us:
        pieces = balanced_split(doc_text, u["a"], u["b"], cap, guard)
        for k, (a, b) in enumerate(pieces):
            if not doc_text[a:b].strip():
                continue
            chunks.append({"a": a, "b": b, "text": doc_text[a:b], "path": u["path"], "merged": u["merged"],
                           "piece": k, "pieces": len(pieces), "page_segments": page_segments(starts, len(doc_text), a, b)})
    return chunks
''', rules=True)

# =====================================================================================================================
md(r"""
## 9 · The chunk arms: v0, the cross-page control, and three split levels

**What this verifies** (lesson `#s8`; I2_FACTS S9). Seven arms with cap C = 1,000 characters: the chunk count, min / median / max / mean length, how many chunks run across a page break, and the length histogram in 100-character bins.

| Arm | Chunks | min / median / max | mean | on 2 pages |
|---|---|---|---|---|
| v0 per page 1000/200 | 97 | 393 / 935 / 1000 | 857.9 | 0 |
| cross-page 1000/200 (control) | 92 | 755 / 962.5 / 999 | 954.8 | 41 |
| L2 chapter | 86 | 644 / 843.5 / 1000 | 844.1 | 29 |
| **L3 section** | **117** | **187 / 619 / 997** | **620.5** | **27** |
| L4 sub-section | 209 | 187 / 338 / 636 | 347.3 | 24 |
| L4 + merge (min 400) | 139 | 187 / 545 / 772 | 522.3 | 25 |
| L3, size-only headings | 117 | = L3 | | |

At L3 the size-only detector gives **exactly the same 117 chunks**: the 192 bold sub-headings change nothing at section level; they matter for splitting at L4 and for the breadcrumb.
""")
code(r'''
CAP, MIN_CHARS = 1000, 400
v0 = v0_chunks(pages, starts)
xp = recursive_doc_chunks(T)
for c in v0 + xp:
    c["page_segments"] = page_segments(starts, len(T), c["a"], c["b"])
HEADS_SIZE = add_paths(align(T, detect_headings(DICTS, "size")))
ARMS = {
    "v0 per page": v0,
    "cross-page control": xp,
    "L2 chapter": structure_chunks(T, HEADS, starts, 2, CAP),
    "L3 section": structure_chunks(T, HEADS, starts, 3, CAP),
    "L4 sub-section": structure_chunks(T, HEADS, starts, 4, CAP),
    "L4 + merge 400": structure_chunks(T, HEADS, starts, 4, CAP, MIN_CHARS),
    "L3 size-only": structure_chunks(T, HEADS_SIZE, starts, 3, CAP),
}
L3 = ARMS["L3 section"]


def stats(ch):
    ln = [c["b"] - c["a"] for c in ch]
    return [len(ch), min(ln), st.median(ln), max(ln), round(sum(ln) / len(ln), 1),
            sum(1 for c in ch if len({p for p, _, _ in c["page_segments"]}) > 1)]


def hist(ch, width=100, top=1000):
    bins = [0] * (top // width)
    for c in ch:
        bins[min((c["b"] - c["a"] - 1) // width, len(bins) - 1)] += 1
    return bins


EXP9 = {"v0 per page": ([97, 393, 935, 1000, 857.9, 0], [0, 0, 0, 1, 0, 9, 13, 5, 3, 66]),
        "cross-page control": ([92, 755, 962.5, 999, 954.8, 41], [0, 0, 0, 0, 0, 0, 0, 1, 1, 90]),
        "L2 chapter": ([86, 644, 843.5, 1000, 844.1, 29], [0, 0, 0, 0, 0, 0, 9, 27, 17, 33]),
        "L3 section": ([117, 187, 619, 997, 620.5, 27], [0, 1, 0, 18, 16, 18, 29, 15, 6, 14]),
        "L4 sub-section": ([209, 187, 338, 636, 347.3, 24], [0, 1, 40, 143, 19, 2, 4, 0, 0, 0]),
        "L4 + merge 400": ([139, 187, 545, 772, 522.3, 25], [0, 1, 7, 36, 19, 17, 34, 25, 0, 0]),
        "L3 size-only": ([117, 187, 619, 997, 620.5, 27], [0, 1, 0, 18, 16, 18, 29, 15, 6, 14])}
for name, ch in ARMS.items():
    check(f"S9 {name}: chunks, min, median, max, mean, on 2 pages", stats(ch), EXP9[name][0])
    check(f"S9 {name}: histogram, 100-char bins", hist(ch), EXP9[name][1])
check("S9 L3 size-only = L3 size+bold: identical chunks",
      [(c["a"], c["b"]) for c in ARMS["L3 size-only"]] == [(c["a"], c["b"]) for c in L3], True)
U3 = units(T, HEADS, 3)
check("S9 L3 units: total, owned by a section, chapter openings (text before the first section)",
      [len(U3), sum(len(u["path"]) == 3 for u in U3), sum(len(u["path"]) == 2 for u in U3)], [71, 68, 3])
check("S9 L3 chunks by pieces per unit {1: chunks, 2: chunks}", dict(sorted(Counter(c["pieces"] for c in L3).items())), {1: 25, 2: 92})
check("S9 L3 units over the cap (of 71)", sum(1 for u in U3 if u["b"] - u["a"] > CAP), 46)
check("S9 L4 + merge: merged chunks", sum(c["merged"] for c in ARMS["L4 + merge 400"]), 70)

SHOW = ["v0 per page", "cross-page control", "L2 chapter", "L3 section", "L4 sub-section", "L4 + merge 400"]
fig = make_subplots(rows=2, cols=3, subplot_titles=[f"{k} ({len(ARMS[k])})" for k in SHOW], shared_yaxes=True,
                    horizontal_spacing=0.05, vertical_spacing=0.2)
binlab = [f"{100 * i}–{100 * i + 99 if i < 9 else 1000}" for i in range(10)]
for i, k in enumerate(SHOW):
    fig.add_bar(x=[100 * j + 50 for j in range(10)], y=hist(ARMS[k]), row=i // 3 + 1, col=i % 3 + 1, width=92,
                marker=dict(color=BLUE if k == "L3 section" else (ORANGE if k == "v0 per page" else MUTED)),
                customdata=binlab, name=k, hovertemplate=k + ": %{customdata} chars: %{y} chunks<extra></extra>")
fig.update_xaxes(range=[0, 1000], tickvals=[0, 250, 500, 750, 1000], title_text="characters")
fig.update_yaxes(title_text="chunks", col=1)
fig.update_layout(title="S9 · Chunk lengths per arm (cap 1,000): v0 piles up at the cap, L3 spreads by section length",
                  height=560, showlegend=False)
fig.show()
''')

# =====================================================================================================================
md(r"""
## 10 · The balanced split, worked out

**What this verifies** (lesson `#s9`; I2_FACTS S10). The shortest L3 section over the cap is Chapter 11 > Advocacy and Activism, **1,004 characters**. n = ⌈1004/1000⌉ = 2, ideal 502 each. The cut goes to the sentence-ending line break nearest 502 (within half a piece): pieces **341 + 663**. A naive cap cut would give 1,000 + **4**: a 4-character orphan. The longest section, Chapter 2 > Greenhouse Gases (1,935), splits **990 + 945**.
""")
code(r'''
GUARD = heading_guard(T, HEADS)
over = sorted([u for u in U3 if CAP < u["b"] - u["a"] <= 2 * CAP], key=lambda u: u["b"] - u["a"])
ex = over[0]
ell = ex["b"] - ex["a"]
pcs = balanced_split(T, ex["a"], ex["b"], CAP, GUARD)
cutp = pcs[0][1]
print(f"   {' > '.join(ex['path'][1:])}: {ell} chars, n = {math.ceil(ell / CAP)}, ideal cut at +{ell / 2:.0f}, real cut at +{cutp - ex['a']}")
print(f"   ...{T[cutp - 70:cutp]!r}  |CUT|  {T[cutp:cutp + 50]!r}...")
check("S10 shortest L3 section over the cap: path, length", [ex["path"][1:], ell],
      [["Chapter 11: Education and Advocacy", "Advocacy and Activism"], 1004])
check("S10 n = ceil(1004/1000), ideal piece", [math.ceil(ell / CAP), ell / 2], [2, 502.0])
check("S10 balanced pieces; naive cap cut", [[b - a for a, b in pcs], [CAP, ell - CAP]], [[341, 663], [1000, 4]])
check("S10 the cut follows a sentence end", T[:cutp].rstrip()[-1:] in ".!?", True)
big = max(U3, key=lambda u: u["b"] - u["a"])
bp = balanced_split(T, big["a"], big["b"], CAP, GUARD)
check("S10 longest L3 section: path, length, pieces", [big["path"][1:], big["b"] - big["a"], [b - a for a, b in bp]],
      [["Chapter 2: Causes of Climate Change", "Greenhouse Gases"], 1935, [990, 945]])
''')

# =====================================================================================================================
md(r"""
## The rules, part 4: the invariants

Five properties every structure chunk list must have. Each is checked on the real chunks, not assumed:
1. **round trip:** `doc_text[a:b] == text`;
2. **cap:** no chunk is longer than C;
3. **gaps:** no non-whitespace text falls between two chunks;
4. **crossing:** no split-level boundary inside a chunk, except a glued heading run (a merged chunk is allowed to hold two small units);
5. **segments:** `page_segments` rebuild `[a, b)` exactly.
""")
code(r'''
# The rules, part 4 (= i2_structure.py: check_invariants, _only_headings)
def _only_headings(doc_text, heads, a, b):
    covered = [(h["start"], h["end"]) for h in heads if a <= h["start"] and h["end"] <= b]
    rest, pos = [], a
    for s, e in sorted(covered):
        rest.append(doc_text[pos:s])
        pos = e
    rest.append(doc_text[pos:b])
    return not "".join(rest).strip()


def check_invariants(doc_text, chunks, heads, split_level, cap):
    """Returns a dict of violations (all lists empty = pass)."""
    bad = {"round_trip": [], "cap": [], "gaps": [], "crossing": [], "segments": []}
    for i, c in enumerate(chunks):
        if doc_text[c["a"]:c["b"]] != c["text"]:
            bad["round_trip"].append(i)
        if c["b"] - c["a"] > cap:
            bad["cap"].append(i)
        segs = c["page_segments"]
        if not segs or segs[0][1] != c["a"] or segs[-1][2] != c["b"] or any(
                s[2] != t[1] for s, t in zip(segs, segs[1:])):
            bad["segments"].append(i)
    for x, y in zip(chunks, chunks[1:]):
        if y["a"] != x["b"] and doc_text[x["b"]:y["a"]].strip():
            bad["gaps"].append((x["b"], y["a"]))
    bounds = sorted(h["start"] for h in heads if h["level"] <= split_level)
    for i, c in enumerate(chunks):
        if c["merged"]:
            continue
        inside = [s for s in bounds if c["a"] < s < c["b"]]
        for s in inside:
            if any(h["start"] >= c["a"] and h["end"] <= s for h in heads) and _only_headings(doc_text, heads, c["a"], s):
                continue
            bad["crossing"].append(i)
            break
    return bad
''', rules=True)

# =====================================================================================================================
md(r"""
## 11 · The invariants hold on every structure arm

**What this verifies** (lesson `#s11`; I2_FACTS S11). **0 violations** of each invariant in all five structure arms, and the L3 chunks **tile** the document: no overlap, gaps only whitespace. Then a self-test that the checker is not blind: a copy of L3 with one chunk's text altered and one chunk removed must show exactly one round-trip violation and one gap.
""")
code(r'''
LEVEL = {"L2 chapter": 2, "L3 section": 3, "L4 sub-section": 4, "L4 + merge 400": 4, "L3 size-only": 3}
for name, lv in LEVEL.items():
    bad = check_invariants(T, ARMS[name], HEADS, lv, CAP)
    check(f"S11 {name}: violations round_trip, cap, gaps, crossing, segments", [len(v) for v in bad.values()], [0, 0, 0, 0, 0])
check("S11 L3 tiles the document: gaps only whitespace; overlapping pairs",
      [all(x["b"] == y["a"] or not T[x["b"]:y["a"]].strip() for x, y in zip(L3, L3[1:])),
       sum(1 for x, y in zip(L3, L3[1:]) if y["a"] < x["b"])], [True, 0])

broken = [dict(c) for c in L3]
broken[10]["text"] = broken[10]["text"][:-1] + "#"          # one character changed: the slice no longer matches
del broken[20]
bad = check_invariants(T, broken, HEADS, 3, CAP)
check("S11 self-test: a corrupted copy is caught (round_trip, gaps)", [len(bad["round_trip"]), len(bad["gaps"])], [1, 1])
''')

# =====================================================================================================================
md(r"""
## 12 · Containment: what each arm keeps together

**What this verifies** (lesson `#s1` and `#s10`; I2_FACTS S12).
- **"Coal"** (the heading at the end of page 1) and its first body line (top of page 2): in one chunk under L3 (chunk 3, pages 1–2), never under v0.
- **The PPP sentence** at doc `[26866, 26997)`, cut by the 12→13 page break: whole in one chunk in every arm except v0, and the structure arms say where it sits (the path).

The chart is the **page ruler** for pages 1–2: v0's chunks stop at the page break (with 200-character overlaps inside each page); L3's chunks follow the sections and run across it. Hover a bar for its chunk.
""")
code(r'''
def holder(ch, a, b):
    return [i for i, c in enumerate(ch) if c["a"] <= a and b <= c["b"]]


cbody = T.find("Coal is the most carbon-intensive", coal["end"])
h_v0, h_l3 = holder(v0, coal["start"], cbody + 30), holder(L3, coal["start"], cbody + 30)
check("S12 'Coal' + its first body line in one chunk: v0, L3", [bool(h_v0), bool(h_l3)], [False, True])
check("S12 L3 chunk that holds it: id, pages", [h_l3[0], [p for p, _, _ in L3[h_l3[0]]["page_segments"]]], [3, [1, 2]])

ppp_a = T.find("Public-\nprivate partnerships (PPPs) can leverage")
ppp_b = T.find("climate solutions.", ppp_a) + len("climate solutions.")
check("S12 PPP sentence: doc [a, b), pages", [ppp_a, ppp_b, page_of(starts, ppp_a), page_of(starts, ppp_b)], [26866, 26997, 12, 13])
check("S12 PPP sentence text", T[ppp_a:ppp_b],
      "Public-\nprivate partnerships (PPPs) can leverage resources, expertise, and innovation to implement \n\nlarge-scale climate solutions.")
P8 = "Chapter 8: Future Directions and Innovations"
EXP12 = {"v0 per page": None, "cross-page control": "-", "L2 chapter": P8, "L3 section": f"{P8} > Policy and Governance",
         "L4 sub-section": f"{P8} > Policy and Governance > Public-Private Partnerships",
         "L4 + merge 400": f"{P8} > Policy and Governance > Public-Private Partnerships", "L3 size-only": f"{P8} > Policy and Governance"}
for name, ch in ARMS.items():
    hh = holder(ch, ppp_a, ppp_b)
    got = (" > ".join(ch[hh[0]].get("path", [])[1:]) or "-") if hh else None
    check(f"S12 whole PPP sentence in one chunk, {name}: path (None = not in one chunk)", got, EXP12[name])

# the page ruler, pages 1-2
end2 = starts[2] - 1
fig = go.Figure()
for row, (name, ch, colour) in enumerate((("v0 per page", v0, ORANGE), ("L3 section", L3, BLUE))):
    y0 = 2 - 1.2 * row
    for i, c in enumerate(ch):
        if c["a"] >= end2:
            continue
        y = y0 + (0.22 if i % 2 else 0)
        fig.add_scatter(x=[c["a"], min(c["b"], end2)], y=[y, y], mode="lines", line=dict(color=colour, width=12),
                        name=name, legendgroup=name, showlegend=(i == 0),
                        hovertemplate=f"{name} chunk {i}: [{c['a']}, {c['b']}) {c['b'] - c['a']} chars<extra></extra>")
hs = [x for x in HEADS if x["start"] < end2]
fig.add_scatter(x=[x["start"] for x in hs], y=[-0.35] * len(hs), mode="markers", name="headings",
                marker=dict(symbol="line-ns", size=16, line=dict(width=2, color=[INK if x["level"] < 4 else MUTED for x in hs])),
                text=[f"L{x['level']} {x['title']}" for x in hs], hovertemplate="%{text} @%{x}<extra></extra>")
fig.add_vline(x=starts[1] - 1, line=dict(color=RED, dash="dash", width=2), annotation_text="page 1 | page 2",
              annotation_position="top")
fig.add_annotation(x=coal["start"], y=-0.35, text="Coal", showarrow=True, ay=-30, ax=-30, font=dict(color=INK))
fig.update_layout(title="S12 · Page ruler, pp.1–2: v0 stops at the page break; L3 keeps 'Coal' with its body",
                  height=380, xaxis=dict(title="doc_text offset (characters)", range=[0, end2]),
                  yaxis=dict(tickvals=[2.1, 0.9, -0.35], ticktext=["v0 per page", "L3 section", "headings"], range=[-0.8, 2.6],
                             showgrid=False))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 13 · Eye inspection: 10 random L3 chunks (your verdict sheet)

**What this verifies** (lesson `#s12`; I2_FACTS S13). `random.Random(0).sample` picks 10 of the 117 L3 chunks: **5, 33, 49, 51, 53, 62, 65, 97, 108, 113**. All 10 start at a heading and end at a sentence end (65 and 108 are second pieces that start at a sub-heading); 51, 62, 97 and 108 run across a page break.

The checks cover the mechanical part. The **verdict** is yours: read each chunk's start, end and path, and mark the sheet (OK / wrong path / bad cut). The tutor's reading in this session found the paths correct; that is not your verdict.
""")
code(r'''
IDX = sorted(random.Random(0).sample(range(len(L3)), 10))
check("S13 sampled chunk ids (seed 0)", IDX, [5, 33, 49, 51, 53, 62, 65, 97, 108, 113])
sheet = []
for i in IDX:
    c = L3[i]
    head = any(x["start"] == c["a"] for x in HEADS)
    sent = c["text"].rstrip()[-1:] in ".!?:"
    pg = [p for p, _, _ in c["page_segments"]]
    sheet.append((i, c["a"], c["b"], c["b"] - c["a"], pg, f"{c['piece'] + 1}/{c['pieces']}", head, sent))
    print(f"chunk {i:3d}  [{c['a']}, {c['b']})  {c['b'] - c['a']} chars  pages {pg}  piece {c['piece'] + 1}/{c['pieces']}"
          f"  starts at a heading: {head}  ends a sentence: {sent}")
    print(f"     path:   {' > '.join(c['path'][1:])}")
    print(f"     starts: {c['text'].lstrip()[:70].replace(chr(10), ' ')!r}")
    print(f"     ends:   {c['text'].rstrip()[-50:].replace(chr(10), ' ')!r}")
    print("     your verdict:  [ ] OK   [ ] wrong path   [ ] bad start/end   note: ________________\n")
check("S13 [a, b) of the 10 chunks", [[a, b] for _, a, b, *_ in sheet],
      [[3556, 4543], [21294, 22207], [31533, 32348], [33071, 33769], [34158, 34869], [39900, 40609], [41727, 42456],
       [60282, 61223], [67316, 68026], [70214, 70603]])
check("S13 lengths", [s[3] for s in sheet], [987, 913, 815, 698, 711, 709, 729, 941, 710, 389])
check("S13 pieces", [s[5] for s in sheet], ["1/1", "1/1", "1/2", "1/2", "1/1", "1/2", "2/2", "1/1", "2/2", "1/2"])
check("S13 start at a heading, end at a sentence end (of 10)", [sum(s[6] for s in sheet), sum(s[7] for s in sheet)], [10, 10])
check("S13 chunks across a page break: id and pages", [(s[0], s[4]) for s in sheet if len(s[4]) > 1],
      [(51, [15, 16]), (62, [18, 19]), (97, [27, 28]), (108, [30, 31])])
check("S13 paths of 65 and 108 (second pieces)", [" > ".join(L3[i]["path"][1:]) for i in (65, 108)],
      ["Chapter 13: Climate Change and Social Justice > Climate Justice", "Chapter 20: Climate Change and Innovation > Social Innovation"])
''')

# =====================================================================================================================
md(r"""
## 14 · Seeds, buckets and retrieval (observations, not results)

**What this verifies** (lesson `#s13`; I2_FACTS S14).
- The 10 draft seeds (`study/tools/examples/climate_seed_spans.jsonl`), 8 answerable; all 11 single-segment quotes match the snapshot.
- **Buckets:** `straddles_v0` (no v0 chunk holds an evidence span) = **0 of 8**; `crosses_page` = **0 of 8**. No seed tests the failure I2 fixes, so the verdict on these 8 is **inconclusive**.
- **Retrieval** with MiniLM-L6, exact cosine, for every arm: **CE@4** (all evidence groups covered by the top 4 chunks), **CE@budget** (top chunks packed in rank order into 4 × v0's mean length = **3,432 characters**), the CE rank per seed and MRR@10 by CE, the first-hit ranks and their MRR@10 (v0: **0.708**, = P4 K4), and the WordPiece maximum (no chunk over 256).
- Cross-check with P4 K3: D-002's top 5 on v0 are chunks 69, 68, 27, 17, 84.

The chart compares CE@4 and CE@budget by arm.
""")
code(r'''
SEEDS = [json.loads(x) for x in (WS / "study" / "tools" / "examples" / "climate_seed_spans.jsonl").read_text(encoding="utf-8").splitlines()
         if x.strip()]
ANS = [s for s in SEEDS if s.get("answerable")]
GROUPS, ok = {}, 0
for s in ANS:
    gs = []
    for g in s["evidence_groups"]:
        alts = []
        for alt in g["alternatives"]:
            segs = [(starts[sg["page"] - 1] + sg["char_start"], starts[sg["page"] - 1] + sg["char_end"]) for sg in alt["segments"]]
            if len(segs) == 1:
                ok += " ".join(T[segs[0][0]:segs[0][1]].split()) == " ".join(alt["quote"].split())
            alts.append(segs)
        gs.append(alts)
    GROUPS[s["qid"]] = gs
check("S14 seeds, answerable, single-segment quotes matching the snapshot", [len(SEEDS), len(ANS), ok], [10, 8, 11])


def covered(segs, ranges):
    return all(any(a <= x and y <= b for a, b in ranges) for x, y in segs)


v0_ranges = [(c["a"], c["b"]) for c in v0]
straddle = [not any(covered(alt, v0_ranges) for g in GROUPS[s["qid"]] for alt in g) for s in ANS]
crosses = [any(len({page_of(starts, x) for x, _ in alt} | {page_of(starts, y - 1) for _, y in alt}) > 1
               for g in GROUPS[s["qid"]] for alt in g) for s in ANS]
for s, a_, b_ in zip(ANS, straddle, crosses):
    pg = sorted({page_of(starts, x) for g in GROUPS[s["qid"]] for alt in g for x, _ in alt})
    print(f"   {s['qid']} {s['category']:22} groups {len(GROUPS[s['qid']])} pages {pg} straddles_v0={a_} crosses_page={b_}")
check("S14 evidence groups per seed D-001..D-008", [len(GROUPS[s["qid"]]) for s in ANS], [1, 1, 1, 1, 2, 2, 2, 1])
check("S14 buckets: straddles_v0, crosses_page (of 8)", [sum(straddle), sum(crosses)], [0, 0])

# ---------------------------------------------------------------- the embedder: local MiniLM, else the ONNX export, else SKIPPED
EMB, why = None, []
try:
    import logging
    logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
    from sentence_transformers import SentenceTransformer
    _st = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")

    class STEmbedder:
        name = "sentence-transformers all-MiniLM-L6-v2 (local cache)"

        def encode(self, texts):
            return _st.encode(list(texts), convert_to_numpy=True, normalize_embeddings=True, batch_size=32, show_progress_bar=False)

        def n_tokens(self, texts):
            return [len(_st.tokenizer(t, add_special_tokens=True)["input_ids"]) for t in texts]

    EMB = STEmbedder()
except Exception as e:  # noqa: BLE001
    why.append(f"sentence-transformers: {type(e).__name__}: {' '.join(str(e).split())[:140]}")

if EMB is None and os.environ.get("I2_MINILM_ONNX"):
    try:
        import onnxruntime as ort
        from tokenizers import Tokenizer

        class OnnxEmbedder:
            """MiniLM-L6 via its ONNX export: WordPiece, 256-token truncation, mean pooling, L2 normalisation."""
            def __init__(self, d):
                self.name = f"ONNX export of all-MiniLM-L6-v2 ({d})"
                self.tok = Tokenizer.from_file(f"{d}/tokenizer.json")
                self.tok.enable_truncation(max_length=256)
                self.tok.enable_padding(pad_id=0, pad_token="[PAD]")
                self.sess = ort.InferenceSession(f"{d}/model.onnx", providers=["CPUExecutionProvider"])
                self.names = [i.name for i in self.sess.get_inputs()]

            def n_tokens(self, texts):
                t = Tokenizer.from_str(self.tok.to_str())
                t.no_truncation()
                t.no_padding()
                return [len(e.ids) for e in t.encode_batch(list(texts))]

            def encode(self, texts, bs=32):
                texts, out = list(texts), []
                for i in range(0, len(texts), bs):
                    enc = self.tok.encode_batch(texts[i:i + bs])
                    ids = np.array([e.ids for e in enc], dtype=np.int64)
                    m = np.array([e.attention_mask for e in enc], dtype=np.int64)
                    feed = {"input_ids": ids, "attention_mask": m, "token_type_ids": np.zeros_like(ids)}
                    h = self.sess.run(None, {k: feed[k] for k in self.names})[0]
                    v = (h * m[..., None]).sum(1) / m.sum(1, keepdims=True)
                    out.append(v / np.linalg.norm(v, axis=1, keepdims=True))
                return np.vstack(out).astype(np.float32)

        EMB = OnnxEmbedder(os.environ["I2_MINILM_ONNX"])
    except Exception as e:  # noqa: BLE001
        why.append(f"ONNX stand-in: {type(e).__name__}: {' '.join(str(e).split())[:140]}")
elif EMB is None:
    why.append("ONNX stand-in: I2_MINILM_ONNX is not set")
print("embedder:", EMB.name if EMB else "none")
''')

code(r'''
EXP14 = {  # CE@4, CE@budget, CE ranks, MRR@10 by CE, first-hit ranks, MRR@10 first hit, WordPiece max, over 256
    "v0 per page":        (8, 8, [3, 3, 1, 1, 1, 1, 3, 2], 0.688, [3, 3, 1, 1, 1, 1, 2, 2], 0.708, 182, 0),
    "cross-page control": (7, 6, [4, 3, 2, 1, 1, 1, 5, 2], 0.598, [4, 3, 2, 1, 1, 1, 4, 2], 0.604, 196, 0),
    "L2 chapter":         (8, 8, [2, 3, 1, 1, 2, 1, 4, 1], 0.698, [2, 3, 1, 1, 1, 1, 2, 1], 0.792, 175, 0),
    "L3 section":         (8, 7, [2, 3, 1, 1, 4, 3, 4, 2], 0.521, [2, 3, 1, 1, 1, 3, 3, 2], 0.625, 196, 0),
    "L4 sub-section":     (7, 8, [1, 1, 1, 1, 2, 1, 5, 1], 0.838, [1, 1, 1, 1, 1, 1, 3, 1], 0.917, 118, 0),
    "L4 + merge 400":     (7, 8, [1, 1, 1, 1, 4, 3, 5, 2], 0.660, [1, 1, 1, 1, 1, 3, 3, 2], 0.771, 140, 0),
    "L3 size-only":       (8, 7, [2, 3, 1, 1, 4, 3, 4, 2], 0.521, [2, 3, 1, 1, 1, 3, 3, 2], 0.625, 196, 0),
}
MEAN_V0 = round(sum(c["b"] - c["a"] for c in v0) / len(v0), 1)
BUDGET = 4 * MEAN_V0                                   # = 4 x 857.9 (the lesson's rounded mean)
check("S14 equal budget = 4 x v0 mean chunk length (characters)", [MEAN_V0, round(BUDGET)], [857.9, 3432])

if EMB is None:
    skip("S14 retrieval table (CE@4, CE@budget, CE ranks, MRR@10, first-hit ranks, WordPiece max) and the CE chart",
         "no MiniLM: " + " | ".join(why))
else:
    t1 = time.time()
    Q = EMB.encode([s["question"] for s in ANS])
    CACHE = {}

    def vecs(texts):
        new = [t for t in dict.fromkeys(texts) if t not in CACHE]
        if new:
            for t, v in zip(new, EMB.encode(new)):
                CACHE[t] = v
        return np.stack([CACHE[t] for t in texts])

    RES = {}
    for name, ch in ARMS.items():
        S = Q @ vecs([c["text"] for c in ch]).T
        ntok = EMB.n_tokens([c["text"] for c in ch])
        ce4, ceb, ranks, hits = [], [], [], []
        for qi, s in enumerate(ANS):
            order = list((-S[qi]).argsort(kind="stable"))

            def ce_at(k):
                rng = [(ch[j]["a"], ch[j]["b"]) for j in order[:k]]
                return all(any(covered(alt, rng) for alt in g) for g in GROUPS[s["qid"]])

            ce4.append(int(ce_at(4)))
            used, k = 0, 0
            while k < len(order) and used + (ch[order[k]]["b"] - ch[order[k]]["a"]) <= BUDGET:
                used += ch[order[k]]["b"] - ch[order[k]]["a"]
                k += 1
            ceb.append(int(ce_at(k)))
            ranks.append(next((k for k in range(1, 11) if ce_at(k)), None))
            hits.append(next((k + 1 for k, j in enumerate(order[:10])
                              if any(covered(alt, [(ch[j]["a"], ch[j]["b"])]) for g in GROUPS[s["qid"]] for alt in g)), None))
        RES[name] = (sum(ce4), sum(ceb), ranks, round(sum(1 / r for r in ranks if r) / len(ranks), 3), hits,
                     round(sum(1 / r for r in hits if r) / len(hits), 3), max(ntok), sum(t > 256 for t in ntok))
        r = RES[name]
        print(f"   {name:19} CE@4 {r[0]}/8  CE@budget {r[1]}/8  CE ranks {r[2]}  MRR@10(CE) {r[3]:.3f}  "
              f"first-hit {r[4]}  MRR@10 {r[5]:.3f}  WordPiece max {r[6]} (> 256: {r[7]})")
    print(f"   (retrieval time {time.time() - t1:.1f} s)")
    for name, e in EXP14.items():
        r = RES[name]
        check(f"S14 {name}: CE@4, CE@budget (of 8)", [r[0], r[1]], [e[0], e[1]])
        check(f"S14 {name}: CE ranks D-001..D-008; MRR@10 by CE", [r[2], r[3]], [e[2], e[3]], T3)
        check(f"S14 {name}: first-hit ranks; MRR@10 first hit", [r[4], r[5]], [e[4], e[5]], T3)
        check(f"S14 {name}: WordPiece max, chunks over 256", [r[6], r[7]], [e[6], e[7]])
    d002 = Q[1] @ vecs([c["text"] for c in v0]).T
    top5 = list((-d002).argsort(kind="stable")[:5])
    check("S14 cross-check P4 K3: v0, D-002 top-5 chunk ids", top5, [69, 68, 27, 17, 84])
    check("S14 cross-check P4 K3: their cosines", [float(d002[j]) for j in top5], [0.4606, 0.4513, 0.4386, 0.4385, 0.3387], T4)

    names = list(EXP14)
    fig = go.Figure()
    fig.add_bar(x=names, y=[RES[n][0] for n in names], name="CE@4 (top 4 chunks)", marker=dict(color=BLUE, line=dict(width=2, color=SURFACE)),
                hovertemplate="%{x}: CE@4 %{y}/8<extra></extra>")
    fig.add_bar(x=names, y=[RES[n][1] for n in names], name="CE@budget (3,432 characters)",
                marker=dict(color=ORANGE, line=dict(width=2, color=SURFACE)), hovertemplate="%{x}: CE@budget %{y}/8<extra></extra>")
    fig.update_layout(title="S14 · Complete evidence on 8 draft seeds (observations): no arm is clearly better; the boundary bucket is empty",
                      barmode="group", height=400, yaxis=dict(title="seeds with all evidence retrieved (of 8)", range=[0, 8.5], dtick=1))
    fig.show()
''')

# =====================================================================================================================
md(r"""
## Result

The cell below counts the checks. Every `FAIL` names the value that disagreed; every `SKIPPED` says why it could not run (a skip is never counted as a pass).
""")
code(r'''
n_fail = sum(not ok for _, ok in CHECKS)
print(f"{len(CHECKS)} checks, {n_fail} failed, {len(SKIPPED)} skipped")
for name, ok in CHECKS:
    if not ok:
        print("   FAILED:", name)
for name, why_ in SKIPPED:
    print("   SKIPPED:", name, "-", why_)
print(f"   ({len(CHECKS) - n_fail} passed; notebook time {time.time() - T0:.1f} s)")
''')


# =====================================================================================================================
def self_test():
    """Execute the notebook's rules cells and compare headings and chunks with i2_structure.py (needs the PDF)."""
    rel = Path("upstream") / "RAG_Techniques" / "data" / "Understanding_Climate_Change.pdf"
    cands = ([Path(os.environ["RAG_PDF"])] if os.environ.get("RAG_PDF") else []) + [
        Path("C:/Yash/New-Work/Book RAG") / rel, WS.parent / rel, WS / rel]
    pdf = next((p for p in cands if p.is_file()), None)
    if pdf is None:
        print("self-test SKIPPED: climate PDF not found (set RAG_PDF)")
        return
    import fitz
    sys.path.insert(0, str(HERE))
    import i2_structure as S
    ns = {}
    exec("\n\n".join(RULES), ns)                                # noqa: S102  (our own cell sources)
    doc = fitz.open(pdf)
    pages = [p.get_text() for p in doc]
    dicts = [p.get_text("dict") for p in doc]
    T = "\n".join(pages)
    starts = S.page_starts(pages)
    assert ns["page_starts"](pages) == starts
    key_h = lambda hs: [(h["page"], h["level"], h["title"], h["start"], h["end"], h["path"]) for h in hs]
    heads = {}
    for rule in ("size", "size+bold"):
        ref = S.add_paths(S.align(T, S.detect_headings(doc, rule)))
        mine = ns["add_paths"](ns["align"](T, ns["detect_headings"](dicts, rule)))
        assert key_h(ref) == key_h(mine), f"headings differ ({rule})"
        heads[rule] = (ref, mine)
    key_c = lambda ch: [(c["a"], c["b"], c["text"], c.get("path"), c.get("merged"), c.get("piece"), c.get("pieces"),
                         c.get("page_segments")) for c in ch]
    arms = {"v0": (S.v0_chunks(pages, starts), ns["v0_chunks"](pages, starts)),
            "cross-page": (S.recursive_doc_chunks(T), ns["recursive_doc_chunks"](T))}
    rb, mb = heads["size+bold"]
    for lv, mc in ((2, 0), (3, 0), (4, 0), (4, 400)):
        arms[f"L{lv} merge {mc}"] = (S.structure_chunks(T, rb, starts, lv, 1000, mc), ns["structure_chunks"](T, mb, starts, lv, 1000, mc))
    rs, ms = heads["size"]
    arms["L3 size-only"] = (S.structure_chunks(T, rs, starts, 3, 1000, 0), ns["structure_chunks"](T, ms, starts, 3, 1000, 0))
    for name, (ref, mine) in arms.items():
        assert key_c(ref) == key_c(mine), f"chunks differ: {name}"
        if name.startswith("L"):
            lv = int(name[1])
            assert S.check_invariants(T, ref, rb if "size-only" not in name else rs, lv, 1000) == \
                ns["check_invariants"](T, mine, mb if "size-only" not in name else ms, lv, 1000)
    print("self-test PASS: notebook rules = i2_structure.py for headings (size, size+bold) and chunks: "
          + ", ".join(f"{k} {len(v[0])}" for k, v in arms.items()))


nb = nbf.v4.new_notebook()
nb.cells = CELLS
nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3 (ipykernel)", "language": "python"},
               "language_info": {"name": "python"}}
self_test()
OUT.parent.mkdir(parents=True, exist_ok=True)
nbf.validate(nb)
nbf.write(nb, str(OUT))
print(f"wrote {OUT.relative_to(WS)}: {len(CELLS)} cells ({sum(c.cell_type == 'code' for c in CELLS)} code, {len(RULES)} rules cells)")
