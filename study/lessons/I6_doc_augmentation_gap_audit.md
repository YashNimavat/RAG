# I6 gap audit: how the lesson's contents were chosen

**What this is:** the check run before and while writing the I6 lesson, so you can judge the method. Every idea the lesson needs had to be found and taught; none of it was optional.
**What this is not:** the lesson itself. That is [I6_doc_augmentation.html](I6_doc_augmentation.html) (open it from the study kit: I6 → step 1). The research behind it is `study/research/phase_04_indexing.md`, "Concept I6"; the measured facts are `sources/verification/I6/I6_FACTS.md`; the contract shared by the lesson, notebook, tool and quiz is `sources/verification/I6/I6_BUILD_SPEC.md`.

## The method, in five steps

1. **Collect every idea the topic uses.** Sources: the research file's 26-row gap table and its lesson blueprint; the two upstream notebooks and their runnable scripts (every cited cell re-opened and checked by `i6_sources.py`, 48 checks); the LangChain and LlamaIndex source lines; AIQ 04 Q45; the course files it names (02 I6 card, 03, 04 DV-25, 06 §6.3 and §6.7, 08 D-09/D-10, P4 D.8, C3, the misconception log). The book was **not available** in the build container, so its Ch11 pages come from 04 and are marked "not re-opened".
2. **For each idea, ask two questions.** Is it taught *before* it is used? Which concept owns it? `concept_tracker.csv` lists every Phase 4 concept, and P4, C3, C4, M2, M4 and R1, as not studied, so their ideas count as not yet learned and get a bridge where I6 needs them.
3. **Classify each idea.**
   - **Core:** I6's own idea; taught in full.
   - **Bridge:** needed here, owned elsewhere; taught briefly, where it is needed.
   - **Next topic:** only a link.
4. **Check the quiz.** Every key point of every question must be answerable from the lesson's **Short** mode and from the short reading file, because the quiz is the same for both depths.
5. **Check the facts.** Every number is matched against `out_i6_kit_measure.txt` (K1–K12) or labelled external, toy or formula; the copyright and number checks run in `i6_md_check.py`.

## What step 2 found: the research's 26 ideas, and where each is now taught

| # | Idea | Class | Now in the lesson |
|---|---|---|---|
| 1 | Shape asymmetry: a question and its answer passage embed apart | bridge (P4 D.8) | step 1: D-002's chunk at rank 3 (0.4606) vs a generated question at 0.9869; 0.886 of questions sit nearer a sibling question than their own chunk; the shape-gap chart (Short) |
| 2 | One query vector, one score per stored vector, sort (no matrix) | bridge (P4/C4; MC-002) | step 1, first paragraph (Short) |
| 3 | Index time vs query time | bridge, critical (MC-003) | step 2: the two-lane diagram and the MC-003 check question (Short) |
| 4 | The parent is the C3 chunk record | bridge (C3) | step 5: the `vectors → (kind, parent_id, question)` table (Short) |
| 5 | Per-chunk generation: prompt, n, JSON list | core | step 3: the prompt file, chunk 21's 10 questions, the n slider (Short) |
| 6 | Structured output and validation | bridge (M3) | step 3: schema, parse, retry once; never split on newlines (Short) |
| 7 | Cleaning rules and the "too vague" filter | core | step 4: rule counts, including a false positive (Short) |
| 8 | Hallucinated or unanswerable questions; filtering (Doc2Query--) | core | step 4: the own-chunk test (58 of 970 outside the top 10), the bottom-30% cut as an arm, not a default (Short); Doc2Query-- itself (Full) |
| 9 | The multi-vector index | core | step 5 (Short); LangChain's `id_key` (Full) |
| 10 | Three designs, including the appended one the course files missed | core | step 5: diagram and table (Short) |
| 11 | Parent score (max / sum / mean / RRF) and oversampling | core (RRF: bridge to R1) | step 6: toy toggle, MRR 0.760 for sum vs 0.781 for max (Short); RRF (Full) |
| 12 | Duplicate parents; dedup before the cut; `set()` loses order | core | step 6: the D-006 trace toggle; 3.00 unique parents in the top 4 vectors at n = 5 (Short) |
| 13 | How many questions; the prefix trick | core | step 3 (prefix) and step 7 (the n curve: n = 1 is worse than none) (Short) |
| 14 | Size and cost multipliers | core | step 5 (size calculator) and step 10 (cost table) (Short) |
| 15 | Which `input_type` for stored questions | core, open variable | Full (frameworks); not measurable with MiniLM |
| 16 | CE@k on the parent span; the question is never evidence | bridge (M2) | step 7 (Short) |
| 17 | Equal token budget | bridge (I1) | step 10: 627.9 vs 671.0 context tokens (Short) |
| 18 | **Leakage between generated questions and eval questions** | core, critical | step 9: the K9 table, the τ slider, the de-leaked arm (0.547), D-009's jump (Short) |
| 19 | Paired bootstrap, dev selection, power | bridge (M4) | step 12: the decision rule, "inconclusive" as a normal result (Short) |
| 20 | HyDE as the mirror image; the break-even | core (HyDE: next, Q2) | step 2 and step 10: the calls-per-month chart with sliders (Short) |
| 21 | The upstream parent (4,000 regex words, no punctuation) | core | step 11: measured, 3 parents, 42.5% each, 4,271 tokens (Short) |
| 22 | Keyword and number queries | core | step 8: rare-token retention 0.264 at n = 5 (Short) |
| 23 | Rebuild keys: a changed chunk regenerates only its questions | bridge (C3/D3) | step 3 and step 10 (Short) |
| 24 | Generated questions must be cached and replayed | bridge (LLMOps) | step 3 (Short); the LLMOps section |
| 25 | Questions into BM25 (the original doc2query) | next (R1) | step 8, one paragraph (Short) |
| 26 | Context cost of big parents | core | step 11: the parent-size bars, 6.4× (Short) |

## What changed from the research blueprint, and why

- **The questions are a stand-in pack.** The blueprint assumed a recorded Groq/Haiku replay pack. None exists (`study/llmops/` is not built), so four Claude helpers wrote 970 questions from the prompt file, one chunk at a time, **without seeing the eval set**. Every question-dependent number is labelled as measured on this pack.
- **D-006 is not the failure.** With MiniLM on v0's 97 chunks D-006 is already rank 1 (P4 K4). The visible effect sits on D-001, D-002, D-008 and the paraphrase D-002-P1; D-006 is kept for the trace (step 6).
- **The leakage result became the centre of the lesson.** Blind generation still produced near-copies of four seeds (cos 0.93–0.99), and deleting the 10 questions within τ drops MRR@10 below v0. The blueprint treated leakage as a risk to check; here it decided the verdict ("inconclusive: possible leakage").
- **The cross-encoder filter is replaced by a bi-encoder stand-in.** The model was not available in the build container; the own-chunk test uses MiniLM. The notebook runs the cross-encoder when it is in your cache.
- **τ is provisional.** 06 has one paraphrase pair (0.7054), not the ≥ 10 the rule needs.
- **The cost table is measured, not estimated.** Real prompt and output token counts replaced the research's assumptions (I6-E11).

## What step 4 found: the quiz against the lesson

The 17 questions of the build spec (§4) were written after the lesson's step list was fixed, each with its teaching step. `i6_md_check.py` checks that every reread line points at a reading section and a lesson step that exist, and that every number in the files is a measured or derived one.

| Question | Taught in (lesson step) |
|---|---|
| I6-PRE-01 | 1 |
| I6-PRE-02 | 2 |
| I6-R-01 | 5, 6, 7 |
| I6-R-02 | 5, 8 |
| I6-R-03 | 6 |
| I6-R-04 | 2, 10 |
| I6-R-05 (review) | 7 |
| I6-R-06 (interview, AIQ 04 Q45) | 4, 9 |
| I6-A-01 | 5, 10 |
| I6-A-02 | 6 |
| I6-A-03 | 10 |
| I6-A-04 | 6 |
| I6-A-05 | 9 |
| I6-A-06 (review) | 8 |
| I6-T-01 | 9, 12 |
| I6-T-02 | 5, 8 |
| I6-T-03 (review) | 10 |

## Left to other concepts on purpose (link only)

- **HyDE's mechanism and its run:** Q2 (v3.1), which will reuse this lesson's leakage guard and decisive slice.
- **RRF and hybrid search, including questions in BM25 text:** R1.
- **Bootstrap intervals and dev/test discipline:** M4.
- **Removing duplicate parents in the context builder:** X3.
- **Comparing I6 with the other granularity choices:** I-CMP.

## Errors found (recorded, not edited)

- **I6-E10:** the research says HyPE cell 19's saved output shows 2 contexts for k = 3; it shows 3 distinct contexts.
- **I6-E11:** the research's cost table assumed 350 input and 250 visible output tokens at n = 10; measured medians are 403 and 111.
- **I6-E12:** the research used D-006 as the visible failure; with MiniLM it is already rank 1.
- **I6-E13:** the research's second-choice interview item "AIQ 04 Q5 (parent_id)" is about chunk size at e080df2.
- The research's DERIVED upstream numbers (I6-E1) are now measured: 3 parents, 42.5% each, 87 fragments, 4,271 tokens.

These are in `I6_FACTS.md` §4 for a later correction pass of the research file.
