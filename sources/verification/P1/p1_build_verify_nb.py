"""Build study/notebooks/P1_tokens_verify.ipynb: the "verify it yourself" notebook for P1 (LLM fundamentals for RAG).

The notebook rebuilds every measured number and chart of the P1 lesson (study/lessons/P1_llm_fundamentals.html) from
code, one section per lesson step (1-11), and compares each value with the lesson's value in a `check(...)` line. The
expected values are copied from sources/verification/P1/P1_FACTS.md (S1-S11) and out_p1_kit_measure.txt (K1-K8); the
code paths are the ones of p1_measure.py, p1_strawberry.py and p1_kit_measure.py, so the numbers come out identical.
No Groq, Cohere or Claude call, no .env read, no network (MiniLM loads from the local cache, offline; tiktoken uses its
cached encodings). Step 7 reads only the logged O2 report, the installed groq SDK's type definitions and, if it exists,
the recorded-call cache.

Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P1/p1_build_verify_nb.py
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P1/p1_verify_nb_run.py      # executes it, saves outputs
"""
from pathlib import Path
from textwrap import dedent

import nbformat as nbf

WS = Path(__file__).resolve().parents[3]                      # rag_learning/
OUT = WS / "study" / "notebooks" / "P1_tokens_verify.ipynb"

CELLS = []


def md(s):
    CELLS.append(nbf.v4.new_markdown_cell(dedent(s).strip()))


def code(s):
    CELLS.append(nbf.v4.new_code_cell(dedent(s).strip()))


# =====================================================================================================================
md(r"""
# P1 · Verify it yourself: tokens, the window, temperature and cost

**What this is:** a notebook that rebuilds every measured number and chart of the P1 lesson from real code, so you can see each one being made and change the inputs.
**What this is not:** the lab (`labs/P1_tokens_lab.ipynb`, where you write the code yourself) or the quiz. It also makes **no API call**: no Groq, no Cohere, no Claude. Where the lesson uses a fact from a provider's docs or a logged call, this notebook shows the fact and says where it comes from; it does not pretend to re-measure it.

**How to use it.** Run all cells from the top (VS Code: *Run All*). The sections are numbered like the lesson's steps, 1 to 11. Each one has:
- a short note on what it verifies;
- a code cell that **computes** the values;
- `check(...)` lines: `PASS` means the code produced the number the lesson shows, `FAIL` means it did not;
- an interactive chart where the lesson has a chart worth seeing. Hover for values; the temperature chart has a slider.

The last cell counts the checks.

**Labels used for numbers.** *measured* = computed here from real text; *toy* = made-up inputs that show a mechanism; *formula* = arithmetic on measured counts and dated prices; *cited* = from a logged run or a dated doc page, not re-run here.

**The running example.** The climate PDF (`upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf`, 33 pages, 72,593 characters), cut into plain 1,000-character windows that overlap by 200 characters (91 windows).

**Where the expected values come from.** `sources/verification/P1/P1_FACTS.md` (sections S1–S11) and `sources/verification/P1/out_p1_kit_measure.txt` (K1–K8). MiniLM, the local embedding model, loads from the cache on this computer.
""")

code(r'''
# Setup: imports, paths and the shared helpers. Run this cell first.
import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")          # MiniLM may load from the local cache only: no network
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import hashlib
import importlib.metadata as md
import json
import math
import sqlite3
import statistics as st
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pymupdf                                        # pinned 1.26.7
import tiktoken
from tokenizers import Tokenizer, models, pre_tokenizers, trainers
import plotly.graph_objects as go
import plotly.io as pio

pio.renderers.default = "plotly_mimetype"             # small outputs that VS Code draws
T0 = time.time()


def find_workspace():
    here = Path.cwd().resolve()
    for p in (here, *here.parents):
        if (p / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").is_file() and (p / "study").is_dir():
            return p
    raise FileNotFoundError("Open this notebook from inside rag_learning/.")


WS = find_workspace()
REPO = WS.parent / "upstream" / "RAG_Techniques"
PDF = REPO / "data" / "Understanding_Climate_Change.pdf"
print("workspace:", WS)
print("python", sys.version.split()[0], {p: md.version(p) for p in
      ("pymupdf", "tiktoken", "tokenizers", "transformers", "sentence-transformers", "numpy", "plotly")})

# ---------------------------------------------------------------- check(): computed value vs the lesson's value
CHECKS, SKIPPED = [], []


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
          + (f"  (tolerance {tol:g})" if tol else ""))      # returns None, so a cell ending in check() shows no "True"


def skip(name, reason):
    SKIPPED.append((name, reason))
    print(f"SKIPPED  {name}: {reason}")


# ---------------------------------------------------------------- chart style (light surface, fixed colour order)
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"    # categorical slots 1-3, always in this order
pio.templates["p1"] = go.layout.Template(layout=dict(
    font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', size=13, color=INK2),
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, colorway=[BLUE, ORANGE, AQUA],
    xaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    yaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=INK2)),
    title=dict(x=0, xanchor="left", font=dict(size=15, color=INK)),
    margin=dict(l=70, r=30, t=90, b=60), hoverlabel=dict(font_size=12)))
pio.templates.default = "p1"


def r5(xs):                                           # round for chart data: smaller outputs
    return [round(float(x), 5) for x in xs]


# ---------------------------------------------------------------- the corpus (same extraction as the acceptance suite)
check("environment: pymupdf version (pinned)", md.version("pymupdf"), "1.26.7")
check("environment: tiktoken, tokenizers versions", [md.version("tiktoken"), md.version("tokenizers")], ["0.14.0", "0.23.2"])
pdf_bytes = PDF.read_bytes()
check("corpus: PDF sha256", hashlib.sha256(pdf_bytes).hexdigest(),
      "1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669")
pages = [p.get_text() for p in pymupdf.open(PDF)]
full = "\n".join(pages)                               # page.get_text() per page, joined with "\n" (contracts_check L764-L766)
check("corpus: pages, characters, page-1 characters (S1)", [len(pages), len(full), len(pages[0])], [33, 72593, 2424])

# the 91 plain 1000/200 character windows (p1_measure.py S3/S4)
S, O = 1000, 200
windows = [(i, i + S) for i in range(0, len(full), S - O)]
windows = [(a, min(b, len(full))) for a, b in windows if a < len(full)]

# ---------------------------------------------------------------- tokenizers
enc = {n: tiktoken.get_encoding(n) for n in ("cl100k_base", "o200k_base", "o200k_harmony", "gpt2")}
harmony, cl100k = enc["o200k_harmony"], enc["cl100k_base"]


def n_tik(name, text):
    return len(enc[name].encode(text, disallowed_special=()))


def pieces_of(e, ids):                                # the text of each token; "·" marks a leading space
    return [e.decode_single_token_bytes(i).decode("utf-8", errors="replace").replace(" ", "·") for i in ids]


MINILM = "sentence-transformers/all-MiniLM-L6-v2"
MODEL, WP, MINILM_OK = None, None, False
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
warnings.filterwarnings("ignore", message="IProgress not found")   # tqdm's notebook-widget notice (no ipywidgets here)
try:
    import transformers
    transformers.utils.logging.disable_progress_bar()
    from sentence_transformers import SentenceTransformer
    MODEL = SentenceTransformer(MINILM, device="cpu")
    WP = MODEL.tokenizer                              # BERT WordPiece (uncased), as used by the embedder
    MINILM_OK = True
except Exception as e:  # noqa: BLE001
    skip("every MiniLM / WordPiece number", f"MiniLM could not load offline: {type(e).__name__}: {str(e)[:160]}")


def n_wp(text):                                       # content tokens only (no [CLS]/[SEP]), as p1_measure.py
    return len(WP(text, add_special_tokens=False, truncation=False)["input_ids"])


def n_unk(text):
    return WP(text, add_special_tokens=False)["input_ids"].count(WP.unk_token_id)


print(f"\nsetup done in {time.time() - T0:.1f} s: {len(windows)} windows; MiniLM loaded: {MINILM_OK}")
''')

# =====================================================================================================================
md(r"""
## 1 · The tokenizer cuts; the model only sees IDs

**What this verifies** (lesson step 1, `#cut`; facts S2, S3, S5). The same sentence cut by three tokenizers:
- `cl100k_base` (GPT-3.5/4 family): **12** tokens;
- `o200k_base` (GPT-4o family; `o200k_harmony`, the one gpt-oss uses, cuts ordinary text the same way): **13** tokens;
- MiniLM's WordPiece: **16** IDs, which include the two markers `[CLS]` and `[SEP]` (14 text tokens).

Also: the vocabulary sizes (S2), the token counts of window 0 (S3: 201 / 198 / 186), and the last step of the story, measured on MiniLM: each ID is a **row number** in the model's embedding table (30,522 rows × 384 numbers). The tokenizer does the cutting; the model only looks rows up.

**The chart** is the token strip: one row per tokenizer, one cell per piece, with its ID underneath. `·` marks a leading space.
""")
code(r'''
SENT = "Anthropogenic emissions are accelerating deglaciation in Greenland."
check("§1 sentence length (characters)", len(SENT), 67)
STRIP = {}
for name in ("cl100k_base", "o200k_base"):
    ids = enc[name].encode(SENT)
    STRIP[name] = list(zip(pieces_of(enc[name], ids), ids))
    print(f"{name:12s} {len(ids):2d} tokens: {[p for p, _ in STRIP[name]]}")
if MINILM_OK:
    wids = WP(SENT)["input_ids"]
    STRIP["MiniLM WordPiece"] = list(zip(WP.convert_ids_to_tokens(wids), wids))
    print(f"{'WordPiece':12s} {len(wids):2d} ids incl. [CLS]/[SEP]: {WP.convert_ids_to_tokens(wids)}")
    check("§1 pieces: cl100k / o200k / WordPiece (incl. [CLS],[SEP])",
          [len(STRIP["cl100k_base"]), len(STRIP["o200k_base"]), len(wids)], [12, 13, 16])
    check("§1 WordPiece text tokens (without [CLS],[SEP])", n_wp(SENT), 14)
else:
    check("§1 pieces: cl100k / o200k", [len(STRIP["cl100k_base"]), len(STRIP["o200k_base"])], [12, 13])
    skip("§1 WordPiece pieces", "MiniLM did not load")
check("§1 o200k_harmony cuts this sentence like o200k_base", harmony.encode(SENT), enc["o200k_base"].encode(SENT))

# vocabulary sizes and which encoding a model name maps to (S2)
check("§1 vocab sizes: cl100k / o200k / o200k_harmony / gpt2 (S2)",
      [enc[n].n_vocab for n in ("cl100k_base", "o200k_base", "o200k_harmony", "gpt2")], [100277, 200019, 201088, 50257])
check("§1 encoding_for_model: gpt-3.5-turbo / gpt-4o-mini / gpt-oss-20b (S2)",
      [tiktoken.encoding_for_model(m).name for m in ("gpt-3.5-turbo", "gpt-4o-mini", "gpt-oss-20b")],
      ["cl100k_base", "o200k_base", "o200k_harmony"])

# window 0 = characters [0, 1000) of the PDF (S3)
w0 = full[windows[0][0]:windows[0][1]]
got = [n_tik("cl100k_base", w0), n_tik("o200k_base", w0)] + ([n_wp(w0)] if MINILM_OK else [])
check("§1 window 0 tokens: cl100k / o200k" + (" / WordPiece" if MINILM_OK else ""), got, [201, 198, 186][:len(got)])

# IDs -> rows of the embedding table (MiniLM, measured)
if MINILM_OK:
    table = MODEL[0].auto_model.embeddings.word_embeddings.weight
    check("§1 MiniLM WordPiece vocab, lower-cases its input (S2)", [WP.vocab_size, bool(WP.do_lower_case)], [30522, True])
    check("§1 MiniLM embedding table: rows x numbers per row", list(table.shape), [30522, 384])
    first = STRIP["MiniLM WordPiece"][1]
    print(f"   e.g. piece {first[0]!r} has ID {first[1]}: the model starts from row {first[1]} of that table "
          f"({table.shape[1]} numbers). It never sees the letters.")

# the token strip as a table
names = list(STRIP)
width = max(len(v) for v in STRIP.values())
cells = [[f"{n}<br>({len(STRIP[n])})" for n in names]]
for j in range(width):
    cells.append([f"<b>{STRIP[n][j][0]}</b><br><span style='color:{MUTED}'>{STRIP[n][j][1]}</span>"
                  if j < len(STRIP[n]) else "" for n in names])
fig = go.Figure(go.Table(
    columnwidth=[150] + [70] * width,
    header=dict(values=["tokenizer (count)"] + [str(j + 1) for j in range(width)], fill_color=GRID,
                font=dict(color=INK, size=12), align="center"),
    cells=dict(values=cells, fill_color=SURFACE, line_color=GRID, align="center", height=44,
               font=dict(color=INK2, size=12))))
fig.update_layout(title=f"§1 · One sentence, three cuts: piece and ID (measured; '·' = leading space)<br>"
                        f"<sup>{SENT}</sup>", height=330, margin=dict(l=10, r=10, t=80, b=10))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 2 · Where the pieces come from (BPE)

**What this verifies** (lesson step 2, `#bpe`; facts K6, S5, S11).
- **A tiny BPE trained on the climate PDF** (Hugging Face `tokenizers`, `BpeTrainer`, vocabulary 300, words split on spaces first). BPE starts from single characters and repeatedly merges the most frequent neighbouring pair. It learns 230 merges; the first ones are `i + n`, `a + n`, `e + s`, … Training twice gives the same merges.
- With only 300 pieces, "greenhouse" needs **4** pieces and "deglaciation" **6**; the real `o200k_harmony` (about 200,000 pieces) reads "greenhouse" as 1 piece after a space and "deglaciation" as 4.
- **Case and space change the cut** (S5, cl100k): `Greenland` 2 tokens, ` Greenland` 1, `GREENLAND` 2.
- **"strawberry"** (S11, `o200k_harmony`): 3 tokens with nothing before it, 1 after a space, and inside the question "How many r's are in strawberry?" it is a single ID (101830). The model sees that ID, not the three letters `r`.

No chart: the lists are the point.
""")
code(r'''
def train_tiny_bpe():                                 # as p1_kit_measure.py K6
    tok = Tokenizer(models.BPE(unk_token="[UNK]"))
    tok.pre_tokenizer = pre_tokenizers.Whitespace()
    tok.train_from_iterator([full], trainers.BpeTrainer(vocab_size=300, min_frequency=2, special_tokens=["[UNK]"],
                                                        show_progress=False))
    return tok


def merges_of(t):
    return [" + ".join(m) if isinstance(m, list) else m.replace(" ", " + ")
            for m in json.loads(t.to_str())["model"]["merges"]]


tiny = train_tiny_bpe()
MERGES = merges_of(tiny)
check("§2 tiny BPE: vocabulary, merges learned (K6)", [tiny.get_vocab_size(), len(MERGES)], [300, 230])
check("§2 tiny BPE: first 12 merges, in order (K6)", MERGES[:12],
      ["i + n", "a + n", "e + s", "a + t", "o + n", "e + n", "an + d", "e + r", "i + on", "in + g", "r + e", "a + l"])
check("§2 tiny BPE: a second training run gives identical merges", merges_of(train_tiny_bpe()) == MERGES, True)

print(f"\n   {'word':13s} {'tiny BPE (300)':34s} o200k_harmony, after a space")
WORDS = {}
for w in ("the", "climate", "greenhouse", "emissions", "deglaciation"):
    t = tiny.encode(w).tokens
    h = pieces_of(harmony, harmony.encode(" " + w))
    WORDS[w] = (t, h)
    print(f"   {w:13s} {len(t)} {str(t):32s} {len(h)} {h}")
check("§2 greenhouse: tiny BPE pieces", WORDS["greenhouse"][0], ["gre", "enh", "ous", "e"])
check("§2 greenhouse: o200k_harmony pieces (after a space)", WORDS["greenhouse"][1], ["·greenhouse"])
check("§2 deglaciation: tiny BPE pieces", WORDS["deglaciation"][0], ["de", "g", "l", "ac", "i", "ation"])
check("§2 deglaciation: o200k_harmony pieces (after a space)", WORDS["deglaciation"][1], ["·de", "gl", "aci", "ation"])
check("§2 the / climate / emissions: 1 piece in both",
      [len(WORDS[w][k]) for w in ("the", "climate", "emissions") for k in (0, 1)], [1] * 6)

# case and leading space (S5, cl100k)
check("§2 cl100k: 'Greenland' / ' Greenland' / 'GREENLAND' tokens (S5)",
      [len(cl100k.encode(s)) for s in ("Greenland", " Greenland", "GREENLAND")], [2, 1, 2])

# "strawberry" (S11, o200k_harmony = encoding_for_model('gpt-oss-20b'))
WORD, QUESTION_R = "strawberry", "How many r's are in strawberry?"
for label, text in (("nothing before it", WORD), ("leading space", " " + WORD), ("in double quotes", f'"{WORD}"')):
    ids = harmony.encode(text)
    print(f"   {label:17s} {text!r:16s} -> {len(ids)} tokens ids={ids} pieces={pieces_of(harmony, ids)}")
check("§2 'strawberry' ids (nothing before it)", harmony.encode(WORD), [302, 1618, 19772])
check("§2 ' strawberry' ids (leading space)", harmony.encode(" " + WORD), [101830])
check("§2 '\"strawberry\"' ids (double quotes)", harmony.encode(f'"{WORD}"'), [1, 302, 1618, 19772, 1])
qids = harmony.encode(QUESTION_R)
print(f"   question {QUESTION_R!r}: {len(qids)} tokens {pieces_of(harmony, qids)}")
check("§2 the question: tokens, and the word inside it is ID 101830", [len(qids), 101830 in qids], [8, True])
check("§2 letter 'r' in 'strawberry' (a string count; the model sees IDs)", WORD.count("r"), 3)
''')

# =====================================================================================================================
md(r"""
## 3 · Characters per token is measured, not 4

**What this verifies** (lesson step 3, `#ratio`; facts S3, S4, K4, K5).
- **The whole PDF:** cl100k 13,026 tokens (5.57 characters per token), o200k 12,840 (5.65), WordPiece 11,694 (6.21). The rule "characters ÷ 4" gives 18,148, which **over-counts by 39%**.
- **It moves with content:** the same table for page 1, windows 0–2, a toy code snippet, a made-up numbers line, a German and a Hindi sentence (S3). Toy code and numbers fall **below** 4; real repo code (`helper_functions.py`) is 4.61 with `o200k_harmony` (K4).
- **Across all 91 windows** (S4): cl100k 4.61 to 6.37 (median 5.52).
- **Digits are cut into groups of up to three** (K4): `1234567` → `123|456|7`.
- **Bytes, not characters** (K5): tiktoken's "about 4" is about **bytes**. The Hindi sentence is 61 characters but 161 UTF-8 bytes; `o200k_harmony` reads it in 18 tokens (3.39 characters, 8.94 bytes per token), while cl100k needs 62 (0.98 characters per token).

One message on stderr is expected here: counting the whole PDF with the MiniLM tokenizer prints `11694 > 256`. It is only a notice that the text is longer than the model reads (§5), not an error.

**The charts.** Bars of characters per token by content type with the ÷4 line, and the 91 window ratios per tokenizer (each dot is one window).
""")
code(r'''
CODE = ("def top_k(scores, k=4):\n"
        "    idx = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]\n"
        "    return [(i, round(scores[i], 3)) for i in idx]\n")
NUMBERS = "Run 2026-10-08T14:32:07Z: 3 x 1,000 chars, k=4, cos=0.8731, p95=1.42s, ids 4f9c2a17, 7b0e93d5."
GERMAN = "Der Klimawandel verändert die Niederschlagsmuster in ganz Europa deutlich."
HINDI = "जलवायु परिवर्तन से पूरे भारत में वर्षा के पैटर्न बदल रहे हैं।"
SAMPLES = [("whole document", full), ("page 1", pages[0])]
SAMPLES += [(f"window {k}", full[a:b]) for k, (a, b) in enumerate(windows[:3])]
SAMPLES += [("code snippet (toy)", CODE), ("numbers line (toy)", NUMBERS), ("German sentence", GERMAN),
            ("Hindi sentence", HINDI)]

ROWS = {}
print(f"   {'sample':20s} {'chars':>6s} | {'cl100k':>6s} {'c/t':>5s} | {'o200k':>6s} {'c/t':>5s} | "
      f"{'WordPc':>6s} {'c/t':>5s} {'[UNK]':>5s} | {'chars/4':>7s} {'err':>5s}")
for label, t in SAMPLES:
    a, b = n_tik("cl100k_base", t), n_tik("o200k_base", t)
    c, u = (n_wp(t), n_unk(t)) if MINILM_OK else (None, None)
    est = len(t) / 4
    ROWS[label] = dict(chars=len(t), cl=a, o2=b, wp=c, unk=u, est=round(est), err=round(100 * (est - a) / a))
    print(f"   {label:20s} {len(t):6d} | {a:6d} {len(t)/a:5.2f} | {b:6d} {len(t)/b:5.2f} | "
          + (f"{c:6d} {len(t)/c:5.2f} {u:5d}" if MINILM_OK else f"{'SKIP':>6s} {'':5s} {'':5s}")
          + f" | {est:7.0f} {ROWS[label]['err']:+4d}%")
print()

EXPECTED_S3 = {  # sample: (chars, cl100k, o200k, WordPiece, chars/4, error % vs cl100k)   -- P1_FACTS S3
    "whole document": (72593, 13026, 12840, 11694, 18148, 39), "page 1": (2424, 490, 486, 441, 606, 24),
    "window 0": (1000, 201, 198, 186, 250, 24), "window 1": (1000, 196, 193, 171, 250, 28),
    "window 2": (1000, 217, 218, 198, 250, 15), "code snippet (toy)": (142, 45, 45, 61, 36, -21),
    "numbers line (toy)": (94, 63, 63, 62, 24, -63), "German sentence": (74, 22, 16, 25, 18, -16),
    "Hindi sentence": (61, 62, 18, 36, 15, -75)}
for label, (ch, a, b, c, est, err) in EXPECTED_S3.items():
    r = ROWS[label]
    got = [r["chars"], r["cl"], r["o2"]] + ([r["wp"]] if MINILM_OK else []) + [r["est"], r["err"]]
    exp = [ch, a, b] + ([c] if MINILM_OK else []) + [est, err]
    check(f"§3 {label}: chars, cl100k, o200k{', WordPiece' if MINILM_OK else ''}, chars/4, error %", got, exp)
R = ROWS["whole document"]
check("§3 whole document chars/token: cl100k / o200k" + (" / WordPiece" if MINILM_OK else ""),
      [round(R["chars"] / R["cl"], 2), round(R["chars"] / R["o2"], 2)] + ([round(R["chars"] / R["wp"], 2)] if MINILM_OK else []),
      [5.57, 5.65, 6.21][:3 if MINILM_OK else 2])
if MINILM_OK:
    check("§3 [UNK] count, every sample", [r["unk"] for r in ROWS.values()], [0] * len(ROWS))
check("§3 whole document: gpt2 tokens, o200k_harmony tokens (= o200k_base)",
      [n_tik("gpt2", full), n_tik("o200k_harmony", full)], [14375, 12840])
words = full.split()
check("§3 whole document: whitespace words, chars per word", [len(words), round(len(full) / len(words), 2)], [9255, 7.84])

# S4: all 91 windows
check("§3 windows: count, length of the last one (S4)", [len(windows), windows[-1][1] - windows[-1][0]], [91, 593])
COUNTERS = {"cl100k_base": lambda t: n_tik("cl100k_base", t), "o200k_base": lambda t: n_tik("o200k_base", t)}
if MINILM_OK:
    COUNTERS["WordPiece"] = n_wp
EXPECTED_S4 = {"cl100k_base": ([4.61, 5.52, 6.37], [157, 180.5, 217]),
               "o200k_base": ([4.59, 5.62, 6.49], [154, 177.5, 218]),
               "WordPiece": ([5.05, 6.21, 7.04], [142, 160.5, 198])}
RATIOS = {}
for name, f in COUNTERS.items():
    r = [(b - a) / f(full[a:b]) for a, b in windows]
    tk = [f(full[a:b]) for a, b in windows[:-1]]          # full-length windows only for token counts
    RATIOS[name] = r
    check(f"§3 {name}: chars/token min / median / max over 91 windows",
          [round(min(r), 2), round(st.median(r), 2), round(max(r), 2)], EXPECTED_S4[name][0])
    check(f"§3 {name}: tokens per full window min / median / max", [min(tk), st.median(tk), max(tk)], EXPECTED_S4[name][1])
if not MINILM_OK:
    skip("§3 WordPiece window ratios", "MiniLM did not load")

# K4: real repo code and digit grouping
CODE_RATIO = {}
for rel, exp in (("helper_functions.py", [11847, 2570, 4.61, 2553, 4.64]),
                 ("evaluation/evalute_rag.py", [5046, 1102, 4.58, 1098, 4.60])):
    t = (REPO / rel).read_text(encoding="utf-8")
    a, b = len(harmony.encode(t, disallowed_special=())), len(cl100k.encode(t, disallowed_special=()))
    CODE_RATIO[rel] = (len(t) / a, len(t) / b)
    check(f"§3 repo code {rel}: chars, o200k_harmony tokens, c/t, cl100k tokens, c/t (K4)",
          [len(t), a, round(len(t) / a, 2), b, round(len(t) / b, 2)], exp)
for s, exp in (("1234567", ["123", "456", "7"]), ("1,234,567", ["1", ",", "234", ",", "567"]),
               ("2023-11-07", ["202", "3", "-", "11", "-", "07"]), ("650,000", ["650", ",", "000"]),
               ("1.5", ["1", ".", "5"])):
    check(f"§3 digits {s!r} under o200k_harmony (K4)", pieces_of(harmony, harmony.encode(s)), exp)

# K5: bytes vs characters
for label, t, exp in (("whole climate PDF", full, [72593, 72595, 12840, 5.65, 5.65]),
                      ("Hindi sentence", HINDI, [61, 161, 18, 3.39, 8.94])):
    n, nb = len(harmony.encode(t, disallowed_special=())), len(t.encode("utf-8"))
    check(f"§3 {label}: chars, UTF-8 bytes, o200k_harmony tokens, chars/token, bytes/token (K5)",
          [len(t), nb, n, round(len(t) / n, 2), round(nb / n, 2)], exp)
check("§3 Hindi sentence chars/token: cl100k (S3)", round(len(HINDI) / n_tik("cl100k_base", HINDI), 2), 0.98)

# chart 1: chars per token by content type, with the ÷4 line
cats = list(ROWS) + ["repo code: helper_functions.py"]
fig = go.Figure()
for key, label, colour in (("cl", "cl100k_base", BLUE), ("o2", "o200k (repo code: o200k_harmony)", ORANGE),
                           ("wp", "MiniLM WordPiece", AQUA)):
    ys = [ROWS[c]["chars"] / ROWS[c][key] if ROWS[c][key] else None for c in ROWS]
    ys.append({"cl": CODE_RATIO["helper_functions.py"][1], "o2": CODE_RATIO["helper_functions.py"][0]}.get(key))
    if key == "wp" and not MINILM_OK:
        continue
    fig.add_bar(x=cats, y=[None if y is None else round(y, 5) for y in ys], name=label,
                marker=dict(color=colour, line=dict(width=2, color=SURFACE)),
                hovertemplate="%{x}<br>%{y:.2f} characters per token<extra>" + label + "</extra>")
fig.add_hline(y=4, line=dict(color=INK, dash="dash", width=1.5),
              annotation_text="the '÷ 4' rule", annotation_position="top right", annotation_font_color=INK)
fig.update_layout(barmode="group", title="§3 · Characters per token by content type (measured; dashed = ÷ 4)",
                  height=460, yaxis=dict(title="characters per token"), xaxis=dict(tickangle=-30))
fig.show()

# chart 2: the 91 window ratios per tokenizer
fig = go.Figure()
for (name, r), colour in zip(RATIOS.items(), (BLUE, ORANGE, AQUA)):
    fig.add_box(y=r5(r), name=name, boxpoints="all", jitter=0.45, pointpos=0, marker=dict(color=colour, size=6),
                line=dict(color=colour), fillcolor="rgba(0,0,0,0)",
                customdata=list(range(len(r))), hovertemplate="window %{customdata}: %{y:.2f} chars/token<extra></extra>")
fig.add_hline(y=4, line=dict(color=INK, dash="dash", width=1.5), annotation_text="÷ 4",
              annotation_position="bottom right", annotation_font_color=INK)
fig.update_layout(title="§3 · Characters per token in each of the 91 windows (measured)", height=440,
                  yaxis=dict(title="characters per token"), showlegend=False)
fig.show()
''')

# =====================================================================================================================
md(r"""
## 4 · Count with the right tokenizer: two traps

**What this verifies** (lesson step 4, `#traps`; facts K2, K3).
- **Trap 1, the model name.** `tiktoken.encoding_for_model("openai/gpt-oss-20b")`, with the id exactly as it is written in `.env`, raises `KeyError`: tiktoken knows `gpt-oss-…` by its prefix, not with the provider in front. Two fixes: name the encoding (`get_encoding("o200k_harmony")`), or strip the prefix (`id.split("/")[-1]`).
- **Trap 2, special-token text inside a document.** `o200k_harmony` has 201,088 IDs, 1,091 of them special (the chat-format markers `<|start|>`, `<|message|>`, `<|end|>`, …). If a document contains the *text* `<|endoftext|>`, a plain `encode()` raises `ValueError`. Passing `disallowed_special=()` counts it as ordinary text (7 tokens).

**The 3-row rule** (what to count with):

| You want to know | Count with |
|---|---|
| Will the embedder read the whole chunk? (truncation) | the **embedder's** tokenizer (MiniLM: WordPiece; Cohere: Cohere's) |
| Will the prompt fit, and roughly what will it cost? (budget) | the **generator's** tokenizer (gpt-oss: `o200k_harmony`) |
| What was I billed? | the provider's **`usage`** in the response (step 7) |
""")
code(r'''
def maps_to(model_id):
    try:
        return tiktoken.encoding_for_model(model_id).name
    except KeyError as ex:
        return f"KeyError: {str(ex)[:60]}"


for m in ("gpt-oss-20b", "openai/gpt-oss-20b", "gpt-4o-mini", "gpt-3.5-turbo"):
    print(f"   encoding_for_model({m!r:22s}) -> {maps_to(m)}")
MID = "openai/gpt-oss-20b"                                # the .env style id (GROQ_MODEL_ID)
check("§4 encoding_for_model('openai/gpt-oss-20b') raises KeyError (K2)", maps_to(MID).startswith("KeyError"), True)
check("§4 fix 1: get_encoding('o200k_harmony') (K2)", tiktoken.get_encoding("o200k_harmony").name, "o200k_harmony")
check("§4 fix 2: encoding_for_model(id.split('/')[-1]) (K2)", tiktoken.encoding_for_model(MID.split("/")[-1]).name,
      "o200k_harmony")

SPECIALS = sorted(harmony.special_tokens_set)
CHAT = ["<|start|>", "<|channel|>", "<|message|>", "<|end|>", "<|return|>", "<|call|>"]
check("§4 o200k_harmony: IDs, special tokens (K3)", [harmony.n_vocab, len(SPECIALS)], [201088, 1091])
check("§4 harmony chat-format markers are special tokens (K3)", [t for t in CHAT if t in harmony.special_tokens_set], CHAT)


def raises_value_error(s):
    try:
        harmony.encode(s)
        return False
    except ValueError as ex:
        print(f"   encode({s!r}) -> ValueError: {str(ex).splitlines()[0][:80]}")
        return True


for s, exp in (("<|endoftext|>", ["<", "|", "end", "of", "text", "|", ">"]), ("<|start|>", ["<", "|", "start", "|", ">"])):
    check(f"§4 encode({s!r}) raises ValueError (K3)", raises_value_error(s), True)
    ids = harmony.encode(s, disallowed_special=())
    check(f"§4 encode({s!r}, disallowed_special=()) -> ordinary pieces (K3)",
          [harmony.decode_single_token_bytes(i).decode() for i in ids], exp)


def count_tokens(text, model_id="openai/gpt-oss-20b"):
    """The fixed counter: strip the provider prefix, and treat special-token text as ordinary text."""
    return len(tiktoken.encoding_for_model(model_id.split("/")[-1]).encode(text, disallowed_special=()))


check("§4 the fixed counter on the O2 smoke message (S9: 7 tokens)", count_tokens("Reply with exactly: smoke test ok"), 7)
''')

# =====================================================================================================================
md(r"""
## 5 · Bridge: the embedder stops reading at 254 tokens

**What this verifies** (lesson step 5, `#truncate`; fact S6), on MiniLM:
- the model reads at most **256** IDs, and those include `[CLS]` (ID 101) and `[SEP]` (ID 102), so **254** text tokens;
- a 400-token passage (from offset 4,836 of the PDF) and its own first 254 tokens give the **same vector**: cosine 1.000000, largest difference 0;
- the same 254 tokens followed by a completely different tail: cosine 1.000000 again. The tail is never read;
- it happens **silently**: no exception, no warning, no log record during `encode()`;
- cutting at 200 tokens does change the vector (0.988245); the passage's own tail, read alone, is far away (0.350182).

The course's default embedder is Cohere `embed-v4.0` (128k-token documents; the server truncates the END by default). P4 owns that part; this section only shows the mechanism on the local model.
""")
code(r'''
if not MINILM_OK:
    skip("§5 truncation (all of it)", "MiniLM did not load")
else:
    check("§5 max_seq_length, tokenizer.model_max_length, vector size",
          [MODEL.max_seq_length, WP.model_max_length, MODEL.get_embedding_dimension()], [256, 256, 384])
    check("§5 modules", [type(m).__name__ for m in MODEL], ["Transformer", "Pooling", "Normalize"])
    # pick the passage exactly as p1_measure.py S6: token 254 ends at a word boundary, so the 254-token prefix
    # re-tokenizes to exactly the first 254 tokens ([CLS] + 254 + [SEP] = 256)
    start0 = len(pages[0]) + 1 + len(pages[1]) + 1     # start of page 3 in the joined text
    chosen = None
    for start in [m for m in range(start0, start0 + 2000) if full[m - 1].isspace() and not full[m].isspace()]:
        span = full[start:start + 4000]
        tok = WP(span, add_special_tokens=False, return_offsets_mapping=True)
        toks = WP.convert_ids_to_tokens(tok["input_ids"])
        if len(toks) < 401 or toks[254].startswith("##") or toks[400].startswith("##"):
            continue
        long_t = span[:tok["offset_mapping"][399][1]]
        pre254 = span[:tok["offset_mapping"][253][1]]
        pre200 = span[:tok["offset_mapping"][199][1]] if not toks[200].startswith("##") else None
        if n_wp(long_t) == 400 and n_wp(pre254) == 254 and pre200 and n_wp(pre200) == 200:
            chosen = (start, long_t, pre254, pre200)
            break
    start, long_t, pre254, pre200 = chosen
    tail = long_t[len(pre254):]
    other = full[-3000:]                               # unrelated text from the end of the document
    swap = pre254 + " " + " ".join(other.split()[:200])
    check("§5 passage: start offset, chars, text tokens, 254-prefix chars, 200-prefix chars, swapped-tail tokens",
          [start, len(long_t), n_wp(long_t), len(pre254), len(pre200), n_wp(swap)], [4836, 2187, 400, 1372, 1122, 502])
    ids_long = MODEL.preprocess([long_t])["input_ids"]  # what the embedder actually receives
    check("§5 IDs fed to the model: shape, first ([CLS]), last ([SEP])",
          [list(ids_long.shape), int(ids_long[0, 0]), int(ids_long[0, -1])], [[1, 256], 101, 102])

    import logging

    class _Grab(logging.Handler):
        def __init__(self):
            super().__init__()
            self.msgs = []

        def emit(self, r):
            self.msgs.append(f"{r.name}: {r.getMessage()[:80]}")

    grab = _Grab()
    for lg in ("transformers", "sentence_transformers"):
        logging.getLogger(lg).addHandler(grab)
    fresh = SentenceTransformer(MINILM, device="cpu")  # a fresh model, as in p1_measure.py
    grab.msgs.clear()
    with warnings.catch_warnings(record=True) as wlist:
        warnings.simplefilter("always")
        E = fresh.encode([long_t, pre254, swap, pre200, tail], normalize_embeddings=True, convert_to_numpy=True,
                         show_progress_bar=False)
    for lg in ("transformers", "sentence_transformers"):
        logging.getLogger(lg).removeHandler(grab)
    check("§5 python warnings, log records during encode() (silent)", [len(wlist), len(grab.msgs)], [0, 0])
    cos = lambda i, j: round(float(E[i] @ E[j]), 6)
    check("§5 cos(400 tokens, its first 254)", cos(0, 1), 1.0)
    check("§5 largest absolute difference between those two vectors", float(np.abs(E[0] - E[1]).max()), 0.0)
    check("§5 cos(400 tokens, same 254 + a different tail)", cos(0, 2), 1.0)
    check("§5 cos(400 tokens, its first 200)", cos(0, 3), 0.988245)
    check("§5 cos(400 tokens, its own tail alone)", cos(0, 4), 0.350182)
''')

# =====================================================================================================================
md(r"""
## 6 · One call's budget: input and output share the window

**What this verifies** (lesson step 6, `#window`; facts S9, S10, K8). The v0 prompt (06 §3.3 template) with four sample windows as sources (not a retrieval result) and the question of seed D-001, counted with `o200k_harmony`:
- system rules **107** + user message **869** (sources 842, question 20, and 7 for the labels `Sources:`, `Question:`, `Answer:`) = **976** tokens (cl100k: 978);
- the O2 smoke call's message counts **7** tokens locally, but Groq billed **78** prompt tokens (step 7). The difference, about **71**, is the chat template (gpt-oss's harmony format) added by the server. Its exact composition on Groq is UNVERIFIED;
- the window inequality: input 976 + template ~71 + output cap 512 = **1,559** tokens, **1.19%** of the 131,072-token window (Groq model page, read 2026-10-17; max output 65,536). Sources are **86%** of the counted input;
- S10 formula lines: 100 queries = 97,600 input tokens; doubling k from 4 to 8 adds about 842 tokens (976 → ~1,818, ×1.86, not ×2).

**The chart** stacks one call: the input parts, the hidden template, and the output cap that reasoning and the answer share. The second bar is the same call at a cap of 64. How the cap splits between reasoning and answer is not measured here; at a cap of 12 the O2 call returned an empty answer (step 7).
""")
code(r'''
SYSTEM_V0 = (  # 06 §3.3 prompts/answer_v1.txt, SYSTEM part, verbatim (as p1_measure.py S9)
    "You answer questions using ONLY the numbered sources below.\n"
    "Rules:\n"
    "1. Every factual sentence must end with one or more citations in the form [doc_id:page],\n"
    "   copied exactly from the source headers, e.g. [climate:10].\n"
    "2. If the sources do not contain the answer, reply exactly:\n"
    "   \"I cannot answer this from the provided documents.\"\n"
    "   Do not use outside knowledge.\n"
    "3. Do not cite a source that does not support the sentence.\n"
    "4. Be concise: at most 5 sentences.\n")
QUESTION = ("According to the document, by how much have global temperatures risen "
            "since the late 19th century?")               # 06 seed item D-001
starts = [sum(len(x) + 1 for x in pages[:i]) for i in range(len(pages))]
page_of = lambda off: max(i + 1 for i, s0 in enumerate(starts) if s0 <= off)   # 1-based page of a doc offset
ctx = "\n\n".join(f"[{k+1}] (climate:{page_of(a)})\n{full[a:b]}" for k, (a, b) in enumerate(windows[:4]))
user = f"Sources:\n{ctx}\n\nQuestion: {QUESTION}\nAnswer:"

B = {}
for n in ("o200k_harmony", "cl100k_base"):
    B[n] = dict(system=n_tik(n, SYSTEM_V0), question=n_tik(n, QUESTION), sources=n_tik(n, ctx), user=n_tik(n, user))
    B[n]["total"] = B[n]["system"] + B[n]["user"]
    print(f"   {n:14s} {B[n]}")
H = B["o200k_harmony"]
check("§6 o200k_harmony: system, question, sources, user message, system + user (S9)",
      [H["system"], H["question"], H["sources"], H["user"], H["total"]], [107, 20, 842, 869, 976])
check("§6 cl100k: system, question, sources, user message, system + user (S9)",
      [B["cl100k_base"][k] for k in ("system", "question", "sources", "user", "total")], [106, 20, 845, 872, 978])
check("§6 characters of system + user", len(SYSTEM_V0) + len(user), 4659)
LABELS = H["user"] - H["sources"] - H["question"]
check("§6 the labels in the user message: 869 - 842 - 20", LABELS, 7)
SMOKE_MSG = "Reply with exactly: smoke test ok"              # labs/O2_smoke_test.py, the logged Groq call
check("§6 O2 smoke message: chars, tokens; its reply 'smoke test ok': tokens (S9)",
      [len(SMOKE_MSG), n_tik("o200k_harmony", SMOKE_MSG), n_tik("o200k_harmony", "smoke test ok")], [33, 7, 4])

# S10 formula lines
N_IN = H["total"]
check("§6 100 queries: input tokens; output bound at cap 256 / 512 (S10)",
      [100 * N_IN, 100 * 256, 100 * 512], [97600, 25600, 51200])
check("§6 k 4 -> 8: input tokens, factor (S10)", [N_IN + H["sources"], round((N_IN + H["sources"]) / N_IN, 2)], [1818, 1.86])

# K8 the window inequality (Groq model page for openai/gpt-oss-20b, read 2026-10-17)
WINDOW, MAX_OUT, OVERHEAD, CAP = 131072, 65536, 71, 512   # OVERHEAD = 78 billed - 7 counted (step 7; DERIVED)
per_call = N_IN + OVERHEAD + CAP
check("§6 input + template + output cap; share of the 131,072 window (K8)",
      [per_call, round(100 * per_call / WINDOW, 2)], [1559, 1.19])
check("§6 sources share of the counted input (K8)", round(100 * H["sources"] / N_IN), 86)
check("§6 the output cap fits Groq's max output for the model", CAP <= MAX_OUT, True)

# chart: the stacked budget, cap 512 and cap 64
parts = [("system rules", H["system"], BLUE, "measured"), ("sources (4 windows)", H["sources"], BLUE, "measured"),
         ("question", H["question"], BLUE, "measured"), ("labels", LABELS, BLUE, "measured"),
         ("template (harmony), ~71", OVERHEAD, MUTED, "DERIVED: 78 billed − 7 counted; composition UNVERIFIED")]
bars = ["v0 call, cap 512", "same call, cap 64"]
fig = go.Figure()
for k, (label, n, colour, how) in enumerate(parts):
    fig.add_bar(y=bars, x=[n, n], orientation="h", name=label if k in (0, 4) else label, showlegend=k in (0, 4),
                legendgroup="input" if k < 4 else "tmpl",
                marker=dict(color=colour, opacity=1 - 0.15 * (k % 2) if k < 4 else 1, line=dict(width=2, color=SURFACE)),
                hovertemplate=f"{label}: %{{x}} tokens ({how})<extra></extra>")
fig.data[0].name = "input you send (counted, o200k_harmony)"
fig.data[4].name = "template the server adds (~71)"
fig.add_bar(y=bars, x=[CAP, 64], orientation="h", name="output cap: reasoning + answer (split not measured)",
            marker=dict(color=ORANGE, line=dict(width=2, color=SURFACE)),
            hovertemplate="output cap: %{x} tokens, shared by reasoning and the answer<extra></extra>")
fig.update_layout(barmode="stack", height=360,
                  title=f"§6 · One call's budget: {per_call:,} tokens at cap 512 = {100*per_call/WINDOW:.2f}% of the "
                        f"{WINDOW:,}-token window",
                  xaxis=dict(title="tokens"), yaxis=dict(autorange="reversed"))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 7 · Reasoning spends the output cap (usage anatomy, no API call)

**What this verifies** (lesson step 7, `#reasoning`). This section makes **no call**. It shows three things:
1. **The documented field layout** of a Groq `usage` object, read from the installed groq SDK's `types/completion_usage.py` (the same file as research source [P1-5]): `prompt_tokens`, `completion_tokens`, `total_tokens` (= prompt + completion), `completion_tokens_details.reasoning_tokens`, `prompt_tokens_details.cached_tokens`, and the timings `queue_time`, `prompt_time`, `completion_time`, `total_time`. The SDK also lists `finish_reason` values (`stop`, `length`, …), `max_completion_tokens` (with `max_tokens` marked deprecated) and the `reasoning_effort` values.
2. **The logged O2 facts** (CITED from `progress/O2_smoke_test_2026-10-08.json`): the smoke call was billed **78** prompt and **23** completion tokens for a reply that counts 4 tokens locally. So about **19** completion tokens were not visible text: reasoning. That reasoning sits inside `completion_tokens` is an inference until one recorded response shows `reasoning_tokens`. The earlier call at a cap of 12 returned an empty answer (CITED, session log 2026-10-08 #2).
3. **Recorded calls**, read from `.cache/llmops/calls.sqlite` only if that file exists. It does not exist yet, so the cell says so and skips.

Dated provider facts used by the lesson (Groq docs, read 2026-10-17; not checkable offline): the default `max_completion_tokens` is 1,024; `reasoning_effort` for gpt-oss is low / medium / high with server default **medium**, and the course pins **low**; the `finish_reason` value Groq returns at the cap is UNVERIFIED.
""")
code(r'''
import inspect
import typing

from groq.types import CompletionUsage
from groq.types.completion_usage import CompletionTokensDetails, PromptTokensDetails
from groq.types.chat.chat_completion import Choice
from groq.resources.chat import completions as groq_completions

print("   groq SDK", md.version("groq"), "(installed; read locally, nothing is sent)")
check("§7 usage fields (groq-python completion_usage.py, [P1-5])", sorted(CompletionUsage.model_fields),
      sorted(["completion_tokens", "prompt_tokens", "total_tokens", "completion_time", "completion_tokens_details",
              "prompt_time", "prompt_tokens_details", "queue_time", "total_time"]))
check("§7 completion_tokens_details / prompt_tokens_details fields",
      [list(CompletionTokensDetails.model_fields), list(PromptTokensDetails.model_fields)],
      [["reasoning_tokens"], ["cached_tokens"]])
import groq.types.completion_usage as usage_module
USAGE_SRC = inspect.getsource(usage_module)
check("§7 total_tokens is documented as prompt + completion",
      "Total number of tokens used in the request (prompt + completion)." in USAGE_SRC, True)
finish_values = list(typing.get_args(Choice.model_fields["finish_reason"].annotation))
check("§7 finish_reason values listed by the SDK include 'stop' and 'length'",
      [v in finish_values for v in ("stop", "length")], [True, True])
params = inspect.signature(groq_completions.Completions.create).parameters
src = inspect.getsource(groq_completions)
check("§7 create() takes max_completion_tokens; max_tokens is documented as deprecated",
      ["max_completion_tokens" in params, "max_tokens: Deprecated in favor of `max_completion_tokens`" in src], [True, True])
import re                                             # the SDK keeps annotations as strings: read the Literal from source

effort = sorted({v for m in re.findall(r"reasoning_effort: Optional\[Literal\[([^\]]*)\]\]", src)
                 for v in re.findall(r'"([^"]+)"', m)})
print("   reasoning_effort values in the SDK (for all Groq models):", effort)
check("§7 reasoning_effort accepts low / medium / high", [v in effort for v in ("low", "medium", "high")], [True] * 3)

# the logged O2 call (CITED)
O2 = json.loads((WS / "progress" / "O2_smoke_test_2026-10-08.json").read_text(encoding="utf-8"))["checks"]["groq_chat"]
check("§7 O2 log: model, reply, prompt_tokens, completion_tokens (CITED)",
      [O2["model"], O2["reply"], O2["prompt_tokens"], O2["completion_tokens"]],
      ["openai/gpt-oss-20b", "smoke test ok", 78, 23])
counted_in, counted_out = n_tik("o200k_harmony", SMOKE_MSG), n_tik("o200k_harmony", O2["reply"])
check("§7 billed - counted: prompt (template overhead), completion (not visible text) (DERIVED)",
      [O2["prompt_tokens"] - counted_in, O2["completion_tokens"] - counted_out], [71, 19])

# an annotated usage object: the documented layout, filled only with what the O2 log recorded
EXAMPLE = [
    ("prompt_tokens", O2["prompt_tokens"], "O2 log", "billed input: your messages + the chat template"),
    ("completion_tokens", O2["completion_tokens"], "O2 log", "billed output: reasoning + visible answer (inside: inference)"),
    ("total_tokens", "prompt + completion", "SDK doc", "documented as prompt + completion"),
    ("completion_tokens_details.reasoning_tokens", "not logged", "SDK doc", "the reasoning part of the output"),
    ("prompt_tokens_details.cached_tokens", "not logged", "SDK doc", "input served from the prompt cache (cheaper)"),
    ("queue_time / prompt_time / completion_time / total_time", "not logged", "SDK doc", "seconds; queue_time = waiting"),
    ("choices[0].finish_reason", "not logged", "SDK doc", "'stop' = finished; 'length' = hit the cap (Groq: UNVERIFIED)"),
]
print("\n   An example `usage` object: the documented FIELD LAYOUT (groq-python), filled ONLY with what O2 logged")
print("   usage = {")
for field, value, src_, note in EXAMPLE:
    v = value if isinstance(value, int) else f'"{value}"'
    print(f"       {field:56s}: {str(v):22s} # [{src_}] {note}")
print("   }")
''')
code(r'''
# Recorded calls (replay only, never records). The llmops helper package and its cache are planned, not built yet.
CALLS = WS / ".cache" / "llmops" / "calls.sqlite"
if not CALLS.is_file():
    skip("§7 recorded calls", f"no recorded pack yet (the llmops helper package is not built): {CALLS.relative_to(WS)} "
                              "does not exist. Nothing is called; the facts above are the documented layout and the O2 log.")
else:
    con = sqlite3.connect(f"file:{CALLS.as_posix()}?mode=ro", uri=True)   # read-only
    try:
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        print(f"   {CALLS.relative_to(WS)}: tables {tables}")
        for t in tables:
            cols = [r[1] for r in con.execute(f"PRAGMA table_info('{t}')")]
            n = con.execute(f"SELECT COUNT(*) FROM '{t}'").fetchone()[0]
            print(f"   {t}: {n} rows; columns {cols}")
        print("   The pack exists. Read its usage fields with the llmops helper (replay mode); this notebook only lists it.")
    finally:
        con.close()
''')

# =====================================================================================================================
md(r"""
## 8 · Temperature reshapes the odds

**What this verifies** (lesson step 8, `#temperature`; fact S7). **Toy** scores (logits) for four answers YES / NO / PARTIAL / MAYBE: [2.0, 1.5, 0.5, −1.0]. These are made up, not from any model; Groq does not return logprobs, so the real numbers cannot be shown.
- probability = softmax(logits ÷ T). Small T sharpens the same scores; large T flattens them;
- entropy (how spread out the odds are, in bits) rises with T: 0.55 at T = 0.25, 1.51 at T = 1, 1.95 at T = 4;
- 1,000 seeded draws (numpy `default_rng(0)`, one generator used in sequence for T = 0.5, 1, 2) follow the probabilities;
- Groq turns T = 0 into 1e-8: with these scores, that is the top answer with probability 1 (greedy).

Repeatability: `seed` is best effort on Groq; on GPU servers the batch your request lands in can change results even at T = 0 (Thinking Machines, 2025; not shown for Groq). Replaying a recorded response is the only guarantee.

**The chart** has a slider over T. Move it and watch the same four scores change shape.
""")
code(r'''
LABELS_T = ["YES", "NO", "PARTIAL", "MAYBE"]
z = np.array([2.0, 1.5, 0.5, -1.0])                  # TOY logits


def softmax_T(z, T):
    s = z / T
    s = s - s.max()
    p = np.exp(s)
    return p / p.sum()


def entropy_bits(p):
    p = p[p > 0]
    return -float((p * np.log2(p)).sum())


EXPECTED_S7 = {0.25: ([0.879, 0.119, 0.002, 0.0], 0.55), 0.5: ([0.704, 0.259, 0.035, 0.002], 1.05),
               1.0: ([0.532, 0.323, 0.119, 0.026], 1.51), 2.0: ([0.404, 0.315, 0.191, 0.090], 1.82),
               4.0: ([0.329, 0.290, 0.226, 0.155], 1.95)}
P = {}
for T, (p_exp, h_exp) in EXPECTED_S7.items():
    P[T] = softmax_T(z, T)
    check(f"§8 T = {T}: probabilities (3 decimals), entropy (bits)",
          [np.round(P[T], 3).tolist(), round(entropy_bits(P[T]), 2)], [p_exp, h_exp], tol=5e-4)
rng = np.random.default_rng(0)
for T, exp in ((0.5, [681, 282, 36, 1]), (1.0, [557, 301, 117, 25]), (2.0, [409, 322, 184, 85])):
    draws = rng.choice(4, size=1000, p=softmax_T(z, T))
    check(f"§8 T = {T}: 1,000 seeded draws per answer", np.bincount(draws, minlength=4).tolist(), exp)
check("§8 T = 1e-8 (Groq's stand-in for 0): the top answer gets probability 1",
      np.round(softmax_T(z, 1e-8), 6).tolist(), [1.0, 0.0, 0.0, 0.0])

# chart: slider over T
TS = [0.25, 0.5, 1.0, 2.0, 4.0]
start = TS.index(1.0)
fig = go.Figure(go.Bar(x=LABELS_T, y=r5(P[TS[start]]), marker=dict(color=BLUE, line=dict(width=2, color=SURFACE)),
                       text=[f"{v:.3f}" for v in P[TS[start]]], textposition="outside",
                       hovertemplate="%{x}: p = %{y:.3f}<extra></extra>"))
steps = [dict(method="update", label=f"T = {T:g}",
              args=[{"y": [r5(P[T])], "text": [[f"{v:.3f}" for v in P[T]]]},
                    {"title.text": f"§8 · softmax(logits ÷ T) at T = {T:g}: entropy {entropy_bits(P[T]):.2f} bits "
                                   f"(TOY logits 2.0, 1.5, 0.5, −1.0)"}]) for T in TS]
fig.update_layout(title=f"§8 · softmax(logits ÷ T) at T = 1: entropy {entropy_bits(P[1.0]):.2f} bits "
                        f"(TOY logits 2.0, 1.5, 0.5, −1.0)",
                  height=460, yaxis=dict(title="probability", range=[0, 1.05]), showlegend=False,
                  sliders=[dict(active=start, steps=steps, currentvalue=dict(prefix="temperature: "),
                                pad=dict(t=40))])
fig.show()
''')

# =====================================================================================================================
md(r"""
## 9 · Each provider counts and samples its own way

**What this verifies** (lesson step 9, `#providers`). A small table of dated facts; **no call** is made. The only checks are what the installed groq SDK can confirm locally: Groq's chat call has a `temperature`, an `n` and a `seed`, and **no** `top_k` parameter.

Claude's SDK is not installed in this environment, and Cohere's tokenizer download needs a key, so their rows stay as dated doc facts.
""")
code(r'''
import pandas as pd

PROVIDERS = pd.DataFrame([
    dict(provider="Groq · openai/gpt-oss-20b", temperature="0 to 2, default 1; 0 is sent as 1e-8",
         reasoning="reasoning_effort low / medium / high (default medium; course: low)",
         counting="o200k_harmony locally; the bill is usage.prompt/completion_tokens",
         source="Groq API reference, OpenAI compatibility, Reasoning pages [P1-2..4], read 2026-10-17"),
    dict(provider="Claude (Haiku / Sonnet / Opus 5.5)", temperature="not accepted: sending it returns 400",
         reasoning="effort instead (thinking on by default)",
         counting="its own tokenizer; free count_tokens call, an estimate, per model",
         source="Anthropic token counting [P1-15]; claude-api skill table cached 2026-10-06 [P1-16]"),
    dict(provider="Cohere chat", temperature="default 0.3", reasoning="-",
         counting="a tokenizer per model (tokenize endpoint needs a key)",
         source="Cohere docs [P1-17], [P1-18], read 2026-10-17"),
])
display(PROVIDERS.style.hide(axis="index").set_properties(**{"text-align": "left", "white-space": "normal"}))

params = inspect.signature(groq_completions.Completions.create).parameters
check("§9 Groq create(): has temperature, n, seed; has no top_k",
      ["temperature" in params, "n" in params, "seed" in params, "top_k" in params], [True, True, True, False])
''')

# =====================================================================================================================
md(r"""
## 10 · Price it: output costs 4× input

**What this verifies** (lesson step 10, `#cost`; fact K7). Formula: cost of one call ≤ (input tokens × input price + output cap × output price) ÷ 1,000,000. Dated prices per 1M tokens (LLMOPS_FOUNDATION §6.2, read 2026-10-17): Groq `openai/gpt-oss-20b` $0.075 in / $0.30 out (cached input $0.037); Claude Haiku 5.5 $0.10 / $0.50.
- One v0 call (976 in, cap 512) on Groq ≤ **$0.000227**; 100 calls ≤ **$0.0227**, of which output is **67.7%**.
- Haiku 5.5: 100 calls ≤ **$0.0354** (72.4% output). The 976 is an `o200k_harmony` count used as a stand-in; Claude's own count comes from `count_tokens`.
- Output costs 4× input on Groq, 5× on Haiku. Reasoning tokens bill as output.

The book prices techniques in a different unit: the **number of LLM calls** per query. This section turns calls into tokens and dollars.

**The chart** splits the bound for 100 calls into input and output per model.
""")
code(r'''
PRICES = {"Groq openai/gpt-oss-20b": (0.075, 0.30), "Claude Haiku 5.5": (0.10, 0.50)}   # $ per 1M tokens, read 2026-10-17
CACHED_IN_GROQ = 0.037
COST = {}
for name, (p_in, p_out) in PRICES.items():
    one = (N_IN * p_in + CAP * p_out) / 1e6
    COST[name] = dict(one=one, inp=100 * N_IN * p_in / 1e6, out=100 * CAP * p_out / 1e6,
                      share=CAP * p_out / (N_IN * p_in + CAP * p_out))
    print(f"   {name:24s} one call <= ${one:.6f} ; 100 calls <= ${100*one:.4f} ; output share {100*COST[name]['share']:.1f}%")
G, Hk = COST["Groq openai/gpt-oss-20b"], COST["Claude Haiku 5.5"]
check("§10 Groq: one call, 100 calls, output share % (K7)",
      [round(G["one"], 6), round(100 * G["one"], 4), round(100 * G["share"], 1)], [0.000227, 0.0227, 67.7])
check("§10 Haiku 5.5: one call, 100 calls, output share % (K7)",
      [round(Hk["one"], 6), round(100 * Hk["one"], 4), round(100 * Hk["share"], 1)], [0.000354, 0.0354, 72.4])
check("§10 output price / input price: Groq, Haiku (K7)",
      [round(p_out / p_in, 1) for p_in, p_out in PRICES.values()], [4.0, 5.0])
print(f"   Groq cached input (dated sheet): ${CACHED_IN_GROQ} per 1M tokens; it applies only to repeated prompt prefixes.")

fig = go.Figure()
names = list(COST)
fig.add_bar(x=names, y=[round(COST[n]["inp"], 6) for n in names], name=f"input ({N_IN} tokens per call)",
            marker=dict(color=BLUE, line=dict(width=2, color=SURFACE)),
            hovertemplate="%{x}<br>input: $%{y:.4f} per 100 calls<extra></extra>")
fig.add_bar(x=names, y=[round(COST[n]["out"], 6) for n in names], name=f"output (cap {CAP} per call)",
            marker=dict(color=ORANGE, line=dict(width=2, color=SURFACE)),
            customdata=[round(100 * COST[n]["share"], 1) for n in names],
            hovertemplate="%{x}<br>output: $%{y:.4f} per 100 calls (%{customdata}% of the bound)<extra></extra>")
fig.update_layout(barmode="stack", height=420, yaxis=dict(title="$ for 100 calls (upper bound at the cap)", tickformat="$.3f"),
                  title="§10 · Cost of 100 v0 calls: output dominates at the cap (formula; prices read 2026-10-17)")
fig.show()
''')

# =====================================================================================================================
md(r"""
## 11 · Time it: limits are tokens per minute

**What this verifies** (lesson step 11, `#time`; fact K7). A rate limit in tokens per minute (TPM) sets a floor on run time: time ≥ total tokens ÷ TPM.
- One v0 call uses about 976 + 71 + 512 = **1,559** tokens (input, template, output cap).
- 100 calls = **155,900** tokens; at 8,000 TPM that is at least **19.5 minutes**, whatever the price.
- A 55-question run = 85,745 tokens, at least 10.7 minutes.

The 8,000 TPM and 200K tokens-per-day limits are the free-plan row for gpt-oss-20b in the course's notes; which plan applies to the learner's account is UNVERIFIED.
""")
code(r'''
TPM = 8000
for calls, exp_tokens, exp_min in ((100, 155900, 19.5), (55, 85745, 10.7)):
    total = calls * per_call
    check(f"§11 {calls} calls: tokens, minimum minutes at {TPM:,} TPM (K7)", [total, round(total / TPM, 1)],
          [exp_tokens, exp_min])
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
