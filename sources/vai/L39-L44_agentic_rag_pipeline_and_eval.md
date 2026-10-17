# VAI lessons 39–44: compliance, fallback, synthesizer, traceability, agentic RAG end to end, RAG eval

[← Guide index](README.md) · Course folder: `C:\Yash\New-Work\RAG\vertical-ai-agents-main\` · Checked 2026-10-17 · Log: [verification/L39-L44_agentic_rag_pipeline_and_eval_log.md](verification/L39-L44_agentic_rag_pipeline_and_eval_log.md)

**What this is:** the guide to VAI lessons 39–44: compliance, fallback, a synthesizer, traceability, agentic RAG end to end and a RAG eval gate.
**What this is not:** the course code, or a run of it. Nothing in the course was run or copied.

**How to read this file:**
- A `file:line` is relative to the project folder named in the lesson heading.
- **UNVERIFIED** marks behaviour that depends on a library version or on Gemini.
- **(counter)** or † means the lesson names a technique without building it. Read it to learn what is missing.
- Tags: **[bug]** the code does the wrong thing · **[misleading]** a label, message or number claims more than the code does · **[shallow]** it works, but is too thin for your project · **[ok-for-demo]** fine for a demo, not for real use · **[LLMOps]** material for your LLMOps notebooks · **[Interview]** worth practising for interviews.
- "I" means the reviewer who checked the code. Each lesson was checked by a reader, a fact-check pass and a completeness pass; the log has every verdict.

**Notes for this block:**
- Where a code pattern was reproduced (the L41 citation regex, the L42 sorting crash), it was with a 3-line scratch snippet, not by running the lesson.
- The generated L42 and L43 folders differ from their `setup.sh`; read the folders.

---

## L39 · Validator agent: compliance rules and audit list  (`lesson39/l39-validator-compliance/`)

**What the code teaches, in one line:** A YAML rule file drives a two-tier checker (regex first, then an LLM yes/no question). It adds up the severities of broken rules into a risk score, and that score approves or rejects the *retrieved documents*.
**What it is not:** It is not an answer-level guardrail (it never sees the generated answer). It is not prompt-injection defence, and it is not a real PII detector.
**Relevance to your RAG study:** Low. Concepts: D4; V2 (adjacent only: a cross-document contradiction check, which is neither relevance grading nor a groundedness check) [Interview]
**Stack:** FastAPI, Redis (cache and audit list), PyYAML. google-generativeai 0.8.3 (`backend/requirements.txt:5`). The model comes from `GEMINI_MODEL`, default `gemini-2.5-flash` (`backend/compliance_engine.py:48`, `backend/validator_agent.py:33`). No embeddings, no vector store. The frontend has a JSON-documents form, live stats over a WebSocket and an audit list.
**Swap to your stack:** easy. There are two short LLM prompts. Redis errors are caught and ignored (`compliance_engine.py:197-198`, `:212-213`, `:243-244`, `:260-261`), so it runs without Redis, but then you get no cache, no audit list, and /stats shows zeros.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `rules/compliance_rules.yaml` | 9 rules: id, domain, severity, regex, LLM prompt, action | PII regex :7; "personal data" regex :75 |
| 2 | `backend/compliance_engine.py` | loads rules, checks each one, sums severity, writes the audit entry | :88-97, :107-180, :215-246 |
| 3 | `backend/validator_agent.py` | stage 1 contradiction check, stage 2 compliance | :41-76, :78-125 |
| 4 | `backend/main.py` | /validate, /stats, /audit-trail, /ws | :42, :46-70 |

### How it works, step by step
1. POST /validate with documents, a query and a domain (`backend/main.py:46-62`). The `domain` field is ignored, because the validator was built once for "healthcare" at startup (`main.py:42`).
2. Factual check, which runs only when there are 2 or more docs (`validator_agent.py:82-83`). Gemini (temperature 0.1, JSON output) gets the first 500 chars of each doc and is asked for contradictions (:86-112). On any error the check returns "passed" plus an error string, so it fails open (:122-125).
3. Compliance check: all the doc texts are joined (:55). The engine loads the rules whose domain is healthcare or all, which gives 7 rules (`compliance_engine.py:73-75`).
4. For each rule, it first looks in the Redis cache under domain + rule + content hash (:111-114). The regex tier runs a case-insensitive `re.search`, and any hit counts as a violation (:117-127). The LLM tier runs at temperature 0.1 with `max_output_tokens=100`. It counts a violation if "YES" appears in the first 10 characters of the reply (:130-164). Every loaded LLM rule has its own prompt, so the content is never sent (see the first bug below). One loaded rule, HARMFUL_CONTENT, has both a regex and an LLM prompt, and a regex hit returns at once (`rules/compliance_rules.yaml:100-102`, `compliance_engine.py:117-127`).
5. Risk is the sum of the severities of the broken rules, and the compliance stage rejects if risk is above 70 (:91-96). So one PII hit (95) rejects on its own, while one missing-disclaimer hit (60) on its own still approves. The decision covers the whole joined text, so one flagged document rejects the full set (`validator_agent.py:55-58`, `:66`).
6. The audit entry goes into the Redis list `audit:healthcare`, trimmed to 1000 entries. It holds the time, the content hash, the first 200 chars, the decision, the risk and the violations (:215-246).

### README vs code
- README says "Immutable Audit Trail: PostgreSQL persistence" (`README.md:10`). The code keeps a Redis list and trims it to the last 1000 entries (`compliance_engine.py:237-242`), so nothing is immutable. psycopg2, SQLAlchemy and asyncpg are installed but never imported (`backend/requirements.txt:7-8,14`).
- README mentions a "Circuit breaker" (`README.md:99`) and "Emits ComplianceViolationEvent" (`README.md:104`). Neither exists in the code.
- The rule `action` field (block/warn/filter) is loaded (`compliance_engine.py:26`) but never read. Only the summed severity decides.

### Where it is thin or wrong
- [bug] **The LLM rules never see the content.** If a rule has its own `classification_prompt`, and every LLM rule in the YAML has one, the code sends only that prompt text. The default prompt, which does include the content, is used only when a rule has no prompt of its own (`compliance_engine.py:132-143`). So the LLM is asked "does this content…?" with no content attached.
- [bug] Fail-open plus caching: if the LLM call raises, the rule falls through to "passed", and that pass is cached for 1 hour (:166-179, :207-210).
- [bug] (UNVERIFIED, not run) `max_output_tokens=100` (:149) on a thinking model (gemini-2.5-flash) may leave no visible text. Reading `response.text` then raises, so the rule passes silently. Whether this happens depends on the model and SDK version. It is the same trap as your gpt-oss-20b `max_tokens` rule.
- [shallow] The PERSONAL_DATA_EXPOSURE regex matches the bare word "email", or "address" followed by any digit on the same line (`rules/compliance_rules.yaml:75`). It has severity 90, so it rejects. A technical PDF that says "memory address 0x10" gets blocked.
- [misleading] `/stats` "total_violations" actually counts rejected requests, not violations (`compliance_engine.py:277`). It also reads only the last 500 audit entries (:265).
- [shallow] **All or nothing on the retrieved set.** The rules run on all documents joined together (`validator_agent.py:55`), and one decision covers them all (`compliance_engine.py:96`). One flagged chunk throws away every chunk. The `Rule` model's comment lists a "filter" action (`compliance_engine.py:26`), but nothing filters per document.
- [shallow] **Stale cache after a rule change.** The cache key holds the domain, the rule id and the content hash, but not the rule's `version` or its prompt (`compliance_engine.py:182-185`; the field is at :27). Edit a rule and the old verdict is served for up to an hour (:209). Your record/replay cache key needs the prompt version for the same reason.
- [shallow] `risk_score` is an unbounded sum (:93). Two regex hits (PII 95 plus personal data 90) give 185, so it is not a 0–100 score.

### Tests and data
- `test.sh` only prints curl output and makes no assertions (`test.sh:11-37`). It has one sample, an SSN text, which triggers PII and is rejected. The rules YAML is the only data file.

### What to take for your project
- D4, in plain Python: write a `check_chunk(text)` that runs the regex rules first and an LLM classifier only for fuzzy rules, with an explicit fail-open or fail-closed choice per rule. Fix the two bugs: send the content, and never cache an error as a pass.
- Decide per chunk: drop the flagged chunk and log why, instead of rejecting the whole retrieved set.
- If you add the LLM tier, call Groq `openai/gpt-oss-20b` with `reasoning_effort="low"` and a generous `max_tokens` (the 100-token trap above). Put the rule version and a prompt hash in the cache key, and run it only on your project PDFs, never on the book's text.
- For technical PDFs, PII matters less than prompt-injection text inside chunks. Skip the rest.

### Try this
- 20 min. Copy the regexes from `rules/compliance_rules.yaml:7` and `:75` into your own scratch file. Note that the YAML strings double every backslash, so use single backslashes in a Python raw string. Run them on 6–8 sentences you write, for example: an SSN, a card number with spaces, "email us", "address 0x7FFF", "date of birth", and a plain technical sentence. Count the false positives and the misses. Then read `compliance_engine.py:132` and write one sentence on why the LLM tier cannot help.

### Interview angle
- **Q:** "Regex or LLM for PII and policy guardrails?" **A:** Use both, in tiers. Regex and validators handle structured PII cheaply and testably, and an LLM classifier handles fuzzy policy. Apply them to the final answer as well as the inputs, decide fail-open or fail-closed by severity, and log every decision.

---

## L40 · Fallback and self-healing loop  (`lesson40/l40-fallback-selfhealing/`)

**What the code teaches, in one line:** A bounded retry loop in which the validator's *failure type* picks the fix (rewrite the query). It adds exponential backoff with jitter, a circuit breaker, and a final "could not validate" exit.
**What it is not:** It is not Corrective RAG with a real relevance grader. There is no real retrieval, no real validation and no answer. The validator is a weighted coin flip (it fails 30% of the time).
**Relevance to your RAG study:** Low (the pattern only). Concepts: A2 (counter-example: the grader is random and the retrieval is invented), Q1 (counter-example: the decomposition is thrown away), V3 (the exit shape only), D2 [Interview]
**Stack:** FastAPI and google-generativeai 0.8.3. `gemini-2.0-flash-exp` is hard-coded in three agents (`backend/planner_agent.py:8`, `backend/retriever_agent.py:8`, `backend/validator_agent.py:8`); it is an experimental id that is probably no longer served (UNVERIFIED). No embeddings, no store. The Redis container, the redis library, psycopg2 and prometheus-client are listed but unused (`docker-compose.yml:15-20`, `backend/requirements.txt:4-9`). The frontend shows breaker state, counters, demo buttons and recent retries.
**Swap to your stack:** easy. Only the fake retriever and the sub-query call use an LLM.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/fallback_orchestrator.py` | the loop and the degradation exit | :25-115 |
| 2 | `backend/validator_agent.py` | random failure | :15-44 |
| 3 | `backend/planner_agent.py` | rewrite per failure type | :18-52 |
| 4 | `backend/retry_policy.py` | backoff with jitter, delay per failure type | :12-37 |
| 5 | `backend/circuit_breaker.py` | closed / open / half-open | :22-53 |
| 6 | `backend/retriever_agent.py` | LLM-invented "documents" | :10-44 |

### How it works, step by step
1. POST /query with `{query, simulate_failure}` (`backend/main.py:34-44`). If the breaker is open, it returns an error at once (`fallback_orchestrator.py:31-37`).
2. It makes up to 3 attempts, with a base delay of 1.0 s (:14). `plan()` returns the query unchanged (`planner_agent.py:10-16`). `retrieve()` asks Gemini to invent snippets, then copies the first 200 chars of the whole reply into two identical "documents" with relevance fixed at 0.85 (`retriever_agent.py:15-29`). On an error it returns a single "fallback.pdf" with relevance 0.5 (:30-38). Both the retriever and the sub-query call catch every error with a bare `except` (`retriever_agent.py:30`, `planner_agent.py:45-46`), so a Gemini failure never reaches the orchestrator.
3. `validate()` fails if `simulate_failure` is set or if random() < 0.3, and it picks the failure type at random (`validator_agent.py:19-37`). It never reads the documents. With `simulate_failure` set, every attempt fails by construction, so no rewrite can help and the request always ends in step 5's exit.
4. **What triggers what.** Each failure type rewrites the *original* query in its own way. A compliance failure adds an "exclude sensitive" suffix. A factual failure adds a "provide sources" suffix. An insufficient-context failure asks Gemini for 2–3 sub-queries (`planner_agent.py:23-46`). The sleep is 0.1 s for compliance, base·2^attempt ±30% for factual, and ×1.5 that for insufficient context (`retry_policy.py:12-37`). There is no sleep after the last attempt (`fallback_orchestrator.py:81`).
5. **What it falls back to.** On success it returns the context plus the validation result, with no answer. If all 3 attempts fail, `graceful_degradation` returns success=false with "Max retries exhausted" and a hint to rephrase (:100-115). That is the closest thing here to abstention (V3).
6. An exception counts as one breaker failure per attempt, with no backoff and no rewrite (:89-98). Because the agents swallow their own errors (step 2), this branch is rarely reached; in practice the breaker mostly counts the "max retries" exits (:101). The breaker opens at 5 failures. After 30 s the next check makes it half-open, and 2 successes close it again (`circuit_breaker.py:11-53`).

### README vs code
- README says "Query reformulation strategies per failure type" (`README.md:46`). The sub-query branch returns `sub_queries` with `reformulated_query=None` (`planner_agent.py:39-44`), and the orchestrator keeps only `reformulated_query or query` (`fallback_orchestrator.py:83`). So the decomposition is thrown away. The retriever never reads `sub_queries` either (`retriever_agent.py:12`).
- README says the "EnhancedValidatorAgent" does "structured validation" (`README.md:40`). The code is `random.random() < 0.3` (`validator_agent.py:19`).
- The frontend demo buttons are labelled "(success)" (`frontend/src/App.js:63-68`), but each attempt still fails validation 30% of the time. So about 30% of these requests need at least one retry, and about 2.7% (0.3³) end in "Max retries exhausted" (worked out from `validator_agent.py:19` and the 3 attempts at `fallback_orchestrator.py:42`).

### Where it is thin or wrong
- [misleading] The validator is random, so every success and failure count on the dashboard is random.
- [misleading] The retrieval is fake: the text is LLM-invented, duplicated, and has a fixed relevance (`retriever_agent.py:21-29`).
- [bug] The decomposed sub-queries are dropped (see above).
- [misleading] `RetryMetrics.delay_seconds` is a fresh random draw of the base backoff, not the delay that was actually slept (`fallback_orchestrator.py:52` vs `:86`).
- [shallow] The breaker counts a validation failure once per request (:101) but an exception once per attempt (:90). A success in the closed state lowers the count by 1 (`circuit_breaker.py:43`), so it is a leaky counter, not "5 failures in a row". `half_open_max_calls` is never enforced (:14).
- [ok-for-demo] `get_state()` calls `is_open()`, which can change the state, so reading /metrics changes the breaker (`circuit_breaker.py:62`).
- [bug] **Success reported during an outage.** If every Gemini call fails (a bad key, or a retired model id), the retriever returns its "fallback.pdf" stub (`retriever_agent.py:30-38`). The random validator still passes 70% of attempts, so the API returns success=true with the stub as its context (`fallback_orchestrator.py:59-77`). The breaker never sees the outage.
- [misleading] **Backoff on the wrong path.** The sleeps follow *validation* failures (`fallback_orchestrator.py:86-87`), where waiting cannot change a quality verdict. The *exception* path, where 429s and timeouts would land, retries at once (:89-98).
- [misleading] The three "(simulated failure)" demo buttons (`frontend/src/App.js:69-71`) always end in "Max retries exhausted", and each adds one breaker failure (`fallback_orchestrator.py:101`). Five of them in a row open the breaker, and then even the "(success)" buttons are refused for 30 s.
- [shallow] The synchronous `generate_content` runs inside `async def` methods (`retriever_agent.py:20`, `planner_agent.py:37`), so each Gemini call blocks the FastAPI event loop and other requests wait.

### Tests and data
- `scripts/test.sh` waits up to 30 s for /health (and exits 1 if the backend never comes up), then sends one normal query, one simulated failure, and reads the metrics. Apart from that wait, it only prints results (:10-40). There is no data.

### What to take for your project
- A2/V3, later in Phase 10: a small table that maps failure type to fix, a bounded number of attempts, and a final abstain message instead of a guessed answer. Your grader must be real (V2), not random.
- D2: write one `call_llm()` wrapper for Groq. It backs off with jitter only on HTTP 429 and timeouts, caps the attempts, sits behind your record/replay cache (a replayed call never retries), and logs each retry in the trace. That is the opposite of this lesson, which backs off after quality failures. A circuit breaker is overkill for a one-user notebook project. Skip the code itself.

### Try this
- 15 min, reading only. With `simulate_failure=true`, hand-trace one request. Count the LLM calls and sleeps, and the expected total sleep for each failure type (`retry_policy.py:14-15`, base 1.0, jitter 0.3). Then write down what a real "insufficient context" handler would do for your PDFs: retrieve for each sub-query, merge, and grade again.

### Interview angle
- **Q:** "Retry, fall back, or abstain: how do you decide?" **A:** Retry with backoff for transient errors like 429s and timeouts. Apply a fix, such as rewriting the query or widening retrieval, when a grader says the context is weak. Abstain when the fixed attempt still fails. Waiting never fixes a weak context, so backoff belongs only on transient errors. A circuit breaker stops you hammering a dependency that is down.

---

## L41 · Synthesizer agent: chained prompts and citations  (`lesson41/vaia-l41-synthesizer/`)

**What the code teaches, in one line:** You hand it chunks in the request. It runs 1, 3 or 5 chained Gemini calls ("CoT steps"), then a separate LLM call maps claims to chunk IDs, and another LLM call judges the result. "Confidence" is computed from answer length.
**What it is not:** It is not retrieval, because the chunks come with the request. It does not put citations inline. It does **not verify citations**: the only check is that the chunk ID exists.
**Relevance to your RAG study:** Medium (useful as a contrast case). Concepts: C5 (counter-example: citations mapped after the answer is written), V1 (counter-example: no support check), P7, M3 (a weak LLM judge) [Interview]
**Stack:** FastAPI, structlog, google-generativeai 0.8.0 (`requirements.txt:2`). The model comes from `GEMINI_MODEL`, default `gemini-2.0-flash-exp` (`backend/main.py:84`, `.env.example:5`). No embeddings, no store. Without a key (or with the placeholder key), /synthesize returns a **canned demo answer** (`main.py:91-122`, `:141-142`). The frontend has a query box that always sends one placeholder chunk (`frontend/src/App.js:16-18`), Run Demo, a confidence badge, citations and reasoning steps.
**Swap to your stack:** easy. There are three call sites (`cot_engine.py:151`, `citation_mapper.py:38`, `coherence_validator.py:39`), but a request needs 3–7 calls, which is slow on a free tier.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/agents/synthesizer_agent.py` | runs the steps | :23-107 |
| 2 | `backend/agents/cot_engine.py` | complexity rule, step plans, prompts, confidence | :13-47, :49-166 |
| 3 | `backend/agents/citation_mapper.py` | after-the-fact mapping, "inject" | :12-76 |
| 4 | `backend/agents/coherence_validator.py` | LLM judge, "citation accuracy" | :10-65 |
| 5 | `backend/models/synthesis_models.py` | Chunk, and a Citation with no claim field | :22-35 |
| 6 | `backend/main.py` | demo chunks and the mock answer | :91-122, :163-220 |

### How it works, step by step
1. POST /synthesize/demo builds 3 chunks with source, section and quality_score (`main.py:166-188`). The query is "How does the Synthesizer Agent implement explainability in production VAIAs?".
2. Complexity: under 10 words with at most 2 chunks is SIMPLE (1 step). Under 25 words with at most 5 chunks is MODERATE (3 steps). Anything else is COMPLEX (5 steps) (`cot_engine.py:19-24`). The demo has 10 words and 3 chunks, so it is MODERATE.
3. Each step is a separate Gemini call with default sampling, because no temperature is set (`cot_engine.py:151`). MODERATE runs context_summary (sees the chunks), then claim_formulation (sees only the summary), then citation_mapping (sees the claims and the chunks) (:71-100). This is prompt chaining, not one chain-of-thought. The step prompts label chunks `[Source i: source]`, never by chunk id (`cot_engine.py:55-58`).
4. The "final answer" is the output of the **last** step (`synthesizer_agent.py:60`). In MODERATE mode that last step is the claim-to-source mapping text, so the user gets a mapping, not a prose answer. In COMPLEX mode, `final_assembly` sees evidence notes and a coherence note, **but not the chunks** (`cot_engine.py:138-148`).
5. **How citations are produced.** Another LLM call gets the final text plus the chunks, labelled `[Chunk i ID: …]`. It must output lines of the form `CITATION: claim | chunk_id | excerpt` (`citation_mapper.py:15-36`), which a regex then parses (:43-44). A citation is kept only if its chunk_id equals a real id (:48-49). The claim text is parsed and then **thrown away** (:46). The excerpt is the LLM's own text, cut to 200 chars, and is never checked against the chunk (:54). Citation confidence is just the chunk's input `quality_score`, or 0.8 when that is 0 (:55).
6. `inject_citations` builds a reference map it never uses (:63-66). It only appends a "Sources:" list of `[i] source, §section`, one line per citation, so the same source can repeat (:69-74). No markers ever go into the answer text.
7. `CoherenceValidator`: an LLM rates CITED, UNSUPPORTED, COHERENT and SCORE, but it sees only the first 200 chars of each chunk (`coherence_validator.py:15-37`). It is told only *how many* citations exist, not which claim cites which chunk (:25). Missing fields default to the passing value, and SCORE defaults to 75 (:43-50). "citation_accuracy" is the share of cited IDs that exist (:53-54). Step 5 already filtered to real IDs, so this is always 1.0. The answer counts as valid if all checks pass and the score is at least 70 (:56).
8. If the answer is invalid, the state becomes REGENERATE_REQUIRED, but the same response is still returned and nothing is retried (`synthesizer_agent.py:77-80`).
9. Step confidence is min(0.95, 0.6 + words/500) (`cot_engine.py:155`), and the overall confidence is the mean of those (`synthesizer_agent.py:85-86`).

### README vs code
- README says "CoT Engine (3-7 steps)" (`README.md:41-42`). The plans have 1, 3 or 5 steps (`cot_engine.py:30-47`).
- README promises "Adaptive XAI formatting" (`README.md:34`). `XAIFormatter` is created (`synthesizer_agent.py:20`) but `format_output` is never called, so the frontend's `requires_full_xai` flag (`frontend/src/App.js:68`) does nothing.
- README promises "Automatic citation mapping" (`README.md:32`). It is there, but done by the LLM after the answer is written, and the result is a source list at the end, not inline citations (`citation_mapper.py:69-74`).
- `.env.example:11-17` sets COT_MAX_STEPS, CONFIDENCE_THRESHOLD, SYNTHESIS_TIMEOUT and LOG_FILE. The code never reads any of them.

### Where it is thin or wrong
- [misleading] Confidence is word count (`cot_engine.py:155`): a longer answer counts as "more confident".
- [bug] In MODERATE mode the answer is the mapping step's output (`synthesizer_agent.py:60` with `cot_engine.py:35-39`).
- [bug] The format line shows placeholders in square brackets. If the model copies them, the regex captures `[chunk_001]` with the brackets, the ID lookup fails, and the citation silently disappears (`citation_mapper.py:33-49`). I confirmed the regex does this on a made-up string. How often Gemini copies the brackets is UNVERIFIED.
- [misleading] citation_accuracy is circular: it re-checks what step 5 already guaranteed (`coherence_validator.py:53`).
- [shallow] The judge sees only 200-char chunk heads (:15), and when it fails it defaults to "pass" (:43-50).
- [ok-for-demo] The mock answer is hard-coded: its text and its "Sources" list (the three demo chunk sources) are returned whatever chunks you send, and its step confidences (0.88, 0.85, 0.9; overall 0.87) are invented (`main.py:95-118`). Its `citations` list is just the first 5 chunks you sent, so every chunk counts as cited whatever the text says (:109-112). It is at least flagged with `metadata.mock=True` (:121).
- [shallow] The judge gets only a citation count (`coherence_validator.py:25`) and a response whose Sources list has no markers in the text. So "are factual claims properly cited?" is answered without the claim-to-chunk map.
- [misleading] `CITATION_GRANULARITY` is read (`main.py:85`) and stored (`citation_mapper.py:10`), but nothing uses it, so changing the "granularity" changes nothing.
- [shallow] Every Gemini call is synchronous inside the `async def` endpoints (`main.py:139-145`, `cot_engine.py:151`), so one request of 3–7 calls blocks the whole server while it runs.

### Tests and data
- `test.sh` checks health and runs the demo. It prints counts and always ends with "All tests passed" (`test.sh:36-47`). The 3 demo chunks are too few to practise on.

### What to take for your project
- Use this lesson as the counter-example for C5/V1, and do **not** copy the after-the-fact mapping. Instead, number the chunks in the prompt, require `[n]` markers inline, and map markers to chunk IDs in code (L43 does this). Then **verify** each cited sentence against its chunk (V1), and log the unsupported ones.
- Keep the *shape* of a citation record, (claim, chunk_id, excerpt), but keep the claim, which this code drops.
- For C5 on your stack, one grounded Groq call is enough. The 3–7 chained calls here add latency and cost (D2) without adding any grounding. In ragkit this means three plain functions: build the numbered context with a number-to-chunk-id map, extract the `[n]` markers, and verify each cited sentence.

### Try this
- 25 min, plain Python, no LLM. Take the 3 demo chunks (`main.py:166-188`). Write a 3-sentence answer with `[1]`–`[3]` markers yourself, and make one sentence wrong. Write a 20-line checker that splits sentences, finds the markers, and flags any sentence whose word overlap with its cited chunk is below 0.3. Compare that with what `citation_mapper.py` "verifies", which is only that the ID exists.

### Interview angle
- **Q:** "How do you make RAG citations trustworthy?" **A:** Have the model cite numbered chunks inline as it writes, and map the markers to chunk IDs in code. Then check every cited sentence against the chunk it cites, and flag or drop the unsupported ones. An ID that exists is not evidence of support.

---

## L42 · Traceability layer: trace context, spans, audit sink  (`lesson42/l42_traceability/`)

**What the code teaches, in one line:** A trace held in a ContextVar, plus a `@trace_step` decorator that wraps each agent call in a timed span. An async sink writes each finished trace to SQLite and to a JSONL file, and query endpoints serve a waterfall, latency and risk views.
**What it is not:** It is not OpenTelemetry or LangSmith. It is **not replayable**, because prompts, model parameters, the answer text and (for real-size chunks) the full retrieved text are not stored. Out of the box it also runs a **canned demo**.
**Relevance to your RAG study:** Medium. Concepts: D1, C6 (partial: chunk IDs per step, but no answer text), C4 (counter-example: word overlap labelled "semantic") [LLMOps] [Interview]
**Stack:** FastAPI, aiosqlite, aiofiles, sse-starlette. google-generativeai 0.7.2 (`requirements.txt:3`) with `gemini-1.5-flash` hard-coded (`backend/agents/planner.py:11`, `validator.py:10`, `synthesizer.py:10`). The "retriever" is keyword overlap over 6 hard-coded sentences (`backend/agents/retriever.py:13-20`), yet it reports `model_id` gemini-1.5-flash (:10, :43). No embeddings and no README. The frontend has a query panel, waterfall, risk and latency per agent, a live SSE tail and history.
**Swap to your stack:** easy. The tracing code does not depend on the provider, and the three agent calls only need a new client and the same JSON parsing.
**Folder vs setup.sh:** demo mode exists only in the generated `pipeline.py` (compare `setup.sh:889-956`). `setup.sh` writes an empty `GEMINI_API_KEY` into `.env` (`setup.sh:10`, `:57-64`), and `scripts/start.sh:5` exports that file, so **the default run is the demo**.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/tracing/context.py` | Span, TraceRecord, TraceContext (mint, start_span, finalize) | :33-173 |
| 2 | `backend/tracing/decorator.py` | `@trace_step` | :10-71 |
| 3 | `backend/agents/*.py` | what each `to_trace_dict` keeps | planner :25-33; retriever :32-44; validator :28-42; synthesizer :22-34 |
| 4 | `backend/agents/pipeline.py` | `run()` and `_run_demo()` | :16-21, :32-146 |
| 5 | `backend/storage/sink.py` | queue, SQLite and JSONL writes | :30-75, :91-140 |
| 6 | `backend/storage/query.py` | waterfall, risk and latency SQL | :13-88 |
| 7 | `tests/test_traceability.py` | 8 tests of the tracing objects | :12-134 |

### How it works, step by step
1. POST /query (`backend/api/app.py:43-47`). If `GEMINI_API_KEY` is empty or DEMO_MODE=1, it runs `_run_demo`: four spans with fixed decisions, fixed confidences (0.8, 0.85, 0.9, 0.88), `asyncio.sleep` standing in for latency, and a canned answer (`pipeline.py:16-21`, `:32-90`).
2. Live path: `TraceContext.mint` makes a trace_id and a request_id and puts the context into a ContextVar (`context.py:126-138`).
3. Each agent method carries `@trace_step`. The decorator starts a span and stores `str(arg)[:512]` for each named input. It then awaits the method and copies the result's `to_trace_dict()` into the span. If the method raises, the span gets status=error and the message (`decorator.py:24-68`). Capture names are matched to arguments by *position*, not by parameter name (:33-38). The pipeline passes keyword arguments, so today the keyword branch is used (`pipeline.py:107-119`).
4. The agents:
   - Planner: Gemini JSON gives intent, sub_queries, a STRICT/BROAD/DEFAULT strategy and a self-reported confidence (`planner.py:42-67`).
   - Retriever: score = shared words / (query words + 1). STRICT multiplies the scores by 1.3, and the top 3 are kept (`retriever.py:54-69`). Words are split on spaces only, so punctuation stays attached: "rag?" does not match "rag" (:56-58). The STRICT boost multiplies every positive score by the same factor, so it cannot change the order; only the reported top score moves (:63-65). The planner's sub-queries are never used (`pipeline.py:107-109`).
   - Validator: Gemini JSON gives verdict, risk, flags and hints from the first 800 chars of the docs (`validator.py:50-80`).
   - Synthesizer: Gemini JSON gives reasoning_chain, response, citations and confidence (`synthesizer.py:45-79`).
   - A FAIL verdict does not stop synthesis; only the correction hints are passed on (`synthesizer.py:48-50`, `pipeline.py:117-119`).
5. `finalize()` marks the trace failed if any span errored. It sets confidence_delta = synthesizer confidence minus planner confidence (`context.py:150-170`).
6. Sink: `enqueue` puts the record into a 2000-slot queue and an in-memory ring, and drops the record when the queue is full (`sink.py:26`, `:91-97`). A background worker runs INSERT OR REPLACE into the `traces` and `spans` tables, then appends one JSON line (`sink.py:105-140`). If a write fails, the worker prints the error and the record is gone (:88-89); the caller has already received its answer.
7. Reads: /trace/{id} returns spans ordered by started_at; /stats/latency gives average, min and max per agent; /live-tail polls the ring every 0.3 s (`query.py:22-88`, `app.py:83-96`).

### What one audit record contains (and can it be replayed?)
- **Stored:** trace_id, request_id, query (up to 1024 chars), status, confidence_delta, and created/finalized times. For each span: agent, status, a decision string, risk, confidence, latency, token counts, model_id, error, flags, `input_summary` (the `str()` of each captured argument, each cut to 512 chars) and the agent's chosen `output_summary` (`sink.py:34-66`, `decorator.py:33-40`).
- **Not stored:** the rendered prompts and parameters. The retriever span keeps only chunk IDs; the validator span's `input_summary` does hold `str(docs)` cut to 512 chars (`validator.py:46`, `decorator.py:33-40`). With these 6 short sentences that covers all 3 retrieved docs, but real chunks would be cut off after the first few hundred characters. It also lacks the **answer text** and the **citations**: the synthesizer keeps only response length, citation count and confidence (`synthesizer.py:24-28`). There is no code or corpus version and no wall-clock time field (only the home-made trace_id encodes time, see below).
- **Verdict:** it cannot be replayed. You can see *that* a step ran, how long it took and what it decided, but not *what the user was told* or *why*.

### README vs code
- There is no README. The `setup.sh` banner promises "the 4-agent traced pipeline" (`setup.sh:1933`). With the default empty key you get the canned demo trace instead.
- The sink.py docstring says "JSONL (immutable archive)" (`sink.py:2`). It is a plain append file, and SQLite uses INSERT OR REPLACE (`sink.py:108,119`), so rows can be overwritten.

### Where it is thin or wrong
- [bug] **The retriever crashes on ties.** It sorts (score, dict) pairs (`retriever.py:67`). When two scores are equal, Python tries to compare two dicts and raises TypeError. With 6 docs, ties (above all at 0.0) happen on almost every query, so the live pipeline returns "failed". I reproduced the pattern with my own snippet. Demo mode hides the crash, and no test calls the retriever.
- [bug] Timestamps use `time.monotonic()` (`context.py:66,130,145,157`). That clock has an arbitrary starting point (on Linux, usually boot), not wall-clock time. The audit rows therefore carry no real dates, and their ordering breaks after a reboot. Only the trace_id, built from `time.time()` (`context.py:14`), encodes the real time, to about 64 ms. /stats/risk-timeline also subtracts 24 h from the monotonic clock (`query.py:42`). That filter works only until the machine reboots; after that, older rows sit on a different clock and are counted wrongly.
- [misleading] **A "rerank" that cannot rerank.** The comment says the strict strategy boosts exact matches (`retriever.py:63`), but a constant factor keeps the order (:65). The docstring says it "simulates semantic retrieval" (:2), but the code is plain word overlap (:54-61).
- [shallow] **Audit records can vanish silently.** A full queue drops the record (`sink.py:96-97`), and a failed write is only printed (:88-89). In an audit layer, a lost record should raise an error or at least be counted.
- [bug] (latent) The decorator maps capture names by position (`decorator.py:33-38`). The validator lists `["intent", "docs"]`, but its parameters are `(docs, intent, query)` (`validator.py:46-48`), so a positional call would store the docs under "intent". The pipeline uses keywords today, so it does not happen yet.
- [shallow] The synthesizer prompt has no "answer only from the sources" or "say you do not know" rule (`synthesizer.py:52-65`), so nothing keeps the answer grounded.
- [shallow] Gemini is called synchronously inside `async def` methods (`planner.py:52`, `validator.py:66`, `synthesizer.py:66`). That blocks the event loop, so the SSE live tail and the sink worker stall during each call.
- [misleading] The retriever's "tokens" are word counts, and it claims the model gemini-1.5-flash (`retriever.py:43,76-77`).
- [misleading] Risk and confidence are numbers the LLM reports about itself, and confidence_delta subtracts one such number from another (`context.py:161-169`).
- [bug] /trace/{id} never returns 404. An unknown id still returns `{"spans": []}`, which counts as true (`query.py:28-38`, `app.py:58-59`).
- [shallow] The synthesizer prompt numbers the docs [1]..[3] but never shows their ids, while asking for "doc_id" citations (`synthesizer.py:45-47,63`). The citations are unchecked strings.
- [shallow] `_uuid7` is home-made: the version digit overwrites part of the timestamp, so IDs sort only to about 64 ms (`context.py:12-18`). The `uuid6` package is installed but unused (`requirements.txt:14`).

### Tests and data
- The 8 pytest tests check the tracing objects and the sink only: ID length 36, span latency of at least 10 ms, the confidence_delta arithmetic, failed status, to_dict, the ring buffer, and that the JSONL contains the trace id (`tests/test_traceability.py:12-134`). None of them calls an agent. T7 checks only the in-memory ring, which `enqueue` fills before anything is written (`sink.py:94-95`), so it passes even if SQLite fails. T8 is the only test of persisted output (`tests/test_traceability.py:114-134`). There is no practice data.

### What to take for your project
- D1/C6, in plain Python: a ContextVar trace, a decorator that times each step and records its inputs and outputs, and append-only JSONL per run. Bind inputs by parameter name (for example with `inspect.signature`), not by position. In a one-user notebook, write synchronously (no queue) and raise on a failed write. This fits your cached record/replay notebooks.
- Add what C6 needs and this lesson lacks: chunk IDs, scores and text hashes; prompt template version and rendered-prompt hash; model id and parameters; raw output; parsed citations; verification results; wall-clock time; `snapshot_id`. Use wall-clock ISO time for "when" and `time.perf_counter()` only for durations.
- LangSmith comes later (D-32), after this plain tracer works, and never with book text in the payload.
- Sort with `key=`, never on tuples that contain dicts.

### Try this
- 20 min. Make a table of every field written in `sink.py:105-140`, with a second column: "needed to replay or audit the answer? yes / no / missing". Then list the fields your ragkit provenance trace needs that are not here. Bonus: reproduce the sort crash with 3 dicts in your own scratch file, and fix it.

### Interview angle
- **Q:** "What would you log per RAG request so you can debug an answer a week later?" **A:** One trace id across every step. Per step: the inputs, outputs, model and prompt version, latency and tokens. On top of that, the retrieved chunk IDs and scores, plus the exact final answer and its citations. Without the answer and its context you can time the pipeline but not audit it.

---

## L43 · Agentic RAG end-to-end  (`lesson43/l43-agentic-rag/`)

**What the code teaches, in one line:** A real but small RAG pipeline. ChromaDB with local MiniLM embeddings holds 15 one-paragraph docs. An optional Gemini **planner** splits the query, and an optional Gemini **chunk grader** drives a bounded re-retrieve loop. A grounded **synthesizer** writes `[n]` citations that are parsed in code, and every query gets a JSON **audit file**.
**What it is not:** By default it is **not agentic**. `FAST_MODE=1` skips the planner and the validator, which leaves plain retrieve-then-generate. There is no chunking (one doc is one chunk) and no keyword or hybrid search (the "strategy" label is ignored). There is no answer-level groundedness check.
**Relevance to your RAG study:** High. Concepts: A5 (only with FAST_MODE=0), A2 (bounded re-retrieve after a low grade), Q1, V2 (relevance grading only; no groundedness check), C4, C5, C6, D1, V3 (prompt only), R1 (counter-example: the "keyword" and "hybrid" strategies are ignored) [LLMOps] [Interview]
**Stack:** FastAPI. chromadb 0.5.23 `PersistentClient` with `DefaultEmbeddingFunction` (`requirements.txt:7`, `backend/agents/retriever.py:15-22`). In Chroma 0.5.x that default is all-MiniLM-L6-v2 run locally through ONNX; this is library behaviour, not visible in the repo (UNVERIFIED here). google-generativeai 0.8.3, with the model from `GEMINI_MODEL`, default `gemini-2.0-flash-lite` (`planner.py:18`, `validator.py:19`, `synthesizer.py:20`). sentence-transformers, tenacity and aiofiles are listed in requirements.txt but unused (`requirements.txt:8,11,12`). No README. The frontend has demo queries, a stage bar, an answer with clickable citations that open a source page, and a history and audit viewer.
**Swap to your stack:** moderate. Replace Chroma's embedding function with Cohere `embed-v4.0` (it uses different input types for queries and documents), or keep MiniLM as your fallback. There are three Gemini call sites to move to Groq. The 429 helper parses Gemini's error text. With gpt-oss-20b, `max_output_tokens=512` can be used up by reasoning, so set `reasoning_effort="low"` and raise max_tokens.
**Folder vs setup.sh:** the `setup.sh` orchestrator always runs all 4 agents (`setup.sh:728-807`), and its synthesizer uses a 6000-char budget and 1024 tokens (`setup.sh:621`, `:661`). The generated folder adds FAST_MODE (on by default; nothing in scripts or compose turns it off), the 429 helper, canned answers and a 4 s cooldown, and it lowers the synthesizer's limits to 4000 chars and 512 tokens.
**Your copy:** in `Book RAG/prior_work/VAI/lesson43/l43-agentic-rag/`, the backend files are byte-identical to the original (`diff -rq`). Only `.env.example`, the Dockerfiles and `frontend/src/App.jsx` are missing, so you did not change the code.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/core/models.py` | typed objects passed between agents | :12-109 |
| 2 | `backend/core/orchestrator.py` | fast vs full path, retry loop, error exit | :21-102 |
| 3 | `backend/agents/retriever.py` | Chroma query, merge, score, ingest | :38-100 |
| 4 | `backend/agents/planner.py` | decomposition prompt and fallback plan | :20-90 |
| 5 | `backend/agents/validator.py` | LLM chunk grading and the pass rule | :21-109 |
| 6 | `backend/agents/synthesizer.py` | context budget, prompt, marker parsing, 429 fallback | :22-147 |
| 7 | `backend/core/tracer.py` | per-trace audit JSON | :15-75 |
| 8 | `backend/seed_knowledge_base.py` | the 15 docs | :10-44 |
| 9 | `backend/api/app.py` | cooldown, /audit, /history, /documents/source | :47-146 |

### How it works, step by step (one query: "How many GPU clusters does our ML infrastructure have?", a demo query at `frontend/src/App.jsx:20`)
0. **Seed.** `start.sh` runs the seed script (`scripts/start.sh:21-22`), which adds 15 paragraphs with fake filenames and random uuid4 ids (`seed_knowledge_base.py:10-44`, `retriever.py:92-100`). It skips seeding if there are already 15 or more docs (:50-54). There is no chunking step.
1. **Request.** POST /query with `{query, collection, max_results=3}`. If the previous query *finished* under 4 s ago, it returns a made-up result instead (`app.py:51-65`, `:68`). `top_k = min(max_results, 5)`, which is 3 here (`orchestrator.py:36`). The `collection` field is ignored (`app.py:38`).
2. **FAST path (default)** (`orchestrator.py:21-22`, `:39-55`): the plan is just the query. It retrieves, then wraps the top chunks as "validated" with quality = retrieval score and risk = 0.2 (:50-53), and goes straight to step 6.
3. **Planner (FULL path, Q1).** Gemini, at temperature 0.1 with 512 max tokens, is asked for 1–3 sub-queries, each with a strategy (semantic, keyword or hybrid) and a priority (`planner.py:20-59`). Code fences are stripped and the JSON parsed. On any error, the fallback plan is the raw query (:73-80). The strategy, priority and retrieval_mode fields are never used afterwards. If the JSON parses but has no `sub_queries`, the plan is empty rather than the fallback (:69). Then nothing is retrieved, all 3 attempts fail, and the synthesizer gets an empty context.
4. **Retriever (C4).** For each sub-query it asks Chroma for `top_k + 3·(attempt−1)` results, capped at 20 (`retriever.py:50-57`). It removes duplicate ids and sets score = 1 − distance (:62). If Chroma's default distance is squared L2 and the MiniLM vectors are unit length, the score equals **2·cos − 1** (this follows from Chroma's defaults, not from this repo; UNVERIFIED here). It sorts and keeps at most `top_k·2` = 6 chunks (:74-80). With one sub-query, attempt 1 asks for only 3, so you get 3. An error on a sub-query is silently swallowed (:70-71). A chunk found by two sub-queries keeps the score of the first sub-query that found it, not the best one (:59-69), and there is no rank fusion such as RRF.
5. **Validator (V2, FULL path).** Gemini at temperature 0.0 scores up to 8 chunks, reading the first 300 chars of each, for quality and "risk of hallucination" (`validator.py:24-36`, `:85-98`). A chunk passes if quality ≥ 0.55 and risk < 0.8 (:21, :65). The **whole step** passes if the **average** quality over all chunks is ≥ 0.55 (:74, :80). If the LLM skips a chunk or its JSON fails to parse, that chunk gets its retrieval score instead (:64, :107-109). The step outputs the passing chunks, or the top 3 if none pass (:77). The audit field `chunks_passed` counts that output, so it says 3 even when none passed (:118). If the step fails, the orchestrator retrieves again with a bigger k and grades again, up to 3 attempts in all (`orchestrator.py:64-71`). After that it synthesizes anyway.
6. **Synthesizer (C5).** Each chunk is cut to 500 chars and added until the next one would push the context past 4000 characters; `TOKEN_BUDGET` is really a character budget (`synthesizer.py:22`, `:120-131`). At top_k = 3 you have at most 6 × 500 = 3000 chars, so the budget never bites here. The prompt says: answer only from the context, cite `[1]`, `[2]`, and give a fixed "not enough information" sentence when the answer is missing (:33-44). It runs at temperature 0.2 with 512 max tokens (:71-74). On a 429, it waits once for 15–70 s (`genai_retry.py:10-30`). After that it returns a **canned answer** for the 5 demo queries, or a "rate limit" message (`synthesizer.py:25-31`, `:79-89`). An error counts as a rate limit if its message contains "429", "quota" or "rate" (`genai_retry.py:19`, `synthesizer.py:81`); "rate" also matches "generate", so other errors can be misread. Any other error becomes the answer text "Synthesis error: …" with state DONE (`synthesizer.py:90-91`, `:109`).
7. **Citations.** A regex finds each `[n]` and keeps it if n maps to a chunk in the context, removing repeats. The snippet is the first 100 chars of that chunk (`synthesizer.py:133-147`). Grouped markers such as `[1, 2]` or `[1-3]` do not match the pattern and are dropped (:136). Nothing checks that the cited sentence is actually supported.
8. **quality_score** is the mean quality of the chunks (the retrieval score in fast mode), or 0.5 if that is 0 or less (`synthesizer.py:97-99`). With an empty context it is still 0.5. It measures **retrieval**, not the answer.
9. **Trace (C6/D1).** Every agent appends a TraceEvent with agent, state, input, output, latency, a wall-clock timestamp and the attempt number. `finalize` writes `backend/data/audit_logs/<trace_id>.json` with all the events plus the full result, meaning the answer and its citations (`tracer.py:33-52`). If the write fails, the error is swallowed (:48-51).
- For this query, the corpus says "a cluster of 200 A100 GPUs" (`seed_knowledge_base.py:19`). A good answer says one cluster, or refuses. What Gemini actually says is UNVERIFIED.

**What the audit file lets you check:**
- Planner event: the full plan.
- Retriever event: the sub-queries, the attempt, the chunk *count* and the top score, but **not the chunk IDs** (`retriever.py:86-87`).
- Validator event: the average, pass/fail and a count, but not *which* chunks passed (`validator.py:116-118`).
- Final result: the answer, plus the cited chunk ids, sources and snippets.
- Missing: the uncited context chunks, the prompts, the model id, the parameters, and per-event errors (`TraceEvent.error` is never set).
- So you can re-read the answer and its cited chunks, but you cannot re-check faithfulness against the full context or replay the run.

### README vs code
- There is no README. The API description and the UI both say "Planner → Retriever → Validator → Synthesizer" (`app.py:21`, `frontend/src/App.jsx:377`), but the default FAST_MODE skips two of the four stages. The stage bar still turns every stage green at "done" (`App.jsx:24-43`).
- The `/history` docstring says it is "Consumed by L44 Ragas evaluator" (`app.py:82`). L44 never calls it, and the audit lacks the `retrieved_contexts` field that L44's `TraceRecord` needs (`lesson44/.../backend/app/models.py:46`).

### Where it is thin or wrong
- [misleading] FAST_MODE is on by default (`orchestrator.py:22`), so out of the box this is not agentic RAG.
- [bug] **The self-correction loop works against itself.** A retry only widens k, which adds lower-ranked chunks, which tends to *lower* the average quality that the pass rule checks (`retriever.py:50` with `validator.py:74-80`). Also, with one sub-query and top_k = 3, attempt 3 returns exactly the same 6 chunks as attempt 2, because results are cut to `top_k·2` (`retriever.py:79`). That makes attempt 3 a wasted LLM call. (Worked out from the code, not run.)
- [shallow] The pass rule uses the *average*, not "at least m good chunks". Fallback retrieval scores (1 − distance) and LLM scores get mixed in one average (`validator.py:64`).
- [shallow] There is no abstention in code: if nothing passes, the top 3 are used anyway (`validator.py:77`). Only the prompt can refuse.
- [misleading] The canned 429 answers contain `[1]`, so they get a real-looking citation to chunk 1 and the state DONE (`synthesizer.py:25-31`, `:94`).
- [bug] The cooldown result carries a trace_id that is never written, so /audit for it returns 404 (`app.py:53-65`).
- [bug] `scripts/start.sh:9` and `scripts/test.sh:3-5` hard-code `/home/systemdr5/...` paths.
- [ok-for-demo] Chunk ids are random uuid4 at each seeding (`retriever.py:94`). Re-seeding breaks old traces, and there are no stable ids for an eval set.
- [bug] **Substring error matching.** The check `"rate" in msg.lower()` (`genai_retry.py:19`, `synthesizer.py:81`) also matches "generate". An error message that mentions generateContent (a model-not-found error, for example; the exact wording is UNVERIFIED) is treated as a 429. That means a 65 s sleep when the message names no retry delay (`genai_retry.py:23-30`), one more failed call, then a canned answer with `[1]` (for the 5 demo queries) or the "rate limit" message, with state DONE.
- [misleading] **Errors returned as answers.** A non-rate synthesis error becomes the response text with state DONE (`synthesizer.py:90-91`, `:109`; `orchestrator.py:85`), and `tokens_used` becomes a chars/4 estimate (`synthesizer.py:106`). The UI shows a finished run.
- [bug] An empty `sub_queries` list from the planner gives an empty plan, not the fallback (`planner.py:69`). The run then answers over no context, and `quality_score` still reads 0.5 (`synthesizer.py:97-99`).
- [misleading] The audit's `chunks_passed` reports the fallback top 3 when nothing passed (`validator.py:77`, `:118`).
- [shallow] No abstention flag. The prompt fixes a refusal sentence (`synthesizer.py:36`), but the code never checks for it, so a refusal and an answer look the same in the result and in the audit.
- [shallow] Duplicates keep the first sub-query's score (`retriever.py:59-69`), and grouped citation markers are dropped (`synthesizer.py:136`).

### Tests and data
- `scripts/test.sh` checks that /health returns 200 and that /query returns `trace_id` and `response` keys; either failure exits 1. It also checks that /audit and /history return 200, but those two only print a cross and do not fail the script (:10-29). It never checks the content of an answer.
- The 15 seed docs are small, synthetic and clean. The 5 demo queries make a useful toy set for answerable vs tricky questions: the "GPU clusters" query is a good abstention probe.

### What to take for your project
- **C5, keep this:** numbered context, inline `[n]` markers, and marker-to-chunk-id mapping in code (`synthesizer.py:120-147`). Add V1 sentence verification on top.
- **V2/A2/V3:** chunk grading with a threshold and a bounded retry is the right shape. Change three things: pass on "at least m chunks pass" rather than the average, change the *query* on a retry rather than only k, and abstain **in code** when nothing passes.
- **C6/D1:** a per-trace JSON with the events and the final result is a good minimal format. Add chunk ids and scores for every step, the prompt and model version, and `snapshot_id`.
- **Q1/R1:** the planner prompt is a fine starting point for decomposition. In FULL mode L43 does retrieve once per sub-query, but it merges by raw score and keeps the first score it sees. Instead, keep the original query as one sub-query, fuse the ranked lists with RRF (R1), and log which sub-query found each chunk.
- **V3:** abstain in code. Check for your fixed refusal sentence, or an empty passing set, and set an `abstained` flag in the trace.
- **D2:** decide "rate limit" from the error type or the HTTP status, never from words in the message.
- **C4 on your stack:** you do not need Chroma at first. Embed with Cohere `embed-v4.0` (or local MiniLM), keep the vectors in a NumPy array, and rank by cosine similarity directly. Then you never have to turn a distance into a score.

### Try this
- 30 min, reading plus a calculator. Hand-trace the GPU query in FULL mode with top_k = 3, and assume the planner returns one sub-query. How many chunks do attempts 1, 2 and 3 return (`retriever.py:50,79`)? Suppose the grader gives the first 3 chunks 0.8, 0.3 and 0.2, and the 3 new chunks 0.1 each. What is the average at attempt 1 and at attempt 2 (`validator.py:74`)? Does the retry help? Write down the rule you would use instead.

### Interview angle
- **Q:** "Walk me through an agentic RAG request, and where it can fail silently." **A:** The flow is plan, retrieve, grade, maybe retry, generate, cite, trace. The silent failures are: the planner falls back to the raw query; retrieval errors are swallowed; grader parse errors fall back to similarity scores; retries only add noise; synthesis errors come back as the answer text; and an answer is generated even when nothing passed. Each of these needs a logged flag, and the last step needs a groundedness check or an abstain path.

---

## L44 · RAG evaluation with an LLM judge and a deployment gate  (`lesson44/l44-rag-evaluation/`)

**What the code teaches, in one line:** Ten hand-written records (question, 2 contexts, answer, ground truth) are scored by four Gemini judge prompts: faithfulness, answer relevancy, context recall and context precision. The scores are averaged and compared with fixed thresholds, which gives PASS/DEPLOYED or FAIL/BLOCKED.
**What it is not:** It does **not evaluate L43**, because it never calls a pipeline. It does not use Ragas by default. It computes no rank-based retrieval metrics (no Recall@k, no MRR), and it does not validate the judge.
**Relevance to your RAG study:** High (as a study object, with heavy caveats). Concepts: M1, M3, D3 (a gate that fails open), M2 (only partly: LLM-judged context recall and precision, no Recall@k or MRR), V4 (counter-example: the judge is never validated) [LLMOps] [Interview]
**Stack:** FastAPI, google-generativeai (>=0.7, <0.8; `backend/requirements.txt:9`). The judge is `gemini-1.5-flash` at temperature 0 with a JSON MIME type (`backend/app/metrics.py:122-130`). An optional Ragas path uses ChatGoogleGenerativeAI `gemini-1.5-flash` with `models/embedding-001` (`metrics.py:247-256`), but ragas, langchain and datasets are **commented out** in `backend/requirements.txt:11-16`. No vector store. The frontend has a run button, polling, a gate badge, metric cards against the thresholds, a radar chart, a per-question table and history.
**Swap to your stack:** easy. The four prompts are plain text. Per your decisions, the judge is a Cohere chat model, run once at the end on stored traces and calibrated against Codex labels.
**Your copy:** in `Book RAG/prior_work/VAI/lesson44/l44-rag-evaluation/`, plus a duplicate in `prior_work/VAI/lesson43/l44-rag-evaluation/`, the backend is identical to the original. The frontend App.jsx, the components and `data/` are missing.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/app/models.py` | TraceRecord, the gate check, thresholds | :26-39, :42-52, :91-96 |
| 2 | `backend/app/metrics.py` | 4 judge prompts, GeminiJudge, evaluate_trace, Ragas path | :21-113, :116-227, :230-293 |
| 3 | `backend/app/evaluator.py` | gold data, run flow, **demo-score swap**, aggregation | :31-42, :59-150, :159-223, :267-281 |
| 4 | `backend/app/main.py` | background run, report storage | :62-151 |

### Exact metrics as coded (judge prompts paraphrased)
- **Faithfulness:** the judge sees the question, the context (joined, first 4000 chars) and the answer. It is told to list the claims, count the supported ones, and return `faithfulness_score` = supported / total (`metrics.py:21-46`, `:146-157`). The code uses the judge's own float, not its counts (:154).
- **Answer relevancy:** the judge sees only the question and the answer, and returns a 0–1 rating that penalises tangents and gaps (:48-68, :159-167). This is **not** Ragas's method, which (per Ragas's design, not checked here) generates questions from the answer and compares embeddings. The gold data itself describes that method (`evaluator.py:109`).
- **Context recall:** needs a ground truth. It counts the ground-truth claims that appear in the context (first 4000 chars) (:70-91, :169-184).
- **Context precision:** each chunk (first 500 chars) is judged relevant or not, and the score = relevant / total (:93-113, :186-197). This is **unranked**, whereas Ragas's version weights by rank (Ragas's design, not checked here).
- **Per record:** the 4 calls run in parallel (:199-227). Any exception or bad JSON becomes **0.0** (:155-157, :219-220). **Per run:** the mean of each metric over all records (`evaluator.py:267-281`).
- **Gate:** faithfulness ≥ 0.85, relevancy ≥ 0.80, recall ≥ 0.75, precision ≥ 0.70 (`models.py:91-96`). A metric that is None is skipped, which means it passes (:37).

### Gold data
- `DEMO_CORPUS` lives in code and has 10 items (`evaluator.py:59-150`). `data/` holds only `reports/.gitkeep`. The topics are RAG and eval definitions. Every answer was written by hand to agree with its two contexts. A few add small details the context does not state (for example "tool use" in the ReAct item, `evaluator.py:93`, and "Retriever and Validator agents" in the Planner item, `:120`), but there are **no deliberately unfaithful, off-topic or unanswerable cases**. That makes it mostly a test of whether the judge says "yes" to easy cases. `num_test_questions` allows up to 50 (`models.py:84`), but only 10 items exist.

### How it works, step by step
1. POST /api/evaluate starts a background task (`main.py:78-89`, `:62-75`).
2. `_build_traces` turns the first n corpus items into TraceRecords (`evaluator.py:225-237`). The "RAG_EXECUTING" phase only writes a log line (:177-181).
3. `try_ragas_evaluate` hits ImportError because the packages are commented out, so the custom judge runs (`metrics.py:288-290`, `evaluator.py:242-263`). It allows 5 records at a time, with a 0.3 s sleep after each.
4. **If all four averages are 0**, for example because the key is invalid or the model id is retired, every item's scores are replaced with `_demo_scores_for_index`: fixed numbers built to pass (`evaluator.py:32-42`, `:190-196`). Per item, every fourth item gets faithfulness 0.84, just under 0.85, but the averages clear every threshold for any run of 2 or more questions (I computed the means from the formula; only a 1-question run would be BLOCKED). The gate then says PASS and the state says DEPLOYED (:203-210). Only a log line records the swap (:193), and the saved report carries no flag. This covers the default 10-question run and the 3-question run in `test.sh:29`. At 2 questions the faithfulness mean lands exactly on 0.85. The swap needs all four means to be exactly 0 (`evaluator.py:45-53`). If only some calls fail, their zeros stay in the means, so a partial outage looks like poor quality.
5. The report is saved twice: once by the evaluator under its own id, and once by main.py under the request id (`evaluator.py:214,283-289`, `main.py:70-75`). Every completed run therefore appears twice in the history list (`main.py:119-151`).

### README vs code
- The metrics.py docstring calls Ragas "primary" (`metrics.py:5`). The README says L44 "consumes TraceRecord objects from L43" and to "Point CHROMA_HOST to L43's ChromaDB" (`README.md:50-51`). In fact no code reads CHROMA_HOST or calls L43, and Ragas is not installed.
- The judge docstring says "with retry logic" (`metrics.py:133`). tenacity is imported but never used (:134).
- The request fields `use_synthetic_dataset`, `corpus_source`, `custom_questions` and `custom_ground_truths` do nothing (`models.py:85-88`, `evaluator.py:163`).

### Where it is thin or wrong
- [bug] **Fake pass when evaluation fails** (`evaluator.py:190-196` with `:32-42`). For any run of 2 or more questions, the gate says DEPLOYED in exactly the case where nothing was measured. This is the worst error in the block.
- [misleading] Errors are scored as 0.0 (`metrics.py:155-157`, `:219-220`). One failed call looks like a hallucination and drags the mean down. If every call fails, the fake pass above kicks in.
- [bug] `asyncio.coroutine` (`metrics.py:214`) was removed in Python 3.11, and the Dockerfile uses 3.11 (`backend/Dockerfile:1`). The branch runs only when the ground truth is missing, which never happens with DEMO_CORPUS. If it did run, it would also make up a recall of 0.75.
- [shallow] The judge's reasoning, unsupported statements and missing aspects are requested and then **thrown away**. `EvalItem.evaluation_reasoning` stays empty (`metrics.py:154,164`, `models.py:58`), so failure analysis (M5) is impossible.
- [shallow] Context is truncated: 4000 chars for faithfulness and recall, 500 per chunk for precision (`metrics.py:151,178,188`). Claims supported by later text count as unsupported.
- [shallow] The judge is never validated: no human labels, no TPR/TNR, no repeat runs.
- [shallow] **Small n, no spread.** The gate compares a mean over at most 10 items with a fixed threshold (`evaluator.py:267-281`, `models.py:32-39`). There is no per-item floor, no confidence interval and no repeat run. With 10 items, a 0.1 change on one item moves the mean by 0.01, which can flip a metric that sits near its threshold.
- [shallow] The judge's counts (`total_claims`, `supported_claims`) are requested but ignored (`metrics.py:154`), so a reply whose counts and score disagree is never caught.
- [shallow] The docstring says temperature 0 gives "reproducible evaluation scores" (`metrics.py:119`). Whether Gemini gives identical verdicts across calls at temperature 0 is UNVERIFIED. Measure it by judging the same item several times.
- [bug] **Security: a Google API key is hard-coded at `docker-compose.yml:8`** (value not copied here). The same line sits in both of your `prior_work` copies. Treat the key as leaked, and never use it.
- [misleading] `gemini-1.5-flash` is an old id. If Google no longer serves it, every call fails, which triggers the fake pass (UNVERIFIED, not run).

### Tests and data
- `test.sh` checks /health, the thresholds and the list. It checks that a run starts and that the report has a "state" after 3 s, and that the modules import (`test.sh:16-44`). It never checks a score, and it never exits non-zero.

### What to take for your project
- **M3:** the four prompts are a fair start. Ask for one verdict per claim (claim, supported yes/no, chunk id, reason) and compute the scores **in code**. Keep the per-claim verdicts and reasons for M5, and record judge errors as `error`, never as 0 and never as a pass. Per your decisions, the judge is a Cohere chat model, run once at the end on stored traces, with every call cached (record/replay).
- **M1:** reuse the record shape (question, contexts, answer, ground_truth), but build the gold set from your project PDFs, never from the book's text (which must not go to an external API). Give each item gold chunk IDs, and include unanswerable and adversarial items.
- **M2:** write `recall_at_k` and `mrr` in plain Python against the gold chunk IDs, kept separate from the answer metrics.
- **D3/LLMOps:** a gate is good, but make it **fail closed** (a missing or errored metric means FAIL). Store n, the judge model id and the prompt version in the report.
- **V4:** validate the judge against your own labels and the Codex calibration labels (TPR/TNR) before you trust any threshold.

### Try this
- 25 min, no API. Take DEMO_CORPUS items 1–3 (`evaluator.py:60-86`). Copy their answers into a scratch file and add one made-up claim to one of them, such as a wrong year. Using the faithfulness rubric (`metrics.py:34-37`), hand-label every claim as supported or not, and compute the scores yourself. Then trace `evaluator.py:190-210` and write down what this service would report if your API key were wrong.

### Interview angle
- **Q:** "How do you make an LLM-judged deployment gate trustworthy?" **A:** Check the judge against human labels (TPR/TNR on a held-out set), and compute scores from per-item verdicts in code. Treat judge errors as errors rather than scores, and fail closed. Version the eval set, the judge model and the prompts, report how many items each mean covers, and keep retrieval metrics (gold chunk IDs) separate from answer metrics.

---

## Block summary
| Lesson | Title | Relevance | Concepts | Best file to read | Biggest problem |
|---|---|---|---|---|---|
| L39 | Validator: compliance rules + audit | Low | D4, V2 (adjacent) | `backend/compliance_engine.py` | LLM rules never see the content (`compliance_engine.py:132-143`); fail-open results cached as passes (:166-179) |
| L40 | Fallback and self-healing | Low | A2 (counter), Q1 (counter), V3, D2 | `backend/fallback_orchestrator.py` | Validator is `random() < 0.3` (`validator_agent.py:19`); retrieval invented by the LLM; an outage still reports success (`retriever_agent.py:30-38`) |
| L41 | Synthesizer: chained prompts + citations | Medium | C5 (counter), V1 (counter), P7, M3 | `backend/agents/citation_mapper.py` | Citations mapped after the fact and never verified (ID-exists only); confidence = length (`cot_engine.py:155`) |
| L42 | Traceability layer | Medium | D1, C6 (partial), C4 (counter) | `backend/tracing/decorator.py` | Audit lacks the answer, prompts and full context, so it cannot be replayed; retriever tie-sort TypeError (`retriever.py:67`); demo by default |
| L43 | Agentic RAG end-to-end | High | A5, A2, Q1, V2, C4, C5, C6, D1, V3, R1 (counter) | `backend/core/orchestrator.py` + `agents/synthesizer.py` | FAST_MODE default skips planner and validator; retry widens k, which tends to lower its own average pass score |
| L44 | RAG evaluation + deployment gate | High | M1, M3, D3, M2 (partly), V4 (counter) | `backend/app/metrics.py` | Fake passing scores replace a failed run, so the gate says DEPLOYED (`evaluator.py:190-196`); API key hard-coded at `docker-compose.yml:8` |

### Cross-lesson patterns
- **They fail open almost everywhere.** L39 caches a pass after an LLM error. L40's retriever turns an outage into a stub document that can still "succeed". L41's judge defaults to pass. L43's grader falls back to similarity and synthesizes anyway, and its synthesis errors come back as DONE answers. L44 substitutes passing scores. Your rule should be the opposite: an error is logged as an error, and the gate fails closed.
- **Mis-named techniques.** L41's "Chain-of-Thought" is prompt chaining. L42's "semantic" retriever is word overlap, and its "rerank" cannot change the order. L43's "keyword" and "hybrid" strategies are ignored, so retrieval is dense only. L44's "Ragas" metrics are custom prompts.
- **Blocking LLM calls in async code.** L40, L41 and L42 call the synchronous `generate_content` inside `async def` handlers, which blocks the server during each call. L43 (`asyncio.to_thread`) and L44 (`run_in_executor`) do it right.
- **Numbers that look like metrics but are not.** L40's validator is random. L41's confidence is word count. L42 uses the LLM's self-reported confidence and risk, and its retriever's "tokens" are word counts. L43's `quality_score` is a retrieval score (1 − distance) in fast mode. L44 hard-codes demo scores.
- **Demo and mock paths that look real.** L41's mock answer, L42's DEMO_MODE (on by default from setup.sh), L43's canned 429 answers carrying `[1]`, and L44's demo scores.
- **Citations are never verified.** L41 checks only that the ID exists, L42 keeps unchecked strings, and L43 maps markers to chunks (the best of the three) but never checks support.
- **Audit trails that cannot replay.** L39 keeps a capped Redis list, L42 has no answer text and monotonic timestamps, and L43 has the answer and the cited chunks but no IDs for the uncited context, no prompts and no model id.
- **Old or experimental Gemini ids on the older `google-generativeai` SDK** (which Google has replaced with a newer SDK; UNVERIFIED here): `gemini-2.5-flash` (L39), `gemini-2.0-flash-exp` (L40, L41), `gemini-1.5-flash` (L42, L44), `gemini-2.0-flash-lite` (L43).
- **Infrastructure listed but unused, and claims that over-reach:** the Postgres libraries in L39 (Redis is used there), Redis, psycopg2 and Prometheus in L40, and Ragas commented out in L44.
- **Generated folders drift from setup.sh:** L42 adds demo mode, and L43 adds FAST_MODE, canned answers and smaller budgets.
- **Weak tests.** Most tests are curl smoke checks that print results and "pass". Only L42 has real unit tests, and they cover the tracer only. No test checks an answer, a citation or a metric value.
- **Your prior_work copies of L43/L44 are unmodified.** The backends are identical to the originals; only frontends and Dockerfiles are missing. They also carry the hard-coded key at line 8 of L44's `docker-compose.yml`.
