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
