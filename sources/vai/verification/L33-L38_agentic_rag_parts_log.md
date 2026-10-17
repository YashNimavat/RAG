# Verification log: VAI lessons 33–38: Reflexion, loop budgets, "agentic RAG", planner, retriever + reranker, validator

[← Lesson guide](../L33-L38_agentic_rag_parts.md) · [← Guide index](../README.md)

Pass A re-opened every cited claim at its source line and tried to refute it. Pass B re-read every backend file with a different lens: control flow, missed issues, concept mapping and fit to your stack. Verdicts: confirmed / corrected / removed / unverified.
## Verification log (pass A)
| Lesson | Claim (short) | Verdict | Evidence file:line |
|---|---|---|---|
| L33 | Actor model `gemini-2.5-flash` via `GEMINI_MODEL_MAIN` | confirmed | `backend/react_agent.py:47` |
| L33 | Critic model via `GEMINI_MODEL_REFLECT` | confirmed | `backend/reflection_engine.py:39` |
| L33 | `google-generativeai==0.8.3`; `redis` listed, never imported | confirmed | `requirements.txt:1,6`; grep: no `import redis` |
| L33 | Dashboard tiles, confidence bars | confirmed | `frontend/src/components/ReflexionDashboard.js:186-260` |
| L33 | Only two `generate_content` calls | confirmed | `backend/react_agent.py:73`; `backend/reflection_engine.py:71` |
| L33 | Read-order key lines (6 rows) | confirmed | all ranges opened; row 6 label clarified |
| L33 | UI resends the received `session_id` | confirmed | `ReflexionDashboard.js:49-55` |
| L33 | `async def` endpoint calls sync `agent.run` | confirmed | `backend/api.py:56-65` |
| L33 | Cap hard-coded 4; `.env` `MAX_REFLECTIONS=3` ignored | confirmed | `backend/api.py:42`; `../setup.sh:55`; `backend/reflexion_agent.py:43` |
| L33 | Prompt: latest reflection only, last 6 history lines, no gen config | confirmed | `backend/react_agent.py:69-70,73,104-110` |
| L33 | First `Action:` regex, one string arg, `Final Answer` unused | confirmed | `backend/react_agent.py:78-79,117-140` |
| L33 | `_is_success` 6 keywords + `< 10` chars | confirmed | `backend/reflexion_agent.py:232-249` |
| L33 | Fail-fast on key/model errors | confirmed | `backend/reflexion_agent.py:91-120` |
| L33 | 429: sleep ≤ 60 s, retry once, not counted | corrected (also fires on the fake tool's "rate limit" text; default 6 s; wrong QUOTA message) | `backend/reflexion_agent.py:123-149,207-223`; `backend/tools.py:14` |
| L33 | Critic temp 0.3, 500 tokens, last 3 reflections, 4 labels | confirmed | `backend/reflection_engine.py:28-32,70-77,99` |
| L33 | Only first critique line kept; 200-char observation stored | confirmed | `backend/reflection_engine.py:122-123`; `backend/reflexion_agent.py:164` |
| L33 | Extra critic call after last attempt | confirmed | `backend/reflexion_agent.py:151-185` |
| L33 | README "LLM-powered critique"; critic verdict never steers | confirmed | `README.md:31`; `backend/reflexion_agent.py:80` |
| L33 | README memory; cross-task leakage via one session | confirmed | `README.md:32`; `ReflexionDashboard.js:51,55`; `backend/reflexion_agent.py:71-74` |
| L33 | README "production-ready"; blocking `time.sleep` | confirmed | `README.md:34`; `backend/reflexion_agent.py:126` |
| L33 | CEO example needs `ceo anthropic`; placeholder passes | confirmed (README line added) | `README.md:53`; `backend/tools.py:16,25` |
| L33 | [bug] `Result: 8` is 9 chars → failure → retries | corrected (softened: unless the model changes its action) | `backend/reflexion_agent.py:248`; `backend/tools.py:36`; `tests/test_reflexion.py:57` |
| L33 | [bug] "No Wikipedia article found" passes; "invalid" fails | confirmed | `backend/tools.py:57`; `backend/reflexion_agent.py:232-245` |
| L33 | [misleading] "Most" failures random 20%/15% | corrected ("Many"; search one goes to quota path first) | `backend/tools.py:13,43`; `backend/reflexion_agent.py:123` |
| L33 | [misleading] Success Rate = critic `SUCCESS: true` share | corrected (adds no-reflection fallback) | `backend/reflection_engine.py:156-171`; `ReflexionDashboard.js:200-202` |
| L33 | [shallow] confidence self-reported | confirmed | `backend/reflection_engine.py:126-131` |
| L33 | [bug] global agent unsafe under concurrency | corrected (latent: blocking endpoint serializes requests today) | `backend/api.py:42,57-65`; `backend/react_agent.py:49` |
| L33 | [ok-for-demo] calculator `eval` after whitelist | confirmed | `backend/tools.py:31-35` |
| L33 | Tests need `GEMINI_API_KEY` exported | corrected (errors are caught; tests likely pass without a key; UNVERIFIED) | `tests/test_reflexion.py:1-13`; `scripts/test.sh:7`; `backend/react_agent.py:91-92` |
| L33 | Asserts only keys and `attempts <= max` | confirmed | `tests/test_reflexion.py:26-29,59-61,71,79-83` |
| L33 | No data files | confirmed | file listing |
| L33 | Try this: doable with 8 strings | corrected ("copy" → re-write in own words; tools not needed) | `backend/reflexion_agent.py:232-249` |
| L33 | Summary cell | confirmed | `backend/reflexion_agent.py:248`; `backend/tools.py:25` |
| L34 | `google-generativeai==0.3.2` | confirmed | `backend/requirements.txt:4` |
| L34 | `gemini-1.5-flash`; may no longer be served | unverified (provider-side) | `backend/app/gemini_client.py:16` |
| L34 | Silent mock fallback | confirmed (cite `:36-37` added) | `backend/app/gemini_client.py:9-18,36-44` |
| L34 | Frontend cite only covered the chart | corrected (PolicyViewer, AgentExecutor named) | `frontend/src/components/MetricsDashboard.js:5-82`; `App.js:53-57` |
| L34 | `generate` is the only LLM seam | confirmed | `backend/app/gemini_client.py:34-44` |
| L34 | Read-order key lines (5 rows) | confirmed | all ranges opened |
| L34 | Policies 50/500k, 20/100k, 10/50k | confirmed | `config/*_policy.json:2-3` |
| L34 | `environment` into path; overrides; new client per request | confirmed | `backend/main.py:48,52-55,58-59` |
| L34 | Loop until "COMPLETE" | confirmed | `backend/app/execution_controller.py:24,39-40,141-150` |
| L34 | Plan prompt, last 3 steps × 100 chars, JSON, `analyze` fallback | confirmed; "Gemini often fences" softened (unverified) | `backend/app/execution_controller.py:52-80,128-139` |
| L34 | Fake tools | confirmed | `backend/app/execution_controller.py:112-126` |
| L34 | Reflect prompt CONTINUE/COMPLETE | confirmed | `backend/app/execution_controller.py:93-101` |
| L34 | `len//4`, +1 per call, check after, `>=` | confirmed | `backend/app/gemini_client.py:40-41`; `backend/app/budget_manager.py:27-36,42,54` |
| L34 | Synthesis; "Task interrupted" message | confirmed | `backend/app/execution_controller.py:44-46,152-182` |
| L34 | `success=True` returned | confirmed | `backend/main.py:62-79` |
| L34 | README token-per-turn vs cumulative | confirmed | `README.md:38`; `backend/app/budget_manager.py:21,41` |
| L34 | README warn/strict; `enforcement_mode` unread | confirmed | `README.md:53-55`; `frontend/src/components/PolicyViewer.js:29`; grep |
| L34 | README cost monitoring | confirmed | `README.md:3` |
| L34 | README circuit breakers | confirmed | `README.md:40` |
| L34 | README "L35 will use" | confirmed | `README.md:84` |
| L34 | [bug] exception caught in `run`; violations always 0 | confirmed | `backend/app/execution_controller.py:44-46`; `backend/main.py:81-98,119-126` |
| L34 | [bug] 10 calls = 5 plan + 5 reflect; 10th thrown away | confirmed (user sees "Completed 4 steps") | `backend/app/budget_manager.py:29,42,54`; `execution_controller.py:32-36,178-180` |
| L34 | [bug] substring stop rule | confirmed | `backend/app/execution_controller.py:144,150` |
| L34 | [misleading] mock always COMPLETE, 3 iterations, dotenv unused | confirmed | `backend/app/gemini_client.py:24,26`; grep: no `dotenv` import |
| L34 | [bug] bare `eval` | confirmed | `backend/app/execution_controller.py:119` |
| L34 | [bug] path traversal | corrected (only `*_policy.json` files reachable) | `backend/main.py:48` |
| L34 | [shallow] `len//4`; `is_approaching_limit` unused; fake async | confirmed | `backend/app/gemini_client.py:22,46-48`; `budget_manager.py:72-77`; grep |
| L34 | test.sh asserts only HTTP 200 | corrected (`curl -f`: any non-error status) | `scripts/test.sh:17-43` |
| L34 | Try this: doable on paper | confirmed | `execution_controller.py`; `budget_manager.py` |
| L34 | Summary cell | confirmed | `backend/app/execution_controller.py:44-46`; `backend/main.py:73-98` |
| L35 | Model id set in 3 agents, only synth calls it | confirmed | `backend/agents/*_agent.py:10`; `synthesizer_agent.py:31` |
| L35 | `google-generativeai==0.8.3` | confirmed | `backend/requirements.txt:4` |
| L35 | UI lines | confirmed (approximate ranges) | `frontend/src/App.jsx:20-55,330-345` |
| L35 | Read-order key lines (6 rows) | confirmed | all ranges opened |
| L35 | `/query` default 3000 at `:35-41` | corrected (default is at `:25`) | `backend/main.py:25,35-41` |
| L35 | WebSocket path pushes state | confirmed | `backend/main.py:50-75`; `orchestrator.py:30-38` |
| L35 | Split 30/20/15/35 | confirmed | `backend/services/budget_manager.py:6-11` |
| L35 | Planner words × 10; constant plan; no LLM | confirmed | `backend/agents/planner_agent.py:16,27-33` |
| L35 | Retriever 0.5 s sleep; fixed 0.95/0.92/0.88 | confirmed | `backend/agents/retriever_agent.py:15,21,27,38,47` |
| L35 | Validator mean ≈ 0.92 ≥ 0.7; no retry | confirmed | `backend/agents/validator_agent.py:30-41`; `orchestrator.py:94-99` |
| L35 | Synth `[Source:]` prompt; word tokens; check after call | confirmed | `backend/agents/synthesizer_agent.py:21-41` |
| L35 | COMPLETED + metadata | confirmed | `backend/services/orchestrator.py:126-131` |
| L35 | README 4 agent claims; citations field dropped | confirmed | `README.md:22-25`; `synthesizer_agent.py:47`; `orchestrator.py:122` |
| L35 | [misleading] synth fallback `success=True` | corrected (text carries an `[API fallback]` note) | `backend/agents/synthesizer_agent.py:57-77,66` |
| L35 | [bug] `reserve()` ignored → overspend never enforced | corrected (agents self-check; real effect is under-reported `used`) | `orchestrator.py:63,82,103,124`; `budget_manager.py:19-23`; `planner_agent.py:18`; `retriever_agent.py:43`; `synthesizer_agent.py:36` |
| L35 | [bug] retriever trims but reports full count; zero docs | corrected (conditions: `max_tokens` < 300 / < 100) | `backend/agents/retriever_agent.py:41-47`; `validator_agent.py:23-28` |
| L35 | [misleading] `iterations_used` always 0 | confirmed | `budget_manager.py:50`; grep: `next_iteration` never called; `orchestrator.py:130` |
| L35 | [shallow] all tokens word-count guesses | corrected (retriever/validator use per-doc constants) | `retriever_agent.py:41`; `validator_agent.py:43` |
| L35 | [ok-for-demo] global `orchestrator` unused | confirmed | `backend/main.py:21,39,61` |
| L35 | Tests mock synth; 4 constant tests | confirmed | `backend/tests/test_pipeline.py:12-36,39-77` |
| L35 | `pytest-asyncio` missing → async tests not run | confirmed (missing); exact pytest behaviour unverified | `backend/requirements.txt:1-9`; `test.sh:9-19` |
| L35 | Data: three one-line strings | confirmed | `backend/agents/retriever_agent.py:10-29` |
| L35 | Try this: `process_query` exists | confirmed | `backend/services/orchestrator.py:40` |
| L35 | Summary cell | confirmed | `retriever_agent.py:10-47`; `synthesizer_agent.py:57-77` |
| L36 | requirements; model id; README "Gemini 2.0 Flash" | confirmed | `backend/requirements.txt:1-4`; `backend/app/planner.py:43`; `README.md:28` |
| L36 | UI cards, badges, 5 s polling | confirmed | `frontend/src/App.js:25-38,185-220` |
| L36 | One call | confirmed | `backend/app/planner.py:87-94` |
| L36 | Read-order key lines (4 rows) | confirmed | all ranges opened |
| L36 | `max_sub_queries` 1–10; refuses to start without key | confirmed | `backend/app/models.py:24`; `backend/app/main.py:38-40` |
| L36 | Prompt paraphrase | confirmed | `backend/app/planner.py:12-36` |
| L36 | 5 s `wait_for` around executor; thread keeps running | confirmed; "still billed" marked unverified | `backend/app/planner.py:41,60-63,87-94` |
| L36 | Fence strip, `json.loads`, 4 keys | confirmed | `backend/app/planner.py:96-128` |
| L36 | Pydantic limits 5–500, 10–200, max 5, Literal strategy | confirmed (complexity Literal added) | `backend/app/models.py:8-18` |
| L36 | Any exception → fallback | confirmed | `backend/app/planner.py:80-85,130-145` |
| L36 | main counts success | confirmed | `backend/app/main.py:59-75` |
| L36 | README Pydantic / strategy / timeout claims | confirmed | `README.md:33,34,37` |
| L36 | README "3-4 sub-queries" | unverified (live model) | `README.md:46-48` |
| L36 | [bug] API 10 vs model 5 | confirmed | `backend/app/models.py:16,24` |
| L36 | [bug] no clamp; limit test fails with live key | confirmed | `backend/tests/test_planner.py:34-42` |
| L36 | [bug] placeholder strategy / long rationale → fallback | confirmed | `backend/app/planner.py:23`; `models.py:9,17` |
| L36 | [misleading] fallback = success; never raises | corrected (3–4-char query makes the fallback itself raise; log line also a trace) | `backend/app/models.py:8,23`; `backend/app/main.py:63,77-87,103` |
| L36 | [shallow] `requires_decomposition` unchecked | confirmed | `backend/app/models.py:12-19` |
| L36 | Tests use `"test-key"`; fallback passes; one deterministic | confirmed | `backend/tests/test_planner.py:9,30,44-50` |
| L36 | demo.sh 3 queries | confirmed | `demo.sh:33-55` |
| L36 | Try this: doable | confirmed | prompt `backend/app/planner.py:12-36` |
| L36 | Summary cell | confirmed | `backend/app/models.py:9,16,24`; `main.py:63` |
| L37 | chromadb 0.4.24, ST 2.5.1, MiniLM, BM25Okapi | confirmed | `backend/requirements.txt:5-6,10`; `backend/vector_store.py:18,86-87` |
| L37 | `gemini-1.5-flash` planner + reranker | confirmed; "may no longer be served" unverified | `backend/planner_agent.py:18`; `backend/reranker_tool.py:19` |
| L37 | redis/prometheus/otel/tiktoken unused | confirmed | `backend/requirements.txt:11-16`; grep over `backend/*.py` |
| L37 | UI toggles and score badges | confirmed | `frontend/src/App.js:65-69`; `RetrievalResults.js:22-34` |
| L37 | "7 one-sentence chunks" | corrected (one or two sentences each) | `backend/vector_store.py:32-68` |
| L37 | Read-order key lines (5 rows) | confirmed | all ranges opened |
| L37 | Startup builds collection + BM25 | confirmed (lifespan cite added) | `backend/main.py:30-36`; `backend/vector_store.py:22-89,132-134` |
| L37 | Defaults 10 / True / False | confirmed (UI hard-codes 10 added) | `backend/main.py:49-53`; `frontend/src/App.js:67` |
| L37 | Planner 2–4, `[query]` on error, own planner | confirmed (non-list path + README "from L36" added) | `backend/planner_agent.py:13,23-28,39-48`; `README.md:7` |
| L37 | `top_k=100` capped at 7; original never searched | corrected (searched when planner falls back) | `backend/retriever_agent.py:48-53`; `backend/vector_store.py:97`; `planner_agent.py:46-48` |
| L37 | `1 − distance` = 2·cos − 1 under default squared L2 | unverified (library defaults); order unchanged added | `backend/vector_store.py:29,106` |
| L37 | RRF `1/(60+rank)` | confirmed | `backend/retriever_agent.py:122-164` |
| L37 | Merge by `hash(content)`, keep higher `vector_score` | confirmed | `backend/retriever_agent.py:166-181` |
| L37 | Rerank: batch 50, 500 chars, 0–100, temp 0, 1000 tokens, pad zeros | confirmed | `backend/reranker_tool.py:22,96-123,132-135` |
| L37 | Response fields | confirmed | `backend/main.py:96-113` |
| L37 | README "cross-encoder" vs listwise LLM | confirmed | `README.md:9`; `backend/reranker_tool.py:13-16,101-112` |
| L37 | README hybrid; "RRF computed correctly" | corrected (formula right; BM25 list keeps zero-score chunks) | `backend/vector_store.py:117`; `retriever_agent.py:127-148` |
| L37 | README parallel; only reranker concurrent | corrected (only one batch ever with 7 chunks) | `backend/vector_store.py:93-98`; `reranker_tool.py:22,48-49,116` |
| L37 | README graceful fallback unreachable | confirmed ("practically") | `backend/reranker_tool.py:87-90,146-152`; `retriever_agent.py:83-90` |
| L37 | [bug] hybrid toggle has no effect | confirmed | `backend/retriever_agent.py:92-97,159-162` |
| L37 | [bug] Gemini fail → zeros, merge order | corrected (RRF order in hybrid; metric still counts "reranked") | `backend/reranker_tool.py:146-152`; `metrics_collector.py:29,35`; `RetrievalResults.js:27-31` |
| L37 | [misleading] no real timeout | confirmed | `backend/reranker_tool.py:29,72-75` |
| L37 | [shallow] top_k 10 > 7, reorder only | confirmed | `backend/main.py:51`; `vector_store.py:97` |
| L37 | [shallow] planner output unvalidated; dropped "silently" | corrected (logged; response model likely rejects; UNVERIFIED) | `backend/planner_agent.py:37-44`; `retriever_agent.py:55-63`; `main.py:58` |
| L37 | [shallow] pads or truncates silently | corrected (pad logs a warning; truncation silent) | `backend/reranker_tool.py:132-139` |
| L37 | [ok-for-demo] `asyncio==3.4.3` | confirmed | `backend/requirements.txt:13` |
| L37 | No tests | confirmed | file listing |
| L37 | Try this: hand BM25/RRF, read `retrieve()` | corrected (assume one search list; tokenizer cite added) | `backend/planner_agent.py:46-48`; `vector_store.py:132-134` |
| L37 | Summary cell | confirmed | `backend/retriever_agent.py:92-97`; `reranker_tool.py:146-152` |
| L38 | requirements; model id; jose/passlib unused | confirmed | `backend/requirements.txt:1-9`; `backend/config/settings.py:10`; grep |
| L38 | Dashboard pre-fill $50M/$50M/$48M | confirmed | `frontend/src/components/ValidatorDashboard.js:6-10` |
| L38 | One call; Redis optional | confirmed | `backend/services/gemini_client.py:40`; `cache_service.py:25-27` |
| L38 | Read-order key lines (5 rows) | confirmed | all ranges opened |
| L38 | Endpoint, max 20, < 2 docs skipped | confirmed | `backend/app/api/validator.py:10-23`; `validator_service.py:87-105` |
| L38 | All pairs; 20 docs → 190 calls | confirmed | `backend/services/validator_service.py:17-24` |
| L38 | MD5 of sorted ids; cache hit | confirmed | `backend/services/validator_service.py:26-30,38-42` |
| L38 | Semaphore 5, 10 s `wait_for` | confirmed | `validator_service.py:45-51`; `settings.py:19-20` |
| L38 | Prompt, 1000 chars, no temperature, 3 keys | confirmed | `backend/services/gemini_client.py:18-53` |
| L38 | Errors → 0.7 / [] / 0.0 | confirmed | `gemini_client.py:57-64`; `validator_service.py:66-81` |
| L38 | TTL 3600 | confirmed | `settings.py:16`; `cache_service.py:56-60` |
| L38 | Aggregation and thresholds | confirmed | `backend/services/validator_service.py:120-146,162` |
| L38 | README pairwise / LLM | confirmed | `README.md:9-10` |
| L38 | README parallel: sync call blocks loop | confirmed | `README.md:12`; `gemini_client.py:14,40` |
| L38 | README timeout does not bound latency | confirmed | `README.md:14`; `validator_service.py:48-51` |
| L38 | README `./setup.sh` missing; demo.sh path wrong | confirmed | `README.md:38`; `demo.sh:5-6,17`; `scripts/start.sh` exists |
| L38 | README sample numbers | unverified (illustrative) | `README.md:120-129` |
| L38 | [bug] cache key ignores content | corrected (only when Redis is running) | `validator_service.py:26-30`; `cache_service.py:36-37`; `tests/test_validator.py:17-25` |
| L38 | [bug] fail-open → "passed" | corrected (passed with 3 docs; float rounding gives "warning" with 4; never "failed") | `validator_service.py:138-146`; arithmetic of `sum/len` |
| L38 | Client-side fallback cached for an hour | confirmed (service-level fallbacks are not cached) | `validator_service.py:53-62,66-81` |
| L38 | [shallow] averaging hides a contradiction | corrected (pair still listed in `high_conflict_pairs`) | `validator_service.py:127-133,138,149-152` |
| L38 | [shallow] unrelated docs; `score` unused; confidence self-reported | confirmed | `gemini_client.py:33-36`; `models/document.py:8`; grep `.score` |
| L38 | [bug] 400 turned into 500 | confirmed | `backend/app/api/validator.py:15-29` |
| L38 | [bug] duplicate `doc{count+1}` ids | confirmed | `ValidatorDashboard.js:34-36,51-52`; `validator_service.py:120-125` |
| L38 | [ok-for-demo] unused settings; WS echo | confirmed | `settings.py:22,25`; grep; `backend/app/main.py:77-86` |
| L38 | Tests: pair count + hash symmetry | confirmed | `backend/tests/test_validator.py:5-25` |
| L38 | Fixture in demo.sh | confirmed | `demo.sh:35-38` |
| L38 | Try this: doable | confirmed | prompt `gemini_client.py:18-37` |
| L38 | Summary cell | corrected ("passed (or warning)"; only client-side fallback cached) | `validator_service.py:53-62,141-146` |
| Cross | Silent fallbacks as success | corrected (L38 wording) | see L34–L38 rows |
| Cross | Token guesses; checks after paid call | confirmed (L35 per-doc constants added) | `budget_manager.py:54`; `synthesizer_agent.py:36-41` |
| Cross | Control by substring | confirmed (L33 quota match added) | `reflexion_agent.py:207-216`; `execution_controller.py:144` |
| Cross | Sync Gemini in `async def` | confirmed | L33 `api.py:57-65`; L34 `gemini_client.py:46-48`; L35 `synthesizer_agent.py:31`; L37 `planner_agent.py:31`; L38 `gemini_client.py:40` |
| Cross | Old/experimental model ids | unverified (provider-side) | model-id rows above |
| Cross | Copied infra incl. Redis never imported | corrected (L38 does use Redis) | L38 `backend/services/cache_service.py:1` |
| Cross | Tests never measure quality | confirmed | test rows above |
| Cross | JSON parsed by stripping fences (L34, L36, L37, L38) | corrected (L34 does not strip fences) | L34 `backend/app/execution_controller.py:73-80` |
| All | Hard-coded API keys in guide or block source | confirmed none | grep for the Google API-key prefix over lessons 33–38 (incl. `lesson38/.../backend/.env.example`): no matches |

## Verification log (pass B)
Lens: completeness and teaching accuracy. All backend `.py` files of L33–L38 were re-read in full, plus the tests, the READMEs, `demo.sh`/`start.sh`, `docker-compose.yml` and the relevant frontend lines. Concept IDs were checked against `rag_learning/02_RAG_MASTER_LEARNING_PLAN.md` (A1–A5 definitions at lines 950–1023).

| Lesson | Item | Change | Evidence file:line |
|---|---|---|---|
| L33 | Step-by-step steps 1–9 (loop, prompt, regex, `_is_success`, fail-fast, quota retry, critic, parser, final critic call) | confirmed, no change | `backend/reflexion_agent.py:59-185,207-253`; `backend/react_agent.py:51-140`; `backend/reflection_engine.py:61-133`; `backend/api.py:42,56-65` |
| L33 | Concept mapping | corrected: A4 removed (curriculum A4 = user-feedback loops, Ch17); A5 added; A2/A3 marked shape only; M3 added as counter-example | `02_RAG_MASTER_LEARNING_PLAN.md:996-1015` (curriculum); no feedback input anywhere in `backend/` |
| L33 | Swap line: critic 500-token cap vs reasoning model | added (reasoning-token accounting UNVERIFIED) | `backend/reflection_engine.py:75` |
| L33 | `_is_success` ignores `task` | added to step 5 | `backend/reflexion_agent.py:225,251-253` |
| L33 | One tool call per attempt; multi-step tasks cannot finish | added [shallow] | `backend/react_agent.py:117-120`; `backend/reflexion_agent.py:80-88` |
| L33 | Critic `SUCCESS` parsed by a substring test | added [bug] | `backend/reflection_engine.py:120-121` |
| L33 | Random tool failures with no seed (not replayable) | added to [misleading] bullet | `backend/tools.py:6,13,43` |
| L33 | Take: critic on Groq, cached, JSON verdict, no book text | added | stack rules (CLAUDE.md); parser `backend/reflection_engine.py:108-133` |
| L33 | Interview answer (Reflexion vs retry) | confirmed technically correct | `backend/reflexion_agent.py:151-167` |
| L34 | Step-by-step steps 1–8; 10-call trace (5 plan + 5 reflect, 10th raises, "Completed 4 steps") | confirmed by re-tracing | `backend/app/budget_manager.py:27-54`; `backend/app/execution_controller.py:21-46,174-182` |
| L34 | Concept mapping | corrected: A4 removed, A5 kept | `02_RAG_MASTER_LEARNING_PLAN.md:996-1015` |
| L34 | Where the key comes from (shell or Docker only) | added to [misleading] mock bullet | `scripts/start.sh:38`; `docker-compose.yml:11`; `backend/app/gemini_client.py:13` |
| L34 | Derived metrics inherit `len//4`; no output cap per call | added to [shallow] bullet | `backend/app/budget_manager.py:65-68`; `backend/app/gemini_client.py:39` |
| L34 | Take: reasoning tokens in budget; replay-mode usage accounting | added (Groq usage field names UNVERIFIED) | `backend/app/gemini_client.py:40-41` (what not to copy) |
| L34 | Interview answer (stopping runaway cost) | confirmed | `backend/main.py:73-79` |
| L35 | Step-by-step steps 1–7 | confirmed, no change | `backend/services/orchestrator.py:40-139`; `backend/agents/*.py`; `backend/main.py:25,35-41` |
| L35 | Concept mapping | corrected: V2 added as counter-example | `backend/agents/validator_agent.py:30-41` |
| L35 | Fallback clamps its token count to the budget | added to [misleading] fallback bullet | `backend/agents/synthesizer_agent.py:75` |
| L35 | Constant relevance/confidence shown in UI; "semantic" strategy label with no search | added [misleading] | `frontend/src/App.jsx:434,453`; `backend/agents/retriever_agent.py:15,21,27`; `backend/agents/planner_agent.py:32` |
| L35 | `test_budget_enforcement` cannot fail | added to Tests | `backend/tests/test_pipeline.py:24,50-56`; `backend/services/orchestrator.py:55-59` |
| L35 | Interview answer (what makes RAG agentic) | confirmed | `backend/services/orchestrator.py:40-139` (no decision points) |
| L36 | Step-by-step steps 1–7 | confirmed | `backend/app/planner.py:47-145`; `backend/app/models.py:8-24`; `backend/app/main.py:38-87` |
| L36 | Concept mapping | corrected: A1 marked weak (flag only counted, never acted on) | `backend/app/main.py:68-69` |
| L36 | No temperature, JSON mode or output cap | added to step 3 | `backend/app/planner.py:92` |
| L36 | Take: plain-Python Groq + Pydantic + cache; `decompositions_with_plan` as a rough signal | added | `backend/app/main.py:68-69,101-103` |
| L36 | Interview answer | corrected: added the sequential (multi-hop) case | `backend/app/models.py:10` (`requires_previous`, never executed) |
| L37 | Step-by-step steps 1–9 | confirmed, no change | `backend/main.py:30-36,49-113`; `backend/retriever_agent.py:46-181`; `backend/vector_store.py:22-134`; `backend/reranker_tool.py:24-152` |
| L37 | Concept mapping | corrected: P4 added (counter-example); cross-encoder named as counter-example inside R3; R1 note | `backend/vector_store.py:106`; `README.md:9`; `backend/retriever_agent.py:92-97` |
| L37 | Gemini library version | added to Stack | `backend/requirements.txt:4` |
| L37 | Merge keeps the copy with the best `vector_score`, so the wrong `rrf_score` survives | added [bug] | `backend/retriever_agent.py:166-181` |
| L37 | Rerank scores matched to chunks by position; padding gives the last chunk a 0 | added [bug] | `backend/reranker_tool.py:111,132-135,139` |
| L37 | `1 - distance` labelled similarity, shown ×100, averaged | added [misleading] (exact formula UNVERIFIED: Chroma default metric) | `backend/vector_store.py:29,106`; `frontend/src/components/RetrievalResults.js:22-25`; `backend/main.py:102` |
| L37 | BM25 tokenizer: no stemming, no stop words | added [shallow] | `backend/vector_store.py:132-134` |
| L37 | Take: Groq rerank variant settings, `{id, score}` output, caching, no book text to Cohere/Groq, cosine not `1 - distance` | added | `backend/reranker_tool.py:111,116-123` (what not to copy) |
| L37 | Try this: "count shared words" is not BM25 | corrected: exact-token matches weighted by IDF; only 2 of 7 chunks share a token with the query; Cluster Autoscaler scores 0 yet is ranked | `backend/vector_store.py:32-68,117,132-134` |
| L37 | Interview answer (bi-encoder vs cross-encoder vs LLM reranker) | confirmed technically correct | `backend/reranker_tool.py:101-112` |
| L38 | Step-by-step steps 1–8 | confirmed, no change | `backend/services/validator_service.py:17-174`; `backend/services/gemini_client.py:14-64`; `backend/services/cache_service.py:14-62` |
| L38 | Concept mapping (V2 adjacent, V4, M3, D2) | confirmed | `backend/services/gemini_client.py:18-37` (doc vs doc, no answer) |
| L38 | Fixture wording: one snippet says "earnings", not "revenue" | corrected in Stack and in Tests and data | `frontend/src/components/ValidatorDashboard.js:7-9`; `demo.sh:36-38` |
| L38 | Conflict blamed on both docs; source/timestamp/score unused | added [shallow] | `backend/services/validator_service.py:123-125`; `backend/models/document.py:8-11`; `backend/config/settings.py:22` |
| L38 | Each document cut to 1,000 characters before judging | added [shallow] | `backend/services/gemini_client.py:21,24` |
| L38 | Take: fixture test case without ambiguity; judge = Cohere + Codex calibration, run once at the end; Groq only for prompt shaping; cache; "which chunk was trusted" trace field | corrected and added | CLAUDE.md judge decision; `backend/services/validator_service.py:53-62` |
| L38 | Interview answer (contradiction detection cost) | confirmed | `backend/services/validator_service.py:17-24` |
| Block | Summary table concept cells (L33–L37) and L37 problem cell | corrected to match the lesson headers | see rows above |
| Block | Cross-lesson: "scores shown as measurements" bullet; concept-mapping note; L35 test that cannot fail | added | see rows above |
| All | Hard-coded API keys in the guide or block source | confirmed none (re-grep for the Google key prefix; `.env.example` values not printed) | `lesson38/l38-validator-agent-consistency/backend/.env.example:1` holds a placeholder value (checked by pattern, value not printed) |
