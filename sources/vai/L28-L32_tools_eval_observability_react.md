# VAI lessons 28–32: tool agent, evaluation, observability, ReAct

[← Guide index](README.md) · Course folder: `C:\Yash\New-Work\RAG\vertical-ai-agents-main\` · Checked 2026-10-17 · Log: [verification/L28-L32_tools_eval_observability_react_log.md](verification/L28-L32_tools_eval_observability_react_log.md)

**What this is:** the guide to VAI lessons 28–32: a tool router, an eval framework, RAG observability and two ReAct lessons.
**What this is not:** the course code, or a run of it. Nothing in the course was run or copied.

**How to read this file:**
- A `file:line` is relative to the project folder named in the lesson heading.
- **UNVERIFIED** marks behaviour that depends on a library version or on Gemini.
- **(counter)** or † means the lesson names a technique without building it. Read it to learn what is missing.
- Tags: **[bug]** the code does the wrong thing · **[misleading]** a label, message or number claims more than the code does · **[shallow]** it works, but is too thin for your project · **[ok-for-demo]** fine for a demo, not for real use · **[LLMOps]** material for your LLMOps notebooks · **[Interview]** worth practising for interviews.
- "I" means the reviewer who checked the code. Each lesson was checked by a reader, a fact-check pass and a completeness pass; the log has every verdict.

**Notes for this block:**
- None of these five lessons has a `setup.sh`; each has only the generated project folder.
- Where a computed result is given, it is a hand count from the code, not app output.

---

## L28 · Tool-equipped agent (RAG + tools router)  (`lesson28/l28-tool-equipped-agent/`)

**What the code teaches, in one line:** This is a one-shot router. Regex rules, with a Gemini classifier as backup, send each query to RAG, to a tool, or to both, and a small Gemini judge then scores the RAG answers.
**What it is not:** It is not an agent loop: nothing repeats think, act, observe. The tools are not real (weather and database are mocks). There is no real reranker and no real corpus, only 5 one-sentence documents. Its "hybrid" means RAG plus a tool in one answer. It is not sparse-plus-dense hybrid retrieval (R1).
**Relevance to your RAG study:** Medium. Concepts: A1, C5, M3, A2 (weak), R3 (counter-example: the "rerank" is a list slice) [LLMOps] [Interview]
**Stack:** FastAPI. ChromaDB `PersistentClient` with Chroma's sentence-transformers embedding function, `all-MiniLM-L6-v2` (`backend/rag/engine.py:18-24`). Chroma's default L2 distance, because no space is set (`backend/rag/engine.py:32-43`). The LLM is Google Gemini through `google-generativeai==0.4.0`, default `gemini-2.0-flash-lite`, with a model fallback chain (`backend/llm_client.py:13-19`, `backend/.env.example:3`). The React UI shows the answer, an intent badge, sources (Chroma doc ids), four score tiles and a stats dashboard. `backend/cli.py` is a terminal client for the same agent.
**Swap to your stack:** Moderate. All LLM calls go through `generate_with_retry`, but Gemini `GenerationConfig` objects are built in four places (`backend/agent/tool_equipped_agent.py:304,458`, `backend/evaluation/evaluator.py:59,83`). MiniLM is already your fallback embedder. For Cohere, Chroma ships a Cohere embedding function, but whether the unpinned Chroma here (`chromadb>=0.5.0`, `backend/requirements.txt:5`) supports `embed-v4.0` is UNVERIFIED. A small custom embedding function always works. One more catch: Cohere wants `input_type="search_document"` for chunks and `"search_query"` for queries. One Chroma embedding function used for both sides may not make that split (UNVERIFIED for this unpinned version). That is a good reason to embed in your own code and pass vectors to the store.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/main.py` | Builds the tool registry and one agent. Endpoints `/api/query`, `/api/stats`, `/api/tools` | 28-35, 50-76 |
| 2 | `backend/agent/tool_equipped_agent.py` | The whole pipeline: route → execute → judge → stats | 54-162, 164-210, 283-313, 412-442 |
| 3 | `backend/rag/engine.py` | Retrieves 5, keeps the first 3, prompts Gemini, falls back to dumping the context | 45-60, 73-132 |
| 4 | `backend/evaluation/evaluator.py` | Two LLM-judge scores plus a length heuristic | 18-42, 44-94 |
| 5 | `backend/llm_client.py` | Retries on 429 and switches model | 13-71 |
| 6 | `backend/tools/*.py` | Base class, registry, calculator (`eval`), mock weather, mock database | `registry.py:23-46`, `calculator.py:33-38` |
| 7 | `frontend/src/App.js` (skim) | Sample buttons, a "quick mode" toggle (no judge), score tiles | 10, 38-42, 144-158 |

### How it works, step by step
We follow the sample query "What is Python?".
1. `/api/query` calls `ToolEquippedAgent.process_query` (`backend/main.py:50-59`).
2. The agent first tries `_try_local_dispatch`, a list of regexes (`tool_equipped_agent.py:69-76,164-210`). They run in this order: hybrid ("X and calculate <digits>", `:168`), calculator (`:180-188`), weather (`:191-195`), database (`:198-204`), and finally RAG phrases such as "what is" or "explain" when the query is longer than 10 characters (`:206-209`). "What is Python?" matches the RAG rule, so the LLM classifier is never called.
3. Only when no regex matches does `_classify_intent` ask Gemini for JSON with `intent_type`, `confidence` and `tool_name` (temperature 0.1, 1024 max tokens). It parses the reply by stripping code fences (`:283-313`). The JSON is not checked against a schema, so a missing key raises an error.
4. RAG branch. `RAGEngine.query` asks Chroma for `top_k=5`, then "reranks" by keeping the first 3 (`rag/engine.py:73-92`). The context is numbered `[1]`…`[3]` (`:95-98`). The prompt says to answer only from the context and to cite sources (`:103-110`). The timeout is `RAG_LLM_TIMEOUT`, 25 s (`:101`). On a timeout, a quota error or an API-key/credentials error, the "answer" is the raw context plus a note (`:115-126`). The returned sources are Chroma ids such as `doc_0` (`:127-132`).
5. Judge. If `include_metrics` is on, `RAGEvaluator.evaluate` runs two Gemini prompts in parallel: groundedness (context vs answer) and relevance (query vs answer). Each asks for a 0–1 score in JSON, at temperature 0.1 with 256 tokens (`evaluator.py:28-31,44-94`). Completeness is just answer length divided by 200, capped at 1 (`:34`). Overall is the plain mean of the three (`:40`).
6. If groundedness is below `EVALUATION_THRESHOLD` (0.7, `tool_equipped_agent.py:42,101`), the agent re-queries with `top_k=10` and `rerank_top_k=7` (`:424-442`). The store holds only 5 documents, so this most likely just puts all 5 into the context. How Chroma handles `n_results` larger than the collection depends on the installed version, which is unpinned (`chromadb>=0.5.0`): UNVERIFIED.
7. Stats are summed in memory for the dashboard (`:114-130`), and the turn is saved in `self.conversations` (`:132-137`).
- Tool branch. For local regex matches, the parameters come from the regex (`:331-332`). Otherwise Gemini extracts the parameters as JSON (`:444-467`), and a second call words the answer (`:469-475`). On the LLM path, a hybrid query runs RAG and parameter extraction at the same time, then makes one synthesis call (`:378-410`).
- Retries. Every LLM call goes through `generate_with_retry`. After a quota error it sleeps the delay parsed from the message (at most 60 s, 30 s when none is found), tries once more, then moves to the next model in the chain (`llm_client.py:22-29,45-63`). The call runs in a worker thread (`llm_client.py:69-71`). Only the RAG answer has a timeout (25 s). The classifier and the judge have none.

### README vs code
- README says "Real-time evaluation metrics" (`README.md:64`). In the code, two scores come from an LLM judge, the third is a length rule, and constants appear whenever something fails (see the next section).
- README gives "Search for Python info and calculate its popularity score" as a hybrid example (`README.md:80`). It has no digits, so no regex matches. It goes to the LLM classifier, and the LLM then has to invent a calculator expression. The result is unpredictable.
- The class docstring says it integrates the L19–L27 RAG pipeline (`tool_equipped_agent.py:29-32`). The engine calls itself "simplified", and it has no chunking, no reranker and no real corpus (`rag/engine.py:15,45-60,90-92`).
- README lists "Conversation history" (`README.md:65`). History is stored, but the prompt context always reads the first conversation ever stored, not the current one (`tool_equipped_agent.py:477-487`).

### Where it is thin or wrong
- [misleading] The sample button "What is FastAPI and calculate 2^10" (`frontend/src/App.js:149`) takes the local hybrid path. That path hard-codes all four scores to 0.75 and adds them to the dashboard averages (`tool_equipped_agent.py:231-233,243`). No judge runs. The dashboard still labels the average "Average Evaluation Scores (n RAG queries)" (`frontend/src/App.js:109`).
- [misleading] If the judge throws an error, every score becomes 0.75 (`:104-105`). If the judge's reply is not valid JSON, the score is 0.5 (`evaluator.py:69-70,93-94`). So under quota errors the screen shows believable numbers for an "answer" that is only a context dump. After a 25 s timeout the judge may still run. It then scores the pasted context against the same context, and completeness is 1.0, because the dump plus its note is longer than 200 characters (`rag/engine.py:115-117`, `evaluator.py:34`).
- [bug] After a low-groundedness re-query, the new answer goes out with the old scores. `_requery_expanded_context` copies `original_result`, which still holds the first `metrics` (`:436-442`). The `requeried` flag is never sent to the client (`:141-148`).
- [bug] On the LLM hybrid path the re-query can delete the tool result. The judge gets only the RAG context, never the tool output (`:394-409`), so the tool half of the answer has nothing to be grounded in. If groundedness comes out below 0.7 (how often depends on the judge: UNVERIFIED), the re-query sends the whole query to RAG alone and replaces the combined answer with a RAG-only one (`:99-103,430-438`). The response still names the tool in `tool_used` (`:144`).
- [shallow] Citations are asked for but never checked. The prompt says "with source citations" (`rag/engine.py:110`). `sources` is every chunk that went into the context, not the chunks the answer cited (`:91-92,127-132`). There is no distance threshold and no "say you don't know" rule, so an off-topic question still gets 3 chunks and an answer (`:82-92,103-110`). This matters for C5, V1 and V3.
- [shallow] The judge is the same model as the generator. Generation and both judge prompts use the same `generate_with_retry` chain, starting from `GEMINI_MODEL` (`rag/engine.py:112`, `evaluator.py:60,84`, `llm_client.py:41-42`). A model grading its own answers tends to be lenient, which is a known LLM-judge bias (M3, V4).
- [shallow] The quota fallback in `process_query` (`:150-159`) almost never does anything. It re-runs the same regexes that `_try_local_dispatch` already ran at `:71`. A query only reaches an LLM call when those regexes returned nothing, or when they matched RAG and the engine let an error through. In the RAG case the fallback calls `_execute_local_dispatch` with the tool name `None`, and the registry raises "Tool not found" (`:159,251-253`, `tools/registry.py:25`).
- [misleading] The "reranking" is a list slice (`rag/engine.py:90-92`).
- [shallow] Completeness is length/200 (`evaluator.py:34`), so a wrong 200-character answer counts as 100 % complete.
- [bug] The weather regex has a second branch that takes any word after "weather" (`:191`). "What's the weather like?" calls the mock with location "like" and gets the default 20 °C Clear (`tools/weather.py:44-48`).
- [bug] The model fallback chain only moves to the next model on quota errors. Any other error, such as a retired model id, is raised at once (`llm_client.py:56-65`). `gemini-exp-1206` in the chain is an experimental id that probably no longer exists (UNVERIFIED).
- [misleading] The calculator calls itself safe (`tools/calculator.py:24`), but it uses `eval` with empty builtins (`:38`). Empty builtins are not a sandbox. On the LLM path, the digit-only regex never filters the expression. Even the local path is unsafe: it turns `^` into `**` (`tool_equipped_agent.py:171,186`), so "calculate 9^9^9" asks `eval` for a number with hundreds of millions of digits. That call is synchronous inside an async tool, so it can tie up the server for a long time (not run).
- [ok-for-demo] The database tool ignores the query and returns the whole mock table (`tools/database.py:47-61`).
- [bug] `Dockerfile:16` copies a `data/` folder that does not exist in the project, so the image build stops there. (A local run creates `backend/data/`, not a top-level `data/`; `start.sh:12,25`, `rag/engine.py:19`.) Even with that folder, `Dockerfile:23` starts `backend.main:app`, but `main.py` uses top-level imports such as the `agent` package (`main.py:9-13`), which cannot be found from `/app`. As written, the Docker route does not work.
- [bug] `cleanup.sh:25-33` stops every Docker container on the machine and prunes all images and volumes, not just this project's. Do not run it.
- [shallow] `ragas`, `datasets`, `duckduckgo-search` and `redis` are pinned (`backend/requirements.txt:11-14`) but never imported.

### Tests and data
- `test.sh:9-22` only checks that the modules import. Nothing tests routing, scores or tools.
- Data: five one-line sentences seeded into Chroma (`rag/engine.py:48-54`), plus mock tables (`tools/database.py:32-45`). Not useful as practice data.

### What to take for your project
- A1: routing with cheap deterministic rules first and an LLM classifier second (`:69-76`). Re-implement it as a small `route(query) -> {route, reason}` function, and log the route so you can measure routing accuracy on a labelled set.
- M3: the judge split is the right shape. Groundedness needs context plus answer. Relevance needs query plus answer. Re-implement it with a binary PASS/FAIL rubric. When the judge fails, return `None`, not a constant, and keep the failure visible. For measurement, do not judge with the generator model, and do not judge live. Your plan already says this: a Cohere judge plus Codex calibration, run once at the end on stored traces. The judge must see everything the answer was allowed to use (here that would include the tool output).
- C5/V1: label each chunk in the prompt with its real chunk id, not `[1]`…`[3]`. Then add a code check: every id the answer cites must be one of the ids you put in the context. Report "cited" and "retrieved" as two separate lists.
- V3: add the abstain rule this prompt lacks, and a score threshold under which you return "not in the documents" without calling the LLM. Measure both on unanswerable questions in your M1 set.
- A2 (weak): "if the grounded score is low, retrieve more and retry" is a real corrective pattern. If you build it, judge the second answer again and record both attempts. The live grader that triggers the retry is part of the system under test. Your offline judge still scores it later.
- Skip the tools, the conversation memory and the Docker files.
- Your earlier copy (`prior_work/VAI/lesson28/`) has these changes. The Dockerfile now installs CPU-only torch and sets `PYTHONPATH=/app/backend`, which fixes the import problem above. It still copies the missing `data/` folder (`prior_work/VAI/lesson28/l28-tool-equipped-agent/Dockerfile:17`), so the build still needs that folder to exist. The compose file uses Node 18 with an anonymous `node_modules` volume. You also added a 1,020-line single-file Streamlit port (`streamlit-demo/app.py`) that uses `google-genai` and `gemini-embedding-001`. The backend Python is unchanged.

### Try this
- About 20 minutes of reading. Make a 4-row table: local tool, local RAG, LLM-classified hybrid, local hybrid. For each row, mark whether each of the four score tiles is (a) an LLM judgment, (b) a heuristic, (c) a constant or (d) absent. Use `process_query` (`:93-107`), `_execute_local_hybrid` (`:212-245`) and `evaluate` (`evaluator.py:18-42`). What to look for: the sample "Hybrid" button shows only constants.

### Interview angle
- Q: "How would you decide between answering from documents and calling a tool?" A: Route with cheap rules first and an LLM classifier as the fallback, and log every routing decision. Evaluate the router on a labelled set, separately from answer quality, because rule false positives (like this weather regex) are a common failure.

---

## L29 · Evaluation framework  (`lesson29/l29-evaluation-framework/`)

**What the code teaches, in one line:** It shows the shape of an eval harness (a JSON test suite, validators, latency percentiles, a regression check against baselines), but almost nothing inside it measures anything real.
**What it is not:** It is not RAG evaluation. The system under test never retrieves anything (`retrieved_chunks` is always empty), and there is no LLM judge and no retrieval metric. The "tool calls" are not real function calls.
**Relevance to your RAG study:** Medium, mostly as a warning. Concepts: M1, M3 (counter-example: word overlap with the reference is called "groundedness"), M4 (weak), D2, D3 [LLMOps] [Interview]
**Stack:** FastAPI, Pydantic, pytest. Gemini `gemini-2.0-flash-exp` via `google-generativeai==0.3.2` (`backend/app/services/agent_service.py:23`, `backend/requirements.txt:5`). No embeddings, no vector store. The Vite + React + Recharts dashboard shows overall accuracy, tool-call accuracy, "RAG Groundedness", P99 latency, tests run, a latency bar chart and a regression list.
**Swap to your stack:** Easy. There is one LLM call (`agent_service.py:35-37`). But the provider is not the problem. The evaluators are.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `data/test_suites/default.json` | The "golden set": 3 cases | 5-27 |
| 2 | `backend/app/models/schemas.py` | TestCase, result and summary models | 11-18, 28-71 |
| 3 | `backend/app/services/evaluation_service.py` | Runs the three evaluators and combines their results | 38-62, 64-132 |
| 4 | `backend/app/services/agent_service.py` | The system under test (LLM or mock) | 16-74 |
| 5 | `backend/app/services/validators.py` | Tool-call check and "groundedness" check | 6-42 |
| 6 | `backend/app/services/latency_profiler.py` | Per-component timing | 6-20 |
| 7 | `backend/app/services/metrics_service.py` | Summary and regression check | 14-81 |
| 8 | `backend/tests/test_validators.py` | 2 unit tests | 4-20 |

### How it works, step by step
We follow the "Run Full Evaluation" button, which sends `test_suite_name: default, iterations: 3` (`frontend/src/App.jsx:38-56`).
1. `/api/evaluate/run` calls `EvaluationService.run_evaluation` (`main.py:54-63`). It loads `data/test_suites/default.json`, or a slightly different hard-coded copy if the file is missing (`evaluation_service.py:134-151`). It caps iterations at 5 (`:41`).
2. Three evaluators run concurrently (`:42-46`). Each one calls the agent itself: the tool evaluator on the tool cases (`:66-70`), the groundedness evaluator on the RAG cases (`:85-88`), and the latency loop on every case again (`:111-113`). So the latency numbers come from different answers than the ones that were scored.
3. The agent. With a key, it sends a one-line prompt that asks for a factual answer and to "specify" a tool if needed, with no list of tools (`agent_service.py:35-37`). Without a key, it sleeps 40 ms and returns a canned answer (`:39-41,62-66`).
4. Tool "extraction" is a keyword search in the free text. If the text contains `get_weather`, it adds a hard-coded `get_weather` call with `location: San Francisco`. If it contains `search_places` or `restaurant`, it adds a hard-coded `search_places` call (`:54-60`). In mock mode, canned tool calls are added by keyword (`:43-44,68-74`).
5. Tool validator. The first tool call's name must equal `expected_tool`, and the parameter score must be at least 0.8. A parameter matches when the expected string appears inside the actual one (`validators.py:7-27`). Accuracy is the share of tool cases that pass (`evaluation_service.py:49`).
6. "Groundedness". The answer is split on full stops, and pieces longer than 10 characters are kept. A piece counts as supported if more than 50 % of its lower-cased, space-split words appear in one source (`validators.py:32-42`). The sources are `retrieved_chunks + ground_truth_docs`, and `retrieved_chunks` is always `[]` (`agent_service.py:48`). So this is really overlap with the reference text. A case passes at a score of 0.7 or more (`evaluation_service.py:100`), and the suite score is the mean (`:50`).
7. Latency. For up to 5 cases × iterations, `profile_query` records four timings (`latency_profiler.py:9-19`). "Retrieval" is a fixed 20 ms sleep. "llm_inference" is the real call. "tool_execution" is a fixed 10 ms sleep, recorded only when the answer has tool calls (`:15-18`). The last is the total. Percentiles are index picks on the sorted list (`evaluation_service.py:121-131`).
8. Summary. Overall accuracy is the mean of tool accuracy and groundedness (`metrics_service.py:39`). Average latency is the mean of the component means, "total" included (`:37`). If a latency value is zero, the summary shows 100 ms (average) or 200 ms (P99) instead (`:42-43`).
9. Regression. The latest summary is compared with fixed baselines of 0.95, 0.90 and 500 ms, and a metric is flagged if it is more than 5 % worse (`metrics_service.py:14-18,61-81`).

### README vs code
- README says to set `GEMINI_API_KEY` "for real LLM evaluation" (`README.md:37`). The LLM only produces the answer. No LLM grades anything.
- README Quick Start runs `./setup.sh` from `lesson29/` (`README.md:9`). There is no `setup.sh`.
- The dashboard says "RAG Groundedness" (`frontend/src/App.jsx:88`). The system under test does no retrieval (`agent_service.py:48`).
- "Regression detection" suggests comparing one run with earlier runs. The code compares against hard-coded targets and keeps history only in memory (`metrics_service.py:12-18,26-29`).

### Where it is thin or wrong
- [misleading] Without a key, the mock is built to pass. My hand check of the canned answers and canned tool calls (`agent_service.py:62-74`) against the validators (`validators.py:20-42`) gives tool accuracy 1.0 and groundedness 1.0 on the default suite (not run).
- [bug] An empty answer scores groundedness 1.0 (`validators.py:34`). Any LLM error produces an empty answer (`agent_service.py:50-52`). So a broken model shows "100 % grounded". Likely cause: `gemini-2.0-flash-exp` may be a retired id (UNVERIFIED). Short sentences vanish the same way. Claims are cut only on full stops and must be longer than 10 characters (`validators.py:32`). So "Python 3.12 is fast." splits into "Python 3" and "12 is fast", both too short, and also scores 1.0 (hand count).
- [bug] The pass/fail counts are wrong. `total` is cases × iterations (9), but `passed` counts each tool or RAG case once (`evaluation_service.py:47-48`). Even a perfect run shows 3 passed and 6 failed.
- [misleading] With a key, tool-call accuracy only checks whether the answer text contains a keyword. The parameters are hard-coded (`agent_service.py:56-59`) and equal the default suite's expected values (`default.json:10,26`), so on this suite the parameter match cannot fail once the keyword is there.
- [misleading] The "retrieval" and "tool_execution" latencies are fixed sleeps (`latency_profiler.py:10,17`).
- [misleading] "Overall accuracy" averages two different kinds of number: a pass rate for tools and a mean overlap score for RAG (`metrics_service.py:39`, `evaluation_service.py:49-50`). A drop in one can hide behind a rise in the other.
- [shallow] There are only 9 samples, so P95 and P99 are both the maximum (`evaluation_service.py:126-128`).
- [shallow] Word overlap is not groundedness. Punctuation stays attached to words, true paraphrases fail, and false claims that reuse the reference's words pass (see Try this). `unsupported_claims` is always empty (`validators.py:35`).
- [misleading] On page load, the dashboard fetches regressions before any run. Zero scores against the 0.95 and 0.90 targets show two "Regression detected" alerts (`App.jsx:13-14,158`, `metrics_service.py:47-55,72`).
- [shallow] `iterations` accepts values up to 1000 (`schemas.py:22`), but it is capped at 5, and only the latency loop and the `total` count use it (`evaluation_service.py:41,47,111`).
- [bug] With a key, a blocking `generate_content` call sits inside async code (`agent_service.py:35`). It stalls the event loop, so the "concurrent" evaluators actually run one after another. (In mock mode, the `asyncio.sleep` at `:40` lets them interleave.)

### Tests and data
- `tests/test_validators.py:4-10` checks the tool validator on an exact match. `:12-20` checks that one overlapping sentence scores above 0.5. Nothing tests the empty-answer case, the mock path or the pass/fail counts.
- `data/test_suites/default.json` has 3 cases: 2 tool cases and 1 RAG case. Its fields (`id`, `type`, `query`, `expected_tool`, `expected_params`, `ground_truth_docs`) make a usable starting schema. The content does not.

### What to take for your project
- M1: copy the idea of a versioned JSON test suite with typed cases. For RAG, add `relevant_chunk_ids`, `answer_key_points`, `answerable` and a `suite_version`.
- M4/D3: compare each run with your previous stored run, not with fixed targets. Save every run to disk, and report counts that add up.
- M3: replace word overlap with a binary judge on stored traces. Your plan already covers this: a Cohere judge plus Codex calibration at the end. Keep a code-based check as a cheap first tier, for example "every cited chunk id was actually retrieved".
- M3/V2: keep two metrics apart that this lesson merges. Groundedness compares the answer with the chunks you retrieved. Correctness compares the answer with the reference answer in your eval set. This lesson pools both sources into one list (`validators.py:33`), and with no retrieval only the reference is left. So its "groundedness" is really a rough correctness score.
- D2: time only real stages. With fewer than about 100 samples, report the median and the maximum, not P99.
- Tool-use evals (interview): score tool selection, argument correctness and execution separately. This lesson collapses all three into one keyword test.
- Your earlier copy (`prior_work/VAI/lesson29/`) added a Dockerfile and compose files (ports 8001/3001) and edited `frontend/vite.config.js` so the proxy target comes from `VITE_BACKEND_URL`. It also added a combined L29+L30 Streamlit app (`streamlit_app/`) built on LangChain, Groq, Cohere embeddings and in-memory Chroma, with edited copies of the services. The course backend files are unchanged. The copy has no `frontend/src/` folder.

### Try this
- About 15 minutes with pen and paper. First cut the answer into claims on full stops, keeping pieces longer than 10 characters (`validators.py:32`). Then use the rule in `validators.py:37-42`: split on spaces, lower-case, keep punctuation. A claim is supported if more than 50 % of its words appear in one reference sentence from `default.json:17-18`. Score three answers:
  - (a) "Python uses indentation to make code easy to read."
  - (b) "Python is an interpreted, high-level, general-purpose programming language that was invented in 2015."
  - (c) an empty answer.
  My hand count: (a) 0.0, though it is true (only 1 of its 8 distinct words matches either sentence). (b) 1.0, though "2015" is false (7 of 13 words match the first sentence, just over half). (c) 1.0. Then write one sentence on what a faithfulness check must do instead.

### Interview angle
- Q: "How do you evaluate a tool-calling agent?" A: Build a labelled set with the expected tool and arguments. Score tool selection, argument validity (against the schema), execution and the final answer separately. Never let mocks or fixed parameters produce the score, and compare each run with the last stored run.

---

## L30 · RAG observability  (`lesson30/l30-rag-observability/`)

**What the code teaches, in one line:** A hand-rolled telemetry layer. Each HTTP call gets one request id. Four RAG stages have timers. structlog writes JSON logs. Metric points are flushed to SQLite every 10 s, and a WebSocket feeds a live dashboard.
**What it is not:** It is not OpenTelemetry or Prometheus: there are no spans and no exporters. It is not a replayable trace either. It never stores the query, the retrieved chunk ids, their scores, the prompt or the answer.
**Relevance to your RAG study:** Medium. The topic is exactly D1, but the code leaves out what matters. Concepts: D1, D2, C6 (an end-to-end pipeline, but no provenance), P4 (counter-example: 1 − L2 distance is called "similarity") [LLMOps] [Interview]
**Stack:** FastAPI with Starlette `BaseHTTPMiddleware`, structlog, aiosqlite. In-memory ChromaDB 0.4.22 (`chromadb.Client()`) and a local `SentenceTransformer('all-MiniLM-L6-v2')` (`backend/services/rag_service.py:16-17`). The LLM is Gemini `gemini-pro` via `google-generativeai==0.4.0` (`rag_service.py:15`). The React dashboard shows total requests, average latency, tokens, cost, error rate and cache hit rate. For each query it also shows stage latencies, chunk count, average similarity, cost and a short trace id.
**Swap to your stack:** Easy. There is one generate call (`rag_service.py:177-180`), and the embedder is already your MiniLM fallback. Groq returns real `usage` token counts, which you can record in place of word counts. The code passes its own vectors to Chroma (`rag_service.py:34-38,112-115`), so a Cohere `embed-v4.0` swap is easy too. Use `input_type="search_document"` for the chunks and `"search_query"` for the query. Then either create the collection with a cosine space or normalise the vectors and compute the dot product yourself in NumPy.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/middleware/observability.py` | Trace id, timing, request logs | 11-57 |
| 2 | `backend/services/rag_service.py` | Four instrumented stages | 41-89, 91-223 |
| 3 | `backend/services/metrics_collector.py` | Buffer, aggregates, SQLite flush, stats | 51-67, 86-107, 122-149 |
| 4 | `backend/services/structured_logger.py` | JSON log lines with trace id and stage | 7-69 |
| 5 | `backend/app/main.py` | Routes and the WebSocket | 17-31, 45-83 |
| 6 | `backend/models/telemetry.py` | Data models, mostly unused | 15-61 |

### How it works, step by step
We follow `POST /api/query` with "What is RAG?".
1. The middleware creates a fresh `uuid4` trace id, stores it on `request.state`, starts a timer, and logs `received` with the method and path (`observability.py:13-25`). It never reads an incoming trace header, so nothing propagates between services.
2. The route passes the id to `InstrumentedRAGService.process_query` (`main.py:45-55`).
3. Embed. It logs the query's length (not its text), encodes with MiniLM synchronously, and records `embedding_latency_ms` (`rag_service.py:91-104`).
4. Retrieve. Chroma is asked for `n_results=3` (`:112-115`). "Similarity" is 1 − distance (`:119`). It records `retrieval_latency_ms`, `chunks_retrieved` and only the average similarity (`:121-126`). The chunk ids and per-chunk scores are thrown away.
5. Augment. It joins the chunks as "Context i: …" and counts tokens as whitespace-separated words (`:139-140`). It records `augmentation_latency_ms` and `context_tokens` (`:143-144`).
6. Generate. The prompt is a plain "use this context to answer the question", with no grounding rule, no abstain rule and no request for citations (`:160-167`). The call runs in a thread (`:177-180`). Prompt and completion "tokens" are word counts (`:169,182`). Cost is word counts × fixed per-1K prices labelled as a Gemini Pro estimate (`:186`, prices UNVERIFIED). On any error, it returns fallback text that pastes the context, counts that text's words as completion tokens, sets cost to 0 and increments `llm_fallbacks` (`:187-201,225-244`).
7. It records `pipeline_latency_ms` (`:63`) and returns the answer, the per-stage metrics and the trace id (`:71-84`). The middleware then records `total_latency_ms` and sets an `X-Trace-ID` response header (`observability.py:31-42`, `metrics_collector.py:77-84`).
8. Every `record` call adds a point to a buffer. Metrics whose names end in `_latency_ms` also go into one shared `latency_samples` deque (`metrics_collector.py:51-67`). A background task writes the buffer to `data/metrics.db` every 10 s (`:13,122-149`).
9. Dashboard. The WebSocket pushes `get_stats` every 2 s (`main.py:72-83`). `/api/timeseries/{metric}` reads from SQLite (`main.py:63-67`, `metrics_collector.py:109-120`).

### README vs code
- README promises "Distributed tracing with trace ID propagation" (`README.md:8`). The code makes one request id per HTTP call. A `TraceSpan` model with `parent_span_id` exists (`models/telemetry.py:15-24`), but nothing uses it. `RAGMetrics`, `LogEntry` and `PipelineStage` are unused too.
- README promises "Token usage and cost tracking" (`README.md:11`). The code counts words and multiplies by a guessed price. It never reads the provider's usage data.
- README mentions trace sampling and under 8 ms of overhead (`README.md:77,82`). There is no sampling code, and the overhead figure is UNVERIFIED.
- `prometheus-client` and `python-json-logger` are pinned (`backend/requirements.txt:12,14`) but never imported. structlog does the JSON logging.
- `SETUP_AND_RUN.md:5-16` lists fixes to a `setup.sh` that is not in the folder. `:28` is the author's home path.

### Where it is thin or wrong
- [bug] "Total Requests" counts latency samples, not requests (`metrics_collector.py:90-98`). Each query adds six samples: five from `rag_service.py:63,102,122,143,205` plus the middleware's `total_latency_ms`. Every `/health` or `/api/stats` call adds one more.
- [bug] Average, P50, P95 and P99 come from that mixed pool (`:95-102`). Sub-millisecond augmentation timings (a string join) sit next to generation timings that include a network call, so the numbers describe no single thing.
- [bug] The time window is ignored. `cutoff` is computed and never used (`:88`), so the dashboard's "5-minute" window (`main.py:79`) is really all-time, up to the last 10,000 samples (`metrics_collector.py:17`).
- [misleading] The error rate stays near 0 even when every LLM call fails. Failures are caught and counted as `llm_fallbacks`, which the dashboard never shows (`rag_service.py:187-201`, `metrics_collector.py:105`). Errors that do get counted (exceptions that reach the middleware, `observability.py:56`) are divided by the number of latency samples, not requests, so even they show at about a sixth of their real rate when most traffic is queries (hand count from the six samples per query; `metrics_collector.py:105`).
- [misleading] The cache hit rate is always 0, because there is no cache (`metrics_collector.py:106`).
- [misleading] "Total Tokens" counts only completion words (`:103`).
- [misleading] Similarity is 1 − Chroma's default L2 distance. The collection is created without a cosine setting (`rag_service.py:20,119`), so this is not cosine similarity and it can go negative. To be precise: Chroma's default `l2` space returns squared Euclidean distance, and MiniLM's vectors come out unit length (both are library behaviour: UNVERIFIED here). If both hold, 1 − d equals 2·cos − 1. The ranking is still right, but a "similarity" of 0.5 means a cosine of 0.75. Any threshold you copy from this number would be off.
- [bug] `gemini-pro` is an old model id that current keys will most likely reject (UNVERIFIED). If so, every answer is the fallback text.
- [shallow] The trace has no query text, chunk ids, per-chunk scores, prompt, model id or answer. You cannot replay or diagnose an answer from the logs.
- [bug] A local (non-Docker) run writes to `data/metrics.db` relative to the working directory (`metrics_collector.py:13`). The `data/` folder is not in the repo, and the non-Docker branch of `scripts/start.sh:20-27` does not create it, so startup can fail outside Docker. Docker creates the folder (`Dockerfile:18`).
- [shallow] `asyncio.sleep(0)` is there to "simulate async", but the encoder still blocks the event loop (`rag_service.py:97-99`). `asyncio==3.4.3` is pinned from PyPI (`requirements.txt:15`). It is an old backport you never need.

### Tests and data
- `scripts/test.sh:23-39` is a curl smoke test (health, one query, stats) that checks no values. `scripts/demo.sh:31-44` sends three queries.
- Data: five one-line sentences (`rag_service.py:25-31`). Not usable as practice data.

### What to take for your project
- D1/C6: keep the good parts: one trace id per query that the caller gets back, a timer per stage, and JSON lines. Add what is missing: the query, `snapshot_id`, retrieved chunk ids with ranks and scores, the prompt template version, the model id, token usage as reported by the provider, the answer, cache hit or miss, and an error/fallback flag. Write one JSONL line per query. That file is also your M3 judge input and the key for your record/replay cache.
- D2: keep one histogram per stage and compute percentiles per stage, never across stages. Count requests with a plain counter.
- Treat every fallback as an error in monitoring. A silent fallback hides an outage.
- Later, in the LLMOps notebook, map the same fields onto LangSmith or OpenTelemetry spans. The plain-Python JSONL comes first. A trace holds the query, the chunks and the answer, so send traces to a hosted service only for your practice corpus, never for book text. Keep the local JSONL as the record.
- P4/C6: log the raw distance and the metric name (`l2`, `cosine`, `ip`) next to each chunk id. Do not log a converted "similarity" whose formula the reader has to guess.
- Your earlier copies: `prior_work/VAI/lesson30/` is the original without its CSS files and `.gitignore`. `prior_work/VAI/lesson29/l30-rag-observability/` changes `chromadb` to `>=0.5,<0.6`, removes the `asyncio` pin and adds CPU-only torch to the Dockerfile.

### Try this
- About 20 minutes. Walk one query through `rag_service.py`. Write down every metric name it records and where each lands: `latency_samples` or `counters`. Predict what "Total Requests" and "Total Tokens" will show after two queries and one `/health` call. Then write the JSON schema of the trace line you want for ragkit, and tick the fields this lesson already has.

### Interview angle
- Q: "What do you log for each RAG request?" A: A trace id, plus each stage's inputs, outputs and timing: the query, retrieved chunk ids with their scores, the prompt version, the model, real token usage and cost, the answer, and any error or fallback. That is enough to replay the request and tell whether retrieval or generation failed.

---

## L31 · ReAct planning: a thought loop without tools  (`lesson31/l31-react-planning/`)

**What the code teaches, in one line:** A loop that asks Gemini up to N times for JSON {thought, action, confidence, is_terminal}, feeding the model's own last thought and action back in each time.
**What it is not:** It is not ReAct. No action is ever executed, so there is never a real observation. There are no tools and no retrieval.
**Relevance to your RAG study:** Low. Concepts: A5 (counter-example: called ReAct, but nothing acts) [LLMOps] [Interview]
**Stack:** FastAPI, pydantic-settings. Gemini `gemini-2.5-flash-lite` with safety set to `BLOCK_ONLY_HIGH` (`backend/app/services/reasoning_engine.py:43-44`). No embeddings, no vector store. The React UI has a task form (1–20 iterations), a step trace with confidence colours, and plan metrics over a WebSocket.
**Swap to your stack:** Easy. There is one call (`reasoning_engine.py:19`). Ask Groq for JSON output.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/app/services/react_planner.py` | The loop | 14-85 |
| 2 | `backend/app/services/reasoning_engine.py` | Prompt, JSON parsing, error handling | 47-144 |
| 3 | `backend/app/models/schemas.py` | Reasoning, Observation and Trace models | 5-44 |
| 4 | `backend/app/api/routes.py` | `/api/v1/plan` and error mapping | 9-36 |

### How it works, step by step
1. `/api/v1/plan` calls a module-level `ReActPlanner` (`routes.py:7-13`). The first observation is the task plus `initial_context` (`react_planner.py:24-28`).
2. Each iteration builds a prompt with the task, the previous thought and action, the context dict and the last 5 actions. It asks for JSON only, and its example shows a confidence of 0.85 (`reasoning_engine.py:111-144`).
3. The reply is stripped of code fences, cut to the outermost braces, parsed with `json.loads` and validated as `Reasoning`, with confidence between 0 and 1 (`:65-78`, bounds at `schemas.py:8`). Tokens are counted as the words in the prompt plus the reply (`:83`).
4. The loop stops when `is_terminal` is true. Otherwise it runs up to `max_iterations`, default 10 (`schemas.py:39`, `react_planner.py:31,50-51`).
5. The next "observation" is built from the model's own thought and action, plus a context dict with `confidence_trend` and `action_count` (`react_planner.py:54-60,80-85`). Nothing from outside enters the loop.
6. The status is COMPLETED if the last step was terminal, otherwise MAX_ITERATIONS (`:70`).

### README vs code
- README promises an "Observe→Thought→Action→Observe loop" and an `ObservationStore` (`README.md:3,40`). There is no store and no action execution. The "observation" is the model's previous output.
- README lists "Confidence scoring" (`README.md:11`). It is the model's self-reported number. The prompt's example shows 0.85 (`reasoning_engine.py:139`), which may anchor it (UNVERIFIED: that is model behaviour, not something the code shows).
- The `MAX_ITERATIONS` and `REASONING_TIMEOUT` settings (`core/config.py:8-9`) are never read. The request value has no upper bound (`schemas.py:39`). Only the UI caps it at 20 (`frontend/src/components/PlanningForm.js:35-36`).

### Where it is thin or wrong
- [misleading] It is called ReAct, but there is no Act step (`react_planner.py:35-60`).
- [bug] Errors and quota failures become a terminal step with confidence 0, so the plan is reported as COMPLETED (`reasoning_engine.py:92-109`, `react_planner.py:70`). Only API-key errors are re-raised instead (`reasoning_engine.py:94-95`). This also covers a reply that is not valid JSON, or one whose confidence is outside 0–1: the parse or validation error lands in the same handler (`reasoning_engine.py:77-78,104-109`). Any message containing "exceeded" gets the rate-limit text (`:97`).
- [bug] `total_tokens` is set once, at first configuration, and never reset (`reasoning_engine.py:45,88`). Each trace therefore reports the running total of all plans since startup, and `record_plan` then adds that running total to the dashboard again (`metrics_collector.py:18`).
- [bug] With `max_iterations: 0`, `steps` stays empty and `steps[-1]` crashes (`react_planner.py:70`).
- [misleading] Any error message containing "400" is reported as an expired API key (`routes.py:31-35`).

### Tests and data
- `test.sh:9-43` is a live smoke test that needs running services and a key. It checks only that the words "healthy", "task_id" and "root" appear. There are no unit tests and no data.

### What to take for your project
- Context only. One part is useful: the per-step trace record (iteration, thought, action, latency, tokens, terminal flag; `schemas.py:19-35`) is a fine shape for logging your A5 agent's steps. Use L32 for the real loop.

### Try this
- About 15 minutes. Put L31's `ReActPlanner.plan` next to L32's `ReActAgent.execute` and fill in a table: who produces the observation, how the output is parsed, what stops the loop, what happens on an error, and what status is reported. What to look for: L31 has no line that runs anything.

### Interview angle
- Q: "What makes ReAct different from chain-of-thought planning?" A: ReAct interleaves reasoning with actions whose results come back from the environment as observations, so the model can correct itself with new facts. A loop that only feeds its own thoughts back, like this one, can rethink its reasoning, but it cannot bring in a single fact it did not already have. For RAG this is the whole point: the retrieval tool's result is the observation.

---

## L32 · ReAct agent with tools  (`lesson32/l32-react-agent/`)

**What the code teaches, in one line:** A real text-protocol ReAct loop. Gemini writes Thought, Action and Action Input; regexes parse them; a registered Python tool runs; and its observation is appended to the prompt until the model says FINISH or the step limit is reached.
**What it is not:** It is not agentic RAG. There is no vector store and no document-search tool. The only knowledge tool is a Wikipedia exact-title lookup, the stock and weather data are simulated, and there is no native function calling.
**Relevance to your RAG study:** Medium. Concepts: A5, A1 [LLMOps] [Interview]
**Stack:** FastAPI. `google-generativeai==0.3.2` with REST transport (`backend/app.py:45`). The model list is `gemini-2.5-flash` → `gemini-2.5-flash-lite` → `gemini-2.0-flash` → `gemini-2.0-flash-lite`, at temperature 0.2 with at most 512 output tokens (`backend/agent.py:17-21,26`). Wikipedia via `wikipedia-api` (`backend/tools.py:50-53`). The React UI shows example queries, the tool list and the Thought→Action→Observation trace.
**Swap to your stack:** Easy. There is one call site (`agent.py:265`), and the text protocol works with any chat model. With `openai/gpt-oss-20b`, read only the final message content (not the reasoning) and set `reasoning_effort="low"`. Stop the model at "Observation:". Whether Groq's `stop` parameter works for this reasoning model is UNVERIFIED, so also cut the reply at the first "Observation:" in your own code; that always works. Do not copy the 512-token cap (`agent.py:18`). With a reasoning model the reasoning can use up a small budget and leave an empty reply, and here an empty reply becomes a parse failure (`agent.py:247,77-85`). Your project rule already says: give it enough `max_tokens`.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/tools.py` | Tool base class, registry, 4 tools | 10-44, 46-214 |
| 2 | `backend/agent.py` | Prompt, loop, parser, tool runner, retries, offline fallback | 38-145, 314-359, 259-301, 147-230 |
| 3 | `backend/app.py` | API and in-memory sessions | 37-52, 94-145 |
| 4 | `backend/test_agent.py` | 3 live tests | 8-38 |

### How it works, step by step
We follow "What is 1234 * 5678?".
1. The app refuses to start without a key (`app.py:37-43`). It registers 4 tools, each named after its class minus "Tool": Wikipedia, StockPrice, Calculator, Weather (`tools.py:32-36`, `app.py:48-52`).
2. `/agent/query` builds a new `ReActAgent` for each request. `max_iterations` comes from the request (default 5, no upper bound). The route then calls the synchronous `execute` (`app.py:55-58,102-114`).
3. The prompt lists each tool's name, description and parameter schema. It then gives the exact format: Thought, Action (a tool name or FINISH), Action Input as JSON, and an Observation line to leave blank. Its rules say one tool per step and FINISH when done (`agent.py:47-65,303-312`).
4. Each iteration calls the model (`:70`) and parses the reply with three regexes (`:314-344`). The first takes the Thought up to the next "Action:". The second takes the first word after "Action:". The third takes the first `{…}` after "Action Input:" and loads it as JSON.
5. If the action is FINISH, the agent returns `answer` from the Action Input (`:92-106`). Otherwise it runs the tool, passing the JSON as keyword arguments (`:346-359`). An unknown tool name becomes an observation that lists the valid tools (`:350`). The calculator accepts only digits and operators before calling `eval` (`tools.py:141-148`).
6. The model's whole reply, the real "Observation: …" and a "Continue reasoning:" cue are appended to the prompt (`agent.py:121`), and the loop repeats.
7. The loop stops on FINISH, on a parse failure (`:77-85`), on an exception (`:123-138`), or at `max_iterations` (`:67`).
8. Retries allow up to 3 attempts. On 429-like errors the agent switches to the next model, or else sleeps the suggested delay plus 5 s (at most 120 s, or 35 s when no delay is found; `:249-257`). On timeouts it backs off 2 s, then 4 s (`:259-301`). If the first iteration hits a quota error, a keyword router calls tools directly, without the LLM, and reports success (`:126-129,147-230`). Each request builds a new agent, so the model index starts again at `gemini-2.5-flash` every time, even after that model ran out of quota (`app.py:102-106`, `agent.py:31-35`).

### README vs code
- README says the LLM is Gemini 1.5 Flash (`README.md:67`). The code uses the 2.x list (`agent.py:26`).
- The Wikipedia tool describes itself as a search (`tools.py:82`). In fact `wiki.page(query)` looks a page up by its title, with no search step, and returns the first 500 characters of the summary (`tools.py:58-60`). A query that is not a page title returns "not found" (`tools.py:66-71`). Whether redirects and case variants are resolved depends on `wikipedia-api==0.6.0` (`backend/requirements.txt:7`): UNVERIFIED.
- README claims "Enterprise-Ready … retry logic" (`README.md:10`). Retries exist, but they block the whole server (see the next section).
- `docs/API.md:23-31` shows a price with no "simulated" label. The real tool output adds "(simulated data)" (`tools.py:109`).

### Where it is thin or wrong
- [bug] Early stops get the wrong label. After a parse failure or an error, the result says "Max iterations reached without completion", with `iterations` set to the limit (`agent.py:140-145`).
- [shallow] There is no stop sequence (`agent.py:17-21`). The model can write its own fake "Observation:" in one reply and keep going. Only the first action runs, and the invented text stays in the prompt history (`:121`).
- [shallow] The Action Input regex is non-greedy (`:326`). Nested JSON is cut at the first `}`, and the run ends as a parse failure.
- [bug] `execute` is synchronous inside an `async` route (`app.py:95,114`), and the retries call `time.sleep` for up to 120 s (`agent.py:293`). One slow request freezes the whole server.
- [bug] Any message containing "exceeded" is treated as a rate limit (`:277`). A "Deadline Exceeded" timeout therefore switches models instead of backing off. Also, with only 3 attempts (`:263`), `MAX_RATE_LIMIT_RETRIES = 5` (`:14`) can never be reached.
- [misleading] The quota fallback answers any stock question with GOOGL and AAPL when no company is recognised, and marks the result `success: True` (`:158-160,175`).
- [misleading] The tests pass even when the LLM never works. `test_agent.py` never calls `genai.configure` (only `app.py:45` does), so whether the SDK finds a key on its own in the tests is UNVERIFIED. Either way, the asserts accept any trace, including an error step (`test_agent.py:20-38`). On an error, `iterations` is set to the limit (`agent.py:144`), so the check at `test_agent.py:24` passes too. A green test run proves nothing.
- [bug] The calculator whitelist allows `*` twice in a row, so `**` (power) gets through (`tools.py:141`). An Action Input such as `9**9**9` makes `eval` build a number with hundreds of millions of digits (`tools.py:148`). It runs inside the synchronous loop, so it can freeze the server for a long time (not run). This is a D4 issue: a whitelist on characters is not a safe evaluator.
- [shallow] The Wikipedia observation loses its provenance. It keeps only the title the model asked for and the first 500 characters of the summary, cut mid-word if need be (`tools.py:58-63`). There is no page URL or revision id. The FINISH answer has no citation field (`agent.py:92-106`), so nothing links the answer to the text it came from.
- [ok-for-demo] The `api_key` argument is unused (`agent.py:28`). Sessions live only in memory and are overwritten when an id is reused (`app.py:82,117-121`).

### Tests and data
- `backend/test_agent.py` has 3 live tests, skipped without a key (`:8-10`), with asserts too weak to fail (see above). `scripts/test.sh:20` runs them. There are no data files. The simulated prices and weather are hard-coded (`tools.py:96-102,178-184`).

### What to take for your project
- A5: re-implement this loop in plain Python with Groq for ragkit. Give it a tool `search_chunks(query, k)` that returns chunk ids, text and scores, and possibly `get_chunk(id)`. The FINISH answer must cite chunk ids that appeared in observations. That is a V1 check you can verify in code.
- Keep: the tool registry with schemas in the prompt, the unknown-tool message as an observation, observations appended to the history, and an explicit step limit.
- Fix: stop generation at "Observation:", validate the Action Input against a schema, and cap `max_iterations` on the server. Return an honest status (`finished`, `parse_error`, `tool_error`, `step_limit`). Log every step to the same JSONL trace you design from L30 (D1).
- Cache: wrap each Groq call in your record/replay cache. Key it on the full prompt so far, the model id and the settings. Then a whole trajectory replays without credits, and a changed prompt is a cache miss you can see.
- Test it offline: put a scripted fake model behind the same call (a fixed list of replies). Then write asserts that can fail: the status for a nested-JSON reply is `parse_error`, a fake "Observation:" in a reply is cut off, and the step limit is honoured. L32's own tests cannot fail.
- Later, compare this with native tool calling and with LangGraph. The D-32 order applies: the mechanism comes first.

### Try this
- About 20 minutes on paper. Push three made-up replies through `_parse_response` (`agent.py:314-344`):
  - (1) an Action Input with nested JSON;
  - (2) "Action: [Calculator]";
  - (3) one reply that contains a Thought, an Action, a fake Observation and then "Action: FINISH".

  For each, predict the parsed result and what `execute` does next. What to look for: (1) ends the run as a parse failure. (2) fails to parse, because `\w+` cannot start at "[". (3) runs the first tool and leaves the fake observation in the prompt.

### Interview angle
- Q: "How do you keep a ReAct agent from looping or inventing tool results?" A: Cap the steps and the time on the server, and stop the same tool call with the same arguments from repeating. Use a stop sequence, or cut the reply at "Observation:", so the model cannot write its own observation. Validate tool arguments against a schema, and return an explicit failure status. Then evaluate whole trajectories (tool choice, arguments, final answer) on a labelled set.

---

## Block summary
| Lesson | Title | Relevance | Concepts | Best file to read | Biggest problem |
|---|---|---|---|---|---|
| L28 | Tool-equipped agent (router) | Medium | A1, C5, M3, A2 (weak), R3 (counter) · LLMOps · Interview | `backend/agent/tool_equipped_agent.py` | Hard-coded 0.75 scores on the local (regex) hybrid path and on judge failure (`tool_equipped_agent.py:105,231-233,243`); re-query keeps the old scores and can drop the tool result (`:430-442`) |
| L29 | Evaluation framework | Medium (as a warning) | M1, M3 (counter), M4 (weak), D2, D3 · LLMOps · Interview | `backend/app/services/validators.py` | An empty or failed answer scores 1.0 groundedness (`validators.py:34`, `agent_service.py:50-52`); no retrieval at all (`agent_service.py:48`); fake sleep latencies (`latency_profiler.py:10,17`) |
| L30 | RAG observability | Medium (topic High, code thin) | D1, D2, C6 (no provenance), P4 (counter) · LLMOps · Interview | `backend/services/metrics_collector.py` + `rag_service.py` | Trace has no query, chunk ids, scores, prompt or answer; "Total Requests" and percentiles pool all stage samples (`metrics_collector.py:63-65,90-102`) |
| L31 | ReAct planning | Low | A5 (counter) · LLMOps · Interview | `backend/app/services/react_planner.py` | No Act step: the observations are the model's own output (`react_planner.py:54-60`); errors are reported as COMPLETED (`:70`) |
| L32 | ReAct agent | Medium | A5, A1 · LLMOps · Interview | `backend/agent.py` | Tests pass without a working LLM (`test_agent.py:20-38`); early stops get the wrong label (`agent.py:140-145`); the sync loop blocks the server (`app.py:114`) |

### Cross-lesson patterns
- **Gemini everywhere, with drifting model ids.** The lessons use `gemini-2.0-flash-lite`, `gemini-exp-1206`, `gemini-2.0-flash-exp`, `gemini-pro`, `gemini-2.5-flash-lite` and the `2.5-flash` list, under two different SDK pins. Some of these ids are likely retired (UNVERIFIED). L28, L31 and L32 each write their own 429 retry (L28 `llm_client.py:37-66`, L31 `reasoning_engine.py:14-29`, L32 `agent.py:259-301`); L29 and L30 have none. L28 and L32 also answer without the LLM. L28 runs its regex router before any LLM call, so regex matches skip the LLM by design (`_try_local_dispatch`, `tool_equipped_agent.py:71`). Its second regex pass on quota errors (`:150-159`) re-runs the same rules and almost never changes anything. L28's real quota fallback is the context dump returned as an answer (`rag/engine.py:115-126`). L32 has a keyword fallback that marks its answer `success: True` (`_direct_tool_fallback`, `agent.py:147-230`).
- **Failures that look like success.**
  - L28: constants 0.75 and 0.5.
  - L29: an empty answer counts as 1.0 grounded, and the mock scores 100 %.
  - L30: fallbacks are not counted as errors.
  - L31: errors are reported as COMPLETED.
  - L32: early stops are reported as "max iterations".
- **Tokens are whitespace word counts** (L30 `rag_service.py:140,169,182`; L31 `reasoning_engine.py:83`), and L30's cost comes from a guessed price (`rag_service.py:186`).
- **Latency statistics you cannot trust.** L29 reports fixed sleeps as stage latency and takes P99 from 9 samples. L30 pools all stages into one percentile.
- **Toy corpora and no retrieval evaluation.** L28 and L30 each use five one-sentence documents. No lesson in this block measures retrieval: no recall@k, no chunk ids in traces. No lesson offers retrieval as a tool inside a loop. L28's RAG is a single routed branch, and L32's only knowledge tool is a Wikipedia title lookup.
- **Synchronous LLM or encoder calls inside async FastAPI routes** block the server (L29 `agent_service.py:35` when a key is set, L30 `rag_service.py:99`, L32 `app.py:114`).
- **Repeated demo tools:** `eval`-based calculators (L28 `tools/calculator.py:38`, L32 `tools.py:148`) and mock weather, database and stock tools. Both calculators let `**` through (L28 `tool_equipped_agent.py:171,186`, L32 `tools.py:141`), so one huge power can freeze the server.
- **Citations and provenance are never checked.** L28 asks for citations but returns every chunk in the context as a "source" (`rag/engine.py:110,127-132`). L30 drops the chunk ids (`rag_service.py:117-133`). L32's Wikipedia observation has no URL (`tools.py:63`). No lesson checks that a cited source was actually retrieved.
- **The LLM grades itself.** L28's judge is the generator model (`evaluator.py:60,84`). L31's confidence is the model's own number (`reasoning_engine.py:139`). L29 and L30 have no judge at all.
- **Tests are import checks or curl smoke tests.** The only unit tests (L29) cover two happy paths.
- **Unused pinned dependencies:** L28 ragas, datasets, redis, duckduckgo-search. L30 prometheus-client, python-json-logger and the PyPI `asyncio`. L31 python-jose and aiofiles (`requirements.txt:7-8`).
- **Docs refer to files and paths that do not exist:** a `setup.sh` (L29 `README.md:9`, L30 `SETUP_AND_RUN.md:5`) and the author's home folder (L30 `SETUP_AND_RUN.md:28`, L32 `API_KEY_SETUP.md:17`).
