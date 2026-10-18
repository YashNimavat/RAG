<!-- kit:reading concept=P2 depth=short version=1 -->
# P2: Information-retrieval framing: needs, relevance, the inverted index and sets vs rankings

**What this is:** the short reading for P2. It follows one question, the book's own "What is the main cause of climate change?", through two retrievers, a person's judgment, the inverted index, the cut at k and the blind spots of the labels, first on a 10-document toy collection and then on the climate PDF.
**What this is not:** the full lesson with the lab ([concepts/P2_ir_framing.md](../../concepts/P2_ir_framing.md)), the BM25 weights (P3), how embeddings work (P4), or the ranking metrics MRR, nDCG and CE@k (P6).

**The answer first.**
1. A retriever never sees relevance. It computes one similarity score for each (question, chunk) pair, sorts the chunks and cuts the list at k.
2. Relevance is a person's judgment: does this chunk help answer the need behind the question? It is written under a guideline and stored as qrels: query, chunk, grade.
3. Similarity is only the system's stand-in for relevance, and it fails in known ways: an echo of the question, a keyword-stuffed footer, an answer phrased in other words.
4. Keyword search finds its candidates through an inverted index (word → chunks), so a chunk that shares no word with the question can never be returned.
5. You measure a run against the qrels with two separate questions: what is in the set, and how high the first useful chunk sits. The numbers are only as good as the labels, because a chunk nobody judged counts as irrelevant.

> **Read in the book:** Ch1 p.8/14, Ch3 p.1/14, Ch13 p.1–2/13, Ch22 p.4–7/19 and p.12/19, plus Ch12 p.3/14 for the index. About 10 minutes. Read them after §4. The book never says "inverted index" or "qrels": the index appears only as the back-of-cookbook analogy, and qrels only as a query's "expected relevant documents".

**Labels used below.** *Measured* numbers come from our scripts. *Toy* means the ten made-up documents written for this lesson: they show that an effect exists, not how often it happens. *Formula* lines are arithmetic you can redo. *External* numbers come from a named paper. Every measured number is in [P2_FACTS](../../sources/verification/P2/P2_FACTS.md) (S1–S11 and K1–K6). No API was called to write this file.

---

## 1. The need behind the question

**The setup.** Four words name the objects. The **collection** is everything the system can search. A **document** is the unit it can return; in RAG that is a chunk. The **information need** is what the person wants to know. The **query** is the text they typed. Our toy collection (S1):

```
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

q1 main cause of climate change    q2 why do sea levels rise    q3 renewable energy
q4 where does methane come from    q5 is extreme heat becoming more common
```

q1 is the book's worked question in keyword form (Ch1 p.8/14). The book retrieves chunks for it and simply calls them relevant. P2 tests that claim instead of assuming it.

**The result.** One query can hide two needs. Take the query `carbon dioxide`:

```
need A: what puts carbon dioxide into the air?     d01 helps     d06 does not
need B: what takes carbon dioxide out of the air?  d06 helps     d01 does not
```

**What this means.** The words are the same; the useful document is not. Both documents contain both words, so a judge who reads only the words would mark both relevant. **Relevance is judged against the need, not against the query's words.** The textbook example is "python": a snake, or a programming language (Manning et al., *Introduction to Information Retrieval*, §8.1).

**For your project:** every question in the eval set gets a one-line note of its need, written before any labelling.

## 2. Two retrievers score it; similarity is not relevance

**The setup.** Two retrievers score q1 against every toy document. *Word overlap* counts how many distinct query words a document contains, using the index of §5. *MiniLM* is a small embedding model: it turns each text into a list of 384 numbers (a vector) so that texts with similar meaning get nearby vectors, and the cosine measures how close two vectors are. P4 teaches how.

**The result** (measured, S5–S6):

```
word overlap   d02 5   d01 3   d08 2          (no other document shares a q1 word)
MiniLM cosine  d02 0.8402   d01 0.6342   d04 0.5139   d03 0.4904  ...  d09 0.2469 (rank 9 of 10)
```

**What this means.** Both retrievers put d02 first, and d02 answers nothing: it repeats the question. **Similarity** is a score that a function computes from the query text and the document text. **Relevance** is whether the document helps the need. Systems rank by similarity because it is cheap to compute for every pair; it is a proxy, and labels measure how good the proxy was. The book makes the same point twice: a page footer full of links scores well and helps nothing (Ch3 p.1/14), and three chunks that echo the question "What is the capital of France?" outrank the one chunk that names Paris (Ch13 p.1–2/13). Our d02 (an echo) and d08 (a keyword-stuffed footer) are the toy versions.

**The tempting wrong idea (MC-002):** "the system compares everything in a similarity matrix". A retriever computes **one score per (query, document) pair** and sorts. It never builds an all-pairs matrix.

**For your project:** never call a chunk relevant because it ranked first. Only labels can say.

## 3. A person judges it: qrels

**The setup.** A judge reads each document against the need, using a written guideline (version 1):

```
2  sufficient     the document alone answers the query
1  partial        it gives part of the answer, or a necessary piece of it
0  not relevant   it does not help, even if it shares words or the topic
binary rule:      relevant  ⇔  grade ≥ 1
```

**The result** (toy labels, S7):

```
qid  doc  grade  reason
q1   d01  2      names the main cause: burning fossil fuels releases carbon dioxide
q1   d03  1      the mechanism (greenhouse gases trap heat), not what emits them
q1   d09  1      one source of a greenhouse gas: part of the cause, not the main one
q1   d02  0      repeats the question; no answer
q1   d08  0      topic words without content
q2   d04  2      gives the reasons: warm water expands and glaciers melt
q2   d05  1      one reason: melting ice sheets add water
→ 8 relevant pairs out of 50 (5 queries × 10 documents); every pair not listed is 0
```

**What this means.** A **qrels** file (query relevance judgments) holds one line per judged pair: query id, document id, grade. A pair that is not listed counts as 0. Four rules keep the labels useful:
- **Judge the need, not the words** (§1).
- **Write a one-line reason** for every non-zero label and for every tempting zero. Reasons expose a vague guideline.
- **Judge before you see any system's ranking**, or you end up grading the system's opinion.
- **Give the guideline a version**, and bump it whenever a sentence changes. d03 and d09 are judgment calls; a disagreement shows where the guideline needs one more sentence.

**For your project:** the book describes the same object without the name: an evaluation dataset pairs each query with its expected relevant documents and a reference answer (Ch22 p.12/19). The expected relevant documents are the qrels.

## 4. Three meanings of "relevance"

**The setup.** The word "relevance" means different things in the book, in the repo and in this course. Take d02 for q1.

**The result:**

| Meaning | Who decides | d02 for q1 |
|---|---|---|
| **System** relevance: the score | the retriever | high: rank 1 in both retrievers |
| **Topical** relevance: about the topic | anyone reading the words | yes: it is about climate change |
| **Situational** relevance: helps answer the need | a judge, against the need | no: grade 0 |

**What this means.** Our qrels label the third meaning: grade 2, "alone answers the query", is situational relevance. The book's "context relevance" asks the same question about each retrieved chunk, with a language model as the scorer (Ch22 p.4/19); its triad picture also uses "relevance" for question → answer. The book's "relevancy grading" is a **filter**: an LLM drops chunks at query time (App p.20/23). **A query-time LLM grader is a filter, not a label.** It is part of the system you are measuring, so it cannot also be the ruler. An LLM can also be used offline to write labels (an LLM assessor); then it is a judge, and the course runs judges only once, at the end, after checking them against human labels.

**For your project:** when someone says "relevant", ask which meaning. In the eval, only the judge's grade counts.

## 5. The inverted index

**The setup.** Write the collection as a table: one row per word, one column per document, a 1 where the word occurs (a term–document incidence matrix). Almost every cell is 0. Keep only the 1s, row by row, and you have the **inverted index**: for each term, the sorted list of documents that contain it, called its **postings list**. A term's **document frequency** (df) is the length of its postings list. Before indexing, the text is tokenized: lower-case, a token is a run of letters a–z or digits 0–9, no stemming, no stop-word list.

```python
import re
from collections import defaultdict

def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())

def build_index(docs):                        # {doc_id: text}
    index = defaultdict(set)
    for doc_id, text in docs.items():
        for term in set(tokenize(text)):      # each id once per term
            index[term].add(doc_id)
    return {term: sorted(ids) for term, ids in index.items()}
```

**The result** (measured, S3):

```
88 terms · 114 postings (from 119 tokens) · 71 terms in one document only
climate → d02, d08     change → d02, d08     of → d01, d02     main → d01, d02     cause → d01, d02
the     → d01, d02, d03, d05, d06   (df 5)   carbon → d01, d06   methane → d09
rise → (none)     rising → d04     renewable, energy → (none)
every postings list equals a full scan of the documents: asserted
```

**What this means.** It is "inverted" because a book is organised by page and the index by word, like the index at the back of a book, which tells you which pages mention a word (the book's cookbook analogy, Ch12 p.3/14). A query reads only the postings of its own words; documents that share no word are never touched. The index matches strings, not meaning: `rise` does not find "rising". Its tokens are whole words from its own simple tokenizer, not the LLM's sub-word tokens of P1 (MC-001): each system cuts text its own way ([P3 §6](P3_bm25.md#6-tokenization-decides-what-can-match)).

**For your project:** the index is the fast path for exact terms such as IDs and error codes. P3 keeps the same postings and replaces "+1 per hit" with a BM25 weight. The repo's BM25 (`rank_bm25` 0.2.2) keeps one word-count dictionary per document and scores every document: correct, but a scan, not an inverted index (S10).

## 6. Boolean AND and OR, and the postings read

**The setup.** **AND** keeps the documents that are in every postings list of the query (intersection). **OR** keeps those in any list (union). The work done is the number of **postings read**: the sum of the lists' lengths.

**The result** (measured, S4):

```
query                                     AND    OR                 postings read
q1 main cause of climate change           d02    d01, d02, d08      10   (5 words × 2)
q2 why do sea levels rise                 —      d04                 2
q3 renewable energy                       —      —                   0
q4 where does methane come from           —      d06, d09            2
q5 is extreme heat becoming more common   —      d02, d03, d10       5
```

**What this means.** AND is too strict: four of five queries return nothing, and q1's only hit is the echo d02. OR is too loose: q4 pulls in d06 only through the word "from". q3 is a **vocabulary mismatch**: solar panels and wind turbines (d07) are renewable energy, but neither query word occurs anywhere, so there are 0 postings and keywords can never find d07. (MiniLM ranks d07 first for q3, 0.5804.) A middle ground between AND and OR is hard to build from Boolean operators; ranking (§7) replaces it.

How AND is computed: walk two sorted postings lists side by side, like a merge, so the cost is O(x + y) for lists of lengths x and y. With several words, start with the shortest lists (smallest df), so the intermediate result stays small.

**For your project:** check every eval question for zero postings (a vocabulary-mismatch question) and for an OR set that covers most of the collection (common words only).

## 7. Ranking from the index; candidates and ties

**The setup.** Ranked retrieval walks the same postings and adds a weight for each hit. Here the weight is 1, so a document's score is the number of distinct query words it contains. Then sort by score.

**The result** (measured, S5 and K2):

```
q1   d02 5   d01 3   d08 2            3 candidates: no other document has a q1 word
q4   d06 1   d09 1                    a tie; the relevant document is d09
     ties by doc id ascending   →  d06, d09    first relevant rank 2
     ties by doc id descending  →  d09, d06    first relevant rank 1
```

**What this means.** Only a document in the union of the query's postings can score above 0. The index fixes the **candidate set**, and no k can add a document outside it. Equal scores need a **tie rule**, and the rule alone moved the relevant d09 from rank 2 to rank 1. Evaluation tools such as `trec_eval` re-sort a run by score and break ties by document id, so the order you saved is not always the order that gets scored.

**For your project:** state the tie rule in every run file, or emit strictly decreasing scores.

## 8. Cut at k: set precision and set recall

**The setup.** Keep the top k of a run: that is the retrieved **set** R. Compare it with the relevant set Rel from the qrels:

```
set precision = |R ∩ Rel| / |R|       how much of what I retrieved is relevant?
set recall    = |R ∩ Rel| / |Rel|     how much of the relevant material did I retrieve?
```

**The result** (measured, q1, relevant = d01, d03, d09; S8 and K3):

```
                 k = 3                  k = 6
word overlap     P 0.333   R 0.333      P 0.333   R 0.333     only 3 candidates
MiniLM           P 0.333   R 0.333      P 0.333   R 0.667     d03 enters at rank 4: 1/3 → 2/6
recall@k for q1: word overlap flat at 0.333 from k = 2 on;  MiniLM 0.667 at k = 4, 1.0 only at k = 9
```

**What this means.** A bigger k raised MiniLM's recall and left its precision flat, because one relevant and two non-relevant documents came in together (MC-005: k trades evidence against noise). For word overlap nothing changed: the candidate set caps recall. Two more facts:
- **Accuracy is useless here.** Almost every pair is non-relevant, so returning nothing at all already gets 42 of the 50 toy pairs right (50 − 8). Precision and recall look only at the relevant side.
- **Recall needs |Rel|**, the number of all relevant documents. You know it only if every relevant document was labelled (§10). The book defines recall the same way, over all relevant documents in the knowledge base, and gives its own worked numbers for both measures (Ch22 p.4–5/19).

**For your project:** report set precision and recall at the k the generator actually reads.

## 9. Set quality is not ranking quality

**The setup.** Three hand-made runs for q1 (toy, S8).

**The result:**

```
run  top 3            precision  recall  first relevant rank   RR = 1/rank
A    d02, d01, d08    0.333      0.333   2                     0.5
B    d01, d08, d02    0.333      0.333   1                     1.0
C    d01, d03, d09    1.0        1.0     1                     1.0
```

**What this means.** A and B hold the same set, so they have the same precision and recall, but B puts the relevant d01 first. B and C share a first relevant rank but hold different sets. **Set measures cannot see order; a rank measure cannot see the rest of the set.** The book says this in its own words: precision and recall describe what came back, not how it was ordered (Ch22 p.6–7/19). The **first relevant rank** answers "how early does the first useful chunk appear?"; its reciprocal, RR = 1/rank, is the per-query piece of MRR. P6 owns MRR, nDCG and CE@k.

**For your project:** report one set measure and one rank measure for every run. They disagree.

## 10. Labels are incomplete and noisy

**The setup.** Nobody labels every pair of a real collection. The usual practice is **pooling**: judge only the documents that some system ranked high, and treat every unjudged document as not relevant (the TREC convention). What happens if the pool comes from one retriever? We built labels only from the word-overlap top 3 and scored both retrievers at k = 4 (toy, K4).

**The result** (measured, K4):

```
q1 pool (judged): d01, d02, d08          MiniLM top 4: d02, d01, d04, d03
d03 is relevant (grade 1) but unjudged   → counted as not relevant
                          full labels    pooled labels
MiniLM  q1 P@4            0.500          0.250
MiniLM  mean P@4          0.350          0.200
MiniLM  mean recall       0.933          1.000
overlap mean recall       0.567          1.000
MiniLM  mean Judged@4     0.350          (Hole@4 = 1 − 0.350 = 0.650)
```

**What this means.** Unjudged is not the same as irrelevant, but the metric treats it so. **Precision drops for the retriever that did not build the pool.** Recall goes the other way: the pooled labels know fewer relevant documents, so the denominator shrinks, both retrievers look perfect (1.000), and the real gap (0.567 against 0.933) disappears. Two diagnostics show the problem: **Judged@k**, the part of a run's top k that has a label, and **Hole@k** = 1 − Judged@k. A quick bounds check: score again with every hole counted as relevant; if the order of two systems flips, the labels decide the comparison, not the retrievers.

BEIR measured the same effect on a real benchmark (external: Thakur et al., NeurIPS 2021, TREC-COVID). The authors then judged the missing pairs, blind to which system had found them:

```
Hole@10                         BM25 6.4%   docT5query 2.8%   ANCE 14.4%   DPR 30.6%   TAS-B 31.8%
nDCG@10 after judging holes     ANCE 0.654 → 0.735          BM25 0.656 → 0.668
```

ANCE went from just below BM25 to above it. The pool favoured lexical systems, although many teams had contributed to it.

Labels are also noisy: **two careful judges agree only fairly well.** Agreement is measured with κ = (P(A) − P(E)) / (1 − P(E)), where P(A) is how often the judges agree and P(E) how often they would agree by chance. IIR's two-judge example gives κ ≈ 0.776 (we recomputed 0.7759); above 0.8 counts as good, 0.67–0.8 as fair. Swapping judges changes the absolute scores, but rarely the order of systems.

**For your project:** pool from both retrievers, report Judged@k next to every retrieval number, and send every hole in a top k to the judge.

## 11. The real PDF

**The setup.** The same index over the climate PDF, cut into 91 windows of 1,000 characters (overlap 200, as in P1). Then the 06 draft questions' evidence spans, turned into window labels: a window is relevant if it overlaps a span (06 §7.2).

**The result** (measured, S9 and K5):

```
1,868 terms · 8,107 postings
main cause of climate change:   OR 90 of 91 windows · AND 0 · 213 postings read  (a scan reads all 91)
span labels → relevant windows (window ids from 0):
D-002  one span                 → 25, 26     two overlapping windows
D-004  two alternative spans    → 22, 63
D-005  two evidence groups      → 2, 3, 4    window 3 serves both groups
```

**What this means.** With common words, OR returns almost everything and AND returns nothing, and the index saves almost no work. Long postings for common words are why P3 down-weights them. On the real PDF the labels are character spans, not window ids. One span can make two overlapping windows relevant, so the chunk-level qrels change whenever the chunking changes. The draft questions are LLM drafts (06 §6.7): illustration only.

**For your project:** store spans; derive chunk qrels for each chunker.

## 12. For your project: build a test collection

**The setup.** IR's standard design (the Cranfield paradigm, used by TREC): a **test collection** = documents + information needs + qrels.

**The result** (what it means for "Ask My Technical PDFs"):

| Piece | In the project |
|---|---|
| Documents | the chunks of your PDFs; labels as spans, chunk qrels derived by overlap |
| Needs | about 50 is IIR's usual minimum; tune on a dev split, report on a held-out test split |
| qrels | 06 `evidence_groups`, judged under a versioned guideline |
| Pool | the top k of both keyword and dense retrieval, judged blind |
| Report | Judged@k next to every retrieval metric |

**What this means.** **Qrels measure retrieval only.** A reference answer is not a relevance label: the repo's `data/q_a.json` holds 44 question–answer pairs and no relevant documents, so it cannot score a retriever. Answer quality is a separate measurement. Fewer needs than the usual minimum still let you compare two versions on the same labels; they are weak evidence for an absolute number.

**For your project:** M1 builds this collection; M2 runs the metrics on it.

## 13. When not to use it

- **No inverted index for one PDF.** A scan of 91 windows is fast enough; that is the repo's choice. Build the index when the collection is large.
- **No graded labels when only "is any evidence present?" matters.** Binary labels are quicker. Grades are needed for nDCG (P6).
- **No absolute claim from a one-retriever pool or a single judge.** Compare versions on the same labels, and say so.
- **No conclusion about frequency from the toy.** It shows that an effect exists, not how often it happens on your PDFs.

What P2 does not cover: BM25 weights (P3), how embeddings are built (P4), MRR, nDCG and CE@k (P6), LLM judges (M3).

## Check yourself

→ [`study/questions/P2_questions.md`](../questions/P2_questions.md): 2 cold questions before reading, 13 after, 1 for a later review, and 1 interview question. Answer the next day, closed book.
