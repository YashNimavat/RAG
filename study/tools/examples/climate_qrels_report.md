# Qrels check

**What this is:** an automatic check of whether your relevance labels (qrels) can measure retrieval on your own chunks: format, reasons, versions, pool coverage, holes, ties.
**What this is not:** an evaluation of a retriever. The P@k and R@k below only show what the labels can and cannot carry.

**Recommendation: labels not ready: fix the format and guideline first** (section 7). Checklist: Q1 ✓ Q2 ✓ Q3 ✗ Q4 ? Q5 ✓ Q6 ✓ Q7 ✓ Q8 ✗ Q9 ? Q10 ? Q11 ✓ Q12 ?.

> **Draft labels:** 10 of 10 questions are `created_by: llm-draft` (06 §6.7). This report illustrates the tool; it says nothing about retriever quality.

Settings: chunks: 1000-character windows, overlap 200 (step 800), pages joined with "\n" · k 4 · relevant = grade ≥ 1 · labels: spans · Hole@k limit 10% · dense `sentence-transformers/all-MiniLM-L6-v2` · pymupdf 1.26.7, numpy 2.5.3, sentence-transformers 6.1.0.
Documents: `Understanding_Climate_Change.pdf` as `climate` (33 page(s), 72,593 characters).
Runs: `keyword` = keyword overlap from the inverted index (distinct question tokens matched; ties: earlier chunk first); `dense` = dense `sentence-transformers/all-MiniLM-L6-v2` cosine over every chunk (ties: earlier chunk first).

## 1 Collection and index

Tokens: lowercase runs of `[a-z0-9]` (no stemming, no stop words), the same for chunks and questions.

| Measure | Value |
|---|---|
| Chunks | 91 |
| Tokens | 11,807 |
| Vocabulary (distinct terms) | 1,868 |
| Postings (term, chunk pairs) | 8,107 |
| Terms in exactly one chunk (df = 1) | 745 |
| Commonest terms (df) | `and` 91, `to` 87, `for` 80, `the` 80, `climate` 77, `in` 76, `of` 74, `are` 67, `can` 65, `is` 65 |
| Postings equal a full scan of the chunks | yes |

## 2 Questions vs the index

AND = chunks with every question token; OR = chunks with at least one (the keyword run's candidates); postings read = the sum of the question tokens' df.

| Question | Tokens | No postings | AND | OR | Postings read | Flag |
|---|---|---|---|---|---|---|
| D-001 | according to the document by how much have global temperatures risen since late 19th century | according document | 0 | 91 | 265 | OR > half |
| D-002 | in what year was the paris agreement adopted | what year | 0 | 87 | 172 | OR > half |
| D-003 | according to the document what is essential regarding countries nationally determined contributions ndcs for meeting paris agreement s goals | according document what regarding | 0 | 91 | 432 | OR > half |
| D-004 | what does dac stand for and it do | what does stand do | 0 | 91 | 187 | OR > half |
| D-005 | how does the document contrast coal and natural gas in terms of carbon intensity | does document contrast terms intensity | 0 | 91 | 375 | OR > half |
| D-006 | what are the advantages of putting solar panels on lakes or reservoirs | what advantages putting | 0 | 90 | 271 | OR > half |
| D-007 | what is the supreme decision making body of convention that provides framework for negotiating kyoto protocol and paris agreement | what | 0 | 91 | 479 | OR > half |
| D-008 | what does the kigali amendment target | what does target | 0 | 80 | 82 | OR > half |
| D-009 | in what year was the ipcc established | what year established | 0 | 87 | 158 | OR > half |
| D-010 | what share of global greenhouse gas emissions comes from aviation | what share aviation | 0 | 86 | 192 | OR > half |

## 3 Label audit

Labels: evidence spans (06 `evidence_groups`), converted to chunk labels with `any_overlap`: a chunk is relevant if it overlaps at least one non-whitespace character of a segment (document offsets: page start + char offset). Every chunk gets a label (0 = no overlap), so every pair is judged.

Judged pairs by grade: grade 0: 895, grade 1: 15.

| Question | Type | Answerable | Relevant chunks (full labels) | Created by | Need / question |
|---|---|---|---|---|---|
| D-001 | exact-term | yes | climate#7 | llm-draft | According to the document, by how much have global temperatures risen since the late 19th century? |
| D-002 | factual-single-span | yes | climate#25, climate#26 | llm-draft | In what year was the Paris Agreement adopted? |
| D-003 | factual-single-span | yes | climate#63, climate#64 | llm-draft | According to the document, what is essential regarding countries' nationally determined contributions (NDCs) for meeting the Paris Agreement's goals? |
| D-004 | exact-term | yes | climate#22, climate#63 | llm-draft | What does DAC stand for, and what does it do? |
| D-005 | multi-span | yes | climate#2, climate#3, climate#4 | llm-draft | How does the document contrast coal and natural gas in terms of carbon intensity? |
| D-006 | vocabulary-mismatch | yes | climate#20 | llm-draft | What are the advantages of putting solar panels on lakes or reservoirs? |
| D-007 | multi-hop | yes | climate#25, climate#26, climate#79 | llm-draft | What is the supreme decision-making body of the convention that provides the framework for negotiating the Kyoto Protocol and the Paris Agreement? |
| D-008 | exact-term | yes | climate#64 | llm-draft | What does the Kigali Amendment target? |
| D-009 | unanswerable | no | - | llm-draft | In what year was the IPCC established? |
| D-010 | unanswerable | no | - | llm-draft | What share of global greenhouse gas emissions comes from aviation? |

Span → chunk conversion, per evidence group and alternative (groups are AND, alternatives OR):

| Question | Group / alternative | Page | Chunks it overlaps |
|---|---|---|---|
| D-001 | g1/g1a | 3 | climate#7 |
| D-002 | g1/g1a | 10 | climate#25, climate#26 |
| D-003 | g1/g1a | 23 | climate#63, climate#64 |
| D-004 | g1/g1a | 8 | climate#22 |
| D-004 | g1/g1b | 23 | climate#63 |
| D-005 | g1/g1a | 2 | climate#2, climate#3 |
| D-005 | g2/g2a | 2 | climate#3, climate#4 |
| D-006 | g1/g1a | 8 | climate#20 |
| D-006 | g2/g2a | 8 | climate#20 |
| D-007 | g1/g1a | 10 | climate#25, climate#26 |
| D-007 | g2/g2a | 29 | climate#79 |
| D-008 | g1/g1a | 24 | climate#64 |

Five relevant pairs to re-read against the need (Q12; a fixed pseudo-random order):

| Question | Chunk | Chunk text (start) |
|---|---|---|
| D-005 | climate#3 | to rise today. Coal Coal is the most carbon-intensive fossil fuel, and its use for electricity generation is a major source of CO2 emissions. Despite a decline  … |
| D-006 | climate#20 | Advanced Renewable Energy Solutions Next-Generation Solar Technologies New advancements in solar technology, such as perovskite solar cells and solar paint, pro … |
| D-002 | climate#26 | iating specific protocols and agreements, such as the Kyoto Protocol and the Paris Agreement. Global cooperation under the UNFCCC is crucial for coordinated cli … |
| D-003 | climate#64 | e to 1.5 degrees Celsius. Countries submit nationally determined contributions (NDCs) outlining their climate action plans. Regular reviews and updates of NDCs  … |
| D-002 | climate#25 | Agroforestry Agroforestry integrates trees and shrubs into agricultural landscapes. This practice enhances biodiversity, improves soil health, and sequesters ca … |

## 4 Pool and holes

Judged@4 and Hole@4 are out of 4 slots (empty slots, when a run returns fewer than 4, are neither). Pool depth = the largest d such that every question's top d in the run is judged. P@4 bounds: holes as not relevant → as relevant.

| Run | Judged@4 | Hole@4 | Empty | Pool depth | P@4 (holes 0) | P@4 (holes relevant) | R@4 |
|---|---|---|---|---|---|---|---|
| `keyword` | 1.000 | 0.000 | 0.000 | 4 | 0.344 | 0.344 | 0.688 (over 8) |
| `dense` | 1.000 | 0.000 | 0.000 | 4 | 0.406 | 0.406 | 0.896 (over 8) |

Means over the 8 answerable question(s); R@4 only over those with a relevant chunk under the labels in use.

No holes: every chunk in every run's top 4 is judged.

Zero-labelled chunks that every run puts in its top 4 (14). A missed place that answers would be a hidden hole, so re-read a few:

D-001 climate#0, D-001 climate#1, D-001 climate#8, D-002 climate#16, D-002 climate#64, D-003 climate#26, D-005 climate#5, D-006 climate#12, D-006 climate#13, D-006 climate#60, D-007 climate#16, D-009 climate#64, D-010 climate#2, D-010 climate#5

Ties at the cut-off (the score at rank 4 equals the score at rank 5); rule: the earlier chunk first.

| Run | Question | Score | Tied chunks | Kept (inside the top k) | Changes P@k under another order |
|---|---|---|---|---|---|
| `keyword` | D-001 | 5 | 4 | climate#0, climate#1 | no |
| `keyword` | D-002 | 4 | 4 | climate#16, climate#17 | no |
| `keyword` | D-003 | 7 | 7 | climate#6 | no |
| `keyword` | D-004 | 3 | 12 | climate#2, climate#3, climate#12, climate#13 | **yes** |
| `keyword` | D-005 | 6 | 3 | climate#5 | no |
| `keyword` | D-007 | 8 | 5 | climate#26 | **yes** |
| `keyword` | D-008 | 1 | 79 | climate#0, climate#1, climate#2 | no |
| `keyword` | D-009 | 2 | 67 | climate#0, climate#2 | no |
| `keyword` | D-010 | 5 | 4 | climate#2, climate#3 | no |

## 5 Set vs ranking per question

Top 4 per run, marked **R** relevant, 0 judged not relevant, ? unjudged (a hole). P@4 = relevant ÷ returned; R@4 = relevant in the top 4 ÷ all relevant; first relevant rank and RR = 1 ÷ rank within the top 4.

| Question | Run | Top 4 | P@4 | R@4 | First relevant rank | RR |
|---|---|---|---|---|---|---|
| D-001 | `keyword` | climate#7 **R**, climate#8 0, climate#0 0, climate#1 0 | 0.250 | 1.000 | 1 | 1.000 |
| D-001 | `dense` | climate#1 0, climate#0 0, climate#8 0, climate#7 **R** | 0.250 | 1.000 | 4 | 0.250 |
| D-002 | `keyword` | climate#26 **R**, climate#64 0, climate#16 0, climate#17 0 | 0.250 | 0.500 | 1 | 1.000 |
| D-002 | `dense` | climate#64 0, climate#26 **R**, climate#16 0, climate#63 0 | 0.250 | 0.500 | 2 | 0.500 |
| D-003 | `keyword` | climate#64 **R**, climate#63 **R**, climate#26 0, climate#6 0 | 0.500 | 1.000 | 1 | 1.000 |
| D-003 | `dense` | climate#26 0, climate#64 **R**, climate#63 **R**, climate#16 0 | 0.500 | 1.000 | 2 | 0.500 |
| D-004 | `keyword` | climate#2 0, climate#3 0, climate#12 0, climate#13 0 | 0.000 | 0.000 | - | - |
| D-004 | `dense` | climate#63 **R**, climate#22 **R**, climate#79 0, climate#25 0 | 0.500 | 1.000 | 1 | 1.000 |
| D-005 | `keyword` | climate#2 **R**, climate#3 **R**, climate#4 **R**, climate#5 0 | 0.750 | 1.000 | 1 | 1.000 |
| D-005 | `dense` | climate#3 **R**, climate#2 **R**, climate#4 **R**, climate#5 0 | 0.750 | 1.000 | 1 | 1.000 |
| D-006 | `keyword` | climate#12 0, climate#13 0, climate#59 0, climate#60 0 | 0.000 | 0.000 | - | - |
| D-006 | `dense` | climate#20 **R**, climate#13 0, climate#12 0, climate#60 0 | 0.250 | 1.000 | 1 | 1.000 |
| D-007 | `keyword` | climate#25 **R**, climate#79 **R**, climate#16 0, climate#26 **R** | 0.750 | 1.000 | 1 | 1.000 |
| D-007 | `dense` | climate#64 0, climate#79 **R**, climate#26 **R**, climate#16 0 | 0.500 | 0.667 | 2 | 0.500 |
| D-008 | `keyword` | climate#64 **R**, climate#0 0, climate#1 0, climate#2 0 | 0.250 | 1.000 | 1 | 1.000 |
| D-008 | `dense` | climate#78 0, climate#64 **R**, climate#54 0, climate#77 0 | 0.250 | 1.000 | 2 | 0.500 |
| D-009 | `keyword` | climate#1 0, climate#64 0, climate#0 0, climate#2 0 | 0.000 | - | - | - |
| D-009 | `dense` | climate#79 0, climate#64 0, climate#32 0, climate#25 0 | 0.000 | - | - | - |
| D-010 | `keyword` | climate#4 0, climate#5 0, climate#2 0, climate#3 0 | 0.000 | - | - | - |
| D-010 | `dense` | climate#2 0, climate#1 0, climate#63 0, climate#5 0 | 0.000 | - | - | - |

## 6 Checklist

✓ = no problem found · ✗ = a problem found on your data · ? = check by hand (the evidence and *how to check* help).

| # | Check | Verdict | Evidence | How to check |
|---|---|---|---|---|
| Q1 | Every question has at least one label, and answerable vs unanswerable is explicit | ✓ | 10 questions: 8 with at least one relevant chunk, 2 marked "answerable": false. | Give every question at least one label; mark a question with no relevant chunk "answerable": false, so 'no answer' is a decision, not a gap. Every label must point at an existing chunk, once. |
| Q2 | Every non-zero label (and each tempting zero) has a reason of more than 3 words | ✓ | every evidence group has a `fact` (the reason each derived label carries), and every unanswerable item a note. | Write `why` in your own words (more than 3 words): what in the chunk meets the need, or why a look-alike does not. With spans, the group's `fact` is the reason; an unanswerable item needs a `notes` line. |
| Q3 | The guideline version is recorded on every label | ✗ | 10 of 10 span items have no guideline version (the 06 span form has no per-item `guideline_version`; add one, or pass --guideline-version). | Put `guideline_version` on every label (or --guideline-version for a TREC file); bump it whenever a guideline sentence changes. |
| Q4 | Labels were written before any run was seen | ? | no label timestamps. Check by hand: did you label before looking at any ranked list? (This tool's own runs are built when the report is made.) | Record `ts` when you label and keep each run file's time; label from the need and the chunks, before you open any ranked list. |
| Q5 | The pool covers more than one retriever (keyword and dense) | ✓ | pool depth (every question's top d judged): `keyword` 4, `dense` 4. Span labels judge every chunk (no overlap = 0), which holds only if your spans list every place that answers; section 4 lists zero-labelled chunks that every run ranks in its top k. | Pool the top k (10 is common) of both the keyword run and the dense run, judge the union, rerun. --pool-from keyword:3 shows what a one-retriever pool hides. |
| Q6 | Hole@k for each run is below the limit (10%) | ✓ | Hole@4: `keyword` 0.0%, `dense` 0.0%. | Hole@k = unjudged chunks in a run's top k ÷ k. Judge the holes listed in section 4, then rerun. |
| Q7 | No two runs swap order when holes count as relevant instead of not relevant | ✓ | mean P@4 (holes as 0 → as relevant): `keyword` 0.344 → 0.344, `dense` 0.406 → 0.406; no pair swaps. | Compute each run's P@k twice: holes as not relevant (lower bound) and holes as relevant (upper bound). If two runs swap order, the unjudged chunks decide the winner. |
| Q8 | Ties at the cut-off k are reported, and the tie rule is stated | ✗ | 9 tie(s) straddle rank 4: `keyword` D-001 (4 chunks at score 5), `keyword` D-002 (4 chunks at score 4), `keyword` D-003 (7 chunks at score 7), `keyword` D-004 (12 chunks at score 3), `keyword` D-005 (3 chunks at score 6), `keyword` D-007 (5 chunks at score 8) … (+3). 2 of them mix relevant and not-relevant chunks, so another tie order would change P@4: `keyword` D-004, `keyword` D-007. Rule: ties: the earlier chunk first (document order) for the keyword and dense runs; your own run files keep their file order. | Compare the score at rank k with the score at rank k + 1. State the tie rule, and say whether another order would change P@k. |
| Q9 | Questions with no keyword candidate, and questions whose OR set covers most of the collection, are listed | ? | OR set over half of the 91 chunks: D-001 (91), D-002 (87), D-003 (91), D-004 (91), D-005 (91), D-006 (90) … (+4). Common words decide those OR sets: rank, do not filter, and check that keyword scores still separate chunks. | Look up each question token's postings: no postings at all = vocabulary mismatch (keyword search can never find it); an OR set over half the chunks = common words dominate. |
| Q10 | Self-agreement on a blind re-label of ≥ 10 items: raw agreement and κ | ? | no --relabel file. After 7 days or more, re-label at least 10 items with the old labels hidden. | After 7 days or more, re-label at least 10 items with the old labels hidden (--relabel); raw agreement ≥ 0.90 (06 §6.5) and κ ≥ 0.67. |
| Q11 | Labels are spans or derived from spans, not chunk ids of one chunker | ✓ | span labels, converted with any_overlap to the 91 chunks here; re-chunking re-derives them. | Label evidence spans (06 evidence_groups) and let the tool derive chunk labels with any_overlap; chunk-id labels are void as soon as you re-chunk. |
| Q12 | A sample of relevant labels is re-read against the need, not the words (one ambiguous question checked) | ? | manual: re-read D-005 climate#3, D-006 climate#20, D-002 climate#26, D-003 climate#64, D-002 climate#25 (section 3). | Re-read the 5 pairs listed in section 3: does the chunk help answer the need, or does it only share words? Then check one ambiguous question in full. |

## 7 Recommendation

**labels not ready: fix the format and guideline first** (rule: Q1 or Q2 or Q3 or Q11 failed; first match wins)

- Q3: 10 of 10 span items have no guideline version (the 06 span form has no per-item `guideline_version`; add one, or pass --guideline-version).
- 10 of 10 questions are `created_by: llm-draft` (06 §6.7): not human labels; keep them out of scored runs until you verify them.

Order of the rules: Q1/Q2/Q3/Q11 label format → Q5/Q6 pool and holes → Q7 bounds → Q10 self-agreement → fit for metrics.
