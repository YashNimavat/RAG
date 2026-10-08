# O1 diagnostic — coach-only bank (do not show the learner until each item is answered)

**Format:** blank-page reconstruction first (05 §5.5 rubric, 0–10), then 12 cold items asked one at a time.
- Grade each item 0–4 with the 05 §4.2 rubrics.
- Record the learner's confidence (1–3) before revealing anything.
- Do not correct in detail during O1. Note misconceptions and give a short "noted" reply. Full feedback comes at the end.

## Items

### Q1 · P1 · Recall
- **Ask:** What is a token? Roughly how many tokens is a 1,000-character English chunk, and why does that number matter for an embedding model?
- **Key:**
  - A token is a subword unit produced by the model's tokenizer.
  - The ratio is corpus- and tokenizer-dependent. The folk rule is ≈ 4 characters/token; the measured value on the climate PDF is ~5.6 (cl100k) and 6.2 (WordPiece).
  - It matters because the embedder has a max_seq_length, and text past it is silently truncated.
- **Misconceptions to probe:** "chunk_size is always tokens"; "a fixed 4 characters per token".

### Q2 · P4 · Application
- **Ask:** Compute the cosine of a = [1, 2, 2] and b = [2, 0, 1]. Then: for unit-length vectors, do ranking by L2 distance and ranking by cosine give the same order? Why?
- **Key:**
  - dot = 4; |a| = 3; |b| = √5 ≈ 2.236; cosine = 4 / 6.708 ≈ 0.596.
  - For unit vectors, ‖a − b‖² = 2 − 2·cos, which is monotone, so the rankings are identical (reversed direction: smaller distance = larger cosine).

### Q3 · P3 · Recall
- **Ask:** A user searches "HNSW ef_construction". Why might BM25 find the right chunk when a dense embedder does not? What do BM25's k1 and b control?
- **Key:**
  - Exact rare terms and identifiers get high IDF, while dense models may blur rare tokens.
  - k1 = term-frequency saturation.
  - b = document-length normalisation.

### Q4 · P6 · Application
- **Ask:** The ranked list is [N, R, N, R, N]; there are 2 relevant items in total. Compute Precision@3, Recall@3 and the reciprocal rank.
- **Key:** P@3 = 1/3 ≈ 0.333; R@3 = 1/2; RR = 1/2.

### Q5 · C2 / C3 · Recall
- **Ask:** You index a PDF. What metadata must each chunk carry, and what breaks if you store only the chunk text?
- **Key:**
  - doc_id, page(s), char offsets, chunk_id, chunker/params hash (and the snapshot/text hash).
  - Without them: no citations, no span-based evaluation, ambiguous index versions, and no dedup or ordering.
- **Fast-track probe:** C2 (chunking_lab).

### Q6 · C4 / P5 · Application (code)
- **Ask:** In plain Python + NumPy, write `top_k(q, M, k)`: q is a (d,) query vector, M is an (n, d) matrix of chunk vectors, and the function returns the indices of the k most cosine-similar rows.
- **Key:**
  - Normalise q and the rows of M.
  - `s = Mn @ qn`
  - `idx = np.argpartition(-s, k)[:k]`, then sort by score; or simply `np.argsort(-s)[:k]`.
  - Handle k > n and zero-norm rows.
- **Fast-track probe:** P5/C4 (my way 1_basic_rag, VAI L19/L20).

### Q7 · P7 / C5 · Recall
- **Ask:** You have 4 retrieved chunks. Describe how you build the prompt so that the answer is grounded and cites sources. What is "lost in the middle", and how does it affect your ordering?
- **Key:**
  - Numbered context blocks with [doc:page] ids.
  - Instructions: answer only from the context, cite ids, say "I don't know" when the context is insufficient.
  - Order by relevance: best evidence at the edges, not the middle.
  - Mind the token budget.

### Q8 · M2 / M3 · Recall + Transfer
- **Ask:** Give one example where retrieval was perfect but the answer was wrong, and one where retrieval failed but the answer was right. How would you measure each separately?
- **Key:**
  - Perfect retrieval, wrong answer: a generator or faithfulness failure, e.g. it ignores the context or misreads a table.
  - Failed retrieval, right answer: parametric knowledge or luck.
  - Measure retrieval with gold evidence (CE@k/Recall@k, MRR) and answers with correctness and faithfulness. The two can disagree; a closed-book control helps separate them.

### Q9 · R1 · Application
- **Ask:** Dense ranks [A, B, C] and BM25 ranks [C, A, D]. Compute Reciprocal Rank Fusion with k = 60 and give the fused order. Why is min-max-normalised weighted score fusion fragile?
- **Key:**
  - A = 1/61 + 1/62 = 0.03252; C = 1/63 + 1/61 = 0.03227; B = 1/62 = 0.01613; D = 1/63 = 0.01587. Order: A > C > B > D.
  - Min-max is sensitive to outliers and score-distribution shape, and is unstable across queries.
  - Bonus: the arrays must be aligned by document (upstream fusion_retrieval cell 17 is not).
- **Fast-track probe:** VAI L23.

### Q10 · R3 · Recall
- **Ask:** Bi-encoder vs cross-encoder: how does each score a query–document pair? Why rerank only a candidate pool of, say, 50, rather than the whole corpus? What limits a reranker's ceiling?
- **Key:**
  - Bi-encoder: separate embeddings, then a dot product; precomputable.
  - Cross-encoder: joint forward pass per pair; more accurate, but cost scales with the pool size.
  - The ceiling is the recall of the candidate pool: a reranker can't bring back what wasn't retrieved.
- **Fast-track probe:** VAI L22.

### Q11 · V2 / A2 · Transfer
- **Ask:** In your CRAG notebook, an LLM grader returns a relevance score from 0 to 1, and you branch at 0.3/0.7. What is wrong with fixed thresholds on that score, and how would you set or validate them?
- **Key:**
  - LLM scores are uncalibrated and model/prompt dependent, so 0.3/0.7 is arbitrary.
  - Set the thresholds on a labelled dev set, check the false-negative/positive rates, confirm on test, and recalibrate whenever the model or prompt changes.
  - Web fallback breaks determinism and evaluation.
- **Fast-track probe:** my way CRAG.

### Q12 · Transfer (D4 / R2 / I5 / M5)
- **Ask:** A support bot over 300 product manuals often cites the wrong product version. Where in the pipeline could this come from? What are the first two things you would measure or try, in order?
- **Key:**
  - Causes: chunks lack product/version metadata or headers (I5); no metadata filter (R2); the query doesn't state the version (Q1 / clarification); near-duplicate distractors across versions.
  - First, measure: build an eval slice of version-specific questions with gold evidence, and check whether CE@k fails (retrieval) or the answer misreads.
  - Then try: version metadata plus filtering or contextual headers; possibly a clarifying question.
