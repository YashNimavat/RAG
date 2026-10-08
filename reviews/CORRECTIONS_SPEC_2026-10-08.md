# CORRECTIONS SPEC — resolving Codex P0/P1 findings (B-01, M-01 … M-07)

Source review: `rag_learning/reviews/CODEX_REVIEW_2026-10-08.md` (the user called it RAG_PLAN_CODEX_REVIEW.md; that file does not exist — the dated report is the only Codex report).
All eight findings were independently re-verified by the orchestrator on 2026-10-08 against the unchanged files (sha256 prefixes match Codex §14).

SCOPE RULES (all editors):
- Fix ONLY B-01 and M-01…M-07 (plus the learner decisions in §L, which B-01/M-06 require). Do NOT fix Minor (m-xx) or Nit (n-xx) findings, do NOT trim/shorten documents, do NOT add new lessons, notebooks, concept IDs, or course content. Exception: where a P1 fix necessarily rewrites a passage that a minor finding also touches, fix it consistently and say so in your report.
- Never modify the book PDFs, the upstream repo, or prior learner folders.
- Every edited section gets a short marker at its end or start: `> Revised 2026-10-08 (Codex <ID>): <one line>. See [corrections log] (reviews/CORRECTIONS_LOG_2026-10-08.md#<id-lower>).` (template shown with a space so it is not parsed as a link) (use correct relative paths: from root files `reviews/...`; from `curriculum/` use `../reviews/...`). Anchors in the log will be `#b-01`, `#m-01` … `#m-07`, `#learner-decisions`.
- Keep existing IDs, citations, and anchors stable (other files link to them). If you rename a heading, keep the old anchor working by leaving the heading text unchanged where possible.
- No fabricated numbers. Values below were computed by the orchestrator (script `sources/verification/corrections/m03_seed_spans.py`, output `.out.txt`).

---

## B-01 (P0) — Replace the single circular readiness rule with three staged approval gates

Problem: 08 Part 7 says every box must be ticked before ANY lab/lesson is built, yet E-1…E-4 (env, smoke test, notebook front end) are outputs of the O2 lab itself; evaluation-readiness items are only needed before Phase 4.

Canonical contract (use these names everywhere):
- **Approval gate A — Design approval.** Required before any build work. Contents: S-1…S-6; C-1…C-5; V-1/V-2/V-4 *at specification level* (the snapshot/coordinate, evidence-group, comparability and calibration contracts are written down — not executed); V-3; P-1 (07 approved as exemplar after the P0/P1 fixes and Codex re-review); P-2 (learner agrees to the coaching protocol); P-3; R-1…R-3; DEC-2 (licence acknowledged — the learner did on 2026-10-08, see §L); DEC-1a = the decisions needed for Phases 0–2 (D-03, D-04, D-05, D-10, D-14, D-16, D-19, D-20). **Permits:** O1–O3, P1–P7 labs, and C1–C6 implementation (building v0).
- **Approval gate B — Environment & baseline exit (O2 exit, then C6 exit).** Contents: E-1…E-4 (locked uv env; smoke test = local embedding fallback + Cohere embed call + BM25 + one Groq call; notebook front end on the project kernel; embedding model limits recorded), plus "v0 runs end-to-end from a clean environment with full traces" and DEC-3 (Corpus T/H chosen, frozen, snapshot manifests created) [corrected in round 2, R-06: Corpus T chosen and frozen (with snapshot) before Phase 3; Corpus H chosen and frozen before K1]. E-items are required only before labs that depend on the environment; v0 working is required before Phase 3 work. **Permits:** M1–M5 (measurement work).
- **Approval gate C — Measurement exit / optimization entry (= learner Gate 3→4 in 02 §4).** Contents: eval set human-verified, bound to a snapshot, with evidence groups (M-01/M-02); deterministic harness reproduces identical retrieval metrics on rerun; dev/test/holdout split recorded (M-05); generation quality covered by a human-labelled pilot (M-06; the automated judge is deferred to the end by learner decision §L); M5 failure buckets with trace IDs and counts. **Permits:** Phase 4+ experiments (I1 onward).
- Every existing Part 7 item is assigned to exactly one gate (table). Explain the relationship: Part 7 gates = *build/approval* gates for artifacts; 02 §4 gates = *learner mastery* gates. Gate A ≈ precondition for Phase 0; Gate B ≈ Gate 0→1 environment part + Gate 2→3; Gate C ≈ Gate 3→4.
- Files: 08 Part 7 (rewrite intro + regroup checklist; keep item IDs S-1… etc.), README status block (current state = "design approval pending re-review after P0/P1 fixes"), 02 §4 (one short paragraph linking learner gates to approval gates; O2 card if it says otherwise), 06 §10 (wherever it says nothing may be built before all checks), BACKBONE §3.

> Revised 2026-10-08 (Codex re-review R-06): inline note on DEC-3 timing (T before Phase 3; H before K1); original text kept. See [corrections log](CORRECTIONS_LOG_2026-10-08.md#r-06).

## M-01 (P1) — One frozen-text snapshot contract and one coordinate system

Canonical contract:
1. **Snapshot manifest** (one per corpus × parser/cleaning configuration), path `evaluation/snapshots/<corpus>_<snapshot_id>.json`. Required fields:
   `snapshot_id` (= first 12 hex of doc_text_sha256 over all docs + parser/cleaning ids), `corpus`, `corpus_version`, `created_utc`,
   `parser: {backend: "pymupdf", version, call: "page.get_text()", options: {...}}`,
   `cleaning: {version, steps: [...]}` (v0: `"none"` — offsets refer to raw extracted text; any cleaning step creates a new snapshot),
   `encoding: "utf-8"`, `newline: "\n"`, `page_join: "\n"`,
   `docs: [{doc_id, pdf_sha256, bytes, pages, doc_text_sha256, page_table: [{page (1-based), doc_char_start, doc_char_end, text_sha256}]}]`.
   The snapshot text itself is stored locally next to the manifest (`<snapshot_id>/<doc_id>.txt`), git-ignored if the PDF licence is unclear.
2. **Real example values (Corpus D, PyMuPDF 1.26.7, no cleaning, pages joined with "\n"):** 33 pages; doc_chars 72,593; doc_text_sha256 `5106772efa77003b0d6c79bc1a429b8dacf244d9556f412bae1c4fe6bc7368c6`; page 1 doc_start 0, len 2,424, text_sha256 `73533984cff86c8a0a20d852bb2fd0fce36f607d5842441977109c2c222fc029`; page 2 doc_start 2,425, len 2,410, text_sha256 `c6c14ed16a4d36979110e27802f47b851fde2f801161816d4910530190cf1ea9`; page 3 doc_start 4,836, len 2,183, text_sha256 `e74d6990381b8873386ef20642880b59988d630080fecc61b7b21936abe2cacb`. pdf_sha256 `1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669`, 206,372 bytes. (page 8 doc_start 16,074; page 10 doc_start 20,555; page 23 doc_start 49,209; page 29 doc_start 62,565.)
3. **One canonical coordinate system: document offsets** into `doc_text` (pages joined with "\n"). Page-relative offsets are a *derived view*.
4. **Canonical Chunk** (replaces 06 §2.3 `Chunk` and aligns 07 H.3 `DocChunk`): `doc_id, snapshot_id, chunk_id, seq, char_start, char_end` (document offsets) `, page_segments: [{page, char_start, char_end}]` (page-relative, one per page touched; per-page chunks have exactly one), `text, text_sha256, chunker, params_hash`. Invariant tests: `doc_text[char_start:char_end] == text`; segments convert back to the same document range.
5. **Gold evidence is authored page-relative** (human-friendly) as segments `{doc_id, page, char_start, char_end}` and converted to document offsets by the loader using the snapshot `page_table` (explicit, tested conversion). Cross-page evidence = two consecutive segments forming one alternative.
6. **Fail closed:** before scoring, the loader recomputes each page's `text_sha256` (or reads the stored snapshot text) and compares it to the manifest; any mismatch, or a dataset whose `snapshot_id` differs from the index's, **stops scoring**. [extended in round 2, R-02: the binding check is incomplete without the exact-bytes `snapshot_manifest_sha256` digest, page-table structural integrity and a recomputed `snapshot_id`, all validated before any gold translation; see [CORRECTIONS_SPEC_R2](CORRECTIONS_SPEC_R2_2026-10-08.md#r-02-major-m-01-fail-closed-binding-and-page-table-integrity)]
7. **Parser/cleaning change ⇒ new snapshot ⇒ new dataset version.** Quote search may *propose* migrated offsets, but every migrated span must be re-validated by the learner; quote uniqueness alone never authorises reuse of old labels. (Replaces 06 §5.3 rule 2 "re-resolved automatically".)
8. **Dataset header** records `snapshot_id`, `snapshot_manifest_sha256`, `scorer_version`.
Acceptance (write as the test spec): a page-2 span and a cross-page (pp.12–13) span score identically whether chunks are per-page or cross-page after conversion; a changed page hash stops scoring; an extraction change cannot silently reuse prior gold.
Files: 06 §2.3, §5.3, §6.1, §6.4, §9.6 test sketch; 07 H.3 (DocChunk fields/design decisions, D.9 provenance table row for offsets if it conflicts, C2-A-05 if it defines a conflicting coordinate rule); 08 D-17 + V-1; BACKBONE §5.

> Revised 2026-10-08 (Codex re-review R-02): inline note on item 6 (full fail-closed binding checks); original text kept. See [corrections log](CORRECTIONS_LOG_2026-10-08.md#r-02).

## M-02 (P1) — Evidence sufficiency: fact groups (AND) of alternatives (OR); complete-evidence recovery is primary

Canonical contract:
1. Replace flat `gold_evidence` + optional `evidence_mode` with **required** `evidence_groups` for scored answerable items:
   ```json
   "evidence_groups": [
     {"group_id": "g1", "fact": "<the fact this group supplies>",
      "alternatives": [
        {"alt_id": "g1a", "segments": [{"doc_id": "climate", "page": 8, "char_start": 1920, "char_end": 2007}], "quote": "<=25 words"},
        {"alt_id": "g1b", "segments": [{"doc_id": "climate", "page": 23, "char_start": 1437, "char_end": 1566}], "quote": "..."}
      ]}
   ]
   ```
   Groups are AND (all required facts); alternatives inside a group are OR (any one sufficient source). Each alternative must be a **complete minimal sufficient span** (a reader shown only it can supply that fact without outside knowledge). Unanswerable items have `evidence_groups: []`. `evidence_logic_version` is recorded in the dataset header.
2. **Coverage** is computed in document coordinates over the **union** of the character ranges of the chunks at a given pipeline stage (candidate pool, final top-k, or final assembled context). An alternative is **satisfied** iff every non-whitespace character of its segments is covered (tolerance: whitespace/newline differences only; state the tolerance explicitly as `tolerance = whitespace-only`).
3. **Primary sufficiency metric: Complete-Evidence@k (CE@k)** = 1 iff every group has ≥1 satisfied alternative in the stage's set; mean over answerable items. Also **Group-Recall@k** = fraction of groups satisfied (diagnostic).
4. **Continuous diagnostic: Span-Coverage@k** = mean over groups of the best alternative's covered-character fraction — clearly named as a diagnostic, never a pass/fail.
5. **First-evidence diagnostics:** Hit@k, MRR, Precision@k, nDCG use a single chunk-relevance rule: a chunk is relevant iff it overlaps (≥1 non-whitespace character) any segment of any alternative. They measure *first evidence*, NOT sufficiency. Remove `min_span_coverage`/τ as a decision threshold and remove the ambiguous `relevance_rule: {mode: any_overlap, min_span_coverage: 0.5}`; config becomes `scoring: {scorer_version: "s1", chunk_relevance: "any_overlap", sufficiency: "complete_evidence", tolerance: "whitespace-only"}`.
6. Stage-specific reporting: retrieval experiments report CE at final top-k; context-assembly versions (v4.x) must ALSO report CE on the final assembled context (this also covers part of minor m-06 — say so).
7. 03 §6.3 2×2 diagnosis: "retrieval succeeded" = CE@k = 1 (and CE on final context for generation diagnosis); Hit@k = 1 only means "some evidence arrived".
Acceptance (test spec, also executed in `sources/verification/corrections/contracts_check.py`): D-005 half-span fragments ("Coal is the most carbon" + "Natural gas is the least carbon-intensive fos") ⇒ CE = 0; two-group item with one group retrieved ⇒ CE = 0; D-004 with either alternative ⇒ CE = 1; a span split across two retrieved chunks whose union covers it ⇒ CE = 1.
Files: 06 §2.4 config, §6.1, §6.4 (steps 3 & 7), §7.2, §7.3 (metric table + toy example: recompute toy so it uses CE; keep the existing toy numbers for Hit/P/MRR/nDCG which remain valid, add CE/Group-Recall rows), §7.6 if it names primary metrics, version cards whose primary metric is "Recall@k" → CE@k (keep Recall@k wording only where it means CE; be careful), §6.7 seeds (converted to evidence_groups); 03 §6.2–6.4; 07 Part B.1 analysis, Part I (H1–H5 primary metrics & results templates: replace "Recall@4 (span coverage)" with CE@4 primary + Span-Coverage diagnostic), I.3 table; 02 M1/M2 cards and Gate 3→4 text if they define Recall@k as primary; BACKBONE §5.

## M-03 (P1) — Seed spans must be semantically sufficient

Corrected values (computed, quotes verified to occur exactly once on the page; PyMuPDF 1.26.7):
- D-004 alternative p.23: **[1437, 1566)** (was [1463,1566)); text "Direct Air Capture (DAC) DAC technology removes CO2 directly from the atmosphere, offering a way to achieve negative emissions." (19 words). Alternative p.8 [1920, 2007) unchanged.
- D-007 group A (UNFCCC provides the framework) p.10: **[137, 339)** (was [211,339)); text "The UNFCCC is an international treaty aimed at addressing climate change. It provides a framework for negotiating specific protocols and agreements, such as the Kyoto Protocol and the Paris Agreement." (30 words) → `quote` = first 25 words: "The UNFCCC is an international treaty aimed at addressing climate change. It provides a framework for negotiating specific protocols and agreements, such as the" ; char_end stays 339.
- D-007 group B (COP is the supreme body of the UNFCCC) p.29: **[963, 1106)** (was [963,1078)); text "The Conference of the Parties (COP) is the supreme decision-making body of the United Nations Framework Convention on Climate Change (UNFCCC)." (21 words).
- All seeds keep `created_by: "llm-draft"`; Codex checking is NOT human verification.
- Convert all 10 seeds to the M-02 `evidence_groups` schema: D-001/D-002/D-003/D-008 one group one alternative; D-004 one group two alternatives (p.8, p.23); D-005 two groups (coal; natural gas); D-006 two groups (land use; evaporation + efficiency) — keep existing offsets; D-007 two groups (above); D-009/D-010 `evidence_groups: []`. Add `split` and `group` fields per M-05. Keep all other existing fields/values.
Files: 06 §6.7 (seed JSONL + text), 06 §6.1 example item (D-002) re-expressed in new schema.

## M-04 (P1) — IDs are not cache keys; content identity is required

Canonical contract:
1. `chunk_id = f"{doc_id}:{snapshot_id}:{params_hash}:{seq:05d}"` — namespaced by snapshot (whose hash changes whenever extracted text changes). Chunks also carry `text_sha256`.
2. **Embedding cache key** = `sha256(provider | model_id | model_revision | input_type ("search_document"/"search_query" for Cohere; "none" otherwise) | preprocessing_version | text)`. LLM cache key unchanged (`sha256(model_id|messages|params)`). State: "config hash alone is not content addressing; chunk/artifact IDs are for joins and traces, never cache keys."
3. Remove the 07 H.3 sentence claiming caches keyed by id stay valid. Update the H.3 code: `DocChunk` gains `snapshot_id` and `text_sha256`; `chunk_document(doc_id, snapshot_id, pages, cfg)`; add `embedding_cache_key(...)` helper. Add tests: (a) same content + config ⇒ identical ids and cache keys (reproducible); (b) same doc/position, changed text ⇒ different cache key (and different snapshot_id ⇒ different chunk_id); (c) query vs document input_type ⇒ different keys. Codex counterexample: doc1, fixed 40/10, texts "AAAA" vs "BBBB" previously gave the same id `doc1:c5c8dfd3d707:00000`.
4. 06 §2.3 chunk_id comment and §2.4 cache config updated (`embeddings: .cache/emb  # keyed by sha256(provider|model_id|revision|input_type|preproc_version|text)`).
Files: 07 H.3 code + design decisions + tests + any mention in J/L items; 06 §2.3/§2.4 (and D1/D2 notes if they mention id caching); BACKBONE §6.
All modified code must be executed and the tests run (pytest via `uv run --no-project --with pytest --with numpy python -m pytest ...` in a scratch dir, or direct calls); record results.

## M-05 (P1) — Exact dataset identity for comparisons; dev/test/holdout discipline

Canonical contract:
1. **Paired comparisons require identical comparison keys:** `dataset_sha256`, `snapshot_id`, qid set, labels, split, `scorer_version`. The runner aligns per-question arrays **by qid** (never by position) and **rejects** arrays whose qid sets differ.
2. **Versioning:** any addition, edit, removal, relabel, split change or scorer change produces a new dataset file and hash. MAJOR/MINOR names stay as human labels, but comparability is defined **by hash**, not by MAJOR version. After items are added, rerun baseline, champion and candidate on the new version, or explicitly compare only on the declared unchanged-qid intersection.
3. **Splits:** `dev` (selection: grid search, thresholds, λ, pool sizes), `test` (locked; touched once per selection round to confirm the chosen candidate), `holdout` (untouched until K1 architecture defence; plus Corpus H). Paraphrase variants share a `group` with their base item; splitting and bootstrap resampling are done **by group** (cluster bootstrap).
4. **Test reuse:** each test touch is logged (selection round, number of configurations tried). Test items inspected repeatedly become regression data; a fresh final set / holdout + Corpus H is reserved for K1. Threshold cross-validation must be nested or use an outer holdout.
5. Update 06 §9.3 `paired_bootstrap` sketch to take dicts `{qid: value}` (or arrays + qids), assert equal qid sets, align by qid, and support group-level (cluster) resampling.
Acceptance: runner rejects different qid sets; shuffled order aligned by qid; base and paraphrase cannot cross splits; candidate selection documented without test-driven retuning.
Files: 06 §6.3 item 6, §6.6, §7.6, §9.3, §9.4 (item 3), §9.2 controls checklist, version-card adoption legend in §4.2 if it says "confirm on test"; 07 I.1 decision rule ("grid selection on dev; confirm once on test"); 02 Gate 3→4 (split recorded); BACKBONE §5.

## M-06 (P1) — Judge calibration is a pilot; certification needs counts, intervals and disjoint sets

Canonical contract (combined with learner decision D-10, §L):
1. **Labelling unit per metric:** faithfulness = claim-level (each atomic claim: supported / unsupported / contradicted); citation = per citation (does the cited excerpt support its sentence?); correctness = answer-level (correct / partial / wrong); abstention = deterministic (no judge). **Abstentions are excluded** from faithfulness and citation calibration.
2. **The first 30 labelled units per metric are a pilot**, used to draft/fix the rubric only.
3. **Certification** requires a *separate, untouched* validation set with **≥30 failure-class units and ≥30 non-failure units per metric** (Assumption/[P] counts), reporting the confusion matrix, Cohen's κ and failure-class recall **with Wilson 95% intervals** and denominators [corrected in round 2, R-03: intervals by statistic: confusion matrix as raw counts; Wilson (or a cluster bootstrap over answers) for binomial rates only; paired bootstrap or large-sample variance for κ, never Wilson; certification on lower 95% bounds, Assumption]. Thresholds (κ ≥ 0.6, failure recall ≥ 0.8) are provisional operating preferences, judged on the interval, never on undefined or tiny denominators (no pass on undefined failure recall). Example to include: 8 of 10 failures caught ⇒ recall 0.8 but Wilson 95% CI ≈ 0.49–0.94 (too wide to certify).
4. If natural outputs contain too few failures, add a **labelled challenge set** (fabricated claims, swapped citations, contradictions) kept separate from natural outputs; report both.
5. Rubric-tuning units and validation units are disjoint; separate **judge repeat variance** (flip rate on repeated runs) from **paired metric-effect uncertainty** (bootstrap).
6. **Unanswerables:** 40 answerable + 6 unanswerable stays a *learning minimum* for Gate C; no abstention-threshold claims until ≥15 unanswerable items exist with ≥5 in dev (Assumption/[P]). Example: 6/6 correct still has an exact two-sided 95% lower bound ≈ 0.54.
7. **Human evaluation is the essential fallback**: Gate C needs a human-labelled generation pilot on v0 (≥30 answer-level labels), not a certified judge.
8. **Learner decision D-10 (2026-10-08):** automated judge = a **Cohere chat model** (different family from the Groq generator); **Codex** = independent calibration labeller on a fixed sample (it is not programmatic and is not the per-run judge; its labels are not "human"); **all judge-based metrics run once, at the end of the curriculum, in a batch over the stored traces of every version** (identical inputs). Until then, decisions use deterministic metrics (CE@k etc., abstention, citation-excerpt existence, EM/F1 for short answers) plus human reading of ~10 answers per version; generation-dependent choices in Phases 7–8 are provisional and may be revised by the final judge batch.
Files: 06 §8.1–8.5 (and §8.6 call budget if it assumes per-run judging), version cards that require judge metrics per version (mark them as human-pilot/deferred judge), 02 Gate 3→4 and M3 card, 08 D-10 (+ RK-03 mitigation text), BACKBONE §5.

> Revised 2026-10-08 (Codex re-review R-03): inline note on item 3 (intervals by statistic; no Wilson for κ or the confusion matrix); original text kept. See [corrections log](CORRECTIONS_LOG_2026-10-08.md#r-03).

## M-07 (P1) — Typed prerequisites: all / any-groups / gate / exposure

Canonical contract:
1. Replace 03 §2.1's columns with a typed registry: `ID | Tier | requires_all | requires_any_groups | requires_gate | requires_exposure | advice (optional, non-binding) | unlocks`. Soft edges mean truly optional advice only. Keep project-version order (which version comes first in the project) separate from conceptual prerequisites — note it in a separate column or note, not as hard edges.
2. Gate names refer to 02 §4 learner gates (e.g. `Gate 3→4`). **Every Phase 4–11 concept** (I*, R*, Q*, X*, V*, D*, A*, S*) has `requires_gate: Gate 3→4` (so S2 can no longer bypass M3/M4/M5).
3. OR groups: **A5** `requires_any_groups: [[A1, A2]]`; **S3** `requires_any_groups: [[S1, R5]]`. (Check 02 for any other "X or Y" wording and convert it.)
4. **I-CMP** `requires_exposure: [I2, I3, I4, I5, I6]` (mechanism exposure: read + trace or demo, not full implementation), matching 02.
5. **K1**: requires `I-CMP, V3, D2` + `requires_gate: Gate 9→10`; K1 must be reachable **without** any A* or S* concept (A/S are electives: v6 → K1 is allowed when residual failures do not justify a controller). Resolve the D3 problem: the minimal regression competence that Gate 9→10 needs is the **T1 retrieval regression test, which is an M4 outcome (M4 already covers regression sets, E)**; D3 (U) is CI wiring, index versioning and incremental re-indexing and is advice for K1, not required. Update 02 §4 Gate 9→10 wording accordingly.
6. The Mermaid diagram is a generated *view*: represent an OR group with a junction node labelled "any of", gates as labelled nodes or a note; keep it valid.
7. 02 concept cards' Pre lines use the same typed notation: `Pre: all{…}; any{A1 | A2}; gate{3→4}; exposure{…}` for the affected cards (A5, S1, S2, S3, K1, I-CMP, and any card whose Pre line names a gate in prose). 04 traceability matrix "Required prerequisites" column mirrors 02 for changed rows.
8. Validator: `sources/verification/corrections/contracts_check.py` parses the 03 registry table and checks: acyclic hard edges; every any-group has ≥2 members and cannot be satisfied by zero members; S2 and every Phase 4–11 concept require Gate 3→4; K1's requirement closure contains no A*/S* concept; A5 cannot unlock without A1 or A2; S3 without S1 or R5; agreement of `requires_all` with 02 Pre lines.
Files: 03 §2 intro, §2.1, §2.2 (edit bullets that call project order "hard"), diagram; 02 cards + §4 Gate 9→10; 04 matrix rows for changed concepts; BACKBONE §3 (mention typed prerequisites).

## §L — Learner decisions (2026-10-08, from the conversation; record in 08 Part 4 with date + owner "Learner")
- D-03 Embeddings: **Cohere embed = default** (input_type search_document / search_query; cache per M-04), **local sentence-transformers = fallback** (offline + second-model comparison). 07's MiniLM/bge numbers stay as upstream-parity / illustration; truncation must be re-measured for the Cohere model at O2/C3 (E-3).
- D-04 LLM: **Groq** for generation and all non-judge LLM calls; model id from config.
- D-05 Ollama: **not used** (rejected by learner).
- D-10 Judge: see M-06 item 8.
- D-01/D-02 Corpus T: **coach's suggested arXiv mix** (3–4 RAG papers + 2 non-RAG technical papers), concrete list proposed at C1; learner may swap; Corpus H later.
- A-01 / schedule: **no time-based schedule**; self-paced, gate-driven (record in 08 Part 6 A-01; do not delete 02 §8 in this pass — add a one-line note that hour estimates are informational only per learner decision; trimming is out of scope).
- DEC-2 / D-13: learner confirmed **study-only use** of the book (owns a copy) and repo (non-commercial, attribution on copies).
- A-11: learner labels; Codex labels the calibration sample (not counted as human). A-13: simulated web fallback. A-14: my-way notebooks count as diagnostic evidence. A-02: key validity checked at O2 start (announced beforehand).
Do not mark DEC-1/DEC-3 fully ticked: D-14/D-16/D-19/D-20 remain to confirm at O2 [superseded in round 2, R-01: decided 2026-10-08 in a decision-only preflight before Gate A; O2 implements them]; T/H files not chosen [corrected in round 2, R-06: Corpus T chosen and frozen (with snapshot) before Phase 3; Corpus H chosen and frozen before K1].

> Revised 2026-10-08 (Codex re-review R-06; R-01): inline round-2 notes added to §B-01 and §L; original text kept. See [corrections log](CORRECTIONS_LOG_2026-10-08.md#r-06) and [R-01](CORRECTIONS_LOG_2026-10-08.md#r-01).
