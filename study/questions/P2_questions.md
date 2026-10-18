<!-- kit:questions concept=P2 version=1 -->
# P2 questions: needs, relevance labels, the inverted index, and sets vs rankings

**How to use:** write your answer and a confidence (1–3) first. Then open the answer and tick the key points you really wrote.

**Where the numbers come from:** `sources/verification/P2/p2_measure.py` and `p2_kit_measure.py` on the toy collection and the climate PDF ([P2_FACTS](../../sources/verification/P2/P2_FACTS.md) S1–S11; [kit run K1–K6](../../sources/verification/P2/out_p2_kit_measure.txt)). BEIR's Hole@10 and nDCG@10 values are **external** (Thakur et al., NeurIPS 2021, read 2026-10-17). "Toy" documents are made up: they show that an effect exists, not how often. No API was called to write this file.

<!-- q id=P2-PRE-01 type=R set=pre -->
### P2-PRE-01 · Recall (before reading)
**Question:** Is the chunk with the highest similarity score always the most relevant one?

**Reply template:** `____, because a similarity score measures ____, while relevance means ____.`

<details><summary>Hint 1</summary>

Think of a chunk that repeats the question word for word but answers nothing.

</details>

<details><summary>Hint 2</summary>

Who computes a similarity score, and who decides whether a chunk helps answer the question?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** No. A similarity score is computed by a function from the query text and the chunk text (shared words, or nearby vectors). Relevance is whether the chunk helps the need behind the question, and only a judge reading against that need can say. On the toy collection, both retrievers put an echo of the question first, and it answers nothing:

```
q1 "main cause of climate change"
word overlap   rank 1: d02 (all 5 words)        MiniLM   rank 1: d02 (cosine 0.8402)
d02 = "What is the main cause of climate change? Students often ask this question in class."   grade 0
```

**Key points** (a 3 needs every point):
- [ ] No: the top-scoring chunk can be irrelevant.
- [ ] Similarity is computed from the texts by a function; relevance is judged against the need.

**For a 4, also:**
- [ ] Gives an example (the echo d02, or the book's link footer or capital-of-France chunks) and says that only labels can tell the two apart.

**Common wrong answers:**
- [ ] "Yes, the model understands meaning, so the closest chunk is the most relevant": MiniLM put the echo d02 first (0.8402).
- [ ] "Retrieval compares every chunk with every other chunk in a similarity matrix": it computes one score per (query, chunk) pair and sorts (MC-002).

**If you missed it, reread:** [short §1](../reading/P2_ir_framing.md#1-the-need-behind-the-question) · [short §2](../reading/P2_ir_framing.md#2-two-retrievers-score-it-similarity-is-not-relevance) · [full D.2](../../concepts/P2_ir_framing.md#d2-similarity-is-computed-relevance-is-judged) · book Ch3 p.1/14 and Ch13 p.1–2/13

</details>
<!-- /q -->

<!-- q id=P2-PRE-02 type=R set=pre -->
### P2-PRE-02 · Recall (before reading)
**Question:** What does the index at the back of a book store?

**Reply template:** `For each ____, it stores ____. To find a word, you ____.`

<details><summary>Hint 1</summary>

Picture a textbook's index: what is on the left of each line, and what is on the right?

</details>

<details><summary>Hint 2</summary>

Is the index organised by page or by word? Why is that direction the useful one for finding things?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** For each word (term), the sorted list of pages that mention it. You look up the word and go straight to those pages. A book is organised by page; its index is organised by word, the other way round. Search engines keep the same structure for documents, the **inverted index**: term → sorted list of document ids (the postings list).

```
toy collection:   climate → d02, d08     of → d01, d02     rising → d04     rise → (none)
```

**Key points** (a 3 needs every point):
- [ ] Each word maps to the pages (documents) that contain it.
- [ ] It is organised by word, the reverse ("inverted") of the text, which is organised by page.

**For a 4, also:**
- [ ] Names the limit: it matches exact strings only, so `rise` does not find "rising".

**Common wrong answers:**
- [ ] "It stores what each page is about": it lists words, not topics or meaning.
- [ ] "It stores the LLM's tokens": a keyword index stores whole words from its own simple tokenizer, not a model's sub-word tokens (MC-001).

**If you missed it, reread:** [short §5](../reading/P2_ir_framing.md#5-the-inverted-index) · [full D.4](../../concepts/P2_ir_framing.md#d4-the-inverted-index) · book Ch12 p.3/14 (the back-of-cookbook index)

</details>
<!-- /q -->

<!-- q id=P2-R-01 type=R set=main -->
### P2-R-01 · Recall (MC-002 check item)
**Question:** What is the difference between similarity and relevance?

**Reply template:** `Similarity is ____ computed by ____. Relevance is ____ decided by ____.`

<details><summary>Hint 1</summary>

One of them is a number that a retriever produces for every chunk. The other needs a person.

</details>

<details><summary>Hint 2</summary>

Compare the inputs: query text and chunk text, or the need behind the query and what the chunk actually says?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** **Similarity** is a score computed by a function (word overlap, BM25, cosine) from the query text and the chunk text, one score per pair, at query time. **Relevance** is a judgment of whether the chunk helps the information need, made by a judge under a guideline and stored as labels. Systems rank by similarity as a cheap proxy for relevance; the labels measure how good the proxy was.

```
q1   d02 (echo of the question)      overlap rank 1 · MiniLM 0.8402 rank 1        grade 0
     d09 (methane, part of a cause)  MiniLM 0.2469, rank 9 of 10                   grade 1
```

**Key points** (a 3 needs every point):
- [ ] Similarity: a score that a function computes from the query text and the chunk text.
- [ ] Relevance: a judgment, against the need, by a judge under a guideline.
- [ ] Systems rank by similarity as a proxy; relevance labels measure that ranking.

**For a 4, also:**
- [ ] Gives a boundary with evidence: the echo d02 is the most similar in both retrievers yet grade 0, and the partly relevant d09 sits at MiniLM rank 9 (or the book's capital-of-France case).

**Common wrong answers:**
- [ ] "Relevance is just a high similarity score": then the echo d02 would be the best answer to q1.
- [ ] "The retriever compares all the chunks in a similarity matrix": it computes one score per (query, chunk) pair, then sorts (MC-002).

**If you missed it, reread:** [short §2](../reading/P2_ir_framing.md#2-two-retrievers-score-it-similarity-is-not-relevance) · [full D.2](../../concepts/P2_ir_framing.md#d2-similarity-is-computed-relevance-is-judged) · [full B.2](../../concepts/P2_ir_framing.md#b2-we-measured-it-on-a-toy-collection) · book Ch13 p.1–2/13

</details>
<!-- /q -->

<!-- q id=P2-R-02 type=R set=main -->
### P2-R-02 · Recall
**Question:** What does one line of a qrels file contain, and who writes it?

**Reply template:** `A line holds ____, ____ and ____. It is written by ____, under ____. A pair that is not listed ____.`

<details><summary>Hint 1</summary>

qrels means query relevance judgments. Three things identify one judgment.

</details>

<details><summary>Hint 2</summary>

Which query, which document, and what verdict? Then: what does an evaluation tool assume about the pairs nobody wrote down?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** A query id, a document id and a grade (here 2 / 1 / 0). A person (the judge) writes it, under a written and versioned guideline, with a one-line reason, before seeing any system's ranking. A pair that is not listed counts as 0, not relevant.

```
q1  d01  2   names the main cause: burning fossil fuels releases carbon dioxide
q1  d02  0   repeats the question; no answer
(q1, d04) is not listed   →   treated as grade 0
```

**Key points** (a 3 needs every point):
- [ ] Query id, document id, grade.
- [ ] Written by a judge under a guideline, not produced by the system.
- [ ] Unlisted pairs count as not relevant.

**For a 4, also:**
- [ ] Adds the consequence and the project unit: a relevant chunk that nobody judged is silently counted as a miss, and in the project the label is a span, with chunk labels derived from it.

**Common wrong answers:**
- [ ] "The retriever's score for that pair": a score is similarity, not a judgment.
- [ ] "The question and its reference answer": that can check an answer, not a retrieval.

**If you missed it, reread:** [short §3](../reading/P2_ir_framing.md#3-a-person-judges-it-qrels) · [short §10](../reading/P2_ir_framing.md#10-labels-are-incomplete-and-noisy) · [full D.3](../../concepts/P2_ir_framing.md#d3-writing-relevance-judgments) · book Ch22 p.12/19 (queries paired with expected relevant documents)

</details>
<!-- /q -->

<!-- q id=P2-R-03 type=R set=main -->
### P2-R-03 · Recall
**Question:** What is an inverted index?

**Reply template:** `It maps each ____ to ____. Its length is called ____. A query reads ____.`

<details><summary>Hint 1</summary>

Start from a table of words × documents with a 1 where the word occurs. What is almost every cell?

</details>

<details><summary>Hint 2</summary>

Keep only the 1s, row by row. What is one row now, and what is its length called?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** For each term, the sorted list of documents that contain it (its **postings list**). It is the term–document table stored row by row with the zeros dropped. A term's document frequency (df) is the length of its list. A query reads only the postings of its own terms, so documents that share no word are never touched.

```
toy: 88 terms · 114 postings · 71 terms in one document only
the → d01, d02, d03, d05, d06   (df 5)        methane → d09   (df 1)
```

**Key points** (a 3 needs every point):
- [ ] Term → sorted list of the documents that contain it (postings).
- [ ] df = the length of the postings list.
- [ ] A query reads only its own terms' postings.

**For a 4, also:**
- [ ] Names the limit: it matches strings, not meaning (`rise` misses "rising"; q3 `renewable energy` gets 0 postings), and its words come from its own tokenizer, not the LLM's (MC-001).

**Common wrong answers:**
- [ ] "Each document maps to its list of words": that is the forward direction, the document itself.
- [ ] "It is the vector index": a vector index finds the nearest vectors; an inverted index looks up words.

**If you missed it, reread:** [short §5](../reading/P2_ir_framing.md#5-the-inverted-index) · [full D.4](../../concepts/P2_ir_framing.md#d4-the-inverted-index) · book Ch12 p.3/14

</details>
<!-- /q -->

<!-- q id=P2-R-04 type=R set=main -->
### P2-R-04 · Recall
**Question:** Which question does set recall answer, and which does the first relevant rank answer?

**Reply template:** `Set recall: how ____? First relevant rank: how ____?`

<details><summary>Hint 1</summary>

One ignores order completely; the other is only about order.

</details>

<details><summary>Hint 2</summary>

Runs A (d02, d01, d08) and B (d01, d08, d02) for q1: which number is the same for both, and which differs?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Set recall: how much of the relevant material is in the retrieved set, |R ∩ Rel| / |Rel|, with order ignored. First relevant rank: how early the first relevant document appears (counting from 1).

```
q1, relevant = d01, d03, d09        set recall   first relevant rank
run A   d02, d01, d08               0.333        2
run B   d01, d08, d02               0.333        1
```

**Key points** (a 3 needs every point):
- [ ] Set recall = the part of all relevant documents that was retrieved; order is ignored.
- [ ] First relevant rank = the position of the first relevant document; only order matters.

**For a 4, also:**
- [ ] Gives the boundary with evidence: runs A and B share a recall but differ in first rank; and recall needs the number of all relevant documents, which is known only if all of them were labelled.

**Common wrong answers:**
- [ ] "High recall means the relevant chunks are near the top": recall ignores order.
- [ ] "Both measure how accurate the top k is": accuracy is useless when almost every document is irrelevant.

**If you missed it, reread:** [short §8](../reading/P2_ir_framing.md#8-cut-at-k-set-precision-and-set-recall) · [short §9](../reading/P2_ir_framing.md#9-set-quality-is-not-ranking-quality) · [full D.5](../../concepts/P2_ir_framing.md#d5-set-quality-vs-ranking-quality) · book Ch22 p.5–6/19

</details>
<!-- /q -->

<!-- q id=P2-R-05 type=R set=main -->
### P2-R-05 · Recall (incomplete labels)
**Question:** A relevant chunk was never judged: how does a retrieval metric count it?

**Reply template:** `It counts as ____. Precision ____. Recall ____. I would detect it with ____.`

<details><summary>Hint 1</summary>

What does a qrels file say about the pairs it does not list?

</details>

<details><summary>Hint 2</summary>

Follow it through both formulas: does the unjudged chunk change the top of the fraction, the bottom, or both?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** As **not relevant**: unjudged counts as 0 (the TREC convention). If a run retrieves it, that run's precision is too low: a real hit is counted as a miss. The number of relevant documents is also too small, so recall is measured against the known-relevant ones only and can look better than it is. The retriever that did not build the pool is hurt most.

```
toy, labels pooled from the word-overlap top 3, scored at k = 4 (K4):
MiniLM   mean P@4        full labels 0.350    pooled 0.200
mean recall, pooled:     1.000 for both retrievers   (full labels: overlap 0.567, MiniLM 0.933)
```

**Key points** (a 3 needs every point):
- [ ] It counts as not relevant.
- [ ] Precision drops for the run that retrieved it.
- [ ] Recall's denominator knows only the judged relevant documents, so recall can be overestimated.

**For a 4, also:**
- [ ] Says how to detect and fix it: report Judged@k (or Hole@k) per run and send the holes in the top k to a judge. External evidence: on BEIR's TREC-COVID, Hole@10 was 6.4% for BM25 and 30.6% for DPR, and judging ANCE's holes raised its nDCG@10 from 0.654 to 0.735.

**Common wrong answers:**
- [ ] "It is skipped, so it has no effect": the metric scores it as a miss.
- [ ] "Recall will catch it": recall's denominator does not know it exists.

**If you missed it, reread:** [short §10](../reading/P2_ir_framing.md#10-labels-are-incomplete-and-noisy) · [full D.3](../../concepts/P2_ir_framing.md#d3-writing-relevance-judgments) · book Ch22 p.5/19 (recall over all relevant documents in the knowledge base)

</details>
<!-- /q -->

<!-- q id=P2-R-06 type=R set=main -->
### P2-R-06 · Recall (the need)
**Question:** One query can hide two different needs: why is relevance judged against the need and not against the query's words?

**Reply template:** `Because the same words ____. Example: ____. So the judge ____.`

<details><summary>Hint 1</summary>

Take the toy query `carbon dioxide`. What could the person want to know?

</details>

<details><summary>Hint 2</summary>

d01 says burning fuel releases carbon dioxide; d06 says forests absorb it. Which one helps depends on what?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The same words can carry different needs, and a document can help one need but not the other. For `carbon dioxide`: if the need is "what puts it into the air?", d01 helps and d06 does not; if the need is "what takes it out?", it is the other way round. Both documents contain both words, so judging the words would mark both relevant. The judge therefore reads each query as a question someone asked, writes the need down, and grades against it.

**Key points** (a 3 needs every point):
- [ ] The same query text can stand for different needs.
- [ ] Whether a document helps depends on the need, so the words alone cannot decide relevance.
- [ ] Write the need down before labelling, and grade against it.

**For a 4, also:**
- [ ] Adds the mechanism and a limit: the word index returns both documents (`carbon` → d01, d06), so the system cannot tell the needs apart; an ambiguous eval question needs a need note, or two questions.

**Common wrong answers:**
- [ ] "A document is relevant if it contains the query words": d08 contains `climate` and `change` and is grade 0 for q1.
- [ ] "The query is the need": the query is the text typed; the need is what the person wants to know.

**If you missed it, reread:** [short §1](../reading/P2_ir_framing.md#1-the-need-behind-the-question) · [full D.1](../../concepts/P2_ir_framing.md#d1-the-objects-and-their-names) · book Ch1 p.8/14 (the book's question, with its chunks called relevant)

</details>
<!-- /q -->

<!-- q id=P2-A-01 type=A set=main -->
### P2-A-01 · Application (coding, from memory)
**Question:** From memory, write `build_index(docs)` for a dict of document id → text that returns each term with its sorted postings.

**Reply template:** `My function returns ____; I tested it on ____ and expected ____.`

<details><summary>Hint 1</summary>

Two steps: tokenize each document, then add the document's id to the list of each of its terms.

</details>

<details><summary>Hint 2</summary>

Lower-case, keep runs of a–z and 0–9. Use a set per term so that each id appears once, and sort at the end.

</details>

<details><summary>Hint 3</summary>

Loop `for term in set(tokenize(text))` and call `index[term].add(doc_id)` on a `defaultdict(set)`.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```python
import re
from collections import defaultdict

def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())

def build_index(docs):                        # {doc_id: text}
    index = defaultdict(set)
    for doc_id, text in docs.items():
        for term in set(tokenize(text)):
            index[term].add(doc_id)
    return {term: sorted(ids) for term, ids in index.items()}

idx = build_index({"a": "Sea level rise", "b": "Sea ice", "c": "Rising seas"})
assert idx["sea"] == ["a", "b"] and idx["rise"] == ["a"] and idx["rising"] == ["c"]
```

On the 10 toy documents it gives 88 terms and 114 postings, with climate → d02, d08 (S3).

**Key points** (a 3 needs every point):
- [ ] Tokenizes each document (lower-case, runs of letters and digits).
- [ ] Adds each document id once per distinct term.
- [ ] Returns a sorted postings list for every term.

**For a 4, also:**
- [ ] Self-checks on 2–3 tiny documents with a known answer, or against the toy's 88 terms and 114 postings, and compares the postings with a full scan.

**Common wrong answers:**
- [ ] "`text.split()` is enough": it keeps punctuation and capitals, so "change?" and "change" become different terms.
- [ ] "Append the id for every token": a repeated word adds duplicates (d08 has `climate` three times).

**If you missed it, reread:** [short §5](../reading/P2_ir_framing.md#5-the-inverted-index) · [full D.4](../../concepts/P2_ir_framing.md#d4-the-inverted-index) · book Ch12 p.3/14

</details>
<!-- /q -->

<!-- q id=P2-A-02 type=A set=main -->
### P2-A-02 · Application (labelling)
**Question:** Using guideline v1, grade q2 `why do sea levels rise` against the ten toy documents below.

```
guideline v1:  2 = alone answers the query · 1 = part of the answer · 0 = does not help (even if it shares words or the topic)
d01  Burning coal, oil and gas releases carbon dioxide, the main cause of recent global warming.
d02  What is the main cause of climate change? Students often ask this question in class.
d03  Greenhouse gases trap heat in the atmosphere like a blanket around the Earth.
d04  Sea levels are rising because warmer ocean water expands and glaciers melt.
d05  Melting ice sheets in Greenland and Antarctica add water to the oceans.
d06  Forests absorb carbon dioxide from the air as trees grow.
d07  Solar panels and wind turbines generate electricity without burning fuel.
d08  Climate change news, climate change videos, climate change quiz: subscribe now!
d09  Cattle and rice paddies release methane, a powerful greenhouse gas.
d10  Heat waves are becoming longer and more frequent in many regions.
```

**Reply template:** `Grade 2: ____. Grade 1: ____. A tempting 0: ____, because ____.`

<details><summary>Hint 1</summary>

Read q2 as a question someone asked: what would answer it?

</details>

<details><summary>Hint 2</summary>

Which document gives the reasons, which gives one reason, and which shares the topic (warming) but says nothing about the sea?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** (reference labels, S7)

```
d04     2   gives the reasons: warm water expands and glaciers melt
d05     1   one reason: melting ice sheets add water to the oceans
d10     0   tempting: about warming, but heat waves say nothing about sea level
others  0
```

**Key points** (a 3 needs every point):
- [ ] d04 = 2.
- [ ] d05 = 1.
- [ ] All the others 0, with a reason for at least one tempting zero.

**For a 4, also:**
- [ ] Defends a borderline call with the guideline (for example d05 as 2, or d03 as 1) and writes the sentence the guideline would need; the labels are written before looking at any ranking.

**Common wrong answers:**
- [ ] "d04 is 0, because it says 'rising', not 'rise'": judge the need, not the words.
- [ ] "d02 is relevant, because it is about climate change": being on the topic is not the same as helping answer.

**If you missed it, reread:** [short §3](../reading/P2_ir_framing.md#3-a-person-judges-it-qrels) · [full D.3](../../concepts/P2_ir_framing.md#d3-writing-relevance-judgments) · [full F](../../concepts/P2_ir_framing.md#part-f--worked-example-by-hand) · book Ch22 p.12/19

</details>
<!-- /q -->

<!-- q id=P2-A-03 type=A set=main -->
### P2-A-03 · Application (what if k doubles?)
**Question:** For MiniLM on q1, k grows from 3 to 6: does set precision go up, go down or stay the same?

```
MiniLM ranking for q1:   d02, d01, d04, d03, d10, d08, d05, d06, d09, d07
relevant (grade ≥ 1):    d01, d03, d09
```

**Reply template:** `Precision ____ (____ → ____), because ____. Recall ____.`

<details><summary>Hint 1</summary>

Count the relevant documents in the top 3, then in the top 6.

</details>

<details><summary>Hint 2</summary>

Precision = relevant retrieved ÷ retrieved. Which relevant documents are inside each cut?

</details>

<details><summary>Hint 3</summary>

The top 3 holds d01; the top 6 adds d03.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** It stays the same, at 0.333: one relevant and two non-relevant documents come in together. Recall doubles.

```
k = 3:  d02, d01, d04              1 relevant    precision 1/3 = 0.333    recall 1/3 = 0.333
k = 6:  + d03, d10, d08            2 relevant    precision 2/6 = 0.333    recall 2/3 = 0.667
```

**Key points** (a 3 needs every point):
- [ ] It stays at 0.333 (1/3 → 2/6).
- [ ] Because the relevant d03 enters at rank 4 together with two non-relevant documents.
- [ ] Recall rises from 0.333 to 0.667.

**For a 4, also:**
- [ ] Self-checks against the word-overlap retriever: nothing changes there, because it has only 3 candidates (recall flat at 0.333 from k = 2 on), and states the k trade-off (MC-005).

**Common wrong answers:**
- [ ] "It goes down, because more chunks means more noise": here the extra noise comes with one more relevant document (MC-005 is a trade-off, not a rule).
- [ ] "Recall reaches 1.0": d09 is at rank 9.

**If you missed it, reread:** [short §8](../reading/P2_ir_framing.md#8-cut-at-k-set-precision-and-set-recall) · [short §2](../reading/P2_ir_framing.md#2-two-retrievers-score-it-similarity-is-not-relevance) · [full D.5](../../concepts/P2_ir_framing.md#d5-set-quality-vs-ranking-quality) · book Ch22 p.4–5/19

</details>
<!-- /q -->

<!-- q id=P2-A-04 type=A set=main -->
### P2-A-04 · Application (Boolean search)
**Question:** For the three postings lists below, what are AND, OR and the number of postings read?

```
climate → d02, d08
of      → d01, d02
the     → d01, d02, d03, d05, d06
```

**Reply template:** `AND = ____. OR = ____. Postings read = ____.`

<details><summary>Hint 1</summary>

AND keeps the documents that are in every list; OR keeps those in any list.

</details>

<details><summary>Hint 2</summary>

The postings read are the sum of the three lists' lengths.

</details>

<details><summary>Hint 3</summary>

Intersect the two short lists first: climate ∩ of. Then check whether that result is in `the`.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
AND = d02                              climate ∩ of = d02, and d02 is in the
OR  = d01, d02, d03, d05, d06, d08     6 documents
postings read = 2 + 2 + 5 = 9
```

**Key points** (a 3 needs every point):
- [ ] AND = d02.
- [ ] OR = d01, d02, d03, d05, d06, d08.
- [ ] 9 postings read.

**For a 4, also:**
- [ ] Explains the cost and the order: merging two sorted lists costs O(x + y), and starting with the shortest lists (smallest df) keeps the intermediate result small (climate ∩ of = d02 before `the` is touched).

**Common wrong answers:**
- [ ] "AND = d01, d02, because they appear in two lists": AND needs every list.
- [ ] "Postings read = 10, the size of the collection": count the list entries, not the documents in the collection.

**If you missed it, reread:** [short §6](../reading/P2_ir_framing.md#6-boolean-and-and-or-and-the-postings-read) · [short §5](../reading/P2_ir_framing.md#5-the-inverted-index) · [full D.4](../../concepts/P2_ir_framing.md#d4-the-inverted-index) · book Ch12 p.3/14 (the book has the index analogy only; no Boolean search)

</details>
<!-- /q -->

<!-- q id=P2-A-05 type=A set=main -->
### P2-A-05 · Application (a one-retriever pool)
**Question:** The labels were made only from the word-overlap top 3, so for MiniLM's top 4 on q1 below, which documents are unjudged, and what happens to its P@4 and recall?

```
judged pool for q1 (word-overlap top 3):   d01 grade 2 · d02 grade 0 · d08 grade 0
full labels for q1:                         d01 2 · d03 1 · d09 1 · all others 0
MiniLM top 4 for q1:                        d02, d01, d04, d03
```

**Reply template:** `Unjudged: ____. P@4: full ____ vs pooled ____. Recall: full ____ vs pooled ____. Effect: ____.`

<details><summary>Hint 1</summary>

An unjudged document counts as not relevant. Which of the four are not in the pool?

</details>

<details><summary>Hint 2</summary>

Under the pooled labels, the only relevant document for q1 is d01. Compute both numbers with that relevant set, then with the full one.

</details>

<details><summary>Hint 3</summary>

Full labels: the relevant documents in the top 4 are d01 and d03, out of 3 relevant in total.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** d04 and d03 are unjudged (Judged@4 = 2/4).

```
                full labels          pooled labels
P@4             2/4 = 0.500          1/4 = 0.250      d03 is counted as not relevant
recall          2/3 = 0.667          1/1 = 1.000      only d01 is known to be relevant
```

Precision is underestimated (a real hit counted as a miss) and recall is overestimated (the denominator lost d03 and d09). Over all five toy queries, MiniLM's mean P@4 falls from 0.350 to 0.200 (K4).

**Key points** (a 3 needs every point):
- [ ] Unjudged: d04 and d03.
- [ ] P@4 falls from 0.500 to 0.250, because the relevant d03 is counted as not relevant.
- [ ] Recall rises from 0.667 to 1.000, because the pooled labels know only d01.

**For a 4, also:**
- [ ] Names the pattern and the fix: the retriever that did not build the pool is penalised (BEIR's pool bias), so pool from both retrievers and report Judged@k.

**Common wrong answers:**
- [ ] "Unjudged documents are skipped, so P@4 = 1/2": the convention counts them as not relevant.
- [ ] "Recall stays at 0.667": the denominator changed with the labels.

**If you missed it, reread:** [short §10](../reading/P2_ir_framing.md#10-labels-are-incomplete-and-noisy) · [full D.3](../../concepts/P2_ir_framing.md#d3-writing-relevance-judgments) · book Ch22 p.5/19

</details>
<!-- /q -->

<!-- q id=P2-A-06 type=A set=review -->
### P2-A-06 · Application (review: ties)
**Question:** In q4 the tie rule changes from doc id ascending to doc id descending: what is the new first relevant rank?

```
q4 "where does methane come from"     word-overlap scores: d06 1 · d09 1
relevant: d09 (grade 2)               current rule (ascending): d06, d09
```

**Reply template:** `New order: ____. First relevant rank: ____ (was ____). RR: ____ → ____.`

<details><summary>Hint 1</summary>

Both documents have the same score, so only the tie rule decides their order.

</details>

<details><summary>Hint 2</summary>

Descending doc id puts which of the two ids first?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** (K2)

```
ascending   →  d06, d09    first relevant rank 2    RR 0.50
descending  →  d09, d06    first relevant rank 1    RR 1.00
```

**Key points** (a 3 needs every point):
- [ ] The new order is d09, d06.
- [ ] The first relevant rank becomes 1 (it was 2).

**For a 4, also:**
- [ ] Says what to do about it: state the tie rule in every run, or emit strictly decreasing scores, because tools such as `trec_eval` re-sort by score and break ties by document id.

**Common wrong answers:**
- [ ] "No change, the scores did not change": with equal scores, only the rule sets the order.
- [ ] "Rank 2 either way, d06 always comes first": that is only the ascending rule.

**If you missed it, reread:** [short §7](../reading/P2_ir_framing.md#7-ranking-from-the-index-candidates-and-ties) · [full D.4](../../concepts/P2_ir_framing.md#d4-the-inverted-index) · book Ch22 p.6/19 (the rank of the first correct result)

</details>
<!-- /q -->

<!-- q id=P2-T-01 type=T set=main -->
### P2-T-01 · Transfer
**Question:** A legal team has 30 typical questions about their contracts and no relevance labels: what do you build first, so they can tell whether their search works?

**Reply template:** `First I would build ____, with ____ per line, judged by ____ under ____. I would check ____.`

<details><summary>Hint 1</summary>

Which three things make a test collection?

</details>

<details><summary>Hint 2</summary>

Who should judge, blind to what? Which unit should the labels use, and which candidates should be judged?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** A small test collection: the contracts, the 30 questions each with a one-line need, and qrels.
- A written guideline (what counts as answering; grades 2 / 1 / 0) with a version number.
- The judge is a lawyer, who writes a reason per label, before seeing any system's ranking.
- Labels are clause spans, not search-result ids, so they survive re-indexing and re-chunking.
- The candidates to judge are pooled from both keyword and dense search (the top k of each); report Judged@k next to every metric, and send new holes to the lawyer.
- Report a set measure at the k the users see and a rank measure; keep answer quality separate.

**Key points** (a 3 needs every point):
- [ ] qrels: question id, clause (span) id, grade and reason, under a written, versioned guideline.
- [ ] A domain judge (a lawyer), blind to the system's rankings.
- [ ] Candidates pooled from both keyword and dense search; Judged@k reported.
- [ ] Retrieval measured with a set and a rank measure, separately from answer quality.

**For a 4, also:**
- [ ] Says how to check the labels and what not to claim: re-label a sample (or use a second lawyer) and measure agreement with κ (above 0.8 good, 0.67–0.8 fair); 30 questions is below the usual ~50 needs, so use the set to compare versions, not for an absolute number.

**Common wrong answers:**
- [ ] "Let an LLM grade the search results at query time": a query-time grader is part of the system, a filter, not a label.
- [ ] "Use their reference answers as the ground truth": a reference answer is not a relevance label; it cannot score retrieval.

**If you missed it, reread:** [short §3](../reading/P2_ir_framing.md#3-a-person-judges-it-qrels) · [short §10](../reading/P2_ir_framing.md#10-labels-are-incomplete-and-noisy) · [short §12](../reading/P2_ir_framing.md#12-for-your-project-build-a-test-collection) · [full D.3](../../concepts/P2_ir_framing.md#d3-writing-relevance-judgments) · [full K](../../concepts/P2_ir_framing.md#part-k--engineering-decisions) · book Ch22 p.12/19

</details>
<!-- /q -->

<!-- q id=P2-T-02 type=T set=main -->
### P2-T-02 · Transfer (pool bias)
**Question:** A vendor report says a dense retriever loses to BM25 on a benchmark whose relevance labels were built from BM25's top results: what do you check before believing it?

**Reply template:** `I would check ____. I expect ____, because ____. I would believe it only if ____.`

<details><summary>Hint 1</summary>

What does the metric do with a document that the dense retriever found and nobody judged?

</details>

<details><summary>Hint 2</summary>

Name a number that shows how much of each system's top k was judged, and a test of whether the holes could flip the result.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Check the holes. Labels pooled from BM25 cover BM25's own top results; the dense retriever's different hits are unjudged and count as misses.
1. Judged@k (or Hole@k) for each system at the reported k.
2. A bounds check: score again with the holes counted as relevant. If the order flips, the labels decide the comparison, not the retrievers.
3. The fix: judge the holes blind (without knowing which system found them), then score again.

BEIR (external) found exactly this on TREC-COVID:

```
Hole@10                         BM25 6.4%    ANCE 14.4%    DPR 30.6%    TAS-B 31.8%
nDCG@10 after judging holes     ANCE 0.654 → 0.735        BM25 0.656 → 0.668
```

**Key points** (a 3 needs every point):
- [ ] Unjudged dense hits count as not relevant, so a pool built from BM25 favours BM25.
- [ ] Check Judged@k (Hole@k) for each system.
- [ ] Judge the holes blind and score again before accepting the result.

**For a 4, also:**
- [ ] Gives evidence and a limit: BEIR's ANCE moved from just below BM25 to above it once its holes were judged; even a fair result holds only for that benchmark, so test on your own labels with a two-retriever pool.

**Common wrong answers:**
- [ ] "A benchmark is objective, so dense is worse": the labels came from one of the two systems.
- [ ] "Look at recall instead of precision": recall's denominator misses the same unjudged documents.

**If you missed it, reread:** [short §10](../reading/P2_ir_framing.md#10-labels-are-incomplete-and-noisy) · [full D.3](../../concepts/P2_ir_framing.md#d3-writing-relevance-judgments) · book Ch22 p.5/19 (recall assumes every relevant document is known)

</details>
<!-- /q -->

<!-- q id=P2-R-07 type=R set=interview source=AIQ-04-Q45 -->
### P2-R-07 · Interview (Recall)
**Question:** "How do you build a golden evaluation set for RAG without months of labelling?"
*From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md` (question 45), Copyright (c) 2026 Om, MIT License.*

**Reply template:** `A golden set is ____. I make labelling fast by ____. I keep it honest by ____.`

<details><summary>Hint 1</summary>

Judging a short candidate list is faster than searching the whole corpus. Where do the candidates come from, and what does that choice miss?

</details>

<details><summary>Hint 2</summary>

What happens later when a new pipeline retrieves a relevant chunk that nobody judged? And when you change the chunk size?

</details>

<details><summary>Show answer (write yours first)</summary>

> **The repo's answer (excerpt, verbatim).** *From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md`, Copyright (c) 2026 Om, MIT License:*
>
> "A useful golden set is (query → relevant chunk IDs → optionally a reference answer), even just 100-300 rows. Bootstrap in layers:"
>
> "for each, label relevant chunks by running generous retrieval (top-50 hybrid) and having a human mark hits - verifying candidates is 10× faster than authoring labels from scratch."
>
> "**Handle the incomplete-labels problem.** Your relevance labels will miss valid chunks (annotators only saw retrieved candidates), so recall is measured against known-relevant, and a pipeline change surfacing a genuinely relevant *unlabelled* chunk scores as a miss. Mitigate by periodically re-adjudicating: when a new pipeline retrieves unlabelled chunks at high rank, send them to labelling and grow the set."
>
> "**Operate it like code**: version the set, tie it to a corpus snapshot (chunk IDs go stale when re-chunking - store text spans, not just IDs), refresh quarterly from new logs, and quarantine a held-out slice you never tune against."

**Our check of that answer:** the shape is right: judge a candidate pool instead of searching the corpus, expect incomplete labels and re-judge the holes, store spans, version the set and keep a held-out slice. These match P2 §3, §10 and §12. Two corrections:
1. "Verifying candidates is 10× faster" has no source in the answer or in ours. Keep the method; drop the number until you time it yourself.
2. The candidates come from one pipeline (a top-50 hybrid run). Labelling only one system's candidates is what BEIR measured as **pool bias**: on TREC-COVID, Hole@10 was 6.4% for BM25 but 14.4–31.8% for dense retrievers, and judging ANCE's holes raised its nDCG@10 from 0.654 to 0.735. So pool the top k of each retriever separately (BM25 **and** dense, plus the fused list), judge blind to the source, and report Judged@k. The incomplete-labels paragraph also understates one effect: recall measured against known-relevant chunks is not only missing hits, it can look **too high** (on our toy, MiniLM's mean recall rose from 0.933 to 1.000 under a one-retriever pool).

**Model answer:** A golden set is a test collection: queries (each with a written need), their relevant chunks as qrels under a versioned guideline, and optionally a reference answer. To make it fast, a person judges a pooled candidate list instead of the whole corpus: the union of the top k from both a keyword (BM25) and a dense retriever, judged blind to the source, with a reason per label. To keep it honest: unjudged chunks count as not relevant, so report Judged@k next to every metric and send the holes in any new pipeline's top k to labelling, bumping the qrels version; store evidence as spans so that labels survive re-chunking; re-label a sample to check agreement; add hard cases (unanswerable, exact terms, vocabulary mismatch); tune on dev and report on a held-out test split.

**Key points** (a 3 needs every point):
- [ ] A golden set = queries + relevant chunks (qrels) under a guideline, optionally a reference answer.
- [ ] Fast: judge a pooled candidate list, pooled from both keyword and dense retrieval, not one pipeline.
- [ ] Unjudged = not relevant, so report Judged@k and re-judge holes; version the set.
- [ ] Store spans, not chunk ids.

**For a 4, also:**
- [ ] Corrects the repo's answer with evidence: "10× faster" is unsourced, and a one-pipeline pool is BEIR's pool bias (dense Hole@10 up to 31.8% against BM25's 6.4%; ANCE 0.654 → 0.735 after judging holes).

**Common wrong answers:**
- [ ] "Generate questions from each chunk with an LLM and use that chunk as the only label": every other relevant chunk is unjudged and scores as a miss.
- [ ] "Label from the current retriever's top results, that is enough": that pool favours the current retriever.

**If you missed it, reread:** [short §3](../reading/P2_ir_framing.md#3-a-person-judges-it-qrels) · [short §10](../reading/P2_ir_framing.md#10-labels-are-incomplete-and-noisy) · [short §12](../reading/P2_ir_framing.md#12-for-your-project-build-a-test-collection) · [full D.3](../../concepts/P2_ir_framing.md#d3-writing-relevance-judgments) · book Ch22 p.12/19 (queries paired with expected relevant documents and a reference answer)

</details>
<!-- /q -->
