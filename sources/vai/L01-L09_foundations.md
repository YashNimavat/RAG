# VAI lessons 1–9: foundations

[← Guide index](README.md) · Course folder: `C:\Yash\New-Work\RAG\vertical-ai-agents-main\` · Checked 2026-10-17 · Log: [verification/L01-L09_foundations_log.md](verification/L01-L09_foundations_log.md)

**What this is:** the guide to VAI lessons 1–9: Python, async, attention, LLM parameters, the LLM client, JSON output, decisions and memory.
**What this is not:** the course code, or a run of it. Nothing in the course was run or copied.

**How to read this file:**
- A `file:line` is relative to the project folder named in the lesson heading.
- **UNVERIFIED** marks behaviour that depends on a library version or on Gemini.
- **(counter)** or † means the lesson names a technique without building it. Read it to learn what is missing.
- Tags: **[bug]** the code does the wrong thing · **[misleading]** a label, message or number claims more than the code does · **[shallow]** it works, but is too thin for your project · **[ok-for-demo]** fine for a demo, not for real use · **[LLMOps]** material for your LLMOps notebooks · **[Interview]** worth practising for interviews.
- "I" means the reviewer who checked the code. Each lesson was checked by a reader, a fact-check pass and a completeness pass; the log has every verdict.

**Notes for this block:**
- `../setup.sh:N` means the lesson's generator script, one level above the project folder.
- A Google API key is hard-coded in several files of this block (listed under Cross-lesson patterns). Its value is not repeated here.

---

## L1 · Python environment setup  (`lesson1/vaia-l1-python-setup/`)

**What the code teaches, in one line:** How to make a venv, pin packages, check that they import, and serve a tiny FastAPI dashboard that counts its own demo calls.
**What it is not:** It makes no LLM call, no tokenizer use, no Gemini use at all. The Gemini SDK is only imported to prove it is installed (`src/main.py:17`, `src/validate_environment.py:14`).
**Relevance to your RAG study:** None — concepts: none
**Stack:** FastAPI 0.109, Pydantic 2.5, NumPy, pandas, `google-generativeai==0.3.2` (`requirements.txt:2-10`). `.env.example:3` names model `gemini-pro`, but nothing reads it. The dashboard is plain HTML served from `src/app.py:32-158`.
**Swap to your stack:** easy. You already use uv and Python 3.12, so `uv add` replaces the whole of `../setup.sh`.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `src/validate_environment.py` | Imports each required package and prints its version | 9-18, 20-28 |
| 2 | `src/app.py` | FastAPI app with an in-memory metrics dict and a demo endpoint | 17-25, 170-197 |
| 3 | `tests/test_app.py` | TestClient checks of the endpoints | 35-52 |

### How it works, step by step
1. `../setup.sh:142-174` makes a venv and pip-installs both requirement files. All pip output goes to /dev/null (`:164`, `:169`, `:173`). The script runs under `set -e` (`../setup.sh:12`), so a failed install does stop it. But you see no error text. The last line you see is "Installing dependencies...".
2. `../setup.sh:178-193` writes `.env.example`, which holds a real-looking Google key, and copies it to `.env`.
3. `POST /api/demo` sleeps 0.1 s, then bumps three counters and a running mean latency (`src/app.py:170-191`).
4. The HTML page polls `/api/metrics` every second (`src/app.py:154`). It also has a meta refresh every 2 s (`src/app.py:40`), so it reloads the whole page as well.

### README vs code
- README says the layout includes `src/agents/`, `services/`, `utils/` and `config/` (`README.md:21-36`). They are empty folders made by `../setup.sh:73-77`, and they are absent from this copy.
- The README never mentions `app.py` or the dashboard, which is the only runnable thing.

### Where it is thin or wrong
- [misleading] "Total Requests" counts only `/api/demo` calls (`src/app.py:179-181`), so "Requests/Second" is demo calls divided by uptime (`src/app.py:166`).
- [misleading] The other cards cannot tell you anything either. "Avg Response Time" times a fixed `asyncio.sleep(0.1)` (`src/app.py:176`, `:184`), so it always sits near 100 ms. "Successful Operations" goes up on every call with no failure path, so it always equals "Demo Executions" (`src/app.py:179-181`). A metric that cannot move is not a metric.
- [bug] Silent install: pip errors are hidden (`../setup.sh:169`, `:173`). Because of `set -e` (`../setup.sh:12`), a failed install stops the script, but with no error message, so you cannot tell why it stopped.
- [ok-for-demo] The version check `major >= 3 and minor >= 12` would reject a future 4.0 (`src/validate_environment.py:23`).
- [bug, D4] A key-shaped secret sits in a committed example file (`.env.example:2`).

### Tests and data
- `tests/test_environment.py:22-27` only passes if you run it from the project root with `venv/` and `.env` present. `tests/test_app.py` checks status codes and that counters go up. There is no data.

### What to take for your project
- Skip it. The one lesson worth keeping is negative: never put a key in an example file (D4).

### Try this
- (10 min) Read `src/app.py:160-197`. Predict "Requests/Second" after 10 demo calls in a server that has been up for 100 s. Then explain why that number is not request throughput.

### Interview angle
- Q: "Why pin dependency versions?" A: So that a rebuild gives the same behaviour. Your frozen-text `snapshot_id` depends on `pymupdf==1.26.7` for exactly this reason. Pins plus a lock file (uv.lock) make runs repeatable.

---

## L2 · Async, decorators, Pydantic  (`lesson2/vaia-l2-advanced-python/`)

**What the code teaches, in one line:** Three wrappers you see in many LLM apps (retry with backoff, a TTL cache, latency tracking), plus `asyncio.gather` to send many prompts to Gemini at once and Pydantic to validate the request.
**What it is not:** In the default mode, the retry never retries an API failure (see README vs code). There is no limit on how many calls run at once, and the cache is not safe for LLM output.
**Relevance to your RAG study:** Medium — concepts: D2 (cache, retry), P1 (minor: temperature and max tokens are only passed through as request fields) [LLMOps] [Interview]
**Stack:** FastAPI, aiohttp REST call to `gemini-2.0-flash-exp` (`backend/app/main.py:145`), key hard-coded at `backend/app/main.py:144`. No embeddings, no vector store. The React UI (`frontend/src/components/Dashboard.js`) shows five metric cards (total requests, active tasks, average latency, success rate, cache hit rate) and a form to send prompts, one per line.
**Swap to your stack:** easy. Only `call_gemini_api` talks to the provider. Swap it for an async Groq client call that returns the message text. Pass `reasoning_effort="low"` and a `max_tokens` large enough for `openai/gpt-oss-20b`, because a reasoning model spends part of its output budget before it writes the answer.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/app/main.py` (models) | `AgentRequest` validation: id regex, 1–100 prompts, temperature 0–2, max_tokens 1–8192 | 30-41 |
| 2 | `backend/app/main.py` (decorators) | `with_retry`, `with_cache`, `with_performance_tracking` | 77-138 |
| 3 | `backend/app/main.py` (provider call) | `call_gemini_api` with 30 s timeout and demo fallbacks | 149-189 |
| 4 | `backend/app/main.py` (fan-out) | `process_prompts_async` gathers all prompts | 191-211 |
| 5 | `scripts/test.sh` | curl smoke tests | 41-55 |

### How it works, step by step
1. `POST /process` validates the body with `AgentRequest` (`backend/app/main.py:217-218`). The id must match `agent-` plus exactly 8 lowercase letters or digits (`:32`).
2. It calls `process_prompts_async`. The outer wrapper is `with_cache` (TTL 300 s, key built from the function name and the string form of its args, `:95-117`, `:191`). Inside it sits `with_performance_tracking` (`:119-138`, `:192`). So each call checks the cache first, and only a miss reaches the tracker.
3. On a cache miss, one `aiohttp` session fires every prompt at once with `asyncio.gather(..., return_exceptions=True)` (`:195-200`). Nothing caps concurrency, and up to 100 prompts are allowed (`:33`).
4. Each call posts the prompt, `temperature` and `maxOutputTokens` to the REST endpoint with a 30 s total timeout (`:153-164`).
5. `with_retry(max_attempts=3, backoff=2.0)` would wait `2 ** attempt` seconds, so 1 s and then 2 s, with no jitter (`:77-93`, `:149`).
6. The result list comes back as `(results, cached_flag)` (`:115`, `:227-241`). `/metrics` reports averages from the global dict (`:247-263`).

### README vs code
- README says "Non-blocking I/O for 1000+ concurrent requests" (`README.md:23`). Nothing measures that, and the code has no concurrency limit.
- README says "Retry". In practice, with the default `GEMINI_USE_FALLBACK=1` (`backend/app/main.py:147`), every error becomes a `[DEMO] ...` string inside the function (`:169-189`). The retry decorator never sees an exception.
- The generator does not have the fallback (`../setup.sh:173-200`). It was added to the folder copy later, so the two disagree.

### Where it is thin or wrong
- [bug] The retry is dead in default mode (above). With the fallback off, the broad `except Exception` (`:184`) re-wraps every error, including the 429 raised at `:174`, as an internal `HTTPException(500)` (`:189`). So it would retry a 400 bad request as readily as a 429. The code never sorts errors into retryable and non-retryable.
- [misleading] Even with the fallback off, your client never sees that 500. After the last retry, `gather(..., return_exceptions=True)` catches the exception and the loop turns it into an `"Error: ..."` string inside the results list (`:200`, `:205-207`). The endpoint still answers HTTP 200 (`:235-241`). In both modes, a failure looks like an answer.
- [shallow] The cache never evicts. Expired entries are overwritten only if the same key comes back, so memory grows with every distinct request (`:104-114`).
- [bug] Fallback and error strings get cached for 300 s and returned with `cached=True` (`:113-115`, `:207`).
- [misleading] `success_rate` counts fallback and "Error: ..." answers as successes, because no exception is raised (`:126-129`, `:204-209`).
- [misleading] Cache hits skip `with_performance_tracking`, because the cache is the outer wrapper, so `total_requests` leaves them out (`:191-192`).
- [shallow] Caching at temperature 0.7 freezes one random sample. The key uses `str(args)`, which works here but is fragile for dicts.
- [misleading] `active_tasks` is `len(asyncio.all_tasks())`, which counts every task on the server's event loop (`:255`).
- [bug] `scripts/test.sh:47` sends ids like `agent-load10`. That is 6 characters after the dash, not 8, so all ten "load test" requests fail with 422. The output goes to /dev/null, so nobody sees it.
- [bug, D4] Hard-coded key (`:144`), sent as a URL query parameter (`:162`).

### Tests and data
- There are no Python tests. `scripts/test.sh` only curls the endpoints and prints JSON. There is no data.

### What to take for your project
- Re-implement in plain Python, for D2: a cache wrapper around your LLM call, done right. Make the key a stable hash of model, prompt, params and prompt version. Store it on disk (your record/replay cache). Never store errors or fallbacks. Count hits and misses. Add one test that forces a provider error and then asserts that the next identical call is a cache miss, not a replayed error.
- Re-implement a retry wrapper that retries only on 429, 5xx and timeouts. Use exponential backoff with jitter, and honour a `Retry-After` header if the provider sends one.
- Add an `asyncio.Semaphore` around the gather. Groq has per-minute request and token limits.

### Try this
- (20 min) Trace by hand what happens when Gemini returns 429 twice, first with the fallback on and then with it off. Write down how many HTTP calls are made, what `success_rate` shows, and what the next identical request returns. You will see why retry, fallback and cache must be designed together.

### Interview angle
- Q: "Where should retry and cache sit around an LLM call?" A: Retry goes innermost, on the raw provider call, and only for transient errors. The cache goes outside it and stores only real successes, keyed on everything that changes the output. Metrics should count cache hits and fallbacks as separate outcomes, not as successes.

---

## L3 · Transformer deep dive (attention visualiser)  (`lesson3/l3-transformer-deep-dive/`)

**What the code teaches, in one line:** A correct NumPy forward pass of a transformer encoder (scaled dot-product attention, multi-head split and merge, sinusoidal positions, FFN, post-layer-norm) whose attention weights are drawn as heatmaps.
**What it is not:** It is not a trained model. The weights are random, the "embeddings" are fresh random noise on every call and ignore which token they stand for, and there is no decoder, no causal mask, no next-token softmax, no temperature or top-p, and no BPE tokenizer. The heatmaps carry no linguistic meaning.
**Relevance to your RAG study:** Medium — concepts: P1, P4 (counter-example: its `create_embeddings` is random noise, not an embedding model) [Interview]
**Stack:** Python, FastAPI, NumPy. Only NumPy does the work. `backend/requirements.txt:9` also pins `google-generativeai==0.8.3`, but no backend file imports it. No LLM call, though `backend/app/config.py:4` stores a Gemini key anyway. The React UI shows a text box, a layer picker, and one Plotly heatmap per head (`frontend/src/components/AttentionHeatmap.js`), plus a "Performance Metrics" tab.
**Swap to your stack:** easy. It is pure NumPy, with nothing to swap.

### Is the attention real or fake?
- **The math is real.** `ScaledDotProductAttention.forward` computes Q·Kᵀ divided by √d_k, applies an optional mask, takes a numerically stable softmax (max subtracted first), and multiplies by V (`backend/app/transformer.py:63-82`, `:84-88`). Heads are split and merged with the correct reshape and transpose (`:116-132`). The positional encoding matches the sin/cos formula (`:192-205`).
- **The inputs are fake.** `SimpleTokenizer.create_embeddings` returns `np.random.randn(len(tokens), d_model) * 0.1` (`:365-368`). It uses only the number of tokens and throws the token ids away. The same word gets a different vector every call, and two copies of a word in one sentence get unrelated vectors.
- **The weights are random.** W_q, W_k, W_v, W_o and the FFN matrices are Xavier-uniform draws made once at startup and never trained (`:105-114`, `:224-231`; built at `backend/app/main.py:38`).
- **Dropout stays on at inference.** With `dropout=0.1` (`backend/app/config.py:10`), `_dropout` zeroes about 10 % of the attention weights and scales the rest by 1/0.9 on every request (`backend/app/transformer.py:76-77`, `:91-94`). The weights you see are after dropout, so rows do not sum to 1 and some cells are random zeros.
- My inference from the magnitudes: the noise has std 0.1, while the positional encoding is on the order of 1. So the encoder input is mostly position, and any pattern in layer 0 mostly reflects position, not words. (Reasoning only, not measured.)

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/app/transformer.py` | `ScaledDotProductAttention`: the core formula | 37-94 |
| 2 | `backend/app/transformer.py` | `MultiHeadAttention`: projections and the head split | 96-183 |
| 3 | `backend/app/transformer.py` | `PositionalEncoding`, `FeedForward`, `LayerNorm`, `TransformerBlock` | 185-283 |
| 4 | `backend/app/transformer.py` | `SimpleTokenizer`: whitespace words and random embeddings | 322-368 |
| 5 | `backend/app/main.py` | `/transform` endpoint and the WebSocket "stream" | 64-139 |
| 6 | `backend/tests/test_transformer.py` | Shape tests and a sum-to-1 test | 21-36 |

### How it works, step by step
1. `POST /transform` lower-cases and whitespace-splits the text. Each new word gets the next id in a vocabulary shared by all requests, capped at 10 000 entries; after that, new words map to `<UNK>`. START and END tokens are added (`backend/app/transformer.py:342-358`, `backend/app/main.py:72-73`).
2. Random embeddings of shape 1 × seq × 512 are created (`backend/app/main.py:76`).
3. `TransformerEncoder.forward` adds positional encoding, then runs 6 blocks (`backend/app/config.py:7-9`; `backend/app/transformer.py:292-319`). No mask is passed (`backend/app/main.py:79`), so every token attends to every token, as in an encoder.
4. Each block runs post-norm. It projects to Q, K and V (512 × 512 each), splits into 8 heads of d_k = 64, runs attention per head in a Python loop, merges, projects with W_o, adds the residual, and applies LayerNorm. Then it runs the FFN (512→2048→512 with ReLU and no biases), adds the residual, and applies LayerNorm (`backend/app/transformer.py:134-183`, `:233-237`, `:263-283`).
5. The response holds every layer's weights (8 × seq × seq) and the full 1 × seq × 512 output, which makes a large JSON payload (`backend/app/main.py:83-94`).

### README vs code
- "Real-time attention weight visualization" (`README.md:32`): the weights come from random inputs. The WebSocket "streaming" computes everything first, then sends layers with an artificial 0.1 s sleep (`backend/app/main.py:125-133`) and reports `latency_ms: 0` (`:138`).
- "Performance metrics dashboard" (`README.md:34`): the latency, throughput and memory charts are `Math.random()` values made in the browser (`frontend/src/components/PerformanceMetrics.js:23-38`), under the caption "Real-time monitoring" (`:44`).
- "Gemini AI integration ready" (`README.md:42`): Gemini is never called.

### Where it is thin or wrong
- [misleading] Random, token-blind embeddings and untrained weights (above). The heatmap for the same sentence changes on every click.
- [bug] Dropout at inference (`backend/app/transformer.py:76-77`), with no train/eval switch.
- [bug] `test_scaled_dot_product_attention` builds the class with its default dropout 0.1 and then asserts that rows sum to 1 (`backend/tests/test_transformer.py:23`, `:36`). By reading, this fails on essentially every run. A row with nothing dropped sums to 1/0.9 ≈ 1.11, and a row with drops sums to (kept mass)/0.9, which equals 1 only by coincidence.
- [shallow] `settings.max_seq_length = 512` is shown in the UI (`frontend/src/components/PerformanceMetrics.js:64-65`) but never applied. The positional table defaults to 5000 rows (`backend/app/config.py:11`, `backend/app/transformer.py:188`, `:290`). No context window is enforced.
- [shallow] LayerNorm divides by (std + eps) rather than √(var + eps) (`backend/app/transformer.py:247-251`). The difference is minor.
- [shallow] The forward passes are `async def` but CPU-bound. They block the event loop and never yield (`:134`, `:263`, `:292`).
- [shallow] No input-length check. Text longer than 4 998 words gives more positions than the 5 000-row table, so the add at `backend/app/transformer.py:218` fails on shape and the request returns HTTP 500. Below that, the JSON reply grows as layers × heads × seq² (`backend/app/main.py:85`).
- [misleading] For a RAG reader: the name `create_embeddings` (`backend/app/transformer.py:365-368`) suggests the vectors you will search with. They are not. Retrieval embeddings (P4) come from a trained model and are pooled into one vector per text. This encoder returns one untrained vector per token (`backend/app/main.py:86`).
- [shallow] The heatmap hover text says "From: x / To: y" (`frontend/src/components/AttentionHeatmap.js:19-25`). Rows (y) are queries and columns (x) are keys. Read as "which token attends to which", the labels are backwards. Read as "information flows from key to query", they are right. The code does not say which it means, so check the axes yourself.

### Tests and data
- The tests check shapes, the d_model % heads check, and START/END tokens (`backend/tests/test_transformer.py:12-83`). The only property test (row sums) contradicts the code. No data files.

### What to take for your project
- Re-implement attention in your own NumPy notebook for P1. Write single-head scaled dot-product attention with dropout off, add a causal mask (a lower-triangular matrix), and assert that rows sum to 1. Then give each token id a fixed embedding, so repeated words get the same vector.
- Use it to explain to yourself why the context window is quadratic in cost: the score matrix is seq × seq, per head and per layer.
- Do not reuse the tokenizer. Real LLMs use subword (BPE) tokens, so whitespace-word counts do not match token counts.
- For P4, keep two ideas apart in your notes: token vectors inside an LLM, and the one-vector-per-chunk embeddings you get from Cohere `embed-v4.0` (or local MiniLM). Only the second kind goes into your index.

### Try this
- (30 min) In your own notebook, re-write `forward` from `backend/app/transformer.py:63-82` in your own words, with a `training` flag. Test three cases: (a) dropout on, then check row sums; (b) random Q, K and V scaled ×10, then watch softmax become nearly one-hot; (c) a causal mask, then check that the upper triangle is 0. What to look for: case (b) shows why the √d_k scaling exists.

### Interview angle
- Q: "Why divide by √d_k in attention?" A: If the parts of q and k are independent with mean 0 and variance 1, their dot product has variance d_k, so scores grow with dimension. Large scores push softmax into near one-hot outputs with tiny gradients. Dividing by √d_k brings the score variance back to about 1.

---

## L4 · "LLM parameters": specs, cost and context  (`lesson4/l4-llm-parameters/`)

**What the code teaches, in one line:** A per-request cost formula with a cached-input share, a latency loop against Gemini, and real token counting with `count_tokens`, all wrapped around a hand-typed table of model "specs".
**What it is not:** "Parameters" here means model size, not sampling parameters. There is nothing on temperature, top-p or top-k beyond a fixed `temperature=0.7` (`backend/main.py:179`). Nothing on training data scale either, though the README promises it.
**Relevance to your RAG study:** Medium — concepts: P1 (tokens, context window), D2 (cost model, caching) [LLMOps] [Interview]
**Stack:** FastAPI and `google-generativeai==0.8.3`. Key hard-coded at `backend/main.py:21`. Models `gemini-2.0-flash-exp`, `gemini-1.5-pro`, `gemini-1.5-flash` (`:24-55`). The React UI has four tabs: model comparison, cost calculator, performance tester, context analyzer.
**Swap to your stack:** moderate. The cost math carries over directly. The real token count needs a local tokenizer for your model or the usage numbers in each Groq response, because Gemini's `count_tokens` has no drop-in twin.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/main.py` | `MODEL_SPECS` table | 24-55 |
| 2 | `backend/main.py` | `calculate_cost`: cached/uncached/output split | 112-157 |
| 3 | `backend/main.py` | `test_performance`: timing loop | 159-239 |
| 4 | `backend/main.py` | `analyze_context_usage`: token percentiles | 241-301 |
| 5 | `test.sh` | curl checks | 8-23 |

### How it works, step by step
1. Cost: for each request, the cached input share (`cache_hit_rate`, default 0.5) is billed at the cached price, the rest of the input at the full input price, and output at the output price, all per 1M tokens. That is then multiplied by requests per day, 30 and 365 (`backend/main.py:126-148`).
2. Performance: it builds a `GenerativeModel` and runs `num_iterations` (default 5) calls with `max_output_tokens=100` and `temperature=0.7`, timed with `datetime.now()`, sleeping 0.5 s between calls (`:166-206`).
3. After each call it counts the **input** prompt tokens with `count_tokens`, one extra API call per iteration. If that fails it uses words × 1.3 (`:198-204`).
4. It returns min, max, mean, median and "p95" from `statistics.quantiles(n=20)[18]` (`:211-217`), plus "variance from spec" against the hand-typed latency (`:222-225`).
5. Context: it counts tokens for each sample text with `count_tokens` (`:252-254`), takes p50, p95 and p99 by index (`:259-266`), and recommends "context limit = p99" with "potential savings" of (window − p99) / window (`:268-297`).

### README vs code
- "Latency measurement (p50/p95/p99)" (`README.md:37`): the performance endpoint has no p99, and its "p95" comes from 5 samples (`backend/main.py:216`).
- "Training data scale" (`README.md:4`): absent.
- "Actual inference benchmarks … token count analysis": it counts only input tokens, which are the same every iteration. Output tokens and tokens per second are never measured (`:199`).

### Where it is thin or wrong
- [misleading] The `"parameters": "7B"` and `"70B"` values (`backend/main.py:26`, `:36`, `:46`) are UNVERIFIED and look invented, since Google does not publish Gemini parameter counts. `latency_estimate_ms` and `max_rpm` are also UNVERIFIED. Prices are dated "May 2025" (`:23`, `:88`) and UNVERIFIED.
- [misleading] `compute_intensity_score` = params × window / 1M and `cost_efficiency_score` = 1000 / (in + out price) are made-up scores (`:100-109`).
- [misleading] **The context "savings" are a fallacy.** You pay for tokens you send, not for unused window space. A 1M-token window with p99 = 400 reports "Potential cost reduction 99.96 %", which nobody would ever save (`:273`, `:295`). Good P1 trap.
- [shallow] p95 from 5 samples via `statistics.quantiles` (default "exclusive" method) can come out above the largest observed value, so it means little (`:216`).
- [bug] A sync `generate_content` call sits inside `async def` (`:160`, `:175`) and blocks the server while it runs.
- [shallow] Dead code: `cache_savings_factor` and `effective_input_tokens` are computed and never used (`:122-123`, `:316`).
- [bug] `/compare` divides by `monthly_cost`, so `requests_per_day=0` gives an HTTP 500 (`:335`).
- [misleading] The `/compare` "recommendation" is simply the cheapest model. It sorts on `1000 / monthly_cost`, with no quality or latency term (`:335`, `:340`, `:350`). `gemini-2.0-flash-exp` and `gemini-1.5-flash` have identical prices in the table (`:28-30`, `:48-50`), so the stable sort keeps table order and always "recommends" the first one.
- [shallow] `cache_hit_rate` has no 0–1 bounds (`:62`). A value of 1.5 makes the uncached input cost negative (`:128-129`), and the API returns that number without complaint.
- [bug] Empty `sample_texts` should get the 400 at `:257`, but the blanket `except Exception` at `:300-301` catches that `HTTPException` and returns HTTP 500 instead.
- [shallow] The timing loop uses the wall clock (`datetime.now()`, `:172`, `:192-193`) rather than a monotonic timer, and it keeps the first (cold-connection) call in the stats.
- [bug] `test.sh` uses `set -e` with `grep -q … && echo`. A failed check just skips its echo, and the script always ends "All tests passed!" (`test.sh:8-23`).

### Tests and data
- There are no unit tests. `test.sh` only greps the responses for words (`test.sh:8-21`). `validate_dashboard.sh` checks that prices and costs are above zero (`validate_dashboard.sh:12`, `:25`, `:38`). Its performance and context checks only print warnings and never count as errors (`:46-78`). There is no data.

### What to take for your project
- For D2: write a tiny `cost.py` in your own words that takes the real `usage` numbers from each Groq response, plus a price table that carries a date and a source URL. Report cost per query split into input and output. Because `openai/gpt-oss-20b` is a reasoning model, check one real response to see whether its reasoning tokens are counted inside `completion_tokens` (UNVERIFIED here). If they are, your output share is larger than the visible answer suggests.
- Store `usage` in your record/replay cache with each recorded call, so a replayed run reports the same token counts and you can still compute cost without credits.
- For P1: the "context window ≠ bill" idea, plus the habit of measuring the token distribution of your real prompts (system prompt + k chunks + question), so you can set k and chunk size inside a budget (links to X3).
- Skip the specs table and the scores.

### Try this
- (15 min) Using `calculate_cost` (`backend/main.py:126-133`), work out on paper the cost for 1 000 RAG queries a day, each with 3 000 input tokens (5 chunks) and 300 output tokens, at cache-hit rates 0 and 0.8. Use your own dated price list. Notice how big the input share is. With 10 input tokens per output token, input dominates unless output costs more than 10× input per token. That is why chunk count and chunk size are cost levers.

### Interview angle
- Q: "Does a bigger context window make RAG cheaper or unnecessary?" A: No. You pay per token sent, and stuffing more context raises cost and latency and can bury the relevant passage. A big window is a ceiling. Retrieval decides what is worth paying to send.

---

## L5 · Model comparison and selection  (`lesson5/vaia-l5-model-comparison/`)

**What the code teaches, in one line:** A sequential benchmark loop (models × prompts × repetitions) that times Gemini calls with `perf_counter_ns`, plus a correct Pareto-dominance check, applied to hard-coded comparison tables.
**What it is not:** It never measures answer quality, so it is not a model evaluation. The "comparison", "MMLU" and "recommendations" are constants, and benchmark results never feed into them.
**Relevance to your RAG study:** Low — concepts: M4 (counter-example: unflagged simulated data, 3-sample p95), D2 (real latency timing and a cost formula), A1 (counter-example: "cascading" is only a label, nothing routes) [LLMOps] [Interview]
**Stack:** FastAPI, `google-generativeai==0.3.2` via `asyncio.to_thread` (`backend/app/services/model_client.py:30-37`). Models `gemini-2.0-flash`, `gemini-1.5-pro`, `gemini-1.5-flash` (`backend/app/main.py:57-89`). The key comes from env (`backend/app/main.py:26`). The React UI picks models, runs 3 fixed prompts × 3 reps, and charts latency and cost (`frontend/src/App.js:19-23`, `:54-62`).
**Swap to your stack:** moderate. `ModelClient.generate` is a one-function swap, but most of the lesson is tables you would delete anyway.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/app/services/model_client.py` | Timed call, then a **simulated fallback** | 13-88 |
| 2 | `backend/app/services/benchmark_service.py` | Benchmark loop and aggregation | 12-86 |
| 3 | `backend/app/services/analytics_engine.py` | Hard-coded comparisons, Pareto check, recommendations | 9-78, 80-164 |

### How it works, step by step
1. `POST /api/benchmark` loops model → prompt → repetition (default 3, temperature 0.7) one call at a time, sleeping 0.5 s between calls (`backend/app/services/benchmark_service.py:23-56`).
2. Each call is timed around a `to_thread` call, with `max_output_tokens=1000` (`backend/app/services/model_client.py:27-41`). Token counts are words × 1.3 (`:47-48`). The code never reads the response's own token counts. Whether the pinned SDK (`google-generativeai==0.3.2`, `backend/requirements.txt:4`) even exposes them is UNVERIFIED. Cost uses a per-1K price table (`:99-110`).
3. **Any exception** (quota, safety block, bad model id) returns a random latency in a model-specific range, a fake text, and `"success": True` (`:59-88`).
4. The aggregation keeps latency, cost and tokens but **drops the `simulated` flag** (`backend/app/services/benchmark_service.py:47-53`), sets `success_rate` to 1.0 (`:69`), and computes "p95" from 3 runs (`:66`).
5. `/api/compare` returns a hard-coded dict of latency, throughput, cost and "mmlu_score" (`backend/app/services/analytics_engine.py:12-29`), then runs `_calculate_pareto_frontier`. That function is a correct "dominated if another option is no worse on all three axes and strictly better on one" check (`:51-78`).
6. `/api/recommendations` filters another hard-coded table by constraints, labels everything `"confidence": "high"`, and suggests "cascading" whenever two or more models pass (`:89-153`).

### README vs code
- "Real-time benchmarking across models" (`README.md:27`): real only when every call succeeds. Otherwise the numbers are random and nothing marks them.
- "Gemini Flash, Pro, Ultra comparison" (`README.md:24`): there is no Ultra in the code.
- "Pareto frontier analysis": computed on constants (`backend/app/services/analytics_engine.py:12-29`), not on your benchmark.
- The generator script has no simulated fallback. Its `except` branch returns `success: False` (`../setup.sh:254-262`). The random fallback was added to the folder copy later. (The only "Simulated" text in the generator is the comment on the hard-coded comparison table, `../setup.sh:415`.)

### Where it is thin or wrong
- [misleading] Random latencies presented as measurements, success forced to True, simulation flag dropped (above).
- [misleading] The MMLU and quality scores are UNVERIFIED constants (`backend/app/services/analytics_engine.py:25-27`, `:93-105`). The benchmark stores nothing, and `self.benchmark_data` is never used (`:7`).
- [shallow] The L4 and L5 price tables disagree only on 2.0 Flash. L4 has `gemini-2.0-flash-exp` at 0.075 / 0.30 per 1M (`lesson4 …/backend/main.py:28-29`). L5 has `gemini-2.0-flash` at 0.0005 / 0.0015 per 1K, which is 0.50 / 1.50 per 1M (`backend/app/services/model_client.py:100`). The 1.5 Pro and 1.5 Flash prices match once you convert per-1K to per-1M (`model_client.py:101-102` vs `lesson4 …/backend/main.py:38-39`, `:48-49`). All prices are UNVERIFIED. L5 also lists `"parameters": "Unknown"` (`backend/app/main.py:61`), where L4 claims "7B".
- [shallow] p95 from 3 samples (`backend/app/services/benchmark_service.py:66`), and the same prompts are always run in the same order, so caching or warm-up effects are not controlled.
- [misleading] In the simulated path even the cost is invented. Output tokens are prompt words × 2.5 (`backend/app/services/model_client.py:76-77`), and that number is priced as if real (`backend/app/services/benchmark_service.py:40-45`).
- [misleading] The summary's `total_requests` is the number of prompts, not calls. It counts per-prompt averages (`backend/app/services/benchmark_service.py:99-107`), so 3 prompts × 3 reps reports 3.
- [shallow] `/api/recommendations` tests constraints by truthiness, so a limit of 0 is silently ignored (`backend/app/services/analytics_engine.py:115-121`). "Cascading" just names the cheapest and the most expensive passing models as primary and fallback (`:147-153`). No query is ever routed.

### Tests and data
- No unit tests. `scripts/test.sh` checks that the endpoints answer, and prints "All tests passed!" even after warnings (`scripts/test.sh:44-61`). It never calls `/api/benchmark`, the only endpoint that reaches a model (`scripts/test.sh:34-58`). No data.

### What to take for your project
- For M4 and I-CMP: re-implement the Pareto check in your own words to compare RAG configurations on (answer-quality score, p50 latency, cost per query). The check itself is sound. Your LLM is fixed (Groq `openai/gpt-oss-20b`), so the useful axis to vary is the retrieval set-up (chunk size, k, reranker on or off), not the model.
- Rule to adopt: any simulated or fallback result must carry a flag all the way to the report and be left out of the metrics.
- Skip the rest. Model choice for RAG needs your own eval set (M1), not MMLU.

### Try this
- (15 min) Read `backend/app/services/model_client.py:59-88` and `backend/app/services/benchmark_service.py:40-70`. With an invalid API key, list every number the UI would show and mark which ones are real. Then write a one-line change, on paper, that would keep the flag.

### Interview angle
- Q: "How would you pick an LLM for a RAG system?" A: Run each candidate on a task-specific eval set with fixed retrieval. Score faithfulness and correctness, and record p50/p95 latency and cost from real usage. Keep the models on the quality–latency–cost Pareto front, then choose by your budget.

---

## L6 · Production LLM API client  (`lesson6/l6-llm-api-client/`)

**What the code teaches, in one line:** The standard client stack around one LLM call: a token-bucket rate limiter with RPM and TPM, a circuit breaker with closed/open/half-open states, retry with exponential backoff and jitter, a per-call cost tracker using real usage, and JSON logs with request ids.
**What it is not:** Out of the box it is a mock. `use_mock_gemini` defaults to True, and in mock mode the circuit breaker and retry are skipped. The client also lacks per-call timeouts, error classification and Retry-After handling.
**Relevance to your RAG study:** High (for the client layer, not RAG itself) — concepts: D2, D1 [LLMOps] [Interview]
**Stack:** FastAPI, `google-generativeai==0.4.0`, `structlog`, pydantic-settings. Model `gemini-1.5-flash` (`config/settings.py:6`). Prices 0.075 / 0.300 per 1M (`config/settings.py:18-19`, UNVERIFIED). `redis` and `prometheus-client` are in `requirements.txt:8-9` but never used. The React UI has a prompt box, a stats panel polled every 5 s, and a history of the last 10 calls (`frontend/src/App.js:14-16`, `:36-52`).
**Swap to your stack:** easy. The SDK is touched only in `__init__` (`backend/gemini_client.py:21-23`) and in `_generate_with_retry` (`:128-143`). Map `usage.prompt_tokens` and `usage.completion_tokens` from Groq onto it.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/rate_limiter.py` | Token bucket with continuous refill for RPM and TPM | 22-57, 59-88 |
| 2 | `backend/circuit_breaker.py` | Three-state breaker | 33-78 |
| 3 | `backend/gemini_client.py` | Orchestration: limit, then breaker, then retry, then cost | 43-126, 128-160 |
| 4 | `backend/cost_tracker.py` | Running totals | 27-62 |
| 5 | `config/settings.py` | All knobs (mock default!) | 5-19 |
| 6 | `tests/test_api_client.py` | Unit tests | 18-99 |

### How it works, step by step
1. `POST /api/generate` passes `generation_config` with temperature (default 0.7) and `max_output_tokens` (default 1000) (`backend/main.py:55-64`).
2. It estimates input tokens as `len(prompt) // 4` (`backend/gemini_client.py:60`) and asks the limiter for 1 request plus that many tokens (`:63`).
3. The limiter refills both buckets in proportion to elapsed time, at capacity/60 per second (`backend/rate_limiter.py:59-74`). If either bucket is short, it **returns immediately** with `wait_seconds` (`:43-57`, `:76-88`), and the client sends back `success: False, error: rate_limited` with HTTP 200 (`backend/gemini_client.py:64-73`).
4. In mock mode it sleeps 50–100 ms and invents token counts (`:76-77`, `:162-177`). In real mode it goes through `CircuitBreaker.call` and then `_generate_with_retry` (`:79-83`).
5. Retry: up to 3 attempts. The sync SDK call runs in an executor, so the event loop stays free (`:133-137`). The delay is 0.1 × 2^attempt plus jitter in [0, base), which works out to about 0.1–0.2 s and then 0.2–0.4 s (`:150-152`). Any exception counts as retryable (`:145`).
6. Breaker: it opens after 5 failures in a row (`config/settings.py:14`). After 60 s the next call moves it to half-open, and 2 successes close it again (`backend/circuit_breaker.py:36-44`, `:59-65`). The breaker wraps the whole retry loop (`backend/gemini_client.py:79-83`), so one breaker "failure" is three failed SDK attempts. It takes 15 failed provider calls to open it.
7. Cost uses `usage_metadata` (prompt and candidate token counts) from the response (`backend/gemini_client.py:141-142`, `:86-88`; `backend/cost_tracker.py:27-45`). In real mode the result always has the token keys, so the chars / 4 estimate at `:86-87` is never used, and a missing inner field gives 0 tokens. Whether SDK 0.4.0 (`requirements.txt:7`) has `usage_metadata` at all is UNVERIFIED. If it does not, reading it raises, and the call is retried and then fails.
8. A JSON log line is written at start, completion and failure, each with an 8-character request id (`backend/main.py:9-14`; `backend/gemini_client.py:56`, `:91-95`, `:117-120`).

### README vs code
- "Exponential backoff with jitter" and "Circuit breaker" (`README.md:33-34`): true only when you turn the mock off. The default skips both (`config/settings.py:7`, `backend/gemini_client.py:76-83`).
- "Comprehensive testing" (`README.md:38`): 6 tests, none for retry, half-open recovery or real-mode cost.
- "Edit .env": there is no `.env` here, yet the `Dockerfile` copies one into the image (`Dockerfile:12`). As shipped, `docker build` stops at that line because the file is missing. If you add one, its secrets are baked into the image.

### Where it is thin or wrong
- [shallow] The code sets no timeout on the provider call (`backend/gemini_client.py:134-137`). Whether the SDK applies its own default timeout is UNVERIFIED. A hung call holds a worker thread, and the breaker does not count it as a failure while it hangs.
- [shallow] Retry does not sort errors. A 400 bad request or a safety-blocked `response.text` gets retried just like a 429. The tiny 0.1 s base is far too short for per-minute quotas. No Retry-After.
- [shallow] TPM counts only estimated **input** tokens, never reconciled with real usage, and ignores `max_output_tokens`. Providers count output too.
- [shallow] Half-open lets every concurrent call through, not one probe. After one success it resets `failure_count` to 0, so 4 more failures leave it half-open (`backend/circuit_breaker.py:54-78`).
- [misleading] A throttled request returns HTTP 200 with `success: false` (`backend/main.py:55-65`), so generic 429 handling in clients will not fire.
- [shallow] All state lives in one process's memory. `requests_per_hour` is total divided by uptime (`backend/cost_tracker.py:60`).
- [misleading] Mock calls are booked as real usage. In the default mock mode, the invented token counts go into `CostTracker` (`backend/gemini_client.py:76-77`, `:86-88`), and the reply says `success: True` (`:97-105`). `GenerateResponse` has no mock field (`backend/main.py:35-45`). So the stats panel shows a cost and token total that no provider ever billed, with only a `[MOCK]` text prefix as a clue (`backend/gemini_client.py:167`).
- [shallow] Because the breaker sits outside the retry (step 6), its `failure_threshold` of 5 really means 15 failed calls. Either design is defensible, but the setting's name hides it.

### Tests and data
- The limiter tests check that a fresh bucket has 59 RPM tokens left after one call, and that a third call is throttled at rpm=2 (`tests/test_api_client.py:18-40`). The breaker test checks that it opens after 3 failures (`:42-59`). The cost test re-checks the arithmetic (`:61-75`). The client tests run in mock mode, and "latency > 0" holds only because the mock sleeps (`:9-10`, `:77-87`). No data.

### What to take for your project
- For D2 and LLMOps, this is the most reusable design in the block. Write your own `ragkit/llm.py` with these pieces:
  - one `complete()` function;
  - your record/replay cache in front;
  - a per-call timeout;
  - retry only on 429, 5xx and timeouts, with full jitter and Retry-After honoured;
  - a token bucket sized to your Groq limits that counts input + `max_tokens`;
  - cost from the real `usage`;
  - one JSONL trace line per call (request id, model, prompt version, tokens, latency, cache hit or miss, error class). That trace line also feeds D1.
  - a `mode` field on every result and trace line (live, replay, mock). Leave mock and replay out of cost totals. L6 is the warning here.
- Keep chunk text out of the trace line. Store chunk ids and a prompt hash instead. Then no book text reaches a log file or a tracing service such as LangSmith, which your rules forbid.
- A circuit breaker is optional for a single-user study project. Know it for interviews.

### Try this
- (25 min) On paper, run `RateLimiter` (`backend/rate_limiter.py`) with rpm=30 and tpm=6000, and send 5 calls of 1 500 input tokens 1 s apart. Which call is throttled first, and what `wait_seconds` does it report? Then redo it counting 500 output tokens per call. You will see why counting only input tokens under-throttles.

### Interview angle
- Q: "What is the difference between retry, rate limiting and a circuit breaker?" A: Rate limiting stops you from sending too much. Retry with backoff absorbs short failures on one call. A circuit breaker stops all calls for a while when the provider keeps failing, so you fail fast instead of piling up waits. You need all three, plus a timeout, because without one a hang never counts as a failure.

---

## L7 · Prompting for JSON output  (`lesson7/l7-prompt-json-system/`)

**What the code teaches, in one line:** A JSON-only prompt template, a three-step parse cascade (direct `json.loads`, then regex extraction from fences or prose, then an LLM "repair" call), a basic field check, and counters of which parse step worked.
**What it is not:** It does not use the provider's native JSON mode or schema-constrained output. The README's "Schema validation with Pydantic" is not real: the Pydantic models are defined and never used. The repair loop breaks after its first failure.
**Relevance to your RAG study:** High — concepts: P7, C5 (answer + citations as JSON), M3/code-based evaluators (schema checks) [LLMOps] [Interview]
**Stack:** FastAPI and `google-generativeai>=0.8.0` (`backend/requirements.txt:5`). The model is **whichever model `genai.list_models()` lists first** that supports generateContent (`backend/main.py:144-181`, duplicated at `:302-339`). The key comes from `.env`, and the app refuses to start without it (`:15-20`). The React UI has a prompt and schema tester, two "Test" buttons, and a metrics panel polled every 2 s.
**Swap to your stack:** easy. Replace the two `generate_content` calls. Better still, ask Groq for JSON with `response_format`, and check which modes `openai/gpt-oss-20b` supports.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/main.py` `PromptEngine` | JSON prompt and repair prompt | 94-133 |
| 2 | `backend/main.py` `JSONParser` | Cascade: direct, regex, repair | 183-290 |
| 3 | `backend/main.py` `generate_structured` | Call with 429 handling, parse, validate | 341-460 |
| 4 | `backend/main.py` `_validate_schema` | Type-name check | 462-480 |
| 5 | `tests/test_parsing.py` | Parser unit tests | 11-95 |

### How it works, step by step
1. The prompt is the instruction, then "respond with ONLY valid JSON matching this exact schema", the schema dumped as indented JSON, and five rules: JSON only, no markdown fences, no extra text, all fields required unless marked optional, exact field names. Few-shot examples are optional (`backend/main.py:96-120`). The schema is a dict of field name to type-name string, such as `"age": "int"` (`:559-564`).
2. The call uses `temperature` 0.1 by default (`:52`, `:362-364`) and sets no max tokens. On 429 or quota errors it reads a number following the word "retry" out of the error text and sleeps that long plus 1, or doubles a 1 s delay up to 60 s. Max 3 tries (`:354-394`). On a 404 it rediscovers a model and retries once (`:405-422`).
3. Parse step 1: `json.loads` on the stripped text (`:211-229`).
4. Parse step 2: four regexes in order: a json fence, any fence, one level of nesting, then the first `{…}` (non-greedy). Each match is tried with `json.loads` (`:231-261`). The regexes never match a top-level array. A bare array does pass `json.loads` in step 1, but `ParseResult.data` must be a dict (`:56`), so building the result raises instead of returning (`:214-221`).
5. Parse step 3: up to 3 repair calls. The prompt shows the bad text and the error and asks for corrected JSON, **without the schema** (`:123-133`, `:200-206`). The repair call passes no generation config, so it runs at the provider's default temperature, not the 0.1 used for the first call (`:267-270`). The repair answer is parsed with direct `json.loads` only, with no fence stripping (`:272-273`).
6. Validation lists missing required fields and compares `type(value).__name__` with the schema string (`:462-480`). It only runs when the parsed dict is non-empty (`:434`). Errors are returned but do not change `success`.
7. `/generate` updates success/fail counters and per-step counts (`:527-536`).

### README vs code
- "Schema validation with Pydantic" (`README.md:10`, `:66`): `UserProfile` and `ProductInfo` (`backend/main.py:71-88`) are never used. The real check compares type-name strings.
- "Try the Test: User Profile button … watch real-time metrics update" (`README.md:50-52`): the button calls `/test/user-profile` (`frontend/src/components/PromptTester.js:48`), and that endpoint does **not** update metrics. Only `/generate` does (`backend/main.py:527-536` vs `:555-584`).
- "Direct parse success rate > 90 %, overall > 95 %" (`README.md:78-79`): targets, never measured. `VALIDATION_REPORT.md:60-68` records 2 of 2 parses failed (0 %) and still calls the metrics "updating correctly". `validate_dashboard.py:62` prints PASSED whenever `total_requests > 0`.

### Where it is thin or wrong
- [bug] **Repair loop crash.** When a repair answer is not pure JSON (for example, a fenced reply), the except branch puts the repair *string* into `ParseResult.data`, which is typed as a dict (`backend/main.py:54-60`, `:283-290`). Pydantic raises. The outer handler in `generate_structured` (`:446-460`) then returns FAILED and **replaces `raw_response` with the error text**, so the model's real output is lost. Attempts 2 and 3 never run.
- [bug] **Type check is wrong for real types.** `"List[str]"` never equals `list`, and `"float"` never equals `int` when the model writes `999`. So on every successful parse, `/test/user-profile` reports an `interests` type error (`:473-478`, `:563`).
- [bug] The non-greedy regexes cut deeper nesting at the first `}` outside fences (`:236-237`).
- [misleading] The "API key error" branch fires for any message containing "invalid", such as "Invalid argument" (`:397-402`).
- [misleading] "Free tier allows 5 requests per minute per model" is hard-coded text (`:391`). UNVERIFIED and dated.
- [shallow] The model is chosen by list order, so it varies by account and date (`:159-163`). `JSONParser` and `GeminiStructuredClient` each discover a model, which means two `list_models` network calls at import (`:142`, `:299-300`, `:487`).
- [shallow] The success metric ignores validation errors, so "success rate" is parse rate only.
- [bug] **An empty `{}` passes.** It parses as a success, and validation is skipped because an empty dict is falsy (`backend/main.py:434`). Every required field can be missing, yet `validation_errors` stays empty and the metric counts a success (`:529-530`).
- [shallow] The 404 "try a different model" path calls the same picker again (`:408`). The picker returns the first listed model that it can build (`:319-321`), so it most likely rebuilds the model that just failed.
- [misleading] `avg_parse_time_ms` mixes sub-millisecond local parses with repair steps that include LLM network calls (`:183-209`, `:535-536`). The `parse_times` list also grows without limit (`:535`). Report the two cases apart.

### Tests and data
- The tests cover direct success and failure, a fenced block, an inline object, prompt text containing the schema, few-shot examples, and `parse_with_fallback` on valid JSON (`tests/test_parsing.py:11-95`). Importing `main` (`tests/test_parsing.py:9`) needs `GEMINI_API_KEY` set to some value, or it raises (`backend/main.py:18-20`). Import also builds the client (`:487`), which calls `genai.list_models()`. If that call fails, the error is swallowed and a fixed model name is used (`:169-176`), so whether the tests run offline is UNVERIFIED. Each test's `JSONParser()` calls `list_models` again (`:142`). No test covers repair, nesting, arrays or `_validate_schema`. No data files. `backend/list_models.py`, `find_working_model.py` and `test_model.py` are model-discovery helpers.

### What to take for your project
- For P7 and C5: define your answer contract as a Pydantic model (answer, cited chunk ids, `cannot_answer` flag). Ask Groq for JSON mode. Then validate with `Model.model_validate_json`, which is the code-based evaluator. Add one more check the lesson lacks: every cited chunk id must be one of the ids you actually put in the prompt. That check is the first step towards V1.
- Write tests for the cases the lesson gets wrong, each with the outcome you expect: `{}` and a top-level array must fail validation and be logged as failures; JSON nested 3 levels inside prose must parse; a fenced repair reply must be unfenced and parsed.
- Keep the cascade idea, in your own words: direct parse, then fence extraction, then **one** repair that includes the schema and the validation error, then give up and log. Count which step succeeded per call (an LLMOps metric), and never count a schema-invalid result as a success.
- Keep temperature low for structured output, as the lesson does.

### Try this
- (25 min) Write 6 test strings: plain JSON, fenced JSON, prose + JSON, nested 3 levels outside fences, a top-level array, and trailing-comma JSON. For each, predict which step of `JSONParser` (`backend/main.py:183-261`) succeeds. Then check your predictions against the regexes. Read `:56` before you predict the array case. Note which inputs a Pydantic model would reject that the lesson accepts.

### Interview angle
- Q: "How do you get reliable JSON out of an LLM?" A: Use the provider's JSON or schema-constrained mode when it exists, keep temperature low, validate against a typed schema, and on failure make one repair call that includes the schema and the exact validation error. Track parse-failure rate as a metric. Prompt rules alone ("no markdown") are not enough.

---

## L8 · Agent decision maker (plan → deliberate → execute)  (`lesson8/l8-agent-decision-maker/`)

**What the code teaches, in one line:** A plan-then-execute agent. Gemini writes a JSON plan of tool calls, each step gets an LLM "should I run this?" check, the tools run with retry, and every phase writes a `DecisionTrace` record.
**What it is not:** It is not ReAct. Results never flow into later steps' parameters, the "modified parameters" from deliberation are ignored, and three of the four tools return canned data. When the LLM fails, a regex planner takes over silently.
**Relevance to your RAG study:** Low now (Phase 10 later) — concepts: A5, A1, C6/D1 (trace record) [Interview]
**Stack:** FastAPI, `google-generativeai==0.8.3`, `structlog`. Model `gemini-1.5-flash` (`backend/main.py:244`), with no generation config, so provider default temperature. The key comes from env (`:22-23`). The React UI has a goal box, a tools list, a metrics panel and a "Decision Trace Viewer" that shows **hard-coded** traces (`frontend/src/components/DecisionTraceViewer.js:7-25`).
**Swap to your stack:** easy. The provider call lives in one function, `gemini_json_call` (`backend/main.py:247-282`), plus the setup lines at `:23` and `:244`.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/main.py` tools | Calculator (real), weather/database/search (canned) | 98-232 |
| 2 | `backend/main.py` `gemini_json_call` | Call with 5 s timeout, strip fences, `json.loads` | 247-282 |
| 3 | `backend/main.py` `generate_plan` + fallback | LLM plan, else regex plan | 284-434 |
| 4 | `backend/main.py` `decision_maker` | Main loop and trace records | 541-643 |
| 5 | `tests/test_decision_maker.py` | Tests | 14-50 |

### How it works, step by step
1. The planner prompt lists each tool's name and description, **not its parameters**, plus one calculator example, and asks for `{steps, confidence}` (`backend/main.py:385-412`).
2. `gemini_json_call` wraps the sync call in `to_thread` and `wait_for` with `MAX_DECISION_TIME` = 5 s (`:245`, `:250-253`). The thread keeps running after a timeout. Then it strips fences and parses.
3. On any error or an empty plan, `_generate_fallback_plan` matches keywords (factorial, weather, search, database, add or multiply). If nothing matches it returns "add [1, 2]" with confidence 0.7 (`:284-379`, `:416-422`). The whole planning phase is also capped at `timeout_seconds / 3`, which is 10 s by default (`:557-560`). If the LLM plan has a step with a missing field, `Step(**step)` raises (`:424`), and the whole run ends as failed (`:627-631`).
4. For each step (up to `max_steps`, default 10, stopping after `timeout_seconds` of 30), `deliberate_step` asks the LLM whether to run it. On error it defaults to running it (`:436-470`, `:581-598`).
5. `execute_step` runs the tool with a 10 s timeout and 3 tries, backing off 1 s then 2 s (`:496-539`). Tools return error dicts rather than raising, so only timeouts get retried.
6. The context gets `last_result` (`:605`), but later steps keep their planned parameters. Final output is the last result, and `success = True` whenever the loop finishes (`:615-619`).

### README vs code
- "Tool selection accuracy: 95 %+", "Decision latency < 500 ms per step" (`README.md:79-80`): never measured. Each step costs one extra LLM call for deliberation.
- "Reuses L7's `gemini_json_call()`" (`README.md:35`): L7 has no such function. This one is a simpler fence-strip, with none of L7's cascade.
- "L9 adds Redis + PostgreSQL" (`README.md:87-91`): L9 uses a dict and JSON files.

### Where it is thin or wrong
- [bug] `success` is True even if every step failed (`backend/main.py:612-619`), so `successful_executions` is inflated (`:743-744`).
- [misleading] When the LLM plan fails, an unrecognised goal silently returns 3, from the default "add 1+2" (`:366-372`, `:416-422`).
- [misleading] `modified_parameters` from deliberation is never applied (`:587-601`). The deliberation JSON example mixes in a Python dict repr and a `//` comment (`:449-454`).
- [shallow] The planner never sees parameter schemas, so it has to guess names. A wrong name means `WeatherTool` silently uses "unknown" and returns sunny, 72 (`:141-151`).
- [bug, D4] Factorial has no bound on its input (`:121-125`). The loop is plain CPU work with no `await`, so a huge number blocks the whole server. The 10 s `wait_for` around the tool (`:500-503`) cannot fire, because the event loop never gets control back.
- [misleading] **The trace hides which planner ran.** The planning trace says "Generated plan with N steps" whether Gemini or the regex wrote the plan (`:562-570`). Only a log line records the fallback (`:418`). The response has no field for it either (`:85-92`).
- [shallow] Deliberation writes a trace only when it skips a step (`:589-598`). When it approves a step, or when its LLM call fails and it defaults to "execute" (`:460-466`), its reasoning is not recorded anywhere in the trace.

### Tests and data
- The tests pass **without any LLM**, because "Calculate 5 factorial" hits the regex fallback (`tests/test_decision_maker.py:22-42`; `backend/main.py:290-301`). They show the code runs, not that the LLM planner works. No data.

### What to take for your project
- For C6 and D1: the `DecisionTrace` shape (timestamp, state, reasoning, action, input, output, duration; `backend/main.py:70-77`) is a fair template for your per-query provenance trace: retrieve, then assemble, then generate, then verify. Add what L8 leaves out: a `path` field (llm, fallback, cache replay) on every record, and one record per phase even when the phase "just passed". For retrieval, record the chunk ids, their scores and their source page, so you can trace an answer back to a page.
- Rule to adopt: tests must fail when the LLM path fails. Make fallbacks explicit and assert on which path ran.
- The agent loop itself waits for Phase 10 (A5).

### Try this
- (15 min) Without a key, trace `decision_maker("What is the weather for Paris?")`. Which plan is used? Which `location` string reaches the tool (look at the lower-casing in `:303-309`)? What does the response claim? Count how many outputs look real but are not.

### Interview angle
- Q: "Plan-and-execute vs ReAct?" A: Plan-and-execute writes the whole plan up front, which is cheaper and predictable but cannot adapt to tool results. ReAct decides each step after seeing the last observation, which makes it more adaptive but uses more LLM calls and is harder to bound. Either way, pass observations forward and validate tool arguments against a schema.

---

## L9 · Agent memory (short-term + long-term)  (`lesson9/L9_Agent_Memory/`)

**What the code teaches, in one line:** Two memory tiers: a per-session list capped at 20 messages in a dict, and a per-user JSON file of "facts" searched by substring, with results sorted by recency.
**What it is not:** There is no LLM, no embeddings and no retrieval scoring. Its "keyword search" is not TF-IDF or BM25 (P3). It is a substring test over the JSON text, keys included.
**Relevance to your RAG study:** Low — concepts: P2 and P3 (counter-examples: "keyword search" with no scoring or ranking), X3 (counter-example: history window by count, not tokens), D4 (path traversal, as a warning)
**Stack:** FastAPI and Pydantic only (`backend/requirements.txt`). No provider. The React UI has store and recall forms plus a metrics panel polled every 3 s (`frontend/src/App.js:19-95`).
**Swap to your stack:** easy. There is nothing to swap; adding Cohere embeddings would be new work.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/memory_manager.py` | Both tiers and the counters | 27-55, 57-115 |
| 2 | `backend/api.py` | REST wrappers | 44-91 |
| 3 | `backend/data/users/*.json` | Saved facts | — |

### How it works, step by step
1. `store_message` appends {timestamp, role, content, metadata} to `sessions[session_id]` and keeps only the last 20 (`backend/memory_manager.py:27-46`). `recall_session` returns the last `limit` (default 10) (`:48-55`).
2. `save_to_longterm` reads `data/users/<user_id>.json`, appends {timestamp, fact}, and rewrites the whole file (`:57-82`).
3. `search_longterm` dumps each fact to lower-case JSON and keeps it if **any** keyword is a substring. It sorts by timestamp, newest first, and returns `limit` (default 5) (`:84-111`). With no keywords it returns the newest entries (`:99-100`).

### README vs code
- "In-memory dict (< 10 ms retrieval)" (`README.md:32`): never measured.
- "Keyword search capability" (`README.md:37`): substring match with no relevance ranking.

### Where it is thin or wrong
- [bug, D4] `user_id` goes straight into a file path, so `../` can write outside the data folder (`backend/memory_manager.py:60`, `:90`).
- [shallow] The read-modify-write has no lock and no atomic write (`:62-77`). As shipped, one process runs this sync code on the event loop (`backend/api.py:61-64`, `:99`), so two requests cannot interleave. Run several workers or processes and one write can be lost.
- [misleading] `short_term_hits` and `long_term_hits` go up on every call, even with nothing found. They count calls, not hits (`:50`, `:86`).
- [shallow] Keys are searched too, so "level" matches every skill fact. Duplicates are never merged. `demo_user.json` holds 11 entries, mostly the same 3 facts repeated by re-runs of `demo.sh:22-30`.
- [shallow] The 20-message window is by count, not tokens (`:42-43`). Nothing summarises older messages.
- [bug] `recall_session` with `limit=0` returns the whole window, not nothing, because a slice from `-0` starts at the beginning (`backend/memory_manager.py:54`). Negative limits are not rejected either (`backend/api.py:55-56`).
- [misleading] A silent fallback that reports success: if a user's JSON file is corrupt or unreadable, `search_longterm` prints the error and returns `[]` (`backend/memory_manager.py:113-115`). The API then answers `success: True` with zero results (`backend/api.py:69-77`). "No memory found" and "memory store broken" look the same.
- [shallow] Under Docker the working folder is `/app` (`Dockerfile:3`, `:17`), so data goes to `/app/data/users`, mounted from `./data` (`docker-compose.yml:9`). A local run starts from `backend/` (`start.sh:5-7`), so it uses `backend/data/users`. The two runs keep separate stores, and Docker never sees the sample files.

### Tests and data
- `test.sh` greps curl output for words like "success" and "pizza" (`test.sh:14-58`). The JSON files are toy facts and useless as RAG practice data.

### What to take for your project
- Skip the code. Keep two ideas: (1) for a chat front-end on ragkit, the history goes into your token budget (X3), so cap it by tokens and condense the follow-up into a standalone query. (2) "Search" without a scoring function is not retrieval. Compare it with your BM25 (P3) to see what ranking adds.

### Try this
- (10 min) For `demo_user.json`, predict the results of `search_longterm` with keywords ["python"], then ["level"], then ["a"]. Then write down what BM25 would do differently with the same facts.

### Interview angle
- Q: "How do you add conversation memory to RAG?" A: Keep recent turns within a token budget, rewrite the new question into a standalone query using that history, and retrieve with the rewritten query. Store long-term facts with embeddings and metadata so you can rank and filter them, and dedupe on write.

---

## Block summary
| Lesson | Title | Relevance | Concepts | Best file to read | Biggest problem |
|---|---|---|---|---|---|
| L1 | Python setup | None | none | `src/validate_environment.py` | Leaked key in `.env.example:2`; silent pip installs (`../setup.sh:169-173`) |
| L2 | Async, decorators, Pydantic | Medium | D2, P1 (minor) · LLMOps · Interview | `backend/app/main.py:77-211` | Retry never fires in default mode; fallback and error strings cached and counted as success, always HTTP 200 (`main.py:169-189`, `:113-115`, `:205-207`) |
| L3 | Transformer deep dive | Medium | P1, P4 (counter) · Interview | `backend/app/transformer.py:37-183` | Real attention math on random, token-blind inputs (`transformer.py:365-368`) with dropout at inference (`:76-77`); its own sum-to-1 test fails |
| L4 | LLM parameters (specs/cost/context) | Medium | P1, D2 · LLMOps · Interview | `backend/main.py:112-157` | Unsourced "7B/70B" specs, UNVERIFIED (`main.py:26-46`); "context savings" fallacy (`:273`) |
| L5 | Model comparison | Low | M4 (counter), D2, A1 (counter) · LLMOps · Interview | `services/analytics_engine.py:51-78` | API errors become random latencies with success True (`model_client.py:59-88`); MMLU and comparisons hard-coded |
| L6 | Production LLM client | High | D2, D1 · LLMOps · Interview | `backend/gemini_client.py` + `rate_limiter.py` | Mock on by default bypasses breaker and retry and books invented tokens as cost (`settings.py:7`, `gemini_client.py:86-88`); no timeout, no error classification |
| L7 | Prompting & JSON output | High | P7, C5, M3 · LLMOps · Interview | `backend/main.py:94-290` | Repair loop crashes and loses raw output (`main.py:283-290`, `:446-460`); `{}` passes unvalidated (`:434`); type check always fails on `List[str]` (`:473-478`); Pydantic unused |
| L8 | Agent decision maker | Low | A5, A1, C6/D1 · Interview | `backend/main.py:541-643` | `success=True` even when all steps fail (`main.py:612-619`); regex fallback is invisible in the trace (`:562-570`) and makes tests pass with no LLM |
| L9 | Agent memory | Low | P2, P3, X3 (counters), D4 | `backend/memory_manager.py` | Path traversal via `user_id` (`memory_manager.py:60`); "search" is substring + recency; corrupt file returns `success: True` (`:113-115`) |

### Cross-lesson patterns
- **No retrieval anywhere in this block.** No backend `.py` file in L1–L9 chunks text, calls an embedding model, builds a vector index or computes a retrieval metric. A search for embed, chunk, vector, cosine, BM25, rerank and retriev finds only L3's random `create_embeddings` (`lesson3/…/backend/app/transformer.py:365-368`) and L9's `retrievals` call counter (`lesson9/…/backend/memory_manager.py:24`). So chunk units, distance versus similarity, and lost page numbers do not come up here. This block is about the LLM-call layer around a RAG system, not RAG itself.
- **Traces and replies that hide which path ran.** L2 returns fallback and error strings as normal results. L5 drops its `simulated` flag. L6 has no mock field. L8's plan trace does not say the regex wrote the plan. Rule for your `ragkit`: every result and every trace record carries a `mode`/`path` field, and your metrics filter on it.
- **Shared leaked key (D4).** One Google key is hard-coded in `lesson1/…/.env.example:2`, `lesson2/…/backend/app/main.py:144`, `lesson3/…/backend/app/config.py:4` and `docker-compose.yml:11`, `lesson4/…/backend/main.py:21`, and the `setup.sh` of L1–L5 and L8. All 13 copies are the same key (compared by hash, value not shown). L7's notes say the key it used was "reported as leaked" and is no longer valid (`lesson7/…/STATUS.md:21-23`, `API_KEY_SETUP.md:4`). L7 reads its key from a `.env` that is not in the repo, so whether that is this same key is UNVERIFIED. If it is, the hard-coded-key lessons cannot run as shipped. Either way, any number they claim to have produced is UNVERIFIED.
- **Fallbacks that hide failure.** L2's `[DEMO]` strings counted as success (`main.py:169-189`). L5's random latencies with `success: True` (`model_client.py:59-88`). L6's mock mode on by default (`settings.py:7`). L8's regex plan and "add 1+2" default (`main.py:284-379`). Fake panels in the browser: L3 `PerformanceMetrics.js:23-38` (random), L8 `DecisionTraceViewer.js:8-25` (hard-coded). Rule for you: label every fallback and keep it out of the metrics.
- **Four token counters.** Real `count_tokens` (L4 `main.py:199`, `:253`). Words × 1.3 (L4 `main.py:203`; L5 `model_client.py:47-48`). Chars / 4 (L6 `gemini_client.py:60`). Real `usage_metadata` (L6 `gemini_client.py:141-142`; support in the pinned SDK is UNVERIFIED). Only the real ones belong in cost or budget code.
- **Retry done three ways, none complete.** L2's decorator never sees errors in default mode (`main.py:184-189`). L6 retries everything, with a 0.1 s base and no timeout (`gemini_client.py:128-160`). L7 sleeps on a number regex-scraped from the error text (`main.py:377-381`). None honours a Retry-After header or sorts errors into retryable and not.
- **p95 from 3–5 samples** (L4 `main.py:216`; L5 `benchmark_service.py:66`). Meaningless, and the default quantile method can extrapolate past the largest sample.
- **Sync SDK calls in `async def`** block the server (L4 `main.py:175`; L3's CPU-bound forward). L5–L8 fix it with `to_thread` or `run_in_executor`.
- **Hand-typed price and spec tables that disagree** (L4 `main.py:24-55` vs L5 `main.py:57-89` and `model_client.py:99-103`). The 2.0 Flash prices differ, and L4 says "7B"/"70B" where L5 says "Unknown". The 1.5 prices agree once you convert units. None cites a source. The only dates are "May 2025" (L4 `main.py:23`) and "as of 2025" (L5 `model_client.py:98`). All prices UNVERIFIED. Several model ids (`gemini-pro`, the 1.5 family, `gemini-2.0-flash-exp`) are old; whether they are still served is UNVERIFIED.
- **Smoke scripts that pass too easily.** L4 `test.sh:8-23` always ends "All tests passed!". L5 `scripts/test.sh:44-61` passes after warnings, though it does stop on a dead backend (`:29-42`). L7 `validate_dashboard.py:62`, which passes at 0 % success, and `VALIDATION_REPORT.md:60-68`.
- **Global in-memory metric dicts** that reset on restart and are not locked (L1 `app.py:17`; L2 `main.py:65`; L7 `main.py:490`; L8 `main.py:677`). Fine for demos. For you, append JSONL trace lines instead, which LLMOps can read later.
- **What is genuinely reusable:** L6's limiter, breaker and cost pattern; L7's parse cascade, once fixed; L4's cost formula; L5's Pareto check; L3's attention formula; L8's trace-record shape. Re-write each in your own words. Do not copy.
