# VAI lessons 33–38: Reflexion, loop budgets, "agentic RAG", planner, retriever + reranker, validator

[← Guide index](README.md) · Course folder: `C:\Yash\New-Work\RAG\vertical-ai-agents-main\` · Checked 2026-10-17 · Log: [verification/L33-L38_agentic_rag_parts_log.md](verification/L33-L38_agentic_rag_parts_log.md)

**What this is:** the guide to VAI lessons 33–38: Reflexion, loop budgets, a so-called agentic RAG, a planner, a retriever + reranker and a validator.
**What this is not:** the course code, or a run of it. Nothing in the course was run or copied.

**How to read this file:**
- A `file:line` is relative to the project folder named in the lesson heading.
- **UNVERIFIED** marks behaviour that depends on a library version or on Gemini.
- **(counter)** or † means the lesson names a technique without building it. Read it to learn what is missing.
- Tags: **[bug]** the code does the wrong thing · **[misleading]** a label, message or number claims more than the code does · **[shallow]** it works, but is too thin for your project · **[ok-for-demo]** fine for a demo, not for real use · **[LLMOps]** material for your LLMOps notebooks · **[Interview]** worth practising for interviews.
- "I" means the reviewer who checked the code. Each lesson was checked by a reader, a fact-check pass and a completeness pass; the log has every verdict.

**Notes for this block:**
- Only lesson33 has a `setup.sh`; lessons 34–38 ship only the generated project folder.
- A4 in your plan means user-feedback loops, so it is not mapped to the self-critique loops here.

---

## L33 · Reflexion agent: critique-and-retry loop  (`lesson33/l33-reflexion-agent/`)

**What the code teaches, in one line:** A ReAct step runs one tool. A keyword check decides whether it "failed". On failure, a second Gemini call writes a critique and a "next strategy", and the next attempt's prompt carries that critique.
**What it is not:** Not RAG (nothing is retrieved), not Self-RAG (no reflection tokens, no relevance or support grading), and not task-level success checking. The "evaluator" is a substring test on the raw tool output, not an LLM judge.
**Relevance to your RAG study:** Medium (as a pattern only) — concepts: A5 (act → check → reflect → retry loop, with no retrieval), A2/A3 (shape only: nothing is retrieved or graded), M3 (counter-example: a keyword "evaluator"), D2 (retry/backoff) [Interview]. Not A4: in your curriculum A4 means loops driven by *user feedback* (Ch17), and this lesson has none.
**Stack:** FastAPI, `google-generativeai==0.8.3` (`requirements.txt:1`). Actor model `gemini-2.5-flash` via `GEMINI_MODEL_MAIN` (`backend/react_agent.py:47`); critic model `gemini-2.5-flash` via `GEMINI_MODEL_REFLECT` (`backend/reflection_engine.py:39`). No embeddings, no vector store. `redis` is listed (`requirements.txt:6`) but never imported. The React dashboard shows the result, the attempt count, each reflection with a confidence bar, and session "success rate" and "avg confidence" tiles (`frontend/src/components/ReflexionDashboard.js:186-260`).
**Swap to your stack:** easy. There are only two `generate_content` calls (`backend/react_agent.py:73`, `backend/reflection_engine.py:71`). Swap them for Groq chat calls with `reasoning_effort="low"` and a generous `max_tokens`. Do not copy the critic's 500-token cap (`backend/reflection_engine.py:75`). On a reasoning model the hidden reasoning probably counts against that cap, so the four labelled lines could get cut off (UNVERIFIED: check one cached Groq response).

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/reflexion_agent.py` | The outer loop: attempt, check, fail-fast, reflect, store | `66-171`, `_is_success` `225-253` |
| 2 | `backend/reflection_engine.py` | Critic prompt, parser, in-memory reflection store | prompt `11-33`, parse `108-133`, memory `135-171` |
| 3 | `backend/react_agent.py` | One ReAct step: prompt, regex-parse the first `Action:`, run the tool | `11-30`, `51-92`, `104-110`, `117-140` |
| 4 | `backend/tools.py` | Fake tools that fail at random | `13-14`, `16-25`, `43-44` |
| 5 | `backend/api.py` | `/api/execute` endpoint around one global agent | `42`, `56-80` |
| 6 | `tests/test_reflexion.py` | Tests with weak asserts (live API only if a key is exported) | `52-83` |

### How it works, step by step
1. The dashboard POSTs `{task, session_id}` to `/api/execute`. After the first answer it sends back the `session_id` it received (`frontend/src/components/ReflexionDashboard.js:49-55`). The endpoint is `async def` but calls the synchronous `agent.run`, which blocks the server while it runs (`backend/api.py:56-65`).
2. `run()` clears the ReAct history and loops while `attempts < max_reflections`. That cap is hard-coded to 4 (`backend/api.py:42`), so `MAX_REFLECTIONS=3` in the generated `.env` (`../setup.sh:55`) is ignored (`backend/reflexion_agent.py:43,66`).
3. Each attempt calls `step()`. The prompt holds the tool list, the task, the latest reflection only (critique plus next strategy, `backend/react_agent.py:104-110`) and the last 6 history lines (`:69-70`). There is no generation config, so the model's default temperature applies (`:73`).
4. A regex takes the first `Action:` line (`backend/react_agent.py:117-120`). A second regex splits it into tool name and argument; quotes are stripped and the tool is called with one string (`:122-140`). If the model wrote only `Final Answer:` with no `Action:`, the step returns an error string (`:78-79`). The `Final Answer` itself is never used.
5. Success is decided by `_is_success` (`backend/reflexion_agent.py:225-253`). It fails if the observation contains any of `error`, `failed`, `exception`, `invalid`, `not found` or `unavailable`, or if it is shorter than 10 characters. Anything else counts as success, and the raw tool output is returned as the result (`:80-88`). The `task` argument is accepted but never used (`:225`, `:251-253`), so the check never asks whether the output answers the question.
6. Before reflecting, it fails fast on API-key and model-not-found errors (`:91-120`). On a quota error it sleeps up to 60 s and retries once (`:123-149`, `:218-223`); that retry does not count as an attempt. The quota test is a substring match that includes `rate limit` (`:207-216`), so the fake search tool's random "rate limit exceeded" error (`backend/tools.py:14`) also lands here. That message does not match the `retry in Ns` pattern, so the agent sleeps the default 6 s (`:223`). If the retry fails the same way, it returns `QUOTA_EXCEEDED` with a message about the Gemini free tier (`:136-149`), which is the wrong diagnosis.
7. On failure, `ReflectionEngine.reflect()` sends the task, action, observation and the last 3 reflections (`backend/reflection_engine.py:93-106`) to the critic at temperature 0.3 with `max_output_tokens=500` (`:70-77`). It asks for four labelled lines: SUCCESS, CRITIQUE, NEXT_STRATEGY and CONFIDENCE (`:28-32`).
8. The parser reads those lines one by one (`:108-133`). Only the first line of a multi-line critique survives (`:122-123`). The reflection, the action and a 200-character slice of the observation are stored per session in a plain dict (`backend/reflexion_agent.py:161-167`, `backend/reflection_engine.py:135-149`).
9. The loop repeats. After the last attempt fails it still makes one more critic call, whose advice is never used, then returns `MAX_REFLECTIONS_EXCEEDED` (`backend/reflexion_agent.py:173-185`).

### README vs code
- README says "LLM-powered critique" (`README.md:31`). True: the critic is a real Gemini call. But the critic's own `SUCCESS` verdict never steers the loop. Only the keyword heuristic does (`backend/reflexion_agent.py:80`).
- README says "Reflection memory across attempts" (`README.md:32`). True, but memory is keyed by session, and the UI reuses one session for every task you type (`frontend/src/components/ReflexionDashboard.js:51,55`). Reflections from task A are injected into task B's first prompt (`backend/reflexion_agent.py:71-74`).
- README says "Production-ready error recovery" (`README.md:34`). The code has fail-fast plus one backoff retry on the error strings above, all in-process, and a `time.sleep` that blocks every request (`backend/reflexion_agent.py:126`).
- The README's example task, "Find the CEO of Anthropic" (`README.md:53`), only reaches the canned answer if the query contains the exact substring `ceo anthropic` (`backend/tools.py:16`). Most phrasings fall through to the placeholder string (`:25`), and that placeholder passes as success.

### Where it is thin or wrong
- [bug] `"Calculate 5 + 3"` (the test task, `tests/test_reflexion.py:57`) returns `Result: 8`, which is 9 characters. The rule `if len(observation.strip()) < 10` (`backend/reflexion_agent.py:248`) marks it a failure, so the agent reflects on a correct answer and retries. It keeps failing until it runs out of attempts, unless the model happens to change its action (for example, `5.0 + 3` gives `Result: 8.0`, 11 characters, which passes).
- [bug] `No Wikipedia article found for ...` (`backend/tools.py:57`) does not contain the substring `not found`, so a failed lookup counts as success. Meanwhile any real answer that happens to contain the word "invalid" counts as failure (`backend/reflexion_agent.py:232-245`).
- [misleading] Many "failures" are injected at random: 20% for search and 15% for Wikipedia (`backend/tools.py:13,43`). The Wikipedia one goes straight to the critic, which then writes a "strategy" for what was really a coin flip. The search one first takes the quota-retry path (step 6). No random seed is set anywhere, so two runs of the same task cannot be compared or replayed (M4).
- [shallow] Each attempt runs exactly **one** tool call. Only the first `Action:` line is executed (`backend/react_agent.py:117-120`), and the first observation that passes the check becomes the final result (`backend/reflexion_agent.py:80-88`). A two-step task ("look X up, then compute Y") can never be finished. The "ReAct loop" is a single act step that is retried.
- [bug] The critic's verdict is parsed with `'true' in line.lower()` (`backend/reflection_engine.py:120-121`). A critic that echoes the template `SUCCESS: [true/false]` counts as true, and so does "not true". That feeds the "Success Rate" tile below.
- [misleading] The dashboard's "Success Rate" is the share of reflections where the critic said `SUCCESS: true` (`backend/reflection_engine.py:162-170`). Reflections only run after failures, so this tile measures how often the critic disagreed with the heuristic, not task success. When a session has no reflections yet, the tile shows 100% or 0% from the task result instead (`frontend/src/components/ReflexionDashboard.js:200-202`).
- [shallow] "Confidence" is the critic's self-reported number (`backend/reflection_engine.py:126-131`), which is uncalibrated.
- [bug] (latent) One global agent instance holds `history` and `current_session_id` for all users (`backend/api.py:42`, `backend/react_agent.py:49`, `backend/reflexion_agent.py:44`). Today the blocking endpoint makes requests run one at a time, so they do not interleave. It becomes a real race as soon as you make the endpoint non-blocking (for example a plain `def` endpoint, which FastAPI runs in a thread pool).
- [ok-for-demo] The calculator `eval`s input after a character whitelist (`backend/tools.py:31-35`). Acceptable for a toy.

### Tests and data
- `tests/test_reflexion.py` does not load `.env` (it imports the backend without `load_dotenv`, and `scripts/test.sh:7` just runs pytest). Unless `GEMINI_API_KEY` is exported in your shell, every Gemini call fails. Those failures are caught and turned into error strings or a fallback reflection (`backend/react_agent.py:91-92`, `backend/reflection_engine.py:83-91`), so the tests most likely still pass without ever reaching Gemini (UNVERIFIED: depends on where the library raises).
- The asserts only check that keys exist and that `attempts <= max` (`:26-29`, `:59-61`, `:71`, `:79-83`). They would pass even with the 9-character bug above. There are no quality checks.
- No data files. The tools return canned strings.

### What to take for your project
- The **shape** (A2/A3): evaluator → verbal critique → store → condition the next attempt. In `ragkit`, put a real evaluator where `_is_success` sits, for example a relevance grade on retrieved chunks (A2) or a groundedness check on the answer (V2). Keep the critique in a short list that is injected into the next query rewrite.
- The lesson to take is the anti-pattern: **if the evaluator is wrong, reflection makes things worse.** Build and test the evaluator first (M3).
- Fail-fast categories (auth and model errors never retry; 429 backs off) are a good habit for your Groq/Cohere cached-call layer (D2). Match on the provider's status code, not on words in the text: this lesson's substring match mistakes a tool's error for a provider quota error.
- If you build a critic (Phase 10, after the gates), run it on Groq `openai/gpt-oss-20b` with `reasoning_effort="low"`. Cache every critic call in your record/replay layer, keyed by prompt version, model id and an input hash, so a rerun replays without credits. Ask for the verdict as JSON with a boolean field instead of parsing labelled lines. Keep book text out of the critic prompt.

### Try this
- (20 min) In a scratch file in your own workspace, re-write the logic of `_is_success` yourself: a list of six error words and a length check (`backend/reflexion_agent.py:232-249`). Feed it these 8 strings: `Result: 8`, `Result: 12`, the Wikipedia "No ... article found" message, the search placeholder, the rate-limit message, `Dario Amodei is the CEO...`, `The input was invalid but here is the answer...`, and an empty string. Write down pass/fail before you run it. Then count how many verdicts match what a human would say. That count is your evaluator's accuracy, and it caps how much reflection can help.

### Interview angle
- **Q:** "How is Reflexion different from just retrying?" **A:** A plain retry sends the same prompt again. Reflexion first turns the failure into a written lesson, stores it, and conditions the next attempt on it. It only helps if the success signal is reliable; a bad evaluator makes the agent "fix" correct answers.

---

## L34 · Planning-loop controls: iteration and token budgets  (`lesson34/l34-planning-loop-controls/`)

**What the code teaches, in one line:** It wraps a plan → act → reflect loop in a `BudgetManager` that counts LLM calls and estimated tokens, and raises an exception when a cap is hit. The exception is caught, and a "partial result" message is returned.
**What it is not:** Not a real cost or latency budget. Tokens are guessed as characters ÷ 4, there are no dollars, no wall-clock timeout and no pre-call check. Not a circuit breaker either: no budget state survives across requests.
**Relevance to your RAG study:** Medium — concepts: D2 (budgets), A5 (a bounded loop with steps and tokens counted per run), D1 (per-step token history) [LLMOps] [Interview]. Not A4 (no user feedback).
**Stack:** FastAPI, `google-generativeai==0.3.2` (`backend/requirements.txt:4`). Model `gemini-1.5-flash` (`backend/app/gemini_client.py:16`), an old id that may no longer be served (UNVERIFIED). The mock fallback is silent (`:9-18`, `:36-44`). No retrieval. The React dashboard shows the policy cards (`frontend/src/components/PolicyViewer.js`), a run form (`frontend/src/components/AgentExecutor.js`) and a chart of iterations and tokens (`frontend/src/components/MetricsDashboard.js:5-82`).
**Swap to your stack:** easy. `GeminiClient.generate` is the only LLM seam (`backend/app/gemini_client.py:34-44`). Groq responses also return real usage counts, which you should record instead of `len//4`.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/app/budget_manager.py` | Counters, exceptions, `check_limits` | `16-54` |
| 2 | `backend/app/execution_controller.py` | Plan/act/reflect loop, stop rule, graceful-degradation message | `21-46`, `141-150`, `174-182` |
| 3 | `backend/app/gemini_client.py` | Gemini call, token estimate, silent mock | `7-48` |
| 4 | `backend/main.py` | Loads a policy JSON, overrides, metrics store | `43-127` |
| 5 | `config/*_policy.json` | dev 50/500k, staging 20/100k, prod 10/50k | `:2-4` each |

### How it works, step by step
1. `POST /api/agent/execute` with `{task, environment}`. The `environment` string goes straight into the file path for the policy JSON (`backend/main.py:48`). Optional `max_iterations` and `max_tokens` override it (`:52-55`). Every request gets a new `GeminiClient` and agent (`:58-59`).
2. `BudgetedReflexionAgent.run` loops until the reflection text says "COMPLETE" (`backend/app/execution_controller.py:24`, `:39-40`, `:141-150`).
3. Plan: the prompt holds the task and the last 3 steps, each cut to 100 characters (`:128-139`). It asks for JSON with thought, reasoning, action and action_input (`:52-64`). If `json.loads` fails (for example when the model wraps the JSON in code fences, which this code does not strip), the action silently becomes `analyze(task)` (`:73-80`).
4. Act: the tools are fakes. Search returns a fixed sentence, calculate is a bare `eval`, and analyze reports the character count (`:112-126`).
5. Reflect: a second call asks whether the step helped and to answer CONTINUE or COMPLETE (`:93-101`).
6. Each LLM call runs `record_llm_call`. It adds estimated tokens (`len(prompt)//4` plus `len(text)//4`, `backend/app/gemini_client.py:40-41`), adds **1 to the iteration count** (`backend/app/budget_manager.py:42`), and then checks the limits (`:54`). The check raises if `current_iteration >= max_iterations` or `tokens_used >= max_tokens` (`:27-36`).
7. When the loop ends, a synthesis call writes the "Final Answer" (`backend/app/execution_controller.py:152-172`). If a budget exception fires anywhere, `run` catches it and returns a sentence like "Task interrupted ... Completed N steps" (`:44-46`, `:174-182`).
8. `main.py` stores the metrics and returns `success=True` (`backend/main.py:62-79`).

### README vs code
- README: "Token-per-turn budgets" (`README.md:38`). The cap is cumulative per request; the name `max_tokens_per_turn` is wrong (`backend/app/budget_manager.py:21,41`).
- README: dev and staging run in "warn mode", prod in "strict mode" (`README.md:53-55`). `enforcement_mode` is never read by the backend. Only the policy viewer displays it (`frontend/src/components/PolicyViewer.js:29`). Every environment is strict.
- README: "cost monitoring" (`README.md:3`). There are no prices or dollars, only estimated tokens.
- README: "Exception-based circuit breakers" (`README.md:40`). These are per-request exceptions, not a breaker that opens after repeated failures.
- README: L35 "will use these budget controls" (`README.md:84`). L35 re-implements its own allocator instead (see L35).

### Where it is thin or wrong
- [bug] `BudgetException` is caught inside `agent.run` (`backend/app/execution_controller.py:44-46`), so the handler in `main.py` (`backend/main.py:81-98`) can never run. Every budget hit is returned as `success=True` (`:73-79`), and the summary's `budget_violations` / `violation_rate` (`:119-126`) is always 0.
- [bug] The check runs **after** the call has been paid for, and "iteration" means "LLM call", not "loop" (`backend/app/budget_manager.py:42,54`). With the prod cap of 10, a loop that never says COMPLETE makes 10 calls (5 plan + 5 reflect). The 10th call raises, its output is thrown away, and synthesis never runs. You pay for 10 calls and get back only "Completed 4 steps" and the last action name.
- [bug] The stop rule is a substring test (`backend/app/execution_controller.py:144,150`). "INCOMPLETE" matches, and so does a reply that just repeats the prompt's "CONTINUE or COMPLETE".
- [misleading] With no key or any API error, the client falls back to a mock without saying so (`backend/app/gemini_client.py:12-18`, `:36-37`, `:43-44`). The mock reflection always says COMPLETE (`:24`), so every run shows 3 "iterations" and a canned "completed successfully" answer (`:26`). `main.py` never loads `.env`; `python-dotenv` is installed but unused (`backend/requirements.txt:6`). The key only arrives if it is already exported in your shell or passed in by Docker (`scripts/start.sh:38`, `docker-compose.yml:11`). The UI gives no sign of which path ran.
- [bug] `eval` runs on LLM-chosen input with no whitelist (`backend/app/execution_controller.py:119`), which is a code-execution hole (D4). The `environment` string also lets the path escape `config/` (`backend/main.py:48`), but only to files whose names end in `_policy.json`, so that risk is small.
- [shallow] The token estimate is `len//4` (`backend/app/gemini_client.py:22,40-41`). The derived metrics `token_utilization` and `tokens_per_second` (`backend/app/budget_manager.py:65-68`) inherit that guess, so the dashboard chart plots estimates as if they were measured. `is_approaching_limit` is never called (`backend/app/budget_manager.py:72-77`). The "async" client is synchronous (`backend/app/gemini_client.py:46-48`). No call sets an output cap, so one long reply can overshoot the token budget by any amount before the after-call check runs (`backend/app/gemini_client.py:39`).

### Tests and data
- `scripts/test.sh` is a curl smoke test against a running server: health, policies, one execute, summary (`:17-43`). It only checks that each `curl -f` call gets a non-error HTTP status. There are no unit tests for the budget logic.
- The policy JSONs (`config/`) are a neat idea for environment-specific caps. There is no other data.

### What to take for your project
- **Re-implement in plain Python (D2):** a `Budget` object with `max_calls`, `max_tokens`, `max_seconds` and `max_usd`. Check **before** each call (estimated prompt tokens plus `max_tokens` against what is left). Record the **real** usage from the Groq or Cohere response. Return the best partial answer, not just a step count.
- With `openai/gpt-oss-20b`, the reasoning tokens are probably billed as output. Leave room for them in `max_tokens` and in the budget (UNVERIFIED: read the usage fields of one cached Groq response before you trust the field names).
- Make the budget work with your record/replay cache. A replayed call costs nothing now, but store its original usage in the cache entry and charge that to the budget. A replayed run then hits the same caps a live run would.
- Keep the idea of per-step token history (`backend/app/budget_manager.py:44-51`) as a trace field in your LLMOps notebook (D1).
- Skip the loop itself; the agent does nothing real.

### Try this
- (15 min, paper) Use the prod policy (10 calls) and a model that never says COMPLETE. Trace the calls through `execution_controller.py` and `budget_manager.py`. How many calls are paid? What does the user see? What does `/api/metrics/summary` report? Then write down where you would move the check so the last paid call is never wasted.

### Interview angle
- **Q:** "How do you stop an agent loop from running up cost?" **A:** Put hard caps on steps, tokens, wall-clock time and dollars. Check them before each call, using real usage numbers, and always return a partial answer. Budget hits should also be counted as real failures in monitoring; this lesson hides them behind `success=True`.

---

## L35 · "Agentic RAG" orchestrator (Planner → Retriever → Validator → Synthesizer)  (`lesson35/l35-agentic-rag/`)

**What the code teaches, in one line:** A fixed four-stage pipeline with a state machine (`PipelineStage`), per-stage token allocations and WebSocket stage updates. Only the last stage calls an LLM.
**What it is not:** Not agentic RAG. No agent decides **whether**, **what** or **when** to retrieve; there is no loop, no retry and no routing. The planner returns a hard-coded plan, the retriever returns the same 3 hard-coded documents for every query, and the validator averages hard-coded "relevance" numbers.
**Relevance to your RAG study:** Low — concepts: A5 and A1 (as a **counter-example**), V2 (counter-example: the "validator" averages constants), D2 (budget split), C5 (synth prompt with `[Source: …]`) [Interview]
**Stack:** FastAPI with WebSocket, `google-generativeai==0.8.3` (`backend/requirements.txt:4`). Model `gemini-2.0-flash-exp`, an experimental id, is set in planner, validator and synthesizer (`backend/agents/planner_agent.py:10`, `validator_agent.py:10`, `synthesizer_agent.py:10`), but only the synthesizer calls it (`synthesizer_agent.py:31`). No embeddings, no vector store. The Vite/React UI shows a stage progress bar, the documents, the validation scores, the response and token totals (`frontend/src/App.jsx:20-55`, `:330-345`).
**Swap to your stack:** easy. One call to replace (`backend/agents/synthesizer_agent.py:31`), but there is little worth swapping.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/services/orchestrator.py` | Linear 4-stage pipeline with stage updates | `40-139` |
| 2 | `backend/services/budget_manager.py` | 30/20/15/35 token split; unused iteration controller | `6-11`, `14-23`, `43-61` |
| 3 | `backend/agents/retriever_agent.py` | Three hard-coded docs with fixed relevance | `10-29`, `31-58` |
| 4 | `backend/agents/validator_agent.py` | Mean of fixed relevance ≥ 0.7 | `13-54` |
| 5 | `backend/agents/synthesizer_agent.py` | The only real LLM call; mock fallback | `12-77` |
| 6 | `backend/agents/planner_agent.py` | Mock plan ("L36 will implement") | `12-40` |

### How it works, step by step
1. `POST /query` builds a new `RAGOrchestrator` with `max_tokens` (default 3000, `backend/main.py:25`) (`:35-41`). The WebSocket path does the same and pushes every state change to the client (`:50-75`, `backend/services/orchestrator.py:30-38`).
2. Budget split: planner 30%, retriever 20%, validator 15%, synthesizer 35% (`backend/services/budget_manager.py:6-11`).
3. Planning: the "token cost" is query words × 10 (`backend/agents/planner_agent.py:16`). The plan is always `sub_queries=[query]`, 3 docs, strategy "semantic" (`:27-33`). No LLM is called.
4. Retrieval: it sleeps 0.5 s to look busy (`backend/agents/retriever_agent.py:38`), then returns the first `estimated_docs_needed` items of the same 3-doc list, whatever the query is (`:47`). Each item carries fixed `relevance` values of 0.95, 0.92 and 0.88 (`:15,21,27`).
5. Validation: it averages those fixed relevance values. The mean is about 0.92, which is ≥ 0.7, so validation always passes (`backend/agents/validator_agent.py:30-41`). If validation failed, the pipeline would stop with FAILED; there is no corrective retry (`backend/services/orchestrator.py:94-99`).
6. Synthesis: the prompt asks for an answer with `[Source: filename]` citations over the 3 docs (`backend/agents/synthesizer_agent.py:21-29`). Tokens are counted as prompt words plus response words (`:34`). The budget check comes after the call has already been paid for (`:36-41`).
7. Done: stage COMPLETED, plus a budget summary and `iterations_used` (`backend/services/orchestrator.py:126-131`).

### README vs code
- README: "PlannerAgent: Analyzes queries, creates retrieval plans" (`README.md:22`). It returns a constant plan (`backend/agents/planner_agent.py:25-33`).
- README: "RetrieverAgent: Executes document searches" (`README.md:23`). It runs no search; it slices a constant list (`backend/agents/retriever_agent.py:47`).
- README: "ValidatorAgent: Scores factual consistency" (`README.md:24`). It averages fixed numbers, and no consistency check happens (`backend/agents/validator_agent.py:16-41`).
- README: "SynthesizerAgent: Generates responses with citations" (`README.md:25`). Partly true. The returned `citations` field is simply every document's source, not what the answer cited (`backend/agents/synthesizer_agent.py:47`), and the orchestrator drops it anyway (`backend/services/orchestrator.py:122`).

### Where it is thin or wrong
- [misleading] The synthesizer's fallback on any API error (an expired key, a retired `-exp` model) returns `success=True` with a templated "answer" (`backend/agents/synthesizer_agent.py:57-77`). The text does end with an `[API fallback - error: ...]` note (`:66`), but the stage still shows COMPLETED. The fallback also reports `tokens_used=min(tokens_used, budget_available)` (`:75`). Its token count is clamped to the budget, so it can never look over budget.
- [misleading] The numbers the UI shows as measurements are constants. Each document shows "Relevance: 0.95 / 0.92 / 0.88" (`frontend/src/App.jsx:434`), and the validation panel shows "Confidence: 91.7%" for every query (`frontend/src/App.jsx:453`). Both come from the hard-coded list (`backend/agents/retriever_agent.py:15,21,27`). The plan's `retrieval_strategy` is labelled "semantic" (`backend/agents/planner_agent.py:32`), but no embedding or search exists anywhere in this lesson.
- [bug] The return value of `budget.reserve()` is ignored at every stage (`backend/services/orchestrator.py:63,82,103,124`). Each agent does its own check against `get_remaining` (`backend/agents/planner_agent.py:18`, `retriever_agent.py:43`, `synthesizer_agent.py:36`), so the stage caps are partly enforced. But when `reserve()` refuses, nothing is added to `used` (`backend/services/budget_manager.py:19-23`), so the budget summary under-reports that stage.
- [bug] When the retriever's budget is short (below 60, i.e. `max_tokens` under 300) it trims the documents but still reports the full token count (`backend/agents/retriever_agent.py:41-47`). If `budget // 20` is 0 (`max_tokens` under 100) it returns no documents, and the validator then fails with "No documents" (`backend/agents/validator_agent.py:23-28`). At budgets that small the planner's own check usually fails first (`backend/agents/planner_agent.py:16-23`).
- [misleading] `IterationController` is never advanced (`next_iteration` is never called), so `iterations_used` is always 0 (`backend/services/budget_manager.py:43-61`, `backend/services/orchestrator.py:130`).
- [shallow] All token numbers are guesses: word counts in the planner and synthesizer (`backend/agents/planner_agent.py:16`, `synthesizer_agent.py:34`) and fixed per-document constants in the retriever (20) and validator (15) (`retriever_agent.py:41`, `validator_agent.py:43`).
- [ok-for-demo] The global `orchestrator` at `backend/main.py:21` is never used.

### Tests and data
- `backend/tests/test_pipeline.py` mocks the synthesizer (`:12-36`). Everything else is already constant, so the four tests check constants: COMPLETED, docs > 0, tokens ≤ budget, confidence ≥ 0.7 (`:39-77`). The tests use `@pytest.mark.asyncio`, but `pytest-asyncio` is not in `backend/requirements.txt`, and `test.sh` installs nothing extra (`test.sh:9-19`). Without the plugin, pytest does not run async tests as written (pytest 8 skips them with a warning; exact behaviour UNVERIFIED here).
- `test_budget_enforcement` **cannot fail** (`backend/tests/test_pipeline.py:50-56`). It only asserts `total_tokens <= 500`. If any stage refuses for lack of budget, the pipeline stops with FAILED and a *smaller* total (`backend/services/orchestrator.py:55-59`), and that still passes. The test never checks the stage. Its mock synthesizer also clamps its tokens to the budget (`backend/tests/test_pipeline.py:24`).
- Data: three one-line strings. Not usable as practice data.

### What to take for your project
- Skip the code. Take the **definition test** instead. A system is agentic RAG only if the model chooses among actions (retrieve or not, which tool or index, rewrite and retry, stop) based on what it sees. Use this lesson as the "fixed pipeline" baseline when you explain A5.
- One small idea for D2: a **per-stage token allocation**, set beside your eval budget and checked before each call.

### Try this
- (20 min, design) Redraw `orchestrator.process_query` as a loop with three decision points. (1) After planning: is retrieval needed at all (A1)? (2) After retrieval: are the chunks relevant enough, and if not, rewrite the query and retrieve again, at most N times (A2)? (3) After synthesis: is every claim supported, and if not, re-retrieve or abstain (V2/V3)? For each one, name the signal you would use in `ragkit` and the cap that bounds it.

### Interview angle
- **Q:** "What makes RAG *agentic*, and when is it worth it?" **A:** A model decides whether to retrieve, what to search for, and whether the evidence is good enough to stop or must be fetched again, inside a bounded loop. A fixed chain of "agents" is only a pipeline with role names. It is worth the extra latency and cost only for multi-hop or ambiguous questions.

---

## L36 · Planner agent: LLM query decomposition  (`lesson36/l36-planner-agent/`)

**What the code teaches, in one line:** One Gemini call turns a question into 1–5 sub-queries with a rationale, a parallel or sequential strategy, and a complexity label. Pydantic validates the result, and any failure falls back to the original query.
**What it is not:** Not end-to-end decomposition RAG. Nothing executes the sub-queries, honours `requires_previous`, or merges results. That half lives in L37, and only partly.
**Relevance to your RAG study:** Medium — concepts: Q1 (decomposition), A1 (weak: the `requires_decomposition` flag is a tiny yes/no router, but nothing acts on it) [Interview]
**Stack:** FastAPI, `google-generativeai==0.8.3`, `pydantic==2.9.2` (`backend/requirements.txt:1-4`). Model `gemini-2.0-flash-exp` (`backend/app/planner.py:43`); the README calls it "Gemini 2.0 Flash" (`README.md:28`). No retrieval. The React UI shows the sub-query cards with their rationale, a "depends on previous" badge, the strategy badge and a metrics panel polled every 5 s (`frontend/src/App.js:25-38`, `:185-220`).
**Swap to your stack:** easy. One call (`backend/app/planner.py:87-94`). With Groq, ask for JSON output (check JSON-mode support for `openai/gpt-oss-20b`) and keep the Pydantic check.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/app/planner.py` | Prompt, timeout, fence-stripping parser, fallback | `12-36`, `47-85`, `96-128`, `130-145` |
| 2 | `backend/app/models.py` | `SubQuery` / `QueryPlan` constraints | `6-31` |
| 3 | `backend/app/main.py` | `/plan`, in-memory metrics | `53-104` |
| 4 | `backend/tests/test_planner.py` | Tests written so that fallback passes | `12-50` |

### How it works, step by step
1. `POST /plan {query, max_sub_queries}`. `max_sub_queries` may range from 1 to 10 (`backend/app/models.py:24`). The server refuses to start without `GEMINI_API_KEY` (`backend/app/main.py:38-40`).
2. Prompt, paraphrased (`backend/app/planner.py:12-36`): you are a query-planning expert. Return exactly this JSON. A simple, single-concept question gets `requires_decomposition=false` and one sub-query equal to the original. Comparisons and multi-concept analysis get decomposed. Each sub-query must be independently searchable. Use "parallel" unless there are dependencies. Complexity is low for 1 concept, medium for 2–3, high for 4+.
3. The call runs in a thread executor with a 5 s `asyncio.wait_for` timeout (`:41`, `:60-63`, `:87-94`). On timeout the request falls back, but the thread keeps running and the Gemini request still completes, so you most likely still pay for it (billing UNVERIFIED). The call passes only the prompt: no temperature, no JSON mode and no output cap (`:92`). The "no markdown" instruction in the prompt is the only guard on the format.
4. Parsing: strip a leading code fence if there is one, `json.loads`, check the 4 required keys (`:96-128`).
5. Pydantic builds `QueryPlan`: each sub-query text is 5–500 characters, each rationale **10–200** characters, at most **5** sub-queries, `strategy` must be exactly the string "parallel" or "sequential", and complexity exactly "low", "medium" or "high" (`backend/app/models.py:8-18`).
6. Any exception, including a Pydantic validation error, triggers `_fallback_plan`: one sub-query equal to the original text, with a rationale saying decomposition failed (`backend/app/planner.py:80-85`, `:130-145`).
7. `main.py` counts the request as a successful decomposition and returns the plan with its latency (`backend/app/main.py:59-75`).

### README vs code
- README: "Structured JSON validation with Pydantic" (`README.md:33`). True (`backend/app/models.py:6-19`). But a failed validation silently becomes the fallback plan instead of being reported.
- README: "Parallel vs sequential strategy planning" (`README.md:34`). The label is produced, but nothing ever executes in parallel or in sequence.
- README: "timeout protection" (`README.md:37`). True for the HTTP response (5 s), not for cost (see step 3).
- README: complex query "Expected: 3-4 sub-queries with parallel strategy" (`README.md:46-48`). UNVERIFIED; it depends on the live model.

### Where it is thin or wrong
- [bug] The API accepts `max_sub_queries` up to 10 (`backend/app/models.py:24`), but the model caps the list at 5 (`:16`). If you ask for 8 and the LLM obeys, validation fails and you silently get 1 sub-query (`backend/app/planner.py:83-85`).
- [bug] There is no clamp to the requested limit. Ask for 3, get 4 back, and the 4 pass (≤ 5). `test_max_sub_queries_limit` (`backend/tests/test_planner.py:34-42`) would then fail with a live key, and only passes reliably on fallback.
- [bug] A rationale longer than 200 characters, or a `strategy` like "parallel or sequential" (the prompt's own placeholder text, `backend/app/planner.py:23`), also triggers the silent fallback.
- [misleading] The fallback counts as a success: `successful_decompositions` goes up and `success_rate` stays at 100% (`backend/app/main.py:63`, `:103`), because `decompose_query` turns errors into the fallback plan (`backend/app/planner.py:80-85`). The only traces are a log line and the rationale text that the UI shows. (Odd exception: a 3- or 4-character query passes the request check, min 3 (`backend/app/models.py:23`), but the fallback's own `SubQuery` needs at least 5 characters (`:8`). If the main path fails, the fallback itself raises, and that request is counted as failed, `backend/app/main.py:77-87`.)
- [shallow] `requires_decomposition` is not checked against the count (true with 1 sub-query is accepted), and nothing checks that sub-queries stay on topic.

### Tests and data
- The tests build the planner with `"test-key"` when no key is set (`backend/tests/test_planner.py:9`). Every live call then fails and falls back, and the asserts are written so that fallback passes (`:30` comment). `test_fallback_plan` is the only deterministic test (`:44-50`).
- `demo.sh` posts 3 example questions to fill the dashboard (`demo.sh:33-55`). Those questions are reasonable seeds for your own decomposition test set.

### What to take for your project
- **Re-implement (Q1):** a decomposition step in `ragkit` with (a) an explicit "decompose or not" decision, (b) a schema with a **clamp** (truncate to k instead of failing), and (c) **logged** fallbacks with a reason code, so your eval can count them (M5).
- Paraphrase the prompt rules (independently searchable, a dependency flag, a complexity scale). They are a good checklist.
- Build it in plain Python first: one Groq call (`openai/gpt-oss-20b`, `reasoning_effort="low"`, JSON output), then a Pydantic check, all behind your record/replay cache, keyed by prompt version and query. Move to a LangChain or LangGraph planner only after this version is measured.
- One honest metric already exists: `decompositions_with_plan` counts only plans with `requires_decomposition` true and more than one sub-query (`backend/app/main.py:68-69`). The ratio of that count to `total_queries` is a rough signal only, because simple questions also fall outside it on purpose. Log a reason code for each fallback as well, so M5 can count them by cause.
- Pair it with L37's merge step and test both together. Decomposition that is never scored can only add noise.

### Try this
- (25 min) Take 10 questions from your eval set (5 single-hop, 5 comparison or multi-hop). Write the "ideal" sub-queries yourself first. Then run your own Groq version of this prompt and count three things: over-decomposition on single-hop questions, missed decomposition on multi-hop ones, and schema failures. Look for sub-queries that drift away from your PDFs' vocabulary.

### Interview angle
- **Q:** "When should you decompose a query, and how do you combine the results?" **A:** Decompose comparisons and multi-hop questions, not simple lookups, because extra sub-queries add latency and off-topic chunks. Run each sub-query, take the de-duplicated union (or fuse ranks with RRF), then rerank against the **original** question so the final context answers what was actually asked. If one sub-query depends on another's answer (a multi-hop chain), run them in order and put the first answer into the second query. A parallel union cannot do that.

---

## L37 · Retriever agent + reranker: multi-query, hybrid BM25/dense, RRF, LLM rerank  (`lesson37/l37-retriever-reranker/`)

**What the code teaches, in one line:** Decompose the query into 2–4 sub-questions, search each one (dense, or dense+BM25 fused with RRF at k=60), merge and de-duplicate, then have Gemini score every chunk 0–100 against the original query and keep the top-k.
**What it is not:** Not a cross-encoder reranker, despite the README and docstring. The "reranker" is one listwise LLM prompt that returns an array of scores. It is also not a real corpus: 7 hard-coded short chunks of one or two sentences each.
**Relevance to your RAG study:** High — concepts: R3 (LLM listwise rerank; the "cross-encoder" is a counter-example: named, not built), R1 (BM25 + dense + RRF, but the fused rank is thrown away), Q1 (multi-query merge), C4, P3 (BM25 with no stemming), P4 (counter-example: distance shown as similarity), P5 [Interview]
**Stack:** FastAPI, in-memory `chromadb==0.4.24`, `sentence-transformers==2.5.1` with `all-MiniLM-L6-v2` (`backend/vector_store.py:16-18`), `rank-bm25` BM25Okapi (`:86-87`). LLM `gemini-1.5-flash` through `google-generativeai==0.4.0` (`backend/requirements.txt:4`), an old id that may no longer be served (UNVERIFIED), for both planner and reranker (`backend/planner_agent.py:18`, `backend/reranker_tool.py:19`). `redis`, `prometheus-client`, `opentelemetry-*` and `tiktoken` are listed (`backend/requirements.txt:11-16`) but never imported. The React UI has rerank and hybrid toggles and shows sub-queries, chunks with Vector / Rerank / RRF scores, and a metrics panel (`frontend/src/App.js:65-69`, `frontend/src/components/RetrievalResults.js:22-34`).
**Swap to your stack:** moderate. MiniLM is already your fallback embedder. Replace Chroma with your NumPy index, the Gemini planner with Groq, and the Gemini reranker with a real cross-encoder (Cohere Rerank, or a local `sentence_transformers.CrossEncoder`).

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/retriever_agent.py` | Per-sub-query search, merge/dedup, rerank, RRF | `46-97`, `122-164`, `166-181` |
| 2 | `backend/reranker_tool.py` | LLM listwise scoring, batching, fallbacks | `24-90`, `92-152` |
| 3 | `backend/vector_store.py` | 7 docs, Chroma dense search, BM25 | `32-68`, `91-130` |
| 4 | `backend/planner_agent.py` | 2–4 sub-question prompt | `20-48` |
| 5 | `backend/main.py` | `/retrieve` endpoint and request defaults | `49-117` |

### How it works, step by step
1. Startup (the app's `lifespan`, `backend/main.py:30-36`) re-creates a Chroma collection with **7 chunks** (Kubernetes, Docker, RAG, rerankers, FastAPI), embeds them with MiniLM and builds BM25 over regex word tokens (`backend/vector_store.py:22-89`, `:132-134`).
2. `POST /retrieve`. Defaults: `top_k=10`, `use_reranking=True`, `use_hybrid=False` (`backend/main.py:49-53`). The UI always sends `top_k: 10` (`frontend/src/App.js:67`).
3. Planner prompt (paraphrased): break the query into 2–4 focused sub-questions and return a JSON array (`backend/planner_agent.py:23-28`). It **always** asks for decomposition, even for simple questions. If the reply is not a list, or on any error, it returns `[query]` (`:39-41`, `:46-48`). This is its own planner, not L36's, although the README and docstring say "from L36" (`README.md:7`, `backend/planner_agent.py:13`).
4. Each sub-query is searched with `top_k=100` (`backend/retriever_agent.py:48-53`), but Chroma is capped at `min(top_k, 7)` (`backend/vector_store.py:97`). So each sub-query returns **all 7 chunks**. The **original query itself is not searched** unless the planner falls back to `[query]`; otherwise it is only used for reranking.
5. `vector_score = 1 - distance` (`backend/vector_store.py:106`). The collection is created with no distance setting (`:29`), so Chroma's default applies. If that default is squared L2 and MiniLM returns unit-length vectors (both library behaviour, UNVERIFIED here), the score works out to 2·cos − 1, not cosine. The ranking is the same as cosine either way; only the numbers shift.
6. Hybrid mode: run dense and BM25, then fuse with RRF, adding `1/(60+rank)` from each list (`backend/retriever_agent.py:99-164`).
7. Merge: de-duplicate by `hash(content)` and keep the copy with the higher `vector_score` (`:166-181`). So the pool is the union of the sub-query results, scored by the best single sub-query match.
8. Rerank against the **original** query (`:74-80`). The chunks go in batches of up to 50 (`backend/reranker_tool.py:22`), each cut to 500 characters and labelled `[DOC_i]` (`:96-99`). The prompt asks for a 0–100 score per document (0 irrelevant, 50 related, 100 directly answers), returned as a bare JSON array (`:101-112`). Settings: temperature 0, `max_output_tokens=1000` (`:116-123`). If the score count is short it pads with zeros (`:132-135`). Then it sorts and keeps the top-k (`:78-82`).
9. The response carries the chunks, the sub-queries, latency, average vector score and average rerank score (`backend/main.py:96-113`).

### README vs code
- README: "RerankerTool: Cross-encoder semantic scoring" (`README.md:9`), and the class docstring says the same (`backend/reranker_tool.py:13-16`). It is an **LLM listwise scorer**: one prompt over many documents, not a model that reads each (query, doc) pair through a trained relevance head.
- README: "Hybrid search (vector + BM25 + RRF)" (`README.md:25`). RRF uses the standard formula (ranks start at 1, k=60, `backend/retriever_agent.py:127-148`). But the BM25 list keeps every chunk, even those with a BM25 score of 0 (`backend/vector_store.py:117`), so a chunk with no shared word still earns a BM25 rank. And the fused ranking is thrown away (see below).
- README: "Parallel sub-query execution" (`README.md:26`). `asyncio.gather` wraps synchronous MiniLM encoding and Chroma calls (`backend/vector_store.py:93-98`), so the searches run one after another. Only the reranker batches use a thread (`backend/reranker_tool.py:116`), and with 7 chunks and a batch size of 50 (`:22`, `:48-49`) there is only ever one batch, so nothing runs in parallel in practice.
- README: "Graceful fallback on reranker failures" (`README.md:29`). The vector-score fallback in `rerank()` (`backend/reranker_tool.py:87-90`) and in the agent (`backend/retriever_agent.py:83-90`) is practically unreachable, because `_score_batch` swallows every error and returns zeros (`backend/reranker_tool.py:146-152`).

### Where it is thin or wrong
- [bug] **The hybrid toggle has no effect on ranking.** With reranking off, the final sort is by `vector_score`, not `rrf_score` (`backend/retriever_agent.py:92-97`). With reranking on, the LLM re-scores everything anyway. And because every chunk shows up in the dense results (7 ≤ n_results), all chunks carry a `vector_score`.
- [bug] If Gemini fails (bad key, retired id), every chunk gets `rerank_score=0` (`backend/reranker_tool.py:146-152`). The stable sort then keeps merge order, which is the first sub-query's dense ranking (its RRF ranking in hybrid mode). The UI shows "Rerank: 0.0" on every chunk (`frontend/src/components/RetrievalResults.js:27-31`), and the "Reranking Usage" metric still counts the request as reranked (`backend/metrics_collector.py:29,35`).
- [bug] **Merging keeps the wrong fused score.** In hybrid mode each sub-query's list carries its own `rrf_score`. De-duplication keeps the copy with the best `vector_score` and ignores `rrf_score` (`backend/retriever_agent.py:166-181`). Even after you fix the sort, the RRF number you would sort by belongs to whichever sub-query had the best dense match, not to the best fused rank. Fusion across sub-queries never happens.
- [bug] **Scores are matched to chunks by position.** The prompt asks for a bare array "in order" (`backend/reranker_tool.py:111`). If the model skips or merges one document, every later score lands on the wrong chunk. The pad step then gives the *last* chunk a 0 and only logs a warning (`:132-135`). Asking for `{id, score}` objects and joining on the id would make this failure visible.
- [misleading] **Distance is shown as similarity.** `vector_score` is `1 - distance`, with the comment "convert distance to similarity" (`backend/vector_store.py:106`). It is not cosine similarity. Under Chroma's default metric (UNVERIFIED: squared L2) with unit-length MiniLM vectors it works out to 2·cos − 1, which goes negative for weak matches. The UI multiplies it by 100 as if it were a percentage (`frontend/src/components/RetrievalResults.js:22-25`), and `avg_vector_score` averages it (`backend/main.py:102`). The rank order is fine. Any threshold on this number is not.
- [shallow] The BM25 tokenizer is lower-case `\w+` with no stemming and no stop-word list (`backend/vector_store.py:132-134`). "autoscale" does not match "Autoscaler", and "pods" does not match "pod". Words like "to" and "the" count as terms.
- [misleading] There is no real timeout. `timeout_ms=500` is only compared after the work finishes, and it just logs a warning (`backend/reranker_tool.py:29`, `:72-75`).
- [shallow] With 7 docs and `top_k=10`, reranking can only **reorder**, never drop anything (`backend/main.py:51`, `backend/vector_store.py:97`). You cannot see the precision gain that reranking is for.
- [shallow] Planner output is not validated beyond "is it a list" (`backend/planner_agent.py:37-44`). A non-string item makes that sub-query's search fail, and `gather` drops it with only a log line (`backend/retriever_agent.py:55-63`). The response model's `sub_queries: List[str]` (`backend/main.py:58`) would then probably reject the whole reply (UNVERIFIED). The planner call is synchronous inside async code (`backend/planner_agent.py:31`).
- [shallow] A listwise 0–100 prompt is exposed to position bias and score-count drift. The code pads a short score list with zeros, with only a log warning (`backend/reranker_tool.py:132-135`), drops extra scores silently through `zip` (`:139`), and logs nothing about score distributions.
- [ok-for-demo] `asyncio==3.4.3` in requirements (`backend/requirements.txt:13`) is the old PyPI backport; it is pointless on Python 3.12.

### Tests and data
- No tests at all.
- Data: 7 short chunks (`backend/vector_store.py:32-68`). They are too small for retrieval metrics, but useful as a **hand-checkable** toy: you can compute BM25, dense and RRF ranks on paper and compare.

### What to take for your project
- **Re-implement (R1):** RRF fusion as `_reciprocal_rank_fusion` does it (`backend/retriever_agent.py:122-164`), over your BM25 and Cohere-dense lists, with k=60 as the default to tune. Drop zero-score BM25 hits first, and make the fused score the one you sort by.
- **Re-implement (R3):** the two-stage shape: a wide pool (e.g. 50) and then rerank to k (e.g. 5). Use a real cross-encoder (Cohere Rerank or a local CrossEncoder) as the baseline and an LLM 0–100 scorer as a variant. Compare them with your M2 harness (Recall@k before rerank vs nDCG@k after).
- For the LLM-scorer variant on Groq `openai/gpt-oss-20b`: set `reasoning_effort="low"` and a `max_tokens` well above what a bare score list needs, because reasoning tokens probably count against it (UNVERIFIED). Return `{id, score}` pairs and check that every id comes back exactly once. Count a failed parse as "rerank failed" in the trace, never as zeros.
- Cache every Cohere Rerank or Groq rerank call (record/replay), keyed by query, the chunk-id list, model id and prompt version. Only send corpus text you are allowed to send: never book text. For book chunks, use the local CrossEncoder.
- Keep `1 - distance` out of your code. Store the cosine itself (a dot product of normalised vectors in NumPy), name it `cosine`, and use ranks, not raw scores, when you fuse (P4, R1).
- **Re-implement (Q1 merge):** union and de-duplicate across sub-queries, rerank against the original question, and **always include the original query** among the searches.
- Keep the "Vector / Rerank / RRF" per-chunk score display as a trace field idea (D1).

### Try this
- (30 min, paper and toy) Pick the query "how to autoscale kubernetes pods". Assume the planner returned only the original query (its fallback, `backend/planner_agent.py:46-48`), so there is one search list. On the 7 chunks (`backend/vector_store.py:32-68`), rank by BM25 by hand. Split the query and each chunk with the lower-case `\w+` tokenizer (`:132-134`) and mark the exact token matches. Rare words weigh more (IDF), so a match on a word found in one chunk beats a match on a word found in several. You should find that only two chunks share any token with the query. The Cluster Autoscaler chunk scores 0 because there is no stemming, yet it still gets a BM25 rank (`:117`). Then rank the chunks by your intuition for dense search and compute the RRF scores with k=60. Read `retrieve()` with `use_hybrid=True, use_reranking=False` and work out which ranking is actually returned. Then fix it on paper (sort by `rrf_score`), and say what else breaks once there are two sub-queries (the merge step).

### Interview angle
- **Q:** "Bi-encoder vs cross-encoder vs LLM reranker: what is the trade-off?" **A:** A bi-encoder embeds the query and documents separately, which is fast and indexable but coarse. A cross-encoder reads each (query, doc) pair together, which is more precise but needs one forward pass per pair, so you only run it on a small pool. An LLM reranker is the most flexible and the most expensive: it is sensitive to position, prompt and parse errors, and needs a fallback that really falls back.

---

## L38 · Validator agent: pairwise document consistency with an LLM judge  (`lesson38/l38-validator-agent-consistency/`)

**What the code teaches, in one line:** For N retrieved documents, it forms all N·(N−1)/2 pairs and asks Gemini for a consistency score (0–1), a list of contradictions and a confidence for each pair. It caches the pair result in Redis, averages the scores per document into passed (≥ 0.7), warning (≥ 0.5) or failed, and flags pairs below 0.5.
**What it is not:** Not an answer-groundedness or faithfulness check (V2's "is the answer supported by the context"). It compares documents with each other, never with an answer. No NLI model, no claim extraction, and no keyword overlap: the whole judgment comes from an LLM.
**Relevance to your RAG study:** Medium — concepts: V2 (adjacent: a context-conflict check), V4 (judge reliability, fail-open defaults), M3 (LLM-as-judge prompt), D2 (caching) [LLMOps] [Interview]
**Stack:** FastAPI, `pydantic-settings`, `google-generativeai==0.3.2`, `redis` asyncio (`backend/requirements.txt:1-6`). Model `gemini-2.0-flash-exp` (`backend/config/settings.py:10`). No embeddings, no retrieval. `python-jose` and `passlib` are listed (`backend/requirements.txt:8-9`) but never imported. The React dashboard lets you edit documents (pre-filled with three Q3 snippets: two about "revenue", $50M and $48M, and one about "earnings", $50M) and shows overall consistency, per-pair conflicts and a status per document (`frontend/src/components/ValidatorDashboard.js:6-10`).
**Swap to your stack:** easy. One call (`backend/services/gemini_client.py:40`). Redis is optional: without it the code runs with no cache (`backend/services/cache_service.py:25-27`).

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/services/validator_service.py` | Pairs, cache, semaphore, timeout, aggregation, thresholds | `17-30`, `32-81`, `107-174` |
| 2 | `backend/services/gemini_client.py` | Judge prompt, JSON extraction, 0.7 fallback | `14-64` |
| 3 | `backend/models/document.py` | Score bounds and report shape | `5-33` |
| 4 | `backend/services/cache_service.py` | Redis get/setex, no-cache fallback | `14-62` |
| 5 | `backend/config/settings.py` | Concurrency 5, timeout 10 s, threshold 0.5, TTL 3600 | `9-22` |

### How it works, step by step
1. `POST /api/v1/validator/validate` with a list of `Document{id, content, score, source}`, at most 20 (`backend/app/api/validator.py:10-23`). With fewer than 2 documents, everything is marked "skipped" with score 1.0 (`backend/services/validator_service.py:87-105`).
2. Build every unique pair (`:17-24`). That is O(N²): 20 documents means 190 LLM calls.
3. For each pair, the cache key is the MD5 of the **sorted document ids** (`:26-30`). A cache hit returns the stored score (`:38-42`).
4. On a miss, a semaphore of 5 and a 10 s `wait_for` wrap the judge call (`:45-51`; `backend/config/settings.py:19-20`).
5. Judge prompt, paraphrased (`backend/services/gemini_client.py:18-37`): compare these two documents (each cut to 1000 characters) for factual consistency and return JSON with `consistency_score` (1.0 fully consistent, 0.0 major contradictions), a list of specific conflicting facts, and your confidence. No temperature is set. Code fences are stripped and the three keys checked (`:43-53`).
6. Any error returns `consistency_score=0.7`, no contradictions, confidence 0.0 (`:57-64`; the timeout and exception paths do the same, `backend/services/validator_service.py:66-81`).
7. The result is cached for an hour (`:61-62`; `backend/services/cache_service.py:56-60`).
8. Aggregate: each document's score is the mean over all pairs it appears in (`backend/services/validator_service.py:120-138`). Status is failed below 0.5, warning below 0.7, otherwise passed (`:141-146`). Pairs below `CONSISTENCY_THRESHOLD` (0.5) go into `high_conflict_pairs` (`:127-133`). Overall consistency is the mean over pairs (`:162`).

### README vs code
- README: "LLM-Based Analysis" and "Pairwise Consistency Checking" (`README.md:9-10`). True.
- README: "Parallel Processing" (`README.md:12`). The client is `async def` but calls the **synchronous** `generate_content` (`backend/services/gemini_client.py:14,40`). That blocks the event loop, so the pairs run one after another and the semaphore does nothing.
- README: "Timeout protection" (`README.md:14`). `wait_for` cannot interrupt a blocking call (`backend/services/validator_service.py:48-51`), so the 10 s timeout does not really bound latency.
- README: "./setup.sh" (`README.md:38`). There is no `setup.sh` in this lesson. `demo.sh` calls `./start.sh` at the project root (`demo.sh:17`), but that file lives under `scripts/`.
- The README's sample numbers (0.85, 0.89; `README.md:120-129`) are illustrative and UNVERIFIED.

### Where it is thin or wrong
- [bug] **The cache key ignores content** (`backend/services/validator_service.py:26-30`). The dashboard's ids are fixed (`doc1`, `doc2`, `doc3`), so when Redis is running, editing a document's text and validating again within an hour returns the old verdict. (Without Redis there is no cache at all, `backend/services/cache_service.py:36-37`.) The test checks exactly this id-only symmetry (`backend/tests/test_validator.py:17-25`).
- [bug] **Fail-open.** On any judge error (bad key, retired `-exp` id, a score outside 0–1 rejected by Pydantic `backend/models/document.py:14`), the pair gets 0.7. A dead judge therefore never produces "failed" and never lands in `high_conflict_pairs` (< 0.5). With the dashboard's 3 documents (2 pairs each) the mean is exactly 0.7, so every document is marked **"passed"** (`backend/services/validator_service.py:138-146`). With 4 documents (3 pairs each), float rounding puts the mean of three 0.7s just below 0.7, so they show "warning" instead. The client-side fallback (`backend/services/gemini_client.py:57-64`) even gets **cached** for an hour (`backend/services/validator_service.py:53-62`).
- [shallow] Averaging hides a single contradiction. A document that clashes with one of five neighbours (scores 0, 1, 1, 1, 1) averages 0.8 and is marked "passed" (`:138`, `:141-146`), even though that pair still appears in `high_conflict_pairs` and its contradictions in the document's flags (`:127-133`, `:149-152`).
- [shallow] **A conflict is blamed on both documents equally.** The pair's score is added to both documents' lists (`backend/services/validator_service.py:123-125`), so the code cannot say which one is wrong. The fields that could help, the source, the timestamp and the retrieval score, are carried on each `Document` (`backend/models/document.py:8-11`) but never read, and `TEMPORAL_DRIFT_DAYS` is unused (`backend/config/settings.py:22`). For a RAG answer that is the decision that matters: which chunk to trust.
- [shallow] Each document is cut to its first 1,000 **characters** before judging (`backend/services/gemini_client.py:21,24`). A contradiction after that point is never seen, and the report does not mention the cut.
- [shallow] The prompt does not say how to score **unrelated** documents (no contradiction, but no agreement either). The retrieval `score` field is never used (`backend/models/document.py:8`). The judge has not been calibrated against labels (V4), and `confidence` is self-reported.
- [bug] The 400 errors for "no documents" and "more than 20" are raised inside a `try` that turns every exception into a 500 (`backend/app/api/validator.py:15-29`).
- [bug] The dashboard's new-document id is `doc{count+1}` (`frontend/src/components/ValidatorDashboard.js:34-36`). Remove one document, add one, and two documents share an id. Their scores then merge in `doc_scores` (`backend/services/validator_service.py:120-125`).
- [ok-for-demo] `TEMPORAL_DRIFT_DAYS` and `WS_HEARTBEAT_INTERVAL` are never used (`backend/config/settings.py:22,25`). The WebSocket only echoes (`backend/app/main.py:77-86`).

### Tests and data
- `backend/tests/test_validator.py` checks the pair count for 3 documents and the hash symmetry (`:5-25`). It never calls the judge and checks no quality.
- Data: the three Q3 snippets in the dashboard and in `demo.sh:35-38` make a nice tiny contradiction fixture. Label them carefully, though. Two say "revenue" ($50M and $48M, a clear conflict), but the third says "earnings reached $50M" (`demo.sh:37`). Earnings are not revenue, so whether that pair agrees or conflicts depends on your labelling rule. Write the rule down before you label (M1).

### What to take for your project
- **For V2/V4:** reuse the *judge-output contract* (score, list of specific conflicts, confidence) but point it at the right target: **answer claim vs cited chunk** (groundedness), not chunk vs chunk. Keep chunk-vs-chunk conflict detection as an optional "context conflict" flag for C5/X3.
- **For D2/LLMOps:** cache judge calls by a **content hash plus prompt version plus model id**, never by document id. Never cache a fallback.
- **For V4:** make judge failures **fail closed** (status "unknown", excluded from pass rates). Validate the judge on labelled pairs (TPR/TNR) before trusting it. That is your Phase 3 method.
- Turn the three-snippet fixture into a test case: 1 contradicting pair (the two revenue lines), plus 1 consistent pair that you write yourself without the revenue/earnings ambiguity.
- Fit it to your judge decision. Your official judge is a Cohere chat model, with Codex as the calibration labeller, run **once at the end** on stored traces. While you are still shaping the prompt, a Groq `openai/gpt-oss-20b` version (`reasoning_effort="low"`, JSON output) on a few hand-labelled pairs is fine. Cache every call in your record/replay layer, and send only non-book chunks to either provider.
- When a pair conflicts, record *which* chunk your pipeline trusted and why (source, date, retrieval rank). That trace field is what V1/V2 need, and this lesson leaves it out.

### Try this
- (20 min) Write 6 chunk pairs from your own PDFs: 2 consistent, 2 contradicting (edit a number), 2 unrelated. Before calling any judge, write your own label for each. Then run your Groq version of this prompt and compare. Watch for the unrelated pairs: does the judge call them "consistent" (1.0), or does it drop the score because they are off-topic? That ambiguity is a prompt-design gap.

### Interview angle
- **Q:** "How would you detect contradictions among retrieved chunks, and what does it cost?" **A:** Pairwise LLM or NLI checks cost O(N²) calls, so cap N, cache by content hash, and run it only when the answer depends on facts that might conflict. A cheaper design pulls out claims once, groups them by entity, and runs NLI on candidate pairs. Either way, a judge error must be treated as "unknown", not "consistent".

---

## Block summary
| Lesson | Title | Relevance | Concepts | Best file to read | Biggest problem |
|---|---|---|---|---|---|
| L33 | Reflexion agent | Medium (pattern) | A5, A2/A3 (shape only), M3 (counter), D2 · Interview | `backend/reflexion_agent.py` | The success signal is a keyword/length heuristic on tool output. `Result: 8` (9 chars) counts as failure (`backend/reflexion_agent.py:248`); placeholder text counts as success |
| L34 | Loop controls & budgets | Medium | D2, D1, A5 · LLMOps · Interview | `backend/app/budget_manager.py` | The budget exception is caught inside `run`, so every violation returns `success=True` and the violation rate is always 0 (`backend/app/execution_controller.py:44-46`, `backend/main.py:73-98`); checks run after the call is paid |
| L35 | "Agentic RAG" orchestrator | Low | A5/A1, V2 (counters), D2, C5 · Interview | `backend/services/orchestrator.py` | Planner, retriever and validator are constants (3 hard-coded docs, fixed relevance); the synth fallback reports success (`backend/agents/retriever_agent.py:10-47`, `backend/agents/synthesizer_agent.py:57-77`) |
| L36 | Planner: query decomposition | Medium | Q1, A1 (weak) · Interview | `backend/app/planner.py` | Any schema slip (more than 5 sub-queries, rationale over 200 chars) falls back to 1 sub-query silently and still counts as success (`backend/app/models.py:9,16,24`, `backend/app/main.py:63`) |
| L37 | Retriever + LLM reranker | High | R3, R1, Q1, C4, P3, P4 (counter), P5 · Interview | `backend/retriever_agent.py` | The "cross-encoder" is a Gemini listwise prompt; the hybrid RRF ranking is discarded (sort by `vector_score`, `backend/retriever_agent.py:92-97`) and the merge keeps the wrong `rrf_score` (`:166-181`); rerank scores are matched by position (`backend/reranker_tool.py:111,132-135`); a reranker failure gives all-zero scores with no real fallback (`:146-152`) |
| L38 | Validator: pairwise consistency | Medium | V2 (adjacent), V4, M3, D2 · LLMOps · Interview | `backend/services/validator_service.py` | The cache key is document ids only, so edited text returns stale verdicts (`:26-30`); judge errors become 0.7, which reads as "passed" (or "warning"), never "failed", and the client-side fallback is cached (`:53-62`, `:141-146`) |

### Cross-lesson patterns
- **Silent fallbacks reported as success.** L34's mock LLM always says COMPLETE (`backend/app/gemini_client.py:24`). L35's synthesizer returns a templated answer with `success=True` (`backend/agents/synthesizer_agent.py:57-77`). L36 counts the fallback plan as a successful decomposition (`backend/app/main.py:63`). L37's reranker gives every chunk a score of 0 (`backend/reranker_tool.py:146-152`). L38's "neutral" 0.7 reads as "passed" (or "warning"), never "failed". Each dashboard looks healthy even when the API key is dead.
- **Token counts are guesses, and budget checks come after the paid call.** L34 uses `len//4` (`backend/app/gemini_client.py:40-41`) and L35 uses word counts and per-document constants. Both check after the money is spent (`backend/app/budget_manager.py:54`, `backend/agents/synthesizer_agent.py:36-41`). None records the provider's real usage numbers.
- **Control decisions by substring.** L33 judges success by error keywords and length, and treats any text containing "rate limit" as a provider quota error; L34 stops when the text contains "COMPLETE", which also matches "INCOMPLETE".
- **Synchronous Gemini calls inside `async def`** (L33 API, L34 client, L35 synthesizer, L37 planner, L38 client) block the event loop. That quietly defeats the claimed "parallel" and "timeout" features. Only L36 (`run_in_executor`) and L37's reranker (`to_thread`) do it right.
- **Old or experimental model ids that may no longer be served** (UNVERIFIED: depends on Google's current model list): `gemini-1.5-flash` (L34, L37) and `gemini-2.0-flash-exp` (L35, L36, L38). Combined with the silent fallbacks, a fresh run probably shows mostly fallback output.
- **No reuse between lessons.** L35's planner is a stub, L37 writes its own 2–4 sub-question planner instead of using L36's, and L35 re-implements L34's budget manager. Copied infrastructure is listed in requirements and never imported: Redis in L33 and L37, OpenTelemetry, Prometheus and tiktoken in L37, jose/passlib in L38. (L38 is the only lesson that really uses Redis.)
- **Tests never measure quality.** They are tests that pass on fallback (L33, L36), constant pipelines (L35), pure helpers (L38), curl smoke tests (L34), or nothing at all (L37). L35's `test_budget_enforcement` cannot fail at all: a budget refusal lowers the total it checks (`backend/tests/test_pipeline.py:50-56`). There are no labelled data, no retrieval metrics and no judge validation anywhere in the block.
- **Scores shown as measurements that are not.** L35's relevance and confidence are typed-in constants (`backend/agents/retriever_agent.py:15,21,27`). L37's "Vector" score is `1 - distance`, shown ×100 like a percentage (`backend/vector_store.py:106`). L33's critic confidence and L38's judge confidence are self-reported. L34's token charts plot `len//4` guesses. None of these numbers is calibrated against labels.
- **Concept mapping note.** None of these lessons is A4 in your curriculum (user-feedback loops, Ch17). The "reflect and retry" loops in L33 and L34 belong under A5, as agent-loop shape only.
- **JSON from LLMs with no JSON mode.** L36, L37 and L38 strip code fences before parsing; L34 does not even do that (`backend/app/execution_controller.py:73-80`). Every parse failure leads to a silent fallback.
