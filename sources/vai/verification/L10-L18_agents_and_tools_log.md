# Verification log: VAI lessons 10–18: agents, context engineering and tool calling

[← Lesson guide](../L10-L18_agents_and_tools.md) · [← Guide index](../README.md)

Pass A re-opened every cited claim at its source line and tried to refute it. Pass B re-read every backend file with a different lens: control flow, missed issues, concept mapping and fit to your stack. Verdicts: confirmed / corrected / removed / unverified.
## Verification log (pass A)

Method: I opened every cited line. Library behaviour was checked only against copies on this machine (Gemini SDK 0.8.6, tiktoken), in scratch scripts outside the repo. Nothing in the repo was run.

| Lesson | Claim (short) | Verdict | Evidence file:line |
|---|---|---|---|
| L10 | Model chain with live test call, then list_models, then `gemini-pro` | confirmed | `backend/agent.py:79-115` |
| L10 | Read order: "4 endpoints, 37-60" | corrected (5 endpoints, 29-60) | `backend/main.py:29-60` |
| L10 | Step 1: POST /agent/act → act | confirmed | `backend/main.py:37-43` |
| L10 | Step 2: last 5 messages + up to 3 memories | confirmed | `backend/agent.py:144-163` |
| L10 | Step 3: "because" split into reasoning | confirmed | `backend/agent.py:177-181` |
| L10 | Step 4: sleep 0.5 s, echo "Executed:" | confirmed | `backend/agent.py:193-202` |
| L10 | Step 5: JSON self-eval, error → 0 % | confirmed | `backend/agent.py:204-243` |
| L10 | Step 6: COMPLETE / FAILED (max 5) / READY | confirmed | `backend/agent.py:73, 270-290` |
| L10 | README "Goal-driven autonomous" vs one step | confirmed | `README.md:34`; `backend/agent.py:245-300` |
| L10 | README "Production-ready" vs errors as actions | confirmed | `README.md:39`; `backend/agent.py:187-191` |
| L10 | [bug] memory query matches keys | confirmed | `backend/agent.py:53-54, 137, 147` |
| L10 | [misleading] self-eval grades an echo | confirmed | `backend/agent.py:202, 206-218` |
| L10 | [misleading] FAILED does not stop; count rises | corrected (sending a goal resets it) | `backend/agent.py:247-249, 254, 287-288` |
| L10 | [bug] blocking sleep in async path; dead code | confirmed | `backend/agent.py:198, 263, 116-127` |
| L10 | [ok-for-demo] live test call on first request | confirmed | `backend/agent.py:92` |
| L10 | test.sh only greps | confirmed (+ unconditional pass message) | `scripts/test.sh:9, 13, 20, 22-23` |
| L10 | decisions.json: 26 records, 22 errors (404/403/400) | corrected (9×404, 5×403, 5×400, 3×429; 4 real) | `data/agent_001_decisions.json` |
| L10 | Try this: keys are `interaction_<ts>`, query("Test") predictable | confirmed | `data/agent_001_memory.json`; `backend/agent.py:53-54` |
| L11 | Model `models/gemini-flash-latest` | confirmed | `backend/cot_agent.py:183` |
| L11 | Fallback chain never runs (constructor makes no call) | confirmed (SDK 0.8.6 constructor; pinned 0.4.1 not checked) | `backend/cot_agent.py:182-192` |
| L11 | Step 1: POST /api/reason | confirmed | `backend/main.py:45-55` |
| L11 | Step 2: two prompt forms; sync call in async | confirmed | `backend/cot_agent.py:21-46, 216` |
| L11 | Step 3: numbered → bullets → sentences (cap 10) | confirmed | `backend/cot_agent.py:52-66` |
| L11 | Step 4: conclusion extraction | confirmed (wording made precise) | `backend/cot_agent.py:69-84` |
| L11 | Step 5: clarity = share of steps passing all checks | corrected (mean of 3 per-step checks; length 21–199) | `backend/cot_agent.py:90-113` |
| L11 | Step 5: logic = entity overlap of neighbours | confirmed | `backend/cot_agent.py:116-135` |
| L11 | Step 5: overall weights 0.3/0.3/0.2/0.2 | confirmed | `backend/cot_agent.py:158-169` |
| L11 | Step 6: ≥ 0.7 served as few-shot | confirmed | `backend/main.py:73-79`; `backend/cot_agent.py:245-250` |
| L11 | README "Extends SimpleAgent" | confirmed | `README.md:51`; `backend/cot_agent.py:171` |
| L11 | README "few-shot for L12"; L12 never reads it | confirmed (grep of lesson12) | `README.md:55` |
| L11 | README "Multi-dimensional scoring" | confirmed | `README.md:31` |
| L11 | setup.sh key and `gemini-pro`; "read the folder" | corrected (generated compose file still has a key) | `setup.sh:39, 202, 1135`; `docker-compose.yml:11` |
| L11 | [misleading] cookie 0.49–0.57, 2+2 0.73, test 0.68 | corrected (2+2 is 0.73 in 1 of 3 runs; cookie answers verified correct) | `data/cot_memory.json` |
| L11 | [bug] regex cuts "**Step 1:**" | corrected (it cuts sub-numbered "Step 2.1:") | `backend/cot_agent.py:55`; `data/cot_memory.json` |
| L11 | [bug] conclusion not the final statement | corrected (softened; stored example cited) | `backend/cot_agent.py:77-80`; `data/cot_memory.json` |
| L11 | Tests: 5 offline tests, tidy traces | confirmed | `backend/test_cot.py:5-50` |
| L11 | test.sh also curls live API | confirmed | `test.sh:25-36` |
| L11 | Data: 10 real traces | confirmed | `data/cot_memory.json` |
| L11 | Try this: "8" vs "9" give identical scores | confirmed (holds if the wrong number is absent from the previous step) | `backend/cot_agent.py:90-169`; `backend/test_cot.py:14-16` |
| L12 | Model `gemini-2.0-flash-exp`; `embedding_model` unused | confirmed (grep) | `backend/main.py:25-26` |
| L12 | Step 1: seeding on every start, 8 Gemini calls | confirmed | `backend/main.py:95, 111, 301-325` |
| L12 | Step 2–3: classify → find_similar_examples | confirmed | `backend/main.py:118-132, 178, 328-331` |
| L12 | Step 4: hash of 3-char slices every 10 chars; cosine trims | confirmed | `backend/main.py:106-116, 136-138` |
| L12 | Step 5: prompt shape | confirmed | `backend/main.py:160-176` |
| L12 | Step 6: word "tokens"; confidence 0.85 / 0.70 | confirmed | `backend/main.py:197, 205` |
| L12 | Step 7: 429 fallback, confidence 0.75 | confirmed (also "quota" text; other errors 500) | `backend/main.py:207-239` |
| L12 | Step 8: accuracy formula; no labels | confirmed | `backend/main.py:48-51, 265, 288` |
| L12 | README "semantic embeddings" | confirmed | `README.md:46`; `backend/main.py:113` |
| L12 | README benchmarking; UI "Accuracy %" | confirmed | `README.md:7`; `frontend/src/components/BenchmarkPanel.js:36, 111` |
| L12 | README "Token counting" | confirmed | `README.md:10`; `backend/main.py:197` |
| L12 | [bug] salted hash; 5 vectors per sentence, 3–5 dims | confirmed (no PYTHONHASHSEED in `start.sh`/`Dockerfile`) | `backend/data/examples.json` |
| L12 | [bug] 42 = 8 × 5 + 2 | confirmed | `backend/data/examples.json`; `backend/main.py:325` |
| L12 | [misleading] constants / formulas | confirmed | `backend/main.py:205, 237, 288` |
| L12 | [misleading] mock fallback not flagged | confirmed | `backend/main.py:207-237, 254-260` |
| L12 | [security] key in main.py and start.sh | corrected (also `Dockerfile:15`, `docker-compose.yml:9`) | `backend/main.py:23`; `start.sh:12, 17` |
| L12 | test.sh greps only | confirmed | `test.sh:9, 20, 24` |
| L12 | Data: "8 distinct labelled intents" | corrected (10 distinct inputs, 8 labels, 42 rows) | `backend/data/examples.json` |
| L12 | Try this: MiniLM picks REFUND first | corrected (made a question: "check whether") | — |
| L13 | Default budget 30 000 from env | confirmed | `backend/services/context_optimizer.py:13, 26` |
| L13 | encoding_for_model("gpt-4") = cl100k | confirmed (offline tiktoken check) | `backend/utils/token_counter.py:10-14` |
| L13 | Fallback characters ÷ 4 | confirmed | `backend/utils/token_counter.py:32` |
| L13 | Bands 70 / 90 %; ratios 0.7 / 0.5 | confirmed | `backend/utils/token_counter.py:56-64`; `backend/services/context_optimizer.py:32-51` |
| L13 | Extractive: TF-IDF on own sentences, 1.5 / 1.3, top max(2, n×ratio) | confirmed | `backend/services/summarizer.py:42, 51-55, 73-85` |
| L13 | Abstractive: temp 0.3, 2048 tokens, 10 s, fallback | confirmed | `backend/services/summarizer.py:99-129` |
| L13 | Hybrid: 1.5 × ratio then 0.8 | corrected (abstractive only if extraction < 80 % of characters) | `backend/services/summarizer.py:141-151` |
| L13 | Truncate if ≥ 90 %; ×4 chars; last-20 % period | confirmed | `backend/services/context_optimizer.py:65-83, 122-137` |
| L13 | Savings $0.01 / 1K × 1M | confirmed | `backend/services/context_optimizer.py:139-151` |
| L13 | README "Precise"; "Gemini compatible" comment wrong | confirmed (comment is in an unreached fallback) | `README.md:44`; `backend/utils/token_counter.py:16-20` |
| L13 | README "Real-time cost analysis" | confirmed | `README.md:11`; `backend/services/context_optimizer.py:142` |
| L13 | README "Enabling L14"; never used there | confirmed (grep of L14) | `README.md:66-68`; L14 `backend/models/agent_state.py:33, 47` |
| L13 | [bug] budget not enforced; 60k vs 30k example | corrected (holds on the extractive path; Gemini path capped by 2048 output tokens) | `backend/services/context_optimizer.py:61-99`; `backend/services/summarizer.py:114, 141-151` |
| L13 | [bug] truncation never re-checked | confirmed | `backend/services/context_optimizer.py:124-125` |
| L13 | [misleading] `gemini-pro` retired → silent extractive | unverified (runtime; L10 log shows a 404) | `backend/services/summarizer.py:23, 127-129, 192` |
| L13 | [misleading] `quality_preserved` echo; ratio inverse | confirmed (ratio is in characters) | `backend/services/context_optimizer.py:93`; `backend/services/summarizer.py:183-184` |
| L13 | [shallow] query-agnostic | confirmed | `backend/services/summarizer.py:30-85` |
| L13 | [bug, UI] chars as tokens; last value as average | confirmed | `frontend/src/components/Summarizer.js:36-38`; `frontend/src/App.js:21` |
| L13 | [ok-for-demo] unused settings | confirmed (grep) | `backend/services/context_optimizer.py:14`; `backend/utils/token_counter.py:34-48` |
| L13 | Tests: 3 token-counter tests only | confirmed | `backend/tests/test_token_counter.py:4-27` |
| L13 | demo_test inputs "about 45 vs 100, 20 vs 50" | corrected (measured 41 and 18 cl100k tokens) | `demo_test.sh:44-67` |
| L13 | Swap: gpt-oss uses `o200k_harmony` | unverified (external fact, not in repo; labelled) | — |
| L14 | Model `gemini-1.5-flash` | confirmed | `backend/services/agent_engine.py:23` |
| L14 | Step 1: POST /api/chat | confirmed | `backend/app/main.py:79-89` |
| L14 | Step 2: Redis then Postgres; errors → None | confirmed | `backend/services/state_manager.py:58-95` |
| L14 | Step 3: last 5 turns; word "tokens" | confirmed | `backend/services/agent_engine.py:48, 86-94, 108` |
| L14 | Step 4: version + 1, upsert, snapshot %5, setex 3600 | confirmed | `backend/services/state_manager.py:104-128, 144` |
| L14 | README diff/rollback read snapshots; not exercised | confirmed | `README.md:33`; `backend/services/state_manager.py:165-170, 197-200`; `demo.sh` |
| L14 | README error handling vs swallowed errors | confirmed | `README.md:34`; `backend/services/state_manager.py:93-95`; `backend/services/agent_engine.py:65` |
| L14 | [misleading] "optimistic locking" not checked | confirmed | `backend/services/state_manager.py:100, 113-121` |
| L14 | [bug, likely] JSONB returned as string | unverified (asyncpg default; no codec confirmed) | `backend/app/main.py:31`; `backend/services/state_manager.py:86, 206` |
| L14 | [bug] rollback version reset → snapshot collision | confirmed (by reading) | `backend/services/state_manager.py:124, 150, 207, 133-137` |
| L14 | [ok-for-demo] demo mode on invalid key | corrected (real trigger condition; line-119 test can never match) | `backend/services/agent_engine.py:118-126, 140-445` |
| L14 | Tests are `pass`; test.sh says passed | confirmed | `backend/tests/test_state_manager.py:17-32`; `test.sh:25` |
| L15 | Model ids for chat and judge | confirmed | `backend/gemini_client.py:14`; `backend/goal_tracker.py:7` |
| L15 | Step 1: POST /messages, load, append | confirmed | `backend/api.py:46-52`; `backend/conversation_engine.py:24-29` |
| L15 | Step 2: `/goal` with no LLM call | confirmed | `backend/conversation_engine.py:32-36`; `backend/models.py:107-111` |
| L15 | Step 3: all history in prompt | confirmed | `backend/gemini_client.py:331-337` |
| L15 | Step 4: 3 tries, 1 s / 2 s; reply-only tokens | confirmed | `backend/gemini_client.py:339-364` |
| L15 | Step 5: YES/NO judge, last 10, errors NO | confirmed | `backend/goal_tracker.py:9-33` |
| L15 | Step 6: INSERT OR REPLACE | confirmed | `backend/memory_manager.py:32-41` |
| L15 | README "Persistent conversation state" | confirmed | `README.md:6` |
| L15 | demo_test hits ML / main types / thank-you branches | corrected (msgs 3–4 hit the greeting via "machine"; ML branch unreachable) | `scripts/demo_test.py:21-27`; `backend/gemini_client.py:37, 183` |
| L15 | [misleading] canned library; note only on first reply | confirmed | `backend/gemini_client.py:21-323, 25-28, 318-320` |
| L15 | [bug] "hi" in "this" / "which" | confirmed (scratch substring check) | `backend/gemini_client.py:37` |
| L15 | [bug] "ai" matches "explain" | corrected ("explain" caught earlier; "available" reaches it) | `backend/gemini_client.py:31-34, 49, 215` |
| L15 | [bug] invalid key still retries and sleeps | corrected (first request only; then direct fallback) | `backend/gemini_client.py:327-329, 350-358` |
| L15 | [shallow] unbounded history; prompt tokens ignored | confirmed | `backend/gemini_client.py:331, 343-346`; `backend/models.py:99-103` |
| L15 | [shallow] criteria default "User satisfaction" | confirmed | `backend/goal_tracker.py:14`; `backend/conversation_engine.py:34` |
| L15 | Tests: model tests; e2e asserts 4 messages | confirmed | `tests/test_models.py:6-21`; `scripts/test.sh:19-44` |
| L16 | SDK 0.8.3; model with `tools=` | confirmed | `setup.sh:22, 247-250` |
| L16 | Demo key default; demo data | confirmed | `setup.sh:32, 86-105` |
| L16 | Step 1: sync call from async handler | confirmed | `setup.sh:329-340` |
| L16 | Step 2: last 5 turns as text | confirmed | `setup.sh:256-265` |
| L16 | Step 3: hand-written schema, required city | confirmed | `setup.sh:145-160, 270` |
| L16 | Step 4: first function call; execute_tool catches | confirmed | `setup.sh:166-190, 275-286` |
| L16 | Step 5: prose second call; return | confirmed | `setup.sh:297-307, 310` |
| L16 | README "Multi-turn loops" / "real API" | confirmed | `setup.sh:1321-1322` |
| L16 | [bug] only first tool call runs | confirmed | `setup.sh:307, 1300-1303` |
| L16 | [bug] second call with tools → `.text` raises → 500 | confirmed (SDK 0.8.6 `text` property) | `setup.sh:301-306, 312-314` |
| L16 | [shallow] prose result; calls not in history | corrected (softened wording) | `setup.sh:257-259, 297-304` |
| L16 | [bug] case-sensitive lookup; in-memory store | confirmed | `setup.sh:97, 211` |
| L16 | test.sh "curls 4 endpoints", asserts nothing | corrected (4 requests to 3 endpoints) | `setup.sh:1278-1306` |
| L17 | Model list; always `gemini-2.5-flash` | confirmed (SDK 0.8.6 constructor) | `backend/main.py:167-191` |
| L17 | Step 1: registration from `model_json_schema()` | confirmed | `backend/main.py:52-60`; `backend/tool_registry.py:20-36` |
| L17 | Step 2: converter keeps type/desc/enum/required | confirmed | `backend/tool_registry.py:48-86, 88-98` |
| L17 | Step 3: chat with tools | confirmed | `backend/main.py:162-197` |
| L17 | Step 4: 10 iterations, all calls, truthiness check | confirmed | `backend/main.py:202-219` |
| L17 | Step 5: arguments converted with `MessageToDict` | corrected (it raises on SDK 0.8.6; `dict()` fallback runs, floats) | `backend/main.py:233-242` |
| L17 | Step 6: FunctionResponse parts sent together | confirmed | `backend/main.py:257-284` |
| L17 | Step 7: in-memory metrics | confirmed | `backend/main.py:32-42, 88-105` |
| L17 | README "Type coercion" test absent | confirmed | `README.md:60`; `tests/test_schemas.py` |
| L17 | Quota message promises auto-retry | confirmed | `backend/main.py:310` |
| L17 | setup.sh uses older model and converter | confirmed | `setup.sh:205-239, 495-496` |
| L17 | [misleading] random weather | confirmed | `backend/tools.py:19-29` |
| L17 | [bug] `get_time` ignores time zone | confirmed | `backend/tools.py:38-49` |
| L17 | [misleading] placeholder search | confirmed | `backend/tools.py:58-64` |
| L17 | [shallow] constraints dropped | confirmed | `backend/tool_registry.py:52-68` |
| L17 | [shallow] Optional / nested → "string" | confirmed (by reading; no such field today) | `backend/tool_registry.py:53` |
| L17 | [bug] sync `send_message` in async | confirmed | `backend/main.py:197, 277` |
| L17 | 6 offline tests | confirmed (list clarified: 3 valid-input tests) | `tests/test_schemas.py:11-42` |
| L17 | Try this: schema vs declaration; 5.0 test | confirmed (doable offline) | `backend/schemas.py:75-97`; `backend/tool_registry.py:38-86` |
| L18 | Default model `gemini-2.0-flash` | confirmed | `backend/main.py:33-37` |
| L18 | Step 1: start-up test call classification; fallback default on | confirmed (+ invalid-key class) | `backend/main.py:325-427, 579-582` |
| L18 | Step 2: POST /chat → loop, max_turns 10 | confirmed | `backend/main.py:837, 848-852, 666-673` |
| L18 | Step 3: full history + tools each turn | confirmed | `backend/main.py:681-684, 542-563` |
| L18 | Step 4: bare hasattr; 30 s timeout; `{"result": …}` | confirmed | `backend/main.py:164-210, 702, 723-749` |
| L18 | Step 5: history append; max turns error | confirmed | `backend/main.py:752-754, 817-826` |
| L18 | Step 6: stats over /ws every 2 s | confirmed | `backend/main.py:212-228, 1047-1065` |
| L18 | README "SafeExecutor" absent | confirmed (grep) | `README.md:61` |
| L18 | README "foundation for L19 RAG"; constants | confirmed | `README.md:51`; `backend/main.py:117-130` |
| L18 | STATUS_REPORT "production-ready" with 429; "never run" | corrected (softened to "no evidence of a successful run") | `STATUS_REPORT.md:10` |
| L18 | [bug] `hasattr` always true for proto Part | confirmed (scratch check, SDK 0.8.6) | `backend/main.py:702, 724-737` |
| L18 | What the API does after an empty-name call | unverified (runtime) | `backend/main.py:740-754` |
| L18 | L16 and L17 have the truthiness check | confirmed | L16 `setup.sh:278`; L17 `backend/main.py:212` |
| L18 | [bug] timeout does not return early | confirmed (executor exit waits for the thread) | `backend/main.py:178-201` |
| L18 | [bug] double-escaped fallback regexes | confirmed (literals read as text, matched in scratch) | `backend/main.py:454, 465, 467, 472, 507` |
| L18 | [misleading] simulated tools | confirmed | `backend/main.py:72-75, 87-97, 102-114` |
| L18 | [shallow] no validation; stale stat; shared executor; sync call | confirmed | `backend/main.py:143, 179, 666-667, 681, 829` |
| L18 | Tests: direct tool runs "offline"; test.sh always passes | corrected (import of `main` triggers start-up call if a key is set) | `scripts/test_tools_direct.py:11, 25, 33-41`; `scripts/test.sh:30` |
| L18 | Try this: L17 211-215 vs L18 702-727 | confirmed | L17 `backend/main.py:211-215`; L18 `backend/main.py:702-727` |
| Summary | L10 biggest problem | confirmed | `backend/agent.py:53-54, 147, 202` |
| Summary | L11 biggest problem | confirmed | `backend/cot_agent.py:90-169`; `data/cot_memory.json` |
| Summary | L12 biggest problem | confirmed | `backend/main.py:113, 288` |
| Summary | L13 biggest problem | confirmed (wording: "never checked") | `backend/services/context_optimizer.py:61-99` |
| Summary | L14 biggest problem | confirmed | `backend/services/state_manager.py:86, 113-121, 207` |
| Summary | L15 biggest problem | confirmed | `backend/gemini_client.py:21-323, 331` |
| Summary | L16 biggest problem | confirmed | `setup.sh:297-307` |
| Summary | L17 biggest problem | confirmed | `backend/tools.py:19-29`; `backend/tool_registry.py:52-68` |
| Summary | L18 "timeout doesn't fire" | corrected ("does not return early") | `backend/main.py:178-201` |
| Cross | Committed key locations | corrected (+ L11 compose, L12 Dockerfile and compose; L15–L18 none) | `lesson11/cot-reasoning-evaluator/docker-compose.yml:11`; `lesson12/l12-few-shot-learning/Dockerfile:15`, `docker-compose.yml:9` |
| Cross | Dead model fallbacks; "L10 at start-up" | corrected (L10 on the first request) | L10 `backend/agent.py:92, 168`; L18 `backend/main.py:338, 829` |
| Cross | Tokens mostly words; no `usage` field read | confirmed (grep) | L12 `main.py:197`; L14 `agent_engine.py:108`; L15 `gemini_client.py:345` |
| Cross | Sync SDK calls in async handlers | confirmed | as listed |
| Cross | Unit tests only in L11, L13, L17 | corrected (+ L15 model tests, L18 direct script) | L15 `tests/test_models.py:6-21`; L18 `scripts/test_tools_direct.py:33-41` |
| Cross | Old SDK; most ids retired | unverified (L10 log 404s confirm two ids; rest not checkable) | L10 `data/agent_001_decisions.json` |

## Verification log (pass B)

Method: I re-read every backend `.py` file of each lesson in full (L16: the `setup.sh` heredocs), plus READMEs, tests and data files. I followed one request through the code and compared it with each "How it works" section. Numbers marked "computed" come from the lesson's own data files, read offline with `python -I` from outside the repo. Key values were never printed (grep output was redacted). Nothing in the repo was run, installed or changed. Paths are relative to each lesson's project folder.

| Lesson | Item | Change | Evidence file:line |
|---|---|---|---|
| All | "How it works" steps vs real control flow | confirmed; only the clarifications listed below were needed | each lesson's backend files |
| All | Line numbers in the guide | re-checked while reading; all within 3 lines | as cited |
| All | Secrets in this guide | none present (grep for the key prefix: 0 hits); key locations re-confirmed, values not shown | cross-lesson list |
| L10 | Relevance and concepts | A5 marked counter-example; added M3 (counter-example) and [LLMOps] | `backend/agent.py:193-202, 204-243, 270-279` |
| L10 | Step 2 | clarified: 5 messages is about 2.5 turns | `backend/agent.py:132-133, 146` |
| L10 | Step 5 | added: evaluator sees only earlier turns | `backend/agent.py:210, 282` |
| L10 | Memory-key bug | added the reverse case ("in" or "T" matches every key) | `backend/agent.py:54, 136-137` |
| L10 | New [misleading] | 3 of 4 real records self-graded 100 % "goal achieved" on echoed plans (computed) | `data/agent_001_decisions.json` (last three records) |
| L10 | What to take | made concrete (JSONL trace fields); added self-grading warning | — |
| L11 | Relevance and concepts | M3, V4 marked counter-example; P7 qualified; [LLMOps] as counter-example | `backend/cot_agent.py:86-169` |
| L11 | New data point | 2-step train trace scored 0.73 with logic 1.0 (computed) | `data/cot_memory.json` |
| L11 | New [misleading] | substring "so" and capitalised-word checks pass for nearly any step | `backend/cot_agent.py:92-95, 104, 108` |
| L11 | What to take | tied to your Cohere judge-at-the-end plan with TPR/TNR | — |
| L12 | Relevance and concepts | P4, C4, M4 marked counter-example | `backend/main.py:106-116, 288` |
| L12 | Swap line | corrected "that alone makes the lesson real": the benchmark still has no labels | `backend/main.py:48-51, 288` |
| L12 | Steps 3 and 8 | added: throwaway Gemini call per query (even k = 0); 2 calls per classification | `backend/main.py:111, 118-123, 265-283` |
| L12 | New [misleading] | cosines from stored vectors: same-sentence copies 0.82 vs different sentences 0.83 (computed) | `backend/data/examples.json`; `backend/main.py:113, 134-146` |
| L12 | New [misleading] | `latency_ms` includes the throwaway call | `backend/main.py:111, 180-183, 241` |
| L12 | New [shallow] | raw reply never mapped onto the label set | `backend/main.py:202` |
| L12 | What to take, Try this | concrete Cohere `input_type`, normalise, NumPy, dedup, vector cache; offline shortcut | — |
| L13 | Relevance and concepts | X2, D2 marked counter-example; X3 scope and P3 use qualified | `backend/services/summarizer.py:30-85`; `backend/services/context_optimizer.py:142` |
| L13 | `compression_ratio` bullet | added: truncation branches compute it in tokens | `backend/services/context_optimizer.py:75, 111` |
| L13 | New [misleading] | missing NLTK `punkt` → first half of the text, still labelled "extractive" (NLTK behaviour not run) | `backend/main.py:18-23`; `backend/services/summarizer.py:62-64` |
| L13 | New [shallow] | "moderate" band compresses text that already fits; no reserve for question or answer | `backend/utils/token_counter.py:59-61`; `backend/services/context_optimizer.py:46-48` |
| L13 | What to take, Try this | reasoning-token reserve for `gpt-oss-20b`; eval-set comparison; cached `usage`; project PDFs only | — |
| L14 | New [misleading] | rollback returns True even if its save fails; reported version is off by one | `backend/services/state_manager.py:104, 207, 210-213`; `backend/app/main.py:120` |
| L14 | New [misleading] | model errors saved as agent turns (runtime part UNVERIFIED) | `backend/services/agent_engine.py:59-65, 127-138` |
| L14 | New [shallow] | `tiktoken` installed but unused | `backend/requirements.txt:18` |
| L14 | What to take | tied to your record/replay cache; loud failure on a replay miss | — |
| L15 | Relevance and concepts | Q1, X3 marked counter-example; M3 qualified | `backend/gemini_client.py:331-337` |
| L15 | README vs code | added: system prompt claims memory of previous conversations | `backend/conversation_engine.py:40-41`; `backend/gemini_client.py:331` |
| L15 | New [bug] | YES/NO parse misses "**YES**"; sync judge call; one extra call per goal per turn | `backend/goal_tracker.py:18-19, 28-32` |
| L15 | What to take, Try this | caching, structured verdict, book-text rule | — |
| L16 | Steps and settings | confirmed | `setup.sh:233-314` |
| L16 | New [security] | OpenWeatherMap key sent in a plain-http query string | `setup.sh:108-115` |
| L16 | What to take, Try this | caching; plain Python before LangGraph | — |
| L17 | Step 6 | added: hitting the cap still returns success | `backend/main.py:205, 286-292` |
| L17 | New [misleading] | "Validation Success Rate" counts only manual `/validate` calls | `backend/main.py:100-102, 113-138`; `backend/tool_registry.py:107-145`; `frontend/src/components/MetricsDashboard.js:63-66` |
| L17 | New [misleading] | capped or all-failed queries counted as success | `backend/main.py:205, 286-292` |
| L17 | New [shallow] | ASCII-only location whitelist rejects valid names | `backend/schemas.py:31-33` |
| L17 | New [shallow] | one error shape for three failure stages | `backend/tool_registry.py:123-145` |
| L17 | What to take, Interview | per-stage validation counters; strict-schema nuance | — |
| L18 | Relevance and concepts | added C4 (counter-example) | `backend/main.py:117-130` |
| L18 | `hasattr` bullet | added: final-answer branch unreachable in LLM mode | `backend/main.py:689, 702, 704-717` |
| L18 | New [bug] | per-tool average latency biased by failures | `backend/main.py:187, 216` |
| L18 | New [shallow] | `max_turns` has no upper bound | `backend/main.py:837, 852` |
| L18 | New [ok-for-demo] | `/api-key-status` spends a live call per request | `backend/main.py:970-971` |
| L18 | What to take | turn cap, record/replay, LangGraph and LangSmith only after the mechanism | — |
| L18 | Interview | corrected: an asyncio task cancels only at an await; blocking code needs a subprocess | — |
| Summary | Concepts and biggest-problem cells | updated to match the lesson headers (L10–L15, L17, L18) | Block summary |
| Cross | New patterns | mislabelled metrics; self-grading; capitalised "API key" test; L15 judge added to sync list | L12 `main.py:111, 180-183`; L17 `main.py:100-102`; L18 `main.py:187, 216`; L14 `agent_engine.py:119`; L15 `gemini_client.py:350`, `goal_tracker.py:18` |
