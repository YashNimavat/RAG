"""Build study/notebooks/I-CMP_granularity_verify.ipynb: the "verify it yourself" notebook for I-CMP (the granularity family).

The notebook rebuilds every measured number of the I-CMP lesson (study/lessons/I-CMP_granularity.html) from code, one
section per lesson step (1-9), and compares each value with the lesson's value in a `check(...)` line. The expected
values are copied from sources/verification/I-CMP/I-CMP_FACTS.md (K1-K12, §2; their output out_icmp_kit_measure.txt).
The code paths are those of icmp_kit_measure.py (same PDF text, chunker `recursive_spans`, heading rules, sentence
regex, MiniLM encodes with the same batch sizes, ties by lower index, the 07 I.2 `take_within_budget` with `break`,
exact McNemar, the paired bootstrap and comparison keys of contracts_check.py), so the numbers come out identical.

The 8 answerable draft seeds are `llm-draft`: every rank, CE value and Δ on them is an observation on draft seeds, not a
result. No I1-I6 per-technique run exists; the buildable arms are probes.

No Groq, Cohere or Claude call, no .env read, no network (MiniLM and its tokenizer load from the local Hugging Face cache,
offline; the MiniLM checks are SKIPPED with a reason if the model is not cached).

Run from rag_learning/ (the repo root):
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I-CMP/icmp_build_verify_nb.py
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I-CMP/icmp_verify_nb_run.py \
        > sources/verification/I-CMP/out_icmp_verify_nb_run.txt                         # executes it, saves outputs
"""
from pathlib import Path
from textwrap import dedent

import nbformat as nbf

WS = Path(__file__).resolve().parents[3]                      # rag_learning/ (the repo root)
OUT = WS / "study" / "notebooks" / "I-CMP_granularity_verify.ipynb"

CELLS = []


def md(s):
    CELLS.append(nbf.v4.new_markdown_cell(dedent(s).strip()))


def code(s):
    CELLS.append(nbf.v4.new_code_cell(dedent(s).strip()))


# =====================================================================================================================
md(r"""
# I-CMP · Verify it yourself: the granularity family, compared fairly

**What this is:** a notebook that rebuilds every measured number and chart of the I-CMP lesson from real code, so you can see each one being made and change the inputs.
**What this is not:** an I1–I6 bake-off. No per-technique run exists yet. The arms you build here are **probes**: v0, three I1 grid points, pages, uncapped sections, and an "I3 probe" (MiniLM, our regex splitter, p90, no cap). None of them is "the I2 arm" or "the I3 result". The notebook also makes **no API call**: no Groq, no Cohere, no Claude. I4 and I6 cost numbers are arithmetic on counts, not runs.

**How to use it.** Run all cells from the top (VS Code: *Run All*). The sections are numbered like the lesson's steps, 1 to 9. Each one has:
- a short note on what it verifies;
- a code cell that **computes** the values;
- `check(...)` lines: `PASS` means the code produced the number the lesson shows, `FAIL` means it did not;
- an interactive chart where one is worth seeing. Hover for values.

The last cell counts the checks. The whole notebook takes about half a minute to a minute on a CPU.

**Labels used for numbers.** *measured* = computed here from the climate PDF or a real model; *toy* = made-up inputs that show a mechanism; *formula* = arithmetic; *derived* = cost arithmetic on measured counts (with any assumption named).

**The draft seeds are not labels.** Step 6 and step 9 use the 8 answerable questions of `study/tools/examples/climate_seed_spans.jsonl` (06 §6.7). An LLM drafted them and you have not checked them yet. v0 already gets all 8 right at k = 4, so they cannot show any arm beating v0. Every rank, CE value and Δ on them is **an observation on 8 draft seeds, not a result**.

**Where the expected values come from.** `sources/verification/I-CMP/I-CMP_FACTS.md` (K1–K12 and §2), produced by `icmp_kit_measure.py` and `icmp_sources.py` in the same folder. MiniLM and its tokenizer load from the Hugging Face cache on this computer.
""")

code(r'''
# Setup: imports, paths, tokenizers, MiniLM and the shared helpers. Run this cell first.
import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")          # MiniLM may load from the local cache only: no network
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import ast
import bisect
import hashlib
import importlib.metadata as md
import json
import logging
import math
import re
import statistics
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pymupdf                                        # pinned 1.26.7
import tiktoken
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

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
UP = WS.parent / "upstream" / "RAG_Techniques"
PDF = UP / "data" / "Understanding_Climate_Change.pdf"
SEEDS = WS / "study" / "tools" / "examples" / "climate_seed_spans.jsonl"
sys.path.insert(0, str(WS / "study" / "tools"))
sys.path.insert(0, str(WS / "sources" / "verification" / "corrections"))
from embed_fit_check import recursive_spans          # noqa: E402  (07 H.1: reproduces v0's 97 chunks)
import contracts_check as cc                          # noqa: E402  (CE, relevance, paired bootstrap, comparison keys)

print("workspace:", WS)
print("python", sys.version.split()[0], {p: md.version(p) for p in
      ("pymupdf", "numpy", "tiktoken", "tokenizers", "transformers", "sentence-transformers", "torch", "plotly")})

# ---------------------------------------------------------------- check(): computed value vs the lesson's value
CHECKS, SKIPPED = [], []
T4, T3 = 5e-5, 5e-4                    # tolerances for values the lesson prints with 4 or 3 decimals


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
          + (f"  (tolerance {tol:g})" if tol else ""))


def skip(name, reason):
    SKIPPED.append((name, reason))
    print(f"SKIPPED  {name}: {reason}")


# ---------------------------------------------------------------- chart style (light surface, fixed colour order)
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
BLUE, ORANGE, AQUA, RED = "#2a78d6", "#eb6834", "#1baf7a", "#c8323c"
LIGHT = "#cfe0f5"
pio.templates["icmp"] = go.layout.Template(layout=dict(
    font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', size=13, color=INK2),
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, colorway=[BLUE, ORANGE, AQUA],
    xaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    yaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=INK2)),
    title=dict(x=0, xanchor="left", font=dict(size=15, color=INK)),
    margin=dict(l=70, r=30, t=90, b=60), hoverlabel=dict(font_size=12)))
pio.templates.default = "icmp"


def bar_style(colour):
    return dict(color=colour, line=dict(width=2, color=SURFACE))


# ---------------------------------------------------------------- environment and corpus (K1)
check("environment: pymupdf, numpy, tiktoken, tokenizers, sentence-transformers (K1)",
      [md.version(p) for p in ("pymupdf", "numpy", "tiktoken", "tokenizers", "sentence-transformers")],
      ["1.26.7", "2.5.3", "0.14.0", "0.23.2", "6.1.0"])
raw = PDF.read_bytes()
check("corpus: PDF sha256 and bytes (K1)", [hashlib.sha256(raw).hexdigest(), len(raw)],
      ["1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669", 206372])
doc = pymupdf.open(PDF)
pages = [pg.get_text() for pg in doc]
doc_text = "\n".join(pages)                           # page.get_text() per page, joined with "\n"
starts, pos = [], 0
for pg in pages:
    starts.append(pos)
    pos += len(pg) + 1


def q(xs, p):
    """Nearest-rank percentile (p in 0..100) of a sorted copy (as icmp_kit_measure.py)."""
    s = sorted(xs)
    return s[max(0, math.ceil(p / 100 * len(s)) - 1)]


def dist(xs):
    """[min, median, p95, max, mean rounded to 1 decimal]."""
    return [min(xs), statistics.median(xs), q(xs, 95), max(xs), round(sum(xs) / len(xs), 1)]


plen = [len(p) for p in pages]
check("corpus: pages, characters (K1)", [len(pages), len(doc_text)], [33, 72593])
check("corpus: page length min / median / max / mean (K1)", [min(plen), statistics.median(plen), max(plen),
      round(sum(plen) / len(plen), 1)], [636, 2225, 2494, 2198.8])

# ---------------------------------------------------------------- tokenizers: tiktoken (gpt2 falls back to r50k_base: same ranks)
ENC = {n: tiktoken.get_encoding(n) for n in ("cl100k_base", "o200k_harmony")}
try:
    ENC["gpt2"] = tiktoken.get_encoding("gpt2")
except Exception:                                     # gpt2 and r50k_base share the same ranks in tiktoken
    ENC["gpt2"] = tiktoken.get_encoding("r50k_base")
print("gpt2 encoding loaded as", ENC["gpt2"].name)


def n_tok(text, enc="o200k_harmony"):
    return len(ENC[enc].encode(text, disallowed_special=()))


# ---------------------------------------------------------------- MiniLM's WordPiece tokenizer and the model (local cache only)
MINILM = "sentence-transformers/all-MiniLM-L6-v2"
WP, WP_OK, MODEL, MINILM_OK = None, False, None, False
try:
    from tokenizers import Tokenizer
    from huggingface_hub import snapshot_download
    _snap = Path(snapshot_download(MINILM, local_files_only=True))
    WP = Tokenizer.from_file(str(_snap / "tokenizer.json"))
    WP.no_truncation()
    WP.no_padding()
    WP_OK = True
except Exception as e:  # noqa: BLE001
    skip("every WordPiece count", f"MiniLM's tokenizer is not in the local cache: {type(e).__name__}: {str(e)[:160]}")
try:
    import transformers
    transformers.utils.logging.set_verbosity_error()
    transformers.utils.logging.disable_progress_bar()
    from sentence_transformers import SentenceTransformer
    MODEL = SentenceTransformer(MINILM, device="cpu")
    MINILM_OK = WP_OK
except Exception as e:  # noqa: BLE001
    skip("every MiniLM number (I3 probe, K5 truncation, K6, K7)",
         f"MiniLM could not load offline: {type(e).__name__}: {str(e)[:160]}")


def n_wp(text, specials=True):
    return len(WP.encode(text, add_special_tokens=specials).ids)


print(f"\nsetup done in {time.time() - T0:.1f} s: {len(pages)} pages, {len(doc_text):,} characters; "
      f"WordPiece loaded: {WP_OK}; MiniLM loaded: {MINILM_OK}")
''')

# =====================================================================================================================
md(r"""
## 1 · Seven notebooks are not a comparison

**What this verifies** (lesson step 1, `#upstream`; facts §2). The repo has one notebook per granularity member. You read each one's setup from its own cells (0-based) and line them up:
- the **corpus** (the climate PDF per page or as one string, a `../data` folder, an inline essay, a Nike 10-K text);
- the **size unit** (characters, LlamaIndex tokens, sentence groups, gpt2 tokens, regex "words") and the size itself;
- the **embedder**, the **model ids** in the LLM column and **k**.

Across the seven notebooks there are 4 corpora, 5 size units, 6 embedder settings (one is "none"), 5 model ids in the LLM column (four chat models and Cohere's reranker, counted as the research §5.1 counts them) and k from 1 to 5. No two notebooks share a baseline. So no upstream number ranks one chunker against another.

The code reads the notebooks from `upstream/RAG_Techniques/all_rag_techniques/`. If that folder is missing on your computer, the section is SKIPPED with a reason. Only short identifiers are shown (the repo's licence is non-commercial).

No chart: the table is the point. Read it row by row and ask what differs.
""")
code(r'''
NBDIR = UP / "all_rag_techniques"
UPSTREAM = [
    # corpus, size unit, size (format, [(cell, regex)]), embedder, LLM-column model ids, k (cell, regex); each with evidence
    dict(nb="simple_rag", corpus="climate PDF", corpus_note="per page (PyPDFLoader)",
         ev_corpus=[(8, 'path = "data/Understanding_Climate_Change.pdf"'), (10, "PyPDFLoader(path)")],
         unit="characters", ev_unit=[(10, "length_function=len")],
         size=("{} / {}", [(10, r"chunk_size=(\d+), chunk_overlap=(\d+)")]),
         embedder="get_langchain_embedding_provider(OPENAI)", ev_emb=[(10, "get_langchain_embedding_provider(EmbeddingProvider.OPENAI)")],
         models=[], k=(13, r'"k": (\d+)')),
    dict(nb="choose_chunk_size", corpus="../data folder", corpus_note="first 20 docs (contents UNVERIFIED)",
         ev_corpus=[(4, 'data_dir = "../data"'), (6, "documents[0:20]")],
         unit="LlamaIndex tokens", ev_unit=[(10, "Settings.chunk_size = chunk_size")],
         size=("{} / {}", [(12, r"chunk_sizes = (\[[\d, ]+\])"), (10, r"Settings\.chunk_overlap = (chunk_size // \d+)")]),
         embedder="LlamaIndex default (not set)", ev_emb=[("absent", "embed_model")],
         models=[("gpt-4o", 8, 'model="gpt-4o"'), ("gpt-3.5-turbo", 10, 'OpenAI(model="gpt-3.5-turbo")')],
         k=(10, r"similarity_top_k=(\d+)")),
    dict(nb="semantic_chunking", corpus="climate PDF", corpus_note="one string (pages lost)",
         ev_corpus=[(8, 'path = "data/Understanding_Climate_Change.pdf"'), (10, "read_pdf_to_string(path)")],
         unit="sentence groups (no size cap)", ev_unit=[(12, "SemanticChunker(")],
         size=("{} {} (no cap)", [(12, r"breakpoint_threshold_type='(\w+)', breakpoint_threshold_amount=(\d+)")]),
         embedder="OpenAIEmbeddings()", ev_emb=[(12, "SemanticChunker(OpenAIEmbeddings()")],
         models=[], k=(16, r'"k": (\d+)')),
    dict(nb="proposition_chunking", corpus="Paul Graham essay", corpus_note="inline text, not the climate PDF",
         ev_corpus=[(7, "Paul Graham"), (7, 'sample_content = """')],
         unit="gpt2 tiktoken tokens", ev_unit=[(9, "from_tiktoken_encoder(")],
         size=("{} / {}", [(9, r"chunk_size=(\d+), chunk_overlap=(\d+)")]),
         embedder="nomic-embed-text:v1.5", ev_emb=[(9, "nomic-embed-text:v1.5")],
         models=[("llama-3.1-70b-versatile", 12, 'ChatGroq(model="llama-3.1-70b-versatile"'),
                 ("llama-3.1-70b-versatile", 15, 'ChatGroq(model="llama-3.1-70b-versatile"')],
         k=(18, r"'k': (\d+)")),
    dict(nb="contextual_chunk_headers", corpus="Nike 10-K", corpus_note="2023 annual report text",
         ev_corpus=[(8, "nike_2023_annual_report.txt")],
         unit="characters", ev_unit=[(9, "length_function=len")],
         size=("{} / {}", [(9, r"chunk_size: int = (\d+)"), (9, r"chunk_overlap=(\d+)")]),
         embedder="none (no index is built)", ev_emb=[("absent", "Embeddings("), ("absent", "as_retriever")],
         models=[("gpt-4o-mini", 11, 'MODEL_NAME = "gpt-4o-mini"'), ("rerank-english-v3.0", 13, 'MODEL = "rerank-english-v3.0"')],
         k=None),
    dict(nb="document_augmentation", corpus="climate PDF", corpus_note="one string",
         ev_corpus=[(13, 'path = "data/Understanding_Climate_Change.pdf"'), (13, "read_pdf_to_string(path)")],
         unit="regex words", ev_unit=[(6, r"re.findall(r'\b\w+\b'")],
         size=("windows {} / {}, fragments {} / {}", [(4, r"DOCUMENT_MAX_TOKENS = (\d+)"), (4, r"DOCUMENT_OVERLAP_TOKENS = (\d+)"),
                                                     (4, r"FRAGMENT_MAX_TOKENS = (\d+)"), (4, r"FRAGMENT_OVERLAP_TOKENS = (\d+)")]),
         embedder="OpenAIEmbeddings()", ev_emb=[(13, "embedding_model = OpenAIEmbeddings()")],
         models=[("gpt-4o-mini", 6, 'ChatOpenAI(model="gpt-4o-mini"')], k=(10, r'"k": (\d+)')),
    dict(nb="HyPE_Hypothetical_Prompt_Embeddings", corpus="climate PDF", corpus_note="per page (PyPDFLoader)",
         ev_corpus=[(7, 'PATH = "data/Understanding_Climate_Change.pdf"'), (13, "PyPDFLoader")],
         unit="characters", ev_unit=[(13, "length_function=len")],
         size=("{} / {}", [(7, r"CHUNK_SIZE = (\d+)"), (7, r"CHUNK_OVERLAP = (\d+)")]),
         embedder="text-embedding-3-small", ev_emb=[(7, 'EMBEDDING_MODEL_NAME = "text-embedding-3-small"')],
         models=[("gpt-4o-mini", 7, 'LANGUAGE_MODEL_NAME = "gpt-4o-mini"')], k=(17, r'"k": (\d+)')),
]

if NBDIR.is_dir():
    UPC = {r["nb"]: [("".join(c["source"]), c["cell_type"], c) for c in
                     json.loads((NBDIR / f"{r['nb']}.ipynb").read_text(encoding="utf-8"))["cells"]] for r in UPSTREAM}

    def found(nb, cell, sub):
        """`sub` is in cell `cell` (0-based); ("absent", sub) means no code cell of the notebook contains it."""
        if cell == "absent":
            return not any(sub in s for s, t, _ in UPC[nb] if t == "code")
        return sub in UPC[nb][cell][0]

    rows, evidence_ok = [], {}
    for r in UPSTREAM:
        nb = r["nb"]
        ev = r["ev_corpus"] + r["ev_unit"] + r["ev_emb"] + [(c, s) for _, c, s in r["models"]]
        evidence_ok[nb] = all(found(nb, c, s) for c, s in ev)
        groups = []
        for c, rx in r["size"][1]:
            m = re.search(rx, UPC[nb][c][0])
            groups.extend(m.groups() if m else ["?"])
        k = None
        if r["k"]:
            m = re.search(r["k"][1], UPC[nb][r["k"][0]][0])
            k = int(m.group(1)) if m else "?"
        rows.append({"notebook": nb, "corpus": f"{r['corpus']} ({r['corpus_note']})", "size unit": r["unit"],
                     "size / overlap": r["size"][0].format(*groups), "embedder": r["embedder"],
                     "LLM column": ", ".join(dict.fromkeys(m for m, _, _ in r["models"])) or "none", "k": k if k is not None else "—",
                     "_corpus": r["corpus"], "_k": k, "_models": [m for m, _, _ in r["models"]]})
    UNITS = pd.DataFrame(rows)
    display(UNITS.drop(columns=["_corpus", "_k", "_models"]).style.hide(axis="index")
            .set_properties(**{"text-align": "left", "white-space": "normal"}))

    for nb, ok in evidence_ok.items():
        check(f"§1 {nb}: every cited cell holds its evidence (§2)", ok, True)
    check("§1 size / overlap per notebook, read from the cells (§2)", dict(zip(UNITS["notebook"], UNITS["size / overlap"])),
          {"simple_rag": "1000 / 200", "choose_chunk_size": "[128, 256] / chunk_size // 5",
           "semantic_chunking": "percentile 90 (no cap)", "proposition_chunking": "200 / 50",
           "contextual_chunk_headers": "800 / 0", "document_augmentation": "windows 4000 / 100, fragments 128 / 16",
           "HyPE_Hypothetical_Prompt_Embeddings": "1000 / 200"})
    check("§1 k per notebook, read from the cells (§2; CCH builds no index)", {r["notebook"]: r["_k"] for r in rows},
          {"simple_rag": 2, "choose_chunk_size": 5, "semantic_chunking": 2, "proposition_chunking": 4,
           "contextual_chunk_headers": None, "document_augmentation": 1, "HyPE_Hypothetical_Prompt_Embeddings": 3})
    ks = [r["_k"] for r in rows if r["_k"] is not None]
    models = {m for ms in UNITS["_models"] for m in ms}
    check("§1 distinct corpora, size units, embedder settings, LLM-column model ids (research §5.1)",
          [UNITS["_corpus"].nunique(), UNITS["size unit"].str.replace(" (no size cap)", "", regex=False).nunique(),
           UNITS["embedder"].nunique(), len(models)], [4, 5, 6, 5])
    check("§1 k ranges over (min, max) (research §5.1)", [min(ks), max(ks)], [1, 5])
    hy11 = UPC["HyPE_Hypothetical_Prompt_Embeddings"][11][0]
    try:
        ast.parse(hy11)
        hy_syntax = False
    except SyntaxError:
        hy_syntax = True
    hy15 = "".join("".join(o.get("text", "")) for o in UPC["HyPE_Hypothetical_Prompt_Embeddings"][15][2].get("outputs", []))
    check("§1 HyPE: cell 11 is a SyntaxError as committed; cell 15's saved output shows 97/97 (§2)",
          [hy_syntax, "97/97" in hy15], [True, True])
    check("§1 proposition_chunking: the same llama-3.1-70b-versatile generates (cell 12) and grades (cell 15) (§2)",
          [found("proposition_chunking", 12, 'ChatGroq(model="llama-3.1-70b-versatile", temperature=0)'),
           found("proposition_chunking", 15, 'ChatGroq(model="llama-3.1-70b-versatile", temperature=0)'),
           found("proposition_chunking", 16, '"accuracy": 7, "clarity": 7, "completeness": 7, "conciseness": 7')],
          [True, True, True])
else:
    skip("§1 upstream units table", f"the upstream notebooks are not at {NBDIR} (clone RAG_Techniques next to rag_learning/)")
''')

# =====================================================================================================================
md(r"""
## 2 · Two axes and a return arrow

**What this verifies** (lesson step 2, `#axes`; no facts: this is the map). Every member changes one of two things:
- **boundary**: where the cuts go (fixed windows I1, document structure I2, embedding-distance breakpoints I3, LLM-written propositions I4);
- **representation**: what text stands for a unit in the index (a header I5, generated questions I6a and I6b).

A third choice cuts across both: **retrieve a small unit, return a bigger one** (I6 returns the parent chunk, I4 can point back to its source chunk, X1's window comes later). The table below is the map as data; it has no measured numbers.
""")
code(r'''
AXES = pd.DataFrame([
    ("I1 fixed / recursive", "boundary", "fixed windows", "the chunk"),
    ("I2 structure-aware", "boundary", "document structure (headings)", "the section chunk"),
    ("I3 semantic", "boundary", "embedding-distance breakpoints", "the chunk"),
    ("I4 propositions", "boundary", "LLM-written propositions", "the proposition, or its source chunk"),
    ("I5 contextual header", "representation", "header text prepended to the chunk", "the chunk (header optional)"),
    ("I6a document augmentation", "representation", "generated questions per document window", "the fragment it points to"),
    ("I6b HyPE", "representation", "generated questions per chunk", "the parent chunk"),
], columns=["member", "axis", "what changes", "returned unit"])
display(AXES.style.hide(axis="index").set_properties(**{"text-align": "left"}))
check("§2 members per axis: boundary, representation", AXES["axis"].value_counts().to_dict(), {"boundary": 4, "representation": 3})
check("§2 members whose returned unit differs from the retrieved one (the return arrow)",
      AXES.loc[AXES["returned unit"].str.contains("parent|source chunk|points to"), "member"].str.split().str[0].tolist(),
      ["I4", "I6a", "I6b"])
''')

# =====================================================================================================================
md(r"""
## 3 · Name the unit before the number

**What this verifies** (lesson step 3, `#units`; facts K2). "Size 500" means nothing until you name the unit. On the whole climate text (72,593 characters) you count:
- **tokens** with four tokenizers: MiniLM's WordPiece **11,694** (6.21 characters per token), cl100k **13,026** (5.57), gpt2 **14,375** (5.05), o200k_harmony **12,840** (5.65);
- **regex words** `\b\w+\b` (what `document_augmentation` calls "tokens"): **9,406** (7.72 characters per word);
- **I3 regex sentences** `(?<=[.?!])\s+` over the whole document: **612**, from 47 to 300 characters (median 111), none under 20;
- the windows two notebooks would build here: I6a's 4,000/100-word windows **3** and its 128/16-word fragments **84**; I4's 200/50 gpt2-token base chunks **96**.

So "1,000 tokens" (cl100k) is about 1,000 × 5.57 = **5,570 characters**, about 5.6 times v0's 1,000-character chunk (whose median is 149 WordPiece tokens, step 4).

**The chart** shows characters per unit for each tokenizer, and the regex word for comparison. Hover for the counts.
""")
code(r'''
SENT_RE = re.compile(r"(?<=[.?!])\s+")              # I3's splitter (LangChain SemanticChunker)
WORD_RE = re.compile(r"\b\w+\b")                     # document_augmentation cell 6 "tokens"


def sentence_spans(text):
    out, i = [], 0
    for m in SENT_RE.finditer(text):
        if m.start() > i:
            out.append((i, m.start()))
        i = m.end()
    if i < len(text):
        out.append((i, len(text)))
    return [(a, b) for a, b in out if text[a:b].strip()]


def word_windows(n_words, size, overlap):
    """document_augmentation cell 6 split_document: windows of `size` words, step size - overlap."""
    return len(range(0, n_words, size - overlap))


TOT = {n: n_tok(doc_text, n) for n in ("cl100k_base", "gpt2", "o200k_harmony")}
if WP_OK:
    TOT = {"WordPiece (MiniLM)": n_wp(doc_text, False), **TOT}
RHO = {n: round(len(doc_text) / v, 2) for n, v in TOT.items()}
words = WORD_RE.findall(doc_text)
sents = sentence_spans(doc_text)
slen = [b - a for a, b in sents]
g2 = ENC["gpt2"].encode(doc_text)
for n, v in TOT.items():
    print(f"   {n:20s} {v:6,} tokens = {len(doc_text) / v:.2f} characters per token")

check("§3 cl100k, gpt2, o200k_harmony tokens (K2)", [TOT["cl100k_base"], TOT["gpt2"], TOT["o200k_harmony"]], [13026, 14375, 12840])
check("§3 characters per token: cl100k, gpt2, o200k_harmony (K2)",
      [RHO["cl100k_base"], RHO["gpt2"], RHO["o200k_harmony"]], [5.57, 5.05, 5.65])
if WP_OK:
    check("§3 WordPiece tokens (no specials) and characters per token (K2)",
          [TOT["WordPiece (MiniLM)"], RHO["WordPiece (MiniLM)"]], [11694, 6.21])
else:
    skip("§3 WordPiece count", "MiniLM's tokenizer is not cached")
check("§3 regex words, characters per word (K2)", [len(words), round(len(doc_text) / len(words), 2)], [9406, 7.72])
check("§3 I3 regex sentences: count; min / median / p95 / max / mean characters (K2)", [len(sents), dist(slen)],
      [612, [47, 111, 189, 300, 117.2]])
check("§3 sentence segments under 20 characters (K2)", sum(x < 20 for x in slen), 0)
check("§3 I6a windows 4000/100 and fragments 128/16 words (K2)",
      [word_windows(len(words), 4000, 100), word_windows(len(words), 128, 16)], [3, 84])
check("§3 I4 base chunks, gpt2-token windows 200/50 (K2)", len(range(0, len(g2), 150)), 96)
check("§3 '1,000 tokens' (cl100k) in characters, and how many v0 chunks of 1,000 characters that is (formula)",
      [round(1000 * RHO["cl100k_base"]), round(1000 * RHO["cl100k_base"] / 1000, 1)], [5570, 5.6])

# chart: characters per unit
names = list(TOT) + ["regex word"]
vals = [RHO[n] for n in TOT] + [round(len(doc_text) / len(words), 2)]
counts = list(TOT.values()) + [len(words)]
fig = go.Figure(go.Bar(x=names, y=vals, text=[f"{v:.2f}" for v in vals], textposition="outside",
                       marker=dict(color=[BLUE] * len(TOT) + [MUTED], line=dict(width=2, color=SURFACE)),
                       customdata=counts, hovertemplate="%{x}: %{y:.2f} characters per unit<br>%{customdata:,} units in 72,593 characters<extra></extra>"))
fig.update_layout(height=430, showlegend=False, yaxis=dict(title="characters per unit", range=[0, 9]),
                  title="§3 · One text, five units: characters per token (measured, Corpus D, whole text)")
fig.show()
''')

# =====================================================================================================================
md(r"""
## 4 · Look at the spread, not the mean

**What this verifies** (lesson step 4, `#sizes`; facts K3, K4).

**The heading tree** (K3). You read every line of the PDF with its font size and bold flag. Every heading line is bold, and its size gives its level: 24 pt title **1**, 18 pt chapters **21** (Chapter 5 wraps onto 2 lines), 13.56 pt sections **68**, 12 pt bold sub-headings **192**: **282** headings. **192 of the 281** below the title (**68%**) are bold body-size text, so a size-only detector misses them. **11** heading names repeat (for example "paris agreement" on p.10 and p.23). All 282 are found in the text, and **75** sit glued inside an I3 regex sentence, because headings carry no full stop.

**The arms** (K4). You build seven sets of units on the same text:
- **v0** (the 07 recursive chunker, per page, 1,000/200 characters): 97 chunks;
- **I1 grid points** 500/100, 1500/300, 2000/400;
- **pages** (one unit per page) and **sections, uncapped** (cut at the title, chapter and section headings);
- the **I3 probe**: MiniLM embeds each sentence with its neighbours (buffer 1), a breakpoint goes where the distance to the next window is above its 90th percentile (**0.2768**), and there is no size cap: **62** chunks.

For each arm you count chunks, characters, MiniLM WordPiece tokens (with the two special tokens) and o200k tokens. MiniLM reads at most **256** tokens and was trained on 128. Truncation share = chunks over 256 / N: v0 **0**, 500/100 **0**, 1500/300 **6.2%**, 2000/400 **49.2%**, pages **97.0%**, sections **1.1%**, I3 probe **29.0%**. The I3 probe's largest chunk has **4,029** characters and **686** tokens; the smallest section has **30** characters.

**The chart** shows every unit's WordPiece token count per arm, with the 128 line (training length) and the 256 line (the cap: MiniLM never reads past it).
""")
code(r'''
# ---------------------------------------------------------------- K3: the heading tree from size + bold
LEVEL = {24.0: "title", 18.0: "chapter", 13.56: "section", 12.0: "sub"}
heads, wrapped = [], []                               # (level, text, page_no)
for pno, pg in enumerate(doc, 1):
    for b in pg.get_text("dict")["blocks"]:
        prev = None
        for ln in b.get("lines", []):
            sp = [s for s in ln["spans"] if s["text"].strip()]
            if not sp or not all(s["flags"] & 16 for s in sp):    # 16 = bold
                prev = None
                continue
            size = round(sp[0]["size"], 2)
            txt = " ".join("".join(s["text"] for s in ln["spans"]).split())
            if prev is not None and prev[0] == LEVEL[size] and prev[2] == pno:   # a heading wrapped onto two lines
                heads[-1] = (prev[0], prev[1] + " " + txt, pno)
                wrapped.append(heads[-1])
            else:
                heads.append((LEVEL[size], txt, pno))
            prev = heads[-1]
cnt = {lv: sum(h[0] == lv for h in heads) for lv in ("title", "chapter", "section", "sub")}
names_ = {}
for lv, t, p in heads:
    names_.setdefault(t.lower(), []).append((lv, p))
REPEAT = {k: v for k, v in names_.items() if len(v) > 1}
hpos, cur = [], 0                                     # headings mapped to doc_text offsets, in reading order
for lv, t, p in heads:
    m = re.compile(r"\s+".join(map(re.escape, t.split()))).search(doc_text, max(cur, starts[p - 1]))
    if m:
        hpos.append((m.start(), lv, t, p))
        cur = m.end()
sent_starts = [a for a, b in sents]
glued = 0
for o, lv, t, p in hpos:
    j = bisect.bisect_right(sent_starts, o) - 1
    a, b = sents[j]
    if a <= o < b and doc_text[a:o].strip():
        glued += 1

check("§4 headings per level: title, chapter, section, sub (K3)", cnt, {"title": 1, "chapter": 21, "section": 68, "sub": 192})
check("§4 headings in total; bold at body size of those below the title; share (K3)",
      [len(heads), cnt["sub"], len(heads) - 1, round(100 * cnt["sub"] / (len(heads) - 1))], [282, 192, 281, 68])
check("§4 the one heading that wraps onto two lines (K3)", [len(wrapped), wrapped[0][0], wrapped[0][1].split(":")[0]],
      [1, "chapter", "Chapter 5"])
check("§4 heading names that repeat (K3)", len(REPEAT), 11)
check("§4 repeats: paris agreement, smart grids, international agreements (level, page) (K3)",
      [REPEAT["paris agreement"], REPEAT["smart grids"], REPEAT["international agreements"]],
      [[["sub", 10], ["sub", 23]], [["sub", 8], ["sub", 22]], [["sub", 6], ["section", 23]]])
check("§4 headings located in the text; glued inside an I3 regex sentence (K3)", [len(hpos), glued], [282, 75])
for k in sorted(REPEAT):
    print(f"   repeated: {k:32s} {REPEAT[k]}")


# ---------------------------------------------------------------- K4: the arms
def per_page_chunks(size, overlap):
    out = []
    for pi, pg in enumerate(pages):
        for a, b in recursive_spans(pg, size, overlap):
            if pg[a:b].strip():
                out.append((starts[pi] + a, starts[pi] + b))
    return out


def section_units(levels=("title", "chapter", "section")):
    cuts = sorted({0} | {o for o, lv, t, p in hpos if lv in levels})
    return [(a, b) for a, b in zip(cuts, cuts[1:] + [len(doc_text)]) if doc_text[a:b].strip()]


ARMS = {
    "v0": per_page_chunks(1000, 200),
    "500/100": per_page_chunks(500, 100),
    "1500/300": per_page_chunks(1500, 300),
    "2000/400": per_page_chunks(2000, 400),
    "page": [(starts[i], starts[i] + len(p)) for i, p in enumerate(pages)],
    "sections": section_units(),
}
LABEL = {"v0": "v0 recursive 1000/200", "500/100": "I1 500/100", "1500/300": "I1 1500/300", "2000/400": "I1 2000/400",
         "page": "pages", "sections": "sections, uncapped", "I3 probe": "I3 probe (MiniLM, p90, no cap)"}

if MINILM_OK:   # the I3 probe: MiniLM sentence windows (buffer 1), threshold = p90 of consecutive distances, no size cap
    win = [" ".join(doc_text[a:b] for a, b in sents[max(0, i - 1): i + 2]) for i in range(len(sents))]
    E = MODEL.encode(win, normalize_embeddings=True, batch_size=64)
    dists = 1 - np.sum(E[:-1] * E[1:], axis=1)
    THR = float(np.percentile(dists, 90))
    brk = [i for i, d in enumerate(dists) if d > THR]
    groups, s0 = [], 0
    for i in brk:
        groups.append((sents[s0][0], sents[i][1]))
        s0 = i + 1
    groups.append((sents[s0][0], sents[-1][1]))
    ARMS["I3 probe"] = groups
    check("§4 I3 probe: windows embedded, distances, p90 threshold, breakpoints, chunks (K4)",
          [len(win), len(dists), round(THR, 4), len(brk), len(groups)], [612, 611, 0.2768, 61, 62], tol=T4)
else:
    skip("§4 I3 probe", "MiniLM is needed to embed the sentence windows")

SIZE = {}
for name, spans in ARMS.items():
    texts = [doc_text[a:b] for a, b in spans]
    s = {"n": len(spans), "chars": [len(t) for t in texts], "o200k": [n_tok(t) for t in texts],
         "cl_mean": round(sum(n_tok(t, "cl100k_base") for t in texts) / len(texts), 1),
         "ratio": round(sum(len(t) for t in texts) / len(doc_text), 3),
         "cross": sum(1 for a, b in spans if bisect.bisect_right(starts, a) != bisect.bisect_right(starts, max(a, b - 1))),
         "bytes": [128 + len(spans) * 384 * 4, 128 + len(spans) * 1536 * 4]}
    if WP_OK:
        s["wp"] = [n_wp(t) for t in texts]
        s["over"] = [sum(x > 128 for x in s["wp"]), sum(x > 256 for x in s["wp"]), sum(x > 512 for x in s["wp"])]
        s["share256"] = round(100 * s["over"][1] / len(spans), 1)
        s["past"] = sum(len(t) - WP.encode(t, add_special_tokens=False).offsets[253][1] for t, x in zip(texts, s["wp"]) if x > 256)
    SIZE[name] = s

EXP4 = {   # N; chars min/median/p95/max/mean; WordPiece min/median/p95/max/mean; over 128/256/512; % over 256; chars past;
           # o200k mean; cl100k mean; stored/doc chars; page crossings; bytes 384-d / 1,536-d      (K4, out_icmp_kit_measure.txt)
    "v0": (97, [393, 935, 996, 1000, 857.9], [59, 149, 174, 182, 140.1], [70, 0, 0], 0.0, 0, 151.7, 153.9, 1.146, 0, [149120, 596096]),
    "500/100": (201, [94, 449, 496, 500, 431.1], [17, 74, 90, 99, 71.4], [0, 0, 0], 0.0, 0, 76.0, 77.2, 1.194, 0, [308864, 1235072]),
    "1500/300": (65, [636, 1303, 1487, 1500, 1242.3], [109, 215, 260, 270, 202.3], [63, 4, 0], 6.2, 184, 219.8, 222.9, 1.112, 0, [99968, 399488]),
    "2000/400": (65, [393, 953, 1997, 2000, 1290.5], [59, 160, 357, 365, 209.5], [38, 32, 0], 49.2, 12333, 228.3, 231.6, 1.155, 0, [99968, 399488]),
    "page": (33, [636, 2225, 2468, 2494, 2198.8], [109, 354, 438, 443, 356.4], [32, 32, 0], 97.0, 21439, 389.1, 394.7, 1.000, 0, [50816, 202880]),
    "sections": (90, [30, 992, 1328, 1898, 806.6], [5, 156, 223, 358, 131.9], [62, 1, 0], 1.1, 565, 142.7, 144.7, 1.000, 28, [138368, 553088]),
    "I3 probe": (62, [78, 812.5, 2905, 4029, 1169.6], [14, 131.5, 456, 686, 190.6], [31, 18, 3], 29.0, 15246, 207.0, 210.1, 0.999, 28, [95360, 381056]),
}
for name, (n, ch, wp, over, share, past, o_mean, cl_mean, ratio, cross, byts) in EXP4.items():
    if name not in SIZE:
        skip(f"§4 {LABEL[name]}", "MiniLM did not load")
        continue
    s = SIZE[name]
    check(f"§4 {LABEL[name]}: N; characters min / median / p95 / max / mean (K4)", [s["n"], dist(s["chars"])], [n, ch])
    check(f"§4 {LABEL[name]}: o200k mean, cl100k mean, stored / document characters, units crossing a page (K4)",
          [round(sum(s["o200k"]) / s["n"], 1), s["cl_mean"], s["ratio"], s["cross"]], [o_mean, cl_mean, ratio, cross])
    check(f"§4 {LABEL[name]}: index bytes at 384-d and 1,536-d = 128 + N x d x 4 (K4, formula)", s["bytes"], byts)
    if WP_OK:
        check(f"§4 {LABEL[name]}: WordPiece min / median / p95 / max / mean (K4)", dist(s["wp"]), wp)
        check(f"§4 {LABEL[name]}: over 128 / 256 / 512; % over 256; characters past the cap (K4)",
              [s["over"], s["share256"], s["past"]], [over, share, past])
    else:
        skip(f"§4 {LABEL[name]}: WordPiece checks", "MiniLM's tokenizer is not cached")
if WP_OK and "I3 probe" in SIZE:
    check("§4 truncation shares at 256, in arm order (K4)", [SIZE[a]["share256"] for a in EXP4],
          [0.0, 0.0, 6.2, 49.2, 97.0, 1.1, 29.0])

    # chart: WordPiece tokens per unit, per arm, with the 128 and 256 lines
    fig = go.Figure()
    for name in EXP4:
        s = SIZE[name]
        fig.add_box(y=s["wp"], name=LABEL[name], boxpoints="all", jitter=0.45, pointpos=0, line=dict(color=BLUE, width=1.5),
                    fillcolor="rgba(42,120,214,0.10)", marker=dict(size=4, color=BLUE, opacity=0.55),
                    hovertemplate=f"{LABEL[name]}<br>%{{y}} WordPiece tokens<extra></extra>")
    fig.add_hline(y=128, line=dict(color=MUTED, dash="dot", width=1.5), annotation_text="128: MiniLM's training length",
                  annotation_position="top left", annotation_font=dict(color=INK2, size=12))
    fig.add_hline(y=256, line=dict(color=RED, dash="dash", width=1.5), annotation_text="256: the cap (MiniLM reads no further)",
                  annotation_position="top left", annotation_font=dict(color=RED, size=12))
    fig.update_layout(height=520, showlegend=False, yaxis=dict(title="MiniLM WordPiece tokens per unit (with [CLS], [SEP])"),
                      title="§4 · Size spread per arm: every unit's token count (measured, Corpus D; probes, not I1–I6 results)")
    fig.show()
''')

# =====================================================================================================================
md(r"""
## 5 · Index-time cost, query-time cost, index size

**What this verifies** (lesson step 5, `#cost`; facts K10, K11). Each member pays at **index time**: E embeds, L LLM calls, T input tokens. At **query time** every member pays the same: 1 query embed and 0 LLM calls. The index size is **bytes = 128 + N_vectors × d × 4**. All values below are **derived** from the counts measured above (prices from LLMOPS §6.2, checked 2026-10-17; assumptions named):
- **v0 / I1 / I2**: 0 LLM calls, N = 97 embeds. **I5 deterministic header**: 0 calls, 97 embeds (new text, new cache keys).
- **I3**: S + N = 612 + 97 = **709** embeds; at 96 texts per Cohere call, ⌈612/96⌉ + ⌈97/96⌉ = **9** calls; 0 LLM calls.
- **I4** (ASSUMPTION: 10 propositions per 200-token chunk): 96 generate + 960 grade = **1,056** LLM calls; 960 vectors, 5,898,368 bytes at 1,536-d.
- **I5 per-chunk context** (the whole document in each call; ASSUMPTION: 100 instruction tokens): 97 calls, 97 × (13,026 + 154 + 100) ≈ **1,288,153** input tokens ≈ **$0.097** (Groq gpt-oss-20b) or **$0.129** (Haiku 5.5). One request is about **13,280** tokens, more than an 8,000 tokens-per-minute limit (UNVERIFIED free-tier value).
- **I6a** document level: **3** calls; 84 fragments + 40 × 3 questions = **204** vectors. **I6b HyPE**: **97** calls; q = 8 questions per chunk (ASSUMPTION) → 776 vectors, 4,767,872 bytes.

**I6 vs Q2** (K11, formula): index-side questions cost N × rebuilds calls; query-side rewriting costs Q_total calls. Which is cheaper depends on both numbers.

**The chart** is the cost ladder on a log scale: LLM calls and embeds per member at index time. A bar that is missing is a **0** (a log axis cannot draw 0; the label says so).
""")
code(r'''
v0 = ARMS["v0"]
N, S = len(v0), len(sents)
doc_cl = n_tok(doc_text, "cl100k_base")
mean_chunk_cl = sum(n_tok(doc_text[a:b], "cl100k_base") for a, b in v0) / N
PROMPT = 100                                          # ASSUMPTION: instruction tokens per context call
i5_in = N * (doc_cl + mean_chunk_cl + PROMPT)
base4 = len(range(0, len(g2), 150))                   # I4 base chunks (gpt2 200/50)
P4 = base4 * 10                                       # ASSUMPTION: 10 propositions per base chunk
nw, nf = word_windows(len(words), 4000, 100), word_windows(len(words), 128, 16)


def index_bytes(n_vectors, d):
    return 128 + n_vectors * d * 4


check("§5 N chunks, S sentences, document cl100k tokens, mean chunk cl100k tokens (K10)",
      [N, S, doc_cl, round(mean_chunk_cl, 1)], [97, 612, 13026, 153.9])
check("§5 I3: embeds S + N; Cohere calls at 96 texts each (K10)", [S + N, math.ceil(S / 96) + math.ceil(N / 96)], [709, 9])
check("§5 I4: generate calls, grade calls, total LLM calls, embeds, bytes at 1,536-d (K10, ASSUMPTION 10 per chunk)",
      [base4, P4, base4 + P4, P4, index_bytes(P4, 1536)], [96, 960, 1056, 960, 5898368])
check("§5 I5 per-chunk context: calls, input tokens, one request's tokens (K10, ASSUMPTION 100 instruction tokens)",
      [N, round(i5_in), round(doc_cl + mean_chunk_cl + PROMPT)], [97, 1288153, 13280])
check("§5 I5 per-chunk context: USD at $0.075/M (Groq gpt-oss-20b) and $0.10/M (Haiku 5.5) (K10)",
      [round(i5_in * 0.075 / 1e6, 3), round(i5_in * 0.10 / 1e6, 3)], [0.097, 0.129], tol=1e-9)
check("§5 I5 per-chunk context: one request fits an 8,000 TPM limit? (K10)", doc_cl + mean_chunk_cl + PROMPT <= 8000, False)
check("§5 I6a: calls (one per 4,000-word window), fragments, questions (40 per window), vectors (K10)",
      [nw, nf, 40 * nw, nf + 40 * nw], [3, 84, 120, 204])
check("§5 I6b HyPE: calls; vectors at q = 5 and q = 8 (K10, ASSUMPTION q)", [N, N * 5, N * 8], [97, 485, 776])
check("§5 I6b HyPE bytes: q = 5 and q = 8 at 1,536-d; q = 5 and q = 8 at 384-d (K10)",
      [index_bytes(N * 5, 1536), index_bytes(N * 8, 1536), index_bytes(N * 5, 384), index_bytes(N * 8, 384)],
      [2979968, 4767872, 745088, 1192064])
check("§5 v0 index bytes at 1,536-d (K10 = C3 S6)", index_bytes(N, 1536), 596096)

# K11: I6 (index-time questions) vs Q2 (query-time rewriting)
K11 = []
for qtot, reb in ((50, 1), (500, 1), (500, 12), (5000, 12)):
    idx = N * reb
    K11.append([qtot, reb, idx, "index-side" if idx < qtot else "query-side"])
    print(f"   Q_total {qtot:5,}, rebuilds {reb:2}: index-side {idx:5,} calls vs query-side {qtot:5,} -> cheaper: {K11[-1][3]}")
check("§5 I6 vs Q2: (Q_total, rebuilds, index-side calls, cheaper side) (K11)", K11,
      [[50, 1, 97, "query-side"], [500, 1, 97, "index-side"], [500, 12, 1164, "query-side"], [5000, 12, 1164, "index-side"]])

# chart: the cost ladder (log y; zeros labelled)
LADDER = [("v0 / I1 / I2", 0, N), ("I3 semantic", 0, S + N), ("I4 propositions*", base4 + P4, P4),
          ("I5 header (deterministic)", 0, N), ("I5 per-chunk context*", N, N), ("I6a document questions", nw, nf + 40 * nw),
          ("I6b HyPE (q = 8)*", N, N * 8)]
xs = [m for m, _, _ in LADDER]
fig = go.Figure()
for label, idx, colour in (("LLM calls at index time", 1, ORANGE), ("embeds at index time", 2, BLUE)):
    ys = [r[idx] for r in LADDER]
    fig.add_bar(x=xs, y=[v if v > 0 else None for v in ys], name=label, marker=bar_style(colour),
                text=[f"{v:,}" for v in ys], textposition="outside",
                hovertemplate="%{x}<br>" + label + ": %{y:,}<extra></extra>")
for i, r in enumerate(LADDER):
    if r[1] == 0:
        fig.add_annotation(x=xs[i], y=0.15, yref="y", text="0 calls", showarrow=False, xshift=-14,
                           font=dict(size=11, color=ORANGE), textangle=-90)
fig.update_layout(barmode="group", height=500, yaxis=dict(type="log", title="count (log scale)", range=[-0.3, 3.6]),
                  title="§5 · The cost ladder on Corpus D (derived from measured counts; * = with a named ASSUMPTION)")
fig.show()
''')

# =====================================================================================================================
md(r"""
## 6 · Compare at the same token budget

**What this verifies** (lesson step 6, `#budget`; facts K6, K12). Bigger chunks bring more text per slot. So "CE@4" for a 2,000-character arm and for a 500-character arm compares different amounts of context. A fair comparison also fixes the **token budget B**: walk down the ranked list and keep each chunk while the total stays ≤ B; stop at the first one that does not fit (`take_within_budget`, 07 I.2, with `break`).

You set B = the mean o200k tokens of v0's top 4 over the seeds: **671**. Then, for every arm, MiniLM ranks the units for each of the 8 answerable draft seeds (exact cosine, ties to the lower index) and you score **CE** (complete evidence: every evidence group fully inside the kept chunks, `contracts_check.complete_evidence`) at fixed k = 4 and at B. **Observations on 8 draft seeds, not results:**
- v0: CE@4 **8/8**, MRR@10 0.708; at B it keeps 3.50 chunks on average and still has 8/8.
- 500/100: CE@4 **7/8**, but at B it keeps 7.75 chunks and reaches **8/8**. 1500/300: 7/8 at k = 4, **5/8** at B.
- pages: CE@4 **5/8** while using **1,590** context tokens (2.4 × B). At B only **1** page fits, and CE drops to **2/8**.
- I3 probe: its largest chunk (**769** tokens) is bigger than B. For D-001 the first-ranked chunk does not fit, so `break` returns **no chunk** (k = 0). B must be at least the largest unit, or the rule must skip instead of stop.

**The toy** (K12, made-up numbers): HyPE-style question vectors point back to parents. Seven hits → P3, P3, P7, P3, P1, P7, P2 with B = 640. Without dedup you keep P3, P3, P7 (480 tokens, **2** distinct parents). Dedup parents first: P3, P7, P1, P2 (620 tokens, **4** distinct).

**The chart** puts CE at k = 4 next to CE at B for every arm (left), and the context tokens each one used (right).
""")
code(r'''
def take_within_budget(ranked, ntok, budget):        # 07 I.2 logic: `break` at the first chunk that does not fit
    kept, used = [], 0
    for c in ranked:
        if used + ntok[c] > budget:
            break
        kept.append(c)
        used += ntok[c]
    return kept, used


# K12 toy first (no model needed)
toy_rank = ["P3", "P3", "P7", "P3", "P1", "P7", "P2"]   # 7 question vectors -> their parents, in rank order
ptok = {"P1": 160, "P2": 150, "P3": 170, "P7": 140}
naive, used_n = [], 0
for p in toy_rank:
    if used_n + ptok[p] > 640:
        break
    naive.append(p)
    used_n += ptok[p]
dedup = list(dict.fromkeys(toy_rank))
kept_d, used_d = take_within_budget(dedup, ptok, 640)
check("§6 toy, no dedup, B = 640: kept, tokens, distinct parents (K12)", [naive, used_n, len(set(naive))], [["P3", "P3", "P7"], 480, 2])
check("§6 toy, dedup parents first, B = 640: kept, tokens, distinct parents (K12)", [kept_d, used_d, len(kept_d)],
      [["P3", "P7", "P1", "P2"], 620, 4])

seeds = [json.loads(x) for x in SEEDS.read_text(encoding="utf-8").splitlines() if x.strip()]
ans = [s for s in seeds if s["answerable"]]
qids = [s["qid"] for s in ans]
check("§6 draft seeds: all, answerable, qids (K6)", [len(seeds), len(ans), qids],
      [10, 8, ["D-001", "D-002", "D-003", "D-004", "D-005", "D-006", "D-007", "D-008"]])
check("§6 every seed was created by an LLM draft, not checked by you (06 §6.7)", sorted({s["created_by"] for s in seeds}), ["llm-draft"])
GROUPS = {s["qid"]: [[[(starts[seg["page"] - 1] + seg["char_start"], starts[seg["page"] - 1] + seg["char_end"])
                       for seg in alt["segments"]] for alt in g["alternatives"]] for g in s["evidence_groups"]] for s in ans}
GD = {q_: [[[("d", a, b) for a, b in alt] for alt in g] for g in G] for q_, G in GROUPS.items()}   # contracts_check format
TX = {"d": doc_text}


def ce(qid, spans):
    return cc.complete_evidence(GROUPS[qid], spans, doc_text) if spans else 0


def span_cov(qid, spans):
    return cc.span_coverage(GD[qid], [("d", a, b) for a, b in spans], TX)


def relevant(qid, span):
    return bool(cc.rel(("d", *span), GD[qid], TX))


RES, RANK = {}, {}
if MINILM_OK:
    Qv = MODEL.encode([s["question"] for s in ans], normalize_embeddings=True)
    for name, spans in ARMS.items():
        V = MODEL.encode([doc_text[a:b] for a, b in spans], normalize_embeddings=True, batch_size=64)
        S_ = Qv @ V.T
        RANK[name] = [sorted(range(len(spans)), key=lambda j, r=r: (-r[j], j)) for r in S_]
    ntok_v0 = SIZE["v0"]["o200k"]
    ctx4 = [sum(ntok_v0[j] for j in RANK["v0"][i][:4]) for i in range(len(ans))]
    B = round(sum(ctx4) / len(ctx4))
    check("§6 v0 top-4 o200k tokens per seed; B = their mean (K6)", [ctx4, B], [[696, 644, 644, 610, 730, 642, 700, 702], 671])
    for name, spans in ARMS.items():
        ntok = SIZE[name]["o200k"]
        r = {k: [] for k in ("rank", "ce4", "cov4", "tok4", "uniq4", "ceB", "kB", "usedB", "uniqB")}
        for i, s in enumerate(ans):
            order = RANK[name][i]
            r["rank"].append(next((n + 1 for n, j in enumerate(order) if relevant(s["qid"], spans[j])), None))
            top4 = [spans[j] for j in order[:4]]
            r["ce4"].append(ce(s["qid"], top4))
            r["cov4"].append(span_cov(s["qid"], top4))
            r["tok4"].append(sum(ntok[j] for j in order[:4]))
            r["uniq4"].append(len({c for a, b in top4 for c in range(a, b)}))
            kept, used = take_within_budget(order, ntok, B)
            kc = [spans[j] for j in kept]
            r["ceB"].append(ce(s["qid"], kc))
            r["kB"].append(len(kept))
            r["usedB"].append(used)
            r["uniqB"].append(len({c for a, b in kc for c in range(a, b)}))
        r["hit4"] = sum(x is not None and x <= 4 for x in r["rank"])
        r["mrr"] = sum(1 / x for x in r["rank"] if x is not None and x <= 10) / len(ans)
        r["largest"] = max(ntok)
        RES[name] = r

    EXP6 = {  # ranks; Hit@4; MRR@10; CE@4 per seed; Span-Cov@4 mean; tokens@4 mean; unique chars@4 mean;
              # k at B per seed; CE@B per seed; realized tokens mean, min, max; unique chars@B mean; largest unit   (K6)
        "v0": ([3, 3, 1, 1, 1, 1, 2, 2], 8, 0.708, [1] * 8, 1.000, 671, 3412, [3, 4, 4, 4, 3, 4, 3, 3], [1] * 8, [589, 526, 644], 3030, 192),
        "500/100": ([1, 1, 2, 1, 2, 1, 4, 1], 8, 0.781, [1, 1, 1, 1, 1, 1, 0, 1], 0.938, 323, 1611, [8, 8, 8, 8, 7, 7, 8, 8], [1] * 8,
                    [614, 575, 641], 3097, 107),
        "1500/300": ([1, 3, 2, 1, 1, 1, 2, 2], 8, 0.729, [0, 1, 1, 1, 1, 1, 1, 1], 0.899, 934, 4979, [2, 2, 3, 3, 2, 2, 2, 2],
                     [0, 0, 1, 1, 1, 1, 0, 1], [525, 445, 644], 2840, 290),
        "2000/400": ([16, 4, 1, 2, 1, 1, 2, 2], 7, 0.594, [0, 1, 1, 1, 1, 1, 1, 1], 0.875, 1022, 5466, [3, 3, 3, 3, 2, 2, 2, 1],
                     [0, 0, 1, 1, 1, 1, 0, 0], [551, 333, 671], 2999, 397),
        "page": ([7, 2, 29, 13, 1, 1, 2, 2], 5, 0.455, [0, 1, 0, 0, 1, 1, 1, 1], 0.625, 1590, 8954, [1] * 8,
                 [0, 0, 0, 0, 1, 1, 0, 0], [420, 372, 486], 2299, 486),
        "sections": ([2, 2, 2, 1, 1, 1, 2, 8], 7, 0.641, [1, 1, 1, 1, 1, 1, 1, 0], 0.875, 620, 3328, [16, 3, 3, 4, 2, 3, 3, 7],
                     [1, 1, 1, 1, 1, 1, 1, 0], [563, 480, 640], 3003, 382),
        "I3 probe": ([1, 3, 1, 1, 1, 2, 2, 9], 7, 0.681, [1, 1, 1, 1, 0, 1, 1, 0], 0.812, 817, 4453, [0, 3, 2, 4, 4, 5, 2, 2],
                     [0, 1, 1, 1, 0, 1, 0, 0], [473, 0, 651], 2589, 769),
    }
    for name, (rk, hit, mrr, ce4, cov, tok4, uq4, kB, ceB, usedB, uqB, big) in EXP6.items():
        r = RES[name]
        L = LABEL[name]
        check(f"§6 {L}: first relevant rank per seed; Hit@4; MRR@10 (K6, observation)", [r["rank"], r["hit4"], round(r["mrr"], 3)],
              [rk, hit, mrr], tol=T3)
        check(f"§6 {L}: CE@4 per seed; Span-Coverage@4 mean (K6, observation)", [r["ce4"], round(sum(r["cov4"]) / 8, 3)], [ce4, cov],
              tol=T3)
        check(f"§6 {L}: context tokens at k = 4, unique characters at k = 4 (means, K6)",
              [sum(r["tok4"]) / 8, sum(r["uniq4"]) / 8], [tok4, uq4], tol=0.5)
        check(f"§6 {L}: k per seed at B = 671; CE@B per seed (K6, observation)", [r["kB"], r["ceB"]], [kB, ceB])
        check(f"§6 {L}: realized tokens at B mean / min / max; unique characters at B (K6)",
              [sum(r["usedB"]) / 8, min(r["usedB"]), max(r["usedB"]), sum(r["uniqB"]) / 8], usedB + [uqB], tol=0.5)
        check(f"§6 {L}: largest unit (o200k); B >= largest unit (K6)", [r["largest"], B >= r["largest"]], [big, B >= big])
    check("§6 mean k at B per arm (K6)", {n: round(sum(RES[n]["kB"]) / 8, 3) for n in EXP6},
          {"v0": 3.5, "500/100": 7.75, "1500/300": 2.25, "2000/400": 2.375, "page": 1.0, "sections": 5.125, "I3 probe": 2.75})
    check("§6 CE@4 and CE@B totals of 8, per arm (K6, observation)", {n: [sum(RES[n]["ce4"]), sum(RES[n]["ceB"])] for n in EXP6},
          {"v0": [8, 8], "500/100": [7, 8], "1500/300": [7, 5], "2000/400": [7, 4], "page": [5, 2], "sections": [7, 7], "I3 probe": [6, 4]})
    check("§6 pages: context tokens at k = 4 vs B (2.4 x B) (K6)", round(sum(RES["page"]["tok4"]) / 8 / B, 1), 2.4)
    i3_first = SIZE["I3 probe"]["o200k"][RANK["I3 probe"][0][0]]
    check("§6 I3 probe, D-001: tokens of its first-ranked chunk > B, so `break` keeps no chunk (K6)",
          [i3_first > B, RES["I3 probe"]["kB"][0], RES["I3 probe"]["ceB"][0]], [True, 0, 0])
    print(f"   I3 probe, D-001: first-ranked chunk has {i3_first} o200k tokens > B = {B}")

    # chart: CE at k = 4 vs at B, and the context tokens behind each
    xs = [LABEL[n] for n in EXP6]
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.1,
                        subplot_titles=("CE of 8 draft seeds: fixed k = 4 vs equal budget B = 671",
                                        "context tokens (o200k, mean over the seeds)"))
    fig.add_bar(x=xs, y=[sum(RES[n]["ce4"]) for n in EXP6], name="at k = 4", marker=bar_style(BLUE), row=1, col=1,
                hovertemplate="%{x}<br>CE@4 %{y}/8<extra></extra>")
    fig.add_bar(x=xs, y=[sum(RES[n]["ceB"]) for n in EXP6], name="at B = 671", marker=bar_style(ORANGE), row=1, col=1,
                customdata=[round(sum(RES[n]["kB"]) / 8, 2) for n in EXP6],
                hovertemplate="%{x}<br>CE@B %{y}/8<br>mean k at B %{customdata}<extra></extra>")
    fig.add_bar(x=xs, y=[round(sum(RES[n]["tok4"]) / 8) for n in EXP6], name="tokens at k = 4", marker=bar_style(BLUE),
                showlegend=False, row=1, col=2, hovertemplate="%{x}<br>%{y} tokens at k = 4<extra></extra>")
    fig.add_bar(x=xs, y=[round(sum(RES[n]["usedB"]) / 8) for n in EXP6], name="tokens at B", marker=bar_style(ORANGE),
                showlegend=False, row=1, col=2, hovertemplate="%{x}<br>%{y} tokens used at B<extra></extra>")
    fig.add_hline(y=B, line=dict(color=INK2, dash="dash", width=1.5), row=1, col=2, annotation_text="B = 671",
                  annotation_position="top left")
    fig.update_yaxes(title_text="CE (of 8)", range=[0, 8.8], dtick=2, row=1, col=1)
    fig.update_yaxes(title_text="tokens", row=1, col=2)
    fig.update_layout(barmode="group", height=500,
                      title="§6 · Equal k is not equal context (observation on 8 llm-draft seeds, not a result)")
    fig.show()
else:
    skip("§6 retrieval on the draft seeds (K6)", "MiniLM is needed to rank the units")
''')

# =====================================================================================================================
md(r"""
## 7 · What a cell may say

**What this verifies** (lesson step 7, `#cells`; fact K8). A cell of the comparison table holds one of these states:
- **measured**: a value with its CI, n, split and run id, on the same comparison keys as the champion, and significant under the family rule of step 9;
- **inconclusive**: the same keys, but the CI spans 0 or the exact p is above its Holm threshold;
- **not run (reason)**: no run exists, for example "needs 1,056 LLM calls";
- **not comparable (which key)**: a run exists but a comparison key differs, for example a subset of the qids;
- **derived**: cost arithmetic only, no metric;
- **book rating (no scale)**: its own column, never beside a measurement. `cell_state` never returns it.

**K8.** `contracts_check.comparison_keys_match` **refuses** the full 8-qid run against a 3-qid subset ("comparison key differs: qids") and **accepts** the subset against the champion rerun on the same 3 qids in reversed order (qids are compared as sets). So a v1.4 run on a subset can sit beside the champion only after the champion is rerun on those qids.

Below you write `cell_state(...)` and test it on all five states, then fill the comparison-table template honestly: every real I1–I6 arm is "not run" or "derived".
""")
code(r'''
COMMON = dict(dataset_sha256="d" * 64, snapshot_id="ea07572562ac", labels_sha256="l" * 64, split="dev", scorer_version="1")
full = cc.make_comparison_meta(qids=qids, **COMMON)
subset_q = [x for x in qids if x in ("D-002", "D-003", "D-004")]
sub = cc.make_comparison_meta(qids=subset_q, **COMMON)
try:
    cc.comparison_keys_match(full, sub)
    k8_full = "ACCEPTED"
except ValueError as e:
    k8_full = f"REFUSED: {e}"
rerun = cc.make_comparison_meta(qids=list(reversed(subset_q)), **COMMON)
check("§7 full 8 qids vs a 3-qid subset (K8)", k8_full, "REFUSED: comparison key differs: qids")
check("§7 subset vs the champion rerun on the same qids, reversed order (K8)", cc.comparison_keys_match(sub, rerun), True)


def mcnemar_exact(b, c):
    """Exact two-sided McNemar p: the binomial test on the b + c discordant pairs."""
    nd = b + c
    return min(1.0, 2 * sum(math.comb(nd, i) for i in range(min(b, c) + 1)) / 2 ** nd) if nd else 1.0


def cell_state(run=None, champion=None, *, reason=None, cost=None, alpha=0.05):
    """The state of one cell of the comparison table, as (state, text).

    run, champion: {"meta": comparison metadata, "scores": {qid: 0 or 1}, "labels": "human" or "llm-draft"}.
    No run: "derived" if a cost is given, else "not run" with the reason. A run on different comparison keys:
    "not comparable" naming the key. Otherwise "measured" only if the paired bootstrap CI excludes 0 AND the exact
    McNemar p <= alpha (the Holm threshold of this comparison); else "inconclusive"."""
    if run is None:
        return ("derived", f"derived: {cost} (cost only, no metric)") if cost else ("not run", f"not run: {reason or 'no reason given'}")
    try:
        cc.comparison_keys_match(champion["meta"], run["meta"])
    except ValueError as e:
        return "not comparable", f"not comparable: the key '{str(e).rsplit(': ', 1)[-1]}' differs"
    a, b_ = champion["scores"], run["scores"]
    bb = sum(a[x] == 1 and b_[x] == 0 for x in a)
    c_ = sum(a[x] == 0 and b_[x] == 1 for x in a)
    p = mcnemar_exact(bb, c_)
    delta, (lo, hi) = cc.ref_paired_bootstrap(a, b_, n_boot=2000, seed=0)
    state = "inconclusive" if (lo <= 0 <= hi or p > alpha) else "measured"
    text = f"{state}: Δ {delta:+.3f} [{lo:+.3f}, {hi:+.3f}], b {bb}, c {c_}, exact p {p:.4f} vs α {alpha:.4f}, n {len(a)}"
    if "llm-draft" in (run.get("labels"), champion.get("labels")):
        text += " (observation on llm-draft seeds)"
    return state, text


# tests: the five states
toy_q = [f"T-{i:02d}" for i in range(12)]
toy_meta = cc.make_comparison_meta(qids=toy_q, **COMMON)
toy_champ = {"meta": toy_meta, "scores": {x: int(i >= 10) for i, x in enumerate(toy_q)}, "labels": "human"}
toy_arm = {"meta": cc.make_comparison_meta(qids=list(reversed(toy_q)), **COMMON), "scores": {x: 1 for x in toy_q}, "labels": "human"}
toy_sub = {"meta": cc.make_comparison_meta(qids=toy_q[:5], **COMMON), "scores": {x: 1 for x in toy_q[:5]}, "labels": "human"}
TESTS = {
    "not run": cell_state(reason="needs 1,056 LLM calls (I4, K10)"),
    "derived": cell_state(cost="97 LLM calls, 1,288,153 input tokens (I5 per-chunk, K10)"),
    "not comparable": cell_state(toy_sub, toy_champ),
    "measured": cell_state(toy_arm, toy_champ, alpha=0.05 / 3),            # toy: b 0, c 10 of n 12
    "inconclusive": cell_state({**toy_arm, "scores": {x: int(i >= 9) for i, x in enumerate(toy_q)}}, toy_champ, alpha=0.05 / 3),
}
for want, (got, text) in TESTS.items():
    print(f"   {want:15s} -> {text}")
check("§7 cell_state: the five states on their test inputs (toy)", {k: v[0] for k, v in TESTS.items()},
      {"not run": "not run", "derived": "derived", "not comparable": "not comparable", "measured": "measured",
       "inconclusive": "inconclusive"})
check("§7 cell_state: 'not comparable' names the key; the toy 'measured' cell has b 0, c 10, exact p 0.0020",
      ["qids" in TESTS["not comparable"][1], "b 0, c 10, exact p 0.0020" in TESTS["measured"][1]], [True, True])
check("§7 cell_state: qid order alone never makes a cell 'not comparable' (K8)", cell_state(toy_arm, toy_champ)[0] != "not comparable", True)

if MINILM_OK:
    seeds_champ = {"meta": full, "scores": dict(zip(qids, RES["v0"]["ce4"])), "labels": "llm-draft"}
    page4 = cell_state({"meta": full, "scores": dict(zip(qids, RES["page"]["ce4"])), "labels": "llm-draft"}, seeds_champ, alpha=0.05 / 6)
    sub500 = cell_state({"meta": sub, "scores": {x: 1 for x in subset_q}, "labels": "llm-draft"}, seeds_champ)
    print(f"   pages vs v0 at k = 4 on the seeds -> {page4[1]}")
    check("§7 pages vs v0 at k = 4 on the seeds: the CI excludes 0 but the cell is 'inconclusive', marked as an observation (K7)",
          [page4[0], page4[1].endswith("(observation on llm-draft seeds)")], ["inconclusive", True])
    check("§7 a 3-qid subset run against the 8-qid champion: 'not comparable' (K8)", sub500[0], "not comparable")
else:
    skip("§7 cell_state on the seed probes", "MiniLM did not load")

# the comparison-table template: the honest state of every real arm today
TEMPLATE = pd.DataFrame([
    ("I1 grid (best of 37)", cell_state(reason="no E01x run yet; the probes above are not the I1 arm")[1],
     cell_state(cost="0 LLM calls, N embeds")[1]),
    ("I2 structure-aware", cell_state(reason="no I2 chunker run yet")[1], cell_state(cost="0 LLM calls, N embeds")[1]),
    ("I3 semantic", cell_state(reason="the I3 probe uses MiniLM and our splitter, not I3's setup")[1],
     cell_state(cost="709 embeds, 9 Cohere calls, 0 LLM calls")[1]),
    ("I4 propositions", cell_state(reason="needs about 1,056 LLM calls")[1], cell_state(cost="1,056 LLM calls (ASSUMPTION 10 per chunk)")[1]),
    ("I5 header (deterministic)", cell_state(reason="no run yet; title header useless on D (1 distinct of 97)")[1],
     cell_state(cost="0 LLM calls, 97 embeds")[1]),
    ("I5 per-chunk context", cell_state(reason="needs 97 LLM calls; one request > 8,000 TPM")[1],
     cell_state(cost="97 LLM calls, about 1,288,153 input tokens")[1]),
    ("I6b HyPE", cell_state(reason="branch; only for a vocabulary-mismatch bucket")[1], cell_state(cost="97 LLM calls, 776 vectors at q = 8")[1]),
], columns=["arm", "CE@4 at fixed k and at B", "index-time cost"])
TEMPLATE["book rating (no scale)"] = "own column"
display(TEMPLATE.style.hide(axis="index").set_properties(**{"text-align": "left", "white-space": "normal"}))
check("§7 template: every real arm's metric cell is 'not run'; every cost cell is 'derived'",
      [TEMPLATE["CE@4 at fixed k and at B"].str.startswith("not run").all(), TEMPLATE["index-time cost"].str.startswith("derived").all()],
      [True, True])
''')

# =====================================================================================================================
md(r"""
## 8 · Each member is a hypothesis about one failure

**What this verifies** (lesson step 8, `#targets`; facts K5, K3). A member is worth running only if your questions show the failure it targets. Corpus D shows why one member cannot be tested here:
- A **document-title header** (I5) gives every one of v0's 97 chunks the same text: **1 distinct value of 97**. It cannot separate anything on a single-document corpus.
- A **path header** (title > chapter > section at the chunk start) gives **71 distinct values of 97** (seq 27: "Understanding Climate Change > Chapter 6: Global and Local Climate Action"). It costs **0 LLM calls** and **97 embeds**. The header is 3 to 23 WordPiece tokens (mean 15.5), a share h/(h + c) of **0.103** on average (max 0.181), and **0** chunks go over 256 tokens after you prepend it.
- The 11 repeated heading names of K3 (step 4) are where a path header could help: the two "paris agreement" sub-headings sit under different chapters.

**The heat table** is the template: members × the M5 failure buckets. An arrow is a **hypothesis** (from 03 §4.1, "failure targeted"), not a measurement. Every arrow cell says "not run" until a run fills it with Δ CE@4 (n). The last column is "when not to use", which belongs to every row.
""")
code(r'''
def path_at(off):
    path = {}
    for o, lv, t, p in hpos:
        if o > off:
            break
        if lv == "title":
            path = {"title": t}
        elif lv == "chapter":
            path = {"title": path.get("title"), "chapter": t}
        elif lv == "section":
            path = {k: path.get(k) for k in ("title", "chapter")} | {"section": t}
    return " > ".join(v for v in (path.get("title"), path.get("chapter"), path.get("section")) if v)


title_h = [heads[0][1]] * len(v0)
path_h = [path_at(a) for a, b in v0]
check("§8 title header: distinct values of 97 (K5)", [len(set(title_h)), len(v0)], [1, 97])
check("§8 path header: distinct values of 97 (K5)", len(set(path_h)), 71)
check("§8 path header of seq 27 (K5)", path_h[27], "Understanding Climate Change > Chapter 6: Global and Local Climate Action")
pa = [o for o, lv, t, p in hpos if t.lower() == "paris agreement"]
check("§8 the two 'paris agreement' sub-headings get different chapter paths (K3)", path_at(pa[0]) != path_at(pa[1]), True)
print("   paris agreement paths:", " | ".join(path_at(o) for o in pa))
check("§8 deterministic header cost: LLM calls, embeds (K5)", [0, len(v0)], [0, 97])
if WP_OK:
    hw = [n_wp(h + "\n", False) for h in path_h]
    cw = [n_wp(doc_text[a:b]) for a, b in v0]
    share = [h / (h + c) for h, c in zip(hw, cw)]
    check("§8 path header WordPiece tokens min / median / p95 / max / mean (K5)", dist(hw), [3, 15, 22, 23, 15.5])
    check("§8 header token share h/(h + c): mean, max (K5)", [round(sum(share) / len(share), 3), round(max(share), 3)],
          [0.103, 0.181], tol=T3)
    check("§8 chunks over 256 after prepending the path (K5)", sum(h + c > 256 for h, c in zip(hw, cw)), 0)
else:
    skip("§8 header token counts", "MiniLM's tokenizer is not cached")

# the heat-table template: members x M5 buckets; arrow = hypothesis; every arrow cell "not run"
BUCKETS = ["parsing", "boundary", "vocabulary mismatch", "exact-term", "rank", "context noise", "unsupported claim",
           "should-have-abstained"]
HYP = {   # 03 §4.1 "failure targeted" -> the M5 bucket it is a hypothesis about; "when not to use" from 03's "expected to lose"
    "I1 fixed / recursive": (None, "baseline: every other arm is compared with it"),
    "I2 structure-aware": ("boundary", "PDFs whose layout extraction is poor"),
    "I3 semantic": ("boundary", "short documents; tables and lists; no size cap"),
    "I4 propositions": ("rank", "broad or synthesis questions; large corpora"),
    "I5 contextual header": ("rank", "single-document corpora (Corpus D: 1 distinct title)"),
    "I6a document augmentation": ("vocabulary mismatch", "questions the generator did not anticipate"),
    "I6b HyPE": ("vocabulary mismatch", "keyword- or number-heavy queries"),
}
HEAT = pd.DataFrame([[("↑ not run" if HYP[m][0] == b else "·") for b in BUCKETS] + [HYP[m][1]] for m in HYP],
                    index=list(HYP), columns=BUCKETS + ["when not to use"])
display(HEAT.style.map(lambda v: f"background-color: {LIGHT}; color: {INK}; font-weight: 600" if str(v).startswith("↑") else "",
                       subset=BUCKETS).set_properties(**{"text-align": "center"}, subset=BUCKETS))
check("§8 heat table: hypothesis cells, all 'not run'; no number anywhere",
      [int((HEAT[BUCKETS] == "↑ not run").to_numpy().sum()), bool(HEAT[BUCKETS].isin(["↑ not run", "·"]).to_numpy().all())], [6, True])
''')

# =====================================================================================================================
md(r"""
## 9 · Many arms, few questions

**What this verifies** (lesson step 9, `#family`; facts K7, K9).

**Paired with v0 on the seeds** (K7, observation). For each arm you count the discordant seeds: b = only v0 right, c = only the arm right. The exact two-sided McNemar p is the binomial test on b + c. **c = 0 for every arm**: no arm gets a seed right that v0 misses, because the seeds saturate v0. The page arm loses 3–0 at k = 4 (**p 0.25**) and 6–0 at B (**p 0.0312**). With Holm over these 6 arms, the first threshold is 0.05 / 6 = **0.0083**, so even 0.0312 is not significant. The paired bootstrap CI for the page arm at k = 4 is [−0.750, −0.125]: it excludes 0 although the exact p is 0.25. A bootstrap on 8 items is overconfident.

**Family statistics** (K9, formula):
- **FWER** = 1 − (1 − α)^m: one false adoption somewhere in m tests at α = 0.05: m = 3 **0.1426**, 5 **0.2262**, 12 **0.4596**.
- **Holm** for 3 arms: sort the p-values and compare them with **0.0167 / 0.025 / 0.05**; stop at the first that fails. Toy p-values A1 0.030, A2 0.012, A3 0.200: Holm rejects A2 only, then stops at A1 (0.030 > 0.025). Bonferroni (0.0167 each) also rejects A2 only.
- **MDE** ≈ 2.8 · √(b + c) / n: with n = 12 dev items and b + c = 4, the smallest CE@4 difference you can detect is **0.4667**. One item on n = 12 moves CE by **0.0833**.

Each v1.x effect is also **conditional**: Δ(arm | champion) is measured on the previous champion, not on v0, so every row records its base.

**The charts**: FWER as m grows, and the discordant counts per arm on the seeds.
""")
code(r'''
EXP7 = {  # metric -> arm -> (b, c, Δ, CI low, CI high, exact p)      (K7, out_icmp_kit_measure.txt)
    "ce4": {"500/100": (1, 0, -0.125, -0.375, 0.0, 1.0), "1500/300": (1, 0, -0.125, -0.375, 0.0, 1.0),
            "2000/400": (1, 0, -0.125, -0.375, 0.0, 1.0), "page": (3, 0, -0.375, -0.750, -0.125, 0.25),
            "sections": (1, 0, -0.125, -0.375, 0.0, 1.0), "I3 probe": (2, 0, -0.250, -0.500, 0.0, 0.5)},
    "ceB": {"500/100": (0, 0, 0.0, 0.0, 0.0, 1.0), "1500/300": (3, 0, -0.375, -0.750, -0.125, 0.25),
            "2000/400": (4, 0, -0.500, -0.875, -0.125, 0.125), "page": (6, 0, -0.750, -1.000, -0.500, 0.0312),
            "sections": (1, 0, -0.125, -0.375, 0.0, 1.0), "I3 probe": (4, 0, -0.500, -0.875, -0.125, 0.125)},
}
PAIR = {}
if MINILM_OK:
    for metric, arms in EXP7.items():
        base = dict(zip(qids, RES["v0"][metric]))
        for name, exp in arms.items():
            arm = dict(zip(qids, RES[name][metric]))
            b_ = sum(base[x] == 1 and arm[x] == 0 for x in qids)
            c_ = sum(base[x] == 0 and arm[x] == 1 for x in qids)
            m_, (lo, hi) = cc.ref_paired_bootstrap(base, arm, n_boot=2000, seed=0)
            PAIR[(metric, name)] = (b_, c_, m_, lo, hi, mcnemar_exact(b_, c_))
            where = "fixed k = 4" if metric == "ce4" else "equal B"
            check(f"§9 {LABEL[name]} vs v0, {where}: b, c, Δ, bootstrap CI, exact McNemar p (K7, observation)",
                  [b_, c_, round(m_, 3), round(lo, 3), round(hi, 3), round(PAIR[(metric, name)][5], 4)], list(exp), tol=T4)
    check("§9 c = 0 for every arm, at k = 4 and at B: no arm beats v0 on any seed (K7)", all(v[1] == 0 for v in PAIR.values()), True)
    holm6 = round(0.05 / 6, 4)
    check("§9 Holm over 6 arms: first threshold; the page arm's p at B is above it (K7)",
          [holm6, PAIR[("ceB", "page")][5] > 0.05 / 6], [0.0083, True])
    pg = PAIR[("ce4", "page")]
    check("§9 page arm at k = 4: the bootstrap CI excludes 0, the exact p is 0.25 (K7: overconfident at n = 8)",
          [pg[4] < 0, round(pg[5], 4)], [True, 0.25])
else:
    skip("§9 paired comparison on the seeds (K7)", "MiniLM did not load")
check("§9 MDE at n = 8, b + c = 4 (K7)", round(2.8 * math.sqrt(4) / 8, 3), 0.7)

# K9: family statistics (formula)
FWER = {m: round(1 - 0.95 ** m, 4) for m in (1, 3, 5, 12, 37, 48)}
check("§9 FWER = 1 - 0.95^m for m = 1, 3, 5, 12, 37, 48 (K9)", list(FWER.values()),
      [0.05, 0.1426, 0.2262, 0.4596, 0.8501, 0.9147], tol=T4)
check("§9 Holm thresholds for 3 arms (K9)", [round(0.05 / (3 - i), 4) for i in range(3)], [0.0167, 0.025, 0.05], tol=T4)


def holm(pvals, alpha=0.05):
    order = sorted(pvals, key=pvals.get)
    out, stop = {}, False
    for i, a in enumerate(order):
        t = alpha / (len(pvals) - i)
        ok = not stop and pvals[a] <= t
        stop = stop or not ok
        out[a] = (round(t, 4), "reject H0" if ok else "keep H0")
    return out


pv = {"A1": 0.030, "A2": 0.012, "A3": 0.200}         # TOY p-values
H = holm(pv)
print("   Holm on the toy:", H)
check("§9 Holm on the toy p-values: (threshold, decision) per arm (K9)", {a: list(v) for a, v in sorted(H.items())},
      {"A1": [0.025, "keep H0"], "A2": [0.0167, "reject H0"], "A3": [0.05, "keep H0"]})
check("§9 Bonferroni on the same toy, threshold 0.0167 (K9)", {a: ("reject" if p <= 0.05 / 3 else "keep") for a, p in pv.items()},
      {"A1": "keep", "A2": "reject", "A3": "keep"})
MDE = {(n, bc): round(2.8 * math.sqrt(bc) / n, 4) for n, bc in ((12, 4), (16, 4), (12, 9), (40, 9), (8, 4))}
check("§9 MDE = 2.8 x sqrt(b + c) / n for (12, 4), (16, 4), (12, 9), (40, 9), (8, 4) (K9)", list(MDE.values()),
      [0.4667, 0.35, 0.7, 0.21, 0.7], tol=T4)
check("§9 one item on n = 12 (K9)", round(1 / 12, 4), 0.0833, tol=T4)

# chart 1: FWER vs m
ms = list(range(1, 51))
fig = go.Figure()
fig.add_scatter(x=ms, y=[1 - 0.95 ** m for m in ms], mode="lines", name="FWER = 1 − 0.95^m", line=dict(color=BLUE, width=2.5),
                hovertemplate="m = %{x}<br>P(at least one false adoption) = %{y:.4f}<extra></extra>")
fig.add_scatter(x=list(FWER), y=list(FWER.values()), mode="markers+text", name="values in the lesson",
                marker=dict(size=9, color=ORANGE, line=dict(width=1, color=SURFACE)),
                text=[f"m {m}: {v:.4f}" for m, v in FWER.items()], textposition="bottom right", textfont=dict(size=11, color=INK2),
                hovertemplate="m = %{x}: %{y:.4f}<extra></extra>")
fig.add_hline(y=0.05, line=dict(color=MUTED, dash="dot"), annotation_text="α = 0.05 (one test)", annotation_position="top left")
fig.update_layout(height=460, xaxis=dict(title="m = tests at α = 0.05 with no true effect", range=[0, 52]),
                  yaxis=dict(title="family-wise error rate", range=[0, 1.02]),
                  title="§9 · Many arms: the chance of at least one false adoption (formula)")
fig.show()

# chart 2: discordant counts per arm (b = v0 only right; c = arm only right)
if MINILM_OK:
    arms_ = list(EXP7["ce4"])
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, subplot_titles=("fixed k = 4", "equal budget B = 671"))
    for col, metric in ((1, "ce4"), (2, "ceB")):
        fig.add_bar(x=[LABEL[a] for a in arms_], y=[PAIR[(metric, a)][0] for a in arms_], name="b: only v0 right",
                    marker=bar_style(BLUE), showlegend=col == 1, row=1, col=col,
                    customdata=[round(PAIR[(metric, a)][5], 4) for a in arms_],
                    hovertemplate="%{x}<br>b = %{y}<br>exact McNemar p %{customdata}<extra></extra>")
        fig.add_bar(x=[LABEL[a] for a in arms_], y=[PAIR[(metric, a)][1] for a in arms_], name="c: only the arm right",
                    marker=bar_style(ORANGE), showlegend=col == 1, row=1, col=col, hovertemplate="%{x}<br>c = %{y}<extra></extra>")
    fig.update_yaxes(title_text="seeds (of 8)", range=[0, 8], dtick=2, row=1, col=1)
    fig.update_layout(barmode="group", height=470,
                      title="§9 · Discordant seeds vs v0: c = 0 everywhere (observation on 8 llm-draft seeds, not a result)")
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
