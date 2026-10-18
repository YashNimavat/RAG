# Qrels check

**What this is:** an automatic check of whether your relevance labels (qrels) can measure retrieval on your own chunks: format, reasons, versions, pool coverage, holes, ties.
**What this is not:** an evaluation of a retriever. The P@k and R@k below only show what the labels can and cannot carry.

**Recommendation: pool is biased: judge the listed holes (top-k chunks from every run that no one judged), then rerun** (section 7). Checklist: Q1 ✓ Q2 ✓ Q3 ✓ Q4 ? Q5 ✗ Q6 ✗ Q7 ✗ Q8 ✓ Q9 ✗ Q10 ? Q11 ? Q12 ?.

Settings: chunks: your chunks (--chunks) · k 4 · relevant = grade ≥ 1 · labels: JSONL, unlisted pairs unjudged · Hole@k limit 10% · simulated pool: keyword top 3 · dense `sentence-transformers/all-MiniLM-L6-v2` · pymupdf 1.26.7, numpy 2.5.3, sentence-transformers 6.1.0.
Runs: `keyword` = keyword overlap from the inverted index (distinct question tokens matched; ties: earlier chunk first); `dense` = dense `sentence-transformers/all-MiniLM-L6-v2` cosine over every chunk (ties: earlier chunk first).

## 1 Collection and index

Tokens: lowercase runs of `[a-z0-9]` (no stemming, no stop words), the same for chunks and questions.

| Measure | Value |
|---|---|
| Chunks | 10 |
| Tokens | 119 |
| Vocabulary (distinct terms) | 88 |
| Postings (term, chunk pairs) | 114 |
| Terms in exactly one chunk (df = 1) | 71 |
| Commonest terms (df) | `and` 6, `the` 5, `in` 4, `a` 2, `are` 2, `burning` 2, `carbon` 2, `cause` 2, `change` 2, `climate` 2 |
| Postings equal a full scan of the chunks | yes |

## 2 Questions vs the index

AND = chunks with every question token; OR = chunks with at least one (the keyword run's candidates); postings read = the sum of the question tokens' df.

| Question | Tokens | No postings | AND | OR | Postings read | Flag |
|---|---|---|---|---|---|---|
| q1 | main cause of climate change | - | 1 | 3 | 10 | - |
| q2 | why do sea levels rise | why do rise | 0 | 1 | 2 | - |
| q3 | renewable energy | renewable energy | 0 | 0 | 0 | **no candidate** |
| q4 | where does methane come from | where does come | 0 | 2 | 2 | - |
| q5 | is extreme heat becoming more common | extreme common | 0 | 3 | 5 | - |

## 3 Label audit

Labels: JSONL qrels, 13 listed pair(s); unlisted pairs are unjudged (TREC rule).

Judged pairs by grade: grade 0: 5, grade 1: 3, grade 2: 5.

| Question | Type | Answerable | Relevant chunks (full labels) | Created by | Need / question |
|---|---|---|---|---|---|
| q1 | - | yes | d01, d03, d09 | - | main cause of climate change |
| q2 | - | yes | d04, d05 | - | why do sea levels rise |
| q3 | - | yes | d07 | - | renewable energy |
| q4 | - | yes | d09 | - | where does methane come from |
| q5 | - | yes | d10 | - | is extreme heat becoming more common |

Five relevant pairs to re-read against the need (Q12; a fixed pseudo-random order):

| Question | Chunk | Chunk text (start) |
|---|---|---|
| q4 | d09 | Cattle and rice paddies release methane, a powerful greenhouse gas. … |
| q1 | d01 | Burning coal, oil and gas releases carbon dioxide, the main cause of recent global warming. … |
| q5 | d10 | Heat waves are becoming longer and more frequent in many regions. … |
| q3 | d07 | Solar panels and wind turbines generate electricity without burning fuel. … |
| q2 | d04 | Sea levels are rising because warmer ocean water expands and glaciers melt. … |

## 4 Pool and holes

**Simulated pool:** only the top 3 of `keyword` are judged, with grades taken from your full labels (unlisted = 0). Every check below uses these pooled labels; the *full* columns use all your labels.

Judged@4 and Hole@4 are out of 4 slots (empty slots, when a run returns fewer than 4, are neither). Pool depth = the largest d such that every question's top d in the run is judged. P@4 bounds: holes as not relevant → as relevant.

| Run | Judged@4 | Hole@4 | Empty | Pool depth | P@4 (holes 0) | P@4 (holes relevant) | R@4 | P@4 full | R@4 full |
|---|---|---|---|---|---|---|---|---|---|
| `keyword` | 0.450 | 0.000 | 0.550 | 4 | 0.433 | 0.433 | 1.000 (over 4) | 0.433 | 0.567 (over 5) |
| `dense` | 0.350 | 0.650 | 0.000 | 0 | 0.200 | 0.850 | 1.000 (over 4) | 0.350 | 0.933 (over 5) |

Means over the 5 answerable question(s); R@4 only over those with a relevant chunk under the labels in use.

Holes to judge (13: chunks in some run's top 4 that no one judged):

| Question | Chunk | In the top k of |
|---|---|---|
| q1 | d03 | `dense` |
| q1 | d04 | `dense` |
| q2 | d01 | `dense` |
| q2 | d02 | `dense` |
| q2 | d05 | `dense` |
| q3 | d01 | `dense` |
| q3 | d03 | `dense` |
| q3 | d07 | `dense` |
| q3 | d08 | `dense` |
| q4 | d01 | `dense` |
| q4 | d03 | `dense` |
| q5 | d01 | `dense` |
| q5 | d04 | `dense` |

Ties at the cut-off (the score at rank 4 equals the score at rank 5); rule: the earlier chunk first.

None.

## 5 Set vs ranking per question

Top 4 per run, marked **R** relevant, 0 judged not relevant, ? unjudged (a hole). P@4 = relevant ÷ returned; R@4 = relevant in the top 4 ÷ all relevant; first relevant rank and RR = 1 ÷ rank within the top 4.

| Question | Run | Top 4 | P@4 | R@4 | First relevant rank | RR |
|---|---|---|---|---|---|---|
| q1 | `keyword` | d02 0, d01 **R**, d08 0 | 0.333 | 1.000 | 2 | 0.500 |
| q1 | `dense` | d02 0, d01 **R**, d04 ?, d03 ? | 0.250 | 1.000 | 2 | 0.500 |
| q2 | `keyword` | d04 **R** | 1.000 | 1.000 | 1 | 1.000 |
| q2 | `dense` | d04 **R**, d05 ?, d02 ?, d01 ? | 0.250 | 1.000 | 1 | 1.000 |
| q3 | `keyword` | (nothing) | 0.000 | - | - | - |
| q3 | `dense` | d07 ?, d01 ?, d03 ?, d08 ? | 0.000 | - | - | - |
| q4 | `keyword` | d06 0, d09 **R** | 0.500 | 1.000 | 2 | 0.500 |
| q4 | `dense` | d09 **R**, d01 ?, d06 0, d03 ? | 0.250 | 1.000 | 1 | 1.000 |
| q5 | `keyword` | d10 **R**, d02 0, d03 0 | 0.333 | 1.000 | 1 | 1.000 |
| q5 | `dense` | d10 **R**, d02 0, d01 ?, d04 ? | 0.250 | 1.000 | 1 | 1.000 |

## 6 Checklist

✓ = no problem found · ✗ = a problem found on your data · ? = check by hand (the evidence and *how to check* help).

| # | Check | Verdict | Evidence | How to check |
|---|---|---|---|---|
| Q1 | Every question has at least one label, and answerable vs unanswerable is explicit | ✓ | 5 questions: 5 with at least one relevant chunk, 0 marked "answerable": false. | Give every question at least one label; mark a question with no relevant chunk "answerable": false, so 'no answer' is a decision, not a gap. Every label must point at an existing chunk, once. |
| Q2 | Every non-zero label (and each tempting zero) has a reason of more than 3 words | ✓ | all 13 listed labels (non-zero and listed zeros) have a reason of more than 3 words. | Write `why` in your own words (more than 3 words): what in the chunk meets the need, or why a look-alike does not. With spans, the group's `fact` is the reason; an unanswerable item needs a `notes` line. |
| Q3 | The guideline version is recorded on every label | ✓ | every label has one: v1. | Put `guideline_version` on every label (or --guideline-version for a TREC file); bump it whenever a guideline sentence changes. |
| Q4 | Labels were written before any run was seen | ? | no label timestamps. Check by hand: did you label before looking at any ranked list? (This tool's own runs are built when the report is made.) | Record `ts` when you label and keep each run file's time; label from the need and the chunks, before you open any ranked list. |
| Q5 | The pool covers more than one retriever (keyword and dense) | ✗ | pool depth (every question's top d judged): `keyword` 4, `dense` 0. Only `keyword` reached the pool (simulated: --pool-from keyword:3). | Pool the top k (10 is common) of both the keyword run and the dense run, judge the union, rerun. --pool-from keyword:3 shows what a one-retriever pool hides. |
| Q6 | Hole@k for each run is below the limit (10%) | ✗ | Hole@4: `keyword` 0.0%, `dense` 65.0%; over the limit: `dense`. 13 hole(s) to judge (section 4). | Hole@k = unjudged chunks in a run's top k ÷ k. Judge the holes listed in section 4, then rerun. |
| Q7 | No two runs swap order when holes count as relevant instead of not relevant | ✗ | `keyword` vs `dense`: P@4 0.433 vs 0.200 with holes as 0, 0.433 vs 0.850 with holes as relevant. | Compute each run's P@k twice: holes as not relevant (lower bound) and holes as relevant (upper bound). If two runs swap order, the unjudged chunks decide the winner. |
| Q8 | Ties at the cut-off k are reported, and the tie rule is stated | ✓ | no tie straddles rank 4 in any run (ties: the earlier chunk first (document order) for the keyword and dense runs; your own run files keep their file order). | Compare the score at rank k with the score at rank k + 1. State the tie rule, and say whether another order would change P@k. |
| Q9 | Questions with no keyword candidate, and questions whose OR set covers most of the collection, are listed | ✗ | no keyword candidate (no question token has postings): q3; answerable among them: q3. Keyword search can never find the answerable ones. | Look up each question token's postings: no postings at all = vocabulary mismatch (keyword search can never find it); an OR set over half the chunks = common words dominate. |
| Q10 | Self-agreement on a blind re-label of ≥ 10 items: raw agreement and κ | ? | no --relabel file. After 7 days or more, re-label at least 10 items with the old labels hidden. | After 7 days or more, re-label at least 10 items with the old labels hidden (--relabel); raw agreement ≥ 0.90 (06 §6.5) and κ ≥ 0.67. |
| Q11 | Labels are spans or derived from spans, not chunk ids of one chunker | ? | JSONL labels on your own chunk ids: fine for fixed documents, void if the ids come from a chunker you may change. | Label evidence spans (06 evidence_groups) and let the tool derive chunk labels with any_overlap; chunk-id labels are void as soon as you re-chunk. |
| Q12 | A sample of relevant labels is re-read against the need, not the words (one ambiguous question checked) | ? | manual: re-read q4 d09, q1 d01, q5 d10, q3 d07, q2 d04 (section 3). | Re-read the 5 pairs listed in section 3: does the chunk help answer the need, or does it only share words? Then check one ambiguous question in full. |

## 7 Recommendation

**pool is biased: judge the listed holes (top-k chunks from every run that no one judged), then rerun** (rule: Q5 or Q6 failed; first match wins)

- Q5: pool depth (every question's top d judged): `keyword` 4, `dense` 0. Only `keyword` reached the pool (simulated: --pool-from keyword:3).
- Q6: Hole@4: `keyword` 0.0%, `dense` 65.0%; over the limit: `dense`. 13 hole(s) to judge (section 4).
- 13 hole(s) listed in section 4.

Order of the rules: Q1/Q2/Q3/Q11 label format → Q5/Q6 pool and holes → Q7 bounds → Q10 self-agreement → fit for metrics.
