<!-- kit:reading concept=R1 depth=short version=1 -->
# R1: Sparse, dense and hybrid retrieval, and how to fuse them

**What this is:** the short, book-first reading for R1. It explains why you run keyword search (BM25) and dense search side by side, and three ways to merge their two lists: min-max weighting, the three-sigma range, and Reciprocal Rank Fusion (RRF).
**What this is not:** the full lesson with the lab and the v2.0 experiment ([concepts/R1_hybrid_fusion.md](../../concepts/R1_hybrid_fusion.md)), or how BM25 itself scores a chunk ([P3](../../concepts/P3_bm25.md)).

**The answer first.** Dense retrieval can rank the chunk that *names* a rare term below chunks that are merely *about* its topic. BM25 cannot match a paraphrase. Hybrid retrieval runs both over the same chunks and merges the two ranked lists. You cannot add their raw scores, because they live on different scales. Either normalise each list and take a weighted sum, or fuse the **ranks** with RRF, which needs no normalisation. On our 10 draft seeds, fusion moved the evidence up (MRR@10 from 0.708 to 1.000 with RRF) but did not change CE@4, which dense retrieval already had at 8/8. The repo's fusion code mixes up its documents and, transcribed onto our chunks, finds the evidence for none of the seeds.

> **Read in the book:** Ch12 p.1–2/14 and p.5–14/14, about 25 minutes. Read them after §1. The cookbook analogy on Ch12 p.3–4/14 is optional, and so are the glossary entries in App p.16–17/23, p.19/23 and p.21/23.

**Labels used below.** *Draft seeds* are the 10 `llm-draft` items of 06 §6.7: observations for learning, never an evaluation result. *Demonstration* means a hand-picked query, with its target found by string search, not by gold labels. *Toy* numbers are made up. Every number comes from `sources/verification/R1/r1_measure.py` ([R1_FACTS](../../sources/verification/R1/R1_FACTS.md)), run on the same 97 chunks and the same local MiniLM index as the C-labs. No API was called.

---

## 1. The failure hybrid retrieval fixes

**The setup.** The book opens the chapter with a chemical acronym (Ch12 p.1/14). The meaning-based search ranks the one chunk that names it fourth, behind chunks about the general topic. On the next page it shows the opposite failure: keyword search misses a chunk that says the same thing in other words (Ch12 p.2/14). We ran P3's five exact-term queries on our own 97 chunks and recorded where the chunk that contains the term lands.

**The result** (demonstration):

```
query                           chunk that names the term     dense rank   BM25 rank
"IPCC"                          page 1                             3            1
"What does BECCS stand for?"    page 30                            4            1
"methane CH4"                   page 1                             4            1
"Kyoto Protocol 1997"           page 24                            1            1
"limit warming to 1.5 degrees"  pages 10, 23                       4            1
```

And the reverse, on draft seed D-006 ("What are the advantages of putting solar panels on lakes or reservoirs?"): the evidence chunk talks about solar farms on water bodies and never says "lakes" or "panels". Dense ranks it 1st; BM25 ranks it 2nd, behind a page-22 chunk that contains the rare word "panels".

**What this means.** Each retriever has a blind spot, and they are different blind spots. Dense retrieval blurs a rare identifier into its topic, so the chunk that names it slips down the list (BECCS at rank 4, just like the book's acronym). BM25 sees only tokens, so a paraphrase scores on whatever common words happen to match.

**For your project:** the v2.0 version card targets exactly the first failure: acronyms, numbers and rare names (06 §4.2). Your eval set has an `exact-term` category for it and a `vocabulary-mismatch` category to make sure the fix does not break the second.

## 2. One question, two retrievers: the Kigali example

We follow one real question through every step of this reading: **draft seed D-008, "What does the Kigali Amendment target?"** Its evidence is one sentence in a chunk on page 24 (chunk seq 69, the Kyoto Protocol paragraph, which also mentions the Kigali Amendment).

**The setup.** Both retrievers score the same 97 chunks. BM25 uses P3's `tok_norm` tokenizer on the question: `what does the kigali amendment target`. Three of those tokens (`what`, `does`, `target`) occur in no chunk at all, so they add nothing. `the` is in 80 of 97 chunks and gets a small floor weight (0.8588). `kigali` and `amendment` occur in **one** chunk each, so they get the highest weight possible here (idf 4.1641).

**The result** (draft seed):

| Rank | Dense: chunk (page) | Cosine | BM25: chunk (page) | BM25 score |
|---|---|---|---|---|
| 1 | seq 28 (page 10), carbon pricing, no query word | 0.2598 | **seq 69 (page 24), the evidence** | **9.4618** |
| 2 | **seq 69 (page 24), the evidence** | **0.2535** | seq 0 (page 1), matches only "the" | 1.8858 |
| 3 | seq 58 (page 20) | 0.2478 | seq 1 (page 1) | 1.8377 |
| 4 | seq 12 (page 5) | 0.2041 | seq 2 (page 1) | 1.7458 |

**What this means.** Dense puts the evidence second, 0.0063 behind a chunk about carbon prices. BM25 puts it first by a factor of five, because nothing else contains the rare words. Neither list is wrong on its own terms: they measure different things. The question for the rest of this reading is how to merge them.

**For your project:** this is a *retrieval ranking* question (CR-11). At k = 4 the evidence is already in the dense top-4; whether the LLM then answers correctly is a separate, generation question.

## 3. Why you cannot add the two scores

**The setup.** The simplest merge is to add the two scores of each chunk. The book warns against it: a cosine near 0.8 and a BM25 score near 14 cannot be added, because the bigger number would decide (Ch12 p.7–8/14).

**The result** (draft seeds):

```
D-008, Kigali chunk:   dense 0.2535  +  BM25 9.4618  =  9.7153
cosine scores are bounded (−1 to 1); the best dense score per seed was 0.26 to 0.71
BM25 scores are not; the best BM25 score per seed was 7.0 to 43.6
raw-sum top-4 vs BM25 top-4, 10 seeds:   37 of 40 chunks are the same
```

**What this means.** A raw sum is almost exactly BM25 alone. The dense score is too small to move anything.

**For your project:** never add raw scores from two retrievers. Normalise each list first (§4–§5), or use ranks (§6).

## 4. Normalising: min-max and the three-sigma range

The book gives two ways to put both lists on a 0-to-1 scale (Ch12 p.8/14). Apply each one **to one list at a time**.

```
min-max:       (s − min) / (max − min)                       the best → 1, the worst → 0
three-sigma:   (s − (mean − 3·sd)) / (6·sd)                  the book's "distribution-based" form
```

**The setup.** D-008 again. Each retriever passes on its top-50 (the 06 v2.0 design). The dense list runs from 0.2598 down to 0.0909; the BM25 list from 9.4618 down to 1.2000.

**The result** (draft seed, then a toy):

```
min-max of the Kigali chunk:     dense (0.2535 − 0.0909) / (0.2598 − 0.0909) ≈ 0.96     BM25 1.0000
                                 (0.9625 from the unrounded scores)
three-sigma of the Kigali chunk: BM25 1.6546                         ← above 1

toy list [2, 4, 6]:              min-max [0, 0.5, 1]       three-sigma [0.296, 0.5, 0.704]
toy list [1, 2, 3, 4, 100]:      min-max [0, 0.010, 0.020, 0.030, 1]
                                 three-sigma [0.410, 0.415, 0.419, 0.423, 0.833]
values outside 0..1 under three-sigma, 10 seeds × top-50:  dense 9 of 500, BM25 15 of 500
```

**What this means.** The book says the three-sigma form is more robust than min-max, which a single outlier can distort. Our toy shows it is not robust against that outlier: the 100 still squeezes the other four scores into a narrow band (0.410 to 0.423). And the book's "between 0 and 1" is not guaranteed: a score more than three standard deviations from the mean lands outside it, which happened 24 times on our seeds.

**For your project:** if you use the three-sigma form, decide whether to clip at 0 and 1 and write it down. Its result is not a probability either.

## 5. Weighted fusion, and the zero that means two things

**The setup.** Weighted fusion adds the normalised scores with weights, for example 0.6 for dense and 0.4 for BM25 (Ch12 p.9/14). The book also gives the rule for a chunk that only one retriever returned: only that retriever's part counts. In other words, a **missing chunk gets 0** from the other list. The book suggests weights from 50/50 to 70/30 (Ch12 p.11/14, p.14/14). Here is D-008 with min-max and 0.5/0.5.

**The result** (draft seed):

| Chunk | Dense part | BM25 part | Fused | Fused rank |
|---|---|---|---|---|
| seq 69, Kigali (evidence) | 0.5 × 0.9625 | 0.5 × 1.0000 | **0.9813** | **1** |
| seq 28 | 0.5 × 1.0000 | 0 (not in the BM25 top-50) | 0.5000 | 2 |
| seq 58 | 0.5 × 0.9287 | 0 (not in the BM25 top-50) | 0.4643 | 3 |
| seq 12 | 0.5 × 0.6701 | 0.5 × 0.0496 | 0.3598 | 4 |

**What this means.** Two things hide in that table.
- **The 0 means two things.** Min-max gives the *last* chunk of each list a 0, and the book gives a *missing* chunk a 0. So the 50th chunk a retriever found counts exactly as if it had not found it.
- **The weights decide close calls.** Toy lists: dense A 0.62, B 0.58, C 0.41 and BM25 C 7.9, A 2.1, D 1.8. Weights 0.5/0.5 give the order A, C, B, D; weights 0.6/0.4 give A, B, C, D. One step of 0.1 swapped two documents.

**For your project:** weighted fusion has knobs (the weight, the normaliser, the list depth), and each one is a variable to record in the run config. The book's advice to tune the weights on representative queries (Ch12 p.11–12/14) means a labelled dev set, which is what v2.0 uses.

## 6. Reciprocal Rank Fusion: ranks, not scores

**The setup.** RRF (Cormack et al. 2009, the v2.0 card's primary arm) ignores the scores and uses only positions:

```
RRF(d) = Σ over the lists of  1 / (k + rank of d in that list)       ranks start at 1, usually k = 60
```

A document missing from a list gets nothing from it. The book does not mention RRF at all.

**The result** (draft seed D-008, top-50 lists, k = 60):

```
seq 69 (Kigali): dense rank 2, BM25 rank 1  →  1/62 + 1/61 = 0.016129 + 0.016393 = 0.032522   ← rank 1
seq 56:          dense rank 6, BM25 rank 13 →                                     0.02885     ← rank 2
seq 28:          dense rank 1, not in BM25  →  1/61                             = 0.016393    ← rank 31
```

**What this means.** Three properties follow from the formula.
- **No normalisation, and rescaling cannot hurt.** We multiplied the dense scores by 100 and, separately, bent them with exp(10 s). RRF's top-4 changed for 0 of the 10 seeds both times. Min-max fusion changed for 0 and 4 of 10.
- **Agreement beats a single vote.** One first place is worth 1/61 = 0.0164. A chunk in both top-50 lists gets at least 2/110 = 0.0182. So with lists of 61 or fewer, every chunk both retrievers found outranks every chunk only one found. That is why seq 28, dense's own winner, falls to rank 31; min-max fusion keeps it at rank 2.
- **k and ties matter.** A small k lets a single first place dominate; a large k rewards agreement. On the seeds, k from 60 to 0 changed 5 of 10 top-4 lists (CE@4 stayed 8/8). And on D-006 the top two chunks tie **exactly** (1/61 + 1/62 both ways); only the tie rule, the smaller `chunk_id`, put the evidence first.

**Try it** (the whole method, on D-008's top-3 lists):

```python
def rrf(ranked_lists, k=60):
    fused = {}
    for lst in ranked_lists:                       # each list: ids, best first
        for rank, d in enumerate(lst, 1):          # ranks start at 1
            fused[d] = fused.get(d, 0.0) + 1.0 / (k + rank)
    return sorted(fused, key=lambda d: (-fused[d], d))   # ties: smaller id first

print(rrf([["c28", "c69", "c58"], ["c69", "c0", "c1"]]))   # ['c69', 'c28', 'c0', 'c1', 'c58']
```

With lists this short, dense's winner c28 still comes second. With the real top-50 lists it falls to 31st, for the reason above.

**For your project:** on the 10 draft seeds, RRF put the first relevant chunk at rank 1 for all 8 answerable items, one of them (D-006) by the tie rule (MRR@10 1.000; dense 0.708; BM25 0.938; min-max 0.5/0.5 0.938). CE@4 was 8/8 for every method, so these easy drafts cannot show a CE gain. That is what the frozen eval set and Part I of the full lesson are for.

## 7. The repo's fusion mixes up its documents

**The setup.** `fusion_retrieval.ipynb` cell 17 (and `all_rag_techniques_runnable_scripts/fusion_retrieval.py` L75–L86) makes three calls, and each returns a different order:
- `similarity_search("")` returns every chunk, **nearest to the empty string** first;
- `bm25.get_scores(...)` returns one score per chunk in **corpus** order;
- `similarity_search_with_score(query)` returns the chunks **nearest to the query** first.

It then adds the vector and BM25 arrays position by position and returns `all_docs[i]`. Position i belongs to three different chunks. We transcribed this logic onto our 97 chunks, with MiniLM in place of OpenAI (the notebook itself needs an OpenAI key and was not run).

**The result:**

```
the repo's example query (cell 19), top-5:   repo-style vs aligned: 0 of 5 chunks in common
8 answerable draft seeds, top-4:             repo-style Hit@4 0/8, CE@4 0/8      aligned 8/8, 8/8
alpha = 1.0 (dense only):                    the same 5 chunks for all 10 questions
"IPCC" (every split() BM25 score is 0):      the 5 chunks nearest to the empty string
```

**What this means.** The vector array is already sorted by the query, so after normalising it is just a ramp from 1 down to 0 by position. With all the weight on dense, the function returns the first five entries of the empty-string order, whatever you ask. The fix is to key every score by chunk id (§5 and §6 do).

**For your project:** do not port this function (06 v2.0 says the same). Write the test it never had: **with all the weight on dense, fusion must return the dense ranking**. That one assert fails on the repo's code immediately.

## 8. When not to use hybrid retrieval

The book lists when fusion is overkill (Ch12 p.12–13/14): queries that are all one type, a collection small enough that vector search alone retrieves reliably, and very tight latency budgets. Our measurements back the second case and add three more:

| Situation | What we saw | What to do |
|---|---|---|
| Dense already finds the evidence | Draft seeds: CE@4 8/8 for dense alone; fusion only improved ranks | Measure CE@k per category before adding a second index |
| Questions are paraphrases | D-006: BM25 and min-max fusion pushed the evidence from rank 1 to 2 | Check the `vocabulary-mismatch` bucket as a guard |
| The tokenizer does not fit the text | With the repo's `split()`, "IPCC" and "BECCS" match nothing (P3) | Test the tokenizer on your identifiers first |
| The two indexes hold different units | Document ids and chunk ids never match, so one side's votes are lost | Build both indexes over the same chunks (Ch12 p.5–6/14) |

**For your project:** v2.0's "when not to use" line (06 §4.2) names two of these: a question set with no exact-term needs, and a tokenizer that fails on the domain. Keep all four in mind when you write its summary.

## 9. What the book says, and what it leaves out

| Book | What it says (paraphrased) | Our check |
|---|---|---|
| Ch12 p.1–2/14 | Each search method has a blind spot the other covers | Confirmed on our chunks (§1) |
| Ch12 p.5–6/14 | Index the same chunks twice; query both in parallel | The same chunk ids are what make fusion possible (§7) |
| Ch12 p.7–8/14 | Scores are on different scales; normalise to 0–1 | Measured: raw sums follow BM25 (§3) |
| Ch12 p.8/14 | The three-sigma form is the more robust one | Not against an outlier, and it can leave 0–1 (§4) |
| Ch12 p.9/14 | After normalising, equal numbers mean equal strength | No: 1.0 only means "best in its own list"; D-009 has no answer, yet its best chunks get 1.0 |
| Ch12 p.9/14, p.11/14 | Weights such as 0.6/0.4; 50/50 to 70/30 | Starting points; one 0.1 step swapped two toy documents (§5) |
| whole book | (no mention of rank-based fusion) | RRF is the v2.0 primary arm; it is standard IR, not in this book |

## Check yourself

→ [`study/questions/R1_questions.md`](../questions/R1_questions.md): 3 cold questions before reading, 12 after, and 2 interview questions. Answer the next day, closed book.
