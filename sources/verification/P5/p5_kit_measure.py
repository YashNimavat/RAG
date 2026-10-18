"""P5 study-kit measurements (K1-K14): the numbers the HTML lesson adds on top of p5_measure.py (S1-S8).

Why a second script: the study kit uses v0's **97 chunks** (the 07 recursive chunker, per page, 1000/200, as in
P3's verify notebook, P4's K facts and R1), while p5_measure.py measured the old 91 plain windows. It also adds
what the October run could not do: approximate search (IVF from scratch in NumPy, then real IVF and HNSW from
faiss-cpu 1.15.1, the optional `ann` group), filtered ANN, and the library tie orders.

Local only: no Groq, Cohere or Claude call, no .env read. MiniLM loads from the local Hugging Face cache (offline).
Labels: the draft seeds of 06 section 6.7 are LLM-drafted and not human-verified, so every rank on them is an
observation, never an evaluation result. Synthetic vectors are labelled SYNTHETIC wherever they are used.

Determinism: every line is identical on a rerun EXCEPT lines that start with "TIME" (machine- and load-dependent
timings). faiss runs with one thread so that index builds (and therefore recall numbers) are reproducible.

Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run --group ann python sources/verification/P5/p5_kit_measure.py \
        "<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"
Saved output: sources/verification/P5/out_p5_kit_measure.txt  (sections K1..K14 for P5_FACTS.md section 1b)
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

import hashlib
import importlib.metadata as md
import json
import logging
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pymupdf                                        # pinned 1.26.7

PDF = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]
L6 = "sentence-transformers/all-MiniLM-L6-v2"
K = 4                                                 # v0 k (06 section 3.1)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)


def head(t):
    print(f"\n=== {t}")


def f4(x):
    return f"{x:.4f}"


# ---------------------------------------------------------------- the 97 chunks and the draft seeds (as P4 K facts)
sys.path.insert(0, str(WS / "sources" / "verification" / "corrections"))
import contracts_check as cc                          # noqa: E402

pdf_bytes = PDF.read_bytes()
pages = [p.get_text() for p in pymupdf.open(PDF)]
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
TEXT = [c["text"] for c in chunks]
PAGE = [c["page_segments"][0]["page"] for c in chunks]
N = len(chunks)
TEXTS = {"climate": "\n".join(pages)}
SEEDS = [json.loads(line) for line in cc.code_blocks(cc.section(md06, "6.7 Draft seed"), "jsonl")[0].splitlines()
         if line.strip()]
for s in SEEDS:
    s["G"] = [[[("climate", starts[seg["page"] - 1] + seg["char_start"], starts[seg["page"] - 1] + seg["char_end"])
                for seg in alt["segments"]] for alt in g["alternatives"]] for g in s["evidence_groups"]]
ANS = [s for s in SEEDS if s["answerable"]]
BYQ = {s["qid"]: s for s in SEEDS}
REL = {s["qid"]: [i for i in range(N) if cc.rel(("climate", chunks[i]["char_start"], chunks[i]["char_end"]), s["G"], TEXTS)]
       for s in ANS}
HEADS = [p.strip()[:200] for p in pages]               # 33 page-head queries, as p5_measure.py S2


# ---------------------------------------------------------------- the functions the lesson teaches
def top_k(scores, k):
    """Exact top-k, higher = better. Tie-aware cut: every id scoring >= the k-th score, order (-score, id), cut to k."""
    scores = np.asarray(scores)
    k = min(k, scores.shape[0])
    cand = np.argpartition(-scores, k - 1)[:k]
    kth = scores[cand].min()
    cand = np.flatnonzero(scores >= kth)
    return cand[np.lexsort((cand, -scores[cand]))][:k]


def brute(scores, k):
    """Reference: pure Python, float64, full sort, ties by the smaller id."""
    s = [float(x) for x in scores]
    return sorted(range(len(s)), key=lambda i: (-s[i], i))[:k]


def v_argpart_only(s, k):                              # BROKEN: no order inside the k
    return np.argpartition(-s, k - 1)[:k].tolist()


def v_sort_picked(s, k):                               # INSUFFICIENT: sorts only the k that argpartition picked
    c = np.argpartition(-s, k - 1)[:k]
    return c[np.lexsort((c, -s[c]))].tolist()


def v_inmemory(s, k):                                  # langchain-core InMemoryVectorStore L317 (source read)
    return np.asarray(s).argsort()[::-1][:k].tolist()


def v_stable(s, k):                                    # correct too: a stable sort keeps the smaller id first
    return np.argsort(-np.asarray(s), kind="stable")[:k].tolist()


def first_rel(ranking, qid):
    return next((r for r, i in enumerate(ranking, 1) if i in REL[qid]), None)


def summary(ranks, k=4):
    hit1 = sum(r is not None and r <= 1 for r in ranks)
    hitk = sum(r is not None and r <= k for r in ranks)
    mrr = sum(1 / r for r in ranks if r is not None and r <= 10) / len(ranks)
    return hit1, hitk, round(mrr, 3)


def nearest_rank(xs, p):
    """Nearest-rank percentile (no interpolation): the ceil(p/100 * n)-th smallest value."""
    ys = sorted(xs)
    return ys[max(0, math.ceil(p / 100 * len(ys)) - 1)]


def lat(fn, queries, warm=5):
    """Per-query latency in ms over the given queries, warm-up excluded; returns (p50, p95, n)."""
    for x in queries[:warm]:
        fn(x)
    ts = []
    for x in queries:
        t0 = time.perf_counter()
        fn(x)
        ts.append((time.perf_counter() - t0) * 1e3)
    return nearest_rank(ts, 50), nearest_rank(ts, 95), len(ts)


def unit(M):
    M = np.asarray(M, np.float32)
    return M / np.linalg.norm(M, axis=-1, keepdims=True)


def clustered(n, d, centres, sigma, rng, batch=50_000):
    """SYNTHETIC clustered unit vectors: a random centre plus Gaussian noise, normalised (float32, built in batches)."""
    out = np.empty((n, d), np.float32)
    for a in range(0, n, batch):
        b = min(n, a + batch)
        lab = rng.integers(0, len(centres), b - a)
        x = centres[lab] + sigma * rng.standard_normal((b - a, d), dtype=np.float32) / np.float32(math.sqrt(d))
        out[a:b] = x / np.linalg.norm(x, axis=1, keepdims=True)
    return out


def recall(approx, exact):
    """ANN recall@k: share of the exact top-k ids that the approximate top-k also returned (one query)."""
    return len(set(approx) & set(exact)) / len(exact)


# ---------------------------------------------------------------- K1
head("K1 environment, corpus, models")
import faiss                                          # noqa: E402  optional `ann` group

faiss.omp_set_num_threads(1)
try:
    cpu = subprocess.run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"],
                         capture_output=True, text=True, timeout=30).stdout.strip()
except Exception as ex:                                # noqa: BLE001
    cpu = f"unknown ({ex})"
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in
      ("pymupdf", "sentence-transformers", "torch", "numpy", "faiss-cpu")})
print(f"faiss.__version__={faiss.__version__}; faiss threads set to 1 (reproducible builds)")
print("pdf sha256", hashlib.sha256(pdf_bytes).hexdigest())
print(f"97 chunks: count={N} chunks.jsonl sha256={SHA_JL} (P3 verify / C2 lab / P4 K1: d4108b89...)")
print(f"draft seeds: {len(SEEDS)} ({len(ANS)} answerable); relevant seqs {REL}")
print(f"verification queries: 10 draft-seed questions + {len(HEADS)} page heads (first 200 characters of each page) = {10 + len(HEADS)}")
print(f"TIME machine: {cpu} | logical cpus {os.cpu_count()}")

from sentence_transformers import SentenceTransformer  # noqa: E402

m6 = SentenceTransformer(L6, device="cpu")


def enc(texts):
    return m6.encode(list(texts), convert_to_numpy=True, batch_size=32, show_progress_bar=False).astype(np.float32)


V = enc(TEXT)
QS = enc([s["question"] for s in SEEDS])
QH = enc(HEADS)
Q43 = np.concatenate([QS, QH])
print(f"V {V.shape} {V.dtype}; max |norm-1| = {np.abs(np.linalg.norm(V, axis=1) - 1).max():.2e}")

# ---------------------------------------------------------------- K2
head("K2 shapes and memory: one score per chunk")
q = QS[[s["qid"] for s in SEEDS].index("D-002")]
s = V @ q
print(f"q {q.shape}; V {V.shape}; s = V @ q -> {s.shape}: one score per chunk")
print(f"batch of the 10 seed questions: Q @ V.T -> {(QS @ V.T).shape} (questions x chunks)")
print(f"an all-pairs chunk matrix V @ V.T would be {N}x{N} = {N * N:,} numbers; retrieval for one question needs {N}")
print(f"index bytes float32: {N} x {V.shape[1]} x 4 = {V.nbytes:,}; per vector {V[0].nbytes}")

# ---------------------------------------------------------------- K3
head("K3 D-002 'In what year was the Paris Agreement adopted?' over the 97 chunks: top-10")
o = brute(s, N)
for r, i in enumerate(o[:10], 1):
    nxt = s[o[r]] if r < N else float("nan")
    print(f"rank {r:2d}: seq {i:2d} page {PAGE[i]:2d} score {f4(s[i])} gap to next {s[i] - nxt:.4f}"
          f"{'  <- relevant (evidence)' if i in REL['D-002'] else ''}")
print(f"first relevant rank {first_rel(o, 'D-002')}; top-{K} = {o[:K]}; gap rank1-rank2 {s[o[0]] - s[o[1]]:.4f}; "
      f"gap rank3-rank4 {s[o[2]] - s[o[3]]:.6f}; gap rank4-rank5 {s[o[3]] - s[o[4]]:.4f}")
print(f"score range over the 97 chunks {s.min():.4f}..{s.max():.4f}")
print("all 97 scores in seq order:", json.dumps([round(float(x), 4) for x in s]))
EXR = [first_rel(brute(V @ QS[j], N), x["qid"]) for j, x in enumerate(SEEDS) if x["answerable"]]
print(f"exact search, 8 answerable seeds: first relevant ranks {EXR}; (Hit@1, Hit@4, MRR@10) = {summary(EXR)}")

# ---------------------------------------------------------------- K4
head("K4 ties: the tie-aware cut vs tempting variants")
toy = np.array([0.70, 0.90, 0.80, 0.80, 0.80, 0.10], dtype=np.float32)    # TOY scores
print(f"TOY scores {toy.tolist()}")
ft = faiss.IndexFlatIP(1)
ft.add(toy.reshape(-1, 1))
for k in range(1, 7):
    print(f"  k={k}: top_k (course) {top_k(toy, k).tolist()} | brute {brute(toy, k)} | argsort()[::-1] (InMemoryVectorStore) "
          f"{v_inmemory(toy, k)} | faiss IndexFlatIP (1-d vectors, query [1]) {ft.search(np.ones((1, 1), np.float32), k)[1][0].tolist()} "
          f"| argpartition only {v_argpart_only(toy, k)} | sort the picked k {v_sort_picked(toy, k)} | stable argsort(-s) {v_stable(toy, k)}")
print(f"  ids tied with the 2nd-best score: {np.flatnonzero(toy == 0.80).tolist()}")
rng = np.random.default_rng(5)
ARR = [rng.integers(0, 6, 20).astype(np.float32) / 5 for _ in range(300)]   # TOY tie-heavy: 20 scores in {0, .2, ..., 1}
print("300 TOY tie-heavy arrays (20 scores each from {0, 0.2, ..., 1.0}, seed 5): equal to brute force (same ids, same order)")
for k in (1, 4, 10):
    row = {name: sum(list(map(int, f(a, k))) == brute(a, k) for a in ARR) for name, f in
           (("top_k", lambda a, k: top_k(a, k).tolist()), ("argpartition only", v_argpart_only),
            ("argpartition, then sort the picked k", v_sort_picked), ("argsort()[::-1] (InMemoryVectorStore)", v_inmemory),
            ("stable argsort(-s)", v_stable))}
    same_set = sum(set(v_sort_picked(a, k)) == set(brute(a, k)) for a in ARR)
    fi = faiss.IndexFlatIP(1)
    ok_f = 0
    for a in ARR:
        fi.reset()
        fi.add(a.reshape(-1, 1))
        ok_f += fi.search(np.ones((1, 1), np.float32), k)[1][0].tolist() == brute(a, k)
    print(f"  k={k:2d}: " + "; ".join(f"{n} {v}/300" for n, v in row.items()) + f"; faiss IndexFlatIP {ok_f}/300 "
          f"| 'sort the picked k' has the right SET for {same_set}/300")
gaps = []
for x in Q43:
    ss = np.sort(V @ x)[::-1]
    gaps.append(float(ss[K - 1] - ss[K]))
print(f"43 real queries: gap between rank {K} and {K + 1}: min {min(gaps):.5f} median {np.median(gaps):.5f} max {max(gaps):.5f}; "
      f"queries with a gap < 1e-6: {sum(g < 1e-6 for g in gaps)}; < 0.001: {sum(g < 1e-3 for g in gaps)}")
d32 = max(float(np.abs((V @ x).astype(np.float64) - V.astype(np.float64) @ x.astype(np.float64)).max()) for x in Q43)
print(f"max |score float32 - score float64| over the 43 queries: {d32:.2e}")
agree = {k: sum(top_k(V @ x, k).tolist() == brute(V @ x, k) for x in Q43) for k in (1, 4, 10)}
inm = {k: sum(v_inmemory(V @ x, k) == brute(V @ x, k) for x in Q43) for k in (1, 4, 10)}
print(f"43 real queries: top_k == brute {agree}; argsort()[::-1] == brute {inm} (no exact ties in real scores)")
V5 = np.tile(V, (5, 1))                                # dartboard cell 9: every document 5 times
s5 = V5 @ q
print(f"duplicated index (5 copies, {len(V5)} rows), D-002 top-4 rows: top_k {top_k(s5, 4).tolist()} | "
      f"argsort()[::-1] {v_inmemory(s5, 4)} | distinct chunks in top-4: {len({int(r) % N for r in top_k(s5, 4)})}")

# ---------------------------------------------------------------- K5
head("K5 rows and metadata: alignment")
ids = top_k(s, K)
print(f"D-002 top-{K}: " + ", ".join(f"row {int(i)} = {chunks[i]['chunk_id'][-5:]} p.{PAGE[i]}" for i in ids))
Vbad = np.delete(V, 0, axis=0)
bad = top_k(Vbad @ q, K)
print("misaligned (row 0 deleted from the vectors only; metadata unchanged), D-002 top-4:")
for i in bad:
    i = int(i)
    print(f"  row {i}: metadata says seq {i} p.{PAGE[i]}; the vector is really seq {i + 1} p.{PAGE[i + 1]}")
print(f"guard len(V) == len(meta): {len(Vbad) == N}")

# ---------------------------------------------------------------- K6
head("K6 filters: pre-filter vs post-filter (fetch_k = 20, LangChain FAISS default)")
keep = np.array([p >= 25 for p in PAGE])
sel = keep.mean()
print(f"filter page >= 25 keeps {int(keep.sum())}/{N} chunks: selectivity {sel:.4f}; expected passers among fetch_k=20: "
      f"{sel * 20:.2f}")


def pre(x, k=K):
    sc = np.where(keep, V @ x, -np.inf)
    return [int(i) for i in top_k(sc, k) if np.isfinite(sc[i])]


def post(x, k=K, fetch_k=20):
    return [int(i) for i in top_k(V @ x, fetch_k) if keep[i]][:k]


pre_n = [len(pre(x)) for x in Q43]
post_n = [len(post(x)) for x in Q43]
pass20 = [int(sum(keep[i] for i in top_k(V @ x, 20))) for x in Q43]
print(f"43 queries: pre-filter returned < {K} for {sum(n < K for n in pre_n)}; post-filter < {K} for "
      f"{sum(n < K for n in post_n)}, 0 for {sum(n == 0 for n in post_n)}; histogram {dict(sorted({c: post_n.count(c) for c in set(post_n)}.items()))}")
print(f"passers among the top 20: mean {np.mean(pass20):.2f}, min {min(pass20)}, max {max(pass20)}")
pre_post_same = sum(pre(x) == post(x) for x in Q43)
print(f"pre and post give the same ids for {pre_post_same}/43 (where post is short it is a prefix of pre: "
      f"{sum(pre(x)[:len(post(x))] == post(x) for x in Q43)}/43)")
print(f"D-002: pre {pre(q)} pages {[PAGE[i] for i in pre(q)]}; post {post(q)}")
QNAMES = [s_["qid"] for s_ in SEEDS] + [f"page-head p.{i + 1}" for i in range(len(HEADS))]
j = next(j for j, x in enumerate(Q43) if len(post(x)) < K)
x = Q43[j]
t20 = top_k(V @ x, 20)
print(f"example of a short post-filter: query {QNAMES[j]!r}: top-20 (seq:page) "
      + " ".join(f"{int(i)}:{PAGE[i]}{'*' if keep[i] else ''}" for i in t20) + f" (* passes); post {post(x)}; pre {pre(x)} "
      f"pages {[PAGE[i] for i in pre(x)]}; pre-filter ranks of its results in the unfiltered list "
      f"{[brute(V @ x, N).index(i) + 1 for i in pre(x)]}")
for fk in (4, 10, 20, 40):
    pn = [len(post(x, fetch_k=fk)) for x in Q43]
    print(f"  post-filter fetch_k={fk:2d}: short for {sum(n < K for n in pn)}/43, empty for {sum(n == 0 for n in pn)}/43")

# ---------------------------------------------------------------- K7
head("K7 library conventions on the 97 chunks (faiss run; LangChain rules replayed in NumPy from the source lines)")
fl2 = faiss.IndexFlatL2(V.shape[1])
fl2.add(V)
Dl2, Il2 = fl2.search(q[None], 10)
fip = faiss.IndexFlatIP(V.shape[1])
fip.add(V)
Dip, Iip = fip.search(q[None], 10)
print(f"IndexFlatL2 D-002 top-10 ids {Il2[0].tolist()} distances {[f4(x) for x in Dl2[0][:4]]}...")
print(f"  == 2 - 2cos (squared L2): max abs diff {np.abs(Dl2[0] - (2 - 2 * s[Il2[0]])).max():.2e}; true L2 would be "
      f"{f4(math.sqrt(Dl2[0][0]))} for rank 1")
print(f"IndexFlatIP D-002 top-10 ids {Iip[0].tolist()} scores {[f4(x) for x in Dip[0][:4]]}...; equals cosine: "
      f"max abs diff {np.abs(Dip[0] - s[Iip[0]]).max():.2e}; same ids as brute {Iip[0].tolist() == brute(s, 10)}; "
      f"same as IndexFlatL2 {Iip[0].tolist() == Il2[0].tolist()}")
allD, allI = fl2.search(q[None], N)
rel_lc = 1 - allD[0] / math.sqrt(2)
print(f"LangChain relevance 1 - d/sqrt(2) on faiss squared L2, D-002: rank 1 {f4(rel_lc[0])} (cos {f4(s[allI[0][0]])}); "
      f"negative for {int((rel_lc < 0).sum())} of {N} chunks; crossing at cos = 1 - 1/sqrt(2) = {1 - 1 / math.sqrt(2):.4f}")
for c in (0.8, 0.5, 0.2934, 0.2):
    print(f"  cos {c}: squared L2 {2 - 2 * c:.4f} -> relevance {1 - (2 - 2 * c) / math.sqrt(2):.4f}; "
          f"on true L2 {1 - math.sqrt(2 - 2 * c) / math.sqrt(2):.4f}")
ok_ip = sum(fip.search(x[None], 10)[1][0].tolist() == brute(V @ x, 10) for x in Q43)
print(f"faiss IndexFlatIP top-10 == brute force for {ok_ip}/43 real queries")
print(f"defaults read from the objects: IndexHNSWFlat(d, 32) efConstruction {faiss.IndexHNSWFlat(8, 32).hnsw.efConstruction}, "
      f"efSearch {faiss.IndexHNSWFlat(8, 32).hnsw.efSearch}; IndexIVFFlat nprobe {faiss.IndexIVFFlat(faiss.IndexFlatL2(8), 8, 4).nprobe}; "
      f"IndexHNSWFlat metric default L2: {faiss.IndexHNSWFlat(8, 32).metric_type == faiss.METRIC_L2}")

# ---------------------------------------------------------------- K8
head("K8 exact search cost (NumPy V @ q + top_k; SYNTHETIC clustered unit vectors beyond 97; TIME lines vary by run)")
grng = np.random.default_rng(2)
QN = 200
p50, p95, n = lat(lambda x: top_k(V @ x, K), list(Q43) * 5)
print(f"TIME real N=97 d=384: p50 {p50 * 1e3:.1f} us p95 {p95 * 1e3:.1f} us ({n} queries)")
TIMES = {}
for d in (384, 1536):
    cen = unit(grng.standard_normal((1000, d), dtype=np.float32))
    for n_ in (1_000, 10_000, 100_000, 200_000):
        A = clustered(n_, d, cen, 0.8, grng)
        Qx = clustered(QN, d, cen, 0.8, grng)
        p50, p95, n = lat(lambda x: top_k(A @ x, K), list(Qx))
        TIMES[(n_, d)] = p50
        print(f"memory N={n_:>7,} d={d:4d}: {A.nbytes:>13,} bytes ({A.nbytes / 1e6:.1f} MB)")
        print(f"TIME N={n_:>7,} d={d:4d}: p50 {p50:.3f} ms p95 {p95:.3f} ms ({n} queries)")
        if (n_, d) == (100_000, 384):
            p8, _, _ = lat(lambda x: top_k(A @ x, 2 * K), list(Qx))
            print(f"TIME   same index, k=8: p50 {p8:.3f} ms (ratio k8/k4 {p8 / p50:.2f})")
            t0 = time.perf_counter()
            for _ in range(5):
                Sb = Qx[:100] @ A.T
                [top_k(r, K) for r in Sb]
            tb = (time.perf_counter() - t0) / 5 * 1e3
            print(f"TIME   batch of 100 queries (Q @ A.T then top_k per row): {tb:.1f} ms total, {tb / 100:.3f} ms per query")
        del A
for d in (384, 1536):
    print(f"TIME doubling N 100k -> 200k, d={d}: p50 ratio {TIMES[(200_000, d)] / TIMES[(100_000, d)]:.2f}; "
          f"d 384 -> 1536 at 100k: ratio {TIMES[(100_000, 1536)] / TIMES[(100_000, 384)]:.2f}")
c384 = TIMES[(200_000, 384)] / 200_000
c1536 = TIMES[(200_000, 1536)] / 200_000
for budget in (10, 50):
    print(f"TIME N_max for a {budget} ms p50 budget (linear from the 200k point): d=384 {budget / c384:,.0f}; d=1536 {budget / c1536:,.0f}")
print(f"TIME projected p50 at 1,000,000 x 384 (linear from 200k): {c384 * 1e6:.1f} ms; at 2,000,000 x 1,536: {c1536 * 2e6:.1f} ms")

# ---------------------------------------------------------------- K9
head("K9 IVF on a 2-D TOY (the lesson's slider picture): 24 points, 4 cells")
trng = np.random.default_rng(7)
BLOB = np.array([[2.0, 2.2], [6.8, 2.0], [2.4, 6.6], [6.6, 6.4]])
P2 = np.round(np.concatenate([b + trng.normal(0, 0.95, (6, 2)) for b in BLOB]), 2)
C2 = P2[[0, 6, 12, 18]].copy()                        # init: the first point of each blob
for _ in range(20):                                    # Lloyd's k-means, 4 cells
    lab = np.argmin(((P2[:, None] - C2[None]) ** 2).sum(-1), 1)
    C2 = np.array([P2[lab == j].mean(0) for j in range(4)])
C2 = np.round(C2, 2)
lab = np.argmin(((P2[:, None] - C2[None]) ** 2).sum(-1), 1)
print("points", P2.tolist())
print("centroids", C2.tolist(), "cell sizes", np.bincount(lab, minlength=4).tolist())
qq = np.array([4.25, 4.25])                            # the lesson's default query position (the slider picture)
cell_order = np.argsort(((C2 - qq) ** 2).sum(1), kind="stable")
nn = int(np.argmin(((P2 - qq) ** 2).sum(1)))
print(f"query {qq.tolist()}: cells by centroid distance {cell_order.tolist()} (distances "
      f"{[round(float(np.sqrt(((C2[c] - qq) ** 2).sum())), 3) for c in cell_order]}); true nearest point #{nn} {P2[nn].tolist()} "
      f"in cell {lab[nn]} at distance {np.sqrt(((P2[nn] - qq) ** 2).sum()):.3f}")
for npb in (1, 2, 3, 4):
    scan = [i for i in range(len(P2)) if lab[i] in cell_order[:npb]]
    got = min(scan, key=lambda i: ((P2[i] - qq) ** 2).sum())
    print(f"  nprobe={npb}: scans {len(scan)}/{len(P2)} points; returns #{got} -> {'correct' if got == nn else 'MISSES the true nearest'}")


# ---------------------------------------------------------------- K10
def kmeans(X, k, iters, seed):
    """Lloyd's k-means (NumPy, seeded): init = k random points; assign by L2 to the centroid; update = mean."""
    r = np.random.default_rng(seed)
    C = X[r.choice(len(X), k, replace=False)].copy()
    for _ in range(iters):
        a = np.argmax(X @ C.T - 0.5 * (C * C).sum(1)[None], 1)   # argmin ||x - c||^2
        for j in range(k):
            m = a == j
            if m.any():
                C[j] = X[m].mean(0)
    a = np.argmax(X @ C.T - 0.5 * (C * C).sum(1)[None], 1)
    return C, a


def ivf_search(X, C, assign, lists, x, k, nprobe):
    """IVF from scratch: rank the cells by centroid, scan only the nprobe nearest cells, exact top-k inside them."""
    cells = top_k(-(((C - x) ** 2).sum(1)), nprobe)
    cand = np.concatenate([lists[c] for c in cells])
    sc = X[cand] @ x
    return cand[top_k(sc, k)].tolist(), len(cand)


head("K10 IVF from scratch in NumPy: climate windows (real MiniLM vectors), then SYNTHETIC 100k")
full = "\n".join(pages)
WIN = [full[a:a + 300] for a in range(0, len(full), 100) if len(full[a:a + 300]) >= 50]
W = enc(WIN)
print(f"climate windows: 300 characters, stride 100 -> {len(W)} windows; nlist rule 10*sqrt(N) = {10 * math.sqrt(len(W)):.0f} "
      f"(about {len(W) / (10 * math.sqrt(len(W))):.1f} vectors per cell, too few)")
EXW = {k: [brute(W @ x, k) for x in Q43] for k in (4, 10)}
for nl in (8, 32):
    C, a = kmeans(W, nl, 25, 0)
    lists = [np.flatnonzero(a == j) for j in range(nl)]
    sizes = sorted(len(x) for x in lists)
    print(f"nlist={nl}: cell sizes min {sizes[0]} median {sizes[len(sizes) // 2]} max {sizes[-1]}")
    for npb in sorted({1, 2, 4, 8, nl // 2, nl}):
        res = [ivf_search(W, C, a, lists, x, 4, npb) for x in Q43]
        r4 = np.mean([recall(r[0], e) for r, e in zip(res, EXW[4])])
        miss = sum(recall(r[0], e) < 1 for r, e in zip(res, EXW[4]))
        print(f"  nprobe={npb:2d}: recall@4 {r4:.3f} (queries with a miss {miss}/43); scanned {np.mean([r[1] for r in res]) / len(W):.3f} of the vectors")
# SYNTHETIC 100k, d=384
srng = np.random.default_rng(11)
cen = unit(srng.standard_normal((1000, 384), dtype=np.float32))
X = clustered(100_000, 384, cen, 0.8, srng)
QX = clustered(200, 384, cen, 0.8, srng)
EX10 = [brute(X @ x, 10) for x in QX]
EX4 = [e[:4] for e in EX10]
print(f"SYNTHETIC: 100,000 x 384 unit vectors around 1,000 random centres (noise 0.8), 200 queries from the same generator")
t0 = time.perf_counter()
C, a = kmeans(X, 1024, 10, 0)
print(f"TIME NumPy k-means nlist=1024, 10 iterations: {time.perf_counter() - t0:.1f} s")
lists = [np.flatnonzero(a == j) for j in range(1024)]
sizes = sorted(len(x) for x in lists)
print(f"nlist=1024 (rule 10*sqrt(N) = {10 * math.sqrt(1e5):.0f}): cell sizes min {sizes[0]} median {sizes[512]} max {sizes[-1]}")
for npb in (1, 2, 4, 8, 16, 32, 64):
    res = [ivf_search(X, C, a, lists, x, 10, npb) for x in QX]
    r10 = np.mean([recall(r[0], e) for r, e in zip(res, EX10)])
    r4 = np.mean([recall(r[0][:4], e) for r, e in zip(res, EX4)])
    print(f"  nprobe={npb:2d}: recall@10 {r10:.3f} recall@4 {r4:.3f}; scanned {np.mean([r[1] for r in res]) / len(X):.4f} of the vectors")
del C, a, lists

# ---------------------------------------------------------------- K11
head("K11 faiss IVF and HNSW on the same SYNTHETIC 100k (1 thread; inner product on unit vectors = cosine)")
flat = faiss.IndexFlatIP(384)
flat.add(X)
p50f, p95f, _ = lat(lambda x: flat.search(x[None], 10), list(QX))
okf = sum(flat.search(x[None], 10)[1][0].tolist() == e for x, e in zip(QX, EX10))
p50n, p95n, _ = lat(lambda x: top_k(X @ x, 10), list(QX))
print(f"faiss IndexFlatIP (exact): top-10 == NumPy brute force for {okf}/200")
print(f"TIME exact: faiss IndexFlatIP 1 thread p50 {p50f:.3f} ms p95 {p95f:.3f} ms | NumPy (OpenBLAS threads) p50 {p50n:.3f} ms p95 {p95n:.3f} ms")


def sweep(index, knob, values, label):
    rows = []
    for v in values:
        setattr(knob[0], knob[1], v)
        I = [index.search(x[None], 10)[1][0].tolist() for x in QX]
        r10 = np.mean([recall(i, e) for i, e in zip(I, EX10)])
        r4 = np.mean([recall(i[:4], e) for i, e in zip(I, EX4)])
        p50, p95, _ = lat(lambda x: index.search(x[None], 10), list(QX))
        rows.append((v, r10, r4, p50, p95))
        print(f"  {label}={v:4d}: recall@10 {r10:.3f} recall@4 {r4:.3f}")
        print(f"TIME   {label}={v:4d}: p50 {p50:.3f} ms p95 {p95:.3f} ms")
    return rows


qz = faiss.IndexFlatIP(384)
ivf = faiss.IndexIVFFlat(qz, 384, 1024, faiss.METRIC_INNER_PRODUCT)
t0 = time.perf_counter()
ivf.train(X)
ivf.add(X)
print(f"TIME IVFFlat nlist=1024: train + add {time.perf_counter() - t0:.1f} s")
print(f"IVFFlat nprobe default after construction: {ivf.nprobe}")
sweep(ivf, (ivf, "nprobe"), (1, 2, 4, 8, 16, 32, 64), "nprobe")
SER = {"IndexFlatIP": len(faiss.serialize_index(flat)), "IndexIVFFlat nlist 1024": len(faiss.serialize_index(ivf))}
del ivf
for M in (16, 32):
    h = faiss.IndexHNSWFlat(384, M, faiss.METRIC_INNER_PRODUCT)
    t0 = time.perf_counter()
    h.add(X)
    print(f"TIME HNSWFlat M={M} (efConstruction {h.hnsw.efConstruction}): build {time.perf_counter() - t0:.1f} s")
    print(f"HNSWFlat M={M}: efSearch default {h.hnsw.efSearch}; top level {h.hnsw.max_level}")
    sweep(h, (h.hnsw, "efSearch"), (16, 32, 64, 128, 256) if M == 32 else (16, 64), "efSearch")
    SER[f"IndexHNSWFlat M {M}"] = len(faiss.serialize_index(h))
    if M == 32:
        H32 = h
for name, b in SER.items():
    print(f"serialized bytes {name}: {b:,} ({b / len(X):.1f} per vector; raw float32 vector {384 * 4})")

# ---------------------------------------------------------------- K12
head("K12 filtered ANN on the SYNTHETIC 100k: a tenant filter keeping 1% (tenant = row % 100 == 7)")
tenant = np.arange(len(X)) % 100
allow = np.flatnonzero(tenant == 7)
Xs = X[allow]
EXF = [allow[top_k(Xs @ x, 4)].tolist() for x in QX]
print(f"allowed rows {len(allow)} of {len(X)} (selectivity {len(allow) / len(X):.2%})")
p50s, p95s, _ = lat(lambda x: top_k(Xs @ x, 4), list(QX))
p50m, p95m, _ = lat(lambda x: top_k(np.where(tenant == 7, X @ x, -np.inf), 4), list(QX))
print(f"TIME exact on the 1,000-row subset: p50 {p50s:.3f} ms | exact pre-filter by masking all 100k: p50 {p50m:.3f} ms")
H32.hnsw.efSearch = 16
for efs, fetch in ((16, 16), (64, 64), (256, 256)):
    H32.hnsw.efSearch = efs
    got = []
    for x in QX:
        I = H32.search(x[None], fetch)[1][0]
        got.append([int(i) for i in I if i >= 0 and tenant[i] == 7][:4])
    lens = [len(g) for g in got]
    print(f"HNSW post-filter (efSearch {efs}, fetch {fetch}, then keep tenant 7): results per query mean {np.mean(lens):.2f} of 4; "
          f"empty {sum(n == 0 for n in lens)}/200; full 4 {sum(n == 4 for n in lens)}/200")
selb = faiss.IDSelectorBatch(allow.astype("int64"))
for efs in (16, 64, 256):
    prm = faiss.SearchParametersHNSW(sel=selb, efSearch=efs)
    got = [[int(i) for i in H32.search(x[None], 4, params=prm)[1][0] if i >= 0] for x in QX]
    lens = [len(g) for g in got]
    rc = np.mean([recall(g, e) for g, e in zip(got, EXF)])
    p50, _, _ = lat(lambda x: H32.search(x[None], 4, params=prm), list(QX))
    print(f"HNSW with the filter inside the search (IDSelectorBatch, efSearch {efs}): results mean {np.mean(lens):.2f} of 4; "
          f"full 4 {sum(n == 4 for n in lens)}/200; recall@4 vs exact-on-subset {rc:.3f}")
    print(f"TIME   IDSelector efSearch {efs}: p50 {p50:.3f} ms")
H32.hnsw.efSearch = 16

# ---------------------------------------------------------------- K13
head("K13 does ANN change retrieval on the 97 chunks? 8 answerable seeds (first relevant rank; Hit@1, Hit@4, MRR@10)")
print(f"exact: {EXR} {summary(EXR)}")
hs = faiss.IndexHNSWFlat(384, 32, faiss.METRIC_INNER_PRODUCT)
hs.add(V)
iv = faiss.IndexIVFFlat(faiss.IndexFlatIP(384), 384, 10, faiss.METRIC_INNER_PRODUCT)
iv.cp.min_points_per_centroid = 1
iv.train(V)
iv.add(V)
QA = np.stack([QS[[x["qid"] for x in SEEDS].index(a["qid"])] for a in ANS])
for name, idx, knob, vals in (("HNSW M=32", hs, (hs.hnsw, "efSearch"), (16,)), ("IVF nlist=10", iv, (iv, "nprobe"), (1, 2, 3, 10))):
    for v in vals:
        setattr(knob[0], knob[1], v)
        ranks, rec = [], []
        for x, a in zip(QA, ANS):
            I = [int(i) for i in idx.search(x[None], 10)[1][0] if i >= 0]
            ranks.append(first_rel(I, a["qid"]))
            rec.append(recall(I[:4], brute(V @ x, 4)))
        r43 = np.mean([recall([int(i) for i in idx.search(x[None], 4)[1][0] if i >= 0], brute(V @ x, 4)) for x in Q43])
        print(f"{name} {knob[1]}={v}: ranks {ranks} {summary(ranks)}; recall@4 vs exact: 8 seeds {np.mean(rec):.3f}, 43 queries {r43:.3f}")

# ---------------------------------------------------------------- K14
head("K14 FORMULA arithmetic for the lesson")
for n_, d in ((97, 384), (50_000, 1024), (1_000_000, 384), (2_000_000, 1536), (100_000, 1536)):
    print(f"float32 index {n_:>9,} x {d:4d} x 4 = {n_ * d * 4:>14,} bytes ({n_ * d * 4 / 1e9:.4f} GB)")
for d in (384, 1024, 1536):
    print(f"bytes per vector d={d}: float32 {4 * d}, int8 {d}, binary {d // 8}")
for n_ in (97, len(W), 100_000, 1_000_000):
    print(f"nlist rule 10*sqrt(N): N={n_:,} -> {10 * math.sqrt(n_):,.0f}")
print(f"LangChain relevance crossing: 1 - (2 - 2c)/sqrt(2) = 0  <=>  c = 1 - 1/sqrt(2) = {1 - 1 / math.sqrt(2):.6f}")
ex, an = [3, 7, 12, 18, 25], [3, 7, 18, 30, 41]           # TOY ANN recall
print(f"TOY ANN recall@5: exact {ex}, ANN {an}: overlap {len(set(ex) & set(an))} -> {len(set(ex) & set(an)) / 5:.2f}")
print("\nDONE")
