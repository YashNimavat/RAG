# R1 lab: REFERENCE SOLUTION (one block per task id). Coach-only: do not show it before an attempt plus a hint (CR-04).
# Used by r1_lab_test.py through r1_lab_runner.py. Each block replaces the learner/prediction cell with that task id.

# == t1_pred
my_prediction_first = "A"
my_prediction_last = "D"

# == t1
toy_fused = {"A": 1 / 61 + 1 / 62, "B": 1 / 62, "C": 1 / 63 + 1 / 61, "D": 1 / 63}
toy_order = ["A", "C", "B", "D"]

# == t2
def rrf(ranked_lists, k=60):
    fused = {}
    for lst in ranked_lists:
        for rank, d in enumerate(lst, 1):
            fused[d] = fused.get(d, 0.0) + 1.0 / (k + rank)
    return fused


def fused_order(scores):
    return sorted(scores, key=lambda d: (-scores[d], d))

# == t3
def minmax(scores):
    if not scores:
        return {}
    lo, hi = min(scores.values()), max(scores.values())
    if hi == lo:
        return {d: 1.0 for d in scores}
    return {d: (v - lo) / (hi - lo) for d, v in scores.items()}


def zscore3(scores):
    if not scores:
        return {}
    v = np.array(list(scores.values()), dtype=float)
    mu, sd = float(v.mean()), float(v.std())
    if sd == 0:
        return {d: 0.5 for d in scores}
    return {d: (x - (mu - 3 * sd)) / (6 * sd) for d, x in scores.items()}


def weighted_fusion(lists, weights, norm):
    normed = {name: norm(lst) for name, lst in lists.items()}
    ids = set().union(*[set(x) for x in normed.values()])
    return {d: sum(weights[name] * normed[name].get(d, 0.0) for name in normed) for d in ids}

# == t4a
def repo_style(all_docs, vector_results, bm25_scores, alpha=0.5, k=3):
    epsilon = 1e-8
    vector_scores = np.array([score for _, score in vector_results])
    vector_scores = 1 - (vector_scores - np.min(vector_scores)) / (np.max(vector_scores) - np.min(vector_scores) + epsilon)
    bm25_scores = (bm25_scores - np.min(bm25_scores)) / (np.max(bm25_scores) - np.min(bm25_scores) + epsilon)
    combined_scores = alpha * vector_scores + (1 - alpha) * bm25_scores
    sorted_indices = np.argsort(combined_scores)[::-1]
    return [all_docs[i] for i in sorted_indices[:k]]


def aligned_style(all_docs, vector_results, bm25_scores, alpha=0.5, k=3):
    corpus = ["d0", "d1", "d2"]                       # the corpus (index) order of bm25_scores
    dense = {d: -dist for d, dist in vector_results}  # smaller distance -> larger similarity
    bm25 = {d: float(bm25_scores[i]) for i, d in enumerate(corpus)}
    return fused_order(weighted_fusion({"dense": dense, "bm25": bm25}, {"dense": alpha, "bm25": 1 - alpha}, minmax))[:k]

# == t4b
def test_fusion_preserves_identity(fuse):
    dense = {"c1": 0.9, "c4": 0.7, "c2": 0.5, "c3": 0.2}      # dense order c1, c4, c2, c3 (not the id order)
    bm25 = {"c3": 8.0, "c2": 3.0, "c1": 1.0, "c4": 0.5}
    assert fuse(dense, bm25, 1.0)[:4] == ["c1", "c4", "c2", "c3"], "alpha=1 must give the dense order"
    assert fuse(dense, bm25, 0.0)[:4] == ["c3", "c2", "c1", "c4"], "alpha=0 must give the BM25 order"
    ren = {d: "z" + d for d in dense}                          # renaming ids must not change which docs win
    out = fuse({ren[d]: s for d, s in dense.items()}, {ren[d]: s for d, s in bm25.items()}, 0.5)
    assert out[:2] == [ren[d] for d in fuse(dense, bm25, 0.5)[:2]], "fusion must follow the documents, not their positions"
    assert set(fuse(dense, bm25, 0.5)) <= set(dense) | set(bm25), "every returned id must exist in the inputs"

# == t5_pred
my_prediction_bm25_better = 3
my_prediction_bm25_worse = 1

# == t5
bm25 = BM25Okapi([tok_norm(c["text"]) for c in chunks])


def dense_list(question, n):
    s = V @ embedder.embed_query(question)
    sc = {IDS[i]: float(s[i]) for i in range(len(IDS))}
    return {d: sc[d] for d in fused_order(sc)[:n]}


def bm25_list(question, n):
    s = bm25.get_scores(tok_norm(question))
    sc = {IDS[i]: float(s[i]) for i in range(len(IDS)) if s[i] > 0}
    return {d: sc[d] for d in fused_order(sc)[:n]}


rankings = {}
for s in SEEDS:
    q = s["question"]
    dl, bl = dense_list(q, N_LIST), bm25_list(q, N_LIST)
    rankings[s["qid"]] = {
        "dense": fused_order(dense_list(q, len(chunks))),
        "bm25": fused_order(bm25_list(q, len(chunks))),
        "rrf60": fused_order(rrf([fused_order(dl), fused_order(bl)], k=60)),
        "mm_0.5": fused_order(weighted_fusion({"dense": dl, "bm25": bl}, {"dense": 0.5, "bm25": 0.5}, minmax)),
    }
first_rel, hit_ce = {}, {}
for arm in ("dense", "bm25", "rrf60", "mm_0.5"):
    first_rel[arm] = {s["qid"]: next((r for r, d in enumerate(rankings[s["qid"]][arm], 1) if rel(d, s)), None)
                      for s in ANSWERABLE}
    hit_ce[arm] = [sum(any(rel(d, s) for d in rankings[s["qid"]][arm][:K]) for s in ANSWERABLE),
                   sum(ce(rankings[s["qid"]][arm][:K], s) for s in ANSWERABLE)]

# == t6
for qid in ("D-008", "D-006"):
    dl, bl = dense_list(QUESTION[qid], N_LIST), bm25_list(QUESTION[qid], N_LIST)
    f = rrf([fused_order(dl), fused_order(bl)])
    print(qid, [(chunks[ROW[d]]["page_segments"][0]["page"], round(f[d], 5)) for d in fused_order(f)[:6]])
dl, bl = dense_list(QUESTION["D-006"], N_LIST), bm25_list(QUESTION["D-006"], N_LIST)
_f6 = rrf([fused_order(dl), fused_order(bl)])
d006_top2 = [_f6[d] for d in fused_order(_f6)[:2]]
diagnosis = {
    "D-008": "Dense puts a carbon-pricing chunk on page 10 first and the Kigali chunk second, by 0.006. BM25 puts the "
             "Kigali chunk first by a wide margin, because kigali and amendment occur in one chunk only. Both fusions "
             "move it to rank 1. This is a retrieval ranking question; no answer is generated here.",
    "D-006": "BM25 puts a page-22 solar technology chunk first because it contains the rare word panels; the evidence "
             "chunk on page 8 never says lakes or panels. Min-max fusion follows BM25 and pushes the evidence to rank 2. "
             "RRF ties the two chunks exactly and the smaller chunk_id decides. A retrieval question, not generation.",
}

# == t7_pred
my_prediction_k0 = 3      # rank 1 dominates at k=0, so near-ties in the middle flip
my_prediction_w07 = 2

# == t7
n_changed_k0 = n_changed_w07 = 0
for s in SEEDS:
    dl, bl = dense_list(s["question"], N_LIST), bm25_list(s["question"], N_LIST)
    n_changed_k0 += fused_order(rrf([fused_order(dl), fused_order(bl)], k=0))[:K] != rankings[s["qid"]]["rrf60"][:K]
    w = fused_order(weighted_fusion({"dense": dl, "bm25": bl}, {"dense": 0.7, "bm25": 1 - 0.7}, minmax))[:K]
    n_changed_w07 += w != rankings[s["qid"]]["mm_0.5"][:K]

# == t8_pred
my_prediction_rescale = {"raw_sum": "changes", "mm": "x100 no, exp maybe", "rrf": "never"}

# == t8
def _top4(dl, bl, method):
    if method == "raw_sum":
        f = {d: dl.get(d, 0.0) + bl.get(d, 0.0) for d in set(dl) | set(bl)}
    elif method == "mm":
        f = weighted_fusion({"dense": dl, "bm25": bl}, {"dense": 0.5, "bm25": 0.5}, minmax)
    else:
        f = rrf([fused_order(dl), fused_order(bl)])
    return fused_order(f)[:K]


rescale_changes = {}
for method in ("raw_sum", "mm", "rrf"):
    for tname, tr in (("x100", lambda x: 100 * x), ("exp", lambda x: math.exp(10 * x))):
        n = 0
        for s in SEEDS:
            dl, bl = dense_list(s["question"], N_LIST), bm25_list(s["question"], N_LIST)
            n += _top4({d: tr(v) for d, v in dl.items()}, bl, method) != _top4(dl, bl, method)
        rescale_changes[f"{method}|{tname}"] = n

# == t9
my_fusion_decision = ("I would make RRF with k = 60 over the two top-50 lists the primary v2.0 arm, because it needs "
                      "no score normalisation and did not move when one scorer was rescaled. I would decide on CE@4 per "
                      "category on dev: exact-term and table/numeric must rise, and vocabulary-mismatch must not fall. "
                      "If weighted min-max fusion wins those buckets on dev, it becomes the champion instead. I would not "
                      "add BM25 at all for a corpus whose questions are all paraphrases with no identifiers.")
