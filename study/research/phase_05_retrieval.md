# Phase 5 research: Retrieval improvements → v2.x

**What this is:** the research and gap audit for Phase 5: R1 sparse vs dense vs hybrid with fusion, R2 metadata filtering, R3 reranking, R4 diversity (MMR / Dartboard) and R5 hierarchical retrieval (hierarchical indices, RAPTOR). It was done on 2026-10-17 by Claude in a Claude Code cloud session, with five research helpers, one per concept.
**What this is not:** lessons or code. Nothing in the course was changed and nothing was installed. No LLM, embedding, rerank or tracing API was called.

**How it was checked, and what could not be checked.** This session ran in a cloud container that differs from Yash's machine. Like the Phase 4 session, several inputs that RESEARCH_PROMPT §3 lists were **not available**, so read the labels with that in mind.
- **Book (*RAG Made Simple*): not present.** No book page was opened. Every book citation comes from 02, 03, 04, 08 or the existing R1 files and is labelled "per 04, not re-opened" (UNVERIFIED for this session). Where those files give different pages, this file reports the disagreement instead of settling it. No book text was read, so none can have been copied.
- **AI Eval book (AE): not present.** AE methods are used only as `sources/EXTERNAL_RESOURCES_REVIEW_2026-10-09.md`, `phase_03_measurement.md` and the R1 lesson summarise them.
- **`CLAUDE.md` and the project skills (`.claude/skills/`): not present.** The skill methods were applied as `LLMOPS_FOUNDATION.md` and `phase_03_measurement.md` describe them. Each LLMOps plan names the skill it follows.
- **Network:** raw GitHub, PyPI and some pages through the web-fetch tool were reachable. For example, Anthropic's Contextual Retrieval page opened. arXiv, ACM, ACL Anthology, OpenReview, Hugging Face and the Cohere and Groq docs sites were **blocked**. So most papers carry **"search-checked only (UNVERIFIED)"**: Cormack 2009, Bruch 2023, Nogueira & Cho 2019, RankGPT, Carbonell & Goldstein 1998, Dartboard, RAPTOR and ACORN. Their authors' code repositories were opened where they exist.
- **Upstream repos:** every cited notebook cell (0-based) and script line was opened at the pinned commit `009adba`. The same holds for the interview repo (AIQ @ `e080df2`, MIT, "Copyright (c) 2026 Om") and the official RAPTOR (`parthsarthi03/raptor` @ `7da1d48`) and Dartboard (`EmergenceAI/dartboard`) code.
- **Library behaviour** was read from released source: the wheel or tag is named at each citation. This covers `rank_bm25` 0.2.2, `langchain-core` 1.6.6, `langchain-classic` 1.0.8, `langchain-community` 0.4.2, `llama-index-core` 0.14.25, `sentence-transformers` 6.1.0 (the locked version), `cohere` 7.2.0 and scikit-learn. Pins come from the PyPI JSON on 2026-10-17, using the newest release on or before 2026-10-03.
- **Corpus D measurements** were made in the session scratchpad with poppler and the standard library: acronym counts, heading tree, chunks per chapter, and redundancy pairs. PyMuPDF, the embedders and the cross-encoder were not run here, so these numbers are approximate. R4's redundancy figures are a TF-IDF stand-in, not embeddings. Every verify notebook re-measures them on the PyMuPDF snapshot. Numbers quoted from `sources/verification/R1/R1_FACTS.md` come from earlier local runs and were not re-run.

**A local follow-up pass is needed** before any Phase 5 lesson is written. On Yash's machine, open the cited book pages (Ch12–Ch15, App) and settle the page disagreements listed in each concept's §4. Then re-open the search-checked papers and load the project skills named in each §9. This is a checking pass, not new research.

**Citation keys used below.**
- Book pages: `Ch13 p.6/13`.
- AE book: `AE ChN, 'section'`.
- Repo cells: `notebook.ipynb cell N` (0-based) at `009adba`.
- Interview repo: `AIQ 04 Q<n>`.
- External sources: **[R3-S5]** and so on, numbered per concept and listed per concept in the final Sources section.
- Error ids are per concept, for example `R4-E6`.

---

## Summary (read this first)

**The 5 most important gaps across the phase**
1. **On Corpus D, no v2.x experiment can reach a decision as planned, and three of its target question groups are too small or undefined.** About 30% of items go to dev (06 §6.3).
   - v2.0 targets exact-term and table/numeric items. That is about 10 items, with 3–4 on test. Even if all of them improve, the best exact sign-test p is 0.125 (R1-E4).
   - v2.3 targets multi-span items. About 2 of them reach dev, and seed D-005 fits inside one chunk (R4-E7).
   - v2.2's "scope-specified" items, the `scope` label and the oracle filter are never defined (R2-E3).
   - v8 (R5) reads a "global" group that 06 §6.2 does not have, and 02 and 06 name different groups (R5-E4).
   - **Fix:**
     - Grow the slices before the runs: a rule-built acronym probe set of about 21 items (R1); scoped items (R2); cross-page multi-span items such as Paris p.10 + p.23 (R4); chapter-level and whole-document ("global") items, at least 8 per split (R5).
     - Add a **headroom gate** to every card. It counts the items a perfect version of the technique could fix before any calls are spent; R3's seeds already show CE@4 = Hit@4 = 8/8 (R3-E8).
     - Pre-register "inconclusive" or "not indicated" as expected verdicts.
2. **The five stages change one pipeline, but the cards are written as if they were independent.**
   - v2.3's dense pool and cosine relevance clash with the v2.1 reranked champion, so two variables change at once (R4-E4).
   - v2.2 says nothing about how the filter combines with the BM25 and dense lists or with the rerank pool (R2-E8).
   - v2.0 must run on the **v1.x champion's** index units, and record which text BM25 indexes. That is `text` or I5's `bm25_text`, and today it goes unrecorded (R1-E5).
   - R5's v8 card does not say which champion it runs on.
   - **Fix:** one stage contract (Phase-level notes, item 1). The filter is applied to both lists before fusion. The rerank pool is the fused list. MMR runs on the reranked pool, using the reranker score normalised per query as relevance and cosine only for redundancy. Every stage stores `chunk_id`, rank, raw score and score kind.
3. **Settings that change results are not recorded, and the framework defaults hide them.**
   - 06's config and trace have no fields for:
     - fusion: list depth, rank base, tie rule, dedup key, BM25 text field;
     - the reranker: model revision, `max_length`, score kind, pre-rerank score, truncation, and the load vs scoring latency split;
     - diversity: no `diversify:` block at all;
     - filters: scope, fail-open vs fail-closed, empty result;
     - summary units: their provenance.
   - The library defaults silently change a comparison:
     - LangChain `EnsembleRetriever`: each list is 4 deep; it returns the whole union (up to 8 chunks, so hybrid wins on volume); it dedups by text, not chunk id.
     - `BM25Retriever`: `split()` with no lower-casing; returns zero-score chunks.
     - `CrossEncoderReranker`: `top_n=3`.
     - LangChain FAISS: post-filters the top `fetch_k=20`.
     - LlamaIndex `QueryFusionRetriever`: `num_queries=4`, i.e. hidden LLM calls; its RRF counts ranks from 0 and ignores the weights.
     - `load_summarize_chain`: two calls per document, with a hidden prompt.
   - LLMOPS_FOUNDATION §9.2 lists none of these (R1-E6/E10, R2-E11, R3-E6/E10, R4-E10, R5-E10).
4. **Several primary and guard metrics in the v2.x cards cannot show the effect or are undefined.**
   - Precision@4 can stay flat while a filter works (R2-E2).
   - Mean pairwise cosine drops under MMR by construction (R4-E6).
   - MRR@10 is undefined when MMR returns only 4 chunks (R4-E5).
   - v2.1's hypothesis says Hit@4 rises, while the card treats Hit@4 as a guard (R3-E8).
   - Nothing says how to score a hit on a summary (R5). If a summary is credited with its source spans, the root node "covers" every question. Only leaf text in the final context should count (R5-E8).
   - **Fix:** M2 gains these metrics:
     - CE@pool and oracle headroom;
     - BM25 content-term hits;
     - removed-gold and false-filter rates;
     - Group-Recall, α-nDCG with evidence groups as nuggets, and a redundant-evidence rate;
     - leaf-only scoring with the summary token share.
5. **Two mechanism facts are stated wrongly or not taught at all.**
   - **RRF's "consensus" on Corpus D is mostly stop words.**
     - `rank_bm25` replaces negative idf with a small positive floor, so "BM25 score > 0" does not mean a content word matched. BM25 lists hold 80–97 of the 97 chunks.
     - On D-008, 29 of the 30 chunks that appear in both top-50 lists are in the BM25 list only through "the".
     - The R1 lesson says the opposite (R1-E3).
   - **Reranker scores are not taught.**
     - The scale depends on the model: sentence-transformers applies a sigmoid unless the model config says otherwise, and ms-marco-MiniLM returns raw logits.
     - An LLM's 1–10 scores over 20 candidates must tie.
     - Listwise prompts have position bias.
     - The LlamaIndex and RankGPT parsers can drop or misalign documents without any error (R3 gap 2).

**Tools to add, across the phase** (details in each concept's §10; install nothing yet)
- **Nothing new for the lessons, verify notebooks or apply-it tools.** They use packages Yash already has: numpy, `rank-bm25` 0.2.2, `sentence-transformers` 6.1.0 (MiniLM and the `ms-marco-MiniLM-L-6-v2` cross-encoder), pymupdf 1.26.7, tiktoken and plotly.
- **`scikit-learn==1.9.1`: declare it explicitly** (R5). It is already in `uv.lock` as a dependency of sentence-transformers. R5 uses `GaussianMixture`, BIC and `PCA`.
- **`langchain-classic==1.0.8`, in the LLMOps group** (R1, R3). `EnsembleRetriever`, `ContextualCompressionRetriever`, `CrossEncoderReranker` and `LLMListwiseRerank` now live only there, and its dependencies are light. LLMOPS_FOUNDATION §11 lists it as read-only, so this is a decision (R3-E11).
- **From LLMOPS_FOUNDATION §11, already planned:** `langchain-core` 1.6.6 (MMR and `InMemoryVectorStore` parity tests, retriever wrappers), `langsmith` 0.14.4, `arize-phoenix-otel` 0.17.2, and `anthropic` 1.11.0 for the optional Haiku arms.
- **Optional:**
  - `ir-measures` 0.4.3 + `pyndeval` **0.0.6** (R4), to cross-check α-nDCG. Versions 0.0.7 and 0.0.8 are only a day old.
  - `umap-learn` 0.5.12 + `numba` 0.68.0 (R5), only if the paper-faithful reduction is wanted. It is about 45 MB, has a slow first run, and caps numpy below 2.6; PCA is the default.
- **Not added:**
  - `bge-reranker-v2-m3`: 2.27 GB, and its 8K context buys nothing on chunks of at most 182 tokens.
  - `langchain-cohere`: needs `cohere<6`, which conflicts with the pinned 7.2.0.
  - `langchain-community`: one read-only cell at most.
  - FAISS, Chroma, Qdrant and Weaviate: their filter behaviour was read, not installed.
  - LangGraph: every Phase 5 flow is linear.

**Decisions Yash must make** (each answerable in a word; recommendation in bold)
1. Before the v2.x runs, grow the eval slices: the acronym probe set, scoped items, cross-page multi-span items, and chapter/global items at ≥ 8 per split. Also add a headroom gate to each card, with "inconclusive" pre-registered. **yes** / no.
2. Adopt the stage contract for every v2.x card? It runs on v1.x champion units, filters before fusion, reranks the fused pool, runs MMR on the reranked pool, and normalises scores per query. **yes** / no.
3. Add `langchain-classic` 1.0.8 to the LLMOps group (R1, R3)? **yes** / no.
4. Run the paid or hosted comparison arms? These are the Cohere rerank arm (about 40–60 cached searches, ≈ $0.04–0.15, price UNVERIFIED) and a Haiku LLM-rerank arm (≈ $0.06) only when credits exist. **yes** / no.
5. R5 depth now: **mechanism only** / full experiment. The experiment waits for v8, where it competes with S1, and for the global slice.

Smaller preferences are in each concept's §11:
- R1: rewrite into the HTML format **now**; add a TMM weighted arm **no**.
- R2: Corpus D mini-experiment **yes**; Groq filter-extraction arm **yes**.
- R3: pool sweep {10, 20, 50} plus "all 97" **yes**; BGE **no**.
- R4: Dartboard **lesson-only**.
- R5: **PCA**, **chapter** units, **Groq** summariser.

**Size of the build work**

| Concept | Size | Why |
|---|---|---|
| R1 hybrid fusion | **M** | Content and measured numbers exist (`R1_FACTS` S1–S14), and about 70% carries over. New work: the HTML rewrite with a fusion explorer; six verify sections (stop-word votes, variants table, framework replicas, the four fusion property tests, acronym probe set); `fusion_fit_check.py` on top of `bm25_fit_check.py`; the LLMOps notebook with an `EnsembleRetriever` parity test; 7 quiz items. API: ≈ 2–4 cached Cohere calls, optional ≈ $0.01 Groq |
| R2 metadata filtering | **M** | The mask is small. The work is scope tagging from I2's heading tree, scoped eval items with gold scopes, a rule extractor with a frozen alias table, the starvation simulation, removed-gold evaluators and fixtures. The adopt/reject decision waits for Corpus T (DEC-3). Optional Groq extraction arm: ≤ 160 calls, ≈ $0.02 |
| R3 reranking | **M** | The mechanism is small and P4 covers part of it. New: headroom/oracle maths, a pool sweep that scores once and slices many times, a CPU latency harness and budget test, LLM pointwise and listwise arms with repair and bias tests, two adapters, and the trace extension. ≈ 352 Groq calls (≈ $0.04, but about 80% of a day's free-tier tokens) plus the optional Cohere and Haiku arms |
| R4 diversity | **M** | MMR, a threshold-dedup arm and Dartboard together are under 100 lines of NumPy. The work is the eligibility gate, α-nDCG and the redundant-evidence metric, the R3 interaction, parity and regression tests, and the tool. ≈ 36 Groq calls, only if the gate passes |
| R5 hierarchical / RAPTOR | **M** (L if the v8 experiment runs) | Two-level chapter → chunk retrieval and a RAPTOR tree with PCA + GMM/BIC on Corpus D; summary provenance and leaf-only scoring; a persisted, seeded `tree.json` so replay works. 21 chapter-summary calls (≈ $0.004) plus 5–25 tree calls per build. A long-context baseline needs Haiku (Corpus D ≈ 13K tokens > Groq's 8K TPM) |

**API cost per full Phase 5 run** (all calls cached; every notebook replays with no key): under about $0.30 in total. It is dominated by the optional Cohere rerank arm, whose price is UNVERIFIED. **Groq's free-tier token limits, not money, set the pace.** R3's pointwise LLM arm alone uses about 160K of the 200K daily tokens, so it must be recorded over a day if needed.

---

## Concept R1: Sparse vs dense vs hybrid retrieval; score fusion and RRF (E, project v2.0)

R1 is the only Phase 5 concept that already has a full course kit: a long lesson in the old Parts A–M template (`concepts/R1_hybrid_fusion.md`, 985 lines), a short reading (`study/reading/R1_hybrid_fusion.md`), a 17-item question file, a 10-task lab, and a verification folder with measured facts (`sources/verification/R1/R1_FACTS.md`, S1–S14, all from local runs on 2026-10-17 with MiniLM, no API). The material is accurate and unusually well measured. So this audit does not redo it. It asks four things:
- Can every quiz key point be answered from the **Short** depth (the reading file, per `study/FORMAT.md` §1 and §3)?
- What does the existing material get wrong or leave out, judged against the research, the libraries as released, and 02/04/06?
- What changes when the technique runs as v2.0 on top of the **v1.x champion**, not on v0's 97 chunks?
- Should it be rewritten into the new house format (`study/lessons/P3_bm25.html`)? **Yes.** The content is mostly reusable; the structure, ten gaps and the production layer are not there yet (§6).

Labels used here: **verified** = opened in this session; **search-checked only** = seen only in search summaries; **UNVERIFIED** = not found or not openable; **toy** = made-up numbers; **draft-seed observation** = the 10 `llm-draft` seeds of 06 §6.7, never an evaluation result. Every R1 number quoted below comes from `R1_FACTS.md` (local run, not re-run here) unless marked "derived here" or "measured here".

### 1. Sources checked

**Book (not present in this session; per 02, 04 and the R1 lesson's own `r1_sources.py` checks; not re-opened, UNVERIFIED here):**
- Ch12 p.1–2/14 (blind spots: an acronym ranked fourth by meaning-based search; a paraphrase missed by keywords), p.3–4/14 (cookbook analogy), p.5–6/14 (one set of chunks indexed twice), p.6–7/14 (two top-K lists with scores; Venn figure), p.7–9/14 (two normalisers; the distribution-based one called more robust; missing chunk gets only the other retriever's part), p.9–12/14 (weights 0.6/0.4; 50/50 to 70/30), p.12–14/14 (overkill cases; takeaways), Ch13 p.5/13 (fusion output as a reranker pool), App p.16–17, 19, 21/23 (glossary).
- 02 and 04 disagree on the page range (R1-E1).
- The book has no RRF (lesson S-src absence checks: no "reciprocal rank fusion", "RRF", "Cormack").

**Repo (verified: downloaded at `009adba` into the session scratchpad, cells read 0-based with `python3 -I`; code not run):**
- `all_rag_techniques/fusion_retrieval.ipynb`:
  - cell 0: the design text (normalise, then a weighted sum with `alpha`);
  - cell 10: `PyPDFLoader`, `RecursiveCharacterTextSplitter(1000, 200)`, `FAISS.from_documents(cleaned_texts, OpenAIEmbeddings())`;
  - cells 14–15: `BM25Okapi([doc.page_content.split() ...])` over the same `cleaned_texts`;
  - cell 17: `similarity_search("", k=ntotal)`; `bm25.get_scores(query.split())`; `similarity_search_with_score(query, k=len(all_docs))`; `1 - minmax(distances)` and `minmax(bm25)` each with `+ 1e-8`; `alpha * vector + (1 - alpha) * bm25`; `argsort`; `all_docs[i]`. Three orders are mixed by position, exactly as the lesson's D.9 says;
  - cell 19: query "What are the impacts of climate change on the environment?", `k=5, alpha=0.5`.
- `all_rag_techniques_runnable_scripts/fusion_retrieval.py` (143 lines): L75–L86 is the same logic; L80–L81 have **no** epsilon; L135 `--alpha` default 0.5.
- `all_rag_techniques/fusion_retrieval_with_llamaindex.ipynb`: cell 3 (legacy `BM25Retriever`, `QueryFusionRetriever`, OpenAI `text-embedding-3-small` at 512 dims); cell 8 (`faiss.IndexFlatL2`); cells 15 and 17 (`similarity_top_k=2` each); cell 19 (`retriever_weights=[0.6, 0.4]`, `num_queries=1`, `mode='dist_based_score'`); cell 20 (rejects `reciprocal_rerank` "since there is no normalization", which is the wrong reason: RRF reads ranks, so it needs none); cell 22 (`retriever.retrieve(query)`).
- LangChain's FAISS wrapper builds `IndexFlatL2` by default (`langchain-community` 0.4.2 `vectorstores/faiss.py` L998–L1001, verified), so the repo's distances are FAISS L2 distances, smaller = closer. This closes half of the lesson's "FAISS behaviour UNVERIFIED". Whether OpenAI accepts an empty string for L75 is still UNVERIFIED.

**Existing course files (read in full or in the relevant parts):**
- `concepts/R1_hybrid_fusion.md` (all 985 lines);
- `study/reading/R1_hybrid_fusion.md` (the Short; 208 lines);
- `study/questions/R1_questions.md` (17 items: 3 pre, 12 main, 2 interview; every key point extracted);
- `labs/R1_hybrid_fusion_lab.ipynb` (48 cells, 9 tasks, CHECK cells by fingerprint);
- `sources/verification/R1/` (`R1_FACTS.md`; `out_r1_measure.txt`; the lab test LT and the document check MD);
- 02 R1 card (L658–L671) and §4 gates; 03 rows L45–L46, L434, L478, L531; 04 R1 row (L174), Ch12 table (L594–L601), DV-26/27/28; 06 §2.3–§2.5 (schema, config, trace), §4.1 rules, v2.0 card (L586–L595), §6.2 categories, §6.3 leakage rule (lexical overlap), §6.7 seeds, §9.4 (MDE ≈ 0.18 at n = 50);
- 08 RB1, RK-15, D-31; ext review L62, L252–L254, L303, L442, L456, L467; backbone §0;
- `sources/vai/L19-L23_core_rag.md` §L23 and its verification log (RRF with 0-based ranks; **no BM25 leg**; a dead leg still labelled "hybrid"; ids paired by position);
- `phase_01_prerequisites.md` (P2 pool-bias row 8; score-direction table), `phase_02_core_rag_baseline.md` (C4 gap 20: dense misses exact strings), `phase_03_measurement.md` (M2, M4, M5), `phase_04_indexing.md` (I5 gap 22 and §5 "Effects on other phases": R1 inherits `bm25_text`; contextual BM25 and doc2query arms are tested at v2.0);
- the P3 pilot (HTML structure, gap audit, verify notebook, `bm25_fit_check.py`, which already recommends "use hybrid" but has no fusion);
- tracker: R1 `exposed` (O1-Q09, score 2; VAI L23); P3, P4, C4, M1, M4 `not_started`; M2, M5 `exposed`. MC-001…MC-006 open; none is about fusion.

**AE book:** not present. One line is carried from the lesson and the ext review (AE Ch2, 'Retrieval Fundamentals': keyword search as the first baseline), paraphrased, UNVERIFIED here.

**Interview repo (AIQ @ `e080df2`, MIT, "Copyright (c) 2026 Om"; verified):** 04 Q9 L216–L242 (hybrid search), Q24 L582 (RRF), Q32 L812 (SPLADE); `12-coding-challenges/17_hybrid_search_and_rerank.py` (`rank_by_score` drops scores ≤ 0 at L118–L123; `reciprocal_rank_fusion(k=60)` at L126).

**External (8 sources; list at the end):** [R1-S1] Cormack et al. 2009 (search-checked only); [R1-S2] Bruch, Gai & Ingber 2023 (search-checked only); [R1-S3] Anthropic Contextual Retrieval (verified); [R1-S4] Anthropic cookbook `retrieve_advanced` (verified); [R1-S5] LangChain `EnsembleRetriever` and `BM25Retriever` source (verified); [R1-S6] `rank_bm25` 0.2.2 source (verified); [R1-S7] LlamaIndex `QueryFusionRetriever` source (verified); [R1-S8] Weaviate hybrid docs and searcher source (verified); [R1-S9] Elasticsearch RRF retriever and OpenSearch score-ranker docs (verified); [R1-S10] SPLADE README (verified).

**Session measurements (new, scratchpad only):**
- Corpus D PDF downloaded (sha256 `1d58a0fa…`, matches R1_FACTS), text via `pdftotext` (71,586 chars; approx.). A regex count found **21 distinct parenthesised acronyms**, 14 of which occur at most twice (HFCs, IPCC, BECCS, CH4, N2O, ESG, …). This is the raw material for an exact-term probe set (§6, §11). Counts are approximate; the verify notebook re-counts them on the PyMuPDF snapshot.
- `numpy` 2.5.3 `np.argsort(np.zeros(n))[::-1][:4]` returns the **last four indices** (n = 10, 97, 1000). `rank_bm25.get_top_n` uses exactly this, so a BM25 retriever whose scores are all 0 returns the last k chunks of the corpus (measured here, toy arrays).

### 2. Gap audit

"Yash studied it?" uses the tracker: R1 `exposed`; P3, P4, C4, M1, M4 `not_started`; M2, M5 `exposed`. "Short" means the reading file.

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class (core / bridge / next) | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Dense retrieval blurs rare identifiers into their topic | Short §1; B.1; PRE-02, R-01 | yes (Short §1, Full B.1; measured BECCS rank 4) | R1 (C4 lacks it, phase_02 C4 gap 20) | no (C4 not started) | core | Keep the five-query table; add the mechanism sentence from Full to Short |
| 2 | How BM25 scores (tf, idf, the floor, `tok_norm`) | Short §2; D.10 | **only in P3**, which is not studied | P3 | no | bridge | One paragraph plus a link to the P3 HTML; never assume it |
| 3 | Sparse vs dense vocabulary; the inverted index | title; Full E | P3 HTML §2–§3 | P3 | no | bridge | One line each, with P3 links |
| 4 | Both retrievers must rank the **same units with the same ids** | D.1; T-02; J5 | yes (Full D.1; Short §8 row) | R1 | exposed | core | Keep. Add the catalogue test to Short (quiz gap, §3) |
| 5 | Scales differ: cosine bounded, BM25 corpus-dependent | Short §3; D.2 | yes | R1 | exposed | core | Keep |
| 6 | Min-max: 1 = best in this list, 0 = last = missing, **the cut moves the scale** | Short §5; D.3; R-05 | Full yes; **Short lacks the cut** | R1 | exposed | core | Add one sentence and the D-009/D-010 example to Short |
| 7 | Three-sigma ("distribution-based"); population vs sample sd; values outside 0–1; what LlamaIndex really does | D.4 | yes, but LlamaIndex marked UNVERIFIED | R1 | exposed | core (Full) | Replace the UNVERIFIED note with the source facts (R1-E7) |
| 8 | **Theoretical min-max** (TMM): normalise against the scorer's possible minimum, so "last" ≠ "missing" | — | **missing** | R1 | no | core (Full) | New idea backed by [R1-S2]. Toy (derived here): dense min −1, BM25 min 0 on the O1-Q09 lists gives C, A, B, D at 0.5/0.5 instead of A, C, B, D; the choice of the cosine minimum (−1 vs 0) is itself a setting |
| 9 | Weighted (convex) fusion; missing → 0; weights as a dev-tuned variable | Short §5; D.5 | yes | R1 | exposed | core | Keep |
| 10 | RRF formula, 1-based ranks, k | Short §6; D.6 | yes | R1 | exposed (O1-Q09 intuition) | core | Keep |
| 11 | **RRF variants in the wild:** 0-based ranks (Weaviate ranked fusion, LlamaIndex, VAI L23); weighted RRF (LangChain, OpenSearch); k = 0 with weights 0.8/0.2 (Anthropic cookbook) | — | **missing** | R1 | no | core (Full table; Short one line) | One table: formula, k, rank base, weights, ties, depth default. 0-based ranks = the paper's formula with k − 1 (derived), so order changes are rare; k = 0 is a different method |
| 12 | The consensus rule (depth ≤ k + 1 ⇒ every both-list chunk beats every one-list chunk) | Short §6; D.7; A-06 | yes | R1 | exposed | core | Keep, and add #13 as its caveat |
| 13 | **Under `rank_bm25`, "score > 0" does not mean a content word matched.** The idf floor (ε × mean idf) gives stop words a positive weight, so BM25 lists hold 80–97 of 97 chunks (S4). On D-008 every BM25 rank after 1 comes from "the" alone, yet those ranks give RRF consensus votes | D.1 rule 3; K; FACTS §0 | **missing; the lesson states the opposite** (R1-E3) | R1 (P3 owns the floor) | no | core | New subsection: count content-term matches separately, show the D-008 noise votes, pre-register a stop-word or min-idf policy as an arm setting |
| 14 | Rescaling invariance and its boundary (a new model or corpus re-orders the lists) | Short §6; D.8; R-06 | Full yes; **Short lacks the boundary** | R1 | exposed | core | One sentence in Short |
| 15 | Exact ties and the tie rule (smaller `chunk_id`) | Short §6; D.6; J3 | yes | C4 / R1 | no (C4) | bridge | Keep; add "frameworks break ties by first-seen order" (#20) |
| 16 | **List depth** as a pre-registered variable; framework defaults differ (LangChain: each retriever's k = 4; LlamaIndex: `similarity_top_k` 2; Elasticsearch: `rank_window_size` = `size` = 10) | D.7; K | partly (depth 50 named; defaults missing) | R1 | no | core | Table of defaults; "set depth explicitly" |
| 17 | The repo's misalignment, and **property tests** that catch any version of it | Short §7; D.9; H.3 | identity test yes; **permutation and monotonicity tests missing** | R1 | exposed | core | Add the four-test suite in §7 below |
| 18 | **Dead leg:** one retriever returns nothing (or junk) but the output still looks hybrid | J2; VAI L23 | partial (J2 only) | R1 / D1 | no | core | Per-leg hit counts in every result and trace; alert on them (§9) |
| 19 | Tokenizer and **BM25 text field** as hidden variables (`text` vs I5's `bm25_text`) | D.10; phase_04 I5 gap 22 | tokenizer yes; text field **missing** | P3 / I5 / R1 | no | core | Config field `bm25.text_field`; contextual-BM25 arm only if the champion has headers |
| 20 | Framework dedup keys and ties: LangChain dedups by `page_content` unless `id_key` is set; LlamaIndex by node hash; stable first-seen ties | — | **missing** | R1 | no | core (Full; LLMOps) | Show how `page_content` dedup re-creates the alignment bug when the two legs carry different text |
| 21 | Per-category CE@4, MRR@10, Hit@4 | Part I; Short §6 | M2 (exposed); lesson uses it | M2 | exposed | bridge | Two lines and a link |
| 22 | **Power of the H1 slice:** about 10 exact-term + table/numeric items, ≈ 3–4 on test | Part I decision rule | **missing** (R1-E4) | M4 / R1 | no | core | Show the arithmetic; plan the probe set or Corpus T; "inconclusive" expected |
| 23 | Lexical overlap per category, and gold built by grep favouring BM25 (pool bias) | 06 §6.3; phase_01 P2 row 8 | **missing in R1** | M1 / P2 | no | bridge | Report question–gold overlap per category next to each arm; one paragraph on pool bias |
| 24 | Compare against the **champion and v0** on identical comparison keys | Part I | partial (R1-E5) | M4 / 06 §4.1 | no | bridge | State the arms on the champion's index units |
| 25 | Cost and latency of a second index | I.3 | design only | D2 | no | bridge | BM25 build time, p50/p95 per leg and fusion (06 trace fields) |
| 26 | What RRF's k = 60 was tested on; the counter-evidence (convex combination beats RRF; RRF sensitive to k) | D.6; Source C #33 "not re-read" | **missing** | R1 | no | core | §5 below: the study, the result, the limits |
| 27 | Learned sparse retrieval (SPLADE) | Full E "not covered" | link only | R1 → later | no | next | One paragraph; non-commercial licence; not in v2.0 |
| 28 | Contextual BM25 and doc2query (questions added to BM25 text) | phase_04 I5/I6 | missing in R1 | I5 / I6 | no | next (arm idea) | Optional v2.0 arm only if v1.2/I6 produced the fields |
| 29 | Reranking the fused pool | Full E; Ch13 p.5/13 | link | R3 | no | next | Link; the fused union (63–76 chunks, S7) is the pool |
| 30 | Merging sub-query lists with RRF | 03 L478 | link | Q1 | no | next | Link; Q1 reuses `fuse_rrf` and its tests |

### 3. Quiz coverage

The Short is the reading file (FORMAT §1, §3). Every key point of the 17 items was checked against it.

**Answerable from Short:** PRE-01, PRE-02, R-01, R-02, R-03, R-04, A-01, A-02, A-03, T-01; PRE-03 by combining §5's missing-chunk rule with §6's 1/61 (derivable, not stated).

**Not fully answerable from Short (fix in the rewrite):**

| Item | Point | What Short lacks |
|---|---|---|
| R1-R-05 | For a 4: "the result depends on where the list is cut" and D-010 | §5 says the last chunk gets 0 but never that the cut sets the scale; D-010 appears only in Full |
| R1-A-04 | For a 4: the test checks alpha = 1.0 → dense order **and** alpha = 0.0 → BM25 order | §7 gives only the alpha = 1.0 half |
| R1-T-02 | Key point 2 ("or returns ids that are not chunks") and For a 4 (catalogue-membership test) | §8 says only that one side's votes are lost |
| R1-T-03 | Key point 3: "decide on dev with CE@k per category and **confirm once on test**" | Short names a dev set (§5) but never the single test confirmation; re-tuning after a scorer swap is implied, not stated |
| R1-R-06 | For a 4: ranks ignore rescaling **but not a new model or corpus** | §6 says rescaling cannot hurt; the boundary is in Full D.8 only |
| R1-A-06 | For a 4: an exact-term chunk that dense misses entirely cannot reach the top under RRF | Derivable from §6, never said; Full D.7 says it |

**Key points that research now contradicts:** none. Two need a caveat: R1-A-06 and R1-PRE-03 assume real consensus, but on Corpus D many "both-list" chunks are in the BM25 list only through stop words (gap #13).

**New question titles needed** (two external items already exist, so these are all course-written):
- **R1-R-07** Under `rank_bm25`, why can a chunk get a BM25 score above 0 without sharing any content word with the question, and what does that do to RRF's consensus votes?
- **R1-R-08** Name two settings that a framework's hybrid retriever fixes for you by default (list depth, dedup key, tie rule, rank base), and why each must be written into the run config.
- **R1-A-07** The O1-Q09 lists under theoretical min-max (cosine min −1, BM25 min 0) at 0.5/0.5: compute the order and say why it differs from plain min-max. (★ C, A, B, D; derived here.)
- **R1-A-08** Weaviate's ranked fusion gives the top item 1/60, the paper 1/61: does the fused order of the O1-Q09 lists change? (★ No; 0-based ranks act like k = 59.)
- **R1-T-04** A LangChain `EnsembleRetriever` fuses a BM25 leg whose documents carry header-prefixed text and a dense leg whose documents carry plain chunk text, with `id_key` unset: what goes wrong, and which one setting fixes it?
- **R1-T-05** Your hybrid log shows BM25 returned no content-term match for 30% of production queries, yet every answer is labelled "hybrid". What do you monitor, and what do you change?
- **Interview** (derived from AIQ 04 Q9 and Q32, MIT): "Is a document that is top-3 in only one list sure to surface after RRF?" (★ Not while ≥ k both-list documents exist at depth ≤ 61; AIQ Q9's answer says it does.)

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| R1-E1 | 04 R1 row (L174) "Ch12 p.4/14–p.12/14" vs 02 R1 card "p.1–2, 5–6, 7–9, 9–12" vs the lesson's own checked list "p.1–14/14" | Three different page ranges. 04 omits the blind-spot pages (p.1–2) that the whole concept rests on and the overkill cases (p.12–14); 02 omits p.3–4, p.12–14 and the glossary (the lesson's G.3 item 1 already notes 02's part). Pages not re-opened here | Use the lesson's checked list in 02 and 04 after the local page check |
| R1-E2 | 06 v2.0 card "static reading; runtime UNVERIFIED"; 04 DV-27 "Fused ranking likely wrong" | Both predate the transcription run: the repo's logic, transcribed with MiniLM, gives Hit@4 0/8 vs 8/8 aligned, and the same 5 chunks for every query at alpha = 1.0 (S11). The lesson's G.3 lists the 04 part only | "Transcribed and measured (R1 S11): 0/8; the notebook itself not run (OpenAI)" |
| R1-E3 | Lesson D.1 rule 3, Part K "scores > 0 only", H.3 "`BM25Retriever` returns only scores > 0"; FACTS §0 | Implies "> 0" means a term matched. With `rank_bm25`'s idf floor (ε·mean idf, source L85–L105 [R1-S6]) a stop word scores > 0, so lists hold 80–97 of 97 chunks (S4) and the filter removes almost nothing. On D-008, `kigali` and `amendment` occur only in seq 69, so BM25 ranks 2–80 come from "the" alone (S5: floored idf 0.8588). Of the 30 chunks in both top-50 lists (S7), 29 are there through "the", and RRF's fused ranks 2–4 (seq 56 at BM25 rank 13, seq 12 at rank 18, seq 27) are stop-word votes on top of dense ranks. The consensus rule (D.7) then rewards noise | Teach it (gap #13). Report "content-term matched" (a query token whose idf is above the floor) per chunk; make the BM25 depth rule a pre-registered setting (all > 0, content-match only, or a stop-word list) |
| R1-E4 | Lesson Part I.1 decision rule (CE@4 on the pooled `exact-term` + `table/numeric` slice, "about 10 items", adopt only if the test CI excludes 0) | With 06 §6.3's ≈30% dev and the rest split between test and holdout, the slice has about 3–4 test items. Even if all 4 improve, the exact two-sided sign test gives p = 0.125, and a bootstrap over 4 items is degenerate. The rule cannot pass on evidence | Grow the exact-term slice before v2.0 (the 21-acronym probe set, human-verified, §6), or move the decision to Corpus T, and pre-register "inconclusive" as the expected verdict on D |
| R1-E5 | Lesson Part I.1 "Baseline: v0 dense … also the current champion if it is not v0"; 06 v2.0 "three arms (dense, BM25 alone, hybrid)" | 06 §4.1 rule 1 requires v0 **and** the champion. At v2.0 the champion is the v1.x output, so the dense arm, the BM25 index and the fused arms must all use the **champion's index units**. If the champion adds I5 headers or I6 questions, which text BM25 indexes (`text` vs `bm25_text`) is an unrecorded variable | "A0 = v1.x champion (dense, Cohere); BM25 and fusion over the champion's units; v0 (E000) as the second reference; `bm25.text_field` recorded" |
| R1-E6 | 06 §2.4 `retrieval:` block (`method: dense \| bm25 \| hybrid` only); 06 §2.5 `fused[].rrf_score` vs lesson H.4 `score` | No config fields for k_rrf, depth, weights, normaliser, missing value, tie rule, BM25 library/params/tokenizer/text field, so none of them enters `config_hash`. A weighted arm has no `rrf_score`. No per-leg hit counts in the trace | Add a `retrieval.hybrid` block (§9) and `fused[].{score, method, ranks_by_source}` plus `legs.{dense_hits, bm25_content_hits}` |
| R1-E7 | Lesson D.4 and Verification log; FACTS §4 "LlamaIndex `dist_based_score` UNVERIFIED" | Now read in `llama-index-core` 0.14.25 [R1-S7]: population sd; no clipping; weights renormalised to sum 1; duplicates summed by node hash; divided by `num_queries`; a constant list → 1.0 if > 0 else 0. Its `reciprocal_rerank` uses **0-based** ranks (top = 1/60), a hard-coded k = 60, and **ignores** `retriever_weights`. Defaults: `num_queries=4` (an LLM writes 3 extra queries unless set to 1), `similarity_top_k=2` (cell 19 sets neither top-k, so it returns 2 nodes). The notebook era's version is UNVERIFIED | Replace the UNVERIFIED lines; add the hidden-LLM-call default to the LLMOps notebook's warnings |
| R1-E8 | Lesson D.6 and Source C "#33 … not re-read"; Part K "Primary fusion: RRF" | Missing evidence, not a wrong claim. What RRF's k = 60 was tuned on (a pilot fusing many TREC runs, "near-optimal … not critical") and the later finding that a tuned convex combination beats RRF in- and out-of-domain while RRF is sensitive to k [R1-S1, R1-S2, both search-checked] are absent. Without them, "RRF primary" reads as "RRF is better" | Add §5's study → result → limits → meaning; keep RRF as the default arm for the stated reason (no tuning, scale-invariant), and the weighted arm as a real contender |
| R1-E9 | Lesson header and 02 R1 card "FT: possible (VAI L23)"; tracker evidence `legacy:vai-L23` | VAI L23 has **no BM25 leg**: its "keyword" leg is a second dense search, and its RRF uses 0-based ranks (`sources/vai/L19-L23_core_rag.md`). L23 can show RRF's shape, not the sparse half of R1 | Fast track may skip RRF-by-hand only; BM25 and fusion-over-aligned-ids still need evidence |
| R1-E10 | LLMOPS_FOUNDATION §9.2 (hidden-defaults table) | No rows for `EnsembleRetriever` or `BM25Retriever` (defaults in §5) | Add both rows (`c=60`, equal weights, `id_key=None` → dedup by text, no truncation, ties first-seen; `split()`, no lower-casing, `k=4`, zero-score documents returned) |
| R1-E11 | AIQ 04 Q9 answer (external; the course uses Q9 as a source in Part L) | "even top-3 in just one list still surfaces" is false for k = 60 and depth ≤ 61 whenever enough both-list documents exist (S7: 10/10 seeds) | Use it as an "is this claim right?" item (§3) |

### 5. What the research says

**[R1-S1] Cormack, Clarke & Büttcher (2009), "Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods", SIGIR '09 short paper.** Search-checked only: every host of the PDF was blocked.
- *The study:* fuse many ranked runs (metasearch) with Σ 1/(k + rank). k was fixed at 60 in a pilot that fused 30 configurations of the Wumpus search engine on TREC collections, then left unchanged for validation on several TREC tracks and on LETOR 3. Compared with Condorcet Fuse, CombMNZ and learning-to-rank methods, by MAP.
- *The result (as summarised):* RRF equalled or beat the other methods; k = 60 was "near-optimal" and its choice "not critical".
- *Limits:* many systems, long TREC-style runs, MAP; not two retrievers at depth 50 over 97 chunks; exact numbers UNVERIFIED.
- *For the project:* k = 60 is a convention inherited from metasearch, not a tuned value for hybrid RAG. On the draft seeds, k 60 → 0 changed 5 of 10 top-4 lists (S10). Record k with every run; do not tune it on 3–4 test items.

**[R1-S2] Bruch, Gai & Ingber (2023), "An Analysis of Fusion Functions for Hybrid Retrieval", ACM TOIS 42(1), art. 20; arXiv 2210.11934 (Pinecone).** Search-checked only (arXiv, ACM and pinecone.io were blocked).
- *The study:* two-way fusion of a lexical and a semantic retriever, convex combination (CC) of normalised scores vs RRF, in-domain and out-of-domain, with an analysis of normalisation choices including a "theoretical min-max" form.
- *The result (as summarised):* CC beat RRF in both settings, contrary to an earlier study; RRF was sensitive to its parameters; the choice of normalisation mattered less than assumed for CC; and CC's one weight could be tuned from a small set of examples or set from domain knowledge.
- *Limits:* benchmark datasets, not span-level gold; datasets, metric and sample sizes UNVERIFIED here; two retrievers only.
- *For the project:* A3 (weighted fusion, weight from {0.3, 0.5, 0.7} on dev) is a serious arm, not a straw man. Add a TMM variant (gap #8) because it removes the "last = missing" zero. "RRF needs no tuning" is true only if k and depth are left at their conventions; it is not "RRF is better".

**[R1-S3] Anthropic, "Introducing Contextual Retrieval" (2024-09-19).** Verified (WebFetch). Phase 4 [I5-S1] already used it for the contextual part.
- *The study:* BM25 plus embeddings, merged and deduplicated "using rank fusion techniques"; the method and weights are not named on the page. Metric 1 − recall@20, averaged over several domains.
- *The result:* contextual embeddings 3.7% failures; adding contextual BM25 2.9%; adding reranking 1.9% (baseline 5.7%). The page says embeddings + BM25 beat embeddings alone, but gives no number for that row in its text.
- *Limits:* vendor; unnamed datasets; recall@20, not CE@4; the BM25 effect is reported only together with contextual text.
- *For the project:* evidence that BM25 adds on top of strong embeddings. The "error code TS-999" example is the exact-term failure R1 targets. A 0.8-point absolute change is far below what ≈50 questions can detect (06 §9.4).

**[R1-S4] Anthropic cookbook, `capabilities/contextual-embeddings/guide.ipynb`, `retrieve_advanced`** (claude-cookbooks @ `a162e01`; verified on raw GitHub).
- *What the code does:* 150 candidates from each leg; score = 0.8 × 1/(rank) for the dense rank + 0.2 × 1/(rank) for the BM25 rank (0-based index + 1, so **k = 0**); a union keyed by `(doc_id, original_index)`; ties broken by id in descending order; it counts how many final chunks came from each leg.
- *For the project:* the published hybrid numbers come from a **weighted k = 0 rank fusion**, not k = 60 RRF. At k = 0 the consensus rule does not hold: one first place outweighs many second places. This is the clearest real-world case for "write the formula down".

**[R1-S5] LangChain `EnsembleRetriever`** (`langchain-classic` 1.0.8, `retrievers/ensemble.py`; verified) **and `BM25Retriever`** (`langchain-community` 0.4.2, `retrievers/bm25.py`; verified).
- `EnsembleRetriever`: weighted RRF, `weight / (rank + c)`, ranks from 1, `c: int = 60` (L70, L328–L335). Weights default to 1/n (L85–L88). `id_key=None` means documents are keyed and **deduplicated by `page_content`** (L329–L334, L338–L347). It returns the **whole union**, with no top-k cut, and no fused score attached. Ties keep first-seen order (Python's stable sort over the chained lists).
- `BM25Retriever`: `default_preprocessing_func` is `text.split()` with **no lower-casing** (L11–L12), `k: int = 4` (L22), and it calls `rank_bm25.get_top_n`, which returns the top n **even when every score is 0** (L111–L116; [R1-S6] L69–L75).
- *For the project:* five hidden defaults the lesson must name. (1) Depth = each leg's k (4), not 50. (2) The union can be up to 8 chunks, so a naive "hybrid" sends more context than dense k = 4 and wins by volume. (3) Text-keyed dedup merges two chunks with identical text, and fails to merge the same chunk when the legs carry different text (I5's `bm25_text`): the alignment bug again. (4) `split()` is P3's broken tokenizer. (5) A dead BM25 leg returns the last 4 chunks of the corpus (measured here on numpy 2.5.3), and they receive RRF votes.

**[R1-S6] `rank_bm25` 0.2.2** (`rank_bm25.py`; verified). `BM25Okapi(k1=1.5, b=0.75, epsilon=0.25)` (L79). idf below 0 is replaced by ε × mean idf (L85–L105), so stop words keep a small positive weight. `get_top_n` = `argsort(scores)[::-1][:n]` with no score filter (L69–L75). This is the mechanism behind R1-E3 and the dead-leg finding.

**[R1-S7] LlamaIndex `QueryFusionRetriever`** (`llama-index-core` 0.14.25, `retrievers/fusion_retriever.py`; verified). The facts are in R1-E7. One more: `reciprocal_rerank` re-sorts each list by score before ranking, so ties in score become insertion order.

**[R1-S8] Weaviate hybrid search** (docs `weaviate/docs` @ `5dcf1d6`, `concepts/search/hybrid-search.md`; server `usecases/traverser/hybrid/searcher.go` on `main`; verified).
- `relativeScoreFusion` (min-max per result set; the default from v1.24) vs `rankedFusion` (the default up to v1.23), whose worked example gives the top item 0.016667 = 1/60, i.e. **0-based** RRF.
- `alpha` weights the vector leg; the server default is 0.75. The docs warn that client libraries may not send it, so the effective weighting can differ; they say to set `alpha` explicitly. The searcher unions both sets, never intersects them.
- *For the project:* the most common production default is score fusion with min-max, not RRF. The ext review's note (L442) that SDG's "relative score fusion" is really min-max is confirmed.

**[R1-S9] Elasticsearch `rrf` retriever** (elastic/elasticsearch docs @ `4f131aa`) **and OpenSearch `score-ranker-processor`** (documentation-website @ `6078098`; verified).
- Elasticsearch: ranks from 1; `rank_constant` default 60, must be ≥ 1; `rank_window_size` (the per-leg depth) defaults to the request `size`, i.e. 10; equal weight per child retriever; `explain` prints each leg's rank.
- OpenSearch: `rank_constant` default 60 (range 1–10,000); optional per-clause weights that must sum to 1.
- *For the project:* k = 60 is the cross-vendor convention; depth is the setting vendors leave implicit, and it is the one the consensus rule depends on.

**[R1-S10] SPLADE** (naver/splade README @ `8dcd33a`; verified). Learned sparse vectors from a BERT MLM head with expansion, served from an inverted index. Reported MS MARCO dev MRR@10 34.0–38.8 for the released models. Licence **CC BY-NC-SA 4.0** (non-commercial). *For the project:* "next" only. It needs a transformer pass per chunk and has no Cohere equivalent here.

**Current practice (2024–2026).**
- Hybrid = BM25 + dense, merged by RRF (Elasticsearch, OpenSearch, LangChain) or by min-max score fusion with a weight (Weaviate's default, LlamaIndex `relative_score`).
- k = 60 everywhere; the per-leg depth differs (4, 10, 50, 150) and is rarely stated.
- Vendors report gains in recall@20 with BM25 added [R1-S3]. A learned sparse leg is the "next" option.

**Pitfalls, with evidence.**
- Positional fusion of differently ordered arrays (repo cell 17; S11: 0/8).
- Ids paired by position after a fetch (VAI L23).
- A dead leg still labelled "hybrid" (VAI L23; `get_top_n` on all-zero scores).
- Text-keyed dedup (LangChain default).
- Stop-word votes from the idf floor (R1-E3).
- A union larger than k (`EnsembleRetriever`).
- Unrecorded k, depth, rank base and weights (§5 variants table).
- Weighted fusion not re-tuned after a scorer change (S9: 4 of 10 top-4 lists changed under a monotone bend).
- `split()` tokenizer (S6: IPCC, BECCS unmatched).

**How to evaluate.**
- Primary: CE@4 per category against the v1.x champion and v0, with identical comparison keys.
- Diagnostics:
  - MRR@10 (where the seeds moved);
  - Hit@4;
  - first-evidence rank per arm;
  - the share of the fused top-4 from one leg only;
  - content-term BM25 hits;
  - ties in the top-4;
  - lexical overlap of question and gold span per category (06 §6.3), because high overlap favours BM25.
- Statistics: discordant pairs and the exact sign test first (M4); with 3–4 test items per slice, expect "inconclusive".
- Ops: BM25 build time; p50/p95 per leg and for fusion.

**Interview questions.**
1. AIQ 04 Q9: what is hybrid search, and why does pure vector search fail on some queries?
2. AIQ 04 Q24: how does RRF work, and why fuse by rank instead of score? (Already R1-R-06.)
3. AIQ 04 Q32: what is learned sparse retrieval (SPLADE), and when would you pick it?
4. Derived: "Your framework's hybrid retriever beats dense by 6 points. What three defaults do you check before believing it?" (★ depth, union size vs k, dedup key.)
5. Derived: "Why can k = 60 RRF bury an exact-match document that only BM25 found?"

### 6. Lesson blueprint

**Rewrite decision.** Rewrite R1 into the house format as `study/lessons/R1_hybrid_fusion.html` (one page, Short/Full toggle, answer first → theory → formula sheet → steps → verify → apply → check), plus `R1_hybrid_fusion_gap_audit.md`. Keep the existing files as sources: their measured numbers (S1–S14), the lab (kept as the lab), and the question file (extended, §3). About 70% of the text can be carried over; the rest is the ten gaps above. The old Part I protocol moves into the experiment card and the LLMOps notebook.

**The answer first (draft, 5 sentences).**
Dense search can rank the chunk that names a rare code below chunks that are merely about its topic, and BM25 cannot match a paraphrase, so hybrid retrieval runs both over the same chunk ids and merges the two ranked lists. Their raw scores live on different scales, so you either normalise each list and take a weighted sum, or add 1/(k + rank) per list with Reciprocal Rank Fusion, which never reads the scores. Every method hides choices that change the result: how deep each list goes, what a missing chunk gets, how ties break, which tokenizer BM25 uses, and whether a BM25 "match" was only a stop word. Fusion code must join scores by chunk id, never by position, and four small tests catch the repo's version of that bug before any evaluation runs. On our easy draft seeds fusion moved the evidence up but never changed CE@4, so v2.0 decides per question category against the v1.x champion, and with only a handful of exact-term test items "inconclusive" is the honest expected verdict.

**The theory in one read (12 ideas, each with its formula).**
1. *Two blind spots.* Dense: one vector per chunk, so a rare token is blurred into its topic. BM25: `score = Σ_t idf(t) · tf-part(t)`, so no shared token gives 0 (bridge to P3).
2. *Same units, same ids.* Fusion is defined over `ids(dense) ∪ ids(bm25)`, and both must be subsets of one chunk catalogue.
3. *Scales.* cos ∈ [−1, 1]; BM25 has no fixed range (it moves with N, df and avgdl). Raw sum ≈ BM25 alone (37/40, S9).
4. *Min-max.* `(s − min)/(max − min)` per list: 1 = best in this list, 0 = last = missing, and the cut sets min.
5. *Three-sigma.* `(s − (μ − 3σ))/(6σ)`, population σ; it can leave [0, 1] once n > 10, because max |z| = (n − 1)/√n.
6. *Theoretical min-max (Full).* `(s − s_min_theory)/(max − s_min_theory)`. "Last" stays above "missing"; the choice of `s_min_theory` (−1 or 0 for cosine) is a setting.
7. *Weighted fusion.* `F(d) = Σ_r w_r · norm_r(d)`, with a missing chunk getting 0. The identity test: w = 1 returns the dense order exactly.
8. *RRF.* `RRF(d) = Σ_r w_r / (k + rank_r(d))`, ranks from 1, k = 60. Variants: 0-based ranks (= k − 1), weighted (LangChain, OpenSearch), k = 0 (Anthropic cookbook).
9. *Consensus rule.* At depth N, if `2/(k + N) > 1/(k + 1)`, i.e. N ≤ k + 1, every both-list chunk beats every one-list chunk.
10. *Stop-word votes.* Under `rank_bm25`, `idf_floor = ε · mean idf > 0`, so "in the BM25 list" ≠ "a content word matched". Count `content_hit(d) = ∃ t ∈ q ∩ d with idf(t) > idf_floor`.
11. *Invariance and its boundary.* RRF is unchanged by any order-preserving change of one scorer; min-max only by linear ones. Neither survives a new model or corpus, which re-orders the lists.
12. *Measuring.* CE@4 per category, against the champion and v0; slice power: with m test items, the smallest exact two-sided sign-test p is 2 · 0.5^m (m = 4 → 0.125).

**Formula-sheet items:** min-max; three-sigma with the (n − 1)/√n bound; TMM; weighted fusion; RRF with the variants table (k, rank base, weights, depth defaults); the consensus bound N ≤ k + 1; the rank-1 vs rank-N vote ratio (k + N)/(k + 1); `content_hit`; the identity, permutation and monotonicity tests; the sign-test floor 2 · 0.5^m.

**Step-by-step outline.** Running example: Corpus D, seed D-008 ("What does the Kigali Amendment target?"), with D-006 as the counter-case. Corpus D is enough for the mechanism; the exact-term **decision** needs more items (the probe set) or Corpus T, and the lesson says why.
1. **The failure** (Short): the five exact-term queries (S6) and D-006 (S5). Bridge to P3 and C4 in one paragraph each.
2. **Two lists for D-008** (Short): dense top-4 and BM25 top-4 with scores (S5); BM25 wins by a factor of 5.02.
3. **Why not add** (Short): the raw sum (S9).
4. **Normalise** (Short: min-max and the zero that means two things, plus the cut; Full: three-sigma, TMM, what LlamaIndex really does).
5. **Weighted fusion** (Short): D-008 at 0.5/0.5; the weight as a dev variable; the identity test.
6. **RRF** (Short): D-008 at k = 60; rank 31 for dense's winner; the consensus rule. Full: the variants table, and k = 0 vs 60 on D-008.
7. **Stop-word votes** (Short: one paragraph; Full: the D-008 BM25 list after rank 1, content-hit counts per seed, RRF with content-hit-only BM25 lists as a pre-registered option).
8. **Rescaling** (Short: the boundary sentence; Full: the S9 table).
9. **The repo bug and the four tests** (Short: the bug and the identity test both ways; Full: line by line and the permutation and monotonicity tests).
10. **Frameworks do it for you, with defaults** (Full): LangChain, LlamaIndex, Weaviate and Elasticsearch defaults; the union-size and dedup traps.
11. **Measuring v2.0** (Short: per-category CE@4 vs the champion and v0; Full: the slice-power arithmetic, the acronym probe set, lexical overlap, "inconclusive").
12. **When not to use it** (Short): the existing four rows, plus "a dead leg you cannot see".

**Visuals that earn their place:**
- *Two-list Venn for D-008* (both / dense only / BM25 only, with stop-word-only BM25 members hatched). Shows how much of the "consensus" is noise.
- *Vote curve* 1/(k + r) for k = 0, 1, 60, 120 over r = 1…50, with the consensus line 1/(k + 1). Shows what k does and where the rule breaks (depth 62).
- *Interactive RRF/weight explorer* on the O1-Q09 toy and on D-008: sliders for k, depth, weight, normaliser (min-max / three-sigma / TMM) and rank base. Shows the fused order and the ranks by source.
- *Misalignment diagram:* three columns (empty-string order, corpus order, query order) with arrows for position i. Shows the bug in one glance.
- *Defaults table as a figure* (library × depth × k × rank base × dedup × ties). Shows that "hybrid" is not one algorithm.

**Full only:**
- three-sigma bounds and LlamaIndex's exact code path;
- TMM and the choice of the cosine minimum;
- the variants table;
- Bruch's CC vs RRF findings in detail;
- the cookbook's k = 0 fusion;
- SPLADE;
- contextual BM25 and doc2query arms (links to I5 and I6);
- the depth-97 break of the consensus rule (S13b);
- pool bias and Judged@k (P2 link).

### 7. Verify notebook plan

`study/notebooks/R1_fusion_verify.ipynb`. Offline; no API by default; about 1–2 minutes on CPU (MiniLM over 97 chunks, as in R1 S1). It reuses `r1_measure.py`'s reference functions and asserts its saved values, in the P3 verify-notebook pattern (a `check()` per number, with a final pass/fail count).
1. **Rebuild S1–S14** from the PyMuPDF snapshot: index hash `d4108b89…`, seeds, toys, D-008/D-006/D-002 walk-throughs, the consensus rule (S7), normalisation ranges (S8), rescaling (S9), k and weight sweeps (S10), the repo transcription (S11), tokenizer (S12), depth (S13b).
2. **Stop-word votes (new, R1-E3):** per seed, BM25 list length, content-hit count, and the RRF top-4 with BM25 lists cut to content hits only. Assert D-008's BM25 list length 80 and that its ranks ≥ 2 have no content hit.
3. **Variants table on the same lists (new):** paper RRF (1-based, k = 60), 0-based (Weaviate, LlamaIndex), weighted RRF 0.6/0.4 (LangChain, OpenSearch), k = 0 with 0.8/0.2 (cookbook), min-max, three-sigma, TMM (cosine min −1 and 0). Count top-4 changes against paper RRF over the 10 seeds; assert the toy A-07 and A-08 answers.
4. **Framework-default replicas (pure Python, no install):** depth 4 with union output (LangChain), text-keyed dedup with two legs carrying different text (a header-prefixed BM25 text), the all-zero BM25 leg returning the last 4 chunks. Each is a failing case the tests in step 5 must catch.
5. **The fusion test suite**, run against the course `fuse_*` (must pass) and the repo transcription plus the step-4 replicas (must fail):
   - identity: w = 1 → dense order, w = 0 → BM25 order;
   - permutation invariance: reversing or shuffling the corpus storage order and the input dict order changes nothing (this is the test that the upstream code fails for any alpha, because its output depends on storage order);
   - monotonicity: raising one chunk's score in one list never lowers its fused rank;
   - catalogue membership: every fused id is in the chunk catalogue, and the output has at most k items;
   - dead leg: an empty or all-zero BM25 list gives exactly the dense order and raises a flag.
6. **Acronym probe set (new):** the regex acronym definitions (≈21, approx.) become "What does X stand for?" probes, with gold = the defining span. Dense vs BM25 vs RRF vs weighted: first-evidence rank and Hit@4. Label: a rule-built **probe**, a mechanism check, not the eval set.
7. **Plotly charts:** the vote curve, the Venn counts per seed, and the variants change matrix.
8. **Optional, replay only:** the same with cached Cohere `embed-v4.0` vectors from the C3 cache (1 query call for ≤ 96 questions if not cached); otherwise skipped with a message.

### 8. Apply-it tool plan and real-world checklist

`study/tools/fusion_fit_check.py`: "Does hybrid retrieval help on MY documents and questions, and is my fusion wired correctly?" It imports `bm25_fit_check.py` for chunking, tokenizers and the question format, so the two tools agree on everything up to fusion.
- **Inputs:** `--docs`; `--questions q.jsonl` (`q`, optional `expect`, `type`); `--tokenizer norm|split|code`; `--dense minilm|cohere` (Cohere through the cache only); `--k 4`; `--depth 50`; `--k-rrf 60`; `--weights 0.3,0.5,0.7`; `--norm minmax|z3|tmm`; `--probe-acronyms` (builds the probe set from the documents); `--check-fn module:function` (runs the test suite against the user's own fusion function); `--report out.md`.
- **Outputs (Markdown plus a Plotly HTML):** per type, Hit@k, MRR and first-evidence rank for dense, BM25, RRF and weighted; per-question ranks by source; leg statistics (content hits, dead-leg rate, one-leg share, ties); the variants table; the checklist; a recommendation.
- Like `bm25_fit_check.py`, it is not an evaluation: it shows the mechanism and whether the set can resolve the arms.

**Real-world checklist (12 checks):**

| # | Check | Auto / manual |
|---|---|---|
| H1 | Both legs index the same units; every fused id is in the catalogue | auto |
| H2 | The user's fusion function passes identity, permutation, monotonicity and dead-leg tests | auto (with `--check-fn`) |
| H3 | k_rrf, depth, weights, normaliser, rank base and tie rule are written in the config | auto (config) + manual (your production config) |
| H4 | The fused output is cut to k (the union is not passed on whole) | auto |
| H5 | The dedup key is the chunk id, not the text | auto (if `--check-fn`) + manual (framework `id_key`) |
| H6 | The BM25 tokenizer keeps your identifiers whole (reuses `bm25_fit_check` C2) | auto |
| H7 | Share of questions with no BM25 content-term hit (dead leg); flag above 20% | auto |
| H8 | Share of fused top-k chunks that come from stop-word-only BM25 matches | auto |
| H9 | Exact-term questions exist and dense misses some (else hybrid has nothing to fix) | auto (with `expect` + `type`) |
| H10 | Paraphrase questions do not lose rank under fusion (the D-006 guard) | auto |
| H11 | At least 10 labelled exact-term questions, else "cannot decide" | auto |
| H12 | Latency budget: p95 of BM25 + fusion vs the dense leg | auto (local timing) + manual (production budget) |

**Recommendation logic:**
- H1, H2 or H5 fails → "fix the fusion wiring first; any metric is meaningless".
- H6 fails → "fix the tokenizer (P3) before fusing".
- H9 shows no dense misses → "hybrid has nothing to fix here; keep dense".
- H7 high → "BM25 rarely matches content: check the tokenizer, or use dense alone".
- H10 fails while H9 gains → "use weighted fusion with a lower BM25 weight, and measure per type".
- H11 fails → "mechanism only; add exact-term questions (try `--probe-acronyms`)".
- Otherwise → "RRF k = 60 as the default; weighted as a tuned arm; confirm on held-out questions".

### 9. LLMOps notebook plan

`study/llmops/notebooks/R1_hybrid_ops.ipynb`: v2.0 as a traced, replayable experiment (foundation §12 row "5 · R1–R5"). **There is no LLM in the mechanism.**
- **Framework build** (after the plain-Python lesson):
  - `langchain-classic` `EnsembleRetriever(retrievers=[dense, bm25], weights=[0.5, 0.5], c=60, id_key="chunk_id")` over two small course retrievers:
    - `CourseDenseRetriever(BaseRetriever)`: `CachedEmbeddings` (foundation §9.3) + NumPy exact cosine, k = depth, returning `Document(metadata={chunk_id, score, rank})`;
    - `CourseBM25Retriever(BaseRetriever)`: `rank_bm25` with `tok_norm`, k = depth, content-hit flag in the metadata.
  - Mapping to the mechanism: retrievers → D.1 (two lists); `id_key` → the alignment rule; `c` → k_rrf; `weights` → weighted RRF; the course truncation to k → H4.
  - **A parity test:** the same fused ids, in the same order, as the course `fuse_rrf` on every qid. Ties are reported separately, because LangChain keeps first-seen order and the course breaks ties by `chunk_id`.
  - **Defaults the notebook demonstrates and overrides** ([R1-S5], [R1-S7]):
    - depth = each leg's k (4);
    - the union returned uncut;
    - `id_key=None` dedups by text;
    - `BM25Retriever` uses `split()`, no lower-casing, and returns zero-score documents;
    - LlamaIndex `QueryFusionRetriever` has `num_queries=4` (hidden LLM calls), `similarity_top_k=2`, and 0-based RRF that ignores weights.
  - `langchain-community`'s `BM25Retriever` appears in one read-only cell only. LangGraph is not used (linear flow).
- **External calls (all cached; the notebook runs in `replay` with no key):**

  | Call | Count | Notes |
  |---|---|---|
  | Cohere `embed-v4.0` `search_document` | **0 new** if the v1.x champion's index is in the C3 cache; otherwise the champion's chunk count ÷ 96 (≈ 2 calls for ≈ 100 chunks) | Same `embed_hash` as the champion; the run fails closed if it differs |
  | Cohere `embed-v4.0` `search_query` | **1** call (≤ 96 eval questions) + **1** for the ≈ 21 probe questions | Shared by every arm |
  | Groq `openai/gpt-oss-20b` (`reasoning_effort=low`) | **≈ 35 calls**: the adopted arm on ≈ 16 dev items + ≈ 16 test items (the champion's answers are already cached), plus a few probe answers | ≈ 35 × (1,500 × 0.075 + 512 × 0.30)/10⁶ ≈ **$0.01**; about 70K tokens, within one day of the free-tier TPD (plan UNVERIFIED). Only if the per-technique gate's generation table is filled |
  | Claude | **0** | No LLM step worth a larger model; a generator swap would be a new arm (foundation §6.4) |
  | Judge | **0** (D-10) | Stored traces feed the end batch |

- **Tracing** (JSONL default, viewed in Phoenix; LangSmith only for Corpus D inside `tracing_context(enabled=True)` after `privacy.assert_corpus_is("D")`):
  - per qid, one retriever span per leg: ranked `chunk_id`, score, rank, `content_hit`, plus `n_returned` and `n_content_hits`;
  - a fusion span: method, k_rrf, depth, weights, normaliser, rank base, tie rule, the fused list with `ranks_by_source`, `n_both`, `n_one_leg`, `ties_in_topk`, and the leg each final chunk came from;
  - an embedding span: cache hits and misses;
  - latency per leg and for fusion (06 `latency_ms.dense/bm25/fusion`);
  - BM25 library and version, tokenizer name and version, `bm25.text_field`;
  - about 4 arms × ≈ 55 questions ≈ 220 traces per run, within the LangSmith free plan.
- **Dataset and evaluators:**
  - the M1 golden set (dev for selection, test once) and the probe set as a separate, labelled diagnostic dataset;
  - Tier-1 code evaluators (foundation §5): CE@4, MRR@10, Hit@4, first-evidence rank, `one_leg_share`, `dead_leg`, ties, and question–gold lexical overlap per category;
  - the fusion property tests as evaluators that must be 1.0 on every run;
  - generation, if run: EM/F1, citation page-hit, abstention string, `finish_reason = length`, and about 10 read answers (D-10);
  - `langsmith.evaluate(..., upload_results=False)` shown once as the framework view (`rag-evaluation`, `code-based-evaluators`).
- **Experiment against the previous version** (06 §4.1 rule 1):
  - arms A0 = v1.x champion (dense), A1 = BM25 alone, A2 = RRF (k = 60, depth 50), A3 = weighted (w from {0.3, 0.5, 0.7} on dev; min-max, with TMM as a pre-registered variant only if Yash agrees, §11);
  - each against the **champion** (primary) and **v0 (E000)**, with identical comparison keys;
  - per-category CE@4; the H1 slice with the exact sign test; "inconclusive" pre-registered as expected on D;
  - `experiments/E020_v2.0_hybrid_rrf/` (06 §2.5 run id); `TEST_LOG.md` records the number of arms tried.
- **Cost, latency and tokens:** BM25 build time; p50/p95 per leg and for fusion; embed calls ("cost if called" vs paid = 0 on replay); generation tokens and cost if run; mean context tokens per arm (equal k, so equal unless the union leaks, H4).
- **Config versioning:** a `retrieval.hybrid` block in `config.yaml` → `config_hash` (R1-E6):
  - `fusion: rrf | weighted`, `k_rrf`, `depth`, `weights`, `normaliser`, `missing_value`, `rank_base`, `tie_rule`;
  - `bm25: {lib: rank_bm25, version: 0.2.2, k1, b, epsilon, tokenizer, tokenizer_version, text_field, depth_rule: all_positive | content_hit}`.
  The prompt `answer_v1` is unchanged (one variable).
- **Monitoring and feedback:**
  - T1 tests on every commit: the fusion property tests, the parity test, CE@4 and MRR ≥ champion − tolerance on cached vectors, and a cap on worsened qids (M4-E5).
  - Alerts (monitor page, foundation §8.3): dead-leg rate, one-leg share of the top-k, any fused id outside the catalogue (hard fail), a change in BM25 N or avgdl after re-indexing (scores move, so weighted arms need re-tuning), and the tie rate.
  - A query where dense and BM25 disagree and the gold is lost goes to the M5 log under "exact-term miss" or "paraphrase loss", then into the golden set as a new version (`error-analysis`, `ci-cd-evals`).
- **Place in the lifecycle:**
  - Analyze: v0.1/v1.x buckets name exact-term misses (`error-analysis`); per-leg patterns across traces (`trace-data-analysis`).
  - Measure: per-category retrieval metrics (`rag-evaluation`, `code-based-evaluators`).
  - Improve: adopt RRF, adopt weighted, or keep the champion (`improving-llm-agents` for the latency side).
  - dev → CI → monitoring: the tests and alerts above (`ci-cd-evals`); tracing (`llm-observability`); framing (`evals-foundations`).

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Fusion, normalisers, tests, probe builder | own code (`ragkit/retrieval.py` per lesson H.3) | — | — | yes | — | — | yes |
| BM25 | `rank-bm25` (`BM25Okapi`) | 0.2.2 | yes | yes | — | Apache-2.0 | yes |
| Arrays | `numpy` | 2.5.3 | yes | yes | — | BSD-3 | yes |
| Sign test | `scipy.stats.binomtest` | 1.18.1 | yes | yes | — | BSD-3 | yes |
| Local dense leg (fallback, verify notebook) | `sentence-transformers` + `all-MiniLM-L6-v2` | 6.1.0 | yes | yes (HF cache) | — | Apache-2.0 | yes (D-03 fallback) |
| Default dense leg | Cohere `embed-v4.0` via `cohere` | 7.2.0 | yes | replay only | 0–2 document calls + 2 query calls; price UNVERIFIED | MIT (SDK) | yes (D-03) |
| PDF snapshot | `pymupdf` | 1.26.7 | yes | yes | — | AGPL | yes (pinned) |
| Charts | `plotly` | locked | yes | yes | — | MIT | yes |
| LLM, generation table only | Groq `openai/gpt-oss-20b` | from `.env` | SDK yes | replay only | ≈ 35 calls ≈ $0.01 | — | yes (D-04) |
| LLM, larger model | Claude: **not needed** (no LLM in the mechanism) | — | no | — | 0 | — | yes (D-32 allows; not worth it) |
| Framework core | `langchain-core` | 1.6.6 | no | yes | — | MIT | yes (foundation §11) |
| Hybrid retriever (LLMOps parity) | `langchain-classic` (`EnsembleRetriever`) | 1.0.8 | no | yes | — | MIT | yes; deps sqlalchemy, requests, pyyaml, langsmith (light) |
| Framework BM25 (read-only cell) | `langchain-community` (`BM25Retriever`) | 0.4.2 | no | yes | — | MIT | optional; already pulled in if Phase 4 adds `langchain-experimental` |
| LangGraph | not needed (linear flow) | — | — | — | — | MIT | n/a |
| Provider integrations | `langchain-cohere` / `langchain-groq` **not used** (pin conflicts) | — | no | — | — | MIT | adapters instead (foundation §9.3) |
| Hosted tracing | `langsmith` | 0.14.4 | no | no | free plan; ≈ 220 traces per run | MIT (SDK) | yes, Corpus D only |
| Local tracing | `arize-phoenix-otel` 0.17.2 + server via `uvx arize-phoenix@20.19.0` | — | no | yes | — | Apache-2.0 / ELv2 | yes |
| Reading only | `llama-index-core` `QueryFusionRetriever` | 0.14.25 | no | — | — | MIT | read the source; do not install |
| Reading only | Weaviate, Elasticsearch, OpenSearch hybrid docs | — | no | — | — | — | servers: not used (Docker; outside local-first) |
| Next only | SPLADE (`naver/splade`) | — | no | — | GPU-friendly, CPU slow | **CC BY-NC-SA 4.0** | not for v2.0; needs a decision only if Yash wants a learned-sparse arm |
| Not needed | `bm25s` (fast BM25) | 0.3.12 | no | yes | — | MIT | no (rank_bm25 is the course reference; noted in phase_01) |

**Install lines (do not run):**
```text
uv add --group llmops langchain-core==1.6.6 langchain-classic==1.0.8 langsmith==0.14.4 arize-phoenix-otel==0.17.2
uv add --group llmops langchain-community==0.4.2      # optional, only for the read-only BM25Retriever cell
```
Nothing new is needed for the lesson, the verify notebook or the apply-it tool.

**Keys:**
- `COHERE_API_KEY` (present): only if the champion's vectors or the query vectors are not yet cached;
- `GROQ_API_KEY` (present): only for the optional generation table;
- `LANGSMITH_API_KEY`: only for the hosted view.

After recording, no keys are needed.

### 11. Open questions for Yash (preferences only)

1. Build the **acronym probe set** from Corpus D (≈21 rule-made "What does X stand for?" items), verify them by hand, and add them to the eval set as a new version's `exact-term` items, so v2.0's H1 slice can resolve anything? **yes** / no (no = v2.0 on Corpus D is expected to end "inconclusive").
2. Rewrite R1 in the HTML house format **now**, with the study-kit pass, or after v2.0 runs? **now** / later.
3. Add a **TMM** variant of the weighted arm (cosine minimum −1) as a pre-registered option? yes / **no** (keep min-max as the single weighted arm; show TMM in Full and in the verify notebook only).
4. BM25 list policy for v2.0: keep every positive score (the library default, recorded) or cut to **content-term hits**? **keep the default and report content hits** / cut.

---

## Concept R2: Metadata filtering (U, project v2.2)

R2 adds a hard constraint to retrieval: only chunks whose metadata matches a scope (a document, a chapter, a section, a year, a tenant) may be returned. The mechanism is small. With the course's exact NumPy search (D-07) a pre-filter is one boolean mask over the score vector. The hard parts are elsewhere: **where** the filter is applied (before, after or inside the search), **where it comes from** (the user, a rule, an LLM), **whether the metadata is right**, and **how to measure it**, because a wrong filter silently deletes the gold evidence. The 06 v2.2 card plans the experiment on Corpus T only, since Corpus D is one document. This section shows that D still has a natural scope (21 chapters, 68 sections, and 11 heading titles that repeat across chapters), so the mechanism, the post-filter recall loss and the filter-error accounting can be taught and verified on D now. The adopt/reject decision waits for T, whose required property is stated in §6.

### 1. Sources checked

**Book (not present; per 02/04, not re-opened, UNVERIFIED).** No chapter teaches metadata filtering (02 R2 card; 03 §2.2 row 12).
- Ch14 p.9–10/13, "the role of metadata" (02 R2 card; 04 §3 Ch14). C3's lesson paraphrases it: page numbers link the summary level to the chunk level, and many documents need document plus section ids (`concepts/C3_embedding_indexing.md` L125).
- Ch14 p.7/13 (the hierarchical sketch: top summaries → section ids → filtered detail search). 04's R2 row cites it; 02's card does not. `P5_FACTS.md` L185 also reads p.7/13 as "filter by section identifiers". Reported as a disagreement (R2-E4).

**Repo (verified: `NirDiamant/RAG_Techniques` @ `009adba`, downloaded to the session scratchpad, cells read 0-based with `python3 -I`; code not run; custom non-commercial licence, described not quoted):**
- `all_rag_techniques/multi_faceted_filtering.ipynb` (26 cells, **no saved outputs**):
  - cell 8: one `Document` per CSV row, metadata `country, company, city, subscription_date, website`;
  - cell 10: MiniLM embeddings into a Chroma store (`Chroma.from_documents`);
  - cell 12: baseline `similarity_search_with_relevance_scores(query, k=10)`;
  - cell 14: `apply_metadata_filter` keeps pairs whose metadata equals the given values, **applied to the top-10 list** (post-filter), exact case-sensitive equality;
  - cell 16: `apply_similarity_threshold(threshold=0.35)`; the text says to tune it, but no labelled data exists to tune it on (MC-006 pattern);
  - cell 18: keyword filter; cell 20: greedy near-duplicate filter at cosine 0.9 (an R4/X3 idea, not R2);
  - cell 22: the four filters composed; every filter value is typed by hand;
  - cell 24: the same hand filter `{"country": "Chile"}` while the query text already says "Chile"; the answer comes from OpenAI `gpt-4o` (outside the project decisions).
  - **Data (verified on `data/customers-100.csv`):** 100 rows, 85 distinct countries, **Chile = 1 row**, at most 4 rows per country. So the demo cannot show starvation or recall loss: the only Chile row is also the one the query names. 02's "data too thin" and 04's "demo has one matching row" are both correct.
- `all_rag_techniques_runnable_scripts/multi_faceted_filtering.py` (194 lines): filters L44–L131, `main` L134–L190; no LLM; the metadata filter is applied only if `--country` is passed (L174). 04's "L20–L131 (filters L44–L131; no LLM)" is correct.
- `all_rag_techniques/hierarchical_indices.ipynb` cell 15 (= `hierarchical_indices.py` L71–L82, matching 04): for each of the top-3 page summaries, `detailed_vectorstore.similarity_search(query, k=k_chunks, filter=lambda metadata: metadata["page"] == page_number)` with `k_chunks=5`. The store is LangChain FAISS, which post-filters the top `fetch_k = 20` (verified below). On D a page holds about 3 v0 chunks (97/33), so "5 per page, up to 15" can never be reached, and a page whose chunks are not in the global top-20 returns fewer, or none. The closure over `page_number` is used immediately inside the loop, so it is not a bug.

**Existing course files:** 02 R2 card (L674–L686), C3 card, D4 card (L933–L941), §4 per-technique gate, §5 VAI L23 row, §7 L1298; 03 rows L42/L47, registry L435, L480–L481, L532, L693, L753, §6.4 L859; 04 R2 row L175, C3/C4 rows, Ch14 table L643–L656, L922; 06 §2.3–2.5, §4 v1.1 and v2.0–v2.3 cards (L586–L630), §5.1, §6.1–6.4, §7.3 (L1060–L1092); 08 D-01, D-02, D-07, Part 2 L349, Part 7 DEC-3; external review L255 (AIQ 04 Q23 item) and L264 (empty-context path); `concepts/P5_vector_search.md` D.4–D.5 and `P5_FACTS.md` S6 (a measured pre- vs post-filter demo on D already exists: filter `page ≥ 25` keeps 23/91 chunks; over 35 queries, pre-filter returns short lists 0 times, post-filter with `fetch_k = 20` 9 times); `concepts/C3_embedding_indexing.md`; `sources/vai/L19-L23_core_rag.md` (L20, L23 filter notes); tracker (R2 `not_started`, linked to O1-Q12, where Yash "missed version metadata/filtering"); MC-005, MC-006; phase_04 I2 (Corpus D heading tree) and phase-level note "R2: `section_path` gives section-scoped metadata filters"; LLMOPS_FOUNDATION §2–§12. No `concepts/R2_*`, `study/reading/R2_*`, `study/questions/R2_*`, `labs/R2_*` or `sources/verification/R2/` exists (checked; the `*R2*` files in `reviews/` are review round 2).

**Corpus D scope structure (re-measured in this session; poppler `pdftohtml -xml -zoom 1`, session scratch scripts (not course files); approximate):** PDF sha256 `1d58a0fa…92669` matches C3_FACTS. Heading counts 1 / 21 / 68 / 192 and the same 11 repeated titles as phase_04 I2 (independent confirmation). Chapters start mid-page (20 of 21), so **page is not a chapter key**. A simplified splitter gives 120 chunks instead of the measured 97, so only orders of magnitude are reported: a chapter covers about 1–10 chunks (selectivity ≈ 1–10%), and a few per-page chunks overlap two chapters, while more (≈ 15%) overlap two sections. Chunk → scope is therefore one-to-many unless v1.1's structure chunks are used.

**Interview repo (AIQ @ `e080df2`, MIT, "Copyright (c) 2026 Om"; verified):** `04-rag-and-retrieval/questions.md` Q8 (exact search composes trivially with filters), Q14 (chunk metadata; ACL enforced in the retrieval filter), Q22 (follow-up: a 5%-selectivity tenant filter), **Q23** (pre- vs post-filtering; starvation; selectivity spectrum; partitioning), Q34 (time: hard filters for correctness, recency as a soft boost).

**External (numbered in "R2 sources"):** [R2-S1] ACORN paper · [R2-S2] Weaviate filtering docs · [R2-S3] Qdrant indexing and query-planning docs · [R2-S4] pgvector README · [R2-S5] FAISS `IDSelector` wiki · [R2-S6] LangChain FAISS and InMemoryVectorStore source · [R2-S7] LangChain `SelfQueryRetriever` and `langchain-groq` structured-output source · [R2-S8] Chroma `where` grammar · [R2-S9] Groq structured-outputs page · [R2-S10] filter-agnostic vector search study.

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Chunk metadata stored aligned with vectors (`doc_id`, page, offsets) | every filter | P5 D.4, C3 (written) | P5 / C3 | no (both `not_started`) | bridge | 4-line recap: row i of `vectors.npy` ↔ line i of `chunks.jsonl`; a filter reads the second |
| 2 | Scope metadata beyond page: chapter, `section_path`, from the heading tree | D experiment | **missing** (I2 plans it; not built) | I2 → R2 | no | bridge | Reuse I2's tree; R2 only adds "tag every chunk with the scopes it overlaps" |
| 3 | Chunk → scope can be one-to-many (chunks that cross a chapter or section) | metadata reliability | **missing** | R2 | no | core | Store scopes as a **set**; filter = "any overlap" (recall-safe); count crossing chunks |
| 4 | Pre-filter as a mask: `score[~allowed] = −∞`, then top-k | the mechanism | P5 D.4 (one demo) | P5 → R2 | no | core | Formula + the D example; exact search makes it exact (D-07) |
| 5 | Post-filter: fetch k′, drop non-matching, keep k | upstream cells 14, 15 | P5 D.4–D.5 (fetch_k = 20, 9/35 short) | R2 | no | core | Reuse P5's measured numbers; add the formula (#6) |
| 6 | **Expected survivors ≈ s·k′**, P(none) = (1 − s)^k′, k′ ≥ k/s | 02 outcome "compute the recall loss" | **missing** | R2 | no | core | Derivation + table (§6); pgvector's own example (10% × 40 = 4) [R2-S4] |
| 7 | Gold-level recall loss of post vs pre: lost iff gold's in-scope rank ≤ k but its full rank > k′ | 02 outcome | **missing** | R2 | no | core | Rank formula; show one D item where it happens |
| 8 | Correlation between filter and query (independence is an assumption) | when s·k′ is wrong | **missing** | R2 | no | core (Full detail) | Positive correlation (scope named in the question) beats s·k′; negative (near-duplicate in another chapter) does worse [R2-S1, S2] |
| 9 | Post-filter with k′ = N equals pre-filter | sanity test | **missing** | R2 | no | core | One property test |
| 10 | In-graph filtered ANN (allow-list traversal, filterable HNSW, ACORN, brute-force cutoff, partitioning) | current practice; P5's HNSW | P5 (HNSW idea only) | R2 (Full) | no | next / Full | One table; not run (D-07 exact search) |
| 11 | Same `filter=` argument, opposite semantics across libraries | LLMOps notebook | P5 D.5 (FAISS only) | R2 | no | core | LangChain FAISS post-filters (fetch_k 20); `InMemoryVectorStore` pre-filters [R2-S6] |
| 12 | Filter dialects and missing fields (`$neq` vs `$ne`; a missing key passes `$neq`) | framework arm | **missing** | R2 | no | core (Full) | Two-line table; test that a chunk with no `chapter` field is handled by policy |
| 13 | Where filters come from: UI / explicit user choice, rules + alias table, LLM extraction (self-query), router | 02 outcome 3 | **missing** | R2 (router = A1) | no | core | Three-row comparison: cost, error type, who is accountable |
| 14 | Structured output for LLM extraction (JSON schema, enum of allowed values, "none") | LLM arm | P1/P7 partly; 03 §2.2 row 14 says unowned | M3/P7 (unowned) | no | bridge | Enum-constrained schema with an explicit `none`; strict mode on gpt-oss-20b [R2-S7] |
| 15 | A filter error is a **hard failure**; filter-removed-gold rate | 06 v2.2 guard | **missing** (named, not defined) | R2 | no | core | Operational definition via CE over the whole allowed set (§6 idea 8) |
| 16 | Over-filtering vs under-filtering: emitting a filter on an unscoped question | evaluator | **missing** | R2 | no | core | False-filter rate on unscoped items; the extractor must say `none` |
| 17 | Fail-open vs fail-closed: relevance filters fall back; access filters never do | R2 → D4 | 03 L481 (one line) | R2 / D4 | no | core | Contrast box; D4 reuses the module with `on_error = deny` |
| 18 | Empty or short list after filtering: abstain, backfill, or relax | X3 empty-context path | ext review L264 (plan) | X3 | no | bridge | Policy is pre-registered; an emptied list is logged as an error, never a correct abstention (AIQ 04 Q23 item) |
| 19 | Hard filter vs soft boost (score bonus) | current practice; AIQ Q34 | **missing** | R2 | no | core (Full) | One paragraph: boost keeps recall when scope extraction is unsure |
| 20 | Oracle filter = scope derived from gold spans; an upper bound for filtering, not retrieval | 06 arms | **missing** (06 names it, never defines it) | R2 | no | core | Definition; OR-alternatives across scopes need a union (D-004: Ch5 and Ch15) |
| 21 | "Scope-specified" items and a `scope` label | 06 primary metric | **missing** (no field, no category, 06 §6.2) | M1 / R2 | no | core | Define the field and bucket (§6, R2-E3); share with I2's `section_scoped` |
| 22 | Which metric moves: CE@4 and MRR vs Precision@4 vs scope-precision@4 | 06 v2.2 | 06 §7.3 (Precision traps) | M2 | M2 exposed | core | Show that a correct filter can leave Precision@4 flat (R2-E2) |
| 23 | Confound: scope words in the question also help dense/BM25 without any filter | D experiment | **missing** | R2 | no | core | Same question text in every arm; only the filter varies |
| 24 | Filter composed with hybrid (both legs before RRF) and with the reranker pool | v2.2 on the v2.1 champion | **missing** (06 card silent) | R1 / R3 | R1 exposed | bridge | Mask both legs; keep full-corpus BM25 statistics (state it); pool from filtered candidates |
| 25 | k trade-off (MC-005) and its link to k′ | starvation | C4 (not studied), MC-005 open | C4 | no | bridge | "k′ is a second k": larger k′ costs nothing with exact search |
| 26 | Uncalibrated score thresholds (cell 16) | upstream critique | M3 (exposed); MC-006 open | M3 / V2 | M3 exposed | bridge | One line: a 0.35 cut on an unlabelled score is a guess; link MC-006 |
| 27 | Paired comparison, sign test, small n, "inconclusive" | the experiment | M4 (planned) | M4 | no | bridge | Link; per-arm b/c against the champion |
| 28 | Access control as a pre-filter (D4) | 02 D4 outcome | — | D4 | no | next | Link only |
| 29 | Hierarchical retrieval is a coarse filter with no fallback | R5 | — | R5 | no | next | Link: same starvation math (cell 15) |

### 3. Quiz coverage

No question file exists. Needed titles (R = recall, A = application, T = transfer):
- **R-01** What is the difference between pre-filtering, post-filtering and filtering inside an ANN graph?
- **R-02** Why can LangChain's FAISS `similarity_search(…, filter=…)` return fewer than k results, while `InMemoryVectorStore` with the same argument cannot?
- **R-03** What is the filter-removed-gold rate, and why is a filter error a hard failure that reranking cannot repair?
- **R-04** Why is an oracle filter an upper bound for filtering but not for retrieval?
- **R-05** Why does a relevance filter fail open and an access-control filter fail closed?
- **A-01** Selectivity s = 0.05, k = 4, fetch_k = 20: expected survivors, P(no survivor), and the k′ needed for 4 survivors on average. (★ 1.0; 0.358; 80.)
- **A-02** Given an unfiltered ranking with scope labels and the gold chunk at full rank 9 and in-scope rank 2: is it in the top-4 under pre-filter, post-filter with k′ = 4, and k′ = 20?
- **A-03** Given 10 extracted filters and gold scopes (some items unscoped), compute exact-match, gold-kept and false-filter rates.
- **A-04** A chunk spans the end of Chapter 15 and the start of Chapter 16. Under "start-chapter" tagging and under "any-overlap" tagging, does a `chapter = 16` filter keep it? Which choice is recall-safe?
- **T-01** Corpus T has 6 papers and the user asks "What does the HyDE paper say about …?". Design the filter source, the alias table and the fallback when the extracted paper is not in the index.
- **T-02** A multi-tenant product has 10,000 tenants; the largest holds 10M vectors and the median 5k. Pre-filter, post-filter, filtered HNSW or partition? (From AIQ 04 Q23's follow-up.)
- **T-03** Your filter raised Precision@4 but CE@4 fell on unscoped questions. Name two mechanisms and the trace field you read first.
- **Interview:** AIQ 04 Q23 "How does metadata filtering interact with ANN indexes? Explain pre- vs post-filtering." (MIT, Copyright (c) 2026 Om). Key: starvation at low selectivity, graph connectivity under strict filters, brute-force the subset, partition by a known key, ask for the selectivity distribution first.
- Review item kept from the external review (L255): "You take the top 4, filter to one document, and get 1 back. Why?"

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| R2-E1 | 06 v2.2 "When NOT to use: single-document corpora (Corpus D)" and "Corpus T only" | Too strong. A long single document has internal scopes. D has 21 chapters, 68 sections and 11 heading titles that repeat in different chapters ("Paris Agreement" p.10 in Ch6 and p.23 in Ch16), which are exactly 06 §6.2's near-duplicate distractors. A question that names a chapter is a valid within-document filter case | "When NOT to use: questions that never name a scope, or metadata you cannot trust." Run the mechanism on D (chapter scope); keep the decision on T |
| R2-E2 | 06 v2.2 "Primary Precision@4 on scope-specified items" vs 03 §6.4 "CE@k and Precision@k on scoped questions" | Two files disagree. And Precision@4 (gold `any_overlap` relevance, 06 §7.3) is a weak primary: a correct filter mostly swaps out-of-scope non-gold chunks for in-scope non-gold chunks, so Precision@4 can stay flat while the evidence arrives; it also rewards overlap duplicates (06 §7.3 trap) | Primary **CE@4 on scope-specified items**; diagnostics MRR@10 and **scope-precision@4** (share of top-4 inside the gold scope, the filter's direct job); keep Precision@4 as a reported diagnostic |
| R2-E3 | 06 v2.2 ("scope-specified"), 06 v1.1 ("section-scoped"); 06 §6.1–6.2 schema | Neither bucket is defined; no item field says what scope a question names, so the rule arm cannot be scored and the oracle arm cannot be built. phase_04 reported the same for `section_scoped` (I2-E3) | Add optional `scope` (`{doc_id?, chapter?, section_path?, year?}`, derived from the gold spans) and `scope_mention` (`explicit` / `implicit` / `none`) in a new dataset version, frozen before v2.2. "Scope-specified" = `scope_mention = explicit`. One definition shared with I2 |
| R2-E4 | 04 R2 row (Ch14 p.7/13 and p.9–10/13) vs 02 R2 card (p.9–10/13 only) | Page sets differ; `P5_FACTS.md` L185 also cites p.7/13 | Use the union, Ch14 p.7/13 and p.9–10/13 (UNVERIFIED here; settle in the local pass) |
| R2-E5 | 03 registry row 435 (R2 prerequisites: R1 only) vs 02 R2 card (Pre: C3, R1) | C3 is missing in 03 (the same pattern as I2-E1) | Add C3 to row 435 |
| R2-E6 | 04 Ch14 table step 4–6 ("k_chunks=5 *per page*, up to 15 chunks") | On D a page holds about 3 v0 chunks (97/33), so 15 is unreachable; and the FAISS filter post-filters the global top-20, so a selected page can return 0 chunks | "Up to 5 per page in principle; on D at most the page's own ~3, and fewer when they are outside the global top `fetch_k = 20`" |
| R2-E7 | 02 §7 L1298 ("a good case for teaching the recall cost of post-filtering") and 03 L532 ("Post-filtering after top-k loses recall (cells 12–14)") | The notebook cannot show a loss: no saved outputs, one Chile row, and the query names Chile, so the filter is perfectly correlated with the ranking | "Shows the post-filter *pattern*; the recall cost must be shown on our data (P5 D.4 and the R2 verify notebook)" |
| R2-E8 | 06 v2.2 "Change: pre-filter on metadata before scoring" | Silent on composition with the v2.0 hybrid (filter both legs before RRF? BM25 statistics on the full corpus or the subset?) and the v2.1 reranker pool; and on what happens when the allowed set has fewer than k chunks | Add: mask both legs before fusion; keep full-corpus BM25 statistics (one-variable rule); the rerank pool is drawn from allowed chunks; a pre-registered `on_short` policy |
| R2-E9 | 06 v2.2 Hypothesis ("a rule-based filter … extracted from the question") | Writing rules while reading the eval questions leaks the test into the extractor | Build the alias table from metadata only (titles, headings, file names), freeze it before scoring, and report rule accuracy on test once |
| R2-E10 | 02 R2 card "Ext: none specific" | External sources exist and are needed for the current-practice part | Add [R2-S1] ACORN, [R2-S4] pgvector, [R2-S2]/[R2-S3] vendor docs |
| R2-E11 | LLMOPS_FOUNDATION §9.2 defaults table | No rows for: LangChain FAISS `filter` (post-filter, `fetch_k = 20`, no warning when short; MMR fetches `2·fetch_k`); `InMemoryVectorStore` `filter` (pre-filter, exact); the `$neq` (LangChain FAISS) vs `$ne` (Chroma) dialect and missing-key semantics; `SelfQueryRetriever` (`use_original_query=False` rewrites the query too; `fix_invalid=False` raises on an unknown attribute; no translator for FAISS or InMemory) | Add the rows [R2-S6, S7, S8] |

### 5. What the research says

**[R2-S6] LangChain's two meanings of `filter=` (source read: `langchain-community` 0.4.2 wheel, `langchain-core` 1.6.6 wheel; verified).**
- *What the code does.* `FAISS.similarity_search_with_score_by_vector` (`faiss.py` L387–L450) searches `k if filter is None else fetch_k` vectors (L417; `fetch_k: int = 20`, L392), applies the filter to that list, then returns `docs[:k]` (L450). Nothing warns when fewer than k survive. MMR with a filter fetches `fetch_k * 2` (L703). Dict filters support `$eq, $neq, $gt, $lt, $gte, $lte, $in, $nin, $and, $or, $not`; values are read with `doc.get(field)` (L1429), so a chunk **missing** the field passes a `$neq` test (fail open). The line numbers equal the 0.4.1 values P5 recorded.
- `InMemoryVectorStore._similarity_search_with_score_by_vector` (`in_memory.py` L291–L332) filters the document list **first**, then computes cosine over the survivors and takes the top k: an exact pre-filter.
- *For the project:* the same keyword means post-filter in one store and pre-filter in another. The lesson shows both, and the LLMOps notebook asserts the behaviour with a short-list test.

**[R2-S4] pgvector README (master, install line v0.8.7; verified).**
- *What it says:* with approximate indexes, filtering is applied after the index is scanned; "if a condition matches 10% of rows, with HNSW and the default `hnsw.ef_search` of 40, only 4 rows will match on average." Since 0.8.0, *iterative index scans* keep scanning until enough rows pass (bounded by `hnsw.max_scan_tuples`). It recommends a B-tree index on the filter column (exact search) for conditions that match few rows, partial indexes for a few distinct values, and partitioning (or separate tables) for many values and for multi-tenancy, because tenants sharing one approximate index affect each other's recall.
- *Limits:* documentation, not a measurement.
- *For the project:* this is exactly the s·k′ formula (0.1 × 40 = 4) stated by a production system, and its three remedies (exact on the subset, partition, iterate) are the lesson's decision table.

**[R2-S1] Patel, Kraft, Guestrin & Zaharia 2024, "ACORN: Performant and Predicate-Agnostic Search Over Vector Embeddings and Structured Data", SIGMOD (arXiv 2403.04871).** Search-checked; the paper page was blocked. The official code repo README was opened (verified): ACORN is an index built on FAISS, constructed as `IndexACORNFlat(d, M, gamma, M_beta)`, and searched with a per-query bitmap of the entities that pass the predicate.
- *Study (per search summaries):* hybrid queries that combine a vector with an arbitrary predicate; baselines include pre-filtering, post-filtering and specialised filtered indexes that support only small sets of equality filters.
- *Result (per the abstract, search-checked):* "predicate subgraph traversal" over an HNSW whose neighbour lists are expanded (γ·M candidates per node) keeps the filtered subgraph navigable; ACORN-γ reports 2–1,000× higher QPS at 0.9 recall than prior methods, the largest gain on a 25M-vector dataset.
- *Limits:* later independent studies report weaker results at very low selectivity and for conjunctions (AND) of predicates [R2-S10, search-checked only]; more memory and build time for the expanded lists.
- *For the project:* this explains **why** in-graph filtering exists (post-filtering starves; pre-filter + brute force does not scale), and why selectivity **and correlation** with the query decide the strategy. It is Full-only reading: the course uses exact search (D-07), where pre-filtering is exact and free.

**[R2-S2] Weaviate filtering docs (`weaviate/docs` main, `concepts/filtering.md` and `config-refs/indexing/vector-index.mdx`; fetched raw 2026-10-17; verified; vendor).**
- Pre-filtering through an inverted index builds an **allow-list**; HNSW traversal still follows every edge but only allowed ids enter the result set. Default `filterStrategy` is `acorn` since v1.34 (a custom implementation "inspired by" the paper: ignore non-matching nodes in distance computations, multi-hop neighbourhood, extra random entry points that match the filter); `sweeping` and `pathseer` (v1.40) are alternatives.
- `flatSearchCutoff` default **40000**: below that many allowed objects, Weaviate switches to brute force over the allowed set. The docs' figure illustrates a cutoff at about 15% of the dataset.
- The docs name the two post-filter failures: an unpredictable result count, and possibly zero matches for a restrictive filter.
- *Limits:* vendor claims ("recall typically not any worse") without a public benchmark on that page.
- *For the project:* the engine-side answer to starvation is "pre-filter by allow-list, brute-force when the allow-list is small". At our corpus size (about 100 chunks) every filter is far below any such cutoff, so exact masking is what a production engine would do too.

**[R2-S3] Qdrant docs (`qdrant/landing_page` master: `manage-data/indexing.md`, `search/search.md`; verified; vendor).**
- Payload (metadata) indexes should exist **before** ingesting data: the filterable HNSW adds extra graph edges per indexed payload value, and those edges are built only after the payload index exists.
- The query planner estimates the filter's cardinality and uses a full scan below `full_scan_threshold` (example config 10000 KB); weak filters use HNSW as is; for strict filters it retrieves points through the payload index and rescores them exactly.
- Extra edges are per payload field, not per combination, so two strict filters together can still disconnect the graph; ACORN-style two-hop search is offered from v1.16.0.
- *For the project:* "metadata reliability at index time" is literal here: an index built before the metadata exists filters badly. The course analogue is the rebuild rule (C3): a change to the metadata schema or the heading rules changes the index manifest.

**[R2-S5] FAISS wiki, "Setting search parameters for one query" (verified).** A subset of ids is searched by passing an `IDSelector` in `SearchParameters(sel=…)` (`IDSelectorRange`, `IDSelectorArray`, `IDSelectorBatch`, `IDSelectorBitmap`, `IDSelectorNot`, `PyCallbackIDSelector`). For IVF, ids are checked during the scan rather than pre-filtered; `IndexFlat` has fast paths for ranges and arrays. *For the project:* the native FAISS route is a selector, not LangChain's post-filter. Not needed (D-07); one Full-only line.

**[R2-S7] Where filters come from: self-query and structured output (source read: `langchain-classic` 1.0.8, `langchain-groq` 1.1.3 wheels; verified).**
- `SelfQueryRetriever` (`retrievers/self_query/base.py` L237–L405) runs a query-constructor chain (`prompt | llm | output_parser`, `chains/query_constructor/base.py`) that returns a `StructuredQuery(query, filter, limit)`. Defaults: `use_original_query=False`, so the LLM also **rewrites the semantic query** (a second variable in an experiment); the parser maps `"NO_FILTER"` to no filter and, with `fix_invalid=False`, raises `OutputParserException` on an attribute or comparator it does not allow; it needs `lark` (`parser.py`). Built-in translators cover Chroma, Qdrant, Weaviate, PGVector, Pinecone and others, **but not FAISS or `InMemoryVectorStore`** (a `ValueError` is raised).
- `ChatGroq.with_structured_output` defaults to `method="function_calling"`; with `method="json_schema", strict=True` it uses Groq's constrained decoding, which the source says is supported **only for `openai/gpt-oss-20b` and `openai/gpt-oss-120b`**, and which needs `additionalProperties: false` and every property in `required` (L983–L991, `_STRICT_STRUCTURED_OUTPUT_MODELS` L78–L81).
- *For the project:* LLM extraction is feasible with the default Groq model, with the allowed values as an enum and an explicit `none`. But the LLMOps notebook builds the extractor on `CachedChatModel` (the official `langchain-groq` conflicts with `groq` 1.7, LLMOPS §9.3) and translates the result into our NumPy mask; `SelfQueryRetriever` is shown read-only. Groq's own page [R2-S9] could not be opened here, so "gpt-oss-20b supports strict JSON schema" is **verified only through the langchain-groq source**, not through Groq's docs in this session.

**[R2-S8] Chroma `where` grammar (`chromadb-client` 1.5.9 wheel, `base_types.py` L129–L149; verified).** Operators `$eq, $ne, $gt, $gte, $lt, $lte, $in, $nin, $contains, $not_contains, $and, $or`; values are flat str/int/float/bool. Chroma spells "not equal" `$ne`, LangChain FAISS spells it `$neq`. The VAI L20/L23 notes already show Chroma's `where` used as a pre-filter inside the query (verified there). Chroma is not used by the course (D-07).

**Derived: the recall loss of post-filtering at a fixed k (this section's own derivation; toy arithmetic).**
- Let N chunks, of which a fraction s pass the filter (selectivity), and the retriever fetches k′ before filtering. If passing is independent of rank, the number of survivors is Binomial(k′, s) (hypergeometric for a finite corpus, same mean): **E[survivors] = s·k′**, **P(no survivor) = (1 − s)^k′**, and k survivors on average need **k′ ≈ k/s**.
- At k = 4: s = 0.05 and k′ = 20 (LangChain's default) give E = 1.0, P(0) = 0.36, P(≥ 4) = 0.016; k′ = 80 gives E = 4 but P(≥ 4) is still only 0.57; P(≥ 4) ≥ 0.95 needs k′ ≈ 153. At s = 0.10, k′ = 40: E = 4 (pgvector's example scaled), P(≥ 4) = 0.58.
- **Gold-level loss.** For a gold chunk inside the scope, let r be its rank in the unfiltered list and r_in its rank among in-scope chunks (r_in = r − the number of out-of-scope chunks above it). Pre-filter finds it in the top k iff r_in ≤ k. Post-filter finds it iff r_in ≤ k **and** r ≤ k′. So the loss is P(r_in ≤ k and r > k′): the gold was good enough within its scope but out-of-scope chunks pushed it past the fetch window. With k′ = N, post-filter equals pre-filter.
- **Correlation.** The s·k′ figure assumes independence. When the scope is what the question is about, in-scope chunks rank high and post-filtering does better than s·k′; when out-of-scope near-duplicates rank above the gold (D's "Paris Agreement" pair), it does worse. That is the case R2 exists for, and the case Weaviate and ACORN single out as hard [R2-S1, S2].

**Derived: when does a filter pay? (decision arithmetic; toy, not a result).** On scope-specified items let p_bad = filter-removed-gold rate, p_ok = rate at which the filter is correct, CE_none = CE@4 without a filter, CE_oracle = CE@4 with the oracle filter. Then ΔCE ≈ p_ok·(CE_oracle − CE_none) − p_bad·CE_none (abstentions and partial scopes ignored). A filter with a 10-point oracle gain and CE_none = 0.6 breaks even at p_bad ≈ p_ok × 0.17: one wrong filter in six correct ones cancels the gain. This is why 06 calls a filter error a hard failure, and why the oracle arm is reported first: if the oracle gain is small, no extractor can help.

**Current practice (2024–2026).**
- Engines pre-filter with an allow-list (inverted or payload index), traverse the graph with filter-aware rules (allow-list traversal, filterable HNSW extra edges, ACORN-style two-hop expansion), and switch to brute force over the allowed set when it is small [R2-S2, S3]. pgvector post-filters unless iterative scans are on [R2-S4].
- Multi-tenancy and other known, high-cardinality keys are handled by partitions or separate indexes, so the filter becomes index selection [R2-S4; AIQ 04 Q23].
- Access control is enforced in the retrieval filter, never by the model (AIQ 04 Q14).
- Filters come from the UI first (explicit scope pickers), then rules and alias tables, then LLM self-query extraction with schema-constrained output [R2-S7]. Time is split: hard filters for correctness (expired, superseded), soft recency boosts for preference (AIQ 04 Q34).
- **For exact search under about 1M vectors, filtering is trivial** (AIQ 04 Q8): scan the allowed subset. That is the course's case.

**Pitfalls, with evidence.**
- Post-filter starvation at a default `fetch_k` (LangChain FAISS 20 [R2-S6]; pgvector `ef_search` 40 [R2-S4]; P5 measured 9/35 short lists on D).
- The same keyword with opposite semantics across stores [R2-S6].
- A missing metadata field passing a negative test (`$neq`, [R2-S6]); dialect drift (`$neq` vs `$ne`, [R2-S6, S8]).
- Metadata built after the index, so the filter is not used by the graph [R2-S3]; heading-derived scopes that are wrong when heading detection is wrong (I2: 68% of D's headings are bold body-size lines).
- Chunks that span two scopes, tagged with only one (Corpus D measurement).
- LLM extraction that also rewrites the query (`use_original_query=False`), or that emits a filter for an unscoped question [R2-S7].
- Treating an emptied list as a correct abstention (external review L255).
- Hand-typed filters and an uncalibrated score threshold presented as a technique (upstream cells 16, 22, 24).

**How to evaluate.**
- **Primary:** CE@4 on scope-specified items (R2-E2), at fixed k = 4, against the previous champion and v0.
- **Diagnostics:** MRR@10; scope-precision@4; Precision@4 (as 06 asks); short-list rate (< k returned); empty-list rate.
- **Hard-failure guard:** filter-removed-gold rate on scope-specified items, with the list of qids.
- **Guards:** CE@4 on all items, and on unscoped items separately; the false-filter rate on unscoped items.
- **Arms:** no filter, rule, oracle (upper bound), plus a post-filter arm at the library default k′ = 20 to show starvation; optional LLM extraction in the LLMOps notebook.
- **Statistics:** M4's paired b/c and group bootstrap; the scoped subset is small, so "inconclusive" is expected.

**Interview questions.**
1. AIQ 04 Q23: pre- vs post-filtering and ANN.
2. AIQ 04 Q14: what metadata per chunk, and which fields are enforced in the filter.
3. AIQ 04 Q22 follow-up: a 5%-selectivity tenant filter changes the store choice how?
4. Derived: "Your filter is extracted by an LLM. How do you know it is not deleting the right answer?" (filter-removed-gold on a labelled set; the false-filter rate; fail-open fallback.)
5. AIQ 04 Q34: hard time filters vs a recency boost.

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).** A metadata filter restricts retrieval to chunks from the scope the question names, such as one paper, one chapter or one tenant, so that a near-identical passage from the wrong place cannot take a top-4 slot. Apply it before ranking (mask the excluded chunks, then take the top k) whenever you can: filtering after ranking keeps only the survivors of the top k′, and with a selectivity s you expect just s·k′ of them, so a 5% filter on LangChain's default 20 leaves about one chunk. The filter is only as good as its two inputs: metadata that is right at index time, and a scope that is read correctly from the question by the user, a rule or an LLM. A wrong filter is a hard failure, because no reranker can bring back a chunk the filter removed, so the experiment reports how often the filter removed the gold evidence next to the gain, and compares against an oracle filter that shows the most filtering could ever give. Use it when questions name scopes and your corpus has competing passages across those scopes; skip it when questions rarely name a scope or the metadata cannot be trusted.

**The theory in one read (11 ideas, each with its formula).**
1. *Scope metadata:* each chunk c carries a set of scope values `scopes(c)` (doc, chapter, section path, year); a chunk that spans two chapters carries both.
2. *Filter as a predicate:* `allowed(c) = f(scopes(c))`, e.g. `chapter ∈ {16}`; selectivity `s = |{c : allowed(c)}| / N`.
3. *Pre-filter:* `score'(c) = score(c)` if `allowed(c)` else −∞; top-k of `score'`. It returns `min(k, sN)` chunks and is exact with NumPy search.
4. *Post-filter:* top-k′ of `score`, keep the allowed ones, cut to k. `E[survivors] = s·k′`; `P(0) = (1 − s)^k′`; `k′ ≈ k/s` (independence assumed).
5. *Gold-level loss:* post-filter misses an in-scope gold iff `r_in ≤ k` and `r > k′`; `k′ = N` ⇒ post = pre.
6. *Correlation:* survivors exceed s·k′ when the scope matches the query's topic and fall below it when out-of-scope near-duplicates outrank the gold.
7. *Sources of the filter:* UI (exact, user-accountable) → rules + alias table (cheap, brittle to wording) → LLM extraction with an enum schema and `none` (flexible; costs one call; can hallucinate scopes).
8. *Filter errors:* `removed_gold(q) = 1` iff CE over **all** allowed chunks is 0 while CE over all chunks is 1 (the filter left no complete alternative for some evidence group). Rate = mean over scope-specified items. False filter = a filter emitted for an item with `scope_mention = none`.
9. *Oracle filter:* `scope*(q)` = the scopes overlapped by the gold spans (the union over OR alternatives); `removed_gold = 0` by construction, so CE_oracle is the filtering ceiling.
10. *When it pays:* `ΔCE ≈ p_ok·(CE_oracle − CE_none) − p_bad·CE_none`.
11. *Failure policy:* relevance filters fail open (no filter, or backfill, logged); access filters fail closed (D4). An empty list is an error, not an abstention.

**Formula sheet items:** s; the pre-filter mask; E = s·k′, P(0) = (1 − s)^k′, k′ ≈ k/s; the gold-loss condition; removed_gold via CE over the allowed set; false-filter rate; scope-precision@k = |{i ≤ k : scopes(c_i) ∩ scope*(q) ≠ ∅}| / k; ΔCE break-even; links back to CE@k and MRR (M2).

**Step-by-step outline (running example: Corpus D, chapter scope).** D is enough for the mechanism, the starvation arithmetic and the error accounting, because its 11 repeated headings give real cross-chapter near-duplicates. It cannot carry the decision: it is one document, its questions are written by us, and its scoped subset will be small. The decision runs on T (below).
1. **The failure.** D-002 ("In what year was the Paris Agreement adopted?", gold p.10, Ch6) and D-003 (NDC reviews, gold p.23, Ch16) are mirror images: each page is the other's distractor (06 §6.7). Show the top-4 for a chapter-scoped version of D-003, with p.10 chunks taking slots.
2. **Scope metadata.** Take I2's heading tree (1/21/68/192) and tag every v0 chunk with the chapters and section paths it overlaps. Count chunks that span two chapters and two sections. Print the 11 repeated titles with their full paths.
3. **Selectivity table.** Chunks per chapter (≈ 1–10 of ~97, so s ≈ 1–10%, approx.); the chapters of the Paris Agreement, smart grids and DAC pairs.
4. **Pre-filter by hand.** The mask, top-4, and the assertion that it returns `min(4, sN)` chunks.
5. **Post-filter and starvation.** Re-run P5 D.4's idea with chapter filters at k′ = 4, 20, 40, N. Plot the observed short-list rate against `1 − P(≥ 4)` from the binomial. Show the one item where the gold is lost at k′ = 20 but found by pre-filter (if one exists; otherwise say so).
6. **Where the filter comes from.** A rule extractor: regex for "Chapter N" plus an alias table built **from the chapter and section titles only**, frozen before scoring. Score it against `scope` labels: exact match, gold kept, false filters on unscoped items.
7. **The oracle.** Build `scope*` from gold spans; show D-004, whose OR alternatives sit in Ch5 and Ch15, so its oracle is the union.
8. **Measure (mechanism experiment, labelled "D: not a decision").** Arms: none, rule, oracle, post-filter at k′ = 20. CE@4 and MRR@10 on scoped items; CE@4 on all items; removed-gold list; short and empty lists. Same question text in every arm.
9. **What would change on T.** Doc-level scopes, an alias table from titles, and real cross-document near-duplicates; the same code with `doc_id` in place of `chapter`.
10. **Write the decision card:** gain, removed-gold rate, cost (0 calls for rules), "when NOT to use".

**What waits for Corpus T, and what T needs (proposed, not chosen; DEC-3).**
- **Waits for T:** the v2.2 adopt/reject decision, doc-level filters (`doc_id`, `year`, `version`), and the alias problem (papers named by nickname, first author or acronym).
- **T must have** (a proposal to add to 06 §5.1's criteria):
  1. at least two documents that share vocabulary and topics strongly enough that, **without a filter**, out-of-scope chunks outrank the gold on some items (otherwise the oracle gain is about 0 and R2 is untestable; 06 criterion 3 asks for overlap but not for this effect);
  2. reliable doc-level metadata recorded in the lock file: title, a short name and aliases, year, arXiv version;
  3. at least about 10 eval items that name a document explicitly (`scope_mention = explicit`), plus unscoped items about the same topics for the false-filter guard;
  4. optionally a doc with two versions or a "superseded" relation, to test time and version filters (AIQ 04 Q34).
- Check property 1 cheaply once T and its eval set exist: run the no-filter and oracle arms on dev; if CE_oracle − CE_none is about 0, record R2 as "not applicable to T" and do not build the extractors.

**Visuals that earn their place.**
- *Survivor curve* (SVG): expected survivors s·k′ and P(≥ 4) against k′ for s = 0.03, 0.05, 0.10, 0.20, with LangChain's 20 and pgvector's 40 marked. Shows why defaults starve selective filters.
- *Two-ranking strip* (SVG): one ranked list with chunks coloured in-scope / out-of-scope, the k′ window, and where the gold sits (r vs r_in). Shows the gold-loss condition at a glance.
- *Chapter ruler for pp.10 and 23* (SVG): the two "Paris Agreement" sub-headings with their different chapter paths, and v0 chunks with their scope tags. Shows why the path, not the title, is the scope.
- *Arms bar chart* (Plotly): CE@4 for none / rule / oracle / post-k′ = 20 on scoped items, with the removed-gold count printed on each bar. Shows gain and hard failures together.
- *Source-of-filter table* (UI / rules / LLM): cost, error type, fallback.

**Full only:**
- in-graph filtered ANN (allow-list traversal, Qdrant's extra edges, ACORN's expanded lists, Weaviate's flat-search cutoff) [R2-S1–S3];
- partitioning for multi-tenancy and pgvector's iterative scans [R2-S4];
- FAISS `IDSelector` [R2-S5];
- the hypergeometric vs binomial note;
- the correlation sweep;
- the soft-boost alternative (add a bonus to in-scope scores rather than masking);
- filter dialects and missing-field semantics;
- `SelfQueryRetriever` defaults [R2-S7];
- BM25 statistics on the full corpus vs the filtered subset.

### 7. Verify notebook plan

`study/notebooks/R2_metadata_filter_verify.ipynb`. Offline by default; NumPy, PyMuPDF 1.26.7, MiniLM, Plotly. No LLM call.
1. **Toy starvation.** Seeded simulation: N = 100, random scores, filters of selectivity s ∈ {0.03, 0.05, 0.10, 0.20}; for k′ ∈ {4, 10, 20, 40, 80, N} measure mean survivors and P(≥ 4); assert they match s·k′ and the binomial within simulation error, and that k′ = N gives exactly the pre-filter list.
2. **Correlation sweep.** Make in-scope scores higher or lower by a shift δ; show survivors above or below s·k′.
3. **Scope tags on D.** Rebuild I2's tree on the PyMuPDF snapshot (or import it from I2); tag v0 chunks with chapters and section paths by offset overlap; assert the counts 21/68 and the 11 repeated titles; print chunks spanning two chapters or two sections (replaces this session's poppler approximation).
4. **Selectivity table** per chapter; mark the chapters of the near-duplicate pairs.
5. **Pre vs post on D.** For every scoped item (and P5's 35 queries for comparison), run pre-filter and post-filter at k′ ∈ {4, 20, 40, N}: short-list rate, empty-list rate, gold lost by post but kept by pre (r_in ≤ 4 and r > k′).
6. **Library semantics replicated in NumPy** (no install): a function with FAISS's post-filter logic (L417/L450) and one with `InMemoryVectorStore`'s pre-filter logic; show they diverge on the same filter.
7. **Rule extractor accuracy** against the `scope` labels; removed-gold and false-filter rates; the oracle construction for D-004.
8. **Mechanism experiment** (once the scoped items exist): arms none / rule / oracle / post-k′ = 20; CE@4, MRR@10, scope-precision@4, Precision@4; paired b/c against "none". Label the result "D mechanism; not a decision".
9. **Optional replay:** the same with cached Cohere `embed-v4.0` vectors (no new calls; v0 vectors are reused).

Runtime about 1 minute on CPU (MiniLM over about 97 chunks plus the simulation). Network: none after the model cache.

### 8. Apply-it tool plan and real-world checklist

`study/tools/filter_fit_check.py`: "Should I filter on this metadata field, and how?"
- **Inputs:** `--chunks chunks.jsonl` (with metadata fields) or `--docs` plus `--scope-from headings|filename|field`; `--field chapter|doc_id|…`; `--questions q.jsonl` (`q`, optional `expect` span, optional `scope`); `--k 4`; `--fetch-k 20`; `--embedder minilm|cohere` (Cohere through the cache only); `--rules aliases.yaml`; `--report out.md`.
- **Outputs (Markdown + Plotly HTML):** value counts and selectivity per value; missing-value rate; chunks with several values; the survivor table at the given fetch_k; observed short lists pre vs post; rule-extractor accuracy if scopes are given; removed-gold and false-filter lists; checklist and recommendation.

**Real-world checklist (11 checks).**

| # | Check | Auto / manual |
|---|---|---|
| F1 | Every chunk has the field (missing rate 0), or the missing-value policy is written down | auto |
| F2 | Chunks with several values are tagged with all of them | auto |
| F3 | Metadata values come from a trusted source (outline, file names, lock file), and a 10-chunk sample is correct | auto (count) + manual (read the sample) |
| F4 | Selectivity per value is known; values with s·k′ < k at the planned fetch_k are listed | auto |
| F5 | The filter is applied before ranking, or k′ is large enough (k′ ≥ k/s for the smallest value) and short lists are counted | auto |
| F6 | The same filter is applied to every retriever leg (dense, BM25) and to the rerank pool | auto (config) + manual |
| F7 | The alias table or rules were written from metadata, not from the eval questions, and frozen before scoring | manual |
| F8 | Removed-gold rate on scoped items is reported, with qids | auto |
| F9 | False-filter rate on unscoped items is reported | auto |
| F10 | Oracle gain (CE_oracle − CE_none) is above the noise; otherwise the field is not worth filtering on | auto |
| F11 | Fallback policy for empty or short lists is set (relevance: fail open and log; access: fail closed) | manual |

**Recommendation logic.**
- F1–F3 fail → "fix the metadata first; a filter on bad metadata deletes evidence".
- F10 shows no oracle gain → "do not filter on this field; questions do not need it".
- F4 shows small values and F5 fails → "pre-filter (or partition); post-filtering at this fetch_k will starve".
- F8 > 0 → "keep the filter only as a soft boost, or fix the extractor; every removed gold is a guaranteed miss".
- F9 high → "the extractor over-filters: require an explicit scope mention or user confirmation".
- Otherwise → "adopt the pre-filter; confirm once on held-out questions".

### 9. LLMOps notebook plan

`study/llmops/notebooks/R2_metadata_filter_ops.ipynb`: the filter as a traced, versioned retrieval stage with an optional LLM extractor (foundation §12 row "5 · R1–R5").

- **Framework build (after the mechanism):**
  - `langchain-core` `InMemoryVectorStore` filled through `CachedEmbeddings`, searched with `filter=callable` → the exact **pre-filter** (mechanism step 3). Our NumPy retriever runs beside it; assert identical ids.
  - A read-only cell shows LangChain FAISS's `filter` + `fetch_k = 20` (L392/L417/L450) and reproduces its short lists with the NumPy replica from the verify notebook (no `langchain-community` install). Defaults to name: `fetch_k = 20`, no warning when short, MMR fetches `2·fetch_k`, `$neq` passes a missing field.
  - **LLM extractor (optional arm):** `CachedChatModel` (LLMOPS §9.3) with native `json_schema`, `strict: true`, on Groq `openai/gpt-oss-20b` (`reasoning_effort=low`). Schema: `{"scope_type": enum["chapter","none"] (T: "doc"), "values": array of enum[allowed ids]}`, all properties required, `additionalProperties: false`. The prompt lists the allowed values with titles from the metadata only (never eval questions). Maps to mechanism idea 7.
  - Read-only: `SelfQueryRetriever` and the query constructor. Named defaults: `use_original_query=False` (it rewrites the query too), `fix_invalid=False` (raises), `"NO_FILTER"`, no FAISS/InMemory translator, needs `lark`. Not used, because it changes two variables and does not support our store.
  - No LangGraph: the flow is linear (extract → mask → retrieve). A fallback branch (no filter when the extractor says `none` or fails) is a plain `if`.
- **External calls (all through the cache; replay runs with no key):**

  | Call | Count | Cost / quota |
  |---|---|---|
  | Cohere `embed-v4.0` documents | 0 new (v0 or champion vectors are cache hits) | — |
  | Cohere `embed-v4.0` queries | ≤ 1 batched call for new scoped items (≤ 96 per call) | trial cap fine |
  | Rule and oracle arms | 0 LLM calls | $0 |
  | Groq `openai/gpt-oss-20b` extraction | one per eval item, scoped **and** unscoped (needed for the false-filter rate): D ≈ 30–60, T ≈ 60–100 → **≤ 160 calls** in all | ≈ 600 input + ≈ 300 output (incl. reasoning) tokens each (assumed) → 160 × (600 × 0.075 + 300 × 0.30)/10⁶ ≈ **$0.02**; ≈ 144K tokens ≈ 72% of one day's 200K TPD and ≥ 18 min at 8K TPM (plan UNVERIFIED) |
  | Claude Haiku 5.5 (optional comparison, credits only) | same items, ≤ 160 | 160 × (600 × 0.10 + 300 × 0.50)/10⁶ ≈ $0.03; a model-family arm, never a silent swap |
  | Generation for the chosen arm | v2.1 champion answers are cached; the filtered arm on dev ≈ 16–20 Groq calls | ≈ $0.005 |
  | Judge | 0 (D-10) | — |

- **Tracing (JSONL default; Phoenix local; LangSmith only for Corpus D under `privacy.assert_corpus_is("D")`):**
  - a `filter` span: `filter_source` (none / rule / llm / oracle), canonical filter JSON, `rules_version` or `prompt_version` + `cache_key`, extraction parse status (ok / none / invalid), `allowed_count`, selectivity, `on_short` policy taken;
  - per retriever leg: ranked ids and scores **before** and **after** the mask (ids only for non-D corpora), `n_returned`, `short_list`, `empty`;
  - eval-only fields: gold scope, `removed_gold`, `false_filter`.
- **Dataset and evaluators:**
  - the golden set with the new `scope` and `scope_mention` fields (new dataset version, R2-E3); D scoped items as a separate D slice;
  - code evaluators: `filter_exact_match`, `filter_keeps_gold` (hard), `false_filter`, `scope_precision@4`, CE@4, MRR@10, Precision@4, short/empty-list flags (foundation §5 tier 1);
  - no judge (D-10); about 10 answers read by Yash for the chosen arm.
- **Experiment against the previous version:** v2.2 arms (none = the v2.1 champion, rule, oracle, optional LLM) on T dev, paired against the champion and v0 (06 §4.1); D results reported as a separate mechanism table; one test touch for the chosen arm.
- **Cost, latency, tokens:** filter latency (mask: microseconds; LLM extraction adds one call on the critical path, report p50/p95 excluding cache hits); extraction tokens and "cost if called"; filtered vs unfiltered context tokens.
- **Prompt and config versioning:** `prompts/filter_extract_v1.txt`; `filters/aliases_v1.yaml` (built from metadata, frozen with a hash); config block `retrieval.filter: {source, fields, mode: pre, any_overlap: true, on_short: fail_open_log | backfill | abstain, apply_to: [dense, bm25, rerank_pool]}` hashed into `config_hash`; the index manifest records `metadata_version` and I2's `heading_rules_version`, so a metadata change forces a rebuild (C3 rule).
- **Monitoring and feedback (`ci-cd-evals`, `error-analysis`):**
  - T1 tests: pre-filter returns `min(k, |allowed|)`; post-filter with k′ = N equals pre-filter; on a frozen fixture the rule filter **never removes gold** (removed_gold = 0); a chunk missing the field follows the written policy; dense and BM25 legs receive the same mask.
  - Replay test for the LLM arm (`replay` marker).
  - Monitor: removed-gold rate (alert on any > 0 on the golden set), empty-list rate, extractor invalid/none rates, distribution of extracted scopes, unknown scope values (a document not in the index).
  - Feedback: every removed-gold or false-filter case → M5 log (bucket "wrong scope") → a new golden item and a fixture.
- **Place in the lifecycle:** Analyze: "wrong-scope" traces from v0.1/v2.1 (`error-analysis`, `trace-data-analysis`). Measure: arms with code evaluators (`rag-evaluation`, `code-based-evaluators`). Improve: adopt or skip the filter (`improving-llm-agents` for the cost of the LLM call). dev → CI: the T1 tests (`ci-cd-evals`). Tracing: `llm-observability`. Framing: `evals-foundations`. Lesson: `visual-learning-writer`.

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version (pin ≥ 2 weeks old) | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Mask, simulation, metrics | `numpy` + own code (M2 metrics, M4 statistics) | 2.5.3 | yes | yes | — | BSD-3 | yes |
| Rule extractor | Python `re` + an alias YAML | stdlib | yes | yes | 0 calls | — | yes |
| Scope metadata | I2 heading tree via `pymupdf` | 1.26.7 (pin) | yes (project) | yes | — | AGPL-3.0 / commercial | yes |
| Local embedder | `all-MiniLM-L6-v2` via `sentence-transformers` | 6.1.0 | yes | yes | — | Apache-2.0 | yes (D-03 fallback) |
| Default embedder | Cohere `embed-v4.0` via `CachedEmbeddings` | `cohere` 7.2.0 | yes | replay only | ≤ 1 query call; documents cached | MIT (SDK) | yes (D-03) |
| LLM filter extraction (optional) | Groq `openai/gpt-oss-20b`, `json_schema` strict, `reasoning_effort=low` | from `.env` | SDK yes | replay only | ≤ 160 calls ≈ $0.02 | — | yes (D-04); strict support verified only in langchain-groq source |
| LLM extraction, Claude arm (optional) | Claude Haiku 5.5 `claude-haiku-5-5`, effort `low`, structured outputs | — | no (`anthropic` 1.11.0 when credits) | replay only | ≤ 160 calls ≈ $0.03 | MIT (SDK) | yes (D-32), only as a labelled arm; high-volume tier per LLMOPS §6.4 |
| Framework core | `langchain-core` (`InMemoryVectorStore`, `BaseChatModel` adapters) | 1.6.6 | no | yes | — | MIT | yes (LLMOps only) |
| LangGraph | not needed (linear flow) | — | — | — | — | MIT | n/a |
| Provider integrations | `langchain-groq` 1.1.3 / `langchain-cohere` **not installed** (pin conflicts) | — | no | — | — | MIT | adapters instead (LLMOPS §9.3) |
| Reading only | `langchain-community` FAISS (`fetch_k` post-filter) | 0.4.2 | no | — | — | MIT | read the source; do not install |
| Reading only | `langchain-classic` `SelfQueryRetriever` (+ `lark` 1.3.1) | 1.0.8 | no | — | — | MIT | read only; no translator for our store |
| Reading only | `faiss-cpu` `IDSelector` | 1.15.1 | no | — | — | MIT | not needed (D-07 exact search) |
| Reading only | Chroma `where` (`chromadb-client`) | 1.5.9 | no | — | — | Apache-2.0 | not used (D-07) |
| Reading only | Qdrant / Weaviate / pgvector docs; ACORN repo | — | — | — | — | — | docs only; servers not run |
| Hosted tracing | `langsmith` | 0.14.4 | no | no | free plan | MIT (SDK) | Corpus D only |
| Local tracing | `arize-phoenix-otel` 0.17.2 + `uvx arize-phoenix@20.19.0 serve` | — | no | yes | — | Apache-2.0 / ELv2 | yes |
| Tests | `pytest` | 9.1.1 | yes (dev) | yes | — | MIT | yes |

**Install lines (do not run):** `uv add --group llmops langchain-core==1.6.6 langsmith==0.14.4 arize-phoenix-otel==0.17.2` (foundation pins); `uv add --group llmops anthropic==1.11.0` only when Claude credits exist. Nothing new for the lesson or the verify notebook. Nothing heavy; no server is needed.

**Keys:** `GROQ_API_KEY` (present) to record the extraction arm once; `COHERE_API_KEY` (present) for one query batch; `ANTHROPIC_API_KEY` only for the optional Haiku arm; `LANGSMITH_API_KEY` only if the hosted view is wanted. After recording, no keys.

### 11. Open questions for Yash (preferences only)

1. For the D mechanism demo, write about 10–16 chapter-scoped questions from the 11 repeated-heading pairs (a new D dataset version), or use only the existing seeds plus P5's 35 queries? **write** / seeds only (recommended: write; without them the rule and oracle arms have nothing to score).
2. Include the optional LLM extraction arm in the LLMOps notebook (Groq, ≤ 160 cached calls)? **yes** / no.
3. Show in-graph filtered ANN (ACORN, Qdrant, Weaviate) as a Full-only reading box, or leave it to the interview item only? **box** / interview only.

---

## Concept R3: Reranking (E, project v2.1)

R3 adds a second ranking stage. A cheap first stage (the v2.0 champion: dense, or hybrid with RRF) fetches a pool of N candidates; a more expensive model reads the question and each candidate **together**, rescores them, and the top k = 4 go to the prompt. The mechanism itself is small: P4 D.7 already shows one cross-encoder pass on two seed questions. What is new in R3 is everything around it:
- the pool sets a hard ceiling (CE@pool), and on Corpus D the headroom may be close to zero;
- cost grows with N, so pool size is a latency decision measured as p95 on a CPU;
- the score's scale is model-specific (raw logit, sigmoid or Cohere's [0, 1]), and none of them is a probability;
- LLM rerankers come in three shapes (pointwise, listwise, pairwise) with very different call counts, ties and position bias;
- a reranker reorders while a grader (V2) filters, and the two are easy to confuse.

No R3 course files exist yet (no `concepts/R3_*`, `study/reading/R3_*`, `study/questions/R3_*`, `labs/R3_*` or `sources/verification/R3/`; checked 2026-10-17). The tracker says R3 `not_started`. O1-Q10 scored 0: Yash could not explain bi- vs cross-encoders, although VAI L22 covered reranking.

### 1. Sources checked

**Book (not present; per 02/04/08, not re-opened, UNVERIFIED):**
- Ch13 p.5/13: retrieve a broad candidate set of about 10–30 (02 card; 04 step 1 cites p.5/13 **and** p.9/13; 08 Q1 cites p.9–10/13 for K = 10–30, N = 3–5). The three files disagree (R3-E2).
- Ch13 p.6–7/13: bi- vs cross-encoder, with a speed-vs-accuracy diagram (02, 04, P4 lesson book table).
- Ch13 p.7–9/13: LLM reranking, scoring each candidate 1–10; sketch p.9/13 (04 step 2).
- Ch13 p.9–10/13: the cross-encoder reranker; sketch p.10/13. P4's book table records that the book calls such rerankers small trained scorers that cannot take custom criteria.
- Ch13 p.10–11/13: reorder and keep the shortlist (04 step 5).
- Ch13 p.12–13/13: reranking contrasted with Ch3's relevance grading (04 errata: it starts on p.12, not p.11).
- 08 Q1 row: the book does not separate pointwise from listwise LLM reranking, and names no model.

**Repo (verified: downloaded at `009adba` into the scratchpad, cells read 0-based with `python3 -I`; code not run; custom non-commercial licence, described not quoted):**
- `all_rag_techniques/reranking.ipynb`:
  - cell 6: imports, including legacy `langchain.docstore.document` and `langchain.chains.RetrievalQA`. `BaseModel`, `Field` and `PromptTemplate` arrive through `from helper_functions import *` (`helper_functions.py` L5–L6).
  - cell 11: `encode_pdf` (pypdf per page, 1000/200 characters, OpenAI embeddings, FAISS L2).
  - cell 15: `RatingScore(relevance_score: float)`, a 1–10 prompt, `gpt-4o` at temperature 0 with `max_tokens=4000`, one sequential `with_structured_output` call per document, `sorted(..., reverse=True)`, `top_n=3`.
  - cell 17: k = 15, then rerank; prints only. No saved output.
  - cell 19: `CustomRetriever.get_relevant_documents(query, num_docs=2)`: k = 30, rerank, keep 2.
  - cell 23: the 5-sentence "capital of France" toy. Its saved output comes from the **LLM** reranker (cell 19's class), not the cross-encoder.
  - cell 27: `CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')`, `[query, doc]` pairs, `predict`, sort descending. Class defaults are k = 5 → 3.
  - cell 29: k = 10 → `rerank_top_k=5`, RetrievalQA. No saved output.
- `all_rag_techniques_runnable_scripts/reranking.py` (173 lines): LLM scorer L26–L53, `CustomRetriever` L56–L64, `CrossEncoderRetriever` L67–L84, toy L87–L107, `RAGPipeline` L110–L143 (CrossEncoder at L119).
- `all_rag_techniques/reranking_with_llamaindex.ipynb`:
  - cell 5: `gpt-3.5-turbo`, `text-embedding-3-small` at 512 dimensions;
  - cell 12: `SentenceSplitter()` defaults (1,024 tokens);
  - cell 16: `similarity_top_k=10`, `LLMRerank(top_n=5)`;
  - cell 19: the same toy with `LLMRerank(top_n=2)`; it has a saved output;
  - cell 23: `SentenceTransformerRerank(model='cross-encoder/ms-marco-MiniLM-L-6-v2', top_n=5)`.

**Upstream bugs and traps found (static reading; runtime UNVERIFIED):**

| # | Where | Problem |
|---|---|---|
| U1 | `reranking.ipynb` cell 15; script L45–L49 | The `try: float(score) except ValueError: score = 0` is dead code. `relevance_score` is already a float. A malformed reply fails **inside** `invoke` (structured-output validation), so one bad reply aborts the whole rerank instead of scoring 0 |
| U2 | same | No 1–10 range check (`Field` has no `ge`/`le`). With 15 or 30 candidates on a 10-level scale, ties are certain (§6 idea 7). Python's stable sort then silently breaks ties by FAISS order, an undocumented tie rule |
| U3 | same | A new `ChatOpenAI` is built per call; N sequential calls per query; `max_tokens=4000` for a one-number answer |
| U4 | cells 19, 27; script L62, L76 | The classes override `get_relevant_documents`. In `langchain-core` 1.6.6 `_get_relevant_documents` is abstract (`retrievers.py` L297–L298) and the public method no longer exists, so these classes cannot be instantiated. `num_docs=2` is unreachable through `RetrievalQA` (which now lives in `langchain-classic`) |
| U5 | cell 27; script L67–L84 | No `revision` pin, no `max_length`, scores thrown away (only documents returned), so no trace can show the rank change. Class defaults (5 → 3) differ from the call in cell 29 (10 → 5) |
| U6 | cell 23 | k = 30 on a 5-document store. No sentence states the answer ("Paris is the capital"), so the toy tests a judgement call, not fact retrieval. The output is one LLM run with no metric |
| U7 | whole notebook | No retrieval metric anywhere. The PDF cases (cells 17, 21, 29) have no saved output (08 Q8 rows 22–23) |
| U8 | `reranking_with_llamaindex.ipynb` cell 19 | `Document(page_content=...)` is LangChain's field name, not LlamaIndex's (`text`). The function ignores its `docs` argument and rebuilds documents from the global `chunks` |
| U9 | LlamaIndex `LLMRerank` (cells 16, 19; library 0.14.25) | Batched **pointwise** scoring, 10 documents per prompt (`choice_batch_size=10`). The prompt asks for 1–10 scores **and** tells the model to leave out irrelevant documents, so it also filters and can return fewer than `top_n`. The parser (`indices/utils.py` L120–L167) silently skips malformed lines. If a line's document number parses but its score does not, the score list falls out of step with the document list. "Doc: 0" becomes index −1, the **last** document. The default is `top_n=10` |
| U10 | LlamaIndex `SentenceTransformerRerank` (cell 23) | Defaults: `model="cross-encoder/stsb-distilroberta-base"` (a **similarity** model, not a relevance model; the cell overrides it), `top_n=2`, `trust_remote_code=True`, `keep_retrieval_score=False` (the first-stage score is overwritten). The cross-encoder reads `get_content(MetadataMode.EMBED)`, i.e. the text **plus** any metadata not excluded. Which keys survive is UNVERIFIED |

**Existing course files:**
- 02 R3 card (L689–L701) and its gates;
- 03 §2.1 R3 rows (L436, L479) and §3.5 row L533;
- 04 matrix row L176, Ch13 detail L614–L640, DV-29 L1018, errata L65 and L69;
- 06 config L280, `Reranker` protocol L210–L212, trace `reranked` L359–L361, §3.2 L425, v2.1 card L597–L606, §6.2 categories, §6.3 rule 6, §7.5, the Phase 5 row L1444;
- 08 Q1/Q2/Q7/Q8 rows, D-03, D-11 ("Cohere rerank stays an optional comparison only"), D-20 (CPU torch), D-32, A-04;
- P4 lesson D.7 and P4_FACTS S1, S8 (cross-encoder `max_seq_length` 512, activation `Identity`, revision `233902d2…`, logits −10.97 to 5.17, CE(q, d) ≠ CE(d, q));
- C4_FACTS S4–S6 (first relevant rank per seed; CE@4 = 8/8 already on 8 seeds);
- 07 D.6 (v0 chunks are at most 182 WordPiece tokens);
- VAI L22 and L23 notes (`sources/vai/L19-L23_core_rag.md` L232–L337);
- external review items L256–L259 and L307, plus open items 25 and 26 (L403–L404);
- `LLMOPS_FOUNDATION.md` §2, §3.3, §6.2, §9, §11, §12;
- `phase_03_measurement.md` M2 (CE@pool, checklist C6), M4, M5 (the "rank" bucket = CE@pool 1 ∧ CE@4 0);
- tracker: R3, P4, M4 `not_started`; M2, M5, R1 `exposed`;
- misconception log: MC-002, MC-005 and MC-006 (uncalibrated LLM scores), which R3 touches.

**AE book:** not present. As summarised in the external review: AE Ch7 'Overview' (two-stage evaluation, recall for the pool and rank metrics after). The review's ★item L256 carries this.

**Interview repo (AIQ @ `e080df2`, MIT, "Copyright (c) 2026 Om"; verified):** 04 Q10 (L243–L267, what a reranker is), Q25 (L609–L625, bi / late interaction / cross), Q43 (follow-up: recall@100 95% vs recall@5 60%), Q46 (L1206, compare pre- and post-rerank positions), Q48 (L1263, rerank of about 100 documents at 50–300 ms), Q58 (L1552–L1577, pointwise / pairwise / listwise LLM reranking).

**External:** [R3-S1] … [R3-S16], listed in "R3 sources" below. Hugging Face, arXiv, sbert.net and docs.cohere.com were blocked (DNS). GitHub raw and PyPI wheels were reachable, so library behaviour is from source and model numbers are from the sentence-transformers repo docs.

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Bi- vs cross-encoder: what is precomputed; one pass per pair | 02 outcome 1; Ch13 p.6–7/13 | P4 D.7 (written, **not studied**; O1-Q10 = 0) | P4 | no | bridge | Five-line recap with P4 S8's D-002 example (gold rank 2 → 1). R3's `all{P4}` gate is open; flag it (cross-concept note) |
| 2 | Two-stage retrieve-then-rerank; the pool comes from the **champion** (v2.0 hybrid if adopted) | 06 v2.1; 03 L479 | 06 only | R3 | no | core | Funnel diagram with Corpus D counts: 97 chunks → N → 4 |
| 3 | Cost: N cross-encoder passes vs 1 query embedding; full corpus = 97 passes | 06 v2.1 Cost; VAI L22 | P4 D.7 (counts only) | R3 | no | core | Formula plus a derived FLOP estimate (§6 idea 3), then a **measured** p95 per N |
| 4 | **Pool-sufficiency ceiling**: Hit@k after rerank ≤ Hit@N; CE@4 after rerank ≤ CE@pool | 06 v2.1 "Ceiling"; M2 #11 | M2 (planned, Full only) | M2 → R3 | M2 exposed | core | Teach as an inequality, then check it on every item (a T1 assert) |
| 5 | **Headroom** = oracle reranker − champion, measured before running any reranker | not in any file | **missing** | R3 | no | core | Oracle = perfect reordering of the pool. If headroom ≈ 0 (C4 seeds: CE@4 already 8/8), say "inconclusive by construction" before spending calls |
| 6 | Pool-size trade-off: CE@pool rises with N; latency ≈ a + b·N; more hard negatives to promote | 02 outcome 2; 06 sweep | **missing** | R3 | no | core | Two-panel chart: CE@pool / oracle / reranked MRR against N, and p95 against N |
| 7 | Corpus scale: on D, N = 50 is 52% of 97 chunks; the latency is not production-like | 06 v2.1 | **missing** | R3 | no | core | One line, and a "pool = all 97" diagnostic arm. Latency conclusions carry over only per pair, not per corpus |
| 8 | Truncation at 512 tokens, `longest_first` (the passage tail is cut, the query kept) | 04 "Build yourself"; VAI L22 | P4 S1 (512 only) | R3 | no | core | Pair length = \|q\| + \|d\| + 3. v0 maximum 182 WordPiece tokens → 0 truncated (derived; same vocabulary assumed). Count it per chunker arm |
| 9 | Score scale: raw logit vs sigmoid vs Cohere [0, 1]; **not a probability**; not comparable across queries or models | 03 L533; VAI L22 | P4 D.7 ("raw logit") | R3 | no | core | Logit vs sigmoid strip: same order, different "improvement %". The ST 6.1.0 default is sigmoid when the model config sets nothing, so the scale depends on the model |
| 10 | Ties under discrete LLM scores; the tie rule hands control back to stage 1 | 02 outcome 3; 03 L533 | **missing** | R3 | no | core | If N > L levels, a tie is certain. Make the first-stage rank an explicit second key |
| 11 | LLM reranking: pointwise / listwise / pairwise; calls per query; parsing failures | 02 outcome 3; DV-29; review L259 | **missing** (DV-29 says only "distinction lost") | R3 | no | core | Classify the repo's three LLM rerankers (cell 15 pointwise; `LLMRerank` batched pointwise with a filter; RankGPT listwise). Call-count formulas |
| 12 | Position bias in listwise reranking; window direction | AIQ Q58; review L259, L443 | **missing** | R3 | no | core (Full) | Forward vs reversed input; Kendall τ. RankGPT slides **back to front** [R3-S5] |
| 13 | Calibration of LLM scores (MC-006) | 02 outcome 3 | M3 / V2 (later) | M3 | no (MC-006 open) | bridge | One box: a 1–10 or 0–3 score only orders; any threshold needs labels (06 §8.4) |
| 14 | Reranking vs relevance grading: reorder-and-cut (always k) vs keep-if-above-θ (0…N) | Ch13 p.12–13/13; 03 L485, L557 | **missing** | R3 / V2 | no | core | Comparison table. "A reranker with a threshold is a grader", so V2 inherits R3's calibration warning |
| 15 | Domain shift from MS MARCO (Bing queries, short web passages) | 06 "When NOT" | **missing** | R3 | no | core | Report the model's MS MARCO numbers [R3-S2], then say clearly that they are not our numbers |
| 16 | Multi-span risk: the cross-encoder scores chunks independently and may demote a partial-evidence chunk | 06 guards (CE@4) | **missing** | R3 | no | core | Why CE@4 is a guard; count "gold demotions" (pre-rank ≤ 4 → post-rank > 4) |
| 17 | Input order (q, d) matters | P4 S8 | P4 D.7 | P4 | no | bridge | One line; a T1 test that pairs are built as (query, passage) |
| 18 | MRR@10 as primary; Hit@4 and CE@4 as guards; paired per-item comparison | 06 v2.1 | M2, M4 (planned) | M2 / M4 | M2 exposed | bridge | Link. Define MRR@10 on the **reranked** list explicitly |
| 19 | Multiple arms (3 pool sizes + LLM + Cohere) on about 16 dev items | 06 §9.4 | M4 (planned) | M4 | no | bridge | Pre-register pool 20 as the primary arm, the rest secondary with Holm; ties go to the smaller pool |
| 20 | Latency measurement: warm model, fixed threads, model load excluded, the percentile method named, n large enough for p95 | 06 §7.5 | 06 §7.5 toy | D2 / M4 | no | core | Repeat each item 5× (≈80 timings on dev); report the load time separately |
| 21 | Hosted rerank (Cohere): per-search billing, `max_tokens_per_doc` default 4,096 (truncation), `top_n`, scores in [0, 1] and non-linear | 06 v2.1 Cost; D-11 | **missing** | R3 | no | core (Full) | Optional arm; one call per query at the largest pool |
| 22 | Pointwise independence lets one scoring of the largest pool serve every smaller pool | not in any file | **missing** | R3 | no | core | True by construction for a cross-encoder (up to float noise from batch padding); test it for Cohere (UNVERIFIED) |
| 23 | Late interaction (ColBERT, MaxSim) as the middle point | review L258; AIQ Q25 | **missing** | R3 | no | next / Full | Sidebar only (C#35) |
| 24 | Distilling an LLM reranker into a cross-encoder; fine-tuning the reranker | AIQ Q58 | — | — | no | next | One line; not in scope |
| 25 | MMR after reranking: which relevance score feeds MMR | review item 26 | — | R4 | no | next | Link to R4 / v2.3 |
| 26 | Ordering inside the prompt (lost in the middle) ≠ rerank order | 03 L550 | — | X3 | no | next | Link |

### 3. Quiz coverage

No question file exists. Needed titles:
- **R-01** Why can a bi-encoder search all 97 chunks with one model pass per query, while a cross-encoder needs one pass per candidate? (Closes O1-Q10.)
- **R-02** What do you measure on the candidate pool, and what on the reranked top-k? (Review ★item L256: CE@pool is the ceiling; MRR@10 with Hit@4 and CE@4 as guards.)
- **R-03** The cross-encoder returns −4.29 for one chunk. Is it "irrelevant"? What changes if you apply a sigmoid?
- **R-04** Reranking vs relevance grading: what does each return when no candidate is relevant?
- **R-05** Name the three LLM reranking formulations and their calls per query for N = 20.
- **A-01** Given first-stage ranks of gold for 8 items and N ∈ {10, 20, 50}, compute Hit@4, Hit@N, CE@pool and oracle Hit@4. Where is there headroom?
- **A-02** Given cross-encoder logits for 10 candidates, rerank, compute RR before and after, and list the gold demotions.
- **A-03** An LLM gives 1–10 scores to 20 candidates: how many ties are guaranteed at minimum? With first-stage order (c1…c20), apply the tie rule.
- **A-04** RankGPT with window 20 and step 10: how many calls for N = 50, 100 and **10**? (★ For 10, the original `sliding_windows` makes 0 calls and returns the input order.)
- **A-05** Cost per query for pointwise vs listwise at N = 20 on Groq gpt-oss-20b, using the §5 token assumptions.
- **T-01** Hit@4 = Hit@20 on your dev set. Your colleague wants to add a reranker. What do you say, and what would you measure first?
- **T-02** A chunker change doubles chunk length to about 450 WordPiece tokens. What happens inside the cross-encoder, and how do you detect it?
- **T-03** You want to use the top reranker score as an abstention threshold. What data do you need, and why can a threshold set on ms-marco logits not be reused for Cohere scores?
- **Interview (AIQ 04 Q58, MIT):** "Teams increasingly rerank with an LLM rather than a cross-encoder. How do pointwise, pairwise and listwise LLM reranking work, and when is the cost justified?" Second choice: AIQ 04 Q10.

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| R3-E1 | 02 R3 outcome "10/20/30" vs 06 v2.1 sweep `{10, 20, 50}` | The two files disagree (external review item 25, still open) | Pre-register `{10, 20, 50}` plus a "pool = whole corpus" diagnostic. Say that on Corpus D, N = 50 is 52% of 97 chunks |
| R3-E2 | 02 R3 Book (p.5/13 for 10–30) vs 04 step 1 (p.5/13 and p.9/13) vs 08 Q1 (p.9–10/13 for K = 10–30, N = 3–5) | Three different page cites for the same claim | Settle in the local book pass (book not present here) |
| R3-E3 | 04 DV-29 and L69 ("`LLMRerank` batching … UNVERIFIED"); 08 Q7 "LLM batch `LLMRerank`" | Now verified in `llama-index-core` 0.14.25: `choice_batch_size=10`, `top_n=10`, a 1–10 score per document **plus** an instruction to leave out irrelevant ones. That is batched pointwise scoring with a filter, not listwise ranking. The parser has the defects in U9 | Rewrite DV-29: "batched pointwise 1–10 with filtering; can return fewer than top_n". Remove UNVERIFIED |
| R3-E4 | 04 Ch13 table: `rs/reranking.py:L26-L54`, `L56-L65` | The functions end at L53 and L64 | Cite L26–L53 and L56–L64 (cosmetic) |
| R3-E5 | 02 R3 Repo line: `reranking_with_llamaindex.ipynb` cells 16, 23 | It omits cell 19, the only cell with a saved before/after output (08 Q8 row 23 cites it). It does not say that `reranking.ipynb` cell 23's saved output is from the **LLM** reranker | Add cell 19 and the note |
| R3-E6 | 06 §2.4 `rerank: {name, model_id, pool: 20}`; §2.5 `reranked` entries `{rank, chunk_id, score, prev_rank}` | Missing: model `revision`, `max_length`, score kind / activation, `batch_size`, `top_n` (k), tie rule, device and threads. The trace lacks `pool_size`, `prev_score`, `score_kind`, `truncated`, `model_id`, and the reranker latency is not split into load and score | Add these fields. `score_kind ∈ {logit, sigmoid, cohere_relevance, llm_grade}` |
| R3-E7 | 06 §3.2 row: cross-encoder "effective max length used by `CrossEncoder` UNVERIFIED" | Measured as 512 in P4_FACTS S1. ST 6.1.0 source caps `model_max_length` at `max_position_embeddings` and truncates pairs `longest_first` [R3-S3] | Replace with "512 (P4 S1; ST 6.1.0 source); passage tail cut first" |
| R3-E8 | 06 v2.1 Hypothesis "raises MRR and Hit@4" vs Experiment "guards Hit@4" | Inconsistent. On the C4 seeds, MiniLM top-4 already has CE@4 = Hit@4 = 8/8 (C4 S6), so Hit@4 can only fall there | Hypothesis on MRR@10 only; Hit@4 and CE@4 as non-inferiority guards. Add a pre-run **headroom** check (oracle − champion) |
| R3-E9 | `LLMOPS_FOUNDATION.md` §6.2 Cohere rerank "(32k context)" | The cohere 7.2.0 v2 `rerank` docstring says long documents are truncated at `max_tokens_per_doc`, **default 4,096**. Chunking (`max_chunks_per_doc`) belongs to the v1 endpoint. A third-party page says documents over 500 tokens are split and billed as extra documents (UNVERIFIED) | Send `max_tokens_per_doc` explicitly and put it in the cache key; record `meta.billed_units.search_units` per call |
| R3-E10 | `LLMOPS_FOUNDATION.md` §9.2 defaults table | Reranker defaults are missing: `CrossEncoderReranker.top_n=3` (and it drops scores); `HuggingFaceCrossEncoder` default model `BAAI/bge-reranker-base`; classic `CohereRerank` is deprecated with default `rerank-english-v2.0`; `langchain-cohere` `CohereRerank.top_n=3` (model required); LlamaIndex `SentenceTransformerRerank` defaults (U10) | Add rows (§5 table below) |
| R3-E11 | `LLMOPS_FOUNDATION.md` §11 `langchain-classic` "read-only; not installed" | `ContextualCompressionRetriever`, `CrossEncoderReranker` and `LLMListwiseRerank` now live only in `langchain-classic` 1.0.8 | A decision: install it for the R3 LLMOps notebook (light; no community deps), or write about 25 lines on `langchain-core` (§9) |

### 5. What the research says

**[R3-S1] Nogueira & Cho 2019, "Passage Re-ranking with BERT"** (arXiv 1901.04085; paper search-checked only; the authors' repo README verified).
- *The study:* BERT, fine-tuned as a binary relevant / not-relevant classifier on (query, passage) pairs, reranks the **BM25 top-1,000** for each MS MARCO query (the README's `top1000.dev` files, about 6,980 dev queries × 1,000 documents). TREC-CAR is the second task.
- *The result:* in the README's table (leaderboard of 8 Jan 2019), BERT-large reaches **Dev MRR@10 36.53 / Eval 35.87**, against 27.80 / 28.06 for the second-placed system. BERT-base gives about 34.7. Search summaries report the gain as 27% relative MRR@10 over the previous state of the art. On TREC-CAR: MAP 33.5 vs BM25 15.6.
- *Limits:* in-domain (trained and tested on MS MARCO); a pool of 1,000 on TPUs; a 3.4 GB model; no latency budget. The truncation details (query cap, 512 total) are UNVERIFIED here.
- *For the project:* this is the design R3 copies: a cheap stage-1 list, then a joint-reading classifier. Our scale is the reverse: a pool of 10–50 out of 97 chunks on a CPU, with a 22M-parameter distilled model. The paper's gain is an upper reference, not an expectation.

**[R3-S2] The `ms-marco-MiniLM-L6-v2` numbers** (sentence-transformers v6.1.0 `docs/cross_encoder/pretrained_models.md`, verified; the HF model card itself was blocked).
- *Table:* NDCG@10 on TREC DL 2019 **74.30**; MRR@10 on MS MARCO dev **39.01**; **1,800 docs/sec**. The hardware (V100 GPU, Transformers v4) is from search-checked mirrors of the card, UNVERIFIED.
- The 12-layer sibling scores 74.31 / 39.02 at 960 docs/sec. So on MS MARCO, L12 buys nothing over L6 at half the speed.
- The docs: raw scores "can reasonably range between −10 and 10"; pass `activation_fn=torch.nn.Sigmoid()` to get 0–1. The docs' canonical id is `cross-encoder/ms-marco-MiniLM-L6-v2` (no hyphen before 6). The course and repo use `…-L-6-v2`, which P4 loaded at revision `233902d2…`. Whether both ids resolve to the same weights is UNVERIFIED (HF blocked); the verify notebook checks the revision once.
- *For the project:* 39.01 is MS MARCO, not Corpus D. Say "domain shift: measure first" (06 "When NOT").

**[R3-S3] sentence-transformers 6.1.0 `CrossEncoder`, the installed version** (wheel source, verified; `uv.lock` pins 6.1.0 with transformers 5.19.0 and torch 2.14.1).
- `__init__` (`cross_encoder/model.py` L150–L210): `max_length=None` → the tokenizer's `model_max_length`, capped at `max_position_embeddings` (`base/modules/transformer.py` L874–L884), so 512 for this model. `revision=None`. `backend="torch"` (ONNX and OpenVINO also exist).
- **Activation default** (`get_default_activation_fn`, L406–L427): first the model config's `sentence_transformers.activation_fn`, then the pre-v4 key, then **`Sigmoid` if `num_labels == 1`, else `Identity`**. Only `torch.*` paths are trusted without `trust_remote_code` (L395–L404).
  - So the scale depends on the model: P4 measured `Identity` (raw logits) for ms-marco-MiniLM because its config says so. A model whose config sets nothing returns sigmoid scores.
  - The version history (whether pre-v4 releases always returned raw logits for this model) is UNVERIFIED. The source shows only the backward-compatibility key.
- `predict` (L568–L750): `batch_size=32`; inputs are **sorted by length** and padded per batch, then un-sorted; scores below float32 are upcast "to break ties"; `convert_to_numpy=True`.
- Truncation: text pairs use `truncation="longest_first"` (`transformer.py` L1259–L1260), so tokens are removed from the longer member first, usually the passage tail. **No warning is raised.**
- `rank(query, documents, top_k=None, return_documents=False)` (L752–L866): stable `sorted` by score, so ties keep input order. It raises for `num_labels != 1`.
- `model.max_length` is a deprecated alias of `max_seq_length` (L453–L460).
- *For the project:* pin `revision`, pass `max_length=512` explicitly, record `activation_fn` in the config hash, and count truncated pairs with the model's own tokenizer.

**[R3-S5] Sun et al. 2023, "Is ChatGPT Good at Search? Investigating LLMs as Re-Ranking Agents"** (EMNLP 2023; arXiv 2304.09542; paper search-checked; repo `sunnweiwei/RankGPT` @ `0d62bc3` README and `rank_gpt.py` verified).
- *The study:* listwise "permutation generation". The LLM sees about 20 numbered passages and outputs an order such as `[2] > [1] > …`. BM25 top-100 is reranked with a **sliding window of 20, step 10, from back to front** (`sliding_windows` L234–L244).
- *The result (search-checked):* GPT-4 beats fine-tuned monoT5-3B by about 2.7 / 2.3 / 2.7 nDCG@10 on TREC / 8 BEIR sets / Mr.TyDi. A distilled 435M student beats monoT5-3B on BEIR by about 1.67.
- *Limits:* GPT-4 cost; contamination risk on public benchmarks (the authors built NovelEval for this); nDCG@10 only, with no latency.
- *Code fact (verified):* `sliding_windows` starts at `rank_end − window_size` and loops while `start_pos ≥ rank_start`. If the pool is **smaller than the window** (N = 10, window 20), **no call is made** and the input order is returned unchanged.
- *For the project:* a listwise arm at N = 20 is one call per query. Window maths: ⌈(N − w)/s⌉ + 1 calls (N = 50 → 4; N = 100 → 9). Guard N < w.

**[R3-S6] Tang et al. 2023, "Found in the Middle: Permutation Self-Consistency Improves Listwise Ranking in LLMs"** (arXiv 2310.07712, NAACL 2024; search-checked only).
- *The study:* listwise outputs change with the **input order**. The method shuffles the list several times and aggregates the rankings.
- *The result:* gains of up to 7–18% (GPT-3.5) and 8–16% (LLaMA-2-70B) across five ranking datasets; sampling temperature did not help.
- *For the project:* measure order sensitivity with two orderings (first-stage and reversed). A listwise LLM fed the first-stage order may simply echo it. Report Kendall τ(output, input order) as an "echo" diagnostic.

**[R3-S7] Qin et al. 2023, "Large Language Models are Effective Text Rankers with Pairwise Ranking Prompting"** (arXiv 2306.17563; search-checked only). Pairwise prompts ("which of A and B is more relevant?") with a 20B open model are competitive with GPT-4 listwise on TREC-DL, and beat pointwise LLM prompting by more than 10% on BEIR. All-pairs costs N(N−1)/2 comparisons (190 at N = 20, doubled if both orders are asked). The paper offers cheaper variants. *For the project:* Full-only. Too many calls for Groq's free tier.

**[R3-S8] Cohere Rerank via the `cohere` 7.2.0 SDK** (wheel source, verified; docs.cohere.com blocked).
- `client.v2.rerank(model, query, documents, top_n=OMIT, max_tokens_per_doc=OMIT, priority=OMIT)`.
- The docstring says: model id e.g. `rerank-v3.5`, with an example of `rerank-v4.0-pro`; not more than 1,000 documents per request is recommended; **long documents are truncated to `max_tokens_per_doc`, default 4,096**; `top_n` omitted means all results.
- `relevance_score` (`v2rerank_response_results_item.py`) is "normalized to be in the range [0, 1]", and the field doc warns that 0.9 is not twice as relevant as 0.45. So it is an ordering score, not a calibrated probability.
- `meta.billed_units.search_units` exists (`api_meta_billed_units.py`).
- The v1 `rerank` keeps `max_chunks_per_doc` (internal chunking).
- Model ids `rerank-v4.0-pro`, `rerank-v4.0-fast` and `rerank-v3.5` are as in foundation §6.2.
- **Price, UNVERIFIED** (third-party search only [R3-S9]): about $2.00 (fast) / $2.50 (pro) per 1,000 searches. One search = 1 query with up to 100 documents.
- Whether a document's score depends on the other documents in the request is UNVERIFIED. The verify plan tests it.

**[R3-S10] LangChain** (wheel source, verified: `langchain-classic` 1.0.8, `langchain-core` 1.6.6, `langchain-community` 0.4.2, `langchain-cohere` 0.6.0):
- `ContextualCompressionRetriever` (classic, `retrievers/contextual_compression.py`): `base_retriever.invoke(query)`, then `base_compressor.compress_documents(docs, query)`. No pool-size field: the pool is whatever the base retriever's k is.
- `CrossEncoderReranker` (classic, `document_compressors/cross_encoder_rerank.py` L16–L50): **`top_n=3`**; `model.score(pairs)`, then a stable sort descending. **The scores are discarded**, not written to metadata.
- `BaseCrossEncoder` is defined in `langchain_core/cross_encoders.py` (one abstract `score` method). So the course can wrap its own pinned `CrossEncoder` with only `langchain-core`.
- `HuggingFaceCrossEncoder` (community): default **`BAAI/bge-reranker-base`**; `model_kwargs` are passed to `sentence_transformers.CrossEncoder` (not to HF), so `revision` and `max_length` go there. For 2-label models it returns a lazy `map` of column 1.
- `LLMListwiseRerank` (classic `listwise_rerank.py`): one structured-output call with all documents (no window), `top_n=3`. `_parse_ranking` raises `IndexError` on an out-of-range id, drops ids the model leaves out, and keeps duplicates. It needs the model's `with_structured_output` (so our `CachedChatModel` must implement `bind_tools`). It cites arXiv 2305.02156 (not opened).
- Classic `CohereRerank`: `@deprecated`, default model `rerank-english-v2.0`. `langchain-cohere` 0.6.0 `CohereRerank`: `top_n=3`, model required, but `Requires-Dist: cohere (>=5.18.0,<6.0)`, so it **conflicts** with our cohere 7.2.0 (foundation finding 4 confirmed). It writes `relevance_score` into metadata.

**[R3-S11] LlamaIndex** `llama-index-core` 0.14.25 (wheel, reading only): U9 and U10 above. `RankGPTRerank`: `top_n=5`, each passage cut to its first 300 words, one call with no window; its parser drops duplicate ids and appends any missing ones in the original order. That is more forgiving than LangChain's.

**[R3-S12] `BAAI/bge-reranker-v2-m3`** (search-checked only): about 568M parameters, about 2.27 GB, 8,192-token input, multilingual. Licence reports conflict (Apache-2.0 vs MIT). **Heavy** (> 500 MB). Its config probably sets no activation, so ST would apply sigmoid (UNVERIFIED). Not proposed: Corpus D chunks are ≤ 182 tokens and English, so the 8K context buys nothing.

**[R3-S13] BEIR (Thakur et al. 2021)** (search-checked; phase_03 [S16]): BM25 + cross-encoder reranking generalised best zero-shot across 18 datasets. That supports "rerankers transfer better than dense retrievers", but Corpus D still needs its own measurement.

**AIQ 04 Q10 / Q58 [R3-S14]:**
- Q10 says reranker scores are "more meaningful for thresholding" than cosine and act as a calibration layer. That holds only after per-corpus calibration on labels (06 §8.4, MC-006). The lesson should show this as a claim to qualify, not as a rule.
- Q58's deployment advice matches this plan: apply the LLM to the cross-encoder's top about 20, control position bias, prove the gain per slice.

**Session estimates (derived, not measured; the verify notebook replaces them):**
- *Truncation:* v0 chunks are at most 182 WordPiece tokens (07 D.6), and seed questions about 10–25. So pairs are ≤ about 210 tokens < 512, and **0 truncated** on v0. This assumes the cross-encoder shares MiniLM's 30,522 BERT vocabulary (UNVERIFIED). I1's 2000/400 arm reaches 365 tokens: still under 509.
- *Compute:*
  - MiniLM-L6-H384 has about 10.6M non-embedding parameters (6 × (4·384² + 2·384·1536)), so about 2 × 10.6M ≈ 21 MFLOP per token, or about 4.2 GFLOP per 200-token pair (attention ignored).
  - Check against [R3-S2]: 1,800 docs/s on a V100 is about 2 GFLOP per 100-token pair × 1,800 ≈ 3.8 TFLOP/s, a plausible V100 rate.
  - On a laptop CPU at an effective 50–150 GFLOP/s: N = 20 → about 0.6–1.7 s; N = 50 → about 1.4–4 s per query.
  - These are **order-of-magnitude only and UNVERIFIED**. They may be pessimistic (AIQ Q48 says 50–300 ms for about 100 documents, presumably on a GPU). They make one point: on CPU, pool size is a real latency lever. Measure.
- *Ties:* 20 candidates on a 10-level scale gives at least one tie (pigeonhole), and in practice many. On a 0–3 scale at least 16 of the 20 documents share a grade with another document.

**Current practice (2024–2026).**
- Hybrid stage 1 → cross-encoder or hosted rerank over about 50–200 → keep 5–20 (AIQ Q3, Q10).
- Open-weight rerankers: ms-marco MiniLM, BGE, mxbai (listed in the ST docs [R3-S2]). Hosted: Cohere v3.5 / v4.0.
- LLM rerankers: listwise with windows (RankGPT), or small decoder models fine-tuned for pointwise yes/no (AIQ Q58), used on a slice or distilled.
- Since the original paper: distilled small models (in the [R3-S2] table MiniLM-L6 scores 1,800 docs/s against electra-base's 340, about 5×, with higher MS MARCO scores); permutation-based LLM reranking; reranker scores used for routing and abstention (always with calibration).

**Library defaults the lessons warn about:**

| Component | Default | Course rule |
|---|---|---|
| ST `CrossEncoder` | `max_length` = model max (512); activation from config, else sigmoid for 1 label; `batch_size=32`; `revision=None` | Pin revision; pass `max_length`; record activation |
| LangChain `CrossEncoderReranker` | `top_n=3`; scores dropped | Set `top_n` = k = 4; use a scoring wrapper that logs the scores |
| `HuggingFaceCrossEncoder` | `BAAI/bge-reranker-base` | Never rely on it; pass the model id and revision |
| `LLMListwiseRerank` | `top_n=3`; no window; strict id parsing | Wrap; repair permutations; N ≤ 20 |
| LlamaIndex `SentenceTransformerRerank` | stsb model, `top_n=2`, `trust_remote_code=True` | Read-only; name all three |
| LlamaIndex `LLMRerank` | `top_n=10`, batch 10, filters | Read-only |
| Cohere v2 rerank | `top_n` all; `max_tokens_per_doc` 4,096 | Send both explicitly; keep all scores |
| RankGPT `sliding_windows` | window 20, step 10; N < window → no call | Guard |

**Pitfalls, with evidence:**
- Gold outside the pool: the ceiling ([R3-S1] reranks a top-1,000 for this reason).
- No headroom: C4 S6 seeds are already at CE@4 = 8/8.
- Silent truncation ([R3-S3]).
- Score-scale confusion: VAI L22 "improvement %" mixes logits with cosines.
- Model-dependent activation ([R3-S3]).
- LLM ties and parse failures (U1, U2, U9).
- Listwise position bias ([R3-S6]).
- Windows that never run ([R3-S5]).
- Default `top_n` of 2–3 instead of 4 ([R3-S10], [R3-S11]).
- STS model instead of a relevance model (U10).
- Hosted truncation at 4,096 ([R3-S8]).
- Multi-span demotion (gap 16).
- Latency measured with the model load inside, or as a p95 over 16 numbers.

**How to evaluate.**
- Retrieval only (06 v2.1): primary MRR@10 on the reranked list. Guards: Hit@4 and CE@4 (non-inferiority), CE@pool (ceiling, unchanged by the reranker by definition), gold demotions, p95 rerank latency.
- Before running: **headroom** = oracle − champion per pool size.
- Baseline: the v2.0 champion (06 §4.1 rule 1), not v0.
- Statistics: per-item RR differences, sign test and group bootstrap from M4. Pool 20 is primary; the other arms use Holm.
- Generation only for the chosen pool, with deterministic checks plus about 10 read answers (D-10).
- LLM and Cohere arms are reported in a separate table, with cost and calls.

**Interview questions:**
1. AIQ 04 Q10: what a reranker is and why you add it after vector search. Follow-up: "your reranker adds 250 ms."
2. AIQ 04 Q25: bi-encoder vs late interaction vs cross-encoder.
3. AIQ 04 Q58: pointwise, pairwise and listwise LLM reranking.
4. AIQ 04 Q43 follow-up: "recall@100 is 95% but recall@5 after rerank is 60%: where is the bug?"
5. Derived: "Would you threshold on the reranker score to abstain? What would you need first?"

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).** A reranker is a second, slower judge. The fast retriever fetches a pool of candidates, and a model that reads the question and each candidate together re-orders that pool, so the best few reach the prompt. It can only reorder what the pool already holds, so before you add one, check how often the evidence is in the pool at all (CE@pool) and how much better a perfect reordering would be than today's ranking. It costs one model pass per candidate, so the pool size is a latency decision you measure as p95 on your own CPU, together with the quality gain. Its scores order candidates but are not probabilities: a raw logit, a sigmoid and Cohere's 0–1 score mean different things, and an LLM's 1–10 score ties so often that the tie rule quietly decides the result. Reranking keeps a fixed k and changes their order, while relevance grading (V2) drops what falls below a threshold, which is why a grader needs calibrated labels and a reranker does not.

**The theory in one read (12 ideas, each with its formula).**
1. *Two stages:* pool P_N = champion top-N; reranked list π = argsort_desc s(q, d), d ∈ P_N; context = π[1..k], k = 4.
2. *Why the bi-encoder is cheap:* documents are encoded once at index time; per query: 1 encoder pass + N_corpus dot products. A cross-encoder has nothing to precompute.
3. *Cost of the cross-encoder:* passes per query = N; tokens per pass = |q| + |d| + 3; latency ≈ a + b·N (measured). Derived compute ≈ 21 MFLOP per token for MiniLM-L6 (§5 estimate).
4. *Ceiling:* Hit@k(π) ≤ Hit@N(P_N); CE@k(π) ≤ CE@pool. The reranker never changes CE@pool.
5. *Headroom:* oracle = a perfect reordering of P_N, so Hit@k_oracle = Hit@N and MRR_oracle = Hit@N. Headroom = metric_oracle − metric_champion. Realised gain = headroom × efficiency.
6. *Pool size:* CE@pool is non-decreasing in N, while hard negatives and latency grow with N. Choose the smallest N not separable from the best (tie rule), within the p95 budget.
7. *Ties:* with L score levels and N > L, P(tie) = 1. Ties are broken by the first-stage rank as an explicit second key: sort by (−s, rank_stage1).
8. *Truncation:* a pair is cut when |q| + |d| + 3 > 512, `longest_first` (passage tail). trunc_rate = #pairs over 512 / #pairs.
9. *Score scale:* the logit z ∈ ℝ; σ(z) = 1/(1 + e^(−z)) is monotone, so the order is the same and thresholds and "improvement %" change. Scores are not comparable across queries or models. Cohere's [0, 1] is non-linear [R3-S8].
10. *LLM formulations and calls per query:*
    - pointwise: N calls;
    - listwise with window w and step s: ⌈(N − w)/s⌉ + 1 calls (0 in RankGPT's code if N < w);
    - pairwise: N(N − 1)/2.
    Cost per query = Σ_calls (in·p_in + out·p_out).
11. *Position bias (listwise):* bias = 1 − τ(rank(order A), rank(order reversed)); echo = τ(output, input order).
12. *Reranking vs grading:* rerank returns exactly k; a grade keeps {d : s(d) ≥ θ}, from 0 to N documents. θ needs labelled calibration (06 §8.4, MC-006).

**Formula-sheet items:** the ceiling inequalities; headroom; passes per query (bi vs cross); pair length and trunc_rate; sigmoid; the tie certainty; LLM calls per formulation, including the window formula; cost per query; Kendall τ for bias; RR and MRR@10 on the reranked list; the gold-demotion count; p95 (method named, 06 §7.5).

**Step-by-step outline.** Running example: Corpus D, frozen snapshot, the M1 dev split, pool from the v2.0 champion. If v2.0 is not adopted, use v0 dense with Cohere vectors from the C3 cache (replay), or MiniLM offline. No other data is needed, because the concept is "does a second stage help on this corpus at this scale?" A note on scale (gap 7) tells Yash to re-run the latency sweep on Corpus T.
1. **Bridge (10 min):** P4 D.7 bi vs cross; re-run P4 S8 D-002 (gold rank 2 → 1). Ask Yash to predict the cost at N = 20.
2. **Read the repo critically:** `reranking.ipynb` cells 15, 23, 27 against U1–U7; the LlamaIndex `LLMRerank` parser (U9) as an "often confused" row.
3. **Headroom first:** for each dev item, the first-stage rank of the first gold chunk; Hit@4, Hit@N, CE@pool and oracle MRR for N ∈ {10, 20, 50, 97}. If the oracle − champion gap is about 0, record "no headroom" and stop the quality claim (latency is still taught).
4. **Pre-register:** primary arm N = 20; secondary 10 and 50; Holm; tie rule (smaller pool); p95 budget; guards.
5. **Score once, slice many:** cross-encoder over pool 50 (pinned revision, `max_length=512`, activation recorded). Pools 10 and 20 are prefix slices. Assert that pool 10 rescored separately matches within 1e-4. Report the truncation count (expected 0).
6. **One query in detail:** D-002's pre-rank → post-rank slope chart with logits; then the same chart in sigmoid units, to show the order does not change.
7. **Metrics per pool vs the champion:** MRR@10, Hit@4, CE@4, demotions; b/c and the M4 interval.
8. **Latency:** warm model, `torch.set_num_threads` fixed, 5 repeats × dev items; p50/p95 with nearest-rank **and** linear named; load time separately; plus "all 97".
9. **LLM arms (cached, pool 20):** pointwise 0–3 rubric via Groq → tie rate, agreement with the cross-encoder (Kendall τ), cost. Listwise (RankGPT prompt, 1 window) in first-stage order and reversed → bias and echo.
10. **Optional Cohere arm:** one call per query at N = 50 (cached), with the same metrics, plus `search_units`.
11. **Decide** by the pre-registered rule; one test touch; `TEST_LOG.md` with m = number of arms.
12. **Generation** for the chosen arm only, plus "when NOT to use".

**Visuals that earn their place:**
- *Funnel:* 97 → N → 4, with passes and milliseconds per stage. Shows where the cost lands.
- *Slope chart* (pre-rank → post-rank, gold highlighted). Shows what reranking actually does to one query.
- *Ceiling-and-headroom chart:* Hit@N / CE@pool / oracle / champion / reranked against N. Shows how much gain is possible at all.
- *Latency curve:* p50/p95 against N, with the budget line. Shows the cost side of the same decision.
- *Logit vs sigmoid strip:* identical order, very different "improvement %" (VAI L22). Shows why scale is not meaning.
- *Score histograms:* cross-encoder (continuous) vs LLM 0–3 (spikes = ties). Shows why the tie rule matters.
- *Listwise bias scatter:* output rank in order A vs in order reversed. Shows position bias.

**Full only:**
- MS MARCO numbers and the monoBERT history [R3-S1, S2];
- activation-default rules across ST versions [R3-S3];
- the batch-padding float noise;
- Cohere billing and `max_tokens_per_doc`;
- pairwise PRP;
- permutation self-consistency;
- ColBERT and MaxSim sidebar (review L258);
- distillation;
- the BGE v2-m3 trade-off;
- the LlamaIndex parser defects (U9);
- the "pool = whole corpus" diagnostic.

### 7. Verify notebook plan

`study/notebooks/R3_reranking_verify.ipynb`. Offline by default: local cross-encoder plus MiniLM, or Cohere vectors from the C3 cache in replay. Plotly charts.
1. **Model facts:** load `cross-encoder/ms-marco-MiniLM-L-6-v2` at the P4 revision `233902d2…`. Assert `max_seq_length == 512`, `num_labels == 1`, activation `Identity`. Print the ST, transformers and torch versions. Also load the canonical id `…-L6-v2` once and compare the revision hash and weights sha (settles [R3-S2]'s id question; needs one download, then offline).
2. **Truncation:** pair token counts with the cross-encoder's own tokenizer for the v0 chunks and the I1 arms (1500/300, 2000/400). Assert v0 = 0 truncated; print the maximum pair length.
3. **Order and scale:** CE(q, d) vs CE(d, q) on D-002 (re-checks P4 S8). Sigmoid preserves the order (assert identical argsort). The "improvement %" toy from VAI L22.
4. **Pointwise independence:** scores for pool 10 computed alone vs as a slice of pool 50: max abs diff (expect < 1e-4, not 0, because of length-sorted batch padding). Ties: 0 expected.
5. **Ceiling asserts on every item:** Hit@4(π) ≤ Hit@N; CE@4(π) ≤ CE@pool; MRR_oracle = Hit@N. A T1-style test.
6. **Pool sweep on dev** (once the M1 dev split exists): headroom table, MRR@10 / Hit@4 / CE@4 / demotions per N, paired b/c against the champion.
7. **Latency harness:** warm-up, fixed threads, 5 repeats; p50/p95 (nearest-rank and linear); load time; "all 97".
8. **Toy LLM-score mechanics, no API:** a tie-rate simulation (random 1–10 and 0–3 grades for N = 20; the share of documents in ties); the tie rule; a hand port of the LlamaIndex parser (about 25 lines) fed crafted strings, showing the "Doc: 0" and misalignment cases; RankGPT's window-count formula and the N < w no-call case with a fake LLM.
9. **Optional cached cells (replay only):** Groq pointwise and listwise outputs, and Cohere scores, recorded by the LLMOps notebook. If nothing is recorded, the cells print "not recorded".

- **Runtime:** cross-encoder scoring of about 16 × 50 = 800 pairs, plus the latency repeats. Roughly 1–5 minutes on CPU (UNVERIFIED; it depends on the §5 compute estimate).
- **API calls:** 0 (cached cells replay only).
- **Network:** the HF model download once (A-04), then `HF_HUB_OFFLINE=1`.

### 8. Apply-it tool plan and real-world checklist

`study/tools/rerank_check.py`: "Would a reranker help **my** retriever on **my** questions, at what pool size, within my latency budget?"
- **Inputs:**
  - `--docs`; `--questions q.jsonl` (`q`, `expect` quote or span, optional `category`);
  - `--retriever bm25|minilm|cohere-cached|hybrid`; `--pools 10,20,50`; `--k 4`;
  - `--reranker ce-minilm|cohere-cached|llm-pointwise-cached`; `--model-revision`; `--max-length 512`;
  - `--budget-ms 300`; `--threads N`; `--report out.md`.
- **Outputs (Markdown plus Plotly HTML):**
  - the headroom table;
  - per-pool MRR@10, Hit@4, CE@4 and demotions;
  - a rank-movement list per question;
  - truncation rate; tie rate (LLM); score-scale note;
  - p50/p95 latency and load time;
  - the checklist and a recommendation.
- Like `bm25_fit_check.py`, it shows the mechanism and what the question set can resolve. It is not an evaluation.

**Real-world checklist (12 checks):**

| # | Check | Auto / manual |
|---|---|---|
| K1 | Gold is in the pool for most items (CE@pool, Hit@N per N reported) | auto |
| K2 | Headroom (oracle − current) > 0 at the chosen N; otherwise "nothing to gain" | auto |
| K3 | Pairs are (query, passage), in that order | auto |
| K4 | Truncated pairs = 0, or the rate is reported (model's own tokenizer, limit 512) | auto |
| K5 | Model id **and** revision pinned; `max_length` and activation recorded | auto (config) |
| K6 | `top_n` / k set explicitly (no library default of 2–3) | auto |
| K7 | Tie rule explicit; tie rate reported for discrete-score rerankers | auto |
| K8 | Gold demotions (pre ≤ k → post > k) listed and read | auto + manual (read the chunks) |
| K9 | p95 latency at the chosen N within the budget, measured warm with threads fixed and the method named | auto |
| K10 | No score threshold used for abstention unless calibrated on labelled items | manual (cite the calibration) |
| K11 | Domain check: per-category gain shown with n; no category with a large loss | auto + manual |
| K12 | Hosted or LLM reranker: calls, cost per query, cache hit rate and `max_tokens_per_doc` recorded | auto |

**Recommendation logic:**
- K1 fails → "recall problem: fix stage 1 (R1, chunking), not ranking".
- K2 ≈ 0 → "no headroom: skip the reranker".
- K4 > 0 → "shorten chunks or raise awareness: the tail is invisible to the reranker".
- Gain supported and K9 passes → "adopt at the smallest N not separable from the best".
- Gain supported but K9 fails → "lower N, use a lighter model, or ONNX".
- Otherwise → "keep the champion; inconclusive".

### 9. LLMOps notebook plan

`study/llmops/notebooks/R3_reranking_ops.ipynb`: reranking as it runs in production (foundation §12 row "5 · R1–R5": Cohere rerank arm cached, p95 rerank latency, rerank fees, pool size in config, latency budget test).

**Framework build (each piece mapped to the mechanism):**
- *Stage 1:* a `langchain-core` `BaseRetriever` wrapper over the champion (M2's wrapper), with `k = N` from config and `chunk_id`, offsets, `pre_rank` and `pre_score` in metadata. Named default: `VectorStoreRetriever k=4`, which would make the pool equal to k.
- *Stage 2, cross-encoder:* `CourseCrossEncoder(BaseCrossEncoder)` (langchain-core only) holds a pinned `sentence_transformers.CrossEncoder(revision, max_length=512)`. Its `score()` logs pairs, logits, truncation and latency to the trace. It is plugged into `CrossEncoderReranker(top_n=4)` inside `ContextualCompressionRetriever` (classic). A post-hook re-attaches `rerank_score` and `post_rank`, because the compressor drops scores (named default `top_n=3`).
- *Stage 2, Cohere (optional):* `CachedCohereReranker(BaseDocumentCompressor)` over `llmops.providers.call_cohere_rerank` (not `langchain-cohere`, which conflicts). It sends `top_n` = None (all), `max_tokens_per_doc` and the model id explicitly.
- *Stage 2, LLM:*
  - pointwise: an LCEL chain `prompt | CachedChatModel(...).with_structured_output(Grade)` mapped over the pool, sorted by (−grade, pre_rank);
  - listwise: `LLMListwiseRerank.from_llm(CachedChatModel, top_n=4)` wrapped with a permutation repair (drop invalid and duplicate ids, append missing ones in first-stage order, log every repair).
  - Requires `CachedChatModel.bind_tools` (foundation §9.3). Not yet built, so UNVERIFIED.
- *Read-only cells:* the upstream classes (U4: why they cannot be instantiated under langchain-core 1.x); LlamaIndex `LLMRerank` and `SentenceTransformerRerank` defaults (U9, U10).
- No LangGraph: linear flow (foundation §9.1).

**Tracing (`llm-observability`):**
- One reranker span per (arm, qid): `model_id`, `revision`, `max_length`, `activation`/`score_kind`, `pool_size`, `top_n`, `batch_size`, `device`, `threads`.
- Per candidate: `chunk_id`, `pre_rank`, `pre_score`, `post_rank`, `rerank_score`, `truncated`, `pair_tokens` (OpenInference `reranker.input_documents` / `output_documents` with ids and scores).
- Latency split into `load_ms` (once per run) and `score_ms`. `cache_key` and `cache_hit` for Cohere and LLM calls. For listwise: the raw permutation and the repairs.
- Derived span attributes: `gold_pre_rank`, `gold_post_rank`, `demoted`.
- Local default: the JSONL trace → Phoenix (`uvx arize-phoenix@20.19.0 serve`). LangSmith only inside `tracing_context(enabled=True)` after `privacy.assert_corpus_is("D")`. About 16 queries × 5 arms ≈ 80 traces per dev run, well inside the 5k/month free plan.
- Exported spans carry ids and scores, not chunk text, unless the corpus is D.

**Dataset and evaluators (`rag-evaluation`, `code-based-evaluators`):**
- The M1 golden set (dev for selection, test once).
- Tier-1 evaluators as `(inputs, outputs, reference_outputs) → {key, score}`: MRR@10 (reranked list), Hit@4, CE@4, CE@pool, oracle MRR, `demotions`, `trunc_rate`, `tie_rate`, `bias_tau` (listwise), `rerank_ms`.
- Run through the course runner and once through `langsmith.evaluate(..., upload_results=False)`.
- Generation checks only for the chosen arm.
- **No judge** (D-10). The LLM reranker is a pipeline component, not an evaluator: its grades are never used as labels.

**Experiment against the previous version:**
- E-v2.1 arms against the v2.0 champion on identical comparison keys: CE at N ∈ {10, 20, 50}; optional Cohere at N = 50; LLM pointwise and listwise at N = 20 (reported separately, not adoption candidates unless Yash decides otherwise).
- M4's `compare_runs.py`: b/c, group bootstrap, Holm across the pool arms; `TEST_LOG.md` with m.

**External calls (all through `llmops.cache`; the notebook runs fully in `replay` with no key once recorded):**

| Call | Count per dev run (≈ 16 items) | Cost / limits |
|---|---|---|
| Cohere `rerank-v3.5` or `rerank-v4.0-fast` (model id pinned; choice open) | 16 (one per query at N = 50; pools 10 and 20 sliced) + 4 independence checks; test touch about 20; full-set table about 60 | ≤ 100 documents → 1 search each. At $2.00–2.50 per 1k searches (UNVERIFIED): ≈ $0.04–0.15. The trial limit of 10 rerank calls/min (foundation §2.5) means about 6 minutes for 60 calls; inside the 1,000 calls/month trial cap |
| Groq `openai/gpt-oss-20b`, pointwise (`reasoning_effort=low`, JSON output) | 16 × 20 = **320** | Assumed about 300 input + ≤ 200 output tokens per call: 320 × (300 × 0.075 + 200 × 0.30)/10⁶ ≈ **$0.026**. About 160K tokens: 80% of the 200K TPD and ≥ 20 min at 8K TPM (plan UNVERIFIED). Record once, over a day if needed |
| Groq, listwise (1 window of 20; 2 orderings) | 16 × 2 = **32** | About 3,800 input + ≤ 400 output: ≈ **$0.013**. Each call is about 4.2K tokens, so about 2 calls/min under 8K TPM |
| Claude Haiku 5.5 (`claude-haiku-5-5`, effort low), only if credits exist, as a comparison arm | 320 + 32 | ≈ 320 × (300 × 0.10 + 200 × 0.50)/10⁶ + 32 × (3,800 × 0.10 + 400 × 0.50)/10⁶ ≈ **$0.06** (lower bound; thinking tokens count as output) |
| Groq generation (chosen arm only) | about 16 dev + about 20 test ≈ 36 | ≈ $0.01 (foundation §6.3 rates) |
| Cohere embed (queries) | 0 new (C3 / M2 cache) | — |
| Judge | **0** (D-10) | — |

The local cross-encoder is not an API call. Its scores are content-cached (`sha256(model|revision|max_length|activation|query|passage)`) so metric cells replay identically. **Latency is always re-measured live.** In replay, Cohere and LLM latencies come from the recorded `latency_ms`.

**Cost, latency and tokens:**
- Per arm: rerank p50/p95 (cross-encoder live; Cohere and LLM recorded), calls and tokens per query, "cost if called" vs "paid", and Cohere `search_units`.
- The **latency budget test** (T1, `ci-cd-evals`): with the warm model and the fixed thread count, p95 `score_ms` at the champion's N ≤ budget, over ≥ 50 timings. It is skipped with a clear message on other hardware (record a `hardware_id`).

**Prompt and config versioning:**
- `rerank:` block in `config.yaml`: name, model_id, revision, max_length, activation, pool, top_n, batch_size, tie_rule, threads, plus `max_tokens_per_doc` for Cohere.
- LLM prompts as files: `prompts/rerank_pointwise_v1.txt` (0–3 rubric) and `rerank_listwise_v1.txt` (RankGPT-style).
- The prompt version and rendered sha go into the cache key and the trace. Any change is a new arm (one variable).

**Monitoring and feedback:**
- T1 tests:
  - the ceiling asserts;
  - pairs built (q, d);
  - `top_n == k`;
  - revision pinned;
  - trunc_rate = 0 on the champion chunker;
  - a regression check: MRR@10 ≥ champion − tolerance with a cap on worsened qids;
  - the `replay` marker on the notebook.
- Monitor page alerts: p95 over budget; a new truncation; demotions on regression items; CE@pool drop (a stage-1 regression); a shift in the mean top-1 logit on 3 canary queries (model or tokenizer drift); a change in the Cohere model id, or a deprecation notice; an LLM parse-repair rate > 5%; listwise bias τ below a set floor.
- A demoted-gold item goes to the M5 log as bucket "rank (reranker)" and then to the golden set as a regression item (`error-analysis`, `ci-cd-evals`).

**Place in the lifecycle:**
- Analyze: "right document, wrong rank" from CE@pool vs CE@4 (M5 bucket; `trace-data-analysis`).
- Measure: the headroom and the sweep (`rag-evaluation`, `code-based-evaluators`).
- Improve: adopt N, or no reranker (`improving-llm-agents` for the latency and cost side).
- dev → CI: the latency budget test plus the regression check (`ci-cd-evals`).
- Monitoring: `llm-observability`.
- Framing: `evals-foundations`.

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Cross-encoder runtime | `sentence-transformers` `CrossEncoder` | 6.1.0 (locked; transformers 5.19.0, torch 2.14.1 CPU) | yes | yes | — | Apache-2.0 | yes (D-20) |
| Default reranker model | `cross-encoder/ms-marco-MiniLM-L-6-v2` @ `233902d2…` | pinned revision | in the HF cache (P4) | yes (`HF_HUB_OFFLINE=1`) | $0 | Apache-2.0 (UNVERIFIED, card blocked) | yes (08 Q2, BACKBONE §6) |
| Heavier local option | `BAAI/bge-reranker-v2-m3` | — | no | yes after download | $0; **≈ 2.27 GB, 568M params (search-checked): heavy** | Apache-2.0 or MIT (conflicting) | **needs a decision**; not recommended (chunks ≤ 182 tokens, English). The lighter step is ms-marco L12, but it shows no MS MARCO gain [R3-S2] |
| Hosted reranker (optional arm) | Cohere `rerank-v3.5` / `rerank-v4.0-fast` / `-pro` via `cohere` | SDK 7.2.0 (keep) | yes | replay only | ≈ 40–60 searches per run; ≈ $0.04–0.15 (price UNVERIFIED); trial cap 1,000 calls/month | MIT (SDK) | yes (D-11 optional); Corpus D text leaves the machine (allowed) |
| LLM reranker (comparison arms) | Groq `openai/gpt-oss-20b` (`reasoning_effort=low`; JSON / structured output, model support per foundation, strict schema UNVERIFIED) | from `.env` | SDK yes | replay only | 352 calls ≈ $0.04 per dev run; TPM-bound (≥ 20 min) | — | yes (D-04) |
| Claude (only with credits) | `claude-haiku-5-5`, effort low; high-volume tier per foundation §6.4 | `anthropic` 1.11.0 | no | replay only | ≈ $0.06 per dev run (lower bound) | MIT (SDK) | yes (D-32), comparison arm only |
| Framework core | `langchain-core` (`BaseRetriever`, `BaseCrossEncoder`, `BaseDocumentCompressor`) | 1.6.6 | no | yes | — | MIT | yes (foundation §11) |
| Reranking wrappers | `langchain-classic` (`ContextualCompressionRetriever`, `CrossEncoderReranker`, `LLMListwiseRerank`) | 1.0.8 | no | yes | — | MIT | **needs a decision** (foundation lists it read-only). Light: core, text-splitters, langsmith, pydantic, pyyaml, requests, sqlalchemy. Alternative: about 25 lines on langchain-core |
| Not used | `langchain-community` (`HuggingFaceCrossEncoder`) | 0.4.2 | no | — | — | MIT | not needed: our `BaseCrossEncoder` subclass replaces it |
| Not used | `langchain-cohere` `CohereRerank` | 0.6.0 | no | — | — | MIT | **conflicts** (cohere < 6); use `CachedCohereReranker` |
| Graphs | `langgraph` | — | — | — | — | MIT | not needed (linear) |
| Reading only | `llama-index-core` (`LLMRerank`, `SentenceTransformerRerank`, `RankGPTRerank`) | 0.14.25 | no | — | — | MIT | read the source; do not install |
| Reading only | RankGPT `rank_gpt.py` @ `0d62bc3` | — | no | — | — | Apache-2.0 | prompt and window logic ported by hand |
| Hosted tracing | `langsmith` | 0.14.4 | no | no | free plan, about 80 traces per run | MIT (SDK) | yes, Corpus D only |
| Local tracing | `arize-phoenix-otel` 0.17.2 (+ server via `uvx arize-phoenix@20.19.0`) | — | no | yes | — | Apache-2.0 / ELv2 | yes |
| Statistics, metrics, plots | `numpy`, `scipy` (`binomtest`, `kendalltau`), `plotly` | locked | yes | yes | — | BSD / MIT | yes |
| Tokens (pair length) | the cross-encoder's own tokenizer (via ST); `tiktoken` `o200k_harmony` for LLM prompt tokens | locked | yes | yes | — | — | yes |

**Install lines (do not run):**
- `uv add --group llmops langchain-core==1.6.6 langchain-classic==1.0.8 langsmith==0.14.4 arize-phoenix-otel==0.17.2`. `langchain-classic` only if decision 3 is yes.
- `uv add --group llmops anthropic==1.11.0`, only when Claude credits exist.
- Nothing new for the lesson or the verify notebook.

**Keys:**
- `COHERE_API_KEY` (present), for the optional arm;
- `GROQ_API_KEY` (present), for the LLM arms;
- `ANTHROPIC_API_KEY` and `LANGSMITH_API_KEY` only if used.
After recording, no keys are needed.

### 11. Open questions for Yash (preferences only)

1. What p95 rerank budget do you want on your laptop CPU at the chosen pool: **300 ms** / 500 ms / 1 s? It is the pass line of the latency test.
2. Record the LLM reranker arms (about 350 Groq calls, about one day of free-tier tokens) or study them only on the toy and parser cells? **record** / toy-only.
3. If the Cohere arm runs, which model: **`rerank-v4.0-fast`** (cheaper, current) or `rerank-v3.5` (older, widely documented)?

---

## Concept R4: Diversity: MMR / Dartboard (U, project v2.3)

R4 changes **which** chunks fill the final top-k, not how chunks are scored. Plain top-k takes the k most relevant chunks, even when several say the same thing. A diversity selector takes a larger candidate pool and picks the k one at a time, so that each new pick adds something the earlier picks did not already cover. The course teaches two such selectors, and they are different objectives that the book and the Appendix blur together (08 B5):
- **MMR** (maximal marginal relevance; external, Carbonell & Goldstein 1998): relevance minus the similarity to the closest chunk already picked, mixed by λ.
- **Dartboard** (book Ch15; upstream `dartboard.ipynb`; Pickett et al. 2024): pick the set that best "covers" where the answer probably is, with Gaussian closeness and a smoothing width σ.

R4 is a **U** (useful) concept. The v2.3 experiment is worth running only if the eval set holds items that need two different chunks **and** plain top-4 misses one of them while the pool holds it. This audit found that the planned eval set has very few such items. That finding drives most of the plan below.

### 1. Sources checked

**Book (not present in this session; per 02/04/03/08, not re-opened, UNVERIFIED):**
- 02 R4 card (L706–L720): Ch15 p.5/12 (oversample), p.6–7/12 (iterative selection), p.8/12 (smoothing); App p.19/23 (MMR glossary).
- 04 §2 R4 row (L177) and the Ch15 table (L669–L695): Ch15 p.4/12–p.9/12, sketch p.7/12, first pick p.6/12, σ ≈ 0.1 on p.8/12.
- Pages that other files cite and 02's card omits:
  - Ch15 p.1–2/12 (relevance plus diversity; 04 DV-B3);
  - Ch15 p.10/12 (the "fusion diversifies" claim; 08 L224);
  - Ch15 p.11/12 (rerank, then diversify; 03 §4.4);
  - Ch15 p.12/12 (no index change; C3 concept L336);
  - App p.3/23 (calls Dartboard "MMR"); Ch19 p.4/10 (names MMR as an option); App p.19/23 (oversampling 3–5×; 08 B9).
- **The disagreement:** 02 cites p.5–8/12; 04 cites p.4–9/12 plus App p.3/23. They overlap and do not contradict each other, but neither one alone is the full list (R4-E1).

**Repo (verified: `all_rag_techniques/dartboard.ipynb` downloaded at `009adba` into the session scratchpad; cells read 0-based with `python3 -I`; code not run):**
- cell 0: cites "Better RAG using Relevant Information Gain" (arXiv 2407.12101). It says the notebook implements the paper's "vanilla" variant and adds relevance and diversity weights.
- cell 2: installs only `numpy` and `python-dotenv`, although cell 4 imports `scipy.special.logsumexp`. Cell 4 also prompts for the OpenAI key with `input()`.
- cell 9: `documents = documents*5`. Every page is loaded 5 times to "emulate a dense dataset". The text is split 1000/200 (characters) and indexed with OpenAI embeddings in FAISS.
- cell 13: `get_context` embeds the query with `embed_documents([query])` (the asymmetry hazard noted in P4/C4) and searches the raw FAISS index. The scores are dropped.
- cell 16: plain top-3. The saved output is **three identical chunks** (verified).
- cell 19: `lognorm(dist, sigma)` is a **Gaussian log-density** of the distance, not a log-normal distribution.
- cell 21: `greedy_dartsearch` with `DIVERSITY_WEIGHT = RELEVANCE_WEIGHT = 1.0` and `SIGMA = 0.1`. Mechanism (static reading):
  - The first pick is the argmax of the query log-density.
  - For every remaining candidate i and every pool point j, it computes `max(current best closeness to j, closeness(i, j))`.
  - It adds the query log-density of j, then takes `logsumexp` over j.
  - It picks the best i and repeats.
  - The returned "scores" are logsumexp totals, with a dummy 1.0 for the first pick. They are not marginal gains.
- cell 23: `get_context_with_dartboard(query, num_results=5, oversampling_factor=3)`. It fetches `num_results × oversampling_factor` candidates and rebuilds their vectors with `reconstruct_batch`. Its distances are `1 − VVᵀ` and `1 − qVᵀ`, which is correct only for unit vectors on an `IndexFlatL2` store.
- cell 24 (markdown): claims the top 3 "are not mere repetitions".
- cell 25: `get_context_with_dartboard(test_query, k=3)`, while the signature has `num_results`, so it raises a `TypeError` as committed (static reading). The saved output (exec count 22) shows 3 chunks, and **Context 1 and Context 3 are identical text** (verified).
- Upstream has no MMR notebook (02 is right).

**Existing course files:**
- 02 R4 card (L706–L720) and the per-technique gate (L1149–L1157); 02 L1268 (Ch15 row); 02 L1378 (week 18: "R2/R4 if indicated");
- 03: §3.2 R4 row (L534); §4.4 MMR/Dartboard rows (L685–L686) and the composition order (L690); §5 row 8 (L749); §6.4 Diversify row (L861); registry L437;
- 04: R4 row (L177); REVIEWER NOTE R-4 (L221); the Ch15 table (L669–L695); L965; DV-31/32/33 (L1020–L1022); DV-B3, DV-B6;
- 06: v2.3 card (L619–L628); config schema (L255–L300); §4.1 rules (L499–L507); §6.2 categories (L902–L915); seeds D-001…D-010 (L986–L1011); §7.3 traps (L1090); §11 module row (L1444);
- 08: B5 (L371), B9; RB7 (L417); stale outputs (L402); Q7/Q8 rows (L101, L179, L224, L265); Part 4 (D-03, D-07, D-09, D-10, D-32);
- the external review: L42, L62, L260 (MMR tests), L404 row 26 (MMR pool and relevance when the champion has RRF or a reranker), L526;
- P5 concept D.3 and H.2 (the 5× replay: 1 distinct chunk in the top-4 for D-002); P4 concept L373–L382; C4 concept L609;
- VAI L24 guide (`sources/vai/L24-L27…md` L48, L64, L91): a library MMR call with `fetch_k=20` and `lambda_mult` left at its default, mislabelled "hybrid";
- `LLMOPS_FOUNDATION.md` §2–§12; phase_04 (I1 `dup_frac`, I2 repeated headings, the winner's curse);
- the tracker (R4, R3, P4, P5, C4, M4, X3: `not_started`; M2 `exposed`); the misconception log (MC-002 "similarity matrix", MC-005 the k trade-off).
- **No R4 course files exist:** no `concepts/R4_*`, `study/reading/R4_*`, `study/questions/R4_*`, `labs/R4_*` or `sources/verification/R4/`.

**AE book:** none. The external review maps no AE section to R4.

**Interview repo (AIQ @ `e080df2`, MIT, "Copyright (c) 2026 Om"; verified):**
- AIQ 04 Q33 (L833–L857): dedup at ingest (exact hash, then MinHash/SimHash), query-time MMR "after reranking", λ ≈ 0.5–0.7 as a start, or "cap chunks per source document".
- AIQ `12-coding-challenges/17_hybrid_search_and_rerank.py`: `mmr()` (L134–L157) and tests 5–6 (L251–L273):
  - λ = 1 must reproduce plain top-k under the (−score, id) order;
  - redundancy must be a **max** over the selected set, not a mean;
  - the docstring (L52–L58) asks whether MMR runs before or after the reranker, and which relevance score it then uses.

**External (numbered in the R4 source list):**
- [R4-S1] Carbonell & Goldstein 1998 (search-checked);
- [R4-S2] Pickett et al. 2024/2025 Dartboard paper (search-checked);
- [R4-S3] the official Dartboard code `EmergenceAI/dartboard` (verified, raw files);
- [R4-S4] `langchain-core` 1.6.6 source (verified);
- [R4-S5] Clarke et al. 2008, α-nDCG (search-checked);
- [R4-S6] `ir-measures` 0.4.3 and `pyndeval` (verified, wheel and PyPI);
- [R4-S7] AIQ (verified);
- [R4-S8] Zhai, Cohen & Lafferty 2003, subtopic retrieval (UNVERIFIED, not opened).

**Session measurements (new; approximate; scratch only):**
- The climate PDF was downloaded (sha256 `1d58a0fa…92669`, matching C3_FACTS); its text was extracted per page with `pdftotext` and split into approximate per-page 1000/200 windows: **97 chunks**.
- **No embedder was available.** sentence-transformers is not installed in this container, and Hugging Face is blocked. So redundancy was measured with a **TF-IDF lexical proxy** (a session scratch script).
- A toy re-implementation of the upstream Dartboard logic was also written (a session scratch script).
- Every number from these is labelled *proxy* or *toy*. The verify notebook re-measures them with MiniLM and the cached Cohere vectors.

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Cosine vs dot vs L2; unit vectors make `1 − q·d` a cosine distance | upstream cell 23; LangChain `_cosine_similarity` | P4 (written, not studied) | P4 | no (MC-002 open) | bridge | One box: MMR needs **one** similarity scale for relevance and redundancy. Check `‖v‖ = 1` before using `1 − dot` |
| 2 | Plain top-k, ties, the (−score, chunk_id) rule | 06 §3.1; λ = 1 regression | P5 D.3 (not studied) | P5 / C4 | no | bridge | Recall the P5 duplicate replay (1 distinct chunk in the top-4 for D-002 on the 5× index) as the motivating failure |
| 3 | **Candidate pool / oversampling** (pool = factor × k) | Ch15 p.5/12; 06 "top-20 pool"; App p.19/23 3–5× | R3 (Ch13 p.5/13, not studied) | R3 → R4 | no | bridge | The selector can only choose from the pool, so CE@pool is its ceiling (as in R3). Add the new rule: with a duplication factor m, the pool needs ≥ m(k−1)+1 rows to hold k distinct texts |
| 4 | **MMR objective**: `argmax_{d∈R\S} [λ·sim₁(d,q) − (1−λ)·max_{s∈S} sim₂(d,s)]`; greedy; the first pick is always the top-relevance chunk | 06 v2.3; AIQ 04 Q33 | **missing** (book glossary only) | R4 | no | core | Full mechanism with a 5-chunk hand table; step-by-step marginal scores |
| 5 | **Max, not mean, redundancy** | AIQ 17 test 6 | **missing** | R4 | no | core | The geometric toy: a near-copy of one pick must be rejected even when it is unlike the others. The Dartboard paper's own "MMR" baseline uses a mean-pairwise objective (#18) |
| 6 | **What λ means depends on the score scale** | 06 λ grid {0.5, 0.7, 0.9} | **missing** | R4 | no | core | λ trades *differences* in relevance against *differences* in redundancy. Proxy example: at λ = 0.5, chunks with relevance ≈ 0.02 entered D-002's top-4. Dense cosines live in a narrow band, so the same λ means different things across embedders |
| 7 | λ = 1 equals plain top-k; λ = 0 is pure diversity after the first pick | AIQ 17 test 5; ext review L260 | **missing** | R4 | no | core | The two limits are the first regression tests |
| 8 | **Relevance source after R3**: embedding cosine vs reranker score (logits, not in [0, 1]) vs RRF score | ext review row 26; AIQ 17 docstring | **missing**; 06 v2.3 says "dense top-20 pool" | R4 (R3 owns the scores) | no | core | Pool = the champion's pool; relevance = the champion's final score, min-max normalised per query to [0, 1]; redundancy = cosine of the course embedder. Pre-register this and give its reason |
| 9 | **Dartboard objective**: choose S to maximise `log Σ_t P(t|q)·max_{s∈S} N(d(s,t); σ)` over the pool; greedy | Ch15 p.6–8/12; cells 19–23 | **missing** (04 has only the cell map) | R4 | no | core (Full for the formula) | Short: "darts land near the query; a set scores well if one of its picks is close to wherever a dart lands". Full: the log-space formula and the code mapping |
| 10 | **σ as the diversity dial**; the σ limits | Ch15 p.8/12; cell 21 | 04 row 7 ("σ ≈ 0.1") only | R4 | no | core | Toy (§5): σ ≤ 0.1 reproduced the KNN order, σ = 0.3 changed one pick, σ ≥ 1 jumped to off-topic clusters. σ is tied to the distance scale (#11) |
| 11 | **Distance scale**: upstream `1 − cos` ∈ [0, 2] vs official `(1 − cos)/2` ∈ [0, 1] | cell 23 vs [R4-S3] | **missing** | R4 | no | core | Upstream σ = 0.1 equals σ = 0.05 on the official scale. σ never transfers across embedders or distance definitions |
| 12 | Book rule "diversity = max distance from any selected" vs the code's coverage rule (DV-31) | Ch15 p.6–7/12 per 04 | 04 DV-31 | R4 | no | core | A max-distance rule would welcome a near-copy of pick 1 that is far from pick 2. That is why MMR uses the **closest** selected chunk |
| 13 | Exact duplicates vs near-duplicates vs complementary passages | 06 v2.3 Problem; Corpus D p.8/p.22–23, p.10/p.23 | backbone §0 note only | R4 / X3 | no | core | Three kinds with three fixes: hash dedup, threshold or MMR, keep both. Corpus D has **no exact duplicates**; its near-duplicates are paraphrases (§6 step 2) |
| 14 | **Near-duplicate ≠ redundant evidence**: p.10 and p.23 Paris paragraphs are near-identical but each holds a fact the other lacks (D-002 "2015" only on p.10; D-003 "regular reviews" only on p.23) | 06 seeds D-002/D-003 | **missing** | R4 | no | core | The central caution. Embedding redundancy is a guess about information redundancy. Show the eviction risk when the gold chunk is not the first pick |
| 15 | **Adjacent overlapping chunks**: a span cut at a boundary needs both neighbours (the CE union rule), and MMR penalises the neighbour for its 200 shared characters | 06 §7.2 union rule; I1 `dup_frac` | M2 (not studied) | M2 / I1 | no (M2 exposed) | core | Derived risk: diversity can turn a fragmentation success into CE = 0. Measure the "adjacent-pair evicted" count |
| 16 | **Cheaper baselines**: exact-hash dedup; cosine-threshold dedup (skip a candidate with cos ≥ τ to any pick, then fill by rank); a cap per page or section | AIQ 04 Q33 | **missing** | R4 (X3 owns assembly dedup) | no | core | Teach before MMR as "the 2-line fix". At λ = 0.9 MMR can still pick an exact copy, so hash dedup is always the first pass (§5) |
| 17 | **Redundancy and diversity metrics**: mean pairwise cosine in the top-k; distinct pages or sections; `dup_frac`; redundant-evidence rate; Group-Recall@k (= subtopic recall); α-nDCG@k | 02 outcome 3; 06 v2.3; 03 §6.4 | partly: Group-Recall in M2; `dup_frac` in I1; α-nDCG **missing** | M2 / R4 | no | core | Tautology warning: MMR lowers mean pairwise cosine by construction, so that number is a manipulation check. Gold-aware measures (Group-Recall, α-nDCG with groups as nuggets, redundant-evidence rate) carry the evidence |
| 18 | **What the Dartboard paper tested** (RGB QA; retrieval MRR/NDCG on Wikipedia revisions; best over a sweep; its MMR baseline is a mean variant) | 04 R-4 | **missing** | R4 | no | core (Full) | §5 study box; the claim is "competitive on one benchmark, tuned on the test sweep", not "better than MMR" |
| 19 | Selection order = rank order; MRR of an MMR list; MRR@10 when MMR returns 4 | 06 v2.3 guard | **missing** | R4 / M2 | no | core | Pre-register `k_select = 10` (MMR picks 10, metrics at 4 and 10), or "MMR picks 4, then the rest of the pool in its original order" |
| 20 | **Headroom / eligible items**: an item can improve only if it has ≥ 2 groups in distinct chunks, CE@pool = 1 and CE@4 = 0 | 06 v2.3 primary; 02 "per-technique gate" | **missing** | R4 (M2 for CE@pool) | no | core | A gate before running v2.3. Approx.: of the 3 seed multi-group items, only D-007 needs two chunks at 1000/200 |
| 21 | Small-n selection: the λ sweep on ~3 eligible dev items; the winner's curse | 06 §9.4; phase_04 I1 toy | M4 (not studied) | M4 | no | bridge | Pre-register one λ (0.7) plus the threshold arm; the sweep is exploratory; "inconclusive" is the expected verdict |
| 22 | Interaction with I5 headers / I2 section paths (headers change the cosine between p.10 and p.23 chunks) | phase_04 I2/I5 | phase_04 only | I5 → R4 | no | bridge | One line: redundancy depends on the embedded text. A header arm can make the two Paris chunks "different" |
| 23 | Interaction with X3 dedup and ordering (Phase 7) | 06 v4.0 | X3 (not written) | X3 | no | next | R4 changes membership; X3 merges overlapping characters and orders the context. Link only |
| 24 | Cost: O(pool² · d) similarities plus O(k · pool) greedy steps; trivial at pool = 20 | 06 v2.3 Cost; 03 §4.4 | 03 only | R4 | no | core | State it and measure p95. Reranking (R3) dominates the latency |
| 25 | LangChain defaults: `k=4, fetch_k=20, lambda_mult=0.5`; cosine recomputed; scores dropped; ties | VAI L24; LLMOps | **missing** | R4 (LLMOps) | no | core (LLMOps) | §9 defaults table |

### 3. Quiz coverage

No question file exists. Needed titles:
- **R-01** Write the MMR selection rule and say what each term and λ does. Why is the redundancy term a **max** over the selected set?
- **R-02** What do λ = 1 and λ = 0 give? Why is λ = 1 the cheapest regression test?
- **R-03** Name three kinds of redundancy (exact copy, paraphrase, adjacent overlap) and the cheapest fix for each.
- **R-04** What does σ control in Dartboard, and why does a σ tuned for one embedder not transfer to another?
- **A-01** Given a 5-chunk pool (relevance scores plus a 5×5 cosine table), run MMR by hand at λ = 0.7 for k = 3. Write the marginal score at each step.
- **A-02** A 5× duplicated index, k = 3, oversampling factor 3: how many distinct chunks can the pool hold? What factor guarantees 3 distinct? (Key: ⌈9/5⌉ = 2; pool ≥ 5·2 + 1 = 11, so a factor of 4.)
- **A-03** Given plain top-4 and MMR top-4 for 6 items, compute CE@4, Group-Recall@4, mean pairwise cosine and the redundant-evidence rate. Say which change is evidence of benefit and which is a manipulation check.
- **A-04** The champion is hybrid + cross-encoder. Write the pre-registered MMR configuration: the pool, the relevance source, its normalisation and the similarity used for redundancy.
- **T-01** D-003's gold is on p.23. The p.10 chunk is near-identical but lacks the answer and ranks first. What can MMR do to D-003, and what would you measure? (Key: eviction of a near-duplicate gold; MRR/CE on the near-duplicate-distractor tag.)
- **T-02** A support knowledge base keeps 3 versions of each policy. Hash dedup, threshold dedup, MMR or a version filter (R2)? Justify. (Key: a version filter or keep-newest first; MMR cannot know which version is current.)
- **Interview** (derived from AIQ 04 Q33 and challenge 17, MIT): "Your top-5 is five paraphrases of one paragraph. Walk me through the fixes in order of cost, and how you would pick λ without tuning it on vibes."

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| R4-E1 | 02 R4 card "Repo: cell 16, cell 23 (function), cell 25"; Book line | The selection algorithm is **cell 21** (`greedy_dartsearch`), and its log-density is cell 19. Cell 23 is the retrieval wrapper (oversampling, distance matrices). The card also omits cell 9 (the 5× duplication that creates the demo's problem) and cell 13. Its book line omits App p.3/23 and Ch15 p.11/12, which 03/04/08 use | Cite cells 9, 13, 16, 19, 21, 23, 25, and add App p.3/23 and Ch15 p.11/12 |
| R4-E2 | 02 card, 04 DV-33, 08 L402 ("stale output still contains a duplicate") | The duplicate is **what the committed algorithm would produce** with `num_results=3`. The pool is 3 × 3 = 9 rows from a 5× duplicated index, so it holds at most ⌈9/5⌉ = 2 distinct chunks, and a duplicate is unavoidable. A toy re-implementation returns `[A, B, A]` on such a pool (§5). The output is stale relative to the call (the `k=` TypeError), but the duplicate is not evidence that the algorithm fails | Add: "oversampling factor 3 < duplication factor 5; the pool needs ≥ 5(k−1)+1 rows". The demo cannot show its own claim at the defaults either: 15 rows hold 3 distinct texts for 5 results |
| R4-E3 | 04 Ch15 table row 7 ("Smoothing with σ ≈ 0.1 … Implemented") and row 2 | The notebook's distance is `1 − cos` ∈ [0, 2]; the official code's is `(1 − cos)/2` clipped to [0, 1] ([R4-S3] `scaled_cosdist`). So the notebook's σ = 0.1 equals σ = 0.05 on the paper code's scale. The notebook also adds RELEVANCE and DIVERSITY weights that the official code does not have | "Implemented on a different distance scale; σ is not transferable; the weights are an upstream addition" |
| R4-E4 | 06 v2.3 Change ("re-select the final top-4 from a dense top-20 pool; scoring model unchanged") | R4 requires R3 (02, 03), and v2.1's champion may be hybrid + cross-encoder. Running MMR over a dense pool with cosine relevance discards the champion's ranking, so two variables change. External review row 26 already flagged this; 06 is unchanged | Pool = the champion's candidate pool; relevance = the champion's final score, normalised per query; redundancy = cosine of the course embedder. Name all three in `config.yaml` |
| R4-E5 | 06 v2.3 guard "MRR@10 on factual-single-span" | MMR as specified returns 4 chunks, so MRR@10 is undefined for the MMR arm | Pre-register `k_select = 10` (metrics @4 and @10), or "MMR picks 4, then the rest of the pool in its original order" |
| R4-E6 | 06 v2.3 Hypothesis ("reduces … mean pairwise cosine within the top-4") | MMR lowers this number by construction, so it confirms the selector ran, not that it helped. It also depends on the embedder | Keep it as a manipulation check. Evidence of benefit: CE@4 / Group-Recall@4 on eligible items, plus the redundant-evidence rate and `dup_frac` |
| R4-E7 | 06 v2.3 Primary "CE@4 on multi-span"; §6.2 target 6 multi-span | About 30% of 6 is about 2 dev items. Seed D-005's two spans (p.2, chars 0–45 and 746–836) fit in **one** 1000-character chunk (approx.), so diversity cannot help it. Of the three multi-group seeds, only D-007 (p.10 + p.29) needs two chunks | Define "R4-eligible" items (≥ 2 groups in distinct champion chunks, CE@pool = 1, CE@4 = 0). Run v2.3 only if dev has enough of them; otherwise record "not indicated" (02 L1378 already says "if indicated") |
| R4-E8 | 02 R4 "Ext: … MMR primary source is not yet verified"; 04 REVIEWER NOTE R-4 | The primary source is identified: Carbonell & Goldstein, SIGIR '98, pp. 335–336, DOI 10.1145/290941.291025 (search-checked; the PDF host is blocked here). The Dartboard paper (cell 0's citation) is now titled "Dartboard: Better RAG using Relevant Information Gain" (v2). Its authors are Pickett, Hartman, Bhowmick, Alam and Vempaty (search-checked); the code is EmergenceAI/dartboard (verified) | Record both. Mark them "search-checked; open on Yash's machine" |
| R4-E9 | 03 §3.2 R4 row and §4.4; 04 R4 row ("Information-gain implementation") | A missing caveat. The paper's own "MMR" baseline (official `get_mmr_crosscoder2`) is a mean-pairwise-distance set objective, not Carbonell's max-similarity rule (static reading). So "Dartboard beats MMR" is against a variant that AIQ 17 calls a common mistake | Add one line to the R4 rows; the lesson's comparison uses textbook MMR |
| R4-E10 | 06 §2.4 config schema | It has no `diversify:` block, so λ, pool size, relevance source, redundancy similarity, the dedup threshold and `k_select` would not enter `config_hash` | Add `diversify: {name: none\|mmr\|threshold\|dartboard, pool, k_select, lambda, sigma, relevance: champion_norm\|cosine, sim: cosine, dedup: {exact: true, tau: null}}` |
| R4-E11 | 06 v2.3 title "MMR diversity (R4; book Ch15 Dartboard …)" | It pairs MMR with the Dartboard chapter, which is the B5 conflation the course warns about | "MMR (external, [R4-S1]); Dartboard arm optional (Ch15)" |

### 5. What the research says

**[R4-S1] Carbonell & Goldstein 1998, "The Use of MMR, Diversity-Based Reranking for Reordering Documents and Producing Summaries"** (SIGIR '98, Melbourne, pp. 335–336, DOI 10.1145/290941.291025; a 2-page poster paper; companion TIPSTER 1998 paper X98-1025). UNVERIFIED (search-checked only): ACM, the CMU copy and ACL Anthology were all blocked.
- *Study (per search summaries):* MMR reranking of retrieved documents, judged in a small user study, plus query-relevant single-document summarisation.
- *Result:* the abstract reports "preliminary" benefits. A secondary summary (a class slide deck) says 4 of the study users preferred MMR. No λ values or effect sizes were confirmed.
- *Limits:* a poster, a tiny user study, no modern retrieval metric, and documents rather than chunks.
- *For the project:* cite it for the **definition** only: relevance minus the **max** similarity to an already selected item, mixed by λ, chosen greedily. It is not evidence that MMR improves RAG answers.

**[R4-S2] Pickett, Hartman, Bhowmick, Alam & Vempaty, "Better RAG using Relevant Information Gain" (arXiv 2407.12101, v1 July 2024); v2 retitled "Dartboard: …" (Feb 2025); also a Springer chapter.** UNVERIFIED (search-checked only; arXiv blocked).
- *Study (search summaries, plus the code in [R4-S3]):*
  - Dartboard was used as the retriever inside a RAG pipeline on the **RGB** benchmark (English, plus the "information integration" split), with k = 5 passages.
  - A retrieval-only test used **Wikipedia articles with 5 revisions each** (built-in near-duplicates), 1,000 test and 100 eval queries, scored by MRR/NDCG of the one gold article, with and without exact dedup.
- *Result:* the authors report state-of-the-art RGB QA accuracy and better NDCG than KNN and MMR. One secondary summary quotes NDCG 0.973 (UNVERIFIED).
- *Limits:*
  1. For the tunable methods (Dartboard σ, MMR "diversity"), the **best score over a parameter sweep** is reported (search summary; consistent with `make_plots` printing the max over the sweep) → optimistic.
  2. The "MMR" baseline is a mean-pairwise variant (R4-E9).
  3. The retrieval metrics reward finding **one** gold article, not covering several facts.
  4. The authors say σ still needs manual tuning, like λ.
- *For the project:* Dartboard is a principled coverage objective and worth teaching as the book's chapter. There is no evidence that it beats a correctly implemented MMR on multi-fact items, so it stays an optional, re-implemented arm (06).

**[R4-S3] Official code, `EmergenceAI/dartboard`** (raw files at `main`, fetched 2026-10-17; commit hash not readable because the GitHub API is blocked; no LICENSE file found at the root (404). Verified by static reading.)
- `dartboard.py`:
  - L56–L58 `lognorm` (identical to upstream cell 19);
  - L59–L61 `scaled_cosdist = clip(1 − (cos+1)/2, 0, 1)`;
  - L89–L101 `greedy_dartsearch` (upstream cell 21 is this function plus weights);
  - L103–L109 the cosine and cross-encoder variants;
  - L112–L127 the hybrid variant (cross-encoder relevance as a softmax over the pool at temperature σ, and `log(1 − dist)` closeness);
  - L64–L67 rescales cross-encoder logits with fixed bounds −11.6/11.4;
  - L130–L148 `get_mmr_crosscoder2`: average query distance minus the average **pairwise** distance, the mean variant.
- `retrieval/do_eval.py`:
  - L30–L41: σ and "diversity" swept over 0…1 in steps of 0.01; triage (pool) = 100; maxk = 40;
  - L7–L8 import `get_dists_crosscoder_hybrid` / `get_dartboard_crosscoder_hybrid`, which `dartboard.py` does not define (`get_dists_hybrid` / `get_dartboard_hybrid`), so the retrieval eval should fail on import as committed (static reading).
- `end2end/do_eval.py`:
  - L7–L31: steps of 0.001, triage 100;
  - L316–L318: `temp = 0.01`, `passage_num = 5`, default model `chatglm`;
  - datasets `en`, `en_int` (L325).
- *For the project:* the two re-implementation hazards are the distance scale and the cross-encoder rescale constants. Also: the paper's own pool (100) is 20× k, against 06's 5×.

**[R4-S4] LangChain `langchain-core` 1.6.6** (wheel from PyPI, released 2026-09-29; verified).
- `vectorstores/utils.py`:
  - the module docstring says it is a **private API** that "can change without notice";
  - L112–L163 `maximal_marginal_relevance(query_embedding, embedding_list, lambda_mult=0.5, k=4)`;
  - first pick = `argmax` of cosine to the query (L144), so the first index wins ties;
  - later picks: `lambda_mult·query_score − (1 − lambda_mult)·max(sim to selected)` (L154–L157), replaced only on a strictly greater score (L158), so the earlier pool position wins ties;
  - cosine is **recomputed** from the raw vectors (L143, L150), whatever metric the store used for the pool.
- `vectorstores/base.py`:
  - L659–L664 `max_marginal_relevance_search(query, k=4, fetch_k=20, lambda_mult=0.5)`, documented as "0 = maximum diversity, 1 = minimum" (L676–L678);
  - L905–L943 `as_retriever(search_type="mmr")` with the same defaults; the example even uses `lambda_mult=0.25`.
- `vectorstores/in_memory.py`:
  - L314–L317: the pool is ordered by `argsort()[::-1]`, so **tied scores come out in descending index order**, the reverse of the course's `chunk_id` rule;
  - L442–L448: the query vector is cast to float32, and `Document`s come back **without scores**.
- *For the project:*
  - λ is defined as in [R4-S1] (06's λ multiplies relevance, as LangChain's does);
  - the default 0.5 is the most diverse value in 06's grid;
  - the framework cannot use a reranker score as the relevance term, so after R3 our own function is required;
  - a parity test must avoid ties, or apply the same tie order.

**[R4-S5] Clarke, Kolla, Cormack, Vechtomova, Ashkan, Büttcher & MacKinnon 2008, "Novelty and Diversity in Information Retrieval Evaluation"** (SIGIR 2008, pp. 659–666, DOI 10.1145/1390334.1390446). UNVERIFIED (search-checked only; the Waterloo PDF and TREC `ndeval.c` were blocked).
- *Study:* a cumulative-gain measure that rewards novelty: each "nugget" (subtopic) counts less every time it has already appeared higher in the list, by a factor (1 − α). Tested on TREC QA-track data.
- *For the project:* our `evidence_groups` are nuggets. So α-nDCG@k with groups as nuggets is the standard diversity metric, and it needs no new labels. Group-Recall@k (M2) is subtopic recall [R4-S8].
- Two conventions to record: the ideal ranking is usually built greedily, because the exact one is NP-hard (UNVERIFIED detail); and α = 0.5 is the common default (UNVERIFIED).

**[R4-S6] `ir-measures` 0.4.3** (wheel; verified): `providers/pyndeval_provider.py` L15–L18 exposes `alpha_nDCG`, `alpha_DCG` and `NRBP` through **`pyndeval`** (MIT). Its PyPI history shows 0.0.6 on 2024-10-03, and 0.0.7/0.0.8 on 2026-10-16, which is too new for the pin rule, so pin 0.0.6 (it has a cp312 win_amd64 wheel). Use it only as an optional cross-check of a 20-line NumPy α-nDCG.

**[R4-S7] AIQ** (verified):
- 04 Q33 gives the cost ladder: hash dedup → near-dup at ingest → boilerplate stripping → query-time MMR after the reranker (λ ≈ 0.5–0.7), or a per-source cap.
- Challenge 17 gives the two tests the course should copy as ideas: λ = 1 equals top-k under (−score, id), and max vs mean.

**Toy and proxy results (session-run; not results about our data).**
- *Dartboard σ limits* (`dart_toy.py`: 12 unit vectors in 3 topics, the query between topics 0 and 1, upstream logic re-implemented):
  - σ = 0.05–0.1 reproduced the KNN order exactly;
  - σ ≤ 0.01: the scores underflowed into ties, and the order fell back to the pool index;
  - σ = 0.3: swapped in one topic-1 item;
  - σ ≥ 1: picked items from the **off-query** topic 2.
  - So σ runs from "plain top-k" to "cover the whole pool", and the useful band depends on the distance scale.
- *Duplicate pool:* 5 copies of A plus 4 copies of B, k = 3, σ = 0.1 → `[A, B, A]`, the same pattern as cell 25's saved output (R4-E2).
- *MMR with an exact copy:* at λ, a copy c of a picked chunk beats a fresh chunk o when λ(r_c − r_o) > (1 − λ)(1 − red_o). At λ = 0.9 and red_o = 0.5, a relevance lead above 0.056 is enough. **MMR at high λ does not remove exact duplicates**, so a hash-dedup pass comes first (derived).
- *Corpus D lexical proxy* (TF-IDF, 97 approx. chunks):
  - The strongest cross-page pair is the **p.10–p.23 Paris chunk pair (0.54)**. It is the only cross-page pair ≥ 0.5 out of 4,560 (p.8–p.23 is 0.42).
  - D-002, D-003 and the smart-grid probe all had the gold at pool rank 1, so MMR could not evict it (the first pick is always rank 1).
  - At λ = 0.5, D-002's top-4 took chunks with relevance ≈ 0.02 (p.21, p.1).
  - The smart-grid probe's plain top-4 held all three smart-grid passages (p.22, p.8, p.23). MMR at λ ≤ 0.7 pushed p.8 down or out.
  - All of this is lexical. Embedding similarities will differ; the verify notebook re-measures it.

**Current practice (2024–2026).**
- Libraries expose MMR as a retriever option with a pool of about 5× k (LangChain k = 4, fetch_k = 20, λ = 0.5).
- Teams run cheap dedup first (hash, MinHash, a per-source cap) and MMR after reranking (AIQ 04 Q33).
- Coverage-style objectives (Dartboard) appear in research. Fixed-k diversity is often judged by eyeballing, as in upstream cells 16 and 25.

**Pitfalls, with evidence:**
- relevance and redundancy on different scales (LangChain recomputes cosine; reranker logits are unbounded; [R4-S3] uses hard-coded rescale bounds);
- mean instead of max redundancy ([R4-S7]; [R4-S3]'s baseline);
- oversampling below the duplication factor (R4-E2);
- high-λ MMR keeping exact copies (derived);
- evicting a near-duplicate that holds the answer (D-002/D-003 structure);
- evicting the adjacent chunk a cut span needs (union rule; derived);
- σ copied across embedders (R4-E3);
- tie order differing across implementations ([R4-S4] in_memory L314–L317);
- tuning λ or σ on the test sweep ([R4-S2]).

**How to evaluate:**
- **Gate first:** count the R4-eligible dev items. If there are fewer than about 5, record "not indicated".
- **Primary:** CE@4 on eligible items.
- **Secondary:** Group-Recall@4 and α-nDCG@4 (groups as nuggets) on multi-group items.
- **Guards:**
  - MRR@10 and Hit@4 on single-group items;
  - CE@4 on the `near-duplicate-distractor` tag;
  - the adjacent-pair-evicted count.
- **Manipulation checks:** mean pairwise cosine, distinct pages or sections, `dup_frac`, and the redundant-evidence rate (top-k chunks whose covered groups are already covered higher up).
- **Statistics:** discordant pairs and the M4 bootstrap against the champion.
- **Ops:** p95 per stage.
- Answer quality is separate: deterministic checks plus about 10 read answers (D-10).

**Interview questions:**
1. AIQ 04 Q33: a corpus full of near-duplicates; where do you deduplicate?
2. AIQ challenge 17 (follow-ups): implement MMR; why max, not mean; λ = 1 as a test; before or after the reranker?
3. Derived: "MMR raised diversity and lowered answer accuracy. Why?" (Single-fact lookups and evicted near-duplicate gold.)
4. Derived: "How do you pick λ without vibes?" (Eligible-item headroom, a pre-registered value, a paired test, "inconclusive" allowed.)
5. Derived: "Dartboard vs MMR in one sentence each."

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).**
Plain top-k can fill all k slots with paraphrases of one paragraph, so a question that needs two different facts gets only one of them. A diversity selector fetches a larger pool, keeps the most relevant chunk, and then adds chunks one at a time that are relevant **and** unlike anything already picked. MMR does this with one dial, λ, scoring each candidate as λ × relevance − (1 − λ) × similarity to its closest already-picked chunk, while Dartboard (the book's chapter) instead picks the set that best covers where the answer is likely to be, with a width σ. Both only help when a question needs several different chunks and the pool already holds them, and both can hurt a single-fact lookup by pushing out a near-duplicate that happens to contain the answer. So you first remove exact copies cheaply, check that your eval set has items diversity could fix, and then measure CE@4 on those items against MRR on single-fact items.

**The theory in one read (11 ideas, each with its formula).**
1. *The failure:* redundant top-k. `distinct = #{distinct texts in top-k}`. The 5× demo gives 1 distinct chunk in the top-4 (P5 D.3).
2. *Pool and ceiling:* `pool = f·k`. The selector's best is CE@pool. With duplication factor m, `pool ≥ m(k−1)+1` for k distinct texts.
3. *Cheapest fixes first:*
   - exact: `sha256(normalised text)`;
   - threshold: skip d if `max_{s∈S} cos(d,s) ≥ τ`, then fill by rank;
   - cap: ≤ c chunks per page or section.
4. *MMR:* `d* = argmax_{d∈P\S} [λ·rel(d) − (1−λ)·max_{s∈S} cos(d,s)]`; S starts with the top-relevance chunk.
5. *Max, not mean:* a near-copy of any one pick must be penalised fully.
6. *λ limits:* λ = 1 gives plain top-k (with the same tie rule); λ = 0 gives "the farthest from the picks" after pick 1.
7. *Scale:* `rel` and `cos` must be on comparable scales. After R3, `rel = (s − min_P s)/(max_P s − min_P s)` per query. Without this, λ has no stable meaning.
8. *Dartboard:* `score(S) = log Σ_{t∈P} exp(log p(t|q) + max_{s∈S} log N(d(s,t); 0, σ))`, with `log N(d; σ) = −log σ − ½ log 2π − d²/2σ²`; greedy.
9. *σ as the dial:* small σ gives plain top-k; large σ gives whole-pool coverage. Distance scale: `1−cos` (upstream) vs `(1−cos)/2` (official).
10. *Metrics:* CE@k and Group-Recall@k (= subtopic recall); `α-DCG@k = Σ_r Σ_g J(d_r,g)(1−α)^{c_{g,r−1}} / log₂(1+r)`; redundant-evidence rate; manipulation checks (mean pairwise cosine, distinct pages, `dup_frac`).
11. *When it can help:* `eligible = (#groups in distinct champion chunks ≥ 2) ∧ CE@pool = 1 ∧ CE@k = 0`. When it hurts: single-span items where the gold is not pick 1 and is near-identical to it, and spans cut across adjacent chunks.

**Formula-sheet items:** the MMR rule; λ limits; per-query min-max normalisation; the pool rule `m(k−1)+1`; the threshold-dedup rule; Dartboard's score and `lognorm`; the two distance scales; α-DCG; the eligible-item rule; the copy-wins inequality `λ(r_c−r_o) > (1−λ)(1−red_o)`.

**Step-by-step outline.** Running example: Corpus D (snapshot `ea07572562ac`), the champion from v2.1, and the M1 dev split. Corpus D is right for this concept: 06 and the backbone name its repeated topics as the redundancy case. Corpus T is not needed.
1. **Show the failure.** Replay the 5× index (P5 D.3): 1 distinct chunk in the top-4. Then remove the copies by hash: problem solved for free. *Lesson:* the upstream demo is an exact-duplicate problem.
2. **Real redundancy on Corpus D.** Draw the near-duplicate census: the cosine histogram of cross-page chunk pairs. Name the two pairs from 06 (p.10/p.23 Paris; p.8 vs p.22–23 smart grids). Read both Paris paragraphs side by side: near-identical wording, different facts ("2015" only on p.10; "regular reviews of NDCs" only on p.23).
3. **MMR by hand** on the smart-grid probe: a 5-chunk pool, the cosine table, λ = 0.7. Write the marginal score at each step and show which smart-grid passage leaves.
4. **λ limits as tests:** λ = 1 equals the champion's top-4 exactly; λ = 0 jumps off-topic. The scale box: at λ = 0.5 the proxy admitted chunks with relevance ≈ 0.02.
5. **Before or after R3:** the same item with the dense pool and cosine relevance vs the champion pool and normalised reranker relevance. Pre-register the latter.
6. **The eviction risk:** D-002 and D-003 under MMR. If the gold is pick 1, nothing changes; construct the case where the non-gold Paris chunk ranks first and show the gold's marginal score at each λ.
7. **The adjacent-chunk risk:** a span cut at a 1000/200 boundary. MMR penalises the neighbour, so CE falls from 1 to 0.
8. **Dartboard:** read cells 19–23 against `greedy_dartsearch`; fix cell 25 (`num_results=3`); explain the duplicate (R4-E2); re-implement on Corpus D vectors; sweep σ on the course distance scale.
9. **Metrics:** for plain, threshold, MMR λ = 0.7 and Dartboard, compute CE@4, Group-Recall@4, α-nDCG@4, MRR@10, the redundant-evidence rate, mean pairwise cosine, distinct pages and `dup_frac`.
10. **Headroom gate:** count the eligible dev items. If there are fewer than about 5, the verdict is "not indicated". Otherwise run the pre-registered comparison once on test (M4).
11. **Write the decision** with "when NOT to use" from your own data (D-002/D-003 type items).

**Visuals that earn their place:**
- *Pool-and-picks strip:* 20 pool chunks as dots coloured by page, with plain top-4 vs MMR top-4 arrows. Shows that membership changes and rank 1 never does.
- *Marginal-score table animation* (Short): the λ·rel and (1−λ)·maxsim bars per step. Shows "relevant **and** new".
- *λ curve* (Plotly): CE@4 on eligible items, MRR on single-span items, and mean pairwise cosine against λ. Shows the trade-off, and that the cosine always falls.
- *Twin-paragraph figure:* p.10 vs p.23 Paris text with the differing sentence highlighted. Shows that "similar" is not "redundant".
- *σ dial* (Full): the toy picks at σ = 0.05 / 0.3 / 1. Shows KNN → coverage → off-topic.

**Full only:**
- the Dartboard log-space derivation and the official-code variants (hybrid, cross-encoder rescale);
- the `m(k−1)+1` pool proof;
- the copy-wins inequality;
- α-nDCG ideal-ranking approximation;
- the paper's evaluation critique (best-over-sweep; the mean-MMR baseline);
- LangChain's tie order and private-API status;
- I5 headers changing redundancy;
- the cost O(pool²·d).

### 7. Verify notebook plan

`study/notebooks/R4_diversity_verify.ipynb`. Offline by default; MiniLM local plus cached Cohere vectors (replay).
1. **MMR from scratch** (NumPy, about 20 lines) on hand toys:
   - assert λ = 1 equals top-k under (−score, chunk_id);
   - the max-vs-mean toy (own numbers, same shape as AIQ test 6);
   - the copy-wins inequality on a 3-vector example.
2. **Threshold dedup and per-page cap**, with unit tests.
3. **Dartboard re-implementation** (cells 19, 21, 23 logic, both distance scales):
   - the σ-limit toy;
   - the 5× pool `[A, B, A]` reproduction, and the pool-size fix (factor 4 for k = 3);
   - a 3-line static check that cell 25's keyword is wrong (`inspect.signature` on a stub; nothing upstream is run).
4. **Corpus D census** on the PyMuPDF snapshot with the C2 chunker (97 chunks): cosine of all cross-page pairs with MiniLM and with the cached Cohere vectors; histograms; the top-10 pairs; assert that p.10/p.23 is among them. Check `‖v‖ = 1` for both embedders.
5. **Per-item traces** for D-002, D-003, D-007 and a smart-grid question: pool, selection order, marginal terms per step, at λ ∈ {1, 0.9, 0.7, 0.5}, plus threshold τ and Dartboard σ.
6. **Metrics:**
   - CE@4, Group-Recall@4, α-nDCG@4 (NumPy; cross-checked against `pyndeval` only if installed);
   - MRR@10 with `k_select = 10`;
   - redundant-evidence rate, mean pairwise cosine, distinct pages, `dup_frac`, adjacent-pair evictions.
7. **Headroom:** the eligible-item count on dev (once M1 exists), listed by qid.
8. **Plotly:** the λ curve and the σ curve.
9. **The lexical proxy** (this session's script) side by side, so Yash sees how lexical and dense redundancy differ.

- **API calls:** none (Cohere vectors only from the C3 cache).
- **Runtime:** under 1 minute on CPU (97 vectors, pools of 20).

### 8. Apply-it tool plan and real-world checklist

`study/tools/diversity_check.py`: "Does MY retriever waste top-k slots on repeats, and would diversity help MY questions or hurt them?"
- **Inputs:**
  - `--docs`, `--questions q.jsonl` (`q`, `expect` quotes or groups, optional `category`);
  - `--embedder minilm|cohere` (Cohere through the cache);
  - `--k 4 --pool 20 --k-select 10`;
  - `--lambdas 1,0.9,0.7,0.5`, `--tau auto|0.9`, `--sigma auto|…`;
  - `--relevance cosine|file:scores.jsonl` (a reranker's scores, normalised);
  - `--group-by page|section`; `--report out.md`.
- **Outputs (Markdown plus Plotly HTML):**
  - the near-duplicate census;
  - per-question plain vs selected lists with marginal terms;
  - the eligible-item count;
  - gold-aware and manipulation metrics per arm;
  - an eviction list (questions where an arm dropped an expected chunk);
  - the checklist and a recommendation.

**Real-world checklist (12 checks):**

| # | Check | Auto / manual |
|---|---|---|
| D1 | Exact duplicates removed first (hash count reported) | auto |
| D2 | Pool ≥ m(k−1)+1, where m is the largest duplicate cluster after dedup | auto |
| D3 | Relevance and redundancy on stated, comparable scales; vectors are unit length | auto |
| D4 | λ = 1 reproduces the baseline top-k exactly (same tie rule) | auto |
| D5 | Eligible-item count ≥ 5; otherwise "diversity cannot show a benefit on this set" | auto |
| D6 | Gold-aware gain (CE@k / Group-Recall@k on eligible items) reported, not only the pairwise cosine | auto |
| D7 | Single-fact guard (MRR, Hit@k) reported with n; evicted gold listed | auto |
| D8 | Adjacent-pair evictions counted (span cut at a boundary) | auto |
| D9 | Near-duplicate-but-different pairs read by a person (do the twins hold different facts?) | manual (read the top-10 pairs) |
| D10 | λ or σ chosen before seeing test; the sweep labelled exploratory | auto (flag) + manual |
| D11 | Cheap baselines (threshold, per-section cap) compared before MMR or Dartboard | auto |
| D12 | p95 latency of the selector stage reported | auto |

**Recommendation logic:**
- D1 or D2 fails → "fix dedup or the pool size first".
- D5 fails → "not indicated: keep plain top-k; add multi-fact questions if you expect them".
- The threshold arm matches MMR → "use the threshold (simpler, one parameter with a meaning)".
- MMR gains on eligible items with no single-fact loss → "adopt at the pre-registered λ; confirm once on held-out questions".
- Gains with D7 evictions → "use only on multi-fact query types (route, A1) or cap per section".

### 9. LLMOps notebook plan

`study/llmops/notebooks/R4_diversity_ops.ipynb` (foundation §12 row "5 · R1–R5"; a concept with no LLM in the selector).
- **Framework build:**
  - `langchain-core` `InMemoryVectorStore` filled with the C3 vectors through `CachedEmbeddings`. Its `max_marginal_relevance_search_by_vector` is the **framework MMR** (mechanism steps 2 and 4).
  - Our `select_diverse(pool, rel, V, cfg)` is wrapped as a `BaseRetriever` (mechanism steps 4–8), because the framework cannot take reranker scores as relevance.
  - A `RunnableLambda` chain: champion retriever (R1/R3) → our selector → context.
  - **Defaults the lesson warns about** ([R4-S4]):
    - `k=4, fetch_k=20, lambda_mult=0.5` (0.5 is our most diverse arm);
    - cosine recomputed whatever the store's metric;
    - tied scores ordered by descending index in `InMemoryVectorStore`;
    - the query vector cast to float32;
    - MMR returns `Document`s without scores;
    - `utils.maximal_marginal_relevance` is a private API;
    - VAI L24's `fetch_k=20` call with the default λ, mislabelled "hybrid".
- **External calls (all cached; replay runs with no key):**

  | Call | Count | Notes |
  |---|---|---|
  | Cohere `embed-v4.0` documents | **0** | C3 cache (97 chunks) |
  | Cohere `embed-v4.0` queries | 0–1 batched call (≤ 96 dev/test questions) | Usually already cached from v0.1 |
  | Cross-encoder (R3 champion) | local, 0 API | Its scores are read from R3's stored traces, or recomputed locally and content-cached |
  | Cohere rerank | 0 new | Only if R3 adopted it; then served from R3's cache |
  | Groq `openai/gpt-oss-20b` generation | ≈ 16 dev items × 2 arms (champion is cached; the chosen arm is new) + ≈ 20 test items ≈ **36 calls ≈ $0.01** | Only if the headroom gate passes; ≈ 72k tokens ≈ ⅓ of a day's free-tier tokens (plan UNVERIFIED) |
  | Claude | 0 | No high-volume LLM step |
  | Judge | **0** (D-10) | Stored traces feed the end batch |

- **Tracing:**
  - One `diversify` span (OpenInference `RERANKER` kind) per (arm, qid). It carries: the input pool (ids, champion scores, normalised relevance), `lambda` or `sigma` or `tau`, `k_select`, and the selection order. Per step it records the chosen id, rel, max-sim, **which selected id caused the max**, the objective, and the runner-up and its margin.
  - Each span also carries the final ids and the manipulation metrics.
  - Local JSONL viewed in Phoenix by default. LangSmith only for Corpus D, inside `tracing_context(enabled=True)` after `privacy.assert_corpus_is("D")`; about 100–150 traces per run.
- **Dataset and evaluators:**
  - the M1 golden set (dev selects, test once), plus a derived `r4_eligible` slice, stored with its rule version;
  - Tier-1 evaluators: CE@4, Group-Recall@4, α-nDCG@4, MRR@10, Hit@4, redundant-evidence rate, adjacent evictions, mean pairwise cosine, distinct pages, `dup_frac`;
  - generation only for the chosen arm (EM/F1 on short answers, citation page-hit, abstention string) plus about 10 read answers;
  - `langsmith.evaluate(..., upload_results=False)` shown once.
- **Experiment against the previous version:**
  - champion (v2.1, or v2.2 if adopted) vs the pre-registered MMR λ = 0.7 and the threshold arm, on identical comparison keys;
  - λ ∈ {0.5, 0.9} and Dartboard σ as an exploratory grid under `experiments/E0xx_v2.3_diversity/grid/`;
  - M4's `compare_runs.py`; "not indicated" is a valid recorded outcome when the gate fails.
- **Cost, latency and tokens:**
  - selector p50/p95 (expected microseconds; reported per stage next to the reranker);
  - realized context tokens per arm (diverse chunks can be longer);
  - cost if called vs paid (0 on replay).
- **Prompt and config versioning:**
  - the `diversify:` block (R4-E10) hashed into `config_hash`;
  - the eligible-slice rule version;
  - `answer_v1` unchanged.
- **Monitoring and feedback:**
  - **T1 regression tests:**
    - λ = 1 equals the champion's top-k, id for id;
    - parity with `maximal_marginal_relevance` on 50 seeded tie-free pools;
    - Dartboard at σ = 0.05 equals the KNN order on the toy;
    - the copy-removal test (hash dedup before MMR);
    - the eligible-slice count is stable for a dataset hash.
  - **Alerts:** an empty or shrinking eligible slice after a dataset change; the evicted-gold count > 0 on the near-duplicate tag; a pool smaller than `m(k−1)+1`.
  - Evicted-gold items go to the M5 log and become regression items (`ci-cd-evals`, `error-analysis`).
- **Place in the lifecycle:**
  - Analyze: the redundancy failure bucket from v0.1 traces (`error-analysis`, `trace-data-analysis`).
  - Measure: the headroom gate and the arms (`rag-evaluation`, `code-based-evaluators`).
  - Improve: adopt, keep, or "not indicated" (`improving-llm-agents`).
  - dev → CI: the T1 tests (`ci-cd-evals`).
  - Tracing: `llm-observability`.
  - Framing: `evals-foundations`.
  - The skills were applied as described in LLMOPS_FOUNDATION; the skill files are not present in this session.

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| MMR, threshold dedup, Dartboard, metrics | own code (NumPy) | — | — | yes | — | — | yes |
| Arrays | `numpy` | 2.5.3 | yes | yes | — | BSD-3 | yes |
| `logsumexp` for Dartboard | `scipy.special` | 1.18.1 (per phase_04 §10) | yes (Yash's env) | yes | — | BSD-3 | yes; a NumPy one-liner also works |
| Local embedder | `sentence-transformers/all-MiniLM-L6-v2` via `sentence-transformers` 6.1.0 | per phase_04 | yes | yes | — | Apache-2.0 | yes (D-03 fallback) |
| Default embedder | Cohere `embed-v4.0` via `cohere` | 7.2.0 | yes | replay | 0–1 calls | MIT (SDK) | yes (D-03) |
| Relevance source after R3 | `cross-encoder/ms-marco-MiniLM-L-6-v2` (R3's model) | R3 pin | yes (sentence-transformers) | yes | — | Apache-2.0 | yes |
| Generation (chosen arm only) | Groq `openai/gpt-oss-20b`, `reasoning_effort=low` | from `.env` | SDK yes | replay | ≈ 36 calls ≈ $0.01 | — | yes (D-04) |
| Claude | not needed (no LLM in the selector) | — | no | — | 0 | — | n/a |
| Plots | `plotly` | locked | yes | yes | — | MIT | yes |
| α-nDCG cross-check (optional) | `ir-measures` + `pyndeval` | 0.4.3 + **0.0.6** (0.0.7/0.0.8 are from 2026-10-16, too new) | no | yes | — | Apache-2.0 + MIT | yes (dev group, optional) |
| Framework MMR, adapter base | `langchain-core` (`InMemoryVectorStore`, `vectorstores.utils.maximal_marginal_relevance`) | 1.6.6 | no | yes | — | MIT | yes (LLMOps only) |
| LangGraph | not needed (a linear selector) | — | — | — | — | MIT | n/a |
| Provider integrations | `langchain-cohere` / `langchain-groq` **not used** (pin conflicts) | — | no | — | — | MIT | adapters (foundation §9.3) |
| Hosted tracing | `langsmith` | 0.14.4 | no | no | free plan, ≈ 150 traces per run | MIT (SDK) | yes, Corpus D only |
| Local tracing | `arize-phoenix-otel` 0.17.2 + `uvx arize-phoenix@20.19.0 serve` | — | no | yes | — | Apache-2.0 / ELv2 | yes |
| Reading only | `EmergenceAI/dartboard` (official code) | `main`, 2026-10-17 | no | — | — | **no licence file found** | read only; do not copy |

- **Install lines (do not run):**
  - `uv add --group llmops langchain-core==1.6.6 langsmith==0.14.4 arize-phoenix-otel==0.17.2` (foundation pins);
  - optional: `uv add --group dev ir-measures==0.4.3 pyndeval==0.0.6`.
- **Keys:** none for the lesson and verify notebook. `COHERE_API_KEY` only if query vectors are missing from the cache. `GROQ_API_KEY` for the chosen arm's answers. `LANGSMITH_API_KEY` is optional.

### 11. Open questions for Yash (preferences only)

1. How deep should the Dartboard part go: the full log-space derivation and the σ study (**Full mode only**), or a one-page "read the code" section?
2. Do AIQ challenge 17's MMR tests as a blank-file exercise (coding-independence evidence) after the lesson? **yes** / no.

---

## Concept R5: Hierarchical retrieval: hierarchical indices and RAPTOR (S, project v8 optional)

R5 adds a second, coarser layer to the index: summaries of larger units. The search then works coarse-to-fine, or over every layer at once. There are two designs, and the course must keep them apart:
- **Two-level hierarchical index (book Ch14):** one summary per logical unit (section or chapter), each pointing to its chunks. Search the summaries first, then search only the chunks of the chosen units.
- **RAPTOR (repo only; Sarthi et al. 2024):** cluster the chunks by embedding, summarise each cluster, and repeat on the summaries to build a tree. Then retrieve over all layers at once (the "collapsed tree") or walk down the tree.

Both add **index-time LLM calls** and **generated text** to the index, so R5 inherits Phase 4's open problem: index units whose text is not a span of the source (phase_04 gap 2). R5 is an S concept with an optional project version (v8), which competes with S1 Graph RAG. It is only worth running when M5 shows that section-level or global questions fail. On Corpus D that bucket does not exist yet. So this audit covers the mechanism, the scoring rule for summary units, the cost on Corpus D, and a gate-aware experiment design.

**No course files exist for R5.** There is no `concepts/R5_*`, `study/reading/R5_*`, `study/questions/R5_questions.md`, `labs/R5_*` or `sources/verification/R5/` (checked 2026-10-17). VAI has nothing on hierarchical retrieval. The tracker row reads `R5, not_started, not_planned`.

### 1. Sources checked

**Book (not present; per 02 and 04 §3 Ch14; not re-opened, UNVERIFIED):**
- 02 R5 card: Ch14 p.4–8/13 (the steps and two-stage retrieval) and p.8–9/13 (why summaries).
- 04 §3 Ch14: sketch on p.7/13; summaries as the first pass on p.8–9/13; the role of metadata on p.9–10/13. Its step table runs: summarise each logical section and attach metadata (p.4–5/13) → chunk each section and tag the chunks with the parent id (p.5–6/13) → two vector stores (p.6/13) → top-K summaries → section ids → filtered detail search, top-N (p.7/13) → generate (p.7/13).
- 02 L1267 assigns the metadata role (p.9–10/13) to C3/R2. 04 §2.4 cites p.4–10/13 for R5. These ranges overlap and do not contradict each other. The difference is only where p.9–10 is taught (R5-E7 notes it).
- RAPTOR is not in the book (02, 04).

**Repo (verified: downloaded at `009adba` into the scratchpad, read with `python3 -I`, cells 0-based, nothing run):**
- `all_rag_techniques/hierarchical_indices.ipynb` (19 cells):
  - cell 11: `encode_pdf_hierarchical`. PyPDFLoader pages are the "sections". `load_summarize_chain(chain_type="map_reduce")` is called with `gpt-4o-mini`, `max_tokens=4000`, in batches of 5 with a 1 s sleep. Each call is wrapped in `retry_with_exponential_backoff(summary_chain.ainvoke([doc]))`. Chunks are split 1000/200 with `chunk_id: i` (a position). Embeddings are `OpenAIEmbeddings()` (model not pinned). Both FAISS stores are built inside the same retry wrapper.
  - cell 13: if `../vector_stores/summary_store` and `detailed_store` exist, it loads them with `FAISS.load_local(..., allow_dangerous_deserialization=True)`; otherwise it builds and saves them. The folder name carries no corpus, chunker or model identity (C3 H.2 already teaches this stale-index trap).
  - cell 15: `retrieve_hierarchical(k_summaries=3, k_chunks=5)` runs one `similarity_search(query, k=5, filter=lambda m: m["page"] == page)` per selected summary. It returns the concatenated lists, with no deduplication, no global ranking and no fallback.
  - cell 17: one demo query ("What is the greenhouse effect?") and no generation.
- `helper_functions.py` L294–L321: `retry_with_exponential_backoff(coroutine, ...)` takes a coroutine **object** and runs `await coroutine` inside the loop (L311). A second attempt re-awaits the same object, which Python refuses with `RuntimeError`, so the "backoff" can never succeed. It also catches only `openai.RateLimitError` (import at L7), so with any other provider it never retries at all. This confirms 08 RB3.
- `all_rag_techniques_runnable_scripts/hierarchical_indices.py`: L22–L68 encode, L71–L82 retrieve, L85–L107 the class with the same load-if-exists pattern (L94–L101). L8 imports `helper_functions` before L10 fixes `sys.path` (04 is right). `is_string=True` builds documents without a `page` key (L31–L34), and L42 then reads `doc.metadata["page"]`, which raises `KeyError` (confirms RB19).
- `all_rag_techniques/raptor.ipynb` (35 cells):
  - cell 9: `perform_clustering` = `GaussianMixture(n_components=n_clusters, random_state=42).fit_predict(...)` on the **raw** embeddings. That is a hard assignment, with no reduction and no BIC. `summarize_texts` formats a Python **list** into the prompt (`{"text": texts}`) and returns `chain.invoke(...)`, which is an `AIMessage`, not the `str` its type hint promises.
  - cell 11: `build_raptor_tree(texts, max_levels=3)`. Level-0 metadata is `{"level": 0, "origin": "original", "parent_id": None}`, with **no `id` key**. So every level-1 `child_ids` list is `[None, …]`. `n_clusters = min(10, len // 2)`. From level 2 on, the inputs are `AIMessage` objects (see §5).
  - cell 13: `build_vectorstore` stores `str(text)` for every node, collects the precomputed embeddings and **never uses them**: `FAISS.from_documents(documents, embeddings)` re-embeds the `str(...)` texts.
  - cell 15: `tree_traversal_retrieval` is defined but never called, and it would fail (§4 R5-E2).
  - cell 17: `ContextualCompressionRetriever` over `vectorstore.as_retriever()` (k = 4) with `LLMChainExtractor` and a custom prompt.
  - cell 19: `hierarchical_retrieval` runs one level-filtered search per level, from `max_level` down to 0. It then appends `" AND id:(summary_1_3 OR …)"` to the **query string** instead of filtering by id.
  - cell 21: answers with `LLMChain(...).run`. Cell 27: the leaves are the 33 PyPDFLoader **pages**. Cell 33: `max_level = 3`.
- `all_rag_techniques_runnable_scripts/raptor.py`: L55–L63 `summarize_texts` (same `AIMessage` return), L94 `str(text)`, L127–L177 the tree build (the same bugs as cell 11), L179–L205 `run()`. **The script differs from the notebook**: `run()` uses the flat compression retriever over all levels (closer to a collapsed tree, but k = 4 nodes with no token budget), and its `k` argument is unused.

**Existing course files:**
- 02 R5 card (L722–L735), §4 gates, §9 (L1394–L1416), L1267, L1299, R2 card L683;
- 03 registry row L438, edges L478–L480, R5 row L535, §4.6 (L712–L728), §5 row 12;
- 04 §2.4 R5 row L178, §3 Ch14 (L642–L666), §4 raptor row L923, DV-30 L1019, Source C #40;
- 06 §4.1 diagram, v8 card (L716–L727), §6.2 categories (L900–L913), §6.7 seeds;
- 08 Part 1 Q3/Q8 rows 24 and 35, RB3, RB11, RB19, Part 4 (D-03, D-07, D-08, D-10, D-32);
- 07 L517 (parent–child row);
- `concepts/C3_embedding_indexing.md` H.2;
- phase_03 M2 and M5 (gap 17, M5-E3);
- phase_04 summary and phase-level notes (IndexUnit, heading tree: 21 chapters, 68 sections; Corpus D ≈ 13K tokens);
- `LLMOPS_FOUNDATION.md` §1.2, §2, §3.3, §6, §9, §12;
- the external review §7 row 6;
- the tracker and the misconception log (MC-003, MC-005).

**AE book:** not needed beyond what phase_03 already uses (M4 statistics, M5 error analysis).

**Interview repo (AIQ @ `e080df2`, MIT, "Copyright (c) 2026 Om"; verified):** `04-rag-and-retrieval/questions.md` has **no RAPTOR item**. The relevant items are:
- Q39 (GraphRAG; global questions; "Why can't plain top-k retrieval ever answer 'summarise the main themes'?");
- Q23 (pre- vs post-filtering, starvation);
- Q5 ("retrieve small, generate big");
- Q50 (long context vs RAG);
- Q29 (keeping an index fresh).

**External (numbered in the R5 list at the end; arXiv, OpenReview, Hugging Face and blogs were blocked, so the paper was not opened):**
- [R5-S1] RAPTOR paper (search-checked only);
- [R5-S2] the official RAPTOR repo source (verified);
- [R5-S3] the LlamaIndex RAPTOR pack (verified);
- [R5-S4] `langchain-classic` 1.0.8 retrievers and summarise chains (verified);
- [R5-S5] `langchain-core` 1.6.6 (verified);
- [R5-S6] `langchain-community` 0.4.2 FAISS (verified);
- [R5-S7] scikit-learn 1.9.1 `GaussianMixture` (verified);
- [R5-S8] umap-learn 0.5.12 plus the PyPI metadata of its dependency stack (verified);
- [R5-S9] the HippoRAG 2 README figure (verified; a competitor's figure);
- [R5-S10] three 2025–2026 re-evaluation tables (search-checked only);
- [R5-S11] GraphRAG "From Local to Global" (not opened, UNVERIFIED).

**Derived arithmetic (derived, not measured):**
- Corpus D is 72,593 characters, about 13.0K cl100k tokens (phase_04, 5.57 chars/token).
- Mean chapter ≈ 620 tokens (13.0K / 21). Mean section ≈ 190 tokens (13.0K / 68).
- v0 = 97 chunks over 33 pages, ≈ 2.9 chunks per page, mean ≈ 750 characters ≈ 135 tokens.

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class (core / bridge / next) | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Why flat top-k fails on "whole-section" or "main themes" questions (evidence spread over many chunks; no chunk states the summary) | 02 R5 Failure; 06 v8; AIQ Q39 | **missing** (no lesson) | R5 | no | core | Open with a Corpus D chapter question whose evidence sits in 6+ chunks; show CE@4 = 0 for v0 |
| 2 | Two-level index: unit summaries → filtered chunk search (book Ch14 steps) | 02 outcome 1; Ch14 p.4–8/13 (per 02/04) | **missing** | R5 | no | core | The book's pipeline as 5 steps, plus the 3 things the repo leaves out (fallback, global top-N, generation) |
| 3 | **Routing ceiling**: two-stage CE ≤ P(every gold unit is among the top-K_s summaries) | Ch14 gap "wrong section"; 03 R5 row | **missing** | R5 | no | core | Formula plus a `route_recall@K_s` diagnostic. Cross-chapter questions are capped by it |
| 4 | Pre- vs post-filtering; FAISS `fetch_k=20` starvation | `hierarchical_indices` cell 15; 02 R2 card | R2 (not written) | R2 | no | bridge | One paragraph and a NumPy demo: the chunks returned per page under post-filtering vs a pre-filter mask (D-07 NumPy) |
| 5 | Choosing the summary unit: page vs section vs chapter; compression ratio = summary tokens / source tokens | 04 Ch14 step 1 "page = section" | **missing** | R5 (I2 owns the heading tree) | no | core | Corpus D: a section ≈ 190 tokens (≈ one v0 chunk), so its summary barely compresses; a chapter ≈ 620 tokens. Pages cut across headings |
| 6 | Heading tree (21 chapters, 68 sections; size rank + bold) | phase_04 I2 | I2 (planned) | I2 | no | bridge | Reuse I2's `section_path` and offsets. Never re-detect headings |
| 7 | Summarisation prompting: length cap, "key details", no outside facts, source labels | P7 (grounded prompting); 03 R5 row lists P7 | partial (P7 is about answers, not summaries) | R5 (P7 bridge) | no (P7 not started) | bridge | A prompt file with a token cap; "only facts stated in the text"; record `prompt_version` |
| 8 | **Summaries are generated text**: faithfulness, the hallucination rate, and the span invariant | phase_04 gap 2; 06 §2.3 | **missing** | R5 (I4/I6 share it) | no | core | `SummaryUnit`: `embed_text` = summary, evidence = none, `source_spans` = union of child spans. An auto number/entity check plus a hand sample |
| 9 | **Scoring summary hits**: never credit a summary with its source spans (the root would cover every question) | M2 CE@k; phase_04 gap 2 | **missing** | R5 (M2 scorer) | M2 exposed only | core | Rule: CE counts **leaf** text in the final context only. Report the summary token share separately. `scorer_version` option |
| 10 | Equal token budget across arms (summaries are dense; nodes have unequal lengths) | 06 §4.1 rule 2; M4 | I1 (planned) | I1 / M4 | no (MC-005 open) | bridge | Collapsed-tree selection by budget B (the paper's mode), not by k. Report realized tokens |
| 11 | Embedding geometry: high dimensions and few points; why reduce before a GMM | `raptor` cell 9 vs [R5-S2] | **missing** | R5 (P4 bridge) | no (P4 not started) | core | Parameter count of a full-covariance GMM: d = 1,536 → 1.18 M per component vs 97 points. After reduction to d = 10, it is 65 |
| 12 | PCA vs UMAP (linear vs neighbour-graph; determinism; weight) | [R5-S2] `cluster_utils.py` | **missing** | R5 | no | core | PCA by default (sklearn, already locked); UMAP as an optional arm. UMAP's `random_state=None` default and the seed/parallelism trade-off [R5-S8] |
| 13 | Gaussian mixtures, EM, soft membership P(j \| x) | RAPTOR clustering | **missing** | R5 | no | core | The formula; the threshold 0.1 means a node can join several clusters (at most 9) |
| 14 | Choosing k with BIC = −2 ln L̂ + p ln n | [R5-S2] L46–L57; [R5-S7] L959–L980 | **missing** | R5 | no | core | BIC curve for k = 1…49 on Corpus D leaves; show how the penalty term grows with p |
| 15 | Global → local clustering; re-clustering when a cluster exceeds the token cap; the stop rule (≤ dim + 1 nodes) | [R5-S2] | **missing** | R5 | no | core (Full for local) | Short: global then local. Full: the 3,500-token cap, the `n_neighbors = √(N−1)` rule, stopping at ≤ 11 nodes |
| 16 | Collapsed tree vs tree traversal | [R5-S1], [R5-S2] | **missing** | R5 | no | core | Side-by-side: one pool selected by budget, vs top-k per layer following children. The repo and the paper differ on budget and k (§5) |
| 17 | Parent/child links with multiple parents (soft clustering) | `raptor` cell 11 bug; [R5-S3] `parent_id` overwrite | **missing** | R5 | no | core | Store `children: list` and `parents: list`; test that every non-leaf has ≥ 1 child id and that no child id is `None` |
| 18 | Index-time cost: calls = Σ clusters per layer; tokens; Groq TPM/TPD; rebuild on corpus change | 02 outcome 3; 06 v8; LLMOPS §1.2 | **missing** | R5 (D2/D3 later) | no | core | The Corpus D cost table (§5). Rebuild: two-level is local, RAPTOR's clustering is global |
| 19 | Contextual headers inside chunks (I5) vs a separate summary level | 03 R5 row "Confusions" | I5 (planned) | I5 | no | bridge | One contrast box. A chapter-path header is a 0-call competitor to chapter routing |
| 20 | Reranking as the baseline champion; a cross-encoder scoring a summary vs a passage | 03 R5 ← R3 (lab-baseline edge) | R3 (not written) | R3 | no | bridge | Pre-register "rerank leaves only"; ms-marco models were trained on passages, not summaries (an assumption to check) |
| 21 | MMR / diversity also targets multi-span | 06 v2.3 | R4 (not written) | R4 | no | bridge | R5 runs on top of the v2 champion, including R4 if it was adopted; name the overlap |
| 22 | Parent–child "retrieve small, return big" (`ParentDocumentRetriever`, `MultiVectorRetriever`) | 07 L517; AIQ Q5 | I6 / X1 (planned) | X1 / I6 | no | next | One line: it expands **down → up** without summaries. R5 routes **up → down** |
| 23 | Graph RAG global search (community summaries) | 06 v8; 03 §4.6; AIQ Q39 | S1 (later) | S1 | no | next | One contrast row: clusters of chunks vs communities of entities |
| 24 | Long-context baseline: Corpus D (≈ 13K tokens) fits in one prompt | AIQ Q2, Q50 | **missing** | R5 (K1 later) | no | core (Full) | A strong baseline for global questions. Blocked on Groq's free tier (13K > 8K TPM per request); possible with Haiku 5.5 |
| 25 | Multi-hop (bridge entity) ≠ multi-span/global | 02 R5 Pre vs 06 v8 gate | **missing** (the two files disagree) | M1 / R5 | no | core | RAPTOR targets thematic and multi-part questions. Bridge-entity chains belong to Q1 decomposition and S1 (R5-E4) |
| 26 | Index persistence and identity (pickle, load-if-exists) | `hierarchical_indices` cell 13 | C3 H.2 (written, not studied) | C3 / D3 | no | bridge | A tree manifest: leaf `params_hash`, `embed_hash`, reduction + seed, prompt version, model. JSON only, no pickle |
| 27 | Summary hallucination evidence and its limits | [R5-S1] (4% of 150 nodes, search-checked) | **missing** | R5 | no | core | The number with its label. Ours is measured on a hand sample |
| 28 | Whether the gains survive strong baselines | [R5-S9], [R5-S10] | **missing** | R5 | no | core (Full) | HippoRAG 2's figure: RAPTOR below plain NV-Embed-v2 on all three task groups. Re-evaluations are mixed |

### 3. Quiz coverage

No question file exists. Needed titles:
- **R-01** What are the two R5 designs, and what does each put in the index (fixed units vs clusters; two levels vs a tree)?
- **R-02** Why can't a retrieved summary count as evidence for CE@k? What would happen to the root node if it did?
- **R-03** What do UMAP/PCA, GMM, BIC and the 0.1 threshold each do in RAPTOR's clustering step?
- **R-04** Collapsed tree vs tree traversal: how does each select nodes, and which needs a token budget?
- **R-05** Name three ways `raptor.ipynb` differs from the paper, and two bugs that corrupt its tree.
- **A-01** Given summary similarities for 5 chapters and a question whose gold lies in chapters 3 and 7, compute `route_recall@3`. Is CE capped?
- **A-02** Compute calls and tokens for chapter summaries on Corpus D (21 × ≈ 620 tokens), and the minimum minutes at 8K TPM. (★ ≈ 21 calls, ≈ 22–25K tokens, ≥ 3 min.)
- **A-03** Count the parameters of a full-covariance GMM with k = 5 at d = 1,536 and at d = 10. Why does BIC on raw embeddings pick k = 1?
- **A-04** Given GMM probabilities for 4 nodes over 3 clusters and threshold 0.1, list the cluster memberships and the parents of each node.
- **A-05** Given node token lengths and similarities, select the collapsed-tree context at B = 400 with "stop" vs "skip".
- **T-01** Your corpus is 40 short FAQ pages. Would you build RAPTOR? Which baseline beats it more cheaply? (Key: flat or long-context; there are no global questions; the cost.)
- **T-02** You edit one page of Corpus D. How many summary calls does a two-level rebuild need, and how many does RAPTOR? (Key: one chapter vs every cluster whose membership changed; seed it; the content cache.)
- **T-03** A product manager wants "main themes of all incident reports". RAPTOR or GraphRAG? (Key: question shape; entity richness; cost; evaluation without span gold.)
- **Interview** (derived from AIQ 04 Q39 and Q23, MIT): "Why can't top-k retrieval answer 'summarise the main themes', and how would you build and *evaluate* a summary layer that can?"

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| R5-E1 | 02 R5 card "cell 13 indexes summaries as an `AIMessage` repr"; 03 R5 row; 08 RB11 | The cause is upstream of cell 13. Cell 9's `summarize_texts` returns an `AIMessage`. Cell 11 then feeds those objects into the **next level's prompt** (formatted as a Python list of reprs), so level-2 and level-3 summaries summarise message reprs. Cell 13 stores `str(AIMessage)`: pydantic's `content='…' additional_kwargs=… response_metadata=…`, since `BaseMessage` defines no `__str__` ([R5-S5] `messages/base.py`, `serializable.py` L220–L225). It also **throws away the computed embeddings and re-embeds** the repr strings | Cite cells 9, 11 and 13 with three effects: reprs indexed, reprs summarised, embeddings recomputed |
| R5-E2 | 02 card "broken parent links"; 04 L923 "traversal never called" | Precisely: level-0 metadata has no `id`, so **every level-1 `child_ids` is `[None, …]`**; level ≥ 2 links are valid (cell 11). Cell 15 would also fail if called: `similarity_search_by_vector_with_relevance_scores` does not exist on FAISS, and `InMemoryDocstore` has no `.values()` ([R5-S6], langchain-community 0.4.2). Cell 19 never filters by id: it appends `" AND id:(…)"` to the query **text**, which only changes the query embedding. Cell 33's `max_level = 3` searches a level that was never stored, because the 2 level-3 summaries are generated and dropped (RB11). 02's cell list (9, 11, 13, 19) misses 15, 17 and 33 | Add cells 15, 17 and 33 to 02's card. Describe cell 19 as "three independent level-filtered searches with a polluted query" |
| R5-E3 | 03 §4.6 RAPTOR row; 04 L923 | "About 17 calls" is an **upper bound** (10 + 5 + 2, if every GMM component is non-empty), and 2 of those calls are wasted on the dropped top level. Query time: up to 4 compressions per level over 3 non-empty levels (12) + 1 answer, not "per level" in general. The script (`raptor.py` L179–L205) has a different query path (flat k = 4 + compression) from the notebook | State "≤ 17 build calls, 2 discarded; ≤ 13 query calls; the notebook and script differ" |
| R5-E4 | 06 v8 card gate ("multi-hop or global … ≥ 8 such items") vs 06 §6.2 and 02 R5 Pre ("multi-span/global") | Three problems. (1) §6.2 has **no global category**, and multi-hop has a minimum of 4, so the ≥ 8 gate is unreachable with the planned set. This extends M5-E3 and the external review's §7 row 6. (2) 02 says multi-span/global, 06 says multi-hop/global. RAPTOR's evidence is on thematic, multi-part reading comprehension [R5-S1], not on bridge-entity chains, which belong to Q1 decomposition and S1. (3) At ≈ 30% dev, 8 items leave ≈ 2–3 for selection | Define R5's target bucket as **chapter-scope multi-span + global/thematic**. Route multi-hop to Q1/S1. Require ≥ 8 target items **per split** (dev and test) in a new dataset version before any v8 run |
| R5-E5 | 04 §3 Ch14 step 4–6 ("k_chunks=5 *per page*, up to 15 chunks"); 03 §4.6 | On Corpus D a page holds ≈ 2.9 chunks (97/33). The FAISS callable filter is a **post-filter over the global top `fetch_k=20`** (langchain-community 0.4.2 `faiss.py` L387–L445). So "up to 15" cannot happen: at most the page's chunks that land in the global top 20, often fewer | State the fetch_k starvation and the page-size cap. The verify notebook measures returned chunks per page |
| R5-E6 | 04 §3 Ch14 step 1 "Implemented (page = section)" | It overstates. Pages are not sections on Corpus D (33 pages vs 21 chapters / 68 sections, and headings that repeat across chapters, phase_04 I2). `map_reduce` makes **2 LLM calls per page** (map + reduce on a one-document list; langchain-classic 1.0.8 `map_reduce.py` L224–L250 and `reduce.py`) with LangChain's built-in default prompt, so 66 calls on Corpus D. The book's "logical section" is never built | "Diverges: page used as section; 2 calls per page with a hidden default prompt" |
| R5-E7 | 02 R5 Book line (p.4–8/13, p.8–9/13) vs 04 §2.4 (p.4–10/13) and 02 L1267 | Not a contradiction: 02 moves p.9–10/13 (metadata) to C3/R2. But R5's lesson needs the metadata link (03 L480 calls R5 ← R2 conceptual) | Keep both. The R5 lesson cites p.9–10/13 as a bridge to R2 (book not re-opened, UNVERIFIED) |
| R5-E8 | 06 v8 card "Hypothesis: raises correctness on the multi-hop/global items" | Answer correctness on global items needs a judge, which D-10 defers. Global items also have many evidence groups, so plain CE@4 is ≈ 0 for every arm. The card names no retrieval metric that can move | Primary retrieval metric: Group-Recall and CE on **leaf** text at equal budget B. Answer side: human labels on the target items until the end batch |
| R5-E9 | 03 registry row L438 (`requires_all` R2, R3, M5) vs 03 row L535 ("R2, R3, M5, P7 (summarization)") | P7 is listed in the table, not in the registry. No concept owns summarisation prompting | Leave the registry. Teach summary prompting as a bridge inside R5 (gap 7) |
| R5-E10 | `LLMOPS_FOUNDATION.md` §9.2 defaults table | Missing rows that R5's framework build hits. FAISS `filter=` post-filters over `fetch_k=20`. `InMemoryVectorStore` pre-filters exactly, but its filter receives a **`Document`**, not a metadata dict ([R5-S5] `in_memory.py` L291–L310), so FAISS-style lambdas break. `load_summarize_chain("map_reduce")` makes 2 calls per document with a hidden default prompt. phase_04 already reported `MultiVectorRetriever` | Add three rows |

### 5. What the research says

**[R5-S1] Sarthi, Abdullah, Tuli, Khanna, Goldie & Manning, "RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval", ICLR 2024, arXiv 2401.18059.** arXiv, OpenReview and the mirrors were blocked here, so **every paper number is UNVERIFIED**. Labels: "search-checked" where a search snippet showed it; "from memory" where only prior knowledge supports it.
- *Study:*
  - Leaves are ≈ 100-token chunks, embedded with SBERT.
  - The chunks are soft-clustered with UMAP + GMM, with k chosen by BIC, global then local.
  - Each cluster is summarised by gpt-3.5-turbo, and the process repeats.
  - Retrieval is either the collapsed tree (all nodes in one pool, filled to a token budget) or tree traversal (top-k per layer, following children).
  - Datasets: NarrativeQA, QASPER and QuALITY, with UnifiedQA, GPT-3 and GPT-4 as readers and SBERT, BM25 and DPR as retrievers, with and without the tree (search-checked).
- *Result:*
  - The authors report state-of-the-art QuALITY accuracy with GPT-4, especially on QuALITY-HARD (search-checked). The commonly quoted figures (QuALITY 82.6%, QASPER F1 55.7, NarrativeQA METEOR 19.1) are **from memory, UNVERIFIED**.
  - Collapsed tree beat traversal in their comparison (search summaries; the budget of ≈ 2,000 tokens is from memory).
  - Hallucination: **6 of 150 annotated summary nodes (4%)** contained some hallucination (search-checked). Whether it hurt QA is UNVERIFIED in this session.
  - A clustering-vs-contiguous-grouping ablation showed only a small gain for clustering (from memory, UNVERIFIED).
- *Limits:*
  - The gains are measured on long single narratives and papers with LLM readers. Most are reader-level, not retrieval-level.
  - Comparisons are at a fixed budget against the authors' own baselines.
  - There is no cost-normalised comparison against long-context reading.
- *For the project:*
  - The mechanism to teach is the paper's, not the notebook's.
  - Compare at an **equal token budget**.
  - Run the "structure tree" (chapters) against the "cluster tree". If contiguous grouping is nearly as good, Corpus D's heading tree is the cheaper first arm.
  - Measure summary faithfulness ourselves.

**[R5-S2] Official repo `parthsarthi03/raptor` @ `7da1d48`** (MIT, "Copyright (c) Parth Sarthi"; source read via raw.githubusercontent.com; verified).
- *Defaults (`cluster_utils.py`):*
  - `reduction_dimension=10`, `threshold=0.1`, `max_length_in_cluster=3500` cl100k tokens (L132–L141);
  - global UMAP `n_neighbors = int(√(N−1))`, `metric="cosine"`, dim `min(10, N−2)` (L23–L34, L72);
  - local UMAP `n_neighbors=10` (L37–L43); local clustering is skipped when a global cluster has ≤ dim + 1 members (L93–L95);
  - BIC search over k = 1…min(50, N)−1 (L46–L57);
  - soft labels = every cluster with P > threshold (L60–L66);
  - a cluster over the token cap is re-clustered recursively (L171–L181), but the recursion drops the caller's `threshold` and `reduction_dimension` (L178–L180 pass only 3 arguments).
- *Not reproducible:* UMAP gets **no `random_state`**; `RANDOM_SEED = 224` seeds only Python's `random` (L18–L20).
- *Tree:*
  - `cluster_tree_builder.py` stops when a layer has ≤ `reduction_dimension + 1` nodes (L95–L100);
  - one summary per cluster, single-node clusters included;
  - children are stored as index sets (L80–L82), so the links are correct;
  - `tree_builder.py` defaults (L42–L74): leaves 100 tokens, 5 layers, `top_k=5`, `selection_mode="top_k"`, `summarization_length=100`, summariser `gpt-3.5-turbo` with "Write a summary of the following, including as many key details as possible" (`SummarizationModels.py` L23–L40).
- *Leaves:* `utils.split_text` splits on `. ! ? \n` with `re.split`, **dropping the delimiters**, and rejoins with spaces (L22–L101). So even official leaves are not substrings of the source: the span invariant fails here too.
- *Retrieval:*
  - `retrieve(top_k=10, max_tokens=3500, collapse_tree=True)` (`RetrievalAugmentation.py`). The collapsed mode takes the **top 10 nodes** and stops at the first node that would cross 3,500 tokens (`tree_retriever.py` L158–L195), so the budget is often not reached.
  - Traversal mode (L197–L250) has a latent bug: `selection_mode="threshold"` keeps nodes whose **cosine distance** exceeds the threshold, which are the *least* similar (L226–L229 with `utils.py` L118–L135). The default `top_k` mode avoids it.
- *For the project:* use these as the documented defaults, set every one explicitly, seed the reduction, and never install the repo. Its `requirements.txt` pins `openai==1.3.3`, `torch` and `transformers==4.38.1`.

**[R5-S3] LlamaIndex `llama-index-packs-raptor` 0.4.2** (wheel read; MIT, "Copyright (c) Jerry Liu"; 2026-04-02; reading only).
- `clustering.py` is a port of [R5-S2], with **`max_length_in_cluster=10000`** (L122) instead of 3,500, `reduction_dimension=10` and `threshold=0.1`.
- `base.py` defaults: `tree_depth=3` (a fixed depth, not the paper's stop rule), `similarity_top_k=2`, `mode="collapsed"` (top-k nodes, **no token budget**), and summary prompt "Summarize the provided text, including as many key details as needed".
- Each child gets a **single** `metadata["parent_id"]`, overwritten in a loop (`insert`), so with soft clustering a node in two clusters keeps only the last parent.
- It requires `llama-index-llms-openai`, `umap-learn` and `numba` (PyPI `requires_dist`).
- *For the project:* a second reading of the same algorithm with different defaults. It shows that "RAPTOR" in a library can mean depth 3, top-2 and a 10K cap.

**[R5-S4] LangChain parent/child retrievers, `langchain-classic` 1.0.8** (wheel read; MIT; read-only per LLMOPS §11).
- `MultiVectorRetriever` (`multi_vector.py` L29–L113):
  - `id_key="doc_id"`: **one** parent id per vector;
  - `search_kwargs={}`, so the store's default k (4) applies;
  - it deduplicates parent ids in first-seen order, **drops scores**, and returns `docstore.mget(ids)`, which can be fewer than k.
  - This fits "summary vector → its whole section" and nothing else. It cannot express RAPTOR's many-child links or a filtered chunk search.
- `ParentDocumentRetriever` (`parent_document_retriever.py` L76–L113) splits each parent into children, gives every child the parent's uuid (`uuid4`, so ids are not stable across rebuilds), and returns parents. That is "small → big", the inverse of R5's routing.
- `ContextualCompressionRetriever` (L27–L46) passes `**kwargs` (for example `filter`) to the base retriever.
- `LLMChainExtractor`'s parser drops a document only when the model says exactly `NO_OUTPUT`. The repo's custom prompt never mentions it, so nothing is ever dropped.

**[R5-S5]/[R5-S6] Vector stores.**
- `langchain-core` 1.6.6 `InMemoryVectorStore._similarity_search_with_score_by_vector` (L291–L331) **pre-filters** the documents and then computes exact cosine. Its filter takes a `Document`.
- `langchain-community` 0.4.2 FAISS `similarity_search_with_score_by_vector` (L387–L445) searches `fetch_k=20` when a filter is given and **filters afterwards**. That is the starvation behind R5-E5.
- `load_local` refuses pickles unless `allow_dangerous_deserialization=True` (L1191–L1200), which is why cell 13 sets it.

**[R5-S7] scikit-learn 1.9.1 `GaussianMixture`** (verified; already in `uv.lock` as a dependency of sentence-transformers).
- Defaults (L768–L773): `covariance_type="full"`, `reg_covar=1e-6`, `max_iter=100`, `n_init=1`, `init_params="kmeans"`.
- `bic(X) = −2·score(X)·n + p·ln n` (L978–L980), with p = k·d(d+1)/2 + k·d + k − 1 for full covariance (L945–L957).
- *For the project:* at d = 1,536 (Cohere) one component has 1,181,952 parameters against 97 points. On raw embeddings, BIC's penalty forces k = 1, and `fit_predict` with a fixed k (the notebook) fits covariances held up only by `reg_covar`. Reducing to d = 10 gives 65 parameters per component. That is the real reason for the reduction step, and it applies to PCA just as well as to UMAP.

**[R5-S8] umap-learn 0.5.12** (2026-04-08; BSD; `umap_.py` at tag `release-0.5.12`, `cdb0eeb`; verified).
- Defaults: `n_neighbors=15`, `n_components=2`, `metric="euclidean"`, `min_dist=0.1`, `n_jobs=-1`, `random_state=None` (L1667–L1687).
- Setting `random_state` forces `n_jobs=1` with a warning (L1953).
- Dependencies (PyPI): `numba>=0.51.2` and `pynndescent`. numba 0.68.0 (2026-09-30) needs `llvmlite<0.51` and **`numpy<2.6`**. The project has numpy 2.5.3, so it fits, but numba then caps future numpy upgrades.
- Download size (cp312 win_amd64): llvmlite 41.9 MB + numba 2.8 MB + umap 0.1 MB + pynndescent 0.1 MB ≈ 45 MB. That is not "heavy" by the 500 MB rule, but numba JIT-compiles on first use (slow start; the duration is not measured).
- *For the project:* PCA (sklearn, deterministic with a fixed solver) is the default reduction. UMAP is an optional, seeded arm.

**[R5-S9] HippoRAG 2 README figure** (`OSU-NLP-Group/HippoRAG` @ `d5c8329`, `images/intro.png`; opened and read; a competitor's own figure, so treat it as one side of the argument).
- *Study:* bar charts for RAPTOR, GraphRAG, HippoRAG, NV-Embed-v2 (plain dense retrieval) and HippoRAG 2 over three task groups. The metric and the setup are not stated in the figure (UNVERIFIED: see the HippoRAG 2 paper).
- *Result:* RAPTOR 53.45 vs NV-Embed-v2 58.80 (factual memory), 21.40 vs 25.70 (sense-making) and 48.37 vs 58.81 (associativity). The README also says that RAPTOR, GraphRAG and LightRAG use significantly more offline indexing resources.
- *Limits:* the authors run their competitors' baselines themselves, with a 7B embedder. Configurations are not shown.
- *For the project:* this is the evidence that a **strong flat retriever can beat RAPTOR, even on sense-making**. R5 is compared against the v2 champion, never against v0 alone.

**[R5-S10] Re-evaluations, 2025–2026 (search-checked only, UNVERIFIED):**
- MultiCube-RAG (arXiv 2602.15898) and Quest-GNN (arXiv 2510.11541) tables reportedly put RAPTOR below NV-Embed-v2 on 2Wiki, and mixed on MuSiQue.
- SUBQRAG (arXiv 2510.07718) reportedly shows RAPTOR far below a plain MiniLM retriever when MiniLM is RAPTOR's own retriever.
- *For the project:* only the direction is used, never the numbers. The gains depend on the embedder and the baseline, and multi-hop QA is not RAPTOR's home ground (R5-E4).

**[R5-S11] Edge et al. 2024, "From Local to Global" (GraphRAG; arXiv 2404.16130; Source C #43; not opened, UNVERIFIED).**
- AIQ Q39 (verified) summarises the competing approach: entity graph → Leiden communities → community summaries for global questions. Index cost is high and incremental updates are hard.
- *For the project:* the S1 contrast. Both build summaries at index time. RAPTOR clusters chunks by embedding, while GraphRAG clusters entities by relations.

**Corpus D cost (derived; Groq `openai/gpt-oss-20b` $0.075/$0.30 per M tokens; Haiku 5.5 $0.10/$0.50; limits 8K TPM / 200K TPD, plan UNVERIFIED; LLMOPS §6).**
- Assumptions: prompt overhead ≈ 120 tokens; output ≈ 150-token summary + 100–300 reasoning tokens at `reasoning_effort=low`; `max_completion_tokens=512`.

| Design | Calls per build | Tokens (in + out) | Groq $ | Min. time at 8K TPM | Share of 200K TPD | Haiku 5.5 $ |
|---|---|---|---|---|---|---|
| Upstream pages, map_reduce | 66 (33 × 2) | ≈ 30–40K | ≈ $0.006 | ≈ 4–5 min | ≈ 20% | — |
| (a1) Chapter summaries | **21** | ≈ 15.6K + 6–9K ≈ 22–25K | **≈ $0.004** | ≥ 3 min | ≈ 12% | ≈ $0.004–0.006 |
| (a2) Section summaries | **68** | ≈ 21K + 20–31K ≈ 42–52K | ≈ $0.011 | ≥ 6.5 min | ≈ 26% | ≈ $0.009–0.017 |
| (b) RAPTOR on the 97 v0 chunks | **≈ 5–25** (≥ 5, because ≈ 14.1K leaf tokens ÷ 3,500 cap; a second layer only if layer 1 has > 11 clusters; **measured, not assumed**) | ≈ 19–24K + 2–11K ≈ 21–35K | ≈ $0.002–0.005 | ≥ 3–5 min | ≤ 18% | ≈ $0.005 |
| Upstream RAPTOR (33 pages) | ≤ 17 (2 discarded) | — | — | — | — | — |

- **Per-request size:** the largest RAPTOR cluster (≤ 3,500 cl100k tokens) + 120 + 512 ≈ 4.1K, which is under 8K TPM. Count the cap in the generator's `o200k_harmony` tokens (phase_04 I1).
- **Embedding (Cohere `embed-v4.0`):** 1 call for 21 or 68 summaries; 1 per RAPTOR layer (≤ 3). Leaves reuse the champion's cached vectors (0 calls).
- **The finding:** a section summary (≈ 190 tokens in, ≈ 150 out) barely compresses, because Corpus D's sections are about one v0 chunk long. **The chapter is the natural summary unit on Corpus D.** Money is negligible; the constraints are TPM per minute and the eval-set gate.

**Current practice (2024–2026).**
- Production stacks usually stop at **parent/child** (retrieve small, return big; AIQ Q5) or at **contextual headers** (phase_04 I5). Both cost 0–1 calls per chunk.
- Summary trees appear as library packs ([R5-S3]) and cookbook recipes, each with its own defaults (depth 3 vs a stop rule; top-2 vs a token budget; a 3.5K vs 10K cap).
- Global "themes" questions are increasingly routed to GraphRAG-style community summaries or to long-context reading (AIQ Q39, Q50).
- Recent multi-hop papers keep RAPTOR as a baseline that strong dense retrievers often match [R5-S9, R5-S10].

**Pitfalls, with evidence:**
- a summary indexed as a message repr, and summaries of reprs (`raptor` cells 9, 11, 13);
- `None` parent links (cell 11);
- id filters written into the query string (cell 19);
- post-filter starvation (cell 15 with [R5-S6]);
- a pickled, identity-free index (cell 13);
- a retry wrapper that cannot retry (`helper_functions.py` L311);
- an unseeded UMAP that makes the tree non-reproducible and **breaks replay**: new cluster texts are new cache keys ([R5-S2] L31);
- GMM on raw high-dimensional vectors ([R5-S7]);
- a single `parent_id` under soft clustering ([R5-S3]);
- top-k instead of a token budget ([R5-S2], [R5-S3]);
- leaves that are not source spans ([R5-S2] `split_text`);
- scoring a summary by its source spans (§6 idea 6);
- summary hallucination (4% in [R5-S1], search-checked).

**How to evaluate.**
- **Target bucket** (new tags, R5-E4): `chapter-scope` multi-span and `global` items, ≥ 8 per split.
- **Retrieval:** at equal budget B (o200k tokens), report:
  - Group-Recall and CE on **leaf text in the final context**;
  - `route_recall@K_s` (two-level arm);
  - the summary token share (collapsed arm).
- **Guards:** MRR@10 and CE@4 on factual-single-span and exact-term must stay ≥ champion − a pre-set tolerance.
- **Answers:** deterministic checks plus human labels on about 10 target answers per arm, with a hand-written theme list scored as nugget recall (D-10).
- **Build:**
  - calls, tokens and cost per build;
  - the rebuild delta after a one-page edit;
  - a summary faithfulness hand sample.
- **Baselines:** the v2 champion (not v0), a raw-chapter routing arm (0 LLM calls), and, as a Full note, whole-document long context.

**Interview questions:**
1. AIQ 04 Q39: GraphRAG and global questions; why top-k cannot summarise themes.
2. AIQ 04 Q23: pre- vs post-filtering, and starvation (two-stage search is a filter).
3. Derived: "Explain RAPTOR's tree build. Why reduce dimensions before the GMM, and why soft clustering?"
4. Derived: "Collapsed tree or tree traversal? How do you compare them fairly with flat retrieval?"
5. AIQ 04 Q29 and Q50: what a summary layer costs when documents change, and when long context makes it pointless.

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).**
Some questions are about a whole chapter or the whole document, and no single chunk says the answer, so flat top-k retrieval returns fragments. Hierarchical retrieval adds coarser units to the index: a summary per chapter (the book's two-level index), or a tree of summaries over clusters of similar chunks (RAPTOR). You search the summaries first and then the chunks under them, or you search all levels together within one token budget. The summaries are written by an LLM at index time, so they cost calls on every rebuild, they can contain errors, and they are never evidence: an answer must still cite the original text. On a 33-page document, measure it against a strong flat retriever and against simply reading the whole chapter; it earns its place only when your own chapter-scope or global questions fail.

**The theory in one read (11 ideas, each with its formula).**
1. *Scope failure:* flat CE@k = 0 when the evidence groups span more chunks than k. For a chapter question with g groups in g different chunks, CE@4 = 0 whenever g > 4.
2. *Two-level routing:* S = top-K_s summaries by cos(q, s); C = {c : unit(c) ∈ S}; return top-N of C. **Routing ceiling:** `route_recall@K_s = 1[every gold unit ∈ S]`, so CE_two-stage ≤ route_recall. A fallback is `C ∪ flat top-N`, or flat search when max cos(q, s) < τ.
3. *Pre- vs post-filter:* a post-filter keeps |top-fetch_k ∩ unit| chunks (often fewer than N); a pre-filter mask searches only the unit's chunks.
4. *Summary unit and compression:* ratio = summary tokens / source tokens. On Corpus D: ≈ 150/620 ≈ 0.24 per chapter vs ≈ 150/190 ≈ 0.8 per section.
5. *Summaries are not evidence:* a `SummaryUnit` has `embed_text` = summary, **no** evidence span, `source_spans` = the union of its children, and `level`, `children[]`, `parents[]`.
6. *Scoring rule:* CE and Group-Recall count only leaf text present in the final context. Crediting summaries with their `source_spans` would give the root node CE = 1 on every question.
7. *Why reduce first:* a full-covariance GMM has p = k·d(d+1)/2 + k·d + k − 1 parameters, which is 1.18 M per component at d = 1,536 and 65 at d = 10. PCA (linear, deterministic) or UMAP (neighbour graph, `n_neighbors = √(N−1)` globally, seeded).
8. *Mixture and soft membership:* P(j|x) = π_j N(x | μ_j, Σ_j) / Σ_l π_l N(x | μ_l, Σ_l). A node joins every j with P(j|x) > 0.1, so it can have several parents (at most 9).
9. *Choosing k:* BIC = −2 ln L̂ + p ln n, minimised over k = 1…min(50, n) − 1. Global clusters, then local ones; re-cluster when Σ tokens > the cap (3,500); stop when a layer has ≤ dim + 1 nodes.
10. *Two retrieval modes:* **collapsed**: sort all nodes by cos(q, ·) and add them while Σ tokens ≤ B (state "stop" vs "skip"). **Traversal**: top-k at the top layer, then top-k among their children, layer by layer.
11. *Cost and rebuild:*
    - calls = Σ_layers #clusters (RAPTOR), or #units (two-level);
    - tokens ≈ Σ (source + overhead) + calls × output;
    - minutes ≥ tokens / TPM;
    - rebuild calls after an edit = #summaries whose member set changed. Two-level gives 1 per changed unit; RAPTOR can give all, unless the reduction is seeded and the cache is keyed on member texts.

**Formula sheet:** routing ceiling; post-filter count; compression ratio; the scoring rule; GMM parameter count; P(j|x) with the threshold; BIC; collapsed-tree budget selection; cost and time; rebuild delta.

**Step-by-step outline (Corpus D: the snapshot, I2's heading tree, the champion chunks; no other data needed, because the chapter structure is the point).**
1. **Find a failing question.** Write one chapter-scope item (for example "What measures does the chapter on renewable energy describe?") with its evidence groups. Show that v0/champion CE@4 = 0 and Group-Recall < 1. Ask Yash to predict which design fixes it.
2. **Read `hierarchical_indices` cells 11–15 critically:** page as section, 2 calls per page, the retry bug, pickle, and post-filter starvation (reproduced in NumPy).
3. **Build the two-level index right:** 21 chapter units from I2's tree; 21 cached summaries (prompt file v1); a `SummaryUnit` with `source_spans`; pre-filter mask search; fallback. Compute `route_recall@K_s` for K_s = 1…5.
4. **Control arm with 0 LLM calls:** route on the **raw chapter text** embedding (Cohere takes 620 tokens; MiniLM would truncate at 256, so this arm uses Cohere or is flagged). It tells you whether the summary adds anything.
5. **Read `raptor` cells 9–19 critically:** the five divergences (pages as leaves; no reduction or BIC; hard clusters; fixed levels; no budget) and the four bugs (reprs; `None` links; query-string ids; dropped top level).
6. **Build the RAPTOR tree on the champion's 97 chunks:** PCA-10 → BIC curve → GMM → soft labels at 0.1 → re-cluster above the cap → summaries (cached) → layer 2 if more than 11 nodes. Print the tree: nodes per layer, parents per leaf, calls.
7. **Collapsed tree vs traversal** at equal budget B on dev: Group-Recall and CE (leaf), plus the summary token share.
8. **Faithfulness:** the automatic check (numbers and capitalised terms absent from the source) on every summary, plus a hand read of all 21 chapter summaries and about 10 RAPTOR nodes.
9. **Cost and rebuild:** the cost table from the cache's usage. Simulate a one-page edit: two-level = 1 call; RAPTOR = count the changed clusters (seeded vs unseeded).
10. **Decide** (06 v8, only if the gate is met), else record "mechanism studied; no target bucket" (02 L85 rule for U/S items).

**Visuals that earn their place:**
- *Two-designs diagram:* a two-level fan (21 chapter summaries → chunks) next to a RAPTOR tree (97 leaves → clusters → layer 2). Shows fixed units vs learned clusters.
- *Routing-ceiling strip:* per dev item, gold chapters vs the top-K_s chapters. Shows why cross-chapter items are capped.
- *Post-filter starvation bar:* chunks returned per selected page, post-filter (fetch_k = 20) vs pre-filter. Shows R5-E5 on our data.
- *BIC curve with the chosen k*, and the GMM parameter count against d (log scale). Shows why the reduction step exists.
- *Tree explorer (Plotly sunburst or icicle):* layer → cluster → leaf, coloured by chapter. Shows whether clusters follow chapters (if they do, the cheap structure tree is enough).
- *Budget bar per arm:* tokens by level in the collapsed context. Shows what the summaries displace.

**Full only:**
- local clustering and the recursion details;
- the UMAP vs PCA arm (seeded; numba weight);
- the LlamaIndex and official defaults table;
- the official repo's threshold-mode bug and its non-substring leaves;
- traversal mode;
- the long-context baseline (13K tokens; Haiku only);
- HippoRAG 2's figure and the re-evaluation caveats;
- the GraphRAG contrast (S1);
- the hallucination study;
- the rebuild experiment with an unseeded reduction.

### 7. Verify notebook plan

`study/notebooks/R5_hierarchy_verify.ipynb`. Offline by default (MiniLM, sklearn, NumPy). It can optionally replay the cached Groq summaries and Cohere vectors recorded by the LLMOps notebook.
1. **Units and sizes:** load I2's heading tree on the PyMuPDF snapshot. Assert 21 chapters and 68 sections. Print tokens per unit in o200k and cl100k, and the compression a 150-token summary would give. The ≈ 620 and ≈ 190 figures above are derived and get re-measured here.
2. **Post-filter starvation:** for every dev question, simulate FAISS's rule (global top 20, then filter by page) against a pre-filter mask. Count the chunks returned per selected page. Assert that post ≤ pre and print how often post < min(5, chunks on the page).
3. **Routing ceiling:** with surrogate summaries (zero-call: chapter title + first 2 sentences) **and**, if cached, the Groq summaries, compute `route_recall@K_s` and two-stage CE/Group-Recall at equal budget for K_s = 1…5. Assert CE ≤ route_recall item by item.
4. **Scoring-rule test:** a toy tree whose root has `source_spans` = the whole document. Scoring it by its spans gives CE = 1 on every item (the trap); the leaf-only rule gives the true value. This becomes a T1 test.
5. **GMM facts:** parameter count at d = 384 / 1,536 / 10; BIC over k = 1…49 on PCA-10 of the 97 MiniLM chunk vectors (seeded; a few seconds); soft labels at 0.1 (parents per leaf histogram). Assert the same tree on a rerun.
6. **Upstream bug replicas (our own code, no upstream run, no LLM):**
   - the cell 11 metadata logic, which shows that level-1 `child_ids` are all `None`;
   - `str()` of a pydantic stand-in message, to show what cell 13 embeds;
   - the cell 19 query-string growth.
7. **RAPTOR build from cached summaries:** layers, nodes and calls. Collapsed vs traversal at budget B on dev; the summary token share.
8. **Rebuild delta:** edit one page's text (a synthetic change), re-chunk, re-embed with MiniLM, re-cluster seeded and unseeded, and count the clusters whose member set changed (that is the number of new summary calls).
9. **Faithfulness pre-check:** numbers, years and capitalised terms in each cached summary that do not occur in its `source_spans` text, listed for hand review.

- **Runtime:** about 1–2 minutes on CPU (MiniLM over 97 chunks + ≤ 100 summaries; 49 small GMM fits).
- **API calls:** 0. With the cache: 0 live calls; it reads ≈ 21 + 5–25 recorded summaries.
- **Charts:** Plotly.

### 8. Apply-it tool plan and real-world checklist

`study/tools/hierarchy_fit_check.py`: "Would a summary layer help MY documents and questions, and what would it cost?"
- **Inputs:**
  - `--docs` (PDF, MD or TXT);
  - `--questions q.jsonl` (`q`, evidence quotes or spans, `category`, optional `scope`);
  - `--unit chapter|section|auto` (from detected headings);
  - `--design two_level|raptor|both`;
  - `--reduce pca|umap`;
  - `--embedder minilm|cohere` (through the cache);
  - `--budget N` (o200k tokens);
  - `--summaries surrogate|cached|record` (`record` calls Groq through the cache; the default needs no key);
  - `--report out.md`.
- **Outputs (Markdown + Plotly HTML):**
  - unit sizes and compression;
  - routing ceiling per question;
  - flat vs two-level vs collapsed Group-Recall/CE (leaf) at budget;
  - tree stats;
  - the cost and time estimate for Groq and Haiku from the token counts;
  - the rebuild-delta estimate;
  - the faithfulness pre-check list;
  - the checklist and a recommendation.
- Like `bm25_fit_check.py`, it shows the mechanism on a few questions. It is not an evaluation.

**Real-world checklist (11 checks):**

| # | Check | Auto / manual |
|---|---|---|
| H1 | At least 8 questions per split really need a chapter or global view (evidence groups in ≥ 3 chunks or ≥ 2 units) | auto (counts) + manual (read them) |
| H2 | The flat champion fails them at equal budget (Group-Recall < 1); otherwise stop here | auto |
| H3 | The summary unit compresses (ratio ≤ 0.5); otherwise use a larger unit | auto |
| H4 | Routing ceiling ≥ 0.8 at the chosen K_s on target items; a fallback is configured | auto |
| H5 | Filtering is a pre-filter (mask), not a post-filter over fetch_k | auto (config) |
| H6 | Summaries carry `source_spans`, `children`/`parents`, prompt version and model; no `None` links | auto |
| H7 | Scoring counts leaf text only; summary token share reported | auto |
| H8 | Faithfulness: the pre-check flags reviewed; ≤ 1 unsupported claim per 10 summaries in the hand sample | auto + manual |
| H9 | The reduction is seeded and a rebuild gives the same tree; the rebuild delta after a one-page edit is reported | auto |
| H10 | Build cost fits the quota (tokens ≤ day budget; largest request < TPM) | auto |
| H11 | Single-span guard: MRR@10 and CE@4 not below champion − tolerance | auto |

**Recommendation logic:**
- H1 or H2 fails → "no target bucket: keep flat retrieval; study only".
- H3 fails → "your units are chunk-sized: summarise chapters, or skip summaries and use path headers (I5)".
- H4 < 0.8 → "routing loses evidence: prefer collapsed tree, or add the flat-union fallback".
- The raw-unit arm ≈ the summary arm → "summaries add nothing: route on raw units (0 calls)".
- RAPTOR ≈ two-level → "take two-level: cheaper, local rebuilds".
- H8 fails → "fix the prompt before measuring".
- Otherwise → "run the pre-registered experiment".

### 9. LLMOps notebook plan

`study/llmops/notebooks/R5_hierarchy_ops.ipynb`: the two-level and RAPTOR indexes built and served as a production component, traced, evaluated and replayable (foundation §12 rows "5 · R1–R5" and "11 · S1–S3/v8").
- **Framework build (mechanism step → piece):**
  - *Units:* I2's heading tree → LangChain `Document`s with `section_path`, `char_start`, `char_end`, `unit_id`. No loader re-parses the PDF; the snapshot is the source.
  - *Summaries:* `ChatPromptTemplate` from `prompts/r5_summary_v1.txt` → `CachedChatModel` (Groq `openai/gpt-oss-20b`, `reasoning_effort="low"`, `max_completion_tokens=512`, temperature 0) via `.batch(..., config={"max_concurrency": 1})` behind the token throttle.
    - **Not** `load_summarize_chain`: 2 calls per document and a hidden default prompt (R5-E6).
    - The output is `.content` from the message, never `str(message)` (R5-E1); a test asserts that no summary starts with `content=`.
  - *Stores:* `InMemoryVectorStore` (langchain-core) with `CachedEmbeddings` (Cohere `embed-v4.0`, `search_document`; queries `search_query`): one store for summaries and one for leaves. Warn that its `filter` receives a `Document` (R5-E10). FAISS is not used (D-07); one read-only cell shows its `fetch_k=20` post-filter.
  - *Two-stage retriever:* a custom `BaseRetriever` subclass `TwoStageRetriever(k_summaries, n_chunks, budget, fallback="union")`. It returns leaves with `metadata["level"]=0` and `metadata["routed_by"]=[unit ids]`.
  - *RAPTOR:* the tree build in plain Python (sklearn PCA/GMM; optional seeded UMAP). It is persisted as `tree.json` (nodes, levels, children, parents, `source_spans`, cluster ids, the BIC curve, seed); there is no LangChain component for it. `CollapsedTreeRetriever(BaseRetriever)` selects by budget B with an explicit `stop|skip` rule.
  - *Reading only:* `MultiVectorRetriever` (one parent id, k = 4, scores dropped, can return fewer than k) and the LlamaIndex pack (depth 3, top-2, single `parent_id`, cap 10K) are shown from source as "what the library would do", with these defaults named.
  - **LangGraph: not needed.** The flow is linear (route → retrieve → assemble → generate). Traversal is a bounded loop with no branch chosen at run time (LLMOPS §9.1 rule). Choosing between flat and hierarchical per question is A1 routing, not R5.
- **External calls (all through `llmops.cache`; replay needs no key):**

  | Call | Count per build or run | Notes |
  |---|---|---|
  | Groq gpt-oss-20b, chapter summaries | 21 | ≈ 22–25K tokens, ≈ $0.004, ≥ 3 min at 8K TPM |
  | Groq, section summaries (exploratory arm) | 68 | ≈ 42–52K tokens, ≈ $0.011 |
  | Groq, RAPTOR summaries | ≈ 5–25 (measured) | ≈ 21–35K tokens, ≈ $0.002–0.005; each request < 4.2K tokens |
  | Cohere embed-v4.0 (`search_document`) | 1 (chapters) + 1 (sections) + ≤ 3 (RAPTOR layers) | Leaves reuse the champion's cached vectors |
  | Cohere embed-v4.0 (`search_query`) | 0 new (shared query cache) | — |
  | Groq generation, experiment | 3 arms × (≈ 8 target + ≈ 16 guard dev items) ≈ 72, + 1 test touch ≈ 16 → **≈ 90** | ≈ $0.03; about one day of TPD at most |
  | Claude Haiku 5.5 (optional summariser arm, credits only) | 21 + RAPTOR | ≈ $0.004 + $0.005; effort `low`, no `temperature` |
  | Judge | **0** (D-10) | Stored traces feed the end batch |

  - Replay depends on a **deterministic tree**: the summary cache key contains the member texts, so an unseeded reduction produces new keys and a `ReplayMiss`. Rule: the build reads `tree.json` when present, and the cluster step runs only in `record` mode with a fixed seed.
- **Tracing (JSONL by default, Phoenix locally, LangSmith for Corpus D only per LLMOPS §3):**
  - **Build spans:**
    - per layer: n nodes, reduction (method, dims, seed), the BIC curve, chosen k, threshold, re-cluster events;
    - per summary call: `cluster_id`, member unit ids, `source_spans`, `prompt_version` + prompt sha256, model requested/returned, tokens (incl. reasoning), `cache_key`, `cache_hit`, latency, faithfulness pre-check flags.
  - **Query spans:**
    - per hit: unit id, **level**, score, rank, tokens, `routed_by`;
    - `route_recall` (when gold is known), budget used, summary token share, fallback taken.
  - Export filters chunk text unless the corpus is D.
- **Dataset and evaluators:**
  - The golden set from M1, plus the new `chapter-scope`/`global` items (a new dataset version, R5-E4). Dev for selection, test touched once.
  - Tier-1 evaluators: Group-Recall and CE on leaf text at budget B, `route_recall@K_s`, MRR@10 and CE@4 on guard items, realized tokens, summary token share, the `content=` repr check, the `None`-link check, and the faithfulness pre-check rate.
  - Answers: deterministic checks plus human labels on about 10 target answers per arm, with nugget recall against a hand theme list (D-10).
  - `langsmith.evaluate(..., upload_results=False)` is shown once.
- **Experiment against the previous version** (proposed refinement of the 06 v8 card; 06 has only the generic card):
  - Base = the current champion (v7, or the v2 champion if R5 runs early on a branch), at equal budget B.
  - Pre-registered arms (≤ 3, phase_04 I1 rule):
    - **A1-raw** chapter routing on raw chapter text (0 LLM calls);
    - **A1-sum** chapter-summary two-stage with union fallback;
    - **A2** RAPTOR collapsed tree (PCA-10, BIC, soft 0.1, cap 3,500 o200k).
  - Exploratory only: section summaries, traversal, UMAP.
  - Primary: Group-Recall (leaf) on the target bucket. Guards: single-span MRR@10/CE@4 ≥ champion − 0.05 [P], faithfulness ≤ 1/10, build calls within quota.
  - Paired comparison and verdicts as in M4: supported / not supported / inconclusive.
  - **Run only if the gate holds** (≥ 8 target items per split, and the flat champion fails them).
- **Cost, latency and tokens:**
  - build cost per arm (calls, tokens, $ "if called" vs paid);
  - rebuild delta after the one-page edit;
  - query p50/p95 (two-stage adds one exact search, so it should be flat at 97 chunks);
  - context tokens by level.
- **Prompt and config versioning:**
  - `prompts/r5_summary_v1.txt` (never edited);
  - `config.yaml` with unit, K_s, N, budget, `stop|skip`, reduction, dims, seed, threshold, cap, model and effort;
  - `tree_manifest.json` with the leaf `params_hash` and `embed_hash`, the prompt sha, model, seed and the `tree.json` sha256.
  - A change to any of them is a new arm in the registry.
- **Monitoring and feedback:**
  - T1 tests: the leaf-only scoring rule; no `None` links and no `content=` reprs; tree determinism (same `tree.json` sha on a seeded rebuild); budget respected.
  - Replay test: the notebook runs with `LLMOPS_CACHE_MODE=replay`.
  - Alerts: rebuild delta > 50% of summaries after a small edit (unseeded or unstable clustering); the faithfulness flag rate rising; the summary token share > 50% of B (summaries crowd out evidence); the route-recall drop.
  - Failures go to the M5 log, and confirmed new chapter or global items go into the golden set (`error-analysis`, `ci-cd-evals`).
- **Place in the lifecycle:**
  - Analyze: the M5 bucket for chapter and global scope (`error-analysis`, `trace-data-analysis`).
  - Measure: Group-Recall and route recall (`rag-evaluation`, `code-based-evaluators`); faithfulness by hand (`collaborative-annotation` method for the sample).
  - Improve: adopt or keep flat, with build cost (`improving-llm-agents`).
  - dev → CI → monitoring: `ci-cd-evals`. Tracing: `llm-observability`. Framing: `evals-foundations`.
  - Skills were applied as the foundation describes them; `.claude/skills/` is not present in this session.

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Two-level index, routing, budget selection, scorer rule, tree JSON | own code (`ragkit`, NumPy exact search) | — | — | yes | — | — | yes (D-07) |
| GMM, BIC, PCA | `scikit-learn` | 1.9.1 | in `uv.lock` (via sentence-transformers), **not declared** | yes | — | BSD-3 | yes; declare it explicitly, since the code imports it |
| Optional reduction arm | `umap-learn` (+ `numba` 0.68.0, `llvmlite` 0.50.0, `pynndescent` 0.6.0) | 0.5.12 | no | yes | ≈ 45 MB download (win cp312); numba JIT start-up; numba caps numpy < 2.6 | BSD | optional; seeded only; PCA is the lighter default |
| Local embedder | `all-MiniLM-L6-v2` via `sentence-transformers` | 6.1.0 | yes | yes | — | Apache-2.0 | yes (fallback; truncates raw chapters at 256 tokens) |
| Default embedder | Cohere `embed-v4.0` via `cohere` | 7.2.0 | yes | replay only | ≈ 2–5 calls per build; price UNVERIFIED | MIT (SDK) | yes (D-03) |
| Summariser (default) | Groq `openai/gpt-oss-20b`, `reasoning_effort=low`, `max_completion_tokens=512` | from `.env` | SDK yes | replay only | 21 / 68 / 5–25 calls; ≈ $0.002–0.011 per build | — | yes (D-04); plain chat, no tool calls or JSON needed |
| Summariser (credits) | Claude Haiku 5.5 `claude-haiku-5-5`, effort `low` | `anthropic` 1.11.0 | no | replay only | ≈ $0.004–0.017 per build | MIT (SDK) | yes (D-32); worth it only as a quality arm |
| Generation for the experiment | Groq gpt-oss-20b | from `.env` | yes | replay only | ≈ 90 calls ≈ $0.03 | — | yes |
| Long-context baseline (Full) | Claude Haiku 5.5 (13K-token prompt) | — | no | replay only | ≈ 10 calls ≈ $0.02 (ASSUMPTION) | — | needs credits; Groq free tier blocked (13K > 8K TPM) |
| Framework core | `langchain-core` (`InMemoryVectorStore`, `BaseRetriever`, prompts) | 1.6.6 | no | yes | — | MIT | yes (LLMOps only) |
| Reading only | `langchain-classic` (`MultiVectorRetriever`, `ParentDocumentRetriever`, `load_summarize_chain`) | 1.0.8 | no | — | — | MIT | read source; do not install |
| Reading only | `langchain-community` FAISS | 0.4.2 | no | — | — | MIT | read source (post-filter); FAISS not used (D-07) |
| Reading only | `llama-index-packs-raptor` | 0.4.2 | no | — | — | MIT | read source; it pulls OpenAI LLM packages |
| Reading only | official RAPTOR repo @ `7da1d48` | — | no | — | — | MIT | read source; it pins `openai==1.3.3`, torch, transformers |
| Graph framework | `langgraph` | — | — | — | — | MIT | **not needed** (linear flow) |
| Provider integrations | `langchain-groq` / `langchain-cohere` | — | no | — | — | MIT | not used (pin conflicts; adapters, LLMOPS §9.3) |
| Hosted tracing | `langsmith` | 0.14.4 | no | no | free plan; ≈ 150 build + query traces | MIT (SDK) | yes, Corpus D only |
| Local tracing | JSONL + `arize-phoenix-otel` 0.17.2, server via `uvx arize-phoenix@20.19.0` | — | no | yes | — | Apache-2.0 / ELv2 | yes |
| Budget tokens | `tiktoken` (`o200k_harmony`) | 0.14.0 | yes | after one BPE download | — | MIT | yes |
| Plots | `plotly` (sunburst/icicle, BIC curve) | locked | yes | yes | — | MIT | yes |

**Install lines (do not run):**
- `uv add scikit-learn==1.9.1` (declare what is already locked).
- `uv add --group llmops langchain-core==1.6.6 langsmith==0.14.4 arize-phoenix-otel==0.17.2` (foundation pins).
- Optional: `uv add --group r5-umap umap-learn==0.5.12 numba==0.68.0`.
- With credits: `uv add --group llmops anthropic==1.11.0`.

**Keys:** `GROQ_API_KEY` and `COHERE_API_KEY` (present) to record once; `ANTHROPIC_API_KEY` only for the Haiku arm or the long-context baseline; `LANGSMITH_API_KEY` only for the hosted view. Replay needs none.

### 11. Open questions for Yash (preferences only)

1. Do you want the Corpus D tree explorer (Plotly sunburst) in the Short lesson, or only in Full? **Full** recommended: Short stays on the two-level design.
2. Will you hand-read all 21 chapter summaries for faithfulness (about 30 minutes), or a random 10? **all 21** recommended: it is the whole population.

---

## Phase-level notes

### 1. One stage contract for v2.0–v2.3 (and R5)

The five concepts are not five separate add-ons. Each changes one stage of the same retriever, and the 06 cards run in order on the previous champion. So the build needs one shared contract, written once in `retrieval.py` and the trace schema.

| Stage (version) | Input | Output | What it cannot fix | Headroom check before running | Owner |
|---|---|---|---|---|---|
| Index units | v1.x champion units (`text`, `embed_text`, `bm25_text`) | — | — | — | Phase 4 |
| Filter (v2.2) | question → scope (user, rules, LLM) | an allowed-id **mask** applied to *both* lists before fusion; BM25 statistics stay corpus-wide | a wrong scope removes the gold chunk (hard failure) | scoped items where gold is outranked by out-of-scope chunks without a filter | R2 |
| Two lists + fusion (v2.0) | masked dense and BM25 lists at a recorded depth | fused list with `ranks_by_source`, cut to the pool size | evidence that neither list retrieves | items where CE@pool(fused) > CE@4(champion) | R1 |
| Rerank (v2.1) | fused top-N pool (N ∈ {10, 20, 50}) | reordered pool with `prev_rank`, `prev_score`, `score_kind` | anything outside the pool (CE@pool is the ceiling) | oracle reorder minus champion per N | R3 |
| Diversify (v2.3) | reranked pool; relevance = the reranker score normalised per query; cosine only for redundancy | top-`k_select` set in selection order | single-span items (diversity can evict the best chunk) | "R4-eligible" items: ≥ 2 evidence groups in different chunks, CE@pool = 1, CE@4 = 0 | R4 |
| Summary layer (v8, optional) | chapter/tree summaries plus leaves | leaves only are scored; summary token share reported | questions whose evidence is in one chunk | chapter/global items, ≥ 8 per split | R5 |

Shared rules:
- **Tie rule:** smaller `chunk_id` everywhere. LangChain and LlamaIndex keep first-seen order, so the parity tests report ties separately.
- **Every candidate list** carries `chunk_id`, rank, raw score and `score_kind`. Without that, R4 cannot reuse R3's pools, and nobody can diagnose the "right document, wrong rank" case.
- **Every arm records** its depth, pool size, `k_select` and token budget, because the frameworks pick these silently.
- **Each card's baseline** is the previous champion *and* v0 (06 §4.1). For R5 (v8, after v7), the card must name the champion explicitly.

### 2. Ordering problems

- **06 order vs 02 numbering.** 06 runs v2.0 R1 → v2.1 R3 → v2.2 R2 → v2.3 R4. 02 numbers them R1, R2, R3, R4. That works if the lessons follow 06's order, or if R2's lesson is taught after R3 and states that the filter must work with reranking. The v2.2 baseline is the v2.1 champion (R2 merge notes).
- **The R3 gate is not met.** R3 requires P4 (bi-encoder vs cross-encoder), but P4 is `not_started` and O1-Q10 scored 0. P4 must be studied first (tracker).
- **The prerequisite lists disagree:**
  - R2 is missing C3 in 03's registry (R2-E5);
  - 03 makes R5 depend on R2, 02 does not;
  - 03 lists P7 for R5 in its table but not in its registry (R5-E9).
  - Settle all three in one correction pass.
- **02 and 03 cite different `dartboard.ipynb` cells** (02: 16, 23, 25; 03: 21, 25). R4-E1 settles it: the selection algorithm is in cells 19 and 21; cell 23 is only the retrieval wrapper.
- **R5 sits in Phase 5 but builds v8**, after v7, where it competes with S1 Graph RAG. Teach R5's mechanism here and keep its experiment for v8. R5 and S1 should share one target-bucket definition, one summary-provenance schema (source spans, children, parents) and one rebuild-cost record.

### 3. What the phase needs from Phases 3 and 4

- **M1 (eval set).** Plan all these additions together, as one versioned dataset change (Decision 1):
  - `scope` and `scope_mention` fields, shared with I2's `section_scoped` (R2-E3 and I2-E3 are the same fix);
  - the rule-built acronym probe set, kept as its own slice (R1);
  - 4–6 cross-page multi-span items (R4);
  - chapter-level and whole-document items (R5).
  The probe set is built from the document, not from chunks, so it keeps 06 §6.3's leakage rule. Its high lexical overlap is deliberate, so report it separately and never pool it into the headline mean.
- **M2 (metrics).** The new metrics listed in Summary gap 4 belong in the M2 harness, not in each notebook.
- **M4 (statistics).** The headroom gate and the pre-registered "inconclusive" verdict follow M4's power rules. Phase 4 needs the same arithmetic (phase_04 Summary gap 1).
- **Phase 4.**
  - R1 inherits the champion's `bm25_text` and `embed_text`.
  - R2 and R5 reuse I2's heading tree: 1 title, 21 chapters, 68 sections, 192 sub-headings; R2's independent recount matches. It should be one shared parsing artefact.
  - R5 needs a summary variant of phase_04's `IndexUnit`.
  - I6 uses the same ms-marco cross-encoder as R3, so share the revision pin and the loader.
  - I2/I5 headers change how similar the two "Paris Agreement" chunks look, so R4's redundancy numbers depend on the chunking champion.

### 4. What other phases inherit

- **Q1 (Phase 6):** merges sub-query lists with RRF. It reuses `fuse_rrf` and the four fusion tests (identity, permutation, monotonicity, catalogue/dead list), and records k, depth and rank base the same way.
- **X3 (Phase 7):**
  - R4 decides which chunks get in; X3 merges overlapping text and decides the order in the prompt.
  - Exact-hash dedup belongs at ingest or at the start of R4, not only in X3.
  - An empty filter result is logged as `no_context`, reason `filter_empty`, and never scored as a correct abstention.
- **V2/V3 (Phase 8):** a relevance grader is a pointwise reranker with a threshold. Share R3's pointwise LLM code, the prompt file and the calibration warning (MC-006). An abstention threshold on reranker scores needs V3 calibration on labelled items.
- **D2/D4 (Phase 9):** R3's latency budget test and `hardware_id` rule belong to D2. D4 reuses R2's filter module but fails closed (`on_error = deny`); R2's fail-open default must not leak into D4.
- **A1 (Phase 10):** "the router" as a filter source belongs to A1. If MMR helps multi-span items but hurts single-span ones, routing diversity by question type is the natural A1 follow-up.
- **S1 (Phase 11):** competes with R5 for v8 (item 2 above). For global questions, R5 also needs a long-context baseline: Corpus D at ≈ 13K tokens fits one prompt. That baseline needs Haiku, because Groq's free tier allows only 8K tokens per minute.

### 5. Corpus T requirements that Phase 5 adds (inputs to DEC-3; not a choice)

- At least two documents whose chunks outrank each other's gold when no filter is used, and at least 10 questions that name a document (R2).
- Real tables and code-like identifiers, so that the exact-term slice is not only acronyms (R1).
- Repeated topics across documents, so that redundancy is not limited to Corpus D's five known pairs (R4).

### 6. Corrections for `LLMOPS_FOUNDATION.md` (reported, not edited)

- **§9.2 (hidden defaults)** needs rows for:
  - `EnsembleRetriever` and `BM25Retriever` (R1-E10);
  - LlamaIndex `QueryFusionRetriever`'s `num_queries=4` (R1-E7);
  - the FAISS `fetch_k=20` post-filter, the `InMemoryVectorStore` pre-filter (it takes a `Document`), the `$ne`/`$neq` filter dialects and `SelfQueryRetriever` (R2-E11, R5-E10);
  - the `CrossEncoder` activation and `max_length`, `CrossEncoderReranker`'s `top_n=3`, and `LLMListwiseRerank` (R3-E10);
  - `max_marginal_relevance_search` (k=4, fetch_k=20, λ=0.5, scores dropped, private utility) (R4);
  - `load_summarize_chain` (R5-E10).
- **§6.2:** Cohere rerank's "32k context" omits that the v2 endpoint truncates each document at 4,096 tokens by default (`max_tokens_per_doc`) (R3-E9).
- **§11:** `langchain-classic` is listed as read-only, but R1's and R3's framework wrappers live only there (R3-E11; Decision 3).
- **§12 (application map), Phase 5 row:** add an "LLM rerank arms (Groq / Haiku)" call column entry, and R5's seeded `tree.json` as the replay artefact. An unseeded reduction produces new cluster texts, so the cached summary calls would miss.

### 7. A comparison lesson the phase needs

There is no "R-CMP" concept, but the stage table in item 1 is the comparison a learner needs. One page should cover each stage: what it changes, what it cannot fix, its headroom check, its cost, and where it sits in the trace. Put it at the end of R4, or as a short Phase 5 summary page.
- **Interview angle:** "Your hybrid + rerank + MMR pipeline gained 4 points. Which stage gets the credit, and how do you know?" The answer is per-stage headroom, ablations on one champion, and the per-stage trace fields.

---

## Sources

Numbered per concept; inline keys such as **[R3-S2]** point here. "Verified" means the page, README, source file or wheel was opened in this session and the fact checked on it. "UNVERIFIED (search-checked only)" means only web-search summaries were seen, because the host was blocked from this cloud session. Book pages are not listed: none was opened in this session (see the header). Shared course inputs (02, 03, 04, 06, 08, LLMOPS_FOUNDATION, phase_03, phase_04, the R1 kit, the tracker) are listed in each concept's §1.

### R1 sources
1. [R1-S1] Cormack, G. V., Clarke, C. L. A., Büttcher, S. "Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods." SIGIR 2009. https://doi.org/10.1145/1571941.1572114 (PDF at https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf). **UNVERIFIED (search-checked only):** the PDF hosts, ACM and plg.uwaterloo.ca were blocked; the pilot, k = 60, TREC and LETOR 3 come from search summaries.
2. [R1-S2] Bruch, S., Gai, S., Ingber, A. "An Analysis of Fusion Functions for Hybrid Retrieval." ACM TOIS 42(1), article 20, 2023; arXiv 2210.11934 (2022). https://arxiv.org/abs/2210.11934 · https://doi.org/10.1145/3596512. **UNVERIFIED (search-checked only):** arXiv, ACM and pinecone.io were blocked; findings from search summaries.
3. [R1-S3] Anthropic. "Introducing Contextual Retrieval." 2024-09-19. https://www.anthropic.com/news/contextual-retrieval. **verified** (WebFetch: hybrid steps, the TS-999 example, the 5.7 / 3.7 / 2.9 / 1.9% figures; no fusion method named).
4. [R1-S4] Anthropic. claude-cookbooks, `capabilities/contextual-embeddings/guide.ipynb`, `retrieve_advanced`, @ `a162e01`. https://raw.githubusercontent.com/anthropics/claude-cookbooks/main/capabilities/contextual-embeddings/guide.ipynb. **verified** (150 per leg, 0.8/0.2 weights, 1/(index + 1), id-keyed union, descending-id ties).
5. [R1-S5] LangChain. `langchain-classic` 1.0.8 `langchain_classic/retrievers/ensemble.py`; `langchain-community` 0.4.2 `langchain_community/retrievers/bm25.py` and `vectorstores/faiss.py` (PyPI wheels). https://pypi.org/project/langchain-classic/1.0.8/ · https://pypi.org/project/langchain-community/0.4.2/. **verified** (source read in full for both retrievers).
6. [R1-S6] dorianbrown. `rank-bm25` 0.2.2, `rank_bm25.py` (PyPI wheel, 2022-02-16). https://pypi.org/project/rank-bm25/0.2.2/. **verified**.
7. [R1-S7] LlamaIndex. `llama-index-core` 0.14.25, `llama_index/core/retrievers/fusion_retriever.py` and `constants.py` (PyPI wheel, 2026-09-21). https://pypi.org/project/llama-index-core/0.14.25/. **verified**.
8. [R1-S8] Weaviate. Docs `docs/weaviate/concepts/search/hybrid-search.md` and `docs/weaviate/search/hybrid.md` @ `5dcf1d6`; server `usecases/traverser/hybrid/searcher.go` (main). https://github.com/weaviate/docs · https://github.com/weaviate/weaviate. **verified** (raw GitHub; docs.weaviate.io itself was unreachable).
9. [R1-S9] Elastic. `docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion.md` @ `4f131aa`, https://github.com/elastic/elasticsearch; OpenSearch `_search-plugins/search-pipelines/score-ranker-processor.md` @ `6078098`, https://github.com/opensearch-project/documentation-website. **verified**.
10. [R1-S10] NAVER Labs Europe. SPLADE README and LICENSE @ `8dcd33a`. https://github.com/naver/splade. **verified** (model table; CC BY-NC-SA 4.0).
11. Interview repo: ombharatiya/AI-Engineer-Interview-Questions @ `e080df2`, `04-rag-and-retrieval/questions.md` Q9, Q24, Q32; `12-coding-challenges/17_hybrid_search_and_rerank.py`. MIT, "Copyright (c) 2026 Om". **verified**.
12. Upstream: NirDiamant/RAG_Techniques @ `009adba`: `all_rag_techniques/fusion_retrieval.ipynb` cells 0, 10, 14, 15, 17, 19; `all_rag_techniques_runnable_scripts/fusion_retrieval.py` L60–L86, L135; `all_rag_techniques/fusion_retrieval_with_llamaindex.ipynb` cells 3, 8, 15, 17, 19, 20, 22; `data/Understanding_Climate_Change.pdf`. Custom non-commercial licence: described, not quoted at length. **verified**.
13. Course files read locally (listed in §1), including `sources/vai/L19-L23_core_rag.md` §L23. **verified** (local).

### R2 sources
1. Liana Patel, Peter Kraft, Carlos Guestrin, Matei Zaharia, "ACORN: Performant and Predicate-Agnostic Search Over Vector Embeddings and Structured Data", SIGMOD 2024, https://arxiv.org/abs/2403.04871 (ACM DOI 10.1145/3654923) — **UNVERIFIED (search-checked only)**; arXiv blocked. Code repo https://github.com/stanford-futuredata/ACORN README — **verified** (opened raw: FAISS-based, `IndexACORNFlat(d, M, gamma, M_beta)`, per-query filter bitmap).
2. Weaviate documentation, "Filtering" (`docs/weaviate/concepts/filtering.md`) and "Vector index" config reference (`docs/weaviate/config-refs/indexing/vector-index.mdx`), Weaviate, main branch fetched 2026-10-17, https://github.com/weaviate/docs — **verified** (opened raw: allow-list pre-filtering, `acorn` default since v1.34, `sweeping`, `pathseer` (v1.40), `flatSearchCutoff` default 40000; vendor).
3. Qdrant documentation, "Indexing" (`manage-data/indexing.md`) and "Search" query-planning section (`search/search.md`), Qdrant, master fetched 2026-10-17, https://github.com/qdrant/landing_page — **verified** (opened raw: filterable HNSW extra edges, payload index before ingest, `full_scan_threshold` 10000 KB example, cardinality-based planning, ACORN option from v1.16.0; vendor).
4. pgvector README, Andrew Kane et al., master (install line v0.8.7), https://github.com/pgvector/pgvector — **verified** (opened raw: "Filtering", "Iterative Index Scans"; the 10% × `ef_search` 40 = 4 example).
5. FAISS wiki, "Setting search parameters for one query" (section "Searching in a subset of elements"), Meta AI, https://github.com/facebookresearch/faiss/wiki/Setting-search-parameters-for-one-query — **verified** (opened raw wiki markdown).
6. LangChain `langchain-community` 0.4.2 wheel (2026-05-22) `vectorstores/faiss.py` L387–L450, L673–L712, L1342–L1440; `langchain-core` 1.6.6 wheel (2026-09-29) `vectorstores/in_memory.py` L291–L332, https://pypi.org/project/langchain-community/0.4.2/ , https://pypi.org/project/langchain-core/1.6.6/ — **verified** (wheels unpacked and read).
7. LangChain `langchain-classic` 1.0.8 wheel (2026-06-10) `retrievers/self_query/base.py` L237–L405, `chains/query_constructor/base.py` L44–L120, `parser.py`; `langchain-groq` 1.1.3 wheel (2026-06-10) `chat_models.py` L78–L81, L905–L991, L1224–L1228, https://pypi.org/project/langchain-classic/1.0.8/ , https://pypi.org/project/langchain-groq/1.1.3/ — **verified** (wheels unpacked and read).
8. Chroma `chromadb-client` 1.5.9 wheel (2026-05-05) `chromadb/base_types.py` L129–L149, https://pypi.org/project/chromadb-client/1.5.9/ — **verified** (wheel unpacked and read).
9. Groq, "Structured Outputs", https://console.groq.com/docs/structured-outputs — **UNVERIFIED in this session** (DNS blocked; search summary says strict mode is limited to select models; LLMOPS_FOUNDATION source 12 lists the page as verified there, without the model list).
10. "An In-Depth Study of Filter-Agnostic Vector Search on a PostgreSQL Database System: [Experiments and Analysis]", authors not confirmed, 2026, https://arxiv.org/abs/2603.23710 — **UNVERIFIED (search-checked only)**; used only for "ACORN weakens at low selectivity with AND predicates".
11. AI-Engineer-Interview-Questions, Om (ombharatiya), 2026, MIT, `04-rag-and-retrieval/questions.md` Q8 (L200–L215), Q14 (L333–L354), Q22 (L530–L549), Q23 (L550–L581), Q34 (L861–L888), https://raw.githubusercontent.com/ombharatiya/AI-Engineer-Interview-Questions/e080df2/04-rag-and-retrieval/questions.md — **verified** (opened raw).
12. NirDiamant/RAG_Techniques @ `009adba`: `all_rag_techniques/multi_faceted_filtering.ipynb` (cells 0–25), `all_rag_techniques_runnable_scripts/multi_faceted_filtering.py` (L1–L194), `data/customers-100.csv`, `all_rag_techniques/hierarchical_indices.ipynb` (cells 9–17), `all_rag_techniques_runnable_scripts/hierarchical_indices.py` (L60–L110), `data/Understanding_Climate_Change.pdf` (sha256 `1d58a0fa…92669`), custom non-commercial licence — **verified** (raw download; cells read with `json`, 0-based; code not run).
13. Corpus D scope inspection, session scratch scripts session scratch scripts (not course files) over poppler `pdftohtml -xml -zoom 1` and `pdftotext`, 2026-10-17 — **verified locally, approximate** (heading counts and repeated titles match phase_04 I2; chunk counts do not match v0, so only ranges are reported).

### R3 sources
1. "Passage Re-ranking with BERT", Rodrigo Nogueira & Kyunghyun Cho, 2019, https://arxiv.org/abs/1901.04085 — **UNVERIFIED (search-checked only)**. Authors' repo https://github.com/nyu-dl/dl4marco-bert @ `a75f26a` README (results table, data files, BERT-base 34.7) — **verified (opened via raw.githubusercontent.com)**.
2. sentence-transformers docs `docs/cross_encoder/pretrained_models.md` @ tag v6.1.0 (`b0bf399`), https://github.com/huggingface/sentence-transformers/blob/v6.1.0/docs/cross_encoder/pretrained_models.md — **verified** (MS MARCO table, sigmoid note, canonical id). Hardware "V100" — **UNVERIFIED (search-checked only)**.
3. sentence-transformers 6.1.0 wheel (`cross_encoder/model.py` L100–L460, L568–L866; `base/modules/transformer.py` L866–L884, L1138–L1158, L1255–L1260; METADATA), https://pypi.org/project/sentence-transformers/6.1.0/ — **verified (source read)**.
4. Hugging Face model card `cross-encoder/ms-marco-MiniLM-L6-v2`, https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2 — **UNVERIFIED (DNS blocked; mirrors search-checked)**.
5. "Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents", Weiwei Sun et al., EMNLP 2023, https://arxiv.org/abs/2304.09542 — **UNVERIFIED (search-checked only)**. Repo https://github.com/sunnweiwei/RankGPT @ `0d62bc3` (README; `rank_gpt.py` L143–L157, L234–L244) — **verified**.
6. "Found in the Middle: Permutation Self-Consistency Improves Listwise Ranking in Large Language Models", Raphael Tang et al., 2023 (NAACL 2024), https://arxiv.org/abs/2310.07712 — **UNVERIFIED (search-checked only)**.
7. "Large Language Models are Effective Text Rankers with Pairwise Ranking Prompting", Zhen Qin et al., 2023 (NAACL 2024 Findings), https://arxiv.org/abs/2306.17563 — **UNVERIFIED (search-checked only)**.
8. cohere 7.2.0 wheel (`v2/client.py` L555–L624; `v2/types/v2rerank_response*.py`; `types/api_meta_billed_units.py`; `base_client.py` L1165–L1215), https://pypi.org/project/cohere/7.2.0/ — **verified (source read)**. Cohere docs https://docs.cohere.com/docs/rerank — **UNVERIFIED here (DNS blocked)**; foundation §6.2 verified the model ids.
9. Cohere rerank prices: third-party pages (developer.puter.com "Cohere API Pricing", cloudprice.net) — **UNVERIFIED (search-checked only; conflicting units)**.
10. LangChain wheels: `langchain-classic` 1.0.8 (`retrievers/contextual_compression.py`, `document_compressors/cross_encoder_rerank.py`, `listwise_rerank.py`, `cohere_rerank.py`), `langchain-core` 1.6.6 (`cross_encoders.py`, `retrievers.py` L297–L298), `langchain-community` 0.4.2 (`cross_encoders/huggingface.py`, METADATA), `langchain-cohere` 0.6.0 (`rerank.py`, METADATA `cohere<6.0`), https://pypi.org/project/langchain-classic/1.0.8/ etc. — **verified (source read)**.
11. `llama-index-core` 0.14.25 wheel (`postprocessor/llm_rerank.py`, `sbert_rerank.py`, `rankGPT_rerank.py`; `prompts/default_prompts.py` L462–L487; `indices/utils.py` L120–L167), https://pypi.org/project/llama-index-core/0.14.25/ — **verified (source read)**.
12. `BAAI/bge-reranker-v2-m3` facts (bge-model.com table; PromptLayer and other pages) — **UNVERIFIED (search-checked only)**.
13. "BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models", Nandan Thakur et al., 2021, https://arxiv.org/abs/2104.08663 — **UNVERIFIED (search-checked only)**; phase_03 [S16].
14. AI-Engineer-Interview-Questions, Om (ombharatiya), 2026, MIT, `04-rag-and-retrieval/questions.md` Q3, Q10 (L243–L267), Q25 (L609–L625), Q43, Q46, Q48, Q58 (L1552–L1577), https://github.com/ombharatiya/AI-Engineer-Interview-Questions @ `e080df2` — **verified**.
15. NirDiamant/RAG_Techniques @ `009adba`: `all_rag_techniques/reranking.ipynb` (cells 0–30), `reranking_with_llamaindex.ipynb` (cells 0–24), `all_rag_techniques_runnable_scripts/reranking.py` (L1–L173), `helper_functions.py` (L1–L76), custom non-commercial licence — **verified (code not run)**.
16. "Zero-Shot Listwise Document Reranking with a Large Language Model", Xueguang Ma et al., 2023, https://arxiv.org/abs/2305.02156 — **UNVERIFIED (not opened; cited by `LLMListwiseRerank`'s docstring)**.

### R4 sources
1. "The Use of MMR, Diversity-Based Reranking for Reordering Documents and Producing Summaries", Jaime Carbonell & Jade Goldstein, SIGIR '98, pp. 335–336, 1998, https://doi.org/10.1145/290941.291025 (also https://ir.webis.de/anthology/1998.sigirconf_conference-98.43/; companion TIPSTER paper https://aclanthology.org/X98-1025) — **UNVERIFIED (search-checked only)**; the ACM, CMU, LangChain-mirror, Melbourne and ACL hosts were blocked.
2. "Better RAG using Relevant Information Gain" (v1, 2024), retitled "Dartboard: Better RAG using Relevant Information Gain" (v2, Feb 2025), Marc Pickett, Jeremy Hartman, Ayan Kumar Bhowmick, Raquib Ul Alam, Aditya Vempaty, https://arxiv.org/abs/2407.12101; Springer chapter https://link.springer.com/chapter/10.1007/978-3-032-11477-8_6 — **UNVERIFIED (search-checked only)**; arXiv blocked.
3. EmergenceAI/dartboard (official code), https://github.com/EmergenceAI/dartboard, `main` fetched 2026-10-17 via raw.githubusercontent.com: `README.md`, `requirements.txt`, `dartboard.py` (159 lines), `retrieval/do_eval.py`, `retrieval/get_articles.py` (head), `end2end/do_eval.py` (`retrieval/dartboard.py` and `end2end/dartboard.py` are links to `../dartboard.py`) — **verified (opened; code not run)**. No root LICENSE (404). Commit hash not recorded (GitHub API blocked).
4. LangChain `langchain-core==1.6.6` wheel (PyPI, uploaded 2026-09-29): `vectorstores/utils.py` L1–L163, `vectorstores/base.py` L370–L410, L655–L690, L905–L943, L1040–L1060, `vectorstores/in_memory.py` L300–L335, L418–L450 — **verified**.
5. "Novelty and Diversity in Information Retrieval Evaluation", C. L. A. Clarke, M. Kolla, G. V. Cormack, O. Vechtomova, A. Ashkan, S. Büttcher, I. MacKinnon, SIGIR 2008, pp. 659–666, https://doi.org/10.1145/1390334.1390446 — **UNVERIFIED (search-checked only)**; the Waterloo PDF and TREC `ndeval.c` were blocked.
6. `ir-measures==0.4.3` wheel (`providers/pyndeval_provider.py` L9–L93) and the PyPI JSON for `pyndeval` (release dates, MIT classifier), https://pypi.org/project/ir-measures/0.4.3/, https://pypi.org/pypi/pyndeval/json — **verified**.
7. AI-Engineer-Interview-Questions, Om (ombharatiya), 2026, MIT ("Copyright (c) 2026 Om"), @ `e080df2`: `04-rag-and-retrieval/questions.md` Q33 (L833–L857), `12-coding-challenges/17_hybrid_search_and_rerank.py` (L1–L285; `mmr` L134–L157; tests L251–L281), https://github.com/ombharatiya/AI-Engineer-Interview-Questions — **verified (opened via raw.githubusercontent.com)**.
8. "Beyond Independent Relevance: Methods and Evaluation Metrics for Subtopic Retrieval", ChengXiang Zhai, William W. Cohen, John Lafferty, SIGIR 2003 — **UNVERIFIED (not opened; cited from general knowledge for "subtopic recall")**.
9. NirDiamant/RAG_Techniques @ `009adba`, `all_rag_techniques/dartboard.ipynb` (cells 0–26), and `data/Understanding_Climate_Change.pdf` (sha256 `1d58a0fa…92669`), custom non-commercial licence — **verified (opened via raw.githubusercontent.com; code not run; described, not quoted at length)**.
10. Session scratch scripts (not course files): a TF-IDF proxy on `pdftotext` pages, and a toy re-implementation of the upstream Dartboard logic — run 2026-10-17; their numbers are labelled proxy or toy.

### R5 sources
1. "RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval", Parth Sarthi, Salman Abdullah, Aditi Tuli, Shubh Khanna, Anna Goldie, Christopher D. Manning, ICLR 2024, https://arxiv.org/abs/2401.18059 — **UNVERIFIED (search-checked only)**. arXiv and OpenReview were blocked. The 4% (6/150) hallucination figure was seen in a search snippet; the QuALITY/QASPER/NarrativeQA figures and the 2,000-token budget are from memory, UNVERIFIED.
2. Official RAPTOR code, `parthsarthi03/raptor` @ `7da1d48a7e1d7dec61a63c9d9aae84e2dfaa5767` (HEAD via `git ls-remote`), https://github.com/parthsarthi03/raptor. Opened: `raptor/cluster_utils.py`, `cluster_tree_builder.py`, `tree_builder.py`, `tree_retriever.py`, `SummarizationModels.py`, `RetrievalAugmentation.py`, `utils.py`, `requirements.txt`, `README.md`, `LICENSE.txt` (MIT) — **verified**.
3. LlamaIndex RAPTOR pack, `llama-index-packs-raptor` 0.4.2 (2026-04-02), https://pypi.org/project/llama-index-packs-raptor/. Wheel opened: `llama_index/packs/raptor/base.py`, `clustering.py`, LICENSE (MIT, Jerry Liu) — **verified**.
4. `langchain-classic` 1.0.8 (2026-06-10), https://pypi.org/project/langchain-classic/. Wheel opened: `retrievers/multi_vector.py`, `parent_document_retriever.py`, `contextual_compression.py`, `document_compressors/chain_extract.py`, `chains/summarize/chain.py`, `chains/combine_documents/map_reduce.py`, `reduce.py` — **verified**.
5. `langchain-core` 1.6.6, https://github.com/langchain-ai/langchain/tree/langchain-core==1.6.6/libs/core. Opened: `messages/base.py`, `load/serializable.py` (L220–L225), `vectorstores/in_memory.py` (L291–L331) — **verified**.
6. `langchain-community` 0.4.2 (2026-05-22), https://pypi.org/project/langchain-community/. Wheel opened: `vectorstores/faiss.py` (L387–L445, L1173–L1200, L1283–L1300), `docstore/in_memory.py` — **verified**.
7. scikit-learn 1.9.1, `sklearn/mixture/_gaussian_mixture.py` (L768–L773, L945–L980), https://github.com/scikit-learn/scikit-learn/blob/1.9.1/sklearn/mixture/_gaussian_mixture.py — **verified**.
8. umap-learn 0.5.12, `umap/umap_.py` (L266, L1667–L1687, L1953) at tag `release-0.5.12` (`cdb0eeb`), https://github.com/lmcinnes/umap; PyPI JSON for umap-learn, numba (0.66.0–0.68.0 requires_dist), llvmlite, pynndescent, hdbscan — **verified** 2026-10-17.
9. HippoRAG 2, OSU-NLP-Group, README and `images/intro.png` @ `d5c8329`, https://github.com/OSU-NLP-Group/HippoRAG — **verified (figure read; a competitor's own comparison; metric not stated in the figure)**.
10. MultiCube-RAG (arXiv 2602.15898), Quest-GNN / "Question-Adaptive Graph Learning for Multi-hop RAG" (arXiv 2510.11541), SUBQRAG (arXiv 2510.07718) — **UNVERIFIED (search-checked only)**; directions only, numbers not used.
11. "From Local to Global: A Graph RAG Approach to Query-Focused Summarization", Darren Edge et al., 2024, https://arxiv.org/abs/2404.16130 (04 Source C #43) — **UNVERIFIED (not opened)**; the approach is summarised from AIQ 04 Q39.
12. AI-Engineer-Interview-Questions @ `e080df2`, `04-rag-and-retrieval/questions.md` Q2, Q5, Q23, Q29, Q39, Q50 (MIT, "Copyright (c) 2026 Om"), https://github.com/ombharatiya/AI-Engineer-Interview-Questions — **verified**.
13. Upstream `NirDiamant/RAG_Techniques` @ `009adba`: `all_rag_techniques/hierarchical_indices.ipynb` (cells 0–18), `all_rag_techniques/raptor.ipynb` (cells 0–34), `helper_functions.py` (L1–L20, L285–L321), `all_rag_techniques_runnable_scripts/hierarchical_indices.py` (all), `raptor.py` (all) — **verified (read, not run; custom non-commercial licence, described not quoted)**.
