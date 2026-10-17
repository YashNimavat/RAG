# Verification log: VAI lessons 1–9: foundations

[← Lesson guide](../L01-L09_foundations.md) · [← Guide index](../README.md)

Pass A re-opened every cited claim at its source line and tried to refute it. Pass B re-read every backend file with a different lens: control flow, missed issues, concept mapping and fit to your stack. Verdicts: confirmed / corrected / removed / unverified.
## Verification log (pass A)
Method: each claim was checked by opening the cited lines in the read-only repo. Nothing was run. Paths are relative to each lesson's project folder, as in the guide.

| Lesson | Claim (short) | Verdict | Evidence file:line |
|---|---|---|---|
| L1 | Gemini SDK only imported, never called | confirmed | `src/main.py:17`; `src/validate_environment.py:14`, `:37` |
| L1 | Pins FastAPI 0.109, Pydantic 2.5, `google-generativeai==0.3.2` | confirmed | `requirements.txt:2-10` |
| L1 | `.env.example` names `gemini-pro`; nothing reads it | confirmed | `.env.example:3`; no reader of `GEMINI_MODEL` in `src/`, `scripts/`, `tests/` |
| L1 | Dashboard HTML served from `app.py` | confirmed | `src/app.py:32-158` |
| L1 | Read-order key lines | confirmed | `src/validate_environment.py:9-18`, `:20-28`; `src/app.py:17-25`, `:170-197`; `tests/test_app.py:35-52` |
| L1 | setup.sh "logs installed whatever happened" | corrected | `set -e` at `../setup.sh:12`; pip output hidden at `:164`, `:169`, `:173` |
| L1 | `.env.example` with key written and copied to `.env` | confirmed | `../setup.sh:178-193` |
| L1 | `/api/demo` sleeps 0.1 s, bumps 3 counters and running mean | confirmed | `src/app.py:170-191` |
| L1 | JS polls every 1 s plus meta refresh every 2 s | confirmed | `src/app.py:154`, `:40` |
| L1 | README folders are empty, made by setup.sh, absent here | confirmed | `README.md:21-36`; `../setup.sh:73-77`; `src/` holds only 4 files |
| L1 | README never mentions `app.py` or the dashboard | confirmed | `README.md:1-56` |
| L1 | [misleading] "Total Requests" counts only demo calls; RPS = demo / uptime | confirmed | `src/app.py:180`, `:166` |
| L1 | [bug] Silent install, success always printed | corrected | `../setup.sh:12`, `:169-174` |
| L1 | [ok-for-demo] Version check rejects a future 4.0 | confirmed | `src/validate_environment.py:23` |
| L1 | [bug, D4] Key in committed example file | confirmed | `.env.example:2`; `.gitignore:41` ignores `.env` only |
| L1 | `test_environment` needs `venv/` and `.env` in cwd | confirmed | `tests/test_environment.py:22-27` |
| L1 | `test_app` checks status codes and that counters rise | confirmed | `tests/test_app.py:16-72` |
| L1 | Try this: RPS after 10 calls in 100 s | confirmed (doable) | `src/app.py:160-197` |
| L2 | REST call to `gemini-2.0-flash-exp`; key hard-coded | confirmed | `backend/app/main.py:145`, `:144` |
| L2 | UI: five metric cards, prompts one per line | confirmed | `frontend/src/components/Dashboard.js:65-81`, `:102`, `:39` |
| L2 | Only `call_gemini_api` talks to the provider | confirmed | `backend/app/main.py:149-189` |
| L2 | `AgentRequest`: id regex, 1-100 prompts, temp 0-2, tokens 1-8192 | confirmed | `backend/app/main.py:30-41` |
| L2 | Read-order key lines (decorators, call, fan-out, test.sh) | confirmed | `backend/app/main.py:77-138`, `:149-189`, `:191-211`; `scripts/test.sh:41-55` |
| L2 | `/process` validates; id = `agent-` + 8 chars | confirmed | `backend/app/main.py:217-218`, `:32` |
| L2 | "Wrapped first by with_cache, then by tracking" | corrected (cache is the outer wrapper) | `backend/app/main.py:191-192` |
| L2 | Cache TTL 300 s, key from name + `str(args)` | confirmed | `backend/app/main.py:101`, `:191` |
| L2 | `gather(return_exceptions=True)`, no cap, up to 100 prompts | confirmed | `backend/app/main.py:195-200`, `:33` |
| L2 | 30 s total timeout; temperature and maxOutputTokens sent | confirmed | `backend/app/main.py:153-164` |
| L2 | Retry waits 1 s then 2 s, no jitter | confirmed | `backend/app/main.py:82-91`, `:149` |
| L2 | Returns `(results, cached)`; `/metrics` from global dict | confirmed | `backend/app/main.py:115`, `:227-241`, `:247-263` |
| L2 | README "1000+ concurrent requests" | confirmed (unmeasured) | `README.md:23` |
| L2 | README "Retry"; default fallback turns errors into `[DEMO]` strings | confirmed | `README.md:24`; `backend/app/main.py:147`, `:169-189` |
| L2 | Generator lacks the fallback | corrected (line range) | `../setup.sh:173-200` |
| L2 | "What it is not": retry does not retry | corrected (default mode only) | `backend/app/main.py:147`, `:184-189` |
| L2 | [bug] Fallback off: every error becomes 500, 400 retried like 429 | confirmed | `backend/app/main.py:174`, `:184-189` |
| L2 | [bug] Fallback and error strings cached 300 s | confirmed | `backend/app/main.py:113-115`, `:207` |
| L2 | [misleading] `success_rate` counts fallbacks as successes | confirmed | `backend/app/main.py:126-129`, `:204-209` |
| L2 | [misleading] Cache hits skip tracking | confirmed | `backend/app/main.py:191-192`, `:104-109` |
| L2 | [shallow] Cache freezes one sample; `str(args)` key | confirmed | `backend/app/main.py:101` |
| L2 | [misleading] `active_tasks` counts all loop tasks | confirmed | `backend/app/main.py:255` |
| L2 | [bug] Load-test ids fail the regex (422), output hidden | confirmed | `scripts/test.sh:47`, `:51`; `backend/app/main.py:32` |
| L2 | [bug, D4] Key hard-coded and sent in URL | confirmed | `backend/app/main.py:144`, `:162` |
| L2 | No Python tests, no data | confirmed | folder listing |
| L2 | Try this: 429 twice, fallback on/off | confirmed (doable) | `backend/app/main.py:77-93`, `:149-211` |
| L3 | Stack "NumPy only" | corrected (`google-generativeai` pinned, unused) | `backend/requirements.txt:9` |
| L3 | Gemini key stored in config | confirmed | `backend/app/config.py:4` |
| L3 | Attention math: QKᵀ/√d_k, mask, stable softmax | confirmed | `backend/app/transformer.py:63-82`, `:84-88` |
| L3 | Head split/merge and sin/cos PE correct | confirmed | `backend/app/transformer.py:116-132`, `:192-205` |
| L3 | Embeddings are fresh random noise, token ids ignored | confirmed | `backend/app/transformer.py:365-368` |
| L3 | Xavier weights, never trained, built at startup | confirmed | `backend/app/transformer.py:105-114`, `:224-231`; `backend/app/main.py:38` |
| L3 | Dropout 0.1 stays on at inference | confirmed | `backend/app/config.py:10`; `backend/app/transformer.py:76-77`, `:91-94` |
| L3 | Noise std 0.1 vs PE ~1, so layer 0 mostly position | unverified (labelled as reasoning in the guide) | `backend/app/transformer.py:367`, `:201-203` |
| L3 | Read-order key lines | confirmed | `backend/app/transformer.py:37-94`, `:96-183`, `:185-283`, `:322-368`; `backend/app/main.py:64-139`; `backend/tests/test_transformer.py:21-36` |
| L3 | Shared vocab, 10 000 cap, START/END | confirmed | `backend/app/main.py:32`; `backend/app/transformer.py:325`, `:342-358` |
| L3 | Embeddings 1 × seq × 512; no mask passed | confirmed | `backend/app/main.py:76`, `:79` |
| L3 | 6 post-norm blocks, 8 heads, d_k 64, FFN 512→2048→512 no bias | confirmed | `backend/app/config.py:7-9`; `backend/app/transformer.py:134-183`, `:233-237`, `:263-283` |
| L3 | Response carries all layers' weights and full output | confirmed | `backend/app/main.py:83-94` |
| L3 | WebSocket fakes streaming with 0.1 s sleeps, `latency_ms: 0` | confirmed | `backend/app/main.py:125-138`; `README.md:32` |
| L3 | Performance charts are `Math.random()` under "Real-time monitoring" | confirmed | `frontend/src/components/PerformanceMetrics.js:23-38`, `:44` |
| L3 | "Gemini AI integration ready" but never called | confirmed | `README.md:42` |
| L3 | [bug] No train/eval switch for dropout | confirmed | `backend/app/transformer.py:76-77` |
| L3 | [bug] Sum-to-1 test fails with default dropout | confirmed (wording tightened) | `backend/tests/test_transformer.py:23`, `:36`; `backend/app/transformer.py:40` |
| L3 | [shallow] `max_seq_length` shown, never applied; PE table 5000 | confirmed | `backend/app/config.py:11`; `backend/app/transformer.py:188`, `:290`; `frontend/src/components/PerformanceMetrics.js:64-65` |
| L3 | [shallow] LayerNorm divides by std + eps | confirmed | `backend/app/transformer.py:247-251` |
| L3 | [shallow] CPU-bound `async def` forwards | confirmed | `backend/app/transformer.py:134`, `:263`, `:292` |
| L3 | [misleading] Hover labels reversed | corrected (convention-dependent, now [shallow]) | `frontend/src/components/AttentionHeatmap.js:15`, `:19-25` |
| L3 | Tests: shapes, divisibility, START/END | confirmed | `backend/tests/test_transformer.py:12-83` |
| L3 | Try this: rewrite `forward` with a training flag | confirmed (doable) | `backend/app/transformer.py:63-82` |
| L4 | Fixed `temperature=0.7` | confirmed | `backend/main.py:179` |
| L4 | SDK 0.8.3; key hard-coded; three models | confirmed | `backend/requirements.txt:3`; `backend/main.py:21`, `:24-55` |
| L4 | Four UI tabs | confirmed | `frontend/src/App.js:61-92` |
| L4 | Read-order key lines | confirmed | `backend/main.py:24-55`, `:112-157`, `:159-239`, `:241-301`; `test.sh:8-23` |
| L4 | Cost formula: cached share 0.5, ×30 and ×365 | confirmed | `backend/main.py:62`, `:126-148` |
| L4 | Perf loop: 5 iterations, 100 tokens, 0.7, `datetime.now()`, 0.5 s sleep | confirmed | `backend/main.py:67`, `:166-206` |
| L4 | Input-only `count_tokens` per iteration; words × 1.3 fallback | confirmed | `backend/main.py:198-204` |
| L4 | min/max/mean/median, p95 = `quantiles(n=20)[18]`, variance from spec | confirmed | `backend/main.py:211-225` |
| L4 | Context p50/p95/p99 by index; limit = p99; savings formula | confirmed | `backend/main.py:252-297` |
| L4 | README p50/p95/p99, but no p99 in perf endpoint | confirmed | `README.md:37`; `backend/main.py:211-217` |
| L4 | README "training data scale" absent | confirmed | `README.md:4` |
| L4 | Output tokens and tokens/s never measured | confirmed | `backend/main.py:199`, `:218-221` |
| L4 | [misleading] "7B"/"70B", latency, RPM, prices UNVERIFIED; "May 2025" | confirmed | `backend/main.py:23`, `:26`, `:36`, `:46`, `:88` |
| L4 | [misleading] Made-up scores | confirmed | `backend/main.py:100-109` |
| L4 | [misleading] Context "savings" fallacy (99.96 % example) | confirmed (arithmetic checked) | `backend/main.py:273`, `:295` |
| L4 | [shallow] 5-sample p95 can exceed the max | confirmed (stdlib "exclusive" method extrapolates) | `backend/main.py:216` |
| L4 | [bug] Sync `generate_content` inside `async def` | confirmed | `backend/main.py:160`, `:175` |
| L4 | [shallow] Dead code `cache_savings_factor`, `effective_input_tokens` | confirmed | `backend/main.py:122-123`, `:316` |
| L4 | [bug] `/compare` divides by `monthly_cost` | confirmed | `backend/main.py:325`, `:335` |
| L4 | [bug] `test.sh` always ends "All tests passed!" | confirmed | `test.sh:2`, `:8-23` |
| L4 | validate_dashboard "only checks costs > 0" | corrected (prices too; perf/context only warn) | `validate_dashboard.sh:12`, `:25`, `:38`, `:46-78` |
| L4 | Try this: "input dominates in RAG" | corrected (depends on price ratio) | `backend/main.py:126-133` |
| L5 | `asyncio.to_thread` call; SDK 0.3.2 | confirmed | `backend/app/services/model_client.py:30-37`; `backend/requirements.txt:4` |
| L5 | Models list; key from env | confirmed | `backend/app/main.py:57-89`, `:26` |
| L5 | UI: 3 fixed prompts × 3 reps | confirmed | `frontend/src/App.js:19-23`, `:54-62` |
| L5 | Read-order key lines | confirmed | `model_client.py:13-88`; `benchmark_service.py:12-86`; `analytics_engine.py:9-78`, `:80-164` |
| L5 | Sequential loop, 3 reps, temp 0.7, 0.5 s sleep | confirmed | `backend/app/services/benchmark_service.py:16-17`, `:23-56` |
| L5 | `max_output_tokens=1000`; per-1K price table | confirmed | `backend/app/services/model_client.py:18`, `:33-36`, `:99-110` |
| L5 | Words × 1.3 "even though the response carries real usage" | corrected (usage not read; SDK support UNVERIFIED) | `backend/app/services/model_client.py:47-48`; `backend/requirements.txt:4` |
| L5 | Any exception → random latency, fake text, success True | confirmed | `backend/app/services/model_client.py:59-88` |
| L5 | Aggregation drops `simulated`, `success_rate` 1.0, p95 from 3 | confirmed | `backend/app/services/benchmark_service.py:47-53`, `:66`, `:69` |
| L5 | `/api/compare` uses constants; Pareto check correct | confirmed | `backend/app/services/analytics_engine.py:13-29`, `:51-78` |
| L5 | Recommendations: constants, "high" confidence, "cascading" if ≥ 2 | confirmed | `backend/app/services/analytics_engine.py:89-153` |
| L5 | README "Real-time", "Ultra", Pareto on constants | confirmed | `README.md:24`, `:27`, `:29` |
| L5 | Generator has no fallback ("no match for simulated or random") | corrected (evidence replaced) | `../setup.sh:254-262`; comment at `../setup.sh:415` |
| L5 | [misleading] MMLU constants; `benchmark_data` unused | confirmed | `backend/app/services/analytics_engine.py:7`, `:25-27`, `:93-105` |
| L5 | [shallow] L4 vs L5 prices differ "for the same family" | corrected (only 2.0 Flash differs) | `model_client.py:100-102`; `lesson4 …/backend/main.py:28-29`, `:38-39`, `:48-49` |
| L5 | [shallow] p95 from 3 runs; fixed prompt order | confirmed | `backend/app/services/benchmark_service.py:29-33`, `:66` |
| L5 | `test.sh` prints passed after warnings | confirmed | `scripts/test.sh:44-61` |
| L5 | Try this: invalid key, list real vs fake numbers | confirmed (doable) | `model_client.py:59-88`; `benchmark_service.py:40-70` |
| L6 | SDK 0.4.0, structlog, `gemini-1.5-flash`, prices 0.075/0.300 | confirmed | `requirements.txt:7`, `:10`; `config/settings.py:6`, `:18-19` |
| L6 | `redis`, `prometheus-client` unused | confirmed | `requirements.txt:8-9`; only settings fields at `config/settings.py:22-24` |
| L6 | UI polls stats every 5 s, keeps last 10 calls | confirmed | `frontend/src/App.js:14-18`, `:44-51` |
| L6 | "Only `_generate_with_retry` touches the SDK" | corrected (also `__init__`) | `backend/gemini_client.py:21-23`, `:128-143` |
| L6 | Read-order key lines | confirmed | `rate_limiter.py:22-57`, `:59-88`; `circuit_breaker.py:33-78`; `gemini_client.py:43-160`; `cost_tracker.py:27-62`; `config/settings.py:5-19`; `tests/test_api_client.py:18-99` |
| L6 | Defaults temperature 0.7, max tokens 1000 | confirmed | `backend/main.py:32-33`, `:55-64` |
| L6 | Input estimate `len(prompt) // 4` | confirmed | `backend/gemini_client.py:60`, `:63` |
| L6 | Refill capacity/60 per s; throttle returns at once; HTTP 200 | confirmed | `backend/rate_limiter.py:43-88`; `backend/gemini_client.py:64-73`; `backend/main.py:55-65` |
| L6 | Mock sleeps 50-100 ms, invents tokens | confirmed | `backend/gemini_client.py:162-177` |
| L6 | Retry 3 tries, executor, 0.1 × 2^n + jitter, any exception | confirmed | `backend/gemini_client.py:128-160` |
| L6 | Breaker: 5 in a row, 60 s, 2 successes | confirmed | `config/settings.py:14-15`; `backend/circuit_breaker.py:36-44`, `:57-65` |
| L6 | Cost from real `usage_metadata` "when present" | corrected / unverified (SDK 0.4.0 support) | `backend/gemini_client.py:86-88`, `:141-142`; `requirements.txt:7` |
| L6 | JSON log lines with 8-char request id | confirmed | `backend/main.py:9-14`; `backend/gemini_client.py:56`, `:91-95`, `:117-120`, `:179-182` |
| L6 | README backoff/breaker only with mock off | confirmed | `README.md:33-34`; `config/settings.py:7`; `backend/gemini_client.py:76-83` |
| L6 | README "Comprehensive testing" = 6 tests | confirmed | `README.md:38`; `tests/test_api_client.py:18-99` |
| L6 | Dockerfile copies a `.env` that does not exist | confirmed | `Dockerfile:12`; folder listing; `README.md:64` |
| L6 | [shallow] No timeout on provider call | unverified (SDK default unknown); softened | `backend/gemini_client.py:134-137` |
| L6 | [shallow] Retry does not sort errors; tiny base; no Retry-After | confirmed | `backend/gemini_client.py:145-152` |
| L6 | [shallow] TPM counts estimated input only | confirmed | `backend/gemini_client.py:60`, `:63` |
| L6 | [shallow] Half-open lets all calls through; reset after one success | confirmed | `backend/circuit_breaker.py:35-47`, `:54-78` |
| L6 | [misleading] Throttle returns HTTP 200 | confirmed | `backend/main.py:55-65` |
| L6 | [shallow] In-memory state; `requests_per_hour` = total / uptime | confirmed | `backend/cost_tracker.py:60` |
| L6 | Tests: limiter, breaker, cost, mock-mode client | confirmed | `tests/test_api_client.py:9-10`, `:18-87` |
| L6 | Try this: rpm 30, tpm 6000, 5 × 1 500 tokens | confirmed (worked through: doable) | `backend/rate_limiter.py:22-88` |
| L7 | SDK `>=0.8.0` | confirmed | `backend/requirements.txt:5` |
| L7 | Model = first listed by `list_models()` (duplicated) | confirmed | `backend/main.py:144-181`, `:302-339` |
| L7 | App refuses to start without key | confirmed | `backend/main.py:15-20` |
| L7 | Metrics panel polled every 2 s | confirmed | `frontend/src/App.js:12` |
| L7 | Read-order key lines | confirmed | `backend/main.py:94-133`, `:183-290`, `:341-460`, `:462-480`; `tests/test_parsing.py:11-95` |
| L7 | Prompt shape: 5 rules, optional few-shot; schema of type strings | confirmed | `backend/main.py:96-120`, `:559-564` |
| L7 | temp 0.1, no max tokens, 429 handling, 3 tries, 404 rediscovery | confirmed | `backend/main.py:52`, `:354-422` |
| L7 | Step 1 direct `json.loads` | confirmed | `backend/main.py:211-229` |
| L7 | Four regexes; "top-level arrays never matched" | corrected (array passes step 1, then `ParseResult` rejects it) | `backend/main.py:56`, `:214-221`, `:233-238` |
| L7 | Repair prompt has no schema; reply parsed by `json.loads` only | confirmed | `backend/main.py:123-133`, `:200-206`, `:272-273` |
| L7 | Validation errors do not change `success` | confirmed | `backend/main.py:433-444`, `:529` |
| L7 | Only `/generate` updates metrics | confirmed | `backend/main.py:527-536` vs `:555-584` |
| L7 | README "Pydantic" models unused | confirmed | `README.md:10`, `:66`; `backend/main.py:71-88` (no other use) |
| L7 | README test button; button skips metrics | confirmed | `README.md:50-52`; `frontend/src/components/PromptTester.js:48` |
| L7 | README targets unmeasured; report 0 % yet "correct"; validator PASSED | confirmed | `README.md:78-79`; `VALIDATION_REPORT.md:60-68`; `validate_dashboard.py:62` |
| L7 | [bug] Repair crash loses raw output | confirmed ("often fenced" softened) | `backend/main.py:54-60`, `:283-290`, `:446-460` |
| L7 | [bug] Type check: `List[str]` and float vs int | corrected ("always" → on every successful parse) | `backend/main.py:434-435`, `:473-478`, `:563` |
| L7 | [bug] Non-greedy regexes cut deep nesting outside fences | confirmed (3 levels fail; fenced and 2 levels work) | `backend/main.py:236-237` |
| L7 | [misleading] Any "invalid" message → API key error | confirmed | `backend/main.py:397-402` |
| L7 | [misleading] Hard-coded "5 requests per minute" | confirmed | `backend/main.py:391` |
| L7 | [shallow] Model by list order; two `list_models` calls at import | confirmed | `backend/main.py:142`, `:159-163`, `:299-300`, `:487` |
| L7 | [shallow] Success rate is parse rate only | confirmed | `backend/main.py:529-532` |
| L7 | Test list | corrected (adds `parse_with_fallback` test) | `tests/test_parsing.py:86-95` |
| L7 | "Importing main needs a real key and network" | corrected (any key value; offline UNVERIFIED) | `backend/main.py:18-20`, `:169-176`, `:487` |
| L7 | No test for repair, nesting, arrays, `_validate_schema` | confirmed | `tests/test_parsing.py:1-98` |
| L7 | Try this: 6 strings through `JSONParser` | confirmed (doable; hint added) | `backend/main.py:183-261`, `:56` |
| L8 | `gemini-1.5-flash`, no generation config; key from env | confirmed | `backend/main.py:244`, `:251`, `:22-23` |
| L8 | Trace viewer shows hard-coded traces | confirmed | `frontend/src/components/DecisionTraceViewer.js:7-25` |
| L8 | Swap: "one function" | corrected (plus setup at `:23`, `:244`) | `backend/main.py:23`, `:244`, `:247-282` |
| L8 | Read-order key lines | confirmed | `backend/main.py:98-232`, `:247-282`, `:284-434`, `:541-643`; `tests/test_decision_maker.py:14-50` |
| L8 | Planner prompt lists names and descriptions, not parameters | confirmed | `backend/main.py:385-412` |
| L8 | `wait_for` 5 s around `to_thread`; fence strip; parse | confirmed | `backend/main.py:245`, `:250-264`, `:414` |
| L8 | Keyword fallback; default "add [1, 2]", confidence 0.7 | confirmed | `backend/main.py:284-379`, `:416-422` |
| L8 | max_steps 10, timeout 30; deliberation defaults to execute | confirmed | `backend/main.py:82-83`, `:436-470`, `:581-598` |
| L8 | Tool timeout 10 s, 3 tries, 1 s then 2 s; only timeouts retried | confirmed | `backend/main.py:496-539`, `:135-136` |
| L8 | `last_result` stored, plan params unchanged; success True | confirmed | `backend/main.py:601-619` |
| L8 | README "95 %+", "< 500 ms" unmeasured | confirmed | `README.md:79-80` |
| L8 | README "reuses L7's `gemini_json_call()`" | confirmed (0 hits in L7 `.py` files) | `README.md:35` |
| L8 | README "L9 adds Redis + PostgreSQL" | confirmed (L9 uses dict + JSON files) | `README.md:87-91`; `lesson9 …/backend/memory_manager.py:15`, `:60` |
| L8 | [bug] `success` True when all steps fail | confirmed | `backend/main.py:612-619`, `:743-744` |
| L8 | [misleading] Unrecognised goal returns 3 | corrected (only when the LLM plan fails) | `backend/main.py:366-372`, `:416-422` |
| L8 | [misleading] `modified_parameters` ignored; Python repr and `//` in prompt | confirmed | `backend/main.py:449-454`, `:587-601` |
| L8 | [shallow] No parameter schemas; wrong name → "unknown", sunny 72 | confirmed | `backend/main.py:141-151`, `:385-388` |
| L8 | [ok-for-demo] Factorial unbounded | confirmed | `backend/main.py:121-125` |
| L8 | Tests pass with no LLM via regex fallback | confirmed | `tests/test_decision_maker.py:22-42`; `backend/main.py:290-301` |
| L8 | Try this: weather goal without a key | confirmed (doable) | `backend/main.py:303-315` |
| L9 | Two tiers: 20-message list; per-user JSON file | confirmed | `backend/memory_manager.py:27-55`, `:57-82` |
| L9 | Substring search over JSON text, keys included | confirmed | `backend/memory_manager.py:104-107` |
| L9 | No provider; UI polls metrics every 3 s | confirmed | `backend/requirements.txt:1-4`; `frontend/src/App.js:19` |
| L9 | Read-order key lines | confirmed | `backend/memory_manager.py:27-55`, `:57-115`; `backend/api.py:44-91` |
| L9 | Steps 1-3 (limits 20, 10, 5; newest-first) | confirmed | `backend/memory_manager.py:42-43`, `:48-55`, `:84-111` |
| L9 | README "< 10 ms", "Keyword search" | confirmed | `README.md:32`, `:37` |
| L9 | [bug, D4] `user_id` path traversal | confirmed | `backend/memory_manager.py:60`, `:90` |
| L9 | [bug] No lock, two writes can lose one | corrected (cannot interleave in one process; now [shallow]) | `backend/memory_manager.py:62-77`; `backend/api.py:61-64`, `:99` |
| L9 | [misleading] "hits" count calls | confirmed | `backend/memory_manager.py:50`, `:86` |
| L9 | [shallow] Keys searched; 11 entries, mostly 3 facts repeated | confirmed | `backend/data/users/demo_user.json`; `demo.sh:22-30` |
| L9 | [shallow] 20-message window by count | confirmed | `backend/memory_manager.py:42-43` |
| L9 | [bug] Docker writes to `/app/data/users` | corrected (separate stores; now [shallow]) | `Dockerfile:3`, `:13`, `:17`; `docker-compose.yml:9`; `start.sh:5-7` |
| L9 | `test.sh` greps for words | confirmed | `test.sh:14-58` |
| L9 | Try this: predict searches for "python", "level", "a" | confirmed (doable) | `backend/memory_manager.py:84-111`; `backend/data/users/demo_user.json` |
| All | One key hard-coded in the listed files and in L1–L5, L8 `setup.sh` | confirmed (13 copies, identical by hash) | `lesson1/…/.env.example:2`; `lesson2/…/backend/app/main.py:144`; `lesson3/…/backend/app/config.py:4`; `lesson3/…/docker-compose.yml:11`; `lesson4/…/backend/main.py:21`; `lesson1/setup.sh:180`; `lesson2/setup.sh:170`; `lesson3/setup.sh:49`, `:1712`; `lesson4/setup.sh:9`, `:39`; `lesson5/setup.sh:9`; `lesson8/setup.sh:46` |
| All | L7 "reported as leaked" means the hard-coded lessons cannot run | corrected / unverified (L7 key comes from a missing `.env`) | `lesson7/…/STATUS.md:21-23`; `lesson7/…/API_KEY_SETUP.md:4`; `lesson7/…/backend/main.py:18` |
| All | Fallbacks that hide failure (L2, L5, L6, L8, plus L3 and L8 UI) | confirmed | lines as cited in the bullet |
| All | Four token counters | confirmed (L6 SDK support UNVERIFIED) | L4 `main.py:199`, `:203`, `:253`; L5 `model_client.py:47-48`; L6 `gemini_client.py:60`, `:141-142` |
| All | Retry three ways, none complete | confirmed ("default mode" added for L2) | L2 `main.py:184-189`; L6 `gemini_client.py:128-160`; L7 `main.py:377-381` |
| All | p95 from 3-5 samples | confirmed | L4 `main.py:216`; L5 `benchmark_service.py:66` |
| All | Sync SDK calls in `async def`; L5-L8 use threads | confirmed | L4 `main.py:175`; L5 `model_client.py:30`; L6 `gemini_client.py:134`; L7 `main.py:359`; L8 `main.py:251` |
| All | Price and spec tables disagree | corrected (only 2.0 Flash prices and "7B" vs "Unknown" differ) | L4 `main.py:24-55`; L5 `main.py:57-89`, `model_client.py:98-103` |
| All | Old model ids "may no longer be served" | unverified | runtime-dependent |
| All | Smoke scripts "always pass" | corrected (L5 stops on a dead backend) | L4 `test.sh:8-23`; L5 `scripts/test.sh:29-61`; L7 `validate_dashboard.py:62` |
| All | Global metric dicts | confirmed | L1 `app.py:17`; L2 `main.py:65`; L7 `main.py:490`; L8 `main.py:677` |
| Summary | L1 cell: key in `.env.example:2`; silent pip installs | confirmed | `.env.example:2`; `../setup.sh:169-173` |
| Summary | L2 cell: "Retry never fires" | corrected ("in default mode") | `backend/app/main.py:147`, `:169-189` |
| Summary | L3 cell: random inputs, dropout, failing test | confirmed | `backend/app/transformer.py:365-368`, `:76-77`; `backend/tests/test_transformer.py:36` |
| Summary | L4 cell: "Invented 7B/70B" | corrected ("Unsourced, UNVERIFIED") | `backend/main.py:26-46`, `:273` |
| Summary | L5 cell: random latencies with success True; constants | confirmed | `backend/app/services/model_client.py:59-88` |
| Summary | L6 cell: mock default bypasses breaker and retry | confirmed | `config/settings.py:7`; `backend/gemini_client.py:76-83` |
| Summary | L7 cell: repair crash, type check, Pydantic unused | confirmed | `backend/main.py:283-290`, `:446-460`, `:473-478` |
| Summary | L8 cell: success True; regex fallback in tests | confirmed | `backend/main.py:612-619` |
| Summary | L9 cell: path traversal; substring + recency | confirmed | `backend/memory_manager.py:60`, `:104-110` |

## Verification log (pass B)
Lens: completeness and teaching accuracy. Method: every backend `.py` file of each lesson was re-read in full (plus `setup.sh` sections, tests, test scripts and data files where cited) and compared with "How it works" and the settings. Nothing was run. Paths are relative to each lesson's project folder.

| Lesson | Item | Change | Evidence file:line |
|---|---|---|---|
| L1 | Step-by-step (venv, hidden pip output, `.env` copy, demo endpoint, polling) | confirmed | `../setup.sh:12`, `:164-173`, `:178-193`; `src/app.py:40`, `:154`, `:170-191` |
| L1 | "Avg Response Time" is a fixed sleep; "Successful Operations" always equals demo count | added [misleading] | `src/app.py:176`, `:179-184` |
| L1 | Concept mapping `none`, relevance None | confirmed | no LLM call in `src/` |
| L1 | Take-away and interview answer | confirmed | `.env.example:2`; `requirements.txt:2-10` |
| L2 | Step-by-step (cache outer, tracking inner, gather, 30 s timeout, retry 1 s then 2 s) | confirmed | `backend/app/main.py:77-93`, `:95-117`, `:149-211` |
| L2 | Fallback-off bullet: error is an internal `HTTPException(500)`, not a 500 to the client | corrected | `backend/app/main.py:174`, `:184-189` |
| L2 | Errors end as `"Error: ..."` strings in an HTTP 200 reply | added [misleading] | `backend/app/main.py:200`, `:205-207`, `:235-241` |
| L2 | Cache never evicts | added [shallow] | `backend/app/main.py:104-114` |
| L2 | P1 mapping marked minor (fields only passed through) | corrected | `backend/app/main.py:153-158` |
| L2 | Swap: `reasoning_effort="low"` and enough `max_tokens` for gpt-oss-20b | added (stack fit) | `backend/app/main.py:149-177` |
| L2 | Take-away: test that a forced error is not cached | added | `backend/app/main.py:113-115` |
| L2 | Interview answer (retry inside, cache outside, separate outcomes) | confirmed | n/a (design) |
| L3 | Step-by-step (shared vocab, random embeddings, 6 post-norm blocks, no mask) | confirmed | `backend/app/transformer.py:263-319`, `:342-358`; `backend/app/main.py:72-79` |
| L3 | Concept mapping: P4 added as counter-example | corrected | `backend/app/transformer.py:365-368` |
| L3 | No input-length check; PE table overflow gives HTTP 500; payload grows with seq² | added [shallow] | `backend/app/transformer.py:188`, `:218`; `backend/app/main.py:85` |
| L3 | `create_embeddings` is not a retrieval embedding (per-token, untrained) | added [misleading] | `backend/app/transformer.py:365-368`; `backend/app/main.py:86` |
| L3 | Take-away: token vectors vs Cohere/MiniLM chunk embeddings | added (P4) | as above |
| L3 | Interview: variance statement made precise (unit-variance parts give variance d_k) | corrected | `backend/app/transformer.py:63-66` |
| L4 | Step-by-step (cost split, timing loop, input-only `count_tokens`, context percentiles) | confirmed | `backend/main.py:126-148`, `:166-217`, `:252-297` |
| L4 | `/compare` "recommendation" is the cheapest model; price tie keeps table order | added [misleading] | `backend/main.py:28-30`, `:48-50`, `:335`, `:340`, `:350` |
| L4 | `cache_hit_rate` unbounded; above 1 gives a negative cost | added [shallow] | `backend/main.py:62`, `:128-129` |
| L4 | Empty `sample_texts`: 400 swallowed and returned as 500 | added [bug] | `backend/main.py:256-257`, `:300-301` |
| L4 | Wall-clock timing; cold first call kept | added [shallow] | `backend/main.py:172`, `:192-193` |
| L4 | Take-away: reasoning tokens in `completion_tokens` (UNVERIFIED); store `usage` with the replay cache | added (stack fit) | n/a (Groq behaviour not in repo) |
| L4 | Concept mapping and interview answer | confirmed | `backend/main.py:268-297` |
| L5 | Step-by-step (sequential loop, simulated fallback, flag dropped, constants, Pareto) | confirmed | `backend/app/services/benchmark_service.py:23-70`; `model_client.py:27-88`; `analytics_engine.py:51-153` |
| L5 | M4 and A1 mapped as counter-examples | corrected | `benchmark_service.py:47-53`, `:66`; `analytics_engine.py:144-164` |
| L5 | Simulated output tokens (prompt words × 2.5) priced as real | added [misleading] | `model_client.py:76-77`; `benchmark_service.py:40-45` |
| L5 | Summary `total_requests` counts prompts, not calls | added [misleading] | `benchmark_service.py:99-107` |
| L5 | Truthiness constraints ignore 0; "cascading" is only a label | added [shallow] | `analytics_engine.py:115-121`, `:147-153` |
| L5 | `scripts/test.sh` never calls `/api/benchmark` | added (tests) | `scripts/test.sh:34-58` |
| L5 | Take-away: vary the retrieval set-up, not the fixed Groq model | added (stack fit) | n/a |
| L5 | Interview answer | confirmed | n/a (design) |
| L6 | Steps 1–8 (estimate, limiter, mock/real, retry delays, breaker, usage, logs) | confirmed | `backend/gemini_client.py:43-160`; `backend/rate_limiter.py:22-88`; `backend/circuit_breaker.py:33-78` |
| L6 | Breaker wraps retry: one breaker failure = 3 SDK attempts, 15 to open | added (step 6) | `backend/gemini_client.py:79-83`, `:128-147`; `config/settings.py:14` |
| L6 | Dockerfile: build fails as shipped (no `.env`) | corrected | `Dockerfile:12`; folder listing |
| L6 | Mock calls booked as real cost; no mock field in the reply | added [misleading] | `backend/gemini_client.py:76-77`, `:86-105`, `:167`; `backend/main.py:35-45` |
| L6 | `failure_threshold` name hides the 15-call reality | added [shallow] | as step 6 |
| L6 | Take-away: `mode` field; chunk ids, not chunk text, in traces (no book text to tracing services) | added (stack fit) | n/a (learner rules) |
| L6 | Interview answer | confirmed | n/a (design) |
| L7 | Steps 1–7 (prompt rules, 429/404 handling, cascade, validation, metrics) | confirmed | `backend/main.py:96-120`, `:183-290`, `:341-460`, `:527-536` |
| L7 | Step 5: repair call has no generation config (default temperature) | added | `backend/main.py:267-270` |
| L7 | Step 6: validation runs only on a non-empty dict | corrected | `backend/main.py:434` |
| L7 | `{}` counts as success with no validation errors | added [bug] | `backend/main.py:434`, `:529-530` |
| L7 | 404 rediscovery most likely rebuilds the same model | added [shallow] | `backend/main.py:302-326`, `:408` |
| L7 | `avg_parse_time_ms` mixes local parses and LLM repairs; list grows forever | added [misleading] | `backend/main.py:183-209`, `:535-536` |
| L7 | Take-away: cited-id check (towards V1); expected outcomes for edge-case tests | added | n/a (design) |
| L7 | Concept mapping P7, C5, M3 and interview answer | confirmed | `backend/main.py:94-133`, `:462-480` |
| L8 | Steps; added planning cap `timeout_seconds / 3` and the `Step(**step)` failure path | added | `backend/main.py:424`, `:557-560`, `:627-631` |
| L8 | Factorial: [ok-for-demo] raised to [bug, D4]; CPU loop blocks the server, timeout cannot fire | corrected | `backend/main.py:121-125`, `:500-503` |
| L8 | Plan trace does not record LLM vs regex planner | added [misleading] | `backend/main.py:418`, `:562-570`, `:85-92` |
| L8 | Deliberation traced only on skip | added [shallow] | `backend/main.py:460-466`, `:589-598` |
| L8 | Take-away: `path` field; per-phase records; chunk ids, scores, source page | added (C6) | `backend/main.py:70-77` |
| L8 | Concept mapping and interview answer | confirmed | `backend/main.py:381-434`, `:541-643` |
| L9 | Steps 1–3 (20-message window, JSON file append, substring search, recency sort) | confirmed | `backend/memory_manager.py:27-111` |
| L9 | Concept mapping: P3 added; P2 and X3 marked counter-examples | corrected | `backend/memory_manager.py:42-43`, `:102-110` |
| L9 | `limit=0` returns the whole window; negative limits accepted | added [bug] | `backend/memory_manager.py:54`; `backend/api.py:55-56` |
| L9 | Corrupt file: error swallowed, API says `success: True` | added [misleading] | `backend/memory_manager.py:113-115`; `backend/api.py:69-77` |
| L9 | Interview answer | confirmed | n/a (design) |
| Summary | L2, L3, L5, L6, L7, L8, L9 cells aligned with the lesson sections | corrected | as cited in each row above |
| Cross | "No retrieval anywhere in this block" (search of all L1–L9 backend `.py`) | added | `lesson3/…/backend/app/transformer.py:365-368`; `lesson9/…/backend/memory_manager.py:24` |
| Cross | "Traces and replies that hide which path ran" | added | L2 `main.py:205-207`; L5 `benchmark_service.py:47-53`; L6 `main.py:35-45`; L8 `main.py:562-570` |
| All | No API key value in this guide | confirmed | text search of this file for the Google key prefix: 0 hits |
