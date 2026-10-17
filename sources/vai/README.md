# VAI course guide: what each lesson's code teaches, mapped to your RAG plan

**What this is:** a lesson-by-lesson guide to the code of the "Advanced Architectures for Vertical AI Agents" course (VAI), mapped to your RAG concepts.
**What this is not:** a copy of the course, or notebooks you can run.

The course code is in `C:\Yash\New-Work\RAG\vertical-ai-agents-main\`. For each of its 49 lesson folders, this guide says what the code really teaches, which files to read, where the code is wrong, and what to take into your project. Every claim cites `file:line`. Each lesson is a small FastAPI backend plus a React frontend, built for Google Gemini. There are no Jupyter notebooks. The course has no licence file, so nothing here is copied.

Written 2026-10-17. Nothing in the course was run, installed or changed.

---

## The answer first

1. **About a dozen lessons are worth your time.** Read them as designs to rebuild in plain Python, not as code to run.
   - **Core RAG:**
     - L19: the naive baseline.
     - L20: embedding search (dense retrieval), done right.
     - L22: re-scoring the top hits with a model that reads question and chunk together (a cross-encoder).
     - L23: the hybrid pipeline shape. Its keyword leg is fake.
     - L37: keyword and embedding search merged by rank (BM25 + dense + RRF).
   - **Prompts and context:**
     - L25: grounding prompts and a fixed refusal sentence. Read it for the ideas, not the code.
     - L7: a fixed JSON answer format.
     - L13: token budgets.
     - L26: rewriting a follow-up into a standalone question.
   - **Agents and checks:**
     - L32: a real think → act → observe loop (ReAct).
     - L43: numbered sources that the answer cites, plus an LLM grading each chunk.
     - L44: judge prompts and a deployment gate.
   - **Production:**
     - L6: a production LLM client.
     - L42 and L69: what a trace record should hold.

   The rest are context, counter-examples or interview stories.
2. **No lesson measures retrieval.**
   - No lesson has a question set labelled with the right chunk ids. L44's 10 gold records carry only reference answers, and L29's suite has 3 cases.
   - None computes Recall@k (is a right chunk in the top k?), MRR (how high is the first right chunk?) or nDCG (a rank-weighted relevance score).
   - L44 comes closest: an LLM, not a label, judges whether the retrieved chunks were relevant and complete.

   So **no VAI number can tell you that a technique works.** Your Phase 3 harness fills that gap, and only your own logged runs fill a results table ([ground rule 5](../../README.md#ground-rules-this-system-enforces)).
3. **Technique names often promise more than the code does.**
   - "BM25 full-text search" in L23 is a second dense search.
   - The "cross-encoder" in L37 is one Gemini prompt.
   - The "semantic embeddings" in L12 are Python `hash()` values.

   The table [below](#the-names-to-distrust) lists the main ones.
4. **The failure that repeats everywhere: errors reported as success.**
   - L27 marks random scores as "completed".
   - L29 gives an empty answer 100% groundedness.
   - L44 swaps in passing scores, so its gate says DEPLOYED.
   - L43 returns synthesis errors, and canned rate-limit answers that carry a real-looking `[1]` citation, with the state DONE.
   - L34 returns every budget hit as success.
   - L69 traces a failed LLM call as OK.

   **For your LLMOps notebooks: a fallback is a labelled, counted failure, and a failed run has the status `failed`.**
5. **Safety warnings.**
   - **Never run any lesson's `cleanup.sh`.** Several delete *all* Docker images and volumes on your machine. Some also stop every running container.
   - **A Google API key is hard-coded in 24 files across 13 lessons** (L1–L5, L8, L10–L14, L22, L44). Treat it as leaked: never use it, and never copy those files into `rag_learning/`, which is your git repo. Your copies in `prior_work\VAI\` have it in 3 files: `lesson22\...\backend\main.py`, and `docker-compose.yml` in both L44 copies.
   - **Some demo tools run `eval` on text the model chose.** L34 has no whitelist at all, which means code execution. L28 and L32 use character whitelists that let `**` through, so one `9**9**9` can freeze the server.
   - **L6's Dockerfile copies `.env` into the image,** so any key you add gets baked in.

**How far to trust this guide:** every cited line was re-opened twice by independent checkers. On the first check about 1 claim in 7 needed a fix (203 of 1,419), and all of those are now corrected. The counts are in the [caveat](#the-honest-limit) at the end; the logs are in [verification/](verification/).

---

## How to use this with your plan

1. **When you start a concept, look it up in the topic map below.** It names the lessons, best first.
   - Concept IDs (P1, C1, M1 …) are the cards in [02 §3](../../02_RAG_MASTER_LEARNING_PLAN.md#3-concept-cards).
   - The letter tells you the phase: P = 1, C = 2, M = 3, I = 4, R = 5, Q = 6, X = 7, V = 8, D = 9, A = 10, S = 11, K = 12.
2. **First read the book pages and our reading file for the concept,** in `study/reading/<ID>_*.md` (for example [P3_bm25.md](../../study/reading/P3_bm25.md)). Only some exist so far.
   - Then read the VAI section as "how someone else built it, and what they got wrong".
   - Then write your own plain-Python version. This is your mechanism-first rule.
3. **Each lesson section has the same parts, in this order:**
   - What the code teaches (one line), and what it is not
   - Relevance and concept IDs
   - Stack, and how hard a swap to Groq or Cohere is
   - Read in this order
   - How it works, step by step
   - README vs code
   - Where it is thin or wrong
   - Tests and data
   - What to take for your project
   - Try this (10–30 minutes)
   - Interview angle (one question)
4. **Open the cited files next to the guide.**
   - A `file:line` is relative to the lesson's project folder. Each lesson heading names that folder, for example `lesson19/l19-naive-rag/`.
   - The lesson links below open the block file at the top. Search for `## L23` to jump to a lesson.
5. **Tags used in the lesson sections.**
   - In "Where it is thin or wrong":
     - **[bug]**: the code does the wrong thing.
     - **[misleading]**: a label, message or number claims more than the code does.
     - **[shallow]**: it works, but is too thin for your project.
     - **[ok-for-demo]**: fine for a demo, not for real use.
   - On the relevance line:
     - **[LLMOps]**: material for your LLMOps notebooks.
     - **[Interview]**: worth practising for interviews.
6. **Don't run the apps.** Many Gemini model ids are old or experimental, and several Docker builds are broken as shipped. The step-by-step sections tell you what the code does anyway.

| Guide file | Lessons | Theme |
|---|---|---|
| [L01-L09_foundations.md](L01-L09_foundations.md) | 1–9 | Python, async, attention, LLM parameters and cost, LLM client, JSON output, decisions, memory |
| [L10-L18_agents_and_tools.md](L10-L18_agents_and_tools.md) | 10–18 | State-machine agent, reasoning scores, few-shot, context engineering, state, conversation, tool calling |
| [L19-L23_core_rag.md](L19-L23_core_rag.md) | 19–23 | **Naive RAG, vector DB, chunking, reranking, hybrid search** |
| [L24-L27_langchain_prompting_multiturn_eval.md](L24-L27_langchain_prompting_multiturn_eval.md) | 24–27 | **LangChain RAG chain (LCEL, LangChain's `\|` pipe syntax), grounding prompts, multi-turn RAG, RAGAS (a RAG evaluation library)** |
| [L28-L32_tools_eval_observability_react.md](L28-L32_tools_eval_observability_react.md) | 28–32 | Tool router, eval framework, RAG observability, ReAct |
| [L33-L38_agentic_rag_parts.md](L33-L38_agentic_rag_parts.md) | 33–38 | Reflexion, loop budgets, "agentic RAG", planner, **retriever + reranker**, validator |
| [L39-L44_agentic_rag_pipeline_and_eval.md](L39-L44_agentic_rag_pipeline_and_eval.md) | 39–44 | Compliance, fallback, synthesizer, traceability, **agentic RAG end to end, RAG eval gate** |
| [L49-L69_multi_agent_and_ops.md](L49-L69_multi_agent_and_ops.md) | 49, 54, 59, 64, 69 | CrewAI, personalisation, multi-agent eval, deployment, OpenTelemetry |
| [verification/](verification/) | all | Every claim that was checked, with its verdict and evidence |

The course says it has 90 lessons. Only these 49 folders are on disk. The others exist only as articles on the course's Substack.

---

## Topic map: your concepts → VAI lessons

**How to read the markers:**
- **(counter)**, or a lesson listed after **Counters:**, names the technique but does not build it. Read it to learn what is missing.
- **(shape only)** and **(weak)** mean the lesson shows the outline of the idea, not a working version.
- **None** means no VAI lesson covers the concept, so the book and our lessons are your only sources.

### Phase 1: prerequisites

| Concept | Read (best first) | What it gives you | Watch out |
|---|---|---|---|
| P1 LLM fundamentals | L3, L4 (L13 for token counts) | L3: real scaled dot-product attention maths. L4: the cost formula, and why the context window is not your bill | L3 feeds random, token-blind inputs, with dropout left on at inference. L13 counts with cl100k (an OpenAI tokenizer), not your model's tokenizer |
| P2 IR framing | L19 | An inverted index (word → chunk ids) in a few lines | L9's "search" is substring match plus recency (counter) |
| P3 TF-IDF & BM25 | L19, L37, L13 | L19: overlap counting, your "before BM25" baseline. L37: real `rank-bm25` BM25Okapi. L13: TF-IDF weights fitted on the context's own sentences (IDF weighting with no query) | **L23 has no BM25 at all** (counter). L37 keeps zero-score BM25 hits and does no stemming. L9's "keyword search" has no scoring (counter) |
| P4 Embeddings & similarity | L20, L21 | L20: separate document and query task types (the embedder is told which kind of text it gets), cosine space, and similarity = 1 − distance, done right. L21: three embedders and their truncation limits | Counters: L3's random "embeddings", L12's `hash()` "embeddings", L24's SHA-256 vectors, L54's cosine on all-positive vectors. L26, L30, L37 and L43 report "1 − distance" on Chroma's default squared L2 as a similarity. For unit vectors that equals 2·cos − 1, which goes negative for weak matches. L37 shows it ×100 as a percentage |
| P5 Vector search | L20 | Chroma told to measure cosine distance (`hnsw:space="cosine"`; HNSW is Chroma's fast search index) | L21, L24, L26, L28, L30, L37 and L43 never set it, so Chroma uses its default: squared L2, the squared straight-line distance |
| P6 Retrieval eval basics | **None** | — | No lesson computes a retrieval metric against labels |
| P7 Grounded prompting | L25, L7, L19, L12, L41 | L25: strict, moderate and creative templates, plus a fixed refusal sentence. L7: parse the JSON; if that fails, strip the ``` fences; if that fails, ask the model to repair it. L12: the few-shot prompt shape. L41: chained prompts, as a contrast | L25's context has no `[Source N]` labels for the model to cite. L12's example picker uses hash noise. L11's chain-of-thought prompt and L49's role prompts carry no grounding context (counters) |

### Phase 2: core baseline

| Concept | Read (best first) | What it gives you | Watch out |
|---|---|---|---|
| C1 Loading & parsing | L19 | PyPDF2 page extraction | Pages are joined, and the cleaning step deletes `/ % + = #`. **No lesson keeps page numbers** |
| C2 Chunking | L19, L20, L21 | Fixed 500/50-character windows. L21 runs 5 chunkers side by side | Characters only, never tokens. L19, L20 and L21 all make a duplicate tail chunk, and L19's test treats it as correct. L21's recursive chunker can recurse forever |
| C3 Indexing with metadata | L20 | Per-chunk metadata and MD5 ids. A manual `clear-collection.sh` reset for re-indexing after a model change | It uses `add`, not `upsert` (insert-or-update), so an edited document leaves stale chunks. L24 passes no ids, so every ingest duplicates |
| C4 Dense retrieval | L20, L43, L37, L24 | L20: the cleanest query → top-k → score path in the course. L37: dense search per sub-query, then merge and de-duplicate. L24: an LCEL retriever chain | Counters: L12; L18's fake `document_search`; L42's "semantic" retriever, which is word overlap and crashes on tied scores. L24's default path uses SHA-256 vectors and a canned answer |
| C5 Context & citations | L43, L25, L7, L19 | L43: numbered context and inline `[n]` markers, mapped to chunk ids in code. L7: the answer as a JSON contract (answer, cited chunk ids). Add a check that every cited id was in the prompt | L41 maps citations after the answer is written and never verifies them (counter). L28 lists every context chunk as a "source" (counter). L64 asks the model to "cite sources" with no retrieval (counter). L19 and L26 label chunks but never ask for citations. L43's canned rate-limit answers contain `[1]`, so they look grounded |
| C6 Baseline + provenance trace | L19, L43, L42, L8, L30 | L19: the skeleton. L43: a per-trace JSON with every agent's events, the answer and the cited chunks. L42 and L8: trace record shapes. L30: what a trace must not leave out | No lesson can trace an answer back to a page. L43's audit lacks the uncited chunk ids, the prompts and the model id. L24's trace is hand-made |
| C7 Structured data RAG | **None** | — | — |

### Phase 3: measurement

| Concept | Read (best first) | What it gives you | Watch out |
|---|---|---|---|
| M1 Eval set | L44, L29, L27 | L44: the record shape (question, contexts, answer, ground truth). L29: a JSON test suite with typed cases (add your own `suite_version`). L27: 10 questions you can label yourself | **L27's "ground truth" is the system's own answer.** L44's 10 items live in code and never test L43 |
| M2 Retrieval metrics | **None** (L44 partly) | L44 has LLM-judged context recall and precision | L27's context precision and recall are a **constant 0.8** (counter). There is no Recall@k, MRR or nDCG anywhere |
| M3 Generation metrics & judge | L44, L27, L28, L7, L38, L15 | L44: four judge prompts. L27: the RAGAS metric definitions. L28: separate groundedness and relevance judges. L7: a schema check as the cheap first tier. L38: a judge-output contract (score, list of conflicts, confidence). L15: a binary YES/NO judge shape | Counters: L11's regex "reasoning quality", L29's word overlap, L10's self-grading, L33's keyword "evaluator", L41's judge (it sees 200-character chunk heads and defaults to pass), L59's "non-empty" test. L27 uses the generator as its own judge |
| M4 Experimental discipline | L5 | The Pareto check is sound: drop any option that another beats on quality, latency and cost | Counters: L5's random latencies on API errors, L12's accuracy formula (0.85 + 0.02 × shots), L27's n = 2. L29 reports fixed sleeps as latency and takes p99 from 9 samples. L4 and L5 take p95 from 3–5 samples |
| M5 Failure taxonomy | **None** | Nothing usable. L44 asks the judge for reasons and then discards them (`backend/app/metrics.py:154, 164`). L36's fallback has no reason code (`backend/app/planner.py:130-145`) | Add per-claim verdicts and fallback reason codes yourself (see the L44 and L36 sections). L27 copies the run average onto every question, so there is nothing to analyse |

### Phase 4: indexing

| Concept | Read (best first) | What it gives you | Watch out |
|---|---|---|---|
| I1 Size/overlap experiments | L21 | The knobs: size, overlap, stride | Its "coherence" score rewards overlap, not quality. Replace it with Recall@k |
| I2 Structure-aware | L21 (weak) | A paragraph → sentence "recursive" splitter | It ignores its own overlap setting, and every `start_pos` is 0 |
| I3 Semantic chunking | L21 | Cut where the cosine between neighbouring sentences drops below 0.5, with a minimum size | No maximum size, so chunks can exceed the embedder's input limit |
| I4, I5, I6 | **None** | — | — |
| I-CMP | L21 (counter) | Compares chunkers on size statistics | No retrieval at all, so it cannot say which chunker retrieves better |

### Phase 5: retrieval

| Concept | Read (best first) | What it gives you | Watch out |
|---|---|---|---|
| R1 Hybrid & fusion | L37, L23 | L37: BM25 + dense merged by RRF (reciprocal rank fusion: each list adds 1/(k + rank); k = 60, ranks from 1). L23: the pipeline shape, RRF → rerank | **L37 throws the fused ranking away**: it sorts by `vector_score`. L23's "keyword" leg is a second dense search. With a working key it is expected to fail on a dimension mismatch and return nothing (Chroma behaviour, UNVERIFIED). L24's "hybrid" is vector search + MMR (a re-pick that drops near-duplicates) (counter). L43's "keyword" and "hybrid" options are ignored (counter) |
| R2 Metadata filtering | L23, L20 | A Chroma `where` pre-filter, plus a hand-written post-filter | L23's post-filter lets unknown operators pass. L20's UI never sends filters |
| R3 Reranking | L22, L37, L23 | L22: a real local cross-encoder. Its outputs are logits (raw scores, often −10 to +10), not 0–1. L37: an LLM 0–100 listwise scorer | L22's "improvement %" compares logits with cosine-like scores, and its cache key ignores `top_k` and the document text. L24 has a reranking flag but no reranker (counter). L28's "rerank" keeps the first 3 of 5 (counter) |
| R4 MMR (diversity) | L24 | A library MMR call, with `lambda_mult` (the relevance-vs-diversity dial) left at its default | Interleaved with plain vector results and called "hybrid" |
| R5 Hierarchical / RAPTOR | **None** | — | — |

### Phase 6: query side

| Concept | Read (best first) | What it gives you | Watch out |
|---|---|---|---|
| Q1 Query transformations | **L26**, L36, L37, L43 | L26: an LLM rewrites the follow-up into a standalone question (the "condense question" step). L36: a decomposition prompt with a schema. L37 and L43: search per sub-query, then merge | L26 decides "ask to clarify" *before* rewriting, from regexes and a constant. L36 silently falls back to 1 sub-query. L15 never rewrites, and L40 throws its sub-queries away (counters) |
| Q2 HyDE | **None** | — | — |

### Phase 7: context

| Concept | Read (best first) | What it gives you | Watch out |
|---|---|---|---|
| X1 Window enrichment | **None** | — | — |
| X2 Compression | L13 (counter) | Extractive TF-IDF compression | It ignores the query, and the output is never checked against the budget |
| X3 Assembly & token budget | L13, L26 | L13: real token counting and a budget. L26: a history window | After compressing, **re-count**; L13 never does. L54's budget "tiers" use hard-coded costs. L15 pastes the whole transcript every turn, and L9 windows history by message count, not tokens (counters) |

### Phase 8: reliability

| Concept | Read (best first) | What it gives you | Watch out |
|---|---|---|---|
| V1 Citation verification | L25, L43 | L25: a regex range check as a cheap first tier. L43: a marker → chunk-id map | **No lesson checks that a cited chunk supports its sentence.** L41 (counter) |
| V2 Relevance grading + groundedness | L43, L28, L38 | L43: grade chunks against a threshold, then a bounded retry. L28: a groundedness judge. L38: a judge-output contract | L38 compares chunk with chunk, not answer with source. L40's validator is `random() < 0.3`. L25's "grounding confidence" never reads the answer. L35's validator averages constants (counters). L39 checks only for contradictions between documents |
| V3 Abstention | L19, L25, L43, L40 (shape only) | L19: no hits, so no LLM call. L25: a fixed refusal sentence, plus adversarial context. L40: a final abstain message | L25 labels an API error "rejected", the same as a correct refusal. L43 answers from the top 3 even when no chunk passes |
| V4 Judge reliability | **None** (counters only) | — | L27 judges with its own generator. L38 turns judge errors into 0.7, which can never read as "failed". L44 turns a failed run into DEPLOYED. L11's regex score and L25's substring "hallucinated" test are never checked against labels. L41's judge defaults to pass |

### Phase 9: production

| Concept | Read (best first) | What it gives you | Watch out |
|---|---|---|---|
| D1 Observability | **L69**, L42, L43, L59, L6, L30 | L69: OpenTelemetry (standard tracing) spans, one per timed step (`agent.run` → prompt / LLM / post-process), with `llm.*` attributes, exported to local SQLite. L42: a trace held in a ContextVar (a per-request Python variable), a timing decorator and JSONL. L43: a per-trace JSON audit file. L59: trace records with parent ids. L6: a JSON log line per call, with a request id. L34: token history per step | L69 traces failures as OK. L30 records no query, chunk ids or answer, so nothing can be replayed. L43's audit has no prompts and no model id. L64 has HTTP-level metrics only |
| D2 Latency, cost, caching | L6, L34, L69, L4, L22, L59 | L6: a rate limiter, a circuit breaker (it pauses calls to a failing API) and a cost tracker. L34: a budget object. L69: p50/p95/p99 per stage (the median, and the slowest 5% and 1% of calls), cost per query. L22: p95/p99 latency. L59: token and latency budgets per test | L6 has mock mode on by default and books invented tokens as cost. L34 checks the budget *after* the call is paid. L2's retry never fires in its default mode. L59's "replay" only copies records, so it is no model for record/replay. L38 caches judge verdicts by document id, so edited text gets stale verdicts, and it caches fallbacks too. L13 prices tokens with a constant (counter). L69's cost alarm almost never fires |
| D3 Regression eval & index versioning | L44, L29, L59, L64, L20 | L44: a threshold gate. L29: compare a run with a baseline. Compare with your previous stored run, not with fixed targets. L59: a test case with token and latency budgets. L64: CI gates. L20: the manual collection reset after a model change | **L44's gate fails open.** L59 grades crashed runs as PASS. L64's CD pipeline is broken as shipped. L27's trend chart plots placeholder numbers, and its test asserts the fake baseline (counter) |
| D4 Security & safety | L17, L39, L64 | L17: Pydantic validation of tool arguments. L39: regex plus LLM rules. L64: a non-root image and a scan for known security holes (CVEs) | L39's LLM rules never see the content. L9 allows path traversal. Keys are hard-coded across 13 lessons. `eval` runs on model-chosen input (L34 with no filter; L28 and L32 let `**` through). L6's Dockerfile bakes `.env` into the image |

### Phase 10: control flow

| Concept | Read (best first) | What it gives you | Watch out |
|---|---|---|---|
| A1 Routing | L28, L26, L16–L18, L32, L36 (weak) | L28: rules first, an LLM classifier second. L26: clarify-or-answer. L16–L18: tool calling | L18's final-answer branch is unreachable in LLM mode. L36's `requires_decomposition` flag is never acted on. L5's "cascading" is only a label (counter) |
| A2 Corrective RAG | L43, L28, L33 | Grade, then retry with a wider k. L28 re-queries when groundedness is low | L43's retry tends to *lower* its own average pass score. L40's grader is random (counter) |
| A3 Self-RAG | L33 (shape only) | Critique → store → retry | Its success signal is a keyword-and-length check on the tool output |
| A4 Feedback loops | **None** | — | L54 stores feedback and never reads it (counter) |
| A5 Agentic RAG | **L32**, L18, L17, L43, L34, L33 | L32: a real Thought / Action / Observation loop with a step limit; add a retrieval tool yourself. L34: a bounded loop with call and token caps. L33: act → check → reflect → retry, with no retrieval | L35 is a fixed pipeline: its planner, retriever and validator return constants, and only the synthesizer calls an LLM. L31 has no Act step. L10's "act" is simulated. L49's agents have no tools (counters). L43's FAST_MODE default skips the planner and validator. L34 reports every cap hit as success |

### Phases 11–12

| Concept | Read | Note |
|---|---|---|
| S1 Graph RAG, S2 Multimodal, S3 MemoRAG | **None** | Not in the course folder |
| K1 Architecture defence | L43, L64 | L43 makes a good system-design case: say what you would change, and why. L64 is for interview questions on deployment and readiness probes |

---

## All 49 lessons at a glance

**How to read this table:**
- Relevance is to *your RAG study*, not to the course's own goals.
- **(rebuild)**: worth rebuilding correctly.
- **(ideas)**: read for the ideas, not the code.
- **(warning)**: an example of what not to do.
- **(Medium for LLMOps)**: little RAG content, but useful for your LLMOps notebooks.
- **High (R3)**: high for that one concept.
- In the Concepts column, "(counters)" after several IDs applies to all of them. "(counter)" after one ID applies to that ID only.

| Lesson | What the code teaches | Relevance | Concepts | Biggest problem |
|---|---|---|---|---|
| [L1](L01-L09_foundations.md) | Python environment setup and checks | None | — | Hard-coded key in `.env.example` |
| [L2](L01-L09_foundations.md) | Async, decorators, Pydantic | Medium | D2, P1 | Retry never fires in default mode; fallbacks cached as success |
| [L3](L01-L09_foundations.md) | Transformer attention visualiser | Medium | P1, P4 (counter) | Real maths on random, token-blind inputs |
| [L4](L01-L09_foundations.md) | LLM parameters, cost, context | Medium | P1, D2 | Unsourced specs; "context savings" fallacy |
| [L5](L01-L09_foundations.md) | Model comparison benchmark | Low | M4 (counter), D2, A1 (counter) | API errors become random latencies with success = true |
| [L6](L01-L09_foundations.md) | Production LLM client | **High** | D2, D1 | Mock mode on by default skips retry and breaker |
| [L7](L01-L09_foundations.md) | Prompting for JSON output | **High** | P7, C5, M3 | Repair loop crashes; `{}` passes unvalidated |
| [L8](L01-L09_foundations.md) | Plan → deliberate → execute agent | Low | A5, A1, C6, D1 | Success even when every step fails |
| [L9](L01-L09_foundations.md) | Agent memory | Low | P2, P3, X3 (counters), D4 | Path traversal; "search" is substring match |
| [L10](L10-L18_agents_and_tools.md) | State-machine agent | Low | A5 (counter), D1, M3 (counter) | "Act" is simulated; self-graded "goal achieved" |
| [L11](L10-L18_agents_and_tools.md) | Chain-of-thought evaluator | Medium | M3, V4 (counters), P7 | Quality score is regex heuristics |
| [L12](L10-L18_agents_and_tools.md) | Few-shot example selection | Medium | P4, C4, M4 (counters), P7 | `hash()` "embeddings"; accuracy is a formula |
| [L13](L10-L18_agents_and_tools.md) | Context engineering: tokens, compression | **High** | X3, X2 (counter), P3, D2 (counter) | Compression ignores the query; budget never re-checked |
| [L14](L10-L18_agents_and_tools.md) | State management (Postgres + Redis) | Low | D2 | No real locking; rollback reports success anyway |
| [L15](L10-L18_agents_and_tools.md) | Conversational agent | Medium | Q1, X3 (counters), M3 | Full transcript every turn; no rewriting |
| [L16](L10-L18_agents_and_tools.md) | Function calling (`setup.sh` only) | Medium | A1, A5 | Only the first tool call runs |
| [L17](L10-L18_agents_and_tools.md) | Tool schemas with Pydantic | Medium | A1, A5, D4 | Tools return fake data; converter drops constraints |
| [L18](L10-L18_agents_and_tools.md) | Tool execution loop | Medium | A5, A1, D1, D2, C4 (counter) | Final-answer branch unreachable; timeout does not return early |
| [L19](L19-L23_core_rag.md) | Naive RAG (keyword overlap + Gemini) | **High** | C1, C2, C5, C6, P2, P3, P7, V3 | No IDF; page numbers lost; errors returned as answers |
| [L20](L19-L23_core_rag.md) | ChromaDB vector store | **High** | P4, P5, C3, C4, R2 | Retrieval only; no page/offset; stale chunks after edits |
| [L21](L19-L23_core_rag.md) | Chunking + embedding lab | Medium-High | C2, I1, I3, P4, I-CMP (counter) | No retrieval; "coherence" rewards overlap |
| [L22](L19-L23_core_rag.md) | Cross-encoder reranker + cache | **High** (R3) | R3, D2, D4 (counter) | "Improvement %" mixes scales; hard-coded key |
| [L23](L19-L23_core_rag.md) | Hybrid search: RRF, filters, rerank | **High** (rebuild) | R1 (counter for the sparse leg), R2, R3 | **No BM25**; "keyword" leg is a second dense search; `alpha` unused |
| [L24](L24-L27_langchain_prompting_multiturn_eval.md) | LangChain RAG chain built with LCEL pipes | Medium | C4, C5, C6, R4, D1; R1, R3 (counters) | Default path uses hash vectors and a canned answer |
| [L25](L24-L27_langchain_prompting_multiturn_eval.md) | Grounding prompts | **High** (ideas) | P7, C5, V1, V3; V2, V4 (counters) | "Grounding confidence" never looks at the answer |
| [L26](L24-L27_langchain_prompting_multiturn_eval.md) | Multi-turn RAG: rewrite + clarify | **High** | Q1, A1, X3, C5 | Retrieval confidence is a constant 0.5 and history is ignored; no Redis = no memory |
| [L27](L24-L27_langchain_prompting_multiturn_eval.md) | RAGAS evaluation dashboard | **High** (warning) | M3; M1, M2, M4, V4, D3 (counters) | Constant 0.8 metrics; own answer as ground truth |
| [L28](L28-L32_tools_eval_observability_react.md) | Tool-equipped agent (router) | Medium | A1, C5, M3, A2 (weak), R3 (counter) | Hard-coded 0.75 scores; re-query keeps old scores |
| [L29](L28-L32_tools_eval_observability_react.md) | Evaluation framework | Medium (warning) | M1, M3 (counter), M4 (weak), D2, D3 | Empty answer scores 1.0 groundedness |
| [L30](L28-L32_tools_eval_observability_react.md) | RAG observability | Medium | D1, D2, C6, P4 (counter) | Trace has no query, chunk ids or answer |
| [L31](L28-L32_tools_eval_observability_react.md) | ReAct planning | Low | A5 (counter) | No Act step; errors reported as COMPLETED |
| [L32](L28-L32_tools_eval_observability_react.md) | ReAct agent with tools | Medium | A5, A1 | Tests cannot fail; sync loop blocks the server |
| [L33](L33-L38_agentic_rag_parts.md) | Reflexion agent | Medium | A5, A2/A3 (shape), M3 (counter), D2 | Success = keyword/length heuristic |
| [L34](L33-L38_agentic_rag_parts.md) | Loop controls and budgets | Medium | D2, D1, A5 | Every budget hit reported as success |
| [L35](L33-L38_agentic_rag_parts.md) | "Agentic RAG" orchestrator | Low | A5, A1, V2 (counters), D2, C5 | Planner, retriever and validator return constants |
| [L36](L33-L38_agentic_rag_parts.md) | Planner: query decomposition | Medium | Q1, A1 (weak) | Schema slips fall back to 1 sub-query silently |
| [L37](L33-L38_agentic_rag_parts.md) | Retriever + reranker | **High** | R3, R1, Q1, C4, P3, P5, P4 (counter) | Fused ranking discarded; "cross-encoder" is a prompt |
| [L38](L33-L38_agentic_rag_parts.md) | Validator: pairwise consistency | Medium | V2 (adjacent), M3, D2, V4 (counter) | Judge errors become 0.7, never "failed" |
| [L39](L39-L44_agentic_rag_pipeline_and_eval.md) | Compliance validator | Low | D4, V2 (adjacent) | LLM rules never see the content |
| [L40](L39-L44_agentic_rag_pipeline_and_eval.md) | Fallback and self-healing | Low | A2, Q1 (counters), V3, D2 | Validator is `random() < 0.3` |
| [L41](L39-L44_agentic_rag_pipeline_and_eval.md) | Synthesizer with citations | Medium | C5, V1 (counters), P7, M3 | Citations mapped after the fact, never verified |
| [L42](L39-L44_agentic_rag_pipeline_and_eval.md) | Traceability layer | Medium | D1, C6 (partial), C4 (counter) | Audit cannot replay an answer; tie-sort crash |
| [L43](L39-L44_agentic_rag_pipeline_and_eval.md) | Agentic RAG end to end | **High** | A5, A2, Q1, V2, V3, C4, C5, C6, D1, R1 (counter) | FAST_MODE default skips planner and validator |
| [L44](L39-L44_agentic_rag_pipeline_and_eval.md) | RAG eval + deployment gate | **High** | M1, M3, D3, M2 (partly), V4 (counter) | Failed run → fake passing scores → DEPLOYED |
| [L49](L49-L69_multi_agent_and_ops.md) | CrewAI role-based crew | Low | A5, P7 (counters) | Demo fallback passes the test |
| [L54](L49-L69_multi_agent_and_ops.md) | Agent personalisation | Low | P4, X3, A4 (counters), D4 (partial) | Cosine on all-positive vectors picks the wrong persona |
| [L59](L49-L69_multi_agent_and_ops.md) | Multi-agent eval and debugging | Medium | D1, D2, D3, M3 (counter) | Crashed runs grade as PASS |
| [L64](L49-L69_multi_agent_and_ops.md) | CD, containers, Prometheus, Kubernetes (k8s) | Low (Medium for LLMOps) | D1–D4, C5 (counter) | Build and deploy wiring broken |
| [L69](L49-L69_multi_agent_and_ops.md) | Agent observability (OpenTelemetry) | Medium | D1, D2 | LLM failures traced as OK |

---

## The names to distrust

Read the number's definition, not its label.

| The course calls it | What the code actually does | Where |
|---|---|---|
| "BM25 full-text search" (L23) | A second dense search through Chroma's default embedder. With a working key it is expected to fail on the 768-vs-384 dimension mismatch (Chroma behaviour, UNVERIFIED) and return `[]` silently. Without a key it ranks identical dummy vectors | L23 `backend/main.py:204-230` |
| "Precision@5: 89%" (L23 README) | No eval or benchmark code exists, so the number has nothing behind it | L23 `README.md:133-135` |
| "Hybrid retrieval" (L24) | Vector search + MMR over the same index, interleaved | L24 `backend/main.py:137-151` |
| "Cross-encoder reranker" (L37) | One Gemini prompt scoring all chunks 0–100 | L37 `backend/reranker_tool.py` |
| "Vector" score (L37) | 1 − Chroma's default distance, shown ×100 as a percentage | L37 `backend/vector_store.py:106` |
| "Rerank" (L28) | Keeps the first 3 of 5 results: a list slice | L28 `backend/rag/engine.py:90-92` |
| "Semantic" retriever and "rerank" (L42) | Word overlap. The rerank multiplies by a constant, so the order never changes | L42 `backend/agents/retriever.py:54-65` |
| "Semantic embeddings" (L12) | Python `hash()` of character slices, different on every restart | L12 `backend/main.py:113` |
| "Grounding confidence" (L25) | Word overlap between the *question* and the context, computed after the answer | L25 `backend/app.py:112-127` |
| "RAG groundedness" (L29) | Word overlap against reference sentences. An empty answer scores 1.0 | L29 `backend/app/services/validators.py:34` |
| "Context precision / recall" (L27) | The constant 0.8 | L27 `backend/app/services/rag_evaluator.py:126-127` |
| "Ragas" metrics (L44) | Ragas is commented out, so four custom Gemini judge prompts run instead. Context precision is unranked (relevant ÷ total) | L44 `backend/app/metrics.py:288-290`, `:93-113` |
| `quality_score` (L43) | The mean retrieval score of the chunks, or 0.5 when that is ≤ 0. It never looks at the answer | L43 `backend/agents/synthesizer.py:97-99` |
| "Chain-of-Thought" (L41) | Prompt chaining: 1, 3 or 5 separate Gemini calls | L41 `backend/agents/cot_engine.py:71-100` |
| "Coherence" (L21) | The mean cosine between *neighbouring* chunks, so more overlap raises it | L21 `backend/app/services/chunking_service.py:212-219` |
| "Agentic RAG" (L35) | A fixed pipeline. The planner, retriever and validator return constants, and only the synthesizer calls an LLM | L35 `backend/agents/retriever_agent.py:10-47` |
| "Validator" (L40) | `random() < 0.3` | L40 `backend/validator_agent.py:19` |
| "Real-time cost analysis" (L13) | A made-up constant of $0.01 per 1K tokens | L13 `backend/services/context_optimizer.py:142` |
| "Semantic" memory (L26) | Falls back to a sliding window | L26 `backend/app/services/conversation_memory.py:15, 33-40` |
| "Query expansion" (L26) | One standalone rewrite. That is fine, but it is rewriting, not expansion | L26 `backend/app/services/context_expander.py:44-51` |

**Backed by the code ✅**

| What | Where |
|---|---|
| Distance → similarity done correctly, because the space is set to cosine | L20 `backend/search_engine.py:31-39` |
| A real local cross-encoder, whose outputs are raw logits | L22 `backend/main.py:120-121` |
| A condense-question rewrite, with retrieval on the rewrite | L26 `backend/app/services/context_expander.py:31-71`, `backend/app/services/rag_service.py:146` |
| A real text-protocol ReAct loop with a step limit | L32 `backend/agent.py` |
| Standard RRF (k = 60, ranks from 1) | L37 `backend/retriever_agent.py:122-164` |
| A numbered context mapped to chunk ids in code | L43 `backend/agents/synthesizer.py:120-147` |
| An OpenTelemetry span tree with token, cost and latency attributes | L69 `backend/agent.py` |

---

## What this changes in your plan (proposed, not applied)

| Where | Today | Proposed | Why |
|---|---|---|---|
| [02 §5](../../02_RAG_MASTER_LEARNING_PLAN.md#5-fast-track-rules-from-the-o1-diagnostic), row "VAI L23 → R1, R2" | Your earlier L23 work counts toward a fast-track on R1 and R2 | Count it toward **RRF only**. The sparse half of R1 gets no fast-track credit | Evidence: L23 has no BM25 (`backend/main.py:204-230`) |
| [02](../../02_RAG_MASTER_LEARNING_PLAN.md) D1 card, "FT: partial (VAI L30: tool tour only)" | Your earlier L30 work is evidence for a partial D1 fast-track, checked by its O1 probe | Keep L30 as fast-track evidence (with its probe) and as the "what is missing" example. Add L69 and L42 as D1 *readings*, not as fast-track anchors (you have not done them) | Evidence: L30 records no query, chunk ids or answer |
| [02](../../02_RAG_MASTER_LEARNING_PLAN.md) M3 card, "VAI L27/L29/L44" | Library tour only | Keep L44's judge prompts as reading. Treat L27 and L29 as counter-examples | Evidence: constant 0.8 (L27), word overlap (L29) |
| [08](../../08_GAP_ANALYSIS_AND_DECISIONS.md) gap row "Conversational / multi-turn RAG … only prior VAI L26" | Not scheduled as its own topic (noted for K1). D-21 and 02 §5 already use L26 as an O1/Q1 probe | Also list L26 as the Q1 reading for the condense-question step | Evidence: `backend/app/services/context_expander.py:31-71` |

- **No VAI coverage** (the book and our lessons only): P6, C7, M2 (beyond L44's judged recall), M5, I4, I5, I6, R5, Q2, X1, A4, S1, S2, S3.
- **Counter-examples only:** V4, X2, I-CMP.
- **Weak only:** I2 (L21).

---

## The honest limit

This guide reads code; nothing was run. Behaviour that depends on a library version or on Gemini is marked UNVERIFIED in the lesson sections. That includes whether an old model id is still served, and how Chroma reacts to a dimension mismatch. The `file:line` citations match the folder as it was on 2026-10-17.

How the checking was done, and what it found:

```
Readers:  8, one per block of lessons
Pass A (fact-check):     1,419 cited claims re-opened at the source line
                         1,182 held as written (83%) · 203 corrected · 34 left UNVERIFIED · 0 removed
Pass B (completeness):   every backend file re-read with a different lens
                         (control flow, missed issues, concept mapping, fit to your stack)
                         424 logged checks and changes, including the missed issues added
                         and 3 concept mappings removed
Index check:             3 critics (consistency, completeness, style); all findings applied
Copying:                 no run of 12+ words shared with the course, except 2 dependency-version lists
```

**What this means:** the lesson sections are as reliable as reading code allows. The weak spots are the UNVERIFIED items: runtime behaviour that you would see only by running the code.

---

## Why nothing here is copied

- The course folder has no licence file, so treat it as all rights reserved.
- This guide paraphrases. It names functions, settings and model ids. It quotes only short phrases (README claims, UI labels, demo questions), where they are needed to show a mismatch.
- The course folder stays outside this git repository: `rag_learning/` is the git root, and the course lives in `C:\Yash\New-Work\RAG\`.

---

## Decisions for you

1. **Copy the course into `Book RAG\upstream\vertical-ai-agents\`?** (copy / no) It would put every cited file inside your one folder: about 1.6 MB, 1,265 files, with no `node_modules`, venvs or logs. The guide works either way. My first try was blocked by the permission check, so if you say "copy", approve the prompt when it appears.
2. **Apply the four plan corrections above to 02 and 08?** (yes / no)
3. **Point the phase research brief (`study/research/RESEARCH_PROMPT.md`) at this map,** so each phase session picks up its VAI pointers? (yes / no)

## Next

1. **Now (Phases 1–2):** read L19, then L20, each after the book pages and the study reading file. Do each one's "Try this". **Why first:** they match your v0 baseline most closely.
2. **Later (Phase 5):** L22 for reranking (R3), then L23 and L37 for fusion (R1). **Why later:** they improve retrieval, and you can measure that only after Phase 3.
3. **When any other phase starts:** open its table in the topic map, and read the lessons in the order given.

Each of these lessons has a 20–30 minute "Try this" that runs locally:
- L19: plain Python.
- L20: MiniLM plus `chromadb`.
- L22: the local MiniLM cross-encoder.
- L23: BM25 plus MiniLM.
