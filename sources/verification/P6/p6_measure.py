"""P6 (retrieval evaluation basics) measurements: every number in concepts/P6_ir_metrics.md comes from this run.

Toy data only (p6_toy.py). No API calls, no .env, no network. Pure Python; scikit-learn's ndcg_score
(already installed in the project env as a dependency of sentence-transformers) is used ONLY as an
independent cross-check of nDCG.

Run from rag_learning/:
    uv run python sources/verification/P6/p6_measure.py
Saved output: sources/verification/P6/out_p6_measure.txt  (sections S1..S11 for P6_FACTS.md)
"""
import importlib.metadata as md
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p6_toy as T  # noqa: E402
from p6_metrics import (average_precision, ce_at_k_chunks, dcg_at_k, hit_at_k, idcg_at_k,  # noqa: E402
                        mean_reciprocal_rank, ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank)


def head(title):
    print(f"\n=== {title}")


def f4(x):
    return f"{x:.4f}"


def row(ranking, qrels, k, gain="exp"):
    return (f"P@{k}={f4(precision_at_k(ranking, qrels, k))} R@{k}={f4(recall_at_k(ranking, qrels, k))} "
            f"Hit@{k}={hit_at_k(ranking, qrels, k)} RR@{k}={f4(reciprocal_rank(ranking, qrels, k))} "
            f"nDCG@{k}={f4(ndcg_at_k(ranking, qrels, k, gain))}")


# ---------------------------------------------------------------- S1
head("S1 environment")
print("python", sys.version.split()[0], "| numpy", md.version("numpy"), "| scikit-learn", md.version("scikit-learn"))

# ---------------------------------------------------------------- S2
head("S2 toy data (made up)")
for q in T.QUERIES:
    print(f"{q}: {T.QUERIES[q]!r}")
    print(f"   qrels {T.QRELS[q]}  (all other chunks grade 0)")
    print(f"   ranking {T.RANKINGS[q]}")
    pos = {d: i for i, d in enumerate(T.RANKINGS[q], start=1)}
    print("   relevant at ranks:", {d: pos[d] for d in T.QRELS[q]})

# ---------------------------------------------------------------- S3
head("S3 discount table 1/log2(i+1) and gains")
for i in range(1, 11):
    print(f"rank {i:2d}: log2(i+1)={math.log2(i + 1):.4f}  1/log2(i+1)={1 / math.log2(i + 1):.4f}")
print("gain exp (2^g-1): g=0 -> 0, g=1 -> 1, g=2 -> 3 | gain linear: g=0 -> 0, g=1 -> 1, g=2 -> 2")

# ---------------------------------------------------------------- S4
head("S4 Q1 at k = 5, every metric (the Part F worked example)")
r, q = T.RANKINGS["Q1"], T.QRELS["Q1"]
print(row(r, q, 5))
print(f"Hit@1={hit_at_k(r, q, 1)}  P@1={f4(precision_at_k(r, q, 1))}")
print(f"DCG@5 (exp)={f4(dcg_at_k(r, q, 5))}  IDCG@5 (exp)={f4(idcg_at_k(q, 5))}")
print(f"  DCG terms: c3 at rank 2 -> 3/log2(3)={f4(3 / math.log2(3))}; c7 at rank 4 -> 1/log2(5)={f4(1 / math.log2(5))}")
print(f"  IDCG terms: grades [2,1,1] -> 3/1 + 1/log2(3) + 1/log2(4) = 3 + {f4(1 / math.log2(3))} + {f4(1 / math.log2(4))}")
for qq in ("Q2", "Q3"):
    print(qq, row(T.RANKINGS[qq], T.QRELS[qq], 5))
print(f"Q3 DCG@5={f4(dcg_at_k(T.RANKINGS['Q3'], T.QRELS['Q3'], 5))} IDCG@5={f4(idcg_at_k(T.QRELS['Q3'], 5))}")

# ---------------------------------------------------------------- S5
head("S5 k sweep for Q1 (the CR-08 'k doubles' probe uses k = 5 -> 10)")
for k in range(1, 11):
    print(f"k={k:2d} " + row(r, q, k))
print("nDCG@k can fall as k grows (QF: a relevant at rank 1, b relevant but never retrieved):")
for k in (1, 2, 5):
    print(f"  QF k={k}: DCG={f4(dcg_at_k(T.QF_RANK, T.QF, k))} IDCG={f4(idcg_at_k(T.QF, k))} "
          f"nDCG={f4(ndcg_at_k(T.QF_RANK, T.QF, k))}")

# ---------------------------------------------------------------- S6
head("S6 MRR over Q1-Q3 (cut-off k = 10) and the '1 / mean rank' trap")
rrs = {qq: reciprocal_rank(T.RANKINGS[qq], T.QRELS[qq], 10) for qq in T.QUERIES}
print("RR per query:", {qq: f4(v) for qq, v in rrs.items()})
print("MRR@10 =", f4(mean_reciprocal_rank(T.RANKINGS, T.QRELS, 10)))
first = {qq: next(i for i, d in enumerate(T.RANKINGS[qq], 1) if T.QRELS[qq].get(d, 0) >= 1) for qq in T.QUERIES}
mean_rank = sum(first.values()) / len(first)
print("first relevant ranks:", first, "| mean rank =", f4(mean_rank), "| 1/mean rank =", f4(1 / mean_rank), "(NOT the MRR)")
print("MRR@3 =", f4(mean_reciprocal_rank(T.RANKINGS, T.QRELS, 3)), "(Q3's first hit at rank 4 is cut off)")

# ---------------------------------------------------------------- S7
head("S7 nDCG conventions and a cross-check")
print(f"Q1 nDCG@5 exp gain = {f4(ndcg_at_k(r, q, 5, 'exp'))} | linear gain = {f4(ndcg_at_k(r, q, 5, 'linear'))}")
print(f"Q1 DCG@5 linear = {f4(dcg_at_k(r, q, 5, 'linear'))} IDCG@5 linear = {f4(idcg_at_k(q, 5, 'linear'))}")
q_bin = {d: 1 for d in q}
print(f"Q1 binary (all grades -> 1): exp = {f4(ndcg_at_k(r, q_bin, 5, 'exp'))} linear = {f4(ndcg_at_k(r, q_bin, 5, 'linear'))}")
# J2 bug: IDCG computed from the retrieved list only
for name, rk in (("Q1 ranking", r), ("J2 ranking (only c7 found)", T.J2_RANK)):
    right = ndcg_at_k(rk, q, 5)
    retrieved_only = {d: g for d, g in q.items() if d in rk[:5]}
    wrong = ndcg_at_k(rk, retrieved_only, 5)
    print(f"{name}: nDCG@5 correct = {f4(right)} | IDCG from retrieved only (bug) = {f4(wrong)}")
try:
    from sklearn.metrics import ndcg_score

    def sk(ranking, qrels, k, gain):
        docs = list(dict.fromkeys(list(ranking) + list(qrels)))
        n = len(docs)
        score = [n - ranking.index(d) if d in ranking else -1 - i for i, d in enumerate(docs)]
        true = [(2 ** qrels.get(d, 0) - 1) if gain == "exp" else qrels.get(d, 0) for d in docs]
        return float(ndcg_score([true], [score], k=k))

    cases = [("Q1", r, q), ("Q2", T.RANKINGS["Q2"], T.QRELS["Q2"]), ("Q3", T.RANKINGS["Q3"], T.QRELS["Q3"]),
             ("QD_A", T.QD_A, T.QD), ("QD_B", T.QD_B, T.QD), ("QG_A", T.QG_A, T.QG), ("QG_B", T.QG_B, T.QG),
             ("QF", T.QF_RANK, T.QF), ("T06 graded", T.T06_RANK, T.T06_QRELS_GRADED), ("J2", T.J2_RANK, q)]
    worst, n_cmp, skipped = 0.0, 0, []
    for name, rk, qr in cases:
        for k in (1, 3, 5, 10):
            for gain in ("exp", "linear"):
                ours, theirs = ndcg_at_k(rk, qr, k, gain), sk(rk, qr, k, gain)
                if k <= len(rk):
                    n_cmp += 1
                    worst = max(worst, abs(ours - theirs))
                elif abs(ours - theirs) > 1e-12:
                    skipped.append(f"{name} k={k} {gain}: ours {f4(ours)} sklearn {f4(theirs)}")
    print(f"sklearn.metrics.ndcg_score cross-check (k <= length of the ranking): {n_cmp} comparisons "
          f"over {len(cases)} rankings, k in (1,3,5,10), 2 gains; max |ours - sklearn| = {worst:.2e}")
    print("k > length of the ranking: sklearn ranks every doc it is given, so relevant docs that were never "
          "retrieved still earn gain after the list. Not comparable (a convention difference):")
    for s in skipped:
        print("   ", s)
    print(f"  Q1 k=5: sklearn linear = {f4(sk(r, q, 5, 'linear'))}, sklearn on 2^g-1 gains = {f4(sk(r, q, 5, 'exp'))}")
except ImportError:
    print("sklearn not installed: cross-check skipped")

# ---------------------------------------------------------------- S8
head("S8 MRR and nDCG disagree")
for name, rk, qr in (("QD_A", T.QD_A, T.QD), ("QD_B", T.QD_B, T.QD)):
    print(f"{name} {rk}: " + row(rk, qr, 5))
print(f"QD IDCG@5 = {f4(idcg_at_k(T.QD, 5))}; QD_A DCG@5 = {f4(dcg_at_k(T.QD_A, T.QD, 5))}; "
      f"QD_B DCG@5 = {f4(dcg_at_k(T.QD_B, T.QD, 5))}")
for name, rk in (("QG_A", T.QG_A), ("QG_B", T.QG_B)):
    print(f"{name} {rk}: RR@5={f4(reciprocal_rank(rk, T.QG, 5))} nDCG@5 exp={f4(ndcg_at_k(rk, T.QG, 5))} "
          f"linear={f4(ndcg_at_k(rk, T.QG, 5, 'linear'))} DCG@5 exp={f4(dcg_at_k(rk, T.QG, 5))}")
print(f"QG IDCG@5 exp = {f4(idcg_at_k(T.QG, 5))}")
print("Same set, different order (QS, Part B):")
for name, rk in (("good", T.QS_GOOD), ("poor", T.QS_POOR)):
    print(f"  {name} {rk}: " + row(rk, T.QS, 5))

# ---------------------------------------------------------------- S9
head("S9 replicate the 06 §7.3 toy table")
rk, qb, qg = T.T06_RANK, T.T06_QRELS_BIN, T.T06_QRELS_GRADED
print("Hit@1/3/5 =", [hit_at_k(rk, qb, k) for k in (1, 3, 5)])
print("P@3 / P@5 =", f4(precision_at_k(rk, qb, 3)), "/", f4(precision_at_k(rk, qb, 5)))
print("CE@3 / CE@5 (chunk-level preview) =", ce_at_k_chunks(rk, T.T06_GROUPS, 3), "/", ce_at_k_chunks(rk, T.T06_GROUPS, 5))
print("RR =", f4(reciprocal_rank(rk, qb, 5)))
print("nDCG@5 binary =", f4(ndcg_at_k(rk, qb, 5)), "| DCG", f4(dcg_at_k(rk, qb, 5)), "IDCG", f4(idcg_at_k(qb, 5)))
print("nDCG@5 graded (exp) =", f4(ndcg_at_k(rk, qg, 5)), "| DCG", f4(dcg_at_k(rk, qg, 5)), "IDCG", f4(idcg_at_k(qg, 5)))
print("context precision@5 (AP over retrieved relevant) =", f4(average_precision(rk, qb, 5, "retrieved_relevant")))
print("MRR of RR (0.5, 1, 0) =", f4((0.5 + 1 + 0) / 3))

# ---------------------------------------------------------------- S10
head("S10 CE@k preview vs Recall@k (QE: overlapping chunks e2, e3 both hold G1; e6 holds G2)")
for k in (2, 3, 4):
    print(f"k={k}: Hit={hit_at_k(T.QE_RANK, T.QE, k)} P={f4(precision_at_k(T.QE_RANK, T.QE, k))} "
          f"Recall={f4(recall_at_k(T.QE_RANK, T.QE, k))} CE={ce_at_k_chunks(T.QE_RANK, T.QE_GROUPS, k)}")

# ---------------------------------------------------------------- S11
head("S11 book-wording checks: MAP denominators; Precision@k on a short list (J1)")
for k in (5, 10):
    print(f"Q1 AP@{k}: standard (/ all relevant) = {f4(average_precision(r, q, k, 'all_relevant'))} | "
          f"/ relevant retrieved = {f4(average_precision(r, q, k, 'retrieved_relevant'))}")
print(f"QD_A AP@5: standard = {f4(average_precision(T.QD_A, T.QD, 5, 'all_relevant'))} | "
      f"/ relevant retrieved = {f4(average_precision(T.QD_A, T.QD, 5, 'retrieved_relevant'))}")
print(f"J1 {T.J1_RANK} (3 returned), Q1 qrels: P@5 (divide by k) = {f4(precision_at_k(T.J1_RANK, q, 5))} | "
      f"divide by 3 returned = {f4(sum(1 for d in T.J1_RANK if q.get(d, 0) >= 1) / len(T.J1_RANK))}")
print("Book examples: 3/5 =", 3 / 5, "| 3/10 =", 3 / 10, "| 1/1 =", 1 / 1, "| 1/3 =", f4(1 / 3))
