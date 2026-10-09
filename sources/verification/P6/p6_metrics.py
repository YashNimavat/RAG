"""P6 reference implementation: retrieval metrics as pure functions (stdlib only).

This file is a SOLUTION for labs/P6_ir_metrics_lab.ipynb. Do not open it before an honest attempt
plus a hint from the tutor (05 CR-04).

Conventions (same names and formulas as 06 §7.3):
- ranking: list of chunk ids, best first, no duplicates.
- qrels: dict chunk_id -> grade (0 = not relevant, 1 = partial, 2 = sufficient). A chunk that is not in
  qrels counts as grade 0 ("unjudged = not relevant").
- Binary metrics (Precision, Recall, Hit, RR) count a chunk as relevant when its grade is >= 1.
- Precision@k divides by k, even when the ranking has fewer than k items.
- Recall@k divides by ALL relevant chunks in qrels (the index), not only the retrieved ones.
- RR@k is 1 / rank of the first relevant chunk within the top k, else 0. MRR is the mean of RR over queries.
- nDCG@k: DCG@k = sum_{i=1..k} gain(g_i) / log2(i + 1); gain = 2^g - 1 ("exp", the 06 default) or g ("linear").
  IDCG@k uses the ideal order of ALL relevant chunks in qrels, cut at k.
- Recall and nDCG are undefined when qrels has no relevant chunk (06 scores answerable items only): ValueError.
"""
import math


def _validate(ranking, k):
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError(f"k must be a positive int, got {k!r}")
    if len(set(ranking)) != len(ranking):
        raise ValueError("ranking contains duplicate ids")


def _n_relevant(qrels):
    return sum(1 for g in qrels.values() if g >= 1)


def precision_at_k(ranking, qrels, k):
    _validate(ranking, k)
    return sum(1 for d in ranking[:k] if qrels.get(d, 0) >= 1) / k


def recall_at_k(ranking, qrels, k):
    _validate(ranking, k)
    n_rel = _n_relevant(qrels)
    if n_rel == 0:
        raise ValueError("no relevant chunk in qrels: recall is undefined (score answerable items only)")
    return sum(1 for d in ranking[:k] if qrels.get(d, 0) >= 1) / n_rel


def hit_at_k(ranking, qrels, k):
    _validate(ranking, k)
    return int(any(qrels.get(d, 0) >= 1 for d in ranking[:k]))


def reciprocal_rank(ranking, qrels, k):
    _validate(ranking, k)
    for i, d in enumerate(ranking[:k], start=1):
        if qrels.get(d, 0) >= 1:
            return 1.0 / i
    return 0.0


def mean_reciprocal_rank(rankings, qrels_by_q, k):
    """Mean of RR@k over the queries in qrels_by_q (each must have a ranking)."""
    if not qrels_by_q:
        raise ValueError("no queries")
    return sum(reciprocal_rank(rankings[q], qrels_by_q[q], k) for q in qrels_by_q) / len(qrels_by_q)


def _gain(g, gain):
    if gain == "exp":
        return 2 ** g - 1
    if gain == "linear":
        return g
    raise ValueError(f"gain must be 'exp' or 'linear', got {gain!r}")


def dcg_at_k(ranking, qrels, k, gain="exp"):
    _validate(ranking, k)
    return sum(_gain(qrels.get(d, 0), gain) / math.log2(i + 1) for i, d in enumerate(ranking[:k], start=1))


def idcg_at_k(qrels, k, gain="exp"):
    ideal = sorted((g for g in qrels.values() if g >= 1), reverse=True)[:k]
    return sum(_gain(g, gain) / math.log2(i + 1) for i, g in enumerate(ideal, start=1))


def ndcg_at_k(ranking, qrels, k, gain="exp"):
    _validate(ranking, k)
    ideal = idcg_at_k(qrels, k, gain)
    if ideal == 0:
        raise ValueError("no relevant chunk in qrels: nDCG is undefined (score answerable items only)")
    return dcg_at_k(ranking, qrels, k, gain) / ideal


# ---------------------------------------------------------------- used only for book/06 comparisons
def average_precision(ranking, qrels, k, denominator="all_relevant"):
    """Sum of P@i at each relevant rank i <= k, divided by
    'all_relevant' (standard AP: every relevant chunk in qrels) or
    'retrieved_relevant' (relevant chunks found in the top k; the 06 'context precision@k' form)."""
    _validate(ranking, k)
    hits, total = 0, 0.0
    for i, d in enumerate(ranking[:k], start=1):
        if qrels.get(d, 0) >= 1:
            hits += 1
            total += hits / i
    denom = _n_relevant(qrels) if denominator == "all_relevant" else hits
    return total / denom if denom else 0.0


def ce_at_k_chunks(ranking, groups, k):
    """PREVIEW ONLY (simplified Complete-Evidence@k). groups: list of sets; each set lists the chunks that
    each, on their own, hold that group's whole evidence span. 1 iff every group has a chunk in the top k.
    The real CE@k works on character spans in document offsets (06 §7.2) and is taught in M2."""
    _validate(ranking, k)
    top = set(ranking[:k])
    return int(all(top & set(g) for g in groups))
