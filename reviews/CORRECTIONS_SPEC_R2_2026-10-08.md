# Corrections spec, round 2: Codex re-review findings R-01 to R-07 (2026-10-08)

**Source:** [CODEX_REREVIEW_2026-10-08.md](CODEX_REREVIEW_2026-10-08.md). The verdict was "Gate A NOT GRANTED".
- **RESOLVED:** M-02, M-03, M-04, M-05.
- **PARTIALLY RESOLVED:** B-01, M-01, M-06, M-07.

All seven R-findings were re-checked by the orchestrator against the cited lines. Each is accepted as stated.

**Scope rules (same as round 1):**
- Fix only R-01 to R-07 and record the learner decisions below.
- No new lessons, labs or concept IDs. No trimming. No minor-finding cleanup from the first review.
- Never modify the book PDFs, the upstream repo, prior learner folders, or the two Codex review files.
- **Revision markers:** `> Revised 2026-10-08 (Codex re-review R-0x): <one line>. See [corrections log] (reviews/CORRECTIONS_LOG_2026-10-08.md#r-0x).` (template shown with a space so it is not parsed as a link) Use `../reviews/...` from `curriculum/`. Log anchors: `#r-01` to `#r-07` and `#round-2-decisions`.
- Keep headings and anchors stable. No fabricated numbers: every new number must be computed and shown, or labelled "Assumption".

## Learner and coach decisions (recorded 2026-10-08, before Gate A)

| Decision | Value | Owner |
|---|---|---|
| D-14 | Python 3.12, pinned with uv | Learner |
| D-20 | CPU-first PyTorch build; switch to CUDA only if a measured slowdown justifies it | Learner |
| D-19 | Notebook front end = VS Code notebooks on the project uv kernel | Learner |
| D-16 | Workspace stays at `C:\Yash\New-Work\Book RAG\rag_learning`; **local git only** (no remote); `.gitignore` covers `.env`, PDFs, snapshot text when the licence is unclear, caches and indexes | Learner |
| P-2 | The learner **agrees** to the coaching/progress protocol in 05 | Learner |
| D-06 | v0 chunk units = characters (1000/200 recursive), with the embedder's token count logged per chunk | Coach confirmation |
| D-07 | Vector store = NumPy exact search for v0–v2; FAISS only in the P5 lab | Coach confirmation |

These are already-recommended defaults; only the confirmation and date are new.

## R-01 (Blocker, closes B-01): remove the decision-entry cycle

- DEC-1a decisions are now made in a **decision-only preflight**: a conversation with no environment created. This preflight is explicitly allowed **before** Gate A.
- With D-03, D-04, D-05, D-10 (round 1) and D-14, D-16, D-19, D-20 (above) all recorded, DEC-1a is complete before O2.
- O2 now **implements** these decisions (it creates the environment). It no longer **makes** them.
- Gate A text in 08 Part 7, 02 §4 and BACKBONE §3 must say:
  - Gate A requires only design-time artifacts plus decisions from the preflight.
  - No Gate A item is produced by O2 or any later lab.
  - "Start O2's decision discussion" (preflight, allowed now) is distinct from "create the environment" (O2, after Gate A).
- In 08:
  - DEC-1a is ticked with "(learner decisions recorded 2026-10-08)".
  - DEC-1b covers D-06 and D-07 (coach confirmation above) plus D-17. D-17 is re-confirmed once R-02 passes.
  - P-2 is ticked with "(learner agreement 2026-10-08)".
  - Rows D-14, D-16, D-19 and D-20 read "Decided 2026-10-08 — Learner". D-06 and D-07 read "Confirmed 2026-10-08 — Coach".
- Remove or replace any wording that says these are "confirmed at the start of O2".

## R-02 (Major, M-01): fail-closed binding and page-table integrity

**Normative contract (06 §5.3 and §6.1).** The loader must validate the dataset's binding **before** translating any gold label, and reject on any failure:

1. **Required binding fields present.** Dataset header: `snapshot_id`, `snapshot_manifest_sha256`, `scorer_version`, `evidence_logic_version`. Manifest: every field listed in §5.3.
2. **`snapshot_manifest_sha256` equals the sha256 of the exact manifest file bytes**, as stored (UTF-8, as written). The dataset records the digest of the bytes it was labelled against.
3. **Page table structural integrity**, per document:
   - pages are numbered 1..n in order with no gaps;
   - `page_table[0].doc_char_start == 0`;
   - for each i: `doc_char_end_i − doc_char_start_i == len(page_text_i)`;
   - `doc_char_start_{i+1} == doc_char_end_i + len(page_join)`;
   - the last `doc_char_end` equals `len(doc_text)`;
   - each page's `text_sha256` matches;
   - `doc_text_sha256` matches the join of the pages.
4. **`snapshot_id` recomputed** with the exact recipe in 06 §5.3 equals both the manifest's and the dataset's `snapshot_id`.
5. **Negative acceptance cases.** A wrong `snapshot_manifest_sha256` is rejected. A page table with page 2's start **and** end both shifted by +1 (text hash and length unchanged) is rejected. Example: pages `["abc","def"]`. The valid page-2 [0,1) maps to document [4,5) = "d"; the shifted table must not silently map it to [5,6) = "e".
6. The checker's snapshot serialisation is aligned with the 06 §5.3 recipe.

## R-05 (Minor, with R-02): two decoders, one stated rule

- **Gold segments** (authored) must lie inside the **physical page text**: `0 ≤ char_start < char_end ≤ len(page_text)`. Decode them with `gold_to_doc(page, start, end)`.
- **Chunk-derived `page_segments`** (07 H.3) may include the **virtual page-join character**. It is assigned to the preceding page, so a segment may end at `len(page_text) + 1` for pages before the last. Decode them with `chunk_segment_to_doc(...)`, which permits that one extra position.
- Coverage is always computed in **document offsets**, so the two decoders never need to agree on page-relative form.
- This rule is stated in 06 §2.3 and §6.4 and in 07 H.3 (a note only; the 07 code is unchanged).
- **Acceptance:** for pages `["abc","def"]`, a whole-document chunk gives page-1 segment [0,4), which `chunk_segment_to_doc` accepts. The gold decoder rejects [0,4) on page 1 and accepts [0,3). Round-trip checks go **through the public decoders**, not raw arithmetic.

## R-03 (Major, M-06): interval methods by statistic

Replace the blanket "Wilson intervals for κ, the confusion matrix and recall" rule (06 §8.4 and every summary that repeats it) with:

- **Confusion matrix:** report the raw **counts**, with no interval.
- **Binomial rates** (failure-class recall, precision, abstention precision and recall, false-abstention rate): use a **Wilson 95% interval** when the units are independent.
  - When several units come from one answer (claims or citations of the same answer), use a **cluster bootstrap over answers** instead.
  - The 8/10 → ≈ 0.49–0.94 example stays as a Wilson example.
- **Cohen's κ:** **not** a proportion; it can be negative. Use a **paired bootstrap over labelled units**, resampling clusters (answers) when units are clustered. Or use the large-sample κ variance (statsmodels `cohens_kappa` is the reference implementation).
  - Example to include: two raters on 4 balanced items who always disagree give observed agreement 0, expected agreement 0.5, so **κ = −1**. A Wilson interval would be meaningless here.
- **Decision rule (provisional operating preference, labelled Assumption):** a judge is certified for a metric only if, on the untouched validation set, the **lower 95% bound** of failure-class recall is **≥ 0.70** and the lower 95% bound of κ is **≥ 0.40**. Otherwise human scoring continues for that metric.
  - The previous point targets (κ ≥ 0.6, recall ≥ 0.8) remain reported as aspirational, not as the pass rule.
- Keep everything else from M-06 unchanged: human fallback, disjoint pilot and validation sets, the deferred judge, the challenge set, and the ≥ 15 unanswerables rule.

**Files:** 06 §8.4 (and §8.5 if needed), 08 D-10 and RK-03, BACKBONE §5, 02 M3/V4/Gate wording if it says "Wilson" for κ or for the confusion matrix, 03 §6 if it does.

## R-04 (Major, M-07): exposure ≠ mastery

- **Learner state has two sets:** `mastered` (concepts at or above the required level) and `exposed` (mechanism exposure recorded: read + trace or demo).
- **Unlock rule:**
  - `requires_all` and `requires_any_groups` are checked against `mastered`;
  - `requires_exposure` is checked against `exposed ∪ mastered`;
  - `requires_gate` is checked against passed gates.
- Exposure to a concept never substitutes for mastery of an all/any prerequisite.
- **03 §2.1 legend / field notes:** state this explicitly.
- **05 progress system:** `progress/concept_tracker.csv` must be able to record exposure. Add an allowed `status` value `exposed` (definition: mechanism exposure demonstrated by a trace or demo; not mastery), with evidence in `evidence_links`. If a separate column fits 05's design better, an `exposed_on` date column is acceptable. Choose one and define it.
- **Checker tests:**
  - I1 mastered + I2–I6 exposed-only ⇒ I-CMP unlocked;
  - one exposure missing ⇒ blocked;
  - exposure alone does not satisfy an all/any prerequisite;
  - K1 is reachable with I2–I6 exposed-only (not mastered) and no A\*/S\* concept mastered or exposed.

## R-06 (Minor, B-01): Corpus H timing everywhere

- Everywhere: **"Corpus T chosen and frozen (with snapshot) before Phase 3; Corpus H chosen and frozen before K1."**
- Fix BACKBONE §3 (Gate B row) and the round-1 spec copy (`reviews/CORRECTIONS_SPEC_2026-10-08.md`). Edit the spec copy with an inline "[corrected in round 2, R-06]" note rather than rewriting history.
- 08 is already correct.

## R-07 (Minor, M-05): qid comparison is order-insensitive

- Comparison metadata stores qids as a **canonical sorted list**, enforced at construction. The guard compares **sets**.
- Add a test: identical metadata with qids in a different order is **accepted**, and different qid sets are still rejected.
- 06 §9.2/§9.3: one sentence stating this.

## Checker additions (`sources/verification/corrections/contracts_check.py`)

Add tests for R-02, R-04, R-05 and R-07, plus κ (R-03):
- the κ = −1 example computes −1, and its bootstrap interval is valid (within [−1, 1], computed);
- the document no longer applies Wilson to κ.

Also add **08 Part 7 structural checks** (Codex noted the suite did not read 08):
- every item ID appears in exactly one approval gate;
- every Gate A item is a design-time item, i.e. not E-\*, BL-\*, MX-\* or DEC-3;
- DEC-1a lists D-03, D-04, D-05, D-10, D-14, D-16, D-19, D-20, and each is marked decided in Part 4.

**All existing checks must keep passing.** Record the new pass counts.
