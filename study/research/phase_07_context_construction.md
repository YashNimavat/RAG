# Phase 7 research: Context construction

**What this is:** the research and gap audit for Phase 7 (X1, X2, X3), done 2026-10-18 by Claude (Sonnet 5.5).
**What this is not:** lessons or code. Nothing in the course was changed, nothing was installed, and no API was called.

**How much could be checked in this session.** Read this before trusting any citation.
- **Not in this checkout:** `CLAUDE.md`, `.claude/skills/`, `upstream/` (the two MIT repos and the interview guide), the book PDFs and the AI Eval book. So **every book page and every repo-notebook cell below is copied from 02, 03, 04 and 01 and is UNVERIFIED here.** No book text was read, so no book wording can have been copied.
- **Blocked by the network policy:** `arxiv.org`, the ACL Anthology, `docs.langchain.com`, `console.groq.com`, Hugging Face. I did not try to get around it. **Every paper below was read only through search-result snippets and is UNVERIFIED** unless a library README or course file quotes it.
- **Opened and checked:** the source code of LangChain (`langchain-classic`, `langchain-core`, `langchain-text-splitters`), LlamaIndex (`sentence_window.py`, `metadata_replacement.py`), dsRAG (`rse.py`), the LLMLingua README; Anthropic's prompting, citations, search-results and contextual-retrieval pages; the PyPI JSON for every package; all the course files listed in the sources.
- **Project skills** (`evals-foundations`, `rag-evaluation`, …) were not on disk. I used their names and methods as `LLMOPS_FOUNDATION.md` states them.
- **Numbers marked "derived"** are hand arithmetic from course facts (for example 1,000-character chunks, 200 overlap, 5.57 characters per token). They are not measurements.

---

## Summary (read this first)

**The 5 most important gaps across the phase**
1. **Nothing in the course yet teaches how text is addressed by document offsets.** X1 and X3 both depend on it: neighbour merging, dedup, and "CE on the final context" are all interval arithmetic. The upstream notebook merges by string-trimming an overlap count (a wrong default silently duplicates text, DV-22). The course snapshot already stores document offsets (06 §2.3), so the merge can be exact. The prerequisites for this (C2 chunking, C3 `seq`/offsets, I1 overlap) are all **not started**.
2. **"Equal token budget" is mandatory (06) but never defined for windows.** By derived arithmetic, a ±1 window is about 2.6× the tokens of one chunk (467 vs 180) and ±2 about 4.2×. At an equal budget, the ±1 arm can keep only about 1–2 of the four hits. So the claim "top-k retrieval metrics are unchanged" is true, but "CE on the final context" can fall. The arm needs a written fill procedure before anyone runs it.
3. **X3 has no source at all** (no book chapter, no notebook, only fragments). Its one outside anchor, "lost in the middle", was measured on long contexts of 2023-era models. The v0 context is about 700–800 tokens at k = 4, where there is hardly a "middle". An ordering ablation at k = 4 is therefore expected to show nothing. It needs a larger-k arm (for example k = 10) to have any chance of showing an effect.
4. **Compression can only be scored by CE if the extract is verbatim and can be mapped back to document offsets.** LangChain's `LLMChainExtractor` asks for "AS IS" text in the prompt but never checks it (source read). Abstractive summaries cannot be CE-scored at all, only labelled by hand. X2 therefore needs a verbatim check and an offset re-alignment step, and a plain non-LLM extractor as the baseline.
5. **Citation labels and the prompt contract break at Phase 7.** C5 labels a block `[doc:page]` using the chunk's *first* page, and its record says "prompt order = rank order". A merged window can span two pages, and X3 ordering separates *rank* from *position*. Both C5 contracts and V1's citation check (Phase 8) must change. This crosses into Phases 2 and 8.

**Also worth knowing**
- RSE (relevant segment extraction) needs a *score for every chunk* of a document. On our 97-chunk corpus, the cosine scores for all 97 chunks already come out of C4's `V @ q` for free. No rerank call is needed, but the repo's constants assume a Cohere rerank scale, so they must be re-tuned on the dev split.
- X2 with one LLM call per chunk is about 220 calls per run (55 questions × k = 4). By my estimate that is about 158K tokens: roughly 79% of Groq's listed daily token quota (plan UNVERIFIED), at least 20 minutes at 8K tokens/min. A batched call (one per question) is about 94K tokens.

**Tools to add, across the phase** (details in each concept's §10)
- **Nothing is required for the lessons and verify notebooks.** `tiktoken`, `numpy`, `pandas`, `plotly`, `rank-bm25`, `sentence-transformers` are installed. A small regex sentence splitter, written in the course, replaces a library.
- **`langchain-core` 1.6.6** (from the foundation): for the LLMOps notebooks. It already contains `BaseDocumentCompressor`, `Document` and `RunnableLambda`, so **`langchain-classic` is not needed**: read its `LLMChainExtractor` source, do not install it.
- **Not recommended:** `llmlingua` (last release 2024-04, needs torch, transformers, accelerate, nltk), `llama-index-core` (many dependencies), `dsrag`. Read their source only.
- **Optional:** `scipy` or `rapidfuzz` only if `numpy` and `difflib` prove too slow or too crude for the paired bootstrap and the fuzzy verbatim match.

**Decisions Yash must make** (each answerable in a word)
1. X2's LLM arm: **per-chunk** calls, **batched** (one call per question, recommended), or **non-LLM only** first?
2. Include RSE as an X1 arm using free cosine scores (no API)? **Yes** is recommended.
3. Run the ordering ablation also at a larger k (for example 10), because k = 4 is expected to be a null? **Yes** is recommended.
4. LLMLingua-style token pruning: **skip** (recommended) or read-only?
5. Claude's native Citations feature as an alternative to the course's `[doc:page]` labels: **defer** to Phase 8 (recommended), or include now?

**Size of the build work** (S / M / L)
- **X1: M.** The mechanism is small (interval merge), but it needs the straddle audit, the equal-budget procedure and the RSE arm.
- **X2: M.** Four compressors (two non-LLM, one LLM, one batched), the verbatim and alignment check, and rate-limit planning. The LLM calls dominate the work.
- **X3: L.** No source to lean on. It needs the assembler, three policies (dedup, order, budget), the label scheme, and changes to the C5 contract. It is the shared base that X1 and X2 plug into.

---

## Concept X1: Context enrichment window and relevant segment extraction

### 1. Sources checked

**Book pages (cited from 02/04/01; UNVERIFIED here, the book is not in this checkout)**
- Ch8 p.4/11–p.5/11 (position metadata, retrieve, expand), p.5/11 (concatenate with overlap awareness), p.6/11 (sketch), p.7/11 (window size, versus headers), p.8/11–p.10/11 (when to use), p.10/11–p.11/11 (key takeaways) (01 §contents row; 02 X1; 04 §Ch8).
- 01 warns that the Ch8 trade-offs table on p.9/11 was garbled in the text dump and was rebuilt from word positions. **Any claim taken from that table needs a check against the PDF.**
- RSE is not in the book (02, 04).

**Repo notebooks and cells (cited from 02/04; UNVERIFIED here)**
- `context_enrichment_window_around_chunk.ipynb` cells 13, 15–19, 23, 25–27; `rs/context_enrichment_window_around_chunk.py:L17-L120`.
- `context_enrichment_window_around_chunk_with_llamaindex.ipynb` cells 12–24.
- `relevant_segment_extraction.ipynb` cells 7–21.

**Existing course files read**
- 02 X1 card; 03 (stage 13, X1 rows, the "context window" name clash, the overlap-plus-window double count); 04 (Ch8 table, DV-21, DV-22); 06 v4.0 and §2.3, §7.2–7.3; 08 D-09, D-10, D-18, D-32 (via 08/foundation quotes); C5 lesson (D.1, D.2, H.3); P7 lesson (D.4, D.6); the tracker and misconception log; the P3 gap audit.
- Not present for X1: lesson, reading file, question file, lab, `sources/verification/X1/`.

**AE book sections:** none specific to X1. The method skills (`rag-evaluation` context swapping) are named in the foundation. Not checked here.
**Interview-repo items:** `upstream/AI-Engineer-Interview-Questions/` is absent. The questions in §5 are my own, typical for the topic, and **not checked against that guide**.

**External sources (numbered as in the Sources list)**
[16] LlamaIndex `SentenceWindowNodeParser` and `MetadataReplacementPostProcessor` source, **verified**. [12] dsRAG `rse.py`, **verified**. [15] `langchain-text-splitters` `base.py`, **verified**. [14] LangChain `ParentDocumentRetriever` (file exists; not read in depth). [1] Liu et al. 2023 (for the interaction with long contexts), snippet only.

### 2. Gap audit

Yash's progress (tracker, 2026-10-18): only **P1 is exposed**; M2, M3, M5, R1 are exposed; **P7, C2, C3, C4, C5, I1, R3, M4, X-anything are not started**. So every bridge below is "not studied".

| # | Idea | Used where | Taught before use? | Owner | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Chunk **sequence number** (`seq`, 0-based per document) and the `chunk_id` format | finding neighbours | Defined in 06 §2.3 and C3; no lesson reads it | C3 | No | bridge | Show one real `chunk_id`, point at `:00027`; neighbours are `:00026` and `:00028`. Warn that `seq` restarts per document, so never assume `seq == row`. |
| 2 | **Stride = size − overlap**, and what overlap does to adjacent chunks | window length, trimming | C2 lesson (not studied) | C2 / I1 | No | bridge | Two lines and a drawn strip: 1,000-char chunks with 200 overlap advance by 800. |
| 3 | **Overlap-aware joining** | every window | The repo trims by an overlap *count* (default 20 vs split 200, DV-22) | X1 | — | **core** | Teach the exact method: a window is a *document-offset interval*; merging is interval union; the text is a slice of `doc_text`. Show the string-trim bug as a counter-example. |
| 4 | **Document offsets** (`char_start`, `char_end`) and the invariant `doc_text[char_start:char_end] == text` | merge, dedup, CE | 06 §2.3 only | C2/C3 | No | bridge | One diagram: a document strip with three chunks and their intervals. |
| 5 | **Window size N** and **token growth** | choosing N | Not taught | X1 | — | **core** | Formula: window chars ≈ size + 2N × stride; tokens ≈ chars ÷ chars-per-token. Derived table N = 0…3 (180, 467, 754, 1,041 tokens). |
| 6 | **Equal-token-budget comparison** | v4.0 arms | 06 rule 1; M4 (not started) | M4 | No | bridge | Define the fill-by-rank procedure in the lesson (see §6). Without it the result is ambiguous. |
| 7 | **Edges**: clamp at document start and end; never cross a document | any hit near an edge | Not taught | X1 | — | core | Two rules and a unit test. |
| 8 | **Merging nearby hits**: two hits within 2N chunks share neighbours | k > 1 | Not taught; the repo expands each hit alone | X1/X3 | — | core | Union of intervals. Same step as dedup in X3. |
| 9 | **Sentence window** variant (embed one sentence, return ±3) | LlamaIndex notebook | Not in the book (DV-21) | X1 | — | core (Full) | Present as a *different* technique with the same goal; show LlamaIndex's mechanism (verified in source). |
| 10 | **RSE**: value per chunk, penalty, best contiguous run | `relevant_segment_extraction.ipynb` | Not in the book; notebook has unexplained constants | X1 | — | **core** | Teach as "a max-sum contiguous run where each irrelevant chunk costs a penalty". Hand-compute a 8-chunk example. |
| 11 | **Absolute vs rank-only relevance** | RSE value function | P3 lesson §11 (scores comparable only within a question) | P3 / R3 | P3 not studied | bridge | One paragraph: RSE multiplies a rank decay by an absolute score; cosine and cross-encoder scores are not on the repo's scale. |
| 12 | **Exponential rank decay** `exp(−rank / decay)` | RSE | Not taught | X1 | — | core (Full) | One sentence and one small chart. |
| 13 | **CE on the final assembled context** (and Span-Coverage as a diagnostic) | v4.0 metric | 06 §7.2–7.3; P6/M2 (M2 exposed) | M2 | exposed only | bridge | Recompute CE on the *union of intervals in the prompt*, not on the top-k list. |
| 14 | **Straddling evidence**: a gold span split across two chunks | the only case X1 can fix | Not taught | X1 | — | **core** | Teach as the reason X1 exists, and as the precondition: if no gold span straddles, X1 cannot help CE. |
| 15 | **When windows hurt**: lists, tables of unrelated rows, big chunks | "when NOT to use" (06) | 06 only | X1 | — | core | A short "do not use when" table with a reason each. |
| 16 | **Name clash**: "context window" (Ch8) vs the LLM's context window | vocabulary | 03 notes it | X1 | — | core | Call Ch8's idea "neighbour window" everywhere. State the clash once. |
| 17 | **Page label of a merged window** | citations | C5 uses the first page | X3/C5 | No | bridge | Link to X3 §label drift; X1 only stores `page_segments` for the merged interval. |
| 18 | **Lost in the middle** interacts with long windows | bigger N pushes evidence to the middle | P7 D.6 (not studied) | P7 | No | bridge | One paragraph, link only. |
| 19 | **O(1) neighbour lookup** (dict keyed by `(doc_id, seq)`) vs the repo's linear scan of every vector | latency | DV-22 | X1 | — | core (small) | Show the scan cost on 97 chunks (trivial) and why it is still a bad pattern. |

### 3. Quiz coverage

No `study/questions/X1_questions.md` exists. Needed question titles (titles only):
- **PRE:** X1-PRE-01 "A chunk is correct but the answer is cut off: which fix, and what does it change?"; X1-PRE-02 "Is overlap an index-time or query-time setting? Is the window?" (MC-003).
- **R:** X1-R-01 stride and overlap arithmetic; X1-R-02 "why does window expansion leave top-k retrieval metrics unchanged but change CE on the final context?"; X1-R-03 "sentence window vs chunk window: what is embedded, what is returned?"; X1-R-04 "what does RSE's penalty do to segment length?"
- **A:** X1-A-01 merge three windows by hand with offsets; X1-A-02 token growth for N = 1 and the k that fits a 720-token budget; X1-A-03 RSE value of a given segment by hand.
- **T:** X1-T-01 "windows added noise and answers got worse: diagnose and fix"; X1-T-02 "choose N and k for a table-heavy manual"; X1-T-03 "the overlap parameter at stitch time was 20 while the splitter used 200: what is visible in the output?"
- **Interview:** X1-R-05 "How do you give the model more context around a retrieved chunk without re-indexing?"
- Short-mode rule (P3 audit): the two formulas (stride, window tokens), the interval-union merge, and the straddle precondition must be in Short.

### 4. Errors found in existing material (not edited)

| # | Where | Problem |
|---|---|---|
| X1-E1 | 02 X1 (Pre: C3, X3) vs 03 registry (X1 requires I1; X3 is advice) | The prerequisite lists disagree: C3 vs I1. |
| X1-E2 | 06 v4.0 hypothesis | It says "equal context-token budget" and "top-k retrieval metrics are unchanged by construction". At an equal budget the ±1 arm keeps fewer hits (derived: 467 vs 180 tokens per hit), so the set of hits *does* change. The arm definition is ambiguous. |
| X1-E3 | 04 X1 row ("Linear-scan lookup; overlap-default mismatch") | Consistent with DV-22. But 04 lists RSE constants (decay 30, penalty 0.2) as "unexplained". In dsRAG's source these exact values are the `precision` preset (`decay_rate` 30, `irrelevant_chunk_penalty` 0.2), and a docstring maps each penalty to a typical segment length. They are inherited and documented, though not tuned for this corpus. (The notebook cell itself is UNVERIFIED here.) |
| X1-E4 | 04 (Ch8 p.9/11 "no LLM calls") and 03 §130 | The claim sits on a page whose table 01 says was garbled in the text dump. Re-read it in the PDF before using it. |
| X1-E5 | 06 §2.5 trace and C5 IA-1 | `page` is the *first* page segment. A window spanning pages is mislabelled by that rule. See X3. |
| X1-E6 | `langchain-text-splitters` `add_start_index` (source `base.py` L137–140) | The start index is found with `text.find(chunk, offset)`, with `strip_whitespace=True` as the default. If whitespace was stripped or text repeats, the index can be wrong, and a missing match gives −1. Do not use it as offsets for merging. Use the course chunker's own offsets. |
| X1-E7 | Foundation §9.2 | The splitter defaults it lists (4,000 characters, overlap 200) match the source read here. No error. Noted because they differ from the course's 1,000/200. |

### 5. What the research says

**Verified in source (framework mechanisms)**
- **LlamaIndex sentence window** [16]. `SentenceWindowNodeParser` makes one node per sentence. Each node carries a window of `window_size` sentences on each side, default **3**, joined with a single space, stored in `metadata["window"]`. The window and the original text are excluded from the embedding text and from the LLM metadata. `MetadataReplacementPostProcessor` swaps the node content for the window at query time, and falls back to the node text if the key is missing. It works per node, so **two adjacent retrieved sentences each expand to overlapping windows, and nothing merges them**. (Read from the code; my reading of "no merge" is that no such step exists in these two files.)
- **dsRAG RSE** [12]. For each query, every chunk gets a value `exp(−rank / decay_rate) × relevance − irrelevant_chunk_penalty`, optionally scaled up for chunks longer than a reference length (700 characters). A segment is a contiguous run of chunks inside one document. Its value is the **sum** of its chunk values. A brute-force loop picks the best run of at most `max_length` chunks that does not overlap earlier picks and does not cross a document boundary, repeats until `overall_max_length` chunks are chosen, and stops when the best remaining value is below `minimum_value`. Presets: `balanced` (max 15, total 30, penalty 0.18, decay 30), `precision` (penalty 0.2, minimum 0.7), `find_all` (max 40, total 200). The penalty is documented to control run length (0.05 gives 20–50 chunks; 0.4 gives 1–3).
  - The cost of the loop is about n × max_length segment scores per pick. Trivial at n = 97.
  - The value needs an **absolute relevance** per chunk. The repo gets it from a Cohere rerank (04). dsRAG's headline benchmark numbers combine several methods and differ between README versions (83% vs 96.6% on FinanceBench in search snippets), so **they are not evidence for RSE alone** (UNVERIFIED).
- **Parent-document and window patterns** are a family. The course keeps them apart: X1 expands at query time from stored sequence ids; I6/parent-document retrieval stores a parent mapping at index time.

**Papers (all UNVERIFIED here; snippets only)**
- **Liu et al., "Lost in the Middle", TACL 12 (2024), arXiv 2307.03172** [1]. *Tested:* multi-document question answering and key-value retrieval, moving the one relevant item across positions. *Result:* best at the start or end, worst in the middle, even for long-context models. *Limits:* 2023-era models; the course's external review read Liu et al.'s Appendix G Table 6 and found the AI Eval book's "lost in the middle" figure overstated against those tables (EXTERNAL_RESOURCES_REVIEW §8 and its closing note). *Meaning here:* expanding windows lengthens the context, so it moves more text into the middle. Measure; do not assume.

**Current practice (my interpretation, not a source claim).** Two things changed since 2023. Context windows are large and cheap, so many pipelines pass more chunks and rely on reranking (Anthropic's contextual-retrieval post passes the top 20 after reranking 150 [18]). Query-time neighbour expansion survives mostly as "small-to-big" retrieval: match a small unit, return a bigger one. The risks are unchanged: noise, duplicated overlap, and label drift.

**Pitfalls (with evidence)**
- Stitching with the wrong overlap duplicates text (DV-22; the unit test is cheap).
- The repo scans every vector to find a neighbour (DV-22).
- A window helps only when the evidence is split across chunks. If the gold span fits in one chunk, a window adds tokens and nothing else.
- Overlap plus a window counts the same text twice (03 §483), unless you merge by offsets.
- RSE needs zero overlap in the repo (04). The offset method removes that need.

**How to evaluate**
- **Retrieval side:** CE@k and Hit@k should not change (confirm only). **CE on the final assembled context** is the retrieval-side metric for this concept. Span-Coverage on the final context is a diagnostic.
- **Answer side:** human labels on the changed answers (D-10), EM/F1 only for short-answer items, citation page-hit. Judge metrics wait for the end batch.
- **Baseline:** v0 or the v3 champion's context at the same budget, k = 4 unwindowed.
- **Precondition check (new):** count gold items whose every alternative span is *not* inside a single chunk ("straddle count"). If the count is zero in dev, X1 cannot move CE and the experiment should say so up front.

**Interview questions (mine; not checked against the interview guide)**
1. How do you provide neighbouring context for a retrieved chunk? What do you store at index time?
2. How do you avoid duplicating overlapped text when you join neighbours?
3. What is the difference between a sentence window and a parent-document retriever?
4. How would you decide the window size?
5. When does expansion hurt?

### 6. Lesson blueprint

**The answer first (draft, 5 sentences)**
1. A retrieved chunk can be right and still cut the answer in half, because chunk boundaries ignore meaning.
2. The neighbour window fixes this at query time: for each hit, also fetch the chunks before and after it, and join them without repeating the overlap.
3. It costs tokens, not LLM calls: with 1,000-character chunks, one hit grows from about 180 tokens to about 470 at ±1, so under a fixed budget you keep fewer hits.
4. It only helps when the evidence really straddles a boundary; otherwise it adds noise.
5. Relevant segment extraction is the same idea driven by scores: choose the best contiguous run of chunks, where every irrelevant chunk in the run costs a penalty.

**The theory in one read (about 10 linked ideas)**
1. Chunks have addresses: `(doc_id, seq)` and an interval `[char_start, char_end)` in document offsets.
2. Overlap and stride: `stride = size − overlap`; neighbouring chunks share `overlap` characters.
3. A window is an interval: `[start(seq − N), end(seq + N))`, clamped to the document.
4. Joining is union of intervals: the text is `doc_text[a:b]`, never the concatenation of chunk strings.
5. Nearby hits merge: if their windows overlap or touch, take one union.
6. Cost: `tokens(N) ≈ (size + 2N × stride) ÷ cpt`, with `cpt` the characters per token (5.57 on the climate corpus with `cl100k`; D.5 of 07).
7. Budget: with budget B and per-hit cost `t(N)`, `k_max = ⌊B ÷ t(N)⌋`. More context per hit means fewer hits.
8. What it can and cannot change: top-k metrics unchanged; CE on the final context can change; only straddling evidence can gain.
9. Sentence window: embed one sentence, return ±S sentences, a different mechanism with the same goal.
10. RSE: value per chunk `v = exp(−rank / d) × s − p`; pick the contiguous run with the largest sum, under a length cap.
11. Failure modes: noise from unrelated neighbours, double-counted overlap, evidence pushed into the middle, wrong page label.

**Formula-sheet items**
- `stride = size − overlap`
- `window_chars(N) = size + 2N × stride` (interior; clamp at edges)
- `window_tokens(N) ≈ window_chars(N) ÷ cpt`
- `k_max = ⌊B ÷ window_tokens(N)⌋`
- `straddle(g) = 1` if no alternative span of group g lies inside one chunk
- `v_i = exp(−rank_i / d) × s_i − p`; `value(a,b) = Σ v_i for i in [a,b)`

**Step-by-step outline (running example: the climate PDF, `Understanding_Climate_Change.pdf`, chunked 1000/200 as v0).** The upstream path is not present in this checkout; the corpus is the one 06 names as Corpus D.
1. Pick one real straddling case (found by the straddle audit): the answer's sentence starts at the end of chunk `…:00026` and finishes in `…:00027`. Show that top-1 retrieves one and CE = 0.
2. Draw the strip: three chunks, their intervals, the 200-character overlap.
3. Expand ±1; show the union interval and the slice.
4. Show the string-trim version with the wrong overlap and the duplicated sentence it produces.
5. Table of N = 0…3: characters and tokens (derived), and `k_max` for B = 720.
6. Two hits close together: merge them; show the token saving versus expanding separately.
7. Recompute CE on the final context for the straddling item.
8. RSE: an 8-chunk toy score vector; compute values with `p = 0.2`, find the best run by hand; change `p` and watch the run shrink.
9. Do-not-use cases, in one table.

**Visuals that earn their place** (hand-drawn SVG unless interactive)
- Chunk strip with intervals and overlap: shows that merging is arithmetic on positions.
- Window growth chart (tokens vs N next to the budget line): shows why k falls.
- Before/after of the wrong-overlap stitch: shows the duplicated sentence.
- RSE value bars with the chosen run highlighted, with a penalty slider (Plotly in the notebook, static SVG in the lesson): shows what the penalty does.

**Full-only details:** the sentence-window variant in depth; the exponential decay and length-adjustment of RSE; multi-document RSE across a meta-document; the interaction with lost in the middle.

### 7. Verify notebook plan

- **File:** `study/notebooks/X1_window_verify.ipynb`. Offline: yes. Calls: **0**. Runtime: under 1 minute.
- **Data:** Corpus D chunks and cached C4 vectors (`vectors.npy`, `chunks.jsonl`), or MiniLM locally if vectors are absent. Gold items: the draft seed items in 06 §6.7 as a toy; the real eval set once M1 exists.
- **Recomputes:**
  1. Interval merge on real chunks, with the assertion `doc_text[a:b] == merged_text`; also for clamped edges and for two close hits.
  2. The string-trim merge with overlap 20 vs 200, counting duplicated characters (reproduces DV-22 on our data).
  3. The token table for N = 0…3 with `tiktoken` `o200k_harmony` (C5's tokenizer), compared with the derived formula; report the gap, if any.
  4. The **straddle audit** on the seed items: for each gold group, is any alternative inside one chunk?
  5. CE@4, then CE on the final context for N = 0, 1, 2 with the equal-budget fill (fill by rank until B).
  6. RSE on the cosine scores of all 97 chunks for three queries, with Plotly bars and a penalty sweep.
- **Needs no LLM.** Charts: Plotly (interactive).

### 8. Apply-it tool plan and real-world checklist

- **Tool:** `study/tools/context_window_check.py`. **Inputs:** a `chunks.jsonl` (with `doc_id`, `seq`, offsets), a questions file with an optional gold quote per question, a budget B, a tokenizer name. **Outputs:** a short report and a CSV.
- **Recommendation logic:** if the straddle count is 0, report "windows cannot help retrieval here"; if ≥ 1 and the median hit is under B ÷ 4 tokens, suggest N = 1; if the median hit already uses more than B ÷ 2 tokens, suggest no window (or smaller chunks, I1); if more than 30% of neighbours sit on a different page or section heading, warn about noise and label drift.

| # | Check | Mode |
|---|---|---|
| 1 | `seq` is contiguous per document and neighbours exist | auto |
| 2 | Offsets satisfy `doc_text[start:end] == text` | auto |
| 3 | The real overlap equals the declared overlap (stride check) | auto |
| 4 | Token growth for N = 1, 2 and the `k_max` under budget B | auto |
| 5 | Straddle count: gold quotes not contained in any single chunk | auto (needs gold quotes) |
| 6 | For each straddling quote, is it inside the ±N window? | auto |
| 7 | Share of neighbours on another page or another heading | auto |
| 8 | Duplicate characters after merging (should be 0) | auto |
| 9 | Read 5 windows: do the neighbours belong to the same topic? | manual (list them) |
| 10 | Do your documents have tables or lists where neighbours are unrelated rows? | manual |
| 11 | Are your chunks already larger than B ÷ 2? | auto |

### 9. LLMOps notebook plan

File: `study/notebooks/X1_window_llmops.ipynb`. Follows `LLMOPS_FOUNDATION.md` (§2 cache, §3 trace, §12 row "7 · X1–X3").

**Framework build (pieces mapped to the mechanism)**
- Retriever: a small `BaseRetriever`-style wrapper (or `RunnableLambda`) over C4's cosine search, using `CachedEmbeddings`. Maps to the "retrieve" step.
- Expansion: a `RunnableLambda` that calls the course's `expand_window(hits, N)`. Plain Python, framework-free inside.
- Generation: the C5 `build_messages` and `CachedChatModel`.
- **LCEL, no LangGraph.** The flow has no cycle, branch or checkpoint, so the foundation's own rule (§9.1) says a plain chain or function is the right tool.
- **Framework defaults the lesson warns about:** `RecursiveCharacterTextSplitter` `chunk_size=4000` characters and `add_start_index=False` (`base.py`); with `add_start_index=True` it recovers offsets by `str.find`, which can mismatch (X1-E6); LlamaIndex joins window sentences with a single space (original whitespace is lost); LlamaIndex `window_size=3` by default; neither framework merges overlapping windows of neighbouring hits.
- Read-only cells: show LlamaIndex's `SentenceWindowNodeParser` source and the output of a ±1 expansion next to ours.

**Caching.** External calls: Cohere embed for any chunk not already cached (about 97 texts, 1–2 calls, usually 0 because C3 cached them); Groq generation for 3 arms (champion, ±1, ±1 + merge) × 46–55 questions ≈ **140–165 calls**, of which the champion arm is likely already recorded. Runs in `replay` with no key and no credits once recorded. `LLMOPS_CACHE_MODE=replay` in CI.

**Tracing.** JSONL trace (always); Phoenix locally; LangSmith only for corpus D inside `tracing_context`, after `privacy.assert_corpus_is("D")`. Context span fields: for every block, `origin` (`hit` / `neighbour` / `rse`), the interval, source chunk ids, tokens, `rank_of_best_hit`, and the merge decisions; the budget used and the blocks dropped by the budget.

**Dataset and evaluators**
- Golden set from M1 (dev split), with a `straddles` tag computed by the audit. Local JSONL is the source of truth.
- Code evaluators: CE@4 (confirm unchanged), CE on the final context, Span-Coverage on the final context, context tokens, duplicate characters (must be 0), label-resolves rate, EM/F1 and citation page-hit where defined. No LLM judge before the end batch (D-10).
- Experiment: arms from 06 v4.0 (champion, ±1, ±1 + dedup) at the **same realised token budget**, plus RSE as an extra, pre-registered arm. Report on all items and on the straddle subset separately, with the paired bootstrap and a note that n is small (06 §9.4).

**Cost, latency, tokens (assumed tokens, not measured).** Per arm: 55 × (≈1,000 input + ≈400 output) ≈ 77K tokens. Groq `gpt-oss-20b`: about **$0.011**; Haiku 5.5: about $0.017; Sonnet 5.5: about $0.33. Three arms ≈ 231K tokens: above one day's listed Groq token quota (200K, plan UNVERIFIED), so plan two days or a client-side throttle. Latency: report p50/p95 per stage, excluding cache hits.

**Versioning.** `prompts/answer_v1.txt` unchanged (so the only variable is context). Config YAML: `context: {strategy, window_n, budget_tokens, fill: by_rank}`, hashed into `config_hash`. Each arm is one pre-registered run.

**Monitoring and feedback.** Watch: tokens per context (p50/p95), share of items over budget, duplicate characters (alert on > 0), merge rate, `finish_reason = length`. Failure flow: an item where the window made things worse goes into M5 as a new bucket "window noise", and is added to the golden set as a regression item.

**Place in the lifecycle.** Analyze (v3 traces: which failures are "answer cut off"?, `error-analysis`) → Measure (`rag-evaluation`, `code-based-evaluators`) → Improve (`improving-llm-agents`); dev notebook → local CI token-budget test (`ci-cd-evals`) → monitor page. Skills used: `rag-evaluation`, `error-analysis`, `code-based-evaluators`, `llm-observability`, `ci-cd-evals`.

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Tokens | `tiktoken` (`o200k_harmony`) | 0.14.0 | yes | yes (encoding file may download once) | — | MIT | yes |
| Arrays, tables, charts | `numpy`, `pandas`, `plotly` | as locked | yes | yes | — | BSD / MIT | yes |
| Scores for RSE | cached C4 vectors (Cohere `embed-v4.0`) or MiniLM `all-MiniLM-L6-v2` | as C3 | yes | MiniLM yes | embed cached | Apache-2.0 | yes |
| Optional absolute relevance | Cohere rerank (`rerank-v4.0-fast`/`pro`) | API | n/a | no | priced per search (price UNVERIFIED); 97 chunks fit one search of ≤ 100 documents | proprietary | optional (D-11) |
| LLM (answers) | Groq `openai/gpt-oss-20b`, `reasoning_effort=low`, `max_completion_tokens` set | per `.env` | yes | no | ≈$0.011 per 55-question arm | — | yes (default) |
| LLM (comparison arm) | Claude Sonnet 5.5 `claude-sonnet-5-5` | via foundation | no | no | ≈$0.33 per arm (assumed tokens) | — | optional (D-32) |
| Framework core | `langchain-core` | 1.6.6 | no | yes | — | MIT | yes |
| Splitters (comparison) | `langchain-text-splitters` | 1.1.3 | no | yes | — | MIT | yes (comparison only) |
| Hosted tracing | `langsmith` | 0.14.4 | no | SDK yes | free plan | MIT | corpus D only |
| Local tracing | JSONL + `arize-phoenix-otel` | 0.17.2 | no | yes | — | Apache-2.0 | yes |
| Read-only reference | `llama-index-core` | 0.14.25 | no | yes | — | MIT | **do not install** (aiohttp, networkx, nltk, sqlalchemy, pillow…) |
| Read-only reference | `dsrag` | 0.5.6 | no | yes | — | MIT | **do not install**; the algorithm is 70 lines |
| Sentence splitter | course-written regex | stdlib | yes | yes | — | — | yes (framework-free) |
| Sentence splitter (alt) | `pysbd` 0.3.4 (last release 2021-02) / `nltk` 3.10.3 (needs data download) | — | no | partly | — | MIT / Apache-2.0 | optional |

- **Install lines:** none new beyond the foundation's. `uv add --group llmops langchain-core==1.6.6 langchain-text-splitters==1.1.3 langsmith==0.14.4` (do not run).
- **Keys:** `GROQ_API_KEY`, `COHERE_API_KEY` (present); `ANTHROPIC_API_KEY`, `LANGSMITH_API_KEY` when wanted.
- **Frameworks needed at all?** No, for the lesson and verify notebook. LangChain only in the LLMOps notebook. LlamaIndex and dsRAG are for reading.
- **Groq features:** plain chat completion only. Nothing exotic.

### 11. Open questions for Yash (preferences only)
- Include RSE as an arm? (decision 2.)
- When the straddle count in dev is zero, should the X1 experiment still run for the lesson's sake, or be reported as "not applicable on this corpus"? **Suggestion:** run only the verify-notebook demo; skip the LLM arms.

---

## Concept X2: Contextual compression

### 1. Sources checked

**Book pages (cited from 02/04/01; UNVERIFIED here)**
- Ch10 p.2/13 (within-chunk relevance), p.3/13–p.5/13 (core, compression funnel), p.5/13–p.6/13 (retrieve), p.6/13–p.7/13 (compress), p.7/13 (generate), p.8/13 (sketch), p.8/13–p.9/13 (full pipeline), p.9/13–p.10/13 (what is removed), p.10/13–p.11/13 (versus relevancy grading), p.11/13–p.13/13 (when, key takeaways). 04 additionally places the grade-then-compress remark on p.11/13. The cost wording of the Ch10 trade-offs (p.12/13 area) is in the garbled-table list of 01. **Re-check it in the PDF.**
- App p.5/23 lists Ch10 under "good documents, wrong order" (03 line 135).

**Repo notebooks and cells (UNVERIFIED here):** `contextual_compression.ipynb` cells 5, 10–14 (`LLMChainExtractor` inside `ContextualCompressionRetriever`; RetrievalQA "stuff"); `rs/contextual_compression.py:L20-L89`.

**Existing course files read:** 02 X2; 03 (stage 13, X2 row, X2 ← X3); 04 (Ch10 table, DV-24); 06 v4.1 and §7.2; D-09, D-10; the tracker; the misconception log (MC-005 touches k and noise); P7 and C5 lessons (token budget, answer reserve, `reasoning_effort`).

**External sources:** [14] LangChain `LLMChainExtractor`, `chain_extract_prompt.py`, `ContextualCompressionRetriever`, `EmbeddingsFilter` (**verified**); [15] `BaseDocumentCompressor` in `langchain-core` (**verified**); [3] RECOMP (snippet); [4–7] LLMLingua family (README verified, papers not); [2] Cuconasu et al. (snippet); [10] Chroma context rot (snippet); [17] Anthropic long-context tips (verified).

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | **What compression is** (query-aware shortening of a retrieved chunk) vs summarisation, reranking, grading | whole concept | Ch10; 03 "commonly confused" | X2 | — | **core** | A 2×2: changes the text? uses the query? Place compression, grading (keeps or drops whole chunks), summarisation (query-blind), reranking (reorders). |
| 2 | **Extractive vs abstractive** | choice of compressor | Not taught | X2 | — | **core** | Extractive = pick existing spans (can be checked and located); abstractive = rewrite (cannot be located). Only extractive can be scored with CE. |
| 3 | **Sentence splitting** | extractive baseline | Not taught | X2 | — | bridge | A 15-line regex splitter; note where it fails (abbreviations, decimals, bullet lists). |
| 4 | **One LLM call per chunk** (cost, latency, rate limits) | `LLMChainExtractor` | Ch10 gap; v4.1 | X2 | — | core | Count calls: 4 per question; show the Groq 30 requests/min and 8K tokens/min arithmetic (foundation §2.5). |
| 5 | **Prompt contract**: "extract AS IS"; the `NO_OUTPUT` sentinel | the LangChain extractor | Not taught | X2 | — | **core** | Show the verified prompt shape and the exact sentinel rule: the reply, stripped, must equal the sentinel to count as empty. |
| 6 | **Verbatim check and offset re-alignment** | CE on the compressed context | DV-24, 04 "build yourself" | X2 | — | **core** | Substring match of each extract against its chunk; map to document offsets; unmatched extracts are flagged "not verbatim" and cannot be scored. |
| 7 | **Evidence retention = CE on the final context** vs CE before | v4.1 metric | 06 §7.2 | M2 | exposed only | bridge | Same function as X1, fed with the compressed intervals. |
| 8 | **Tokens saved and compression ratio** | v4.1 primary metric | Not taught | X2 | — | core | `ratio = tokens_after ÷ tokens_before`; saving = 1 − ratio. Count with the same tokenizer as C5. |
| 9 | **What compression removes**: qualifiers, numbers, units, negations, the referent of a pronoun | faithfulness risk | Ch10 p.9–10/13 | X2 | — | core | A small gallery of 6 real failures from our corpus; a regex checker for dropped digits and negations. |
| 10 | **Non-inferiority claim**: "tokens fall, correctness does not drop" | the v4.1 hypothesis | M4 (not started) | M4 | No | bridge | Pre-register a margin; say what n can and cannot show (06 §9.4). |
| 11 | **Grade-then-compress** (DV-24) | Ch10 p.11/13 | not in the repo | X2/V2 | — | core (Full) / next | Build it as a two-step arm only if cheap; the grader itself belongs to V2. Link. |
| 12 | **Cross-chunk duplicates survive**, because each chunk is compressed alone | 03 note; confirmed in source | Not taught | X2/X3 | — | core | Run dedup (X3) *before* compression, then compress once. |
| 13 | **Reasoning-model budget**: a low `max_completion_tokens` gives an empty reply (`finish_reason = length`) | any Groq call | P1/C5 D.6 | P1 | exposed | bridge | One reminder plus the `assert text.strip()` rule. |
| 14 | **Non-LLM compressors**: sentence scoring by BM25 or cosine; keep the top-m sentences in original order | baseline arm | 04 says build one | X2 | — | core | The main teaching device: it shows the idea without an LLM and gives a free baseline. |
| 15 | **Token-level pruning (LLMLingua family)** | alternative | Not in the book | X2 (next) | — | next | Two paragraphs: what it does, why the output is not readable text, why it is out of scope. |
| 16 | **Faithfulness measurement** | v4.1 guard | M3 (exposed); judge at the end (D-10) | M3 | exposed | bridge | Human labels until the end batch. Say so in the lesson. |
| 17 | **Compressor sees untrusted text** | injection | D4 | D4 | No | next | One line, link to D4. |
| 18 | **Position of compression in the pipeline**: dedup and budget decisions need lengths *after* compression | assembler | X3 | X3 | — | bridge | Pipeline order drawn once (see Phase-level notes). |

### 3. Quiz coverage

No `study/questions/X2_questions.md`. Needed question titles:
- **PRE:** X2-PRE-01 "What problem does compression solve that reranking does not?"; X2-PRE-02 "Compression or grading: which keeps whole chunks?"
- **R:** X2-R-01 extractive vs abstractive and why it matters for checking; X2-R-02 "why can't a per-chunk compressor remove duplicates between chunks?"; X2-R-03 "what does `NO_OUTPUT` mean and how is it parsed?"; X2-R-04 "what changes in the prompt when compression is on: tokens, calls, latency?"
- **A:** X2-A-01 compute the compression ratio and the tokens saved for given chunks; X2-A-02 estimate calls and the time at 30 requests/min for 55 questions; X2-A-03 given an extract and its chunk, is it verbatim and which offsets does it cover?
- **T:** X2-T-01 "answers got worse after compression: find which sentence was dropped"; X2-T-02 "legal or numeric text: should you compress?"; X2-T-03 "what would you measure to claim 'no loss'?"
- **Interview:** X2-R-05 "Compare reranking, grading and compression."
- Short-mode rule: the ratio formula, the extractive/abstractive split, the verbatim check, and one cost count must be in Short.

### 4. Errors found in existing material (not edited)

| # | Where | Problem |
|---|---|---|
| X2-E1 | 04 Ch10 table, "drop behaviour UNVERIFIED" | Now verified from source [14]: an empty or sentinel-only reply is dropped (`len(output) == 0 → continue`); the sentinel parser compares the whole stripped reply to `NO_OUTPUT`, so a reply like `NO_OUTPUT.` is **kept** as text. Metadata is kept. |
| X2-E2 | 04 / 02 (X2: "extraction may not be verbatim") | Correct, and stronger: the code never checks. The prompt text asks for "AS IS" extraction; nothing verifies it. |
| X2-E3 | 04 "Outdated: `langchain.chains` / `langchain.retrievers`" | Confirmed: both now live in `langchain_classic` (1.0.8). In the current source the extractor is a plain `prompt | llm | parser` chain; the old `LLMChain` branch is a legacy path only. |
| X2-E4 | 06 v4.1 "+1 LLM call per retrieved chunk (or one batched call)" | OK. But the *sync* LangChain path calls the chain **one document at a time** (a loop of `invoke`); only the async path uses `abatch`. A k = 4 compression in a sync notebook adds four sequential calls to latency. |
| X2-E5 | 06 v4.1 hypothesis: "cuts context tokens substantially with no drop in answer correctness" | "No drop" is a non-inferiority claim and needs a margin chosen in advance; with n ≈ 46–100 it cannot support "no drop", only "no large drop". |
| X2-E6 | 02 X2 Pre (X3, M3) | M3 is "exposed" only; the faithfulness part needs human labels until the D-10 batch. The card should say so. |
| X2-E7 | 04 (cells 0 vs 12) | Markdown says GPT-4, code uses `gpt-4o-mini`. Already noted in 04. Both are OpenAI, outside the project decisions. |

### 5. What the research says

**Verified in source**
- **LangChain `LLMChainExtractor`** [14]. Prompt (read): given the question and context, extract any part of the context *as is*, do not edit; if nothing is relevant return the sentinel. The chain is `prompt | llm | parser`. For each document, in the sync path, one `invoke`; an empty result drops the document; surviving documents keep their metadata. `ContextualCompressionRetriever` calls the base retriever, then the compressor, and returns `[]` if nothing was retrieved. `EmbeddingsFilter` (the non-LLM sibling) keeps chunks by similarity, with `k=20` by default and no threshold; it keeps or drops **whole chunks**, so it is grading by embedding, not compression.
- `BaseDocumentCompressor` lives in `langchain-core` [15], and its docstring recommends a `RunnableLambda` instead of subclassing. So our compressor does not need `langchain-classic`.
- **Anthropic** [17]: for long inputs (20K+ tokens), put documents first and the query last (up to 30% better "in tests" for multi-document inputs); ask the model to **quote the relevant parts first**, then answer. This is a one-call cousin of compression, with the cost moved to output tokens. Our contexts (about 1–2K tokens) are far below that range, so do not assume the size of the effect.

**Papers (UNVERIFIED here; snippets only)**
- **RECOMP, Xu, Shi, Choi, ICLR 2024, arXiv 2310.04408** [3]. *Tested:* trained extractive and abstractive compressors for language modelling and open-domain QA. *Result:* compression to as low as about 6% of the text with small loss, better than off-the-shelf summarisers; the compressors can return an empty string when nothing helps ("selective augmentation"). *Limits:* the compressors are trained for the task; our setting is a prompted general LLM or a plain scorer, which the paper does not test. *Meaning:* the empty-output option matches LangChain's sentinel and supports a grade step.
- **LLMLingua family** [4–7]. README claims: up to 20× compression (LLMLingua, EMNLP 2023); LongLLMLingua "up to 21.4% better RAG performance using 1/4 of the tokens" (ACL 2024); LLMLingua-2 is a BERT-sized token classifier distilled from GPT-4 and is "3×–6× faster" (ACL Findings 2024). *Limits:* these are the authors' own claims, not read in the papers; the output is a token-pruned, non-fluent text; the package's last release is 2024-04 and needs torch, transformers, accelerate and nltk. *Meaning:* out of scope; mention only.
- **Cuconasu et al., "The Power of Noise", SIGIR 2024, arXiv 2401.14887** [2]. *Result (snippet):* adding **random** documents can raise accuracy by up to 35%, while high-scoring documents that do not contain the answer hurt. *Limits:* the setup, models and datasets were not read. *Meaning:* noise is not all alike. Related-but-wrong text (like the 1.5 °C and 2 °C distractors in D-001, P7 J4) is the harmful kind. Compression only helps if it removes *that* kind.
- **Chroma, "Context Rot" (2025)** [10]. *Result (snippet):* 18 models become less reliable as input grows even on simple tasks. *Limits:* secondary summaries only. *Meaning:* background for "shorter is not automatically worse".

**Current practice (my interpretation).** With cheap long contexts, compression is mainly a cost and latency tool, and teams that use it typically want extractive output so that citations still point at real text. The serious risk is silent loss of qualifiers and numbers.

**Pitfalls (with evidence)**
- Not verbatim: the framework does not check (source).
- A reply `NO_OUTPUT.` with a full stop leaks into the context (source).
- One LLM call per chunk is slow on the critical path (source) and eats the Groq quota (derived below).
- Dangling referents: a sentence starting "It" or "This" loses its antecedent when its neighbour is dropped.
- Compressing before dedup wastes calls on duplicates.

**How to evaluate**
- **Primary (two-sided, pre-registered):** mean context tokens and answer correctness (06 v4.1), with a non-inferiority margin for correctness.
- **Guards:** CE on the final context versus CE before compression (the evidence-retention rate); human-labelled faithfulness until the end batch (D-10); verbatim rate; p95 latency.
- **Baselines:** no compression (the v4.0 champion), the non-LLM extractive compressor, and an equal-token truncation (cut each chunk to its first m tokens) to show that "smart" beats "short".

**Interview questions (mine; not checked against the interview guide)**
1. Compare reranking, relevance grading and contextual compression.
2. Why do you want the compressor to be extractive?
3. How would you prove compression did not remove evidence?
4. When would you not use it?
5. What does it add to latency and cost, and how do you cut that?

### 6. Lesson blueprint

**The answer first (draft, 5 sentences)**
1. Contextual compression shortens each retrieved chunk to the parts that matter for the question, so the model reads less noise.
2. An LLM (or a scoring rule) reads the question and the chunk and returns only the relevant sentences, or nothing.
3. The gain is fewer prompt tokens; the cost is extra calls (one per chunk, or one batched call) and the risk of cutting out the one sentence the answer needed.
4. The safe form is extractive: the output must be a verbatim part of the chunk, so you can check it and still point at the real page.
5. Judge it by tokens saved against evidence kept (CE on the final context) and answer quality, and compare it with a no-LLM baseline.

**The theory in one read (about 9 ideas)**
1. Where it sits: after retrieval and dedup, before the budget fit and the prompt.
2. Four neighbours: reranking (reorders), grading (keeps or drops a whole chunk), summarising (ignores the question), compression (rewrites or cuts inside a chunk).
3. Extractive vs abstractive; only extractive is locatable.
4. The LLM extractor: the prompt, the sentinel, the empty output.
5. The non-LLM extractor: split into sentences, score each against the question, keep the top-m in original order.
6. Verbatim check and offsets: substring match, interval, mapping to document coordinates.
7. Metrics: `ratio`, tokens saved, CE after vs CE before, verbatim rate.
8. Cost: calls = k per question (or 1 batched); latency adds up in the sync path; Groq's rate limits.
9. Failure modes: dropped qualifier or number, dangling pronoun, merged sentences, the sentinel leak.

**Formula-sheet items**
- `ratio = tokens_after ÷ tokens_before`
- `saved = 1 − ratio`
- `calls = q × k` (per-chunk) or `q` (batched)
- `retention = CE(final) ÷ CE(before)` over answerable items (a ratio of means; define it exactly in the lab)
- `min_minutes = max(calls ÷ RPM, tokens ÷ TPM)`

**Step-by-step outline (running example: Corpus D, v0 top-4 for one question).**
1. Take the real top-4 for one question; mark which sentences carry the gold span.
2. Hand-write what an ideal extract looks like; count tokens before and after.
3. The non-LLM extractor: sentence split, BM25 and cosine scores, top-2 sentences, original order.
4. The LLM extractor on the same chunks (replayed); verbatim check; the offsets.
5. Show a failure: a number dropped, a "However" kept without its sentence.
6. CE before and after; tokens before and after; a small table.
7. Cost and time count for 55 questions.
8. When not to use: legal or numeric text; short chunks; contexts that are not a cost problem.

**Visuals that earn their place**
- Funnel: chunks → sentences → kept sentences, with token counts: shows where tokens go.
- Before/after view of one chunk with kept sentences highlighted and dropped ones struck through: shows exactly what was removed (the repo has no such view, DV-24 neighbour).
- A tokens-saved vs evidence-kept scatter over questions for each compressor: shows the trade-off per item.

**Full-only details:** RECOMP and LLMLingua at a glance; grade-then-compress; quote-first prompting as a one-call variant; the non-inferiority margin worked through.

### 7. Verify notebook plan

- **File:** `study/notebooks/X2_compression_verify.ipynb`. Offline: yes in replay. Runtime under 2 minutes.
- **Data:** Corpus D chunks, v0 top-4 lists for 5–10 seed questions.
- **Recomputes:** sentence splits and counts; BM25-sentence and cosine-sentence extractors (MiniLM local); tokens before and after; ratio; the verbatim check for LLM extracts; CE before and after on the seed items; a dropped-digit and dropped-negation scan; the call-count and minutes arithmetic.
- **LLM calls (recorded once, then replayed):** the per-chunk LLM extractor on ≤ 5 questions × 4 chunks = **≤ 20 Groq calls**. If the batched variant is shown too, add 5 calls.
- Charts: Plotly (interactive).

### 8. Apply-it tool plan and real-world checklist

- **Tool:** `study/tools/compression_check.py`. **Inputs:** retrieved context blocks (JSONL) and questions, optional gold quotes; option `--llm` (off by default). **Outputs:** per-chunk before/after view, a summary, and a recommendation.
- **Recommendation logic:** "compress" only if the median context is a real cost (for example above 50% of the budget), the offline extractor keeps ≥ 95% of gold quotes, and the dropped-number rate is zero; "do not compress" if gold quotes include numbers or exact wording, or if the context is already small; "try the LLM arm" only if the offline extractor loses evidence the LLM would keep.

| # | Check | Mode |
|---|---|---|
| 1 | Median context tokens vs the budget (is length a problem at all?) | auto |
| 2 | Tokens saved by the offline extractor | auto |
| 3 | Gold quotes still present after compression | auto (needs quotes) |
| 4 | Numbers, units, negations dropped | auto |
| 5 | Sentences that start with a pronoun after their neighbour was dropped | auto |
| 6 | Verbatim rate of LLM extracts | auto (with `--llm`) |
| 7 | Empty extraction rate | auto |
| 8 | Estimated calls, tokens and minutes at your rate limits | auto |
| 9 | Read 5 before/after pairs side by side | manual |
| 10 | Does your text need exact wording (law, contracts, specs)? | manual |
| 11 | Compare answers with and without compression on 10 questions | manual |

### 9. LLMOps notebook plan

File: `study/notebooks/X2_compression_llmops.ipynb`.

**Framework build**
- A `BaseDocumentCompressor` subclass (from `langchain-core`) or a `RunnableLambda` that runs the course extractor. Maps to the lesson's "compress" step. **Do not install `langchain-classic`.**
- Show `LLMChainExtractor` as read-only source next to ours, with its three behaviours called out: no verbatim check, sentinel compared on the whole stripped reply, one call per document in the sync path.
- `RunnableParallel` or `abatch` for the per-chunk arm, if latency matters in the cached-miss run.
- **LCEL, no LangGraph.** An optional two-node graph (grade, then compress or skip) is a bridge to A2 only if the grade-then-compress arm is built; the foundation's rule (a branch chosen at run time) would then apply.
- **Defaults the lesson warns about:** `EmbeddingsFilter` `k=20`, no threshold; `format_document` in the default "stuff" chain keeps only `page_content`, which drops page labels (see X3); `Runnable.with_retry` retries every exception and must not wrap cached calls (foundation §9.2).

**Caching.** Calls and sizes (assumed tokens, not measured), for 55 questions × k = 4:

| Arm | Calls | Approx. tokens | Groq `gpt-oss-20b` cost | Haiku 5.5 cost | Min. time at 30 RPM / 8K TPM |
|---|---|---|---|---|---|
| Per-chunk LLM | 220 | ≈158K (99K in, 59K out) | ≈ $0.025 | ≈ $0.040 | ≈ 20 min (token limit) |
| Batched, one call per question | 55 | ≈94K (72K in, 22K out) | ≈ $0.012 | ≈ $0.018 | ≈ 12 min |
| Non-LLM extractors | 0 | — | $0 | $0 | seconds |

The per-chunk arm alone uses about 79% of a 200K daily token quota (plan UNVERIFIED), so the run must be resumable, throttled client-side, and recorded across two days if needed. Sonnet 5.5 for the per-chunk arm would be about $0.79; not recommended for a high-volume step (foundation §6.4). All arms replay with no key once recorded. The structured (JSON) form of the batched call needs Groq structured-output support for the configured model, which I could not confirm this session (Groq docs blocked): **UNVERIFIED**. The foundation lists the Groq structured-outputs page as checked; confirm that it covers `gpt-oss-20b` before relying on it. Fallback: delimiter-based output parsed in code.

**Tracing.** Per chunk: the original and the extract (corpus D only; otherwise ids and counts), tokens before and after, verbatim flag, empty flag, interval, `prompt_version`, `cache_key`, latency, cost. Per question: calls made, whether the sync path ran sequentially.

**Dataset and evaluators.** The same golden set. Code evaluators: tokens, ratio, verbatim rate, CE on the final context vs before, dropped-digit count, empty rate, plus EM/F1 and citation page-hit. Faithfulness by human labels (about 10 answers read per version, D-10). Experiment: v4.0 champion vs {truncate, BM25-sentence, cosine-sentence, LLM per-chunk or batched}, at equal pre-registered settings; two-sided primary (tokens, correctness) with a non-inferiority margin; guards as in 06 v4.1.

**Cost / latency / token tracking.** Cost per question, calls per question, p50/p95 added latency, tokens saved. Report "cost if called" and "cost paid" (foundation §6.1).

**Versioning.** `prompts/compress_v1.txt` (never edited after first use); config: `compression: {method, model_id_resolved, max_completion_tokens, reasoning_effort, batched}`. The cache key already contains the rendered prompt.

**Monitoring and feedback.** Alerts: verbatim rate below 100% for extractive methods; any dropped digit on numeric items; empty-extraction rate jump; `finish_reason = length`; calls over budget. Failures go to M5 as "evidence dropped by compression" and become regression items.

**Lifecycle and skills.** Analyze: v4.0 traces (`error-analysis`) → Measure: `code-based-evaluators`, `rag-evaluation`, human labels → Improve: `improving-llm-agents` (cascade: cheap extractor first, LLM only when needed). Dev → CI (a replayed T1 check that extracts are substrings) → monitor page. Skills: `llm-observability`, `ci-cd-evals`, `improving-llm-agents`.

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Tokens | `tiktoken` | 0.14.0 | yes | yes | — | MIT | yes |
| Sentence scoring (BM25) | `rank-bm25` | locked | yes | yes | — | Apache-2.0 | yes |
| Sentence scoring (dense) | `sentence-transformers` MiniLM | locked | yes | yes (cached model) | — | Apache-2.0 | yes |
| Optional cross-encoder scoring | `cross-encoder/ms-marco-MiniLM-L-6-v2` | R3's model | via R3 | yes | — | Apache-2.0 | yes |
| Fuzzy verbatim match (optional) | `difflib` (stdlib) or `rapidfuzz` 3.14.6 | — | stdlib yes | yes | — | MIT | yes |
| LLM extractor (default) | Groq `openai/gpt-oss-20b`, `reasoning_effort=low`, enough `max_completion_tokens` | per `.env` | yes | no | table above | — | yes |
| LLM extractor (Claude) | Haiku 5.5 `claude-haiku-5-5`, effort `low` | via foundation | no | no | ≈$0.04 per 220-call run | — | optional |
| Framework core | `langchain-core` (`BaseDocumentCompressor`, `RunnableLambda`) | 1.6.6 | no | yes | — | MIT | yes |
| Read-only | `langchain-classic` (`LLMChainExtractor`, `ContextualCompressionRetriever`) | 1.0.8 | no | yes | — | MIT | read the source; **do not install** |
| Not recommended | `llmlingua` | 0.2.2 (2024-04) | no | needs a model download | — | MIT | skip: torch, transformers, accelerate, nltk |
| Tracing | JSONL; `langsmith` 0.14.4 (corpus D only); `arize-phoenix-otel` 0.17.2 | — | no | partly | — | MIT / Apache-2.0 | yes |

- **Install lines:** none beyond the foundation's (do not run). **Keys:** `GROQ_API_KEY`; optionally `ANTHROPIC_API_KEY`, `LANGSMITH_API_KEY`.
- **Framework needed at all?** No. LangChain only for the LLMOps notebook.
- **LLM features:** the batched variant benefits from JSON output; support on the configured Groq model is **UNVERIFIED** (docs blocked here).

### 11. Open questions for Yash (preferences only)
- Per-chunk, batched, or non-LLM first? (decision 1.)
- Should the verify notebook show the LLM extractor at all, or keep it in the LLMOps notebook only? **Suggestion:** keep the verify notebook LLM-free except one replayed example.

---

## Concept X3: Context assembly (dedup, ordering, token budget, citation formatting)

### 1. Sources checked

**Book pages (UNVERIFIED here):** no chapter. Fragments per 02: Ch8 p.5/11 (overlap-aware joining) and Ch22 p.11/19 (noise sensitivity). Fragments per 04: Ch5 p.10/14 (dedup of sub-query results), Ch8 p.5/11, Ch10 p.12/13 (context-window tokens). The two lists differ (X3-E3). Ch22 p.5/19 and Appendix p.15/23 carry the book's one position claim (documents that come first get more weight), per the P7 lesson.

**Repo notebooks and cells (from 04; UNVERIFIED here):** `HyPE_Hypothetical_Prompt_Embeddings.ipynb` cell 19 (`set()` dedup, loses order); `memorag.ipynb` cell 28 (order-preserving dedup); `graph_rag.ipynb` cell 12 (`max_context_length` defined but unused); `multi_faceted_filtering.ipynb` cell 20 (near-duplicate filter). 04 itself says (REVIEWER NOTE R-2) that these are fragments and no source compares them.

**Existing course files read:** 02 X3; 03 (stage 13; X3 ← I1, R3 and the "Pre" mismatch); 04 X3 row; 06 §3.3 (v0 template and `[doc_id:page]` labels), §3.4, §2.3, §2.5, §7.2–7.3, v4.0; C5 lesson (D.1, D.2, D.4–D.7, H.3 and IA-1, IA-3, IA-4, IA-5); P7 lesson (D.4 budget and answer reserve, D.5, D.6 lost in the middle, J4); misconception log MC-003, MC-004, MC-005; EXTERNAL_RESOURCES_REVIEW (the SDG/AIQ position notes: "lost in the middle is a reading effect on the generation side, not retrieval quality", and the sliding-window direction error); foundation §2.3, §3.3, §6.

**AE book sections:** none located specific to X3; `rag-evaluation` context swapping is the relevant method (named in the foundation; not checked here). **Interview-repo items:** guide absent.

**External sources:** [1] Liu et al. (snippet); [8] Yu et al., OP-RAG (snippet); [9] Jin et al. (secondhand); [2] Cuconasu et al. (snippet); [17] Anthropic long-context tips (**verified**); [18] Anthropic contextual retrieval (**verified**); [19] Anthropic Citations (**verified**); [20] Anthropic search-result blocks (schema **verified**); [15] LangChain `stuff` chain and `format_document` (**verified**); [11] a 2026 reproduction of position effects (snippet).

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | **The assembler as a pure function with named stages** (dedup → order → fit → label) and a trace per stage | whole concept | Not taught | X3 | — | **core** | One diagram and one signature. Each stage returns what it dropped and why. |
| 2 | **Exact duplicates** (same `chunk_id`) | multi-query, hybrid | `set()` in the repo loses order | X3 | — | core | Order-preserving dedup by id. |
| 3 | **Overlap duplicates** (two chunks share 200 characters) | any k > 1 | 03 §483 | X3/X1 | — | **core** | Interval union in document coordinates; count duplicate characters. Link to X1. |
| 4 | **Near-duplicates** (the same passage in two places, boilerplate) | multi-document corpora | the repo's `multi_faceted_filtering` cell 20 | X3 | — | core (Full) | A cosine or shingle-Jaccard threshold; say that a fixed threshold needs checking (MC-006 calibration warning). |
| 5 | **Rank vs position**: the order of retrieval is not the order in the prompt | ordering | P7 D.6 | P7 | No | bridge | Two fields in the trace: `rank` and `position`. |
| 6 | **Ordering policies**: rank order; document order; edges-first (best at both ends); reverse | the ablation | P7 D.6 has edges-first `[1,3,4,2]` | X3 | — | **core** | Define each as a permutation function. Prove the middle positions for k = 4 are ranks 3 and 4 in edges-first (P7 quick check). |
| 7 | **Lost-in-the-middle evidence and its scope** | why ordering is tested | P7 D.6 (no numbers) | P7 | No | bridge | Link, plus the scope warning: measured on long contexts of 2023 models; our k = 4 context is short. |
| 8 | **Token budget with an answer reserve**: `budget = window − reserve − prompt overhead` | the fit step | P7 D.4 | P7 | No | **core** | Re-teach in four lines with the numbers C5 measured (system 107, user 695, total 802 tokens for four chunks). |
| 9 | **Hard vs silent truncation**: drop whole blocks by priority; never cut mid-sentence; record `truncated_chunks` | budget overflow | C5 IA-4 says 0 in v0 | X3 | — | **core** | Policy: fill by priority until the next block does not fit; skip it and try smaller ones? No: stop, and log. State the choice. |
| 10 | **Which tokenizer counts** (local `o200k_harmony` vs provider usage) | the budget | C5 IA-3: they differ by template overhead | P1/C5 | P1 exposed | bridge | Count locally for decisions, compare with provider `prompt_tokens` in the trace. |
| 11 | **Reasoning tokens are not in the input budget but are in the output cap** | `max_completion_tokens` | P1/C5 D.3 | P1 | exposed | bridge | One reminder: the reserve is for reasoning plus the answer. |
| 12 | **k under a budget**: fixed k vs fill-to-budget | outcome 3 of 02 | MC-005 | X3 | — | **core** | Show both rules on the same retrieval lists; a table of k vs context tokens (the C4 lab idea). |
| 13 | **Stable labels** `[doc:page]` and their meaning | citations | 06 §3.3; C5 D.4 | C5/P7 | No | core | Keep the format; fix the rules for merged blocks. |
| 14 | **Label drift** | merged, windowed or compressed blocks span pages; two blocks share a page | C5 resolves a label to *all* retrieved chunks on that page | X3 | — | **core** | Rule: a block never spans pages in its label; split by page (`page_segments`) into sub-blocks, or label with the first page and list the other in a second field. Choose one (see §6). |
| 15 | **Block format**: plain headers vs XML tags | prompt text | Anthropic suggests `<document index>`, `<source>`, `<document_content>` [17] | X3 | — | core (Full) | Keep v0's plain format (the template is versioned); mention XML as a model-specific option, not an upgrade. |
| 16 | **Where the question goes** (after the sources) | prompt | Anthropic: query last helps on long inputs [17] | P7/C5 | No | bridge | C5 already puts it last. One sentence. |
| 17 | **Provider-native citations** (Claude Citations, `search_result` blocks) | an alternative to text labels | not taught | X3 / V1 | — | next | Short comparison box (see §5); defer to V1. |
| 18 | **Determinism**: ties broken by `chunk_id`, shuffled input → same output | trace and cache | 06 line 412 | X3 | — | core | A property test. |
| 19 | **Prompt caching and block order**: stable prefix first | cost | foundation §6.2 | D2 | No | next | One line, link to D2. |
| 20 | **Retrieved text is untrusted**: delimiters are not a defence | safety | D4 | D4 | No | next | One line, link to D4. |
| 21 | **CE@k vs Precision@k** with overlapping chunks: Precision rewards redundancy | metric choice | 06 §7.3 | M2 | exposed | bridge | Use it to justify dedup as a metric-clean step. |
| 22 | **Metadata cost**: titles and headings in each block add tokens | block format | not taught | X3 | — | core (Full) | Count them in the budget; test on/off. |

### 3. Quiz coverage

No `study/questions/X3_questions.md`. Needed titles:
- **PRE:** X3-PRE-01 "List the four decisions made between retrieval and the prompt."; X3-PRE-02 "Chunk overlap vs the prompt: which stage does each belong to?" (MC-003).
- **R:** X3-R-01 "Why is `set()` a bad dedup here?"; X3-R-02 "Rank vs position: define both."; X3-R-03 "What is the answer reserve for?"; X3-R-04 "Why does a merged block need a label rule?"
- **A:** X3-A-01 order four blocks with edges-first and name the middle ranks (MC-004, P7 check); X3-A-02 compute the budget and the k that fits from a given template and window; X3-A-03 merge three overlapping chunks and report duplicate characters removed; X3-A-04 compute which labels resolve for a given answer and blocks (C5 rules).
- **T:** X3-T-01 "the answer cites page 11 but the evidence is on page 10: trace the cause"; X3-T-02 "the context grew after enabling windows: where did the overflow go?"; X3-T-03 "design an ordering experiment: what k, what items, what counts as a win?"
- **Interview:** X3-R-05 "How do you decide what goes into the prompt and in which order?"
- Short-mode rule: the stage list, the budget formula, the rank-vs-position distinction and the label rule must be in Short.

### 4. Errors found in existing material (not edited)

| # | Where | Problem |
|---|---|---|
| X3-E1 | 02 X3 (Pre: C5, P7, R3) and 04 row vs 03 registry (X3 requires I1, R3) | Prerequisite lists disagree (C5, P7 vs I1). Both could be true, but the sources should say which are `requires_all`. |
| X3-E2 | 06 v4.0 arms vs 02 X3 outcome "run an ordering ablation" | v4.0 lists three arms (champion, ±1, ±1 + dedup) and no ordering arm. The ablation has no home in 06. |
| X3-E3 | 02 X3 fragments (Ch8 p.5/11, Ch22 p.11/19) vs 04 (Ch5 p.10/14, Ch8 p.5/11, Ch10 p.12/13) | Different fragment lists. Neither checked here. |
| X3-E4 | C5 H.3 comment "prompt order = rank order"; IA-1 "sort by rank"; IA-4 `truncated_chunks = 0` | Correct for v0, but X3 changes all three. The record needs a `position` field and a `dropped` list. |
| X3-E5 | C5 IA-5 / 06 §2.5 (`page` = first page segment) | A block that spans two pages is labelled with the first page. V1's citation check (Phase 8) would then mark a correct citation of the second page as unsupported or as "retrieved but wrong page". |
| X3-E6 | C5 D.2 (blocks labelled `[i] (doc_id:page)`, citation by `doc_id:page`) | A fixed label can be shared by two *non-adjacent* blocks on the same page after dedup and ordering. `resolved_chunk_ids` handles that, but the trace should keep both block ids. |
| X3-E7 | P7 lesson "the book's only position claim" / 02 "position effects are not in the book" | Already corrected inside P7 (G.2). Noted for completeness: the claim lives on Ch22 p.5/19 and App p.15/23 (UNVERIFIED here). |
| X3-E8 | LangChain default `format_document` / "stuff" chain [15] | The default document prompt is `{page_content}` only, joined with `"\n\n"`. Metadata (page, source) is dropped unless you pass a custom prompt. If a notebook uses the default, labels vanish silently. |
| X3-E9 | Review notes on SDG/AIQ position claims (EXTERNAL_RESOURCES_REVIEW §8) | The review says rerankers "fix" lost in the middle in the SDG guide, and that AIQ labels it retrieval quality. Both are wrong per the review. The lesson should not repeat them. |

### 5. What the research says

**Verified**
- **Anthropic prompting guidance** [17]: long documents first, query last; structure many documents with `<document>` tags that include a source; ask for quotes before answering. The "up to 30%" figure is Anthropic's own testing on 20K+ token multi-document inputs; do not transfer it to a 1K-token context.
- **Anthropic contextual retrieval** [18]: their pipeline passes the top **20** chunks after reranking 150, and reports 20 beating 10 and 5 *in that pipeline*. Meaning: k under a budget is something you measure, not a constant. Our v0 k = 4 is a baseline, not a recommendation.
- **Anthropic Citations** [19]: plain-text and PDF documents are split into sentences that can be cited; `cited_text` does **not** count toward output tokens; citations are incompatible with structured outputs (the API returns a 400 if both are on); "custom content" documents are used as given with no further chunking, so a RAG chunk can be one citable unit. `search_result` blocks [20] carry `source`, `title` and `content` and give each citation the source and title you supplied. Meaning: a provider-native route exists for Claude, but the course's own text labels keep the Groq default and keep verification in our code (V1). Defer.
- **LangChain `stuff` chain defaults** [15]: `DEFAULT_DOCUMENT_PROMPT = {page_content}`, separator `"\n\n"` (X3-E8).

**Papers (UNVERIFIED here; snippets only)**
- **Liu et al. 2023 / TACL 2024** [1]: see X1. For ordering, the finding is about *where* a single relevant item sits among many documents. The course checked the tables in an earlier review; this session could not.
- **Yu et al., "In Defense of RAG in the Era of Long-Context LLMs" (OP-RAG), arXiv 2409.01666** [8]. *Idea:* keep retrieved chunks in their **original document order** instead of relevance order. *Result (secondary summaries):* answer quality rises and then falls as more chunks are added (an inverted U); on one long-QA benchmark, OP-RAG with Llama 3.1-70B scored F1 44.43 at about 16K tokens against 34.32 for the full 128K context, and 44.43 vs 38.40 for relevance-ordered RAG at 128 chunks. *Limits:* figures come from secondary summaries; very long contexts (16K+ tokens), not ours. *Meaning:* "document order" is a real ordering arm and a k sweep is a real experiment, but both are tested at sizes far above ours.
- **Jin et al., "Long-Context LLMs Meet RAG", arXiv 2410.05983** [9]. *Reported (secondhand):* more retrieved passages first help then hurt; placing top-scoring passages at the edges ("retrieval reordering") helps mainly when many passages are retrieved and gives negligible gains for small sets. *Limits:* secondhand; I did not open it. *Meaning:* this supports the plan to run ordering at a larger k.
- **Cuconasu et al. 2024** [2]: see X2. For assembly: high-scoring *non-answer* documents hurt; so "which blocks to include" matters more than "how to order them" when distractors are close.
- **A 2026 reproduction** ("Lost in the Evidence?", arXiv 2605.27105) [11], snippet only: topic sampling strongly affects results and small topic sets can hide or exaggerate ordering effects. Meaning: our small eval set may show nothing or something spurious. Report that.
- **Chroma 2025** [10], snippet: reliability falls with length; secondary only.

**Current practice (my interpretation).** Assembly in production code is mostly an explicit step: dedup by id or by span, keep a token counter, drop lowest-priority blocks when over budget, and number the sources. Ordering policies are cheap to try and usually small. Native citation features are now in the provider APIs. The risk that does not go away is label drift.

**Pitfalls (with evidence)**
- `set()` dedup destroys order (04, repo cell 19).
- A `max_context_length` that is defined and never applied (04, repo cell 12): the budget exists only if a test fails when it is exceeded.
- Silent truncation: C5 v0 has none by design (06 §3.4), so overflow would surface as an API error or a cut prompt, not a flag.
- The default LangChain document formatting drops labels (X3-E8).
- Reordering can make a human-readable context incoherent (fragments out of document order), so the reorder must keep the block boundaries and labels intact.

**How to evaluate**
- **Deterministic:** assembler unit tests (never over budget, deterministic, no duplicate offsets, every label resolves), CE on the final context, duplicate characters, truncation rate, tokens per context (p50/p95).
- **Answer side:** human labels on changed answers, citation page-hit, EM/F1 on short answers; the ordering ablation reports the position of the evidence block per item.
- **Baselines:** v0 (rank order, k = 4, no budget) and the best v3 champion. For ordering: rank order is the baseline.
- **Design of the ordering ablation:** only items whose evidence sits in exactly one block (position is then well defined); k = 4 and one larger k (for example 10); four policies; the same retrieval lists; answers cached. Expect a null at k = 4.

**Interview questions (mine; not checked against the interview guide)**
1. How do you decide what goes into the prompt after retrieval, and in what order?
2. How do you enforce a token budget and what do you drop first?
3. How do you keep citations correct after merging chunks?
4. What is "lost in the middle" and how would you test it on your own data?
5. How would you detect duplicate or near-duplicate context?

### 6. Lesson blueprint

**The answer first (draft, 5 sentences)**
1. Between retrieval and the model, the system must decide what text goes in, in what order, how much, and how each piece is labelled.
2. Four small steps do that: remove duplicates, order the blocks, fit them to a token budget, and attach stable labels.
3. Duplicates include overlapping chunks, so the cleanest dedup is a union of document-offset intervals.
4. The budget is the context window minus the answer reserve and the prompt overhead, and anything dropped must be recorded, never silently cut.
5. Order and k are things you test on your own data: "lost in the middle" is a long-context finding, and a 700-token context may show nothing.

**The theory in one read (about 10 ideas)**
1. The assembler: `assemble(candidates, policy) → blocks, dropped, report`, a pure, deterministic function.
2. Candidates and blocks: a block is an interval, its text, its page segments, its origin, its best rank, its tokens.
3. Dedup: exact id; interval union for overlap; optional near-duplicate threshold.
4. Rank vs position and the ordering policies (rank, document, edges-first).
5. The budget formula and the answer reserve.
6. Fit policy: fill by priority; whole blocks only; log the drops.
7. k under a budget: fixed k vs fill-to-budget.
8. Labels: `[doc_id:page]`; the rule for blocks that cross pages; the trace keeps block ids and chunk ids.
9. What the experiment can show: the position effect at small and large k; noise vs coverage.
10. Failure modes: duplicate overlap, budget overflow, evidence mid-context, label drift.

**Formula-sheet items**
- `budget = window − reserve − overhead(template, question)`
- `fits(block) = used + tokens(block) ≤ budget`
- `edges_first([1,2,3,4]) = [1,3,4,2]` (best at both ends; middle = ranks 3 and 4 for k = 4)
- `dup_chars = Σ lengths(blocks) − |union of intervals|`
- `context_tokens = Σ tokens(block) + separators`

**Step-by-step outline (running example: Corpus D, top-6 for one question with two overlapping hits).**
1. List the six candidates with ranks, intervals and token counts.
2. Remove exact duplicates, then merge overlapping intervals; count duplicate characters.
3. Order with each policy; draw the positions.
4. Fit to a 720-token budget (and then 1,500); show what was dropped and why.
5. Label: a merged block crossing pages 10–11; show the label rule and the C5 check.
6. Show the final trace record.
7. The ordering experiment design, as a plan, not a result.

**Visuals that earn their place**
- The assembler pipeline with what each stage can drop: shows the order of operations (and why compression sits between dedup and fit).
- Position strip for the three orderings with the evidence block highlighted: shows rank vs position.
- Budget bar: window, reserve, overhead, context, with drops marked: shows where overflow happens.
- Label resolution diagram: a two-page block and which citation resolves: shows label drift.

**Full-only details:** near-duplicate detection; XML block format; metadata cost; the Claude Citations and search-result routes; the OP-RAG and reorder papers in detail; prompt-caching order.

### 7. Verify notebook plan

- **File:** `study/notebooks/X3_assembly_verify.ipynb`. Offline in replay. Runtime under 1 minute for the deterministic part.
- **Recomputes (no LLM):** exact vs `set()` dedup (order lost, shown); interval union and duplicate characters on real overlapping chunks; the three ordering permutations and the positions of each rank for k = 4, 6, 10; the budget arithmetic with `o200k_harmony` and the C5 measured numbers (802 total for four chunks); the overflow case (k large) showing what each fit policy drops; label resolution for a two-page block under the candidate rules; determinism (shuffled input gives identical output).
- **Optional measured part (LLM, recorded once):** the ordering ablation on **≤ 10 items with a known evidence block** × 3 policies × k ∈ {4, 10} = **≤ 60 Groq calls**; report as exploratory with the 2026 reproduction's warning (small topic sets).
- Charts: Plotly.

### 8. Apply-it tool plan and real-world checklist

- **Tool:** `study/tools/context_budget_check.py`. **Inputs:** retrieval results JSONL (`qid`, ranked chunks with offsets, page segments), the prompt template, a window size and answer reserve, an ordering policy. **Outputs:** per-question token breakdown, a list of overflows, duplicate characters, near-duplicate pairs, label collisions, the position of the gold block, and the k that fits.
- **Recommendation logic:** "set a hard budget" if any question overflows; "merge overlaps" if duplicate characters exceed 5% of context; "try edges-first / reduce k" only if the median context is large (for example above 2,000 tokens) and gold blocks sit in the middle positions for a clear share of failing questions; "split blocks at page boundaries" if any block's page segments span more than one page.

| # | Check | Mode |
|---|---|---|
| 1 | Token breakdown: system, template, sources, question, reserve | auto |
| 2 | Does any question overflow the budget? | auto |
| 3 | Is any block dropped silently (dropped without a record)? | auto |
| 4 | Duplicate characters after dedup (should be 0) | auto |
| 5 | Near-duplicate pairs above a similarity threshold | auto |
| 6 | Same label used by non-adjacent blocks | auto |
| 7 | Blocks whose page segments cross a page boundary | auto |
| 8 | Position of the gold block under each policy | auto (needs gold) |
| 9 | k that fits at your budget; compare with your current k | auto |
| 10 | Rank-vs-position: does your pipeline keep both in the trace? | auto |
| 11 | Read three assembled prompts end to end: is it coherent? | manual |
| 12 | Do your documents contain instructions that might be read as commands? | manual (D4 link) |

### 9. LLMOps notebook plan

File: `study/notebooks/X3_assembly_llmops.ipynb`.

**Framework build**
- The assembler is plain Python; the notebook wraps it as a `RunnableLambda` in an LCEL chain: retriever → `assemble` → `ChatPromptTemplate` → `CachedChatModel`. Maps to the lesson's four stages.
- **Framework defaults the lesson warns about:** the "stuff" chain's `{page_content}`-only document prompt and `"\n\n"` separator drop labels (X3-E8); `VectorStoreRetriever` default `k=4` and `similarity` (foundation §9.2); no token budget exists anywhere in the default chain. Show the default output beside ours.
- **LCEL, no LangGraph** (no cycle, branch or checkpoint).
- Anthropic's `search_result` / Citations route is shown as a read-only comparison cell, not run.

**Caching.** Calls: Groq generation for the arms of the ordering ablation: 4 policies × 46–55 questions ≈ **185–220 calls** at k = 4, plus the same at k = 10 if approved (decision 3), and the budget arms (fixed k vs fill-to-budget, 2 × 55 = 110). Many arms share answers when the assembled context is identical (the cache key contains the full messages), so identical contexts cost nothing. Assumed tokens per call ≈ 1,000 in + 400 out at k = 4 (≈77K tokens per arm), ≈ 2,200 in + 400 out at k = 10 (≈143K per arm); Groq `gpt-oss-20b` ≈ $0.011 and ≈ $0.016 per arm; Haiku 5.5 ≈ $0.017 and ≈ $0.023; the daily quota (200K, plan UNVERIFIED) allows about two arms a day, so the ablation needs several days or a throttle. All replay with no key once recorded.

**Tracing.** The context span from the foundation §3.3, extended with: `blocks[]` (id, origin, interval, source chunk ids, rank, position, tokens), `dropped[]` (id, reason: `dup` / `overlap_merged` / `budget`), `budget` (window, reserve, overhead, used), `policy` names, `label_map`. Content stored for corpus D only; otherwise ids and counts.

**Dataset and evaluators.** Golden set with two new tags: `single_evidence_block` (position well defined) and `straddles`. Code evaluators: budget never exceeded (property test), duplicate characters = 0, labels resolve, CE on the final context, tokens, truncation rate, EM/F1 and citation page-hit. Human labels on changed answers. Experiments: (a) fixed-k vs fill-to-budget at the same budget; (b) ordering ablation; (c) dedup on/off. Pre-register each, with the paired bootstrap.

**Cost / latency / tokens.** Assembly itself is deterministic and costs no calls. Track context tokens p50/p95, number of dropped blocks, prompt tokens from provider usage vs local count (they differ by template overhead, C5 IA-3).

**Versioning.** Policy and budget in the config YAML (`context: {dedup, order, budget_tokens, reserve_tokens, label_scheme}`); `answer_v1.txt` unchanged except where the label scheme requires a template version bump (a new file, never an edit).

**Monitoring and feedback.** Alerts: any overflow, any drop reason `budget` above a set rate, duplicate characters above 0, unresolved labels, `finish_reason = length`. A citation that points at the wrong page, or evidence dropped by the budget, goes to M5 as "label drift" / "evidence dropped by budget" and becomes a regression test (replay marker).

**Lifecycle and skills.** Analyze: `error-analysis` on v3 traces (evidence present in retrieval but absent from the answer) → Measure: `rag-evaluation` (context swapping separates retrieval from generation), `code-based-evaluators` → Improve: `improving-llm-agents` → CI: `ci-cd-evals` token-budget test → monitor: `llm-observability`.

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Token counting | `tiktoken` `o200k_harmony` | 0.14.0 | yes | yes | — | MIT | yes |
| Interval and dedup logic | stdlib + `numpy` | locked | yes | yes | — | — | yes |
| Near-duplicate (optional) | cosine on cached vectors; `datasketch` 2.0.0 (MinHash) | — | cosine yes | yes | — | MIT | cosine yes; MinHash is overkill at 97 chunks |
| Fuzzy matching (optional) | `rapidfuzz` 3.14.6 / `difflib` | — | stdlib yes | yes | — | MIT | optional |
| LLM (ablation answers) | Groq `openai/gpt-oss-20b`, `reasoning_effort=low`, `max_completion_tokens` | per `.env` | yes | no | ≈$0.011–0.016 per arm | — | yes |
| LLM (comparison) | Sonnet 5.5 / Haiku 5.5 | via foundation | no | no | ≈$0.33 / $0.017 per arm | — | optional |
| Framework core | `langchain-core` (`RunnableLambda`, `ChatPromptTemplate`) | 1.6.6 | no | yes | — | MIT | yes |
| Native citations (read-only) | Anthropic Citations / search-result blocks | API | — | no | — | — | defer to V1 |
| Tracing | JSONL; `langsmith` 0.14.4; `arize-phoenix-otel` 0.17.2 | — | no | partly | — | MIT / Apache-2.0 | yes |
| Statistics | `numpy` paired bootstrap; `scipy` 1.18.1 optional | — | numpy yes | yes | — | BSD | yes |

- **Install lines:** none beyond the foundation's (do not run). **Keys:** `GROQ_API_KEY`; optionally `ANTHROPIC_API_KEY`, `LANGSMITH_API_KEY`.
- **Framework needed at all?** No for the lesson and verify notebook.
- **LLM features:** nothing special; plain chat completions.

### 11. Open questions for Yash (preferences only)
- Label rule for a block that crosses a page: **split into one block per page**, or **label with the first page and add a second field**? **Suggestion:** split by page, because it keeps one label per citable page and keeps V1's check exact.
- Should dropped-by-budget policy be "stop at the first block that does not fit" or "skip it and try smaller ones"? **Suggestion:** stop (simple, predictable, ordered by priority); log the rest.

---

## Phase-level notes

**1. Teaching order.** 02 says X1 is taught concurrently with X3; 03 says X1/X3 → X2. My suggestion: split X3. **X3-core** (intervals, dedup, budget, rank vs position) first and in Short; then **X1**; then **X2**; and **X3-ordering-and-labels** last (Full), because the label rule needs the merged blocks from X1 and the compressed blocks from X2.

**2. One shared design: `context.py` (a plan).**

| Stage | Input → output | Can drop | Trace fields |
|---|---|---|---|
| Retrieve (existing) | question → ranked chunks | — | as 06 §2.5 |
| Expand (X1) | hits → window intervals, or RSE runs | — | origin, intervals |
| Dedup/merge (X3) | intervals → union | duplicates | dup characters |
| Compress (X2, optional) | blocks → shorter blocks (verbatim, re-aligned) | sentences, empty blocks | tokens before/after, verbatim |
| Order (X3) | blocks → positions | — | rank, position, policy |
| Fit (X3) | blocks → within budget | lowest priority whole blocks | dropped, budget |
| Label (X3) | blocks → text with labels | — | label map |

Compression sits **before** the fit (so the budget sees the real length) and **after** the dedup (so duplicates are not paid for twice).

**3. Data model that all three need.** Every block carries `doc_id`, `[doc_char_start, doc_char_end)` in document offsets, `page_segments`, source chunk ids, origin, best rank, tokens, and a content hash. With this, CE on the final context is one function for all three concepts, and compression is scorable only if its output re-aligns to an interval.

**4. The straddle audit is a gate for X1.** Run it once the eval set exists. If no gold group straddles two chunks, X1's retrieval-side benefit is nil on this corpus and the experiment should be reported as not applicable.

**5. Statistics.** Dev sets of 46–100 items give wide intervals; X1, ordering and compression effects will often be inside the noise. Pre-register one primary metric per concept; report the ordering ablation as exploratory (06 §9.4 and the 2026 reproduction's caution).

**6. Rate limits shape the plan.** Groq's listed quotas (30 requests/min, 8K tokens/min, 200K tokens/day; plan UNVERIFIED) allow roughly two answer-generation arms a day. A three-concept phase with about eight arms needs several days, a resumable runner, and the cache.

**7. Changes this phase forces elsewhere (reported, not made)**
- **C5/06 §2.5:** add `position`, `dropped`, `budget`, `label_map`; drop the "prompt order = rank order" assumption; define labels for multi-page blocks.
- **M2/06 §7.3:** a CE-on-final-context function that takes intervals, not chunk ids.
- **V1 (Phase 8):** citation verification must accept the new labels.
- **D2 (Phase 9):** prompt-cache friendliness of block order.
- **D4 (Phase 9):** retrieved text and the compressor as an injection surface.
- **I1/I-CMP (Phase 4):** overlap and window are two ways to pay for the same text; the equal-budget protocol should be shared.

**8. Skills.** `.claude/skills/` was not present in this checkout; the skill names and methods above come from the foundation file.

---

## Sources

Status key: **verified** = opened and checked in this session; **UNVERIFIED** = seen only in a search snippet, a README, or a course file.

1. N. F. Liu et al., "Lost in the Middle: How Language Models Use Long Contexts", TACL 12:157–173 (2024), arXiv 2307.03172. https://arxiv.org/abs/2307.03172 — **UNVERIFIED** (blocked; search snippet; the course read the abstract on 2026-10-08 and the Appendix G table in an earlier review).
2. F. Cuconasu et al., "The Power of Noise: Redefining Retrieval for RAG Systems", SIGIR 2024, arXiv 2401.14887. https://arxiv.org/abs/2401.14887 — **UNVERIFIED** (snippet).
3. F. Xu, W. Shi, E. Choi, "RECOMP: Improving Retrieval-Augmented LMs with Compression and Selective Augmentation", ICLR 2024, arXiv 2310.04408. https://arxiv.org/abs/2310.04408 — **UNVERIFIED** (snippet).
4. H. Jiang et al., "LLMLingua", EMNLP 2023. https://aclanthology.org/2023.emnlp-main.825/ — **UNVERIFIED** (README only).
5. H. Jiang et al., "LongLLMLingua", ACL 2024. https://aclanthology.org/2024.acl-long.91/ — **UNVERIFIED** (README only).
6. Z. Pan et al., "LLMLingua-2", ACL 2024 Findings. https://aclanthology.org/2024.findings-acl.57/ — **UNVERIFIED** (README only).
7. microsoft/LLMLingua README. https://raw.githubusercontent.com/microsoft/LLMLingua/main/README.md — **verified**.
8. Z. Yu et al., "In Defense of RAG in the Era of Long-Context Language Models" (OP-RAG), arXiv 2409.01666. https://arxiv.org/abs/2409.01666 — **UNVERIFIED** (snippets).
9. B. Jin et al., "Long-Context LLMs Meet RAG: Overcoming Challenges for Long Inputs in RAG", arXiv 2410.05983. https://arxiv.org/abs/2410.05983 — **UNVERIFIED** (secondhand summary).
10. Chroma Research, "Context Rot: How Increasing Input Tokens Impacts LLM Performance" (2025). https://research.trychroma.com/context-rot — **UNVERIFIED** (snippet).
11. "Lost in the Evidence? Reproducing Document Position and Context Size Effects in RAG", arXiv 2605.27105 (2026). https://arxiv.org/html/2605.27105 — **UNVERIFIED** (snippet; ID as returned by the search).
12. D-Star-AI/dsRAG, `dsrag/rse.py` (main). https://raw.githubusercontent.com/D-Star-AI/dsRAG/main/dsrag/rse.py — **verified**. (dsRAG README benchmark figures: **UNVERIFIED**, snippets conflict.)
13. dsRAG on PyPI, 0.5.6 (2025-11-10). https://pypi.org/project/dsrag — **verified** (PyPI JSON).
14. LangChain `langchain_classic/retrievers/` (`contextual_compression.py`, `document_compressors/chain_extract.py`, `chain_extract_prompt.py`, `embeddings_filter.py`; `parent_document_retriever.py` listed only). https://github.com/langchain-ai/langchain — **verified** (raw source, master, 2026-10-18).
15. LangChain `langchain-core` (`documents/compressor.py`, `prompts/base.py` `format_document`), `langchain-text-splitters` (`base.py`), `langchain_classic/chains/combine_documents/stuff.py` — **verified** (raw source).
16. LlamaIndex `llama_index/core/node_parser/text/sentence_window.py` and `postprocessor/metadata_replacement.py` (main). https://github.com/run-llama/llama_index — **verified**.
17. Anthropic, Prompting best practices (long-context section; the old `long-context-tips` URL redirects to it). https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices — **verified**.
18. Anthropic, "Introducing Contextual Retrieval". https://www.anthropic.com/news/contextual-retrieval — **verified**.
19. Anthropic, Citations. https://platform.claude.com/docs/en/build-with-claude/citations — **verified**.
20. Anthropic, Search results. https://platform.claude.com/docs/en/build-with-claude/search-results — **verified** (schema and introduction only).
21. PyPI JSON API for `langchain-classic`, `langchain-core`, `langchain-text-splitters`, `llama-index-core`, `llmlingua`, `dsrag`, `tiktoken`, `scikit-learn`, `scipy`, `rapidfuzz`, `datasketch`, `nltk`, `pysbd`, `spacy`. https://pypi.org/pypi/<name>/json — **verified** 2026-10-18.
22. Course files read: `LLMOPS_FOUNDATION.md`; 02 (X1–X3 cards, Phase 7 table); 03 (stage 13, rows, notes); 04 (Ch8, Ch10, X3 fragments, DV-21/22/24, R-2); 06 (§2.3, §2.5, §3.3, §3.4, §7.2–7.3, v4.0, v4.1); 08 (D-04, D-09, D-10, D-11, D-16, D-18 as quoted); 01 §contents rows for Ch8 and Ch10; `concepts/C5_generation_citations.md`; `concepts/P7_grounded_prompting.md`; `progress/concept_tracker.csv`; `progress/misconception_log.md`; `study/lessons/P3_bm25_gap_audit.md`; `sources/EXTERNAL_RESOURCES_REVIEW_2026-10-09.md`; `pyproject.toml`; `.gitignore`.
