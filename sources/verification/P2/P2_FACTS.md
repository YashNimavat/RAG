# P2_FACTS — what the P2 lesson can rely on (run-verified)

Run date: **2026-10-08**. Every number in [`concepts/P2_ir_framing.md`](../../../concepts/P2_ir_framing.md) is listed here with the command and output section that produced it. Numbers that were not produced by these runs are marked CITED, DERIVED or UNVERIFIED.

## 0. Environment, provenance, how to re-run

- **Interpreter.** CPython 3.12.8 (Windows 11), the project uv environment (`rag_learning/.venv`).
- **Versions** (printed in S1): pymupdf 1.26.7 · numpy 2.5.3 · sentence-transformers 6.1.0 · transformers 5.19.0 · torch 2.14.1 (CPU) · rank-bm25 0.2.2.
- **Toy corpus.** [`p2_toy_corpus.json`](p2_toy_corpus.json), written for P2 (made-up documents; not from the book or repo). File sha256 `a2bee6be44e4a170423ecf0fb83d0a4a70017f5e31e774bd6653d4be43198b5c`. 10 docs, 5 queries, 13 listed qrels (all other pairs are grade 0).
- **Real corpus (S9 only).** `upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf`, sha256 `1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669`; extraction as in the acceptance suite and P1 (`page.get_text()`, pages joined with `"\n"`); plain character windows 1,000 / overlap 200.
- **Model (S6 only).** `sentence-transformers/all-MiniLM-L6-v2` from the local HF cache, offline (`HF_HUB_OFFLINE=1` set in the script), `normalize_embeddings=True`, cosine = dot.
- **No API calls.** No Groq or Cohere call; `.env` is never read.
- **Scripts and outputs** (this folder):

  | File | What it is |
  |---|---|
  | `p2_measure.py` | Sections S1–S11: toy tokens, index, AND/OR, overlap ranking, MiniLM ranking, qrels, set vs ranking, PDF index, rank_bm25 internals, lab fingerprints |
  | `out_p2_measure.txt` / `out_p2_measure.stderr.txt` | Its stdout / stderr (stderr holds only the model-loading progress bar) |
  | `p2_sources.py` → `out_p2_sources.txt` | S-src: every cited repo cell (0-based) and book page, plus absence checks |
  | `out_p2_labtest.txt` | The lab run in a Jupyter kernel with a throwaway solution (good) and a broken one (see §3) |
  | `p2_kit_measure.py` → `out_p2_kit_measure.txt` (2026-10-18) | K1–K6 for the HTML lesson: ties, recall@k curves, the one-retriever pool demo, span-derived window labels, κ (§1b) |

- **Re-run** (from `rag_learning/`, Git Bash):
  ```bash
  B="C:/Yash/New-Work/Book RAG"
  PYTHONIOENCODING=utf-8 uv run python sources/verification/P2/p2_measure.py "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
      > sources/verification/P2/out_p2_measure.txt 2> sources/verification/P2/out_p2_measure.stderr.txt
  PYTHONIOENCODING=utf-8 uv run python sources/verification/P2/p2_sources.py "$B/upstream/RAG_Techniques" "$B/RAG_Made_Simple_The_Complete_Visual_Guide" \
      > sources/verification/P2/out_p2_sources.txt
  ```
- **Determinism.** Two consecutive runs of `p2_measure.py` gave **byte-identical** stdout.

## 1. Facts by section

`M` = `p2_measure.py` (section in `out_p2_measure.txt`); `S` = `p2_sources.py`.

### S1 Toy corpus

| Fact | Value | Source |
|---|---|---|
| Docs / queries / listed qrels / pairs | 10 / 5 / 13 / 50 | M S1 |
| `_fp(DOCS)` / `_fp(QUERIES)` (lab setup check) | `1edaacca3ff916da` / `acb0163a7a3906b8` | M S1 |

### S2 Tokenization (lowercase; runs of `[a-z0-9]`; no stemming, no stopwords)

| Fact | Value | Source |
|---|---|---|
| Total tokens in the 10 docs | 119 | M S2 |
| d08 tokens / distinct | 11 / 7 | M S2 |
| `tokenize('Sea-level RISE, 2019!')` | `['sea', 'level', 'rise', '2019']` | M S2 |
| Query tokens | q1 main, cause, of, climate, change · q2 why, do, sea, levels, rise · q3 renewable, energy · q4 where, does, methane, come, from · q5 is, extreme, heat, becoming, more, common | M S2 |

### S3 Inverted index (toy)

| Fact | Value | Source |
|---|---|---|
| Vocabulary / total postings / df = 1 terms | 88 / 114 / 71 | M S3 |
| Highest df | and 6, the 5, in 4 | M S3 |
| Postings | climate, change → d02, d08 · of → d01, d02 · the → d01, d02, d03, d05, d06 · carbon → d01, d06 · heat → d03, d10 · methane → d09 · rising → d04 · rise, renewable, energy → none | M S3 |
| Postings equal a full scan of the docs | asserted, OK | M S3 |

### S4 Boolean retrieval (toy)

| Query | AND | OR | Postings read | Source |
|---|---|---|---|---|
| q1 | d02 | d01, d02, d08 | 10 | M S4 |
| q2 | — | d04 | 2 | M S4 |
| q3 | — | — | 0 | M S4 |
| q4 | — | d06, d09 | 2 | M S4 |
| q5 | — | d02, d03, d10 | 5 | M S4 |

### S5 Overlap ranking from the index (distinct query terms matched)

q1 (d02 5, d01 3, d08 2) · q2 (d04 2) · q3 () · q4 (d06 1, d09 1) · q5 (d10 3, d02 1, d03 1). Source: M S5.

### S6 MiniLM cosine over all 10 docs (toy illustration)

| Query | Ranking (cosine) | Source |
|---|---|---|
| q1 | d02 0.8402, d01 0.6342, d04 0.5139, d03 0.4904, d10 0.4318, d08 0.3992, d05 0.3927, d06 0.2736, **d09 0.2469 (rank 9)**, d07 0.1341 | M S6 |
| q2 | d04 0.8316, d05 0.4038, … | M S6 |
| q3 | **d07 0.5804**, d01 0.3598, … | M S6 |
| q4 | d09 0.6326, … | M S6 |
| q5 | d10 0.6342, … | M S6 |

Embedding dim 384; norms ≈ 1.

### S7 Reference qrels (guideline v1; relevant = grade ≥ 1)

q1: d01 (2), d03 (1), d09 (1) · q2: d04 (2), d05 (1) · q3: d07 (2) · q4: d09 (2) · q5: d10 (2). **8 relevant pairs of 50.** Source: M S7.

### S8 Set quality vs ranking quality

| Fact | Value | Source |
|---|---|---|
| Run A d02, d01, d08 (q1) | precision 0.3333, recall 0.3333, first relevant rank 2 | M S8 |
| Run B d01, d08, d02 | 0.3333, 0.3333, rank 1 | M S8 |
| Run C d01, d03, d09 | 1.0, 1.0, rank 1 | M S8 |
| Lexical mean set recall, k = 3 / 6 | 0.567 / 0.567 (per query 0.333, 0.5, 0.0, 1.0, 1.0) | M S8 |
| MiniLM mean set recall, k = 3 / 6 | 0.867 / 0.933 | M S8 |
| MiniLM q1 precision / recall, k = 3 → 6 | 0.333 / 0.333 → 0.333 / 0.667 (d03 enters at rank 4) | M S8 |
| Lexical q1 candidates; recall@3; recall@6 | 3; 0.3333; 0.3333 | M S8 |
| Edge cases | precision([]) = 0.0; first_relevant_rank(['d02']) = None | M S8 |

### S9 Inverted index over the climate PDF (91 windows)

| Fact | Value | Source |
|---|---|---|
| Characters / windows / last window | 72,593 / 91 / 593 | M S9 |
| Vocabulary / postings / tokens / df = 1 terms | 1,868 / 8,107 / 11,807 / 745 | M S9 |
| df (windows of 91) | and 91, to 87, for 80, the 80, climate 77, in 76, of 74, change 59, energy 42, carbon 30, renewable 30, greenhouse 15, rising 6, methane 5, rise 4 | M S9 |
| `methane emissions` | OR 34, AND 5, postings read 39 | M S9 |
| `main cause of climate change` | OR 90, AND 0, postings read 213 | M S9 |
| `renewable energy` | OR 42, AND 30, postings read 72 | M S9 |
| OR results equal a full scan | asserted, OK | M S9 |

### S10 rank_bm25 internals

| Fact | Value | Source |
|---|---|---|
| Version | 0.2.2 | M S10 |
| `doc_freqs` | list of 10 dicts (one term-count dict per document) | M S10 |
| Any attribute mapping term → documents | False | M S10 |
| `get_scores` source loops `for doc in self.doc_freqs` | True | M S10 |
| `get_scores(q4)` | length 10; non-zero for d06, d09 | M S10 |

### S11 Lab fingerprints (`labs/P2_ir_framing_lab.ipynb`)

tokenize per doc `043587a6e439e8a1` · index `a75adb6a2aa3ee3a` · AND `5375cb3802db14a1` · OR `946fea0d80376ae5` · overlap rankings `109e8ca0d7fce277` · toy runs A/B/C `9d72704a91f3c210` · CR-08 `[3, 0.3333, 0.3333]` `f0320f3ce2231c5f` · PDF facts `[91, 1868, 80, 5, 34]` `552eae7370ad8bbe` · 50 per-pair binary reference hashes (last line of `out_p2_measure.txt`, embedded in the Task 5 CHECK).

### S-src Citations

`p2_sources.py`: **ALL PASS** (repo HEAD `009adba2…`; 8 cell checks with 25 substrings + 1 NameError check; `data/q_a.json` keys; 2 repo absence checks; 26 book-page phrase checks, each phrase < 15 words; 3 book absence checks).

| Citation | Checked content |
|---|---|
| `simple_rag.ipynb` cell 13 | `as_retriever(search_kwargs={"k": 2})` |
| `fusion_retrieval.ipynb` cell 14 | `create_bm25_index`, the IR-ranking-function docstring, `doc.page_content.split()`, `BM25Okapi(tokenized_docs)` |
| `fusion_retrieval.ipynb` cell 17 | `similarity_search("", k=vectorstore.index.ntotal)`, `bm25.get_scores(query.split())`, `argsort(...)[::-1]`, `[:k]` |
| `reliable_rag.ipynb` cell 14 | binary relevance docstring; "keyword(s) or semantic meaning related"; "does not need to be a stringent test"; `ChatGroq(model="llama-3.1-8b-instant", temperature=0)` |
| `evaluation/define_evaluation_metrics.ipynb` cell 3 | `Ground Truth: {ground_truth}`; ground truth = an answer |
| `evaluation/define_evaluation_metrics.ipynb` cell 9 | rubric 0.33 "related keywords or concepts", 1.00 "directly and fully answers"; "Average of all scores"; prompt named `relevancy_score_prompt` but chain uses undefined `ratio_of_relevant_docs_prompt` |
| `evaluation/evaluation_deep_eval.ipynb` cells 6, 11 | `ContextualRelevancyMetric(`; test cases with `expected_output=gt_answer`, `retrieval_context=retrieved_document` |
| `data/q_a.json` | 44 items, keys `question`, `answer` only |
| Repo absences | no "inverted", no "qrel" in any notebook source cell, `.py` or `.md` |
| Book | Intro p.1/8; Ch1 p.8/14, p.10/14, p.12/14; Ch3 p.1/14; Ch12 p.2/14, p.3/14, p.5/14, p.6/14; Ch13 p.1/13, p.2/13, p.5/13, p.9/13; Ch22 p.4/19, p.5/19, p.6/19, p.7/19, p.12/19; App p.19/23, p.20/23, p.22/23 (page counts checked) |
| Book absences | "inverted" and "qrel" never appear; "relevance judg…" only at App p.9/23 |

## 1b. Added 2026-10-18: K1–K6 (`p2_kit_measure.py`) for the HTML lesson

`K` = `p2_kit_measure.py` (section in `out_p2_kit_measure.txt`). Run from `rag_learning/`:
`PYTHONIOENCODING=utf-8 uv run python sources/verification/P2/p2_kit_measure.py "C:/Yash/New-Work/Book RAG/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"`. A second run gave byte-identical stdout (`cmp`); stderr holds only model-loading progress. Same toy corpus, tokenizer, overlap ranking and MiniLM ranking as S2–S8. No API call, no `.env` read. `p2_measure.py` is unchanged.

| Id | Fact | Value |
|---|---|---|
| K1 | Environment | Python 3.12.8; pymupdf 1.26.7, numpy 2.5.3, sentence-transformers 6.1.0, scikit-learn 1.9.1 |
| K2 | The tie rule decides a rank (q4: d06 and d09 both score 1; relevant = d09) | doc id ascending (S5): d06, d09 → first relevant rank **2**, RR 0.50; doc id descending: d09, d06 → rank **1**, RR 1.00 |
| K3 | Set recall at k = 1…10 | lexical q1: 0.0, then 0.333 from k = 2 on (only 3 candidates); lexical mean: 0.3, then 0.567 from k = 2 on. MiniLM q1: 0.0, 0.333, 0.333, 0.667 (k 4–8), 1.0 (k 9–10); MiniLM mean: 0.7, 0.867, 0.867, 0.933 (k 4–8), 1.0 (k 9–10). Lexical candidates per query: q1 3, q2 1, q3 0, q4 2, q5 3 |
| K4 | Labels built only from the lexical top 3 (one-retriever pool), scored at k = 4 | Pooled relevant: q1 d01 · q2 d04 · q3 none · q4 d09 · q5 d10 (full: q1 d01, d03, d09 · q2 d04, d05 · q3 d07 · q4 d09 · q5 d10). **Lexical:** mean P@4 0.433 full = 0.433 pooled; mean recall 0.567 full → 1.000 pooled. **MiniLM:** mean Judged@4 0.350 (of 4 slots); mean P@4 **0.350 full → 0.200 pooled**; mean recall 0.933 full → 1.000 pooled. q1 MiniLM top 4 = d02, d01, d04, d03: 2 of 4 judged; P@4 0.500 → 0.250 (d03 unjudged, so counted as not relevant). Pooled recall is averaged over the 4 queries that have a pooled relevant doc (q3 has none) |
| K5 | 06 §6.7 draft seeds: evidence spans → relevant windows (91 windows of 1,000 chars, step 800; `any_overlap` on non-whitespace characters; window ids 0-based) | D-001 [7] · D-002 [25, 26] · D-003 [63, 64] · D-004 [22, 63] (alternatives: p.8 → 22, p.23 → 63) · D-005 [2, 3, 4] (group 1 → 2, 3; group 2 → 3, 4) · D-006 [20] · D-007 [25, 26, 79] · D-008 [64] · D-009 [] · D-010 []. Seeds are `llm-draft` (06 §6.7): illustration only |
| K6 | κ on IIR Table 8.2 (counts yes-yes 300, yes-no 20, no-yes 10, no-no 70; confirmed on the IIR §8.5 page 2026-10-18) | P(A) 0.9250; P(relevant), pooled marginals, 0.7875; P(E) 0.6653; **κ 0.7759**; Cohen's κ with separate marginals (scikit-learn 1.9.1) 0.7761. IIR prints 0.776 (and P(relevant) 0.7878, a rounding slip: 630/800 = 0.7875) |

## 2. CITED, DERIVED and UNVERIFIED

| Item | Status |
|---|---|
| O1-Q04 = 0; O1-TR1 "similarity matrix"; confidence-3 answers averaged 1.1 / 4 | CITED: `progress/session_log.md`, session 2026-10-08 #1 |
| Book numbers 0.6 (3 of 5) and 0.3 (3 of 10) | CITED: Ch22 p.4–5/19 (checked by S-src) |
| 8 of 50 pairs relevant; 1/3 → 2/6 for MiniLM q1; Day-7 item (2/3, 2/3, rank 1) | DERIVED from S7–S8, shown in the lesson |
| Whether the `reliable_rag` cell 14 grader would mark d02 or d08 relevant | UNVERIFIED (no API calls) |
| Pooling in IR test collections; which IIR chapters cover the inverted index | Now verified (2026-10-17/18, external): IIR §1.1–1.3 (incidence matrix, inverted index, Boolean merge) and §8.5 (pooling, κ); see `study/research/phase_01_prerequisites.md`, Concept P2 sources [P2-1]–[P2-8]. The toy pool effect is measured in K4 |
| How often similar-but-irrelevant chunks occur on the real corpus | UNVERIFIED (needs M1 labels) |

## 3. Lab test (`labs/P2_ir_framing_lab.ipynb`)

- Executed every code cell in order in a real Jupyter kernel (`jupyter_client`, project `.venv`), with the learner and prediction cells replaced by a **throwaway solution kept outside the workspace** (session scratchpad; not committed anywhere).
- **Good solution: 8/8 CHECK cells pass.** Its labels in Task 5 deliberately differ from the reference on one pair; the check reported 49/50 agreement and listed `q1:d09`.
- **Broken solution** (one typical mistake per task: `split()` tokenizer, duplicate postings, AND as union, constant overlap scores, a 2-word justification, a fixed denominator in precision, recall@6 on the top 3, a case-sensitive lookup): **0/8 pass**, each with a readable message.
- The saved notebook has no outputs and no solution code (8 learner cells hold only a placeholder comment; the Task 5 cell holds an empty template).

## 4. Notes for 04 and 02 (not edited; recorded here)

- **04 P2 row, book:** cites only Intro p.1/8 and Ch1 p.1–3/14 (motivation). The P2 content is in Ch3 p.1/14, Ch13 p.1–2/13, Ch22 p.4–7/19, Ch22 p.12/19 and Ch12 p.3/14.
- **04 P2 row, gap column:** relevance labels are described in Ch22 p.12/19 (queries paired with expected relevant documents) and the set-vs-ranking split in Ch22 p.6/19; only the inverted index is truly absent.
- **04 P2 row, "not in repo":** true for inverted index and qrels; but `reliable_rag.ipynb` cell 14, `define_evaluation_metrics.ipynb` cell 9 and `evaluation_deep_eval.ipynb` cell 6 define relevance operationally (LLM-judged) and are worth reading.
- **02 P2 card:** "no IR framing" in the book is too strong (Ch22 p.4–7/19, p.12/19). Ext #7, #9 (IIR ch.6–7) do not cover building an inverted index (believed IIR ch.1–2; UNVERIFIED).
