# Codex re-review 2: R-01–R-07 corrections

**Date:** 2026-10-08 (Asia/Calcutta)  
**Scope:** Round-2 corrections and the Gate A items they unblock  
**Result:** Six findings RESOLVED; R-02 PARTIALLY resolved, with one remaining Minor defect  
**Gate A:** **GRANTED WITH FIXES**

The original decision-entry cycle and all five requested counterexamples are repaired. The requested suite reports **142 passed, 0 failed**; the exact extracted lesson tests report **13 passed**. Independently extracting Corpus D and executing the documented snapshot recipe gives **`ea07572562ac`**.

There are no remaining Blocker or Major findings in this scoped review. Two Minor defects in the new reference helpers remain: incomplete validation of a nested manifest field and an unhandled undefined-κ bootstrap case. Design work may proceed under Gate A with those targeted fixes carried forward. Fix the manifest validator before using it to accept datasets, and the bootstrap guard before using that helper for agreement reports. Gates B and C remain separate, ungranted exit gates.

## 1. Scope and evidence

Read the [Round-2 corrections log](C:/Yash/New-Work/RAG/rag_learning/reviews/CORRECTIONS_LOG_2026-10-08.md:339) and [round-2 spec](C:/Yash/New-Work/RAG/rag_learning/reviews/CORRECTIONS_SPEC_R2_2026-10-08.md) first. Compared each change with the Correction/Acceptance text in [re-review §3](C:/Yash/New-Work/RAG/rag_learning/reviews/CODEX_REREVIEW_2026-10-08.md:61), then inspected the revision-marked sections and relevant helper implementations.

This report does not re-review the original minor/nit backlog, the trim proposal, book/repo citations, or untouched lesson content. Previously accepted evidence is carried forward where indicated; neither earlier score is changed.

Execution used Python **3.12.8**, PyMuPDF **1.26.7** and the installed pytest **8.4.2**. The upstream checkout remained clean at **`009adba2be1bef49780ef73b6dd3c18fd24b035b`**. No API calls, environment setup or learner experiments were performed.

All **68 pre-existing workspace files** were fingerprinted before execution. They remain unchanged. Only this report was added. Exact lesson blocks were written to a temporary directory outside the workspace for pytest and removed afterward.

## 2. Verdict per finding

The severity column identifies each finding's severity in the previous re-review. Remaining defects are ranked separately in §5.

| Finding | Previous severity | Verdict | Evidence against Correction/Acceptance |
|---|---|---|---|
| **R-01** | Blocker | **RESOLVED** | [08 Part 7](C:/Yash/New-Work/RAG/rag_learning/08_GAP_ANALYSIS_AND_DECISIONS.md:630), [02 §4](C:/Yash/New-Work/RAG/rag_learning/02_RAG_MASTER_LEARNING_PLAN.md:1105) and [BACKBONE §3](C:/Yash/New-Work/RAG/rag_learning/curriculum/CURRICULUM_BACKBONE.md:144) explicitly allow decision-only preflight before A. O2 implements the decisions afterward. All eight DEC-1a choices are dated in Part 4; DEC-1a and P-2 have dated learner records. D-06/D-07 now have coach confirmations. No remaining O2 decision-entry prerequisite cycle was found. |
| **R-02** | Major | **PARTIALLY** | [06 §5.3](C:/Yash/New-Work/RAG/rag_learning/06_RAG_PROJECT_AND_EVALUATION_PLAN.md:836), §6.1 and [checker validate_binding](C:/Yash/New-Work/RAG/rag_learning/sources/verification/corrections/contracts_check.py:190) now enforce exact-byte digest, page structure, page/document hashes and recomputed ID before gold translation. Both original negatives are rejected; valid page 2 maps to “d.” The canonical ID is reproduced. However, “every manifest field” is not fully enforced: removing `cleaning.steps` is accepted with a correctly recomputed digest. See R2-01, **Minor**, below. The original coordinate-corruption mechanism is repaired. |
| **R-03** | Major | **RESOLVED** | [06 §8.4](C:/Yash/New-Work/RAG/rag_learning/06_RAG_PROJECT_AND_EVALUATION_PLAN.md:1176) now reports matrix counts, Wilson intervals for independent binomial rates, answer-cluster bootstrap for dependent units, and paired/cluster bootstrap or κ-specific variance for κ. D-10/RK-03/V-4, BACKBONE §5 and the revised 02/04 summaries agree. The explicitly provisional certification rule uses lower bounds: recall ≥0.70 and κ ≥0.40. The −1 example reproduces with bootstrap interval [−1,0]; the Wilson proportion examples still reproduce. R2-02 is a defensive helper defect, not a recurrence of Wilson-on-κ. |
| **R-04** | Major | **RESOLVED** | [03 §2.1](C:/Yash/New-Work/RAG/rag_learning/03_RAG_CONCEPT_DEPENDENCY_MAP.md:465) and [can_unlock](C:/Yash/New-Work/RAG/rag_learning/sources/verification/corrections/contracts_check.py:661) use separate mastery and exposure sets. I1 mastered plus I2–I6 exposed-only unlocks I-CMP. Missing exposure blocks; exposed I1 cannot substitute for mastered I1; all/any checks remain mastery-based. K1 is reachable with no A*/S* concepts and no I2–I6 mastery. [05 §6.1/§7.1](C:/Yash/New-Work/RAG/rag_learning/05_LEARNING_AND_RETENTION_SYSTEM.md:438) records mechanism exposure separately as `exposed_on`, with trace/demo evidence, and distinguishes it from L1 status. Both revised 07 M.7 rows parse into the correct 20 columns. |
| **R-05** | Minor | **RESOLVED** | [06 §2.3](C:/Yash/New-Work/RAG/rag_learning/06_RAG_PROJECT_AND_EVALUATION_PLAN.md:230), §6.4 and [07 H.3](C:/Yash/New-Work/RAG/rag_learning/07_SAMPLE_LESSON.md:1050) distinguish physical gold bounds from chunk segments including the virtual join. For [“abc”,“def”], the chunk decoder accepts p1 [0,4); gold rejects it and accepts [0,3). The suite's 2,000 random spans and 189 actual chunks now round-trip through the public decoder, rather than raw addition. |
| **R-06** | Minor | **RESOLVED** | [BACKBONE §3 Gate B](C:/Yash/New-Work/RAG/rag_learning/curriculum/CURRICULUM_BACKBONE.md:149) agrees with 08 DEC-3: T frozen before Phase 3; H frozen before K1. The [round-1 spec §B-01/§L](C:/Yash/New-Work/RAG/rag_learning/reviews/CORRECTIONS_SPEC_2026-10-08.md:21) keeps the historical wording with explicit superseding round-2 timing notes. No need to select H before design approval. |
| **R-07** | Minor | **RESOLVED** | [06 §9.3](C:/Yash/New-Work/RAG/rag_learning/06_RAG_PROJECT_AND_EVALUATION_PLAN.md:1298) documents canonical sorted qids and set comparison. [make_comparison_meta/comparison_keys_match](C:/Yash/New-Work/RAG/rag_learning/sources/verification/corrections/contracts_check.py:462) implement that rule. Shuffled qid metadata is accepted; a changed set is rejected; construction sorts qids and rejects duplicates/missing comparison keys. |

The remaining partial status for R-02 is narrowly about the full required-field acceptance contract. It does not preserve the former Major severity after its two harmful counterexamples have been fixed.

## 3. Executable verification

### Requested suite

Ran the exact requested command:

```powershell
python -I sources/verification/corrections/contracts_check.py "C:\Yash\New-Work\RAG\upstream\RAG_Techniques\data\Understanding_Climate_Change.pdf"
```

**Result:** exit 0; **142 passed, 0 failed, 142 checks**.

| Check group | Passed |
|---|---:|
| M-01 / R-02 / R-05 | 15 / 17 / 8 |
| M-02 / M-03 / M-04 | 19 / 2 / 9 |
| M-05 / R-07 | 9 / 5 |
| M-06 / R-03 | 3 / 11 |
| M-07 / R-04 | 22 / 8 |
| B-01 / R-01 / R-06 | 5 / 7 / 2 |

Passing a check group is not a proof that every allowed input was tested; R2-01 illustrates the distinction.

### Independent repetition of the requested probes

Loaded the checker functions in memory without invoking its main test runner. Constructed fresh fixtures and invoked the helpers directly.

| Probe | Observed result |
|---|---|
| Wrong `snapshot_manifest_sha256="deliberately-wrong"` | **BindingError**, before gold conversion. |
| [“abc”,“def”], page 2 start/end both shifted +1, with digest recomputed over the mutated manifest | **BindingError:** start differs from previous end + page join. Updating the digest cannot bypass structural validation. |
| Valid page-2 [0,1) | Document [4,5), text **“d”**. |
| I-CMP: mastered={I1}, exposed={I2,I3,I4,I5,I6}, Gate 3→4 passed | **True**. Removing I4 exposure gives False; putting I1 only in exposed also gives False. |
| K1 reachability | **True**, with 31 prerequisite concepts mastered, I2–I6 exposed-only, and no A*/S* concept in either set. Each mastery step is checked through the unlock rule. |
| Identical metadata with qids [q1,q2] versus [q2,q1] | **True**. Replacing q2 with q3 raises **ValueError**. |
| Human=[1,1,0,0], judge=[0,0,1,1] | κ=**−1.0**; paired bootstrap seed 0, 2,000 resamples: **[−1.0,0.0]**, zero undefined resamples. |
| Separate gold/chunk decoders, p1 [0,4) | Chunk: **(0,4)**. Gold: **ValueError**. Gold p1 [0,3): **(0,3)**. |

For the κ example, observed agreement is 0 and expected agreement is 0.5; (0−0.5)/(1−0.5)=−1. The four-item bootstrap is a demonstration of the method, not judge certification.

### Exact 07 H.1 + H.3 pytest

Extracted the H.1 implementation into `ragkit/_core.py`, H.3 implementation into `ragkit/chunking.py`, and the unchanged H.3 test block into a temporary test module. Added only an empty package initializer.

Ran with `python -I -B -m pytest -q -p no:cacheprovider`, third-party plugin autoload disabled and bytecode disabled.

**Result:** **13 passed in 0.07s**, exit 0. Temporary extraction removed.

Source hashes of the extracted implementation blocks:

- H.1: `389551b7aae03d98d5be8de5de308913197abb727fc8e4e1f0ca1717b0af41c7`
- H.3: `d381cfa528d1ec1ccddf9cd857844c9c54865643479fc1e5c1c63ca8b39a8483`

This repeats the requested lesson tests, not the entire original lesson review.

### Inspection of what the new checks assert

- The digest-order test uses deliberately invalid gold. A valid binding reaches the gold decoder and raises ValueError; the wrong digest instead raises BindingError, which is not a ValueError subclass. This genuinely tests validation **before** translation.
- The shifted-table test recomputes the exact-byte digest after mutation. Its failure therefore genuinely tests page structure, not merely stale manifest bytes.
- The round-trip test calls `chunk_segment_to_doc`; it also checks gold acceptance/rejection at join boundaries. This repairs the previous arithmetic-only assurance.
- The exposure path checks separate state sets and builds K1 prerequisite mastery step by step. It no longer hides optional mastery in one broad set.
- Gate checks parse actual 08 sections and compare BACKBONE assignments: **24 Gate A, 7 Gate B, 5 Gate C items**, each assigned exactly once.
- The missing-manifest-field test loops over top-level, document and row fields. It does **not** include every nested cleaning field, which explains R2-01 despite 142 passing checks.
- The κ tests exercise the negative and clustered examples, but not a case with no defined bootstrap draws, R2-02.

## 4. Independent snapshot-ID reproduction

Read the [Climate PDF](C:/Yash/New-Work/RAG/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf) directly with PyMuPDF 1.26.7 and `page.get_text()`, options {}, no cleaning. Joined the 33 extracted page strings with one newline.

Computed:

- PDF SHA-256: `1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669`
- Document length: **72,593 characters**
- Document SHA-256: `5106772efa77003b0d6c79bc1a429b8dacf244d9556f412bae1c4fe6bc7368c6`

Independently extracted and executed the exact Python block from [06 §5.3](C:/Yash/New-Work/RAG/rag_learning/06_RAG_PROJECT_AND_EVALUATION_PLAN.md:812), supplying `backend="pymupdf"`, `version="1.26.7"`, `options={}`, `cleaning_version="none"` and the actual document hash keyed by `climate`.

**Result: `ea07572562ac`, exactly as documented.** The recipe's page-join hash token contains a literal backslash followed by n, whereas the actual text join is a newline. The revised comment makes that distinction explicit.

## 5. Remaining/new findings

### R2-01 — Minor: missing cleaning.steps is accepted

**Related finding:** R-02.  
**Evidence:** [06 §5.3 manifest and required-field rule](C:/Yash/New-Work/RAG/rag_learning/06_RAG_PROJECT_AND_EVALUATION_PLAN.md:789); [validate_binding](C:/Yash/New-Work/RAG/rag_learning/sources/verification/corrections/contracts_check.py:207); missing-field tests L852–868.

The normative contract requires every field in the displayed manifest, including `cleaning.steps`. The implementation requires `cleaning.version` but does not require `cleaning.steps`. Its “20 fields” negative test omits that nested field.

**Executed reproduction:** Build a valid [“abc”,“def”] fixture; delete `manifest["cleaning"]["steps"]`; serialize it; recompute the header's exact-byte digest. `validate_binding` **accepts** it.

The original wrong-digest/shifted-coordinate problems are fixed. This remaining defect loses required cleaning provenance and overstates schema-validation completeness; this probe does not shift gold or bypass a mismatched digest. It is **Minor**, not a continuing Major coordinate-integrity failure.

**Fix/acceptance:** Require `cleaning.steps` along with cleaning.version and test its removal using a matching digest. Include the nested parser/cleaning fields in the missing-field test inventory so its completeness claim matches the normative schema. Missing cleaning.steps must raise BindingError before translation; valid “none/[]” manifests must still pass.

**Timing:** Fix before relying on this acceptance loader for dataset validation. O1/O2 design and environment work need not wait.

### R2-02 — Minor: undefined κ bootstrap raises an unhandled IndexError

**Related finding:** new R-03 helper.  
**Evidence:** [cohens_kappa/kappa_bootstrap](C:/Yash/New-Work/RAG/rag_learning/sources/verification/corrections/contracts_check.py:538).

The point helper correctly returns None when expected agreement is 1. The bootstrap counts undefined draws and discards them, but indexes the remaining list without checking whether it is empty.

**Executed reproduction:** `kappa_bootstrap([1]*60, [1]*60, n_boot=2000, seed=0)` raises **IndexError: list index out of range**. All sampled label pairs are constant and identical, so κ is undefined in every draw.

This example does not meet the documented ≥30 failure/≥30 non-failure certification composition. It is a defensive helper/fallback defect, not evidence of false certification or a reason to reject the repaired statistical design. The requested κ=−1 case works.

**Fix/acceptance:** If the point statistic is undefined, or no defined resamples remain, return an explicit undefined result or raise a descriptive validation error. Preserve/report the undefined-resample count and follow the existing human-scoring/no-certification fallback. Add a constant-label test; retain the negative-κ and answer-cluster tests.

**Timing:** Fix before using this helper for agreement reports.

No additional Blocker, Major or Nit introduced by the inspected round-2 changes was found. The tracker-column edits and revised interval summaries remain consistent in the checked sections.

## 6. Gate A re-evaluation

These approvals are recorded **in this report**, without editing 08. Learner/coach decisions are accepted as dated documentary records in the supplied log/spec and Part 4; I did not independently access the originating conversation.

| Gate A item | Re-review decision | Basis and limits |
|---|---|---|
| **C-1** | **Confirmed within this correction scope** | The corrected exposure/mastery registry, gate semantics and project references are consistent; 02 ancestor/typed-gate checks pass and 03 remains the authoritative unlock registry. This is not a new certificate that every untouched display row “matches exactly”; earlier minor display/elective wording issues remain in the excluded backlog. |
| **DEC-1a** | **Confirmed** | All eight choices are recorded before Gate A, with date/owner; O2 implements them. |
| **DEC-1b** | **Confirmed for design, with R2-01 fix** | D-06/D-07 have dated coach confirmation. **D-17 reviewer confirmation: Codex, 2026-10-08** — approve frozen snapshot/document offsets, exact-byte binding, canonical ID and separate decoders as written; require the nested-field validator fix before dataset acceptance. |
| **V-1** | **Specification approved; reference acceptance has one Minor fix** | The required integrity rules are explicit and both harmful negatives now fail closed. R2-01 remains for complete schema enforcement. |
| **V-2** | **Carry forward confirmed** | M-02 was resolved in the previous review. No new metric-contract regression was found in the relevant changed material; no fresh full review performed. |
| **V-4** | **Confirmed at design level** | Interval method, clustering, disjoint sets, lower-bound rule, exact comparison keys and qid alignment are documented. R2-02 is a helper guard to fix before agreement reporting. |
| **P-1** | **Exemplar approved for the corrected design, with targeted helper fixes** | H.1/H.3 13 pytest cases pass; public decoder round-trips pass; shared snapshot/coordinate design is accepted. Carry forward earlier evidence and retained UNVERIFIED markings; this does not claim every untouched block was freshly executed or reopen the lesson's minor backlog. |
| **P-2** | **Confirmed** | Explicit dated learner agreement is recorded; no inference from the review request is needed. |
| S-1…S-6; C-2…C-5; DEC-2; V-3; P-3; R-1…R-3 | **Carry forward their existing narrow approvals** | Sixteen items outside the reopened correction scope. Source audits, scope/note decisions, empty-results policy and existing risk controls are not re-audited here. |

**Gate A may proceed with fixes.** It permits O1–O3, P1–P7 and C1–C6 implementation. The two Minor helper fixes above should be made alongside that work, before their affected validation/reporting paths are used. They do not require a new corpus, a certified judge or a working v0 in advance.

**Gate B remains ungranted:** the project environment, provider/model-limit smoke checks, working v0 and Corpus T exit evidence still belong to their producing labs. **Gate C remains ungranted:** human-verified labels, recorded splits, deterministic learner harness, human pilot and failure traces remain measurement outputs. The 142 checks and 13 pytest tests are reference verification, not learner mastery or those later artifacts.

The prior B-01 and M-07 blockers/majors can now close. M-01's original integrity counterexamples are closed, with R2-01 retained as a Minor acceptance gap. M-06's statistical-method error is closed. M-02/M-03/M-04/M-05 stay resolved.

**GRANTED WITH FIXES**
