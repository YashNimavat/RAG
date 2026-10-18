<!-- kit:questions concept=P4 version=1 -->
# P4 questions: embeddings, similarity measures, score direction, bi- vs cross-encoders

**How to use:** write your answer and a confidence (1–3) first. Then open the answer and tick the key points you really wrote.

**Where the numbers come from:** `sources/verification/P4/p4_measure.py` and `p4_kit_measure.py` with MiniLM (`all-MiniLM-L6-v2`) on the climate PDF ([P4_FACTS](../../sources/verification/P4/P4_FACTS.md) S1–S10; [kit run K1–K13](../../sources/verification/P4/out_p4_kit_measure.txt)). The draft questions (D-001…D-010) are LLM-drafted and not yet checked by you: ranks on them are observations, not results. Cohere facts are from Cohere's documentation (read 2026-10-17); the Cohere price is UNVERIFIED. "Toy" vectors are made up. No API was called to write this file.

<!-- q id=P4-PRE-01 type=R set=pre -->
### P4-PRE-01 · Recall (before reading)
**Question:** Two arrows point in exactly the same direction, but one is twice as long. What is their cosine?

**Reply template:** `cos = ____, because cosine looks only at ____.`

<details><summary>Hint 1</summary>

Picture the angle between the two arrows. Does stretching one arrow change that angle?

</details>

<details><summary>Hint 2</summary>

cos(a, b) = a·b / (‖a‖ ‖b‖). If b = 2a, write a·b and ‖b‖ in terms of a.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Exactly 1. Cosine measures only the angle, and the angle between an arrow and a stretched copy of it is 0. In the formula the length cancels:

```
b = 2a :  a·b = 2‖a‖²,  ‖b‖ = 2‖a‖  →  cos = 2‖a‖² / (‖a‖ · 2‖a‖) = 1
toy (S2): q = [1, 2, 2], d3 = [2, 4, 4] = 2q  →  cos 1.0000, but dot 18 and L2 3.0000
```

**Key points** (a 3 needs every point):
- [ ] The cosine is 1.
- [ ] Cosine measures the angle (direction) only; length does not change it.

**For a 4, also:**
- [ ] Contrasts the other two measures: the dot product doubles and the L2 distance between the tips is not 0 (d3: dot 18, L2 3.0).

**Common wrong answers:**
- [ ] "0.5, because one is half as long": length cancels out of the cosine.
- [ ] "2, because the dot product doubles": that is the dot product, not the cosine.

**If you missed it, reread:** [short §2](../reading/P4_embeddings.md#2-an-embedding-is-an-arrow) · [full D.2](../../concepts/P4_embeddings_similarity.md#d2-the-three-measures) · book Ch1 p.5/14

</details>
<!-- /q -->

<!-- q id=P4-PRE-02 type=R set=pre -->
### P4-PRE-02 · Recall (before reading)
**Question:** In dense search, what happens to a user's question before it can be compared with the stored chunks?

**Reply template:** `The question is ____ by ____, so that ____.`

<details><summary>Hint 1</summary>

The chunks were turned into vectors at index time. What must the question become to be compared with them?

</details>

<details><summary>Hint 2</summary>

Which model must do it? What would go wrong with a different one?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** It is embedded into a vector by **the same model** that embedded the chunks (with the model's query label, if it has one), so the two vectors live in the same space and can be compared. The book stresses the same point (Ch1 p.8/14). With a different model of the same size, nothing errors but the ranks collapse:

```
8 draft questions (K4)   right model: right chunk in top 4 for 8 of 8   wrong model (L3): 3 of 8
```

**Key points** (a 3 needs every point):
- [ ] The question is turned into a vector (embedded).
- [ ] By the same model that embedded the chunks.

**For a 4, also:**
- [ ] Says why: vectors from different models are not comparable, even with the same length, and nothing raises an error (Hit@4 8 → 3 of 8).

**Common wrong answers:**
- [ ] "The question is compared word by word with the chunks": that is keyword search (P3), not dense search.
- [ ] "Any embedding model works if it gives the same number of dimensions": a matching length is not a matching space.

**If you missed it, reread:** [short §4](../reading/P4_embeddings.md#4-one-score-per-chunk) · [short §1](../reading/P4_embeddings.md#1-three-bugs-that-raise-no-error) · [full D.1](../../concepts/P4_embeddings_similarity.md#d1-the-objects-involved-mc-002-fix) · book Ch1 p.8/14

</details>
<!-- /q -->

<!-- q id=P4-PRE-03 type=R set=pre -->
### P4-PRE-03 · Recall (before reading)
**Question:** A vector store returns the score 0.3 for chunk A and 0.8 for chunk B. Which chunk is closer to the question?

**Reply template:** `It depends on ____. If the score is a ____, then ____; if it is a ____, then ____.`

<details><summary>Hint 1</summary>

Is a bigger number always better? Think of a distance on a map.

</details>

<details><summary>Hint 2</summary>

Which kind of score is a cosine, and which kind is an L2 distance?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** You cannot tell without the store's convention. If the score is a **similarity** (cosine, dot product), higher is closer, so B. If it is a **distance** (L2; FAISS returns squared L2), lower is closer, so A. Read the documentation once, and convert every score to one direction at a single place. The repo's `graph_rag.ipynb` (cell 12) gets this wrong: it treats a FAISS distance as a similarity, so it explores the closest chunk last (toy, S10).

**Key points** (a 3 needs every point):
- [ ] It depends on whether the score is a similarity or a distance.
- [ ] Similarity: higher = closer (B); distance: lower = closer (A).

**For a 4, also:**
- [ ] Names a way to check: the self-retrieval test (a chunk's own text must come back first, with cosine 1 or distance 0), or the library's documentation.

**Common wrong answers:**
- [ ] "B, a bigger score is always better": for a distance, smaller is better.

**If you missed it, reread:** [short §3](../reading/P4_embeddings.md#3-normalise-and-read-the-direction) · [short §1](../reading/P4_embeddings.md#1-three-bugs-that-raise-no-error) · book App p.15/23

</details>
<!-- /q -->

<!-- q id=P4-R-01 type=R set=main -->
### P4-R-01 · Recall (O1-Q02 check)
**Question:** Write the cosine formula.

**Reply template:** `cos(a, b) = ____ / ____`

<details><summary>Hint 1</summary>

It is the dot product, divided by something that removes the effect of length.

</details>

<details><summary>Hint 2</summary>

The length of a vector is ‖a‖ = √(a·a). How many lengths appear in the bottom?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
cos(a, b) = (a · b) / (‖a‖ · ‖b‖)        a · b = Σ aᵢbᵢ        ‖a‖ = √(a · a)
```

It runs from −1 (opposite) through 0 (at right angles) to 1 (same direction), and measures the angle only. For vectors of length 1 the bottom is 1, so the cosine equals the dot product.

**Key points** (a 3 needs every point):
- [ ] The top is the dot product a · b.
- [ ] The bottom is the product of the two lengths, ‖a‖ ‖b‖.

**For a 4, also:**
- [ ] Gives the range (−1 to 1), says it measures angle only, and that on unit vectors it equals the dot product.

**Common wrong answers:**
- [ ] "a · b / ‖a − b‖": that mixes in the L2 distance.
- [ ] "a · b, nothing else": that is the dot product, which also rewards long vectors.

**If you missed it, reread:** [short §2](../reading/P4_embeddings.md#2-an-embedding-is-an-arrow) · [full D.2](../../concepts/P4_embeddings_similarity.md#d2-the-three-measures) · book App p.15/23

</details>
<!-- /q -->

<!-- q id=P4-R-02 type=R set=main -->
### P4-R-02 · Recall (MC-002 check item)
**Question:** What happens to the user's question at query time?

**Reply template:** `It is ____ with ____, then ____.`

<details><summary>Hint 1</summary>

Two times: index time (once) and query time (every question). What exists already when a question arrives?

</details>

<details><summary>Hint 2</summary>

E is the 97 × 384 chunk matrix and q the question's vector. What shape does E · q have?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The question is embedded with the **same model** as the chunks (plus its query label, if the model has one). Its vector q is multiplied with the stored chunk matrix E, which gives **one score per chunk**, and the scores are sorted and cut at k. It is a list of scores, not a similarity matrix:

```
E: 97 × 384   q: 384   s = E · q: shape (97,)        an all-pairs matrix would be 97 × 97 = 9,409 scores (K3)
D-002 top 5: chunks 69, 68, 27, 17, 84 → the right chunk (27) at rank 3
```

**Key points** (a 3 needs every point):
- [ ] Embedded with the same model (and its query label if it has one).
- [ ] One score per chunk (a vector of N scores).
- [ ] Sorted, and the top k kept.

**For a 4, also:**
- [ ] Names the boundary: a score vector, not an all-pairs matrix; N × N matrices belong to training batches, diversity (dartboard) and duplicate analysis.

**Common wrong answers:**
- [ ] "The system builds a similarity matrix of all the chunks": one question gets one score per chunk (MC-002).
- [ ] "The question is added to the index": it is only compared with the index.

**If you missed it, reread:** [short §4](../reading/P4_embeddings.md#4-one-score-per-chunk) · [full D.1](../../concepts/P4_embeddings_similarity.md#d1-the-objects-involved-mc-002-fix) · book Ch1 p.8/14

</details>
<!-- /q -->

<!-- q id=P4-R-03 type=R set=main -->
### P4-R-03 · Recall (O1-Q10 check)
**Question:** Why can a bi-encoder search a whole collection, while a cross-encoder cannot?

**Reply template:** `The bi-encoder can ____, but the cross-encoder must ____.`

<details><summary>Hint 1</summary>

What can each model compute before the question arrives?

</details>

<details><summary>Hint 2</summary>

Count model passes for one question against N chunks, for each model.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** A bi-encoder embeds each text alone, so every chunk's vector is computed **once, at index time**; a search then costs one model pass (the question) plus cheap multiplications. A cross-encoder reads the question and a chunk **together**, so nothing can be stored in advance and it needs one model pass **per (question, chunk) pair**: 97 for the climate chunks, a million for a million chunks. In exchange it sees how the two texts' words relate, which makes it more precise, so it is used to rerank a shortlist (Ch13 p.6–7/13):

```
D-002 (K9): bi-encoder rank 3 → rank 1 after the cross-encoder reranked the top 10 (10 passes, not 97)
```

**Key points** (a 3 needs every point):
- [ ] The bi-encoder precomputes and stores the chunk vectors; one pass per question.
- [ ] The cross-encoder needs one pass per (question, chunk) pair; nothing can be stored.

**For a 4, also:**
- [ ] The trade-off and the design: the joint reading is more precise, so the cross-encoder reranks the bi-encoder's shortlist (fetch 10, keep 5, as `reranking.ipynb` cells 27 and 29).

**Common wrong answers:**
- [ ] "The cross-encoder is less accurate": it is usually more precise; the problem is its cost.
- [ ] "The cross-encoder outputs bigger vectors": it outputs one score per pair, no vector at all.

**If you missed it, reread:** [short §8](../reading/P4_embeddings.md#8-bi-encoder-vs-cross-encoder) · [full D.7](../../concepts/P4_embeddings_similarity.md#d7-bi-encoder-vs-cross-encoder) · book Ch13 p.6–7/13

</details>
<!-- /q -->

<!-- q id=P4-R-04 type=R set=main -->
### P4-R-04 · Recall
**Question:** What does Cohere's `input_type` setting do?

**Reply template:** `It tells the model whether a text is ____ or ____, because ____.`

<details><summary>Hint 1</summary>

The book's asymmetry problem: how does a question differ from the passage that answers it?

</details>

<details><summary>Hint 2</summary>

Which two values does the course use, and for which texts?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** It marks which side of the search a text is on: `search_document` for chunks, `search_query` for questions (it is required for Cohere's v3 and newer models). Questions are short and ask; chunks are long and state, so they embed apart even on the same topic (the asymmetry problem, Ch6 p.1–2/14). A model trained with side markers embeds each side the way it learned to, so the two meet. Using the wrong one is allowed and silent.

```
asymmetry on MiniLM (K8): chunk 27 vs the question 0.4386 (rank 3) · vs the statement "…adopted in 2015." 0.4775 (rank 1)
```

**Key points** (a 3 needs every point):
- [ ] It says whether the text is a query (question) or a document (chunk).
- [ ] Because questions and passages embed differently (asymmetry); the model was trained to embed each side its own way.

**For a 4, also:**
- [ ] Names the limit: a wrong input type raises no error, and how much it costs on our corpus is UNVERIFIED until the recorded Cohere run.

**Common wrong answers:**
- [ ] "It sets the language or the file type": it sets the role of the text in the search.
- [ ] "It does not matter, it is the same model": the model was trained to use the marker.

**If you missed it, reread:** [short §7](../reading/P4_embeddings.md#7-questions-may-need-their-own-label) · [full D.8](../../concepts/P4_embeddings_similarity.md#d8-querydocument-asymmetry-input-types-and-prefixes) · book Ch6 p.1–2/14

</details>
<!-- /q -->

<!-- q id=P4-R-05 type=R set=main -->
### P4-R-05 · Recall
**Question:** Why do L2 distance and cosine rank unit vectors in the same order?

**Reply template:** `For unit vectors, L2² = ____, so ____.`

<details><summary>Hint 1</summary>

Expand ‖â − b̂‖² = (â − b̂)·(â − b̂). What are ‖â‖² and ‖b̂‖² for unit vectors?

</details>

<details><summary>Hint 2</summary>

Once you have L2² as a formula in cos, ask: when cos goes up, what does L2 do?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** For unit vectors,

```
‖â − b̂‖² = ‖â‖² + ‖b̂‖² − 2 â·b̂ = 1 + 1 − 2·cos = 2 − 2·cos
```

So L2 is a function of the cosine that always goes down as the cosine goes up: the smallest distance and the largest cosine belong to the same chunk, and the whole ranking is the same (lower-first for L2, higher-first for cosine). The dot product of unit vectors also equals the cosine. Toy check: 0.4714² = 0.2222 = 2 − 2 × 0.8889; on 100 random questions × 1,000 documents the full rankings matched 100 of 100 times (S3).

**Key points** (a 3 needs every point):
- [ ] For unit vectors, L2² = 2 − 2·cos.
- [ ] So L2 always falls as cosine rises: the order is the same (reversed direction of the number).

**For a 4, also:**
- [ ] Names when it fails: on vectors that are not unit length the measures can disagree (toy: raw L2's top result differed for 94 of 100 questions), so normalise and assert first.

**Common wrong answers:**
- [ ] "They give the same numbers": the numbers differ (one is a distance); only the order matches.
- [ ] "They always rank the same": only on unit vectors.

**If you missed it, reread:** [short §3](../reading/P4_embeddings.md#3-normalise-and-read-the-direction) · [full D.3](../../concepts/P4_embeddings_similarity.md#d3-normalisation-and-the-proof-that-l2-then-ranks-like-cosine) · book App p.15/23

</details>
<!-- /q -->

<!-- q id=P4-R-06 type=R set=main -->
### P4-R-06 · Recall
**Question:** Search does not build a similarity matrix. Where does a real N × N matrix of similarities appear?

**Reply template:** `In ____, as ____; in ____, as ____; and in ____.`

<details><summary>Hint 1</summary>

One of them happens before the model is ever used for search.

</details>

<details><summary>Hint 2</summary>

Think of a step that compares candidates with each other, and of a check that looks for chunks saying the same thing twice.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** In three jobs that compare many texts with many texts, none of them the search itself:
- **training:** a batch of B question–passage pairs gives S = Q·Pᵀ, a B × B matrix whose diagonal holds the true pairs (MiniLM: batches of 1,024);
- **diversity:** the repo's `dartboard.ipynb` (cell 23) builds a K × K matrix among the candidates, to pick chunks that differ from each other;
- **analysis:** all chunks against all chunks (97 × 97 = 9,409 scores) to find near-duplicates; here the closest pair scores 0.8590 (K6).

**Key points** (a 3 needs every point):
- [ ] Training: the B × B batch matrix (true pairs on the diagonal).
- [ ] At least one more: dartboard's K × K diversity matrix, or the all-pairs duplicate analysis.

**For a 4, also:**
- [ ] Says why search needs none: one question gives one score per chunk, shape (N,) (MC-002).

**Common wrong answers:**
- [ ] "In every search, to compare the question with all chunks": that is a vector of N scores, not a matrix (MC-002).

**If you missed it, reread:** [short §4](../reading/P4_embeddings.md#4-one-score-per-chunk) · [short §5](../reading/P4_embeddings.md#5-where-the-closeness-comes-from) · [full D.1](../../concepts/P4_embeddings_similarity.md#d1-the-objects-involved-mc-002-fix) · book Ch1 p.8/14

</details>
<!-- /q -->

<!-- q id=P4-R-07 type=R set=main -->
### P4-R-07 · Recall
**Question:** How did MiniLM learn to put similar texts close together?

**Reply template:** `It was trained on ____. In each batch it ____, and was penalised unless ____.`

<details><summary>Hint 1</summary>

What kind of data: single texts, or texts that belong together?

</details>

<details><summary>Hint 2</summary>

In a batch, each question has one true partner and many others. What should the scores do?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** It was trained **contrastively** on over a billion pairs of texts that belong together (its model card). In each step it embedded a batch of 1,024 pairs, computed the cosine of every question against every partner in the batch, and was penalised (a cross-entropy loss) unless the true partner scored highest. So true pairs were pulled together and the rest of the batch pushed apart. Consequences: "close" means "the kind of pair its training data paired", and the similarity to use is the one it was trained with (cosine, hence its Normalize step). Training texts were cut at 128 tokens.

```
toy batch of 4 (K10): the true pair tops its row for 3 of 4; mean loss 0.2903 at τ = 0.05, 7.0697 with shuffled pairs
```

**Key points** (a 3 needs every point):
- [ ] Trained on pairs of texts that belong together.
- [ ] Contrastive: the true pair must score higher than the other pairs in the batch (pull together, push apart).

**For a 4, also:**
- [ ] A consequence: use the similarity it was trained with (cosine for MiniLM; DPR used the dot product), or "fits 256 tokens but trained on 128".

**Common wrong answers:**
- [ ] "It understands meaning like a person": it learned which texts were paired in its training data.
- [ ] "It was trained to predict the next word, like the LLM": that is a decoder; MiniLM is an encoder trained for comparison.

**If you missed it, reread:** [short §5](../reading/P4_embeddings.md#5-where-the-closeness-comes-from) · book App p.16/23

</details>
<!-- /q -->

<!-- q id=P4-R-08 type=R set=interview source=AIQ-04-Q15 -->
### P4-R-08 · Recall (interview)
**Question:** "Many embedding models tell you to prefix queries and documents differently, or to pass a task instruction. Why, and what goes wrong if you ignore it?" *From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md` (Q15), Copyright (c) 2026 Om, MIT License.*

**Reply template:** `Because ____. If you ignore it, ____. To catch it, ____.`

<details><summary>Hint 1</summary>

The book's asymmetry problem: a question and its answer passage look different.

</details>

<details><summary>Hint 2</summary>

Does anything raise an error when the prefix is missing? What should you store with the index?

</details>

<details><summary>Show answer (write yours first)</summary>

The repository's answer (excerpt, verbatim, MIT License, Copyright (c) 2026 Om):

> Because retrieval is asymmetric, and these models learned it with the markers present. A query is short, question-shaped and underspecified; a passage is long and declarative. A model trained contrastively with a side marker uses it to decide how to encode the text, so the marker is part of the model, not a formatting nicety.
>
> If you ignore it, nothing errors. Results still look plausible, just measurably worse, and every published number for that model assumed the convention, so you are no longer running the model you evaluated.

**Model answer:** Questions are short and ask; passages are long and state (the asymmetry problem, Ch6 p.1–2/14). Models trained with side markers learned to embed each side differently, so the marker is part of the model: Cohere's `input_type`, or a prefix named in the model card. Ignore it and nothing errors; the ranks just get worse. A marker on a model that was **not** trained with one is not harmless either: it just moves the vector (MiniLM: "query: " + D-002 has cosine 0.9626 with the plain question, S9). Catch it by storing the marker with the model id in the index metadata, keeping `embed_query` and `embed_documents` separate, and measuring with and without on labelled questions. How much a wrong marker costs on our corpus with Cohere is UNVERIFIED until the recorded run.

**Key points** (a 3 needs every point):
- [ ] Asymmetry: questions and passages differ in form, and the model learned to embed each side with its marker.
- [ ] Ignoring it raises no error; retrieval quietly gets worse.
- [ ] Use only the marker the model card names (a marker on a model not trained with one just moves the vector).

**For a 4, also:**
- [ ] A guard: store the marker with the model id, separate `embed_query` / `embed_documents`, and measure with vs without on labelled questions.

**Common wrong answers:**
- [ ] "A prefix always helps, so add `query:` to every model": on MiniLM it only moves the vector (0.9626, S9).
- [ ] "It is only formatting": the model was trained with it.

**If you missed it, reread:** [short §7](../reading/P4_embeddings.md#7-questions-may-need-their-own-label) · [full D.8](../../concepts/P4_embeddings_similarity.md#d8-querydocument-asymmetry-input-types-and-prefixes) · book Ch6 p.1–2/14

</details>
<!-- /q -->

<!-- q id=P4-A-01 type=A set=main -->
### P4-A-01 · Application (MC-002 check item)
**Question:** Compute cos(a, b) for a = [3, 0, 4] and b = [0, 0, 5].

**Reply template:** `dot = ____, lengths ____ and ____, cos = ____.`

<details><summary>Hint 1</summary>

Multiply the matching numbers and add them up.

</details>

<details><summary>Hint 2</summary>

‖a‖ = √(3² + 0² + 4²). Then divide the dot product by both lengths.

</details>

<details><summary>Hint 3</summary>

dot = 3·0 + 0·0 + 4·5 = 20. Now the two lengths.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
dot = 3·0 + 0·0 + 4·5 = 20
‖a‖ = √(9 + 0 + 16) = 5        ‖b‖ = √(0 + 0 + 25) = 5
cos = 20 / (5 × 5) = 0.8
```

Self-check: 0.8 is between −1 and 1, and both vectors have a positive third number, so the cosine must be positive.

**Key points** (a 3 needs every point):
- [ ] dot = 20.
- [ ] lengths 5 and 5.
- [ ] cos = 0.8.

**For a 4, also:**
- [ ] A self-check (the range −1 to 1, or the sign).

**Common wrong answers:**
- [ ] "cos = 20": that is the dot product; it still has to be divided by both lengths.
- [ ] "cos = 0.8 means the chunk is 80% relevant": a cosine orders texts; it is not a probability.

**If you missed it, reread:** [short §2](../reading/P4_embeddings.md#2-an-embedding-is-an-arrow) · [full Part F](../../concepts/P4_embeddings_similarity.md#part-f--worked-example-by-hand) · book App p.15/23

</details>
<!-- /q -->

<!-- q id=P4-A-02 type=A set=main -->
### P4-A-02 · Application (CR-08)
**Question:** You multiply one document vector by 2. What happens to its dot product, cosine and L2 distance with the question?

**Data:** q = [1, 2, 2], d1 = [2, 1, 2] (dot 8, cos 0.8889, L2 1.4142).

**Reply template:** `dot ____; cosine ____; L2 ____.`

<details><summary>Hint 1</summary>

Which of the three measures ignores length?

</details>

<details><summary>Hint 2</summary>

Compute 2·d1 = [4, 2, 4], then q − 2·d1, then its length.

</details>

<details><summary>Hint 3</summary>

q − [4, 2, 4] = [−3, 0, −2].

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
dot   8 → 16        doubles
cos   0.8889 → 0.8889   unchanged (angle only)
L2    1.4142 → √(9 + 0 + 4) = 3.6056   changes, by no fixed factor
```

So any ranking by raw dot or raw L2 can change when vector lengths change, while cosine cannot. That is why vectors are normalised before L2 or dot is used.

**Key points** (a 3 needs every point):
- [ ] The dot product doubles (8 → 16).
- [ ] The cosine is unchanged (0.8889).
- [ ] L2 changes, but not by a fixed factor (1.4142 → 3.6056).

**For a 4, also:**
- [ ] A self-check, or the consequence: raw-L2 and raw-dot rankings can flip when lengths vary; normalise first.

**Common wrong answers:**
- [ ] "L2 doubles too": it went from 1.4142 to 3.6056, not 2.8284.
- [ ] "The cosine doubles": length cancels out of the cosine.

**If you missed it, reread:** [short §2](../reading/P4_embeddings.md#2-an-embedding-is-an-arrow) · [short §3](../reading/P4_embeddings.md#3-normalise-and-read-the-direction) · [full D.2](../../concepts/P4_embeddings_similarity.md#d2-the-three-measures) · book Ch1 p.5/14

</details>
<!-- /q -->

<!-- q id=P4-A-03 type=A set=main -->
### P4-A-03 · Application (debugging)
**Question:** What is wrong in this code?

```python
q = model_v2.encode([question])[0]       # model_v2 also gives 384 numbers
scores = E_v1 @ q                        # E_v1 built last month with model_v1
```

**Reply template:** `The bug is ____. It raises ____. The fix is ____.`

<details><summary>Hint 1</summary>

Which model made the question's vector, and which made the chunks'?

</details>

<details><summary>Hint 2</summary>

Will numpy complain? Shapes: (N, 384) @ (384,).

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The question and the index come from **different models**. The shapes match (384), so nothing raises an error, but the two vector spaces are unrelated and the ranks collapse. Measured on the climate chunks with L3 questions against MiniLM chunks (K4): the right chunk in the top 4 for 3 of 8 questions instead of 8 of 8; D-002 from rank 3 to rank 16. Fix: embed the question with model_v1, or re-embed every chunk with model_v2; store the model id with the index and assert it matches at query time.

**Key points** (a 3 needs every point):
- [ ] Question and chunks are embedded by different models.
- [ ] No error, because the dimensions match.
- [ ] Fix: one model for both sides (re-embed, or use model_v1 for the question).

**For a 4, also:**
- [ ] The guard: store the model id with the index and assert it at query time (or a measured effect: Hit@4 8 → 3 of 8).

**Common wrong answers:**
- [ ] "numpy will raise a shape error": (N, 384) @ (384,) is valid.
- [ ] "It is fine if both models are good": a good model used with another model's vectors is broken (L3 alone found 8 of 8).

**If you missed it, reread:** [short §1](../reading/P4_embeddings.md#1-three-bugs-that-raise-no-error) · [full D.5](../../concepts/P4_embeddings_similarity.md#d5-same-model-for-the-query-and-what-scores-look-like) · book Ch1 p.8/14

</details>
<!-- /q -->

<!-- q id=P4-A-04 type=A set=main -->
### P4-A-04 · Application
**Question:** Two unit vectors have cosine 0.6. What does a FAISS `IndexFlatL2` search report for them, and what does LangChain's relevance score on that number show?

**Reply template:** `FAISS reports ____ (because ____). LangChain shows ____.`

<details><summary>Hint 1</summary>

For unit vectors, L2² = 2 − 2·cos. Does FAISS's L2 index return L2 or L2²?

</details>

<details><summary>Hint 2</summary>

LangChain's Euclidean relevance is 1 − d/√2, with √2 ≈ 1.4142.

</details>

<details><summary>Hint 3</summary>

d = 2 − 2 × 0.6 = 0.8.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
FAISS IndexFlatL2 returns the SQUARED L2:  2 − 2 × 0.6 = 0.8        (true L2 would be √0.8 = 0.8944)
LangChain relevance on it:                 1 − 0.8 / 1.4142 = 0.434
```

A distance: lower is closer. LangChain's formula assumes the true L2 (0 to 2); on FAISS's squared distance (0 to 4) it goes negative once the cosine is under about 0.293. For D-002, 91 of 97 chunks are under it (K5).

**Key points** (a 3 needs every point):
- [ ] FAISS reports 0.8 (squared L2 = 2 − 2·cos).
- [ ] LangChain's relevance is 1 − 0.8/√2 ≈ 0.434.

**For a 4, also:**
- [ ] A self-check or limit: lower FAISS = closer; the relevance score turns negative below cos ≈ 0.293, so do not divide by it.

**Common wrong answers:**
- [ ] "FAISS reports 0.6, the cosine": an L2 index reports a distance.
- [ ] "FAISS reports 0.8944": that is the true L2; FAISS skips the square root.

**If you missed it, reread:** [short §3](../reading/P4_embeddings.md#3-normalise-and-read-the-direction) · book App p.15/23 and Ch12 p.8/14

</details>
<!-- /q -->

<!-- q id=P4-A-05 type=A set=main -->
### P4-A-05 · Application
**Question:** A 300-token chunk has its answer at token 280. Can MiniLM retrieve this chunk because of that answer?

**Reply template:** `____, because MiniLM reads only ____. The answer at token 280 ____.`

<details><summary>Hint 1</summary>

What is MiniLM's length limit, and do the special tokens count?

</details>

<details><summary>Hint 2</summary>

What happens to tokens past the limit: an error, or something quieter?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** No. MiniLM reads at most 256 tokens including [CLS] and [SEP], so 254 tokens of text; the rest is dropped without any error. The answer at token 280 is never seen, so it cannot pull the chunk up the ranking. Measured (S7): a passage whose DAC definition starts at token 300 scores 0.019276 against the question, exactly like its first 254 tokens alone. If the chunk is retrieved for other reasons, the generator still reads the whole text.

**Key points** (a 3 needs every point):
- [ ] No: MiniLM reads only the first 256 tokens (254 of text).
- [ ] The rest is dropped silently, so the answer cannot affect the vector or the rank.

**For a 4, also:**
- [ ] The check and fix: count tokens with the model's own tokenizer before indexing; shorter chunks or a longer-context model; Cohere `truncate="NONE"` to make it an error.

**Common wrong answers:**
- [ ] "Yes, the answer is in the chunk": only the part the model reads counts.
- [ ] "Python raises an error": the extra tokens are cut without an error.

**If you missed it, reread:** [short §6](../reading/P4_embeddings.md#6-text-past-the-limit) · [full D.6](../../concepts/P4_embeddings_similarity.md#d6-truncation-linked-not-repeated) · book Ch1 p.5/14 (the book never mentions the length limit)

</details>
<!-- /q -->

<!-- q id=P4-A-06 type=A set=main -->
### P4-A-06 · Application
**Question:** You keep the first 256 of a unit vector's 1,536 numbers. What is the new vector's length, and what must you do before you store it?

**Reply template:** `Its length is ____ than 1, so ____. This only works well if ____.`

<details><summary>Hint 1</summary>

The length is √(sum of squares). You removed some of the squares.

</details>

<details><summary>Hint 2</summary>

What breaks in a dot-product or L2 index when vectors are not length 1?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Shorter than 1, because you dropped part of the sum of squares (MiniLM cut from 384 to 256 numbers: lengths 0.771 to 0.869, K11). So **rescale it to length 1** (divide by its new length), on both the chunks and the questions; otherwise dot and L2 no longer rank like cosine (at 256 numbers, dot and cosine agreed on the top 5 for only 4 of 8 questions). Cutting works well only for models trained for it (Matryoshka models; Cohere says embed-v4.0 is one, with 256/512/1,024/1,536); re-measure top-k overlap and Hit@k against the full vectors before switching. MiniLM, not trained for it, fell to MRR@10 0.358 at 32 numbers.

**Key points** (a 3 needs every point):
- [ ] The length is below 1.
- [ ] Rescale (normalise) it again, for chunks and questions alike.

**For a 4, also:**
- [ ] Only for Matryoshka-trained models (embed-v4.0's 256/512/1,024), and re-measure top-k overlap and Hit@k before switching.

**Common wrong answers:**
- [ ] "Still 1, cutting does not change the length": it removes part of the sum of squares.
- [ ] "Cutting is free for every model": MiniLM, not trained for it, lost most of its quality at 32 numbers.

**If you missed it, reread:** [short §10](../reading/P4_embeddings.md#10-smaller-vectors) · book Ch1 p.5/14

</details>
<!-- /q -->

<!-- q id=P4-A-07 type=A set=main -->
### P4-A-07 · Application
**Question:** How many Cohere embed calls and how many tokens does it take to embed 10,000 chunks of about 250 tokens each?

**Reply template:** `calls = ____ = ____; tokens = ____; cost ≈ ____ (price ____).`

<details><summary>Hint 1</summary>

How many texts can one Cohere embed call take?

</details>

<details><summary>Hint 2</summary>

Calls are rounded up: ⌈n / 96⌉.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
calls  = ⌈10,000 / 96⌉ = 105
tokens = 10,000 × 250  = 2,500,000
cost   ≈ 2.5 × $0.12   = $0.30    (the $0.12 per million price is from third-party lists: UNVERIFIED)
```

Measure the tokens per chunk instead of guessing (Cohere bills the input tokens it reports per call, `billed_units`), and check the price on the day. Questions are embedded too, with `search_query`, in their own calls.

**Key points** (a 3 needs every point):
- [ ] At most 96 texts per call, so ⌈10,000 / 96⌉ = 105 calls.
- [ ] 2,500,000 tokens.

**For a 4, also:**
- [ ] Says the price is unverified and that tokens per chunk should be measured (billed units), not assumed.

**Common wrong answers:**
- [ ] "104 calls": 10,000 / 96 = 104.17, rounded up to 105.
- [ ] "10,000 calls": one call takes up to 96 texts.

**If you missed it, reread:** [short §11](../reading/P4_embeddings.md#11-choosing-a-model-and-its-cost) · book Ch1 p.7/14

</details>
<!-- /q -->

<!-- q id=P4-T-01 type=T set=main -->
### P4-T-01 · Transfer (practice item)
**Question:** A help-desk search uses a model whose vectors have very different lengths. Should it use the dot product or cosine?

**Reply template:** `I would use ____, because ____. I would check it by ____.`

<details><summary>Hint 1</summary>

What does the dot product reward that cosine ignores? Does that length mean anything for this model?

</details>

<details><summary>Hint 2</summary>

Where would you find out how the model was trained? How would you measure the choice?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Use the similarity the model was trained with, so read the model card first. If it was trained with cosine (like MiniLM), length carries no meaning: use cosine, or normalise both sides and use the dot product (same ranking). Otherwise long vectors win just for being long (toy: raw dot changed the top result for 68 of 100 questions when lengths varied, S3). If the card says the model was trained with the dot product on unnormalised vectors, keep the dot product: the length is then part of the signal. Either way, measure: Hit@k and MRR on labelled help-desk questions, dot vs cosine, same chunks, retrieval only.

**Key points** (a 3 needs every point):
- [ ] Check how the model was trained (model card): the similarity to use is the training one.
- [ ] If length carries no meaning: cosine, or normalise and use the dot product (same ranking).
- [ ] Measure the choice on labelled questions (Hit@k, MRR), retrieval only.

**For a 4, also:**
- [ ] When not to normalise: a model trained with the dot product on unnormalised vectors, where length is signal.

**Common wrong answers:**
- [ ] "Always cosine, it is the standard": DPR, for example, was trained with the dot product.
- [ ] "Always the dot product, it is faster": on unnormalised vectors it rewards long vectors.

**If you missed it, reread:** [short §3](../reading/P4_embeddings.md#3-normalise-and-read-the-direction) · [short §5](../reading/P4_embeddings.md#5-where-the-closeness-comes-from) · [full D.4](../../concepts/P4_embeddings_similarity.md#d4-does-your-model-already-output-unit-vectors-check-do-not-assume) · book App p.14–15/23

</details>
<!-- /q -->

<!-- q id=P4-T-02 type=T set=main -->
### P4-T-02 · Transfer
**Question:** For a search over legal contracts, you must choose between the current leaderboard winner and a smaller model. How do you decide?

**Reply template:** `I would shortlist with ____, then decide by ____, checking ____.`

<details><summary>Hint 1</summary>

What does a leaderboard average over, and is your domain in it?

</details>

<details><summary>Hint 2</summary>

What must stay the same between the two models for the comparison to be fair? What else matters besides quality?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The leaderboard (MTEB) is a shortlist, not a decision: it averages over many public datasets, no method wins everywhere, and your contracts are not in it. Use its **retrieval** tasks to shortlist both models, then build a labelled set of real contract questions with their right passages and compare the two on the **same chunks**, with Hit@k and MRR, retrieval only. Also check what the setup needs: the length limit against your chunk lengths (contracts are long), the query label or prefix each model expects, the licence and where the text goes (an API vs local), memory per vector and cost. Re-embed everything with the chosen model, and never mix models in one index.

**Key points** (a 3 needs every point):
- [ ] The leaderboard is only a shortlist (averages; not your domain).
- [ ] Decide on your own labelled contract questions, same chunks, retrieval metrics (Hit@k, MRR).
- [ ] Check practical fit: length limit, query label, licence/privacy, cost or memory.

**For a 4, also:**
- [ ] Says how much data a decision needs (a handful of questions shows a mechanism, not a winner) and that switching means re-embedding everything.

**Common wrong answers:**
- [ ] "Take the leaderboard winner": it is the best average on someone else's data.
- [ ] "Take the bigger model, it is always better": MMTEB's best public model was smaller than several LLM-based embedders.

**If you missed it, reread:** [short §11](../reading/P4_embeddings.md#11-choosing-a-model-and-its-cost) · [short §6](../reading/P4_embeddings.md#6-text-past-the-limit) · book Ch1 p.5/14

</details>
<!-- /q -->

<!-- q id=P4-T-03 type=T set=main -->
### P4-T-03 · Transfer
**Question:** 2 million chunks stored as 1,536 float32 numbers each do not fit in your server's RAM. What are your options, and how do you check that quality holds?

**Reply template:** `It needs ____ GB. Options: ____, ____, ____. I check by ____.`

<details><summary>Hint 1</summary>

Bytes per vector = numbers × bytes per number. Which of the two factors can you shrink?

</details>

<details><summary>Hint 2</summary>

Which model property decides whether keeping fewer numbers is safe? What do you compare the smaller vectors against?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
2,000,000 × 1,536 × 4 bytes = 12.288 GB (float32)
int8  (1 byte per number):    3.072 GB        binary (1 bit): 0.384 GB
256 numbers, float32:          2.048 GB
```

Options: **fewer numbers** (only safe for a Matryoshka-trained model such as embed-v4.0 with `output_dimension` 256/512/1,024; rescale to length 1 after cutting); **fewer bits** (int8 or binary; often search with binary, then rescore the shortlist with full floats); or keep the vectors on disk with an approximate index (P5, D2). Check quality on labelled questions: top-k overlap with the full vectors and Hit@k / MRR, same chunks; keep the smaller setting only if they stay level. On the climate chunks, int8 kept 4.4 of float's top 5 on average (K12), an illustration only.

**Key points** (a 3 needs every point):
- [ ] About 12.3 GB (2 M × 1,536 × 4 bytes).
- [ ] At least two options: fewer numbers (Matryoshka, then rescale), fewer bits (int8/binary), or a disk-based/approximate index.
- [ ] Check against the full vectors: top-k overlap and Hit@k on labelled questions.

**For a 4, also:**
- [ ] Names when cutting is unsafe (a model not trained for it: MiniLM fell to MRR@10 0.358 at 32 numbers) or the binary-then-rescore pattern.

**Common wrong answers:**
- [ ] "Just keep the first 256 numbers of any model": only Matryoshka-trained models survive that, and the cut vector must be rescaled.
- [ ] "Use a smaller vector and do not re-measure": quality must be checked on your questions.

**If you missed it, reread:** [short §10](../reading/P4_embeddings.md#10-smaller-vectors) · book Ch1 p.6/14

</details>
<!-- /q -->
