# Review queue — generated 2026-10-08 (from progress/concept_tracker.csv after the O1 diagnostic)

Format: [05 §6.4](../05_LEARNING_AND_RETENTION_SYSTEM.md#64-reviewsreview_queuemd-template).

## 1. Reinforcement (reinforcement_flag = 1)

These are taught in Phase 1. They are not reviewed before they have been taught.

| Concept | Why |
|---|---|
| P1 | MC-001 |
| P3 | BM25 not known |
| P4 | Cosine formula not recalled; MC-002 |
| P5 | NumPy top-k not attempted |
| P6 | Ranking metrics not recalled |
| P7 | MC-003, MC-004 |

## 2. Due / overdue

All five are due **2026-10-09**, interval 1 day. Each is a short closed-book recall of what was answered today: 1–2 items, about 5 minutes per concept.

| Concept | Recall item |
|---|---|
| M2 | Why can a correct answer appear even when retrieval failed? Give a measurement that would expose it. |
| M3 | Same family as M2: answer quality vs retrieval quality. |
| R1 | Re-derive the A, C, B, D fused order from the two rankings, and explain your reasoning. |
| M5 | Name 3 places in the pipeline where a "wrong product version" answer can originate. |
| O3 | (1) Give the two reasons reviews come first in a session. (2) A concept has interval 3 days, reviewed 2026-10-12, score 2: give the next review date. (Criteria: 05 §2.4, §5.1, §5.2; expected 2026-10-15.) |

## 3. Interleaving plan
- Not yet: there is fewer than one phase of taught material. Interleaving starts after Phase 2 (05 §5.3).

## 4. Due checkpoints
- Gate 0→1 box 2: E-1 first commit (learner OK) → clean-clone `uv sync` + smoke; E-4 kernel check. Then P1–P7 (Phase 1).
- Gate 1→2 hand computations at the end of Phase 1.
