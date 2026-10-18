# P2 gap audit: how the lesson's contents were chosen

**What this is:** the check run before writing the P2 lesson, so you can judge the method. Every idea the lesson needs had to be found and taught; none of it was optional.
**What this is not:** the lesson itself. That is [P2_ir_framing.html](P2_ir_framing.html) (open it from the study kit: P2 → step 1). The full research behind it is `study/research/phase_01_prerequisites.md`, "Concept P2".

## The method, in five steps

1. **Collect every idea the topic uses.** Sources: the book pages (Ch1 p.8/14, Ch3 p.1/14, Ch12 p.3/14, Ch13 p.1–2/13 and p.9/13, Ch22 p.4–7/19 and p.12/19, App p.20/23), the old full lesson `concepts/P2_ir_framing.md` and its lab, the 17 quiz questions with their key points and wrong answers, the repo cells, and outside sources (the *Introduction to Information Retrieval* textbook chapters 1 and 8, BEIR, Saracevic's relevance review).
2. **For each idea, ask two questions.** Is it taught *before* it is used? Which concept owns it (P2, P3, P4, P6, M1, M2, R3)? Your progress file says every Phase 1 concept is `not_started`, so their ideas count as not yet learned.
3. **Classify each idea.**
   - **Core:** P2's own idea; taught in full.
   - **Bridge:** needed here, but owned elsewhere; taught briefly, in the place it is needed.
   - **Next topic:** only a link.
4. **Check the quiz.** Every key point of every question must be taught in the lesson, in **Short** mode too, because the quiz is the same for both depths.
5. **Check the facts.**
   - Every number is matched against the measured facts file (`sources/verification/P2/P2_FACTS.md`, S1–S11 and the new K1–K6).
   - Every book page was opened and checked.
   - No 15 or more consecutive words are copied from the book.

## What step 2 found: 12 gaps in the old P2 files

| # | Idea | Where P2 uses it | Before | Now in the lesson |
|---|---|---|---|---|
| 1 | **One query can hide two needs**; judge against the need | every label | a definition table, no example | step 1, with an ambiguous query (Short) |
| 2 | **Three meanings of "relevance"** (score, topic, usefulness), and the book's other uses of the word | the book's Ch22, App, the repo | missing | step 4, a 3-row table (Short); Saracevic's five kinds (Full) |
| 3 | **A query-time LLM grader is a filter, not a label** | the repo's `reliable_rag` grader | the filter only | step 4 (Short); LLM-written labels are judges under D-10 (Full) |
| 4 | **Dense retrieval in two sentences** | the MiniLM comparison throughout | used before P4, no bridge | step 2 (bridge) |
| 5 | **The incidence matrix** as the picture behind the index | why the index is inverted | missing | step 5, the five words of q1 (Short) |
| 6 | **Ties need a rule, and the rule changes a metric** | lab Task 4 (rule given, never explained) | missing | step 7, a toggle on q4: rank 2 or 1 (Short) |
| 7 | **Recall as k grows; the candidate cap** | the k = 3 → 6 item | two values only | step 8, recall@k curves for k = 1–10 (Short) |
| 8 | **Accuracy is useless; recall needs the number of relevant documents** | set metrics | formulas only | step 8 (Short) |
| 9 | **Unjudged = not relevant, and pool bias** | every metric, M1, R1 | missing (pooling marked UNVERIFIED) | step 10: a pool demo on the toy and BEIR's measured numbers (Short) |
| 10 | **Labels are noisy; κ** | 06 §6.5 self-agreement | a link only | step 10: one sentence (Short); the formula and IIR's worked example (Full) |
| 11 | **Labels from spans, chunk relevance derived by overlap** | M1, M2, 06 §7.2 | stated, never worked | step 11: the draft seeds on the 91 windows (Short) |
| 12 | **The test collection** (about 50 needs; dev and test) | 06 §6, M1, M4 | missing | step 12 (Short) |

Ideas that were already taught well stayed, rewritten for clarity: the toy collection and guideline v1, the echo (d02) and the stuffed footer (d08), vocabulary mismatch (q3), the inverted index and Boolean AND/OR, runs A/B/C, the candidate cap, the PDF index facts, and the repo's `rank_bm25` scan.

## What step 4 found: the quiz against the lesson

All 17 questions are answerable from the lesson's **Short** mode and from the short reading file. Checking every key point caught **9 more gaps in Short mode**, which were fixed in both:

| Question | Needs | Was | Fix |
|---|---|---|---|
| P2-R-06 (why judge against the need) | a concrete query with two needs | an abstract example | step 1: `carbon dioxide` (what puts it in the air: d01; what takes it out: d06) |
| P2-A-02 (label q2) | a worked row of labels and the ten texts | the heat table only | step 3: the q2 row explained; the texts in step 6 |
| P2-A-01 (write `build_index`) | the index build in code | prose only | step 5: a six-line sketch |
| P2-PRE-02 (the back of a book) | "organised by word, not by page" | missing | step 5, with the book's cookbook index (Ch12 p.3/14) |
| P2-A-04 (AND, OR, postings read) | merge cost O(x + y) and "smallest df first" | Full only | moved into step 6 Short |
| P2-A-06 (tie rule flips) | how the scoring tool treats ties | Full only | step 7 Short |
| P2-R-04 (set vs rank) | a worked accuracy example | one sentence | step 8: 42 of 50 pairs "right" by returning nothing |
| P2-A-05, P2-R-05, P2-T-02 (holes) | recall overestimated; the bounds check; judging holes blind; Hole@4 | partly | step 10: three bullets and Hole@4 = 0.650 |
| P2-T-01 (a team with no labels) | κ and its thresholds; small sets compare but do not certify | Full only | step 10 (κ formula and thresholds in Short) and step 12 |

| Question | Taught in (lesson step) |
|---|---|
| P2-PRE-01, P2-R-01 | 1, 2 |
| P2-R-06 | 1 |
| P2-R-02 | 3, 10 |
| P2-A-02 | 3, 6 |
| P2-PRE-02, P2-R-03, P2-A-01 | 5 |
| P2-A-04 | 6 |
| P2-A-06 | 7, 9 |
| P2-A-03 | 2, 8 |
| P2-R-04 | 8, 9 |
| P2-R-05, P2-A-05, P2-T-02 | 10 |
| P2-T-01 | 3, 10, 12 |
| P2-R-07 (interview) | 3, 10, 11, 12 |

## Left to other concepts on purpose (link only)

- **Weights for words (tf, idf, BM25):** P3.
- **Vectors and cosine in depth:** P4.
- **Hit@k, MRR, nDCG and the course's main metric, CE@k:** P6.
- **Building and freezing the labelled set; the harness that reports Judged@k:** M1 and M2.
- **Diversity and duplicates (marginal relevance):** R4.

P2 only needs to know these exist and why.

## Errors found in the old files (recorded, not edited)

- The 02 P2 card says the book has "no IR framing"; Ch22 p.4–7/19 and p.12/19 teach precision, recall, rank metrics and labelled test sets. Only the inverted index and Boolean search are truly absent.
- The 02 card and 04 say the repo has no IR framing; `evaluation/open-rag-eval-example.ipynb` cells 0, 4, 5, 7 use a BEIR dataset, a TREC-style evaluator and a 0–3 relevance scale.
- The 02 card points P2 to the IR textbook's chapters 6–7; P2's content is in chapters 1 and 8.
- The 02 card cites Ch1 p.8–9/14 for top-K; it is on p.8/14 and p.10/14.
- The old lesson marked pooling as UNVERIFIED and never explained its tie rule or what the recall denominator assumes.

These are in the research file's error table (E1–E14) for a later correction pass.
