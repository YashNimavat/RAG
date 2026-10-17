# Verification log: VAI lessons 39–44: compliance, fallback, synthesizer, traceability, agentic RAG end to end, RAG eval

[← Lesson guide](../L39-L44_agentic_rag_pipeline_and_eval.md) · [← Guide index](../README.md)

Pass A re-opened every cited claim at its source line and tried to refute it. Pass B re-read every backend file with a different lens: control flow, missed issues, concept mapping and fit to your stack. Verdicts: confirmed / corrected / removed / unverified.
## Verification log (pass A)
| Lesson | Claim (short) | Verdict | Evidence file:line |
|---|---|---|---|
| L39 | 9 rules in YAML; PII regex :7, personal-data regex :75 | confirmed | `rules/compliance_rules.yaml:3-121`, `:7`, `:75` |
| L39 | Default model gemini-2.5-flash in both classes | confirmed | `backend/compliance_engine.py:48`, `backend/validator_agent.py:33` |
| L39 | google-generativeai 0.8.3 | confirmed | `backend/requirements.txt:5` |
| L39 | "Redis optional, code skips it when absent" | corrected (client is still created; each Redis error is caught) | `compliance_engine.py:56-60`, `:197-198`, `:212-213`, `:243-244`, `:260-261` |
| L39 | `domain` field ignored; built for healthcare at startup | confirmed | `backend/main.py:28`, `:42` |
| L39 | Factual check: ≥2 docs, temp 0.1, JSON, 500 chars, fails open | confirmed | `validator_agent.py:82-125` |
| L39 | 7 rules loaded (healthcare + all) | confirmed | `compliance_engine.py:73-75`; YAML domains |
| L39 | Cache key domain+rule+hash; case-insensitive regex | confirmed | `compliance_engine.py:111-127`, `:182-185` |
| L39 | LLM tier temp 0.1, max_output_tokens 100, "YES" in first 10 chars | confirmed | `compliance_engine.py:145-155` |
| L39 | Risk = sum of severities, reject if >70; 95 rejects, 60 approves | confirmed | `compliance_engine.py:88-96`; YAML :6, :16 |
| L39 | Audit list `audit:healthcare`, trimmed to 1000, fields | confirmed | `compliance_engine.py:215-246` |
| L39 | README PostgreSQL/immutable; psycopg2, SQLAlchemy, asyncpg unused | confirmed | `README.md:10`; `requirements.txt:7-8,14`; grep found no imports |
| L39 | README circuit breaker and ComplianceViolationEvent absent | confirmed | `README.md:99`, `:104`; grep found nothing |
| L39 | `action` field loaded, never read | confirmed | `compliance_engine.py:26`; grep |
| L39 | [bug] LLM rules never see the content | confirmed | `compliance_engine.py:132-143`; every LLM rule has a prompt (YAML :19, :33, :48, :62, :87, :102, :115) |
| L39 | [bug] fail-open pass cached 1 h | confirmed | `compliance_engine.py:166-179`, `:207-210` |
| L39 | max_output_tokens=100 on thinking model leaves no text | unverified (runtime; retagged [bug] from [misleading]) | `compliance_engine.py:149`, `:153` |
| L39 | PERSONAL_DATA regex false positives ("address 0x10") | confirmed | `rules/compliance_rules.yaml:75`, `:74` |
| L39 | /stats total_violations counts rejections | confirmed | `compliance_engine.py:277` |
| L39 | test.sh: no assertions; SSN sample rejected | confirmed | `test.sh:11-37`; YAML :7 severity 95 |
| L39 | Frontend: JSON form, WebSocket stats, audit list | confirmed | `frontend/src/App.js:21-58`; `components/ValidationForm.js:12-35` |
| L39 | Try this: "8 sentences" (only 6 listed); YAML escaping | corrected | `rules/compliance_rules.yaml:7`, `:75` |
| L40 | gemini-2.0-flash-exp hard-coded in 3 agents | confirmed | `planner_agent.py:8`, `retriever_agent.py:8`, `validator_agent.py:8` |
| L40 | Redis container, psycopg2, prometheus unused | confirmed (redis lib added) | `docker-compose.yml:15-20`; `requirements.txt:4-9`; grep found no imports |
| L40 | Breaker-open early return | confirmed | `fallback_orchestrator.py:31-37` |
| L40 | 3 attempts, base delay 1.0 s, breaker 5/30 s | confirmed | `fallback_orchestrator.py:13-14` |
| L40 | plan() returns query unchanged | confirmed | `planner_agent.py:10-16` |
| L40 | Retriever: 200 chars into 2 identical docs, 0.85; fallback 0.5 | confirmed | `retriever_agent.py:15-38` |
| L40 | Validator random <0.3, random type, ignores docs | confirmed | `validator_agent.py:15-37` |
| L40 | Rewrites start from the original query; 3 strategies | confirmed | `fallback_orchestrator.py:82`; `planner_agent.py:23-46` |
| L40 | Delays 0.1 / 2^n ±30% / ×1.5; no sleep after last attempt | confirmed | `retry_policy.py:12-37`; `fallback_orchestrator.py:81` |
| L40 | Success returns context, no answer; graceful degradation | confirmed | `fallback_orchestrator.py:59-77`, `:100-115` |
| L40 | Exception = breaker failure per attempt, no backoff/rewrite | confirmed | `fallback_orchestrator.py:89-98` |
| L40 | Half-open after 30 s; 2 successes close | confirmed | `circuit_breaker.py:22-53` |
| L40 | README reformulation; sub-queries dropped | confirmed | `README.md:46`; `planner_agent.py:39-44`; `fallback_orchestrator.py:83`; `retriever_agent.py:12` |
| L40 | README "structured validation" vs random | confirmed | `README.md:40`; `validator_agent.py:19` |
| L40 | "(success)" buttons "still fail 30% of the time" | corrected (30% per attempt; ~2.7% of requests end in max retries) | `frontend/src/App.js:63-68`; `validator_agent.py:19`; `fallback_orchestrator.py:42` |
| L40 | delay_seconds is a fresh draw, not the slept delay | confirmed | `fallback_orchestrator.py:52` vs `:86` |
| L40 | Leaky breaker counter; half_open_max_calls unused | confirmed | `circuit_breaker.py:14`, `:43`; `fallback_orchestrator.py:90`, `:101` |
| L40 | get_state() mutates via is_open() | confirmed | `circuit_breaker.py:24-28`, `:62` |
| L40 | test.sh "only prints results" | corrected (also waits for /health and exits 1 on timeout) | `scripts/test.sh:10-40` |
| L40 | Try this line refs | confirmed | `retry_policy.py:14-15` |
| L41 | google-generativeai 0.8.0; default gemini-2.0-flash-exp | confirmed | `requirements.txt:2`; `backend/main.py:84`; `.env.example:5` |
| L41 | Canned mock answer without key | confirmed | `main.py:91-122`, `:141-142`, `:190-197` |
| L41 | Frontend "query box with fixed chunks" | corrected (one placeholder chunk) | `frontend/src/App.js:16-18`, `:63-69` |
| L41 | 3 call sites; 3–7 calls per request | confirmed | `cot_engine.py:151`; `citation_mapper.py:38`; `coherence_validator.py:39`; plans :30-47 |
| L41 | Demo: 3 chunks, 10-word query → MODERATE | confirmed (word count checked) | `main.py:166-200`; `cot_engine.py:19-24` |
| L41 | No temperature; chained inputs per step | confirmed | `cot_engine.py:71-100`, `:151` |
| L41 | Answer = last step; COMPLEX final step has no chunks | confirmed | `synthesizer_agent.py:60`; `cot_engine.py:138-148` |
| L41 | Citation format, regex, ID filter, claim dropped, excerpt unchecked | confirmed | `citation_mapper.py:15-54` |
| L41 | Citation confidence = quality_score | corrected (0.8 when quality_score is 0) | `citation_mapper.py:55` |
| L41 | inject_citations: unused map, Sources list only | confirmed | `citation_mapper.py:63-74` |
| L41 | Judge: 200-char heads, pass defaults, SCORE 75, circular accuracy | confirmed | `coherence_validator.py:15-56` |
| L41 | REGENERATE_REQUIRED, no retry | confirmed | `synthesizer_agent.py:77-80` |
| L41 | Confidence = min(0.95, 0.6+words/500), mean | confirmed | `cot_engine.py:155`; `synthesizer_agent.py:85-86` |
| L41 | README 3–7 steps vs 1/3/5 | confirmed | `README.md:41-42`; `cot_engine.py:30-47` |
| L41 | XAIFormatter never called; requires_full_xai unused | confirmed | `synthesizer_agent.py:20`; `frontend/src/App.js:68`; grep |
| L41 | README "Automatic citation mapping" | confirmed (line added) | `README.md:32`; `citation_mapper.py:69-74` |
| L41 | .env vars never read | confirmed | `.env.example:11-17`; grep shows only 3 getenv calls |
| L41 | [bug] bracketed IDs dropped by regex | confirmed (own made-up string) | `citation_mapper.py:33-49` |
| L41 | [ok-for-demo] mock "invented sources" | corrected (hard-coded list = demo sources, ignores request chunks) | `main.py:95-121` |
| L41 | test.sh always "All tests passed" | confirmed | `test.sh:36-47` |
| L41 | Try this line refs | confirmed | `main.py:166-188` |
| L42 | gemini-1.5-flash hard-coded; SDK 0.7.2 | confirmed | `planner.py:11`; `retriever.py:10`; `validator.py:10`; `synthesizer.py:10`; `requirements.txt:3` |
| L42 | Keyword-overlap retriever reports model id | confirmed | `retriever.py:13-20`, `:43` |
| L42 | No README | confirmed | folder listing |
| L42 | Demo only in generated pipeline; empty key → demo by default | confirmed (start.sh evidence added) | `setup.sh:10`, `:57-64`, `:889-956`; `scripts/start.sh:5`; `pipeline.py:16-21` |
| L42 | Demo spans: fixed values and sleeps | confirmed | `pipeline.py:32-90` |
| L42 | mint + ContextVar | confirmed | `context.py:126-138` |
| L42 | Decorator: 512 chars per input, to_trace_dict, error status | confirmed | `decorator.py:24-68` |
| L42 | Planner JSON fields | confirmed | `planner.py:42-67` |
| L42 | Retriever scoring, STRICT ×1.3, top 3; sub-queries unused | confirmed | `retriever.py:54-69`; `pipeline.py:107-109` |
| L42 | Validator 800 chars; synthesizer JSON | confirmed | `validator.py:50-80`; `synthesizer.py:45-79` |
| L42 | FAIL verdict does not stop synthesis | confirmed | `synthesizer.py:48-50`; `pipeline.py:117-119` |
| L42 | finalize and confidence_delta | confirmed | `context.py:150-170` |
| L42 | Queue 2000, drop when full, INSERT OR REPLACE, JSONL append | confirmed | `sink.py:26`, `:91-140` |
| L42 | Waterfall order, latency stats, live tail 0.3 s | confirmed | `query.py:22-88`; `app.py:83-96` |
| L42 | input_summary is "a string of the args, ≤512" | corrected (dict of str() per arg, each ≤512) | `decorator.py:33-40`; `sink.py:130` |
| L42 | Retrieved chunk text not stored | corrected (validator span holds str(docs)[:512]) | `validator.py:46`; `decorator.py:33-40` |
| L42 | Answer text and citations not stored | confirmed | `synthesizer.py:22-34` |
| L42 | Banner "4-agent traced pipeline" | confirmed | `setup.sh:1933` |
| L42 | JSONL "immutable"; INSERT OR REPLACE | confirmed | `sink.py:2`, `:108`, `:119` |
| L42 | [bug] tie sort raises TypeError | confirmed (own snippet) | `retriever.py:67` |
| L42 | [bug] monotonic = "seconds since boot", "no real dates" | corrected (arbitrary start point; trace_id encodes wall time) | `context.py:14`, `:66`, `:130`, `:145`, `:157` |
| L42 | Retriever tokens are word counts | confirmed | `retriever.py:76-77` |
| L42 | Self-reported confidence; delta | confirmed | `context.py:161-169` |
| L42 | /trace/{id} never 404 | confirmed | `query.py:28-38`; `app.py:58-59` |
| L42 | Synth prompt numbers docs, asks for doc_id | confirmed | `synthesizer.py:45-47`, `:63` |
| L42 | _uuid7 sorts only to ~64 ms | confirmed (bit arithmetic: version digit replaces ms bits 2–5) | `context.py:12-18` |
| L42 | uuid6 installed, unused | confirmed | `requirements.txt:14`; grep |
| L42 | 8 tests, none call an agent | confirmed | `tests/test_traceability.py:12-134` |
| L42 | Try this line refs | confirmed | `sink.py:105-140` |
| L43 | chromadb 0.5.23, PersistentClient, DefaultEmbeddingFunction | confirmed | `requirements.txt:7`; `retriever.py:15-22` |
| L43 | Default EF is MiniLM via ONNX | unverified (library behaviour) | `retriever.py:17` |
| L43 | Default model gemini-2.0-flash-lite | confirmed | `planner.py:18`; `validator.py:19`; `synthesizer.py:20` |
| L43 | sentence-transformers, tenacity, aiofiles unused | confirmed | `requirements.txt:8`, `:11`, `:12`; grep |
| L43 | setup.sh runs all 4 agents; 6000 chars, 1024 tokens | confirmed (exact lines added) | `setup.sh:728-807`, `:621`, `:661` |
| L43 | Generated adds FAST_MODE, 429 helper, canned answers, cooldown; nothing turns FAST_MODE off | confirmed | `orchestrator.py:21-22`; grep of setup.sh, scripts, compose |
| L43 | prior_work copy byte-identical backend | confirmed | `diff -rq` (only .env.example, Dockerfiles, App.jsx differ) |
| L43 | Seed: 15 docs, uuid4, skip if ≥15 | confirmed | `scripts/start.sh:21-22`; `seed_knowledge_base.py:10-54`; `retriever.py:92-100` |
| L43 | 4 s cooldown returns made-up result | confirmed (refined: measured from end of last query) | `app.py:32`, `:51-65`, `:68` |
| L43 | top_k = min(max_results, 5); collection ignored | confirmed | `orchestrator.py:36`; `app.py:38` |
| L43 | FAST path: quality = score, risk 0.2 | confirmed | `orchestrator.py:39-55` |
| L43 | Planner temp 0.1, 512 tokens, fallback; strategy unused | confirmed | `planner.py:20-80`; `retriever.py:52-57` |
| L43 | Retrieval k growth, cap 20, 1 − distance, errors swallowed | confirmed | `retriever.py:50-71` |
| L43 | "keeps top_k·2 = 6 chunks" | corrected (at most 6; attempt 1 with one sub-query gives 3) | `retriever.py:50`, `:79` |
| L43 | Score = 2·cos − 1 | unverified (Chroma default distance) | `retriever.py:62` |
| L43 | Validator: 8 chunks, 300 chars, temp 0, 0.55/0.8, average rule, fallback, top-3 | confirmed | `validator.py:21-109` |
| L43 | Up to 3 attempts, then synthesize anyway | confirmed | `orchestrator.py:64-77` |
| L43 | 500-char snippets, 4000-char budget | confirmed (refined: budget never bites at top_k 3) | `synthesizer.py:22`, `:120-131` |
| L43 | Prompt rules; temp 0.2; 512 tokens | confirmed | `synthesizer.py:33-44`, `:71-74` |
| L43 | 429: one wait of 15–70 s; canned answers | confirmed | `genai_retry.py:10-30`; `synthesizer.py:25-31`, `:79-89` |
| L43 | Citation regex, dedupe, 100-char snippet | confirmed | `synthesizer.py:133-147` |
| L43 | quality_score = mean chunk quality or 0.5 | confirmed | `synthesizer.py:97-99` |
| L43 | Tracer JSON with events + result; write error swallowed | confirmed | `tracer.py:15`, `:33-52` |
| L43 | GPU fact; demo query line | confirmed | `seed_knowledge_base.py:19`; `frontend/src/App.jsx:20` |
| L43 | Audit: retriever/validator events lack IDs; TraceEvent.error never set | confirmed | `retriever.py:86-87`; `validator.py:116-118`; grep for `error=` |
| L43 | API/UI say 4 stages; stage bar all green at done | confirmed | `app.py:21`; `App.jsx:24-43`, `:209`, `:377` |
| L43 | /history "consumed by L44" is false | confirmed | `app.py:82`; no `/history` or 8043 in L44 backend; `lesson44/.../models.py:46` |
| L43 | [misleading] FAST_MODE default | confirmed | `orchestrator.py:22` |
| L43 | [bug] retry widens k, attempt 3 = attempt 2 | confirmed (worked out from code) | `retriever.py:50`, `:79`; `validator.py:74-80` |
| L43 | [shallow] average rule; fallback scores "2·cos−1" mixed in | corrected (stated as 1 − distance) | `validator.py:64`, `:74` |
| L43 | [shallow] no abstention in code | confirmed | `validator.py:77` |
| L43 | [misleading] canned 429 answers cite [1], state DONE | confirmed | `synthesizer.py:25-31`, `:94`, `:109` |
| L43 | [bug] cooldown trace_id never written → 404 | confirmed | `app.py:53-65`; `tracer.py:33-52` |
| L43 | [bug] hard-coded /home/systemdr5 paths | confirmed | `scripts/start.sh:9`; `scripts/test.sh:3-5` |
| L43 | [ok-for-demo] uuid4 ids per seeding | confirmed | `retriever.py:94` |
| L43 | test.sh checks | corrected (audit/history failures do not fail the script) | `scripts/test.sh:10-29` |
| L43 | Try this: chunk counts per attempt | corrected (assume one sub-query) | `retriever.py:50`, `:79`; `validator.py:74` |
| L44 | 10 hand-written records | confirmed | `evaluator.py:59-150` |
| L44 | Judge gemini-1.5-flash, temp 0, JSON MIME | confirmed | `metrics.py:122-130` |
| L44 | Ragas path models; packages commented out | confirmed | `metrics.py:247-256`; `requirements.txt:11-16` |
| L44 | google-generativeai >=0.7,<0.8 | confirmed | `backend/requirements.txt:9` |
| L44 | prior_work copies: backend identical | confirmed | `diff -rq` (App.jsx, components, data/, .gitignore missing) |
| L44 | Faithfulness: 4000 chars, uses judge's float | confirmed | `metrics.py:146-157` |
| L44 | Relevancy: question + answer only; not Ragas's method | confirmed for code; Ragas side unverified | `metrics.py:159-167`; `evaluator.py:109` |
| L44 | Recall needs GT, 4000 chars | confirmed | `metrics.py:169-184` |
| L44 | Precision: 500 per chunk, unranked; Ragas is rank-weighted | confirmed for code; Ragas side unverified | `metrics.py:186-197` |
| L44 | 4 calls in parallel; errors → 0.0 | confirmed | `metrics.py:199-227` |
| L44 | Per-run mean, None skipped | confirmed | `evaluator.py:267-281` |
| L44 | Thresholds; None metric passes the gate | confirmed | `models.py:32-39`, `:91-96` |
| L44 | Gold answers all agree with contexts | corrected (a few small extra details; no deliberate bad cases) | `evaluator.py:93`, `:120` |
| L44 | num_test_questions up to 50 | confirmed | `models.py:84` |
| L44 | Background task; RAG_EXECUTING is a log line | confirmed | `main.py:62-89`; `evaluator.py:177-181` |
| L44 | ImportError → custom judge; 5 at a time, 0.3 s | confirmed | `metrics.py:288-290`; `evaluator.py:242-263` |
| L44 | Demo scores "above every threshold" | corrected (item faithfulness 0.84 every 4th item; means pass for n ≥ 2, n = 1 BLOCKED) | `evaluator.py:32-42` |
| L44 | Swap logged only; report has no flag | confirmed | `evaluator.py:190-196`; `models.py:61-73` |
| L44 | Report saved twice; shows twice in history | confirmed (completed runs) | `evaluator.py:214`, `:283-289`; `main.py:70-75`, `:119-151` |
| L44 | README/docstring Ragas primary, CHROMA_HOST | confirmed | `metrics.py:5`; `README.md:50-51`; grep found no CHROMA_HOST |
| L44 | "with retry logic"; tenacity unused | confirmed | `metrics.py:133-134` |
| L44 | Request fields unused | confirmed | `models.py:85-88`; `evaluator.py:163`; `main.py:68` |
| L44 | [bug] fake pass when evaluation fails | confirmed (n ≥ 2 qualifier added) | `evaluator.py:190-210` |
| L44 | [misleading] errors scored 0.0 | confirmed | `metrics.py:155-157`, `:219-220` |
| L44 | [bug] asyncio.coroutine removed in 3.11; Dockerfile 3.11 | confirmed (Python 3.11 change; not run) | `metrics.py:214`; `backend/Dockerfile:1` |
| L44 | [shallow] judge reasoning discarded | confirmed | `metrics.py:154`, `:164`; `models.py:58` |
| L44 | [shallow] truncation 4000/500 | confirmed | `metrics.py:151`, `:178`, `:188` |
| L44 | [bug] API key hard-coded (value not copied) | confirmed (also in both prior_work copies) | `docker-compose.yml:8` |
| L44 | gemini-1.5-flash no longer served | unverified (runtime) | `metrics.py:122` |
| L44 | test.sh: no score checks, never exits non-zero | confirmed | `test.sh:16-44` |
| L44 | Try this line refs | confirmed | `evaluator.py:60-86`; `metrics.py:34-37` |
| Summary | L42 cell "lacks answer, prompts and context" | corrected ("full context") | `validator.py:46`; `decorator.py:33-40` |
| Summary | L43 cell "lowers its own average" | corrected ("tends to lower") | `retriever.py:50`; `validator.py:74-80` |
| Summary | L44 cell "fake above-threshold scores" | corrected ("fake passing scores") | `evaluator.py:32-42` |
| Cross | L42 "tokens are word counts" | corrected (retriever only) | L42 `retriever.py:76-77` |
| Cross | L43 quality_score "of 2·cos−1" | corrected (1 − distance, fast mode) | L43 `synthesizer.py:97-99`; `retriever.py:62` |
| Cross | L43 audit "no context IDs" | corrected (cited IDs present; uncited missing) | L43 `tracer.py:44-45`; `synthesizer.py:141-146` |
| Cross | Redis "listed but unused" in L39 | corrected (Redis is used in L39) | L39 `compliance_engine.py:56-60`, `:237-242` |
| Cross | google-generativeai is deprecated | unverified (external fact) | requirements files of L39–L44 |
| Cross | Model ids per lesson | confirmed | see each lesson's Stack line |

## Verification log (pass B)
Lens: completeness and teaching accuracy. Every backend `.py` file of L39–L44 was re-read in full (nothing run). Change column: confirmed = text already right; corrected = text changed; added = new finding or advice.

| Lesson | Item | Change | Evidence file:line |
|---|---|---|---|
| L39 | Step-by-step control flow (validate, factual check, compliance, audit) | confirmed | `backend/main.py:46-70`; `backend/validator_agent.py:41-125`; `backend/compliance_engine.py:82-246` |
| L39 | HARMFUL_CONTENT has regex + LLM; regex hit returns first | added (step 4) | `rules/compliance_rules.yaml:100-102`; `compliance_engine.py:117-127` |
| L39 | One decision for the whole joined document set | added (step 5) | `validator_agent.py:55-58`, `:66` |
| L39 | [shallow] all-or-nothing; "filter" action never implemented | added | `validator_agent.py:55`; `compliance_engine.py:26`, `:96` |
| L39 | [shallow] cache key lacks rule version/prompt; 1 h stale verdicts | added | `compliance_engine.py:27`, `:182-185`, `:209` |
| L39 | [shallow] risk_score is an unbounded sum | added | `compliance_engine.py:93`; YAML `:6`, `:74` |
| L39 | /stats reads only the last 500 entries | added | `compliance_engine.py:265` |
| L39 | Concept V2 changed to "adjacent only" (a contradiction check is not relevance grading or groundedness) | corrected | `validator_agent.py:78-125` |
| L39 | What to take: per-chunk decision, Groq settings, versioned cache key, no book text | corrected | `compliance_engine.py:149`, `:182-185` |
| L39 | Interview answer | confirmed | — |
| L40 | Step-by-step control flow and settings | confirmed | `backend/fallback_orchestrator.py:13-115`; `backend/retry_policy.py:12-37`; `backend/circuit_breaker.py:11-63` |
| L40 | Bare `except` in retriever and sub-query call hides Gemini errors | added (step 2) | `backend/retriever_agent.py:30`; `backend/planner_agent.py:45-46` |
| L40 | simulate_failure makes every attempt fail | added (step 3) | `backend/validator_agent.py:19` |
| L40 | Exception branch rarely reached; breaker mostly counts max-retry exits | added (step 6) | `fallback_orchestrator.py:89-101` |
| L40 | [bug] outage still reports success via fallback stub + random pass | added | `retriever_agent.py:30-38`; `validator_agent.py:19`; `fallback_orchestrator.py:59-77` |
| L40 | [misleading] backoff after validation failures, none after exceptions | added | `fallback_orchestrator.py:86-87`, `:89-98` |
| L40 | [misleading] "(simulated failure)" buttons always exhaust; 5 in a row open the breaker | added | `frontend/src/App.js:69-71`; `fallback_orchestrator.py:101`; `circuit_breaker.py:45-53` |
| L40 | [shallow] sync `generate_content` inside async methods | added | `retriever_agent.py:20`; `planner_agent.py:37` |
| L40 | Concepts: A2 and Q1 marked counter-example; V3 "exit shape only" | corrected | `validator_agent.py:19`; `planner_agent.py:39-44`; `fallback_orchestrator.py:83` |
| L40 | What to take D2: concrete Groq `call_llm()` wrapper behind the cache | corrected | `fallback_orchestrator.py:86-98` |
| L40 | Interview: backoff only for transient errors | corrected | `fallback_orchestrator.py:86-98` |
| L41 | Step-by-step control flow and settings | confirmed | `backend/agents/synthesizer_agent.py:23-107`; `backend/agents/cot_engine.py:13-166` |
| L41 | Step prompts label chunks by source, not chunk id | added (step 3) | `cot_engine.py:55-58` |
| L41 | Judge sees only the citation count | added (step 7 + thin) | `backend/agents/coherence_validator.py:25` |
| L41 | Mock `citations` = first 5 request chunks | added | `backend/main.py:109-112` |
| L41 | [misleading] CITATION_GRANULARITY read but unused | added | `main.py:85`; `citation_mapper.py:10` (grep: no other use) |
| L41 | [shallow] sync Gemini calls inside async endpoints | added | `main.py:139-145`; `cot_engine.py:151` |
| L41 | Concepts: C5 and V1 marked counter-example; M3 "weak judge" | corrected | `citation_mapper.py:43-55`; `coherence_validator.py:43-56` |
| L41 | What to take: one grounded Groq call; three plain functions | added | — |
| L41 | Interview answer | confirmed | — |
| L42 | Step-by-step control flow (demo and live) | confirmed | `backend/agents/pipeline.py:16-146`; `backend/tracing/decorator.py:24-68` |
| L42 | Decorator maps capture names by position | added (step 3) | `decorator.py:33-38`; `pipeline.py:107-119` |
| L42 | Tokens keep punctuation; STRICT ×1.3 cannot reorder | added (step 4) | `backend/agents/retriever.py:56-58`, `:63-65` |
| L42 | Failed sink write is printed and lost | added (step 6) | `backend/storage/sink.py:88-89` |
| L42 | [misleading] "rerank" and "semantic" are mis-named | added | `retriever.py:2`, `:54-65` |
| L42 | [shallow] audit records can vanish (queue full, write error) | added | `sink.py:88-89`, `:96-97` |
| L42 | [bug] latent capture-name swap for the validator | added | `decorator.py:33-38`; `backend/agents/validator.py:46-48` |
| L42 | [shallow] synthesizer prompt has no grounding or abstain rule | added | `backend/agents/synthesizer.py:52-65` |
| L42 | [shallow] sync Gemini calls block the event loop | added | `planner.py:52`; `validator.py:66`; `synthesizer.py:66` |
| L42 | risk-timeline also uses the monotonic clock | added | `backend/storage/query.py:42` |
| L42 | Tests: T7 checks only the in-memory ring | added | `sink.py:94-95`; `tests/test_traceability.py:93-110` |
| L42 | Concepts: C6 "partial"; C4 counter-example | corrected | `retriever.py:2`, `:35`; `synthesizer.py:22-34` |
| L42 | What to take: bind by name, sync write, perf_counter, LangSmith later | corrected | `decorator.py:33-38`; `sink.py:88-97` |
| L42 | Interview answer | confirmed | — |
| L43 | Step-by-step control flow (fast and full) and settings | confirmed | `backend/core/orchestrator.py:21-102`; `backend/agents/*.py` |
| L43 | Empty `sub_queries` gives an empty plan, not the fallback | added (step 3 + thin) | `backend/agents/planner.py:69`; `retriever.py:52`; `validator.py:52-59` |
| L43 | Duplicate chunk keeps first sub-query's score; no fusion | added (step 4 + thin) | `backend/agents/retriever.py:59-69` |
| L43 | Audit `chunks_passed` counts the fallback top 3 | added (step 5 + thin) | `backend/agents/validator.py:77`, `:118` |
| L43 | "rate" substring also matches "generate" | added (step 6 + thin) | `backend/core/genai_retry.py:19`, `:23-30`; `synthesizer.py:81` |
| L43 | Synthesis error returned as answer with state DONE; tokens_used = chars/4 | added | `synthesizer.py:90-91`, `:106`, `:109`; `orchestrator.py:85` |
| L43 | Grouped markers `[1, 2]` dropped | added (step 7 + thin) | `synthesizer.py:136` |
| L43 | quality_score 0.5 even with empty context | added (step 8) | `synthesizer.py:97-99` |
| L43 | [shallow] no abstention flag in code | added | `synthesizer.py:36`, `:94-110` |
| L43 | Concepts: A2 added; qualifiers on A5, V2, V3; R1 counter-example | corrected | `orchestrator.py:22`, `:64-71`; `planner.py:20-40`; `retriever.py:52-57` |
| L43 | What to take Q1: "actually use the sub-queries" was wrong (FULL mode does retrieve per sub-query) | corrected | `retriever.py:52-69` |
| L43 | What to take: V3 flag, D2 by error type, C4 in NumPy | added | — |
| L43 | Interview: add "synthesis errors come back as answers" | corrected | `synthesizer.py:90-91` |
| L44 | Step-by-step control flow, metrics and gate | confirmed | `backend/app/main.py:62-89`; `backend/app/evaluator.py:159-223`; `backend/app/metrics.py:146-227` |
| L44 | Demo-score means: n = 1 BLOCKED, n = 2 faithfulness exactly 0.85 (PASS), n ≥ 3 PASS | confirmed (own reimplementation of the formula, not the lesson's code) | `evaluator.py:32-42`; `models.py:32-39`, `:91-96` |
| L44 | Swap needs all four means at 0; partial failures drag means down | added (step 4) | `evaluator.py:45-53`, `:192` |
| L44 | test.sh runs 3 questions, so it gets the fake pass | added (step 4) | `test.sh:29` |
| L44 | tenacity import inside every judge call is not a missing dependency | confirmed (checked, no change) | `backend/requirements.txt:24`; `metrics.py:134` |
| L44 | [shallow] small n, no spread, no per-item floor | added | `evaluator.py:267-281`; `models.py:32-39` |
| L44 | [shallow] judge's claim counts ignored | added | `metrics.py:154` |
| L44 | [shallow] "reproducible" at temperature 0 is UNVERIFIED | added | `metrics.py:119` |
| L44 | Concepts: D3 "fails open"; M2 detail; V4 counter-example | corrected | `evaluator.py:190-210`; `metrics.py:169-197` |
| L44 | What to take: Cohere judge at the end, record/replay, no book text, `recall_at_k`/`mrr`, Codex calibration | corrected | — |
| L44 | Interview: report n per mean | corrected | — |
| L44 | Hard-coded key: only file:line named, value absent from the guide (also in both prior_work copies, line 8) | confirmed | `docker-compose.yml:8` |
| All | Pass A file:line references re-read against every backend `.py` file: all within 3 lines | confirmed | see each lesson |
| Summary | Concepts column updated for all six lessons; L40 biggest problem now names the outage-as-success bug | corrected | see lesson headers |
| Cross | Fail-open bullet extended with L40 and L43 | corrected | L40 `retriever_agent.py:30-38`; L43 `synthesizer.py:90-91` |
| Cross | New bullet: mis-named techniques | added | L41 `cot_engine.py:26-47`; L42 `retriever.py:2`, `:63-65`; L43 `planner.py:25`; L44 `metrics.py:5` |
| Cross | New bullet: blocking LLM calls in async code | added | L40 `retriever_agent.py:20`; L41 `cot_engine.py:151`; L42 `planner.py:52`; L43 `planner.py:50`; L44 `metrics.py:136-139` |
