<!-- kit:questions concept=I6 version=1 -->
# I6 questions: document augmentation and HyPE (index-time question generation)

**How to use:** write your answer and a confidence (1–3) first. Then open the answer and tick the key points you really wrote.

**Where the numbers come from:** `sources/verification/I6/i6_kit_measure.py` with MiniLM (`all-MiniLM-L6-v2`, rebuilt from an ONNX export in the build container, parity checked against P4) on v0's 97 chunks of the climate PDF ([I6_FACTS](../../sources/verification/I6/I6_FACTS.md) K1–K12; [kit run](../../sources/verification/I6/out_i6_kit_measure.txt)). The 970 generated questions are a **stand-in pack** written by Claude helpers who never saw the eval set; a Groq or Haiku replay pack will give different numbers. The draft seeds (D-001…D-010, 8 answerable) are LLM-drafted and not human-verified: they show the mechanism, not a winner. Book pages are per 04, not re-opened. "Toy" scores are made up. No API was called to write this file.

<!-- q id=I6-PRE-01 type=R set=pre -->
### I6-PRE-01 · Recall (before reading)
**Question:** Why might a question's vector not land near the passage that answers it?

**Reply template:** `Because a question is ____ and a passage is ____, so the question's vector sits near ____.`

<details><summary>Hint 1</summary>

Compare the form of "When was the treaty adopted?" with the form of the sentence that answers it.

</details>

<details><summary>Hint 2</summary>

What kind of text would an embedder place closest to a short question: a long statement, or another short question?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Questions and passages have different shapes. A question is short and asks; a passage is long and states. The embedder tends to put question-shaped text near other question-shaped text, so the answering passage can score lower than a passage that only looks like an answer (the book's asymmetry problem). Measured on D-002 ("In what year was the Paris Agreement adopted?"):

```
best chunk score      0.4606   (chunk 69, the wrong treaty; the right chunk 27 is rank 3)
best question score   0.9869   "When was the Paris Agreement adopted?" (a generated question of chunk 27)
generated questions nearer a sibling question than their own chunk:  859 of 970 = 0.886
```

**Key points** (a 3 needs every point):
- [ ] A question and its answering passage differ in shape (short and asking vs long and stating).
- [ ] So the question's vector can sit nearer other questions (or answer-shaped text) than the passage that answers it.

**For a 4, also:**
- [ ] Gives evidence and the limit: D-002's best chunk 0.4606 vs a generated question 0.9869 (or 0.886 of questions nearer a sibling question), and says it is a hypothesis to test on your own data, not a law.

**Common wrong answers:**
- [ ] "Because the embedder is bad": a good embedder still separates shapes; the right chunk is often in the top few, just not first.
- [ ] "The system compares the question with every chunk in a similarity matrix, and the matrix is noisy": search computes one score per stored vector, not a matrix (MC-002).

**If you missed it, reread:** [short §1](../reading/I6_doc_augmentation.md#1-questions-and-statements-embed-apart) · [lesson step 1](../lessons/I6_doc_augmentation.html#shape) · book Ch11 p.1/13 (per 04, not re-opened)

</details>
<!-- /q -->

<!-- q id=I6-PRE-02 type=R set=pre -->
### I6-PRE-02 · Recall (before reading)
**Question:** If questions are written for each chunk when the index is built, how many LLM calls does a user's query add?

**Reply template:** `____ extra calls, because ____.`

<details><summary>Hint 1</summary>

Draw two lanes: the index lane (runs once per rebuild) and the query lane (runs for every question). In which lane does the LLM write the questions?

</details>

<details><summary>Hint 2</summary>

What does the query lane do with the user's question before the answer model sees it? Does any step there need a generator?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Zero. The questions were generated in the index lane, one call per chunk at each rebuild, before any user arrived. The query lane is unchanged: embed the user's question, search the stored vectors, map the hits to unique parent chunks, and send those chunks to the answer model (that last call happens with or without I6). HyDE, the mirror image, would add one LLM call per query.

**Key points** (a 3 needs every point):
- [ ] Zero extra LLM calls per query.
- [ ] The generation happened at index time (one call per chunk per rebuild), not at query time.

**For a 4, also:**
- [ ] Contrasts HyDE: one extra LLM call per query, on the critical path, so it adds latency.

**Common wrong answers:**
- [ ] "One call per query, to write questions for the user's question": that is HyDE-like query-time generation, not I6.
- [ ] "The generated questions are added to the prompt, so the prompt gets longer": they never reach the prompt; generation and prompt building are different stages (MC-003).

**If you missed it, reread:** [short §2](../reading/I6_doc_augmentation.md#2-index-time-vs-query-time-who-pays-the-llm-call) · [lesson step 2](../lessons/I6_doc_augmentation.html#lanes) · book Ch11 p.9–10/13 (per 04, not re-opened)

</details>
<!-- /q -->

<!-- q id=I6-R-01 type=R set=main -->
### I6-R-01 · Recall
**Question:** What is stored in a multi-vector index, and what is returned to the answer model?

**Reply template:** `Stored: ____, each with ____. Returned: ____.`

<details><summary>Hint 1</summary>

Think of a table with one row per vector. What must each row carry so that a hit can be turned into something citable?

</details>

<details><summary>Hint 2</summary>

Several rows can point to the same chunk. What happens to them before the answer model sees anything?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** One vector per generated question (and, in the chunks + questions design, one per chunk), each stored with a pointer to its parent chunk: `vectors[i] → (kind, parent_id, question_text)`. At query time the hits are mapped to their parents, each parent scored by its best vector (`max`), duplicates removed in rank order, and the list cut to k. The answer model receives those k **parent chunks**, with their page and offsets, never the generated questions.

```
D-006 (n = 5): top 12 vectors = 11 questions + 1 chunk, 8 unique parents → returned parents 21, 64, 19, 32
```

**Key points** (a 3 needs every point):
- [ ] Stored: vectors for the generated questions (plus the chunk vectors in chunks + questions).
- [ ] Each vector carries a pointer to its parent chunk (parent_id).
- [ ] Returned: the unique parent chunks, cut to k, not the questions.

**For a 4, also:**
- [ ] Says how parents are ranked and checked: max over the parent's vectors, dedup before the cut, and CE@k computed on the parents' character spans.

**Common wrong answers:**
- [ ] "The matched questions are returned as context": a question holds no evidence; the parent chunk does.
- [ ] "A new, augmented chunk text is stored and returned": the parent is the unchanged v0 chunk; only extra vectors are added (that is the appended-text design, a different one).

**If you missed it, reread:** [short §5](../reading/I6_doc_augmentation.md#5-three-designs-one-parent-table) · [short §6](../reading/I6_doc_augmentation.md#6-search-the-vectors-return-unique-parents) · [short §7](../reading/I6_doc_augmentation.md#7-score-the-parents-span-never-the-question) · [lesson step 5](../lessons/I6_doc_augmentation.html#designs) · [lesson step 6](../lessons/I6_doc_augmentation.html#search) · [lesson step 7](../lessons/I6_doc_augmentation.html#score) · book Ch11 p.6–8/13 (per 04, not re-opened)

</details>
<!-- /q -->

<!-- q id=I6-R-02 type=R set=main -->
### I6-R-02 · Recall
**Question:** Name the three designs and the one thing each gives up.

**Reply template:** `1. ____ gives up ____. 2. ____ gives up ____. 3. ____ gives up ____.`

<details><summary>Hint 1</summary>

The designs differ only in which vectors exist for one chunk: the chunk's own vector, question vectors, or one vector made from both texts.

</details>

<details><summary>Hint 2</summary>

For each design ask: what does it cost in vectors, and what kind of query has nothing left to match?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

| Design | Vectors (97 chunks, n = 5) | Gives up |
|---|---|---|
| chunks + questions (doc-aug) | 582 | compactness: 6× the vectors, and duplicate parents crowd the top k |
| questions only (HyPE) | 485 | the chunk's own vector, so queries by number, code or exact term (rare-token retention 0.264) |
| questions appended to the chunk text (doc2query, LlamaIndex) | 97 | a separate question match: one vector mixes the statement and its questions |

**Key points** (a 3 needs every point):
- [ ] Chunks + questions: gives up size (n + 1 vectors per chunk; 582 at n = 5).
- [ ] Questions only: gives up the chunk vector, so keyword and number queries.
- [ ] Questions appended to the text: gives up a separate question vector (one blended vector per chunk).

**For a 4, also:**
- [ ] Picks a default with a reason: chunks + questions, because the chunk vector still catches queries that copy the document's words; or adds BM25 (R1) for exact terms.

**Common wrong answers:**
- [ ] "Questions only is strictly better because it removes the noisy chunk vectors": it loses the rare tokens; it matched A1 here only because the pack happened to name the exact terms.
- [ ] "Appending the questions makes the index bigger": it stays at 97 vectors; it changes what each vector means.

**If you missed it, reread:** [short §5](../reading/I6_doc_augmentation.md#5-three-designs-one-parent-table) · [short §8](../reading/I6_doc_augmentation.md#8-keyword-and-number-queries-the-guard) · [lesson step 5](../lessons/I6_doc_augmentation.html#designs) · [lesson step 8](../lessons/I6_doc_augmentation.html#guard) · book Ch11 p.6–8/13 (per 04, not re-opened)

</details>
<!-- /q -->

<!-- q id=I6-R-03 type=R set=main -->
### I6-R-03 · Recall
**Question:** Why must duplicates be removed before cutting to k?

**Reply template:** `Because ____. If you cut first, ____. So fetch ____, dedup ____, then cut.`

<details><summary>Hint 1</summary>

One chunk can own up to n + 1 vectors. What can the top 4 vectors look like when one chunk has several good questions?

</details>

<details><summary>Hint 2</summary>

Count unique parents after "cut to k vectors, then dedup" and after "dedup all hits, then cut to k parents".

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Several top vectors often belong to the same parent. Cut to k vectors first and the dedup leaves fewer than k parents. Fetch more vectors than you need (`K_vec ≥ k(n + 1)`, since each parent owns at most n + 1), keep each parent's first appearance in rank order, then cut to k.

```
toy, k = 3:   cut then dedup → [A, B]        dedup then cut → [A, B, C]
measured, n = 5: unique parents in the top 4 vectors, mean 3.00 over 8 seeds, min 2
```

**Key points** (a 3 needs every point):
- [ ] Several of the top vectors can map to one parent.
- [ ] Cutting first returns fewer than k unique parents.
- [ ] Oversample (K_vec ≥ k(n + 1)), dedup in rank order, then cut.

**For a 4, also:**
- [ ] Names a trap: `set()` keeps the members but loses the rank order; LangChain's default fetches 4 child vectors, so "k = 4" can return 2 parents.

**Common wrong answers:**
- [ ] "Duplicates don't matter, the answer model just sees the same chunk twice": the duplicates are removed anyway, so you silently get fewer chunks than k.
- [ ] "Dedup with set() at the end": the order is lost, so you cannot cut to the best k.

**If you missed it, reread:** [short §6](../reading/I6_doc_augmentation.md#6-search-the-vectors-return-unique-parents) · [lesson step 6](../lessons/I6_doc_augmentation.html#search) · book Ch11 p.8/13 (per 04, not re-opened)

</details>
<!-- /q -->

<!-- q id=I6-R-04 type=R set=main -->
### I6-R-04 · Recall
**Question:** When does index-time question generation pay its LLM calls, and when does HyDE?

**Reply template:** `Index time: ____ calls, paid ____. HyDE: ____ calls, paid ____. Index time is cheaper in calls when ____.`

<details><summary>Hint 1</summary>

One method writes questions for chunks; the other writes a fake answer for each query.

</details>

<details><summary>Hint 2</summary>

Count the calls per month for each: one depends on the number of chunks and rebuilds, the other on the number of queries.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Index-time generation pays N calls (one per chunk) at every rebuild, before any user asks, and adds 0 calls per query. HyDE pays one call per query, at query time, on the critical path (it adds latency to every answer). In calls, index time is cheaper when `Q_total > N × rebuilds`: for 97 chunks rebuilt twice a month, more than 97 × 2 = 194 queries a month.

**Key points** (a 3 needs every point):
- [ ] Index time: one call per chunk per rebuild (97 for v0), paid before queries arrive.
- [ ] HyDE: one call per query, at query time.
- [ ] Break-even: index time wins in calls when queries exceed N × rebuilds.

**For a 4, also:**
- [ ] Adds latency and the limit: I6 adds no LLM call to a query's path while HyDE adds one; but HyDE adapts to the real question while I6 must guess the questions in advance.

**Common wrong answers:**
- [ ] "Both pay at query time": I6 pays only at index time (MC-003: the stages are separate).
- [ ] "Index time is always cheaper because it is done once": a corpus rebuilt often with few queries pays more.

**If you missed it, reread:** [short §2](../reading/I6_doc_augmentation.md#2-index-time-vs-query-time-who-pays-the-llm-call) · [short §10](../reading/I6_doc_augmentation.md#10-what-it-costs-and-when-hyde-is-cheaper) · [lesson step 2](../lessons/I6_doc_augmentation.html#lanes) · [lesson step 10](../lessons/I6_doc_augmentation.html#cost) · book Ch11 p.9–10/13 (per 04, not re-opened)

</details>
<!-- /q -->

<!-- q id=I6-R-05 type=R set=review -->
### I6-R-05 · Recall
**Question:** Why are generated questions never scored as evidence or sent to the answer model?

**Reply template:** `Because a generated question is ____. Evidence is scored on ____, and the answer model gets ____.`

<details><summary>Hint 1</summary>

Who wrote the question, and does a question state any fact?

</details>

<details><summary>Hint 2</summary>

What does CE@k need from a retrieved item, and what does a citation need?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** A generated question is an LLM's guess about what the chunk answers. It states no fact, and it can be wrong about its own chunk: 58 of 970 questions did not find their own chunk in the top 10, and the lowest scored 0.0407 against it. It is only a pointer. Evidence coverage (CE@k) is computed on the parents' `[char_start, char_end)` spans, and the answer model gets the parent chunk text with page and offsets, so it can ground and cite. Because the returned unit is unchanged, the context size stays about the same (627.9 vs 671.0 tokens for k = 4).

**Key points** (a 3 needs every point):
- [ ] A generated question is model output (a guess), not source text, and may be hallucinated.
- [ ] Questions are pointers; evidence is scored on the parent chunk's span (CE@k).
- [ ] The answer model gets the parent chunk, so it can ground and cite page and offsets.

**For a 4, also:**
- [ ] Gives a measured sign of wrong questions (58 of 970 miss their own chunk in the top 10) or notes the HyPE notebook stores no metadata, which makes citation impossible.

**Common wrong answers:**
- [ ] "Sending the matched question helps the model understand the user": the user's own question is already in the prompt; a generated one adds unverified text.
- [ ] "If the question matched, the chunk must be right, so count the question as a hit": a hit counts only if the parent's span holds the gold evidence.

**If you missed it, reread:** [short §7](../reading/I6_doc_augmentation.md#7-score-the-parents-span-never-the-question) · [lesson step 7](../lessons/I6_doc_augmentation.html#score) · book Ch11 p.6–8/13 (per 04, not re-opened)

</details>
<!-- /q -->

<!-- q id=I6-R-06 type=R set=interview source=AIQ-04-Q45 -->
### I6-R-06 · Interview (Recall)
**Question:** "How do you build a golden evaluation set for RAG without months of labelling?"
*From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md` (question 45), Copyright (c) 2026 Om, MIT License.* Answer it, then say what it means for an index that already holds LLM-generated questions.

**Reply template:** `A golden set is ____. To build it fast, ____. Synthetic questions are risky because ____; with question generation in the index, that means ____, so I ____.`

<details><summary>Hint 1</summary>

Where do the eval questions come from, and where do the index questions come from? What happens if both are written the same way from the same chunks?

</details>

<details><summary>Hint 2</summary>

How would you measure whether an eval question already has a near-copy in the index, and which items would you trust for the decision?

</details>

<details><summary>Show answer (write yours first)</summary>

> **The repo's answer (excerpt, verbatim).** *From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md`, Copyright (c) 2026 Om, MIT License:*
>
> "A useful golden set is (query → relevant chunk IDs → optionally a reference answer), even just 100-300 rows. Bootstrap in layers:"
>
> "**Synthesise to fill gaps.** For each sampled chunk, have an LLM generate realistic questions it answers - instantly giving (query, gold chunk) pairs. Two corrections make or break synthetic sets: style-match the generator to real user phrasing (raw synthetic questions are too well-formed and echo the chunk's vocabulary, inflating retrieval scores - paraphrase them away from the source text), and filter with a judge model for answerability and naturalness. Use synthetic data to cover the long tail; never let it *replace* the mined-reality core, because you'd be evaluating on a distribution nobody queries."
>
> "**Engineer hard cases deliberately**: unanswerable questions (tests refusal), multi-hop questions needing 2+ chunks, ambiguous queries, exact-match queries (IDs, error codes - tests the lexical path), and near-duplicate distractor traps. These are where systems differ; easy questions saturate quickly."

**Our check of that answer:** the shape is right: a real-query core, synthetic questions only to fill gaps, and deliberate hard cases. Its "echo" warning is exactly the I6 leakage risk, and for an augmented index it is stronger than the repo says:
1. The index questions are synthetic questions too. The stand-in pack echoes its chunks (mean vocabulary echo 0.777; 227 of 970 questions use only chunk words), and LLM-drafted eval questions do the same, so the two meet inside the index: D-002 has a generated near-copy at 0.9869 ("When was the Paris Agreement adopted?"), D-004 at 0.9653, D-008 at 0.9368. Delete the 10 generated questions within τ = 0.7054 of a seed and A1's MRR@10 falls from 0.781 to 0.547, below the chunks-only 0.708.
2. "Paraphrase them away from the source text" and a judge filter do not detect this: the index questions are paraphrases as well. You have to measure each eval item's closeness to the index questions and decide on items that pass.

**Model answer:** A golden set is a list of queries, each with its relevant chunks (better: evidence spans) and optionally a reference answer. Build it fast from real queries (logs, tickets), judging a candidate pool instead of the whole corpus; add synthetic questions only for gaps, and add hard cases (unanswerable, multi-hop, exact terms). Synthetic questions echo their chunk's words and inflate retrieval scores. With index-time question generation that becomes leakage: the index already holds questions written the same way, so an eval question can retrieve its own near-copy. So I compute `leak(i)` (the best cosine of each eval question to any generated question, plus n-gram overlap), set τ from paraphrase pairs, report the flagged share and a de-leaked arm, and decide only on human-written plus unflagged items.

**Key points** (a 3 needs every point):
- [ ] A golden set = queries + their relevant chunks or spans (+ optionally a reference answer), with real queries as the core.
- [ ] Synthetic questions echo the chunk's vocabulary and inflate retrieval scores.
- [ ] With generated questions in the index this is leakage: an eval question can match its own near-copy.
- [ ] Measure it (leak(i) against the index questions, flag above τ) and decide on human-written plus unflagged items.

**For a 4, also:**
- [ ] Cites the measured effect: near-copies at 0.9869 / 0.9653 / 0.9368, and the de-leaked MRR@10 of 0.547 below the 0.708 baseline (the gain vanished), with τ only provisional (one paraphrase pair).

**Common wrong answers:**
- [ ] "Generate the eval questions with the same prompt as the index questions, that keeps them consistent": that maximises leakage.
- [ ] "The helpers never saw the eval set, so there is no leakage": no copying is needed; the same drafting habit produces the same questions.

**If you missed it, reread:** [short §4](../reading/I6_doc_augmentation.md#4-clean-then-check-every-question-against-its-own-chunk) · [short §9](../reading/I6_doc_augmentation.md#9-leakage-when-the-index-already-holds-the-eval-question) · [lesson step 4](../lessons/I6_doc_augmentation.html#clean) · [lesson step 9](../lessons/I6_doc_augmentation.html#leak) · book Ch11 p.6/13 (per 04, not re-opened; the book does not discuss leakage)

</details>
<!-- /q -->

<!-- q id=I6-A-01 type=A set=main -->
### I6-A-01 · Application
**Question:** For v0's 97 chunks at n = 5, how many vectors, LLM calls and float32 bytes at 1,536 dimensions does each design need?

**Reply template:** `chunks + questions: ____ vectors, ____ calls, ____ bytes; questions only: ____ vectors, ____ calls, ____ bytes.`

<details><summary>Hint 1</summary>

Chunks + questions keeps 1 chunk vector plus n question vectors per chunk; questions only keeps the n question vectors.

</details>

<details><summary>Hint 2</summary>

One call writes all n questions for a chunk. A float32 number takes 4 bytes, so one vector takes d × 4 bytes.

</details>

<details><summary>Hint 3</summary>

One vector at 1,536-d = 1,536 × 4 = 6,144 bytes. Multiply by the vector count.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
chunks + questions:  97 × (1 + 5) = 582 vectors     582 × 1,536 × 4 = 3,575,808 bytes
questions only:      97 × 5       = 485 vectors     485 × 1,536 × 4 = 2,979,840 bytes
calls: 97 in both designs (one call per chunk writes all 5 questions)
self-check: 3,575,808 / (97 × 6,144) = 6, the same 6× as the vectors; v0's index (C3) is 596,096 bytes
```

**Key points** (a 3 needs every point):
- [ ] 582 vectors (chunks + questions) and 485 (questions only).
- [ ] 97 calls in both designs (one per chunk, not one per question).
- [ ] 3,575,808 bytes and 2,979,840 bytes.

**For a 4, also:**
- [ ] A self-check: the bytes grow by the same factor as the vectors (6× and 5× of v0's 97 vectors), and v0's own index is 596,096 bytes.

**Common wrong answers:**
- [ ] "485 calls, one per question": one call returns all n questions for a chunk.
- [ ] "The appended-text design also needs 582 vectors": it keeps one vector per chunk, 97.

**If you missed it, reread:** [short §5](../reading/I6_doc_augmentation.md#5-three-designs-one-parent-table) · [short §10](../reading/I6_doc_augmentation.md#10-what-it-costs-and-when-hyde-is-cheaper) · [lesson step 5](../lessons/I6_doc_augmentation.html#designs) · [lesson step 10](../lessons/I6_doc_augmentation.html#cost) · book Ch11 p.6–8/13 (per 04, not re-opened)

</details>
<!-- /q -->

<!-- q id=I6-A-02 type=A set=main -->
### I6-A-02 · Application
**Question:** Rank the three parents X, Y and Z by max and by sum, and say which parent wins only because it has more vectors.

**Data** (toy, made-up scores; 8 vectors in rank order):

```
vector  parent  kind      score
v1      Y       question  0.78
v2      Z       question  0.71
v3      Z       chunk     0.69
v4      Z       question  0.67
v5      X       question  0.64
v6      Z       question  0.62
v7      X       chunk     0.58
v8      Y       chunk     0.40
```

**Reply template:** `max: ____, ____, ____. sum: ____, ____, ____. ____ wins under sum only because ____.`

<details><summary>Hint 1</summary>

First group the eight scores by parent. Count how many vectors each parent owns.

</details>

<details><summary>Hint 2</summary>

Max keeps each parent's single best score; sum adds all of them up. Compute both for X, Y and Z.

</details>

<details><summary>Hint 3</summary>

Z owns v2, v3, v4 and v6: its best is 0.71, its sum is 0.71 + 0.69 + 0.67 + 0.62.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
parent  vectors  max    sum
X       2        0.64   0.64 + 0.58 = 1.22
Y       2        0.78   0.78 + 0.40 = 1.18
Z       4        0.71   0.71 + 0.69 + 0.67 + 0.62 = 2.69
max: Y, Z, X        sum: Z, X, Y
```

Z wins under sum only because it owns 4 vectors; no single Z vector beats Y's best match (0.78). Y holds the best match of all and falls to last under sum. That is why the default parent score is max: sum rewards parents with more vectors (on the seeds, sum gave MRR@10 0.760 against max's 0.781).

**Key points** (a 3 needs every point):
- [ ] max: Y, Z, X.
- [ ] sum: Z, X, Y.
- [ ] Z wins under sum because it has 4 vectors, not because any of its matches is best.

**For a 4, also:**
- [ ] Says which to use and why: max (or RRF, R1) by default, since sum is biased toward parents with more vectors; and notes that each parent's top vector, in rank order, is exactly what dedup keeps.

**Common wrong answers:**
- [ ] "Z is the most relevant because it matched four times": four questions about one chunk say how many were generated, not how relevant it is.
- [ ] "max: Y, X, Z": Z's best (0.71) beats X's best (0.64).

**If you missed it, reread:** [short §6](../reading/I6_doc_augmentation.md#6-search-the-vectors-return-unique-parents) · [lesson step 6](../lessons/I6_doc_augmentation.html#search) · book Ch11 p.8/13 (per 04, not re-opened)

</details>
<!-- /q -->

<!-- q id=I6-A-03 type=A set=main -->
### I6-A-03 · Application
**Question:** For 97 chunks, how many queries a month must arrive before index-time generation uses fewer LLM calls than HyDE, if you rebuild twice a month and if you rebuild every day?

**Reply template:** `twice a month: more than ____ queries a month; daily: more than ____ a month (about ____ a day).`

<details><summary>Hint 1</summary>

Index time pays N calls per rebuild; HyDE pays one call per query.

</details>

<details><summary>Hint 2</summary>

Break-even: Q_total > N × rebuilds. Take a month as 30 days for the daily case.

</details>

<details><summary>Hint 3</summary>

Twice a month: 97 × 2. Daily: 97 × 30.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
twice a month:  97 × 2  = 194 calls a month    → index time wins in calls above 194 queries a month
daily:          97 × 30 = 2,910 calls a month  → above 2,910 queries a month, i.e. more than 97 a day
```

Below those volumes HyDE uses fewer calls. Calls are not the only cost: index time adds 0 calls to a query's path while HyDE adds 1 to every query (latency). If the cache is keyed by chunk text, a rebuild regenerates only the changed chunks, which lowers the index-side count.

**Key points** (a 3 needs every point):
- [ ] Break-even rule: queries > N × rebuilds.
- [ ] Twice a month: 194 queries a month.
- [ ] Daily: 2,910 queries a month (97 a day).

**For a 4, also:**
- [ ] Names what the call count leaves out: HyDE's extra latency on every query, and that a text-keyed cache regenerates only changed chunks (so the real index-side count can be far below N per rebuild).

**Common wrong answers:**
- [ ] "97 queries, whatever the rebuild rate": each rebuild pays the 97 calls again.
- [ ] "485 queries, one per question at n = 5": calls are per chunk, not per question.

**If you missed it, reread:** [short §10](../reading/I6_doc_augmentation.md#10-what-it-costs-and-when-hyde-is-cheaper) · [lesson step 10](../lessons/I6_doc_augmentation.html#cost) · book Ch11 p.9–10/13 (per 04, not re-opened)

</details>
<!-- /q -->

<!-- q id=I6-A-04 type=A set=main -->
### I6-A-04 · Application
**Question:** The top 4 vectors map to only 2 unique parents: what does a default "k = 4" retriever return, and how many vectors must you fetch at n = 10 to be sure of 4 parents?

**Reply template:** `"k = 4" returns ____ parents. Fetch K_vec = ____ (because ____), dedup ____, then cut to 4.`

<details><summary>Hint 1</summary>

LangChain's `MultiVectorRetriever` fetches 4 child vectors by default and returns their unique parents.

</details>

<details><summary>Hint 2</summary>

In chunks + questions, how many vectors can one parent own at n = 10? In the worst case the top vectors are all from as few parents as possible.

</details>

<details><summary>Hint 3</summary>

Each parent owns at most n + 1 = 11 vectors, so k × 11 vectors must contain at least k parents.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** It returns 2 parents, not 4: the retriever cuts at 4 vectors, then removes the duplicates. Fetch `K_vec = k(n + 1)` vectors, dedup in rank order, then cut to 4:

```
K_vec = 4 × (10 + 1) = 44        (questions only: 4 × 10 = 40)
measured, chunks + questions n = 10: 4 parents appeared after at most 11 vectors (seeds needed 4 to 11)
```

The bound is a guarantee, not what you usually need; fetching 44 of 1,067 vectors is still cheap.

**Key points** (a 3 needs every point):
- [ ] "k = 4" returns 2 parents (fewer than asked, silently).
- [ ] K_vec = k(n + 1) = 44 for n = 10 (each parent owns at most 11 vectors).
- [ ] Dedup in rank order, then cut to 4.

**For a 4, also:**
- [ ] A self-check or limit: the measured need was at most 11 vectors; in LangChain set `search_kwargs={"k": K_vec}` and cut yourself, and never dedup with `set()`.

**Common wrong answers:**
- [ ] "It returns 4 parents, k means parents": in the default it means child vectors.
- [ ] "Fetch 10 vectors, one per question": that ignores that one parent can fill them all.

**If you missed it, reread:** [short §6](../reading/I6_doc_augmentation.md#6-search-the-vectors-return-unique-parents) · [lesson step 6](../lessons/I6_doc_augmentation.html#search) · book Ch11 p.8/13 (per 04, not re-opened)

</details>
<!-- /q -->

<!-- q id=I6-A-05 type=A set=main -->
### I6-A-05 · Application
**Question:** With the provisional τ = 0.7054, which of these five eval items are flagged as leaked, and which items does the decision use?

**Data** (leak_cos = the best cosine between the eval question and any generated question in the index):

```
item    leak_cos
D-002   0.9869
D-003   0.7101
D-005   0.4723
D-006   0.6007
D-007   0.7565
```

**Reply template:** `flagged: ____; not flagged: ____. The decision uses ____, which here leaves ____ items, so ____.`

<details><summary>Hint 1</summary>

An item is flagged when leak_cos ≥ τ: it is as close to an index question as a deliberate paraphrase is to its original.

</details>

<details><summary>Hint 2</summary>

The decisive slice is human-written items plus unflagged items. How many items are left, and what can so few items prove?

</details>

<details><summary>Hint 3</summary>

Compare each value with 0.7054; D-003 is only just above it.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
flagged (≥ 0.7054):    D-002 0.9869, D-003 0.7101, D-007 0.7565
not flagged:           D-005 0.4723, D-006 0.6007
```

The decision uses the **decisive slice**: human-written items plus unflagged items. All seeds are LLM-drafted, so here that is D-005 and D-006: two items, far too few to decide anything, so the verdict stays "inconclusive" and you report the flagged share and the de-leaked arm (MRR@10 0.547 against A0's 0.708) next to the headline gain. τ itself is provisional: it comes from one paraphrase pair, and 06 asks for at least 10 pairs; D-003 sits just above it.

**Key points** (a 3 needs every point):
- [ ] Flagged: D-002, D-003, D-007.
- [ ] Not flagged: D-005, D-006.
- [ ] The decision uses human-written plus unflagged items (the decisive slice), not the flagged ones.

**For a 4, also:**
- [ ] States the limits: 2 items cannot support a decision, and τ from one pair is provisional (calibrate it from at least 10 paraphrase pairs); D-003 is borderline.

**Common wrong answers:**
- [ ] "Only D-002 is leaked, because only it is above 0.9": the threshold is τ from paraphrase pairs, not a round number picked by eye (MC-006).
- [ ] "Drop the flagged items and report the rest as the result": two LLM-drafted items are a diagnostic, not a result.

**If you missed it, reread:** [short §9](../reading/I6_doc_augmentation.md#9-leakage-when-the-index-already-holds-the-eval-question) · [lesson step 9](../lessons/I6_doc_augmentation.html#leak) · book Ch11 p.6/13 (per 04, not re-opened; the book does not discuss leakage)

</details>
<!-- /q -->

<!-- q id=I6-A-06 type=A set=review -->
### I6-A-06 · Application
**Question:** With questions only at n = 5, rare-token retention is 0.264: what happens to a query by number or acronym, and what fixes it?

**Reply template:** `About ____ of the chunks' numbers and acronyms appear in no question, so ____. Fix: ____.`

<details><summary>Hint 1</summary>

Retention is the share of each chunk's numbers and acronyms that appear in at least one of its questions.

</details>

<details><summary>Hint 2</summary>

In a questions-only index, what vector is left to match a query that copies an exact number from the document?

</details>

<details><summary>Hint 3</summary>

1 − 0.264 = 0.736 of the rare tokens are in no question.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** About three quarters of the rare tokens (1 − 0.264 = 0.736; 67 of 91) appear in no generated question, and questions only has no chunk vector, so a query by that number or acronym has nothing that carries it and can miss its chunk. The seeds did not show this, but only because the pack happened to contain a question naming each exact term (D-004 matched "What does DAC stand for?"). Fix: keep the chunk vector (chunks + questions), or add a keyword index (BM25, R1); a larger n helps only partly (0.549 at n = 10).

```
retention   n = 1 0.066 · n = 3 0.143 · n = 5 0.264 (24 of 91) · n = 10 0.549 (50 of 91)
```

**Key points** (a 3 needs every point):
- [ ] Most numbers and acronyms (about 74% at n = 5) appear in no question.
- [ ] A questions-only index then has nothing to match a query by that number, so it can miss.
- [ ] Fix: keep the chunk vector or add BM25 (hybrid).

**For a 4, also:**
- [ ] Says how to check: an exact-term guard (CE@k on exact-term items must not drop) and the retention metric; and that the seeds passed only by luck of the pack.

**Common wrong answers:**
- [ ] "Raise n to 10 and the problem is gone": retention reaches only 0.549.
- [ ] "Dense vectors match numbers as well as words": a paraphrased question drops the number entirely.

**If you missed it, reread:** [short §8](../reading/I6_doc_augmentation.md#8-keyword-and-number-queries-the-guard) · [lesson step 8](../lessons/I6_doc_augmentation.html#guard) · book Ch11 p.11/13 (per 04, not re-opened)

</details>
<!-- /q -->

<!-- q id=I6-T-01 type=T set=main -->
### I6-T-01 · Transfer
**Question:** Your eval questions were drafted by the same kind of model that wrote the index questions, and the questions-only index scores Hit@4 = 1.00: what do you check, and what do you report?

**Reply template:** `I check ____. I report ____. If the gain disappears, the verdict is ____.`

<details><summary>Hint 1</summary>

A perfect score from two sets of LLM-written questions over the same chunks: what could the eval question be matching in the index?

</details>

<details><summary>Hint 2</summary>

Think of a per-item measure of closeness to the index questions, a threshold from paraphrase pairs, an arm with the near-copies deleted, and the items you can trust.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Check for leakage before believing the score. For each eval item compute `leak(i)` = the best cosine to any generated question (plus content-word 3-gram overlap); calibrate τ from at least 10 base↔paraphrase pairs; flag the items above it. Re-run with the near-copies deleted (a de-leaked arm) and on the decisive slice (human-written plus unflagged items), with its n. Report the headline score next to the flagged share, the de-leaked score and the slice score, and CE@4 on parent spans, not just Hit@4. On our seeds the same pattern happened: MRR@10 rose 0.708 → 0.781, and after deleting the 10 near-copies it fell to 0.547. If the gain vanishes, the verdict is "inconclusive: possible leakage".

**Key points** (a 3 needs every point):
- [ ] Suspect leakage: the eval questions may have near-copies among the index questions.
- [ ] Measure leak(i) per item and flag against a τ from paraphrase pairs.
- [ ] Re-score de-leaked and on the decisive slice (human-written + unflagged).
- [ ] Report all of them; if the gain disappears, say "inconclusive".

**For a 4, also:**
- [ ] Adds what would settle it: human-written questions, or index questions from another model family (A5), plus a paired bootstrap CI; and notes that a handful of items proves nothing either way.

**Common wrong answers:**
- [ ] "Hit@4 = 1.00 shows questions only is the best design": a perfect score on same-habit questions is the leakage signature.
- [ ] "Paraphrase the eval questions and the problem is gone": the index questions are paraphrases too; measure, don't assume.

**If you missed it, reread:** [short §9](../reading/I6_doc_augmentation.md#9-leakage-when-the-index-already-holds-the-eval-question) · [short §12](../reading/I6_doc_augmentation.md#12-when-not-to-use-it) · [lesson step 9](../lessons/I6_doc_augmentation.html#leak) · [lesson step 12](../lessons/I6_doc_augmentation.html#project) · book Ch11 p.11/13 (per 04, not re-opened)

</details>
<!-- /q -->

<!-- q id=I6-T-02 type=T set=main -->
### I6-T-02 · Transfer
**Question:** A product catalogue is searched mostly by part numbers: which design, if any, would you use, and why?

**Reply template:** `For part-number queries I would ____, because ____. Question generation helps only if ____, and then with design ____.`

<details><summary>Hint 1</summary>

What happens to a part number when an LLM writes a natural question about the chunk?

</details>

<details><summary>Hint 2</summary>

Which retriever matches exact strings? Which of the three designs still keeps the chunk's own text in a vector?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Part numbers are rare tokens, and generated questions tend to drop them (rare-token retention 0.264 at n = 5 on our pack), so questions only is the wrong choice. For ID lookups, use keyword search (BM25) or an exact-match field, combined with dense search if needed (R1). Question generation helps only for the natural-language queries ("which pump fits a garden hose?") and only if the baseline misses them; then use chunks + questions, which keeps the chunk vector, next to BM25. Check it with the retention metric and an exact-term guard on labelled part-number queries.

**Key points** (a 3 needs every point):
- [ ] Not questions only: generated questions drop part numbers (rare tokens).
- [ ] Use keyword/BM25 or exact match for IDs (hybrid with dense, R1).
- [ ] If at all, chunks + questions for natural-language queries, keeping the chunk vector.

**For a 4, also:**
- [ ] Says how to measure it (rare-token retention, an exact-term CE@k guard) and when to skip I6 entirely (queries are mostly IDs, or the baseline already finds them).

**Common wrong answers:**
- [ ] "Generate more questions so every part number appears": retention rises only partly (0.549 at n = 10), and the index grows.
- [ ] "Dense search handles part numbers like words": embeddings see the topic, not the exact string.

**If you missed it, reread:** [short §5](../reading/I6_doc_augmentation.md#5-three-designs-one-parent-table) · [short §8](../reading/I6_doc_augmentation.md#8-keyword-and-number-queries-the-guard) · [lesson step 5](../lessons/I6_doc_augmentation.html#designs) · [lesson step 8](../lessons/I6_doc_augmentation.html#guard) · book Ch11 p.11/13 (per 04, not re-opened)

</details>
<!-- /q -->

<!-- q id=I6-T-03 type=T set=review -->
### I6-T-03 · Transfer
**Question:** A corpus changes every day and gets 50 queries a day: would you generate questions at index time or at query time?

**Reply template:** `Index time costs ____ calls a day; query time costs ____. I would choose ____, unless ____.`

<details><summary>Hint 1</summary>

Use the break-even rule, per day: index-side calls are the chunks regenerated per day; HyDE's are the queries per day.

</details>

<details><summary>Hint 2</summary>

Does a daily change mean every chunk changes? What does a cache keyed by chunk text regenerate?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Compare calls per day. Query time (HyDE) costs 50 calls a day, one per query, each on the critical path. Index time costs one call per **changed** chunk, if the question cache is keyed by chunk text. If the whole corpus is regenerated daily, a 97-chunk corpus already costs 97 calls a day, more than 50, so query time wins in calls. If only a few chunks change a day (fewer than 50), index time wins in calls and adds no latency per query. So: measure the daily change in chunks; choose index time when changed chunks per day < queries per day, HyDE otherwise, and confirm on your own questions that either one helps at all.

**Key points** (a 3 needs every point):
- [ ] Query time costs 50 calls a day (one per query, added latency).
- [ ] Index time costs one call per regenerated chunk per day.
- [ ] Decide by break-even: index time only if changed chunks per day < 50.

**For a 4, also:**
- [ ] Notes the text-keyed cache (only changed chunks regenerate) and that neither is worth it unless the baseline actually misses question-shaped queries.

**Common wrong answers:**
- [ ] "Index time, because it is free at query time": a daily full rebuild of more chunks than queries costs more calls.
- [ ] "Query time, because the corpus changes": with a text-keyed cache, only the changed chunks are regenerated.

**If you missed it, reread:** [short §10](../reading/I6_doc_augmentation.md#10-what-it-costs-and-when-hyde-is-cheaper) · [lesson step 10](../lessons/I6_doc_augmentation.html#cost) · book Ch11 p.9–10/13 (per 04, not re-opened)

</details>
<!-- /q -->
