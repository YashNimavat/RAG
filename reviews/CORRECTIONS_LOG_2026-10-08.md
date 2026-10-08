# Corrections log: Codex P0/P1 findings (2026-10-08)

**Input review:** [CODEX_REVIEW_2026-10-08.md](CODEX_REVIEW_2026-10-08.md) (verdict NOT READY, 84/100).
The request named `reviews/RAG_PLAN_CODEX_REVIEW.md`. That file does not exist; the dated report is the only Codex review, and it explains that it used the dated filename instead of the one from the older task.

**Scope.**
- All verified **P0 (Blocker)** and **P1 (Major)** findings were resolved: B-01 and M-01 to M-07.
- Learner decisions made on 2026-10-08 that these fixes depend on are also recorded.
- **Not done in this pass:**
  - minor findings m-01 to m-08 and nits n-01 and n-02, except where a P1 rewrite necessarily touched the same text (noted below);
  - Codex's proposed ~42% trim;
  - any new lessons, labs, concept IDs or course content.
- **The course was not expanded.**

**Sources preserved (checked after the edits).**
- Book PDFs: unchanged. Modification times are all 2026-06-10.
- Upstream repo: `git status` clean at `009adba2be1bef49780ef73b6dd3c18fd24b035b`.
- Prior learner folders: untouched.
- The Codex review file itself was not edited.

**How the corrections were made.**
1. Each finding was first **re-verified independently** against the reviewed files. Their sha256 prefixes matched Codex's §14 fingerprints, so the same text was checked.
2. One canonical contract per finding was written down in [CORRECTIONS_SPEC_2026-10-08.md](CORRECTIONS_SPEC_2026-10-08.md).
3. One editor per file applied the contracts.
4. An executable acceptance checker tested Codex's counterexamples against the edited documents and the real climate PDF.
5. A cross-document sweep removed leftover statements of the old contracts.
6. The orchestrator fixed the remaining inconsistencies the agents reported ([`residual_alignment_edits.py`](../sources/verification/corrections/residual_alignment_edits.py)).

Every changed section carries a `Revised 2026-10-08 (Codex <ID>)` marker linking to the matching entry below (135 markers across 01–04, 06–08 and BACKBONE; 05 needed no change).

**Acceptance evidence:** [`contracts_check.py`](../sources/verification/corrections/contracts_check.py) → [`contracts_check.out.txt`](../sources/verification/corrections/contracts_check.out.txt): **80 passed, 0 failed**. It was run with system Python 3.12.8, PyMuPDF 1.26.7 and numpy 2.3.3 (numpy is used only to execute 06 §9.3's sketch). It was re-run after the final residual edits with the same result.

| ID | Severity | Verified? | Status | Acceptance checks |
|---|---|---|---|---|
| [B-01](#b-01) | P0 | Yes | Resolved | Structural (gate table; every item ID in exactly one gate) |
| [M-01](#m-01) | P1 | Yes | Resolved | 16 PASS |
| [M-02](#m-02) | P1 | Yes | Resolved | 19 PASS |
| [M-03](#m-03) | P1 | Yes | Resolved | 2 PASS (plus the shared seed checks counted under M-02) |
| [M-04](#m-04) | P1 | Yes | Resolved | 9 PASS (+ 13 pytest cases in 07 H.3) |
| [M-05](#m-05) | P1 | Yes | Resolved | 9 PASS |
| [M-06](#m-06) | P1 | Yes | Resolved | 3 PASS (interval numbers) + document changes |
| [M-07](#m-07) | P1 | Yes | Resolved | 22 PASS |

---

<a id="b-01"></a>
## B-01 (P0): circular readiness rule → three staged approval gates

**Finding verified.** 08 Part 7 said every box must be ticked before *any* lab notebook or lesson is built. Yet E-1 to E-4 (locked env, smoke test, notebook front end) are outputs of the O2 lab itself, and the evaluation items are only needed before Phase 4. The gate could never be passed.

**Correction.** The single gate was replaced by three **approval gates** (build permissions), kept separate from the **learner mastery gates** in 02 §4.

| Gate | Requires | Permits | Matching learner gate |
|---|---|---|---|
| **A: Design approval** | Source audit (S-1–S-6); consistency (C-1–C-5); contracts written at specification level (V-1, V-2, V-4); V-3; exemplar approved (P-1); P-2, P-3; R-1–R-3; DEC-1a/1b; DEC-2 | O1–O3, P1–P7 labs, C1–C6 (building v0) | Before Phase 0 |
| **B: Environment & baseline exit** | E-1–E-4 (O2 outputs; needed only before labs that depend on them); BL-1 (v0 end-to-end from a clean env with traces); DEC-1c; DEC-3 (Corpus T frozen with snapshot) | M1–M5 | Environment part of Gate 0→1, plus Gate 2→3 |
| **C: Measurement exit** | MX-1–MX-5: verified eval set bound to a snapshot with evidence groups; reproducible harness; recorded splits; human generation pilot; M5 failure buckets | Phase 4+ experiments | Gate 3→4 |

**Where:**
- 08 header purpose line and Part 7: intro rewritten; checklist regrouped under gates A, B and C with "Permits:" lines; DEC-1 split into 1a/1b/1c; new BL-1 and MX-1…MX-5.
- 02 §4: "Learner gates vs approval gates" paragraph; O2 card.
- BACKBONE §3: staged approval-gate table.
- README: status block.

**Ticks recorded in 08 Part 7:**
- Items Codex ticked are marked `[x] (Codex 2026-10-08)`.
- DEC-2 is ticked on the learner's confirmation.
- V-4 and E-3 were left open: V-4's criterion was rewritten, and Codex verified only MiniLM's limit while Cohere is now the default.

**Residual alignment by the orchestrator:** DEC-3 now requires Corpus T before Phase 3, and Corpus H only before K1, because the learner deferred choosing H.

<a id="m-01"></a>
## M-01 (P1): one frozen-text snapshot contract and one coordinate system

**Finding verified.**
- 06 §2.3 `Chunk` used page-relative offsets, while 07 H.3 used document offsets.
- 06 §5.3 rule 2 re-resolved offsets *automatically* after parser changes.
- No per-page text hashes existed.

**Correction.**
- **Snapshot manifest** (`evaluation/snapshots/<corpus>_<snapshot_id>.json`): parser and version/options, cleaning version (v0: none), encoding, newline, page join, PDF hash, `doc_text_sha256`, and a page table (document start/end + `text_sha256` per page).
  - The exact `snapshot_id` formula is fixed in 06 §5.3.
  - Real Corpus D values are shown: 33 pages, 72,593 characters, doc hash `5106772e…`, page-table rows 1–3.
- **One coordinate system: document offsets.** Page-relative offsets are a derived view (`page_segments`).
  - Canonical `Chunk`/`DocChunk` fields are identical in 06 and 07.
  - Gold evidence is authored page-relative, and the loader converts it through the page table (tested).
- **Fail closed.** A page-hash mismatch, or a dataset or index bound to another `snapshot_id`, stops scoring. *[Extended in round 2, see [R-02](#r-02): manifest digest, page-table structure and recomputed `snapshot_id` are also checked before any gold label is translated.]*
- **A parser or cleaning change means a new snapshot and a new dataset version.** Quote search only *proposes* migrated spans, and the learner re-validates them.

**Where:**
- 06 §2.2, §2.3, §2.4, §2.5, §3.1, §5.3, §6.1, §6.4, §9.6.
- 07 D.1 diagram, D.9 table, H.3 code and design decisions, Part K index/incremental-update guidance.
- 08 D-17, V-1, RK-05.
- 02 C3 card.
- BACKBONE §5.

**Acceptance (all PASS):**
- The manifest values recompute from the PDF.
- D-002 converts from p.10 [438,537) to doc [20993,21092), and 2,000 random spans round-trip.
- A page-2 span and a pp.12–13 cross-page span score identically under per-page and cross-page chunking; the negative control without conversion differs.
- A tampered page hash raises `SnapshotMismatch`.
- A dataset on another snapshot is refused.
- The 06 and 07 chunk fields are identical.

**Note.** The checker serialises its own snapshot id (`e4fa80ec1678`, valid only inside the checker). The documented formula was fixed afterwards. The production id is computed by `ragkit` at C1.

<a id="m-02"></a>
## M-02 (P1): evidence sufficiency; Complete-Evidence@k is primary

**Finding verified.**
- With the default τ = 0.5, half of a span counted as "retrieved".
- The config listed `mode: any_overlap` and `min_span_coverage: 0.5` with no precedence between them.
- A flat `all`/`any` mode could not express "fact A AND fact B, each with alternative sources".
- 03's 2×2 diagnosis treated Hit@k = 1 as success.

**Correction.**
- **Required `evidence_groups`:** groups are AND, alternatives within a group are OR, and each alternative is a complete minimal sufficient span.
- **Coverage** is measured over the union of the chunks at a stated stage (candidate pool, top-k or final context), in document coordinates, with whitespace-only tolerance.
- **Primary metric: Complete-Evidence@k (CE@k).**
- **Diagnostics:**
  - Group-Recall@k;
  - Span-Coverage@k (continuous);
  - Hit/MRR/Precision/nDCG, which measure *first* evidence under one any-overlap rule.
- τ was removed as a decision threshold. The config is now `scoring: {scorer_version: s1, chunk_relevance: any_overlap, sufficiency: complete_evidence, tolerance: whitespace-only}`.
- v4.x versions must also report CE on the final assembled context. This also covers part of minor m-06.

**Where:**
- 06 §2.4, §6.1, §6.4, §7.2, §7.3 (toy example gains CE@3 = 0, CE@5 = 1, Group-Recall rows), §9.4, §9.6, and version cards v1.0–v4.1 plus the §4.3 roll-up (Recall@4 → CE@4).
- 03 §6.1–§6.4: the 2×2 is now split on CE@k, with final-context CE separating assembly from generation failures.
- 07 B.1, PK-7, Part I (H1–H5, I.3, I.4, I.5), J1/J5/J8, Part K, C2-A-05, C2-T-01/02.
- 02 principle 3, M1/M2/X1 cards.
- 04 Q1 row.
- 08 V-2, D-09, A-09.
- BACKBONE §2 and §5.

**Acceptance (Codex counterexamples, all PASS):**

| Case | Result |
|---|---|
| D-005 half-span fragments | CE 0 (Hit 1, Span-Coverage 0.504) |
| One of two groups retrieved | CE 0 (Group-Recall 0.5) |
| D-004, either alternative | CE 1 |
| D-004, old p.23 start | CE 0 |
| Span covered only by two chunks together | CE 1 |
| D-007 p.29 alone | CE 0 |

The §7.3 toy values reproduce, and the 06 §9.6 test sketches pass on the reference code.

<a id="m-03"></a>
## M-03 (P1): seed evidence spans that were not self-sufficient

**Finding verified** by re-extracting the climate PDF (PyMuPDF 1.26.7):
- D-004's p.23 span began *after* the heading that expands "DAC".
- D-007's p.10 span began with an unresolved "It".
- D-007's p.29 span stopped before "on Climate Change (UNFCCC)."

**Correction** (computed by [`m03_seed_spans.py`](../sources/verification/corrections/m03_seed_spans.py) → [`.out.txt`](../sources/verification/corrections/m03_seed_spans.out.txt)):

| Seed | Before | After | Quote |
|---|---|---|---|
| D-004 alt p.23 | [1463,1566) | **[1437,1566)**, includes "Direct Air Capture (DAC)" | 19 words |
| D-007 group A p.10 | [211,339) | **[137,339)**, starts "The UNFCCC is an international treaty…" | First 25 words (true end kept) |
| D-007 group B p.29 | [963,1078) | **[963,1106)**, ends "…on Climate Change (UNFCCC)." | 21 words |

- All 10 seeds were converted to `evidence_groups`.
- All stay `created_by: "llm-draft"`; Codex's check is not human verification.
- They carry `split: "unassigned"`, which scored runs reject until the learner assigns splits.

**Where:** 06 §6.1 (D-002 example), §6.7 (JSONL and table), §5.2 (quote length ≤ 25 words).

**Acceptance (PASS):**
- All 10 JSONL lines parse.
- Every quote is a prefix of its normalised span, ≤ 25 words, and occurs once on its page and on no other page.
- The corrected offsets match.
- The table quotes equal the JSONL quotes.

<a id="m-04"></a>
## M-04 (P1): chunk IDs are not cache keys

**Finding verified.** 07 H.3 claimed that caches keyed by chunk id stay valid. Reproduced: `doc_id="doc1"`, fixed 40/10, texts "AAAA" and "BBBB" gave the same id, `doc1:c5c8dfd3d707:00000`.

**Correction.**
- `chunk_id = doc_id:snapshot_id:params_hash:seq`, namespaced by the snapshot. Chunks also carry `text_sha256`.
- **Embedding cache key** = sha256(provider | model_id | model_revision | input_type | preprocessing_version | text).
- The LLM cache key is unchanged.
- Stated explicitly: IDs are for joins and traces, never cache keys, and a config hash is not content addressing.
- 07 H.3 code: `PageSegment`, new `DocChunk` fields, `chunk_document(doc_id, snapshot_id, pages, cfg)`, `embedding_cache_key`, and three new tests (reproducible; changed text gives a new key; query vs document input types).

**Where:** 07 H.3 (code, design decisions, tests), I.2, Part K, Verification log; 06 §2.2, §2.3, §2.4, §9.2; 02 C3; BACKBONE §6.

**Acceptance:**
- 07 H.3: **13 passed**, both on Python 3.12.8 with pytest 8.4.2 and on Python 3.14.2 with pytest 9.1.1.
- The new ids for the counterexample differ: `doc1:65232ca1fd98:…` vs `doc1:656cee243439:…`, with different cache keys.
- The checker's 9 M-04 checks PASS, including "a stale snapshot_id reused by mistake still gives a different cache key".

<a id="m-05"></a>
## M-05 (P1): exact dataset identity for comparisons; dev/test/holdout discipline

**Finding verified.**
- Adding items was a MINOR version, yet comparability was defined "within one MAJOR version".
- The test split could be reused for repeated selection.
- Cross-validation over the full set had no outer holdout.

**Correction.**
- Paired comparisons require identical `dataset_sha256`, `snapshot_id`, qid set, labels, split and `scorer_version`.
- The runner aligns values by qid and rejects mismatched qid sets.
- After any addition: rerun baseline, champion and candidate, or compare on the declared unchanged-qid intersection.
- **Splits:**
  - `dev`: all selection;
  - `test`: locked, touched once per selection round, every touch logged in `TEST_LOG.md`;
  - `holdout` and Corpus H: untouched until K1.
- Paraphrases share a `group` with their base item; splitting and bootstrap resample by group.
- Nested cross-validation only.

**Where:**
- 06 §4.1, §6.3, §6.6, §7.6, §9.1–§9.4, plus the §9.3 `paired_bootstrap`, now `{qid: value}` with cluster resampling.
- 07 I.1 decision rule, I.2, I.4 test-confirmation log.
- 02 M1/M4/I1 cards and Gate 3→4.
- 08 D-09, RK-04, V-4, MX-3.
- BACKBONE §4 and §5.

**Acceptance (PASS):**
- Shuffled order gives an identical result, with both the reference implementation and the 06 sketch.
- Mismatched qid sets raise.
- The cluster bootstrap keeps base and paraphrase together (grouped CI [0,0] vs ungrouped [−0.6,0.6]).
- The group-level split keeps them in one split (50 seeds).
- A differing comparison key is rejected.

<a id="m-06"></a>
## M-06 (P1): judge calibration is a pilot; certification needs counts, intervals and disjoint sets

**Finding verified.**
- 30 items per metric could contain almost no failures.
- Abstentions were included in support metrics.
- A failure recall ≥ 0.8 could be undefined or rest on tiny denominators.
- The flip rate was conflated with effect uncertainty.

**Correction (combined with learner decision D-10):**
- **Labelling units:** claim-level for faithfulness, per citation, answer-level for correctness. Abstention is scored deterministically, and abstentions are excluded from support metrics.
- **The first 30 units are a pilot** (rubric only).
- **Certification** needs a disjoint, untouched validation set with **≥ 30 failure and ≥ 30 non-failure units**, reporting the confusion matrix, κ and failure recall with **Wilson 95% intervals**. Example: 8/10 gives ≈ 0.49–0.94, too wide. *[Corrected in round 2, see [R-03](#r-03): Wilson applies only to binomial rates; κ gets a bootstrap or κ-variance interval; the confusion matrix is reported as counts.]*
- A labelled challenge set is used when natural failures are rare.
- Repeat-judge variance is reported separately from bootstrap uncertainty.
- **Unanswerables:** 40 + 6 is a learning minimum. No threshold claim until there are ≥ 15 unanswerables with ≥ 5 in dev; even 6/6 has an exact lower bound of ≈ 0.54.
- **Human evaluation is the fallback.** Gate C needs a human-labelled pilot (≥ 30 answer-level labels), not a certified judge.
- **Learner decision D-10:** a Cohere chat model is the evaluation judge, and Codex is an independent calibration labeller (not counted as human). All judge-based metrics run **once at the end**, over the stored traces of every version. Until then, decisions use deterministic metrics plus human reading, and Phase 7–8 choices are provisional.

**Where:**
- 06 §6.2, §7.4, §8.1–§8.6, version cards v0.1/v4.0/v4.1/v5.0/v6.0, §10, §11.
- 02 M3, V3, V4 cards, Gate 3→4, Gate 8→9.
- 03 §6.2 (correctness and abstention rows).
- 04 M3/M4/X2/V3/V4 rows.
- 08 D-10, D-09, RK-03.
- BACKBONE §3 and §5.

**Acceptance (PASS):**
- Wilson 95% for 8/10 = 0.4902–0.9433, and the exact 6/6 lower bound = 0.5407. These match the numbers quoted in 06 and BACKBONE.

<a id="m-07"></a>
## M-07 (P1): typed prerequisites (all / any-groups / gate / exposure)

**Finding verified.**
- "A or B" was encoded as two optional soft edges, which can be satisfied by neither.
- S2 could unlock after M2 without M3–M5.
- A5 and S3 had no mandatory alternative.
- K1's gate silently required D3, a U-tier concept.

**Correction.**
- 03 §2.1 is now a single machine-parseable **typed registry** for all 56 concepts, with columns `requires_all`, `requires_any_groups`, `requires_gate`, `requires_exposure`, `advice`, `unlocks`.
- **Every Phase 4–11 concept requires Gate 3→4.**
- **OR groups:** A5 `[A1 | A2]`, S3 `[S1 | R5]`, plus R3 `[R1 | C4]` and A4 `[A1 | A2]`, converted from 02's wording.
- **I-CMP** gets exposure to I2–I6.
- **K1** = all{I-CMP, V3, D2} + Gates 3→4 and 9→10. No A\*/S\* concept is required, and D3 is advice only. Gate 9→10's regression requirement is now the **M4 T1 test** (E).
- Project-version order is listed separately from prerequisites.
- The Mermaid diagram is a generated view, with "any of" junction nodes and gate nodes.
- 02 Pre lines use typed notation. 02 now states that the **03 registry is the single unlock rule**: Pre lines list the key direct prerequisites, and each is validated to be an ancestor in 03.

**Where:**
- 03 §2 intro, diagram, §2.1, §2.2, §3.1, §3.6.
- 02 §1.2 legend and authority statement, cards I-CMP/R3/A1/A2/A4/A5/S1/S2/S3/K1/M4, Gate 9→10.
- 04 matrix rows for the same concepts.
- BACKBONE §2 and §3.

**Acceptance (22 PASS):**
- The registry counts match (56 concepts / 78 / 4 groups / 8 members / 5 / 5).
- The hard edges are acyclic, and no edge points back to an earlier phase.
- Every any-group has ≥ 2 members and fails with zero.
- Every Phase 4–11 concept (S2 included) requires Gate 3→4.
- K1 unlocks with no A\*/S\* mastered.
- A5 needs A1 or A2; S3 needs S1 or R5.
- Every concept 02 names is an ancestor in 03, and the any/exposure/gate notation agrees.

**One fix during verification:** K1's gate field gained Gate 3→4 to match 02 and 04.

**INFO, not a failure:** 03 is stricter than 02 in 14 places (for example S2 ← M2, A4 ← V4). These are covered by the authority statement.

<a id="learner-decisions"></a>
## Learner decisions recorded (2026-10-08)

These came from the conversation, not from Codex. They are recorded because B-01 (DEC-1a) and M-06 depend on them.

| Decision | Recorded value | Where |
|---|---|---|
| D-03 Embeddings | Cohere embed default (`search_document`/`search_query` input types; content-keyed cache); local sentence-transformers fallback. 07's MiniLM/bge numbers stay as labelled illustrations; truncation is re-measured for the Cohere model at O2/C3 (E-3) | 08, 06 §2.4/§3.1/§3.2, 01 §4.1/§4.3/§4.7, 02, 07 I.1, BACKBONE §0/§4/§6 |
| D-04 LLM | Groq for generation and all non-judge calls; model id from config | Same files |
| D-05 Ollama | Not used | Same files |
| D-10 Judge | Cohere chat judge + Codex calibration labeller; one final batch over stored traces | See [M-06](#m-06) |
| D-01/D-02 Corpus T | Coach's mix: 3–4 RAG papers + 2 non-RAG technical papers; list proposed at C1; learner may swap. Corpus H deferred (needed before K1) | 08, 06 §5.1 |
| D-13 / DEC-2 | Study-only use of the book (the learner owns a copy) and of the repo (non-commercial, attribution on copies) | 08 Part 4 and Part 7 |
| A-01 | No time-based schedule; self-paced and gate-driven. Hour estimates are informational | 08 Part 6, 02 §8 |
| A-02 / A-11 / A-13 / A-14 | Key check announced at O2 start; learner labels, Codex labels the calibration sample; simulated web fallback; `my way/` notebooks count as diagnostic evidence | 08 Part 6 |

## Remaining items (not P0/P1; carried to the next pass)

1. **Minor and nit findings, untouched:**
   - m-01: PK-5 rubric and absolute citation-granularity claim.
   - m-02: C2 session length, 350 minutes.
   - m-03: 07 fast-track wording.
   - m-04: CR-04/CR-06 hint-rule conflict.
   - m-05: PyPDFLoader vs PyMuPDF numbers.
   - m-06: partly covered via final-context CE.
   - m-07: v7/v8 elective wording.
   - m-08: durable verification environment.
   - n-01, n-02.
2. **Codex's trim proposal** (8,058 → ~4,710 lines). The edits added text: the eight deliverables plus BACKBONE are now 8,903 lines.
3. **Line endings:** 08 is now saved with LF while the other files use CRLF. This is harmless to content.
4. ~~**Validator id:** `contracts_check.py` uses its own snapshot-id serialisation.~~ Done in round 2 ([R-02](#r-02)): the checker executes the exact 06 §5.3 recipe (Corpus D = `ea07572562ac`).
5. **Seed splits:** the learner must assign splits and verify all 10 seed items before they can be scored.

## Request for re-review (round 1, superseded)

*Superseded by [Round 2](#round-2-codex-re-review-findings-r-01-to-r-07). Codex's first re-review ([CODEX_REREVIEW_2026-10-08.md](CODEX_REREVIEW_2026-10-08.md)) did not grant Gate A.*

Please re-review **only** the eight sections above against Codex's acceptance criteria. The fastest checks are to re-run `python -I sources/verification/corrections/contracts_check.py <climate PDF>` and to read 08 Part 7. If the re-review confirms B-01 and M-01 to M-07, the next permitted step is **approval gate A**: Phase 0 (diagnostic, uv environment, key checks).


---

## Round 2: Codex re-review findings R-01 to R-07

**Input:** [CODEX_REREVIEW_2026-10-08.md](CODEX_REREVIEW_2026-10-08.md). Its verdicts:
- **Resolved:** M-02, M-03, M-04 and M-05.
- **Partially resolved:** B-01, M-01, M-06 and M-07.
- **Gate A:** not granted.
- **Remaining issues:** one blocker (R-01), three majors (R-02 to R-04) and three minors (R-05 to R-07).

**What was done:**
- Every R-finding was re-checked against the cited lines before editing. All seven hold. Examples: `can_unlock` checked exposure against the *mastered* set; the qid guard compared lists by order; 08's DEC-1a said its decisions were "confirmed at the start of O2".
- The contracts are in [CORRECTIONS_SPEC_R2_2026-10-08.md](CORRECTIONS_SPEC_R2_2026-10-08.md).
- File-owned editors applied them, the acceptance suite was extended, a consistency sweep followed, and the orchestrator applied the last residual edits ([`round2_residual_edits.py`](../sources/verification/corrections/round2_residual_edits.py)).
- **Sources preserved:** book PDFs, the upstream repo (clean at `009adba`), prior learner folders and both Codex review files were not modified.

**Acceptance evidence:** [`contracts_check.py`](../sources/verification/corrections/contracts_check.py) → [`contracts_check.out.txt`](../sources/verification/corrections/contracts_check.out.txt) reports **142 passed, 0 failed** (round 1: 80).

| Group | Passed |
|---|---|
| M-01 | 15/15 |
| R-02 | 17/17 |
| R-05 | 8/8 |
| M-02 | 19/19 |
| M-03 | 2/2 |
| M-04 | 9/9 |
| M-05 | 9/9 |
| R-07 | 5/5 |
| M-06 | 3/3 |
| R-03 | 11/11 |
| M-07 | 22/22 |
| R-04 | 8/8 |
| B-01 | 5/5 |
| R-01 | 7/7 |
| R-06 | 2/2 |

- 07 H.1 + H.3 extracted tests: **13 passed** (pytest 8.4.2, Python 3.12.8).
- **The suite can fail.** It was broken deliberately in 8 checker places and 6 document places (scratch copies), and every break was caught.

<a id="round-2-decisions"></a>
### Decisions recorded before Gate A (decision-only preflight)

| Decision | Value | Owner |
|---|---|---|
| D-14 | Python 3.12, pinned with uv | Learner |
| D-20 | CPU-first PyTorch; CUDA only after a measured slowdown | Learner |
| D-19 | VS Code notebooks on the project uv kernel | Learner |
| D-16 | Workspace stays at `C:\Yash\New-Work\Book RAG\rag_learning`; local git only, no remote; `.gitignore` covers `.env`, PDFs, unclear-licence snapshot text, caches and indexes | Learner |
| P-2 | Agrees to the coaching/progress protocol in 05 | Learner |
| D-06 | v0 chunk units = characters (1000/200), with embedder token counts logged | Coach confirmation |
| D-07 | NumPy exact search for v0–v2; FAISS only in the P5 lab | Coach confirmation |

**Where recorded:** 08 Part 4 and Part 7, BACKBONE §6.

<a id="r-01"></a>
### R-01 (Blocker, closes B-01): decision-entry cycle removed

**Problem.** Gate A required DEC-1a, but four DEC-1a decisions were scheduled for the start of O2, and O2 itself needs Gate A.

**Fix.**
- A **decision-only preflight** (a conversation, no environment created) is explicitly allowed before Gate A. All eight DEC-1a decisions were made there and recorded on 2026-10-08.
- O2 now *implements* these decisions (creates the environment); it does not *make* them.
- Gate A requires only design-time artifacts plus preflight decisions. No Gate A item is produced by O2 or any later lab.
- DEC-1a and P-2 are ticked. DEC-1b (D-06, D-07 confirmed; D-17 re-confirmed now that R-02 passes) and C-1, V-1, V-4, P-1 carry "ready for re-confirmation at Codex re-review 2".

**Where:** 08 Part 7 intro, Gate A row, Gate A section, Part 4 rows; 02 §4 approval-gate paragraph; BACKBONE §3; README status.

**Acceptance:** R-01 7/7 and B-01 5/5 checks pass:
- every item ID is in exactly one gate (A 24, B 7, C 5), and BACKBONE assigns the same items;
- Gate A has no E-, BL-, MX- or DEC-3 items;
- DEC-1a lists exactly the eight decisions, each marked Decided in Part 4;
- DEC-1a and P-2 are ticked;
- no "confirmed at the start of O2" wording remains for these decisions.

The A-02 API-key check at the start of O2 is an environment action, not a Gate A decision, and stays.

<a id="r-02"></a>
### R-02 (Major, M-01): fail-closed binding and page-table integrity

**Problem.** The reference loader ignored `snapshot_manifest_sha256`. It accepted a page table with page 2 shifted by +1, which silently moved a gold label from "d" to "e".

**Fix (06 §5.3 rule 4, §6.1).** Before any gold label is translated, the loader rejects:
- missing required binding fields;
- `snapshot_manifest_sha256` that is not the sha256 of the exact stored manifest bytes;
- any page-table structure break: pages 1..n in order; start 0; end − start = page length; next start = end + `len(page_join)`; last end = `len(doc_text)`; page and document hashes;
- a mismatch with the `snapshot_id` recomputed by the exact recipe.

**Related changes:**
- The recipe line is now unambiguous: `page_join=\n` means a literal backslash + "n".
- The real Corpus D id is **`ea07572562ac`**, computed by the checker executing the documented block.
- Snapshot text storage is stated: page texts are slices of the document text through the page table.
- Both negative tests are in the 06 §9.6 sketch.
- The checker's private serialisation was replaced by the recipe.

**Where:** 06 §5.3, §6.1, §9.6; 08 D-17, V-1, RK-05; BACKBONE §5; 07 H.3 fail-closed note; round-1 spec note.

**Acceptance:** R-02 17/17.
- The real manifest passes `validate_binding`.
- A wrong digest is rejected (3 variants), as is a re-serialised manifest with identical JSON content.
- Every missing field is rejected (4 header, 20 manifest).
- The shifted `["abc","def"]` table is rejected. The round-1 control accepts it and maps the label to "e".
- The valid page-2 [0,1) maps to [4,5) = "d".
- Nine other structural mutations are rejected.

<a id="r-03"></a>
### R-03 (Major, M-06): interval methods by statistic

**Problem.** A blanket "Wilson 95% interval" was applied to the confusion matrix and to Cohen's κ. κ is not a proportion and can be negative.

**Fix.**
- **Confusion matrix:** reported as counts.
- **Binomial rates:** Wilson when units are independent; a cluster bootstrap over answers when several units share an answer.
- **κ:** a paired/cluster bootstrap, or the κ-specific variance (statsmodels `cohens_kappa`).
  - Worked example: 4 balanced items, raters always disagree, p_o = 0, p_e = 0.5, κ = −1.
- **Decision rule (Assumption, provisional):** certify only if the lower 95% bound of failure recall is ≥ 0.70 and the lower 95% bound of κ is ≥ 0.40.
  - κ ≥ 0.6 and recall ≥ 0.8 stay as aspirational targets.
  - The 8/10 example (0.49–0.94) does not certify.

**Where:** 06 §8.4 and §11; 08 D-10, RK-03, V-4; 02 M3 and V4 cards; 04 M3 and V4 rows; BACKBONE §5; round-1 spec note.

**Acceptance:** R-03 11/11.
- κ = −1, with a seeded paired bootstrap interval of [−1.000, 0.000].
- Clustered resampling keeps each answer's units together.
- The lower-bound rule is present.
- A scan finds no clause applying Wilson to κ or to the confusion matrix.

The M-06 numeric checks (8/10 Wilson, 6/6 exact bound) still pass.

<a id="r-04"></a>
### R-04 (Major, M-07): exposure ≠ mastery

**Problem.** `can_unlock` required exposure concepts to be *mastered*, so I-CMP was blocked when I2–I6 were only exposed.

**Fix.**
- **Learner state has two sets:** `mastered` and `exposed`.
- **Unlock rule:**
  - all and any-group requirements are checked against `mastered`;
  - exposure is checked against `exposed ∪ mastered`;
  - gates are checked against passed gates.
- Exposure never substitutes for mastery.
- 05 gains an `exposed_on` column in `concept_tracker.csv`. A column was used rather than a status value, because `exposed` already names the L1 mastery level. 05 §7.1 clarifies the difference, and 07's example tracker rows were updated to 20 fields.

**Where:** 03 §2.1 legend and field notes; 05 §6.1 and §7.1; 07 M.7; `contracts_check.py`.

**Acceptance:** R-04 8/8.
- I-CMP unlocks with I1 mastered and I2–I6 exposed-only.
- It is blocked when any one exposure is missing.
- Exposure never satisfies an all or any-group requirement.
- K1 is reachable with I2–I6 exposed-only and no A\*/S\* concepts.

All 22 M-07 checks still pass.

<a id="r-05"></a>
### R-05 (Minor, with R-02): two decoders, one stated rule

**Problem.** Chunk-derived segments count the virtual page-join character towards the preceding page, while the gold decoder rejected any offset beyond the physical page text. The round-trip check bypassed both decoders.

**Fix.**
- `gold_to_doc`: authored gold segments must lie inside the physical page text.
- `chunk_segment_to_doc`: chunk-derived segments may end at `len(page_text) + 1` on non-last pages.
- Coverage is always computed in document offsets.

**Where:** 06 §2.3 and §6.4; 07 H.3 note (code unchanged).

**Acceptance:** R-05 8/8.
- `["abc","def"]`: the whole-document chunk's page-1 segment [0,4) is accepted by the chunk decoder and rejected by the gold decoder, which accepts [0,3).
- The 2,000-span round-trip and all 189 real chunks go through the public decoders.

<a id="r-06"></a>
### R-06 (Minor, B-01): Corpus H timing

**Fix.** Everywhere now says "Corpus T chosen and frozen (with snapshot) before Phase 3; Corpus H chosen and frozen before K1".

**Where:** BACKBONE §3 Gate B row; round-1 spec (inline "[corrected in round 2, R-06]" notes). 08 was already correct.

**Acceptance:** R-06 2/2.

<a id="r-07"></a>
### R-07 (Minor, M-05): order-insensitive qid comparison

**Fix.** Comparison metadata stores qids as a canonical sorted list, and the guard compares sets.

**Where:** 06 §9.3 sentence; `contracts_check.py`.

**Acceptance:** R-07 5/5. Shuffled qid order is accepted; different sets are rejected.

### Round-2 residual edits and known non-blocking items

- **Orchestrator edits** ([`round2_residual_edits.py`](../sources/verification/corrections/round2_residual_edits.py)) in 06:
  - real `snapshot_id`;
  - recipe comment;
  - storage rule;
  - two negative test sketches in §9.6;
  - escaped pipes in the Precision@k and Context-precision rows of the §7.3 metric table, which split those rows (a pre-existing rendering bug in an M-02 table).
- **Historical round-1 lines** in this log and in the round-1 spec now carry "corrected in round 2" notes rather than being rewritten.
- **Still deferred**, as in round 1: minor findings m-01 to m-08, nits n-01 and n-02, and the trim proposal. 06's loose "Corpus T frozen … by v1.1" phrasing does not contradict DEC-3's "before Phase 3" and is left as is.

### Request for re-review 2

Please re-review **only** R-01 to R-07 (sections above) and the readiness items they unblock (C-1, DEC-1b, V-1, V-4, P-1 in 08 Part 7). Instructions are in [CODEX_REREVIEW2_BRIEF.md](CODEX_REREVIEW2_BRIEF.md).


---

<a id="round-3"></a>
## Round 3: Codex re-review 2, Gate A granted with fixes

**Input:** [CODEX_REREVIEW2_2026-10-08.md](CODEX_REREVIEW2_2026-10-08.md). Verdict: **GATE A GRANTED WITH FIXES**.
- **Resolved:** R-01, R-03, R-04, R-05, R-06 and R-07.
- **Partially resolved:** R-02, now carrying a Minor defect only.
- **No Blocker or Major findings remain.**

**What Codex reproduced independently:**
- 142/142 checks pass, and the 13 lesson tests pass.
- Its own negative probes: wrong digest, shifted table, exposed-only I-CMP, shuffled qids and κ = −1.
- The documented snapshot recipe gives `ea07572562ac`.

<a id="r2-01"></a>
### R2-01 (Minor, R-02): `cleaning.steps` was not required

**Problem.** `validate_binding` accepted a manifest without `cleaning.steps` (digest recomputed). The missing-field test did not cover nested fields.

**Fix** ([`round3_r2_fixes.py`](../sources/verification/corrections/round3_r2_fixes.py)):
- `CLEANING_REQUIRED = ("version", "steps")` is now enforced.
- The missing-field test now loops over every nested `parser.*` and `cleaning.*` field as well: 26 fields, each with a recomputed digest.
- Two new checks: removing `cleaning.steps` raises `BindingError` before translation, and a valid `{version: none, steps: []}` still passes.

**Evidence:**
- A mutation run that restores the old validator makes both checks FAIL (`['cleaning.steps']`).
- The fixed version passes.

<a id="r2-02"></a>
### R2-02 (Minor, R-03): undefined κ bootstrap crashed

**Problem.** `kappa_bootstrap([1]*60, [1]*60)` raised `IndexError` because every resample was undefined.

**Fix.** If the point κ is undefined, or no defined resamples remain, the helper returns an explicit `(None, None, n_undefined)`. The documented fallback then applies: no certification, and human scoring continues. A constant-label check was added (2000/2000 undefined, no exception).

**Evidence:**
- A mutation run with the guard removed crashes on the old IndexError.
- The κ = −1 and answer-cluster checks still pass.

### Result and records

- **Acceptance suite:** **145 passed, 0 failed** (adds R2-01 2/2 and R2-02 1/1) → [`contracts_check.out.txt`](../sources/verification/corrections/contracts_check.out.txt).
- **08 Part 7:**
  - Gate A is marked **GRANTED WITH FIXES (2026-10-08)**.
  - All 24 Gate A items are ticked. C-1, DEC-1b, V-1, V-2, V-4 and P-1 carry Codex re-review 2 annotations.
  - Script: [`round3_record_gate_a.py`](../sources/verification/corrections/round3_record_gate_a.py).
- **Gates B and C remain ungranted.** Their items are produced by the O2/C6 labs and by measurement work.
- **Gate A permits:** O1–O3, P1–P7 labs, and C1–C6 implementation (building v0).
- **Still deferred:** the round-1 minor and nit backlog (m-01 to m-08, n-01, n-02), the trim proposal, and the offline coach kit.
