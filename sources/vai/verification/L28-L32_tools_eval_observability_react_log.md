# Verification log: VAI lessons 28–32: tool agent, evaluation, observability, ReAct

[← Lesson guide](../L28-L32_tools_eval_observability_react.md) · [← Guide index](../README.md)

Pass A re-opened every cited claim at its source line and tried to refute it. Pass B re-read every backend file with a different lens: control flow, missed issues, concept mapping and fit to your stack. Verdicts: confirmed / corrected / removed / unverified.
## Verification log (pass A)
Paths are relative to each lesson's project folder unless they start with `prior_work/`. "confirmed" means I opened the cited lines and the code does what the guide says.

| Lesson | Claim (short) | Verdict | Evidence file:line |
|---|---|---|---|
| all | No lesson in L28–L32 has a `setup.sh` | confirmed | file listing of `lesson28`…`lesson32` |
| L28 | Chroma `PersistentClient` + sentence-transformers `all-MiniLM-L6-v2` | confirmed | `backend/rag/engine.py:18-24` |
| L28 | Default L2 distance (no space set) | confirmed | `backend/rag/engine.py:32-43` |
| L28 | Default model `gemini-2.0-flash-lite`, 5-model fallback chain, SDK 0.4.0 | confirmed | `backend/llm_client.py:13-19`, `backend/.env.example:3`, `backend/requirements.txt:4` |
| L28 | `GenerationConfig` built in four places; all calls go through `generate_with_retry` | confirmed | `tool_equipped_agent.py:304,458`, `evaluator.py:59,83`; calls at `tool_equipped_agent.py:305,400,459,472`, `engine.py:112`, `evaluator.py:60,84` |
| L28 | "Cohere would need a custom Chroma embedding function" | corrected (Chroma ships one; `embed-v4.0` support UNVERIFIED) | `backend/requirements.txt:5` |
| L28 | Read-in-order key lines (main, agent, engine, evaluator, llm_client, tools, App.js) | confirmed | `main.py:28-35,50-76`; `tool_equipped_agent.py:54-162,164-210,283-313,412-442`; `engine.py:45-60,73-132`; `registry.py:23-46`; `calculator.py:33-38`; `App.js:38-42,144-149` |
| L28 | Regex order hybrid, calculator, weather, database, RAG; "What is Python?" hits the RAG rule | confirmed (hand-traced all five regexes) | `tool_equipped_agent.py:168,180-188,191-195,198-204,206-209` |
| L28 | Classifier: temp 0.1, 1024 tokens, fence stripping, no schema check (missing key raises) | confirmed | `tool_equipped_agent.py:304-313`, `:79` |
| L28 | `top_k=5`, slice to 3, numbered context, "only context + cite" prompt, 25 s timeout | confirmed | `engine.py:76-77,82-98,101-110` |
| L28 | Context-dump fallback "on a timeout or quota error" | corrected (also API-key, credentials and "expired" errors) | `engine.py:115-126` |
| L28 | Judge: two parallel prompts, temp 0.1, 256 tokens; completeness len/200; overall = mean | confirmed | `evaluator.py:28-31,34,40,59,83` |
| L28 | Threshold 0.7; re-query `top_k=10`, `rerank_top_k=7` | confirmed | `tool_equipped_agent.py:42,101,430-434` |
| L28 | Re-query "puts all 5 into the context" | unverified (depends on how unpinned Chroma handles `n_results` > count) | `backend/requirements.txt:5`, `engine.py:82-85` |
| L28 | Stats summed in memory; turn saved in `self.conversations` | confirmed | `tool_equipped_agent.py:114-137` |
| L28 | Tool branch: regex params, LLM parameter extraction, wording call, parallel hybrid | confirmed | `tool_equipped_agent.py:331-332,444-475,378-410` |
| L28 | README "Real-time evaluation metrics" | confirmed | `README.md:64` |
| L28 | README hybrid example has no digits, so it goes to the LLM classifier | confirmed | `README.md:80`, `tool_equipped_agent.py:168,206-209` |
| L28 | Docstring claims L19–L27; engine calls itself "simplified" | confirmed | `tool_equipped_agent.py:29-32`, `engine.py:15` |
| L28 | History reads the first conversation ever stored | confirmed | `tool_equipped_agent.py:477-487` |
| L28 | [misleading] sample hybrid button gets constant 0.75 scores | confirmed | `frontend/src/App.js:149`, `tool_equipped_agent.py:87-90,231-233,243` |
| L28 | [misleading] judge error gives 0.75; bad JSON gives 0.5 | confirmed | `tool_equipped_agent.py:104-105`, `evaluator.py:68-70,92-94` |
| L28 | [bug] re-query keeps old metrics; `requeried` not returned | confirmed | `tool_equipped_agent.py:100,436-442,141-148` |
| L28 | [misleading] rerank is a list slice | confirmed | `engine.py:90-92` |
| L28 | [shallow] completeness = length/200 | confirmed | `evaluator.py:34` |
| L28 | [bug] weather regex picks "like", mock returns default 20 °C Clear | confirmed | `tool_equipped_agent.py:191-195`, `tools/weather.py:44-48` |
| L28 | [bug] fallback chain moves on only for quota errors; `gemini-exp-1206` may be retired | confirmed (retirement stays UNVERIFIED) | `llm_client.py:15,56-65` |
| L28 | [misleading] "safely" calculator uses `eval`; LLM path unfiltered | confirmed | `tools/calculator.py:24,38`, `tool_equipped_agent.py:335` |
| L28 | [ok-for-demo] database ignores the query | confirmed | `tools/database.py:47-61` |
| L28 | [bug] Docker "container cannot start" | corrected (build fails first at `COPY data/`; the import problem is also real) | `Dockerfile:16,23`, `main.py:9-13`, `start.sh:12,25` |
| L28 | [bug] `cleanup.sh` stops all containers and prunes all images and volumes | confirmed | `cleanup.sh:25-33` |
| L28 | [shallow] ragas, datasets, duckduckgo-search, redis never imported | confirmed (grep of backend `.py` files finds none) | `backend/requirements.txt:11-14` |
| L28 | `test.sh` only checks imports | confirmed | `test.sh:9-22` |
| L28 | Data: five sentences plus mock tables | confirmed | `engine.py:48-54`, `tools/database.py:32-45` |
| L28 | Prior copy: CPU torch, `PYTHONPATH`, Node 18 + anonymous volume, 1,020-line Streamlit with `google-genai` and `gemini-embedding-001`, backend unchanged | corrected (the copy still has `COPY data/`) | `prior_work/VAI/lesson28/l28-tool-equipped-agent/Dockerfile:13,17,21`, `.../docker-compose.yml:18,24`, `prior_work/VAI/lesson28/streamlit-demo/app.py:7,21` |
| L28 | Try this: 4-row score-source table | confirmed (tool path gives `None` metrics; RAG and LLM hybrid get judge + heuristic; local hybrid gets constants) | `tool_equipped_agent.py:93-107,212-245`, `evaluator.py:18-42` |
| L29 | `gemini-2.0-flash-exp`, SDK 0.3.2, one LLM call | confirmed | `agent_service.py:23,35-37`, `backend/requirements.txt:5` |
| L29 | Dashboard tiles, Recharts bar chart, regression list | confirmed | `frontend/src/App.jsx:2,77-98,138-177` |
| L29 | Read-in-order key lines | confirmed | `default.json:5-27`, `schemas.py:11-18,28-71`, `evaluation_service.py:38-132`, `agent_service.py:16-74`, `validators.py:6-42`, `latency_profiler.py:6-20`, `metrics_service.py:14-81`, `tests/test_validators.py:4-20` |
| L29 | Button sends `default`, `iterations: 3` | confirmed | `frontend/src/App.jsx:45` |
| L29 | Route, suite fallback, cap at 5 | confirmed | `main.py:54-63`, `evaluation_service.py:41,134-151` |
| L29 | "Measured on three different answers" | corrected (tool and RAG evaluators use different cases; the latency loop calls every case again) | `evaluation_service.py:66-70,85-88,111-113` |
| L29 | Prompt with no tool list; mock sleeps 40 ms | confirmed | `agent_service.py:36,39-41,62-66` |
| L29 | Tool "extraction" by keyword with hard-coded params; mock tool calls | confirmed | `agent_service.py:43-44,54-60,68-74` |
| L29 | Tool validator rule (first call, score at least 0.8, substring match) | confirmed | `validators.py:7-27`, `evaluation_service.py:49` |
| L29 | Groundedness rule; `retrieved_chunks` always `[]`; pass at 0.7; mean | confirmed | `validators.py:32-42`, `agent_service.py:48,52`, `evaluation_service.py:50,100` |
| L29 | Latency: fixed 20 ms and 10 ms sleeps; index-pick percentiles | confirmed (added: tool sleep only when tool calls exist) | `latency_profiler.py:10,15-18`, `evaluation_service.py:121-131` |
| L29 | Summary means; zero latency shown as 100 or 200 ms | confirmed | `metrics_service.py:36-43` |
| L29 | Regression: fixed 0.95 / 0.90 / 500 ms, 5 % | confirmed | `metrics_service.py:14-18,61-81` |
| L29 | README key note, missing `setup.sh`, "RAG Groundedness" label, in-memory history | confirmed | `README.md:9,37`, `App.jsx:88`, `metrics_service.py:12-18,26-29` |
| L29 | [misleading] mock scores 1.0 and 1.0 | confirmed (hand count: claim 1 = 5/7 words, claim 2 = 5/5; both tool cases match) | `agent_service.py:65,68-74`, `default.json:10,17-18,26`, `validators.py:20-42` |
| L29 | [bug] empty answer scores 1.0; LLM error gives an empty answer | confirmed (model-id retirement stays UNVERIFIED) | `validators.py:34`, `agent_service.py:50-52` |
| L29 | [bug] total 9 vs passed counted once (3 passed, 6 failed) | confirmed | `evaluation_service.py:47-48,55` |
| L29 | [misleading] params "cannot fail" | corrected (true only because the hard-coded values equal this suite's expected values; key path) | `agent_service.py:56-59`, `default.json:10,26` |
| L29 | [misleading] fixed-sleep latencies | confirmed | `latency_profiler.py:10,17` |
| L29 | [shallow] 9 samples, so P95 = P99 = max | confirmed (`int(9*0.95)` and `int(9*0.99)` are both 8) | `evaluation_service.py:126-128` |
| L29 | [shallow] word overlap; `unsupported_claims` always empty | confirmed | `validators.py:35,38-40` |
| L29 | [misleading] two "Regression detected" alerts on page load | confirmed (latency 0 vs 500 is not flagged) | `App.jsx:13-14,158,172`, `metrics_service.py:47-55,72` |
| L29 | [shallow] `iterations` up to 1000, "only the latency loop uses it" | corrected (also used for `total`) | `schemas.py:22`, `evaluation_service.py:41,47,111` |
| L29 | [bug] blocking call stalls the loop | corrected (only with a key; the mock path yields) | `agent_service.py:35,40` |
| L29 | Tests cover one exact match and one overlap case | confirmed | `tests/test_validators.py:4-20` |
| L29 | `default.json`: 3 cases, usable field schema | confirmed | `default.json:4-28`, `schemas.py:11-18` |
| L29 | Prior copy: Dockerfile and compose (8001/3001), Streamlit with LangChain, Groq, Cohere, in-memory Chroma; "original files unchanged" | corrected (`vite.config.js` edited; no `frontend/src/`) | `prior_work/VAI/lesson29/l29-evaluation-framework/docker-compose.yml:5,20,22`, `.../frontend/vite.config.js`, `prior_work/VAI/lesson29/streamlit_app/app.py:25-27,127` |
| L29 | Try this hand counts (a) 0.0, (b) 1.0, (c) 1.0 | confirmed ((a) best 1/8; (b) 7/13, just over 0.5) | `validators.py:32-42`, `default.json:17-18` |
| L30 | Stack: BaseHTTPMiddleware, structlog, aiosqlite, Chroma 0.4.22 `Client()`, MiniLM, `gemini-pro`, SDK 0.4.0 | confirmed | `middleware/observability.py:4,8`, `services/rag_service.py:15-17`, `backend/requirements.txt:5-8,13` |
| L30 | Dashboard and per-query UI fields | confirmed | `frontend/src/components/MetricsDashboard.js:40-87`, `QueryInterface.js:58-107` |
| L30 | One generate call | confirmed | `rag_service.py:177-180` |
| L30 | Read-in-order key lines | confirmed | `observability.py:11-57`, `rag_service.py:41-223`, `metrics_collector.py:51-67,86-107,122-149`, `structured_logger.py:7-69`, `app/main.py:17-31,45-83`, `models/telemetry.py:15-61` |
| L30 | New uuid4 per request; no incoming header read | confirmed | `observability.py:13-25` |
| L30 | Embed logs only the query length; encode is synchronous | confirmed | `rag_service.py:95-104` |
| L30 | `n_results=3`; similarity = 1 minus distance; only the average kept | confirmed | `rag_service.py:112-126,71-84` |
| L30 | Augment: word-count "tokens" | confirmed | `rag_service.py:139-144` |
| L30 | Plain prompt; thread call; word-count tokens; fixed prices; fallback text | confirmed (prices stay UNVERIFIED) | `rag_service.py:160-201,225-244` |
| L30 | `pipeline_latency_ms`; `total_latency_ms`; `X-Trace-ID` header | confirmed | `rag_service.py:63`, `metrics_collector.py:77-84`, `observability.py:31-42` |
| L30 | `_latency_ms` names go to one deque; flush every 10 s | confirmed | `metrics_collector.py:13,51-67,122-149` |
| L30 | WebSocket every 2 s; timeseries from SQLite | confirmed | `app/main.py:63-67,72-83`, `metrics_collector.py:109-120` |
| L30 | README tracing and token claims; `TraceSpan` and other models unused | confirmed | `README.md:8,11`, `models/telemetry.py:6-61` |
| L30 | README sampling and under 8 ms overhead | confirmed no sampling code; overhead figure unverified | `README.md:77,82` |
| L30 | prometheus-client, python-json-logger unused | confirmed (grep finds no import) | `backend/requirements.txt:12,14` |
| L30 | `SETUP_AND_RUN.md` refers to an absent `setup.sh` and a home path | confirmed | `SETUP_AND_RUN.md:5-16,28` |
| L30 | [bug] "Total Requests" = latency samples; six per query; one more per HTTP call | confirmed | `metrics_collector.py:63-65,81,90-98`, `rag_service.py:63,102,122,143,205` |
| L30 | [bug] pooled percentiles | confirmed (wording softened: generation time is runtime) | `metrics_collector.py:95-102` |
| L30 | [bug] `cutoff` unused | confirmed (added: deque cap of 10,000) | `metrics_collector.py:17,88`, `app/main.py:79` |
| L30 | [misleading] error rate ignores fallbacks | confirmed | `rag_service.py:187-201`, `metrics_collector.py:105`, `observability.py:56` |
| L30 | [misleading] cache hit rate always 0 | confirmed (nothing records `cache_hits`) | `metrics_collector.py:106` |
| L30 | [misleading] "Total Tokens" = completion words only | confirmed | `metrics_collector.py:103` |
| L30 | [misleading] similarity from L2, can go negative | confirmed | `rag_service.py:20,119` |
| L30 | [bug] `gemini-pro` likely rejected | unverified (kept as UNVERIFIED) | `rag_service.py:15` |
| L30 | [shallow] trace lacks query, ids, scores, prompt, model, answer | confirmed | `rag_service.py:95,110,146-150,158,210-216` |
| L30 | [bug] `data/metrics.db` relative path; folder missing outside Docker | confirmed | `metrics_collector.py:13`, `scripts/start.sh:20-27`, `Dockerfile:18` |
| L30 | [shallow] `asyncio.sleep(0)`; PyPI `asyncio` pin | confirmed | `rag_service.py:97-99`, `backend/requirements.txt:15` |
| L30 | Smoke tests check no values; demo sends three queries | confirmed | `scripts/test.sh:23-39`, `scripts/demo.sh:31-44` |
| L30 | Prior copies (CSS missing; chromadb `>=0.5,<0.6`; asyncio pin removed; CPU torch) | confirmed (added: `.gitignore` also missing) | `prior_work/VAI/lesson29/l30-rag-observability/backend/requirements.txt:6`, `.../Dockerfile:10-12` |
| L30 | Try this: list metric names and where each lands | confirmed (doable from the `record` rule) | `metrics_collector.py:63-67`, `rag_service.py:63-208` |
| L31 | `gemini-2.5-flash-lite`, `BLOCK_ONLY_HIGH`, one call | confirmed | `reasoning_engine.py:19,43-44` |
| L31 | Read-in-order key lines | confirmed | `react_planner.py:14-85`, `reasoning_engine.py:47-144`, `schemas.py:5-44`, `routes.py:9-36` |
| L31 | Module-level planner; first observation = task + context | confirmed | `routes.py:7,13`, `react_planner.py:24-28` |
| L31 | Prompt: task, previous thought and action, context, last 5 actions, 0.85 example | confirmed | `reasoning_engine.py:113-141` |
| L31 | Parse: fences, outer braces, `Reasoning` with 0–1 bounds; word-count tokens | confirmed | `reasoning_engine.py:65-78,83`, `schemas.py:8` |
| L31 | Default 10 iterations; stop on `is_terminal` | confirmed | `schemas.py:39`, `react_planner.py:31,50-51` |
| L31 | Next observation built only from model output | confirmed | `react_planner.py:54-60,80-85` |
| L31 | Status COMPLETED vs MAX_ITERATIONS | confirmed | `react_planner.py:70` |
| L31 | README loop and `ObservationStore` | confirmed (no such class) | `README.md:3,40` |
| L31 | Confidence "anchored by" the 0.85 example | unverified (model behaviour) | `reasoning_engine.py:139` |
| L31 | `MAX_ITERATIONS`, `REASONING_TIMEOUT` never read; no upper bound; UI max 20 | confirmed (grep finds no reads) | `core/config.py:8-9`, `schemas.py:39`, `frontend/src/components/PlanningForm.js:35-36` |
| L31 | [misleading] no Act step | confirmed | `react_planner.py:35-60` |
| L31 | [bug] errors reported as COMPLETED | confirmed (added: API-key errors re-raise) | `reasoning_engine.py:92-109`, `react_planner.py:70` |
| L31 | [bug] `total_tokens` never reset; added again by `record_plan` | confirmed | `reasoning_engine.py:45,88`, `react_planner.py:72`, `routes.py:17`, `services/metrics_collector.py:18` |
| L31 | [bug] `max_iterations: 0` crashes at `steps[-1]` | confirmed (no lower bound) | `schemas.py:39`, `react_planner.py:70` |
| L31 | [misleading] any "400" reported as an expired key | confirmed | `routes.py:31-35` |
| L31 | `test.sh` live smoke test, grep-only checks | confirmed | `test.sh:9-43` |
| L31 | python-jose, aiofiles unused | confirmed (grep finds no import) | `backend/requirements.txt:7-8` |
| L31 | Try this: compare L31 `plan` with L32 `execute` | confirmed (both functions exist as named) | `react_planner.py:14`, L32 `backend/agent.py:38` |
| L32 | SDK 0.3.2 with REST transport | confirmed | `backend/requirements.txt:5`, `backend/app.py:45` |
| L32 | Model list; temp 0.2; 512 tokens; no stop sequence | confirmed | `backend/agent.py:17-21,26` |
| L32 | `wikipedia-api` client; one call site | confirmed | `backend/tools.py:50-53`, `backend/agent.py:265` |
| L32 | Read-in-order key lines | confirmed | `tools.py:10-214`, `agent.py:38-359`, `app.py:37-52,94-145`, `test_agent.py:8-38` |
| L32 | Refuses to start without a key; tool names = class name minus "Tool" | confirmed | `app.py:37-43,48-52`, `tools.py:32-36` |
| L32 | New agent per request; default 5; no upper bound; sync `execute` | confirmed | `app.py:55-58,102-114` |
| L32 | Prompt lists tool schemas and the exact format | confirmed | `agent.py:47-65,303-312` |
| L32 | Three parsing regexes | confirmed | `agent.py:318,322,326` |
| L32 | FINISH path; kwargs call; unknown-tool observation; calculator whitelist then `eval` | confirmed | `agent.py:92-106,346-359`, `tools.py:141-148` |
| L32 | Reply + observation + "Continue reasoning:" appended | confirmed | `agent.py:121` |
| L32 | Stop conditions | confirmed | `agent.py:67,77-85,92,123-138` |
| L32 | Retries: 3 attempts, model switch, delay + 5 s up to 120 s, 2 s then 4 s backoff | confirmed (added: 35 s default) | `agent.py:12-14,249-301` |
| L32 | Quota error on the first iteration triggers a keyword fallback that reports success | confirmed | `agent.py:125-129,147-230` |
| L32 | README says Gemini 1.5 Flash | confirmed | `README.md:67` |
| L32 | Wikipedia "exact-title lookup" | corrected (title lookup with no search; redirect handling UNVERIFIED) | `tools.py:58-71,82`, `backend/requirements.txt:7` |
| L32 | README "Enterprise-Ready … retry logic" | confirmed | `README.md:10` |
| L32 | `docs/API.md` shows a price without the "simulated" label | confirmed | `docs/API.md:23,30`, `tools.py:109` |
| L32 | [bug] early stops labelled "Max iterations", `iterations` = limit | confirmed | `agent.py:140-145` |
| L32 | [shallow] no stop sequence; a fake observation stays in the history | confirmed | `agent.py:17-21,121,322` |
| L32 | [shallow] non-greedy Action Input regex breaks nested JSON | confirmed | `agent.py:326,332,342-344` |
| L32 | [bug] sync loop plus `time.sleep` up to 120 s blocks the server | confirmed | `app.py:95,114`, `agent.py:253,293` |
| L32 | [bug] "exceeded" treated as rate limit; `MAX_RATE_LIMIT_RETRIES` unreachable | confirmed | `agent.py:14,263,275-280` |
| L32 | [misleading] stock fallback defaults to GOOGL + AAPL with `success: True` | confirmed | `agent.py:157-160,175` |
| L32 | [misleading] tests pass without a working LLM | corrected (no `configure` call confirmed; whether the SDK finds a key alone is UNVERIFIED; weak asserts confirmed) | `test_agent.py:4-38`, `app.py:45`, `agent.py:144` |
| L32 | [ok-for-demo] `api_key` unused; sessions overwritten | confirmed | `agent.py:28`, `app.py:82,117-121` |
| L32 | Tests skipped without a key; run by `scripts/test.sh`; hard-coded demo data | confirmed | `test_agent.py:8-10`, `scripts/test.sh:20`, `tools.py:96-102,178-184` |
| L32 | Try this: (1) nested JSON fails to parse; (2) "[" defeats `\w+`; (3) first tool runs, fake text kept | confirmed (hand-traced) | `agent.py:77-85,121,318-344` |
| Summary | L28 biggest-problem cell | confirmed (wording: "local (regex) hybrid path") | `tool_equipped_agent.py:105,231-233,243,436-442` |
| Summary | L29 biggest-problem cell | confirmed | `validators.py:34`, `agent_service.py:48,50-52`, `latency_profiler.py:10,17` |
| Summary | L30 biggest-problem cell | confirmed | `metrics_collector.py:63-65,90-102` |
| Summary | L31 biggest-problem cell | confirmed | `react_planner.py:54-60,70` |
| Summary | L32 biggest-problem cell | confirmed | `test_agent.py:20-38`, `agent.py:140-145`, `app.py:114` |
| Cross | Model ids and two SDK pins (0.3.2 and 0.4.0) | confirmed | L28 `requirements.txt:4`; L29, L30, L31, L32 `requirements.txt:5` |
| Cross | "Each lesson writes its own 429 retry and quota fallback" | corrected (retries in L28, L31, L32 only; regex fallbacks in L28 and L32) | L28 `llm_client.py:37-66`, L31 `reasoning_engine.py:14-29`, L32 `agent.py:259-301` |
| Cross | Failures that look like success (five items) | confirmed | see the per-lesson rows above |
| Cross | Word-count tokens; guessed cost | corrected (a cost exists only in L30) | L30 `rag_service.py:140,169,182,186`, L31 `reasoning_engine.py:83` |
| Cross | Untrustworthy latency statistics | confirmed | L29 `latency_profiler.py:10,17`, L30 `metrics_collector.py:95-102` |
| Cross | Toy corpora; no retrieval evaluation; no retrieval tool in a loop | confirmed | L28 `engine.py:48-54`, L30 `rag_service.py:25-31`, L32 `tools.py:46-86` |
| Cross | Sync calls inside async routes | confirmed (L29 only with a key) | L29 `agent_service.py:35`, L30 `rag_service.py:99`, L32 `app.py:114` |
| Cross | `eval` calculators; mock tools | confirmed | L28 `tools/calculator.py:38`, L32 `tools.py:148` |
| Cross | Tests are import checks or smoke tests | confirmed | L28 `test.sh:9-22`, L29 `tests/test_validators.py:4-20`, L30 `scripts/test.sh:23-39`, L31 `test.sh:9-43` |
| Cross | Unused pinned dependencies | confirmed | L28 `requirements.txt:11-14`, L30 `requirements.txt:12,14,15`, L31 `requirements.txt:7-8` |
| Cross | Docs refer to an absent `setup.sh` and the author's home folder | confirmed | L29 `README.md:9`, L30 `SETUP_AND_RUN.md:5,28`, L32 `API_KEY_SETUP.md:17` |
| all | Any API key value in the guide | confirmed none (the only key-like text in these lessons is a placeholder, not a real key) | L32 `API_KEY_SETUP.md:28` |

---

## Verification log (pass B)
Lens: completeness and teaching accuracy. I read every backend `.py` file of L28–L32 in full (L28: `main.py`, `cli.py`, `llm_client.py`, `agent/tool_equipped_agent.py`, `rag/engine.py`, `evaluation/evaluator.py`, `tools/*.py`; L29: `app/main.py`, `models/schemas.py`, `services/*.py`, `tests/test_validators.py`; L30: `app/main.py`, `middleware/observability.py`, `models/telemetry.py`, `services/*.py`; L31: `app/main.py`, `api/routes.py`, `core/config.py`, `models/schemas.py`, `services/*.py`; L32: `app.py`, `agent.py`, `tools.py`, `test_agent.py`). I ran nothing. Paths are relative to each lesson's project folder.

| Lesson | Item | Change | Evidence file:line |
|---|---|---|---|
| L28 | Step-by-step control flow (regex order, classifier, RAG, judge, re-query, tool branch) | confirmed against the code | `tool_equipped_agent.py:54-162,164-210,283-313,412-475`, `rag/engine.py:73-132`, `evaluation/evaluator.py:18-94` |
| L28 | Retry settings missing from the walk-through | added (2 attempts per model, delay at most 60 s / 30 s default, next model; worker thread; only RAG has a timeout) | `llm_client.py:22-29,45-63,69-71`, `rag/engine.py:101,111-114` |
| L28 | "What it is not": "hybrid" naming | added (RAG + tool, not R1 hybrid retrieval) | `tool_equipped_agent.py:85-91,378-410` |
| L28 | Concept mapping | corrected (added R3 counter-example: "rerank" is a slice) | `rag/engine.py:76-77,90-92` |
| L28 | Swap: Cohere `input_type` split | added (UNVERIFIED for the unpinned Chroma) | `rag/engine.py:22-24`, `backend/requirements.txt:5` |
| L28 | Read-in-order App.js key lines | corrected (`quickMode` state and toggle at 10 and 156-158) | `frontend/src/App.js:10,41,149,156-158` |
| L28 | Constant 0.75 shown under a "RAG queries" heading | added | `frontend/src/App.js:109`, `tool_equipped_agent.py:231-233` |
| L28 | Context dump can be judged and score high after a timeout | added (completeness 1.0 is code; judge score UNVERIFIED) | `rag/engine.py:115-117`, `evaluator.py:34` |
| L28 | [bug] LLM hybrid re-query replaces the combined answer with a RAG-only one | added | `tool_equipped_agent.py:99-103,394-409,430-438,144` |
| L28 | [shallow] citations unchecked; all context ids returned as sources; no threshold or abstain rule | added | `rag/engine.py:82-92,103-110,127-132` |
| L28 | [shallow] judge is the generator model | added | `rag/engine.py:112`, `evaluator.py:60,84`, `llm_client.py:41-42` |
| L28 | [shallow] quota fallback in `process_query` is effectively dead | added | `tool_equipped_agent.py:71,150-159,251-253`, `tools/registry.py:17-25` |
| L28 | Calculator: `^` turned into `**`; empty builtins are not a sandbox | added (runtime cost not run) | `tool_equipped_agent.py:171,186`, `tools/calculator.py:38` |
| L28 | Take-away: judge with a different model offline; C5/V1 id check; V3 abstain; live grader vs offline judge | added | `evaluator.py:44-94`, `rag/engine.py:95-110` |
| L28 | Interview answer | confirmed correct | `tool_equipped_agent.py:164-210` |
| L29 | Step-by-step control flow and settings | confirmed against the code | `evaluation_service.py:38-151`, `agent_service.py:16-74`, `validators.py:6-42`, `latency_profiler.py:6-20`, `metrics_service.py:14-81` |
| L29 | Concept mapping | corrected (M3 counter-example; M4 marked weak) | `validators.py:29-42`, `metrics_service.py:14-18` |
| L29 | Short sentences vanish and score 1.0 ("Python 3.12 is fast.") | added (hand count: pieces of 8 and 10 characters, both not over 10) | `validators.py:32,34` |
| L29 | [misleading] "Overall accuracy" mixes a pass rate and a mean score | added | `metrics_service.py:39`, `evaluation_service.py:49-50` |
| L29 | Take-away: groundedness (vs retrieved chunks) and correctness (vs reference) kept apart | added | `validators.py:33`, `agent_service.py:48` |
| L29 | Interview answer | confirmed correct | `validators.py:7-27` |
| L30 | Step-by-step control flow and settings | confirmed against the code | `rag_service.py:41-244`, `metrics_collector.py:51-149`, `observability.py:11-57`, `app/main.py:45-83` |
| L30 | Concept mapping | corrected (C6 noted as no provenance; P4 counter-example added) | `rag_service.py:117-133,119` |
| L30 | Swap: vectors are passed in; Cohere `input_type`; cosine or NumPy dot product | added | `rag_service.py:34-38,112-115` |
| L30 | Error-rate denominator is latency samples, not requests | added (about 1/6 is a hand count) | `metrics_collector.py:90,105`, `observability.py:56` |
| L30 | 1 − squared L2 equals 2·cos − 1 for unit vectors | added (squared L2 and unit-length MiniLM are library behaviour: UNVERIFIED) | `rag_service.py:16,20,119` |
| L30 | Take-away: no book text to hosted tracing; log raw distance and metric name | added | `rag_service.py:117-126` |
| L30 | Interview answer | confirmed correct | `rag_service.py:91-223` |
| L31 | Step-by-step control flow and settings | confirmed against the code | `react_planner.py:14-85`, `reasoning_engine.py:14-147`, `schemas.py:5-44`, `routes.py:9-36` |
| L31 | Concept mapping | corrected ("A5 (as a contrast)" changed to "A5 (counter-example)") | `react_planner.py:35-60` |
| L31 | Invalid JSON or out-of-range confidence also ends as COMPLETED; "exceeded" gets the rate-limit text | added | `reasoning_engine.py:77-78,92-109,97` |
| L31 | Interview answer | corrected (a self-feeding loop can rethink but cannot add facts) | `react_planner.py:54-60` |
| L32 | Step-by-step control flow and settings | confirmed against the code | `agent.py:38-359`, `tools.py:10-214`, `app.py:94-145` |
| L32 | Model index resets per request | added | `app.py:102-106`, `agent.py:31-35` |
| L32 | Swap: Groq `stop` UNVERIFIED for this model, cut at "Observation:" in code; 512-token cap and empty replies | corrected / added | `agent.py:17-21,232-247,77-85` |
| L32 | [bug] calculator whitelist lets `**` through | added (runtime cost not run) | `tools.py:141,148` |
| L32 | [shallow] Wikipedia observation has no URL or revision; 500-character cut; FINISH has no citation field | added | `tools.py:58-63`, `agent.py:92-106` |
| L32 | Take-away: record/replay cache key; offline scripted-model tests that can fail | added | `agent.py:259-301`, `test_agent.py:20-38` |
| L32 | Interview answer | corrected (added the repeated-action guard; cut at "Observation:" as an alternative to a stop sequence) | `agent.py:67,121` |
| Summary | Concept cells for L28, L29, L30, L31 | corrected to match the lesson headers | see the rows above |
| Summary | L28 biggest-problem cell | corrected (re-query can also drop the tool result) | `tool_equipped_agent.py:430-442` |
| Cross | L28 "regex fallback on quota errors" | corrected (the second pass is effectively dead; the real fallback is the context dump) | `tool_equipped_agent.py:71,150-159`, `rag/engine.py:115-126` |
| Cross | New patterns: `**` in both calculators; citations and provenance never checked; LLM grades itself | added | L28 `tool_equipped_agent.py:171,186`, `rag/engine.py:110,127-132`, `evaluator.py:60,84`; L30 `rag_service.py:117-133`; L31 `reasoning_engine.py:139`; L32 `tools.py:63,141` |
| all | API key values | confirmed none in the guide; the only key-like text in these lessons is a placeholder | L32 `API_KEY_SETUP.md:28` |
