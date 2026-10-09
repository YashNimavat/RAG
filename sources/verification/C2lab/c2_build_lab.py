"""Build labs/C2_chunking_lab.ipynb (blank-file-first scaffold, no solution code).

Every CHECK fingerprint is computed here by executing the given setup cell and the throwaway reference solution
(c2_solution_ref.py) in one namespace, then evaluating the SAME expression that the CHECK cell evaluates.
Run from rag_learning/:
    uv run python sources/verification/C2lab/c2_build_lab.py labs/C2_chunking_lab.ipynb > sources/verification/C2lab/out_c2_build_lab.txt
"""
import hashlib
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from c2_common import run_reference  # noqa: E402
from c2_setup import SETUP  # noqa: E402

OUT = sys.argv[1]
NS = run_reference(os.path.join(HERE, "c2_solution_ref.py"))
FPS = {}


def fp(name, expr):
    """Evaluate a fingerprint expression in the reference namespace; return the line fragment for a CHECK."""
    v = eval(expr, NS)
    assert isinstance(v, str) and len(v) == 16, (name, v)
    FPS[name] = (expr, v)
    return f'{expr} == "{v}"'


# ---- the reference values the CHECK cells rely on (also printed for C2LAB_FACTS.md) ----
KEYS = ["doc_id", "snapshot_id", "chunk_id", "seq", "char_start", "char_end", "page_segments", "text",
        "text_sha256", "chunker", "params_hash", "meta"]
recs = NS["records"]
PH = NS["params_hash"](NS["PARAMS"])
JSONL = "".join(json.dumps({k: r[k] for k in KEYS}, ensure_ascii=False) + "\n" for r in recs).encode("utf-8")
JSONL_SHA = hashlib.sha256(JSONL).hexdigest()
assert len(recs) == 97 and PH == "1ca9c5a3b548"
SWEEP = "[(10, 3), (8, 4), (300, 60), (7, 6), (5, 0)]"
TOY_PAGES = '["abc def", "", "ghi jk"]'
P_ARGS = "[(1000, 0, 500), (1000, 200, 500), (1000, 400, 500), (1000, 200, 200), (1000, 200, 201), (1000, 200, 202), (1000, 200, 250), (300, 60, 71)]"


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text, tag, task=None):
    meta = {"tags": [tag]}
    if task:
        meta["task"] = task
    return {"cell_type": "code", "execution_count": None, "metadata": meta, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


def learner(task, what):
    return code(f"# Your code here ({what}). Blank-file first: write it yourself; no copying from 07 H.1 or sources/verification/.",
                "learner", task)


cells = [
    md("""
# C2 lab: chunking with offsets you can trust

Lesson: [07 Sample lesson (C2)](../07_SAMPLE_LESSON.md): Part H.1 (code), D.2–D.4 (math), D.8–D.9 (pages and metadata), Part F (worked example), Part L (items C2-A-01, C2-A-03, C2-A-05). Interface: [06 §2.3](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#23-provider-agnostic-interfaces) (chunk record) and [06 §3.1](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#31-stage-by-stage-specification) (v0 chunker).

**How this lab works (blank-file first).**
- Each task has a **task cell**, an **empty code cell** for you, and a **CHECK cell** (`# CHECK`, do not edit). Run the CHECK after your code. If it fails, read the message and fix your code.
- This notebook has **no solution code**. Write every line yourself. Do not copy from 07 H.1 or from `sources/verification/C2lab/` (that folder holds a solution). Open them only after an honest try and a hint from the tutor (CR-04).
- **Predict first** where a task says so: fill the prediction cell **before** you write or run code. The CHECK cells refuse to run without it.
- CHECK cells compare **fingerprints** (`_fp`), so the answers stay hidden until you have tried.
- **Units:** every size and overlap here is in **characters** (Python `len`).
- Pure Python 3.12 plus PyMuPDF for loading. No API calls. Kernel: the project uv environment (`rag-learning`). Run the cells top to bottom.
- What you build in Task 7 is the **v0 chunk record** that C3 (indexing) reads. The last cell states its exact shape.
"""),
    md("""
## Setup (given)

Run this cell. It loads Corpus D the way C1 and [06 §5.3](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#53-corpus-freezing) define it, so this lab does not depend on your C1 code:
- `pages`: the 33 page texts from PyMuPDF 1.26.7 `page.get_text()`, no cleaning;
- `doc_text`: the pages joined with one `"\\n"`; `page_starts[i]`: where page `i + 1` starts in `doc_text`;
- `SNAPSHOT_ID`: recomputed with the 06 §5.3 recipe; the cell stops if it is not `ea07572562ac`;
- `PARAMS`: the v0 chunking settings, copied from 06 §2.4; `SEPARATORS = PARAMS["separators"]`;
- the small inputs `T`, `W`, `PARA`, `FACT_SPAN`, and the helpers the CHECK cells use (`_fp`, `_names`, `_spans`, `_limited`).
"""),
    code(SETUP, "given"),

    # ---------------- Task 1 ----------------
    md("""
## Task 1: trace fixed windows by hand (C2-A-01)

No code yet. `T = "abcdefghijklmnopqrstuvw"` has 23 characters.

A window of size S starts every S − O characters (the **stride**). The last window is cut at the end of the text, and no window starts after one has reached the end. Spans are half-open, like Python slices: `(0, 10)` means `T[0:10]`.

**Predict:** write the `(start, end)` spans of
- `fixed_window_chunks(T, 10, 3)`, and
- `fixed_window_chunks(T, 8, 4)`.

Then your confidence: 1 = guessing, 2 = fairly sure, 3 = sure.
"""),
    code("""
my_spans_10_3 = []          # e.g. [(0, 10), ...]
my_spans_8_4 = []
my_confidence_t1 = None     # 1, 2 or 3
""", "prediction", "T1"),
    code("""
# CHECK Task 1 (do not edit)
for _s in (my_spans_10_3, my_spans_8_4):
    assert _s and all(len(x) == 2 and all(isinstance(v, int) for v in x) for x in _s), "write each span as (start, end) with two ints"
assert my_confidence_t1 in (1, 2, 3), "confidence must be 1, 2 or 3"
print("Task 1 recorded. Task 2's CHECK compares it with your code.")
""", "check"),

    # ---------------- Task 2 ----------------
    md("""
## Task 2: `Chunk` and `fixed_window_chunks` (07 H.1, from a blank cell)

Write two things.

1. **`Chunk`**: a frozen dataclass with the fields `chunk_id` (int: its position in the list), `text`, `char_start`, `char_end`, in that order. Offsets are half-open: `text == source[char_start:char_end]`.
2. **`fixed_window_chunks(text, size, overlap=0)`** → a list of `Chunk`:
   - raise `ValueError` unless `size > 0` and `0 <= overlap < size`;
   - window k covers `[k * stride, k * stride + size)` with `stride = size - overlap`, cut at `len(text)`;
   - stop as soon as a window reaches the end of the text;
   - empty text gives `[]`.

The CHECK counts your windows for many text lengths, so an off-by-one in the stride shows up.
"""),
    learner("T2", "Task 2"),
    code(f"""
# CHECK Task 2 (do not edit)
import dataclasses
for _a in (("abc", 10, 10), ("abc", 10, 11), ("abc", 10, -1), ("abc", 0, 0)):
    try:
        _limited(fixed_window_chunks, *_a)
    except ValueError:
        continue
    raise AssertionError(f"fixed_window_chunks{{_a}} must raise ValueError (need size > 0 and 0 <= overlap < size)")
assert fixed_window_chunks("", 5, 2) == [], "empty text must give []"
_c = fixed_window_chunks(T, 10, 3)
assert dataclasses.is_dataclass(_c[0]) and [f.name for f in dataclasses.fields(_c[0])] == ["chunk_id", "text", "char_start", "char_end"], \\
    "Chunk must be a dataclass with the fields chunk_id, text, char_start, char_end (in that order)"
try:
    _c[0].text = "changed"
    raise AssertionError("Chunk must be frozen: @dataclass(frozen=True)")
except dataclasses.FrozenInstanceError:
    pass
assert all(c.chunk_id == i and c.text == T[c.char_start:c.char_end] for i, c in enumerate(_c)), "chunk_id = position, text = T[char_start:char_end]"
assert {fp("t2_a01", "_fp([_spans(fixed_window_chunks(T, 10, 3)), _spans(fixed_window_chunks(T, 8, 4))])")}, \\
    "the spans for T are not right yet: check where each window starts and where you stop"
assert {fp("t2_counts", f"_fp([[len(fixed_window_chunks('x' * L, S, O)) for L in range(1, 5 * S + 1)] for S, O in {SWEEP}])")}, \\
    "the number of windows is wrong for some lengths: compare with 07 D.2, ceil((L - O) / (S - O)) for L > S"
_d = fixed_window_chunks(doc_text, 1000, 200)
assert len(_d) == 91, f"doc_text at 1000/200 should give 91 windows, got {{len(_d)}}"
_ok = [list(x) for x in my_spans_10_3] == [list(x) for x in _spans(_c)] and \\
      [list(x) for x in my_spans_8_4] == [list(x) for x in _spans(fixed_window_chunks(T, 8, 4))]
print(f"Task 2 OK. Your Task 1 hand trace was {{'right' if _ok else 'not right'}} (confidence {{my_confidence_t1}}): log it.")
print(f"doc_text: {{len(doc_text):,}} characters -> {{len(_d)}} windows at 1000/200 (07 D.2 also gets 91 on PyPDFLoader's 72,523 characters).")
""", "check"),

    # ---------------- Task 3 ----------------
    md("""
## Task 3: `check_chunks`, your safety net (07 H.1)

Write `check_chunks(text, chunks, size)`. It returns nothing when the chunks are fine. It fails with `assert` (an `AssertionError`) when:
- the list is empty;
- the first chunk does not start at 0, or the last chunk does not end at `len(text)`;
- a chunk's text is not `text[char_start:char_end]` (the **offset round-trip**);
- a chunk is empty or longer than `size`;
- two neighbours leave a gap, or a chunk does not start after the one before it.

The CHECK gives it good chunks, then seven broken lists. Every broken list must fail.
"""),
    learner("T3", "Task 3"),
    code("""
# CHECK Task 3 (do not edit)
import dataclasses
_g = [Chunk(i, T[a:b], a, b) for i, (a, b) in enumerate([(0, 12), (8, 20), (16, 23)])]   # good: size 12, overlap 4
check_chunks(T, _g, 12)
check_chunks(PARA, fixed_window_chunks(PARA, 300, 60), 300)
check_chunks(doc_text, fixed_window_chunks(doc_text, 1000, 200), 1000)
_bad = {
    "empty list": (T, [], 12),
    "first chunk does not start at 0": (T, _g[1:], 12),
    "last chunk does not reach the end": (T, _g[:2], 12),
    "text does not match its offsets": (T, [_g[0], dataclasses.replace(_g[1], char_start=9), _g[2]], 12),
    "a chunk longer than size": (T, _g, 11),
    "a gap between neighbours": (T, [_g[0], _g[2]], 12),
    "a chunk that does not move forward": (T, [_g[0], _g[0], _g[1], _g[2]], 12),
}
_missed = []
for _name, (_t, _ch, _size) in _bad.items():
    try:
        check_chunks(_t, _ch, _size)
        _missed.append(_name)
    except AssertionError:
        pass
    except Exception as e:
        raise AssertionError(f"'{_name}': fail with assert, not {type(e).__name__}: {e}")
assert not _missed, f"check_chunks did not catch: {_missed}"
print(f"Task 3 OK. check_chunks passes good chunks and catches all {len(_bad)} broken lists.")
""", "check"),

    # ---------------- Task 4 ----------------
    md("""
## Task 4: when does overlap keep a fact whole? (07 D.3, Part F)

`PARA` is the 785-character paragraph from 07 Part F. The fact sits at `FACT_SPAN = (558, 629)`, so its length is F = 71.

**Predict, one question at a time (no code):**
1. Fixed windows of 300 with overlap 0: which chunk ids **wholly** contain the fact? (A list; `[]` if none.)
2. The same with overlap 60.
3. With S = 1000 and O = 200: what is the **largest** fact length F that is whole in some chunk **wherever** it starts?
"""),
    code("""
my_fact_chunks_o0 = None        # a list of chunk ids, e.g. [1]
my_fact_chunks_o60 = None       # a list of chunk ids
my_largest_guaranteed_f = None  # an int
my_confidence_t4 = None         # 1, 2 or 3
""", "prediction", "T4p"),
    md("""
Now write three functions.
- `chunks_containing(chunks, start, end)` → the ids of the chunks with `char_start <= start` and `end <= char_end`.
- `p_formula(S, O, F)` → the D.3 formula `min(1, (S - F + 1) / (S - O))`.
- `p_brute(L, S, O, F)` → the share of start positions `p = 0, 1, …, L - F` whose span `[p, p + F)` lies wholly inside some chunk of **your** `fixed_window_chunks` on a text of length L (any text works, e.g. `"x" * L`). Chunk once, then loop over p.

The formula describes positions far from the edges. The brute force counts the whole finite text, so it comes out a little higher (07 D.3, last column).
"""),
    learner("T4", "Task 4"),
    code(f"""
# CHECK Task 4 (do not edit)
assert isinstance(my_fact_chunks_o0, list) and isinstance(my_fact_chunks_o60, list) and isinstance(my_largest_guaranteed_f, int) \\
    and my_confidence_t4 in (1, 2, 3), "fill all four predictions first"
assert {fp("t4_contain", "_fp([chunks_containing(fixed_window_chunks(PARA, 300, 0), *FACT_SPAN), chunks_containing(fixed_window_chunks(PARA, 300, 60), *FACT_SPAN), chunks_containing(fixed_window_chunks(T, 10, 3), 6, 9), chunks_containing(fixed_window_chunks(T, 10, 3), 8, 10)])")}, \\
    "chunks_containing is not right yet: a chunk contains [start, end) when char_start <= start and end <= char_end"
assert {fp("t4_formula", f"_fp([round(p_formula(S, O, F), 3) for S, O, F in {P_ARGS}])")}, \\
    "p_formula is not right yet: min(1, (S - F + 1) / (S - O))"
assert "fixed_window_chunks" in _names(p_brute), "p_brute must use your fixed_window_chunks"
assert {fp("t4_brute", "_fp([round(p_brute(20000, 1000, O, 500), 4) for O in (0, 200, 400)])")}, \\
    "p_brute is not right yet: count p = 0 .. L - F, and divide by the number of positions (L - F + 1)"
assert p_brute(20000, 1000, 200, 201) == 1.0 and p_brute(20000, 1000, 200, 202) < 1.0, \\
    "at S = 1000, O = 200, a 201-character fact must always be whole and a 202-character fact not always"
_a0 = chunks_containing(fixed_window_chunks(PARA, 300, 0), *FACT_SPAN)
_a60 = chunks_containing(fixed_window_chunks(PARA, 300, 60), *FACT_SPAN)
print(f"Task 4 OK.  overlap 0: predicted {{my_fact_chunks_o0}}, actual {{_a0}};  overlap 60: predicted {{my_fact_chunks_o60}}, actual {{_a60}}")
print(f"largest always-whole F at 1000/200: predicted {{my_largest_guaranteed_f}}, actual 201 (= O + 1, 07 D.3)")
print(f"P(contained) for the 71-character fact at 300/60: formula {{p_formula(300, 60, 71):.3f}}; interior 1000/200/500: {{p_formula(1000, 200, 500):.3f}}, whole text L = 20,000: {{p_brute(20000, 1000, 200, 500):.4f}}")
""", "check"),

    # ---------------- Task 5 ----------------
    md("""
## Task 5: the recursive splitter (07 D.4; v0 uses it)

Hand trace first (C2-A-03). `W = "the cat sat on the mat"` (22 characters), size 10, overlap 4.
- **Split:** cut on spaces; each space stays at the **end** of the piece before it: `"the "`, `"cat "`, `"sat "`, …
- **Merge:** add pieces while the chunk stays ≤ 10 characters. When the next piece does not fit, emit the chunk. The next chunk starts with the old chunk's **whole trailing pieces** that total ≤ 4 characters.

**Predict:** the `(start, end)` spans of the chunks.
"""),
    code("""
my_w_spans = []             # e.g. [(0, 8), ...]
my_confidence_t5 = None     # 1, 2 or 3
""", "prediction", "T5p"),
    md("""
Now write two functions. This is the hardest task: re-read the **text** of 07 D.4 (not the H.1 code), and ask the tutor for a hint (H1–H3) when you are stuck.

1. `split_spans(text, start, end, separators, size)` → a list of `(a, b)` pieces that tile `[start, end)` exactly, each at most `size` long.
   - If `[start, end)` already fits, return it as one piece.
   - Otherwise split on the **first** separator. Each piece ends just **after** a separator.
   - A piece that is still longer than `size` is split again with the **remaining** separators.
   - `""` means "single characters". Careful: `text.find("", i)` always returns `i`, so a find loop on `""` never moves.
2. `recursive_chunks(text, size, overlap=0, separators=SEPARATORS)` → a list of `Chunk`.
   - Same `ValueError` rule as Task 2; empty text gives `[]`.
   - Merge the pieces as in the hand trace. The overlap budget is counted in **characters**.
   - If the next piece still does not fit after keeping the overlap pieces, drop pieces from the front.
   - Never strip whitespace: offsets must stay exact.

`SEPARATORS` is the v0 list from 06: `["\\n\\n", "\\n", " ", ""]`.
"""),
    learner("T5", "Task 5"),
    code(f"""
# CHECK Task 5 (do not edit)
import random
assert my_w_spans and my_confidence_t5 in (1, 2, 3), "fill your prediction and confidence first"
assert {fp("t5_pieces", "_fp(split_spans(W, 0, len(W), SEPARATORS, 10))")}, \\
    "split_spans(W, 0, 22, SEPARATORS, 10) is not right yet: pieces end just after each space"
assert {fp("t5_long", "_fp(_spans(_limited(recursive_chunks, 'short ' + 'x' * 25 + ' tail', 10, 0)))")}, \\
    "a 25-character word must be cut into single characters (the '' separator) and merged back"
for _a in (("abc", 4, 4), ("abc", 4, 5), ("abc", 4, -1)):
    try:
        _limited(recursive_chunks, *_a)
    except ValueError:
        continue
    raise AssertionError(f"recursive_chunks{{_a}} must raise ValueError")
assert recursive_chunks("", 5, 2) == [], "empty text must give []"
assert {fp("t5_w", "_fp(_spans(recursive_chunks(W, 10, 4)))")}, \\
    "recursive_chunks(W, 10, 4) is not right yet: compare with your hand trace, step by step"
assert {fp("t5_para", "_fp(_spans(recursive_chunks(PARA, 300, 60)))")}, \\
    "recursive_chunks(PARA, 300, 60) is not right yet (07 Part F, step 3)"
_rng = random.Random(0)
_words = "alpha beta gamma delta\\n\\nepsilon zeta\\neta theta iota supercalifragilistic".split(" ")
for _ in range(200):
    _t = " ".join(_rng.choice(_words) for _ in range(_rng.randint(1, 120)))
    _size = _rng.randint(2, 150); _ov = _rng.randint(0, _size - 1)
    _ch = recursive_chunks(_t, _size, _ov)
    check_chunks(_t, _ch, _size)
    _real = [a.char_end - b.char_start for a, b in zip(_ch, _ch[1:])]
    assert all(0 <= x <= _ov for x in _real), f"real overlap {{max(_real)}} > overlap {{_ov}} characters: count the overlap in characters"
    assert [c.chunk_id for c in _ch] == list(range(len(_ch))), "chunk_id must be the position"
_rd = recursive_chunks(doc_text, 1000, 200)
check_chunks(doc_text, _rd, 1000)
assert len(_rd) == 92, f"doc_text at 1000/200 should give 92 recursive chunks, got {{len(_rd)}}"
print(f"Task 5 OK. W: predicted {{my_w_spans}}, actual {{_spans(recursive_chunks(W, 10, 4))}}")
print(f"PARA 300/60: {{_spans(recursive_chunks(PARA, 300, 60))}}; the fact is in chunk {{chunks_containing(recursive_chunks(PARA, 300, 60), *FACT_SPAN)}}")
print(f"doc_text 1000/200, one piece of text: {{len(_rd)}} chunks (07 H.1 also 92 on PyPDFLoader text)")
""", "check"),

    # ---------------- Task 6 ----------------
    md("""
## Task 6: per-page scope with document offsets (06 §3.1, 07 D.8)

v0 chunks **each page on its own** (`scope = per_page`), so no chunk crosses a page break. Offsets must still be **document** offsets into `doc_text` (06 §2.3): one coordinate system, the one gold spans use.

For comparison: the same splitter on the whole joined text gave 92 chunks, and 41 of them cross a page break. (07 D.8 says 39: that count came from PyPDFLoader's text, 72,523 characters. This lab uses PyMuPDF's text, 72,593 characters.)

**Predict:** how many chunks does per-page chunking at 1000/200 give? (One number.)
"""),
    code("""
my_guess_per_page_count = None   # an int
""", "prediction", "T6p"),
    md("""
Now write `chunk_pages(pages, size, overlap)` → a list of `(char_start, char_end, page)` tuples in document order:
- run your `recursive_chunks` on each page text;
- add that page's start offset in the joined text (each earlier page counts its length plus 1 for the joining `"\\n"`); work it out from the `pages` you are given;
- `page` is 1-based.
"""),
    learner("T6", "Task 6"),
    code(f"""
# CHECK Task 6 (do not edit)
assert isinstance(my_guess_per_page_count, int), "write your prediction first"
_cp = chunk_pages(pages, 1000, 200)
assert all(len(x) == 3 for x in _cp), "return (char_start, char_end, page) tuples"
_rel = [(a, b, p) for a, b, p in _cp if a < page_starts[p - 1]]
assert not _rel, f"{{len(_rel)}} chunks start before their own page, e.g. {{_rel[0]}}: page-relative offsets? Add the page's start offset (C2-A-05)"
_cross = [(a, b, p) for a, b, p in _cp if not page_starts[p - 1] <= a < b <= page_starts[p - 1] + len(pages[p - 1])]
assert not _cross, f"{{len(_cross)}} chunks run past the end of their page, e.g. {{_cross[0]}}: per-page scope means no chunk crosses a page"
_bad = [(a, b, p) for a, b, p in _cp if not doc_text[a:b] == pages[p - 1][a - page_starts[p - 1]:b - page_starts[p - 1]]]
assert not _bad, f"{{len(_bad)}} chunks fail the offset round-trip on doc_text, e.g. {{_bad[0]}}"
assert all(x[0] < y[0] and x[2] <= y[2] for x, y in zip(_cp, _cp[1:])), "keep document order"
for _i, _p in enumerate(pages):
    assert [(a - page_starts[_i], b - page_starts[_i]) for a, b, p in _cp if p == _i + 1] == _spans(recursive_chunks(_p, 1000, 200)), \\
        f"page {{_i + 1}}: the chunks must be recursive_chunks(page text, 1000, 200), shifted to document offsets"
assert {fp("t6_toy", f"_fp([list(x) for x in chunk_pages({TOY_PAGES}, 4, 1)])")}, \\
    "a toy with an empty page fails: work out the page starts from the pages you are given (length + 1 per page)"
assert {fp("t6_all", "_fp([list(x) for x in chunk_pages(pages, 1000, 200)])")}, "the per-page spans are not right yet"
_l = sorted(b - a for a, b, p in _cp)
print(f"Task 6 OK. per-page 1000/200: predicted {{my_guess_per_page_count}}, actual {{len(_cp)}} (one piece of text: 92)")
print(f"lengths min / median / max: {{_l[0]}} / {{_l[len(_l) // 2]}} / {{_l[-1]}}  (07 D.8 got 97 chunks, 391 / 933 / 999, on PyPDFLoader text)")
""", "check"),

    # ---------------- Task 7 ----------------
    md("""
## Task 7: the v0 chunk records (06 §2.3; C3 reads these)

Write two functions.

1. `params_hash(params)` → the first 12 hex characters of `sha256(json.dumps(params, sort_keys=True).encode("utf-8"))`. This lab fixes that recipe for v0 (see the last cell).
2. `make_records(doc_id, snapshot_id, pages, params)` → one dict per chunk of `chunk_pages(pages, params["chunk_size"], params["chunk_overlap"])`, with exactly these keys:

| Key | Value |
|---|---|
| `doc_id` | `doc_id` |
| `snapshot_id` | `snapshot_id` |
| `chunk_id` | `f"{doc_id}:{snapshot_id}:{params_hash}:{seq:05d}"` |
| `seq` | 0, 1, 2, … in document order |
| `char_start`, `char_end` | document offsets into the pages joined with `"\\n"` |
| `page_segments` | a list with one dict `{"page": …, "char_start": …, "char_end": …}`, offsets relative to that page |
| `text` | the chunk text |
| `text_sha256` | the sha256 hex digest of `text` (UTF-8) |
| `chunker` | `params["name"]` |
| `params_hash` | `params_hash(params)` |
| `meta` | `{}` |

The same inputs must always give the same ids. So: no `uuid`, no `random`, no clock, and no Python `hash()` (for strings it changes every time Python starts).
"""),
    learner("T7", "Task 7"),
    code(f"""
# CHECK Task 7 (do not edit)
_KEYS = ["doc_id", "snapshot_id", "chunk_id", "seq", "char_start", "char_end", "page_segments", "text",
         "text_sha256", "chunker", "params_hash", "meta"]
assert re.fullmatch(r"[0-9a-f]{{12}}", params_hash(PARAMS)), "params_hash must be 12 lowercase hex characters"
assert {fp("t7_ph", "_fp(params_hash(PARAMS))")}, "params_hash is not right yet: sha256 of json.dumps(params, sort_keys=True), first 12 hex"
_r = make_records(DOC_ID, SNAPSHOT_ID, pages, PARAMS)
assert all(set(x) == set(_KEYS) for x in _r), f"each record needs exactly the keys {{_KEYS}}"
# offset round-trip
assert all(doc_text[x["char_start"]:x["char_end"]] == x["text"] for x in _r), "text must equal doc_text[char_start:char_end]"
# per-page scope: one segment, inside its page, converting back to the document range
for x in _r:
    assert len(x["page_segments"]) == 1, f"{{x['chunk_id']}}: a per-page chunk has exactly one page segment"
    _s = x["page_segments"][0]
    _p0 = page_starts[_s["page"] - 1]
    assert (_p0 + _s["char_start"], _p0 + _s["char_end"]) == (x["char_start"], x["char_end"]) and _s["char_end"] <= len(pages[_s["page"] - 1]), \\
        f"{{x['chunk_id']}}: the page segment must be page-relative and convert back to [char_start, char_end) inside its page"
assert all(x["text_sha256"] == hashlib.sha256(x["text"].encode("utf-8")).hexdigest() for x in _r), "text_sha256 = sha256 of the UTF-8 text"
assert all(x["seq"] == i and x["doc_id"] == DOC_ID and x["snapshot_id"] == SNAPSHOT_ID and x["chunker"] == PARAMS["name"]
           and x["params_hash"] == params_hash(PARAMS) and x["meta"] == {{}} for i, x in enumerate(_r)), "check seq, doc_id, snapshot_id, chunker, params_hash, meta"
# deterministic ids
assert not ({{"uuid1", "uuid4", "random", "randint", "time", "time_ns", "now", "hash", "id"}} & _names(make_records)), \\
    "ids must not use uuid, random, the clock, hash() or id()"
assert [x["chunk_id"] for x in make_records(DOC_ID, SNAPSHOT_ID, pages, PARAMS)] == [x["chunk_id"] for x in _r], "two runs must give the same ids"
assert all(x["chunk_id"] == f"{{DOC_ID}}:{{SNAPSHOT_ID}}:{{params_hash(PARAMS)}}:{{i:05d}}" for i, x in enumerate(_r)), \\
    "chunk_id must be f'{{doc_id}}:{{snapshot_id}}:{{params_hash}}:{{seq:05d}}'"
_r2 = make_records(DOC_ID, SNAPSHOT_ID, pages, dict(PARAMS, chunk_overlap=199))
assert not ({{x["chunk_id"] for x in _r2}} & {{x["chunk_id"] for x in _r}}), "a different overlap must give a different params_hash and new ids"
assert {fp("t7_records", "_fp(make_records(DOC_ID, SNAPSHOT_ID, pages, PARAMS))")}, "the records differ from the v0 reference somewhere"
print(f"Task 7 OK. {{len(_r)}} records; params_hash {{params_hash(PARAMS)}}; first id {{_r[0]['chunk_id']}}; last id {{_r[-1]['chunk_id']}}")
""", "check"),

    # ---------------- Task 8 ----------------
    md("""
## Task 8: how much overlap did you really get? (07 D.4, L.6)

You asked for 200 characters of overlap. Before you measure:

**Predict:** is the real overlap between neighbouring chunks on a page **always exactly 200**? (`True` or `False`)
"""),
    code("""
my_guess_all_200 = None   # True or False
""", "prediction", "T8p"),
    md("""
Now write `achieved_overlaps(records)` → a list of ints: for each pair of neighbouring records **on the same page**, the previous record's `char_end` minus the next record's `char_start`, in order.
"""),
    learner("T8", "Task 8"),
    code(f"""
# CHECK Task 8 (do not edit)
assert my_guess_all_200 in (True, False), "write your prediction first"
_ao = achieved_overlaps(make_records(DOC_ID, SNAPSHOT_ID, pages, PARAMS))
assert all(isinstance(x, int) for x in _ao), "return a list of ints"
assert all(0 <= x <= PARAMS["chunk_overlap"] for x in _ao), f"some overlap is above {{PARAMS['chunk_overlap']}}: the budget is in characters"
assert {fp("t8_ao", "_fp(achieved_overlaps(make_records(DOC_ID, SNAPSHOT_ID, pages, PARAMS)))")}, \\
    "achieved_overlaps is not right yet: only pairs on the same page, previous char_end minus next char_start"
import statistics
print(f"Task 8 OK. {{len(_ao)}} same-page pairs; real overlap min / median / max = {{min(_ao)}} / {{statistics.median(_ao)}} / {{max(_ao)}}; exactly 200: {{_ao.count(200)}}")
print(f"You predicted 'always 200' = {{my_guess_all_200}}; actual = {{all(x == 200 for x in _ao)}}.")
print(f"First four: {{_ao[:4]}}. 07 H.2 shows 180, 140, 197, 177: LangChain on PyPDFLoader text, which also strips spaces at chunk edges.")
""", "check"),

    # ---------------- Save ----------------
    md("""
## Save the records (given)

Run this after Task 8 passes. It writes `C2_out/<snapshot_id>_<params_hash>/chunks.jsonl` next to this notebook (one JSON object per line, keys in the 06 order) and compares the file with the v0 reference. Only a matching file should go to C3.
"""),
    code(f"""
# CHECK save (do not edit)
from pathlib import Path
_KEYS = ["doc_id", "snapshot_id", "chunk_id", "seq", "char_start", "char_end", "page_segments", "text",
         "text_sha256", "chunker", "params_hash", "meta"]
records = make_records(DOC_ID, SNAPSHOT_ID, pages, PARAMS)
_data = "".join(json.dumps({{k: x[k] for k in _KEYS}}, ensure_ascii=False) + "\\n" for x in records).encode("utf-8")
_dir = Path("C2_out") / f"{{SNAPSHOT_ID}}_{{records[0]['params_hash']}}"
_dir.mkdir(parents=True, exist_ok=True)
(_dir / "chunks.jsonl").write_bytes(_data)
_sha = hashlib.sha256(_data).hexdigest()
print(f"wrote {{_dir / 'chunks.jsonl'}}: {{len(records)}} lines, {{len(_data):,}} bytes, sha256 {{_sha}}")
assert _sha == "{JSONL_SHA}", "the file differs from the v0 reference: do not hand it to C3"
print("Matches the v0 reference file.")
""", "check"),

    md("""
## Wrap-up: evidence for the log

Answer **one at a time**, in one or two lines each, closed book. Copy the template and fill the blanks.

1. *Boundary:* "With overlap 200, a fact is **always** whole only if it is at most ____ characters long, because ____. Confidence (1–3): __"
2. *Per-page scope:* "Per-page chunks make `[doc:page]` citations exact because ____. The cost is ____ (07 D.8). Overlap cannot fix it because ____. Confidence: __"
3. *Ids:* "`chunk_id` is not a cache key because ____; the embedding cache is keyed by ____. Confidence: __"
4. *Predictions:* "Task 1: ____; Task 4: __ of 3 right; Task 5: ____; Task 6: I guessed ____, it was ____; Task 8: ____."

> Tell the tutor when you are done. The tutor grades `coding_independence_0_3` (Tasks 2, 3 and 5) and `debugging_0_3` (any failed CHECK you fixed yourself).
"""),
    md(f"""
## Output: what C3 receives (the v0 chunk interface)

`records = make_records(DOC_ID, SNAPSHOT_ID, pages, PARAMS)`: a `list` of **97** `dict`s, in document order (`seq` 0…96), saved as `C2_out/ea07572562ac_{PH}/chunks.jsonl` (UTF-8, one JSON object per line, `ensure_ascii=False`, keys in this order, sha256 `{JSONL_SHA}`).

| Key | Type | v0 value on Corpus D |
|---|---|---|
| `doc_id` | str | `"climate"` |
| `snapshot_id` | str, 12 hex | `"ea07572562ac"` (06 §5.3 recipe; PyMuPDF 1.26.7, no cleaning, pages joined with `"\\n"`) |
| `chunk_id` | str | `f"{{doc_id}}:{{snapshot_id}}:{{params_hash}}:{{seq:05d}}"`, e.g. `"climate:ea07572562ac:{PH}:00000"`; for joins and traces, **never** a cache key |
| `seq` | int | 0-based position in the document's chunk list |
| `char_start`, `char_end` | int | **document** offsets into `doc_text`, half-open: `doc_text[char_start:char_end] == text` |
| `page_segments` | list of 1 dict | `[{{"page": int (1-based), "char_start": int, "char_end": int}}]`, page-relative; per-page scope gives exactly one segment |
| `text` | str | raw extracted text, no stripping or cleaning |
| `text_sha256` | str, 64 hex | `sha256(text.encode("utf-8")).hexdigest()`; content identity for the embedding cache key (06 §2.4) |
| `chunker` | str | `"recursive_char"` (06 §2.4 `chunking.name`) |
| `params_hash` | str, 12 hex | `"{PH}"` = `sha256(json.dumps(PARAMS, sort_keys=True).encode("utf-8")).hexdigest()[:12]` |
| `meta` | dict | `{{}}` in v0 |

`PARAMS` = `{json.dumps(NS["PARAMS"], sort_keys=True)}` (06 §2.4/§3.1: recursive, characters, 1000/200, per page). The splitter keeps separators at the end of the piece before them and never strips whitespace, so offsets are exact; `""` means single characters.

Interface assumptions (06 does not fix these; recorded in `sources/verification/C2lab/C2LAB_FACTS.md`): the `params_hash` recipe above; `page_segments` serialised as a list of dicts; `chunker` = `"recursive_char"`. 07 H.3's `ChunkerConfig` hashes different field names (`name="recursive"`, `size`, `overlap`, no `""` separator) and gives `77bc4c45809b` for the same spans; never mix the two id sets.
"""),
]

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "rag-learning (3.12.8)", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12.8", "file_extension": ".py", "mimetype": "text/x-python",
                          "codemirror_mode": {"name": "ipython", "version": 3}, "nbconvert_exporter": "python",
                          "pygments_lexer": "ipython3"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
for i, c in enumerate(nb["cells"]):
    c["id"] = f"c2-{i:02d}"
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
    f.write("\n")

print(f"wrote {OUT}: {len(cells)} cells "
      f"({sum(c['cell_type'] == 'markdown' for c in cells)} markdown, {sum(c['cell_type'] == 'code' for c in cells)} code; "
      f"{sum('check' in c['metadata'].get('tags', []) for c in cells)} CHECK, "
      f"{sum('learner' in c['metadata'].get('tags', []) for c in cells)} learner, "
      f"{sum('prediction' in c['metadata'].get('tags', []) for c in cells)} prediction)")
print("fingerprints (name, expression evaluated on the reference, value):")
for k, (e, v) in FPS.items():
    print(f"  {k:11s} {v}  {e}")
print("values behind the fingerprints (reference):")
print(f"  t2_a01     {[NS['_spans'](NS['fixed_window_chunks'](NS['T'], 10, 3)), NS['_spans'](NS['fixed_window_chunks'](NS['T'], 8, 4))]}")
print(f"  t4_contain {[NS['chunks_containing'](NS['fixed_window_chunks'](NS['PARA'], 300, o), *NS['FACT_SPAN']) for o in (0, 60)]} + T(10,3) [6,9) {NS['chunks_containing'](NS['fixed_window_chunks'](NS['T'], 10, 3), 6, 9)}, [8,10) {NS['chunks_containing'](NS['fixed_window_chunks'](NS['T'], 10, 3), 8, 10)}")
print(f"  t4_formula {[round(NS['p_formula'](*a), 3) for a in eval(P_ARGS)]}")
print(f"  t4_brute   {[round(NS['p_brute'](20000, 1000, o, 500), 4) for o in (0, 200, 400)]}")
print(f"  t5_pieces  {NS['split_spans'](NS['W'], 0, len(NS['W']), NS['SEPARATORS'], 10)}")
print(f"  t5_long    {NS['_spans'](NS['recursive_chunks']('short ' + 'x' * 25 + ' tail', 10, 0))}")
print(f"  t5_w       {NS['_spans'](NS['recursive_chunks'](NS['W'], 10, 4))}")
print(f"  t5_para    {NS['_spans'](NS['recursive_chunks'](NS['PARA'], 300, 60))}")
print(f"  t6_toy     {NS['chunk_pages'](eval(TOY_PAGES), 4, 1)}")
cp = NS["chunk_pages"](NS["pages"], 1000, 200)
print(f"  t6_all     {len(cp)} spans; first {cp[:3]}; last {cp[-1]}")
print(f"  t7_ph      {PH}")
print(f"  t7_records {len(recs)} records (= out_c2_measure.txt M6)")
ao = NS["achieved_overlaps"](recs)
print(f"  t8_ao      {len(ao)} values; min/median/max {min(ao)}/{statistics.median(ao)}/{max(ao)}; first {ao[:4]}")
print(f"  save       chunks.jsonl sha256 {JSONL_SHA} ({len(JSONL)} bytes)")
