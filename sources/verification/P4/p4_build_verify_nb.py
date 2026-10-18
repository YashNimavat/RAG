"""Build study/notebooks/P4_embeddings_verify.ipynb: the "verify it yourself" notebook for P4 (embeddings and similarity).

The notebook rebuilds every measured number and chart of the P4 lesson (study/lessons/P4_embeddings.html) from code,
one section per lesson step (1-12), and compares each value with the lesson's value in a `check(...)` line. Expected
values are copied from sources/verification/P4/P4_FACTS.md: section 1 (S1-S10, p4_measure.py, the old 91 windows,
used only where chunking does not matter) and section 1b (K1-K13, p4_kit_measure.py, v0's 97 chunks). The code paths
are those of the two scripts, so the numbers come out identical.

The step 11 Cohere comparison reads a recorded replay pack only (the planned LLMOps notebook makes it). Until that pack
exists, its checks are SKIPPED with a reason; nothing is called and nothing is guessed.

No Groq, Cohere or Claude call, no .env read, no network (the three models load from the local Hugging Face cache).
LangChain and FAISS are not imported: their score conventions are applied as formulas to MiniLM vectors.

Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P4/p4_build_verify_nb.py
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P4/p4_verify_nb_run.py \
        > sources/verification/P4/out_p4_verify_nb_run.txt                              # executes it, saves outputs
"""
from pathlib import Path
from textwrap import dedent

import nbformat as nbf

WS = Path(__file__).resolve().parents[3]                      # rag_learning/
OUT = WS / "study" / "notebooks" / "P4_embeddings_verify.ipynb"

CELLS = []


def md(s):
    CELLS.append(nbf.v4.new_markdown_cell(dedent(s).strip()))


def code(s):
    CELLS.append(nbf.v4.new_code_cell(dedent(s).strip()))


# =====================================================================================================================
md(r"""
# P4 · Verify it yourself: embeddings and similarity

**What this is:** a notebook that rebuilds every measured number and chart of the P4 lesson from real code, so you can see each one being made and change the inputs.
**What this is not:** the lab (`labs/P4_embeddings_lab.ipynb`, where you write the functions yourself) or the quiz. It makes **no API call**: no Groq, no Cohere, no Claude. Where the lesson uses an outside fact (a paper, Cohere's documentation), this notebook says so and does not pretend to re-measure it.

**How to use it.** Run all cells from the top (VS Code: *Run All*). The sections are numbered like the lesson's steps, 1 to 12. Each one has:
- a short note on what it verifies;
- a code cell that **computes** the values;
- `check(...)` lines: `PASS` means the code produced the number the lesson shows, `FAIL` means it did not;
- an interactive chart where one is worth seeing. Hover for values.

The last cell counts the checks.

**Labels used for numbers.** *measured* = computed here from real text with a real model; *toy* = made-up vectors that show a mechanism; *formula* = arithmetic; *external* = from a paper or documentation, not re-run here.

**The running example.** Draft question **D-002**, "In what year was the Paris Agreement adopted?", against the **97 chunks** of the climate PDF (v0's index: the 07 recursive chunker, per page, 1,000 characters with 200 overlap; the same file as P3's notebook). The 10 draft questions and their evidence spans come from 06 §6.7. They were drafted by an LLM and are not yet checked by you, so every rank here is an **observation, not an evaluation result**.

**Models** (local cache, offline): `all-MiniLM-L6-v2` (MiniLM, "L6"), `paraphrase-MiniLM-L3-v2` ("L3", the other model of bug 1) and `cross-encoder/ms-marco-MiniLM-L-6-v2` (the repo's reranker). The whole notebook takes about one to two minutes on a CPU.

**Where the expected values come from.** `sources/verification/P4/P4_FACTS.md`: S1–S10 (`p4_measure.py`) and §1b K1–K13 (`p4_kit_measure.py`).
""")

code(r'''
# Setup: imports, paths, the 97 chunks, the draft questions, the models and the shared helpers. Run this cell first.
import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")          # the models may load from the local cache only: no network
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

import hashlib
import heapq
import importlib.metadata as md
import json
import logging
import math
import re
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pymupdf                                        # pinned 1.26.7
import plotly.graph_objects as go
import plotly.io as pio

pio.renderers.default = "plotly_mimetype"             # small outputs that VS Code draws
warnings.filterwarnings("ignore", message="IProgress not found")
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
T0 = time.time()


def find_workspace():
    here = Path.cwd().resolve()
    for p in (here, *here.parents):
        if (p / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").is_file() and (p / "study").is_dir():
            return p
    raise FileNotFoundError("Open this notebook from inside rag_learning/.")


WS = find_workspace()
PDF = WS.parent / "upstream" / "RAG_Techniques" / "data" / "Understanding_Climate_Change.pdf"
print("workspace:", WS)
print("python", sys.version.split()[0], {p: md.version(p) for p in ("pymupdf", "numpy", "sentence-transformers", "torch", "plotly")})

# ---------------------------------------------------------------- check(): computed value vs the lesson's value
CHECKS, SKIPPED = [], []
T6, T4, T3 = 5e-7, 5e-5, 5e-4        # tolerances for values the lesson prints with 6, 4 or 3 decimals


def _plain(x):
    if isinstance(x, np.generic):
        x = x.item()
    if isinstance(x, np.ndarray):
        x = x.tolist()
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def _same(got, exp, tol):
    got, exp = _plain(got), _plain(exp)
    if got is None or exp is None:
        return got is None and exp is None
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
    return repr(x)


def check(name, got, expected, tol=0.0):
    """PASS when the computed value equals the lesson's value (numbers within `tol`)."""
    ok = _same(got, expected, tol)
    CHECKS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}: got {_show(got)}  |  lesson {_show(expected)}"
          + (f"  (tolerance {tol:g})" if tol else ""))


def skip(name, reason):
    SKIPPED.append((name, reason))
    print(f"SKIPPED  {name}: {reason}")


# ---------------------------------------------------------------- chart style (light surface, fixed colour order)
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
BLUE, ORANGE, AQUA, RED = "#2a78d6", "#eb6834", "#1baf7a", "#c8323c"
pio.templates["p4"] = go.layout.Template(layout=dict(
    font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', size=13, color=INK2),
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, colorway=[BLUE, ORANGE, AQUA],
    xaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    yaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=INK2)),
    title=dict(x=0, xanchor="left", font=dict(size=15, color=INK)),
    margin=dict(l=70, r=30, t=90, b=60), hoverlabel=dict(font_size=12)))
pio.templates.default = "p4"

# ---------------------------------------------------------------- environment (K1)
check("environment: pymupdf version (pinned)", md.version("pymupdf"), "1.26.7")
check("environment: sentence-transformers, numpy (K1)", [md.version("sentence-transformers"), md.version("numpy")], ["6.1.0", "2.5.3"])
pdf_bytes = PDF.read_bytes()
check("corpus: PDF sha256", hashlib.sha256(pdf_bytes).hexdigest(), "1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669")
pages = [p.get_text() for p in pymupdf.open(PDF)]

# ---------------------------------------------------------------- the 97 chunks, built exactly as p4_kit_measure.py (and P3's notebook)
sys.path.insert(0, str(WS / "sources" / "verification" / "corrections"))
import contracts_check as cc                          # noqa: E402  (06 recipe, 07 chunker loader, reference rel)

md06 = (WS / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
md07 = (WS / "07_SAMPLE_LESSON.md").read_text(encoding="utf-8")
cc.RECIPE_06 = cc.code_blocks(cc.section(md06, "5.3 Corpus freezing"), "python")[0]
manifest06 = cc.build_manifest("climate", pages, pdf_bytes, {**cc.PARSER, "version": pymupdf.VersionBind}, cc.CLEANING_NONE)
SNAP = manifest06["snapshot_id"]
starts = [r["doc_char_start"] for r in manifest06["docs"][0]["page_table"]]
_core, chunking, _ = cc.load_07_modules(md07)
dch = chunking.chunk_document("climate", SNAP, pages,
                              chunking.ChunkerConfig(name="recursive", size=1000, overlap=200, scope="per_page"))
CHUNKING = {"name": "recursive_char", "unit": "chars", "chunk_size": 1000, "chunk_overlap": 200,
            "separators": ["\n\n", "\n", " ", ""], "scope": "per_page"}
PH = hashlib.sha256(json.dumps(CHUNKING, sort_keys=True).encode("utf-8")).hexdigest()[:12]
chunks = [{"doc_id": "climate", "snapshot_id": SNAP, "chunk_id": f"climate:{SNAP}:{PH}:{c.seq:05d}", "seq": c.seq,
           "char_start": c.char_start, "char_end": c.char_end,
           "page_segments": [{"page": g.page, "char_start": g.char_start, "char_end": g.char_end} for g in c.page_segments],
           "text": c.text, "text_sha256": c.text_sha256, "chunker": CHUNKING["name"], "params_hash": PH, "meta": {}}
          for c in dch]
SHA_JL = hashlib.sha256("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in chunks).encode("utf-8")).hexdigest()
check("97 chunks: count", len(chunks), 97)
check("97 chunks: chunks.jsonl sha256 (= P3's notebook and the C2 lab file)", SHA_JL,
      "d4108b8936093394c6eb50d4c22e8d4013d9a048fb38d5769281af4aadb3011b")
TEXT = [c["text"] for c in chunks]
PAGE = [c["page_segments"][0]["page"] for c in chunks]
N = len(chunks)
TEXTS = {"climate": "\n".join(pages)}

# the 10 draft seeds of 06 §6.7 (llm-draft: observations, never evaluation results)
SEEDS = [json.loads(line) for line in cc.code_blocks(cc.section(md06, "6.7 Draft seed"), "jsonl")[0].splitlines() if line.strip()]
for s in SEEDS:
    s["G"] = [[[("climate", starts[seg["page"] - 1] + seg["char_start"], starts[seg["page"] - 1] + seg["char_end"])
                for seg in alt["segments"]] for alt in g["alternatives"]] for g in s["evidence_groups"]]
ANS = [s for s in SEEDS if s["answerable"]]
BYQ = {s["qid"]: s for s in SEEDS}
REL = {s["qid"]: [i for i in range(N) if cc.rel(("climate", chunks[i]["char_start"], chunks[i]["char_end"]), s["G"], TEXTS)]
       for s in ANS}
check("draft seeds: 10, of which 8 answerable", [len(SEEDS), len(ANS)], [10, 8])
check("relevant chunk seqs, D-001..D-008 (K1)", [REL[s["qid"]] for s in ANS],
      [[7], [27], [68], [23, 67, 68], [3, 4], [21], [27, 85], [69]])


def order(scores, low_is_best=False):
    """chunk seqs best first; ties broken by the smaller seq (the course rule)."""
    s = np.asarray(scores, float)
    return sorted(range(len(s)), key=lambda i: ((s[i] if low_is_best else -s[i]), i))


def first_rel(ranking, qid):
    return next((r for r, i in enumerate(ranking, 1) if i in REL[qid]), None)


def summary(ranks, k=4):
    """Hit@1, Hit@k (counts) and MRR@10 over a list of first-relevant ranks."""
    return (sum(r is not None and r <= 1 for r in ranks), sum(r is not None and r <= k for r in ranks),
            round(sum(1 / r for r in ranks if r is not None and r <= 10) / len(ranks), 3))


def unit(M):
    M = np.asarray(M, float)
    return M / np.linalg.norm(M, axis=-1, keepdims=True)


# ---------------------------------------------------------------- the three local models
MODELS_OK = False
try:
    import transformers
    transformers.utils.logging.disable_progress_bar()
    from sentence_transformers import CrossEncoder, SentenceTransformer
    from sentence_transformers.util import quantize_embeddings
    m6 = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
    m3 = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L3-v2", device="cpu")
    ce = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device="cpu")
    m6_raw = SentenceTransformer(modules=[m6[0], m6[1]], device="cpu")     # same weights, Normalize removed
    MODELS_OK = True
except Exception as e:  # noqa: BLE001
    skip("every model-based check", f"a model could not load offline: {type(e).__name__}: {str(e)[:160]}")


def enc(model, texts, **kw):
    return model.encode(list(texts), convert_to_numpy=True, batch_size=32, show_progress_bar=False, **kw)


if MODELS_OK:
    E6, E6raw, E3 = enc(m6, TEXT), enc(m6_raw, TEXT), enc(m3, TEXT)
    Q6 = {s["qid"]: enc(m6, [s["question"]])[0] for s in SEEDS}
    Q6raw = {s["qid"]: enc(m6_raw, [s["question"]])[0] for s in SEEDS}
    Q3 = {s["qid"]: enc(m3, [s["question"]])[0] for s in SEEDS}
print(f"\nsetup done in {time.time() - T0:.1f} s: {N} chunks, {len(SEEDS)} draft questions, models loaded: {MODELS_OK}")
''')

# =====================================================================================================================
md(r"""
## 1 · Three bugs that raise no error

**What this verifies** (lesson step 1).
- **Bug 1, the wrong model:** the 8 answerable questions embedded by L3, scored against chunk vectors made by L6. Both give 384 numbers, so nothing raises. Compared with L6 used correctly, and with L3 used correctly (its own chunk vectors).
- **Bug 2, a distance read as a similarity:** the `graph_rag.ipynb` cell 12 heap with toy scores 0.2, 0.5, 0.9 (S10).
- **Bug 3, truncation:** the 400-token passage whose DAC definition starts at text token 300 (S7; built from the whole PDF text, so it does not depend on chunking).
""")
code(r'''
if MODELS_OK:
    ARMS = {
        "right": {s["qid"]: E6 @ Q6[s["qid"]] for s in ANS},
        "wrong": {s["qid"]: E6 @ unit(Q3[s["qid"]]) for s in ANS},
        "L3 own": {s["qid"]: unit(E3) @ unit(Q3[s["qid"]]) for s in ANS},
    }
    RANKS = {a: [first_rel(order(sc[s["qid"]]), s["qid"]) for s in ANS] for a, sc in ARMS.items()}
    for a in RANKS:
        print(f"   {a:7s} ranks D-001..D-008 {RANKS[a]}  Hit@1, Hit@4, MRR@10 = {summary(RANKS[a])}")
    check("§1 bug 1: right model, ranks (K4)", RANKS["right"], [3, 3, 1, 1, 1, 1, 2, 2])
    check("§1 bug 1: wrong model, ranks (K4)", RANKS["wrong"], [21, 16, 7, 1, 1, 9, 1, 15])
    check("§1 bug 1: Hit@4 right vs wrong (of 8)", [summary(RANKS["right"])[1], summary(RANKS["wrong"])[1]], [8, 3])
    check("§1 bug 1: MRR@10 right, wrong, L3 own index", [summary(RANKS[a])[2] for a in ("right", "wrong", "L3 own")],
          [0.708, 0.407, 0.698], T3)
    check("§1 bug 1: L3 used correctly, Hit@4 (of 8)", summary(RANKS["L3 own"])[1], 8)
    check("§1 bug 1: D-002 rank right -> wrong (of 97)", [RANKS["right"][1], RANKS["wrong"][1]], [3, 16])
    check("§1 bug 1: both models give 384 numbers (so nothing raises)", [E6.shape[1], Q3["D-002"].shape[0]], [384, 384])

# bug 2: graph_rag cell 12, priority = 1 / score, smallest priority popped first (TOY scores, S10)
nodes = {"A": 0.20, "B": 0.50, "C": 0.90}
h = []
for n, s in nodes.items():
    heapq.heappush(h, (1 / s, n))
pops = [heapq.heappop(h)[1] for _ in range(len(h))]
check("§1 bug 2: heap pop order with 1/score (S10)", pops, ["C", "B", "A"])
check("§1 bug 2: if the score is a distance, the closest node (A) is explored at step", pops.index("A") + 1, 3)
try:
    1 / 0.0
    zero = "no error"
except ZeroDivisionError:
    zero = "ZeroDivisionError"
check("§1 bug 2: a distance of exactly 0 gives", zero, "ZeroDivisionError")

# bug 3: truncation (S7), the same construction as p4_measure.py
if MODELS_OK:
    norm_ws = lambda s: re.sub(r"\s+", " ", s)
    nf = norm_ws("\n".join(pages))
    key = "Direct air capture (DAC)"
    tok = m6.tokenizer
    offs = tok(nf, add_special_tokens=False, return_offsets_mapping=True, truncation=False)["offset_mapping"]
    pos = nf.find(key)
    key_tok = next(i for i, (a, b) in enumerate(offs) if a >= pos)
    st = key_tok - 300
    long_text = nf[offs[st][0]:offs[st + 400 - 1][1]]
    prefix = nf[offs[st][0]:offs[st + 254 - 1][1]]
    tail = nf[offs[st + 254][0]:offs[st + 400 - 1][1]]
    qv = enc(m6, [BYQ["D-004"]["question"]])[0]
    el, ep, et = enc(m6, [long_text, prefix, tail])
    check("§1 bug 3: the DAC phrase starts at text token (S7)", key_tok - st, 300)
    check("§1 bug 3: cos(question, 400-token passage), cos(question, first 254 tokens), cos(question, tail) (S7)",
          [float(qv @ el), float(qv @ ep), float(qv @ et)], [0.019276, 0.019276, 0.284787], T6)
''')

# =====================================================================================================================
md(r"""
## 2 · An embedding is an arrow; cosine reads only its angle

**What this verifies** (lesson step 2). MiniLM's output size and pooling (K1); the toy table with q = [1, 2, 2] (S2), the rankings, and the "double one vector" effects; and the playground's default numbers (toy, 2 numbers per arrow: q at 45° and length 1.5, A at 20° and length 1, B at 55° and length 2.4).
""")
code(r'''
if MODELS_OK:
    check("§2 MiniLM: numbers per vector, pooling, modules (K1)",
          [m6.get_embedding_dimension(), m6[1].get_config_dict().get("pooling_mode"), [type(x).__name__ for x in m6]],
          [384, "mean", ["Transformer", "Pooling", "Normalize"]])


def cos(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def l2(a, b):
    return float(np.linalg.norm(np.asarray(a, float) - np.asarray(b, float)))


q = np.array([1, 2, 2], float)
D = {"d1": np.array([2, 1, 2], float), "d2": np.array([0, 3, 4], float), "d3": np.array([2, 4, 4], float)}
check("§2 toy lengths |q|, |d1|, |d2|, |d3| (S2)", [np.linalg.norm(v) for v in (q, *D.values())], [3, 3, 5, 6], T6)
check("§2 toy dot (S2)", [q @ d for d in D.values()], [8, 14, 18])
check("§2 toy cosine (S2)", [cos(q, d) for d in D.values()], [0.8889, 0.9333, 1.0], T4)
check("§2 toy L2 (S2)", [l2(q, d) for d in D.values()], [1.4142, 2.4495, 3.0], T4)
check("§2 ranking by cosine (high first)", sorted(D, key=lambda k: -cos(q, D[k])), ["d3", "d2", "d1"])
check("§2 ranking by raw L2 (low first): the exact reverse", sorted(D, key=lambda k: l2(q, D[k])), ["d1", "d2", "d3"])
check("§2 double d1: dot, cos, L2", [q @ (2 * D["d1"]), cos(q, 2 * D["d1"]), l2(q, 2 * D["d1"])], [16, 0.8889, 3.6056], T4)
check("§2 double q: raw-L2 ranking flips to", sorted(D, key=lambda k: l2(2 * q, D[k])), ["d3", "d2", "d1"])

# the playground's default arrows (TOY)
arrow = lambda ang, ln: ln * np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
qa, A, B = arrow(45, 1.5), arrow(20, 1.0), arrow(55, 2.4)
pg = [[qa @ A, qa @ B], [cos(qa, A), cos(qa, B)], [l2(qa, A), l2(qa, B)]]
print("   playground q vs A, q vs B: dot", np.round(pg[0], 4), "cos", np.round(pg[1], 4), "L2", np.round(pg[2], 4))
check("§2 playground L2: q vs A, q vs B", pg[2], [0.7288, 0.9588], T4)
check("§2 playground winners: dot, cosine, L2", ["A" if pg[0][0] > pg[0][1] else "B", "A" if pg[1][0] > pg[1][1] else "B",
                                                 "A" if pg[2][0] < pg[2][1] else "B"], ["B", "B", "A"])
uq, uA, uB = (v / np.linalg.norm(v) for v in (qa, A, B))
check("§2 playground normalised: L2 now prefers B too", "A" if l2(uq, uA) < l2(uq, uB) else "B", "B")
''')

# =====================================================================================================================
md(r"""
## 3 · Normalise once, and the three measures agree; read the direction

**What this verifies** (lesson step 3).
- The bridge L2² = 2 − 2cos on the toy (S2) and on 1,000 random vectors × 100 random questions (S3, `default_rng(0)`, the same draws as `p4_measure.py`).
- Vector lengths on the 97 chunks with and without the Normalize step, and for L3 (K2).
- What raw vectors do to the rankings (K3, K4).
- Every library convention for one pair (K5), the converter at cosine 0.6, and the self-retrieval test. **No LangChain or FAISS import:** their formulas (squared L2; 1 − d/√2) are applied to MiniLM vectors.
""")
code(r'''
uq = q / np.linalg.norm(q)
UL = [l2(uq, d / np.linalg.norm(d)) for d in D.values()]
check("§3 toy L2 on unit vectors (S2)", UL, [0.4714, 0.3651, 0.0], T4)
check("§3 toy 0.4714^2 = 2 - 2 x 0.8889", [UL[0] ** 2, 2 - 2 * cos(q, D["d1"])], [0.2222, 0.2222], T4)

rng = np.random.default_rng(0)                         # S3: the same draws, in the same order, as p4_measure.py
X, Q = rng.normal(size=(1000, 384)), rng.normal(size=(100, 384))
cosM = (Q @ X.T) / (np.linalg.norm(Q, axis=1)[:, None] * np.linalg.norm(X, axis=1)[None, :])
Xu, Qu = unit(X), unit(Q)
L2U = np.sqrt(np.maximum(0.0, 2 - 2 * (Qu @ Xu.T)))   # ‖q̂ − x̂‖ for unit vectors, without a 100 × 1,000 × 384 array
same_full = sum(np.array_equal(np.argsort(-cosM[i], kind="stable"), np.argsort(L2U[i], kind="stable")) for i in range(100))
scales = rng.uniform(0.5, 2.0, size=1000)
Xs = X * scales[:, None]
top_cos = ((Q @ Xs.T) / (np.linalg.norm(Q, axis=1)[:, None] * np.linalg.norm(Xs, axis=1)[None, :])).argmax(1)
sq_l2 = (Q ** 2).sum(1)[:, None] + (Xs ** 2).sum(1)[None, :] - 2 * (Q @ Xs.T)   # ‖q − x‖², the same expansion
l2_diff = int((sq_l2.argmin(1) != top_cos).sum())
dot_diff = int(((Q @ Xs.T).argmax(1) != top_cos).sum())
check("§3 random vectors: identical full ranking, cosine vs unit-vector L2 (S3)", same_full, 100)
check("§3 random vectors, lengths 0.5-2x: raw-L2 top-1 differs, raw-dot top-1 differs (of 100, S3)", [l2_diff, dot_diff], [94, 68])

if MODELS_OK:
    nrm = {k: np.linalg.norm(E, axis=1) for k, E in (("L6", E6), ("L6 raw", E6raw), ("L3", E3))}
    check("§3 MiniLM as shipped: shortest, longest vector (K2)", [nrm["L6"].min(), nrm["L6"].max()], [1.0, 1.0], T6)
    check("§3 Normalize removed: shortest, longest (K2)", [nrm["L6 raw"].min(), nrm["L6 raw"].max()], [2.048730, 3.272804], T6)
    check("§3 L3 (no Normalize): shortest, longest (K2)", [nrm["L3"].min(), nrm["L3"].max()], [2.363580, 3.474059], T6)
    dr = E6raw @ Q6raw["D-002"]
    lr = np.linalg.norm(E6raw - Q6raw["D-002"], axis=1)
    check("§3 D-002 on raw vectors: rank under raw dot, under raw L2 (K3)",
          [first_rel(order(dr), "D-002"), first_rel(order(lr, True), "D-002")], [1, 4])
    raw_dot = [first_rel(order(E6raw @ Q6raw[s["qid"]]), s["qid"]) for s in ANS]
    raw_l2 = [first_rel(order(np.linalg.norm(E6raw - Q6raw[s["qid"]], axis=1), True), s["qid"]) for s in ANS]
    check("§3 8 questions on raw vectors: MRR@10 raw dot, raw L2 (K4; both ways, i.e. noise)",
          [summary(raw_dot)[2], summary(raw_l2)[2]], [0.719, 0.698], T3)

    fig = go.Figure()
    for k, colour in (("L6", BLUE), ("L6 raw", ORANGE), ("L3", AQUA)):
        fig.add_histogram(x=nrm[k], name={"L6": "MiniLM as shipped", "L6 raw": "Normalize removed", "L3": "L3 (no Normalize)"}[k],
                          marker=dict(color=colour), nbinsx=40, hovertemplate="length %{x:.3f}: %{y} chunks<extra></extra>")
    fig.update_layout(title="§3 · Vector lengths of the 97 chunks: only the shipped MiniLM gives exactly 1", barmode="overlay",
                      height=360, xaxis=dict(title="vector length ‖v‖"), yaxis=dict(title="chunks"))
    fig.update_traces(opacity=0.8)
    fig.show()

    # every library convention for one pair (K5)
    a, b = enc(m6, ["greenhouse gas emissions", "a recipe for chocolate cake"])
    c_ab, L = float(a @ b), float(np.linalg.norm(a - b))
    m6.similarity_fn_name = "euclidean"
    st_euc = float(m6.similarity(a[None], b[None])[0][0])
    m6.similarity_fn_name = "cosine"
    check("§3 the pair: cosine, L2, squared L2 (FAISS), 2 - 2cos (K5)", [c_ab, L, L * L, 2 - 2 * c_ab],
          [-0.0859, 1.4737, 2.1719, 2.1719], T4)
    check("§3 sentence-transformers similarity_fn_name='euclidean' returns -L2 (K5)", st_euc, -1.4737, T4)
    check("§3 LangChain 1 - d/sqrt(2): on FAISS squared L2, on true L2 (K5)",
          [1 - L * L / math.sqrt(2), 1 - L / math.sqrt(2)], [-0.5357, -0.0421], T4)
    check("§3 worst case (squared L2 = 4) and the sign-change cosine 1 - 1/sqrt(2) (K5)",
          [1 - 4 / math.sqrt(2), 1 - 1 / math.sqrt(2)], [-1.8284, 0.2929], T4)
    c2 = E6 @ Q6["D-002"]
    check("§3 D-002: chunks with cos < 0.2929 (negative LangChain relevance on FAISS), with cos < 0 (K5)",
          [int((c2 < 1 - 1 / math.sqrt(2)).sum()), int((c2 < 0).sum())], [91, 33])
    check("§3 self-retrieval: chunks that rank themselves first (K5)", sum(order(E6 @ E6[i])[0] == i for i in range(N)), 97)

# the converter and the chord (FORMULA)
c = 0.6
check("§3 converter at cos 0.6: L2, squared L2, -L2, LangChain on FAISS, LangChain as designed",
      [math.sqrt(2 - 2 * c), 2 - 2 * c, -math.sqrt(2 - 2 * c), 1 - (2 - 2 * c) / math.sqrt(2), 1 - math.sqrt(2 - 2 * c) / math.sqrt(2)],
      [0.8944, 0.8, -0.8944, 0.4343, 0.3675], T4)
check("§3 chord: L2 of two unit arrows at 60 and 90 degrees", [math.sqrt(2 - 2 * math.cos(math.radians(t))) for t in (60, 90)],
      [1.0, 1.4142], T4)
''')

# =====================================================================================================================
md(r"""
## 4 · The question is embedded too, and gets one score per chunk

**What this verifies** (lesson step 4). D-002's score vector: its shape, the top 5 with their cosines, the rank of the right chunk, and Hit@4 / reciprocal rank; the 8-question summary; what chunks 69 and 27 contain; and the chunk-against-chunk analysis (the N × N matrix that belongs to analysis, not search).
""")
code(r'''
if MODELS_OK:
    s2 = E6 @ Q6["D-002"]
    o2 = order(s2)
    check("§4 D-002: score vector shape; an all-pairs matrix would hold (K3)", [list(s2.shape), N * N], [[97], 9409])
    check("§4 D-002 top 5 chunk seqs (K3)", o2[:5], [69, 68, 27, 17, 84])
    check("§4 D-002 top 5 cosines (K3)", [s2[i] for i in o2[:5]], [0.4606, 0.4513, 0.4386, 0.4385, 0.3387], T4)
    r = first_rel(o2, "D-002")
    check("§4 D-002: rank of the right chunk, Hit@4, reciprocal rank", [r, int(r <= 4), 1 / r], [3, 1, 0.3333], T4)
    check("§4 8 questions: Hit@4 (of 8), MRR@10 (K4)", list(summary(RANKS["right"])[1:]), [8, 0.708], T3)
    check("§4 chunk 69 is about the Kyoto Protocol's year; chunk 27 holds the answer",
          ["Kyoto Protocol, adopted in 1997" in re.sub(r"\s+", " ", TEXT[69]), "adopted in 2015" in re.sub(r"\s+", " ", TEXT[27]),
           PAGE[27]], [True, True, 10])
    check("§4 L2 on unit vectors gives the identical full ranking (K3)", order(np.linalg.norm(E6 - Q6["D-002"], axis=1), True) == o2, True)

    C = E6 @ E6.T
    iu = np.triu_indices(N, 1)
    pairs = C[iu]
    j = int(np.argmax(pairs))
    check("§4 analysis: distinct chunk pairs, closest pair (seqs), its cosine, pairs above 0.90 (K6)",
          [len(pairs), [int(iu[0][j]), int(iu[1][j])], float(pairs[j]), int((pairs > 0.90).sum())], [4656, [4, 5], 0.8590, 0], T4)

    fig = go.Figure()
    srt = [s2[i] for i in o2]
    fig.add_scatter(x=list(range(1, N + 1)), y=np.round(srt, 4), mode="lines+markers", name="D-002 score per chunk, best first",
                    line=dict(color=BLUE, width=2), marker=dict(size=5), customdata=o2,
                    hovertemplate="rank %{x}: chunk %{customdata}, cosine %{y:.4f}<extra></extra>")
    fig.add_scatter(x=[3], y=[round(float(s2[27]), 4)], mode="markers+text", name="the right chunk (27)", text=["chunk 27: rank 3"],
                    textposition="top right", marker=dict(size=12, color=AQUA), hoverinfo="skip")
    fig.update_layout(title="§4 · One question, 97 scores: a list, not a matrix (D-002, MiniLM)", height=380,
                      xaxis=dict(title="rank"), yaxis=dict(title="cosine with the question"))
    fig.show()

    fig = go.Figure(go.Histogram(x=pairs, xbins=dict(start=-0.2, end=1.0, size=0.1), marker=dict(color=ORANGE, line=dict(width=2, color=SURFACE)),
                                 hovertemplate="cosine %{x}: %{y} pairs<extra></extra>"))
    fig.update_layout(title="§4 · Analysis, not search: all 4,656 chunk-vs-chunk cosines (97 × 97, one triangle)", height=340,
                      xaxis=dict(title="cosine between two chunks"), yaxis=dict(title="pairs"), showlegend=False)
    fig.show()
    check("§4 histogram counts, bins -0.2..1.0 by 0.1 (K6)", np.histogram(pairs, bins=np.arange(-0.2, 1.0001, 0.1))[0].tolist(),
          [0, 2, 70, 375, 787, 1201, 1139, 704, 286, 87, 5, 0])
''')

# =====================================================================================================================
md(r"""
## 5 · Where the closeness comes from

**What this verifies** (lesson step 5). The training facts read from MiniLM's local model card (batch size, training length, number of pairs, the contrastive objective), and the toy training batch: 4 questions with their right chunks, S = Q·Pᵀ, the softmax share of each row at τ = 0.05, and the loss with the true and with shuffled pairs (K10). τ is a toy choice; the card does not state MiniLM's own.
""")
code(r'''
hub = Path.home() / ".cache" / "huggingface" / "hub" / "models--sentence-transformers--all-MiniLM-L6-v2"
card_file = hub / "snapshots" / "1110a243fdf4706b3f48f1d95db1a4f5529b4d41" / "README.md"
if card_file.exists():
    card = card_file.read_text(encoding="utf-8")
    check("§5 model card: batch size 1024, sequence length 128, 'above 1 billion' pairs, contrastive, 256 truncation",
          ["batch size of 1024" in card, "limited to 128 tokens" in card, "above 1 billion" in card,
           "contrastive" in card, "longer than 256 word pieces is truncated" in card], [True] * 5)
else:
    skip("§5 model card facts", f"README not found at {card_file}")

if MODELS_OK:
    Bq = ["D-002", "D-004", "D-006", "D-008"]
    Qb = np.stack([Q6[k] for k in Bq])
    Pb = np.stack([E6[REL[k][0]] for k in Bq])
    Sb = Qb @ Pb.T
    check("§5 batch columns: the first right chunk of each question", [REL[k][0] for k in Bq], [27, 23, 21, 69])
    check("§5 S = Q P^T, row D-002 (K10)", Sb[0], [0.4386, -0.0065, -0.0837, 0.4606], T4)
    check("§5 S, rows D-004, D-006, D-008 (K10)", Sb[1:], [[0.2136, 0.4035, -0.0315, 0.0964], [0.1202, 0.3313, 0.5331, 0.1391],
                                                       [0.1716, -0.0716, -0.0409, 0.2535]], T4)
    check("§5 rows whose largest cosine is on the diagonal", int(sum(np.argmax(Sb[i]) == i for i in range(4))), 3)

    def info_nce(S, scale):
        z = S * scale
        lsm = z - np.log(np.exp(z).sum(1, keepdims=True))
        return np.exp(np.diag(lsm)), float(-np.mean(np.diag(lsm)))

    share, loss = info_nce(Sb, 20)
    check("§5 tau 0.05: the true pair's share of each row; mean loss (K10)", [*share, loss], [0.3917, 0.9759, 0.9820, 0.8343, 0.2903], T4)
    check("§5 tau 1: mean loss (K10)", info_nce(Sb, 1)[1], 1.1789, T4)
    check("§5 shuffled pairs, tau 0.05: mean loss (K10)", info_nce(Qb @ Pb[[1, 2, 3, 0]].T, 20)[1], 7.0697, T4)
    fig = go.Figure(go.Heatmap(z=np.round(Sb, 4), x=[f"chunk {REL[k][0]}" for k in Bq], y=Bq, colorscale=[[0, SURFACE], [1, BLUE]],
                               text=np.round(Sb, 4), texttemplate="%{text}", hovertemplate="%{y} vs %{x}: %{z:.4f}<extra></extra>"))
    fig.update_layout(title="§5 · A toy training batch: S = Q·Pᵀ (the true pairs are on the diagonal)", height=360,
                      yaxis=dict(autorange="reversed"))
    fig.show()
''')

# =====================================================================================================================
md(r"""
## 6 · Text past the limit cannot help retrieval

**What this verifies** (lesson step 6). The two models' limits (S1), the token counts of the 97 chunks with MiniLM's own tokenizer (special tokens included), how many go past 256 and past the 128 tokens MiniLM was trained on, and how many L3 would cut (K7). The DAC passage itself is checked in section 1.
""")
code(r'''
if MODELS_OK:
    check("§6 max_seq_length: L6, L3 (S1)", [m6.max_seq_length, m3.max_seq_length], [256, 128])
    ntok = [len(m6.tokenizer(t, add_special_tokens=True)["input_ids"]) for t in TEXT]
    ntok3 = [len(m3.tokenizer(t, add_special_tokens=True)["input_ids"]) for t in TEXT]
    check("§6 tokens per chunk: min, median, max (K7)", [min(ntok), int(np.median(ntok)), max(ntok)], [59, 149, 182])
    check("§6 chunks over 256, over 128 (trained length), cut by L3 (K7)",
          [sum(n > 256 for n in ntok), sum(n > 128 for n in ntok), sum(n > 128 for n in ntok3)], [0, 70, 70])
    check("§6 characters per chunk: min, median, max (K7)", [min(map(len, TEXT)), int(np.median(list(map(len, TEXT)))), max(map(len, TEXT))],
          [393, 935, 1000])
    fig = go.Figure(go.Histogram(x=ntok, nbinsx=25, marker=dict(color=BLUE, line=dict(width=2, color=SURFACE)),
                                 hovertemplate="%{x} tokens: %{y} chunks<extra></extra>"))
    fig.add_vline(x=128, line=dict(color=ORANGE, dash="dash"), annotation_text="trained on ≤ 128", annotation_position="top left")
    fig.add_vline(x=256, line=dict(color=RED), annotation_text="limit 256", annotation_position="top left")
    fig.update_layout(title="§6 · Tokens per chunk (MiniLM's tokenizer): all fit under 256, most are longer than 128",
                      height=360, xaxis=dict(title="tokens, [CLS] and [SEP] included", range=[0, 280]), yaxis=dict(title="chunks"), showlegend=False)
    fig.show()
''')

# =====================================================================================================================
md(r"""
## 7 · Same model, but the question may need its own label

**What this verifies** (lesson step 7). sentence-transformers' `encode_query` / `encode_document` against `encode` for MiniLM (no prompts, so identical), the question-vs-statement gap on chunk 27 (K8), and what a prefix does to a model not trained with one (S9; independent of chunking).
""")
code(r'''
if MODELS_OK:
    qs = [s["question"] for s in SEEDS]
    check("§7 MiniLM's prompts are empty (K1)", [m6.prompts.get("query"), m6.prompts.get("document")], ["", ""])
    d_q = float(np.abs(m6.encode_query(qs, convert_to_numpy=True, show_progress_bar=False) - enc(m6, qs)).max())
    d_d = float(np.abs(m6.encode_document(TEXT[:10], convert_to_numpy=True, show_progress_bar=False) - E6[:10]).max())
    check("§7 max |encode_query - encode|, max |encode_document - encode| (K8)", [d_q, d_d], [0.0, 0.0])
    eq, es = enc(m6, [BYQ["D-002"]["question"], "The Paris Agreement was adopted in 2015."])
    check("§7 chunk 27: cos with the question, with the statement; cos(question, statement) (K8)",
          [float(eq @ E6[27]), float(es @ E6[27]), float(eq @ es)], [0.4386, 0.4775, 0.8069], T4)
    check("§7 rank of chunk 27: with the question, with the statement (K8)",
          [first_rel(order(E6 @ eq), "D-002"), first_rel(order(E6 @ es), "D-002")], [3, 1])
    pre = [float(np.dot(*enc(m6, [p + BYQ["D-002"]["question"], BYQ["D-002"]["question"]])))
           for p in ("query: ", "search_query: ", "Represent this sentence for searching relevant passages: ")]
    check("§7 a prefix just moves the vector: cos(prefix + q, q) (S9)", pre, [0.9626, 0.6965, 0.6865], T4)
''')

# =====================================================================================================================
md(r"""
## 8 · Bi-encoder vs cross-encoder

**What this verifies** (lesson step 8). The cross-encoder reranking D-002's top 10, its raw logits, the effect of input order, the 8-question illustration, and the pass counts (K9). An illustration on easy draft questions, not an evaluation: R3 measures reranking properly.
""")
code(r'''
if MODELS_OK:
    qd = BYQ["D-002"]["question"]
    short = order(E6 @ Q6["D-002"])[:10]
    cs = ce.predict([(qd, TEXT[i]) for i in short], show_progress_bar=False)
    rer = [short[i] for i in np.argsort(-cs, kind="stable")]
    check("§8 D-002 bi-encoder top 10 (K9)", short, [69, 68, 27, 17, 84, 85, 70, 35, 83, 71])
    check("§8 D-002 cross-encoder logits on the top 10: min, max (K9)", [float(cs.min()), float(cs.max())], [-11.056, 3.272], T3)
    check("§8 D-002 reranked top 3; rank of chunk 27 after reranking (K9)", [rer[:3], first_rel(rer, "D-002")], [[27, 68, 69], 1])
    check("§8 order matters: CE(question, chunk 69), CE(chunk 69, question) (K9)",
          [float(ce.predict([(qd, TEXT[69])], show_progress_bar=False)[0]), float(ce.predict([(TEXT[69], qd)], show_progress_bar=False)[0])],
          [-4.361, -3.321], T3)
    ce_r = []
    for s in ANS:
        ob = order(E6 @ Q6[s["qid"]])
        sc = ce.predict([(s["question"], TEXT[i]) for i in ob[:10]], show_progress_bar=False)
        ce_r.append(first_rel([ob[:10][i] for i in np.argsort(-sc, kind="stable")] + ob[10:], s["qid"]))
    check("§8 8 questions: right chunk first, bi-encoder vs after reranking (K9)", [summary(RANKS["right"])[0], summary(ce_r)[0]], [4, 8])
check("§8 model passes per question: bi, rerank top 10, cross-encoder over all 97 (FORMULA)", [1, 1 + 10, 97], [1, 11, 97])
''')

# =====================================================================================================================
md(r"""
## 9 · A 0.5 means different things in different places

**What this verifies** (lesson step 9). The five sentence pairs (S5, re-measured), the best score per draft question including the two with no answer in the PDF (K4), the per-question medians and the spread of all 970 question–chunk scores (K6). The chart is the lesson's score strip.
""")
code(r'''
if MODELS_OK:
    PAIRS = [("greenhouse gas emissions", "carbon dioxide in the atmosphere"),
             ("greenhouse gas emissions", "a recipe for chocolate cake"),
             ("Burning coal and oil releases gases that warm the planet.", "Fossil fuel combustion emits greenhouse gases that heat the Earth."),
             ("Burning coal and oil releases gases that warm the planet.", "The museum opens at nine on Saturday mornings."),
             ("Global temperatures have risen since the late 19th century.", "Global temperatures have not risen since the late 19th century.")]
    pc = [float(np.dot(*enc(m6, [a, b]))) for a, b in PAIRS]
    check("§9 sentence pairs: book pair, cake, paraphrase, museum, opposite claims (S5)", pc, [0.5356, -0.0859, 0.6918, -0.0478, 0.8436], T4)
    top1 = {s["qid"]: float((E6 @ Q6[s["qid"]]).max()) for s in SEEDS}
    check("§9 best score per question D-001..D-010 (K4)", list(top1.values()),
          [0.4929, 0.4606, 0.6497, 0.4210, 0.4272, 0.5331, 0.7094, 0.2598, 0.3099, 0.5196], T4)
    check("§9 answerable questions whose best score is below D-010's", sum(top1[s["qid"]] < top1["D-010"] for s in ANS), 5)
    med = {s["qid"]: float(np.median(E6 @ Q6[s["qid"]])) for s in SEEDS}
    check("§9 median score over the 97 chunks: lowest, highest (K6)", [min(med, key=med.get), med["D-002"], max(med, key=med.get), med["D-010"]],
          ["D-002", 0.0289, "D-010", 0.2500], T4)
    allq = np.concatenate([E6 @ Q6[s["qid"]] for s in SEEDS])
    check("§9 all 970 scores: min, median, 90th percentile, max (K6)",
          [allq.min(), np.median(allq), np.percentile(allq, 90), allq.max()], [-0.1536, 0.1416, 0.3228, 0.7094], T4)
    check("§9 chunk-vs-chunk median (K6)", float(np.median(C[np.triu_indices(N, 1)])), 0.3906, T4)

    fig = go.Figure()
    fig.add_scatter(x=np.round(pc, 4), y=["sentence pairs"] * 5, mode="markers+text", marker=dict(size=12, color=[BLUE, BLUE, BLUE, BLUE, RED]),
                    text=["book pair", "cake", "paraphrase", "museum", "opposite claims"], textposition="top center", name="sentence pairs",
                    hovertemplate="%{text}: %{x:.4f}<extra></extra>")
    ans_q = [s["qid"] for s in ANS]
    fig.add_scatter(x=[round(top1[k], 4) for k in ans_q], y=["best chunk per question"] * 8, mode="markers", marker=dict(size=12, color=AQUA),
                    name="answerable", text=ans_q, hovertemplate="%{text}: %{x:.4f}<extra></extra>")
    fig.add_scatter(x=[round(top1["D-009"], 4), round(top1["D-010"], 4)], y=["best chunk per question"] * 2, mode="markers+text",
                    marker=dict(size=13, color=RED, symbol="x"), text=["D-009", "D-010"], textposition="bottom center", name="no answer in the PDF",
                    hovertemplate="%{text}: %{x:.4f}<extra></extra>")
    fig.add_box(x=np.round(allq, 4), y=["all 970 scores"] * len(allq), name="all 970 question-chunk scores", marker=dict(color=ORANGE),
                boxpoints=False, orientation="h")
    fig.update_layout(title="§9 · MiniLM scores on one line: no threshold separates 'answer' from 'no answer'", height=420,
                      xaxis=dict(title="cosine", range=[-0.25, 0.95]), yaxis=dict(title=""))
    fig.show()
''')

# =====================================================================================================================
md(r"""
## 10 · Smaller vectors: cut, rescale, re-measure

**What this verifies** (lesson step 10). Cutting MiniLM to 256, 128, 64 and 32 numbers with `truncate_dim` (MiniLM is not Matryoshka-trained): the lengths after the cut, the 8-question ranks with rescaled cosine and with raw dot, and how often the two agree on the top 5 (K11). Then int8 and binary vectors (K12). Two charts: MRR@10 per size, and top-5 overlap per question.
""")
code(r'''
if MODELS_OK:
    EXP = {384: ([1.0, 1.0], [3, 3, 1, 1, 1, 1, 2, 2], 0.708, 0.708, 8), 256: ([0.7707, 0.8690], [2, 2, 1, 1, 1, 1, 2, 2], 0.750, 0.688, 4),
           128: ([0.5108, 0.6417], [2, 2, 2, 1, 2, 1, 2, 6], 0.583, 0.705, 2), 64: ([0.3256, 0.4842], [3, 2, 2, 1, 3, 1, 3, 6], 0.521, 0.570, 1),
           32: ([0.2069, 0.4035], [6, 23, 5, 1, 2, 1, 11, 32], 0.358, 0.375, 0)}
    DIMS = {}
    for d in (384, 256, 128, 64, 32):
        Ed = enc(m6, TEXT, truncate_dim=d)
        Qd = {s["qid"]: enc(m6, [s["question"]], truncate_dim=d)[0] for s in ANS}
        n_d = np.linalg.norm(Ed, axis=1)
        cr = [first_rel(order(unit(Ed) @ unit(Qd[s["qid"]])), s["qid"]) for s in ANS]
        dr_ = [first_rel(order(Ed @ Qd[s["qid"]]), s["qid"]) for s in ANS]
        same5 = sum(order(Ed @ Qd[s["qid"]])[:5] == order(unit(Ed) @ unit(Qd[s["qid"]]))[:5] for s in ANS)
        DIMS[d] = (summary(cr)[2], summary(dr_)[2])
        e = EXP[d]
        check(f"§10 {d} numbers: shortest and longest chunk vector after the cut (K11)", [n_d.min(), n_d.max()], e[0], T4)
        check(f"§10 {d} numbers: ranks with rescaled cosine (K11)", cr, e[1])
        check(f"§10 {d} numbers: MRR@10 rescaled cosine, raw dot; top 5 identical (of 8) (K11)", [DIMS[d][0], DIMS[d][1], same5],
              [e[2], e[3], e[4]], T3)
    fig = go.Figure()
    xs = [str(d) for d in (32, 64, 128, 256, 384)]
    fig.add_scatter(x=xs, y=[DIMS[d][0] for d in (32, 64, 128, 256, 384)], mode="lines+markers", name="rescaled cosine", line=dict(color=BLUE, width=3))
    fig.add_scatter(x=xs, y=[DIMS[d][1] for d in (32, 64, 128, 256, 384)], mode="lines+markers", name="raw dot, not rescaled",
                    line=dict(color=ORANGE, width=2, dash="dash"))
    fig.update_layout(title="§10 · MRR@10 on 8 draft questions as MiniLM is cut (not Matryoshka-trained; noise between close values)",
                      height=380, xaxis=dict(title="numbers kept", type="category"), yaxis=dict(title="MRR@10", range=[0, 1]))
    fig.show()

    QA = np.stack([Q6[s["qid"]] for s in ANS])
    rngs = np.vstack((E6.min(0), E6.max(0)))
    E8, Q8 = quantize_embeddings(E6, "int8", ranges=rngs), quantize_embeddings(QA, "int8", ranges=rngs)
    Eb, Qb2 = quantize_embeddings(E6, "ubinary"), quantize_embeddings(QA, "ubinary")
    check("§10 bytes per vector: float32, int8, binary (K12)", [E6[0].nbytes, E8[0].nbytes, Eb[0].nbytes], [1536, 384, 48])
    bits = np.unpackbits(Eb, axis=1)
    rk, ov = {"int8": [], "binary": []}, {"int8": [], "binary": []}
    for j, s in enumerate(ANS):
        of = order(E6 @ QA[j])
        o8 = order(E8.astype(np.int32) @ Q8[j].astype(np.int32))
        ob = order((bits != np.unpackbits(Qb2[j][None], axis=1)).sum(1), low_is_best=True)
        for k_, oo in (("int8", o8), ("binary", ob)):
            rk[k_].append(first_rel(oo, s["qid"]))
            ov[k_].append(len(set(oo[:5]) & set(of[:5])))
    check("§10 int8: ranks; MRR@10; mean top-5 overlap with float (K12)", [rk["int8"], summary(rk["int8"])[2], float(np.mean(ov["int8"]))],
          [[4, 3, 1, 1, 1, 1, 2, 1], 0.760, 4.375], T3)
    check("§10 binary: ranks; MRR@10; mean top-5 overlap with float (K12)", [rk["binary"], summary(rk["binary"])[2], float(np.mean(ov["binary"]))],
          [[2, 2, 2, 1, 1, 1, 3, 4], 0.635, 4.125], T3)
    check("§10 every right chunk still in the top 4 (int8, binary)", [max(rk["int8"]) <= 4, max(rk["binary"]) <= 4], [True, True])
    fig = go.Figure()
    for k_, colour in (("int8", BLUE), ("binary", ORANGE)):
        fig.add_bar(x=ans_q, y=ov[k_], name=k_, marker=dict(color=colour, line=dict(width=2, color=SURFACE)),
                    hovertemplate="%{x}: %{y} of float's top 5<extra>" + k_ + "</extra>")
    fig.update_layout(title="§10 · Compressed vectors: how many of float32's top 5 they keep, per question", height=360,
                      yaxis=dict(title="chunks shared with float's top 5", range=[0, 5.2]), barmode="group")
    fig.show()
''')

# =====================================================================================================================
md(r"""
## 11 · Choosing a model, and what it costs

**What this verifies** (lesson step 11). The cost and memory arithmetic (FORMULA, K13; the $0.12-per-million price is UNVERIFIED and only illustrates the formula). Then the Cohere column: it fills **only** from a recorded replay pack made by the planned LLMOps notebook (`study/notebooks/P4_embeddings_llmops.ipynb`, 12 recorded calls). This section looks for that pack and, if it is missing, skips with a reason. It never calls Cohere.
""")
code(r'''
check("§11 Cohere calls for 97, 1,000, 10,000 texts at <= 96 per call (K13)", [math.ceil(n / 96) for n in (97, 1000, 10000)], [2, 11, 105])
check("§11 10,000 chunks x 250 tokens; cost at $0.12 per 1M (UNVERIFIED price) (K13)", [10000 * 250, round(10000 * 250 * 0.12 / 1e6, 2)],
      [2500000, 0.30], T3)
check("§11 bytes per vector at 1,536 numbers: float32, int8, binary (K13)", [1536 * 4, 1536, 1536 // 8], [6144, 1536, 192])
check("§11 2,000,000 vectors: GB at float32 1536, int8 1536, binary 1536, float32 256 (K13)",
      [2e6 * 1536 * 4 / 1e9, 2e6 * 1536 / 1e9, 2e6 * 1536 / 8 / 1e9, 2e6 * 256 * 4 / 1e9], [12.288, 3.072, 0.384, 2.048], T3)

PACK = WS / "study" / "llmops" / "replay" / "P4_cohere_pack.json"
if PACK.exists():
    pack = json.loads(PACK.read_text(encoding="utf-8"))
    print("   recorded pack found:", PACK.relative_to(WS), "| keys:", sorted(pack)[:8])
    skip("§11 Cohere column", "a pack exists, but the reader for it is written together with the LLMOps notebook")
else:
    skip("§11 Cohere column (dimension, raw lengths, search_query vs search_document, Hit@4)",
         f"no recorded pack at {PACK.relative_to(WS)}: the LLMOps notebook is not built yet, so the lesson's Cohere column stays empty")
''')

# =====================================================================================================================
md(r"""
## 12 · The one-line checks, run on the v0 index

**What this verifies** (lesson step 12). The lesson's assert list, run against MiniLM on the 97 chunks. Each one is a check here instead of an `assert`, so you see its result.
""")
code(r'''
if MODELS_OK:
    index_meta = {"model_id": "sentence-transformers/all-MiniLM-L6-v2"}
    query_model_id = "sentence-transformers/all-MiniLM-L6-v2"
    scores = E6 @ Q6["D-002"]
    check("§12 unit length", bool(np.allclose(np.linalg.norm(E6, axis=1), 1, atol=1e-3)), True)
    check("§12 same model id on both sides", index_meta["model_id"] == query_model_id, True)
    check("§12 one score per chunk", scores.shape == (len(chunks),), True)
    check("§12 a chunk finds itself first (all 97)", all(int(np.argmax(E6 @ E6[i])) == i for i in range(N)), True)
    check("§12 nothing cut: longest chunk <= max_seq_length", max(ntok) <= m6.max_seq_length, True)
    check("§12 the dimension asked for", E6.shape[1], 384)
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
