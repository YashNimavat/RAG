# VAI lessons 10–18: agents, context engineering and tool calling

[← Guide index](README.md) · Course folder: `C:\Yash\New-Work\RAG\vertical-ai-agents-main\` · Checked 2026-10-17 · Log: [verification/L10-L18_agents_and_tools_log.md](verification/L10-L18_agents_and_tools_log.md)

**What this is:** the guide to VAI lessons 10–18: simple agents, reasoning scores, few-shot, context engineering, state, conversation and tool calling.
**What this is not:** the course code, or a run of it. Nothing in the course was run or copied.

**How to read this file:**
- A `file:line` is relative to the project folder named in the lesson heading.
- **UNVERIFIED** marks behaviour that depends on a library version or on Gemini.
- **(counter)** or † means the lesson names a technique without building it. Read it to learn what is missing.
- Tags: **[bug]** the code does the wrong thing · **[misleading]** a label, message or number claims more than the code does · **[shallow]** it works, but is too thin for your project · **[ok-for-demo]** fine for a demo, not for real use · **[LLMOps]** material for your LLMOps notebooks · **[Interview]** worth practising for interviews.
- "I" means the reviewer who checked the code. Each lesson was checked by a reader, a fact-check pass and a completeness pass; the log has every verdict.

**Notes for this block:**
- Lesson 16 has no generated project folder, so its citations are `setup.sh:<line>`.
- Some SDK behaviour (Gemini SDK 0.8.6, tiktoken) was checked in scratch scripts outside the course folder; the lessons themselves were not run.
- Several `setup.sh` files and some generated files in this block hard-code a Google API key. Values are not repeated here.

---

## L10 · Simple state-machine agent  (`lesson10/l10-simple-agent/`)

**What the code teaches, in one line:** You see the shape of an agent step (think → act → self-evaluate → log). But the "act" does nothing, so the loop is one LLM call plus the LLM grading itself.
**What it is not:** It has no tools, no real actions, and no loop that runs by itself. Each HTTP call runs exactly one step.
**Relevance to your RAG study:** Low. Concepts: A5 (counter-example: loop shape only, the action is simulated), D1 (decision log), M3 (counter-example: the model grades its own step, unvalidated). [LLMOps] (the decision log is a crude per-step trace)
**Stack:** FastAPI, `google-generativeai>=0.8.0`. Gemini model chosen on first use: it tries `gemini-pro`, `gemini-1.5-flash`, `gemini-1.5-pro` with a live test call, then any listed model, then `gemini-pro` as a last resort (`backend/agent.py:79-115`). No embeddings and no vector store; memory is JSON files. The UI shows the state, a progress bar and the decision log.
**Swap to your stack:** easy. Two plain prompt calls; swap them for Groq chat completions and parse the JSON.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/agent.py` | Memory classes, `SimpleAgent.act` | 9-54, 144-163, 245-300 |
| 2 | `backend/main.py` | 5 endpoints | 29-60 |
| 3 | `data/agent_001_decisions.json` | Logged runs | whole file |

### How it works, step by step
1. `POST /agent/act` calls `agent.act(content, goal)` (`backend/main.py:37-43`).
2. The state becomes THINKING. `_build_context` pastes the last 5 short-term messages and up to 3 "relevant" long-term memories into a prompt that asks for the next action (`backend/agent.py:144-163, 257`). Five messages is about 2.5 turns, because each turn stores a user and an agent message (`backend/agent.py:132-133`).
3. `_generate_action` calls Gemini. If the reply contains the word "because", the text after it is stored as the "reasoning" (`backend/agent.py:177-181`).
4. ACTING: `_execute` sleeps 0.5 s and returns "Executed: " plus the action text (`backend/agent.py:193-202`).
5. EVALUATING: a second prompt asks Gemini for JSON with `goal_achieved` and `progress_percentage`. The code strips code fences and parses it; any error becomes 0 % (`backend/agent.py:204-243`). The evaluator sees only earlier turns: the current input is stored after the evaluation (`backend/agent.py:210, 282`).
6. The decision is written to a JSON file. The state becomes COMPLETE, FAILED (after `max_attempts=5`) or READY (`backend/agent.py:73, 270-290`).

### README vs code
- README says "Goal-driven autonomous behavior" (`README.md:34`). The code runs one step per request; nothing repeats on its own (`backend/agent.py:245-300`).
- README says "Production-ready patterns" (`README.md:39`). Errors are turned into the action text and logged as decisions (`backend/agent.py:187-191`).

### Where it is thin or wrong
- [bug] "Relevant past experiences" is almost always empty. Memory keys are `interaction_<timestamp>` (`backend/agent.py:137`). `query` matches the goal's first word against the key string, not the stored content (`backend/agent.py:53-54, 147`). The reverse also happens: a goal whose first word is "in" or "T" matches *every* key, because each key is "interaction_" plus an ISO timestamp that contains a "T".
- [misleading] Self-evaluation grades an action that never ran: the "result" is only an echo (`backend/agent.py:202, 206-218`).
- [misleading] The stored log shows the self-grade cannot be trusted. Of the 4 records with real model text, 3 are marked `goal_achieved: true` at 100 %. Their "action" is only a plan ("Respond with a reciprocal greeting…") and their "result" is the echo of that plan (`data/agent_001_decisions.json`, last three records). The user got a description of a reply, and the evaluator called the goal met.
- [misleading] FAILED does not stop anything. `attempt_count` keeps rising on later calls that send no goal; a call that sends a goal resets it to 0 (`backend/agent.py:247-249, 254, 287-288`).
- [bug] A blocking `time.sleep(0.5)` runs inside the async request path (`backend/agent.py:198, 263`). Code after `return` is dead (`backend/agent.py:116-127`).
- [ok-for-demo] `_get_model` spends one live "test" call on the first request (`backend/agent.py:92`).

### Tests and data
- `scripts/test.sh` only greps for "running", "agent_id" and "action" (`scripts/test.sh:9, 13, 20`), then prints "All tests passed!" whatever happened (`scripts/test.sh:22-23`). It passes even when the action is an error message.
- `data/agent_001_decisions.json` has 26 records. 22 are error strings:
  - 9 × 404 "model not found" (`gemini-pro`, `gemini-1.5-flash`);
  - 5 × 403 saying the API key "was reported as leaked";
  - 5 × 400 "API key not valid";
  - 3 × 429 quota errors.

  Only 4 hold real model text. Do not use it as practice data.

### What to take for your project
- Skip the code. Take one idea only: write one log record per step (goal, action, result, evaluation). That is the seed of a D1 trace. In `ragkit`, write one JSONL record per pipeline stage: query, retrieved chunk ids with scores, prompt version, answer, latency and token usage.
- Take one warning too (M3, V4): never let the generator grade its own output and report that as progress. The decision log above is a ready-made example of why a judge must be validated against labels first.

### Try this
- (15 min) Read `LongTermStore.query` and `_build_context`. Write down three keys from `data/agent_001_memory.json` and predict what `query("Test")` returns. Then, in a scratch copy, change the search to look inside the stored values, and see which memories now match.

### Interview angle
- Q: "What makes something an agent rather than a prompt?" A: A loop that picks an action, really runs it, observes the result and stops on a checked condition. Here the action is simulated, so it is really one prompt plus self-grading.

---

## L11 · Chain-of-thought evaluator  (`lesson11/cot-reasoning-evaluator/`)

**What the code teaches, in one line:** It shows how to prompt for step-by-step reasoning, and how *not* to score it. The "quality score" is regex surface features that never check whether the answer is right.
**What it is not:** It is not an LLM-as-judge, has no reference answers, and does no correctness or faithfulness check.
**Relevance to your RAG study:** Medium, as a counter-example. Concepts: M3 (counter), V4 (counter), P7 (CoT prompt shape only; nothing is grounded). [LLMOps] (as a counter-example: an unvalidated evaluator over stored traces) [Interview]
**Stack:** FastAPI and `google-generativeai==0.4.1`. Model `models/gemini-flash-latest` (`backend/cot_agent.py:183`); the fallback chain below it never runs. Traces are kept in a JSON file. The UI shows the trace, the steps, a coloured "High/Medium/Low Quality" badge (≥ 0.7 / ≥ 0.5 / below) and averages.
**Swap to your stack:** easy. One generate call; the evaluator is pure Python.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/cot_agent.py` | Prompt builder, parser, scorer | 17-46, 48-84, 86-169 |
| 2 | `data/cot_memory.json` | 10 real Gemini traces with their scores | whole file |
| 3 | `backend/test_cot.py` | Unit tests on hand-written traces | 12-50 |
| 4 | `backend/main.py` | Endpoints, "high quality" filter | 45-94 |

### How it works, step by step
1. `POST /api/reason` → `reason_with_cot(query, style)` (`backend/main.py:45-55`).
2. The prompt says "think step by step", in a short 3-point form or a detailed 5-point form (`backend/cot_agent.py:21-46`). Gemini is called synchronously inside an async handler (`backend/cot_agent.py:216`).
3. Steps are found by a numbered-list regex, then bullets, then a split on full stops (pieces over 10 characters, capped at 10) (`backend/cot_agent.py:52-66`).
4. The conclusion runs from the last occurrence of the first marker in the list that appears anywhere ("therefore", "thus", …) to the end of the text. Without a marker it is the last sentence (`backend/cot_agent.py:69-84`).
5. Scoring:
   - clarity = for each step, the share of three checks it passes (a transition word found as a substring, a length of 21–199 characters, any digit or capitalised word), averaged over the steps (`backend/cot_agent.py:90-113`);
   - logic = overlap of numbers and capitalised words between neighbouring steps (`backend/cot_agent.py:116-135`);
   - overall = 0.3 clarity + 0.3 logic + 0.2 conclusion + 0.2 × min(steps/5, 1) (`backend/cot_agent.py:158-169`).
6. Traces scoring ≥ 0.7 are served as "high quality … for few-shot examples" (`backend/main.py:73-79`, `backend/cot_agent.py:245-250`).

### README vs code
- README says the agent "Extends SimpleAgent from L10" (`README.md:51`). `CoTAgent` is a standalone class (`backend/cot_agent.py:171`).
- README says stored traces "become few-shot examples for L12" (`README.md:55`). L12 never reads `cot_memory.json` (I checked with grep).
- README says "Multi-dimensional quality scoring" (`README.md:31`). Every dimension is a surface heuristic.
- `setup.sh` hard-codes a key in `genai.configure` and in docker-compose, and uses `gemini-pro` (`setup.sh:39, 1135, 202`). The generated folder's Python was edited later and reads the key from the environment, but the generated `docker-compose.yml:11` still holds a hard-coded key. Read the folder, not the script, for the code.

### Where it is thin or wrong
- [misleading] The stored data shows that the score does not track correctness:
  - the three cookie-problem answers are all correct (Alice 3, Bob 1, Charlie 1), yet all scored `conclusion_present 0.0` (the extracted "conclusion" was just `**`), with overall 0.49–0.57;
  - "What is 2+2?" scored 0.73 ("High Quality") in one of its three runs (the other two: 0.64 and 0.67);
  - the one-word query "test" scored 0.68 (`data/cot_memory.json`);
  - a correct train answer that the parser split into only 2 steps got `logic_flow` 1.0 and overall 0.73, which is "High Quality" (`data/cot_memory.json`). A broken parse raised the score.
- [misleading] Two of the three clarity checks pass for almost any step. The transition test is a substring test, so "so" matches inside "also", "solve" or "reasoning". Any capitalised word, such as the first word of a sentence, counts as a "specific" (`backend/cot_agent.py:92-95, 104, 108`). In practice clarity mostly measures step length.
- [bug] The numbered-step regex starts a new step at any "digit + full stop" (`backend/cot_agent.py:55`). Sub-numbered headings such as "**Step 2.1: Define Addition**" are cut at "2.", so stored steps include fragments such as "…**Step" followed by "1: Define Addition**" (`data/cot_memory.json`, first trace). Decimals would split the same way.
- [bug] `extract_conclusion` checks markers in a fixed list order and returns everything from that marker to the end (`backend/cot_agent.py:77-80`). So the "conclusion" can be a long tail, not the final statement: one stored train answer's conclusion starts at "Result:**" and still contains a later "Step 5" heading (`data/cot_memory.json`).
- [misleading] The model fallback chain is dead code. Building `GenerativeModel(...)` makes no API call, so the first `try` never fails (`backend/cot_agent.py:182-192`). I checked the constructor in SDK 0.8.6 on this machine; the lesson pins 0.4.1.

### Tests and data
- `backend/test_cot.py` has 5 real offline tests. They only use tidy hand-written traces (`backend/test_cot.py:14-16, 42-45`) and never use a wrong answer. `test.sh` also curls the live API (`test.sh:25-36`).
- `data/cot_memory.json` holds 10 real traces. It is useful as data for a "does the metric agree with correctness?" exercise.

### What to take for your project
- Take the lesson, not the code. For M3 and V4: any metric must first be checked against labelled correct and incorrect outputs. Build a final-answer check (exact or numeric match) before any style score.
- Re-implement nothing. If you want a reasoning judge later, use your planned judge (Cohere, run once at the end on stored traces) as a binary PASS/FAIL judge per failure mode. Validate it with TPR/TNR against your own labels before you report its numbers (your `llm-as-judge` and `judge-validation` skills).

### Try this
- (20 min) In a scratch notebook, re-type the scorer in your own words. Score two traces with identical structure (for example the shape of `backend/test_cot.py:14-16`): one ends "5 + 3 = 8", the other "5 + 3 = 9". Note that the scores are identical (true as long as the wrong number does not also appear in the step before). Then add a reference-answer check and see the two separate.

### Interview angle
- Q: "How would you evaluate reasoning or answer quality?" A: Surface features (step count, transition words) do not measure correctness. Use a reference answer where one exists, or a binary LLM judge per failure mode that you validate against human labels.

---

## L12 · Few-shot classification with "similar example" selection  (`lesson12/l12-few-shot-learning/`)

**What the code teaches, in one line:** It shows the shape of dynamic few-shot prompting: pick the k "nearest" labelled examples, put them in the prompt, classify. But the "embeddings" are hash noise and the benchmark accuracy is a formula.
**What it is not:** Not similarity-based retrieval in any real sense. No embedding model, no labels in the benchmark, no measured accuracy.
**Relevance to your RAG study:** Medium. Concepts: P4 (counter-example: hash "embeddings"), C4 (counter-example: kNN over noise), P7 (few-shot prompt shape), M4 (counter-example: formula accuracy). The *idea* (kNN over real embeddings) is sound; the code does not implement it. [LLMOps] (latency and prompt-size logging) [Interview]
**Stack:** FastAPI, `google-generativeai==0.8.3`. Gemini `gemini-2.0-flash-exp` for both the classifier and a "model" named `embedding_model` that is never used (`backend/main.py:25-26`). "Embeddings" are Python `hash()` values. The store is `backend/data/examples.json`. The UI shows classification, an examples manager, a benchmark chart and a metrics page.
**Swap to your stack:** easy. Replace `_generate_embedding` with Cohere `embed-v4.0` (or MiniLM) and the classifier call with Groq. That makes the similarity real; the benchmark still needs gold labels before its accuracy means anything.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/main.py` `ExampleStore` | Store, fake embedding, cosine | 61-152 |
| 2 | `backend/main.py` `FewShotEngine` | Prompt, classify, benchmark | 155-294 |
| 3 | `backend/main.py` startup seeding | 8 seed examples | 301-325 |
| 4 | `backend/data/examples.json` | Persisted examples and vectors | whole file |

### How it works, step by step
1. On import, `init_sample_examples` adds 8 customer-support examples. It does this on every start, and each add also makes a Gemini call (`backend/main.py:301-325, 95, 111`).
2. `POST /api/classify` → `classify` (`backend/main.py:328-331, 178`).
3. `find_similar_examples` "embeds" the query and ranks stored examples by cosine (`backend/main.py:118-132`). This "embedding" step spends one throwaway Gemini call, even when k is 0 (`backend/main.py:111, 123`).
4. The "embedding" works like this: call Gemini with "Generate a semantic representation", throw the reply away, then return up to 10 numbers, each the `hash()` of a 3-character slice taken every 10 characters, mod 1000, divided by 1000 (`backend/main.py:106-116`). Cosine trims both vectors to the shorter length (`backend/main.py:136-138`).
5. The prompt is: the task description, then "Example i: Input/Output" blocks, then the new input and "Output:" (`backend/main.py:160-176`).
6. `token_count` is the number of whitespace-separated words (`backend/main.py:197`). `confidence` is hard-coded: 0.85 with 3 or more examples, otherwise 0.70 (`backend/main.py:205`).
7. On an error whose text contains "429" or "quota", the code silently returns the top example's label, or a keyword rule, with confidence 0.75. Other errors give a 500 (`backend/main.py:207-239`).
8. The benchmark runs 0/1/3/5 shots over your queries, but it reports `accuracy = 0.85 + 0.02 × shots` (`backend/main.py:265, 288`). `BenchmarkRequest` has no labels at all (`backend/main.py:48-51`). Each classification makes two Gemini calls (the throwaway one, then the real one), so a benchmark makes 2 × 4 × (number of queries) calls (`backend/main.py:265-283`).

### README vs code
- README says "Cosine similarity with semantic embeddings" (`README.md:46`). The vectors are salted hashes of character slices (`backend/main.py:113`).
- README says "Performance benchmarking across shot counts" (`README.md:7`). The accuracy is simulated (`backend/main.py:288`), but the UI plots it as "Accuracy %" (`frontend/src/components/BenchmarkPanel.js:36, 111`).
- README says "Token counting" (`README.md:10`). It counts words (`backend/main.py:197`).

### Where it is thin or wrong
- [bug] Python salts `str` hashes per process, and no `PYTHONHASHSEED` is set in `start.sh` or the `Dockerfile`. So the same sentence gets a different vector after each restart. In `backend/data/examples.json`, each seed sentence appears 5 times with 5 different vectors, of 3–5 dimensions. Similarity therefore compares vectors from different runs: it is effectively random.
- [misleading] The similarity numbers look high for everything and mean nothing. All hash values lie in [0, 1), so every cosine is positive. I computed the cosines between the 42 stored vectors with the code's own rule (trim, then cosine), offline from the data file. Copies of the *same* sentence average 0.82; *different* sentences average 0.83, and some different pairs reach 1.00 (rounded) (`backend/data/examples.json`; `backend/main.py:113, 134-146`). The ranking is noise.
- [bug] Seeds are duplicated on every restart: 42 stored examples, which is the 8 seeds × 5 plus 2 user-added (`backend/main.py:325`). The top 3 can include repeated copies of one example.
- [misleading] Confidence and benchmark accuracy are constants or formulas (`backend/main.py:205, 237, 288`).
- [misleading] `latency_ms` includes the throwaway "embedding" call (`backend/main.py:180-183, 111, 241`). So the benchmark's latency per shot count measures two LLM calls, not the effect of a longer prompt.
- [shallow] The reply is returned raw (`backend/main.py:202`). Nothing maps it onto the label set, so once you add real labels, a reply such as "Output: REFUND_REQUEST" or a full sentence would score as a wrong class.
- [misleading] The mock fallback is not flagged in the response (`backend/main.py:207-237, 254-260`).
- [security] A real-looking API key is the default value in code (`backend/main.py:23`). It is also exported in `start.sh:12, 17` and baked into `Dockerfile:15` and `docker-compose.yml:9`.

### Tests and data
- `test.sh` greps for "healthy", "classification" and "customer_support" (`test.sh:9, 20, 24`). There is no correctness check.
- `backend/data/examples.json` holds 42 rows: 10 distinct inputs over 8 labels (the 8 seeds × 5, plus 2 user-added rows labelled REFUND_REQUEST and POSITIVE_FEEDBACK). It is too small and too duplicated for practice, apart from an 8-row toy set.

### What to take for your project
- Re-implement the idea properly (C4, P4): dynamic few-shot selection is dense retrieval over example inputs. In plain NumPy:
  - embed each stored input once with Cohere `embed-v4.0` (`input_type` "search_document"), and the new input as "search_query"; MiniLM is the local fallback;
  - L2-normalise the vectors and rank with one dot product;
  - dedup identical inputs before you take the top k;
  - cache every vector on disk, keyed by model id plus a hash of the text, so reruns replay without credits.

  It is the same code you will write for chunk retrieval.
- Take the benchmark *design* (0/1/3/5 shots, latency and prompt-size per setting), then fix what is missing (M1, M4): gold labels, a parser that maps each reply onto the label set, and accuracy reported with the number of items. Time the classification call on its own.

### Try this
- (25 min) Re-type the hash-vector line in a scratch script. Run it for one sentence under `PYTHONHASHSEED=1` and `=2`, and compare the cosine between the two runs. Then embed the 8 seed inputs with MiniLM, and check whether "I want my money back" now picks the REFUND example first. A shortcut for the first half: load `backend/data/examples.json` and compare the cosines between the 5 stored copies of one sentence with the cosines between different sentences. You should find no gap.

### Interview angle
- Q: "How do you pick few-shot examples at run time?" A: Embed the example inputs, retrieve the nearest k to the query, then dedup and balance labels. Check that it helps by measuring accuracy on a labelled set at each k against zero-shot.

---

## L13 · Context engineering: token counting, compression, budget  (`lesson13/vaia-l13-context-engineering/`)

**What the code teaches, in one line:** Count tokens with a real tokenizer, then choose pass-through, extractive or "hybrid" compression from the share of the budget used. The compression ignores the query, and the budget is never checked against the output.
**What it is not:** Not query-aware contextual compression (X2 in the RAG sense) and not context assembly (no chunks, no dedup, no ordering). The output is not checked against `max_tokens`.
**Relevance to your RAG study:** High. Concepts: X3 (token budgeting only: no chunks, dedup or ordering), X2 (counter-example: query-agnostic compression), P3 (TF-IDF used for sentence salience, with no query), D2 (counter-example: a constant price stands in for cost). [LLMOps] [Interview]
**Stack:** FastAPI, `tiktoken==0.5.2`, `nltk==3.8.1`, scikit-learn TF-IDF, `google-generativeai==0.3.2`. Gemini `gemini-pro` for abstractive summaries (`backend/services/summarizer.py:23`). No embeddings and no vector store. The UI shows a token counter with a usage bar, a summarizer, an optimizer and "cost savings" tiles.
**Swap to your stack:** easy. The tokenizer is local. Swap the one Gemini call for Groq. For exact counts use the `usage` field Groq returns. gpt-oss uses OpenAI's o200k-family tokenizer (`o200k_harmony`), not cl100k. (That last fact comes from OpenAI's gpt-oss release, not from this repo; check that your tiktoken version has it.)

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/utils/token_counter.py` | tiktoken counts, budget bands | 10-20, 22-32, 50-74 |
| 2 | `backend/services/context_optimizer.py` | Strategy choice, truncation, savings | 26-120, 122-151 |
| 3 | `backend/services/summarizer.py` | Extractive TF-IDF, abstractive, hybrid | 30-85, 87-129, 131-155, 157-195 |
| 4 | `backend/api/routes/context_routes.py` | 3 POST endpoints | 29-90 |
| 5 | `backend/tests/test_token_counter.py` | 3 small tests | 4-27 |

### How it works, step by step
1. `POST /api/v1/optimize-context` → `context_optimizer.optimize(text, max_tokens)`. The default budget is 30 000 tokens, from `MAX_CONTEXT_TOKENS` (`backend/api/routes/context_routes.py:74-82`, `backend/services/context_optimizer.py:13, 26`).
2. Counting: `tiktoken.encoding_for_model("gpt-4")`, i.e. cl100k_base (`backend/utils/token_counter.py:10-14`; I confirmed the mapping offline with tiktoken). So the count is a real tokenizer count, for GPT-4's tokenizer rather than Gemini's. If encoding fails, it falls back to characters ÷ 4 (`backend/utils/token_counter.py:32`).
3. Budget bands: under 70 % is "optimal" (pass through unchanged); 70–90 % is "moderate" (extractive, keep ratio 0.7); 90 % and over is "critical" (hybrid, ratio 0.5) (`backend/utils/token_counter.py:56-64`, `backend/services/context_optimizer.py:32-51`).
4. Extractive:
   - split into sentences with NLTK (`backend/services/summarizer.py:42`); with 2 sentences or fewer, the text comes back unchanged (`backend/services/summarizer.py:44-45`);
   - fit TF-IDF on *those sentences only* (English stop words, `max_features=100`) and score each sentence by the sum of its TF-IDF weights;
   - multiply the first sentence's score by 1.5 and the last one's by 1.3;
   - keep the top max(2, n × ratio) sentences in their original order (`backend/services/summarizer.py:51-55, 73-85`).

   The ratio is a share of *sentences*, not tokens.
5. Abstractive: asks Gemini for "about N characters", with temperature 0.3, `max_output_tokens` 2048 and a 10 s timeout. Any error falls back to extractive (`backend/services/summarizer.py:99-129`). Hybrid = extractive at 1.5 × ratio; then, only if that cut the text below 80 % of its characters, abstractive at 0.8 (`backend/services/summarizer.py:141-151`).
6. Check: if the result still has ≥ 90 % of the original tokens, it truncates instead, at max_tokens × 4 characters, cutting at the last full stop if that falls in the final 20 % (`backend/services/context_optimizer.py:65-83, 122-137`).
7. "Savings" assume $0.01 per 1K tokens and project ×1 000 000 requests a month (`backend/services/context_optimizer.py:139-151`).

### README vs code
- README says "Precise token analysis" (`README.md:44`). The counts are precise for cl100k only. The comment calling cl100k "Gemini compatible" is wrong, and it sits in a fallback branch that "gpt-4" never reaches (`backend/utils/token_counter.py:16-20`).
- README says "Real-time cost analysis" (`README.md:11`). The price is a made-up constant (`backend/services/context_optimizer.py:142`).
- README says "Enabling L14: context optimization layer for state" (`README.md:66-68`). L14 never imports any of this; its `context_summary` field is never filled (I checked with grep).

### Where it is thin or wrong
- [bug] The budget is never checked against the output. In the "critical" path, the compressed text is returned whenever it is under 90 % of the original, even if it is still above `max_tokens` (`backend/services/context_optimizer.py:61-99`). Example on the extractive path (Gemini fails or times out): 60 000 tokens against a 30 000 budget → about 60–75 % of the sentences kept → still well over the budget (`backend/services/summarizer.py:124-129, 141-151`). If Gemini does answer, the size is bounded by its 2048-token output cap (`backend/services/summarizer.py:114`), not by the budget.
- [bug] Truncation uses a 4-characters-per-token guess and never re-checks the result against the budget (`backend/services/context_optimizer.py:124-125`).
- [misleading] UNVERIFIED at runtime: `gemini-pro` is very likely retired (L10's own logs record a 404 for it). If so, "abstractive" and "hybrid" silently become extractive but are still labelled with their own names (`backend/services/summarizer.py:23, 127-129, 192`).
- [misleading] `quality_preserved` just echoes the request flag (`backend/services/context_optimizer.py:93`). `compression_ratio` is original ÷ compressed, in characters: the inverse of `target_ratio` (`backend/services/summarizer.py:183-184`). The two truncation branches compute the same field in *tokens* (`backend/services/context_optimizer.py:75, 111`), so one field carries two units.
- [misleading] Silent fallback that keeps its label. If NLTK's `punkt` data is missing, `sent_tokenize` raises (NLTK library behaviour; not run here). The start-up download only logs a warning when it fails, for example offline (`backend/main.py:18-23`). Extractive "summarisation" then returns the first half of the characters, and the response still says "extractive" (`backend/services/summarizer.py:62-64`).
- [shallow] The "moderate" band compresses text that already fits: at 70–90 % of the budget it still drops about 30 % of the sentences (`backend/utils/token_counter.py:59-61`, `backend/services/context_optimizer.py:46-48`). Nothing reserves room for the question or the answer, so the bands are a rough stand-in for a real reserve.
- [shallow] The compression is query-agnostic: the question is never an input. TF-IDF sums favour long sentences.
- [bug, UI] The summarizer tab reports *characters* saved as "tokens saved" (`frontend/src/components/Summarizer.js:36-38`). "Average compression" is just the last value (`frontend/src/App.js:21`).
- [ok-for-demo] Settings that exist but do nothing: `compression_timeout` (`backend/services/context_optimizer.py:14`) and `count_messages` (`backend/utils/token_counter.py:34-48`) are never used.

### Tests and data
- `backend/tests/test_token_counter.py` checks that "Hello, world!" is 1–9 tokens, that the analysis has its keys, and that empty text gives 0. The summarizer and optimizer have no tests.
- In `demo_test.sh:44-67`, the "optimize" inputs are far under budget: 41 cl100k tokens against a budget of 100, and 18 against 50 (I counted them offline with tiktoken). Both are under the 70 % band, so they pass through and compression is never exercised. There is no data folder.

### What to take for your project
- X3: count with the real tokenizer of the model you call. Reserve room for the system prompt, question and answer. With `openai/gpt-oss-20b` the answer reserve must also cover its reasoning tokens, even at `reasoning_effort="low"`, so give `max_tokens` headroom and count it in the budget. Fill the rest with ranked chunks and drop whole chunks, lowest rank first. **Re-count the final prompt** and assert it fits.
- X2: re-implement extractive compression *conditioned on the query*: score sentences by similarity to the question (BM25 or embeddings), not by a TF-IDF fit on the context itself. Compare against this query-agnostic baseline on your eval set, and keep retrieval quality and answer quality as separate numbers.
- D2: log `usage` from each Groq response (store it with the cached call) instead of estimating cost with a constant.

### Try this
- (30 min) Take 5 chunks from your project PDFs (for example the climate-change PDF; never the book). Everything here runs locally. Count each one four ways: cl100k, o200k, characters ÷ 4 and words. Then run a re-typed version of the extractive scorer on the 5 chunks joined together, with a question about one chunk (the scorer never sees the question; that is the point). Count how many kept sentences come from the relevant chunk. That count is your X2 baseline.

### Interview angle
- Q: "Your retrieved context does not fit the window. What do you do?" A: Budget with the model's own tokenizer, rank and dedup the chunks, and drop the lowest whole chunks or compress them relative to the query. Then verify the final prompt count, instead of cutting characters blindly.

---

## L14 · State management (Postgres + Redis)  (`lesson14/l14-state-management/`)

**What the code teaches, in one line:** It shows a cache-aside pattern for conversation state: Redis first with a 1-hour TTL, Postgres as the durable store, a version counter and snapshots every 5 versions.
**What it is not:** It has no real optimistic locking, no working rollback (likely), no summarisation of history, and no tests.
**Relevance to your RAG study:** Low. Concepts: D2 (cache-aside, TTL). No retrieval of any kind.
**Stack:** FastAPI, asyncpg, `redis.asyncio`, DeepDiff, Pydantic, `google-generativeai==0.8.3`. Gemini `gemini-1.5-flash` (`backend/services/agent_engine.py:23`). No embeddings. The UI shows a chat, a state inspector and metrics.
**Swap to your stack:** moderate. The LLM swap is trivial; the work is running Postgres and Redis.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/models/agent_state.py` | State schema | 26-66 |
| 2 | `backend/services/state_manager.py` | Load, save, snapshot, diff, rollback | 58-95, 97-137, 160-217 |
| 3 | `backend/services/agent_engine.py` | One chat turn | 28-94, 96-138 |

### How it works, step by step
1. `POST /api/chat` → `process_message` (`backend/app/main.py:79-89`).
2. `load_state` tries Redis key `state:<id>` first, then Postgres. Any error is swallowed and returns None (`backend/services/state_manager.py:58-95`).
3. The prompt holds the last 5 turns (user and agent) plus the new message. "Tokens" = prompt words + reply words (`backend/services/agent_engine.py:48, 86-94, 108`).
4. `save_state`: version + 1, upsert into Postgres in a transaction, a snapshot whenever the version is divisible by 5, and a fire-and-forget Redis `setex` with 3600 s (`backend/services/state_manager.py:104-128, 144`).

### README vs code
- README says "State diff and rollback" (`README.md:33`). Both read snapshot rows only (`backend/services/state_manager.py:165-170, 197-200`), and neither is exercised by `demo.sh` or any test.
- README says "Production error handling" (`README.md:34`). Load errors become "no state" (`backend/services/state_manager.py:93-95`), and failed saves are ignored by the caller (`backend/services/agent_engine.py:65`).

### Where it is thin or wrong
- [misleading] The docstring says "optimistic locking via version increment", but the upsert never checks the expected version, so the last write wins (`backend/services/state_manager.py:100, 113-121`).
- [bug, likely; UNVERIFIED at runtime] asyncpg returns JSONB as a string by default (its documented behaviour), and no codec is registered (`backend/app/main.py:31`). Then `AgentState(**row['state_data'])` would fail on every Postgres read (`backend/services/state_manager.py:86, 206`). Consequences: after the Redis TTL expires, a session silently restarts empty and overwrites its history, and rollback always fails. `demo.sh` reads state within seconds, so this path is never hit.
- [bug] Even when rollback works, the version is reset to the target (`backend/services/state_manager.py:207`). Later saves then reach old snapshot ids again (`<id>_v10`), hit the primary key and roll back the whole save. `save_state` returns False, and `process_message` ignores it (`backend/services/state_manager.py:133-137`, `backend/services/agent_engine.py:65`).
- [misleading] Rollback reports success even when its own save fails: `rollback_state` ignores what `save_state` returns and always returns True (`backend/services/state_manager.py:210-213`). The endpoint then reports the target version, but the stored version is target + 1, because `save_state` adds 1 (`backend/app/main.py:120`; `backend/services/state_manager.py:104, 207`).
- [misleading] Model errors become saved conversation turns. A quota error, or any error other than a key error, comes back as an apology text with 0 tokens. It is appended to the history as the agent's reply, saved, and fed back as context on later turns (`backend/services/agent_engine.py:59-65, 127-138`). UNVERIFIED at runtime: L10's log records a 404 for `gemini-1.5-flash`, the model this lesson uses, so in practice every reply may be such an error string.
- [shallow] `tiktoken` is installed (`backend/requirements.txt:18`) but never imported; "tokens" are word counts.
- [ok-for-demo] When the error text contains `API_KEY` (for example `API_KEY_INVALID`) or "expired", about 300 lines of canned answers about Redis and Postgres are returned, marked "Demo mode" (`backend/services/agent_engine.py:118-126, 140-445`). The first test on line 119 can never match: it looks for "API key" with capitals inside a lower-cased string.

### Tests and data
- `backend/tests/test_state_manager.py:17-32` holds three tests whose body is `pass`. `test.sh:25` still prints "All tests passed!".

### What to take for your project
- Context only. The useful shape is your record/replay cache (D2): key = hash of (provider, model id, prompt version, input); read the cache, else call and write the cache. Test the cache-miss path on purpose, and make replay mode fail loudly on a miss instead of quietly calling the API.
- Take the warning about silent success: any save, rollback or cache write must return a result the caller checks.

### Try this
- (15 min) On paper, take a session at v12, roll back to v5, then send 5 messages. Write down each version and snapshot id, and find the collision.

### Interview angle
- Q: "What can go wrong with a Redis-in-front-of-Postgres cache?" A: Stale or lost updates without a compare-and-set version check, an untested miss path, and serialisation mismatches. Test expiry and concurrent writes deliberately.

---

## L15 · Conversational agent with memory and goals  (`lesson15/conversational-agent/`)

**What the code teaches, in one line:** Persist a whole conversation in SQLite and paste the *entire* history into every prompt. Add `/goal` tracking judged by a YES/NO LLM call per goal per turn.
**What it is not:** No conversational query rewriting, no history window or summary, no token budget, and no retrieval.
**Relevance to your RAG study:** Medium. Concepts: Q1 (counter-example: the rewrite step is missing), X3 (counter-example: unbounded history), M3 (binary goal judge; right shape, never validated). [Interview]
**Stack:** FastAPI, aiosqlite, `google-generativeai==0.8.3`. Gemini `gemini-2.0-flash-exp` for the chat and for goal judging (`backend/gemini_client.py:14`, `backend/goal_tracker.py:7`). There is also a CLI (`backend/cli.py`). The UI shows goals, history and token counts.
**Swap to your stack:** easy. Two prompt calls; replace both with Groq.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/conversation_engine.py` | One turn end-to-end | 23-61 |
| 2 | `backend/gemini_client.py` `generate_response` | Prompt, retries, token estimate | 325-364 |
| 3 | `backend/goal_tracker.py` | YES/NO goal judge | 9-39 |
| 4 | `backend/memory_manager.py` | SQLite persistence | 15-50 |
| 5 | `backend/models.py` | State machine | 6-10, 99-120 |

### How it works, step by step
1. `POST /messages` → `process_message`: load the state JSON from SQLite and append the user message (`backend/api.py:46-52`, `backend/conversation_engine.py:24-29`).
2. If the message starts with `/goal `, the goal is added, the state becomes GOAL_SEEKING, and there is no LLM call (`backend/conversation_engine.py:32-36`, `backend/models.py:107-111`).
3. Otherwise, the system context lists the active goals (`backend/conversation_engine.py:39-43`). The prompt = system context + *all* previous messages as "role: content" + the current message (`backend/gemini_client.py:331-337`).
4. Up to 3 tries, with blocking backoff sleeps of 1 s and 2 s (`backend/gemini_client.py:339-364`). Tokens = max(words × 1.3, characters ÷ 4) of the *reply only* (`backend/gemini_client.py:343-346`).
5. For each open goal, a second LLM call reads the last 10 messages and answers YES or NO. Errors count as NO (`backend/goal_tracker.py:9-33`).
6. The whole state is saved with INSERT OR REPLACE (`backend/memory_manager.py:32-41`).

### README vs code
- README says "Persistent conversation state" (`README.md:6`). True, but "memory" means the full raw transcript every turn; nothing is selected or summarised.
- The system prompt tells the model "You remember previous conversations" (`backend/conversation_engine.py:40-41`). Only the current conversation's messages are sent (`backend/gemini_client.py:331`); the user's other conversations are never read.
- STATUS.md says "Everything is working!" in "intelligent fallback mode", i.e. with no LLM at all (`../STATUS.md:77`). In that mode the demo shows even less than it seems. `scripts/demo_test.py:21-27` sends five messages. Messages 3 and 4 contain "machine", which contains "hi", so they get the same canned greeting as message 1 (`backend/gemini_client.py:37`). Only the thank-you message gets its own canned reply. The fallback's "machine learning" answer can never be reached by a message that spells out "machine learning".

### Where it is thin or wrong
- [misleading] After any failure, a canned library answers (`backend/gemini_client.py:21-323`). Only the first reply carries a note, and only when the key is marked invalid (`backend/gemini_client.py:25-28, 318-320`), so later canned replies look real.
- [bug] The fallback keyword checks use substrings:
  - "hi" matches "this", "which" or "machine", so "Can you explain this?" gets the greeting (`backend/gemini_client.py:37`);
  - "ai" matches words such as "available" or "again", so "What is available?" gets the AI overview (`backend/gemini_client.py:215`). ("explain" also contains "ai", but it is caught earlier by the "detailed" check, `backend/gemini_client.py:31-34, 49`.)
- [bug] The first request with an invalid key still runs the retries and sleeps (about 3 s) before falling back (`backend/gemini_client.py:350-358`). After that `api_key_valid` is False, and later requests go straight to the fallback (`backend/gemini_client.py:327-329`). Blocking `time.sleep` and a sync SDK call run inside async code (`backend/gemini_client.py:341, 355, 361`).
- [shallow] History is unbounded, so the prompt grows each turn and cost grows with it. `total_tokens` ignores prompt tokens.
- [shallow] The goal judge's criteria default to "User satisfaction" because `/goal` never sets any (`backend/goal_tracker.py:14`). The judge is never validated.
- [bug] The judge's verdict parse is fragile. It lower-cases the reply and checks `startswith('yes')` (`backend/goal_tracker.py:19`), so a reply such as "**YES**" (Markdown bold) counts as NO. The judge is also a sync SDK call inside async code (`backend/goal_tracker.py:18`), and it costs one extra LLM call per open goal per turn (`backend/goal_tracker.py:28-32`).

### Tests and data
- `tests/test_models.py:6-21` covers serialisation and counters. `scripts/test.sh:19-44` runs the engine end-to-end and asserts 4 stored messages. It passes with no API key, through the fallback.
- No data files.

### What to take for your project
- Q1: add the missing step. Before retrieval, ask Groq to rewrite the follow-up into a standalone question using the last few turns. Log the original and rewritten queries, and evaluate retrieval on the rewritten one. Cache each rewrite call (record/replay).
- X3: keep a bounded window (last N turns, or a running summary) instead of the full transcript, and count it in your token budget.
- M3: the per-goal YES/NO judge is the right *shape* for a binary judge. Ask for a structured verdict (for example JSON with a PASS/FAIL field) instead of parsing free text, and validate it against labels (TPR/TNR) before trusting it.

### Try this
- (25 min) Write 5 two-turn exchanges about your project PDFs, e.g. "What is BM25?" then "How is it different from TF-IDF?". Your own questions are fine to send to Groq; book text is not. Write the standalone rewrite you want for each, then prompt Groq to produce rewrites (cache the calls) and score them by hand. Then retrieve with the raw and the rewritten follow-up, and compare the top-3 chunks.

### Interview angle
- Q: "How do you handle follow-up questions in conversational RAG?" A: Rewrite the follow-up into a standalone query from recent history before retrieval. Give the generator a bounded history (a window or summary) so cost and distraction do not grow every turn.

---

## L16 · Tool use and function calling (one weather tool)  (`lesson16/`, `setup.sh` only, no generated folder)

**What the code teaches, in one line:** A minimal function-calling round trip. Declare a JSON-schema tool, let Gemini request it, run it, then make a second call with the result pasted in as text.
**What it is not:** No loop, no parallel calls, no structured tool-result message, no argument validation.
**Relevance to your RAG study:** Medium. Concepts: A1 (the model chooses a tool), A5 (foundation). [Interview]
**Stack:** FastAPI, `google-generativeai==0.8.3`, `requests`. Gemini `gemini-2.0-flash-exp` with `tools=` (`setup.sh:247-250`). The weather comes from OpenWeatherMap, or demo data when the key is "demo", which is the default in the generated `.env` (`setup.sh:32, 86-105`). The UI shows a chat and a "recent tool calls" panel.
**Swap to your stack:** moderate. Groq uses OpenAI-style `tools` / `tool_calls` and `role: "tool"` messages, so the parsing changes, but the schema dict is almost the same.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `setup.sh` heredoc `backend/main.py` | Tool, schema, registry | 80-160 |
| 2 | same | `execute_tool` | 166-190 |
| 3 | same | `chat_with_tools` round trip | 233-314 |
| 4 | same | `test.sh` | 1278-1306 |

### How it works, step by step
1. `POST /chat` creates a conversation id if none is given and calls `chat_with_tools` synchronously from an async handler (`setup.sh:329-340`).
2. The prompt is the last 5 turns as "User:/Assistant:" text plus the new message (`setup.sh:256-265`).
3. The first Gemini call goes out with the tool declarations: the hand-written schema for `get_weather(city)` with `required: ["city"]` (`setup.sh:145-160, 270`).
4. The code loops over the reply parts. At the *first* function call it runs `execute_tool`, which catches unknown names and `TypeError` for bad arguments (`setup.sh:166-190, 275-286`).
5. A second call sends the original prompt plus "Tool result: …" as plain text, and the code returns at once (`setup.sh:297-307`). With no function call, the code returns the text (`setup.sh:310`).

### README vs code
- README says "Multi-turn conversation loops" (`setup.sh:1322`). There are at most two model calls per request, and no loop.
- README says "Weather function with real API integration" (`setup.sh:1321`). The generated `.env` sets the demo key, so the answers are canned: 4 cities, and every other city gets 20 °C "Clear" (`setup.sh:32, 91-97`).

### Where it is thin or wrong
- [bug] Only the first tool call runs, because of the `return` inside the parts loop (`setup.sh:307`). The test "Compare weather in London and Paris" (`setup.sh:1300-1303`) can therefore get real tool data for one city at most.
- [bug] The second call still has tools attached. If the model asks for another tool, `final_response.text` raises and the request returns 500 (`setup.sh:301-306, 312-314`). (In SDK 0.8.6, `.text` raises `ValueError` on a function-call part; the lesson pins 0.8.3.)
- [shallow] The tool result is sent back as prose, not as a function-response part, so there is no structured link between the result and its call (`setup.sh:297-304`). Tool calls are not put into the prompt history (`setup.sh:257-259`).
- [bug] The demo city lookup is case-sensitive ("tokyo" → default values) (`setup.sh:97`). The conversation store is in-memory only (`setup.sh:211`).
- [security] With a real OpenWeatherMap key, the key goes into the query string of a plain `http://` URL (`setup.sh:108-115`), so it travels unencrypted.

### Tests and data
- `test.sh` sends 4 requests to 3 endpoints (`/health`, `/tools`, and `/chat` twice) and prints the output. It asserts nothing (`setup.sh:1278-1306`). No data files.

### What to take for your project
- Read it as the smallest possible example, then build the correct version in plain Python with Groq (A5 foundation):
  - send `tools`;
  - for *each* `tool_call`, run it and append a `role: "tool"` message carrying the call id;
  - loop until there are no calls or a turn cap is reached;
  - cache each Groq call and each tool result (record/replay), so the loop reruns without credits.
- Do it in plain Python first. Try LangGraph's tool node only after your own loop works, so you know what it hides.

### Try this
- (30 min) Rewrite `chat_with_tools` for Groq with a proper loop and parallel calls (cache the calls). Test "Compare weather in London and Paris" and check that two tool calls appear in your log.

### Interview angle
- Q: "Walk me through one function-calling round trip." A: The model returns a tool name and JSON arguments, you validate and run them, and you send the result back as a tool message linked to that call. You repeat until the model answers in text, with a turn cap.

---

## L17 · Tool schemas with Pydantic validation  (`lesson17/l17-tool-schemas/`)

**What the code teaches, in one line:** Define tool inputs and outputs as Pydantic models, generate the function declarations from them, and validate every model-produced argument on the server. Validation errors go back to the model so it can correct itself.
**What it is not:** The tools are fake (random weather, ignored time zone, placeholder search). The schema converter drops most constraints, so the model never sees them.
**Relevance to your RAG study:** Medium. Concepts: A1, A5, D4 (input validation). [LLMOps] (per-tool counters; but the success-rate metric ignores the model's own calls, see below) [Interview]
**Stack:** FastAPI, Pydantic v2, `google-generativeai==0.8.3`. The model list tries `gemini-2.5-flash` first; in practice that is always the one used (`backend/main.py:167-191`). No embeddings. The UI has a tools list, a query box, a validation tester and a metrics dashboard.
**Swap to your stack:** easy to moderate. `model_json_schema()` maps almost directly onto OpenAI-style `tools[].function.parameters`, which is simpler than Gemini's format. The loop changes to Groq's `tool_calls`.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/schemas.py` | Input and output models, validators | 9-35, 46-66, 75-97, 107-123 |
| 2 | `backend/tool_registry.py` | Pydantic → declaration; validate → run → validate | 38-86, 107-145 |
| 3 | `backend/main.py` `/query` | Multi-call tool loop | 140-292 |
| 4 | `backend/main.py` `/validate` | Validate without running | 107-138 |
| 5 | `backend/tools.py` | Tool bodies (simulated) | 13-71 |
| 6 | `tests/test_schemas.py` | 6 offline Pydantic tests | 11-42 |

### How it works, step by step
1. At startup, each entry in `TOOL_SCHEMAS` is registered, and its Gemini declaration is built from `model_json_schema()` (`backend/main.py:52-60`, `backend/tool_registry.py:20-36`).
2. The converter keeps each top-level property's type, description and enum, plus the `required` list. Unknown types become "string", and defaults are dropped (`backend/tool_registry.py:48-86, 88-98`).
3. `POST /query` starts a chat with tools and sends the question (`backend/main.py:162-197`).
4. The loop runs up to 10 iterations. It collects *all* function calls in a reply, using the correct `hasattr(...) and part.function_call` check, plus any text (`backend/main.py:202-219`).
5. For each call, the code first tries `MessageToDict` on the arguments. On SDK 0.8.6 (checked in a scratch script; the lesson pins 0.8.3) that raises on the SDK's map type, so the `dict(fc.args)` fallback is what runs, and numbers arrive as floats such as 5.0 (`backend/main.py:233-242`). Then `validate_and_execute`: Pydantic input validation, the function call, then output validation. A failure gives a dict with the error and `parameters_received` (`backend/main.py:245-248`, `backend/tool_registry.py:123-145`).
6. Each result, or the error dict, goes back as a `FunctionResponse` part, and all of them are sent together (`backend/main.py:257-279`). The loop stops when a reply has no calls (`backend/main.py:282-284`). If the cap of 10 is hit first, the loop just ends, and the request still returns the latest text and counts as a success (`backend/main.py:205, 286-292`).
7. Counters for queries, tool calls and validations are kept in memory and served at `/metrics` (`backend/main.py:32-42, 88-105`).

### README vs code
- README says the tests cover "Type coercion" (`README.md:60`). No such test exists, and nothing tests the converter or the loop.
- The quota-error message promises "The system will automatically retry with alternative models" (`backend/main.py:310`). It does not. The model list only guards the constructor, and the constructor never fails (`backend/main.py:177-188`).
- `setup.sh:495-496` uses `gemini-2.0-flash-exp` and an older converter (`setup.sh:205-239`). The generated folder was patched later.

### Where it is thin or wrong
- [misleading] `get_weather` returns random temperature, condition and humidity on every call (`backend/tools.py:19-29`). An eval would see different "facts" each run.
- [bug] `get_time` ignores the time zone: it returns the server's local time with `utc_offset` fixed at "+00:00" (`backend/tools.py:38-49`).
- [misleading] `search` returns "Result i for '<query>'" with example.com URLs (`backend/tools.py:58-64`).
- [shallow] `min_length`, `max_length`, `ge`/`le` and the character whitelists never reach the model (`backend/tool_registry.py:52-68`). So the model learns the limits only by failing.
- [shallow] `Optional` or nested fields would be flattened to "string" (`backend/tool_registry.py:53`).
- [bug] Sync `send_message` calls run inside an async handler (`backend/main.py:197, 277`).
- [misleading] The dashboard's "Validation Success Rate" counts only manual `/validate` calls (`backend/main.py:100-102, 113-138`; `frontend/src/components/MetricsDashboard.js:63-66`). The arguments the model produces in `/query` go through `validate_and_execute`, which updates no counter (`backend/tool_registry.py:107-145`). So the one metric about argument quality never sees the model.
- [misleading] Hitting the 10-iteration cap is reported as a successful query (`backend/main.py:205, 286-292`), and so is a query whose every tool call failed validation.
- [shallow] The location whitelist is ASCII-only (`backend/schemas.py:31-33`), so real names such as "São Paulo" or "Zürich" are rejected. A validator can be wrong too: test it on valid edge cases, not only on attacks.
- [shallow] Input-validation errors, tool crashes and output-validation errors all come back in one shape (`backend/tool_registry.py:123-145`). Your logs could not tell an argument-generation failure from an execution failure.

### Tests and data
- `tests/test_schemas.py` holds 6 real offline tests:
  - valid weather, time and search inputs pass (3 tests);
  - unit "kelvin" is rejected;
  - a `<script>` location is rejected;
  - `max_results=25` is rejected.

  They are good small examples of code-based checks. No data files.

### What to take for your project
- Reuse the pattern directly (A5, D4). Each future `ragkit` tool, such as `retrieve(query, k, filters)`, gets a Pydantic input model. Generate the tool schema from it, validate the model's arguments, and return validation errors to the model.
- Fix the converter gap: pass the full JSON Schema, with its constraints, in the tool definition (OpenAI-style tools accept it).
- Make tool bodies deterministic, or cache them, so runs can be replayed (your record/replay rule).
- Count validation results inside the loop itself, per tool, split into input-invalid, execution-error and output-invalid. Then you can see which stage fails (your `tool-use-evaluation` skill's four stages).

### Try this
- (20 min) Print `SearchToolInput.model_json_schema()` next to the declaration `_pydantic_to_gemini` builds from it. List every constraint that was dropped. Then write one extra test where the arguments arrive as `{"query": "x", "max_results": 5.0}` (a float, which is what this lesson's own argument conversion delivers), and check what Pydantic does.

### Interview angle
- Q: "Why validate tool arguments if the model already has the schema?" A: The schema in the prompt is a hint, not enforcement: models emit wrong types, out-of-range values and even injected strings. Even a provider's strict schema mode covers types and shape, not every constraint or your business rules. Validate on the server and return a structured error, so the model can correct itself and nothing unsafe runs.

---

## L18 · Tool execution loop  (`lesson18/l18-tool-execution-loop/`)

**What the code teaches, in one line:** It shows a fuller agent loop: model → tool calls → function responses appended to history → repeat, up to `max_turns`. It adds per-tool timeouts, stats over a WebSocket and a no-LLM fallback planner. The loop's tool-call check is broken.
**What it is not:** Not RAG. `document_search` returns the same three hard-coded documents with fixed "relevance" for any query. There is also no argument validation (L17's Pydantic layer is not used).
**Relevance to your RAG study:** Medium. Concepts: A5, A1, D1 (execution log), D2 (timeouts, latency), C4 (counter-example: `document_search` returns fixed "vector_similarity" results). [LLMOps] [Interview]
**Stack:** FastAPI with WebSocket, `google-generativeai==0.8.3`. The model is `GEMINI_MODEL`, default `gemini-2.0-flash` (`backend/main.py:33-37`). No embeddings or vector store, despite the "RAG" tool. The UI (Vite/React) shows example queries, the execution log and live stats.
**Swap to your stack:** moderate. The registry and timeout code is provider-free. The loop needs Groq's `tool_calls` / `role: "tool"` format.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/main.py` `FunctionRegistry` | Register, run with timeout, stats | 136-250 |
| 2 | `backend/main.py` `execute_loop` | The loop | 577-826 |
| 3 | `backend/main.py` tool bodies | Simulated tools | 69-130 |
| 4 | `backend/main.py` fallback planner | Regex "planner" without an LLM | 435-540 |
| 5 | `scripts/test_tools_direct.py` | Direct tool runs, no LLM (but importing `main` still makes the start-up test call if a key is set) | 33-61 |

### How it works, step by step
1. Startup makes a live "test" generate call to classify the key as valid, quota-exceeded, quota-zero, invalid or model-not-found (`backend/main.py:329-427`). If the LLM is unavailable and `ALLOW_FALLBACK_PLANNER` is on (the default), the regex planner runs instead (`backend/main.py:325-327, 579-582`).
2. `POST /chat` → `execute_loop(query, max_turns)`, with `max_turns` 10 by default. The history starts with the user query (`backend/main.py:837, 848-852, 666-673`).
3. Each turn calls the model with the full history and the tool declarations, rebuilt every turn from the registry (`backend/main.py:681-684, 542-563`).
4. The code decides whether there are function calls with a bare `hasattr` (`backend/main.py:702`). Each call is logged and run through `registry.execute` with a 30 s timeout in a thread pool. The result is wrapped as a `FunctionResponse` with the response `{"result": …}` (`backend/main.py:723-749, 164-210`).
5. The model's parts and the function responses are appended to the history, and the loop goes round again (`backend/main.py:752-754`). After 10 turns it fails with "Maximum turns exceeded" (`backend/main.py:817-826`).
6. Stats (calls, successes, per-tool success rate and average latency) are pushed every 2 s over `/ws` (`backend/main.py:212-228, 1047-1065`).

### README vs code
- README lists a "SafeExecutor: Timeout and error wrapper" component (`README.md:61`). No such class exists; the logic lives in `FunctionRegistry.execute`.
- README says the lesson "provides foundation for L19 RAG" (`README.md:51`). `document_search` ignores the query and reports `"search_method": "vector_similarity"` and `total_searched: 1000` as constants (`backend/main.py:117-130`).
- `STATUS_REPORT.md:10` calls the system "fully functional and production-ready" while saying the chat path hit a 429 quota error. Nothing in the repo shows the LLM loop running successfully; the many FIX/QUOTA .md files point the same way.

### Where it is thin or wrong
- [bug] `hasattr(part, 'function_call')` is always true for the SDK's proto `Part` objects, because an unset message field still exists. So a plain-text final answer is treated as a function call: `fc.name` is empty, the registry returns "Unknown function", and the loop goes round again instead of returning the answer (`backend/main.py:702, 724-737`). L16 (`setup.sh:278`) and L17 (`backend/main.py:212`) add the needed truthiness check; L18 dropped it. I confirmed in a scratch script on SDK 0.8.6 (the lesson pins 0.8.3) that a text-only `Part` gives `hasattr` True and an empty, falsy `function_call`. What Gemini then does with a function response that has an empty name (an API error, or more turns until `max_turns`) is UNVERIFIED. One consequence follows from the code alone: the check is `any(...)` over a list of parts that is never empty at that point (`backend/main.py:689`), so it is true on every turn. The "final answer" branch (`backend/main.py:704-717`) can therefore never run in LLM mode, and no LLM run can return `success: true` (given the SDK behaviour above).
- [bug] The timeout does not return early. Leaving the `with ThreadPoolExecutor` block waits for the worker thread, so a hung tool still blocks the request (`backend/main.py:178-201`).
- [bug] The fallback regexes are double-escaped inside raw strings, so revenue ("q3 2024", "quarter 3 2024") and product search ("search for laptop products") never match (`backend/main.py:465, 467, 472`). I checked by reading the pattern literals from the file as text and matching them in a scratch script. Only weather and keyword document search work, and the weather pattern stops at the first space, so an unlisted "San Francisco" becomes "San" (`backend/main.py:454`). The error text even suggests "Calculate revenue for Q3 2024" (`backend/main.py:507`).
- [misleading] Every tool is simulated:
  - revenue = $1M × 1.15^(quarters since 2020);
  - weather comes from a fixed table;
  - product search is a substring match over 5 items, with `search_time_ms` fixed at 150 (`backend/main.py:72-75, 87-97, 102-114`).
- [shallow] There is no input validation: `func(**inputs)` takes whatever the model sends (`backend/main.py:179`). The global `avg_latency_ms` stat is never updated (`backend/main.py:143`). One shared executor holds the history for all requests (`backend/main.py:666-667, 829`), and a sync model call runs inside an async handler (`backend/main.py:681`).
- [bug] Per-tool average latency adds latency only for successful calls but divides by all calls, so failures and timeouts pull the average *down* (`backend/main.py:187, 216`).
- [shallow] `max_turns` comes from the request with no upper bound (`backend/main.py:837, 852`), so a client can ask for any number of paid model calls.
- [ok-for-demo] `/api-key-status` spends a live model call on every request (`backend/main.py:970-971`).

### Tests and data
- `scripts/test_tools_direct.py:33-41` runs 7 direct tool calls and checks only the success flag (`scripts/test_tools_direct.py:25`). It imports `main` (`scripts/test_tools_direct.py:11`), so with a key set the start-up test call still runs (`backend/main.py:829, 338`). `scripts/test.sh` curls 4 endpoints and always ends with "All tests passed!" (`scripts/test.sh:30`). No data files.

### What to take for your project
- A5 skeleton, re-implemented in plain Python with Groq:
  - a registry of `name → (Pydantic schema, function)`;
  - a loop with a turn cap that appends tool results to the message list;
  - a per-step log entry (turn, tool, inputs, result, latency);
  - a real, cancellable timeout;
  - a server-side maximum for that cap, so a caller cannot raise it without limit.
- Make your first real tool `ragkit.retrieve(query, k)`, so the model decides when to retrieve (A1). Then measure retrieval quality and answer quality separately on the logged steps.
- D1: the per-turn `execution_log` is the right trace shape. Add token usage and cost per turn, and cache every model call and tool result (record/replay) so a logged run can be replayed step by step.
- Only after your plain-Python loop works, compare it with LangGraph's prebuilt agent and look at the LangSmith trace, on your own questions and project PDFs, never book text.

### Try this
- (20 min) Put `backend/main.py:211-215` (L17) next to `backend/main.py:702-727` (L18). Write two sentences on why L18 misreads a text answer. Then, in your own scratch code, build a fake reply with one text part and test both checks.

### Interview angle
- Q: "How do you stop an agent loop from running forever or hanging?" A: Cap the turns and the token or cost budget, and give every tool a timeout that really stops it. A Python thread cannot be killed, and an asyncio task is cancelled only at an `await`, so blocking tool code needs a subprocess you can kill; at the very least, stop waiting for the thread. Detect repeated identical calls and log every step, so you can see why a run stopped.

---

## Block summary

| Lesson | Title | Relevance | Concepts | Best file to read | Biggest problem |
|---|---|---|---|---|---|
| L10 | Simple state-machine agent | Low | A5 (counter), D1, M3 (counter) | `backend/agent.py` | "Act" is simulated, yet self-grading marks 3 of 4 real runs "goal achieved"; memory lookup searches keys, not content (`agent.py:53-54, 147, 202`; `data/agent_001_decisions.json`) |
| L11 | CoT reasoning evaluator | Medium | M3 (counter), V4 (counter), P7 | `backend/cot_agent.py` | Quality score is regex heuristics; correct answers score below "2+2" and "test" (`cot_agent.py:90-169`, `data/cot_memory.json`) |
| L12 | Few-shot learning | Medium | P4, C4, M4 (counters), P7 | `backend/main.py` | Hash-based "embeddings" that change every restart (same-sentence copies score no higher than different sentences); accuracy = 0.85 + 0.02 × shots (`main.py:113, 288`) |
| L13 | Context engineering | High | X3, X2 (counter), P3, D2 (counter) | `backend/services/context_optimizer.py` | Query-agnostic compression; budget never checked against the output (`context_optimizer.py:61-99`) |
| L14 | State management | Low | D2 | `backend/services/state_manager.py` | No real locking; Postgres-read and rollback paths likely broken, and rollback reports success anyway; empty tests (`state_manager.py:86, 113-121, 207, 210-213`) |
| L15 | Conversational agent | Medium | Q1 (counter), X3 (counter), M3 | `backend/gemini_client.py` | Full transcript pasted every turn, no query rewriting; canned fallback looks real (`gemini_client.py:21-323, 331`) |
| L16 | Tool / function calling | Medium | A1, A5 | `setup.sh:233-314` | Only the first tool call runs; result sent as prose (`setup.sh:297-307`) |
| L17 | Tool schemas (Pydantic) | Medium | A1, A5, D4 | `backend/tool_registry.py` | Tools are random or fake; converter drops constraints; "Validation Success Rate" ignores the model's calls (`tools.py:19-29`, `tool_registry.py:52-68`, `main.py:100-102`) |
| L18 | Tool execution loop | Medium | A5, A1, D1, D2, C4 (counter) | `backend/main.py:577-826` | Bare `hasattr` makes the final-answer branch unreachable; timeout does not return early; fake `document_search` (`main.py:702, 704-717, 178-201, 117-130`) |

### Cross-lesson patterns
- **Committed API keys (D4).** Full-length Google keys are hard-coded in:
  - `lesson10/setup.sh:9`;
  - `lesson11/setup.sh:9, 39, 1135`;
  - `lesson11/cot-reasoning-evaluator/docker-compose.yml:11`;
  - `lesson12/setup.sh:9, 40, 1336, 1429, 1446`;
  - `lesson13/setup.sh:9`;
  - `lesson14/setup.sh:9`;
  - `lesson10/l10-simple-agent/scripts/update-api-key.sh:17`;
  - `lesson12/l12-few-shot-learning/backend/main.py:23`;
  - `lesson12/l12-few-shot-learning/start.sh:12, 17`;
  - `lesson12/l12-few-shot-learning/Dockerfile:15` and `docker-compose.yml:9`.

  I grepped all of L10–L18 for the key prefix; L15–L18 contain none (their docs only mention the prefix). L10's own log records a 403 "API key was reported as leaked". This is a ready-made real example of why secrets stay in `.env`.
- **Dead model fallbacks.** `GenerativeModel(...)` makes no API call, so try/except chains around it never switch models (L11 `cot_agent.py:182-192`, L14 `agent_engine.py:22-26`, L17 `main.py:167-191`). L10 instead spends a live "test" call on the first request (`agent.py:92`), and L18 at start-up (`main.py:338`).
- **Tokens are mostly words.** Word counts in L12 (`main.py:197`) and L14 (`agent_engine.py:108`); a words × 1.3 guess in L15 (`gemini_client.py:345`); only L13 uses a real tokenizer (cl100k). None reads the provider's `usage` field (I checked with grep).
- **Canned or simulated outputs presented like real ones:**
  - L12: constant confidence and formula accuracy;
  - L13: $0.01/1K "savings";
  - L14 and L15: canned chat answers;
  - L16 and L18: table-driven weather;
  - L17: random weather;
  - L18: fixed "vector_similarity" documents.
- **Metrics that measure something other than their label.** Before you trust a dashboard number, find the line that computes it:
  - L12: `latency_ms` includes a throwaway LLM call (`main.py:111, 123, 180-183`);
  - L13: `compression_ratio` is characters in one branch and tokens in another (`summarizer.py:184`; `context_optimizer.py:75, 111`);
  - L17: "Validation Success Rate" counts only manual `/validate` calls (`main.py:100-102, 113-138`);
  - L18: per-tool average latency divides success-only latency by all calls (`main.py:187, 216`).
- **Self-grading or unvalidated judges reported as progress.** L10's evaluator marked 3 of 4 real runs "goal achieved" for echoed plans (`data/agent_001_decisions.json`); L11's heuristic score; L15's YES/NO goal judge (`goal_tracker.py:9-33`). None is checked against labels.
- **A capitalised "API key" test on a lower-cased string** can never match (L14 `agent_engine.py:119`, L15 `gemini_client.py:350`). In both, another test on the same line still catches `API_KEY_INVALID`.
- **Sync SDK calls inside `async` FastAPI handlers** (L11 `cot_agent.py:216`, L12 `main.py:201`, L15 `gemini_client.py:341` and `goal_tracker.py:18`, L16 `setup.sh:270`, L17 `main.py:197`, L18 `main.py:681`), which blocks the server. L10, L13 and L14 use a thread.
- **Tests check shape, not behaviour.** curl + grep, or "prints only" (L10, L12, L16, L18); `pass` bodies (L14). Real offline unit tests exist only in L11, L13, L15 (`tests/test_models.py`, 2 model tests) and L17, plus L18's direct tool-run script. None tests the core claim (score validity, budget fit, converter).
- **Generated folders differ from `setup.sh`** (L11, L17), because they were edited after generation. Always read the folder.
- **Old SDK.** Every lesson uses `google-generativeai` (pinned 0.3.2 to 0.8.3; L10 asks for >=0.8.0). The 0.8.6 build on this machine prints an end-of-support warning. Some model ids are already dead: L10's log shows 404s for `gemini-pro` and `gemini-1.5-flash`. Whether `gemini-2.0-flash-exp` and the other ids still answer is UNVERIFIED. Expect most of this code to need changes before it runs.
