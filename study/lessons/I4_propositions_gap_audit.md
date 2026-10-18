# I4 gap audit: how the lesson's contents were chosen

**What this is:** the check run before and while writing the I4 lesson, so you can judge the method. Every idea the lesson needs had to be found and taught; none of it was optional.
**What this is not:** the lesson itself. That is [I4_propositions.html](I4_propositions.html) (open it from the study kit: I4 → step 1). The research behind it is `study/research/phase_04_indexing.md`, "Concept I4"; the measured numbers are in `sources/verification/I4/I4_FACTS.md`.

## The method, in five steps

1. **Collect every idea the topic uses.** Sources: the research file's I4 gap table (22 ideas) and blueprint, the repo notebook `proposition_chunking.ipynb` at `009adba` (read cell by cell as data), the course files it cites (06 §2.3 chunk contract, 06 §6.7 draft seeds, 06 v1.4, LLMOPS_FOUNDATION §6.2 prices and limits), and the external sources the research opened (Dense X README, LangChain template, `MultiVectorRetriever`, FActScore).
2. **For each idea, ask two questions.** Is it taught *before* it is used? Which concept owns it (I4, I1, I5, M2, M3, M4, P1, P6)? Your progress file says I4 is `not_started` and so are I1–I3 and M1–M5, so their ideas count as not yet learned.
3. **Classify each idea.**
   - **Core:** I4's own idea; taught in full.
   - **Bridge:** needed here, but owned elsewhere; taught briefly, in the place it is needed.
   - **Next topic:** only a link.
4. **Check the quiz.** Every key point of every question must be taught in the lesson, in **Short** mode too, because the quiz is the same for both depths.
5. **Check the facts.**
   - Every measured number is matched against `out_i4_kit_measure.txt` (K1–K12); assumed and external numbers carry their label on the page.
   - The book was **not** available in this session, so its pages are cited from the course's page notes and marked as not re-opened (step 15 of the lesson). No book text was read, so none can have been copied.

## What step 1 had to work with

I4 had **no** earlier lesson, lab, facts file or question file. Everything below is new. Two things the research planned do not exist yet, and the lesson says so at the top:
- **No LLM-written propositions.** They need recorded Groq calls through the course's `study/llmops/` cache, which is not built. The lesson uses **40 propositions the tutor wrote by hand** from the PyMuPDF text (pages 2, 10, 23, 29) and **six planted mistakes**, both stored in `sources/verification/I4/`.
- **No embedding rankings.** Every ranked list in the lesson is a made-up order, labelled so. The verify notebook adds a MiniLM ranking as an observation when the model is in your local cache.

## What step 2 found: the 22 ideas of the research table, and where each is taught

| # | Idea | Class | Taught in (Short unless marked) |
|---|---|---|---|
| 1 | A proposition: the five rules; Dense X's distinct, minimal, self-contained | core | step 2, with 10:7 split into three |
| 2 | Dilution: one vector for many facts | bridge (I1) | step 1: chunk 27 and the 1/√n toy with a slider |
| 3 | Decontextualisation | core | step 3: three real pronoun cases (10:4, 29:14, 2:2); the `resolved` check |
| 4 | Structured output: schema, validation, logged failures | bridge (M3) | step 5; the framework's forced tool call in Full |
| 5 | Source anchoring with sentence ids | core | steps 4 and 6: units with offsets; span(p); parents |
| 6 | Scoring rewritten units against span gold | core | step 9: arms (a), (b), (c) and the text check |
| 7 | Multi-vector retrieval: k children → ≤ k parents | core | step 9, with the repo's cells 20 and 32 |
| 8 | The quality grade is a filter (D-10), the 7 is uncalibrated (MC-006) | core | step 8: keep-good and catch-bad |
| 9 | Per-proposition against batched grading cost | core | steps 8 and 11: 1,433 against 66 calls |
| 10 | Faithfulness by hand, with an interval | core | step 7: supported / added / distorted; Wilson calculator |
| 11 | Coverage ceilings | core | step 10: sentence_coverage, gold_reachability |
| 12 | Near-duplicates crowd the top k | core | step 10: distinct-facts@4 = 3 on D-002; the repo's cells 28 and 36 |
| 13 | Atomicity loses relations | core | step 10: D-005 and D-007, arm (a) against arm (b) |
| 14 | Index size and cost multiplier | core | step 11: ×14.4 vectors; cost per 1k chunks |
| 15 | Reasoning tokens count as output; `finish_reason = length` | bridge (P1) | step 5 |
| 16 | Few-shot examples and the 8-gram leakage test | core | steps 5 and 12: a fresh example; clean 0, injected 10 |
| 17 | Fair comparison: fixed k and equal budget; the degenerate baseline | bridge (I1, M4) | steps 9 and 12: k = 4 over 3 chunks; the 5-page ceiling |
| 18 | Small n: "inconclusive" is an expected verdict | bridge (M4) | step 12 |
| 19 | The retired model id | core (short) | step 5; Full step 13 |
| 20 | A local propositionizer (Flan-T5-large) | next | Full step 14 only |
| 21 | Shared idea with entity extraction (Graph RAG) | next | not taught; S1 owns it |
| 22 | Book text never goes into a prompt | bridge (D4) | step 12 |

Ideas the research did not list but the lesson needed, found while writing:

| Idea | Why it was needed | Now in |
|---|---|---|
| **Units include headings**, with their own ids | the UNFCCC's full name is only in the heading 10:2, so a proposition must be able to cite it | step 4; the prompt allows a heading id only together with a sentence id |
| **Where a resolved name may come from** (earlier on the same page) and the code check for it | without it, "decontextualise" invites outside knowledge | step 3 |
| **What alignment cannot see** (dropped qualifiers, wrong referents) | the research's checklist implies align catches unfaithful rewrites; the planted mistakes show two kinds it cannot catch | step 7 |
| **The text check** on arm (b) | span overlap credits p10-08 for D-002 although it does not state the year | step 9 |
| **Two parents** for sentences in the chunk overlap | 6 of the 40 propositions have two parents; the dedup rule needs a primary | step 6 |
| **The IndexUnit** record | the chunk contract fails for a rewrite (research error I4-E6) | step 6 |

## What step 4 found: the quiz against the lesson

QUIZ_TABLE

## Left to other concepts on purpose (link only)

- **Chunk size and overlap, the grid, equal-budget packing:** I1.
- **Contextual chunk headers, the cheaper fix for "it":** I5; compared in I-CMP.
- **The metrics themselves (Hit@k, MRR, CE@k, Wilson):** P6 and M2; used here, not derived.
- **Structured-output plumbing, retries, the cache:** M3 and the LLMOps foundation.
- **Selection on small dev sets, Holm, pre-registration:** M4.
- **Entity extraction for graphs:** S1.

## Errors found (recorded, not edited)

From this session's checks (details in `I4_FACTS.md` §3):
- **Research I4-E5 is not reproduced.** The repo's cell 16 output is consistent with its code: 31 written, 2 dropped, 29 embedded.
- **Research gap row 3's example** ("It is the supreme decision-making body", D-007 p.29) is not in the PDF; the real pronoun cases are 10:4 "It provides…" and 29:14 "These meetings…".
- **Checklist C4's cut-off** (align < 0.5) misses the repo's own astronaut proposition (0.667) and a wrong year (0.750); the lesson and tool list every align < 1.
- **P2 and P4 lessons (not edited):** their Short/Full code listens on every `.seg` button on the page, including in-body toggles. Clicking one (P2's AND/OR, tie rule, pool toggles; P4's in-body toggles) sets the depth to "undefined", which shows the Full-only parts while Short stays highlighted (checked in a browser on 2026-10-18; P1 and P3 have no in-body toggles). The fix is to listen on the top bar's group only, as the I4 lesson does (`#depth button`).

From the research file's error table, still open for a later correction pass: the S/U tier conflict (I4-E1), the 02 card's incomplete cell list (I4-E2), the embedder cell (I4-E9: cell 9, not 18), the page-range disagreement (I4-E10), 06's undefined "pointing back to the source span" (I4-E6) and the 5-page index ceiling (I4-E7).
