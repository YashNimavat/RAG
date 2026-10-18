# I6 build spec: what each part of the I6 kit must contain

**What this is:** the contract shared by the four I6 build pieces of 2026-10-18 (the HTML lesson, the verify notebook, the apply-it tool, and the question + reading files), so that they teach, rebuild and check the same things with the same numbers and the same names. Every check script tests against this file.
**What this is not:** the lesson. The research is `study/research/phase_04_indexing.md` ("Concept I6"); the measured facts are [`I6_FACTS.md`](I6_FACTS.md) (K1–K12, S-src). **Never invent a number:** every number comes from `out_i6_kit_measure.txt`, `I6_FACTS.md`, the EXTERNAL list (§7), or arithmetic shown in the text (DERIVED).

Templates to mirror (same pipeline as P1, P2 and P4): P2 and P4 for the question and reading files, the md check, the notebook builder and runner, and the tool test; P4's `embed_fit_check.py` for a tool that rebuilds v0's 97 chunks and uses MiniLM. House style: `curriculum/WRITING_STYLE.md`, `study/PORTABLE_LESSON_STYLE.md`; file formats: `study/FORMAT.md`.

---

## 1. Names and paths (fixed)

| Piece | Path |
|---|---|
| HTML lesson | `study/lessons/I6_doc_augmentation.html` |
| Gap audit | `study/lessons/I6_doc_augmentation_gap_audit.md` |
| Short reading | `study/reading/I6_doc_augmentation.md` |
| Questions | `study/questions/I6_questions.md` (17 items, §4) |
| Verify notebook | `study/notebooks/I6_doc_augmentation_verify.ipynb`, built by `sources/verification/I6/i6_build_verify_nb.py`, executed by `i6_verify_nb_run.py` → `out_i6_verify_nb_run.txt` |
| Apply-it tool | `study/tools/question_augment_check.py`; test `sources/verification/I6/i6_tool_test.py` → `out_i6_tool_test.txt`; example report `study/tools/examples/climate_i6_report.md` |
| Markdown check | `sources/verification/I6/i6_md_check.py` → `out_i6_md_check.txt` |
| Stand-in question pack | `study/tools/examples/climate_i6_questions.jsonl` (+ prompt `i6_questions_prompt_v1.txt`) |
| Eval set for examples | `study/tools/examples/climate_seed_spans.jsonl` (the 06 §6.7 seeds, 06 format, page-relative offsets) |

The kit finds the tool through `study/kit.py` `_TOOL_HINT["I6"] = "question_augment"`.

## 2. Lesson steps (HTML section ids; the reading file uses the same order)

Top: `answer` (five sentences), `theory` (12 ideas), `glance` (formula sheet). Then:

| Step | id | Title idea | Must teach (Short) | Key facts |
|---|---|---|---|---|
| 1 | `shape` | Questions and statements embed apart | Bridge: one query vector, one score per stored vector, sort (no matrix, MC-002). The shape hypothesis. D-002: the gold chunk 27 is rank 3 (0.4386; the best chunk scores 0.4606), while a generated question about the same fact scores 0.9869. **859 of 970 = 0.886** generated questions sit closer to a sibling question than to their own chunk | K1, K5, K7, K12 |
| 2 | `lanes` | Index time vs query time | Two lanes; who pays the LLM call; nothing extra at query time; MC-003 check question ("is question generation part of the prompt?" No). HyDE as the mirror image (one sentence; Q2 owns it) | — |
| 3 | `generate` | One call per chunk writes n questions | The prompt file and its rules; JSON list of `n_max = 10`; the prefix trick (n = 1, 3, 5, 10 from one call); structured output, parse once, retry once and log (never split on newlines, HyPE cell 9); cache key = prompt version + chunk text + model; the pack is a **stand-in** written by Claude helpers blind to the eval set; chunk 21's first three questions (the first is about perovskite cells: order is the generator's guess) | K1, K5 |
| 4 | `clean` | Clean, then check every question against its own chunk | Rule counts (empty 0, no "?" 0, numbering 0, deictic 1 = a false positive, duplicates in a chunk 0, across chunks 6); vocabulary echo 0.777; hallucinated or vague questions (Doc2Query--); self-retrieval: own chunk rank 1 for 529, > 10 for 58 of 970; the bottom-30% filter (cut 0.5351, drops 291) is a bi-encoder stand-in for the cross-encoder | K5 |
| 5 | `designs` | Three designs, one parent table | `vectors[i] → (kind, parent_id, question_text)`; chunks + questions (doc-aug), questions only (HyPE), questions appended to the text (doc2query, LlamaIndex); sizes: n = 5 → 582 vs 485 vs 97 vectors; 3,575,808 bytes at 1,536-d vs 596,096 | K4 |
| 6 | `search` | Search the vectors, return unique parents | The D-006 trace (top 12: 11 questions + 1 chunk, 8 unique parents); max vs sum on the toy (A, B, C vs B, A, C); RRF one line (R1 owns it); oversample K_vec ≥ k(n + 1), dedup in rank order, then cut; `set()` loses order; LangChain's default returns 2 parents for "k = 4" on the toy; mean 3.00 unique parents in the top 4 vectors at n = 5 (min 2) | K3, K6, K7 |
| 7 | `score` | Score the parent's span, never the question | CE@k on the parents' `[char_start, char_end)`; the K6 table (A0 MRR@10 0.708 → A1 n = 5 0.781; Hit@1 4 → 5; CE@4 8 → 7 because D-007 needs two chunks); the n-curve (n = 1 is worse than none: 0.653); questions only equals A1 at n ≥ 5 here; sum is worse than max (0.760); 8 draft items prove nothing | K6, K8 |
| 8 | `guard` | Keyword and number queries | Rare-token retention 0.066 / 0.143 / 0.264 / 0.549 for n = 1 / 3 / 5 / 10; the exact-term seeds pass only because the pack happens to name their terms; keep the chunk vector or add BM25 (doc2query was a BM25 expansion; R1) | K5, K8, K9 |
| 9 | `leak` | Leakage: when the index already holds the eval question | K9 table; provisional τ_cos = 0.7054 from the one paraphrase pair (06 asks for ≥ 10 pairs); 10 of 970 questions flagged; de-leaked MRR@10 0.547 < 0.708; not copying (helpers never saw the seeds): the same drafting habit; the decisive slice = human-written + unflagged items; D-009 (unanswerable) best score 0.3099 → 0.7939; AIQ Q45 | K9, K12 |
| 10 | `cost` | What it costs, and when HyDE is cheaper | 97 calls; measured tokens (input median 403, output median 111 at n = 10); Groq $0.0061 visible / $0.0148 with an assumed 300 reasoning tokens; 9.7 min and 39.0% of a day at the free tier; break-even `Q_total > N × rebuilds` (2× a month → 194 queries); 0 extra calls per query vs HyDE's 1; context: 627.9 vs 671.0 tokens (unchanged unit) | K10, K11 |
| 11 | `upstream` | The repo, read critically | Doc-aug: 3 parents of 4,000 / 4,000 / 1,606 regex words (42.5%), 4,271 tokens, 0 punctuation, k = 1 → 6.4× v0's context; "at least 40" questions; parent from a leftover loop variable. HyPE: cell 11 SyntaxError (stale outputs), no metadata, `split("\n")`, `set()` | K2, K11, S-src |
| 12 | `project` | Run it as an experiment, or skip it | When not to use it; the pre-registered arms A0–A5, hypotheses H1–H3, the decision rule, "inconclusive" as an expected verdict; the 3 open decisions for Yash (generator model, langchain-classic, run vs mechanism-only) | research §9, §11 |

Full-only sections (dashed): `research` (doc2query, docTTTTTquery, Doc2Query--, HyPE paper claims, HyDE), `frameworks` (LangChain `MultiVectorRetriever` defaults, LlamaIndex `QuestionsAnsweredExtractor`, `input_type`), `book` (Ch11 pointers, per 04, not re-opened). Then `verify`, `apply`, `llmops` (LLMOps notebook: planned, not built), `check`.

## 3. The formula sheet (cards)

vectors `N·(1+n)` / `N·n`; bytes `vectors × d × 4`; calls `N` per rebuild; cost `Σ(t_in·p_in + t_out·p_out)`; TPM floor `tokens / TPM`; break-even `Q_total > N × rebuilds`; `s(p) = max_v cos(q, v)`; sum and RRF; `K_vec ≥ k(n+1)`; `leak(i) = max_g cos(q_i, g)`; CE@k on parent spans.

## 4. Questions (`study/questions/I6_questions.md`, 17 items)

| id | type | set | Asks | Taught in step |
|---|---|---|---|---|
| I6-PRE-01 | R | pre | Why might a question's vector not land near the passage that answers it? | 1 |
| I6-PRE-02 | R | pre | If questions are written for each chunk when the index is built, how many LLM calls does a user's query add? | 2 |
| I6-R-01 | R | main | What is stored in a multi-vector index, and what is returned to the answer model? | 5, 6, 7 |
| I6-R-02 | R | main | Name the three designs and the one thing each gives up | 5, 8 |
| I6-R-03 | R | main | Why must duplicates be removed before cutting to k? | 6 |
| I6-R-04 | R | main | When does index-time question generation pay its LLM calls, and when does HyDE? | 2, 10 |
| I6-R-05 | R | review | Why are generated questions never scored as evidence or sent to the answer model? | 7 |
| I6-R-06 | R | interview | AIQ 04 Q45, verbatim (`source=AIQ-04-Q45`), our check: the "echo" point is the I6 leakage risk; 0.777 echo and the K9 near-copies | 4, 9 |
| I6-A-01 | A | main | Vectors, calls and float32 bytes for 97 chunks at n = 5 in both designs at 1,536-d (582 / 485; 97 calls; 3,575,808 / 2,979,840) | 5, 10 |
| I6-A-02 | A | main | A new 8-vector table over 3 parents (NOT the lesson's toy): rank by max and by sum; which parent wins only because it has more vectors | 6 |
| I6-A-03 | A | main | Break-even queries for 97 chunks rebuilt twice a month (194), and for daily rebuilds | 10 |
| I6-A-04 | A | main | The top 4 vectors map to 2 unique parents: what does "k = 4" return, and how many vectors to fetch for n = 10 (k(n+1) = 44)? | 6 |
| I6-A-05 | A | main | Given leak_cos for five items and τ = 0.7054, which are flagged, and what does the decision use? | 9 |
| I6-A-06 | A | review | Rare-token retention 0.264 at n = 5 with questions only: what happens to a query by number, and what fixes it? | 8 |
| I6-T-01 | T | main | Eval questions drafted by the same kind of model as the index questions; HyPE scores Hit@4 = 1.00: what do you check and report? | 9, 12 |
| I6-T-02 | T | main | A product catalogue searched by part numbers: which design, if any, and why? | 5, 8 |
| I6-T-03 | T | review | A corpus that changes daily and gets 50 queries a day: index time or query time? | 10 |

Rules: FORMAT §2 (hints 1–2 required, Hint 3 only on A items; 2–5 key points; 1–2 "for a 4"; 1–3 common wrong answers, MC ids where they match: MC-002 matrix, MC-003 stages, MC-006 uncalibrated filter); at most 2 external items (the interview item counts). Every key point must be answerable from the **Short** lesson and from the short reading file. Reread lines: `[short §N](../reading/I6_doc_augmentation.md#...)` · `[lesson step N](../lessons/I6_doc_augmentation.html#<id>)` · a book page `Ch11 p.x/13` (per 04). Never use a transfer seed (`sources/coach/transfer_seed_bank.md`; it has no I6 seed, but do not open it to look).

## 5. Reading file (`study/reading/I6_doc_augmentation.md`)

FORMAT §3: header `<!-- kit:reading concept=I6 depth=short version=1 -->`, "What this is / is not", the book box "> **Read in the book:** Ch11 p.1/13, p.6–11/13 (per 04; not re-opened in the build session)", sections `## 1.` … `## 11.` in the order of steps 1–11, `## 12. When not to use it` (step 12), `## Check yourself` → `study/questions/I6_questions.md`. 1,800–3,000 words of prose (code blocks removed). House-style beats. Same numbers as the lesson.

## 6. Verify notebook and tool

**Notebook** (`I6_doc_augmentation_verify.ipynb`): one section per lesson step 1–11 (plus the upstream arithmetic), rebuilding every K-number with `check(name, got, expected)` against I6_FACTS; Plotly charts: the shape-gap bars (K12), the cleaning counts and the own-chunk cosine histogram with the 30% cut (K5), the index-size bars (K4), the D-006 top-12 strip coloured by parent (K7), the n-curve of MRR@10 and Hit@1 for A1 and A2 (K6), the unique-parents curve against K_vec (K6), the rare-token retention curve (K5), the leakage scatter leak_cos vs best chunk cos coloured by flag (K9), the cost lanes (cumulative calls vs queries for rebuild 1×, 2×, 4× a month vs HyDE) (K10), the parent-size bar (K11). The cross-encoder filter section runs `cross-encoder/ms-marco-MiniLM-L-6-v2` if it is in the local cache and prints `SKIPPED (model not in cache)` otherwise; no lesson number depends on it. No API call; HF offline.

**Tool** (`question_augment_check.py`): "Would index-time question generation help my documents and my questions, and is the gain real?" Inputs: `--docs` (PDF/TXT/MD) or `--chunks chunks.jsonl`; `--queries` (txt or jsonl); optional `--evalset` (06 JSONL with spans, like `climate_seed_spans.jsonl`); `--questions pack.jsonl` (a recorded pack keyed by `text_sha256`); `--n 5`; `--design both|chunks+q|q-only`; `--k 4`; `--tau` (default: calibrated from `paraphrase_of` pairs in the eval set, else the K9 provisional rule); `--rebuilds-per-month`, `--queries-per-month`; `--prices`; `--llm none` (default; `groq`/`haiku` refuse until `study/llmops/` exists, like P4's `--provider cohere`); `--report`. Checks Q1–Q12 and the recommendation logic exactly as in research §8 (Q5/Q6 tolerance 20% [P]). The climate example (pack + seeds) must reproduce K5, K6 (A0, A1 n = 5, A2 n = 5), K9 and K10 numbers. Refuse book text (any path under a folder named like the book). No network.

## 7. EXTERNAL and DERIVED numbers allowed in the kit

EXTERNAL (dated research facts): doc2query 21.8 vs 18.6 MRR@10, 61 vs 55 ms, 5 queries per passage, re-ranking leaderboard 36.8; docTTTTTquery 27.2 at 64 ms, 27.7, 80 samples / first 40, ≈ 8 TPU hours, ≈ $20; Doc2Query-- 70th percentile, "16% / 30% / 48%" (UNVERIFIED); HyPE "up to 42 / 45" percentage points (claimed); LlamaIndex default 5 questions; LangChain default k = 4; Groq 8,000 TPM / 200,000 TPD (plan UNVERIFIED); prices $0.075 / $0.30 and $0.10 / $0.50 per M. DERIVED: anything computed in the text from the numbers above (show the arithmetic).

## 8. Key numbers (each must appear in at least one of lesson / reading / questions; md check verifies they are printed by the measurement)

`0.708`, `0.781`, `0.653`, `0.547`, `0.9869`, `0.886`, `0.777`, `0.264`, `0.7054`, `0.7939`, `0.5351`, `582`, `485`, `3,575,808`, `596,096`, `4,271`, `42.5%`, `0.0061`, `0.0148`, `194`, `627.9`, `671.0`.

## 9. Banned wording (coach hidden-seed phrases, from the P2/P4 checks)

"a guide says", "well above zero", "narrow positive band", "who is right", "sixth", "add a pdf", "adding a document", "new document", "another pdf", "tenant", "300 pdf". Also never name the model that wrote the stand-in pack beyond "Claude" (no model ids in repo files).

## 10. Labels every piece must carry

- The question pack is a **stand-in** (Claude helpers, blind to the eval set), not the planned Groq/Haiku replay pack.
- The seeds are LLM-drafted, not human-verified; 8 answerable items show the mechanism, not a winner.
- Book pages are "per 04, not re-opened" (the book was not in the build container).
- MiniLM was rebuilt from an ONNX export in the build container, with parity checked against P4 (I6_FACTS §0).
- Measured / toy / formula badges on every number in the HTML lesson.
