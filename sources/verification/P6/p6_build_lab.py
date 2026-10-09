"""Build labs/P6_ir_metrics_lab.ipynb (blank-file-first scaffold, no solution code).

The CHECK cells compare sha256 fingerprints computed here from the reference implementation
(p6_metrics.py) on the toy data (p6_toy.py), so expected answers stay hidden in the notebook.
Run from rag_learning/:
    uv run python sources/verification/P6/p6_build_lab.py labs/P6_ir_metrics_lab.ipynb
Saved output: sources/verification/P6/out_p6_build_lab.txt (the fingerprints and the values behind them)
"""
import hashlib
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p6_toy as T  # noqa: E402
from p6_metrics import (hit_at_k, mean_reciprocal_rank, ndcg_at_k, precision_at_k,  # noqa: E402
                        recall_at_k, reciprocal_rank)

OUT = sys.argv[1]


def _fp(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:16]


def _r4(v):
    return round(float(v), 4)


R, Q = T.RANKINGS, T.QRELS
vals = {
    "P_sweep": [_r4(precision_at_k(R["Q1"], Q["Q1"], k)) for k in range(1, 11)],
    "R_sweep": [_r4(recall_at_k(R["Q1"], Q["Q1"], k)) for k in range(1, 11)],
    "H_sweep": [_r4(hit_at_k(R["Q1"], Q["Q1"], k)) for k in range(1, 11)],
    "P_short": _r4(precision_at_k(T.J1_RANK, Q["Q1"], 5)),
    "RR10": {q: _r4(reciprocal_rank(R[q], Q[q], 10)) for q in Q},
    "MRR10": _r4(mean_reciprocal_rank(R, Q, 10)),
    "MRR3": _r4(mean_reciprocal_rank(R, Q, 3)),
    "N_sweep": [_r4(ndcg_at_k(R["Q1"], Q["Q1"], k)) for k in range(1, 11)],
    "N_lin5": _r4(ndcg_at_k(R["Q1"], Q["Q1"], 5, "linear")),
    "N_q3": _r4(ndcg_at_k(R["Q3"], Q["Q3"], 5)),
    "N_j2": _r4(ndcg_at_k(T.J2_RANK, Q["Q1"], 5)),
    "HAND6": {"P@5": _r4(precision_at_k(R["Q1"], Q["Q1"], 5)), "R@5": _r4(recall_at_k(R["Q1"], Q["Q1"], 5)),
              "Hit@1": _r4(hit_at_k(R["Q1"], Q["Q1"], 1)), "Hit@5": _r4(hit_at_k(R["Q1"], Q["Q1"], 5)),
              "RR@5": _r4(reciprocal_rank(R["Q1"], Q["Q1"], 5)), "nDCG@5": _r4(ndcg_at_k(R["Q1"], Q["Q1"], 5))},
}


def _dir(a, b):
    return "up" if b > a + 1e-12 else "down" if b < a - 1e-12 else "same"


r1, q1 = R["Q1"], Q["Q1"]
vals["DIR"] = {
    "P": _dir(precision_at_k(r1, q1, 5), precision_at_k(r1, q1, 10)),
    "R": _dir(recall_at_k(r1, q1, 5), recall_at_k(r1, q1, 10)),
    "Hit": _dir(hit_at_k(r1, q1, 5), hit_at_k(r1, q1, 10)),
    "RR": _dir(reciprocal_rank(r1, q1, 5), reciprocal_rank(r1, q1, 10)),
    "nDCG": _dir(ndcg_at_k(r1, q1, 5), ndcg_at_k(r1, q1, 10)),
}


# Guard: no true value may sit within 1e-9 of a 4-decimal rounding boundary (fingerprints must be robust).
def _raw():
    out = []
    for k in range(1, 11):
        out += [precision_at_k(r1, q1, k), recall_at_k(r1, q1, k), ndcg_at_k(r1, q1, k)]
    out += [mean_reciprocal_rank(R, Q, 10), mean_reciprocal_rank(R, Q, 3), ndcg_at_k(r1, q1, 5, "linear"),
            ndcg_at_k(R["Q3"], Q["Q3"], 5), ndcg_at_k(T.J2_RANK, q1, 5)]
    return out


for v in _raw():
    frac = (v * 1e4) % 1
    assert abs(frac - 0.5) > 1e-6, f"value {v} is too close to a rounding boundary"

FP = {k: _fp(v) for k, v in vals.items()}
print("values behind the fingerprints:")
for k, v in vals.items():
    print(f"  {k:8s} {FP[k]}  {v}")

HAND_KEYS = ["P@5", "R@5", "Hit@1", "Hit@5", "RR@5", "nDCG@5"]
disc = "\n".join(f"| {i} | {1 / math.log2(i + 1):.4f} |" for i in range(1, 8))


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text, tag, task=None):
    meta = {"tags": [tag]}
    if task:
        meta["task"] = task
    return {"cell_type": "code", "execution_count": None, "metadata": meta, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


LEARNER = "# Your code here (blank-file first: write it yourself; no copying from sources/verification/P6/)."

cells = [
    md("""
# P6 lab: retrieval metrics by hand, then as tested functions

Lesson: [`concepts/P6_ir_metrics.md`](../concepts/P6_ir_metrics.md), Part H.1. Concept card: [02 P6](../02_RAG_MASTER_LEARNING_PLAN.md#p6).

**How this lab works (blank-file first).**
- Each task has a **task cell** (what to build), an **empty code cell** for you, and a **CHECK cell** (`# CHECK`, do not edit). Run the CHECK cell after your code. If it fails, read the message and fix your code.
- This notebook contains **no solution code**. Write every line yourself. The reference files in `sources/verification/P6/` are solutions: open them only after an honest attempt and a hint from the tutor (CR-04).
- Where a task says **Predict first**, fill the prediction cell **before** you write or run code.
- Pure Python is enough. No API calls. All data here is a **toy illustration** (made up).
- Kernel: the project **`.venv` (Python 3.12)**.
"""),
    md("""
## Setup (given)
Run this cell. It defines the toy data and `_fp`, a fingerprint that the CHECK cells use so the expected answers stay hidden.

- `QRELS[q]` maps a chunk id to a **grade**: 2 = sufficient, 1 = partial. A chunk that is not listed is grade 0 (not relevant).
- `RANKINGS[q]` is the toy retriever's output for query `q`, best first.
"""),
    code(f'''
import hashlib, json

def _fp(x):
    """Fingerprint of a value. The CHECK cells compare fingerprints, not visible answers."""
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:16]

def _r4(v):
    return round(float(v), 4)

QUERIES = {json.dumps(T.QUERIES, indent=4)}

QRELS = {json.dumps(T.QRELS, indent=4)}

RANKINGS = {{
    "Q1": {json.dumps(T.RANKINGS["Q1"])},
    "Q2": {json.dumps(T.RANKINGS["Q2"])},
    "Q3": {json.dumps(T.RANKINGS["Q3"])},
}}

for q in QUERIES:
    print(q, QUERIES[q], "| qrels", QRELS[q])
    print("   ranking", RANKINGS[q])
''', "given"),
    md(f"""
## Task 1: Q1 by hand (paper first, no code)

Use Q1 and **k = 5**. A chunk counts as relevant for P, R, Hit and RR when its grade is 1 or 2. For nDCG use gain = 2^grade − 1 and divide by log2(rank + 1). IDCG is the DCG of the best possible order of **all** of Q1's relevant chunks.

| rank i | 1 / log2(i + 1) |
|---|---|
{disc}

Write your six numbers in the next cell (3 decimals is enough), and your confidence: 1 = guessing, 2 = fairly sure, 3 = sure.
"""),
    code('''
hand = {"P@5": None, "R@5": None, "Hit@1": None, "Hit@5": None, "RR@5": None, "nDCG@5": None}
my_confidence = None   # 1, 2 or 3
''', "prediction", "T1"),
    code(f'''
# CHECK Task 1 (do not edit)
assert set(hand) == {set(HAND_KEYS)!r}, "keep the six keys"
assert all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in hand.values()), "every value must be a number between 0 and 1"
assert my_confidence in (1, 2, 3), "confidence must be 1, 2 or 3"
print("Task 1 recorded. These are graded in Task 6 against your own code, not here.")
''', "check"),
    md("""
## Task 2: Precision@k, Recall@k, Hit@k

Write three functions. Each takes `(ranking, qrels, k)`.
- `precision_at_k`: relevant chunks in the top k, divided by **k**.
- `recall_at_k`: relevant chunks in the top k, divided by the number of relevant chunks in `qrels`.
- `hit_at_k`: 1 if at least one relevant chunk is in the top k, else 0.

Rules for all your metric functions:
- relevant means grade ≥ 1; a chunk missing from `qrels` is grade 0;
- raise `ValueError` if `k` is not a positive `int`, or if `ranking` has a duplicate id;
- `recall_at_k` raises `ValueError` when `qrels` has no relevant chunk (recall is undefined then).
"""),
    code(LEARNER, "learner", "T2"),
    code(f'''
# CHECK Task 2 (do not edit)
R1, Q1 = RANKINGS["Q1"], QRELS["Q1"]
assert _fp([_r4(precision_at_k(R1, Q1, k)) for k in range(1, 11)]) == "{FP['P_sweep']}", \\
    f"precision_at_k for k = 1..10 is not right yet: {{[_r4(precision_at_k(R1, Q1, k)) for k in range(1, 11)]}}"
assert _fp([_r4(recall_at_k(R1, Q1, k)) for k in range(1, 11)]) == "{FP['R_sweep']}", \\
    "recall_at_k is not right yet. What is the denominator?"
assert _fp([_r4(hit_at_k(R1, Q1, k)) for k in range(1, 11)]) == "{FP['H_sweep']}", "hit_at_k is not right yet"
assert _fp(_r4(precision_at_k(["c3", "c5", "c7"], Q1, 5))) == "{FP['P_short']}", \\
    "a ranking with only 3 chunks, scored at k = 5: what do you divide by?"
for bad in (0, -2, 2.5):
    for f in (precision_at_k, recall_at_k, hit_at_k):
        try:
            f(R1, Q1, bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{{f.__name__}} must raise ValueError for k = {{bad!r}}")
for f in (precision_at_k, recall_at_k, hit_at_k):
    try:
        f(["c3", "c3"], Q1, 2)
    except ValueError:
        pass
    else:
        raise AssertionError(f"{{f.__name__}} must raise ValueError for a duplicate id")
try:
    recall_at_k(R1, {{}}, 5)
except ValueError:
    pass
else:
    raise AssertionError("recall_at_k must raise ValueError when qrels has no relevant chunk")
print("Task 2 OK")
''', "check"),
    md("""
## Task 3: reciprocal rank and MRR

- `reciprocal_rank(ranking, qrels, k)`: 1 / (rank of the first relevant chunk), counting ranks from 1; **0.0** if no relevant chunk is in the top k.
- `mean_reciprocal_rank(rankings, qrels_by_q, k)`: the mean of `reciprocal_rank` over the queries in `qrels_by_q`.

**Predict first.** In Q1, Q2 and Q3 the first relevant chunk sits at some rank. Without code, what is MRR with k = 10? Write it below.
"""),
    code('''
my_prediction_mrr10 = None   # your number, BEFORE you write the functions
''', "prediction", "T3"),
    code(LEARNER, "learner", "T3b"),
    code(f'''
# CHECK Task 3 (do not edit)
assert my_prediction_mrr10 is not None, "write your prediction first"
assert _fp({{q: _r4(reciprocal_rank(RANKINGS[q], QRELS[q], 10)) for q in QRELS}}) == "{FP['RR10']}", \\
    "reciprocal_rank is not right yet. Do ranks start at 1?"
assert _fp(_r4(mean_reciprocal_rank(RANKINGS, QRELS, 10))) == "{FP['MRR10']}", \\
    "mean_reciprocal_rank is not right yet. Is it the mean of the reciprocal ranks?"
assert _fp(_r4(mean_reciprocal_rank(RANKINGS, QRELS, 3))) == "{FP['MRR3']}", \\
    "with k = 3, a first hit at rank 4 must count as 0"
assert reciprocal_rank(["c5", "c8"], QRELS["Q1"], 2) == 0.0, "no relevant chunk in the top k gives 0.0"
print(f"Task 3 OK. MRR@10 = {{mean_reciprocal_rank(RANKINGS, QRELS, 10):.4f}}; you predicted {{my_prediction_mrr10}}")
''', "check"),
    md("""
## Task 4: DCG and nDCG with graded relevance

- `dcg_at_k(ranking, qrels, k, gain="exp")`: sum over ranks i = 1..k of gain(grade) / log2(i + 1).
- `ndcg_at_k(ranking, qrels, k, gain="exp")`: DCG@k divided by IDCG@k.
- `gain="exp"` means 2^grade − 1 (our course default, 06 §7.3). `gain="linear"` means the grade itself.
- IDCG@k: the DCG of the ideal order of **all** relevant chunks in `qrels`, cut at k.
- Raise `ValueError` if `qrels` has no relevant chunk, and for a bad `k` or duplicates (as in Task 2).
"""),
    code(LEARNER, "learner", "T4"),
    code(f'''
# CHECK Task 4 (do not edit)
R1, Q1 = RANKINGS["Q1"], QRELS["Q1"]
assert _fp([_r4(ndcg_at_k(R1, Q1, k)) for k in range(1, 11)]) == "{FP['N_sweep']}", \\
    f"ndcg_at_k (exp gain) for k = 1..10 is not right yet: {{[_r4(ndcg_at_k(R1, Q1, k)) for k in range(1, 11)]}}"
assert _fp(_r4(ndcg_at_k(R1, Q1, 5, gain="linear"))) == "{FP['N_lin5']}", "the linear-gain option is not right yet"
assert _fp(_r4(ndcg_at_k(RANKINGS["Q3"], QRELS["Q3"], 5))) == "{FP['N_q3']}", "Q3 is not right yet"
assert _fp(_r4(ndcg_at_k(["c7", "c5", "c8", "c1", "c2"], Q1, 5))) == "{FP['N_j2']}", \\
    "a ranking that finds only c7: is your IDCG built from ALL relevant chunks in qrels?"
assert abs(ndcg_at_k(["c3", "c7", "c9"], Q1, 3) - 1.0) < 1e-12, "a perfect ranking must give 1.0"
try:
    ndcg_at_k(R1, {{"c1": 0}}, 5)
except ValueError:
    pass
else:
    raise AssertionError("ndcg_at_k must raise ValueError when qrels has no relevant chunk")
try:   # independent cross-check: scikit-learn's ndcg_score uses LINEAR gain
    from sklearn.metrics import ndcg_score
    for q in QRELS:
        docs = RANKINGS[q]
        true = [[QRELS[q].get(d, 0) for d in docs]]
        score = [[len(docs) - i for i in range(len(docs))]]
        for k in (1, 3, 5, 10):
            assert abs(ndcg_score(true, score, k=k) - ndcg_at_k(docs, QRELS[q], k, gain="linear")) < 1e-9, \\
                f"your linear-gain nDCG disagrees with scikit-learn on {{q}} at k = {{k}}"
    print("Cross-check: your linear-gain nDCG equals sklearn.metrics.ndcg_score on Q1-Q3, k = 1, 3, 5, 10")
except ImportError:
    print("scikit-learn not available: cross-check skipped")
print("Task 4 OK")
''', "check"),
    md("""
## Task 5: unit tests that would catch real bugs

Write **at least 6** test functions named `test_...` in the next cell. Each one uses plain `assert` (or `pytest.raises`). Include:
- your Task 1 hand values for Q1 at k = 5 (corrected if needed);
- at least two edge cases (for example: a short ranking, the k cut-off, no relevant chunk, a perfect ranking).

The CHECK runs your tests on your functions (they must all pass). Then it runs them against **six deliberately broken versions** of your functions. Good tests catch (fail on) at least 4 of the 6.
"""),
    code(LEARNER, "learner", "T5"),
    code('''
# CHECK Task 5 (do not edit)
import inspect
_tests = {n: f for n, f in list(globals().items()) if n.startswith("test_") and callable(f)}
assert len(_tests) >= 6, f"write at least 6 test functions; found {len(_tests)}"

def _run_tests():
    failed = []
    for n, f in _tests.items():
        try:
            f()
        except Exception as e:   # an AssertionError or any error counts as a failed test
            failed.append(f"{n}: {type(e).__name__}")
    return failed

_bad = _run_tests()
assert not _bad, f"your own tests must pass on your functions first: {_bad}"

_orig = {n: globals()[n] for n in ("precision_at_k", "recall_at_k", "hit_at_k", "reciprocal_rank", "ndcg_at_k")}

def _m_prec(r, q, k):
    return _orig["precision_at_k"](r, q, k) * k / max(1, min(k, len(r)))

def _m_rec(r, q, k):
    return _orig["recall_at_k"](r, {d: g for d, g in q.items() if g >= 2}, k)

def _m_hit(r, q, k):
    return _orig["hit_at_k"](r, q, k - 1) if k > 1 else 0

def _m_rr(r, q, k):
    return _orig["reciprocal_rank"](r, q, max(k, len(r)))

def _m_idcg(r, q, k, gain="exp"):
    sub = {d: g for d, g in q.items() if d in r[:k]}
    return _orig["ndcg_at_k"](r, sub, k, gain) if any(g >= 1 for g in sub.values()) else 0.0

def _m_lin(r, q, k, gain="exp"):
    return _orig["ndcg_at_k"](r, q, k, "linear")

_MUTANTS = [
    ("precision divides by the number of chunks returned, not by k", "precision_at_k", _m_prec),
    ("recall ignores partial (grade 1) chunks", "recall_at_k", _m_rec),
    ("hit looks at one chunk too few", "hit_at_k", _m_hit),
    ("reciprocal rank ignores the cut-off k", "reciprocal_rank", _m_rr),
    ("nDCG builds IDCG from the retrieved chunks only", "ndcg_at_k", _m_idcg),
    ("nDCG uses linear gain instead of 2^g - 1", "ndcg_at_k", _m_lin),
]
_caught = []
try:
    for label, name, fake in _MUTANTS:
        globals()[name] = fake
        try:
            if _run_tests():
                _caught.append(label)
        finally:
            globals()[name] = _orig[name]
finally:
    globals().update(_orig)
for label, _, _ in _MUTANTS:
    print(("caught   " if label in _caught else "MISSED   ") + label)
assert len(_caught) >= 4, f"your tests caught {len(_caught)} of 6 broken versions; add tests for the MISSED ones"
print(f"Task 5 OK: {len(_tests)} tests, all pass; they catch {len(_caught)} of 6 broken versions")
''', "check"),
    md("""
## Task 6: hand values vs code values

The CHECK compares your Task 1 hand values with your own (now tested) code. **Do not edit Task 1.** If a hand value was wrong, put the corrected value in `hand_corrected` and say in one line what went wrong. That line is evidence for the tutor.
"""),
    code('''
hand_corrected = {}          # e.g. {"nDCG@5": 0.56}; leave empty if Task 1 was right
what_went_wrong = ""         # one line, only if you corrected something
''', "prediction", "T6"),
    code(f'''
# CHECK Task 6 (do not edit)
R1, Q1 = RANKINGS["Q1"], QRELS["Q1"]
_code = {{"P@5": precision_at_k(R1, Q1, 5), "R@5": recall_at_k(R1, Q1, 5), "Hit@1": hit_at_k(R1, Q1, 1),
         "Hit@5": hit_at_k(R1, Q1, 5), "RR@5": reciprocal_rank(R1, Q1, 5), "nDCG@5": ndcg_at_k(R1, Q1, 5)}}
assert _fp({{m: _r4(v) for m, v in _code.items()}}) == "{FP['HAND6']}", \
    "your functions are not all correct yet: pass the CHECKs of Tasks 2, 3 and 4 first"
_first_try = sum(abs(hand[m] - _code[m]) <= 0.01 for m in _code)
for m in _code:
    print(f"{{m:7s}} hand {{hand[m]!s:>6}}  code {{_code[m]:.4f}}  {{'match' if abs(hand[m] - _code[m]) <= 0.01 else 'DIFFERENT'}}")
print(f"First try: {{_first_try}} of 6 hand values matched your code (log this number).")
_final = {{**hand, **hand_corrected}}
_still = [m for m in _code if abs(_final[m] - _code[m]) > 0.01]
assert not _still, f"redo these by hand and correct them in hand_corrected: {{_still}}"
assert _first_try == 6 or what_went_wrong.strip(), "you corrected a value: say in one line what went wrong"
print("Task 6 OK: hand values equal code values")
''', "check"),
    md("""
## Task 7: make MRR and nDCG disagree

Build your **own** example. Choose qrels for one query and two rankings `rank_A` and `rank_B` (5 chunks each) such that, at k = 5:
- **MRR prefers A**: `reciprocal_rank(rank_A) > reciprocal_rank(rank_B)`, and
- **nDCG prefers B**: `ndcg_at_k(rank_A) < ndcg_at_k(rank_B)`.

Do not copy the lesson's example (D.6). Then explain the disagreement in one or two plain sentences.
"""),
    code('''
my_qrels = {}
rank_A = []
rank_B = []
why_they_disagree = ""
''', "learner", "T7"),
    code(f'''
# CHECK Task 7 (do not edit)
assert len(rank_A) == 5 and len(rank_B) == 5, "use exactly 5 chunks per ranking"
assert (rank_A, rank_B) != ({T.QD_A!r}, {T.QD_B!r}), "build your own example, not the lesson's"
rrA, rrB = reciprocal_rank(rank_A, my_qrels, 5), reciprocal_rank(rank_B, my_qrels, 5)
nA, nB = ndcg_at_k(rank_A, my_qrels, 5), ndcg_at_k(rank_B, my_qrels, 5)
print(f"A: RR {{rrA:.4f}}  nDCG@5 {{nA:.4f}}")
print(f"B: RR {{rrB:.4f}}  nDCG@5 {{nB:.4f}}")
assert rrA > rrB, "MRR must prefer A (higher reciprocal rank)"
assert nA < nB, "nDCG must prefer B"
assert len(why_they_disagree.split()) >= 10, "explain the disagreement in one or two sentences"
print("Task 7 OK. Read your explanation to the tutor.")
''', "check"),
    md("""
## Task 8: what if k doubles? (CR-08)

For Q1, k goes from **5 to 10**. **Predict first:** for each metric, will it go `"up"`, `"down"` or stay the `"same"`?

Then, in the empty code cell, build `actual_direction`: a dict with the same five keys, each `"up"`, `"down"` or `"same"`, computed with **your** functions at k = 5 and at k = 10.
"""),
    code('''
my_direction = {"P": None, "R": None, "Hit": None, "RR": None, "nDCG": None}
''', "prediction", "T8"),
    code(LEARNER, "learner", "T8b"),
    code(f'''
# CHECK Task 8 (do not edit)
assert all(v in ("up", "down", "same") for v in my_direction.values()), 'use "up", "down" or "same"'
assert set(actual_direction) == set(my_direction), "compute actual_direction with the same five keys"
assert _fp(actual_direction) == "{FP['DIR']}", "actual_direction is not right yet: compute each metric at k = 5 and k = 10"
_right = sum(my_direction[m] == actual_direction[m] for m in my_direction)
for m in my_direction:
    print(f"{{m:5s}} predicted {{my_direction[m]:5s}} actual {{actual_direction[m]}}")
print(f"Task 8 OK. Your predictions were right on {{_right}} of 5 (log this number).")
''', "check"),
    md("""
## Wrap-up: evidence for the log

Answer each in one line, no notes.

1. *Hand vs code:* "On the first try, ____ of 6 hand values matched my code. The one I missed was ____ because ____."
2. *Disagreement:* "MRR and nDCG disagree on my pair because ____."
3. *k doubles:* "When k went 5 → 10, ____ went up, ____ went down, and ____ stayed the same, because ____."
4. *Which metric:* "To ask 'did **all** the evidence arrive?', I would use ____; the course's primary metric for that is ____."

> Tell the tutor when you are done. The tutor grades `coding_independence_0_3` (Tasks 2, 3, 4) and `debugging_0_3` (any failed CHECK you fixed yourself, and Task 5).
"""),
]

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "rag-learning (3.12.8)", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12.8", "file_extension": ".py", "mimetype": "text/x-python",
                          "codemirror_mode": {"name": "ipython", "version": 3},
                          "nbconvert_exporter": "python", "pygments_lexer": "ipython3"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
for i, c in enumerate(nb["cells"]):
    c["id"] = f"p6-{i:02d}"
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print(f"wrote {OUT}: {len(cells)} cells")
