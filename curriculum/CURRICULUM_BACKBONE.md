# CURRICULUM BACKBONE — authoritative design spec (referred to as "BACKBONE" in 01–08)

> Copied into the workspace on 2026-10-08 from the orchestration scratchpad so that every "BACKBONE §n" reference resolves. The deliverables 01–08 elaborate this spec; where they record a decision against it (see [08](../08_GAP_ANALYSIS_AND_DECISIONS.md) D-21…D-30), the deliverable wins. Paths below that mention a scratchpad refer to session-temporary working files; their durable copies are in [`../sources/verification/`](../sources/verification/).

This file fixes IDs, ordering, project versions and evaluation design so the eight deliverables are mutually consistent.
Writers may elaborate but must not rename IDs, reorder phases, or contradict decisions here. If you believe something here is wrong, say so in a clearly marked "REVIEWER NOTE" in your output instead of silently changing it.

## 0. Fixed facts (verified by the orchestrator by direct inspection)

- Workspace: `C:\Yash\New-Work\Book RAG\rag_learning\` (new; all deliverables go here). Relative links inside the workspace.
- Book: *RAG Made Simple: The Complete Visual Guide* (Nir Diamant). Local copy: `C:\Yash\New-Work\Book RAG\RAG_Made_Simple_The_Complete_Visual_Guide\` — 25 separate PDFs: `intro.pdf`, `index.pdf` (TOC), `chapter 1.pdf` … `chapter 22.pdf`, `Appendix.pdf` (Appendix A decision guide pp.1–12, Appendix B glossary pp.13–23). No copyright/edition page present in the split files; every page carries a third-party "OceanofPDF.com" footer → edition/version cannot be verified; there are no printed page numbers. Citation convention: **"Ch4 p.3/15"** = PDF page 3 of the 15-page file `chapter 4.pdf`. Never cite printed book pages.
  - An identical copy of the chapter PDFs also exists at `C:\Yash\New-Work\Book RAG\prior_work\RAG book step by step\chapter pdf\` (UNVERIFIED byte-identity; same file names).
- Book chapter order: Ch1 Simple RAG · Ch2 RAG for Structured Data (CSV) · Ch3 Reliable RAG · Ch4 Proposition Chunking · Ch5 Query Transformations · Ch6 HyDE · Ch7 Contextual Chunk Headers · Ch8 Context Enrichment Window · Ch9 Semantic Chunking · Ch10 Contextual Compression · Ch11 Document Augmentation · Ch12 Fusion Retrieval · Ch13 Reranking · Ch14 Hierarchical Indices · Ch15 Dartboard Retrieval · Ch16 Multi-Modal RAG with Captioning · Ch17 Retrieval with Feedback Loops · Ch18 Adaptive Retrieval · Ch19 Explainable Retrieval · Ch20 Corrective RAG · Ch21 Graph RAG · Ch22 RAG Evaluation · Appendix A Decision Guide · Appendix B Glossary.
- The book is explicitly code-free ("intuition, not code") and says it is derived from the RAG_Techniques repo.
- Repo: `https://github.com/NirDiamant/RAG_Techniques`, pinned clone at `C:\Yash\New-Work\Book RAG\upstream\RAG_Techniques`, commit `009adba2be1bef49780ef73b6dd3c18fd24b035b` (2026-09-21, 538 commits). 41 notebooks in `all_rag_techniques/` (README/AGENTS.md claim 42), 21 scripts in `all_rag_techniques_runnable_scripts/`, 5 eval notebooks + `evaluation/evalute_rag.py`, `helper_functions.py`, `tests/` (import smoke tests only), `data/`. No requirements.txt / pyproject in repo. Custom non-commercial LICENSE.
- Two older local zip-extracted copies exist (no .git, no commit hash): `C:\Users\Yash\Downloads\Compressed\RAG_Techniques-main\RAG_Techniques-main` and `C:\Yash\New-Work\RAG\RAG_Techniques-main`; plus the learner's working copy `C:\Yash\New-Work\Book RAG\prior_work\RAG book step by step\` (June 2026 snapshot, missing newer notebooks such as light_rag, multi_faceted_filtering, local_rag_huggingface_faiss, graph_rag_local_attribution). Diffs vs pinned clone include marketing/CTA notebook cells; `helper_functions.py` identical to the Downloads copy. Treat the pinned clone as canonical.
- Prior learner materials (DO NOT modify): `C:\Yash\New-Work\Book RAG\prior_work\RAG book step by step\learning_guides\` (22 chapter guides all generated 2026-06-11 within ~20 minutes, `PROGRESS.md` states the chapter mapping is "estimated"; its numbering does NOT match the real book — e.g. its "chapter-04-chunk-size" while real Ch4 is Proposition Chunking), `study_companion.py`, `study_progress.json` (Ch1 quizzed once: scores [1,3,3], avg 2.33; Ch2 "studied"; others not started). Earlier memory notes said PDFs "cannot be read programmatically" — that is now false: `pdftotext` (mingw64) works.
- Machine: Windows 11, uv 0.9.20, Python 3.12.8 (default) + uv-managed 3.13/3.14, NVIDIA RTX 3060 Laptop 6 GB VRAM, no CUDA toolkit. **Ollama is NOT installed** (empty ~/.ollama, no exe) → no local LLM today. Jupyter only partially installed (jupyter_core/ipykernel in user site, no notebook/lab front end confirmed).
- Credentials (names only): `GROQ_API_KEY`, `COHERE_API_KEY` exist in `C:\Yash\New-Work\Book RAG\prior_work\my way\.env`. **No OPENAI_API_KEY anywhere** → ~36 of 46 upstream notebooks cannot run as written. **Groq has no embeddings or rerank endpoint** (verified in Groq API reference 2026-10-08) → embeddings default to local sentence-transformers (Cohere embed/rerank optional). *(Superseded 2026-10-08 by learner decision D-03: Cohere embed is the default and local sentence-transformers the fallback — see §6 and the [corrections log](../reviews/CORRECTIONS_LOG_2026-10-08.md#learner-decisions).)*
- Repo count correction: README/AGENTS.md claim 42 notebooks; there are **41** `.ipynb` in `all_rag_techniques/` + 5 in `evaluation/`. `C:\Yash\New-Work\Book RAG\RAG_Techniques-main\RAG_Techniques-main` is byte-identical (ignoring CRLF) to the pinned commit.
- Book Ch22 explains Precision@K/Recall@K (p.4–5/19) and MRR/MAP/NDCG (p.5–6/19) verbally (no formulas worked); the repo computes **none** of Recall@k/MRR/nDCG anywhere. `evaluation/evalute_rag.py` generates fresh LLM questions each run, splits on newlines, has no ground truth, and `calculate_average_scores` is a stub (L160–L163).
- Repo `data/q_a.json` (44 Q/A, no evidence pages; heuristically covers only climate PDF pp.1–5). Climate PDF = 33 pages, ~9.3k words, 21 chapters, with repeated topics across pages (Paris Agreement p.10 & p.23; smart grids p.8 & p.22; CCS/DAC p.7–8 & p.23) → natural near-duplicate distractors.
- Learner's real hands-on evidence: `C:\Yash\New-Work\Book RAG\prior_work\my way\` executed LangGraph CRAG / Reliable RAG / query-rewrite notebooks (Groq + Cohere), VAI labs (chunking_lab Streamlit with 6 chunkers; L22 reranking; L23 hybrid; L27/L29/L44 eval; L30 observability). Prior study evidence = one self-rated quiz (Ch1, 2.33 on a 1–3 self-rating scale). Diagnostic O1 should probe these areas and may fast-track phases where the learner demonstrates mastery.
- Notable upstream defects (verified by static reading; runtime UNVERIFIED unless stated): fusion_retrieval.ipynb cell 17 combines vector/BM25 score arrays that are not aligned to the same documents; graph_rag uses L2 distance as similarity; helper retry_with_exponential_backoff re-awaits a coroutine; HyPE cell 11 SyntaxError; dartboard cell 25 wrong kwarg; adaptive_retrieval Opinion path crash; several stale saved outputs (choose_chunk_size cell 12 shows a ServiceContext warning the current code cannot produce). Legacy `langchain.*` imports fail under langchain 1.x (an agent probed locally installed langchain 1.2.13).

## 1. Design principles (non-negotiable)

1. Organize by **engineering problem and conceptual dependency**, not book or repo order.
2. **Measure before improving.** Evaluation moves EARLY (Phase 3), immediately after the baseline. The book places evaluation last (Ch22; Appendix A p.7 "Layer 5 … Finally, add measurement") while its own Appendix A key takeaways (p.12) say to measure before and after every change — we resolve this contradiction in favour of measuring first.
3. **Retrieval quality ≠ answer quality.** Every experiment reports retrieval metrics and generation metrics separately.
4. Every technique is introduced as: failure observed in baseline → hypothesis → intervention → controlled experiment → decision. No technique without a named failure it targets.
5. Mechanism before framework: Layer 1 plain Python/NumPy, Layer 2 upstream repo code reading, Layer 3 reusable module in `rag_learning/ragkit/`.
6. No fabricated numbers: all result tables are templates with empty cells until the learner runs them. Illustrative toy numbers are allowed only when computed by hand/by code and labelled "toy illustration".
7. Provider-agnostic; default free/local path must exist for every essential lab.
8. Priority tiers: **E = Essential**, **U = Useful**, **S = Specialized**. Advanced/agentic content is never on the critical path.

## 2. Curriculum phases and concept IDs (fixed)

Concept IDs are used in every file. Format `<PhaseLetter><n>`.

**Typed prerequisites.** The phase lists below fix IDs and order only; *which* concepts unlock which is defined by the typed prerequisite registry in [03 §2.1](../03_RAG_CONCEPT_DEPENDENCY_MAP.md) with four fields: `requires_all` (every listed concept), `requires_any_groups` (OR groups — e.g. A5 needs A1 *or* A2; S3 needs S1 *or* R5), `requires_gate` (a learner mastery gate from §3 / [02 §4](../02_RAG_MASTER_LEARNING_PLAN.md)) and `requires_exposure` (mechanism exposure — read + trace or demo — e.g. I-CMP needs exposure to I2–I6). Soft edges are non-binding advice only; project-version order (§4) is not a conceptual prerequisite. Every Phase 4–11 concept (I*, R*, Q*, X*, V*, D*, A*, S*) has at least `requires_gate: Gate 3→4`; K1 (`requires_all: I-CMP, V3, D2`; `requires_gate: Gate 9→10`, defined in 02 §4) is reachable without any A* or S* concept.

> Revised 2026-10-08 (Codex M-07): concept unlocking is governed by typed prerequisites (all / any-groups / gate / exposure) in 03 §2.1. See [corrections log](../reviews/CORRECTIONS_LOG_2026-10-08.md#m-07).

### Phase 0 — Orientation & Recovery (O)
- O1 Prior-knowledge diagnostic (blank-page RAG pipeline reconstruction + 12 diagnostic questions) — E
- O2 Environment setup lab (uv project, `.env`, provider config, smoke test with the local embedding fallback, one Cohere embed call, BM25 and one Groq call — E-2 in 08 Part 7) — E
- O3 How to use this system (coaching protocol, progress files, review cadence) — E

> Revised 2026-10-08 (Codex B-01; learner decisions D-03, D-04): the O2 smoke test matches approval gate B's E-2. See [corrections log](../reviews/CORRECTIONS_LOG_2026-10-08.md#b-01).

### Phase 1 — Prerequisites (P)
- P1 LLM fundamentals: tokens & tokenization, context windows, sampling/temperature, cost per token, chars≈tokens heuristics (and why they are only heuristics) — E
- P2 Information-retrieval framing: documents, queries, relevance, inverted index, ranking — E
- P3 Lexical retrieval: TF-IDF and BM25 (with a hand-computed numeric example), tokenization for BM25 — E
- P4 Embeddings & similarity: vectors, dot product, cosine, L2, normalization (numeric examples), bi-encoders, embedding model max sequence length & truncation, asymmetric query/document embedding — E
- P5 Vector search: exact k-NN in NumPy, ANN intuition (HNSW, IVF), FAISS/vector stores, metadata storage — E (ANN internals U)
- P6 Retrieval evaluation basics: relevance labels (qrels), Precision@k, Recall@k, Hit@k, MRR, nDCG (numeric examples) — E
- P7 Prompting for grounded generation: context construction, instruction to cite, "lost in the middle", context budget — E

### Phase 2 — Core RAG baseline (C)  → Project v0
- C1 Document loading & parsing (PDF text extraction, page provenance, artifacts: headers/footers, hyphenation, multi-column, tables) — E
- C2 Chunking fundamentals: fixed-size & recursive splitting, overlap, units (chars vs tokens), provenance metadata — E  ← SAMPLE LESSON (07)
- C3 Embedding & indexing with metadata (doc_id, page, chunk_id, char offsets, params hash) — E
- C4 Dense retrieval (top-k, score inspection) — E
- C5 Context construction & answer generation with citations — E
- C6 Baseline pipeline v0 end-to-end + provenance trace — E
- C7 Structured data RAG (CSV/JSON) — S (sidebar; book Ch2; repo simple_csv_rag, json_rag)

### Phase 3 — Measurement first (M)  → Project v0.1 (eval harness; pipeline unchanged)
- M1 Building an evaluation set: question categories, gold evidence as **character spans with doc_id+page** (chunk-agnostic), answerable vs unanswerable, synthetic-question pitfalls (leakage, ceiling effects) — E
- M2 Retrieval metrics harness on v0: Complete-Evidence@k (primary sufficiency metric) plus diagnostics Group-Recall@k, Span-Coverage@k, Hit@k, MRR, nDCG@k (definitions in §5) — E *(revised 2026-10-08, Codex M-02: was "Recall@k, MRR, nDCG@k, span-coverage")*
- M3 Generation metrics: faithfulness/groundedness, answer correctness, citation precision/recall, abstention accuracy; LLM-as-a-judge strengths/limits, judge calibration vs a small human-labelled set — E
- M4 Experimental discipline: controls, seeds, caching, variance, ablations, regression sets, latency & cost logging — E
- M5 Failure analysis taxonomy (book Appendix A symptom families + supplementary "failure points" literature) and error-bucketing of v0 failures — E

### Phase 4 — Indexing & representation (I)  → Project v1.x
- I1 Chunk size/overlap experiments (the controlled experiment of the sample lesson; repo choose_chunk_size) — E
- I2 Structure-aware chunking (headings/sections/pages; recursive separators) — U (gap in both sources)
- I3 Semantic chunking (Ch9) — U
- I4 Proposition chunking (Ch4) — S/U (expensive; LLM at index time)
- I5 Contextual chunk headers / contextual retrieval (Ch7) — U
- I6 Document augmentation & HyPE: index-time question generation (Ch11; HyPE notebook) — S
- I-CMP Comparative lesson: "granularity family" fixed vs structure vs semantic vs proposition vs headers — E

### Phase 5 — Retrieval improvements (R)  → Project v2.x
- R1 Sparse vs dense vs hybrid; fusion (Ch12): weighted score fusion vs Reciprocal Rank Fusion — E
- R2 Metadata filtering (repo multi_faceted_filtering; book: no chapter) — U
- R3 Reranking (Ch13): cross-encoder vs LLM reranker; candidate-pool size — E
- R4 Diversity: MMR / Dartboard (Ch15) — U
- R5 Hierarchical retrieval: hierarchical indices (Ch14), RAPTOR (repo only) — S

### Phase 6 — Query-side improvements (Q)  → Project v3.x
- Q1 Query transformations: rewriting, step-back, sub-query decomposition (Ch5) — U
- Q2 HyDE (Ch6) and comparison with HyPE/document augmentation (query-time vs index-time) — U

### Phase 7 — Context construction (X)  → Project v4.x
- X1 Context enrichment window (Ch8) & relevant segment extraction (repo only) — U
- X2 Contextual compression (Ch10) — U
- X3 Context assembly: dedup, ordering, token budgeting, citation formatting (gap) — E

### Phase 8 — Reliability & grounding (V)  → Project v5.x
- V1 Grounded answers & citation verification (Ch19 Explainable Retrieval; repo graph_rag_local_attribution for attribution ideas) — E
- V2 Reliable RAG: relevance grading + hallucination/groundedness check (Ch3) — E
- V3 Answerability & abstention (gap; thresholds, "I don't know" policy, evaluation of refusals) — E
- V4 Hallucination detection limits & judge reliability (ties back to M3) — U

### Phase 9 — Production readiness (D)  → Project v6
- D1 Observability: structured traces of every intermediate (query, candidates, scores, context, prompt, answer, citations) — E
- D2 Latency & cost measurement/budgets, caching — E
- D3 Regression evaluation in CI (pytest + eval thresholds), index versioning, incremental re-indexing — U
- D4 Security & safety: prompt injection via retrieved documents, access control via metadata, PII — U

### Phase 10 — Adaptive & corrective control flow (A)  → Project v7 (choose ONE first)
- A1 Adaptive retrieval / query routing (Ch18) — U
- A2 Corrective RAG (Ch20; repo crag) — U
- A3 Self-RAG (repo only) — S
- A4 Feedback loops (Ch17) — S
- A5 Agentic RAG (repo only) — S (last; never before Phase 8 mastery)

### Phase 11 — Specialized architectures (S) — elective
- S1 Graph RAG (Ch21; repo graph_rag, Microsoft_GraphRag, light_rag, graphrag_with_milvus_vectordb) — S
- S2 Multimodal RAG (Ch16; repo captioning, ColPali) — S
- S3 MemoRAG (repo memorag) — S

### Phase 12 — Capstone (K)
- K1 Architecture defence: choose a stack for a new corpus with evidence from your own experiments; blank-page reconstruction; optional Streamlit UI — E

## 3. Mastery gates (between phases)
These are **learner mastery gates** (what the learner must demonstrate). They are distinct from the **staged approval gates A/B/C** at the end of this section, which govern when artifacts may be built ([08 Part 7](../08_GAP_ANALYSIS_AND_DECISIONS.md)). Mastery gates are what the `requires_gate` field of the typed prerequisite registry refers to (§2, 03 §2.1).

- Gate 0→1: diagnostic done; env smoke test passes.
- Gate 1→2: hand-compute cosine, BM25 term score, Recall@k/MRR/nDCG on toy data without notes; explain chars vs tokens and embedding truncation.
- Gate 2→3: v0 runs end-to-end from a clean env; learner can trace one query through every intermediate artifact and explain each; writes chunker from memory.
- Gate 3→4 (= approval Gate C): eval set ≥ 40 human-verified answerable questions with span-level gold `evidence_groups` (§5) + ≥ 6 unanswerable (a learning minimum only — no abstention-threshold claims yet, §5), bound to a snapshot manifest, with the dev/test/holdout split recorded; harness reproduces identical retrieval metrics on rerun; generation quality covered by a human-labelled pilot on v0 (≥ 30 answer-level labels; the automated judge is deferred to the end of the curriculum, §5); M5 failure buckets with trace IDs and counts; learner explains why judge scores ≠ retrieval metrics.
- Gate 4/5/6/7 (per technique): completed controlled experiment write-up with hypothesis verdict, cost/latency delta, "when NOT to use", and passes transfer question.
- Gate 8→9: abstention policy evaluated on unanswerable set; citation verification implemented.
- Capstone: architecture defence + blank-page reconstruction + unseen-corpus transfer.
A completed notebook is never sufficient evidence.

### Staged approval gates (build/approval)
Approval gates decide when *artifacts* (labs, lessons, code) may be built; mastery gates above decide when the *learner* moves on. Building never waits for artifacts that only later work can produce. Every 08 Part 7 item is assigned to exactly one approval gate; the authoritative item-by-item assignment table is in [08 Part 7](../08_GAP_ANALYSIS_AND_DECISIONS.md).

Gate A requires only **design-time artifacts plus decisions recorded in a decision-only preflight**: a conversation in which no environment is created, explicitly allowed **before** Gate A. No Gate A item is produced by O2 or any later lab. "Start O2's decision discussion" (the preflight, allowed now) is distinct from "create the environment" (O2 itself, after Gate A): O2 **implements** the DEC-1a decisions; it does not make them.

| Approval gate | Contents (08 Part 7 item IDs) | Permits | Relation to mastery gates |
|---|---|---|---|
| **A — Design approval** | S-1…S-6; C-1…C-5; V-1, V-2, V-4 *at specification level* (snapshot/coordinate, evidence-group, comparability and calibration contracts written down, not executed); V-3; P-1 (07 approved as exemplar after the P0/P1 fixes and Codex re-review); P-2 (learner agrees to the coaching protocol; learner agreement 2026-10-08); P-3; R-1…R-3; DEC-2 (licence acknowledged by the learner on 2026-10-08); DEC-1a = decisions needed for Phases 0–2 (D-03, D-04, D-05, D-10, D-14, D-16, D-19, D-20), all made in the decision-only preflight (learner decisions recorded 2026-10-08; see §6); DEC-1b = coach/reviewer design decisions D-06, D-07 (coach confirmation 2026-10-08), D-17 (re-confirmed once R-02 passes) | O1–O3 (O2 creates the environment that implements DEC-1a), P1–P7 labs, C1–C6 implementation (building v0) | Precondition for Phase 0 (the decision-only preflight may run before it) |
| **B — Environment & baseline exit** (O2 exit, then C6 exit) | O2 exit: E-1…E-4 (locked uv env; smoke test = local embedding fallback + Cohere embed call + BM25 + one Groq call; notebook front end on the project kernel; embedding model limits recorded). C6 exit: BL-1 (v0 runs end-to-end from a clean environment with full traces); DEC-1c (corpus and eval-set decisions D-01, D-02, D-09); DEC-3 (Corpus T chosen and frozen (with snapshot) before Phase 3; Corpus H chosen and frozen before K1) | E-items: labs that depend on the environment. C6 exit: M1–M5 (measurement work) | ≈ environment part of Gate 0→1 + Gate 2→3 |
| **C — Measurement exit / optimization entry** | MX-1…MX-5: eval set human-verified, bound to a snapshot, with evidence groups (§5); deterministic harness reproduces identical retrieval metrics on rerun; dev/test/holdout split recorded; generation quality covered by a human-labelled pilot (automated judge deferred to the end, §5); M5 failure buckets with trace IDs and counts | Phase 4+ experiments (I1 onward) | = Gate 3→4 |

E-items are required only before labs that depend on the environment; a working v0 is required before Phase 3 work. Status on 2026-10-08: Gate A not yet passed — the Codex re-review did not grant it; design approval is pending re-review of the round-2 corrections (R-01…R-07).

> Revised 2026-10-08 (Codex B-01): the single "everything before any build" rule is replaced by staged approval gates A/B/C mapped to the learner mastery gates; Gate 3→4 aligned with Gate C; item IDs (DEC-1a/1b/1c, BL-1, MX-1…MX-5) match 08 Part 7 (cross-document sweep). See [corrections log](../reviews/CORRECTIONS_LOG_2026-10-08.md#b-01).

> Revised 2026-10-08 (Codex M-07): mastery gates are referenced by the typed `requires_gate` field (§2, 03 §2.1). See [corrections log](../reviews/CORRECTIONS_LOG_2026-10-08.md#m-07).

> Revised 2026-10-08 (Codex re-review R-01): Gate A needs only design-time artifacts plus decisions from a decision-only preflight (allowed before Gate A); O2 implements DEC-1a, it does not make it. See [corrections log](../reviews/CORRECTIONS_LOG_2026-10-08.md#r-01).

> Revised 2026-10-08 (Codex re-review R-06): DEC-3 timing in the Gate B row is "Corpus T chosen and frozen (with snapshot) before Phase 3; Corpus H chosen and frozen before K1", matching 08. See [corrections log](../reviews/CORRECTIONS_LOG_2026-10-08.md#r-06).

## 4. Project "Ask My Technical PDFs" — versions (fixed)

| Version | Change (single variable where possible) | Targets failure | Phase |
|---|---|---|---|
| v0 | Baseline: PyMuPDF page text → fixed recursive char chunks 1000/200 (book Ch1 p.4 default) → Cohere embed (local sentence-transformers fallback; §6) → NumPy exact cosine top-k (k=4) → Groq LLM prompt with numbered citations [doc:page] | — | C |
| v0.1 | Eval harness (no pipeline change): eval set, retrieval + generation metrics, trace logging, cost/latency | can't measure | M |
| v1.0 | Chunk size/overlap grid (I1) | dilution vs fragmentation | I |
| v1.1 | Structure-aware chunking (I2); v1.2 contextual chunk headers (I5); v1.3 semantic chunking (I3); v1.4 propositions on a subset (I4) | boundary/context loss | I |
| v2.0 | BM25 + dense hybrid with RRF (R1) | exact-term/acronym misses | R |
| v2.1 | Cross-encoder reranking (R3) | right doc, wrong rank | R |
| v2.2 | Metadata filtering (R2); v2.3 MMR (R4) | scope / redundancy | R |
| v3.0 | Query rewriting / decomposition (Q1); v3.1 HyDE (Q2) — applied only to query categories where v2 fails | vocabulary mismatch, multi-part | Q |
| v4.0 | Context assembly: window enrichment, dedup, budget (X1, X3); v4.1 compression (X2) | missing surrounding context / noise | X |
| v5.0 | Grounding: citation verification, groundedness check, abstention (V1–V3) | unsupported claims, answering unanswerable | V |
| v6.0 | Observability, cost/latency budgets, regression tests in CI (D1–D3) | silent regressions | D |
| v7.0 | ONE of corrective (A2) or adaptive routing (A1), justified by failure buckets | residual failures | A |
| v8 (optional) | One specialized architecture only if eval shows multi-hop/global questions fail (S1 or R5) | global/multi-hop | S |
| Capstone | Optional Streamlit UI over the best evidence-backed configuration | — | K |

Every version keeps v0 runnable and is compared against v0 AND the previous best on the frozen eval set (same `dataset_sha256`, `snapshot_id`, qid set, labels, split and `scorer_version` — §5).

> Revised 2026-10-08 (Codex M-05 / learner decisions D-03, D-04, D-05): v0 uses Cohere embed with a local fallback and a Groq LLM (no Ollama); "frozen eval set" means identical comparison keys. See [corrections log](../reviews/CORRECTIONS_LOG_2026-10-08.md#learner-decisions).

## 5. Corpus & evaluation design (fixed defaults; corpus choice is an OPEN DECISION to list in 08)
- Corpus D (dev/smoke + parity with upstream): `data/Understanding_Climate_Change.pdf` from the repo — lets the learner compare directly with upstream notebooks.
- Corpus T (main "technical PDFs"): 4–6 technical PDFs the learner chooses. Default proposal: a handful of arXiv RAG papers (e.g. RAG (Lewis 2020), DPR, HyDE, Lost in the Middle, RAPTOR) — dense technical text with tables, equations, two-column layout = realistic parsing challenges. Licence: personal local use; do not redistribute PDFs.
- Corpus H (held-out transfer): a different-domain technical PDF the learner already owns (e.g. the *Effective XGBoost* PDF present in `C:\Users\Yash\Documents\`) — used only at capstone to test transfer.
- Do NOT use the RAG Made Simple PDFs as the experimental corpus (copyright/redistribution and conflation of study material with test data) — open decision noted.
- **Frozen-text snapshot.** Every eval set is bound to one snapshot manifest per corpus × parser/cleaning configuration, stored at `evaluation/snapshots/<corpus>_<snapshot_id>.json`. Required fields: `snapshot_id` (first 12 hex of the doc_text_sha256 over all docs + parser/cleaning ids), `corpus`, `corpus_version`, `created_utc`, `parser: {backend: "pymupdf", version, call: "page.get_text()", options}`, `cleaning: {version, steps}` (v0: `"none"` — offsets refer to raw extracted text; any cleaning step creates a new snapshot), `encoding: "utf-8"`, `newline: "\n"`, `page_join: "\n"`, and `docs: [{doc_id, pdf_sha256, bytes, pages, doc_text_sha256, page_table: [{page (1-based), doc_char_start, doc_char_end, text_sha256}]}]`. The snapshot text is stored locally next to the manifest (`<snapshot_id>/<doc_id>.txt`), git-ignored if the PDF licence is unclear. Example (Corpus D, PyMuPDF 1.26.7, no cleaning): 33 pages, 72,593 document characters.
- **One coordinate system.** Canonical offsets are **document offsets** into `doc_text` (pages joined with "\n"); page-relative offsets are a derived view. Canonical chunk fields: `doc_id, snapshot_id, chunk_id, seq, char_start, char_end` (document offsets), `page_segments: [{page, char_start, char_end}]` (page-relative, one per page touched), `text, text_sha256, chunker, params_hash`; invariants: `doc_text[char_start:char_end] == text`, and segments convert back to the same document range. Gold evidence is authored page-relative (human-friendly) and converted to document offsets by the loader via the snapshot `page_table` (explicit, tested conversion); cross-page evidence = two consecutive segments forming one alternative.
- **Fail closed.** Before scoring, the loader recomputes each page's `text_sha256` (or reads the stored snapshot text) and compares it to the manifest; any mismatch, or a dataset whose `snapshot_id` differs from the index's, stops scoring. Before translating any gold label, the loader also rejects (R-02, [06 §5.3](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#53-corpus-freezing) rule 4): a missing header or manifest field; a `snapshot_manifest_sha256` that differs from the sha256 of the exact stored manifest bytes; any page-table structural break (pages 1..n without gaps, first start 0, each end − start = page-text length, next start = previous end + page-join length, last end = document-text length, page and `doc_text_sha256` hashes match); and a recomputed `snapshot_id` that differs from the manifest's or the dataset's. A parser/cleaning change ⇒ new snapshot ⇒ new dataset version: quote search may *propose* migrated offsets, but every migrated span is re-validated by the learner; quote uniqueness alone never authorises reuse of old labels. Acceptance: a page-2 span and a cross-page (pp.12–13) span score identically with per-page or cross-page chunks; a changed page hash stops scoring; an extraction change cannot silently reuse prior gold.
- Eval set schema (JSONL). Dataset header: `snapshot_id, snapshot_manifest_sha256, scorer_version, evidence_logic_version` (plus the human version label). Item: `qid, question, category, answerable(bool), gold_answer, evidence_groups, split (dev|test|holdout), group, difficulty, created_by(human|llm-draft|llm-draft-human-verified), notes`, where `evidence_groups: [{group_id, fact, alternatives: [{alt_id, segments: [{doc_id, page, char_start, char_end}], quote(≤25 words)}]}]` is **required** for scored answerable items. Groups are AND (every required fact); alternatives inside a group are OR (any one sufficient source). Each alternative is a **complete minimal sufficient span** (a reader shown only it can supply that fact without outside knowledge). Unanswerable items have `evidence_groups: []`. *(Replaces the flat `gold_evidence` list.)*
- Question categories: factual-single-span, multi-span/synthesis, vocabulary-mismatch/paraphrase, exact-term (acronyms, function names, numbers), table/numeric, multi-hop, unanswerable, ambiguous.
- Relevance and sufficiency (one rule each, no thresholds). Coverage is computed in document coordinates over the **union** of the character ranges of the chunks at a given stage (candidate pool, final top-k, or final assembled context). An alternative is *satisfied* iff every non-whitespace character of its segments is covered (`tolerance = whitespace-only`). A chunk is *relevant* (first-evidence metrics only) iff it overlaps ≥ 1 non-whitespace character of any segment of any alternative. Config: `scoring: {scorer_version: "s1", chunk_relevance: "any_overlap", sufficiency: "complete_evidence", tolerance: "whitespace-only"}` — the former "≥50% of span covered" option is removed. Because gold is span-based, labels survive re-chunking — this is what makes chunking experiments valid.
- Retrieval metrics: **primary = Complete-Evidence@k (CE@k)** — 1 iff every group has ≥ 1 satisfied alternative in the stage's set; mean over answerable items. Diagnostics: Group-Recall@k (fraction of groups satisfied); Span-Coverage@k (mean over groups of the best alternative's covered-character fraction — continuous, never pass/fail); first-evidence metrics Hit@k, MRR, Precision@k, nDCG@k (they show that *some* evidence arrived, not that it is sufficient); context tokens retrieved. Retrieval experiments report CE at final top-k; context-assembly versions (v4.x) also report CE on the final assembled context. Acceptance: half-span fragments of D-005's two facts ⇒ CE = 0; two-group item with one group retrieved ⇒ CE = 0; either alternative of D-004 ⇒ CE = 1; a span split across two retrieved chunks whose union covers it ⇒ CE = 1. Generation metrics: answer correctness (vs gold), faithfulness/groundedness, citation precision/recall, abstention precision/recall — scored as in the next bullet. Ops: index build time, #chunks, #embeddings, p50/p95 latency, tokens & estimated cost per query.
- Generation scoring — judge pilot vs certification (learner decision D-10, 2026-10-08). Labelling units: faithfulness = claim-level (supported / unsupported / contradicted); citation = per citation (does the cited excerpt support its sentence?); correctness = answer-level (correct / partial / wrong); abstention = deterministic (no judge). Abstentions are excluded from faithfulness and citation calibration. The first 30 labelled units per metric are a **pilot**, used only to draft/fix the rubric. **Certification** needs a separate, untouched validation set with ≥ 30 failure-class and ≥ 30 non-failure units per metric (Assumption: provisional counts), reported with denominators and an interval method chosen **by statistic**: the **confusion matrix** as raw counts (no interval); **binomial rates** (failure-class recall, precision, abstention precision/recall, false-abstention rate) with a **Wilson 95% interval** when units are independent, or a **cluster bootstrap over answers** when several units (claims or citations) come from one answer; **Cohen's κ** — not a proportion, it can be negative — with a **paired bootstrap over labelled units** (resampling answers when units are clustered) or the large-sample κ variance (statsmodels `cohens_kappa` is the reference implementation). Example: two raters on 4 balanced items who always disagree have observed agreement 0 and expected agreement 0.5·0.5 + 0.5·0.5 = 0.5, so κ = (0 − 0.5)/(1 − 0.5) = **−1**; a Wilson interval is meaningless here. **Decision rule (Assumption: provisional operating preference):** a judge is certified for a metric only if, on the untouched validation set, the **lower 95% bound** of failure-class recall is ≥ 0.70 **and** the lower 95% bound of κ is ≥ 0.40; otherwise human scoring continues for that metric. The point targets κ ≥ 0.6 and failure recall ≥ 0.8 are still reported as aspirational, not as the pass rule — never a pass on undefined or tiny denominators (8 of 10 failures caught = recall 0.8, but Wilson 95% CI ≈ 0.49–0.94: too wide to certify). If natural outputs contain too few failures, add a labelled challenge set (fabricated claims, swapped citations, contradictions), kept and reported separately. Rubric-tuning and validation units are disjoint; judge repeat variance (flip rate on repeated runs) is reported separately from paired metric-effect uncertainty (bootstrap). **Judge = a Cohere chat model** (a different family from the Groq generator); Codex labels a fixed calibration sample as an independent labeller (not counted as human, not the per-run judge). **All judge-based metrics run once, at the end of the curriculum, in one batch over the stored traces of every version** (identical inputs). Until then, decisions use deterministic metrics (CE@k etc., abstention, citation-excerpt existence, EM/F1 for short answers) plus human reading of ~10 answers per version; generation-dependent choices in Phases 7–8 are provisional and may be revised by the final judge batch. Human evaluation is the essential fallback: Gate 3→4 needs a human-labelled generation pilot on v0 (≥ 30 answer-level labels), not a certified judge.
- Unanswerables: 40 answerable + 6 unanswerable stays a *learning minimum* for Gate 3→4; no abstention-threshold claims until ≥ 15 unanswerable items exist with ≥ 5 in dev (Assumption: provisional counts) — even 6/6 correct has an exact two-sided 95% lower bound ≈ 0.54.
- Comparability and splits. Paired comparisons require identical comparison keys: `dataset_sha256`, `snapshot_id`, qid set, labels, split and `scorer_version`; the runner aligns per-question values **by qid** (never by position) and rejects arrays whose qid sets differ. Any addition, edit, removal, relabel, split change or scorer change produces a new dataset file and hash; MAJOR/MINOR names stay as human labels, but comparability is defined **by hash**, not by MAJOR version. After items are added, rerun baseline, champion and candidate on the new version, or compare only on the declared unchanged-qid intersection. Splits: `dev` (selection: grid search, thresholds, λ, pool sizes), `test` (locked; touched once per selection round to confirm the chosen candidate; each touch logged with selection round and number of configurations tried), `holdout` (untouched until the K1 architecture defence, plus Corpus H). Paraphrase variants share a `group` with their base item; splitting and bootstrap resampling are done by group (cluster bootstrap). Test items inspected repeatedly become regression data; threshold cross-validation must be nested or use an outer holdout.
- Controls: frozen snapshot (`snapshot_id`, manifest hash) and frozen eval set (`dataset_sha256`), fixed embedding model+version, fixed k (and separately equal-token-budget comparisons), temperature 0, cached LLM calls and content-keyed embedding cache (§6), seeds, record library versions.

> Revised 2026-10-08 (Codex M-01): one snapshot manifest contract, document offsets as the single coordinate system, fail-closed scoring, re-validation after parser changes. See [corrections log](../reviews/CORRECTIONS_LOG_2026-10-08.md#m-01).

> Revised 2026-10-08 (Codex re-review R-02): the fail-closed bullet now lists the full binding checks (exact-bytes manifest digest, page-table structural integrity, recomputed `snapshot_id`) run before any gold translation. See [corrections log](../reviews/CORRECTIONS_LOG_2026-10-08.md#r-02).

> Revised 2026-10-08 (Codex M-02): required `evidence_groups` (AND of OR-alternatives); CE@k is the primary sufficiency metric, coverage and Hit/MRR/nDCG are diagnostics; ≥50% coverage rule removed. See [corrections log](../reviews/CORRECTIONS_LOG_2026-10-08.md#m-02).

> Revised 2026-10-08 (Codex M-05): comparability by dataset hash and qid set (qid-aligned, cluster bootstrap); dev/test/holdout discipline. See [corrections log](../reviews/CORRECTIONS_LOG_2026-10-08.md#m-05).

> Revised 2026-10-08 (Codex M-06): judge calibration split into pilot and certification with counts and Wilson intervals; Cohere judge run once at the end; human pilot for Gate 3→4. See [corrections log](../reviews/CORRECTIONS_LOG_2026-10-08.md#m-06).

> Revised 2026-10-08 (Codex re-review R-03): interval method by statistic — confusion matrix as counts, Wilson only for binomial rates (cluster bootstrap when units share an answer), κ via paired bootstrap or κ variance (κ = −1 example); certification on lower 95% bounds (Assumption). See [corrections log](../reviews/CORRECTIONS_LOG_2026-10-08.md#r-03).

## 6. Environment defaults (preferences, not necessities — label as such)
- uv project at `rag_learning/` with `pyproject.toml`; Python 3.12.
- Learner decisions (decided 2026-10-08 in the decision-only preflight, before Gate A; O2 implements them, §3): **D-14** Python 3.12, pinned with uv. **D-20** CPU-first PyTorch build; switch to CUDA only if a measured slowdown justifies it. **D-19** notebook front end = VS Code notebooks on the project uv kernel. **D-16** workspace stays at `C:\Yash\New-Work\Book RAG\rag_learning`; **local git only** (no remote); `.gitignore` covers `.env`, PDFs, snapshot text when the licence is unclear, caches and indexes.
- Core (necessary for essential labs): numpy, pymupdf, rank-bm25, sentence-transformers (or fastembed), tiktoken or a HF tokenizer, jupyter, pytest, python-dotenv, pandas.
- Embeddings (learner decision D-03, 2026-10-08): **Cohere embed = default** (`input_type` `search_document` for chunks, `search_query` for queries; model id from config). **Local sentence-transformers = fallback** (offline work + second-model comparison): a small open model (e.g. `BAAI/bge-small-en-v1.5` or `sentence-transformers/all-MiniLM-L6-v2`) — the writer must state each model's max sequence length only if verified, else mark UNVERIFIED. MiniLM/bge figures in 07 stay as upstream-parity illustration; truncation limits are re-measured for the Cohere model at O2/C3 (E-3).
- LLM (learner decisions D-04, D-05): **Groq** for generation and all non-judge LLM calls (key already present; configurable model id — never hardcode a model name as permanently valid, Groq deprecates models). **Ollama is not used** (rejected by the learner; not installed). Automated judge = a Cohere chat model, run once at the end (§5, D-10). Optional Cohere rerank; OpenAI only to reproduce upstream notebooks (no key present). Phase 1–3 and most of Phase 4–5 labs must remain runnable with ZERO API calls via the local fallback (local embeddings + BM25 + cross-encoder; principle 7); LLM calls are needed only for generation/judging.
- Cache-key contract (Codex M-04). `chunk_id = f"{doc_id}:{snapshot_id}:{params_hash}:{seq:05d}"` — namespaced by the snapshot, whose id changes whenever extracted text changes; chunks also carry `text_sha256`. **Embedding cache key** = `sha256(provider | model_id | model_revision | input_type ("search_document"/"search_query" for Cohere; "none" otherwise) | preprocessing_version | text)`. LLM cache key unchanged: `sha256(model_id | messages | params)`. A config hash alone is not content addressing: chunk/artifact IDs are for joins and traces, never cache keys. Required tests: same content + config ⇒ identical ids and cache keys; same doc/position with changed text ⇒ different cache key (and a different snapshot_id ⇒ different chunk_id); query vs document `input_type` ⇒ different keys.
- Reranker default: local cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`, the model the repo uses) — optional Cohere rerank.
- Python 3.12 (not 3.14: wheel availability risk).
- Framework use: LangChain/LlamaIndex only to READ upstream code or where they add clear value (e.g. text splitters for comparison). The learner's `ragkit` is framework-free.
- `ragkit/` module layout (proposed): `config.py, providers/ (llm.py, embeddings.py), loaders.py, chunking.py, index.py, retrieval.py (dense, bm25, hybrid), rerank.py, context.py, generate.py, eval/ (dataset.py, retrieval_metrics.py, generation_metrics.py, judge.py), tracing.py, experiments.py`.

> Revised 2026-10-08 (Codex M-04): IDs are not cache keys; chunk_id is snapshot-namespaced and embedding caches are keyed by provider/model/revision/input_type/preprocessing/text. See [corrections log](../reviews/CORRECTIONS_LOG_2026-10-08.md#m-04).

> Revised 2026-10-08 (learner decisions D-03/D-04/D-05/D-10): Cohere embed default + local fallback, Groq LLM, no Ollama, Cohere judge at the end. See [corrections log](../reviews/CORRECTIONS_LOG_2026-10-08.md#learner-decisions).

> Revised 2026-10-08 (Codex re-review R-01; round-2 decisions): D-14 Python 3.12, D-20 CPU-first torch, D-19 VS Code notebooks on the uv kernel, D-16 local git only — recorded in the decision-only preflight. See [corrections log](../reviews/CORRECTIONS_LOG_2026-10-08.md#round-2-decisions).

## 7. Workspace layout (fixed)
```
rag_learning/
  README.md                      master index (links every file)
  01_SOURCE_INVENTORY.md … 08_GAP_ANALYSIS_AND_DECISIONS.md   (first-stage deliverables, at workspace root)
  sources/       source registry notes, pinned commit, page-citation convention (no copied book text)
  curriculum/    future per-phase module pages
  concepts/      future one-file-per-concept lessons (C2 sample lives as 07 for now)
  labs/          future notebooks (lab id = concept id, e.g. labs/C2_chunking_lab.ipynb)
  experiments/   experiment configs + result write-ups (templates only now)
  evaluation/    eval sets + harness docs
  progress/      progress tracker, misconception log
  reviews/       spaced-repetition queue
  ragkit/        (future) reusable package
```
First stage creates only the eight .md deliverables + README.md + minimal placeholder READMEs in subfolders explaining their purpose (no notebooks, no full lessons).
