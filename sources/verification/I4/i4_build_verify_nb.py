"""Build study/notebooks/I4_propositions_verify.ipynb: the "verify it yourself" notebook for I4 (proposition chunking).

The notebook rebuilds every measured number and chart of the I4 lesson (study/lessons/I4_propositions.html) from code,
one section per lesson step (1-12), and compares each value with the expected value in a `check(...)` line. Expected
values are copied from sources/verification/I4/out_i4_kit_measure.txt (K1-K12, i4_kit_measure.py; listed in
I4_FACTS.md). The code paths are those of i4_kit_measure.py (the same splitter `split_page`, `words` / `stem` / `STOP`,
`check_prop`, the three scorings, the cost plan and the 8-gram test), so the numbers come out identical.

The notebook is self-contained: it imports nothing from sources/. It reads the climate PDF and the upstream notebook
(one level above the workspace), 06 (the draft seeds) and the JSONL / prompt / schema files in sources/verification/I4/.
It rebuilds v0's 97 chunks with its own copy of the 07 H.1 recursive splitter and checks chunks.jsonl's sha256 (K1).

Honesty labels carried into the notebook: the 40 propositions are hand-written by the tutor (no LLM wrote them); the
ranked lists of step 9-10 are made-up orders; no hand faithfulness labels exist; per-call token sizes are ASSUMED.
The MiniLM section of step 9 is an observation, never a check; without sentence-transformers or the cached model it
prints one SKIPPED line.

No Groq, Cohere or Claude call, no .env read, no network (MiniLM, if present, loads from the local cache, offline).

Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I4/i4_build_verify_nb.py
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I4/i4_verify_nb_run.py \
        > sources/verification/I4/out_i4_verify_nb_run.txt                              # executes it, saves outputs
"""
from pathlib import Path
from textwrap import dedent

import nbformat as nbf

WS = Path(__file__).resolve().parents[3]                      # rag_learning/
OUT = WS / "study" / "notebooks" / "I4_propositions_verify.ipynb"

CELLS = []


def md(s):
    CELLS.append(nbf.v4.new_markdown_cell(dedent(s).strip()))


def code(s):
    CELLS.append(nbf.v4.new_code_cell(dedent(s).strip()))


# =====================================================================================================================
md(r"""
# I4 · Verify it yourself: proposition chunking

**What this is:** a notebook that rebuilds every measured number and chart of the I4 lesson (`study/lessons/I4_propositions.html`) from real code, so you can see each one being made and change the inputs.
**What this is not:** a recorded LLM run. **No LLM has written a proposition yet.** The notebook makes **no API call**: no Groq, no Cohere, no Claude. It checks the *mechanism* (units, spans, alignment, parents, scorings, cost) on propositions that a person wrote.

**How to use it.** Run all cells from the top (VS Code: *Run All*). The sections are numbered like the lesson's steps, 1 to 12. Each one has:
- a short note on what it verifies (the lesson step, its anchor, and the facts rows K1–K12);
- a code cell that **computes** the values;
- `check(...)` lines: `PASS` means the code produced the number the lesson uses, `FAIL` means it did not;
- an interactive chart where one is worth seeing. Hover for values.

The last cell counts the checks.

**Read these labels before any number.**
- The 40 propositions in `sources/verification/I4/i4_tutor_props.jsonl` are **hand-written by the tutor** (2026-10-18) from the PyMuPDF page text. They stand in for the recorded LLM run that does not exist yet. They show how the checks work; they are not a measurement of what an LLM writes.
- The 6 propositions in `i4_planted_props.jsonl` are **deliberate mistakes**, written to test the checks.
- The ranked lists in steps 9 and 10 are **made-up orders**, not model output.
- There are **no hand faithfulness labels** yet. Step 7's Wilson intervals are formula outputs.
- The per-call token sizes in step 11 are **ASSUMED** (research I4 §9).

**Other labels used for numbers.** *measured* = computed here from the real PDF or the real upstream notebook; *toy* = made-up vectors that show a mechanism; *formula* = arithmetic; *derived* = computed from another measured ratio; *cited* = from a paper or library source, not re-run here.

**The running example.** Draft question **D-002**, "In what year was the Paris Agreement adopted?", against v0's **97 chunks** of the climate PDF (the 07 recursive chunker, per page, 1,000 characters with 200 overlap). D-005 (coal vs natural gas) and D-007 (two hops: UNFCCC, then COP) are the guards. The 10 draft questions and their evidence spans come from 06 §6.7. They were drafted by an LLM and are not yet checked by you, so every rank here is an **illustration, not an evaluation result**.

**Where the expected values come from.** `sources/verification/I4/out_i4_kit_measure.txt` (sections K1–K12 of `i4_kit_measure.py`), listed with their labels in `I4_FACTS.md`. The whole notebook runs in a few seconds on a CPU.
""")

code(r'''
# Setup: imports, paths, the corpus, the 97 chunks, the draft questions, the units and the shared helpers. Run first.
import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")          # MiniLM (step 9, optional) may load from the local cache only
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

import hashlib
import importlib.metadata as md
import json
import math
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pymupdf                                        # pinned 1.26.7
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
UP = WS.parent / "upstream" / "RAG_Techniques"
PDF = UP / "data" / "Understanding_Climate_Change.pdf"
UPNB = UP / "all_rag_techniques" / "proposition_chunking.ipynb"
I4 = WS / "sources" / "verification" / "I4"           # data files only (JSONL, prompt, schema): nothing is imported
print("workspace:", WS)
print("python", sys.version.split()[0], {p: md.version(p) for p in ("pymupdf", "numpy", "plotly", "jsonschema")})

# ---------------------------------------------------------------- check(): computed value vs the expected value
CHECKS, SKIPPED = [], []
T3, T2 = 5e-4, 5e-3                   # tolerances for values printed with 3 or 2 decimals


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
    """PASS when the computed value equals the expected value from out_i4_kit_measure.txt (numbers within `tol`)."""
    ok = _same(got, expected, tol)
    CHECKS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}: got {_show(got)}  |  expected {_show(expected)}"
          + (f"  (tolerance {tol:g})" if tol else ""))


def skip(name, reason):
    SKIPPED.append((name, reason))
    print(f"SKIPPED ({reason})  {name}")


# ---------------------------------------------------------------- chart style (light surface, fixed colour order)
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
BLUE, ORANGE, AQUA, RED = "#2a78d6", "#eb6834", "#1baf7a", "#c8323c"
pio.templates["i4"] = go.layout.Template(layout=dict(
    font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', size=13, color=INK2),
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, colorway=[BLUE, ORANGE, AQUA],
    xaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    yaxis=dict(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, showline=True, ticks="", automargin=True),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=INK2)),
    title=dict(x=0, xanchor="left", font=dict(size=15, color=INK)),
    margin=dict(l=70, r=30, t=90, b=60), hoverlabel=dict(font_size=12)))
pio.templates.default = "i4"


def bar_style(colour):
    return dict(color=colour, line=dict(width=2, color=SURFACE))


# ---------------------------------------------------------------- K1 environment and corpus
check("environment: pymupdf version (pinned) (K1)", md.version("pymupdf"), "1.26.7")
pdf_bytes = PDF.read_bytes()
check("corpus: PDF sha256 (K1)", hashlib.sha256(pdf_bytes).hexdigest(), "1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669")
pages = [p.get_text() for p in pymupdf.open(PDF)]
DOC = "\n".join(pages)                                # the document text: pages joined with "\n" (06 §5.3)
STARTS, _pos = [], 0
for _t in pages:
    STARTS.append(_pos)
    _pos += len(_t) + 1
check("corpus: pages, document characters (K1)", [len(pages), len(DOC)], [33, 72593])

# snapshot_id: the 06 §5.3 recipe, transcribed (parser pymupdf@VersionBind, no options, no cleaning, page_join "\n")
_parts = ["snapshot-v1", f"parser=pymupdf@{pymupdf.VersionBind}", "options=" + json.dumps({}, sort_keys=True),
          "cleaning=none", "page_join=\\n"]                  # literal backslash + "n", as the recipe says
_parts += [f"climate:{hashlib.sha256(DOC.encode('utf-8')).hexdigest()}"]
SNAP = hashlib.sha256("|".join(_parts).encode("utf-8")).hexdigest()[:12]
check("corpus: snapshot_id (K1)", SNAP, "ea07572562ac")


# ---------------------------------------------------------------- the 97 parents: own copy of the 07 H.1 recursive splitter
def _split_spans(text, start, end, seps, size):
    """Recursively cut [start, end) into contiguous pieces of <= size chars, preferring early separators (07 H.1)."""
    if end - start <= size:
        return [(start, end)]
    if not seps:
        return [(s, s + 1) for s in range(start, end)]
    sep, rest = seps[0], seps[1:]
    pieces, i = [], start
    while i < end:
        j = text.find(sep, i, end)
        if j == -1:
            pieces.append((i, end))
            break
        pieces.append((i, j + len(sep)))
        i = j + len(sep)
    out = []
    for a, b in pieces:
        out.extend([(a, b)] if b - a <= size else _split_spans(text, a, b, rest, size))
    return out


def recursive_spans(text, size, overlap, separators=("\n\n", "\n", " ")):
    """07 H.1 recursive_chunks, returning (start, end) spans: greedy merge up to `size`, whole trailing pieces as overlap."""
    if not text:
        return []
    pieces = _split_spans(text, 0, len(text), separators, size)
    spans, cur = [], []
    for p in pieces:
        if cur and p[1] - cur[0][0] > size:
            spans.append((cur[0][0], cur[-1][1]))
            keep = []
            for q in reversed(cur):
                if cur[-1][1] - q[0] <= overlap:
                    keep.insert(0, q)
                else:
                    break
            cur = keep
            while cur and p[1] - cur[0][0] > size:
                cur.pop(0)
        cur.append(p)
    if cur:
        spans.append((cur[0][0], cur[-1][1]))
    return spans


CHUNKING = {"name": "recursive_char", "unit": "chars", "chunk_size": 1000, "chunk_overlap": 200,
            "separators": ["\n\n", "\n", " ", ""], "scope": "per_page"}
PH = hashlib.sha256(json.dumps(CHUNKING, sort_keys=True).encode("utf-8")).hexdigest()[:12]
_spans = [(pn, STARTS[pn - 1] + a, STARTS[pn - 1] + b) for pn, t in enumerate(pages, 1) for a, b in recursive_spans(t, 1000, 200)]
chunks = [{"doc_id": "climate", "snapshot_id": SNAP, "chunk_id": f"climate:{SNAP}:{PH}:{seq:05d}", "seq": seq,
           "char_start": a, "char_end": b,
           "page_segments": [{"page": pn, "char_start": a - STARTS[pn - 1], "char_end": b - STARTS[pn - 1]}],
           "text": DOC[a:b], "text_sha256": hashlib.sha256(DOC[a:b].encode("utf-8")).hexdigest(),
           "chunker": CHUNKING["name"], "params_hash": PH, "meta": {}}
          for seq, (pn, a, b) in enumerate(_spans)]
SHA_JL = hashlib.sha256("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in chunks).encode("utf-8")).hexdigest()
N = len(chunks)
check("parents: v0's chunks, params_hash (K1)", [N, PH], [97, "1ca9c5a3b548"])
check("parents: chunks.jsonl sha256 (K1; = C2 lab, P3, P4)", SHA_JL, "d4108b8936093394c6eb50d4c22e8d4013d9a048fb38d5769281af4aadb3011b")
TEXTS = {"climate": DOC}


# ---------------------------------------------------------------- 06 §6.7 draft seeds (llm-draft: illustration only)
def section(mdtext, heading_prefix):
    """The Markdown section that starts with this heading (fence-aware), up to the next heading of the same level."""
    lines, fence, start, level = mdtext.splitlines(), False, None, None
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = re.match(r"^(#+)\s+(.*)$", ln)
        if not m:
            continue
        if start is None and m.group(2).startswith(heading_prefix):
            start, level = i, len(m.group(1))
        elif start is not None and len(m.group(1)) <= level:
            return "\n".join(lines[start:i])
    if start is None:
        raise KeyError(heading_prefix)
    return "\n".join(lines[start:])


def code_blocks(mdtext, lang):
    return re.findall(r"^```" + re.escape(lang) + r"[ \t]*\n(.*?)^```", mdtext, flags=re.S | re.M)


# ---------------------------------------------------------------- the evidence rules (06 §7.2-7.3), as the course's reference scorer
def _merge(ranges):
    out = []
    for a, b in sorted(ranges):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def _covered_fraction(segments, ranges, texts):
    """Share of the segments' NON-WHITESPACE characters that the ranges cover (document offsets)."""
    total = hit = 0
    for doc, a, b in segments:
        union = _merge([(x, y) for d, x, y in ranges if d == doc])
        t = texts[doc]
        for i in range(a, b):
            if t[i].isspace():
                continue
            total += 1
            if any(x <= i < y for x, y in union):
                hit += 1
    return 1.0 if total == 0 else hit / total


def ce(groups, ranges, texts):
    """complete evidence: every group has an alternative whose non-whitespace characters are all covered."""
    return int(all(max(_covered_fraction(alt, ranges, texts) for alt in g) == 1.0 for g in groups))


def rel(rng, groups, texts):
    """any_overlap: the range overlaps >= 1 non-whitespace character of any segment of any alternative."""
    d, x, y = rng
    t = texts[d]
    for g in groups:
        for alt in g:
            for doc, a, b in alt:
                if doc == d and any(not t[i].isspace() for i in range(max(a, x), min(b, y))):
                    return 1
    return 0


md06 = (WS / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
SEEDS = [json.loads(line) for line in code_blocks(section(md06, "6.7 Draft seed"), "jsonl")[0].splitlines() if line.strip()]
for s in SEEDS:
    s["G"] = [[[("climate", STARTS[seg["page"] - 1] + seg["char_start"], STARTS[seg["page"] - 1] + seg["char_end"])
                for seg in alt["segments"]] for alt in g["alternatives"]] for g in s["evidence_groups"]]
ANS = [s for s in SEEDS if s["answerable"]]
BYQ = {s["qid"]: s for s in SEEDS}
REL = {s["qid"]: [i for i in range(N) if rel(("climate", chunks[i]["char_start"], chunks[i]["char_end"]), s["G"], TEXTS)]
       for s in ANS}
check("draft seeds: 10, of which 8 answerable (K1)", [len(SEEDS), len(ANS)], [10, 8])
check("relevant chunk seqs per answerable seed (K1)", REL,
      {"D-001": [7], "D-002": [27], "D-003": [68], "D-004": [23, 67, 68], "D-005": [3, 4], "D-006": [21],
       "D-007": [27, 85], "D-008": [69]})

# ---------------------------------------------------------------- the units: the sentence splitter (explained in step 4)
SENT_END = re.compile(r'[.!?]["”)\]]?(?=\s|$)')
LINE_END = re.compile(r'[.!?:]["”)\]]?\s*$')


def split_page(t):
    """Units of one page as (kind, a, b), page-relative offsets, whitespace trimmed. kind 'h' = heading line,
    's' = sentence. A heading is a short line (< 80 chars) that starts with a capital letter, has no end
    punctuation, and is not inside an unfinished sentence. A sentence ends at . ! ? followed by whitespace."""
    units, buf, pos = [], None, 0
    for ln in t.split("\n"):
        a, s = pos, ln.strip()
        pos += len(ln) + 1
        if not s:
            continue
        a2 = a + len(ln) - len(ln.lstrip())
        b2 = a + len(ln.rstrip())
        if buf is None and not LINE_END.search(s) and s[0].isupper() and len(s) < 80:
            units.append(("h", a2, b2))
            continue
        if buf is None:
            buf = a2
        for mt in SENT_END.finditer(ln):
            e = a + mt.end()
            if e <= buf:
                continue
            units.append(("s", buf, e))
            buf = None
            rest = ln[mt.end():]
            if rest.strip():
                buf = a + mt.end() + len(rest) - len(rest.lstrip())
    if buf is not None:
        units.append(("s", buf, len(t.rstrip())))
    return units


UNITS = {}                                            # "page:i" -> unit
for pn, t in enumerate(pages, 1):
    for i, (k, a, b) in enumerate(split_page(t)):
        UNITS[f"{pn}:{i}"] = {"id": f"{pn}:{i}", "page": pn, "kind": k, "a": a, "b": b,
                              "da": STARTS[pn - 1] + a, "db": STARTS[pn - 1] + b, "text": t[a:b]}

# ---------------------------------------------------------------- content words, alignment, parents (steps 3, 6, 7)
STOP = set("""a an the is are was were be been being of in on at to for and or but with by as from that this these those
it its their them they such which who whom whose than then there here into over under about also can may might will would
should could has have had do does did not no nor so very via per each every all both other another some any many much more
most less least only just up down out off our your his her he she we you i if while when where what how why""".split())


def stem(w):
    for suf in ("ing", "ed", "es", "s", "e"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


def words(t):
    """W(t): the content-word stems of a text (lower case, hyphen line breaks joined, stop words dropped)."""
    t = re.sub(r"-\s*\n\s*", "-", t.lower())
    return {stem(w) for w in re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", t) if (len(w) > 1 or w.isdigit()) and w not in STOP}


PRONOUN_START = re.compile(r"^(it|its|they|their|them|this|these|those|that|he|she|his|her|such)\b", re.I)


def load(name):
    return [json.loads(l) for l in (I4 / name).read_text(encoding="utf-8").splitlines() if l.strip()]


def check_prop(p):
    """ids and span (C3), alignment with verified resolved names, parents, pronoun start."""
    ids_ok = all(i in UNITS for i in p["source_ids"]) and len(p["source_ids"]) > 0
    r = {"prop_id": p["prop_id"], "ids_ok": ids_ok}
    if not ids_ok:
        r.update(span=None, align=None, parents=[], pronoun=bool(PRONOUN_START.match(p["text"])), resolved_ok=None)
        return r
    us = [UNITS[i] for i in p["source_ids"]]
    a, b = min(u["da"] for u in us), max(u["db"] for u in us)
    first = min(u["da"] for u in us)
    pg = us[0]["page"]
    before = DOC[STARTS[pg - 1]:first]
    resolved_ok = all(words(nm) <= words(before) for nm in p["resolved"])
    allowed = set().union(*(words(u["text"]) for u in us))
    if resolved_ok:
        allowed |= set().union(set(), *(words(nm) for nm in p["resolved"]))
    W = words(p["text"])
    contain = [c["seq"] for c in chunks if c["char_start"] <= a and b <= c["char_end"]]
    overlap = [c["seq"] for c in chunks if c["char_start"] < b and a < c["char_end"]]
    r.update(span=(a, b), inside=0 <= a < b <= len(DOC), align=len(W & allowed) / len(W), unsupported=sorted(W - allowed),
             parents=contain or overlap, contained=bool(contain), pronoun=bool(PRONOUN_START.match(p["text"])),
             resolved_ok=resolved_ok, one_page=len({u["page"] for u in us}) == 1)
    return r


def flat(t):
    """one line: every run of white space (the PDF's line breaks) as one space"""
    return re.sub(r"\s+", " ", t)


def norm_text(t):
    """the normalised text used for distinct-facts@k and near-duplicates"""
    return " ".join(re.findall(r"[a-z0-9.]+", t.lower()))


TUTOR = load("i4_tutor_props.jsonl")                  # hand-written by the tutor, NOT LLM output
PLANT = load("i4_planted_props.jsonl")                # six deliberate mistakes
RT = {p["prop_id"]: check_prop(p) for p in TUTOR}
RP = {p["prop_id"]: check_prop(p) for p in PLANT}
PT = {p["prop_id"]: p for p in TUTOR + PLANT}
check("tutor set: file sha256 (K4)", hashlib.sha256((I4 / "i4_tutor_props.jsonl").read_bytes()).hexdigest(),
      "154a1e34c1fc13fa2af1394c2a1653623f419b495554e6c64691134708d87375")

# ---------------------------------------------------------------- the upstream notebook, read as JSON (never run)
up_bytes = UPNB.read_bytes()
cells = json.loads(up_bytes)["cells"]


def src(i):
    return "".join(cells[i]["source"])


def outs(i):
    return "".join("".join(o.get("text", [])) or "".join(o.get("data", {}).get("text/plain", [])) for o in cells[i].get("outputs", []))


def ranked(i):
    """the saved top-k hits of an upstream retrieval cell: (text, chunk id)"""
    return re.findall(r"\d+\) Content: (.+?) --- Chunk_id: (\d+)", outs(i), re.S)


print(f"\nsetup done in {time.time() - T0:.1f} s: {N} chunks, {len(UNITS)} units, {len(TUTOR)} tutor propositions, "
      f"{len(PLANT)} planted mistakes, {len(cells)} upstream cells")
''')

# =====================================================================================================================
md(r"""
## 1 · One vector for many facts

**What this verifies** (lesson step 1, `#dilution`; facts K8, K1).
- The dilution toy: n made-up fact vectors at right angles; the chunk vector is their normalised mean. Its cosine with a one-fact question is 1/√n (K8). A one-fact distractor at cosine 0.60 wins from n = 3.
- D-002's relevant chunk is chunk 27 (K1). It mixes the UNFCCC, the Paris Agreement, NDCs, carbon pricing and targets: 14 of the 40 tutor propositions have chunk 27 as a parent (K4).
""")
code(r'''
F = np.eye(8)                                          # TOY: 8 orthonormal "fact" vectors
COSN = []
for n in range(1, 9):
    v = F[:n].mean(0)
    v = v / np.linalg.norm(v)                          # the chunk vector: normalised mean of n facts
    COSN.append(float(F[0] @ v))                       # the question asks about fact 0 only
check("§1 cos(one-fact question, n-fact chunk), n = 1..8 (K8, toy)", COSN,
      [1.000, 0.707, 0.577, 0.500, 0.447, 0.408, 0.378, 0.354], T3)
check("§1 the toy equals 1/sqrt(n) (K8, formula)", max(abs(c - 1 / math.sqrt(n)) for n, c in enumerate(COSN, 1)) < 1e-12, True)
check("§1 a one-fact distractor at cos 0.60 beats the right chunk from n = (K8)", next(n for n, c in enumerate(COSN, 1) if c < 0.60), 3)

check("§1 D-002's relevant chunk (K1)", REL["D-002"], [27])
c27 = chunks[27]
heads27 = [u["text"] for u in UNITS.values() if u["kind"] == "h" and c27["char_start"] <= u["da"] and u["db"] <= c27["char_end"]]
print("   chunk 27 (page", c27["page_segments"][0]["page"], f"doc [{c27['char_start']}, {c27['char_end']})) holds these headings:", heads27)
P27 = [pid for pid, r in RT.items() if 27 in r["parents"]]
check("§1 tutor propositions with chunk 27 as a parent (K4)", P27, [f"p10-{i:02d}" for i in range(1, 15)])
for pid in ("p10-01", "p10-07", "p10-11", "p10-14"):
    print(f"   one of chunk 27's facts: {pid} | {PT[pid]['text']}")

fig = go.Figure()
fig.add_scatter(x=list(range(1, 9)), y=np.round(COSN, 3), mode="lines+markers", name="cos(question, n-fact chunk) = 1/√n",
                line=dict(color=BLUE, width=3), marker=dict(size=8), hovertemplate="n = %{x}: cosine %{y:.3f}<extra></extra>")
fig.add_hline(y=0.60, line=dict(color=ORANGE, dash="dash"), annotation_text="a one-fact distractor at 0.60",
              annotation_position="top right")
fig.update_layout(title="§1 · Dilution (toy): the more facts a chunk holds, the weaker its match to a one-fact question",
                  height=380, xaxis=dict(title="facts in the chunk (n)", dtick=1), yaxis=dict(title="cosine", range=[0, 1.05]))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 2 · What a proposition is

**What this verifies** (lesson step 2, `#proposition`; facts K2, K4).
- The upstream notebook `proposition_chunking.ipynb` @ 009adba, read as JSON and never run (cells are 0-based): its sha256 and 40 cells; cell 9's splitter (200 / 50 tokens of the default `gpt2` encoding, MC-001) and embedder; cells 12 and 15's model id (retired upstream) and temperature; cell 12's five rules and its few-shot example.
- Sentence 10:7 becomes three tutor propositions, each one fact.
- Dense X's unit counts (257M propositions / 114M sentences, CITED) give 2.25 propositions per sentence; the tutor set has 1.54.
""")
code(r'''
check("§2 upstream notebook sha256, cells (K2)", [hashlib.sha256(up_bytes).hexdigest(), len(cells)],
      ["dbe9d464be6ddd61701f802926f3081dcd7fd737474ae83ede38925ef6c7f297", 40])
m9 = re.search(r"from_tiktoken_encoder\(\s*chunk_size=(\d+), chunk_overlap=(\d+)", src(9))
check("§2 cell 9: from_tiktoken_encoder chunk_size, chunk_overlap (K2)", [int(m9.group(1)), int(m9.group(2))], [200, 50])
check("§2 cell 9: encoding_name given (no: the library default 'gpt2' applies) (K2)", "encoding_name" in src(9), False)
check("§2 cell 9: the embedder is set here (K2)", re.search(r'model=.([^"]+?).,', src(9)).group(1), "nomic-embed-text:v1.5")
MODELS = sorted(set(re.findall(r'ChatGroq\(model="([^"]+)"', src(12) + src(15))))
check("§2 cells 12 and 15: ChatGroq model ids (retired upstream) (K2)", MODELS, ["llama-3.1-70b-versatile"])
check("§2 cells 12 and 15: temperature=0 in both (K2)", src(12).count("temperature=0") == 1 and src(15).count("temperature=0") == 1, True)
RULES = [f"{a}. {b}" for a, b in re.findall(r"^\s*(\d)\. ([^:]+):", src(12), re.M)]
check("§2 cell 12: the five rules of the system prompt (K2)", RULES,
      ["1. Express a Single Fact", "2. Be Understandable Without Context", "3. Use Full Names, Not Pronouns",
       "4. Include Relevant Dates/Qualifiers", "5. Contain One Subject-Predicate Relationship"])
EX_DOC = re.search(r'"document":\s*\n\s*"([^"]+)"', src(12)).group(1)
EX_PROPS = re.findall(r"'([^']+?\.)'", re.search(r'"propositions":\s*\n\s*"(\[.+?\])"', src(12)).group(1))
check("§2 cell 12: the few-shot document (K2)", EX_DOC,
      "In 1969, Neil Armstrong became the first person to walk on the Moon during the Apollo 11 mission.")
check("§2 cell 12: the few-shot propositions, count and first (K2)", [len(EX_PROPS), EX_PROPS[0]], [5, "Neil Armstrong was an astronaut."])

# one sentence, three propositions (hand-written by the tutor)
FROM_10_7 = [p["prop_id"] for p in TUTOR if p["source_ids"] == ["10:7"]]
print("   [10:7]", re.sub(r"\s+", " ", UNITS["10:7"]["text"]))
for pid in FROM_10_7:
    print(f"      -> {pid}: {PT[pid]['text']}")
check("§2 tutor propositions from sentence 10:7 alone (K4)", FROM_10_7, ["p10-07", "p10-08", "p10-09"])

SRC_SENT = {u for p in TUTOR for u in p["source_ids"] if UNITS[u]["kind"] == "s"}
check("§2 tutor set: propositions, source sentences, per sentence (K4)", [len(TUTOR), len(SRC_SENT), len(TUTOR) / len(SRC_SENT)],
      [40, 26, 1.54], T2)
check("§2 Dense X README: 257M propositions / 114M sentences (CITED counts; K4, K9)", 257 / 114, 2.254, T3)
''')

# =====================================================================================================================
md(r"""
## 3 · Decontextualisation: names instead of pronouns

**What this verifies** (lesson step 3, `#decontext`; facts K4).
- Three source sentences start with a pronoun: 10:4 "It provides…" (the UNFCCC), 29:14 "These meetings…" (COP meetings), 2:2 "It is mined…" (coal). Their propositions name the referent and record it in `resolved`.
- The code check: every resolved name must occur **earlier on the same page**. Then its words count as supported in align(p). 15 of the 40 propositions use a resolved name; none starts with a pronoun.
- The planted x-05 keeps the pronoun, and only the pronoun check catches it. (I5 adds names per chunk instead of per proposition.)
""")
code(r'''
CASES = [("10:4", "p10-03", "UNFCCC"), ("29:14", "p29-04", "COP"), ("2:2", "p02-04", "Coal")]
for uid, pid, name in CASES:
    u = UNITS[uid]
    before = DOC[STARTS[u["page"] - 1]:u["da"]]
    earlier = next(v["id"] for v in UNITS.values() if v["page"] == u["page"] and words(name) <= words(v["text"]))
    print(f"   [{uid}] {flat(u['text'])[:60]}...\n      -> {pid}: {PT[pid]['text']}\n"
          f"      resolved {PT[pid]['resolved']}; first unit on the page that holds the name: [{earlier}]; "
          f"in the text before the sentence: {words(name) <= words(before)}")
check("§3 the three source sentences start with a pronoun (K3, K4)",
      [bool(PRONOUN_START.match(UNITS[u]["text"])) for u, _, _ in CASES], [True, True, True])
check("§3 their resolved names (K4)", [PT[p]["resolved"] for _, p, _ in CASES], [["UNFCCC"], ["COP"], ["Coal"]])
check("§3 every resolved name occurs earlier on the same page (K4)", all(r["resolved_ok"] for r in RT.values()), True)
check("§3 propositions that use a resolved name (K4)", sum(bool(p["resolved"]) for p in TUTOR), 15)
check("§3 pronoun-initial tutor propositions (K4, C7)", [k for k, r in RT.items() if r["pronoun"]], [])
check("§3 planted x-05 ('It provides…'): pronoun check, align (K5)", [RP["x-05"]["pronoun"], RP["x-05"]["align"]], [True, 1.0])

# what the name check stops: a name the page has not used before the sentence (a MADE-UP proposition, printed only)
demo = {"prop_id": "demo", "page": 10, "text": "The UNFCCC was signed in Rio.", "source_ids": ["10:4"], "resolved": ["Rio"]}
r_demo = check_prop(demo)
print(f"   made-up demonstration: resolved ['Rio'] is not on p.10 before 10:4 -> resolved_ok {r_demo['resolved_ok']}, "
      f"align {r_demo['align']:.3f}, unsupported {r_demo['unsupported']}")
''')

# =====================================================================================================================
md(r"""
## 4 · Number the units first

**What this verifies** (lesson step 4, `#units`; facts K3).
- The splitter (`split_page` in the setup cell): headings are their own units, a sentence ends at . ! ? followed by white space, and every unit keeps its offsets, so `DOC[da:db] == text` for all of them.
- Counts on the 33 pages: 621 sentences and 286 headings (907 units); per page min 6 / median 19 / max 22; 614 sentences of at least 4 words.
- p.10: units 10:0–10:26 (16 sentences, 11 headings). The five splitter tests, and the known limits (23:0 = "resources.", the end of a p.22 sentence).
""")
code(r'''
PER_PAGE = [(pn, sum(u["kind"] == "s" for u in UNITS.values() if u["page"] == pn),
             sum(u["kind"] == "h" for u in UNITS.values() if u["page"] == pn)) for pn in range(1, len(pages) + 1)]
NS = [s for _, s, _ in PER_PAGE]
check("§4 sentences per page (K3)", {p: s for p, s, _ in PER_PAGE},
      {1: 18, 2: 20, 3: 20, 4: 22, 5: 21, 6: 21, 7: 16, 8: 18, 9: 21, 10: 16, 11: 18, 12: 18, 13: 19, 14: 20, 15: 19, 16: 19,
       17: 20, 18: 18, 19: 19, 20: 18, 21: 20, 22: 19, 23: 19, 24: 19, 25: 19, 26: 21, 27: 18, 28: 21, 29: 20, 30: 18, 31: 19,
       32: 21, 33: 6})
check("§4 sentences, headings, units (K3)", [sum(NS), sum(h for _, _, h in PER_PAGE), len(UNITS)], [621, 286, 907])
check("§4 sentences per page: min, median, max (K3)", [min(NS), sorted(NS)[len(NS) // 2], max(NS)], [6, 19, 22])
check("§4 sentences of >= 4 words (K3; research's rough pdftotext count: about 620)",
      sum(len(re.findall(r"\S+", u["text"])) >= 4 for u in UNITS.values() if u["kind"] == "s"), 614)
check("§4 every unit satisfies DOC[da:db] == text (K3)", all(DOC[u["da"]:u["db"]] == u["text"] for u in UNITS.values()), True)

P10 = [u for u in UNITS.values() if u["page"] == 10]
for u in P10[:8]:
    print(f"   [{u['id']}] {u['kind']} page [{u['a']}, {u['b']}) doc [{u['da']}, {u['db']}) {u['text'][:70]!r}")
print("   ...")
check("§4 p.10: units, sentences, headings; last id (K3)",
      [len(P10), sum(u["kind"] == "s" for u in P10), sum(u["kind"] == "h" for u in P10), P10[-1]["id"]], [27, 16, 11, "10:26"])
check("§4 p.10 heading ids (K3)", [u["id"] for u in P10 if u["kind"] == "h"],
      ["10:0", "10:1", "10:2", "10:6", "10:9", "10:10", "10:13", "10:17", "10:21", "10:22", "10:26"])
check("§4 10:7 page and document offsets (K3)", [UNITS["10:7"][k] for k in ("a", "b", "da", "db")], [438, 625, 20993, 21180])

TESTS = {
    "'1.5 degrees' stays inside one sentence (10:7)": "1.5 degrees Celsius." in UNITS["10:7"]["text"],
    "'pre-industrial' and the line break stay inside 10:7": "pre-industrial" in UNITS["10:7"]["text"],
    "heading 'Paris Agreement' is its own unit (10:6)": UNITS["10:6"]["kind"] == "h" and UNITS["10:6"]["text"] == "Paris Agreement",
    "lower-case page start is not a heading (29:0)": UNITS["29:0"]["kind"] == "s",
    "'market-\\nbased' kept inside 29:2": "market-\nbased" in UNITS["29:2"]["text"],
}
check("§4 the five splitter tests (K3)", list(TESTS.values()), [True] * 5)
check("§4 known limit: page-start fragment 23:0 (K3)", UNITS["23:0"]["text"], "resources.")
check("§4 known limit: 'e.g.' would split a sentence; occurrences in the PDF (K3)", DOC.count("e.g."), 0)

fig = go.Figure()
fig.add_bar(x=[p for p, _, _ in PER_PAGE], y=NS, name="sentences", marker=bar_style(BLUE),
            hovertemplate="p.%{x}: %{y} sentences<extra></extra>")
fig.add_bar(x=[p for p, _, _ in PER_PAGE], y=[h for _, _, h in PER_PAGE], name="headings", marker=bar_style(ORANGE),
            hovertemplate="p.%{x}: %{y} headings<extra></extra>")
fig.update_layout(title="§4 · Units per page: 621 sentences and 286 headings, each with its own id page:i", barmode="stack",
                  height=380, xaxis=dict(title="page", dtick=2), yaxis=dict(title="units"))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 5 · The prompt and the output schema

**What this verifies** (lesson step 5, `#prompt`; facts K10, K2).
- The frozen prompt `prop_gen_v1.txt` and schema `proposition_set_v1.json`: their sha256, the schema's required fields, the template size, and the prompt rendered for p.10 (3,858 characters, about 682 tokens; the token count is DERIVED from P1's ratio, since no tokenizer runs here).
- The rendered units look like `[10:0] (heading) …`.
- Validation, shown on the prompt's own example output and on two broken replies (made up here): a missing `source_ids` fails the schema, and a reply cut off by `finish_reason=length` fails to parse. Both are **logged as failures**, never turned into an empty list (the LangChain template's silent fallback, CITED).
- The prompt's example (a town library) is from outside the corpus and every example proposition is supported (align 1); upstream's example adds "astronaut" (step 7).
""")
code(r'''
PROMPT = (I4 / "prop_gen_v1.txt").read_text(encoding="utf-8")
SCHEMA = json.loads((I4 / "proposition_set_v1.json").read_text(encoding="utf-8"))
check("§5 prop_gen_v1.txt sha256 (K10)", hashlib.sha256(PROMPT.encode("utf-8")).hexdigest(),
      "bdff5976641a8a32316cc84425bd3ecd81ee22d556c95fd523296d6d50934dd1")
check("§5 proposition_set_v1.json sha256 (K10)", hashlib.sha256((I4 / "proposition_set_v1.json").read_bytes()).hexdigest(),
      "9aaced8e41d8c531cfa68e2b8dba29a2e117fc95415afdfa6a97fc602ca9e64f")
check("§5 schema: required fields of a proposition (K10)", SCHEMA["properties"]["propositions"]["items"]["required"], ["text", "source_ids"])
TOK_PER_CHAR = 12840 / 72593                          # DERIVED: P1's measured o200k_harmony tokens / characters


def render(pn):
    lines = []
    for u in (u for u in UNITS.values() if u["page"] == pn):
        txt = re.sub(r"\s+", " ", u["text"])
        lines.append(f"[{u['id']}] " + ("(heading) " if u["kind"] == "h" else "") + txt)
    return PROMPT.replace("{units}", "\n".join(lines))


R10 = render(10)
check("§5 template characters; rendered p.10 characters; about tokens (DERIVED) (K10)",
      [len(PROMPT), len(R10), round(len(R10) * TOK_PER_CHAR)], [1506, 3858, 682])
FIRST3 = R10.split("Page:\n")[1].splitlines()[:3]
check("§5 rendered p.10 units, first 3 lines (K10)", FIRST3,
      ["[10:0] (heading) Chapter 6: Global and Local Climate Action", "[10:1] (heading) International Collaboration",
       "[10:2] (heading) United Nations Framework Convention on Climate Change (UNFCCC)"])
print("   ... the p.10 sentence 10:7 as the model sees it:", next(l for l in R10.splitlines() if l.startswith("[10:7]")))

# validate: parse, then the schema, then log; never silently empty (demonstration on made-up replies)
import jsonschema


def parse_reply(raw, page, log):
    try:
        obj = json.loads(raw)
        jsonschema.validate(obj, SCHEMA)
        return obj["propositions"]
    except (json.JSONDecodeError, jsonschema.ValidationError) as e:
        log.append({"page": page, "error": type(e).__name__, "detail": str(e).splitlines()[0][:80]})
        return None                                    # None = failed and logged; [] would hide the page


EXAMPLE_OUT = PROMPT.split("Example output:\n")[1].split("\n\nPage:")[0]
LOG = []
replies = {"the prompt's own example output": EXAMPLE_OUT,
           "made up: a proposition without source_ids": '{"propositions": [{"text": "The Paris Agreement was adopted in 2015."}]}',
           "made up: a reply cut off (finish_reason=length)": EXAMPLE_OUT[:120]}
for what, raw in replies.items():
    got = parse_reply(raw, 10, LOG)
    print(f"   {what}: " + (f"{len(got)} propositions, schema-valid" if got is not None else f"FAILED and logged -> {LOG[-1]}"))
print(f"   parse-failure log: {len(LOG)} of {len(replies)} replies (each failure is a logged row, not an empty page)")

# the example's propositions are supported by the example units ("town library" resolved from [0:0]/[0:1])
EX_UNITS = {m.group(1): m.group(2) for m in re.finditer(r"^\[(0:\d)\] (?:\(heading\) )?(.+)$", PROMPT, re.M)}
for pr in json.loads(EXAMPLE_OUT)["propositions"]:
    allowed = set().union(*(words(EX_UNITS[i]) for i in pr["source_ids"])) | words("town library")
    W = words(pr["text"])
    print(f"   example align {len(W & allowed) / len(W):.3f} | {pr['text']}")
print(f"   upstream cells 12 and 15 ask for {MODELS[0]!r}, a model id Groq has retired: read the id from config and record the id returned")
''')

# =====================================================================================================================
md(r"""
## 6 · Every proposition points back to its source

**What this verifies** (lesson step 6, `#anchor`; facts K4).
- span(p) = [min aᵢ, max bᵢ) over the units i in `source_ids`, all on one page. Every source id exists, every span lies inside the document, every proposition's sources are on one page (C3).
- Parents by containment: every span lies fully inside a v0 chunk (40/40); 34 propositions have 1 parent and **6 have 2** (the 200-character overlap); the primary parent is the lowest seq.
- Why a proposition cannot be a `Chunk`: 06 §2.3 requires `doc_text[char_start:char_end] == text`, and a rewritten text is not a slice of the document. So it is stored as an **IndexUnit**: the text to embed, plus the evidence span and the parents.
- Then a cell for **your own propositions** (p.29, units 29:7–29:9).
""")
code(r'''
check("§6 every source id exists; every span inside the document; sources on one page (K4, C3)",
      [all(r["ids_ok"] for r in RT.values()), all(r["inside"] for r in RT.values()), all(r["one_page"] for r in RT.values())],
      [True, True, True])
check("§6 span(p10-01) = [min a, max b) of 10:2 and 10:3 (K4)", list(RT["p10-01"]["span"]), [20628, 20765])
check("§6 span(p10-07) = the span of 10:7 (K4)", list(RT["p10-07"]["span"]), [20993, 21180])
NPAR = [len(r["parents"]) for r in RT.values()]
check("§6 spans fully inside a chunk; with 1 parent; with 2 parents (K4)",
      [sum(r["contained"] for r in RT.values()), NPAR.count(1), NPAR.count(2)], [40, 34, 6])
check("§6 the six propositions with two parents (K4)", {k: r["parents"] for k, r in RT.items() if len(r["parents"]) == 2},
      {"p10-12": [27, 28], "p10-13": [27, 28], "p10-14": [27, 28], "p10-22": [28, 29], "p02-05": [3, 4], "p02-06": [3, 4]})
check("§6 primary parent = lowest seq, per page (K4)",
      {pg: sorted({r["parents"][0] for k, r in RT.items() if PT[k]["page"] == pg}) for pg in (2, 10, 23, 29)},
      {2: [3], 10: [27, 28, 29], 23: [68], 29: [85]})

# why it cannot be a Chunk (06 §2.3 invariant), and what it is instead
a, b = RT["p10-07"]["span"]
print(f"   p10-07 text: {PT['p10-07']['text']!r}")
print(f"   DOC[{a}:{b}]: {flat(DOC[a:b])!r}")
print(f"   DOC[char_start:char_end] == text? {DOC[a:b] == PT['p10-07']['text']}  -> it cannot be a Chunk")


@dataclass(frozen=True)
class IndexUnit:
    unit_id: str               # prop_id
    embed_text: str            # what is embedded (a rewrite: NOT a slice of the document)
    evidence_span: tuple       # (doc_id, char_start, char_end): what is scored against gold
    source_ids: tuple          # the units it came from
    parent_seqs: tuple         # the v0 chunks returned to the generator; [0] is the primary parent


IUNITS = [IndexUnit(p["prop_id"], p["text"], ("climate", *RT[p["prop_id"]]["span"]), tuple(p["source_ids"]),
                    tuple(RT[p["prop_id"]]["parents"])) for p in TUTOR]
print("   ", IUNITS[11])
check("§6 the evidence span of every IndexUnit lies inside a parent chunk (K4)",
      all(chunks[u.parent_seqs[0]]["char_start"] <= u.evidence_span[1] and u.evidence_span[2] <= chunks[u.parent_seqs[0]]["char_end"]
          for u in IUNITS), True)

# the p.10 picture: proposition spans under the three parent chunks
fig = go.Figure()
p10 = [p for p in TUTOR if p["page"] == 10]
for seq, colour in ((27, BLUE), (28, AQUA), (29, ORANGE)):
    c = chunks[seq]
    fig.add_bar(y=[f"chunk {seq}"], x=[c["char_end"] - c["char_start"]], base=[c["char_start"]], orientation="h",
                marker=dict(color=colour), name=f"chunk {seq}", hovertemplate=f"chunk {seq}: doc [%{{base}}, {c['char_end']})<extra></extra>")
fig.add_bar(y=[p["prop_id"] for p in p10], x=[RT[p["prop_id"]]["span"][1] - RT[p["prop_id"]]["span"][0] for p in p10],
            base=[RT[p["prop_id"]]["span"][0] for p in p10], orientation="h", name="span(p)",
            marker=dict(color=[RED if len(RT[p["prop_id"]]["parents"]) == 2 else MUTED for p in p10]),
            customdata=[[p["text"], str(RT[p["prop_id"]]["parents"])] for p in p10],
            hovertemplate="%{y}: [%{base}, …) parents %{customdata[1]}<br>%{customdata[0]}<extra></extra>")
fig.update_layout(title="§6 · p.10: each proposition's span(p) under its parent chunks (red = two parents, in the overlap)",
                  height=760, showlegend=False, xaxis=dict(title="document offset (characters)"),
                  yaxis=dict(autorange="reversed", title=""))
fig.show()
''')

md(r"""
### Your turn: write propositions for p.29 "Monitoring and Enforcement"

The cell below prints units 29:6–29:9. Write your own propositions for the three sentences 29:7–29:9 in `MY_PROPS` (one fact each, names instead of "This", `source_ids` from the ids shown; put a name you bring in from earlier on the page in `resolved`). Then run the cell: it prints the same checks as above (ids, span, align, unsupported words, pronoun start, parents). These lines are **printed, not checked**: there is no expected value for your own writing.
""")
code(r'''
for uid in ("29:6", "29:7", "29:8", "29:9"):
    print(f"   [{uid}] {'(heading) ' if UNITS[uid]['kind'] == 'h' else ''}{flat(UNITS[uid]['text'])}")

MY_PROPS = [
    # one example row; add your own below it (one dict per proposition)
    {"prop_id": "my-01", "page": 29, "text": "Ensuring compliance with climate policies requires robust monitoring mechanisms.",
     "source_ids": ["29:7"], "resolved": []},
]

for p in MY_PROPS:
    p.setdefault("resolved", [])
    try:
        r = check_prop(p)
    except ZeroDivisionError:
        print(f"   {p['prop_id']}: no content words in the text")
        continue
    if not r["ids_ok"]:
        print(f"   {p['prop_id']}: a source id does not exist on the page -> fix source_ids | {p['text']}")
        continue
    print(f"   {p['prop_id']} ids={p['source_ids']} span={list(r['span'])} align={r['align']:.3f} unsupported={r['unsupported']} "
          f"pronoun_start={r['pronoun']} resolved_ok={r['resolved_ok']} parents={r['parents']} | {p['text']}")
covered = {u for p in MY_PROPS for u in p["source_ids"]}
print(f"   sentence_coverage of 29:7-29:9: {sum(u in covered for u in ('29:7', '29:8', '29:9'))}/3 (printed, not checked)")
''')

# =====================================================================================================================
md(r"""
## 7 · Checking the rewrite: alignment and its blind spots

**What this verifies** (lesson step 7, `#align`; facts K5, K4, K11).
- align(p) = |W(p) ∩ (W(sources) ∪ W(resolved names))| / |W(p)|, with W = content-word stems (`words`).
- Upstream's few-shot "Neil Armstrong was an astronaut.": align 2/3 = 0.667, so an `align < 0.5` rule would **not** flag it.
- The planted mistakes table: which check catches which. x-03 (dropped "well") and x-04 (wrong referent) have align 1.000: **no code check catches them**, only a person reading against the source.
- The list of every align < 1 (C4): none in the tutor set, x-01 and x-02 in the planted file.
- The hand sample: Wilson 95% intervals for 27/30, 54/60, 51/60, 57/60 (formula outputs; **no labels exist yet**).
""")
code(r'''
WA = words("Neil Armstrong was an astronaut.")
check("§7 astronaut: words, unsupported, align (K5)", [sorted(WA), sorted(WA - words(EX_DOC)), len(WA & words(EX_DOC)) / len(WA)],
      [["armstrong", "astronaut", "neil"], ["astronaut"], 0.667], T3)
AST = len(WA & words(EX_DOC)) / len(WA)
check("§7 astronaut flagged by align < 0.5, by align < 1 (K5)", [AST < 0.5, AST < 1], [False, True])

for p in PLANT:
    r = RP[p["prop_id"]]
    al = r["align"]
    print(f"   {p['prop_id']} [{p['error']}] ids_ok={r['ids_ok']} align={'nan' if al is None else f'{al:.3f}'} "
          f"unsupported={r.get('unsupported')} pronoun={r['pronoun']} | {p['text']}")
check("§7 planted: ids_ok (K5)", [RP[k]["ids_ok"] for k in RP], [True, True, True, True, True, False])
check("§7 planted: align, x-01..x-06 (K5)", [float("nan") if RP[k]["align"] is None else RP[k]["align"] for k in RP],
      [0.400, 0.750, 1.0, 1.0, 1.0, float("nan")], T3)
check("§7 planted: unsupported words x-01, x-02 (K5)", [RP["x-01"]["unsupported"], RP["x-02"]["unsupported"]],
      [["196", "countri", "sign"], ["2016"]])
CHECKS_COLS = ["id check", "align < 0.5", "align < 1", "pronoun check"]


def flags(r):
    al = r["align"]
    return [int(not r["ids_ok"]), int(al is not None and al < 0.5), int(al is not None and al < 1), int(r["pronoun"])]


MATRIX = {k: flags(r) for k, r in RP.items()}
check("§7 the planted-mistake matrix: id, align < 0.5, align < 1, pronoun (K5)", MATRIX,
      {"x-01": [0, 1, 1, 0], "x-02": [0, 0, 1, 0], "x-03": [0, 0, 0, 0], "x-04": [0, 0, 0, 0], "x-05": [0, 0, 0, 1], "x-06": [1, 0, 0, 0]})
check("§7 caught by no code check (K5)", [k for k, v in MATRIX.items() if not any(v)], ["x-03", "x-04"])
check("§7 C4 list, every align < 1: tutor set, planted file (K4, K5)",
      [[k for k, r in RT.items() if r["align"] < 1], [k for k, r in RP.items() if r["align"] is not None and r["align"] < 1]],
      [[], ["x-01", "x-02"]])
check("§7 tutor set: lowest align (K4)", min(r["align"] for r in RT.values()), 1.0)

fig = go.Figure(go.Heatmap(z=[MATRIX[k] + [int(not any(MATRIX[k]))] for k in MATRIX], x=CHECKS_COLS + ["no code check"],
                           y=[f"{k} {PT[k]['error']}" for k in MATRIX], colorscale=[[0, SURFACE], [1, ORANGE]], showscale=False,
                           text=[["caught" if v else "" for v in MATRIX[k] + [int(not any(MATRIX[k]))]] for k in MATRIX],
                           texttemplate="%{text}", xgap=3, ygap=3, hovertemplate="%{y} · %{x}: %{text}<extra></extra>"))
fig.update_layout(title="§7 · The planted mistakes: which code check catches which (x-03 and x-04 need a person)", height=400,
                  yaxis=dict(autorange="reversed"), xaxis=dict(side="top"))
fig.show()

names = ["upstream 'astronaut'"] + [f"{k} {PT[k]['error']}" for k in RP if RP[k]["align"] is not None]
vals = [AST] + [RP[k]["align"] for k in RP if RP[k]["align"] is not None]
fig = go.Figure(go.Bar(x=names, y=np.round(vals, 3), marker=bar_style([ORANGE if v < 1 else BLUE for v in vals]),
                       hovertemplate="%{x}: align %{y:.3f}<extra></extra>"))
fig.add_hline(y=0.5, line=dict(color=RED, dash="dash"), annotation_text="align < 0.5 (misses two)", annotation_position="top left")
fig.add_hline(y=1.0, line=dict(color=MUTED, dash="dot"), annotation_text="align < 1: list for reading", annotation_position="bottom left")
fig.update_layout(title="§7 · align(p): only ADDED words lower it; a dropped qualifier or a wrong referent keeps 1.000",
                  height=380, yaxis=dict(title="align(p)", range=[0, 1.1]), showlegend=False)
fig.show()


def wilson(x, n, z=1.959963984540054):
    p = x / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


SAMPLES = [(27, 30), (54, 60), (51, 60), (57, 60)]
WI = {f"{x}/{n}": [round(v, 3) for v in wilson(x, n)] for x, n in SAMPLES}
check("§7 Wilson 95% intervals (K11, formula; no labels exist)", WI,
      {"27/30": [0.744, 0.965], "54/60": [0.799, 0.953], "51/60": [0.739, 0.919], "57/60": [0.863, 0.983]}, T3)
check("§7 lower bound >= 0.85 (K11)", [wilson(x, n)[0] >= 0.85 for x, n in SAMPLES], [False, False, False, True])
NEED = next(n for n in range(20, 2000, 20) if wilson(n * 19 // 20, n)[0] >= 0.85)
check("§7 smallest multiple of 20 where 95% supported clears 0.85 (K11)", [NEED, NEED * 19 // 20], [60, 57])
fig = go.Figure()
fig.add_scatter(x=[x / n for x, n in SAMPLES], y=list(WI), mode="markers", marker=dict(size=11, color=BLUE),
                error_x=dict(type="data", symmetric=False, array=[wilson(x, n)[1] - x / n for x, n in SAMPLES],
                             arrayminus=[x / n - wilson(x, n)[0] for x, n in SAMPLES], color=BLUE, thickness=2),
                name="supported share, Wilson 95%", hovertemplate="%{y}: %{x:.3f}<extra></extra>")
fig.add_vline(x=0.85, line=dict(color=ORANGE, dash="dash"), annotation_text="0.85", annotation_position="top")
fig.update_layout(title="§7 · A hand-checked sample (formula outputs, no labels yet): only 57/60 clears a lower bound of 0.85",
                  height=340, xaxis=dict(title="supported / labelled", range=[0.7, 1.0]), yaxis=dict(autorange="reversed"))
fig.show()
print("   no hand faithfulness labels exist yet: label the sheet first; the intervals above only show the formula")
''')

# =====================================================================================================================
md(r"""
## 8 · The quality grade is a filter

**What this verifies** (lesson step 8, `#grade`; facts K2, K9).
- Upstream cell 15's grader: 5 examples, **all 10/10/10/10** (no failing example); label typos "Propositons" ×5 and "Evaluation_3" ×2; a human turn `"{proposition}, {original_text}"` with no labels; the same model as the generator.
- Cell 16: threshold 7 on all four grades; the saved output rejects **#17** (completeness 6) and **#31** (conciseness 6), in exactly the format the code prints. Cell 18: 29 embedded, so 31 generated and 2 rejected (0.065).
- The grade is an index-time filter, not an evaluation (D-10, MC-006). Its error rates need your labels: keep-good = kept ∧ good / good and catch-bad = dropped ∧ bad / bad. No labels exist, so they are not computed.
- Calls on Corpus D: generation + batched grading = 66, generation + per-proposition grading = 1,433 (K9).
""")
code(r'''
GRADES = re.findall(r'"accuracy": (\d+), "clarity": (\d+), "completeness": (\d+), "conciseness": (\d+)', src(15))
check("§8 cell 15: grader examples, all 10/10/10/10 (K2)", [len(GRADES), all(g == ("10", "10", "10", "10") for g in GRADES)], [5, True])
check("§8 cell 15: label typos 'Propositons', 'Evaluation_3' (K2)", [src(15).count("Propositons_"), src(15).count("Evaluation_3")], [5, 2])
HUMAN = re.search(r'\("human", "([^"]+)"\)', src(15))
check("§8 cell 15: the human turn (no field labels) (K2)", HUMAN.group(1) if HUMAN else None, "{proposition}, {original_text}")
THR = json.loads(re.search(r"thresholds = (\{[^}]+\})", src(16)).group(1))
check("§8 cell 16: thresholds (K2)", THR, {"accuracy": 7, "clarity": 7, "completeness": 7, "conciseness": 7})
FAILS = re.findall(r"(\d+)\) Propostion: (.+?) \n Scores: (\{[^}]+\})\nFail", outs(16))
FAIL_SCORES = {f"#{n}": json.loads(s.replace("'", '"')) for n, _, s in FAILS}
check("§8 cell 16 saved output: the rejected propositions and their scores (K2)", FAIL_SCORES,
      {"#17": {"accuracy": 8, "clarity": 9, "completeness": 6, "conciseness": 8},
       "#31": {"accuracy": 10, "clarity": 10, "completeness": 8, "conciseness": 6}})
check("§8 the keep rule (every grade >= 7) rejects both (K2)", [all(v >= THR[k] for k, v in s.items()) for s in FAIL_SCORES.values()],
      [False, False])
CODE_PRINTS = ("print(f\"{idx+1}) Propostion: {proposition.page_content} \\n Scores: {scores}\")" in src(16)
               and 'print("Fail")' in src(16))
check("§8 cell 16's code prints exactly that format (the output is consistent with the code) (K2)", CODE_PRINTS, True)
EMB = re.search(r"(\d+)/(\d+) \[", outs(18))
GEN = int(EMB.group(1)) + len(FAILS)
check("§8 cell 18: embedded, generated, rejected, rejected share (K2)", [int(EMB.group(1)), GEN, len(FAILS), len(FAILS) / GEN],
      [29, 31, 2, 0.065], T3)
for n, txt, _ in FAILS:
    print(f"   rejected #{n}: {txt.strip()[:90]}")


def keep_good(kept, good):
    """share of the good propositions (by your labels) that the filter kept"""
    g = [k for k, ok in zip(kept, good) if ok]
    return None if not g else sum(g) / len(g)


def catch_bad(kept, good):
    """share of the bad propositions (by your labels) that the filter dropped"""
    b = [not k for k, ok in zip(kept, good) if not ok]
    return None if not b else sum(b) / len(b)


print("   keep-good and catch-bad: not computed. They need hand labels (supported / added / distorted), and none exist yet.")
check("§8 index-time calls on Corpus D, 33 pages, about 1,400 propositions: gen + batched, gen + per-proposition (K9)",
      [33 + 33, 33 + round(sum(NS) * 257 / 114)], [66, 1433])
''')

# =====================================================================================================================
md(r"""
## 9 · Three ways to score propositions

**What this verifies** (lesson step 9, `#score`; facts K7, K12).
- **Arm (a), parents after dedup (the fair A/B):** rank propositions, map each to its primary parent, keep the first occurrence of each parent; MRR@10 and CE@4 on the parent chunks.
- **Arm (b), proposition spans:** rel(p) = 1 iff span(p) overlaps a gold segment (any_overlap, non-whitespace); CE@4 on ∪ span(p) of the top 4.
- **Text check:** arm (b) counts p only if p's text states the gold fact ("2015" for D-002).
- **(c) page parents:** rejected; with a page as the parent every p.10 proposition counts for D-002.
- The D-002 worked list (a **made-up order**): arm (a) RR 1.000, arm (b) RR 1.000, text check RR 0.333; the top 4 propositions give **2 distinct parents** (k children → ≤ k parents, as `MultiVectorRetriever` returns). Upstream cells 20 and 32: 4 hits, 1 distinct parent (K12).
- MiniLM (optional): an **observation, not a check**.
""")
code(r'''
GOLD_TEXT = {"D-002": ["2015"], "D-007": ["Conference of the Parties", "COP"], "D-005": ["coal", "natural gas"]}


def score_lists(qid, order, k=4, verbose=True):
    """The three scorings of i4_kit_measure.py K7 for one ranked list of prop_ids; returns the numbers."""
    s = BYQ[qid]
    rows = []
    for rank, pid in enumerate(order, 1):
        r = RT[pid]
        relb = rel(("climate", *r["span"]), s["G"], TEXTS)
        rows.append((rank, pid, r["parents"][0], relb))
        if verbose:
            print(f"   {qid} rank {rank}: {pid} parent {r['parents'][0]} (page {chunks[r['parents'][0]]['page_segments'][0]['page']}) "
                  f"span-overlaps-gold={relb} parent-relevant={int(r['parents'][0] in REL[qid])} | {PT[pid]['text']}")
    parents, top_k_parents = [], []
    for _, _, par, _ in rows:
        if par not in parents:
            parents.append(par)
    for _, _, par, _ in rows[:k]:
        if par not in top_k_parents:
            top_k_parents.append(par)
    out = {"parents": parents, "top_k_parents": top_k_parents,
           "rr_a": next((1 / i for i, par in enumerate(parents, 1) if par in REL[qid] and i <= 10), 0.0),
           "ce_a": ce(s["G"], [("climate", chunks[p]["char_start"], chunks[p]["char_end"]) for p in top_k_parents], TEXTS),
           "rr_b": next((1 / rk for rk, _, _, rb in rows if rb and rk <= 10), 0.0),
           "ce_b": ce(s["G"], [("climate", *RT[pid]["span"]) for _, pid, _, _ in rows[:k]], TEXTS),
           "distinct_facts": len({norm_text(PT[pid]["text"]) for _, pid, _, _ in rows[:k]}),
           "rr_text": next((1 / rk for rk, pid, _, rb in rows
                            if rb and rk <= 10 and any(g.lower() in PT[pid]["text"].lower() for g in GOLD_TEXT[qid])), 0.0),
           "rows": rows}
    if verbose:
        print(f"   {qid} arm (a) parents after dedup {parents}; relevant {REL[qid]}; RR {out['rr_a']:.3f}; top {k} -> "
              f"{len(top_k_parents)} distinct parents {top_k_parents}; CE@{k} {out['ce_a']}")
        print(f"   {qid} arm (b) RR {out['rr_b']:.3f}; CE@{k} on the union of the top-{k} spans {out['ce_b']}; "
              f"distinct-facts@{k} {out['distinct_facts']}")
    return out


LISTS = {"D-002": ["p10-08", "p23-02", "p10-07", "p10-10", "p23-01", "p10-09"],            # MADE-UP orders, not model output
         "D-007": ["p29-01", "p10-01", "p10-06", "p10-05", "p29-04", "p10-03"],
         "D-007 swapped": ["p29-01", "p10-01", "p10-06", "p29-04", "p10-05", "p10-03"],
         "D-005": ["p02-01", "p02-02", "p02-04", "p02-03", "p02-05", "p02-06"]}
S = {}
S["D-002"] = score_lists("D-002", LISTS["D-002"])
check("§9 D-002 arm (a): parents after dedup, RR, distinct parents in the top 4, CE@4 (K7)",
      [S["D-002"]["parents"], S["D-002"]["rr_a"], len(S["D-002"]["top_k_parents"]), S["D-002"]["ce_a"]], [[27, 68], 1.0, 2, 1], T3)
check("§9 D-002 arm (b): RR, CE@4, distinct-facts@4 (K7)", [S["D-002"]["rr_b"], S["D-002"]["ce_b"], S["D-002"]["distinct_facts"]],
      [1.0, 1, 3], T3)
TXT_RANK = next(rk for rk, pid, _, rb in S["D-002"]["rows"] if rb and "2015" in PT[pid]["text"])
check("§9 D-002 text check: first rank that overlaps gold AND states '2015'; RR (K7)", [TXT_RANK, S["D-002"]["rr_text"]], [3, 0.333], T3)

# (c) page parents: rejected (printed only)
p10_rel = sum(rel(("climate", STARTS[9], STARTS[9] + len(pages[9])), BYQ["D-002"]["G"], TEXTS) for p in TUTOR if p["page"] == 10)
print(f"   (c) with p.10 as the parent, {p10_rel} of the 25 p.10 propositions count as relevant for D-002: page routing, not ranking")

# MultiVectorRetriever-style return on upstream's own outputs (K12)
for i in (20, 32):
    hits = ranked(i)
    check(f"§9 upstream cell {i}: proposition hits -> distinct parent chunks (K12)", [len(hits), sorted({c for _, c in hits})], [4, ["3"]])

fig = go.Figure()
for name, colour in (("D-002", BLUE), ("D-007", AQUA), ("D-005", ORANGE)):
    rows = score_lists(name, LISTS[name], verbose=False)["rows"]
    xs = list(range(1, 7))
    fig.add_scatter(x=xs, y=[len({par for _, _, par, _ in rows[:k]}) for k in xs], mode="lines+markers", name=f"{name} (made-up order)",
                    line=dict(color=colour, width=3), hovertemplate="top %{x} propositions: %{y} distinct parents<extra></extra>")
fig.add_scatter(x=list(range(1, 7)), y=list(range(1, 7)), mode="lines", name="chunk index: k chunks", line=dict(color=MUTED, dash="dot"))
fig.update_layout(title="§9 · k proposition hits return at most k parents, often fewer (parent dedup)", height=380,
                  xaxis=dict(title="k (propositions retrieved)", dtick=1), yaxis=dict(title="distinct parent chunks", dtick=1))
fig.show()
''')

md(r"""
### MiniLM on the tutor propositions (observation, not a check)

If `sentence-transformers` and `all-MiniLM-L6-v2` are in the local cache, this cell embeds the 40 tutor propositions and the 97 chunks, ranks both for D-002, D-005 and D-007, and prints arm (a), arm (b), the text check and the chunk arm (RR@10 and CE@4). **No reference value exists**, so nothing here is a `check`. The proposition index holds only 40 propositions from 4 pages, while the chunk index holds the whole PDF, so this is not a fair comparison either. If the model is missing, the cell prints one SKIPPED line.
""")
code(r'''
MINI = None
try:
    import logging
    logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
    from sentence_transformers import SentenceTransformer
    MINI = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
except Exception as e:  # noqa: BLE001
    skip("§9 MiniLM observation", "MiniLM not in the local cache")
    print(f"   ({type(e).__name__}: {str(e)[:120]})")

if MINI is not None:
    print("   observation, not a check: MiniLM all-MiniLM-L6-v2, 40 hand-written propositions vs 97 chunks")

    def emb(texts):
        return MINI.encode(list(texts), convert_to_numpy=True, normalize_embeddings=True, batch_size=32, show_progress_bar=False)

    EP, EC = emb([p["text"] for p in TUTOR]), emb([c["text"] for c in chunks])
    for qid in ("D-002", "D-005", "D-007"):
        qv = emb([BYQ[qid]["question"]])[0]
        sp, sc = EP @ qv, EC @ qv
        prop_order = [TUTOR[i]["prop_id"] for i in sorted(range(len(TUTOR)), key=lambda i: (-float(sp[i]), i))]
        chunk_order = sorted(range(N), key=lambda i: (-float(sc[i]), i))
        m = score_lists(qid, prop_order, verbose=False)
        rr_c = next((1 / r for r, i in enumerate(chunk_order, 1) if i in REL[qid] and r <= 10), 0.0)
        ce_c = ce(BYQ[qid]["G"], [("climate", chunks[i]["char_start"], chunks[i]["char_end"]) for i in chunk_order[:4]], TEXTS)
        print(f"   {qid} top 4 propositions {prop_order[:4]}")
        print(f"   {qid} arm (a) RR {m['rr_a']:.3f} CE@4 {m['ce_a']} (parents {m['top_k_parents']}) | arm (b) RR {m['rr_b']:.3f} "
              f"CE@4 {m['ce_b']} | text check RR {m['rr_text']:.3f} | chunks RR {rr_c:.3f} CE@4 {ce_c} (top 4 {chunk_order[:4]})")
''')

# =====================================================================================================================
md(r"""
## 10 · What atomic facts lose

**What this verifies** (lesson step 10, `#relations`; facts K7, K6, K2, K4).
- **D-007 (two hops):** with the made-up order, arm (a) CE@4 = 1 and arm (b) CE@4 = 1. Swap p10-05 to rank 5: arm (a) stays 1, arm (b) drops to **0**, because the p.10 gold span [137, 339) needs the "It provides…" sentence (10:4), and in this list only p10-05 and p10-03 point to it.
- **D-005 (contrast):** the four coal propositions first: arm (a) 1 distinct parent [3], CE@4 1 (both gold spans sit in chunk 3); arm (b) CE@4 **0** (no natural-gas proposition in the top 4).
- **Near-duplicates:** p10-08 and p23-02 have the same normalised text; D-002's distinct-facts@4 = 3. Upstream cells 28 and 36: 3 of the top 4 hits start "Founder Mode is".
- **Coverage ceilings:** sentence_coverage per scope (p.2: 4/6, the methane and fracking sentences left out on purpose) and gold_reachability 6/12 = 0.500, a property of the sample, not of the method.
""")
code(r'''
for name in ("D-007", "D-007 swapped", "D-005"):
    print(f"   --- {name}")
    S[name] = score_lists(name.split()[0], LISTS[name])
check("§10 D-007: arm (a) CE@4, arm (b) CE@4, distinct-facts@4 (K7)", [S["D-007"]["ce_a"], S["D-007"]["ce_b"], S["D-007"]["distinct_facts"]],
      [1, 1, 4])
check("§10 D-007 swapped (p10-05 to rank 5): arm (a) CE@4, arm (b) CE@4 (K7)", [S["D-007 swapped"]["ce_a"], S["D-007 swapped"]["ce_b"]], [1, 0])
check("§10 D-007: arm (a) parents after dedup, RR, both orders (K7)",
      [S["D-007"]["parents"], S["D-007"]["rr_a"], S["D-007 swapped"]["parents"], S["D-007 swapped"]["rr_a"]], [[85, 27], 1.0, [85, 27], 1.0], T3)
g1 = BYQ["D-007"]["evidence_groups"][0]["alternatives"][0]["segments"][0]
check("§10 D-007 group g1: page and page-relative span (K7)", [g1["page"], g1["char_start"], g1["char_end"]], [10, 137, 339])
check("§10 the list's propositions that point to 10:4 ('It provides…') (K7)",
      [pid for pid in LISTS["D-007"] if "10:4" in PT[pid]["source_ids"]], ["p10-05", "p10-03"])
check("§10 D-005: distinct parents in the top 4, arm (a) CE@4, arm (b) CE@4, distinct-facts@4 (K7)",
      [S["D-005"]["top_k_parents"], S["D-005"]["ce_a"], S["D-005"]["ce_b"], S["D-005"]["distinct_facts"]], [[3], 1, 0, 4])
check("§10 D-005: arm (a) RR, arm (b) RR (K7)", [S["D-005"]["rr_a"], S["D-005"]["rr_b"]], [1.0, 1.0], T3)

# near-duplicates
check("§10 p10-08 and p23-02 have the same normalised text (K4)", norm_text(PT["p10-08"]["text"]) == norm_text(PT["p23-02"]["text"]), True)
print("   normalised:", repr(norm_text(PT["p10-08"]["text"])))
for i in (28, 36):
    hits = ranked(i)
    check(f"§10 upstream cell {i}: top-4 hits starting 'Founder Mode is'; distinct chunk ids (K2)",
          [sum("Founder Mode is" in t for t, _ in hits), sorted({c for _, c in hits})], [3, ["1", "2"]])

# coverage ceilings
SCOPES = {"p.10 (whole page)": [u for u in UNITS if UNITS[u]["page"] == 10],
          "p.23 Paris section (23:25-23:27)": ["23:25", "23:26", "23:27"],
          "p.29 COP section (29:12-29:14)": ["29:12", "29:13", "29:14"],
          "p.2 coal and gas paragraphs (2:0-2:2, 2:8-2:10)": ["2:0", "2:1", "2:2", "2:8", "2:9", "2:10"]}
COVERED = {u for p in TUTOR for u in p["source_ids"]}
COV, MISS = {}, {}
for nm, ids in SCOPES.items():
    sent = [u for u in ids if UNITS[u]["kind"] == "s"]
    COV[nm] = f"{sum(u in COVERED for u in sent)}/{len(sent)}"
    MISS[nm] = [u for u in sent if u not in COVERED]
check("§10 sentence_coverage per scope (K6)", list(COV.values()), ["16/16", "3/3", "3/3", "4/6"])
check("§10 sentences with no proposition, p.2 (K6)", MISS["p.2 coal and gas paragraphs (2:0-2:2, 2:8-2:10)"], ["2:9", "2:10"])
for u in MISS["p.2 coal and gas paragraphs (2:0-2:2, 2:8-2:10)"]:
    print(f"   left out: [{u}] {flat(UNITS[u]['text'])}")
SP = [("climate", *RT[p["prop_id"]]["span"]) for p in TUTOR]
alts = reach = 0
REACH = {}
for s in ANS:
    per_g = []
    for g in s["G"]:
        per_alt = [any(rel(sp, [[alt]], TEXTS) for sp in SP) for alt in g]
        alts += len(per_alt)
        reach += sum(per_alt)
        per_g.append(any(per_alt))
    REACH[s["qid"]] = all(per_g)
check("§10 gold_reachability per seed: all groups reachable (K6)", REACH,
      {"D-001": False, "D-002": True, "D-003": True, "D-004": False, "D-005": True, "D-006": False, "D-007": True, "D-008": False})
check("§10 gold_reachability: alternatives reached / alternatives (K6)", [reach, alts, reach / alts], [6, 12, 0.5], T3)
''')

# =====================================================================================================================
md(r"""
## 11 · What it costs

**What this verifies** (lesson step 11, `#cost`; facts K9).
- Measured: 621 sentences. Propositions ≈ 621 × 2.254 = about 1,400 (the Dense X ratio, CITED counts); about 955 at the tutor set's 1.54.
- DERIVED: page input tokens = characters × 0.1769 (P1's ratio): mean 389, p.10 367.
- **ASSUMED** tokens per call (research I4 §9, not measured): generation 1,050 in / 1,600 out, batched grade 1,800 / 1,600, per-proposition grade 870 / 300. Prices $0.075 / $0.30 per 1M tokens, 200K tokens per day and 8K per minute (CITED; the plan row is UNVERIFIED).
- calls = pages (generate) + pages (batched grade) or + propositions (per-proposition grade); index size = n_props × dim × 4 bytes (×14.4 vectors); cost per 1k chunks = Corpus D × 1000 / 97 (DERIVED).
""")
code(r'''
S_TOT = sum(NS)
RATIO = 257 / 114
P_EST = round(S_TOT * RATIO)
P_TUT = round(S_TOT * len(TUTOR) / len(SRC_SENT))
check("§11 sentences; propositions at the Dense X ratio; at the tutor ratio (K9)", [S_TOT, P_EST, P_TUT], [621, 1400, 955])
check("§11 page input tokens, DERIVED: mean, p.10 (K9)",
      [int(f"{sum(len(p) for p in pages) / len(pages) * TOK_PER_CHAR:.0f}"), int(f"{len(pages[9]) * TOK_PER_CHAR:.0f}")], [389, 367])
PRICE_IN, PRICE_OUT, TPD, TPM = 0.075, 0.30, 200_000, 8_000      # CITED (LLMOPS 6.2, prices_2026-10-17.json); plan UNVERIFIED
ASSUME = {"gen": (1050, 1600), "batched": (1800, 1600), "per_prop": (870, 300)}   # ASSUMED (research I4 section 9)


def plan(npages, nprops, grading):
    calls = {"gen": npages, "batched": npages if grading == "batched" else 0, "per_prop": nprops if grading == "per_prop" else 0}
    tin = sum(calls[k] * ASSUME[k][0] for k in calls)
    tout = sum(calls[k] * ASSUME[k][1] for k in calls)
    usd = (tin * PRICE_IN + tout * PRICE_OUT) / 1e6
    return sum(calls.values()), tin + tout, usd


EXP9 = {("subset 5 pages", "off"): [5, 13250, 0.003, 0.07, 2], ("subset 5 pages", "batched"): [10, 30250, 0.006, 0.15, 4],
        ("subset 5 pages", "per_prop"): [217, 261290, 0.036, 1.31, 33], ("Corpus D 33 pages", "off"): [33, 87450, 0.018, 0.44, 11],
        ("Corpus D 33 pages", "batched"): [66, 199650, 0.039, 1.00, 25], ("Corpus D 33 pages", "per_prop"): [1433, 1725450, 0.236, 8.63, 216]}
PLAN = {}
for nm, npg, npr in (("subset 5 pages", 5, round(P_EST * 5 / 33)), ("Corpus D 33 pages", 33, P_EST)):
    for gr in ("off", "batched", "per_prop"):
        c, t, u = plan(npg, npr, gr)
        PLAN[(nm, gr)] = (c, t, u)
        print(f"   {nm} (about {npr:,} propositions), grading {gr}: {c:,} calls, {t:,} tokens, ${u:.3f}, "
              f"{t / TPD:.2f} days of 200K TPD, at least {t / TPM:.0f} min at 8K TPM")
        check(f"§11 {nm}, grading {gr}: calls, tokens, $, days of 200K TPD, min at 8K TPM (K9; ASSUMED sizes)",
              [c, t, round(u, 3), round(t / TPD, 2), int(f"{t / TPM:.0f}")], EXP9[(nm, gr)], T3)
check("§11 subset: about propositions on 5 pages (K9)", round(P_EST * 5 / 33), 212)

SIZE = {nm: [int(f"{97 * d * 4 / 1024:.0f}"), int(f"{P_EST * d * 4 / 1024:.0f}")] for d, nm in ((384, "MiniLM 384-d"), (1536, "Cohere 1,536-d"))}
check("§11 index size float32, KiB: 97 chunks vs about 1,400 propositions (K9)", SIZE, {"MiniLM 384-d": [146, 2100], "Cohere 1,536-d": [582, 8400]})
check("§11 vectors multiplier (K9)", round(P_EST / 97, 1), 14.4, T3)
PER1K = {}
for gr in ("off", "batched", "per_prop"):
    c, t, u = plan(33, P_EST, gr)
    PER1K[gr] = [int(f"{c * 1000 / 97:.0f}"), int(f"{t * 1000 / 97:.0f}"), round(u * 1000 / 97, 2)]
check("§11 cost per 1k chunks (DERIVED): calls, tokens, $ (K9)", PER1K,
      {"off": [340, 901546, 0.19], "batched": [680, 2058247, 0.40], "per_prop": [14773, 17788144, 2.43]}, T2)

fig = go.Figure()
for gr, colour, label in (("off", AQUA, "generation only"), ("batched", BLUE, "+ batched grade (1 per page)"),
                          ("per_prop", ORANGE, "+ per-proposition grade")):
    fig.add_bar(x=["5-page subset", "Corpus D (33 pages)"], y=[PLAN[("subset 5 pages", gr)][1], PLAN[("Corpus D 33 pages", gr)][1]],
                name=label, marker=bar_style(colour),
                customdata=[PLAN[("subset 5 pages", gr)][0], PLAN[("Corpus D 33 pages", gr)][0]],
                hovertemplate="%{x}: %{y:,} tokens in %{customdata:,} calls<extra>" + label + "</extra>")
fig.add_hline(y=TPD, line=dict(color=RED, dash="dash"), annotation_text="200K tokens = one day of the free tier (plan UNVERIFIED)",
              annotation_position="top left")
fig.update_layout(title="§11 · Index-time tokens (ASSUMED sizes per call): the per-proposition grader dominates", barmode="group",
                  height=400, yaxis=dict(title="tokens (in + out, reasoning included)", type="log"))
fig.show()

fig = go.Figure()
for i, (label, colour) in enumerate((("97 chunks", BLUE), ("about 1,400 propositions", ORANGE))):
    fig.add_bar(x=list(SIZE), y=[SIZE[k][i] for k in SIZE], name=label, marker=bar_style(colour),
                hovertemplate="%{x}: %{y:,} KiB<extra>" + label + "</extra>")
fig.update_layout(title="§11 · Index size (float32): ×14.4 vectors", barmode="group", height=360, yaxis=dict(title="KiB"))
fig.show()
''')

# =====================================================================================================================
md(r"""
## 12 · Proposition chunking in your project

**What this verifies** (lesson step 12, `#project`; facts K10, K12).
- **The 8-gram leakage test:** the prompt's template and few-shot example share **0** 8-grams with the eval texts (10 questions + 12 gold quotes, 172 distinct 8-grams). With the example sentence replaced by the D-002 quote, they share **10**, and the test fails, as it should.
- **The k = 4 ceiling:** upstream cell 22 embeds 3 chunks and retrieves k = 4, so every query returns the whole chunk index (K12). A 5-page proposition index would sit near the same ceiling, so v1.4 indexes the full corpus and restricts the eval items if needed, never the index.
- The v1.4 table is empty until the recorded run exists: fixed k **and** an equal token budget, with "inconclusive" pre-registered as a likely verdict.
""")
code(r'''
def toks(t):
    return re.findall(r"[a-z0-9]+", t.lower())


def ngrams(t, n=8):
    w = toks(t)
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


EVAL_TEXT = [s["question"] for s in SEEDS] + [alt["quote"] for s in SEEDS for g in s["evidence_groups"] for alt in g["alternatives"]]
EV = set().union(*(ngrams(t) for t in EVAL_TEXT))
EXAMPLE_PART = PROMPT.split("Page:\n")[0]
LEAKY = EXAMPLE_PART.replace("The town library opened in 1998.",
                             "The Paris Agreement, adopted in 2015, aims to limit global warming to well below 2 degrees Celsius.")
check("§12 eval texts (questions + gold quotes), distinct 8-grams (K10)", [len(EVAL_TEXT), len(EVAL_TEXT) - 10, len(EV)], [22, 12, 172])
check("§12 leakage test: clean prompt shares, injected leak shares (8-grams) (K10)",
      [len(ngrams(EXAMPLE_PART) & EV), len(ngrams(LEAKY) & EV)], [0, 10])
print("   the test, as an assert for your build:  assert not ngrams(EXAMPLE_PART) & EV, 'few-shot example leaks eval text'")

LG = re.search(r"(\d+)/(\d+) \[", outs(22))
check("§12 upstream cell 22: chunks embedded; k = 4 >= chunks (K12)", [int(LG.group(1)), 4 >= int(LG.group(1))], [3, True])

print("\n   the v1.4 table (empty until the recorded run exists; fill it from the run, never from this notebook):")
print("   | arm | k | context tokens (realised) | MRR@10 | CE@4 | discordant +/- |")
for arm in ("v0 chunks (control)", "v1.0 champion", "v1.4 arm (a): propositions -> parents, fixed k",
            "v1.4 arm (a): propositions -> parents, equal token budget"):
    print(f"   | {arm} |  |  |  |  |  |")
print("   pre-registered verdict options: adopt / reject / inconclusive (a likely verdict on a small set of factual items)")
''')

# =====================================================================================================================
md(r"""
## Result

The cell below counts the checks. Every `FAIL` names the value that disagreed; every `SKIPPED` says why it could not run. The MiniLM observation in step 9 is never counted as a check.
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
