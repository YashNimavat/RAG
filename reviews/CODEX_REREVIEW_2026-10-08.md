# Codex re-review: P0/P1 corrections

**Date:** 2026-10-08 (Asia/Calcutta)  
**Scope:** B-01 and M-01–M-07 only  
**Result:** Four findings RESOLVED; four PARTIALLY RESOLVED  
**Approval gate A:** **NOT GRANTED**

The corrections substantially improve the design. Both requested test runs pass: **80 contract checks, 0 failures**, and **13 extracted H.3 pytest cases passed**. The corrected seed spans are semantically sufficient.

Those results do not establish that all eight findings are closed. A smaller approval-entry cycle remains; the reference snapshot validator does not enforce the full integrity contract; the calibration rewrite assigns the wrong interval method to κ; and the unlock helper conflates exposure with mastery. These are specific remaining corrections, not a request to implement the future RAG system.

This review does **not** revisit the original minor/nit findings, trimming, or untouched material. New minor issues below arise in the correction artifacts themselves. The earlier 84/100 score is not recalculated.

## 1. Evidence and method

Read the corrections log and canonical spec first, then the revised sections and their dependent contracts in 02, 03, 04, 06, 07, 08, BACKBONE and README. Compared the changes with the original report's §3 acceptance criteria. Inspected the acceptance script, including its source-level checks, conversion tests, scoring functions, bootstrap and unlock helper.

Execution environment: Python **3.12.8**, PyMuPDF **1.26.7**, NumPy **2.3.3**. Upstream remained clean at:

`009adba2be1bef49780ef73b6dd3c18fd24b035b`

Climate PDF: 33 pages, 206,372 bytes, SHA-256:

`1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669`

All 64 pre-existing workspace files were fingerprinted before the checks. The only persistent file authored by this review is this report. H.1/H.3/test blocks were extracted unchanged into a temporary directory outside the workspace and removed after pytest. No provider API, package installation, credential inspection, or learner experiment was performed.

### Requested test runs

1. Ran the requested command:

   `python -I sources/verification/corrections/contracts_check.py "<climate PDF path>"`

   Result: **80 passed, 0 failed, 80 checks**.

2. Extracted the first Python block of 07 H.1 into `ragkit/_core.py`, the implementation block of H.3 into `ragkit/chunking.py`, and the unchanged test block into a temporary test module. Added only the package initializer needed for imports.

   Ran Python 3.12.8 with `-I -B -m pytest -q -p no:cacheprovider`, automatic third-party plugins disabled.

   Result: **13 passed in 0.09s**, exit code 0.

3. Executed additional small negative probes against the supplied reference helpers, without modifying them. Their outcomes are recorded in §3.

The 80-check suite does not read 08 and therefore does not establish B-01 or Gate A readiness. Its M-06 checks verify the three quoted interval numbers, not the complete calibration methodology.

## 2. Verdict against each original finding

| Finding | Verdict | Acceptance evidence and remaining limitation |
|---|---|---|
| **B-01** | **PARTIALLY RESOLVED** | 08 Part 7, 02 §4 and BACKBONE §3 now separate design, environment/baseline and measurement gates. Environment/evaluation artifacts no longer precede their producing work. However, Gate A remains a precondition for O2 while DEC-1a requires decisions explicitly scheduled for the start of O2. See R-01. |
| **M-01** | **PARTIALLY RESOLVED** | 06 §§2.3/5.3/6.1/6.4/9.6 and 07 H.3 now specify snapshots, hashes, canonical document offsets and derived page segments. The original page-2/cross-page, changed-page-text and changed-snapshot counterexamples pass. The reference loader nevertheless accepts a wrong manifest hash and a structurally shifted page table; its round-trip evidence bypasses that loader's segment bounds. The written contract is largely repaired; its integrity acceptance evidence is incomplete. See R-02 and R-05. |
| **M-02** | **RESOLVED** | 06 §§6.1/7.2/7.3, 03's diagnosis and 07 Part I distinguish complete evidence from first evidence. AND-groups/OR-alternatives and whitespace-only sufficiency are required. Actual D-005 half spans give CE=0 despite Hit=1; one required group gives CE=0/Group-Recall=0.5; either D-004 alternative and jointly covering chunks pass. Final-context CE is now required for context changes. |
| **M-03** | **RESOLVED** | 06 §6.7 uses the requested longer spans, verified directly against the PDF. The acronym expansion, named antecedent and full convention identity are present. Seeds remain llm-draft with unassigned splits; scoring rejects those splits. Semantic results are in §4. |
| **M-04** | **RESOLVED** | 07 H.3 and 06 §§2.2–2.4 namespace IDs by snapshot and key embeddings by provider/model/revision/input type/preprocessing/text. Exact code and 13 pytest cases pass. AAAA/BBBB no longer share cache keys, even when an old snapshot ID is deliberately reused; query/document modes differ. |
| **M-05** | **RESOLVED** | 06 §§6.3/6.6/7.6/9.2–9.4 and 07 I.1 require exact comparison identity, qid alignment, group splitting/bootstrap, dev selection, logged test touches and reserved holdout. The extracted bootstrap rejects unequal qid sets and is invariant to dict insertion order; clustered variants stay together. The reference metadata comparator has a new minor order-normalization issue, R-07; the written design and bootstrap correction are accepted. |
| **M-06** | **PARTIALLY RESOLVED** | 06 §§8.4–8.5, 02 Gate 3→4 and 08 D-10 separate pilot/certification, specify labeling units, disjoint sets/failure counts, challenge outputs, human fallback and repeat-judge variance. The numerical examples reproduce. But 06 §8.4 assigns Wilson intervals to κ and the confusion matrix as well as recall. This is a new statistical error in the correction. See R-03. |
| **M-07** | **PARTIALLY RESOLVED** | 03 §2.1 correctly records all/any/gate/exposure/advice. OR-groups reject zero members, S2 requires Gate 3→4, hard edges are acyclic and K1 no longer depends on D3 or A*/S* concept IDs. However, the checker implements exposure using its mastered set, so it cannot validate the promised exposed-but-not-mastered path. See R-04. |

“RESOLVED” refers to this design-stage correction and its original counterexamples, not a production implementation or learner mastery.

## 3. Remaining issues and regressions introduced by the corrections

### R-01 — Blocker: Gate A still depends on entering O2

**Applies to:** B-01.  
**Evidence:** 08 Part 7 L626/L636 makes Gate A the precondition for Phase 0/O2; DEC-1a L654 states D-14/D-16/D-19/D-20 are confirmed at the start of O2. The corrections spec §B-01/§L repeats this ordering. 02 §4 L1102 calls Gate A the precondition for Phase 0.

**Problem:** The original environment-artifact cycle is removed, but a decision-entry cycle remains. DEC-1a must pass before O2; O2 is where DEC-1a's outstanding decisions are completed. The statement at 08 L622 that no gate requires something produced by its permitted work is therefore not yet true.

**Correction:** Either explicitly permit a **decision-only preflight before Gate A** and record its outcomes before granting A, or move those O2-entry confirmations to a prerequisite for environment creation under Gate B. Distinguish “start O2's decision discussion” from “create the environment.” Do not require a later lab to supply a precondition for starting that lab.

DEC-1a is also factually pending, independent of the ordering defect. This review does not choose the learner's notebook front end, versioning preference or compute setup.

### R-02 — Major: the acceptance loader does not enforce manifest identity or page-table integrity

**Applies to:** M-01.  
**Evidence:** `contracts_check.py` L142–152, L160–164, L180–200 and L576; 06 §6.1 L843; 08 V-1 L659.

The written header includes `snapshot_manifest_sha256`, but the reference loader checks only snapshot-ID equality and page hashes/lengths. It never inspects that header hash. The main tests even supply a header without it.

**Executed negative probes:**

- Supplying `snapshot_manifest_sha256="deliberately-wrong"` still loads the item.
- With pages `["abc","def"]`, shifting page 2's document start **and** end by one preserves its text hash and length. The validator accepts this altered table and maps page-2 [0,1) to document **[5,6)** instead of **[4,5)**. The actual document is `"abc\ndef"`: the label points to “e” rather than “d.”

This does not refute the legitimate passing page-text tamper test. It demonstrates a different integrity boundary that remains unchecked. The report is not asking for future production ragkit code; the problem is in the correction's supplied acceptance implementation and its claim to enforce the documented binding.

**Correction:**

1. Require and verify the dataset's manifest digest against a defined canonical serialization or the exact stored manifest bytes.
2. Verify ordered page numbers, contiguous starts/end lengths with the defined join, total document hash and the exact canonical snapshot-ID recipe.
3. Reject missing required binding fields and metadata mismatches before translating gold.
4. Add the two negative probes above to the acceptance suite. Align the checker’s snapshot serialization with 06 §5.3; the log acknowledges that they currently differ.

**Acceptance:** Neither a wrong digest nor a shifted table can silently change gold coordinates. Existing valid page-2/cross-page cases continue to pass.

### R-03 — Major: Wilson is not a confidence interval for Cohen's κ

**Applies to:** M-06.  
**Evidence:** 06 §8.4 L1158 says the confusion matrix, Cohen's κ and failure-class recall should each have a denominator and a Wilson interval. The rewritten summaries/spec repeat a broad Wilson requirement.

Wilson intervals apply to binomial **proportions**, such as failure recall, not directly to a chance-corrected agreement statistic. Cohen's κ can be negative; for two balanced raters that always disagree, κ=-1. It is not a successes/trials proportion. Nor does a confusion matrix have one scalar Wilson interval. The distinction is supported by [NIST's proportion-interval description](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm) and the [statsmodels κ API, which computes κ-specific variance](https://www.statsmodels.org/stable/generated/statsmodels.stats.inter_rater.cohens_kappa.html).

The 8/10 Wilson interval **0.4902–0.9433** and 6/6 exact lower bound **0.5407** are correct. Passing those three numerical checks does not validate applying Wilson to κ.

**Correction:** Report the confusion matrix as counts. Use Wilson for defined binomial rates when its sampling assumptions hold. Give κ a κ-specific variance-based interval or a justified bootstrap of paired rater labels. Where several claims/citations come from one answer, preserve that clustering when estimating uncertainty. State the threshold decision rule explicitly, such as which lower confidence bound must meet the provisional operating target. Keep human fallback, disjoint pilot/validation and the deferred judge policy.

**Acceptance:** A negative-κ example is handled with a valid agreement interval; no rule treats κ as a binomial proportion. Proportion examples still reproduce.

### R-04 — Major: exposure is implemented as mastery in the unlock checker

**Applies to:** M-07.  
**Evidence:** 03 §2.1 L433/L464 says I-CMP requires mechanism exposure to I2–I6, not implementation/mastery. In `contracts_check.py` L474–477, `can_unlock` tests `requires_exposure` against the same `mastered` set as `requires_all`.

**Executed counterexample:** Gate 3→4 passed, I1 mastered, I2–I6 exposed but not mastered. The helper returns **False** for I-CMP. It returns True only after those exposure IDs are inserted into the mastered set.

That conflation is absent from the document’s intended policy but present in its executable verifier. It can force optional advanced concepts to be mastered before an essential comparison. The K1 test uses a very broad mastered set, so it does not expose this distinction.

**Correction:** Pass separate mastery and exposure state to the helper, or use typed statuses. For example, `requires_all`/any-groups check mastery, while exposure accepts the exposed-or-mastered set. Add tests for:

- I1 mastered + I2–I6 exposed-only ⇒ I-CMP unlocked.
- One required exposure missing ⇒ I-CMP blocked.
- Exposure to an all/any prerequisite alone does not substitute for mastery.
- K1 is reachable with those optional concepts exposed where required, rather than all counted as mastered.

**Acceptance:** Keep the already-passing OR/gate/cycle tests and validate both kinds of learner state separately.

### R-05 — Minor: derived chunk segments and gold segment bounds use different page-end rules

**Applies to:** the new M-01 representation; not the previous minor findings.  
**Evidence:** 07 H.3 L993–1001/L1049 assigns the synthetic page-join newline to the preceding page. The reference `Snapshot.to_doc` L160–164 accepts only offsets within the actual extracted page length. The 2,000-span round-trip check L543–550 uses arithmetic instead of that converter.

For `["abc","def"]`, a whole-document chunk produces page 1 [0,4), including the virtual join; the gold converter rejects it because page 1 has three characters.

The virtual-join convention can be valid. However, chunk-derived segments and authored gold segments are not currently interchangeable through the same conversion API.

**Correction:** Explicitly distinguish their bounds/decoders, or represent joins separately and keep all page-relative segments within physical page text. Test conversion through the chosen public decoder at a page boundary, not only unchecked addition.

This clarification alone is not a Gate A blocker; it should accompany R-02's conversion/manifest repair.

### R-06 — Minor: Corpus H timing still conflicts in the new gate descriptions

**Applies to:** B-01's revised gate tables.  
**Evidence:** 08 DEC-3 L687 defers H until K1, consistent with the corrections log's residual alignment. BACKBONE §3 L147 and corrections spec §B-01 still place “Corpus T/H chosen, frozen” at the C6 exit needed before Phase 3.

08 declares its item-by-item gate table authoritative, so the intended later H timing is recoverable. The other gate views should nevertheless agree.

**Correction:** Say “T before Phase 3; H before K1” in the spec and BACKBONE too. No need to choose H now.

### R-07 — Minor: qid metadata equality is order-sensitive

**Applies to:** M-05's new reference helper.  
**Evidence:** `contracts_check.py` L321–326 compares `ra["qids"] != rb["qids"]` directly. A probe with identical hashes/labels/split/scorer and qid tuples `("q1","q2")` versus `("q2","q1")` raises `ValueError: comparison key differs: qids`.

The actual extracted bootstrap correctly aligns values by qid. This is an unnecessary rejection in the metadata guard, not a demonstrated miscomputed effect or data leak.

**Correction:** Compare validated qid sets, or require canonical sorted qids in the metadata and enforce that at construction. Add a shuffled-metadata case alongside the existing shuffled-value case.

## 4. Corrected seed spans: semantic spot-check

All three requested offsets match PyMuPDF 1.26.7 exactly. Corpus D's extracted document has 72,593 characters and hash:

`5106772efa77003b0d6c79bc1a429b8dacf244d9556f412bae1c4fe6bc7368c6`

| Seed/span | Direct PDF evidence | Verdict |
|---|---|---|
| D-004 p.23 [1437,1566) | Includes the Direct Air Capture (DAC) heading and states that DAC removes CO2 from the atmosphere, enabling negative emissions. | Sufficient alternative for both acronym expansion and function. The p.8 alternative also remains sufficient. |
| D-007 p.10 [137,339) | Names UNFCCC as the treaty, then assigns it the framework for negotiating Kyoto and Paris. | The antecedent and first bridge fact are now present. |
| D-007 p.29 [963,1106) | Identifies COP as the supreme decision-making body and includes the full convention name and UNFCCC acronym. | Completes the second bridge fact. Together with p.10, sufficient for the question without supplying the bridge from memory. |

The p.10 span is 30 words; the stored quote is its first 25 while the true end remains 339. This follows the corrected prefix-anchor contract.

All ten seeds remain `llm-draft`, `split="unassigned"`. This review confirms the span corrections; it is not the human verification required by Gate C.

## 5. Checks inspected: do they test their stated claims?

At least two checks were required; these five were examined closely.

| Check and location in contracts_check.py | Assessment |
|---|---|
| Page-2/cross-page coordinate checks, L537–605 | Valid for gold-coordinate conversion and oracle-selected evidence under two chunk scopes. The negative control genuinely detects skipping conversion. They do not prove that actual ranked top-k retrieval is equal between chunkers; the test selects all overlapping evidence chunks. |
| Half-span / AND-OR sufficiency checks, M-02 section | Use actual seed spans and the reference coverage function. Half fragments fail CE despite a hit; one group fails; alternatives and unions pass. These genuinely exercise the original M-02 counterexamples. |
| Changed-content cache checks, M-04 section, plus exact H.3 pytest | Exercise the actual extracted cache helper, including deliberate stale snapshot-ID reuse. They genuinely distinguish trace IDs from cache identity. |
| Qid-alignment / group-bootstrap checks, M-05 section | Execute both reference code and 06's extracted sketch; shuffled maps, missing qids and grouped variants are tested. The metadata-order caveat is separate, R-07. |
| Typed unlock / gate checks, L899–983 | Correctly test cycles, required gates and nonempty OR choices. They do not test exposure-only state; the helper requires it in mastered, R-04. |

Additional limitations:

- The “snapshot verifies” check follows a real verification call, so it is not an unconditional pass in isolation. However, verification checks page text hashes/lengths, not full binding/structural integrity; R-02.
- The round-trip check bypasses the guarded converter; R-05.
- M-06's three checks reproduce numbers in text. They do not validate κ interval methodology.
- The checker’s snapshot-ID recipe deliberately differs from the final documented one. The log discloses this, but the canonical recipe should be used when extending integrity acceptance checks.

## 6. Readiness re-evaluation: gates A, B and C

Marks below are recorded **in this report only**. Prior checked items outside this correction scope are carried forward, not independently re-audited. A pending future runtime artifact is not a reason to withhold **design** approval; the reasons below are the remaining in-scope design/acceptance defects and explicit Gate A decisions.

### Gate A — design approval

| Items | Status in this scoped re-review | Evidence / next step |
|---|---|---|
| S-1, S-2, S-3, S-4, S-5, S-6 | Carry forward checked | Prior source audit remains the evidence; no repeat audit of untouched citations/book content was requested. |
| C-1 | Not yet checked | The revised prerequisite registry is coherent on paper, but its executable exposure rule still contradicts that policy (R-04). Carry forward the previous checks of untouched phase/version content; do not reopen the previous minor display-order finding. |
| C-2, C-3, C-4, C-5 | Carry forward checked for their narrow criteria | Prior failure/family/scope/note-decision records remain; this report updates only the eight correction verdicts. Recorded decisions do not imply every implementation amendment is closed. |
| DEC-1a | Pending / blocks A as written | D-03/D-04/D-05/D-10 are documented as learner decisions; D-14/D-16/D-19/D-20 are explicitly pending until O2. Repair R-01 and record the needed choices. |
| DEC-1b | Pending | D-17 cannot be unconditionally re-confirmed while R-02 remains. D-06 and D-07 are recommendations without the complete dated confirmation required by this item. |
| DEC-2 | Carry forward new documented acknowledgment | 08 D-13 records learner acknowledgment dated 2026-10-08. This review accepts that documentary record; it did not access the other conversation itself. |
| V-1 | Partially satisfied; not ticked | Frozen-text fields and coordinates are written; full integrity/conversion acceptance still needs R-02/R-05. |
| V-2 | Checked at specification level | Revised evidence-group, CE, diagnostic and metric-separation contract meets M-02. |
| V-3 | Carry forward checked | No learner experiment results were filled by this re-review; test outputs are verification evidence. |
| V-4 | Partially satisfied; not ticked | Comparison/split policy is accepted; κ interval method needs R-03. |
| P-1 | Not yet checked | Corrected H.3 implementation and 13 tests pass, but approval of the shared snapshot contract remains conditional on R-02. This is not a re-review of the old minor lesson issues or all untouched blocks. |
| P-2 | Pending / blocks A as written | The supplied records do not document the learner's agreement to the coaching/progress protocol; 08 leaves this item open. Requesting a technical re-review is not that agreement. |
| P-3 | Carry forward checked | No re-review of the prior-material migration policy. |
| R-1, R-2, R-3 | Carry forward checked for design | Existing logging, extraction-quality and minimal-reproduction controls remain; the corrected embedding cache passed this re-review. |

### Gate B — environment and baseline exit

| Item | Status | Reason |
|---|---|---|
| E-1 | Pending | No project environment/committed lock was built in this review. |
| E-2 | Pending | No Cohere/Groq smoke calls were made. |
| E-3 | Pending | The Cohere default model/limit is not verified by these correction checks; the earlier MiniLM fact remains fallback evidence. |
| E-4 | Pending | No project notebook front end launched. |
| BL-1 | Pending | No v0 end-to-end system built or executed. |
| DEC-1c | Pending | Concrete T files and D-09 confirmation remain future work. |
| DEC-3 | Pending at the appropriate later stage | T needs selection/freezing before Phase 3; H should remain deferred to K1. Synchronize R-06. |

These are expected later exit criteria, not present reasons to demand a built system before Gate A.

### Gate C — measurement exit

| Item | Status | Reason |
|---|---|---|
| MX-1 | Pending | Draft seed verification by AI is not a human-verified frozen eval set. |
| MX-2 | Pending | Reference acceptance checks are not the learner's v0 retrieval harness rerun. |
| MX-3 | Pending | Seeds have unassigned splits; group-split tests validate the mechanism, not the final dataset. |
| MX-4 | Pending | No human-labeled v0 generation pilot exists from this review. |
| MX-5 | Pending | No learner v0 failure-bucket counts/traces were produced. |

## 7. What must happen before Gate A can be granted

1. Remove the residual DEC-1a/O2 ordering cycle or explicitly allow decision-only preflight; record the remaining pre-build decisions and P-2 agreement.
2. Repair the reference manifest loader and its negative tests so R-02 fails closed; clarify the virtual page-join decoding in R-05.
3. Replace the blanket Wilson requirement with rate-specific and κ-specific interval methods.
4. Separate mastery from exposure in the unlock helper and add the exposed-only I-CMP/K1 acceptance path.
5. Synchronize the corrected contracts, their summaries and the Gate A decision records. Address the minor H-timing/qid-order discrepancies without expanding the course.
6. Re-run the existing tests and the new negatives, then re-confirm C-1/DEC-1b/V-1/V-4/P-1. Leave Gates B/C pending until their producing work is authorized and completed.

No notebook expansion, provider setup, dataset labeling, trim pass or unrelated minor-finding cleanup is required to perform those corrections. The tests that already pass should remain passing.

**Final verdict: NOT GRANTED.**
