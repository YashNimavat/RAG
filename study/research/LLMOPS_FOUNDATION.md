# LLMOps foundation for the RAG course (research Session 0)

**What this is:** the shared LLMOps design that every phase session (1–12) applies. It covers caching and replay, tracing, datasets, evaluators, cost, versioning, local CI and the framework rules. Researched 2026-10-17 by Claude (Opus 5.5) from primary sources: provider docs, library source code and PyPI.
**What this is not:** code, lessons or notebooks. Nothing in the course was changed, nothing was installed, and no API was called. The helper package in §10 is a plan only.

**How it was checked.** One multi-agent web search with 3-vote adversarial checks covered caching, provider errors and Groq seeds. Four follow-up agents opened the provider docs, GitHub source and PyPI JSON for everything else. Claude model ids and prices come from the `claude-api` skill (price table cached 2026-10-06). Facts that no one could confirm are labelled **UNVERIFIED**. All web facts are external and dated 2026-10-17. Prices and limits change, so re-check them before any paid run.

---

## Summary (read this first)

**The 5 most important findings**
1. **The course must own its cache.** LangChain's built-in caches cannot be the replay layer.
   - Its LLM cache is never used by `stream()`/`astream()`. LangChain's docs say so, and the source confirms it.
   - Its chat cache key is built from LangChain's own serialisation of the model, which we do not control.
   - `CacheBackedEmbeddings` leaves the model id out of the key unless you pass it, uses SHA-1 by default, and does not cache queries.
   - So one small course-owned cache (§2), keyed on provider + exact model + all parameters + full input, sits under every call. LangChain reaches it through two small adapter classes.
2. **"Out of credits" has no single error code.**
   - Claude has three. The tier spend cap is a **429** with no `retry-after` and `error_code = enforced_spend_limit_reached`. A spend limit you set yourself is a **400**. A payment problem is a **402**.
   - On Groq, a spend limit is a **400 `blocked_api_access`**.
   - On Cohere it is a **402**.
   - SDKs retry 429s quietly (Anthropic: twice by default), so a naive loop wastes calls on an exhausted account. §2.5 gives the full detection table and the automatic switch to replay.
3. **Nothing makes a hosted model repeat itself exactly. Replay is the only guarantee.**
   - Groq and Cohere call `seed` "best effort" only.
   - Server batching changes the arithmetic, so even temperature 0 can vary (Thinking Machines Lab, 2025).
   - The current Claude models reject `temperature` with a 400, so they cannot be set to 0 at all.
4. **The official LangChain integrations conflict with our pinned SDKs.**
   - `langchain-groq` 1.1.3 needs `groq<1.0`; the project has `groq` 1.7.0.
   - `langchain-cohere` 0.6.0 needs `cohere<6`; the project has 7.2.0.
   - The adapters from finding 1 avoid both packages. Only `langchain-core`, `langgraph` and `langchain-text-splitters` are needed (§9, decision 1).
5. **Groq's free-tier limits shape every plan.**
   - `openai/gpt-oss-20b` is listed at 30 requests/min, 1K requests/day, 8K tokens/min and 200K tokens/day. Which plan this row belongs to is **UNVERIFIED**.
   - One v0 run (55 questions × about 2,000 tokens) then needs at least 14 minutes and about half a day's token quota. A client-side token throttle and resumable runs are required, not optional.

**Tools to add** (details in §11; install nothing yet):
- `langchain-core`, `langgraph`, `langchain-text-splitters` and `langsmith`: the framework track that D-32 allows.
- `anthropic`: Claude calls, when Yash has credits.
- `arize-phoenix-otel` plus the OpenInference instrumentors: local tracing.
- The Phoenix server itself is run with `uvx`, outside the project lock, because it pulls 54 dependencies.
- `pre-commit` and `nox`: local CI.
- `judgy`: judge-error correction in the D-10 end batch.
- `pytest` is already present.

**Decisions Yash must make** (each answerable in a word):
1. LangChain integration route: **adapters** over our cache (recommended), or the official `langchain-groq`/`langchain-cohere` in a second environment?
2. Should the response cache be committed to git? **No** is recommended: it stays git-ignored, with an export command for backups.
3. Create a free LangSmith account, for climate-PDF notebooks only? **Yes** is recommended.
4. Run Phoenix locally as the trace viewer? **Yes** is recommended.
5. Get a Cohere **production** key before the D-10 end batch, since trial keys are capped at 1,000 calls a month? **Yes** is recommended.

**Size of the build work** (plan only):
- Helper package `study/llmops/`: **M**. That is about 9 small modules plus tests; the hardest parts are the cache and the error classifier.
- LangChain adapters: **S**.
- Local CI wiring: **S**.
- Monitoring page: **S**.

---

## 1. The lifecycle for this course

### 1.1 Two loops

- **Analyze → Measure → Improve** (`evals-foundations`). Read traces and name the failures (`error-analysis`, `trace-data-analysis`). Turn them into checks (`code-based-evaluators`; `llm-as-judge` and `judge-validation` only in the D-10 end batch). Fix one thing, then re-measure (`improving-llm-agents`). The loop never ends, because every fix moves the failure mix.
- **dev → CI → monitoring** (`ci-cd-evals`). In a notebook, try the idea on dev items. In local CI, a fixed golden set must not regress on any commit. In monitoring, watch real use and feed new failures back into the golden set. Here "real use" means the apply-it tools on Yash's own documents, plus a scheduled canary (§8.4).

The course already has the pieces for both loops: the version cards, the trace schema (06 §2.5), the run registry (06 §9.1), and the T1/T2 test tiers (06 §9.6). LLMOps adds no new loop. It wires these pieces to tools and keeps every call replayable.

### 1.2 Mapping onto the version cards (06 §4.2)

| Version | Analyze | Measure | Improve | dev → CI → monitor | Skills |
|---|---|---|---|---|---|
| v0 baseline | First traces of every query (D1 starts here) | none yet | none | dev only; traces in JSONL | `llm-observability` |
| v0.1 harness | Failure buckets on v0 traces (M5) | CE@k, Hit@k, MRR, nDCG; deterministic answer checks; ≥ 30 human labels | Chooses which v1–v3 cards to run | Golden set frozen; T1 suite starts | `error-analysis`, `rag-evaluation`, `collaborative-annotation`, `synthetic-data-generation` |
| v1.x indexing | Chunk-level failures (dilution, fragmentation, truncation) | Retrieval metrics at fixed k **and** equal token budget | One chunking variable | Retrieval regression test per champion | `rag-evaluation`, `trace-data-analysis` |
| v2.x retrieval | "Right doc, wrong rank" from Hit@20 vs Hit@4 | Retrieval metrics + p95 latency | Hybrid, rerank, filter, MMR | Cohere rerank calls cached; latency budget test | `rag-evaluation`, `improving-llm-agents` |
| v3.x query side | Vocabulary-mismatch and multi-hop failures | CE@4 per category; LLM calls and cost per query | Rewrite, HyDE | Every LLM rewrite cached; cost guard | `improving-llm-agents`, `code-based-evaluators` |
| v4.x context | Evidence lost during assembly | CE on the final context; human answer labels | Window, budget, compression | Token-budget test | `rag-evaluation` |
| v5.0 grounding | Unsupported claims, bad citations, false answers | Citation page-hit, abstention F1 (deterministic); human labels | Verification, abstention gate | Abstention regression (T2) | `code-based-evaluators`, `llm-as-judge` (end batch only) |
| v6.0 production | Regression causes | Budgets per stage; flip rate | Tracing, budgets, CI | Full local CI + monitoring page | `ci-cd-evals`, `llm-observability`, `safety-evals` |
| v7.0 control flow | Grader/router errors | Controller accuracy against hand labels | CRAG or routing (LangGraph) | Every branch in the trace | `tool-use-evaluation`, `multi-turn-evaluation` |
| v8 / K1 | Multi-hop and global questions | Index-build calls and cost | Graph RAG or RAPTOR | Rebuild cost tracked | `trace-data-analysis` |
| End batch (D-10) | none | Cohere judge over stored traces; TPR/TNR; corrected rates | Revise provisional decisions | One cached batch | `llm-as-judge`, `judge-validation` |

---

## 2. Response caching and replay (top priority)

### 2.1 Why the course owns the cache

| Option | What we found | Verdict |
|---|---|---|
| LangChain `set_llm_cache` (InMemory or SQLite) | `stream()`/`astream()` never read or write it. The key is `dumps(messages)` plus `_get_llm_string`: the serialised model JSON plus sorted call parameters. On a hit, the stored `usage_metadata` is kept and the cost is set to 0, with no "cached" flag. `SQLiteCache` round-trips through `dumps`/`loads`. Whether `tool_calls` survive that round trip is **UNVERIFIED**. | Useful for showing how frameworks cache; not the replay layer. |
| `CacheBackedEmbeddings` (now in `langchain-classic`) | `namespace` defaults to `""`, so two models share keys unless you pass the model id. The key encoder defaults to SHA-1, and LangChain itself warns it is not collision-resistant. `query_embedding_cache` defaults to False. | Not used. The C3 cache already does this correctly (§2.6). |
| HTTP cassettes (VCR.py / pytest-recording) | They record HTTP traffic. vcrpy supports `httpx`. The `anthropic` SDK has used **`httpx2`** since 1.0.0 (2026-08-20), and tools that patch `httpx` do not see its requests. Groq 1.7.0 and Cohere 7.2.0 still use `httpx`. Whether vcrpy can intercept `httpx2` is **UNVERIFIED**. | Optional for tests of Groq and Cohere wiring; not the cache. |
| **A course-owned cache at the SDK-call level** | We control the key, what is stored, the three modes and error handling. It works the same for plain Python and for LangChain (through adapters). | **Chosen.** |

### 2.2 What gets cached

Every external call is cached. That means every LLM call (Groq and Claude), every embedding call (Cohere), every rerank call (Cohere), and every call made through LangChain or LangGraph, via the adapters in §9.3. Local models (MiniLM, the ms-marco cross-encoder) are not API calls. Their outputs are still cached by content where that saves time, as C3 does for embeddings.

Rule: **no external call goes around the cache.** A helper refuses to build a raw client when cache mode is `replay`. Calls made only to measure variance (flip rate, 06 §8.5; generator flip rate, review §4 M4) go through the cache in `record` mode, which adds a new sample instead of overwriting (§2.4).

### 2.3 The cache key

The key is the SHA-256 of one canonical JSON object. Canonical means `sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=False` and UTF-8 bytes.

```text
key = sha256(canonical_json({
  "key_version": "k1",            # bump to invalidate every entry on purpose
  "provider":    "groq" | "anthropic" | "cohere",
  "endpoint":    "chat" | "embed" | "rerank",
  "model":       "<exact requested id>",        # e.g. "openai/gpt-oss-20b", "claude-haiku-5-5"
  "params":      { every request parameter actually sent, after normalisation },
  "input":       messages (chat) | texts + input_type (embed) | query + documents (rerank),
  "tools":       [...] or null,                  # full tool schemas
  "response_format": {...} or null               # json_object / json_schema
}))
```

How parameters are normalised (from the provider facts below):
- **Always send every parameter that changes the output, and put it in the key.** Never rely on a server default. Groq's `reasoning_effort` defaults to `medium` when omitted. Claude Haiku 5.5 and Opus 5.5 default to effort `medium`. Cohere's chat temperature defaults to 0.3.
- **One name per idea.** Groq has deprecated `max_tokens` in favour of `max_completion_tokens`. Its default of 1,024 may be too low for reasoning. Store the field under the name actually sent; the course should switch to `max_completion_tokens` (Errors E3).
- **Leave out of the key** anything that cannot change the answer: the API key, timeouts, `max_retries`, the user agent, `n` (always 1). Streaming is never used through the cache.
- **Claude:** current models reject `temperature`, `top_p` and `top_k` with a 400. Their keys therefore hold `output_config.effort` and the `thinking` setting instead of a temperature.
- **Model id:** the key uses the id that was *requested*. The id the provider *returned*, and Groq's `system_fingerprint`, are stored next to the response. A silent backend change then shows up in the stored data without breaking replay.

**Embeddings keep the C3 key**, `sha256(provider|model_id|revision|input_type|preproc_version|text)` (C3 D.4), so existing cached vectors stay valid. One field must be added. Cohere `embed-v4.0` can return 256, 512, 1024 or 1536 dimensions, plus several `embedding_types`. The output dimension and type must go into the key, folded into `preproc_version` or as new fields (Errors E2).

**Never cache by similarity.** An answer must not be reused for a "similar" question, because paraphrase variants would get their base item's answer (review §5, AIQ `16_semantic_cache.py`). Keys are exact.

### 2.4 What gets stored, and where

**Storage:** one SQLite file, `rag_learning/.cache/llmops/calls.sqlite`.
- SQLite over JSONL because it writes atomically, finds a key quickly with an index, survives a crash in the middle of a run, and is one file.
- A `cache export` command writes JSONL (gzip) for reading, diffing and backup.
- Embedding vectors stay in C3's `.npy` store. The SQLite file holds one metadata row per embedding API call.

| Column | Content |
|---|---|
| `key`, `sample` | Primary key. `sample` 0 is the canonical answer; `record` mode adds 1, 2, … for variance runs |
| `provider`, `endpoint`, `model_requested`, `model_returned`, `system_fingerprint` | Identity and backend drift |
| `request_json` | The canonical request: everything in the key, minus secrets |
| `response_json` | The full provider response (`model_dump()`), including reasoning text when returned |
| `usage_json` | Input, output, reasoning and cached tokens as reported. Groq: `completion_tokens_details.reasoning_tokens`, `prompt_tokens_details.cached_tokens`, `queue_time`, `total_time` |
| `cost_usd`, `price_table_version` | Cost at record time, from `prices.json` (§6) |
| `latency_ms`, `http_attempts` | Wall time and the number of HTTP attempts (SDK retries off, §2.5) |
| `created_utc`, `run_id`, `notebook`, `status` | Provenance; `status` is `ok`, `error` or `refused` |
| `input_source` | `corpus:D`, `corpus:T`, `learner-docs` or `synthetic`. Book sources cannot appear, because the guard below blocks them |

**Committed or git-ignored? Git-ignored** (decision 2). `.cache/` is already ignored (D-16).
- The cache holds corpus text and possibly Yash's own documents (apply-it tools). The corpus licences are unclear (D-16), and the file grows without limit.
- Replay still survives: `cache export --notebook <name>` writes a replay pack to a backup folder outside git, and `cache import` restores it.
- A small committed **manifest** (`study/llmops/replay_manifest.json`: notebook → keys needed) lets CI say exactly which keys are missing.

**The book-text guard (privacy rule, D-32 (5)).** Before any external call, `privacy.py` checks the input against locally stored fingerprints of the two books: hashed 8-word shingles, so no book text is stored. It refuses on a match (`status = refused`). This works in every mode, and also guards trace export (§3). It complements, and does not replace, the rule that book PDFs are never inputs to an LLMOps notebook.

### 2.5 The three modes, and detecting "no credits"

The mode comes from `LLMOPS_CACHE_MODE`; the default is `auto`. CI and the replay test always use `replay`.

| Mode | On a hit | On a miss |
|---|---|---|
| `record` | Calls anyway and stores a new sample. Sample 0 is kept, unless `--overwrite` is given for a deliberate re-record | Calls and stores |
| `replay` | Serves sample 0 | **Never calls.** Raises `ReplayMiss` with the provider, model, key prefix, notebook and the command to record it |
| `auto` | Serves sample 0 | Calls only if a key exists **and** the provider is not marked exhausted. Otherwise it behaves like `replay` |

**Retries are made visible.** Each SDK client is built with `max_retries=0`. The Anthropic default is 2, with backoff from 0.5 s to 8 s that honours `retry-after`. Our layer does the retries instead, so every attempt is counted and logged and an exhausted account is never retried.

**Error classifier** (provider docs, read 2026-10-17):

| Provider | Signal | Meaning | Action |
|---|---|---|---|
| Anthropic | 429 `rate_limit_error`, **no `retry-after`**, `error.details.error_code = "enforced_spend_limit_reached"` | Tier monthly spend cap reached | **Exhausted** until 00:00 UTC on the 1st of next month |
| Anthropic | 400 `invalid_request_error`, message starts "You have reached your specified API usage limits" (or "workspace API usage limits") | A spend limit Yash set | **Exhausted** |
| Anthropic | 402 `billing_error` | Billing or payment problem | **Exhausted** |
| Anthropic | 429 with `retry-after`; 529 `overloaded_error`; 5xx; connection error | Transient | Wait (`retry-after`, or exponential backoff with jitter); at most 3 attempts |
| Anthropic | 401 / no key | No credentials | `auto` acts as `replay` |
| Groq | 400 with code `blocked_api_access` | Organisation spend limit | **Exhausted** |
| Groq | 429 with a short `retry-after` | Per-minute limit (RPM/TPM) | Wait `retry-after` |
| Groq | 429 where `x-ratelimit-remaining-requests` is 0, or `retry-after` is above 120 s | Daily quota (RPD/TPD) used | **Exhausted** until `x-ratelimit-reset-requests` |
| Groq | 498 | Flex tier full (`service_tier=flex` only; not used) | Wait |
| Groq | 413 | Request too large | Fail; do not retry |
| Cohere | 402, "Maximum billing reached" (SDK: generic `ApiError`, `status_code` 402) | Billing cap for the key | **Exhausted** until next month |
| Cohere | 429 `TooManyRequestsError` | Per-minute limit; trial keys are also capped at 1,000 calls/month | Wait; if it repeats after 3 backoffs, mark **exhausted**. The monthly-cap error is **UNVERIFIED** |
| Cohere | 498 `InvalidTokenError` / 401 | Bad key | `auto` acts as `replay` |

"Exhausted" is written to a `provider_state` table with a reset time. `auto` then serves the rest of the run from the cache. On a miss it stops with a clear message, for example: "Groq daily quota used; 12 calls missing; rerun after 00:00 UTC or use `replay` with a recorded pack." The run's trace notes the switch.

Proactive throttle: a client-side token bucket per provider and model, set from the limits in `prices.json` (Groq gpt-oss-20b: 30 RPM / 8K TPM, plan **UNVERIFIED**; Cohere trial Command A: 20 req/min, rerank 10 req/min, embed 2,000 inputs/min). Before a run, the planner estimates calls and tokens. It refuses a run that would exceed the daily quota, unless `--allow-partial` is given, because runs resume by skipping items already in `results.jsonl` (06 §8.6).

### 2.6 How LangChain's cache fits, and the C3 embedding cache

- **LangChain:** notebooks call LangChain through two adapters (§9.3). `CachedChatModel` is a `BaseChatModel` and `CachedEmbeddings` is an `Embeddings`; both route to `llmops.cache`. LangChain's global cache stays **off** (`set_llm_cache(None)`) so that two caches never disagree. One teaching cell turns `SQLiteCache` on, to show its key and its streaming gap.
- **C3's embedding cache:** it is already content-keyed and model-aware, which is better than LangChain's default. It stays as the vector store. `CachedEmbeddings` reads and writes it, and adds the missing output-dimension field (E2). C3's `embed_hash` (the index folder name) is unchanged. The SQLite row per Cohere call adds usage, cost and latency, which C3 did not record.

### 2.7 Determinism: what replay guarantees and what it does not

- **Groq:** `temperature` 0–2 (default 1). The `seed` gets a "best effort" to sample deterministically; "determinism is not guaranteed". `system_fingerprint` identifies the backend configuration.
- **Cohere chat:** temperature is non-negative (default 0.3); seed is best effort.
- **Claude** (current models): sampling parameters are removed, so the variation is controlled only by `effort` and `thinking`.
- **Why temperature 0 still varies on a server** (Thinking Machines Lab, Horace He et al., 10 Sept 2025):
  - **The study:** Qwen3-235B at temperature 0, with the same prompt sent 1,000 times.
  - **The result:** 80 different completions, the first difference at token 103. Batch-invariant kernels made all 1,000 identical, at roughly 1.6–2× the run time.
  - **What it means:** the cause is not "GPU parallelism" in general. The numbers for a request depend on how many other requests share its batch, and server load changes that.
  - **For this project:** answers from Groq and Cohere can differ between runs even at temperature 0.
- **Reasoning models add a second source.** `gpt-oss-20b` writes reasoning tokens before the answer, so a small early difference can change the whole reply. It also spends output budget: `finish_reason = length` with an empty answer is a known failure (C5 D.6).
- **What replay guarantees:** an identical request returns a byte-identical stored response, forever and offline. That makes notebook outputs, metrics and plots repeatable.
- **What replay does not guarantee:** that the model would answer the same way today, or that a changed prompt would behave the same (it is a cache miss). "Replay passes after a prompt edit" proves only that the unchanged paths reproduce (review §5, AIQ 07 Q50).
- **Model variance is measured, not assumed.** The generator flip rate (M4 lab) and the judge flip rate (06 §8.5) use `record` mode with `sample = 1, 2`.

### 2.8 How cached traces feed the D-10 end-of-course judge batch

1. Every experiment stores its answers in `results.jsonl` traces (06 §2.5) with the LLM `cache_key`. The answer text is therefore recoverable from the trace **and** from the cache.
2. The end batch reads the stored traces of every judged version. It never regenerates them, so the judge sees identical inputs (D-10).
3. Judge calls go through the same cache with the 06 §8.6 key, extended to the §2.3 schema. The judge prompt version goes into `params`, so a prompt change is a new key.
4. The variance run (06 §8.5) uses `record` mode with sample 1. The flip rate is computed by comparing samples 0 and 1.
5. `judge-validation` statistics (TPR/TNR, corrected success rate with a bootstrap CI via `judgy`, plus 06 §8.4's failure-class recall and κ lower bounds) run offline on the stored labels.
6. **Budget check:** about 165 judge calls per judged version (06 §8.6). Three or four versions plus a variance run is about 700–1,000 calls, close to Cohere's **trial** cap of 1,000 calls a month. Hence decision 5.

---

## 3. Tracing

### 3.1 The options

| | Plain JSONL (06 §2.5) | Arize Phoenix (local) | LangSmith (hosted) | Langfuse (self-hosted) |
|---|---|---|---|---|
| Runs offline | Yes | Yes. No account; port 6006 | No | Yes, but needs Docker |
| Cost | $0 | $0 | Free plan: 1 seat, 5k base traces/month, hard cap with no card; base traces kept 14 days | $0 software; host needs ≥ 4 cores / 16 GiB |
| Licence | ours | **Elastic License 2.0** (source-available; fine for personal use) | Proprietary service; SDK MIT | Core MIT, `ee/` separate |
| Weight | none | Server: 54 direct deps (pandas, pyarrow, grpcio, fastapi…). Client (`arize-phoenix-otel`): 9 deps | SDK only | Postgres + ClickHouse + Redis + S3/MinIO |
| LangChain | via callback or adapter | `openinference-instrumentation-langchain` | native | `langfuse.langchain.CallbackHandler` |
| Groq / Anthropic | adapter spans | OpenInference instrumentors exist for both | `wrap_anthropic`; `@traceable` | `@observe` |
| Hiding text | we choose the fields | `OPENINFERENCE_HIDE_INPUTS`, `HIDE_OUTPUTS`, `HIDE_RETRIEVAL_DOCUMENTS`… | `LANGSMITH_HIDE_INPUTS/OUTPUTS`, `hide_inputs` callables, `create_anonymizer`, applied before upload | `mask_otel_spans` |
| Datasets / experiments | our runner | yes | yes | yes |

### 3.2 Choice

- **Default, always on: the plain JSONL trace** (06 §2.5, D-18), extended with OpenInference-style span records so other tools can read it (§3.3). It works offline, costs nothing, and book text cannot leave the machine.
- **Local viewer: Phoenix**, run as a separate process (`uvx arize-phoenix@20.19.0 serve`). Its heavy dependencies then stay out of `uv.lock`. Set `PHOENIX_WORKING_DIR` to a git-ignored folder, `PHOENIX_TELEMETRY_ENABLED=false` and `PHOENIX_ALLOW_EXTERNAL_RESOURCES=false`. The project itself installs only `arize-phoenix-otel` plus the instrumentors. Phoenix's default SQLite location is documented inconsistently (**UNVERIFIED**), so check the path printed at start-up.
- **Hosted: LangSmith, climate-corpus notebooks only** (decision 3). Tracing is off unless `LANGSMITH_TRACING=true`; an unset variable means off.
  - **Never** put `LANGSMITH_TRACING=true` in `.env`.
  - A notebook turns it on inside `tracing_context(enabled=True)`, and only after `privacy.assert_corpus_is("D")` passes.
  - `LANGSMITH_HIDE_INPUTS` stays available as a second layer.
  - Pick the EU or US endpoint once and record it (`LANGSMITH_ENDPOINT`).
- **Not chosen: self-hosted Langfuse.** It needs Docker plus four services and 16 GiB on a CPU laptop. It is worth revisiting only if Docker becomes normal for Yash.
- **The trace store never sends anything itself.** Export to Phoenix or LangSmith is a separate step, and `privacy.py` filters it again.

### 3.3 What every trace must capture (`llm-observability`, 06 §2.5, OpenInference / OTel GenAI)

| Span | Fields |
|---|---|
| Run (root) | `run_id`, `qid`, `config_hash`, `index_manifest_hash`, `dataset_sha256`, `snapshot_id`, `split`, `cache_mode`, git commit, timestamps |
| Query transform (LLM) | original and transformed queries, `prompt_version`, `cache_key` |
| Embedding | provider, model, `input_type`, dimension, number of texts, cache hits and misses |
| Retriever | per retriever: ranked `chunk_id`, `doc_id`, page, score, rank (OpenInference `retrieval.documents` id + score) |
| Reranker | input ranks, output ranks, scores, model |
| Context | chunk ids, context tokens, tokenizer, truncated chunks |
| LLM | provider, model requested and returned, `system_fingerprint`, every sent parameter, prompt sha256, tokens (input / output / reasoning / cached), `finish_reason`, latency (+ Groq `queue_time`), cost, `cache_hit`, `cache_key`, `http_attempts` |
| Controller (v7) | grade or route decision, its input, retries, branch taken |
| Errors | classified error (§2.5), and whether the run switched to replay |

**Content rule.** The OTel GenAI conventions are still "Development" status, have moved to a new repository, and say message content should not be captured by default. Our JSONL stores content for the course corpus, and for Yash's own documents only on Yash's machine. Anything exported stores ids and scores for retrieved chunks, never their text, unless the corpus is D.

---

## 4. Datasets and experiments

- **Source of truth: the local JSONL golden set**, following 06 §6.6. Any change makes a new file and a new `dataset_sha256`, and comparisons need identical comparison keys. LangSmith or Phoenix datasets are **mirrors** of it.
- **Mirroring:** `datasets.py push --to langsmith` uploads a frozen version, tagged with the first 12 hex digits of its `dataset_sha256`. LangSmith versions a dataset on every change and supports `update_dataset_tag(as_of=…)` and `splits=[…]`. Only Corpus D items are pushed.
- **Golden-set lifecycle** (`ci-cd-evals`):
  - Start from the course eval set: 40 answerable + 6 unanswerable minimum, target 60–100 (D-09).
  - Add an item only when a new failure mode is confirmed by `error-analysis`; every addition is a new version.
  - Keep regression items (past failures) tagged.
  - Run on dev, touch test once per selection round, keep holdout for K1 (06 §9.4).
- **Leakage check** (`ci-cd-evals`). A T1 test fails if any golden question, gold answer or gold quote appears in `prompts/*.txt`, in the judge few-shots, or in any LLM-rewrite few-shots. It checks normalised 8-word overlaps, not just exact strings.
- **Experiments:**
  - The course runner (06 §9) is the primary path. It is offline, replayable and uses the paired bootstrap.
  - `langsmith.evaluate(target, data=…, evaluators=[…], upload_results=False)` is the framework view. With `upload_results=False`, nothing is recorded to LangSmith. The flag is marked beta. Whether it runs with no API key at all is **UNVERIFIED**.
  - Defaults to know: `max_concurrency=0` (no concurrency), `num_repetitions=1`, `error_handling="log"`.
  - Each LLMOps notebook compares its version with the previous champion and v0 on identical comparison keys (06 §4.1 rule 1).

---

## 5. Evaluators

A cheap-to-expensive cascade (`code-based-evaluators`), with retrieval and answer quality kept separate (`rag-evaluation`):

| Tier | What | When | Source |
|---|---|---|---|
| 1. Deterministic | Retrieval: CE@k, Hit@k, MRR, nDCG, Span-Coverage. Answers: EM/F1 for short answers, citation page-hit, citation format, the abstention string, `finish_reason = length`, empty answer, JSON schema validity for structured outputs | Every run, every commit (T1) | 06 §7.3–7.4 |
| 2. Human labels | ≥ 30 answer-level labels on v0, about 10 answers read per version, plus Codex as a separate calibration labeller | Until the end batch | 06 §8.4, D-10 |
| 3. LLM judge (Cohere) | Binary or 3-level correctness, faithfulness, citation support; one dimension per call; rationale before the label | **Once, at the end**, on stored traces | D-10, `llm-as-judge` |
| 4. Judge validation | TPR/TNR on a held-out labelled split. Corrected rate θ̂ = (p_obs + TNR − 1)/(TPR + TNR − 1) with a bootstrap CI (`judgy`). 06 §8.4 decision rule: lower 95% bounds of failure-class recall ≥ 0.70 and κ ≥ 0.40 | End batch | `judge-validation` |

Two notes:
- With "pass" as the positive class, the skill's TNR is 06's failure-class recall. Both are reported, so the two vocabularies line up.
- The Cohere judge model id must be pinned and recorded. Current ids include `command-a-03-2025` and `command-a-reasoning-08-2025`; old aliases were deprecated on 2025-09-15. Command A prices are **UNVERIFIED** (not shown on cohere.com/pricing on 2026-10-17).

---

## 6. Cost, latency and model choice

### 6.1 Token and cost accounting

- Cost per call = input × price_in + cached input × price_cached + output × price_out, plus fees per embedding or rerank call. Prices come from `study/llmops/prices.json`, with the date checked recorded as `price_table_version`.
- Output tokens include reasoning tokens. On Groq, whether `completion_tokens` already contains `reasoning_tokens` is **UNVERIFIED**, so check one live response and record the rule.
- Each run reports both **cost if called** (from cached usage) and **cost actually paid** (0 on a replay hit).
- Latency is reported as p50/p95 per stage, with the method named, excluding cache hits (06 §7.5). Groq also reports `queue_time`, which separates server queueing from generation.

### 6.2 Prices (checked 2026-10-17 unless noted; per 1M tokens)

| Model | Input | Output | Notes |
|---|---|---|---|
| Groq `openai/gpt-oss-20b` | $0.075 | $0.30 | Cached input $0.037 (prompt caching is automatic; cached tokens do not count toward rate limits). Batch API −50% (24 h or 7 d window; seems to need the Developer plan, **UNVERIFIED**). Context 131,072; max output 65,536 |
| Claude Haiku 5.5 `claude-haiku-5-5` | $0.10 | $0.50 | For prompts ≤ 100K tokens ($0.50/$2.50 beyond). Effort default `medium` |
| Claude Sonnet 5.5 `claude-sonnet-5-5` | $2.00 | $10.00 | Cache reads $0.20 |
| Claude Opus 5.5 `claude-opus-5-5` | $4.00 | $20.00 | Cache reads $0.20 (0.05×); thinking cannot be disabled |
| Claude, all | | | Prompt-cache writes 1.25× (5 min) or 2× (1 h); reads about 0.1×; Batch API −50%, which stacks with caching. Source: `claude-api` skill, price table cached 2026-10-06 |
| Cohere `embed-v4.0` | **UNVERIFIED** | | 128k context; dimensions 256/512/1024/1536 (default 1536); ≤ 96 texts per call; `truncate` default END |
| Cohere rerank `rerank-v4.0-pro` / `-fast` (32k context); `rerank-v3.5` still listed | **UNVERIFIED** | | Priced per "search" (1 query, ≤ 100 documents) |

### 6.3 Budgets per run

- Every run declares `Budget(max_usd, max_calls, max_tokens_per_provider)`. The planner estimates the cost from the planned calls and tokens. The cache layer counts as it goes and stops **before** a call would cross the budget.
- **Worked estimate** (assumed tokens, not measured): one v0 generation run is 55 questions × (1,500 input + 512 output at the cap).

| Model | Cost per run (upper bound at the output cap) |
|---|---|
| Groq gpt-oss-20b | 55 × (1,500 × 0.075 + 512 × 0.30)/10⁶ ≈ **$0.015** |
| Claude Haiku 5.5 | ≈ $0.022 |
| Claude Sonnet 5.5 | ≈ $0.45 |
| Claude Opus 5.5 | ≈ $0.89 |

- The Claude figures are lower bounds. Thinking tokens also count as output, so a Claude run needs a larger `max_tokens`.
- **Rate limits decide the time, not the money.** At 8K TPM, 55 × about 2,000 tokens takes at least 14 minutes. 200K TPD allows about 1.8 such runs a day, plan **UNVERIFIED**.

### 6.4 Model tiers (D-32)

| Task type | Default | Claude when credits exist | Why |
|---|---|---|---|
| High-volume steps: query rewrite (Q1), HyDE passage (Q2), proposition extraction (I4), chunk grading (V2, A2), contextual headers (I5) | Groq gpt-oss-20b, `reasoning_effort=low` | **Haiku 5.5**, effort `low` | Cheap and fast; quality is checked by retrieval metrics |
| Final answers (C5, v-series generation) | Groq gpt-oss-20b | **Sonnet 5.5** as a comparison arm only | Changing the generator is a new experiment arm, never a silent swap (06 §9.2) |
| Hard reasoning: decomposition plans, agent planning (A5), K1 design critique | Groq | **Opus 5.5**, effort `medium` | Quality decides the result |
| Judge (end batch) | **Cohere** (D-10) | Claude only if Yash revises D-10 | Different family from the generator |

Claude rules:
- Pin the exact ids above, never with date suffixes.
- Always send `output_config.effort` explicitly.
- Never send `temperature`.
- Forced `tool_choice` returns a 400 on Opus 5.5 and Sonnet 5.5. Use `auto` plus `strict: true`, or structured outputs.
- Check `stop_reason` for `refusal` before reading the content.

---

## 7. Prompt and config versioning

- **Prompts are files:** `prompts/<name>_v<N>.txt`, never edited after first use. A change is a new file with a new version. The trace stores `prompt_version` and the sha256 of the rendered template (06 §2.5). Judge prompts follow the same rule (06 §2.3 `Judge.name`).
- **Config is one YAML per run** (06 §2.4), hashed into `config_hash`. Model ids come from `.env` names (`GROQ_MODEL_ID`, and later `ANTHROPIC_MODEL_ID_SMALL`, `_LARGE`), but the **resolved** id is written into the run's `config.yaml`, so a later `.env` change cannot rewrite history.
- **Each change is tied to an experiment.** A prompt or config change enters only through a pre-registered run (06 §9.1 `summary.md`) whose config diff shows exactly one variable. The registry row links the prompt version. The cache key contains the rendered prompt, so old runs stay replayable after a prompt change.
- **LangSmith's prompt hub is not used.** Prompts stay local files under git.
- Commits happen only with Yash's OK (CLAUDE.md). Pre-registration timestamps rely on those commits.

---

## 8. CI and monitoring with local git only

### 8.1 Test tiers (extending 06 §9.6)

| Marker | Runs | Needs |
|---|---|---|
| (none) T1 | Metric unit tests, snapshot and chunker tests, cache-key tests, privacy-guard tests, leakage check, `quiz.py --check`, retrieval regression on cached embeddings or MiniLM | Nothing; network blocked |
| `replay` | Every LLMOps notebook and apply-it tool executed headless with `LLMOPS_CACHE_MODE=replay`; fails on any `ReplayMiss` and lists the missing keys from `replay_manifest.json` | The local cache; no key, no network |
| `llm` T2 | Generation regression subset (abstention F1, citation page-hit, EM/F1) | API key and credits; manual |

Register the markers in `pyproject.toml` under `[tool.pytest.ini_options]` (or `[tool.pytest]` on pytest 9) with strict markers, so a typo fails instead of silently selecting nothing. Block the network in T1 and `replay` with a socket guard; `pytest-recording` offers `--block-network` if added.

### 8.2 Hooks and sessions

- **pre-commit** (`repo: local`; `language: unsupported`, which pre-commit 4.4 renamed from `system`, with `system` kept as an alias):
  - Stage `pre-commit` runs the fast T1 subset and `quiz.py --check`, with `pass_filenames: false`.
  - Stage `pre-push`, installed with `pre-commit install --hook-type pre-push`, runs all of T1 plus `replay`. With no remote there is no push, so this stage is run by hand as `pre-commit run --hook-stage pre-push --all-files`, or through nox.
- **nox** with `nox.options.default_venv_backend = "uv"`:
  - Sessions `t1`, `replay`, `t2` (manual) and `monitor` (builds the page in §8.3).
  - Caveat: the uv backend does not reinstall local packages, so use `--reuse-venv=no` after dependency changes.
- **Acceptance test (v6.0):** inject a known regression (`normalize: false`, or a prompt swap) and confirm the suite fails.

### 8.3 A simple monitoring view

`nox -s monitor` writes one offline Plotly HTML page from `calls.sqlite`, `experiments/*/results.jsonl` and the apply-it tool logs. It shows:
- cost per day and per provider;
- calls, cache hit rate and replay misses;
- p50/p95 latency per stage;
- error classes, including exhausted switches;
- `finish_reason = length` and empty-answer rates;
- metric per version (CE@4, abstention F1);
- flip rates;
- `system_fingerprint` changes.

Thresholds are written in `monitor.yaml`, for example: cost over budget, length-stop rate above 5%, hit rate dropping, a new fingerprint. A breach is shown in red and also fails `nox -s monitor --check`.

### 8.4 Canaries and feedback

- **Embedding canary:** embed 3 fixed strings with the cache bypassed and stop if the vectors drift beyond a tolerance set from two runs (review §4 M4).
- **Generator canary:** 3 fixed questions in `record` mode; compare with sample 0.
- **Feedback loop:** a failure seen in an apply-it run or a canary goes to the error-analysis log (M5 taxonomy). If confirmed, it is added to the golden set as a new item (new dataset version), then becomes a T1 or T2 regression test (`ci-cd-evals`, `error-analysis`).

---

## 9. Framework guidelines

### 9.1 When LangChain and LangGraph add value

| Use the framework for | Stay in plain Python for |
|---|---|
| Showing how production code is usually wired (loaders, splitters, retrievers, chat models, runnables) | Every mechanism lesson and verify notebook (D-32: mechanism first) |
| LangGraph for **multi-step control flow** with state, branches, retries or human checkpoints: CRAG loops (A2), routing (A1), Self-RAG (A3), agentic RAG (A5) | Linear pipelines: retrieve → assemble → generate. A function is clearer than a graph |
| `InMemorySaver` / `SqliteSaver` checkpoints and `interrupt()` for resumable or human-in-the-loop runs | Metrics, statistics and the experiment runner |
| Tracing integrations (callbacks → LangSmith or Phoenix) | The cache and the error classifier |

LangChain's "workflows vs agents" page separates predetermined code paths (prompt chaining, routing, parallel, orchestrator-worker, evaluator-optimizer) from agents that choose their own steps. It gives no graph-versus-loop rule. Our rule: use a graph only when the flow has a cycle, a branch chosen at run time, or a checkpoint.

One trap: after `interrupt()` resumes, the node restarts from its beginning, so side effects before the interrupt run again. With our cache, a repeated LLM call is a cache hit, not a second charge.

### 9.2 Defaults that hide behaviour the lessons warn about

| Component | Hidden default (source, 2026-10-17) | Course rule |
|---|---|---|
| `ChatGroq` | `temperature=0.7`; `max_retries=2`; `reasoning_effort=None` → server default `medium` | Not used directly (adapter); if shown, set all three |
| `ChatAnthropic` | `max_tokens` filled from the model profile (fallback 4,096); `max_retries=2`; `stream_usage=True` | Set `max_tokens`, effort and `max_retries=0` |
| `ChatCohere` / `BaseCohere` | **`model=None` triggers a network call** to list the default chat model, so the model can change silently; `timeout_seconds=300` | Always pass the model id |
| `CohereEmbeddings` | `max_retries=3`; `truncate=None` (Cohere's server default is END, i.e. silent truncation); no batching (all texts in one call; the API limit is 96) | Use `CachedEmbeddings`, which batches at 96 and records truncation |
| `RecursiveCharacterTextSplitter` | `chunk_size=4000`, `chunk_overlap=200`, `length_function=len` (**characters**), `keep_separator=True`, `strip_whitespace=True` | Set 1000/200 and the unit explicitly; compare with the course chunker (C2) |
| `VectorStoreRetriever` | `similarity`, `k=4` | Set k from the config |
| `Runnable.with_retry` | Retries on any `Exception`, 3 attempts, jitter | Do not use around cached calls |
| LangChain LLM cache | Not used when streaming; key from serialised model | Off; use the adapters |
| `CacheBackedEmbeddings` | SHA-1, empty namespace, queries not cached | Not used |
| `langsmith.evaluate` | `upload_results=True` | Pass `upload_results=False` unless corpus D |

### 9.3 The two adapters (plan)

- **`CachedChatModel(BaseChatModel)`** takes `provider`, `model`, `params` and `cache`. `_generate` turns LangChain messages (and `bind_tools` schemas) into the provider request, calls `llmops.cache.call(...)`, and turns the stored response back into an `AIMessage` with `tool_calls`, `usage_metadata` and `response_metadata` (cache_hit, cache_key, model_returned). Streaming is **not implemented on purpose**. This avoids `langchain-groq` (groq < 1.0) and `langchain-cohere` (cohere < 6), so the project keeps groq 1.7.0 and cohere 7.2.0.
- **`CachedEmbeddings(Embeddings)`**: `embed_documents` uses `search_document` and `embed_query` uses `search_query`. It uses C3's key and store, batches at 96, and records usage.
- Read-only cells may still show the official `ChatGroq` and `ChatCohere` code as "how teams usually write it", with the hidden defaults from §9.2 pointed out.

### 9.4 Pinning and API churn

- **The policy:** LangChain and LangGraph 1.x promise no breaking public-API changes within a major version; deprecated features are removed only in 2.0. The 0.3 line is in maintenance until December 2026.
- **What moved:** chains, retrievers, the indexing API, `hub` and `CacheBackedEmbeddings` moved to `langchain-classic`. `langchain` 1.x holds `create_agent` (which replaces LangGraph's deprecated `create_react_agent`) and middleware.
- **Pin rule:** declare `>=X.Y,<2` in `pyproject.toml` and let `uv.lock` hold the exact versions; upgrade only between experiments, with the lock diff recorded in `env.json` (06 §9.1).
- **Churn seen in the last 2 weeks:**
  - Several releases of `langchain-core`, `langgraph`, `langsmith` and `arize-phoenix`.
  - **`langfuse` 5.0** (a new major).
  - `anthropic` 1.11 → 1.15.
  - `langchain-community` (May) and `ragas` (January) have been quiet.
- **httpx vs httpx2:** `anthropic` 1.x and `langsmith` 0.14 use `httpx2`; `groq`, `cohere`, `langchain-core` and `langfuse` use `httpx`. Expect both in the environment. HTTP-level mocks must handle both, or call `httpx2.alias_httpx()` first.
- **Skip for now:** `ragas` hard-depends on `openai` and `langchain_openai`, and its defaults expect OpenAI. `deepeval` sends telemetry through posthog. Both stay out unless a phase session finds a specific need (Phase 3 assesses them).

---

## 10. One shared helper package (plan only)

`rag_learning/study/llmops/`, imported by every LLMOps notebook and apply-it tool. No notebook re-implements caching, tracing or cost.

| Module | Job | Key tests |
|---|---|---|
| `cache.py` | §2.3 keys, SQLite store, samples, the three modes, `ReplayMiss`, export/import, `replay_manifest` | Every key field changes the key; secrets and timeouts do not; replay never opens a socket; record appends samples; crash-safe writes |
| `providers.py` | Thin `call_groq`, `call_anthropic`, `call_cohere_embed`, `call_cohere_rerank`, `call_cohere_chat`. Each sends every output-affecting parameter explicitly and sets SDK `max_retries=0` | Uses fake clients, as the C5 lab's `FakeGroq` does |
| `errors.py` | The §2.5 classifier, `provider_state`, retry with backoff, the throttle | One fixture per row of the §2.5 table |
| `privacy.py` | Book shingle fingerprints (hashes only), `guard(input)`, `assert_corpus_is()` | A known book sentence is refused; climate text passes |
| `trace.py` | 06 §2.5 records plus §3.3 spans to JSONL; optional OTel export to Phoenix; LangSmith only through the climate guard | Round trip; no chunk text in exported spans unless corpus D |
| `cost.py` | `prices.json`, cost per call, run budget, rate-limit planner | Hand-computed toy costs (06 §7.5 style) |
| `evals.py` | Tier-1 evaluators wrapped for LangSmith/Phoenix evaluator signatures (`inputs, outputs, reference_outputs` → `{key, score}`), and `judgy` correction for the end batch | Same numbers as `ragkit` metrics |
| `datasets.py` | Load golden JSONL, verify `dataset_sha256`, leakage check, mirror push (corpus D only) | Leakage fixture fails |
| `lc.py` | `CachedChatModel`, `CachedEmbeddings` | Tool calls survive a replay; hit flag set |
| `cli.py` | `status`, `export`, `import`, `stats`, `missing` | — |

**Relation to `ragkit`** (06 §2): one implementation only. When `ragkit/providers/` is built, it imports `llmops.cache` and `llmops.providers` rather than writing its own LLM cache. The C3 embedding cache code moves into `llmops` with its key unchanged.

---

## 11. Tools list

Pins are the newest release at least 2 weeks old (on or before 2026-10-03), from the PyPI JSON API on 2026-10-17. "Installed" is from `uv pip list` (read-only).

| Purpose | Package | Pin | Installed now? | Offline? | Cost / keys | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Groq LLM | `groq` | 1.7.0 (keep) | yes | no (API) | `GROQ_API_KEY` | Apache-2.0 | yes |
| Claude LLM | `anthropic` | 1.11.0 | no | no (API) | `ANTHROPIC_API_KEY`, when credits exist | MIT | yes (D-32); uses httpx2 |
| Cohere embed, rerank, judge | `cohere` | 7.2.0 (keep) | yes | no (API) | `COHERE_API_KEY`; production key for the end batch | MIT | yes |
| Framework core | `langchain-core` | 1.6.6 | no | yes | — | MIT | yes (D-32, after mechanism) |
| Splitters (comparison only) | `langchain-text-splitters` | 1.1.3 | no | yes | — | MIT | yes |
| Graphs (A1–A5, v7) | `langgraph` | 1.2.12 | no | yes | — | MIT | yes |
| Graph checkpoints | `langgraph-checkpoint-sqlite` | 3.1.1 | no | yes | — | MIT | yes |
| Agents (A5 only) | `langchain` | 1.4.3 | no | yes | — | MIT | later, if A5 needs `create_agent` |
| Legacy reading only | `langchain-classic` | 1.0.8 | no | yes | — | MIT | read-only; not installed |
| Claude via LangChain (optional) | `langchain-anthropic` | 1.7.5 | no | no | as `anthropic` | MIT | optional; the adapter is preferred |
| **Not installed** | `langchain-groq` 1.1.3 | — | — | — | — | MIT | **conflicts**: needs groq < 1.0 |
| **Not installed** | `langchain-cohere` 0.6.0 | — | — | — | — | MIT | **conflicts**: needs cohere < 6 |
| Hosted tracing and eval | `langsmith` | 0.14.4 | no | SDK yes; service no | `LANGSMITH_API_KEY`; free plan | MIT | yes, climate corpus only |
| Local tracing client | `arize-phoenix-otel` | 0.17.2 | no | yes | — | Apache-2.0 | yes |
| Instrumentors | `openinference-instrumentation-langchain` / `-anthropic` / `-groq` | 0.1.78 / 3.0.1 / 0.1.31 | no | yes | — | Apache-2.0 | yes; support for groq 1.7 **UNVERIFIED** |
| Local trace viewer | `arize-phoenix` (server) | 20.19.0 via `uvx` | no | yes | — | **ELv2** | yes, as a separate tool; heavy (54 deps) |
| OTel SDK | `opentelemetry-sdk` | 1.45.0 | no | yes | — | Apache-2.0 | pulled in by phoenix-otel |
| Self-hosted tracing | `langfuse` | 4.16.0 (5.0 is new) | no | needs Docker | — | MIT | not chosen |
| Judge correction | `judgy` | 0.1.0 (only release, 2025-05-25) | no | yes | — | MIT (ai-evals-course) | yes (end batch) |
| Local CI hooks | `pre-commit` | 4.6.2 | no | yes | — | MIT | yes |
| Task runner | `nox` | 2026.8.17 | no | yes | — | Apache-2.0 | yes |
| Tests | `pytest` | 9.1.1 | yes (dev) | yes | — | MIT | yes |
| HTTP cassettes (optional) | `vcrpy` / `pytest-recording` | 8.3.0 / 0.14.0 | no | yes | — | MIT | optional; httpx2 support **UNVERIFIED** |
| Not now | `ragas` 0.4.3, `deepeval` 4.2.8 | — | no | — | OpenAI defaults; telemetry | Apache-2.0 | assessed in Phase 3 |

Install lines (**do not run** until a phase builds its notebook):

```text
uv add --group llmops langchain-core==1.6.6 langgraph==1.2.12 langgraph-checkpoint-sqlite==3.1.1 langchain-text-splitters==1.1.3 langsmith==0.14.4
uv add --group llmops arize-phoenix-otel==0.17.2 openinference-instrumentation-langchain==0.1.78 openinference-instrumentation-groq==0.1.31
uv add --group llmops anthropic==1.11.0 openinference-instrumentation-anthropic==3.0.1     # when Claude credits exist
uv add --group dev pre-commit==4.6.2 nox==2026.8.17
uv add --group eval judgy==0.1.0                                                             # end batch
uvx arize-phoenix@20.19.0 serve                                                              # run on demand, not a project dependency
```

**Keys and accounts:**
- Present: `GROQ_API_KEY`, `COHERE_API_KEY`.
- Add when needed: `ANTHROPIC_API_KEY`, `LANGSMITH_API_KEY` (+ `LANGSMITH_ENDPOINT`).
- **Never** set `LANGSMITH_TRACING` in `.env`.
- Phoenix needs no key.

**Weight:**
- The Phoenix server is the only heavy item, and it stays out of the lock through `uvx`.
- `cohere` already brings the `tokenizers` Rust wheel.
- Nothing needs a GPU.

---

## 12. The application map

Phase sessions use this to decide what each concept's LLMOps notebook covers. "Calls" means the external calls that go through the cache. A notebook with no LLM call still traces retrieval, logs metrics per version and adds a regression test.

| Phase · concepts | External calls (cached) | Framework build | Trace focus | Dataset and evaluators | Cost / latency | Versioning | CI / monitoring |
|---|---|---|---|---|---|---|---|
| 0 · O2 env | none | none | — | — | — | lock hash in `env.json` | `llmops` smoke test; `replay` marker wired |
| 1 · P1 LLM basics | Groq (a few prompts), Claude optional | `CachedChatModel` | tokens incl. reasoning, `finish_reason` | toy checks | cost per call; reasoning share | prompt files | replay test |
| 1 · P2–P3, P5–P6 | none | retriever wrappers (read-only) | ranked lists, scores | Hit@k/MRR on toy sets | p50/p95 | — | T1 metric tests |
| 1 · P4 embeddings | Cohere embed | `CachedEmbeddings` | input_type, dimension | similarity checks | cost per 1k texts | embed key fields | canary |
| 1 · P7 grounded prompting | Groq | prompt templates | prompt sha, abstention | abstention string, page-hit | tokens | prompt versions | T1 format checks |
| 2 · C1–C2 | none | loader and splitter comparison | chunk stats | chunk property tests | build time | `params_hash` | T1 |
| 2 · C3–C4 | Cohere embed | `CachedEmbeddings` + retriever | embed hits/misses; retriever spans | retrieval metrics | embed cost | `embed_hash` | retrieval regression |
| 2 · C5–C6 | Groq generation | LCEL chain or plain function over `CachedChatModel` | full v0 trace | deterministic answer checks; human labels | cost/query, p95 | `answer_v1` | first golden run; monitor page |
| 2 · C7 structured data | Groq (text-to-SQL, if used) | SQL tool | SQL text + result rows | execution-match checks | calls/query | prompt versions | T2 |
| 3 · M1–M5 | Groq (drafting items), none for metrics | `langsmith.evaluate` view (`upload_results=False`) | per-item metrics | golden set, leakage check, human labels, Codex labels | bootstrap cost ≈ 0 | dataset hashes | T1 harness; flip-rate lab (`record`) |
| 4 · I1–I3, I-CMP | Cohere embed (I3: per sentence) | splitters compared with ours | chunk sizes, truncation | CE@k at fixed k and equal budget | index build cost | `params_hash` per arm | grid regression |
| 4 · I4–I6 | Groq / Haiku per chunk (propositions, headers, HyPE questions) | batch over `CachedChatModel` | generated text → source span | proposition faithfulness (hand sample) | **index-time calls × chunks** | prompt + doc hash in key | rebuild cost tracked |
| 5 · R1–R5 | Cohere rerank (R3 arm); Groq/Haiku summaries (R5) | retrievers, ensemble, reranker | per-retriever ranks, fused ranks | CE@k, MRR, CE@pool | p95 rerank latency; rerank fees | pool size, λ | latency budget test |
| 6 · Q1–Q2 | Groq / Haiku per query | rewrite / HyDE chain | original vs transformed query | CE@4 per category | +1 call/query on the critical path | rewrite prompt versions | cost guard |
| 7 · X1–X3 | Groq / Haiku (X2 compression) | context assembly function | context tokens, dropped evidence | CE on final context; human labels | tokens saved vs calls added | budget config | token-budget test |
| 8 · V1–V4 | Groq / Haiku (verification, grading) | verification step | per-claim support decisions | citation page-hit, abstention F1; judge only at the end | +1–2 calls/query | grader prompt versions | abstention regression (T2) |
| 9 · D1–D4 | all of the above | tracing integrations | everything in §3.3 | regression suite; safety checks (`safety-evals`) | budgets per stage | index versioning | full CI + monitor + injected-regression test |
| 10 · A1–A5 | Groq / Haiku graders and routers; Opus for A5 planning (optional) | **LangGraph** graphs (cycles, routes, checkpoints) | each node, decision, retry, branch | controller accuracy vs hand labels (`tool-use-evaluation`, `multi-turn-evaluation`) | calls per query, variable latency | graph + prompt versions | branch coverage test |
| 11 · S1–S3 | Groq / Haiku extraction or summaries at index time; vision model for S2 (needs a decision in Phase 11) | graph or tree build | build calls, storage | target-category correctness | **index-build cost** | extraction prompt versions | rebuild cost |
| 12 · K1 | replay only (Corpus H runs recorded once) | champion pipeline | full traces | holdout + Corpus H | cost per answer | frozen champion config | final replay run |
| End batch (D-10) | Cohere judge (+ variance run) | — | judge calls | TPR/TNR, θ̂ with CI, κ | ~165 calls/version | judge prompt versions | one cached batch |

---

## Errors found in existing material (reported; not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| E1 | 06 §2.4 `cache.llm` comment | The LLM key `sha256(model_id\|messages\|params)` has no provider, tools or response format, and needs a canonical encoding | Use the §2.3 canonical-JSON key |
| E2 | 06 §2.4 / C3 D.4 embedding key; C3 `embed_hash` fields | `embed-v4.0` returns 256–1536 dimensions and several `embedding_types`; neither is in the key or in `EMBED_FIELDS`, so changing the dimension would serve stale vectors. Cohere's `truncate` default (END) is not recorded | Add `output_dimension`, `embedding_type` and `truncate` to the key and the manifest |
| E3 | 06 §2.4 `max_tokens: 512`; C5 `call_llm` (`c5_measure.py` L139–141); 06 §2.5 `llm.max_tokens` | Groq has deprecated `max_tokens` in favour of `max_completion_tokens` (default 1,024) | Switch the name in the next C5 revision; keep the trace field name, or record both |
| E4 | 06 §2.5 trace `llm` object | Missing `model_returned`, `system_fingerprint`, `reasoning_tokens`, `cached_tokens`, `http_attempts`, `cache_key`, `queue_time` | Add these fields (§3.3) |
| E5 | 06 §7.5 "Groq pricing is UNVERIFIED"; §8.6 rate-limit line | Prices and limits are now documented: $0.075 / $0.30; 30 RPM / 8K TPM / 200K TPD (plan ambiguous) | Record them with the check date; plan token-based throttling |
| E6 | 06 §8.3 item 4 and §9.2 "temperature 0" | Fine for Groq and Cohere; current Claude models reject `temperature` (400) | If Claude is used: "temperature 0 where the API accepts it; otherwise record effort/thinking" (matches review §7 row 16) |
| E7 | 08 D-08 (frameworks read-only) and D-18 (JSONL; external tools optional) | Partly superseded by D-32 but not marked | Add a "see D-32" note to both rows |
| E8 | The review's §5 note that the SDKs already retry | True, but the retries are invisible in latency and cost logs and waste calls on spend-cap 429s | `max_retries=0` plus our own logged retries (§2.5) |

---

## Open questions for Yash (preferences only)

The five decisions in the Summary. One more, optional: should the LangSmith endpoint be **EU** or **US**? EU is suggested if a hosted service is used at all.

---

## Sources

Opened on 2026-10-17 by the research agents unless stated. "Verified" means the page was opened and the fact checked on it; "3-vote" means it also survived the adversarial verification.

1. Anthropic, Rate limits — https://platform.claude.com/docs/en/api/rate-limits — verified (3-vote)
2. Anthropic, Errors — https://platform.claude.com/docs/en/api/errors — verified (3-vote)
3. Anthropic, Python SDK — https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/python — verified (3-vote; httpx2 note)
4. anthropic-sdk-python `_constants.py`, `_base_client.py` (main) — verified (3-vote; retry defaults)
5. `claude-api` skill (bundled, price table cached 2026-10-06): model ids, prices, caching and batch multipliers, error-code table — read locally
6. Groq, Errors — https://console.groq.com/docs/errors — verified (3-vote)
7. Groq, Rate limits — https://console.groq.com/docs/rate-limits — verified; plan for the gpt-oss-20b row UNVERIFIED
8. Groq, Spend limits — https://console.groq.com/docs/spend-limits — verified
9. Groq, API reference — https://console.groq.com/docs/api-reference — verified (seed, system_fingerprint, max_tokens deprecation, reasoning_effort default)
10. Groq, gpt-oss-20b model page — https://console.groq.com/docs/model/openai/gpt-oss-20b — verified (price, context)
11. Groq, Reasoning — https://console.groq.com/docs/reasoning — verified
12. Groq, Structured outputs — https://console.groq.com/docs/structured-outputs — verified
13. Groq, Tool use — https://console.groq.com/docs/tool-use — verified
14. Groq, Prompt caching — https://console.groq.com/docs/prompt-caching — verified
15. Groq, Batch — https://console.groq.com/docs/batch — verified
16. groq-python `completion_usage.py` — https://raw.githubusercontent.com/groq/groq-python/main/src/groq/types/completion_usage.py — verified
17. Cohere, Errors — https://docs.cohere.com/reference/errors — verified
18. Cohere, Rate limits — https://docs.cohere.com/docs/rate-limits — verified
19. Cohere, Models; Embed reference; Rerank; Chat reference — https://docs.cohere.com/docs/models, /reference/embed, /docs/rerank, /reference/chat — verified; prices UNVERIFIED
20. cohere-python errors — https://raw.githubusercontent.com/cohere-ai/cohere-python/main/src/cohere/errors/too_many_requests_error.py — verified
21. Thinking Machines Lab, "Defeating Nondeterminism in LLM Inference" (H. He et al., 2025-09-10) — https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/ — verified
22. LangChain PR #15575 (stream cache) — https://github.com/langchain-ai/langchain/pull/15575 — verified (3-vote)
23. LangChain commit #23842 (chat cache key) — https://app.semanticdiff.com/gh/langchain-ai/langchain/commit/9ccc4b1616591bd4f92ead6f15689d5d36534c21 — verified (3-vote)
24. langchain-core source (`chat_models.py`, `caches.py`, `globals.py`, `base.py`, `vectorstores/base.py`, `runnables/base.py`) and langchain-community `cache.py`, master — verified
25. `CacheBackedEmbeddings.from_bytes_store` reference — https://reference.langchain.com/python/langchain-classic/embeddings/cache/CacheBackedEmbeddings/from_bytes_store — verified (3-vote)
26. langchain-groq, langchain-anthropic, langchain-cohere, langchain-text-splitters source (master) — verified (defaults table)
27. LangChain v1 migration and release notes; release policy — https://docs.langchain.com/oss/python/migrate/langchain-v1, /releases/langchain-v1, /release-policy — verified
28. LangGraph v1, persistence, interrupts, workflows-agents — https://docs.langchain.com/oss/python/releases/langgraph-v1, /langgraph/persistence, /langgraph/interrupts, /langgraph/workflows-agents — verified
29. LangSmith pricing, billing, usage and retention, changelog — https://www.langchain.com/pricing, https://docs.langchain.com/langsmith/billing, /usage-and-billing, /changelog — verified; price per extra trace UNVERIFIED
30. LangSmith tracing quickstart, conditional tracing, masking, Anthropic wrapper, regions, Kubernetes — https://docs.langchain.com/langsmith/observability-quickstart, /conditional-tracing, /mask-inputs-outputs, /trace-anthropic, /regions-faq, /kubernetes — verified
31. langsmith-sdk `utils.py`, `evaluation/_runner.py` — verified
32. LangSmith local eval, code evaluators, datasets, pytest — https://docs.langchain.com/langsmith/local, /code-evaluator-sdk, /manage-datasets-programmatically, /manage-datasets, /pytest — verified
33. Arize Phoenix LICENSE, README, `config.py`, pyproject — github.com/Arize-ai/phoenix — verified
34. Phoenix docs: configuration, environments, privacy, network security, `arize-phoenix-otel` — https://arize.com/docs/phoenix/… — verified; default SQLite path UNVERIFIED
35. OpenInference spec (configuration, traces, semantic conventions) — github.com/Arize-ai/openinference/spec — verified
36. Langfuse LICENSE, docker-compose, self-hosting, SDK, masking, LangChain, experiments, pricing — github.com/langfuse/langfuse, https://langfuse.com/… — verified
37. OpenTelemetry GenAI semantic conventions (moved) — https://opentelemetry.io/docs/specs/semconv/gen-ai/ and github.com/open-telemetry/semantic-conventions-genai — verified
38. pytest-recording README — https://github.com/kiwicom/pytest-recording — verified (default record mode `none`)
39. vcrpy docs (usage, advanced, installation) — https://vcrpy.readthedocs.io/ — verified (default record mode `once`; httpx supported)
40. pre-commit docs — https://pre-commit.com/ — verified
41. pytest docs (markers, configuration) — https://docs.pytest.org/en/stable/how-to/mark.html, /reference/customize.html — verified
42. nox docs (usage, config) — https://nox.thea.codes/en/stable/ — verified
43. PyPI JSON API for every package in §11 — https://pypi.org/pypi/<name>/json — verified 2026-10-17
44. Course files read locally: CLAUDE.md; rag_learning/README.md; 06 §2–§9; 08 Part 4 (D-03…D-32); sources/EXTERNAL_RESOURCES_REVIEW_2026-10-09.md; concepts/C3 (D.4, H.4); sources/verification/C3/c3_measure.py; sources/verification/C5/c5_measure.py; .gitignore; pyproject.toml; .claude/skills (evals-foundations, llm-observability, ci-cd-evals, code-based-evaluators, llm-as-judge, judge-validation, rag-evaluation, improving-llm-agents)
