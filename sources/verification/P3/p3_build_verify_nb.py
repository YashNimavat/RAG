"""Build study/notebooks/P3_bm25_verify.ipynb: the "verify it yourself" notebook for P3 (keyword search, TF-IDF, BM25).

The notebook rebuilds every number and chart of the P3 lesson (study/lessons/P3_bm25.html) from code, one section per
lesson step (1-13), and compares each value with the lesson's value in a `check(...)` line. The expected values are
copied from sources/verification/P3/P3_FACTS.md and sources/verification/R1/R1_FACTS.md; the code paths are the ones of
p3_measure.py, p3_kit_measure.py (91 windows, toys) and r1_measure.py (97 chunks, MiniLM), so the numbers come out
identical. No Groq or Cohere call, no .env read, no network (MiniLM loads from the local cache, offline).

Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P3/p3_build_verify_nb.py
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P3/p3_verify_nb_run.py      # executes it, saves outputs
"""
from pathlib import Path
from textwrap import dedent

import nbformat as nbf

WS = Path(__file__).resolve().parents[3]                      # rag_learning/
OUT = WS / "study" / "notebooks" / "P3_bm25_verify.ipynb"

CELLS = []


def md(s):
    CELLS.append(nbf.v4.new_markdown_cell(dedent(s).strip()))


def code(s):
    CELLS.append(nbf.v4.new_code_cell(dedent(s).strip()))


# =====================================================================================================================
md(r"""
# P3 · Verify it yourself: keyword search, TF-IDF and BM25

**What this is:** a notebook that rebuilds every number and chart of the P3 lesson from real code, so you can see each one being made and change the inputs.
**What this is not:** the lab (`labs/P3_bm25_lab.ipynb`, where you write the code yourself) or the quiz. Do the lab first if you have not: this notebook shows finished code.

**How to use it.** Run all cells from the top (VS Code: *Run All*). The sections are numbered like the lesson, 1 to 13. Each one has:
- a short note on what it verifies;
- a code cell that **computes** the values;
- `check(...)` lines: `PASS` means the code produced the number the lesson shows, `FAIL` means it did not;
- an interactive chart where the lesson has a chart or a table worth seeing. Hover for values; some charts have a slider underneath.

The last cell counts the checks.

**Two chunk sets, never mixed.**
- **91 windows**: the climate PDF cut into plain 1,000-character slices that overlap by 200 characters (P3).
- **97 chunks**: the course index (the 07 recursive chunker, per page, 1000/200), as R1 builds it.

**Where the expected values come from.** `sources/verification/P3/P3_FACTS.md` (sections S and K) and `sources/verification/R1/R1_FACTS.md`. No API is called; MiniLM, the local embedding model, loads from the cache on this computer.
""")

code(r'''
# Setup: imports, paths and the shared helpers. Run this cell first.
import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")          # MiniLM may load from the local cache only: no network
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import collections
import hashlib
import importlib.metadata as md
import json
import math
import re
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pymupdf                                        # pinned 1.26.7
from rank_bm25 import BM25Okapi
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
PDF = WS.parent / "upstream" / "RAG_Techniques" / "data" / "Understanding_Climate_Change.pdf"
print("workspace:", WS)
print("python", sys.version.split()[0], {p: md.version(p) for p in ("rank-bm25", "numpy", "pymupdf", "plotly")})

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
    return ok


def skip(name, reason):
    SKIPPED.append((name, reason))
    print(f"SKIPPED  {name}: {reason}")


# ---------------------------------------------------------------- chart style (light surface, fixed colour order)
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"    # categorical slots 1-3, always in this order
pio.templates["p3"] = go.layout.Template(layout=dict(
    font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', size=13, color=INK2),
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, colorway=[BLUE, ORANGE, AQUA],
    xaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    yaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=INK2)),
    title=dict(x=0, xanchor="left", font=dict(size=15, color=INK)),
    margin=dict(l=70, r=30, t=90, b=60), hoverlabel=dict(font_size=12)))
pio.templates.default = "p3"


def r5(xs):                                           # round for chart data: smaller outputs
    return [round(float(x), 5) for x in xs]


# ---------------------------------------------------------------- tokenizers and BM25 helpers (as in p3_measure.py)
def tok_split(text):                       # the repo's tokenizer (fusion_retrieval.ipynb cells 14 and 17)
    return text.split()


def tok_lower_split(text):                 # case only
    return text.lower().split()


def tok_word(text):                        # case + punctuation, the common \w+ regex
    return re.findall(r"\w+", text.lower())


NORM_RE = re.compile(r"[a-z0-9]+(?:[.,][0-9]+)*")


def tok_norm(text):                        # the course tokenizer: lower-case, letters and digits, keeps 1.5 whole
    return NORM_RE.findall(text.lower())


def fold(t):                               # TOY plural folding. Not Porter, not Snowball.
    return t[:-1] if len(t) > 3 and t.endswith("s") and not t.endswith("ss") else t


def tok_norm_fold(text):
    return [fold(t) for t in tok_norm(text)]


TOKENIZERS = {"split": tok_split, "lower+split": tok_lower_split, r"lower+\w+": tok_word,
              "norm": tok_norm, "norm+fold(toy)": tok_norm_fold}


def bm25_numpy(corpus_tokens, query_tokens, k1=1.5, b=0.75, epsilon=0.25):
    """Reference NumPy BM25 that matches rank_bm25 0.2.2 BM25Okapi (P3 S2, S10)."""
    vocab = {w: j for j, w in enumerate(sorted({w for d in corpus_tokens for w in d}))}
    N, V = len(corpus_tokens), len(vocab)
    tf = np.zeros((N, V))
    for i, d in enumerate(corpus_tokens):
        for w in d:
            tf[i, vocab[w]] += 1
    dl = tf.sum(axis=1)
    avgdl = dl.mean()
    n = (tf > 0).sum(axis=0)
    idf = np.log(N - n + 0.5) - np.log(n + 0.5)
    eps = epsilon * idf.mean()                 # floor = epsilon x mean idf over ALL terms (before flooring)
    idf = np.where(idf < 0, eps, idf)          # strictly negative only: idf == 0 stays 0
    K = k1 * (1 - b + b * dl / avgdl)
    scores = np.zeros(N)
    for q in query_tokens:                     # a repeated query term is added again
        j = vocab.get(q)
        if j is None:
            continue
        f = tf[:, j]
        scores += idf[j] * f * (k1 + 1) / (f + K)
    return scores


def tf_part(f, dl_over_avgdl, k1=1.5, b=0.75):
    return f * (k1 + 1) / (f + k1 * (1 - b + b * dl_over_avgdl))


def ranked(scores):                        # positions best first; ties by the lower index
    return sorted(range(len(scores)), key=lambda i: (-scores[i], i))


# ---------------------------------------------------------------- the corpus and the 91 windows
check("environment: rank-bm25 version", md.version("rank-bm25"), "0.2.2")
check("environment: pymupdf version (pinned)", md.version("pymupdf"), "1.26.7")
pdf_bytes = PDF.read_bytes()
check("corpus: PDF sha256", hashlib.sha256(pdf_bytes).hexdigest(),
      "1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669")
pages = [p.get_text() for p in pymupdf.open(PDF)]
full = "\n".join(pages)                    # the same extraction as the acceptance suite, P1 and P3
check("corpus: pages, characters", [len(pages), len(full)], [33, 72593])
SIZE, OVERLAP = 1000, 200
W = [full[i:min(i + SIZE, len(full))] for i in range(0, len(full), SIZE - OVERLAP)]
C91 = [tok_norm(w) for w in W]
BM91 = BM25Okapi(C91)
DF91 = collections.Counter(t for c in C91 for t in set(c))
FLOOR91 = BM91.epsilon * BM91.average_idf
check("91 windows: count", len(W), 91)

# ---------------------------------------------------------------- the 97 chunks, built exactly as r1_measure.py S1
sys.path.insert(0, str(WS / "sources" / "verification" / "corrections"))
import contracts_check as cc                          # noqa: E402  (06 recipe, 07 chunker loader, reference rel / ce)

md06 = (WS / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
md07 = (WS / "07_SAMPLE_LESSON.md").read_text(encoding="utf-8")
cc.RECIPE_06 = cc.code_blocks(cc.section(md06, "5.3 Corpus freezing"), "python")[0]
manifest06 = cc.build_manifest("climate", pages, pdf_bytes, {**cc.PARSER, "version": pymupdf.VersionBind},
                               cc.CLEANING_NONE)
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
check("97 chunks: chunks.jsonl sha256 (= the C2 lab file)", SHA_JL,
      "d4108b8936093394c6eb50d4c22e8d4013d9a048fb38d5769281af4aadb3011b")
IDS = [c["chunk_id"] for c in chunks]
ROW = {d: i for i, d in enumerate(IDS)}
PAGE = {c["chunk_id"]: c["page_segments"][0]["page"] for c in chunks}
SEQ = {c["chunk_id"]: c["seq"] for c in chunks}
BM97 = BM25Okapi([tok_norm(c["text"]) for c in chunks])
BM97S = BM25Okapi([tok_split(c["text"]) for c in chunks])
check("97 chunks: BM25 tok_norm avgdl, vocabulary", [round(BM97.avgdl, 2), len(BM97.idf)], [111.23, 1769])
check("97 chunks: BM25 split() avgdl, vocabulary", [round(BM97S.avgdl, 2), len(BM97S.idf)], [109.49, 2630])

# the 10 draft seeds of 06 §6.7 (llm-draft: draft-seed observations, never evaluation results)
SEEDS = [json.loads(line) for line in cc.code_blocks(cc.section(md06, "6.7 Draft seed"), "jsonl")[0].splitlines()
         if line.strip()]
for s in SEEDS:
    s["G"] = [[[("climate", starts[seg["page"] - 1] + seg["char_start"], starts[seg["page"] - 1] + seg["char_end"])
                for seg in alt["segments"]] for alt in g["alternatives"]] for g in s["evidence_groups"]]
ANS = [s for s in SEEDS if s["answerable"]]
TEXTS = {"climate": "\n".join(pages)}


def order(scores):
    """ids best first; ties broken by the smaller id. `scores` is a dict id -> float."""
    return sorted(scores, key=lambda d: (-scores[d], d))


def top_list(scores, n, positive_only=False):
    ids = [d for d in order(scores) if (scores[d] > 0 or not positive_only)][:n]
    return {d: scores[d] for d in ids}


def rel_id(d, s):
    c = chunks[ROW[d]]
    return cc.rel(("climate", c["char_start"], c["char_end"]), s["G"], TEXTS)


def ce_ids(ids, s):
    return cc.ce(s["G"], [("climate", chunks[ROW[d]]["char_start"], chunks[ROW[d]]["char_end"]) for d in ids], TEXTS)


def first_rel(ranking, s):
    return next((r for r, d in enumerate(ranking, 1) if rel_id(d, s)), None)


print(f"\nsetup done in {time.time() - T0:.1f} s: {len(W)} windows, {len(chunks)} chunks, {len(SEEDS)} draft seeds")
''')

# =====================================================================================================================
md(r"""
## 1 · Why keyword search exists: the chunk that names the word can still lose

**What this verifies** (lesson §1). Five hand-picked queries that each contain an exact term, on the **97 chunks**. For each retriever, the rank of the first chunk that contains the term:
- dense search with MiniLM (search by meaning), recomputed here;
- BM25 with the course tokenizer `tok_norm`;
- BM25 with the repo's `split()`.

A demonstration of the mechanism, not an evaluation. If MiniLM cannot load offline, the dense part is marked SKIPPED, never faked.
""")
code(r'''
DEMO = [("IPCC", "IPCC"), ("What does BECCS stand for?", "BECCS"), ("methane CH4", "CH4"),
        ("Kyoto Protocol 1997", "1997"), ("limit warming to 1.5 degrees", "1.5")]
DENSE_OK, MODEL, V97 = False, None, None
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
warnings.filterwarnings("ignore", message="IProgress not found")   # tqdm's notebook-widget notice (no ipywidgets here)
try:
    import transformers
    transformers.utils.logging.disable_progress_bar()
    from sentence_transformers import SentenceTransformer
    MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
    DENSE_OK = True
except Exception as e:  # noqa: BLE001
    skip("§1 dense ranks (and every other MiniLM number)", f"MiniLM could not load offline: {type(e).__name__}: {str(e)[:160]}")


def embed(texts):                                     # as r1_measure.py: normalised, float32
    return MODEL.encode(list(texts), normalize_embeddings=True, convert_to_numpy=True,
                        show_progress_bar=False).astype(np.float32)


if DENSE_OK:
    V97 = embed([c["text"] for c in chunks])


def dense_scores(q):
    s = V97 @ embed([q])[0]
    return {IDS[i]: float(s[i]) for i in range(len(IDS))}


def bm25_scores(q, bm=BM97, tok=tok_norm):
    s = bm.get_scores(tok(q))
    return {IDS[i]: float(s[i]) for i in range(len(IDS))}


def first_hit(ranking, targets):
    return next((r for r, d in enumerate(ranking, 1) if d in targets), None)


RANKS = {"dense": [], "bm25": [], "split": []}
for q, target in DEMO:
    tgt = {c["chunk_id"] for c in chunks if target in c["text"]}
    if DENSE_OK:
        RANKS["dense"].append(first_hit(order(dense_scores(q)), tgt))          # dense ranks every chunk
    RANKS["bm25"].append(first_hit(order(top_list(bm25_scores(q), len(IDS), True)), tgt))   # BM25: score > 0 only
    RANKS["split"].append(first_hit(order(top_list(bm25_scores(q, BM97S, tok_split), len(IDS), True)), tgt))
    print(f"{q!r:32s} target {target!r:7s} in chunk seq {sorted(SEQ[d] for d in tgt)}")

show = lambda r: "not found" if r is None else str(r)
print(f"\n{'query':32s} {'dense':>6s} {'BM25':>6s} {'split()':>10s}")
for j, (q, _) in enumerate(DEMO):
    print(f"{q!r:32s} {show(RANKS['dense'][j]) if DENSE_OK else 'SKIP':>6s} {show(RANKS['bm25'][j]):>6s} "
          f"{show(RANKS['split'][j]):>10s}")
print()
if DENSE_OK:
    check("§1 dense (MiniLM) ranks, 97 chunks", RANKS["dense"], [3, 4, 4, 1, 4])
check("§1 BM25 tok_norm ranks, 97 chunks", RANKS["bm25"], [1, 1, 1, 1, 1])
check("§1 BM25 split() ranks, 97 chunks (None = not found)", RANKS["split"], [None, None, 2, 1, 1])

NF = 6                                                # x position used for "not found"
fig = go.Figure()
for key, label, colour, dy in (("dense", "dense (MiniLM)", ORANGE, -0.2), ("bm25", "BM25, tok_norm", BLUE, 0.0),
                               ("split", "BM25, split()", AQUA, 0.2)):
    if not RANKS[key]:
        continue
    fig.add_scatter(x=[NF if r is None else r for r in RANKS[key]], y=[j + dy for j in range(len(DEMO))],
                    mode="markers", name=label,
                    marker=dict(size=13, color=colour, line=dict(width=2, color=SURFACE)),
                    customdata=[[q, show(r)] for (q, _), r in zip(DEMO, RANKS[key])],
                    hovertemplate=label + "<br>%{customdata[0]}<br>rank of the chunk with the term: %{customdata[1]}"
                                  "<extra></extra>")
fig.update_layout(title="§1 · Where the chunk that names the term lands (97 chunks; rank 1 = top)", height=380,
                  xaxis=dict(title="rank (lower is better)", tickvals=[1, 2, 3, 4, 5, NF],
                             ticktext=["1", "2", "3", "4", "5", "not found"], range=[0.5, NF + 0.5]),
                  yaxis=dict(tickvals=list(range(len(DEMO))), ticktext=[f'"{q}"' for q, _ in DEMO],
                             autorange="reversed", showgrid=False, zeroline=False))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 2 · Meaning vs words: a dense vector and a sparse one

**What this verifies** (lesson §2). Two sizes the lesson quotes:
- MiniLM turns a text into **384** numbers (a dense vector: every slot holds a number);
- keyword search on the 91 windows has **1,870** distinct `tok_norm` tokens, so written as a vector, a window gets 1,870 slots, almost all of them 0 (a sparse vector).

**The chart** counts, for each real window, how many of its 1,870 slots are not 0.
""")
code(r'''
if DENSE_OK:
    check("§2 MiniLM vector length (dimensions)", int(V97.shape[1]), 384)
    v = V97[0]
    print(f"   chunk seq 0 as a dense vector: {v.size} slots, {int((v != 0).sum())} of them not 0")
else:
    skip("§2 MiniLM dimensions", "MiniLM did not load (see §1)")
check("§2 distinct tok_norm tokens on the 91 windows (= sparse vector length)", len(BM91.idf), 1870)
check("§2 the same count from the document frequencies", len(DF91), 1870)

used = [len(set(c)) for c in C91]
print(f"   slots that are not 0 per window: min {min(used)}, median {int(np.median(used))}, max {max(used)} "
      f"of 1,870 (median {100 * np.median(used) / 1870:.1f}%)")
fig = go.Figure(go.Histogram(x=used, nbinsx=25, marker=dict(color=BLUE, line=dict(width=2, color=SURFACE)),
                             hovertemplate="%{x} non-zero slots: %{y} windows<extra></extra>"))
fig.update_layout(title="§2 · A window as a sparse vector: non-zero slots out of 1,870 (91 windows)", height=340,
                  xaxis=dict(title="distinct tokens in the window (= slots that are not 0)"),
                  yaxis=dict(title="windows"), showlegend=False, bargap=0.05)
fig.show()
''')

# =====================================================================================================================
md(r"""
## 3 · The index: word → the chunks that contain it

**What this verifies** (lesson §3), on the six-document **toy** collection of P3:
- the index itself: for every word, df (how many documents contain it) and idf (its weight);
- vocabulary 44, mean idf 1.089767 (computed before any flooring), floor 0.272442;
- the question "bpa regulation 2019" scores d0 1.938496, d2 1.28372, d1 0.587787, and the others 0.

**The charts.** The heatmap is the index: one row per document, one column per word; hover a cell for f, df and idf. The bar chart scores a question; the buttons switch questions. A document that shares no word with the question stays at 0.
""")
code(r'''
TOY = [
    "BPA regulation (2019): the EU limits BPA in food-contact plastics.",
    "Climate policy and plastics: a review of chemical safety regulation.",
    "The 2019 BPA ban covers baby bottles; BPA, BPS and BPF are bisphenols.",
    "Climate change raises sea levels and flood risks for coastal cities.",
    "Greenhouse gas emissions and climate targets under the Paris Agreement.",
    "Plastics manufacturing adds climate emissions.",
]
TT = [tok_norm(d) for d in TOY]
toy = BM25Okapi(TT)
toy_df = collections.Counter(w for t in TT for w in set(t))
toy_raw = {w: math.log(len(TT) - n + 0.5) - math.log(n + 0.5) for w, n in toy_df.items()}
words = sorted(toy_df, key=lambda w: (-toy_df[w], w))
print("word          df  raw idf  idf used")
for w in words:
    print(f"{w:12s} {toy_df[w]:3d} {toy_raw[w]:+8.4f} {toy.idf[w]:9.6f}")
print()
check("§3 toy document lengths, avgdl", [[len(t) for t in TT], toy.avgdl], [[11, 10, 13, 11, 10, 5], 10.0])
check("§3 toy vocabulary", len(toy.idf), 44)
check("§3 toy mean idf (before the floor)", toy.average_idf, 1.089767, T6)
check("§3 toy floor = 0.25 × mean idf", 0.25 * toy.average_idf, 0.272442, T6)
q3 = tok_norm("bpa regulation 2019")
s3 = toy.get_scores(q3)
check("§3 'bpa regulation 2019' scores d0..d5", s3, [1.938496, 0.587787, 1.28372, 0, 0, 0], T6)
check("§3 ranking: d0, d2, d1 (the rest score 0)", [i for i in ranked(list(s3)) if s3[i] > 0], [0, 2, 1])
check("§3 the NumPy reference gives the same scores", float(np.abs(s3 - bm25_numpy(TT, q3)).max()), 0.0, 1e-12)

z = [[t.count(w) for w in words] for t in TT]
hover = [[f"d{i} · {w}<br>f (mentions here) = {t.count(w)}<br>df = {toy_df[w]} of 6 · idf used = {toy.idf[w]:.4f}"
          for w in words] for i, t in enumerate(TT)]
fig = go.Figure(go.Heatmap(z=z, x=words, y=[f"d{i}" for i in range(6)], text=hover, hoverinfo="text",
                           colorscale=[[0, SURFACE], [0.5, "#86b6ef"], [1, "#184f95"]], xgap=2, ygap=2,
                           colorbar=dict(title="f", tickvals=[0, 1, 2])))
fig.update_layout(title="§3 · The index of the toy collection: mentions of each word in each document", height=360,
                  xaxis=dict(tickangle=-60, showgrid=False), yaxis=dict(autorange="reversed", showgrid=False))
fig.show()

QS = ["bpa regulation 2019", "climate", "eu", "plastics", "bpa bpa"]
bars = {q: r5(toy.get_scores(tok_norm(q))) for q in QS}
fig = go.Figure(go.Bar(x=[f"d{i}" for i in range(6)], y=bars[QS[0]], marker=dict(color=BLUE),
                       text=[f"{v:.4f}" for v in bars[QS[0]]], textposition="outside",
                       hovertemplate="%{x}: score %{y:.6f}<extra></extra>"))
fig.update_layout(title="§3 · BM25 score of each toy document for one question", height=380,
                  yaxis=dict(title="BM25 score", range=[min(0, min(min(v) for v in bars.values())) - 0.1,
                                                         max(max(v) for v in bars.values()) * 1.25]),
                  updatemenus=[dict(type="buttons", direction="right", x=0, y=1.13, xanchor="left", showactive=True,
                                    buttons=[dict(label=q, method="restyle",
                                                  args=[{"y": [bars[q]], "text": [[f"{v:.4f}" for v in bars[q]]]}])
                                             for q in QS])])
fig.show()
''')

# =====================================================================================================================
md(r"""
## 4 · Three counts: tf, df and idf (and the one piece of maths, ln)

**What this verifies** (lesson §4):
- the toy table: in d0, **eu** has tf 1 and df 1, **bpa** tf 2 and df 2, **climate** tf 0 and df 4;
- the BECCS question on the **91 windows**: `what`, `does`, `stand` have df 0 (not in the index), `beccs` df 2, `for` df 80;
- the ln facts the lesson uses: ln 1 = 0; ln of the ipcc fraction (about 60.3) is about 4.10; ln of the `for` fraction (about 0.143) is about −1.95; ln 10 ≈ 2.3 and ln 100 ≈ 4.6.
""")
code(r'''
d0 = TT[0]
check("§4 toy d0: tf and df of eu, bpa, climate",
      [[d0.count("eu"), toy_df["eu"]], [d0.count("bpa"), toy_df["bpa"]], [d0.count("climate"), toy_df["climate"]]],
      [[1, 1], [2, 2], [0, 4]])
qB = tok_norm("What does BECCS stand for?")
check("§4 BECCS question tokens (tok_norm)", qB, ["what", "does", "beccs", "stand", "for"])
check("§4 df on the 91 windows: what, does, beccs, stand, for", [DF91[t] for t in qB], [0, 0, 2, 0, 80])
check("§4 tokens with df 0 are not in the index at all", [t in BM91.idf for t in qB], [False, False, True, False, True])

N = len(W)
frac = lambda n: (N - n + 0.5) / (n + 0.5)
check("§4 ln(1) = 0", math.log(1), 0.0)
check("§4 the fraction for a word in 1 of 91 windows ≈ 60.3; its ln ≈ 4.10", [frac(1), math.log(frac(1))], [60.3, 4.10], 0.05)
check("§4 the fraction for a word in 80 of 91 windows ≈ 0.143; its ln ≈ −1.95", [frac(80), math.log(frac(80))],
      [0.143, -1.95], 0.005)
check("§4 ln 10 ≈ 2.3, ln 100 ≈ 4.6", [math.log(10), math.log(100)], [2.3, 4.6], 0.05)

fig = go.Figure(go.Bar(x=qB, y=[DF91[t] for t in qB], marker=dict(color=BLUE),
                       text=[str(DF91[t]) for t in qB], textposition="outside",
                       hovertemplate="%{x}: in %{y} of 91 windows<extra></extra>"))
fig.update_layout(title="§4 · Document frequency of each token of the BECCS question (91 windows)", height=340,
                  yaxis=dict(title="windows containing the token (df)", range=[0, 95]), showlegend=False)
fig.show()
''')

# =====================================================================================================================
md(r"""
## 5 · TF-IDF multiplies the counts, and over-rewards repeats

**What this verifies** (lesson §5), on the **toy** "flip" collection of `p3_kit_measure.py` (K4): six documents of 8 tokens each, question "bpa ban". Document **x** says each word once; document **y** says "BPA" six times and never "ban".
- textbook TF-IDF: x 2.8904, y 6.5917, so **y** wins;
- BM25: x 1.8871, y 1.1756, so **x** wins.

It also rebuilds the "which TF-IDF?" note: TF-IDF against BM25 for 1 to 16 mentions (P3 S7), and scikit-learn's idf for `bpa`, 1.847298.

**The chart** shows the two methods side by side, each with its own scale (two small charts, not one chart with two axes). What matters is the order inside each one.
""")
code(r'''
STUFF = [
    "The BPA ban covers baby bottles and cans.",          # x: matches both words once
    "BPA BPA BPA BPA BPA BPA in plastics.",                # y: repeats one word six times
    "Sea levels rise and coastal cities flood often.",
    "Greenhouse gas emissions warm the planet every year.",
    "Solar farms on lakes cut water loss too.",
    "Climate policy needs clear targets and fair rules.",
]
ST = [tok_norm(d) for d in STUFF]
sq = tok_norm("bpa ban")
dfs = collections.Counter(t for d in ST for t in set(d))
tfidf = [sum(d.count(t) * math.log(len(ST) / dfs[t]) for t in sq if dfs[t]) for d in ST]
bm_st = BM25Okapi(ST)
bms = bm_st.get_scores(sq)
check("§5 toy: every document has 8 tokens", [len(t) for t in ST], [8] * 6)
check("§5 textbook TF-IDF: x, y", tfidf[:2], [2.8904, 6.5917], T4)
check("§5 BM25: x, y", bms[:2], [1.8871, 1.1756], T4)
check("§5 who ranks first: TF-IDF y (doc 1), BM25 x (doc 0)", [ranked(tfidf)[0], ranked(list(bms))[0]], [1, 0])
check("§5 idf bpa, ban; BM25 tf part at f = 6", [bm_st.idf["bpa"], bm_st.idf["ban"], tf_part(6, 1.0)],
      [0.587787, 1.299283, 2.0], T6)

raw_bpa = math.log(4.5 / 2.5)                         # toy of §3: bpa in 2 of 6 documents
s7 = {f: (f * math.log(6 / 2), raw_bpa * tf_part(f, 1.0)) for f in (1, 2, 4, 8, 16)}
for f, (a, b_) in s7.items():
    print(f"   f = {f:2d}: TF-IDF {a:8.4f}   BM25 {b_:.4f}")
check("§5 TF-IDF f × ln 3 at f = 1, 2, 4, 8, 16", [v[0] for v in s7.values()],
      [1.0986, 2.1972, 4.3944, 8.7889, 17.5778], T4)
check("§5 BM25 for bpa at f = 1, 2, 4, 8, 16", [v[1] for v in s7.values()], [0.5878, 0.8397, 1.0687, 1.2374, 1.3435], T4)
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    vec = TfidfVectorizer().fit(TOY)
    check("§5 scikit-learn idf_ for bpa = ln(7/3) + 1", vec.idf_[vec.vocabulary_["bpa"]], 1.847298, T6)
    check("§5 scikit-learn's analyzer drops 1.5 from 'limit warming to 1.5 degrees'",
          vec.build_analyzer()("limit warming to 1.5 degrees"), ["limit", "warming", "to", "degrees"])
except ImportError as e:
    skip("§5 scikit-learn checks", f"scikit-learn not installed ({e})")

fig = make_subplots(rows=1, cols=2, subplot_titles=("Textbook TF-IDF", "BM25 (rank_bm25)"), horizontal_spacing=0.12)
for col, vals in ((1, tfidf[:2]), (2, list(bms[:2]))):
    fig.add_bar(x=["x: bpa once, ban once", "y: bpa six times"], y=r5(vals), row=1, col=col, showlegend=False,
                marker=dict(color=[BLUE, ORANGE], line=dict(width=2, color=SURFACE)),
                text=[f"{v:.4f}" for v in vals], textposition="outside", hovertemplate="%{x}: %{y:.4f}<extra></extra>")
fig.update_yaxes(title_text="score", row=1, col=1, range=[0, 7.5])
fig.update_yaxes(range=[0, 2.3], row=1, col=2)
fig.update_layout(title="§5 · Question 'bpa ban' (toy): repetition wins under TF-IDF, coverage wins under BM25", height=380)
fig.show()
''')

# =====================================================================================================================
md(r"""
## 6 · BM25's two brakes (k1 and b), and one score by hand

**What this verifies** (lesson §6):
- **Brake 1, k1:** the tf part at average length for f = 1, 2, 3, 5, 10, 100, 1000 is 1, 1.4286, 1.6667, 1.9231, 2.1739, 2.4631, 2.4963 (ceiling k1 + 1 = 2.5); the k1 table of P3 S5;
- **Brake 2, b:** the length table for b = 0, 0.375, 0.75, 1 at dl/avgdl = 0.5, 1, 2 (P3 S5);
- **one score by hand** for `bpa` in toy d0: idf 0.587787, K 1.6125, tf part 1.384083, score 0.813546 (rank_bm25 agrees); `bpa` in d2 0.765846;
- one mention in a 5-token vs a 20-token toy chunk: 0.829243 vs 0.495899 at b = 0.75, and 0.587787 each at b = 0;
- the question is a list: "bpa bpa" scores 1.627091; and k1 = 0 gives NaN.

**The charts.** Move the **k1** slider: the BM25 curve flattens toward the dashed ceiling, while TF-IDF keeps climbing. The green dots are real: every window that contains "for", at its own length. Move the **b** slider: one mention's tf part against chunk length; the dots are the 91 real windows.
""")
code(r'''
F_LIST = (1, 2, 3, 5, 10, 100, 1000)
check("§6 tf part at dl = avgdl, f = 1, 2, 3, 5, 10, 100, 1000", [tf_part(f, 1.0) for f in F_LIST],
      [1, 1.4286, 1.6667, 1.9231, 2.1739, 2.4631, 2.4963], T4)
check("§6 the tf part never passes k1 + 1 (f = 10^6)", tf_part(10**6, 1.0) < 2.5, True)
check("§6 k1 = 0, 0.75, 1.5, 3.0 at f = 1, 2, 5",
      [[tf_part(f, 1.0, k1=k) for f in (1, 2, 5)] for k in (0.0, 0.75, 1.5, 3.0)],
      [[1, 1, 1], [1, 1.2727, 1.5217], [1, 1.4286, 1.9231], [1, 1.6, 2.5]], T4)
# the same limits through rank_bm25 itself: a padded synthetic document, all documents 2000 tokens long
pad = lambda fq, length: ["x"] * fq + ["pad"] * (length - fq)
lib_ratio = []
for fq in (1, 10, 100, 1000):
    m = BM25Okapi([pad(fq, 2000), ["y"] * 2000, ["z"] * 2000])
    lib_ratio.append(m.get_scores(["x"])[0] / m.idf["x"])
check("§6 rank_bm25 score / idf at f = 1, 10, 100, 1000", lib_ratio, [1.0, 2.173913, 2.463054, 2.496256], T6)

B_LIST, R_LIST = (0.0, 0.375, 0.75, 1.0), (0.5, 1.0, 2.0)
table = [[tf_part(1, r, b=bb) for r in R_LIST] for bb in B_LIST]
print("   one mention, k1 = 1.5    half as long  average  twice as long")
for bb, row in zip(B_LIST, table):
    print(f"   b = {bb:<5}               " + "   ".join(f"{v:8.4f}" for v in row))
check("§6 length table, rows b = 0, 0.375, 0.75, 1; columns dl/avgdl = 0.5, 1, 2", table,
      [[1.0, 1.0, 1.0], [1.1268, 1.0, 0.8163], [1.2903, 1.0, 0.6897], [1.4286, 1.0, 0.625]], T4)
check("§6 b = 0.75, dl/avgdl = 4", tf_part(1, 4.0), 0.4255, T4)

# one score by hand: bpa in d0
N_, n_, f_, dl_, avgdl_, k1, b = 6, toy_df["bpa"], TT[0].count("bpa"), len(TT[0]), toy.avgdl, 1.5, 0.75
idf_h = math.log((N_ - n_ + 0.5) / (n_ + 0.5))
K_h = k1 * (1 - b + b * dl_ / avgdl_)
tfp_h = f_ * (k1 + 1) / (f_ + K_h)
print(f"\n   1 idf = ln(({N_} - {n_} + 0.5) / ({n_} + 0.5)) = ln({(N_ - n_ + 0.5) / (n_ + 0.5):.1f}) = {idf_h:.6f}")
print(f"   2 K = 1.5 × (1 - 0.75 + 0.75 × {dl_}/{avgdl_:g}) = {K_h:.6f}")
print(f"   3 tf part = {f_} × 2.5 / ({f_} + {K_h:.4f}) = {tfp_h:.6f}")
print(f"   4 score = {idf_h:.6f} × {tfp_h:.6f} = {idf_h * tfp_h:.6f}")
check("§6 by hand: N, n, f, dl, avgdl", [N_, n_, f_, dl_, avgdl_], [6, 2, 2, 11, 10.0])
check("§6 by hand: idf, K, tf part, score", [idf_h, K_h, tfp_h, idf_h * tfp_h], [0.587787, 1.6125, 1.384083, 0.813546], T6)
check("§6 rank_bm25 gives the same score", toy.get_scores(["bpa"])[0], 0.813546, T6)
contrib = [toy.get_scores([w])[0] for w in q3]
check("§6 'bpa regulation 2019' in d0 = 0.813546 + 0.562475 + 0.562475", [*contrib, sum(contrib)],
      [0.813546, 0.562475, 0.562475, 1.938496], T6)
check("§6 bpa in d2 (f 2, dl 13, larger K): below d0", toy.get_scores(["bpa"])[2], 0.765846, T6)

long_short = ([["x"] + [f"a{j}" for j in range(19)], ["x"] + [f"b{j}" for j in range(4)]]
              + [[f"c{i}_{j}" for j in range(15)] for i in range(4)])
ls = {bb: BM25Okapi(long_short, b=bb).get_scores(["x"])[:2] for bb in (0.75, 0.0)}
check("§6 one mention, 5-token vs 20-token chunk, b = 0.75 (short, long)", [ls[0.75][1], ls[0.75][0]],
      [0.829243, 0.495899], T6)
check("§6 the same at b = 0 (length ignored)", [ls[0.0][1], ls[0.0][0]], [0.587787, 0.587787], T6)
check("§6 the question is a list: 'bpa bpa' = 2 × 'bpa'", toy.get_scores(["bpa", "bpa"])[0], 1.627091, T6)
with warnings.catch_warnings(record=True) as wl:
    warnings.simplefilter("always")
    s_k0 = BM25Okapi(TT, k1=0.0).get_scores(["bpa"])
check("§6 k1 = 0: documents without bpa compute 0/0 = NaN", s_k0, [0.587787, math.nan, 0.587787, math.nan, math.nan, math.nan], T6)
check("§6 k1 = 0: numpy warns once", len(wl), 1)

# ---- chart: brake 1 (k1), with the real "for" counts of the 91 windows
F = list(range(0, 21))
K1S = [round(0.25 * i, 2) for i in range(1, 13)]
for_pts = [(C91[i].count("for"), len(C91[i]) / BM91.avgdl, i) for i in range(len(C91)) if "for" in C91[i]]
curve = lambda k: r5(tf_part(f, 1.0, k1=k) for f in F)
for_y = lambda k: r5(tf_part(f, r, k1=k) for f, r, _ in for_pts)
fig = go.Figure()
fig.add_scatter(x=F, y=F, name="TF-IDF: f × the one-mention value", mode="lines", line=dict(color=ORANGE, width=2))
fig.add_scatter(x=F, y=curve(1.5), name="BM25 tf part (chunk of average length)", mode="lines+markers",
                line=dict(color=BLUE, width=2), marker=dict(size=6),
                hovertemplate="f = %{x}: tf part %{y:.4f}<extra></extra>")
fig.add_scatter(x=[0, 20], y=[2.5, 2.5], name="ceiling k1 + 1", mode="lines", line=dict(color=MUTED, width=1.5, dash="dash"),
                hoverinfo="skip")
fig.add_scatter(x=[f for f, _, _ in for_pts], y=for_y(1.5), mode="markers", name='real: "for" in a window, at its own length',
                marker=dict(size=9, color=AQUA, opacity=0.75, line=dict(width=1.5, color=SURFACE)),
                customdata=[[i, f, len(C91[i])] for f, _, i in for_pts],
                hovertemplate="window %{customdata[0]}: f %{customdata[1]}, dl %{customdata[2]}<br>tf part %{y:.4f}<extra></extra>")
fig.update_layout(title="§6 · Brake 1: the tenth mention adds little (move k1)", height=520,
                  xaxis=dict(title="mentions of the word in the chunk (f)", range=[-0.3, 20.3]),
                  yaxis=dict(title="score ÷ the one-mention score", range=[0, 6]),
                  sliders=[dict(active=K1S.index(1.5), currentvalue=dict(prefix="k1 = "), pad=dict(t=50),
                                steps=[dict(method="restyle", label=f"{k:g}",
                                            args=[{"y": [curve(k), [k + 1, k + 1], for_y(k)]}, [1, 2, 3]])
                                       for k in K1S])])
fig.show()

# ---- chart: brake 2 (b), with the 91 real windows
RX = [round(0.1 + 0.05 * i, 2) for i in range(79)]                 # dl / avgdl from 0.1 to 4.0
BSL = [round(0.05 * i, 2) for i in range(21)]
win_r = [len(c) / BM91.avgdl for c in C91]
line_b = lambda bb: r5(tf_part(1, r, b=bb) for r in RX)
pts_b = lambda bb: r5(tf_part(1, r, b=bb) for r in win_r)
fig = go.Figure()
fig.add_scatter(x=RX, y=line_b(0.75), name="one mention, k1 = 1.5", mode="lines", line=dict(color=BLUE, width=2),
                hovertemplate="dl/avgdl %{x}: tf part %{y:.4f}<extra></extra>")
fig.add_scatter(x=r5(win_r), y=pts_b(0.75), name="the 91 real windows", mode="markers",
                marker=dict(size=9, color=AQUA, opacity=0.75, line=dict(width=1.5, color=SURFACE)),
                customdata=[[i, len(C91[i])] for i in range(len(C91))],
                hovertemplate="window %{customdata[0]}: dl %{customdata[1]} (x = %{x:.3f})<br>tf part %{y:.4f}<extra></extra>")
fig.update_layout(title="§6 · Brake 2: length cuts both ways (move b)", height=500,
                  xaxis=dict(title="chunk length ÷ average length (dl / avgdl)"),
                  yaxis=dict(title="tf part of one mention", range=[0, 2.6]),
                  shapes=[dict(type="line", x0=0, x1=4.1, y0=1, y1=1, line=dict(color=AXIS, width=1))],
                  sliders=[dict(active=BSL.index(0.75), currentvalue=dict(prefix="b = "), pad=dict(t=50),
                                steps=[dict(method="restyle", label=f"{bb:g}", args=[{"y": [line_b(bb), pts_b(bb)]}, [0, 1]])
                                       for bb in BSL])])
fig.show()
''')

# =====================================================================================================================
md(r"""
## 7 · Common words and the idf floor of `rank_bm25`

**What this verifies** (lesson §7), on the **91 windows**:
- idf of ipcc 4.099885 (df 1), beccs 3.577948 (df 2), emissions 0.510826 (df 34);
- climate (df 77) and for / the (df 80) have a negative raw idf, so the library uses the **floor**, 0.838237 = 0.25 × the mean idf 3.352948;
- the **valley**: a word in 28 to 45 of the 91 windows gets an idf *below* the floor, so it is worth less than the most common words;

and the toy edge cases: `plastics` (3 of 6) gets idf 0; a near-duplicate corpus has a *negative* floor, −0.281750, with scores −0.249652 and −0.301106; a two-document corpus with a shared word gives −0.080472.

**The chart.** Lines: the textbook idf, the library's raw idf, and the idf it really uses. Dots: **every word of the 91 windows** at its own df (moved sideways a little so each dot can be hovered; the height is exact). The slider moves a marker along the used idf.
""")
code(r'''
N = len(W)
raw_idf = lambda n: math.log(N - n + 0.5) - math.log(n + 0.5)
used_idf = lambda n: raw_idf(n) if raw_idf(n) >= 0 else FLOOR91
for w in ("ipcc", "beccs", "emissions", "climate", "for", "the"):
    print(f"   {w:10s} df {DF91[w]:2d}  raw {raw_idf(DF91[w]):+.6f}  used {BM91.idf[w]:.6f}")
check("§7 idf ipcc, beccs, emissions", [BM91.idf[w] for w in ("ipcc", "beccs", "emissions")],
      [4.099885, 3.577948, 0.510826], T6)
check("§7 df of climate, for, the", [DF91[w] for w in ("climate", "for", "the")], [77, 80, 80])
check("§7 climate, for, the use the floor", [BM91.idf[w] for w in ("climate", "for", "the")], [0.838237] * 3, T6)
check("§7 mean idf (before the floor), floor", [BM91.average_idf, FLOOR91], [3.352948, 0.838237], T6)
check("§7 avgdl of the 91 windows", BM91.avgdl, 129.67, 0.005)
floored = sorted([w for w, n in DF91.items() if raw_idf(n) < 0], key=lambda w: (-DF91[w], w))
check("§7 words in more than half of the windows (floored)", len(floored), 18)
valley = [n for n in range(1, N + 1) if 0 <= raw_idf(n) < FLOOR91]
check("§7 the valley: used idf below the floor for n = 28 to 45", [min(valley), max(valley), valley == list(range(28, 46))],
      [28, 45, True])
in_valley = sorted(w for w, n in DF91.items() if 28 <= n <= 45)
print(f"   {len(in_valley)} words of the 91 windows sit in the valley, e.g. {in_valley[:8]}")

# toy edge cases (P3 S6, K9)
check("§7 toy: plastics (3 of 6) gets idf 0, so it scores 0 everywhere", [toy.idf["plastics"], float(toy.get_scores(["plastics"]).max())],
      [0.0, 0.0], T6)
three = BM25Okapi([["a", "b", "c"], ["a", "b"], ["a", "b"]])
check("§7 near-duplicate corpus: mean idf, floor", [three.average_idf, three.epsilon * three.average_idf], [-1.126998, -0.281750], T6)
check("§7 near-duplicate corpus: scores for 'a'", three.get_scores(["a"]), [-0.249652, -0.301106, -0.301106], T6)
two_a = BM25Okapi([["bpa", "ban"], ["climate", "policy"]])
check("§7 two documents, word in one: idf 0, scores 0", [two_a.idf["bpa"], *two_a.get_scores(["bpa"])], [0.0, 0.0, 0.0], T6)
two_b = BM25Okapi([["bpa", "ban", "the"], ["climate", "policy", "the"]])
check("§7 two documents, a shared word: floor and both scores", [two_b.idf["the"], *two_b.get_scores(["the"])],
      [-0.080472, -0.080472, -0.080472], T6)
check("§7 an unknown word adds 0, no error", float(np.abs(toy.get_scores(["ipcc"])).max()), 0.0)

# ---- chart: idf against df, with every word of the 91 windows
ns = list(range(1, N + 1))
rng = np.random.default_rng(0)
vocab = sorted(DF91)
jit = rng.uniform(-0.35, 0.35, len(vocab))
fig = go.Figure()
fig.add_scatter(x=[round(DF91[w] + j, 3) for w, j in zip(vocab, jit)], y=r5(BM91.idf[w] for w in vocab), mode="markers",
                name=f"every word of the 91 windows ({len(vocab)})", marker=dict(size=6, color=BLUE, opacity=0.35),
                customdata=[[w, DF91[w]] for w in vocab],
                hovertemplate="<b>%{customdata[0]}</b><br>in %{customdata[1]} of 91 windows<br>idf used %{y:.4f}<extra></extra>")
fig.add_scatter(x=ns, y=r5(math.log(N / n) for n in ns), name="textbook idf ln(N/n)", mode="lines",
                line=dict(color=MUTED, width=1.5), hovertemplate="n %{x}: textbook %{y:.4f}<extra></extra>")
fig.add_scatter(x=ns, y=r5(raw_idf(n) for n in ns), name="rank_bm25 raw idf", mode="lines",
                line=dict(color=ORANGE, width=2), hovertemplate="n %{x}: raw %{y:.4f}<extra></extra>")
fig.add_scatter(x=ns, y=r5(used_idf(n) for n in ns), name="idf used (raw, or the floor if negative)", mode="lines",
                line=dict(color=BLUE, width=2.5), hovertemplate="n %{x}: used %{y:.4f}<extra></extra>")
fig.add_scatter(x=[34], y=[used_idf(34)], mode="markers", name="slider", showlegend=False,
                marker=dict(size=14, color=INK, line=dict(width=2, color=SURFACE)), hoverinfo="skip")
note = lambda n: (f"n = {n}: raw {raw_idf(n):+.4f}, used {used_idf(n):.4f}"
                  + ("  (floored)" if raw_idf(n) < 0 else "  (in the valley: below the floor)" if raw_idf(n) < FLOOR91 else ""))
marks = [("ipcc", 0, -30), ("beccs", 25, -25), ("emissions", -45, -40), ("climate", -40, -30), ("for", 30, -30)]
anns = [dict(x=0.98, y=0.97, xref="paper", yref="paper", text=note(34), showarrow=False, xanchor="right", yanchor="top",
             font=dict(color=INK, size=13), bgcolor=SURFACE)]
anns += [dict(x=DF91[w], y=BM91.idf[w], text=(w if w != "for" else "for, the"), ax=ax, ay=ay, arrowcolor=MUTED,
              font=dict(color=INK)) for w, ax, ay in marks]
anns += [dict(x=36.5, y=-0.3, text="valley: n 28 to 45", showarrow=False, font=dict(color=ORANGE))]
fig.update_layout(title="§7 · idf against document frequency on the 91 windows (move n)", height=560,
                  xaxis=dict(title="windows containing the word (n, of 91)", range=[0, 92]),
                  yaxis=dict(title="idf", range=[-3.2, 5]), annotations=anns,
                  shapes=[dict(type="rect", x0=27.5, x1=45.5, y0=0, y1=FLOOR91, fillcolor="rgba(235,104,52,0.12)",
                               line=dict(width=0), layer="below"),
                          dict(type="line", x0=0, x1=92, y0=FLOOR91, y1=FLOOR91, line=dict(color=INK2, width=1, dash="dot")),
                          dict(type="line", x0=0, x1=92, y0=0, y1=0, line=dict(color=AXIS, width=1))],
                  sliders=[dict(active=33, currentvalue=dict(prefix="n = "), pad=dict(t=50),
                                steps=[dict(method="update", label=str(n),
                                            args=[{"x": [[n]], "y": [[round(used_idf(n), 5)]]},
                                                  {"annotations[0].text": note(n)}, [4]]) for n in ns])])
fig.show()
''')

# =====================================================================================================================
md(r"""
## 8 · One question, scored word by word: "What does BECCS stand for?"

**What this verifies** (lesson §8, P3_FACTS K2), on the **91 windows**:
- 80 of 91 windows score above 0;
- the top three, split per word: window 83 = beccs 3.649768 + for 1.412504 = 5.062271; window 82 = 3.662734 + 1.217614 = 4.880348; window 16 = for alone, 1.671968 (six "for"s, close to its ceiling 2.095593);
- 78 of the 80 matching windows contain no "beccs" at all: they match on "for" alone.

**The chart** stacks what each word adds, for the top 10 windows.
""")
code(r'''
qB = tok_norm("What does BECCS stand for?")
sB = BM91.get_scores(qB)
oB = ranked(list(sB))
check("§8 windows scoring above 0", int((sB > 0).sum()), 80)
check("§8 top 5 windows", oB[:5], [83, 82, 16, 53, 45])
check("§8 top 5 scores", [sB[i] for i in oB[:5]], [5.0623, 4.8803, 1.672, 1.6156, 1.607], T4)
part = lambda t, i: float(BM91.get_scores([t])[i])
for i, exp in ((83, [124, 1.450805, 1, 3.649768, 3, 1.412504, 5.062271]),
               (82, [123, 1.442129, 1, 3.662734, 2, 1.217614, 4.880348]),
               (16, [132, 1.520212, 0, 0.0, 6, 1.671968, 1.671968])):
    dl = len(C91[i])
    K = 1.5 * (0.25 + 0.75 * dl / BM91.avgdl)
    got = [dl, K, C91[i].count("beccs"), part("beccs", i), C91[i].count("for"), part("for", i), float(sB[i])]
    print(f"   window {i}: dl {dl}, K {K:.6f} | beccs f {got[2]} -> {got[3]:.6f} | for f {got[4]} -> {got[5]:.6f} | total {got[6]:.6f}")
    check(f"§8 window {i}: dl, K, beccs f, beccs part, for f, for part, total", got, exp, T6)
check("§8 tf parts: beccs in 83, for in 83, beccs in 82, for in 82, for in 16",
      [tf_part(1, 124 / BM91.avgdl), tf_part(3, 124 / BM91.avgdl), tf_part(1, 123 / BM91.avgdl),
       tf_part(2, 123 / BM91.avgdl), tf_part(6, 132 / BM91.avgdl)],
      [1.020073, 1.685088, 1.023697, 1.452589, 1.994625], T6)
check("§8 ceiling of 'for' = idf × (k1 + 1)", BM91.idf["for"] * 2.5, 2.095593, T6)
only_for = sum(1 for i in range(len(W)) if sB[i] > 0 and "beccs" not in C91[i])
check("§8 matching windows without 'beccs' (they match on 'for' alone)", only_for, 78)

top = oB[:10]
fig = go.Figure()
for t, colour in (("beccs", BLUE), ("for", ORANGE)):
    vals = [part(t, i) for i in top]
    fig.add_bar(y=[f"window {i}" for i in top], x=r5(vals), orientation="h", name=f"{t} (idf {BM91.idf[t]:.3f})",
                marker=dict(color=colour, line=dict(width=2, color=SURFACE)),
                customdata=[[C91[i].count(t), len(C91[i])] for i in top],
                hovertemplate=t + ": f %{customdata[0]}, dl %{customdata[1]} -> adds %{x:.4f}<extra></extra>")
fig.update_layout(barmode="stack", title="§8 · 'What does BECCS stand for?': what each word adds (top 10 of 91 windows)",
                  height=440, xaxis=dict(title="BM25 score"), yaxis=dict(autorange="reversed", showgrid=False))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 9 · Tokens: a perfect formula cannot match a broken token

**What this verifies** (lesson §9), on the **91 windows** unless marked toy:
- `split()` against `tok_norm`: the BECCS question gets 0 windows above 0 against 80; "IPCC" gets 0 windows against rank 1 at 3.892792 (window 1; P3_FACTS K3);
- the vocabulary of the whole PDF: 2,630 distinct `split()` tokens against 1,769 for `tok_norm`; "emissions" has four `split()` spellings, used 22, 20, 7 and 1 times;
- when nothing matches, `np.argsort(scores)[::-1][:5]` still returns five windows: [90, 89, 88, 87, 86];
- `tok_norm("v2.10.3 ERR_CONN_RESET")` keeps the version and cuts the error code;
- the code-identifier toy (K6), and lower-casing only the question: 2.1246 → 1.2894 (toy, P3 S8);
- the five-tokenizer table of P3 S9 (rank of the target window for each query).

**The charts.** A tokenizer table for five examples (buttons): the chunk's tokens, the question's tokens, and the ones they share. Then the windows that score above 0 under each tokenizer.
""")
code(r'''
SPLIT91 = BM25Okapi([tok_split(w) for w in W])
sBs = SPLIT91.get_scores(tok_split("What does BECCS stand for?"))
sIs = SPLIT91.get_scores(tok_split("IPCC"))
sIn = BM91.get_scores(tok_norm("IPCC"))
check("§9 BECCS question, windows above 0: split() vs tok_norm", [int((sBs > 0).sum()), int((sB > 0).sum())], [0, 80])
check("§9 IPCC under split(): windows above 0", int((sIs > 0).sum()), 0)
check("§9 IPCC under tok_norm: rank-1 window and its score", [ranked(list(sIn))[0], sIn.max()], [1, 3.892792], T6)
check("§9 IPCC in window 1: df, idf, dl, K, tf part",
      [DF91["ipcc"], BM91.idf["ipcc"], len(C91[1]), 1.5 * (0.25 + 0.75 * len(C91[1]) / BM91.avgdl), tf_part(1, len(C91[1]) / BM91.avgdl)],
      [1, 4.099885, 145, 1.632998, 0.949488], T6)
check("§9 the split() tokens of the text that contain IPCC / BECCS",
      [sorted({t for t in tok_split(full) if "IPCC" in t}), sorted({t for t in tok_split(full) if "BECCS" in t})],
      [["(IPCC)"], ["(BECCS),"]])
check("§9 whole-PDF vocabulary: split() vs tok_norm", [len(set(tok_split(full))), len(set(tok_norm(full)))], [2630, 1769])
vocab5 = {name: len(set(tk(full))) for name, tk in TOKENIZERS.items()}
check("§9 whole-PDF vocabulary under the five tokenizers", list(vocab5.values()), [2630, 2276, 1767, 1769, 1617])
spell = collections.Counter(t for t in tok_split(full) if t.lower().strip('.,;:()"') == "emissions")
check("§9 split() spellings of 'emissions'", sorted(spell.items(), key=lambda kv: -kv[1]),
      [["emissions", 22], ["emissions.", 20], ["emissions,", 7], ["Emissions", 1]])
check("§9 all-zero scores: the repo's argsort still returns 5 windows", np.argsort(sIs)[::-1][:5].tolist(), [90, 89, 88, 87, 86])
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    nan_norm = (sIs - sIs.min()) / (sIs.max() - sIs.min())
check("§9 min-max without epsilon on all-zero scores: NaN for every window", int(np.isnan(nan_norm).sum()), 91)
check("§9 tok_norm on 'v2.10.3 ERR_CONN_RESET'", tok_norm("v2.10.3 ERR_CONN_RESET"), ["v2.10.3", "err", "conn", "reset"])
check("§9 the \\w+ rule does the opposite", tok_word("v2.10.3 ERR_CONN_RESET"), ["v2", "10", "3", "err_conn_reset"])

# lower-casing only the question (toy, P3 S8)
TS = [tok_split(d) for d in TOY]
check("§9 toy, split() index: 'BPA regulation 2019' vs the lower-cased question (d0)",
      [BM25Okapi(TS).get_scores("BPA regulation 2019".split())[0], BM25Okapi(TS).get_scores("bpa regulation 2019".split())[0]],
      [2.1246, 1.2894], T4)

# the five-tokenizer table (P3 S9)
QUERIES = [("IPCC", "IPCC"), ("What does BECCS stand for?", "BECCS"), ("methane CH4", "CH4"),
           ("Kyoto Protocol 1997", "1997"), ("limit warming to 1.5 degrees", "1.5")]
S9 = {}
for name, tk in TOKENIZERS.items():
    m = BM25Okapi([tk(w) for w in W])
    row = []
    for qtext, target in QUERIES:
        tw = [i for i, w in enumerate(W) if target in w]
        sc = m.get_scores(tk(qtext))
        st = max(sc[i] for i in tw)
        row.append(((1 + int((sc > st).sum())) if st > 0 else None, int((sc > 0).sum())))
    S9[name] = row
    print(f"   {name:15s} ranks {[r for r, _ in row]}  windows > 0 {[n for _, n in row]}")
check("§9 split(): target ranks (91 windows)", [r for r, _ in S9["split"]], [None, None, 3, 1, 1])
check("§9 split(): windows above 0", [n for _, n in S9["split"]], [0, 0, 3, 5, 87])
check("§9 tok_norm: target ranks", [r for r, _ in S9["norm"]], [1, 1, 1, 1, 1])
check("§9 tok_norm: windows above 0", [n for _, n in S9["norm"]], [1, 80, 5, 5, 87])
check("§9 lower+split ranks; lower+\\w+ ranks", [[r for r, _ in S9["lower+split"]], [r for r, _ in S9[r"lower+\w+"]]],
      [[None, None, 3, 1, 1], [1, 1, 1, 1, 1]])

# ---- the lesson playground's code-aware rule (tokCode; the same rule as the fit-check tool's --tokenizer code)
CODE_RUN = re.compile(r"[A-Za-z0-9_]+(?:[.,][0-9]+)*")
CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def tok_code(text):                          # split at _ and at case changes, keep the whole name; 1.5 and v2.10.3 stay whole
    out = []
    for run in CODE_RUN.findall(text):
        parts = [w.lower() for piece in re.split(r"_+", run) for w in CAMEL.split(piece) if w]
        out += parts + ([run.lower()] if len(parts) > 1 else [])
    return out


# ---- chart 1: tokenizer table with buttons
EX = [("BECCS", "bioenergy with carbon capture and storage (BECCS), direct air capture", "What does BECCS stand for?"),
      ("IPCC in brackets", "The Intergovernmental Panel on Climate Change (IPCC) has documented", "IPCC"),
      ("Different wording", "the display turns off", "my screen goes dark"),
      ("Version and error code", "Upgrade to v2.10.3 if you see ERR_CONN_RESET.", "v2.10.3 ERR_CONN_RESET"),
      ("Function names", "getUserId(token) -> int", "user id")]
TKS = [("split()", tok_split), ("tok_norm", tok_norm), ("code-aware (as in the lesson playground)", tok_code)]
fig = go.Figure()
for j, (label, text, question) in enumerate(EX):
    rows = []
    for tname, tk in TKS:
        ct, qt = tk(text), tk(question)
        shared = [t for t in dict.fromkeys(qt) if t in set(ct)]
        rows.append([tname, " · ".join(ct), " · ".join(qt), " · ".join(shared) if shared else "none: score 0"])
    fig.add_trace(go.Table(visible=(j == 0), columnwidth=[1.3, 3, 2, 1.6],
                           header=dict(values=["tokenizer", f"chunk text: \"{text}\"", f"question: \"{question}\"", "shared"],
                                       fill_color="#f0efec", font=dict(color=INK), align="left"),
                           cells=dict(values=list(map(list, zip(*rows))), align="left", fill_color=SURFACE,
                                      font=dict(color=INK2), height=30)))
fig.update_layout(title="§9 · Tokenizer table: what BM25 can match (pick an example)", height=330,
                  margin=dict(t=110, b=10),
                  updatemenus=[dict(type="buttons", direction="right", x=0, y=1.2, xanchor="left", showactive=True,
                                    buttons=[dict(label=label, method="update",
                                                  args=[{"visible": [k == j for k in range(len(EX))]}])
                                             for j, (label, _, _) in enumerate(EX)])])
fig.show()

# ---- chart 2: windows above 0, split() vs tok_norm
qlabels = [f'"{q}"' for q, _ in QUERIES]
fig = go.Figure()
for name, label, colour in (("split", "split() (the repo)", AQUA), ("norm", "tok_norm (the course)", BLUE)):
    fig.add_bar(x=qlabels, y=[n for _, n in S9[name]], name=label, marker=dict(color=colour, line=dict(width=2, color=SURFACE)),
                customdata=[["not found" if r is None else r] for r, _ in S9[name]],
                hovertemplate="%{x}<br>windows above 0: %{y}<br>target rank: %{customdata[0]}<extra>" + label + "</extra>")
fig.update_layout(barmode="group", title="§9 · Windows that score above 0, per query (91 windows)", height=400,
                  yaxis=dict(title="windows with score > 0 (of 91)", range=[0, 95]))
fig.show()
''')

md(r"""
### §9, continued · the code-identifier toy (P3_FACTS K6)

**Which code tokenizer.** The next cell rebuilds K6's numbers with **K6's toy rule** (`tok_parts_whole`), because P3_FACTS and the lesson's K6 numbers were measured with it. That rule takes runs of letters, digits and `_` only, so it **splits at dots**: `1.5` → `1`, `5` and `v2.10.3` → `v2`, `10`, `3`. The tokenizer table above, the lesson's playground (`tokCode`) and the fit-check tool's `--tokenizer code` use the code-aware rule: the same split at `_` and at case changes, plus the whole name, but dotted numbers stay whole (`1.5`, `v2.10.3`). On the ten function signatures of K6 there are no dotted numbers, so both rules give the same tokens there.
""")
code(r'''
# ---- the code-identifier toy (P3_FACTS K6), with K6's TOY rule as measured. It splits at dots (1.5 -> 1, 5);
#      the lesson playground's tokCode and the tool's --tokenizer code keep dotted numbers whole (see the note above).
SIGS = ["getUserId(token) -> int", "get_user_id(session) -> int", "getOrderId(order) -> int", "delete_user(user_id) -> None",
        "listUsers(team) -> list", "parseConfig(path) -> dict", "sendEmail(to, body) -> bool",
        "resizeImage(img, width) -> Image", "hashPassword(pw) -> str", "openSocket(host, port) -> Socket"]
CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def tok_parts(text):                         # TOY code tokenizer: split snake_case and camelCase into lower-case parts
    out = []
    for run in re.findall(r"[A-Za-z0-9_]+", text):
        out += [w.lower() for piece in run.split("_") for w in CAMEL.split(piece) if w]
    return out


def tok_parts_whole(text):                   # TOY: the parts, plus the whole identifier when it has more than one part
    out = []
    for run in re.findall(r"[A-Za-z0-9_]+", text):
        parts = tok_parts(run)
        out += parts + ([run.lower()] if len(parts) > 1 else [])
    return out


def k6(tk, q):
    m = BM25Okapi([tk(s) for s in SIGS])
    s = m.get_scores(tk(q))
    o = ranked(list(s))
    return s, o, (o.index(0) + 1 if s[0] > 0 else None)


name_of = lambda i: SIGS[i].split("(")[0]
s, o, r = k6(tok_norm, "user id")
check("§9 K6 tok_norm, 'user id': matches and getUserId's rank",
      [[name_of(i), s[i]] for i in o if s[i] > 0] + [r], [["delete_user", 2.6276], ["get_user_id", 2.1134], None], T4)
s, o, r = k6(tok_norm, "getUserId")
check("§9 K6 tok_norm, 'getUserId': the only match", [[name_of(i), s[i]] for i in o if s[i] > 0], [["getUserId", 2.0176]], T4)
s, o, r = k6(tok_parts, "user id")
check("§9 K6 parts only, 'user id': top 3 and getUserId's rank", [[name_of(i), s[i]] for i in o[:3]] + [r],
      [["delete_user", 1.4243], ["getUserId", 1.0983], ["get_user_id", 1.0983], 2], T4)
s, o, r = k6(tok_parts, "getUserId")
check("§9 K6 parts only, 'getUserId': a tie with get_user_id", [s[0], s[1]], [1.8392, 1.8392], T4)
s, o, r = k6(tok_parts_whole, "user id")
check("§9 K6 parts + whole name, 'user id': getUserId rank and score", [r, s[0]], [2, 1.1126], T4)
s, o, r = k6(tok_parts_whole, "getUserId")
check("§9 K6 parts + whole name, 'getUserId': getUserId, get_user_id", [s[0], s[1], r], [3.6807, 1.8631, 1], T4)
''')

# =====================================================================================================================
md(r"""
## 10 · Chunking: one mention can count as two chunks

**What this verifies** (lesson §10, P3_FACTS K2 and K8), on the **91 windows**:
- the PDF says "BECCS" once, at character 66,441;
- window 82 covers characters 65,600 to 66,600 and window 83 covers 66,400 to 67,400: the mention sits in their 200-character overlap, so df = 2;
- of the 799 tokens that occur once in the whole text, 184 (23.0%) are counted in two windows; the windows contain 101 token "fragments" (words cut at a window edge) that do not exist in the whole text.

**The chart** draws windows 80 to 85 as character ranges, with the mention marked.
""")
code(r'''
offs = [m.start() for m in re.finditer("BECCS", full)]
check("§10 character offsets of 'BECCS'", offs, [66441])
spans = {i: [i * (SIZE - OVERLAP), min(i * (SIZE - OVERLAP) + SIZE, len(full))] for i in range(len(W))}
check("§10 window 82 and 83 character ranges", [spans[82], spans[83]], [[65600, 66600], [66400, 67400]])
check("§10 windows that contain the one mention", [i for i, w in enumerate(W) if "BECCS" in w], [82, 83])
check("§10 so df(beccs) = 2, and its idf is 3.577948 (not ipcc's 4.099885 for df 1)", [DF91["beccs"], BM91.idf["beccs"]],
      [2, 3.577948], T6)
once = [t for t, n in collections.Counter(tok_norm(full)).items() if n == 1]
two = [t for t in once if DF91[t] == 2]
whole = set(tok_norm(full))
check("§10 tokens once in the whole text; of them counted in 2 windows; share in %",
      [len(once), len(two), round(100 * len(two) / len(once), 1)], [799, 184, 23.0])
check("§10 window vocabulary vs whole-text vocabulary; fragments; whole-text tokens missing",
      [len(DF91), len(whole), len(set(DF91) - whole), len(whole - set(DF91))], [1870, 1769, 101, 0])
print("   five fragments:", sorted(set(DF91) - whole)[:5])

show_w = list(range(80, 86))
fig = go.Figure()
fig.add_bar(y=[f"window {i}" for i in show_w], x=[spans[i][1] - spans[i][0] for i in show_w], base=[spans[i][0] for i in show_w],
            orientation="h", marker=dict(color=[BLUE if i in (82, 83) else AXIS for i in show_w], line=dict(width=2, color=SURFACE)),
            customdata=[spans[i] for i in show_w], showlegend=False,
            hovertemplate="%{y}: characters %{customdata[0]:,} to %{customdata[1]:,}<extra></extra>")
fig.update_layout(title="§10 · Windows 80 to 85 as character ranges: one BECCS mention, two windows", height=380,
                  xaxis=dict(title="character position in the PDF text", tickformat=","),
                  yaxis=dict(autorange="reversed", showgrid=False),
                  shapes=[dict(type="rect", x0=66400, x1=66600, y0=-0.5, y1=5.5, fillcolor="rgba(42,120,214,0.10)", line=dict(width=0),
                               layer="below"),
                          dict(type="line", x0=66441, x1=66441, y0=-0.5, y1=5.5, line=dict(color=ORANGE, width=2))],
                  annotations=[dict(x=66441, y=-0.5, yref="y", text="BECCS @ 66,441", showarrow=False, yanchor="bottom",
                                    xanchor="left", font=dict(color=INK))])
fig.show()
''')

# =====================================================================================================================
md(r"""
## 11 · A score is not an answer

**What this verifies** (lesson §11):
- on the **91 windows**, the vague question "What can be done about this?" has no rare word, yet 81 of 91 windows score above 0 and its top score, 5.7608, is *higher* than the BECCS question's 5.0623 (P3_FACTS K7);
- on the **97 chunks** (R1_FACTS S5, S8): draft seeds with no answer in the PDF still get high best scores, D-009 6.9559 and D-010 13.2576; for the paraphrase D-006, a chunk containing "panels" (seq 64, page 22) scores 13.6205, above the real evidence (seq 21) at 9.2298, while dense search ranks the evidence first.

**The chart** plots every window's score, best first, for the two questions.
""")
code(r'''
q7 = tok_norm("What can be done about this?")
s7v = BM91.get_scores(q7)
o7 = ranked(list(s7v))
for t in q7:
    print(f"   {t:6s} df {DF91[t]:2d}  idf used {'not in the index' if t not in BM91.idf else f'{BM91.idf[t]:.6f}'}")
check("§11 vague question: tokens not in the index", [t for t in q7 if t not in BM91.idf], ["what", "done"])
check("§11 vague question: idf of can, be, about, this", [BM91.idf[t] for t in ("can", "be", "about", "this")],
      [0.838237, 2.284780, 2.284780, 0.838237], T6)
check("§11 vague question: windows above 0", int((s7v > 0).sum()), 81)
check("§11 vague question: score at rank 1, 5, 10, 40", [s7v[o7[i]] for i in (0, 4, 9, 39)], [5.7608, 4.3718, 3.6997, 1.7162], T4)
check("§11 the BECCS question's top score is lower", sB.max(), 5.0623, T4)

BS = {s["qid"]: bm25_scores(s["question"]) for s in SEEDS}
check("§11 D-009 best BM25 score (97 chunks; no answer in the PDF)", max(BS["D-009"].values()), 6.9559, T4)
check("§11 D-010 best BM25 score (97 chunks; no answer in the PDF)", max(BS["D-010"].values()), 13.2576, T4)
o6 = order(top_list(BS["D-006"], len(IDS), True))
id21 = next(d for d in IDS if SEQ[d] == 21)
check("§11 D-006 BM25 rank 1: chunk seq and page", [SEQ[o6[0]], PAGE[o6[0]]], [64, 22])
check("§11 D-006 BM25: seq 64 vs the evidence seq 21", [BS["D-006"][o6[0]], BS["D-006"][id21]], [13.6205, 9.2298], T4)
check("§11 D-006: idf of 'panels' (97 chunks)", BM97.idf["panels"], 4.1641, T4)
if DENSE_OK:
    DS = {s["qid"]: dense_scores(s["question"]) for s in SEEDS}
    od6 = order(DS["D-006"])
    check("§11 D-006 dense rank 1 is the evidence, seq 21; its cosine; seq 64's cosine",
          [SEQ[od6[0]], DS["D-006"][od6[0]], DS["D-006"][o6[0]]], [21, 0.5331, 0.5004], T4)
else:
    skip("§11 D-006 dense ranks", "MiniLM did not load (see §1)")

fig = go.Figure()
for label, sc, colour in (('"What does BECCS stand for?"', sB, BLUE), ('"What can be done about this?"', s7v, ORANGE)):
    srt = sorted(sc, reverse=True)
    fig.add_scatter(x=list(range(1, len(srt) + 1)), y=r5(srt), mode="lines+markers", name=label,
                    line=dict(color=colour, width=2), marker=dict(size=6),
                    hovertemplate="rank %{x}: score %{y:.4f}<extra>" + label + "</extra>")
fig.update_layout(title="§11 · Every window's score, best first: a vague question can out-score a perfect match (91 windows)",
                  height=420, xaxis=dict(title="rank"), yaxis=dict(title="BM25 score"))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 12 · Measuring: count where the right chunk lands

**What this verifies** (lesson §12):
- from the §1 ranks (97 chunks): Hit@1 / Hit@4 / MRR = dense 1/5, 5/5, 0.417 · BM25 `tok_norm` 5/5, 5/5, 1.000 · BM25 `split()` 2/5, 3/5, 0.500. (MRR: average of 1 ÷ rank; not found counts 0);
- the 8 answerable draft seeds of 06 §6.7 (97 chunks), **recomputed** here with R1's code (the reference `rel` and `ce` of the acceptance suite): MRR@10 dense 0.708 and BM25 0.938; CE@4 8/8 for both. Draft-seed observations, not evaluation results: the seeds were drafted by an LLM.

**The chart** shows Hit@k for k = 1 to 10 from the five §1 queries.
""")
code(r'''
hit = lambda ranks, k: sum(r is not None and r <= k for r in ranks)
mrr = lambda ranks: sum(1 / r for r in ranks if r is not None) / len(ranks)
EXP12 = {"dense": [1, 5, 0.417], "bm25": [5, 5, 1.000], "split": [2, 3, 0.500]}
for key, label in (("dense", "Dense"), ("bm25", "BM25, tok_norm"), ("split", "BM25, split()")):
    if not RANKS[key]:
        skip(f"§12 {label} Hit@1/Hit@4/MRR", "MiniLM did not load (see §1)")
        continue
    got = [hit(RANKS[key], 1), hit(RANKS[key], 4), mrr(RANKS[key])]
    print(f"   {label:15s} ranks {RANKS[key]}: Hit@1 {got[0]}/5, Hit@4 {got[1]}/5, MRR {got[2]:.3f}")
    check(f"§12 {label}: Hit@1, Hit@4 (of 5), MRR", got, EXP12[key], T3)


def summarise(rank_fn, k=4):                              # as r1_measure.py S4
    h = c = 0
    rr, per = [], {}
    for s in ANS:
        rk = rank_fn(s["qid"])
        fr = first_rel(rk, s)
        h += int(fr is not None and fr <= k)
        c += ce_ids(rk[:k], s)
        rr.append(1.0 / fr if (fr is not None and fr <= 10) else 0.0)
        per[s["qid"]] = fr
    return {"hit": h, "ce": c, "mrr10": sum(rr) / len(rr), "first_rel": per}


SUM_B = summarise(lambda q: order(top_list(BS[q], len(IDS), True)))
check("§12 draft seeds, BM25 tok_norm: Hit@4, CE@4 (of 8), MRR@10", [SUM_B["hit"], SUM_B["ce"], SUM_B["mrr10"]], [8, 8, 0.938], T3)
check("§12 draft seeds, BM25: first relevant rank D-001..D-008", list(SUM_B["first_rel"].values()), [1, 1, 1, 1, 1, 2, 1, 1])
if DENSE_OK:
    SUM_D = summarise(lambda q: order(DS[q]))
    check("§12 draft seeds, dense: Hit@4, CE@4 (of 8), MRR@10", [SUM_D["hit"], SUM_D["ce"], SUM_D["mrr10"]], [8, 8, 0.708], T3)
    check("§12 draft seeds, dense: first relevant rank D-001..D-008", list(SUM_D["first_rel"].values()), [3, 3, 1, 1, 1, 1, 2, 2])
else:
    SUM_D = None
    skip("§12 draft seeds, dense metrics", "MiniLM did not load; R1_FACTS S4 gives MRR@10 0.708 and CE@4 8/8 (taken from R1's run)")

ks = list(range(1, 11))
fig = go.Figure()
for key, label, colour in (("dense", "dense (MiniLM)", ORANGE), ("bm25", "BM25, tok_norm", BLUE), ("split", "BM25, split()", AQUA)):
    if RANKS[key]:
        fig.add_scatter(x=ks, y=[hit(RANKS[key], k) for k in ks], name=label, mode="lines+markers",
                        line=dict(color=colour, width=2, shape="hv"), marker=dict(size=8),
                        hovertemplate="k = %{x}: %{y} of 5 queries hit<extra>" + label + "</extra>")
fig.update_layout(title="§12 · Hit@k on the five §1 queries (97 chunks): at k = 4 dense and BM25 tie", height=420,
                  xaxis=dict(title="k (chunks passed to the LLM)", dtick=1), yaxis=dict(title="queries whose target is in the top k", range=[0, 5.4], dtick=1))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 13 · When to use BM25 alone, and when not

**What this verifies** (lesson §13). The decision table rests on numbers checked above; this cell gathers them in one place:
- **exact identifiers**: BM25 `tok_norm` ranks all five §1 terms first; the BECCS chunk is 4th for dense (§1);
- **own words**: on the paraphrase D-006, dense ranks the evidence 1st and BM25 2nd (§11, §12);
- **vague questions**: 81 of 91 windows match, by common words only (§11).

The chart splits the 8 draft seeds by their 06 category and shows MRR@10 for each retriever. These per-category values are **computed here** from the ranks checked in §12; they are draft-seed observations on very small groups (1 to 3 questions), so they illustrate how to report per type, not which retriever is better.
""")
code(r'''
if DENSE_OK:
    check("§13 BECCS: dense rank, BM25 rank; D-006: dense rank, BM25 rank",
          [RANKS["dense"][1], RANKS["bm25"][1], SUM_D["first_rel"]["D-006"], SUM_B["first_rel"]["D-006"]], [4, 1, 1, 2])
else:
    skip("§13 dense side of the decision table", "MiniLM did not load (see §1)")
check("§13 vague question: windows that match by common words only", int((s7v > 0).sum()), 81)

cats = collections.defaultdict(list)
for s in ANS:
    cats[s["category"]].append(s["qid"])
mrr10 = lambda per, qids: sum((1 / per[q]) if per[q] and per[q] <= 10 else 0 for q in qids) / len(qids)
print(f"   {'category':22s} {'n':>2s} {'dense MRR@10':>13s} {'BM25 MRR@10':>12s}")
for cat, qids in cats.items():
    dval = f"{mrr10(SUM_D['first_rel'], qids):.3f}" if SUM_D else "SKIP"
    print(f"   {cat:22s} {len(qids):2d} {dval:>13s} {mrr10(SUM_B['first_rel'], qids):12.3f}   {qids}")

labels = [f"{c} (n = {len(q)})" for c, q in cats.items()]
fig = go.Figure()
if SUM_D:
    fig.add_bar(x=labels, y=r5(mrr10(SUM_D["first_rel"], q) for q in cats.values()), name="dense (MiniLM)",
                marker=dict(color=ORANGE, line=dict(width=2, color=SURFACE)), hovertemplate="%{x}: %{y:.3f}<extra>dense</extra>")
fig.add_bar(x=labels, y=r5(mrr10(SUM_B["first_rel"], q) for q in cats.values()), name="BM25, tok_norm",
            marker=dict(color=BLUE, line=dict(width=2, color=SURFACE)), hovertemplate="%{x}: %{y:.3f}<extra>BM25</extra>")
fig.update_layout(barmode="group", title="§13 · Report per question type: MRR@10 by category (8 draft seeds, 97 chunks)",
                  height=420, yaxis=dict(title="MRR@10", range=[0, 1.1]))
fig.show()
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
for name, why in SKIPPED:
    print("   SKIPPED:", name, "-", why)
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
