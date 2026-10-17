# Review queue — generated 2026-10-08 (from progress/concept_tracker.csv after the O1 diagnostic); §2 updated 2026-10-17

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

**Nothing is due (updated 2026-10-17).** Two decisions from the session of 2026-10-14 apply:
- **O3 is retired.** The learner asked not to be quizzed on the learning system itself (the protocol, intervals and gates). The tutor runs the protocol and explains a rule only when it affects them, never as a graded item.
- **The M2, M3, M5 and R1 reviews are paused until each concept's lesson has been read.** Their only evidence is the O1 diagnostic, so a review now would test material that was never taught. Each one restarts on the normal schedule once its lesson is read.

The tracker's `next_review` fields for O3, M2, M3, M5 and R1 were cleared on 2026-10-17.

From now on, the study kit's website (`study/`) works out offline reviews from `progress/study_attempts.jsonl`. This file covers tutor-graded reviews only.

## 3. Interleaving plan
- Not yet: there is fewer than one phase of taught material. Interleaving starts after Phase 2 (05 §5.3).

## 4. Due checkpoints
- Gate 0→1 box 2: E-1 first commit (learner OK) → clean-clone `uv sync` + smoke; E-4 kernel check. Then P1–P7 (Phase 1).
- Gate 1→2 hand computations at the end of Phase 1.
