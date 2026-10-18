# P5 gap audit: how the lesson's contents were chosen

**What this is:** the check behind the P5 HTML lesson, so you can see why each part exists. Every idea the lesson needs had to be found and taught; none of it was optional.
**What this is not:** the lesson itself. That is [P5_vector_search.html](P5_vector_search.html) (open it from the study kit: P5 → step 1). The full research is in `study/research/phase_01_prerequisites.md`, Concept P5.

## The method, in five steps

1. **Collect every idea the topic uses.** Sources:
   - the book pages (Ch1 p.6–10/14 and p.13/14, Ch2 p.9/11, and the glossary at App p.16/23, p.21–22/23);
   - the old full lesson `concepts/P5_vector_search.md` and its lab;
   - the repo cells it cites (`helper_functions.py` L74, `simple_csv_rag` cells 12 and 16, `dartboard` cells 9, 13 and 23);
   - the FAISS paper and wiki, the HNSW paper, hnswlib, pgvector, ANN-Benchmarks and LangChain's source;
   - all 18 quiz questions.
2. **For each idea, ask two questions.** Is it taught *before* it is used? Which concept owns it (P4, P5, P6, C3, C4, R2, R4, D2, D3)? Your progress file says whether you have studied that concept.
3. **Classify each idea.**
   - **Core:** taught in full.
   - **Bridge:** taught briefly, where it is needed.
   - **Next topic:** a link only.
4. **Check the quiz.** Every key point of every question must be taught in **Short**.
5. **Check the facts.**
   - Every number is matched against the measured facts file (`P5_FACTS.md`, S1–S8 and the new K1–K14).
   - Every book page is opened.
   - No run of 15 or more words is copied from the book.

## Two changes from the research blueprint

**The running example.** The old lesson used 91 plain windows. The phase plan decided that every new retrieval example uses v0's **97 chunks**, the same chunks as P3, P4 and R1. So every chunk-dependent number was measured again (`p5_kit_measure.py`, K1–K14). Lines that are not timings are byte-identical on a rerun. D-002's evidence is now at rank 3, only 0.000081 above rank 4, which shows near-ties on real data without making any up. The old lab still uses the 91 windows, and the lesson says so.

**faiss was installed** (your decision, 2026-10-18): `faiss-cpu==1.15.1` in the optional `ann` group. So the ANN parts are measured, not described:
- real HNSW and IVF recall curves;
- filtered HNSW;
- the squared-L2 check;
- the library defaults, read from the objects themselves.

IVF is also built from scratch in NumPy, as the blueprint planned.

## What step 2 found: the gaps in the old P5 files

| # | Idea | Before | Now in the lesson |
|---|---|---|---|
| 1 | **The tie-aware cut** as a stated rule: take every id scoring ≥ the k-th score, sort by (−score, id), cut to k. Sorting only the k that `argpartition` picked is not enough | shown as a result, never stated; the old fix was the insufficient version | step 3 (Short: a toy strip with a k slider and a measured table of five variants) |
| 2 | **Library tie orders**: `InMemoryVectorStore` and faiss both put tied ids largest first | missing | step 3 (Short) and step 6's table |
| 3 | **Near-ties and float32**: a tie rule fixes exact equality only | number shown, meaning not drawn | step 3 (Full) |
| 4 | **Selectivity** and the estimate selectivity × fetch_k | not named | step 5 (Short) |
| 5 | **FAISS returns squared L2**; LangChain's relevance goes negative below cos 0.293 | marked UNVERIFIED | step 6 (Short): faiss run on the 97 chunks (K7) |
| 6 | **IVF mechanism**: k-means cells, nprobe, boundary misses, default nprobe 1 | one UNVERIFIED table row | step 8 (Short: a 2-D toy with sliders, measured recall on real windows) |
| 7 | **k-means** (needed by IVF; owned by no earlier concept) | missing | step 8 (a three-line bridge) |
| 8 | **HNSW mechanism**: layers, greedy descent, beam efSearch ≥ k; M and efConstruction | one UNVERIFIED table row | step 9 (Short: a stepping layer diagram, the knobs, the measured curve) |
| 9 | **Two meanings of "recall"**: ANN recall@k (overlap with exact) vs IR Recall@k (P6) | one word for both | step 10 (Short, a highlighted note) |
| 10 | **Recall vs latency** as one curve, and how ANN-Benchmarks measures it | missing | step 10 (Short: measured curve; Full: the LID caveat) |
| 11 | **Filtered ANN**: post-filter starvation inside an index, filter-aware search, exact on the subset | missing | step 11 (Short: measured on 100k synthetic vectors) |
| 12 | **What a store adds beyond an index**; the store is not the source of truth; persisted ANN indexes are fragile | partly | step 12 (Short table) |
| 13 | **Library defaults differ a lot** (faiss, hnswlib, pgvector) | missing | step 9 (Short: the three defaults that matter; Full: the full table) |
| 14 | **Book scale** (Ch2 p.9/11: linear growth, embedding cost is the bigger worry) | page not cited | step 7 and the book section |
| 15 | **p50/p95 with a named percentile method**, warm-up excluded, machine named | missing | step 7 (two sentences) |
| 16 | **Synthetic vectors mislead ANN tests** | missing | step 10 (Full); every synthetic number is labelled |
| 17 | **Bridges**: cosine = dot on unit vectors (P4), Hit@k and MRR (P6, not yet studied) | used without definition | steps 1, 6 and 10, one or two sentences each |

The old lesson sent ANN at scale to D4, which is security. The lesson now points to **D2** (latency budgets) and **D3** (index versioning and re-indexing), as the research found (error E6).

Ideas that were already taught well stayed, rewritten in the house style:
- one score per chunk (MC-002);
- `argpartition` then sort;
- rows and metadata, and the misalignment demo;
- pre- vs post-filter;
- the hidden defaults of LangChain's FAISS wrapper;
- the cost of exact search, and why k barely changes it;
- duplicates crowding the top k.

## What step 4 found: the quiz against Short

All 18 questions are answerable from Short; `p5_md_check.py` checks that each one's reread line names the section that teaches it.

| Questions | Taught in (Short) |
|---|---|
| PRE-01, R-01 | step 1 |
| A-01 | step 3 |
| A-05 | step 5 |
| R-02, A-06 | step 6 |
| PRE-02, A-02, A-03 | step 7 |
| R-03 | steps 8–10 |
| R-05 | step 9 |
| R-04, A-04 | step 10 |
| T-02 | step 11 |
| PRE-03, R-06 | step 12 |
| T-01, R-07 (interview, AIQ-04 Q8) | step 13 (with step 7) |

Not used anywhere in the kit files:
- the tutor-reserved interview question (AIQ-04 Q11);
- the coach's hidden P5 seed.

The tie-aware cut is taught and tested on toy arrays only. AIQ-04 Q20, Q21 and Q23 are not kit items, but the lesson makes them answerable (good self-practice after the course).

## Left to other concepts on purpose (link only)

- **Hit@k, MRR, Recall@k in full**, and the "recall" name table: P6.
- **The tie rule on string `chunk_id`s**, and the cut on the real index: C4.
- **Building and persisting the index with its manifest**: C3.
- **Filter selectivity in depth**: R2.
- **Diversity in the top k** (MMR, dartboard): R4.
- **Latency budgets and ANN at real scale**: D2. **Index versioning and re-indexing**: D3.
- **The framework version** (LangChain `InMemoryVectorStore`, traced): the LLMOps notebook, once `study/llmops/` exists.
