# Independent review of the RAG learning system

**Reviewer:** Codex  
**Date:** 2026-10-08 (Asia/Calcutta)  
**Overall design score:** **84/100**  
**Implementation-readiness verdict:** **NOT READY**  
**Equivalent pasted-task verdict:** **REWORK REQUIRED**

The architecture is worth keeping. Evaluation precedes optimization; techniques target named failures; the learner implements mechanisms before using frameworks; and delayed recall, debugging, transfer and architecture defence are assessed separately. The sampled source references are real. The review did not find fabricated book pages or notebook cells in its citation sample; one claim about the exclusivity of a book mention is overbroad.

Do not expand this into more lessons or notebooks yet. Repair the readiness rule, the text/offset contract, evidence sufficiency, cache identity, evaluation version comparisons, judge calibration and prerequisite semantics first. These are bounded corrections, not a request to rebuild the curriculum. Missing project code and environment files are expected at this first stage and are not themselves defects in a design-only deliverable.

This is the single dated report requested by `CODEX_REVIEW_BRIEF.md`. It also includes the weighted scorecard and severity mapping requested in the pasted task; it does not create the alternate report filename from that older task. Learning documents, PDFs and upstream code were not edited.

## 1. Scope, method and limits

Reviewed the eight root learning documents, README, review brief, BACKBONE, and relevant preserved verification scripts/logs. The eight documents total **8,058 lines**. Source roots:

- Learning system: `C:\Yash\New-Work\RAG\rag_learning`
- Book: `C:\Users\Yash\Documents\BOOK\RAG_Made_Simple_The_Complete_Visual_Guide`
- Repository: `C:\Yash\New-Work\RAG\upstream\RAG_Techniques`

The repository HEAD was **009adba2be1bef49780ef73b6dd3c18fd24b035b**, and its working tree was clean. The book has 25 PDFs and 320 pages. Citations below use PDF pages, not printed pages; notebook cell indices are zero-based. Upstream paths are relative to the pinned repository, and document line numbers refer to the files reviewed on this date.

Independent checks included:

- Fifteen book-page checks across eleven PDF files and citations from multiple learning documents.
- Twenty repo citation checks across inventory, dependency map, mapping, evaluation plan, sample and gap analysis.
- Nine claimed upstream defects: six reproduced through isolated execution/compilation, three additionally confirmed by source reading.
- All ten Corpus D seeds: PDF hash, pages, offsets, quotes, answerability and sufficient-evidence review.
- Six of seven Python blocks in 07 executed successfully in memory; H.3's ten parameterized cases were called directly and passed. This was **not a fresh pytest invocation**.
- Independent brute force of the boundary formula and finite-document rates.
- Acyclicity/ancestor checks of 03's authoritative hard-edge table.
- A scan of Markdown in the workspace for normalized 16-word sequences from the book: no matches.
- Inspection of the cached MiniLM configuration and the original LlamaIndex source.

**Execution limits:** No provider API, paid call, package install, credential-value inspection, or model-weight download was performed. Whole upstream notebooks were not executed. Isolated reproductions establish specific defects, not end-to-end runnability. The original temporary lab environment exists but now fails imports because `typing_extensions` is missing. A retry of the preserved climate script with system Python timed out after 40 seconds. Its output does not establish a fresh result.

The working audit interpreter was Python 3.12.8 with NumPy 2.3.3 and PyMuPDF 1.26.7; these differ from 07's recorded temporary lab stack. Book checks used page text; this review does not certify every diagram, tradeoff table, citation or external reference. The quotation scan checks extractable text, not text embedded in images. Current Groq availability, quotas and account suitability remain unverified.

## 2. Scorecard

Scores assess the **design**, not an implementation that this stage deliberately does not contain.

| Category | Weight | Score | Evidence and deduction |
|---|---:|---:|---|
| Conceptual correctness and completeness | 20 | 18 | Strong coverage of IR, representation, context, grounding and operations. Deduct for conflating partial coverage with sufficient evidence and an overconfident mixed-topic embedding rubric. |
| Connections and prerequisite ordering | 15 | 12 | Early evaluation and late complex architectures are sound. Gate requirements and either/or dependencies disappear from the DAG; several hard edges encode project order rather than conceptual necessity. |
| Book/repository traceability and accuracy | 15 | 14 | Fourteen sampled book claims are supported; one overbroad source-scope claim needs amendment, and twenty repo locators resolve. Provenance limits and static/runtime distinctions are unusually clear. Some evidence still depends on a temporary environment; MMR and learning-science references need consolidation. |
| Implementation and code understanding | 15 | 13 | Mechanism → trace → implement → modify → debug is explicit. Exact H.3 cases pass; upstream failures reproduced. Deduct for inconsistent offset contracts and unsafe advice about caching by chunk ID alone. |
| Evaluation and experimental rigor | 15 | 10 | Good controls, closed-book control, paired comparisons and separate metric families. Deduct for evidence logic, tiny calibration strata, incomplete frozen-text schema and comparability/test-reuse ambiguity. |
| Active learning and retention | 10 | 9 | Attempt-first coaching, delayed checks, novel transfer, interleaving and evidence-based progression are strong. Deduct for conflicting correction/hint rules, sample fast-track criteria and excessive session load. |
| Project progression and maintainability | 10 | 8 | Common baseline, champion comparisons and traces are sound. Deduct for the circular readiness gate, module/coordinate inconsistency and mandatory-looking optional versions. |
| **Total** | **100** | **84** | Below the pasted task's suggested 85-point threshold, with a blocking readiness-rule defect. |

Severity mapping: **Blocker = P0**, **Major = P1**, **Minor = P2**, **Nit = P3**. A Blocker below concerns the usability of the current approval process; it does not mean the entire curriculum is fundamentally wrong.

## 3. Verified findings, ranked by severity

### B-01 — Blocker / P0: readiness requires artifacts that its own rule forbids building

**Location:** 08 Part 7, L596 and E-1–E-4; README status; 02 O2; 06 §10 L1166.

**Problem:** Every checkbox must pass before *any* lab notebook or full concept lesson is built. E-1–E-4 require a locked environment, an executed smoke test and a launched notebook front end. These are O2 outputs, and O2 is itself an environment lab. Evaluation requirements are explicitly needed before Phase 4, yet are placed under the same global prohibition.

**Evidence:** The current folder has no `pyproject.toml`, `uv.lock`, `ragkit`, evaluation dataset directory or Git repository, as expected for this stage. Requiring all later artifacts before permitting the work that produces them creates a circular gate.

**Why it matters:** The learner and coach cannot consistently follow the stated rules.

**Exact correction:** Replace the single global gate with three gates:

1. **Design approval:** source sample audit, corrected contracts, reviewer decisions and approved lesson format. Permits O1–O3 and foundational P/C implementation.
2. **O2/C6 exit:** locked environment and smoke tests before dependent labs; working v0 before measurement work.
3. **M1–M5 exit / optimization entry:** verified evaluation dataset, calibrated or human evaluation, reproducible harness and failure buckets before Phase 4 experiments.

Assign each existing Part 7 item to one gate. Do not require the learner to pre-build all runtime artifacts to obtain design approval.

### M-01 — Major / P1: the promised frozen-text contract is missing and coordinates disagree

**Location:** 06 §§2.3, 5.3, 6.1, 6.4 and 9.6; 07 H.3 and C2-A-05; 08 D-17/V-1.

**Problem:** D-17 requires a frozen hashed extracted-text snapshot. However, 06 contains neither `text_sha256` nor `extractor@version`. Its corpus example records PDF bytes and parser version, not the actual page text/cleaning snapshot. Its Chunk type uses page-relative offsets; 07's DocChunk type always uses joined-document offsets.

**Evidence:** 06 L164–166 specifies one page and offsets into that page. 07 L956–959 specifies document offsets and page ranges; L995 calls these the single coordinate system. 06 §5.3 proposes automatic offset re-resolution after parser changes, while its regression sketch only checks quote uniqueness. A quote can remain unique while layout order, cleaning or the full gold span changes.

**Why it matters:** Labels can silently join to the wrong coordinates; cross-page evidence cannot be handled by the current single-page Chunk type; parser upgrades can change what is being measured.

**Exact correction:** Define one versioned snapshot manifest with parser/version, extraction options, cleaning version, PDF hash, **per-page text hashes**, encoding/newline convention and document page-start offsets. Store the snapshot reference/hash with each dataset. Use a canonical Chunk with document offsets plus `page_segments[{page,char_start,char_end}]`, or provide an explicit, tested conversion to those segments. Score gold against the frozen snapshot. Parser/cleaning changes produce a new snapshot and revalidated dataset; quote search is a migration aid, not automatic authorization to preserve old labels.

**Acceptance:** Page-2 and cross-page fixtures score identically after correct coordinate conversion; a changed page hash stops scoring; an extraction change cannot silently reuse prior gold.

### M-02 — Major / P1: default coverage is not evidence sufficiency, and flat all/any is too weak

**Location:** 06 §§6.1, 6.4, 7.2–7.3; config L268; 03 §6.3.

**Problem:** At the default threshold 0.5, a span is declared retrieved when only half its characters arrive. Hit@k means *some* relevant evidence, but 03's diagnosis labels Hit@k=1 as successful gold-evidence retrieval. The optional flat `evidence_mode` cannot represent “fact A AND fact B, each with alternative sources.”

**Evidence:** Applying the documented 50% rule to D-005's two spans gives Recall=1 for retrieved text consisting of **“Coal is the most carbon”** and **“Natural gas is the least carbon-intensive fos”**. The first fact is incomplete. For two required facts, retrieving only one still gives Hit=1. Config simultaneously lists `mode: any_overlap` and `min_span_coverage: 0.5` without specifying their precedence.

**Why it matters:** A chunker can win by retrieving unusable fragments; failure attribution can blame generation even when a required fact never arrived.

**Exact correction:** Keep character coverage as a **continuous diagnostic**, clearly named. Add complete evidence-set recovery as the primary sufficiency metric: required fact groups are AND; alternatives within a fact group are OR. Require complete annotated minimal spans (with a stated tolerance for whitespace/normalization), or manually validated sufficient alternatives. Keep Hit/MRR as first-evidence diagnostics. Make the evidence logic required and versioned. Define a single relevance mode and explicit defaults.

**Acceptance:** The half-span counterexample fails complete-evidence recovery; a two-fact question with one fact retrieved fails; either sufficient source for one alternative group passes; combined fragments covering the full span pass.

### M-03 — Major / P1: two seed labels do not contain all facts they claim to support

**Location:** 06 §6.7 D-004 and D-007.

**Problem:** Quotes and offsets are correct, but minimum sufficient evidence is incomplete.

**Evidence:** D-004 allows either p.8 or p.23. Its p.23 span describes removal of CO2 but omits the heading that expands DAC to direct air capture. D-007's p.10 span begins with an unresolved “It”; its p.29 span ends before “on Climate Change (UNFCCC).” The bridge must be supplied from outside the annotated spans.

**Why it matters:** Correct offset matching does not make an evidence label semantically complete. Short chunks can be penalized for recovering real support or rewarded for fragments that require background knowledge.

**Exact correction:** Extend D-004's p.23 alternative to include the acronym expansion heading. Extend D-007's p.10 span to include the named treaty/antecedent and its p.29 span to include the full convention name/acronym. Recompute offsets and human-verify. Where needed, store a ≤25-word quote prefix while retaining the longer true span. Keep all seeds `llm-draft` until learner validation; independent AI checking does not make them human-verified.

**Acceptance:** A reader shown only each sufficient alternative, or all required fact groups, can answer the whole question and explain the bridge without outside knowledge.

### M-04 — Major / P1: chunk IDs are not safe embedding-cache keys by themselves

**Location:** 07 H.3 L987–994; 06 §2.3 L162 and cache/index contracts.

**Problem:** 07 says deterministic IDs allow embedding caches keyed by ID to remain valid. IDs contain document ID, config hash and sequence number, but no content/snapshot version.

**Executed evidence:** With `doc_id="doc1"`, fixed 40/10 and text `AAAA` versus `BBBB`, the exact H.3 code produced the same ID: `doc1:c5c8dfd3d707:00000`. Text changed; ID did not. 06's proposed ID formula similarly omits text identity.

**Why it matters:** An incremental update can reuse an embedding for different text. Existing happy-path determinism tests do not detect this.

**Exact correction:** Remove the statement that ID-only caches are valid. Embedding cache keys must include model/revision, preprocessing/query-document mode and a hash of the actual embedded text. Namespace artifact IDs by source snapshot/version, or include content identity. Keep the already-good content-keyed cache in 06 L264 and 07 I.2. State that config hash alone is not content addressing.

**Acceptance:** Same content/config is reproducible; same logical document/position with changed content cannot hit the old embedding cache.

### M-05 — Major / P1: dataset versioning and repeated test selection can manufacture gains

**Location:** 06 §§6.3, 6.6, 7.6, 9.3–9.4 and version-card adoption rules.

**Problem:** Additions create MINOR versions, but comparability is defined as sharing a MAJOR version. An expanded question set changes the denominator and category mix even when old labels are unchanged. The repeatedly reported frozen test split can also become a tuning set across the grid and later versions.

**Evidence:** L809 defines MINOR as additions; L811 permits comparison within a MAJOR version. L773 says to freeze before experimenting; §9.4 allows confirmation on test, while §7.6 reports repeated champion/candidate results. Threshold cross-validation “over the full set” is suggested without reserving an outer evaluation set.

**Why it matters:** Reported differences can reflect different questions or adaptive reuse of test outcomes.

**Exact correction:** Require identical **dataset hash, qid set, labels, split and scorer version** for paired comparisons. After *any* item addition, rerun baseline/champion/candidate on the same expanded version, or explicitly compare only the unchanged qid intersection. Group paraphrase variants with their base item in splitting/bootstrap. Select grid candidates on dev; confirm on a locked test once per selection round. Treat repeatedly inspected test items as regression data and reserve a fresh final set/H for the architecture defence. If using cross-validation for thresholds, evaluate with an outer holdout or nested folds.

**Acceptance:** The runner rejects paired arrays from different qid sets; shuffled qid order is aligned by ID; base and paraphrase cannot cross splits; candidate selection is documented without test-driven retuning.

### M-06 — Major / P1: judge calibration is a pilot, not a reliable certification protocol

**Location:** 06 §8.4–8.5; 08 D-10; 02 Gate 3→4.

**Problem:** Thirty items per metric can be a useful pilot but may include almost no failures. The protocol asks v0 outputs alone to provide stratified correct/partial/wrong and faithful/unfaithful labels. Abstentions are included even though faithfulness/citation metrics exclude them. Failure-class recall ≥0.8 may therefore be undefined or based on very few cases. Label flip rate is also not directly a minimum detectable effect for every metric.

**Evidence:** With ten failure examples, catching eight yields the requested 0.8 recall but a wide Wilson 95% interval, approximately 0.49–0.94. Six perfectly handled unanswerables still have a two-sided exact 95% lower success bound of only about 0.54. The 30/70 split leaves roughly two dev unanswerables at the six-item minimum.

**Why it matters:** The system can pass a point threshold despite an unreliable judge or unsupported abstention policy.

**Exact correction:** Treat the first 30 as pilot calibration. Define the labeling unit for each metric (claim, citation/sentence, answer); count positives and failures separately; exclude abstentions from inapplicable support metrics. If natural v0 outputs lack failures, use explicitly labeled challenge outputs with fabricated claims, swapped citations and contradictions, and retain natural outputs for evaluation. Reserve untouched validation examples, report confusion matrices and intervals, and human-score while uncertainty is too large. Separate repeated-judge variance from paired metric-effect uncertainty. Expand unanswerable dev/test cases before threshold claims; keep 40+6 as a learning minimum only.

**Acceptance:** No pass on undefined failure recall; denominators/intervals accompany every threshold; rubric tuning and validation labels are disjoint.

### M-07 — Major / P1: an acyclic DAG is not enough; required gates and alternatives are lost

**Location:** 03 §2 introduction and §2.1 L394, L417–421; 02 I-CMP, A4, A5, S1–S3 and K1.

**Problem:** The hard-edge table is acyclic, but “A or B” is represented as two optional soft edges, permitting neither. Gate conditions are omitted. A learner following the table alone can unlock S2 after M2 without M3/M4/M5, although 02 requires Gate 3→4. A5 has no mandatory A1-or-A2 condition; S3 has no mandatory S1-or-R5 condition.

**Evidence:** The computed S2 ancestor set contains M1/M2 but no M3, M4 or M5. A5 ancestors include neither A1 nor A2; S3 ancestors include neither S1 nor R5. K1 lacks the full Gate 9→10 contract, including D3's regression check. I-CMP marks mechanism exposure to I2–I5 as soft, although 02 names that exposure as required.

**Why it matters:** The “authoritative” table cannot safely drive lesson unlocking or the progress script.

**Exact correction:** Add explicit `requires_all`, `requires_any_groups`, `requires_gate` and `requires_exposure` fields. Soft edges should mean truly optional advice. Keep conceptual prerequisites separate from chosen project-version order. Generate the graph/table from one registry and validate semantic agreement with 02. Either make minimal regression competence essential for the stated gate or remove that gate dependency; do not silently require a U experiment.

**Acceptance:** Neither OR group passes with zero members; S2 cannot bypass measurement readiness; K1 can skip A/S but must satisfy the actual core gate; no new cycles.

## 4. Minor findings and editorial nits

| ID / severity | File and location | Verified problem / evidence | Why it matters and exact correction |
|---|---|---|---|
| m-01 / Minor P2 | 07 PK-5 L94–95; D.7; B.3 L198 | PK-5 treats a mixed-topic embedding as necessarily between topics with lower cosine, while D.7 correctly labels linear mixing a toy. “Citation can be no finer than the retrieved unit” is also too absolute. | Grade the answer “may dilute relevance; measure it” as correct. Real contextual encoders do not obey the toy geometry universally. A retrieved passage can support a finer excerpt; citation resolution depends on the output/provenance contract. |
| m-02 / Minor P2 | 07 header L21; 05 §2; 02 §8 | C2's listed parts total **350 minutes**, before I1's extra 3–5 hours. The standard concept session is 90–120 minutes. | Split C2 into short core sessions; make library internals and the full grid a later extension. Do not impose this length on every future lesson. |
| m-03 / Minor P2 | 07 Part A L142; 05 CR-16 and §7.3; 02 §5 | The sample offers fast-track based on six recall responses plus confidence 3; the governing rule requires cold Recall/Application/Transfer evidence. | Confidence must not determine eligibility. Refer to the three-item rule and delayed check; a recall diagnostic may suggest which test to offer. |
| m-04 / Minor P2 | 05 CR-04, CR-06, hint-ladder Solution row | CR-06 requires immediate correction with the correct statement after an incorrect answer, but CR-04 and the ladder postpone full solutions; the Solution row is stricter than CR-04. | Distinguish grading/remediation from guided problem solving. During an active puzzle, identify the error and give the next allowed hint; reveal the full correction when the agreed stopping condition is met. Use one stopping rule. |
| m-05 / Minor P2 | 06 §3.2; 07 D.6, I.3 and verification log | Token/chunk measurements come from PyPDFLoader text, while v0 uses PyMuPDF and a framework-free recursive chunker. 07 correctly lists PyMuPDF counts as unverified. | Keep the existing numbers labeled upstream-parity measurements. Recompute chunk counts/token tails from the actual v0 extraction/splitter at C6/M2; do not use 97/182 as certified v0 measurements. |
| m-06 / Minor P2 | 06 v4.0/v4.1; 03 §6.2–6.4 | Candidate metrics can stay unchanged while window expansion, dedup, budgeting or compression changes evidence actually sent to the generator. 03 names final-context evidence checks only as a proposal. | Make stage-specific evidence coverage mandatory: candidate pool, final ranked top-k, and final prompt context. Preserve provenance for compressed text. Diagnose missing evidence at assembly before blaming generation. |
| m-07 / Minor P2 | 02 core-path schedule; 06 non-goals/v7; 08 D-23 | “No advanced content on the critical path” coexists with a core schedule containing v7 and wording that picks exactly one controller. D-23/gates also allow none. | Explicitly permit v6 → K1 when residual failures do not justify a controller. Make A1/A2/S1/R5/S2/S3 elective experiments. Minimal security/regression competence can remain core without forcing every advanced implementation. |
| m-08 / Minor P2 | 07 verification log; LAB_FACTS §0 | Re-run instructions point into Claude's temporary scratchpad. That interpreter now fails for missing typing_extensions; a working permanent verification environment is absent. | Retain existing scripts/outputs, add a minimal durable verification dependency group/lock and commands rooted in the workspace at O2. Mark old outputs as historical. Do not imply that preserving scripts preserves a runnable environment. |
| n-01 / Nit P3 | 07 D.2/D.3 L263, L306 | The count rule says one chunk for L≤S but H.1 returns [] for empty input; “storage linearly” conflicts with S/(S−O). | State L=0 → 0 and 0<L≤S → 1. Describe overlap storage growth as nonlinear/hyperbolic at fixed S. |
| n-02 / Nit P3 | 01 §3.4; BACKBONE §0; 04 X rows | The repo-count NOTE says BACKBONE still has old counts after D-30 records its fix; Phase-7 learning-order numbers still list X2 before X3. | Mark the count note resolved. Change the display order to X1/X3 → X2 across all overview/matrix rows. |

Additional implementation requirements, rather than demonstrated failures: define zero-denominator behavior for empty answers/citations and nDCG with no relevant indexed chunk; validate qid alignment and bootstrap array shapes; preserve decimal signs/units in short-answer normalization; include formatting overhead and the **generator tokenizer** in actual prompt-budget checks. Keep the budget helper explicitly a ranked-prefix policy: it stops at the first over-budget chunk rather than searching later candidates.


## 5. Source verification results

### 5.1 Book citation audit

**OK** means the inspected page supports the stated source claim and its denominator is correct. It does not endorse the book's recommendation as an empirical fact. Ranges were sampled at the indicated page; uninspected adjacent pages are not implicitly certified.

| ID | Citation taken from | Book page checked | Result | Direct evidence, paraphrased |
|---|---|---|---|---|
| B1 | 01 §2.5; 07 G.1 | Ch1 p.4/14 | OK | Presents the 1000-character/200-overlap default and page-level extraction. |
| B2 | 04 §2.6 V1/R-1 | Ch3 p.8/14 | OK | Describes tracing answer claims to exact supporting source excerpts and flagging/regenerating ungrounded answers. |
| B3 | 01 §2.3, Ch4 Core range | Ch4 p.3/15 | OK | Defines atomic, self-contained propositions with resolved names and qualifiers. |
| B4 | 03 §2.2, Q1 fusion dependency | Ch5 p.8/14 | OK | Step-back searches original and broader queries; decomposition gathers and deduplicates multiple searches. |
| B5 | 07 D.3/G.1 | Ch8 p.1/11 | OK | Explicitly treats overlap as an incomplete boundary fix. |
| B6 | 03 §4.3; 04 DV-26 | Ch12 p.8/14 | OK | Describes mean±3σ normalization, min–max normalization and incompatible score scales. |
| B7 | 03 §2.2 R5/R2 edge | Ch14 p.9/13 | OK | Uses summary/detail metadata to restrict second-stage retrieval by page. |
| B8 | 02 V1 NOTE; 08 Part 2 B8 | Ch19 p.8/10 | OK | Separates explanation of retrieval from attribution of generated claims. |
| B9 | 01 §2.3; 02 S1 | Ch21 p.6/13 | OK | Entity/relation graph, Leiden community detection and hierarchical communities. |
| B10 | 06 §7.3 | Ch22 p.4/19 | OK | Precision@k example is 3 relevant of 5 = 0.6. |
| B11 | 06 §7.3; 04 M2 | Ch22 p.6/19 | OK | Verbal definitions of MRR, MAP and graded discounted gain. The curriculum's explicit formulas are additions. |
| B12 | 02 evaluation-size NOTE; 08 B18 | Ch22 p.13/19 | OK | Recommends 200–500 validated examples and distinguishes component from end-to-end evaluation. Sample size alone does not guarantee significance. |
| B13 | 08 B15; 03 §2.2 | App p.7/23 | OK | Places measurement in the final operational layer. |
| B14 | 07 G.1; 02 §1.1 | App p.12/23 | OK | Recommends measurement around each change, supporting the curriculum's earlier evaluation order. |
| B15 | 04 R-4 NOTE, cross-checked against 03 §4.4 | Ch19 p.4/10 | **WRONG for the exclusivity claim** | Ch19 also names “maximum marginal relevance.” R-4's assertion that the term appears only in two Appendix locations is too narrow. It is still true that the book supplies no adequate algorithm explanation. |

All 25 file totals were read directly. An additional regex audit found **452 explicit ChN page-denominator occurrences and zero denominator mismatches**; this is a denominator check, not 452 content checks. The Markdown/book normalized 16-word scan found no matches.

### 5.2 Repo citation audit

Each checked file came from the clean clone at the pinned commit. These checks validate locations and code mechanisms, not whole-notebook execution.

| ID | Learning-document locator | Pinned source checked | Result | Evidence |
|---|---|---|---|---|
| R1 | 01 §3.7; 07 G.2 | helper_functions.py:L48–L76 | OK | Per-page loader, recursive character splitter, tab replacement, OpenAI embeddings and FAISS construction. |
| R2 | 01 §3.7; 08 RB3 | helper_functions.py:L294–L321 | OK | Retry loop awaits the same coroutine object again. |
| R3 | 04 DV-44; 06 v0.1 | evaluation/evalute_rag.py:L133–L138 | OK | Fresh generic climate questions are generated and split on newlines. |
| R4 | 01 §3.8; 08 RB4 | evaluation/evalute_rag.py:L160–L163 | OK | Aggregate function body is a stub. |
| R5 | 07 G.3 | simple_rag.ipynb cell 10 | OK | Defines the local encode_pdf implementation and character splitter. |
| R6 | 06 §3.1; 07 G.3 | simple_rag.ipynb cell 13 | OK | Uses retrieval k=2, unlike the curriculum's v0 k=4. |
| R7 | 03 §4.3; 08 RB1 | fusion_retrieval.ipynb cell 17 | OK | Empty-query doc order, BM25 corpus order and query-distance order are combined positionally. |
| R8 | 07 G.4; 08 RB15 | choose_chunk_size.ipynb cell 8 | OK | Registers the custom prompt under your_prompt_key. |
| R9 | 07 D.5/G.4 | choose_chunk_size.ipynb cell 10 | OK | Sets size and size//5 overlap, retrieves top five and reports answer-level judgments. |
| R10 | 07 G.4 | choose_chunk_size.ipynb cell 12 | OK | Loops over [128,256]. Saved output is historical evidence, not a fresh audit run. |
| R11 | 07 G.4 | all_rag_techniques_runnable_scripts/choose_chunk_size.py:L48 | OK | Constructs SentenceSplitter with size only; no overlap argument. |
| R12 | 07 G.4 | same script:L107 | OK | Uses the same placeholder prompt key. |
| R13 | 04 DV-33; 08 RB7 | dartboard.ipynb cell 23 | OK | Signature accepts num_results, not k. |
| R14 | 04 DV-33; 08 RB7 | dartboard.ipynb cell 25 | OK | Calls that function with k=3. |
| R15 | 03 structured-output NOTE; 08 RB8 | adaptive_retrieval.ipynb cell 15 | OK | Calls split() on structured-output indices. |
| R16 | 01 notebook inventory; 08 RB6 | HyPE_Hypothetical_Prompt_Embeddings.ipynb cell 11 | OK | Missing comma after index constructor prevents parsing. |
| R17 | 02 S1; 04 DV-41 | graph_rag.ipynb cell 9 | OK | Graph nodes are chunks; extracted entities/concepts are attributes, not entity nodes with community reports. |
| R18 | 04 DV-42; 08 RB2 | graph_rag.ipynb cell 12 | OK | Reads similarity_search_with_score and assigns priority=1/score to a min-heap. |
| R19 | 03 §2.2; 04 R5 | hierarchical_indices.ipynb cell 15 | OK | Searches detail chunks separately for each selected summary using a page metadata filter. |
| R20 | 03 post-retrieval family; 06 §3.2 | reranking.ipynb cell 27 | OK | ms-marco MiniLM cross-encoder scores query/document pairs, sorts them and truncates the initial candidate pool. |

Counts independently confirmed: **41 technique notebooks + 5 evaluation notebooks**, and no requirements.txt/pyproject.toml/setup.py/environment.yml in the repo root.

### 5.3 Upstream defect confirmation

| Claimed defect | Verdict | Reading versus running | Independent evidence |
|---|---|---|---|
| Fusion score/document misalignment | Confirmed | **Executed exact cell function** with a fake store/BM25 | With alpha=1 and query ordering C,B,A, the function returns A,B,C because it returns empty-query document positions. No real embedding/provider was needed. |
| Retry reuses a coroutine | Confirmed | **Executed AST-extracted exact helper** | Synthetic first-call RateLimitError plus no-op backoff produces RuntimeError: cannot reuse already awaited coroutine. |
| No aggregate from evalute_rag | Confirmed | **Executed AST-extracted function** | calculate_average_scores([{"score":5}]) returns None. No module-level judge objects were imported. |
| Dartboard wrong keyword | Confirmed | **Executed exact function definition/call** | TypeError: unexpected keyword argument 'k'. The body does not need to reach FAISS to establish this. |
| HyPE syntax error | Confirmed | **Parsed exact cell with ast.parse** | SyntaxError at cell-source line 32, missing comma after the index constructor. |
| Opinion list.split error | Confirmed | **Executed failing expression** | With [0,1] as structured indices, split() raises AttributeError. This is a statement-level reproduction, not a full routed pipeline run. |
| choose_chunk_size.py size 128/default overlap | Confirmed | **Source reading; fresh library run blocked** | Script L48 omits overlap; original LlamaIndex source defines default overlap 200 and rejects overlap>size at constructor L83–87. Saved author run agrees. This audit did not freshly execute the constructor successfully. |
| your_prompt_key no-op | Confirmed | **Source reading; fresh library run blocked** | FaithfulnessEvaluator._update_prompts L152–157 recognizes only eval_template/refine_template. The author's positive-control log is preserved but is not this review's fresh run. |
| Graph traversal distance inversion | Confirmed under the inspected FAISS defaults | **Source reading** | Installed FAISS wrapper defaults to EUCLIDEAN_DISTANCE and IndexFlatL2; inverse distance in a min-heap favors farther seeds and divides by zero for exact distance 0. Full graph/LLM traversal not run. |

Do not broaden these results to all 21 listed bugs. Feedback-loop, DuckDuckGo, RAPTOR, and other version-dependent claims remain static hypotheses unless separately reproduced.

### 5.4 Foundational, intermediate and advanced deep checks

- **Foundational C2:** exact chunker blocks, provenance, full/partial-span behavior, page-coordinate mismatch and integer boundary math were checked. The mechanism is largely correct; contracts and scope qualifiers need repair.
- **Intermediate R1/R3:** fusion was checked at document-identity level rather than by notebook title; the alpha=1 counterexample proves a wrong result even with only one scoring source. Reranking cell 27 correctly exposes candidate-pool recall limits and query/document pair scoring.
- **Advanced S1:** Ch21's entity graph/Leiden/community-summary mechanism differs materially from graph_rag's chunk graph with shared-concept attributes and query-time traversal. The curriculum correctly warns against treating the names as interchangeable. The L2 priority defect was independently inspected.

## 6. Evaluation design and all ten seeds

### 6.1 Seed audit

Corpus D independently matched **33 pages**, **206,372 bytes**, SHA-256:

`1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669`

PyMuPDF 1.26.7 reproduced every listed offset and normalized quote. Evidence quotes have at most 19 whitespace-delimited words. Matching quote locations and semantic sufficiency are separate checks.

| Seed | Page/offset and answer check | Verdict |
|---|---|---|
| D-001 | p.3 [1089,1203); the stated temperature rise and unit conversion occur there. | Accept as draft; exact numeric label fits. |
| D-002 | p.10 [438,537); adoption year occurs there. | Accept as draft. |
| D-003 | p.23 [2117,2202); reviews/updates of NDCs support the answer. | Accept as draft; reference resolution still matters for very small chunks. |
| D-004 | p.8 [1920,2007) is sufficient. p.23 [1463,1566) lacks the acronym expansion heading. | **Amend** the p.23 alternative, then re-anchor; see M-03. |
| D-005 | p.2 [0,45) and [746,836) support the two-part contrast. | Accept as draft; require both facts, not half-span success. |
| D-006 | p.8 [364,484) and [508,615) support land, evaporation and cooling benefits. | Accept as draft. The mismatch category is partial, since question and evidence still share solar-panel wording; measure lexical overlap rather than assuming it. |
| D-007 | p.10 [211,339) and p.29 [963,1078) match but omit the antecedent/full bridge identity. | **Amend** both spans; see M-03. |
| D-008 | p.24 [468,564) names the targeted gases. | Accept as draft. |
| D-009 | IPCC appears only on p.1; no establishment year is supplied. No 1988 occurrence. | Accept as corpus-relative unanswerable draft. |
| D-010 | No aviation, percentage sign or percent occurrence across the extracted PDF; surrounding transport discussion supplies no share. | Accept as corpus-relative unanswerable draft. |

These remain drafts. A scientifically familiar answer from a model's memory does not make D-009/D-010 answerable **from this corpus**.

### 6.2 Overall evaluation judgment

**Span-level gold is sound in principle** and better than chunk IDs for re-chunking experiments. It needs immutable text identity, explicit coordinate conversion, sufficient evidence sets and alternate valid sources. Use the source PDF alongside extracted text when judging whether the parser dropped a table/column; otherwise the benchmark can silently exclude parsing failures by defining all gold only from surviving text.

**40+6 is adequate for a learning gate and coarse diagnostics**, not small-effect selection, per-category comparisons or reliable refusal calibration. The plan already acknowledges limited power; keep that acknowledgement. A 60–100 target improves coverage without guaranteeing power. Plan counts per targeted failure and report discordant paired outcomes. Grow unanswerables deliberately, especially plausible-but-absent questions.

**Core metric formulas are mostly correct.** The nDCG toy gives about 0.651 binary and 0.640 graded; the RR, precision, token-F1 and abstention examples are consistent. “Context precision” uses normalization by relevant items actually retrieved and is a custom rank-precision score; do not call it ordinary AP/MAP with a corpus-relevance denominator. Span Recall is a custom metric, not classical relevant-document Recall. The documented redundancy caveat for chunk nDCG is correct.

**Retrieval and answer quality are well separated.** Preserve the closed-book control and correctness-versus-faithfulness distinction. Fix Hit versus full-evidence interpretation and measure assembly coverage separately. Report answer coverage/false abstention alongside conditional faithfulness: otherwise a system can appear more faithful by answering fewer questions.

**Judge calibration is directionally right but currently too optimistic.** Different-family judging is a useful bias mitigation, not a substitute for human checks, and a free hosted tier is not a durable offline path. Permit human evaluation for essential labs if no suitable judge exists. Treat κ/recall thresholds as provisional operational preferences with intervals, not proof of truth.

## 7. Sample lesson assessment and re-execution

**Assessment:** good material bank and a strong mechanism/debugging exemplar; not approved unchanged as the mandatory size and structure of every lesson.

Keep the initial diagnostic, concrete PPP page-boundary example, integer derivation, clearly labeled dilution toy, blank-file fixed-window exercise, source critique, controlled experiment and novel transfer. Keep the distinction between code execution and mastery.

Cut repeated explanations of overlap, units and provenance; reduce the library-default memorization in flashcards; move exhaustive library internals and the full I1 grid to a reference/experiment section. Add strict versus partial evidence examples, content-change cache tests, coordinate-conversion tests, and a parser/snapshot mismatch exercise.

| Exact 07 block | Audit outcome |
|---|---|
| D.7, L412, dilution toy | Executed: cosines 1.000, 0.707, 0.447, 0.316, 0.243; competitor wins from n=2. This validates the toy, not a universal encoder law. |
| H.1, L684, minimal chunkers | Executed in an in-memory module; fixed-window count/containment and edge checks passed. |
| H.2, L871, PyPDFLoader trace | Fresh parity re-run blocked: original labenv import failure; system-interpreter script attempt timed out. No fresh 97-chunk/overlap result claimed. |
| H.3, L924, reusable design | Executed exactly with in-memory ragkit._core; also exposes the changed-content/same-ID defect. |
| H.3 tests, L1001 | Four name/scope combinations, three ordinary cases and three invalid-overlap cases: **10 passed** when called directly. |
| I.2, L1110, budget helper | Executed: toy a/b/c/d uses 520 of 640 tokens; one 700-token chunk gives empty output. |
| L.3, L1437, deliberately buggy windows | Executed on the safe 23-character example: four windows including redundant 'vw'. The infinite-loop input was not executed. |

### Boundary-probability mathematics

The derivation is correct for **integer character offsets**, fixed windows, 1≤F≤S and a uniform interior start residue:

`stride = S−O`  
`P(contained) = min(1,(S−F+1)/(S−O))`  
`guarantee iff F≤O+1`

Independent results at S=1000, F=500:

| O | Interior probability | Whole L=20,000 probability |
|---:|---:|---:|
| 0 | 0.501000 | 0.5138198041 |
| 200 | 0.626250 | 0.6320188708 |
| 400 | 0.835000 | 0.8375467925 |

At O=200: F=200/201 gives 1; F=202 gives 0.99875; F=250 gives 0.93875. These match the lesson. Independent count checks over four additional size/overlap settings and positive lengths below 20S had zero mismatches.

Do not transfer the exact guarantee to recursive splitters. For continuous offsets the +1 does not apply. At fixed S, the storage factor is nonlinear in O. The statement that cross-page scope “changes nothing elsewhere” should be a measured hypothesis with a tolerance: rechunking the whole document can move boundaries and rankings away from the page cut too.


## 8. Curriculum order, missing connections and complexity

**Evaluation in Phase 3:** accept. P6 already establishes metrics, C6 supplies a system to evaluate, and M1–M5 then measure it before optimization. Do not require a full judge platform before the first retrieval improvement: human generation labels plus deterministic retrieval metrics provide an essential fallback. Reduce setup burden through staged gates, not by moving measurement to the end.

**Query work after retrieval:** a reasonable default, not a universal dependency. Hybrid retrieval and reranking are useful controls before paying for query LLM calls. RRF is relevant to merging decomposition results. A simple single-query rewrite does not conceptually require a reranker; distinguish that from the preferred experiment order. Permit a failure-driven Q1 branch after measurement/basic retrieval, while comparing with the cheaper hybrid/reranking alternatives.

**Graph/agentic work late:** accept. The learner's prior framework exposure is a reason to assess mechanics and measurement, not to skip them. Keep S1/R5, multimodal, MemoRAG, proposition/HyPE indexing, Self-RAG, feedback and hosted agentic systems elective. A one-hop factoid miss should not trigger a graph build. A5 needs bounded iterations, stop reasons, tool-error traces and a baseline, not merely a hosted SDK call.

All 56 cards have named failure fields; there is no unnamed technique in the inspected card set. However, a named *possible* failure is not evidence that it occurred in this learner's baseline. Require M5 trace IDs and counts before an optional experiment. Synthetic fault fixtures may teach mechanisms without being presented as proof that a production intervention is needed.

Add or clarify these connections inside existing IDs:

- **O2/P5:** zero vectors, dimensions, dtype, normalization, stable tie-breaking and k>index size.
- **C1/M1:** PDF-view versus extracted-text quality check, cleaning maps, Unicode/newline conventions and snapshot identity.
- **M1/M2:** sufficient evidence groups, alternative valid sources, ambiguous-question interpretation and corpus-relative answerability.
- **M3/V1:** source-excerpt existence versus claim support. Exact substring checking cannot prove semantic entailment; NLI/judges can also err.
- **M3/A1–A3:** typed enums, schema validation, bounded retry and explicit invalid-output behavior.
- **X3:** evaluate post-assembly evidence, not only top-k candidates; account for citation headers/tokenization.
- **D1/D2/D3:** manifest/code/scorer identity and content-keyed caching; temperature zero is not a complete determinism guarantee.
- **D4/A2:** prompt injection, privacy and retrieval scope before admitting web material; live-web output is a separate benchmark/corpus from frozen PDF retrieval.
- **Q1 optional:** conversation-history condensation, entity retention and ambiguity/clarification tests if multi-turn behavior is actually chosen.

Keep the existing out-of-scope treatment of retriever fine-tuning and long-context comparisons, but make the no-retrieval control a small C5/K1 comparison where the corpus fits. Do not make every provider/framework variant a mandatory exercise.

Production coverage is sufficient for a personal learning project once minimal fail-closed loading, trace redaction and regression checks are concrete. Full multi-tenancy, distributed ANN, serving infrastructure and sophisticated observability platforms are reasonable exclusions.

## 9. Verdict on every REVIEWER NOTE

There are **22 substantive NOTE blocks** in 01–08. References to those notes in 03's introduction, 04's matrix, 06's summary, 07's summary and 08's decision table do not introduce additional proposals. 06 L4 is a convention describing how notes are marked; accept that convention, subject to the actual corrections below.

| # | Note locator | Verdict | Resolution |
|---|---|---|---|
| N1 | 01 L181, repo counts | **Accept** | 41+5 independently confirmed. BACKBONE already reflects the correction; mark this note resolved rather than saying it still contains the old totals. |
| N2 | 01 L333, global torch/embeddings | **Accept** | Global package metadata contains torch/sentence-transformers; keep a fresh locked project. Package presence is not proof of successful model/device execution. |
| N3 | 02 L801, V1 versus Ch19 | **Accept** | Ch3 p.8 is the primary attribution anchor; Ch19 explains retrieval. Teach excerpt existence, attribution and semantic support as distinct checks. |
| N4 | 02 L1077, evaluation size | **Amend** | Keep 40+6 as learning minimum; grow targeted strata and report power/intervals. Bootstrap reporting does not itself make most effects detectable. Exact dataset identity is required after growth. |
| N5 | 02 L1162, conversational RAG ID | **Accept** | No new essential ID. Add an optional Q1 history/ambiguity probe; formal multi-turn outcomes only if the project adopts that feature. |
| N6 | 03 L438, Phase-7 order | **Accept** | X1/X3 → X2, with basic budgeting already introduced in C5. Update all display/matrix orders. |
| N7 | 03 L440, resolved R4/A5 mismatches | **Amend** | R3-before-R4 is acceptable as project order. A5 still requires an explicit A1-or-A2 group; two optional edges are not that condition. Resolve semantics before automation. |
| N8 | 03 L442, structured outputs | **Accept** | Explicit outcome in M3, inherited by V2/A1–A3. Add invalid enum/parse fixtures, one bounded retry and a defined safe failure path. |
| N9 | 04 L199 R-1, V1 book anchor | **Accept** | Same resolution as N3/D-28. Book attribution prompts are not a ready-made verifier implementation. |
| N10 | 04 L201 R-2, I-CMP/X3 fragments | **Amend** | Clearly label curriculum synthesis. Experiments provide evidence about implementations; primary IR/context literature also supports mechanisms. Lack of a standalone book chapter is not a problem. |
| N11 | 04 L203 R-3, M5 reference gap | **Accept** | Add Barnett et al.'s verified failure-points paper below; use its buckets as a starting point and keep corpus-specific trace diagnoses. |
| N12 | 04 L205 R-4, MMR source | **Amend** | Add Carbonell/Goldstein and the distinct Relevant Information Gain source. Ch19 p.4 also mentions the term using “maximum”; correct the “only Appendix” claim. No adequate algorithm exposition was established in the book. |
| N13 | 05 L21, learning-science references | **Accept** | Add retrieval-practice and spacing references below before O3 is expanded. Keep exact ladder/multiplier values labeled preferences, not research-derived constants. |
| N14 | 05 L566, resolved fast-track mismatch | **Amend** | 05 now defers to 02 correctly, but 07 L142 still uses recall/confidence eligibility. Align the exemplar with cold R/A/T and delayed evidence. |
| N15 | 05 L643, due_reviews script location | **Accept** | progress/due_reviews.py is adequate for a future small utility. Do not introduce a new tools folder solely for one script. |
| N16 | 06 L118, module additions | **Accept** | query.py/control.py can be added when needed; grounding may start in generate.py. Avoid creating unused scaffolding before a version needs it. |
| N17 | 06 L738, optional schema fields | **Amend** | Keep typed fields. Evidence logic, split policy, dataset/snapshot identity must be required for scored data; flat all/any needs fact groups. Aliases/tags remain optional. Do not encode machine-required fields inside free-text notes. |
| N18 | 06 L852, AI-drafted seeds | **Accept** | llm-draft is the correct current label. Exclude from scoring until human verification; this report does not satisfy that human step. |
| N19 | 07 L398, bge length resolution | **Accept** | The recorded 512 config limit is an appropriate sourced claim; actual truncation and corpus-T token lengths remain separately unverified. Recompute using actual v0 artifacts. |
| N20 | 07 L1076, experiment artifacts | **Accept** | summary.md with a preregistration section matches 05/06. Preserve raw outputs/configs beside it. |
| N21 | 08 L498 D-02, study/corpus overlap | **Amend** | Closed-book control is valuable. Non-RAG PDFs are a useful diversity preference, not a guarantee that a pretrained model has not seen them. Select useful corpus-specific questions and test grounding; learner chooses files. |
| N22 | 08 L503 D-09, minimum and target size | **Amend** | Accept the pilot minimum and 60–100 target, but expand unanswerables/targeted failures and preserve exact-version comparisons. More items do not automatically establish small-effect power. |

07's final summary also restates the overlap overclaim: **accept that critique**, within the fixed-window scope demonstrated above. This is a restatement of D.3/G.1, not a twenty-third substantive NOTE block.

## 10. Reviewer-owned decisions in 08 Part 4

All eleven rows naming Reviewer, including shared ownership and already-resolved rows, receive a decision here. **Decision date: 2026-10-08. Owner: Codex for reviewer scope only.** These are review resolutions; Claude still needs to apply the specified edits. Learner preferences, file choices, spending, service selection and licence acknowledgment are not silently decided.

| Decision | Verdict | Recorded reviewer decision |
|---|---|---|
| D-01, corpus structure | **Accept** | D for parity/smoke, T for main experiments, H for untouched transfer; exclude the book from experimental gold. File selection remains learner-owned. |
| D-08, framework policy | **Accept** | Framework-free core plus optional isolated comparison dependencies. Upstream read-only; adapt copies only when execution adds learning value. |
| D-17, evidence anchoring | **Amend** | Adopt an immutable extracted-text snapshot with required hashes/options and explicit page/document conversion, as M-01. Do not approve automatic quote-only migration after parser changes. |
| D-21, conversational concept ID | **Accept** | No new essential ID now; optional Q1 history/ambiguity outcome when chosen, not merely an untracked diagnostic mention. |
| D-22, structured output home | **Accept** | M3 is the primary home; schema/enum validation and invalid-output behavior are explicit acceptance criteria inherited by graders/controllers. |
| D-25, additional modules | **Accept** | query.py and control.py are allowed version-driven additions; grounding.py is optional when complexity warrants it. |
| D-26, due-reviews script | **Accept** | progress/due_reviews.py, future standard-library utility with the documented dry-run/validation behavior. |
| D-27, Phase-7 ordering | **Accept** | X1/X3 → X2 in BACKBONE, cards, matrix and schedule. |
| D-28, V1 source | **Accept** | Ch3 p.8–9 primary for attribution; Ch19 secondary as explanation/attribution comparison. Cite verification mechanisms separately. |
| D-29, missing references | **Accept** | Add verified external references listed below to Source C before O3/M5 expansion. Also close the separately raised MMR source gap. |
| D-30, counts | **Accept / already applied** | Confirm 41 technique +5 evaluation notebooks and retain the corrected BACKBONE counts. Update stale note wording. |

Non-reviewer choices remain open. In particular, this report does not establish a working Groq model, valid keys, selected T/H files, notebook front end, signed-off licence choice or an installed project environment.

### Verified external references for the source gaps

These are primary sources inspected through their publisher/author/arXiv records; they are **external to the local book and repo**.

- **M5:** Barnett et al. (2024), [Seven Failure Points When Engineering a Retrieval Augmented Generation System](https://arxiv.org/html/2401.05856v1). Its experience-report taxonomy covers missing content, missed/ranked-out evidence, context extraction, formatting, specificity and completeness. Map these to the learner's trace buckets rather than replacing local failure analysis with a memorized list.
- **R4/MMR:** Carbonell and Goldstein (1998), [The Use of MMR, Diversity-Based Reranking for Reordering Documents and Producing Summaries](https://www.cs.cmu.edu/afs/cs/Web/People/jgc/publication/MMR_DiversityBased_Reranking_SIGIR_1998.pdf). Supports the relevance-minus-redundancy objective; it is not the Dartboard objective.
- **R4/Dartboard:** [Better RAG using Relevant Information Gain](https://arxiv.org/abs/2407.12101), the actual paper associated with the notebook's arXiv ID. Keep this mechanism distinct from MMR and do not inherit its claimed gains as local results.
- **O3/retrieval practice:** Roediger and Karpicke (2006), [Test-enhanced learning: taking memory tests improves long-term retention](https://pubmed.ncbi.nlm.nih.gov/16507066/). Supports delayed retrieval practice rather than exposure/self-familiarity as evidence.
- **O3/spacing:** Cepeda et al. (2006), [Distributed practice in verbal recall tasks: A review and quantitative synthesis](https://pubmed.ncbi.nlm.nih.gov/16719566/). Supports spacing and its interaction with retention delay; it does not validate this curriculum's exact 1/3/7/14/30/60 ladder.
- **Runtime semantics:** [LlamaIndex SentenceSplitter API/source](https://developers.llamaindex.ai/python/framework-api-reference/node_parsers/sentence_splitter/) was checked as an official reference; the defect confirmation above relies on the locally preserved version's source, not assumptions about the current web version.

## 11. Concrete length and duplication trims

A proposed reduction of the eight-document set from **8,058 to about 4,710 lines** (roughly **42%**) is feasible. These are editorial targets, not measured reading-time savings. Preserve concept IDs, citation locators, tests, decision IDs and source provenance.

| File | Current → target lines | Concrete section-by-section trim |
|---|---:|---|
| 01 | 630 → 350 | Keep §§2.1–2.4 provenance/citation rules, compact file inventory, repo pin/defect table and Source C registry. Merge §§3.5–3.8 overlapping defect descriptions into one keyed table; reduce prior-material narrative §§5.2–5.4 to a migration table linked from 05. Keep UNVERIFIED status. |
| 02 | 1353 → 850 | Keep phase overview, concise cards with failure/outcome/pre/evidence, gates and fast-track rules. Replace repeated source paragraphs on cards with row links into 04; merge §6 book-order rationale with the canonical mapping rather than repeating it in every card. Make §8 a flexible schedule after logged pace, not a second full curriculum. |
| 03 | 791 → 420 | Keep canonical pipeline, typed prerequisite registry/table, essential family comparisons and stage/metric map. Generate the diagram from that registry; remove repeated edge listings/long project-order prose. Link source-defect detail to 01/04 and numeric metric examples to 06. |
| 04 | 1043 → 700 | Retain the master traceability matrix and divergence catalogue. Shorten §3 chapter narratives and step tables where they duplicate the matrix; generate chapter views from the same records. Keep each unique book↔cell divergence and its evidence. |
| 05 | 677 → 420 | Keep one coaching rule table, one rubric per assessment type, schedule, mastery state machine and file schemas. Compress the old-system critique/migration duplication in §§1/8 into a single checklist. Move optional §9 automation implementation detail to its future utility spec; keep its interface/requirements here. |
| 06 | 1224 → 900 | Keep canonical data/snapshot schema, metric formulas/toys, experimental controls, calibration and version acceptance. Replace repeating module/version diagrams with one diagram and a version delta table. Keep full cost/when-not-to-use detail only where it changes, not identical boilerplate on every card. |
| 07 | 1702 → 650 | Core A–F: one diagnostic, real boundary failure, integer mechanism, toy and worked example. H: fixed-window blank-file exercise plus links to preserved recursive/test code. Move exhaustive library-default tables and parity internals to sources/verification; make Part I a later I1 spec. Reduce J/K to representative failure families; L/M to a small item bank plus delayed transfer. Preserve Parts A–M coverage without requiring every lesson to contain every appendix. |
| 08 | 638 → 420 | Keep decisions, unresolved risks and staged readiness. Convert repeated Q1–Q10 explanations to short conclusions linked to canonical evidence; link bugs to 01/04 instead of duplicating full tables. Consolidate reviewer resolutions with date/owner and remaining implementation actions. |

Single-source ownership after trimming:

- **01:** source identity, limitations, external registry and defect provenance.
- **02/03:** concept outcomes and typed prerequisite/gate registry, with generated views.
- **04:** book-to-code citation mapping and unique divergences.
- **05:** teaching, assessment, scheduling and progress formats.
- **06:** runtime contracts, evaluation and experiment rules.
- **07:** learner interaction/examples, referring to canonical rules.
- **08:** decisions, risks, staged readiness.

Relocation is useful only if the same prose is removed from its old duplicate location. Do not lose durable source evidence by replacing it with a temporary scratchpad path.

## 12. Readiness checklist: every item in 08 Part 7

These marks are recorded **in this report only**; 08 remains unchanged. A checked item records the narrow criterion stated, not a blanket approval. Runtime items remain unchecked because this stage intentionally has not implemented them. The circular requirement to satisfy them all before any work must be removed under B-01.

### Sources and traceability

- [x] **S-1:** 01 records the full pinned commit, book location, page convention and provenance caveat; pin independently confirmed.
- [x] **S-2:** At least ten book citation/page checks completed; sampled denominators correct, and 452 explicit chapter denominators show no mismatch; one source-scope claim is corrected in B15.
- [x] **S-3:** Twenty repo citations resolve at the clean pinned commit with the stated zero-based cells/line numbers.
- [x] **S-4:** More than five inventory-derived upstream claims in 08 were checked against primary code; methods are distinguished in §5.3.
- [x] **S-5:** No normalized 16-word book sequence was found in workspace Markdown; no oversized book quotation was found in inspected text.
- [x] **S-6:** Source C is explicitly identified as external by the legends/registry and reviewed usages; new references here are likewise external.

### Design consistency

- [ ] **C-1:** IDs largely agree, but prerequisite/gate semantics, Phase-7 display order and mandatory-looking optional versions need alignment.
- [x] **C-2:** All inspected concept cards name their target failure; actual optional interventions still require M5 evidence.
- [x] **C-3:** Confusable technique families have homes in 02/03; no family requires all its optional implementations.
- [x] **C-4:** Missing topics in Q4(c) have concept homes or an explicit out-of-scope entry; conversational work has the recorded optional resolution.
- [x] **C-5:** Every substantive NOTE and reviewer-owned decision has an accept/amend verdict recorded here; applying amendments remains required work.

### Decisions

- [ ] **DEC-1:** The listed learner/coach choices are recommendations, not all dated, owner-confirmed decisions; reviewer-only scope is resolved in §10.
- [ ] **DEC-2:** No explicit learner acknowledgment of D-13 was established; it cannot be inferred from requesting a review.
- [ ] **DEC-3:** T/H file choices and corpus locks are not established in the design-only folder.

### Environment

- [ ] **E-1:** No project pyproject.toml/uv.lock/.git exists yet; this belongs to the O2 exit gate.
- [ ] **E-2:** A fresh local dense/BM25/provider smoke test was not performed; no credentialed call was made.
- [x] **E-3:** The selected MiniLM snapshot's sentence_bert_config.json was read directly: max_seq_length=256, revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41.
- [ ] **E-4:** No project-kernel notebook front end was launched.

### Evaluation readiness

- [ ] **V-1:** 06 does not yet contain the required frozen-text hashes/manifest reference and compatible coordinate contract; M-01.
- [ ] **V-2:** Separate formulas and toys exist, but sufficient-evidence semantics and Hit/full-recovery diagnosis need repair before approving the scoring contract.
- [x] **V-3:** Results templates remain empty; existing numbers are labeled toys, corpus properties, historical runs or assumptions.
- [x] **V-4:** Calibration/statistical rules are written down; M-05/M-06 specify the changes needed before treating them as reliable acceptance rules.

### Pedagogy

- [ ] **P-1:** Exemplar is not approved unchanged; six blocks passed, parity trace was not freshly reproduced, and contract/rubric/length fixes remain.
- [ ] **P-2:** 05 is a strong proposed protocol, but explicit learner agreement and rule-conflict resolution are not established.
- [x] **P-3:** 05 explicitly retires prior guide numbering/statuses and maps previous work to diagnostic evidence rather than mastery.

### Risk controls

- [x] **R-1:** LLM cache keys and model-ID logging are designed in 06; the separate embedding-ID caveat is M-04.
- [x] **R-2:** C1 extraction-quality checks are specified before gold labeling; they still need actual execution on chosen T PDFs.
- [x] **R-3:** 08 A-08/Part 2 require minimal reproduction before teaching defects; 07's G/H/J and verification records demonstrate that workflow, with fresh-run limits now explicit.

## 13. Exact changes Claude should make next

1. Apply B-01: stage the approval checklist so O1/O2/P/C work can legitimately produce later exit artifacts.
2. Implement the **specification edits**, not new labs, for M-01 through M-07. Choose one snapshot/coordinate/evidence contract across 02/03/04/06/07/BACKBONE.
3. Correct D-004/D-007 spans and the source-scope MMR statement; leave seeds as drafts.
4. Replace ID-only cache advice and add changed-content acceptance cases to the future test spec.
5. Fix dataset hash/qid/version comparison and test-selection policy; strengthen calibration with failure counts and held-out labels.
6. Record typed AND/OR/gate/exposure prerequisites; fix Phase-7 displays and explicitly allow skipping unjustified v7/v8 work.
7. Apply the minor lesson/coaching corrections and shorten the core exemplar before using it as the template.
8. Add the verified external references and durable verification-environment plan; retain historical logs without claiming fresh parity.
9. Carry reviewer decisions into 08 with date/owner. Leave learner-owned choices open for the learner; do not manufacture agreement.
10. Re-review corrected contracts and checklist. Only then begin the environment/core learning stage allowed by the new staged gate.

A satisfactory revision should pass the explicit counterexamples in M-01/M-02/M-04, semantically validate the dependency rules, and make the amended seed spans sufficient on their own. No requirement to run all upstream notebooks, purchase a provider, install Ollama or build an advanced architecture follows from this review.

## 14. Audit fingerprint and final verdict

The eight reviewed files were fingerprinted before report creation and can be checked against these SHA-256 values:

| File | SHA-256 |
|---|---|
| 01_SOURCE_INVENTORY.md | 53df5e41c4d56e185ab1d0e2dd4a8310563615797ce3c42c41324b41fb917a49 |
| 02_RAG_MASTER_LEARNING_PLAN.md | eda653b73130421f9e6582d7de1df801a0e25495417e0ca69f2f5bdf4bab9e8e |
| 03_RAG_CONCEPT_DEPENDENCY_MAP.md | 2eaf99df0d24d4826d637b3dcdcc259f059f711e5c7b48bd3e78988d52426b65 |
| 04_BOOK_TO_CODE_MAPPING.md | 17502113cf0d518ea70316dd90697392bfb418103ae787b47a58e4a18f6c33fd |
| 05_LEARNING_AND_RETENTION_SYSTEM.md | 5b3dbf8d40eaeeb196c3f8649c438dbb0e5de3becbfe5ca5bc40c6d3db604b8f |
| 06_RAG_PROJECT_AND_EVALUATION_PLAN.md | 973efc708e1fd664e2163c132f4e6d19b3ba6b98f8fb26d5ceef9637ac6c2d43 |
| 07_SAMPLE_LESSON.md | 63ca8f5d587be6b237b6f1306ed555939bb0d16d5d55baaf793df9421ea5afce |
| 08_GAP_ANALYSIS_AND_DECISIONS.md | 777263b2049c211a7e23783f61b8ca1a2b5ef0c383d82265561f958b8b12c84d |

**Verdict: NOT READY.** The design is strong enough to repair in place, but its current readiness rule and measurement/artifact contracts should be corrected before expansion. **84/100** is not an approval substitute. After those corrections, the appropriate next approval is for the staged environment/core work, not a claim that later runtime/evaluation gates have already passed.
