# Verification log: VAI lessons 49, 54, 59, 64, 69: multi-agent systems and operations

[← Lesson guide](../L49-L69_multi_agent_and_ops.md) · [← Guide index](../README.md)

Pass A re-opened every cited claim at its source line and tried to refute it. Pass B re-read every backend file with a different lens: control flow, missed issues, concept mapping and fit to your stack. Verdicts: confirmed / corrected / removed / unverified.
## Verification log (pass A)
Method: I opened and read every cited line. Nothing in the source repo was run or installed. The L54 numbers (cosines, noise) come from my own scratch NumPy script, which uses constants copied from the code. The L54 `setup.sh` comparison comes from a scratch script that pulls each heredoc out of `setup.sh` and diffs it against the generated file. No API key value appears in this block; the two `.env.example` files hold only placeholders.

| Lesson | Claim (short) | Verdict | Evidence file:line |
|---|---|---|---|
| all | Only lesson54 has a `setup.sh` | confirmed | folder listings of lesson49/54/59/64/69 |
| L54 | Generated files equal `setup.sh` except `chat.py` adds `import json` | confirmed | heredoc diff; `backend/routers/chat.py:3, 97-98` |
| all | None of the five does retrieval | confirmed | L64 `src/core/agent.py:26-46` (Chroma heartbeat only) |
| L49 | LLM `gemini/gemini-2.0-flash` via CrewAI `LLM` | confirmed | `backend/crew.py:9-13` |
| L49 | `crewai==0.80.0` | confirmed | `backend/requirements.txt:3` |
| L49 | UI streams agent cards over SSE, shows "Technical Briefing" | confirmed | `frontend/src/App.js:108-126, 262` |
| L49 | Swap: "CrewAI routes through LiteLLM" | unverified (reworded) | `backend/crew.py:10` (id format only) |
| L49 | No delegation, sequential process | confirmed | `backend/crew.py:30, 44, 58, 109` |
| L49 | Key lines crew 19-59 / 62-104 / 113-166; main 66-75 / 78-111; test 15-23 | confirmed | same lines |
| L49 | Step 1: `run_crew` in a thread | confirmed | `backend/main.py:72` |
| L49 | Step 2: max_iter 3, temps 0.3 / 0.5 | corrected (citations) | `backend/crew.py:8, 16, 29, 43, 55, 57` |
| L49 | Step 3: "each task description has the topic" | corrected (analysis task has none) | `backend/crew.py:35, 64, 76-81, 94, 117` |
| L49 | Step 4: context chaining | confirmed | `backend/crew.py:88, 103` |
| L49 | Step 5: outputs paired by index | confirmed | `backend/crew.py:120-125` |
| L49 | README points at missing `../setup.sh` | confirmed | `README.md:16`; lesson49 holds only the project folder |
| L49 | README makes no quality claims | confirmed | `README.md:1-44` |
| L49 | Any exception returns "[DEMO MODE]"; HTTP 500 path never fires for LLM errors | confirmed | `backend/crew.py:134-166`; `backend/main.py:74-75` |
| L49 | Compose sets an empty key | corrected (line 10 to 9) | `docker-compose.yml:9`; `backend/main.py:17` |
| L49 | SSE fixed sleeps, at least 42 s | confirmed | `backend/main.py:87, 97-100` |
| L49 | Backstories invent credentials | confirmed | `backend/crew.py:36-39` |
| L49 | `cleanup.sh` stops all containers and prunes | corrected (volume scope depends on Docker version) | `cleanup.sh:15, 27-30` |
| L49 | `test.sh` passes in demo mode | confirmed | `test.sh:19-21`; `backend/crew.py:153-166` |
| L49 | Try this points at real lines and is doable | confirmed | `backend/crew.py:134-166`; `test.sh:19-21` |
| L54 | Stack: FastAPI, aiosqlite, numpy, google-generativeai | confirmed | `backend/requirements.txt:1-6` |
| L54 | Model `gemini-2.0-flash` at two call sites | confirmed | `backend/routers/chat.py:23, 69`; `backend/services/inference.py:56, 81` |
| L54 | UI: profiles, radar, chat, compare, analytics | confirmed | `frontend/src/App.jsx:3, 38, 83` |
| L54 | No ChromaDB or Redis despite the docstring | confirmed | `backend/db/store.py:2`; `backend/requirements.txt` |
| L54 | Key lines router 12-17, 47-59; chat 94-151; inference 58-161; compressor 42-61 | confirmed | same lines |
| L54 | Step 1: `X-User-Id`, no auth, auto-create | confirmed | `backend/routers/chat.py:95-106` |
| L54 | Step 2: budget out of 8000; min of three fractions | confirmed | `backend/routers/chat.py:109-112`; `backend/models/budget.py:14-18` |
| L54 | Step 3: persona = best cosine to stored vector | corrected (DEFAULT when no vector) | `backend/routers/chat.py:115-121`; `backend/main.py:70-78` |
| L54 | Step 4: RICH above 0.6, STANDARD above 0.3, else MINIMAL | confirmed | `backend/services/compressor.py:47-61` |
| L54 | Step 5: prompt is prefix + message; token count is a word count | confirmed | `backend/routers/chat.py:129, 131` |
| L54 | Step 6: 20 interactions, 300 chars, JSON, threshold 0.3 | confirmed (consent gate added) | `backend/services/inference.py:46, 64-88`; `backend/routers/profiles.py:80-84` |
| L54 | README covers start, stop and cleanup only | confirmed | `README.md:1-29` |
| L54 | `DB_PATH`, `REDIS_URL`, `PRIVACY_MODE` never read | confirmed | `backend/config.py:3-5`; `backend/db/store.py:16`; `backend/routers/profiles.py:18-19` |
| L54 | Cosines "all between 0.8 and 0.98"; default user maps to ANALYST, confidence 0.975 | corrected (0.79-0.98 for the seed vectors; 0.9755; a new user gets DEFAULT) | `backend/services/router.py:13-16, 51-59`; `backend/main.py:49-50, 84`; `backend/routers/profiles.py:94-105` |
| L54 | VP Eng seed: ANALYST 0.934 vs EXECUTIVE 0.910 | confirmed | scratch computation from `router.py:13-16`, `main.py:49-50` |
| L54 | Noise alone exceeds 0.3 "about 98%, mean 0.65" | corrected (97-98%, mean 0.63-0.65) | scratch simulation of `backend/models/profile.py:64-70`; `inference.py:115-123, 144-146` |
| L54 | Effective epsilon about 5 | corrected (per dimension, assuming sensitivity 1) | `backend/models/profile.py:67` |
| L54 | Personalisation token costs 85 / 32 / 8 are hard-coded | confirmed | `backend/services/compressor.py:50, 55, 60` |
| L54 | Offline demo replies; inference fallback | confirmed | `backend/routers/chat.py:26-75`; `backend/services/inference.py:91-112` |
| L54 | `feedback_score` stored but never read; ADK export is base64 JSON | confirmed | `backend/db/store.py:218-224` (only writer, by search); `backend/models/profile.py:75-82` |
| L54 | `test.sh`: 11 checks, one real-logic check, never exits non-zero | confirmed | `scripts/test.sh:20-57` |
| L54 | Try this is doable | corrected (zero-vector note) | `backend/services/router.py:51-52` |
| L59 | Model `gemini-2.0-flash-exp`; effect if retired | confirmed (retirement stays UNVERIFIED) | `backend/services/mas_runner.py:51` |
| L59 | Stack: aiosqlite WAL, loguru, networkx | confirmed | `backend/requirements.txt:5-8`; `backend/core/logger.py:99` |
| L59 | UI: WebSocket table, hotspots, eval report | confirmed | `frontend/src/App.js:122-125, 181-184` |
| L59 | All LLM calls go through `_gemini_call` | confirmed | `backend/services/mas_runner.py:36-81, 104-130` |
| L59 | Key lines in trace / runner / logger / harness / graph / tests | confirmed | same lines |
| L59 | Step 1: one TestCase per regex, default ".+" | confirmed | `backend/api/main.py:82-85` |
| L59 | Step 2: 4 calls with SEND records between | confirmed | `backend/services/mas_runner.py:101-130` |
| L59 | Step 3: parent = previous record, so a chain | confirmed (SESSION_START note added) | `backend/services/mas_runner.py:39, 86`; `backend/core/session.py:46-52` |
| L59 | Step 4: usage metadata, else chars / 4 | confirmed | `backend/services/mas_runner.py:24-28, 54-60` |
| L59 | Step 5: queue of 10,000, drop when full, batches of 50, WebSocket push | confirmed | `backend/core/logger.py:56-58, 85-95, 103-146` |
| L59 | Step 6: regex IGNORECASE + DOTALL; 50,000 tokens / 30,000 ms; both must hold | confirmed | `backend/core/harness.py:37, 47-65`; `backend/models/trace.py:56-57` |
| L59 | Step 7: critical-path weights, hotspots | confirmed | `backend/core/graph.py:39-60` |
| L59 | README: deterministic fallback with no key | confirmed | `README.md:35`; `backend/services/mas_runner.py:31-33` |
| L59 | Topology and replay promised; `topology_ok` never set; replay engine unused | confirmed | `backend/core/harness.py:2`; `backend/api/main.py:3, 19`; `backend/models/trace.py:65` |
| L59 | `replay()` only deep-copies | confirmed | `backend/core/replay.py:2, 41-50` |
| L59 | Failed runs grade as PASS | confirmed | `backend/services/mas_runner.py:31-33, 69-81`; `backend/api/main.py:84-85` |
| L59 | Fallback tokens count toward the budget | confirmed | `backend/services/mas_runner.py:74-77`; `backend/core/graph.py:74-78` |
| L59 | JSONL sink never gets normal traces | confirmed | `backend/core/logger.py:21-29, 85-95`; `backend/core/replay.py:31-35` |
| L59 | Critical-path test "cannot fail" | corrected (softened) | `backend/tests/test_evaluation.py:41-47` |
| L59 | `profile_async` never applied; `"profiler": {}` | confirmed | `backend/services/mas_runner.py:17` (no other use, by search); `backend/api/main.py:96` |
| L59 | Wall time leaves out the final call | confirmed (`close()` adds no record) | `backend/core/harness.py:58-64`; `backend/services/mas_runner.py:42`; `backend/core/session.py:63-67` |
| L59 | Monotonic timestamps "not comparable across restarts" | corrected (part UNVERIFIED) | `backend/models/trace.py:35`; `backend/core/logger.py:162-165` |
| L59 | Docker passes no key | confirmed | `docker-compose.yml:15-16` |
| L59 | Test coverage list; docstring names replay; no fallback test | confirmed | `backend/tests/test_evaluation.py:2, 32-150` |
| L59 | Fixture keys "match neither model nor DB" | corrected (`compl_tok` matches the DB column) | `backend/fixtures/sample_trace.jsonl`; `backend/models/trace.py:38`; `backend/core/logger.py:42-43` |
| L59 | Try this is doable | corrected (wording) | `backend/services/mas_runner.py:70, 79`; `backend/core/harness.py:20-65` |
| L64 | Model `models/gemini-2.0-flash-lite` | confirmed | `src/core/config.py:9`; `k8s/configmap.yaml:12` |
| L64 | Chroma heartbeat only; Redis unused | confirmed | `requirements.txt:6-7`; `src/core/agent.py:26-46` (no Redis use, by search) |
| L64 | UI polls every 5 s | confirmed | `frontend/src/App.jsx:80-132` |
| L64 | One `generate_content` call | confirmed | `src/core/agent.py:57-60` |
| L64 | Key lines for main / infer / agent / Dockerfile / k8s / cd / prometheus | confirmed | same lines |
| L64 | Step 1: ready even if Chroma fails | confirmed | `src/core/agent.py:26-37` |
| L64 | Step 2: middleware metrics, buckets 5 ms to 5 s | confirmed | `src/main.py:24-28, 72-87` |
| L64 | Step 3: live always 200; ready needs a heartbeat within 2 s | confirmed | `src/main.py:92-114` |
| L64 | Step 4: context prepended; auth gives 503; quota gives 200 | confirmed | `src/core/agent.py:54`; `src/routers/infer.py:55-70` |
| L64 | Step 5: 2 replicas, maxUnavailable 0, 250m/256Mi, 500m/512Mi, HPA 2-10 at 60% | confirmed | `k8s/deployment.yaml:11, 18-19, 44-50`; `k8s/hpa.yaml:12-20` |
| L64 | "Cite sources" with no retrieval | confirmed | `src/core/agent.py:50-54` |
| L64 | `COPY tests/` vs `.dockerignore` | confirmed (build failure expected, not run) | `Dockerfile:36`; `.dockerignore:18` |
| L64 | No curl in the runtime image, yet healthchecks and smoke test use it | confirmed (pod `kubectl exec` added) | `Dockerfile:45-65`; `docker-compose.yml:30`; `.github/workflows/cd.yml:145-146`; `tests/test_dockerfile.py:38-42` |
| L64 | "L49 installs curl for exactly this reason" | corrected (motive removed) | L49 `docker/Dockerfile.backend:3` |
| L64 | Two workers split the Prometheus counters | confirmed (library behaviour, not run) | `Dockerfile:71-73`; `src/main.py:24-28` |
| L64 | Short-SHA tag vs full `github.sha` | confirmed (documented default, not run) | `.github/workflows/cd.yml:67-68, 87, 132` |
| L64 | Workflow is not at the repo root, so it never runs | confirmed | no `.github` folder at the repo root |
| L64 | No Chroma manifest; secret placeholder is not base64 | confirmed | `k8s/configmap.yaml:7`; `k8s/` listing; `k8s/secret.yaml:9` |
| L64 | "A quota failure counts as 200" | corrected (quota only; auth is 503) | `src/routers/infer.py:55-70` |
| L64 | UI polling inflates the counter; raw-path label | confirmed | `frontend/src/App.jsx:132`; `src/main.py:74` |
| L64 | `yaml` import not declared | corrected (likely installed through another package; UNVERIFIED) | `tests/test_k8s_manifests.py:6`; `requirements.txt`; `requirements-dev.txt` |
| L64 | `test_health` "with agent=None" | corrected (two tests set it) | `tests/test_health.py:26, 49` |
| L64 | No test runs inference or checks a metric value | confirmed | `tests/test_*.py` |
| L64 | CI has a coverage gate and no eval step | confirmed | `.github/workflows/cd.yml:31-37` |
| L64 | Try this is doable | confirmed | `src/main.py:72-87` |
| L69 | OTel SDK 1.25.0; model `gemini-2.0-flash` | confirmed | `requirements.txt:6`; `backend/agent.py:36` |
| L69 | No OTLP or collector; FastAPI instrumentation unused | confirmed | `backend/tracer.py:170-188`; `requirements.txt:7` (no import, by search) |
| L69 | One LLM call; two price constants | confirmed | `backend/agent.py:21-22, 95` |
| L69 | Key lines agent / tracer / main / db / tests | confirmed | same lines |
| L69 | Step 1: thread pool | confirmed | `backend/main.py:72-75` |
| L69 | Step 2: root span attributes | confirmed | `backend/agent.py:46-52` |
| L69 | Step 3: child span attributes and events | confirmed | `backend/agent.py:70-139` |
| L69 | Step 4: cost formula | confirmed | `backend/agent.py:117-118` |
| L69 | Step 4: prices are Flash-Lite class | unverified (code comment says 2.0 Flash) | `backend/agent.py:20-22` |
| L69 | Step 5: batches of 32 every 500 ms; trace upsert | confirmed | `backend/tracer.py:111-164, 180-185` |
| L69 | Step 6: 0.65 s sleep, newest trace, breach at 5000 ms / $0.01 | confirmed | `backend/main.py:77-94` |
| L69 | Step 7: percentiles "by nearest rank" | corrected (simple index pick; cost-trend window added) | `backend/db.py:53-94` |
| L69 | `.env` ignored; dotenv installed but unused | confirmed | `README.md:30`; `requirements.txt:10`; `start.sh:1-26` |
| L69 | README points at missing `../setup.sh` | confirmed | `README.md:4`; lesson69 holds only the project folder |
| L69 | Fallback looks healthy; `error_rate_pct` stays 0 | confirmed | `backend/agent.py:62, 102-118`; `backend/db.py:60, 101` |
| L69 | Trace-id race; 1-second `created_at` | confirmed | `backend/main.py:78-80`; `backend/db.py:22`; `backend/tracer.py:39` |
| L69 | Roll-up keeps the first span's start, status and root name | confirmed | `backend/tracer.py:146-163` |
| L69 | WebSocket hard-codes OK; mixed latency quantities | confirmed | `backend/main.py:110`; `backend/db.py:56, 65-70` |
| L69 | Raw input in a span attribute | confirmed | `backend/agent.py:51` |
| L69 | Compose curl healthcheck, gcc-only image, no key | confirmed | `docker-compose.yml:9-13`; `Dockerfile:4` |
| L69 | Tests: tautology, no span test, real DB | confirmed | `tests/test_l69.py:2, 19, 57`; `backend/tracer.py:18` |
| L69 | Try this is doable | confirmed (`tracer.py:158` note added) | `backend/agent.py:83-132`; `backend/db.py:96-110` |
| summary | L49 "Biggest problem" cell | confirmed | `backend/crew.py:134-166`; `test.sh:21` |
| summary | L54 cell ("default user" maps to ANALYST) | corrected | `backend/routers/chat.py:119-121`; `backend/main.py:49-50` |
| summary | L59 cell | confirmed | `backend/api/main.py:84-85`; `backend/services/mas_runner.py:69-81` |
| summary | L64 cell | confirmed | `.dockerignore:18`; `.github/workflows/cd.yml:67-68, 87` |
| summary | L69 cell | confirmed | `backend/agent.py:62, 102-110`; `backend/main.py:78-80` |
| cross | Fallbacks hide failures in every lesson | corrected (L64 quota only; L59 records ERROR) | L64 `src/routers/infer.py:55-70`; L59 `mas_runner.py:70` |
| cross | Estimated tokens shown as real | confirmed | L54 `chat.py:131`; L69 `agent.py:115-116`; L59 `mas_runner.py:24-28`; L54 `compressor.py:50-60` |
| cross | Tests check shape, not behaviour | confirmed | L69 `tests/test_l69.py:57`; L59 `tests/test_evaluation.py:41-47` |
| cross | "No API key passed" for L49 | corrected (L49 passes an empty one) | L49 `docker-compose.yml:9` |
| cross | Unused components | corrected (L64 Redis wholly unused) | L64 `src/core/config.py:12` (no other use) |
| cross | `cleanup.sh` scope per lesson | corrected | L49 `cleanup.sh:15, 27-30`; L54 `cleanup.sh:22, 25`; L59 `cleanup.sh:22, 25`; L64 `cleanup.sh:7-17, 20-23`; L69 `cleanup.sh:31-35` |
| cross | Gemini everywhere, 1-2 call sites per lesson | confirmed | per-lesson model lines above |

---

## Verification log (pass B)
Lens: completeness and teaching accuracy. Method: I read every backend `.py` file of each lesson in full, plus the tests, Compose files, Dockerfiles, CD workflow, k8s manifests and READMEs. Nothing in the source repo was run, installed or changed. One new number comes from my own scratch NumPy script (`vai_review/passb_scratch/l54_flip.py`, beside the `verified/` folder that holds this file), which uses constants re-typed from `router.py:13-16`, `main.py:48-57` and `profile.py:64-70`. A search for key patterns (Google-style key prefixes, `sk-` keys, literal `api_key=` strings) over all five lessons and over this guide found no secret, so nothing had to be removed. Pass A's cosine and drift numbers were kept as they were; I did not re-run them.

| Lesson | Item | Change | Evidence file:line |
|---|---|---|---|
| L49 | Step 1: which endpoint the UI really calls | added (`/stream-crew`, not `/run-crew`) | `frontend/src/App.js:108-109`; `backend/main.py:91-111` |
| L49 | Step 2: `max_iter`, temperatures 0.3 / 0.5 | confirmed | `backend/crew.py:8, 16, 29, 43, 55, 57` |
| L49 | Step 3: topic only in two descriptions and the goals | confirmed | `backend/crew.py:35, 64, 76-81, 94, 117` |
| L49 | Steps 4-5: context chaining, index pairing | confirmed | `backend/crew.py:88, 103, 120-125` |
| L49 | Step 6: canned fallback in the control flow | added | `backend/crew.py:134-166` |
| L49 | UI run time includes the fixed 42 s of sleeps | added [misleading] | `frontend/src/App.js:106, 134`; `backend/main.py:87, 97-100` |
| L49 | Raw exception text shown in `final_output` | added [ok-for-demo] | `backend/crew.py:154` |
| L49 | `sse-starlette` and the `build_crew` import unused | added [shallow] | `backend/requirements.txt:6`; `backend/main.py:14, 19, 118-121` |
| L49 | Concepts A5 / P7 | corrected (both are counter-examples: no tools, no grounding context) | `backend/crew.py:19-59` (no `tools=`) |
| L49 | What to take: A5 retrieval-tool check; fallback must fail the gate | added | `test.sh:19-21`; `backend/crew.py:134-166` |
| L49 | Interview answer | confirmed | `backend/crew.py:19-59` |
| L49 | No hard-coded key | confirmed | `docker-compose.yml:9` (empty value only) |
| L54 | Steps 1, 2, 4 | confirmed | `backend/routers/chat.py:95-112`; `backend/models/budget.py:14-18`; `backend/services/compressor.py:47-61` |
| L54 | Step 3: chat recomputes the persona and ignores the stored column | corrected (added) | `backend/routers/chat.py:115-118` |
| L54 | Step 5: prompt has no chat history | confirmed (wording sharpened) | `backend/routers/chat.py:129` |
| L54 | Step 6: every chat stored, no consent check | added | `backend/routers/chat.py:134-142` |
| L54 | Step 8: persona from the clean vector; noisy copy stored; clean copy returned | added | `backend/services/inference.py:115, 141-152` |
| L54 | "Privacy" noise protects nothing (clean vector in the API response) | added [misleading] | `backend/services/inference.py:107, 152` |
| L54 | Reported persona differs from the chat persona (about 15% to 50% in simulation) | added [bug] | `backend/services/inference.py:141-146`; `backend/routers/chat.py:115-118`; scratch `l54_flip.py` |
| L54 | `INSERT OR REPLACE` wipes vector, persona, consent and count | added [bug] | `backend/db/store.py:97-101` |
| L54 | Consent gates inference only; `consent_embedding` never read | added [misleading] | `backend/routers/chat.py:103-106, 134-142`; `backend/db/store.py:24` (no other reader, by search) |
| L54 | Corpus includes agent replies; LLM JSON not range-checked; missing keys default to 0.5 | added [shallow] | `backend/services/inference.py:72-76`; `backend/models/profile.py:84-87` |
| L54 | Compare tab uses the default vector for every user | added [misleading] | `backend/routers/chat.py:177`; `backend/services/compressor.py:63-66` |
| L54 | Seeded analytics with a fixed `token_cost` of 140; `budget_usage_log` never written | added [misleading] | `backend/main.py:83-91`; `backend/db/store.py:61-71, 177` (its only other use is a delete) |
| L54 | Delete test cannot fail | added | `backend/db/store.py:172-181`; `scripts/test.sh:53` |
| L54 | Concepts: P4 cautionary, X3 and A4 counter-examples, D4 partial | corrected | `backend/services/compressor.py:50, 55, 60`; `backend/db/store.py:218-224`; `backend/services/inference.py:64-65` |
| L54 | What to take: P4 baseline-cosine notebook on project chunks (cached, not book text); D4 delete path | added | `backend/services/router.py:13-16, 47-59` |
| L54 | Interview answer | confirmed | `backend/services/inference.py:115-123` |
| L59 | Steps 1-5 and 7 | confirmed | `backend/api/main.py:82-85`; `backend/services/mas_runner.py:24-28, 36-130`; `backend/core/session.py:46-55`; `backend/core/logger.py:85-146`; `backend/core/graph.py:39-60` |
| L59 | Step 6: only `final_output` is graded | added | `backend/core/harness.py:25` |
| L59 | Replay cannot parse the one JSONL line; `response` vs `response_preview` key mismatch | added [bug] | `backend/core/logger.py:91-95`; `backend/core/replay.py:32-39, 55`; `backend/services/mas_runner.py:66` |
| L59 | Client regex unguarded: an invalid pattern gives 500 after 4 LLM calls; backtracking risk | added [bug] | `backend/api/main.py:82-88`; `backend/core/harness.py:50` |
| L59 | Concepts: D2 replay counter-example, D3 shape only | corrected | `backend/core/replay.py:41-50`; `backend/api/main.py:78-97` |
| L59 | What to take: a real record/replay cache keyed by a request hash | added | `backend/core/replay.py:41-50` |
| L59 | Interview answer | confirmed | `backend/core/harness.py:20-65` |
| L64 | Steps 1-3 and 5 | confirmed | `src/core/agent.py:26-37`; `src/main.py:24-28, 72-114`; `k8s/deployment.yaml:11-19, 44-50`; `k8s/hpa.yaml:12-20` |
| L64 | Step 4: system prompt sent as a content part; limits in characters; other errors give 500 | corrected (added; library reading, not run) | `src/core/agent.py:57-60`; `src/routers/infer.py:23-24, 71`; L69 `backend/agent.py:39-42` |
| L64 | Readiness never recovers after a failed warm-up | added [bug] | `src/core/agent.py:28-41`; `docker-compose.yml:24-26` |
| L64 | CPU-based HPA is a weak signal for an I/O-bound LLM proxy | added [shallow] (not measured) | `k8s/hpa.yaml:20`; `src/core/agent.py:57-60` |
| L64 | Metrics test passes on any `# HELP` output | added [shallow] | `tests/test_health.py:41` |
| L64 | Concept C5 counter-example ("cite sources" with no sources) | added | `src/core/agent.py:50-54` |
| L64 | What to take: local `uv run` gate (local git only, so no Actions); chunk ids and pages for C5 | added | `.github/workflows/cd.yml:20-37` |
| L64 | Interview: startup probe and recoverable readiness | corrected (extended) | `k8s/deployment.yaml:67-72`; `src/core/agent.py:36-41` |
| L69 | Steps 1-5 and 7 | confirmed | `backend/main.py:72-75`; `backend/agent.py:44-139`; `backend/tracer.py:111-164, 180-185`; `backend/db.py:53-94` |
| L69 | Step 6: breach latency is the LLM call's latency only | added | `backend/agent.py:112, 131`; `backend/main.py:84` |
| L69 | $0.01 cost breach needs about 33,000 output or 133,000 input tokens | added [misleading] (arithmetic from code constants) | `backend/agent.py:21-22`; `backend/main.py:85` |
| L69 | `agent.total_latency_ms` holds LLM latency only | added [misleading] | `backend/agent.py:61, 112, 131` |
| L69 | What to take: cost from Groq `usage`, cost 0 on a cache hit, fallback as ERROR; book-text redaction before LangSmith | added | `backend/agent.py:51, 115-118` |
| L69 | Concepts D1, D2 | confirmed | `backend/agent.py:44-139`; `backend/db.py:51-111` |
| L69 | Interview answer | confirmed | `backend/agent.py:83-132` |
| summary | Concept cells for L49, L54, L59, L64 | corrected (now match the lesson headers) | lesson headers above |
| summary | "Biggest problem" cells for all five | corrected (extended with pass-B findings) | L49 `backend/main.py:97-100`; L54 `backend/services/inference.py:152`; L59 `backend/core/replay.py:32-39`; L64 `src/core/agent.py:36-41`; L69 `backend/main.py:85` |
| cross | Gates and alarms that cannot trip | added | L59 `backend/api/main.py:85`; L64 `tests/test_health.py:41`; L54 `backend/db/store.py:181`; L69 `backend/main.py:85`; L49 `test.sh:21` |
| cross | No caching anywhere | added | search for "cache" in all five backends: only a docstring (L54 `backend/db/store.py:2`) and a test name (L64 `tests/test_dockerfile.py:38`) |
| cross | Units hidden in names | added | L64 `src/routers/infer.py:23-24`; L69 `backend/agent.py:61` |
| all | No API key or secret in the source or the guide | confirmed | key-pattern search over lesson49/54/59/64/69 (no hits) |
