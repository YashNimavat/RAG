"""Build study/notebooks/P2_ir_framing_verify.ipynb: the "verify it yourself" notebook for P2 (information-retrieval framing).

The notebook rebuilds every measured number and chart of the P2 lesson (study/lessons/P2_ir_framing.html) from code,
one section per lesson step (1-12), and compares each value with the lesson's value in a `check(...)` line. The
expected values are copied from sources/verification/P2/P2_FACTS.md (S1-S11; their output out_p2_measure.txt) and
section 1b (K1-K6; output out_p2_kit_measure.txt). The code paths are the ones of p2_measure.py and p2_kit_measure.py
(same tokenizer, index, overlap ranking with ties by doc id ascending, MiniLM ranking, set metrics, windows and
any_overlap rule), so the numbers come out identical. The BEIR Table 4 values in step 10 are external (Thakur et al.
2021), shown as a chart and never re-measured. The research plan's optional ir-measures parity section is left out
(ir-measures is not installed).

No Groq, Cohere or Claude call, no .env read, no network (MiniLM loads from the local Hugging Face cache, offline).

Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P2/p2_build_verify_nb.py
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P2/p2_verify_nb_run.py \
        > sources/verification/P2/out_p2_verify_nb_run.txt                              # executes it, saves outputs
"""
from pathlib import Path
from textwrap import dedent

import nbformat as nbf

WS = Path(__file__).resolve().parents[3]                      # rag_learning/
OUT = WS / "study" / "notebooks" / "P2_ir_framing_verify.ipynb"

CELLS = []


def md(s):
    CELLS.append(nbf.v4.new_markdown_cell(dedent(s).strip()))


def code(s):
    CELLS.append(nbf.v4.new_code_cell(dedent(s).strip()))


# =====================================================================================================================
md(r"""
# P2 · Verify it yourself: similarity, relevance, the index and the labels

**What this is:** a notebook that rebuilds every measured number and chart of the P2 lesson from real code, so you can see each one being made and change the inputs.
**What this is not:** the lab (`labs/P2_ir_framing_lab.ipynb`, where you write the code yourself) or the quiz. It also makes **no API call**: no Groq, no Cohere, no Claude. Where the lesson uses an outside fact (BEIR's Table 4, the IIR agreement table), this notebook shows the fact and says where it comes from; it does not pretend to re-measure it.

**How to use it.** Run all cells from the top (VS Code: *Run All*). The sections are numbered like the lesson's steps, 1 to 12. Each one has:
- a short note on what it verifies;
- a code cell that **computes** the values;
- `check(...)` lines: `PASS` means the code produced the number the lesson shows, `FAIL` means it did not;
- an interactive chart where the lesson has a chart worth seeing. Hover for values.

The last cell counts the checks.

**Labels used for numbers.** *measured* = computed here from real text or a real model; *toy* = made-up inputs that show a mechanism; *formula* = arithmetic on counts; *external* = from a published paper or textbook, not re-run here.

**The running example.** The book's own question, "What is the main cause of climate change?" (Ch1 p.8/14), written as the keyword query `main cause of climate change` (toy query q1). It runs against a **toy corpus** of 10 short made-up documents with 5 queries and hand-written relevance labels (`sources/verification/P2/p2_toy_corpus.json`), because relevance must be judged by a person and these labels already exist. The climate PDF (`upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf`, 91 windows of 1,000 characters overlapping by 200) shows the same index at scale.

**Where the expected values come from.** `sources/verification/P2/P2_FACTS.md`: sections S1–S11 (`p2_measure.py`) and §1b K1–K6 (`p2_kit_measure.py`). MiniLM, the local embedding model, loads from the cache on this computer.
""")

code(r'''
# Setup: imports, paths, the toy corpus and the shared helpers. Run this cell first.
import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")          # MiniLM may load from the local cache only: no network
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

import hashlib
import importlib.metadata as md
import inspect
import json
import math
import re
import sys
import time
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
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
TOY_FILE = WS / "sources" / "verification" / "P2" / "p2_toy_corpus.json"
PDF = WS.parent / "upstream" / "RAG_Techniques" / "data" / "Understanding_Climate_Change.pdf"
print("workspace:", WS)
print("python", sys.version.split()[0], {p: md.version(p) for p in
      ("pymupdf", "numpy", "sentence-transformers", "scikit-learn", "rank-bm25", "plotly")})

# ---------------------------------------------------------------- check(): computed value vs the lesson's value
CHECKS, SKIPPED = [], []


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
    g, e = float(got), float(exp)
    if math.isnan(g) or math.isnan(e):
        return math.isnan(g) and math.isnan(e)
    return abs(g - e) <= tol


def _show(x):
    x = _plain(x)
    if isinstance(x, float):
        return "nan" if math.isnan(x) else (f"{x:.6f}".rstrip("0").rstrip(".") or "0")
    if isinstance(x, list):
        return "[" + ", ".join(_show(v) for v in x) + "]"
    if isinstance(x, dict):
        return "{" + ", ".join(f"{k}: {_show(v)}" for k, v in x.items()) + "}"
    return repr(x)


def check(name, got, expected, tol=0.0):
    """PASS when the computed value equals the lesson's value (numbers within `tol`)."""
    ok = _same(got, expected, tol)
    CHECKS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}: got {_show(got)}  |  lesson {_show(expected)}"
          + (f"  (tolerance {tol:g})" if tol else ""))      # returns None, so a cell ending in check() shows no "True"


def skip(name, reason):
    SKIPPED.append((name, reason))
    print(f"SKIPPED  {name}: {reason}")


def _fp(x):
    """The lab's fingerprint (p2_measure.py): first 16 hex characters of sha256 of the sorted JSON."""
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:16]


# ---------------------------------------------------------------- chart style (light surface, fixed colour order)
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"    # categorical slots 1-3, always in this order
LIGHT = "#cfe0f5"                                       # the light end of the blue scale
pio.templates["p2"] = go.layout.Template(layout=dict(
    font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', size=13, color=INK2),
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, colorway=[BLUE, ORANGE, AQUA],
    xaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    yaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=INK2)),
    title=dict(x=0, xanchor="left", font=dict(size=15, color=INK)),
    margin=dict(l=70, r=30, t=90, b=60), hoverlabel=dict(font_size=12)))
pio.templates.default = "p2"


def bar_style(colour):
    return dict(color=colour, line=dict(width=2, color=SURFACE))


# ---------------------------------------------------------------- environment (K1, S1)
check("environment: pymupdf version (pinned)", md.version("pymupdf"), "1.26.7")
check("environment: numpy, sentence-transformers, scikit-learn, rank-bm25 (K1, S1)",
      [md.version(p) for p in ("numpy", "sentence-transformers", "scikit-learn", "rank-bm25")],
      ["2.5.3", "6.1.0", "1.9.1", "0.2.2"])

# ---------------------------------------------------------------- the toy corpus (p2_measure.py S1)
raw = TOY_FILE.read_bytes()
toy = json.loads(raw)
DOCS, QUERIES = toy["docs"], toy["queries"]
GRADE = {(r["qid"], r["did"]): r["grade"] for r in toy["qrels"]}
dids, qids = sorted(DOCS), sorted(QUERIES)
REL = {q: sorted(d for d in dids if GRADE.get((q, d), 0) >= 1) for q in qids}   # binary rule: grade >= 1


# ---------------------------------------------------------------- the shared IR functions (p2_measure.py S2-S8)
def tokenize(text):
    """Lowercase; a token is a maximal run of a-z or 0-9; everything else separates tokens."""
    return re.findall(r"[a-z0-9]+", text.lower())


def build_index(docs_tokens):
    """term -> sorted list of the documents that contain it (the postings list)."""
    idx = {}
    for d in sorted(docs_tokens):
        for term in sorted(set(docs_tokens[d])):
            idx.setdefault(term, []).append(d)
    return idx


def search_or(query, idx):
    out = set()
    for t in set(tokenize(query)):
        out |= set(idx.get(t, []))
    return sorted(out)


def search_and(query, idx):
    terms = set(tokenize(query))
    if not terms:
        return []
    out = None
    for t in terms:
        p = set(idx.get(t, []))
        out = p if out is None else out & p
    return sorted(out)


def overlap_scores(query, idx):
    """Score = number of distinct query terms in the doc, accumulated from the postings."""
    acc = Counter()
    for t in set(tokenize(query)):
        for d in idx.get(t, []):
            acc[d] += 1
    return acc


def rank_by_overlap(query, idx):
    """Only docs with score >= 1 are returned (the candidates the index can find). Ties: doc id ascending."""
    return sorted(overlap_scores(query, idx).items(), key=lambda x: (-x[1], x[0]))


def precision(ret, rel):
    return 0.0 if not ret else len(set(ret) & set(rel)) / len(ret)


def recall(ret, rel):
    return float("nan") if not rel else len(set(ret) & set(rel)) / len(rel)


def first_rank(ret, rel):
    return next((i for i, d in enumerate(ret, 1) if d in rel), None)


toks = {d: tokenize(t) for d, t in DOCS.items()}
index = build_index(toks)
df = {t: len(p) for t, p in index.items()}
LEX_SCORED = {q: rank_by_overlap(QUERIES[q], index) for q in qids}
LEX = {q: [d for d, _ in LEX_SCORED[q]] for q in qids}

# ---------------------------------------------------------------- MiniLM (p2_measure.py S6)
MINILM = "sentence-transformers/all-MiniLM-L6-v2"
MODEL, MINILM_OK, COS, DENSE, DENSE_SCORED = None, False, None, {}, {}
warnings.filterwarnings("ignore", message="IProgress not found")   # tqdm's notebook-widget notice (no ipywidgets here)
try:
    import transformers
    transformers.utils.logging.disable_progress_bar()
    from sentence_transformers import SentenceTransformer
    MODEL = SentenceTransformer(MINILM, device="cpu")
    D_EMB = MODEL.encode([DOCS[d] for d in dids], normalize_embeddings=True)
    Q_EMB = MODEL.encode([QUERIES[q] for q in qids], normalize_embeddings=True)
    COS = Q_EMB @ D_EMB.T                             # one cosine per (query, document) pair: 5 x 10
    for i, q in enumerate(qids):
        order = sorted(range(len(dids)), key=lambda j: (-COS[i, j], dids[j]))
        DENSE_SCORED[q] = [(dids[j], round(float(COS[i, j]), 4)) for j in order]
        DENSE[q] = [dids[j] for j in order]
    MINILM_OK = True
except Exception as e:  # noqa: BLE001
    skip("every MiniLM number", f"MiniLM could not load offline: {type(e).__name__}: {str(e)[:160]}")

# ---------------------------------------------------------------- the climate PDF (same extraction as P1 and the acceptance suite)
pages = [p.get_text() for p in pymupdf.open(PDF)]
full = "\n".join(pages)                               # page.get_text() per page, joined with "\n"
windows = [full[i:i + 1000] for i in range(0, len(full), 800)]       # 1,000 characters, step 800 (overlap 200)
print(f"\nsetup done in {time.time() - T0:.1f} s: {len(DOCS)} toy docs, {len(QUERIES)} queries, "
      f"{len(windows)} PDF windows; MiniLM loaded: {MINILM_OK}")
''')

# =====================================================================================================================
md(r"""
## 1 · The need behind the question

**What this verifies** (lesson step 1, `#need`; fact S1). The pieces of a retrieval test, loaded from the toy file:
- a **collection** of 10 documents (in RAG, a document is a chunk), 5 **queries**, and a relevance **guideline** with grades 2 / 1 / 0;
- 13 listed labels; of the 10 × 5 = 50 (query, document) pairs, every pair that is not listed has grade 0;
- the file is the one the facts were measured on (sha256 and the lab's fingerprints).

A query is the words typed; the **information need** is what the person wants to know. `main cause of climate change` could come from a student who wants the cause named, or from someone who wants the mechanism explained: one query, two needs. Labels are written against the need, so the guideline says what "answers it" means.

No chart: the corpus is short enough to read.
""")
code(r'''
check("§1 toy corpus file sha256 (S1)", hashlib.sha256(raw).hexdigest(),
      "a2bee6be44e4a170423ecf0fb83d0a4a70017f5e31e774bd6653d4be43198b5c")
check("§1 docs / queries / listed qrels / pairs (S1)",
      [len(DOCS), len(QUERIES), len(toy["qrels"]), len(DOCS) * len(QUERIES)], [10, 5, 13, 50])
check("§1 lab fingerprints fp(DOCS), fp(QUERIES) (S1)", [_fp(DOCS), _fp(QUERIES)], ["1edaacca3ff916da", "acb0163a7a3906b8"])
check("§1 q1 is the book's question in keyword form", QUERIES["q1"], "main cause of climate change")

print("\n   the guideline (v1):")
for g in ("2", "1", "0", "binary_rule"):
    print(f"     {g:11s} {toy['guideline_v1'][g]}")
print("\n   the queries:")
for q in qids:
    print(f"     {q}  {QUERIES[q]}")
print("\n   the collection:")
for d in dids:
    print(f"     {d}  {DOCS[d]}")
''')

# =====================================================================================================================
md(r"""
## 2 · Two retrievers score it; similarity is not relevance

**What this verifies** (lesson step 2, `#similar`; facts S5, S6, S7). Two retrievers score q1 against every document:
- **word overlap through the index** (how many distinct query words the document contains): d02 **5**, d01 **3**, d08 **2**; no other document shares a word;
- **MiniLM cosine** (local embedding model, 384 numbers per text): d02 **0.8402**, d01 **0.6342**, …; d09, which the guideline marks relevant, sits at **rank 9** (0.2469).

Both put **d02** first. d02 repeats the question word for word and answers nothing (grade 0). A retriever computes **one score per (query, document) pair**: 5 queries × 10 documents = 50 scores. It never compares documents with each other, and no "similarity matrix" of all chunks is involved.

**The chart** puts every one of the 50 pairs on two axes: the MiniLM cosine (what the retriever sees) and the guideline grade (what a person judged). q1's ten pairs are blue. If similarity were relevance, the dots would climb from left to right. They do not: the highest cosine of q1 has grade 0.
""")
code(r'''
check("§2 overlap scores from the index, q1 (S5)", [list(p) for p in LEX_SCORED["q1"]], [["d02", 5], ["d01", 3], ["d08", 2]])
check("§2 overlap rankings, all queries (S5)", {q: [list(p) for p in LEX_SCORED[q]] for q in qids},
      {"q1": [["d02", 5], ["d01", 3], ["d08", 2]], "q2": [["d04", 2]], "q3": [],
       "q4": [["d06", 1], ["d09", 1]], "q5": [["d10", 3], ["d02", 1], ["d03", 1]]})

if MINILM_OK:
    for q in qids:
        print(f"   MiniLM {q}: " + ", ".join(f"{d} {s:.4f}" for d, s in DENSE_SCORED[q]))
    check("§2 MiniLM q1 ranking with cosines (S6)", [list(p) for p in DENSE_SCORED["q1"]],
          [["d02", 0.8402], ["d01", 0.6342], ["d04", 0.5139], ["d03", 0.4904], ["d10", 0.4318],
           ["d08", 0.3992], ["d05", 0.3927], ["d06", 0.2736], ["d09", 0.2469], ["d07", 0.1341]], tol=5e-5)
    check("§2 MiniLM q1: rank of the relevant d09 (S6)", DENSE["q1"].index("d09") + 1, 9)
    check("§2 MiniLM top 2 for q2, q3; top 1 for q4, q5 (S6)",
          [[list(p) for p in DENSE_SCORED["q2"][:2]], [list(p) for p in DENSE_SCORED["q3"][:2]],
           list(DENSE_SCORED["q4"][0]), list(DENSE_SCORED["q5"][0])],
          [[["d04", 0.8316], ["d05", 0.4038]], [["d07", 0.5804], ["d01", 0.3598]], ["d09", 0.6326], ["d10", 0.6342]],
          tol=5e-5)
    check("§2 embedding dim; every vector has length 1 (S6)",
          [D_EMB.shape[1], bool(np.allclose(np.linalg.norm(D_EMB, axis=1), 1, atol=1e-5))], [384, True])
    check("§2 one score per (query, document) pair: queries x docs = pairs (S1)",
          [COS.shape[0], COS.shape[1], COS.size], [5, 10, 50])
    check("§2 both retrievers put d02 first for q1, and d02's grade is 0 (S5, S6, S7)",
          [LEX["q1"][0], DENSE["q1"][0], GRADE[("q1", "d02")]], ["d02", "d02", 0])

    # chart: cosine vs grade, all 50 pairs (q1 in blue)
    fig = go.Figure()
    for is_q1 in (False, True):
        xs, ys, hov = [], [], []
        for i, q in enumerate(qids):
            if (q == "q1") != is_q1:
                continue
            for j, d in enumerate(dids):
                g = GRADE.get((q, d), 0)
                xs.append(round(g + (j - 4.5) * 0.035, 4))   # a small fixed sideways spread so dots do not overlap
                ys.append(round(float(COS[i, j]), 4))
                hov.append(f"{q} · {d} (MiniLM rank {DENSE[q].index(d) + 1})<br>{DOCS[d][:70]}")
        fig.add_scatter(x=xs, y=ys, mode="markers", name="q1 (main cause of climate change)" if is_q1 else "q2–q5",
                        marker=dict(size=11 if is_q1 else 8, color=BLUE if is_q1 else MUTED,
                                    opacity=1 if is_q1 else 0.55, line=dict(width=1, color=SURFACE)),
                        customdata=hov, hovertemplate="%{customdata}<br>cosine %{y:.4f}<extra></extra>")
    for d, txt, ay in (("d02", "d02: the echo of the question, grade 0", -40), ("d09", "d09: relevant, MiniLM rank 9", 40)):
        j = dids.index(d)
        fig.add_annotation(x=GRADE.get(("q1", d), 0) + (j - 4.5) * 0.035, y=float(COS[0, j]), text=txt,
                           showarrow=True, arrowhead=0, arrowcolor=INK2, ax=90, ay=ay, font=dict(size=12, color=INK))
    fig.update_layout(height=470, title="§2 · Similarity is not relevance: MiniLM cosine vs the guideline grade "
                                        "(measured, toy; 50 pairs)",
                      xaxis=dict(title="guideline grade (0 not relevant · 1 partial · 2 sufficient)",
                                 tickvals=[0, 1, 2], range=[-0.4, 2.4]),
                      yaxis=dict(title="MiniLM cosine (the retriever's score)"))
    fig.show()
else:
    skip("§2 MiniLM checks and chart", "MiniLM did not load")
''')

# =====================================================================================================================
md(r"""
## 3 · A person judges it: qrels

**What this verifies** (lesson step 3, `#judge`; fact S7). The labels, called **qrels** (query relevance judgments): one line per judged pair, `(query, document, grade)`, each with a written reason.
- Guideline v1: 2 = the document alone answers; 1 = part of the answer; 0 = does not help, even if it shares words or the topic. **Binary rule:** relevant = grade ≥ 1.
- q1: **d01 2, d03 1, d09 1**; everything else 0. d02 (the echo) and d08 (the keyword-stuffed footer) are listed with grade 0 and a reason.
- **8 relevant pairs of 50.** A pair that is not listed counts as grade 0.
- The lab's fingerprint over the 50 binary labels matches.

The order matters: write the guideline, judge, and only then look at what the retrievers returned. Change the guideline and its version number changes too.

**The chart** is the label table, query × document. Dark cells are relevant; `0` is a listed "not relevant" with a reason; `·` is a pair nobody listed (grade 0 by the rule).
""")
code(r'''
for q in qids:
    graded = {d: GRADE[(q, d)] for d in dids if GRADE.get((q, d), 0) >= 1}
    print(f"   {q}: relevant={REL[q]} grades={graded}")
check("§3 relevant docs per query (S7)", REL,
      {"q1": ["d01", "d03", "d09"], "q2": ["d04", "d05"], "q3": ["d07"], "q4": ["d09"], "q5": ["d10"]})
check("§3 q1 grades d01, d03, d09 (S7)", [GRADE[("q1", d)] for d in ("d01", "d03", "d09")], [2, 1, 1])
check("§3 relevant pairs of all pairs (S7)", [sum(len(v) for v in REL.values()), len(qids) * len(dids)], [8, 50])
check("§3 listed qrels lines (S1)", len(toy["qrels"]), 13)
check("§3 d02 and d08 are listed for q1 with grade 0 (S7)", [GRADE[("q1", "d02")], GRADE[("q1", "d08")]], [0, 0])
check("§3 every listed line has a written reason", all(len(r["why"].split()) >= 3 for r in toy["qrels"]), True)
binary_ref = sorted(_fp([q, d, int(GRADE.get((q, d), 0) >= 1)]) for q in qids for d in dids)
check("§3 lab fingerprint of the 50 binary labels (S7)", _fp(binary_ref), "c46167a0335a1135")
why = {(r["qid"], r["did"]): r["why"] for r in toy["qrels"]}
print(f"   q1 d02 reason: {why[('q1', 'd02')]}")
print(f"   q1 d08 reason: {why[('q1', 'd08')]}")

# chart: the qrels heat table
z, ann = [], []
for i, q in enumerate(qids):
    z.append([GRADE.get((q, d), 0) for d in dids])
    for j, d in enumerate(dids):
        listed = (q, d) in GRADE
        g = GRADE.get((q, d), 0)
        ann.append(dict(x=d, y=q, text=str(g) if listed else "·", showarrow=False,
                        font=dict(size=15, color=SURFACE if g == 2 else INK)))
hov = [[f"{q} · {d}: grade {GRADE.get((q, d), 0)}" + (f"<br>why: {why[(q, d)]}" if (q, d) in why else
        "<br>not listed: grade 0 by the rule") for d in dids] for q in qids]
fig = go.Figure(go.Heatmap(z=z, x=dids, y=qids, zmin=0, zmax=2, customdata=hov, xgap=3, ygap=3,
                           colorscale=[[0, "#f1f0ea"], [0.5, LIGHT], [1, BLUE]], showscale=False,
                           hovertemplate="%{customdata}<extra></extra>"))
fig.update_layout(annotations=ann, height=360, yaxis=dict(autorange="reversed", showline=False, showgrid=False),
                  xaxis=dict(side="top", showline=False, showgrid=False),
                  title="§3 · The qrels: grade per (query, document) (toy, guideline v1; '·' = not listed = 0)",
                  margin=dict(l=60, r=30, t=110, b=30))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 4 · Three meanings of "relevance"

**What this verifies** (lesson step 4, `#meanings`; facts S5, S6, S7). The same word means three different things, and q1's documents show all three:
- **score** (system relevance): what the retriever computed;
- **about the topic** (topical relevance): the document is on climate change;
- **helps answer** (situational relevance): our guideline's grade.

d02 has the top score from both retrievers and is on the topic, but its grade is 0. d08 shares two query words and is on the topic, grade 0. d01 has a lower score than d02 and is the only grade 2.

The book's "context relevance" (Ch22 p.4/19) is a fourth use: an evaluator's score for a retrieved chunk. An LLM that grades chunks at query time is a filter in the pipeline, not a label; an LLM that writes labels is a judge and must be checked against a person.

No chart: the table is the point.
""")
code(r'''
rows = []
for d, topic in (("d02", "yes (repeats the question)"), ("d08", "yes (topic words only)"), ("d01", "yes")):
    lex = dict(LEX_SCORED["q1"]).get(d, 0)
    row = {"doc": d, "text": DOCS[d], "overlap score": lex, "lexical rank": LEX["q1"].index(d) + 1}
    if MINILM_OK:
        row.update({"MiniLM cosine": dict(DENSE_SCORED["q1"])[d], "MiniLM rank": DENSE["q1"].index(d) + 1})
    row.update({"about the topic? (read)": topic, "grade (helps answer)": GRADE[("q1", d)]})
    rows.append(row)
MEAN = pd.DataFrame(rows)
display(MEAN.style.hide(axis="index").set_properties(**{"text-align": "left", "white-space": "normal"}))
check("§4 d02, d08, d01: overlap score (S5)", MEAN["overlap score"].tolist(), [5, 2, 3])
check("§4 d02, d08, d01: grade (S7)", MEAN["grade (helps answer)"].tolist(), [0, 0, 2])
if MINILM_OK:
    check("§4 d02, d08, d01: MiniLM cosine (S6)", MEAN["MiniLM cosine"].tolist(), [0.8402, 0.3992, 0.6342], tol=5e-5)
    check("§4 the highest score in both retrievers has grade 0 (S5-S7)",
          [GRADE.get(("q1", LEX["q1"][0]), 0), GRADE.get(("q1", DENSE["q1"][0]), 0)], [0, 0])
else:
    skip("§4 MiniLM columns", "MiniLM did not load")
''')

# =====================================================================================================================
md(r"""
## 5 · The inverted index

**What this verifies** (lesson step 5, `#index`; facts S2, S3, S11).
- **Tokenization first** (S2): lowercase, a token is a run of letters or digits; no stemming, no stopword list. `'Sea-level RISE, 2019!'` → `sea, level, rise, 2019`. The 10 documents hold **119** tokens; d08 has 11 tokens but only 7 distinct ones. These **index tokens** are words. They are not the LLM tokens of P1 (pieces of words, counted by a tokenizer such as `o200k_harmony`); the same word "token" names two different things. P3 §9 uses the same word tokens for BM25.
- **The incidence matrix** has one row per term and one column per document, with 1 where the term occurs. It is almost all zeros, so the index stores only the 1s: for each term, the sorted list of documents that contain it, its **postings**. The row sum is the **document frequency** df(t), and df(t) = the length of the postings list.
- **The toy index** (S3): **88** terms, **114** postings, **71** terms with df = 1; the highest df: `and` 6, `the` 5, `in` 4. Postings like `climate → d02, d08` and `rise → none` (d04 says "rising"). Every postings list equals a full scan of the documents.

**The chart** shows df for every toy term that appears in at least 2 documents (q1's words in orange). The other 71 terms appear in one document each.
""")
code(r'''
check("§5 tokenize('Sea-level RISE, 2019!') (S2)", tokenize("Sea-level RISE, 2019!"), ["sea", "level", "rise", "2019"])
check("§5 total tokens in the 10 docs (S2)", sum(len(v) for v in toks.values()), 119)
check("§5 d08: tokens, distinct tokens (S2)", [len(toks["d08"]), len(set(toks["d08"]))], [11, 7])
check("§5 query tokens q1..q5 (S2)", [tokenize(QUERIES[q]) for q in qids],
      [["main", "cause", "of", "climate", "change"], ["why", "do", "sea", "levels", "rise"], ["renewable", "energy"],
       ["where", "does", "methane", "come", "from"], ["is", "extreme", "heat", "becoming", "more", "common"]])
check("§5 lab fingerprint fp(tokenize per doc) (S11)", _fp([tokenize(DOCS[d]) for d in dids]), "043587a6e439e8a1")

# the incidence matrix for q1's words: rows = terms, columns = documents
Q1_TERMS = tokenize(QUERIES["q1"])
INC = pd.DataFrame([[int(t in set(toks[d])) for d in dids] for t in Q1_TERMS], index=Q1_TERMS, columns=dids)
INC["df (row sum)"] = INC.sum(axis=1)
INC["postings"] = [", ".join(index.get(t, [])) for t in Q1_TERMS]
print("   incidence matrix for q1's words (1 = the term occurs in the document):")
display(INC)
full_inc_rows = {t: sum(int(t in set(toks[d])) for d in dids) for t in index}
check("§5 df = row sum of the incidence matrix = postings length, every term", full_inc_rows == df, True)

check("§5 vocabulary / total postings / df = 1 terms (S3)",
      [len(index), sum(len(v) for v in index.values()), sum(1 for n in df.values() if n == 1)], [88, 114, 71])
top3 = sorted(df.items(), key=lambda x: (-x[1], x[0]))[:3]
check("§5 highest df (S3)", [list(x) for x in top3], [["and", 6], ["the", 5], ["in", 4]])
check("§5 postings: climate, change, of, the, carbon, heat, methane, rising (S3)",
      [index.get(t, []) for t in ("climate", "change", "of", "the", "carbon", "heat", "methane", "rising")],
      [["d02", "d08"], ["d02", "d08"], ["d01", "d02"], ["d01", "d02", "d03", "d05", "d06"], ["d01", "d06"],
       ["d03", "d10"], ["d09"], ["d04"]])
check("§5 postings: rise, renewable, energy are not in the index (S3)",
      [index.get(t, []) for t in ("rise", "renewable", "energy")], [[], [], []])
check("§5 every postings list equals a full scan of the docs (S3)",
      all(index[t] == sorted(d for d in toks if t in toks[d]) for t in index), True)
check("§5 lab fingerprint fp(index) (S11)", _fp(index), "a75adb6a2aa3ee3a")
DF2 = sorted(((t, n) for t, n in df.items() if n >= 2), key=lambda x: (-x[1], x[0]))
check("§5 all terms with df >= 2 (out_p2_measure S3)", [list(x) for x in DF2],
      [["and", 6], ["the", 5], ["in", 4], ["a", 2], ["are", 2], ["burning", 2], ["carbon", 2], ["cause", 2],
       ["change", 2], ["climate", 2], ["dioxide", 2], ["gas", 2], ["greenhouse", 2], ["heat", 2], ["main", 2],
       ["of", 2], ["water", 2]])

# chart: toy df bars
fig = go.Figure(go.Bar(x=[t for t, _ in DF2], y=[n for _, n in DF2],
                       marker=bar_style([ORANGE if t in Q1_TERMS else BLUE for t, _ in DF2]),
                       customdata=[", ".join(index[t]) for t, _ in DF2],
                       hovertemplate="%{x}: df %{y}<br>postings: %{customdata}<extra></extra>"))
fig.update_layout(height=420, showlegend=False, yaxis=dict(title="df = documents containing the term (of 10)", dtick=1),
                  title="§5 · Document frequency in the toy index: terms with df ≥ 2 (measured, toy; "
                        "q1's words in orange)<br><sup>71 more terms have df = 1</sup>")
fig.show()
''')

# =====================================================================================================================
md(r"""
## 6 · Boolean AND / OR and the postings read

**What this verifies** (lesson step 6, `#boolean`; facts S4, S11).
- **AND** = the documents in every query word's postings (intersection); **OR** = in any of them (union).
- The table (S4): q1 AND = **d02** (the echo), OR = **d01, d02, d08**; q2–q5 AND = nothing. AND is too strict, OR too loose.
- **Postings read** = the sum of the postings lengths of the query words: 10 / 2 / 0 / 2 / 5. The index reads only those lists, never the other documents.
- **q3 `renewable energy`:** neither word is in the index (0 postings), so nothing is returned. The relevant d07 talks about "solar panels and wind turbines": a **vocabulary mismatch**, never found by keyword search.
- **Linear merge** (the IIR algorithm): walk two sorted postings lists side by side, cost O(x + y); start with the shortest list (smallest df) so the running result stays small. It gives the same AND as the set intersection.

**The chart** shows how many documents AND and OR return per query, with the postings read in the hover.
""")
code(r'''
AND = {q: search_and(QUERIES[q], index) for q in qids}
OR = {q: search_or(QUERIES[q], index) for q in qids}
READ = {q: sum(df.get(t, 0) for t in set(tokenize(QUERIES[q]))) for q in qids}
for q in qids:
    missing = sorted(t for t in set(tokenize(QUERIES[q])) if t not in index)
    print(f"   {q} {QUERIES[q]!r:40s} AND={AND[q]} OR={OR[q]} postings read={READ[q]} not in index={missing}")
check("§6 AND per query (S4)", AND, {"q1": ["d02"], "q2": [], "q3": [], "q4": [], "q5": []})
check("§6 OR per query (S4)", OR, {"q1": ["d01", "d02", "d08"], "q2": ["d04"], "q3": [], "q4": ["d06", "d09"],
                                   "q5": ["d02", "d03", "d10"]})
check("§6 postings read per query (S4)", [READ[q] for q in qids], [10, 2, 0, 2, 5])
check("§6 q3: words not in the index; the relevant d07 is never a candidate (S3, S4, S7)",
      [sorted(t for t in tokenize(QUERIES["q3"]) if t not in index), "d07" in OR["q3"], REL["q3"]],
      [["energy", "renewable"], False, ["d07"]])
check("§6 edge cases: AND of an empty query; OR of an unknown word (S4)",
      [search_and("", index), search_or("photosynthesis", index)], [[], []])
check("§6 lab fingerprints fp(AND), fp(OR) (S11)", [_fp(AND), _fp(OR)], ["5375cb3802db14a1", "946fea0d80376ae5"])


def intersect_merge(p1, p2):
    """IIR's linear merge of two sorted postings lists: one pass, O(len(p1) + len(p2))."""
    i = j = 0
    out = []
    while i < len(p1) and j < len(p2):
        if p1[i] == p2[j]:
            out.append(p1[i]); i += 1; j += 1
        elif p1[i] < p2[j]:
            i += 1
        else:
            j += 1
    return out


def and_by_merge(query, idx):
    terms = sorted(set(tokenize(query)), key=lambda t: (len(idx.get(t, [])), t))   # smallest df first
    if not terms:
        return []
    out = idx.get(terms[0], [])
    for t in terms[1:]:
        out = intersect_merge(out, idx.get(t, []))
    return out


check("§6 AND by linear merge (smallest df first) = AND by set intersection, every query",
      all(and_by_merge(QUERIES[q], index) == AND[q] for q in qids), True)

# chart: AND / OR result sizes per query
labels = [f"{q}<br><sup>{QUERIES[q]}</sup>" for q in qids]
fig = go.Figure()
for name, res, colour in (("AND (every word)", AND, BLUE), ("OR (any word)", OR, ORANGE)):
    fig.add_bar(x=labels, y=[len(res[q]) for q in qids], name=name, marker=bar_style(colour),
                text=[", ".join(res[q]) or "none" for q in qids], textposition="outside",
                customdata=[READ[q] for q in qids],
                hovertemplate="%{x}<br>" + name + ": %{y} docs<br>postings read: %{customdata}<extra></extra>")
fig.update_layout(barmode="group", height=440, yaxis=dict(title="documents returned (of 10)", range=[0, 3.8], dtick=1),
                  title="§6 · Boolean retrieval on the toy index: AND is too strict, OR too loose (measured, toy)")
fig.show()
''')

# =====================================================================================================================
md(r"""
## 7 · Ranking from the index; candidates; ties

**What this verifies** (lesson step 7, `#rank`; facts S5, S10, S11, K2, K3).
- Ranking from the index adds up a score per document while reading the postings (here: +1 per matched query word). Only a document in **at least one postings list** can score above 0, so the **candidates** are exactly the OR set. Lexical candidates per query: q1 3, q2 1, q3 0, q4 2, q5 3 (K3).
- **Ties:** in q4, d06 and d09 both score 1 (each matches one word: d06 "from", d09 "methane"). The rule "doc id ascending" puts d06 first, so the relevant d09 is at **rank 2** (reciprocal rank 0.50). Reverse the rule and d09 is at **rank 1** (RR 1.00), with the same scores (K2). The tie rule is a hidden parameter; state it, or emit strictly decreasing scores.
- **A library without an index** (S10): `rank_bm25` 0.2.2, used by the repo's `fusion_retrieval.ipynb` cell 14, keeps one term-count dictionary per document and loops over **every** document in `get_scores`. It has no term → documents map; it gives the same non-zero documents for q4 (d06, d09) by scanning.

No chart: the lists are the point.
""")
code(r'''
for q in qids:
    print(f"   {q}: {LEX_SCORED[q]}")
check("§7 candidates = the OR set of the postings, every query", all(set(LEX[q]) == set(OR[q]) for q in qids), True)
check("§7 lexical candidates per query (K3)", {q: len(LEX[q]) for q in qids}, {"q1": 3, "q2": 1, "q3": 0, "q4": 2, "q5": 3})
check("§7 lab fingerprint fp(LEX) (S11)", _fp({q: LEX_SCORED[q] for q in qids}), "109e8ca0d7fce277")

# K2: the tie rule decides the rank (p2_kit_measure.py)
sc4 = overlap_scores(QUERIES["q4"], index)
asc = [d for d, _ in sorted(sc4.items(), key=lambda x: (-x[1], x[0]))]
desc = [d for d, _ in sorted(sc4.items(), key=lambda x: (-x[1], [-ord(c) for c in x[0]]))]
for name, run in (("doc id ascending (S5 rule)", asc), ("doc id descending", desc)):
    fr = first_rank(run, REL["q4"])
    print(f"   {name:28s} run={run} scores={[sc4[d] for d in run]} first relevant rank={fr} RR={1/fr:.2f}")
check("§7 q4 ties, doc id ascending: run, scores, first relevant rank, RR (K2)",
      [asc, [sc4[d] for d in asc], first_rank(asc, REL["q4"]), round(1 / first_rank(asc, REL["q4"]), 2)],
      [["d06", "d09"], [1, 1], 2, 0.50])
check("§7 q4 ties, doc id descending: run, first relevant rank, RR (K2)",
      [desc, first_rank(desc, REL["q4"]), round(1 / first_rank(desc, REL["q4"]), 2)], [["d09", "d06"], 1, 1.00])

# S10: rank_bm25 keeps no inverted index
from rank_bm25 import BM25Okapi
bm = BM25Okapi([toks[d] for d in dids])
check("§7 rank_bm25: version; doc_freqs is a list of one dict per document (S10)",
      [md.version("rank-bm25"), type(bm.doc_freqs).__name__, len(bm.doc_freqs), type(bm.doc_freqs[0]).__name__],
      ["0.2.2", "list", 10, "dict"])
check("§7 rank_bm25: any attribute mapping term -> documents (S10)",
      any(isinstance(v, dict) and v and isinstance(next(iter(v.values())), (list, set)) for v in vars(bm).values()), False)
check("§7 rank_bm25: get_scores loops over every document (S10)",
      "for doc in self.doc_freqs" in inspect.getsource(BM25Okapi.get_scores), True)
sc = bm.get_scores(tokenize(QUERIES["q4"]))
check("§7 rank_bm25 get_scores(q4): length, docs with a non-zero score (S10)",
      [len(sc), [dids[i] for i in np.nonzero(sc)[0]]], [10, ["d06", "d09"]])
''')

# =====================================================================================================================
md(r"""
## 8 · Cut at k: set precision and set recall

**What this verifies** (lesson step 8, `#cut`; facts S8, S11, K3). The retriever keeps the top **k**. Treat those k as a set:
- **precision@k** = relevant retrieved ÷ retrieved; **recall@k** = relevant retrieved ÷ all relevant (recall needs the number of relevant documents, which only the labels know).
- Lexical has only **3 candidates** for q1, so k = 6 adds nothing: recall 0.333 → 0.333. MiniLM ranks all 10 documents and reaches d03 at rank 4: q1 recall 0.333 → **0.667**, precision stays 0.333 (S8).
- Mean recall over the 5 queries: lexical 0.567 at k = 3 and k = 6; MiniLM 0.867 → 0.933.
- **Recall as k grows** (K3): lexical q1 is 0.0 at k = 1, then flat at 0.333 from k = 2 on; MiniLM q1 is 0.667 from k = 4 and 1.0 at k = 9.
- Accuracy (right on every pair, relevant or not) is useless here: almost every pair is "not relevant", so returning nothing already scores high.

**The chart** draws recall@k for k = 1…10: q1 on the left, the mean of the 5 queries on the right. The lexical line goes flat when it runs out of candidates.
""")
code(r'''
print("   system  query  k   retrieved                                    precision recall first_rel_rank")
for name, runs in (("lexical", LEX), ("MiniLM", DENSE)):
    for q in qids if runs else []:
        for k in (3, 6):
            ret = runs[q][:k]
            print(f"   {name:7s} {q:5s} {k:2d}  {str(ret):44s} {precision(ret, REL[q]):.3f}     "
                  f"{recall(ret, REL[q]):.3f}  {first_rank(ret, REL[q])}")
check("§8 lexical q1: candidates, recall@3, recall@6 (S8)",
      [len(LEX["q1"]), round(recall(LEX["q1"][:3], REL["q1"]), 4), round(recall(LEX["q1"][:6], REL["q1"]), 4)],
      [3, 0.3333, 0.3333])
k3, k6 = recall(LEX["q1"][:3], REL["q1"]), recall(LEX["q1"][:6], REL["q1"])
check("§8 lab fingerprint fp(CR08) (S11)", _fp([len(LEX["q1"]), round(k3, 4), round(k6, 4)]), "f0320f3ce2231c5f")
check("§8 lexical mean set recall k = 3 / 6; per query (S8)",
      [round(float(np.mean([recall(LEX[q][:k], REL[q]) for q in qids])), 3) for k in (3, 6)]
      + [[round(recall(LEX[q][:3], REL[q]), 3) for q in qids]],
      [0.567, 0.567, [0.333, 0.5, 0.0, 1.0, 1.0]])
check("§8 edge cases: precision of an empty run; first relevant rank of ['d02'] (S8)",
      [precision([], REL["q1"]), first_rank(["d02"], REL["q1"])], [0.0, None])

KS = list(range(1, 11))
CURVE = {}
for name, runs in (("lexical", LEX), ("MiniLM", DENSE)):
    if not runs:
        continue
    CURVE[name] = dict(q1=[round(recall(runs["q1"][:k], REL["q1"]), 3) for k in KS],
                       mean=[round(float(np.mean([recall(runs[q][:k], REL[q]) for q in qids])), 3) for k in KS])
check("§8 lexical recall@1..10: q1 (K3)", CURVE["lexical"]["q1"], [0.0] + [0.333] * 9)
check("§8 lexical recall@1..10: mean of 5 queries (K3)", CURVE["lexical"]["mean"], [0.3] + [0.567] * 9)
if MINILM_OK:
    check("§8 MiniLM q1 at k = 3 -> 6: precision, recall (S8)",
          [round(precision(DENSE["q1"][:k], REL["q1"]), 3) for k in (3, 6)]
          + [round(recall(DENSE["q1"][:k], REL["q1"]), 3) for k in (3, 6)], [0.333, 0.333, 0.333, 0.667])
    check("§8 MiniLM q1: d03 enters at rank 4 (S8)", DENSE["q1"].index("d03") + 1, 4)
    check("§8 MiniLM mean set recall k = 3 / 6 (S8)",
          [round(float(np.mean([recall(DENSE[q][:k], REL[q]) for q in qids])), 3) for k in (3, 6)], [0.867, 0.933])
    check("§8 MiniLM recall@1..10: q1 (K3)", CURVE["MiniLM"]["q1"], [0.0, 0.333, 0.333] + [0.667] * 5 + [1.0, 1.0])
    check("§8 MiniLM recall@1..10: mean of 5 queries (K3)", CURVE["MiniLM"]["mean"],
          [0.7, 0.867, 0.867] + [0.933] * 5 + [1.0, 1.0])
else:
    skip("§8 MiniLM checks", "MiniLM did not load")

# chart: recall@k curves
fig = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.06,
                    subplot_titles=("q1 (3 relevant documents)", "mean of the 5 queries"))
for col, part in ((1, "q1"), (2, "mean")):
    for name, colour in (("lexical (word overlap)", BLUE), ("MiniLM", ORANGE)):
        key = name.split()[0]
        if key not in CURVE:
            continue
        fig.add_scatter(x=KS, y=CURVE[key][part], mode="lines+markers", name=name, showlegend=col == 1,
                        line=dict(color=colour, width=2.5, shape="hv"), marker=dict(size=8, color=colour),
                        hovertemplate=f"{name}<br>k = %{{x}}: recall %{{y:.3f}}<extra></extra>", row=1, col=col)
fig.update_xaxes(title_text="k (documents kept)", dtick=1)
fig.update_yaxes(title_text="set recall@k", range=[-0.03, 1.05], row=1, col=1)
fig.update_layout(height=440, title="§8 · Recall as k grows: the lexical line stops when it runs out of candidates "
                                    "(measured, toy)")
fig.show()
''')

# =====================================================================================================================
md(r"""
## 9 · Set quality vs ranking quality

**What this verifies** (lesson step 9, `#setrank`; facts S8, S11). Three hand-made runs of 3 documents for q1 (relevant: d01, d03, d09):
- **A** = d02, d01, d08: precision 0.333, recall 0.333, first relevant at rank **2**;
- **B** = d01, d08, d02: the **same set** as A, so the same precision and recall, but the first relevant document is at rank **1**;
- **C** = d01, d03, d09: the same first rank as B, but precision and recall 1.0.

Set measures cannot see the order; the first relevant rank cannot see the rest of the set. You need both questions. **Reciprocal rank** RR = 1 ÷ first relevant rank (A 0.5, B and C 1.0). P6 continues with MRR, nDCG and the RAG metrics.

**The chart** puts the set measures (left) next to the first relevant rank (right) for the three runs.
""")
code(r'''
RUNS = {"A": ["d02", "d01", "d08"], "B": ["d01", "d08", "d02"], "C": ["d01", "d03", "d09"]}
TOYRUNS = {n: [round(precision(r, REL["q1"]), 4), round(recall(r, REL["q1"]), 4), first_rank(r, REL["q1"])]
           for n, r in RUNS.items()}
for n, r in RUNS.items():
    print(f"   run {n} {r}: precision={TOYRUNS[n][0]} recall={TOYRUNS[n][1]} first relevant rank={TOYRUNS[n][2]}")
check("§9 run A: precision, recall, first relevant rank (S8)", TOYRUNS["A"], [0.3333, 0.3333, 2])
check("§9 run B: precision, recall, first relevant rank (S8)", TOYRUNS["B"], [0.3333, 0.3333, 1])
check("§9 run C: precision, recall, first relevant rank (S8)", TOYRUNS["C"], [1.0, 1.0, 1])
check("§9 A and B: same set, different first rank", [set(RUNS["A"]) == set(RUNS["B"]), TOYRUNS["A"][2] != TOYRUNS["B"][2]],
      [True, True])
check("§9 reciprocal rank RR = 1 / first relevant rank: A, B, C", [round(1 / TOYRUNS[n][2], 2) for n in "ABC"],
      [0.50, 1.00, 1.00])
check("§9 lab fingerprint fp(TOYRUNS) (S11)", _fp(TOYRUNS), "9d72704a91f3c210")

# chart: set vs rank
names = [f"run {n}<br><sup>{', '.join(RUNS[n])}</sup>" for n in RUNS]
fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.12,
                    subplot_titles=("set quality: what is in the top 3", "ranking quality: where the first hit sits"))
fig.add_bar(x=names, y=[TOYRUNS[n][0] for n in RUNS], name="precision@3", marker=bar_style(BLUE),
            hovertemplate="%{x}<br>precision %{y:.3f}<extra></extra>", row=1, col=1)
fig.add_bar(x=names, y=[TOYRUNS[n][1] for n in RUNS], name="recall@3", marker=bar_style(AQUA),
            hovertemplate="%{x}<br>recall %{y:.3f}<extra></extra>", row=1, col=1)
fig.add_bar(x=names, y=[TOYRUNS[n][2] for n in RUNS], name="first relevant rank (lower is better)",
            marker=bar_style(ORANGE), text=[TOYRUNS[n][2] for n in RUNS], textposition="outside",
            hovertemplate="%{x}<br>first relevant at rank %{y}<extra></extra>", row=1, col=2)
fig.update_yaxes(title_text="value", range=[0, 1.1], row=1, col=1)
fig.update_yaxes(title_text="rank", range=[0, 3], dtick=1, row=1, col=2)
fig.update_layout(barmode="group", height=440,
                  title="§9 · Same set, different ranking; same first rank, different set (toy runs for q1)")
fig.show()
''')

# =====================================================================================================================
md(r"""
## 10 · Labels are incomplete and noisy

**What this verifies** (lesson step 10, `#holes`; facts K4, K6; BEIR external).

**The pool demo (toy, K4).** Real test collections cannot judge every pair, so they judge a **pool**: the top results of some systems. Every document outside the pool is **unjudged**, and the rule is **unjudged = not relevant**. Here the pool is the lexical top 3 only (one retriever), and both retrievers are scored at k = 4:
- pooled relevant: q1 d01 · q2 d04 · q3 none · q4 d09 · q5 d10 (full labels: q1 d01, d03, d09 · q2 d04, d05 · q3 d07 · q4 d09 · q5 d10);
- **lexical**: mean P@4 0.433 with full labels and 0.433 with pooled labels: it built the pool, so nothing changes;
- **MiniLM**: only 0.350 of its top-4 slots are judged (Judged@4); mean P@4 drops from **0.350 to 0.200**. For q1 its top 4 is d02, d01, d04, d03: 2 of 4 judged, and d03, which is relevant, counts as a miss (P@4 0.500 → 0.250);
- mean recall rises to **1.000 for both**: recall divides by the relevant documents that are known, and the pool only knows the ones the lexical retriever found. Pooled recall is averaged over the 4 queries with a pooled relevant document (q3 has none).

**Judged@k** = judged documents in the top k ÷ k; **Hole@k** = 1 − Judged@k. Report it next to every retrieval number.

**The same effect, measured at scale (external).** BEIR (Thakur et al. 2021, Table 4, TREC-COVID): the share of each system's top 10 that the official judges never saw, Hole@10, was 6.4% for BM25 and 2.8% for docT5query (lexical) but 30.6% for DPR, 14.4% for ANCE and 31.8% for TAS-B (dense). After the authors judged the holes, ANCE's nDCG@10 rose from 0.654 to 0.735 and BM25's from 0.656 to 0.668: ANCE moved from just below BM25 to above it.

**Two judges disagree (K6).** Cohen's κ = (P(A) − P(E)) ÷ (1 − P(E)), agreement corrected for chance. On IIR's Table 8.2 (two judges, 400 documents: 300 both yes, 20 and 10 split, 70 both no): P(A) 0.9250, P(E) 0.6653, **κ 0.7759** with pooled marginals (IIR prints 0.776); 0.7761 with scikit-learn's separate marginals. Above 0.8 is good agreement, 0.67–0.8 fair: two careful judges agree only fairly well. Swapping judges changes absolute scores but rarely the order of systems.

**The charts.** First, P@4 and recall with full vs pooled labels for each retriever (toy). Second, BEIR's Hole@10 and the nDCG@10 change after judging the holes (external, not re-measured).
""")
code(r'''
K, POOL_K = 4, 3
pool = {q: set(LEX[q][:POOL_K]) for q in qids}
REL_POOL = {q: sorted(d for d in REL[q] if d in pool[q]) for q in qids}
print("   pool (judged docs) per query:", {q: sorted(pool[q]) for q in qids})
check("§10 relevant under pooled labels (K4)", REL_POOL, {"q1": ["d01"], "q2": ["d04"], "q3": [], "q4": ["d09"], "q5": ["d10"]})

POOLRES = {}
for name, runs in (("lexical", LEX), ("MiniLM", DENSE)):
    if not runs:
        continue
    rows = []
    for q in qids:
        top = runs[q][:K]
        rows.append(dict(q=q, top=top, judged=sum(1 for d in top if d in pool[q]),
                         p_full=precision(top, REL[q]), p_pool=precision(top, REL_POOL[q]),
                         r_full=recall(top, REL[q]), r_pool=recall(top, REL_POOL[q])))
        r = rows[-1]
        print(f"   {name:8s} {q} top{K}={top} judged@{K}={r['judged']}/{len(top)} P@{K} full={r['p_full']:.3f} "
              f"pooled={r['p_pool']:.3f} recall full={r['r_full']:.3f} pooled={r['r_pool']:.3f}")
    POOLRES[name] = dict(rows=rows, judged=float(np.mean([r["judged"] / K for r in rows])),
                         p_full=float(np.mean([r["p_full"] for r in rows])),
                         p_pool=float(np.mean([r["p_pool"] for r in rows])),
                         r_full=float(np.nanmean([r["r_full"] for r in rows])),
                         r_pool=float(np.nanmean([r["r_pool"] for r in rows])),
                         n_pool=sum(1 for r in rows if not math.isnan(r["r_pool"])))
L = POOLRES["lexical"]
check("§10 lexical: mean Judged@4, P@4 full, P@4 pooled, recall full, recall pooled (K4)",
      [round(L[k], 3) for k in ("judged", "p_full", "p_pool", "r_full", "r_pool")], [0.450, 0.433, 0.433, 0.567, 1.000])
check("§10 pooled recall is averaged over the queries with a pooled relevant doc (K4)", L["n_pool"], 4)
if MINILM_OK:
    M = POOLRES["MiniLM"]
    check("§10 MiniLM: mean Judged@4, P@4 full, P@4 pooled, recall full, recall pooled (K4)",
          [round(M[k], 3) for k in ("judged", "p_full", "p_pool", "r_full", "r_pool")], [0.350, 0.350, 0.200, 0.933, 1.000])
    m1 = M["rows"][0]
    check("§10 MiniLM q1: top 4, judged of 4, P@4 full, P@4 pooled (K4)",
          [m1["top"], m1["judged"], round(m1["p_full"], 3), round(m1["p_pool"], 3)],
          [["d02", "d01", "d04", "d03"], 2, 0.500, 0.250])
    check("§10 MiniLM q1: d03 is relevant but unjudged (outside the lexical pool)",
          ["d03" in REL["q1"], "d03" in pool["q1"]], [True, False])
else:
    skip("§10 MiniLM pool demo", "MiniLM did not load")

# K6: kappa on IIR Table 8.2
yy, yn, ny, nn = 300, 20, 10, 70                      # external counts (IIR §8.5, Table 8.2)
n = yy + yn + ny + nn
pa = (yy + nn) / n
p_rel = ((yy + yn) + (yy + ny)) / (2 * n)
pe = p_rel ** 2 + (1 - p_rel) ** 2
kappa = (pa - pe) / (1 - pe)
check("§10 κ on IIR Table 8.2: P(A), P(relevant) pooled, P(E), κ (K6)",
      [round(pa, 4), round(p_rel, 4), round(pe, 4), round(kappa, 4)], [0.9250, 0.7875, 0.6653, 0.7759])
from sklearn.metrics import cohen_kappa_score
j1 = [1] * yy + [1] * yn + [0] * ny + [0] * nn
j2 = [1] * yy + [0] * yn + [1] * ny + [0] * nn
check("§10 Cohen's κ with separate marginals, scikit-learn (K6)", round(cohen_kappa_score(j1, j2), 4), 0.7761)

# chart 1: the pool demo
fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.1,
                    subplot_titles=("mean P@4", "mean recall@4"))
names = list(POOLRES)
for col, (kf, kp) in ((1, ("p_full", "p_pool")), (2, ("r_full", "r_pool"))):
    for key, label, colour in ((kf, "full labels (all 50 pairs judged)", BLUE),
                               (kp, "pooled labels (lexical top 3 judged only)", ORANGE)):
        fig.add_bar(x=names, y=[round(POOLRES[m][key], 3) for m in names], name=label, showlegend=col == 1,
                    marker=bar_style(colour), text=[f"{POOLRES[m][key]:.3f}" for m in names], textposition="outside",
                    customdata=[round(POOLRES[m]["judged"], 3) for m in names],
                    hovertemplate="%{x}: %{y:.3f}<br>mean Judged@4 %{customdata:.3f}<extra>" + label + "</extra>",
                    row=1, col=col)
fig.update_yaxes(range=[0, 1.15])
fig.update_layout(barmode="group", height=440,
                  title="§10 · Unjudged = not relevant: a one-retriever pool hurts the other retriever (measured, toy)")
fig.show()

# chart 2: BEIR Table 4 (external, not re-measured)
BEIR_HOLE = {"BM25": 6.4, "docT5query": 2.8, "DPR": 30.6, "ANCE": 14.4, "TAS-B": 31.8}     # Hole@10 %, TREC-COVID
BEIR_NDCG = {"BM25": (0.656, 0.668), "ANCE": (0.654, 0.735)}                              # nDCG@10 before -> after
LEXICAL_FAMILY = {"BM25", "docT5query"}
fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.12, column_widths=[0.58, 0.42],
                    subplot_titles=("Hole@10: top-10 results nobody judged (%)", "nDCG@10 before / after judging the holes"))
fig.add_bar(x=list(BEIR_HOLE), y=list(BEIR_HOLE.values()), showlegend=False,
            marker=bar_style([BLUE if s in LEXICAL_FAMILY else ORANGE for s in BEIR_HOLE]),
            text=[f"{v}%" for v in BEIR_HOLE.values()], textposition="outside",
            customdata=["lexical / sparse" if s in LEXICAL_FAMILY else "dense" for s in BEIR_HOLE],
            hovertemplate="%{x} (%{customdata}): Hole@10 %{y}%<extra>external</extra>", row=1, col=1)
for k, (label, colour) in enumerate((("official judgments", MUTED), ("after judging the holes", AQUA))):
    fig.add_bar(x=list(BEIR_NDCG), y=[v[k] for v in BEIR_NDCG.values()], name=label, marker=bar_style(colour),
                text=[f"{v[k]:.3f}" for v in BEIR_NDCG.values()], textposition="outside",
                hovertemplate="%{x}: nDCG@10 %{y:.3f}<extra>" + label + "</extra>", row=1, col=2)
fig.update_yaxes(title_text="Hole@10 (%)", range=[0, 38], row=1, col=1)
fig.update_yaxes(title_text="nDCG@10", range=[0.6, 0.76], row=1, col=2)
fig.update_layout(barmode="group", height=460,
                  title="§10 · BEIR on TREC-COVID: dense retrievers had the most unjudged hits "
                        "(external, Thakur et al. 2021, Table 4; not re-measured)<br>"
                        "<sup>blue = lexical / sparse, orange = dense</sup>")
fig.show()
''')

# =====================================================================================================================
md(r"""
## 11 · The real PDF

**What this verifies** (lesson step 11, `#pdf`; facts S9, S11, K5). The same index over the climate PDF, cut into 91 windows of 1,000 characters (overlap 200):
- 72,593 characters, 91 windows (the last has 593 characters); **1,868** terms, **8,107** postings, 11,807 tokens, 745 terms with df = 1;
- common words are in almost every window: `and` 91 of 91, `the` 80, `climate` 77, `of` 74, `change` 59; rare ones are few: `methane` 5, `rise` 4;
- `main cause of climate change`: OR returns **90** of 91 windows, AND returns **0**, and the index reads **213** postings. As a filter, the index is useless for this query; ranking (P3) has to do the work. `methane emissions`: OR 34, AND 5, 39 read; `renewable energy`: OR 42, AND 30, 72 read. Each OR equals a full scan.

**Labels from evidence spans (K5).** The project's draft seed questions (06 §6.7, `llm-draft`, illustration only) mark their evidence as character spans on PDF pages. A window is relevant when it overlaps a span in at least one non-whitespace character (`any_overlap`). So the same span becomes different chunk labels under a different chunker. D-002's one span → windows **25, 26** (two overlapping windows); D-004's two alternatives (p.8 and p.23) → **22, 63**; D-005's two evidence groups → **2, 3, 4** (window 3 serves both). D-009 and D-010 are unanswerable: no relevant window.

**The charts.** df of the measured terms (log scale; q1's words in orange), then the span → window table.
""")
code(r'''
check("§11 PDF sha256 (S9)", hashlib.sha256(PDF.read_bytes()).hexdigest(),
      "1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669")
check("§11 characters, windows, last window characters (S9)", [len(full), len(windows), len(windows[-1])], [72593, 91, 593])
wids = [f"w{i:02d}" for i in range(len(windows))]
wtoks = dict(zip(wids, (tokenize(w) for w in windows)))
pindex = build_index(wtoks)
pdf_df = {t: len(p) for t, p in pindex.items()}
check("§11 vocabulary, postings, tokens, df = 1 terms (S9)",
      [len(pindex), sum(len(v) for v in pindex.values()), sum(len(v) for v in wtoks.values()),
       sum(1 for v in pdf_df.values() if v == 1)], [1868, 8107, 11807, 745])
PDF_TERMS = ["and", "to", "for", "the", "climate", "in", "of", "change", "energy", "carbon", "renewable",
             "greenhouse", "rising", "methane", "rise"]
check("§11 df (windows of 91) for 15 terms (S9)", [pdf_df.get(t, 0) for t in PDF_TERMS],
      [91, 87, 80, 80, 77, 76, 74, 59, 42, 30, 30, 15, 6, 5, 4])
check("§11 10 highest-df terms (out_p2_measure S9)",
      [list(x) for x in sorted(pdf_df.items(), key=lambda x: (-x[1], x[0]))[:10]],
      [["and", 91], ["to", 87], ["for", 80], ["the", 80], ["climate", 77], ["in", 76], ["of", 74], ["are", 67],
       ["can", 65], ["is", 65]])
PQ = {}
for qtext in ("methane emissions", "main cause of climate change", "renewable energy"):
    terms = sorted(set(tokenize(qtext)))
    o, a = search_or(qtext, pindex), search_and(qtext, pindex)
    scan = sorted(w for w in wids if set(terms) & set(wtoks[w]))
    PQ[qtext] = [len(o), len(a), sum(pdf_df.get(t, 0) for t in terms), scan == o]
    print(f"   {qtext!r:32s} OR={len(o)} AND={len(a)} postings read={PQ[qtext][2]} OR equals a full scan: {scan == o}")
check("§11 'methane emissions': OR, AND, postings read, OR = scan (S9)", PQ["methane emissions"], [34, 5, 39, True])
check("§11 'main cause of climate change': OR, AND, postings read, OR = scan (S9)",
      PQ["main cause of climate change"], [90, 0, 213, True])
check("§11 'renewable energy': OR, AND, postings read, OR = scan (S9)", PQ["renewable energy"], [42, 30, 72, True])
PDFFACTS = [len(windows), len(pindex), pdf_df["the"], pdf_df.get("methane", 0), len(search_or("methane emissions", pindex))]
check("§11 lab fingerprint fp(PDFFACTS) (S11)", _fp(PDFFACTS), "552eae7370ad8bbe")

# chart 1: PDF df, log scale
order = sorted(PDF_TERMS, key=lambda t: (-pdf_df[t], t))
fig = go.Figure(go.Bar(x=order, y=[pdf_df[t] for t in order],
                       marker=bar_style([ORANGE if t in tokenize(QUERIES["q1"]) else BLUE for t in order]),
                       text=[pdf_df[t] for t in order], textposition="outside",
                       hovertemplate="%{x}: in %{y} of 91 windows<extra></extra>"))
fig.update_layout(height=440, showlegend=False,
                  yaxis=dict(type="log", title="df = windows containing the term (of 91, log scale)", range=[0.4, 2.15]),
                  title="§11 · Document frequency in the climate PDF index (measured, 91 windows; "
                        "q1's words in orange)")
fig.show()

# K5: evidence spans -> relevant windows (p2_kit_measure.py)
starts = [sum(len(x) + 1 for x in pages[:i]) for i in range(len(pages))]
wins = [(i, min(i + 1000, len(full))) for i in range(0, len(full), 800)]
plan = (WS / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
block = plan.split("Machine-readable form (offsets: PyMuPDF 1.26.7")[1].split("```jsonl")[1].split("```")[0]
seeds = [json.loads(line) for line in block.strip().splitlines()]


def hits(a, b):
    """0-based windows that share at least one non-whitespace character with the span [a, b)."""
    return [w for w, (x, y) in enumerate(wins) if any(not ch.isspace() for ch in full[max(x, a):min(y, b)])]


SPAN = {}
quotes_ok = True
for s in seeds:
    per_alt, allw = [], set()
    for g in s["evidence_groups"]:
        for alt in g["alternatives"]:
            ws = set()
            for seg in alt["segments"]:
                a = starts[seg["page"] - 1] + seg["char_start"]
                b = starts[seg["page"] - 1] + seg["char_end"]
                quotes_ok &= full[a:b].split()[:3] == alt["quote"].split()[:3]
                ws |= set(hits(a, b))
            per_alt.append(f"{g['group_id']}/{alt['alt_id']} p.{alt['segments'][0]['page']} → {sorted(ws)}")
            allw |= ws
    SPAN[s["qid"]] = dict(category=s["category"], windows=sorted(allw), alts=per_alt)
check("§11 06 §6.7 draft seeds; every evidence span starts with its quoted words (K5)", [len(seeds), quotes_ok], [10, True])
check("§11 span-derived relevant windows per seed (K5)", {q: v["windows"] for q, v in SPAN.items()},
      {"D-001": [7], "D-002": [25, 26], "D-003": [63, 64], "D-004": [22, 63], "D-005": [2, 3, 4], "D-006": [20],
       "D-007": [25, 26, 79], "D-008": [64], "D-009": [], "D-010": []})
check("§11 D-004 alternatives; D-005 evidence groups (K5)", [SPAN["D-004"]["alts"], SPAN["D-005"]["alts"]],
      [["g1/g1a p.8 → [22]", "g1/g1b p.23 → [63]"], ["g1/g1a p.2 → [2, 3]", "g2/g2a p.2 → [3, 4]"]])

# chart 2: the span -> window table
fig = go.Figure(go.Table(
    columnwidth=[60, 150, 120, 300],
    header=dict(values=["seed", "category", "relevant windows (0-based)", "per evidence group / alternative"],
                fill_color=GRID, font=dict(color=INK, size=12), align="left"),
    cells=dict(values=[list(SPAN), [v["category"] for v in SPAN.values()],
                       [", ".join(map(str, v["windows"])) or "none (unanswerable)" for v in SPAN.values()],
                       ["; ".join(v["alts"]) or "-" for v in SPAN.values()]],
               fill_color=[[LIGHT if q in ("D-002", "D-004", "D-005") else SURFACE for q in SPAN]] * 4,
               line_color=GRID, align="left", height=28, font=dict(color=INK2, size=12))))
fig.update_layout(title="§11 · Evidence spans → relevant windows (measured; 06 §6.7 draft seeds, llm-draft, "
                        "illustration only)<br><sup>91 windows of 1,000 characters, step 800; any_overlap on "
                        "non-whitespace characters; highlighted rows are the lesson's examples</sup>",
                  height=440, margin=dict(l=10, r=10, t=90, b=10))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 12 · For your project

**What this verifies** (lesson step 12, `#project`; facts S1, S7, K4, K5). A **test collection** = documents + information needs + qrels (the Cranfield design). IIR suggests about 50 needs; tune on a development set and report on a separate test set. For the project:
- the qrels are written in the standard TREC format, one line per judged pair: `query  0  document  grade` (the 0 is an unused "iteration" column). Unlisted pairs count as 0. Written out and read back, the toy's 13 lines give the same 8 relevant pairs;
- 06's `evidence_groups` are qrels made of **spans**, not chunk ids; chunk labels are derived per chunker (step 11), so they never go stale when the chunking changes;
- **pool from both retrievers** when you label: the one-retriever pool of step 10 never showed d03 to the judge, although MiniLM ranks it 4th for q1;
- report **Judged@k** next to every retrieval metric;
- qrels measure **retrieval** only. A reference answer is not a relevance label, and answer quality is measured separately.

No chart: the file format is the point.
""")
code(r'''
# toy qrels -> TREC lines -> read back
TREC = "\n".join(f"{r['qid']} 0 {r['did']} {r['grade']}" for r in toy["qrels"])
print("   toy qrels in TREC format (first 6 lines):")
print("\n".join("     " + line for line in TREC.splitlines()[:6]))
back = {}
for line in TREC.splitlines():
    q, _, d, g = line.split()
    back[(q, d)] = int(g)
REL_BACK = {q: sorted(d for d in dids if back.get((q, d), 0) >= 1) for q in qids}
check("§12 TREC qrels lines written (S1)", len(TREC.splitlines()), 13)
check("§12 read back: the same relevant set; relevant pairs (S7)",
      [REL_BACK == REL, sum(len(v) for v in REL_BACK.values())], [True, 8])

# span labels -> chunk qrels for this chunker (K5)
SPAN_TREC = [f"{q} 0 w{w:02d} 1" for q in ("D-002", "D-004", "D-005") for w in SPAN[q]["windows"]]
print("\n   span-derived chunk qrels for the 91-window chunker (D-002, D-004, D-005):")
print("\n".join("     " + line for line in SPAN_TREC))
check("§12 span-derived chunk qrels lines (K5)", SPAN_TREC,
      ["D-002 0 w25 1", "D-002 0 w26 1", "D-004 0 w22 1", "D-004 0 w63 1", "D-005 0 w02 1", "D-005 0 w03 1", "D-005 0 w04 1"])

# why the pool must include both retrievers (K4)
if MINILM_OK:
    check("§12 q1: d03 is in MiniLM's top 4 but not in the lexical pool (K4)",
          ["d03" in DENSE["q1"][:4], "d03" in LEX["q1"][:3]], [True, False])
else:
    skip("§12 pool check", "MiniLM did not load")
''')

# =====================================================================================================================
md(r"""
## Result

The cell below counts the checks. Every `FAIL` names the value that disagreed; every `SKIPPED` says why it could not run.
""")
code(r'''
n_pass = sum(ok for _, ok in CHECKS)
n_fail = len(CHECKS) - n_pass
print(f"{n_pass} checks passed / {n_fail} failed")
for name, ok in CHECKS:
    if not ok:
        print("   FAILED:", name)
for name, why_ in SKIPPED:
    print("   SKIPPED:", name, "-", why_)
print(f"   ({len(SKIPPED)} skipped; notebook time {time.time() - T0:.1f} s)")
''')

nb = nbf.v4.new_notebook()
nb.cells = CELLS
nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3 (ipykernel)", "language": "python"},
               "language_info": {"name": "python"}}
OUT.parent.mkdir(parents=True, exist_ok=True)
nbf.validate(nb)
nbf.write(nb, str(OUT))
print(f"wrote {OUT.relative_to(WS)}: {len(CELLS)} cells ({sum(c.cell_type == 'code' for c in CELLS)} code)")
