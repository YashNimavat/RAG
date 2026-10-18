# P6_FACTS — what the P6 lesson can rely on (run-verified)

Run date: **2026-10-08**. Every number in [`concepts/P6_ir_metrics.md`](../../../concepts/P6_ir_metrics.md) is listed here with the command and output section that produced it. Numbers not produced by these runs are marked DERIVED (arithmetic shown in the lesson) or UNVERIFIED. All metric values are a **toy illustration** on made-up data (`p6_toy.py`), never a result about a real retriever.

## 0. Environment, provenance, how to re-run

- **Interpreter.** CPython 3.12.8 (Windows 11), the project uv environment (`rag_learning/.venv`).
- **Versions** (printed in S1): numpy 2.5.3 · scikit-learn 1.9.1 (already installed as a dependency; nothing was installed for P6) · pymupdf 1.26.7 (book pages) · pytest 9.1.1 (dev group).
- **No API calls, no network, `.env` never read.** The metric code is pure Python (stdlib `math`).
- **Independent cross-check.** `sklearn.metrics.ndcg_score` (S7). No other IR library (ranx, pytrec_eval, ir_measures) is installed, and none was installed.
- **Files** (this folder):

  | File | What it is | Saved output |
  |---|---|---|
  | `p6_toy.py` | The toy chunks, queries, graded qrels and rankings (made up) | — |
  | `p6_metrics.py` | Reference implementation: P@k, R@k, Hit@k, RR, MRR, DCG, IDCG, nDCG (exp and linear gain), AP (two denominators), a chunk-level CE preview. **A solution for the lab** | — |
  | `test_p6_metrics.py` | 23 pytest cases: hand values = code values, conventions, edge cases, the 06 toy table | `out_p6_tests.txt` |
  | `p6_measure.py` | Sections S1–S11: every number in the lesson | `out_p6_measure.txt`, `out_p6_measure.stderr.txt` (empty) |
  | `p6_sources.py` | Repo-wide rank-metric search; every cited repo cell/line and book page | `out_p6_sources.txt` |
  | `p6_build_lab.py` | Writes `labs/P6_ir_metrics_lab.ipynb`; computes the CHECK fingerprints from `p6_metrics.py` | `out_p6_build_lab.txt` |
  | `p6_lab_runner.py` | Runs the lab top to bottom with learner cells taken from a solutions file; reports each CHECK | `out_p6_labtest_*.txt` |

- **Re-run** (from `rag_learning/`, Git Bash):
  ```bash
  export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
  B="C:/Yash/New-Work/Book RAG"; V=sources/verification/P6
  uv run python $V/p6_measure.py > $V/out_p6_measure.txt 2> $V/out_p6_measure.stderr.txt
  uv run pytest -v -p no:cacheprovider $V/test_p6_metrics.py > $V/out_p6_tests.txt
  uv run python $V/p6_sources.py "$B/upstream/RAG_Techniques" "$B/RAG_Made_Simple_The_Complete_Visual_Guide" > $V/out_p6_sources.txt
  uv run python $V/p6_build_lab.py labs/P6_ir_metrics_lab.ipynb > $V/out_p6_build_lab.txt
  uv run python $V/p6_lab_runner.py labs/P6_ir_metrics_lab.ipynb <solutions file outside the workspace>
  ```
- **Determinism.** Two consecutive runs of `p6_measure.py` gave byte-identical stdout.

## 1. Facts by section (`M` = `out_p6_measure.txt`)

### Toy data (M S2)

| Query | qrels (grade 2 = sufficient, 1 = partial) | Relevant at ranks |
|---|---|---|
| Q1 "Which gases trap heat in the atmosphere?" | c3:2, c7:1, c9:1 | c3 → 2, c7 → 4, c9 → 7 |
| Q2 "What does the Paris Agreement aim for?" | c4:2 | c4 → 1 |
| Q3 "How does cutting forests add CO2 to the air?" | c6:2, c10:1 | c10 → 4, c6 → 5 |

Rankings: Q1 `c5 c3 c8 c7 c1 c2 c9 c4 c6 c10`; Q2 `c4 c2 c1 c3 c5 c6 c7 c8 c9 c10`; Q3 `c1 c8 c2 c10 c6 c3 c4 c5 c7 c9`.

### S3 Discounts 1/log2(i + 1)

| i | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1/log2(i+1) | 1.0000 | 0.6309 | 0.5000 | 0.4307 | 0.3869 | 0.3562 | 0.3333 | 0.3155 | 0.3010 | 0.2891 |

Gains: exp (2^g − 1) 0/1/3; linear 0/1/2.

### S4 Q1 at k = 5 (Part F) and Q2, Q3

| Fact | Value |
|---|---|
| Q1 P@5 / R@5 / Hit@1 / Hit@5 / RR@5 / nDCG@5 | 0.4000 / 0.6667 / 0 / 1 / 0.5000 / **0.5625** |
| Q1 DCG@5 / IDCG@5 (exp) | 2.3235 (= 1.8928 + 0.4307) / 4.1309 (= 3 + 0.6309 + 0.5000) |
| Q2 at k = 5 | P 0.2000, R 1.0000, Hit 1, RR 1.0000, nDCG 1.0000 |
| Q3 at k = 5 | P 0.4000, R 1.0000, Hit 1, RR 0.2500, nDCG 0.4382 (DCG 1.5912, IDCG 3.6309) |

### S5 k sweep (Q1) and "nDCG can fall"

| k | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| P@k | 0 | 0.5000 | 0.3333 | 0.5000 | 0.4000 | 0.3333 | 0.4286 | 0.3750 | 0.3333 | 0.3000 |
| R@k | 0 | 0.3333 | 0.3333 | 0.6667 | 0.6667 | 0.6667 | 1 | 1 | 1 | 1 |
| Hit@k | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| RR@k | 0 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 |
| nDCG@k | 0 | 0.5213 | 0.4582 | 0.5625 | 0.5625 | 0.5625 | 0.6431 | 0.6431 | 0.6431 | 0.6431 |

QF (a relevant at rank 1, b relevant but never retrieved): nDCG@1 = 1.0000, nDCG@2 = nDCG@5 = 0.6131 (IDCG 1.0000 → 1.6309).

### S6 MRR

| Fact | Value |
|---|---|
| RR@10 Q1 / Q2 / Q3 | 0.5000 / 1.0000 / 0.2500 |
| MRR@10 | **0.5833** |
| First relevant ranks; mean rank; 1 / mean rank | 2, 1, 4; 2.3333; 0.4286 (not the MRR) |
| MRR@3 | 0.5000 (Q3's first hit at rank 4 is cut off) |

### S7 nDCG conventions and cross-check

| Fact | Value |
|---|---|
| Q1 nDCG@5, exp gain vs linear gain | 0.5625 vs 0.5406 (linear DCG 1.6925, IDCG 3.1309) |
| Q1 with every grade set to 1 | 0.4982 under both gains |
| IDCG-from-retrieved bug, Q1 ranking | 0.6399 instead of 0.5625 |
| IDCG-from-retrieved bug, J2 ranking (`c7 c5 c8 c1 c2`, only the partial chunk) | 1.0000 instead of 0.2421 |
| `sklearn.metrics.ndcg_score`, k ≤ ranking length | 66 comparisons (10 rankings, k ∈ {1,3,5,10}, both gains): max difference 1.11e-16 |
| sklearn, Q1 k = 5 | 0.5406 with the grades as given (linear gain); 0.5625 when given 2^g − 1 |
| k > ranking length | not comparable: sklearn ranks every doc it is given, so unretrieved relevant docs still earn gain (e.g. QD_A k = 10: ours 0.4693, sklearn 0.7929) |

### S8 MRR and nDCG disagree

| Ranking (k = 5) | P@5 | R@5 | RR | nDCG@5 |
|---|---|---|---|---|
| QD_A `d1 n1 n2 n3 n4` (d1–d3 relevant) | 0.2000 | 0.3333 | **1.0000** | 0.4693 |
| QD_B `n1 d1 d2 d3 n2` | 0.6000 | 1.0000 | 0.5000 | **0.7328** |
| QG_A `p h n1 n2 n3` (h = 2, p = 1) | — | — | 1.0000 | 0.7967 (linear 0.8597) |
| QG_B `h p n1 n2 n3` | — | — | 1.0000 | 1.0000 |
| QS good `a b x y z` (a, b relevant) | 0.4000 | 1.0000 | 1.0000 | 1.0000 |
| QS poor `x y a z b` | 0.4000 | 1.0000 | 0.3333 | 0.5438 |

QD IDCG@5 = 2.1309; DCG@5 QD_A 1.0000, QD_B 1.5616. QG IDCG@5 = 3.6309; DCG@5 QG_A 2.8928.

### S9 The 06 §7.3 toy table, replicated

All 06 values reproduced: Hit@1/3/5 = 0/1/1; P@3/P@5 = 0.3333/0.4000; CE@3/CE@5 = 0/1 (chunk-level preview); RR 0.5000; nDCG@5 binary 0.6509 (DCG 1.0616, IDCG 1.6309); graded 0.6399 (DCG 2.3235, IDCG 3.6309); context precision@5 0.5000; MRR of (0.5, 1, 0) = 0.5000.

### S10 CE@k preview vs Recall@k (QE: e2 and e3 overlap and both hold G1; e6 holds G2)

| k | Hit | P | Recall | CE |
|---|---|---|---|---|
| 2 | 1 | 1.0000 | 0.6667 | 0 |
| 3 | 1 | 0.6667 | 0.6667 | 0 |
| 4 | 1 | 0.7500 | 1.0000 | 1 |

### S11 Book-wording checks

| Fact | Value |
|---|---|
| Q1 AP@5: standard (÷ all 3 relevant) vs ÷ relevant retrieved (2) | 0.3333 vs 0.5000 |
| Q1 AP@10 | 0.4762 both (all 3 retrieved) |
| QD_A AP@5: standard vs ÷ relevant retrieved | 0.3333 vs 1.0000 |
| J1 (3 chunks returned, k = 5): P@5 ÷ k vs ÷ 3 returned | 0.4000 vs 0.6667 |
| Book examples | 3/5 = 0.6; 3/10 = 0.3; 1/3 = 0.3333 (book prints 0.33) |

### Unit tests (`out_p6_tests.txt`)

23 passed (hand values for Q1 at k = 5 and MRR; P@k on a short list; RR cut-off; grade-1 counts as relevant; unjudged = not relevant; perfect ranking = 1; IDCG from all relevant; gain conventions; nDCG can fall; Recall and Hit never decrease with k; the D.6 disagreement; the 06 toy table; ValueError for bad k, duplicates, and no relevant chunk).

### Lab fingerprints (`out_p6_build_lab.txt`)

The notebook's CHECK cells compare 16-hex sha256 fingerprints of 4-decimal values computed by `p6_metrics.py` (13 fingerprints; values listed in the output file). A guard in the build script asserts that no hidden value lies within 1e-6 of a 4-decimal rounding boundary.

### Lab test (`out_p6_labtest_*.txt`; the throwaway solutions lived in the session scratchpad, outside the workspace)

| Run | Result |
|---|---|
| `good`: an independent solution written for the test (not importing `p6_metrics.py`) | **8/8 CHECK cells pass**; Task 5: its 6 tests catch 6 of 6 broken versions; Task 8 prediction 4 of 5 |
| `good` in a real Jupyter kernel (`jupyter_client` + the project ipykernel; driver script in the scratchpad) | 8/8 PASS (`out_p6_labtest_kernel.txt`) |
| `broken`: recall ÷ k, MRR as 1/mean rank, RR without cut-off, IDCG from retrieved, weak tests, the lesson's own D.6 pair, wrong `actual_direction` | 1/8 pass (Task 1 only, which only checks that values are filled) |
| `empty`: the notebook as shipped | 0/8 pass |
| `singlebugs`: seven one-bug variants of `good`, plus correct functions with weak tests | each bug fails the CHECK of its own task (P ÷ returned → Task 2; RR from 0 → Task 3; RR no cut-off → Task 3; IDCG from retrieved → Task 4; linear gain → Task 4; discount shifted → Task 4; wrong hand nDCG without correction → Task 6); weak tests → Task 5 (caught 0 of 6) |

### S-src Citations (`out_p6_sources.txt`): **ALL PASS** (87 checks)

| Citation | Checked content |
|---|---|
| Repo HEAD | `009adba2be1bef49780ef73b6dd3c18fd24b035b` |
| Repo-wide search | 46 notebooks (cell sources and text outputs) + 25 `.py` files; regex for nDCG, DCG, reciprocal rank, MRR, Recall@/at k, hit rate, Hit@, Precision@/at k, average precision, MAP@. **One hit only:** "hit rate" in `local_rag_huggingface_faiss.ipynb` cell 30. Matches inside base64 image outputs only (not text): `Agentic_RAG`, `graph_rag`, `multi_model_rag_with_colpali` |
| `local_rag_huggingface_faiss.ipynb` cell 30 | `evaluate_rag(rag_chain, retriever)` inside `try`/`except ImportError`; fallback counts `expected_keywords` found in the **answer**; prints "Keyword hit rate" |
| `evaluation/evalute_rag.py` | L95 `def evaluate_rag(retriever, num_questions: int = 5)`; L117 1–5 rating prompt; L134 questions generated by the LLM; L144–L145 retrieved docs joined into one string; L160–L163 `calculate_average_scores` body is `pass` |
| `evaluation/define_evaluation_metrics.ipynb` cells 3, 6, 9, 10 | LLM correctness and faithfulness prompts; cell 9 defines `relevancy_score_prompt` (0 / 0.33 / 0.66 / 1, "average of all scores") but builds the chain from `ratio_of_relevant_docs_prompt`, which appears nowhere else in the notebook |
| `evaluation/evaluation_deep_eval.ipynb` cells 2, 4, 6 | deepeval `GEval` correctness, `FaithfulnessMetric`, `ContextualRelevancyMetric` |
| `evaluation/end-2-end_rag_evaluation.ipynb` cells 12, 19, 22 | LLM completeness judge; RAGAS `faithfulness`; thresholds and `classification_report` against human annotations |
| `evaluation/evaluation_grouse.ipynb` cells 4, 36 | GroUSE `GroundedQAEvaluator`, `meta_evaluate_pipeline` (judge meta-evaluation) |
| `evaluation/open-rag-eval-example.ipynb` cells 7, 8 | UMBRELA graded passage labels 0–3 (`NO_RELEVANCE` … `EXACT_ANSWER`), printed per passage |
| `choose_chunk_size.ipynb` cells 8, 10 | `FaithfulnessEvaluator()`, `RelevancyEvaluator()`; averages of pass rates and response time with `similarity_top_k=5` |
| `HyPE_Hypothetical_Prompt_Embeddings.ipynb` cell 0 | claims an improvement "in retrieval precision" (from a preprint; not computed in the repo) |
| Book Ch22 p.4/19, p.5/19, p.6/19, p.7/19, p.8/19, p.18/19 | P@K and the 0.6 example; Recall@K over all relevant documents and the 0.3 example; "context precision"; the MRR/MAP/NDCG section heading; MRR per query averaged over queries with the 0.33 example; MAP; NDCG's logarithmic discount, ideal-ranking normalisation, graded relevance, 0-to-1 range; the good-vs-poor ranking caption; generation vs retrieval isolation; the key-takeaway line |
| Book Appendix (23 pages) p.13, 15, 18, 19, 20 | Appendix B Glossary begins p.13/23; Context Precision p.15/23; MAP p.18/23; MRR, NDCG, Precision at K p.19/23; Recall at K p.20/23 |
| Whole-book absence | never "hit rate" or "Hit@"; never "qrels"; never "log2"/"log base"; never "2^"; never "DCG =" (no formulas) |

The two figures (Ch22 p.5/19 precision 3/5 vs recall 3/10; Ch22 p.7/19 good vs poor ranking) were viewed as rendered images, not only as text.

## 1b. Added 2026-10-18: K1–K12 (`p6_kit_measure.py`) for the HTML lesson, on v0's 97 chunks

`K` = `p6_kit_measure.py` (section in `out_p6_kit_measure.txt`). Run from `rag_learning/`:
`PYTHONIOENCODING=utf-8 uv run --group eval python sources/verification/P6/p6_kit_measure.py "C:/Yash/New-Work/Book RAG/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"`. A second run gave byte-identical stdout (`cmp`); stderr holds only model-loading messages. No API call, no `.env` read. `p6_measure.py` is unchanged. The optional `eval` group (`ir-measures==0.4.3`, `pytrec-eval-terrier==0.5.10`) was added on 2026-10-18 at the learner's OK; K11 needs it.

**Corpus and labels.** v0's 97 chunks (07 recursive chunker, per page, 1,000/200; `params_hash` `1ca9c5a3b548`; `chunks.jsonl` sha256 `d4108b89…`, the file used by P3's verify notebook, P4's K-run and the C2 lab). Relevance = the 06 §6.7 draft seeds' evidence spans through `contracts_check.rel` (any overlap); every unlisted chunk counts as 0. Chunk ids are 0-based `seq` numbers. Retrievers: BM25 (`rank_bm25` 0.2.2, `tok_norm`, k1 = 1.5, b = 0.75) and dense MiniLM `all-MiniLM-L6-v2` (cosine on unit vectors); ties by (−score, seq). The seeds are `llm-draft`, not human-verified: every number here is an **observation, never an evaluation result**.

| Id | Fact | Value |
|---|---|---|
| K1 | Labels per answerable seed (relevant seqs; groups they touch) | D-001 [7] G1 · D-002 [27] G1 · D-003 [68] G1 · D-004 [23, 67, 68] all G1 · **D-005 [3, 4]: s003 touches G1 and G2, s004 only G2** · D-006 [21] G1+G2 · **D-007 [27, 85]: s027 = G1 (p.10), s085 = G2 (p.29)** · D-008 [69] G1. n_rel = [1, 1, 1, 3, 2, 1, 2, 1]: 3 of 8 seeds have more than one relevant chunk; 3 of 8 have two fact groups. D-009, D-010 unanswerable. BM25 avgdl 111.23, vocabulary 1,769 (= P3 verify) |
| K2 | **Running example D-007, dense** | Top 5: s069 p.24 no · **s027 p.10 G1** · **s085 p.29 G2** · s084 p.29 no · s017 p.6 no (cosines 0.7094, 0.6105, 0.5954, 0.5902, 0.5849). k = 1: all 0. **k = 2: Hit 1, P 0.50, R 0.50, RR 0.50, nDCG 0.3869, CE 0, Group-Recall 0.50.** k = 3: Hit 1, P 0.67, R 1.00, RR 0.50, nDCG 0.6934, CE 1, Group-Recall 1.00. k = 4: P 0.50 (rest as k = 3). k = 5: P 0.40. k = 10: P 0.20, nDCG 0.6934. DCG/IDCG: k = 2 0.6309/1.6309; k = 3 1.1309/1.6309 |
| K3 | D-007, BM25 | Top 5: **s027**, **s085**, s017, s069, s068 (scores 42.6533, 31.9874, 26.6370, 24.4334, 23.3142). k = 1: Hit 1, P 1.00, **R 0.50, CE 0**, RR 1, nDCG 1.0000. k = 2: P 1.00, R 1.00, CE 1, nDCG 1.0000. k = 4: P 0.50 |
| K4 | **D-005: counting chunks ≠ counting facts** | Dense top 5: s003 (G1+G2), s004 (G2), s002, s005, s067. **k = 1: Recall 0.50 but CE 1** (one chunk holds both facts). BM25 top 5: s003, s002, s004, s077, s005; k = 2: P 0.50, R 0.50, CE 1, nDCG 0.6131; k = 4: R 1.00, nDCG 0.9197 |
| K5 | P@4 ceiling n_rel/k | 0.25 for D-001/002/003/006/008; 0.50 for D-005, D-007; 0.75 for D-004. **Both retrievers reach the ceiling on every seed** (P@4 = ceiling 8/8) |
| K6 | Every seed, both retrievers (set metrics at k = 4; RR, nDCG at 10) | First relevant rank, dense [3, 3, 1, 1, 1, 1, 2, 2]; BM25 [1, 1, 1, 1, 1, 2, 1, 1]. **Dense means (n = 8): Hit@1 0.500, Hit@4 1.000, P@4 0.3750, R@4 1.0000, MRR@10 0.7083, nDCG@10 0.7905, CE@4 1.000.** **BM25: Hit@1 0.875, Hit@4 1.000, P@4 0.3750, R@4 1.0000, MRR@10 0.9375, nDCG@10 0.9398, CE@4 1.000.** MRR@10 to 3 dp = **0.708 / 0.938 = P3 §12**. CE@k counts of 8, dense/BM25: k = 1 4/6 · k = 2 5/8 · k = 3 8/8 · k = 4 8/8 (the seeds saturate) |
| K7 | Discreteness of RR | RR@10 can take 11 values (1, 1/2 … 1/10, 0). Per seed: dense [0.3333, 0.3333, 1, 1, 1, 1, 0.5, 0.5]; BM25 [1, 1, 1, 1, 1, 0.5, 1, 1]. BM25 − dense per seed [0.6667, 0.6667, 0, 0, 0, −0.5, 0.5, 0.5]: 3 ties, **1 seed (D-006) where dense wins**. One seed moving from rank 2 to rank 1 moves an 8-seed MRR by **0.0625** |
| K8 | AP, R-precision (toy Q1 = TOY; D-007 = observation) | Toy Q1: R-precision = P@3 = **0.3333**; AP@10 0.4762; AP@5 0.3333 standard vs 0.5000 ÷ relevant retrieved (= S11). D-007 dense: AP@5 0.5833 both denominators (both relevant chunks retrieved); R-precision = P@2 = 0.5000. Review item A-06 (relevant, not, not, relevant, not; 3 relevant exist): AP@5 **0.5000** standard vs **0.7500** ÷ relevant retrieved (the research's DERIVED values, now measured) |
| K9 | **Unjudged = not relevant, real corpus** (labels kept only for relevant chunks inside one retriever's top D; seeds whose pool holds none are dropped) | Pool = BM25 top 1 (n = 7): **P@4 0.3929 → 0.2500 for both retrievers**; MRR@10 unchanged (dense 0.6667, BM25 1.0000); nDCG@10 dense 0.7606 → 0.7517, **BM25 0.9839 → 1.0000 (rises)**; 21 of 28 top-4 slots unjudged; 4 truly relevant top-4 chunks scored 0. Pool = BM25 top 2 (n = 8): P@4 0.3750 → 0.3125 both; nDCG dense 0.7905 → 0.7805, BM25 0.9398 → **0.9539**. Pool = dense top 1 (n = 4): P@4 0.4375 → 0.2500 both; nDCG BM25 0.8795 → 0.9077, dense 1.0000 → 1.0000. Pool = dense top 2 (n = 6): nDCG dense 0.8874 → 0.8770, BM25 0.9197 → 0.9046. **Reading:** missing labels lower P@k, and can raise nDCG (IDCG shrinks too); MRR did not move here because each seed's first relevant chunk was in the pool. Small, saturated draft seeds: the direction of the nDCG change is not stable |
| K10 | Ties at rank 4 | None on any seed for either retriever. BM25 chunks scoring exactly 0 per seed: D-001 1, D-002 5, D-006 1, **D-008 17**, D-009 5, D-010 8, others 0 |
| K11 | **Same run, two tools** (ir-measures 0.4.3 → pytrec-eval-terrier 0.5.10) | Seeds, scores = 97 − rank (no ties): P@4, R@4, Success@4, RR@10, nDCG@10 agree with `p6_metrics` (max \|diff\| 1.11e-16 dense, 0 BM25); ir-measures `RR` (no cut-off) = RR@10 here. Toy Q1 nDCG@5: ir-measures default (gain = qrels value) **0.5406**; grades mapped to 2^g − 1 **0.5625** (= ours, exp; ours linear 0.5406). `nDCG(dcg='exp-log2')` calls a Perl script (gdeval) and fails on this machine, so map the gains instead. **Tie:** a and b both score 1.0, a relevant: course rule RR **1.0**; ir-measures RR **0.5**, P@1 0 (ties broken by docno, descending: b first). **Cut-off:** first relevant at rank 12: `RR` 0.0833, `RR@10` 0, ours 0 |
| K12 | MRR vs nDCG on real seeds | D-004: RR equal (1, 1), nDCG dense 1.0000 vs BM25 **0.9675** (relevant at 1, 2, 4 vs 1, 2, 3). D-005: RR 1 both; nDCG 1.0000 vs **0.9197**. D-006: dense wins both (1 vs 0.5; 1 vs 0.6309) |

**Status changes since section 2 was written** (2026-10-17 research, `study/research/phase_01_prerequisites.md`, Concept P6, sources [P6-3]–[P6-9]; papers read, not run here):
- **nDCG history resolved.** Järvelin & Kekäläinen 2002 used the relevance weight itself as the gain and log_b i with no discount before rank b (b = 2: ranks 1 and 2 undiscounted) [P6-3, p.425–426]. The (2^g − 1)/log2(1 + i) form is Burges et al. 2005, eq. 16 [P6-4], and IIR §8.4 [P6-1]. 06 §7.3's citation of J&K for that formula is research error E1 (not edited). The section-2 UNVERIFIED row below is superseded by this note.
- **trec_eval conventions** (source read [P6-8]; K11 confirms the tie and cut-off behaviour through pytrec_eval): gain = the qrels value (linear); discount log2(rank + 1); ties broken by docno, descending; the rank column is ignored; `recip_rank` has no cut-off.


## 2. DERIVED and UNVERIFIED

| Item | Status |
|---|---|
| Hand arithmetic shown in Parts D, F, L (e.g. 2.3235 / 4.1309) | DERIVED from S3–S8 and equal to the code values |
| Whether Järvelin & Kekäläinen (2002), which 06 cites for nDCG, used the 2^g − 1 gain or the grade itself, and the same discount | UNVERIFIED (paper not opened). sklearn's linear gain is measured (S7) |
| What `open_rag_eval` computes internally from UMBRELA labels | UNVERIFIED (external library, not run) |
| Runtime behaviour of `local_rag_huggingface_faiss.ipynb` cell 30 (`evaluate_rag(rag_chain, retriever)` against the signature `evaluate_rag(retriever, num_questions=5)`) | STATIC read only; not run (needs an OpenAI key) |
| `define_evaluation_metrics.ipynb` cell 9 raising `NameError` | STATIC inference from the source (the name is never defined); not run |

## 3. Notes for 04 and 02 (not edited; recorded here)

- **04 P6 row** cites Ch22 p.4/19–p.6/19 with "two tiny examples". The book has **three** numeric examples (P@5 = 0.6 on p.4/19; Recall = 0.3 on p.5/19; MRR 1.0 and 0.33 on p.6/19). The row also misses the ranking figure on p.7/19 (which 04's own M2 row and its Ch22 cross-table include, as p.4/19–p.7/19) and the glossary pages App p.18–20/23 (listed in the 02 card).
- **04 P6 row, repo column** ("No Recall@k/MRR/nDCG anywhere"): **confirmed**. The only term found is the answer-level "Keyword hit rate" in `local_rag_huggingface_faiss.ipynb` cell 30 (02 names it; 04 does not).
- **02 P6 card**: book pages, the repo claim and the cell-30 note all **confirmed**.
- **06 §7.3**: every toy value reproduced (S9). 06 defines no plain Recall@k (it was replaced by CE@k and Group-Recall@k on 2026-10-08); the lesson teaches the standard chunk-level Recall@k and labels it as distinct from both.
