# Session log (append-only, newest last; format: [05 §6.2](../05_LEARNING_AND_RETENTION_SYSTEM.md#62-progresssession_logmd-template))

## Session 2026-10-08 #1 — diagnostic
- **Concept(s):** O1 (probes P1, P3–P7, C2–C5, M2, M3, M5, R1–R3, I5, V2, A2, D4)
- **Duration:** ~60 min
- **Tutor:** Claude (claude-opus-5-5)
- **Plan vs actual:** blank-page reconstruction + 2 trace questions + 12 cold items, as planned. No notes. No teaching during the diagnostic.

### Items

All items: type R/A/T/X as shown, not scheduled, hint level H0, unassisted. "Conf." is the learner's confidence (1 = guessing, 3 = sure). Learner answers are paraphrased, except the reconstruction, which is verbatim in its own file.

| item_id | Type | Conf. | Score | Rationale |
|---|---|---|---|---|
| O1-REC | X | 3 | 4/10 | Rubric 05 §5.5; see [reconstruction](../reviews/reconstructions/2026-10-08_phase0.md). |
| O1-TR1 | R | 3 | 1 | Named cosine similarity. Missed that the **question is embedded with the same model**. Called it a "similarity matrix". |
| O1-TR2 | R | 3 | 1 | Knows a parameter limits the number of chunks. Didn't name k. "More = not good" is one-sided: no recall vs noise/cost trade-off. |
| O1-Q01 | R | 3 | 1 | Token = subword unit: partly right. "Decided by the embeddings": wrong (the tokenizer decides). 1,000 characters → 1,000 tokens: wrong (~4–6 characters per token). Truncation (max_seq_length) missed. |
| O1-Q02 | A | — | 0 | Could not recall the cosine formula. The L2-vs-cosine ranking question was not attempted. |
| O1-Q03 | R | 3 | 1 | Idea that a rare term embeds poorly: partial. BM25's exact-term matching / IDF not stated. k1 and b not known. |
| O1-Q04 | A | — | 0 | Precision@k, Recall@k and reciprocal rank definitions not recalled. |
| O1-Q05 | R | 3 | 1 | Headings, sub-headings, paragraph number, topic: useful context. Missing doc_id, page, offsets, chunk_id, params. Did not say what breaks. |
| O1-Q06 | A | — | 0 | NumPy top-k by cosine not attempted. |
| O1-Q07 | R | 1 / 3 | 1 | **Part 1:** prompt construction answered as "overlap words so chunks stay connected", which mixes up index-time chunking with query-time prompt building. **Part 2:** "lost in the middle" described vaguely as finding small things in long text, then linked to local vs global minima (wrong association). |
| O1-Q08 | R | 2 | 2 | Correct: a right answer despite failed retrieval comes from the LLM's internal (parametric) knowledge. Did not give a perfect-retrieval / wrong-answer example or how to measure each. |
| O1-Q09 | A | 3 | 2 | Did not know RRF. Rank-agreement intuition gave the order **A, C, B, D**, which matches RRF (k = 60). No formula; min-max fragility not discussed. |
| O1-Q10 | R | — | 0 | Bi-encoder vs cross-encoder not known, although VAI L22 covered reranking. |
| O1-Q11 | T | 2 | 1 | Blamed bad thresholds on data/chunking quality. Did not see that an LLM score is uncalibrated. Proposed "multiple runs", not a labelled dev set with error rates. |
| O1-Q12 | T | 1 | 2 | Suggested hybrid BM25 + vector search (helps with exact version strings) and manual chunk checks. Missed version metadata/filtering, contextual headers and an eval slice to measure. |

**Totals:** 12 items = 11 / 48 (23%); reconstruction 4 / 10.

**Calibration:**
- Answers given with confidence 3 (O1-TR1, TR2, Q01, Q03, Q05, Q07-2, Q09) averaged **1.1 / 4**.
- "Feeling sure" is currently a poor guide to being right. This is the core reason for closed-book retrieval practice.
- The confidence definition was clarified mid-session (after Q06).

### Difficulty changes
- None. The diagnostic was fixed-form.

### Tracker changes (each with evidence)
- **Seeded:** 56 rows, all `not_started` (05 §8.3 step 1).
- **`exposed`, interval 1, next review 2026-10-09** (O1 score 2; evidence `log:2026-10-08#…`): M2, M3 (O1-Q08), R1 (O1-Q09), M5 (O1-Q12).
- **O1:** `exposed`, first_studied 2026-10-08 (diagnostic completed; reconstruction saved).
- **Phase 1 priority, `reinforcement_flag = 1`** (O1 score ≤ 1): P1, P3, P4, P5, P6, P7.
- **Legacy evidence** recorded in `evidence_links`, unscored (05 §8.3 step 4).

### Misconceptions
- **New:** MC-001 to MC-006 ([misconception log](misconception_log.md)).
- **Candidate not opened:** "overlap guarantees nothing is lost". Hinted at in the reconstruction but not directly probed. C2 Part A item PK-4 probes it.

### Fast-track (02 §5)
- **No concept is eligible.** Eligibility needs three cold items at ≥ 3; the highest O1 score was 2.
- Prior `my way/` and VAI work stays as exposure only.
- No phase is compressed. Phase 1 runs in full.

### Next session
- **Due reviews:** 4 (M2, M3, R1, M5) on 2026-10-09. Because their prerequisites are not yet mastered, these are short recall checks on what was answered today, not lessons (Coach note).
- **Next concept:** O2 (environment setup). Allowed: Approval gate A granted 2026-10-08. A-02 key check announced before running.
- **Then:** O3, then Phase 1 starting at P1, with P4 and P6 emphasised.

## Session 2026-10-08 #2 — concept (O2 environment setup)
- **Concept(s):** O2
- **Duration:** ~40 min, mostly downloads
- **Tutor:** Claude (claude-opus-5-5)
- **Plan vs actual:** set up the environment per DEC-1a (D-14 Python 3.12, D-20 CPU torch, D-19 VS Code notebooks, D-16 local git). The learner approved the API smoke calls in advance.

### Items
| item_id | What | Result |
|---|---|---|
| O2-ENV | uv project + install | **PASS.** Python 3.12.8; torch 2.14.1+cpu (CUDA off by design); sentence-transformers 6.1.0; numpy 2.5.3; **pymupdf pinned 1.26.7** (uv first installed 1.28.2, which would have changed the frozen snapshot: parser version is part of `snapshot_id`); cohere, groq, rank-bm25, tiktoken, python-dotenv; dev: pytest, ipykernel. `uv.lock` written. |
| O2-GIT | Local git | **PASS.** `git init`, no remote; `.gitignore` covers `.env`, `.venv/`, PDFs, snapshot text, caches and indexes (verified with `git check-ignore`). No commit made yet. |
| O2-KEYS | `.env` | **PASS.** Copied from `my way/.env`; values never printed. Added `GROQ_MODEL_ID=openai/gpt-oss-20b` and `COHERE_EMBED_MODEL=embed-v4.0`. |
| O2-SMOKE | `labs/O2_smoke_test.py` | **4/4 PASS** ([report](O2_smoke_test_2026-10-08.json)): MiniLM cosine top-1; BM25 top-1; Cohere `embed-v4.0` (1,536 dims, 8,192-token context); Groq `openai/gpt-oss-20b` replied "smoke test ok". |

### What the smoke test surfaced
- **Groq model availability.** None of the Llama ids used by the repo notebooks are offered on this account. Chat models available: `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `qwen/qwen3.8-27b`, `allam-2-7b`. This confirms 08 RK-01 (model deprecation).
- **Reasoning-model token use.** `gpt-oss-20b` is a reasoning model. With `max_tokens=12` it returned an **empty** answer, having spent its tokens on reasoning, and the first version of the check still marked it PASS. The check now asserts the reply text and uses `reasoning_effort="low"` with `max_tokens=256`. Lesson for C5: always assert on content, and budget for reasoning tokens.
- **Cohere embedding models available:** `embed-v4.0` and `embed-v5.0-fast/pro` (8,192-token context); the v3.0 family (512). `embed-v4.0` is the D-03 default.
- **API calls made:** Cohere 2 embed calls (+ 2 model-list calls); Groq 3 chat calls (+ 3 model-list calls).

### Tracker changes (each with evidence)
- O2.status: not_started → exposed — evidence: log:2026-10-08#O2-ENV, the smoke-test report.
- 08 Part 7: E-2 and E-3 ticked. E-1 waits for the first commit; E-4 waits for the learner to run `labs/O2_kernel_check.ipynb` in VS Code.

### Relocation (learner request)
- All files now live under `C:\Yash\New-Work\Book RAG\`: the workspace, the book PDFs, the pinned clone, the old repo copy, and `prior_work\` (copies of `my way`, `VAI` and `RAG book step by step`, source files only).
- Paths were updated, and the acceptance suite passes 145/145 from the new location.

### Next session
- **Due reviews:** 4 (M2, M3, R1, M5) on 2026-10-09.
- **Next concept:** O3 (how to use this system, ~10 min), then Phase 1 from P1.
- **Learner actions:** run `labs/O2_kernel_check.ipynb` in VS Code (E-4); approve the first git commit (E-1).

## Session 2026-10-08 #3 — concept (O3 how to use this system)
- **Concept(s):** O3
- **Duration:** ~25 min
- **Tutor:** Claude (claude-opus-5-5)
- **Plan vs actual:** Step 0 skipped (no reviews due until 2026-10-09). Part A → teach (session steps, evidence vs status, gates, interval ladder) → reduced assessment (1 A + 1 T; the R evidence is O3-A2b). No lab (O3 has none). Learner actions E-1 and E-4 were raised but not done.

### Items
| item_id | Type | Conf. | Hint max | Score | Rationale |
|---|---|---|---|---|---|
| O3-A1 | R (Part A, routing only) | 2 | H0 | 1 | Gave only "answer, then evaluation". Steps 0, 2–7 missing. |
| O3-A2 | R | 3 | H0 | 2 | "Check retention": core idea right. Mixed it up with Part A ("prior knowledge for topic"). Missed both reasons (recall strengthens memory; the result routes the session, 05 §2.4). |
| O3-A2b | R (restate) | 3 → — | H1 | 3 | Try 1 repeated "measure" only. After H1 (fill-in-the-blank): recall makes memory more permanent; weak old material comes before new. Cap 3. Confidence not given on try 2. |
| O3-A3 | A | 3 | H2 | 2 | Gate 0→1 box check. Try 1: "all 3 ticked" (wrong; 0 commits means no clean clone). Try 2 after H2: "0 files", so box 2 is open. Cap 2. |
| O3-L1 | A | — | H0 | 2 | Interval rule right (3 → up to 3 days; 1 → back to 1 day). Did not compute the dates asked (2026-10-12 / 2026-10-10). |
| O3-L2 | T | 3 | H0 | 2 | "Finished notebook ≠ mastered" right, with the need for checks on later days (L2 idea). Missed that running a notebook is not evidence at all (05 §7.4); needs graded items plus code from a blank file. |

**Calibration:**
- Confidence-3 answers: A2 = 2, A3 (try 1) = 0, A3 (try 2) = 2, L2 = 2. Mean **1.5 / 4**. The O1 pattern persists, and this was pointed out to the learner twice.
- Confidence was omitted twice (A2b try 2, L1) and logged as "—".

### Difficulty changes
- **Format, not level:** the learner did not understand two multi-part prompts (the first O3-A1 wording and O3-A3 as a table). Both were re-asked as one short question with a reply template. Coach note: keep prompts short, plain English, one sub-question, with a fill-in template. Avoid evidence tables inside a question.

### Tracker changes (each with evidence)
- O3.status: not_started → exposed (L1: session ran to step 5; R item O3-A2b logged). next_review 2026-10-09, interval 1. application_score 2 (O3-A3/O3-L1), transfer_score 2 (O3-L2). Evidence: log:2026-10-08#O3-A2b; log:2026-10-08#O3-L1; log:2026-10-08#O3-L2.

### Misconceptions
- None opened. The gaps were protocol knowledge, not RAG mechanisms. The O3 Card's evidence (the first weekly review logged) is still pending.

### Gate 0→1 status (as reasoned in O3-A3)
- Box 1 (O1 graded): done. Box 3 (fast-track decisions): done. **Box 2 (uv sync + smoke from a clean clone): open.** Needs E-1 (first commit, learner OK) and a clean-clone smoke run. E-4 (kernel check in VS Code) is also open.

### Next session
- **Due reviews 2026-10-09:** M2, M3, R1, M5, O3 (5 concepts, short recall).
- **Before P1:** E-1 commit (learner OK) → clean-clone `uv sync` + smoke test → E-4 kernel check. Then Gate 0→1 can be re-checked.
- **Next concept:** P1 (tokens), once Gate 0→1 is passed.
