"""Build labs/C1_parsing_lab.ipynb (blank-file-first scaffold, no solution code).

The CHECK cells compare sha256 fingerprints computed here from the reference implementation (c1_ref.py) on
Corpus D, the book's chapter 1 and the synthetic zoo (c1_zoo.py), so expected answers stay hidden.
The setup cell contains the zoo builder verbatim (an input fixture, not a solution) and the Page interface (06 §3.1).
Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C1/c1_build_lab.py "<Book RAG>" labs/C1_parsing_lab.ipynb
Saved output: sources/verification/C1/out_c1_build_lab.txt (the fingerprints and the values behind them)
"""
import hashlib
import inspect
import json
import os
import re
import sys
import tempfile

import pymupdf as fitz

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c1_ref as R  # noqa: E402
import c1_zoo as Z  # noqa: E402

BASE, OUT = sys.argv[1], sys.argv[2]
CLIMATE = os.path.join(BASE, "upstream", "RAG_Techniques", "data", "Understanding_Climate_Change.pdf")
CH1 = os.path.join(BASE, "RAG_Made_Simple_The_Complete_Visual_Guide", "chapter 1.pdf")


def _fp(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:16]


FP = {}


def fp(name, value):
    FP[name] = _fp(value)
    print(f"{name}: {FP[name]}  <- {json.dumps(value, ensure_ascii=False)[:300]}")


# ------------------------------------------------------------------ values from the reference implementation
pages = R.load_pages(CLIMATE, "climate")
texts = [p.text for p in pages]
doc_text, rows = R.build_page_table(texts)
dsha = R.sha256_hex(doc_text)
fp("t1_lengths", [len(t) for t in texts])
fp("t2_len", len(doc_text))
fp("t2_rows", rows)
sid = R.snapshot_id("pymupdf", "1.26.7", {}, "none", {"climate": dsha})
fp("t3_sid", sid)
fp("t3_sid_1282", R.snapshot_id("pymupdf", "1.28.2", {}, "none", {"climate": dsha}))
fp("t3_sid_tabs", R.snapshot_id("pymupdf", "1.26.7", {}, "tabs_v1", {"climate": dsha}))
fp("t4_pdf", [hashlib.sha256(open(CLIMATE, "rb").read()).hexdigest(), os.path.getsize(CLIMATE)])
offs = [0, 2423, 2424, 2425, 16074, len(doc_text) - 1]
fp("t5_offsets", [list(R.page_of(o, rows)) for o in offs])
first = doc_text.find("Paris Agreement")
fp("t5_paris", [list(R.page_of(first, rows)), sorted({R.page_of(m.start(), rows)[0] for m in re.finditer("Paris Agreement", doc_text)})])
a = R.artifact_counts(texts)
fp("t6_counts", {k: a[k] for k in ("empty_pages", "ligatures", "tabs", "double_newlines", "lines", "lines_ending_space")})
fp("t6_breaks", [list(x) for x in a["hyphen_breaks"]])
fp("t6_repeated", list(R.repeated_lines(texts)))

tmp = tempfile.mkdtemp()
zp = Z.build_zoo(os.path.join(tmp, "zoo.pdf"))
with fitz.open(zp) as d:
    zt = [p.get_text() for p in d]
    fp("t7_default_p1", zt[0].split("\n"))
    col = R.extract_columns(d[0])
    fp("t7_columns_p1", col)
    fp("t7_tables", [len(p.find_tables().tables) for p in d])
    kinds = ["text" if t.strip() else ("image_only" if p.get_images() else "empty") for p, t in zip(d, zt)]
    fp("t7_kinds", kinds)
    fp("t7_lig", sum(col.count(c) for c in R.LIGATURES))
zpages = [col] + zt[1:]
edits = R.plan_edits("zoo", zpages)
fp("t8_edits", [[e["page"], e["rule"], e["start"], e["end"], e["before"], e["after"]] for e in edits])
fp("t8_climate", [len(R.plan_edits("climate", texts)), sum(len(R.HYPHEN_BREAK.findall(t)) for t in texts)])
with fitz.open(CH1) as d:
    p2, p13 = d[1], d[12]
    irect = p2.get_image_rects(p2.get_images()[0][0])[0]
    inside = sum(1 for b in p2.get_text("blocks") if fitz.Rect(b[:4]).intersects(irect))
    fp("t9_book", [len(p2.get_images()), inside, len(p13.find_tables().tables), len(p13.find_tables(strategy="text").tables)])

ZOO_SRC = inspect.getsource(Z).split('"""', 2)[2].lstrip("\n")    # the module body without its docstring


# ------------------------------------------------------------------ notebook cells
def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text, tag, task=None):
    meta = {"tags": [tag]}
    if task:
        meta["task"] = task
    return {"cell_type": "code", "execution_count": None, "metadata": meta, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


EMPTY = "# Your code here (blank-file first: write it yourself; no copying from c1_ref.py or c1_measure.py)."

cells = [
md("""
# C1 lab: document loading and parsing (builds the v0 snapshot)

Lesson: [`concepts/C1_document_parsing.md`](../concepts/C1_document_parsing.md), Part H. Concept card: [02 C1](../02_RAG_MASTER_LEARNING_PLAN.md#c1). Data model: [06 §3.1 and §5.3](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#53-corpus-freezing).

**How this lab works (blank-file first).**
- Each task has a **task cell**, an **empty code cell** for you, and a **CHECK cell** (`# CHECK`, do not edit). Run the CHECK cell after your code. If it fails, read the message and fix your code.
- This notebook has **no solution code**. The CHECK cells compare fingerprints, so the expected answers stay hidden until you have predicted.
- Where a task says **Predict first**, fill the prediction cell **before** you compute anything.
- **No API calls.** Never print values from `.env`. Kernel: the project **`.venv` (Python 3.12)**, where `pymupdf` is pinned at **1.26.7**.
- **What you build here is v0's input.** Tasks 1–4 produce the pages and the frozen snapshot that C2 (chunking) and C3 (embedding) read. Tasks 5–9 are diagnosis: nothing in them changes the snapshot.
"""),
md("""
## Setup (given)
Run this cell. It names the input files, defines the fingerprint helper `_fp`, the `Page` record from 06 §3.1 (do not change its fields: C2 and C3 rely on them), and `build_zoo`, which writes a small synthetic PDF with known artifacts (a toy, for Tasks 7–8).
"""),
code('''
import hashlib, json, os, re, tempfile, unicodedata
from dataclasses import dataclass
import pymupdf as fitz

BASE = r"C:\\Yash\\New-Work\\Book RAG"
PDF = os.path.join(BASE, "upstream", "RAG_Techniques", "data", "Understanding_Climate_Change.pdf")   # Corpus D
BOOK_CH1 = os.path.join(BASE, "RAG_Made_Simple_The_Complete_Visual_Guide", "chapter 1.pdf")         # specimen only, not a corpus
SNAP_DIR = os.environ.get("C1_SNAP_DIR", os.path.join(BASE, "rag_learning", "evaluation", "snapshots"))  # 06 §5.3
ZOO_PDF = os.path.join(tempfile.gettempdir(), "c1_zoo.pdf")                                            # outside the workspace

def _fp(x):
    """Fingerprint of a value. The CHECK cells compare fingerprints, not visible answers."""
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:16]

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class Page:                 # 06 §3.1: Page(doc_id, page=1-based, text, parser="pymupdf <version>")
    doc_id: str
    page: int               # 1-based PDF page
    text: str               # raw page.get_text(); v0 does no cleaning
    parser: str             # e.g. "pymupdf 1.26.7"

# ---- the artifact zoo (a toy PDF; copied verbatim from sources/verification/C1/c1_zoo.py) ----
''' + ZOO_SRC + '''
build_zoo(ZOO_PDF)
print("pymupdf", fitz.VersionBind, "| snapshot folder:", SNAP_DIR, "| ready")
''', "setup"),

# ---------------------------------------------------------------- Task 1
md("""
## Task 1: load the PDF page by page

**Predict first** (cell below): how many pages does Corpus D have, and what number will **your** first page carry?

Then write `load_pages(pdf_path, doc_id)` that returns a list of `Page`, one per PDF page, in order:
- `page` is **1-based** (the first page is 1);
- `text` is exactly `page.get_text()`: no strip, no cleaning;
- `parser` is `f"pymupdf {fitz.VersionBind}"`.

Then run `pages = load_pages(PDF, "climate")`.
"""),
code('''
# PREDICTION
my_prediction_n_pages = None        # an integer
my_prediction_first_page = None     # 0 or 1
''', "prediction", "t1_pred"),
code(EMPTY, "learner", "t1"),
code(f'''
# CHECK Task 1 (do not edit)
assert my_prediction_n_pages is not None and my_prediction_first_page is not None, "fill the prediction cell first"
assert fitz.VersionBind == "1.26.7", f"pymupdf must be the pinned 1.26.7, got {{fitz.VersionBind}}: snapshot_id depends on it"
assert isinstance(pages, list) and all(isinstance(p, Page) for p in pages), "pages must be a list of Page"
assert [p.page for p in pages] == list(range(1, len(pages) + 1)), "page numbers must be 1, 2, 3, ... (1-based, in order)"
assert {{p.doc_id for p in pages}} == {{"climate"}} and {{p.parser for p in pages}} == {{"pymupdf 1.26.7"}}, "doc_id / parser fields"
assert _fp([len(p.text) for p in pages]) == "{FP['t1_lengths']}", "page texts differ from raw page.get_text(): did you strip or clean?"
print("Task 1 OK:", len(pages), "pages; you predicted", my_prediction_n_pages, "| shortest page:",
      min(pages, key=lambda p: len(p.text)).page, "with", min(len(p.text) for p in pages), "characters")
''', "check"),

# ---------------------------------------------------------------- Task 2
md("""
## Task 2: one document text, one page table

v0 has **one coordinate system**: offsets into `doc_text`, the pages joined with `"\\n"` (06 §2.3).

**Predict first:** the 33 page texts add up to `sum(len(p.text) for p in pages)` characters (print that number first). How long will `doc_text` be?

Write `build_page_table(page_texts)` that returns `(doc_text, rows)`, where each row is a dict with exactly these keys (06 §5.3):
`{"page": 1-based, "doc_char_start": ..., "doc_char_end": ..., "text_sha256": sha256_hex(page text)}`.
Rule: `doc_text[row["doc_char_start"]:row["doc_char_end"]]` must equal that page's text.
"""),
code('''
# PREDICTION
my_prediction_len_doc_text = None   # an integer, BEFORE you build doc_text
''', "prediction", "t2_pred"),
code(EMPTY, "learner", "t2"),
code(f'''
# CHECK Task 2 (do not edit)
assert my_prediction_len_doc_text is not None, "fill the prediction cell first"
doc_text, rows = build_page_table([p.text for p in pages])
assert all(doc_text[r["doc_char_start"]:r["doc_char_end"]] == p.text for r, p in zip(rows, pages)), "a slice does not give back its page"
assert _fp(len(doc_text)) == "{FP['t2_len']}", "len(doc_text) is not right yet: how many join characters are there?"
assert _fp(rows) == "{FP['t2_rows']}", "rows differ: check the keys, 1-based page numbers, and the +1 after each page"
print("Task 2 OK. len(doc_text) =", len(doc_text), "| you predicted", my_prediction_len_doc_text,
      "| page 8 starts at", rows[7]["doc_char_start"], "(06 §5.3 says 16,074)")
''', "check"),

# ---------------------------------------------------------------- Task 3
md("""
## Task 3: the `snapshot_id`

Write `snapshot_id(backend, version, options, cleaning_version, doc_text_sha256)` by copying the **exact formula in 06 §5.3**. `doc_text_sha256` is a dict `{doc_id: sha256_hex(doc_text)}`. Watch the comment about `"page_join=\\\\n"`.

Then compute `sid = snapshot_id("pymupdf", fitz.VersionBind, {}, "none", {"climate": sha256_hex(doc_text)})`.

**Predict first:** suppose a newer pymupdf (say 1.28.2) extracted **byte-identical** text. Would the id stay the same?
"""),
code('''
# PREDICTION
my_prediction_same_id_under_1_28_2 = None   # True or False
''', "prediction", "t3_pred"),
code(EMPTY, "learner", "t3"),
code(f'''
# CHECK Task 3 (do not edit)
assert my_prediction_same_id_under_1_28_2 is not None, "fill the prediction cell first"
assert _fp(sid) == "{FP['t3_sid']}", "sid is not the 06 §5.3 value yet. Is page_join a literal backslash + n? Is options json.dumps(..., sort_keys=True)?"
h = {{"climate": sha256_hex(doc_text)}}
other = snapshot_id("pymupdf", "1.28.2", {{}}, "none", h)
assert _fp(other) == "{FP['t3_sid_1282']}", "your function does not put the version into the id the 06 way"
tabs = snapshot_id("pymupdf", "1.26.7", {{}}, "tabs_v1", h)
assert _fp(tabs) == "{FP['t3_sid_tabs']}", "your function does not put the cleaning version into the id the 06 way"
print("Task 3 OK. snapshot_id =", sid, "| same text, version 1.28.2 ->", other, "| cleaning 'tabs_v1' ->", tabs)
print("You predicted 'same id under 1.28.2':", my_prediction_same_id_under_1_28_2)
''', "check"),
md("""
**One sentence.** Corpus D has no tab characters at all. Why does a no-op cleaning step (`tabs_v1`) still change the id, and why is that the right design?

*Template:* "The id changes because ____ is part of the recipe. This is right because ____."

*Your answer:*
"""),

# ---------------------------------------------------------------- Task 4
md("""
## Task 4: write the snapshot, then refuse a broken one

1. Build `manifest`, a dict with the **06 §5.3 fields**: `snapshot_id, corpus ("D"), corpus_version ("1.0"), created_utc, parser, cleaning, encoding, newline, page_join, docs`. `parser` = `{"backend": "pymupdf", "version": fitz.VersionBind, "call": "page.get_text()", "options": {}}`; `cleaning` = `{"version": "none", "steps": []}`; `docs` = one dict with `doc_id, pdf_sha256, bytes, pages, doc_text_sha256, page_table` (the page table is your `rows`).
2. Write `doc_text` to `SNAP_DIR/<sid>/climate.txt` and the manifest to `SNAP_DIR/D_<sid>.json` (`json.dumps(manifest, indent=2, ensure_ascii=False)`), both UTF-8. Set `text_path` and `manifest_path` to the two paths.
3. Write `validate_snapshot(manifest, doc_texts)` (`doc_texts = {doc_id: text}`) that **raises `ValueError`** unless: the text hash matches; pages are 1..n starting at 0; each start = previous end + 1; the last end = `len(text)`; each page slice has its `text_sha256`; and the recomputed `snapshot_id` matches.

**Predict first:** you are on Windows. If you write the text with a plain `open(path, "w", encoding="utf-8")`, will the file's sha256 equal `doc_text_sha256`?
"""),
code('''
# PREDICTION
my_prediction_plain_open_hash_matches = None   # True or False
''', "prediction", "t4_pred"),
code(EMPTY, "learner", "t4"),
code(f'''
# CHECK Task 4 (do not edit)
import copy
assert my_prediction_plain_open_hash_matches is not None, "fill the prediction cell first"
need = {{"snapshot_id", "corpus", "corpus_version", "created_utc", "parser", "cleaning", "encoding", "newline", "page_join", "docs"}}
assert set(manifest) == need, f"manifest keys differ from 06 §5.3: {{sorted(set(manifest) ^ need)}}"
d0 = manifest["docs"][0]
assert set(d0) == {{"doc_id", "pdf_sha256", "bytes", "pages", "doc_text_sha256", "page_table"}}, "docs[0] keys differ from 06 §5.3"
assert _fp([d0["pdf_sha256"], d0["bytes"]]) == "{FP['t4_pdf']}", "pdf_sha256 / bytes: hash the PDF file's bytes"
assert manifest["snapshot_id"] == sid and d0["page_table"] == rows and manifest["page_join"] == "\\n"
raw = open(text_path, "rb").read()
assert hashlib.sha256(raw).hexdigest() == d0["doc_text_sha256"], \\
    f"the file's bytes do not hash to doc_text_sha256 ({{len(raw)}} bytes on disk vs {{len(doc_text.encode())}}). Hint: newline="
assert json.load(open(manifest_path, encoding="utf-8"))["snapshot_id"] == sid
validate_snapshot(manifest, {{"climate": doc_text}})                      # must pass
bad = copy.deepcopy(manifest)
bad["docs"][0]["page_table"][1]["doc_char_start"] += 1                 # page 2 shifted by one,
bad["docs"][0]["page_table"][1]["doc_char_end"] += 1                   # same length, same hash
try:
    validate_snapshot(bad, {{"climate": doc_text}})
    raise AssertionError("validate_snapshot accepted a page table with page 2 shifted by +1: it must fail closed")
except ValueError as e:
    print("shifted page table rejected:", e)
print("Task 4 OK. Wrote", text_path, "and", manifest_path)
''', "check"),

# ---------------------------------------------------------------- Task 5
md("""
## Task 5: from a document offset back to a page

Citations need a page. Write `page_of(doc_offset, rows)` that returns `(page, page_offset)`: the 1-based page that contains `doc_offset`, and the offset inside that page's text. Rule (07 H.3): the joining `"\\n"` after page *p* belongs to page *p*.

Then set `paris = page_of(doc_text.find("Paris Agreement"), rows)` and `paris_pages`, the sorted list of **distinct** pages on which "Paris Agreement" occurs.
"""),
code(EMPTY, "learner", "t5"),
code(f'''
# CHECK Task 5 (do not edit)
offs = [0, 2423, 2424, 2425, 16074, len(doc_text) - 1]
got = [list(page_of(o, rows)) for o in offs]
assert _fp(got) == "{FP['t5_offsets']}", f"page_of is not right yet: {{got}}. Which page owns offset 2424 (the join after page 1)?"
assert _fp([list(paris), list(paris_pages)]) == "{FP['t5_paris']}", "paris / paris_pages are not right yet"
print("Task 5 OK. First 'Paris Agreement' is on page", paris[0], "at page offset", paris[1], "| pages:", paris_pages)
''', "check"),

# ---------------------------------------------------------------- Task 6
md("""
## Task 6: an artifact inventory of Corpus D (raw text, nothing changed)

Write `artifact_counts(page_texts)` that returns a dict with:
- `"empty_pages"`: 1-based pages whose text is only whitespace;
- `"hyphen_breaks"`: a list of `[page, match]` for every match of `re.compile(r"([A-Za-z]+)-\\n([a-z]+)")`;
- `"ligatures"`: count of the characters U+FB00 to U+FB06; `"tabs"`: count of `"\\t"`; `"double_newlines"`: count of `"\\n\\n"`;
- `"lines"`: number of newline-terminated lines; `"lines_ending_space"`: how many of them end with `" "` before the `"\\n"`.

Write `repeated_lines(page_texts)` that returns `[threshold, {key: n_pages}]`: a line's key is the stripped line with each run of digits replaced by `"#"`; count the **pages** a key appears on; `threshold = max(3, ceil(n_text_pages / 2))`; keep keys at or over it.

**Predict first:** how many of the line-end hyphens in Corpus D are real compound words (like "well-being") rather than words split by the layout?
"""),
code('''
# PREDICTION
my_prediction_real_compounds = None   # e.g. "all", "none", "about half"
''', "prediction", "t6_pred"),
code(EMPTY, "learner", "t6"),
code(f'''
# CHECK Task 6 (do not edit)
assert my_prediction_real_compounds is not None, "fill the prediction cell first"
texts = [p.text for p in pages]
a = artifact_counts(texts)
keys = ("empty_pages", "ligatures", "tabs", "double_newlines", "lines", "lines_ending_space")
assert _fp({{k: a[k] for k in keys}}) == "{FP['t6_counts']}", f"some count is not right yet: {{ {{k: a[k] for k in keys}} }}"
assert _fp([list(x) for x in a["hyphen_breaks"]]) == "{FP['t6_breaks']}", "hyphen_breaks is not right yet"
assert _fp(list(repeated_lines(texts))) == "{FP['t6_repeated']}", "repeated_lines is not right yet"
for pg, m in a["hyphen_breaks"]:
    print(f"  p.{{pg}}: {{m!r}}")
print("Task 6 OK.", {{k: a[k] for k in keys}}, "| repeated lines:", repeated_lines(texts))
''', "check"),
md("""
**Two sentences.** (1) Would a rule "delete every `-\\n`" help or hurt Corpus D? (2) C2's splitter tries `"\\n\\n"` first. What does your `double_newlines` count mean for it?

*Template:* "(1) It would ____ because ____. (2) The `\\n\\n` separator ____ on this text, so the splitter ____."

*Your answer:*
"""),

# ---------------------------------------------------------------- Task 7
md("""
## Task 7: diagnose the artifact zoo (toy PDF)

The zoo (`ZOO_PDF`, 5 pages) has a running header and footer, two columns on page 1 written line by line across the page, a word hyphenated at a line end, three ligature glyphs, a ruled table, an empty page and an image-only ("scanned") page.

**Predict first:** on page 1, after the header lines, which line will `get_text()` give right after "Parsing comes before chunking:"?

Then compute:
- `zoo_default`: the list of `page.get_text()` for the 5 pages, and `p1_lines = zoo_default[0].split("\\n")`;
- `extract_columns(page)`: the left half of the page (full height) then the right half, using `page.get_text(clip=...)`;
- `zoo_tables`: `len(page.find_tables().tables)` for each page;
- `zoo_kinds`: for each page `"text"` (non-whitespace text), else `"image_only"` (it has images), else `"empty"`;
- `lig_count`: ligature characters (U+FB00–U+FB06) in `extract_columns(page 1)`.
"""),
code('''
# PREDICTION
my_prediction_line_after_parsing = None   # the exact line you expect
''', "prediction", "t7_pred"),
code(EMPTY, "learner", "t7"),
code(f'''
# CHECK Task 7 (do not edit)
assert my_prediction_line_after_parsing is not None, "fill the prediction cell first"
assert _fp(p1_lines) == "{FP['t7_default_p1']}", "p1_lines must be the raw get_text() of page 1 split on newlines"
with fitz.open(ZOO_PDF) as _d:
    _col = extract_columns(_d[0])
assert _fp(_col) == "{FP['t7_columns_p1']}", "extract_columns: left half (full height) then right half, plain get_text(clip=...)"
assert _fp(zoo_tables) == "{FP['t7_tables']}", f"zoo_tables is not right yet: {{zoo_tables}}"
assert _fp(zoo_kinds) == "{FP['t7_kinds']}", f"zoo_kinds is not right yet: {{zoo_kinds}}"
assert _fp(lig_count) == "{FP['t7_lig']}", "lig_count is not right yet"
i = p1_lines.index("Parsing comes before chunking:")
print("Task 7 OK. After 'Parsing comes before chunking:' get_text() gives:", repr(p1_lines[i + 1]))
print("You predicted:", repr(my_prediction_line_after_parsing), "| tables per page:", zoo_tables, "| kinds:", zoo_kinds)
print("'file' found in page 1 text:", "file" in _col, "| after NFKC:", "file" in unicodedata.normalize("NFKC", _col))
''', "check"),

# ---------------------------------------------------------------- Task 8
md("""
## Task 8: cleaning rules that log every change (analysis only; v0 applies none)

An **edit** is a dict `{"doc_id", "page", "rule", "start", "end", "before", "after"}` with **page-relative** raw offsets: it says "raw `text[start:end]` (= `before`) becomes `after`".

Write `plan_edits(doc_id, page_texts)` with three rules, edits sorted by `(page, start)`:
- **R1_header_footer:** every line (including its `"\\n"`) whose key (Task 6) is in `repeated_lines(page_texts)`; `after = ""`.
- **R2_dehyphenate:** for each match of the Task 6 regex, if `(left + right).lower()` occurs as a word (`[A-Za-z]+`, lowercased) anywhere in `page_texts`, delete **only** the `"-\\n"`: `start` = end of the left fragment, `end = start + 2`, `before = "-\\n"`, `after = ""`.
- **R3_ligature:** each character U+FB00–U+FB06 becomes `unicodedata.normalize("NFKC", ch)`.

Write `apply_edits(page_text, edits) -> (cleaned, src)` where `src[i]` is the raw offset of cleaned character `i` (an inserted character maps to its edit's `start`), and `undo_edits(cleaned, src, edits, raw_len) -> raw` that rebuilds the raw text.

Use `zoo_pages = [extract_columns(page 1)] + zoo_default[1:]` and set `zoo_edits = plan_edits("zoo", zoo_pages)`.

**Predict first:** how many edits will the same three rules make on Corpus D?
"""),
code('''
# PREDICTION
my_prediction_edits_on_D = None   # an integer
''', "prediction", "t8_pred"),
code(EMPTY, "learner", "t8"),
code(f'''
# CHECK Task 8 (do not edit)
assert my_prediction_edits_on_D is not None, "fill the prediction cell first"
got = [[e["page"], e["rule"], e["start"], e["end"], e["before"], e["after"]] for e in zoo_edits]
assert _fp(got) == "{FP['t8_edits']}", "zoo_edits are not right yet: compare each rule with the spec (R2 deletes only '-\\\\n')"
for i, t in enumerate(zoo_pages, 1):
    pe = [e for e in zoo_edits if e["page"] == i]
    cleaned, src = apply_edits(t, pe)
    assert len(src) == len(cleaned), "src needs one raw offset per cleaned character"
    assert undo_edits(cleaned, src, pe, len(t)) == t, f"page {{i}}: undo(apply(edits)) does not give back the raw text"
d_edits = plan_edits("climate", [p.text for p in pages])
naive = sum(len(re.findall(r"([A-Za-z]+)-\\n([a-z]+)", p.text)) for p in pages)
assert _fp([len(d_edits), naive]) == "{FP['t8_climate']}", "plan_edits on Corpus D is not right yet"
by_rule = {{}}
for e in zoo_edits:
    by_rule[e["rule"]] = by_rule.get(e["rule"], 0) + 1
print("Task 8 OK. Zoo edits by rule:", by_rule, "| Corpus D edits:", len(d_edits), "(you predicted", my_prediction_edits_on_D, ")",
      "| a naive '-\\\\n' join would change", naive)
c1, s1 = apply_edits(zoo_pages[0], [e for e in zoo_edits if e["page"] == 1])
k = c1.find("extraction")
print("cleaned 'extraction' comes from raw page-1 offsets", s1[k], "to", s1[k + 9], ":", repr(zoo_pages[0][s1[k]:s1[k + 9] + 1]))
''', "check"),

# ---------------------------------------------------------------- Task 9
md("""
## Task 9: a real page with a figure and a table (the book, as a specimen)

Open `BOOK_CH1` (read-only). On **page 2**: count the images, and count the text blocks (`page.get_text("blocks")`) whose rectangle intersects the image's rectangle (`page.get_image_rects(xref)`). On **page 13**: count tables with `find_tables()` and with `find_tables(strategy="text")`.

Set `book_obs = [images_p2, blocks_inside_image_p2, tables_p13_default, tables_p13_text]`. Then look at the page images yourself (open the PDF) and compare with `get_text()`.
"""),
code(EMPTY, "learner", "t9"),
code(f'''
# CHECK Task 9 (do not edit)
assert _fp(list(book_obs)) == "{FP['t9_book']}", f"book_obs is not right yet: {{book_obs}}"
print("Task 9 OK.", book_obs)
''', "check"),
md("""
**One sentence each.** (1) What does `get_text()` give you from the figure on page 2? (2) What happened to the table's rows on page 13?

*Template:* "(1) From the figure I get ____. (2) The rows became ____, so a chunk could ____."

*Your answer:*
"""),

# ---------------------------------------------------------------- hand-off
md("""
## Hand-off to C2 and C3 (run, do not edit)

This prints the exact shape that the next lessons read. Copy the printed `snapshot_id` into your notes.
"""),
code('''
print("pages      :", type(pages).__name__, "of", type(pages[0]).__name__, "| n =", len(pages),
      "| fields:", list(Page.__dataclass_fields__))
print("doc_text   : str, len", len(doc_text), "| sha256", sha256_hex(doc_text)[:16], "| pages joined with '\\\\n'")
print("rows       : page_table, keys", list(rows[0]))
print("snapshot_id:", manifest["snapshot_id"], "| cleaning:", manifest["cleaning"]["version"])
print("files      :", text_path, "|", manifest_path)
''', "handoff"),

md("""
## Wrap-up: evidence for the log

Answer each in one line, no notes.

1. *Decision:* "v0 applies ____ cleaning, because offsets must refer to ____. A cleaning rule would create a new ____."
2. *Two extractors:* "The repo's `encode_pdf` and `read_pdf_to_string` give different ____, so the same character has ____."
3. *Corpus T (pending the file list, D-01/D-02):* "When T is chosen, I will rerun Tasks 1–8 on it and log every artifact with ____ and ____."

> Tell the tutor when you are done. The tutor grades `coding_independence_0_3` (Tasks 1, 2, 3, 5) and `debugging_0_3` (any failed CHECK you fixed yourself, and Task 4).
"""),
]

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "rag-learning (3.12.8)", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12.8", "file_extension": ".py", "mimetype": "text/x-python",
                          "codemirror_mode": {"name": "ipython", "version": 3},
                          "nbconvert_exporter": "python", "pygments_lexer": "ipython3"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
for i, c in enumerate(nb["cells"]):
    c["id"] = f"c1-{i:02d}"
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print(f"wrote {OUT}: {len(cells)} cells")
