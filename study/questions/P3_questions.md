<!-- kit:questions concept=P3 version=1 -->
# P3 questions: keyword search, TF-IDF and BM25

**How to use:** write your answer and a confidence (1–3) first. Then open the answer and tick the key points you really wrote.

**Where the numbers come from:** `sources/verification/P3/p3_measure.py` and `p3_kit_measure.py` ([P3_FACTS](../../sources/verification/P3/P3_FACTS.md)). Numbers marked "97 chunks" come from R1's run ([R1_FACTS](../../sources/verification/R1/R1_FACTS.md)). Two chunkings of the climate PDF appear: the **91 windows** are P3's plain 1,000-character slices with 200 characters of overlap; the **97 chunks** are the C-lab index. "Toy" numbers are made up. "Draft seeds" are the 10 `llm-draft` items of 06 §6.7: observations for learning, never an evaluation result.

<!-- q id=P3-PRE-01 type=R set=pre -->
### P3-PRE-01 · Recall (before reading)
**Question:** A user searches for "IPCC": why might keyword search find the right chunk when vector search does not?

**Reply template:** `Keyword search matches ____. Vector search might miss it because ____.`

<details><summary>Hint 1</summary>

Think about what each search compares: the exact words, or the overall meaning.

</details>

<details><summary>Hint 2</summary>

BM25 needs the same token in the question and in the chunk, and a rare token weighs a lot. A dense embedding places "IPCC" somewhere near "climate reports" in general. Which chunks crowd around that point?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Keyword search (BM25) matches the **exact token** `ipcc`. Only 1 of the 91 windows contains it, so it gets a high weight (idf 4.0999), and that window scores far above the rest. Dense retrieval turns the question into one point of meaning. A rare acronym lands near its general topic, so chunks *about* climate reports can outrank the chunk that *names* the IPCC. The book tells the same story with a chemical acronym (Ch12 p.1/14).

```
"IPCC" (97 chunks):   dense rank 3     BM25 rank 1 (lower-cased tokens)     BM25 with the repo's split(): not found
```

**Key points** (a 3 needs every point):
- [ ] Keyword search matches the exact token, and a rare token gets a high weight (idf).
- [ ] Dense retrieval blurs the rare acronym into its topic, so chunks about the topic can rank above the chunk that names it.

**For a 4, also:**
- [ ] Gives the boundary: it works only if the tokenizer makes the same token on both sides. The repo's `split()` keeps `(IPCC)` in the text, so the query `IPCC` scores 0 everywhere.

**Common wrong answers:**
- [ ] "Vector search cannot see IPCC because the word is not in the model's vocabulary": the model splits it into subword pieces and still embeds it. On our chunks it ranked the IPCC chunk 3rd, not nowhere.
- [ ] "Keyword search finds it whenever the letters are in the chunk": only if both sides become the same token; under `split()` it finds nothing.

**If you missed it, reread:** [short §1](../reading/P3_bm25.md#1-the-failure-keyword-search-fixes) · [full B.1](../../concepts/P3_bm25.md#b1-dense-retrieval-ranks-the-named-chunk-below-its-topic) · book Ch12 p.1–2/14

</details>
<!-- /q -->

<!-- q id=P3-PRE-02 type=R set=pre -->
### P3-PRE-02 · Recall (before reading)
**Question:** What does "inverse document frequency" reward, and why?

**Reply template:** `IDF gives more weight to ____, because ____.`

<details><summary>Hint 1</summary>

"Document frequency" is counted across the whole collection, not inside one chunk.

</details>

<details><summary>Hint 2</summary>

Compare a word that is in 1 of 6 documents with one that is in 4 of 6. A match on which one tells you more about a chunk?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** IDF rewards words that occur in **few** chunks. A match on a rare word says much more about a chunk than a match on a word that is everywhere. It is computed from the **document frequency** n (how many chunks contain the word), not from how often the word occurs inside one chunk (that is the term frequency, tf).

```
toy, 6 documents:   eu (in 1)  idf 1.299283     bpa (in 2)  0.587787     climate (in 4)  raw −0.587787 → floored to 0.272442
```

**Key points** (a 3 needs every point):
- [ ] It rewards words that occur in few chunks (documents).
- [ ] It is computed from the document frequency (how many chunks contain the word), not from the count inside one chunk.

**For a 4, also:**
- [ ] Gives `rank_bm25`'s formula, ln((N − n + 0.5) / (n + 0.5)), and its boundary: for a word in more than half of the chunks it goes negative, and the library replaces it with a floor (0.25 × the mean idf).

**Common wrong answers:**
- [ ] "IDF counts how often the word appears in the chunk": that is the term frequency (tf).
- [ ] "IDF says how important a word is in English": it is measured on your own collection; the same word gets a different idf in another corpus.

**If you missed it, reread:** [short §2](../reading/P3_bm25.md#2-three-counts-before-any-formula) · [full D.2](../../concepts/P3_bm25.md#d2-three-counts-before-any-formula-and-why-tf-idf-over-rewards-repeats) · book Ch12 p.5/14 and App p.17/23

</details>
<!-- /q -->

<!-- q id=P3-PRE-03 type=R set=pre -->
### P3-PRE-03 · Recall (before reading)
**Question:** A chunk mentions "methane" ten times instead of once: does its BM25 score for "methane" become ten times larger?

**Reply template:** `The score becomes ____, because ____.`

<details><summary>Hint 1</summary>

Does the tenth mention of a word tell you as much about a chunk as the first?

</details>

<details><summary>Hint 2</summary>

BM25's tf part is f × (k1 + 1) / (f + K). For a chunk of average length, K = k1 = 1.5. What happens to the tf part as f grows?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** **No.** It grows, but it **saturates**. At average chunk length with k1 = 1.5, one mention gives a tf part of 1.0 and ten mentions give 2.174, not 10. The ceiling is k1 + 1 = 2.5 times the idf, however many mentions there are. TF-IDF with raw counts, by contrast, does grow ten times.

```
mentions f   1      2      5      10     100    → limit 2.5
tf part      1.000  1.429  1.923  2.174  2.463
```

(This assumes the chunk keeps the same length; nine extra words would also change the length factor.)

**Key points** (a 3 needs every point):
- [ ] No: the score grows but flattens out (saturates).
- [ ] Ten mentions give about 2.17 times one mention, and never more than k1 + 1 = 2.5 times the idf.

**For a 4, also:**
- [ ] Names k1 as the knob that sets how fast it flattens, and contrasts TF-IDF, which grows in a straight line.

**Common wrong answers:**
- [ ] "Yes, ten mentions means ten times as relevant": that is TF-IDF with raw counts; BM25 was built to stop it.
- [ ] "No, extra mentions add nothing after the first": that would be k1 = 0 (present or absent), not the default.

**If you missed it, reread:** [short §5](../reading/P3_bm25.md#5-repeats-flatten-out-k1-and-length-cuts-both-ways-b) · [full D.4](../../concepts/P3_bm25.md#d4-saturation-k1-and-length-normalisation-b) · book Ch12 p.5/14 and App p.22/23

</details>
<!-- /q -->

<!-- q id=P3-PRE-04 type=R set=pre -->
### P3-PRE-04 · Recall (before reading)
**Question:** Two chunks each mention "BPA" once, one 5 words long and one 20 words long: which scores higher, and what controls the gap?

**Reply template:** `The ____ chunk scores higher. The gap is controlled by ____.`

<details><summary>Hint 1</summary>

One mention in a short chunk is a larger share of what that chunk is about.

</details>

<details><summary>Hint 2</summary>

Length enters through K = k1 × (1 − b + b × dl / avgdl). Which chunk has the larger K, and what does a larger K do to the tf part?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The **short** chunk. Length enters through K: a longer chunk has a larger K, so the same single mention adds less. The parameter **b** (0 to 1) sets how much length matters; at b = 0 both chunks score the same.

```
small made-up corpus (avgdl 14.17):   b = 0.75:  5 words 0.829243,  20 words 0.495899      b = 0:  0.587787 each
```

**Key points** (a 3 needs every point):
- [ ] The short chunk scores higher.
- [ ] b controls the gap; at b = 0 the two scores are equal.

**For a 4, also:**
- [ ] Gives the mechanism (dl/avgdl inside K) and notes that the adjustment also **raises** chunks shorter than average, not only lowers long ones.

**Common wrong answers:**
- [ ] "The long one, because it has more words that could match": BPA appears once in both; the extra words only make K larger.
- [ ] "They tie, because the count is the same": only at b = 0.

**If you missed it, reread:** [short §5](../reading/P3_bm25.md#5-repeats-flatten-out-k1-and-length-cuts-both-ways-b) · [full D.4](../../concepts/P3_bm25.md#d4-saturation-k1-and-length-normalisation-b) · book Ch12 p.5/14 and App p.18/23

</details>
<!-- /q -->

<!-- q id=P3-PRE-05 type=R set=pre -->
### P3-PRE-05 · Recall (before reading)
**Question:** The repo builds its BM25 index with `doc.page_content.split()`: name one thing that can go wrong.

**Reply template:** `With split(), the token ____ will not match ____.`

<details><summary>Hint 1</summary>

`split()` cuts only at spaces. What stays attached to a word?

</details>

<details><summary>Hint 2</summary>

The climate PDF writes "Intergovernmental Panel on Climate Change (IPCC)". Which token does `split()` make from the last word, and does the query `IPCC` equal it?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** `split()` cuts only at whitespace, so case and punctuation stay attached: `(IPCC)`, `emissions.` and `Emissions` are all different tokens from `ipcc` and `emissions`. The repo applies the same `split()` to the query (cell 17), so the user's own case and punctuation matter too. Measured on the 91 windows:

```
"emissions" under split():            emissions 22, emissions. 20, emissions, 7, Emissions 1
query "IPCC":                          0 windows score above 0        (the text holds "(IPCC)")
query "What does BECCS stand for?":    0 of 91 windows score above 0  (the text holds "(BECCS),"; the query holds "for?")
```

**Key points** (a 3 needs every point):
- [ ] `split()` keeps case and punctuation attached to words.
- [ ] So an exact term in the text (`(IPCC)`) never equals the query token (`IPCC`), and the chunk scores 0.

**For a 4, also:**
- [ ] Adds that the query goes through the same `split()` (cell 17), and that the repo's code still returns k chunks when every score is 0.

**Common wrong answers:**
- [ ] "`rank_bm25` cleans the tokens itself": it counts exactly the strings it is given.
- [ ] "The embedding model's tokenizer takes care of the punctuation": BM25 never sees the embedding model's tokens; it uses whatever your own tokenizer outputs (MC-001 is the same mix-up of tokenizer and model).

**If you missed it, reread:** [short §6](../reading/P3_bm25.md#6-tokenization-decides-what-can-match) · [full B.2](../../concepts/P3_bm25.md#b2-the-repos-bm25-cannot-find-ipcc) · [full D.5](../../concepts/P3_bm25.md#d5-tokenization-decides-what-can-match) · book Ch12 p.6/14 and p.10/14

</details>
<!-- /q -->

<!-- q id=P3-R-01 type=R set=main -->
### P3-R-01 · Recall
**Question:** What does IDF measure?

**Reply template:** `IDF is high when ____, because ____.`

<details><summary>Hint 1</summary>

It is the "rarity" factor among the book's three factors (Ch12 p.5/14).

</details>

<details><summary>Hint 2</summary>

It uses N (chunks in the collection) and n (chunks that contain the word). Which way does it move as n grows?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** How **rare** a word is across the collection. It is high when the word occurs in few chunks, because a match on a rare word is strong evidence about a chunk. `rank_bm25` computes ln((N − n + 0.5) / (n + 0.5)) from the document frequency n, never from the count inside one chunk.

```
running example, 91 windows:   beccs (in 2)   3.577948          ipcc (in 1)  4.099885
                               for (in 80)    raw −1.945910  →  replaced by the floor 0.838237
```

**Key points** (a 3 needs every point):
- [ ] High when the word occurs in few chunks (documents).
- [ ] Uses the document frequency n (chunks containing the word), not the count inside one chunk.
- [ ] `rank_bm25`: ln((N − n + 0.5) / (n + 0.5)).

**For a 4, also:**
- [ ] Gives the boundary: above n = N/2 the idf is negative and the library uses the floor (0.25 × the mean idf, 0.838 on our windows), so a very common word can outweigh a mid-frequency one (`climate` 0.838 against `emissions` 0.511).

**Common wrong answers:**
- [ ] "IDF counts the word inside the chunk": that is tf.
- [ ] "Common words get an idf of 0": a word in exactly half of the chunks gets 0; a word in more than half gets the floor, which is positive on our windows.

**If you missed it, reread:** [short §2](../reading/P3_bm25.md#2-three-counts-before-any-formula) · [short §4](../reading/P3_bm25.md#4-bm25-exactly-as-rank_bm25-022-computes-it) · [full D.3](../../concepts/P3_bm25.md#d3-bm25-exactly-as-rank_bm25-022-computes-it) · book Ch12 p.5/14 and App p.17/23

</details>
<!-- /q -->

<!-- q id=P3-R-02 type=R set=main -->
### P3-R-02 · Recall (02 card evidence)
**Question:** What happens to a term's BM25 score as its count in a chunk keeps growing?

**Reply template:** `It approaches ____, because ____.`

<details><summary>Hint 1</summary>

Look at the tf part, f × (k1 + 1) / (f + K), when f is huge.

</details>

<details><summary>Hint 2</summary>

For a very large f, the K in the denominator stops mattering. What is left of the fraction?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** It rises but **saturates** toward idf × (k1 + 1), which is 2.5 × idf at the default k1 = 1.5. Each extra mention adds less than the one before. k1 sets how fast the curve flattens.

```
f          1       10      100     1000         (dl = avgdl; rank_bm25 itself: score / idf = 2.173913 at f = 10)
tf part    1.000   2.174   2.463   2.496
toy "bpa" at f = 16:   TF-IDF 17.578      BM25 1.344
```

**Key points** (a 3 needs every point):
- [ ] The score rises but saturates.
- [ ] The ceiling is idf × (k1 + 1), 2.5 × idf at the default.
- [ ] k1 controls how fast it saturates.

**For a 4, also:**
- [ ] Self-checks with a number (f = 10 gives 2.174 at dl = avgdl) and contrasts TF-IDF, which grows linearly.

**Common wrong answers:**
- [ ] "It keeps growing in proportion to the count": that is TF-IDF with raw counts.
- [ ] "It grows until the chunk is full of the word": the limit is set by k1, not by the chunk.

**If you missed it, reread:** [short §5](../reading/P3_bm25.md#5-repeats-flatten-out-k1-and-length-cuts-both-ways-b) · [full D.4](../../concepts/P3_bm25.md#d4-saturation-k1-and-length-normalisation-b) · book Ch12 p.5/14 (more mentions score higher; the book never says it flattens)

</details>
<!-- /q -->

<!-- q id=P3-R-03 type=R set=main -->
### P3-R-03 · Recall (02 card evidence)
**Question:** What happens to the score when b goes to 0?

**Reply template:** `With b = 0, the score ____, so ____.`

<details><summary>Hint 1</summary>

b multiplies the length ratio dl/avgdl inside K.

</details>

<details><summary>Hint 2</summary>

Put b = 0 into K = k1 × (1 − b + b × dl / avgdl). Does dl still appear?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Document length is **ignored**. K becomes k1 for every chunk, so one mention scores the same in a short and a long chunk. At the other end, b = 1 normalises fully by dl/avgdl; the default 0.75 is in between.

```
small made-up corpus:   b = 0.75:  5-token chunk 0.829243,  20-token chunk 0.495899      b = 0:  0.587787 and 0.587787
```

**Key points** (a 3 needs every point):
- [ ] Length is ignored: K = k1 for every chunk.
- [ ] So the same mention scores the same in a short and a long chunk (0.588 each).

**For a 4, also:**
- [ ] Gives the mechanism (b weights dl/avgdl inside K) and the other boundary: b = 1 is full normalisation, and at the default a chunk shorter than average is raised, not only a long one lowered.

**Common wrong answers:**
- [ ] "b = 0 switches the score off": b only touches the length part; the idf and the repeat count still work.
- [ ] "b = 0 favours short chunks": it makes length irrelevant.

**If you missed it, reread:** [short §5](../reading/P3_bm25.md#5-repeats-flatten-out-k1-and-length-cuts-both-ways-b) · [full D.4](../../concepts/P3_bm25.md#d4-saturation-k1-and-length-normalisation-b) · book Ch12 p.5/14 and App p.18/23

</details>
<!-- /q -->

<!-- q id=P3-R-04 type=R set=main -->
### P3-R-04 · Recall
**Question:** Why does the repo's BM25 not find "IPCC" in the climate PDF?

**Reply template:** `Because the index holds ____ and the query holds ____.`

<details><summary>Hint 1</summary>

Write down the token that `split()` makes from "Change (IPCC)".

</details>

<details><summary>Hint 2</summary>

BM25 adds a word's score only when the query token and the chunk token are identical strings. Are `IPCC` and `(IPCC)` identical?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** `split()` keeps punctuation. The index holds `(IPCC)`, the query holds `IPCC`, so no window shares a token with the query and every score is 0. The repo's helper still returns k chunks, chosen by position, so nothing warns you.

```
split():     0 of 91 windows score above 0;  argsort returns windows [90, 89, 88, 87, 86]
tok_norm:    ipcc in 1 window (idf 4.099885)  →  rank 1, score 3.8928
```

**Key points** (a 3 needs every point):
- [ ] `split()` keeps the brackets: the index token is `(IPCC)`, the query token `IPCC`.
- [ ] Different strings never match, so every score is 0.
- [ ] The code still returns k chunks, so the miss is silent.

**For a 4, also:**
- [ ] Gives the fix (one normalising tokenizer for chunks and query; keep only scores above 0) and a test with the corpus's own acronyms.

**Common wrong answers:**
- [ ] "IPCC is too rare for BM25 to rank": rare words get the highest weight; with matching tokens it is rank 1.
- [ ] "Lower-case the query and it works": the index still holds `(IPCC)`. Lower-casing only the query even made the toy worse (d0 dropped from 2.125 to 1.289).

**If you missed it, reread:** [short §6](../reading/P3_bm25.md#6-tokenization-decides-what-can-match) · [full B.2](../../concepts/P3_bm25.md#b2-the-repos-bm25-cannot-find-ipcc) · [full J](../../concepts/P3_bm25.md#part-j--failure-and-debugging) · book Ch12 p.6/14

</details>
<!-- /q -->

<!-- q id=P3-A-01 type=A set=main -->
### P3-A-01 · Application
**Question:** In the toy corpus, compute the BM25 score of `eu` in d0 (N = 6, n = 1, f = 1, dl = 11, avgdl = 10).

**Reply template:** `idf = ____, tf part = ____, score = ____.`

<details><summary>Hint 1</summary>

Three steps: the idf from N and n; K from dl and avgdl; the tf part from f and K. Use k1 = 1.5 and b = 0.75.

</details>

<details><summary>Hint 2</summary>

idf = ln((6 − 1 + 0.5) / (1 + 0.5)); K = 1.5 × (0.25 + 0.75 × 11 / 10); tf part = 1 × 2.5 / (1 + K).

</details>

<details><summary>Hint 3</summary>

idf = ln(5.5 / 1.5) = 1.299283; K = 1.6125; tf part = 2.5 / 2.6125. Now multiply.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
idf     = ln(5.5 / 1.5)              = 1.299283
K       = 1.5 × (0.25 + 0.75 × 1.1)  = 1.6125
tf part = 2.5 / (1 + 1.6125)         = 0.956938
score   = 1.299283 × 0.956938        = 1.243333        (rank_bm25 gives the same)
```

**Key points** (a 3 needs every point):
- [ ] idf = ln(5.5 / 1.5) ≈ 1.2993.
- [ ] K = 1.6125 and tf part ≈ 0.9569.
- [ ] score ≈ 1.2433.

**For a 4, also:**
- [ ] Self-checks: `eu` is rarer than `bpa` (in 1 document against 2), so its idf must be larger (1.299 > 0.588); and with f = 1 in a chunk slightly longer than average, the tf part must be slightly below 1.

**Common wrong answers:**
- [ ] "idf = ln(6 / 1) = 1.792": that is the textbook TF-IDF idf, not the one `rank_bm25` uses.
- [ ] "tf part = 1, because f = 1": only when dl = avgdl; d0 has 11 tokens against an average of 10.

**If you missed it, reread:** [short §4](../reading/P3_bm25.md#4-bm25-exactly-as-rank_bm25-022-computes-it) · [full F](../../concepts/P3_bm25.md#part-f--worked-example-by-hand) · [full D.3](../../concepts/P3_bm25.md#d3-bm25-exactly-as-rank_bm25-022-computes-it) · book Ch12 p.5/14 (the three factors in words; the formula is not in the book)

</details>
<!-- /q -->

<!-- q id=P3-A-02 type=A set=main -->
### P3-A-02 · Application (what if k1 doubles?)
**Question:** A term occurs twice in a chunk of average length, and k1 doubles from 1.5 to 3.0: does its tf part go up or down?

**Reply template:** `It goes ____, from ____ to ____, because ____.`

<details><summary>Hint 1</summary>

At average length, K = k1. Write the tf part for f = 2 at both values of k1.

</details>

<details><summary>Hint 2</summary>

Compute 2 × (k1 + 1) / (2 + k1), once with 1.5 and once with 3.0.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** **Up**, from 1.429 to 1.600. A larger k1 delays saturation, so the second mention counts for more.

```
k1 = 1.5:   2 × 2.5 / (2 + 1.5) = 1.4286
k1 = 3.0:   2 × 4.0 / (2 + 3.0) = 1.6000
```

**Key points** (a 3 needs every point):
- [ ] Up.
- [ ] From 1.4286 to 1.6.
- [ ] Mechanism: a larger k1 lets repeats count for longer before the curve flattens.

**For a 4, also:**
- [ ] Self-checks: at f = 1 and dl = avgdl the tf part is exactly 1 for any k1, so the change can only show from the second mention on.

**Common wrong answers:**
- [ ] "Down, because k1 grows in the denominator": the numerator grows too (k1 + 1); for f > 1 the net effect is up.
- [ ] "No change, because k1 only matters for long chunks": that is b.

**If you missed it, reread:** [short §5](../reading/P3_bm25.md#5-repeats-flatten-out-k1-and-length-cuts-both-ways-b) · [full D.4](../../concepts/P3_bm25.md#d4-saturation-k1-and-length-normalisation-b) · book Ch12 p.5/14

</details>
<!-- /q -->

<!-- q id=P3-A-03 type=A set=main -->
### P3-A-03 · Application (what if b halves?)
**Question:** A term occurs once in a chunk twice the average length, and b halves from 0.75 to 0.375: does its tf part go up or down?

**Reply template:** `It goes ____, from ____ to ____, because ____.`

<details><summary>Hint 1</summary>

Here dl / avgdl = 2. Compute K at both values of b.

</details>

<details><summary>Hint 2</summary>

K = 1.5 × (1 − b + 2b). Then the tf part = 1 × 2.5 / (1 + K).

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** **Up**, from 0.690 to 0.816. A smaller b means a smaller length penalty for this long chunk.

```
b = 0.75:    K = 1.5 × 1.75  = 2.625      tf part = 2.5 / 3.625  = 0.6897
b = 0.375:   K = 1.5 × 1.375 = 2.0625     tf part = 2.5 / 3.0625 = 0.8163
```

**Key points** (a 3 needs every point):
- [ ] Up.
- [ ] From 0.6897 to 0.8163.
- [ ] Mechanism: a smaller b shrinks the length penalty (K gets smaller).

**For a 4, also:**
- [ ] Self-checks: at b = 0 it would be exactly 1.000, so it must move toward 1; and for a chunk half the average length, halving b moves it **down** (1.290 to 1.127).

**Common wrong answers:**
- [ ] "Down, because there is less normalisation": less normalisation helps a long chunk.
- [ ] "No change, because f = 1": f = 1 removes the saturation effect of k1, not the length effect.

**If you missed it, reread:** [short §5](../reading/P3_bm25.md#5-repeats-flatten-out-k1-and-length-cuts-both-ways-b) · [full D.4](../../concepts/P3_bm25.md#d4-saturation-k1-and-length-normalisation-b) · book Ch12 p.5/14 and App p.18/23

</details>
<!-- /q -->

<!-- q id=P3-A-04 type=A set=main -->
### P3-A-04 · Application (debugging)
**Question:** This returns five chunks for `ipcc`, but none of them mentions IPCC: what is wrong?

```python
bm25 = BM25Okapi([c.split() for c in chunks])
top = np.argsort(bm25.get_scores("ipcc".split()))[::-1][:5]
```

**Reply template:** `The bug is ____. The fix is ____.`

<details><summary>Hint 1</summary>

Print the chunk tokens that contain "IPCC". Then print the scores.

</details>

<details><summary>Hint 2</summary>

Two problems stack up: the tokens never match, and `argsort` does not care whether a score is 0.

</details>

<details><summary>Hint 3</summary>

The chunk token is `(IPCC)`, so every score is 0.0. `argsort` of an all-zero array, reversed, gives the last five positions.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The chunks keep their case and punctuation (`(IPCC)`), and the query is lower-case `ipcc`, so no token matches and every score is 0. `argsort` still returns five indices, chosen only by position: on our 91 windows, [90, 89, 88, 87, 86], the last five of the document. Fix: run the **same** normalising tokenizer on chunks and query, and keep only scores above 0.

```python
tok = lambda t: re.findall(r"[a-z0-9]+(?:[.,][0-9]+)*", t.lower())
bm25 = BM25Okapi([tok(c) for c in chunks])
scores = bm25.get_scores(tok("ipcc"))
top = [i for i in np.argsort(-scores, kind="stable")[:5] if scores[i] > 0]   # 91 windows: [1], score 3.8928
assert top, "BM25: no query token matched"
```

**Key points** (a 3 needs every point):
- [ ] The chunk tokens keep case and punctuation (`(IPCC)`), so the query token `ipcc` never matches and every score is 0.
- [ ] `argsort` still returns five indices, chosen only by position.
- [ ] Fix: the same normalising tokenizer for chunks and query, and drop the scores of 0.

**For a 4, also:**
- [ ] Adds a check that would have caught it: `assert (scores > 0).any()`, or a tokenizer test on the corpus's own acronyms before indexing.

**Common wrong answers:**
- [ ] "Search for upper-case IPCC instead": the chunk token is `(IPCC)`, with brackets; it still does not match.
- [ ] "BM25 cannot handle acronyms": with matching tokens the acronym is the strongest word there is (idf 4.0999, rank 1).

**If you missed it, reread:** [short §6](../reading/P3_bm25.md#6-tokenization-decides-what-can-match) · [full J](../../concepts/P3_bm25.md#part-j--failure-and-debugging) · [full D.5](../../concepts/P3_bm25.md#d5-tokenization-decides-what-can-match) · book Ch12 p.10/14

</details>
<!-- /q -->

<!-- q id=P3-T-01 type=T set=main -->
### P3-T-01 · Transfer
**Question:** A team indexes software release notes, and users search for version strings like `v2.10.3` and error codes like `ERR_CONN_RESET`: which tokenizer would you start with?

**Reply template:** `I would tokenize ____, because ____. I would check it by ____.`

<details><summary>Hint 1</summary>

Run both identifier shapes through each tokenizer in this lesson in your head. Which one survives whole?

</details>

<details><summary>Hint 2</summary>

`\w+` keeps underscores but cuts at dots; `tok_norm` keeps dots between digits but cuts at underscores. What rule keeps both, and how would you prove it works?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Start with a custom rule that keeps both shapes whole, because **neither tokenizer in this lesson does** (measured on one sentence):

```
"Upgrade to v2.10.3 if you see ERR_CONN_RESET."
lower + \w+  :   ... v2  10  3 ... err_conn_reset          ← cuts the version
tok_norm     :   ... v2.10.3   ... err  conn  reset        ← cuts the error code
scikit-learn :   ... v2  10    ... err_conn_reset          ← also drops the "3"
```

So keep dots between digits **and** underscores inside words. It matters because `10` and `3` on their own match every chunk that has those numbers. Lower-casing is probably safe for error codes, but check for collisions. Use the same tokenizer for index and query, with a unit test on real identifiers from the notes. Then measure Recall@k on a slice of exact-identifier questions against a `split()` baseline. Do not rely on BM25 alone for paraphrased questions such as "why does my connection drop?".

**Key points** (a 3 needs every point):
- [ ] Neither `\w+` nor `tok_norm` keeps both identifiers whole: one cuts `v2.10.3`, the other `ERR_CONN_RESET`.
- [ ] A rule that keeps digit-dot-digit and underscores, the same for index and query.
- [ ] A unit test on real identifiers from the notes before indexing.

**For a 4, also:**
- [ ] Says how to measure it (Recall@k on an exact-identifier slice, against `split()`) and when not to rely on BM25 alone (paraphrased questions).

**Common wrong answers:**
- [ ] "Use tok_norm, it fixed IPCC": it cuts `ERR_CONN_RESET` into `err`, `conn` and `reset`.
- [ ] "split() is best here, because it keeps identifiers whole": it also keeps `ERR_CONN_RESET.` with its full stop, and keeps every capitalised word apart from its lower-case form.

**If you missed it, reread:** [short §6](../reading/P3_bm25.md#6-tokenization-decides-what-can-match) · [full D.5](../../concepts/P3_bm25.md#d5-tokenization-decides-what-can-match) · [full K](../../concepts/P3_bm25.md#part-k--engineering-decisions) · book Ch12 p.10/14 (product codes and citations as exact terms)

</details>
<!-- /q -->

<!-- q id=P3-T-02 type=T set=main -->
### P3-T-02 · Transfer (code identifiers)
**Question:** Developers search an API index with words like "user id", but the functions are named `getUserId` and `get_user_id`: what does `tok_norm` do with them, and what would you change?

**Reply template:** `tok_norm turns getUserId into ____ and get_user_id into ____, so ____. I would ____. I would check by ____.`

<details><summary>Hint 1</summary>

Run both names through `tok_norm` in your head. Which characters does it treat as separators?

</details>

<details><summary>Hint 2</summary>

`tok_norm` keeps runs of letters and digits, so an underscore separates words but a capital letter does not. What must a code tokenizer do so that "user id" reaches both functions, while an exact search for `getUserId` still puts that one function first?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** `tok_norm` treats the two names differently. The underscore is a separator, so `get_user_id` becomes `get`, `user`, `id`. A camelCase name has no separator, so `getUserId` becomes one token, `getuserid`, and a developer who types "user id" never reaches it. Split identifiers into their parts, at underscores and where a lower-case letter meets a capital, and also keep the whole name as one extra token. Use the same rule for the index and the query. Measured on a toy API index of ten function signatures:

```
                      query "user id": does getUserId score?            query "getUserId": the top results
tok_norm              no (only delete_user 2.6276, get_user_id 2.1134)   getUserId 2.0176, the only match
parts only            yes, rank 2 (tied with get_user_id at 1.0983)      getUserId and get_user_id tie at 1.8392
parts + whole name    yes, rank 2 (1.1126)                               getUserId 3.6807, then get_user_id 1.8631
```

Splitting alone loses the exact match; the whole-name token brings it back. One thing no tokenizer fixes: `delete_user(user_id)` wins "user id" every time, because it says "user" twice. BM25 cannot see that the developer wants to *get* an id, not delete a user. Check the change with labelled queries in two groups, natural words and exact names, and compare Recall@k and MRR per group for each tokenizer. If developers mostly paste exact names, keep identifiers whole, as in P3-T-01. For questions about intent ("how do I find the current user's number?"), BM25 alone is not enough.

**Key points** (a 3 needs every point):
- [ ] `tok_norm` splits `get_user_id` at the underscores but keeps `getUserId` as one token (`getuserid`), so "user id" never matches it.
- [ ] Split identifiers into parts at underscores and case changes, and also keep the whole name, with the same rule for index and query.
- [ ] Parts alone make an exact search for `getUserId` tie with `get_user_id`; the whole-name token restores the exact match.

**For a 4, also:**
- [ ] Says how to measure (labelled natural-word and exact-name queries, Recall@k and MRR per group, against `tok_norm`) and names a limit: `delete_user` still wins "user id", because intent is not in the tokens; and if users paste exact names, splitting only adds noise.

**Common wrong answers:**
- [ ] "tok_norm lower-cases, so getUserId matches user id": lower-casing does not split anything; `getuserid` is still one token.
- [ ] "Split everything into parts and drop the whole names": then an exact search for `getUserId` ties with `get_user_id`.
- [ ] "Stemming would fix it": stemming trims word endings; it does not cut `getuserid` apart.

**If you missed it, reread:** [short §6](../reading/P3_bm25.md#6-tokenization-decides-what-can-match) · [full D.5](../../concepts/P3_bm25.md#d5-tokenization-decides-what-can-match) · [full K](../../concepts/P3_bm25.md#part-k--engineering-decisions) · book App p.9/23 (keyword search for exact method names) and Ch12 p.10/14

</details>
<!-- /q -->

<!-- q id=P3-T-03 type=T set=main -->
### P3-T-03 · Transfer (when not to use BM25 alone)
**Question:** A colleague wants BM25 alone for a help desk whose users write "my screen goes dark" while the manual says "the display turns off": would you agree?

**Reply template:** `I would ____, because ____. I would check by ____. I would change my mind if ____.`

<details><summary>Hint 1</summary>

Which words do the user's sentence and the manual's sentence share?

</details>

<details><summary>Hint 2</summary>

BM25 can only add scores for shared tokens. Think about what it then ranks first, whether its raw score warns you, and how you would compare it with dense retrieval on real questions.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Not alone. The two sentences share no word, so the manual's sentence earns nothing for this question, and BM25 ranks whichever chunks happen to contain "screen" or "dark". Stemming does not help: it joins word forms, not synonyms. And a raw BM25 score will not warn you. A question with no rare word still gets confident-looking scores:

```
91 windows:   "What can be done about this?"   81 windows score above 0; top score 5.76
              "What does BECCS stand for?"     the true match scores 5.06
97 chunks:    draft seed D-006 (a paraphrase)  BM25 ranks a chunk sharing "panels" 1st, the evidence 2nd; dense ranks the evidence 1st
```

Keep BM25 for product codes and model numbers, and add dense retrieval (hybrid, R1). Decide by measurement: label real help-desk questions by category (paraphrase or exact term) and compare BM25 alone, dense and hybrid on CE@k and MRR per category. I would change my mind if nearly all queries turned out to be codes and part numbers; the book says BM25 alone suffices then (Ch12 p.12/14).

**Key points** (a 3 needs every point):
- [ ] BM25 matches tokens only: the paraphrase shares no word with the manual, so the right chunk gets nothing.
- [ ] It then ranks chunks that share stray words, and its raw score does not show that the match is poor.
- [ ] Use BM25 for codes and identifiers, combined with dense retrieval, not alone.

**For a 4, also:**
- [ ] Measures it: labelled help-desk questions in paraphrase and exact-term categories; BM25 alone vs dense vs hybrid on CE@k and MRR per category, with retrieval kept separate from answer quality. Says when BM25 alone would be fine (nearly every query is a keyword lookup).

**Common wrong answers:**
- [ ] "BM25 alone is fine: it beat dense on our seeds (MRR@10 0.938 against 0.708)": those are 8 LLM-drafted questions, not paraphrasing users, and on D-006, the paraphrase seed, BM25 lost.
- [ ] "Add stemming and it will match": stemming joins `emission` and `emissions`, not `screen` and `display`.

**If you missed it, reread:** [short §7](../reading/P3_bm25.md#7-when-not-to-use-bm25-alone) · [full D.7](../../concepts/P3_bm25.md#d7-a-raw-bm25-score-says-nothing-about-whether-an-answer-exists) · [full K](../../concepts/P3_bm25.md#part-k--engineering-decisions) · book Ch12 p.2/14 and p.12/14

</details>
<!-- /q -->

<!-- q id=P3-A-05 type=A set=review -->
### P3-A-05 · Application (review)
**Question:** In the toy corpus, compute the BM25 score of `emissions` in d5 (N = 6, n = 2, f = 1, dl = 5, avgdl = 10).

**Reply template:** `idf ____ × tf part ____ = ____`

<details><summary>Hint 1</summary>

The same three steps as P3-A-01. d5 is half the average length.

</details>

<details><summary>Hint 2</summary>

idf = ln(4.5 / 2.5); K = 1.5 × (0.25 + 0.75 × 0.5).

</details>

<details><summary>Hint 3</summary>

K = 0.9375, so the tf part = 2.5 / 1.9375.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
idf     = ln(4.5 / 2.5)               = 0.587787
K       = 1.5 × (0.25 + 0.75 × 0.5)   = 0.9375
tf part = 2.5 / (1 + 0.9375)          = 1.290323
score   = 0.587787 × 1.290323         = 0.758434        (in d4, which has the average length: 0.587787)
```

**Key points** (a 3 needs every point):
- [ ] idf ≈ 0.5878.
- [ ] K = 0.9375 and tf part ≈ 1.2903.
- [ ] score ≈ 0.7584.

**For a 4, also:**
- [ ] Self-checks: d5 is shorter than average, so the tf part must be above 1 and the score above the idf; in d4 (average length) the score equals the idf exactly.

**Common wrong answers:**
- [ ] "The same as in d4, because f = 1 in both": length still enters through b.
- [ ] "The short chunk is penalised": at the default b, a chunk shorter than average is raised.

**If you missed it, reread:** [short §5](../reading/P3_bm25.md#5-repeats-flatten-out-k1-and-length-cuts-both-ways-b) · [full F](../../concepts/P3_bm25.md#part-f--worked-example-by-hand) · [full D.4](../../concepts/P3_bm25.md#d4-saturation-k1-and-length-normalisation-b) · book Ch12 p.5/14 and App p.18/23

</details>
<!-- /q -->

<!-- q id=P3-R-05 type=R set=interview source=AIQ-04-Q12 -->
### P3-R-05 · Interview (Recall)
**Question:** "What does BM25 actually compute? Walk me through the formula's moving parts."
*From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md` (question 12), Copyright (c) 2026 Om, MIT License.*

**Reply template:** `BM25 adds up, over the query's words, ____ × ____. The moving parts: ____. Its limits: ____.`

<details><summary>Hint 1</summary>

Name the three factors first, then say where k1 and b enter.

</details>

<details><summary>Hint 2</summary>

The idf from the document frequency; the tf part f × (k1 + 1) / (f + K); K = k1 × (1 − b + b × dl / avgdl). Then two limits: what BM25 can never match, and what decides its tokens.

</details>

<details><summary>Show answer (write yours first)</summary>

> **The repo's answer (excerpt, verbatim).** *From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md`, Copyright (c) 2026 Om, MIT License:*
>
> "**Term frequency with saturation** is the key improvement over naive TF-IDF. Raw TF is linear: 20 occurrences look 20 times better than one. BM25 pushes TF through `tf / (tf + k1 * (...))`, which saturates, so the jump from 1 to 2 occurrences matters a lot and 20 to 21 barely registers. `k1` (typically ~1.2 to 2.0) controls how fast it saturates. This is exactly right for relevance: a document mentioning your term once is very different from never, a document mentioning it 50 times is probably not 50 times better."
>
> "**Length normalization** divides by document length relative to the corpus average, controlled by `b` (typically ~0.75). Without it, long documents win everything by accident. `b=0` disables it, `b=1` normalizes fully."

**Our check of that answer:** the three factors, the saturation idea, "b = 0 disables it, b = 1 normalises fully", and the two limits it names later (BM25 is purely lexical, and it depends on the analyzer) are right. The 1-to-2 versus 20-to-21 claim holds: at the defaults the tf part rises by 0.428571 and then by only 0.007752. Three corrections:
1. The written form `tf / (tf + k1 * (...))` drops the (k1 + 1) in the numerator. The ranking stays the same, because every word is scaled by the same 2.5, but one word's ceiling is idf × (k1 + 1), not idf × 1.
2. Length normalisation does not divide the score by the document length. It enlarges K = k1 × (1 − b + b × dl / avgdl), so a long document saturates sooner. And it **raises** documents shorter than average: one mention gives 1.290 at half the average length, against 0.690 at double.
3. It never says which idf. In `rank_bm25` the idf of a word in more than half of the documents is negative and is replaced by a floor, so "common words count less" is not strictly true: on our windows `climate` (0.838) outweighs `emissions` (0.511).

"k1 typically ~1.2 to 2.0" and "b typically ~0.75" are common settings, not checked against a primary source here (UNVERIFIED). `rank_bm25`'s defaults, 1.5 and 0.75, fit them.

**Model answer:** BM25 scores a chunk by adding up, over the query's words, idf × tf part. The idf rewards words found in few chunks: in `rank_bm25` it is ln((N − n + 0.5) / (n + 0.5)), with a floor for very common words. The tf part, f × (k1 + 1) / (f + K), grows with the number of mentions but saturates at k1 + 1; k1 sets how fast. K = k1 × (1 − b + b × dl / avgdl) brings in the length: b = 0 ignores it, b = 1 normalises fully. The limits: it is purely lexical (no synonyms), and the tokenizer decides what can match (the repo's `split()` never matches `IPCC` against `(IPCC)`).

**Key points** (a 3 needs every point):
- [ ] A sum over the query's words of idf × a saturating tf part.
- [ ] The idf rewards rare words, from the document frequency.
- [ ] k1 sets the saturation (ceiling k1 + 1); b sets the length normalisation through dl/avgdl.

**For a 4, also:**
- [ ] Names both limits with evidence: no synonyms (a paraphrase misses), and dependence on the tokenizer (`split()` keeps `(IPCC)`, so 0 windows match).

**Common wrong answers:**
- [ ] "BM25 divides the score by the document length": length enters through K, and it lifts short documents as well.
- [ ] "Each extra mention adds the same amount": that is TF-IDF with raw counts.

**If you missed it, reread:** [short §4](../reading/P3_bm25.md#4-bm25-exactly-as-rank_bm25-022-computes-it) · [short §5](../reading/P3_bm25.md#5-repeats-flatten-out-k1-and-length-cuts-both-ways-b) · [full D.3](../../concepts/P3_bm25.md#d3-bm25-exactly-as-rank_bm25-022-computes-it) · [full D.4](../../concepts/P3_bm25.md#d4-saturation-k1-and-length-normalisation-b) · book Ch12 p.5/14 and p.14/14

</details>
<!-- /q -->
