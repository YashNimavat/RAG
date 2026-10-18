"""Build study/notebooks/I5_headers_verify.ipynb: the "verify it yourself" notebook for I5 (contextual chunk headers).

The notebook rebuilds every measured number and chart of the I5 lesson (study/lessons/I5_contextual_headers.html)
from code, one section per lesson step (1-12, spec section 3), and compares each value with the lesson's value in a
`check(...)` line. The expected values are copied from sources/verification/I5/I5_FACTS.md (K1-K16; their output
out_i5_kit_measure.txt). The code paths are the ones of i5_kit_measure.py (the 97 chunks through contracts_check and
the 07 modules, the heading extractor, the start and majority path rules, the four header arms, the BM25 preview, the
cost arithmetic, the K12 cache keys and the K13 toy), so the numbers come out identical.

MiniLM (sentence-transformers/all-MiniLM-L6-v2) loads from the local Hugging Face cache only (offline). When it is
not cached, the MiniLM cells (exact WordPiece counts per arm, Hit@4 / CE@4 / MRR@10 per arm, the D-002 / D-003
margins, Kendall tau, the margin dumbbell) print SKIPPED with the reason; everything else runs. No tokenizer file is
loaded otherwise: token figures outside the MiniLM cells are DERIVED from measured characters-per-token ratios.

No Groq, Cohere or Claude call, no .env read, no network.

Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I5/i5_build_verify_nb.py
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I5/i5_verify_nb_run.py \
        > sources/verification/I5/out_i5_verify_nb_run.txt                              # executes it, saves outputs
"""
from pathlib import Path
from textwrap import dedent

import nbformat as nbf

WS = Path(__file__).resolve().parents[3]                      # rag_learning/
OUT = WS / "study" / "notebooks" / "I5_headers_verify.ipynb"

CELLS = []


def md(s):
    CELLS.append(nbf.v4.new_markdown_cell(dedent(s).strip()))


def code(s):
    CELLS.append(nbf.v4.new_code_cell(dedent(s).strip()))


# =====================================================================================================================
md(r"""
# I5 · Verify it yourself: contextual chunk headers

**What this is:** a notebook that rebuilds every measured number and chart of the I5 lesson from real code, so you can see each one being made and change the inputs.
**What this is not:** the apply-it tool (`study/tools/header_fit_check.py`, which checks *your* documents) or the quiz. It makes **no API call**: no Groq, no Cohere, no Claude, and it never reads `.env`. Where the lesson uses an outside fact (Anthropic's post, the cookbook, dsRAG's README), this notebook shows it and says where it comes from; it does not pretend to re-measure it.

**How to use it.** Run all cells from the top (VS Code: *Run All*). The sections are numbered like the lesson's steps, 1 to 12. Each one has:
- a short note on what it verifies;
- a code cell that **computes** the values;
- `check(...)` lines: `PASS` means the code produced the number the lesson shows, `FAIL` means it did not, `SKIPPED` means the check could not run here and says why;
- an interactive chart where one is worth seeing. Hover for values.

The last cell counts the checks.

**Labels used for numbers.** *measured* = computed here from the real PDF, chunks or model; *toy* = made-up vectors or strings that show a mechanism; *formula* = arithmetic on counts and prices; *external* = from a published post, notebook or README, not re-run here; **DERIVED** = a token estimate made from characters with a measured ratio (6.21 characters per MiniLM WordPiece token, 5.65 per `o200k_harmony` token, 12,840 `o200k` tokens for the whole document). A DERIVED number is an estimate, not a count.

**The running example.** The climate PDF (Corpus D) cut into v0's **97 chunks** (the 07 recursive chunker, per page, 1,000 characters with 200 overlap), and two draft questions that are near-duplicates of each other:
- **D-002** "In what year was the Paris Agreement adopted?": gold chunk **27** (p.10, Chapter 6);
- **D-003** the NDC "regular reviews and updates" question: gold chunk **68** (p.23, Chapter 16).

Both pages have a heading called "Paris Agreement". Only the chapter and section above it tell them apart, which is what a header path adds. The 10 draft questions and their evidence spans come from 06 §6.7. They were drafted by an LLM and are not yet checked by you, so every rank here is an **observation on draft seeds, not an evaluation result**.

**MiniLM** (`all-MiniLM-L6-v2`) loads from the Hugging Face cache on this computer, offline. If it is not cached, the MiniLM cells print `SKIPPED` with the reason and the rest still runs. Everything else takes a few seconds.

**Where the expected values come from.** `sources/verification/I5/I5_FACTS.md`, sections K1–K16 (`i5_kit_measure.py`, output `out_i5_kit_measure.txt`). Prices: `study/tools/examples/prices_2026-10-17.json`.
""")

code(r'''
# Setup: imports, paths, the 97 chunks, the draft questions, the heading tree, the four header arms and the helpers.
# Run this cell first.
import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")          # MiniLM may load from the local cache only: no network
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

import collections
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
import pymupdf                                        # pinned 1.26.7
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from rank_bm25 import BM25Okapi

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
UPSTREAM_NB = WS.parent / "upstream" / "RAG_Techniques" / "all_rag_techniques" / "contextual_chunk_headers.ipynb"
PRICES = WS / "study" / "tools" / "examples" / "prices_2026-10-17.json"
L6 = "sentence-transformers/all-MiniLM-L6-v2"
WP_CPT = 6.21          # WordPiece characters per token on Corpus D (C2_FACTS K2, measured)
O200_CPT = 5.65        # o200k_harmony characters per token on Corpus D (P1_FACTS K5, measured)
O200_DOC = 12840       # o200k_harmony tokens in the whole PDF text (P1_FACTS K5, measured)
SEP = "\n\n"           # header / chunk separator in embed_text
ARMS = ("none", "title", "path", "major")
print("workspace:", WS)
print("python", sys.version.split()[0], {p: md.version(p) for p in ("pymupdf", "numpy", "rank-bm25", "plotly")})

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
          + (f"  (tolerance {tol:g})" if tol else ""))


def skip(name, reason):
    SKIPPED.append((name, reason))
    print(f"SKIPPED  {name}: {reason}")


def r3(x):
    return float(f"{x:.3f}")                          # the value as the facts print it (3 decimals)


def r4(x):
    return float(f"{x:.4f}")


def wp(chars):
    """DERIVED WordPiece token estimate from characters (C2 K2 ratio)."""
    return round(chars / WP_CPT)


# ---------------------------------------------------------------- chart style (light surface, fixed colour order)
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
BLUE, ORANGE, AQUA, RED = "#2a78d6", "#eb6834", "#1baf7a", "#c8323c"
LIGHT = "#cfe0f5"
pio.templates["i5"] = go.layout.Template(layout=dict(
    font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', size=13, color=INK2),
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, colorway=[BLUE, ORANGE, AQUA],
    xaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    yaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=INK2)),
    title=dict(x=0, xanchor="left", font=dict(size=15, color=INK)),
    margin=dict(l=70, r=30, t=90, b=60), hoverlabel=dict(font_size=12)))
pio.templates.default = "i5"

# ---------------------------------------------------------------- environment (K1)
check("environment: pymupdf, numpy, rank-bm25 (K1)", [md.version(p) for p in ("pymupdf", "numpy", "rank-bm25")],
      ["1.26.7", "2.5.3", "0.2.2"])
pdf_bytes = PDF.read_bytes()
check("corpus: PDF sha256 (K1)", hashlib.sha256(pdf_bytes).hexdigest(),
      "1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669")
doc = pymupdf.open(PDF)
pages = [p.get_text() for p in doc]

# ---------------------------------------------------------------- the 97 chunks, built exactly as i5_kit_measure.py (and P4)
sys.path.insert(0, str(WS / "sources" / "verification" / "corrections"))
import contracts_check as cc                          # noqa: E402  (06 recipe, 07 chunker loader, reference rel / ce)

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
DOC = "\n".join(pages)
TEXTS = {"climate": DOC}
N = len(chunks)
PAGE = [c["page_segments"][0]["page"] for c in chunks]
check("corpus: pages, characters, snapshot_id (K1)", [len(pages), len(DOC), SNAP], [33, 72593, "ea07572562ac"])
check("97 chunks: count, params_hash, chunks.jsonl sha256 prefix (K1)", [N, PH, SHA_JL[:16]],
      [97, "1ca9c5a3b548", "d4108b8936093394"])
lens = [len(c["text"]) for c in chunks]
check("97 chunks: characters min / median / max (K1)", [min(lens), int(statistics.median(lens)), max(lens)],
      [393, 935, 1000])

# the 10 draft seeds of 06 §6.7 (llm-draft: observations, never evaluation results)
SEEDS = [json.loads(line) for line in cc.code_blocks(cc.section(md06, "6.7 Draft seed"), "jsonl")[0].splitlines()
         if line.strip()]
for s in SEEDS:
    s["G"] = [[[("climate", starts[seg["page"] - 1] + seg["char_start"], starts[seg["page"] - 1] + seg["char_end"])
                for seg in alt["segments"]] for alt in g["alternatives"]] for g in s["evidence_groups"]]
ANS = [s for s in SEEDS if s["answerable"]]
BYQ = {s["qid"]: s for s in SEEDS}
REL = {s["qid"]: [i for i in range(N) if cc.rel(("climate", chunks[i]["char_start"], chunks[i]["char_end"]), s["G"], TEXTS)]
       for s in ANS}
check("draft seeds: 10, of which 8 answerable", [len(SEEDS), len(ANS)], [10, 8])
check("relevant chunks (any_overlap) per answerable seed (K1, K7)", REL,
      {"D-001": [7], "D-002": [27], "D-003": [68], "D-004": [23, 67, 68], "D-005": [3, 4], "D-006": [21],
       "D-007": [27, 85], "D-008": [69]})


def order(scores):
    """chunk seqs best first; ties broken by the smaller seq (the course rule)."""
    s = np.asarray(scores, float)
    return sorted(range(len(s)), key=lambda i: (-s[i], i))


def first_rel(ranking, qid):
    return next((r for r, i in enumerate(ranking, 1) if i in REL[qid]), None)


def ce_at(ranking, qid, k=4):
    top = [("climate", chunks[i]["char_start"], chunks[i]["char_end"]) for i in ranking[:k]]
    return cc.ce(BYQ[qid]["G"], top, TEXTS)


def summary(ranks, ces, k=4):
    hitk = sum(r is not None and r <= k for r in ranks)
    mrr = sum(1 / r for r in ranks if r is not None and r <= 10) / len(ranks)
    return hitk, sum(ces), round(mrr, 3)


# ---------------------------------------------------------------- the heading tree (font size + bold), as i5_kit_measure.py
LEVEL_BY_SIZE = {24.0: 0, 18.0: 1, 13.56: 2}          # title, chapter, section; 12 pt bold = subsection (3)
LEVEL_NAME = ["title", "chapter", "section", "subsection"]


def heading_level(span):
    size = round(span["size"], 2)
    bold = bool(span["flags"] & 16)
    if size in LEVEL_BY_SIZE and bold:
        return LEVEL_BY_SIZE[size]
    if size == 12.0 and bold:
        return 3
    return None


def extract_headings():
    """[(level, text, page, doc_start, doc_end)] in reading order. A heading that wraps over two lines of one block
    (Chapter 5) is merged. Offsets are located in the same page.get_text() string the chunks are cut from."""
    out = []
    for pno, page in enumerate(doc, 1):
        found = []
        for b in page.get_text("dict")["blocks"]:
            prev = None
            for ln in b.get("lines", []):
                sp = [s for s in ln["spans"] if s["text"].strip()]
                if not sp:
                    continue
                lv = {heading_level(s) for s in sp}
                if len(lv) != 1 or None in lv:
                    prev = None
                    continue
                lv = lv.pop()
                txt = "".join(s["text"] for s in sp).strip()
                if prev is not None and prev[0] == lv and lv == 1:
                    found[-1] = (lv, found[-1][1] + [txt])
                else:
                    found.append((lv, [txt]))
                prev = (lv,)
        cur = 0
        ptxt = pages[pno - 1]
        for lv, parts in found:
            a = ptxt.find(parts[0], cur)
            assert a >= 0, (pno, parts)
            e = a
            for p in parts:
                e = ptxt.find(p, e)
                assert e >= 0, (pno, p)
                e += len(p)
            cur = e
            out.append((lv, " ".join(parts), pno, starts[pno - 1] + a, starts[pno - 1] + e))
    return out


H = extract_headings()
TITLE = next(h[1] for h in H if h[0] == 0)


def path_at(pos):
    """the heading path in effect at document offset pos: the last heading of each level that starts at or before
    pos, deeper levels reset when a shallower heading starts."""
    path = [None, None, None, None]
    for lv, txt, _p, a, _e in H:
        if a > pos:
            break
        path[lv] = txt
        for d in range(lv + 1, 4):
            path[d] = None
    return tuple(path)


def first_nonspace(c):
    t = c["text"]
    k = len(t) - len(t.lstrip())
    return c["char_start"] + k


def inside(c):
    return [h for h in H if c["char_start"] <= h[3] < c["char_end"]]


def path_votes(c):
    """non-space characters of the chunk counted per heading path in effect at that character."""
    votes = collections.Counter()
    for i in range(c["char_start"], c["char_end"]):
        if not DOC[i].isspace():
            votes[path_at(i)] += 1
    return votes


def path_majority(c, votes=None):
    votes = path_votes(c) if votes is None else votes
    return max(votes.items(), key=lambda kv: (kv[1], kv[0] is not None))[0] if votes else path_at(c["char_start"])


def fmt_path(p, with_title=True):
    parts = [x for x in (p if with_title else p[1:]) if x]
    return " › ".join(parts)


VOTES = [path_votes(c) for c in chunks]
START = [path_at(first_nonspace(c)) for c in chunks]                 # start rule
MAJ = [path_majority(c, v) for c, v in zip(chunks, VOTES)]           # majority rule (the lesson's default)
HDR = {
    "none": ["" for _ in chunks],
    "title": [TITLE for _ in chunks],
    "path": [fmt_path(p) for p in START],
    "major": [fmt_path(p) for p in MAJ],
}
EMBED = {arm: [(h + SEP + c["text"]) if h else c["text"] for h, c in zip(HDR[arm], chunks)] for arm in HDR}
print(f"headings found: {len(H)}; header arms built: {list(HDR)}")

# ---------------------------------------------------------------- MiniLM: from the local Hugging Face cache only
MODEL, MINILM_OK, MINILM_WHY, _EMB = None, False, "", {}
try:
    from huggingface_hub import snapshot_download
    snapshot_download(L6, local_files_only=True)      # raises if the model is not in the local cache (no download)
except Exception as e:  # noqa: BLE001
    MINILM_WHY = (f"{L6} is not in the local Hugging Face cache ({type(e).__name__}); this notebook never downloads. "
                  "Run it where the model is cached")
else:
    try:
        import transformers
        transformers.utils.logging.disable_progress_bar()
        from sentence_transformers import SentenceTransformer
        MODEL = SentenceTransformer(L6, device="cpu")
        MINILM_OK = True
    except Exception as e:  # noqa: BLE001
        MINILM_WHY = f"MiniLM could not load offline: {type(e).__name__}: {str(e)[:160]}"
print("MiniLM:", "loaded from the local cache" if MINILM_OK else f"not available - {MINILM_WHY}")


def minilm_embeddings():
    """{arm: 97 x 384 unit vectors} and the 8 query vectors; computed once (MiniLM only)."""
    if not _EMB:
        enc = lambda texts: MODEL.encode(list(texts), normalize_embeddings=True, batch_size=32, show_progress_bar=False)
        _EMB["Q"] = enc(s["question"] for s in ANS)
        for arm in ARMS:
            _EMB[arm] = enc(EMBED[arm])
    return _EMB
''')

# =====================================================================================================================
md(r"""
## 1 · A chunk loses its context

**What this verifies** (lesson step 1, `#anon`; facts K4, K5, K9). A chunk is cut out of a page. It keeps its words but can lose three things: what a pronoun refers to, the heading it sits under, and the chapter. That is **contextual anonymity**. How bad is it on Corpus D?
- **0 of 97** chunks lack a heading line: the document has a heading every 257 characters, so every chunk carries at least one;
- **31 of 97** end on an **orphaned heading** (the last non-empty text is a heading whose body went to the next chunk); **16** of those sit at a page end, the same 16 that 07 D.8 counts;
- **46 of 97** start mid-sentence (first character lower-case), because the 200-character overlap cuts inside sentences;
- **chunk 34** (p.12) starts with **"It"**: "It can be used for tracking carbon credits…". The "it" is blockchain, named only in the heading above, which the chunk does not contain.

So Corpus D is **heading-dense**: expect a small header effect here. The text cuts (orphans, mid-sentence starts, "it") are real.

No chart: the counts and chunk 34's first line make the point.
""")
code(r'''
no_head = [i for i, c in enumerate(chunks) if not inside(c)]
orphan = [i for i, c in enumerate(chunks)
          if any(h[4] <= c["char_end"] and not DOC[h[4]:c["char_end"]].strip() for h in inside(c))]
page_end = [i for i in orphan if i == N - 1 or PAGE[i + 1] != PAGE[i]]
cut_start = [i for i, c in enumerate(chunks) if c["text"].lstrip()[:1].islower()]
WRE = re.compile(r"[a-z0-9]+")
PRON = {"it", "its", "this", "these", "they", "their", "such", "those", "that", "he", "she", "the"}
anon = [i for i in no_head if (w := WRE.findall(chunks[i]["text"].lower()[:40])) and w[0] in PRON]
pron_start = [i for i, c in enumerate(chunks) if (w := WRE.findall(c["text"].lower()[:40])) and w[0] in PRON]

check("§1 chunks with no heading line inside (K4)", len(no_head), 0)
check("§1 'anonymous' chunks: no heading inside and the first word a pronoun (K9)", len(anon), 0)
check("§1 orphaned-heading chunks, and how many sit at a page end (K4; 07 D.8 = 16)", [len(orphan), len(page_end)], [31, 16])
check("§1 the 16 page-end orphans (K4)", page_end, [2, 5, 8, 11, 14, 17, 20, 23, 29, 32, 50, 53, 59, 80, 89, 92])
check("§1 chunks that start mid-sentence (K9)", len(cut_start), 46)
c34 = chunks[34]
check("§1 chunk 34: page, span, first word (K4, K5)", [PAGE[34], c34["char_start"], c34["char_end"], c34["text"].split()[0]],
      [12, 25535, 26463, "It"])
check("§1 chunk 34 begins 'It can be used for tracking carbon credits' (K4)",
      c34["text"].lstrip().startswith("It can be used for tracking carbon credits"), True)
print(f"\n   chunk 34, first 120 characters: {c34['text'].lstrip()[:120]!r}")
print(f"   heading above chunk 34's first character: {START[34][3]!r} (not inside the chunk)")
print(f"   chunks whose first word is a pronoun or 'the' (they all hold a heading somewhere inside): {pron_start}")
''')

# =====================================================================================================================
md(r"""
## 2 · Where the header goes: `embed_text`, not `text`

**What this verifies** (lesson step 2, `#fields`; facts K1, K5). The header is written into a **separate field**:

`embed_text = header + "\n\n" + text`

and `text`, `char_start`, `char_end` stay as they are. Three reasons:
- the **span invariant** `DOC[char_start:char_end] == text` must keep holding, because CE@4 is scored on character spans; it holds for all 97;
- there are **three inputs** a header could change: the embedding input (06 v1.2, this lesson), the BM25 input (v2.0, previewed in step 9) and the generation input (a later arm). v1.2 changes the first one only;
- the header template is part of **`preproc_version`**, which goes into **`embed_hash`** (06 §3.2: 12 hex of the sha256 of the embedder settings), so each arm gets its own index folder. If two arms shared a `preproc_version`, the second would silently reuse the first one's vectors.

Queries are embedded as they are; only the chunk side gets a header.

No chart: the field layout is the point.
""")
code(r'''
check("§2 span invariant DOC[char_start:char_end] == text, all 97 (K1)",
      sum(DOC[c["char_start"]:c["char_end"]] == c["text"] for c in chunks), 97)
check("§2 the separator between header and text (K5)", SEP, "\n\n")
check("§2 text is recoverable from embed_text in every arm: the chunk itself never changes",
      [sum(e.endswith(c["text"]) and (not h or e == h + SEP + c["text"]) for e, h, c in zip(EMBED[a], HDR[a], chunks))
       for a in ARMS], [97, 97, 97, 97])
check("§2 example embed_text, path arm, chunk 34 (first 200 characters, K5)", EMBED["path"][34][:200],
      "Understanding Climate Change › Chapter 8: Future Directions and Innovations › Emerging Technologies › "
      "Blockchain for Climate Action\n\nIt can be used for tracking carbon credits, verifying renewable ene")


def embed_hash(preproc_version, provider="sentence-transformers", model_id=L6, revision="<pinned revision>",
               input_type="document", normalize=True):
    """06 §3.2: 12 hex of sha256(json.dumps({provider, model_id, revision, input_type, normalize, preproc_version}))."""
    return hashlib.sha256(json.dumps({"provider": provider, "model_id": model_id, "revision": revision,
                                      "input_type": input_type, "normalize": normalize,
                                      "preproc_version": preproc_version}, sort_keys=True).encode("utf-8")).hexdigest()[:12]


EH = {arm: embed_hash(f"v1.2-header-{arm}") for arm in ARMS}
for arm in ARMS:
    print(f"   arm {arm:6s} preproc_version v1.2-header-{arm:6s} -> embed_hash {EH[arm]} -> index/{SNAP}/{PH}/{EH[arm]}/")
check("§2 one preproc_version per arm gives four index folders", len(set(EH.values())), 4)
check("§2 the bug: leave the header template out of preproc_version and the none and path arms share one folder",
      len({embed_hash("v1.1") for _arm in ("none", "path")}), 1)
emb_key = lambda t, pv: hashlib.sha256(f"sentence-transformers|{L6}|<rev>|document|{pv}|{t}".encode("utf-8")).hexdigest()
check("§2 the embedding cache key (06 §3.2 text form) changes for every chunk between none and path",
      sum(emb_key(a, "v1.1") != emb_key(b, "v1.2-header-path") for a, b in zip(EMBED["none"], EMBED["path"])), 97)
print("\n   query side, unchanged:", repr(BYQ["D-002"]["question"]))
''')

# =====================================================================================================================
md(r"""
## 3 · Get the headings from the PDF

**What this verifies** (lesson step 3, `#tree`; fact K2). The PDF has no outline and its metadata title is **empty**, so the headings come from the text style. PyMuPDF's `page.get_text("dict")` gives every line with its spans, each with a font **size** and a **bold** flag (`flags & 16`). On Corpus D there are five line classes:

| size, bold | lines | level |
|---|---|---|
| 12 regular | 814 | body |
| 12 bold | 192 | subsection |
| 13.56 bold | 68 | section |
| 18 bold | 22 | chapter (21 chapters; Chapter 5's title wraps over 2 lines and is merged) |
| 24 bold | 1 | title, `Understanding Climate Change` |

That gives **282** headings (1 / 21 / 68 / 192), one every **257** characters; every page has 1 to 11 headings of levels 1–3 (median 9). **192 of 281 = 0.68** of the non-title headings are 12 pt bold, the same size as the body. A detector that needs "larger than the body text" finds only 90 and misses them all.

**The chart** is a heading strip: one column per page, one row per level, the number of headings in each cell. The top row marks pages that hold a section or subsection name used again under another chapter (step 4).
""")
code(r'''
check("§3 PDF metadata title (K2)", doc.metadata.get("title"), "")
cls = collections.Counter()
for page in doc:
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            sp = [s for s in ln["spans"] if s["text"].strip()]
            if sp:
                cls[tuple(sorted({(round(s["size"], 2), bool(s["flags"] & 16)) for s in sp}))] += 1
CLS = {" + ".join(f"{sz:g} {'bold' if bd else 'regular'}" for sz, bd in k): v
       for k, v in sorted(cls.items(), key=lambda kv: -kv[1])}
print("   line classes (size, bold):", CLS)
check("§3 line classes by (size, bold) (K2)", CLS,
      {"12 regular": 814, "12 bold": 192, "13.56 bold": 68, "18 bold": 22, "24 bold": 1})
cnt = collections.Counter(h[0] for h in H)
check("§3 headings by level: title / chapter / section / subsection, total (K2)",
      [cnt[0], cnt[1], cnt[2], cnt[3], len(H)], [1, 21, 68, 192, 282])
check("§3 the title and its length (K2)", [TITLE, len(TITLE)], ["Understanding Climate Change", 28])
check("§3 the merged two-line chapter (K2)", [h[1] for h in H if h[0] == 1 and h[1].startswith("Chapter 5")],
      ["Chapter 5: The Role of Technology in Climate Change Mitigation"])
per_page = collections.Counter(h[2] for h in H if h[0] >= 1)
pp = [per_page.get(p, 0) for p in range(1, len(pages) + 1)]
check("§3 headings (levels 1-3) per page min / median / max; pages with at least one (K2)",
      [min(pp), statistics.median(pp), max(pp), sum(x > 0 for x in pp)], [1, 9, 11, 33])
check("§3 one heading every N characters on average (K2)", round(len(DOC) / len(H)), 257)
check("§3 12 pt bold subsections / non-title headings (K2)", [cnt[3], len(H) - cnt[0], round(cnt[3] / (len(H) - cnt[0]), 2)],
      [192, 281, 0.68])
check("§3 a size-only detector (size > body 12 pt) finds levels 0-2 only (K2: 1 + 21 + 68)",
      sum(1 for h in H if h[0] <= 2), 90)

# reused names (computed fully in step 4; here only to mark the pages)
_cur = [None] * 4
_by_name = collections.defaultdict(list)
for lv, txt, p, a, e in H:
    _cur[lv] = txt
    for d in range(lv + 1, 4):
        _cur[d] = None
    if lv >= 2:
        _by_name[txt].append((p, _cur[1]))
_reused = {n: v for n, v in _by_name.items() if len({c for _p, c in v}) > 1}
reused_on_page = collections.defaultdict(list)
for n, v in _reused.items():
    for p, c in v:
        reused_on_page[p].append(f"{n} ({c.split(':')[0]})")

# chart: the heading strip
P = list(range(1, len(pages) + 1))
rows = ["subsection", "section", "chapter"]
z = [[sum(1 for h in H if h[2] == p and h[0] == LEVEL_NAME.index(r)) for p in P] for r in rows]
hov = [[f"p.{p} · {r}: {z[ri][pi]}<br>" + "<br>".join(h[1] for h in H if h[2] == p and h[0] == LEVEL_NAME.index(r))[:600]
        for pi, p in enumerate(P)] for ri, r in enumerate(rows)]
fig = go.Figure(go.Heatmap(z=z, x=P, y=rows, colorscale=[[0, "#f1f0ea"], [0.3, LIGHT], [1, BLUE]], xgap=2, ygap=2,
                           customdata=hov, hovertemplate="%{customdata}<extra></extra>",
                           colorbar=dict(title="headings", thickness=12)))
rp = sorted(reused_on_page)
fig.add_scatter(x=rp, y=["reused name"] * len(rp), mode="markers", name="a name used again under another chapter",
                marker=dict(symbol="diamond", size=12, color=ORANGE, line=dict(width=1, color=SURFACE)),
                customdata=["<br>".join(reused_on_page[p]) for p in rp],
                hovertemplate="p.%{x}<br>%{customdata}<extra></extra>")
for p in (10, 23):
    fig.add_annotation(x=p, y="reused name", text=f"p.{p}: Paris Agreement", showarrow=True, arrowhead=0, ax=0, ay=-34,
                       font=dict(size=12, color=INK), arrowcolor=INK2)
fig.update_layout(height=400, title="§3 · The heading tree, page by page (measured; font size + bold from get_text('dict'))"
                                    "<br><sup>282 headings: 1 title, 21 chapters, 68 sections, 192 subsections in "
                                    "body-size bold; every page has at least one</sup>",
                  xaxis=dict(title="page", dtick=1, showgrid=False),
                  yaxis=dict(categoryorder="array", categoryarray=["subsection", "section", "chapter", "reused name"],
                             showgrid=False))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 4 · The path, not the leaf

**What this verifies** (lesson step 4, `#path`; facts K3, K5). A heading name alone (the **leaf**) is not unique. **11** section or subsection names are used again under a different chapter, among them **Paris Agreement** (p.10 under Chapter 6, p.23 under Chapter 16). The two Paris headings get these **paths** (title › chapter › section › subsection):

- p.10: `Understanding Climate Change › Chapter 6: Global and Local Climate Action › International Collaboration › Paris Agreement`
- p.23: `Understanding Climate Change › Chapter 16: Global Cooperation and Governance › International Agreements › Paris Agreement`

They share the title and the leaf. Only the **chapter and section** separate them, so a leaf-only header would give D-002's and D-003's gold chunks the same words.

Over the 260 section and subsection headings, a full path is **75 / 120 / 168** characters (min / median / max), about **12 / 19 / 27** WordPiece tokens (DERIVED, 6.21 characters per token). The separator is ` › ` (U+203A with spaces).

No chart of its own: the reused names are the orange marks of step 3's strip.
""")
code(r'''
by_name = collections.defaultdict(list)
cur = [None] * 4
for lv, txt, p, a, e in H:
    cur[lv] = txt
    for d in range(lv + 1, 4):
        cur[d] = None
    if lv >= 2:
        by_name[txt].append((p, cur[1]))
reused = {n: v for n, v in by_name.items() if len({c for _p, c in v}) > 1}
REUSED = {n: "; ".join(f"p.{p} {c.split(':')[0]}" for p, c in v) for n, v in sorted(reused.items(), key=lambda kv: kv[1][0][0])}
for n, v in REUSED.items():
    print(f"   {n!r}: {v}")
check("§4 names reused under different chapters (K3)", len(REUSED), 11)
check("§4 the 11 reused names with their pages and chapters (K3)", REUSED, {
    "Marine Ecosystems": "p.5 Chapter 3; p.13 Chapter 9",
    "International Agreements": "p.6 Chapter 4; p.23 Chapter 16",
    "Research and Innovation": "p.7 Chapter 4; p.16 Chapter 10",
    "Smart Grids": "p.8 Chapter 5; p.22 Chapter 15",
    "Carbon Capture and Utilization": "p.8 Chapter 5; p.23 Chapter 15",
    "Carbon Utilization": "p.8 Chapter 5; p.23 Chapter 15",
    "International Collaboration": "p.10 Chapter 6; p.16 Chapter 10",
    "Paris Agreement": "p.10 Chapter 6; p.23 Chapter 16",
    "Policy and Governance": "p.12 Chapter 8; p.18 Chapter 12",
    "Youth Engagement": "p.13 Chapter 8; p.32 Chapter 21",
    "Nature-Based Solutions": "p.14 Chapter 9; p.26 Chapter 17"})
paris = [h for h in H if h[1] == "Paris Agreement"]
PARIS = {f"p.{h[2]}": fmt_path(path_at(h[3])) for h in paris}
check("§4 the two Paris Agreement paths (K3)", PARIS, {
    "p.10": "Understanding Climate Change › Chapter 6: Global and Local Climate Action › International Collaboration › Paris Agreement",
    "p.23": "Understanding Climate Change › Chapter 16: Global Cooperation and Governance › International Agreements › Paris Agreement"})
a10, a23 = (path_at(h[3]) for h in paris)
check("§4 which levels differ between the two Paris paths: title, chapter, section, leaf", [x != y for x, y in zip(a10, a23)],
      [False, True, True, False])
leaves = [fmt_path(path_at(h[3])) for h in H if h[0] >= 2]
lp = [len(x) for x in leaves]
check("§4 path header length over the section/subsection headings: count, chars min / median / max (K3)",
      [len(lp), min(lp), int(statistics.median(lp)), max(lp)], [260, 75, 120, 168])
check("§4 the same in WordPiece tokens (DERIVED, 6.21 chars/token, K3)", [wp(min(lp)), wp(statistics.median(lp)), wp(max(lp))],
      [12, 19, 27])
leaf_only = [p[3] or p[2] or p[1] or "" for p in START]
check("§4 leaf-only header (start rule) distinct over the 97 chunks (K5)", len(set(leaf_only)), 97)
check("§4 the path separator is U+203A with spaces", " › ".encode("unicode_escape").decode(), " \\u203a ")
''')

# =====================================================================================================================
md(r"""
## 5 · Which heading a chunk gets

**What this verifies** (lesson step 5, `#assign`; fact K4). A chunk of 1,000 characters on a page with a heading every 257 characters usually holds **several** headings (**94 of 97** hold two or more). Which path goes in its header? Three rules:
- **start rule:** the path in effect at the chunk's first non-space character;
- **majority rule:** the path that covers the most non-space characters of the chunk (the lesson's default);
- **all-inside:** the start path plus every heading that starts inside the chunk (long: 93 / 198 / 306 characters).

Start and majority disagree on **84 of 97** chunks. The running example shows why it matters:
- **chunk 27** (D-002 gold, p.10) starts on the Chapter 6 heading itself, so the start rule gives just `Chapter 6: Global and Local Climate Action`; the majority rule gives `Chapter 6 › International Collaboration › Paris Agreement`, where the answer is.
- **chunk 68** (D-003 gold, p.23): the start rule gives `Chapter 15 › Carbon Capture and Utilization › Direct Air Capture (DAC)`, the **wrong chapter** for its Paris text; the majority rule gives `Chapter 16 › International Agreements › Paris Agreement`.
- **chunk 34** (p.12) is the counter-case: it starts "It can be used for tracking carbon credits", and the start rule's `Chapter 8 › Emerging Technologies › Blockchain for Climate Action` names what "it" is, while the majority rule's `Chapter 8 › Policy and Governance › Integrated Climate Policies` does not. Neither rule is right for every chunk.

**The first chart** shows, for every chunk, the share of its non-space characters that sit under the start-rule path and under the majority path. **The second** compares header lengths under the three rules.
""")
code(r'''
starts_with_head = [i for i, c in enumerate(chunks) if any(h[3] == first_nonspace(c) for h in H)]
diff = [i for i in range(N) if START[i] != MAJ[i]]
multi = [i for i, c in enumerate(chunks) if len(inside(c)) >= 2]
check("§5 chunks containing >= 2 headings (K4)", len(multi), 94)
check("§5 chunks whose first non-space character starts a heading (K4)", len(starts_with_head), 21)
check("§5 start-rule path != majority-rule path (K4)", len(diff), 84)
check("§5 the 13 chunks where the rules agree (K4)", [i for i in range(N) if i not in diff],
      [4, 20, 21, 32, 38, 39, 47, 55, 74, 75, 86, 88, 96])

EXAMPLES = {
    27: dict(span=[20555, 21506], page=10,
             start="Chapter 6: Global and Local Climate Action",
             major="Chapter 6: Global and Local Climate Action › International Collaboration › Paris Agreement",
             inside=["Chapter 6: Global and Local Climate Action", "International Collaboration",
                     "United Nations Framework Convention on Climate Change (UNFCCC)", "Paris Agreement",
                     "National Strategies", "Carbon Pricing"]),
    68: dict(span=[50756, 51413], page=23,
             start="Chapter 15: Climate Change and Technology › Carbon Capture and Utilization › Direct Air Capture (DAC)",
             major="Chapter 16: Global Cooperation and Governance › International Agreements › Paris Agreement",
             inside=["Chapter 16: Global Cooperation and Governance", "International Agreements", "Paris Agreement"]),
    34: dict(span=[25535, 26463], page=12,
             start="Chapter 8: Future Directions and Innovations › Emerging Technologies › Blockchain for Climate Action",
             major="Chapter 8: Future Directions and Innovations › Policy and Governance › Integrated Climate Policies",
             inside=["Bioengineering", "Policy and Governance", "Integrated Climate Policies", "International Cooperation"]),
}
for i, ex in EXAMPLES.items():
    c = chunks[i]
    tag = {27: "D-002 gold", 68: "D-003 gold", 34: "the counter-case"}[i]
    check(f"§5 chunk {i} ({tag}): page and span (K4)", [PAGE[i], c["char_start"], c["char_end"]], [ex["page"], *ex["span"]])
    check(f"§5 chunk {i}: start rule (K4)", fmt_path(START[i], False), ex["start"])
    check(f"§5 chunk {i}: majority rule (K4)", fmt_path(MAJ[i], False), ex["major"])
    check(f"§5 chunk {i}: headings inside (K4)", [h[1] for h in inside(c)], ex["inside"])
check("§5 chunk 68: the start rule names the wrong chapter for D-003's Paris text (K4)",
      [START[68][1].split(":")[0], MAJ[68][1].split(":")[0], "Paris" in chunks[68]["text"]], ["Chapter 15", "Chapter 16", True])

ALL_IN = [fmt_path(START[i]) + "".join(f" | {h[1]}" for h in inside(c) if h[3] > first_nonspace(c))
          for i, c in enumerate(chunks)]
RULES = {"start": HDR["path"], "majority": HDR["major"], "all-inside": ALL_IN}
RULE_STATS = {}
for name, hs in RULES.items():
    L = [len(h) for h in hs]
    est = [wp(len(h) + 2 + len(c["text"])) + 2 for h, c in zip(hs, chunks)]
    RULE_STATS[name] = [min(L), int(statistics.median(L)), max(L), len(set(hs)), sum(x > 256 for x in est)]
    print(f"   rule {name:10s}: header chars min/median/max {RULE_STATS[name][:3]}; distinct {RULE_STATS[name][3]};"
          f" header+chunk over 256 (DERIVED) {RULE_STATS[name][4]}")
check("§5 header length by rule: chars min / median / max, distinct, over 256 DERIVED (K4)", RULE_STATS,
      {"start": [28, 120, 168, 97, 0], "majority": [67, 123, 168, 96, 0], "all-inside": [93, 198, 306, 97, 0]})

# chart 1: the share of each chunk's non-space characters under the start path and under the majority path
tot = [sum(v.values()) for v in VOTES]
sh_start = [VOTES[i][START[i]] / tot[i] for i in range(N)]
sh_major = [VOTES[i][MAJ[i]] / tot[i] for i in range(N)]
fig = go.Figure()
fig.add_bar(x=list(range(N)), y=[round(x, 3) for x in sh_major], name="majority path (the lesson's default)",
            marker=dict(color=LIGHT, line=dict(width=0)),
            customdata=[fmt_path(MAJ[i], False) for i in range(N)],
            hovertemplate="chunk %{x}: majority path covers %{y:.0%}<br>%{customdata}<extra></extra>")
fig.add_scatter(x=list(range(N)), y=[round(x, 3) for x in sh_start], mode="markers", name="start-rule path",
                marker=dict(size=7, color=[ORANGE if i in diff else BLUE for i in range(N)], line=dict(width=1, color=SURFACE)),
                customdata=[fmt_path(START[i], False) for i in range(N)],
                hovertemplate="chunk %{x}: start path covers %{y:.0%}<br>%{customdata}<extra></extra>")
for i, txt, ay in ((27, "27 (D-002 gold)", -50), (34, "34 ('It can be used…')", -80), (68, "68 (D-003 gold)", -50)):
    fig.add_annotation(x=i, y=sh_start[i], text=txt, showarrow=True, arrowhead=0, ax=0, ay=ay, arrowcolor=INK2,
                       font=dict(size=12, color=INK))
fig.update_layout(height=440, barmode="overlay",
                  title="§5 · Start rule vs majority rule: share of each chunk under the chosen path (measured)"
                        "<br><sup>orange dots: the two rules disagree (84 of 97 chunks); a dot at the bottom means the "
                        "start path covers only a few characters</sup>",
                  xaxis=dict(title="chunk seq", dtick=8), yaxis=dict(title="share of non-space characters", tickformat=".0%",
                                                                     range=[0, 1.05]))
fig.show()

# chart 2: header length by rule
fig = go.Figure()
for (name, hs), col in zip(RULES.items(), (BLUE, ORANGE, AQUA)):
    fig.add_box(y=[len(h) for h in hs], name=name, boxpoints="all", jitter=0.4, pointpos=0, marker=dict(size=5, color=col),
                line=dict(color=col), customdata=list(range(N)),
                hovertemplate=f"{name}: chunk %{{customdata}} header %{{y}} chars<extra></extra>")
fig.update_layout(height=430, showlegend=False,
                  title="§5 · Header length by rule (measured, characters; ~6.21 characters per WordPiece token)"
                        "<br><sup>start 28 / 120 / 168 · majority 67 / 123 / 168 · all-inside 93 / 198 / 306 "
                        "(min / median / max)</sup>",
                  yaxis=dict(title="header characters"))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 6 · The information test: a constant title adds nothing

**What this verifies** (lesson step 6, `#info`; facts K5, K10). A header can help ranking only if it **differs between chunks**. Count the distinct headers over the 97 chunks:

| arm | distinct headers | largest group sharing one header | header characters min / median / max |
|---|---|---|---|
| none | 1 | 97 | 0 / 0 / 0 |
| title | **1** | **97** | 28 / 28 / 28 |
| path (start rule) | 97 | 1 | 28 / 120 / 168 |
| path (majority rule) | 96 | 2 | 67 / 123 / 168 |

On a one-document corpus the title is the same 28 characters on every chunk: it cannot tell any chunk from another. It is not harmless either. It still **moves every vector** (mean pooling averages its tokens in), and in BM25 its three words occur in all 97 units, so their raw idf is negative and rank_bm25 lifts each to the floor 0.25 × average idf = **0.8565**: nearly the same score added to every chunk.

With MiniLM cached, the cell also measures how far the constant title moves each chunk vector (your run).

No chart: the table is the point.
""")
code(r'''
ARM_STATS = {}
for arm in ARMS:
    hs = HDR[arm]
    top = collections.Counter(hs).most_common(1)[0]
    L = [len(h) for h in hs]
    ARM_STATS[arm] = [len(set(hs)), top[1], round(top[1] / N, 2), min(L), int(statistics.median(L)), max(L)]
    print(f"   {arm:6s} distinct {ARM_STATS[arm][0]:3d} / {N} | largest group {top[1]:3d} ({top[1] / N:.2f})"
          f" | header chars {ARM_STATS[arm][3:]}")
check("§6 per arm: distinct, largest group, its share, header chars min / median / max (K5)", ARM_STATS,
      {"none": [1, 97, 1.0, 0, 0, 0], "title": [1, 97, 1.0, 28, 28, 28], "path": [97, 1, 0.01, 28, 120, 168],
       "major": [96, 2, 0.02, 67, 123, 168]})
grp = collections.Counter(HDR["major"])
check("§6 majority arm: the one header shared by two chunks", [n for n in grp.values() if n > 1], [2])
print("   majority arm, the shared header:", [(g.split(" › ")[-1], [i for i in range(N) if HDR["major"][i] == g])
                                             for g, n in grp.items() if n > 1])

# BM25 over each arm's embed_text (the v2.0 bm25_text field; also used in step 9)
NORM_RE = re.compile(r"[a-z0-9]+(?:[.,][0-9]+)*")


def tok(t):
    return NORM_RE.findall(t.lower())


BM_TOKS = {arm: [tok(e) for e in EMBED[arm]] for arm in ARMS}
BM = {arm: BM25Okapi(BM_TOKS[arm]) for arm in ARMS}
bm_t = BM["title"]
IDF = {w: [r4(bm_t.idf[w]), sum(w in set(c) for c in BM_TOKS["title"])] for w in tok(TITLE)}
print("   title arm idf, df:", IDF, "| floor 0.25 x average_idf =", r4(0.25 * bm_t.average_idf))
check("§6 title arm: idf and df of understanding / climate / change (K10)", IDF,
      {"understanding": [0.8565, 97], "climate": [0.8565, 97], "change": [0.8565, 97]})
check("§6 that idf is the floor 0.25 x average_idf (K10)", r4(0.25 * bm_t.average_idf), 0.8565)

if MINILM_OK:
    E = minilm_embeddings()
    shift = np.einsum("ij,ij->i", E["none"], E["title"])
    print(f"   your run: cos(chunk, title + chunk) min / median / max {shift.min():.4f} / {np.median(shift):.4f} / {shift.max():.4f}")
    check("§6 the constant title moves every one of the 97 MiniLM vectors (cos < 0.9999)", int((shift < 0.9999).sum()), 97)
else:
    skip("§6 how far the constant title moves each MiniLM vector", MINILM_WHY)
''')

# =====================================================================================================================
md(r"""
## 7 · Dilution and the header magnet

**What this verifies** (lesson step 7, `#dilute`; facts K6, K13). MiniLM **mean-pools** its token vectors, so a header of `h` tokens on a chunk of `c` tokens gets the share

`s = h / (h + c)`

of the chunk vector. With a 120-character path (~19 tokens, DERIVED): **0.106** on a 1,000-character chunk (~161 tokens), **0.112** on the median 935 (~151), **0.229** on a 400-character tail (~64). By characters, the path arm's share over the 97 chunks is **0.029 / 0.119 / 0.201**. Short chunks get the biggest push.

**The toy (K13)** shows what a shared header does under mean pooling. d = 64, seed 0. Each token is a unit vector near its topic (mean cosine 0.4965). Chunks A and B have 150 tokens on two different topics; the header has its own topic. As `h` grows, A moves away from its bare self, A and B move toward each other, and both move toward the header's topic: the **header magnet**. The magnitudes are toy, not MiniLM.

**The chart** shows `s` for three chunk lengths (left) and the toy's three cosines (right), with the K13 table points marked.
""")
code(r'''
hc = [len(h) for h in HDR["path"]]
s_chars = [h / (h + len(c["text"])) for h, c in zip(hc, chunks)]
check("§7 path arm, header share by characters: min / median / max (K6)",
      [r3(min(s_chars)), r3(statistics.median(s_chars)), r3(max(s_chars))], [0.029, 0.119, 0.201])
S_TOK = {}
for hchars, cchars in ((120, 1000), (120, 935), (120, 400)):
    h_t, c_t = wp(hchars), wp(cchars)
    S_TOK[cchars] = [h_t, c_t, r3(h_t / (h_t + c_t))]
check("§7 s = h/(h+c): [header tokens, chunk tokens, s] for 1,000 / 935 / 400-character chunks (DERIVED, K6)", S_TOK,
      {1000: [19, 161, 0.106], 935: [19, 151, 0.112], 400: [19, 64, 0.229]})

# K13 toy: mean pooling with a shared header (exactly as i5_kit_measure.py; the random draws are in the same order)
rng = np.random.default_rng(0)
d = 64


def unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def tokens(topic, n):
    return unit(topic[None] + 1.7 * rng.normal(size=(n, d)) / math.sqrt(d))


tA, tB, tH = (unit(rng.normal(size=d)) for _ in range(3))
A, B, Hd = tokens(tA, 150), tokens(tB, 150), tokens(tH, 100)
pa0, pb0 = unit(A.mean(0)), unit(B.mean(0))


def toy_row(h):
    pa = unit(np.vstack([A, Hd[:h]]).mean(0))
    pb = unit(np.vstack([B, Hd[:h]]).mean(0))
    return [float(pa @ pa0), float(pa @ pb), float(pa @ tH)]


check("§7 toy: mean cos(token, its topic) (K13)", r4(float((A @ tA).mean())), 0.4965)
TOY = {h: [r3(h / (h + 150))] + [r4(x) for x in toy_row(h)] for h in (0, 19, 27, 50, 100)}
for h, row in TOY.items():
    print(f"   h={h:3d} s={row[0]:.3f}: cos(A+header, A) {row[1]:.4f} | cos(A, B) same header {row[2]:+.4f}"
          f" | cos(A+header, header topic) {row[3]:+.4f}")
check("§7 toy table: [s, cos(A+hdr, A), cos(A, B), cos(A+hdr, header topic)] per h (K13)", TOY, {
    0: [0.0, 1.0, -0.1651, -0.1261], 19: [0.112, 0.9897, -0.1857, 0.0078], 27: [0.153, 0.981, -0.1734, 0.0608],
    50: [0.25, 0.9423, -0.1265, 0.2047], 100: [0.4, 0.8014, 0.0964, 0.485]})
check("§7 toy: the header magnet - A and B end up positively aligned at h = 100 (K13)", TOY[100][2] > 0 > TOY[0][2], True)

# chart: s for three chunk lengths, and the toy curves
fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.12,
                    subplot_titles=("share s = h/(h+c) (formula, DERIVED tokens)", "toy K13: mean pooling, d = 64"))
hh = list(range(0, 101))
for c_t, col, lab in ((64, ORANGE, "c = 64 (400-char tail)"), (151, BLUE, "c = 151 (median chunk)"), (161, AQUA, "c = 161 (1,000 chars)")):
    fig.add_scatter(x=hh, y=[round(h / (h + c_t), 4) for h in hh], mode="lines", name=lab, line=dict(color=col, width=2),
                    hovertemplate=f"{lab}<br>h %{{x}} tokens: s %{{y:.3f}}<extra></extra>", row=1, col=1)
    fig.add_scatter(x=[19], y=[round(19 / (19 + c_t), 3)], mode="markers", showlegend=False, marker=dict(size=9, color=col),
                    hovertemplate=f"{lab}<br>19-token path header: s %{{y:.3f}}<extra></extra>", row=1, col=1)
curves = np.array([toy_row(h) for h in hh])
for k, (lab, col) in enumerate((("cos(A + header, A bare)", BLUE), ("cos(A, B), same header", ORANGE),
                                 ("cos(A + header, header topic)", AQUA))):
    fig.add_scatter(x=hh, y=np.round(curves[:, k], 4), mode="lines", name=lab, line=dict(color=col, width=2, dash="dot"),
                    hovertemplate=f"{lab}<br>h %{{x}}: %{{y:.4f}}<extra></extra>", row=1, col=2)
    fig.add_scatter(x=list(TOY), y=[TOY[h][k + 1] for h in TOY], mode="markers", showlegend=False,
                    marker=dict(size=8, color=col), hovertemplate="K13 table: h %{x}, %{y:.4f}<extra></extra>", row=1, col=2)
fig.update_xaxes(title_text="header tokens h", row=1, col=1)
fig.update_xaxes(title_text="header tokens h (chunks have 150)", row=1, col=2)
fig.update_yaxes(title_text="s", row=1, col=1)
fig.update_yaxes(title_text="cosine", row=1, col=2)
fig.update_layout(height=500, title="§7 · Dilution and the header magnet (formula + toy)", legend=dict(y=-0.32, yanchor="top"),
                  margin=dict(l=70, r=30, t=90, b=140))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 8 · Truncation: the tail is cut

**What this verifies** (lesson step 8, `#trunc`; fact K6). MiniLM reads at most **256** tokens, `[CLS]` and `[SEP]` included (C2 K9). The header goes **first**, so when `h + c > 256` it is the **chunk's tail** that is cut, never the header. The longest v0 chunk is **182** WordPiece tokens with the specials (C2 K2, cited):
- with a 27-token path header: 182 + 27 = **209**, fits;
- with a 100-token LLM-written context: 182 + 100 = **282**, over by **26**: the last 26 tokens of the chunk are not embedded.

Over the 97 chunks (DERIVED from characters): **0 of 97** path-arm `embed_text` go over 256 (estimate max 188), while a 100-token context would push **about 29 of 97** over.

With MiniLM cached, the cell also counts the tokens exactly with MiniLM's own tokenizer, per arm (your run).

**The chart** stacks, for every chunk sorted by length, the chunk's tokens (DERIVED) and a 100-token context against the 256 line.
""")
code(r'''
TRUNC = []
for extra in (wp(max(hc)), 27, 100):
    tot = 182 + extra
    TRUNC.append([extra, tot, tot <= 256, max(0, tot - 256)])
check("§8 182 + longest path header (DERIVED 27) / + 27 / + 100: [extra, total, fits, over by] (K6)", TRUNC,
      [[27, 209, True, 0], [27, 209, True, 0], [100, 282, False, 26]])
est = [wp(len(e)) + 2 for e in EMBED["path"]]
check("§8 path arm embed_text over 256, and the largest estimate (DERIVED, K6)", [sum(x > 256 for x in est), max(est)], [0, 188])
est_c = [wp(len(c["text"])) + 2 for c in chunks]
est100 = [x + 100 for x in est_c]
check("§8 a 100-token LLM context + chunk over 256 (DERIVED, K6)", sum(x > 256 for x in est100), 29)

if MINILM_OK:
    tk = MODEL.tokenizer
    NTOK = {arm: [len(tk(e)["input_ids"]) for e in EMBED[arm]] for arm in ARMS}
    for arm in ARMS:
        print(f"   your run, {arm:6s} exact tokens incl. specials min/median/max {min(NTOK[arm])}/"
              f"{int(statistics.median(NTOK[arm]))}/{max(NTOK[arm])}; over 256: {sum(x > 256 for x in NTOK[arm])}")
    hdr_tok = [p - n for p, n in zip(NTOK["path"], NTOK["none"])]
    print(f"   your run, path header exact tokens (incl. the separator) min/median/max "
          f"{min(hdr_tok)}/{int(statistics.median(hdr_tok))}/{max(hdr_tok)} (DERIVED estimate 5/19/27 from characters)")
    check("§8 MiniLM max_seq_length (C2 K9)", MODEL.max_seq_length, 256)
    check("§8 exact WordPiece, none arm: the chunk maximum incl. [CLS]/[SEP] (C2 K2, cited in K6)", max(NTOK["none"]), 182)
    check("§8 the title arm adds exactly 3 tokens (understanding, climate, change) to every chunk",
          sorted(set(t - n for t, n in zip(NTOK["title"], NTOK["none"]))), [3])
    check("§8 exact count over 256, path and majority arms (K4/K6 DERIVED: 0)",
          [sum(x > 256 for x in NTOK[a]) for a in ("path", "major")], [0, 0])
else:
    skip("§8 exact WordPiece token counts per arm (none / title / path / major)", MINILM_WHY)

# chart: truncation bars (DERIVED)
srt = sorted(range(N), key=lambda i: est_c[i])
fig = go.Figure()
fig.add_bar(x=[str(i) for i in srt], y=[est_c[i] for i in srt], name="chunk + [CLS]/[SEP] (DERIVED)",
            marker=dict(color=BLUE, line=dict(width=0)), hovertemplate="chunk %{x}: %{y} tokens<extra></extra>")
fig.add_bar(x=[str(i) for i in srt], y=[min(100, max(0, 256 - est_c[i])) for i in srt], name="100-token context, embedded",
            marker=dict(color=AQUA, line=dict(width=0)), hovertemplate="chunk %{x}: %{y} context tokens fit<extra></extra>")
fig.add_bar(x=[str(i) for i in srt], y=[max(0, est100[i] - 256) for i in srt], name="over 256: the chunk's tail is cut",
            marker=dict(color=RED, line=dict(width=0)), hovertemplate="chunk %{x}: %{y} tokens of the chunk tail cut<extra></extra>")
fig.add_hline(y=256, line=dict(color=INK, width=1.5, dash="dash"), annotation_text="256 = MiniLM max_seq_length",
              annotation_position="top left")
fig.update_layout(barmode="stack", height=460, bargap=0.05,
                  title=f"§8 · A 100-token context pushes about {sum(x > 256 for x in est100)} of 97 chunks over 256 (DERIVED tokens)"
                        "<br><sup>the header comes first, so the red part is cut from the end of the chunk; "
                        "a path header (≤ 27 tokens) fits on every chunk</sup>",
                  xaxis=dict(title="chunk seq, sorted by length", showticklabels=False), yaxis=dict(title="tokens"))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 9 · Measuring it on your questions

**What this verifies** (lesson step 9, `#measure`; facts K7, K8, K10, K15, K16). A header arm is a **retrieval** change, so it is measured like one: CE@4 on the dev questions at a fixed k, per category with its n, paired against the arm without headers (count the discordant pairs), plus two checks specific to headers.
- **The near-duplicates.** Four chunks mention Paris: **17** (p.6), **27** (p.10, D-002 gold), **68** (p.23, D-003 gold), **70** (p.24). D-002's distractor pages are 6, 23, 24; D-003's are 6, 10. The **margin** = best gold score − best distractor score shows whether a header separates them.
- **Leakage.** If the questions were written by reading the headings, a header "helps" by repeating the question. On the 8 draft seeds no question word is in the gold chunk's header but missing from its text (only `coal` for D-005 and `solar` for D-006 are in both): the seeds were written from spans.
- **Ceiling.** The BM25 preview (v2.0's field, not v1.2) gives **Hit@4 8/8, CE@4 8/8, MRR@10 0.938 in every arm**: these span-written seeds are too easy for BM25 to show a header effect either way, so b + c = 0.
- **Detectable effect** (06 §9.4): with n = 50 paired and b + c = 10, the 95% half-width is **±0.124**, and about **0.18** is needed for 80% power. A small header gain on D will not be visible.

With MiniLM cached, the cell also computes per arm: Hit@4 / CE@4 / MRR@10 on the 8 answerable seeds, the D-002 and D-003 margins, Kendall's τ between the none and title rankings, and the margin dumbbell chart (your run). Only the none arm has an expected value: P4 measured it on the same chunks and seeds (ranks [3, 3, 1, 1, 1, 1, 2, 2], Hit@4 8/8, MRR@10 0.708; I5_FACTS §2, CITED P4_FACTS K4).

**The chart** here is the BM25 preview table.
""")
code(r'''
PARIS_CH = [i for p in (6, 10, 23, 24) for i in range(N) if PAGE[i] == p and "Paris" in chunks[i]["text"]]
check("§9 chunks on pages 6, 10, 23, 24 that mention Paris (K7)", [[i, PAGE[i]] for i in PARIS_CH],
      [[17, 6], [27, 10], [68, 23], [70, 24]])
check("§9 their start-rule paths, without the title (K7)", [fmt_path(START[i], False) for i in PARIS_CH], [
    "Chapter 4: Mitigation and Adaptation › Reforestation and Afforestation › Afforestation Initiatives",
    "Chapter 6: Global and Local Climate Action",
    "Chapter 15: Climate Change and Technology › Carbon Capture and Utilization › Direct Air Capture (DAC)",
    "Chapter 16: Global Cooperation and Governance › Regional and National Initiatives › European Green Deal"])
check("§9 distractor pages of D-002 and D-003 (06 §6.7)", [BYQ["D-002"]["distractor_pages"], BYQ["D-003"]["distractor_pages"]],
      [[6, 23, 24], [6, 10]])
DIST = {q: [i for i in range(N) if PAGE[i] in BYQ[q]["distractor_pages"] and "Paris" in chunks[i]["text"] and i not in REL[q]]
        for q in ("D-002", "D-003")}
check("§9 distractor chunks (on a distractor page, mention Paris, not gold) (K7)", DIST, {"D-002": [17, 68, 70], "D-003": [17, 27]})

# leakage: question words in the gold chunk's header but not in its text (K8)
STOP = set("a an and are as at be by does did do for from how in is it of on or the this that to was what which who why with "
           "according document regarding countries".split())
LEAK = {}
for s in ANS:
    q = {w for w in WRE.findall(s["question"].lower()) if w not in STOP and len(w) > 2}
    i = REL[s["qid"]][0]
    htoks = set(WRE.findall(HDR["path"][i].lower()))
    ttoks = set(WRE.findall(chunks[i]["text"].lower()))
    LEAK[s["qid"]] = [sorted(q & htoks - ttoks), sorted(q & htoks & ttoks)]
check("§9 leakage: header-only question words, all 8 seeds (K8)", [v[0] for v in LEAK.values()], [[]] * 8)
check("§9 question words in both header and text (K8)", {q: v[1] for q, v in LEAK.items() if v[1]},
      {"D-005": ["coal"], "D-006": ["solar"]})

# BM25 preview per arm (K10)
BM25_RES = {}
for arm in ARMS:
    ranks, ces = [], []
    for s in ANS:
        r = order(BM[arm].get_scores(tok(s["question"])))
        ranks.append(first_rel(r, s["qid"]))
        ces.append(ce_at(r, s["qid"]))
    BM25_RES[arm] = dict(ranks=ranks, ces=ces, summary=list(summary(ranks, ces)))
    print(f"   BM25 {arm:6s} first relevant rank {ranks} | Hit@4, CE@4, MRR@10 {BM25_RES[arm]['summary']}")
check("§9 BM25 first relevant rank D-001..D-008, every arm (K10)", [BM25_RES[a]["ranks"] for a in ARMS],
      [[1, 1, 1, 1, 1, 2, 1, 1]] * 4)
check("§9 BM25 Hit@4, CE@4, MRR@10, every arm: the ceiling (K10)", [BM25_RES[a]["summary"] for a in ARMS], [[8, 8, 0.938]] * 4)


def discordant(ces_a, ces_b):
    """paired comparison on CE@4: b = items only arm A gets right, c = items only arm B gets right."""
    return [sum(a and not b for a, b in zip(ces_a, ces_b)), sum(b and not a for a, b in zip(ces_a, ces_b))]


check("§9 BM25 none vs majority: discordant pairs b, c (both arms at 8/8)",
      discordant(BM25_RES["none"]["ces"], BM25_RES["major"]["ces"]), [0, 0])
se = math.sqrt(10) / 50
check("§9 06 §9.4, n = 50 paired, b + c = 10: SE, 95% half-width, 80%-power effect (formula, K15)",
      [r3(se), r3(1.96 * se), float(f"{2.8 * se:.2f}")], [0.063, 0.124, 0.18])

# chart: the BM25 preview table
qids = [s["qid"] for s in ANS]
fig = go.Figure(go.Table(
    columnwidth=[90] + [52] * 8 + [62, 62, 70],
    header=dict(values=["arm"] + qids + ["Hit@4", "CE@4", "MRR@10"], fill_color=GRID, font=dict(color=INK, size=12),
                align="center"),
    cells=dict(values=[["none", "title", "path (start)", "path (majority)"]]
                      + [[BM25_RES[a]["ranks"][k] for a in ARMS] for k in range(8)]
                      + [[f"{BM25_RES[a]['summary'][0]}/8" for a in ARMS], [f"{BM25_RES[a]['summary'][1]}/8" for a in ARMS],
                         [BM25_RES[a]["summary"][2] for a in ARMS]],
               fill_color=[[SURFACE] * 4] * 6 + [[LIGHT] * 4] + [[SURFACE] * 4] * 5, line_color=GRID, align="center",
               height=30, font=dict(color=INK2, size=12))))
fig.update_layout(title="§9 · BM25 preview: first relevant rank per draft seed and arm (measured; v2.0 field, "
                        "draft seeds)<br><sup>identical in all four arms: at the ceiling, these 8 span-written questions "
                        "cannot show a header effect (D-006, highlighted, is the only rank 2)</sup>",
                  height=330, margin=dict(l=10, r=10, t=90, b=10))
fig.show()
''')

code(r'''
# MiniLM per arm (K16): runs only when the model is in the local Hugging Face cache. Values are "your run":
# I5_FACTS has no MiniLM numbers (the build session could not load the model), so only invariants are checked.
if MINILM_OK:
    E = minilm_embeddings()
    Q = E["Q"]
    check("§9 MiniLM vectors: 8 queries and 97 chunks per arm, 384 numbers, unit length",
          [list(Q.shape), [list(E[a].shape) for a in ARMS],
           bool(all(np.allclose(np.linalg.norm(E[a], axis=1), 1, atol=1e-4) for a in ARMS))],
          [[8, 384], [[97, 384]] * 4, True])
    ML_RES = {}
    for arm in ARMS:
        ranks, ces = [], []
        for qi, s in enumerate(ANS):
            r = order(E[arm] @ Q[qi])
            ranks.append(first_rel(r, s["qid"]))
            ces.append(ce_at(r, s["qid"]))
        ML_RES[arm] = dict(ranks=ranks, ces=ces, summary=summary(ranks, ces))
        hk, c4, mrr = ML_RES[arm]["summary"]
        print(f"   your run, MiniLM {arm:6s} first relevant rank {dict(zip(qids, ranks))} | Hit@4 {hk}/8 CE@4 {c4}/8 MRR@10 {mrr}")
    for arm in ("title", "path", "major"):
        b, c = discordant(ML_RES["none"]["ces"], ML_RES[arm]["ces"])
        per_cat = collections.defaultdict(lambda: [0, 0, 0])
        for k, s in enumerate(ANS):
            per_cat[s["category"]][0] += 1
            per_cat[s["category"]][1] += ML_RES["none"]["ces"][k]
            per_cat[s["category"]][2] += ML_RES[arm]["ces"][k]
        print(f"   your run, CE@4 none vs {arm}: b = {b} (only none), c = {c} (only {arm}); per category "
              f"[n, CE@4 none, CE@4 {arm}]: {dict(per_cat)}")
    check("§9 MiniLM: a first relevant rank for every seed and arm (relevant chunks are always ranked)",
          all(r is not None for a in ARMS for r in ML_RES[a]["ranks"]), True)
    check("§9 MiniLM none arm = P4's baseline on the same chunks and seeds (I5_FACTS §2, CITED P4_FACTS K4)",
          [ML_RES["none"]["ranks"], ML_RES["none"]["summary"][0], ML_RES["none"]["summary"][2]],
          [[3, 3, 1, 1, 1, 1, 2, 2], 8, 0.708])
else:
    skip("§9 MiniLM retrieval per arm (Hit@4 / CE@4 / MRR@10 on the 8 answerable draft seeds)", MINILM_WHY)

if MINILM_OK:
    from scipy.stats import kendalltau
    MARGIN = {}
    for q in ("D-002", "D-003"):
        qi = qids.index(q)
        gold = REL[q]
        for arm in ARMS:
            sc = E[arm] @ Q[qi]
            g, dd = float(max(sc[gold])), float(max(sc[DIST[q]]))
            MARGIN[(q, arm)] = (g, dd, int(DIST[q][int(np.argmax(sc[DIST[q]]))]))
            print(f"   your run, {q} {arm:6s} best gold {g:.4f} best distractor {dd:.4f} (chunk {MARGIN[(q, arm)][2]})"
                  f" margin {g - dd:+.4f}")
    TAU = {s["qid"]: float(kendalltau(E["none"] @ Q[qi], E["title"] @ Q[qi])[0]) for qi, s in enumerate(ANS)}
    print("   your run, Kendall tau none vs title per seed:", {q: round(t, 4) for q, t in TAU.items()})
    check("§9 Kendall tau none vs title is a valid correlation for every seed", all(-1 <= t <= 1 for t in TAU.values()), True)

    # chart: the margin dumbbell
    fig = go.Figure()
    ys = [f"{q} · {arm}" for q in ("D-002", "D-003") for arm in ARMS]
    for y in ys:
        q, arm = y.split(" · ")
        g, dd, _ = MARGIN[(q, arm)]
        fig.add_scatter(x=[dd, g], y=[y, y], mode="lines", line=dict(color=AXIS, width=3), showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=[MARGIN[tuple(y.split(" · "))][1] for y in ys], y=ys, mode="markers", name="best distractor (Paris, other page)",
                    marker=dict(size=12, color=ORANGE), customdata=[MARGIN[tuple(y.split(" · "))][2] for y in ys],
                    hovertemplate="%{y}: distractor chunk %{customdata}, cos %{x:.4f}<extra></extra>")
    fig.add_scatter(x=[MARGIN[tuple(y.split(" · "))][0] for y in ys], y=ys, mode="markers", name="best gold chunk",
                    marker=dict(size=12, color=BLUE),
                    customdata=[f"{MARGIN[tuple(y.split(' · '))][0] - MARGIN[tuple(y.split(' · '))][1]:+.4f}" for y in ys],
                    hovertemplate="%{y}: gold cos %{x:.4f}, margin %{customdata}<extra></extra>")
    fig.update_layout(height=470, title="§9 · Gold vs best distractor per header arm (measured, your run; MiniLM cosine)"
                                        "<br><sup>blue to the right of orange = the gold chunk wins; the gap is the margin</sup>",
                      xaxis=dict(title="MiniLM cosine to the question"), yaxis=dict(autorange="reversed"))
    fig.show()
else:
    skip("§9 D-002 / D-003 gold-vs-best-distractor margins per arm and the margin dumbbell chart", MINILM_WHY)
    skip("§9 Kendall tau between the none and title rankings", MINILM_WHY)
''')

# =====================================================================================================================
md(r"""
## 10 · LLM-written contexts and the cost ladder

**What this verifies** (lesson step 10, `#llm`; fact K11). Anthropic's contextual retrieval gives an LLM the **whole document** plus one chunk and asks for 50–100 tokens that situate the chunk (external). dsRAG's header is document-level (a title and a summary). Between "no LLM" and "whole document per chunk" there is a ladder:

| rung | what | calls on D | input tokens per call | cost on D |
|---|---|---|---|---|
| 0 | path header from the PDF | 0 | — | $0 |
| 1 | title / summary per document | 1–2 | ≤ 4K–8K | not needed: the title is the 24 pt line |
| 2 | chapter window, Groq `gpt-oss-20b` | 97 | median **855**, max 1,322 | **$0.0124**; 106,743 tokens; ≥ **13.3 min** at 8K TPM |
| 3 | whole document, Groq free tier | 97 | **13,090** | **blocked**: 13,090 > 8,000 TPM in one request; 1,269,730 tokens vs 200K TPD |

All token counts here are **DERIVED** (`o200k_harmony` ratio 5.65 characters per token, 12,840 tokens for the document; Claude's own tokenizer would differ). Assumptions: 250 tokens of chunk + instruction per call, 200 output tokens including reasoning. Prices are from `prices_2026-10-17.json`; the Groq rate limits are a plan row, UNVERIFIED.

**The chart** (in step 11, with the caching rows) compares the rungs' costs.
""")
code(r'''
prices = json.loads(PRICES.read_text(encoding="utf-8"))
g = prices["models"]["groq:openai/gpt-oss-20b"]
hk5 = prices["models"]["anthropic:claude-haiku-5-5"]
tpm = prices["rate_limits"]["groq:openai/gpt-oss-20b"]["tpm"]
tpd = prices["rate_limits"]["groq:openai/gpt-oss-20b"]["tpd"]
check("§10 prices (USD per 1M): Groq in / out / cached; Haiku 5.5 in / out; Groq TPM, TPD",
      [g["input"], g["output"], g["cached_input"], hk5["input"], hk5["output"], tpm, tpd],
      [0.075, 0.3, 0.037, 0.1, 0.5, 8000, 200000])
P_TOK, O_TOK = 250, 200        # chunk + instruction tokens per call; output incl. reasoning (research assumptions)
chap_bounds = [h[3] for h in H if h[0] == 1] + [len(DOC)]
chap_len = [b - a for a, b in zip(chap_bounds, chap_bounds[1:])]
check("§10 chapters and their characters min / median / max (K11)",
      [len(chap_len), min(chap_len), int(statistics.median(chap_len)), max(chap_len)], [21, 1591, 3336, 6058])


def chapter_of(i):
    pos = first_nonspace(chunks[i])
    k = max(j for j, a in enumerate(chap_bounds[:-1]) if a <= pos) if pos >= chap_bounds[0] else 0
    return k


win_tok = [round(chap_len[chapter_of(i)] / O200_CPT) for i in range(N)]
in2 = [w + P_TOK for w in win_tok]
cost2 = sum(x * g["input"] + O_TOK * g["output"] for x in in2) / 1e6
tok2 = sum(in2) + N * O_TOK
check("§10 rung 2 (chapter window, Groq): input tokens per call median, max; total tokens (DERIVED, K11)",
      [int(statistics.median(in2)), max(in2), tok2], [855, 1322, 106743])
check("§10 rung 2: USD, fits the TPD, minutes at 8K TPM (formula, K11)",
      [r4(cost2), tok2 <= tpd, float(f"{tok2 / tpm:.1f}")], [0.0124, True, 13.3])
in3 = O200_DOC + P_TOK
check("§10 rung 3 (whole document): input tokens per call; too large for one request at 8K TPM; 97 calls (K11)",
      [in3, in3 > tpm, N * in3], [13090, True, 1269730])
c_groq_cached = (O200_DOC * g["input"] + (N - 1) * O200_DOC * g["cached_input"] + N * P_TOK * g["input"]
                 + N * O_TOK * g["output"]) / 1e6
check("§10 rung 3 on a paid Groq tier with 50% cached input, USD (formula, K11)", r4(c_groq_cached), 0.0542)
''')

# =====================================================================================================================
md(r"""
## 11 · Prompt caching, cache keys and wrong contexts

**What this verifies** (lesson step 11, `#cache`; facts K11, K12). The whole-document prompt repeats the same 12,840 document tokens 97 times. **Prompt caching** stores that prefix once: put the **document first and the chunk last**, and process the chunks in document order, so every call after the first starts with the same bytes. Claude's write costs 1.25× (5-minute cache) once, and each read 0.1× (external, `claude-api` skill). The formula:

`cost_d = D·p_in·w + (n−1)·D·p_in·ρ + n·(c+P)·p_in + n·o·p_out`

On D with Haiku 5.5: **$0.1367** uncached vs **$0.0261** cached, **5.2×** cheaper. A prefix below the model's minimum is **silently not cached**: the cookbook's 3,412-token document is under Haiku 4.5's 4,096 minimum (external); Haiku 5.5's minimum is 512.

**Cache keys.** The stored contexts must be rebuilt when anything in the prompt changes. After a one-line edit on page 12 (" (revised)" appended to its first line), only chunk 33's text changes:
- a key over the **chunk text only** serves **96 of 97** contexts from cache, all written from the old document;
- a key over **prompt version + document text + chunk text** serves **0 of 97**: all are rebuilt.

**Wrong contexts.** An LLM can write a context that names something not in the document. A cheap check: every capitalised name in the context must occur in the document text (toy example below).

**The chart** compares the cost of each rung of the ladder (steps 10 and 11).
""")
code(r'''
w_mult, r_mult = 1.25, 0.10
c_unc = (N * in3 * hk5["input"] + N * O_TOK * hk5["output"]) / 1e6
c_cache = (O200_DOC * hk5["input"] * w_mult + (N - 1) * O200_DOC * hk5["input"] * r_mult
           + N * P_TOK * hk5["input"] + N * O_TOK * hk5["output"]) / 1e6
check("§11 rung 3 with Haiku 5.5: uncached USD, cached USD, ratio (formula, K11)",
      [r4(c_unc), r4(c_cache), float(f"{c_unc / c_cache:.1f}")], [0.1367, 0.0261, 5.2])
check("§11 minimum cacheable prefix: Haiku 5.5 (512) vs our 12,840; Haiku 4.5 (4,096) vs the cookbook's 3,412 "
      "(external): [D is cached, cookbook is cached]", [O200_DOC >= 512, 3412 >= 4096], [True, False])

# prefix order: the document first gives every prompt the same prefix; the chunk first gives none
doc_first = [f"<document>\n{DOC}\n</document>\n<chunk>\n{c['text']}\n</chunk>" for c in chunks]
chunk_first = [f"<chunk>\n{c['text']}\n</chunk>\n<document>\n{DOC}\n</document>" for c in chunks]
pre_doc, pre_chunk = len(os.path.commonprefix(doc_first)), len(os.path.commonprefix(chunk_first))
print(f"   shared prefix of the 97 prompts: document first {pre_doc} characters; chunk first {pre_chunk} characters")
check("§11 document first: the 97 prompts share the whole document as prefix; chunk first: almost nothing",
      [pre_doc >= len(DOC), pre_chunk < 50], [True, True])

# K12: cache keys after a one-line edit on page 12
edited_pages = list(pages)
edited_pages[11] = pages[11].replace("\n", " (revised)\n", 1)
EDOC = "\n".join(edited_pages)
edch = chunking.chunk_document("climate", "edited", edited_pages,
                               chunking.ChunkerConfig(name="recursive", size=1000, overlap=200, scope="per_page"))
sha = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
k_chunk = [sha(c["text"]) for c in chunks]
k_chunk_e = [sha(c.text) for c in edch]
k_full = [sha("i5_context_wholedoc_v1|" + DOC + "|" + c["text"]) for c in chunks]
k_full_e = [sha("i5_context_wholedoc_v1|" + EDOC + "|" + c.text) for c in edch]
check("§11 edit on page 12: chunk count unchanged; changed chunks; page-12 chunks (K12)",
      [len(edch), [i for i in range(N) if k_chunk[i] != k_chunk_e[i]], [i for i in range(N) if PAGE[i] == 12]],
      [97, [33], [33, 34, 35]])
check("§11 served from cache: chunk-text key vs prompt version + document + chunk key (K12)",
      [sum(a == b for a, b in zip(k_chunk, k_chunk_e)), sum(a == b for a, b in zip(k_full, k_full_e))], [96, 0])
check("§11 doc_text_sha256 before / after the edit, first 12 hex (K12)", [sha(DOC)[:12], sha(EDOC)[:12]],
      ["5106772efa77", "1377caa13861"])

# wrong contexts: every capitalised name in a context must occur in the document (toy contexts)
NAME_RE = re.compile(r"\b[A-Z][A-Za-z0-9-]+(?:\s+[A-Z][A-Za-z0-9-]+)*")


def names_not_in_doc(context, doc_text=DOC):
    return [n for n in NAME_RE.findall(context) if n not in doc_text]


TOY_CTX = {
    "good": "This chunk is from Chapter 6 on Global and Local Climate Action, under International Collaboration; "
            "it describes the Paris Agreement.",
    "wrong": "This chunk is from the Nike annual report and describes the Kyoto Protocol.",
}
for k, v in TOY_CTX.items():
    print(f"   toy context ({k}): {v!r} -> names not in the document: {names_not_in_doc(v)}")
check("§11 entity check on two toy contexts: names not in the document (toy)",
      {k: names_not_in_doc(v) for k, v in TOY_CTX.items()}, {"good": [], "wrong": ["Nike"]})

# chart: the cost ladder
LADDER = [("rung 0 · path header (no LLM)", 0.0, AQUA, "$0 · 0 calls"),
          ("rung 2 · chapter window, Groq gpt-oss-20b", cost2, BLUE, f"${cost2:.4f} · 97 calls · ≥ {tok2 / tpm:.1f} min"),
          ("rung 3 · whole doc, Groq free tier", 0.0, RED, "blocked: 13,090 > 8,000 TPM per request"),
          ("rung 3 · whole doc, Groq paid, 50% cached", c_groq_cached, BLUE, f"${c_groq_cached:.4f}"),
          ("rung 3 · whole doc, Haiku 5.5 cached", c_cache, ORANGE, f"${c_cache:.4f}"),
          ("rung 3 · whole doc, Haiku 5.5 uncached", c_unc, ORANGE, f"${c_unc:.4f} ({c_unc / c_cache:.1f}× the cached)")]
fig = go.Figure(go.Bar(y=[r[0] for r in LADDER], x=[round(r[1], 4) for r in LADDER], orientation="h",
                       marker=dict(color=[r[2] for r in LADDER], line=dict(width=2, color=SURFACE)),
                       text=[r[3] for r in LADDER], textposition="outside", cliponaxis=False,
                       hovertemplate="%{y}: $%{x:.4f}<extra></extra>"))
fig.update_layout(height=420, showlegend=False,
                  title="§10–11 · The cost ladder on Corpus D, 97 chunks (formula; DERIVED tokens; prices 2026-10-17)"
                        "<br><sup>rung 1 (title / summary per document) is not needed on D: the title is the 24 pt line</sup>",
                  xaxis=dict(title="USD for the whole corpus", range=[0, 0.27]), yaxis=dict(autorange="reversed"),
                  margin=dict(l=280, r=40, t=90, b=60))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 12 · Reading the vendor numbers

**What this verifies** (lesson step 12, `#claims`; facts K14, K15). Vendor numbers measure something specific; turn them into what you would measure.
- **Anthropic** reports the failure rate **1 − recall@20**, not CE@4: 5.7% → 3.7% with contextual embeddings is **−2.0 points absolute** but **−35.1% relative**; adding contextual BM25 gives 2.9% (−49.1%), adding a reranker 1.9% (−66.7%) (external, the figures as reported).
- **The cookbook** reports Pass@10 87.15 → 92.34 → 95.26 (external); **dsRAG's KITE** reports 4.72 → 6.04 (external, vendor-reported; the table is also in the upstream notebook's cell 15).
- **The upstream notebook** (`contextual_chunk_headers.ipynb` @ `009adba`) shows 0.10576342 → 0.92206234. That is a **Cohere reranker relevance score** for **one** chunk of a **Nike** 10-K and one query that names "Nike"; the header adds the word the query asks for. It is not a retrieval metric over a set of questions. Its other settings: the climate PDF is downloaded but the Nike text is used, `chunk_size=800`, `chunk_overlap=0`, a 4,000-token document cap, `gpt-4o-mini` at `temperature=0.2`.

No chart: these are reading checks.
""")
code(r'''
K15 = {}
for a, b, what in ((5.7, 3.7, "contextual embeddings"), (5.7, 2.9, "+ contextual BM25"), (5.7, 1.9, "+ rerank")):
    K15[what] = [float(f"{b - a:+.1f}"), float(f"{(b - a) / a * 100:+.1f}")]
check("§12 1 - recall@20 as [absolute points, relative %] (formula, K15)", K15,
      {"contextual embeddings": [-2.0, -35.1], "+ contextual BM25": [-2.8, -49.1], "+ rerank": [-3.8, -66.7]})
check("§12 the same failure-rate drop seen as recall@20: 94.3% -> 96.3% (formula)",
      [round(100 - 5.7, 1), round(100 - 3.7, 1)], [94.3, 96.3])

if UPSTREAM_NB.exists():
    nb_raw = UPSTREAM_NB.read_bytes()
    unb = json.loads(nb_raw)
    src = lambda i: "".join(unb["cells"][i]["source"])
    outs = lambda i: "".join("".join(o.get("text", "")) for o in unb["cells"][i].get("outputs", []))
    check("§12 upstream notebook: sha256 prefix, cells, code execution counts (K14)",
          [hashlib.sha256(nb_raw).hexdigest()[:16], len(unb["cells"]),
           [c.get("execution_count") for c in unb["cells"] if c["cell_type"] == "code"]],
          ["11b78dc9cc583026", 17, [None, 3, None, 4, 5, 13]])
    check("§12 cell 8 downloads the climate PDF and a Nike text (K14)",
          [k in src(8) for k in ("Understanding_Climate_Change", "nike")], [True, True])
    check("§12 cell 9 chunks the Nike text with chunk_size=800, chunk_overlap=0 (K14)",
          [k in src(9) for k in ("nike", "chunk_size=800", "chunk_overlap=0")], [True, True, True])
    check("§12 cell 11: MAX_CONTENT_TOKENS = 4000, gpt-3.5-turbo encoder, gpt-4o-mini, temperature=0.2 (K14)",
          [k in src(11) for k in ("MAX_CONTENT_TOKENS = 4000", "gpt-3.5-turbo", "gpt-4o-mini", "temperature=0.2")],
          [True, True, True, True])
    check("§12 cell 11 saved output: the document title the LLM wrote (K14)", outs(11).strip(), "NIKE, INC. ANNUAL REPORT ON FORM 10-K")
    check("§12 cell 13: Cohere rerank-english-v3.0 via cohere.Client; query 'Nike climate change impact' (K14)",
          [k in src(13) for k in ("rerank-english-v3.0", "cohere.Client")] + ["Query: Nike climate change impact" in outs(13)],
          [True, True, True])
    sims = re.findall(r"Similarity (w/o|with) contextual chunk header: ([0-9.]+)", outs(13))
    check("§12 cell 13 saved output: the two reranker scores (K14)", sims, [["w/o", "0.10576342"], ["with", "0.92206234"]])
    check("§12 cell 15 holds the KITE table with the averages 4.72 and 6.04 (external, the dsRAG figures)",
          [k in src(15) for k in ("KITE", "4.72", "6.04")], [True, True, True])
else:
    skip("§12 upstream notebook checks (K14)", f"not found at {UPSTREAM_NB}; clone NirDiamant/RAG_Techniques @ 009adba next to rag_learning/")
''')

# =====================================================================================================================
md(r"""
## Result

The cell below counts the checks. Every `FAIL` names the value that disagreed; every `SKIPPED` says why it could not run.
""")
code(r'''
n_pass = sum(ok for _, ok in CHECKS)
n_fail = len(CHECKS) - n_pass
print(f"{n_pass} checks passed / {n_fail} failed / {len(SKIPPED)} skipped")
for name, ok in CHECKS:
    if not ok:
        print("   FAILED:", name)
for name, why_ in SKIPPED:
    print("   SKIPPED:", name, "-", why_)
print(f"   (notebook time {time.time() - T0:.1f} s)")
''')

nb = nbf.v4.new_notebook()
nb.cells = CELLS
nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3 (ipykernel)", "language": "python"},
               "language_info": {"name": "python"}}
OUT.parent.mkdir(parents=True, exist_ok=True)
nbf.validate(nb)
nbf.write(nb, str(OUT))
print(f"wrote {OUT.relative_to(WS)}: {len(CELLS)} cells ({sum(c.cell_type == 'code' for c in CELLS)} code)")
