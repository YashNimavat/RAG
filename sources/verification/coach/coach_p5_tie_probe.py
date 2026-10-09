"""Coach re-check for the P5 seed in sources/coach/transfer_seed_bank.md (written 2026-10-09).

Question: on the P5 index duplicated 5 times (P5 D.3, lab Task 5b), which top-k variants return the
same ids as a reference that breaks ties by the smaller id (the course rule, 06 §3.1)?
  A  "AIQ pattern": argpartition picks k winners, then the k are sorted by score only
     (the two lines of AIQ 12-coding-challenges/08 VectorIndex.search, re-typed here, never imported).
  B  argpartition picks k winners, then the k are sorted by (-score, id).
  C  the course top_k, copied unchanged from sources/verification/P5/p5_measure.py (L44-L54).
The review's scratch probe reported that B "still differed on 26 of 30 queries"; that probe was not
logged. This script replaces it with a logged run on the course's own P5 data.

Data: built exactly as p5_measure.py S1-S2 (PyMuPDF page text joined with "\n", plain 1000/200
character windows, MiniLM-L6 unit vectors, float32), then tiled 5 times as in p5_measure.py S5.
Queries: the 33 page-head texts and the 2 demo questions from p5_measure.py, plus 200 random unit
vectors (numpy default_rng(0)).

Local only: no Groq or Cohere call, .env never read. MiniLM from the local HF cache (offline forced).
Run from rag_learning/ (Git Bash):
    B="C:/Yash/New-Work/Book RAG"
    PYTHONIOENCODING=utf-8 uv run python sources/verification/coach/coach_p5_tie_probe.py \
        "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
        > sources/verification/coach/out_coach_p5_tie_probe.txt \
        2> sources/verification/coach/out_coach_p5_tie_probe.stderr.txt

Variant A re-types two lines from AI-Engineer-Interview-Questions @ e080df2,
12-coding-challenges/08_semantic_search_rag.py (VectorIndex.search). Copyright (c) 2026 Om. MIT License.
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import hashlib
import importlib.metadata as md
import sys

import numpy as np
import pymupdf as fitz                                # pinned 1.26.7

PDF = sys.argv[1]
MINILM = "sentence-transformers/all-MiniLM-L6-v2"
REP = 5


# ---------------------------------------------------------------- copied from p5_measure.py (unchanged)
def top_k(scores, k):
    """Exact top-k of a 1-D score vector (higher = better). Ties broken by the smaller id."""
    n = scores.shape[0]
    k = min(k, n)
    cand = np.argpartition(-scores, k - 1)[:k]        # the k best, in no particular order
    # ties at the boundary: argpartition may pick any of the tied ids, so take every id whose score
    # equals the k-th best, then order by (-score, id) and cut to k.
    kth = scores[cand].min()
    cand = np.flatnonzero(scores >= kth)
    order = np.lexsort((cand, -scores[cand]))         # last key is primary: -score, then id
    return cand[order][:k]


def brute_force_top_k(scores, k):
    """Reference: pure Python, float64, full sort. Ties broken by the smaller id."""
    s = [float(x) for x in scores]
    return sorted(range(len(s)), key=lambda i: (-s[i], i))[:k]


# ---------------------------------------------------------------- the two variants under test
def variant_a(scores, k):
    """AIQ challenge 08 pattern: argpartition, then sort only the k winners by score."""
    k = min(k, len(scores))
    top = np.argpartition(-scores, k - 1)[:k]
    top = top[np.argsort(-scores[top])]
    return top


def variant_b(scores, k):
    """argpartition, then sort only the k winners by (-score, id)."""
    k = min(k, len(scores))
    cand = np.argpartition(-scores, k - 1)[:k]
    return cand[np.lexsort((cand, -scores[cand]))]


def head(title):
    print(f"\n=== {title}")


# ---------------------------------------------------------------- data (as p5_measure.py S1-S2)
head("E1 environment and data")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in ("pymupdf", "numpy", "sentence-transformers", "torch")})
print("pdf sha256", hashlib.sha256(open(PDF, "rb").read()).hexdigest())
pages = [p.get_text() for p in fitz.open(PDF)]
full = "\n".join(pages)
S, O = 1000, 200
wins = [(a, min(a + S, len(full))) for a in range(0, len(full), S - O)]
texts = [full[a:b] for a, b in wins]
print(f"pages={len(pages)} chars={len(full)} chunks={len(texts)} (size {S}, overlap {O}, plain slices)")

from sentence_transformers import SentenceTransformer  # noqa: E402

model = SentenceTransformer(MINILM, device="cpu")
V = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
Q_D002 = "In what year was the Paris Agreement adopted?"
Q_D008 = "What does the Kigali Amendment target?"
QD = model.encode([Q_D002, Q_D008], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
QP = model.encode([p.strip()[:200] for p in pages], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
rng = np.random.default_rng(0)
QR = rng.standard_normal((200, V.shape[1])).astype(np.float32)
QR /= np.linalg.norm(QR, axis=1, keepdims=True)
V5 = np.tile(V, (REP, 1))                              # row r is chunk r % 91, copy r // 91
print(f"index: {V.shape} float32; duplicated index: {V5.shape} ({REP} copies of each chunk)")
print(f"queries: {len(QP)} page-head texts, {len(QD)} demo questions (D-002, D-008), {len(QR)} random unit vectors (seed 0)")

# ---------------------------------------------------------------- same numbers as the logged P5 run?
head("E2 consistency with out_p5_measure.txt S5 (query D-002, k = 4)")
s5 = V5 @ QD[0]
print("argpartition(-s5, 3)[:4] rows ->", np.argpartition(-s5, 3)[:4].tolist(), " (P5 S5 logged [428, 337, 64, 246])")
print("top_k(s5, 4) rows ->", top_k(s5, 4).tolist(), " (P5 S5 logged [64, 155, 246, 337])")
print("variant A rows ->", variant_a(s5, 4).tolist())
print("variant B rows ->", variant_b(s5, 4).tolist())
print("reference rows ->", brute_force_top_k(s5, 4))

# ---------------------------------------------------------------- the probe
head("E3 duplicated index: queries where each variant's ordered ids differ from the reference")
sets = (("page-head", QP), ("demo", QD), ("random", QR))
for k in (3, 4, 10):
    for label, Qs in sets:
        n = len(Qs)
        cut = da = db = dc = sa = rep = 0
        for x in Qs:
            s = V5 @ x
            ref = brute_force_top_k(s, k)
            srt = np.sort(s)[::-1]
            cut += bool(srt[k - 1] == srt[k])          # the k-th and (k+1)-th scores are tied
            a = variant_a(s, k).tolist()
            da += a != ref
            sa += set(a) != set(ref)
            db += variant_b(s, k).tolist() != ref
            dc += top_k(s, k).tolist() != ref
            rep += variant_a(s, k).tolist() == variant_a(s.copy(), k).tolist()
        print(f"k={k:2d} {label:9s} n={n:3d}: tie across the cut {cut:3d}/{n} | differ: A {da:3d}/{n} (set {sa:3d}/{n}), "
              f"B {db:3d}/{n}, C top_k {dc:3d}/{n} | A same rows on a second call {rep:3d}/{n}")

head("E4 control: the same variants on the plain index (no duplicates)")
for k in (3, 4, 10):
    for label, Qs in sets:
        n = len(Qs)
        da = sum(variant_a(V @ x, k).tolist() != brute_force_top_k(V @ x, k) for x in Qs)
        db = sum(variant_b(V @ x, k).tolist() != brute_force_top_k(V @ x, k) for x in Qs)
        print(f"k={k:2d} {label:9s} n={n:3d}: differ A {da}/{n}, B {db}/{n}")
