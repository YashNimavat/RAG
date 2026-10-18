"""vector_search_check: is exact search enough for MY documents, and is my vector store set up safely?

What this is: a command-line tool (also importable) that chunks your documents like the course's v0 index (the 07
recursive splitter, per page, 1,000 characters with 200 overlap), embeds them with a LOCAL sentence-transformers model,
searches them exactly (one score per chunk, the tie-aware cut), times that search on this machine, projects it to the
corpus size you expect, and writes a Markdown report:
  1 Collection       chunks, vector lengths, memory, alignment of rows and metadata
  2 Speed and memory measured p50/p95 per query here; projected at --grow; the largest corpus your budget allows
  3 Ties             exact ties and near-ties at the k-th place; duplicate chunks
  4 Filters          with --filter: pre-filter vs post-filter (fetch_k), how often post-filtering comes back short
  5 ANN              with --ann (needs faiss-cpu, the optional `ann` group): HNSW and IVF recall@k against exact search
  6 Per question     the top k with scores; the rank of the chunk that contains "expect"
  7 Checklist        V1-V12 with a verdict (✓ fine, ✗ problem found, ? check by hand) and the evidence
  8 Recommendation   exact / exact + batching / ANN with a recall report / fix first / too little data
What this is not: an evaluation of retrieval quality, or a benchmark of your production store. Timings are for this
machine only, and ANN recall on a few hundred vectors says little about ANN at millions.

Lesson: study/lessons/P5_vector_search.html. Checks V1-V12 are the lesson's real-world checklist.

No API calls. --provider cohere is reserved for when the course's study/llmops/ cache exists (record once, replay
offline); until then it refuses to run. Book text must never be sent to any API. Standard library + numpy + pymupdf
+ sentence-transformers (local Hugging Face cache only); faiss-cpu only with --ann.

Usage, from rag_learning/:
    uv run python study/tools/vector_search_check.py --docs my_docs/ --questions q.jsonl --report vs_report.md
    uv run --group ann python study/tools/vector_search_check.py --docs a.pdf --questions q.jsonl \
        --grow 1000000 --budget-ms 10 --qps 5 --filter "page>=25" --ann
    # check an index you saved yourself (rows of vectors.npy must match the lines of chunks.jsonl, each with "text"):
    uv run python study/tools/vector_search_check.py --docs a.pdf --vectors index/vectors.npy --meta index/chunks.jsonl
Questions: the same formats as embed_fit_check.py: .txt (one per line) or .jsonl with
    {"q": "...", "expect": "text the right chunk contains" (optional), "type": "..." (optional), "id": "..." (optional)}
--filter: page>=N, page<=N, page==N, page!=N or doc==<file name>.

Import:
    from vector_search_check import run_check, render_report
    res = run_check(["doc.pdf"], "questions.jsonl", k=4, grow=1_000_000)
    print(render_report(res))
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed_fit_check import (DEFAULT_MODEL, _version, first_hit, load_documents, load_model,  # noqa: E402
                             load_questions, make_chunks, metrics, model_setup, norm_ws)

OK, BAD, ASK = "✓", "✗", "?"
DUP = 0.98                 # cosine above which two chunks count as near-duplicates
NEAR_TIE = 1e-6            # a k-th / (k+1)-th gap below this is a near-tie (float32 rounding is about 1e-7)
MIN_LABELLED = 10          # fewer labelled questions than this = "mechanism only"
MIN_QUESTIONS = 5          # fewer questions than this = "too little data"
EXTRA_QUERIES = 100        # chunk-head queries added for timing and ANN recall (the first 200 characters of chunks)
ANN_RECALL_TARGET = 0.95   # default recall@k an ANN arm must reach against exact search
TIMED = 200                # timed queries per measurement (warm-up excluded)


# ---------------------------------------------------------------------------------------------------------------- search
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


def nearest_rank(xs, p):
    """Nearest-rank percentile, no interpolation: the ceil(p/100 * n)-th smallest value."""
    ys = sorted(xs)
    return ys[max(0, math.ceil(p / 100 * len(ys)) - 1)]


def latency(fn, queries, warm=5):
    """Per-query latency in ms (p50, p95) over the queries; the first `warm` calls are not timed."""
    for x in queries[:warm]:
        fn(x)
    ts = []
    for x in queries:
        t0 = time.perf_counter()
        fn(x)
        ts.append((time.perf_counter() - t0) * 1e3)
    return nearest_rank(ts, 50), nearest_rank(ts, 95)


def unit(M):
    M = np.asarray(M, np.float32)
    n = np.linalg.norm(M, axis=-1, keepdims=True)
    return M / np.where(n == 0, 1, n)


def parse_filter(expr):
    m = re.fullmatch(r"\s*(page|doc)\s*(>=|<=|==|!=)\s*(.+?)\s*", expr or "")
    if not m:
        raise ValueError(f"cannot read --filter {expr!r}: use page>=N, page<=N, page==N, page!=N or doc==<file name>")
    field, op, val = m.groups()
    if field == "page":
        v = int(val)
        ops = {">=": lambda p: p is not None and p >= v, "<=": lambda p: p is not None and p <= v,
               "==": lambda p: p == v, "!=": lambda p: p != v}
        return lambda c, docs: ops[op](c["page"])
    if op not in ("==", "!="):
        raise ValueError("doc filters support == and != only")
    return lambda c, docs: (docs[c["doc"]]["name"] == val) == (op == "==")


# ---------------------------------------------------------------------------------------------------------------- the check
def run_check(docs, questions=None, model=DEFAULT_MODEL, chunk_size=1000, overlap=200, chunker="v0", k=4,
              budget_ms=10.0, qps=1.0, grow=None, filt=None, fetch_k=20, ann=False, recall_target=ANN_RECALL_TARGET,
              manifest=None, vectors=None, meta=None, seed=0):
    docs = load_documents(docs) if not (docs and isinstance(docs[0], dict)) else docs
    qs = load_questions(questions)
    chunks = make_chunks(docs, chunk_size, overlap, chunker)
    m = load_model(model)
    setup = model_setup(m, model)
    texts = [c["text"] for c in chunks]
    N, d = len(chunks), setup["dim"]
    grow = int(grow or N)
    for c in chunks:
        c["_norm"] = norm_ws(c["text"])

    # 1 collection: vectors, lengths, memory, alignment
    E_raw = m.encode_document(texts, convert_to_numpy=True, batch_size=32, show_progress_bar=False).astype(np.float32)
    norms = np.linalg.norm(E_raw, axis=1)
    V = unit(E_raw)
    meta_rows = [{"row": i, "id": c["id"], "page": c["page"]} for i, c in enumerate(chunks)]
    align = {"own_rows": len(V), "own_meta": len(meta_rows), "own_ok": len(V) == len(meta_rows)
             and all(r["row"] == i for i, r in enumerate(meta_rows)), "user": None}
    if vectors and meta:
        align["user"] = check_user_index(m, vectors, meta)
    rng = np.random.default_rng(seed)
    heads = [texts[i].strip()[:200] for i in sorted(rng.choice(N, min(EXTRA_QUERIES, N), replace=False))]
    Q = unit(m.encode_query([q["q"] for q in qs], convert_to_numpy=True, batch_size=32, show_progress_bar=False)) \
        if qs else np.zeros((0, d), np.float32)
    H = unit(m.encode_query(heads, convert_to_numpy=True, batch_size=32, show_progress_bar=False))
    QA = np.concatenate([Q, H])                          # every query: yours first, then the chunk heads

    # 3 ties, near-ties, brute-force agreement, duplicates
    agree, gaps, ties = 0, [], []
    for j, x in enumerate(QA):
        s = V @ x
        agree += top_k(s, k).tolist() == brute(s, k)
        if N > k:
            ss = np.sort(s)[::-1]
            gaps.append(float(ss[k - 1] - ss[k]))
            if ss[k - 1] - ss[k] < NEAR_TIE:
                ties.append(j)
    hashes = {}
    for i, c in enumerate(chunks):
        hashes.setdefault(hashlib.sha256(c["_norm"].encode("utf-8")).hexdigest(), []).append(i)
    exact_dups = [ids for ids in hashes.values() if len(ids) > 1]
    near_dups = []
    if N <= 5000:
        C = V @ V.T
        iu = np.triu_indices(N, 1)
        pc = C[iu]
        near_dups = [(int(iu[0][j]), int(iu[1][j]), float(pc[j])) for j in np.flatnonzero(pc > DUP)[:50]]
    dup_set = {a for a, b, _ in near_dups} | {b for a, b, _ in near_dups}
    ties_info = {"agree": agree, "n_queries": len(QA), "gaps": gaps, "near_ties": len(ties),
                 "near_tie_yours": sum(j < len(Q) for j in ties), "exact_dups": exact_dups, "near_dups": near_dups}

    # 2 speed and memory (machine-specific)
    p50, p95 = latency(lambda x: top_k(V @ x, k), list(np.resize(QA, (max(TIMED, len(QA)), d))))
    n_syn = int(min(max(grow, 10_000), 200_000))
    syn = unit(rng.standard_normal((n_syn, d), dtype=np.float32))
    sq = unit(rng.standard_normal((TIMED, d), dtype=np.float32))
    s50, s95 = latency(lambda x: top_k(syn @ x, k), list(sq))
    t0 = time.perf_counter()
    for r in sq[:100] @ syn.T:
        top_k(r, k)
    batch_ms = (time.perf_counter() - t0) * 1e3 / 100
    del syn
    per_vec = s50 / n_syn
    speed = {"p50": p50, "p95": p95, "n_syn": n_syn, "syn_p50": s50, "syn_p95": s95, "batch_ms": batch_ms,
             "proj_p50": per_vec * grow, "proj_p95": s95 / n_syn * grow, "proj_batch": batch_ms / n_syn * grow,
             "n_max": budget_ms / per_vec, "bytes_now": N * d * 4, "bytes_grow": grow * d * 4,
             "int8_grow": grow * d, "budget_ms": budget_ms, "qps": qps, "grow": grow}
    speed["load"] = qps * speed["proj_p50"] / 1000          # share of one core spent searching, one query at a time

    # 4 filters
    filt_res = None
    if filt:
        test = parse_filter(filt)
        keep = np.array([test(c, docs) for c in chunks])
        pre_n, post_n = [], []
        for x in QA:
            s = V @ x
            sp = np.where(keep, s, -np.inf)
            pre_n.append(sum(np.isfinite(sp[i]) for i in top_k(sp, k)))
            post_n.append(sum(bool(keep[i]) for i in top_k(s, min(fetch_k, N))))
        post_k = [min(n, k) for n in post_n]
        filt_res = {"expr": filt, "kept": int(keep.sum()), "selectivity": float(keep.mean()), "fetch_k": fetch_k,
                    "expected": float(keep.mean()) * min(fetch_k, N), "mean_pass": float(np.mean(post_n)),
                    "pre_short": sum(n < min(k, int(keep.sum())) for n in pre_n), "post_short": sum(n < k for n in post_k),
                    "post_empty": sum(n == 0 for n in post_k), "n": len(QA)}

    # 5 ANN (optional)
    ann_res = run_ann(V, QA, k, recall_target) if ann else None

    # 6 per question
    rows = []
    for qi, q in enumerate(qs):
        s = V @ Q[qi]
        order = brute(s, N)
        targets = {i for i, c in enumerate(chunks) if q["expect"] and any(norm_ws(x) in c["_norm"] for x in q["expect"])}
        rows.append({**q, "top": [(order[j], float(s[order[j]])) for j in range(min(k, N))],
                     "gap": float(s[order[k - 1]] - s[order[k]]) if N > k else None,
                     "targets": sorted(targets), "rank": first_hit(order, targets) if targets else None,
                     "missing_target": bool(q["expect"]) and not targets, "dups_in_top": len(dup_set & set(order[:k]))})
    labelled = [r for r in rows if r["targets"]]
    measuring = metrics([r["rank"] for r in labelled], k) if labelled else None

    man = None
    if manifest:
        man = json.loads(Path(manifest).read_text(encoding="utf-8")) if isinstance(manifest, (str, Path)) else dict(manifest)
    res = {"docs": [{"name": x["name"], "pages": len(x["pages"]), "chars": sum(len(p) for p in x["pages"])} for x in docs],
           "settings": {"model": model, "chunker": chunker, "chunk_size": chunk_size, "overlap": overlap, "k": k,
                        "budget_ms": budget_ms, "qps": qps, "grow": grow, "filter": filt, "fetch_k": fetch_k, "ann": ann,
                        "recall_target": recall_target,
                        "versions": {p: _version(p) for p in ("sentence-transformers", "numpy", "pymupdf", "faiss-cpu")}},
           "setup": setup, "n_chunks": N, "dim": d, "chunks": [{"id": c["id"], "page": c["page"]} for c in chunks],
           "norm_min": float(norms.min()), "norm_max": float(norms.max()), "max_dev": float(np.abs(norms - 1).max()),
           "align": align, "ties": ties_info, "speed": speed, "filter": filt_res, "ann_res": ann_res, "n_questions": len(qs),
           "n_heads": len(heads), "rows": rows, "n_labelled": len(labelled), "measuring": measuring, "manifest": man}
    res["checklist"] = checklist(res)
    res["recommendation"] = recommend(res)
    return res


def check_user_index(model, vectors, meta):
    """Your own saved index: rows of vectors vs lines of meta, ids unique, and 5 sampled rows re-embedded from their text."""
    Vu = np.load(vectors)
    lines = [json.loads(x) for x in Path(meta).read_text(encoding="utf-8").splitlines() if x.strip()]
    ids = [str(x.get("chunk_id", x.get("id", i))) for i, x in enumerate(lines)]
    out = {"rows": int(Vu.shape[0]), "meta": len(lines), "dim": int(Vu.shape[1]) if Vu.ndim == 2 else None,
           "unique_ids": len(set(ids)) == len(ids), "sample": [], "norm_dev": float(np.abs(np.linalg.norm(Vu, axis=1) - 1).max())}
    n = min(len(lines), Vu.shape[0])
    if n and all("text" in x for x in lines[:n]):
        for i in sorted({int(round(t)) for t in np.linspace(0, n - 1, min(5, n))}):
            e = unit(model.encode_document([lines[i]["text"]], convert_to_numpy=True, show_progress_bar=False))[0]
            out["sample"].append((i, float(unit(Vu[i:i + 1])[0] @ e) if Vu.shape[1] == e.shape[0] else None))
    return out


def run_ann(V, QA, k, target):
    """HNSW and IVF from faiss (if installed) against exact search on the same vectors and queries."""
    try:
        import faiss
    except ImportError:
        return {"error": "faiss is not installed (uv add --group ann faiss-cpu==1.15.1, then run with uv run --group ann)"}
    faiss.omp_set_num_threads(1)
    N, d = V.shape
    kk = min(k, N)
    exact = [brute(V @ x, kk) for x in QA]
    rows = []

    def measure(name, index, knob, values, build_s, nbytes):
        for v in values:
            setattr(knob[0], knob[1], v)
            got = [[int(i) for i in index.search(x[None], kk)[1][0] if i >= 0] for x in QA]
            rec = [len(set(g) & set(e)) / kk for g, e in zip(got, exact)]
            p50, p95 = latency(lambda x: index.search(x[None], kk), list(np.resize(QA, (max(TIMED, len(QA)), d))))
            rows.append({"index": name, "knob": f"{knob[1]}={v}", "recall": float(np.mean(rec)),
                         "min_recall": float(min(rec)), "missed": sum(r < 1 for r in rec), "p50": p50, "p95": p95,
                         "build_s": build_s, "bytes": nbytes})

    t0 = time.perf_counter()
    h = faiss.IndexHNSWFlat(d, 32, faiss.METRIC_INNER_PRODUCT)
    h.add(V)
    bh = time.perf_counter() - t0
    measure("HNSW M=32 (efConstruction 40)", h, (h.hnsw, "efSearch"), (16, 64), bh, len(faiss.serialize_index(h)))
    nlist = max(1, min(int(round(10 * math.sqrt(N))), N // 39))      # faiss wants >= 39 training points per cell
    if nlist >= 2:
        t0 = time.perf_counter()
        iv = faiss.IndexIVFFlat(faiss.IndexFlatIP(d), d, nlist, faiss.METRIC_INNER_PRODUCT)
        iv.train(V)
        iv.add(V)
        bi = time.perf_counter() - t0
        measure(f"IVF nlist={nlist}", iv, (iv, "nprobe"), sorted({1, min(8, nlist)}), bi, len(faiss.serialize_index(iv)))
    flat = faiss.IndexFlatIP(d)
    flat.add(V)
    return {"rows": rows, "target": target, "n_queries": len(QA), "flat_bytes": len(faiss.serialize_index(flat)),
            "nlist": nlist, "faiss": faiss.__version__}


# ---------------------------------------------------------------------------------------------------------------- checklist
def checklist(res):
    k, sp, T, A = res["settings"]["k"], res["speed"], res["ties"], res["align"]
    out = []

    def add(cid, title, verdict, evidence, how):
        out.append({"id": cid, "title": title, "verdict": verdict, "evidence": evidence, "how": how})

    add("V1", "Vectors are length 1 (or normalised by you)", OK if res["max_dev"] < 1e-3 else BAD,
        f"lengths as returned {res['norm_min']:.6f}–{res['norm_max']:.6f}"
        + ("" if res["max_dev"] < 1e-3 else "; this tool normalised them, your pipeline must too, or dot, cosine and L2 disagree"),
        "max |‖v‖ − 1| over the stored vectors")
    man = res["manifest"]
    if man and man.get("model_id"):
        same = man["model_id"] == res["setup"]["name"]
        add("V2", "Questions and chunks use the same model id (and input type)", OK if same else BAD,
            f"index manifest says {man['model_id']!r}; questions here use {res['setup']['name']!r}",
            "store the model id and input type with the index; refuse a mismatch at query time")
    else:
        add("V2", "Questions and chunks use the same model id (and input type)", ASK,
            "this tool embeds both sides with one model; pass --manifest with your index's model_id to check your pipeline",
            "store the model id and input type with the index; refuse a mismatch at query time")
    u = A["user"]
    if u:
        bad_sample = [i for i, c in u["sample"] if c is None or c < 0.999]
        ok = u["rows"] == u["meta"] and u["unique_ids"] and not bad_sample
        add("V3", "Rows and metadata are aligned", OK if ok else BAD,
            f"your index: {u['rows']} vector rows, {u['meta']} metadata lines, ids unique: {u['unique_ids']}; "
            + (f"re-embedded rows {[i for i, _ in u['sample']]}: cos with the stored row "
               + ", ".join('-' if c is None else f'{c:.4f}' for _, c in u['sample']) if u["sample"] else "no text in the metadata, rows not re-embedded"),
            "assert len(V) == len(meta) at load time; re-embed a few rows from their text and compare")
    else:
        add("V3", "Rows and metadata are aligned", OK if A["own_ok"] else BAD,
            f"this tool's index: {A['own_rows']} rows, {A['own_meta']} metadata records, row i ↔ record i; "
            "pass --vectors and --meta to check an index you saved", "assert len(V) == len(meta) at load time; store chunk_id in each record")
    add("V4", "Exact top-k equals a brute-force reference", OK if T["agree"] == T["n_queries"] else BAD,
        f"tie-aware top_k == pure-Python full sort for {T['agree']}/{T['n_queries']} queries", "compare your search with a sorted() reference on real queries")
    add("V5", "Ties at the k-th place are handled by a written rule", BAD if T["near_ties"] and T["near_tie_yours"] else (ASK if T["near_ties"] else OK),
        f"queries with a k-th/(k+1)-th gap below {NEAR_TIE:g}: {T['near_ties']} of {T['n_queries']} ({T['near_tie_yours']} of yours); "
        + (f"smallest gap {min(T['gaps']):.2e}" if T["gaps"] else "fewer chunks than k"),
        "take every id scoring ≥ the k-th score, sort by (−score, id), cut to k; know your store's tie order")
    nd = len(T["near_dups"]) + sum(len(x) - 1 for x in T["exact_dups"])
    add("V6", "Duplicate chunks are known", BAD if nd else OK,
        f"{len(T['exact_dups'])} groups of identical chunks; {len(T['near_dups'])} pairs above cosine {DUP}"
        + (f"; questions with a duplicate in their top {k}: {sum(r['dups_in_top'] > 1 for r in res['rows'])}" if res["rows"] else ""),
        "deduplicate before indexing, or diversify the top k (R4)")
    fits = sp["proj_p95"] <= sp["budget_ms"]
    add("V7", "Exact search fits the latency budget at the expected size", OK if fits else BAD,
        f"here: p50 {sp['p50'] * 1e3:.0f} µs, p95 {sp['p95'] * 1e3:.0f} µs at N={res['n_chunks']:,}; projected at N={sp['grow']:,}: "
        f"p50 {sp['proj_p50']:.2f} ms, p95 {sp['proj_p95']:.2f} ms vs budget {sp['budget_ms']:g} ms; N_max ≈ {sp['n_max']:,.0f} (this machine)",
        "time real queries (warm-up excluded, nearest-rank p95) on the production machine; exact cost is linear in N × d")
    add("V8", "Index memory fits", OK if sp["bytes_grow"] < 4e9 else BAD,
        f"float32 now {sp['bytes_now']:,} bytes; at N={sp['grow']:,}: {sp['bytes_grow'] / 1e9:.3f} GB (int8: {sp['int8_grow'] / 1e9:.3f} GB)",
        "N × d × 4 bytes for float32; compare with the RAM you can give the index")
    F = res["filter"]
    if F:
        add("V9", "Filters do not starve results", BAD if F["post_short"] else OK,
            f"{F['expr']} keeps {F['kept']}/{res['n_chunks']} (selectivity {F['selectivity']:.2%}); post-filter at fetch_k={F['fetch_k']} came back "
            f"short for {F['post_short']}/{F['n']} queries (empty {F['post_empty']}); pre-filter short {F['pre_short']}/{F['n']}",
            "filter before scoring (mask) or raise fetch_k; expected passers ≈ selectivity × fetch_k")
    else:
        add("V9", "Filters do not starve results", ASK, "no filter given (use --filter)", "run with the filter your app uses")
    An = res["ann_res"]
    if An and "rows" in An:
        best = {}
        for r in An["rows"]:
            best.setdefault(r["index"], []).append(r)
        defaults = [rs[0] for rs in best.values()]
        low = [r for r in defaults if r["recall"] < An["target"]]
        add("V10", "ANN recall is measured against exact search", BAD if low else OK,
            "; ".join(f"{r['index']} {r['knob']}: recall@{k} {r['recall']:.3f}" for r in An["rows"])
            + f" (target {An['target']:g}; first value of each index = the library default)",
            "measure recall@k vs exact on real queries; re-check after bulk inserts or deletes")
    elif An:
        add("V10", "ANN recall is measured against exact search", ASK, An["error"], "install faiss-cpu in the optional ann group")
    else:
        add("V10", "ANN recall is measured against exact search", ASK, "not run (use --ann)", "only needed if you use an ANN index")
    M = res["measuring"]
    nl = res["n_labelled"]
    if nl:
        add("V11", "The right chunk is found (labelled questions)", ASK if nl < MIN_LABELLED else (OK if M["hitk"] >= 0.8 * nl else BAD),
            f"Hit@{k} {M['hitk']}/{nl}, Hit@1 {M['hit1']}/{nl}, MRR@10 {M['mrr']:.3f}" + (f"; fewer than {MIN_LABELLED} shows a mechanism, not a result" if nl < MIN_LABELLED else ""),
            "Hit@k and MRR on questions with a known right chunk")
    else:
        add("V11", "The right chunk is found (labelled questions)", ASK, "no labelled questions (add an expect text)", "label at least 10 questions")
    add("V12", "Your real store's defaults are written down", ASK,
        "a tool cannot read them for you: metric (and score direction), k, filter order (pre or post, fetch_k), tie order, ANN knobs (efSearch / nprobe)",
        "read your store's docs or source once and put every value in your config")
    return out


def recommend(res):
    text = _recommend(res)
    if {x["id"]: x["verdict"] for x in res["checklist"]}["V9"] == BAD and not text.startswith(("Fix first", "Too little")):
        text += " Also: your filter starves post-filtered results (V9); filter before scoring, or raise fetch_k."
    return text


def _recommend(res):
    c = {x["id"]: x["verdict"] for x in res["checklist"]}
    sp = res["speed"]
    if c["V1"] == BAD or c["V3"] == BAD or c["V4"] == BAD:
        return "Fix first: " + ", ".join(x for x in ("V1", "V3", "V4") if c[x] == BAD) + " failed. Speed does not matter while the results are wrong."
    if res["n_questions"] < MIN_QUESTIONS:
        return f"Too little data: give at least {MIN_QUESTIONS} real questions (better 10 or more with an expect text)."
    time_ok = sp["proj_p95"] <= sp["budget_ms"]
    thru_ok = sp["load"] <= 0.7
    mem_ok = c["V8"] == OK
    if time_ok and thru_ok and mem_ok:
        tail = " Keep the tie rule and the filter order written in your config." if c["V5"] != OK or c["V9"] == BAD else ""
        return f"Exact search is enough: projected p95 {sp['proj_p95']:.2f} ms at N={sp['grow']:,} is under your {sp['budget_ms']:g} ms budget.{tail}"
    if time_ok and mem_ok and not thru_ok:
        return (f"Exact + batching: one query fits the budget, but {sp['qps']:g} queries/s would keep about {sp['load']:.1f} cores busy; "
                f"batched it costs about {sp['proj_batch']:.2f} ms per query.")
    An = res["ann_res"]
    msg = (f"ANN (HNSW) is justified: exact search is projected at p95 {sp['proj_p95']:.1f} ms (budget {sp['budget_ms']:g} ms)"
           + ("" if mem_ok else f" and needs {sp['bytes_grow'] / 1e9:.1f} GB as float32") + ". ")
    if An and "rows" in An:
        ok = [r for r in An["rows"] if r["recall"] >= An["target"]]
        msg += (f"Here, {ok[0]['index']} {ok[0]['knob']} reached recall@{res['settings']['k']} {ok[0]['recall']:.3f}. " if ok else
                "No tested setting reached the recall target here: raise efSearch or nprobe and measure again. ")
    return msg + f"Ship it with a recall@k report against exact search (target ≥ {res['settings']['recall_target']:g}) and re-check after bulk changes."


# ---------------------------------------------------------------------------------------------------------------- report
def _r(x):
    return "-" if x is None else str(x)


def render_report(res):
    st, sp, T, k = res["settings"], res["speed"], res["ties"], res["settings"]["k"]
    cl = " ".join(f"{x['id']} {x['verdict']}" for x in res["checklist"])
    out = ["# Vector search check", "",
           "**What this is:** an automatic check of exact vector search on these documents: correctness, ties, filters, speed and memory, measured here.",
           "**What this is not:** an evaluation of retrieval quality, or a benchmark of a production store. Timings are for this machine only.", "",
           f"**Recommendation:** {res['recommendation']} (section 8). Checklist: {cl}.", "",
           f"Settings: model `{st['model']}` · chunker `{st['chunker']}` ({st['chunk_size']} characters, overlap {st['overlap']}) · k {k}"
           f" · budget {st['budget_ms']:g} ms · {st['qps']:g} queries/s · expected size {st['grow']:,}"
           + (f" · filter `{st['filter']}` (fetch_k {st['fetch_k']})" if st["filter"] else "") + (" · ANN" if st["ann"] else "")
           + " · " + ", ".join(f"{p} {v}" for p, v in st["versions"].items() if v) + ". No API call.",
           "Documents: " + "; ".join(f"`{x['name']}` ({x['pages']} page(s), {x['chars']:,} characters)" for x in res["docs"]) + ".",
           f"Queries: {res['n_questions']} of yours + {res['n_heads']} chunk heads (the first 200 characters of sampled chunks), used for ties, timing, filters and ANN.", "",
           "## 1 Collection", "",
           f"- {res['n_chunks']} chunks × {res['dim']} numbers; one question gives **{res['n_chunks']} scores**, one per chunk.",
           f"- Vector lengths as returned: {res['norm_min']:.6f} to {res['norm_max']:.6f}; scores below use normalised vectors (dot = cosine).",
           f"- Index memory (float32): {res['n_chunks']} × {res['dim']} × 4 = {sp['bytes_now']:,} bytes.",
           f"- Alignment: {res['checklist'][2]['evidence']}.", "",
           "## 2 Speed and memory (this machine)", "",
           "| Measurement | p50 | p95 |", "|---|---|---|",
           f"| Your index, N={res['n_chunks']:,} (exact, one query at a time) | {sp['p50'] * 1e3:.1f} µs | {sp['p95'] * 1e3:.1f} µs |",
           f"| Synthetic random unit vectors, N={sp['n_syn']:,}, d={res['dim']} | {sp['syn_p50']:.3f} ms | {sp['syn_p95']:.3f} ms |",
           f"| Projected at N={sp['grow']:,} (linear in N) | {sp['proj_p50']:.3f} ms | {sp['proj_p95']:.3f} ms |",
           f"| Projected, batches of 100 queries | {sp['proj_batch']:.3f} ms per query | |", "",
           f"Largest N within a {sp['budget_ms']:g} ms p50 budget here: about **{sp['n_max']:,.0f}** vectors of {res['dim']} numbers. "
           f"Memory at N={sp['grow']:,}: float32 {sp['bytes_grow'] / 1e9:.3f} GB, int8 {sp['int8_grow'] / 1e9:.3f} GB. "
           f"At {sp['qps']:g} queries/s one at a time, searching keeps about {sp['load']:.2f} of a core busy. "
           "Percentiles are nearest-rank over 200 timed queries, warm-up excluded.", "",
           "## 3 Ties and duplicates", "",
           f"- Tie-aware top_k equals a pure-Python full sort for {T['agree']}/{T['n_queries']} queries.",
           f"- Gap between rank {k} and rank {k + 1}: " + (f"min {min(T['gaps']):.2e}, median {float(np.median(T['gaps'])):.4f}; near-ties (< {NEAR_TIE:g}) {T['near_ties']}." if T["gaps"] else "fewer chunks than k."),
           f"- Identical chunks: {len(T['exact_dups'])} group(s); near-duplicate pairs (cosine > {DUP}): {len(T['near_dups'])}"
           + ("" if not T["near_dups"] else ", e.g. " + ", ".join(f"{res['chunks'][a]['id']}–{res['chunks'][b]['id']} {c:.4f}" for a, b, c in T["near_dups"][:5])) + ".", ""]
    F = res["filter"]
    out += ["## 4 Filters", ""]
    if F:
        out += [f"`{F['expr']}` keeps {F['kept']} of {res['n_chunks']} chunks (selectivity {F['selectivity']:.2%}).", "",
                "| Strategy | Short of k | Empty |", "|---|---|---|",
                f"| Pre-filter (excluded chunks scored −∞, then top {k}) | {F['pre_short']}/{F['n']} | 0 |",
                f"| Post-filter (top {F['fetch_k']}, then filter, keep {k}) | {F['post_short']}/{F['n']} | {F['post_empty']}/{F['n']} |", "",
                f"Expected passers among the top {F['fetch_k']}: selectivity × fetch_k = {F['expected']:.2f}; observed mean {F['mean_pass']:.2f} "
                "(higher when the filter matches what the queries are about).", ""]
    else:
        out += ["No filter given (use --filter).", ""]
    An = res["ann_res"]
    out += ["## 5 ANN (approximate search)", ""]
    if An and "rows" in An:
        out += [f"faiss {An['faiss']}, one thread, inner product on unit vectors. Recall@{k} = share of the exact top {k} that the index also returned, "
                f"averaged over {An['n_queries']} queries. This is **not** retrieval quality (section 6 is).", "",
                f"| Index | Knob | Recall@{k} | Worst query | Queries with a miss | p50 | p95 | Build | Bytes |", "|---|---|---|---|---|---|---|---|---|"]
        for r in An["rows"]:
            out.append(f"| {r['index']} | {r['knob']} | {r['recall']:.3f} | {r['min_recall']:.2f} | {r['missed']} | {r['p50']:.3f} ms | {r['p95']:.3f} ms | {r['build_s']:.2f} s | {r['bytes']:,} |")
        out += ["", f"Flat (exact) index bytes: {An['flat_bytes']:,}. With few vectors ANN has nothing to gain; its numbers here only show the mechanism.", ""]
    elif An:
        out += [An["error"], ""]
    else:
        out += ["Not run (use --ann; needs the optional `ann` group).", ""]
    rows = res["rows"]
    out += ["## 6 Per question", ""]
    if not rows:
        out += ["No questions given (use --questions).", ""]
    else:
        out += [f"| Question | Top {k} (score) | Gap rank {k}–{k + 1} | Right chunk | Rank |", "|---|---|---|---|---|"]
        for r in rows:
            top = " · ".join(f"{res['chunks'][i]['id']}{'' if res['chunks'][i]['page'] is None else ' p.' + str(res['chunks'][i]['page'])} {sc:.3f}" for i, sc in r["top"])
            right = ", ".join(res["chunks"][i]["id"] for i in r["targets"]) if r["targets"] else ("**expect text not found**" if r["missing_target"] else "-")
            out.append(f"| {r['id']}: {r['q'][:70]} | {top} | {'-' if r['gap'] is None else f'{r['gap']:.4f}'} | {right} | {_r(r['rank'])} |")
        M = res["measuring"]
        if M:
            out += ["", f"{res['n_labelled']} labelled question(s): Hit@1 {M['hit1']}, Hit@{k} {M['hitk']}, MRR@10 {M['mrr']:.3f} (a rank above 10 counts 0)."]
        out.append("")
    out += ["## 7 Checklist", "", "| Check | Verdict | Evidence | How to check |", "|---|---|---|---|"]
    for x in res["checklist"]:
        out.append(f"| {x['id']} {x['title']} | {x['verdict']} | {x['evidence']} | {x['how']} |")
    out += ["", "✓ fine · ✗ problem found · ? check by hand.", "", "## 8 Recommendation", "", res["recommendation"], "",
            "Lesson: `study/lessons/P5_vector_search.html`. This report is a mechanism check on your data, not an evaluation result."]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description="Is exact vector search enough for my documents, and is my store set up safely? Writes a Markdown report.")
    ap.add_argument("--docs", nargs="+", required=True, help="files or folders (.pdf, .txt, .md)")
    ap.add_argument("--questions", help=".txt (one per line) or .jsonl ({\"q\", \"expect\", \"type\", \"id\"})")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="a local sentence-transformers model")
    ap.add_argument("--chunker", choices=["v0", "windows"], default="v0")
    ap.add_argument("--chunk-size", type=int, default=1000)
    ap.add_argument("--overlap", type=int, default=200)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--budget-ms", type=float, default=10.0, help="latency budget for one search (ms)")
    ap.add_argument("--qps", type=float, default=1.0, help="queries per second you expect")
    ap.add_argument("--grow", type=int, help="the corpus size (number of chunks) to project to")
    ap.add_argument("--filter", help="page>=N, page<=N, page==N, page!=N or doc==<file name>")
    ap.add_argument("--fetch-k", type=int, default=20, help="candidates a post-filter looks at (LangChain FAISS default 20)")
    ap.add_argument("--ann", action="store_true", help="also measure faiss HNSW and IVF recall (needs the ann group)")
    ap.add_argument("--recall-target", type=float, default=ANN_RECALL_TARGET)
    ap.add_argument("--manifest", help="JSON of an existing index with a model_id (check V2)")
    ap.add_argument("--vectors", help="your saved vectors (.npy) to check alignment (V3); needs --meta")
    ap.add_argument("--meta", help="your saved metadata (.jsonl, one line per row, with \"text\")")
    ap.add_argument("--provider", choices=["local", "cohere"], default="local")
    ap.add_argument("--report", help="write the Markdown report here (default: print it)")
    a = ap.parse_args(argv)
    if a.provider == "cohere":
        print("--provider cohere is not available yet: it needs the course's study/llmops/ cache (record once, replay offline), "
              "which is not built. Never send private or book text to an API.", file=sys.stderr)
        return 2
    if bool(a.vectors) != bool(a.meta):
        ap.error("--vectors and --meta go together")
    res = run_check(a.docs, a.questions, model=a.model, chunk_size=a.chunk_size, overlap=a.overlap, chunker=a.chunker, k=a.k,
                    budget_ms=a.budget_ms, qps=a.qps, grow=a.grow, filt=a.filter, fetch_k=a.fetch_k, ann=a.ann,
                    recall_target=a.recall_target, manifest=a.manifest, vectors=a.vectors, meta=a.meta)
    text = render_report(res)
    if a.report:
        Path(a.report).write_text(text, encoding="utf-8")
        print(f"report written: {a.report} ({res['recommendation']})")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
