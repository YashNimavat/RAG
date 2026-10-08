# Misconception log (format: [05 §6.3](../05_LEARNING_AND_RETENTION_SYSTEM.md#63-progressmisconception_logmd-template))

A misconception is closed only when two check items score ≥ 3 on different days, unassisted.

## MC-001 — Tokens = characters; "tokens are decided by the embeddings"
- **Concept:** P1 (prerequisite involved: none)
- **Opened:** 2026-10-08, detected by item O1-Q01 (session 2026-10-08 #1)
- **Learner's statement (paraphrased):** "A token is decided by the embeddings; a 1,000-character chunk split by characters is 1,000 tokens."
- **Correct model:**
  - The model's **tokenizer** (BPE / WordPiece) defines tokens. The embedding model only maps token IDs to vectors.
  - Characters per token depend on the tokenizer and the corpus. On the repo's climate PDF it measured 5.57 (cl100k) and 6.20 (WordPiece) ([07 D.5](../07_SAMPLE_LESSON.md#d5-units-characters-tokens-and-tokens)).
  - The embedding model reads at most `max_seq_length` tokens and silently drops the rest (07 D.6).
- **Root-cause type:** unit-confusion
- **Severity:** high (blocks C2/C3 sizing decisions)
- **Remediation:** P1 lesson (tokenization lab: count the tokens of one page with two tokenizers); 07 Part D.5–D.6
- **Check items:** P1 recall item on tokenizer vs embedder; 07 C2 Part A PK-2/PK-3
- **Status:** open

## MC-002 — Missing query-embedding step; "similarity matrix"
- **Concept:** C4 (prerequisite involved: P4)
- **Opened:** 2026-10-08, detected by item O1-TR1
- **Learner's statement (paraphrased):** "The system finds vectors close to it by a similarity matrix like cosine."
- **Correct model:**
  - At query time the **question is embedded with the same model** used for the chunks.
  - A similarity **score** (cosine = dot product of normalised vectors) is computed between the query vector and each chunk vector, and the top-k are returned.
  - A "similarity matrix" means all-pairs scores, which retrieval does not compute.
- **Root-cause type:** terminology + prerequisite-gap (P4)
- **Severity:** medium
- **Remediation:** P4 lesson (hand-compute cosine); P5 NumPy top-k lab
- **Check items:** P4 application (cosine by hand); C4 code item (`top_k`)
- **Status:** open

## MC-003 — Prompt construction confused with chunk overlap (index time vs query time)
- **Concept:** C5 (prerequisite involved: P7)
- **Opened:** 2026-10-08, detected by item O1-Q07 (part 1)
- **Learner's statement (paraphrased):** "To build the prompt from 4 chunks, overlap words so the chunks stay connected."
- **Correct model:**
  - Overlap is an **indexing-time** chunking setting.
  - Prompt construction happens at **query time**: an instruction (answer only from the context; cite IDs; say "I don't know" when the context is insufficient), plus numbered context blocks labelled `[doc:page]`, plus the question, within a token budget.
- **Root-cause type:** prerequisite-gap (P7), conflation of pipeline stages
- **Severity:** high (blocks C5 / v0 citations)
- **Remediation:** P7 lesson; C5 lab (write the prompt template); blank-page reconstruction with index/query split
- **Check items:** P7 recall (parts of a grounded prompt); C5 application (build the prompt for 4 given chunks)
- **Status:** open

## MC-004 — "Lost in the middle" linked to local vs global minima
- **Concept:** P7 (prerequisite involved: none)
- **Opened:** 2026-10-08, detected by item O1-Q07 (part 2)
- **Learner's statement (paraphrased):** "It's hard to find small things in large text, like local minima vs global minima in gradient descent."
- **Correct model:**
  - Long-context LLMs use information placed in the **middle** of the context less reliably than information at the **beginning or end** (Liu et al. 2023, Source C #39, external).
  - Implication: put the strongest evidence at the edges, and keep the context lean.
  - It is unrelated to optimisation minima.
- **Root-cause type:** over-generalisation / wrong association
- **Severity:** medium
- **Remediation:** P7 lesson (read the paper's position-curve figure; reorder exercise)
- **Check items:** P7 recall; X3 application (order 4 chunks for a budget)
- **Status:** open

## MC-005 — "Sending more chunks is not good" (one-sided k trade-off)
- **Concept:** C4 (prerequisite involved: P6, P7)
- **Opened:** 2026-10-08, detected by item O1-TR2
- **Learner's statement (paraphrased):** "A parameter controls it; more chunks is not good."
- **Correct model:**
  - **k** trades evidence recall (more chunks → more chance the evidence is present, CE@k) against noise, cost, latency and dilution of the evidence.
  - The right k is measured on an eval set, ideally also at an equal token budget.
- **Root-cause type:** over-generalisation
- **Severity:** medium
- **Remediation:** C4 lab (sweep k on toy data; plot Recall@k vs context tokens); 07 Part I equal-budget idea
- **Check items:** C4 transfer (choose k for a new corpus with a reason); P6 application
- **Status:** open

## MC-006 — Fixed LLM-score thresholds blamed on chunking; calibration unknown
- **Concept:** V2 / A2 (prerequisite involved: M3)
- **Opened:** 2026-10-08, detected by item O1-Q11
- **Learner's statement (paraphrased):** "Fixed thresholds are fine; the problem is when the data or chunking is complicated. I'd do multiple runs and then decide."
- **Correct model:**
  - An LLM-emitted 0–1 score is **uncalibrated**: its meaning depends on the model and the prompt.
  - Thresholds must be chosen on a **labelled dev set** (false-positive and false-negative rates), confirmed once on test, and re-checked when the model or prompt changes ([06 §8.4](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#84-calibration-against-human-labels)).
  - Repeated runs measure variance, not calibration.
- **Root-cause type:** prerequisite-gap (M3)
- **Severity:** medium (relevant from Phase 8; blocks nothing before then)
- **Remediation:** M3 lesson (pilot labels); V2/A2 lessons
- **Check items:** M3 transfer; V3 application (choose a threshold on dev)
- **Status:** open
