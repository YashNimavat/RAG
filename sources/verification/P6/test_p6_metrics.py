"""Unit tests for p6_metrics.py: hand values (lesson Part F, derived on paper) must equal code values.

Run from rag_learning/:
    uv run pytest -q -p no:cacheprovider sources/verification/P6/test_p6_metrics.py
Saved output: sources/verification/P6/out_p6_tests.txt
"""
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p6_toy as T  # noqa: E402
from p6_metrics import (average_precision, ce_at_k_chunks, dcg_at_k, hit_at_k, idcg_at_k,  # noqa: E402
                        mean_reciprocal_rank, ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank)

R1, Q1 = T.RANKINGS["Q1"], T.QRELS["Q1"]
L2 = math.log2


# ---- hand values from Part F (Q1, k = 5): relevant c3 (grade 2) at rank 2, c7 (grade 1) at rank 4, c9 (grade 1) at rank 7
def test_q1_precision_hand():
    assert precision_at_k(R1, Q1, 5) == pytest.approx(2 / 5)


def test_q1_recall_hand():
    assert recall_at_k(R1, Q1, 5) == pytest.approx(2 / 3)


def test_q1_hit_hand():
    assert hit_at_k(R1, Q1, 1) == 0 and hit_at_k(R1, Q1, 5) == 1


def test_q1_rr_hand():
    assert reciprocal_rank(R1, Q1, 5) == pytest.approx(1 / 2)


def test_q1_ndcg_hand():
    dcg = 3 / L2(3) + 1 / L2(5)
    idcg = 3 / L2(2) + 1 / L2(3) + 1 / L2(4)
    assert dcg_at_k(R1, Q1, 5) == pytest.approx(dcg)
    assert idcg_at_k(Q1, 5) == pytest.approx(idcg)
    assert ndcg_at_k(R1, Q1, 5) == pytest.approx(dcg / idcg)


def test_mrr_hand_and_not_one_over_mean_rank():
    assert mean_reciprocal_rank(T.RANKINGS, T.QRELS, 10) == pytest.approx((1 / 2 + 1 / 1 + 1 / 4) / 3)
    assert mean_reciprocal_rank(T.RANKINGS, T.QRELS, 10) != pytest.approx(1 / ((2 + 1 + 4) / 3))


# ---- conventions and edge cases
def test_precision_divides_by_k_on_short_list():
    assert precision_at_k(T.J1_RANK, Q1, 5) == pytest.approx(2 / 5)


def test_rr_cutoff():
    assert reciprocal_rank(T.RANKINGS["Q3"], T.QRELS["Q3"], 3) == 0.0
    assert reciprocal_rank(T.RANKINGS["Q3"], T.QRELS["Q3"], 4) == pytest.approx(0.25)


def test_partial_grade_counts_as_relevant_for_binary_metrics():
    assert reciprocal_rank(T.QG_A, T.QG, 5) == 1.0


def test_unjudged_is_not_relevant():
    assert precision_at_k(["zzz", "c3"], Q1, 2) == pytest.approx(0.5)


def test_perfect_ranking_ndcg_is_one():
    assert ndcg_at_k(["c3", "c7", "c9", "c1"], Q1, 4) == pytest.approx(1.0)
    assert ndcg_at_k(["c3", "c9", "c7"], Q1, 3) == pytest.approx(1.0)   # ties between equal grades


def test_idcg_uses_all_relevant_not_retrieved():
    assert ndcg_at_k(T.J2_RANK, Q1, 5) == pytest.approx(1 / (3 + 1 / L2(3) + 1 / L2(4)))


def test_gain_conventions_differ_on_graded_but_not_binary():
    assert ndcg_at_k(R1, Q1, 5, "exp") != pytest.approx(ndcg_at_k(R1, Q1, 5, "linear"))
    qb = {d: 1 for d in Q1}
    assert ndcg_at_k(R1, qb, 5, "exp") == pytest.approx(ndcg_at_k(R1, qb, 5, "linear"))


def test_ndcg_can_fall_as_k_grows():
    assert ndcg_at_k(T.QF_RANK, T.QF, 1) == 1.0
    assert ndcg_at_k(T.QF_RANK, T.QF, 2) < 1.0


def test_recall_and_hit_never_decrease_with_k():
    for q in T.QUERIES:
        r, qr = T.RANKINGS[q], T.QRELS[q]
        rec = [recall_at_k(r, qr, k) for k in range(1, 11)]
        hit = [hit_at_k(r, qr, k) for k in range(1, 11)]
        assert rec == sorted(rec) and hit == sorted(hit)


def test_mrr_and_ndcg_disagree_on_constructed_pair():
    assert reciprocal_rank(T.QD_A, T.QD, 5) > reciprocal_rank(T.QD_B, T.QD, 5)
    assert ndcg_at_k(T.QD_A, T.QD, 5) < ndcg_at_k(T.QD_B, T.QD, 5)


def test_06_toy_table():
    rk = T.T06_RANK
    assert [hit_at_k(rk, T.T06_QRELS_BIN, k) for k in (1, 3, 5)] == [0, 1, 1]
    assert round(ndcg_at_k(rk, T.T06_QRELS_BIN, 5), 3) == 0.651
    assert round(ndcg_at_k(rk, T.T06_QRELS_GRADED, 5), 3) == 0.640
    assert average_precision(rk, T.T06_QRELS_BIN, 5, "retrieved_relevant") == pytest.approx(0.5)
    assert [ce_at_k_chunks(rk, T.T06_GROUPS, k) for k in (3, 5)] == [0, 1]


@pytest.mark.parametrize("fn", [precision_at_k, recall_at_k, hit_at_k, reciprocal_rank, ndcg_at_k])
def test_bad_k_and_duplicates_raise(fn):
    for bad_k in (0, -1, 2.0, True):
        with pytest.raises(ValueError):
            fn(R1, Q1, bad_k)
    with pytest.raises(ValueError):
        fn(["c3", "c3"], Q1, 2)


def test_undefined_without_relevant():
    with pytest.raises(ValueError):
        recall_at_k(R1, {}, 5)
    with pytest.raises(ValueError):
        ndcg_at_k(R1, {"c1": 0}, 5)
