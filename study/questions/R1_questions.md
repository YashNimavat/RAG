<!-- kit:questions concept=R1 version=1 -->
# R1 questions: sparse vs dense vs hybrid; fusion

**How to use:** write your answer and a confidence (1–3) first. Then open the answer and tick the key points you really wrote.

**Where the numbers come from:** every number in the answers was produced by `sources/verification/R1/r1_measure.py` ([R1_FACTS](../../sources/verification/R1/R1_FACTS.md)). "Draft seeds" are the 10 `llm-draft` items of 06 §6.7: observations for learning, never an evaluation result. "Toy" numbers are made up.

<!-- q id=R1-PRE-01 type=R set=pre -->
### R1-PRE-01 · Recall (before reading)
**Question:** Why can't you rank chunks by simply adding a BM25 score to a cosine score?

**Reply template:** `Because BM25 scores ____ while cosine scores ____, so the sum ____.`

<details><summary>Hint 1</summary>

Think about how big each number usually is for the same chunk.

</details>

<details><summary>Hint 2</summary>

A cosine of two unit vectors lies between −1 and 1. A BM25 score has no fixed upper end. What happens to a sum when one part is 30 times larger than the other?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The two scores live on different scales. A cosine of unit vectors lies between −1 and 1; on the 10 draft seeds the best dense score is 0.26 to 0.71. BM25 has no fixed range; the best BM25 score on the same seeds is 7.0 to 43.6. In a plain sum the bigger scale decides: the raw-sum top-4 shares 37 of its 40 chunks with the BM25 top-4, so the dense signal almost disappears.

```
D-008, the Kigali chunk:   dense 0.2535   +   BM25 9.4618   =   9.7153
```

**Key points** (a 3 needs every point):
- [ ] The scales differ: cosine is bounded (−1 to 1), BM25 is unbounded.
- [ ] In a plain sum the larger scale (BM25) decides the ranking.

**For a 4, also:**
- [ ] Names a fix (normalise each list first, or fuse the ranks with RRF) and gives a number or an example of BM25 dominating (37 of 40 shared chunks on the draft seeds, or the book's 0.87 vs 14.2).

**Common wrong answers:**
- [ ] "You can add them, because both are similarity scores": they measure different things on different scales; a BM25 score of 3 is not "better" than a cosine of 0.9.
- [ ] "Just divide BM25 by 10": a fixed factor is a guess, and BM25's scale moves with the corpus (N, document frequency and average length, P3).

**If you missed it, reread:** [short §3](../reading/R1_hybrid_fusion.md#3-why-you-cannot-add-the-two-scores) · [full D.2](../../concepts/R1_hybrid_fusion.md#d2-why-raw-scores-cannot-be-added) · book Ch12 p.7–8/14

</details>
<!-- /q -->

<!-- q id=R1-PRE-02 type=R set=pre -->
### R1-PRE-02 · Recall (before reading)
**Question:** Name one kind of question where keyword search beats dense search, and one where dense search wins.

**Reply template:** `Keyword search wins on ____, because ____. Dense search wins on ____, because ____.`

<details><summary>Hint 1</summary>

Think of a question that contains an acronym or a code, and one that uses different words from the document.

</details>

<details><summary>Hint 2</summary>

BM25 needs the same token on both sides. An embedding needs a similar meaning. Which kind of question breaks each one?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Keyword search (BM25) wins on **exact identifiers**: acronyms, codes, names and numbers. A rare token gets a high IDF, so the one chunk that contains it stands out. Dense search wins on **paraphrase**: the question uses other words than the chunk, and BM25 can only match tokens.

```
"What does BECCS stand for?"  (demonstration query)     dense rank 4    BM25 rank 1
D-006 "solar panels on lakes or reservoirs" (draft seed)  dense rank 1    BM25 rank 2
```

In D-006 the evidence chunk talks about solar farms on water bodies and never says "lakes" or "panels"; BM25 puts a page-22 chunk that contains "panels" first.

**Key points** (a 3 needs every point):
- [ ] Keyword search wins on exact terms: acronyms, codes, names, numbers.
- [ ] Dense search wins on paraphrase: the question and the chunk use different words.

**For a 4, also:**
- [ ] Gives both mechanisms (a rare token's IDF vs closeness of meaning) and one limit: BM25 works only if the tokenizer makes the same token on both sides (P3: `(IPCC)` never matches `IPCC`).

**Common wrong answers:**
- [ ] "Dense search is always better, because it understands meaning": on exact identifiers it can rank chunks about the topic above the chunk that names the term (book Ch12 p.1/14; BECCS at rank 4 here).
- [ ] "Keyword search also finds synonyms": BM25 matches tokens only; "accord" never matches "Agreement".

**If you missed it, reread:** [short §1](../reading/R1_hybrid_fusion.md#1-the-failure-hybrid-retrieval-fixes) · [full B.1](../../concepts/R1_hybrid_fusion.md#b1-dense-retrieval-pushes-exact-terms-down) · book Ch12 p.1–2/14

</details>
<!-- /q -->

<!-- q id=R1-PRE-03 type=A set=pre -->
### R1-PRE-03 · Application (before reading)
**Question:** A chunk is first in the BM25 list but missing from the dense list: should hybrid retrieval still put it near the top?

**Reply template:** `It depends on ____. With weighted fusion it ____; with RRF it ____.`

<details><summary>Hint 1</summary>

A chunk that is missing from a list gets nothing from that list. What does it get from the list where it is first?

</details>

<details><summary>Hint 2</summary>

Weighted fusion: (1 − w) × its normalised score, and a list's best chunk normalises to 1.0. RRF: 1/(60 + 1). Compare each with what a chunk found by both lists gets.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** It depends on the fusion method.
- **Weighted min-max fusion** gives it (1 − w) × 1.0, for example 0.5 at weights 0.5/0.5. That can still be near the top.
- **RRF with k = 60** gives it only 1/61 = 0.0164. A chunk in both top-50 lists gets at least 2/110 = 0.0182. So it falls below **every** chunk that both lists found.

Measured mirror image on draft seed D-008: the dense rank-1 chunk (page 10) is missing from the BM25 top-50.

```
min-max 0.5/0.5:  fused rank 2        RRF k = 60:  fused rank 31
```

**Key points** (a 3 needs every point):
- [ ] A chunk missing from one list gets nothing from that list.
- [ ] Weighted fusion still gives it (1 − w) × 1.0 from the list where it is best, so it can stay near the top.
- [ ] RRF gives it 1/61, which is less than any chunk found by both short lists, so it drops below all of them.

**For a 4, also:**
- [ ] Says that which behaviour you want depends on whether single-retriever hits are often right (exact terms), and that this is measured per question category, not assumed.

**Common wrong answers:**
- [ ] "Fusion always keeps each retriever's best chunk at the top": RRF dropped one to rank 31 (D-008).
- [ ] "A missing chunk counts as an average score": the book's rule (Ch12 p.9/14) is that only the other retriever's weighted score counts.

**If you missed it, reread:** [short §6](../reading/R1_hybrid_fusion.md#6-reciprocal-rank-fusion-ranks-not-scores) · [full D.7](../../concepts/R1_hybrid_fusion.md#d7-the-consensus-rule-hidden-in-rrf) · book Ch12 p.9/14

</details>
<!-- /q -->

<!-- q id=R1-R-01 type=R set=main -->
### R1-R-01 · Recall
**Question:** What does each retriever miss that the other one catches?

**Reply template:** `Dense retrieval misses ____. BM25 misses ____.`

<details><summary>Hint 1</summary>

The book's BPA example shows both blind spots, one on each page (Ch12 p.1–2/14).

</details>

<details><summary>Hint 2</summary>

One retriever matches meaning, the other matches tokens. Which kind of question breaks each?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Dense retrieval can miss **exact terms**: it ranks chunks *about* the topic above the one chunk that *names* the acronym, code or number. BM25 misses **paraphrase**: a chunk that says the same thing in other words shares no tokens with the question.

```
rank of the chunk that names the term (demonstration, 97 v0 chunks)
                  dense   BM25
"IPCC"              3       1
"BECCS"             4       1
"methane CH4"       4       1
D-006 paraphrase (draft seed): dense 1, BM25 2
```

**Key points** (a 3 needs every point):
- [ ] Dense misses exact terms (acronyms, codes, names, numbers): chunks on the same topic outrank the chunk that names the term.
- [ ] BM25 misses paraphrase: no shared token, no score.

**For a 4, also:**
- [ ] Gives the mechanism (one vector for the whole meaning vs token overlap weighted by IDF) and one limit, for example that BM25 only works when the tokenizer produces the same token on both sides.

**Common wrong answers:**
- [ ] "Dense retrieval drops rare words because they are not in its vocabulary": the model splits them into subword pieces; the term is blurred into the topic, not removed.
- [ ] "BM25 fails on long questions": the length is not the problem; missing shared tokens is.

**If you missed it, reread:** [short §1](../reading/R1_hybrid_fusion.md#1-the-failure-hybrid-retrieval-fixes) · [full B.1](../../concepts/R1_hybrid_fusion.md#b1-dense-retrieval-pushes-exact-terms-down) · [full B.2](../../concepts/R1_hybrid_fusion.md#b2-bm25-is-misled-by-shared-words) · book Ch12 p.1–2/14

</details>
<!-- /q -->

<!-- q id=R1-R-02 type=R set=main -->
### R1-R-02 · Recall
**Question:** Why must BM25 and cosine scores be normalised before a weighted sum?

**Reply template:** `Because ____. Without it, ____.`

<details><summary>Hint 1</summary>

Look at the two score columns for the Kigali example in the reading.

</details>

<details><summary>Hint 2</summary>

One scale is bounded, the other is not. Which one decides the order of a plain sum?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The two retrievers score on different scales, so their numbers cannot be compared or added. Without normalising, the larger scale decides the order: on the 10 draft seeds, the raw-sum top-4 shares 37 of its 40 chunks with the BM25 top-4. Normalising maps each list onto 0 to 1 first (book Ch12 p.8/14).

```
D-008 dense top score 0.2598     BM25 top score 9.4618
```

**Key points** (a 3 needs every point):
- [ ] The scales differ (cosine bounded, BM25 unbounded), so the numbers are not comparable.
- [ ] Without normalising, the larger-scale retriever (BM25) decides the ranking.

**For a 4, also:**
- [ ] Adds a limit: normalising does not make the numbers mean the same thing. A normalised 1.0 only means "best in this list for this question": D-009 has no answer in the document, yet its best chunk still gets 1.0. (Or: RRF avoids the problem by using ranks.)

**Common wrong answers:**
- [ ] "After normalising, 0.8 from BM25 and 0.8 from dense mean an equally strong match": the book says so (Ch12 p.9/14), but a normalised score only says where a chunk sits in its own list.

**If you missed it, reread:** [short §3](../reading/R1_hybrid_fusion.md#3-why-you-cannot-add-the-two-scores) · [full D.2](../../concepts/R1_hybrid_fusion.md#d2-why-raw-scores-cannot-be-added) · [full D.3](../../concepts/R1_hybrid_fusion.md#d3-min-max-what-1-and-0-really-mean) · book Ch12 p.7–9/14

</details>
<!-- /q -->

<!-- q id=R1-R-03 type=R set=main -->
### R1-R-03 · Recall
**Question:** What is the Reciprocal Rank Fusion formula, and what does it use instead of scores?

**Reply template:** `RRF(d) = ____, summed over ____. It uses ____ instead of scores.`

<details><summary>Hint 1</summary>

Each list gives a document a vote that depends only on its position.

</details>

<details><summary>Hint 2</summary>

The vote is 1 divided by (a constant plus the rank). What does a document get from a list it is not in?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** RRF(d) = Σ over the lists of 1 / (k + rank of d in that list), with ranks starting at 1 and usually k = 60 (Cormack et al. 2009, 06 v2.0 card). It uses only the **ranks**, so the two score scales never meet and nothing needs normalising. A list that does not contain d adds nothing.

```
rank 1  → 1/61  = 0.0164
rank 50 → 1/110 = 0.0091
```

**Key points** (a 3 needs every point):
- [ ] RRF(d) = the sum over the lists of 1/(k + rank), ranks from 1.
- [ ] It uses ranks only, so no normalisation is needed.
- [ ] k = 60 by default; a document missing from a list gets nothing from it.

**For a 4, also:**
- [ ] Adds a limit: RRF throws away score gaps (D-008's BM25 winner scores 5 times the runner-up, yet counts only as "rank 1"), and exact ties happen (draft seed D-006), so it needs a tie rule.

**Common wrong answers:**
- [ ] "RRF averages the normalised scores": no score enters the formula, only positions.
- [ ] "Ranks start at 0": the standard form counts from 1; at k = 0 a rank of 0 would divide by zero.

**If you missed it, reread:** [short §6](../reading/R1_hybrid_fusion.md#6-reciprocal-rank-fusion-ranks-not-scores) · [full D.6](../../concepts/R1_hybrid_fusion.md#d6-reciprocal-rank-fusion) · book Ch12 p.8–9/14 (the score-based method RRF replaces; RRF itself is not in the book)

</details>
<!-- /q -->

<!-- q id=R1-R-04 type=R set=main -->
### R1-R-04 · Recall
**Question:** What goes wrong in the repo's `fusion_retrieval` function (`fusion_retrieval.ipynb` cell 17)?

**Reply template:** `The three arrays come back in ____ orders, so ____. A test that would catch it: ____.`

<details><summary>Hint 1</summary>

Write down, for `all_docs`, `bm25_scores` and `vector_scores`, which order each one is in.

</details>

<details><summary>Hint 2</summary>

The first is sorted by distance to the empty string, the second is in corpus order, the third is sorted by distance to the query. The sum adds them position by position, and the result is read from `all_docs`.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** It mixes three different orders position by position. `all_docs` is sorted by distance to the **empty string**, `bm25_scores` is in **corpus** order, and `vector_scores` is sorted by distance to the **query**. The sum adds element i of the last two, which belong to different chunks, and the function then returns `all_docs[i]`, a third chunk. Measured on our 97 chunks, with MiniLM in place of OpenAI (the repo's logic transcribed; the notebook itself not run):

```
cell-19 query, top-5:       repo-style vs aligned: 0 of 5 chunks in common
8 draft seeds, top-4:       repo-style Hit@4 0/8, CE@4 0/8      aligned Hit@4 8/8, CE@4 8/8
alpha = 1.0:                the same 5 chunks for all 10 seed questions
```

**Key points** (a 3 needs every point):
- [ ] The vector scores, the BM25 scores and the returned chunks are in three different orders.
- [ ] So the sum mixes the scores of different chunks, and the function returns yet another chunk.
- [ ] Measured: the transcribed logic finds no evidence in the top-4 for any draft seed (0/8); the aligned version 8/8.

**For a 4, also:**
- [ ] Names a test that would have caught it: with alpha = 1.0 the output must equal the dense ranking (the buggy code returns the same 5 chunks for every question).

**Common wrong answers:**
- [ ] "The only bug is the missing epsilon in the script": that gives NaN when every BM25 score is equal (script L81), but the misalignment breaks every query, with or without epsilon.
- [ ] "Fixing the tokenizer fixes it": with `tok_norm` BM25 the transcribed logic still gets 0/8.

**If you missed it, reread:** [short §7](../reading/R1_hybrid_fusion.md#7-the-repos-fusion-mixes-up-its-documents) · [full D.9](../../concepts/R1_hybrid_fusion.md#d9-the-repos-misalignment-bug-line-by-line) · book Ch12 p.10/14 (the sketch assumes each score belongs to one chunk)

</details>
<!-- /q -->

<!-- q id=R1-R-05 type=R set=main -->
### R1-R-05 · Recall
**Question:** After min-max normalisation, what score does the last chunk of each list get, and why does that matter?

**Reply template:** `It gets ____, which is the same as ____, so ____.`

<details><summary>Hint 1</summary>

Put the lowest score of a list into (s − min) / (max − min).

</details>

<details><summary>Hint 2</summary>

Compare the result with what a chunk that is missing from the list gets in weighted fusion (book Ch12 p.9/14).

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** It gets **0**, which is exactly what a chunk **missing** from that list gets. So the last chunk a retriever found counts as if that retriever had not found it. At the other end, the top chunk always gets 1.0, even when nothing in the list answers the question.

```
toy dense list:  A 0.62 → 1.00   B 0.58 → 0.81   C 0.41 → 0.00   (C was found, but scores like a miss)
D-009 (no answer in the document):  best dense chunk 0.3099 → 1.0   best BM25 chunk 6.9559 → 1.0
```

**Key points** (a 3 needs every point):
- [ ] The lowest chunk of a list gets 0 and the highest gets 1.
- [ ] 0 is also what a missing chunk gets, so the last-ranked hit counts like no hit.

**For a 4, also:**
- [ ] Adds the consequence: the result depends on where the list is cut (the cut-off decides which chunk is "lowest"), and a 1.0 does not mean "relevant" (D-009 and D-010 have no answer).

**Common wrong answers:**
- [ ] "Min-max keeps the real gaps, so the scores stay faithful": it keeps the relative gaps inside one list, but its 0 and 1 are set by whichever chunks happen to be first and last.

**If you missed it, reread:** [short §5](../reading/R1_hybrid_fusion.md#5-weighted-fusion-and-the-zero-that-means-two-things) · [full D.3](../../concepts/R1_hybrid_fusion.md#d3-min-max-what-1-and-0-really-mean) · book Ch12 p.8–9/14

</details>
<!-- /q -->

<!-- q id=R1-A-01 type=A set=main -->
### R1-A-01 · Application (the R1 review item)
**Question:** Dense ranks [A, B, C] and BM25 ranks [C, A, D]: compute RRF with k = 60 and give the fused order.

**Reply template:** `A = ____, B = ____, C = ____, D = ____ ; fused order: ____ , ____ , ____ , ____`

<details><summary>Hint 1</summary>

Each document gets 1/(60 + rank) from every list it is in. Ranks start at 1.

</details>

<details><summary>Hint 2</summary>

A is rank 1 in dense and rank 2 in BM25, so A = 1/61 + 1/62. Do the same for C (dense rank 3, BM25 rank 1). B and D are each in one list only.

</details>

<details><summary>Hint 3</summary>

A = 0.016393 + 0.016129. C = 0.015873 + 0.016393. B = 1/62, D = 1/63. Now sort.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
A = 1/61 + 1/62 = 0.032522
C = 1/63 + 1/61 = 0.032266
B = 1/62        = 0.016129
D = 1/63        = 0.015873
fused order: A, C, B, D
```

A and C are in both lists, so they come first. A beats C by only 0.000256: both have one rank-1 vote, and A's other vote (rank 2) is worth more than C's (rank 3). The order stays the same at k = 0, 1 and 120. This is the order you reached in the O1 diagnostic by reasoning about agreement; now it has a formula.

**Key points** (a 3 needs every point):
- [ ] Uses 1/(60 + rank) with ranks from 1, and adds the votes from both lists.
- [ ] A ≈ 0.0325 and C ≈ 0.0323 (both lists); B ≈ 0.0161 and D ≈ 0.0159 (one list each).
- [ ] Fused order A, C, B, D.

**For a 4, also:**
- [ ] Self-checks: every document in both lists must beat every document in one list (the worst both-list score, 2/63 = 0.0317, is above the best one-list score, 1/61 = 0.0164), and A beats C because 1/62 > 1/63.

**Common wrong answers:**
- [ ] "C first, because it is BM25's best": one rank-1 vote (1/61) does not beat A's two votes.
- [ ] "I normalised the scores first": RRF uses no scores, only positions.

**If you missed it, reread:** [short §6](../reading/R1_hybrid_fusion.md#6-reciprocal-rank-fusion-ranks-not-scores) · [full F](../../concepts/R1_hybrid_fusion.md#part-f--worked-example-by-hand) · [full D.6](../../concepts/R1_hybrid_fusion.md#d6-reciprocal-rank-fusion) · book Ch12 p.7/14 (the two overlapping lists; RRF itself is not in the book)

</details>
<!-- /q -->

<!-- q id=R1-A-02 type=A set=main -->
### R1-A-02 · Application
**Question:** With dense scores A 0.62, B 0.58, C 0.41 and BM25 scores C 7.9, A 2.1, D 1.8, what is the min-max fused order at weights 0.3 dense / 0.7 BM25?

**Reply template:** `normalised dense: ____; normalised BM25: ____; fused: A = ____, B = ____, C = ____, D = ____ → order ____`

<details><summary>Hint 1</summary>

Normalise each list on its own with (s − min)/(max − min). A document missing from a list gets 0 from it.

</details>

<details><summary>Hint 2</summary>

Dense: A → 1, C → 0, B → (0.58 − 0.41)/0.21. BM25: C → 1, D → 0, A → (2.1 − 1.8)/6.1. Then fused = 0.3 × dense + 0.7 × BM25.

</details>

<details><summary>Hint 3</summary>

Dense B = 0.8095 and BM25 A = 0.0492. A = 0.3 × 1 + 0.7 × 0.0492; B = 0.3 × 0.8095; C = 0.7 × 1; D = 0.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** (toy numbers)

```
dense min-max:  A 1.0000   B 0.8095   C 0.0000
BM25  min-max:  C 1.0000   A 0.0492   D 0.0000
0.3 / 0.7:      C 0.7000   A 0.3344   B 0.2429   D 0.0000    →  C, A, B, D
```

The same lists give A, C, B, D at 0.5/0.5 and A, B, C, D at 0.6/0.4. So the weight alone decides which of A, B and C comes first or second: BM25's favourite C wins once BM25 carries most of the weight.

**Key points** (a 3 needs every point):
- [ ] Normalises each list separately (dense B = 0.8095, BM25 A = 0.0492).
- [ ] Gives a missing document 0 from the list it is missing from (B from BM25, D from dense).
- [ ] Fused C 0.7000, A 0.3344, B 0.2429, D 0 → order C, A, B, D.

**For a 4, also:**
- [ ] Self-checks: no fused score can exceed the sum of the weights (1.0), and C's score must equal the BM25 weight exactly, because C is BM25's best and dense's worst (0).

**Common wrong answers:**
- [ ] "Normalise all six scores together": then BM25's large numbers squeeze every cosine to about 0; each list is normalised on its own.
- [ ] "B gets an average BM25 score because it is missing": a missing document gets 0 from that list (book Ch12 p.9/14).

**If you missed it, reread:** [short §5](../reading/R1_hybrid_fusion.md#5-weighted-fusion-and-the-zero-that-means-two-things) · [full F](../../concepts/R1_hybrid_fusion.md#part-f--worked-example-by-hand) · [full D.5](../../concepts/R1_hybrid_fusion.md#d5-weighted-fusion-over-aligned-ids) · book Ch12 p.8–9/14

</details>
<!-- /q -->

<!-- q id=R1-A-03 type=A set=main -->
### R1-A-03 · Application (what if k changes?)
**Question:** For the ranked lists [0, 1, 2, 3, 4] and [4, 1, 3, 2, 0], which document wins RRF at k = 60, and which at k = 0?

**Reply template:** `k = 60: document ____ wins, because ____. k = 0: document ____ wins, because ____.`

<details><summary>Hint 1</summary>

Document 1 is rank 2 in both lists. Documents 0 and 4 are rank 1 in one list and rank 5 in the other.

</details>

<details><summary>Hint 2</summary>

Compare 2/(k + 2) with 1/(k + 1) + 1/(k + 5), once at k = 60 and once at k = 0.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
k = 60:  doc 1 = 2/62 = 0.03226     docs 0 and 4 = 1/61 + 1/65 = 0.03178    → 1 wins
k = 0:   doc 1 = 2/2  = 1.00000     docs 0 and 4 = 1/1  + 1/5  = 1.20000    → 0 wins (tied with 4; smaller id)
fused order: k = 60 [1, 0, 4, 2, 3]      k = 0 [0, 4, 1, 2, 3]
```

A large k flattens the votes, so agreement (rank 2 twice) wins. With k = 0, rank 1 dominates: one first place is worth five fifth places.

**Key points** (a 3 needs every point):
- [ ] k = 60: document 1 wins (0.0323 vs 0.0318).
- [ ] k = 0: document 0 wins (1.2 vs 1.0); it ties with document 4 and goes first by the smaller id.
- [ ] Mechanism: a small k rewards a single top rank; a large k rewards agreement.

**For a 4, also:**
- [ ] Adds the measured size on the draft seeds: k from 60 to 0 changes the ordered top-4 of 5 of the 10 seeds but not CE@4 (8/8 both), so k is a setting to record, not a constant to forget.

**Common wrong answers:**
- [ ] "k never changes the order; it only scales the scores": it changed the winner here, and 5 of 10 seed top-4 lists.
- [ ] "At k = 0 document 1 still wins, because it is high in both lists": the vote of a rank-1 position (1/1) outweighs two rank-2 votes.

**If you missed it, reread:** [short §6](../reading/R1_hybrid_fusion.md#6-reciprocal-rank-fusion-ranks-not-scores) · [full D.6](../../concepts/R1_hybrid_fusion.md#d6-reciprocal-rank-fusion) · book Ch12 p.11/14 (the book's only tuning knob is the weight; k is not in the book)

</details>
<!-- /q -->

<!-- q id=R1-A-04 type=A set=main -->
### R1-A-04 · Application (debugging)
**Question:** This fusion returns the same five chunks for every question when `alpha = 1.0`: what is the bug, and what one test would have caught it?

```python
all_docs = store.similarity_search("", k=n)                       # every chunk, nearest to "" first
bm25 = minmax(bm25_index.get_scores(query.split()))               # corpus order
dist = np.array([s for _, s in store.similarity_search_with_score(query, k=n)])   # nearest to the query first
vec = 1 - minmax(dist)
top5 = [all_docs[i] for i in np.argsort(alpha * vec + (1 - alpha) * bm25)[::-1][:5]]
```

**Reply template:** `The bug is ____. With alpha = 1.0 it returns ____, because ____. The test: ____.`

<details><summary>Hint 1</summary>

At alpha = 1.0 only `vec` counts. In what order is `vec`, and what does `argsort` of it return?

</details>

<details><summary>Hint 2</summary>

`vec` is already sorted by closeness to the query, so after `1 − minmax` it falls from 1 to 0 by position. Which positions does argsort pick, and which chunks sit at those positions of `all_docs`?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The arrays are combined **by position**, and they are in three different orders. `vec` is already sorted by closeness to the query, so after normalising it is just a ramp from 1 down to 0. At alpha = 1.0 the argsort returns positions 0 to 4, and `all_docs[0:5]` are the chunks nearest to the **empty string**: the same for every question.

```
measured (MiniLM, our 97 chunks, the repo's logic transcribed):
alpha = 1.0 over the 10 draft seeds: 1 distinct top-5 list; it equals no seed's dense top-5
```

Fix: keep every score in a dict `{chunk_id: score}` and fuse by id. The test:

```python
assert fuse(dense, bm25, alpha=1.0) == ranked(dense)     # all the weight on dense gives the dense order
```

**Key points** (a 3 needs every point):
- [ ] The three lists are in different orders and are combined by position, not by chunk id.
- [ ] At alpha = 1.0 the vector part is a ramp by position, so the output is `all_docs[:5]`, the chunks nearest to the empty string.
- [ ] Fix: key every score by chunk id and fuse over aligned ids.

**For a 4, also:**
- [ ] Gives the test (alpha = 1.0 must return the dense ranking; alpha = 0.0 the BM25 ranking) and says it fails on this code before any evaluation is run.

**Common wrong answers:**
- [ ] "The empty-string search is only slow": it also fixes the order of `all_docs`, which is where the results are read from.
- [ ] "It is a generation problem, because the answers are bad": the wrong chunks are retrieved, so the LLM never sees the evidence (CR-11).

**If you missed it, reread:** [short §7](../reading/R1_hybrid_fusion.md#7-the-repos-fusion-mixes-up-its-documents) · [full D.9](../../concepts/R1_hybrid_fusion.md#d9-the-repos-misalignment-bug-line-by-line) · [full J](../../concepts/R1_hybrid_fusion.md#part-j--failure-and-debugging) · book Ch12 p.10/14

</details>
<!-- /q -->

<!-- q id=R1-T-01 type=T set=main -->
### R1-T-01 · Transfer (when not to use hybrid)
**Question:** A support team searches a 25-page FAQ where every question is a plain "how do I …" sentence and nobody types codes or product names: would you add BM25 hybrid retrieval?

**Reply template:** `I would ____, because ____. I would check by ____. I would change my mind if ____.`

<details><summary>Hint 1</summary>

Which failure does BM25 fix, and does this question set have it?

</details>

<details><summary>Hint 2</summary>

Think about the cost (a second index, tokenizer choices), the risk on paraphrase questions, and how you would measure it on a small labelled set.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Probably not at first. Hybrid retrieval fixes exact-term misses, and these questions contain no identifiers. They are paraphrases, where BM25 can pull in chunks that merely share common words: on draft seed D-006, BM25 and min-max fusion pushed the evidence from rank 1 to rank 2. The corpus is small, which is one of the book's "overkill" cases (Ch12 p.12/14). Measure before deciding: label 20 to 30 real questions, compare dense against hybrid on CE@k and MRR per category, and note the extra latency. Add BM25 only if exact-term questions appear and dense misses them.

**Key points** (a 3 needs every point):
- [ ] Hybrid targets exact-term misses, which this FAQ does not have.
- [ ] The risk: on paraphrase questions BM25 can add lookalike chunks and push the evidence down (D-006).
- [ ] Decide by measuring dense against hybrid on a labelled set (CE@k, MRR), not by default.

**For a 4, also:**
- [ ] Says what would change the answer (users start typing error codes or product names and dense misses them in the evaluation) and keeps retrieval metrics separate from answer quality.

**Common wrong answers:**
- [ ] "Hybrid is always better, so add it": it costs a second index and a tokenizer, and on our seeds it improved ranks but never CE@4 (8/8 with dense alone).
- [ ] "BM25 cannot hurt; it only adds candidates": weighted fusion moved a lookalike chunk above the evidence on D-006.

**If you missed it, reread:** [short §8](../reading/R1_hybrid_fusion.md#8-when-not-to-use-hybrid-retrieval) · [full K](../../concepts/R1_hybrid_fusion.md#part-k--engineering-decisions) · [full B.2](../../concepts/R1_hybrid_fusion.md#b2-bm25-is-misled-by-shared-words) · book Ch12 p.12–13/14

</details>
<!-- /q -->

<!-- q id=R1-T-02 type=T set=main -->
### R1-T-02 · Transfer
**Question:** BM25 indexes whole documents, the vector index holds chunks, and RRF fuses the two lists by chunk id: what goes wrong?

**Reply template:** `____ goes wrong, because ____. I would test for it with ____.`

<details><summary>Hint 1</summary>

Which ids does each list contain?

</details>

<details><summary>Hint 2</summary>

RRF adds votes for the **same id**. If one list ranks documents and the other ranks chunks, can any id appear in both?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The two lists rank different units, so their ids never match. The BM25 votes go to document ids that no chunk has. Either they are dropped, and the fusion silently becomes dense-only, or document ids come out of the fusion and the context builder cannot find them as chunks. Nothing raises an error. The fix is that both retrievers index **the same chunks** (book Ch12 p.5–6/14: one set of chunks, indexed twice). Test: every fused id must exist in the shared chunk catalogue, and with all the weight on BM25 the fused list must equal the BM25 ranking of chunks. Then measure CE@k per category before and after the fix.

**Key points** (a 3 needs every point):
- [ ] The two lists rank different units (documents vs chunks), so the ids never match.
- [ ] The BM25 votes never reach a chunk: the fusion becomes dense-only, or returns ids that are not chunks, with no error.
- [ ] Fix: build both indexes over the same chunk ids.

**For a 4, also:**
- [ ] Gives a test that catches it (every fused id is in the chunk catalogue; BM25-only fusion equals the BM25 chunk ranking) and a measurement (CE@k per category, before and after).

**Common wrong answers:**
- [ ] "RRF needs no alignment, because it uses ranks": the ranks belong to ids; both lists must rank the same ids.

**If you missed it, reread:** [short §7](../reading/R1_hybrid_fusion.md#7-the-repos-fusion-mixes-up-its-documents) · [full D.1](../../concepts/R1_hybrid_fusion.md#d1-the-pipeline-two-lists-over-the-same-chunk-ids) · [full D.9](../../concepts/R1_hybrid_fusion.md#d9-the-repos-misalignment-bug-line-by-line) · book Ch12 p.5–6/14

</details>
<!-- /q -->

<!-- q id=R1-T-03 type=T set=main -->
### R1-T-03 · Transfer (compare two designs)
**Question:** Your BM25 library will be replaced next quarter and you have 300 labelled questions: would you choose RRF or tuned weighted score fusion?

**Reply template:** `I would choose ____, because ____. I would measure ____ on ____. I would not ____ when ____.`

<details><summary>Hint 1</summary>

Which method notices when one scorer changes its scale?

</details>

<details><summary>Hint 2</summary>

Weighted fusion needs a weight tuned on labelled data and depends on the shape of the scores; RRF needs only ranks. What does the library swap do to each?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Start with RRF as the default arm. It uses only ranks, so a BM25 library with a different scale cannot move it: on the draft seeds, RRF's top-4 changed for 0 of 10 seeds under every rescaling, while min-max fusion changed for 4 of 10 when the dense scores were bent by a monotone curve. 300 labelled questions are enough to tune a weight on dev and confirm it once on test, so run weighted fusion as a second arm. Adopt it only if it wins CE@k per category with a paired bootstrap interval, and re-tune it after the library swap. Weighted fusion is worth it when score gaps carry information that ranks throw away (D-008's BM25 winner scores 5 times the runner-up).

**Key points** (a 3 needs every point):
- [ ] RRF ignores score scales, so the library swap cannot move it; weighted fusion can shift.
- [ ] Weighted fusion can use score gaps that RRF throws away, but its weight must be tuned and re-tuned.
- [ ] Decide on dev with CE@k per category and confirm once on test.

**For a 4, also:**
- [ ] Names when not to use weighted fusion (no labelled data, or scorers that change often) and keeps retrieval metrics separate from answer quality.

**Common wrong answers:**
- [ ] "Weighted fusion is always better, because it uses more information": only while its weight fits the current scorers; a changed scale silently changes the fusion.
- [ ] "RRF needs no settings at all": k and the list depth are still settings, and RRF ignores large score gaps.

**If you missed it, reread:** [short §6](../reading/R1_hybrid_fusion.md#6-reciprocal-rank-fusion-ranks-not-scores) · [full D.8](../../concepts/R1_hybrid_fusion.md#d8-what-each-method-ignores-rescaling-one-scorer) · [full K](../../concepts/R1_hybrid_fusion.md#part-k--engineering-decisions) · book Ch12 p.11–12/14

</details>
<!-- /q -->

<!-- q id=R1-R-06 type=R set=interview source=AIQ-04-Q24 -->
### R1-R-06 · Interview (Recall)
**Question:** "How does reciprocal rank fusion work, and why fuse by rank instead of by score?"
*From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md` (question 24), Copyright (c) 2026 Om, MIT License.*

**Reply template:** `RRF adds ____ from each list. Ranks are used because ____. Its limits: ____.`

<details><summary>Hint 1</summary>

Say the formula first, then which problem with scores it avoids.

</details>

<details><summary>Hint 2</summary>

The formula with k = 60; the two scales (cosine bounded, BM25 unbounded); then two limits: the score gaps it loses, and what can still change the ranks.

</details>

<details><summary>Show answer (write yours first)</summary>

> **The repo's answer (excerpt, verbatim).** *From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md`, Copyright (c) 2026 Om, MIT License:*
>
> "**Why ranks, not scores:** BM25 scores are unbounded and corpus-dependent (term frequencies, document lengths); cosine similarities live in a narrow model-specific band (one embedder's "great match" is 0.85, another's is 0.55); neither is a calibrated probability. Adding or averaging them requires normalization (min-max or z-score per query), which is fragile - normalization statistics shift per query, per corpus update, and per model version, so a weighted-score fusion tuned today silently degrades next quarter. Ranks are invariant to all of that."

**Our check of that answer:** the formula, the 1/(60+1) ≈ 0.016 example and the scale argument are right. Three corrections:
1. "Ranks are invariant to all of that" holds for changes of scale that keep each list's order. A new embedding model or a corpus update **reorders** the lists, so the ranks change too.
2. The repo calls k "famously insensitive". On our draft seeds, k from 60 to 0 changed the ordered top-4 of 5 of 10 seeds (CE@4 stayed 8/8). Not a measurement for our data either way.
3. Its code sorts with `sorted(scores, key=scores.get, reverse=True)`, which has no tie rule. Exact ties happen (draft seed D-006), so sort by (−score, chunk_id).

**Model answer:** RRF scores each document by adding 1/(k + rank) over the ranked lists it appears in (ranks from 1, k = 60 by default); a missing document adds nothing. It fuses by rank because BM25 scores are unbounded and corpus-dependent while cosine scores sit in a small, model-specific band, so adding them needs a fragile normalisation. Ranks sidestep that: rescaling either scorer cannot change the result. The cost is that RRF throws away how far ahead a winner was, and the ranks still change when the model or the corpus changes.

**Key points** (a 3 needs every point):
- [ ] RRF(d) = Σ 1/(k + rank), ranks from 1, k ≈ 60; a missing document adds nothing.
- [ ] BM25 and cosine scores are on different scales; using ranks avoids normalising them.
- [ ] Limit: RRF throws away score size (a huge BM25 gap counts as one rank).

**For a 4, also:**
- [ ] Adds a precise boundary: ranks ignore rescaling, but not a new model or corpus; and RRF needs a tie rule.

**Common wrong answers:**
- [ ] "RRF works on the normalised scores": it uses no scores at all.
- [ ] "Ranks never change when you upgrade the embedder": a new model reorders the dense list.

**If you missed it, reread:** [short §6](../reading/R1_hybrid_fusion.md#6-reciprocal-rank-fusion-ranks-not-scores) · [full D.6](../../concepts/R1_hybrid_fusion.md#d6-reciprocal-rank-fusion) · [full D.8](../../concepts/R1_hybrid_fusion.md#d8-what-each-method-ignores-rescaling-one-scorer) · book Ch12 p.8/14

</details>
<!-- /q -->

<!-- q id=R1-A-06 type=A set=interview source=AIQ-04-Q24-followup -->
### R1-A-06 · Interview (Application)
**Question:** "If a doc appears in the dense list only, what's its ceiling in the fused ranking?"
*From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md` (a follow-up of question 24), Copyright (c) 2026 Om, MIT License.*

**Reply template:** `Its best possible RRF score is ____. A doc in both top-50 lists scores at least ____, so ____.`

<details><summary>Hint 1</summary>

The best a one-list document can do is rank 1 in that list. Write its RRF score at k = 60.

</details>

<details><summary>Hint 2</summary>

Compare that with the smallest score a document in both top-50 lists can get: rank 50 in each.

</details>

<details><summary>Show answer (write yours first)</summary>

The repo lists this as a follow-up without an answer. Our answer:

**Model answer:** Its ceiling is 1/(k + 1) = 1/61 = 0.0164. A document in both lists gets at least 2/(k + N) for lists N long: at N = 50 that is 2/110 = 0.0182. So with two lists of depth 61 or less, **every** document both lists found outranks **every** document only one list found.

```
one list, rank 1:          1/61  = 0.016393
both lists, rank 50 each:  2/110 = 0.018182
both lists, rank 62 each:  2/122 = 0.016393    ← the bound breaks at depth 62
```

Measured: the rule held on all 10 draft seeds with top-50 lists (24 to 37 chunks were in both lists). On D-008, the dense rank-1 chunk is missing from the BM25 top-50 and lands at fused rank 31. Weighted min-max fusion puts the same chunk at rank 2.

**Key points** (a 3 needs every point):
- [ ] Ceiling = 1/(k + 1) = 1/61 ≈ 0.0164 at k = 60.
- [ ] A document in both top-50 lists scores at least 2/110 ≈ 0.0182.
- [ ] So with short lists (depth ≤ 61) a one-list document can never beat a document both lists found.

**For a 4, also:**
- [ ] Self-checks the boundary (at depth 62 the two are equal, 2/122 = 1/61) and states the consequence: an exact-term chunk that dense misses entirely cannot reach the top under RRF while other chunks are in both lists.

**Common wrong answers:**
- [ ] "It can still come first if it is rank 1 in its list": not while other documents are in both lists; 1/61 is below all of them.

**If you missed it, reread:** [short §6](../reading/R1_hybrid_fusion.md#6-reciprocal-rank-fusion-ranks-not-scores) · [full D.7](../../concepts/R1_hybrid_fusion.md#d7-the-consensus-rule-hidden-in-rrf) · book Ch12 p.9/14 (the book's missing-chunk rule for weighted fusion; RRF is not in the book)

</details>
<!-- /q -->
