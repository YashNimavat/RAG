# P3 gap audit: how the lesson's contents were chosen

**What this is:** the check I ran before rewriting P3, so you can judge the method. Every idea the lesson needs had to be found and taught; none of it was optional.
**What this is not:** the lesson itself. That is [P3_bm25.html](P3_bm25.html) (open it from the study kit: P3 → step 1).

## The method, in five steps

1. **Collect every idea the topic uses.** Sources: the book pages (Ch12 p.1–14, the glossary, Ch13 p.5), the old short and full P3 files, the lab tasks, and all 18 quiz questions, including their key points and wrong answers.
2. **For each idea, ask two questions.** Is it taught *before* it is used? And by which concept does it belong (P1, P2, P4, C2, P6)? Your progress file says whether you have studied that concept.
3. **Classify each idea.**
   - **Core:** this concept's own idea; taught in full.
   - **Bridge:** needed here, but it belongs elsewhere; taught briefly, in the place it is needed.
   - **Next topic:** only a link.
4. **Check the quiz.** Every key point of every question must be taught in the lesson, and in **Short** mode too, because the quiz is the same for both depths.
5. **Check the facts.**
   - Every number is matched against the measured facts file.
   - Every book page is opened and checked.
   - No 15 or more consecutive words are copied from the book (the longest shared run is 8 words).

## What step 2 found: 12 gaps in the old P3 files

| # | Idea | Where P3 uses it | Before | Now in the lesson |
|---|---|---|---|---|
| 1 | **Inverted index** (what "the BM25 index" is; df = the length of a word's list) | book: "build a BM25 index", storage cost | not taught anywhere in P3 (only P2, which you haven't studied) | §3, with an index explorer (Short) |
| 2 | **Dense search**: embeddings and vectors, and why a rare code gets blurred | §1 compares "dense rank 4" with "BM25 rank 1"; pre-test question 1 | one sentence | §2 bridge (Short) |
| 3 | **How `ln` behaves** (0 at 1, negative below 1) | why the idf turns negative, the floor, "exactly half gives 0" | not taught | §4 "the one piece of maths" (Short) |
| 4 | **Score vs relevance**; scores comparable only within one question | quiz T-03; "never use a fixed threshold" | Full lesson only | §11 (Short) |
| 5 | **Measuring**: Hit@k, MRR, Recall@k, CE@k, results per question type | MRR used in a caveat; quiz T-01, T-02 and T-03 expect it in their answers | **used but never taught** | §12 (Short: Hit@k and MRR; Full: Recall@k, CE@k, per-type results) |
| 6 | **Sparse vs dense, lexical**, and what "BM25" stands for | interview vocabulary; R1's title | not taught | §2 (Short) |
| 7 | **Stop words** | the old lesson's debugging fix ("stop-word removal") | used, never defined | §7 and §9 (Full) |
| 8 | **Stemming** | quiz T-02 and T-03 wrong answers | example only | §9, defined (Full) |
| 9 | **Code identifiers** (`getUserId`, `ERR_CONN_RESET`, `v2.10.3`) | quiz T-01 and T-02 | only in the questions | §9 "two identifier traps", plus the playground (Short) |
| 10 | **Top-k, collection, overlap** | throughout | used, never defined | defined where first used (§3, §10) |
| 11 | **BM25 tokens vs LLM tokens** | your open mix-up MC-001 | one line | §9, highlighted note (Short) |
| 12 | **What comes next** (hybrid, reranking) | quiz T-03: "combine with dense" | not linked | §13, one paragraph each and a link to R1 |

Ideas that were already taught well stayed, rewritten for clarity: tf, df, idf, TF-IDF, the BM25 formula, k1, b, the idf floor, the tokenizer trap, the effect of overlap, and the repo's zero-score fallback.

## What step 4 found: the quiz against the lesson

All 18 questions are now answerable from the lesson. The check caught **5 more gaps in Short mode**, which I fixed:

| Question | Needs | Was | Fix |
|---|---|---|---|
| P3-A-01, P3-A-05 (compute a score) | a worked computation | Full only | "One score by hand" moved into Short (§6) |
| P3-R-02 | the ceiling idf × (k1 + 1) | Full only | one sentence added under the chart (§6) |
| P3-R-03 | at b = 0, K = k1 for every chunk | missing | added to the wrong-ideas box (§6) |
| P3-T-01, P3-T-02 | the version/error-code conflict, and splitting function names | Full only | "Two identifier traps" moved into Short (§9) |
| P3-PRE-03 | k1 = 0 means "present or absent" | missing | added (§6, Full; it is a wrong-answer option, not a key point) |

| Question | Taught in |
|---|---|
| P3-PRE-01, P3-R-04, P3-A-04, P3-PRE-05 | §1, §2, §9 |
| P3-PRE-02, P3-R-01 | §4, §7 |
| P3-PRE-03, P3-R-02, P3-A-02 | §6 (chart and readout) |
| P3-PRE-04, P3-R-03, P3-A-03 | §6 (length table; Full: length chart) |
| P3-A-01, P3-A-05 | §6 formula and "one score by hand", §7 idf |
| P3-T-01, P3-T-02 | §9 traps and playground, §12 measuring |
| P3-T-03 | §2, §11, §12, §13 |
| P3-R-05 (interview) | §2, §6, §9 |

## Left to other concepts on purpose (link only)

- **Merging BM25 with dense search** (normalisation, RRF): R1.
- **Reranking**: R3.
- **How embeddings are trained or compared**: P4 and C4.
- **Building and freezing a labelled question set**: M1.
- **CE@k in depth**: P6 and M2.

P3 only needs to know these exist and why.

## If you like this approach: the checklist for every topic

1. List every idea from the book pages, the lesson files, the lab and the questions.
2. Mark each one: taught before use? Which concept owns it? Have you studied that concept?
3. Teach the core fully, teach bridges briefly where they are needed, and link next topics.
4. Check every quiz key point against **Short** mode.
5. Check every number against the facts file, every book page, and the 15-word copyright limit. Then test the page: its numbers, its controls, and that it works offline.
