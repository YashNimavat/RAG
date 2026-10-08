# RAG Learning System: master index

> **Location (2026-10-08).** Everything lives under **`C:\Yash\New-Work\Book RAG\`**:
> - `rag_learning\` — this workspace;
> - `RAG_Made_Simple_The_Complete_Visual_Guide\` — the book PDFs, sha256-identical to the copy cited before the move;
> - `upstream\RAG_Techniques\` — the pinned git clone at `009adba`;
> - `RAG_Techniques-main\` — your earlier zip copy, identical, kept untouched;
> - `prior_work\` — **copies** of your earlier work (`my way\`, `VAI\`, `RAG book step by step\`). Source files only: notebooks, code, docs and PDFs (540 files, 64 MB). Virtual environments, `node_modules`, caches and `.env` were excluded. The originals in `C:\Yash\New-Work\RAG\` are unchanged; [`relocate_prior_work.py`](sources/verification/relocate_prior_work.py) repointed the references.
>
> **Open `C:\Yash\New-Work\Book RAG` as the single folder** in VS Code and in Codex.
>
> All workspace paths were updated by [`relocate_paths.py`](sources/verification/relocate_paths.py). Codex's review reports and the lab run records keep the old paths (`C:\Yash\New-Work\RAG\…`, `C:\Users\Yash\Documents\BOOK\…`) because they are historical records of where things were when they ran.

A connected, implementation-focused system for learning RAG. You understand each technique, implement it, measure it and decide when to use it. The anchor is one evolving project, **"Ask My Technical PDFs"**.

> **Status (2026-10-08): Approval gate A (design approval) GRANTED WITH FIXES by Codex re-review 2** ([report](reviews/CODEX_REREVIEW2_2026-10-08.md)). Both required fixes are applied, and the acceptance suite passes 145/145. Phase 0–2 work (O1–O3, P1–P7, building v0) is now permitted. Gates B and C are not yet granted. History: [corrections log](reviews/CORRECTIONS_LOG_2026-10-08.md#round-3).
> - This stage contains the plan, the source mapping, the gap analysis and **one** sample lesson.
> - No lab notebooks, `ragkit` code or further lessons exist yet, by design. **Nothing will be expanded until the critical findings are confirmed resolved.**
> - Codex's review: [reviews/CODEX_REVIEW_2026-10-08.md](reviews/CODEX_REVIEW_2026-10-08.md) (verdict NOT READY, 84/100). It raised one P0 and seven P1 findings, all re-verified and corrected. Each correction is documented in [reviews/CORRECTIONS_LOG_2026-10-08.md](reviews/CORRECTIONS_LOG_2026-10-08.md); the contracts applied are in [reviews/CORRECTIONS_SPEC_2026-10-08.md](reviews/CORRECTIONS_SPEC_2026-10-08.md).
> - Codex's re-review: [reviews/CODEX_REREVIEW_2026-10-08.md](reviews/CODEX_REREVIEW_2026-10-08.md) (Gate A not granted; findings R-01…R-07). The round-2 contracts are in [reviews/CORRECTIONS_SPEC_R2_2026-10-08.md](reviews/CORRECTIONS_SPEC_R2_2026-10-08.md); the fixes are logged from [R-01](reviews/CORRECTIONS_LOG_2026-10-08.md#r-01) onward.
> - Readiness is now staged (Codex B-01), see [08 Part 7](08_GAP_ANALYSIS_AND_DECISIONS.md#part-7--implementation-readiness-criteria):
>   - **Gate A, design approval:** permits Phase 0–2 work.
>   - **Gate B, environment and v0 working:** permits measurement work.
>   - **Gate C, verified eval set and harness:** permits optimisation experiments.
> - The first review's instructions for Codex are in [CODEX_REVIEW_BRIEF.md](CODEX_REVIEW_BRIEF.md).
>
> Revised 2026-10-08 (Codex re-review R-01…R-07): status now reads "awaiting Codex re-review 2 of R-01…R-07"; re-review and round-2 spec linked. See [corrections log](reviews/CORRECTIONS_LOG_2026-10-08.md#r-01).

## Read in this order

| # | File | What it answers | Read it when |
|---|---|---|---|
| 01 | [Source inventory](01_SOURCE_INVENTORY.md) | What was actually inspected: the book PDFs (provenance, per-page citation convention), the repo pinned at `009adba`, this machine's keys and dependencies, prior materials, and external references | First, to trust (or challenge) every citation |
| 02 | [Master learning plan](02_RAG_MASTER_LEARNING_PLAN.md) | The dependency-ordered path: 13 phases and 56 concept cards (O1…K1), mastery gates, fast-track rules, book order vs curriculum order, schedule | To know what to study next and why |
| 03 | [Concept dependency map](03_RAG_CONCEPT_DEPENDENCY_MAP.md) | Where each technique sits in the pipeline, the prerequisite DAG, technique families that need comparison, and which metric observes which stage | When techniques start to blur together |
| 04 | [Book-to-code mapping](04_BOOK_TO_CODE_MAPPING.md) | The **master traceability matrix** (concept → stage → prerequisites → book pages → notebook cells → gaps → experiment → order → priority), chapter-by-chapter mapping, and a catalogue of book-vs-code divergences | While studying any chapter or notebook |
| 05 | [Learning & retention system](05_LEARNING_AND_RETENTION_SYSTEM.md) | Session protocol, AI-coach rules (hint ladder, one question at a time), recall/application/transfer rubrics, spaced repetition, progress file formats, mastery levels | Before the first study session |
| 06 | [Project & evaluation plan](06_RAG_PROJECT_AND_EVALUATION_PLAN.md) | `ragkit` architecture, the exact v0 spec, version cards v0…v8, corpora, span-level eval set (with 10 draft seed items), metric formulas, judge protocol, experiment registry and statistics | When building or comparing anything |
| 07 | [Sample lesson: C2 chunking (+ I1 experiment)](07_SAMPLE_LESSON.md) | One complete Parts A–M lesson, the quality bar for every future lesson. All numbers are lab-verified | As the first real lesson, and as the template |
| 08 | [Gap analysis & decisions](08_GAP_ANALYSIS_AND_DECISIONS.md) | The ten gap questions answered, errors in both sources, 30 open decisions (with owners), 20 risks, assumptions, readiness checklist | Before approving the next stage |

## Supporting folders

| Folder | Contents now | Future contents |
|---|---|---|
| [curriculum/](curriculum/) | [`CURRICULUM_BACKBONE.md`](curriculum/CURRICULUM_BACKBONE.md): the design spec that 01–08 call "BACKBONE" | Per-phase module pages |
| [sources/](sources/) | [`verification/`](sources/verification/): lab scripts and outputs behind every number in 07 ([`LAB_FACTS.md`](sources/verification/LAB_FACTS.md)) | Source registry notes (no copied book text) |
| [concepts/](concepts/) | — | One lesson per concept ID, following [07](07_SAMPLE_LESSON.md) |
| [labs/](labs/) | — | Notebooks named `<ConceptID>_*.ipynb`; adapted upstream copies in `labs/upstream_adaptations/` |
| [experiments/](experiments/) | — | `E0xx_<version>/` runs: `config.yaml`, `results.jsonl`, `summary.md` ([06 §9](06_RAG_PROJECT_AND_EVALUATION_PLAN.md#9-experiment-protocol)) |
| [evaluation/](evaluation/) | — | Frozen eval sets (JSONL) and harness notes ([06 §6](06_RAG_PROJECT_AND_EVALUATION_PLAN.md#6-evaluation-dataset)) |
| [progress/](progress/) | — | `concept_tracker.csv`, `session_log.md`, `misconception_log.md` ([05 §6](05_LEARNING_AND_RETENTION_SYSTEM.md#6-progress-system-file-formats)) |
| [reviews/](reviews/) | — | `review_queue.md` (spaced-repetition queue) |

## Sources (read-only; never modified)

- **Book:** *RAG Made Simple: The Complete Visual Guide* (Nir Diamant), 25 split PDFs in `C:\Yash\New-Work\Book RAG\RAG_Made_Simple_The_Complete_Visual_Guide\`.
  - Cite as `Ch4 p.3/15`, meaning PDF page 3 of the 15-page `chapter 4.pdf`. The book has no printed page numbers.
  - The edition cannot be verified ([01 §2.1](01_SOURCE_INVENTORY.md#21-identity-and-provenance)).
- **Repo:** `https://github.com/NirDiamant/RAG_Techniques`, cloned to `C:\Yash\New-Work\Book RAG\upstream\RAG_Techniques` at commit `009adba2be1bef49780ef73b6dd3c18fd24b035b` (41 technique notebooks + 5 evaluation notebooks). Custom **non-commercial** licence.
- **Prior materials:** `C:\Yash\New-Work\Book RAG\prior_work\RAG book step by step\learning_guides\` is **retired**: 19 of 22 guides are mis-numbered against the real book ([01 §5](01_SOURCE_INVENTORY.md#5-prior-learner-materials)). Your executed `my way\` notebooks and VAI labs feed the O1 diagnostic.

## Ground rules this system enforces

1. Measure before improving. Evaluation (Phase 3) comes right after the baseline, not last as in the book.
2. Retrieval quality and answer quality are always reported separately.
3. Every technique enters as: observed failure → hypothesis → single-variable change → controlled experiment → decision, including "when NOT to use".
4. Mechanism before framework. You write plain Python/NumPy first, read the upstream code second, and build reusable `ragkit` code third.
5. No invented numbers. Results tables stay empty until a logged run fills them. Every claim cites a book page, a notebook cell or line, or is marked UNVERIFIED.
6. A completed notebook is not evidence of mastery ([05 §7.4](05_LEARNING_AND_RETENTION_SYSTEM.md#74-what-counts-as-evidence-and-what-does-not)).
