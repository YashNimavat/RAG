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

Every key point of the 19 questions was checked against the **Short** lesson (and the short reading file, where `i5_md_check.py` also checks that each reread names the section that teaches it). Two points were missing from the Short lesson and were added: late chunking (interview item, now one sentence in step 10; the details stay in step 14, Full) and "retrying cannot help" (I5-T-03, step 10).

| Item | What its key points need | Taught in (Short) |
|---|---|---|
| I5-PRE-01 | the subject sits outside the chunk ("it"); the retriever sees only the chunk's words | step 1 |
| I5-PRE-02 | a title identical on every chunk separates nothing; a header must vary | step 6 |
| I5-R-01 | meaning depends on text outside the span; two kinds of context: where it sits, what it refers to | step 1 |
| I5-R-02 | 1 distinct header for 97 chunks; the information test; it still shifts every vector | step 6 |
| I5-R-03 | embedding, BM25, generation inputs; v1.2 changes the embedding only; separate fields | step 2 |
| I5-R-04 | the span invariant; CE scoring uses offsets; template id → `preproc_version` → its own index | step 2 |
| I5-R-05 | 1 − recall@20; 5.7% → 3.7%; 35% is relative, 2.0 points absolute | step 12 |
| I5-R-06 | the document is a shared prefix written once, read 96 times; document first; below the minimum nothing is cached; any change in the prefix breaks the match | step 11 |
| I5-A-01 | 182 + 27 = 209 fits; 182 + 100 = 282, over by 26; the tail is cut | step 8 (ruler) |
| I5-A-02 | uncached $0.1367; cached $0.0261 (1.25× once, 0.1× reads); about 5.2× | steps 10–11 (calculator) |
| I5-A-03 | the p.10 and p.23 paths; title and leaf equal, chapter and section differ | step 4 |
| I5-A-04 | −2.0 points, −35.1%; about 18 points needed at n = 50 | steps 9 and 12 (converter) |
| I5-A-05 | chunk 68: start → Chapter 15 › … › DAC; majority → Chapter 16 › … › Paris Agreement; majority right for D-003 (for a 4: the start rule wins on chunk 34) | step 5 (explorer) |
| I5-A-06 | s = 0.112 on 151 tokens, 0.229 on 64; the short chunk is pulled about twice as much | step 7 (slider) |
| I5-T-01 | check n per category and the discordant pairs first; then dilution on short chunks; then shared or wrong headers | steps 5, 7, 9 |
| I5-T-02 | the key held the chunk text only; a context depends on the whole document; key on prompt version + document + chunk | step 11 (demo) |
| I5-T-03 | one 13,090-token request exceeds 8,000 TPM; waiting cannot help; two fixes (chapter window, Haiku with caching, paid tier) | step 10 |
| I5-T-04 | header–question leakage; the per-question header-only word check; re-test on span-written questions | step 9 |
| I5-R-07 | chunks lose context; contextual retrieval (LLM context from the whole document, cached); late chunking (dense only); the title is constant on one document; the heading rule matters (chunk 68) | steps 1, 5, 6, 10 |

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
