# 04 Book-to-Code Mapping and Master Traceability Matrix

This file maps every curriculum concept and book chapter to the exact book pages, notebook cells and script lines that cover it. It also records where the book and the code disagree, and what neither of them implements. **It hosts the master traceability matrix** (§2). The other deliverables point here for "where does X live?" questions.

| Section | Use it when you want to… |
|---|---|
| [1. How to use; citation conventions](#1-how-to-use-this-file) | read or check a citation |
| [2. Master traceability matrix](#2-master-traceability-matrix) | start a concept: find its pages, cells, gaps, experiment and order |
| [3. Chapter-by-chapter mapping](#3-chapter-by-chapter-mapping) | read a chapter next to its code, one algorithm step at a time |
| [4. Repo-only notebooks](#4-repo-only-notebooks) | place a notebook the book never mentions |
| [5. Book content with no code](#5-book-content-with-no-code) | see what you must build yourself |
| [6. Divergence catalogue](#6-divergence-catalogue) | check every book-vs-code mismatch in one table |

Related deliverables: the source registry is in [01](01_SOURCE_INVENTORY.md), the phase plan in [02](02_RAG_MASTER_LEARNING_PLAN.md), prerequisite edges in [03](03_RAG_CONCEPT_DEPENDENCY_MAP.md), the retention protocol in [05](05_LEARNING_AND_RETENTION_SYSTEM.md), project versions and the eval design in [06](06_RAG_PROJECT_AND_EVALUATION_PLAN.md), the C2 sample lesson in [07](07_SAMPLE_LESSON.md), and open decisions in [08](08_GAP_ANALYSIS_AND_DECISIONS.md).

---

## 1. How to use this file

**Starting a concept (normal use).**
1. Find its row in §2.
2. Read the book pages listed there for intuition.
3. Open the chapter section in §3 to see which notebook cell implements each algorithm step, and where the code departs from the book.
4. Read the cited cells (Layer 2: reading upstream code). Do not run them as your reference implementation.
5. Build the missing pieces in your own `ragkit` (Layer 3). The concept's experiment row tells you how to test it.

**Reading a notebook first.** Look it up in §3 (if the book covers it) or §4 (if it is repo-only). Check §6 before trusting its output.

**Reviewing.** Every reference here can be checked mechanically. Book pages come from the per-page text dumps. Notebook cells come from the 0-based cell dumps of the pinned commit. Script lines come from the pinned clone.

### 1.1 Citation conventions

| Kind | Format used here | Meaning |
|---|---|---|
| Book chapter page | `Ch4 p.3/15` | PDF page 3 of the 15-page file `chapter 4.pdf`. The book has no printed page numbers. |
| Intro / Appendix | `Intro p.2/8`, `App p.6/23` | Pages of `intro.pdf` and `Appendix.pdf`. App A is the decision guide (pp.1–12); App B is the glossary (pp.13–22; p.23/23 is the author bio, so BACKBONE's "pp.13–23" is one page wide). |
| Notebook cell | `simple_rag.ipynb cell 13` | `all_rag_techniques/simple_rag.ipynb`, 0-based index in the nbformat `cells` list. The folder prefix is dropped in tables to save width. Evaluation notebooks keep their `evaluation/` prefix. |
| Runnable script | `rs/simple_rag.py:L44-L61` | `all_rag_techniques_runnable_scripts/simple_rag.py`, lines 44–61. |
| Other repo files | `helper_functions.py:L48-L76`, `evaluation/evalute_rag.py:L160-L163` | Repo-root-relative path. Note the upstream file name is misspelt ("evalute"). |
| Supplementary source | `C#13 (IIR BM25)` | **External (Source C).** Not in the learner's files. Numbered as in the verified Source C registry ([01](01_SOURCE_INVENTORY.md)); see the legend in §1.3. |

- **Repo version.** Every repo citation refers to `NirDiamant/RAG_Techniques` at commit `009adba2be1bef49780ef73b6dd3c18fd24b035b` (local clone `C:\Yash\New-Work\Book RAG\upstream\RAG_Techniques`). Older local copies can differ in cell numbering.
- **Script line ranges** run from the `def`/`class` line to the line before the next top-level definition, so they may include trailing blank lines.
- **Status words** in §3:
  - **Implemented**: the code does what the book step says.
  - **Partial**: part of the step is done.
  - **Missing**: no code exists for the step.
  - **Diverges**: the code does something materially different (see §6).
- **UNVERIFIED** marks a claim that could not be confirmed by static reading of the pinned sources. Nothing in this file was executed, and no runtime behaviour is claimed unless it is marked as such. Static-reading bugs are labelled "(static reading)".
- **Book text.** It is paraphrased throughout. Any quoted phrase is shorter than 15 words.

### 1.2 How the citations were verified, and errata found

The pass worked like this:
- Each citation was taken from the verified inventory.
- Book pages were spot-checked by per-page grep of the text dumps (`=== [chapter N.pdf | PDF page x of y] ===` markers).
- Notebook cell numbers were re-located by searching the notebook dumps for the defining code (e.g. `def fusion_retrieval` is in `fusion_retrieval.ipynb cell 17`).
- Script line ranges were taken from `def`/`class` positions in the pinned clone.

Errata found against the intermediate inventory:
- **Ch3 "I don't know" sentence.** It is on **Ch3 p.11/14**, not p.12/14 as one inventory note said. This file uses p.11/14.
- **Epsilon in fusion min-max.** The notebook has the `1e-8` epsilon (`fusion_retrieval.ipynb cell 17`). The script does not (`rs/fusion_retrieval.py:L80-L81`, confirmed by direct read).

Errata from the independent verification pass (all 760 book page references re-checked for page totals; content spot-checked page by page; repo cells and line ranges re-located):
- Ch13 "vs Ch3 grading" starts on p.12/13, not p.11/13.
- DV-B12 statement B now cites Ch8 p.9/11 and Ch9 p.10/14 (the earlier Ch8 p.7/11–p.8/11 cite did not contain the claim).
- O2: `helper_functions.py` does not import deepeval; deepeval arrives via the `evaluation.evalute_rag` star import.
- DV-38: the script's crash at L158 is `.isdigit()` on ints, not `.split()` (the `.split()` crash is in the notebook).
- `LLMRerank` batching and the "HHEM" name are library knowledge, not visible in the notebooks; both are now marked UNVERIFIED.

### 1.3 Source C legend (external material only)

These references are **not in the book or the repo**. Use them only where the matrix marks the book or repo as silent or wrong.

| C# | Short title | C# | Short title |
|---|---|---|---|
| 1 | uv documentation | 30 | Dense X Retrieval (propositions), arXiv 2312.06648 |
| 3 | HF LLM Course ch.6, tokenizers | 31 | Anthropic, "Introducing Contextual Retrieval" (vendor blog) |
| 4 | HF Transformers tokenizer summary | 32 | HyDE (Gao et al. 2022), arXiv 2212.10496 |
| 5 | tiktoken repo | 33 | Reciprocal Rank Fusion (Cormack et al. 2009) |
| 7 | IIR ch.6, scoring and the vector space model | 34 | Passage Re-ranking with BERT (cross-encoder), arXiv 1901.04085 |
| 8 | IIR §6.2.2, tf-idf | 35 | ColBERT (late interaction), arXiv 2004.12832 |
| 9 | IIR ch.7, complete search system | 37 | Sentence-Transformers CrossEncoder usage |
| 10 | IIR ch.8, IR evaluation | 38 | RAG (Lewis et al. 2020), arXiv 2005.11401 |
| 11 | IIR §8.4, ranked evaluation | 39 | Lost in the Middle, arXiv 2307.03172 |
| 13 | IIR, Okapi BM25 section | 40 | RAPTOR, arXiv 2401.18059 |
| 15 | Robertson & Zaragoza, BM25 and beyond | 41 | Self-RAG, arXiv 2310.11511 |
| 16 | Sentence-BERT, arXiv 1908.10084 | 42 | Corrective RAG, arXiv 2401.15884 |
| 17 | Sentence-Transformers docs | 43 | From Local to Global (GraphRAG), arXiv 2404.16130 |
| 18 | SBERT semantic search guide | 44 | Microsoft GraphRAG docs |
| 19 | DPR, arXiv 2004.04906 | 45 | Cumulated gain (nDCG), Järvelin & Kekäläinen 2002 |
| 20 | MTEB, arXiv 2210.07316 | 47 | BEIR repo (reference metric code) |
| 22 | HNSW, arXiv 1603.09320 | 48 | Ragas, arXiv 2309.15217 |
| 24 | The Faiss library, arXiv 2401.08281 | 50 | ARES, arXiv 2311.09476 |
| 25 | Faiss docs/wiki | 51 | Judging LLM-as-a-Judge, arXiv 2306.05685 |
| 26 | Chroma, Evaluating Chunking Strategies | 52/53 | Cohere Embed / Rerank v2 API |
| 27 | chunking_evaluation code | 54/55 | GroqCloud docs / API reference (no embeddings or rerank endpoint) |
| 28 | NVIDIA chunking blog (vendor) | 29 | Pinecone chunking guide (vendor) |

Assumption: [01](01_SOURCE_INVENTORY.md) keeps the Source C numbering #1–#55. If it renumbers, match by the short title above.

---

## 2. Master traceability matrix

One row per concept ID in the BACKBONE (§2 there); there are 56 rows. Column meanings:
- **Book chapter/pages** links to that chapter's section in §3.
- **Required prerequisites** mirror the hard **Pre** lines of [02](02_RAG_MASTER_LEARNING_PLAN.md) (aligned in the cross-document consistency pass); the full edge list, including implied and soft edges, is in [03 §2.1](03_RAG_CONCEPT_DEPENDENCY_MAP.md#21-edge-list-authoritative-the-diagram-is-generated-from-it). Rows whose 02 Pre line names a gate or an alternative use the same typed notation as 02 ([§1.2 legend](02_RAG_MASTER_LEARNING_PLAN.md#12-card-legend-used-in-3)): `all{…}` every listed concept, `any{A1 | A2}` at least one of the group, `gate{3→4}` a learner gate in 02 §4, `exposure{…}` mechanism exposure only. Every Phase 4–11 concept also requires `gate{3→4}`.
- **Learning order** is `phase.step`. The step is the concept's position in the BACKBONE listing for its phase. [02](02_RAG_MASTER_LEARNING_PLAN.md) owns the schedule. Where the project version order in [06](06_RAG_PROJECT_AND_EVALUATION_PLAN.md) differs, the project order governs lab sequencing. For example, I5 (v1.2) is built before I3 (v1.3), and R3 (v2.1) before R2 (v2.2).
- **Proposed experiment** names the comparison only. Every experiment reports retrieval metrics and generation metrics separately. Result tables stay empty until the learner runs them (see [06](06_RAG_PROJECT_AND_EVALUATION_PLAN.md)).
- "—" means none exists. "not in book" and "not in repo" are explicit absences, not omissions by this file.

> Revised 2026-10-08 (Codex M-07): typed prerequisite notation added for rows with gates or alternatives (I-CMP, R3, A1, A2, A4, A5, S1, S2, S3, K1). See [corrections log](reviews/CORRECTIONS_LOG_2026-10-08.md#m-07).

### 2.1 Phase 0 (Orientation) and Phase 1 (Prerequisites)

| Concept (ID + name) | Pipeline stage | Required prerequisites | Book chapter/pages | Repo notebook/script path (+cells/lines) | What the book contributes | What the repo contributes | Missing explanation or implementation gap | Proposed experiment | Learning order (phase.step) | Priority (E/U/S) |
|---|---|---|---|---|---|---|---|---|---|---|
| **O1** Prior-knowledge diagnostic | Meta | — | not in book (closest: [Intro](#intro) p.7/8, reading modes) | not in repo | Says to read Ch1 first because later chapters assume its vocabulary (Intro p.7/8) | — | Diagnostic content must be written. It should probe the learner's own executed labs (CRAG, reliable RAG, rerank, hybrid, eval); see [05](05_LEARNING_AND_RETENTION_SYSTEM.md) | Blank-page pipeline drawing scored against the C6 trace; 12 diagnostic questions | 0.1 | E |
| **O2** Environment setup lab | Meta | — | not in book | not in repo. No requirements/pyproject. Version pins are rare (e.g. `simple_rag.ipynb cell 3`). `tests/test_imports.py` is an import smoke test. Notebooks star-import `helper_functions` (which imports PyMuPDF and rank_bm25, `helper_functions.py:L1-L15`) and, in 17 notebooks, `evaluation.evalute_rag` (which imports deepeval, `evaluation/evalute_rag.py:L19-L21`) | — | Shows the hidden dependency surface: star imports pull PyMuPDF, rank_bm25 and (via the eval script) deepeval into most notebooks | uv project, `.env`, provider switch. Groq has no embedding endpoint, so a local embedding model is required → C#1, C#54/55 (external) | Smoke test: embed 3 strings locally + 1 Groq chat call; record library versions | 0.2 | E |
| **O3** How to use this system | Meta | O1 | [Intro](#intro) p.7/8–p.8/8 (how to read; uniform chapter template) | not in repo | Chapter template: problem → idea → algorithm → tradeoffs | — | Coaching protocol, progress files and review cadence live in [05](05_LEARNING_AND_RETENTION_SYSTEM.md) | — | 0.3 | E |
| **P1** LLM fundamentals (tokens, context, sampling, cost) | Foundations | O2 | not in book. "Token" is never defined; it appears only in passing, e.g. [Ch10](#ch10-contextual-compression) p.12/13 | Units in use: `proposition_chunking.ipynb cell 9` (200 tiktoken tokens); `reliable_rag.ipynb cell 6` (500 tokens); `contextual_chunk_headers.ipynb cell 11` (4000-token truncation); `simple_rag_with_llamaindex.ipynb cell 4` (comment: LlamaIndex counts tokens, LangChain chars); `document_augmentation.ipynb cell 6` ("tokens" are regex words) | Uses tokens and latency as cost words in tradeoff tables | Concrete evidence that "chunk_size" means chars, BPE tokens or words depending on the notebook | Definitions, tokenizer differences, chars≈tokens heuristics and their limits, temperature, pricing → C#3, C#4, C#5 (external) | Count chars vs tiktoken tokens vs an HF tokenizer on climate-PDF chunks; plot the ratio distribution | 1.1 | E |
| **P2** IR framing (documents, queries, relevance, inverted index, ranking) | Foundations | — | [Intro](#intro) p.1/8; [Ch1](#ch1-simple-rag) p.1/14–p.3/14 (problem, core idea) | not in repo | Motivation: retrieve passages, then answer from them | — | Relevance labels, qrels, inverted index, ranking as a scoring problem → C#7, C#9, C#10 (external) | Hand-label 5 queries × 10 chunks (toy qrels), reused in P6 | 1.2 | E |
| **P3** Lexical retrieval: TF-IDF, BM25 | Retrieval (sparse) | P2 | [Ch12](#ch12-fusion-retrieval) p.5/14–p.6/14 (BM25 described verbally; no formula); TF-IDF not in book | `fusion_retrieval.ipynb cells 14-15` (BM25Okapi, whitespace `split()`); `helper_functions.py:L248-L273` (`bm25_retrieval`); `fusion_retrieval_with_llamaindex.ipynb cell 15` | Intuition: term statistics; exact-term queries where semantic search fails (BPA example, Ch12 p.1/14–p.2/14) | A working BM25Okapi index with default k1/b | No formula, no k1/b, and no effect of tokenization (case, punctuation) → C#8, C#13, C#15 (external) | Hand-compute one BM25 term score; then case-folded + punctuation-stripped tokenization vs `split()` on exact-term questions | 1.3 | E |
| **P4** Embeddings & similarity (cosine, dot, L2, normalization, bi-encoders, truncation, asymmetry) | Retrieval (dense) | P1, P2 | [Ch1](#ch1-simple-rag) p.5/14–p.6/14 (embeddings); cosine first used [Ch12](#ch12-fusion-retrieval) p.8/14, defined only in [App B](#appendix-b-glossary) p.15/23; bi- vs cross-encoder [Ch13](#ch13-reranking) p.6/13–p.7/13; query–document asymmetry [Ch6](#ch6-hypothetical-document-embedding) p.1/14–p.2/14 | `dartboard.ipynb cell 23` (distance = 1 − VVᵀ, assumes unit norm); `json_rag.ipynb cells 19-23` (all-MiniLM-L6-v2, raw L2 distances); `local_rag_huggingface_faiss.ipynb cell 14` (normalized bge-base) | Intuition: texts with similar meaning embed nearby ("greenhouse gas emissions" vs "carbon dioxide", Ch1 p.5/14–p.6/14) | Local embedding models in use; an L2-on-normalized example | The glossary says Ch1 explains cosine; it does not (DV-B4). Missing: L2 vs cosine vs dot, normalization, max sequence length, truncation → C#16–C#20 (external) | Verify numerically that cosine = dot after L2 normalization; embed one long chunk truncated vs full and compare similarity to its question | 1.4 | E |
| **P5** Vector search (exact k-NN, ANN, FAISS, metadata) | Retrieval (dense) | P4 | [Ch1](#ch1-simple-rag) p.6/14 (vector store; FAISS called a database) | `simple_csv_rag.ipynb cell 12` (hand-built `IndexFlatL2` + `InMemoryDocstore`); `json_rag.ipynb cell 21`; `simple_rag.ipynb cell 10` (`FAISS.from_documents`, flat L2 default) | Where the store sits in the pipeline | Exact flat index; docstore/id-map pattern | ANN (HNSW/IVF), persistence, metadata storage; FAISS is a library, not a database (DV-04) → C#22, C#24, C#25 (external) | NumPy exact k-NN vs FAISS `IndexFlatIP` on 100 queries: identical top-k? Time both | 1.5 | E (ANN internals U) |
| **P6** Retrieval evaluation basics (qrels, P@k, Recall@k, Hit@k, MRR, nDCG) | Evaluation | P2 | [Ch22](#ch22-rag-evaluation) p.4/19–p.6/19 (verbal; P@5 = 0.6 example p.4/19; MRR examples p.6/19) | not in repo. No Recall@k/MRR/nDCG anywhere (repo-wide check) | Verbal definitions; two tiny examples | — | Formulas, graded relevance, worked nDCG, Hit@k → C#10, C#11, C#45, C#47 (external) | Hand-compute, then unit-test Recall@k/MRR/nDCG on the P2 toy qrels; cross-check against a reference implementation | 1.6 | E |
| **P7** Prompting for grounded generation | Generation | P1 | [Ch1](#ch1-simple-rag) p.9/14 (question + chunks to the LLM); [Ch3](#ch3-reliable-rag) p.5/14–p.6/14 | `simple_csv_rag.ipynb cell 16` (stuff prompt); `local_rag_huggingface_faiss.ipynb cells 22-24` (context-only prompt with refusal, `[Page n]` tags); `helper_functions.py:L162-L205` (context-only QA chain, never called by a notebook); counter-example `reliable_rag.ipynb cell 18` ("based upon your knowledge") | The step "pass question plus chunks" | Several real prompt templates, including one that invites parametric answers | Instruction to cite, context ordering, lost-in-the-middle, context budget → C#39 (external) | Same retrieved context, two prompts (permissive vs context-only + cite): faithfulness and citation precision on 20 questions | 1.7 | E |

### 2.2 Phase 2 (Core RAG baseline, Project v0)

| Concept (ID + name) | Pipeline stage | Required prerequisites | Book chapter/pages | Repo notebook/script path (+cells/lines) | What the book contributes | What the repo contributes | Missing explanation or implementation gap | Proposed experiment | Learning order (phase.step) | Priority (E/U/S) |
|---|---|---|---|---|---|---|---|---|---|---|
| **C1** Document loading & parsing | Ingestion | O2 | [Ch1](#ch1-simple-rag) p.4/14 (load, page by page), p.5/14 (clean artifacts); [Ch16](#ch16-multi-modal-rag-with-captioning) p.4/11 (text and images) | `simple_rag.ipynb cell 10` (PyPDFLoader, one Document per page); `helper_functions.py:L223-L245` (`read_pdf_to_string` concatenates pages, so page provenance is lost); `helper_functions.py:L18-L31` (`replace_t_with_space`); `multi_model_rag_with_captioning.ipynb cells 8-9` (PyMuPDF text + images) | Parse page by page; clean before chunking | Two loaders with opposite provenance behaviour | The book lists several cleanups; the code replaces tabs only (DV-02). Headers/footers, hyphenation, multi-column and tables are absent in both | Parse the climate PDF and one two-column arXiv PDF with PyMuPDF vs pypdf; hand-count artifacts on 5 pages each | 2.1 | E |
| **C2** Chunking fundamentals (sample lesson) | Indexing | C1, P1 | [Ch1](#ch1-simple-rag) p.4/14, p.7/14, p.10/14–p.11/14; [App B](#appendix-b-glossary) p.14/23 (overlap about 200 chars) | `simple_rag.ipynb cells 10-11` (recursive 1000/200 chars); `helper_functions.py:L48-L76`; `context_enrichment_window_around_chunk.ipynb cell 13` (raw char slicer); `proposition_chunking.ipynb cell 9` (tokens); `document_augmentation.ipynb cell 6` (regex words) | The 1000/200 starting default; too-small (100) and too-large (5,000) examples (p.10/14–p.11/14) | Four incompatible size units side by side | Recursive separators unexplained (DV-03); overlap does not guarantee nothing is lost; provenance metadata. Full lesson: [07](07_SAMPLE_LESSON.md); external: C#26, C#29 | Defined in [07](07_SAMPLE_LESSON.md) (feeds I1) | 2.2 | E |
| **C3** Embedding & indexing with metadata | Indexing | C2, P5 | [Ch1](#ch1-simple-rag) p.5/14–p.6/14; [Ch8](#ch8-context-enrichment-window) p.4/11 (store chunk index); [Ch14](#ch14-hierarchical-indices) p.9/13–p.10/13 (role of metadata) | `simple_rag.ipynb cell 10`; `hierarchical_indices.ipynb cell 13` (`save_local`/`load_local`, pickle-based); `context_enrichment_window_around_chunk.ipynb cell 13` (index + whole document text in every chunk's metadata) | Metadata as the bridge between levels (Ch14) | Page metadata from PyPDFLoader; a persistence pattern | Embedding model never pinned (`helper_functions.py:L352-L354`). No doc_id, char offsets or params hash anywhere | Rebuild the index twice from one config: identical hash and ids? Change one chunk parameter: does the hash change? | 2.3 | E |
| **C4** Dense retrieval (top-k, score inspection) | Retrieval | C3 | [Ch1](#ch1-simple-rag) p.8/14 (top-K, typically 2–5), p.10/14 (sketch) | `simple_rag.ipynb cells 13-15` (k=2, no scores shown); `json_rag.ipynb cell 23` (prints L2 distances); `multi_faceted_filtering.ipynb cell 12` (relevance scores) | Embed the query with the same model; take the top-K | Score-printing examples (outside simple_rag) | Scores hidden in the baseline; "lower L2 = better" never explained | Score distributions for answerable vs unanswerable questions (input to V3) | 2.4 | E |
| **C5** Context construction & answer generation with citations | Generation | C4, P7 | [Ch1](#ch1-simple-rag) p.9/14–p.10/14; [Ch3](#ch3-reliable-rag) p.8/14–p.9/14 (attribution) | `local_rag_huggingface_faiss.ipynb cells 24, 28` (page-tagged context; answer + sources); `crag.ipynb cell 20` (`generate_response` cites sources); `helper_functions.py:L162-L205` | The generation step | Formatting and source-return patterns | `simple_rag.ipynb` never generates (DV-01). The `[doc:page]` citation format must be built | Citation format A (numbered + list) vs B (inline `[doc:page]`): citation precision/recall | 2.5 | E |
| **C6** Baseline pipeline v0 + provenance trace | Whole pipeline | C1–C5 | [Ch1](#ch1-simple-rag) p.7/14 and p.10/14 (both sketches) | `rs/simple_rag.py:L18-L61` (retrieval only; timing L36-L57); `local_rag_huggingface_faiss.ipynb cells 10-28` (end-to-end; generation is remote despite the "local" claim) | The full 2-phase pipeline in one place | A class-wrapped CLI script with timing | No trace of intermediates anywhere. v0 must be built framework-free | Gate check: two v0 runs give a byte-identical retrieval trace | 2.6 | E |
| **C7** Structured data RAG (CSV/JSON) | Ingestion + indexing | C6 | [Ch2](#ch2-rag-for-structured-data) p.3/11–p.9/11 (sketches p.6/11, p.8/11) | `simple_csv_rag.ipynb cells 10-18`; `simple_csv_rag_with_llamaindex.ipynb cells 10-17`; `json_rag.ipynb cells 13-23` | Row serialization; large tables; when not to use | Row → "column: value" documents; JSON field selection (jRAG) | Top-K silently drops rows for "list all" questions (DV-07); no SQL/filter hybrid | "List all customers in country X": recall of rows at k=4 vs a pandas filter ground truth | 2.7 | S |

### 2.3 Phase 3 (Measurement first, Project v0.1)

| Concept (ID + name) | Pipeline stage | Required prerequisites | Book chapter/pages | Repo notebook/script path (+cells/lines) | What the book contributes | What the repo contributes | Missing explanation or implementation gap | Proposed experiment | Learning order (phase.step) | Priority (E/U/S) |
|---|---|---|---|---|---|---|---|---|---|---|
| **M1** Building an evaluation set | Evaluation | P6, C6 | [Ch22](#ch22-rag-evaluation) p.12/19–p.13/19 (golden, synthetic and adversarial data; the 200–500 size is unsourced) | `data/q_a.json` (44 Q/A, no evidence pages; heuristically pp.1–5 only); `choose_chunk_size.ipynb cell 6` (LLM-generated, unseeded sample); `evaluation/evalute_rag.py:L133-L138` (fresh LLM questions every run) | Kinds of eval data and an expert-review loop | Examples of what not to do (no gold evidence, non-reproducible questions) | Span-level gold evidence, unanswerables, categories. Schema in [06](06_RAG_PROJECT_AND_EVALUATION_PLAN.md) | Re-chunk check: span labels yield valid chunk relevance under 3 chunkings | 3.1 | E |
| **M2** Retrieval metrics harness | Evaluation | M1, P6 | [Ch22](#ch22-rag-evaluation) p.4/19–p.7/19 | not in repo (no rank metric in any `.py` or notebook source) | Verbal metric definitions | — | Whole harness missing (DV-43) → C#47 (external) | Run the v0 harness twice: identical metrics (determinism gate) | 3.2 | E |
| **M3** Generation metrics & LLM-as-judge | Evaluation | M1, C5 | [Ch22](#ch22-rag-evaluation) p.7/19–p.10/19 (faithfulness sketch p.8/19; judge biases p.10/19) | `evaluation/define_evaluation_metrics.ipynb cells 3-11`; `evaluation/evaluation_deep_eval.ipynb cells 2-9`; `evaluation/end-2-end_rag_evaluation.ipynb cells 12-19` (judges vs human labels); `evaluation/evaluation_grouse.ipynb cells 36, 39` (judge meta-evaluation); `evaluation/open-rag-eval-example.ipynb cells 7-14` (UMBRELA, nuggets, citation P/R) | Claim-decomposition faithfulness; answer relevance; completeness; judge bias list | Five eval frameworks; two judge-validation examples | All judges are OpenAI models. Bugs: `define_evaluation_metrics.ipynb cell 9` NameError; `end-2-end_rag_evaluation.ipynb cell 22` undefined names → C#48, C#50, C#51 (external) | Label a human generation pilot on v0 (≥ 30 answer-level labels; a rubric pilot, not a certification). The Cohere judge is certified only in the end-of-curriculum batch, on a separate validation set with ≥ 30 failure and ≥ 30 non-failure units per metric and intervals chosen by statistic: confusion matrix as counts, Wilson 95% (or a cluster bootstrap over answers) for binomial rates, bootstrap or κ variance for κ (D-10; [06 §8.4](06_RAG_PROJECT_AND_EVALUATION_PLAN.md#84-calibration-against-human-labels)) | 3.3 | E |
| **M4** Experimental discipline | Evaluation / ops | M2, M3 | [Ch22](#ch22-rag-evaluation) p.13/19–p.15/19 (component vs end-to-end; latency, cost); [App A](#appendix-a-decision-guide) p.12/23 (measure before and after each change) | `rs/simple_rag.py:L36-L57`, `rs/semantic_chunking.py:L51-L73` (wall-clock timing only); `choose_chunk_size.ipynb cell 6` (`random.sample`, no seed) | Component-level measurement; percentile latency | Timing snippets | Seeds, caching, variance, ablation protocol | 5 reruns of v0 at temperature 0, with and without a response cache: spread of retrieval metrics and deterministic generation metrics (judge repeat variance is measured in the final judge batch, D-10) | 3.4 | E |
| **M5** Failure analysis taxonomy | Evaluation | M2, M3 | [App A](#appendix-a-decision-guide) p.3/23–p.5/23 (symptom families); [Ch22](#ch22-rag-evaluation) p.1/19 (three complaints mapped to failures) | not in repo | Symptom → technique map | — | The "failure points" literature named in the BACKBONE is **not** in the verified Source C registry (UNVERIFIED; see REVIEWER NOTE R-3) | Bucket every v0 failure (retrieval miss / wrong rank / context / generation); counts only | 3.5 | E |

> Revised 2026-10-08 (Codex M-06; learner decision D-10): M3's experiment is a human-labelled pilot (the Cohere judge is certified only in the final batch); M4's reruns no longer call a judge. See [corrections log](reviews/CORRECTIONS_LOG_2026-10-08.md#m-06).

> Revised 2026-10-08 (Codex re-review R-03): M3's certification cell names intervals by statistic (counts for the confusion matrix, Wilson or a cluster bootstrap for binomial rates, bootstrap or κ variance for κ) instead of Wilson for everything. See [corrections log](reviews/CORRECTIONS_LOG_2026-10-08.md#r-03).

### 2.4 Phase 4 (Indexing & representation, Project v1.x)

| Concept (ID + name) | Pipeline stage | Required prerequisites | Book chapter/pages | Repo notebook/script path (+cells/lines) | What the book contributes | What the repo contributes | Missing explanation or implementation gap | Proposed experiment | Learning order (phase.step) | Priority (E/U/S) |
|---|---|---|---|---|---|---|---|---|---|---|
| **I1** Chunk size/overlap experiments | Indexing | M4, C2 | [Ch1](#ch1-simple-rag) p.10/14–p.11/14; [Ch6](#ch6-hypothetical-document-embedding) p.9/14–p.10/14 (matching chunk size); [Ch8](#ch8-context-enrichment-window) p.7/11 (window size) | `choose_chunk_size.ipynb cells 6-12` (128/256 tokens via LlamaIndex; saved output is a 1.00/1.00 ceiling; cell 12 output is stale); `rs/choose_chunk_size.py:L23-L123` | Dilution vs fragmentation tradeoff | A sweep skeleton scored only by an LLM judge | No retrieval metric; ceiling effect; units differ from the book (DV-06) | v1.0 grid size × overlap; compare at fixed k and at equal token budget | 4.1 | E |
| **I2** Structure-aware chunking | Indexing | I1, C1 | not in book as a technique. Hints: [Ch7](#ch7-contextual-chunk-headers) p.8/11 (section-path headers); [Ch14](#ch14-hierarchical-indices) p.4/13 (logical sections) | not in repo. Closest: recursive separators in `simple_rag.ipynb cell 10` | A section is a natural unit | — | Gap in both sources → C#28, C#29 (external, vendor) | v1.1 heading/page-aware vs best v1.0 | 4.2 | U |
| **I3** Semantic chunking | Indexing | I1, P4 | [Ch9](#ch9-semantic-chunking) p.4/14–p.8/14 (sketch p.7/14) | `semantic_chunking.ipynb cells 11-18`; `rs/semantic_chunking.py:L19-L78` | Sentence-distance breakpoints; percentile / std-dev / IQR | LangChain SemanticChunker, percentile 90 | No size caps; distance curve never shown; library internals vs book IQR formula UNVERIFIED (DV-23) | v1.3 vs best fixed size; log chunk-length distribution | 4.3 | U |
| **I4** Proposition chunking | Indexing | I1, I3, M3 | [Ch4](#ch4-proposition-chunking) p.4/15–p.10/15 (sketches p.6/15, p.9/15) | `proposition_chunking.ipynb cells 9-38` | 5 proposition properties; 4 QC criteria, threshold 7 | Full generate + grade pipeline (Groq) | No answer step and a degenerate baseline (DV-15); per-proposition grading cost (DV-14) → C#30 (external) | v1.4 on a subset: retrieval metrics + index-time LLM calls; variant that returns the parent chunk | 4.4 | S/U |
| **I5** Contextual chunk headers | Indexing | I1, C3 | [Ch7](#ch7-contextual-chunk-headers) p.4/11–p.9/11 (sketch p.8/11) | `contextual_chunk_headers.ipynb cells 9-15` | Prepend a header; keep it for reranking and generation | Title generation; a one-chunk rerank demo | No header index is ever built; 0.1→0.9 is a reranker score (DV-19, DV-20) → C#31 (external) | v1.2 title header vs none; then title + section path | 4.5 | U |
| **I6** Document augmentation & HyPE | Indexing | I1, M3 (pairs with Q2) | [Ch11](#ch11-document-augmentation) p.6/13–p.11/13 (sketch p.8/13) | `document_augmentation.ipynb cells 4-17`; `rs/document_augmentation.py:L52-L150`; `HyPE_Hypothetical_Prompt_Embeddings.ipynb cells 7-21` (cell 11 SyntaxError, static reading); `rs/HyPE_Hypothetical_Prompt_Embeddings.py:L21-L153` | Questions per chunk with a parent pointer; mirror of HyDE | Two designs: chunks + questions vs questions only | No baseline; "parent" is a 4000-word document (DV-25); duplicate parents in top-k | Vocabulary-mismatch subset: questions-only vs chunks + questions vs baseline | 4.6 | S |
| **I-CMP** Granularity family comparison | Indexing | `all{I1}; exposure{I2, I3, I4, I5, I6}; gate{3→4}` | [Ch9](#ch9-semantic-chunking) p.10/14–p.11/14 (spectrum); [Ch4](#ch4-proposition-chunking) p.10/15–p.11/15; [Ch8](#ch8-context-enrichment-window) p.7/11–p.8/11 | — (spread across the notebooks above) | Qualitative comparisons only | — | No side-by-side measurement anywhere → C#26, C#27 (external) | Consolidated v1.x results table (template in [06](06_RAG_PROJECT_AND_EVALUATION_PLAN.md)) | 4.7 | E |

> Revised 2026-10-08 (Codex M-07): I-CMP prerequisites typed (mechanism exposure to I2–I6 is required). See [corrections log](reviews/CORRECTIONS_LOG_2026-10-08.md#m-07).

### 2.5 Phases 5–7 (Retrieval, Query, Context)

| Concept (ID + name) | Pipeline stage | Required prerequisites | Book chapter/pages | Repo notebook/script path (+cells/lines) | What the book contributes | What the repo contributes | Missing explanation or implementation gap | Proposed experiment | Learning order (phase.step) | Priority (E/U/S) |
|---|---|---|---|---|---|---|---|---|---|---|
| **R1** Sparse vs dense vs hybrid; weighted fusion vs RRF | Retrieval | P3, P4, M4 | [Ch12](#ch12-fusion-retrieval) p.4/14–p.12/14 (sketch p.10/14) | `fusion_retrieval.ipynb cells 10-19` (cell 17 adds misaligned arrays, static reading); `rs/fusion_retrieval.py:L20-L116` (no epsilon, L80-L81); `fusion_retrieval_with_llamaindex.ipynb cells 15-22` | Score normalization + weighted sum; weight ranges | Two weighted-fusion implementations; RRF named as a mode (llamaindex cell 20) | RRF absent from the book (DV-28); alignment bug (DV-27) → C#33 (external) | v2.0: BM25 vs dense vs weighted vs RRF on exact-term and paraphrase categories | 5.1 | E |
| **R2** Metadata filtering | Retrieval | C3, R1 | not in book as a technique; [Ch14](#ch14-hierarchical-indices) p.7/13 and p.9/13–p.10/13 (filter by section metadata) | `multi_faceted_filtering.ipynb cells 7-24`; `rs/multi_faceted_filtering.py:L20-L131` (filters L44-L131; no LLM) | Section metadata as a filter key | Four composable post-filters | Pre- vs post-filter recall loss; demo has one matching row | v2.2: doc-scoped questions with vs without filter | 5.2 | U |
| **R3** Reranking (cross-encoder vs LLM; pool size) | Retrieval | `all{P4}; any{R1 \| C4}; gate{3→4}` | [Ch13](#ch13-reranking) p.4/13–p.11/13 (sketches p.9/13, p.10/13) | `reranking.ipynb cells 15-29`; `rs/reranking.py:L26-L143`; `reranking_with_llamaindex.ipynb cells 16-23` | Two-stage idea; K=10–30 → N=3–5 | Local cross-encoder `ms-marco-MiniLM-L-6-v2`; pointwise LLM scorer | No measurement; long-chunk truncation; logits are not probabilities → C#34, C#37 (external) | v2.1: candidate pool 10/20/50 × rerank on/off; latency per query | 5.3 | E |
| **R4** Diversity: MMR / Dartboard | Retrieval | R3, P4 | [Ch15](#ch15-dartboard-retrieval) p.4/12–p.9/12 (sketch p.7/12) | `dartboard.ipynb cells 9-25` (cell 25 TypeError, static reading) | Oversample, then greedy relevance + diversity | Information-gain implementation (arXiv 2407.12101, cited in cell 0) | Book rule ≠ code (DV-31). The MMR primary paper is not in Source C (UNVERIFIED; REVIEWER NOTE R-4) | v2.3: MMR λ sweep vs dartboard on multi-span questions; report a redundancy measure | 5.4 | U |
| **R5** Hierarchical retrieval (indices, RAPTOR) | Retrieval | R3, M5 | [Ch14](#ch14-hierarchical-indices) p.4/13–p.10/13 (sketch p.7/13) | `hierarchical_indices.ipynb cells 11-17`; `rs/hierarchical_indices.py:L22-L107`; `raptor.ipynb cells 9-33`; `rs/raptor.py:L119-L205` | Summary routing, then filtered detail search | Page-level two-store index; RAPTOR tree (bugs, static reading) | Recall lost when routing picks the wrong section; RAPTOR uncited → C#40 (external) | v8 option: summary routing vs flat on synthesis questions | 5.5 | S |
| **Q1** Query transformations | Query | R3, M5 | [Ch5](#ch5-query-transformations) p.4/14–p.11/14 (sketches p.6/14, p.8/14, p.10/14) | `query_transformations.ipynb cells 6-16`; `rs/query_transformations.py:L14-L124` | Three strategies; keep the original question for generation | Prompt templates only | No retrieval, merge, dedup or generation (DV-16); parse bug (DV-17) | v3.0 on failing categories only: per-strategy CE@k (Complete-Evidence@k; Span-Coverage@k as diagnostic) | 6.1 | U |
| **Q2** HyDE vs HyPE (query-time vs index-time) | Query | Q1, P4 | [Ch6](#ch6-hypothetical-document-embedding) p.5/14–p.11/14 (sketch p.7/14); [Ch11](#ch11-document-augmentation) p.9/13–p.10/13 (mirror image) | `HyDe_Hypothetical_Document_Embedding.ipynb cells 12-18`; `rs/HyDe_Hypothetical_Document_Embedding.py:L19-L59` | The hypothetical answer is embedded, then discarded | Retriever class | No generation and no baseline (DV-18) → C#32 (external) | v3.1: HyDE vs raw query vs HyPE on the vocabulary-mismatch subset | 6.2 | U |
| **X1** Context enrichment window & RSE | Context | C3, X3 (concurrent) | [Ch8](#ch8-context-enrichment-window) p.4/11–p.8/11 (sketch p.6/11) | `context_enrichment_window_around_chunk.ipynb cells 13-27`; `rs/context_enrichment_window_around_chunk.py:L17-L120`; `context_enrichment_window_around_chunk_with_llamaindex.ipynb cells 12-24`; `relevant_segment_extraction.ipynb cells 7-21` | Neighbour expansion with overlap trimming | Three designs: chunk-index window, sentence window, RSE | Linear-scan lookup; overlap-default mismatch (DV-22); multi-document indexing | v4.0: window N=0/1/2 at equal token budget | 7.1 | U |
| **X2** Contextual compression | Context | X3, M3 | [Ch10](#ch10-contextual-compression) p.5/13–p.11/13 (sketch p.8/13) | `contextual_compression.ipynb cells 10-14`; `rs/contextual_compression.py:L20-L89` | Per-chunk, query-aware extraction; grade-then-compress | LLMChainExtractor pipeline | No before/after view; extraction may not be verbatim; grade-then-compress missing (DV-24) | v4.1: compression vs none: CE on the final assembled context, context tokens, faithfulness, answer correctness (human labels until the final judge batch, D-10) | 7.2 | U |
| **X3** Context assembly (dedup, ordering, budget, citation formatting) | Context | C5, P7, R3 | not in book as a topic. Fragments: [Ch5](#ch5-query-transformations) p.10/14 (dedup sub-query results); [Ch8](#ch8-context-enrichment-window) p.5/11 (overlap-aware joining); [Ch10](#ch10-contextual-compression) p.12/13 (context-window tokens) | Fragments only: `HyPE_Hypothetical_Prompt_Embeddings.ipynb cell 19` (`set()` dedup, loses order); `memorag.ipynb cell 28` (order-preserving dedup); `graph_rag.ipynb cell 12` (`max_context_length` defined but unused); `multi_faceted_filtering.ipynb cell 20` (near-duplicate filter) | Scattered hints | Scattered dedup snippets | Ordering, token budgeting and citation formatting are missing in both → C#39 (external) | v4.0 ablation: dedup / ordering / budget toggled one at a time | 7.3 | E |

> Revised 2026-10-08 (Codex M-07, M-02): R3 prerequisites typed; Q1's proposed experiment now names CE@k (Complete-Evidence@k) as the primary metric instead of span-coverage Recall@k; X2's v4.1 experiment adds final-context CE and human labels until the final judge batch (M-02, M-06; cross-document sweep). See [corrections log](reviews/CORRECTIONS_LOG_2026-10-08.md#m-07) and [M-02](reviews/CORRECTIONS_LOG_2026-10-08.md#m-02).

### 2.6 Phases 8–12 (Reliability, Production, Control flow, Specialized, Capstone)

| Concept (ID + name) | Pipeline stage | Required prerequisites | Book chapter/pages | Repo notebook/script path (+cells/lines) | What the book contributes | What the repo contributes | Missing explanation or implementation gap | Proposed experiment | Learning order (phase.step) | Priority (E/U/S) |
|---|---|---|---|---|---|---|---|---|---|---|
| **V1** Grounded answers & citation verification | Generation / verification | X3, M3 | [Ch3](#ch3-reliable-rag) p.8/14–p.9/14 (Step 5 attribution); [Ch19](#ch19-explainable-retrieval) p.3/10–p.7/10 (sketch p.5/10) | `reliable_rag.ipynb cells 22-23` (highlighted segments, no substring check); `explainable_retrieval.ipynb cell 6`; `rs/explainable_retrieval.py:L17-L50`; `graph_rag_local_attribution.ipynb cells 7, 9` (citation dataclasses; unverified source sentences) | Attribution step; explanation-prompt craft | LLM-reported segments and explanations | Programmatic verification (substring or span overlap) is absent everywhere (DV-11). See REVIEWER NOTE R-1 on the Ch19 mapping | v5.0: precision/recall of verified citations | 8.1 | E |
| **V2** Reliable RAG (relevance grading + groundedness check) | Verification | V1, M3 | [Ch3](#ch3-reliable-rag) p.4/14–p.11/14 (sketches p.5/14, p.8/14, p.9/14) | `reliable_rag.ipynb cells 6-23` | Retrieve → grade → generate → verify → trace | Groq + Cohere implementation (closest to the learner's keys) | No retry branch (DV-10); prompt invites parametric answers (DV-09); grader accuracy unmeasured | Grader precision/recall against M1 span-derived relevance | 8.2 | E |
| **V3** Answerability & abstention | Generation | V2, M1 | [Ch3](#ch3-reliable-rag) p.11/14 ("I don't know" preferred; no algorithm) | `adaptive_retrieval.ipynb cell 23` (prompt allows "don't know"); `local_rag_huggingface_faiss.ipynb cells 22, 26` (refusal instruction; out-of-scope probe, no saved output); `crag.ipynb cell 26`, `self_rag.ipynb cell 20` (out-of-domain probes) | A stated preference only | Probes, never evaluated | Thresholds, refusal policy, abstention metrics | Score-threshold sweep: abstention precision/recall, tuned on `dev` and reported on `test`; no threshold claim until ≥ 15 unanswerables exist with ≥ 5 in dev (6 is a learning minimum only) | 8.3 | E |
| **V4** Hallucination-detection limits & judge reliability | Evaluation | M3, V2 | [Ch22](#ch22-rag-evaluation) p.9/19–p.10/19 (judge biases); [Ch3](#ch3-reliable-rag) p.10/14–p.11/14 (choosing verification models) | `evaluation/evaluation_grouse.ipynb cells 24-39`; `evaluation/open-rag-eval-example.ipynb cells 11-12` (hallucination score; the notebook does not name the model behind it, so "HHEM" is UNVERIFIED) | Bias list and mitigations | Two judge meta-evaluations | Self-grading with the same model (`reliable_rag.ipynb cells 18, 20`) | V2 grader vs human labels and a labelled challenge set (Phase 8; Wilson intervals for error/recall rates, bootstrap or κ-variance interval for κ, confusion matrix as counts); Cohere evaluation judge vs human and Codex labels only in the final judge batch (D-10; revised 2026-10-08, Codex M-06) | 8.4 | U |
| **D1** Observability (structured traces) | Ops | C6, M4 | [Ch22](#ch22-rag-evaluation) p.14/19–p.16/19 | not in repo (prints only) | Per-component monitoring idea | — | Trace schema and logging missing | Every v0 query emits a complete trace (query, candidates, scores, context, prompt, answer, citations) | 9.1 | E |
| **D2** Latency & cost budgets, caching | Ops | D1, P1 | [Ch22](#ch22-rag-evaluation) p.14/19–p.15/19 (p50/p95/p99; quality-vs-cost example) | `rs/simple_rag.py:L36-L57`, `rs/light_rag.py:L151-L257` (time_records); `rs/graph_rag.py:L539` (`get_openai_callback`); `hierarchical_indices.ipynb cell 11` (batching + backoff via `helper_functions.py:L294-L321`, which re-awaits a coroutine) | Percentiles; quality-cost tradeoff | Timing snippets only | Token/cost accounting; response caching | p50/p95 latency and tokens per query for v0 and every accepted version | 9.2 | E |
| **D3** Regression eval in CI, index versioning, incremental re-index | Ops | D1, M4 | [Ch22](#ch22-rag-evaluation) p.15/19 (offline → shadow → A/B → monitor); [Ch17](#ch17-retrieval-with-feedback-loops) p.7/11 (periodic re-index) | `tests/test_imports.py` (import smoke only); `hierarchical_indices.ipynb cell 13` (cached stores reused; stale-cache risk) | Production evaluation loop | Cache-reuse pattern | No CI eval; no incremental indexing | A pytest threshold test fails when a deliberate regression is injected | 9.3 | U |
| **D4** Security & safety (injection, access control, PII) | Ops | X3, R2 | [Ch22](#ch22-rag-evaluation) p.16/19–p.17/19 (safety evaluation, incl. prompt injection) | not in repo. Anti-patterns: `crag.ipynb cells 20-22` (raw web text into the prompt); `Microsoft_GraphRag.ipynb cell 14` (API key written into settings.yaml) | Safety test categories | Anti-patterns to recognise | Injection via retrieved docs; ACL via metadata; PII | Plant an injection document: attack success rate before/after mitigation | 9.4 | U |
| **A1** Adaptive retrieval / routing | Control flow | `all{Q1, M5}; gate{3→4, 9→10}` | [Ch18](#ch18-adaptive-retrieval) p.3/12–p.10/12 (sketches p.6/12, p.9/12) | `adaptive_retrieval.ipynb cells 7-27`; `rs/adaptive_retrieval.py:L28-L221` | Classify → 4 routed strategies | Strategy classes | Opinion path crash; user context never passed (DV-37, DV-38) | Router accuracy on labelled categories + per-route retrieval metrics | 10.1 | U |
| **A2** Corrective RAG | Control flow | `all{V2, V3}; gate{3→4, 9→10}` | [Ch20](#ch20-corrective-rag) p.3/11–p.8/11 (sketch p.6/11) | `crag.ipynb cells 12-26`; `rs/crag.py:L42-L184` | 0.3/0.7 confidence routing; knowledge refinement | Complete flow with DuckDuckGo | Uncalibrated thresholds; search-result parsing bug (DV-40) → C#42 (external) | Threshold sweep on an answerable/unanswerable mix, web branch disabled | 10.2 | U |
| **A3** Self-RAG | Control flow | A2 | not in book | `self_rag.ipynb cells 14-20`; `rs/self_rag.py:L21-L150` | — | Prompted approximation of reflection steps | Not the paper's trained model → C#41 (external) | Retrieve-decision accuracy vs always-retrieve | 10.3 | S |
| **A4** Feedback loops | Control flow | `all{D1}; any{A1 \| A2}; gate{3→4}` | [Ch17](#ch17-retrieval-with-feedback-loops) p.3/11–p.9/11 (sketch p.7/11) | `retrieval_with_feedback_loop.ipynb cells 10-24`; `rs/retrieval_with_feedback_loop.py:L26-L124` | avg/3 score multiplier; periodic enrichment | Feedback store; LLM applicability judge | Case bug; adjusted ranking unused; poisoning (DV-35, DV-36) | Simulated noisy raters: metric drift over rounds | 10.4 | S |
| **A5** Agentic RAG | Control flow | `all{D1, D2}; any{A1 \| A2}; gate{3→4, 8→9}` | not in book ("agentic" appears only as an example topic, Ch3 p.1/14) | `Agentic_RAG.ipynb cells 9-72` (vendor platform) | — | Vendor black box | Mechanism not inspectable | Deferred until after the Phase 8 gate | 10.5 | S |
| **S1** Graph RAG | Architecture | `all{M5}; gate{3→4, 9→10}` (only if M5 shows multi-hop/global failures) | [Ch21](#ch21-graph-rag) p.4/13–p.10/13 (sketch p.8/13) | `Microsoft_GraphRag.ipynb cells 12-21` (CLI only); `graph_rag.ipynb cells 7-26`; `rs/graph_rag.py:L49-L789`; `light_rag.ipynb cells 10-28`; `rs/light_rag.py:L95-L269`; `graphrag_with_milvus_vectordb.ipynb cells 12-38`; `graph_rag_local_attribution.ipynb cells 5-19` | Entity graph, Leiden, community summaries, local/global search | Five different "graph" designs | Only the black-box notebook matches the book (DV-41, DV-42) → C#43, C#44 (external) | v8 option on the global/multi-hop subset only | 11.1 | S |
| **S2** Multimodal RAG | Architecture | `all{C1}; gate{3→4}` | [Ch16](#ch16-multi-modal-rag-with-captioning) p.4/11–p.9/11 (sketch p.6/11) | `multi_model_rag_with_captioning.ipynb cells 8-20`; `multi_model_rag_with_colpali.ipynb cells 9-24` | Caption images; embed with text | Caption and page-image (ColPali) paths | Tables not captioned; page metadata implicit (DV-34); ColPali uncited → C#35 (external, late interaction) | Figure/table question subset: captions vs text-only | 11.2 | S |
| **S3** MemoRAG | Architecture | `any{S1 \| R5}; gate{3→4}` | not in book | `memorag.ipynb cells 9-72` | — | Simplified memory + clue queries | Eval calls broken (cells 45, 62); data artifacts missing from the repo | Deferred | 11.3 | S |
| **K1** Capstone architecture defence | All | `all{I-CMP, V3, D2}; gate{3→4, 9→10}` (no A*/S* required; D3 is advice) | [App A](#appendix-a-decision-guide) p.7/23–p.11/23 (stacks, quick-reference tables), p.12/23 | not in repo | Decision heuristics (ratings are unmeasured) | — | Evidence must come from the learner's own v0–v7 results | Transfer: rerun the best configuration on corpus H and compare deltas against v0 | 12.1 | E |

> Revised 2026-10-08 (Codex M-07): A1, A2, A4, A5, S1, S2, S3 and K1 prerequisites typed; A5/A4 need A1 or A2, S3 needs S1 or R5, K1 needs I-CMP, V3, D2 and Gate 9→10 but no A*/S* elective. See [corrections log](reviews/CORRECTIONS_LOG_2026-10-08.md#m-07).

> Revised 2026-10-08 (Codex M-05, M-06): V3's threshold sweep is tuned on `dev`, reported on `test`, and makes no threshold claim until ≥ 15 unanswerables exist with ≥ 5 in dev. See [corrections log](reviews/CORRECTIONS_LOG_2026-10-08.md#m-06).

> Revised 2026-10-08 (Codex re-review R-03): V4's experiment cell no longer implies Wilson intervals for κ or the confusion matrix. See [corrections log](reviews/CORRECTIONS_LOG_2026-10-08.md#r-03).

> **REVIEWER NOTE R-1 (V1 book source).** BACKBONE V1 names Ch19 as its book chapter. Ch19's explanations are LLM rationalisations produced after retrieval, and Ch19 p.8/10 itself sends claim-level tracing to Ch3's source attribution. The closest book source for *citation verification* is therefore **Ch3 Step 5 (p.8/14–p.9/14)**. Ch19 is secondary: it teaches explanation-prompt craft and why explanations are not evidence. The matrix lists both, Ch3 first. Proposed: keep the V1 ID and treat Ch3 as its primary book anchor.
>
> **REVIEWER NOTE R-2 (I-CMP and X3 rows).** Neither concept has a book chapter or a notebook of its own. The cited pages and cells are fragments, and no source compares them. The listed experiments are the only place these concepts get evidence.
>
> **REVIEWER NOTE R-3 (M5 sources).** BACKBONE M5 cites "supplementary failure points literature". No such paper is in the verified Source C registry ([01](01_SOURCE_INVENTORY.md); C#1–C#55). Until a reference is verified, M5 rests on App A p.3/23–p.5/23 plus the learner's own error buckets. The external reference is UNVERIFIED.
>
> **REVIEWER NOTE R-4 (MMR source).** The book never explains MMR; it appears only as a label in App p.3/23 and the glossary p.19/23. The original MMR paper is not in Source C, so R4 currently has no verified primary source for MMR. The dartboard notebook's own source (arXiv 2407.12101, `dartboard.ipynb cell 0`) is a repo citation. It has not been checked by this pass.

---

## 3. Chapter-by-chapter mapping

### 3.0 Coverage at a glance

Column definitions:
- **Fidelity** is how much of the chapter's algorithm the code actually performs. It is judged by static reading only.
- **Runs as written?** assumes the learner's credentials (Groq and Cohere keys, no OpenAI key, Ollama not installed) and the pinned code. Detail is in [01](01_SOURCE_INVENTORY.md) and [08](08_GAP_ANALYSIS_AND_DECISIONS.md).

| Book unit | Primary notebook(s) | Runnable script | Fidelity to book | Runs as written? | Concept IDs |
|---|---|---|---|---|---|
| [Intro](#intro) | — | — | n/a | n/a | O3, P2 |
| [Ch1](#ch1-simple-rag) Simple RAG | simple_rag; also choose_chunk_size, simple_rag_with_llamaindex | rs/simple_rag.py, rs/choose_chunk_size.py | Partial (no generation) | No (OpenAI) | C1–C6, I1 |
| [Ch2](#ch2-rag-for-structured-data) Structured data | simple_csv_rag; simple_csv_rag_with_llamaindex | — | Implemented for one lookup query | No (OpenAI) | C7 |
| [Ch3](#ch3-reliable-rag) Reliable RAG | reliable_rag | — | Partial (no retry branch, no verbatim check) | Keys match (Groq + Cohere). Model ids may be retired (UNVERIFIED) | V2, V1, V3 |
| [Ch4](#ch4-proposition-chunking) Propositions | proposition_chunking | — | Partial (no answer step) | No (needs Ollama) | I4 |
| [Ch5](#ch5-query-transformations) Query transformations | query_transformations | rs/query_transformations.py | Partial (strings only) | No (OpenAI) | Q1 |
| [Ch6](#ch6-hypothetical-document-embedding) HyDE | HyDe_Hypothetical_Document_Embedding | rs/HyDe_Hypothetical_Document_Embedding.py | Partial (no generation) | No (OpenAI) | Q2 |
| [Ch7](#ch7-contextual-chunk-headers) Contextual headers | contextual_chunk_headers | — | Diverges (rerank demo, no index) | No (OpenAI + Cohere) | I5 |
| [Ch8](#ch8-context-enrichment-window) Context window | context_enrichment_window_around_chunk; …_with_llamaindex | rs/context_enrichment_window_around_chunk.py | Implemented (inefficient lookup) | No (OpenAI) | X1 |
| [Ch9](#ch9-semantic-chunking) Semantic chunking | semantic_chunking | rs/semantic_chunking.py | Implemented through a library (black box) | No (OpenAI) | I3 |
| [Ch10](#ch10-contextual-compression) Compression | contextual_compression | rs/contextual_compression.py | Implemented through a library | No (OpenAI) | X2 |
| [Ch11](#ch11-document-augmentation) Augmentation | document_augmentation (+ HyPE, repo-only) | rs/document_augmentation.py | Diverges ("parent" = 4000-word doc) | No (OpenAI) | I6 |
| [Ch12](#ch12-fusion-retrieval) Fusion | fusion_retrieval; fusion_retrieval_with_llamaindex | rs/fusion_retrieval.py | Diverges (alignment bug; numbers from the LlamaIndex variant) | No (OpenAI) | R1, P3 |
| [Ch13](#ch13-reranking) Reranking | reranking; reranking_with_llamaindex | rs/reranking.py | Implemented | No (OpenAI embeddings; the cross-encoder itself is local) | R3 |
| [Ch14](#ch14-hierarchical-indices) Hierarchical | hierarchical_indices (+ raptor, repo-only) | rs/hierarchical_indices.py | Partial (no generation; up to 15 chunks) | No (OpenAI) | R5 |
| [Ch15](#ch15-dartboard-retrieval) Dartboard | dartboard | — | Diverges (different diversity rule; cell 25 cannot run) | No (OpenAI) | R4 |
| [Ch16](#ch16-multi-modal-rag-with-captioning) Multimodal | multi_model_rag_with_captioning (+ colpali, repo-only) | — | Implemented (images only) | No (Gemini key absent) | S2 |
| [Ch17](#ch17-retrieval-with-feedback-loops) Feedback loops | retrieval_with_feedback_loop | rs/retrieval_with_feedback_loop.py | Diverges (adjustment likely dead code) | No (OpenAI) | A4 |
| [Ch18](#ch18-adaptive-retrieval) Adaptive | adaptive_retrieval | rs/adaptive_retrieval.py | Partial (opinion crash, context unwired) | No (OpenAI) | A1 |
| [Ch19](#ch19-explainable-retrieval) Explainable | explainable_retrieval | rs/explainable_retrieval.py | Implemented (toy corpus) | No (OpenAI) | V1 |
| [Ch20](#ch20-corrective-rag) Corrective RAG | crag | rs/crag.py | Implemented (parsing bug) | No (OpenAI) | A2 |
| [Ch21](#ch21-graph-rag) Graph RAG | Microsoft_GraphRag (black box); graph_rag (different design) | rs/graph_rag.py | Black box / diverges | No (OpenAI/Azure) | S1 |
| [Ch22](#ch22-rag-evaluation) Evaluation | evaluation/*.ipynb (5) | evaluation/evalute_rag.py | Partial (no rank metrics) | No (OpenAI judges) | P6, M1–M4, V4, D1–D4 |
| [App A](#appendix-a-decision-guide) Decision guide | — | — | n/a | n/a | M5, K1 |
| [App B](#appendix-b-glossary) Glossary | — | — | n/a | n/a | P3, P4, C2 |

Every chapter in the book follows the same template (the pattern is stated at Intro p.8/8; the section headings below were observed in the chapters themselves): Problem → Core Idea → How It Works (with an "Algorithm Sketch" box) → When to Use This → Key Takeaways. Prerequisites are stated on p.1 of each chapter (confirmed for all 22 chapters). Each section below therefore gives the sketch page, the main section pages, and then a step table.

### Intro

- **Book.**
  - Intro p.1/8–p.2/8: RAG idea and failure families.
  - Intro p.3/8: the book is said to derive from the repo, claiming a runnable notebook per technique.
  - Intro p.5/8–p.6/8: seven chapter groups.
  - Intro p.7/8–p.8/8: how to read.
- **Code.** None.
- **Divergences.**
  - The "runnable notebook per technique" claim is only partly true: see §5 and the fidelity column above.
  - Book-internal issues DV-B1 to DV-B3 are in §6.2.
- **Learner action.** Use the Intro p.2/8 stage map only as orientation. The curriculum order is set by [02](02_RAG_MASTER_LEARNING_PLAN.md), not by chapter numbers (BACKBONE principle 1).

### Ch1 Simple RAG

- **Book.**
  - Sketches: preparation p.7/14, query p.10/14.
  - Preparation steps: p.3/14–p.7/14.
  - Query steps: p.8/14–p.10/14.
  - Role of chunk size: p.10/14–p.11/14.
  - Limits: p.11/14–p.12/14.
  - Tradeoffs: p.12/14–p.13/14.

| # | Book step (paraphrase) | Book page | Notebook cells | Script lines | Status |
|---|---|---|---|---|---|
| 1 | Load the PDF page by page | p.4/14 | `simple_rag.ipynb cell 10` (PyPDFLoader) | `rs/simple_rag.py:L23-L42` → `helper_functions.py:L48-L76` | Implemented |
| 2 | Split into ~1000-char chunks, ~200 overlap | p.4/14 | `simple_rag.ipynb cells 10-11` (RecursiveCharacterTextSplitter, `length_function=len`) | `helper_functions.py:L66-L69` | Implemented. Recursive separators are not described in the book (DV-03) |
| 3 | Clean formatting artifacts | p.5/14 | `simple_rag.ipynb cell 10` → `helper_functions.py:L18-L31` | same helper | Partial: tabs only (DV-02) |
| 4 | Embed each chunk | p.5/14 | `simple_rag.ipynb cell 10` (EmbeddingProvider enum; `helper_functions.py:L338-L362`) | `helper_functions.py:L73` (hardcodes `OpenAIEmbeddings()`) | Implemented; model unpinned |
| 5 | Store vectors | p.6/14 | `simple_rag.ipynb cell 10` (`FAISS.from_documents`) | `helper_functions.py:L74` | Implemented; in memory only (DV-04) |
| 6–7 | Embed the question; search top-K (2–5) | p.8/14 | `simple_rag.ipynb cell 13` (k=2) | `rs/simple_rag.py:L44-L61` | Implemented; scores never shown |
| 8 | Return chunk texts | p.10/14 | `simple_rag.ipynb cell 15` → `helper_functions.py:L129-L149` | `rs/simple_rag.py:L55-L61` | Implemented |
| 9 | Pass question + chunks to the LLM and answer | p.9/14–p.10/14 | none. Cell 17 runs `evaluate_rag` instead | none | **Missing** (DV-01). Reading alternatives: `simple_rag_with_llamaindex.ipynb cell 23` (query engine) or `local_rag_huggingface_faiss.ipynb cell 24` (LCEL chain) |
| — | Choose chunk size empirically | p.10/14–p.11/14 | `choose_chunk_size.ipynb cells 6-12` | `rs/choose_chunk_size.py:L23-L123` | Diverges (DV-06) |

- **Divergences:** DV-01 to DV-06.
- **Build yourself (v0, C1–C6):**
  - generation with `[doc:page]` citations;
  - score display;
  - doc_id/page/char-offset metadata;
  - index persistence with a params hash;
  - a trace of every intermediate;
  - a fixed eval set (replacing `evaluate_rag`).
- **Outdated code to watch:**
  - Legacy `langchain.document_loaders` / `.text_splitter` / `.vectorstores` imports (`simple_rag.ipynb cell 5`).
  - `get_relevant_documents` (`helper_functions.py:L143`), which no longer exists in langchain-core 1.x per the local probe; use `.invoke`.
  - Colab-only key loading (cell 5).
  - Hardcoded `gpt-4-turbo` in `evaluation/evalute_rag.py:L73, L85, L91, L108`.
  - `rs/simple_rag.py:L8` assumes it is run from inside the scripts folder.

### Ch2 RAG for Structured Data

- **Book.**
  - Sketches: preparation p.6/11, query p.8/11.
  - Field serialization: p.8/11–p.9/11.
  - Large tables: p.9/11.
  - When to use: p.10/11–p.11/11.

| # | Book step | Book page | Notebook cells | Script | Status |
|---|---|---|---|---|---|
| 1 | Parse CSV into rows | p.4/11 | `simple_csv_rag.ipynb cell 10` (`CSVLoader.load_and_split`); `simple_csv_rag_with_llamaindex.ipynb cells 10-11` (PagedCSVReader) | — | Implemented |
| 2 | Serialize each row as "Field: value" | p.4/11, p.8/11 | implicit in the loaders (cell 10; the LlamaIndex saved sample in cell 11 shows "Column: value" lines) | — | Implemented implicitly; never shown in the LangChain version |
| 3–4 | Embed rows; store (no overlap) | p.5/11 | `simple_csv_rag.ipynb cells 12-14` (`IndexFlatL2` + `InMemoryDocstore`, `add_documents`) | — | Implemented |
| 5–8 | Embed question; nearest rows | p.8/11 | `simple_csv_rag.ipynb cell 16` (`as_retriever()`, default k=4) | — | Implemented |
| 9–10 | LLM answers from rows | p.8/11 | `simple_csv_rag.ipynb cells 16-18` (stuff chain; one Sheryl Baxter lookup) | — | Implemented for one query |
| — | Large tables (cost) | p.9/11 | none | — | Missing |

- **Divergences:** DV-07.
- **Build yourself (C7, elective):**
  - column selection;
  - exact filters for "list all" questions;
  - an embedding-cost estimate per row count.
- **Related repo-only notebook:** `json_rag.ipynb` (§4).
- **Outdated:**
  - `langchain.chains` helpers moved to langchain-classic (cell 16);
  - `gpt-3.5-turbo-0125` (cell 5).

### Ch3 Reliable RAG

- **Book.**
  - Sketches: grading p.5/14, hallucination check p.8/14, highlighting p.9/14.
  - Complete pipeline: p.9/14–p.10/14.
  - Choosing models: p.10/14–p.11/14.
  - "I don't know" preference: p.11/14.

| # | Book step | Book page | Notebook cells | Status |
|---|---|---|---|---|
| 1 | Retrieve ≥4 candidates | p.4/14 | `reliable_rag.ipynb cell 6` (500-token chunks, overlap 0, Chroma, k=4), cells 8-12 | Implemented |
| 2 | Grade each chunk yes/no; drop the "no" chunks | p.4/14–p.5/14 | cells 14 (GradeDocuments, lenient prompt), 16 (filter loop) | Implemented; grader accuracy unmeasured |
| 3 | Generate from the filtered chunks | p.5/14–p.6/14 | cell 18 | Diverges: prompt says "based upon your knowledge" (DV-09) |
| 4 | Check groundedness; flag or regenerate | p.6/14–p.8/14 | cell 20 | Partial: prints the score only, no regenerate (DV-10) |
| 5 | Extract verbatim supporting segments with ids/sources | p.8/14–p.9/14 | cells 22-23 | Partial: verbatim not checked (DV-11) |
| — | Use the strongest model for final generation | p.10/14–p.11/14 | cells 14, 18, 20, 22 | Diverges (DV-08) |

There is no runnable script.

- **Divergences:** DV-08 to DV-12.
- **Build yourself (V1–V3):**
  - a regenerate-or-abstain branch;
  - a substring/span check for cited segments;
  - grader precision/recall against M1 gold;
  - an empty-context fallback.
- **Outdated:**
  - Groq model ids `llama-3.1-8b-instant` / `mixtral-8x7b-32768` may be retired (cells 14, 18, 20, 22; UNVERIFIED against the current catalogue);
  - legacy imports (cells 6, 22);
  - deprecated Chroma wrapper (cell 6);
  - incomplete pip cell (cell 3).

### Ch4 Proposition Chunking

- **Book.**
  - Sketches: generation p.6/15, quality check p.9/15.
  - Comparison: p.10/15–p.11/15.
  - Strengths and weaknesses: p.11/15–p.12/15.

| # | Book step | Book page | Notebook cells | Status |
|---|---|---|---|---|
| 1 | Moderate initial chunks | p.4/15–p.5/15 | `proposition_chunking.ipynb cell 9` (200/50 tiktoken tokens, gpt2 encoding) | Implemented (size unit not stated in the book) |
| 2 | LLM decomposes each chunk into propositions | p.5/15–p.6/15 | cells 12-13 (GeneratePropositions, 1 few-shot example; `chunk_id` back-pointer) | Implemented |
| 3 | Grade each proposition on 4 criteria; keep if all ≥7 | p.7/15–p.9/15 | cells 15-16 | Implemented. Same model as the generator (DV-13); per-proposition calls (DV-14) |
| 4 | Embed and store propositions | p.9/15 | cell 18 (Ollama `nomic-embed-text`) | Implemented |
| 5 | Retrieve and answer | p.9/15–p.10/15 | cells 19-37 (retrieval printouts only) | Partial: no answer (DV-15) |
| — | Compare with standard chunks | p.10/15–p.11/15 | cells 22-24 (k=4 over 3 chunks returns the whole corpus), cell 38 (qualitative table) | Diverges (degenerate baseline) |

There is no runnable script.

- **Build yourself (I4):**
  - an answer step;
  - parent-chunk return via `chunk_id`;
  - near-duplicate proposition handling;
  - retrieval metrics.
- **Outdated:**
  - `langchain_core.pydantic_v1` (cell 12);
  - `langchain.text_splitter` (cell 9);
  - community `OllamaEmbeddings` (cell 9), and Ollama is not installed locally;
  - `llama-3.1-70b-versatile` (cells 12, 15) likely retired (UNVERIFIED).

### Ch5 Query Transformations

- **Book.**
  - Sketches: rewriting p.6/14, step-back p.8/14, decomposition p.10/14.
  - Choosing a strategy: p.10/14–p.11/14.
  - Composition: p.11/14.
  - Pipeline position: p.11/14–p.12/14.

| # | Book step | Book page | Notebook cells | Script lines | Status |
|---|---|---|---|---|---|
| 1 | Rewrite the query | p.4/14–p.6/14 | `query_transformations.ipynb cells 6, 8` | `rs/query_transformations.py:L14-L28` | Partial (string only) |
| 2 | Step-back query | p.6/14–p.8/14 | cells 10, 12 | `rs/query_transformations.py:L30-L44` | Partial |
| 3 | Decompose into 2–4 sub-queries | p.8/14–p.10/14 | cells 14, 16 | `rs/query_transformations.py:L46-L61` | Partial; parse bug (DV-17) |
| 4 | Search with transformed queries; merge; dedup | p.6/14, p.8/14, p.10/14 | none | none (`run()` L104-L124 only prints) | **Missing** (DV-16) |
| 5 | Generate with the original question | p.6/14, p.8/14, p.10/14 | none | none | **Missing** |
| — | Composition (decompose + rewrite; parallel step-back) | p.11/14 | none | none | Missing |

- **Build yourself (Q1):**
  - retrieval per transformed query;
  - merge by RRF (link to R1);
  - order-preserving dedup;
  - generation with the original question;
  - an intent-drift check.
- **Outdated:**
  - `langchain.prompts` (cell 4);
  - hardcoded `gpt-4o` (cells 6, 10, 14).

### Ch6 Hypothetical Document Embedding

- **Book.**
  - Sketch: p.7/14.
  - Why imperfect is fine: p.8/14–p.9/14.
  - Matching chunk size: p.9/14–p.10/14.
  - Relation to other pre-retrieval techniques: p.10/14–p.11/14.

| # | Book step | Book page | Notebook cells | Script lines | Status |
|---|---|---|---|---|---|
| 1–3 | LLM writes a hypothetical answer of about chunk length | p.5/14, p.7/14 | `HyDe_Hypothetical_Document_Embedding.ipynb cell 12` (asks for "exactly" 500 chars) | `rs/HyDe_Hypothetical_Document_Embedding.py:L34-L36` | Diverges slightly (DV-18) |
| 4–6 | Embed it; search top-K real chunks | p.5/14–p.6/14 | cell 12 (`similarity_search(hypothetical_doc, k=3)`), cells 14-18 | `rs/HyDe_Hypothetical_Document_Embedding.py:L38-L41` | Implemented |
| 7 | Discard the hypothetical document | p.6/14 | cell 12 returns it alongside the results | same | Diverges (harmless if never passed on) |
| 8 | Generate from real chunks + original question | p.6/14 | none | none | **Missing** |

- **Build yourself (Q2):**
  - a generation step;
  - a raw-query baseline;
  - an optional multi-hypothesis average (paper idea, C#32; external).
- **Outdated:**
  - install cell covers only dotenv (cell 5);
  - star imports run before `load_dotenv` (cell 7);
  - markdown says GPT-4, code uses `gpt-4o-mini` (cell 12).

### Ch7 Contextual Chunk Headers

- **Book.**
  - Sketch: p.8/11.
  - Richer headers: p.8/11.
  - The impact (0.1 → 0.9): p.8/11–p.9/11.

| # | Book step | Book page | Notebook cells | Status |
|---|---|---|---|---|
| 1 | Chunk with any strategy | p.8/11 | `contextual_chunk_headers.ipynb cell 9` (800/0 chars) | Implemented |
| 2 | Generate a document title | p.4/11 | cell 11 (`gpt-4o-mini`, 4000-token truncation) | Implemented |
| 3 | Prepend the header to each chunk | p.4/11–p.7/11 | cell 13 (only inside the rerank call) | Partial |
| 4 | Embed and store augmented chunks | p.7/11 | none (no vector index built) | **Missing** (DV-20) |
| 5 | Keep the header for reranking and generation | p.8/11 | cell 13 (rerank only) | Partial |
| — | Richer headers (summary, section path) | p.8/11 | none | Missing |
| — | Impact 0.1 → 0.9 | p.8/11–p.9/11 | cells 13-14 (Cohere rerank 0.1058 → 0.9221 on chunk 86); cell 15 (external KITE/FinanceBench numbers) | Diverges (DV-19) |

There is no runnable script.

- **Build yourself (I5):**
  - a real header index (embed header + chunk; display chunk without header);
  - a section-path header;
  - a measured comparison.
- **Outdated:**
  - `langchain.text_splitter` (cell 9);
  - `open()` without encoding, a Windows risk (cell 9);
  - Cohere v1 client and `rerank-english-v3.0` (cell 13);
  - stale output (cell 13).

### Ch8 Context Enrichment Window

- **Book.**
  - Sketch: p.6/11.
  - Steps: p.4/11–p.5/11.
  - Window size: p.7/11.
  - Relation to contextual headers: p.7/11–p.8/11.

| # | Book step | Book page | Notebook cells | Script lines | Status |
|---|---|---|---|---|---|
| 1 | Tag chunks with a sequential index | p.4/11 | `context_enrichment_window_around_chunk.ipynb cell 13` (raw char slicer; whole text in metadata) | `rs/context_enrichment_window_around_chunk.py:L17-L25` | Implemented |
| 2 | Normal top-K search | p.4/11 | cells 15-17 (400/200 chars, k=1) | `rs/context_enrichment_window_around_chunk.py:L110-L114` | Implemented |
| 3–4 | Window I−N … I+N; fetch by index | p.6/11 | cell 19 (fetch every vector, linear scan), cell 23 | `rs/context_enrichment_window_around_chunk.py:L29-L34`, `L38-L71` | Diverges in efficiency (DV-22) |
| 5–6 | Join while trimming overlap at each junction | p.5/11–p.6/11 | cell 23 (default overlap 20 must match the split) | `rs/context_enrichment_window_around_chunk.py:L38-L71` | Partial (fragile default) |
| — | Sentence-window variant | not in book | `context_enrichment_window_around_chunk_with_llamaindex.ipynb cells 14, 22` (window_size=3; MetadataReplacementPostProcessor) | none | Not in book (DV-21) |

- **Build yourself (X1):**
  - dict lookup keyed by (doc_id, index);
  - clamping at document edges;
  - merging of overlapping windows;
  - a token budget.
- **Outdated:**
  - `langchain.docstore.document` (cell 6);
  - `get_relevant_documents` with an extra `k` kwarg (cells 23-27).

### Ch9 Semantic Chunking

- **Book.**
  - Steps: p.4/14–p.8/14.
  - Sketch: p.7/14.
  - Comparison with fixed chunks: p.8/14–p.10/14.
  - Strategy spectrum: p.10/14–p.11/14.

| # | Book step | Book page | Notebook cells | Script lines | Status |
|---|---|---|---|---|---|
| 1–3 | Sentences → embed each → distances between consecutive ones | p.4/14–p.6/14 | `semantic_chunking.ipynb cell 12` (inside `SemanticChunker`; its buffer/neighbour behaviour is library knowledge, UNVERIFIED locally) | `rs/semantic_chunking.py:L24-L58` | Implemented as a black box |
| 4–5 | Pick a method (percentile / std / IQR) and set a threshold | p.6/14–p.7/14 | cell 12 (percentile 90 only) | `rs/semantic_chunking.py:L24-L48` (type and amount configurable; adds "gradient", L90) | Partial (DV-23) |
| 6–7 | Split at breakpoints; group sentences | p.7/14–p.8/14 | cells 12-14 (`create_documents`) | same | Implemented |
| 8 | Embed and store chunks | p.7/14–p.8/14 | cell 16 (k=2), cell 18 (one query) | `rs/semantic_chunking.py:L60-L78` | Implemented |

- **Build yourself (I3), from scratch in NumPy:**
  - sentence split;
  - consecutive cosine distances;
  - all three threshold rules;
  - min/max chunk caps;
  - a plot of the distance curve.
- **Outdated:**
  - `langchain_experimental` is not installed locally;
  - unpinned `OpenAIEmbeddings()`;
  - the script imports helpers before fixing `sys.path` (L6 vs L11);
  - `--chunk_size` / `--experiment` args are declared but never used (L95-L102).

### Ch10 Contextual Compression

- **Book.**
  - Sketch: p.8/13.
  - Full pipeline: p.8/13–p.9/13.
  - What is removed: p.9/13–p.10/13.
  - Compression vs grading: p.10/13–p.11/13.

| # | Book step | Book page | Notebook cells | Script lines | Status |
|---|---|---|---|---|---|
| 1–2 | Embed the query; retrieve top-K | p.5/13–p.6/13 | `contextual_compression.ipynb cells 10-12` (default k=4) | `rs/contextual_compression.py:L20-L72` | Implemented |
| 3–5 | Compress each chunk against the query; drop empty ones | p.6/13–p.7/13 | cell 12 (`LLMChainExtractor` in `ContextualCompressionRetriever`) | same | Implemented by library (drop behaviour UNVERIFIED) |
| 6–7 | Concatenate; generate | p.7/13 | cell 12 (RetrievalQA "stuff"), cell 14 | `rs/contextual_compression.py:L73-L89` | Implemented |
| — | Grade first, then compress | p.11/13 | none | none | **Missing** (DV-24) |

- **Build yourself (X2):**
  - before/after token counts;
  - a check that extracts are verbatim (substring);
  - grade-then-compress;
  - a non-LLM compressor baseline.
- **Outdated:**
  - `langchain.chains` / `langchain.retrievers` (cell 5; `rs/contextual_compression.py:L6-L8`), now in langchain-classic;
  - markdown says GPT-4, code uses `gpt-4o-mini` (cells 0 vs 12).

### Ch11 Document Augmentation

- **Book.**
  - Sketch: p.8/13.
  - Mirror of HyDE: p.9/13–p.10/13.
  - Number of questions: p.11/13.

| # | Book step | Book page | Notebook cells | Script lines | Status |
|---|---|---|---|---|---|
| 1 | Chunk the document | p.6/13 | `document_augmentation.ipynb cells 4, 6, 10` (4000-"token" docs and 128-"token" fragments; "tokens" are regex words) | `rs/document_augmentation.py:L86-L94` | Diverges (units) |
| 2–3 | LLM generates N questions per chunk | p.6/13 | cell 6 (`generate_questions`; DOCUMENT_LEVEL, 40 per document) | `rs/document_augmentation.py:L61-L73` | Implemented at document level only |
| 4 | Clean and dedup questions | p.6/13 | cell 6 (strip numbering, keep "?", `set()`) | `rs/document_augmentation.py:L52-L59` | Partial ("too vague" filter missing) |
| 5–6 | Store chunks + questions with a parent pointer | p.6/13–p.7/13 | cell 10 (`metadata['text']` = parent *document*) | `rs/document_augmentation.py:L101-L150` | Diverges (DV-25) |
| 7–9 | Match the query; fetch the parent; generate | p.7/13–p.8/13 | cells 13-17 | `rs/document_augmentation.py:L160-L187` | Implemented |

- **Sibling (repo-only):** `HyPE_Hypothetical_Prompt_Embeddings.ipynb` stores only question vectors that map to the chunk text (cells 9-11, dedup in cell 19). See §4.
- **Build yourself (I6):**
  - fragment-level generation;
  - dedup of parents in top-k;
  - a no-augmentation baseline.
- **Outdated:**
  - legacy imports (cell 4);
  - `generate_answer` returns an AIMessage, not text (cells 6, 17);
  - HyPE cell 11 SyntaxError (static reading; the script fixes it at L99).

### Ch12 Fusion Retrieval

- **Book.**
  - Sketch: p.10/14.
  - Two indexes: p.5/14–p.6/14.
  - Parallel query: p.6/14–p.7/14.
  - Normalization (min-max and mean ± 3 std): p.7/14–p.9/14.
  - Weighting (0.6/0.4 example): p.9/14.
  - Choosing weights: p.11/14–p.12/14.
  - Multi-query option: p.12/14.

| # | Book step | Book page | Notebook cells | Script lines | Status |
|---|---|---|---|---|---|
| 1–2 | Chunk; build the vector index | p.5/14, p.10/14 | `fusion_retrieval.ipynb cell 10` (1000/200) | `rs/fusion_retrieval.py:L20-L44` | Implemented |
| 3 | Build the BM25 index | p.5/14–p.6/14 | cells 14-15 (whitespace split, case-sensitive) | `rs/fusion_retrieval.py:L46-L58` | Implemented (naive tokenization) |
| 4–5 | Query both; top-K from each | p.6/14–p.7/14 | cell 17 scores **all** chunks (`similarity_search('')` with `k=ntotal`) | `rs/fusion_retrieval.py:L61-L86` | Diverges (DV-27) |
| 6 | Normalize to 0–1 | p.7/14–p.9/14 | cell 17 (1 − min-max of L2 distance; eps 1e-8); `fusion_retrieval_with_llamaindex.ipynb cell 19` (`dist_based_score`, mean ± 3σ) | `rs/fusion_retrieval.py:L80-L81` (no epsilon: NaN if all BM25 scores are equal) | Partial |
| 7 | Weighted sum | p.9/14 | cell 17/19 (alpha 0.5); llamaindex cell 19 (0.6/0.4) | `rs/fusion_retrieval.py:L83` | Diverges in defaults (DV-26) |
| 8 | Rank; pass the top results on | p.10/14 | cell 17 (`argsort` over misaligned arrays, static reading) | `rs/fusion_retrieval.py:L84-L86` | Diverges (bug) |
| — | Multi-query expansion | p.12/14 | llamaindex cell 19 (`num_queries=1`, i.e. switched off) | none | Not exercised |
| — | Rank-based fusion (RRF) | not in book | llamaindex cell 20 lists it as a mode | none | Not in book (DV-28) |

- **Build yourself (R1):**
  - align scores by chunk id;
  - union of per-retriever top-K, with explicit handling of missing scores;
  - RRF;
  - lowercase + punctuation tokenization;
  - a sanity test that would catch the misalignment.
- **Outdated:**
  - `langchain.docstore.document` (cell 5);
  - `llama_index.legacy` BM25Retriever (llamaindex cell 3);
  - embedding an empty string to list documents (cell 17).

### Ch13 Reranking

- **Book.**
  - Sketches: LLM reranking p.9/13, cross-encoder p.10/13.
  - Bi- vs cross-encoder: p.6/13–p.7/13.
  - Reorder and select: p.10/13–p.11/13.
  - vs Ch3 grading: p.12/13–p.13/13.

| # | Book step | Book page | Notebook cells | Script lines | Status |
|---|---|---|---|---|---|
| 1 | Retrieve K=10–30 candidates | p.5/13, p.9/13 | `reranking.ipynb cell 17` (k=15), cell 19 (k=30) | `rs/reranking.py:L56-L65` | Implemented |
| 2 | LLM scores each candidate 1–10 | p.7/13–p.9/13 | cell 15 (`RatingScore`, `gpt-4o`, sequential calls) | `rs/reranking.py:L26-L54` | Implemented (pointwise) |
| 3 | Sort; keep top N=3–5 | p.9/13 | cell 15 (top_n=3), cell 19 (num_docs=2) | same | Implemented |
| 4 | Cross-encoder: score (query, chunk) pairs in batch | p.9/13–p.10/13 | cell 27 (`CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')`) | `rs/reranking.py:L67-L84` | Implemented |
| 5 | Shortlist replaces the original results | p.10/13–p.11/13 | cells 19, 29 (RetrievalQA, k=10 → 5) | `rs/reranking.py:L110-L143` | Implemented |
| — | Toy "capital of France" example | p.1/13–p.2/13 | cell 23 (5 sentences; the book shows 4) | `rs/reranking.py:L87-L107` | Minor difference (DV-29) |
| — | Batch/listwise LLM reranking | not in book | `reranking_with_llamaindex.ipynb cells 16, 19` (LLMRerank), cell 23 (SentenceTransformerRerank) | none | Not in book (DV-29) |

- **Build yourself (R3):**
  - candidate-pool sweep;
  - truncation handling for long chunks;
  - latency per query;
  - retrieval metrics before and after reranking.
- **Outdated:**
  - RetrievalQA (cells 19, 29);
  - overriding `get_relevant_documents` (cells 19, 27);
  - pydantic v1-style `Config` (cells 19, 27; `rs/reranking.py:L59-L60, L73-L74`).

### Ch14 Hierarchical Indices

- **Book.**
  - Sketch: p.7/13.
  - Summaries as the first pass: p.8/13–p.9/13.
  - Role of metadata: p.9/13–p.10/13.

| # | Book step | Book page | Notebook cells | Script lines | Status |
|---|---|---|---|---|---|
| 1 | Summarize each logical section; attach metadata | p.4/13–p.5/13 | `hierarchical_indices.ipynb cell 11` (one summary per *page*; map_reduce; batches of 5 with backoff) | `rs/hierarchical_indices.py:L22-L68` | Implemented (page = section) |
| 2 | Chunk each section; tag chunks with the parent id | p.5/13–p.6/13 | cell 11 (1000/200; page metadata) | same | Implemented |
| 3 | Two vector stores | p.6/13 | cells 11, 13 (cached with `save_local`/`load_local`) | `rs/hierarchical_indices.py:L85-L107` | Implemented |
| 4–6 | Top-K summaries → section ids → filtered detail search, top-N | p.7/13 | cell 15 (k_summaries=3; k_chunks=5 *per page*, up to 15 chunks; post-filter lambda) | `rs/hierarchical_indices.py:L71-L82` | Diverges (DV-30) |
| 7 | Generate | p.7/13 | none | none | **Missing** |

- **Repo-only extension:** `raptor.ipynb` (§4).
- **Build yourself (R5):**
  - a fallback to flat search when routing is wrong;
  - a multi-document section key;
  - generation.
- **Outdated:**
  - `load_summarize_chain` legacy path (cell 6);
  - `retry_with_exponential_backoff` re-awaits a coroutine (`helper_functions.py:L294-L321`, static reading);
  - `is_string` branch crash (cell 11; `rs/hierarchical_indices.py:L34, L42`);
  - pickle deserialization (cell 13);
  - script imports helpers before fixing `sys.path` (L8 vs L10).

### Ch15 Dartboard Retrieval

- **Book.**
  - Sketch: p.7/12.
  - Oversampling: p.5/12.
  - First pick: p.6/12.
  - Iterative selection: p.6/12–p.7/12.
  - Smoothing parameter: p.8/12.

| # | Book step | Book page | Notebook cells | Status |
|---|---|---|---|---|
| 1 | Oversample N = K × factor | p.5/12 | `dartboard.ipynb cell 23` (num_results=5 × oversampling_factor=3) | Implemented |
| 2 | Query-to-candidate and pairwise distances | p.7/12 | cell 23 (1 − VVᵀ and 1 − qVᵀ on reconstructed FAISS vectors; assumes unit norm) | Implemented (normalization assumption unstated) |
| 3 | First pick = closest to the query | p.6/12–p.7/12 | cell 21 (`argmax` of query log-probabilities; dummy score 1.0) | Implemented |
| 4–6 | Diversity = max distance from any selected chunk; weighted sum; greedy | p.6/12–p.7/12 | cell 21 (element-wise max of log-probabilities, then log-sum-exp over the pool) | **Diverges** (DV-31) |
| 7 | Smoothing with σ ≈ 0.1 | p.8/12 | cell 19 (`lognorm` is a Gaussian log-density despite its name); cell 21 (SIGMA=0.1) | Implemented (naming misleads) |
| 8 | Return K results | p.7/12 | cell 23; cell 25 calls it with `k=3`, a kwarg the signature lacks | Diverges: TypeError as committed (DV-33, static reading) |

There is no runnable script. The demo corpus is the climate PDF duplicated ×5 (cell 9).

- **Build yourself (R4):**
  - plain MMR from scratch as the baseline;
  - a redundancy metric (mean pairwise cosine in the top-k);
  - a σ-scale study for the chosen embedding model.
- **Outdated:**
  - stale saved output in cell 25;
  - `input()` key prompt (cell 4);
  - install cell covers only numpy and dotenv (cell 2).

### Ch16 Multi-Modal RAG with Captioning

- **Book.**
  - Sketch: p.6/11.
  - Extraction: p.4/11–p.5/11.
  - Captioning: p.5/11–p.7/11.
  - Chunking both streams: p.7/11–p.8/11.
  - Retrieval: p.8/11–p.9/11.

| # | Book step | Book page | Notebook cells | Status |
|---|---|---|---|---|
| 1 | Split the PDF into text and images, tagged by page | p.4/11 | `multi_model_rag_with_captioning.ipynb cells 8-9` (PyMuPDF; images saved as `image_<page>_<index>`) | Implemented (raster images only) |
| 2 | Caption each image for retrieval | p.5/11–p.6/11 | cells 10-12 (`gemini-1.5-flash`) | Implemented |
| 3 | Collect captions with page metadata | p.6/11 | cells 12, 14 (page appears only in the file name) | Partial (DV-34) |
| 4 | Chunk and embed both streams into one store | p.7/11–p.8/11 | cells 14-15 (400/50 tiktoken tokens; Cohere embed; Chroma) | Implemented |
| 5 | Retrieve and answer | p.8/11–p.9/11 | cells 17-20 (k=1; uses `docs[0]` only; `command-r-plus`; saved answer 27.3) | Implemented |

There is no runnable script.

- **Repo-only alternative:** `multi_model_rag_with_colpali.ipynb` (§4).
- **Build yourself (S2, elective):**
  - table extraction;
  - caption → image back-links;
  - a text-only baseline proving that the retrieval, not the model's memory, produced the answer.
- **Outdated:** Gemini SDK and model id (cells 4, 10; current availability UNVERIFIED); missing installs (cell 3).

### Ch17 Retrieval with Feedback Loops

- **Book.**
  - Sketch (feedback-adjusted retrieval): p.7/11.
  - Collect feedback: p.4/11–p.5/11.
  - Adjust scores: p.5/11–p.7/11.
  - Enrich index: p.7/11–p.8/11.

| # | Book step | Book page | Notebook cells | Script lines | Status |
|---|---|---|---|---|---|
| 1 | Collect and store ratings (1–5) | p.4/11–p.5/11 | `retrieval_with_feedback_loop.ipynb cells 12-16` (JSON-lines store) | `rs/retrieval_with_feedback_loop.py:L31-L56` | Implemented |
| 2 | Retrieve candidates | p.7/11 | cell 10 (default k=4), cell 22 | `rs/retrieval_with_feedback_loop.py:L105-L124` | Implemented |
| 3 | LLM judges whether each feedback item applies to each doc | p.5/11–p.7/11 | cell 18 (compares to lowercase `'yes'` while the schema asks for Yes/No) | `rs/retrieval_with_feedback_loop.py:L58-L94` (L86) | Diverges: likely never matches (DV-35, static reading) |
| 4 | Multiply the score by avg/3 | p.6/11–p.7/11 | cell 18 | same | Implemented (unreachable if 3 never matches) |
| 5 | Re-rank and pass to the LLM | p.7/11 | cell 22 (`search_kwargs['docs']` is not used by the retriever) | L121-L122 | Diverges (DV-35) |
| 6 | Periodically add highly rated Q+A docs (≥4/≥4) alongside the index | p.7/11–p.8/11 | cell 20 (concatenates all Q+A into one string and rebuilds the whole index), cell 24 | `rs/retrieval_with_feedback_loop.py:L96-L101` | Diverges (DV-36) |

- **Build yourself (A4, elective):**
  - feedback keyed by query cluster;
  - a poisoning guard (verify before reinjecting);
  - before/after retrieval metrics.
- **Outdated:**
  - RetrievalQA (cell 5);
  - `qa_chain` keeps the old retriever after re-indexing (cell 24; `rs/retrieval_with_feedback_loop.py:L148`).

### Ch18 Adaptive Retrieval

- **Book.**
  - Sketches: factual p.6/12, overall p.9/12.
  - Strategies: p.5/12–p.9/12.

| # | Book step | Book page | Notebook cells | Script lines | Status |
|---|---|---|---|---|---|
| 1 | Classify the query into 4 types | p.4/12–p.5/12 | `adaptive_retrieval.ipynb cell 7` (free-string category) | `rs/adaptive_retrieval.py:L48-L60` | Implemented; no validation |
| 2 | Factual: rewrite → 2K → LLM 1–10 score → top K | p.5/12–p.6/12 | cell 11 | `rs/adaptive_retrieval.py:L74-L102` | Implemented |
| 3 | Analytical: sub-questions → pool → diverse subset | p.7/12–p.8/12 | cell 13 (LLM sees 50-char previews) | `rs/adaptive_retrieval.py:L104-L130` | Partial (DV-37) |
| 4 | Opinion: viewpoints → pool → broad subset | p.8/12 | cell 15 (`.split()` on a list) | `rs/adaptive_retrieval.py:L132-L159` (L158) | Diverges: crashes (static reading, DV-38) |
| 5 | Contextual: reformulate with user context | p.9/12 | cell 17 (callers never pass `user_context`, cell 19) | `rs/adaptive_retrieval.py:L161-L192` | Diverges (DV-37) |
| 6 | Route and generate | p.9/12–p.10/12 | cells 19 (exact dict key), 23 | `rs/adaptive_retrieval.py:L194-L221` | Implemented (KeyError on an unknown label) |

The demo corpus is a single sentence (cell 25).

- **Build yourself (A1):**
  - a label-validated router with a fallback route;
  - router accuracy on labelled queries;
  - a no-LLM router baseline (embedding/keyword).
- **Outdated:**
  - `langchain_core.pydantic_v1` (cell 5; `rs/adaptive_retrieval.py:L13`);
  - overriding `get_relevant_documents` (cell 21);
  - hardcoded `gpt-4o`.

### Ch19 Explainable Retrieval

- **Book.**
  - Sketch: p.5/10.
  - Explanation prompt craft: p.6/10–p.7/10.
  - Compared to source attribution: p.8/10.

| # | Book step | Book page | Notebook cells | Script lines | Status |
|---|---|---|---|---|---|
| 1–2 | Retrieve top-K | p.3/10–p.4/10 | `explainable_retrieval.ipynb cell 6` (k=5 over a 3-sentence corpus, cell 8) | `rs/explainable_retrieval.py:L17-L38` | Implemented (toy) |
| 3 | For each doc, ask the LLM why it is relevant | p.4/10–p.5/10 | cell 6 (`retrieve_and_explain`) | `rs/explainable_retrieval.py:L39-L50` | Implemented |
| 4 | Return (doc, explanation) pairs | p.5/10–p.6/10 | cell 10 | `rs/explainable_retrieval.py:L53-L58` | Implemented |
| — | Brief, specific explanations | p.6/10–p.7/10 | cell 6 (no brevity constraint; the prompt asks why the context is relevant, so it presupposes relevance) | same | Diverges (DV-39) |

- **Build yourself (V1):**
  - an explanation that may answer "not relevant";
  - a test showing that explanations do not replace citation verification.
- **Outdated:** `get_relevant_documents` (cell 6; `rs/explainable_retrieval.py:L40`).

### Ch20 Corrective RAG

- **Book.**
  - Sketch: p.6/11.
  - Thresholds: p.5/11–p.6/11. In the text dump the inequality symbols are lost; check the PDF.
  - Refinement: p.6/11–p.7/11.

| # | Book step | Book page | Notebook cells | Script lines | Status |
|---|---|---|---|---|---|
| 1 | Retrieve top-K | p.4/11 | `crag.ipynb cell 20` (k=3) | `rs/crag.py:L75-L77` | Implemented |
| 2 | Score each doc 0–1 | p.4/11 | cells 16, 20 | `rs/crag.py:L79-L91` | Implemented (uncalibrated) |
| 3 | Route on max score: >0.7 best doc; <0.3 web; else combine | p.4/11–p.6/11 | cell 22 | `rs/crag.py:L144-L184` | Implemented |
| 4 | Rewrite for the web, search, extract key points | p.6/11–p.7/11 | cells 14, 16, 18, 20 (DuckDuckGo; `parse_search_results` expects JSON) | `rs/crag.py:L93-L127` | Implemented with a likely parsing bug (DV-40, static reading) |
| 5 | Generate from the selected knowledge | p.7/11–p.8/11 | cell 20 (`generate_response` cites sources) | `rs/crag.py:L129-L142` | Implemented |

- **Build yourself (A2):**
  - threshold calibration on labelled data;
  - corpus-only mode for evaluation;
  - search-failure handling;
  - sanitising web text before prompting (D4).
- **Outdated:**
  - `pydantic_v1` (`rs/crag.py:L7`);
  - script imports helpers before fixing `sys.path` (L9 vs L12-L13).

### Ch21 Graph RAG

- **Book.**
  - Sketch (indexing): p.8/13.
  - Extraction: p.4/13–p.5/13.
  - Graph and communities (Leiden): p.5/13–p.7/13.
  - Summaries: p.7/13–p.8/13.
  - Local and global search: p.9/13–p.10/13.

| # | Book step | Book page | `Microsoft_GraphRag.ipynb` (matches the book's design) | Other repo designs | Status |
|---|---|---|---|---|---|
| 1 | Chunk documents | p.8/13 | inside the `graphrag` CLI (cell 14) | `graph_rag.ipynb cell 7` (1000/200); `light_rag.ipynb cell 10` (1200/150) | Black box / implemented |
| 2 | LLM extracts entities + relationships, with "what did you miss" passes | p.4/13–p.5/13 | inside the CLI | `light_rag.ipynb cells 12-16`; `graph_rag_local_attribution.ipynb cell 9`; `graph_rag.ipynb cell 9` extracts *concepts*, not relations | Black box / partial |
| 3–4 | Merge entities; build the graph | p.5/13–p.6/13 | inside the CLI | `light_rag.ipynb cells 16-18`; `graph_rag.ipynb cell 9` (nodes = chunks; edges where cosine > 0.8) | Diverges in `graph_rag` (DV-41) |
| 5 | Hierarchical community detection (Leiden) | p.6/13–p.7/13 | inside the CLI (overview markdown cell 1) | none | Black box only |
| 6–7 | Summarize communities; store | p.7/13–p.8/13 | inside the CLI | none | Black box only |
| 8 | Local search from query entities | p.9/13 | cells 17-19 (`graphrag.query --method local`) | `light_rag.ipynb cell 24`; `graph_rag_local_attribution.ipynb cells 15-19`; `graphrag_with_milvus_vectordb.ipynb cells 20-36`; `graph_rag.ipynb cell 12` (Dijkstra-like traversal that treats L2 distance as similarity, DV-42) | Several partial analogues |
| 9 | Global map-reduce over community summaries | p.9/13 | cells 17, 21 (`--method global`) | none | Black box only |

- **Build yourself (S1, elective, only if eval shows global/multi-hop failures):**
  - inspect the GraphRAG output artifacts;
  - a small entity-graph prototype;
  - a cost estimate (LLM calls per chunk × passes).
- **Outdated:**
  - pre-1.0 `python -m graphrag.index/query` CLI with an unpinned install (cells 5, 14, 17);
  - API key written into `settings.yaml` (cell 14);
  - `graph_rag` uses `langchain.retrievers` (`rs/graph_rag.py:L5-L6`) and processes documents twice (`rs/graph_rag.py:L733-L755` plus the main-block call).

### Ch22 RAG Evaluation

- **Book.**
  - Sketch (faithfulness): p.8/19.
  - Evaluation triad: p.2/19–p.4/19.
  - Retrieval metrics: p.4/19–p.7/19.
  - Generation metrics: p.7/19–p.9/19.
  - Judges: p.9/19–p.10/19.
  - Reference metrics: p.10/19.
  - Robustness: p.11/19–p.12/19.
  - Dataset: p.12/19–p.13/19.
  - Component vs end-to-end: p.13/19–p.14/19.
  - Latency and cost: p.14/19–p.15/19.
  - Production: p.15/19–p.16/19.
  - Safety: p.16/19–p.17/19.

| # | Book content | Book page | Repo location | Status |
|---|---|---|---|---|
| 1 | Context relevance (fraction of useful chunks) | p.4/19 | `evaluation/define_evaluation_metrics.ipynb cells 9-11` (NameError in cell 9, static reading); `evaluation/evaluation_deep_eval.ipynb cell 6` | Partial (LLM-judged, unranked) |
| 2 | P@K, R@K, MRR, MAP, NDCG | p.4/19–p.7/19 | none | **Missing** (DV-43) |
| 3 | Faithfulness by claim decomposition | p.7/19–p.8/19 | `define_evaluation_metrics.ipynb cells 6-8` (0/1, not claim-level); `evaluation_deep_eval.ipynb cell 4`; `evaluation/end-2-end_rag_evaluation.ipynb cell 19` (RAGAS) | Partial |
| 4 | Answer relevance | p.8/19–p.9/19 | `evaluation/evaluation_grouse.ipynb cells 13-23` | Partial |
| 5 | Completeness (weighted sub-questions) | p.9/19 | `end-2-end_rag_evaluation.ipynb cells 12-14` (0/1/2 judge); `evaluation/open-rag-eval-example.ipynb cells 9-10` (nuggets; equivalence UNVERIFIED) | Partial |
| 6 | LLM-as-judge, biases, mitigations | p.9/19–p.10/19 | `evaluation/evalute_rag.py:L95-L158`; `evaluation_grouse.ipynb cells 36, 39` (meta-evaluation) | Partial |
| 7 | Reference text metrics (BLEU/ROUGE/BERTScore) | p.10/19 | none | Missing |
| 8 | Noise-robustness sweep | p.11/19–p.12/19 | none | Missing |
| 9 | Evaluation dataset | p.12/19–p.13/19 | `data/q_a.json`; `evaluation/evalute_rag.py:L133-L138` (fresh LLM questions each run) | Diverges (DV-44) |
| 10 | Latency and cost | p.14/19–p.15/19 | timing in scripts only (see D2) | Partial |
| 11 | Production loop; safety | p.15/19–p.17/19 | none | Missing |

- **Build yourself (P6, M1–M4, D1–D4):** the whole retrieval-metric harness, the span-gold eval set, a judge calibration set, latency/cost logging and safety probes. Design is in [06](06_RAG_PROJECT_AND_EVALUATION_PLAN.md).
- **Outdated:**
  - hardcoded `gpt-4-turbo` (`evaluation/evalute_rag.py:L73, L85, L91, L108`);
  - deepeval metric objects built at import time (L71-L93);
  - `calculate_average_scores` is a stub (L160-L163);
  - `memorag.ipynb cells 45, 62` pass a kwarg that `evaluate_rag` does not accept.

### Appendix A Decision Guide

- **Book.**
  - How to use: App p.1/23.
  - Pipeline at a glance: p.1/23–p.3/23.
  - Symptom map (6 families): p.3/23–p.5/23.
  - Progressive enhancement layers: p.5/23–p.7/23 ("Layer 5", measurement last, p.7/23).
  - Stacks: p.7/23–p.9/23.
  - Quick-reference tables and decision tree: p.9/23–p.11/23.
  - Key takeaways (measure before and after every change): p.12/23.
- **Code.** None. The appendix never names a notebook.
- **Use in this curriculum:**
  - M5 failure buckets start from the symptom map.
  - K1 uses the stacks as hypotheses to test, not answers. Its Low/Medium/High ratings are unmeasured.
  - The measure-first contradiction is resolved in favour of measuring first (BACKBONE principle 2).
- **Divergences:** book-internal only (DV-B5 and DV-B7 to DV-B10 in §6.2).

### Appendix B Glossary

- **Book.** App p.13/23–p.22/23. Entries relevant here:
  - BM25 (p.14/23);
  - chunk overlap of about 200 chars (p.14/23);
  - cosine similarity (p.15/23);
  - MRR / NDCG and oversampling (p.19/23).
- **Code.** None.
- **Use.** A quick definitional check during spaced review ([05](05_LEARNING_AND_RETENTION_SYSTEM.md)), with two known errors:
  - The cosine entry says Ch1 explains cosine; it does not (DV-B4).
  - The oversampling entry gives 3–5×, while Ch18 uses 2K (DV-B6).

---

## 4. Repo-only notebooks

These notebooks have no book chapter. Their names never appear in the book text (grep over all book text files). They are either variants the book silently merged, or techniques it omits. Placement uses BACKBONE IDs. "Layer 2" means read-only code reading; the learner does not adopt the notebook's code.

| Notebook (all_rag_techniques/) | What it actually implements (static reading) | Nearest book unit | Curriculum placement | Runs with learner's setup? / caution |
|---|---|---|---|---|
| `HyPE_Hypothetical_Prompt_Embeddings.ipynb` (+ `rs/HyPE_Hypothetical_Prompt_Embeddings.py`) | Index-time question generation per chunk; only the question vectors are stored, each pointing to the chunk text (cells 9-11); dedup of results with `set()` (cell 19). Cell 0 cites an SSRN preprint whose gains are unverified | Ch11 (mirror of HyDE, Ch11 p.9/13–p.10/13) | I6 (with Ch11); compared against Q2 HyDE | No (OpenAI). Cell 11 SyntaxError (static reading); the script fixes it at L99 |
| `relevant_segment_extraction.ipynb` | Cohere-rerank every chunk, transform the scores, then a constrained max-sum search for contiguous segments (cells 7-21); zero overlap required | Ch8 (same problem: missing neighbouring context) | X1 (alternative to windows) | Cohere only, but expects the env var `CO_API_KEY` (the learner's key is named `COHERE_API_KEY`); `scipy`/`cohere` not in the pip cell. Constants (decay 30, penalty 0.2) untuned |
| `multi_faceted_filtering.ipynb` (+ `rs/multi_faceted_filtering.py`) | Four post-retrieval filters: metadata equality, score threshold, keyword, near-duplicate (cells 14-22); the notebook adds a GPT-4o answer (cell 24) | Ch14 metadata role (p.9/13–p.10/13) | R2 | The script needs no API key (local MiniLM + Chroma; no LLM). Packages are not installed yet |
| `raptor.ipynb` (+ `rs/raptor.py`) | GMM-clustered recursive summary tree; all levels in one FAISS store; compression retriever (cells 9-21) | Ch14 (two-level only) | R5 (S); optional v8 | No (OpenAI). Summaries indexed as AIMessage repr; broken parent links; the traversal function is never called (static reading). C#40 (external) |
| `self_rag.ipynb` (+ `rs/self_rag.py`) | Prompted retrieve-decision → relevance → per-doc generation → support → utility selection (cells 14-16) | Ch20 (sibling) | A3 (S) | No (OpenAI). Exact-string control flow. C#41 (external) |
| `Agentic_RAG.ipynb` | Contextual AI vendor platform: datastore, agent, parser, instructable reranker, grounded LM, LMUnit (cells 9-72) | none | A5 (S, last) | No (vendor key). Mechanism not inspectable; promotional framing |
| `light_rag.ipynb` (+ `rs/light_rag.py`) | From-scratch LightRAG: per-chunk entity/relation extraction, two FAISS indexes, low- and high-level keyword retrieval (cells 10-28) | Ch21 (cheaper alternative to communities) | S1 (S) | No (OpenAI/Azure). Incremental update described, not implemented |
| `graph_rag_local_attribution.ipynb` | Ollama-built entity graph with BFS multi-hop and `[N]` citations mapped to LLM-reported source sentences (cells 5-19) | Ch21 local search (p.9/13) | S1; citation ideas for V1 | No: Ollama is not installed, and the notebook then silently produces an empty graph (cell 5). Source sentences are never verified |
| `graphrag_with_milvus_vectordb.ipynb` | Hand-written triplets in 3 Milvus collections; adjacency-matrix subgraph expansion; LLM reranking of relations (cells 12-38) | Ch21 local search | S1 (S) | No (OpenAI + Zilliz cloud). One-query "superiority" claim |
| `memorag.ipynb` | LLM-extracted topic/detail "memory", clue and surrogate queries, comparison with simple RAG (cells 9-72) | none | S3 (S) | No (OpenAI). Data artifacts missing; `evaluate_rag` kwarg TypeError (cells 45, 62) |
| `json_rag.ipynb` | jRAG field flattening + all-MiniLM-L6-v2 + raw FAISS L2, retrieval only (cells 13-23) | Ch2 | C7 (S) | Embeddings local, no LLM. Live Nobel-prize API call (cell 8) |
| `local_rag_huggingface_faiss.ipynb` | bge-base local embeddings + FAISS + remote HF endpoint generation; page-tagged context; source attribution (cells 10-28) | Ch1 | C5/C6 reference reading (generation and refusal prompts) | Partly: embeddings local, generation needs an HF token. "Fully local" claim is false (cell 0); not in the README |
| `multi_model_rag_with_colpali.ipynb` | Page images indexed with ColPali via byaldi; Gemini answers from the top page image (cells 9-24) | Ch16 (alternative) | S2 (S) | No (HF + Gemini keys; GPU needed; fit in 6 GB VRAM is UNVERIFIED). Broken install cell 5 |
| `choose_chunk_size.ipynb` (+ `rs/choose_chunk_size.py`) | LlamaIndex sweep of 128/256-token chunks scored by GPT-4o faithfulness/relevancy and response time (cells 6-12) | Ch1 p.10/14–p.11/14 (folded in) | I1 (as the "what not to conclude" example) | No (OpenAI). Ceiling 1.00/1.00; stale output (cell 12) |
| `simple_rag_with_llamaindex.ipynb` | LlamaIndex baseline: 200/50-token SentenceSplitter, top_k=2, query engine *with* generation, deepeval on `q_a.json` (cells 4-23) | Ch1 (silently merged) | C6 (Layer 2 comparison) | No (OpenAI; llama-index not installed). The FAISS store is likely bypassed (cells 9, 16) |
| `simple_csv_rag_with_llamaindex.ipynb` | PagedCSVReader + query engine top_k=2 (cells 10-17) | Ch2 (merged) | C7 | No (OpenAI) |
| `context_enrichment_window_around_chunk_with_llamaindex.ipynb` | Sentence windows (±3 sentences) via SentenceWindowNodeParser + MetadataReplacementPostProcessor (cells 12-24) | Ch8 (merged, DV-21) | X1 | No (OpenAI). No saved outputs |
| `fusion_retrieval_with_llamaindex.ipynb` | QueryFusionRetriever, `dist_based_score`, weights 0.6/0.4, top-2 per retriever (cells 15-22) | Ch12 (merged; source of the book's numbers, DV-26) | R1 | No (OpenAI). The FAISS store is never used (cells 8, 17) |
| `reranking_with_llamaindex.ipynb` | LLMRerank and SentenceTransformerRerank postprocessors (cells 16-23) | Ch13 (merged) | R3 | No (OpenAI) |
| `evaluation/evaluation_grouse.ipynb`, `evaluation/open-rag-eval-example.ipynb`, `evaluation/end-2-end_rag_evaluation.ipynb` | Judge meta-evaluation (GroUSE), UMBRELA/nuggets/hallucination score/citation scores, judges vs human labels | Ch22 (topics absent from the book) | M3, V4 | No (OpenAI judges). Bugs listed in the Ch22 table |

`Microsoft_GraphRag.ipynb` is not listed: it is the design Ch21 describes, although the book never names it. `graph_rag.ipynb` is mapped under Ch21 as a divergent design.

---

## 5. Book content with no code

Each row is something the book describes that **no** notebook or script implements, or implements so partially that the learner must build it. "Built in" names the concept and project version ([06](06_RAG_PROJECT_AND_EVALUATION_PLAN.md)) where `ragkit` gets it.

| Book content | Book page | Closest repo code | Built in |
|---|---|---|---|
| Answer generation in the Simple RAG baseline | Ch1 p.9/14–p.10/14 | none in `simple_rag`; see `local_rag_huggingface_faiss.ipynb cell 24` | C5, v0 |
| Full artifact cleaning (whitespace, broken line endings) | Ch1 p.5/14 | `helper_functions.py:L18-L31` (tabs only) | C1, v0 |
| Embedding-cost reasoning for large tables | Ch2 p.9/11 | none | C7 (elective) |
| Regenerate/flag branch after a failed groundedness check | Ch3 p.7/14–p.8/14 | `reliable_rag.ipynb cell 20` prints only | V2, v5.0 |
| Verbatim guarantee for highlighted segments | Ch3 p.8/14 | none (no substring check) | V1, v5.0 |
| Answer step after proposition retrieval | Ch4 p.9/15–p.10/15 | none | I4, v1.4 |
| Retrieval, merging, dedup and generation for rewrite / step-back / decomposition | Ch5 p.6/14, p.8/14, p.10/14 | none (strings only) | Q1, v3.0 |
| Composition of strategies | Ch5 p.11/14 | none | Q1 (optional) |
| Final answer from HyDE-retrieved chunks | Ch6 p.6/14 | none | Q2, v3.1 |
| Embedding and storing header-augmented chunks; richer headers (summary, section path) | Ch7 p.7/11–p.8/11 | none (rerank demo only) | I5, v1.2 |
| Grade-then-compress pipeline | Ch10 p.11/13 | none | X2, v4.1 |
| Per-chunk (fragment-level) question generation, as the sketch describes; "too vague" question filter; 5–40 range | Ch11 p.6/13, p.11/13 | enum exists, only DOCUMENT_LEVEL with 40 is run (`document_augmentation.ipynb cell 4`) | I6 |
| Distribution-based normalization in the main (LangChain) implementation; multi-query expansion | Ch12 p.8/14, p.12/14 | LlamaIndex variant only, `num_queries=1` | R1, v2.0 |
| Single filtered detail search returning N total; generation | Ch14 p.7/13 | per-summary searches (cell 15) | R5 (S) |
| "Max distance from any selected" diversity rule | Ch15 p.6/12–p.7/12 | different rule in `dartboard.ipynb cell 21` | R4 (implement MMR instead; see DV-31) |
| Caption page metadata as a field; table/figure coverage | Ch16 p.4/11–p.6/11 | page only in the file name (cell 14) | S2 |
| Adding synthetic feedback docs alongside the index; a working re-ranking effect | Ch17 p.7/11 | full rebuild; adjustment likely dead (cells 18-22) | A4 |
| Contextual strategy with real user context; full-pool diversity review | Ch18 p.7/12, p.9/12 | unwired / 50–100-char previews | A1 |
| Brief, specific explanations | Ch19 p.6/10–p.7/10 | unconstrained prompt (cell 6) | V1 |
| Entity extraction with gleaning passes, Leiden communities, community summaries, global map-reduce | Ch21 p.4/13–p.9/13 | only inside the `graphrag` CLI | S1 (elective) |
| P@K, R@K, MRR, MAP, NDCG | Ch22 p.4/19–p.7/19 | none | P6, M2, v0.1 |
| Claim-level faithfulness | Ch22 p.7/19–p.8/19 | 0/1 whole-answer judges only | M3, v0.1 |
| Answer relevance via reverse-generated questions; weighted completeness | Ch22 p.8/19–p.9/19 | holistic judges only | M3 |
| Reference text metrics (BLEU/ROUGE/BERTScore) | Ch22 p.10/19 | none | M3 (optional) |
| Noise-robustness sweep (100% → 80% → 60% relevant) | Ch22 p.11/19–p.12/19 | none | M4/V4 experiment |
| Latency/cost tracking per component; production loop (shadow, A/B, monitoring) | Ch22 p.14/19–p.16/19 | wall-clock prints only | D1–D3, v6.0 |
| Safety evaluation incl. prompt injection | Ch22 p.16/19–p.17/19 | none | D4 |
| Decision guide, symptom map, stacks | App p.1/23–p.12/23 | none (by nature) | M5, K1 |

---

## 6. Divergence catalogue

### 6.1 Book vs code

Every row has both citations. "Static reading" means the defect was inferred from the code, not observed at runtime.

| ID | Ch | Book says (paraphrase, cite) | Code does (cite) | Consequence for the learner | Concept |
|---|---|---|---|---|---|
| DV-01 | 1 | The pipeline ends with the LLM answering from retrieved chunks (Ch1 p.9/14–p.10/14) | `simple_rag.ipynb` retrieves and prints only (cells 13-15), then runs `evaluate_rag` (cell 17); `rs/simple_rag.py:L44-L61` is retrieval-only | The "simple RAG" notebook never shows the G in RAG | C5, C6 |
| DV-02 | 1 | Cleaning removes tabs, extra whitespace and broken line endings (Ch1 p.5/14) | `helper_functions.py:L18-L31` replaces tab characters only | Parsing artifacts reach the embeddings unnoticed | C1 |
| DV-03 | 1 | Splitting described as cutting by character count with overlap (Ch1 p.4/14) | RecursiveCharacterTextSplitter tries paragraph → line → word separators before cutting (`simple_rag.ipynb cell 10`) | Learner cannot predict chunk boundaries | C2 |
| DV-04 | 1 | FAISS presented as a vector database (Ch1 p.6/14; glossary App p.16/23) | FAISS is a flat in-memory index; metadata lives in a separate docstore (`simple_csv_rag.ipynb cell 12`); default metric is L2 | Wrong mental model of persistence and metadata | P5, C3 |
| DV-05 | 1 | Evaluation not discussed in Ch1 | `simple_rag.ipynb cell 17` → `evaluation/evalute_rag.py:L95-L163`: LLM-generated questions, no ground truth, stubbed average | Looks like a benchmark but produces no number | M1, M2 |
| DV-06 | 1 | Chunk size in characters, ~1000/200 as a starting point (Ch1 p.10/14–p.11/14) | `choose_chunk_size.ipynb cells 6-12`: 128/256 tokens via LlamaIndex, overlap size//5, judged only by GPT-4o; saved output 1.00/1.00 (ceiling); stale warning in cell 12 | The only chunk-size experiment in the repo cannot discriminate | I1 |
| DV-07 | 2 | Region and inference queries over customer rows; one row per chunk (Ch2 p.1/11, p.5/11, p.7/11) | One lookup query only (`simple_csv_rag.ipynb cell 18`); default k=4 (cell 16) silently caps "list all" answers; `load_and_split` used (cell 10) | Completeness failures are invisible | C7 |
| DV-08 | 3 | Reserve the most capable model for final generation (Ch3 p.10/14–p.11/14) | Small `llama-3.1-8b-instant` generates and grades (cells 14, 18, 20); larger Mixtral only highlights (cell 22) | Model-allocation advice is untested | V2 |
| DV-09 | 3 | Generation is the same as simple RAG, just with cleaner input (Ch3 p.6/14) | Prompt allows answering "based upon your knowledge" (`reliable_rag.ipynb cell 18`) | Invites ungrounded answers inside a "reliable" pipeline | V2, P7 |
| DV-10 | 3 | Flag or regenerate when the answer is not grounded (Ch3 p.7/14–p.8/14) | `reliable_rag.ipynb cell 20` prints the binary score; no branch | "Reliable" is diagnostic only | V2, V3 |
| DV-11 | 3 | Highlighted segments are exact excerpts (Ch3 p.8/14) | LLM-returned segments are never string-matched to the source (cells 22-23) | Citations may be paraphrased or invented | V1 |
| DV-12 | 3 | Two to four extra LLM calls (prose), 2–3 (table) (Ch3 p.11/14) | One grading call per retrieved chunk (k=4, cells 6, 16) + groundedness + highlight = 6 calls | Cost understated; it scales with k | V2, D2 |
| DV-13 | 4 | A second language model grades the propositions (Ch4 p.7/15) | Same `llama-3.1-70b-versatile` generates and grades (cells 12, 15) | Self-grading bias | I4, V4 |
| DV-14 | 4 | One QC call per chunk (Ch4 p.13/15); this conflicts with the book's own per-proposition sketch (Ch4 p.9/15) | Grading loops over each proposition (cell 16) | Index-time cost scales with propositions, not chunks | I4 |
| DV-15 | 4 | Step 5 retrieves and answers (Ch4 p.9/15–p.10/15) | Retrieval printouts only (cells 19-37); baseline k=4 over 3 chunks returns the whole corpus (cells 22-24) | No answer quality and no fair comparison | I4 |
| DV-16 | 5 | Each strategy searches, merges/dedups and generates with the original query (Ch5 p.6/14, p.8/14, p.10/14) | Only transformed strings are produced (cells 6-16; `rs/query_transformations.py:L104-L124`) | Retrieval benefit untested | Q1 |
| DV-17 | 5 | Sub-queries as a clean list of 2–4 (Ch5 p.8/14–p.9/14) | The prompt carries a few-shot example built on the same demo query (cell 14); the parser keeps the echoed "Original query" line (cell 16 output) | Primed demo plus a parse bug | Q1 |
| DV-18 | 6 | Hypothetical doc of *about* chunk length; discarded after search; final answer generated (Ch6 p.5/14–p.7/14) | Prompt demands *exactly* 500 characters; `retrieve` returns the hypothetical doc; no generation (`HyDe_Hypothetical_Document_Embedding.ipynb cell 12`; `rs/HyDe_Hypothetical_Document_Embedding.py:L34-L41`) | Unrealistic length constraint; incomplete pipeline | Q2 |
| DV-19 | 7 | Relevance rises from about 0.1 to about 0.9 with a title header, framed as an embedding effect (Ch7 p.8/11–p.9/11) | Number is a Cohere **rerank** score on one hand-picked chunk (0.1058 → 0.9221, `contextual_chunk_headers.ipynb cells 13-14`); the book's "Acme Corp" is the notebook's Nike 10-K (cells 8-13) | A single reranker score is presented as a general embedding gain | I5 |
| DV-20 | 7 | Headers are embedded and stored; richer headers optional (Ch7 p.7/11–p.8/11) | No vector index is built; title only (cells 9-15) | Core mechanism never demonstrated | I5 |
| DV-21 | 8 | Expansion uses the chunk index ±N, with overlap trimming (Ch8 p.4/11–p.6/11) | LlamaIndex variant embeds single sentences and swaps in a ±3-sentence window (`context_enrichment_window_around_chunk_with_llamaindex.ipynb cells 14, 22`) | Two different techniques under one chapter | X1 |
| DV-22 | 8 | Neighbours fetched by fast index lookup (Ch8 p.9/11) | `get_chunk_by_index` pulls every vector via an empty-query search and scans linearly (cell 19; `rs/context_enrichment_window_around_chunk.py:L29-L34`); stitch default overlap 20 vs split overlap 200 (cells 15, 23) | Anti-pattern; text silently duplicated if the overlap is not passed | X1 |
| DV-23 | 9 | Three threshold methods; IQR = Q3 + 1.5·IQR (Ch9 p.6/14–p.7/14) | Library `SemanticChunker`, percentile 90 only (`semantic_chunking.ipynb cell 12`); library IQR formula UNVERIFIED; library never named in the book | Mechanism invisible; formula may not match | I3 |
| DV-24 | 10 | Optionally grade, then compress (Ch10 p.11/13) | Compression only (`contextual_compression.ipynb cell 12`); demo query "main topic" does not exercise extraction (cell 14) | Recommended combination untested | X2 |
| DV-25 | 11 | Generated questions point to their parent *chunk*; 5–40 questions per chunk (Ch11 p.6/13–p.8/13, p.11/13) | Parent is a 4000-word document window (`document_augmentation.ipynb cells 4, 10, 17`); fixed 40 per document; "tokens" are regex words | Much larger context than the book implies | I6 |
| DV-26 | 12 | Example weights 0.6/0.4; distribution-based normalization with mean ± 3 std (Ch12 p.8/14–p.9/14) | These come from `fusion_retrieval_with_llamaindex.ipynb cell 19`; the main LangChain notebook uses alpha 0.5 with min-max (`fusion_retrieval.ipynb cells 17, 19`) | Book numbers cannot be reproduced in the main notebook | R1 |
| DV-27 | 12 | Each retriever returns its top-K; fuse those (Ch12 p.6/14–p.7/14, p.10/14) | Scores *all* chunks; vector and BM25 arrays are in different document orders before addition (`fusion_retrieval.ipynb cell 17`; `rs/fusion_retrieval.py:L75-L86`; static reading); script lacks the epsilon (L80-L81) | Fused ranking likely wrong; NaN possible in the script | R1 |
| DV-28 | 12 | Fusion = normalize + weighted sum; RRF never mentioned (Ch12 whole chapter; grep finds no "reciprocal") | LlamaIndex notebook lists reciprocal-rank mode (cell 20) | Learner misses the standard rank-based method → C#33 (external) | R1 |
| DV-29 | 13 | Pointwise per-document LLM scoring; four-chunk France example (Ch13 p.1/13–p.2/13, p.7/13–p.9/13) | `LLMRerank` in the LlamaIndex notebook (cells 16, 19) scores candidates in batches (library default `choice_batch_size`; not set in the notebook, UNVERIFIED locally); toy example has 5 sentences (`reranking.ipynb cell 23`) | Pointwise vs listwise distinction lost | R3 |
| DV-30 | 14 | One filtered detail search returning N=3–5 chunks; then generate (Ch14 p.7/13) | One search per selected summary with k=5 → up to 15 chunks; FAISS post-filter lambda; no generation (`hierarchical_indices.ipynb cell 15`; `rs/hierarchical_indices.py:L71-L82`) | Context size and recall differ from the book | R5 |
| DV-31 | 15 | Diversity = maximum distance from any selected chunk (Ch15 p.6/12–p.7/12) | Element-wise max of log-probabilities (closeness), log-sum-exp over the pool: an information-gain objective (`dartboard.ipynb cell 21`) | Implementing the book's rule gives a different algorithm. It would also favour near-duplicates of a single selected chunk | R4 |
| DV-32 | 15 | Chapter never mentions MMR; App p.3/23 calls dartboard MMR | Notebook attributes it to arXiv 2407.12101 (cell 0) | Three labels for one technique | R4 |
| DV-33 | 15 | Returns K diverse chunks (Ch15 p.7/12) | Cell 25 calls `get_context_with_dartboard(..., k=3)`, but the signature has `num_results` (cell 23): TypeError (static reading); the saved output predates the code and still shows a duplicate; corpus duplicated ×5 (cell 9) | Notebook cannot reproduce its own claim | R4 |
| DV-34 | 16 | Captions stored with page metadata; tables and charts captioned (Ch16 p.4/11–p.6/11) | Only raster images extracted (cell 9); page only in the file name (cell 14); k=1 and `docs[0]` (cells 15, 20) | Tables and vector figures are missed; weak provenance | S2 |
| DV-35 | 17 | Applicable feedback rescales scores, and the re-ranked list feeds the LLM (Ch17 p.5/11–p.7/11) | Compares to lowercase `'yes'` (`retrieval_with_feedback_loop.ipynb cell 18`; `rs/retrieval_with_feedback_loop.py:L86`); adjusted list put in `search_kwargs['docs']`, which the retriever ignores (cell 22) | Adjustment is likely dead code (static reading) | A4 |
| DV-36 | 17 | Synthetic Q+A docs are *added* to the index periodically (Ch17 p.7/11) | All good Q+A joined into one string, appended to the PDF text, and the whole index rebuilt (cell 20; `rs/retrieval_with_feedback_loop.py:L96-L101`); `qa_chain` keeps the old retriever (cell 24) | Rebuild cost; enrichment never reaches the QA chain | A4 |
| DV-37 | 18 | Contextual strategy needs user context; analytical review sees the full pool (Ch18 p.7/12, p.9/12) | `user_context` never passed (cells 17, 19); selector sees 50/100-char previews (cells 13, 15) | Two of four routes do not behave as described | A1 |
| DV-38 | 18 | Opinion route selects diverse viewpoints (Ch18 p.8/12); classifier output assumed valid | `.split()` on a list of ints (cell 15) crashes; the script drops `.split()` but still calls `.isdigit()` on ints (`rs/adaptive_retrieval.py:L158`), also an AttributeError; unknown labels raise KeyError (cell 19); static reading | Route failures are unhandled | A1 |
| DV-39 | 19 | Explanations should be brief and specific; claim tracing belongs to source attribution (Ch19 p.6/10–p.8/10). App A instead says explainable retrieval traces each claim (App p.3/23, p.5/23) | Prompt has no brevity constraint and asks why the context is relevant, presupposing relevance (`explainable_retrieval.ipynb cell 6`) | Explanations are post-hoc rationalisations, not verification | V1 |
| DV-40 | 20 | CRAG checks retrieved documents before generating (Ch20 p.3/11–p.6/11). App A says it detects and repairs low-confidence answers (App p.3/23) | `parse_search_results` expects JSON from DuckDuckGo output (`crag.ipynb cell 18`; `rs/crag.py:L113-L127`), so sources are likely empty in web branches (static reading); high-confidence path keeps only the single best doc (cell 22) | Web-branch citations may be missing; recall loss on the high path | A2 |
| DV-41 | 21 | Entities and relationships form the graph; Leiden communities; community summaries; local and global search (Ch21 p.4/13–p.10/13) | `graph_rag.ipynb`: nodes are *chunks*, edges where cosine > 0.8 plus shared concepts (cell 9); priority traversal with LLM completeness checks (cell 12); no communities | The notebook named "graph_rag" does not implement the chapter | S1 |
| DV-42 | 21 | Graph traversal follows meaningful relations (Ch21 p.9/13) | `graph_rag.ipynb cell 12` / `rs/graph_rag.py:L415-L428` uses `1/score` from an L2 *distance* as priority; the only faithful notebook (`Microsoft_GraphRag.ipynb cells 14, 17`) shells out to a CLI | Traversal order inverted (static reading); the faithful version is a black box | S1 |
| DV-43 | 22 | Defines P@K, R@K, MRR, MAP, NDCG (Ch22 p.4/19–p.7/19) | Computed nowhere in notebooks or `.py` files (repo-wide source check) | Retrieval quality has never been measured in the repo | P6, M2 |
| DV-44 | 22 | Use golden datasets of validated examples and compare runs (Ch22 p.12/19–p.13/19) | `evaluation/evalute_rag.py:L133-L138` generates new questions each run and splits on newlines; `calculate_average_scores` is `pass` (L160-L163); `data/q_a.json` lacks evidence locations | Results not comparable across runs or techniques | M1, M4 |

### 6.2 Book-internal inconsistencies (no code involved)

These matter because the learner may memorise the wrong version. Decisions about them belong in [08](08_GAP_ANALYSIS_AND_DECISIONS.md).

| ID | Statement A (cite) | Conflicting statement B (cite) |
|---|---|---|
| DV-B1 | With RAG there is no hallucination or guesswork (Intro p.1/8) | RAG answers can still hallucinate (Ch3 p.1/14–p.2/14) |
| DV-B2 | Ch11 grouped under post-retrieval processing (Intro p.5/8) | Ch11 generates questions at indexing time (Ch11 p.6/13) |
| DV-B3 | Dartboard summarised as progressively tighter filters (Intro p.5/8) | Dartboard balances relevance and diversity (Ch15 p.1/12–p.2/12) |
| DV-B4 | Glossary says Chapter 1 explains cosine similarity (App p.15/23) | Ch1 never mentions cosine (text grep); first use is Ch12 p.8/14 |
| DV-B5 | Stacks diagram (App p.8/23) | Stacks text for Support and Tech Docs (App p.8/23–p.9/23) |
| DV-B6 | Oversampling typically 3–5× (App p.19/23) | Factual route retrieves 2K (Ch18 p.5/12–p.6/12) |
| DV-B7 | Decision-tree flowchart routing (App p.11/23) | Symptom map (App p.3/23–p.5/23); its Yes/No arrows are incoherent |
| DV-B8 | Indexing-time techniques add no per-query overhead (App p.12/23) | Quick-reference table rates Ch16 and Ch21 query cost Medium (App p.10/23) |
| DV-B9 | App A summaries: adaptive retrieval routes by complexity (App p.5/23); explainable retrieval traces each claim (App p.3/23); CRAG repairs answers (App p.3/23) | Ch18 routes by query type (Ch18 p.4/12); Ch19 p.8/10 sends claim tracing to attribution; Ch20 grades documents before generation (Ch20 p.3/11–p.6/11) |
| DV-B10 | Measurement added last, as Layer 5 (App p.7/23; Ch22 is the final chapter) | Measure before and after every change (App p.12/23). Resolved in favour of measuring first (BACKBONE principle 2) |
| DV-B11 | Proposition chunking needs LLM calls once per document (Ch10 p.13/13) | One LLM call per chunk (Ch8 p.9/11; Ch9 p.10/14) |
| DV-B12 | Context window shown as a chunking strategy in the spectrum (Ch9 p.11/14) | The window leaves chunking unchanged (Ch8 p.9/11; Ch9 p.10/14 says so itself, one page before the spectrum) |
| DV-B13 | "Twenty techniques" (Ch22 p.2/19) | Twenty-two (App p.1/23–p.2/23) |

**How to use this catalogue.**
1. When a lesson cites a book number or behaviour, check this table first.
2. If a DV row exists, the lesson must show both sides.
3. The learner then decides with their own measurement, never by trusting either source.

