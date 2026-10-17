# VAI lessons 49, 54, 59, 64, 69: multi-agent systems and operations

[← Guide index](README.md) · Course folder: `C:\Yash\New-Work\RAG\vertical-ai-agents-main\` · Checked 2026-10-17 · Log: [verification/L49-L69_multi_agent_and_ops_log.md](verification/L49-L69_multi_agent_and_ops_log.md)

**What this is:** the guide to VAI lessons 49, 54, 59, 64 and 69: multi-agent systems and operations.
**What this is not:** the course code, or a run of it. Nothing in the course was run or copied.

**How to read this file:**
- A `file:line` is relative to the project folder named in the lesson heading.
- **UNVERIFIED** marks behaviour that depends on a library version or on Gemini.
- **(counter)** or † means the lesson names a technique without building it. Read it to learn what is missing.
- Tags: **[bug]** the code does the wrong thing · **[misleading]** a label, message or number claims more than the code does · **[shallow]** it works, but is too thin for your project · **[ok-for-demo]** fine for a demo, not for real use · **[LLMOps]** material for your LLMOps notebooks · **[Interview]** worth practising for interviews.
- "I" means the reviewer who checked the code. Each lesson was checked by a reader, a fact-check pass and a completeness pass; the log has every verdict.

**Notes for this block:**
- None of these five lessons does retrieval. Their value for you is in LLMOps patterns (tracing, metrics, eval-harness shape) and in how those can mislead.
- Only lesson54 has a `setup.sh`. Its generated files match it except `backend/routers/chat.py`, which adds a missing `import json`.

---

## L49 · CrewAI role-based crew  (`lesson49/l49-crewai-role-based/`)

**What the code teaches, in one line:** CrewAI agents are role/goal/backstory prompt strings. A "sequential crew" feeds each task's output into the next task as context.
**What it is not:** Not research. The "Researcher" has no tools and no retrieval, so it answers from the model's memory. It is also not a delegating or hierarchical crew (`allow_delegation=False`, `Process.sequential`).
**Relevance to your RAG study:** Low. Concepts: A5 (counter-example: a "Researcher" agent with no retrieval tool), P7 (counter-example: role prompts with no grounding context). [Interview]
**Stack:** FastAPI, `crewai==0.80.0` (`backend/requirements.txt:3`). LLM: `gemini/gemini-2.0-flash` through CrewAI's `LLM` wrapper (`backend/crew.py:9-13`). No embeddings, no vector store. The React UI streams three agent cards over SSE, then shows the final "Technical Briefing".
**Swap to your stack:** easy. The model id uses the LiteLLM-style `provider/model` form (`gemini/gemini-2.0-flash`, `crew.py:10`), so you change one string to a Groq id. That CrewAI 0.80 sends it through LiteLLM, and whether it passes `reasoning_effort` on, is library behaviour I could not confirm by reading this repo (UNVERIFIED).

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/crew.py` | Three agents and three tasks, plus the run function and a demo fallback | 19-59, 62-104, 113-166 |
| 2 | `backend/main.py` | `/run-crew`, plus a `/stream-crew` SSE that runs on a timer | 66-75, 78-111 |
| 3 | `test.sh` | A smoke test over HTTP | 15-23 |

### How it works, step by step
1. `POST /run-crew` runs `run_crew` in a thread (`main.py:72`). The React UI does not call it. It opens an `EventSource` on `GET /stream-crew` (`frontend/src/App.js:108-109`), which runs the same `run_crew` in a thread and sends timed events (`main.py:91-111`).
2. `build_crew` makes three agents. Each has `max_iter=3` (`crew.py:29, 43, 57`). The researcher and analyst share one LLM at temperature 0.3; the writer gets its own at 0.5 (`crew.py:8, 16, 55`).
3. The research and writing task descriptions have the topic pasted in with f-strings (`crew.py:64, 94`). The analysis task description has no topic at all; only the analyst's goal does (`crew.py:35, 76-81`). So `kickoff(inputs=...)` at `crew.py:117` has no `{topic}` placeholders left to fill.
4. Context chaining: the analysis task gets `context=[research_task]`, and the writing task gets both earlier tasks (`crew.py:88, 103`).
5. Each output is paired with its agent by list index (`crew.py:120-125`).
6. If anything raises, the `except` branch returns three canned "[DEMO MODE]" outputs and a canned briefing, with the same keys and counts as a real run (`crew.py:134-166`).

### README vs code
- The README says the generator is `../setup.sh` (`README.md:16`). There is no `setup.sh` in `lesson49/`.
- The README describes the stack only. It makes no quality claims.

### Where it is thin or wrong
- [misleading] Any exception, such as a missing key, returns a canned "[DEMO MODE]" result with `agent_count: 3` (`crew.py:134-166`). So the HTTP 500 path at `main.py:74-75` never fires for LLM errors.
- [bug] Docker Compose sets `GEMINI_API_KEY=` to an empty value (`docker-compose.yml:9`). `load_dotenv()` (`main.py:17`) does not override a variable that already exists, so inside Docker the crew falls back to the demo unless you edit that line.
- [misleading] The SSE "agent_start" events fire after fixed sleeps of 2, 14 and 26 s, one after another (`main.py:97-100`). They do not follow real progress, and every streamed run takes at least 42 s before results are sent.
- [misleading] The run time the UI shows is fake as a latency number. It is browser time from the click to `crew_complete` (`frontend/src/App.js:106, 134`), so it includes the 42 s of fixed sleeps. A demo-mode run that failed in milliseconds still shows about 42 s. You can never see the crew's real latency in the UI.
- [ok-for-demo] The demo fallback pastes the raw provider exception text into `final_output` (`crew.py:154`), and the UI displays it. That shows internal error details to the user.
- [shallow] `sse-starlette` is declared (`backend/requirements.txt:6`) but unused: the stream is FastAPI's own `StreamingResponse` (`main.py:14, 118-121`). `build_crew` is imported but unused (`main.py:19`).
- [misleading] The backstories invent credentials, such as "shipped 40+ production AI systems" (`crew.py:36-39`). A persona string makes no output more factual.
- [bug] `cleanup.sh` stops every running Docker container on the machine (`cleanup.sh:15`). It then prunes stopped containers, all unused images (`-af`, so in effect every image, since nothing is running now), networks and unused volumes (`cleanup.sh:27-30`). Which volumes `volume prune` removes depends on your Docker version (UNVERIFIED). Do not run it.

### Tests and data
- `test.sh:19-21` checks only that there are 3 agents, 3 tasks and more than 100 characters of output. The demo fallback passes all three. No data files.

### What to take for your project
- Skip the code. Keep one idea for A5: an "agent" with no retrieval tool is just a prompt, so it is not RAG.
- **A5, later (when your gates open Phase 10; plain Python first, then LangGraph):** when you build an agent step, give it your ragkit `retrieve()` as its only tool. Add a check that fails when the final answer cites no chunk id from the retrieved set. That check is exactly what `test.sh:19-21` lacks.
- **M4 / D3:** any gate you write must fail on fallback output. Tag every fallback result (for example `fallback=True` in your trace), and make your eval script count it as a failure, not as a short answer.

### Try this
- (15 min) Read `crew.py:134-166` and `test.sh:19-21` side by side. Write down why the test passes with no API key. Then write one assertion that would fail in demo mode, for example "output does not contain `[DEMO MODE]`".

### Interview angle
- *Q: What do role, goal and backstory actually do in CrewAI?* A: They are text placed into the agent's prompt. They shape style and focus, but they add no knowledge or tools. Grounding still needs retrieval or tools.

---

## L54 · Agent personalisation  (`lesson54/l54-agent-personalization/`)

**What the code teaches, in one line:** It stores a user profile in SQLite and lets an LLM infer an 8-number "preference vector" from recent chats. It picks a persona by cosine similarity against 4 hand-made archetype vectors, then puts a persona system prompt in front of the message.
**What it is not:** Not memory retrieval. It never embeds user memories, never searches them by similarity, and never puts past chats into the reply prompt. There is no ChromaDB and no Redis, whatever the docstring says.
**Relevance to your RAG study:** Low. Concepts: no RAG concept at the core. P4 (real cosine on toy vectors: a cautionary example), X3 (counter-example: "budget-aware" prefix tiers with hard-coded, unmeasured token costs), A4 (counter-example: feedback stored but never used), D4 (partial: a consent gate on inference only, plus right-to-forget delete).
**Stack:** FastAPI, aiosqlite, numpy, `google-generativeai`. LLM: `gemini-2.0-flash` (`backend/routers/chat.py:23`, `backend/services/inference.py:56`). No embeddings, no vector store. The React/Vite UI shows profile cards, a preference radar chart, chat, a persona compare tab and analytics.
**Swap to your stack:** easy. There are two `generate_content` call sites to change to a Groq chat call.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/services/router.py` | Archetypes, cosine persona pick, persona prompts | 12-17, 47-59 |
| 2 | `backend/routers/chat.py` | Profile → persona → prefix → LLM → log the interaction | 94-151 |
| 3 | `backend/services/inference.py` | Builds the history corpus, gets JSON from the LLM, adds noise, checks drift | 58-161 |
| 4 | `backend/services/compressor.py` | Three tiers of prompt prefix by remaining budget | 42-61 |

### How it works, step by step
1. `POST /chat` reads the `X-User-Id` header with no auth check. It loads the profile, or auto-creates one (`chat.py:95-106`).
2. The budget fraction from the client becomes `used_tokens` out of 8000 (`chat.py:109-112`). The remaining fraction is the minimum of tokens, steps and time (`models/budget.py:14-18`).
3. If the profile has a stored vector, the persona is the archetype with the highest cosine similarity to it (`router.py:47-59`). With no stored vector, for example a new anonymous user, the persona is DEFAULT (`chat.py:115-121`). The four seed users get a vector at startup (`main.py:70-78`). Chat always recomputes the persona from the stored vector. It never reads the stored `persona` column.
4. The prefix tier is RICH above 0.6, STANDARD above 0.3, MINIMAL otherwise (`compressor.py:47-61`).
5. The prompt is the prefix plus the user message, nothing else: no chat history (`chat.py:129`). The "token count" is a word count (`chat.py:131`).
6. Every message and reply is saved to SQLite with the persona and tier (`chat.py:134-142`). There is no consent check on this write.
7. Inference (`POST /profiles/{id}/infer`, `routers/profiles.py:80-84`) runs only if the user gave behavioural consent (`inference.py:64-65`). It uses the last 20 interactions, with each user and agent message cut to 300 characters, and asks the LLM for 8 floats as JSON (`inference.py:67-88`). The drift threshold is an L2 distance of 0.3 (`inference.py:46`).
8. The persona comes from the clean new vector (`inference.py:141`). The stored copy gets Laplace noise (`inference.py:115, 144-146`), but the API response returns the clean vector (`inference.py:152`).

### README vs code
- The README covers only start, stop and cleanup. The store docstring promises "SQLite + ChromaDB + Redis hot cache" (`db/store.py:2`); the code is SQLite only.
- `config.DB_PATH`, `REDIS_URL` and `PRIVACY_MODE` are never read (`config.py:3-5`). The store hard-codes its path (`store.py:16`).

### Where it is thin or wrong
- [bug] The persona pick is skewed toward ANALYST. Every value is in [0,1], so the cosines crowd together. For the four seed users and the all-0.5 vector, all 20 scores lie between about 0.79 and 0.98. I computed this myself in a scratch NumPy file from the constants at `router.py:13-16` and the seeds at `main.py:48-57`, without running the app. The "VP Eng" seed (`main.py:49-50`) scores ANALYST 0.934 against EXECUTIVE 0.910, so startup stores ANALYST for her (`main.py:73-78`). Yet the seeded chat labels that user EXECUTIVE (`main.py:84`). An all-0.5 vector would also map to ANALYST, and `GET /profiles/{id}/persona` would report a "confidence" of 0.9755 (`routers/profiles.py:97-105`). A brand-new user with no stored vector gets DEFAULT instead (`chat.py:119-121`, `profiles.py:94-95`). In the same scratch check, ANALYST won about 45% of 20,000 uniform random vectors, where an even split would give 25%.
- [bug] The privacy noise causes false drift. The stored vector carries Laplace noise (`inference.py:115, 144-146`). The next run compares a clean vector against that noisy one (`inference.py:119-123`). In my scratch simulation of the noise at `profile.py:64-70`, the noise alone pushed the L2 distance past the 0.3 threshold about 97-98% of the time (mean L2 about 0.63-0.65 for the seed vectors).
- [misleading] "Differential privacy, epsilon=0.1" really draws noise at scale 1/ε and then multiplies it by 0.02 (`profile.py:67`), so the real Laplace scale is 0.2. If you assume a sensitivity of 1 per dimension, that is an effective ε of about 5 per dimension, and more across all 8. The code does no sensitivity analysis.
- [misleading] The noise protects nothing. The API hands the clean vector back to the caller (`inference.py:152`, and the fallback at `:107`), so only the stored copy is noised. That stored copy is the one chat routes on.
- [bug] The persona the inference endpoint reports is often not the one chat uses. Inference reports and stores the persona of the clean vector (`inference.py:141-146`). Chat recomputes the persona from the stored, noisy vector (`chat.py:115-118`). I ran a scratch NumPy simulation, using each seed vector as the "clean" inferred vector, the noise from `profile.py:64-70` and 20,000 draws. The noisy copy picked a different persona about 15% of the time for the analyst seed, and about 48-50% for the exec, dev and junior seeds.
- [bug] `create_profile` uses `INSERT OR REPLACE` (`store.py:97-101`). A second `POST /profiles` with an existing `user_id` silently wipes that user's preference vector, persona, consent and interaction count.
- [misleading] Consent gates only inference. Every chat message is stored for every user, anonymous ones too (`chat.py:103-106, 134-142`). `consent_embedding` is stored (`store.py:24`) but nothing reads it, and there are no embeddings at all.
- [shallow] The inference corpus mixes in the agent's own replies (`inference.py:72-76`). When Gemini is down, those replies are the canned "[Offline demo …]" strings. So the LLM judges the user's style partly from text the persona wrote. The returned JSON is not validated: `from_dict` keeps any float, with no clamp to [0,1], and a missing key silently stays 0.5 (`profile.py:84-87`).
- [misleading] The persona-compare tab ignores each user's preferences. `/chat/compare` builds every prompt from the default all-0.5 vector (`chat.py:177`, `compressor.py:63-66`), so only the persona system prompt differs between users.
- [misleading] First-load analytics are seeded. Five demo interactions with a fixed `token_cost` of 140 and hand-picked persona and tier labels are inserted at startup (`main.py:83-91`). The `budget_usage_log` table is created (`store.py:61-71`) but never written.
- [misleading] The personalisation token costs of 85, 32 and 8 are hard-coded, not measured (`compressor.py:50, 55, 60`).
- [ok-for-demo] Gemini errors return canned "[Offline demo]" replies (`chat.py:26-75`), and failed inference falls back to the explicit preferences (`inference.py:91-112`).
- [shallow] `feedback_score` is stored (`store.py:218-224`) but nothing reads it. The ADK export is just base64 JSON (`profile.py:75-82`).

### Tests and data
- `scripts/test.sh:20-53` has 11 curl checks that grep for a key in the JSON. Only "constrained budget → MINIMAL" (`:43-47`) tests real logic. The "Delete profile" check cannot fail, because `delete_profile` returns `True` even for an unknown id (`store.py:172-181`, `test.sh:53`). The script never exits non-zero (`:57`). There is no practice data.

### What to take for your project
- Skip it for RAG. Keep one lesson for P4: cosine similarity on all-positive, hand-made vectors separates poorly. Centre the vectors, or use a distance, before you trust "confidence".
- **P4 / C4, concrete:** in your P4 notebook, embed about 200 chunks of your project corpus (not book text) with `embed-v4.0` through your cached client, and the same chunks with MiniLM. Plot the cosine scores of random chunk pairs. The baseline shows you why a fixed "score > 0.8 means relevant" rule is unsafe. Set any relevance threshold (V3 abstention) from labelled pairs instead.
- **D4:** consent and deletion must cover what you store, not only what you infer. Your local traces hold queries and chunk text, so give `results.jsonl` a delete-by-id path and keep it off any external tracing service.

### Try this
- (20 min) In a scratch NumPy file, copy the 4 archetype numbers (`router.py:13-16`) and compute the cosine for `[0.5]*8` and for the exec seed (`main.py:49-50`, other dimensions 0.5). Then subtract 0.5 from every vector and recompute. Look at whether EXECUTIVE now wins for the exec seed. Note that `[0.5]*8` becomes the zero vector after centring, so its cosine is undefined; the router returns DEFAULT for a zero-length vector (`router.py:51-52`).

### Interview angle
- *Q: How would you personalise an assistant without leaking or drifting?* A: Keep explicit preferences apart from inferred ones, and ask for consent before inferring. Measure drift against the clean stored value, not a noised copy. Only call it differential privacy if you can state the sensitivity and the real ε.

---

## L59 · Multi-agent system evaluation and debugging  (`lesson59/l59-mas-eval/`)

**What the code teaches, in one line:** It logs every agent step as a span-like `TraceRecord` (with a parent id, duration and tokens) into SQLite. It rebuilds a DAG with networkx and runs regex plus budget checks per test case.
**What it is not:** Not an LLM judge, not semantic scoring and not random metrics. "Correctness" is a regex match, or just "output is non-empty". "Topology" scoring and "replay" are named but not built.
**Relevance to your RAG study:** Medium (LLMOps track). Concepts: D1 (trace schema with parent links), D2 (token and latency budget per test; its "replay" is a counter-example of record/replay), D3 (shape only: per-request pattern checks, with no CI and no stored eval set), M3 (counter-example: no generation judge). [LLMOps] [Interview]
**Stack:** FastAPI, aiosqlite (WAL), loguru, networkx, `google-generativeai`. LLM: `gemini-2.0-flash-exp` (`backend/services/mas_runner.py:51`), an experimental id. If it has been retired, every call takes the fallback (UNVERIFIED). No embeddings. The React UI shows a live WebSocket trace table, agent hotspot bars and the eval report.
**Swap to your stack:** easy. All LLM calls go through one function, `_gemini_call` (`mas_runner.py:36-81`). Groq's `usage.prompt_tokens` and `completion_tokens` map straight onto `TokenCost`.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/models/trace.py` | `TraceRecord`, `TestCase`, `TestResult`, `EvalReport` | 29-40, 53-66, 69-80 |
| 2 | `backend/services/mas_runner.py` | A 4-call pipeline; each call emits a record linked to the last one | 36-81, 96-134 |
| 3 | `backend/core/logger.py` | Non-blocking queue → batched SQLite writes → WebSocket broadcast | 55-61, 85-95, 103-146 |
| 4 | `backend/core/harness.py` | The whole "evaluation" | 20-65 |
| 5 | `backend/core/graph.py` | DAG, critical path, hotspots, token total | 19-78 |
| 6 | `backend/tests/test_evaluation.py` | 8 unit tests | 32-150 |

### How it works, step by step
1. `POST /api/run` builds one `TestCase` per regex the client sends. With none, it uses the single pattern ".+" (`api/main.py:82-85`).
2. The pipeline is orchestrator decompose → researcher → analyst → orchestrator format. Between calls it emits a SEND record (`mas_runner.py:101-130`).
3. Each record's `parent_id` is the span id of the previous record (`mas_runner.py:39, 86`). The SESSION_START record goes straight to the logger and is not kept in `session.records` (`session.py:46-52`), so the first LLM call has no parent. So the "DAG" is always one straight chain.
4. Tokens come from Gemini `usage_metadata`. Missing counts fall back to characters divided by 4 (`mas_runner.py:24-28, 54-60`).
5. `emit` puts the record on a queue of up to 10,000 without blocking, and drops it if the queue is full (`logger.py:85-95`). A writer task drains up to 50 records per batch into SQLite and pushes each to WebSocket clients (`logger.py:103-146`).
6. `score`: correctness is a case-insensitive regex search with DOTALL (`harness.py:47-50`). Efficiency means total tokens ≤ `max_tokens` (default 50,000) and first-to-last record time ≤ `max_latency_ms` (default 30,000) (`harness.py:52-65`, `trace.py:56-57`). A test passes only if both hold (`harness.py:37`). Only `session.final_output` is checked (`harness.py:25`). The intermediate agent outputs sit in the trace but are never graded.
7. The critical path is the longest path, where each edge weight is the child's duration (`graph.py:39-48`). Hotspots are the total duration per agent (`graph.py:52-60`).

### README vs code
- README: "uses deterministic fallback responses" with no key (`README.md:35`). True (`mas_runner.py:31-33`). But the README does not say the eval still passes.
- Docstrings promise "topology scoring" (`harness.py:2`) and replay endpoints (`api/main.py:3`). `topology_ok` is never set (`trace.py:65`). `TraceReplayEngine` is imported but no endpoint uses it (`api/main.py:19`).
- `replay.py:2` says it "re-executes" traces. `replay()` only deep-copies the records and optionally overwrites one payload (`replay.py:41-50`). Nothing runs again and nothing flows downstream.

### Where it is thin or wrong
- [bug] Failed runs grade as PASS. When every call fails, the fallback text, such as "Orchestrator fallback response: You are an orchestrator…", is non-empty (`mas_runner.py:31-33, 69-81`). It matches the default ".+" test. The harness never looks at ERROR records.
- [misleading] Fallback calls record estimated tokens (`mas_runner.py:74-77`). Those count toward the token budget as if they were real.
- [bug] The loguru JSONL sink keeps only log lines bound with `trace_id` (`logger.py:21-29`). Normal trace records are never sent to loguru at all; the only call that binds `trace_id` is the "queue full" warning (`logger.py:91`). So the JSONL file that `replay.py:31-35` is built to read never gets normal traces.
- [bug] Replay cannot work even on that one line. Its `extra` holds the bound `trace_id` plus the warning's keyword fields (`logger.py:91-95`), with no `agent_name` or `event_type`. So building a `TraceRecord` from it fails, and the bare `except` skips it with no message (`replay.py:32-39`). Also, `extract_llm_responses` reads the payload key `response` (`replay.py:55`), but the runner writes `response_preview` (`mas_runner.py:66`). So it would return only empty strings.
- [bug] The test patterns are client-supplied regexes, used without a guard (`api/main.py:82-83`, `harness.py:50`). An invalid pattern raises inside `score`, after all four LLM calls have already run (`api/main.py:87-88`), so the client gets an HTTP 500 and no report. A hostile pattern can also make the backtracking regex engine run for a very long time (D4).
- [shallow] The chain topology makes critical-path analysis trivial: every node is on the path. `test_critical_path_identifies_bottleneck` (`tests/test_evaluation.py:41-47`) builds a 3-node chain, so the "slowest" node is on the path whatever rule picks it. The test can fail only if the chain itself is not built; it cannot catch a wrong critical-path rule.
- [misleading] The `profile_async` decorator is imported but never applied (`mas_runner.py:17`). The API returns `"profiler": {}` hard-coded (`api/main.py:96`).
- [bug] Wall time runs from the first record's creation to the last one's (`harness.py:58-64`). LLM records are created before the call (`mas_runner.py:42`), and `close()` adds no end record (`session.py:63-67`), so the final call's duration is left out. Timestamps come from `time.monotonic` (`trace.py:35`). Python only promises that differences within one process mean something, yet `list_traces` sorts traces from different runs on them (`logger.py:162-165`). Whether the clock survives an app restart on your OS is UNVERIFIED; it does not survive a reboot.
- [bug] Docker passes no `GEMINI_API_KEY` (`docker-compose.yml:15-16`), so a Docker run always falls back.

### Tests and data
- The tests check graph shape, hotspot sorting, token sums, the regex pass, the token-budget fail, persistence of 5 records, and the empty-output fail (`tests/test_evaluation.py:32-150`). The test docstring names `TraceReplayEngine` (`:2`), but no test covers it. No test covers the "fallback passes" case.
- `backend/fixtures/sample_trace.jsonl` has 12 synthetic rows ("step N content"). It uses wall-clock (epoch) timestamps, unlike the monotonic ones the app writes. Its token keys do not match each other: `prompt_tokens` sits at the top level (the model nests it under `token_cost`, `trace.py:38`, and the database column is `prompt_tok`, `logger.py:42`), while `compl_tok` does match the database column (`logger.py:43`). No code, test or script loads the file. It is not useful practice data.

### What to take for your project
- **D1 / LLMOps:** reuse the record shape. Give each record `trace_id`, `span_id`, `parent_id`, stage name, `duration_ns`, prompt and completion tokens, and an error message. Write one per ragkit stage (embed, retrieve, rerank, build_context, generate) into your `results.jsonl` trace.
- **D3:** reuse the `TestCase` idea: an expected pattern plus `max_tokens` plus `max_latency_ms`. Use it only as a cheap first gate in a code-first chain. Add "no ERROR or fallback span" as a hard fail.
- **M3:** do not treat a regex pass as answer quality. Faithfulness still needs your judge on stored traces.
- **D2 / record-replay rule:** L59's "replay" is not what your notebooks need. A real replay cache stores each response under a key, such as a hash of provider, model, messages and parameters (for Groq include `reasoning_effort` and `max_tokens`). In replay mode it returns the stored response and never calls the API. Write that as one small wrapper around your Groq and Cohere calls, and mark each trace span `cache_hit=True/False`.

### Try this
- (25 min) Read `harness.py:20-65` and `mas_runner.py:69-81`. Write a 6-line check in plain Python, next to the `TestCase` checks, that fails a run when any record has `event_type == "ERROR"` or `payload.get("fallback")` is true (the fallback branch sets both, `mas_runner.py:70, 79`). Then decide where it belongs in your D3 regression script.

### Interview angle
- *Q: How do you evaluate a multi-agent pipeline?* A: Grade each step from its trace, not just the final string. Use code checks first (errors, fallbacks, token and latency budgets, required patterns), then a validated LLM judge for quality. A "non-empty output" test will pass on a crashed run.

---

## L64 · CD and containerisation with Prometheus and Kubernetes  (`lesson64/vaia-l64/`)

**What the code teaches, in one line:** How to ship an LLM API. It covers a multi-stage Dockerfile, separate liveness, readiness and startup probes, a Prometheus `/metrics` endpoint with HTTP counters and a latency histogram, k8s Deployment/Service/Ingress/HPA/ConfigMap/Secret, and a GitHub Actions CD pipeline with a Trivy CVE gate.
**What it is not:** Not RAG and not LLM monitoring. ChromaDB is only heart-beaten, never queried. The metrics have no tokens, no cost and no quality signal. CI has no eval step.
**Relevance to your RAG study:** Low (Medium for the LLMOps track). Concepts: D1 (HTTP RED metrics), D2 (latency histogram), D3 (CI gates: coverage and image scan), D4 (non-root user, secrets, CVE scan), C5 (counter-example: "cite sources" asked for, with no retrieval and no source ids). [LLMOps] [Interview]
**Stack:** FastAPI, `prometheus-client`, `chromadb==0.5.23` (unused), redis (unused), `google-generativeai`. LLM: `models/gemini-2.0-flash-lite` (`src/core/config.py:9`). The Vite UI polls `/health/*` and `/metrics` every 5 s, draws a request chart and has an infer box.
**Swap to your stack:** easy. There is one `generate_content` call (`src/core/agent.py:57-60`). The infra patterns do not depend on the provider.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `src/main.py` | Metrics, middleware, liveness and readiness | 24-28, 65-66, 72-87, 92-114 |
| 2 | `src/routers/infer.py` + `src/core/agent.py` | Infer endpoint, error classification, quota fallback | infer 10-19, 35-71; agent 26-69 |
| 3 | `Dockerfile` + `.dockerignore` | builder / dev / runtime stages | 11-23, 29-39, 45-73 |
| 4 | `k8s/deployment.yaml`, `k8s/hpa.yaml` | Rolling update, probes, resources, CPU HPA | 15-19, 44-72; hpa 12-29 |
| 5 | `.github/workflows/cd.yml` | ci → build and scan → push → deploy | 20-37, 62-107, 110-146 |
| 6 | `prometheus.yml` | One static scrape target `agent:8000` | 1-8 |

### How it works, step by step
1. At startup, `warm_up` tries to connect to Chroma, then sets `is_ready=True` even if that failed (`agent.py:26-37`).
2. Every HTTP request passes through middleware. It increments `vaia_active_requests`, observes `vaia_request_latency_seconds` (buckets from 5 ms to 5 s), and counts `vaia_requests_total{endpoint,status}` (`main.py:24-28, 72-87`).
3. `/health/live` always returns 200. `/health/ready` returns 503 until the agent is ready and the Chroma heartbeat answers within 2 s (`main.py:92-114`).
4. `/v1/agent/infer` puts the client-supplied `context` in front of the query and calls Gemini (`agent.py:48-66`). The "system prompt" is passed as the first item of the contents list in that same call (`agent.py:57-60`), not through the model's `system_instruction` (L69 does use that, L69 `backend/agent.py:39-42`). My reading of the library is that the list becomes parts of one user message (not run). The size limits are 4096 characters for the query and 8192 for the context, counted in characters, not tokens (`infer.py:23-24`). Auth errors give 503. Quota errors give 200 with a demo answer (`infer.py:55-70`). Any other error gives 500 (`infer.py:71`).
5. k8s settings: 2 replicas, `maxUnavailable: 0`; requests 250m/256Mi, limits 500m/512Mi; HPA 2-10 pods at 60% CPU (`deployment.yaml:11-19, 44-50`; `hpa.yaml:12-20`).

### README vs code
- The README only covers how to run it. The code promises "cite sources when available" in the system prompt (`agent.py:50-53`), but no retrieval exists. The only "context" is what the caller sends.

### Where it is thin or wrong
- [bug] The `dev` stage runs `COPY tests/` (`Dockerfile:36`), but `.dockerignore` excludes `tests/` (`.dockerignore:18`). So `docker compose --profile test run test` should fail at build (expected Docker behaviour; not run).
- [bug] The runtime stage installs no OS packages, which `tests/test_dockerfile.py:38-42` even enforces, and it starts from `python:3.12-slim` (`Dockerfile:45`). So it should have no `curl`, but both healthchecks and the CD smoke test (which runs `curl` inside the pod via `kubectl exec`) call `curl` (`Dockerfile:64-65`, `docker-compose.yml:30`, `cd.yml:145-146`). Compare L49, whose backend Dockerfile does install curl (L49 `docker/Dockerfile.backend:3`).
- [bug] `--workers 2` (`Dockerfile:71-73`) with the default prometheus registry means each worker process keeps its own counters. Each scrape returns the numbers of whichever worker answers it. Correct totals need `prometheus_client` multiprocess mode (library behaviour, not run).
- [bug] `docker/metadata-action` `type=sha` makes short-SHA tags by default (`cd.yml:67-68`; documented default, not run). Trivy and deploy refer to the full `github.sha` (`cd.yml:87, 132`), so the image they name should not exist. The workflow also sits under the lesson folder, not at the repo root, so GitHub never runs it from this repo.
- [bug] The k8s ConfigMap points at `chromadb-service` (`configmap.yaml:7`), but no Chroma manifest exists. Readiness stays 503 and the rollout times out. The `secret.yaml:9` placeholder is not valid base64.
- [misleading] A quota or rate-limit failure is counted as status 200 (`infer.py:60-70`), so the dashboards hide that kind of provider outage. Auth errors do show up, as 503 (`infer.py:55-59`). The UI's own 5 s polling (`frontend/src/App.jsx:132`) inflates `vaia_requests_total`. The endpoint label is the raw path (`main.py:74`), which risks high label cardinality.
- [bug] Readiness never recovers after a failed warm-up. If Chroma is down at startup, `_chroma_client` stays `None` (`agent.py:28-37`), and `chroma_heartbeat` then always returns False (`agent.py:40-41`). Nothing creates the client again, even though the log line says it "will retry on readiness probe" (`agent.py:36`). A pod that starts before Chroma stays unready until it is restarted. Locally, Compose waits for a healthy Chroma first (`docker-compose.yml:24-26`), which hides this.
- [shallow] The HPA scales on CPU at 60% (`hpa.yaml:20`), but each request mostly waits on a remote API inside a thread (`agent.py:57-60`). An I/O-bound LLM proxy can queue requests while its CPU stays low, so CPU is a weak scaling signal here. In-flight requests or latency would be better. This is expected behaviour; nothing was measured.
- [shallow] `test_metrics_endpoint_reachable` passes on any Prometheus output, because its check ends in `or b"# HELP" in r.content` (`tests/test_health.py:41`). The client library's default collectors also write `# HELP` lines, so the test passes even if the app's own metrics are missing.

### Tests and data
- `tests/test_dockerfile.py` greps the Dockerfile for strings. `tests/test_k8s_manifests.py` checks YAML keys, and it imports `yaml` (`:6`), which neither requirements file declares. It probably still installs, because `uvicorn[standard]` pulls in PyYAML (UNVERIFIED; nothing was installed). `tests/test_health.py:13-55` checks status codes only; two tests set `agent=None` on purpose (`:26, :49`). No test exercises inference or checks that a metric value changes. No data.

### What to take for your project
- **D1/D2:** copy the metric shape, not the code: one counter and one histogram per stage, labelled by stage, not by raw path. Add the LLM signals this lesson lacks: tokens, cost and cache-hit rate, which your `LLMResult` already holds.
- **D3:** the CI idea "tests must pass before build, hard gate on scan" carries over. Your gate should be the frozen eval set and the contracts check, not coverage. You use local git only, so GitHub Actions will never run for you. Write the gate as one local `uv run` script that exits non-zero on failure, and run it before each commit you ask to make.
- **C5:** "cite sources" in a prompt does nothing without numbered sources. Your context builder must label each chunk with an id and its PDF page (for example `doc.pdf p.3/15`), and a check must confirm that every cited id is in the retrieved set.
- Skip k8s; it is far beyond your local, uv-only setup.

### Try this
- (20 min) Read `main.py:72-87` and list which questions about a RAG query it cannot answer. Examples: how much retrieval took, the token count, whether the answer was a fallback. Write the three metric names you would add, with labels.

### Interview angle
- *Q: Liveness vs readiness for an LLM service?* A: Liveness asks whether the process is alive, so keep it cheap or k8s will restart pods for nothing. Readiness asks whether the service can take traffic now (dependencies up, warm-up done), so failing it removes the pod from the load balancer without a restart. A startup probe holds off the liveness probe during a slow warm-up (`k8s/deployment.yaml:67-72`). Readiness must also be able to recover; here it cannot (`agent.py:36-41`).

---

## L69 · Agent observability with OpenTelemetry  (`lesson69/l69-agent-observability/`)

**What the code teaches, in one line:** It uses the OpenTelemetry SDK with a hand-written `SpanExporter` that writes spans to SQLite. One root span per request has 3 child spans, and tokens, cost and latency are span attributes. It also rolls these up into per-trace totals, p50/p95/p99 latency, a cost trend and threshold "breaches".
**What it is not:** Not OTLP, Jaeger or Phoenix: there is no standard exporter or collector. There is no FastAPI auto-instrumentation, though the package is installed. The attribute names are custom `llm.*`, not the OTel GenAI conventions.
**Relevance to your RAG study:** Medium. Concepts: D1 (per-stage spans), D2 (cost and latency budgets, percentiles). [LLMOps] [Interview]
**Stack:** FastAPI, `opentelemetry-sdk==1.25.0`, sqlite3/aiosqlite, `google-generativeai`. LLM: `gemini-2.0-flash` (`backend/agent.py:36`). No embeddings. The React UI shows metric cards, a span waterfall, a cost chart, p50/p95/p99 bars, a live WebSocket feed and three demo queries.
**Swap to your stack:** easy. There is one LLM call (`agent.py:95`). Groq returns usage tokens, and you update the two price constants (`agent.py:21-22`).

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/agent.py` | Span tree and attributes | 44-68, 70-81, 83-132, 134-139 |
| 2 | `backend/tracer.py` | Resource, BatchSpanProcessor, SQLite exporter, trace roll-up | 22-73, 99-164, 170-188 |
| 3 | `backend/main.py` | Runs the agent, finds the trace id, writes threshold snapshots | 70-114 |
| 4 | `backend/db.py` | Dashboard aggregates and percentiles | 51-111 |
| 5 | `tests/test_l69.py` | 8 tests | 23-78 |

### How it works, step by step
1. `POST /api/agent/run` runs the synchronous `agent.run` in a thread pool (`main.py:72-75`).
2. The root span is `agent.run` (SERVER), with attributes `agent.model`, the first 500 characters of the input, and the context keys (`agent.py:46-52`).
3. The children run one after another. `agent.build_prompt` records the prompt length and a `prompt_built` event (`agent.py:70-81`). `agent.llm_call` (CLIENT) records `llm.vendor`, `llm.model`, `llm.prompt_chars`, `llm.input_tokens`, `llm.output_tokens`, `llm.latency_ms`, `llm.cost_usd` and `llm.finish_reason`, plus request and response events (`agent.py:83-124`). `agent.postprocess` records the output length and word count (`agent.py:134-139`).
4. Cost is the input tokens over 1000 times $0.000075, plus the output tokens over 1000 times $0.000300 (`agent.py:21-22, 117-118`). The code comment calls these "Gemini 2.0 Flash pricing" (`agent.py:20`). As far as I know they are Flash-Lite-class list prices, not 2.0 Flash prices (UNVERIFIED; check the current price page).
5. `BatchSpanProcessor` exports up to 32 spans every 500 ms (`tracer.py:180-185`). The exporter writes each span and upserts a `traces` row that sums cost and tokens and counts spans (`tracer.py:111-164`).
6. The API sleeps 0.65 s, then takes the newest trace as "this" trace (`main.py:77-80`). It writes `metric_snapshots` with breach flags at 5000 ms latency and $0.01 cost (`main.py:83-94`). The latency it compares is the LLM call's own latency (`agent.py:112, 131`), not the request's.
7. `/api/metrics` covers the last hour: request count, average trace duration, cost, tokens, ERROR count (`db.py:53-63`). Percentiles come from `agent.llm_call` span durations, picked by a simple index into the sorted list with no interpolation (`db.py:65-70, 91-94`). The cost trend covers only the last 10 minutes, in 1-minute buckets (`db.py:72-81`).

### README vs code
- The README says to copy `.env.example` to `.env` (`README.md:30`). Nothing calls `load_dotenv`, even though python-dotenv is installed (`requirements.txt:10`), so `.env` is ignored and only exported variables work.
- The README says `setup.sh` is in the parent folder (`README.md:4`). It is not there. `opentelemetry-instrumentation-fastapi` is installed (`requirements.txt:7`) but never used.

### Where it is thin or wrong
- [bug] A failed LLM call looks healthy. The fallback adds only an event (`agent.py:102-110`). The span is never set to ERROR, and the root is set to OK (`agent.py:62`). Tokens become word counts, and a cost is still computed (`agent.py:115-118`). So `error_rate_pct`, which counts only ERROR trace rows (`db.py:60, 101`), stays 0 during an outage.
- [bug] Race on `trace_id`. "Newest trace after 0.65 s" (`main.py:78-80`) can return another request's trace under concurrency, and `created_at` has only 1-second resolution. Read the id from the root span's context instead.
- [bug] The trace roll-up keeps the first exported span's `start_time`, `status` and `root_name` (`tracer.py:146-158`). Children end first, so `root_name` is usually `agent.build_prompt` and the status stays `UNSET`, because only ERROR overwrites it. Duration is slightly under-reported.
- [misleading] The cost alarm can almost never fire. At the code's prices (`agent.py:21-22`), one call must use more than about 33,000 output tokens, or about 133,000 input tokens, to pass $0.01 (`main.py:85`). That is plain arithmetic from the two constants. A threshold that cannot trip is not monitoring; set yours from your measured cost distribution.
- [misleading] The root attribute `agent.total_latency_ms` (`agent.py:61`) holds only the LLM call's latency (`agent.py:112, 131`). Prompt building and post-processing are left out, despite the name.
- [misleading] The WebSocket event hard-codes `"status": "OK"` (`main.py:110`). The dashboard puts average *trace* latency next to percentiles of *LLM span* latency (`db.py:56, 65-70`). These are different quantities.
- [ok-for-demo] Raw user input goes into a span attribute (`agent.py:51`). That is fine locally. For you it matters, because book text must never reach an external tracing service.
- [bug] The Compose healthcheck uses `curl` (`docker-compose.yml:13`), but the image installs only `gcc` (`Dockerfile:4`). Compose also passes no API key.

### Tests and data
- The tests check the health route, the metrics keys, list and 404 routes, the table names, and the list types (`tests/test_l69.py:23-78`). `test_cost_calculation` is a tautology that ends in `or expected > 0` (`:57`) and never calls the agent. No test creates or inspects a span, although the docstring says "span schema" (`:2`). The tests write to the real `data/traces.db`. No data.

### What to take for your project
- **D1:** re-implement the pattern in plain Python first. Make one span-like dict per ragkit stage (embed, retrieve, rerank, build_context, generate) with `trace_id`, `span_id`, `parent_id`, start and end, status and attributes. Record the token, cost, latency, `cache_hit` and `finish_reason` names your `LLMResult` already has. Then optionally switch to the real OTel SDK with a local exporter, never a remote one.
- **D2:** reuse the roll-ups: p50/p95/p99 per stage, cost per query, and threshold breaches. Fix the three bugs: mark fallbacks as ERROR, take the trace id from the root span, and roll up from the root span.
- **LLMOps notebook:** the "custom `SpanExporter` to a local file or database" idea fits your record/replay rule. Traces stay on disk.
- **Cost, done right for your stack:** take token counts only from Groq's `usage` fields, and price them with your own constants for `openai/gpt-oss-20b`, not L69's Gemini numbers. On a cache hit, record `cache_hit=True` and cost 0. On a canned fallback, record status ERROR with no tokens and no cost, never word counts (the mistake at `agent.py:115-118`).
- **Book-text rule:** L69 puts the raw user input into a span attribute (`agent.py:51`). If you ever turn on LangSmith (after the plain-Python mechanism), apply that rule in code. Store only a hash or a short label for book-derived text in any span that can leave your machine.

### Try this
- (30 min) Copy `agent.py:83-132` to a scratch file. Replace the Gemini call with a function that raises. Add `span.set_status(Status(StatusCode.ERROR))` and a `fallback=True` attribute in the except branch. List which dashboard numbers (`db.py:96-110`) would now change. Look for `error_rate_pct`: one ERROR child span is enough to turn the trace row to ERROR (`tracer.py:158`), even though the root is still set to OK (`agent.py:62`).

### Interview angle
- *Q: What would you put on the spans of a RAG request?* A: One span per stage, each with its latency and status. Retrieval spans get top-k, chunk ids and scores. The LLM span gets model, tokens, cost, finish reason and whether a fallback or cache was used. Mark degraded paths as errors, or your error rate will lie.

---

## Block summary
| Lesson | Title | Relevance | Concepts | Best file to read | Biggest problem |
|---|---|---|---|---|---|
| L49 | CrewAI role-based crew | Low | A5 (counter), P7 (counter); Interview | `backend/crew.py` | Silent demo fallback passes `test.sh` (`crew.py:134-166`, `test.sh:21`); UI run time includes 42 s of fixed sleeps (`main.py:97-100`); Docker key empty |
| L54 | Agent personalisation | Low | P4 (cautionary), X3 (counter), A4 (counter), D4 (partial) | `backend/services/router.py` | Cosine on all-positive vectors routes the "VP Eng" seed (and any all-0.5 vector) to ANALYST (`router.py:13-16`, `main.py:49-50`); the "privacy" noise leaks the clean vector anyway (`inference.py:152`) yet changes the chat persona (`chat.py:115-118`) and causes false drift (`inference.py:115-123`) |
| L59 | MAS evaluation and debugging | Medium | D1, D2 (replay: counter-example), D3 (shape only), M3 (counter); LLMOps, Interview | `backend/core/harness.py` | Fallback text passes the default ".+" test; ERROR records ignored (`api/main.py:84-85`, `mas_runner.py:69-81`); replay cannot load or return anything (`replay.py:32-39, 55`) |
| L64 | CD, containers, Prometheus, k8s | Low (Medium LLMOps) | D1, D2, D3, D4, C5 (counter); LLMOps, Interview | `src/main.py` | Broken plumbing: `tests/` dockerignored (`.dockerignore:18`), curl missing, multi-worker metrics, SHA tag mismatch (`cd.yml:67-68` vs `:87`), readiness never recovers (`agent.py:36-41`) |
| L69 | Agent observability (OTel) | Medium | D1, D2; LLMOps, Interview | `backend/agent.py` | LLM failures traced as OK (`agent.py:102-110, 62`); trace id is "newest row" (`main.py:78-80`); cost alarm practically unreachable (`main.py:85`) |

### Cross-lesson patterns
- **Fallbacks hide failures from the measuring tool.** Every lesson swallows provider errors: L49 `crew.py:134`, L54 `chat.py:73-75`, L59 `mas_runner.py:69-81`, L64 `infer.py:60-70` (quota and rate-limit errors only), L69 `agent.py:102-110`. In each case the reply, test, eval, metric or span still looks like a success. (L59 does write an ERROR record; its eval just ignores it.) For your notebooks: a fallback must be a labelled, counted failure.
- **Estimated tokens shown as real ones.** Word counts (L54 `chat.py:131`, L69 `agent.py:115-116`), characters divided by 4 (L59 `mas_runner.py:24-28`) and constants (L54 `compressor.py:50-60`).
- **Tests check shape, not behaviour.** Key-exists or status-code checks, a tautology (L69 `test_l69.py:57`), a test that cannot fail (L59 `test_evaluation.py:41-47`), Dockerfile greps (L64).
- **Docker plumbing bugs.** `curl` healthchecks in images without curl (L64, L69), an empty or missing API key in Compose (L49 sets it empty; L59 and L69 pass none), READMEs pointing at a missing `../setup.sh` (L49, L69).
- **Advertised but unused components:** Chroma/Redis (L54 docstring; L64 Chroma is heartbeat-only and Redis is never used), the profiler (L59), replay (L59), FastAPI OTel instrumentation and dotenv (L69).
- **Dangerous `cleanup.sh` in every lesson.** All five prune every unused Docker image on the whole machine (`image prune -a`), not just this project's. Some go further: L49 stops every running container (`cleanup.sh:15`); L64 stops and then force-removes every container (`cleanup.sh:7-17`); L54 and L59 run `docker system prune -af --volumes` (`cleanup.sh:25` in both). L69 stops at images, networks and build cache (`cleanup.sh:31-35`). Never run them.
- **Provider:** Gemini everywhere (2.0 Flash, Flash-Lite, flash-exp). Each lesson has 1-2 call sites, so a swap to Groq is easy in all five.
- **Gates and alarms that cannot trip.** L59's default ".+" test (`api/main.py:85`), L64's `or # HELP` metrics test (`tests/test_health.py:41`), L54's delete test (`store.py:181`, `test.sh:53`), L69's $0.01 cost breach (`main.py:85`) and L49's length check (`test.sh:21`) all stay green on broken or idle runs. Before you trust a check, write the input that should make it fail and see that it does.
- **No caching and no real replay anywhere.** None of the five caches an LLM call, so none can rerun without credits. L59's "replay" only copies records (`replay.py:41-50`). Your record/replay wrapper has no model in this block.
- **Units hidden in names.** "Tokens" that are words or characters ÷ 4 (above), size limits in characters (L64 `infer.py:23-24`), and "total latency" that is LLM latency only (L69 `agent.py:61`). In your traces, put the unit in the field name (`_chars`, `_tokens`, `_ms`) and say where the number came from (`usage` vs estimate).
