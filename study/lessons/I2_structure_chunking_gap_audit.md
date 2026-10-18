# I2 gap audit: how the lesson's contents were chosen

**What this is:** the check run before and while writing the I2 lesson, so you can judge the method. Every idea the lesson needs had to be found and taught; none of it was optional.
**What this is not:** the lesson itself. That is [I2_structure_chunking.html](I2_structure_chunking.html) (open it from the study kit: I2 → step 1). The research behind it is `study/research/phase_04_indexing.md`, "Concept I2"; the measured facts are `sources/verification/I2/I2_FACTS.md`.

## The method, in five steps

1. **Collect every idea the topic uses.** Sources: the research file's I2 audit (27 ideas, §2), its quiz titles (§3), its error table (§4), the library source notes (§5), the lesson blueprint (§6), the course files it names (02 I2 card, 06 v1.1 card, 07 D.4/D.8/D.9/H.3, LAB_FACTS §7), the repo cells, and the AIQ interview question 04 Q4. There was no old I2 lesson and no question file: I2 is new.
2. **For each idea, ask two questions.** Is it taught *before* it is used? Which concept owns it (C1, C2, I1, I5, M1, M2, P6)? Your progress file says none of these is studied yet, so their ideas count as not yet learned.
3. **Classify each idea.**
   - **Core:** I2's own idea; taught in full.
   - **Bridge:** needed here, owned elsewhere; taught briefly, in the place it is needed.
   - **Next topic:** only a link.
4. **Check the quiz.** Every key point of every question must be taught in the lesson's **Short** mode, because the quiz is the same for both depths.
5. **Check the facts.**
   - Every number was re-measured on the PyMuPDF 1.26.7 snapshot (`i2_measure.py`, byte-identical on rerun); the research's numbers were inputs to check, not facts to copy.
   - The repo cells and the AIQ text were checked by `i2_sources.py` (all pass).
   - **The book was not available in this session.** Its four pages are cited as the course files cite them and are marked UNVERIFIED in the lesson footer. Your local pass must open them.

## What the measurement changed in the research's plan

| Research said | Measured | What the lesson does |
|---|---|---|
| 16 orphans and 8 cuts, counted on PyPDFLoader text; "re-measure on PyMuPDF" (I2-E7) | identical on PyMuPDF text: the same 16 and 8 page breaks | step 1 uses them as measured facts |
| hyphen headings "may arrive as three runs" | all 15 are one span | step 5 says so; the rule still works on whole lines |
| a 1,068-character section splits into 534 + 534 | no such section; the shortest over-cap section is 1,004 → 341 + 663 (sentence end), the longest 1,935 → 990 + 945 | step 9 uses the real ones; the calculator shows the ideal formula |
| "check whether the PPP sentence lands in one chunk (verify)" | yes: L3 chunk [26553, 27136) | step 10 |
| size-only misses the 192 bold sub-headings | confirmed; **and** at split level L3 size-only gives the same 117 chunks | step 8: the bold rule matters at L4 and for the path |
| measure CE@4 per bucket | the 8 seeds have 0 straddling and 0 cross-page items | step 13: "inconclusive"; M1 must add boundary items |
| (not in the research) | balanced splitting at the nearest line break cut mid-sentence in 3 of 10 inspected chunks, and preferring `"\n\n"` cut right after headings (in this PDF `"\n\n"` occurs only at page joins) | the rule became "sentence-ending line break within half a piece, else nearest line break; never inside or right after a heading". 10 of 10 inspected chunks now pass (step 12) |

## What step 2 found: 27 ideas, and where each is taught

| # | Idea | Class | In the lesson |
|---|---|---|---|
| 1 | Snapshot text, document offsets, page table | bridge (C1) | step 6, five lines; step 10 for the page join |
| 2 | The recursive splitter and its separators | bridge (C2) | step 1 (v0), step 9 (the cut rule inside long sections) |
| 3 | Per-page vs cross-page scope; 16 orphans, 8 cuts | bridge (C2/I1) | step 1, with the page ruler; step 10 for the cross-page control arm |
| 4 | Blocks → lines → spans; the span dict fields | core | step 2, one real span dict |
| 5 | `flags` bits; bold = `flags & 16`; `char_flags` | core | step 2, bit table and the "== 16" mistake |
| 6 | Body size by characters, not spans | core | step 3, ladder chart and a toy counter-example |
| 7 | Heading rules: size rank, bold at body size, numbering, short line | core | steps 4–5, the rule explorer |
| 8 | Other structure sources: outline, tags, markup | core | step 4 (one line); Full step 14 decision table |
| 9 | Error modes: wraps, hyphen runs, bold lead-ins, running headers, captions, two columns, repeated titles | core | step 5 table |
| 10 | Aligning a heading line to an exact offset (cursor + find) | core | step 6, with why the cursor matters (repeated titles) |
| 11 | Section tree and path | core | step 7, the Chapter 6 tree and the two Paris Agreement paths |
| 12 | Split by section, then cap; balanced split | core | steps 8–9, histogram switcher and calculator |
| 13 | Merging small siblings | core | step 9 (L4, m = 400: 209 → 139) |
| 14 | Cross-page continuation; page segments | core | step 10 |
| 15 | Heading in the chunk vs metadata vs prepended | bridge (I5) | step 7: exact slice; path is metadata; prepending is I5 |
| 16 | Uneven sizes break fixed-k; equal budget | bridge (I1/M4) | steps 8 and 13 |
| 17 | Embedder truncation | bridge (C2/C3) | step 13 (no chunk over 256 WordPiece tokens; in I2_FACTS) and checklist S9 |
| 18 | Boundary bucket and section-scoped items | core (with M1) | step 13: `straddles_champion`, `crosses_page`, both empty today |
| 19 | CE@k on spans | bridge (M2/P6) | step 13, one sentence with the P6 D.7 link |
| 20 | Eye-inspection protocol | core | step 12, the 10-chunk sheet |
| 21 | Chunk-property tests | core | step 11, five invariants with code |
| 22 | Tables kept whole | next (C7/S2) | Full step 16, one paragraph |
| 23 | PDF → Markdown converters, header splitter, re-anchoring | core (LLMOps) | step 6 mistake (Short); Full step 15; LLMOps plan |
| 24 | Layout models | next (S2) | Full step 16 |
| 25 | Rules tuned on one corpus may fail on another | core | step 4 mistake, the apply-it tool and checklist |
| 26 | Duplicate titles as near-duplicate distractors | bridge (I5/R2) | step 5 table, step 7 paths |
| 27 | Element-type and page-level chunking as rivals | core (Full) | Full step 16; the page-level rival also in step 13's reading |

## What step 4 found: the quiz against the lesson

QUIZ_TABLE

## Left to other concepts on purpose (link only)

- **Prepending the path or an LLM context to the embedded text:** I5.
- **Choosing the cap (the v1.0 champion):** I1.
- **Building and freezing the boundary items; the harness and CE@k:** M1 and M2.
- **Tables, OCR and layout models:** C7 and S2.
- **Semantic and proposition chunking:** I3 and I4; the comparison of all of them: I-CMP.

## Errors found in the course files (recorded, not edited)

From the research (I2-E1 to I2-E10), still open: 03 row 428 misses C1 as a prerequisite; the 02 and 04 page sets for I2 differ (use their union); "boundary-bucket" (02) and "section-scoped" (06) are undefined; 06 v1.1 says "font-size/bold spans" without the bold-at-body rule; v1.1 changes page scope too, so it needs the cross-page control arm; 03's "PDFs rarely carry reliable heading markup" is too strong for born-digital PDFs; the AIQ answer overclaims; LLMOPS §9.2 lacks a `MarkdownHeaderTextSplitter` row. **Closed by this pass:** I2-E7 (the 16 orphans re-measured on PyMuPDF text).
New in this pass: the research's 1,068-character example section does not exist under these rules; the seeds contain no boundary items (I2_FACTS §3).
