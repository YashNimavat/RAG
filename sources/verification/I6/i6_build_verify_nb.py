"""Build study/notebooks/I6_doc_augmentation_verify.ipynb: the "verify it yourself" notebook for I6 (document
augmentation / HyPE: questions written for each chunk when the index is built).

The notebook rebuilds every measured number and chart of the I6 lesson (study/lessons/I6_doc_augmentation.html) from
code, one section per lesson step (1-11; step 11 holds the K2 upstream arithmetic), and compares each value with the
lesson's value in a `check(...)` line. Expected values are copied from sources/verification/I6/I6_FACTS.md (K1-K12,
i6_kit_measure.py -> out_i6_kit_measure.txt). The code paths are those of i6_kit_measure.py (v0's 97 chunks rebuilt
through sources/verification/corrections/contracts_check.py and the 07 modules, exactly as P4 does it), so the numbers
come out identical.

The index-time questions are read from the STAND-IN pack study/tools/examples/climate_i6_questions.jsonl (written by
Claude helpers blind to the eval set; not the planned Groq / Haiku replay pack). The seeds are the LLM-drafted 06 section
6.7 items. The optional cross-encoder filter section runs only if cross-encoder/ms-marco-MiniLM-L-6-v2 is in the local
Hugging Face cache and is SKIPPED otherwise; no lesson number depends on it.

No Groq, Cohere or Claude call, no .env read, no network (MiniLM loads from the local Hugging Face cache, offline).
The climate PDF path: the environment variable CLIMATE_PDF if set, else <rag_learning>/../upstream/RAG_Techniques/data/
Understanding_Climate_Change.pdf (the layout of the course machine, as in P4's notebook).

Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I6/i6_build_verify_nb.py
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I6/i6_verify_nb_run.py \
        > sources/verification/I6/out_i6_verify_nb_run.txt                              # executes it, saves outputs
"""
from pathlib import Path
from textwrap import dedent

import nbformat as nbf

WS = Path(__file__).resolve().parents[3]                      # rag_learning/
OUT = WS / "study" / "notebooks" / "I6_doc_augmentation_verify.ipynb"

CELLS = []


def md(s):
    CELLS.append(nbf.v4.new_markdown_cell(dedent(s).strip()))


def code(s):
    CELLS.append(nbf.v4.new_code_cell(dedent(s).strip()))


# =====================================================================================================================
md(r"""
# I6 · Verify it yourself: questions written for each chunk at index time

**What this is:** a notebook that rebuilds every measured number and chart of the I6 lesson (document augmentation and HyPE) from real code, so you can see each one being made and change the inputs.
**What this is not:** the lesson, the quiz, or the planned LLMOps notebook that will call a real generator. It makes **no API call**: no Groq, no Cohere, no Claude. Nothing here writes a question; it only reads questions that were written earlier.

**How to use it.** Run all cells from the top (VS Code: *Run All*). The sections are numbered like the lesson's steps, 1 to 11. Each one has:
- a short note on what it rebuilds;
- a code cell that **computes** the values;
- `check(...)` lines: `PASS` means the code produced the number the lesson shows, `FAIL` means it did not;
- an interactive chart where one is worth seeing. Hover for values.

The last cell counts the checks.

**Labels used for numbers.** *measured* = computed here from real text with a real model; *toy* = made-up scores that show a mechanism; *formula* = arithmetic; *external* = from a paper, a price page or documentation, not re-run here.

**Read these labels before any number.**
- **The questions are a stand-in.** `study/tools/examples/climate_i6_questions.jsonl` holds 10 questions for each of the 97 chunks (970 in all). Claude helpers wrote them on 2026-10-18 with the prompt file `i6_questions_prompt_v1.txt`, one chunk at a time, and **never saw the eval set**. They stand in for the replay pack the LLMOps notebook will record with the course's generator (Groq or Haiku). Every number that depends on the questions is a measurement **on this pack**; another generator will give other numbers.
- **The seeds are LLM-drafted.** The 10 draft questions of 06 §6.7 (8 with an answer in the PDF) were written by an LLM and are not yet checked by you. Eight items show the mechanism; they cannot name a winner. Every rank here is an **observation, not an evaluation result**.
- **The model.** `all-MiniLM-L6-v2` from the local Hugging Face cache, offline. In the build container its weights were rebuilt from an ONNX export of the same model, and parity with P4's numbers was checked first (I6_FACTS §0). On your machine it loads from the normal cache.
- **Book pages** in the lesson are "per 04, not re-opened"; this notebook uses none.

**The running example.** The **97 chunks** of the climate PDF (v0's index: the 07 recursive chunker, per page, 1,000 characters with 200 overlap; the same file as P3's and P4's notebooks), the 970 stand-in questions, and the draft seeds D-001 to D-010 plus the one paraphrase 06 gives, D-002-P1.

**The PDF.** Set the environment variable `CLIMATE_PDF` to the file, or leave it unset to use `<rag_learning>/../upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf`.

**Where the expected values come from.** `sources/verification/I6/I6_FACTS.md`, sections K1–K12 (`i6_kit_measure.py` → `out_i6_kit_measure.txt`). The upstream source citations (S-src) are checked by `i6_sources.py`, not here. The whole notebook takes well under a minute on a CPU.
""")

code(r'''
# Setup: imports, paths, the 97 chunks, the draft seeds, the question pack, MiniLM and the shared helpers. Run this first.
import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")          # the model may load from the local cache only: no network
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

import hashlib
import importlib.metadata as md
import json
import logging
import math
import re
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
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
T0 = time.time()


def find_workspace():
    here = Path.cwd().resolve()
    for p in (here, *here.parents):
        if (p / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").is_file() and (p / "study").is_dir():
            return p
    raise FileNotFoundError("Open this notebook from inside rag_learning/.")


WS = find_workspace()
# The climate PDF: CLIMATE_PDF if set, else the course layout (<Book RAG>/upstream next to rag_learning/).
PDF = Path(os.environ.get("CLIMATE_PDF") or WS.parent / "upstream" / "RAG_Techniques" / "data" / "Understanding_Climate_Change.pdf")
EX = WS / "study" / "tools" / "examples"
PACK = EX / "climate_i6_questions.jsonl"              # the STAND-IN question pack (Claude helpers, blind to the eval set)
PROMPT = EX / "i6_questions_prompt_v1.txt"
PRICES = EX / "prices_2026-10-17.json"
L6 = "sentence-transformers/all-MiniLM-L6-v2"
NS = (1, 3, 5, 10)                                    # n served from the one n_max = 10 pack by prefix
K = 4                                                 # the course's k
print("workspace:", WS)
print("PDF:", PDF.name, "(from CLIMATE_PDF)" if os.environ.get("CLIMATE_PDF") else "(default path)")
print("python", sys.version.split()[0], {p: md.version(p) for p in ("pymupdf", "numpy", "sentence-transformers", "torch", "tiktoken", "plotly")})

# ---------------------------------------------------------------- check(): computed value vs the lesson's value
CHECKS, SKIPPED = [], []
T6, T4, T3, T1 = 5e-7, 5e-5, 5e-4, 0.05   # tolerances for values the lesson prints with 6, 4, 3 or 1 decimals


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
        return (isinstance(got, dict) and isinstance(exp, dict) and list(got) == list(exp)
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
        return "{" + ", ".join(f"{k!r}: {_show(v)}" for k, v in x.items()) + "}"
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
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, RED = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#c8323c"
pio.templates["i6"] = go.layout.Template(layout=dict(
    font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', size=13, color=INK2),
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, colorway=[BLUE, ORANGE, AQUA, YELLOW],
    xaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    yaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=INK2)),
    title=dict(x=0, xanchor="left", font=dict(size=15, color=INK)),
    margin=dict(l=70, r=30, t=90, b=60), hoverlabel=dict(font_size=12)))
pio.templates.default = "i6"

# ---------------------------------------------------------------- environment (K1)
check("environment: pymupdf version (pinned)", md.version("pymupdf"), "1.26.7")
check("environment: sentence-transformers, numpy, tiktoken (K1)",
      [md.version("sentence-transformers"), md.version("numpy"), md.version("tiktoken")], ["6.1.0", "2.5.3", "0.14.0"])
pdf_bytes = PDF.read_bytes()
check("corpus: PDF sha256", hashlib.sha256(pdf_bytes).hexdigest(), "1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669")
pages = [p.get_text() for p in pymupdf.open(PDF)]

# ---------------------------------------------------------------- the 97 chunks, built exactly as i6_kit_measure.py (and P4)
sys.path.insert(0, str(WS / "sources" / "verification" / "corrections"))
import contracts_check as cc                          # noqa: E402  (06 recipe, 07 chunker loader, reference rel and CE)

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
check("97 chunks: chunks.jsonl sha256 (= P3, P4 and the C2 lab file)", SHA_JL,
      "d4108b8936093394c6eb50d4c22e8d4013d9a048fb38d5769281af4aadb3011b")
TEXT = [c["text"] for c in chunks]
PAGE = [c["page_segments"][0]["page"] for c in chunks]
SPAN = [("climate", c["char_start"], c["char_end"]) for c in chunks]
N = len(chunks)
TEXTS = {"climate": "\n".join(pages)}

# the 10 draft seeds of 06 §6.7 (llm-draft: observations, never evaluation results) and the one paraphrase variant
SEEDS = [json.loads(line) for line in cc.code_blocks(cc.section(md06, "6.7 Draft seed"), "jsonl")[0].splitlines() if line.strip()]
for s in SEEDS:
    s["G"] = [[[("climate", starts[seg["page"] - 1] + seg["char_start"], starts[seg["page"] - 1] + seg["char_end"])
                for seg in alt["segments"]] for alt in g["alternatives"]] for g in s["evidence_groups"]]
ANS = [s for s in SEEDS if s["answerable"]]
BYQ = {s["qid"]: s for s in SEEDS}
REL = {s["qid"]: [i for i in range(N) if cc.rel(SPAN[i], s["G"], TEXTS)] for s in ANS}
VARIANT = {"qid": "D-002-P1", "question": "When did countries adopt the Paris climate accord?", "paraphrase_of": "D-002"}
check("draft seeds: 10, of which 8 answerable; all created_by llm-draft (K1)",
      [len(SEEDS), len(ANS), sorted({s["created_by"] for s in SEEDS})], [10, 8, ["llm-draft"]])
check("relevant chunk seqs, D-001..D-008 (K1)", [REL[s["qid"]] for s in ANS],
      [[7], [27], [68], [23, 67, 68], [3, 4], [21], [27, 85], [69]])
check("seed categories D-001..D-010 (K1)", [s["category"] for s in SEEDS],
      ["exact-term", "factual-single-span", "factual-single-span", "exact-term", "multi-span", "vocabulary-mismatch",
       "multi-hop", "exact-term", "unanswerable", "unanswerable"])

# the stand-in question pack: one line per chunk, keyed by the chunk text's sha256
pack = [json.loads(line) for line in PACK.read_text(encoding="utf-8").splitlines() if line.strip()]
QS = [p["questions"] for p in pack]
check("question pack: sha256 (K1)", hashlib.sha256(PACK.read_bytes()).hexdigest(),
      "b6d060c7ab3024372d368c7ce4bd5df81f03b62ce249a9cbb21b83cdc25ce2c9")
check("question pack: lines, questions, per chunk min, max (K1)",
      [len(pack), sum(map(len, QS)), min(map(len, QS)), max(map(len, QS))], [97, 970, 10, 10])
check("question pack: one line per chunk in seq order, keyed by text_sha256",
      [[p["seq"] for p in pack] == list(range(N)), all(p["text_sha256"] == chunks[i]["text_sha256"] for i, p in enumerate(pack))],
      [True, True])


def first_rel(parents, qid):
    return next((r for r, i in enumerate(parents, 1) if i in REL[qid]), None)


def summary(ranks, k=K):
    """Hit@1, Hit@k (counts) and MRR@10 over a list of first-relevant ranks."""
    return (sum(r is not None and r <= 1 for r in ranks), sum(r is not None and r <= k for r in ranks),
            round(sum(1 / r for r in ranks if r is not None and r <= 10) / len(ranks), 3))


def ce_at(parents, qid, k):
    """CE@k: do the parents' [char_start, char_end) spans cover every evidence group? (06 reference rule)"""
    return cc.ce(BYQ[qid]["G"], [SPAN[i] for i in parents[:k]], TEXTS)


# ---------------------------------------------------------------- MiniLM (local cache) and the vectors
MODELS_OK = False
ENC_CALLS = [0]                                      # how many times the embedding model is called (section 2)
try:
    import transformers
    transformers.utils.logging.disable_progress_bar()
    transformers.utils.logging.set_verbosity_error()
    from sentence_transformers import SentenceTransformer
    m6 = SentenceTransformer(L6, device="cpu")
    MODELS_OK = True
except Exception as e:  # noqa: BLE001
    skip("every model-based check", f"MiniLM could not load offline: {type(e).__name__}: {str(e)[:160]}")


def enc(texts):
    ENC_CALLS[0] += 1
    return m6.encode(list(texts), convert_to_numpy=True, batch_size=32, show_progress_bar=False)


FLATQ = [(p, j, q) for p, qs in enumerate(QS) for j, q in enumerate(qs)]   # (parent seq, position, question text)
QIDX = {(p, j): r for r, (p, j, _) in enumerate(FLATQ)}
if MODELS_OK:
    EC = enc(TEXT)                                   # chunk vectors, unit length
    EQ = enc([q for _, _, q in FLATQ])               # question vectors, unit length
    QV = {s["qid"]: enc([s["question"]])[0] for s in SEEDS}
    QV[VARIANT["qid"]] = enc([VARIANT["question"]])[0]
    check("vectors: chunks, questions (K1)", [list(EC.shape), list(EQ.shape)], [[97, 384], [970, 384]])
    check("vectors: unit length (max |norm - 1| < 1e-6; K1 prints 1.19e-07)",
          bool(max(np.abs(np.linalg.norm(EC, axis=1) - 1).max(), np.abs(np.linalg.norm(EQ, axis=1) - 1).max()) < 1e-6), True)

# ---------------------------------------------------------------- the o200k_harmony tokenizer (token counts, sections 10-11)
TOK_OK = False
try:
    import tiktoken
    ENC_TT = tiktoken.get_encoding("o200k_harmony")
    TOK = lambda t: len(ENC_TT.encode(t))           # noqa: E731
    TOK_OK = True
except Exception as e:  # noqa: BLE001
    skip("every token-count check (sections 10, 11)", f"o200k_harmony could not load offline: {type(e).__name__}: {str(e)[:160]}")


# ---------------------------------------------------------------- the multi-vector index, as i6_kit_measure.py builds it
def mv_scores(qv, n, design):
    """One score per stored vector. design: 'chunks' (A0), 'chunks+q' (A1), 'q-only' (A2); n questions per chunk."""
    own_, kind, qtext, mats = [], [], [], []
    if design in ("chunks", "chunks+q"):
        mats.append(EC)
        own_ += list(range(N)); kind += ["chunk"] * N; qtext += [None] * N
    if design in ("chunks+q", "q-only"):
        rows = [QIDX[(p, j)] for p in range(N) for j in range(min(n, len(QS[p])))]
        mats.append(EQ[rows])
        own_ += [FLATQ[r][0] for r in rows]; kind += ["question"] * len(rows); qtext += [FLATQ[r][2] for r in rows]
    M = np.vstack(mats)
    return M @ qv, np.array(own_), kind, qtext


def parents_ranked(qv, n, design, agg="max"):
    """Parents best first: score = max (or sum) over the parent's vectors; duplicates removed; ties by smaller seq."""
    s, ow, _, _ = mv_scores(qv, n, design)
    if agg == "max":
        best = {}
        for i in sorted(range(len(s)), key=lambda i: (-s[i], i)):
            best.setdefault(int(ow[i]), float(s[i]))
        return sorted(best, key=lambda p: (-best[p], p)), best
    tot = Counter()
    for i in range(len(s)):
        tot[int(ow[i])] += float(s[i])
    return sorted(tot, key=lambda p: (-tot[p], p)), dict(tot)


def unique_in_topk(qv, n, design, kvec):
    s, ow, _, _ = mv_scores(qv, n, design)
    top = sorted(range(len(s)), key=lambda i: (-s[i], i))[:kvec]
    return len(dict.fromkeys(int(ow[i]) for i in top))


print(f"\nsetup done in {time.time() - T0:.1f} s: {N} chunks, {len(FLATQ)} stand-in questions, {len(SEEDS)} draft seeds "
      f"+ 1 variant; MiniLM loaded: {MODELS_OK}; tokenizer loaded: {TOK_OK}")
''')

# =====================================================================================================================
md(r"""
## 1 · Questions and statements embed apart

**What this rebuilds** (lesson step 1, K12, K5). Search is one query vector, one score per stored vector, then a sort: a list, never a matrix. The shape hypothesis says a question's vector sits nearer other questions than the passage that answers it.
- **D-002** ("In what year was the Paris Agreement adopted?"): the chunk that holds the answer (27) is only rank 3 among the 97 chunks; the best chunk scores 0.4606. A generated question about the same fact scores **0.9869**.
- **The shape gap** for every seed: best question score minus best chunk score, with all 10 questions per chunk in the index (n = 10).
- **859 of 970** stand-in questions sit closer to a sibling question of their own chunk than to the chunk itself (0.886).
""")
code(r'''
if MODELS_OK:
    q2 = QV["D-002"]
    c2 = EC @ q2
    o2 = sorted(range(N), key=lambda i: (-c2[i], i))
    check("§1 D-002: one score per chunk (a list, not a matrix); with questions n = 5, one per stored vector",
          [list(c2.shape), len(mv_scores(q2, 5, "chunks+q")[0])], [[97], 582])
    check("§1 D-002: rank of chunk 27 among the chunks; the best chunk's score (K12)", [o2.index(27) + 1, float(c2.max())], [3, 0.4606], T4)
    g2 = EQ @ q2
    check("§1 D-002: the best generated question, its score and its chunk (K7, K12)",
          [FLATQ[int(g2.argmax())][2], float(g2.max()), FLATQ[int(g2.argmax())][0]], ["When was the Paris Agreement adopted?", 0.9869, 27], T4)

    ITEMS = [s["qid"] for s in SEEDS] + [VARIANT["qid"]]
    best_c = {k: float((EC @ QV[k]).max()) for k in ITEMS}
    best_q = {k: float((EQ @ QV[k]).max()) for k in ITEMS}
    gap = {k: best_q[k] - best_c[k] for k in ITEMS}
    check("§1 best chunk score D-001..D-010 (K12)", [best_c[k] for k in ITEMS[:10]],
          [0.4929, 0.4606, 0.6497, 0.4210, 0.4272, 0.5331, 0.7094, 0.2598, 0.3099, 0.5196], T4)
    check("§1 best question score D-001..D-010 (K12)", [best_q[k] for k in ITEMS[:10]],
          [0.9311, 0.9869, 0.7101, 0.9653, 0.4723, 0.6007, 0.7565, 0.9368, 0.7939, 0.5826], T4)
    check("§1 shape gap D-001..D-010, D-002-P1 (K12)", [gap[k] for k in ITEMS],
          [0.4382, 0.5263, 0.0604, 0.5443, 0.0450, 0.0676, 0.0471, 0.6770, 0.4840, 0.0631, 0.1277], T4)
    ans_q = [s["qid"] for s in ANS]
    check("§1 mean gap over the 8 answerable seeds; seeds where a question beats every chunk (K12)",
          [float(np.mean([gap[k] for k in ans_q])), sum(gap[k] > 0 for k in ans_q)], [0.3007, 8], T4)

    # the shape hypothesis on the pack itself (K5)
    closer = 0
    for p, qs in enumerate(QS):
        for j in range(len(qs)):
            g = EQ[QIDX[(p, j)]]
            sib = max(float(g @ EQ[QIDX[(p, jj)]]) for jj in range(len(qs)) if jj != j)
            closer += sib > float(g @ EC[p])
    check("§1 questions closer to a sibling question than to their own chunk; share (K5)",
          [closer, round(closer / len(FLATQ), 3)], [859, 0.886], T3)

    fig = go.Figure()
    fig.add_bar(x=ITEMS, y=[round(best_c[k], 4) for k in ITEMS], name="best chunk", marker=dict(color=BLUE, line=dict(width=2, color=SURFACE)),
                hovertemplate="%{x}: best chunk %{y:.4f}<extra></extra>")
    fig.add_bar(x=ITEMS, y=[round(best_q[k], 4) for k in ITEMS], name="best generated question (n = 10)",
                marker=dict(color=ORANGE, line=dict(width=2, color=SURFACE)), customdata=[round(gap[k], 4) for k in ITEMS],
                hovertemplate="%{x}: best question %{y:.4f} (gap %{customdata:+.4f})<extra></extra>")
    fig.update_layout(title="§1 · The shape gap: a generated question outscores every chunk for each seed (D-009, D-010 have no answer)",
                      barmode="group", height=400, xaxis=dict(title="draft seed (LLM-drafted) and the one paraphrase"),
                      yaxis=dict(title="cosine with the seed question (MiniLM)", range=[0, 1.05]))
    fig.show()
''')

# =====================================================================================================================
md(r"""
## 2 · Index time vs query time

**What this rebuilds** (lesson step 2). There are two lanes. At **index time** the generator writes questions once per chunk: 97 calls per rebuild, paid before any user arrives. At **query time** nothing extra happens: the user's question is embedded once, exactly as in v0, and searched against more vectors. Question generation is **not** part of the prompt sent to the answer model.

This cell counts the embedding calls one search makes with and without questions in the index (one each), and the generator calls a query adds (zero). HyDE is the mirror image: it writes a hypothetical answer for every query, one LLM call per query (Q2 owns it; section 10 has the arithmetic).
""")
code(r'''
if MODELS_OK:
    def search(question, n, design, k=K):
        qv = enc([question])                         # the only model call a query makes
        return parents_ranked(qv[0], n, design)[0][:k]

    before = ENC_CALLS[0]
    top_a0 = search(BYQ["D-002"]["question"], 0, "chunks")
    calls_a0 = ENC_CALLS[0] - before
    before = ENC_CALLS[0]
    top_a1 = search(BYQ["D-002"]["question"], 5, "chunks+q")
    calls_a1 = ENC_CALLS[0] - before
    llm_calls_at_query_time = 0                      # nothing in search() writes text
    print(f"   D-002 top 4 parents: chunks only {top_a0}; chunks + questions (n = 5) {top_a1}")
    check("§2 embedding calls per query: chunks only, chunks + questions; generator calls per query",
          [calls_a0, calls_a1, llm_calls_at_query_time], [1, 1, 0])
check("§2 generator calls per index build: one per chunk (FORMULA)", N, 97)
''')

# =====================================================================================================================
md(r"""
## 3 · One call per chunk writes n questions

**What this rebuilds** (lesson step 3, K1, K5). The prompt file and the pack it produced: `n_max = 10` questions per chunk in a JSON list, so n = 1, 3, 5 and 10 are served from the **same** call by taking the first n (the prefix trick; the prompt asks for the most central question first, so the order is the generator's guess). Then the safe way to read the answer: parse the JSON once, retry once and log (never split free text on newlines, as HyPE's cell 9 does), and a cache key built from the prompt version, the chunk text and the model.

The pack is a **stand-in** written by Claude helpers who never saw the eval set.
""")
code(r'''
tmpl = PROMPT.read_text(encoding="utf-8")
check("§3 prompt file sha256 (K1)", hashlib.sha256(PROMPT.read_bytes()).hexdigest(),
      "b44a15ec3beb8f8518e3de237108a036cfeac1edf911a54b82879fff196d6fab")
check("§3 prompt: placeholders {n_max} and {chunk_text}; asks for JSON; bans 'the text' references",
      ["{n_max}" in tmpl, "{chunk_text}" in tmpl, '{"questions"' in tmpl, '"the text"' in tmpl], [True, True, True, True])
check("§3 pack: prompt_version, n_max, generator label (stand-in, blind to the eval set) (K1)",
      [sorted({p["prompt_version"] for p in pack}), sorted({p["n_max"] for p in pack}),
       all("stand-in" in p["generator"] and "blind to the eval set" in p["generator"] for p in pack)],
      [["i6_questions_v1"], [10], True])
check("§3 the prefix trick: questions served for n = 1, 3, 5, 10 from one call per chunk",
      [sum(len(qs[:n]) for qs in QS) for n in NS], [97, 291, 485, 970])
check("§3 chunk 21 (page 8, D-006's gold): its first three questions (K5)", [PAGE[21], QS[21][:3]],
      [8, ["What are perovskite solar cells and solar paint?", "What are floating solar farms?",
           "Why do floating solar panels work more efficiently?"]])

# parse once, retry once (TOY replies): the JSON reply parses; free text split on newlines keeps the numbering
def parse_questions(reply, n_max=10):
    obj = json.loads(reply)
    qs = obj["questions"]
    if not (isinstance(qs, list) and len(qs) == n_max and all(isinstance(q, str) and q.strip().endswith("?") for q in qs)):
        raise ValueError("wrong shape")
    return qs


good = json.dumps({"questions": [f"Toy question {i}?" for i in range(10)]})
bad = "Here are your questions:\n1. Toy question 0?\n2. Toy question 1?"
try:
    parse_questions(bad)
    bad_result = "parsed"
except (ValueError, json.JSONDecodeError):
    bad_result = "rejected: retry once, then log"
check("§3 parse once: the JSON reply gives 10 questions; the free-text reply is", [len(parse_questions(good)), bad_result],
      [10, "rejected: retry once, then log"])
check("§3 HyPE-style split('\\n') of the free-text reply keeps the header and the numbering", bad.split("\n")[:2],
      ["Here are your questions:", "1. Toy question 0?"])


def cache_key(prompt_version, chunk_text, model):
    return hashlib.sha256(json.dumps([prompt_version, chunk_text, model]).encode("utf-8")).hexdigest()[:16]


k0 = cache_key("i6_questions_v1", TEXT[21], "generator-model")
check("§3 cache key changes with the prompt version, the chunk text and the model (not with the run)",
      [k0 != cache_key("i6_questions_v2", TEXT[21], "generator-model"), k0 != cache_key("i6_questions_v1", TEXT[22], "generator-model"),
       k0 != cache_key("i6_questions_v1", TEXT[21], "other-model"), k0 == cache_key("i6_questions_v1", TEXT[21], "generator-model")],
      [True, True, True, True])
''')

# =====================================================================================================================
md(r"""
## 4 · Clean, then check every question against its own chunk

**What this rebuilds** (lesson step 4, K5).
- **Rule counts** on the 970 questions: empty, no "?", a numbering prefix, a vague reference to the source ("the passage", "according to the …"; the one hit is a false positive), duplicates inside a chunk and across chunks.
- **Vocabulary echo:** the share of a question's content words found in its own chunk (0.777). A question that only repeats its chunk's words adds little a keyword search could not find.
- **Self-retrieval:** use each question as a query against the 97 chunks. Its own chunk is rank 1 for 529 questions and below rank 10 for 58: those questions are vague or point elsewhere (the Doc2Query-- concern).
- **The bottom-30% filter:** drop the 30% of questions with the lowest cos(question, own chunk). The cut is 0.5351; it drops 291. This is a **bi-encoder stand-in** for Doc2Query--'s cross-encoder (section 4b).
""")
code(r'''
DEICTIC = re.compile(r"\b(the|this) (text|passage|author|document|chunk|article|context|section)\b|according to the", re.I)
NUMBERING = re.compile(r"^\s*(\d+[.)]|[-*•])\s*")


def norm_q(q):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", q.lower())).strip()


flat = [q for qs in QS for q in qs]
r_empty = sum(not q.strip() for q in flat)
r_noq = sum(not q.strip().endswith("?") for q in flat)
r_num = sum(bool(NUMBERING.match(q)) for q in flat)
r_deictic = [q for q in flat if DEICTIC.search(q)]
dup_in = sum(len(qs) - len({norm_q(q) for q in qs}) for qs in QS)
dup_across = sum(c - 1 for c in Counter(norm_q(q) for q in flat).values() if c > 1)
RULES = {"empty": r_empty, "no '?'": r_noq, "numbering": r_num, "vague reference": len(r_deictic),
         "duplicate in a chunk": dup_in, "duplicate across chunks": dup_across}
print("   the one vague-reference hit:", r_deictic)
check("§4 rule counts: empty, no '?', numbering, vague reference, duplicates in a chunk, across chunks (K5)",
      list(RULES.values()), [0, 0, 0, 1, 0, 6])
check("§4 the vague-reference hit is a false positive ('the context of climate change')",
      bool(r_deictic) and "context of climate change" in r_deictic[0], True)
wl = [len(q.split()) for q in flat]
check("§4 words per question min, median, max (K5)", [min(wl), int(np.median(wl)), max(wl)], [3, 8, 15])
if TOK_OK:
    check("§4 tokens per question, median (o200k_harmony; K5)", int(np.median([TOK(q) for q in flat])), 10)

STOP = set("a an the of in on at to for and or is are was were be been by with from as that this what which who whom whose "
           "how why when where do does did can could would should will may might its it their there than then into about "
           "over under more most less least between such any each other some much many these those".split())


def content_words(t):
    return [w for w in re.findall(r"[a-z0-9]+", t.lower()) if w not in STOP and len(w) > 1]


echo = []
for p, qs in enumerate(QS):
    cw = set(content_words(TEXT[p]))
    for q in qs:
        w = content_words(q)
        echo.append(sum(x in cw for x in w) / len(w) if w else 0.0)
check("§4 vocabulary echo: mean, median; questions using only chunk words (K5)",
      [round(float(np.mean(echo)), 3), round(float(np.median(echo)), 3), sum(e == 1.0 for e in echo)], [0.777, 0.800, 227], T3)
check("§4 chunk 21: echo of each of its 10 questions (K5)", [round(echo[QIDX[(21, j)]], 2) for j in range(10)],
      [1.0, 1.0, 0.4, 1.0, 1.0, 0.8, 1.0, 0.6, 1.0, 0.67], 1e-9)

fig = go.Figure(go.Bar(x=list(RULES), y=list(RULES.values()), marker=dict(color=BLUE, line=dict(width=2, color=SURFACE)),
                       text=list(RULES.values()), textposition="outside", hovertemplate="%{x}: %{y} of 970<extra></extra>"))
fig.update_layout(title="§4 · Cleaning rules on the 970 stand-in questions: almost nothing to remove", height=360,
                  xaxis=dict(title="rule"), yaxis=dict(title="questions caught", range=[0, 8]), showlegend=False)
fig.show()

if MODELS_OK:
    own = np.array([float(EQ[QIDX[(p, j)]] @ EC[p]) for p, j, _ in FLATQ])
    own_rank = []
    for r, (p, j, _) in enumerate(FLATQ):
        s = EC @ EQ[r]
        own_rank.append(int((s > s[p]).sum()) + 1)
    own_rank = np.array(own_rank)
    check("§4 cos(question, own chunk): min, 10th percentile, median, max (K5)",
          [own.min(), np.percentile(own, 10), np.median(own), own.max()], [0.0407, 0.4274, 0.5917, 0.8464], T4)
    edges = [round(x * 0.1, 1) for x in range(0, 10)]
    hist = [int(((own >= a) & (own < a + 0.1)).sum()) for a in edges]
    check("§4 histogram of cos(question, own chunk), bins of 0.1 from 0.0 to 1.0 (K5)", hist,
          [5, 8, 20, 45, 132, 314, 322, 114, 10, 0])
    check("§4 own chunk's rank among 97: rank 1, <= 4, <= 10, > 10 (K5)",
          [int((own_rank == 1).sum()), int((own_rank <= 4).sum()), int((own_rank <= 10).sum()), int((own_rank > 10).sum())],
          [529, 830, 912, 58])
    cut30 = float(np.percentile(own, 30))
    check("§4 bottom-30% filter (bi-encoder stand-in): cut, dropped, kept (K5)",
          [cut30, int((own < cut30).sum()), int((own >= cut30).sum())], [0.5351, 291, 679], T4)
    worst = sorted(range(len(FLATQ)), key=lambda r: own[r])[:3]
    check("§4 the three lowest questions: (chunk seq, cos, own rank) (K5)",
          [[FLATQ[r][0], float(own[r]), int(own_rank[r])] for r in worst], [[73, 0.0407, 81], [63, 0.0439, 76], [87, 0.0618, 65]], T4)
    for r in worst:
        print(f"   chunk {FLATQ[r][0]} (p.{PAGE[FLATQ[r][0]]}): {FLATQ[r][2]!r}")

    fig = go.Figure()
    fig.add_bar(x=[a + 0.05 for a in edges], y=hist, width=0.1, name="questions", marker=dict(color=BLUE, line=dict(width=2, color=SURFACE)),
                customdata=[f"{a:.1f}-{a + 0.1:.1f}" for a in edges], hovertemplate="cos %{customdata}: %{y} questions<extra></extra>")
    fig.add_vline(x=cut30, line=dict(color=ORANGE, dash="dash", width=2),
                  annotation_text=f"30% cut {cut30:.4f}: drops {int((own < cut30).sum())}", annotation_position="top left")
    fig.update_layout(title="§4 · cos(question, its own chunk) for the 970 questions, with the bottom-30% cut", height=380,
                      xaxis=dict(title="cosine with its own chunk (MiniLM)", range=[0, 1], dtick=0.1),
                      yaxis=dict(title="questions"), showlegend=False)
    fig.show()
''')

md(r"""
### 4b · Optional: the cross-encoder filter

Doc2Query-- filters with a **cross-encoder** score of (question, own chunk), not with a bi-encoder cosine. This cell runs `cross-encoder/ms-marco-MiniLM-L-6-v2` on the 970 pairs **only if the model is already in your local Hugging Face cache** (this notebook never downloads), and compares its bottom 30% with the bi-encoder's. Otherwise it prints `SKIPPED (model not in cache)`. No lesson number depends on it, and a skip is not a failure.
""")
code(r'''
CE_ID = "cross-encoder/ms-marco-MiniLM-L-6-v2"
ce_dir = Path(os.environ.get("HF_HUB_CACHE") or Path(os.environ.get("HF_HOME") or Path.home() / ".cache" / "huggingface") / "hub")
ce_snap = ce_dir / f"models--{CE_ID.replace('/', '--')}" / "snapshots"
if MODELS_OK and ce_snap.is_dir() and any(ce_snap.iterdir()):
    from sentence_transformers import CrossEncoder
    ce = CrossEncoder(CE_ID, device="cpu")
    ce_s = np.asarray(ce.predict([(q, TEXT[p]) for p, _, q in FLATQ], batch_size=64, show_progress_bar=False), float)
    ce_cut = float(np.percentile(ce_s, 30))
    drop_ce, drop_bi = set(np.where(ce_s < ce_cut)[0]), set(np.where(own < cut30)[0])
    print(f"   cross-encoder bottom 30%: cut {ce_cut:.3f} (raw logit), drops {len(drop_ce)}; "
          f"overlap with the bi-encoder's {len(drop_bi)} dropped questions: {len(drop_ce & drop_bi)}")
    print("   (no lesson number depends on this; it shows how far the bi-encoder stand-in is from the real filter)")
else:
    skip("§4b optional cross-encoder filter",
         f"SKIPPED (model not in cache): {CE_ID} is not in the local Hugging Face cache; the lesson uses the bi-encoder "
         "stand-in, and no lesson number depends on this section")
''')

# =====================================================================================================================
md(r"""
## 5 · Three designs, one parent table

**What this rebuilds** (lesson step 5, K4). Every stored vector points to a row of a parent table: `vectors[i] → (kind, parent_id, question_text)`. Three designs:
- **chunks + questions** (document augmentation): 97 chunk vectors plus n question vectors per chunk, `N·(1+n)`;
- **questions only** (HyPE): `N·n`;
- **questions appended to the chunk text** (doc2query, LlamaIndex's extractor as metadata): still 97 vectors.

Bytes are `vectors × d × 4` (float32), at Cohere's 1,536 numbers and MiniLM's 384. C3's v0 index file is 596,096 bytes (128 header bytes + 97 × 1,536 × 4).
""")
code(r'''
SIZES = {n: (N * (1 + n), N * n) for n in NS}
check("§5 vectors, chunks + questions, n = 1, 3, 5, 10 (K4)", [SIZES[n][0] for n in NS], [194, 388, 582, 1067])
check("§5 vectors, questions only, n = 1, 3, 5, 10 (K4)", [SIZES[n][1] for n in NS], [97, 291, 485, 970])
check("§5 multiples of the 97-vector index at n = 5: chunks + q, q only (K4)", [SIZES[5][0] / N, SIZES[5][1] / N], [6, 5])
check("§5 bytes, chunks + questions at 1,536-d (K4)", [SIZES[n][0] * 1536 * 4 for n in NS], [1191936, 2383872, 3575808, 6555648])
check("§5 bytes, chunks + questions at 384-d (K4)", [SIZES[n][0] * 384 * 4 for n in NS], [297984, 595968, 893952, 1638912])
check("§5 bytes at n = 5, questions only, 1,536-d (K4; I6-A-01)", SIZES[5][1] * 1536 * 4, 2979840)
check("§5 C3 baseline file 128 + 97 x 1536 x 4; the appended-text design at 1,536-d (K4)", [128 + N * 1536 * 4, N * 1536 * 4], [596096, 595968])

# the parent table for chunks + questions at n = 5
TABLE = [("chunk", p, None) for p in range(N)] + [("question", p, QS[p][j]) for p in range(N) for j in range(5)]
check("§5 parent table at n = 5: rows; chunk rows, question rows; every parent_id is a chunk seq",
      [len(TABLE), sum(t[0] == "chunk" for t in TABLE), sum(t[0] == "question" for t in TABLE), {t[1] for t in TABLE} == set(range(N))],
      [582, 97, 485, True])
if MODELS_OK:
    _, ow5, kd5, qt5 = mv_scores(QV["D-002"], 5, "chunks+q")
    check("§5 the search code's vector order matches the parent table", [list(zip(kd5, ow5.tolist(), qt5)) == TABLE], [True])
print("   rows 97..99 of the table:", TABLE[97:100])

fig = go.Figure()
xs = [f"n = {n}" for n in NS]
fig.add_bar(x=xs, y=[SIZES[n][0] for n in NS], name="chunks + questions", marker=dict(color=BLUE, line=dict(width=2, color=SURFACE)),
            customdata=[f"{SIZES[n][0] * 1536 * 4:,}" for n in NS], hovertemplate="%{x}: %{y} vectors, %{customdata} bytes at 1,536-d<extra>chunks + questions</extra>")
fig.add_bar(x=xs, y=[SIZES[n][1] for n in NS], name="questions only", marker=dict(color=ORANGE, line=dict(width=2, color=SURFACE)),
            customdata=[f"{SIZES[n][1] * 1536 * 4:,}" for n in NS], hovertemplate="%{x}: %{y} vectors, %{customdata} bytes at 1,536-d<extra>questions only</extra>")
fig.add_bar(x=xs, y=[N] * len(NS), name="questions appended to the text (= v0)", marker=dict(color=AQUA, line=dict(width=2, color=SURFACE)),
            hovertemplate="%{x}: %{y} vectors<extra>appended text</extra>")
fig.update_layout(title="§5 · Index size for the 97 chunks: vectors per design (bytes = vectors × d × 4)", barmode="group", height=380,
                  xaxis=dict(title="questions per chunk"), yaxis=dict(title="stored vectors"))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 6 · Search the vectors, return unique parents

**What this rebuilds** (lesson step 6, K3, K7, K6).
- **The toy** (made-up scores, 8 vectors over 3 parents A, B, C): parent score by **max** gives A, B, C; by **sum** B, A, C (B wins only because it has 4 vectors); mean and RRF for comparison; cutting to k vectors **before** removing duplicates loses C; LangChain's default fetches 4 child vectors and returns only **2 parents** for "k = 4".
- **The D-006 trace** on the real index (chunks + questions, n = 5): the top 12 vectors are 11 questions and 1 chunk from 8 parents; removing duplicates in rank order gives the 4 parents 21, 64, 19, 32. A `set()` would lose the order.
- **Duplicates crowd the top k:** unique parents among the top 4 vectors, per arm, and how many vectors to fetch. Fetching K_vec = k(n + 1) vectors always leaves at least k parents.
""")
code(r'''
TOY = [("v1", "A", "question", 0.81), ("v2", "B", "question", 0.74), ("v3", "B", "question", 0.72),
       ("v4", "B", "chunk", 0.70), ("v5", "B", "question", 0.69), ("v6", "C", "question", 0.66),
       ("v7", "C", "chunk", 0.55), ("v8", "A", "chunk", 0.50)]
agg = {}
for _, p, _, s in TOY:
    agg.setdefault(p, []).append(s)
mx = {p: max(v) for p, v in agg.items()}
sm = {p: round(sum(v), 2) for p, v in agg.items()}
mn = {p: round(sum(v) / len(v), 4) for p, v in agg.items()}
rk = lambda d: sorted(d, key=lambda p: (-d[p], p))   # noqa: E731
check("§6 toy: vectors per parent (K3)", {p: len(v) for p, v in sorted(agg.items())}, {"A": 2, "B": 4, "C": 2})
check("§6 toy max: scores and ranking (K3)", [mx, rk(mx)], [{"A": 0.81, "B": 0.74, "C": 0.66}, ["A", "B", "C"]], 1e-9)
check("§6 toy sum: scores and ranking (K3)", [sm, rk(sm)], [{"A": 1.31, "B": 2.85, "C": 1.21}, ["B", "A", "C"]], 1e-9)
check("§6 toy mean: scores and ranking (K3)", [mn, rk(mn)], [{"A": 0.655, "B": 0.7125, "C": 0.605}, ["B", "A", "C"]], 1e-9)


def parent_order(kind):
    seen = []
    for _, p, kd, _ in sorted(TOY, key=lambda t: -t[3]):
        if kd == kind and p not in seen:
            seen.append(p)
    return seen


lc, lq = parent_order("chunk"), parent_order("question")
rrf = {p: round(1 / (60 + lc.index(p) + 1) + 1 / (60 + lq.index(p) + 1), 6) for p in agg}
check("§6 toy RRF (k = 60): chunk list, question list, scores, ranking (K3)", [lc, lq, rrf, rk(rrf)],
      [["B", "C", "A"], ["A", "B", "C"], {"A": 0.032266, "B": 0.032522, "C": 0.032002}, ["B", "A", "C"]], T6)
ranked = [p for _, p, _, _ in sorted(TOY, key=lambda t: -t[3])]
check("§6 toy: unique parents in the top 3, 4, 6, 8 vectors (K3)", [len(dict.fromkeys(ranked[:kv])) for kv in (3, 4, 6, 8)], [2, 2, 3, 3])
check("§6 toy k = 3: cut then dedup; dedup then cut (K3)", [list(dict.fromkeys(ranked[:3])), list(dict.fromkeys(ranked))[:3]],
      [["A", "B"], ["A", "B", "C"]])
check("§6 toy: set() of the top-4 parents has (and its order is not the rank order)", len(set(ranked[:4])), 2)


def lc_multivector(vectors, k_child=4):
    """LangChain MultiVectorRetriever default (langchain-classic 1.0.8), emulated: k child vectors, first-seen parents, scores dropped."""
    ids = []
    for d in sorted(vectors, key=lambda t: -t[3])[:k_child]:
        if d[1] not in ids:
            ids.append(d[1])
    return ids


check("§6 LangChain default emulation: parents for 'k = 4'; with search_kwargs k = 8 (K3)", [lc_multivector(TOY), lc_multivector(TOY, 8)],
      [["A", "B"], ["A", "B", "C"]])

if MODELS_OK:
    q6 = QV["D-006"]
    c0 = EC @ q6
    o0 = sorted(range(N), key=lambda i: (-c0[i], i))
    check("§6 D-006 chunks only: top 4, pages, gold rank (K7)", [o0[:4], [PAGE[i] for i in o0[:4]], o0.index(21) + 1],
          [[21, 64, 14, 13], [8, 22, 5, 5], 1])
    check("§6 D-006 chunks only: top 4 scores (K7)", [c0[i] for i in o0[:4]], [0.5331, 0.5004, 0.4772, 0.4696], T4)
    sc, ow, kd, qt = mv_scores(q6, 5, "chunks+q")
    order_ = sorted(range(len(sc)), key=lambda i: (-sc[i], i))
    top12 = order_[:12]
    for r, i in enumerate(top12, 1):
        print(f"   {r:2d} {sc[i]:.4f} {kd[i]:8s} parent {int(ow[i]):2d} (p.{PAGE[int(ow[i])]}) {qt[i] or ''}")
    check("§6 D-006 top vector: score, kind, parent, text (K7)", [float(sc[top12[0]]), kd[top12[0]], int(ow[top12[0]]), qt[top12[0]]],
          [0.5976, "question", 21, "Why do floating solar panels work more efficiently?"], T4)
    check("§6 D-006 top 12: parents in rank order (K7)", [int(ow[i]) for i in top12], [21, 64, 19, 32, 21, 14, 21, 74, 64, 66, 13, 13])
    chunk_pos = [r for r, i in enumerate(top12, 1) if kd[i] == "chunk"]
    check("§6 D-006 top 12: questions, chunks, the chunk's rank and score, unique parents (K7)",
          [sum(kd[i] == "question" for i in top12), len(chunk_pos), chunk_pos[0], float(sc[top12[chunk_pos[0] - 1]]),
           len(dict.fromkeys(int(ow[i]) for i in top12))], [11, 1, 7, 0.5331, 8], T4)
    par6, best6 = parents_ranked(q6, 5, "chunks+q")
    check("§6 D-006 dedup in rank order: 4 parents, pages (K7)", [par6[:4], [PAGE[i] for i in par6[:4]]], [[21, 64, 19, 32], [8, 22, 7, 11]])
    check("§6 D-006 the 4 parents' scores (K7)", [best6[i] for i in par6[:4]], [0.5976, 0.5869, 0.5752, 0.5696], T4)
    check("§6 chunk 21: best question vs its own chunk vector (K7)",
          [max(float(EQ[QIDX[(21, j)]] @ q6) for j in range(5)), float(c0[21])], [0.5976, 0.5331], T4)

    EXP_U = {(1, "chunks+q"): ([4, 3, 3, 4, 3, 4, 3, 4], 3.50, 3, 5), (1, "q-only"): ([4] * 8, 4.00, 4, 8),
             (3, "chunks+q"): ([4, 3, 2, 4, 2, 4, 2, 4], 3.12, 2, 7), (3, "q-only"): ([4, 3, 3, 4, 3, 4, 3, 4], 3.50, 3, 11),
             (5, "chunks+q"): ([4, 3, 2, 3, 2, 4, 2, 4], 3.00, 2, 10), (5, "q-only"): ([4, 3, 2, 4, 2, 4, 3, 4], 3.25, 2, 13),
             (10, "chunks+q"): ([3, 3, 2, 3, 2, 3, 2, 4], 2.75, 2, 14), (10, "q-only"): ([3, 3, 2, 3, 2, 3, 2, 4], 2.75, 2, 16)}
    mins_kvec = []
    for (n, design), (e_u, e_mean, e_min, e_kv) in EXP_U.items():
        u = [unique_in_topk(QV[s["qid"]], n, design, K) for s in ANS]
        uo = [unique_in_topk(QV[s["qid"]], n, design, K * (n + 1)) for s in ANS]
        mins_kvec.append(min(uo))
        check(f"§6 unique parents in the top 4 vectors, {design} n = {n}: per seed, mean, min; min at K_vec = {K * (n + 1)} (K6)",
              [u, round(float(np.mean(u)), 2), min(u), min(uo)], [e_u, e_mean, e_min, e_kv], 5e-3)
    check("§6 with K_vec = k(n + 1), at least 5 unique parents in every arm (K6)", min(mins_kvec) >= 5, True)
    fetch = []
    for s in ANS:
        sc_, ow_, _, _ = mv_scores(QV[s["qid"]], 10, "chunks+q")
        seen = []
        for r, i in enumerate(sorted(range(len(sc_)), key=lambda i: (-sc_[i], i)), 1):
            if int(ow_[i]) not in seen:
                seen.append(int(ow_[i]))
            if len(seen) == K:
                fetch.append(r)
                break
    check("§6 vectors fetched before 4 unique parents appear (chunks + q, n = 10): per seed, max, bound k(n + 1) (K6)",
          [fetch, max(fetch), K * 11], [[5, 5, 11, 10, 8, 5, 7, 4], 11, 44])

    # chart: the D-006 strip, coloured by parent (the 4 parents that survive the dedup get a colour; the rest are grey)
    PCOL = {21: BLUE, 64: ORANGE, 19: AQUA, 32: YELLOW}
    fig = go.Figure()
    for p in list(PCOL) + ["other"]:
        idx = [i for i in top12 if (int(ow[i]) == p if p != "other" else int(ow[i]) not in PCOL)]
        if not idx:
            continue
        fig.add_scatter(x=[order_.index(i) + 1 for i in idx], y=[round(float(sc[i]), 4) for i in idx], mode="markers",
                        name=(f"parent {p} (p.{PAGE[p]})" if p != "other" else "other parents (14, 74, 66, 13)"),
                        marker=dict(size=[16 if kd[i] == "chunk" else 12 for i in idx], color=PCOL.get(p, MUTED),
                                    symbol=["square" if kd[i] == "chunk" else "circle" for i in idx], line=dict(width=2, color=SURFACE)),
                        customdata=[[int(ow[i]), kd[i], qt[i] or "(the chunk's own vector)"] for i in idx],
                        hovertemplate="rank %{x}: %{y:.4f}, %{customdata[1]} of parent %{customdata[0]}<br>%{customdata[2]}<extra></extra>")
    fig.update_layout(title="§6 · D-006, top 12 vectors (chunks + questions, n = 5): 11 questions, 1 chunk (square), 8 parents",
                      height=400, xaxis=dict(title="vector rank", dtick=1), yaxis=dict(title="cosine with D-006"))
    fig.show()

    # chart: unique parents against K_vec
    fig = go.Figure()
    for (n, design), colour, dash in (((5, "chunks+q"), BLUE, "solid"), ((10, "chunks+q"), ORANGE, "solid"), ((5, "q-only"), AQUA, "dash")):
        orders = []
        for s in ANS:
            sc_, ow_, _, _ = mv_scores(QV[s["qid"]], n, design)
            orders.append([int(ow_[i]) for i in sorted(range(len(sc_)), key=lambda i: (-sc_[i], i))])
        kv = list(range(1, 45))
        mean_u = [float(np.mean([len(dict.fromkeys(o[:k_])) for o in orders])) for k_ in kv]
        fig.add_scatter(x=kv, y=np.round(mean_u, 3), mode="lines", name=f"{design}, n = {n}", line=dict(color=colour, width=2, dash=dash),
                        hovertemplate="K_vec %{x}: %{y:.2f} unique parents (mean of 8 seeds)<extra>" + f"{design}, n = {n}" + "</extra>")
        fig.add_scatter(x=[K * (n + 1)], y=[round(mean_u[K * (n + 1) - 1], 3)], mode="markers", marker=dict(size=10, color=colour),
                        showlegend=False, hovertemplate=f"K_vec = k(n + 1) = {K * (n + 1)}: " + "%{y:.2f}<extra></extra>")
    fig.add_hline(y=4, line=dict(color=INK2, dash="dot"), annotation_text="k = 4 parents wanted", annotation_position="bottom right")
    fig.add_vline(x=4, line=dict(color=MUTED, dash="dot"), annotation_text="LangChain default: 4 vectors", annotation_position="top right")
    fig.update_layout(title="§6 · Unique parents among the top K_vec vectors (mean over the 8 seeds): fetch more, then dedup, then cut",
                      height=400, xaxis=dict(title="vectors fetched, K_vec"), yaxis=dict(title="unique parents"))
    fig.show()
''')

# =====================================================================================================================
md(r"""
## 7 · Score the parent's span, never the question

**What this rebuilds** (lesson step 7, K6, K7, K8). Each arm returns parents (chunks); the metrics read the parents' `[char_start, char_end)` spans against the seeds' evidence spans, so a generated question is never scored as evidence and never sent to the answer model.
- **The K6 table:** first relevant rank for D-001…D-008, Hit@1, Hit@4, MRR@10 and CE@1 / CE@2 / CE@4 for A0 (chunks only, v0), A1 (chunks + questions) and A2 (questions only) at n = 1, 3, 5, 10, and the **sum** aggregation at n = 5.
- **What to read in it:** A1 at n = 5 lifts MRR@10 from 0.708 to 0.781 and Hit@1 from 4 to 5, while CE@4 drops from 8 to 7 because D-007 needs two chunks. n = 1 is worse than none (0.653). Questions only equals A1 from n = 5 on here. Sum is worse than max (0.760). **Eight LLM-drafted items prove nothing**: this is the mechanism, not a winner.
- D-001, D-002, D-008 and the paraphrase D-002-P1: the visible effect (rank 3, 3, 2 → 1).
""")
code(r'''
if MODELS_OK:
    EXP6 = {
        ("A0", 0, "chunks"): ([3, 3, 1, 1, 1, 1, 2, 2], 4, 8, 0.708, [4, 5, 8]),
        ("A1", 1, "chunks+q"): ([1, 4, 1, 1, 1, 2, 3, 7], 4, 7, 0.653, [4, 5, 7]),
        ("A1", 3, "chunks+q"): ([1, 1, 1, 1, 1, 1, 3, 15], 6, 7, 0.792, [6, 6, 7]),
        ("A1", 5, "chunks+q"): ([1, 1, 2, 1, 2, 1, 4, 1], 5, 8, 0.781, [5, 7, 7]),
        ("A1", 10, "chunks+q"): ([1, 1, 2, 1, 1, 2, 3, 1], 5, 8, 0.792, [5, 7, 7]),
        ("A2", 1, "q-only"): ([1, 17, 1, 2, 1, 4, 19, 13], 3, 5, 0.469, [3, 4, 5]),
        ("A2", 3, "q-only"): ([1, 1, 1, 3, 1, 1, 4, 31], 5, 7, 0.698, [5, 5, 6]),
        ("A2", 5, "q-only"): ([1, 1, 2, 1, 2, 1, 4, 1], 5, 8, 0.781, [5, 7, 7]),
        ("A2", 10, "q-only"): ([1, 1, 2, 1, 1, 2, 3, 1], 5, 8, 0.792, [5, 7, 7]),
    }
    RES = {}
    for (arm, n, design), (e_r, e_h1, e_h4, e_mrr, e_ce) in EXP6.items():
        ranks, ces = [], [0, 0, 0]
        for s in ANS:
            par, _ = parents_ranked(QV[s["qid"]], n, design)
            ranks.append(first_rel(par, s["qid"]))
            for j, k_ in enumerate((1, 2, 4)):
                ces[j] += ce_at(par, s["qid"], k_)
        RES[(arm, n)] = (ranks, *summary(ranks), ces)
        label = f"{arm} {design}" + (f" n = {n}" if n else "")
        check(f"§7 {label}: ranks D-001..D-008 (K6)", ranks, e_r)
        check(f"§7 {label}: Hit@1, Hit@4, MRR@10; CE@1, CE@2, CE@4 (of 8) (K6)", [*summary(ranks), ces], [e_h1, e_h4, e_mrr, e_ce], T3)
    for arm, design, e_r, e_mrr in (("A1", "chunks+q", [3, 1, 1, 1, 1, 2, 4, 1], 0.760), ("A2", "q-only", [3, 1, 1, 1, 1, 3, 4, 1], 0.740)):
        ranks = [first_rel(parents_ranked(QV[s["qid"]], 5, design, "sum")[0], s["qid"]) for s in ANS]
        check(f"§7 {arm} {design} n = 5, SUM: ranks; Hit@1, Hit@4, MRR@10 (K6)", [ranks, *summary(ranks)], [e_r, 5, 8, e_mrr], T3)
    check("§7 questions only equals chunks + questions at n = 5 and n = 10 (ranks)",
          [RES[("A2", 5)][0] == RES[("A1", 5)][0], RES[("A2", 10)][0] == RES[("A1", 10)][0]], [True, True])
    par_d7, _ = parents_ranked(QV["D-007"], 5, "chunks+q")
    check("§7 the CE@4 loss is D-007: how many of its two chunks (27, 85) are in A1's top 4 parents; CE@4 A0, A1 (K6)",
          [sum(i in par_d7[:4] for i in (27, 85)), int(ce_at(parents_ranked(QV["D-007"], 0, "chunks")[0], "D-007", 4)),
           int(ce_at(par_d7, "D-007", 4))], [1, 1, 0])
    check("§7 D-002-P1: rank of chunk 27, A0, A1 n = 5, A2 n = 5 (K6)",
          [1 + parents_ranked(QV["D-002-P1"], n, d)[0].index(27) for n, d in ((0, "chunks"), (5, "chunks+q"), (5, "q-only"))], [3, 1, 1])
    for qid, e_ranks, e_top, e_text in (("D-001", [3, 1, 1], 0.9311, "How much have global temperatures risen since the late 19th century?"),
                                        ("D-002", [3, 1, 1], 0.9869, "When was the Paris Agreement adopted?"),
                                        ("D-008", [2, 1, 1], 0.9368, "What is the Kigali Amendment?")):
        rr = [first_rel(parents_ranked(QV[qid], n, d)[0], qid) for n, d in ((0, "chunks"), (5, "chunks+q"), (5, "q-only"))]
        sc_, ow_, kd_, qt_ = mv_scores(QV[qid], 5, "chunks+q")
        i = int(np.argmax(sc_))
        check(f"§7 {qid}: gold rank A0, A1, A2 (n = 5); A1's top vector: score, kind, text (K7)", [rr, float(sc_[i]), kd_[i], qt_[i]],
              [e_ranks, e_top, "question", e_text], T4)
    cats = [[s["qid"], s["category"], RES[("A0", 0)][0][j], RES[("A1", 5)][0][j], RES[("A2", 5)][0][j]] for j, s in enumerate(ANS)]
    check("§7 per category: first relevant rank A0 -> A1 n = 5 -> A2 n = 5 (K8)", cats,
          [["D-001", "exact-term", 3, 1, 1], ["D-002", "factual-single-span", 3, 1, 1], ["D-003", "factual-single-span", 1, 2, 2],
           ["D-004", "exact-term", 1, 1, 1], ["D-005", "multi-span", 1, 2, 2], ["D-006", "vocabulary-mismatch", 1, 1, 1],
           ["D-007", "multi-hop", 2, 4, 4], ["D-008", "exact-term", 2, 1, 1]])

    # chart: the n-curve (n = 0 is A0, the same point for both arms); two panels, one per metric (no dual axis)
    fig = make_subplots(rows=1, cols=2, subplot_titles=("MRR@10", "Hit@1 (of 8)"), horizontal_spacing=0.12)
    xs = [0, 1, 3, 5, 10]
    for arm, colour, dash, name in (("A1", BLUE, "solid", "A1 chunks + questions"), ("A2", ORANGE, "dash", "A2 questions only")):
        ys = [RES[("A0", 0)]] + [RES[(arm, n)] for n in NS]
        fig.add_scatter(x=xs, y=[r[3] for r in ys], mode="lines+markers", name=name, line=dict(color=colour, width=2, dash=dash),
                        marker=dict(size=9), hovertemplate="n = %{x}: MRR@10 %{y:.3f}<extra>" + name + "</extra>", row=1, col=1)
        fig.add_scatter(x=xs, y=[r[1] for r in ys], mode="lines+markers", name=name, showlegend=False,
                        line=dict(color=colour, width=2, dash=dash), marker=dict(size=9),
                        hovertemplate="n = %{x}: Hit@1 %{y}<extra>" + name + "</extra>", row=1, col=2)
    fig.update_xaxes(title_text="questions per chunk (n = 0: chunks only, v0)", tickvals=xs)
    fig.update_yaxes(range=[0, 1], row=1, col=1)
    fig.update_yaxes(range=[0, 8.5], dtick=1, row=1, col=2)
    fig.update_layout(title="§7 · The n-curve on 8 LLM-drafted seeds (an observation, not a result)", height=430,
                      margin=dict(t=130), legend=dict(y=1.16))
    fig.show()
''')

# =====================================================================================================================
md(r"""
## 8 · Keyword and number queries

**What this rebuilds** (lesson step 8, K5, K8, K9). Generated questions paraphrase, and paraphrases drop the rare tokens a user may type: numbers and acronyms. **Rare-token retention** is the share of a chunk's numbers and acronyms that appear in at least one of its first n questions: 0.066, 0.143, 0.264, 0.549 for n = 1, 3, 5, 10.

The three exact-term seeds still pass with questions only, but only because this pack **happens** to contain a question naming each term (D-004's "DAC", D-008's "Kigali"), not because questions keep rare tokens in general. The fix is to keep the chunk vector (chunks + questions) or add BM25 (doc2query itself was a BM25 expansion; R1 owns hybrid search).
""")
code(r'''
RARE = re.compile(r"\b(?:\d[\d.,]*\d|\d|[A-Z]{2,}[A-Za-z0-9]*)\b")
RET = {}
for n in NS:
    kept = tot = 0
    for p, qs in enumerate(QS):
        rare = set(RARE.findall(TEXT[p]))
        joined = " ".join(qs[:n])
        tot += len(rare)
        kept += sum(bool(re.search(r"(?<![\w.])" + re.escape(r) + r"(?![\w])", joined)) for r in rare)
    RET[n] = (kept, tot)
check("§8 rare tokens kept in the first n questions, n = 1, 3, 5, 10; of (K5)", [[RET[n][0] for n in NS], RET[1][1]], [[6, 13, 24, 50], 91])
check("§8 rare-token retention n = 1, 3, 5, 10 (K5)", [round(RET[n][0] / RET[n][1], 3) for n in NS], [0.066, 0.143, 0.264, 0.549], T3)
if MODELS_OK:
    matched = {qid: FLATQ[int(np.argmax(EQ @ QV[qid]))][2] for qid in ("D-001", "D-004", "D-008")}
    print("   best generated question per exact-term seed:", matched)
    check("§8 exact-term seeds: questions only (n = 5) still finds them at rank (K8)",
          [RES[("A2", 5)][0][[s["qid"] for s in ANS].index(q)] for q in ("D-001", "D-004", "D-008")], [1, 1, 1])
    check("§8 ...because the pack names their terms: 'DAC' in D-004's match, 'Kigali' in D-008's (K9)",
          ["DAC" in matched["D-004"], "Kigali" in matched["D-008"]], [True, True])

fig = go.Figure(go.Scatter(x=list(NS), y=[round(RET[n][0] / RET[n][1], 3) for n in NS], mode="lines+markers+text",
                           text=[f"{RET[n][0]}/{RET[n][1]}" for n in NS], textposition="top left", line=dict(color=BLUE, width=2),
                           marker=dict(size=10), hovertemplate="n = %{x}: %{y:.3f} of the chunks' numbers and acronyms (%{text})<extra></extra>"))
fig.update_layout(title="§8 · Rare-token retention: most numbers and acronyms never reach the questions", height=380, showlegend=False,
                  xaxis=dict(title="questions per chunk, n", tickvals=list(NS)), yaxis=dict(title="share kept", range=[0, 1]))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 9 · Leakage: when the index already holds the eval question

**What this rebuilds** (lesson step 9, K9, K12). For each seed, `leak(i) = max_g cos(q_i, g)` over the 970 generated questions, plus a 3-gram containment. τ_cos would be the 10th percentile of ≥ 10 base↔paraphrase pairs (06 §6.2); 06 gives only one pair (D-002 vs D-002-P1, cos **0.7054**), so 0.7054 is a **provisional** τ_cos, with τ_ngram = 0.5.
- 10 of 970 generated questions are flagged; deleting them (A4, de-leaked A1 at n = 5) drops MRR@10 to **0.547**, below A0's 0.708.
- This is not copying: the helpers never saw the seeds. The same drafting habit (an LLM turning a chunk's key sentence into its obvious question) wrote both. On these 8 items the gain and the leak cannot be separated; the decisive slice is human-written, unflagged questions.
- The unanswerable D-009's best score rises from 0.3099 (best chunk) to **0.7939** (a question "What does IPCC stand for?"): a fixed score threshold for abstaining gets harder.
""")
code(r'''
if MODELS_OK:
    def grams(t, n=3):
        w = content_words(t)
        return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}

    tau_cos = float(QV["D-002"] @ QV["D-002-P1"])
    check("§9 the one paraphrase pair (D-002 vs D-002-P1): cos = provisional tau_cos (K9)", tau_cos, 0.7054, T4)
    EXP9 = {"D-001": (0.9311, 7, 1, 0.4929, 0.750, True), "D-002": (0.9869, 27, 3, 0.4606, 0.500, True),
            "D-003": (0.7101, 27, 4, 0.6497, 0.182, True), "D-004": (0.9653, 23, 7, 0.4210, 0.000, True),
            "D-005": (0.4723, 3, 7, 0.4272, 0.000, False), "D-006": (0.6007, 64, 9, 0.5331, 0.000, False),
            "D-007": (0.7565, 17, 5, 0.7094, 0.000, True), "D-008": (0.9368, 69, 4, 0.2598, 0.000, True),
            "D-009": (0.7939, 1, 8, 0.3099, 0.000, True), "D-010": (0.5826, 6, 4, 0.5196, 0.200, False),
            "D-002-P1": (0.7305, 27, 3, 0.6028, 0.000, True)}
    LEAK = {}
    for s in SEEDS + [VARIANT]:
        qq = QV[s["qid"]]
        sims = EQ @ qq
        r = int(np.argmax(sims))
        g3 = grams(s["question"])
        cont = max((len(g3 & grams(FLATQ[i][2])) / len(g3) if g3 else 0.0) for i in range(len(FLATQ)))
        flag = bool(sims[r] >= tau_cos or cont >= 0.5)
        LEAK[s["qid"]] = (float(sims[r]), FLATQ[r][0], FLATQ[r][1] + 1, float((EC @ qq).max()), cont, flag)
        e = EXP9[s["qid"]]
        check(f"§9 {s['qid']}: leak_cos, parent, q#, best chunk cos, 3-gram containment, flagged (K9)",
              [LEAK[s["qid"]][0], LEAK[s["qid"]][1], LEAK[s["qid"]][2], LEAK[s["qid"]][3], round(cont, 3), flag], list(e), T4)
    check("§9 D-004's and D-009's matched questions (K9)", [FLATQ[int(np.argmax(EQ @ QV[q]))][2] for q in ("D-004", "D-009")],
          ["What does DAC stand for?", "What does IPCC stand for?"])
    flagged_g = [r for r in range(len(FLATQ)) if max(float(EQ[r] @ QV[s["qid"]]) for s in SEEDS) >= tau_cos]
    check("§9 generated questions with cos >= tau_cos to any seed; by parent (K9)",
          [len(flagged_g), [list(t) for t in sorted(Counter(FLATQ[r][0] for r in flagged_g).items())]],
          [10, [[1, 1], [7, 1], [17, 1], [23, 1], [27, 2], [68, 1], [69, 3]]])
    keep = set(range(len(FLATQ))) - set(flagged_g)
    ranks4 = []
    for s in ANS:
        qq = QV[s["qid"]]
        best = {i: float(EC[i] @ qq) for i in range(N)}
        for r in keep:
            p, j, _ = FLATQ[r]
            if j < 5:
                best[p] = max(best[p], float(EQ[r] @ qq))
        ranks4.append(first_rel(sorted(best, key=lambda p: (-best[p], p)), s["qid"]))
    check("§9 A4 de-leaked A1 (n = 5): ranks; Hit@1, Hit@4, MRR@10 (K9)", [ranks4, *summary(ranks4)], [[8, 4, 1, 1, 2, 1, 2, 18], 3, 6, 0.547], T3)
    check("§9 de-leaked MRR@10 is below A0's", summary(ranks4)[2] < RES[("A0", 0)][3], True)
    check("§9 D-009 (unanswerable): best score, chunks only -> with questions (K12)", [best_c["D-009"], best_q["D-009"]], [0.3099, 0.7939], T4)

    fig = go.Figure()
    for flag, colour, name in ((True, ORANGE, "flagged"), (False, BLUE, "not flagged")):
        ks = [k for k in LEAK if LEAK[k][5] == flag]
        fig.add_scatter(x=[round(LEAK[k][3], 4) for k in ks], y=[round(LEAK[k][0], 4) for k in ks], mode="markers+text", name=name, text=ks,
                        textposition="middle right", marker=dict(size=12, color=colour, line=dict(width=2, color=SURFACE)),
                        hovertemplate="%{text}: leak_cos %{y:.4f}, best chunk %{x:.4f}<extra>" + name + "</extra>")
    fig.add_hline(y=tau_cos, line=dict(color=INK2, dash="dash"), annotation_text=f"provisional τ_cos = {tau_cos:.4f} (one pair)",
                  annotation_position="bottom right")
    fig.add_scatter(x=[0.2, 1.0], y=[0.2, 1.0], mode="lines", line=dict(color=GRID, width=1), showlegend=False, hoverinfo="skip")
    fig.update_layout(title="§9 · Leakage: each seed's best generated question vs its best chunk (above the diagonal: a question wins)",
                      height=440, xaxis=dict(title="best chunk cosine", range=[0.2, 0.8]), yaxis=dict(title="leak_cos: best generated question", range=[0.4, 1.02]))
    fig.show()
''')

# =====================================================================================================================
md(r"""
## 10 · What it costs, and when HyDE is cheaper

**What this rebuilds** (lesson step 10, K10, K11). One generator call per chunk: **97 calls** per rebuild. Input tokens are measured on the filled prompt for each chunk; output tokens on the pack's JSON at n = 3, 5 and 10 (o200k_harmony; Haiku's tokenizer differs, so its figures are approximate). Prices and limits are read from `prices_2026-10-17.json` (Groq $0.075 / $0.30 and Haiku $0.10 / $0.50 per million tokens, CITED 2026-10-17; Groq 8,000 TPM and 200,000 TPD, plan UNVERIFIED). The 300 reasoning tokens per call are an **assumption** (UNVERIFIED).

Then the break-even with HyDE (one call per query): the index side spends `N × rebuilds` calls a month, so it makes fewer calls once `Q_total > N × rebuilds`. A query adds **0** calls with questions in the index and **1** with HyDE. Last, the context sent to the answer model: k = 4 parents is still 4 chunks (627.9 vs 671.0 tokens).
""")
code(r'''
prices = json.loads(PRICES.read_text(encoding="utf-8"))
gkey = [k for k in prices["models"] if k.startswith("groq:")]
hkey = [k for k in prices["models"] if k.startswith("anthropic:")]
check("§10 price file: one Groq row, one Haiku row", [len(gkey), len(hkey)], [1, 1])
G, H = prices["models"][gkey[0]], prices["models"][hkey[0]]
tpm, tpd = prices["rate_limits"][gkey[0]]["tpm"], prices["rate_limits"][gkey[0]]["tpd"]
check("§10 prices per M tokens (Groq in, out; Haiku in, out) and Groq TPM, TPD (EXTERNAL)",
      [G["input"], G["output"], H["input"], H["output"], tpm, tpd], [0.075, 0.30, 0.10, 0.50, 8000, 200000], 1e-9)
if TOK_OK:
    inp = [TOK(tmpl.replace("{n_max}", "10").replace("{chunk_text}", t)) for t in TEXT]
    check("§10 prompt template alone (n_max = 10), tokens (K10)", TOK(tmpl.replace("{n_max}", "10").replace("{chunk_text}", "")), 241)
    check("§10 input tokens per call min, median, max; total (K10)", [min(inp), int(np.median(inp)), max(inp), sum(inp)], [309, 403, 433, 38095])
    REASON = 300                                      # assumed reasoning tokens per call (UNVERIFIED)
    EXP10 = {  # n: (median visible, [visible, +reasoning] for: output total, Groq $, Haiku $, tokens, TPM minutes, % of a day)
        3: (37, [(3560, 0.0039, 0.0056, 41655, 5.2, 20.8), (32660, 0.0127, 0.0201, 70755, 8.8, 35.4)]),
        5: (58, [(5613, 0.0045, 0.0066, 43708, 5.5, 21.9), (34713, 0.0133, 0.0212, 72808, 9.1, 36.4)]),
        10: (111, [(10797, 0.0061, 0.0092, 48892, 6.1, 24.4), (39897, 0.0148, 0.0238, 77992, 9.7, 39.0)])}
    COST = {}
    for n, (e_med, rows) in EXP10.items():
        out = [TOK(json.dumps({"questions": qs[:n]}, ensure_ascii=False)) for qs in QS]
        check(f"§10 n = {n}: visible output tokens per call, median (K10)", int(np.median(out)), e_med)
        for (label, extra), e in zip((("visible only", 0), (f"+{REASON} reasoning (assumed)", REASON)), rows):
            o_tot = sum(out) + extra * N
            g = (sum(inp) * G["input"] + o_tot * G["output"]) / 1e6
            h = (sum(inp) * H["input"] + o_tot * H["output"]) / 1e6
            t_tot = sum(inp) + o_tot
            COST[(n, extra)] = (g, h, t_tot)
            check(f"§10 n = {n} {label}: output total, Groq $, Haiku $ (K10)", [o_tot, g, h], list(e[:3]), T4)
            check(f"§10 n = {n} {label}: tokens, TPM floor (min), % of a day at TPD (K10)",
                  [t_tot, t_tot / tpm, 100 * t_tot / tpd], list(e[3:]), T1)
check("§10 HyDE break-even: index-side calls a month for 1, 2, 4, 30 rebuilds (K10)", [N * reb for reb in (1, 2, 4, 30)], [97, 194, 388, 2910])
check("§10 extra generator calls per query: questions in the index, HyDE (FORMULA)", [0, 1], [0, 1])

if MODELS_OK and TOK_OK:
    ctx = [sum(TOK(TEXT[i]) for i in parents_ranked(QV[s["qid"]], 5, "chunks+q")[0][:4]) for s in ANS]
    ctx0 = [sum(TOK(TEXT[i]) for i in parents_ranked(QV[s["qid"]], 0, "chunks")[0][:4]) for s in ANS]
    check("§10 context, k = 4 parents (A1 n = 5): tokens per seed, mean (K11)", [ctx, float(np.mean(ctx))],
          [[696, 625, 553, 522, 660, 633, 644, 690], 627.9], T1)
    check("§10 context, k = 4 chunks (A0): tokens per seed, mean (K11)", [ctx0, float(np.mean(ctx0))],
          [[696, 644, 644, 610, 730, 642, 700, 702], 671.0], T1)

# chart: the cost lanes, calls a month against queries a month
qx = list(range(0, 501, 5))
fig = go.Figure()
fig.add_scatter(x=qx, y=qx, mode="lines", name="HyDE: one call per query", line=dict(color=ORANGE, width=3),
                hovertemplate="%{x} queries a month: %{y} HyDE calls<extra></extra>")
for reb, colour, dash in ((1, AQUA, "dot"), (2, BLUE, "solid"), (4, YELLOW, "dash")):
    fig.add_scatter(x=qx, y=[N * reb] * len(qx), mode="lines", name=f"index time, rebuilt {reb}× a month ({N * reb} calls)",
                    line=dict(color=colour, width=2, dash=dash), hovertemplate=f"rebuilt {reb}× a month: {N * reb} calls, any number of queries<extra></extra>")
    fig.add_scatter(x=[N * reb], y=[N * reb], mode="markers", marker=dict(size=10, color=colour, line=dict(width=2, color=SURFACE)),
                    showlegend=False, hovertemplate=f"break-even at {N * reb} queries a month<extra></extra>")
fig.update_layout(title="§10 · Generator calls a month: index-time questions are a flat cost, HyDE grows with every query",
                  height=450, margin=dict(t=130), legend=dict(y=1.04),
                  xaxis=dict(title="queries a month"), yaxis=dict(title="generator calls a month", range=[0, 520]))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 11 · The upstream repo, read critically (and its arithmetic on this PDF)

**What this rebuilds** (lesson step 11, K2, K11). The `document_augmentation` notebook of RAG_Techniques, re-typed with the standard library only and run on the climate PDF:
- `read_pdf_to_string` joins the pages with **no separator**; `split_document` keeps only regex words (`\b\w+\b`) and joins them with spaces, so all punctuation is gone ("1.2 degrees" becomes "1 2 degrees").
- Its 4,000-word "documents" with 100 overlap give **3 parents** of 4,000 / 4,000 / 1,606 words (42.5% / 42.5% / 17.1% of the PDF), up to **4,271** tokens each. With k = 1, one parent is **6.4×** v0's whole k = 4 context. The notebook asks for "at least 40" questions per parent and reads the parent from a leftover loop variable.
- HyPE's notebook (cell 11 raises a SyntaxError, its saved outputs are stale; no metadata; `split("\n")`; `set()`) is cited and checked line by line in `i6_sources.py` (S-src), not re-run here.
""")
code(r'''
content = "".join(pages)                              # helper_functions.read_pdf_to_string: content += page.get_text()
words = re.findall(r"\b\w+\b", content)


def split_document(document, chunk_size, chunk_overlap):   # the notebook's cell 6, re-typed (stdlib only)
    tokens = re.findall(r"\b\w+\b", document)
    out = []
    for i in range(0, len(tokens), chunk_size - chunk_overlap):
        out.append(tokens[i:i + chunk_size])
        if i + chunk_size >= len(tokens):
            break
    return [" ".join(c) for c in out]


parents = split_document(content, 4000, 100)
check("§11 PDF text: characters, regex words, whitespace words (K2)", [len(content), len(words), len(content.split())], [72561, 9406, 9255])
check("§11 4000/100 parents: count, words each (K2)", [len(parents), [len(p.split()) for p in parents]], [3, [4000, 4000, 1606]])
check("§11 share of the PDF's regex words per parent (K2)", [round(len(p.split()) / len(words), 3) for p in parents], [0.425, 0.425, 0.171], T3)
frags = [split_document(p, 128, 16) for p in parents]
check("§11 128/16 fragments per parent; total (K2)", [[len(f) for f in frags], sum(map(len, frags))], [[36, 36, 15], 87])
check("§11 characters per parent (K2)", [len(p) for p in parents], [28589, 30553, 12537])
check("§11 punctuation characters: PDF text, parents (K2)",
      [sum(ch in ".,;:()%?!'\"-" for ch in content), sum(ch in ".,;:()%?!" for p in parents for ch in p)], [1493, 0])
check("§11 '1.2 degrees' in the PDF; in parent 0; '1 2 degrees' in parent 0 (K2)",
      ["1.2 degrees" in content, "1.2 degrees" in parents[0], "1 2 degrees" in parents[0]], [True, False, True])
if TOK_OK:
    ptok = [TOK(p) for p in parents]
    ctok = [TOK(t) for t in TEXT]
    check("§11 o200k_harmony tokens per parent (K2, K11)", ptok, [4271, 4237, 1687])
    check("§11 v0 chunk tokens min, median, max; mean (K2)", [min(ctok), int(np.median(ctok)), max(ctok), round(float(np.mean(ctok)), 1)],
          [68, 162, 192, 151.7], T1)
    if MODELS_OK:
        check("§11 the largest parent vs A0's mean k = 4 context (K11)", round(max(ptok) / float(np.mean(ctx0)), 1), 6.4, T1)

        labels = ["upstream parent 1 (k = 1)", "upstream parent 2", "upstream parent 3", "v0: k = 4 chunks (A0, mean)",
                  "k = 4 parents, chunks + q n = 5 (mean)"]
        vals = ptok + [round(float(np.mean(ctx0)), 1), round(float(np.mean(ctx)), 1)]
        fig = go.Figure(go.Bar(y=labels, x=vals, orientation="h", marker=dict(color=[ORANGE] * 3 + [BLUE, AQUA], line=dict(width=2, color=SURFACE)),
                               text=[f"{v:,}" for v in vals], textposition="outside", hovertemplate="%{y}: %{x:,} tokens<extra></extra>"))
        fig.update_layout(title="§11 · What reaches the answer model: one upstream parent is 6.4× v0's whole context", height=380,
                          xaxis=dict(title="tokens (o200k_harmony)", range=[0, 5000]), yaxis=dict(title="", autorange="reversed"), showlegend=False)
        fig.show()
''')

# =====================================================================================================================
md(r"""
## Result

The cell below counts the checks. Every `FAIL` names the value that disagreed; every `SKIPPED` says why it could not run (the optional cross-encoder section skips when the model is not in your local cache; that is not a failure).
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
