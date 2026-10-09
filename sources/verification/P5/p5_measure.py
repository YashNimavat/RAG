"""P5 (vector search) measurements: every measured number in concepts/P5_vector_search.md comes from this run.

Local only: no Groq or Cohere calls, no .env read. No faiss, no LangChain (neither is in the project env).
The MiniLM model is loaded from the local Hugging Face cache (offline mode is forced below).

Run from rag_learning/ (Git Bash):
    B="C:/Yash/New-Work/Book RAG"
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P5/p5_measure.py \
        "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" "$B/RAG_Made_Simple_The_Complete_Visual_Guide"
Saved output: sources/verification/P5/out_p5_measure.txt (sections S1..S8 for P5_FACTS.md).
Sections S1-S7 are deterministic. S8 (timings) depends on the machine and its load; it is printed with the CPU name.
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import glob
import hashlib
import importlib.metadata as md
import json
import platform
import statistics as st
import sys
import time

import numpy as np
import pymupdf as fitz                                # pinned 1.26.7 (snapshot_id depends on it)

PDF, BOOK = sys.argv[1], sys.argv[2]
MINILM = "sentence-transformers/all-MiniLM-L6-v2"
K = 4                                                 # v0 k (06 §3.1)


def head(title):
    print(f"\n=== {title}")


def fp(x):                                            # same fingerprint as the lab's _fp
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:16]


# ---------------------------------------------------------------- the two functions the lesson teaches
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


# ---------------------------------------------------------------- S1
head("S1 environment, extraction and chunks with metadata")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in
      ("pymupdf", "numpy", "sentence-transformers", "torch", "transformers")})
print("platform", platform.platform(), "| cpu_count", os.cpu_count())
print("pdf sha256", hashlib.sha256(open(PDF, "rb").read()).hexdigest())
pages = [p.get_text() for p in fitz.open(PDF)]
full = "\n".join(pages)
starts = [sum(len(x) + 1 for x in pages[:i]) for i in range(len(pages))]


def page_of(off):                                     # 1-based page of a character offset
    return max(i + 1 for i, s0 in enumerate(starts) if s0 <= off)


S, O = 1000, 200                                      # plain fixed character windows (as in P1)
wins = [(a, min(a + S, len(full))) for a in range(0, len(full), S - O)]
meta = [{"chunk_id": i, "page": page_of(a), "page_end": page_of(b - 1), "char_start": a, "char_end": b}
        for i, (a, b) in enumerate(wins)]
texts = [full[a:b] for a, b in wins]
print(f"pages={len(pages)} chars={len(full)} chunks={len(meta)} (size {S}, overlap {O}, plain slices)")
print("chunk 0 metadata:", meta[0])
print("last chunk metadata:", meta[-1])
print(f"chunks that cross a page break: {sum(m['page'] != m['page_end'] for m in meta)}")
print("fingerprint of the page list [m['page'] for m in meta]:", fp([m["page"] for m in meta]))

# ---------------------------------------------------------------- S2
head("S2 embeddings (MiniLM, local, CPU)")
from sentence_transformers import SentenceTransformer  # noqa: E402
from huggingface_hub import snapshot_download  # noqa: E402

print("MiniLM cache snapshot:", os.path.basename(snapshot_download(MINILM, local_files_only=True)))
model = SentenceTransformer(MINILM, device="cpu")
print("modules:", [type(m).__name__ for m in model])
raw = model.encode(texts, normalize_embeddings=False, convert_to_numpy=True)
norms = np.linalg.norm(raw, axis=1)
print(f"normalize_embeddings=False: shape={raw.shape} dtype={raw.dtype} norm min/max = {norms.min():.6f}/{norms.max():.6f}")
V = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
print(f"normalize_embeddings=True:  shape={V.shape} dtype={V.dtype} max|norm-1| = {np.abs(np.linalg.norm(V, axis=1) - 1).max():.2e}")
print(f"index size: {V.shape[0]} x {V.shape[1]} x 4 bytes = {V.nbytes:,} bytes")

Q_D002 = "In what year was the Paris Agreement adopted?"       # 06 §6.7 seed D-002 (draft; demo only)
Q_D008 = "What does the Kigali Amendment target?"             # 06 §6.7 seed D-008 (draft; demo only)
qv = model.encode([Q_D002, Q_D008], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
# a verification query set of real text: the first 200 characters of every page
page_heads = [p.strip()[:200] for p in pages]
QP = model.encode(page_heads, normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
rng = np.random.default_rng(0)
QR = rng.standard_normal((200, V.shape[1])).astype(np.float32)
QR /= np.linalg.norm(QR, axis=1, keepdims=True)
print(f"queries: 2 demo questions (D-002, D-008), {len(QP)} page-head texts, {len(QR)} random unit vectors (seed 0)")

# ---------------------------------------------------------------- S3
head("S3 one query, exact search (D-002)")
q = qv[0]
scores = V @ q
print(f"q.shape={q.shape}  V.shape={V.shape}  scores = V @ q -> shape {scores.shape} (one score per chunk)")
print(f"an all-pairs chunk 'similarity matrix' V @ V.T would be {V.shape[0]}x{V.shape[0]} = {V.shape[0]**2:,} scores; "
      f"one query needs {V.shape[0]}")
ids = top_k(scores, K)
full_order = np.lexsort((np.arange(len(scores)), -scores))
for r, i in enumerate(full_order[:6], 1):
    m = meta[i]
    print(f"rank {r}: id={i:2d} score={scores[i]:.4f} page={m['page']}-{m['page_end']} "
          f"chars=[{m['char_start']},{m['char_end']}) text={texts[i][:60]!r}{'  <- top-4' if i in ids else ''}")
print(f"top-{K} ids = {ids.tolist()}  fingerprint {fp(ids.tolist())}")
print(f"score gap rank4 - rank5 = {scores[full_order[3]] - scores[full_order[4]]:.4f}; "
      f"score range over all chunks = {scores.min():.4f} .. {scores.max():.4f}")
gold = [m["chunk_id"] for m in meta if m["char_start"] <= starts[9] + 438 and m["char_end"] >= starts[9] + 537]
print(f"chunks that contain the whole D-002 evidence span (p.10 [438,537)): {gold}")
for name, qq in (("D-008", qv[1]),):
    s2 = V @ qq
    o2 = np.lexsort((np.arange(len(s2)), -s2))[:K]
    print(f"{name} top-{K}: " + ", ".join(f"id={i} p.{meta[i]['page']} {s2[i]:.4f}" for i in o2)
          + f"  fingerprint {fp(top_k(s2, K).tolist())}")
gold8 = [m["chunk_id"] for m in meta if m["char_start"] <= starts[23] + 468 and m["char_end"] >= starts[23] + 564]
print(f"chunks that contain the whole D-008 evidence span (p.24 [468,564)): {gold8}")
QB = qv
SB = QB @ V.T
print(f"batch of {len(QB)} queries: Q @ V.T -> shape {SB.shape} (queries x chunks), still not chunks x chunks")

# ---------------------------------------------------------------- S4
head("S4 verify top_k (argpartition) against brute force (pure Python, float64, full sort)")
for k in (1, 4, 10):
    for label, Qs in (("page-head", QP), ("random", QR)):
        same = sum(top_k(V @ x, k).tolist() == brute_force_top_k(V @ x, k) for x in Qs)
        same_sort = sum(np.lexsort((np.arange(len(V)), -(V @ x)))[:k].tolist() == brute_force_top_k(V @ x, k) for x in Qs)
        print(f"k={k:2d} {label:9s}: top_k == brute force for {same}/{len(Qs)} queries; full lexsort == brute force {same_sort}/{len(Qs)}")
gaps = []
for x in QP:
    s = np.sort(V @ x)[::-1]
    gaps.append(float(s[K - 1] - s[K]))
print(f"page-head queries: gap between rank {K} and rank {K+1} min/median/max = "
      f"{min(gaps):.5f}/{st.median(gaps):.5f}/{max(gaps):.5f}")
# float32 (numpy) vs float64 (brute force) disagreement in the scores themselves
d = max(float(np.abs((V @ x).astype(np.float64) - V.astype(np.float64) @ x.astype(np.float64)).max()) for x in QP)
print(f"max |score float32 - score float64| over page-head queries = {d:.2e}")
# a broken implementation, to show what the check catches
bad = sum(np.argpartition(-(V @ x), K - 1)[:K].tolist() == brute_force_top_k(V @ x, K) for x in QP)
print(f"BROKEN variant (argpartition only, no sort): equal to brute force (same order) for {bad}/{len(QP)} page-head queries")
bad2 = sum(np.argsort(V @ x)[:K].tolist() == brute_force_top_k(V @ x, K) for x in QP)
print(f"BROKEN variant (argsort ascending, forgot the minus): equal for {bad2}/{len(QP)}")
# argpartition does not promise any order inside the k it returns; test that on a bigger random index
r3 = np.random.default_rng(3)
Abig = r3.standard_normal((10_000, 384), dtype=np.float32)
Abig /= np.linalg.norm(Abig, axis=1, keepdims=True)
Qbig = r3.standard_normal((100, 384), dtype=np.float32)
Qbig /= np.linalg.norm(Qbig, axis=1, keepdims=True)
for k in (4, 10, 50):
    ok_order = sum(np.argpartition(-(Abig @ x), k - 1)[:k].tolist() == brute_force_top_k(Abig @ x, k) for x in Qbig)
    ok_set = sum(set(np.argpartition(-(Abig @ x), k - 1)[:k].tolist()) == set(brute_force_top_k(Abig @ x, k)) for x in Qbig)
    ok_topk = sum(top_k(Abig @ x, k).tolist() == brute_force_top_k(Abig @ x, k) for x in Qbig)
    print(f"synthetic N=10,000 (seed 3), 100 random queries, k={k}: argpartition-only same ORDER {ok_order}/100, "
          f"same SET {ok_set}/100; top_k same order {ok_topk}/100")
del Abig
print("np.argpartition docstring says 'The order of all elements in the partitions is undefined':",
      "The order of all elements in the partitions is undefined" in " ".join(np.argpartition.__doc__.split()))

# ---------------------------------------------------------------- S5
head("S5 ties")
toy = np.array([0.70, 0.90, 0.80, 0.80, 0.80, 0.10], dtype=np.float32)    # TOY scores, made up
print("toy scores:", toy.tolist(), " k=2")
print("  np.argpartition(-toy, 1)[:2] ->", np.argpartition(-toy, 1)[:2].tolist())
print("  np.argsort(-toy)[:2] (default quicksort) ->", np.argsort(-toy)[:2].tolist())
print("  np.argsort(-toy, kind='stable')[:2] ->", np.argsort(-toy, kind="stable")[:2].tolist())
print("  top_k (ties by smaller id) ->", top_k(toy, 2).tolist(), " fingerprint", fp(top_k(toy, 2).tolist()))
print("  top_k k=4 ->", top_k(toy, 4).tolist(), " fingerprint", fp(top_k(toy, 4).tolist()))
print("  tied ids at the boundary for k=2:", np.flatnonzero(toy == np.sort(toy)[::-1][1]).tolist())
# dartboard.ipynb cell 9 loads every document 5 times; replay that on our chunks
REP = 5
V5 = np.tile(V, (REP, 1))                              # row r is chunk r % 91, copy r // 91
s5 = V5 @ q
top10 = top_k(s5, 10)
print(f"duplicated index ({REP} copies of each of {len(V)} chunks = {len(V5)} rows), query D-002:")
print("  top-10 rows -> (chunk, copy):", [(int(r % len(V)), int(r // len(V))) for r in top10])
print(f"  distinct chunks in top-4: {len({int(r % len(V)) for r in top10[:4]})}; in top-10: {len({int(r % len(V)) for r in top10})}")
cp = s5[[ids[0] + c * len(V) for c in range(REP)]]
print(f"  scores of the 5 copies of chunk {ids[0]}: {cp.tolist()}  all bit-identical: {bool(np.all(cp == cp[0]))}")
print(f"  argpartition(-s5, 3)[:4] rows -> {np.argpartition(-s5, 3)[:4].tolist()} (which copies is not specified)")
print(f"  top_k(s5, 4) rows -> {top_k(s5, 4).tolist()}; brute force -> {brute_force_top_k(s5, 4)}")

# ---------------------------------------------------------------- S6
head("S6 metadata alongside the vectors: results, filters, misalignment")
res = [{"rank": r + 1, "score": round(float(scores[i]), 4), **meta[i]} for r, i in enumerate(ids)]
for x in res:
    print("  ", x)


def search_prefilter(V, meta, q, k, keep):
    s = V @ q
    mask = np.array([keep(m) for m in meta])
    s = np.where(mask, s, -np.inf)
    out = top_k(s, k)
    return [int(i) for i in out if np.isfinite(s[i])]


def search_postfilter(V, meta, q, k, keep, fetch_k=20):  # the LangChain FAISS pattern (source read, not run)
    cand = top_k(V @ q, fetch_k)
    return [int(i) for i in cand if keep(meta[i])][:k]


keep = lambda m: m["page"] >= 25                       # e.g. "only the later sections"
n_keep = sum(keep(m) for m in meta)
print(f"filter page >= 25 keeps {n_keep}/{len(meta)} chunks")
allq = list(qv) + list(QP)
pre_short = sum(len(search_prefilter(V, meta, x, K, keep)) < K for x in allq)
post_counts = [len(search_postfilter(V, meta, x, K, keep)) for x in allq]
print(f"{len(allq)} real queries (2 demo + {len(QP)} page heads): pre-filter returned < {K} results for {pre_short}; "
      f"post-filter (fetch_k=20) returned < {K} for {sum(c < K for c in post_counts)}, 0 results for {sum(c == 0 for c in post_counts)}")
print(f"post-filter result counts histogram: { {c: post_counts.count(c) for c in sorted(set(post_counts))} }")
print(f"D-002 pre-filter: {search_prefilter(V, meta, q, K, keep)}  post-filter: {search_postfilter(V, meta, q, K, keep)}")
# misalignment: delete one vector but keep the metadata list unchanged
Vbad = np.delete(V, 0, axis=0)
ids_bad = top_k(Vbad @ q, K)
print("misaligned index (row 0 deleted from vectors only), D-002:")
for i in ids_bad:
    print(f"   row {int(i)}: metadata says chunk {meta[i]['chunk_id']} p.{meta[i]['page']}, "
          f"vector really is chunk {int(i) + 1} p.{meta[int(i) + 1]['page']}")
print("guard: assert len(V) == len(meta) ->", len(Vbad) == len(meta))

# ---------------------------------------------------------------- S7
head("S7 hidden defaults: the distance")
X = np.concatenate([qv, QP])
s_dot = X @ V.T
s_cos = s_dot / (np.linalg.norm(X, axis=1, keepdims=True) * np.linalg.norm(V, axis=1)[None, :])
l2sq = ((X[:, None, :] - V[None, :, :]) ** 2).sum(-1)
print(f"unit vectors: max |L2^2 - (2 - 2 cos)| = {np.abs(l2sq - (2 - 2 * s_cos)).max():.2e}")
same = lambda A, B: sum(top_k(a, K).tolist() == top_k(b, K).tolist() for a, b in zip(A, B))
print(f"unit vectors, {len(X)} real queries: top-{K} by dot == by cosine: {same(s_dot, s_cos)}; by -L2 == by cosine: {same(-l2sq, s_cos)}")
# TOY: give each chunk vector a different length, as an embedder without normalisation could
r = np.random.default_rng(1).uniform(0.5, 1.5, size=len(V)).astype(np.float32)
U = V * r[:, None]
u_dot = X @ U.T
u_cos = u_dot / (np.linalg.norm(X, axis=1, keepdims=True) * np.linalg.norm(U, axis=1)[None, :])
u_l2 = ((X[:, None, :] - U[None, :, :]) ** 2).sum(-1)
print(f"TOY un-normalised chunk vectors (lengths x U(0.5,1.5), seed 1), {len(X)} queries: "
      f"top-{K} by dot == by cosine for {same(u_dot, u_cos)}; by -L2 == by cosine for {same(-u_l2, u_cos)}; "
      f"by dot == by -L2 for {same(u_dot, -u_l2)}")
print(f"  cosine ranking unchanged by the scaling: {same(u_cos, s_cos)}/{len(X)}")
print(f"  D-002: cosine top-{K} {top_k(u_cos[0], K).tolist()}  dot top-{K} {top_k(u_dot[0], K).tolist()}  "
      f"L2 top-{K} {top_k(-u_l2[0], K).tolist()}")
print("  fingerprint of the count (dot == cosine):", fp(int(same(u_dot, u_cos))))
# a distance turned into a 'relevance' score (LangChain _euclidean_relevance_score_fn: 1 - d / sqrt(2); source read, not run)
for c in (0.8, 0.5, 0.2):
    d1 = (2 - 2 * c) ** 0.5
    print(f"cos={c}: L2={d1:.4f}  L2^2={d1*d1:.4f}  1-L2/sqrt2={1 - d1 / 2**0.5:.4f}  1-L2^2/sqrt2={1 - d1*d1 / 2**0.5:.4f}")

# ---------------------------------------------------------------- S8
head("S8 timing exact search (machine-specific; median of repeats)")
try:
    import subprocess
    cpu = subprocess.run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"],
                         capture_output=True, text=True, timeout=30).stdout.strip()
except Exception as ex:                                # noqa: BLE001
    cpu = f"unknown ({ex})"
print("cpu:", cpu, "| logical cpus:", os.cpu_count(), "| numpy BLAS: OpenBLAS (multi-threaded by default)")


def search(Vm, qq, k):
    return top_k(Vm @ qq, k)


def timeit(fn, budget=1.0, min_reps=7, max_reps=5000):
    fn()                                              # warm-up
    ts = []
    t_end = time.perf_counter() + budget
    while (len(ts) < min_reps or time.perf_counter() < t_end) and len(ts) < max_reps:
        t0 = time.perf_counter(); fn(); ts.append(time.perf_counter() - t0)
    return st.median(ts), len(ts)


t, n = timeit(lambda: search(V, q, K))
print(f"real corpus N={len(V)} d={V.shape[1]}: median {t*1e6:.1f} us per query ({n} reps)")
t, n = timeit(lambda: brute_force_top_k(V @ q, K))
print(f"real corpus, brute_force_top_k (Python sort) on the same scores: median {t*1e6:.1f} us ({n} reps)")
# book scale: chunk every book PDF the same way (1000/200) and count
book_chars, book_chunks, nfiles = 0, 0, 0
for f in sorted(glob.glob(os.path.join(BOOK, "*.pdf"))):
    tx = "\n".join(p.get_text() for p in fitz.open(f))
    book_chars += len(tx); book_chunks += len(range(0, len(tx), S - O)); nfiles += 1
print(f"the whole book ({nfiles} PDFs): {book_chars:,} chars -> {book_chunks:,} chunks of 1000/200")
grng = np.random.default_rng(2)


def synth(N, d):
    A = grng.standard_normal((N, d), dtype=np.float32)
    A /= np.linalg.norm(A, axis=1, keepdims=True)
    return A


rows = []
for N, d in ((book_chunks, 384), (1_000, 384), (10_000, 384), (100_000, 384), (200_000, 384), (500_000, 384),
             (book_chunks, 1536), (100_000, 1536)):
    A = synth(N, d)
    qq = synth(1, d)[0]
    t, n = timeit(lambda: search(A, qq, K))
    rows.append((N, d, t))
    print(f"synthetic N={N:>7,} d={d:4d}: memory {A.nbytes/1e6:8.1f} MB  median {t*1e3:8.3f} ms per query ({n} reps)")
    if (N, d) == (100_000, 384):
        t8, n8 = timeit(lambda: search(A, qq, 2 * K))
        print(f"   same index, k={2*K}: median {t8*1e3:.3f} ms ({n8} reps)  ratio k8/k4 = {t8/t:.2f}")
        Qb = synth(100, d)
        tb, nb = timeit(lambda: [top_k(row, K) for row in Qb @ A.T], budget=2.0)
        print(f"   batch of 100 queries (Q @ A.T, then top_k per row): {tb*1e3:.1f} ms total = {tb*1e3/100:.3f} ms per query ({nb} reps)")
    if (N, d) == (500_000, 384):
        sc = A @ qq
        ta, na = timeit(lambda: np.argsort(-sc)[:K])
        tp, npp = timeit(lambda: top_k(sc, K))
        tm, nm = timeit(lambda: A @ qq)
        print(f"   on the 500k score vector: full argsort {ta*1e3:.2f} ms vs top_k (argpartition) {tp*1e3:.2f} ms; "
              f"the matrix-vector product alone {tm*1e3:.2f} ms")
    del A
r100 = [t for N, d, t in rows if (N, d) == (100_000, 384)][0]
r200 = [t for N, d, t in rows if (N, d) == (200_000, 384)][0]
print(f"doubling N 100k -> 200k (d=384): time ratio {r200/r100:.2f}")
print("DONE")
