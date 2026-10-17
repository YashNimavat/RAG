"""Build labs/R1_hybrid_fusion_lab.ipynb (blank-file first: tasks, empty learner cells, prediction cells, CHECK cells;
NO solution code). Every CHECK fingerprint is read from the "FP <name> <value>" lines of out_r1_measure.txt, so the
notebook and the measurement can never drift apart.

Run from rag_learning/:  uv run python sources/verification/R1/r1_build_lab.py
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]
OUT = WS / "labs" / "R1_hybrid_fusion_lab.ipynb"
FP = dict(re.findall(r"^FP (\S+) ([0-9a-f]{16})$", (HERE / "out_r1_measure.txt").read_text(encoding="utf-8"), re.M))


def fp(name):
    return FP[name]


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text, tag, task=None):
    meta = {"tags": [tag]}
    if task:
        meta["task"] = task
    return {"cell_type": "code", "execution_count": None, "metadata": meta, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


def learner(task, hint="Your code here"):
    return code(f"# {hint} ({task}). Blank-file first: write it yourself; no copying from r1_measure.py.", "learner", task)


cells = []
A = cells.append

A(md(r"""
# R1 lab: sparse, dense and hybrid retrieval, and how to fuse them

Lesson: [`concepts/R1_hybrid_fusion.md`](../concepts/R1_hybrid_fusion.md), Part H.1. Short reading: [`study/reading/R1_hybrid_fusion.md`](../study/reading/R1_hybrid_fusion.md). Concept card: [02 R1](../02_RAG_MASTER_LEARNING_PLAN.md#r1). Prerequisites: your P3 lab (BM25, `tok_norm`) and your C4 lab (`retrieve` with scores, ties by `chunk_id`).

**How this lab works (blank-file first).**
- Each task has a **task cell**, an **empty code cell** for you, and a **CHECK cell** (`# CHECK`, do not edit). Run the CHECK after your code. If it fails, read the message and fix your code.
- This notebook contains **no solution code**. The reference scripts in `sources/verification/R1/` are solutions: open them only after an honest attempt and a hint from the tutor (CR-04).
- **Predict first** where asked. The CHECK cells refuse to run without your prediction.
- CHECK cells compare **fingerprints** (`_fp`), so the expected answers stay hidden until you have predicted.
- **No API calls.** Dense retrieval uses the local MiniLM fallback; nothing calls Groq or Cohere. Never print a key.
- Everything here is **retrieval** quality. No answer is generated.
- The 10 seed items are **drafts** (06 §6.7, `llm-draft`): good for a lab, never a scored result.
- Kernel: the project uv environment (`rag-learning`). Run the cells top to bottom.
"""))

A(md(r"""
## Setup (given)

Imports, paths, the fingerprint helper `_fp`, and P3's tokenizer `tok_norm` (lower-case, runs of letters and digits, `1.5` kept whole).
"""))
A(code(r'''
import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")          # never download; the model is in the local HF cache
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
import hashlib, json, math, re, sys, types, random
from pathlib import Path
import numpy as np
import pymupdf
from rank_bm25 import BM25Okapi

WS = Path(r"C:\Yash\New-Work\Book RAG\rag_learning")
PDF = r"C:\Yash\New-Work\Book RAG\upstream\RAG_Techniques\data\Understanding_Climate_Change.pdf"
MINILM = "sentence-transformers/all-MiniLM-L6-v2"
K = 4            # v0 k (06 §3.1)
N_LIST = 50      # each retriever passes on its top-50 (06 v2.0 card)

def _fp(x):
    """Fingerprint of a value. The CHECK cells compare fingerprints, not visible answers."""
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:16]

_NORM_RE = re.compile(r"[a-z0-9]+(?:[.,][0-9]+)*")
def tok_norm(text):
    """P3's tokenizer (P3 Part K): the SAME function for chunks and queries."""
    return _NORM_RE.findall(text.lower())

print("numpy", np.__version__, "| pymupdf", pymupdf.VersionBind)
''', "given"))

A(md(r"""
## The v0 index (given, see C3 and C4)

The same index as the C4 lab: 97 chunks from the 07 recursive chunker (per page, 1000/200 characters), course chunk ids `climate:ea07572562ac:1ca9c5a3b548:00000` … `00096`, MiniLM vectors `V` (row i = `chunks[i]`), and `embedder.embed_query(text)`. If you built the C3 index files, set `INDEX_DIR` and the cell loads them instead.
"""))
A(code(r'''
INDEX_DIR = None        # e.g. Path(r"...\index\ea07572562ac\1ca9c5a3b548\c398eeba043f") once your C3 index exists

def _section(md, prefix):
    lines, fence, start, level = md.splitlines(), False, None, None
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("```"):
            fence = not fence; continue
        m = None if fence else re.match(r"^(#+)\s+(.*)$", ln)
        if m and start is None and m.group(2).startswith(prefix):
            start, level = i, len(m.group(1))
        elif m and start is not None and len(m.group(1)) <= level:
            return "\n".join(lines[start:i])
    return "\n".join(lines[start:])

def _blocks(md, lang):
    return re.findall(r"^```" + lang + r"[ \t]*\n(.*?)^```", md, flags=re.S | re.M)

pages = [p.get_text() for p in pymupdf.open(PDF)]
doc_text = "\n".join(pages)
starts = [sum(len(x) + 1 for x in pages[:i]) for i in range(len(pages))]
_sha = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
_parts = ["snapshot-v1", f"parser=pymupdf@{pymupdf.VersionBind}", "options=" + json.dumps({}, sort_keys=True),
          "cleaning=none", "page_join=\\n", f"climate:{_sha(doc_text)}"]          # 06 §5.3 recipe
SNAP = _sha("|".join(_parts))[:12]
assert SNAP == "ea07572562ac", f"snapshot {SNAP}: the extracted text differs from Corpus D (PyMuPDF must be 1.26.7)"

md07 = (WS / "07_SAMPLE_LESSON.md").read_text(encoding="utf-8")
for name in ("ragkit", "ragkit._core", "ragkit.chunking"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["ragkit"].__path__ = []
exec(_blocks(_section(md07, "H.1 Minimal implementation"), "python")[0], sys.modules["ragkit._core"].__dict__)
exec(_blocks(_section(md07, "H.3 Reusable design"), "python")[0], sys.modules["ragkit.chunking"].__dict__)
_ch = sys.modules["ragkit.chunking"]
CFG = _ch.ChunkerConfig(name="recursive", size=1000, overlap=200, scope="per_page")
CHUNKING = {"name": "recursive_char", "unit": "chars", "chunk_size": 1000, "chunk_overlap": 200,
            "separators": ["\n\n", "\n", " ", ""], "scope": "per_page"}
PARAMS_HASH = hashlib.sha256(json.dumps(CHUNKING, sort_keys=True).encode("utf-8")).hexdigest()[:12]
assert PARAMS_HASH == "1ca9c5a3b548", PARAMS_HASH

def _record(c):
    return {"doc_id": "climate", "snapshot_id": SNAP, "chunk_id": f"climate:{SNAP}:{PARAMS_HASH}:{c.seq:05d}",
            "seq": c.seq, "char_start": c.char_start, "char_end": c.char_end,
            "page_segments": [{"page": g.page, "char_start": g.char_start, "char_end": g.char_end} for g in c.page_segments],
            "text": c.text, "text_sha256": c.text_sha256, "chunker": CHUNKING["name"], "params_hash": PARAMS_HASH, "meta": {}}

from sentence_transformers import SentenceTransformer

class MiniLMEmbedder:
    """06 §2.3 Embedder for the local fallback model (symmetric: queries and documents use the same call)."""
    def __init__(self, name=MINILM):
        self.model_id, self._m = name, SentenceTransformer(name, device="cpu")
    def embed_documents(self, texts):
        return self._m.encode(list(texts), normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
    def embed_query(self, text):
        return self._m.encode([text], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)[0]

embedder = MiniLMEmbedder()
if INDEX_DIR is None:
    chunks = [_record(c) for c in _ch.chunk_document("climate", SNAP, pages, CFG)]
    V = embedder.embed_documents([c["text"] for c in chunks])
else:
    V = np.load(Path(INDEX_DIR) / "vectors.npy")
    chunks = [json.loads(l) for l in open(Path(INDEX_DIR) / "chunks.jsonl", encoding="utf-8")]
assert len(V) == len(chunks) and V.dtype == np.float32, "one float32 vector per chunk row"
assert len({c["chunk_id"] for c in chunks}) == len(chunks), "chunk_ids must be unique"
_jl = "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in chunks).encode("utf-8")
assert hashlib.sha256(_jl).hexdigest().startswith("d4108b89"), "chunks differ from the C2/C3/C4 chunks.jsonl (sha256 d4108b89...)"
IDS = [c["chunk_id"] for c in chunks]
ROW = {d: i for i, d in enumerate(IDS)}
print(f"index: {len(chunks)} chunks, V {V.shape} {V.dtype}, chunks.jsonl sha256 d4108b89... OK")
''', "given"))

A(md(r"""
## Seeds and judging helpers (given, see 06 §6.7, C4 and P6)

- `SEEDS`: the 10 **draft** seed items; `ANSWERABLE`: the 8 with an answer; `QUESTION[qid]`.
- `rel(chunk_id, item)`: 1 if that chunk overlaps a gold span (06 §7.2 `any_overlap`).
- `ce(chunk_ids, item)`: 1 if the chunks **together** cover every evidence group (Complete Evidence).
"""))
A(code(r'''
md06 = (WS / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
SEEDS = [json.loads(l) for l in _blocks(_section(md06, "6.7 Draft seed"), "jsonl")[0].splitlines() if l.strip()]
for s in SEEDS:
    s["G"] = [[[(starts[g["page"] - 1] + g["char_start"], starts[g["page"] - 1] + g["char_end"]) for g in alt["segments"]]
               for alt in grp["alternatives"]] for grp in s["evidence_groups"]]
ANSWERABLE = [s for s in SEEDS if s["answerable"]]
QUESTION = {s["qid"]: s["question"] for s in SEEDS}

def _covered(a, b, ranges):
    idx = [i for i in range(a, b) if not doc_text[i].isspace()]
    return sum(any(x <= i < y for x, y in ranges) for i in idx) / max(1, len(idx))

def rel(chunk_id, item):
    c = chunks[ROW[chunk_id]]
    x, y = c["char_start"], c["char_end"]
    return int(any(any(not doc_text[i].isspace() for i in range(max(a, x), min(b, y)))
                   for grp in item["G"] for alt in grp for a, b in alt))

def ce(chunk_ids, item):
    ranges = [(chunks[ROW[d]]["char_start"], chunks[ROW[d]]["char_end"]) for d in chunk_ids]
    return int(all(any(all(_covered(a, b, ranges) == 1.0 for a, b in alt) for alt in grp) for grp in item["G"]))

print(len(SEEDS), "seeds,", len(ANSWERABLE), "answerable:", [(s["qid"], s["category"]) for s in SEEDS])
''', "given"))

# ---------------------------------------------------------------- Task 1
A(md(r"""
## Task 1: Reciprocal Rank Fusion by hand

Two retrievers ranked four documents (the O1-Q09 lists):

```
dense: [A, B, C]        BM25: [C, A, D]
```

RRF gives each document `1 / (k + rank)` from every list it appears in (ranks start at **1**), and adds them up. A document missing from a list gets nothing from that list. Use **k = 60**.

**Predict first.** Without computing: which document comes first, and which comes last?
"""))
A(code(r'''
my_prediction_first = None   # e.g. "B"
my_prediction_last = None    # e.g. "C"
''', "prediction", "t1_pred"))
A(md(r"""
Now compute by hand, with plain arithmetic (no loops, no functions):
- `toy_fused`: a dict `{doc: RRF score}` for A, B, C and D;
- `toy_order`: the four documents, best first.
"""))
A(learner("t1"))
A(code(f'''
# CHECK Task 1 (do not edit)
assert my_prediction_first is not None and my_prediction_last is not None, "write both predictions first"
assert set(toy_fused) == {{"A", "B", "C", "D"}}, "one score for each of A, B, C, D"
assert _fp({{d: round(float(v), 5) for d, v in toy_fused.items()}}) == "{fp('toy_rrf_scores_k60_r5')}", \\
    "a score is not right yet: ranks start at 1, and k = 60"
assert _fp(list(toy_order)) == "{fp('toy_rrf_order_k60')}", "toy_order is not right yet"
print("Task 1 OK.", {{d: round(v, 5) for d, v in toy_fused.items()}}, "order", toy_order,
      "| you predicted first", my_prediction_first, "and last", my_prediction_last)
''', "check"))

# ---------------------------------------------------------------- Task 2
A(md(r"""
## Task 2: `rrf` and `fused_order`

Write two functions:
- `rrf(ranked_lists, k=60) -> dict`: `ranked_lists` is a list of lists of ids, each best first. Returns `{id: fused score}`.
- `fused_order(scores) -> list`: the ids of a `{id: score}` dict, **highest score first, ties broken by the smaller id** (06 §3.1, as in C4). This one function is reused by every fusion method below.
"""))
A(learner("t2"))
A(code(f'''
# CHECK Task 2 (do not edit)
_t = rrf([["A", "B", "C"], ["C", "A", "D"]])
assert _fp(fused_order(_t)) == "{fp('toy_rrf_order_k60')}", "your rrf/fused_order disagree with your Task 1 hand result"
assert abs(rrf([["x"], []])["x"] - 1 / 61) < 1e-12, "a list where a document is missing adds nothing; rank 1 gives 1/61"
assert fused_order({{"b": 0.5, "a": 0.5, "c": 0.9}}) == ["c", "a", "b"], "ties must go to the smaller id"
assert fused_order(rrf([["b", "a"], ["a", "b"]])) == ["a", "b"], "exact RRF ties (1/61 + 1/62 both ways) go to the smaller id"
_L1, _L2 = [0, 1, 2, 3, 4], [4, 1, 3, 2, 0]
assert _fp(fused_order(rrf([_L1, _L2]))) == "{fp('aiq_order_k60')}", "AIQ lists at k=60: not right yet"
assert _fp(fused_order(rrf([_L1, _L2], k=0))) == "{fp('aiq_order_k0')}", "AIQ lists at k=0: not right yet (is k a parameter?)"
assert rrf([]) == {{}}, "no lists, no scores"
print("Task 2 OK. AIQ lists: k=60 ->", fused_order(rrf([_L1, _L2])), "| k=0 ->", fused_order(rrf([_L1, _L2], k=0)))
''', "check"))
A(md(r"""
**In one sentence:** why does document 1 win at k = 60 but not at k = 0? *(Your answer, in this cell.)*
"""))

# ---------------------------------------------------------------- Task 3
A(md(r"""
## Task 3: score normalisation and weighted fusion over **aligned** ids

Now give the Task 1 lists made-up scores (a **toy**):

```
dense (cosine): A 0.62, B 0.58, C 0.41        BM25: C 7.9, A 2.1, D 1.8
```

Write three functions. Every list is a **dict keyed by document id**, never a positional array:
- `minmax(scores) -> dict`: `(s - min) / (max - min)` over that one list. If every score is equal, return **1.0** for each (they are all the list's best; course rule).
- `zscore3(scores) -> dict`: the book's distribution-based form (Ch12 p.8/14): `(s - (mean - 3*sd)) / (6*sd)`, with the **population** sd (`np.std` default). If sd is 0, return **0.5** for each. Do not clip.
- `weighted_fusion(lists, weights, norm) -> dict`: `lists` is `{"dense": {...}, "bm25": {...}}`, `weights` is `{"dense": w, "bm25": 1 - w}`, `norm` is `minmax` or `zscore3`. Normalise **each list on its own**, then sum `weight * normalised score` per id over the **union** of ids. An id missing from a list gets **0** from it (book Ch12 p.9/14).
"""))
A(learner("t3"))
A(code(f'''
# CHECK Task 3 (do not edit)
_D = {{"A": 0.62, "B": 0.58, "C": 0.41}}
_B = {{"C": 7.9, "A": 2.1, "D": 1.8}}
_w = lambda a: {{"dense": a, "bm25": round(1 - a, 10)}}
_m246 = minmax({{"a": 2, "b": 4, "c": 6}}); _z246 = zscore3({{"a": 2, "b": 4, "c": 6}})
assert _fp([round(float(_m246[k]), 3) for k in "abc"]) == "{fp('toy_246_mm')}", "minmax([2, 4, 6]) is not right yet"
assert _fp([round(float(_z246[k]), 3) for k in "abc"]) == "{fp('toy_246_z3')}", "zscore3([2, 4, 6]) is not right yet (population sd?)"
assert minmax({{"x": 3.0, "y": 3.0}}) == {{"x": 1.0, "y": 1.0}}, "a constant list: every member is the best, 1.0"
assert zscore3({{"x": 3.0, "y": 3.0}}) == {{"x": 0.5, "y": 0.5}}, "a constant list under zscore3: 0.5"
_f55 = weighted_fusion({{"dense": _D, "bm25": _B}}, _w(0.5), minmax)
_f64 = weighted_fusion({{"dense": _D, "bm25": _B}}, _w(0.6), minmax)
assert set(_f64) == {{"A", "B", "C", "D"}}, "fuse over the UNION of the two lists"
assert abs(_f64["B"] - 0.6 * (0.58 - 0.41) / (0.62 - 0.41)) < 1e-9, "B is missing from BM25: it gets only its dense part"
assert _fp(fused_order(_f55)) == "{fp('toy_mm55_order')}", "min-max 0.5/0.5 order is not right yet"
assert _fp(fused_order(_f64)) == "{fp('toy_mm64_order')}", "min-max 0.6/0.4 order is not right yet"
assert _fp({{d: round(float(v), 4) for d, v in _f64.items()}}) == "{fp('toy_mm64_scores_r4')}", "min-max 0.6/0.4 scores are not right yet"
assert _fp(fused_order(weighted_fusion({{"dense": _D, "bm25": _B}}, _w(0.6), zscore3))) == "{fp('toy_z64_order')}", \\
    "zscore3 0.6/0.4 order is not right yet"
# identity: all the weight on dense must give back the dense order (the test the repo never had)
assert fused_order(weighted_fusion({{"dense": _D, "bm25": _B}}, _w(1.0), minmax))[:3] == ["A", "B", "C"], \\
    "weight 1.0 on dense must reproduce the dense order"
# alignment: the order in which the dicts were built must not matter
_Dr, _Br = dict(reversed(list(_D.items()))), dict(reversed(list(_B.items())))
assert weighted_fusion({{"dense": _Dr, "bm25": _Br}}, _w(0.6), minmax) == _f64, "fusion must depend on ids, not on positions"
print("Task 3 OK. min-max 0.5/0.5:", fused_order(_f55), "| 0.6/0.4:", fused_order(_f64),
      "| zscore3 0.6/0.4:", fused_order(weighted_fusion({{"dense": _D, "bm25": _B}}, _w(0.6), zscore3)))
''', "check"))
A(md(r"""
**Look at C under min-max.** C is BM25's **best** document but dense's **worst** of three. What does min-max give C on the dense side, and how is that different from C being absent from the dense list? *(Your answer, in this cell.)*
"""))

# ---------------------------------------------------------------- Task 4
A(md(r"""
## Task 4: the repo's misalignment bug, in three documents

Read `fusion_retrieval.ipynb` cell 17 (or `all_rag_techniques_runnable_scripts/fusion_retrieval.py` L75–L86) first. Three objects come back from three calls, and **each is in a different order**:

| Repo line | What it returns | Toy value below |
|---|---|---|
| L75 `similarity_search("", k=ntotal)` | every document, nearest to the **empty string** first | `toy_all_docs` |
| L76 `bm25.get_scores(query.split())` | one BM25 score per document, in **corpus (index) order** | `toy_bm25_scores` (corpus order d0, d1, d2) |
| L77 `similarity_search_with_score(query, k=n)` | (document, L2 distance) pairs, nearest to the **query** first | `toy_vector_results` |

**4a.** Write `repo_style(all_docs, vector_results, bm25_scores, alpha=0.5, k=3)` that does **exactly** what L79–L86 do with these arrays (keep cell 17's `+ 1e-8`), and returns the list of document names. Then write `aligned_style(...)` with the same inputs that builds **dicts keyed by document** and uses your `weighted_fusion` and `fused_order` (turn each distance into a similarity first: a smaller distance must give a larger score).
"""))
A(code(r'''
toy_all_docs = ["d2", "d0", "d1"]                          # L75: nearest to the empty string first
toy_vector_results = [("d1", 0.20), ("d2", 0.50), ("d0", 0.90)]   # L77: (doc, L2 distance), nearest to the query first
toy_bm25_scores = np.array([3.0, 0.0, 1.0])                # L76: corpus order d0, d1, d2
''', "given"))
A(learner("t4a"))
A(code(f'''
# CHECK Task 4a (do not edit)
_bug = repo_style(toy_all_docs, toy_vector_results, toy_bm25_scores, alpha=0.5, k=3)
_ok = aligned_style(toy_all_docs, toy_vector_results, toy_bm25_scores, alpha=0.5, k=3)
assert _fp(list(_bug)) == "{fp('toy_bug_order')}", "repo_style must reproduce L79-L86 exactly (positions, not documents)"
assert _fp(list(_ok)) == "{fp('toy_aligned_order')}", "aligned_style is not right yet (dicts keyed by document; ties by smaller id)"
print("Task 4a OK. Repo-style order:", _bug, "| aligned order:", _ok)
''', "check"))
A(md(r"""
**4b. The unit test that would have caught it.** Write `test_fusion_preserves_identity(fuse)`. `fuse(dense, bm25, alpha)` takes two dicts `{doc id: score}` (dense: higher is better) and returns doc ids best first. Your test builds its own small data (at least 4 documents, with a dense order that differs from the id order) and uses `assert` to check properties that **any** correct fusion must have. Ideas: with `alpha = 1.0` the output must equal the dense order; renaming or reordering the input rows must not change which ids come out; every returned id must exist in the inputs.

The CHECK runs your test on **your** fusion (it must pass) and on a transcription of the repo's logic (it must fail with an `AssertionError`).
"""))
A(learner("t4b"))
A(code(r'''
# CHECK Task 4b (do not edit)
def _repo_fuse(dense, bm25, alpha):
    """The repo's L75-L86 logic, adapted to dict inputs. Contains the bug on purpose."""
    corpus = sorted(set(dense) | set(bm25))                          # index order
    all_docs = corpus[1:] + corpus[:1]                                # L75: some other order (nearest to "")
    vector_results = sorted(((d, -dense.get(d, 0.0)) for d in corpus), key=lambda t: t[1])   # L77: nearest first
    vs = np.array([s for _, s in vector_results])
    vs = 1 - (vs - vs.min()) / (vs.max() - vs.min() + 1e-8)          # L80
    b = np.array([bm25.get(d, 0.0) for d in corpus])                 # L76: corpus order
    b = (b - b.min()) / (b.max() - b.min() + 1e-8)                    # L81
    comb = alpha * vs + (1 - alpha) * b                               # L83: three orders mixed
    return [all_docs[i] for i in np.argsort(comb)[::-1]]             # L84-L86

def my_fuse(dense, bm25, alpha):
    return fused_order(weighted_fusion({"dense": dense, "bm25": bm25}, {"dense": alpha, "bm25": 1 - alpha}, minmax))

test_fusion_preserves_identity(my_fuse)                               # must pass
try:
    test_fusion_preserves_identity(_repo_fuse)
    raise RuntimeError("your test did NOT catch the repo bug: use 4+ docs and a dense order that differs from the id order")
except AssertionError:
    pass
print("Task 4b OK: your test passes on aligned fusion and fails on the repo's logic.")
''', "check"))

# ---------------------------------------------------------------- Task 5
A(md(r"""
## Task 5: BM25, dense and fused retrieval on Corpus D

**Predict first.** For how many of the **8 answerable** seeds will BM25 rank the first relevant chunk **higher** (a smaller rank number) than dense retrieval? And for how many **lower**?
"""))
A(code(r'''
my_prediction_bm25_better = None   # an integer 0..8
my_prediction_bm25_worse = None    # an integer 0..8
''', "prediction", "t5_pred"))
A(md(r"""
Build, with the **same chunks** and `tok_norm` on both sides:
1. `bm25 = BM25Okapi([tok_norm(c["text"]) for c in chunks])` (defaults k1 = 1.5, b = 0.75).
2. `dense_list(question, n)`: `{chunk_id: cosine}` for the top-n chunks (the C4 scores: `V @ embedder.embed_query(question)`).
3. `bm25_list(question, n)`: `{chunk_id: BM25 score}` for the top-n chunks **with score > 0** (P3: 0 means no term matched).
4. `rankings[qid]` for every seed: a dict of four rankings, each a list of chunk_ids best first (use `fused_order` everywhere):
   - `"dense"`: all 97 chunks by cosine;
   - `"bm25"`: every chunk with BM25 score > 0;
   - `"rrf60"`: `rrf` over the two **top-50** lists, k = 60;
   - `"mm_0.5"`: `weighted_fusion` of the two **top-50** lists, min-max, weights 0.5 / 0.5.
5. `first_rel[arm]`: `{qid: rank of the first relevant chunk}` for the 8 answerable seeds (`None` if no relevant chunk is in that ranking).
6. `hit_ce[arm]`: `[Hit@4, CE@4]` over the 8 answerable seeds (`rel` and `ce` from the given cell).
"""))
A(learner("t5"))
A(code(f'''
# CHECK Task 5 (do not edit)
assert my_prediction_bm25_better is not None and my_prediction_bm25_worse is not None, "write both predictions first"
_A = ("dense", "bm25", "rrf60", "mm_0.5")
assert set(rankings) == {{s["qid"] for s in SEEDS}} and all(set(rankings[q]) >= set(_A) for q in rankings), "rankings[qid][arm] for every seed"
assert len(rankings["D-002"]["dense"]) == len(chunks), "the dense ranking covers all chunks"
assert _fp(rankings["D-002"]["dense"][:4]) == "{fp('lab_d002_dense_top4')}", "D-002 dense top-4 differs from C4 (query side? ties?)"
assert _fp({{s["qid"]: len(bm25_list(s["question"], N_LIST)) for s in SEEDS}}) == "{fp('lab_bm25_len')}", \\
    "bm25_list: top-50 with score > 0, tok_norm on the query too"
assert _fp(rankings["D-002"]["bm25"][:4]) == "{fp('lab_d002_bm25_top4')}", "D-002 BM25 top-4 is not right yet"
assert _fp(rankings["D-002"]["rrf60"][:4]) == "{fp('lab_d002_rrf_top4')}", "D-002 RRF top-4 is not right yet (top-50 lists, k=60)"
assert _fp(rankings["D-002"]["mm_0.5"][:4]) == "{fp('lab_d002_mm05_top4')}", "D-002 min-max top-4 is not right yet"
assert _fp(rankings["D-008"]["rrf60"][:4]) == "{fp('lab_d008_rrf_top4')}", "D-008 RRF top-4 is not right yet"
assert _fp(rankings["D-008"]["mm_0.5"][:4]) == "{fp('lab_d008_mm05_top4')}", "D-008 min-max top-4 is not right yet"
for _a, _h in (("dense", "{fp('seeds_first_rel_dense')}"), ("bm25", "{fp('seeds_first_rel_bm25')}"),
               ("rrf60", "{fp('seeds_first_rel_rrf60')}"), ("mm_0.5", "{fp('seeds_first_rel_mm05')}")):
    assert _fp(first_rel[_a]) == _h, f"first_rel[{{_a!r}}] is not right yet"
assert _fp({{a: [int(x) for x in hit_ce[a]] for a in _A}}) == "{fp('lab_hit_ce4')}", "hit_ce is not right yet"
for _a in _A:
    print(f"{{_a:7s}} Hit@4 {{hit_ce[_a][0]}}/8  CE@4 {{hit_ce[_a][1]}}/8  first_rel {{first_rel[_a]}}")
print("Task 5 OK. You predicted BM25 better on", my_prediction_bm25_better, "and worse on", my_prediction_bm25_worse)
''', "check"))

# ---------------------------------------------------------------- Task 6
A(md(r"""
## Task 6: diagnose one seed where fusion helps and one where it hurts

Print the top-6 of each arm for **D-008** ("What does the Kigali Amendment target?") and **D-006** ("What are the advantages of putting solar panels on lakes or reservoirs?"), with each chunk's page, its dense rank, its BM25 rank and its fused score. Open the texts of the top chunks.

1. `d006_top2`: the RRF scores of D-006's fused rank 1 and rank 2, as a list of two floats.
2. `diagnosis`: a dict with keys `"D-008"` and `"D-006"`, 2–4 sentences each: which chunk each retriever put first and **why** (which query tokens matched, how rare they are), what each fusion did, and whether this is a **retrieval** or a **generation** question (CR-11).

The tutor grades the diagnoses (Application rubric).
"""))
A(learner("t6"))
A(code(f'''
# CHECK Task 6 (do not edit)
assert _fp([round(float(x), 6) for x in d006_top2]) == "{fp('lab_d006_rrf_top2_r6')}", "d006_top2: the RRF scores of fused ranks 1 and 2"
assert set(diagnosis) == {{"D-008", "D-006"}}, "one diagnosis for D-008 and one for D-006"
for _q, _t in diagnosis.items():
    assert len(_t.split()) >= 25, f"{{_q}}: write at least 2 sentences (25+ words)"
    assert re.search(r"retriev|generat", _t, re.I), f"{{_q}}: say whether it is a retrieval or a generation question (CR-11)"
print(f"Task 6 OK (format). D-006 RRF ranks 1 and 2: {{d006_top2[0]!r}} vs {{d006_top2[1]!r}}; equal: {{d006_top2[0] == d006_top2[1]}}.")
print("If they are equal, what decided the order? Add one sentence about it to your D-006 diagnosis.")
''', "check"))

# ---------------------------------------------------------------- Task 7
A(md(r"""
## Task 7: what if a setting changes? (CR-08)

**Predict first**, with the direction and a reason:
- (a) k_rrf drops from 60 to **0**. How many of the 10 seeds change their **ordered** top-4 under `"rrf60"`?
- (b) the dense weight in `"mm_0.5"` rises from 0.5 to **0.7** (BM25 0.3). How many of the 10 seeds change their ordered top-4?
"""))
A(code(r'''
my_prediction_k0 = None     # an integer 0..10, and a reason in a comment
my_prediction_w07 = None    # an integer 0..10, and a reason in a comment
''', "prediction", "t7_pred"))
A(md(r"""
Compute `n_changed_k0` and `n_changed_w07` (same top-50 lists as Task 5; compare each seed's new top-4 list with its Task 5 top-4 list). Then check whether CE@4 changed at all.
"""))
A(learner("t7"))
A(code(f'''
# CHECK Task 7 (do not edit)
assert my_prediction_k0 is not None and my_prediction_w07 is not None, "write both predictions first"
assert _fp({{"k0": int(n_changed_k0), "w07": int(n_changed_w07)}}) == "{fp('lab_cr08')}", "the change counts are not right yet"
print(f"Task 7 OK. k_rrf 60 -> 0 changed {{n_changed_k0}}/10 top-4 lists (you predicted {{my_prediction_k0}}); "
      f"dense weight 0.5 -> 0.7 changed {{n_changed_w07}}/10 (you predicted {{my_prediction_w07}}).")
''', "check"))

# ---------------------------------------------------------------- Task 8
A(md(r"""
## Task 8: rescale one scorer. Which fusion notices?

A new embedding model, or a new BM25 library, can put the same ranking on a different scale. Simulate that on the **dense top-50 list** of each seed, before fusing, with two changes that keep the dense order the same:
- `x100`: every dense score times 100;
- `exp`: every dense score `s` becomes `math.exp(10 * s)`.

**Predict first:** for each method, will any seed's ordered top-4 change?
"""))
A(code(r'''
my_prediction_rescale = None   # e.g. {"raw_sum": "changes", "mm": "...", "rrf": "..."}
''', "prediction", "t8_pred"))
A(md(r"""
For each of three methods, count over the 10 seeds how many **ordered** top-4 lists differ from the same method without the change:
- `raw_sum`: dense score + BM25 score, no normalisation (an id missing from a list adds 0);
- `mm`: `weighted_fusion` with `minmax`, 0.5 / 0.5;
- `rrf`: `rrf` with k = 60.

Store `rescale_changes = {"raw_sum|x100": n, "raw_sum|exp": n, "mm|x100": n, "mm|exp": n, "rrf|x100": n, "rrf|exp": n}`.
"""))
A(learner("t8"))
A(code(f'''
# CHECK Task 8 (do not edit)
assert my_prediction_rescale is not None, "write your prediction first"
assert set(rescale_changes) == {{"raw_sum|x100", "raw_sum|exp", "mm|x100", "mm|exp", "rrf|x100", "rrf|exp"}}, "six counts"
assert _fp({{k: int(v) for k, v in rescale_changes.items()}}) == "{fp('lab_rescale')}", "a count is not right yet"
print("Task 8 OK.", rescale_changes)
''', "check"))

# ---------------------------------------------------------------- Task 9
A(md(r"""
## Task 9: decide (Transfer)

In `my_fusion_decision`, write 3–5 sentences for the v2.0 experiment: which fusion method you would make the primary arm and why, **which per-category numbers** (06 §6.2 buckets) would change your mind, and one situation in which you would **not** add BM25 at all. The tutor grades it with the Transfer rubric.
"""))
A(code(r'''
my_fusion_decision = None   # your sentences
''', "prediction", "t9"))
A(code(r'''
# CHECK Task 9 (do not edit)
assert isinstance(my_fusion_decision, str) and len(my_fusion_decision.split()) >= 40, "write 3-5 sentences (40+ words)"
assert re.search(r"CE|bucket|categor", my_fusion_decision, re.I), "name the per-category metric that decides"
assert re.search(r"\bnot\b|n't", my_fusion_decision, re.I), "say when you would not use hybrid retrieval"
print("Task 9 OK (format). The tutor grades the content.")
''', "check"))

nb = {"cells": cells, "metadata": {
    "kernelspec": {"display_name": "rag-learning (3.12.8)", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.12.8", "file_extension": ".py", "mimetype": "text/x-python",
                      "codemirror_mode": {"name": "ipython", "version": 3}, "nbconvert_exporter": "python",
                      "pygments_lexer": "ipython3"}}, "nbformat": 4, "nbformat_minor": 5}
for i, c in enumerate(nb["cells"]):
    c["id"] = f"r1-{i:02d}"
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("wrote", OUT, "cells:", len(cells), "| CHECK cells:", sum("check" in c["metadata"].get("tags", []) for c in cells),
      "| fingerprints used:", len(FP))
