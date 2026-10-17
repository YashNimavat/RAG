# Phase 4 research: Indexing and representation → v1.x

**What this is:** the research and gap audit for Phase 4 (I1 chunk size/overlap experiments, I2 structure-aware chunking, I3 semantic chunking, I4 proposition chunking, I5 contextual chunk headers / contextual retrieval, I6 document augmentation and HyPE, I-CMP granularity comparison), done 2026-10-17 by Claude with seven research helpers, one per concept, in a Claude Code cloud session.
**What this is not:** lessons or code. Nothing in the course was changed, nothing was installed, and no LLM, embedding, rerank or tracing API was called.

**How it was checked, and what could not be checked.** This session ran in a cloud container that differs from Yash's machine, so several inputs that RESEARCH_PROMPT §3 lists were **not available**. Read the labels with that in mind.
- **Book (*RAG Made Simple*): not present.** No book page was opened in this session. Every book citation comes from the paraphrased page notes in 02, 03, 04 §3 and 07, which earlier sessions verified, and carries the label "per 04, not re-opened" (UNVERIFIED for this session). Where 02 and 04 give different pages, this file reports the disagreement instead of settling it. Because no book text was read, none can have been copied; 04's paraphrases were summarised, not reproduced.
- **AI Eval book (AE): not present.** AE methods are used only as summarised in `sources/EXTERNAL_RESOURCES_REVIEW_2026-10-09.md` and `phase_03_measurement.md`.
- **`CLAUDE.md` and the project skills (`.claude/skills/`): not present.** The skill methods were applied as `LLMOPS_FOUNDATION.md` and `phase_03_measurement.md` describe them, and each LLMOps plan names the skill it follows.
- **Network:** raw GitHub, github.com, PyPI and anthropic.com were reachable. arXiv, ACL Anthology, OpenReview, Hugging Face, the LangChain/Groq/Cohere docs sites and vendor blogs were **blocked**. Papers that could only be found through web search are labelled **"search-checked, page not opened (UNVERIFIED)"**; GitHub READMEs and source code were opened and are labelled verified.
- **Upstream repo:** every cited notebook cell (0-based) and script line was opened at the pinned commit `009adba`, and so were the AIQ (`e080df2`, MIT, "Copyright (c) 2026 Om") and SDG (`ed955b2`, MIT) files used.
- **Library behaviour:** read from released source code (tag or wheel named at each citation). Pins come from the PyPI JSON on 2026-10-17 (newest release on or before 2026-10-03).
- **Corpus D measurements** (heading tree, sentence counts, chunk counts) were made in the scratchpad with poppler (`pdftotext`, `pdftohtml`) and the standard library, because PyMuPDF is not installed here. They are approximate. For example, one helper's re-implementation of v0 gives 103 chunks where the measured C2 value is 97. Every verify notebook re-measures them on the PyMuPDF snapshot.

**A local follow-up pass is needed** before any Phase 4 lesson is written. On Yash's machine: open the cited book pages and settle the page disagreements (listed in each concept's §4); re-open the search-checked papers; and load the project skills named in each §9. It is a checking pass, not new research.

**Citation keys used below.** Book pages as `Ch9 p.6/14`. AE as `AE ChN, 'section'`. Repo cells as `notebook.ipynb cell N` (0-based) at `009adba`. Interview repo as `AIQ <file> Q<n>`. External sources as **[I1-S3]** and so on, numbered per concept and listed per concept in the final Sources section. Error ids are per concept (`I3-E8`).

---

## Summary (read this first)

**The 5 most important gaps across the phase**
1. **Phase 4 cannot select reliably on the planned data, and nothing says so.**
   - Dev holds about 12–16 answerable items (≈30% of 40–55, 06 §6.3), so the smallest CE@4 difference it can detect is about 0.4.
   - Phase 4 tries about 45–50 arms on dev, 34–37 of them in the v1.0 grid alone. A toy simulation (I1 §5) where every arm is equally good still gives the dev winner +0.16 to +0.25. With about 5 test touches, the chance of at least one false adoption is ≈0.23.
   - Fix: a pre-registered shortlist of at most 3 arms per round, a tie rule towards v0 or the cheaper arm, Holm correction within a round, one register of every arm tried, and "inconclusive" as an expected verdict (I1-E8, I-CMP gap 2).
2. **Derived index units break the course's span invariant, and no file defines how to score them.**
   - 06 §2.3 requires `doc_text[char_start:char_end] == text` for every chunk. That fails for semantic chunks that LangChain rejoins with spaces (I3), LLM-written propositions (I4), chunks with prepended headers (I5) and generated questions (I6).
   - Fix: one `IndexUnit` type whose `embed_text` may differ from its evidence span, a parent mapping, one shared "dedup-before-cut" retriever, and the scoring rules written into the scorer spec as `scorer_version` options (I4-E6, I5 gap 2, I6 gap 2).
3. **Corpus D's real structure changes the I2 and I5 designs.** Two helpers measured it independently, I2 from the raw PDF streams and I5 with poppler, and got the same tree: 1 title, 21 chapters, 68 sections and 192 sub-headings.
   - 192 of 282 headings (68%) are bold at the 12 pt body size. So a size-only detector, including `pymupdf4llm`'s default, misses them.
   - Corpus D is one document, so a document-title header is the same on all 97 chunks and carries no information.
   - 11 heading names repeat across chapters ("Paris Agreement" on p.10 under Ch6 and on p.23 under Ch16). Only the chapter and section levels tell those pages apart.
   - Effects: 06 v1.1 must say "size rank + bold", and 06/04's "title header" arm must become a heading-path arm. Title claims belong to Corpus T (I2 gap 2, I5 gap 1).
4. **The index-time LLM arms have new risks: leakage, quota and an uncalibrated filter.**
   - **Leakage (I6):** generated questions can paraphrase the LLM-drafted eval questions (D-09) and inflate scores. No file guards against it. I6 designs a `leak(i)` report, a calibrated threshold, a decisive slice and a de-leaked arm.
   - **Quota and filter (I4):** grading each proposition separately is about 1,400 calls (≈8.6 days of Groq free-tier tokens). It is also an uncalibrated LLM filter, which is the MC-006 pattern. Batch it per page and check it against hand labels.
   - **Request size (I5):** the whole-document context arm sends about 13K tokens per request, which is over Groq's 8K TPM. So LLMOPS §6.4's routing of I5 to Groq fails for that arm.
5. **The equal-token-budget comparison is under-specified, and two question buckets are undefined.**
   - **Budget:** a whole-number k misses the budget by up to −32%; no tokenizer is named (I1 recommends `o200k_harmony`, the generator's own encoding, already in tiktoken 0.14.0); and 07's packing loop stops at the first chunk that does not fit. Realized tokens must be reported per arm (I1 gap 2).
   - **Buckets:** "boundary-bucket" (02) and "section-scoped" (06) questions are never defined.
   - **Page scope:** v1.1 changes page scope as well as boundaries, so it needs a cross-page v1.0 control arm (I2 gap 3).

**Tools to add, across the phase** (details in each concept's §10; install nothing yet)
- **Nothing new for the lessons or verify notebooks.** They use numpy, pymupdf 1.26.7, tiktoken 0.14.0, sentence-transformers (MiniLM, and the ms-marco cross-encoder as I6's question filter), scipy and plotly, which are all installed.
- **From `LLMOPS_FOUNDATION.md` §11, when the LLMOps notebooks are built:** `langchain-core` 1.6.6, `langchain-text-splitters` 1.1.3 (splitter comparisons in I1, I2 and I5), `langsmith` 0.14.4, `arize-phoenix-otel` 0.17.2, and `anthropic` 1.11.0 for the optional Haiku arms.
- **New, LLMOps comparison arms only:**
  - `langchain-experimental` 0.4.2 (MIT, 2026-05-22), for I3's parity test against `SemanticChunker`. It pulls `langchain-community` 0.4.2 and `langchain-classic` 1.0.8, 14 packages in all, with no OpenAI.
  - `pymupdf4llm` 0.2.9 + `tabulate` 0.10.0, for I2's Markdown-header arm. 0.2.9 is the newest release compatible with the `pymupdf==1.26.7` pin (it needs `pymupdf>=1.26.6`, checked on PyPI). AGPL/commercial, the same as PyMuPDF.
- **Optional:** `pysbd` 0.3.4, only if the Corpus T sentence-split check fails (I3); `statsmodels` 0.15.0 for Holm (I-CMP), which is easy to do by hand.
- **Not added (read-only or Full-only):**
  - `docling` (torch models; its chunker adds headings to the embedded text by default) and `unstructured` (spaCy/numba).
  - `pymupdf-layout` (needs PyMuPDF 1.28.2).
  - The Dense X Flan-T5 propositionizer (≈3 GB).
  - Late chunking: it needs a long-context local embedder with token outputs, not Cohere.
  - `langchain-classic` direct: read its source instead.

**Decisions Yash must make** (each answerable in a word; recommendation in bold)
1. Grow the eval set before the v1.0 grid, to about 30 dev items and towards D-09's 60–100 target? **yes** / no.
2. Cap each v1.x round at 3 pre-registered arms with Holm, and treat the rest of the v1.0 grid as exploratory? **yes** / no.
3. When Claude credits exist, write the index-time LLM text with Haiku 5.5 (I5's whole-document headers, I6's questions; the model-family swap also lowers I6's leakage risk)? **yes** / no. I4 stays on Groq either way.
4. Scope of the v1.4 proposition index: **full** Corpus D / 5-page subset. A 5-page index would recreate upstream's ceiling (k=4 over about 15 chunks). Restrict the eval items if needed, not the index.
5. Add the two LLMOps comparison packages, `langchain-experimental` (I3) and `pymupdf4llm` (I2)? **yes** / no.

Smaller preferences are in each concept's §11: embed every distinct I1 arm with Cohere (all); I2's lesson split level (section); a late-chunking demo (no); run I6's experiment or study only its mechanism (run).

**Size of the build work**

| Concept | Size | Why |
|---|---|---|
| I1 chunk grid | **M** | The chunker, metrics and statistics exist (C2, M2, M4). New: the grid runner with duplicate-arm hashing, budget packing with realized tokens, a `dup_frac` diagnostic, the winner's-curse demo, heatmaps and the apply-it tool. About 70 Groq calls |
| I2 structure-aware | **M** | A chunker of about 150 lines plus tests. Heading rules (size rank + bold), mapping heading lines to snapshot offsets, merge and balance, fixture "zoo" and the new bucket tags all need care. No API work |
| I3 semantic | **M** | The NumPy mechanism is small. The work is a span-preserving sentence splitter at document scope, the equal-budget and size-matched arms, a parity test against LangChain and a size monitor. 8–10 cached Cohere calls |
| I4 propositions | **M** | New `Proposition` type with spans, anchored generation, alignment, two scorings, a 60-unit hand sample. 10–66 API calls |
| I5 contextual headers | **M** | The deterministic arm is S (it reuses I2's heading tree and the I1 runner). The LLM arm adds prompt files, measured caching, an entity check and a Corpus T run |
| I6 document augmentation | **S** | A NumPy multi-vector table plus dedup, the leakage report and an experiment card. 97 calls ≈ $0.02 per build |
| I-CMP comparison | **M** | No new mechanism and 0 new calls, but it aggregates every I1–I6 artifact into one table, one chooser tool and one consolidated LLMOps view. It can be finished only after the runs exist; its fixture mode works before |

---

## Concept I1: Chunk size/overlap experiments (E, project v1.0)

I1 is the first Phase 4 experiment. It is not a new mechanism. C2 already teaches how chunks are made: windows, overlap, units, truncation and page scope (07 Parts A–H). M4 already teaches how to compare two runs: pairing, the sign test, the group bootstrap, power, and testing once on test. I1 joins the two. It runs one designed grid, picks a size on dev without fooling itself, confirms that size once on test, and writes the decision down with its costs. So this audit covers the ideas that are new when the experiment is **a grid**, not a pair:
- duplicate arms;
- equal-budget k when it must be a whole number;
- duplicated text in top-k;
- the winner's curse on a small dev split;
- ceiling items;
- truncation as a confound that only the fallback model has.

### 1. Sources checked

**Book (not present; per 04 §3 and 07 G.1; not re-opened, UNVERIFIED):**
- Ch1 p.10–11/14 (role of chunk size; per 04 §3 Ch1 and 07 G.1). The book calls chunk size the most important setting in simple RAG. Very small chunks (about 100 characters) lose context, very large ones (about 5,000) bury the signal, and about 1,000/200 is called the sweet spot. **Asserted, not measured** (07 G.1, CR-07).
- Ch6 p.9–10/14 (HyDE: the hypothetical answer should be about chunk length; per 04 §3 Ch6). For I1 this is a **downstream consequence**: the I1 champion's size becomes the length target for Q2. It is not evidence about chunk size.
- Ch8 p.7/11 (window size; listed by 04 §2.4, **not** by 02's card). This page is about X1's neighbour window, not the chunk size. Treat it as a "next" link (Errors I1-E1).
- No chapter covers measuring chunk size; the book's evaluation chapter (Ch22) comes last (07 G.1, App p.12/23 per 07).

**Repo (verified: downloaded at `009adba`, cells read 0-based with `python3 -I`; code not run):**
- `all_rag_techniques/choose_chunk_size.ipynb`:
  - cell 2: imports, including `DatasetGenerator`;
  - cell 4: `SimpleDirectoryReader("../data")` loads every file in the folder;
  - cell 6: `documents[0:20]`, then `random.sample(..., 25)` with no seed;
  - cell 8: `gpt-4o` judges, plus the no-op `update_prompts({"your_prompt_key": ...})`;
  - cell 10: `Settings.chunk_size = chunk_size`, `Settings.chunk_overlap = chunk_size // 5`, `similarity_top_k=5`, answers by `gpt-3.5-turbo`, binary `.passing` scores;
  - cell 12: `chunk_sizes = [128, 256]`. The saved output is a `ServiceContext` deprecation warning plus "Faithfulness: 1.00, Relevancy: 1.00" for both sizes, at 1.35 s and 1.31 s. The warning comes from code that is no longer in the cell, so the output is **stale**.
  - All of this matches 07 G.4.
- `all_rag_techniques_runnable_scripts/choose_chunk_size.py` (141 lines):
  - L23–L72 is the evaluation function; L48 is `SentenceSplitter(chunk_size=chunk_size)` with no overlap; L52 is `similarity_top_k=5`;
  - L107 has the same no-op prompt key;
  - the defaults `[128, 256]` sit at **L133**, outside 04's cited range L23–L123 (I1-E2).

**Existing course files:**
- 02 I1 card (L547–L563) and the per-technique gate (L1149–L1157);
- 03 rows L427 and L515, and edge notes L477/L483;
- 04 §2.4 I1 row, §3 Ch1/Ch6/Ch8, DV-06;
- 06 §3.1, §3.2, §4.1 rules, v1.0 card (L529–L540), §4.3, §6.1–6.3, §7.2–7.6, §9.1–9.6;
- 07 Parts D.2–D.8, G.4, I (I.1–I.5) and J1/J5/J7/J10;
- 08 D-03, D-06, D-09, D-10, D-32;
- `C2LAB_FACTS.md`, `C3_FACTS.md`;
- `phase_02_core_rag_baseline.md`: C2 §5 [C2-1…C2-9] and C3 [C3-1…C3-3], already researched, reused and re-checked here, not redone;
- `phase_03_measurement.md` M4 (the statistics I1 reuses);
- `LLMOPS_FOUNDATION.md` §2–§12;
- the tracker (I1, C2, C3, M1–M5 all `not_started`; M2 `exposed`);
- the misconception log (MC-001, MC-003, MC-005).

**AE book:** not needed beyond M4. The review notes that AE promises a chunking grid-search section that is absent (phase_02 C2 §1). One row of the review applies: before reporting the grid, list the items with CE@k = 0 under every arm and re-read their gold spans (review L247).

**Interview repo (AIQ @ `e080df2`, MIT, "Copyright (c) 2026 Om"; verified):**
- 04 Q5 L123–L137 (size and overlap; start at about 512 tokens with 10–20% overlap; "retrieve small, generate big");
- 04 Q33 L833–L855 ("Overlapping chunks manufacture redundancy after ingest");
- 04 Q43 (metrics).

**External (numbered in the I1 list in the final Sources section):**
- [I1-S1] Chroma `chunking_evaluation` code (verified);
- [I1-S2] Chroma report (numbers carried from phase_02 [C2-4]; page blocked);
- [I1-S3] Bhat et al. 2025 (search-checked; code repo exists);
- [I1-S4] NVIDIA blog (search-checked, vendor);
- [I1-S5] LangChain splitter source (verified);
- [I1-S6] LlamaIndex `SentenceSplitter` source (verified);
- [I1-S7] Cohere embed-v4.0 limits (phase_02 verified docs, plus search);
- [I1-S8] Cawley & Talbot 2010 (search-checked);
- [I1-S9] tiktoken 0.14.0 source (verified);
- [I1-S10] the one-standard-error rule (UNVERIFIED, not opened).

**Helper measurements (new; approximate):**
- I downloaded the climate PDF (sha256 `1d58a0fa…92669`, which matches C3_FACTS) and extracted the text per page with `pdftotext`: 71,583 characters, against PyMuPDF's 72,593 (−1.4%).
- I re-implemented the course-style recursive splitter (06 separators, no stripping, overlap built from whole pieces) and ran all 36 configurations.
- My v0 (1000/200, per page) gives **103 chunks, against the measured 97** on PyMuPDF. So every count below is labelled **approx.** and must be re-measured on the PyMuPDF snapshot by the verify notebook.

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class (core / bridge / next) | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Dilution vs fragmentation as two failure buckets with opposite fixes | 02 card "Failure"; 06 v1.0 Problem | 07 B.3, D.7 (toy) | C2 | no | bridge | One recap paragraph plus the D.7 toy figure. Then make it testable: H1 (dilution → MRR on single-span), H2 (fragmentation → CE@4 on multi-span) |
| 2 | Chunk size and k are **coupled**: context = k × mean chunk length (MC-005) | 06 §4.1 rule 2; 07 J10 | 07 I.2 (design only); M4 step 5 (one pair) | I1 | no (MC-005 open) | core | A worked table: at k = 4, 400-char chunks carry about 46% of v0's text (approx. 345 vs 750 mean characters). Show "bigger chunks" and "bigger k" as two routes to the same extra context |
| 3 | **Equal-token-budget k**: k = B / mean chunk tokens; integer k; floor vs round; per-query packing vs fixed k per arm | 06 v1.0 Experiment; 07 I.2 `take_within_budget` | **incomplete** (07 gives the packing code but no k arithmetic, no rounding rule, and no "realized budget" report) | I1 | no | core | Formula plus a table (approx.): at B = 3,000 chars, the 1500-char arm gets k = 2 by floor (−32% context) or 3 by rounding (+1%). The rule must be pre-registered, and realized mean tokens reported per arm |
| 4 | Which tokenizer counts the budget (generator's) vs which one counts truncation (embedder's) | 06 §3.2; 07 I.2 "named tokenizer" | **missing** (07 says "named" but names none) | I1 (P1 for tokenizers) | P1 exposed only; MC-001 open | core | Two tokenizers, two jobs: `o200k_harmony` (gpt-oss, in tiktoken 0.14.0 [I1-S9]) for the context budget; the embedder's own tokenizer for truncation. Never cl100k for either (07 D.6: cl100k flags 18 chunks over 256 where WordPiece flags 4) |
| 5 | Overlap duplication: overlapping chunks retrieved together repeat text and spend the budget twice | 07 I.2 coach note; AIQ 04 Q33 | 07 coach note only | I1 (X3 owns dedup) | no | core | Diagnostic `dup_frac = 1 − unique chars / total chars` per query; Chroma's precision divides by the **sum**, not the union, of retrieved chunk lengths [I1-S1]. Dedup at assembly is X3, linked only |
| 6 | **Nominal vs realized overlap** (recursive overlap is made of whole pieces) | 07 D.4 | 07 D.4 (one paragraph); C2 lab Task 8 | C2 | no | bridge | Grid fact (approx.): stored/original is 1.08 at 1000/200 (fixed windows: 1.25), and **1.00** at 2000/x per page, so those overlap arms are not real arms |
| 7 | **Duplicate arms**: different configs giving byte-identical chunk sets | 07 I.2 "36 configurations"; 06 §9.4 "36+" | **missing** | I1 | no | core | Hash each arm's span list. Approx.: 34 distinct sets out of 36, since per-page 2000/0, 2000/200 and 2000/400 are identical, and 1500/150 and 1500/300 add only 1–2 new texts each over 1500/0. Count distinct arms for multiple comparisons and cost |
| 8 | Page length caps chunk size under per-page scope | 07 I.3 | 07 I.3 | I1 | no | core | Keep the 07 note and add the duplicate-arm finding (#7) as its consequence |
| 9 | Per-page vs cross-page arm: citation exactness vs boundary cuts | 06 v1.0; 07 D.8, H4 | 07 D.8 | C2 / I1 | no | core | Approx.: cross-page 1000/200 gives 99 chunks, 34 of them span two pages. The cost is two-page citations. Score by document offsets (06 §7.2), so both scopes are scored identically |
| 10 | Truncation as a confound **only for the fallback** | 06 §3.2; 07 H5, J1 | 07 D.6 (MiniLM numbers) | C2 / C3 | no | core | Under D-03 (Cohere embed-v4.0, limit 8,192 or 128k [I1-S7]) the largest grid chunk (≈ 360 cl100k tokens, derived) cannot be cut. H5 belongs to the MiniLM arm. Send `truncate="NONE"` so any cut fails loudly |
| 11 | MiniLM's 128-token training length (fits under 256 ≠ well represented) | 07 D.6 | 07 D.6 | C2 / P4 | no | bridge | One line; a reason the MiniLM arm may favour smaller chunks than the Cohere arm (consistent with [I1-S3]'s embedder disagreement) |
| 12 | The grid is **many comparisons**: P(any false win) = 1 − 0.95^m; the winner's curse | 06 §9.4 item 3 | M4 idea 7 (formula only) | M4 → I1 | no | core | New here: the toy simulation (§5). With about 15 dev items and 34 equally good arms, the dev winner looks +0.16 to +0.25 better than the truth. Larger than the minimum detectable effect |
| 13 | **Selection design**: a pre-registered shortlist plus an exploratory grid; coarse-to-fine; the one-SE / prefer-simpler tie rule | 06 §4.1 rule 4; 07 I.1 | **missing** (07 says "choose one candidate there" with no rule for choosing among 34) | I1 | no | core | §6 step 6: decide among ≤ 3 hypothesis-driven arms; the full grid is a descriptive heatmap labelled exploratory; ties go to v0, or the cheaper arm |
| 14 | Dev/test discipline: one test touch, logged with the number of **distinct** arms tried | 06 §9.1 `TEST_LOG.md`; 07 I.4 | M4 | M4 | no | bridge | Reuse M4's `compare_runs.py`; log distinct arms (34), not nominal configs (37) |
| 15 | Paired comparison, discordant pairs, group bootstrap, MDE | 06 §9.3–9.4 | M4 (planned) | M4 | no | bridge | Two lines and a link. Do not re-teach. Show only b/c per arm against v0 |
| 16 | Ceiling and floor items: CE = 1 or 0 under **every** arm carries no information | 02 outcome 3; review L247 | 07 J7 (the repo's 1.00/1.00 only) | I1 | no | core | Report the informative-item count (items whose CE differs across arms). Re-read the all-zero items' gold spans before reporting |
| 17 | The ceiling in `choose_chunk_size` (1.00/1.00), and why it is not a win | 02 outcome 3; DV-06 | 07 G.4, J7 | I1 | no | core | Short critique, then contrast: the same question asked of our grid ("would you believe sizes don't matter?") |
| 18 | CE@k (union; sufficiency) vs Precision/nDCG (reward redundancy) vs IoU (punishes redundancy) | 06 §7.3 traps; I1-S1 | 06 §7.3; M2 planned | M2 | M2 exposed | bridge | A three-row table: what each metric does when the same span arrives twice. CE stays primary |
| 19 | IDCG changes with chunking, so nDCG is not comparable across arms | 06 §7.3 | 06 only | M2 | no | bridge | One line; rank on CE@4, then MRR |
| 20 | Retrieval ≠ answer; generation only for the top 2–3; deterministic checks plus ~10 read answers (D-10) | 06 v1.0; 07 I.3, I.5 | 07 I.5; M3 | M3 | no | bridge | The 2×2 from 06 §7.1, one line; costs in §9 |
| 21 | Per-category reporting with n (diagnosis only) | 06 §7.6; 07 I.4 | 06 | M4 | no | bridge | Dev per-category n ≈ 2–4: show the direction only, never a decision |
| 22 | Index build cost per arm (#chunks, embed calls, cold build time) | 02 gate "cost and latency delta"; 06 §7.5 | 06 | I1 (D2 later) | no | core | Approx.: 5,916 chunk embeddings over 36 configs, 2,323 unique texts; 83 Cohere calls without dedup, 45 with the content cache |
| 23 | Content-keyed cache reuse across arms (identical texts embed once) | 07 I.2 Caching row; C3 | C3 (not studied) | C3 | no | bridge | Show the hit rate in the trace (approx. 61% on the first run, 100% on replay) |
| 24 | Overlap (index time) vs prompt joining (query time) (MC-003) | 07 J5; MC-003 | P7 / C5 (not studied) | C5 / P7 | no (MC-003 open) | bridge | One contrast box: overlap changes what is **stored**; X1 windows and X3 assembly change what is **sent** |
| 25 | Lost in the middle: a longer equal-budget context can still hurt answers | 07 I.5; MC-004 | P7 (not studied) | P7 / X3 | no | next | Link only (Source C #39); relevant to the generation table |
| 26 | "Retrieve small, generate big" (parent or window return) decouples the two sizes | AIQ 04 Q5 | — | X1 / I6 | no | next | Link: it is why I1's answer is "for retrieval", and why X1 exists |
| 27 | Transfer: the best size depends on question type **and** embedder | phase_02 [C2-7]; [I1-S3] | phase_02 research only | I1 | no | core (Full) | "An I1 result never transfers across an embedder change": rerun I1 if D-03 changes |
| 28 | The token-unit arm (D-06): which tokenizer, and why | 07 I.2 (200 WordPiece / 40) | 07 (arm only) | I1 | no | core | Label it "MiniLM-native" (WordPiece = MiniLM's tokenizer). A Cohere-native token arm needs Cohere's tokenizer, which is not available locally (UNVERIFIED) |

### 3. Quiz coverage

No question file exists for Phase 4. Needed titles (R = recall, A = application, T = transfer):
- **R-01** Why must a chunk-size comparison also be run at an equal context-token budget?
- **R-02** Why is 1.00/1.00 in `choose_chunk_size` a ceiling, not evidence that both sizes are good?
- **R-03** Which tokenizer counts the context budget, and which one counts truncation? Why are they different?
- **R-04** What does `dup_frac` measure, and which metric rewards duplication (Precision/nDCG), punishes it (IoU) or ignores it (CE)?
- **A-01** Given mean chunk tokens per arm and B, compute k by floor and by rounding, and the realized budget error. (★ The 1500-char arm: k = 2 gives −32%, k = 3 gives +1%.)
- **A-02** Given per-arm span lists, find the duplicate arms and the number of distinct arms m. Then compute 1 − 0.95^m.
- **A-03** Given per-question CE@4 for v0 and three shortlisted arms on 16 dev items, list b/c against v0 and apply the pre-registered rule, including the tie rule.
- **A-04** Count the informative items (CE differs across arms) in a 6-arm × 10-item table.
- **T-01** Your 34-arm grid's best dev arm is +0.19 CE@4 on 16 items. Write the next three steps. (Key: winner's curse, the shortlist, one paired test touch, "inconclusive" allowed.)
- **T-02** A colleague switches the embedder from Cohere to MiniLM and reuses the I1 champion. What do you check? (Key: truncation rate, rerun I1, [I1-S3].)
- **T-03** A new corpus has 600-character pages. Which grid arms are pointless under per-page scope, and why?
- **Interview (derived from AIQ 04 Q5 and Q33, MIT; Q5 itself is already C2-R-06):** "You tuned chunk size on a small golden set and the best setting won by 12 points. How do you know it is real, and how did you keep the comparison fair?"

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| I1-E1 | 04 §2.4 I1 row vs 02 I1 card | 04 lists Ch8 p.7/11 (window size) as an I1 page; 02 does not. That page is X1's neighbour window, not chunk size. Ch6 p.9–10/14 is a Q2 length target, also not a chunk-size argument | Keep Ch1 p.10–11/14 as the I1 source; list Ch6 p.9–10/14 as "downstream (Q2)" and Ch8 p.7/11 as "next (X1)" |
| I1-E2 | 04 §2.4 `rs/choose_chunk_size.py:L23-L123` | The defaults `[128, 256]` that 07 G.4 and J2(c) rely on are at **L133**; L128–L134 is `parse_args` | Cite L23–L134 |
| I1-E3 | 07 I.1–I.4 "37-configuration grid"; 06 §9.4 "36+ configurations"; 07 I.4 test log "Configs tried: 37" | On Corpus D (approx.), 3 per-page arms are byte-identical (2000/0, /200, /400) and 2 more add only 1–2 texts (1500/150, /300). The grid has about 34 distinct arms, plus the token arm. Logging 37 overstates the hypotheses tried and wastes embeddings and statistics on duplicates | Hash each arm's span list, collapse duplicates before scoring, and log the number of **distinct** arms in `TEST_LOG.md` |
| I1-E4 | 06 §3.2 "Why this matters for v0 and v1.0"; 07 H5, J1, I.5 | Truncation is presented as a grid confound in general. Under the D-03 default (Cohere embed-v4.0, limit 8,192 per the models API or 128k per the docs [I1-S7]), a 2,000-character chunk (≈ 360 cl100k tokens, derived) cannot be truncated. Only the MiniLM fallback arm is confounded | Scope H5 to the MiniLM arm. For Cohere, record truncation = 0 with evidence (`truncate="NONE"` plus `meta.billed_units`) |
| I1-E5 | 07 I.2 token-unit configuration (200 WordPiece / 40) | WordPiece is MiniLM's tokenizer, not the default embedder's. The arm is tied to the fallback model without saying so | Label it "MiniLM-native token arm". A Cohere-native arm needs Cohere's tokenizer (publication for embed-v4.0 UNVERIFIED, phase_02 [C2-3]) |
| I1-E6 | 07 I.2 "equal context budget B tokens … tokenizer used for budget counts (named)" | No tokenizer is named, and B is "v0's mean context tokens" with no unit. The generator is gpt-oss-20b, whose encoding `o200k_harmony` is in tiktoken 0.14.0 [I1-S9] | Name `o200k_harmony` for the budget; record it in `config.yaml` |
| I1-E7 | 07 I.2 `take_within_budget` (`break`) | It stops at the first chunk that does not fit, so the realized context can be well below B and varies per query (with large chunks, often one chunk fewer). The design reports neither realized tokens nor the rule's alternatives | Pre-register `break` vs `skip`; report realized mean and p10/p90 context tokens per arm next to the metric |
| I1-E8 | 06 v1.0 card and 07 I.1 decision rule | "Choose one candidate on dev" among 34+ arms with about 16 dev items (30% of ~55, 06 §6.3) has no selection rule. A toy simulation (§5) shows a +0.16 to +0.25 winner's curse at that n, larger than 06 §9.4's MDE (0.18 at n = 50) | Add a pre-registered shortlist (≤ 3 arms from H1–H4), a tie rule, and "exploratory" labels for the rest of the grid |
| I1-E9 | phase_03 M4 step-by-step (arms 1000/200 vs 500/100, equal budget k = 8) | 500/100 is not an I1 grid value, so its cached index cannot be reused in I1 | Suggest M4 use 400/40 or 400/80 (in the grid). Its equal-budget k is then 8 (approx. B/mean = 8.7–8.9) |
| I1-E10 | 02 I1 card "Repo: cells 6, 8, 10, 12" | It omits cells 2 and 4, which carry two of the critique's points (the deprecated `DatasetGenerator`; all seven `data/` files loaded) | Cite cells 2–12, as 07 G.4 does |

### 5. What the research says

**[I1-S1] Chroma `chunking_evaluation` code** (Brandon Smith, MIT 2024; `main` @ `e708410`; `chunking_evaluation/evaluation_framework/base_evaluation.py` read in full for the metrics).
- *What the code does:*
  - Chunk offsets are found after splitting, by a fuzzy `rigorous_document_search` (L141–L147). The comment at L120–L121 admits that the metadata is wrong when a chunk repeats.
  - Recall = covered highlight characters / highlight characters (L265, L269). That is a continuous coverage, like our Span-Coverage, not sufficiency.
  - **Precision's denominator is the plain sum of the retrieved chunks' lengths** (L266), while the numerator is a union (L254). So overlapping chunks that repeat the same text lower precision and IoU (L267, L275).
  - `retrieve=5` is the default (L329). `retrieve=-1` uses an oracle k: the minimum number of chunks that holds the excerpts (L336, L405–L406).
  - The code works on **character** offsets, although the report calls the metrics token-level.
- *Limits:* offsets come from search, not from the splitter (the problem C2 fixes); there is no paired test; standard deviations print next to the means.
- *For the project:* copy one idea and nothing else. Report a **duplication-aware** diagnostic (`dup_frac`, or IoU computed with a sum denominator) next to CE@4. CE uses the union, so it neither rewards nor punishes duplication; Precision and nDCG reward it (06 §7.3). Do not install the package: it pulls in `chromadb`, `openai` and `anthropic` (`setup.py` L7–L18), and IoU takes about 20 lines of NumPy.

**[I1-S2] Chroma technical report** (Smith & Troynikov 2024). The page is blocked here; the numbers are carried from phase_02 [C2-4] (UNVERIFIED in this session).
- *Study:* 5 corpora, 472 LLM-written queries with exact excerpts, cl100k-token sizes, k = 5 fixed.
- *Result:* recall stayed in a narrow band (about 84–92%). Recursive 400/0 beat 400/200 slightly (89.5 vs 88.1 recall; IoU 3.6 vs 3.3). 800/400 had the lowest IoU (1.4). With MiniLM, overlap helped the token splitter (82.4 vs 77.1).
- *Limits:* fixed k, so size and context move together; no paired test; synthetic queries.
- *For the project:* the overlap effect is small and depends on the model, while its cost is certain. This motivates H3 ("changes CE@4 by less than a margin"), the `dup_frac` column, and the equal-budget arm.

**[I1-S3] Bhat, Rudat, Spiekermann & Flores-Herr 2025, "Rethinking Chunk Size For Long-Document Retrieval: A Multi-Dataset Analysis"** (arXiv 2505.21700; Fraunhofer IAIS). Search-checked; the code repo `fraunhofer-iais/chunking-strategies` exists (README opened at HEAD `d5fa14c`; it has install steps only, no results).
- *Study:* 6 QA datasets, fixed-size chunks of 64–1,024 tokens with no overlap, two embedders (Stella, Snowflake), Recall@k.
- *Result:* 64–128 tokens is best for short factoid answers; 512–1,024 for long, spread-out answers (NarrativeQA, NQ, TechQA). **The two embedders prefer different sizes** (Stella larger, Snowflake smaller).
- *Limits:* string-match gold favours bigger chunks at fixed k; stitched synthetic documents; no overlap arm.
- *For the project:*
  - Per-category directions (H1 vs H2) are the expected shape.
  - An I1 champion is **embedder-specific**: the Cohere and MiniLM arms may disagree, and that is a finding, not a bug.
  - Note the size scale. Our 200–2,000 characters is about 35–360 cl100k tokens (derived from 5.57 chars/token, 07 D.5), so the grid covers only the small half of what papers test.

**[I1-S4] NVIDIA technical blog, "Finding the Best Chunking Strategy for Accurate AI Responses"** (vendor; search-checked, page not opened, UNVERIFIED; phase_02 [C2-6] dates it 2025, third-party summaries say 2024).
- *Study:* token chunks of 128–2,048 with 15% overlap, plus page-level chunks; answer accuracy judged by LLMs; no retrieval metric.
- *Result:* page-level had the best average (0.648) and the lowest variance; the best token size differed per dataset.
- *For the project:* per-page scope is a strong baseline. It supports keeping v0 per-page and reading the cross-page arm as a trade-off, not an obvious upgrade.

**[I1-S5] LangChain `RecursiveCharacterTextSplitter`** (`langchain-text-splitters==1.1.3`, tag commit `e2db474`; verified).
- `base.py`:
  - L64–L69: `chunk_size=4000`, `chunk_overlap=200`, `length_function=len` (characters), `keep_separator=False` (base class), `add_start_index=False`, `strip_whitespace=True`;
  - L282/L284: `from_tiktoken_encoder` with `encoding_name="gpt2"`.
- `character.py`:
  - L101: `keep_separator=True` for the recursive class;
  - L107: separators `["\n\n", "\n", " ", ""]`.
- *For the project:* the LLMOps notebook must pass size, overlap and unit explicitly, and should never use `start_index` as gold offsets (phase_02 [C2-1], issue #29884).

**[I1-S6] LlamaIndex `SentenceSplitter`** (`llama-index-core` v0.14.25, tag commit `f12d46a`; reading only; verified).
- `node_parser/text/sentence.py`:
  - L22: `SENTENCE_CHUNK_OVERLAP = 200`;
  - L24: paragraph separator `"\n\n\n"`;
  - L83: raises when overlap > size;
  - L104: tokenizer `get_tokenizer()`.
- `constants.py`:
  - L10: `DEFAULT_CHUNK_SIZE = 1024  # tokens`;
  - L11: a second `DEFAULT_CHUNK_OVERLAP = 20`.
- *For the project:* this explains the repo script's crash. `choose_chunk_size.py` L48 sets size 128 with no overlap, so the 200-token default overlap is larger than the chunk, and L83 raises (07 J2(c), run there).

**[I1-S7] Cohere embed-v4.0 input limits.** Phase_02 [C3-1/C3-2] opened Cohere's docs (verified there): 128k context, ≤ 96 texts per call, `truncate` default `END`; the O2 models API read 8,192. This session's search (Oracle, AWS Bedrock pages) confirms 128k and shows Bedrock naming `truncate` as `NONE | LEFT | RIGHT` (search-checked, UNVERIFIED for the Cohere-native API).
- *For the project:* both limits are far above the grid's largest chunk, so the Cohere arm truncates nothing. The 8,192 vs 128k conflict stays a C3 item.

**[I1-S8] Cawley & Talbot 2010, "On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation"** (JMLR 11: 2079–2107; search-checked, page not opened, UNVERIFIED).
- *Claim:* the variance of a selection criterion matters as much as its bias. Choosing the best of many settings on a finite sample overfits that sample, and the bias can be as large as the differences between methods.
- *For the project:* this is the named result behind gap #12, and the reason the decision is made among a short pre-registered list.

**Toy simulation (helper-run, not a result about our data).**
- *Setup:* every arm has the **same** true CE = 0.6. Arms share item difficulty; each arm redraws a fraction f of its items. 20,000 repetitions, seed 0.
- *Result:*
  - At **15 items and 34 arms**, the best observed dev CE averaged 0.757 / 0.820 / 0.850 for f = 0.2 / 0.5 / 1.0, against a true 0.600. P(the best looks ≥ 0.10 above the truth) = 0.72 / 0.95 / 1.00.
  - With 6 arms: 0.693–0.756.
  - With 1 arm: 0.601.
  - At 50 items and 34 arms: 0.687–0.742.
- *What it means:* "pick the max on dev" will always look like a win at this n. The single test touch must be a **paired** comparison against v0, and "inconclusive" is the expected verdict.

**[I1-S10] The one-standard-error rule** (Breiman et al. 1984; Hastie, Tibshirani & Friedman, *ESL*, cross-validation section; not opened, UNVERIFIED): among settings whose score is within one standard error of the best, choose the simplest. Adapted here: among shortlisted arms not separable from the best on dev, choose v0, or the arm with the fewest chunks.

**Helper grid measurements (approx., pdftotext text; re-measure on PyMuPDF):**

| Scope | Size | Overlap 0 / 10% / 20%: #chunks | Mean chars (20% overlap) | Stored / original at 20% | Chunks spanning 2 pages (20%) |
|---|---|---|---|---|---|
| per page | 200 | 431 / 441 / 462 | 159 | 1.028 | 0 |
| per page | 400 | 211 / 214 / 220 | 345 | 1.059 | 0 |
| per page | 800 | 106 / 108 / 120 | 663 | 1.111 | 0 |
| per page | 1000 | 102 / 103 / 103 | 750 | 1.080 | 0 |
| per page | 1500 | 71 / 71 / 71 | 1,014 | 1.006 | 0 |
| per page | 2000 | 65 / 65 / 65 (identical sets) | 1,101 | 1.000 | 0 |
| cross page | 1000 | 93 / 99 / 99 | 785 | 1.085 | 34 |
| cross page | 2000 | 47 / 48 / 54 | 1,402 | 1.058 | 37 |

- Totals: 5,916 chunk embeddings over 36 configs; **2,323 unique texts**; about 1.02 M unique characters (≈ 184k cl100k tokens at 5.57 chars/token, derived).
- Equal budget at B = 4 × 750 = 3,000 characters (≈ 540 cl100k tokens):

| Size (20%) | Mean | k (floor) | Realized vs B | k (round) | Realized vs B |
|---|---|---|---|---|---|
| 200 | 159 | 18 | −2% | 18 | −2% |
| 400 | 345 | 8 | −8% | 9 | +3% |
| 800 | 663 | 4 | −12% | 5 | +10% |
| 1000 | 750 | 4 | 0% | 4 | 0% |
| 1500 | 1,014 | 2 | −32% | 3 | +1% |
| 2000 | 1,101 | 2 | −27% | 3 | +10% |

**Current practice (2024–2026).**
- Sizes are tuned per corpus against a span-gold retrieval set.
- Recursive or token splitters at about 256–512 tokens with 10–20% overlap are the usual starting point (AIQ 04 Q5).
- Page-level or section-level units are strong baselines [I1-S4].
- Teams increasingly decouple the retrieval unit from the generation unit: small chunks for matching, a parent or window for answering (AIQ 04 Q5; X1, I6).
- Fixed-k comparisons are still the norm in published studies [I1-S2, I1-S3, I1-S4]. That is the confound I1 removes.

**Pitfalls, with evidence.**
- Fixed k only (all three studies).
- The grid winner's curse (toy; [I1-S8]).
- Duplicate arms (helper measurement).
- Realized overlap far below nominal (1.08 vs 1.25; 07 D.4).
- The budget counted with the wrong tokenizer (07 D.6).
- A ceiling from synthetic questions (repo cell 12).
- Offsets found by search ([I1-S1] L120; phase_02 [C2-1]).
- Embedder-specific optima [I1-S3].

**How to evaluate.**
- Primary: CE@4 at fixed k **and** at equal budget (06 §4.1 rule 2).
- Diagnostics: MRR@10, Span-Coverage@4, Hit@4, `dup_frac`, and realized context tokens.
- Ops: #chunks, distinct-arm flag, embed calls, cold build time, and the truncation rate (MiniLM arm).
- Statistics: discordant pairs and the group bootstrap against v0, taken from M4 (06 §9.3).
- Generation: only for v0 plus the shortlisted arms, deterministic checks plus about 10 read answers (D-10).

**Interview questions:**
1. AIQ 04 Q5, size and overlap starting points, and why tune them.
2. AIQ 04 Q33, near-duplicates and overlap redundancy in top-k.
3. Derived: "36 chunk configs on a 16-question dev set; the best is +12 points. Ship?"
4. Derived: "Your chunk size is 512. Characters or tokens, and which tokenizer?"
5. AIQ 04 Q43, which retrieval metrics, and what each misses.

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).**
Chunk size has no correct value; it trades dilution (a fact buried in a big chunk) against fragmentation (evidence split across small ones), so you measure it on your own questions. Because a smaller chunk at the same k also sends less text, every comparison is run twice: at fixed k and at an equal token budget, where k = budget ÷ mean chunk tokens is chosen per arm. A grid of 36 settings is 36 chances for luck, so you first remove arms that produce identical chunks, then decide among two or three arms you predicted in advance, and treat the rest of the grid as a picture, not a verdict. The chosen arm is confirmed once on test against v0, question by question, and with about 50 questions "inconclusive" is a normal answer. A 1.00/1.00 score like the repo's is a ceiling: the test was too easy to tell the arms apart, so it says nothing about which size is better.

**The theory in one read (11 ideas, each with its formula).**
1. *Two failure modes:* dilution (rank falls as unrelated text grows; the 07 D.7 toy `cos = 1/√(1+n²)`) vs fragmentation (CE needs every group: `CE = Π_g 1[group g covered]`).
2. *Coupling:* context characters ≈ k × mean chunk length; at k = 4, 400-char chunks carry about 46% of v0's text (approx.).
3. *Equal budget:* `k_arm = B / mean_tokens_arm`. State the rounding rule, or pack per query with `take_within_budget` and report realized tokens, since a fixed integer k can miss B by −32% (1,500-char arm by floor).
4. *Two tokenizers:* budget tokens use the generator's encoding (`o200k_harmony`); truncation uses the embedder's own (`trunc_rate = #chunks with n_tok > max_seq / #chunks`).
5. *Realized overlap:* `stored/original` is 1.08 at nominal 1000/200, against the fixed-window `S/(S−O)` = 1.25. At large per-page sizes it is 1.00.
6. *Duplicate arms:* `arm_id = sha256(span list)`. Distinct arms m ≈ 34 of 36 (approx.).
7. *Duplication in top-k:* `dup_frac = 1 − |∪ spans| / Σ |span|`. CE ignores it, Precision/nDCG reward it, IoU punishes it.
8. *Many comparisons:* `P(any false win) = 1 − (1−α)^m` (m = 34 → 0.83 at α = 0.05). The winner's curse grows as n falls (toy: +0.16 to +0.25 at 15 items).
9. *Selection design:* ≤ 3 pre-registered shortlist arms (from H1–H4) decide; the full grid is exploratory; ties go to v0, or the cheaper arm (one-SE idea).
10. *Information per item:* only items whose CE differs across arms can rank arms. `informative = #{q : max_arm CE − min_arm CE > 0}`. Ceiling items (all 1) and floor items (all 0) are excluded from interpretation, and the floor items' gold spans are re-read.
11. *Transfer:* the optimum depends on question category and embedder [I1-S3]. A D-03 change means rerunning I1.

**Formula-sheet items:**
- k at equal budget, with rounding and the realized error;
- `dup_frac`;
- stored/original;
- `trunc_rate`;
- `1 − (1−α)^m`;
- the informative-item count;
- the D.3 containment `min(1, (S−F+1)/(S−O))` (a link back to C2);
- M4's sign test and MDE (link only).

**Step-by-step outline.** Running example: the climate PDF (Corpus D), frozen snapshot `ea07572562ac`, the M1 eval set's dev split. No other data is needed: the concept is tuning on this corpus.
1. **Recall C2 in 5 minutes.** v0 = 1000/200 per page, 97 chunks; per-page scope; the truncation table. Ask Yash to predict which way H1 and H2 go.
2. **Read `choose_chunk_size` as an anti-example** (cells 6–12): what each uncontrolled variable would need. Reuse 07 G.4's table; do not repeat it.
3. **Pre-register** H1–H4 (plus H5 for the MiniLM arm only), the shortlist (proposed: 400/40 per page for H1; 1000/200 cross page for H4; 1000/0 per page for H3), the budget rule, the tie rule and the tolerances, committed before running.
4. **Build all arms.** Count chunks, hash the span lists, collapse duplicates (show that per-page 2000/0, /200 and /400 are one arm), record stored/original and the truncation rate per embedder.
5. **Fixed-k run on dev.** CE@4 heatmap (size × overlap, one panel per scope); MRR@10 beside it; `dup_frac` column.
6. **Equal-budget run on dev.** Pick B from v0's mean context in `o200k_harmony` tokens, pack per query, and report realized tokens. Recompute the heatmap. Where a fixed-k gap disappears, the cause was context volume.
7. **Decide on the shortlist only:** b/c against v0 and the M4 group bootstrap; apply the tie rule. Show the toy winner's curse next to the exploratory grid's best arm.
8. **Ceiling and floor check:** the informative-item count; re-read the all-zero items (review L247).
9. **One test touch** for the chosen arm against v0. Log it in `TEST_LOG.md` with m = distinct arms. The verdict is supported, not supported, or inconclusive.
10. **Generation for v0 plus the shortlisted arms** on dev: deterministic checks plus about 10 read answers (D-10); a separate table.
11. **Write the decision with costs:** #chunks, embed calls, build time, mean context tokens, "when NOT to use".

**Visuals that earn their place:**
- *Coupling diagram:* the same 3,000-character budget filled by 18 small, 4 medium or 3 large chunks. Shows why fixed k is unfair.
- *Heatmap pair (fixed k | equal budget)*, size × overlap, with duplicate cells hatched. Shows the main effect and which effects are only context volume.
- *Realized-overlap bar:* nominal vs realized stored/original per size. Shows that overlap arms at large per-page sizes are not real.
- *Winner's-curse plot:* best observed CE against the number of arms, for n = 16 and 50, with the true value marked. Shows why the grid is not the decision.
- *Discordance strip* for the shortlist against v0 (reused from M4's visual).

**Full only:**
- the Chroma IoU definition and its sum denominator;
- `break` vs `skip` packing;
- the cross-page citation cost;
- the MiniLM 128-token training length;
- the embedder-disagreement study [I1-S3];
- the NVIDIA page-level result (vendor);
- the token-unit arm and the missing Cohere tokenizer;
- successive or coarse-to-fine designs (size first at the shortlist overlap, then overlap around the winner) and why they still need the one-touch test;
- the CE@k curve over k = 1…10 per arm, as a description only.

### 7. Verify notebook plan

`study/notebooks/I1_chunk_grid_verify.ipynb`. Offline, with no API calls by default.
1. **Grid facts on the PyMuPDF snapshot.** Use the C2/C3 given chunker (06 block, `params_hash` per arm). Assert:
   - v0 = 97 chunks;
   - per-arm #chunks, mean, min/max and stored/original;
   - the cross-page page-spanning counts.
   These replace the helper's pdftotext approximations.
2. **Duplicate arms.** Hash every span list. Assert which arms collapse (expected from the approximation: per-page 2000/0, /200, /400) and print m. Report unique texts across arms (approx. 2,323) and the cache hit rate a first run would see.
3. **Realized overlap.** Real overlap per adjacent pair (C2 lab Task 8 method) per arm, against nominal.
4. **Budget arithmetic.** Count tokens per chunk with tiktoken `o200k_harmony` and with cl100k (to show the difference). Compute B from v0 at k = 4. Print the k floor/round table and the realized error. Test `take_within_budget` against hand toys, including `break` vs `skip`.
5. **Truncation per embedder.** MiniLM WordPiece counts per arm (re-measuring 07 D.6 on PyMuPDF text). Cohere: the derived maximum against 8,192, which asserts truncation = 0.
6. **Duplication metric.** On a 3-chunk toy with overlap, CE = 1, Precision@3 = 1 and `dup_frac` > 0; the IoU with a sum denominator drops. Cross-check one case against a hand port of Chroma L254–L275 [I1-S1].
7. **Winner's-curse simulation** (the §5 toy; NumPy, seeded, about 5 s). Assert that the 1-arm case is unbiased within 0.01.
8. **Real offline grid** (once the M1 dev split exists): MiniLM, exact cosine, CE@4 / MRR@10 / Span-Coverage@4 at fixed k and at equal budget for all distinct arms. Heatmaps with Plotly. The informative-item count. All-zero items listed.
9. **Optional, cached:** the same with Cohere `embed-v4.0` (§9 call counts), replayed from the cache.

- **Runtime:** about 1–3 minutes on CPU. MiniLM over about 2,323 unique chunks, derived from C3's 97-chunk cold embed of 1.8–6.3 s, so roughly 45–150 s.
- **Network:** tiktoken downloads its BPE file once; cache it (`TIKTOKEN_CACHE_DIR`, UNVERIFIED path) so later runs are offline.

### 8. Apply-it tool plan and real-world checklist

`study/tools/chunk_grid_check.py`: "Which chunk size suits MY documents and questions, and can my question set even tell the sizes apart?"
- **Inputs:**
  - `--docs` (PDF, MD or TXT);
  - `--questions q.jsonl` (`q`, `expect` quote or span, optional `category`, `group`);
  - `--sizes`, `--overlaps`, `--scope per_page|cross_page|both`, `--unit chars|tokens`;
  - `--embedder minilm|cohere` (Cohere through the cache only);
  - `--k 4`, `--budget auto|N`, `--budget-tokenizer o200k_harmony`;
  - `--baseline 1000/200/per_page`, `--shortlist ...`, `--report out.md`.
- **Outputs (Markdown plus a Plotly HTML):**
  - the arm table (#chunks, distinct-arm id, stored/original, realized overlap, truncation rate, embed calls);
  - fixed-k and equal-budget CE/Hit/MRR with realized tokens;
  - `dup_frac`;
  - the informative-item count;
  - b/c against the baseline for the shortlist;
  - the winner's-curse warning with m and n;
  - the checklist and a recommendation.
- Like `bm25_fit_check.py`, it is not an evaluation. With a handful of labelled questions it shows the mechanism and how much the set can resolve.

**Real-world checklist (12 checks):**

| # | Check | Auto / manual |
|---|---|---|
| K1 | Unit named for size, overlap and budget; the budget tokenizer is the generator's | auto (config) |
| K2 | Duplicate arms collapsed; m (distinct arms) reported | auto |
| K3 | Realized overlap reported next to nominal; arms with realized ≈ 0 flagged | auto |
| K4 | No chunk over the embedder's limit (its own tokenizer), or the truncation rate is reported per arm | auto |
| K5 | Fixed-k **and** equal-budget results both shown; realized mean tokens within ±10% of B | auto |
| K6 | `dup_frac` shown; arms where duplication eats > 20% of the context flagged | auto |
| K7 | Informative items ≥ 10, else "this question set cannot rank the arms" | auto |
| K8 | Items with CE = 0 under every arm listed for a gold re-read | auto + manual (read the spans) |
| K9 | Decision made among ≤ 3 pre-registered arms; the rest labelled exploratory | auto (shortlist flag) + manual (pre-registration predates the run) |
| K10 | Discordant counts against the baseline, with the M4 interval; "inconclusive" when the interval spans 0 | auto |
| K11 | Per-category directions shown with n; none used for the decision | auto |
| K12 | Page length vs size: share of pages shorter than the size (per-page arms collapse) | auto |

**Recommendation logic:**
- K1 or K4 fails → "fix units or truncation first; results confounded".
- K7 fails → "questions too easy or too few: add harder multi-span items before tuning".
- K5 or K6 shows the gain vanishes at equal budget → "the win is context volume: raise k (or use X1), not chunk size".
- A shortlist arm is supported → "adopt; confirm once on held-out questions".
- Otherwise → "keep the baseline; record inconclusive".

### 9. LLMOps notebook plan

`study/llmops/notebooks/I1_chunk_grid_ops.ipynb`: the grid run as a traced, replayable experiment (foundation §12 row "4 · I1–I3").
- **Framework build:**
  - `langchain-text-splitters` `RecursiveCharacterTextSplitter` (explicit `chunk_size`, `chunk_overlap`, `length_function=len`, `add_start_index=True`) next to the course chunker, for each shortlisted arm. A span-diff table shows boundaries moved by `strip_whitespace=True`, real overlap, and any `start_index` that differs from the course offsets ([I1-S5]; foundation §9.2).
  - Retrieval runs through `CachedEmbeddings` (foundation §9.3) and a plain NumPy retriever. No LangChain retriever, because its default k = 4 would hide the equal-budget k.
  - LlamaIndex appears in a read-only cell only, to explain the 200-token default overlap crash [I1-S6].
- **External calls (all cached; replay runs with no key):**

  | Call | Count | Notes |
  |---|---|---|
  | Cohere `embed-v4.0`, `search_document` | **≈ 45 calls** (≈ 2,323 unique texts at ≤ 96 per call; 83 without the content cache), plus about 2 for the token arm | Approx. counts; ≈ 184k cl100k tokens (Cohere's own count UNVERIFIED); price UNVERIFIED; within the trial cap of 1,000 calls/month; the 2,000 inputs/min limit means a throttle and about 2 minutes |
  | Cohere `embed-v4.0`, `search_query` | 1 call (≤ 96 questions, shared by every arm) | Query vectors are identical across arms |
  | Groq `openai/gpt-oss-20b` generation | v0 is already cached from v0.1. 3 shortlist arms × ~16 dev items ≈ **48 calls**, plus the test touch for 1 arm × ~20 items ≈ 20 → **≈ 70 calls** | ≈ 70 × (1,500 × 0.075 + 512 × 0.30)/10⁶ ≈ **$0.02**. About 140k tokens, which fits one day of the 200K TPD free tier (plan UNVERIFIED); at least 18 minutes at 8K TPM |
  | Claude Haiku 5.5 (optional comparison only) | not planned | Changing the generator would be a new arm (foundation §6.4) |
  | Judge | **0** (D-10) | Stored traces feed the end batch |

  MiniLM runs locally (no API) and its vectors are content-cached as in C3.
- **Tracing:**
  - The run root holds `run_id`, `config_hash`, the **list of arms with `params_hash` and the distinct-arm id**, `dataset_sha256`, `snapshot_id`, `split`, `cache_mode` and the git commit.
  - One retrieval span per (arm, qid) carries the ranked `chunk_id`s with scores and ranks, `k_used`, `budget_tokens`, `realized_tokens`, `dup_frac` and CE/MRR. That is about 34 × 16 ≈ 540 spans on dev.
  - One embedding span per arm carries cache hits and misses and the truncation count.
  - One index-build span per arm carries #chunks, cold build time and embed calls.
  - The local default is the JSONL trace, viewed in Phoenix (`uvx arize-phoenix@20.19.0 serve`).
  - LangSmith: **Corpus D only**, inside `tracing_context(enabled=True)` after `privacy.assert_corpus_is("D")`. About 600 traces fit the free plan's 5k/month.
- **Dataset and evaluators:**
  - the M1 golden set (dev for selection, test once);
  - Tier-1 evaluators: CE@4, Span-Coverage@4, Hit@4, MRR@10, `dup_frac`, realized tokens (foundation §5);
  - for the shortlist, generation checks: EM/F1 on short answers, citation page-hit, abstention string, `finish_reason = length`;
  - human reading of about 10 answers per arm.
  - `langsmith.evaluate(..., upload_results=False)` is shown once as the framework view.
- **Experiment against the previous version:**
  - v0 (E000) against each shortlist arm, at fixed k and at equal budget, through M4's `compare_runs.py`, with identical comparison keys;
  - the exploratory grid stored under `experiments/E010_v1.0_chunk_grid/grid/<params_hash>/`;
  - `TEST_LOG.md` records m.
- **Cost, latency and tokens:**
  - index-build cost per arm (embed calls, cold seconds; "cost if called" against "paid" = 0 on replay);
  - query p50/p95 per stage (should be flat at this scale; 06 v1.0);
  - context tokens per query per arm (the main cost lever).
- **Prompt and config versioning:**
  - one `config.yaml` per arm, its `params_hash` from the 06 block (unit, scope and tokenizer included);
  - the budget rule and tokenizer recorded;
  - the prompt `answer_v1` unchanged (one variable).
- **Monitoring and feedback:**
  - Champion regression test (T1): CE@4 and MRR ≥ champion − tolerance on cached embeddings or MiniLM, plus a **cap on worsened qids** (M4-E5).
  - A grid manifest test: distinct arms really are distinct, and `params_hash` values are unique.
  - An embedding canary before any re-run (foundation §8.4).
  - Alerts: champion CE@4 drop, a new embedder fingerprint, a nonzero Cohere truncation count, or realized tokens drifting past ±10% of B.
  - Items the champion breaks go to the M5 log and then to the golden set (`ci-cd-evals`, `error-analysis`).
- **Place in the lifecycle:**
  - Analyze: v0.1 buckets name dilution or fragmentation (`error-analysis`, `trace-data-analysis` for per-arm patterns).
  - Measure: the grid (`rag-evaluation`, `code-based-evaluators`).
  - Improve: adopt or keep v0 (`improving-llm-agents` for the cost side).
  - dev → CI: the champion regression test (`ci-cd-evals`).
  - Tracing: `llm-observability`.
  - Lifecycle framing: `evals-foundations`.

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Course chunker, grid runner, budget packing, `dup_frac`, IoU | own code (C2 chunker, M2 metrics, M4 statistics) | — | — | yes | — | — | yes |
| Arrays, simulation | `numpy` | 2.5.3 | yes | yes | — | BSD-3 | yes |
| Sign test | `scipy.stats.binomtest` | 1.18.1 | yes | yes | — | BSD-3 | yes |
| Budget and diagnostic tokens | `tiktoken` (`o200k_harmony` for gpt-oss; cl100k for comparison) | 0.14.0 | yes | after one BPE download | — | MIT | yes |
| Local embedder (fallback arm, truncation arm) | `sentence-transformers/all-MiniLM-L6-v2` via `sentence-transformers` | 6.1.0 | yes | yes (HF cache) | — | Apache-2.0 | yes (D-03 fallback) |
| Default embedder | Cohere `embed-v4.0` via `cohere` | 7.2.0 | yes | replay only | ≈ 45 + 1 calls per full grid (approx.); price UNVERIFIED | MIT (SDK) | yes (D-03); Corpus D text leaves the machine (allowed) |
| Generation for the shortlist | Groq `openai/gpt-oss-20b` (`reasoning_effort=low`) | from `.env` | SDK yes | replay only | ≈ 70 calls ≈ $0.02 | — | yes (D-04) |
| Claude | not needed for I1 (no high-volume LLM step) | — | no | — | 0 | — | yes (D-32 allows; not worth it) |
| Plots | `plotly` heatmaps | locked | yes | yes | — | MIT | yes |
| Splitter comparison | `langchain-text-splitters` | 1.1.3 | no | yes | — | MIT | yes (LLMOps only) |
| Framework core (adapter base classes) | `langchain-core` | 1.6.6 | no | yes | — | MIT | yes (foundation §11) |
| LangGraph | not needed (a linear grid, no cycles) | — | — | — | — | MIT | n/a |
| Provider integrations | `langchain-cohere` / `langchain-groq` **not used** (pin conflicts) | — | no | — | — | MIT | adapters instead (foundation §9.3) |
| Hosted tracing | `langsmith` | 0.14.4 | no | no | free plan, ≈ 600 traces per grid | MIT (SDK) | yes, Corpus D only |
| Local tracing | `arize-phoenix-otel` 0.17.2 + server via `uvx arize-phoenix@20.19.0` | — | no | yes | — | Apache-2.0 / ELv2 | yes |
| Reading only | `llama-index-core` `SentenceSplitter` | 0.14.25 (GitHub) | no | — | — | MIT | read on GitHub; do not install |
| Reading only | Chroma `chunking_evaluation` @ `e708410` | — | no | — | — | MIT | read only; it pulls `chromadb`, `openai`, `anthropic` |
| Optional Holm correction | `statsmodels.stats.multitest.multipletests` | 0.15.0 | no | yes | — | BSD-3 | optional (M4 row) |

**Install lines (do not run):** `uv add --group llmops langchain-core==1.6.6 langchain-text-splitters==1.1.3 langsmith==0.14.4 arize-phoenix-otel==0.17.2`. These are the foundation §11 pins; nothing new is needed for the lesson or the verify notebook.

**Keys:**
- `COHERE_API_KEY` (present), to record the grid once;
- `GROQ_API_KEY` (present), for the shortlist generation;
- `LANGSMITH_API_KEY` only if the hosted view is wanted.
After recording, no keys are needed.

### 11. Open questions for Yash (preferences only)

1. Before v1.0, will you grow the dev split from about 16 to about 30 items, so the shortlist decision can resolve gaps of about 0.23 instead of about 0.31? (MDE ≈ 2.8·√(b+c)/n with 20% of items discordant; toy arithmetic, M4's formula.) **grow / keep**
2. Should the exploratory grid embed every distinct arm with Cohere (about 45 calls, recorded once), or only the shortlist with Cohere and the rest with MiniLM? **all / shortlist** (all recommended: cheap, and it keeps one embedder across the heatmap)

---

## Concept I2: Structure-aware chunking

### 1. Sources checked

**Book (not present in this session; nothing re-opened, all UNVERIFIED).** No chapter teaches I2. The nearest pages, per the course files:
- Ch7 p.1–2/11: chunks lose their headings (per 07 source map and 07 D.8; not re-opened, UNVERIFIED).
- Ch7 p.8/11: richer headers with a section path (per 04 §2.4 and §3 Ch7; not re-opened, UNVERIFIED).
- Ch9 p.10–11/14: where chunking strategies sit on a spectrum (per 02 I2 card and 04 §3 Ch9; not re-opened, UNVERIFIED). DV-B12 applies: the spectrum also lists the context window, which is not a chunker.
- Ch14 p.4–5/13: summarise each logical section (per 04 §3 Ch14 step 1; 02 cites p.4–5/13, 04 §2.4 cites only p.4/13; not re-opened, UNVERIFIED).

**Repo (`NirDiamant/RAG_Techniques` @ `009adba2…`, downloaded to my scratch folder; verified).**
- `all_rag_techniques/simple_rag.ipynb` cell 10: `encode_pdf` builds `RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, length_function=len)` and calls `split_documents` on `PyPDFLoader` pages. No `separators` argument, so the library defaults are used. Verified.
- `helper_functions.py` L48–L76: the same `encode_pdf` (L48 `def`, L76 `return vectorstore`). Verified. 03's citation is correct.
- `all_rag_techniques/hierarchical_indices.ipynb` cell 11: one summary per `PyPDFLoader` page, so a **page stands in for a section**. This is the only "section" logic upstream. Verified.
- README technique list: no structure-aware, heading or Markdown-header notebook exists. Verified (grep of README).
- The climate PDF bytes match the lock file (sha256 `1d58a0fa…92669`, 206,372 bytes). Verified.

**Corpus D structure (new facts; my own stdlib-only inspection of the raw PDF, no PyMuPDF; approximate, to be recounted with PyMuPDF in the verify notebook) [I2-S17].**
- Producer and creator: Microsoft Word 2021. The PDF is **tagged** (`/StructTreeRoot`, `/MarkInfo <</Marked true>>`).
- **No `/Outlines` object**, so `Document.get_toc()` should return `[]` (inferred from the source of `get_toc`, which returns `[]` when `doc.outline` is empty [I2-S1]; not run).
- Fonts: `TimesNewRomanPS-BoldMT` (resource F1), `TimesNewRomanPSMT` (F2), one Calibri run.
- Font sizes of the bold font, and what they hold:

  | Size (pt), bold | Lines (after joining hyphen runs) | What they are | Structure tag count |
  |---|---|---|---|
  | 24 | 1 | the title "Understanding Climate Change" | H1: 1 |
  | 18 | 22 | 21 chapter headings "Chapter N: …"; Chapter 5's heading wraps onto a second line ("Mitigation") | H2: 21 |
  | 13.56 | 68 | section headings ("Historical Context", "Greenhouse Gases" …) | H3: 68 |
  | 12 (= body size) | 192 | sub-headings ("Coal", "Oil", "Paris Agreement" …), bold only | H4: 1 (the rest look tagged as P) |

- Body text is regular Times at 12 pt (about 1,660 text-setting operators). So **192 of 282 headings (68%) differ from body text only by boldness, not by size.**
- Eleven heading titles repeat across chapters, for example "Paris Agreement" (sub-heading on p.10 under Chapter 6 and on p.23 under Chapter 16), "Smart Grids" (p.8, p.22), "Marine Ecosystems" (p.5, p.13), "Youth Engagement" (p.13, p.32), "Carbon Capture and Utilization" (p.8, p.23). "International Agreements" is a sub-heading on p.6 but a section heading on p.23. These are exactly 06's near-duplicate distractor topics.
- The 16 pages that LAB_FACTS §7 says end in an orphaned heading (1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 17, 18, 20, 27, 30, 31) all carry a bold heading in my page map. Consistent, but not a re-measurement.
- Some headings are written as three text runs around a hyphen ("Nature", "-", "Based Solutions"). Whether PyMuPDF merges them into one span is UNVERIFIED.

**Existing course files read:** 02 I2/I1/I-CMP cards and §4 per-technique gate; 03 rows 427–433 and §5 row 516; 04 §2.4, §3 (Ch7, Ch8, Ch9, Ch14), §5, §6; 06 §3.2, §4.1, v1.0–v1.2 cards, §4.3, §5.1–5.3, §6.1–6.3; 07 B.1–B.2, D.4, D.8, D.9, H.3, Part K; 08 Part 4 (D-06, D-08, D-17, D-32); `concepts/C1_document_parsing.md` (grep); `sources/verification/C1/C1_FACTS.md`; `sources/verification/LAB_FACTS.md` §7; `sources/verification/C2lab/C2LAB_FACTS.md` (L96); external review §5–§6; LLMOPS_FOUNDATION Summary, §2.3–2.5, §3, §4–§12; tracker; misconception log; `phase_03_measurement.md` (format).

**AE book:** nothing on structure-aware chunking in the review. The review notes that AE Ch7 promises a chunking section that is missing (per the review, not re-opened).

**Interview repo (AIQ, MIT, "Copyright (c) 2026 Om", @ `e080df2`; verified by raw download):** `04-rag-and-retrieval/questions.md` Q4 "What chunking strategies do you know, and how do you pick one?" (its "Structure-aware" bullet), Q13 (detect silent parser corruption), Q14 (chunk metadata, including embedding the heading path). The external review keeps `harvey.md` Q1 (defined terms far from their clause) as an I2/I5 reserve and rejects `harvey.md` Q7's clause chunker.

**Library source (read from the exact released files) [I2-S1–S5, S15]:** PyMuPDF 1.26.7 `src/__init__.py` (GitHub tag `1.26.7`); `pymupdf4llm` 0.2.9 wheel; `langchain-text-splitters` 1.1.3 wheel; `unstructured` 0.27.10 wheel; `docling-core` 2.99.0 wheel; `docling-slim` 2.133.0 PyPI metadata; `chonkie` 1.7.0 wheel; PyPI JSON for every pin.

**External (8 web sources, most search-checked only):** [I2-S6] Docling report · [I2-S7] Jimeno Yepes et al. 2024 · [I2-S8] NVIDIA chunking blog · [I2-S9] Shaukat et al. 2026 · [I2-S10] oil-and-gas chunking study 2026 · [I2-S11] Lavarec & Du (IJAI) · [I2-S12] Snowflake finance RAG blog 2025 · [I2-S13] financial PDF parsing and chunking 2026. List in "For the lead: sources".

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class (core / bridge / next) | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Snapshot text, document offsets, page table, `page_of` (D-17) | every chunk I2 makes | C1 lesson, C1 lab (written) | C1 | no (`not_started`) | bridge | 5-line refresher: offsets point into `doc_text`; a chunk is a slice `[a, b)` |
| 2 | Recursive splitter: separators, merge, achieved overlap ≤ requested | the fallback inside long sections | 07 D.4 (written) | C2 | no | bridge | Recall D.4's table; say which separators the fallback uses |
| 3 | Per-page vs cross-page scope; 8 mid-sentence cuts; 16 orphaned headings | the failure I2 targets | 07 D.8 (PyPDFLoader counts; not re-measured on PyMuPDF, C2LAB L96) | C2 / I1 | no | bridge | Open with the "Coal" orphan (p.1→2) and the PPP cut (p.12→13); re-measure on PyMuPDF |
| 4 | PDF text model: block → line → span; `get_text("dict")` fields `size`, `flags`, `font`, `bbox`, `origin`, `char_flags` | heading detection | **missing** (C1 uses plain `get_text()` only) | I2 | no | core | Print one real span dict from page 1; name each field |
| 5 | `flags` bit values: 1 superscript, 2 italic, 4 serif, 8 monospaced, **16 bold** | bold test | **missing** | I2 | no | core | Bit table + `flags & 16`; note synthetic bold sits in `char_flags` |
| 6 | Body font size = the size that holds the most characters | level assignment | **missing** | I2 | no | core | Character-weighted histogram of sizes on Corpus D (expect 12) |
| 7 | Heading rules: size above body (rank = level), bold at body size, numbering regex, short line without final full stop | heading detection | **missing** | I2 | no | core | Show all four rules on Corpus D; 68% of its headings need the bold rule |
| 8 | Other structure sources: outline (`get_toc`), PDF tags, Markdown/HTML markup | choosing the signal | **missing** | I2 | no | core | Decision table: TOC first if present, then typography; tags only as a check |
| 9 | Heading error modes: wrapped headings (Chapter 5), hyphen-split runs, bold lead-ins inside paragraphs, running headers, captions, two-column order, same title at different levels | eye inspection, tests | **missing** | I2 | no | core | One real example per mode where D has one; synthetic zoo for the rest |
| 10 | Aligning each heading line to an exact snapshot offset (moving cursor + `find`) | offsets preserved | **missing** | I2 | no | core | Show why: `dict` and plain text come from the same text page, but offsets exist only in plain text |
| 11 | Section tree and section path (breadcrumb) | metadata, I5 later | **missing** | I2 | no | core | Draw Chapter 6 → International Collaboration → Paris Agreement |
| 12 | Split by section, then cap by size with a recursive fallback; balanced split so no tiny tail | the algorithm | **missing** | I2 | no | core | Pseudocode + the balanced-split formula |
| 13 | Merging small sibling sections up to the cap | Corpus D sub-sections average ~250 chars | **missing** | I2 | no | core | Show the chunk-length histogram with and without merging |
| 14 | Cross-page continuation; `page_segments` for citations | v1.1 card | 07 D.9 (fields only) | C2 / C5 | no | core | A section that spans pp.12–13 becomes one chunk with two page segments |
| 15 | Heading text inside the chunk vs in metadata vs prepended for embedding | one-variable rule (v1.1 vs v1.2) | I5 not written | I5 | no | bridge | v1.1 keeps the exact slice; the breadcrumb is metadata only. Prepending is I5's experiment |
| 16 | Uneven chunk sizes break fixed-k comparisons; equal token budget | experiment design | 07 Part I, I1 (written) | I1 / M4 | no | bridge | Show the size spread; report both modes |
| 17 | Embedding truncation per chunk (06 §3.2) | merged or uncapped sections | 07 D.6 | C2 / C3 | no | bridge | T1 check: no chunk over MiniLM's 256 tokens |
| 18 | Boundary bucket and section-scoped items: definitions, frozen before the run | the comparison 02 and 06 ask for | **missing** (no such category or tag in 06 §6.2) | I2 (with M1) | no | core | Define both; derived bucket computed from the v1.0 champion's chunks before v1.1 runs |
| 19 | CE@k, Span-Coverage over the union of chunk ranges | primary metric | M2 (exposed in O1 only) | M2 | exposed | bridge | One line; CE works for any chunker because gold is a span |
| 20 | Eye-inspection protocol (10 random chunks, fixed seed, written verdicts) | 06 v1.1 card | **missing** | I2 | no | core | A printed card per chunk and a 6-item pass/fail sheet |
| 21 | Chunk-property tests: offset round trip, no section crossing unless merged or continued, cap respected | T1 | 07 H.3 tests cover fixed/recursive only | I2 | no | core | Three pytest properties, run on D and on a synthetic zoo |
| 22 | Tables kept whole; table rows never split from their header | Corpus T | **missing** (D has none) | C7 / S2 | no | next | One paragraph; unstructured and docling isolate tables by default |
| 23 | PDF → Markdown converters, then a Markdown header splitter | LLMOps arm | **missing** | I2 | no | core (LLMOps only) | Show that converted text has no offsets into the snapshot; measure the re-anchoring rate |
| 24 | Layout models (docling, unstructured `hi_res`) | when heuristics fail | **missing** | S2 / I2 | no | next | Full only: what they cost and when to reach for them |
| 25 | Transfer risk: rules tuned on one corpus fail on another | v1.1 "When NOT to use" | 06 v1.1 card (one line) | I2 | no | core | Run the apply-it tool on one T paper before trusting the D rules |
| 26 | Duplicate heading titles across chapters create near-duplicate distractors | I5, R2 | 06 §5.1 lists the topics; their headings are new | I5 / R2 | no | bridge | The Paris Agreement pair: same leaf title, different chapter paths |
| 27 | Element-type and page-level chunking as rival "structure" units | research context | **missing** | I2 | no | core (Full) | Two short study cards with their limits |

### 3. Quiz coverage

There is no question file. Needed titles:
- **R:**
  - Which span-dict field and which bit tell you a span is bold?
  - Why is the body font size estimated by character count, not by span count?
  - Why can a structure-aware chunk contain its own heading but not its parent headings?
  - What does a Markdown header splitter lose that the course chunker keeps?
- **A:**
  - Given 6 line records (size, bold, text), assign heading levels with body size 12.
  - A section of 2,300 characters with cap 1,000: give the balanced split sizes, and say why not 1,000 + 1,000 + 300.
  - Given chunk ranges and section ranges, find the chunk that breaks the "no section crossing" property.
  - Build the section path for the p.23 "Paris Agreement" sub-heading.
- **T:**
  - Corpus T has two-column papers with numbered, bold, body-size headings and a PDF outline. Which signal do you use first, and what do you check by eye?
  - v1.1 wins on the boundary bucket but loses on factual-single-span. Name two mechanisms that could cause this, and the trace you would read first.
- **Interview:** AIQ `04-rag-and-retrieval/questions.md` Q4, "What chunking strategies do you know, and how do you pick one?" (MIT, Copyright (c) 2026 Om). After the repo's answer, show the correction in §4 (E8): "best whenever structure exists" is not what the studies found.

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| I2-E1 | 03 §2 registry row 428 vs 02 I2 Pre and 03 §5 row 516 | Row 428 lists only I1 as a prerequisite. 02, 04 §2.4 and 03 row 516 all list I1 **and C1** | Add C1 to row 428 |
| I2-E2 | 02 I2 card Book line vs 04 §2.4 | Different page sets: 02 gives Ch9 p.10–11/14 and Ch14 p.4–5/13; 04 gives Ch7 p.8/11 and Ch14 p.4/13. They do not contradict; each is incomplete. 04 §3's own Ch14 table says p.4–5/13. Neither cites Ch7 p.1–2/11 (heading loss), which 07 uses | Use the union: Ch7 p.1–2/11, Ch7 p.8/11, Ch9 p.10–11/14, Ch14 p.4–5/13 (all UNVERIFIED here) |
| I2-E3 | 02 I2 Outcomes ("boundary-bucket questions"); 06 v1.1 Hypothesis ("section-scoped questions") | Neither term is defined. 06 §6.2 has no such category and no such tag | Define both (§6 below): a derived `straddles_champion` bucket plus `crosses_page` and `section_scoped` tags in a new dataset version, frozen before v1.1 |
| I2-E4 | 06 v1.1 Hypothesis ("font-size/bold spans") | On Corpus D, 192 of 282 headings are body-size bold. A size-only rule, including `pymupdf4llm`'s default `IdentifyHeaders` (sizes above the most common size only [I2-S2]), finds 90 headings and misses the 192 sub-headings | State the rule as "size rank, plus bold at body size", and test both arms |
| I2-E5 | 06 v1.1 Change ("size cap = champion size") | If the v1.0 champion is per-page, v1.1 changes two things: boundary rule **and** page scope (sections run across pages). That breaks 06 §4.1 rule 2 | Add the best cross-page v1.0 configuration as a control arm |
| I2-E6 | 03 §5 row 516 ("PDFs rarely carry reliable heading markup") | Too strong for born-digital PDFs. Corpus D is a tagged Word PDF whose H1–H3 tags match its typography (counts 1/21/68). Only the bold sub-headings are untagged | "Born-digital PDFs often carry typographic structure, and sometimes an outline or tags; scans carry none. Check per corpus" |
| I2-E7 | 07 D.8 and Part K ("16 orphaned headings") | Counted on PyPDFLoader text; C2LAB_FACTS L96 says they were not re-measured on PyMuPDF text, which v0 uses | Re-measure in the I2 verify notebook (my raw page map is consistent with the 16 pages) |
| I2-E8 | AIQ 04 Q4 "Structure-aware … Best choice whenever structure exists; the heading path alone fixes many retrieval misses" (MIT) | Overclaim. One study found recursive splitting best on editorial content [I2-S11]; NVIDIA's vendor blog found page-level best on average [I2-S8]. "Heading path fixes misses" is an I5 claim, not an I2 one | Use as a critique target in the quiz |
| I2-E9 | LLMOPS_FOUNDATION §9.2 (defaults table) | Has no row for `MarkdownHeaderTextSplitter`, which the I2 LLMOps notebook uses | Add: `strip_headers=True`; lines are stripped and re-joined with `"  \n"`; no offsets; no size cap [I2-S3] |
| I2-E10 | 06 §5.1 Corpus D row ("21 chapters (eval inventory)") | Not an error: confirmed, 21 "Chapter N:" headings at 18 pt (one wraps onto two lines) [I2-S17] | Cite the new count source |

### 5. What the research says

**What the library code actually does (verified from source).**
- **PyMuPDF 1.26.7 [I2-S1].**
  - Each span in `get_text("dict")` gets `size`, `flags`, `bidi`, `char_flags`, `font`, `color`, `alpha`, `ascender`, `descender`, `origin`, `bbox` and `text` (`JM_make_spanlist`, `src/__init__.py` L20519, fields set at L20623–L20632).
  - A new span starts whenever size, flags, font or colour change, so one heading line can hold several spans.
  - Flag bits: `TEXT_FONT_SUPERSCRIPT = 1`, `ITALIC = 2`, `SERIFED = 4`, `MONOSPACED = 8`, `BOLD = 16` (L17575–L17579). Bold comes from `fz_font_is_bold(font)`, i.e. font metadata (L18825). A font with no bold flag, or bold drawn by stroking, will not set bit 16. `pymupdf4llm` therefore also checks `char_flags & 8` [I2-S2].
  - `TEXTFLAGS_DICT` equals `TEXTFLAGS_TEXT` plus `TEXT_PRESERVE_IMAGES` (L17628–L17673). On a page with no images, `dict` and plain `get_text()` read the same text in the same order. That is what makes heading-to-offset alignment possible.
  - `Document.get_toc(simple=True)` walks the PDF outline and returns `[level, title, page]` rows. It returns `[]` when there is no outline (L5217–L5266).
- **pymupdf4llm [I2-S2].**
  - Newer releases pin PyMuPDF exactly: 1.27.2.1 needs `pymupdf==1.27.2`; 1.28.2 needs `pymupdf==1.28.2` plus `pymupdf_layout`. 0.3.3–0.3.4 need `pymupdf>=1.27.1`.
  - **The newest release compatible with our pin is 0.2.9** (2026-01-10; `pymupdf>=1.26.6`, `tabulate`; minimum version check in `versions_file.py`). It imports the classic path because PyMuPDF 1.26.7 defines `_get_layout = None` (L336).
  - `IdentifyHeaders` rounds each span's size, weights by characters, takes the most common size as body (never below `body_limit=12`), and maps up to 6 larger sizes to `#`…`######`. **Bold is not a header signal.** On Corpus D this should give `#` for 24 pt, `##` for 18 pt and `###` for 13.56 → 14 pt, and nothing for the 192 bold sub-headings (derived from the code and the D font table; not run).
  - Full-bold lines are wrapped in `**…**`, so header text arrives as `## **Chapter 1: …**`. Consecutive header lines with the same level are joined, which repairs the Chapter 5 wrap.
  - Side effect: `IdentifyHeaders` deletes `StructTreeRoot` from the document object you pass in. Open a separate `Document` for it.
  - `TocHeaders` is the alternative: it uses `get_toc()` entries and loose prefix matching. It gives nothing on D (no outline).
  - Licence: AGPL-3.0 or commercial, the same as PyMuPDF.
- **LangChain `langchain-text-splitters` 1.1.3 [I2-S3].**
  - `MarkdownHeaderTextSplitter(headers_to_split_on, return_each_line=False, strip_headers=True, custom_header_patterns=None)`.
  - It strips every line and removes non-printable characters, then joins aggregated lines with `"  \n"`. So the output is **rewritten text, with no offsets and no size cap**.
  - With the default `strip_headers=True`, the heading leaves the text and survives only as metadata.
  - `custom_header_patterns={"**": 4}` makes a whole `**…**` line a level-4 header. That is how the bold sub-headings in `pymupdf4llm` output can be caught.
  - `RecursiveCharacterTextSplitter.from_language(Language.MARKDOWN)` uses the regex separators `"\n#{1,6} "`, code fences, horizontal rules, then `"\n\n"`, `"\n"`, `" "`, `""`.
  - `add_start_index=True` finds each chunk with `text.find(chunk, …)`, so repeated text can be mis-anchored.
  - `HTMLSemanticPreservingSplitter` defaults to `max_chunk_size=1000`, `chunk_overlap=0`, and may exceed the size "to preserve semantics". It applies only to HTML (needs `bs4`).
- **unstructured 0.27.10 [I2-S4].**
  - `chunk_by_title` defaults: `max_characters` = `CHUNK_MAX_CHARS_DEFAULT = 500` (hard max; `base.py` L34); `new_after_n_chars` = `max_characters`; `combine_text_under_n_chars` = `max_characters` (`title.py` ~L240); `multipage_sections=True`; overlap 0, only on split chunks unless `overlap_all`; `isolate_table=True`; `repeat_table_headers=True`.
  - It starts a new chunk at each `Title` element, or when page/section metadata changes.
  - Weight: the base install now pulls `spacy`, `numba` and `lxml`; PDF needs the `pdf` extra (pdfminer, pdf2image…). `hi_res` needs `unstructured-inference` models.
- **docling [I2-S5].**
  - `docling` 2.133.0 = `docling-slim[standard]`, which pulls **torch, torchvision, accelerate, docling-ibm-models (layout and table models), rapidocr, scipy**…
  - `docling-core` `HybridChunker` defaults: `merge_peers=True`, `repeat_table_header=True`, and a default tokenizer of `sentence-transformers/all-MiniLM-L6-v2` (`tokenizer/huggingface.py` L93).
  - `contextualize()` joins the heading metadata and the text with `"\n"`. That is the I5 "embed the breadcrumb" idea, switched on by default.
- **chonkie 1.7.0 [I2-S15]:** `Chunk` carries `start_index`/`end_index`. It has a Markdown "chef" and a `TableChunker`. Optional; not needed.

**Studies.**
- **Element-type chunking (Jimeno Yepes et al., Unstructured, 2024) [I2-S7].**
  - *Study:* chunk SEC financial reports by element type (titles, tables, narrative) from a document-understanding model, against fixed 128/256/512-token chunks, on FinanceBench.
  - *Result:* the abstract says element-type chunking "largely" improves RAG on financial reports and avoids tuning a size. A secondary page claims 80 reports and about 50% lower indexing cost.
  - *Limits:* vendor authors; one domain; heavy tables; numbers not opened (search-checked only).
  - *For your project:* the closest published evidence for v1.1. It matters most for Corpus T tables, not for D.
- **Page-level vs section-level vs token chunks (NVIDIA blog, vendor) [I2-S8].**
  - *Study:* token, page and section chunking (sections from NVIDIA's own layout parser) on five datasets (FinanceBench, Earnings, KG-RAG, RAGBattlePacket, DigitalCorpora767).
  - *Result (secondary write-ups):* page-level had the best average accuracy (0.648) and the lowest variance. The blog also reports 15% overlap best on FinanceBench at 1,024 tokens.
  - *Limits:* vendor; metric scale unnamed; section-level numbers not seen; page not opened.
  - *For your project:* page-level is a cheap rival. The I1 per-page arm is already close to it, so v1.1 must beat the best per-page arm too.
- **Systematic comparison, six domains (Shaukat, Adnan, Kuhn, 2026) [I2-S9].**
  - *Study:* 36 chunking methods, five embedders, LLM-graded nDCG@5.
  - *Result (abstract and summaries):* content-aware methods beat naive fixed character windows (best mean nDCG@5 ≈ 0.459, "paragraph group" chunking; fixed characters below 0.244). One summary says structure heuristics beat costlier semantic methods.
  - *Limits:* LLM-graded relevance; tables not opened.
  - *For your project:* supports trying I2 before I3, and keeping a cheap heuristic.
- **Mixed results elsewhere.**
  - Oil-and-gas documents (2026): structure-aware chunking had the best top-K retrieval at lower cost; all methods failed on diagrams [I2-S10].
  - Editorial SaaS content (2,419 QA pairs): recursive chunking beat structure-aware, semantic and LLM chunking on every metric [I2-S11].
  - Financial PDF study (2026): parser choice mattered as much as chunker choice; recursive + pdfminer had the best MRR (0.655); no header splitter was in the chunk test [I2-S13].
  - Snowflake (2025, vendor): Markdown-aware chunking reportedly helped by 5–10%, with a smaller advantage once global document context was added [I2-S12].
  - All UNVERIFIED (search-checked).
  - *What it means:* there is **no consistent winner**. Structure helps when headings are reliable and the parser is good. The gain shrinks once headers are prepended (I5). This is why v1.1 is a measured experiment, and why "inconclusive" is a likely verdict on 40 items.
- **Docling technical report (2024) [I2-S6]:** layout analysis (an RT-DETR model trained on DocLayNet) plus TableFormer for tables; claims sub-second per page on CPU at 72 dpi (search-checked). This is the "layout model" route: better recovery of tables and columns, at the price of torch models.

**Current practice (2024–2026).**
- Parse to structured elements or Markdown, split by heading, cap by size, merge small neighbours, keep tables whole.
- Store the heading path as metadata, and often also prepend it to the embedded text (docling `contextualize`, AIQ Q14).
- Use the outline when it exists (`TocHeaders`); fall back to typography; use layout models for complex layouts.
- Production pipelines keep provenance (page, element ids); docling and unstructured keep `orig_elements` and provenance. Character offsets into one frozen text, as D-17 requires, are rare in frameworks. The course must build that itself.

**Pitfalls (with evidence).**
- Size-only detection misses bold body-size headings (68% on D) [I2-S2, S17].
- Wrapped and hyphen-split headings become two headings or a broken title [I2-S17].
- Duplicate leaf titles ("Paris Agreement") make the breadcrumb, not the leaf, the identity [I2-S17].
- Tiny sections become tiny chunks; average sub-section length on D is about 257 characters (72,593 / 282; derived).
- Framework output cannot be scored with span gold without re-anchoring [I2-S3].
- Mutating a shared `Document` (`IdentifyHeaders`) [I2-S2].
- Tuning rules on D and assuming they hold for T.

**How to evaluate.**
- Primary CE@4 on dev, at fixed k **and** equal token budget, against v0, the v1.0 champion and the best cross-page v1.0 arm.
- Report by bucket: `straddles_champion` (derived), `crosses_page`, `section_scoped`, plus the 06 categories with n.
- Guard metrics: factual-single-span CE@4, MRR, mean context tokens, chunk count, size spread, truncation rate.
- Eye inspection before any metric; the heading-recall check (§7) before any CE.

**Interview angle.**
- AIQ 04 Q4 (strategies and how to pick one).
- AIQ 04 Q14 (what metadata per chunk, and what belongs inside the embedded text).
- AIQ 04 Q13 (detect silent parse corruption).
- "How do you chunk a PDF with no markup?"
- "How would you show that structure-aware chunking helped?"

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).** Structure-aware chunking cuts a document where its author cut it: at headings, sections and their continuation across pages, instead of every N characters. In a PDF the structure has to be recovered from typography (larger or bold lines become headings, their size rank becomes the level), or from the outline when one exists. The chunker builds a section tree, emits one chunk per section, splits long sections with the recursive fallback, merges tiny neighbours, and keeps every chunk an exact slice of the frozen snapshot, so span gold and citations still work. On the climate PDF this repairs 16 orphaned headings and 8 page-cut sentences, but 68% of its headings are bold body-size lines, so a size-only detector would miss most of them. Whether it actually retrieves better is an experiment: compare it with the v1.0 champion at fixed k and equal token budget, by bucket, and expect "inconclusive" on a small set.

**The theory in one read (11 ideas).**
1. *The text model:* page → blocks → lines → spans; span = (text, size, flags, font, bbox).
2. *Bold:* `bold(span) = (flags & 16) ≠ 0 or (char_flags & 8) ≠ 0`.
3. *Body size:* b = argmax_s Σ_{spans with round(size) = s} len(text.strip()).
4. *Heading levels:* the sizes above b, sorted from largest down, get levels 1, 2, …; a line that is all bold at size b gets the next level; optional numbering (`^Chapter \d+:`, `^\d+(\.\d+)*\s`) gives level = depth.
5. *Line filters:* a heading line is short (≤ 12 words, a [P] value), has no final full stop, is not a running header (repeats on ≥ 3 pages), and is not inside a table.
6. *Joining:* consecutive heading lines with the same level and style are one heading (the Chapter 5 wrap).
7. *Alignment:* for each heading line in reading order, `pos = doc_text.find(line_text, cursor)`, then `cursor = pos + len(line_text)`. Every heading must be found; otherwise stop (fail closed).
8. *Section tree:* section(h) = [start(h), start(next heading with level ≤ level(h))); path(h) = the titles on the stack.
9. *Split rule:* for each section at the split level L, with length ℓ and cap C: if ℓ ≤ C, one chunk; else n = ⌈ℓ/C⌉ pieces with target ⌈ℓ/n⌉, cut at recursive separators. Chunks never cross a split-level section boundary.
10. *Merge rule:* while two adjacent sibling sections are each below m (min size) and together ≤ C, merge them; the merged chunk's path is the parent's path, and `merged = true`.
11. *Invariants:* `doc_text[a:b] == text` for every chunk; spans tile the document with no gaps (zero overlap inside a section unless set); `b − a ≤ C`; every chunk lies inside one section unless `merged`; `page_segments` reconstruct `[a, b)`.

**Formula sheet items:** bold test; body-size argmax; level map; section span; balanced split n = ⌈ℓ/C⌉, target ⌈ℓ/n⌉; merge condition; `straddles(alt, chunks) = ¬∃ c: alt ⊆ [c.a, c.b)`; equal-budget k per arm (from I1); the three invariants.

**Step-by-step outline (running example: Corpus D, PyMuPDF 1.26.7 snapshot `ea07572562ac`).** Corpus D is the right first corpus here: it has clean typographic structure, four levels and known page-break failures. Corpus T is then the transfer test.
1. **The failure.** Page 1 ends with the heading "Coal"; its paragraph starts page 2 (LAB_FACTS §7). The PPP sentence crosses pp.12→13. Show both per-page chunks.
2. **Look inside the PDF.** Print the span dicts of page 1's first 10 lines: size 24 title, 18 chapter, 13.56 section, 12 bold "Fossil Fuels", 12 regular body.
3. **Find the body size.** Character-weighted histogram, so b = 12.
4. **Detect headings, three ways.** (a) size only, (b) size + bold-at-body, (c) PDF tags (read-only check). Show counts per level against the expected 1/21/68/192, and the 192 that (a) misses.
5. **Fix the error modes.** Join the Chapter 5 wrap. Check whether "Nature-Based Solutions" arrives as one span. List the 11 repeated titles.
6. **Align to the snapshot.** Cursor search; assert all 282 headings are found; print the offset of "Coal" (should be at the end of page 1's slice).
7. **Build the tree.** Print the outline with offsets. Draw Chapter 6 > International Collaboration > Paris Agreement (p.10) next to Chapter 16 > International Agreements > Paris Agreement (p.23).
8. **Chunk at three split levels** (chapter, section, sub-section) with cap C = the v1.0 champion size (1,000 characters until I1 is run). Show chunk counts and the length histogram for each.
9. **Merge and balance.** Show what the merge rule does at sub-section level, and what balanced splitting does to a 1,068-character section (two pieces of 534, not 1,000 + 68).
10. **Check continuation.** The "Coal" heading and its body are now one chunk spanning pp.1–2. The PPP sub-section ("Public-Private Partnerships", Chapter 8, p.12) is predicted to fall in one chunk spanning pp.12–13 (verify).
11. **Run the invariants** (offset round trip, no crossing, cap).
12. **Eye inspection:** 10 random chunks, seed 0, verdict sheet.
13. **Measure:** CE@4 for v0, the v1.0 champion, the best cross-page v1.0 arm and v1.1, at fixed k and equal budget, per bucket. Read 5 items that got better and 5 that got worse.

**Visuals that earn their place.**
- **Font-size ladder** (SVG): the four D levels as horizontal bars (24 / 18 / 13.56 / 12 bold / 12 regular) with counts. Shows why size alone misses 68% of headings.
- **Page ruler** (SVG): character axis for pp.1–2 and pp.12–13 with page breaks, heading ticks, per-page chunks above and structure chunks below. Shows the orphan repaired and the cut sentence kept whole.
- **Section tree** (SVG, one chapter): nodes with character lengths. Shows why sub-sections need merging.
- **Chunk-length histograms** (Plotly): fixed 1000/200 vs structure at three split levels. Shows the uneven sizes behind the equal-budget rule.
- **Duplicate-title table:** the 11 repeated headings with their full paths. Shows why the breadcrumb is the identity.

**Full only:**
- the outline (`get_toc`) route and `TocHeaders`;
- PDF tags as a cross-check;
- two-column order (C1 column clipping);
- element-type chunking [I2-S7];
- page-level chunking [I2-S8];
- layout models (docling, unstructured `hi_res`) and their weight;
- tables kept whole;
- the mixed-evidence studies [I2-S9–S13];
- why `add_start_index` can mis-anchor.

### 7. Verify notebook plan

`study/notebooks/I2_structure_chunking_verify.ipynb`. Offline; PyMuPDF 1.26.7, NumPy, Plotly; MiniLM for retrieval.
1. **Recount D's structure with PyMuPDF.** Span sizes, the bold bit, headings per level. Assert they match the raw-stream counts (1/21/68/192; 11 repeated titles), or explain each difference. Record whether the hyphen headings are one span. Check that `get_toc()` returns `[]`.
2. **Same text, same order.** For each page, assert that the `dict` lines joined with `"\n"` equal `page.get_text()` (or record the exact differences). Alignment rests on this.
3. **Re-measure 07 D.8 on PyMuPDF text:** the orphaned headings (pages ending in a detected heading line) and the mid-sentence cuts. Closes I2-E7.
4. **Chunk** at split levels {chapter, section, sub-section} × merge {off, on} with C = 1,000 (later: the champion). Show counts, min/median/max length, WordPiece and cl100k token maximums, and the truncation rate (MiniLM 256).
5. **Invariants** as executable cells: round trip, tiling, cap, section containment, `page_segments` round trip.
6. **Containment demos:** "Coal" + body in one chunk; the PPP sentence whole in some v1.1 chunk (prediction to confirm).
7. **Buckets:** compute `straddles_champion` for the D seed items from the champion's chunks; list `crosses_page` items.
8. **Retrieval:** MiniLM exact cosine, CE@4 and Span-Coverage@4 at fixed k and at equal budget for v0, champion (placeholder until I1), cross-page control and the v1.1 arms; per bucket with n.
9. **Charts:** the font ladder, the length histograms, the CE-by-bucket bars (Plotly).

API calls: none (the optional cached Cohere view runs in replay only). Runtime: about 1–2 minutes on CPU.

### 8. Apply-it tool plan and real-world checklist

`study/tools/structure_fit_check.py`: "Will structure-aware chunking work on my PDFs, and what settings?"
- **Inputs:** `--pdf` (one or more); `--cap` (default 1000 characters, or the champion); `--split-level auto|1|2|3|4`; `--min-chars`; `--sample 10 --seed 0`; optional `--evalset` (M1 format) for bucket CE.
- **Outputs:**
  - per-file font-size histogram and body size;
  - outline present? tags present? (via the PDF catalog; method to confirm in PyMuPDF 1.26.7, UNVERIFIED);
  - heading candidates per level, with the size-only vs size+bold difference;
  - column check (block x0 values, C1 method);
  - alignment rate;
  - the outline print;
  - chunk statistics per split level;
  - the orphan and page-cut counts fixed;
  - a 10-chunk inspection sheet (Markdown);
  - the checklist and a recommendation.

**Real-world checklist (11 checks)**

| # | Check | Auto / manual |
|---|---|---|
| S1 | Text layer exists on every page (no scans); otherwise structure is "none" | auto |
| S2 | Body size is clear: one size holds ≥ 50% of characters ([P] threshold) | auto |
| S3 | At least two heading levels are found, and the heading count is plausible (between 1 per 3 pages and 15 per page; [P]) | auto |
| S4 | Size-only and size+bold detectors disagree on fewer than X% of lines, or the difference is explained | auto (count) + manual (read the list) |
| S5 | Outline (`get_toc`) present: its titles match the detected headings (≥ 90%, [P]) | auto |
| S6 | Every heading aligns to an exact snapshot offset | auto |
| S7 | Single column, or columns handled (C1 clipping) before detection | auto (x0 clusters) + manual (one page by eye) |
| S8 | No running headers or footers are detected as headings (lines repeated on ≥ 3 pages are excluded) | auto |
| S9 | Chunk sizes: none over the cap; fewer than 10% under the min ([P]); no chunk over the embedder's limit | auto |
| S10 | 10 random chunks pass the inspection sheet (start at a heading or a clean continuation; correct path; no mid-sentence end unless forced by the cap) | manual |
| S11 | Tables are detected and kept whole, or flagged for C7/S2 | auto (`find_tables` count) + manual |

**Recommendation logic.**
- S1 fails → "No structure: use v1.0 recursive (or OCR/layout, S2)."
- S5 passes → "Use the outline as the heading source."
- S2–S4 pass → "Typography route at split level = the deepest level whose median section ≥ min-chars."
- S7 fails → "Fix reading order first (C1)."
- S10 < 8/10 → "Do not measure yet: parsing errors will show up as false negatives (06 v1.1)."
- Duplicate titles found → "Keep `section_path`; consider I5 headers."

### 9. LLMOps notebook plan

`study/llmops/notebooks/I2_structure_chunking_ops.ipynb`: the chunker as a versioned index build, traced and regression-tested. No LLM calls.
- **Framework build (comparison arm, after the mechanism):**
  - `pymupdf4llm.to_markdown(<separate Document>, page_chunks=False)` (0.2.9) → `MarkdownHeaderTextSplitter(headers_to_split_on=[("#","h1"),("##","h2"),("###","h3")], custom_header_patterns={"**": 4}, strip_headers=False)` → `RecursiveCharacterTextSplitter(chunk_size=C, chunk_overlap=0)`.
  - **Re-anchoring step:** strip Markdown markup, normalise whitespace, map each chunk back into `doc_text` (two-pointer search over the normalised text with an offset map). Report the **anchoring rate**. Score only anchored chunks, and report the unanchored count as a failure.
  - Map to the mechanism: converter = heading detection; header splitter = section tree; recursive splitter = cap; re-anchor = the alignment step the course chunker does natively.
  - **Defaults to name** [I2-S2, S3]: size-only headers; `**…**` in header text; `strip_headers=True`; `"  \n"` rewriting; no offsets; no cap; `IdentifyHeaders` deletes `StructTreeRoot` from the passed document.
  - Read-only cells: `unstructured.chunk_by_title` defaults (500 / 500 / 500, multipage on) and docling `HybridChunker` (`merge_peers`, MiniLM tokenizer, `contextualize` adds headings). Not installed.
- **External calls (cached, D-32):** Cohere `embed-v4.0` (`search_document`) per arm. D has about 90–300 chunks per arm, so ≤ 4 batched calls of ≤ 96 texts per arm. With 3 split levels + the framework arm, that is **≤ 16 calls**. Query vectors are cache hits from v1.0, and identical chunk texts hit the content-addressed cache. MiniLM runs locally. Replay mode serves everything; no key needed after recording.
- **Tracing (JSONL default; Phoenix locally; LangSmith only for Corpus D):**
  - an index-build span: `chunker`, `params_hash`, `split_level`, `cap`, `min_chars`, `heading_counts` per level, alignment rate, chunk count, length stats, truncation count, build time;
  - per chunk: `chunk_id`, `[a, b)`, `page_segments`, `section_path`, `merged`, `continued`;
  - retriever spans per query with ranked `chunk_id` + score + `section_path`.
  - Exported spans carry ids, offsets and paths, and chunk text only for Corpus D (foundation §3.3).
- **Dataset and evaluators:**
  - the frozen dev split, with the new tags in a new dataset version;
  - code evaluators: CE@4, Span-Coverage@4, Hit@4, MRR; per bucket `straddles_champion`, `crosses_page`, `section_scoped`;
  - index evaluators: anchoring rate, cap violations, section crossings, heading recall against the hand-checked D outline (282).
  - No judge (D-10).
- **Experiment against the previous version:** v1.1 (best split level on dev) vs v1.0 champion vs best cross-page v1.0 vs v0, at fixed k and equal budget; paired bootstrap by group; one test touch. The framework arm is reported beside them, never adopted unless it is fully anchored.
- **Cost / latency / tokens:** index build time per arm; embed calls and "cost if called" (Cohere price UNVERIFIED); query p50/p95 unchanged (same index type); mean context tokens per arm.
- **Versioning:** `ChunkerConfig(name="structure_aware", size=C, overlap, scope="cross_page", split_level, min_chars, heading_rules_version)`. All fields go into `params_hash`, so a rule change makes a new index. The heading rules live in a versioned YAML.
- **CI and monitoring (`ci-cd-evals`):**
  - T1, on D and on a synthetic zoo: offset round trip, tiling, cap, no section crossing unless `merged`, heading counts per level equal the frozen outline (a regression catches a PyMuPDF upgrade that changes spans), alignment rate = 100%.
  - Retrieval regression on cached vectors.
  - Monitor: heading counts and chunk-count drift per corpus version; alert when the alignment rate is below 100% or a new heading level appears.
  - Feedback: a failed inspection chunk → error-analysis log → a zoo fixture → a T1 test.
- **Lifecycle:** Improve (one v1.x card) → Measure (CE by bucket) → CI (T1 properties). Skills: `rag-evaluation`, `code-based-evaluators`, `error-analysis`, `trace-data-analysis`, `llm-observability`, `ci-cd-evals`, `visual-learning-writer` (lesson).

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version (pin ≥ 2 weeks old) | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| PDF spans, outline | `pymupdf` | 1.26.7 (keep pin; 1.28.2 is the newest) | yes | yes | — | AGPL-3.0 / commercial | yes |
| PDF → Markdown (LLMOps arm only) | `pymupdf4llm` | **0.2.9** (the newest compatible with 1.26.7; 0.3.x needs ≥ 1.27.1; 1.27+/1.28 pin PyMuPDF exactly) | no | yes | — | AGPL-3.0 / commercial | yes, comparison arm only |
| its dependency | `tabulate` | 0.10.0 | no | yes | — | MIT | yes |
| Layout model add-on | `pymupdf-layout` | 1.28.2 | no | yes | — | AGPL / commercial | **no**: needs `PyMuPDF==1.28.2` plus onnxruntime |
| Header splitter, recursive fallback | `langchain-text-splitters` (+ `langchain-core`) | 1.1.3 (+ 1.6.6) | no | yes | — | MIT | yes (D-32, after the mechanism) |
| Element chunking (read-only) | `unstructured` | 0.27.10 | no | yes (`fast`) | — | Apache-2.0 | heavy (spacy, numba); `hi_res` needs models; not installed |
| Layout + table models (read-only) | `docling` / `docling-core` | 2.133.0 / 2.99.0 | no | yes after model download | — | MIT | **heavy**: torch + torchvision + IBM models (well over 500 MB); read only. A future S2 decision |
| Offset-keeping chunk types (optional) | `chonkie` | 1.7.0 | no | yes | — | MIT | optional; not needed |
| Embeddings | Cohere `embed-v4.0` via `CachedEmbeddings` | — | — | replay yes | ≤ 4 batched calls per arm on D; price UNVERIFIED | — | yes (D-03) |
| Offline embeddings | `all-MiniLM-L6-v2` | `sentence-transformers` 6.1.0 | yes | yes | $0 | Apache-2.0 | yes |
| LLM | none | — | — | — | 0 calls | — | yes. LLM heading repair is rejected: cost per page and non-deterministic boundaries break the T1 regression |
| Tracing | JSONL; `arize-phoenix-otel` 0.17.2; `langsmith` 0.14.4 (Corpus D only) | as foundation §11 | no | JSONL/Phoenix yes | free | — | yes |
| Tests | `pytest` | 9.1.1 | yes | yes | — | MIT | yes |

**Install lines (do not run):**
```text
uv add --group llmops langchain-core==1.6.6 langchain-text-splitters==1.1.3   # already in the foundation plan
uv add --group llmops pymupdf4llm==0.2.9 tabulate==0.10.0                     # I2 comparison arm only
```
**Keys:** `COHERE_API_KEY` (present) for recording; none for replay or for MiniLM. `LANGSMITH_API_KEY` only if Yash opts in for Corpus D.

### 11. Open questions for Yash (preferences only)

- In the lesson, start the climate example at the sub-section level (finest, needs merging) or at the section level (sizes near 1,000 characters)? **section / sub-section** (recommended: section)
- Add the `pymupdf4llm` comparison arm to the LLMOps notebook (adds one AGPL package to the `llmops` group)? **yes / no** (recommended: yes)

---

## Concept I3: Semantic chunking

### 1. Sources checked

**Book (not re-opened; the PDFs are not in this session, so every page below is UNVERIFIED).**
Page map taken from 01 (line 97), 02 (I3 card) and 04 §3 Ch9:
- Ch9 p.1–2/14: the problem (fixed windows ignore meaning).
- Ch9 p.4–5/14: split into sentences. p.5/14: embed each. p.5–6/14: distances between neighbours (01 lists an illustrative distance-curve figure on p.6).
- Ch9 p.6–7/14: three breakpoint methods (percentile, standard deviation, IQR; 04 DV-23 records the book's IQR rule as Q3 + 1.5·IQR).
- Ch9 p.7–8/14: group sentences into chunks (sketch p.7, pipeline figure p.8 per 01).
- Ch9 p.8–10/14: compared with fixed chunks. p.10–11/14: the strategy spectrum. **p.12–13/14: when to use it (01 only; not cited by 02 or 04).**
- App p.6/23: "Layer 2" quick wins name semantic chunking (per 07 L30/L613, 05 CR-07 and the review row 248). App p.12/23: measure before and after every change (per 04 §3 App A).

**Repo (verified; `NirDiamant/RAG_Techniques` @ `009adba`, custom non-commercial licence) [I3-S1, I3-S2].**
- `all_rag_techniques/semantic_chunking.ipynb` has 20 cells (0-based) and **no saved outputs in any cell**.
  - Cell 0: credits Greg Kamradt and LangChain; says the same OpenAI embeddings are used "for both" chunking and the vector store.
  - Cell 5: imports `SemanticChunker` from `langchain_experimental.text_splitter`. Cell 7 downloads the PDF twice (duplicate line).
  - Cell 10: `content = read_pdf_to_string(path)`. This joins all 33 pages into one string and drops page numbers (`helper_functions.py` L223–L245).
  - Cell 11 (markdown): three breakpoint types, described in one line each.
  - Cell 12: `SemanticChunker(OpenAIEmbeddings(), breakpoint_threshold_type='percentile', breakpoint_threshold_amount=90)`. No buffer, minimum or maximum is set.
  - Cell 14: `create_documents([content])`. Cell 16: a new `OpenAIEmbeddings()` for FAISS, k = 2. Cell 18: one test query.
  - So 02's "cells 12, 14" and 04's "cells 11–18" are both correct. 02 omits cell 16, where the chunk embedder is chosen.
- `all_rag_techniques_runnable_scripts/semantic_chunking.py`:
  - L19–L58: `SemanticChunkingRAG`. One `self.embeddings` object computes the breakpoints (L44–L48) **and** embeds the chunks (L57).
  - L51–L53: wall-clock timing only.
  - L89–L91: `--breakpoint_threshold_type` choices `percentile`, `standard_deviation`, `interquartile`, `gradient`; default 90 (L93).
  - L95–L102: `--chunk_size`, `--chunk_overlap` and `--experiment` are declared and never used. L6 imports helpers before L11 fixes `sys.path`. Both match 04.

**Library source (verified, read at pinned tags).**
- `langchain-experimental` 0.4.2 `langchain_experimental/text_splitter.py`, from the PyPI wheel (sha256 `fd98b994…0d40`). It is byte-identical to GitHub tag `libs/experimental/v0.4.2` and to `main` on 2026-10-17 [I3-S3].
- `langchain-community` 0.4.2 `utils/math.py` `cosine_similarity` [I3-S4].
- LlamaIndex `llama-index-core` v0.14.25 `node_parser/text/semantic_splitter.py` and `text/utils.py` [I3-S5].
- `chonkie` v1.7.0 `src/chonkie/chunker/semantic.py` [I3-S6].
- Cohere SDK 7.2.0 `cohere/types/embed_input_type.py` [I3-S14].

**Course files.**
- 02 I3 card; 03 rows 429, 517, 609 and §5 row 16 ("statistics behind thresholds" assumed known); 04 §2.4 row, §3 Ch9, DV-23; 06 §3.2, §4.1, v1.3 card, §7.3; 08 lines 43, 95, 178.
- 07 L513, L1472, L1639–1645, L1748 (I3 forward links); `concepts/C3_embedding_indexing.md` (records with `char_start/char_end`, `page_segments`, `params_hash`, `embed_hash`); `sources/verification/C3/C3_FACTS.md` (33 pages, 72,593 characters, 97 chunks at 1000/200); LLMOPS_FOUNDATION §2–§12.
- There is no I3 lesson, question file, lab or verification folder.

**AE book:** no semantic-chunking section. Per the review (not re-opened): AE Ch7 promises a chunking grid-search section that is missing; AE Ch11 'Beyond Clustering' calls 1.5×IQR robust to skew, and the review notes that on skewed data it flags much of the upper tail. That matters for IQR breakpoints.

**Interview repos (verified).** AIQ `04-rag-and-retrieval/questions.md` Q4 [I3-S12]. SDG `06-retrieval-systems/02-chunking-strategies.md` §'Semantic Chunking' and the 'fixed-size' Q&A [I3-S13].

**External:** [I3-S7] Kamradt's notebook · [I3-S8] Chroma `chunking_evaluation` code · [I3-S9] Chroma report (UNVERIFIED) · [I3-S10] Qu, Tu and Bao (UNVERIFIED) · [I3-S11] pySBD · [I3-S16], [I3-S17] 2025–26 follow-ups (UNVERIFIED).

**Measured here (no API calls).** The climate PDF from upstream @ `009adba` (sha256 `1d58a0fa…2669`), extracted with `pdftotext`. That is **not** the course parser: it gives 71,551 characters against C3's 72,593 with PyMuPDF.
- Default LangChain regex on the joined text: **613 segments**. Median 110 characters, p99 219, maximum 295, mean 115.6.
- No abbreviation splits and no "digit. digit" splits.
- All 21 "Chapter N:" headings are glued to the first body sentence that follows (no full stop after headings).
- 24 of 33 pages end without `.?!`, so a sentence or heading runs across the page break.
- Re-measure on the PyMuPDF snapshot in the verify notebook.

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class (core / bridge / next) | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Sentence segmentation is a hidden first step (regex `(?<=[.?!])\s+`; abbreviations, decimals, headings and bullets with no full stop) | Ch9 p.4–5/14; library L119, L211–L212 | **missing** | I3 | no | core | Show the 613 segments and the 21 glued headings on Corpus D. Show "et al. 2024" splitting on a Corpus T line. Compare regex with pySBD in Full |
| 2 | One embedding per sentence window; cosine similarity; normalisation | Ch9 p.5/14 | P4 (not studied; MC-002 open) | P4 | no | bridge | 5-line refresher: cos = a·b/(‖a‖‖b‖); for unit vectors, 1 − cos = ‖a − b‖²/2 |
| 3 | `buffer_size`: each sentence is embedded with its neighbours (b = 1 gives a 3-sentence window) | library L15–L53; Kamradt cell 77 | **missing** (04 says "UNVERIFIED") | I3 | no | core | Draw the sliding window. Kamradt found single sentences "too noisy" |
| 4 | The distance curve d_i = 1 − cos(w_i, w_{i+1}), with N − 1 values for N sentences | Ch9 p.5–6/14; library L56–L85 | missing in the repo (no output) | I3 | no | core | Plot it on Corpus D with the 21 chapter starts marked |
| 5 | Percentile rule, NumPy's linear interpolation, strict ">" | Ch9 p.6–7/14; L139–L143, L241–L245 | missing | I3 | no | core | Toy curve by hand (§6) |
| 6 | mean + k·σ rule (library default k = 3) | Ch9 p.6–7/14; L144–L149 | assumed (03 §5 row 16) | I3 | no | core | Toy: k = 3 finds **no** breakpoint on a small document, because the outliers inflate σ |
| 7 | IQR rule: the book uses Q3 + 1.5·IQR; LangChain uses **mean** + 1.5·IQR | DV-23; L150–L156 | missing; DV-23 UNVERIFIED until now | I3 | no | core | Show both thresholds on the toy (0.200 vs 0.259) and say which code does which |
| 8 | Gradient rule: percentile of `np.gradient(d)`; the cut can shift one sentence before the peak | L157–L163; script L90; not in the book | missing | I3 | no | core (Full) | Toy: the gradient puts the cut at index 5; the peak is at 6 |
| 9 | **The threshold is relative to the document.** The percentile fixes the cut count: about (1 − p/100)(N − 1) cuts, whatever the content | follows from L142 | **missing** | I3 | no | core | Arithmetic: N = 613, p = 90 gives ≈ 61 cuts, 62 chunks, mean ≈ 1,140 characters; p = 95 gives ≈ 31 cuts and ≈ 2,210 characters |
| 10 | `number_of_chunks` (an inverse percentile) and size-matched arms (Chroma binary-searches the threshold to a target mean size) | L170–L192; [I3-S8] | missing | I3 | no | core (Full) | The fair arm: same chunk count as the champion |
| 11 | Unbounded size: no maximum anywhere; `min_chunk_size` counts **characters**, merges forward and does not apply to the last chunk | L120, L258–L263, L270–L272 | 02/03/04 say "no size cap" | I3 | no | core | Chunk-size histogram; one hand-traced merge |
| 12 | Truncation: MiniLM reads 256 tokens; Cohere `embed-v4.0` has 128k context (LLMOPS §6.2) | 06 §3.2; 07 D.6 | 06 only | C2/C3 | no | bridge | p = 95 means ≈ 2,200-character chunks, so MiniLM truncates many of them. With Cohere it does not matter |
| 13 | Equal-token-budget comparison; fixed k confounds size with boundaries | 06 §4.1 rule 2; v1.3 card | I1 (not studied) | I1/M4 | no | bridge | One table: fixed k = 4 vs k chosen per arm so mean context tokens match |
| 14 | Which embedder computes the breakpoints vs which embeds the chunks; `input_type` for breakpoints (`search_document` vs `clustering`) | 06 v1.3 "record which embedder"; script L41/L57 | **missing** | I3 | no | core | 2×2 design box. Default: Cohere for both, `search_document`; MiniLM breakpoints as a diagnostic arm |
| 15 | Scope: one threshold per document vs per page; page provenance | cell 10; 06 §3.1 `per_page` | C1/C3 (not studied) | C1/C3 | no | bridge | Use document scope with `page_segments`. 24 of 33 pages end mid-sentence, so per-page scope would cut sentences |
| 16 | **Offsets and text identity.** LangChain rejoins sentences with `" "`, so chunks are not substrings of the source; `add_start_index` drifts (L289). LlamaIndex keeps exact substrings | L257, L271, L289; [I3-S5] | **missing** | I3 (C3 records) | no | core | The course chunker returns character spans from `re.finditer`; text = `doc[start:end]`. CE@k needs this |
| 17 | Index cost: N × (2b + 1) sentences of embedding input, plus the chunks; a threshold sweep re-uses the sentence vectors | 03 row 609; 06 v1.3 "Cost" | partly | I3 | no | core | Corpus D: ≈ 613 window texts = 7 Cohere calls (96 per call) + 1 call per arm. About 3× v0's embedding tokens (estimate) |
| 18 | `params_hash` must include the breakpoint embedder | C3 manifest splits chunker and embedding | **missing** | C3/I3 | no | core | A new embedding model changes the chunks. C3's chunker hash would not notice |
| 19 | Determinism: breakpoints are a pure function of cached vectors; ties at the threshold; float32 vs float64 (`simsimd`) | [I3-S4]; LLMOPS §2.7 | missing | I3 / LLMOps | no | core | Rerun gives the same breakpoints; a canary catches embedding drift |
| 20 | Index time vs query time (MC-003) | C3 | C3 (not studied) | C3 | no | bridge | One line: zero query-time cost |
| 21 | Evaluation: CE@4 primary, per category (multi-span, boundary items), dev selection, a sweep = multiple comparisons | 06 v1.3, §9.4 | M2 (exposed), M4 (not studied) | M2/M4 | exposed / no | bridge | Pre-registration box; say "sweep only if promising" |
| 22 | Chunk-size distribution as an evidence item and a monitor | 02 Evidence line | missing | I3 | no | core | Histogram plus p50/p95/max table per arm |
| 23 | Research evidence: fixed-size often matches or beats semantic on real documents | [I3-S10], [I3-S9] | **missing** | I3 | no | core | Evidence box: study → result → limits |
| 24 | Often confused: semantic chunking vs semantic search; vs clustering; absolute vs relative thresholds | SDG Q4 (review §8); SDG 0.82 | missing | I3 | no | core | "Often confused" table |
| 25 | Book claims as hypotheses (App p.6/23 "quick win"; Ch9 p.8–10/14) | 06 v1.3; review row 248 | 07 L613 only | I3/M4 | no | core | State it as H1 to test, with the AIQ "marginal" counter-claim |
| 26 | Alternatives: clustering + DP (Chroma), Savitzky–Golay minima with a 2,048-token cap (chonkie), LLM chunking, late chunking | [I3-S6], [I3-S8] | — | I-CMP / I5 | no | next | Link only; one row each in Full |

### 3. Quiz coverage

There is no question file. Titles needed:
- **R:** What text does `buffer_size = 1` embed for sentence i? · Write the four threshold rules as formulas, and say which IQR rule LangChain uses. · Why does a percentile threshold fix the number of chunks, whatever the document says? · Name two things that make semantic chunks hard to cite by page.
- **A:** Distances `[0.12, 0.10, 0.48, 0.09, 0.14, 0.11, 0.52, 0.13, 0.10]`: find the breakpoints for percentile 90, mean + 3σ, mean + 1.5·IQR, Q3 + 1.5·IQR and gradient 95 (key in §6). · A document has 613 sentences: how many chunks at p = 90 and p = 95, and how many Cohere embed calls at b = 1? · A chunk of 2,200 characters goes to MiniLM: what fraction of its text is read? (Use the 07 D.6 ratio, about 4.3 characters per token: 256 tokens ≈ 1,100 characters, so about half.)
- **T:** A teammate reports "semantic beats fixed by 6 points of CE@4 at k = 4"; the semantic chunks average 2,200 characters. What do you ask first? (Equal budget.) · A corpus of FAQ pages, each 3–5 sentences: would you use semantic chunking? · You switch the breakpoint embedder from MiniLM to Cohere and CE@4 changes: which variable changed?
- **Interview (set=interview, source=AIQ-04-Q4):** "What chunking strategies do you know, and how do you pick one?" Its answer calls semantic gains "marginal over recursive+structure-aware". Our checked answer cites [I3-S10] (UNVERIFIED numbers) and says "measure it at equal budget". This doubles as the review row 248 L item: "The book calls it a quick win; a guide calls it marginal. How do we settle it?"

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| I3-E1 | 04 DV-23 and §2.4 row ("library IQR formula UNVERIFIED"); 08 L95 | **Resolved.** `langchain-experimental` 0.4.2 (the PyPI wheel and tag `libs/experimental/v0.4.2`) computes `np.mean(distances) + amount * (q3 − q1)` (L150–L156). The book (per 04) uses Q3 + 1.5·IQR. The review §7 row 31(e) found this on `main`; it is now confirmed on the released version | DV-23: "library uses mean + 1.5·IQR (0.4.2, L150–L156); book Q3 + 1.5·IQR" |
| I3-E2 | 04 §3 Ch9 table, rows 1–3 ("buffer/neighbour behaviour … UNVERIFIED locally") | Verified: `buffer_size = 1` by default; `combine_sentences` (L15–L53) embeds previous + current + next, joined by spaces | Replace UNVERIFIED with the line numbers |
| I3-E3 | 04 §3 Ch9 "Build yourself … all three threshold rules"; 02 I3 outcomes | The library has a fourth rule (`gradient`, L157–L163; also script L90) and a `number_of_chunks` mode (L170–L192). Its defaults are percentile 95, std 3, IQR 1.5, gradient 95 (L91–L96), so the notebook's 90 overrides the default | Add gradient and `number_of_chunks` as Full-only; record the defaults |
| I3-E4 | 06 v1.3 card ("recommends … high-leverage addition (App p.12/23)") | 07 L30/L613, 05 CR-07 and the review row 248 put the "quick win" claim on App p.6/23. 04 §3 says p.12/23 is "measure before and after". Probably a wrong page in 06 (UNVERIFIED: book not opened) | Cite App p.6/23 for the claim and p.12/23 for "measure first" |
| I3-E5 | 02 and 04 Ch9 page lists | Neither cites the "when to use" pages p.12–13/14 (01 L97), which the per-technique gate's "when NOT to use" needs | Add p.12–13/14 (UNVERIFIED) |
| I3-E6 | 04 §3 Ch9 "sketch p.7/14" vs 01 L97 figures (distance curve p.6, pipeline p.8, comparison p.10) | The figure pages disagree, and 04's "distance curve never shown" is true only of the repo | Check at the next book session |
| I3-E7 | 02 I3 Repo line | Omits cell 16, where a second `OpenAIEmbeddings()` embeds the chunks; the breakpoint and chunk embedders are coupled by default | Add "cell 16 (chunk embedder; k = 2)" |
| I3-E8 | C3 manifest design (`params_hash` = chunker only; `embed_hash` = document embedding) | For a semantic chunker the chunk boundaries depend on an embedder. A model change would keep `params_hash` the same while the chunks change | The semantic chunking block includes `breakpoint_embed_hash` (§9) |
| I3-E9 | 06 §3.2 and v1.3 ("can exceed the embedder limit") | True for the MiniLM fallback (256 tokens). For the default Cohere `embed-v4.0` (128k context, LLMOPS §6.2) truncation is irrelevant at these sizes, so the real issue is budget, not truncation | Say "MiniLM: truncation; Cohere: context-token budget" |
| I3-E10 | LLMOPS §11 tools list | `langchain-experimental` 0.4.2 hard-requires `langchain-community` 0.4.x, which pulls `langchain-classic`, `aiohttp`, `sqlalchemy` and more (14 packages beyond the llmops group) | Add a row (§10) |
| I3-E11 | Upstream (not course): `SemanticChunker` docstring and `add_start_index` | The docstring says it "merges" similar groups; the code only cuts at distances above the threshold. `start_index += len(chunk)` (L289) ignores the whitespace replaced by `" "`, so the offsets drift | Lesson "often confused" row; LLMOps parity test re-maps the offsets |
| I3-E12 | SDG `02-chunking-strategies.md` (external, MIT) | Uses an absolute 0.82 cosine threshold. Claims semantic chunking gives "significantly higher retrieval precision" with no evidence. The same guide's question bank describes semantic chunking as clustering (review §8) | Critique target in the lesson; no course edit |

### 5. What the research says

- **Where the method comes from, and what its author claimed** [I3-S7].
  - *Study:* Greg Kamradt's "5 Levels of Text Splitting" notebook, Level 4, on one Paul Graham essay (317 regex sentences).
  - *Result:* single-sentence embeddings were "too noisy", so the notebook embeds 3-sentence windows. Kamradt picked the 95th percentile of the distances as the only parameter.
  - *Limits:* one essay; no retrieval metric. The notebook calls the method "far from usable yet", says it "should be tested with RAG eval", and notes that chunk size was not handled.
  - *For the project:* LangChain's code is this notebook almost line for line (same regex, same `combine_sentences`, same slicing). The library default of 95 comes from here; the upstream 90 is an unexplained override.
- **Library behaviour today (2026)** [I3-S3–S6].
  - *LangChain 0.4.2:* regex split; window b = 1; distance = 1 − cosine; four rules with defaults 95 / 3 / 1.5 / 95; strict ">"; no maximum size; `min_chunk_size` in characters; chunks rejoined with spaces.
  - *LlamaIndex 0.14.25:* NLTK punkt via `span_tokenize`, keeping the whitespace, so chunks are exact substrings. Percentile only, default 95; buffer 1; no maximum. With no `embed_model` it tries OpenAI.
  - *chonkie 1.7.0:* a different design. It compares a 3-sentence window with the next sentence, smooths with Savitzky–Golay (window 5, order 3), cuts at local minima filtered by `threshold = 0.8`, and enforces a **2,048-token maximum**. Whether 0.8 is a percentile or an absolute value sits in the Rust core (UNVERIFIED).
  - *For the project:* "semantic chunking" names a family. The percentile/breakpoint form is the book's and the repo's; the others are I-CMP rows.
- **Does it beat fixed-size chunking?** [I3-S10] (UNVERIFIED: search-checked, paper not opened; arXiv, ACL and Vectara are blocked here).
  - *Study:* Qu, Tu and Bao (Vectara / UW–Madison), arXiv 2410.13070, Findings of NAACL 2025. They compare fixed-size, breakpoint and clustering chunkers on document retrieval, evidence retrieval and answer generation. Search summaries say they also built "stitched" documents by joining short texts (about 100 sentences each), and report F1@5 and BERTScore.
  - *Result (per the summaries):* semantic chunking won slightly only on the stitched, topic-diverse documents. On natural documents, fixed-size was equal or better; one summary says it won 3 of 5 evidence-retrieval datasets. The embedding model mattered more than the chunker. The authors conclude that the cost is not justified by consistent gains.
  - *Limits:* stitched data inflates topic shifts; it is unknown whether chunk sizes were matched; there are no exact numbers here.
  - *For the project:* the v1.3 prior is "inconclusive or not supported". Corpus D is one document with 21 chapters, so it sits between the stitched and the natural cases.
- **Chroma's chunking report** [I3-S8 verified code; I3-S9 report UNVERIFIED, page blocked].
  - *Study:* token-level recall, precision and IoU over exact excerpts.
  - *What the code shows:* `KamradtModifiedChunker` binary-searches the threshold until the number of cuts equals total tokens ÷ `avg_chunk_size` (default 400 tokens; minimum 50). So Chroma **size-matched** Kamradt's method before comparing it. `ClusterSemanticChunker` pre-splits into 50-token pieces and uses dynamic programming to maximise within-chunk similarity, with a hard maximum (default 400).
  - *Result (secondary summary only):* the plain Kamradt chunker had the lowest precision; the cluster chunker was near the recursive splitter on recall.
  - *For the project:* the fair arm is semantic boundaries at a matched size (`number_of_chunks`). That separates "where the cuts fall" from "how big the chunks are".
- **Sentence splitting quality** [I3-S11].
  - *Study:* pySBD (Sadvilkar & Neumann, NLP-OSS 2020) on the "Golden Rules" test set.
  - *Result:* 97.92% of the English rules pass, which the paper reports as 25% better than the next best open-source Python tool.
  - *Limits:* rule-based; last released in 2021.
  - *For the project:* Corpus D has no abbreviation or decimal traps for the regex (0 found), but its headings carry no full stop and glue onto the next sentence. Corpus T (arXiv papers with "et al.", "Fig.", "Eq.") will break the regex. The apply-it tool measures this.
- **2025–26 follow-ups** (UNVERIFIED, search-checked only).
  - Vendor benchmarks quoted in blogs report recursive 512-token splitting ahead of semantic on end-to-end accuracy; one notes semantic fragments averaging about 43 tokens [I3-S16]. That is a size confound, not evidence about boundaries.
  - arXiv 2606.00881 and 2608.00824 (the latter on "the measurement trap in text-transform ablations") appear in searches; titles only [I3-S17].
- **Current practice.**
  - Percentile 95 with b = 1 is the default in LangChain and LlamaIndex.
  - Newer tools add a maximum size (chonkie 2,048 tokens; Chroma 400) or fit a target size.
  - Experienced practitioners (AIQ Q4) treat recursive plus structure-aware splitting as the default and semantic chunking as optional.
- **Pitfalls (with evidence):**
  - Comparing at fixed k with larger chunks (§2 #9).
  - p = 95 on a small document gives very few cuts (toy: p = 90 finds 1 of 2 obvious shifts).
  - A 3σ rule finds none.
  - Offsets drift (L289).
  - Breakpoints change silently with the embedder (I3-E8).
  - The library merges small chunks forward but leaves a tiny last chunk.
  - Headings glue to the next sentence.
  - Per-page scope cuts sentences (24 of 33 pages).
- **How to evaluate.**
  - CE@4 on dev, at fixed k **and** at equal context tokens, against the v1.0 champion and v0.
  - Per category; multi-span and boundary items matter most.
  - Report the chunk-size distribution and truncation rate.
  - Label-free sanity check: boundary recall = share of the 21 chapter starts within ±1 sentence of a cut.
  - Retrieval and answer quality are reported separately; answers only for the top arm.
- **Interview questions:**
  - How does semantic chunking pick boundaries, and what does the threshold depend on?
  - How would you compare it fairly with fixed-size chunking? (Equal budget, matched size.)
  - What does it cost at ingest, and how do you cap the chunk size?
  - When would you not use it? (Short documents, lists and tables, structured documents.)
  - AIQ 04 Q4.

### 6. Lesson blueprint

**The answer first (draft).** Semantic chunking cuts a document where the meaning changes, instead of every 1,000 characters. It splits the text into sentences, embeds each sentence together with its neighbours, and measures the cosine distance between consecutive windows. A cut goes wherever that distance is unusually high for *this* document: above a percentile, above mean + k·σ, or above an IQR fence. So the number of chunks follows the threshold rule, and chunk sizes are not controlled at all. Whether this beats a well-tuned fixed splitter is an open question; published comparisons mostly say no on natural documents. You therefore test it at an equal context-token budget, with the chunk-size distribution on the table.

**The theory in one read (11 ideas).**
1. *Sentences:* s_1 … s_N from a splitter. Its errors become boundary errors.
2. *Windows:* w_i = s_{i−b} … s_{i+b} (b = `buffer_size`, default 1). One embedding per window, e_i = f(w_i).
3. *Distance:* d_i = 1 − cos(e_i, e_{i+1}) for i = 1 … N − 1. With unit vectors, d_i = ‖e_i − e_{i+1}‖²/2 (P4 bridge).
4. *Cut set:* B = {i : d_i > τ}. Chunk j is the sentences between consecutive cuts (strict ">").
5. *Percentile:* τ = P_p(d), with NumPy's linear interpolation. Then |B| ≈ (1 − p/100)(N − 1).
6. *Standard deviation:* τ = mean(d) + k·σ(d) (library default k = 3).
7. *IQR:* book τ = Q3 + 1.5·(Q3 − Q1); LangChain τ = mean(d) + 1.5·(Q3 − Q1).
8. *Gradient (Full):* g = np.gradient(d); B = {i : g_i > P_p(g)}. It marks where the distance is rising, which can be one step before the peak.
9. *Size is not controlled:* mean chunk length ≈ L / (|B| + 1). There is no maximum; `min_chunk_size` (characters) merges forward. The fair variant fixes |B| (`number_of_chunks`) or caps the size.
10. *Cost:* index-time embedding inputs = N windows × about (2b + 1) sentences, plus the chunk embeddings. Query cost is unchanged. A threshold change re-uses the window vectors.
11. *Fair comparison:* fixed k plus equal context tokens; record the breakpoint embedder (and include it in `params_hash`); one variable per arm.

**Formula sheet items:** w_i; d_i; the four τ rules (both IQR forms); |B| ≈ (1 − p/100)(N − 1); mean size ≈ L/(|B| + 1); calls = ⌈N/96⌉ + ⌈n_chunks/96⌉; equal budget: choose k per arm so the mean context tokens match.

**Worked toy (hand-checked with NumPy).**
- d = [0.12, 0.10, 0.48, 0.09, 0.14, 0.11, 0.52, 0.13, 0.10]; mean 0.1989, σ 0.1619, Q1 0.10, Q3 0.14.

| Rule | Threshold τ | Breakpoints |
|---|---|---|
| Percentile 90 | 0.488 | {6} only. It misses the obvious shift at 2 |
| Percentile 80 | 0.276 | {2, 6} |
| mean + 3σ (library default) | 0.685 | none |
| mean + 1σ | 0.361 | {2, 6} |
| mean + 1.5·IQR (LangChain) | 0.259 | {2, 6} |
| Q3 + 1.5·IQR (book) | 0.200 | {2, 6} |
| Gradient 95 | 0.186 | {5}, one step before the peak |

- The two IQR forms differ by 0.059, so any distance between 0.200 and 0.259 is a cut for the book's rule but not for LangChain's.

**Step-by-step outline (running example: Corpus D, the climate PDF; the course corpus).**
1. Predict where you would cut page 1 (07 L1748 asks this).
2. Split the frozen snapshot into sentences with spans. Count them (≈ 600). List the glued headings and the sentences that cross a page break.
3. Build the b = 1 windows. Embed them with MiniLM (offline; check every window is ≤ 256 tokens).
4. Plot d_i with the 21 chapter starts marked. Do the peaks line up?
5. Apply the four rules and `number_of_chunks` = the champion's chunk count. Fill the table: cuts, chunks, size p50/p95/max, MiniLM truncation.
6. Check the percentile arithmetic: predicted vs actual chunk count.
7. Build chunk records with exact offsets and `page_segments`. Show why LangChain's text and offsets cannot be used directly.
8. Retrieve for the seed items D-001…D-008 at fixed k = 4 and at equal tokens. CE@4 against v0 (a diagnostic, not a verdict).
9. Cost table: inputs, estimated tokens and calls, against v0's 97 chunks.
10. Write the pre-registration for v1.3 (H1 from App p.6/23; guard metrics; "sweep only if promising").

**Visuals.**
- **Window-and-distance strip** (SVG): sentences as boxes, the b = 1 windows as brackets, d_i as bars. Shows what is actually compared.
- **Distance curve with τ lines** (Plotly): four horizontal threshold lines; chapter starts as ticks. Shows the threshold is relative and the rules disagree.
- **Chunk-size histogram** (Plotly): semantic p90 / p95 / matched vs v0, with the 256-token MiniLM line. Shows the size spread and truncation.
- **2×2 embedder box** (SVG): breakpoint embedder × chunk embedder. Shows the confound.
- **Toy table** (above) as a hand-check card.

**Full only:** the gradient rule; `number_of_chunks` maths (L179–L192); the `min_chunk_size` forward merge and the exempt last chunk; float32 `simsimd` vs float64; LlamaIndex and chonkie designs; the Chroma DP chunker; pySBD vs regex; `input_type = clustering` as a possible arm; the AE IQR-on-skew note.

### 7. Verify notebook plan

`study/notebooks/I3_semantic_chunking_verify.ipynb`. Offline by default (`HF_HUB_OFFLINE=1`).
1. **Toy asserts:** the §6 table (thresholds to 3 decimals, breakpoint sets), and the gradient index shift.
2. **Corpus D snapshot** through the course loader (PyMuPDF 1.26.7, C1/C3). Sentence spans via `re.finditer` with the LangChain regex.
   - Report N, the length percentiles, the glued headings (expect 21), sentences that cross a page, and segments under 20 or over 1,000 characters.
   - Optional pySBD column if installed.
3. **Windows** (b = 0, 1, 2) and their MiniLM token counts. **Embed** with `all-MiniLM-L6-v2` (normalised), cached by C3's key.
4. **Distance curve** (Plotly) with the chapter ticks. **Boundary recall** of the 21 chapter starts (±1 sentence) per rule.
5. **Rules table:** percentile 90/95, std 1/3, both IQR forms, gradient 95, `number_of_chunks` = the v1.0 champion's non-overlapping count. Columns: cuts, chunks, size p50/p95/max in characters and in MiniLM tokens, truncated count.
   - Assert the percentile chunk count is within ±1 of (1 − p/100)(N − 1) + 1.
6. **Parity with the library formulas:** re-implement L136–L192 in NumPy and assert identical breakpoints on the same vectors. (The real LangChain call is in the LLMOps notebook, so the verify notebook stays framework-free.)
7. **Records:** text = doc[start:end] for every chunk; `page_segments`; `params_hash` including the breakpoint embedder.
8. **Retrieval diagnostic:** D-001…D-008 at k = 4 and at equal mean context tokens (tiktoken `o200k_harmony` and MiniLM WordPiece, both named): CE@4 and Span-Coverage@4 against v0.
9. **Determinism:** two runs give an identical breakpoint hash. Then nudge one distance across τ to show a tie flip.
10. **Cost table:** window characters, estimated tokens (≈ 4 characters per token, labelled an estimate), and Cohere calls if recorded.

API calls: none (an optional cell reads cached Cohere vectors in replay mode). Runtime: a few minutes on CPU (≈ 600 short windows plus the chunks; estimate, not measured).

### 8. Apply-it tool plan and real-world checklist

`study/tools/semantic_chunk_check.py`: "Would semantic chunking suit my documents, and what would it cost?"
- **Inputs:**
  - `--docs`; `--embedder minilm|cohere-cached`; `--method percentile|std|iqr|iqr-book|gradient|nchunks`; `--amount`.
  - `--buffer 1`; `--min-chars`; `--max-tokens`; `--scope document|page`.
  - `--compare-fixed 1000/200`; optional `--evalset` (M1 format or the light `expect` form of `bm25_fit_check.py`).
- **Outputs:**
  - a sentence-split report;
  - a distance-curve HTML;
  - a per-rule table (chunks, size p50/p95/max, truncation);
  - a cost estimate against the fixed chunker;
  - an offsets check;
  - CE@k at fixed k and equal budget when an eval set is given;
  - the checklist and a recommendation.

**Real-world checklist (12 checks)**

| # | Check | Auto / manual |
|---|---|---|
| C1 | Suspicious sentence splits (an abbreviation before the split, a segment under 20 characters, a number cut) are below 2% of segments | auto (lists them) |
| C2 | Lines without end punctuation (headings, bullets, table rows) are found and shown, glued to their neighbour | auto list + manual read |
| C3 | The distance curve has real peaks: p95(d) / median(d) is reported; a flat curve means the method has nothing to find | auto + manual (look at the plot) |
| C4 | Known section starts fall within ±1 sentence of a cut (boundary recall) | auto if headings are detectable; else manual on 10 cuts |
| C5 | The chunk count matches the rule's arithmetic, and the user knows that the percentile fixed it | auto |
| C6 | No chunk exceeds the embedder's limit (MiniLM 256 tokens): truncation rate 0, or a maximum cap applied | auto |
| C7 | Size spread is acceptable: p95/p50 ratio, and the share of chunks under 100 characters or a single sentence | auto |
| C8 | Every chunk is an exact substring with offsets and page segments (citations will work) | auto |
| C9 | The breakpoint embedder and the chunk embedder are recorded, and the breakpoint embedder is in `params_hash` | auto |
| C10 | Index cost against fixed chunking: embedding inputs, estimated tokens, calls | auto |
| C11 | On your questions, CE@k at fixed k **and** at equal context tokens against the fixed chunker | auto (needs an eval set) |
| C12 | Two builds from the cache give identical cuts; a rebuild with a different embedder is flagged as a new chunker | auto |

**Recommendation logic:**
- C1 or C8 fails → "fix sentence splitting or offsets first; results not trustworthy".
- C3 flat, or C4 low → "no topic structure for the method to find; keep the fixed or structure-aware chunker (I2)".
- C6 fails → "add a maximum cap, or use Cohere".
- C11 gains only at fixed k, not at equal budget → "the gain is chunk size, not boundaries; tune size in I1 instead".
- C11 gain at equal budget, and C10 cost acceptable → "candidate for adoption; confirm on test".

### 9. LLMOps notebook plan

`study/llmops/notebooks/I3_semantic_chunking_ops.ipynb`: v1.3 as a team would run it, after the NumPy mechanism.
- **Framework build.**
  - `SemanticChunker(CachedEmbeddings(provider="cohere", model="embed-v4.0", input_type="search_document"), buffer_size=1, breakpoint_threshold_type="percentile", breakpoint_threshold_amount=90)` from `langchain-experimental` 0.4.2. This maps to steps 1–6 of the lesson.
  - Indexing and retrieval use the M2 `BaseRetriever` wrapper over the course NumPy index, not FAISS.
- **Parity cell.**
  - The same cached vectors go into the course NumPy chunker and into LangChain. Assert identical breakpoint indices for all four types plus `number_of_chunks`.
  - Assert the chunk texts are equal after whitespace normalisation, since LangChain rejoins with `" "`.
  - Offsets are re-mapped by the course code, because `add_start_index` drifts.
  - `simsimd` must be absent (otherwise the similarity is computed in float32); a near-threshold tolerance check is included.
- **Defaults to name** (from the source):
  - percentile **95** default (upstream overrides to 90); std 3; IQR = **mean** + 1.5·IQR; gradient 95; b = 1;
  - the regex splitter; **no maximum size**; `min_chunk_size` in characters, last chunk exempt;
  - `embed_documents` sends all windows in one call (the adapter batches at 96);
  - the docstring's "merges".
  - Read-only cell: LlamaIndex `SemanticSplitterNodeParser` (default 95, punkt, exact substrings, OpenAI embedder if none is given). Not installed.
- **External calls (cached):**
  - Cohere `embed-v4.0` for ≈ 600 windows → about 7 calls at 96 texts per call.
  - About 62 chunks for the p = 90 arm → 1 call. Each extra threshold arm costs 1 more call; the windows are re-used.
  - Queries: the same `search_query` vectors as earlier versions, so cache hits (≈ 0–1 new calls).
  - Total first record ≈ 8–10 calls, well inside the trial key's 1,000 calls a month. Embed price **UNVERIFIED** (LLMOPS §6.2).
  - Optional generation for the top arm only: Groq `openai/gpt-oss-20b`, ≈ 55 calls, ≈ $0.015 per run (LLMOPS §6.3). No judge (D-10). No Claude: the technique has no LLM step.
  - Replay mode serves everything.
- **Tracing:**
  - A chunker span with: N sentences, b, rule, amount, τ, number of cuts, chunk-size p50/p95/max, the breakpoint embedder id and `input_type`, cache hits and misses, and the sha256 of `distances.npy` (saved as a run artifact) and of the breakpoint list.
  - Retrieval spans as in M2: ids, scores, ranks, context tokens.
  - JSONL by default; Phoenix locally; LangSmith only for Corpus D, after `privacy.assert_corpus_is("D")`.
- **Dataset and evaluators:**
  - The M1 golden set, `dev` only.
  - Code evaluators: CE@4 (primary), Span-Coverage@4, MRR@10, mean context tokens, truncation rate, chunk-size stats. All run at fixed k and at equal budget.
  - Through the course runner, plus `langsmith.evaluate(..., upload_results=False)`; the numbers must be identical.
- **Experiment against the previous version:**
  - v1.3 (p = 90, upstream parity) against the v1.0 champion and v0, with the paired bootstrap by group (06 §9.3) and a pre-registered rule.
  - A second arm (`number_of_chunks` = the champion's count) only if the first is promising or inconclusive, logged as an extra comparison (§9.4).
  - MiniLM breakpoints with Cohere chunks as a diagnostic only.
- **Cost / latency:** index build time and embed calls and tokens per arm; query p50/p95 unchanged (asserted); "cost if called" vs "paid".
- **Versioning:**
  - The chunking block `{"name":"semantic","splitter":"regex:(?<=[.?!])\\s+","buffer_size":1,"threshold":{"type":"percentile","amount":90},"min_chars":null,"max_tokens":null,"scope":"document","breakpoint_embed_hash":"…"}` goes into `params_hash` (fixes I3-E8).
  - The library version is recorded in `env.json`.
- **Monitoring and feedback:**
  - On every rebuild, the chunk-size monitor: chunks per document, p95 and maximum tokens, % over the embedder limit, % tiny chunks, and the Jaccard similarity of the cut sets against the last build.
  - Alert when the chunk count or p95 moves by more than 20% for an unchanged document, when truncation is above 0, or when cut Jaccard is below 0.9 with no config change. The embedding canary (LLMOPS §8.4) explains the alert.
  - Items that newly fail go to error analysis and then become golden-set regressions.
- **CI (T1 / replay):** toy-threshold tests; the NumPy-vs-LangChain parity on recorded vectors (replay marker); offset integrity; chunk-count arithmetic; retrieval regression on cached vectors (CE@4 ≥ champion − tolerance).
- **Lifecycle:** Improve (the v1.3 experiment) → CI (parity and regression tests) → monitoring on rebuild.
- **Skills:** `rag-evaluation`, `code-based-evaluators`, `ci-cd-evals`, `llm-observability`, `improving-llm-agents` (index cost), `error-analysis`.

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version (pin a released version ≥ 2 weeks old) | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Mechanism (split, distances, thresholds) | `numpy` + `re` | 2.5.3 (lock) | yes | yes | — | BSD-3 | yes |
| Offline breakpoint and chunk embedder | `sentence-transformers/all-MiniLM-L6-v2` (256 tokens) | `sentence-transformers` 6.1.0 | yes | yes | $0 | Apache-2.0 | yes (fallback) |
| Default embedder | Cohere `embed-v4.0` via `cohere` SDK | 7.2.0 (keep) | yes | replay only | ≈ 8–10 calls per first record on Corpus D; +1 per threshold arm | MIT (SDK) | yes (D-03) |
| Context tokens | `tiktoken` | 0.14.0 | yes | yes | — | MIT | yes |
| Charts | `plotly` | lock | yes | yes | — | MIT | yes |
| Framework chunker (LLMOps only) | `langchain-experimental` | **0.4.2** (2026-05-22) | no | yes | — | MIT | yes. Needs `langchain-core` ≥ 1.4 (compatible with 1.6.6); **pulls `langchain-community` 0.4.2 and `langchain-classic` 1.0.8**, plus aiohttp, sqlalchemy, pydantic-settings, httpx-sse and others (14 packages beyond the llmops group, resolved with `uv pip compile`, nothing installed). No OpenAI dependency |
| Framework core, splitters | `langchain-core`, `langchain-text-splitters` | 1.6.6, 1.1.3 | no | yes | — | MIT | yes (LLMOPS §11) |
| Better sentence splitting (optional) | `pysbd` | 0.3.4 (2021) | no | yes | — | MIT | yes; pure Python. Add only if C1 fails on Corpus T |
| Not recommended | `nltk` punkt | 3.10.3 | no | needs a data download | — | Apache-2.0 | heavier; pySBD covers the need |
| Read only | `llama-index-core` `SemanticSplitterNodeParser` | 0.14.25 | no | — | — | MIT | read only (OpenAI default embedder; large dependency tree) |
| Read only | `chonkie` `SemanticChunker` | 1.7.0 | no | — | — | MIT | read only (Rust core, model2vec default) |
| Do not install | `simsimd` | — | no | — | — | — | changes LangChain's cosine to float32 |
| LLM (optional generation, top arm) | Groq `openai/gpt-oss-20b` | `.env` `GROQ_MODEL_ID` | yes (`groq` 1.7.0) | replay | ≈ 55 calls, ≈ $0.015/run | — | yes |
| LLM (Claude) | none needed | — | — | — | — | — | The technique has no LLM step |
| Tracing (hosted) | `langsmith` | 0.14.4 | no | SDK yes | free plan; Corpus D only | MIT | yes |
| Tracing (local) | `arize-phoenix-otel` + `openinference-instrumentation-langchain` | 0.17.2 / 0.1.78 | no | yes | — | Apache-2.0 | yes |
| Not installed | `langchain-cohere` | — | — | — | — | — | conflicts (cohere < 6); use `CachedEmbeddings` |

**Install lines** (do not run):
```text
uv add --group llmops langchain-experimental==0.4.2     # pulls langchain-community 0.4.2, langchain-classic 1.0.8
uv add --group dev pysbd==0.3.4                         # optional, only if the Corpus T split check fails
```
**Keys:** `COHERE_API_KEY` (present) for recording only; replay needs none. `LANGSMITH_API_KEY` only for the hosted view. No new key.

### 11. Open questions for Yash (preferences only)

- Install `langchain-experimental` (14 extra packages) so the LLMOps notebook runs the real `SemanticChunker` parity test, or keep the LLMOps notebook to the course NumPy chunker plus read-only library code? **install / read-only** (recommended: install, in the `llmops` group).

---

## Concept I4: Proposition chunking

### 1. Sources checked

- **Book (not present in this session; nothing re-opened, all UNVERIFIED):** Ch4 p.4–5/15 (moderate first chunks), p.5–6/15 (LLM decomposition; sketch p.6/15), p.7–9/15 (quality check on four criteria, keep at ≥ 7/10; sketch p.9/15), p.9/15 (embed and store), p.9–10/15 (retrieve and answer), p.10–11/15 (vs standard chunks), p.11–12/15 (where it helps and where it struggles), p.13/15 (one check per chunk, per 04 DV-14). All page notes come from 04 §2.4, 04 §3 "Ch4", 04 §5, 04 §6.1 DV-13/14/15 and 03 rows 430/518/610. Cited below as "per 04 §3; not re-opened, UNVERIFIED".
- **Repo (verified):** `all_rag_techniques/proposition_chunking.ipynb` @ `009adba` downloaded to the session scratchpad. Read cells 2, 4–5, 7, 9–10, 12–13, 15–16, 18–24, 27–38 (source and saved outputs). The cells are 0-based; there are 40 (0–39). Findings in §4 and §5.
- **Course files:**
  - 02 I4 card (lines 594–607) and the per-technique gate;
  - 03 rows 39, 212, 301, 308, 363, 394, 430, 490, 518, 610, 746;
  - 04 §2.4 I4 row, §3 Ch4, §5 row "Answer step", DV-13/14/15;
  - 06 §2.3 (`Chunk` invariant), §2.5, §3.2, §4.1, §4.2 v1.4, §4.3, §6.1–6.4, §7.2–7.5, §9.2–9.4;
  - 08 D-03, D-04, D-09, D-10, D-17, D-22, D-32;
  - LLMOPS_FOUNDATION §2.3–2.5, §3.2–3.3, §4, §5, §6.2–6.4, §7, §9.2–9.3, §10, §12 (row "4 · I4–I6");
  - ext review rows 263 and 388 (few-shot leakage test);
  - `progress/concept_tracker.csv` (I4 `S`, `not_started`); `misconception_log.md` MC-001, MC-006;
  - C2LAB_FACTS / `out_c2_measure.txt` (97 per-page chunks, median 935 chars, page lengths 636/2,225/2,494); C3_FACTS (72,593 chars, 33 pages).
- **AE book:** not opened. Only the review's rows 263/388 (AE Ch9 leakage) are used, "per the review, not re-opened".
- **Interview repo:** AIQ `04-rag-and-retrieval/questions.md` @ `e080df2` Q4 (chunking strategies), Q5 (size and overlap; "retrieve small, generate big"), Q17 (contextual retrieval and late chunking). Copyright (c) 2026 Om, MIT License. Q4's answer lists five strategies and leaves out propositions.
- **Measured here (offline, no API):** pdftotext on the climate PDF (sha256 `1d58a0fa…92669`, the same file as C3) gives about **620 sentences** of ≥ 4 words (median 19 per page; 6 to 22). This is a rough regex count on pdftotext text, not PyMuPDF. It is used only to size the cost estimate.
- **External:** [I4-S1]–[I4-S13] in the I4 list in the final Sources section. The ones opened: the factoid-wiki README and LICENSE; the LangChain template files at tag `langchain==0.2.0`; `MultiVectorRetriever` (langchain-classic 1.0.8); `BaseChatModel.with_structured_output` (langchain-core 1.6.6); `from_tiktoken_encoder` (langchain-text-splitters 1.1.3); the FActScore README and `atomic_facts.py`; the claude-api skill. The rest are search-checked only.

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class (core / bridge / next) | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | A proposition: one fact, self-contained, minimal (the five properties in the upstream prompt; Dense X's definition) | Ch4 p.5–6/15; cell 12 system prompt; [I4-S1] | **missing** | I4 | no | core | One climate sentence split into propositions, with each property ticked |
| 2 | Why a multi-fact chunk vector "points at nothing": dilution | 06 v1.0 / v1.4 Problem | I1 (not written) | I1 | no | bridge | One paragraph plus the toy: a 3-fact chunk vs a 1-fact query |
| 3 | **Decontextualisation**: replacing pronouns and implicit subjects with full names | cell 12 rule 3; LangChain template rule 3 [I4-S4] | **missing** | I4 (I5 does it per chunk) | no | core | "It is the supreme decision-making body" → "The COP is…" (D-007 p.29); link forward to I5 |
| 4 | Generation with structured output (schema, validation, one retry, parse-failure log) | cells 12–13; D-22 (owner M3) | M3 (not written) | M3 | exposed | bridge | Pydantic schema → JSON Schema → strict mode → validate → log; "schema-valid is not correct" |
| 5 | **Source anchoring**: every proposition records the source sentence span(s) it came from | 06 v1.4 "pointing back to the source span" (undefined) | **missing** (no design anywhere) | I4 | no | core | Numbered-sentence prompt; the model returns `source_ids`; code checks them and stores document offsets (§6, §9) |
| 6 | **Scoring LLM-written units with span gold** (CE@k, MRR on character spans) | 06 §7.2–7.3 vs v1.4 | **missing** | I4 (M2 owns the metrics) | M2 exposed | core | The three scorings in §6 idea 6: what each one measures |
| 7 | Multi-vector retrieval: retrieve propositions, return parent chunks (small-to-big) | 04 "Build yourself"; AIQ Q5; [I4-S4, S5] | **missing** | I4 (X1 later) | no | core | Max-over-children ranking; parent dedup gives fewer than k parents (MultiVectorRetriever L105–113) |
| 8 | The QC grade is an **index-time filter**, not an evaluation (D-10); an uncalibrated 7/10 threshold (MC-006) | Ch4 p.7–9/15; cells 15–16 | M3 (not written) | I4 + M3 | exposed (MC-006 open) | core | Hand-label the filter's keep/drop on the sample; report keep-good and catch-bad rates |
| 9 | Per-proposition vs batched grading cost (DV-14) | cell 16; Ch4 p.9 vs p.13/15 | 04 only | I4 | no | core | The call-count table (§6 idea 8): 1,400 vs 33 calls on Corpus D |
| 10 | **Proposition faithfulness** (supported / added / distorted) measured by hand | 06 v1.4 guard | **missing** | I4 (M3 claim labels) | no | core | A 60-unit sample with Wilson intervals; the upstream "astronaut" example as the warning (§4 I4-E3) |
| 11 | Coverage: sentences with no proposition; gold facts no proposition reaches | none | **missing** | I4 | no | core | Deterministic `sentence_coverage` and `gold_reachability`. Both are ceilings for the proposition arm |
| 12 | Near-duplicate propositions crowd the top-k | cells 28, 36 (verified); 03 row 518 | 03 only | I4 (R4 later) | no | core | Distinct-facts@k diagnostic; Corpus D repeats paragraphs (p.10 vs p.23) |
| 13 | Atomicity loses relations: synthesis and contrast questions | 06 "When NOT"; Ch4 p.11–12/15 | **missing** | I4 | no | core | D-005 (coal vs gas contrast) and D-007 (multi-hop) as guards |
| 14 | Index size and cost multiplier (vectors ×14, LLM calls × pages) | 02 outcome "compute index-time cost" | **missing** | I4 | no | core | Cost table; "cost per 1k chunks" (02 evidence line) |
| 15 | Reasoning tokens count as output on gpt-oss-20b; `finish_reason=length` gives an empty or partial JSON | LLMOPS §2.7, §6.1 | P1 / C5 (not studied) | P1 | exposed (MC-001 open) | bridge | `max_completion_tokens` sized for about 45 propositions plus reasoning; truncation flagged |
| 16 | Few-shot examples, and **few-shot leakage** (T1 n-gram test) | ext review rows 263/388; cell 12 | **missing** | M4/M1 (I4 is the first prompt with examples) | no | core (the test) | The example must come from outside the corpus; T1 8-gram test with an injected leak |
| 17 | Fair comparison: fixed k **and** equal token budget; a degenerate baseline (k=4 over 3 chunks) | DV-15; 06 §4.1 rule 2 | 07 Part I (I1) | I1/M4 | no | bridge | Why upstream's comparison returns the whole corpus; the subset-index ceiling (§4 I4-E7) |
| 18 | Small n: MRR on about 10 factual items is nearly always inconclusive | 06 §9.4 | M4 (not written) | M4 | no | bridge | Pre-register "inconclusive" as an expected verdict; report the discordant counts |
| 19 | The model id is retired upstream (`llama-3.1-70b-versatile`) | cells 12, 15; D-04 | 04 / D-04 | I4 | no | core (short) | Read the model id from config; record the model id actually returned |
| 20 | A local propositionizer (Flan-T5-large, about 3 GB) as a no-API option | [I4-S2, S3] | **missing** | I4 | no | next (Full only) | Mentioned with its size; not run on CPU in the core path |
| 21 | Shared idea with entity extraction (Graph RAG) | 03 "S1 advice ← I4" | — | S1 | no | next | One linking sentence |
| 22 | Book text never goes into a prompt (privacy); the few-shot example is not taken from Ch4 | D-32 (5); LLMOPS §2.4 | LLMOPS only | D4 | no | bridge | `privacy.guard` on the rendered prompt; the example is written fresh |

### 3. Quiz coverage

There is no question file for Phase 4. Needed titles:
- **R:** What makes a statement a proposition (the five properties)? · Why can a proposition not be scored with the CE@k span rule directly, and what does it store instead? · Why is the 7/10 quality grade a filter and not a faithfulness measurement?
- **A:** From a given 3-sentence climate paragraph, write its propositions and the `source_ids` of each. · Count the index-time calls for 33 pages with per-proposition vs batched grading (1,400 vs 33 grading calls). · Given a ranked list of 6 propositions with parent chunk ids, compute MRR@10 on parents after dedup, and the number of distinct parents in the top 4.
- **T:** A legal-contract corpus that changes weekly, with mostly "compare clause A and B" questions: propositions or not? · Your proposition arm wins MRR but the hand-checked faithfulness is 0.80: what do you report, and can you adopt it? · The few-shot example in your generator prompt was written from page 10. What breaks, and which test catches it?
- **Interview:** AIQ 04 Q4, "What chunking strategies do you know, and how do you pick one?" Its model answer should add propositions (cost, decontextualisation, parent return). Second choice: AIQ 04 Q5 ("retrieve small, generate big").

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| I4-E1 | **Tier conflict.** 02 card "I4 · S/U"; 04 §2.4 "S/U"; 03 row 430 "S/U (drawn as S)" and class S in the graph; tracker `I4,…,S` | The three files disagree on whether I4 is S or U | Pick one. Recommendation: **S** (03 line 488 already reasons I-CMP stays E because I4/I6 are S), and fix 02/04 to "S" |
| I4-E2 | 02 I4 card Repo line "cells 9, 12–13, 15" | Leaves out cell 16 (the per-proposition grading loop, thresholds 7), cell 18 (embedding store), cells 22–24 (the degenerate baseline) and 28/36 (near-duplicates). 04 cites 9–38 | "cells 9, 12–13, 15–16, 18, 22–24, 28, 36" |
| I4-E3 | Upstream cell 12 few-shot example; cell 15 grader example; not noted in 02/04 | The example output adds "Neil Armstrong was an astronaut.", which the source sentence does not say. Cell 15's example grades that proposition 10/10 on accuracy. The prompt teaches the model to add world knowledge, and the grader rewards it | Lesson critique target. Our example is fully supported by its source |
| I4-E4 | Cell 15 grader | Every example is graded 10/10/10/10, so there is no negative anchor (leniency). Its human turn is `"{proposition}, {original_text}"`, with no labels. The labels contain typos ("Propositons", two "Evaluation_3"). The same model generates and grades (DV-13) | Note as static reading. Our grader (if used) has labelled fields and at least one failing example |
| I4-E5 | Cell 16 saved output | It prints "Fail" lines that the current code cannot print, so the output is **stale**. The output shows 2 of 31 propositions rejected (6.5%), on completeness 6 and conciseness 6. Cell 18's progress bar shows 29 embedded | Cite "≥ 31 generated, 29 kept (stale output)" only as an illustration |
| I4-E6 | 06 §2.3 `Chunk` invariant `doc_text[char_start:char_end] == text` vs 06 v1.4 | A proposition's text is not a substring of `doc_text`, so it cannot be a `Chunk`. 06 never defines what "pointing back to the source span" means, or how MRR/CE are computed for it | Add a `Proposition` / `IndexUnit` type (embed text ≠ evidence span) and the scoring rules of §6 idea 6 |
| I4-E7 | 06 v1.4 "Change: … on a subset (for example, 5 pages)" | If the **index** is restricted to 5 pages (about 15 chunks), k=4 retrieves over a quarter of the index. That is the same ceiling as upstream's k=4 over 3 chunks (DV-15) | Restrict the **eval items** to the subset if needed, never the index. Use the full-corpus index (affordable, §6 idea 8) or a mixed index |
| I4-E8 | DV-14 / 03 row 610 "1 grading call per proposition" | Per-proposition grading is the dominant cost. On Corpus D it is about 1,400 calls and 1.6M tokens, over 8 days of Groq free-tier daily tokens (plan UNVERIFIED). One batched call per page is 33 calls and about 112K tokens | Teach both; batched grading is the default; per-proposition is a measured ablation on 1 page |
| I4-E9 | 04 §3 Ch4 step 4 "cell 18 (Ollama `nomic-embed-text`)" | The model is set in cell 9 as `nomic-embed-text:v1.5`; cell 18 only builds FAISS. Minor | "cell 9 (model), cell 18 (FAISS)" |
| I4-E10 | 04 §2.4 I4 row "Ch4 p.4/15–p.10/15" vs 02 "p.4–12/15" vs DV-14 "p.13/15" | The page ranges differ. p.13/15 (the one-check-per-chunk claim) is in neither Book line | Possible error. List p.13/15 in the 02 card when the book is re-opened |
| I4-E11 | AIQ 04 Q4 answer (external) | The chunking-strategy list has no propositions | Use it as the interview item and add propositions in our model answer |

### 5. What the research says

- **Dense X Retrieval: propositions as the retrieval unit [I4-S1, I4-S2].**
  - *The study:* English Wikipedia (2021-10-13 dump) indexed three ways. The README gives the unit counts: 41M passages, 114M sentences, 257M propositions (verified). That is about 2.25 propositions per sentence and 6.3 per 100-word passage. Six dense retrievers were tested on five open-domain QA datasets (search-checked).
  - *The result (search-checked, UNVERIFIED numbers):*
    - Recall@20 rose by about +10.1 points on average for unsupervised retrievers and about +2.7 for supervised ones (v1 of the paper gives +2.2).
    - The gain was larger for rarer entities (EntityQuestions).
    - Under a fixed budget of retrieved words, propositions held the answer more often. Downstream EM@500 words was reported about +2.8 for GTR with LLaMA-2-7B (secondary summary).
  - *Its limits:*
    - Wikipedia factoid QA, where answers are short entities.
    - The propositionizer was trained for Wikipedia.
    - The gains on retrievers trained for passages are small.
    - Indexing cost is not the paper's subject.
  - *For your project:* climate prose is close to encyclopaedic text, so the factoid items (D-002, D-003) are where a gain could appear. The supervised-retriever result says to expect little with Cohere `embed-v4.0`, a strong trained embedder. Pre-register "inconclusive" as likely. The fixed-word-budget comparison is the paper's own form of 06's equal-token-budget rule.
- **The released propositionizer [I4-S2, I4-S3].** `chentong00/propositionizer-wiki-flan-t5-large`. Its input format is `Title: … Section: … Content: …` and its output is a JSON list; a parse failure gives an empty list (README, verified). The repo is Apache-2.0 (LICENSE, verified). The model's own licence was not found, and its weights are a 3.13 GB safetensors file (search snippet of the HF file list; UNVERIFIED). It is a no-API option, but heavy on CPU. Full only.
- **LangChain's propositional-retrieval template [I4-S4] (verified at tag `langchain==0.2.0`; the template is gone from `master`).**
  - Its prompt is "modified from the paper". It keeps the original wording where possible (rule 1), splits off entity descriptions (rule 2), decontextualises pronouns (rule 3), and returns JSON (rule 4), with one long Wikipedia example.
  - It forces a tool call (`tool_choice` on `decompose_content`) and runs `indexer.batch(..., {"max_concurrency": 10})`.
  - **`.with_fallbacks([RunnableLambda(empty_proposals)])`** turns any failure into an **empty proposition list without a log**. A chunk then silently drops out of the index.
  - Parents are **8,000-character** splits returned through `MultiVectorRetriever`.
  - *For your project:* "keep the original phrasing" makes span alignment easier, so adopt it. The silent fallback is the anti-pattern to test against (parse-failure rate is a logged metric). With 8,000-character parents, the "precision" of propositions disappears at the context level, which is why the parent size must be the champion chunk, not a page.
- **`MultiVectorRetriever` defaults [I4-S5] (verified, langchain-classic 1.0.8 `multi_vector.py` L105–113).** It runs `similarity_search(query, **search_kwargs)` with `search_kwargs` defaulting to `{}`, so the vector store's own k applies (4 for most stores). It then keeps the first occurrence of each parent id. **k child hits give at most k parents, often fewer.** The lesson must state this when it compares "k=4".
- **FActScore's atomic facts [I4-S8] (README and `atomic_facts.py`, verified).**
  - Decomposition runs **per sentence** ("Please breakdown the following sentence into independent facts"), with fixed demonstrations plus BM25-retrieved demonstrations (k=1, n=7 for bios; k=0, n=8 otherwise).
  - It keeps a sentence → facts mapping. It measures precision and says so (phase_03 [S5]). The README estimates about $1 of API cost per 100 sentences (2023 prices, OpenAI).
  - *For your project:* per-sentence anchoring is the cleanest answer to the span problem. Ask for propositions **with their source sentence ids** and check them in code.
- **Evidence that propositions do not always help.**
  - *Zhou, Wang, Koopman & Zuccon (2026), "Beyond Chunk-Then-Embed" [I4-S9]:* a reproduction across chunking methods. Search summaries report that DenseX-style propositions were **uniformly worse** than fixed-size, sentence and paragraph splitting for in-corpus retrieval, for example 0.3888 vs 0.4849 (Jina-v3) and 0.3883 vs 0.4863 (E5-large). It also reports that the method was among the slowest. Search-checked, UNVERIFIED; the metric and datasets are not confirmed.
  - *LumberChunker (Duarte et al., 2024) [I4-S10]:* propositions were weaker on narrative text (GutenQA). That is their own benchmark (search-checked).
  - *Upstream cells 28 and 36 (verified):* 3 of the 4 top hits are near-duplicate phrasings of one fact ("Founder Mode is an emerging paradigm…").
  - *For your project:* the null hypothesis is realistic. The "When NOT to use" section has evidence beyond the book.
- **Structured output for the generator.**
  - *Groq (search-checked; docs blocked) [I4-S11]:* `response_format: json_schema` with `strict: true` is constrained decoding, documented for `openai/gpt-oss-20b` and `-120b`. All fields must be `required`, and objects need `additionalProperties: false` (secondary). Community reports describe intermittent `400 json_validate_failed` on gpt-oss-20b even in strict mode. One staff reply says json_schema is unsupported with reasoning (conflicting, UNVERIFIED).
  - *Claude (claude-api skill, cached 2026-10-06) [I4-S13]:* Haiku 5.5 supports `output_config.format` JSON schemas. **`minimum`/`maximum` and string length limits are not supported** (the SDK strips them and validates client-side), so 1–10 scores need a code check. Structured output works with the Batches API (−50%). Haiku 5.5's minimum cacheable prefix is listed as 512 tokens ("check the docs").
  - *For your project:*
    - Request strict JSON on Groq.
    - Validate with `jsonschema` in every case.
    - Log `json_validate_failed` and `finish_reason=length` separately.
    - Retry once with `json_object` mode if strict fails (that is a new cache key).
- **Framework default to name [I4-S6] (verified, langchain-core 1.6.6 `chat_models.py` L2536–2556).** `BaseChatModel.with_structured_output` needs `bind_tools` and calls it with **`tool_choice="any"`**. Forced tool use returns a 400 on Opus 5.5 and Sonnet 5.5 (LLMOPS §6.4). So `CachedChatModel` must override `with_structured_output` to use native JSON-schema output.
- **Upstream splitter unit [I4-S7] (verified).** `from_tiktoken_encoder` defaults to `encoding_name="gpt2"` (langchain-text-splitters 1.1.3 `base.py` L284). Cell 9's "200 tokens" are GPT-2 BPE tokens, not cl100k or model tokens (MC-001).
- **Current practice (2024–2026):**
  - Index propositions or other small units and return the parent (multi-vector).
  - Generate with structured output.
  - Filter with cheap code checks before any LLM grade.
  - Contextual headers and late chunking (AIQ Q17) are the cheaper rivals for the pronoun problem.
- **How to evaluate:** retrieval metrics on parent spans and on source-sentence spans (separately); proposition faithfulness and coverage by hand and by code; cost per 1k chunks. Answer quality only by human reading (D-10).
- **Interview questions:**
  1. Chunking strategies and how to choose (AIQ Q4).
  2. Retrieve small, generate big (AIQ Q5).
  3. Proposition indexing vs contextual retrieval vs late chunking (AIQ Q17).
  4. "How would you check that LLM-rewritten index units are faithful?"
  5. "What does proposition indexing cost per 1k chunks, and what dominates it?"

### 6. Lesson blueprint

**The answer first (draft).** A chunk that holds five facts gets one vector that is a blend of all five, so a question about one of them may rank it low. Proposition chunking asks an LLM to rewrite each passage as short, self-contained statements, one fact each, with pronouns replaced by names, and indexes those instead. The rewrite is not text from the document, so every proposition must keep a pointer to the sentence it came from: that pointer is what lets you score it against span gold and return the original text. It costs LLM calls at index time: one per page to generate, plus one per page if you batch the quality grade, or one per proposition if you do not (about 1,400 calls on this corpus). Measure it as "does ranking by propositions bring the right chunk up earlier?" on factual questions, check by hand that the propositions are faithful, and expect no gain on contrast and synthesis questions, where atomic facts lose the relation.

**The theory in one read (11 ideas).**
1. *Dilution:* sim(q, chunk) is the similarity to a mixture of facts. One focused unit per fact gives a sharper match (bridge from I1).
2. *Proposition properties:* one fact; understandable alone; full names, no pronouns; dates and qualifiers kept; one subject–predicate (cell 12, Ch4 p.5–6/15 per 04). Dense X's version: distinct, minimal, self-contained [I4-S1].
3. *Decontextualisation:* resolve the referent from the surrounding text. It is the per-unit form of I5's per-chunk header.
4. *Anchored generation:* number the sentences sᵢ with spans [aᵢ, bᵢ). The model returns {text, source_ids}. Then span(p) = ∪ [aᵢ, bᵢ) for i ∈ source_ids.
5. *Alignment check:* align(p) = |content words of p ∩ content words of its sources| / |content words of p|, excluding resolved entity names. A low value flags an added fact (the "astronaut" case).
6. *Three scorings, kept separate:*
   - **(a) Parent return (primary, P→C).** Rank propositions by cosine. Map each to its champion chunk(s) by span containment. Keep the first occurrence of each parent. Score MRR@10 and CE@4 on the parent chunks with the unchanged `any_overlap` and complete-evidence rules. *Measures:* whether proposition vectors rank **the same chunks** better. The returned text and token budget are identical in kind to the chunk arm, so this is the fair A/B.
   - **(b) Proposition return (P).** rel(p) = 1 iff span(p) overlaps gold. CE over ∪ span(p) of the top k. *Measures:* whether the retrieved units **come from** the evidence. It over-credits a lossy rewrite, so it must be paired with idea 7.
   - **(c) Parent = generation unit (page).** Rejected: a page-sized parent makes any_overlap almost always true, and Hit/MRR then measure page routing only.
7. *Faithfulness and sufficiency of the text:* supported / total on a hand-labelled sample. Plus, for each gold fact reached in (b), "does the proposition **text** state the fact?" (hand). The idea-6b score counts only where the text passes.
8. *Cost:* LLM calls = pages (generation) + pages (batched grading) or + propositions (per-proposition grading). Tokens = Σ(input + output + reasoning). Index size = n_props × dim × 4 bytes. Corpus D: about 1,400 propositions vs 97 chunks, about ×14.
9. *The quality gate is a filter:* keep p iff all four grades ≥ 7. Its error rates against your labels are keep-good = kept∧good / good and catch-bad = dropped∧bad / bad. MC-006: the 7 is uncalibrated.
10. *Coverage ceilings:*
    - sentence_coverage = sentences with ≥ 1 kept proposition / sentences.
    - gold_reachability = gold alternatives overlapped by some kept span(p) / alternatives. Arm (b) can never beat this.
11. *Distinct facts@k:* the number of distinct normalised proposition texts in the top k. Near-duplicates lower it; parent dedup hides it.

**Formula sheet:** span(p); align(p); MRR@10 on parents after dedup; CE@k on ∪ span(p); faithfulness with a Wilson interval; keep-good and catch-bad; sentence_coverage; gold_reachability; distinct-facts@k; calls and cost per 1k chunks; index-size multiplier.

**Step-by-step outline.** Running example: **Corpus D p.10 and p.29** (D-002, D-007), then the 5-page subset {2, 3, 8, 10, 23}. Gold for D-001…D-006 lives on these pages, and they include the p.10/p.23 near-duplicates.
1. Show D-002 ranking under the v1.0 champion. The p.10 chunk mixes Paris, Kyoto and the UNFCCC.
2. Split p.10 into numbered sentences with offsets. Show the splitter's errors ("1.2 degrees" kept whole; headings as separate units).
3. Read the frozen prompt `prop_gen_v1`: rules, one example from outside the corpus, and a JSON schema with `source_ids`. Show the recorded response (replay).
4. Validate: schema, ids in range, align(p). Find the flagged propositions. Label 10 by hand.
5. Decontextualisation on p.29: COP/UNFCCC pronouns resolved, so D-007's bridge fact stands alone.
6. Read the batched grade for p.10 (`prop_grade_v1`). Compare its keep/drop with your labels (idea 9).
7. Embed the kept propositions (Cohere, cached; MiniLM fallback). Rank for D-002. Compute arm (a) and arm (b) by hand for the top 6.
8. Run the subset metrics and the full-corpus metrics. Fill the v1.4 table (empty until run): fixed k, then equal budget.
9. Read the guards: D-005 (contrast) and D-007 (multi-hop) CE@4, distinct-facts@4, and the cost table.
10. Write "When NOT to use" from your own data.

**Visuals:**
- **Chunk vs propositions diagram (SVG):** one p.10 chunk fanning into 8–12 proposition cards, each with an arrow to its sentence span. *Shows* that propositions are rewrites with pointers.
- **Three-scorings diagram:** a ranked list of propositions mapped (a) to parents with dedup and (b) to sentence spans. *Shows* why the two MRRs differ.
- **Cost bars (Plotly):** calls and tokens for generation, batched grading and per-proposition grading, subset vs Corpus D, with the 200K TPD line. *Shows* that the grader dominates.
- **Faithfulness strip:** labelled sample units coloured supported / added / distorted, with a Wilson bar.
- **Top-k crowding chart:** distinct-facts@k vs k for propositions vs chunks.

**Full only:** Dense X details and the word-budget curve; the Flan-T5 propositionizer; per-proposition grading as an ablation; FActScore's demo retrieval; the mixed index design; LangChain's template critique (silent fallback, 8K parents); the Zhou et al. 2026 counter-evidence.

### 7. Verify notebook plan

`study/notebooks/I4_propositions_verify.ipynb` (plain Python; Plotly).
1. **Mechanism without an LLM:**
   - a hand-written proposition set for p.10 (written by Yash in the lab, stored as JSONL with `source_ids`);
   - the sentence splitter with offsets and tests (decimals, "e.g.", headings);
   - `span(p)`, `align(p)` and the parent mapping, with asserts: every span lies inside `doc_text`; every parent contains its span;
   - a toy ranked list giving arm (a) and arm (b) MRR, CE and distinct-facts by hand and by code.
2. **Upstream reproduction (static):** count cell 16's stale rejections (2/31); show cells 28/36 duplicates; compute that k=4 over 3 chunks equals the whole corpus.
3. **Recorded LLM run (replay by default):**
   - 5 generation calls + 5 batched grading calls on the subset (Groq gpt-oss-20b, `reasoning_effort=low`);
   - optional: 1 page with per-proposition grading (about 40 calls) for the cost ablation;
   - all through `llmops.cache`, so a `ReplayMiss` lists the missing keys.
4. **Metrics:** sentence_coverage, gold_reachability, parse-failure rate, `finish_reason` counts, tokens including reasoning, cost if called vs paid.
5. **Retrieval:** MiniLM (offline) and Cohere (cached) embeddings of propositions. Arms (a) and (b) vs the champion on the D seed items, at fixed k=4 and at equal budget (choose k so the mean context tokens match).
6. **Hand-label cell:** load `labels.jsonl` (60 units). Faithfulness with Wilson; the filter's keep-good and catch-bad.

API calls: **0 in replay.** To record: 10 Groq calls (+ about 40 optional), and Cohere embed of about 190 texts (2 calls of ≤ 96). Runtime replayed: under 1 minute (MiniLM about 10 s on CPU).

### 8. Apply-it tool plan and real-world checklist

`study/tools/proposition_fit_check.py`: "Would proposition indexing help on MY documents, what would it cost, and are the propositions faithful?"
- **Inputs:**
  - `--docs` (PDF/MD/TXT);
  - optional `--questions` JSONL (`q`, `expect` text, `type`);
  - `--pages` or `--sample N` (default 3 pages);
  - `--provider groq|anthropic`, `--grading batched|per-prop|off`;
  - `--budget-usd`;
  - `--mode replay|auto|record`.
- **Outputs:** a Markdown report with:
  - the cost forecast for the whole collection (calls, tokens, $, Groq quota days);
  - the sample propositions with `source_ids` and align scores;
  - a labelling sheet (CSV) for faithfulness;
  - coverage numbers;
  - with questions, MRR on parents (arm a) vs the plain chunks;
  - the checklist and a recommendation.

**Real-world checklist (12 checks)**

| # | Check | Auto / manual |
|---|---|---|
| C1 | Forecast before any call: calls, tokens (reasoning included) and $ for the whole collection, vs the budget and the Groq daily quota | auto |
| C2 | Every LLM response is schema-valid. Parse-failure and `finish_reason=length` rates are under 2%. Failures are logged, never silently emptied (the LangChain fallback trap) | auto |
| C3 | Every `source_id` exists. Every span lies inside the document text | auto |
| C4 | Alignment: the share of propositions with align(p) < 0.5 is listed (likely added facts) | auto + manual (read the list) |
| C5 | Hand-checked faithfulness on ≥ 30 units, with a Wilson lower bound reported | manual (the labelling sheet) |
| C6 | sentence_coverage ≥ 0.9; sentences with no proposition are listed (lost facts) | auto |
| C7 | No pronoun-initial propositions ("It", "They", "This"…) left (decontextualisation) | auto |
| C8 | Near-duplicates: distinct-facts@4 and the share of duplicate normalised texts | auto |
| C9 | The quality grade (if on) is compared with your labels: keep-good and catch-bad with n | auto (once labels exist) |
| C10 | The prompt has no text from your eval questions or gold quotes (8-gram leakage test), and no book text (privacy guard) | auto |
| C11 | Your questions are mostly single-fact lookups, not compare or summarise (from `type` or a keyword heuristic) | auto + manual |
| C12 | The corpus is stable (re-indexing cost on change = calls × changed pages) | manual (how often do the documents change?) |

**Recommendation logic:**
- C2 or C3 fails → "fix generation (token cap, schema) before measuring".
- C5 lower bound < 0.85 or many C4 flags → "propositions are rewriting facts; do not index them; consider I5 headers".
- C11 is mostly synthesis → "keep chunks; propositions lose relations".
- Arm (a) MRR does not improve and C1 is high → "not worth the index cost".
- Otherwise → "adopt as a multi-vector index that returns parents; re-run on new documents".

### 9. LLMOps notebook plan

`study/llmops/notebooks/I4_propositions_ops.ipynb`. Proposition indexing as an index-build job, after the mechanism.
- **Framework build** (each piece maps to a lesson step):
  - `PromptTemplate` from the frozen `prompts/prop_gen_v1.txt` → step 3.
  - `CachedChatModel(provider="groq", model=GROQ_MODEL_ID, params={temperature: 0, reasoning_effort: "low", max_completion_tokens: 4096, seed: 0})`. `with_structured_output(PropositionSet, method="json_schema", strict=True, include_raw=True)` is **overridden in the adapter**, because the core default forces `tool_choice="any"` [I4-S6] → steps 3–4.
  - `.batch(pages, {"max_concurrency": 2})`, kept under the token throttle; the run resumes from `index_build.jsonl` → step 3.
  - Grader: a second chain, `prop_grade_v1` (batched per page) → step 6.
  - Indexing: `CachedEmbeddings` + a small in-memory vector store; a `MultiVectorRetriever`-style parent mapping written in plain Python, because langchain-classic is read-only. Its dedup and k defaults are named [I4-S5] → step 7.
  - **Defaults to name:** `ChatGroq` temperature 0.7 and the server-side `reasoning_effort` (LLMOPS §9.2); `with_structured_output`'s forced tool call; `MultiVectorRetriever` returning fewer than k parents; the LangChain template's silent `with_fallbacks`.
- **Caching:**
  - Cache key = LLMOPS §2.3 key (provider, exact model, all params, `response_format` schema, rendered messages). The rendered prompt contains `prompt_version` + the page text, and the run manifest adds `doc_text_sha256` and `snapshot_id`.
  - External calls:
    - subset: 5 + 5 Groq;
    - full Corpus D: 33 + 33 Groq;
    - optional per-proposition ablation on 1 page: about 40;
    - Cohere embed: about 2 calls (subset) or about 15 (Corpus D, ≤ 96 texts per call).
  - Haiku 5.5 arm (optional, credits): the same 66 calls.
  - Everything replays with no key.
- **Tracing (`llm-observability`):**
  - One root span per index build: `build_id`, `snapshot_id`, prompt versions, model requested and returned, `system_fingerprint`.
  - One LLM span per page: tokens in, out and reasoning; `finish_reason`; latency and Groq `queue_time`; cost; `cache_key`; parse status; retries.
  - Proposition records carry `prop_id`, `source_ids`, span, align score, grades, kept flag, `parent_chunk_ids`.
  - Retrieval spans per query: ranked `prop_id` with scores, then the deduplicated parent list.
  - Local: JSONL + Phoenix. LangSmith only for Corpus D, inside `tracing_context`, after `privacy.assert_corpus_is("D")`.
- **Dataset and evaluators (`code-based-evaluators`, `rag-evaluation`):**
  - Retrieval evaluators: arm (a) MRR@10 and CE@4 on parents; arm (b) MRR@10 and CE@4 on source spans; distinct-facts@4.
  - Index evaluators: parse-failure rate, sentence_coverage, gold_reachability, align-flag rate, pronoun-initial rate.
  - Human labels: `labels.jsonl` (unit = proposition; `labeller`, `rubric_version`).
  - **No LLM judge** (D-10). The quality grader is a pipeline component and is evaluated *against* the labels.
- **Experiment:** v1.4 vs the v1.0 champion (or the current v1.x champion) and v0, on identical comparison keys (06 §4.1). Report fixed k and equal budget, plus the grader-on vs grader-off ablation. Selection on dev; one logged test touch.
- **Cost, latency, tokens:**
  - Index build: calls, tokens (reasoning share), $ if called vs $ paid, wall time including throttle waits, and **cost per 1k chunks**.
  - Query time: p50/p95 of embed + search (unchanged in kind, but over about ×14 vectors).
- **Prompt and config versioning:** `prompts/prop_gen_v1.txt`, `prompts/prop_grade_v1.txt` and `schemas/proposition_set_v1.json` are frozen and their sha256 is traced. The config records `generation_unit: page`, `parent: champion params_hash`, `grading: batched|off`, `threshold: 7`.
- **Monitoring and feedback (`ci-cd-evals`, `error-analysis`):**
  - Watch the parse-failure rate, the length-stop rate, align flags, propositions per page (a sudden drop means silent truncation), cost per rebuild, and new fingerprints.
  - Alert if parse failures exceed 2%, or propositions per page fall below 50% of the recorded mean.
  - Added-fact propositions found by hand go to the M5 log, and to the T1 regression fixtures as an "alignment must flag this" case.
  - The **T1 leakage test** (8-gram overlap of the prompt and few-shots against eval questions and gold quotes, with an injected leak) is created here if I4 is the first prompt with examples (review rows 263/388).
- **Lifecycle:** Analyze (failure bucket: dilution on factual items) → Measure (arm a/b, faithfulness, cost) → Improve (adopt or reject). dev → CI: the T1 leakage test, the schema and alignment tests, and a replay test of the index build. Monitoring: the rebuild-cost row on the monitor page.
- **Skills:** `rag-evaluation`, `code-based-evaluators`, `llm-observability`, `ci-cd-evals`, `improving-llm-agents` (batching the grader is a cost cascade), `error-analysis`, `collaborative-annotation` (self-agreement on 10 re-labelled units).

**Cost estimates** (assumed tokens, not measured. Generation: about 1,050 in / 1,600 out including reasoning per page. Per-proposition grading: 870 / 300. Batched grading: 1,800 / 1,600 per page. Prices from LLMOPS §6.2. The Groq free-tier plan is UNVERIFIED.)

| Scope | Generation | Grading, batched | Grading, per proposition | Groq total (gen + batched) | Groq quota |
|---|---|---|---|---|---|
| Subset, 5 pages (about 190 props) | 5 calls, Groq $0.003 / Haiku $0.005 | 5 calls, $0.003 / $0.005 | 190 calls, $0.030 / $0.045 | 10 calls, about 30K tokens, **$0.006** | ≥ 4 min; 0.15 of a day |
| Corpus D, 33 pages (about 1,400 props) | 33 calls, $0.018 / $0.030 | 33 calls, $0.020 / $0.032 | 1,400 calls, $0.22 / $0.33 | 66 calls, about 200K tokens, **$0.04** | ≥ 25 min; about 1.0 day |
| Corpus D with per-proposition grading | — | — | — | 1,433 calls, about 1.7M tokens, $0.24 | ≥ 3.6 h; **about 8.6 days** |
| Per 1k chunks of 1,000 chars (gen per chunk, about 14 props/chunk) | Groq $0.23 / Haiku $0.36 | $0.28 / $0.43 | $2.17 / $3.32 | — | 1.35M tokens for generation alone |

Money is never the obstacle; the Groq daily token quota is. Groq prompt caching (cached tokens do not count toward limits, LLMOPS §6.2) and Claude's Batch API (−50%) lower these numbers. Haiku 5.5 is worth it only to remove the quota wait. The Haiku rate limits for Yash's tier are unknown.

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version (pin a released version ≥ 2 weeks old) | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Proposition generation (default) | Groq `openai/gpt-oss-20b` via `.env` `GROQ_MODEL_ID`, `reasoning_effort=low`, strict `json_schema` | `groq` 1.7.0 | yes | replay only | 10 calls (subset) / 66 (Corpus D) ≈ $0.006 / $0.04 | Apache-2.0 (SDK) | yes; strict support search-checked, **UNVERIFIED** |
| Generation, Claude arm (optional) | `claude-haiku-5-5`, effort `low`, `output_config.format` | `anthropic` 1.11.0 | no | replay only | same calls ≈ $0.009 / $0.06; Batch −50% | MIT | yes (D-32); validate 1–10 ranges in code (no min/max in schemas) |
| Schema and validation | `pydantic` → JSON Schema; `jsonschema` | 2.13.5 / 4.26.0 | yes | yes | — | MIT | yes |
| Sentence split + offsets | own regex splitter (stdlib `re`); `regex` is available | 2026.9.29 | yes | yes | — | Apache-2.0 / PSF | yes |
| Alignment | stdlib `difflib` + content-word overlap | — | yes | yes | — | PSF | yes (no rapidfuzz needed) |
| Embeddings | Cohere `embed-v4.0` (`search_document` / `search_query`); MiniLM fallback | `cohere` 7.2.0; sentence-transformers 6.1.0 | yes | MiniLM yes | about 2 / 15 embed calls; Cohere price UNVERIFIED | MIT / Apache-2.0 | yes |
| Token counts for the forecast | `tiktoken` cl100k as a proxy; provider usage as the truth | 0.14.0 | yes | yes | — | MIT | yes (a proxy only, MC-001) |
| Local propositionizer (Full only) | `chentong00/propositionizer-wiki-flan-t5-large` via `transformers` | — | weights not cached | yes, after download | about 3.13 GB weights (UNVERIFIED); slow on CPU | repo Apache-2.0; model licence **UNVERIFIED** | heavy; **not in the core path** |
| Framework | `langchain-core` (prompt, batch, `with_structured_output` override in the adapter) | 1.6.6 | no | yes | — | MIT | yes (after the mechanism) |
| Multi-vector reading | `langchain-classic` `MultiVectorRetriever` | 1.0.8 | no | — | — | MIT | read only; reimplement the parent mapping |
| Graph | `langgraph` | 1.2.12 | no | yes | — | MIT | **not needed** (a linear build) |
| Provider integrations | `langchain-groq` / `langchain-cohere` | — | no | — | — | MIT | **no** (SDK conflicts; adapters instead) |
| Tracing (hosted) | `langsmith` | 0.14.4 | no | no | free plan | MIT (SDK) | Corpus D only |
| Tracing (local) | JSONL + `arize-phoenix-otel` 0.17.2; server via `uvx arize-phoenix@20.19.0` | as listed | no | yes | $0 | Apache-2.0 / ELv2 | yes |

**Install lines** (do not run): none for the lesson and verify notebook. The LLMOps notebook uses the LLMOPS §11 `llmops` group (`uv add --group llmops langchain-core==1.6.6 langsmith==0.14.4 arize-phoenix-otel==0.17.2`). Claude arm: `uv add --group llmops anthropic==1.11.0`.

**Keys:** `GROQ_API_KEY` and `COHERE_API_KEY` (present); `ANTHROPIC_API_KEY` (optional arm); `LANGSMITH_API_KEY` (optional, Corpus D only). Never print them.

### 11. Open questions for Yash (preferences only)

- Index scope for v1.4: **full Corpus D** (66 Groq calls, about 1 day of free-tier quota, no ceiling effect; recommended) or **5-page index** (02/06 wording; cheaper, but a ceiling risk)? Either way, the hand-checked sample is the 5 subset pages.
- Run the optional Haiku 5.5 arm when you have credits (about $0.06 for Corpus D), to see whether a second generator changes faithfulness? **yes / no** (recommendation: no, unless Groq faithfulness is below 0.85).

---

## Concept I5: Contextual chunk headers / contextual retrieval

Project version v1.2. Priority U. Pre (02): I1, C3. Tracker: `not_started` (O1-Q12 logged that Yash did not name contextual headers when asked how to fix a version-string retrieval miss).

### 1. Sources checked

- **Book (not opened in this session, UNVERIFIED).** Taken from 04 §2.4, the 04 §3 Ch7 table, 04 §5, DV-19 and DV-20, plus 02, 03, 07 and 08:
  - Ch7 p.1–2/11: the problem. Chunks lose pronoun referents and headings (per 02 and 07 D.8; the phase_02 file marks p.1–2 as checked).
  - Ch7 p.4/11: document-title generation. C3 also cites p.4/11 for the point that headers change only the preparation phase.
  - Ch7 p.4–7/11: steps (per 02). 04 §2.4 gives p.4/11–p.9/11.
  - Ch7 p.7/11: embed and store the augmented chunks (per 04).
  - Ch7 p.8/11: the sketch, richer headers (summary, section path), and the advice to reuse the header for reranking and generation.
  - Ch7 p.8–9/11: the "0.1 → 0.9" impact claim, which the book frames as an embedding effect (per 08 B13). It was never measured in the book.
- **Repo (verified).** `all_rag_techniques/contextual_chunk_headers.ipynb` @ `009adba`, downloaded to the session scratchpad, all 17 cells read (0-based) [I5-S9]:
  - cell 0: CCH overview. Its text matches dsRAG's README "AutoContext" paragraph almost word for word [I5-S3].
  - cell 8: downloads the climate PDF **and** the Nike 10-K text.
  - cell 9: `RecursiveCharacterTextSplitter` with 800 characters and overlap 0, run on **the Nike `.txt`**, not the climate PDF. It imports from `langchain.text_splitter` (cell 6 also imports from `langchain_text_splitters`) and calls `open()` with no encoding.
  - cell 11: the title prompt. It truncates to `MAX_CONTENT_TOKENS = 4000` with the `gpt-3.5-turbo` encoder (cl100k) while calling `gpt-4o-mini`. It reuses the same 4000 as the output `max_tokens`, sets `temperature=0.2`, and hard-codes "~3000 words" in the truncation message. Saved output: `NIKE, INC. ANNUAL REPORT ON FORM 10-K`.
  - cell 13: Cohere `rerank-english-v3.0` through the v1 `cohere.Client`. It scores one chunk (index 86) twice for the query "Nike climate change impact": once bare and once with `Document Title: …` prepended. Saved output: 0.10576342 → 0.92206234. **The output is stale.** The source prints "Similarity without …" at 4 decimals, but the saved output shows "Similarity w/o …" at 8 decimals.
  - cell 14: the narrative of the 0.1 → 0.92 jump.
  - cell 15: KITE results (4.72 → 6.04, with the CCH arm using title **plus document summary**) and FinanceBench "83% vs 19%" (CCH and RSE tested jointly).
  - Execution counts run 4, 5, 13 across cells 9, 11 and 13.
  - No vector index is built anywhere (DV-20 stands).
- **Course files.** 02 I5 card (L608–620) and §4 per-technique gate (L1149–1157); 03 rows L431, L519, L611 and L745; 04 §2.4 row L164, Ch7 table L451–478, §5 row L960, DV-19 and DV-20; 06 §3.2, v1.2 card (L553–562), §5.1, §6.2, §6.7 seeds, §7.3, §9.2–9.4 and risk row L1470; 07 D.8 and the technique table L515; 08 L53, L93, L161, L251, L379; C3 lesson and `C3_FACTS.md` (`preproc_version` rule, item 5); LLMOPS_FOUNDATION §2.3, §6.2, §6.4 and §12; review rows 249, 250, 251, 402 and L446.
- **AE book:** nothing specific to I5 in the review or phase_03 (not re-opened).
- **Interview repo:** AIQ `04-rag-and-retrieval/questions.md` Q17 @ `e080df2` (MIT, "Copyright (c) 2026 Om"), which covers contextual retrieval and late chunking [I5-S10]. SDG `06-retrieval-systems/10-contextual-retrieval.md` @ `ed955b2` was opened, as a pointer only [I5-S11].
- **Corpus D measured here (scratch, not course code).** The climate PDF was downloaded from the pinned upstream (sha256 `1d58a0fa…92669`, which matches C3). Font specs came from `pdftohtml -xml` and page text from `pdftotext` (poppler, already installed). The script was kept in the session scratchpad only, and the numbers are in §5.
- **External** (7 opened, 2 search-checked): [I5-S1] Anthropic blog, [I5-S2] Anthropic cookbook guide, [I5-S3] dsRAG, [I5-S4] late chunking (GitHub README), [I5-S5] Merola & Singh 2025 (search only), [I5-S6] Groq prompt caching (search only), [I5-S7] Claude prompt-caching facts (`claude-api` skill), [I5-S8] LlamaIndex source, [I5-S12] Cohere rerank model list (search only).

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class (core / bridge / next) | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | "Contextually anonymous" chunk: pronouns, implicit subject, orphaned heading | 02 I5 Failure; Ch7 p.1–2/11; 07 D.8 (16 orphaned headings) | 07 D.8 names it (C2, not studied) | I5 | no | core | Open with a real Corpus D chunk that has lost its heading |
| 2 | Chunk record fields: `text`, `char_start/end`, `page_segments`, the invariant `text == doc_text[start:end]` | header storage; CE scoring | C3 (not studied) | C3 | no | bridge | Show that a header **must not** go into `text`; add an `embed_text` field |
| 3 | `preproc_version` → `embed_hash` → new index folder | rebuilding the index for each header arm | C3 item 5 (not studied) | C3 | no | bridge | One line: header template id = `preproc_version`; otherwise two arms share a folder name |
| 4 | Heading extraction from font sizes (PyMuPDF `get_text("dict")`) | the deterministic header source | **missing** (I2 owns it; 02 I5 Pre does not list I2 or C1) | I2 / C1 | no | bridge | A short function in Short mode; the full detector stays in I2 |
| 5 | Heading path vs leaf heading; which heading a chunk gets (path at chunk start, majority, all headings inside) | 06 v1.2 "doc title > section heading" | **missing** | I5 | no | core | Show p.10 chunk 34: the path at its start says "Chapter 6", yet the chunk contains the "Paris Agreement" subsection |
| 6 | A constant prefix carries no discriminating information (one document gives one title) | 06 v1.2 hypothesis; 04 §2.4 "title header vs none" | **missing**; 03 L611 says "single-document corpora" only as a weakness | I5 | no | core | A formula plus a negative-control arm (title only) |
| 7 | Three separate decisions: header text in the **embedding** input, in the **BM25** input, in the **generation** input | 02 outcomes; 06 v1.2; Ch7 p.8/11 | **contradictory** (02 vs 06; §4) | I5 | no | core | A 3-column decision table; v1.2 changes the embedding input only |
| 8 | Mean pooling: the header's share of tokens dilutes short chunks | header dilution | P4 (not studied) | P4 | no | bridge | Formula `h/(h+c)`; numbers for 1,000- vs 400-character chunks |
| 9 | Truncation: header + chunk > `max_seq_length` (MiniLM 256) drops the chunk's **tail** | 06 §3.2; 07 D.6 | 07 D.6 (C2, not studied) | C2 / P4 | no | bridge | Worked numbers: 182 + 27 vs 182 + 100 tokens |
| 10 | `input_type` asymmetry: headers on documents only; queries unchanged | embedding both sides | P4 / C3 (not studied) | P4 | no | bridge | One line: query vectors are reused unchanged across arms (cache hit) |
| 11 | Near-duplicate distractors and the "header magnet" (every chunk of a section pulled toward the section title) | 06 v1.2 (p.10 vs p.23) | 06 only | I5 / M1 | no | core | The 11 reused heading names on Corpus D (§5); a margin chart |
| 12 | Header-query leakage: questions written from headings inflate header gains | evaluation | **missing** | M1 | no | core (Full) | A trap box; also the upstream demo query names the header's entity ("Nike") |
| 13 | LLM contextualization: whole document + chunk → a 50–100-token context [I5-S1] | Source C #31; 06 second arm | **missing** in the course | I5 | no | core | The prompt shape, its cost, and what it adds beyond a path header |
| 14 | Cost ladder: 0 calls → 1 per document → 1 per chunk (window) → 1 per chunk (whole document) | review 249; 06 cost line | **missing** | I5 | no | core | Ladder table with calls and tokens for Corpus D and T |
| 15 | Prompt caching: prefix match, minimum length, TTL, write/read multipliers; Groq automatic 50% | the LLM arm's cost | **missing** (P1 not studied; D2 later) | D2 / P1 | no | bridge | Cost formula plus the D numbers; "the document first, the chunk last" |
| 16 | Rate limits make the whole-document arm infeasible on Groq's free tier (13K tokens per request > 8K TPM) | LLMOPS §6.4 routes I5 to Groq | **missing** (§4) | I5 / D2 | no | core | Arithmetic box; three fixes |
| 17 | Cache key must include the document (hash) and the prompt version | review 402; 06 risk row L1470 | LLMOPS §2.3 (not studied) | LLMOps | no | bridge | Show that a chunk-hash-only key serves stale contexts after a page edit |
| 18 | Hallucinated context: entities or numbers not in the document; wrong section | LLM arm | **missing** | I5 / V1 | no | core | Deterministic entity-in-document check plus a hand-read of 10 |
| 19 | Vendor metric vs our metric: 1 − recall@20 (relative 35%) vs CE@4 | review 250, L446 | **missing** | M2 | exposed | core | Convert 5.7% → 3.7% into absolute and relative change; the detectable effect at n ≈ 50 (06 §9.4) |
| 20 | Reranker score vs embedding similarity (DV-19) | Ch7's 0.1 → 0.9 | 03 L745 (removed dependency) | R3 | no | bridge | One paragraph: a cross-encoder relevance score on n = 1 is not a retrieval metric |
| 21 | CE@k, paired bootstrap, per-category n, dev/test discipline | v1.2 experiment | M2 / M4 (M2 exposed, M4 not) | M2 / M4 | partly | bridge | Reuse the I1 runner; report discordant pairs |
| 22 | Contextual BM25 (header terms in an inverted index; constant terms get idf ≤ 0, then the floor) | 02 outcome; Anthropic | P3 (not studied) | R1 (v2.0) | no | next | Link: tested at v2.0 by reusing I5's `bm25_text` field |
| 23 | Late chunking (pool token vectors per chunk after encoding the whole document) | review 251 | **missing** | I5 | no | next (Full) | One row: needs token-level outputs; impossible with Cohere's API; MiniLM's 256-token window makes it pointless |
| 24 | Contextual chunk embedding APIs (voyage-context-*) | SDG | **missing** | — | no | next | One line: outside the project's decisions (Voyage is not used) |
| 25 | Headers shown to the generator (`[1] (climate:10 · Ch6 › …)`) | Ch7 p.8/11; 02 outcome 2 | **missing** | C5 / X3 | no | next | Separate later arm (generation side; judged at the end under D-10) |
| 26 | Index time vs query time | I5 is index time; display is query time | open MC-003 | C5 / P7 | no | bridge | Name it explicitly; one review item touches MC-003 |

### 3. Quiz coverage

No question file exists. Titles needed:

- **R (recall)**
  - What makes a chunk "contextually anonymous", and which two kinds of context can a header restore?
  - In a one-document corpus, why can a title header add no discriminating information, and what can it still change?
  - Name the three inputs a header can be added to. Which one does v1.2 change?
  - Why must the header live in a field separate from the chunk `text`?
  - What exactly does Anthropic's "35%" measure?
  - Why does prompt caching make the per-chunk, whole-document arm cheap, and what makes a cache silently miss?
- **A (apply)**
  - A chunk has 182 MiniLM tokens. Add a 27-token path header, then a 100-token LLM context: which text is truncated, and where?
  - Using the D numbers and Haiku 5.5 prices, compute the cost of the whole-document arm with and without caching.
  - Write the path headers of the p.10 and p.23 "Paris Agreement" chunks. Which heading level separates them?
  - Turn 5.7% → 3.7% into an absolute and a relative change. On 50 questions, is that detectable (06 §9.4)?
- **T (troubleshoot)**
  - Headers raised CE@4 on near-duplicate items but lowered it on factual-single-span items. What do you check first?
  - After an edit to page 12, the LLM contexts for page-12 chunks came back from cache unchanged. What was wrong with the key?
  - The first Groq contextualization call fails with a "request too large / TPM" error. Why, and what are two fixes?
  - A teammate's questions were written by reading the section titles, and headers gave +20 points. What is suspicious?
- **Interview:** AIQ 04 Q17, "Explain contextual retrieval. What problem does it solve, and how does late chunking relate?" (MIT, © 2026 Om) [I5-S10]. Its model answer recommends prepending "document title + heading path … unconditionally". Use the Corpus D finding (a constant title) as the follow-up that tests understanding.

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| I5-E1 | 02 I5 outcome 1 ("for both embedding and BM25 text") vs 06 v1.2 ("embedding input only") and review row 402 | Contradiction. BM25 arrives only at v2.0, so v1.2 cannot test the BM25 side | 02: "embedding text at v1.2; the BM25 text field is stored and first tested at v2.0 (R1)" |
| I5-E2 | 06 v1.2 hypothesis "`doc title > section heading`"; 04 §2.4 experiment "title header vs none; then title + section path" | On Corpus D the doc title is the same for all 97 chunks, so a title-only arm carries no discriminating information. "Section heading" is ambiguous: a leaf heading collides across chapters (11 reused names, §5) | Primary arm: the **full heading path** (chapter › section › subsection). Run title-only as a negative control on D; test titles on T (multi-document) |
| I5-E3 | 02 I5 Pre "I1, C3" | The deterministic header needs heading extraction (C1 `get_text("dict")`, I2's detector), and the BM25 side needs P3 | Pre: I1, C3, **I2** (heading parser; v1.1 precedes v1.2 anyway); BM25 part → R1 |
| I5-E4 | LLMOPS §6.4 (contextual headers on Groq gpt-oss-20b, `reasoning_effort=low`) | The whole-document arm sends about 13K tokens per call on Corpus D (72,593 chars ÷ 5.57 chars/token, DERIVED). That exceeds the 8K TPM free-tier limit **per request**, and 97 calls ≈ 1.29M input tokens ≫ 200K TPD (limits plan UNVERIFIED) | Groq: chapter-window arm only. Whole-document arm: Haiku 5.5 with caching (≈ $0.03 per D build, §5), or a paid Groq tier |
| I5-E5 | 06 risk row L1470 "caching by chunk hash" | A chunk-hash key goes stale when the rest of the document changes (review 402) | Use the LLMOPS §2.3 key (full messages, so the document text is part of the key) plus `prompt_version`; store `doc_text_sha256` with each context |
| I5-E6 | 06 v1.2 "Change: embedding input only" | Silent on where the header is stored. Writing it into `text` breaks the C3 span invariant and CE scoring | Add `embed_text` (and later `bm25_text`, `display_text`) fields; bump `preproc_version` (C3 item 5) |
| I5-E7 | 04 Ch7 table (L459–465) | Step order vs pages looks inconsistent: step 1 "chunk" cites p.8/11 and step 2 "title" p.4/11. 02 gives the steps as p.4–7/11, 04 §2.4 as p.4–9/11. Book not re-opened | Re-check at the I5 lesson session against the PDF |
| I5-E8 | Upstream cell 15 (copied from dsRAG) | FinanceBench "83% vs 19%" is out of date. The current dsRAG README reports 96.6% for dsRAG and 32% for its own re-run baseline (19% "according to the paper") [I5-S3]. The KITE CCH arm also used a document **summary**, not only the title | Cite dsRAG's README directly, with the date, as vendor-reported, n = 50 questions, judged by GPT-4o |
| I5-E9 | Upstream cells 8–13 | The demo runs on the Nike 10-K, not Corpus D, so it cannot be replayed on the course corpus. Its query contains the exact entity the header supplies ("Nike") | Lesson: show the demo as a constructed best case; re-measure on D with retrieval metrics |
| I5-E10 | 04 Ch7 "Outdated" list | Add: cl100k encoder used for a `gpt-4o-mini` truncation; `max_tokens=4000` reused for a title; the stale cell-13 output label. `rerank-english-v3.0` is still listed in Cohere's docs, but the latest models are `rerank-v4.0-pro/-fast` (search-checked, UNVERIFIED) | Extend the list |
| I5-E11 | 02 Ext "vendor-reported numbers, not reproducible here" | Anthropic's eval data (737 chunks, 248 queries) is public in the cookbook [I5-S2]. It is "not reproducible under our decisions" (it needs Voyage embeddings and Claude), not unpublished | Reword |

### 5. What the research says

**Corpus D facts measured here** (scratch run of `pdftohtml`/`pdftotext`; the verify notebook must re-measure them with PyMuPDF 1.26.7):

| Fact | Value |
|---|---|
| Heading levels by font | 24 pt bold title (1), 18 pt bold chapters (21; Chapter 5's title wraps onto 2 lines), 13.56 pt bold sections (68), 12 pt **bold** subsections (192), 12 pt regular body. (Lead's note: `pdftohtml` renders at its default 1.5× zoom, so it printed 36/27/20/18 pt; the true sizes above match I2's raw-PDF reading. The counts agree exactly.) |
| PDF metadata Title | **none** (`pdfinfo` lists no Title), so `doc.metadata["title"]` would be empty; the title comes from the 24 pt line |
| Headings per page | 281 headings over 72,593 chars: about one heading every 260 characters |
| Path header length (title › chapter › section › subsection) | 75 / 120 / 168 chars (min / median / max over 260 leaf headings). That is about 19 / 27 WordPiece tokens at 6.20 chars/token (DERIVED; MC-001 ratio) |
| Title-only header | 28 chars, identical for every chunk |
| Heading names reused under different chapters | 11. Examples: Paris Agreement (Ch6 p.10, Ch16 p.23); Smart Grids (Ch5 p.8, Ch15 p.22); Carbon Capture and Utilization and Carbon Utilization (Ch5 p.8, Ch15 p.23); Marine Ecosystems (Ch3 p.5, Ch9 p.13); Youth Engagement (Ch8 p.13, Ch21 p.32); International Collaboration (Ch6 p.10, Ch10 p.16) |
| Paris near-duplicates | p.10 path: Ch6 "Global and Local Climate Action" › International Collaboration › Paris Agreement. p.23 path: Ch16 "Global Cooperation and Governance" › International Agreements › Paris Agreement. The leaf is identical, so **only the chapter and section levels separate them** (06 v1.2's help/hurt question, confirmed structurally) |
| Chunks with no heading line inside them | 18 of 120 in a scratch 1000/200 split of `pdftotext` text. That split does not reproduce C3's 97 chunks, so re-measure on the real 97 |

The key point: **Corpus D is heading-dense.** Most chunks already contain a heading, so D has little "anonymity" to repair below chapter level. Expect a small effect on D, and a ceiling. T (papers, few headings per page, phrases like "our method") is where I5 can matter. Following 06 §5.1, T results drive the decision.

**Anthropic, "Introducing Contextual Retrieval" (2024-09-19) [I5-S1].**
- *Study:* an LLM (Claude 3 Haiku) writes a 50–100-token context per chunk, given the whole document and the chunk. The context is prepended before embedding ("contextual embeddings") and before BM25 indexing. Domains: codebases, fiction, arXiv papers and science papers. Top-k values 5, 10 and 20 were tested; the reranker was Cohere, with 150 candidates reranked to 20.
- *Result:* metric = **1 − recall@20** (the share of relevant chunks missing from the top 20). Baseline 5.7% → contextual embeddings 3.7% (−35% relative) → plus contextual BM25 2.9% (−49%) → plus reranking 1.9% (−67%). One-time cost with prompt caching: $1.02 per million document tokens, assuming 8K-token documents, 800-token chunks, 50 tokens of instructions and 100 tokens of context.
- *Limits:* a vendor study. Adding generic document summaries gave "very limited" gains in their tests. They advise putting a knowledge base under about 200K tokens straight into the prompt instead of using RAG.
- *For the project:* Corpus D is about 13K tokens. By Anthropic's own rule it fits in a prompt, so it is a teaching corpus here, not a realistic I5 case. The 2-point absolute change (5.7 → 3.7) is far below what 50 questions can detect (about 18 points at 80% power, 06 §9.4).

**Anthropic cookbook guide @ `a162e01` (MIT, © 2023 Anthropic) [I5-S2].**
- *Study:* 9 codebases, 737 chunks, 248 queries, Voyage `voyage-2` embeddings. "Pass@k" is the **mean fraction of golden chunks found in the top k**, matched by exact chunk content.
- *Result:* Pass@10 87.15% → 92.34% with contextual embeddings → 95.26% with reranking (cell 32 table). Cached input share 61.83%, costing about $2.85 instead of about $9.20 in input tokens (cell 22).
- *Limits found while reading:*
  - The table's hybrid row (86.43 / 93.21 / 94.99) does not match cell 28's output (88.86 / 92.31 / 95.23).
  - The baseline cell's printed header says "Contextual Embeddings".
  - Cell 18 shows `cache_creation_input_tokens: 0` for a 3,412-token prompt on `claude-haiku-4-5`. Our reading (an inference): that prompt is below Haiku 4.5's 4,096-token minimum cacheable prefix [I5-S7], so caching silently did nothing.
  - It sends `temperature=0.0`. On Haiku 5.5, non-default sampling values return a 400 [I5-S7], so a port must drop that parameter.
- *For the project:* use its prompt shape (`<document>` block marked `cache_control`, then the `<chunk>` and the instruction). Teach the "silent no-cache" trap as a CHECK.

**dsRAG (D-Star AI, MIT, © 2024 D-Star) @ `5215e97` [I5-S3]**, the source of the upstream notebook's text.
- *Design (`dsrag/auto_context.py`):*
  - 1 LLM call for the title (first 4,000 cl100k tokens), and 1 for a one-sentence document summary (first 8,000 tokens).
  - Optional section summaries (default off), plus LLM "semantic sectioning" for section titles.
  - The header is `Document context: the following excerpt is from a document titled '…'. <summary>`, then `Section context: this excerpt is from the section titled '…'.`
  - The header shown to the LLM ("segment header") carries **document-level information only**.
  - It makes **no per-chunk LLM calls**.
- *Result:* KITE has 50 questions over 4 datasets, graded 0–10 by GPT-4o: top-k 4.72 → CCH 6.04, RSE 6.73, CCH + RSE 8.42. Semantic sectioning was not used in these runs.
- *Limits:* vendor benchmark, n = 50 (about 12 per dataset), an LLM judge, end-to-end answers (not a retrieval metric). AI Papers went only from 4.5 to 4.7.
- *For the project:* this is rung 1 of the cost ladder. Its "embed with section, show the generator only document-level context" split is a real design precedent for decision #7.

**Late chunking, Günther et al. 2024 (arXiv 2409.04701; GitHub README @ `1d3bb02`) [I5-S4].**
- *Study:* encode the whole document with a long-context embedder (`jina-embeddings-v2`, 8,192 tokens), then mean-pool the token vectors per chunk span. Tested on BEIR subsets with 256-token chunks.
- *Result:* nDCG@10 improved on 4 of 5 sets, by 0.6–6.5 points; e.g. NFCorpus 23.46 → 29.98; Quora unchanged at 87.19.
- *Limits:* it needs token-level outputs, which Cohere's API does not return, and it helps only the dense side. Its own table shows "no chunking" winning on 2 of 5 sets.
- *For the project:* Full-only. Not runnable with Cohere. MiniLM's 256-token window equals the chunk length, so there is no context to add.

**Merola & Singh 2025, "Reconstructing Context" (arXiv 2504.19754, ECIR 2025 workshop) [I5-S5]** (search-checked, page not opened, UNVERIFIED): contextual retrieval kept semantic coherence better at a higher compute cost, while late chunking was cheaper but less consistent across embedders and datasets. Cite only as "an independent comparison exists"; no numbers.

**Caching facts** (the cost lever for the per-chunk, whole-document arm):
- **Claude [I5-S7]:** a prefix match. The minimum cacheable prefix is 512 tokens on Haiku 5.5 (the skill says to check the docs before relying on it) and 4,096 on Haiku 4.5. Writes cost 1.25× (5-minute TTL) or 2× (1 hour); reads cost about 0.1×. A read refreshes the TTL.
- **Groq [I5-S6]** (search-checked, UNVERIFIED): automatic on `gpt-oss-20b`, exact prefix only, 50% off cached input. That matches LLMOPS §6.2's $0.037. Entries expire after about 2 hours unused, and hits are not guaranteed. Cached tokens "do not count towards rate limits".
- **Consequence:** put the document first, then the chunk and the instruction. Process chunks document by document, never shuffled.

**Cost ladder for Corpus D** (DERIVED; assumes about 250 tokens of chunk + instruction per call and about 200 output tokens including reasoning; prices from LLMOPS §6.2):

| Rung | Calls (D / T≈750 chunks, ASSUMPTION) | Input tokens per call | D cost |
|---|---|---|---|
| 0 Deterministic path header | 0 / 0 | — | $0 (plus 2 Cohere embed calls per arm) |
| 1 One call per document (title/summary; dsRAG, upstream cell 11) | 1–2 / 6–12 | ≤ 4K–8K | < $0.01. Not needed on D: the real title is the 24 pt line |
| 2 One call per chunk, chapter window (about 3.5K chars ≈ 620 tokens) | 97 / ~750 | ≈ 870 | Groq ≈ 97 × (870 × 0.075 + 300 × 0.30)/10⁶ ≈ **$0.015**; about 113K tokens, so it fits the 200K TPD in one day (≥ 14 min at 8K TPM) |
| 3 One call per chunk, whole document (Anthropic) | 97 / ~750 | ≈ 13.3K (D) | Haiku 5.5 cached: write 13,033 × 0.125 + reads 96 × 13,033 × 0.01 + 97 × 250 × 0.10 + 97 × 200 × 0.50 (all /10⁶) ≈ **$0.026**; uncached ≈ $0.139. Groq: **blocked** on the free tier (13.3K > 8K TPM per request) |

General formula (per document d, with n_d chunks, document tokens D_d, chunk + instruction tokens c̄ + P, output o):
`cost_d = D_d·p_in·w + (n_d − 1)·D_d·p_in·ρ + n_d·(c̄+P)·p_in + n_d·o·p_out`. For Claude, w = 1.25 and ρ = 0.1. For Groq, w = 1 and ρ = 0.5.

**Framework defaults worth naming [I5-S8]** (LlamaIndex `v0.14.25`, read only):
- `TextNode` embeds **all metadata by default**, with template `"{key}: {value}"` and text template `"{metadata_str}\n\n{content}"` (`schema.py` L66–67). Keys are removed only through `excluded_embed_metadata_keys` / `excluded_llm_metadata_keys` (L294–301). So a "no-header" LlamaIndex baseline may already carry a file-name or page header. This is also the cleanest existing API for decision #7.
- `DocumentContextExtractor` is LlamaIndex's port of Anthropic's prompt (`extractors/document_context.py` L44–53). Its defaults (L104–113):
  - `max_context_length=1000` tokens with `oversized_document_strategy="warn"`. A larger document (Corpus D ≈ 13K tokens) only logs a warning and is still sent whole (L268–285).
  - `max_output_tokens=512`.
  - Its own retry loop: 5 attempts, 60 s base delay.
  - The 2024 caching beta header.

**Current practice (2024–2026).** Three families:
- deterministic title/path headers (cheap; the default in dsRAG-style systems);
- LLM per-chunk contexts with caching (Anthropic; LlamaIndex extractor);
- contextual embeddings inside the embedder (late chunking; hosted "contextual chunk embedding" APIs, which are outside our decisions).

SDG's "CCH gives 10–20%" figure has no source. Do not use it.

**Pitfalls (with evidence).**
- A constant prefix on a single-document corpus (measured above).
- Leaf-heading collisions (11 on D).
- Truncation of the chunk tail when header + chunk passes 256 on MiniLM. 182 + 27 ≈ 209 tokens is fine at 1,000 characters; 182 + 100 ≈ 282 truncates (DERIVED). The cookbook gives the same warning [I5-S2].
- Silent no-cache below the minimum prefix [I5-S2, S7].
- A stale cache key (review 402).
- Header-query leakage (the upstream "Nike" query).
- n = 1 reranker evidence presented as an embedding effect (DV-19).

**How to evaluate.**
- Primary: CE@4 on dev, at fixed k. Equal budget is not needed, because the header does not enter the context unless decision #7 says so; say this explicitly.
- Per-category results for vocabulary-mismatch and `near-duplicate-distractor` (≥ 6 items), with n.
- Discordant pairs and the paired bootstrap (06 §9.3).
- A label-free diagnostic: the cosine margin between the gold chunk and its near-duplicate distractor.
- Generation is untouched at v1.2.

**Interview questions:**
- AIQ 04 Q17.
- "Why does contextual BM25 add to contextual embeddings?"
- "How does prompt caching change the cost math at 10M chunks?"
- "What is the re-indexing story when a document is edited?" (AIQ 04 Q17 follow-ups.)
- "When is a title header useless?"

### 6. Lesson blueprint

**The answer first (draft).** A chunk cut out of a document often loses what it is about: its heading, its chapter, the name that "it" refers to. So a question that names the subject cannot match it. A contextual header fixes this at index time: you prepend a short description of where the chunk sits (a heading path, or an LLM-written sentence) to the text you **embed**, while the stored chunk text and its offsets stay unchanged. A header helps only when it carries information that **differs between chunks**. In Corpus D, the one document title is the same everywhere, so only chapter and section headings can separate near-duplicates like the two "Paris Agreement" pages. The LLM version costs one call per chunk, each carrying the whole document, which is affordable only with prompt caching. Vendors report it cuts missed chunks from 5.7% to 3.7% at top-20, a change our ~50 questions cannot detect. So v1.2 measures the free, deterministic header first, with CE@4, and pays for the LLM arm only if the free arm helps.

**The theory in one read (11 ideas).**
1. *Contextual anonymity:* a chunk's meaning depends on text outside its span (pronouns, an orphaned heading, the chapter).
2. *Header:* `embed_text = template(header) + sep + text`. `text`, `char_start` and `char_end` are unchanged, so CE scoring is unaffected.
3. *Information test:* a header discriminates only if it varies. In a one-document corpus, the title header has one value, so it contributes no ranking information; it only shifts every vector. Distinct headers / chunks is a quick measure.
4. *Header source:* deterministic (font-size heading tree, path at the chunk start, or all headings inside the chunk) or generated (an LLM call).
5. *Path vs leaf:* a leaf collides across chapters (Paris Agreement, p.10 and p.23). The path separates them at chapter level.
6. *Dilution (mean pooling):* the header's token share is `s = h/(h+c)`. With h ≈ 19 and c ≈ 150, s ≈ 0.11. On a 400-character chunk (c ≈ 65), s ≈ 0.23. Chunks in one section are pulled toward each other (the "header magnet").
7. *Truncation:* if `h + c > L` (MiniLM L = 256), the **end** of the chunk is dropped, not the header. Cohere `embed-v4.0` (128K) avoids this.
8. *Three decisions:* embedding input (v1.2), BM25 input (v2.0), generation input (a later arm). Store `embed_text`, `bm25_text` and `display_text` separately.
9. *LLM context:* whole document + chunk → a context of about 50–100 tokens. The cost formula is in §5; with caching, reads cost 0.1× (Claude) or 0.5× (Groq).
10. *Cache keys and rebuilds:* the LLM key holds the model, the parameters, the rendered prompt (prompt version) and the full document text. The embedding side bumps `preproc_version`, which changes `embed_hash`.
11. *Evidence:* a vendor's 1 − recall@20 is not CE@4. Relative vs absolute change; the detectable effect at n ≈ 50; Ch7's 0.1 → 0.9 is a reranker score on one chunk.

**Formula sheet:** `embed_text` template · `s = h/(h+c)` · truncation `h + c ≤ L` · distinct-header ratio · LLM-arm cost formula with w and ρ · relative change `(b − a)/a` vs absolute change `b − a` · CE@4, paired Δ with CI.

**Step-by-step outline** (running example: Corpus D, seeds D-002 Paris 2015 (gold p.10; distractors p.6, p.23, p.24) and D-003 NDCs (gold p.23)):
1. Show the p.10 and p.23 chunks bare, and ask which one is about "the 2015 agreement".
2. Extract the heading tree from font sizes and print the two paths.
3. Build three `embed_text` variants: none, title only, path. Count the distinct headers: 1 vs 97.
4. Compute the token share and truncation for the 97 chunks (MiniLM).
5. Embed (MiniLM offline; cached Cohere optional). Compute the cosine margin gold − distractor for D-002 and D-003 under each arm.
6. Run CE@4 / Hit@4 / MRR on the dev seeds for the three arms, and read the discordant items.
7. Cost ladder: compute rungs 2–3 for D with the formula. Show why Groq rejects rung 3 on the free tier.
8. LLM context, using one recorded response from the cache (replay): hand-check it against the page; run the entity-in-document check.
9. Compare with the upstream demo and with Anthropic's numbers (metric, k, corpus).

**Visuals that earn their place.**
- *Heading-tree strip* (SVG): 33 pages × heading levels, with the 11 reused names highlighted. Shows where headers can discriminate.
- *Embed-text anatomy* (SVG): `[header | chunk text]` against a 256-token ruler, with the truncated tail shaded. Shows dilution and truncation together.
- *Distractor-margin dumbbell* (Plotly): per near-duplicate pair, the margin for none / title / path. Shows help vs hurt.
- *Cost ladder* (table plus bar): calls and USD per rung for D and T. Shows why caching decides rung 3.
- *Three-decision diagram:* one chunk record flowing into the embedding, BM25 and prompt inputs. Shows which fields v1.2 changes.

**Full only:** heading-assignment rules compared; constant-title control in depth; contextual BM25 preview (idf of constant terms); late chunking; LlamaIndex metadata modes; dsRAG section summaries; the cookbook's silent no-cache; hosted contextual embedders.

### 7. Verify notebook plan

`study/notebooks/I5_headers_verify.ipynb`. Offline by default, about 2–3 minutes on CPU.
1. Load the Corpus D snapshot and C3's `chunks.jsonl` (97 records, `params_hash 1ca9c5a3b548`). Assert the span invariant.
2. Build the heading tree from PyMuPDF `get_text("dict")` (sizes 36/27/20/18-bold; bold via span flags). Assert the counts against §5 (1/21/68/192) or record the PyMuPDF differences.
3. Map chunks to paths under three rules (start, majority, all inside). Print the disagreements (e.g. chunk 34 on p.10). Count chunks with no heading inside, and orphaned-heading repairs (07 D.8: 16).
4. Header statistics: distinct headers, token share (MiniLM WordPiece and tiktoken `o200k_harmony`, both named), truncation counts at 1000/200, 1500/300 and 2000/400.
5. Reused-name table (11) and the near-duplicate pairs (Paris p.6/10/23/24; smart grids p.8/12/22/23; DAC p.8/23/30, from 06 §5.1).
6. MiniLM embeddings for each arm (`embed_hash` changes with `preproc_version`). Cosine margins; dumbbell chart (Plotly).
7. Retrieval on the dev seeds: CE@4, Hit@4, MRR, per category, plus the paired bootstrap (06 §9.3). Optional replay-only cell with cached Cohere `embed-v4.0`.
8. Constant-title control: Kendall τ between the rankings of "none" and "title only". Show that the rankings move but no information was added.
9. Toy check of the dilution formula: a bag of unit vectors, mean-pooled.
10. Cost-ladder cell: pure arithmetic from token counts and `prices.json`.

API calls: none by default. One optional replayed LLM context (rung 2 or 3) from the LLMOps recording.

### 8. Apply-it tool plan and real-world checklist

`study/tools/header_fit_check.py`: "Would contextual headers help my documents, and which kind?"
- **Inputs:** `--docs` (PDFs); `--evalset` (optional, M1 format or a light `expect` form); `--embedder minilm|cohere-cached`; `--chunk-size --overlap --scope`; `--contexts contexts.jsonl` (optional, for LLM-arm output).
- **Output:** the heading tree summary, the per-chunk header table, the checklist with pass/warn/fail, a recommendation and a JSONL log. Same pattern as `bm25_fit_check.py`.

| # | Check | Auto / manual |
|---|---|---|
| H1 | A heading hierarchy is detectable (≥ 2 font levels; headings on ≥ 50% of pages) | auto |
| H2 | A title exists (metadata, largest font, or file name), and how many distinct titles the corpus has (1 → "title header useless") | auto |
| H3 | Distinct headers / chunks, and the largest share of chunks sharing one header (header magnet) | auto |
| H4 | Leaf headings reused under different parents (list) | auto |
| H5 | Median and max header token share (warn if over 0.25) | auto |
| H6 | Header + chunk exceeds the embedder's limit (count; MiniLM 256) | auto |
| H7 | Anonymous chunks: no heading inside, and the first sentence starts with a pronoun or "this/the …" (heuristic rate) | auto |
| H8 | Header-query leakage: eval questions whose content words appear in a heading but not in the gold span | auto + manual |
| H9 | Near-duplicate margins, with and without headers (needs an embedder) | auto |
| H10 | Read 10 random chunks with their headers: is the section right? | manual (tick the list) |
| H11 | LLM contexts (if given): rate of entities and numbers not found in the document; empty or over-long contexts | auto |
| H12 | Hand-check 10 LLM contexts for wrong claims or a wrong section | manual |

**Recommendation logic:**
- H1 fails → "no deterministic header; consider an LLM context (rung 2) or I2 parsing first".
- H2 is 1 and H3 is high → "title header carries no information; use the path".
- H4 is large → "full path, not leaf".
- H5 or H6 warns → "shorter header template or a larger-window embedder".
- H7 is low → "chunks are already self-contained; expect little gain".
- H8 is high → "eval set biased toward headers; re-check with span-written questions".
- H11 is over 2% → "do not index the LLM contexts".

### 9. LLMOps notebook plan

`study/llmops/notebooks/I5_headers_ops.ipynb`.
- **Framework build:**
  - LangChain `Document`s with metadata `heading_path`, `doc_id`, `char_start`, `char_end`, `text_sha256` and `doc_text_sha256`.
  - A `RunnableLambda` header builder (rung 0) produces `embed_text`.
  - `CachedEmbeddings` (`search_document`) embeds it; queries stay `search_query` and hit the cache.
  - The rung 2/3 contextualizer is `CachedChatModel.batch()` over chunks, ordered by document. Prompt files: `prompts/i5_context_window_v1.txt` and `prompts/i5_context_wholedoc_v1.txt`.
  - A read-only cell shows LlamaIndex's `DocumentContextExtractor` and its defaults (`max_context_length=1000` + "warn", 5 retries, metadata embedded by default) [I5-S8].
  - No LangGraph: the flow is linear.
- **External calls (all cached; the notebook runs fully in replay):**

  | Call | Corpus D | Corpus T (ASSUMPTION ~6 docs, ~750 chunks) |
  |---|---|---|
  | Cohere embed per header arm | 2 calls (97 texts) | 8 |
  | Cohere query embeds | 0 new (reused) | 0 new after T's first run |
  | Groq gpt-oss-20b, rung 2 (chapter window), `reasoning_effort=low`, `max_completion_tokens` ≥ 512 | 97 calls, ≈ 113K tokens, ≈ $0.015 | ~750, ≈ 0.9M tokens: several days at 200K TPD, so use Haiku or a paid tier |
  | Haiku 5.5, rung 3 (whole document, `cache_control` on the document block, effort `low`, no `temperature`) | 97 calls, ≈ $0.026 | ~750, ≈ $0.2 (ASSUMPTION) |
  | Rung 1 title/summary (for T only) | 0 | 6–12 |

- **Tracing:**
  - Per chunk: `header_text`, header tokens, `embed_text` sha, truncated flag. Per LLM call: everything in LLMOPS §3.3, plus `cached_tokens` / `cache_read_input_tokens` and `cache_creation_input_tokens`.
  - LangSmith only for Corpus D, through `privacy.assert_corpus_is("D")`. T stays local (Phoenix or JSONL), because T contexts contain paper text.
- **Dataset and evaluators:**
  - The D and T dev golden sets.
  - Code evaluators: CE@4, Hit@4, MRR per category; distractor margin; header token share; truncation count.
  - For contexts: entity-in-document rate (capitalised tokens and numbers string-matched against the document), length, empty, `finish_reason=length`.
  - A human hand-check of 10 contexts, stored as labels. No judge (D-10).
- **Experiment against the previous version:** v1.1 champion vs v1.2-path (D smoke test, T decision), plus a title-only control. The LLM arm runs only if the path arm is "supported" (06 v1.2). One variable: the header template (`preproc_version`).
- **Cost, latency and tokens:** index-time calls × chunks, tokens, cache-hit share, USD per 1,000 chunks, build wall time. Query latency is unchanged (state it, and measure p50/p95 to confirm).
- **Versioning:** the header template id is part of `preproc_version` (and hence `embed_hash`). Prompt files are immutable. `contexts.jsonl` rows carry `model_requested`, `prompt_version`, `doc_text_sha256`, `text_sha256` and `cache_key`.
- **CI and monitoring:**
  - T1 tests: header builder snapshot on D; span invariant; `preproc_version` changes `embed_hash`; header + chunk ≤ limit or flagged; replay test with 0 misses; entity rate ≤ threshold.
  - Monitor (`monitor.yaml`): header-length p95; share of chunks with an empty path (heading detection broke on a new PDF); entity rate; context length; cache-hit share; cost per build.
  - When `doc_text_sha256` changes, a rebuild of that document's contexts is triggered.
- **Lifecycle:** Improve (an index-time change) → Measure (CE@4) → CI (header and replay tests) → monitoring (header and context drift). Failures go to the M5 error log, and confirmed ones become new golden items (near-duplicate or leakage cases).
- **Skills:** `rag-evaluation`, `code-based-evaluators`, `improving-llm-agents` (caching cost), `llm-observability`, `ci-cd-evals`, `error-analysis`.

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Heading extraction (font sizes) | `pymupdf` `get_text("dict")` | 1.26.7 (pinned) | yes | yes | — | AGPL-3.0 | yes |
| Token counts | `tiktoken` (`o200k_harmony`) + MiniLM WordPiece via `transformers` | 0.14.0 / 5.19.0 | yes | yes | — | MIT / Apache-2.0 | yes |
| Offline embedder | `all-MiniLM-L6-v2` (256 tokens) | `sentence-transformers` 6.1.0 | yes | yes | $0 | Apache-2.0 | yes |
| Default embedder | Cohere `embed-v4.0` via `CachedEmbeddings` | cohere 7.2.0 | yes | replay yes | ~2 calls per arm (D) | MIT (SDK) | yes |
| LLM, rung 2 | Groq `openai/gpt-oss-20b`, `reasoning_effort=low` | groq 1.7.0 | yes | replay yes | 97 calls, ≈ $0.015 (D) | Apache-2.0 (SDK) | yes; rung 3 is **not** feasible on the free tier |
| LLM, rung 3 (optional) | Claude Haiku 5.5 `claude-haiku-5-5`, effort `low`, prompt caching (512-token minimum) | `anthropic` 1.11.0 | no | replay yes | 97 calls, ≈ $0.026 (D) | MIT | yes (D-32, when credits exist) |
| Charts | `plotly` | installed | yes | yes | — | MIT | yes |
| Framework core | `langchain-core` | 1.6.6 | no | yes | — | MIT | yes (LLMOps notebook only) |
| Splitter comparison | `langchain-text-splitters` | 1.1.3 | no | yes | — | MIT | yes |
| Graphs | `langgraph` | 1.2.12 | no | yes | — | MIT | not needed (linear flow) |
| Provider packages | `langchain-groq`, `langchain-cohere` | — | no | — | — | MIT | **conflict** (LLMOPS §9.3); use the adapters |
| Claude via LangChain | `langchain-anthropic` | 1.7.5 | no | — | — | MIT | optional; adapter preferred |
| Hosted tracing | `langsmith` | 0.14.4 | no | SDK yes | free plan | MIT | Corpus D only |
| Local tracing | `arize-phoenix-otel` + server via `uvx arize-phoenix@20.19.0` | 0.17.2 | no | yes | — | Apache-2.0 / ELv2 | yes |
| Read-only comparison | LlamaIndex `llama-index-core` (`DocumentContextExtractor`, `MetadataMode`) | 0.14.25 (2026-09-21) | no | — | — | MIT (repo) | read only (D-08); not installed |
| Next only | late chunking (`jina-embeddings-v2-small-en`, 8K window, `trust_remote_code`) | — | no | yes after download | $0 | Apache-2.0 (UNVERIFIED) | needs a decision; Full-only demo |
| Not used | Voyage contextual embeddings; Elasticsearch BM25 (cookbook) | — | — | — | — | — | no (outside D-03; Docker) |

**Install lines** (do not run):

```text
uv add --group llmops langchain-core==1.6.6 langchain-text-splitters==1.1.3 langsmith==0.14.4 arize-phoenix-otel==0.17.2
uv add --group llmops anthropic==1.11.0      # only for the rung-3 arm, when credits exist
```

**Keys:** `COHERE_API_KEY` and `GROQ_API_KEY` (both present); `ANTHROPIC_API_KEY` (rung 3, optional); `LANGSMITH_API_KEY` (Corpus D traces only).

### 11. Open questions for Yash (preferences only)

- If the deterministic header helps and the LLM arm runs: use **Haiku 5.5 with the whole document** (about 3 cents per D build, needs credits) or **Groq with a chapter window** (free, less context)? **haiku / groq**
- Include the optional Full-only late-chunking demo with a local `jina-embeddings-v2-small-en` (one model download; runs remote model code)? **yes / no**

---

## Concept I6: Document augmentation and HyPE (index-time question generation)

Priority S. Experiment branch only: 06 has **no version card** for I6, so the experiment design is written here (§9, "The experiment").

### 1. Sources checked

- **Book (not present in this session; every page is from 04 §3 / §5 / §6 and 03, not re-opened, UNVERIFIED):**
  - Ch11 p.6/13: the steps. Chunk, generate N questions per chunk, clean them and drop "too vague" ones (04 §5).
  - Ch11 p.6/13–p.8/13: store each question with a pointer to its parent chunk; match the query; fetch the parent; generate. The sketch is on p.8/13.
  - Ch11 p.9/13–p.10/13: the mirror image of HyDE.
  - Ch11 p.11/13: how many questions to make (a 5–40 range, per 04 §5 and DV-25).
  - Ch11 p.1/13: the asymmetry problem (per `concepts/P4_embeddings_similarity.md` line 362).
  - Intro p.5/8 puts Ch11 under post-retrieval processing. Ch11 itself works at index time (DV-B2).
  - The Appendix quick-reference table rates Ch11 High/Low (per 03 §4.1). The scale is not stated.
  - 02 and 04 agree on the Ch11 pages; I found no page conflict.
- **Repo (verified: downloaded at `009adba2…` into the session scratchpad; 0-based cells; read with `python3 -I` + `json`; cells parsed with `ast`; nothing executed):**
  - `all_rag_techniques/document_augmentation.ipynb`, 19 cells, **no saved output in any cell**.
    - Cell 4: the constants `DOCUMENT_MAX_TOKENS=4000`, `DOCUMENT_OVERLAP_TOKENS=100`, `FRAGMENT_MAX_TOKENS=128`, `FRAGMENT_OVERLAP_TOKENS=16`, `QUESTION_GENERATION=DOCUMENT_LEVEL`, `QUESTIONS_PER_DOCUMENT=40`; legacy imports.
    - Cell 6: `clean_and_filter_questions` (strip the `^\d+\.` numbering, keep lines ending in "?"); `generate_questions` (`gpt-4o-mini`, temperature 0, a prompt asking for "at least {num_questions}" questions, `with_structured_output(QuestionList)`, `list(set(...))`); `split_document`, which uses `re.findall(r'\b\w+\b')` "tokens" joined by spaces.
    - Cell 10: `process_documents`. Each fragment and each question is a FAISS document with `metadata["text"] = text_document`, which is the 4000-word window. The retriever uses `k=1`.
    - Cells 13–17: one query; the parent is taken from the loop variable `doc`, left over from cell 15.
  - `all_rag_techniques_runnable_scripts/document_augmentation.py`:
    - L52–L58 cleaning; L61–L72 generation; L86–L94 splitter; L101–L150 the processor; L160–L187 the demo.
    - **Its prompt (L65–L66) drops the notebook's "directly answerable … no answers or headers" clause.**
  - `all_rag_techniques/HyPE_Hypothetical_Prompt_Embeddings.ipynb`, 23 cells:
    - Cell 0: the claims of +42 pp precision and +45 pp claim recall, with a link to the SSRN preprint 5139335.
    - Cell 7: `gpt-4o-mini`, `text-embedding-3-small`, 1000/200.
    - Cell 9: a free-text prompt for "essential questions", split with `.replace("\n\n","\n").split("\n")`. The number of questions is not set.
    - Cell 11: **SyntaxError confirmed** by `ast.parse`, at cell line 32 (`index=faiss.IndexFlatL2(...)` is missing its comma). The vectors go in with `add_embeddings((chunk.page_content, vec))` and **no metadata**.
    - Cell 13: `PyPDFLoader` → `RecursiveCharacterTextSplitter(1000, 200, len)`.
    - Cell 15: output "97/97".
    - Cell 17: `k=3`.
    - Cell 19: `list(set(context))`. The saved output shows **2 contexts for k = 3**.
    - Cell 21: `evaluate_rag`. Its output is malformed generated quiz items (multiple-choice and matching).
  - `all_rag_techniques_runnable_scripts/HyPE_Hypothetical_Prompt_Embeddings.py` L21–L153: the comma is fixed at L99; generation at L60–L74; the store at L76–L108; dedup with `set` at L152.
  - `helper_functions.py`:
    - `read_pdf_to_string` uses PyMuPDF.
    - `replace_t_with_space` returns the **Document** objects.
    - `retrieve_context_per_question` returns `page_content` strings.
- **Model ids used upstream:** `gpt-4o-mini` (doc-aug cell 6 / script L62, L76; HyPE cell 7 / script L60). The embedder is `OpenAIEmbeddings()` with the library default model (doc-aug cell 13) or `text-embedding-3-small` (HyPE cell 7, script L61, L98). Both are OpenAI, which the course does not use; the repo is read only.
- **Course files:**
  - 02 I6 card (lines 623–635); 03 rows I6a/I6b (lines 520–521), §4.1–4.2 tables, line 491 ("Q2 advice ← I6");
  - 04 §2.4 row, Ch11 section, §4 repo-only row, §5 row, DV-25, DV-B2;
  - 06 §3.2, §4.1, §4.2 v1.x and v3.1 cards, §6.1–6.3, §7.2–7.5, §9.2–9.4, §11 risk row "Index-time LLM cost creep";
  - 08 D-03, D-07, D-09, D-10, D-32;
  - `LLMOPS_FOUNDATION.md` §2–§12; `phase_03_measurement.md` (M1 leakage, format);
  - `concepts/P4_embeddings_similarity.md` D.8 (asymmetry, `input_type`);
  - `C3_FACTS.md`, `C2LAB_FACTS.md`, `P1_FACTS.md` (Corpus D numbers);
  - `07_SAMPLE_LESSON.md` Part I (experiment pattern); tracker and misconception log.
  - The external review has no I6 item. Its leakage rows (§4 M1, row 10) apply here.
- **AE book:** only through the review. Its leakage rule (AE Ch9 'Common Mistakes with CI'; Ch12 'Prompt Refinement'), per the review, not re-opened.
- **Interview repo (AIQ `04-rag-and-retrieval/questions.md` @ e080df2, MIT, "Copyright (c) 2026 Om"):**
  - Q5 (retrieve small, generate big; resolve `parent_id`);
  - Q26 (HyDE; "when does HyDE hurt?");
  - Q33 (near-duplicates crowding top-k);
  - Q45 (synthetic questions "echo the chunk's vocabulary, inflating retrieval scores").
  - SDG `06-retrieval-systems/09-advanced-retrieval-patterns.md` @ ed955b2: HyDE only; no HyPE or doc2query item.
- **External** (7 sources; see the sources block):
  - [I6-S1] doc2query; [I6-S2] docTTTTTquery; [I6-S3] Doc2Query--; [I6-S4] HyPE paper; [I6-S5] HyDE (C#32);
  - [I6-S6] LangChain `MultiVectorRetriever` source; [I6-S7] LlamaIndex `QuestionsAnsweredExtractor` source.

### 2. Gap audit

"Yash studied it?" comes from `concept_tracker.csv`: *no* = `not_started`; *exposed* = O1 diagnostic only. No Phase 4 lesson, reading or question file exists, so nothing is "taught" yet. "Taught before use" names the planned owner lesson and whether that lesson covers the idea.

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class (core / bridge / next) | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Query–document **shape asymmetry**: a short question and a declarative passage embed apart | The whole motivation; Ch11 p.1/13, p.9–10/13 | P4 D.8 (written) | P4 | no (MC-002 open) | bridge | Open with D-006 (the question avoids "floating" and "water bodies"). One picture: the question vector sits near other questions, not near the passage |
| 2 | Embedding, cosine, top-k, the same model for both sides | Every retrieval step | P4, C4 (written) | P4/C4 | no; MC-002 open ("similarity matrix") | bridge | Three lines: one query vector, one score per stored vector, sort. Say plainly that I6 adds rows to the index; it computes no matrix |
| 3 | **Index time vs query time** | The I6 vs Q2 trade-off; who pays the LLM call | 03 §4.2 table only | P2/C6 → I6 | no; **MC-003 open** (conflates stages) | bridge (critical) | A two-lane timeline: index lane (chunk → questions → vectors) vs query lane (embed → search → parent → answer). Ask MC-003's check question |
| 4 | The chunk as the **parent unit**: `chunk_id`, doc offsets, `text_sha256` | Pointer target; CE scoring | C2/C3 (written) | C3 | no | bridge | Reuse the C3 record; the parent is the v0/v1 champion chunk, never a new text |
| 5 | Per-chunk question generation: prompt, n, structured list output | The core build | missing | I6 | no | core | Show the prompt file, a JSON-schema list, and three generated questions (from the replay pack) |
| 6 | Structured LLM output and validation (schema, parse failure, retry) | Generation step | M3 / D-22 (not written) | M3 | exposed | bridge | One box: Groq `json_schema` strict; on a parse failure, retry once and log it; never `split("\n")` (HyPE cell 9) |
| 7 | Cleaning: strip numbering, dedup, the **"too vague"** filter (deictic "this text", "the author") | Ch11 p.6/13; cell 6 keeps only the "?" rule | missing (04 §5: the filter is not in the repo) | I6 | no | core | Deterministic filter rules plus a count of what each rule removed |
| 8 | **Hallucinated or unanswerable questions**; filtering by relevance (Doc2Query--) | Index quality | missing | I6 | no | core | [I6-S3]: the generator invents content; filtering raised effectiveness and shrank the index. Course version: a local cross-encoder score with the bottom share dropped (an arm, not the default) |
| 9 | **Multi-vector index**: many vectors → one parent id | The core data structure | missing | I6 | no | core | Table `vectors[i] → (kind, parent_id, q_text)`; compare with LangChain's `id_key` [I6-S6] |
| 10 | **Three designs**: chunks + questions (doc-aug), questions only (HyPE), questions appended to the chunk text (doc2query, LlamaIndex) | Choosing a design | 03 I6a/I6b (2 of 3) | I6 | no | core | One diagram with three columns; the single-vector concatenation is the third design that the course files miss |
| 11 | **Score aggregation per parent** (max / sum / mean / RRF) and **oversampling** K_vec ≥ k·(n+1) | Ranking parents | missing | I6 (RRF: R1) | no (R1 exposed) | core (RRF bridge) | Toy with 8 vectors and 3 parents: max vs sum flip the order. RRF in one line, linked to R1 |
| 12 | **Duplicate parents in top-k** → fewer unique parents; dedup before cutting to k | HyPE cell 19 (2 unique for k = 3); DV-25 note | missing | I6 (X3 later) | no | core | Show that `set()` loses order (04 X3 row); dedup in rank order, then cut |
| 13 | **How many questions**: diminishing returns; one call can serve n = 1…n_max by prefix | Ch11 p.11/13; doc2query 5, docTTTTTquery 40 of 80 [I6-S1, S2] | missing | I6 | no | core | Plot CE@4 against n from a single n_max = 10 generation pass |
| 14 | **Index-size and cost multiplier**: vectors ×(1+n) or ×n; calls = chunks; rate-limit time | 02 outcome "compute the multiplier" | 03 §4.1 (qualitative) | I6 (D2 later) | no | core | A formula sheet plus the Corpus D table (§9) |
| 15 | **Which `input_type` to use for stored questions** (`search_document` vs `search_query`) | Embedding questions with Cohere | P4 D.8 (written; not for this case) | I6 | no | core | An open design variable: questions are stored items but question-shaped. Pre-register `search_document`; probe `search_query` as a dev-only arm |
| 16 | **CE@k on the parent's character span** (union of unique parents) | Scoring | M2 (not written) | M2 | exposed | bridge | The retrieved unit is unchanged (the champion chunk), so CE uses its `[char_start, char_end)`; the question text is never scored |
| 17 | **Equal token budget** | Comparison fairness | I1 (07 Part I) | I1 | no | bridge | Same unit means fixed k ≈ equal budget after dedup. The upstream 4000-word parent breaks this badly (see 26) |
| 18 | **Leakage: generated index questions vs eval questions** (same model family, same pages) | Validity of any I6 gain | **missing everywhere** (06 §6.3 covers leakage into prompts and chunk-based eval questions only) | I6 / M1 | no | core (critical) | Teach it as the main threat to validity; overlap metrics, the decisive slice and a de-leaked arm (§9) |
| 19 | Paired bootstrap by group; dev selection, one test touch; power (~0.18 detectable) | The decision | M4 (not written) | M4 | no | bridge | Two lines and a link; state honestly that the vocabulary-mismatch slice (n ≈ 6 + variants) is diagnostic only |
| 20 | **HyDE as the mirror image**; break-even `Q_total > N_units × rebuilds` | Ch11 p.9–10/13; 03 §4.2 | 03 §4.2 | Q2 | no | core (HyDE itself: next) | Two-lane cost chart; the HyDE mechanism stays in Q2 |
| 21 | Upstream: the "parent" is a 4000-regex-word window with punctuation removed; regex "tokens" | DV-25; cells 4, 6, 10 | 04 (partly) | I6 | no; MC-001 open (units) | core | Compute on Corpus D: about 3 parents, each about 43% of the PDF (§4 E1). Ties to MC-001: "tokens" here are regex words |
| 22 | Keyword and number queries: questions paraphrase away rare terms (HyPE drops the chunk vector) | 03 §4.1 "expected to lose" | 03 only | I6 (R1 later) | no | core | A guard metric on exact-term items; a "rare-token retention" check (§8) |
| 23 | Rebuild and refresh: questions are keyed by chunk text hash; a changed chunk means regenerated questions | Production, D3 | C3 cache (written) | C3 / D3 | no | bridge / next | The cache key holds the chunk text + prompt version + model; show 1 changed chunk → 1 new call (C3's S4 pattern) |
| 24 | Generated questions are model output: non-deterministic, so they must be cached and replayed | LLMOps | foundation §2.7 | LLMOps | no | bridge | Record once; the verify notebook and tool read the replay pack |
| 25 | Lexical side: put questions into BM25 text (the original doc2query) | Hybrid follow-up | R1 (lesson exists, not studied) | R1 | exposed | next | One paragraph: doc2query was a BM25 expansion [I6-S1]; link to R1 |
| 26 | **Context cost of big parents** (k = 1 × about 5.3K tokens vs v0's ≈ 720) | Upstream design | missing | I6 / X3 | no | core | One bar chart; a "retrieval" that returns 43% of the corpus measures nothing |

### 3. Quiz coverage

There is no `study/questions/I6_questions.md`. Questions needed (titles only; FORMAT rules):
- **R (recall):**
  - What is stored in a multi-vector index, and what is returned?
  - Name the three designs (chunks + questions, questions only, questions appended) and the one thing each gives up.
  - Why must you dedup parents *before* cutting to k?
  - Index time or query time: when does HyPE pay its LLM calls, and when does HyDE?
- **A (application):**
  - Compute the vector count, LLM calls and storage for 97 chunks at n = 5 in both designs (1,536-d float32).
  - Given 8 scored vectors over 3 parents, rank the parents by max and by sum, and say which one a 10-question parent wins unfairly.
  - Compute the break-even query count between HyPE and HyDE for a corpus rebuilt twice a month.
  - Compute CE@4 when the top-6 vectors map to only 3 unique parents.
- **T (transfer):**
  - Your eval questions were drafted by the same model that wrote the index questions, and HyPE scores 1.00 Hit@4. What do you check, and what do you report?
  - A product-catalogue corpus with SKU-number queries: which design, if any, and why?
  - (Optional) The corpus changes daily and gets 50 queries a day: HyPE or HyDE?
- **Interview (`set=interview`):** AIQ 04 Q45 ("How do you build a golden evaluation set for RAG without months of labelling?"), framed around its "synthetic questions echo the chunk's vocabulary" point. Second choice: AIQ 04 Q5 (retrieval unit vs generation unit, `parent_id`).

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| I6-E1 | 04 DV-25, Ch11 table; 03 I6a | "The parent is a 4000-word document" is true but understates it. (a) The words are `\b\w+\b` matches joined by single spaces, so the parent and fragment texts **lose all punctuation** and have **no character offsets**: CE@k cannot be computed without re-mapping. (b) Corpus D has 9,255 whitespace words (P1 facts), so the 4000/100 split gives **about 3 parents, each about 43% of the PDF**, and about 85–95 fragments (DERIVED; the regex word count is not measured, because pymupdf is not installed in this session). With `k=1` the context is about 5.3K tokens versus about 720 for v0 at k = 4 (DERIVED) | Add (a) and (b) to DV-25; the verify notebook measures the exact counts |
| I6-E2 | 04 Ch11 table, step 2–3 ("40 per document") | The prompt asks for "**at least** 40". Cleaning keeps only lines ending in "?" and then applies `set()`, so the count varies, and there is no saved output to show it. The script's prompt (L65–L66) differs from the notebook's (cell 6): it drops "directly answerable … no answers or headers" | "Asks for at least 40; actual count unknown (no outputs); script and notebook prompts differ" |
| I6-E3 | 04 §4 and Ch11 notes on HyPE | Not recorded: (a) `add_embeddings` is called **without metadata**, so page and source are lost, page citations are impossible, and parents are identified only by text equality (cell 11 / script L105); (b) the generation function receives the LangChain `Document` object, not a string (helper `replace_t_with_space` returns Documents), so the prompt very likely gets `str(Document)`, metadata included (static reading, UNVERIFIED); (c) `split("\n")` can embed empty strings; (d) `ThreadPoolExecutor` + `as_completed` makes the insertion order run-dependent | Add to the 04 §4 row |
| I6-E4 | 04 "cell 11 SyntaxError (static reading)" | **Confirmed** with `ast.parse` (cell line 32). The saved outputs are **stale**: cell 15 (exec 71) shows a successful 97/97 build after the broken cell 11 (exec 66), and the execution counts run out of order (cell 21 = 76 before cell 17 = 79) | Add "outputs predate the edit" |
| I6-E5 | 02 I6 card, 04 §4 ("the precision gains quoted in cell 0 are a preprint claim") | A peer-reviewed version appears to exist: IEEE Access 13 (2025), DOI 10.1109/ACCESS.2025.3589499 [I6-S4] (search-checked only, UNVERIFIED). The gains are still not reproduced, and their metrics look judge-based | "Published 2025 (UNVERIFIED); claims not reproduced" |
| I6-E6 | 02 I6 card Ext line | Cites only C#32 (HyDE). The primary literature for index-time question generation (doc2query, docTTTTTquery, Doc2Query--) is missing from Source C | Add [I6-S1–S3] to Source C |
| I6-E7 | 06 (no I6 card); 06 §6.3 leakage rules; v3.1 card ("also compare with I6/HyPE") | No artefact or experiment id exists for I6. More importantly, **no course file addresses leakage between index-time generated questions and the LLM-drafted eval set** (D-09). This is the main validity risk for I6 and Q2's comparison | Adopt the §9 experiment design and leakage guard |
| I6-E8 | HyPE cell 15 comment ("chunk size can be quite large … not losing precision") | An untested claim. A large chunk returns more context tokens, and a fixed n covers fewer of its facts | Treat it as a hypothesis (the n × chunk-size interaction), not advice |
| I6-E9 | 03 §4.1 I6a row ("1 per document window") | True for the run setting; `FRAGMENT_LEVEL` would be 1 call per 128-word fragment (cell 10 code path, never run) | Add "FRAGMENT_LEVEL code exists, never run" |

### 5. What the research says

- **doc2query: index-time question generation started as sparse expansion** [I6-S1].
  - *The study:* Nogueira, Yang, Lin and Cho (2019) trained a seq2seq Transformer on MS MARCO (passage → query). They predicted 5 queries per passage (README, "Predicting Queries"), **appended them to the passage text**, and indexed the result with BM25 (Anserini).
  - *The result:* doc2query + BM25 reached MRR@10 21.8 vs BM25 18.6 at about the same latency (61 ms vs 55 ms) (docTTTTTquery README table). With a BERT re-ranker on top, it placed first on the re-ranking leaderboard (36.8 eval).
  - *Limits:* it used a supervised generator trained on in-domain query logs, a sparse index, and the MS MARCO query style.
  - *For the project:* this is the third design (questions appended to the text). It shows the idea predates LLM RAG. With BM25 (R1) it would also help exact-term queries, which question-only vectors do not.
- **docTTTTTquery: more samples help, then flatten** [I6-S2].
  - *The study:* the same idea with T5-base and top-k sampling (k = 10), 80 sampled queries per passage.
  - *The result:* MRR@10 27.2 (eval), close to the best non-BERT model (27.7), at 64 ms per query. The authors concatenate **only the first 40 predictions**, because using all 80 gives "a tiny gain". Sampling one query for each of 8.8M passages took about 8 TPU hours (about $20).
  - *Limits:* a 2019 leaderboard on a sparse index, not a dense multi-vector design.
  - *For the project:* returns diminish with n. On 97 chunks the whole index costs cents (§9), so the reason to keep n small is **index noise and leakage surface**, not money.
- **Doc2Query--: filter out the hallucinated questions** [I6-S3].
  - *The study:* Gospodinov, MacAvaney and Macdonald (ECIR 2023) scored each generated query against its own passage with a relevance model (ELECTRA in the PyTerrier README example) and dropped the low scorers before indexing. The README's example threshold is the 70th percentile of scores, which keeps roughly the top 30% of generated queries (my reading of the comment).
  - *The result (search-checked, UNVERIFIED):* up to 16% better effectiveness, 30% faster queries and a 48% smaller index (ECIR version). A later arXiv version reports different figures.
  - *Limits:* MS MARCO-style data; supervised scorers.
  - *For the project:* generated questions can be wrong about their own chunk. A cheap local filter (the `ms-marco-MiniLM-L-6-v2` cross-encoder scoring (question, parent)) is a defensible arm. Count what it removes.
- **HyPE: questions only, dense, at index time** [I6-S4] (UNVERIFIED: search-checked, page not opened).
  - *The study:* Vake, Vičič and Tošić, "Bridging the Question-Answer Gap in Retrieval-Augmented Generation: Hypothetical Prompt Embeddings", IEEE Access 13 (2025), pp. 129952–129961. It is also listed as an SSRN preprint (5139335, the notebook's link) and on arXiv. Per the abstract, they precompute several hypothetical prompts per chunk, embed them in place of the chunk, and evaluate on six datasets against naive RAG and HyDE.
  - *The result (claimed):* up to +42 percentage points in context precision and +45 in claim recall. "Up to" means the best case, not the average.
  - *Limits:* I could not confirm the dataset names, the generator and embedder, k, or how "claim recall" was computed (it is probably LLM-judged). Nothing is reproduced.
  - *For the project:* a hypothesis source only. The course test is CE@4 on its own span gold.
- **HyDE: the query-side mirror** [I6-S5] (C#32).
  - *The study:* Gao et al. (2022) had GPT-3 write a fictional answer document per query, encoded it with unsupervised Contriever, and searched (README; TREC DL19 notebook).
  - *For the project:* it pays one LLM call per query on the critical path, but it adapts to the real question. I6 pays N_chunks calls per rebuild but must guess the questions. Q2 owns the run (06 v3.1).
- **Framework defaults** (verified source).
  - **LangChain `MultiVectorRetriever`** (`langchain-classic==1.0.8`, `retrievers/multi_vector.py`) [I6-S6]:
    - `id_key="doc_id"` (L55), `search_kwargs={}` (L57) and `search_type=similarity` (L60). The vector store's default k is 4 (`langchain-core==1.6.6` `vectorstores/base.py` L361–L362).
    - So by default it fetches **4 child vectors**, keeps the first-seen parent ids in rank order (L107–L111), and calls `docstore.mget`.
    - Children without `id_key` and missing parents are **silently dropped** (L110, L113).
    - Scores are discarded, so the parent rank is effectively "max (first hit)". A parent that matches 3 times gets no boost.
    - **You can get 1–4 parents for "k = 4".** To get k parents you must oversample through `search_kwargs={"k": K_vec}` and cut afterwards yourself.
  - **LlamaIndex `QuestionsAnsweredExtractor`** (`llama-index-core` v0.14.25, `extractors/metadata_extractors.py`) [I6-S7]:
    - It defaults to 5 questions (L282–L283). Its prompt asks for questions the context answers that are "unlikely to be found elsewhere" (L253–L265).
    - It stores them as node **metadata** (`questions_this_excerpt_can_answer`, L334), which LlamaIndex embeds together with the text. That is the doc2query-style single-vector design.
    - Its `embedding_only=True` field is not referenced anywhere else in that file (static reading; whether it takes effect is UNVERIFIED).
- **Current practice (2024–2026).**
  - Index-time questions survive as "hypothetical questions" multi-vector recipes (LangChain), as metadata extractors (LlamaIndex), and as HyPE.
  - Teams combine them with the raw chunk vector (doc-aug style) rather than replacing it. 03 §4.1 predicts that question-only indexes lose on keyword queries; this is an inference to test.
- **Pitfalls with evidence:**
  - hallucinated questions [I6-S3];
  - duplicate parents crowding top-k (HyPE cell 19: 2 of 3; AIQ Q33);
  - huge parents (I6-E1);
  - lost metadata (I6-E3);
  - synthetic questions echoing the source vocabulary and inflating scores (AIQ Q45; Rahmani et al., per phase_03 [S23], not re-opened);
  - stale or uncontrolled question counts (I6-E2).
- **How to evaluate it.**
  - Retrieval only: CE@4 on the parent spans, with Hit@4 and MRR@10 as diagnostics.
  - Baseline: the v1.x champion (same chunks, no questions) and v0.
  - Per category, the target is vocabulary-mismatch and paraphrase variants; the guard is exact-term.
  - Report the index-build calls and cost, the vector multiplier and the duplicate-parent rate.
  - **Leakage-stratified**: the decisive slice is items that pass the leakage check, plus human-written items (§9).
  - Answer quality is unchanged by design, because the parent is the same text, so no generation run is needed unless retrieval moves.
- **Interview questions (3–5):**
  - How does index-time question generation differ from HyDE, and when is each cheaper? (03 §4.2 break-even)
  - How do you stop one parent from filling your top-k? (AIQ Q33 / Q5)
  - Your eval set is synthetic: why can doc2query-style indexing look better than it is? (AIQ Q45)
  - Questions only vs chunks + questions: what breaks for SKU or number queries?
  - How many questions per chunk, and how would you choose? ([I6-S2])

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).** Users ask questions, but documents make statements, and a question's vector often lands closer to other questions than to the passage that answers it. Document augmentation fixes this at **index time**: an LLM writes a few questions each chunk can answer, you store a vector for each question, and each vector points back to its parent chunk, so a user's question is matched against questions. At query time nothing extra is called: you search the vectors, turn the hits into **unique** parent chunks, and give those chunks (never the generated questions) to the answer model. The costs are one LLM call per chunk at every rebuild and an index (n + 1) times bigger. The main risks are hallucinated questions, one parent filling the top-k, keyword queries that the questions paraphrase away, and a fake gain when the index questions resemble your eval questions. HyDE solves the same mismatch from the other side, at query time; which one is cheaper depends on how many queries arrive between rebuilds.

**The theory in one read (12 linked ideas, each with its formula or rule).**
1. *Shape mismatch:* `cos(q, chunk)` is lower than `cos(q, q')` for a question q' about the same fact. That is the hypothesis being tested, not a law (P4 D.8).
2. *The multi-vector index:* `V = ⋃_p V(p)`, with `V(p) = {e(chunk_p)} ∪ {e(g_{p,1..n})}` (chunks + questions) or `{e(g_{p,1..n})}` (questions only); a map `owner(v) = p`.
3. *The third design:* `e(chunk_p ‖ g_{p,1..n})`, one vector per chunk (doc2query / LlamaIndex).
4. *Parent score:* `s(p) = max_{v∈V(p)} cos(q, v)` (default); alternatives are `Σ` (biased toward parents with more vectors), mean, or `RRF(p) = Σ_lists 1/(60 + rank_l(p))` over a chunk list and a question list (R1 owns RRF).
5. *Oversample, then dedup:* fetch `K_vec ≥ k·|V(p)|max` vectors (e.g. k·(n+1)), dedup in rank order, cut to k parents. Rule: never cut before dedup.
6. *Evaluate the parent:* CE@k over the union of the k parents' `[char_start, char_end)` (06 §7.2); question text never counts as evidence.
7. *Size:* `vectors = N·(1+n)` or `N·n`; `bytes = vectors × d × 4` (float32).
8. *Index-time cost:* `calls = N` per rebuild (n questions per call); `cost = N × (t_in·p_in + t_out·p_out)`; the time floor at a TPM limit is `N·(t_in + t_out)/TPM`.
9. *Break-even against HyDE:* index-side is cheaper in calls when `Q_total > N × rebuilds` (03 §4.2). Latency: I6 adds 0 LLM calls per query; HyDE adds 1.
10. *How many questions:* gains flatten with n [I6-S2]. Choose n on dev with the prefix trick (`n_max` in one call).
11. *Question quality:* drop questions that are unanswerable from their own chunk, vague (deictic), or duplicates; score (question, parent) with a cross-encoder and drop the bottom share [I6-S3].
12. *Leakage:* `leak(i) = max_g sim(q_i, g)` over all generated g. Report its distribution; the decision uses items with `leak(i) < τ` and human-written items (§9).

**Formula-sheet items:**
- the vector count and bytes;
- calls, cost and TPM time;
- the HyDE break-even;
- the max / sum / RRF parent scores;
- `K_vec` oversampling;
- `leak(i)` and τ calibrated from paraphrase pairs;
- CE@k on parent spans.

**Step-by-step outline.** The running example is Corpus D (`Understanding_Climate_Change.pdf`): it is the only frozen corpus with verified seeds (06 §6.7) and the C3 index.
1. **The failure.** D-006, "advantages of putting solar panels on lakes or reservoirs?". The gold is on p.8 ("Floating solar farms, installed on water bodies…"), with lexical traps on p.8 (pumped hydro), p.14 and p.22. Read v0's ranks for D-006 from the v0.1 traces.
2. **Index time vs query time.** Two lanes. Ask MC-003's check: "is the question generation part of the prompt?" (No.)
3. **Generate.** One prompt file (`prompts/i6_questions_v1.txt`) and a JSON-schema list of `n_max = 10`. Show three questions from the p.8 chunk, from the replay pack. Point out any question that reuses "floating" (vocabulary kept) or "reservoirs" (vocabulary shifted).
4. **Clean.** Apply the vague, duplicate and empty-string rules, then (optionally) the cross-encoder filter. Count the removals.
5. **Index.** Build the `vectors → parent` table in two designs; compute the multiplier for n = 5 (582 vs 97 vectors).
6. **Search.** Score D-006 against all vectors; show the top-12 vectors and their owners; dedup; max vs sum; cut to 4 parents.
7. **Score.** CE@4 on the parent spans for D-006, D-002 and D-004. Compare with the baseline.
8. **Cost.** 97 calls, the tokens, $ and the TPM time (§9 table); break-even with HyDE.
9. **Leakage.** For each eval item, show `leak(i)` and which generated question matched. Discuss why a near-copy makes the gain unearned.
10. **The upstream reading.** Doc-aug cell 10 (a 43%-of-corpus parent, k = 1) and HyPE cell 19 (2 of 3 unique). What to fix.

**Visuals that earn their place:**
- **Three-design diagram** (SVG): chunk vectors, question vectors and concatenated text, with arrows to one parent id. *Shows* what is stored and what is returned.
- **Top-k crowding strip** (SVG): 12 ranked vectors coloured by parent, then the dedup to 4 parents. *Shows* why to oversample and dedup first.
- **Max vs sum toy** (small table and bar): a 10-question parent wins under sum without being more relevant. *Shows* the aggregation bias.
- **Cost lanes chart** (Plotly line): cumulative LLM calls against queries served, for HyPE (step per rebuild) and HyDE (slope 1). *Shows* the break-even.
- **Leakage scatter** (Plotly): `leak(i)` against ΔCE@4 per item, coloured by `created_by`. *Shows* whether gains concentrate where index questions copy eval questions.
- **Upstream parent-size bar:** v0 context (about 720 tokens) vs upstream k = 1 (about 5.3K tokens). *Shows* why the repo demo proves nothing.

**Full only:**
- doc2query/docTTTTTquery history and numbers;
- Doc2Query-- filtering;
- the LangChain and LlamaIndex defaults;
- the `input_type` probe;
- RRF aggregation;
- the HyPE paper's claims and why they are not comparable;
- `FRAGMENT_LEVEL` in the upstream code;
- the rebuild and refresh keys.

### 7. Verify notebook plan

`study/notebooks/I6_hype_verify.ipynb`. Offline; runtime under 2 minutes. It **needs no live API call**: it reads the I6 replay pack (the generated questions and their Cohere vectors, recorded once by the LLMOps notebook, §9). With no pack it runs the MiniLM arm, using questions from the pack's JSONL if present, or else only the deterministic parts.
1. **Upstream arithmetic on Corpus D** (PyMuPDF 1.26.7 text; `read_pdf_to_string` uses PyMuPDF): count `\b\w+\b` words; re-implement `split_document` (stdlib); report the number of 4000/100 parents, the 128/16 fragments, each parent's share of the corpus, and the tokens (o200k_harmony) per parent. This resolves I6-E1's DERIVED numbers.
2. **Toy multi-vector index** (hand-made 3-d vectors): max vs sum vs mean vs RRF parent ranking; dedup in rank order vs `set()`; how many unique parents k vectors give; `K_vec` oversampling. Assert the hand-computed values.
3. **LangChain default emulation** (no install): re-implement `MultiVectorRetriever._get_relevant_documents` (L91–L113, quoted with attribution) over the toy, and show that "k = 4" returns 2 parents.
4. **Corpus D index stats:** the vector counts and bytes for n ∈ {1, 3, 5, 10} × 2 designs, at d = 1,536 and 384; compare with C3's 596,096-byte baseline.
5. **Question cleaning on the replay pack:** rule-by-rule removal counts; vague-pattern hits; cross-encoder (question, parent) score histogram (local model) with the bottom-30% cut marked.
6. **Retrieval on the frozen eval set (dev)** with the C3 index and MiniLM: baseline vs chunks + questions vs questions only; CE@4, Hit@4, MRR@10; duplicate-parent rate at `K_vec = 4` and at `4·(n+1)`. Plotly bars per category, with n stated. (Cohere vectors are used only when they are in the pack.)
7. **Leakage report:** `leak(i)` from 3-gram content-word containment and from cosine; the τ calibration from base↔variant pairs; the distribution per `created_by` and category; the de-leaked index result.
8. **Cost calculator:** the §9 table recomputed from `prices.json` and token counts measured on the actual chunks (o200k_harmony).

### 8. Apply-it tool plan and real-world checklist

`study/tools/question_augment_check.py`: "Would index-time question generation help my documents and my questions, and is the gain real?"
- **Inputs:**
  - `--docs` (PDF/MD/TXT), or `--chunks chunks.jsonl` (C3 format);
  - `--queries` (Yash's real questions, one per line; optional `--evalset` in 06 JSONL with gold spans);
  - `--n 5`; `--design both|chunks+q|q-only`;
  - `--llm groq|haiku` (default `auto`: cached or replay first);
  - `--embedder minilm|cohere`; `--budget-usd 0.10`.
- **Privacy:** refuses book text (`privacy.guard`). Asks for consent before sending Yash's own documents to Groq or Anthropic; `--llm none` runs only the deterministic checks.
- **Output:** a Markdown report with the cost estimate before any call, the checklist verdicts, the per-query trace (which question matched and which parent was returned), and the recommendation.

**Real-world checklist (12 checks)**

| # | Check | Auto / manual |
|---|---|---|
| Q1 | **Shape gap exists:** the share of queries that are questions (wh-word or "?") vs the share of chunks that are declarative; mean `max cos(q, question)` − `max cos(q, chunk)` on a sample | auto |
| Q2 | **Baseline actually fails** on paraphrase-style queries (Hit@k / CE@k misses with gold), so there is something to fix | auto (needs `--evalset`) |
| Q3 | **Cost and size within budget:** calls = N, $ estimate, TPM time, vector multiplier, bytes | auto |
| Q4 | **Corpus change rate:** rebuild calls per month vs expected queries per month (the HyDE break-even) | manual (Yash states the change rate and query volume; the tool computes) |
| Q5 | **Hallucinated questions:** the share with a cross-encoder (question, parent) score below the cut; read 20 at random and mark "answerable from this chunk?" | auto + manual |
| Q6 | **Vague or deictic questions** ("this text", "the author", "according to the passage"), duplicates, empty lines | auto |
| Q7 | **Duplicate-parent rate:** unique parents among the top `K_vec`; k is filled after oversampling | auto |
| Q8 | **Rare-token retention:** the share of each chunk's numbers, acronyms and IDs that appear in at least one of its questions (questions only loses keyword queries) | auto |
| Q9 | **Exact-term guard:** CE@k on exact-term queries does not drop (questions only especially) | auto (needs `--evalset`) |
| Q10 | **Leakage:** the `leak(i)` distribution between generated questions and the eval questions; flagged share; the gain recomputed on unflagged items | auto |
| Q11 | **The gain holds on human-written queries** (`created_by`), not only on LLM-drafted ones | auto (if the field is present) |
| Q12 | **Returned context is the parent, not the questions,** and carries page and offsets for citation (unlike HyPE cell 11) | auto |

**Recommendation logic:**
- Q1 or Q2 fails → "no shape gap / nothing to fix: skip I6".
- Q3 fails, or Q4 says that queries per rebuild are below N → "use HyDE (Q2) or nothing; index-time is not cheaper here".
- Q10 or Q11 fails → "gain not established: possible leakage; report as inconclusive".
- Q8 or Q9 fails with questions only → "keep the chunk vectors (chunks + questions) or add BM25 (R1)".
- Q5 or Q6 above about 20% (a [P] tolerance) → "fix the prompt or turn on the filter before measuring".
- Otherwise → "adopt chunks + questions with n = the smallest n within the CI of the best".

### 9. LLMOps notebook plan

`study/llmops/notebooks/I6_hype_ops.ipynb`: index-time question generation as a production index build, traced, cost-tracked and regression-tested.

- **Framework build (each piece mapped to the mechanism):**
  1. *Generation (lesson step 3).* `PromptTemplate` (`prompts/i6_questions_v1.txt`) `|` `CachedChatModel` with a JSON-schema response (`{"questions": [str] (minItems n_max, maxItems n_max)}`), parsed into a Pydantic `QuestionList`. The adapter passes Groq `response_format={"type":"json_schema", strict}`, which phase_03 records as verified for gpt-oss-20b. For Claude it uses structured outputs, never forced `tool_choice` (foundation §6.4). Batch over the 97 chunks with `RunnableLambda.batch(max_concurrency=1)`, so that the throttle governs; no `with_retry` (foundation §9.2).
  2. *Cleaning and filtering (step 4).* Plain functions; the optional cross-encoder filter uses local `sentence-transformers` `CrossEncoder`.
  3. *Embedding (step 5).* `CachedEmbeddings.embed_documents` (batches of 96, C3 key with `input_type` and output dimension). Each question is embedded once, so all n arms share the vectors.
  4. *Multi-vector retriever (step 6), plain Python first:* a NumPy matrix + an `owner` array + `retrieve(q, k, K_vec, agg="max")` that returns `[(parent_id, score, matched_kind, matched_text, vec_rank)]`.
  5. *Comparison cell:* LangChain `InMemoryVectorStore` (langchain-core) + `InMemoryStore` (`langchain_core.stores` L244) wired the way `MultiVectorRetriever` does it. Either import `langchain-classic==1.0.8` (decision 2 in §11) or show its 37-line logic (L76–L113) as a quoted reading cell. **Defaults to name:** k = 4 child vectors, no oversampling, scores dropped, silent drops of children without `doc_id`, a variable number of parents. Set `search_kwargs={"k": K_vec}` and cut to k yourself.
- **External calls (all through the cache; replay mode reruns with no key):**
  - Groq `openai/gpt-oss-20b` (`reasoning_effort="low"`, explicit `max_completion_tokens=800`, temperature 0): **97 calls**, one per chunk at `n_max = 10`, serving n = 1, 3, 5, 10 by prefix. Optional Claude Haiku 5.5 `claude-haiku-5-5` (effort `low`): another 97, for the family-swap arm.
  - Cohere `embed-v4.0`: up to 970 question texts at n = 10 → **11 calls** (≤ 96 per call), and 22 if the Haiku arm also runs. Chunk vectors and eval-query vectors are already in the C3/v0.1 cache (0 new calls). Optional `search_query` probe: +11 calls.
  - LangSmith uploads only after `privacy.assert_corpus_is("D")`.
  - `replay_manifest.json` lists the 97 (or 194) chat keys and the 11 (or 22) embed keys.
- **Tracing (foundation §3.3):**
  - The index-build run has one span per generation call: chunk_id, `text_sha256`, prompt version, `cache_key`, tokens including reasoning, `finish_reason`, the number of questions returned, and the number removed by each filter rule.
  - Each query trace has a retriever span with the top `K_vec` vectors: (vec_rank, score, kind = chunk|question, `matched_question` text, parent_id), then the deduped parents with their aggregated scores. **This is where "which question matched, which parent was returned" lives.**
  - Default: the local JSONL. Viewer: Phoenix (OpenInference `retrieval.documents` carries the parent id and score; the matched question goes in span attributes). LangSmith for Corpus D only.
- **Dataset and evaluators:**
  - The golden set is the frozen Corpus D set, dev split only, for selection.
  - Code evaluators: CE@4 and Hit@4 / MRR@10 on parent spans; the duplicate-parent rate; question-schema validity; the vague-question rate; rare-token retention (Q8); the leakage report.
  - No judge (D-10). Answer generation is not needed, because the parent text is unchanged. If retrieval moves, run the top arm once through v0 generation and have humans read about 10 answers (06 rule 6).
- **The experiment** (06 has no card; this is the branch's pre-registration, `experiments/<id>_I6_doc_augmentation/summary.md`; the id is assigned by the registry):
  - **Problem:** question-shaped queries miss declarative evidence (vocabulary-mismatch and paraphrase items), and the failure persists after the v1.x champion.
  - **Arms (one variable each, against the v1.x champion = A0, plus v0):**
    - A1 chunks + questions, n = 5, max aggregation, `K_vec = 4·6`;
    - A2 questions only, n = 5;
    - A3 the n-sweep {1, 3, 10} on A1 (dev only, for the n-curve; not adoption candidates beyond the best);
    - A4 **de-leaked** A1: delete every generated question with `sim(g, q_i) ≥ τ` for any eval item i (a diagnostic, not a candidate);
    - A5 (optional) the family-swap: the A1 index with Haiku-generated questions (a leakage-sensitivity diagnostic).
  - **Hypotheses:**
    - H1: A1 raises CE@4 over A0 on dev.
    - H2: A2 lowers CE@4 on exact-term items (guard).
    - H3: A1's gain on the **decisive slice** is at least half of its overall gain.
  - **Decisive slice:** items in vocabulary-mismatch or paraphrase-variant categories, **or** `created_by` human, **and** with `leak(i) < τ`. Report its n; it is likely about 10–20 items, so it is diagnostic-strength (06 §9.4).
  - **Leakage guard (pre-registered):**
    - `leak(i)` = max over generated questions of (a) cosine in the stored embedding space and (b) content-word 3-gram containment.
    - τ_cos = the 10th percentile of cosine(base, paraphrase variant) over the ≥ 10 variant pairs (06 §6.2), so "flagged" means "as close as a deliberate paraphrase". τ_ngram = 0.5 ([P]).
    - Report the distribution per category and per `created_by`.
  - **Decision rule (06 §4.1 rule 4):** adopt A1 (or A2) as the I6 champion only if the paired 95% cluster-bootstrap CI of ΔCE@4 on dev excludes 0, H3 holds, the exact-term CE@4 drop is ≤ 1 item ([P]), and MRR@10 does not drop. Then confirm once on test and log the touch. Otherwise the verdict is "inconclusive" (or "inconclusive: possible leakage" if H3 fails or A4 erases the gain).
  - **Equal budget:** the unit is the champion chunk, so k = 4 parents ≈ the A0 budget. Still report mean context tokens; the equal-budget table uses 07's `take_within_budget`.
  - **Q2 link:** v3.1 re-runs HyDE on the same slice and reads A1 from this run's cached results; the comparison is "where the cost is paid".
- **Cost, latency and tokens (estimates, not measured; Corpus D: 97 chunks at 1000/200, about 180 o200k tokens per chunk (P1 facts: 177.5 median per full window); prompt ≈ 350 input tokens; visible output about 80 / 130 / 250 tokens for n = 3 / 5 / 10, plus about 300 reasoning tokens at low effort (UNVERIFIED); prices from foundation §6.2):**

| n per chunk (one call each) | Calls | Groq gpt-oss-20b | Haiku 5.5 | Groq TPM floor (8K TPM) | Share of 200K TPD | Cohere embed calls | Vectors: chunks+q / q-only | Bytes at 1,536-d (chunks+q) |
|---|---|---|---|---|---|---|---|---|
| 3 | 97 | ≈ $0.014 | ≈ $0.022 | ≈ 9 min | ≈ 36% | 4 | 388 / 291 | ≈ 2.4 MB |
| 5 | 97 | ≈ $0.015 | ≈ $0.024 | ≈ 10 min | ≈ 38% | 6 | 582 / 485 | ≈ 3.6 MB |
| 10 (n_max pass; serves all arms) | 97 | ≈ $0.019 | ≈ $0.030 | ≈ 11 min | ≈ 44% | 11 | 1,067 / 970 | ≈ 6.6 MB |
| Upper bound at the 800-token output cap | 97 | ≈ $0.026 | ≈ $0.042 | ≈ 14 min | ≈ 56% | — | — | — |

  - Formulas: e.g. n = 5 Groq = 97 × (350 × 0.075 + 430 × 0.30)/10⁶ ≈ $0.0151; Haiku = 97 × (350 × 0.10 + 430 × 0.50)/10⁶ ≈ $0.0243. Haiku's tokenizer differs, so its counts are approximate. The Cohere price is **UNVERIFIED**; 11 calls are about 1% of the trial cap of 1,000 per month. The baseline index is 596,096 bytes (C3).
  - Query time: 0 LLM calls; exact search over 6–11× more vectors, still well under a millisecond at this scale (to be measured; p50/p95 per stage).
  - Upstream for contrast: `DOCUMENT_LEVEL` makes about 3 calls with "at least 40" questions each.
- **Prompt and config versioning:**
  - `prompts/i6_questions_v1.txt` (never edited; a change is v2); `configs/i6_*.yaml` holding n, design, aggregation, `K_vec`, `input_type`, filter on/off, the generator model id (resolved) and the effort.
  - The question cache key is foundation §2.3 with the chunk text in `input`, so an edited chunk regenerates only its own questions (C3 S4 pattern).
  - A `questions.jsonl` manifest (chunk_id, `text_sha256`, prompt version, model returned, questions) is hashed into `index_manifest_hash`.
- **Monitoring and feedback:**
  - On the monitor page: index-build cost per rebuild, questions per chunk, filter removal rates, the duplicate-parent rate, the leakage-flag share, `finish_reason=length` and schema-failure rates.
  - Alerts: a schema-failure rate above 2% ([P]); the leakage-flag share going up after an eval-set version bump; build cost above budget.
  - A failure (e.g. a hallucinated question pulling a wrong parent) goes into the M5 log, becomes a golden item if confirmed, and gets a regression test.
- **Regression tests (T1 unless marked):**
  - (a) The multi-vector retriever on cached vectors reproduces the champion's ranked parent lists byte for byte.
  - (b) Dedup-before-cut: an injected 3-vector parent never yields fewer than k parents when `K_vec` is sufficient.
  - (c) **Leakage test:** fails on any normalised 8-gram shared by the eval questions or gold quotes and the prompt file or few-shots (foundation §4). Fails if the leakage report is missing or older than the eval-set hash. An injected leak fixture proves it fires. Soft overlap is *reported*, not failed.
  - (d) Schema: every cached response parses into `QuestionList` with n_max items.
  - (e) `replay` marker: the notebook runs headless with `LLMOPS_CACHE_MODE=replay`.
- **Place in the lifecycle:**
  - Analyze: which vocabulary-mismatch failures persist after v1.x (`error-analysis`, `trace-data-analysis`).
  - Measure: CE@4 per slice, the leakage report and cost (`rag-evaluation`, `code-based-evaluators`).
  - Improve: n, the filter and the design (`improving-llm-agents`: index-time vs query-time cost).
  - dev → CI: the T1 tests (`ci-cd-evals`); monitoring through the rebuild-cost panel (`llm-observability`).
- **Skills used:** `rag-evaluation`, `synthetic-data-generation` (the question prompt dimensions), `code-based-evaluators`, `error-analysis`, `ci-cd-evals`, `llm-observability`, `improving-llm-agents`.

### 10. Tools, frameworks, libraries and LLMs

Pins are the newest release on or before 2026-10-03 (PyPI JSON, read 2026-10-17, or as recorded in `LLMOPS_FOUNDATION.md` §11). "Installed" is from the brief and `uv.lock`.

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Question generation (default) | Groq `openai/gpt-oss-20b`, `reasoning_effort="low"`, `max_completion_tokens` explicit, `json_schema` strict structured output (verified per phase_03) | `groq` 1.7.0 | yes | replay yes | 97 calls/build ≈ $0.015–0.026; ≈ 10–14 min at 8K TPM (plan UNVERIFIED) | Apache-2.0 | yes (D-04) |
| Question generation (credits) / family-swap arm | Claude Haiku 5.5 `claude-haiku-5-5`, effort `low`, no `temperature` | `anthropic` 1.11.0 | no | replay yes | 97 calls ≈ $0.024–0.042 | MIT | yes (D-32); a different family from a gpt-oss eval drafter |
| Embeddings (default) | Cohere `embed-v4.0`, `input_type="search_document"` for questions (the `search_query` probe is an arm) | `cohere` 7.2.0 | yes | replay yes | 4–11 calls per arm; price UNVERIFIED | MIT | yes (D-03) |
| Embeddings (fallback) | `sentence-transformers/all-MiniLM-L6-v2` | `sentence-transformers` 6.1.0 | yes | yes | $0 | Apache-2.0 | yes |
| Question filter (Doc2Query-- style) | `cross-encoder/ms-marco-MiniLM-L-6-v2` via `CrossEncoder` | same | yes (library; model in the HF cache per 06 §3.2) | yes | $0; 97 × n pairs | Apache-2.0 (model card, UNVERIFIED here) | yes |
| Vector math, multi-vector index | `numpy` (exact search, D-07) | locked | yes | yes | — | BSD-3 | yes |
| Token counts | `tiktoken` (`o200k_harmony`) | 0.14.0 | yes | yes | — | MIT | yes |
| Schema | `pydantic` / `jsonschema` | 2.13.5 / 4.26.0 | yes | yes | — | MIT | yes |
| Optional lexical arm (doc2query original) | `rank-bm25` (P3 tokenizer) | 0.2.2 | yes | yes | — | Apache-2.0 | yes (R1 link only) |
| Framework core | `langchain-core` (`PromptTemplate`, `InMemoryVectorStore`, `InMemoryStore`, Runnables) | 1.6.6 (2026-09-29) | no | yes | — | MIT | yes, after the mechanism |
| Reading / comparison only | `langchain-classic` `MultiVectorRetriever` | 1.0.8 (2026-06-10) | no | yes | — | MIT | read-only by default (foundation); install only if decision 2 says so |
| Reading only | `llama-index-core` `QuestionsAnsweredExtractor` | 0.14.25 (2026-09-21) | no | — | — | MIT (repo) | no install (read source only) |
| Graphs | `langgraph` | 1.2.12 | no | — | — | MIT | **not needed**: the flow is linear |
| Provider integrations | `langchain-groq` / `langchain-cohere` | — | no | — | — | MIT | **not used** (conflicts); use the `CachedChatModel` / `CachedEmbeddings` adapters |
| Hosted tracing | `langsmith` (`evaluate(upload_results=False)` unless Corpus D) | 0.14.4 | no | SDK partly | free plan | MIT (SDK) | yes, Corpus D only |
| Local tracing | `arize-phoenix-otel` + `openinference-instrumentation-langchain` / `-groq`; server via `uvx arize-phoenix@20.19.0 serve` | 0.17.2 / 0.1.78 / 0.1.31 | no | yes | $0 | Apache-2.0 / ELv2 | yes |
| Cache and replay | `study/llmops/` helper package | — | not built | yes | — | ours | required |
| Upstream vector store | `faiss-cpu` | — | no | — | — | MIT | **not needed** (NumPy exact, D-07) |
| Upstream LLM and embedder | OpenAI `gpt-4o-mini`, `text-embedding-3-small` | — | — | — | — | — | **no** (OpenAI excluded) |

**Install lines** (do not run):
- `uv add --group llmops langchain-core==1.6.6 langsmith==0.14.4 arize-phoenix-otel==0.17.2` (shared with other phases);
- `uv add --group llmops anthropic==1.11.0` (when credits exist);
- only if decision 2 = yes: `uv add --group llmops langchain-classic==1.0.8`.

**Keys:** `GROQ_API_KEY` and `COHERE_API_KEY` (present). `ANTHROPIC_API_KEY` for the Haiku arm and `LANGSMITH_API_KEY` (+ `LANGSMITH_ENDPOINT`) when needed. Never put `LANGSMITH_TRACING` in `.env`.

### 11. Open questions for Yash (preferences only)

1. **Which model writes the index-time questions?** **Haiku** if you have credits (recommended, because it is a different family from the gpt-oss-drafted eval items, which lowers the shared-phrasing leakage risk), or **Groq** now, with the Haiku family-swap arm later. **haiku / groq**
2. Install `langchain-classic` for one comparison cell, or read `MultiVectorRetriever` as quoted source plus a 15-line re-implementation? **No install** is recommended. **install / read**
3. Run the I6 experiment at all, or take 02's "mechanism recall plus transfer only" route? **Run** is recommended: it costs about 2 cents, and it teaches the leakage check that Q2 needs too. **run / mechanism-only**

---

## Concept I-CMP: Comparative lesson: the granularity family (E, v1.x summary)

### 1. Sources checked

- **Book (not present in this session; nothing re-opened, all UNVERIFIED).** Page notes come from 02, 03 and 04 only:
  - Ch9 p.10–11/14: where semantic chunking sits among strategies; the "strategy spectrum" (per 04 §3 Ch9). DV-B12: the spectrum on p.11/14 lists the context window as a chunking strategy, although Ch8 and Ch9 p.10/14 say the window leaves chunking unchanged (per 04 §6.2).
  - Ch4 p.10–11/15: propositions vs standard chunks (per 04 §3 Ch4).
  - Ch8: **the two plans disagree.** 02 cites p.8–10/11 "(compared to propositions)". 04 §2.4 cites p.7/11–p.8/11, and 04's Ch8 section says p.7–8/11 is the relation to contextual headers. DV-B11 places a proposition-cost statement on Ch8 p.9/11. See §4, I-CMP-E1.
  - App A: quick-reference cost tables with Low/Medium/High ratings and no stated scale. 02 says p.10–11/23. 04 says p.9/23–p.11/23, with the decision tree on p.11/23 (DV-B7) and the query-cost table on p.10/23 (DV-B8). See I-CMP-E2.
  - Ch1 p.10–11/14 (chunk-size trade-off) and the ratings 03 §4.1 quotes (Ch1 Low/Low, Ch9 Medium/Low, Ch4 High/Low, Ch7 Medium/Low, Ch11 High/Low; per 03, UNVERIFIED).
- **Repo notebooks, downloaded at `009adba2…` and read cell by cell (0-based, verified).** The units table is in §5.1.
  - `choose_chunk_size` cells 4, 6, 8, 10, 12.
  - `semantic_chunking` cells 10, 12, 14, 16.
  - `proposition_chunking` cells 7, 9, 12, 13, 15, 16, 18, 22, plus the saved outputs of 16, 20, 24, 28 and 29.
  - `contextual_chunk_headers` cells 8, 9, 11, 13, plus the markdown in cells 14–15.
  - `document_augmentation` cells 4, 6 (`split_document`), 10, 13.
  - `HyPE_Hypothetical_Prompt_Embeddings` cells 0, 7, 9, 11, 13, 15, plus the saved outputs of 15 and 19.
  - `simple_rag` cells 10 and 13.
  - `helper_functions.py` L48–L76.
- **Course files:**
  - 02: the I-CMP card, Phase 4 cards and §4 gates (Gate 3→4, the per-technique gate, the eval-set-size note).
  - 03: §2.1 rows 427–433, the exposure and unlock rule (lines 464–465), §2.2 bullets, §3.1 Phase 4 table, §4.1 granularity family, §4.2 query-side vs index-side.
  - 04: §2.4; §3 Ch1, Ch4, Ch8, Ch9 and App A; §6.1 (DV-03, DV-06, DV-13–15, DV-19–20, DV-23, DV-25); §6.2 (DV-B7, DV-B8, DV-B11, DV-B12).
  - 06: §3.1–3.2, §4.1 rules, v1.0–v1.4 cards, §4.3 roll-up, §5.1, §6.2, §6.3 item 6 (split), §7.3, §7.5, §9.2–9.4.
  - 07: D.5 (units), G.5, Part I (the I1 design, `take_within_budget`).
  - 08: D-03, D-06, D-07, D-08, D-09, D-10, D-32.
  - `C2LAB_FACTS.md`, `C3_FACTS.md`, LLMOPS_FOUNDATION (Summary, §2.3–2.5, §3.2–3.3, §4–7, §9.2–9.3, §10–12), `phase_03_measurement.md` (M4, M5).
  - The tracker and the misconception log (MC-001, MC-003, MC-005).
- **AE book:** not present. The review lists no I-CMP item. Its I3 row ("book calls semantic chunking a quick win; a guide calls it marginal") and its I5 rows (cost ladder; "vendor number vs our metric") feed this lesson (review §4, rows at lines 248–250; per the review, not re-opened).
- **Interview repo (MIT, "Copyright (c) 2026 Om"):** AIQ `04-rag-and-retrieval/questions.md` Q4 (strategies and how to pick one, plus the follow-up "How do you A/B test two chunking strategies?") and Q5 (size and overlap). SDG `06-retrieval-systems/02-chunking-strategies.md` (headings read only).
- **External:** [I-CMP-S1]…[I-CMP-S9] (list at the end). Comparative benchmarks only; each mechanism belongs to its own helper.

### 2. Gap audit

Tracker (2026-10-17): I1–I6 and I-CMP `not_started`; P1, M2, M3, M5 `exposed`; P4, C1–C3, M1, M4 `not_started`. Open misconceptions that matter here: MC-001 (tokens = characters), MC-003 (index time vs query time), MC-005 (one-sided k trade-off).

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class (core / bridge / next) | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Two independent axes: **boundary** (fixed / structure / semantic / proposition) vs **representation** (headers, generated questions); they compose | 03 §4.1; 02 card | 03 only | I-CMP | no | core | The 2-axis map is the lesson's spine. Every member gets one cell |
| 2 | "Retrieve small, return big" is a third axis: the retrieval unit can differ from the returned unit (I6 parent, proposition `chunk_id`, X1 windows) | 03 §4.1 | 03 only | I-CMP (X1 later) | no | core | One row per member: retrieval unit → returned unit |
| 3 | Size units differ across the repo: characters, gpt2 or cl100k tokens, regex "words", sentences, LLM propositions | 07 D.5; 04 P1/C2 rows; §5.1 | 07 written, not studied; P1 lesson written | P1 / C2 | P1 exposed (MC-001 open) | bridge | Re-show the §5.1 table. Every cell of the comparison table names its unit and tokenizer |
| 4 | Size *distribution*, not only mean size: uncapped semantic chunks; 393–1,000-char v0 chunks; page length capping size (07 I.3) | 02 I3; C3_FACTS S1 | **missing** as a cross-technique idea | I-CMP | no | core | Box plot per member: chars and embedder tokens, truncation share |
| 5 | Equal-k vs equal-token-budget fairness; overlap and duplicate parents spend the budget twice | 06 §4.1 rule 2, §9.2; 07 I.2 | 07 written; M4 not studied | M4 / I1 | no | bridge | Worked equal-budget k for every member (formula sheet). "Unique characters in context" as a diagnostic |
| 6 | Index-time cost model per technique (embeds + LLM calls + tokens), and query-time cost | 03 §4.1 columns; 02 I4/I6 outcomes | 03 table (calls only, no tokens) | I-CMP | no | core | Cost ladder, with Corpus D numbers marked DERIVED (§6) |
| 7 | Index size (vectors × dim × 4 bytes) and rebuild cost on corpus change | C3_FACTS S6, S8 | C3 written, not studied | C3 | no | bridge | One formula; HyPE and propositions multiply N |
| 8 | Failure bucket targeted (M5 buckets: parsing, boundary, vocabulary mismatch, exact-term, rank, context noise, unsupported claim, should-have-abstained) | 02 M5; per-technique gate | M5 exposed | M5 | exposed | bridge | Per-bucket heat table: hypothesis first, measured Δ later |
| 9 | "When NOT to use" per member | per-technique gate; 06 cards | 06 only | each I-concept | no | core (as a comparison) | A column; at least one case from Yash's own data |
| 10 | Champion lineage: each v1.x arm runs on the previous champion, so effects are **conditional**, not marginal | 06 §4.1 rule 1; 03 §2.1 project-order note | **missing** | I-CMP / M4 | no | core | A lineage diagram; every row records its base config |
| 11 | Multiple comparisons across the whole v1.x family (≈ 45–50 dev arms) and repeated test touches | 06 §9.4 item 3; 06 v1.3 card | M4 (not studied) | M4 | no | bridge | Family-wise error table, Holm across arms per round, the test-touch log as the family register |
| 12 | Power at the real dev size (~30% of ~40–55 items ≈ 12–16 dev items) | 06 §6.3 item 6, §9.4 | 06 reasons at n = 50 only | M4 | no | core (here) | Recompute MDE at dev n; "inconclusive" is the expected verdict for most rows |
| 13 | Filling the table honestly: measured / not run (reason) / inconclusive / not comparable / derived only | 02 card "your numbers or 'not run'" | **missing** | I-CMP | no | core | A cell-state legend; book ratings sit in their own column |
| 14 | Comparable rows need identical comparison keys; the v1.4 subset has a different qid set | 06 §4.1 rule 1, v1.4 card | 06 only | M1 / M4 | no | core | Show the refused comparison; rerun the champion on the subset |
| 15 | External benchmark numbers use different metrics (character-range IoU/recall at k = 5, F1@5, 1 − recall@20, LLM-judged accuracy, fixed 4,096-token context) and cannot be compared with CE@4 | §5.2 | **missing** | I-CMP | no | core | A metric-translation table; the "which is better?" item |
| 16 | Decision procedure for a new corpus (the transfer task) and a pre-registered plan | 02 card outcome 2; gate transfer item | **missing** | I-CMP | no | core | A flowchart plus one worked unseen corpus (§6) |
| 17 | Index-side vs query-side cost crossover (I6 vs Q2) | 03 §4.2 | 03 only | I6 / Q2 | no | bridge | One line: index-side is cheaper in calls when Q_total > N_units × rebuilds; with replay, repeated eval runs are free |
| 18 | Single-document corpus limits: a title header is identical on all 97 Corpus D chunks | 06 v1.2; 03 §4.1 "expected to lose" | 03 hint only | I5 | no | bridge | Explain why D cannot test title headers; T decides (06 §5.1) |
| 19 | Book ratings have no stated scale and are unmeasured | 04 App A; DV-B8 | 04 only | I-CMP | no | core | A separate "book rating" column, never mixed with measurements |
| 20 | The context window (X1) is not a chunker (DV-B12) | 04 §6.2 | 04 only | X1 | no | next | One line; link to X1 |
| 21 | Late chunking as a representation-axis alternative | AIQ 04 Q4; ext review I5 row | **missing** | I5 (Full) | no | next | Mention only; it needs token outputs from a long-context embedder |

### 3. Quiz coverage

No question file exists. Titles needed (`study/questions/I-CMP_questions.md`):

- **R (recall):**
  - Name the two axes of the granularity family and place I1–I6 on them.
  - Why must a chunker comparison hold the token budget equal, as well as k?
  - What may a cell say instead of a number, and when ("not run", "not comparable", "derived")?
- **A (application):**
  - Given chunk token counts for three arms and B = 4 × v0's mean, compute each arm's k at equal budget, including duplicate parents for HyPE.
  - Count index-time embeds, LLM calls and tokens for I3, I4, I5 (per-chunk) and I6 on a 100-chunk corpus.
  - Five v1.x rounds each confirm one candidate on test at α = 0.05: what is the chance of at least one false adoption under no true effect (0.226)? Apply Holm to three arms.
  - The dev split has 12 answerable items. What is the smallest CE@4 difference you could detect with b + c = 4 (≈ 0.47)?
- **T (transfer):**
  - Choose a chunker for an unseen corpus description, and write the pre-registered three-arm plan (the gate's transfer item).
  - A report says chunker A wins on recall@5 and chunker B wins on IoU. Explain how both can be true.
  - A vendor reports a 67% cut in 1 − recall@20; your CE@4 moved +0.04. Which is better? (You cannot tell; say why.)
  - v1.4 ran on a 5-page subset. Can its CE@4 sit in the roll-up beside v1.3? (No; rerun the champion on the subset's qids.)
- **Interview:** AIQ 04 Q4, "What chunking strategies do you know, and how do you pick one?", with its follow-up "How do you A/B test two chunking strategies?" (MIT, © 2026 Om).

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| I-CMP-E1 | 02 I-CMP card (Book: Ch8 p.8–10/11 "compared to propositions") vs 04 §2.4 (Ch8 p.7/11–p.8/11) | The two plans cite different pages. 04's own Ch8 section says p.7–8/11 covers the relation to **contextual headers**, and DV-B11 cites Ch8 p.9/11 for a proposition-cost statement. Possibly both are partly right; neither was re-opened here | Re-open Ch8 p.7–10/11 and record which page compares with Ch7 and which with Ch4 |
| I-CMP-E2 | 02 card (App p.10–11/23) vs 04 App A (quick-reference tables and decision tree p.9/23–p.11/23) | A page-range mismatch | Re-open App p.9–11/23 |
| I-CMP-E3 | 02 card, Repo line: "cross-cutting units summary … see 04" | 04 has no such section. The material sits in 04's P1 and C2 rows, and the full table is 07 D.5 | Point the card to 07 D.5 (and this file's §5.1) |
| I-CMP-E4 | 03 §2.2 bullet "I-CMP ← exposure to I2–I6" | It says 02's card names I2–I5. Since M-07, 02 names I2–I6 | Drop the stale clause |
| I-CMP-E5 | 06 §4.3 roll-up template | It lacks what I-CMP needs: index-time LLM calls and tokens, #vectors and index bytes, build time, CE at equal budget, base config (lineage), split and n, qid-set hash. It has no I6 branch row. The v1.4 subset uses a different qid set, so under 06 §4.1 rule 1 its row cannot sit beside v1.0–v1.3 | Add the columns, plus a "comparable to" column. Require a champion rerun on the v1.4 subset qids |
| I-CMP-E6 | 06 §6.3 item 6 (~30% dev) vs §9.4 (power reasoned at n = 50) | With 40 answerable items, dev is about 12 items. One item is 8.3 points, and the MDE is about 0.40–0.47 (§6). The v1.0 grid (37 configurations) plus about 10 more Phase 4 arms are selected on those 12 items | State the dev-n MDE in §9.4. Grow the set toward the D-09 target (60–100) before v1.x selection, or cap the arms (decision 1 below) |
| I-CMP-E7 | 02 I4 Pre (I1, I3, M3); 03 row 430 (I4 requires I3) | The I4 mechanism uses no I3 machinery: cell 9 is a recursive tiktoken splitter followed by LLM calls, with no sentence embeddings. 03 §3.1 itself labels the edge "(02 order)" | Make I3 → I4 an advice edge, or state the conceptual reason (meaning-based boundaries) |
| I-CMP-E8 | 02 I5 Pre (I1, C3) | v1.2's header is "doc title > section heading" (06), which needs I2's heading detection (v1.1). The edge is missing | Add an advice edge I2 → I5, or say in the card that the section-path arm reuses I2's detector even if I2 is rejected |
| I-CMP-E9 | `progress/concept_tracker.csv` I4 priority `S` vs 02 `S/U` | A minor mismatch | Align |
| I-CMP-E10 | 02 I1 and 04 DV-06 (describe `choose_chunk_size` as a climate-PDF experiment) | Cell 4 loads `SimpleDirectoryReader("../data")`, i.e. **every file** in `data/`, and cell 6 uses the first 20 loaded documents. Cell 6 also generates questions before cell 8 sets `Settings.llm`. The folder contents at the pinned commit were not listed (the GitHub API was blocked): UNVERIFIED | Say "the data folder (contents UNVERIFIED)", not "the climate PDF" |

### 5. What the research says

#### 5.1 Upstream: the seven notebooks are not a comparison (verified, cells 0-based)

| Notebook (cells) | Corpus | Size unit | Size / overlap | Splitter | Embedder | LLM (index / answer / judge) | k |
|---|---|---|---|---|---|---|---|
| `simple_rag` (10, 13) | climate PDF, per page (PyPDFLoader) | characters (`length_function=len`) | 1000 / 200 | `RecursiveCharacterTextSplitter` | `get_langchain_embedding_provider(OPENAI)` (cell 10); `helper_functions.py` L73 hardcodes `OpenAIEmbeddings()` | none | 2 |
| `choose_chunk_size` (4, 6, 8, 10, 12) | `../data` folder, first 20 docs (UNVERIFIED contents) | LlamaIndex tokens (cl100k per 07 D.5) | [128, 256] / size // 5 | LlamaIndex default node parser via `Settings.chunk_size` | LlamaIndex default (not set; UNVERIFIED) | `gpt-3.5-turbo` answers; `gpt-4o` judge; 25 sampled questions | 5 |
| `semantic_chunking` (10, 12, 14, 16) | climate PDF as one string (`read_pdf_to_string`; pages lost) | sentence groups; **no size cap** | percentile 90 | `SemanticChunker` | `OpenAIEmbeddings()` unpinned, for breakpoints and index | none | 2 |
| `proposition_chunking` (7, 9, 12–16, 18, 22) | inline Paul Graham essay text (cell 7), **not** the climate PDF | gpt2 tiktoken tokens (`from_tiktoken_encoder`; 07 D.5) | 200 / 50 → 3 chunks | recursive + LLM propositions | Ollama `nomic-embed-text:v1.5` | Groq `llama-3.1-70b-versatile` generates **and** grades (cells 12, 15); per-proposition grading (cell 16; saved output shows propositions no. 17 and 31 failing) | 4 (over 3 chunks) |
| `contextual_chunk_headers` (8, 9, 11, 13) | Nike 2023 10-K text | characters | 800 / 0 | `RecursiveCharacterTextSplitter` | none (no index is built) | `gpt-4o-mini`, T = 0.2, title from the first 4,000 cl100k tokens; Cohere `rerank-english-v3.0` scores one chunk | — |
| `document_augmentation` (4, 6, 10, 13) | climate PDF as one string | regex words `\b\w+\b` ("tokens") | windows 4000/100, fragments 128/16 | custom `split_document` (drops punctuation) | `OpenAIEmbeddings()` | `gpt-4o-mini`, T = 0; 40 questions per **window** (`DOCUMENT_LEVEL`) | 1 |
| `HyPE_…` (7, 9, 11, 13, 15) | climate PDF, per page | characters | 1000 / 200 | `RecursiveCharacterTextSplitter` | `text-embedding-3-small` | `gpt-4o-mini`, T = 0; one call per chunk, **97/97** in the saved output of cell 15; the question count is left to the model | 3 (deduped by `set`) |

What follows (inference from the table):
- Across the seven notebooks there are 4 corpora, 5 size units, 6 embedder settings (one is none), 5 LLM ids and k from 1 to 5. No two techniques share a baseline, so no upstream number ranks one chunker against another.
- The only quantitative comparative claim is the CCH markdown in cell 15. It reports the repo's KITE benchmark: 4 datasets, **50 questions**, graded 0–10 by an LLM, average 4.72 → 6.04 with title + summary headers. A FinanceBench 19% → 83% result was measured jointly with RSE. Both are unreproduced repo claims (not external).
- `HyPE` cell 11 is a SyntaxError as committed: a missing comma after the `IndexFlatL2(...)` argument (confirmed). The saved 97/97 output predates it.

#### 5.2 Comparative benchmarks: what was compared, the metric, the result, the limits, what transfers

| Source | Compared | Metric (unit) | Result | Limits | What transfers |
|---|---|---|---|---|---|
| Chroma report [I-CMP-S1] with code [I-CMP-S2] | recursive and token splitters at several sizes and overlaps; Kamradt semantic; Chroma's ClusterSemanticChunker and LLMChunker | **Character-range** recall, precision and IoU (verified in `base_evaluation.py`: chunk `start_index`/`end_index` from searching the corpus string), at `retrieve=5` by default; "precision Ω" uses the best possible chunks. The precision denominator **sums** retrieved chunk lengths without a union, so overlap is penalised | Report page not reachable. Secondary summaries (UNVERIFIED) give recall ≈ 87–92% but IoU ≈ 4–7% at ≈ 200 tokens and k = 5, with the LLM chunker highest on recall and lowest on IoU | Verified: **472** LLM-generated queries over **5** corpora (wikitexts 144, pubmed 99, finance 97, state_of_the_union 76, chatlogs 56); OpenAI embedders; fixed k, so bigger chunks raise recall and lower IoU mechanically | Span-based gold is the right idea; it matches 06's offset gold. Recall vs IoU ranks chunkers differently, which is exactly why 06 uses CE@k **plus** an equal budget |
| Qu, Tu & Bao, Findings NAACL 2025 [I-CMP-S3] | fixed-size vs breakpoint semantic vs clustering semantic | F1@5 for document retrieval, evidence retrieval and answer generation | Search-checked only: semantic chunking's cost was not justified by consistent gains. It won mainly on **stitched** datasets (artificial topic shifts, e.g. Miracl stitched 81.89 breakpoint vs 69.45 fixed, per a search snippet); fixed-size did better on non-stitched | Synthetic stitching creates the very boundaries semantic chunking detects; BEIR/RAGBench-style data | Corpus D and T are real documents, not stitched, so expect a small or no I3 gain. Pre-register "inconclusive" as a likely result |
| NVIDIA developer blog (2025 per search; the brief says 2024) [I-CMP-S4] | token chunks 128–2,048 with 10/15/20% overlap; page-level; section-level | End-to-end answer accuracy; how it was judged, and the scale, are not visible (secondary: "metric scale unstated") | Search-checked only: page-level had the highest average and the lowest variance; 15% overlap was best at 1,024 tokens on FinanceBench | Vendor; paginated financial PDFs; the page could not be opened | Pages are a strong, free baseline for paginated PDFs (06 v1.0 already lists this as a "when NOT to use a grid" case). Add a page-level arm |
| Merola & Singh, ECIR 2025 workshop [I-CMP-S5] | early chunking vs late chunking vs contextual retrieval (Phi-3.5-mini contexts) | Retrieval relevance metrics (exact metric not opened) | Search-checked only: contextual retrieval kept coherence better but cost more compute; late chunking was cheaper, with results that depend on the embedder and dataset | Small models; page not opened | Representation-axis arms need a cost column; their gains depend on the embedder |
| HiChunk / HiCBench, ACL 2026 [I-CMP-S6] | fixed 200, semantic, LumberChunk (LLM), HiChunk (hierarchical, fine-tuned LLM) with auto-merge | Answer-level metrics at a **fixed 4,096-token context** (verified in the README: `--token_num 4096`) | Scores not opened (UNVERIFIED). The benchmark argues that evidence-sparse QA cannot discriminate chunkers | Needs GPU and vLLM to reproduce | Two design rules transfer: compare at an equal token budget, and use evidence-dense (multi-span) items, because single-sentence items hide chunking effects |
| Anthropic, Contextual Retrieval (2024) [I-CMP-S7] | contextual embeddings ± contextual BM25 ± reranking | **1 − recall@20** over relevant chunks (verified) | 5.7% → 3.7% → 2.9% → 1.9% (reranking from the top 150 to 20); about $1.02 per million document tokens with prompt caching, assuming 800-token chunks and 8k-token documents | Vendor; unnamed datasets; k = 20 | No way to compare with CE@4; the cost model per chunk is the useful part |

**The metric-comparability lesson.** These six sources use six different scores: character-range IoU and recall at k = 5; F1@5; LLM-judged accuracy; recall at a fixed 4,096-token context; 1 − recall@20; and our CE@4 at fixed k and equal budget. They also differ in k, unit, corpus, embedder and query source (LLM-generated vs human). A number from one cannot be ranked against a number from another. What transfers is (a) the **direction under stated conditions** (semantic chunking helps on stitched topic shifts; pages are strong on paginated PDFs; contextual text helps when chunks are anonymous) and (b) the **design rules** (span gold, equal budget, evidence-dense items).

**Current practice (2024–2026).** Structure-aware or recursive chunking as the default, with the heading path embedded. Contextual enrichment or late chunking when chunks are ambiguous. Small-to-big retrieval. Chunk size chosen on a labelled set. AIQ 04 Q4 puts it this way (MIT, © 2026 Om): semantic chunking "in practice gains are marginal over recursive+structure-aware and it adds embedding cost at ingest" [I-CMP-S8]. That is a guide's opinion, consistent with [I-CMP-S3].

**Pitfalls (with evidence):**
- Fixed-k comparisons reward bigger units on recall [I-CMP-S2 code].
- Overlap and duplicate parents inflate precision-like metrics or waste the budget (06 §7.3 traps; 07 I.2).
- Uncapped semantic chunks exceed the embedder's limit (06 §3.2; 02 I3).
- LLM-written units can be unfaithful: I4 self-grading (DV-13).
- Single-document corpora cannot test title headers (§2 row 18).
- Many arms on a tiny dev set produce a winner by chance (06 §9.4).

**How to evaluate the family.** CE@4 at fixed k **and** at equal budget B, with Span-Coverage@4 and MRR@10 as diagnostics. Per bucket with n. Paired group bootstrap plus discordant counts. Index-time calls, tokens, cost and bytes per arm. All on identical comparison keys; dev selection; one test touch per round. Decisions on Corpus T; D for parity (06 §5.1).

**Interview angle:**
- How do you pick a chunker? (AIQ 04 Q4.)
- How do you A/B test two chunkers? (Q4 follow-up.)
- What does chunk size trade? (Q5.)
- Why are vendor chunking benchmarks not comparable?
- When is HyPE (index-time) cheaper than HyDE (query-time)?

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).** Every member of the granularity family changes one of two things: where the boundaries go (fixed windows, document structure, embedding-distance breakpoints, or LLM-written propositions), or what text represents a unit in the index (a header, or generated questions). The two axes combine freely, and a third choice, retrieving a small unit but returning its parent, cuts across both. They differ in unit, size spread, index-time cost (from 0 LLM calls to more than one per proposition), index size, and the failure bucket they target. None is better in general. The only fair comparison holds the question set, the embedder and the token budget fixed, and with about 12–16 dev questions most differences will honestly read "inconclusive". So you choose for a new corpus by matching its structure and question mix to each member's target failure and cost, then pre-register at most three arms, and write "not run" or "not comparable" wherever you have no fair number.

**The theory in one read (11 ideas, each with its formula):**
1. *Two axes plus one:* unit = boundary(text); pointer = representation(unit); returned = parent(unit) or the unit itself.
2. *Units:* size_chars ≈ size_tokens × ρ, where ρ is measured per corpus and tokenizer (Corpus D: 5.57 cl100k, 5.07 gpt2, 6.20 WordPiece; 07 D.5). Never compare a "500" with a "500".
3. *Size distribution:* report min, median, p95 and max in chars and in embedder tokens; truncation share = #(tokens > max_seq_len) / N.
4. *Index-time cost per member* (N = chunks, S = sentences, P = propositions, D = documents, q = questions per unit):
   - I1 and I2: E = N, L = 0.
   - I3: E = S (breakpoints) + N (index), L = 0.
   - I4: L = N (generate) + P (grade, per cell 16), E = P.
   - I5: deterministic, L = 0 and E = N (all new cache keys); title, L = D; per-chunk context, L = N with N × (doc + chunk + prompt) input tokens.
   - I6: document level, L = D_win; HyPE, L = N; E = N·q (+ N if the originals are kept).
5. *Query-time cost:* 1 query embed for all members; 0 LLM calls; exact search O(N_vectors · d).
6. *Index bytes* = 128 + N_vectors × d × 4.
7. *Equal-budget k:* walk the ranked list until Σ tokens ≤ B (`take_within_budget`, 07 I.2), with B = mean v0 context tokens at k = 4. Deduplicate parents first (HyPE, I6a, propositions returned as parents). Header tokens count only if the header is kept at generation.
8. *Fair comparison:* identical comparison keys; one variable; fixed k **and** equal B (06 §4.1, §9.2).
9. *Conditional effects:* Δ(arm | champion lineage) ≠ Δ(arm | v0). Record the base for every row.
10. *Family-wise error:* P(≥ 1 false win) = 1 − (1 − α)^m. Holm across the arms in a round. MDE ≈ 2.8·√(b + c)/n at the dev n.
11. *Choosing:* priority = bucket count × severity / cost; the book's Low/Medium/High ratings are hypotheses with no scale.

**Formula sheet items:** ρ; truncation share; the cost model per member (idea 4); index bytes; equal-budget k; the I6 vs Q2 crossover (`Q_total > N_units × rebuilds`, 03 §4.2); FWER; Holm thresholds (0.0167 / 0.025 / 0.05 for 3 arms); MDE.

**Corpus D numbers for the cost ladder** (DERIVED unless noted; prices from LLMOPS §6.2; Groq plan UNVERIFIED):

| Member | Index-time LLM calls on D | Input tokens (≈) | Embeds | Vectors / bytes at 1,536-d | Note |
|---|---|---|---|---|---|
| v0 / I1 1000/200 | 0 | — | 97 (measured, C3) | 97 / 596,096 (C3 S6) | baseline |
| I2 | 0 | — | ≈ N | ≈ N | PyMuPDF `dict` parse cost only |
| I3 | 0 | — | S + N; S ≈ 450–500 sentences (ASSUMPTION from ~9.3k words) | ≈ N | ≈ 6 Cohere calls at 96 texts each |
| I4, full D | ≈ 96 generate + ≈ 960 grade ≈ **1,056** (ASSUMPTION: ~10 propositions per 200-token chunk, from the 3-chunk / ≥ 31-proposition saved output) | ≈ 0.79M | ≈ 960 | ≈ 960 / 5.9 MB | ≈ 3.9 days of a 200K TPD quota; ≈ $0.08 on Groq. (Lead's note: I4's own estimate, from ≈ 620 sentences, is ≈ 1,400 propositions, so ≈ 1,430 calls with per-proposition grading, or 66 calls with per-page batched grading; I4 §5 is authoritative.) |
| I4, v1.4 subset (5 pages) | ≈ 15 + 150 = **165** | ≈ 0.12M | ≈ 150 | — | as 06 v1.4 plans |
| I5 deterministic | 0 | — | 97 (all cache misses: new text) | 97 | — |
| I5 per-chunk context (whole doc) | 97 | 97 × (13,033 + ~230) ≈ **1.29M** | 97 | 97 | ≈ $0.10 Groq or $0.13 Haiku 5.5 (≈ $0.02 with Claude cache reads); **one request (~13K tokens) exceeds an 8K TPM limit**, so it cannot run on that Groq plan (UNVERIFIED plan); use page-level context or Haiku |
| I6a document level | 3 windows (DERIVED from ~9.3–10.8k regex words) | ≈ 3 × 5k | ≈ 86–99 fragments + ≤ 120 questions | ≈ 200 | the parent is a 4,000-word window (DV-25) |
| I6b HyPE | **97** (verified saved output) | ≈ 97 × 300 | 97 × q (q model-chosen; ≈ 8 assumed) ≈ 800 | ≈ 800 / 4.9 MB | the original chunk vector is dropped |

**Step-by-step outline.** Running example: the v1.x arms on Corpus D, recomputed from cached artifacts, then one unseen-corpus decision. Corpus D is used because every per-technique run records on it and it matches upstream; decisions move to T (06 §5.1).
1. Upstream is not a comparison: read the §5.1 table and mark what differs per row.
2. Place I1–I6 on the 2-axis map; add the "returned unit" arrow.
3. Units and size distributions per arm (from each arm's `chunks.jsonl`).
4. The cost ladder (table above), recomputed by Yash from the counts.
5. Equal-budget k per arm; show HyPE duplicate parents eating slots.
6. Fill the comparison table with cell states (legend below); v1.4 gets "not comparable" until the champion is rerun on its qids.
7. The per-bucket heat table: hypotheses (03 §4.1 "expected to win") vs measured Δ CE@4 with n.
8. Family discipline: count the arms tried, compute FWER, apply Holm per round, read `TEST_LOG.md`.
9. **Transfer, worked.** The unseen corpus: an HR policy handbook, 120 Markdown pages with clean H1–H3, three near-identical regional versions (UK/US/IN), questions such as "parental leave in region X", updated monthly.
   - Structure exists, so take boundaries from I2.
   - Near-duplicate documents are where headers win (03 §4.1), so add I5 with region + doc title + section path (deterministic, 0 calls).
   - Skip I3: the headings already give the boundaries, and [I-CMP-S3] predicts little gain.
   - Skip I4: monthly re-indexing would repay its LLM calls every month, and the questions are lookups that sections already answer.
   - Keep I6 as a later branch, only if a vocabulary-mismatch bucket appears.
   - Pre-registered arms: A0 recursive 1000/200 (baseline), A1 = I2, A2 = I2 + I5. Primary metric CE@4 on region-scoped items at fixed k and equal B; guard MRR@10 and mean context tokens; Holm over 2 comparisons; dev → one test touch.
   - Never use Corpus H for this exercise; it is reserved for K1.

**Cell-state legend:** `measured: value [95% CI], n, split, run id` · `inconclusive: CI spans 0` · `not run: reason (empty bucket / cost / branch)` · `not comparable: which comparison key differs` · `derived: cost only, no metric` · `book rating (no scale)` in its own column.

**Visuals (each with the one thing it shows):**
- **2-axis map (SVG):** boundary on x, representation on y, a dashed "returned unit" arrow. Shows that the members compose rather than compete.
- **Cost ladder (bar chart, log scale):** index-time LLM calls and input tokens per member on D. Shows the jump from 0 calls to about 1,000.
- **Size-distribution strip plot** per arm, with the 256/512 truncation lines. Shows which units the embedder cannot fully read.
- **Equal-k vs equal-budget panel:** two bars per arm. Shows when a "gain" is only more context.
- **Per-bucket heat table template:** members × M5 buckets; arrow = hypothesis, number = Δ CE@4 (n). Shows which failure each member targets.
- **Champion lineage graph** v0 → v1.0 → … with adopted/rejected marks. Shows that effects are conditional.
- **Metric-translation table** (§5.2). Shows why vendor numbers do not rank.

**Full only:** late chunking; the HiChunk auto-merge idea; Chroma's precision Ω; the Holm proof; the I6 vs Q2 crossover with caching; Corpus T vs D disagreement as a finding; the KITE and FinanceBench repo claims.

### 7. Verify notebook plan

`study/notebooks/I-CMP_granularity_verify.ipynb`. Offline, **0 API calls**, about 1 minute.
1. **The units table:** recompute ρ (chars per token) on the frozen D snapshot with tiktoken cl100k and gpt2 and the MiniLM WordPiece tokenizer. Assert 72,593 chars and 33 pages (C2/C3 facts). Count regex words (`\b\w+\b`), which also settles I6a's window count. Count sentences with the I3 splitter, which replaces the ASSUMPTION in §6.
2. **The size and cost table:** read each arm's cached `chunks.jsonl` and manifest (I1 champion, I2, I3, I4 subset, I5, I6). Report N, the size distribution in chars and embedder tokens, truncation share, `vectors.npy` bytes (assert 128 + N·d·4) and the index-time calls and tokens from the cache's `usage_json` rows (`cost if called`). An arm that was not run shows "not run".
3. **Equal-budget k:** B from v0's cached top-4 contexts. For each arm, replay its cached query rankings (cached embeddings; exact cosine) through `take_within_budget` after deduplicating parents. Report mean k and mean unique characters.
4. **Comparability check:** the keys checker refuses v1.4 vs v1.3 (different qid set) and accepts the subset rerun.
5. **Family statistics:** FWER for the logged number of arms; Holm over this round; MDE at the dev n (asserts 0.4596 for m = 12 and 0.2262 for m = 5; 0.467 for n = 12, b + c = 4).
6. **Plotly charts:** cost ladder, size strips, equal-k vs budget panel, heat table.
Needs the per-technique runs to exist. Before that it runs on a fixture of v0 plus a synthetic arm and says so.

### 8. Apply-it tool plan and real-world checklist

`study/tools/chunker_chooser.py`: "Given my documents and my questions, which granularity arms should I test, and what will each cost?" It follows the `bm25_fit_check.py` pattern: offline, deterministic, a checklist with auto and manual verdicts.
- **Inputs:**
  - `--docs` (PDF, Markdown or text files);
  - `--questions` (optional JSONL with `category`);
  - `--profile` (YAML: update frequency, expected queries per month, budget in USD or calls, provider);
  - `--k 4`, `--embedder minilm|cohere-meta`.
- **Measures:** heading detectability (PyMuPDF font-size spans or `#` lines); page and section length distributions; ρ per tokenizer; truncation share at candidate sizes; near-duplicate documents and sections (8-word shingle Jaccard); the share of chunks starting with an unresolved pronoun or "this/it" (a proxy for anonymous chunks); sentence count; numeric and table density; the question-type mix; index-time calls, tokens, USD and quota-days per arm.
- **Outputs:** a ranked list of up to 3 arms with reasons; a "not recommended because" list; a **pre-registration draft** (hypotheses, primary metric, k and B, Holm α, dev/test plan, MDE at the stated n); the checklist. API calls: 0 (costs are estimates from token counts).

**Real-world checklist (12 checks)**

| # | Check | Auto / manual |
|---|---|---|
| K1 | The size unit and tokenizer are named for every arm; ρ is measured on this corpus | auto |
| K2 | No candidate exceeds the embedder's max length for more than 1% of chunks | auto |
| K3 | Reliable structure exists (headings detected on ≥ 80% of pages or files); otherwise I2 is not proposed | auto + manual (inspect 10 chunks) |
| K4 | Near-duplicate documents or sections exist (headers worth testing); a single-document corpus is flagged for title headers | auto |
| K5 | The anonymous-chunk proxy is high enough to justify a contextual arm | auto + manual (read 10) |
| K6 | The question mix fits the targets: factoid share (I4), vocabulary mismatch (I6), multi-span (bigger units / small-to-big) | auto if questions are given, otherwise manual |
| K7 | Index-time cost per rebuild × rebuilds per month fits the budget and the provider's quota (TPD, per-request TPM) | auto |
| K8 | The equal-budget B is at least the largest chunk of every arm | auto |
| K9 | At most 3 arms; Holm α stated; the MDE at the dev n is shown; "inconclusive" is allowed | auto |
| K10 | Gold is chunk-agnostic (character spans), so all arms are scored on the same labels | manual (check the eval-set schema) |
| K11 | A page-level or section-level arm is considered for paginated PDFs [I-CMP-S4] | auto (suggested) |
| K12 | "When NOT to use" is written for each rejected arm, with one example from these documents | manual |

**Recommendation logic:**
- Always A0 = recursive at the measured-safe size.
- Add I2 if K3 passes.
- Add I5 (deterministic) if K4 or K5 passes. Propose the LLM context arm only if the deterministic arm helps and K7 passes.
- Propose I3 only if long topic-shifting prose and no structure.
- Propose I4 only on a subset, for a factoid-heavy mix, with a static corpus and K7 passing.
- Propose I6 only for a vocabulary-mismatch bucket with many expected queries.
- Cut to 3 arms by bucket count × severity / cost.

### 9. LLMOps notebook plan

`study/llmops/notebooks/I-CMP_family_ops.ipynb`: one consolidated experiment view across the v1.x arms, as a team would run a chunker bake-off.
- **Framework build:**
  - The Corpus D golden set mirrored to a LangSmith dataset (tag = `dataset_sha256[:12]`), allowed because it is Corpus D only.
  - Each arm is one `langsmith.evaluate(..., upload_results=False)` experiment locally. It is uploaded only for D, with metadata `{version, arm, params_hash, embed_hash, base_champion, index_calls, index_tokens, index_bytes, k, B}`.
  - `langchain-text-splitters` `RecursiveCharacterTextSplitter` is shown beside the course chunker, with its hidden defaults named (chunk_size 4000, `len` = characters, `strip_whitespace=True`; foundation §9.2).
  - The retriever is a plain function over cached vectors; `VectorStoreRetriever`'s k = 4 default is named.
- **External calls:** **none new.** Everything replays from the per-technique runs (I3 sentence embeds, I4/I5/I6 LLM calls, query embeds). The notebook runs in `replay` mode and lists missing keys from `replay_manifest.json`.
- **Tracing:**
  - Local JSONL plus Phoenix (`uvx arize-phoenix@20.19.0 serve`) by default.
  - The run root carries `config_hash`, `index_manifest_hash` and the lineage.
  - Retriever spans carry ranked `chunk_id`s and scores, and the parent id when the returned unit differs.
  - The context span carries tokens, the tokenizer, duplicates removed and k at budget.
- **Dataset and evaluators:** code-based only. CE@4 (fixed k and equal B), Span-Coverage@4, MRR@10, per bucket with n; index cost and size evaluators read from the manifests. No judge (D-10).
- **Experiment vs the previous version:** every arm vs v0 **and** its base champion on identical keys. The v1.4 subset is compared only with the champion rerun on the subset qids.
- **Cost, latency, tokens:** index-time `cost if called` vs `paid` per arm (from `calls.sqlite`); cost per 1k chunks; quota-days; query p50/p95 (unchanged except for the vector count).
- **Prompt and config versioning:** each arm's `config.yaml` plus prompt files (I4 generate/grade, I5 context, I6 questions) are tied to an `experiments/E01x` run. The family register lists every arm tried, which is the multiple-comparison denominator.
- **Monitoring and feedback:**
  - A **family-level regression suite** (T1): for the adopted champion, CE@4 and MRR ≥ champion − tolerance on frozen D with cached embeddings; a per-qid flip list; a **cost regression** (index calls per 1k chunks must not grow more than X% without a new run).
  - The monitor page adds an "arms tried vs adopted" counter and the champion lineage.
  - A failure found in the bake-off goes to the M5 log and then becomes a golden item.
- **Lifecycle:** Measure → Improve (the decision record) → CI (the family regression). Skills: `rag-evaluation`, `evals-foundations`, `ci-cd-evals`, `error-analysis`, `llm-observability`, `improving-llm-agents` (cost).

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Token counts (cl100k, gpt2) | `tiktoken` | 0.14.0 | yes (uv.lock) | yes (cached encodings) | — | MIT | yes |
| Embedder tokenizer, truncation | `sentence-transformers` / `transformers` (MiniLM tokenizer) | 6.1.0 / 5.19.0 | yes | yes | — | Apache-2.0 | yes |
| Parsing, heading spans | `pymupdf` | 1.26.7 (pinned) | yes | yes | — | AGPL-3.0 | yes |
| Tables, charts, statistics | `numpy`, `pandas`, `plotly`, `scipy` | per uv.lock | yes | yes | — | BSD / MIT | yes |
| Holm (optional cross-check) | `statsmodels` `multipletests(method="holm")` | 0.15.0 | no | yes | — | BSD-3 | yes (own 5-line Holm preferred) |
| Splitter comparison (LLMOps only) | `langchain-text-splitters` | 1.1.3 | no | yes | — | MIT | yes, after the mechanism |
| Framework core | `langchain-core` | 1.6.6 | no | yes | — | MIT | yes (D-32) |
| Experiments view | `langsmith` | 0.14.4 | no | SDK yes | free plan; Corpus D only | MIT | yes |
| Local tracing | `arize-phoenix-otel` 0.17.2 + Phoenix server via `uvx` 20.19.0 | — | no | yes | — | Apache-2.0 / ELv2 | yes |
| LLM (I-CMP itself) | none: replay of the I4–I6 runs (Groq `openai/gpt-oss-20b`; Claude Haiku 5.5 for the per-chunk context arm if credits exist, because a whole-document request exceeds the 8K TPM limit) | — | — | replay yes | **0 new calls** | — | yes |
| Embeddings | Cohere `embed-v4.0` (cached); MiniLM fallback | — | cohere yes | replay yes | 0 new calls | — | yes |
| Reference only | `chunking_evaluation` (Chroma) | GitHub main (no release read) | no | — | depends on openai, chromadb, anthropic (README) | UNVERIFIED | **read only** (OpenAI dependency) |

**Install lines (not run):** `uv add --group llmops langchain-core==1.6.6 langchain-text-splitters==1.1.3 langsmith==0.14.4 arize-phoenix-otel==0.17.2`; optional `uv add --group dev statsmodels==0.15.0`. Pins are taken from LLMOPS §11 and phase_03, not re-checked here.
**Keys:** none for the verify notebook or the tool. `LANGSMITH_API_KEY` only to upload the Corpus D experiments.

### 11. Open questions for Yash (preferences only)

- For the transfer exercise, do you want a described corpus (like the HR-handbook example) or one of your own document sets run through the chooser tool? **described / own**
- Should the heat table show numbers only, or colour plus numbers? **numbers / colour**

---

## Phase-level notes

### 1. Ordering problems (not prerequisites; reported, not edited)

- **06's build order works, and one edge is missing.** The order is v1.0 I1 → v1.1 I2 → v1.2 I5 → v1.3 I3 → v1.4 I4, with I6 on a branch. It suits the work, because I5's section-path header is built from I2's heading tree. But neither 02's I5 Pre line nor 03's registry records I5 ← I2 (I-CMP-E8, I5 note). Add it as at least an advice edge.
- **I4 ← I3 is ordering only.** Propositions use recursive token chunks plus LLM calls, not sentence embeddings (I-CMP-E7). The one thing I4 genuinely shares with I3 is the span-preserving sentence splitter.
- **03 row 428 lists only I1 for I2.** 02's Pre line also names C1, so 03 is missing C1 (I2-E1).
- **Each version runs on the previous champion,** so I3's and I4's measured effects depend on which I1, I2 and I5 choices were adopted. The I-CMP table must record the base of every row, or rerun the key arms on v0 too.
- **M4's running example** should use a grid arm (400/40 or 400/80, not 500/100), so its cached index carries straight into v1.0 (I1-E9).

### 2. Shared infrastructure the phase needs (build once)

| Piece | Used by | Where it should live |
|---|---|---|
| `IndexUnit` with `embed_text` (what is embedded) separate from the evidence span (what is scored and cited), plus a `preproc_version` bump whenever `embed_text` changes | I3, I4, I5, I6 | `ragkit` types (06 §2.3) |
| One retriever that removes duplicate parents **before** the top-k cut: `retrieve(q, k, K_vec, agg)`, with max aggregation over children and oversampling | I4, I6, then X3 | `ragkit` retrieval |
| A span-preserving sentence splitter at document scope that records multi-page `page_segments` (24 of 33 Corpus D pages end mid-sentence) | I3, I4, later X2 | `ragkit` chunking |
| A heading tree (`section_path`, level, char offsets) | I2 → I5, later R2 (section filters) and R5 | `ragkit` parsing |
| A cache-key rule for index-time LLM text: prompt version + document hash + chunk text + model, never the chunk text alone | I4, I5, I6 | `llmops.cache` params (LLMOPS §2.3) |
| A `breakpoint_embed_hash` in the chunker `params_hash` for any chunker that depends on embeddings | I3 | C3 manifest |
| Duplicate-arm hashing (configs that produce identical chunks share one result) | I1, I-CMP | the experiment runner |
| An n-gram/embedding leakage check between prompts or generated text and eval items | I4 (first few-shot prompt), I6, then Q1/Q2 | `llmops.datasets` (LLMOPS §4) |

### 3. The cost and quota picture for Corpus D (estimates, not measured)

| Concept | Index-time LLM calls per build | Cohere embed calls | Money | What limits it |
|---|---|---|---|---|
| I1 | 0 for retrieval; about 70 Groq calls for the generation shortlist | about 45 for the whole grid (61% of chunk texts repeat across arms) + 1 query batch | ≈ $0.02 | Groq TPM for the shortlist |
| I2 | 0 | ≤ 16 | ≈ $0 | none |
| I3 | 0 | 8–10 (one vector per sentence window) | ≈ $0 | none |
| I4 | 66 with grading batched per page; ≈ 1,430 with per-proposition grading | a few | ≈ $0.04 batched | per-proposition grading ≈ 8.6 days of Groq free-tier tokens; batched ≈ 1 day |
| I5 | rung 1: 0; rung 2 (chapter window, Groq): 97, ≈ 113K tokens; rung 3 (whole document, Haiku 5.5 cached): 97 | as I1's champion | $0 / ≈ $0.015 / ≈ $0.026 (≈ $0.139 uncached) | rung 3 is blocked on Groq's free tier: ≈ 13K tokens per request > 8K TPM |
| I6 | 97 (n = 5 questions per call) | 4–11 | ≈ $0.015–0.026 Groq; ≈ $0.024–0.042 Haiku | 9–14 min per build; 36–56% of a day's Groq tokens |
| I-CMP | 0 (replay only) | 0 | $0 | none |

Groq limits are the free-tier row in LLMOPS §2.5 (30 RPM, 8K TPM, 200K TPD; the plan is UNVERIFIED). On this corpus **money is never the obstacle; the daily token quota and the per-request TPM are.** Every plan therefore records once and then replays, which is LLMOPS §2.5's resumable-run rule.

### 4. Corrections this phase suggests for `LLMOPS_FOUNDATION.md` (reported, not edited)

- **§6.4** sends contextual headers (I5) to Groq. That works for rungs 1–2, but rung 3 (the whole document per chunk) exceeds 8K TPM per request. Route rung 3 to Haiku 5.5 with prompt caching, or to a paid Groq tier (I5-E4).
- **§9.2** has no rows for `MarkdownHeaderTextSplitter` (`strip_headers=True` rewrites text, keeps no offsets, has no size cap; I2) or `SemanticChunker` (mean + 1.5·IQR rather than the book's Q3 + 1.5·IQR, no maximum size, rejoins sentences with spaces, `start_index` drifts; I3). Also missing: `MultiVectorRetriever` (4 child vectors, first-seen order, scores dropped, can return fewer than k parents; I6) and LlamaIndex's default of embedding all metadata (I5).
- **§9.3 adapter:** `BaseChatModel.with_structured_output` forces `tool_choice="any"`, which returns a 400 on Opus 5.5 and Sonnet 5.5 (LLMOPS §6.4 rule). `CachedChatModel` must override it to use native JSON-schema output (I4).

### 5. Effects on other phases

- **Phase 3 (M1):** before v1.1, add the `crosses_page` and `section_scoped` tags in a new dataset version (I2). Record which model drafted each item in `created_by`, so I6's family-overlap check can be audited (I6). Re-read items that fail under every grid setting before reporting the grid (review row 247).
- **C3:** the manifest needs `breakpoint_embed_hash` (I3) and a `preproc_version` bump for header text (I5). The 8,192-token vs 128k Cohere input limit still needs one recorded value (I1).
- **C5:** multi-page chunks need a citation rule: first page, or every segment (I2). Whether the generator sees the header is a C5/X3 decision, not an I5 one.
- **R1 (v2.0):** it inherits a `bm25_text` field, and "contextual BM25" is tested there, not in v1.2. A title term that appears in every chunk gets idf ≤ 0 and then hits rank_bm25's floor (I5). Questions appended to BM25 text (doc2query style) are a natural hybrid arm (I6).
- **R2:** `section_path` gives section-scoped metadata filters (I2).
- **R5:** test RAPTOR against section summaries, not only against flat chunks (I-CMP).
- **Q2 (v3.1):** reuse I6's leakage guard and decisive slice, since HyDE passages can paraphrase gold spans too. Read I6's cached results instead of regenerating them. HyDE's target length equals the I1 champion's size (I1, Ch6 p.9–10/14 per 04).
- **X1 / X3:** windows and overlap count the same text twice, so report unique characters. X3 owns the deduplication that I1's `dup_frac` measures, and the removal of duplicate parents from I4 and I6.
- **S1:** entity extraction at index time reuses I4's calls-per-page cost model (the 03 advice edge).
- **K1:** the I-CMP table is K1's main evidence for the chunker choice. Corpus H stays untouched until then, and is the transfer test for I2's heading rules.

### 6. Points where helpers disagreed, and how they were settled

- **Corpus D heading sizes.** I5's poppler run printed 36/27/20/18 pt; I2's raw-PDF reading gave 24/18/13.56/12 pt. The heading counts were identical. `pdftohtml` renders at its default 1.5× zoom, so I2's values are the true ones, and the I5 section has been corrected.
- **I4's cost on all of Corpus D.** I-CMP assumed about 10 propositions per 200-token chunk (≈ 1,056 calls). I4 counted ≈ 620 sentences and used Dense X's ratio (≈ 1,400 propositions). I4 §5 is authoritative; I-CMP's table carries a note.
- **Embedding reuse across I1 arms.** The brief told helpers reuse was impossible; I1 measured that about 61% of chunk texts repeat across configurations, so the content-keyed cache saves about 46% of embed calls. I1 is right; the brief was wrong.

---

## Sources

Numbered per concept; inline keys such as **[I3-S2]** point here. "Verified" means the page, README or source file was opened in this session and the fact checked on it. "UNVERIFIED (search-checked only)" means only web-search summaries were seen, because the host was blocked from this cloud session. Book pages are not listed: none was opened in this session (see the header).

### I1 sources

1. Chroma `chunking_evaluation`, Brandon Smith, 2024, https://github.com/brandonstarxel/chunking_evaluation (`main` @ `e708410`; README, `setup.py`, `LICENSE`, `chunking_evaluation/evaluation_framework/base_evaluation.py`) — **verified (opened via raw.githubusercontent.com)**.
2. "Evaluating Chunking Strategies for Retrieval", Brandon Smith & Anton Troynikov, Chroma, 2024, https://research.trychroma.com/evaluating-chunking — **UNVERIFIED** (DNS blocked here; numbers carried from phase_02 [C2-4]).
3. "Rethinking Chunk Size For Long-Document Retrieval: A Multi-Dataset Analysis", Sinchana Ramakanth Bhat, Max Rudat, Jannis Spiekermann, Nicolas Flores-Herr, 2025, https://arxiv.org/abs/2505.21700 — **UNVERIFIED (search-checked only)**. Code repo https://github.com/fraunhofer-iais/chunking-strategies (HEAD `d5fa14c`) — **verified (README opened; no results in it)**.
4. "Finding the Best Chunking Strategy for Accurate AI Responses", NVIDIA Technical Blog, 2024 or 2025 (date disputed), https://developer.nvidia.com/blog/finding-the-best-chunking-strategy-for-accurate-ai-responses/ — **UNVERIFIED (search-checked only; vendor)**.
5. LangChain `langchain-text-splitters==1.1.3` (`base.py` L64–L69, L282–L284; `character.py` L101, L107), tag commit `e2db474`, https://github.com/langchain-ai/langchain/tree/langchain-text-splitters==1.1.3/libs/text-splitters — **verified (opened via raw.githubusercontent.com)**.
6. LlamaIndex `llama-index-core` v0.14.25 (`node_parser/text/sentence.py` L22, L24, L83, L104; `constants.py` L10–L11), tag commit `f12d46a`, https://github.com/run-llama/llama_index/tree/v0.14.25 — **verified (opened via raw.githubusercontent.com)**.
7. Cohere embed-v4.0 limits: Cohere docs (https://docs.cohere.com/reference/embed, https://docs.cohere.com/docs/cohere-embed) per phase_02 [C3-1/C3-2], verified there on 2026-10-17. Oracle OCI (https://docs.oracle.com/en-us/iaas/Content/generative-ai/cohere-embed-4.htm) and AWS Bedrock (https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-embed-v4.html) — **UNVERIFIED (search-checked only)**.
8. "On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation", Gavin C. Cawley & Nicola L. C. Talbot, JMLR 11 (2010) 2079–2107, https://www.jmlr.org/papers/v11/cawley10a.html — **UNVERIFIED (search-checked only)**.
9. tiktoken 0.14.0 `tiktoken_ext/openai_public.py` (L123–L125 `o200k_harmony`; L161 registry), https://github.com/openai/tiktoken/blob/0.14.0/tiktoken_ext/openai_public.py — **verified (opened via raw.githubusercontent.com)**.
10. The one-standard-error rule: Breiman, Friedman, Olshen & Stone, *Classification and Regression Trees*, 1984; Hastie, Tibshirani & Friedman, *The Elements of Statistical Learning*, 2nd ed., 2009 — **UNVERIFIED (not found/opened; cited from general knowledge)**.
11. AI-Engineer-Interview-Questions, Om (ombharatiya), 2026, MIT, `04-rag-and-retrieval/questions.md` Q4, Q5 (L103–L137), Q33 (L833–L855), Q43, https://github.com/ombharatiya/AI-Engineer-Interview-Questions @ `e080df2` — **verified (opened via raw.githubusercontent.com)**.
12. NirDiamant/RAG_Techniques @ `009adba`, `all_rag_techniques/choose_chunk_size.ipynb` (cells 0–13) and `all_rag_techniques_runnable_scripts/choose_chunk_size.py` (L1–L141), plus `data/Understanding_Climate_Change.pdf` (sha256 `1d58a0fa…92669`), custom non-commercial licence — **verified (opened via raw.githubusercontent.com; code not run)**.
13. Lost in the Middle (Liu et al. 2023, arXiv 2307.03172; Source C #39) — link only, **not opened** (X3/P7 own it).

### I2 sources

1. PyMuPDF 1.26.7 `src/__init__.py` (Artifex), 2025, https://raw.githubusercontent.com/pymupdf/PyMuPDF/1.26.7/src/__init__.py — verified (opened raw at tag `1.26.7`; lines cited).
2. pymupdf4llm 0.2.9 wheel and PyPI JSON for all versions (Artifex), 2026, https://pypi.org/pypi/pymupdf4llm/json — verified (wheel unpacked; `requires_dist` read per version).
3. langchain-text-splitters 1.1.3 wheel (LangChain), 2026-10-02, https://pypi.org/project/langchain-text-splitters/1.1.3/ — verified (`markdown.py`, `character.py`, `base.py`, `html.py` read).
4. unstructured 0.27.10 wheel (Unstructured), 2026-09-27, https://pypi.org/project/unstructured/0.27.10/ — verified (`chunking/base.py`, `chunking/title.py` read).
5. docling-core 2.99.0 wheel; docling 2.133.0 / docling-slim 2.133.0 PyPI metadata; docling README (Deep Search Team, IBM), 2026, https://pypi.org/project/docling-core/2.99.0/ , https://raw.githubusercontent.com/docling-project/docling/main/README.md — verified (wheel source, metadata, GitHub README).
6. Docling Technical Report, Deep Search Team (IBM Research), 2024, https://arxiv.org/abs/2408.09869 — UNVERIFIED (search-checked only; existence and citation verified via the GitHub README).
7. Financial Report Chunking for Effective Retrieval Augmented Generation, A. Jimeno Yepes, Y. You, J. Milczek, S. Laverde, R. Li, 2024, https://arxiv.org/abs/2402.05131 — UNVERIFIED (search-checked only).
8. Finding the Best Chunking Strategy for Accurate AI Responses, NVIDIA Technical Blog (author per search: S. Han), date UNVERIFIED (2024–2025), https://developer.nvidia.com/blog/finding-the-best-chunking-strategy-for-accurate-ai-responses/ — UNVERIFIED (search-checked only; DNS blocked).
9. A Systematic Investigation of Document Chunking Strategies and Embedding Sensitivity, M. A. Shaukat, M. Adnan, C. C. N. Kuhn, 2026, https://arxiv.org/abs/2603.06976 — UNVERIFIED (search-checked only).
10. Evaluating Chunking Strategies For Retrieval-Augmented Generation in Oil and Gas Enterprise Documents, authors not confirmed, 2026, https://arxiv.org/abs/2603.24556 — UNVERIFIED (search-checked only).
11. Evaluating document chunking approaches for retrieval augmented generation in editorial content, Lavarec and Du, IAES IJAI, year UNVERIFIED, https://ijai.iaescore.com/index.php/IJAI/article/view/30378 — UNVERIFIED (search-checked only).
12. Long-Context Isn't All You Need: Impact of Retrieval and Chunking on Finance RAG, Snowflake engineering blog (author not confirmed), 2025-03-11, https://www.snowflake.com/en/engineering-blog/impact-retrieval-chunking-finance-rag/ — UNVERIFIED (search-checked only; DNS blocked).
13. Empirical Evaluation of PDF Parsing and Chunking for Financial Question Answering with RAG, authors not confirmed, 2026, https://arxiv.org/abs/2604.12047 — UNVERIFIED (search-checked only).
14. AI-Engineer-Interview-Questions `04-rag-and-retrieval/questions.md` Q4, Q13, Q14, Om Bharatiya, 2026 (MIT), https://raw.githubusercontent.com/ombharatiya/AI-Engineer-Interview-Questions/e080df2/04-rag-and-retrieval/questions.md — verified (opened raw).
15. chonkie 1.7.0 wheel (Chonkie), 2026, https://pypi.org/project/chonkie/1.7.0/ — verified (wheel listing and `types/base.py`).
16. NirDiamant/RAG_Techniques @ `009adba2…`: `simple_rag.ipynb` cell 10, `helper_functions.py` L48–L76, `hierarchical_indices.ipynb` cell 11, README, `data/Understanding_Climate_Change.pdf` — verified (raw download; cells read with `json`, 0-based).
17. Corpus D raw-structure inspection, own stdlib scripts (zlib + regex over content streams; no PyMuPDF), 2026-10-17, scripts `pdfpeek.py`, `pdfpeek2.py`, `pdfpages.py` and a per-page heading map, kept in the session scratchpad only — verified locally (approximate; recount with PyMuPDF in the verify notebook).

### I3 sources

1. **[I3-S1]** NirDiamant, *RAG_Techniques*, `all_rag_techniques/semantic_chunking.ipynb` @ `009adba2be1bef49780ef73b6dd3c18fd24b035b`. https://raw.githubusercontent.com/NirDiamant/RAG_Techniques/009adba2be1bef49780ef73b6dd3c18fd24b035b/all_rag_techniques/semantic_chunking.ipynb. Verified (opened with curl; cells read with `json`).
2. **[I3-S2]** Same repo, `all_rag_techniques_runnable_scripts/semantic_chunking.py` and `helper_functions.py` (L223–L245) @ `009adba`. Verified (curl).
3. **[I3-S3]** LangChain, `langchain-experimental` 0.4.2, `langchain_experimental/text_splitter.py` (2026-05-22). PyPI wheel sha256 `fd98b9948cb6f991e0f632ea3d5fb839bcfe21e6d5a190a51126a76270a66d40`, identical to tag `libs/experimental/v0.4.2` and `main`. https://raw.githubusercontent.com/langchain-ai/langchain-experimental/libs/experimental/v0.4.2/libs/experimental/langchain_experimental/text_splitter.py. Verified (wheel and GitHub raw, diffed).
4. **[I3-S4]** LangChain, `langchain-community` 0.4.2, `langchain_community/utils/math.py`. https://raw.githubusercontent.com/langchain-ai/langchain-community/libs/community/v0.4.2/libs/community/langchain_community/utils/math.py. Verified (GitHub raw).
5. **[I3-S5]** LlamaIndex, `llama-index-core` v0.14.25, `node_parser/text/semantic_splitter.py` and `node_parser/text/utils.py`. https://raw.githubusercontent.com/run-llama/llama_index/v0.14.25/llama-index-core/llama_index/core/node_parser/text/semantic_splitter.py. Verified (GitHub raw).
6. **[I3-S6]** chonkie-inc, `chonkie` v1.7.0, `src/chonkie/chunker/semantic.py`. https://raw.githubusercontent.com/chonkie-inc/chonkie/v1.7.0/src/chonkie/chunker/semantic.py. Verified (GitHub raw).
7. **[I3-S7]** G. Kamradt, "5 Levels of Text Splitting" (2024), `FullStackRetrieval-com/RetrievalTutorials`, `tutorials/LevelsOfTextSplitting/5_Levels_Of_Text_Splitting.ipynb` (main, fetched 2026-10-17), cells 77–107. https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/tutorials/LevelsOfTextSplitting/5_Levels_Of_Text_Splitting.ipynb. Verified (GitHub raw).
8. **[I3-S8]** B. Smith, `brandonstarxel/chunking_evaluation`: `README.md`, `chunking/kamradt_modified_chunker.py`, `chunking/cluster_semantic_chunker.py` (main, fetched 2026-10-17). https://github.com/brandonstarxel/chunking_evaluation. Verified (GitHub raw; code only, no results files in the repo).
9. **[I3-S9]** B. Smith and A. Troynikov, "Evaluating Chunking Strategies for Retrieval", Chroma Technical Report, 2024. https://research.trychroma.com/evaluating-chunking. UNVERIFIED (search-checked only; host blocked; authors from memory).
10. **[I3-S10]** R. Qu, R. Tu, F. S. Bao, "Is Semantic Chunking Worth the Computational Cost?", arXiv 2410.13070 (2024); Findings of NAACL 2025. https://arxiv.org/abs/2410.13070 ; https://aclanthology.org/2025.findings-naacl.114/. UNVERIFIED (search-checked only; arXiv, ACL and Vectara blocked).
11. **[I3-S11]** N. Sadvilkar and M. Neumann, "PySBD: Pragmatic Sentence Boundary Disambiguation", NLP-OSS 2020; `nipunsadvilkar/pySBD` README. https://github.com/nipunsadvilkar/pySBD. Verified (GitHub README).
12. **[I3-S12]** Om (ombharatiya), *AI-Engineer-Interview-Questions* @ `e080df2`, `04-rag-and-retrieval/questions.md` Q4. MIT, "Copyright (c) 2026 Om". https://github.com/ombharatiya/AI-Engineer-Interview-Questions. Verified (GitHub raw).
13. **[I3-S13]** ombharatiya, *ai-system-design-guide* @ `ed955b2`, `06-retrieval-systems/02-chunking-strategies.md`. MIT. https://github.com/ombharatiya/ai-system-design-guide. Verified (GitHub raw).
14. **[I3-S14]** Cohere, Python SDK 7.2.0, `cohere/types/embed_input_type.py` (includes `clustering`). https://pypi.org/project/cohere/7.2.0/. Verified (PyPI wheel).
15. **[I3-S15]** PyPI JSON for `langchain-experimental`, `langchain-community`, `langchain-classic`, `llama-index-core`, `chonkie`, `pysbd`, `nltk`, `spacy`, plus a `uv pip compile` resolution (`--exclude-newer 2026-10-03`, nothing installed). https://pypi.org/pypi/langchain-experimental/json. Verified (curl, 2026-10-17).
16. **[I3-S16]** Vendor benchmark summaries (premai.io "RAG Chunking Strategies: The 2026 Benchmark Guide"; firecrawl.dev "Best Chunking Strategies for RAG"). UNVERIFIED (search-checked only).
17. **[I3-S17]** arXiv 2606.00881 ("Chunking Methods on Retrieval-Augmented Generation – Effectiveness Evaluation Against Computational Cost and Limitations") and arXiv 2608.00824 ("Structure-Aware Semantic Chunking with Title-Chain Prefixes…"). UNVERIFIED (titles from search only).

### I4 sources

1. **[I4-S1]** *Dense X Retrieval: What Retrieval Granularity Should We Use?* T. Chen, H. Wang, S. Chen, W. Yu, K. Ma, X. Zhao, H. Zhang, D. Yu. EMNLP 2024 (arXiv 2023). https://arxiv.org/abs/2312.06648. **UNVERIFIED (search-checked only)**: Recall@20 +10.1 / +2.7, word-budget result, EM@500 +2.8 (secondary).
2. **[I4-S2]** chentong0/factoid-wiki README and LICENSE (`main`, read 2026-10-17). https://github.com/chentong0/factoid-wiki. **verified (opened raw GitHub README and LICENSE)**: unit counts 41M/114M/257M; propositionizer usage; Apache-2.0.
3. **[I4-S3]** `chentong00/propositionizer-wiki-flan-t5-large` model page. https://huggingface.co/chentong00/propositionizer-wiki-flan-t5-large. **UNVERIFIED (search-checked only)**: 3.13 GB safetensors; licence not found.
4. **[I4-S4]** LangChain `templates/propositional-retrieval` (proposal_chain.py, ingest.py, storage.py, chain.py, README) at tag `langchain==0.2.0`. https://github.com/langchain-ai/langchain/tree/langchain%3D%3D0.2.0/templates/propositional-retrieval. **verified (opened raw GitHub files)**; absent on `master`.
5. **[I4-S5]** `MultiVectorRetriever`, langchain-classic 1.0.8, `libs/langchain/langchain_classic/retrievers/multi_vector.py` L57, L105–113. **verified (opened raw GitHub at tag `langchain-classic==1.0.8`)**.
6. **[I4-S6]** `BaseChatModel.with_structured_output`, langchain-core 1.6.6, `libs/core/langchain_core/language_models/chat_models.py` L2385, L2536–2556 (`tool_choice="any"`). **verified (opened raw GitHub at tag `langchain-core==1.6.6`)**.
7. **[I4-S7]** `TextSplitter.from_tiktoken_encoder`, langchain-text-splitters 1.1.3, `base.py` L282–284 (`encoding_name="gpt2"`). **verified (opened raw GitHub at tag)**.
8. **[I4-S8]** *FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation.* S. Min, K. Krishna, X. Lyu, M. Lewis, W. Yih, P. W. Koh, M. Iyyer, L. Zettlemoyer, H. Hajishirzi. EMNLP 2023. https://github.com/shmsw25/FActScore (README; `factscore/atomic_facts.py` L96–125). **verified (opened raw GitHub `main`)**.
9. **[I4-S9]** *Beyond Chunk-Then-Embed: A Comprehensive Taxonomy and Evaluation of Document Chunking Strategies for Information Retrieval.* Y. Zhou, S. Wang, B. Koopman, G. Zuccon. 2026. https://arxiv.org/abs/2602.16974. **UNVERIFIED (search-checked only)**; the numbers come from search summaries.
10. **[I4-S10]** *LumberChunker: Long-Form Narrative Document Segmentation.* A. V. Duarte et al. 2024. Seen only through a search-result summary (https://liner.com/review/lumberchunker-longform-narrative-document-segmentation); the primary URL was not found. **UNVERIFIED (search-checked only)**.
11. **[I4-S11]** Groq docs, Structured Outputs. https://console.groq.com/docs/structured-outputs, plus Groq community threads (https://community.groq.com/t/i-am-receiving-400-gpt-oss-20b-structured-output/941) and the HF forum (https://discuss.huggingface.co/t/groq-route-intermittently-returns-json-validate-failed-with-strict-structured-outputs/179097). **UNVERIFIED (search-checked only; console.groq.com blocked)**.
12. **[I4-S12]** Groq docs, Deprecations (`llama-3.1-70b-versatile` retired; replacement `llama-3.3-70b-versatile`, itself shut down 2026-08-16 per search). https://console.groq.com/docs/deprecations. **UNVERIFIED (search-checked only)**.
13. **[I4-S13]** claude-api skill, cached 2026-10-06: `shared/tool-use-concepts.md` §Structured Outputs (Haiku 5.5 supported; no numeric or length constraints; works with Batches); `shared/prompt-caching.md` (Haiku 5.5 minimum prefix 512 tokens, "check the docs"); model table ($0.10 / $0.50). **verified (skill files read)**.
14. **[I4-S14]** NirDiamant/RAG_Techniques `all_rag_techniques/proposition_chunking.ipynb` @ `009adba2be1bef49780ef73b6dd3c18fd24b035b` (custom non-commercial licence; short snippets only). **verified (downloaded; cells read with python -I)**.
15. **[I4-S15]** ombharatiya/AI-Engineer-Interview-Questions @ `e080df2`, `04-rag-and-retrieval/questions.md` Q4, Q5, Q17. MIT, Copyright (c) 2026 Om. **verified (opened raw GitHub)**.

### I5 sources

1. [I5-S1] Anthropic, "Introducing Contextual Retrieval", 2024-09-19. https://www.anthropic.com/news/contextual-retrieval. **verified** (opened with WebFetch).
2. [I5-S2] Anthropic, "Enhancing RAG with Contextual Retrieval" (cookbook guide), `anthropics/claude-cookbooks` @ `a162e0184e71b60290808a43961a6cbc8060123c`, `capabilities/contextual-embeddings/guide.ipynb`, MIT. https://github.com/anthropics/claude-cookbooks/blob/main/capabilities/contextual-embeddings/guide.ipynb. **verified** (downloaded; all 33 cells read).
3. [I5-S3] D-Star AI, dsRAG README and `dsrag/auto_context.py`, @ `5215e9791133fc1ad383af043fb2fde0e7d4e4d4`, MIT (© 2024 D-Star). https://github.com/D-Star-AI/dsRAG. **verified** (raw files read).
4. [I5-S4] Günther, Mohr, Williams, Wang, Xiao, "Late Chunking: Contextual Chunk Embeddings Using Long-Context Embedding Models", 2024, arXiv 2409.04701; repo README @ `1d3bb02`. https://github.com/jina-ai/late-chunking. **verified (GitHub README)**; paper not opened.
5. [I5-S5] Merola & Singh, "Reconstructing Context: Evaluating Advanced Chunking Strategies for Retrieval-Augmented Generation", 2025, arXiv 2504.19754. https://arxiv.org/abs/2504.19754. **UNVERIFIED (search-checked only)**.
6. [I5-S6] Groq, "Prompt caching" docs. https://console.groq.com/docs/prompt-caching. **UNVERIFIED (search-checked only)**.
7. [I5-S7] Anthropic prompt-caching facts (minimum prefix per model, TTL, multipliers, Haiku 5.5 prices, sampling rules), `claude-api` skill, cache dated 2026-10-06. **verified** (skill file read; the skill itself says to confirm Haiku 5.5's 512-token minimum in the live docs).
8. [I5-S8] LlamaIndex `llama-index-core` v0.14.25, `schema.py` (L66–67, L242–245, L294–301) and `extractors/document_context.py` (L44–53, L104–113, L176–210, L268–285). https://github.com/run-llama/llama_index/tree/v0.14.25. **verified** (raw files read).
9. [I5-S9] NirDiamant/RAG_Techniques `all_rag_techniques/contextual_chunk_headers.ipynb` @ `009adba2be1bef49780ef73b6dd3c18fd24b035b` (custom non-commercial licence). **verified** (downloaded; cells 0–16 read).
10. [I5-S10] Om, AI-Engineer-Interview-Questions, `04-rag-and-retrieval/questions.md` Q17 @ `e080df2`, MIT (© 2026 Om). **verified** (raw file read).
11. [I5-S11] ai-system-design-guide `06-retrieval-systems/10-contextual-retrieval.md` @ `ed955b2`, MIT. **verified (opened)**; used as a pointer only; its numbers are unsourced.
12. [I5-S12] Cohere Rerank model list / deprecations (rerank-v4.0-pro/fast latest; rerank-english-v3.0 still listed). https://docs.cohere.com/v2/docs/rerank. **UNVERIFIED (search-checked only)**.
13. Corpus D structure measurement: `Understanding_Climate_Change.pdf` @ upstream `009adba` (sha256 `1d58a0fa…92669`) via poppler `pdftohtml -xml` / `pdftotext`; script `headers_scan.py`, kept in the session scratchpad only. **verified (scratch run)**; must be re-measured with PyMuPDF.

### I6 sources

1. [I6-S1] Nogueira, Yang, Lin, Cho, "Document Expansion by Query Prediction" (doc2query), 2019, arXiv 1904.08375. Repo https://github.com/nyu-dl/dl4ir-doc2query. **Verified (opened GitHub README via raw.githubusercontent.com):** 5 predicted queries per document; appended to the passage text; BM25/Anserini; re-ranking leaderboard 36.8 eval MRR@10. The paper itself was not opened.
2. [I6-S2] Nogueira, Lin, "From doc2query to docTTTTTquery", 2019. https://github.com/castorini/docTTTTTquery. **Verified (opened GitHub README):** MRR@10 27.2 (eval) at 64 ms vs BM25 18.6 at 55 ms and doc2query 21.8; 80 sampled queries per passage, first 40 used ("tiny gain" from 80); dev reproduction 0.2768; about 8 TPU hours (about $20) per sample pass.
3. [I6-S3] Gospodinov, MacAvaney, Macdonald, "Doc2Query--: When Less is More", ECIR 2023 (LNCS, pp. 414–422), arXiv 2301.03266. Method **verified (opened GitHub README `terrierteam/pyterrier_doc2query`)**: `QueryScorer` (ELECTRA) + `QueryFilter` at the 70th-percentile threshold, `num_samples=5`. The numbers (up to +16% effectiveness, −30% query time, −48% index size, ECIR version) are **UNVERIFIED (search-checked only)**.
4. [I6-S4] Vake, Vičič, Tošić, "Bridging the Question-Answer Gap in Retrieval-Augmented Generation: Hypothetical Prompt Embeddings", IEEE Access 13 (2025), pp. 129952–129961, DOI 10.1109/ACCESS.2025.3589499; SSRN 5139335 (notebook cell 0); arXiv 2607.29402 listing. **UNVERIFIED (search-checked only; arxiv.org, alphaxiv and the university pages were unreachable).**
5. [I6-S5] Gao, Ma, Lin, Callan, "Precise Zero-Shot Dense Retrieval without Relevance Labels" (HyDE), 2022, arXiv 2212.10496 (Source C #32). https://github.com/texttron/hyde. **Verified (opened GitHub README)** for the method only.
6. [I6-S6] LangChain `MultiVectorRetriever`, `libs/langchain/langchain_classic/retrievers/multi_vector.py` at tag `langchain-classic==1.0.8` (L45–L113); defaults in `langchain_core/vectorstores/base.py` L361–L362 and `stores.py` L244 at `langchain-core==1.6.6`. https://github.com/langchain-ai/langchain. **Verified (opened source via raw.githubusercontent.com).**
7. [I6-S7] LlamaIndex `QuestionsAnsweredExtractor`, `llama-index-core/llama_index/core/extractors/metadata_extractors.py` at `v0.14.25` (L253–L334). https://github.com/run-llama/llama_index. **Verified (opened source).**
8. Upstream `NirDiamant/RAG_Techniques` @ `009adba2be1bef49780ef73b6dd3c18fd24b035b`: `all_rag_techniques/document_augmentation.ipynb`, `all_rag_techniques/HyPE_Hypothetical_Prompt_Embeddings.ipynb`, `all_rag_techniques_runnable_scripts/document_augmentation.py`, `all_rag_techniques_runnable_scripts/HyPE_Hypothetical_Prompt_Embeddings.py`, `helper_functions.py`. **Verified (downloaded, cells read, `ast`-parsed).** Custom non-commercial licence; only short snippets are quoted.
9. AIQ `ombharatiya/AI-Engineer-Interview-Questions` @ e080df2, `04-rag-and-retrieval/questions.md` Q5, Q26, Q33, Q45 (MIT, "Copyright (c) 2026 Om"). **Verified (opened raw file).** SDG `ombharatiya/ai-system-design-guide` @ ed955b2, `06-retrieval-systems/09-advanced-retrieval-patterns.md` (MIT). **Verified (opened raw file).**
10. PyPI JSON for `langchain-classic`, `langchain-core` and `llama-index-core` (versions and upload dates). **Verified (curl, 2026-10-17).**

### I-CMP sources

1. Smith, B. & Troynikov, A., "Evaluating Chunking Strategies for Retrieval", Chroma technical report, 2024. https://research.trychroma.com/evaluating-chunking. UNVERIFIED (search-checked only; host blocked). Numbers in §5.2 come from secondary summaries.
2. brandonstarxel/chunking_evaluation (Chroma's code): README, `evaluation_framework/base_evaluation.py`, `general_evaluation.py`, `general_evaluation_data/questions_df.csv`. https://github.com/brandonstarxel/chunking_evaluation. Verified (opened via raw.githubusercontent.com, main branch, 2026-10-17; 472 queries over 5 corpora counted; metric code read).
3. Qu, R., Tu, R. & Bao, F., "Is Semantic Chunking Worth the Computational Cost?", arXiv 2410.13070 (2024); Findings of NAACL 2025. https://aclanthology.org/2025.findings-naacl.114/. UNVERIFIED (search-checked only).
4. NVIDIA Developer Blog, "Finding the Best Chunking Strategy for Accurate AI Responses" (2025 per search). https://developer.nvidia.com/blog/finding-the-best-chunking-strategy-for-accurate-ai-responses/. UNVERIFIED (search-checked only; host blocked).
5. Merola, C. & Singh, J., "Reconstructing Context: Evaluating Advanced Chunking Strategies for Retrieval-Augmented Generation", arXiv 2504.19754, 2025 (ECIR 2025 workshop). https://arxiv.org/abs/2504.19754. UNVERIFIED (search-checked only).
6. Lu, W., Chen, K. et al., "HiChunk: Evaluating and Enhancing Retrieval-Augmented Generation with Hierarchical Chunking", arXiv 2509.11552, 2025; ACL 2026. README at https://github.com/TencentCloudADP/HiChunk. Verified (GitHub README opened via raw.githubusercontent.com: fixed 4,096-token context in the eval commands); paper results UNVERIFIED.
7. Anthropic, "Introducing Contextual Retrieval", 2024. https://www.anthropic.com/news/contextual-retrieval. Verified (opened with WebFetch, 2026-10-17).
8. ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md` Q4, Q5 (MIT, © 2026 Om). Verified (opened via raw.githubusercontent.com).
9. NirDiamant/RAG_Techniques @ 009adba2be1bef49780ef73b6dd3c18fd24b035b: `all_rag_techniques/{simple_rag, choose_chunk_size, semantic_chunking, proposition_chunking, contextual_chunk_headers, document_augmentation, HyPE_Hypothetical_Prompt_Embeddings}.ipynb`, `helper_functions.py` (custom non-commercial licence). Verified (downloaded; cells read 0-based).
10. ombharatiya/ai-system-design-guide @ ed955b2, `06-retrieval-systems/02-chunking-strategies.md` (MIT). Verified (opened; headings only, not used for claims).
