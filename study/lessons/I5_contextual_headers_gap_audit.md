# I5 gap audit: how the lesson's contents were chosen

**What this is:** the check run before and while writing the I5 lesson, so you can judge the method. Every idea the lesson needs had to be found and taught; none of it was optional.
**What this is not:** the lesson itself. That is [I5_contextual_headers.html](I5_contextual_headers.html) (open it from the study kit: I5 → the visual lesson). The research behind it is `study/research/phase_04_indexing.md`, "Concept I5"; the measured numbers are in `sources/verification/I5/I5_FACTS.md`; the build contract is `sources/verification/I5/I5_BUILD_SPEC.md`.

## The method, in five steps

1. **Collect every idea the topic uses.** Sources: the book pages as the course plan cites them (Ch7 p.1–2/11, p.4–9/11; the book was not available in this build session, see step 5), the upstream notebook `contextual_chunk_headers.ipynb` (all 17 cells re-read at `009adba`), the 06 v1.2 card, the research's 26-idea audit and 11 errors, the 19 quiz questions with their key points and wrong answers, and outside sources (Anthropic's contextual retrieval post and cookbook, dsRAG, late chunking, LlamaIndex source).
2. **For each idea, ask two questions.** Is it taught *before* it is used? Which concept owns it (I5, I2, C2, C3, P3, P4, M1, M2, R1, R3, LLMOps)? Your progress file says I5 and all its prerequisites are `not_started`, so their ideas count as not yet learned.
3. **Classify each idea.**
   - **Core:** I5's own idea; taught in full.
   - **Bridge:** needed here, but owned elsewhere; taught briefly, in the place it is needed.
   - **Next topic:** only a link.
4. **Check the quiz.** Every key point of every question must be taught in the lesson, in **Short** mode too, because the quiz is the same for both depths.
5. **Check the facts.**
   - Every number is matched against `I5_FACTS.md` (K1–K16, from `i5_kit_measure.py`, byte-identical on rerun).
   - The build session could not download MiniLM or the tiktoken files (blocked hosts), so token counts are labelled estimates from measured ratios, and every MiniLM result is a "your run" cell that the verify notebook fills in.
   - The book was not present, so its pages are cited as 02/04 give them; the book-dependent checks (page exists, 15-word copyright) are SKIPPED in `i5_md_check.py` and must be rerun on your machine.

## What step 2 found: the ideas, and where each is taught

There was no earlier I5 lesson, so every idea is new. The research listed 26; the measurements for this build added 4 (marked **new**).

| # | Idea | Class | Where in the lesson |
|---|---|---|---|
| 1 | "Contextually anonymous" chunk: pronoun, orphaned heading, missing chapter | core | step 1, with chunk 34 ("It can be used for …") (Short) |
| 2 | Chunk record fields and the span invariant `text == doc[start:end]` | bridge (C3) | step 2 (Short) |
| 3 | `preproc_version` → embedding cache key → index folder | bridge (C3) | step 2 (Short) |
| 4 | Headings from font size and bold (`get_text("dict")`) | bridge (I2, C1) | step 3, the line-style table and the per-page chart (Short) |
| 5 | Heading path vs leaf heading | core | step 4, the two Paris paths (Short) |
| 6 | **new:** which heading a chunk gets (start, majority, all inside); no rule is right everywhere | core | step 5, the rule explorer on chunks 68, 27 and 34 (Short) |
| 7 | A constant prefix carries no discriminating information | core | step 6, the arms table (Short) |
| 8 | The three inputs: embedding, BM25, generation | core | step 2, a 3-row table (Short) |
| 9 | Mean pooling: the header's share `h/(h+c)` | bridge (P4) | step 7, the share slider (Short) |
| 10 | Truncation cuts the chunk's tail; specials count inside 256 | bridge (C2, P4) | step 8, the ruler (Short) |
| 11 | Query side unchanged (`input_type` asymmetry, cache hits) | bridge (P4, C3) | step 2, one sentence (Short) |
| 12 | Near-duplicate distractors and the header magnet | core | steps 4 and 7, with the toy chart (Short) |
| 13 | Header–question leakage | core | step 9 (Short); the upstream "Nike" query in steps 12 and 13 |
| 14 | LLM contextualization (whole document + chunk → 50–100 tokens) | core | step 10 (Short) |
| 15 | Cost ladder: rungs 0–3 | core | step 10, the table and the calculator (Short) |
| 16 | Prompt caching: prefix match, minimum, TTL, write/read multipliers | bridge (P1, D2) | step 11 (Short); the calculator's "below the minimum" case |
| 17 | Groq's per-request limit blocks the whole-document arm on the free tier | core | step 10 (Short) |
| 18 | Cache key must hold the document and the prompt version | bridge (LLMOps) | step 11, the page-12 demo (Short) |
| 19 | Hallucinated context; the entity-in-document check | core | step 11 (Short); tool checks H11–H12 |
| 20 | Vendor metric vs ours; absolute vs relative change; detectable effect at n ≈ 50 | core | steps 9 and 12, the converter (Short) |
| 21 | A reranker score on one chunk is not a retrieval metric | bridge (R3) | step 12 (Short), step 13 (Full) |
| 22 | CE@4, paired comparison, discordant pairs, per-category n | bridge (M2, M4) | step 9 (Short) |
| 23 | Contextual BM25 | next (R1) | step 2 (one row), step 6 (the idf floor), step 14 (Full) |
| 24 | Late chunking | next | step 14 (Full) |
| 25 | Hosted contextual embedders | next | step 14 (Full) |
| 26 | Headers shown to the generator | next (C5, X3) | step 2, one row |
| 27 | **new:** Corpus D is heading-dense: 0 chunks without a heading, 94 of 97 with two or more | core | steps 1 and 5 (Short) |
| 28 | **new:** orphaned headings counted at every chunk end (31), not only page ends (16) | core | step 1 (Short) |
| 29 | **new:** the seeds are at the BM25 ceiling, so they cannot show a gain | core | step 9 (Short) |
| 30 | Index time vs query time (MC-003) | bridge (C5, P7) | step 2: the header is built once at index time; queries are unchanged |

## What step 4 found: the quiz against the lesson

{{QUIZ_TABLE}}

## Left to other concepts on purpose (link only)

- **The heading detector itself** (merging, balancing, odd PDFs): I2, structure-aware chunking. I5 uses the tree.
- **Contextual BM25 as an experiment:** R1 at v2.0, through the `bm25_text` field.
- **Showing headers to the generator:** a later C5/X3 arm, judged at the end-of-course judge batch (D-10).
- **The LLMOps notebook** (cached Groq/Haiku calls, tracing, monitoring): planned in the research §9; it needs `study/llmops/` first, like P4's.
- **The lab** `labs/I5_chunk_headers_lab.ipynb` (02 card): not built in this session.

## Errors found (recorded, not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| I5-E1 … E11 | research §4 | stand as reported; K14 re-confirms the upstream facts behind I5-E9 and E10 | as in the research |
| I5-E12 | research §5 and §6 | "18 of 120 chunks have no heading" came from a scratch split; on v0's 97 chunks it is **0** (K4) | use the K4 numbers |
| I5-E13 | research §5 primary arm | the path at the chunk start gives D-003's gold chunk (68) the wrong chapter (K4) | pre-register start and majority as two arms |
| I5-E14 | 07 D.8 "16 orphaned headings" | correct for page ends; at every chunk end there are 31 (K4) | say "16 at page ends, 31 in all" |
| I5-E15 | `study/lessons/P2_ir_framing.html` script | the Short/Full handler listens to every `.seg` button, so the in-page AND/OR, tie and pool toggles set the depth to `undefined` and show every Full part | listen to `.top .seg button` only (I5 does this). Found while testing I5; not fixed here |
