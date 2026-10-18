"""Build study/notebooks/C1_parsing_verify.ipynb: the "verify it yourself" notebook for C1 (document loading and parsing).

The notebook rebuilds every measured number and chart of the C1 lesson (study/lessons/C1_parsing.html) from code, one
section per lesson step (1-12; the Full-only steps 13 #repo and 14 #book have no section, but section 1 re-reads the
repo lines it quotes), and compares each value with the lesson's value in a `check(...)` line. Expected values are
copied from sources/verification/C1/C1_FACTS.md: section 1 (S1-S12, c1_measure.py, c1_crossversion.py) and section 1b
(K1-K12, c1_kit_measure.py).

The code is not re-written: this builder copies, verbatim, the module body of c1_ref.py (page records, page table,
snapshot_id, page_of, artifact counts, logged cleaning), of c1_zoo.py (the artifact zoo) and the K8 "paper" page
builder plus its helpers from c1_kit_measure.py into the notebook's library cell (extracted with `ast` at build time),
so the notebook is self-contained and the numbers come out identical. The notebook also re-checks, at run time, that
these copies still match the scripts (sha256 of each copied segment).

The two synthetic PDFs are written into a temporary directory of the operating system (never into the workspace) and
deleted in the last cell. No book PDF is opened. pypdf is not installed in the project environment, so the S11 cell
prints the recorded values and says SKIPPED. Corpus T (DEC-3) is not chosen, so its cell is SKIPPED as well.

No Groq, Cohere or Claude call, no .env read, no network, nothing installed.

Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C1/c1_build_verify_nb.py
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C1/c1_verify_nb_run.py <scratch dir> \
        > sources/verification/C1/out_c1_verify_nb_run.txt          # executes a copy in <scratch dir>
"""
import ast
import hashlib
from pathlib import Path
from textwrap import dedent

import nbformat as nbf

WS = Path(__file__).resolve().parents[3]                      # rag_learning/
HERE = Path(__file__).resolve().parent
OUT = WS / "study" / "notebooks" / "C1_parsing_verify.ipynb"

CELLS = []


def md(s):
    CELLS.append(nbf.v4.new_markdown_cell(dedent(s).strip()))


def code(s):
    CELLS.append(nbf.v4.new_code_cell(dedent(s).strip()))


# ----------------------------------------------------------------------------- verbatim copies from the C1 scripts
def segments(path, names=None, skip_imports=False):
    """Source segments of the top-level statements of `path` (docstring and `from __future__` dropped). With `names`,
    only the assignments / functions defining those names, in file order."""
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    out = []
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant):
            continue                                            # module docstring
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue
        if skip_imports and isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if names is not None:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                defined = {node.name}
            elif isinstance(node, ast.Assign):
                defined = {t.id for t in node.targets if isinstance(t, ast.Name)}
            else:
                defined = set()
            if not defined & set(names):
                continue
        seg = ast.get_source_segment(src, node, padded=False)
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.decorator_list:
            first = node.decorator_list[0].lineno - 1
            seg = "\n".join(src.splitlines()[first:node.end_lineno])
        out.append(seg)
    return out


REF_SEGS = segments(HERE / "c1_ref.py")
ZOO_SEGS = segments(HERE / "c1_zoo.py")
KIT_NAMES = ["sh", "line_starts", "rl_jumps", "nfkc_changes", "PAPER_L", "PAPER_R", "TABLE", "lig_font", "build_paper"]
KIT_SEGS = segments(HERE / "c1_kit_measure.py", KIT_NAMES, skip_imports=True)
assert len(KIT_SEGS) == len(KIT_NAMES), [s[:30] for s in KIT_SEGS]
SEG_SHA = {name: hashlib.sha256("\n\n".join(segs).encode("utf-8")).hexdigest()[:16]
           for name, segs in (("c1_ref.py", REF_SEGS), ("c1_zoo.py", ZOO_SEGS), ("c1_kit_measure.py", KIT_SEGS))}
LIBRARY = ("# ======== copied verbatim from sources/verification/C1/c1_ref.py (module body) ========\n"
           + "\n\n\n".join(REF_SEGS)
           + "\n\n\n# ======== copied verbatim from sources/verification/C1/c1_zoo.py (module body) ========\n"
           + "\n\n\n".join(ZOO_SEGS)
           + "\n\n\n# ======== copied verbatim from sources/verification/C1/c1_kit_measure.py (K8 paper page + helpers) ========\n"
           + "\n\n\n".join(KIT_SEGS)
           + "\n\n\nLIB_SHA = " + repr(SEG_SHA) + "   # sha256[:16] of each copied block, written by the builder\n")


# =====================================================================================================================
md(r"""
# C1 · Verify it yourself: loading and parsing documents

**What this is:** a notebook that rebuilds every measured number and chart of the C1 lesson from real code, so you can see each one being made and change the inputs.
**What this is not:** the lab (`labs/C1_parsing_lab.ipynb`, where you write the loader yourself) or the quiz. It makes **no API call**: no Groq, no Cohere, no Claude. Where the lesson uses an outside fact (a parser benchmark, a library's documentation), this notebook says so and does not pretend to re-measure it.

> **Do the lab first.** The library cell below contains working code for the lab's tasks (it is copied from `sources/verification/C1/c1_ref.py`). Reading it before you try the lab gives the answers away.

**How to use it.** Run all cells from the top (VS Code: *Run All*). The sections are numbered like the lesson's steps, 1 to 12. Each one has:
- a short note on what it verifies;
- a code cell that **computes** the values;
- `check(...)` lines: `PASS` means the code produced the number the lesson shows, `FAIL` means it did not, `SKIPPED` says why a check could not run here;
- an interactive chart where one is worth seeing. Hover for values.

The last cell counts the checks. The whole notebook takes well under a minute on a CPU.

**Labels used for numbers.** *measured* = computed here from a real PDF; *toy* = a synthetic PDF or string made to show one mechanism; *formula* = arithmetic on counts; *external* = from a paper or documentation, not re-run here.

**Three inputs.**
- **Corpus D**, the repo's climate PDF (`upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf`, 33 pages). Every mechanism number is measured on it. It is a clean, born-digital, one-column PDF, so it shows almost no artifacts.
- **The zoo** (toy, 5 pages, `c1_zoo.py`): each failure drawn on purpose, so the true text is known.
- **The paper page** (toy, 1 page, built in `c1_kit_measure.py`): two columns drawn column by column, as LaTeX writes a paper, with a results table that has no ruling lines.

Both toy PDFs are written into a temporary folder of your operating system and deleted at the end. No book PDF is opened.

**Where the expected values come from.** `sources/verification/C1/C1_FACTS.md`: S1–S12 (`c1_measure.py`, `c1_crossversion.py`) and §1b K1–K12 (`c1_kit_measure.py`).
""")

code(r'''
# Setup: imports, paths, check(), chart style, the PDFs. Run this cell first.
import ast
import hashlib
import importlib.metadata as imd
import importlib.util
import json
import math
import os
import re
import shutil
import sys
import tempfile
import time
import unicodedata
from pathlib import Path

import pymupdf                                        # pinned 1.26.7
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

pio.renderers.default = "plotly_mimetype"             # small outputs that VS Code draws
T0 = time.time()


def find_workspace():
    here = Path.cwd().resolve()
    for p in (here, *here.parents):
        if (p / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").is_file() and (p / "study").is_dir():
            return p
    raise FileNotFoundError("Open this notebook from inside rag_learning/.")


WS = find_workspace()
C1_DIR = WS / "sources" / "verification" / "C1"
PDF = WS.parent / "upstream" / "RAG_Techniques" / "data" / "Understanding_Climate_Change.pdf"
REPO = WS.parent / "upstream" / "RAG_Techniques"
if not PDF.is_file():
    raise FileNotFoundError(f"Corpus D is missing: expected the repo's climate PDF at {PDF}. "
                            "It ships with upstream/RAG_Techniques (pinned 009adba2); restore that folder.")
TMP = Path(tempfile.mkdtemp(prefix="c1_verify_"))      # the two toy PDFs go here, outside the workspace
print("workspace:", WS)
print("temporary folder for the toy PDFs:", TMP)
print("python", sys.version.split()[0], {p: imd.version(p) for p in ("pymupdf", "plotly")},
      "| unicodedata", unicodedata.unidata_version)

# ---------------------------------------------------------------- check(): computed value vs the lesson's value
CHECKS, SKIPPED = [], []


def _show(x):
    if isinstance(x, list):
        return "[" + ", ".join(_show(v) for v in x) + "]"
    if isinstance(x, tuple):
        return "(" + ", ".join(_show(v) for v in x) + ")"
    if isinstance(x, dict):
        return "{" + ", ".join(f"{_show(k)}: {_show(v)}" for k, v in x.items()) + "}"
    return repr(x)


def check(name, got, expected):
    """PASS when the computed value equals the lesson's value exactly (tuples and lists compare as lists)."""
    norm = lambda v: json.loads(json.dumps(v, ensure_ascii=False, default=str))
    ok = norm(got) == norm(expected)
    CHECKS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}: got {_show(got)}  |  lesson {_show(expected)}")


def skip(name, reason):
    SKIPPED.append((name, reason))
    print(f"SKIPPED  {name}: {reason}")


# ---------------------------------------------------------------- chart style (light surface, fixed colour order)
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"    # categorical slots 1-3, always in this order
pio.templates["c1"] = go.layout.Template(layout=dict(
    font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', size=13, color=INK2),
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, colorway=[BLUE, ORANGE, AQUA],
    xaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    yaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=INK2)),
    title=dict(x=0, xanchor="left", font=dict(size=15, color=INK)),
    margin=dict(l=70, r=30, t=90, b=60), hoverlabel=dict(font_size=12)))
pio.templates.default = "c1"


def bar_style(colour):
    return dict(color=colour, line=dict(width=2, color=SURFACE))


# ---------------------------------------------------------------- environment and input (K1, S1)
check("environment: pymupdf version (pinned; K1, S1)", pymupdf.VersionBind, "1.26.7")
check("environment: Unicode database of this Python (K1)", unicodedata.unidata_version, "15.0.0")
pdf_bytes = PDF.read_bytes()
check("Corpus D sha256, bytes (S1)", [hashlib.sha256(pdf_bytes).hexdigest(), len(pdf_bytes)],
      ["1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669", 206372])
''')

md(r"""
### The library cell (copied, not re-written)

The next cell holds the code the facts were measured with, copied word for word by the builder (`sources/verification/C1/c1_build_verify_nb.py`):
- `c1_ref.py`: `Page`, `load_pages`, `build_page_table`, `snapshot_id` (06 §5.3), `build_manifest`, `validate_snapshot`, `page_of`, `artifact_counts`, `repeated_lines`, the logged cleaning rules (`plan_edits`, `apply_edits`, `undo_edits`) and `extract_columns`;
- `c1_zoo.py`: `build_zoo`, the 5-page toy PDF;
- `c1_kit_measure.py`: `build_paper` (the toy paper page of K8) and the helpers `line_starts`, `rl_jumps` (right→left jumps) and `nfkc_changes`.

It defines functions only. The cell after it checks that the copies still match the scripts.
""")
code(LIBRARY)
code(r'''
# Do the copies above still match the scripts? (sha256 of each copied block, recomputed from the files)
def _segments(path, names=None, skip_imports=False):
    src = path.read_text(encoding="utf-8")
    out = []
    for node in ast.parse(src).body:
        if isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant):
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue
        if skip_imports and isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if names is not None:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                defined = {node.name}
            elif isinstance(node, ast.Assign):
                defined = {t.id for t in node.targets if isinstance(t, ast.Name)}
            else:
                defined = set()
            if not defined & set(names):
                continue
        seg = ast.get_source_segment(src, node, padded=False)
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.decorator_list:
            seg = "\n".join(src.splitlines()[node.decorator_list[0].lineno - 1:node.end_lineno])
        out.append(seg)
    return out


KIT_NAMES = ["sh", "line_starts", "rl_jumps", "nfkc_changes", "PAPER_L", "PAPER_R", "TABLE", "lig_font", "build_paper"]
if all((C1_DIR / f).is_file() for f in LIB_SHA):
    now = {f: hashlib.sha256("\n\n".join(_segments(C1_DIR / f, *((KIT_NAMES, True) if f == "c1_kit_measure.py" else ())))
                             .encode("utf-8")).hexdigest()[:16] for f in LIB_SHA}
    check("library cell = the code of c1_ref.py, c1_zoo.py, c1_kit_measure.py", now, LIB_SHA)
else:
    skip("library cell = the scripts", f"scripts not found in {C1_DIR}")

# Corpus D, loaded once: the 33 page records, doc_text and the page table (used by every section)
pages = load_pages(str(PDF), "climate")
texts = [p.text for p in pages]
doc_text, table = build_page_table(texts)
DOC = pymupdf.open(PDF)
# the two toy PDFs
zoo = pymupdf.open(build_zoo(str(TMP / "c1_zoo.pdf")))
zt = [p.get_text() for p in zoo]
paper = pymupdf.open(build_paper(str(TMP / "c1_paper.pdf")))
pg = paper[0]
dflt = pg.get_text()
print(f"setup done in {time.time() - T0:.1f} s: Corpus D {len(pages)} pages, zoo {len(zoo)} pages, paper 1 page")
''')

# =====================================================================================================================
md(r"""
## 1 · Three silent problems

**What this verifies** (lesson step 1, `#lost`; facts S4, S6, S9, S11, K2).

**Setup.** The repo loads a PDF with `read_pdf_to_string` (`helper_functions.py` L223–L245): open the file, add each page's `get_text()` to one string, return the string.

**Result.** The string has **72,561** characters and nothing else: no page numbers. Page 2 starts at 2,424 in it, but at 2,425 in our `doc_text`, which puts one `"\n"` between pages; by page 33 the gap has grown to 32 (71,925 vs 71,957). The first "Paris Agreement" sits at offset **13,420** of `doc_text`. In the glued string it is at 13,420 − 5 = 13,415 (formula: five joins come before page 6), and the string cannot say which page that is.

**What it means.** Three problems, none of which raises an error:
1. **The page is lost.** A chunk cut from this string cannot cite its page.
2. **The offsets depend on the library.** pypdf reads the same 33 pages with the same words in the same order, yet **0 of 33** pages are identical character for character (S11): every pypdf page lacks PyMuPDF's final `"\n"`. A gold label stored as character offsets only fits the text it was made on.
3. **Text that is not there.** A page can come back as `''`. Section 2 shows the two reasons (blank page, image-only page).

The pypdf comparison runs only if `pypdf` is installed. It is **not** installed in this project (and must not be installed for this), so the cell prints the values recorded on 2026-10-08 in a separate throwaway environment and says SKIPPED.
""")
code(r'''
def read_pdf_to_string(path):                        # helper_functions.py L223-L245, re-typed without its comments
    doc = pymupdf.open(path)
    content = ""
    for page_num in range(len(doc)):
        content += doc[page_num].get_text()
    return content


glued = read_pdf_to_string(PDF)
check("§1 read_pdf_to_string length (S4)", len(glued), 72561)
check("§1 it returns one str: no page field at all", type(glued).__name__, "str")
check("§1 page 2 start: glued vs doc_text (S4)", [len(texts[0]), table[1]["doc_char_start"]], [2424, 2425])
check("§1 page 33 start: glued vs doc_text (S4)", [sum(map(len, texts[:32])), table[32]["doc_char_start"]], [71925, 71957])
first = doc_text.find("Paris Agreement")
check("§1 first 'Paris Agreement': doc_text offset (S6); glued offset = 13,420 - 5 joins (formula)",
      [first, glued.find("Paris Agreement")], [13420, 13420 - 5])

# the repo lines the lesson quotes (read-only; short code lines only)
hf = REPO / "helper_functions.py"
if hf.is_file():
    L = hf.read_text(encoding="utf-8").splitlines()
    quoted = {237: "doc = fitz.open(path)", 244: "content += page.get_text()", 62: "loader = PyPDFLoader(path)",
              69: "texts = text_splitter.split_documents(documents)", 70: "cleaned_texts = replace_t_with_space(texts)"}
    for n, s in quoted.items():
        print(f"   helper_functions.py L{n}: {L[n - 1].strip()}")
    check("§1 repo lines L237, L244 (glue pages), L62, L69, L70 (load, split, then clean) (S-src)",
          [L[n - 1].strip() for n in quoted], list(quoted.values()))
else:
    skip("§1 repo lines", f"{hf} not found")

# S11: pypdf vs PyMuPDF, optional
if importlib.util.find_spec("pypdf") is not None:
    import pypdf
    pp = [p.extract_text() for p in pypdf.PdfReader(str(PDF)).pages]
    words = lambda s: re.findall(r"\w+", s)
    print("   pypdf", pypdf.__version__, "(the recorded values are for pypdf 6.19.0)")
    check("§1 pypdf vs PyMuPDF: identical pages / same word sequence / PyMuPDF page = pypdf page + '\\n' (S11)",
          [sum(a == b for a, b in zip(pp, texts)), sum(words(a) == words(b) for a, b in zip(pp, texts)),
           sum(b == a + "\n" for a, b in zip(pp, texts))], [0, 33, 33])
    check("§1 pypdf joined length (S11)", len("\n".join(pp)), 72560)
else:
    print("   recorded on 2026-10-08 (S11; pypdf 6.19.0 in a throwaway environment outside the workspace):")
    print("     pages with identical text, pypdf vs PyMuPDF: 0 of 33")
    print("     pages with the same word sequence: 33 of 33")
    print("     PyMuPDF page == pypdf page + '\\n': 33 of 33 | pypdf joined with '\\n': 72,560 characters")
    skip("§1 pypdf vs PyMuPDF (S11)", "pypdf is not installed in this environment (do not install it here); "
         "the recorded values are printed above")
''')

# =====================================================================================================================
md(r"""
## 2 · What a PDF page is

**What this verifies** (lesson step 2, `#page`; facts S4, S9, K7).

**Setup.** A PDF page does not store paragraphs or a reading order. It stores drawing commands: put this glyph at this x, y. A parser walks those commands in the order the file lists them (the content stream) and guesses lines and words from the positions. A **born-digital** PDF (made by a program) has this text layer. A **scanned** PDF is a picture of a page with no text layer; only OCR can make one, with its own errors (that is concept S2, not C1).

**Result.** On the zoo:
- characters per page **273, 74, 0, 0, 101**; images per page **0, 0, 0, 1, 0**;
- page 3 has 0 characters and 0 images: a **blank** page;
- page 4 has 0 characters and 1 image: an **image-only** page (a scan, here a picture of one sentence);
- page 1's lines start at two x positions (72 and 320), and the default extraction walks them across the page: header, footer, then left 1, right 1, left 2, right 2, …

On Corpus D every text block starts at x = 72 (one column) and there are 0 images.

**What it means.** `chars = 0` is not one problem but two, and the image count tells them apart: with images it is a page to OCR, without images it is a blank page to ignore.
""")
code(r'''
check("§2 zoo characters per page (S9, K7)", [len(t) for t in zt], [273, 74, 0, 0, 101])
check("§2 zoo images per page (S9, K7)", [len(p.get_images()) for p in zoo], [0, 0, 0, 1, 0])


def kind(chars, images):
    return "text" if chars else ("image-only" if images else "blank")


check("§2 zoo page kinds by chars and images (S9)", [kind(len(t), len(p.get_images())) for t, p in zip(zt, zoo)],
      ["text", "text", "blank", "image-only", "text"])
check("§2 zoo p.3 and p.4 text (S9)", [zt[2], zt[3]], ["", ""])

print("   zoo p.1, each line as the parser walks it: (x, y) and the first characters")
for x, y, t in line_starts(zoo[0]):
    print(f"     x={x:6.1f}  y={y:6.1f}  {t[:40]}")
lab = lambda s: ("L" + str(ZOO_LEFT.index(s) + 1)) if s in ZOO_LEFT else ("R" + str(ZOO_RIGHT.index(s) + 1)) \
    if s in ZOO_RIGHT else s[:12]
check("§2 zoo p.1 line order (K7)", [lab(l[2]) for l in line_starts(zoo[0])],
      ["ACME Technic", "Page 1", "L1", "R1", "L2", "R2", "L3", "R3", "L4", "R4", "The ﬁrst ﬂag"])
check("§2 Corpus D: distinct text-block x0 values, images (S4)",
      [sorted({round(b[0]) for p in DOC for b in p.get_text("blocks") if b[6] == 0}),
       sum(len(p.get_images()) for p in DOC)], [[72], 0])
''')

# =====================================================================================================================
md(r"""
## 3 · One record per page, numbered from 1

**What this verifies** (lesson step 3, `#records`; facts S2, S4, K2, K9).

**Setup.** v0 keeps one record per page: `Page(doc_id, page, text, parser)`. `text` is the raw `page.get_text()`; `page` counts from 1, like the page numbers a person sees. PyMuPDF itself counts from 0 (`doc[0]` is page 1).

**Result** (measured, Corpus D):
- **33** records, pages 1 to 33; shortest page 33 (**636** characters), longest page 19 (**2,494**); total **72,561** characters;
- every page ends with `"\n"`;
- `.strip()` on each page (as the repo's captioning notebook does) removes **70** characters (72,491 left);
- **the 37-character gap.** The 07 lab's `PyPDFLoader` text had 72,523 characters, pypdf's raw pages joined 72,560: 37 fewer. pypdf's pages are PyMuPDF's minus the final `"\n"` (S11), so their sum is 72,561 − 33 = 72,528. `.strip()` on each page removes 37 more (all trailing spaces before the final newline, none at the start): 72,491, and joined with 32 `"\n"`, **72,523**. The loader strips each page (K2).

**What it means.** A one-line loader can carry three bugs: 0-based page numbers, a silent `.strip()` that moves every later offset, and no record of which parser and version made the text. Characters are not tokens either: these counts are `len()` of a Python string (P1).

**The chart** follows one document's character count through the three ways of reading it.
""")
code(r'''
check("§3 records, first and last page number (S2)", [len(pages), pages[0].page, pages[-1].page], [33, 1, 33])
check("§3 record fields and parser (S2)", [list(Page.__dataclass_fields__), pages[0].doc_id, pages[0].parser],
      [["doc_id", "page", "text", "parser"], "climate", "pymupdf 1.26.7"])
check("§3 PyMuPDF index 0 is our page 1", DOC[0].get_text() == pages[0].text and pages[0].page == 1, True)
lens = [len(t) for t in texts]
check("§3 shortest, longest page (page, chars) and total (S2)",
      [(lens.index(min(lens)) + 1, min(lens)), (lens.index(max(lens)) + 1, max(lens)), sum(lens)],
      [(33, 636), (19, 2494), 72561])
check("§3 characters per page (K9)", lens,
      [2424, 2410, 2183, 2269, 2255, 2389, 2137, 2225, 2254, 2077, 2116, 2216, 2215, 2252, 2217, 2125, 2144, 2035,
       2494, 2257, 2298, 2195, 2204, 2266, 2167, 2388, 2087, 2238, 2468, 2309, 2166, 2445, 636])
check("§3 every page ends with '\\n' (S2)", all(t.endswith("\n") for t in texts), True)

raw_sum = sum(lens)
no_final_nl = sum(len(t[:-1]) for t in texts)        # = pypdf's pages (S11)
stripped = sum(len(t.strip()) for t in texts)
check("§3 .strip() per page: chars left, removed (S4)", [stripped, raw_sum - stripped], [72491, 70])
check("§3 K2 sums: PyMuPDF, pypdf (= minus final \\n), .strip()", [raw_sum, no_final_nl, stripped], [72561, 72528, 72491])
check("§3 K2 joined with '\\n': PyMuPDF, pypdf, .strip() = PyPDFLoader's 72,523",
      [raw_sum + 32, no_final_nl + 32, stripped + 32], [72593, 72560, 72523])
check("§3 K2 removed vs pypdf, vs PyMuPDF; leading / trailing whitespace before the final \\n",
      [no_final_nl - stripped, raw_sum - stripped, sum(len(t) - len(t.lstrip()) for t in texts),
       sum(len(t[:-1]) - len(t[:-1].rstrip()) for t in texts)], [37, 70, 0, 37])

fig = go.Figure(go.Bar(
    y=["PyMuPDF get_text() (v0)", "pypdf extract_text()", "PyPDFLoader: pypdf + .strip() per page"],
    x=[0, raw_sum - no_final_nl, raw_sum - stripped], orientation="h", marker=bar_style(BLUE),
    text=[f"{raw_sum:,} chars", f"{no_final_nl:,} chars (−33: no final \\n per page)",
          f"{stripped:,} chars (−70 = 33 + 37 stripped)"], textposition="outside",
    hovertemplate="%{y}<br>characters removed vs PyMuPDF: %{x}<extra></extra>"))
fig.update_layout(height=300, title="§3 · Same 33 pages, three character counts (measured, Corpus D; K2)",
                  xaxis=dict(title="characters removed compared with PyMuPDF's raw pages", range=[0, 120]),
                  yaxis=dict(autorange="reversed"), margin=dict(l=260, r=30, t=70, b=60))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 4 · One coordinate system: the page table

**What this verifies** (lesson step 4, `#offsets`; facts S2, S6, S12, K10).

**Setup.** `doc_text = "\n".join(pages)`. The page table stores, for each page, where its text starts and ends in `doc_text`: `[start, end)`, end not included. Each page starts at the previous end + 1 (the join). The join character after page *p* belongs to page *p*. A gold label is a span `[start, end)` of this one text, so this table is how any offset finds its page.

**Result** (measured, Corpus D):
- `len(doc_text)` = 72,561 + 32 joins = **72,593**;
- rows: p.1 [0, 2,424), p.2 [2,425, 4,835), p.3 [4,836, 7,019), …, p.33 [71,957, 72,593);
- `doc_text[start:end]` gives back each page exactly (all 33);
- offset 2,424 (the join) → page 1, offset 2,424; offset 2,425 → page 2, offset 0;
- "Paris Agreement" at 13,420 → **page 6, offset 1,874**; it occurs 8 times, on pages 6, 10, 23, 24;
- `"\n\n"` occurs 32 times, every one at a page join (each page's own final `"\n"` plus the join).

**Toy arithmetic** (formula, K10): page lengths 100, 50, 80 → starts 0, 100 + 1 = 101, 101 + 50 + 1 = **152**; total 232.
""")
code(r'''
check("§4 len(doc_text) = sum + 32 joins (S2)", [len(doc_text), len(doc_text) == sum(lens) + 32], [72593, True])
check("§4 doc_text sha256 (S2)", sha256_hex(doc_text), "5106772efa77003b0d6c79bc1a429b8dacf244d9556f412bae1c4fe6bc7368c6")
rows = lambda tbl, ps: [(tbl[p - 1]["page"], tbl[p - 1]["doc_char_start"], tbl[p - 1]["doc_char_end"]) for p in ps]
check("§4 rows p.1-p.3 and p.33 (S2)", rows(table, [1, 2, 3, 33]),
      [(1, 0, 2424), (2, 2425, 4835), (3, 4836, 7019), (33, 71957, 72593)])
check("§4 starts of p.8, p.10, p.23, p.29 (S2)", [table[p - 1]["doc_char_start"] for p in (8, 10, 23, 29)],
      [16074, 20555, 49209, 62565])
check("§4 start = previous end + 1 on every row", all(b["doc_char_start"] == a["doc_char_end"] + 1
                                                      for a, b in zip(table, table[1:])), True)
check("§4 round trip doc_text[s:e] == page, all pages (S2)",
      all(doc_text[r["doc_char_start"]:r["doc_char_end"]] == t for r, t in zip(table, texts)), True)
check("§4 page_of 2,424 / 2,425 / 0 / 72,592 (S6)", [page_of(o, table) for o in (2424, 2425, 0, 72592)],
      [(1, 2424), (2, 0), (1, 0), (33, 635)])
check("§4 'Paris Agreement' 13,420 -> (page, offset) (S6)", page_of(first, table), (6, 1874))
check("§4 'Paris Agreement' pages, occurrences (S6)",
      [sorted({page_of(m.start(), table)[0] for m in re.finditer("Paris Agreement", doc_text)}),
       doc_text.count("Paris Agreement")], [[6, 10, 23, 24], 8])
check("§4 '\\n\\n' in doc_text / at page joins (S2)",
      [doc_text.count("\n\n"), sum(doc_text[r["doc_char_end"] - 1:r["doc_char_end"] + 1] == "\n\n" for r in table[:-1])],
      [32, 32])

# toy arithmetic (K10) and Part F (S12)
_, t3 = build_page_table(["x" * (n - 1) + "\n" for n in (100, 50, 80)])
check("§4 toy lengths 100, 50, 80 -> rows (K10)", rows(t3, [1, 2, 3]), [(1, 0, 100), (2, 101, 151), (3, 152, 232)])
toy3 = ["Ice melts.\n", "Seas rise.\n", "Act now.\n"]
tdoc, trows = build_page_table(toy3)
check("§4 Part F toy: doc_text length, rows (S12, K10)", [len(tdoc), rows(trows, [1, 2, 3])],
      [33, [(1, 0, 11), (2, 12, 23), (3, 24, 33)]])
check("§4 Part F page_of 10, 11, 12, 17, 30 (S12)", [page_of(o, trows) for o in (10, 11, 12, 17, 30)],
      [(1, 10), (1, 11), (2, 0), (2, 5), (3, 6)])
''')

# =====================================================================================================================
md(r"""
## 5 · Freeze the text: the snapshot id

**What this verifies** (lesson step 5, `#snapshot`; facts S2, S3, S7, S12, K5, K10).

**Setup.** A **hash** turns any text into a short fixed-length value; change one byte and the value changes completely. The snapshot id (06 §5.3) hashes five inputs together: the parser and its version, the parser options, the cleaning version, the page join, and the sha256 of each document's text. It is the name of one exact frozen text.

**Result.**
- Hashes of toy strings (sha256, first 12 hex): `"Seas rise.\n"` 63c2941c7f6b; one extra space b1e07b17c9c7; `"\r\n"` a71b05c14df5; lower-case s 2d04a7947fc7 (K5).
- Corpus D's snapshot id is **`ea07572562ac`**, the value published in 06 §5.3 (S2).
- Change one input and keep the text: version 1.28.2 → 4b7e61b9e418; cleaning `tabs_v1` → 6164dfc95324; options `{"sort": true}` → f1e46e7c3c68; one extra space at the end of page 1 → a79df757e413; `page_join` read as a real newline instead of the two characters `\n` → 5ad6acfd28ec (S3).
- The manifest validates; shift page 2 by one character and it is rejected (S7).
- **One page added at the end** (toy, K10): lengths 100, 50, 80 plus 40 → rows 1–3 stay as they were, row 4 is (4, 233, 273); the text hash, so the id, changes. Labels made on the old snapshot must be re-bound to the new id (06 §5.3 rule 3), even though their offsets still point at the same characters.

**What it means.** The PDF's own sha256 locks the file's bytes. The snapshot id locks the **text** you label and index. The same PDF gives a different text under another parser, version or option, and the id says so.
""")
code(r'''
K5 = {"Seas rise.\n": "63c2941c7f6b", "Seas rise. \n": "b1e07b17c9c7", "Seas rise.\r\n": "a71b05c14df5",
      "seas rise.\n": "2d04a7947fc7"}
check("§5 sha256[:12] of four toy strings (K5)", {s: sh(s) for s in K5}, K5)
dsha = sha256_hex(doc_text)
check("§5 parser block (S2)", parser_info(),
      {"backend": "pymupdf", "version": "1.26.7", "call": "page.get_text()", "options": {}})
sid = snapshot_id("pymupdf", pymupdf.VersionBind, {}, "none", {"climate": dsha})
check("§5 Corpus D snapshot_id = 06 §5.3 (S2)", sid, "ea07572562ac")

one = texts[:]
one[0] = one[0] + " "
parts_nl = ["snapshot-v1", "parser=pymupdf@1.26.7", "options={}", "cleaning=none", "page_join=\n", f"climate:{dsha}"]
S3 = {"version 1.28.2": snapshot_id("pymupdf", "1.28.2", {}, "none", {"climate": dsha}),
      "cleaning tabs_v1": snapshot_id("pymupdf", "1.26.7", {}, "tabs_v1", {"climate": dsha}),
      "options sort=True": snapshot_id("pymupdf", "1.26.7", {"sort": True}, "none", {"climate": dsha}),
      "one extra space, page 1": snapshot_id("pymupdf", "1.26.7", {}, "none", {"climate": sha256_hex(build_page_table(one)[0])}),
      "page_join as a real newline": hashlib.sha256("|".join(parts_nl).encode()).hexdigest()[:12]}
check("§5 one change, new id (S3)", S3,
      {"version 1.28.2": "4b7e61b9e418", "cleaning tabs_v1": "6164dfc95324", "options sort=True": "f1e46e7c3c68",
       "one extra space, page 1": "a79df757e413", "page_join as a real newline": "5ad6acfd28ec"})
check("§5 tabs in Corpus D; replace_t_with_space would change the text (S3)",
      [sum(t.count("\t") for t in texts), [t.replace("\t", " ") for t in texts] != texts], [0, False])

man = build_manifest("D", "1.0", [{"doc_id": "climate", "pdf_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
                                    "bytes": len(pdf_bytes), "pages": 33, "doc_text_sha256": dsha, "page_table": table}],
                     parser_info(), CLEANING_NONE, "2026-10-08T00:00:00Z")
validate_snapshot(man, {"climate": doc_text})
bad = json.loads(json.dumps(man))
bad["docs"][0]["page_table"][1]["doc_char_start"] += 1
bad["docs"][0]["page_table"][1]["doc_char_end"] += 1
try:
    validate_snapshot(bad, {"climate": doc_text})
    msg = "accepted"
except ValueError as e:
    msg = str(e)
check("§5 manifest validates (id); page 2 shifted by +1 is rejected (S7)", [man["snapshot_id"], msg],
      ["ea07572562ac", "climate p.2: start != previous end + len(page_join)"])

# one page added at the end (K10), and page 1 doubled (S12)
L3, L4 = ["x" * (n - 1) + "\n" for n in (100, 50, 80)], ["x" * (n - 1) + "\n" for n in (100, 50, 80, 40)]
d3, r3 = build_page_table(L3)
d4, r4 = build_page_table(L4)
tid = lambda d: snapshot_id("pymupdf", "1.26.7", {}, "none", {"toy": sha256_hex(d)})
check("§5 a 4th page of 40: rows 1-3 unchanged, row 4, total, id changes (K10)",
      [r4[:3] == r3, rows(r4, [4]), len(d4), tid(d3) != tid(d4)], [True, [(4, 233, 273)], 273, True])
bdoc, brows = build_page_table(["Ice melts.\n" * 2, "Seas rise.\n", "Act now.\n"])
check("§5 Part F page 1 doubled: page 2 start, length, id changes (S12)",
      [brows[1]["doc_char_start"], len(bdoc), tid(tdoc) != tid(bdoc)], [23, 44, True])
''')

# =====================================================================================================================
md(r"""
## 6 · Characters are not bytes

**What this verifies** (lesson step 6, `#bytes`; facts S7, K3).

**Setup.** Python's `len()` counts characters (code points). A file stores UTF-8 bytes: 1 byte for ASCII, 2 to 4 for the rest. On Windows, `open(path, "w")` also turns every `"\n"` into `"\r\n"` while writing.

**Result** (measured, Corpus D):
- **72,593** characters, **72,595** UTF-8 bytes: the only non-ASCII character is one `—` (3 bytes, so +2);
- 1,132 newlines; written with plain `open(..., "w")` on Windows the file has **73,727** bytes (72,595 + 1,132) and its sha256 no longer equals `doc_text`'s; written with `newline="\n"` it has **72,595** bytes and the same hash;
- reading the plain file back in text mode turns `"\r\n"` back into `"\n"` and hides the problem; reading it with `newline=""` shows it.

**What it means.** Write snapshot text with `encoding="utf-8", newline="\n"`, and check the file's hash, not only the string's.
""")
code(r'''
check("§6 characters, UTF-8 bytes, non-ASCII characters (K3, S7)",
      [len(doc_text), len(doc_text.encode("utf-8")), sorted({c for c in doc_text if ord(c) > 127})], [72593, 72595, ["—"]])
check("§6 newlines in doc_text (S7)", doc_text.count("\n"), 1132)
p_default, p_lf = TMP / "climate_default.txt", TMP / "climate_lf.txt"
with open(p_default, "w", encoding="utf-8") as f:
    f.write(doc_text)
with open(p_lf, "w", encoding="utf-8", newline="\n") as f:
    f.write(doc_text)
fsha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
check("§6 newline='\\n': bytes, file hash == doc_text hash (S7)", [p_lf.stat().st_size, fsha(p_lf) == dsha], [72595, True])
if os.name == "nt":
    check("§6 Windows: os.linesep; plain open(): bytes, hash equal (S7)",
          [os.linesep, p_default.stat().st_size, fsha(p_default) == dsha], ["\r\n", 73727, False])
    check("§6 read back in text mode == doc_text; with newline='' == doc_text (S7)",
          [p_default.read_text(encoding="utf-8") == doc_text, open(p_default, encoding="utf-8", newline="").read() == doc_text],
          [True, False])
else:
    skip("§6 plain open() on Windows (S7)", f"this computer is not Windows (os.linesep {os.linesep!r}); "
         "the recorded Windows values are 73,727 bytes and a different hash")
''')

# =====================================================================================================================
md(r"""
## 7 · The artifact catalogue, and one check for each

**What this verifies** (lesson step 7, `#artifacts`; facts S4, S5, S9, K6, K7, K8, K9).

**Setup.** Each artifact has a cheap per-page signal: characters and images (blank or image-only pages), repeated lines (running headers and footers), right→left jumps (a line in the right half followed by one in the left half, body lines only: reading order), line-end hyphens, ligature characters (`ﬁ`, `ﬂ`), ruled tables found by `find_tables()`.

**Result, Corpus D** (measured, K9, S5): 0 images, 0 right→left jumps, 0 ligatures, 0 ruled tables, no repeated lines (threshold 17, and none even at 3 pages). 7 line-end hyphens, on pages 8, 11, 12, 19, 29 (2) and 31, and all 7 are real compounds: the hyphenated form (`well-being`) occurs elsewhere in the text, the joined form (`wellbeing`) never does. 24 of the 32 page breaks do not end a sentence; on 8 of them the next page starts in lower case (a sentence cut by the page).

**Result, the zoo** (toy, K7, S9): header "ACME Technical Report" and footer "Page #" on 3 pages each; page 1's two columns come out line by line across the page (**4** right→left jumps); `sort=True` puts both columns on one line; clipping each column gives the true order; PyMuPDF's `TEXT_DEHYPHENATE` joins `extrac-` to the next line *in the parser's order*, which is the wrong column; page 2's ruled table is found by `find_tables()` (3 × 2, correct) while `get_text()` gives one cell per line.

**Result, the paper page** (toy, K8): drawn column by column, the default order is **correct** (left column, then right column) with **1** right→left jump (right column → table). `sort=True`, which sorts by position, now **breaks** it: 3 lines mix words of both columns. The unruled table: `find_tables()` with ruling lines finds 0; `strategy="text"` finds 1 "table" of 23 × 9 cells that takes in the page's text. `get_text()` gives the table one cell per line.

**What it means.** Reading order follows the order the file was written in. LaTeX papers write column by column and mostly come out right; producers that write line by line across the page do not. One option (`sort=True`) fixes one producer and breaks the other, so check per corpus. A figure is invisible: text extraction returns no words for it (Ch16 p.1/11).

**The charts:** the per-page signals of the zoo and the paper page, then Corpus D's characters per page with its hyphen breaks marked.
""")
code(r'''
# ---------- Corpus D (S5, K9, S4)
a = artifact_counts(texts)
check("§7 D: empty pages, ligatures, soft hyphens, tabs, '\\n\\n' inside pages (S5)",
      [a["empty_pages"], a["ligatures"], a["soft_hyphens"], a["tabs"], a["double_newlines"]], [[], 0, 0, 0, 0])
check("§7 D: lines, lines ending with a space, non-ASCII (S5)", [a["lines"], a["lines_ending_space"], a["non_ascii"]],
      [1100, 1093, {"—": 1}])
check("§7 D: line-end hyphen breaks (S5)", [(p, s.replace("\n", "|")) for p, s in a["hyphen_breaks"]],
      [(8, "cost-|competitive"), (11, "well-|being"), (12, "Public-|private"), (19, "well-|being"),
       (29, "market-|based"), (29, "climate-|friendly"), (31, "decision-|making")])
vocab = {w.lower() for t in texts for w in re.findall(r"[A-Za-z]+", t)}
joined = [s.replace("-\n", "").lower() in vocab for _, s in a["hyphen_breaks"]]
hyph = [s.replace("\n", "").lower() in doc_text.lower() for _, s in a["hyphen_breaks"]]
check("§7 D: joined form attested elsewhere / hyphenated form attested (S5)", [sum(joined), sum(hyph)], [0, 7])
hb = {i: len(HYPHEN_BREAK.findall(t)) for i, t in enumerate(texts, 1) if HYPHEN_BREAK.findall(t)}
check("§7 D: hyphen breaks per page (K9)", hb, {8: 1, 11: 1, 12: 1, 19: 1, 29: 2, 31: 1})
thr, rep = repeated_lines(texts)
c3 = {}
for t in texts:
    for k in {line_key(x) for x in t.split("\n") if x.strip()}:
        c3[k] = c3.get(k, 0) + 1
check("§7 D: repeated-line threshold, lines over it, lines on >= 3 pages (S5)",
      [thr, rep, {k: v for k, v in c3.items() if v >= 3}], [17, {}, {}])
ends = [t.rstrip() for t in texts]
nonterm = [i for i, t in enumerate(ends[:-1], 1) if t and t[-1] not in '.!?:")\'']
lower_next = [f"{i}->{i + 1}" for i in nonterm if texts[i].lstrip()[:1].islower()]
check("§7 D: page breaks not ending a sentence; next page starts lower case (S5)", [len(nonterm), lower_next],
      [24, ["12->13", "14->15", "15->16", "16->17", "21->22", "22->23", "24->25", "28->29"]])
check("§7 D: images, right->left jumps per page (sets), ruled tables (K9)",
      [sorted({len(p.get_images()) for p in DOC}), sorted({rl_jumps(p) for p in DOC}),
       sum(len(p.find_tables().tables) for p in DOC)], [[0], [0], 0])
check("§7 D: U+FFFD, '(cid:' strings (K9)", [doc_text.count("�"), doc_text.count("(cid:")], [0, 0])
check("§7 D: get_text('text') == get_text(); sort=True differs; same after whitespace collapse (S4)",
      [sum(p.get_text("text") == t for p, t in zip(DOC, texts)), sum(p.get_text(sort=True) != t for p, t in zip(DOC, texts)),
       sum(re.sub(r"\s+", " ", p.get_text(sort=True)).strip() == re.sub(r"\s+", " ", t).strip() for p, t in zip(DOC, texts))],
      [33, 33, 33])
''')
code(r'''
# ---------- the zoo (S9, K6, K7)
zthr, zrep = repeated_lines(zt)
check("§7 zoo: repeated-line threshold and lines (S9, K7)", [zthr, zrep],
      [3, {"ACME Technical Report": 3, "Page #": 3}])
ZSIG = []
for i, p in enumerate(zoo, 1):
    t = zt[i - 1]
    ZSIG.append([i, len(t), len(p.get_images()), sum(t.count(c) for c in LIGATURES), len(HYPHEN_BREAK.findall(t)),
                 rl_jumps(p), len(p.find_tables().tables), nfkc_changes(t)[1]])
print("   page | chars | images | ligatures | hyphen breaks | R->L jumps | ruled tables | NFKC delta")
for r in ZSIG:
    print("   " + " | ".join(str(v) for v in r))
check("§7 zoo per-page signals (K7)", ZSIG,
      [[1, 273, 0, 3, 1, 4, 0, 3], [2, 74, 0, 0, 0, 0, 1, 0], [3, 0, 0, 0, 0, 0, 0, 0], [4, 0, 1, 0, 0, 0, 0, 0],
       [5, 101, 0, 0, 0, 0, 0, 0]])
truth = ZOO_LEFT + ZOO_RIGHT
srt = zoo[0].get_text(sort=True)
check("§7 zoo p.1: default order is true order? sort=True puts both columns on one line? clip by column true? (S9)",
      [[x for x in zt[0].split("\n") if x in truth] == truth,
       any(ZOO_LEFT[0] in x and ZOO_RIGHT[0] in x for x in srt.split("\n")),
       [x for x in extract_columns(zoo[0]).split("\n") if x in truth] == truth], [False, True, True])
DEH = pymupdf.TEXTFLAGS_TEXT | pymupdf.TEXT_DEHYPHENATE
check("§7 zoo p.1 TEXT_DEHYPHENATE: default order / with the left-column clip (S9)",
      [[x for x in zoo[0].get_text(flags=DEH).split("\n") if "extrac" in x],
       [x for x in zoo[0].get_text(clip=pymupdf.Rect(0, 0, 297.5, 842), flags=DEH).split("\n") if "extrac" in x]],
      [["by any later extracreading order must follow"], ["by any later extraction or retrieval step."]])
check("§7 K6: TEXTFLAGS_TEXT and its bits",
      [pymupdf.TEXTFLAGS_TEXT, {n: bool(pymupdf.TEXTFLAGS_TEXT & getattr(pymupdf, n)) for n in
       ("TEXT_PRESERVE_LIGATURES", "TEXT_PRESERVE_WHITESPACE", "TEXT_PRESERVE_IMAGES", "TEXT_DEHYPHENATE",
        "TEXT_MEDIABOX_CLIP", "TEXT_CID_FOR_UNKNOWN_UNICODE")}, pymupdf.TEXT_DEHYPHENATE],
      [195, {"TEXT_PRESERVE_LIGATURES": True, "TEXT_PRESERVE_WHITESPACE": True, "TEXT_PRESERVE_IMAGES": False,
             "TEXT_DEHYPHENATE": False, "TEXT_MEDIABOX_CLIP": True, "TEXT_CID_FOR_UNKNOWN_UNICODE": True}, 16])
lig_line = [x for x in zt[0].split("\n") if "flag" in unicodedata.normalize("NFKC", x)][0]
nolig = zoo[0].get_text(flags=pymupdf.TEXTFLAGS_TEXT & ~pymupdf.TEXT_PRESERVE_LIGATURES)
check("§7 zoo p.1 ligatures: count, 'file' found, after NFKC, without PRESERVE_LIGATURES (S9)",
      [sum(lig_line.count(c) for c in LIGATURES), "file" in lig_line, "file" in unicodedata.normalize("NFKC", lig_line),
       sum(nolig.count(c) for c in LIGATURES)], [3, False, True, 0])
check("§7 zoo p.2: get_text() one cell per line; find_tables() (S9)",
      [zt[1].split("\n"), [t.extract() for t in zoo[1].find_tables().tables]],
      [["ACME Technical Report", "Page 2", "Model", "Max tokens", "MiniLM-L6", "256", "bge-small", "512", ""],
       [[["Model", "Max tokens"], ["MiniLM-L6", "256"], ["bge-small", "512"]]]])
''')
code(r'''
# ---------- the paper page (K8)
check("§7 paper: page text sha256[:12] (K12; the page this notebook built is the one measured)", sh(dflt), "4033785d96eb")
print("   default text, first 5 lines:", dflt.split("\n")[:5])
check("§7 paper: default order puts the left column before the right; R->L jumps (K8)",
      [dflt.index(PAPER_L[-1]) < dflt.index(PAPER_R[0]), rl_jumps(pg)], [True, 1])
psrt = pg.get_text(sort=True)
mixed = [ln for ln in psrt.split("\n") if any(w in ln for w in ("Dense retrieval", "to a vector", "ones to the"))
         and any(w in ln for w in ("Table 1", "dense model", "of the five"))]
print("   sort=True, the first mixed line:", repr(mixed[0][:70]) if mixed else None)
check("§7 paper: sort=True lines holding words of both columns (K8)", len(mixed), 3)
pvocab = {w.lower() for w in re.findall(r"[A-Za-z]+", dflt)}
check("§7 paper: line-end hyphens and whether the joined word occurs elsewhere (K8)",
      [(x, y, (x + y).lower() in pvocab) for x, y in HYPHEN_BREAK.findall(dflt)],
      [("accu", "racy", True), ("mar", "gin", False)])
tl_lines, tl_text = pg.find_tables(), pg.find_tables(strategy="text")
check("§7 paper: find_tables() lines strategy / text strategy, shape (K8)",
      [len(tl_lines.tables), len(tl_text.tables), (tl_text.tables[0].row_count, tl_text.tables[0].col_count)],
      [0, 1, (23, 9)])
tl = dflt.split("\n")
i0 = tl.index("Method")
check("§7 paper: the table as extracted, one cell per line (K8)", tl[i0:i0 + 12],
      ["Method", "NQ", "TQA", "SQuAD", "BM25", "59.1", "66.9", "68.8", "Dense", "78.4", "79.4", "63.2"])
check("§7 paper: ligatures, NFKC changes, NFKC delta, chars, images (K8)",
      [sum(dflt.count(c) for c in LIGATURES), *nfkc_changes(dflt), len(dflt), len(pg.get_images())], [3, 3, 3, 575, 0])

# ---------- Corpus T (DEC-3): not chosen yet
skip("§7 Corpus T per-page signals", "DEC-3 is not decided, so no Corpus T PDF exists in the course; the lesson "
     "quotes the 2026-10-17 research probe (research C1 §5.6) as 'research probe' until T is frozen and re-measured")
''')
code(r'''
# ---------- chart 1: per-page signals, zoo pages 1-5 and the paper page (small multiples, one measure per row)
def flags(chars, images, lig, hyph, jumps, tables):
    f = []
    if chars == 0:
        f.append("image-only" if images else "blank")
    f += [n for n, v in (("ligatures", lig), ("line-end hyphens", hyph), ("right→left jumps", jumps),
                         ("ruled table", tables)) if v]
    return f


SIG = [(f"zoo p.{r[0]}", r[1], r[2], flags(r[1], r[2], r[3], r[4], r[5], r[6])) for r in ZSIG]
psig = [len(dflt), len(pg.get_images()), sum(dflt.count(c) for c in LIGATURES), len(HYPHEN_BREAK.findall(dflt)),
        rl_jumps(pg), len(pg.find_tables().tables)]
SIG.append(("paper", psig[0], psig[1], flags(*psig)))
check("§7 page flags (formula on K7, K8 signals)", {n: f for n, _, _, f in SIG},
      {"zoo p.1": ["ligatures", "line-end hyphens", "right→left jumps"], "zoo p.2": ["ruled table"],
       "zoo p.3": ["blank"], "zoo p.4": ["image-only"], "zoo p.5": [],
       "paper": ["ligatures", "line-end hyphens", "right→left jumps"]})
x = [n for n, *_ in SIG]
hov = ["<br>".join(f) or "no flag" for *_, f in SIG]
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                    subplot_titles=("characters", "images", "flags (signals that fire)"))
for row, ys, colour in ((1, [s[1] for s in SIG], BLUE), (2, [s[2] for s in SIG], BLUE), (3, [len(s[3]) for s in SIG], ORANGE)):
    fig.add_bar(x=x, y=ys, row=row, col=1, marker=bar_style(colour), showlegend=False, customdata=hov,
                text=ys, textposition="outside", cliponaxis=False,
                hovertemplate="%{x}: %{y}<br>%{customdata}<extra></extra>")
fig.update_yaxes(rangemode="tozero")
fig.update_yaxes(range=[0, 340], row=1, col=1)
fig.update_yaxes(range=[0, 1.6], dtick=1, row=2, col=1)
fig.update_yaxes(range=[0, 3.8], dtick=1, row=3, col=1)
fig.update_layout(height=560, title="§7 · Per-page signals: the zoo and the paper page (toy; K7, K8). Hover for the flags")
fig.show()

# ---------- chart 2: Corpus D characters per page, hyphen breaks marked
pno = list(range(1, len(texts) + 1))
fig = go.Figure()
fig.add_bar(x=pno, y=lens, name="characters on the page", marker=bar_style(BLUE),
            hovertemplate="page %{x}: %{y:,} characters<extra></extra>")
hp = sorted(hb)
fig.add_scatter(x=hp, y=[lens[p - 1] + 120 for p in hp], mode="markers+text", name="line-end hyphen breaks (all compounds)",
                marker=dict(symbol="triangle-down", size=12, color=ORANGE, line=dict(width=1, color=SURFACE)),
                text=[str(hb[p]) for p in hp], textposition="top center", textfont=dict(color=INK2),
                customdata=[", ".join(s.replace("\n", "") for q, s in a["hyphen_breaks"] if q == p) for p in hp],
                hovertemplate="page %{x}: %{text} hyphen break(s)<br>%{customdata}<extra></extra>")
fig.update_layout(height=420, title="§7 · Corpus D: characters per page, hyphen breaks marked (measured; K9, S5)",
                  xaxis=dict(title="page (1-based)", dtick=2), yaxis=dict(title="characters", range=[0, 2900]))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 8 · Normalisation moves every later offset

**What this verifies** (lesson step 8, `#unicode`; facts K3, K4, K8).

**Setup.** Unicode NFKC normalisation replaces "compatibility" characters with plain ones. Some replacements change the length of the text.

**Result** (literal strings, K3):

| character | UTF-8 bytes | after NFKC | length change |
|---|---|---|---|
| `ﬁ` (U+FB01), `ﬂ` | 3 | `fi`, `fl` | +1 |
| `…` | 3 | `...` | +2 |
| `½` | 2 | `1⁄2` | +2 |
| `x²` | 3 | `x2` (the exponent is lost) | 0 |
| `e` + combining accent | 3 | `é` | −1 |
| `é`, `—`, soft hyphen | 2, 3, 2 | unchanged | 0 |
| no-break space | 2 | a plain space | 0 |

"file" is not found in "The ﬁle"; after NFKC it is. Corpus D has **0** characters NFKC would change (delta 0). The paper page: NFKC leaves `q·p` and `‖q‖ ≤ 1` alone but turns `10⁵` into `105` (K8).

**Offset shift** (toy, K4): a 520-character text with ligatures at raw offsets 100 and 300. After NFKC it has 522 characters, and the character at raw offset 500 is now at **502**. Each ligature shifts every later offset by +1.

**What it means.** Never normalise the frozen snapshot in place: every gold span after the first changed character would point at the wrong text. If a ligature must go (search needs "file"), do it as a logged edit with a cleaned→raw map (rule R3, step 9), under a new cleaning version.

**The chart** is the offset-shift strip: how far each raw offset moves.
""")
code(r'''
SAMPLES = [("ligature fi", "ﬁ", 3, "fi", 1), ("ligature fl", "ﬂ", 3, "fl", 1), ("ellipsis", "…", 3, "...", 2),
           ("one half", "½", 2, "1⁄2", 2), ("x squared", "x²", 3, "x2", 0),
           ("e acute, one code point", "é", 2, "é", 0), ("e + combining acute", "é", 3, "é", -1),
           ("em dash", "—", 3, "—", 0), ("soft hyphen", "­", 2, "­", 0),
           ("non-breaking space", " ", 2, " ", 0), ("plain a", "a", 1, "a", 0)]
got = {n: [len(s.encode("utf-8")), unicodedata.normalize("NFKC", s), len(unicodedata.normalize("NFKC", s)) - len(s)]
       for n, s, *_ in SAMPLES}
check("§8 bytes, NFKC form, length change for 11 strings (K3)", got, {n: [b, f, d] for n, _, b, f, d in SAMPLES})
check("§8 'file' in 'The \\ufb01le': before, after NFKC (K3)",
      ["file" in "The ﬁle", "file" in unicodedata.normalize("NFKC", "The ﬁle")], [False, True])
check("§8 Corpus D: characters NFKC would change, length delta (K3)", list(nfkc_changes(doc_text)), [0, 0])
check("§8 NFKC on 'q·p', '‖q‖ ≤ 1', 'x²', '10⁵' (K8)",
      [unicodedata.normalize("NFKC", s) for s in ("q·p", "‖q‖ ≤ 1", "x²", "10⁵")],
      ["q·p", "‖q‖ ≤ 1", "x2", "105"])

# K4: the offset shift (code as in c1_kit_measure.py)
body = ("Parsing is the first step. " * 30)[:520]
toy = body[:100] + "ﬁ" + body[101:300] + "ﬂ" + body[301:]
assert len(toy) == 520 and toy[100] == "ﬁ" and toy[300] == "ﬂ"
dec = unicodedata.normalize("NFKC", toy)
src = []                                              # cleaned index -> raw index
for i, c in enumerate(toy):
    src.extend([i] * len(unicodedata.normalize("NFKC", c)))
new_pos = src.index(500)
check("§8 K4: length after NFKC; raw 500 lands at; same character", [len(dec), new_pos, dec[new_pos] == toy[500]],
      [522, 502, True])
check("§8 K4: cleaned->raw map at cleaned 101, 102, 502", [src[101], src[102], src[502]], [100, 101, 500])

raw_pos = list(range(len(toy)))
shift = [src.index(i) - i for i in raw_pos]           # where raw offset i now starts, minus i
fig = go.Figure()
fig.add_scatter(x=raw_pos, y=shift, mode="lines", line=dict(shape="hv", width=2, color=BLUE), name="shift",
                showlegend=False, hovertemplate="raw offset %{x} → cleaned offset %{customdata} (shift +%{y})<extra></extra>",
                customdata=[src.index(i) for i in raw_pos])
for lx, txt in ((100, "ﬁ at raw 100"), (300, "ﬂ at raw 300")):
    fig.add_vline(x=lx, line=dict(color=ORANGE, width=2, dash="dot"))
    fig.add_annotation(x=lx, y=2.35, text=txt, showarrow=False, xanchor="left", xshift=4, font=dict(color=INK2))
fig.add_scatter(x=[500], y=[shift[500]], mode="markers+text", marker=dict(size=11, color=BLUE, line=dict(width=2, color=SURFACE)),
                text=["raw 500 → 502"], textposition="top left", showlegend=False, hoverinfo="skip")
fig.update_layout(height=360, title="§8 · Offset-shift strip: two ligatures decomposed by NFKC (toy; K4)",
                  xaxis=dict(title="raw offset", range=[0, 520]),
                  yaxis=dict(title="shift after NFKC (characters)", range=[-0.2, 2.6], dtick=1))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 9 · Cleaning as logged edits, and why v0 applies none

**What this verifies** (lesson step 9, `#cleaning`; facts S10, S12, K11, K12).

**Setup.** A cleaning rule never rewrites text silently. It produces **edits** `{page, rule, start, end, before, after}` on the raw page, and applying them returns the cleaned text plus a map `src[i]` = the raw offset of cleaned character *i*. `undo(apply(edits))` must give the raw text back. Three rules:
- **R1** header/footer: drop a line whose digit-masked form appears on ≥ max(3, ⌈n/2⌉) pages;
- **R2** de-hyphenate: join `frag-\nment` **only if** the joined word occurs elsewhere in the document;
- **R3** ligature: one ligature character → its letters.

**Result.**
- **Zoo** (toy, page 1 read by columns): R1 6 edits, R2 1, R3 3; 92 raw characters removed, 6 inserted. The R2 edit deletes page 1 [107, 109) `"-\n"`; the cleaned "extraction" maps back to raw offsets 101–112. Round trip: exact on every page.
- **Part F toy**: `"later extrac-\ntion\n"` with "extraction" on another page → one R2 edit [12, 14); cleaned `"later extraction\n"`, cleaned offset 12 ← raw 14.
- **Paper page** (toy, K11): R2 joins `accu-racy` ("accuracy" occurs elsewhere) and leaves `mar-gin` ("margin" does not); R3 3 edits; 575 → 576 characters; round trip exact. Each cleaning version is a new snapshot (K12): `none` 202926ae0c7b, `r3_ligatures_v1` 83b34428ba76, `r2r3_v1` 63d18fdddf83.
- **Corpus D** (measured): the same rules make **0** edits. A naive "join every `-\n`" rule would change **7** places, and all 7 are real compounds, so it would damage 7 of 7.

**What it means.** On Corpus D cleaning has nothing to fix and something to break, so v0 applies none. Rules also misfire on real text: R1 flags 5 real section titles in the book's `index.pdf` as "headers" (S8, recorded; the book is not opened here). The book cleans after splitting (Ch1 p.5/14, p.7/14), and so does the repo (`helper_functions.py` L69–L70); cleaning before splitting, as logged edits, keeps every offset traceable.
""")
code(r'''
# zoo, page 1 by columns (a parser option), pages 2-5 as extracted (S10)
zpages = [extract_columns(zoo[0])] + zt[1:]
edits = plan_edits("zoo", zpages)
by_rule = {}
for e in edits:
    by_rule[e["rule"]] = by_rule.get(e["rule"], 0) + 1
check("§9 zoo edits by rule (S10)", by_rule, {"R1_header_footer": 6, "R2_dehyphenate": 1, "R3_ligature": 3})
check("§9 zoo raw characters removed, inserted (S10)",
      [sum(e["end"] - e["start"] for e in edits), sum(len(e["after"]) for e in edits)], [92, 6])
r2 = [e for e in edits if e["rule"] == "R2_dehyphenate"][0]
check("§9 zoo R2 edit: page, [start, end), before (S10)", [r2["page"], r2["start"], r2["end"], r2["before"]],
      [1, 107, 109, "-\n"])
ok = True
for i, t in enumerate(zpages, 1):
    pe = [e for e in edits if e["page"] == i]
    cleaned, smap = apply_edits(t, pe)
    ok &= undo_edits(cleaned, smap, pe, len(t)) == t and len(smap) == len(cleaned)
    if i == 1:
        k = cleaned.find("extraction")
        ext = [smap[k], smap[k + len("extraction") - 1]]
check("§9 zoo cleaned 'extraction' -> raw offsets (S10)", ext, [101, 112])
check("§9 zoo round trip undo(apply(edits)) == raw, every page (S10)", ok, True)

# Part F toy (S12)
hpg = ["later extrac-\ntion\n", "extraction\n"]
he = plan_edits("toy", hpg)
hc, hs = apply_edits(hpg[0], [e for e in he if e["page"] == 1])
check("§9 Part F toy: R2 edit, cleaned text, cleaned 12 <- raw (S12)",
      [[(e["page"], e["rule"], e["start"], e["end"]) for e in he], hc, hs[12]],
      [[(1, "R2_dehyphenate", 12, 14)], "later extraction\n", 14])

# the paper page (K11, K12; code as in c1_kit_measure.py)
pe = []
for m in HYPHEN_BREAK.finditer(dflt):
    if (m.group(1) + m.group(2)).lower() in pvocab:
        pe.append({"start": m.end(1), "end": m.end(1) + 2, "before": "-\n", "after": ""})
for i, c in enumerate(dflt):
    if c in LIGATURES:
        pe.append({"start": i, "end": i + 1, "before": c, "after": unicodedata.normalize("NFKC", c)})
pclean, pmap = apply_edits(dflt, pe)
check("§9 paper: R2 edits, R3 edits, raw -> cleaned length, round trip (K11)",
      [sum(e["before"] == "-\n" for e in pe), sum(e["before"] in LIGATURES for e in pe), len(dflt), len(pclean),
       undo_edits(pclean, pmap, pe, len(dflt)) == dflt], [1, 3, 575, 576, True])
check("§9 paper: 'accuracy' joined, 'mar-' + 'gin' left (K8, K11)", ["accuracy" in pclean, "mar-\ngin" in pclean], [True, True])
K12 = {}
for cl, txt in (("none", dflt), ("r3_ligatures_v1", apply_edits(dflt, [e for e in pe if e["before"] in LIGATURES])[0]),
                ("r2r3_v1", pclean)):
    K12[cl] = [sh(txt), snapshot_id("pymupdf", pymupdf.VersionBind, {}, cl, {"paper": hashlib.sha256(txt.encode()).hexdigest()})]
check("§9 paper: text sha256[:12] and snapshot_id per cleaning version (K12)", K12,
      {"none": ["4033785d96eb", "202926ae0c7b"], "r3_ligatures_v1": ["de3202cd0790", "83b34428ba76"],
       "r2r3_v1": ["2fc9105c0b44", "63d18fdddf83"]})

# Corpus D (S10)
check("§9 D: edits by R1-R3; places a naive '-\\n' join would change (S10)",
      [len(plan_edits("climate", texts)), sum(len(HYPHEN_BREAK.findall(t)) for t in texts)], [0, 7])
''')

# =====================================================================================================================
md(r"""
## 10 · Parsers compared

**What this verifies** (lesson step 10, `#parsers`; fact S2; the rest is external).

**Setup.** Parsers sit on a ladder: cheap text extractors (PyMuPDF, pypdf, pdfplumber) read the text layer; layout models (Docling, marker) also find reading order, tables and headings; vision-language models read the rendered page image. Each step up costs more time per page and more install weight, and some carry licence limits.

**Result.** Nothing here is re-measured: the published evaluations ([C1-1] Docling, [C1-2] OmniDocBench, [C1-3] Adhikari & Agarwal) are *external*, each with its own documents and limits (research C1 §5). This cell checks only what v0 pins: PyMuPDF 1.26.7, `page.get_text()` with no options. It also lists which other parsers this environment has (it imports none of them).

**What it means.** A parser is chosen per corpus by measuring it on that corpus (step 11), not by a ranking from someone else's documents. PyMuPDF stays pinned (its licence is AGPL, fine for this local study project); Docling is a possible comparison arm, as its own snapshot with its own id.
""")
code(r'''
check("§10 v0 parser block (S2)", parser_info(),
      {"backend": "pymupdf", "version": "1.26.7", "call": "page.get_text()", "options": {}})
avail = {m: importlib.util.find_spec(m) is not None for m in ("pypdf", "pdfplumber", "docling", "marker",
                                                              "pymupdf4llm", "langchain_community")}
print("   other parsers importable here (none is used):", avail)
''')

# =====================================================================================================================
md(r"""
## 11 · Measuring parse quality

**What this verifies** (lesson step 11, `#measure`; formula on K7, K8, K9).

**Setup.** Parse quality is measured in three separate parts:
1. **Extraction on its own:** per-page signals (step 7) flag pages to look at; a person checks a small sample, chosen from flagged and unflagged pages alike, against the rendered page; a second parser's text is diffed against the first.
2. **Does it matter for retrieval:** compare Hit@k (1 if a right chunk is in the top k) and CE@k (P6) on questions whose gold spans lie on flagged pages with the rest.
3. **Answer quality** is a separate measurement again (AE Ch8, 'PDF Documents'): extraction errors must not be blamed on the model.

**Result.** The flags of step 7, page by page: zoo pages 1 (ligatures, hyphens, right→left jumps), 2 (ruled table), 3 (blank) and 4 (image-only); page 5 has none. The paper page: ligatures, hyphens, 1 jump. Corpus D: pages 8, 11, 12, 19, 29, 31, each for a line-end hyphen, and a look shows all of them are real compounds.

**What it means.** A flag is a reason to look, not a verdict: Corpus D's six flagged pages are fine. Parts 2 and 3 need questions with gold spans (M1), so they wait for the labels; this notebook stops at part 1.
""")
code(r'''
DFLAG = {}
for i, (p, t) in enumerate(zip(DOC, texts), 1):
    f = flags(len(t), len(p.get_images()), sum(t.count(c) for c in LIGATURES), len(HYPHEN_BREAK.findall(t)),
              rl_jumps(p), len(p.find_tables().tables))
    if f:
        DFLAG[i] = f
check("§11 zoo pages with a flag (formula on K7)", [n for n, _, _, f in SIG if f and n.startswith("zoo")],
      ["zoo p.1", "zoo p.2", "zoo p.3", "zoo p.4"])
check("§11 Corpus D pages with a flag, and why (formula on K9)", DFLAG,
      {8: ["line-end hyphens"], 11: ["line-end hyphens"], 12: ["line-end hyphens"], 19: ["line-end hyphens"],
       29: ["line-end hyphens"], 31: ["line-end hyphens"]})
''')

# =====================================================================================================================
md(r"""
## 12 · For your project

**What this verifies** (lesson step 12, `#project`; facts S2, S7).

**Setup.** C1 hands on a fixed interface to chunking (C2) and the index (C3): `pages` (a list of `Page(doc_id, page, text, parser)`), `doc_text` (pages joined with `"\n"`), page-table rows `{page, doc_char_start, doc_char_end, text_sha256}`, a manifest, and its `snapshot_id`.

**Result.** For Corpus D the interface is built and the manifest validates with snapshot id `ea07572562ac`. **Corpus T** (arXiv papers) is not chosen yet (DEC-3): its cleaning rules must be decided, and its snapshot frozen, **before** any M1 label is written, because every label is a span of that frozen text. Its cell below is SKIPPED until then.
""")
code(r'''
check("§12 Page fields; page-table row keys (S2)", [list(Page.__dataclass_fields__), list(table[0])],
      [["doc_id", "page", "text", "parser"], ["page", "doc_char_start", "doc_char_end", "text_sha256"]])
check("§12 manifest fields (06 §5.3 order) and snapshot_id (S2, S7)", [list(man), man["snapshot_id"]],
      [["snapshot_id", "corpus", "corpus_version", "created_utc", "parser", "cleaning", "encoding", "newline",
        "page_join", "docs"], "ea07572562ac"])
skip("§12 Corpus T snapshot", "DEC-3 is not decided: no Corpus T PDFs or lock file exist yet")
''')

# =====================================================================================================================
md(r"""
## Result

The cell below counts the checks and deletes the temporary folder with the two toy PDFs. Every `FAIL` names the value that disagreed; every `SKIPPED` says why it could not run.
""")
code(r'''
for d in (zoo, paper, DOC):
    d.close()
shutil.rmtree(TMP, ignore_errors=True)
n_pass = sum(ok for _, ok in CHECKS)
n_fail = len(CHECKS) - n_pass
print(f"{n_pass} checks passed / {n_fail} failed")
for name, ok in CHECKS:
    if not ok:
        print("   FAILED:", name)
for name, why_ in SKIPPED:
    print("   SKIPPED:", name, "-", why_)
print(f"   ({len(SKIPPED)} skipped; temporary folder removed: {not TMP.exists()}; notebook time {time.time() - T0:.1f} s)")
''')

nb = nbf.v4.new_notebook()
nb.cells = CELLS
nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3 (ipykernel)", "language": "python"},
               "language_info": {"name": "python"}}
OUT.parent.mkdir(parents=True, exist_ok=True)
nbf.validate(nb)
nbf.write(nb, str(OUT))
print(f"wrote {OUT.relative_to(WS)}: {len(CELLS)} cells ({sum(c.cell_type == 'code' for c in CELLS)} code); "
      f"library copies {SEG_SHA}")
