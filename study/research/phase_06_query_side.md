# Phase 6 research: Query-side improvements → v3.x

**What this is:** the research and gap audit for Phase 6 (Q1 query transformations: rewrite, step-back, decomposition; Q2 HyDE vs HyPE), done 2026-10-18 by Claude in a Claude Code cloud session.
**What this is not:** lessons or code. Nothing in the course was changed, nothing was installed, and no LLM, embedding, rerank or tracing API was called.

**How it was checked, and what could not be checked.** This session ran in a cloud container, like the Phase 4 and 5 sessions. Several inputs that RESEARCH_PROMPT §3 lists were **not available**. Read every label with that in mind.
- **Book (*RAG Made Simple*): not present.** No book page was opened. Every book citation (Ch5, Ch6, Ch11, Ch12) comes from 02, 03, 04 and 08 and is labelled "per 04, not re-opened" (UNVERIFIED here). No book text was read, so none can have been copied.
- **AI Eval book (AE), interview repo (AIQ), `upstream/RAG_Techniques`, `CLAUDE.md`, `.claude/skills/`: not present.** The notebook cells and script lines for Q1/Q2 are cited from 04 and 03 and are UNVERIFIED here. Skill methods are applied as `LLMOPS_FOUNDATION.md` and `phase_03_measurement.md` describe them. Interview questions come from general practice, not from AIQ.
- **Network:** `arxiv.org` is blocked (DNS failure). Papers were therefore checked through web-search summaries of the paper pages, the ACL Anthology and ICLR listings, labelled **"search-checked only"**. Library behaviour was read from raw GitHub source (LangChain `master`, LlamaIndex `main`), labelled **verified (source, `master`/`main` on 2026-10-18)**; those branches move, so re-check the pinned release before quoting a default.
- **Corpus D measurements:** none made here. All Corpus D numbers come from the existing `sources/verification/R1/R1_FACTS.md` (local runs; not re-run) or from 06's draft seeds, and are labelled so.
- **A local follow-up pass is needed** before any Phase 6 lesson is written: open Ch5/Ch6/Ch11 pages, read the notebook cells, open the papers' result tables, and load the project skills named in each §9. That is a checking pass, not new research.

**Citation keys.** Book: `Ch5 p.4/14` (per 04). Repo cells: `notebook cell N` (0-based, per 04). External sources: **[Q1-Sn]** and **[Q2-Sn]**, listed at the end. Error ids: `Q1-E1` …

---

## Summary (read this first)

**The 5 most important gaps across the phase**
1. **There is almost no headroom on Corpus D, so v3.x cannot show a win as planned.**
   - On the 8 answerable draft seeds, dense retrieval already has CE@4 = Hit@4 = 8/8 (`R1_FACTS.md` S4). Only the first-relevant rank moves: D-007 (the multi-hop item) puts its first evidence at rank 3 for dense.
   - The target categories, vocabulary-mismatch (6) and multi-hop (4), have about 10 items before the dev/test split. A paired test on 3–4 test items cannot resolve anything.
   - **Fix:** a **headroom gate** before any call is spent: after v2.x, count the dev items whose evidence is *not* in the top-4 but *is* in the top-20 or top-50. If fewer than about 5, pre-register "inconclusive" as the expected verdict, and grow the slices (a rule-built paraphrase set; hand-written multi-hop and compound questions).
2. **Both cards compare the wrong things unless the pipeline contract is fixed.** v3.0 and v3.1 sit on top of the v2.x champion (hybrid, rerank, filter, MMR). A rewritten query must be (a) retrieved by the **same** pipeline, (b) **reranked against the original question**, and (c) answered from the **original question**. None of the three is written down in 06. Without them, "rewrite beats champion" can mean "the reranker saw a different query".
3. **Merging several result lists is not taught before Q1 uses it.** Decomposition and step-back need rank fusion. R1 teaches it, but R1's tracker status is only `exposed` (O1-Q09, score 2). Q1 must teach the *query-side* part itself: depth per sub-query, dedup by chunk id, equal weight versus a weight for the original query, and a cap on the merged list.
4. **The repo notebooks never retrieve, and HyDE never generates** (04 DV-16, DV-18, per 04). The course must build the missing halves, and add a **raw-query baseline** next to every arm. 04 also lists a primed few-shot example in the decomposition prompt (DV-17); the leakage check in 06 §6.3 must cover transform prompts as well as judge prompts.
5. **HyDE's evidence is weak for our setting.** The original gains are over an *unsupervised* Contriever with a 2022 GPT-3 [Q2-S1]. A large 2023 study of 11 expansion methods on 24 retrievers found that expansion helps weak retrievers and often hurts strong ones [Q2-S4]. Our default dense leg is Cohere `embed-v4.0` plus (after v2.x) BM25 and a reranker, which is a strong stack. Also, the climate PDF is a topic the LLM already knows, so a win on Corpus D partly measures the model's world knowledge, not the technique. Corpus T (technical PDFs) is the fairer test.

**Tools to add, across the phase** (details in §10 of each concept; install nothing yet)
- Nothing new for the lessons, verify notebooks or apply-it tools: plain Python, `numpy`, `rank-bm25`, `cohere`, `groq`, `scipy`, all already installed.
- LLMOps notebooks (foundation §11): `langchain-core`, `langgraph` (only for a decomposition fan-out demo, optional), `langchain-classic` (for reading and parity tests of `MultiQueryRetriever`, `HypotheticalDocumentEmbedder`, `create_history_aware_retriever`), `langsmith` (climate corpus only), `arize-phoenix-otel`.
- `anthropic` only if Yash wants a Claude arm (Haiku 5.5 for rewrites, Opus 5.5 for hard decomposition). Optional.

**Decisions Yash must make** (each answerable in a word)
1. Add a **paraphrase/compound probe set** to grow the v3.x slices (rule- and hand-built, about 20 items)? **yes** / no (no = v3.x on Corpus D is expected to end "inconclusive").
2. Run Q2 on **both** Corpus D and the first Corpus T documents once chosen (DEC-3), because D is knowledge-contaminated? **yes** / no.
3. Add a **Claude Haiku 5.5 arm** for the rewrite/HyDE generation (about $0.04 per full run)? **yes** / no (Groq only).
4. Add a small **conversational follow-up** probe (the "condense question" case) as a Q1 elective, since 02 has no concept id for it? **yes** / no.
5. For HyDE with Cohere, test the passage as `search_document` as well as `search_query` (two arms)? **yes** / no.

**Size of the build work**
- **Q1: L.** Three strategies, a merge stage, an intent-drift check, a per-category gate, a headroom gate, and the most LLM calls of the phase (about 700 per full grid before caching; §9).
- **Q2: M.** One strategy, but it needs a baseline, an index-time comparison with I6 (which may not be built), and a contamination check.

---

## Concept Q1: Query transformations: rewrite, step-back, decomposition (U, project v3.0)

### 1. Sources checked

**Book (not present; per 02/03/04, not re-opened, UNVERIFIED here):**
- Ch5 p.4–6/14 (rewriting), p.6–8/14 (step-back, sketch p.6/14 and p.8/14), p.8–10/14 (decomposition, sketch p.10/14), p.10–11/14 (choosing; composition p.11/14); Ch12 p.12/14 (multi-query expansion, per 02).
- 04's step table for Ch5 says searching, merging and deduplicating are **missing** from the notebook, and generation with the original question is **missing** (04 Ch5 rows 4–5).
- 08 L40 records the book's rule that the *original* question drives the final answer (Ch5 p.4–5/14, p.10/14).

**Repo (per 04, not re-opened):** `query_transformations.ipynb` cells 6, 8 (rewrite), 10, 12 (step-back), 14, 16 (decomposition); `rs/query_transformations.py` L14–L61 and the printing-only `run()` L104–L124. DV-16: nothing is retrieved. DV-17: the decomposition prompt carries a few-shot example built on the demo query, and the parser keeps an echoed "Original query" line. Outdated: `langchain.prompts` import (cell 4) and a hard-coded `gpt-4o` (cells 6, 10, 14) (04).

**Existing course files (read):** `02` Q1 card (L740–L753); `03` rows L44, L46, L478–L479, L541, L630–L632, L751 and the evidence line L862; `04` Q1 row (L179) and the Ch5 table (L410–L425); `06` v3.0 card (L630–L639), §6.2 categories and §6.7 draft seeds; `08` L40, L91, L221; `study/research/LLMOPS_FOUNDATION.md` in full; `study/reading/R1_hybrid_fusion.md` (RRF section, `k = 60`, 0-based vs 1-based ranks); `sources/vai/L10-L18` and `L24-L27` (the "condense question" fast-track probe; VAI L15 has no rewrite step); `sources/verification/R1/R1_FACTS.md`; `phase_04_indexing.md` (I6); `phase_05_retrieval.md` (stage contract, R1/R3 LLMOps plans); `progress/concept_tracker.csv` (Q1 and Q2 `not_started`; R1 `exposed`; M5 `exposed`; R3, P4, C4 `not_started`).

**Existing Q1 lesson, reading, questions, lab:** none. Only the card and the `labs/Q1_query_transform_lab.ipynb` name in 02.

**AE book / interview repo:** not present. No claim here relies on them.

**External sources (8; list at the end):** [Q1-S1] Press et al. 2022 (Self-Ask); [Q1-S2] Zheng et al. 2023 (Step-Back); [Q1-S3] Ma et al. 2023 (Rewrite-Retrieve-Read); [Q1-S4] Trivedi et al. 2023 (IRCoT); [Q1-S5] Rackauckas 2024 (RAG-Fusion); [Q1-S6] Jagerman et al. 2023; [Q1-S7] LangChain `MultiQueryRetriever` and `create_history_aware_retriever` source (verified); [Q1-S8] LlamaIndex `DecomposeQueryTransform` and `LLMQuestionGenerator` source (verified). Q2's [Q2-S4] (Weller et al.) also bears on Q1.

### 2. Gap audit

Yash's studied status (tracker, 2026-10-08): nothing in Phase 6 is started. P4, C4, R3 are `not_started`; R1 and M5 are `exposed` only. "Written" is not "studied", so most bridge ideas below need a short in-place explanation.

| # | Idea | Used where | Taught before use? | Owner | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | **Vocabulary mismatch** (question words ≠ document words), and why a rewrite can help | Whole concept; v3.0 "Problem" | Partly: P2 (IR framing), P4, R1 §1 (both blind spots) | P2 / R1 | no / exposed | bridge | One paragraph with the course's own D-006 example (solar panels vs "floating solar farms … water bodies"). Say what a rewrite can and cannot add |
| 2 | **Intent drift**: a rewrite changes the question | "When not to use"; guard metric | Missing | **Q1** | no | core | Define drift; show an exact-term question ("Kigali Amendment") rewritten away from its key term; add a check that the rare token survives |
| 3 | **Original question drives the answer**; transformed queries only drive search | Generation step | Missing in the notebook (DV-16); stated in book (per 08) | **Q1** | no | core | A rule plus a one-line trace field (`answer_query == original`) |
| 4 | **Three strategies** and what each adds (sharpen, broaden, split) | Core | Book; notebook strings only | **Q1** | no | core | One table: input, output, calls, searches, failure it targets |
| 5 | **Fusing several ranked lists** (RRF), dedup by id | Decomposition, step-back, multi-query | R1 (written, `exposed`) | R1 | exposed | bridge | Reuse `fuse_rrf` from R1. Teach only the query-side choices: equal weights, original query included or not, depth per list, cap |
| 6 | **Retrieval depth per sub-query** and the final cut to k | Merge stage | Missing | **Q1** | no | core | Depth 20 per list, merge, cut to the pool, rerank, cut to 4. State why a short list per sub-query loses evidence |
| 7 | **Where the rerank query comes from** | v2.1 champion under v3.0 | Missing (06 silent) | **Q1** (with R3) | no | core | Rerank against the original question. Explain why: the transformed query may hide the user's intent |
| 8 | **Parsing a list from an LLM** (sub-queries) | Decomposition | Missing; notebook parse bug (DV-17) | **Q1** | no | core | Ask for JSON (`json_schema` or `json_object`); fall back to line parsing; cap at 4; drop empties, duplicates and echoes. Log parse failures |
| 9 | **Prompt priming / few-shot leakage** | Decomposition prompt (DV-17); eval fairness | 06 §6.3 covers judge prompts only | M1 / **Q1** | no | bridge | Few-shot examples come from the learner's *non-eval* questions; extend the 06 §6.3 8-word leakage check to `prompts/rewrite_*`, `step_back_*`, `decompose_*` |
| 10 | **Cost and latency model**: calls, extra searches, critical path | "Compute the added latency and calls" (outcome) | Missing | D2 later; **Q1** now | no | bridge | A table per strategy: LLM calls, searches, embed calls, rerank calls. Sequential vs parallel retrieval |
| 11 | **Headroom gate** (is there anything to fix?) | Every v3 run | Phase 5 introduced it for v2.x | M4 / M5 | exposed | bridge | Count items that fail at k = 4 but have evidence in the top 20–50. Pre-register "inconclusive" |
| 12 | **Per-category reporting and a regression guard** | Experiment; "only the failing categories" | M2 / M4 (not studied) | M2 / M4 | exposed (M2 only) | bridge | Show CE@4 per category with n. Warn that n = 4–6 per category is anecdote (06 §9.4) |
| 13 | **Which categories to target** (a router decides) | "Applied only to failing categories" | Missing; A1 owns routing | A1 | no | next | Q1 *measures* per category and states a rule. It does not build a router. Link to A1 |
| 14 | **Multi-hop needs sequential retrieval** (sub-query 2 depends on answer 1) | Decomposition limits | Missing | **Q1** | no | core | Distinguish *parallel* sub-queries (what the book teaches) from *iterative* retrieval (IRCoT, A5 next). Use D-007 as the example |
| 15 | **Composition** of strategies (decompose then rewrite) | Book p.11/14 | Missing in the notebook | Q1 | no | next | One short paragraph and a combinatorics warning (arms multiply). Not built |
| 16 | **Conversational follow-up rewriting** ("condense question") | VAI L15/L26; 02 reviewer note L1234 | No concept id | Q1 (elective) | no | next | A short optional block; decide via question 4 (§11) |
| 17 | **Model choice per step**: small fast model for rewrite, larger for decomposition plans | LLMOps plan | Foundation §6.4 | foundation | n/a | bridge | State the tier rule; test Groq against Haiku only if Yash agrees |
| 18 | **Caching/replay of LLM transforms** | Reproducibility | Foundation §2 | foundation | n/a | bridge | A transform is keyed on the original query + prompt version + model + parameters, so reruns are identical |
| 19 | **Reasoning-model behaviour** (`gpt-oss-20b` spends output on reasoning; may return an empty reply at a small cap) | Every rewrite call | P1 / C5 (D.6 per foundation) | P1 | studied-ish (P1 written, not logged as studied) | bridge | Set `reasoning_effort=low` and `max_completion_tokens` high enough; check `finish_reason`; count empties |
| 20 | **Query-time metrics must be per-question paired** | Evaluation | M4 | M4 | no | bridge | Paired differences per `qid`; the bootstrap CI; exact sign test for tiny slices |
| 21 | **Embedding `input_type`** for each transformed query | Embedding the rewrite | C3 / P4 | C3 | no | bridge | Every transformed query is a *query*: `search_query`. (HyDE differs; see Q2) |
| 22 | **Error analysis bucket names** (vocabulary-mismatch, multi-part, exact-term) | Which items count as "still failing" | M5 | M5 | exposed | bridge | Use the M5 buckets from v0.1/v2.x traces; do not invent a new taxonomy |

### 3. Quiz coverage

No question file exists. Needed question titles (R = recall, A = application, T = transfer, I = interview):
- **R1** Name the three transformations and say what each one changes in the query.
- **R2** Which question does the final answer use, the original or the transformed one, and why?
- **R3** How many LLM calls and searches does decomposition into 3 sub-queries add?
- **A1** Given a chunk list per sub-query, merge them with RRF and read off the top 4 (toy numbers).
- **A2** Given a question and its rewrite, decide whether the rewrite drifted (rare term lost; scope changed).
- **A3** Choose the strategy for each of five questions and say why (one exact-term, one vague, one compound, one multi-hop, one already clear).
- **A4** Your rewrite raised CE@4 on vocabulary-mismatch and lowered it on exact-term. What do you report, and what do you do next?
- **T1** A multi-hop question needs the answer to part one to build part two. Why does parallel decomposition fail, and what would you use instead?
- **T2** Estimate the added p95 latency and cost per query of your chosen strategy.
- **I1** "When would you not use query rewriting?" **I2** "How do you evaluate a query transformation?"

Every key point must be answerable from the Short depth. Draft the Short reading with an explicit line for each of: the three strategies, the original-question rule, the merge rule, the drift check and the cost table.

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| Q1-E1 | 06 v3.0 card | No rule for which query the **reranker** and the **generator** see. A rewrite that is reranked against itself hides drift | Add: retrieval uses transformed queries; rerank and generation use the original question |
| Q1-E2 | 06 v3.0 card; 04 "Build yourself" | "sub-query lists merged with RRF" gives no list depth, no weights, and no statement whether the original query is also searched | Add depth 20 per list, equal weights, original always included as an arm-independent extra list (pre-register as a variable) |
| Q1-E3 | 06 v3.0 "Experiment" | "Run on the failing categories **and** on all categories" with 3 arms plus the baseline multiplies arms. 06 §9.4 limits comparisons, and the card names no multiple-comparison rule | Pre-register the arm count; use dev for selection and test once; count arms tried in `TEST_LOG.md` (as Phase 5 did) |
| Q1-E4 | 06 v3.0 "Cost" | "+1 LLM call per query" is right for rewrite and step-back; decomposition is also +1 call **but +n retrievals and +n query embeddings**; step-back adds +1 search (04/03 L631–L632 say this) | Replace with the per-strategy table in §9 |
| Q1-E5 | 02 Q1 card, Pre line | `Pre: R3, M5`. 03 L479 says the R3 edge is a *lab-baseline* edge, and that the real conceptual dependency is R1 (merging). The card omits R1 | Add R1 to the Pre line of 02 (03 already lists R1) |
| Q1-E6 | 04 Q1 row | The experiment names CE@k, but Q1's own failure bucket (vocabulary-mismatch) can also be fixed at index time (I5, I6) and by R1 hybrid. The card does not say Q1 should run on the *post-v2.x* failures only | Add a "residual failures only" statement with the headroom gate |
| Q1-E7 | Foundation §12, row "6 · Q1–Q2" | Lists "+1 call/query" only | Add the per-strategy counts from §9 below |
| Q1-E8 | 04 Ch5 "Outdated" | `langchain.prompts` and `gpt-4o` are noted. Not noted: current `langchain` 1.x moved chains and retrievers to `langchain-classic` (foundation §9.4) | Mention in the LLMOps notebook, not in the lesson |
| Q1-E9 | 02 reviewer note L1234 | Conversational rewriting is "folded into Q1 as a fast-track probe" but there is no lesson slot, concept id or lab for it | Decide with question 4 (§11) |

### 5. What the research says

**Keep the study separate from the interpretation.** Papers were seen through web-search summaries (arXiv blocked). Numbers marked "search-checked" were not checked against the paper's tables.

**[Q1-S2] Step-Back Prompting (Zheng et al., Google DeepMind, ICLR 2024; search-checked only).**
- **Study:** ask the model for a higher-level question first, answer that for principles, then answer the original. Tested with PaLM-2L on reasoning, TimeQA and MuSiQue, with and without retrieval.
- **Result:** the search summary gives MuSiQue 35.5% (baseline), 39.6% (RAG), 42.6% (step-back), 42.8% (step-back + RAG), and a 27% gain on TimeQA. The abstract does not say if gains are absolute or relative (UNVERIFIED). For TimeQA the authors report that 45% of remaining errors were still retrieval failures.
- **Limits:** the retrieval gain from adding RAG on top of step-back is tiny (42.6 → 42.8). The abstraction is used mostly to *prompt the reader*, not only to search. Models and tasks differ from ours.
- **For us:** the book's version (search with the step-back question *and* the original) is a retrieval adaptation, and the paper does not test it on a 97-chunk corpus.

**[Q1-S3] Rewrite-Retrieve-Read (Ma et al., EMNLP 2023; search-checked only).**
- **Study:** add a rewrite step before retrieval. Variants: an LLM rewriter, and a small T5-large rewriter trained with reinforcement learning from the frozen reader's feedback. Readers: ChatGPT and Vicuna-13B. Open-domain and multiple-choice QA, with a web search engine as the retriever.
- **Result (per summary):** rewriting improves downstream QA; a small trained rewriter works. The exact scores were not seen.
- **Limits:** a *web search engine* retrieves, not a private dense index; the rewrite targets keyword search engines. The setting differs from a small private corpus.

**[Q1-S1] Self-Ask (Press et al., Findings of EMNLP 2023; search-checked only).** Models answer single-hop facts far better than compositions of them, and the gap does not shrink with scale. Self-Ask makes the model write follow-up questions and answer each; plugging in a search engine for the follow-ups raises accuracy further. This is the paper-level justification for decomposition. The ">10 points" figure in one secondary summary was **not** confirmed.

**[Q1-S4] IRCoT (Trivedi et al., ACL 2023; search-checked only).** For multi-step questions the right query depends on what was already found, so one-shot retrieval fails. Interleaving retrieval with reasoning steps raised retrieval recall by up to 21 points and QA by up to 15 points (GPT-3; HotpotQA, 2WikiMultihopQA, MuSiQue, IIRC), with gains also on Flan-T5-large. **For us:** parallel decomposition (the book's version) cannot do this; *iterative* retrieval is A5's territory (next).

**[Q1-S5] RAG-Fusion (Rackauckas, IJNLC 2024; search-checked only).** Multi-query plus RRF at Infineon, judged by manual review. The answers looked more accurate and complete, but some drifted off topic when generated queries strayed. The evidence is **qualitative, small and unreplicated**. Use it as a source of the drift warning, not as proof of a gain.

**[Q1-S6] Jagerman et al. 2023 (search-checked only).** LLM query expansion by prompting (zero-shot, few-shot, chain-of-thought), tested on MS MARCO and BEIR; chain-of-thought prompts gave the most expansion terms and beat traditional expansion. The setting is keyword retrieval (BM25), where extra terms help directly.

**[Q2-S4] Weller et al. 2023 (EACL Findings 2024; search-checked only).** 11 expansion techniques, 12 datasets, 24 retrievers: the weaker the retriever, the larger the gain; strong retrievers often lose. Expansion adds some useful information but also noise, which creates false positives at the top. Guidance: use expansion for weak retrievers or when the target data differs from the training data. **This is the most relevant study for v3.0:** after v2.x, our retriever stack is strong.

**Library defaults (verified, source `master`, 2026-10-18).**
- **[Q1-S7] LangChain `MultiQueryRetriever`:** the default prompt asks for *three* reworded versions, separated by newlines. The count is *not enforced in code*. `LineListOutputParser` splits on newlines and drops empty lines but keeps bullets and numbering. **`include_original=False` by default**: the original query is *not* searched. Results are merged by `unique_union`: first occurrence kept, retrieval order preserved, equality check is quadratic, **no RRF and no scores**. The sync path runs sequentially; the async path runs concurrently. `verbose=True` logs the generated queries.
- **[Q1-S7] `create_history_aware_retriever`:** with an empty `chat_history` the raw input goes straight to the retriever and **no LLM call is made**; otherwise `prompt | llm | StrOutputParser | retriever`. The prompt must include `input`.
- **[Q1-S8] LlamaIndex `DecomposeQueryTransform`:** a *single-step* transform: it turns a query into **one** sub-query, given an index summary. It is not the 2–4 sub-queries of Ch5. `LLMQuestionGenerator` (used by the sub-question engine) asks the LLM for a list of `SubQuestion` objects, each tied to a tool, and parses them with an output parser.

**Current practice (2024–2026).** The common production pattern is a *small, cheap model* for rewriting, run only when needed (a classifier or a confidence rule decides), with caching. Many teams keep the original query as one of the retrieved lists and fuse. The source for this paragraph is the pattern shared by the library defaults above and the papers; no single production write-up was opened (UNVERIFIED as a "common practice" claim).

**Pitfalls and failure modes (evidence level in brackets).**
- Rewrites drop the rare token that BM25 or exact-match needs [paper-level: RAG-Fusion drift warning; Q2-S4 noise effect]. Demonstrate on D-008.
- Decomposition fails on questions that are not compound; it adds searches and noise [Q2-S4 for the noise mechanism].
- Parallel decomposition cannot answer multi-hop questions whose second part depends on the first [Q1-S4].
- A reasoning model can return an empty reply at a small token cap (foundation §2.7, C5 D.6) [project evidence].
- Few-shot examples borrowed from eval questions inflate scores (06 §6.3; DV-17) [project evidence].

**How to evaluate.**
- **Retrieval (primary):** CE@4 per category on dev; MRR@10 and Hit@20 as diagnostics; the **pool metric CE@pool** (evidence in the merged pool before the cut) to separate "retrieved but ranked low" from "never retrieved".
- **Guards:** exact-term and factual-single-span CE@4; **drift rate** (rare query tokens absent from the rewrite); mean context tokens; LLM calls and cost per query; p95 latency.
- **Answers (secondary, separate block):** deterministic checks (citation page-hit, abstention string, EM/F1), plus a hand-read sample of about 10 answers per version. No LLM judge before the end batch (D-10).
- **Baselines:** the v2.x champion (primary), and the raw question searched with the same pipeline. For decomposition, also **"original + rewrite"** versus **"rewrite only"**.
- **Statistics:** paired per `qid`; exact sign test where n < 10; bootstrap CI otherwise (M4).

**Interview angle (general knowledge, not from AIQ).** (1) What are query rewriting, step-back and decomposition, and when does each help? (2) Why keep the original query? (3) How do you merge results from several sub-queries? (4) How would you measure whether query rewriting helps, and what could go wrong? (5) What is the latency and cost cost, and how do you cap it?

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).**
1. A single user question can fail retrieval because its words differ from the document's words, or because it asks for several things at once.
2. Query transformation fixes this by asking an LLM to rewrite the question (sharpen), to ask a broader question (step-back), or to split it into 2–4 smaller questions (decompose), and then searching with the new queries.
3. The new queries only change *what you search for*; the reranker and the final answer still use the **original** question, so the user's intent is not lost.
4. Several searches give several ranked lists, which you merge by rank (RRF) and deduplicate by chunk id.
5. It costs at least one extra LLM call and sometimes several extra searches per question, it can drift away from the user's intent, and on a strong retriever it often does not help, so you apply it only to the questions that still fail.

**The theory in one read (idea list).**
1. Vocabulary mismatch and compound questions (the two failures).
2. Three strategies: sharpen, broaden, split (input → output).
3. The original-question rule.
4. Intent drift, and the rare-token check: `drift = 1 − |rare tokens of Q that survive in Q′| / |rare tokens of Q|`.
5. Merge by RRF: `score(d) = Σ_lists 1 / (k + rank_list(d))`, `k = 60`, ranks from 1 (bridge to R1).
6. Depth: each sub-query returns `depth` chunks; the merged pool is cut to `pool`; rerank; cut to `k`.
7. Cost model: `calls = 1 (LLM) ; searches = 1 + n ; embeds = 1 + n ; reranks = 1`; latency `≈ t_LLM + max(t_search_i) + t_merge + t_rerank` if parallel.
8. Parallel versus iterative multi-hop.
9. The headroom gate: `headroom = #{dev items: evidence not in top-4 but in top-N}`.
10. Per-category gating (measure; do not route; A1 owns routing).
11. When not to use: already-clear questions; exact-term questions; strong retriever; tight latency.

**Formula-sheet items.** RRF; drift ratio; calls/searches/embeds per strategy; added-latency bound; headroom count; CE@pool.

**Step-by-step outline (running example).** Corpus D (the course climate PDF), 97 chunks, the 10 draft seeds. Walk three questions through all three strategies:
- **D-006** (vocabulary mismatch: "solar panels on lakes or reservoirs" vs "floating solar farms … on water bodies"): rewrite and show the new wording.
- **D-007** (multi-hop: supreme body of the convention behind the Kyoto Protocol and the Paris Agreement; evidence p.10 + p.29): decompose; show why the second sub-query depends on the first; show the merged list.
- **D-008** (exact term: "Kigali Amendment"): show a rewrite that loses "Kigali" and the drift check catching it.
- Steps: the failure → three prompts → the transformed queries → the searches → the merge → the original-question rerank → the answer → the cost table → the drift check.
- *Why Corpus D:* it is the project's v0 corpus and the seeds already exist. Real numbers for D-006…D-008 under dense/BM25/RRF come from `R1_FACTS.md`; the transformed outputs are **recorded** in the verify notebook (once) and then replayed.

**Visuals (each earns its place).**
1. *Pipeline diagram:* original question → transform → N searches → merge → rerank(original) → generate(original). Shows that the original question stays on both ends.
2. *Three-column strategy table with example outputs* (D-006/D-007/D-008). Shows what each strategy produces.
3. *RRF merge worked chart:* three lists and the merged order. Shows why dedup by id matters.
4. *Drift bar:* rare tokens kept versus lost per rewrite. Shows the failure.
5. *Cost/latency waterfall:* LLM call, parallel searches, rerank. Shows the critical path.
6. *Per-category delta chart (Plotly) with n labels:* champion versus arms. Shows that wins are local and noisy.

**Full-only.** Composition of strategies; the RAG-Fusion variant; iterative retrieval sketch (IRCoT); the conversational condense-question block; prompt-design variants; the multiple-comparison argument.

### 7. Verify notebook plan

`study/notebooks/Q1_query_transform_verify.ipynb`. It stays framework-free.
- **Recomputes:** RRF merge on toy lists (hand-checkable); the drift ratio on recorded rewrites; the cost table; CE@pool and CE@4 per seed for the baseline and each strategy; the headroom count from the existing v2.x champion's traces.
- **Data:** Corpus D snapshot, the 97-chunk index (C3 cache), the 10 draft seeds, `R1_FACTS`-style fixtures.
- **LLM calls (recorded once, then replayed):** 3 strategies × 10 seeds = **30 Groq calls** (rewrite, step-back, decomposition). Add 8–10 calls if the notebook also shows the failing D-008 rewrite under a naive prompt. **Query embeddings:** about 30–60 texts in 1–2 Cohere `search_query` calls (≤96 per call). **Offline with MiniLM** as the fallback; the numbers will differ, so the notebook prints which embedder it used.
- **Runtime:** under 1 minute in replay; the recording run takes about 30 calls at ≤30 requests/min, so about 1–2 minutes, plus the 8K tokens/minute limit (foundation §2.5), so allow 3 minutes.
- **Charts:** Plotly bar of first-evidence rank per arm; the RRF merge table.
- **Pass/fail check:** the merged list contains no duplicate chunk ids, and `answer_query == original` for every row.

### 8. Apply-it tool plan and real-world checklist

`study/tools/query_transform_check.py` (**input:** a JSONL of Yash's questions with optional expected pages, and a PDF or the corpus snapshot; **output:** a Markdown report and a CSV of per-question results).

**What it does.** For each question it records the baseline top-k, generates the three transforms (cached), searches, merges, and reports where the expected evidence ranks under each arm. It never overwrites the baseline.

**Recommendation logic.**
- If baseline CE@4 is already 100% on the user's set: "no headroom; do not add a query step."
- If failures have evidence in the top-20/50: "try rewrite on the failing questions only"; if the failing questions are compound: "try decomposition."
- If any rewrite loses a rare token: "protect exact-term questions; do not apply to them."
- If a transformation helps fewer than about 3 questions or hurts any on the guard category: "not worth the extra call."

**Real-world checklist (8–12 checks).**

| # | Check | Auto / manual |
|---|---|---|
| 1 | Baseline CE@4 and Hit@20 on your questions (headroom count) | auto |
| 2 | Share of failing questions whose evidence is in the top-20/50 | auto |
| 3 | Each question labelled sharp / vague / compound / multi-hop | manual (label), auto (count) |
| 4 | Rewrite drift rate (rare tokens lost) | auto |
| 5 | Rewrite helps vague questions without hurting sharp ones (per-category CE@4) | auto |
| 6 | Decomposition returns 2–4 clean sub-queries (parse failure rate) | auto |
| 7 | Merged pool has no duplicate ids and the original query is included | auto |
| 8 | Answer uses the original question (trace field) | auto |
| 9 | Added calls, searches and p95 latency per question | auto |
| 10 | Cost per 1,000 questions with your chosen model | auto |
| 11 | Read 10 transformed queries for sense | manual |
| 12 | Multi-hop questions: does the second hop need the first answer? | manual |

### 9. LLMOps notebook plan

`study/llmops/notebooks/Q1_query_transform_ops.ipynb`: v3.0 as a traced, replayable experiment (foundation §12 row "6 · Q1–Q2"). **There is an LLM in the mechanism.**

**Framework build (after the plain-Python lesson).**
- A LangChain `Runnable` chain `prompt | CachedChatModel | parser` per strategy, using the foundation's adapters (§9.3), so nothing bypasses the cache.
- Retrieval: the course's retriever (champion pipeline) wrapped as a `BaseRetriever`.
- Merge: a small RRF function (course code), with a **parity test** against `langchain-classic` `MultiQueryRetriever` (`unique_union`, `include_original`) showing the differences: the library has no RRF and does not search the original by default [Q1-S7].
- Decomposition fan-out: optional **LangGraph** (`Send`-style parallel nodes) only if the notebook demonstrates parallel searches; otherwise `asyncio.gather` is simpler (foundation §9.1 rule: a graph only for cycles, runtime branches or checkpoints). Recommendation: **no LangGraph here.**
- **Mapping to the mechanism:** `prompt | llm | parser` → "transform"; retriever → "search"; RRF → "merge"; reranker with the original query → "rerank".
- **Defaults to demonstrate and override:** `MultiQueryRetriever` three queries not enforced, `include_original=False`, unique-union without scores; `create_history_aware_retriever` skips the LLM when history is empty; `ChatGroq` temperature 0.7 if the official class is shown (foundation §9.2).

**External calls (all cached; replay mode runs with no key).**

| Call | Count (full grid) | Notes |
|---|---|---|
| Groq `openai/gpt-oss-20b`, `reasoning_effort=low`, rewrite | 1 per question × ≈ 55 questions | ≈ 55 calls |
| Same, step-back | ≈ 55 | |
| Same, decomposition | ≈ 55 | |
| Prompt-variant arms (one alternative prompt each, optional) | ≈ 165 | pre-register or skip |
| Cohere `embed-v4.0` `search_query` | ≈ 55 × (1 + 1 + 2 + 3 sub-queries ≈ 7 texts) ≈ 385 texts → ≈ 5 calls of ≤96 | shared across arms |
| Cohere rerank (if the champion uses it) | 1 per question per arm × 4 arms × ≈ 55 ≈ 220 searches | price UNVERIFIED (foundation §6.2); depends on the champion |
| Groq generation of final answers, adopted arm only | ≈ 35 (dev + test of the adopted arm) | ≈ $0.01 as in Phase 5 |
| Claude (optional Haiku 5.5 arm) | the same ≈ 165 transform calls | ≈ 165 × (400 in × $0.10 + 300 out × $0.50)/10⁶ ≈ **$0.03**; Opus 5.5 for decomposition plans only: ≈ 55 × (500 × $4 + 600 × $20)/10⁶ ≈ **$0.78** |
| Judge | 0 (D-10) | |

**Estimate notes.** Token counts are assumed, not measured. The base grid is ≈ 165 transform calls ≈ 165 × (400 in × $0.075 + 400 out × $0.30)/10⁶ ≈ **$0.025** on Groq. At 8K tokens/minute that is about 20–25 minutes of paced calls and about 130K tokens, which is **most of one day's 200K TPD** (plan UNVERIFIED, foundation §6.3). The runner must therefore be resumable and may not fit one session with the generation step. Run each strategy on a separate day if the quota is tight.

**Tracing (JSONL default, Phoenix to view, LangSmith only for Corpus D).** Per question: a `transform` span (strategy, `prompt_version`, original query, transformed queries, parse status, `cache_key`, tokens including reasoning, `finish_reason`, latency, cost), one retriever span per query (ranked `chunk_id`, score, rank), a `merge` span (method, `k_rrf`, depth, pool size, sources per chunk, `n_unique`, `n_in_more_than_one_list`), a `rerank` span (query used = original), and the LLM span. Fields follow foundation §3.3.

**Dataset and evaluators.**
- The M1 golden set (dev for selection; test confirmed once), plus the **probe set** (decision 1) as a separate diagnostic dataset.
- Tier-1 evaluators: CE@4, CE@pool, Hit@20, MRR@10, first-evidence rank, `drift_rate`, `parse_ok`, `answer_query_is_original`, `n_calls`, `n_searches`, `latency_ms`, `cost_usd`. All deterministic.
- `langsmith.evaluate(..., upload_results=False)` shown once for the framework view. Retrieval and answer metrics in separate blocks (`rag-evaluation`, `code-based-evaluators`).

**Experiment against the previous version.** Arms: A0 = v2.x champion; A1 = rewrite + original; A2 = step-back + original; A3 = decomposition (+ original); A4 = rewrite only (no original) as the drift stress test. Each arm against the champion (primary) and v0. Pre-register: headroom gate first; "inconclusive" expected on Corpus D; an arm count in `TEST_LOG.md`; `experiments/E030_v3.0_query_rewrite/` (06 run-id style). Compare identical comparison keys (06 §4.1 rule 1).

**Cost, latency and tokens.** Per-strategy table: LLM calls, searches, embed calls, rerank calls, p50/p95 per stage, mean context tokens, "cost if called" versus "paid" (0 on replay).

| Strategy | LLM calls | Searches | Embeds | Reranks | Note |
|---|---|---|---|---|---|
| Baseline | 0 | 1 | 1 | 1 | |
| Rewrite (replace) | 1 | 1 | 1 | 1 | original optionally +1 search |
| Step-back + original | 1 | 2 | 2 | 1 | |
| Decomposition (n = 2–4) | 1 | n (+1 original) | n (+1) | 1 | parallelisable |

**Prompt and config versioning.** `prompts/rewrite_v1.txt`, `step_back_v1.txt`, `decompose_v1.txt`, never edited after first use; the trace stores `prompt_version` and the rendered-template sha256. A `query_transform` block in `config.yaml`: `{strategy, include_original, depth, pool, n_max, rerank_query: original, model, reasoning_effort, max_completion_tokens}`. One variable changes per pre-registered run.

**Monitoring and feedback.**
- CI/T1: the merge property tests (no duplicate ids, original included), a leakage check over transform prompts (8-word overlap with gold questions), parse-failure rate under a cap, `answer_query_is_original` = 1.0, a cap on worsened qids.
- Alerts (monitor page): drift rate up, parse-failure rate up, empty-reply (`finish_reason=length`) rate above 5%, cost per query over budget, a new `system_fingerprint`.
- A question where the rewrite lost the gold goes to the M5 log ("rewrite drift" or "decomposition noise"), then into the golden set as a new version (`error-analysis`, `ci-cd-evals`).

**Place in the lifecycle.** Analyze: M5 buckets and headroom (`error-analysis`, `trace-data-analysis`). Measure: per-category CE@4 (`rag-evaluation`, `code-based-evaluators`). Improve: adopt, restrict to a category, or reject (`improving-llm-agents`). dev → CI → monitor: tests and alerts above (`ci-cd-evals`, `llm-observability`, `evals-foundations`).

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Merge, drift, metrics, tests | own code | — | — | yes | — | — | yes |
| Arrays / stats | `numpy`, `scipy` | locked | yes | yes | — | BSD-3 | yes |
| BM25 leg (champion) | `rank-bm25` | 0.2.2 | yes | yes | — | Apache-2.0 | yes |
| Dense leg | Cohere `embed-v4.0` via `cohere` | 7.2.0 | yes | replay only | ≈ 5 query-embed calls per grid; price UNVERIFIED | MIT (SDK) | yes (D-03) |
| Local fallback | `sentence-transformers` + MiniLM | 6.1.0 | yes | yes | — | Apache-2.0 | yes |
| Rerank (champion) | Cohere rerank or cross-encoder | per Phase 5 | per Phase 5 | replay / yes | ≈ 220 searches per grid; price UNVERIFIED | — | yes |
| LLM, transforms (default) | Groq `openai/gpt-oss-20b`, `reasoning_effort=low` | `.env` | SDK yes | replay only | ≈ 165 calls ≈ $0.025 | — | yes (D-04). JSON schema support for this model on Groq: **UNVERIFIED**; use `json_object` plus validation, or line parsing |
| LLM, optional | Claude Haiku 5.5 `claude-haiku-5-5` ($0.10 / $0.50 per 1M) | `anthropic` 1.11.0 | no | replay only | ≈ $0.03 per grid | MIT (SDK) | yes (D-32); decision 3 |
| LLM, hard decomposition (optional) | Claude Opus 5.5 `claude-opus-5-5` ($4 / $20) | same | no | replay only | ≈ $0.78 per grid (assumed tokens) | — | optional; justified only if Groq and Haiku decompose badly |
| Framework core | `langchain-core` | 1.6.6 | no | yes | — | MIT | yes (D-32) |
| Reference retrievers (parity, read) | `langchain-classic` (`MultiQueryRetriever`, `create_history_aware_retriever`) | 1.0.8 | no | yes | — | MIT | yes, read-only |
| Graph | `langgraph` | 1.2.12 | no | yes | — | MIT | **not needed** (fan-out is `asyncio`) |
| Hosted tracing | `langsmith` | 0.14.4 | no | no | free plan; ≈ 4 arms × 55 questions ≈ 220 traces per run | MIT (SDK) | Corpus D only |
| Local tracing | `arize-phoenix-otel` 0.17.2; server via `uvx arize-phoenix@20.19.0` | — | no | yes | — | Apache-2.0 / ELv2 | yes |
| Reading only | LlamaIndex `DecomposeQueryTransform`, `LLMQuestionGenerator` | `llama-index-core` 0.14.25 | no | — | — | MIT | read; do not install |
| Provider LangChain packages | `langchain-groq`, `langchain-cohere` | — | — | — | — | MIT | **not used** (version conflicts, foundation §9) |

**Install lines (do not run):**
```text
uv add --group llmops langchain-core==1.6.6 langchain-classic==1.0.8 langsmith==0.14.4 arize-phoenix-otel==0.17.2
uv add --group llmops anthropic==1.11.0      # only if decision 3 is yes
```
**Keys:** `GROQ_API_KEY`, `COHERE_API_KEY` (present); `ANTHROPIC_API_KEY` (optional); `LANGSMITH_API_KEY` (optional). After recording, none is needed.

### 11. Open questions for Yash (preferences only)

1. Build a small **paraphrase and compound-question probe set** (about 20 items) so v3.0 can resolve anything? **yes** / no.
2. Add the **conversational follow-up** ("condense question") block as an elective of Q1? **yes** / no.
3. Add a **Claude Haiku 5.5** arm? **yes** / no.
4. Should the original query always be searched alongside the transformed ones (recommended), or tested as an arm? **always** / arm.

---

## Concept Q2: HyDE vs HyPE (document augmentation): query-time vs index-time (U, project v3.1)

### 1. Sources checked

**Book (not present; per 02/03/04/08, not re-opened, UNVERIFIED here):**
- Ch6 p.1–2/14 (the query/document asymmetry), p.5–7/14 (steps; sketch p.7/14), p.6/14 (the hypothetical document is discarded and the answer comes from real chunks), p.8–9/14 (why an imperfect passage is enough), p.9–10/14 (match chunk size), p.10–11/14 (relation to other pre-retrieval techniques).
- Ch11 p.9–10/13 (document augmentation as the mirror image), p.12/13 (who pays the LLM cost, per 08 L44, L221).

**Repo (per 04, not re-opened):** `HyDe_Hypothetical_Document_Embedding.ipynb` cell 12 (`similarity_search(hypothetical_doc, k=3)`; asks for "exactly" 500 characters; returns the hypothetical document with the results), cells 14–18; `rs/HyDe_Hypothetical_Document_Embedding.py` L34–L41. DV-18: prompt demands exactly 500 characters, `retrieve` returns the hypothetical document, no generation. Outdated: install cell covers only dotenv (cell 5); star imports run before `load_dotenv` (cell 7); markdown says GPT-4 but code uses `gpt-4o-mini` (cell 12). `HyPE_Hypothetical_Prompt_Embeddings.ipynb` cells 9–11, 19 (per 04).

**Existing course files (read):** 02 Q2 card (L755–L766); 03 rows L44, L365, L491, L542, L633, L862; 04 Q2 row (L180) and the Ch6 table (L426–L451); 06 v3.1 card (L641–L648); 08 L41, L44, L180, L221, L259; `phase_04_indexing.md` I6 (L1972 onward: three designs, I6-E7 leakage between index-time questions and the LLM-drafted eval set); `phase_05_retrieval.md` (stage contract); `LLMOPS_FOUNDATION.md`; ext review L304 (an SDG clause: HyDE plus RRF); tracker (Q2, I6 `not_started`).

**Existing Q2 lesson, reading, questions, lab:** none.

**AE book / interview repo:** not present.

**External sources (6):** [Q2-S1] Gao et al. 2022, HyDE (search-checked); [Q2-S2] LangChain `HypotheticalDocumentEmbedder` source (verified); [Q2-S3] LlamaIndex `HyDEQueryTransform` source (verified); [Q2-S4] Weller et al. 2023 (search-checked); [Q2-S5] Wang et al. 2023, query2doc (search-checked); [Q2-S6] Jagerman et al. 2023 (shared with Q1-S6).

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | **Query/document asymmetry**: a question and its answer passage look different | Motivation | P2/P4 partly | P4 | no | bridge | Two short examples from Corpus D. Say what "close in embedding space" means |
| 2 | **HyDE mechanism**: generate → embed → search → discard | Core | Book; notebook has no generation step (DV-18) | **Q2** | no | core | Three-line pseudocode and one diagram |
| 3 | **The hypothetical document is a search key, never evidence** | Generation step | Book p.6/14; notebook returns it (DV-18) | **Q2** | no | core | Rule plus a trace check (`hypothetical not in context`) |
| 4 | **Length and style of the passage**: about chunk length, not "exactly 500 characters" | Prompt | Book p.9–10/14; repo diverges | **Q2** | no | core | Ask for chunk-sized prose, *measured in tokens*; give the course chunker's size |
| 5 | **Averaging / including the original query** | Config | Missing | **Q2** | no | core | Arms: passage only; passage + question (mean of vectors); several passages averaged. Library defaults differ (see §5) |
| 6 | **`input_type` for the passage** (`search_document` vs `search_query`) with an asymmetric embedder | Embedding | C3/P4 (not studied) | C3 | no | bridge | Explain the two roles. Test both (decision 5). No primary source decides which |
| 7 | **Domain-wrong hallucination pulls in wrong chunks** | Failure | Missing | **Q2** | no | core | A deliberately wrong passage and its effect; a check that the passage shares terms with the retrieved chunks |
| 8 | **LLM world-knowledge contamination of the test** | Evaluation validity | Missing | **Q2** | no | core | The climate PDF is a famous topic; the model may "know" the answer. Report results on Corpus T; add a private-fact probe |
| 9 | **Query-time vs index-time cost** (HyDE vs HyPE) | Comparison, 02 outcome | I6 (not built or studied) | I6 / **Q2** | no | core | Cost model below; do the sums for Corpus D |
| 10 | **HyPE / document augmentation designs** | Comparison | I6 | I6 | no | bridge | Three-sentence recap, link to I6 |
| 11 | **Fusing HyDE with the plain query** (two lists, RRF) | An arm; ext review SDG clause | R1 (exposed) | R1 | exposed | bridge | An arm: RRF of plain and HyDE lists |
| 12 | **Strong retrievers gain less** (expansion can hurt) | Prior expectation | Missing | **Q2** | no | core | Quote the finding [Q2-S4]; set the expectation to "may not help" |
| 13 | **Latency on the critical path** (LLM before retrieval) | Guard metric | Missing | **Q2** | no | core | A latency waterfall; p95 guard |
| 14 | **Reproducible generation** (caching, temperature, reasoning-effort) | LLMOps | Foundation §2 | foundation | n/a | bridge | Key = query + prompt version + model + parameters; N passages are N samples (variance mode) |
| 15 | **Embedding `search_query` cache is by exact text** | Cost | C3 | C3 | no | bridge | Each passage is a new text, so a new embedding call |
| 16 | **Reasoning-model behaviour** (empty reply at small cap) | Every call | P1 / C5 | P1 | partly | bridge | `reasoning_effort=low`, high enough cap, empties counted |
| 17 | **Eval leakage**: HyDE prompts built from gold passages | Fairness | 06 §6.3 | M1 | no | bridge | The prompt may not contain gold text; extend the leakage check |
| 18 | **Per-category reporting and the headroom gate** | Experiment | as Q1 #11–12 | M4/M5 | exposed | bridge | Same gate as Q1 |
| 19 | **query2doc as a related variant** (append the passage to the query for BM25) | Alternative | Missing | next | no | next | One line in Full: lexical-leg use of the passage; link only |
| 20 | **MemoRAG clue generation (S3) builds on HyDE** | Later phase | 03 L365 | S3 | no | next | Link only |

### 3. Quiz coverage

No question file exists. Needed titles:
- **R1** What does HyDE put into the embedding step instead of the question?
- **R2** Is the hypothetical document shown to the answer model? Why or why not?
- **R3** What is the query/document asymmetry in one example?
- **A1** Given a question, write the instruction you would give the LLM for the passage (length, style) and say why.
- **A2** The model invents a plausible but wrong passage. What happens to retrieval, and what check catches it?
- **A3** Compute the LLM calls for 1,000 queries and a 5,000-chunk corpus for HyDE versus HyPE (3 questions per chunk), and say when each is cheaper.
- **A4** Choose HyDE, HyPE or neither for three given situations.
- **T1** Your corpus is private product manuals the model has never seen. Predict HyDE's effect and design a test.
- **T2** HyDE raised recall but lowered MRR. Give two explanations and one check each.
- **I1** "What is HyDE and when does it fail?" **I2** "HyDE versus doc2query/HyPE: trade-offs?"

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| Q2-E1 | 06 v3.1 card | The card has "Change: the hypothetical passage replaces (or is averaged with) the question embedding; record which", but the arms are not listed. There is no plain-query side-by-side, which 04 also notes (DV-18) | List the arms: passage only; passage + question (mean); RRF of two lists; plus the raw baseline |
| Q2-E2 | 06 v3.1 "Hypothesis" | States HyDE "raises CE@4 on vocabulary-mismatch items" with no mention that gains in the paper are over an *unsupervised* retriever [Q2-S1], or that a strong stack may not benefit [Q2-S4] | Add a prior of "may not help" and a headroom gate |
| Q2-E3 | 06 v3.1 / 02 Q2 | The `input_type` for the passage is not specified; with Cohere's asymmetric `embed-v4.0`, `search_query` versus `search_document` is a real choice | Add as an arm or fix one and record it |
| Q2-E4 | 06 v3.1 "Experiment" | "also compare with index-time question generation (I6/HyPE)" has no artefact, no corpus rebuild cost, and no leakage rule (I6-E7 in Phase 4) | Make the comparison conditional on I6 being built; otherwise compare cost by arithmetic only |
| Q2-E5 | 04 Ch6 table | Step 7 says the notebook "returns the hypothetical document alongside the results (diverges, harmless if never passed on)". It becomes harmful as soon as the course builds generation (Q2-E6) | Add a rule: the passage is dropped before context assembly |
| Q2-E6 | 02 Q2 card | "Ext: C#32 (Gao et al.)" is the only external source; the strong-retriever result [Q2-S4] is absent from the course | Add [Q2-S4] to the reading list |
| Q2-E7 | 02 Q2 | Pre = Q1, P4 only. HyDE is conceptually independent of Q1 (03 L491 says "either order works" for I6) | Note that Q1 is a lab-order dependency only |
| Q2-E8 | 04 Ch6 "Outdated" | Does not mention that the repo's embedding model (OpenAI) is not allowed here (D-03) and that the hypothetical document must be embedded with the *course* embedder | Add to the "swap to your stack" note |

### 5. What the research says

**[Q2-S1] HyDE (Gao, Ma, Lin, Callan; ACL 2023; search-checked only).**
- **Study:** zero-shot instruct an LLM (GPT-3 family) to write a fictional document that answers the query; encode that document with the unsupervised Contriever; search the real corpus with that vector. The generated text is only a search key.
- **Result (search-reported Table 1, TREC DL19 / DL20, nDCG@10):** BM25 50.6 / 48.0; Contriever 44.5 / 42.1; **HyDE 61.3 / 57.9**; fine-tuned Contriever 62.1 / 63.2. Recall@1k: HyDE 88.0 / 84.4. HyDE beats BM25 and unsupervised Contriever and nearly matches the fine-tuned model on DL19, but trails it on DL20. (One secondary source labelled the 61.3 vs 44.5 pair as DL20; the table gives it for DL19. Re-check the table.) Further web-search, low-resource and multilingual results exist; not seen.
- **Limits:** the baseline is a retriever *without* supervision; modern commercial embedders are trained on query-document pairs and are much closer to the fine-tuned row. The generator is GPT-3 (2022). The text appears to average several (reported as 8) generations at temperature 0.7 (UNVERIFIED; recalled, not seen here).
- **For us:** the closest analogue is our *raw* dense baseline versus HyDE. Whether the gain survives Cohere `embed-v4.0` is the experiment. Do not assume it.

**[Q2-S4] Weller et al. 2023 (search-checked).** See Q1. Strong negative correlation between a retriever's baseline score and the gain from LLM expansion over 11 methods, 12 datasets and 24 retrievers; expansions add noise at the top of the ranking. Practical advice: use expansion on weaker retrievers or on data unlike the retriever's training data.

**[Q2-S5] query2doc (Wang, Yang, Wei, EMNLP 2023; search-checked).** Few-shot prompt an LLM for a pseudo-document, *append it to the query* (for BM25), improving BM25 by 3–15% on MS MARCO and TREC DL without fine-tuning; dense retrievers also benefit but gains shrink with strong rerankers. The abstract notes diminishing gains when the retrieval is already distilled from a cross-encoder.

**Library defaults (verified, source on `master`/`main`, 2026-10-18).**
- **[Q2-S2] LangChain `HypotheticalDocumentEmbedder.embed_query`:** generates **one** document per query (no count parameter in this file), embeds it, and averages the vectors with NumPy `mean(axis=0)`. Needs `prompt_key` or `custom_prompt`; unknown keys raise `ValueError`. The **original question is not embedded or averaged in**.
- **[Q2-S3] LlamaIndex `HyDEQueryTransform`:** one hypothetical document per query (a TODO notes multiple are unsupported). **`include_original=True` by default**: the embedding strings are `[hypothetical, original]`, which the retriever embeds and combines. The original `query_str` is kept for the response step.
- The two libraries differ on the key design choice: LangChain embeds the passage alone; LlamaIndex embeds the passage and the question. A learner who reads only one library gets half the picture.

**Current practice (2024–2026).** HyDE is a standard optional step in retrieval toolkits. Web posts describe it as helpful for short abstract queries and harmful for niche domains the model does not know, which matches the paper's logic. One web glossary claims 2026 reruns show the gap shrinking to 1–4 points and going negative on entity-heavy corpora; **no primary source was found**, so do not use it. No peer-reviewed 2024–2025 failure study was found in this session (UNVERIFIED; a targeted search on an unblocked index is needed).

**Pitfalls and failure modes.**
- A confidently wrong passage points at the wrong region [HyDE paper's own reasoning; blog-level evidence for specifics].
- On exact-term questions the passage dilutes the rare token (hypothesis; test on D-008).
- Passing the passage to the answer model as if it were evidence (architecture rule).
- Contamination: the LLM already knows the climate text's topic, so the test is easy and unrepresentative.
- Latency: one LLM call before retrieval, on the critical path.

**How to evaluate.**
- **Retrieval (primary):** CE@4 and MRR@10 per category on dev; CE@pool; Hit@20.
- **Guards:** exact-term and factual-single-span CE@4; p95 latency; cost per query; the wrong-passage rate on a hand-read sample.
- **Baselines:** raw query with the champion pipeline (primary); BM25 and hybrid as they stand after v2.x; and, if I6 is built, the HyPE index.
- **Arms:** (A) raw; (B) passage only (`search_query`); (C) passage only (`search_document`), if decision 5 is yes; (D) mean of passage and question vectors; (E) RRF of raw list and HyDE list; (F) mean of 3 passages (variance mode, 3 calls).
- **Contamination check:** a small probe of private or invented facts (not in the LLM's training data) added to a private test document. Compare HyDE's effect on those versus well-known climate facts.

**Interview angle (general knowledge).** (1) What is HyDE and why does it work? (2) When does it fail? (3) How does it differ from query rewriting? (4) HyDE versus doc2query/HyPE: cost and quality trade-offs? (5) How would you measure it and what is the baseline?

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).**
1. A question and the passage that answers it often look different, so their embeddings can be far apart even when they belong together.
2. HyDE asks an LLM to write a short fake answer, embeds that text instead of (or together with) the question, and searches with it.
3. The fake answer is only a search key: it is thrown away, and the final answer is written from the real chunks and the original question.
4. It helps when the model knows the topic and the retriever is weak; it can mislead retrieval when the model invents wrong details.
5. It adds one LLM call before every search, so you compare it with the index-time alternative (HyPE) that pays its LLM calls once, up front.

**The theory in one read.**
1. The asymmetry: question space vs passage space.
2. HyDE steps: generate → embed → search → discard → answer from real chunks.
3. What to ask for: chunk-sized prose, in the corpus's style, not a list.
4. What to embed: passage only, passage + question (mean), several passages (mean), or two lists fused.
5. `input_type`: the role label given to the embedder.
6. Why a wrong passage can still work (shared terms and topic), and why a wrong passage can fail (wrong region).
7. Failure checks: term overlap between the passage and the retrieved chunks; passage-only vs raw rank change.
8. Strong retrievers gain less.
9. Cost: query-time `C_HyDE = Q × (c_llm + c_embed)` versus index-time `C_HyPE = N × m × c_llm + N × m × c_embed`, where Q = queries, N = chunks, m = questions per chunk; break-even `Q* = N × m` (ignoring the embed cost difference).
10. Latency on the critical path.
11. Contamination of the evaluation.

**Formula-sheet items.** The mean-vector formula `v = (1/(n+1)) (Σ e(d_i) + e(q))`; cost break-even; RRF (from R1); term-overlap ratio.

**Step-by-step outline (running example).** Corpus D, 97 chunks, seeds D-006 (vocabulary mismatch) and D-008 (exact term). Steps: the question and its chunk → the fake answer → its embedding → the top chunks with and without it → the answer from real chunks → the cost → the failure case (a wrong passage) → the HyPE comparison by arithmetic. *Why Corpus D:* the seeds exist; *but* flag the contamination and show a private-fact example from Yash's own documents.

**Visuals.**
1. *Embedding-space sketch (SVG):* question, passage and fake answer positions. Shows the asymmetry in one picture.
2. *Pipeline diagram:* the fake answer is discarded before context assembly.
3. *Arms table with example vectors (toy 2-D).* Shows what "mean of vectors" does.
4. *Cost lines (Plotly):* HyDE vs HyPE cumulative LLM calls against number of queries. Shows the break-even `Q* = N × m`.
5. *Rank-change slope chart per seed:* raw vs HyDE first-evidence rank.

**Full-only.** query2doc and appending to BM25; multi-sample averaging; multilingual and low-resource results; MemoRAG link.

### 7. Verify notebook plan

`study/notebooks/Q2_hyde_verify.ipynb` (framework-free).
- **Recomputes:** the mean-vector construction on toy 2-D vectors; the cost break-even; first-evidence rank for raw vs HyDE arms on the seeds; the passage-to-chunk term overlap.
- **LLM calls (recorded once):** one HyDE passage per seed = **10 Groq calls**; plus 20 more if the 3-passage variance arm is shown. **Embeddings:** each passage is a new text: about 10–40 texts, 1 Cohere call (≤96). **Offline:** MiniLM fallback.
- **Runtime:** under 1 minute in replay.
- **Charts:** Plotly slope chart of ranks; cost lines.
- **Check:** the passage never appears in the assembled context.

### 8. Apply-it tool plan and real-world checklist

`study/tools/hyde_fit_check.py` (**input:** the user's questions and documents; **output:** a report and a CSV).
- For each question it generates the passage (cached), searches raw and HyDE, and reports rank changes and a term-overlap score between the passage and the evidence. It also reports the passage's vocabulary versus the question's.
- **Recommendation logic:** if raw CE@4 is already 100%: "no headroom"; if HyDE lowers any exact-term question: "do not apply to exact-term questions"; if the passages have a low term overlap with the retrieved chunks and the corpus is private: "likely wrong-domain; do not use HyDE"; if HyDE helps several vague questions with a small latency budget: "try it on those."

| # | Check | Auto / manual |
|---|---|---|
| 1 | Raw CE@4 and Hit@20 (headroom) | auto |
| 2 | Fraction of failures that are vocabulary-mismatch | manual labels + auto count |
| 3 | Passage length in tokens vs your chunk size | auto |
| 4 | Passage–evidence term overlap | auto |
| 5 | Rank change per question (raw vs HyDE) | auto |
| 6 | Exact-term questions: any loss? | auto |
| 7 | The passage never reaches the answer model | auto |
| 8 | Does the model know your domain? Read 10 passages | manual |
| 9 | Added latency and cost per query | auto |
| 10 | Index-time alternative: HyPE LLM calls for your chunk count | auto |
| 11 | Private-fact probe (invented facts) behaves like climate facts? | manual + auto |

### 9. LLMOps notebook plan

`study/llmops/notebooks/Q2_hyde_ops.ipynb`: v3.1 as a traced, replayable experiment.

**Framework build.** `HypotheticalDocumentEmbedder` from `langchain-classic`, with a `CachedEmbeddings` base and a `CachedChatModel`, as a **parity** test against the course's HyDE function. Map: `llm_chain` → generate; `base_embeddings.embed_documents` → embed the passage; `combine_embeddings` → the mean. **Defaults to demonstrate:** LangChain does not include the original question; LlamaIndex does (`include_original=True`); LangChain's `embed_query` calls `embed_documents` on the passage, so the role label is `search_document` with a Cohere wrapper that maps `embed_documents` to that type (this is an inference from the design in foundation §9.3, **UNVERIFIED** for the exact class behaviour; check against the released `langchain-classic` 1.0.8 source). No LangGraph (linear).

**External calls (all cached).**

| Call | Count | Notes |
|---|---|---|
| Groq `openai/gpt-oss-20b`, `reasoning_effort=low`, one passage | ≈ 55 | ≈ 55 × (300 in × $0.075 + 500 out × $0.30)/10⁶ ≈ **$0.01** |
| Same, 3-sample variance arm (optional) | +110 | `record` mode with `sample = 1, 2` |
| Cohere `embed-v4.0` (passage as `search_query` and as `search_document`) | ≈ 110–165 texts → 2 calls | the second role is arm C |
| Cohere rerank | as the champion's: ≈ 55 per arm | price UNVERIFIED |
| Groq generation, adopted arm | ≈ 35 | ≈ $0.01 |
| Claude Haiku 5.5 (optional) | ≈ 55 | ≈ $0.01 |
| Judge | 0 (D-10) | |

**Tracing.** A `hyde` span: prompt version, original query, the passage (stored locally; for exported spans only length and sha256, since text could be derived from the corpus), tokens including reasoning, `finish_reason`, cost, latency, `cache_key`; the embedding span with `input_type` and dimension; the retriever span; a `passage_in_context` boolean (must be false).

**Dataset and evaluators.** The M1 golden set plus the probe set (private-fact items). Tier-1: CE@4, CE@pool, MRR@10, Hit@20, `term_overlap`, `passage_in_context`, `wrong_passage_rate` (hand-labelled on 10), cost, latency. `langsmith.evaluate(..., upload_results=False)` shown once.

**Experiment against the previous version.** Arms A–F (§5) against the v3.0 champion (or v2.x if v3.0 is rejected), and against v0. `experiments/E031_v3.1_hyde/`. Pre-register: headroom gate; contamination check; "inconclusive" expected on Corpus D. If I6 is built, a HyPE arm with the index-build cost counted.

**Cost, latency, tokens.** Per-arm table (LLM calls, embed calls, p50/p95 per stage); the break-even plot with the measured `c_llm`; "cost if called" vs paid.

**Prompt and config versioning.** `prompts/hyde_v1.txt` (never edited); config block `{arm, n_passages, include_original, input_type, target_tokens, model, reasoning_effort}`; one variable per run; the leakage check covers the prompt.

**Monitoring and feedback.** T1: `passage_in_context` is always false; the leakage check; the empty-reply rate cap; a cap on worsened qids. Alerts: exact-term regressions, passage length drift, new `system_fingerprint`, cost per query. A failure (wrong passage; lost rare token) goes to the M5 log ("HyDE hallucination"), then into the golden set.

**Place in the lifecycle.** Analyze (`error-analysis`), Measure (`rag-evaluation`, `code-based-evaluators`), Improve (`improving-llm-agents`), dev → CI → monitor (`ci-cd-evals`, `llm-observability`, `evals-foundations`).

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Mean vector, cost, metrics | `numpy`, own code | locked | yes | yes | — | BSD-3 | yes |
| Dense leg | Cohere `embed-v4.0` via `cohere` | 7.2.0 | yes | replay only | ≈ 2 calls per grid; price UNVERIFIED | MIT (SDK) | yes |
| Local fallback | `sentence-transformers` MiniLM | 6.1.0 | yes | yes | — | Apache-2.0 | yes (its 256-token limit matters for 500-token passages: truncation, per 06 L423) |
| LLM, passage (default) | Groq `openai/gpt-oss-20b`, `reasoning_effort=low` | `.env` | SDK yes | replay only | ≈ 55 calls ≈ $0.01 | — | yes |
| LLM, optional | Claude Haiku 5.5 | `anthropic` 1.11.0 | no | replay only | ≈ $0.01 | MIT | optional; decision 3 |
| Framework | `langchain-core` 1.6.6; `langchain-classic` 1.0.8 (HyDE parity, read) | | no | yes | — | MIT | yes |
| Tracing | `langsmith` 0.14.4 (Corpus D only); `arize-phoenix-otel` 0.17.2 + server by `uvx` | | no | partly | free plan | MIT / Apache-2.0 / ELv2 | yes |
| Reading only | LlamaIndex `HyDEQueryTransform` (`llama-index-core` 0.14.25) | | no | — | — | MIT | read only |
| Official HyDE repo | `texttron/HyDE` | — | no | needs pyserini, Java | — | UNVERIFIED | **not used** (heavy; read only) |
| HyPE (comparison) | own code from I6 | — | — | — | index-time calls × chunks | — | conditional on I6 |

**Install lines (do not run):** the same as Q1 (shared group). **Keys:** `GROQ_API_KEY`, `COHERE_API_KEY` present; others optional.

### 11. Open questions for Yash (preferences only)

1. Test the passage as both `search_query` and `search_document` (two arms)? **yes** / no.
2. Run Q2 on **Corpus T** as well as D once chosen (DEC-3)? **yes** / no.
3. Add a small **private-fact probe** (invented facts in your own document) to measure contamination? **yes** / no.
4. Use 1 passage per query (default) or add a 3-sample variance arm? **1** / 3.

---

## Phase-level notes

1. **One stage contract for v3.x** (extends Phase 5's): transformed queries feed retrieval *only*; the champion's merge/filter/rerank stages run unchanged; the reranker and generator see the original question; HyDE passages are dropped before context assembly. Write it once in 06 for both cards.
2. **Order inside the phase.** Teach Q1 first (it introduces the merge and the drift check), then Q2. Q2 can run before Q1 in the lab if Yash prefers (03 L491: either order).
3. **Headroom and power.** Both cards are about 10 items strong on Corpus D. Decisions 1 and Q2's "run on Corpus T" matter more than any tool.
4. **Dependency on Phase 5.** v3.0/v3.1 inherit the Phase 5 champion. If Phase 5 ends "inconclusive", the champion is v1.x or v0; say so in the experiment id.
5. **Dependency on Phase 4 (I6).** The Q2 vs HyPE comparison is by arithmetic unless I6 is built. I6-E7 (index-time questions and the LLM-drafted eval set can leak) applies.
6. **Other phases.** A1 (routing) is the natural consumer of Q1's per-category results. A2 (CRAG) re-uses query rewriting after a failed grade. S3 (MemoRAG) builds on HyDE. X-phase work is unaffected.
7. **Rate limits.** Q1's grid is the largest Groq consumer so far (≈ 130K tokens of a 200K daily quota, plan UNVERIFIED). Plan a multi-day recording run or use Haiku.
8. **Foundation update suggested** (not edited): add the per-strategy call table to §12 row "6 · Q1–Q2".

## Sources

Status: **verified** = page or source opened; **search-checked** = only seen through web-search summaries of the paper page or listing (arXiv blocked); **UNVERIFIED** = not opened.

1. [Q2-S1] Gao, Ma, Lin, Callan, "Precise Zero-Shot Dense Retrieval without Relevance Labels" (HyDE), ACL 2023 — https://arxiv.org/abs/2212.10496 (also https://github.com/texttron/hyde) — search-checked only
2. [Q1-S2] Zheng et al., "Take a Step Back: Evoking Reasoning via Abstraction in Large Language Models", ICLR 2024 — https://arxiv.org/abs/2310.06117 (ICLR listing: https://proceedings.iclr.cc/paper_files/paper/2024/hash/592da1445a51e54a3987958b5831948f-Abstract-Conference.html) — search-checked only
3. [Q1-S3] Ma et al., "Query Rewriting in Retrieval-Augmented Large Language Models", EMNLP 2023 — https://arxiv.org/abs/2305.14283 ; https://aclanthology.org/2023.emnlp-main.322 — search-checked only
4. [Q1-S1] Press et al., "Measuring and Narrowing the Compositionality Gap in Language Models" (Self-Ask), Findings of EMNLP 2023 — https://arxiv.org/abs/2210.03350 — search-checked only
5. [Q1-S4] Trivedi et al., "Interleaving Retrieval with Chain-of-Thought Reasoning for Knowledge-Intensive Multi-Step Questions" (IRCoT), ACL 2023 — https://aclanthology.org/2023.acl-long.557 — search-checked only
6. [Q1-S5] Rackauckas, "RAG-Fusion: a New Take on Retrieval-Augmented Generation", IJNLC 2024 — https://arxiv.org/abs/2402.03367 — search-checked only
7. [Q1-S6 / Q2-S6] Jagerman et al., "Query Expansion by Prompting Large Language Models", 2023 — https://arxiv.org/abs/2305.03653 — search-checked only
8. [Q2-S4] Weller et al., "When do Generative Query and Document Expansions Fail?", Findings of EACL 2024 — https://arxiv.org/abs/2309.08541 ; https://github.com/orionw/lm-expansions — search-checked only
9. [Q2-S5] Wang, Yang, Wei, "Query2doc: Query Expansion with Large Language Models", EMNLP 2023 — https://arxiv.org/abs/2303.07678 ; https://aclanthology.org/2023.emnlp-main.585 — search-checked only
10. [Q1-S7] LangChain `MultiQueryRetriever` — https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/langchain/langchain_classic/retrievers/multi_query.py — verified (source, master, 2026-10-18)
11. [Q1-S7] LangChain `create_history_aware_retriever` — https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/langchain/langchain_classic/chains/history_aware_retriever.py — verified
12. [Q2-S2] LangChain `HypotheticalDocumentEmbedder` — https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/langchain/langchain_classic/chains/hyde/base.py — verified
13. [Q2-S3 / Q1-S8] LlamaIndex query transforms — https://raw.githubusercontent.com/run-llama/llama_index/main/llama-index-core/llama_index/core/indices/query/query_transform/base.py — verified
14. [Q1-S8] LlamaIndex `LLMQuestionGenerator` — https://raw.githubusercontent.com/run-llama/llama_index/main/llama-index-core/llama_index/core/question_gen/llm_generators.py — verified
15. Web posts on HyDE failure modes (e.g. aussieai.com, freeCodeCamp, FutureAGI glossary) — seen only as search summaries; used for the qualitative failure modes only; the FutureAGI 2026 numbers are **not used** — UNVERIFIED
16. Course files read locally: `study/research/RESEARCH_PROMPT.md`, `LLMOPS_FOUNDATION.md`, `phase_04_indexing.md` (I6), `phase_05_retrieval.md`; 02 (L101, L624–L628, L740–L766, L1223–L1264), 03, 04 (Q1/Q2 rows, Ch5/Ch6 tables, DV-16…DV-18), 06 (v3.0/v3.1 cards, §6.2, §6.7), 08, `study/reading/R1_hybrid_fusion.md`, `sources/verification/R1/R1_FACTS.md`, `sources/vai/L10-L18` and `L24-L27`, `progress/concept_tracker.csv`, `progress/misconception_log.md`, `pyproject.toml`
17. Book (Ch5, Ch6, Ch11, Ch12), AE book, interview repo (AIQ), `upstream/RAG_Techniques`, `CLAUDE.md`, project skills — not present in this session — UNVERIFIED
