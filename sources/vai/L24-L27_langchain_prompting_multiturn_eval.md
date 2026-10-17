# VAI lessons 24–27: LangChain RAG, grounding prompts, multi-turn RAG, RAG evaluation

[← Guide index](README.md) · Course folder: `C:\Yash\New-Work\RAG\vertical-ai-agents-main\` · Checked 2026-10-17 · Log: [verification/L24-L27_langchain_prompting_multiturn_eval_log.md](verification/L24-L27_langchain_prompting_multiturn_eval_log.md)

**What this is:** the guide to VAI lessons 24–27: a LangChain RAG chain, grounding prompts, multi-turn RAG and RAGAS evaluation.
**What this is not:** the course code, or a run of it. Nothing in the course was run or copied.

**How to read this file:**
- A `file:line` is relative to the project folder named in the lesson heading.
- **UNVERIFIED** marks behaviour that depends on a library version or on Gemini.
- **(counter)** or † means the lesson names a technique without building it. Read it to learn what is missing.
- Tags: **[bug]** the code does the wrong thing · **[misleading]** a label, message or number claims more than the code does · **[shallow]** it works, but is too thin for your project · **[ok-for-demo]** fine for a demo, not for real use · **[LLMOps]** material for your LLMOps notebooks · **[Interview]** worth practising for interviews.
- "I" means the reviewer who checked the code. Each lesson was checked by a reader, a fact-check pass and a completeness pass; the log has every verdict.

**Notes for this block:**
- None of these four lessons has a `setup.sh`; each has only the generated project folder.
- Numbers marked "computed from the formula" come from a scratch re-implementation of one scoring rule, not from running the app.

---

## L24 · Modular RAG with LangChain (LCEL)  (`lesson24/l24-langchain-rag/`)

**What the code teaches, in one line:** How a 4-stage RAG pipeline (retrieve → format → prompt → LLM → string) looks when you write it as one LangChain Expression Language (LCEL) chain, plus a custom `BaseRetriever` subclass and Prometheus timing counters.
**What it is not:** It has no document loaders, no text splitters (no chunking at all), and no keyword or BM25 search. It has no LangSmith tracing. By default it has no real embeddings and no LLM: the out-of-the-box path uses SHA-256 "hash vectors" and a canned "offline" answer.
**Relevance to your RAG study:** Medium. Concepts: C4, C5, C6 (the pipeline is real; the trace is hand-made), R4 (library MMR call), D1; R1 (counter-example: called "hybrid", but there is no sparse retriever); R3 (counter-example: an `enable_reranking` flag with no reranker anywhere, `main.py:50`). Tags: [LLMOps] (latency histograms only), [Interview].
**Stack:** FastAPI. `langchain==0.3.7`, `langchain-google-genai==2.0.5`, `langchain-chroma==0.1.4`, `chromadb==0.5.23` (`backend/requirements.txt:3-6`). LLM: Gemini `gemini-2.0-flash-exp`, temperature 0.3, max 1024 output tokens (`backend/main.py:116-121`). This is an experimental id, probably retired (UNVERIFIED). Embeddings: Gemini `models/embedding-001` (`main.py:83-86`), **but only when `USE_GEMINI` is set**; otherwise a 32-dim SHA-256 hash (`main.py:67-78, 82-88`). Vector store: persistent Chroma at `../data/chroma_db` (`main.py:91-94`). `sentence-transformers` is listed but never imported (`requirements.txt:7`). The React UI shows a query box, a hybrid/vector selector, a Top-K box, the answer, timings, a 2-row "chain trace" and source cards with a % score.
**Swap to your stack:** Moderate. `ChatGroq` and Cohere embeddings drop into `main.py:83-86` and `116-121`. But you would also have to fix the `USE_GEMINI` gate, the legacy imports and the Chroma path. A plain-Python rewrite is about 50 lines, and that is the order your plan wants anyway.
**Your earlier copy (`prior_work/VAI/lesson24`):** identical to the original (only `.gitignore` and `App.css` are missing).
**Path shorthand below:** `main.py` = `backend/main.py`; `QueryInterface.js` = `frontend/src/components/QueryInterface.js`; `init-data.sh`, `test.sh` and `build.sh` are in `scripts/`.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `README.md` | Claims: hybrid retrieval, LCEL, "production ready", Gemini | 22-35 |
| 2 | `backend/requirements.txt` | Versions you are reading against | 3-6 |
| 3 | `backend/main.py` | Provider switch, hash "embeddings", Chroma, LLM | 63-121 |
| 4 | `backend/main.py` | `HybridChromaRetriever` (vector plus MMR, interleaved) | 123-185 |
| 5 | `backend/main.py` | Prompt, `format_docs`, `offline_answer`, LCEL `build_chain` | 187-240 |
| 6 | `backend/main.py` | `/api/query` request flow, fake scores, hand-made trace | 286-342 |
| 7 | `docker-compose.yml`, `Dockerfile` | Env vars and paths (see bugs) | compose 10-12; Dockerfile 24, 34 |
| 8 | `scripts/init-data.sh`, `scripts/test.sh` | 3 short sample docs (2–3 sentences each); curl smoke test | all |
| 9 | `frontend/src/components/QueryInterface.js` (skim) | Top-K box; sends `top_k`; shows score as % | 20-24, 78-87, 148 |

### How it works, step by step
1. **Startup: provider choice.** `USE_GEMINI` must be "1/true/yes" and the key must be real (`main.py:63-64, 82`). If not, `embeddings = SimpleHashEmbeddings()`. This class turns the text's SHA-256 digest into 32 numbers between 0 and 1 (`main.py:70-72`). These vectors carry **no meaning**: changing one character gives an unrelated vector. The LLM is created only under the same condition (`main.py:114-121`); otherwise `llm = None`.
2. **Store.** A persistent Chroma client is created (`main.py:91-94`). A bare `except` creates the collection if `get_collection` fails (`main.py:96-104`), and LangChain's `Chroma` wrapper is built around it (`main.py:107-111`).
3. **Ingest.** `POST /api/documents` adds the whole text as **one** vector via `add_texts` (`main.py:273-284`). There is no loader and no splitter. No ids are passed (`main.py:277-280`), so every call gets fresh random ids (see the bugs below).
4. **Retrievers.** `HybridChromaRetriever` runs `similarity_search(k)`, then `max_marginal_relevance_search(k, fetch_k=20)` on the **same vector index** (`main.py:137-151`). It interleaves the two lists, dedups by the first 100 characters of the text, and cuts to k (`main.py:153-177`). k is fixed at 5 (`main.py:180-185`). The "vector" retriever is plain `as_retriever(k=5)` (`main.py:185`). Settings you do not see: the collection is created with no distance setting (`main.py:100-103`), so `similarity_search` ranks by Chroma's default `l2` distance (library default; see L26). `lambda_mult` is not passed, so MMR uses the library default of 0.5 (seen in `langchain_community`'s Chroma, `vectorstores/chroma.py:622`; the pinned `langchain_chroma` 0.1.4 is not installed here, so UNVERIFIED for it).
5. **LCEL chain.** The chain runs in parallel: {context = retriever then `format_docs`, question = passthrough}, then the prompt, then the LLM, then a string parser (`main.py:227-235`). `format_docs` labels each chunk `[Source i]` (`main.py:202-207`). The prompt says, in short: answer from the context; if the context lacks the information, say so (`main.py:188-197`). It does **not** ask for citations.
6. **Query.** `/api/query` picks a chain from `mode` (`main.py:294-299`). It calls the retriever once to get `docs` (`main.py:303`). If an LLM is configured, it then calls `chain.invoke`, which **retrieves again** inside the chain (`main.py:308-309`). With no LLM the chain is `None` (`main.py:225-226`), so retrieval runs only once and it returns `offline_answer`: the first 200 characters of up to 3 docs (`main.py:209-220, 311`).
7. **Response decoration.** Each source gets `relevance_score = 0.9 - 0.1·rank` (`main.py:321`). The "trace" is two hand-made rows, and "tokens" is the word count (`main.py:327-330`). Prometheus counters and histograms are real (`main.py:29-32, 175, 289, 292, 314`).

**LangChain pieces vs plain Python**
| Stage | LangChain piece used | Plain-Python equivalent | What LCEL adds / hides |
|---|---|---|---|
| Load / split | none | `pymupdf` + your chunker | n/a |
| Store | `langchain_chroma.Chroma` (`main.py:107`) | NumPy matrix or Chroma client | a wrapper only |
| Retrieve | `BaseRetriever` subclass (`main.py:124`), `as_retriever` (`185`) | `search(q, k) -> list[chunk]` | with an LLM configured, the same retrieval runs twice per query here (`303`, `309`) |
| Prompt | `ChatPromptTemplate.from_template` (`199`) | an f-string | nothing |
| Chain | `RunnableParallel`/`RunnablePassthrough`/`StrOutputParser` (`227-235`) | 4 function calls | `.invoke/.batch/.stream`, callback hooks; hides intermediate values |
| Trace | `BaseCallbackHandler` subclass (`243-266`) | a dict per stage | **defined but never attached** |

### README vs code
- README says "Hybrid Retrieval: combines vector and keyword search" (`README.md:24`). The code combines vector search with MMR over the same embeddings; no keyword search exists (`main.py:137-151`). The comment "Keyword search via MMR" (`main.py:143`) is wrong.
- README says "Swap retrievers, prompts, and LLMs without code changes" (`README.md:26`). The code has two hard-coded chains; the "keyword" mode in the request model (`main.py:48`) silently falls back to vector (`main.py:298`).
- README says "Gemini integration" and "Embeddings: Google Embedding-001" (`README.md:28, 34-35`). The code uses them only if `USE_GEMINI` is set, and `docker-compose.yml:10-12` passes only `GEMINI_API_KEY`. So the documented Docker run uses hash vectors and the offline answer.
- README says "Production ready: metrics, logging, observability" (`README.md:27`). The Prometheus metrics are real. The `TracingCallback` is never used, and `chain_trace` is fabricated from two timers (`main.py:243-266, 327-330`).

### Where it is thin or wrong
- [misleading] The default "embeddings" are a hash (`main.py:67-78, 88`). Retrieval order is arbitrary. The demo still looks fine, because the corpus is 3–4 short documents (`scripts/init-data.sh:4-23` plus one from `scripts/test.sh:15-20`) and k=5 returns everything (`main.py:182, 185`).
- [misleading] `relevance_score = 0.9 - (i * 0.1)` (`main.py:321`) is shown as "Score: 90.0%" in the UI (`QueryInterface.js:148`). It is a rank label, not a score.
- [bug] `top_k` and `enable_reranking` from the request are ignored (`main.py:49-50` vs `182, 185`). The UI's Top-K box (`QueryInterface.js:79-86`, sent at line 23) does nothing. Even the smoke test asks for `top_k: 3` and gets up to 5 back (`test.sh:31`). There is no reranker anywhere in the backend (grep), so the flag names a technique (R3) that does not exist.
- [bug] Re-ingesting duplicates documents. `add_texts` is called without ids on a **persistent** store (`main.py:91-94, 277-280`), and the wrapper then makes a new random id per text (library behaviour, seen in `langchain_community`'s Chroma `add_texts`, `vectorstores/chroma.py:273`; pinned `langchain_chroma` not installed). So every run of `init-data.sh` or `test.sh` stores the same texts again. Vector mode then returns duplicates; hybrid mode hides them only through the 100-character prefix dedup (`main.py:162-165`).
- [bug] No index version. The same persistent collection `l24_documents` is reused whichever embedder is active (`main.py:82-88, 96-98`), and nothing records which embedder built it. Documents added in hash mode keep 32-number vectors. If you later set `USE_GEMINI`, queries are embedded by Gemini, which does not produce 32-number vectors, so expect a dimension error or meaningless matches (UNVERIFIED: not run). This is the D3 "index versioning" problem in miniature.
- [bug] When an LLM is configured, retrieval runs twice per query (`main.py:303, 309`). `generation_time` then includes the second retrieval, and the retrieval histogram is observed twice per hybrid query (`main.py:175`). In offline mode the chain is `None`, so this does not happen (`main.py:225-226, 308-311`).
- [shallow] The "fusion" is interleave-and-dedup by a 100-character text prefix (`main.py:157-172`). It ignores scores and is not RRF. If two different chunks share the same first 100 characters, the second one is silently dropped.
- [bug] `Dockerfile:24` copies `data/`, but no `data/` folder exists in the lesson, and `scripts/build.sh:5` builds without creating it. Docker refuses to copy a missing path, so the build fails. The Chroma path `../data/chroma_db` (`main.py:92`) is relative to the working directory. With `Dockerfile:34` (run from `/app`) it resolves to `/data/chroma_db`, outside the mounted `./data:/app/data` volume (`docker-compose.yml:9`), so the index is not persisted. Run locally from the project root (`README.md:18`), it writes outside the project.
- [shallow] Legacy import paths `langchain.schema...` and `langchain.callbacks...` (`main.py:10-14`), plus the deprecated `get_relevant_documents` (`main.py:303`). Modern code uses `langchain_core` and `.invoke`.
- [ok-for-demo] Bare `except:` around `get_collection` (`main.py:99`) and around MMR (`main.py:150`) hides real errors.

### Tests and data
- There is no pytest. `scripts/test.sh` is a curl smoke test: health, add one doc, one query, stats. It always prints "All tests passed!" (`test.sh:41`), whatever the responses were.
- `scripts/init-data.sh:4-23` adds 3 short docs of 2–3 sentences each (about RAG, LangChain and hybrid search). They are too few to show any retrieval difference, so they have no practice value.

### What to take for your project
- **Reading value (C5/C6, later LangChain phase):** The LCEL shape at `main.py:227-235` is the cleanest 9-line picture of "RAG as a composable chain" in this block. Only after your plain-Python `ragkit` pipeline works, rebuild it in the same shape with `ChatGroq` (model from `GROQ_MODEL_ID`, `reasoning_effort="low"`, enough `max_tokens`; the field exists in `langchain-groq` 1.1.2, seen in a local install at `langchain_groq/chat_models.py:377`) and Cohere `embed-v4.0`. Route both through your record/replay cache so the chain reruns without credits. Retrieve **once** and pass the same docs to the prompt and to the response. Then diff the chain's output against your plain-Python trace. If you switch on LangSmith tracing, trace only your project PDFs, never book text.
- **P4/C3 interface:** Keep the split between `embed_documents` and `embed_query` (`main.py:74-78`). Cohere `embed-v4.0` needs it, because chunks and queries are embedded with different `input_type` values (`search_document` vs `search_query`). Put MiniLM behind the same two methods.
- **C3/D3 checks L24 lacks:** give every chunk a stable id (for example, document id + page + chunk number) and pass it at ingest. Test that ingesting the same PDF twice leaves the count unchanged. Store the embedder model id and vector dimension with the index, and refuse to query an index built by a different embedder.
- **D1/D2 idea:** Keep separate retrieval and generation timers, as the histograms at `main.py:30-32` do, in your provenance trace. Time each stage **once**.
- **A useful test double:** A deterministic hash embedder (the idea at `main.py:70-72`) is handy for offline unit tests of plumbing (store/load, ids, k). Name it as a fake, and never evaluate retrieval with it.
- **Anti-patterns to avoid:** rank-based fake scores, dedup by text prefix (use stable chunk ids), calling vector+MMR "hybrid" (R1 means sparse+dense, fused for example with RRF), flags for techniques that do not exist, and retrieving twice.

### Try this
- (20 min) In your own notebook, write a 3-line SHA-256-to-vector function in your own words. Compute cosine similarity for "What is LangChain?" against one sentence about LangChain and one unrelated sentence. Then do the same with MiniLM. **Look for:** the hash scores are arbitrary, and every pair scores fairly high, because all 32 numbers are positive (`main.py:72`). MiniLM should rank the LangChain sentence first (expected, not run). Then answer: why did L24's demo still "work"? (Because k=5 is at least the corpus size, every document is returned whatever the scores are; `main.py:182`.)

### Interview angle
- **Q:** "What does LangChain's LCEL give you over a plain-Python RAG pipeline, and what can it hide?"
  **A:** LCEL gives one Runnable interface (invoke, batch, stream, async), callback hooks for tracing, and easy component swaps. It can also hide steps. In this lesson the chain re-runs retrieval inside itself, so the sources you show come from a separate call, not from what the chain actually passed to the model. They usually match, but nothing guarantees it, and the "generation" time silently includes a second retrieval. The fix is to retrieve once and carry the docs through the chain next to the answer, so the response shows exactly what the model saw. Learn the mechanism in plain Python first, then adopt LCEL where tracing and streaming pay off.

---

## L25 · Advanced prompting for grounded RAG  (`lesson25/l25-advanced-prompting-rag/`)

**What the code teaches, in one line:** Three system prompts with different grounding strictness (strict, moderate, creative), a regex citation checker, a fixed abstention sentence, and an "adversarial" mode that feeds deliberately irrelevant context to see whether the model refuses.
**What it is not:** It is not an evaluation of prompts. There is no question set, no comparison of the three templates, and no faithfulness metric. It has no chain-of-thought, no few-shot examples and no structured (JSON) output. "Grounding confidence" never looks at the answer.
**Relevance to your RAG study:** High (the ideas). The code is thin. Concepts: P7, C5, V1 (citation range check only), V3 (fixed refusal sentence, adversarial context); V2 (counter-example: the "grounding" check is question–context word overlap, and nothing checks the answer against the context); V4 (counter-example: "hallucinated" is a substring test). Tag: [Interview].
**Stack:** FastAPI. `langchain==0.3.7` `RetrievalQA` (a legacy chain), `langchain-community==0.3.7` `Chroma` (in memory), `chromadb==0.5.18` (`backend/requirements.txt:4-7`). LLM: Gemini, default `gemini-2.0-flash` via the `GEMINI_MODEL` env var, temperature 0.1 (`backend/app.py:40-45`). Embeddings: Gemini `models/embedding-001` (`app.py:34-37`); without a key or on error it falls back to `sentence-transformers/all-MiniLM-L6-v2` (`app.py:207, 224-241`). The UI shows a question box, a domain selector, an "Adversarial Test Mode" checkbox, a grounding badge, a "Grounding Confidence" %, a "Citations Found" count, citation cards and the validation JSON (`frontend/src/App.jsx:115-136, 185-236`).
**Swap to your stack:** Easy. Only the `llm` and `embeddings` constructors (`app.py:34-45`) and the unused `genai.configure` call (`app.py:29-31`) are provider-specific, and the MiniLM fallback already matches yours. With `gpt-oss-20b`, set `reasoning_effort="low"` and enough `max_tokens`, and check that the substring tests still see the refusal sentence.
**Your earlier copy:** same backend; `App.jsx` and `.env.example` (and `.gitignore`, `App.css`) are missing from the copy, so its React UI cannot be built.
**Path shorthand below:** `app.py` = `backend/app.py`; `App.jsx` = `frontend/src/App.jsx`; `test.sh` is at the project root. `.env.example` holds only a placeholder, not a real key.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `README.md` | Feature claims | 14-37 |
| 2 | `backend/app.py` | The three prompt templates | 47-105 |
| 3 | `backend/app.py` | `GroundingValidator`, `CitationExtractor`, `AdversarialTester` | 107-174 |
| 4 | `backend/app.py` | KB of 10 sentences, embeddings fallback, 3 `RetrievalQA` chains (k=3) | 204-252 |
| 5 | `backend/app.py` | `/query`: demo path, adversarial path, normal path, state rules | 308-431 |
| 6 | `tests/test_grounding.py` | Unit tests of the three helpers | 8-56 |
| 7 | `test.sh` | Two live requests that print states | 20-47 |
| 8 | `frontend/src/App.jsx` (skim) | What "confidence" and "citations" show | 191-208 |

### How it works, step by step
1. **Startup.** It builds 10 one-sentence docs with metadata `source`/`id` (`app.py:210-222`) and an in-memory Chroma collection `l25_knowledge` (`app.py:228-233`). If an LLM exists, it builds one `RetrievalQA` "stuff" chain per template with k=3 (`app.py:244-252`).
2. **Request.** `POST /query` takes `{question, domain, test_mode}` (`app.py:177-180`).
3. **No key → demo path.** The demo path does retrieval only and lists the top 3 docs as the "answer" (`app.py:322-342`). It still runs the word-overlap check and labels the result "grounded" when the overlap is ≥ 0.3, otherwise "partial" (`app.py:326, 333-334`), although no LLM ran. In test mode it returns a **canned** refusal sentence with state "rejected" (`app.py:317-321`).
4. **Adversarial path (key set).** It picks one of 5 canned off-topic strings by substring match on the question (`app.py:159-174`), formats it into the chosen template and calls the LLM (`app.py:356-361`). State = "rejected" if the answer contains "do not contain", else "hallucinated" (`app.py:364, 367`).
5. **Normal path.** `chain.invoke({"query": ...})` (`app.py:371`) retrieves the top 3, stuffs them into `{context}` and calls Gemini at temperature 0.1. The "stuff" chain joins the raw `page_content` with blank lines. That is LangChain's default document format: the default document prompt is just the page content, and the separator is a blank line (library behaviour, not in this repo; confirmed in the later `langchain_classic` 1.0.1 source, `chains/combine_documents/base.py:21-23`; the pinned 0.3.7 is not installed here). So **the context carries no `[Source N]` labels** even though the template demands them.
6. **Post-hoc "grounding check."** It takes the question words (lower-cased, punctuation stripped) that also occur in the retrieved text, divided by the number of question words; threshold 0.3 (`app.py:112-127, 388`). Stopwords count.
7. **Citations.** A regex finds `[Source N]`, and the check is only that 1 ≤ N ≤ number of sources (`app.py:134-152, 391-392`).
8. **State rules** (`app.py:395-406`): overlap < 0.3 → "rejected" (confidence 0). Else, if the answer contains "do not contain" or "insufficient" → "rejected". Else, if it has citations and they are all in range → "grounded" (confidence = overlap). Else → "partial" (confidence = overlap × 0.5). **The LLM answer is returned in every case**, even when the state is "rejected" (`app.py:417-419`).
9. **Citation cards.** One card is built for **every retrieved doc**, cited or not, with `relevance_score` read from metadata that never has it, so it is always 0.0 (`app.py:409-415`, metadata at `222`). The card's `source_id` is the rank (1–3), not the stored `doc_N` id (`app.py:410-412`).
10. **Error paths (a branch of steps 4–5).** If the LLM call throws with "429", "quota" or "rate limit" in the message, you get the same retrieval-only answer as the demo path, again labelled by word overlap (`app.py:372-378, 282-306`). Any other error returns HTTP 200 with the error text as the answer and state **"rejected"** (`app.py:379-381`; default state at `275`).

**Prompt techniques present (paraphrased):**
- *Strict* (`app.py:51-66`): answer only from the context, cite every claim as `[Source N]`, give an exact refusal sentence when the information is missing, never use training knowledge, make no inferences.
- *Moderate* (`app.py:71-85`): prioritise the context; general knowledge is allowed but must be marked.
- *Creative* (`app.py:90-103`): use the context as a foundation and expand.
- Also present: low temperature (`app.py:44`). Absent: CoT, few-shot, JSON/structured output, quote-first extraction, numbered context blocks.

### README vs code
- README says "LLM: Gemini 1.5 Flash" (`README.md:19`). The code defaults to `gemini-2.0-flash`, and its own comment says 1.5 returns 404 (`app.py:39-40`).
- README says "Citation extraction and validation" (`README.md:25`). The code only checks that the number is in range (`app.py:141-152`), never that the cited text supports the claim.
- README says "Grounding confidence scoring" (`README.md:26`). The code measures keyword overlap between the **question** and the retrieved context (`app.py:112-127`). The answer is never inspected.
- The class docstring says "Validates context relevance before generation" (`app.py:109`). The code calls it after the LLM has answered (`app.py:371, 388`), so it is a label, not an abstention gate.
- README says the adversarial mode verifies refusal (`README.md:37`). Without a key the refusal is canned (`app.py:317-321`), so the "test" always passes.
- README says "Built on L24's modular RAG pipeline" (`README.md:39`). No code is shared: L24 uses LCEL with persistent Chroma; L25 uses `RetrievalQA` with in-memory Chroma.

### Where it is thin or wrong
- [bug] The context is unlabelled, yet the prompt asks for `[Source N]` (`app.py:58, 66` vs the default stuff format). Numbering depends on the model guessing the order, so the "valid citation" check is weakly anchored.
- [misleading] "Grounding Confidence" (`App.jsx:191-193`) is word overlap with stopwords included. "What is RAG?" against the RAG sentence (`app.py:212`) scores 1/3 (only "rag" overlaps; computed from the formula). In the app the check runs against all 3 retrieved sentences joined (`app.py:387-388`), so a well-grounded answer shows **33.3%** unless another retrieved sentence happens to contain "what" or "is" (two KB sentences do, `app.py:214, 216`; which 3 are retrieved is UNVERIFIED). The unit test passes with exactly this borderline value (`tests/test_grounding.py:13-18`).
- [misleading] "Citations Found" counts retrieved documents, not citations in the answer (`app.py:409-415`; `App.jsx:207-208`).
- [misleading] Citation `relevance_score` is always 0.0 on the normal path (`app.py:414`) and a hard-coded 0.5 in demo and fallback (`app.py:294, 330`).
- [shallow] Abstention is detected by substring (`app.py:364, 398`). A refusal worded differently is missed. "insufficient" also triggers on moderate-mode answers that then go on to add general knowledge.
- [misleading] For the moderate and creative templates, adversarial mode labels any non-refusal "hallucinated" (`app.py:364`), even though those templates explicitly allow general knowledge (`app.py:79-81, 97`).
- [bug] The keyword "api" matches inside "capital" and "rapid" (`app.py:164, 170-171`). With a key set, `test.sh:23` ("capital of France") therefore gets the REST-API context. (Without a key the canned refusal is returned before this code runs, `app.py:317-321`.) Harmless, but it shows the matching is naive.
- [misleading] `test.sh:27` checks for HTTP 503, which the backend never returns (`app.py:310`). In demo mode it prints "Passed: True" from the canned refusal, and "All tests passed" is unconditional (`test.sh:47`).
- [shallow] Deprecated APIs throughout: `RetrievalQA`, community `Chroma`, community `HuggingFaceEmbeddings`, `@app.on_event` (`app.py:12-13, 207, 254`). `google.generativeai` is configured but otherwise unused (`app.py:15, 31`).
- [misleading] The demo and quota paths call a list of retrieved sentences "grounded" (`app.py:296, 334`). With no LLM at all, "What is RAG?" gets at least 1/3 overlap from the RAG sentence (`app.py:212`; computed from the formula, assuming that sentence is retrieved, UNVERIFIED), which is ≥ 0.3. So the UI shows a "grounded" state for an answer no model wrote.
- [misleading] An API error is labelled "rejected", the same state as a correct refusal (`app.py:275, 379-381`). If you counted refusals from these states, errors would inflate the abstention rate.
- [shallow] Provenance is lost. The citation card's `source_id` is the rank, and the stored `source`/`id` metadata (`app.py:222`) is never returned (`app.py:410-415`). A `[Source 2]` in the answer can only be traced back to a KB sentence by its position.
- [misleading] The UI labels the strict template "Strict (Legal/Medical)" with the hint "100% grounding required, citations mandatory" (`App.jsx:117, 122`). A prompt cannot guarantee that, and nothing enforces it: an answer with no citations is only marked "partial" and is still returned (`app.py:404-406, 417-419`).
- [shallow] `test.sh` has no `set -e`, so a failing pytest run (`test.sh:10`) does not stop the script. The HTTP part still runs and ends with the unconditional "All tests passed" (`test.sh:47`).

### Tests and data
- `tests/test_grounding.py` checks only the three helper functions: overlap above or below 0.3 on two hand-picked pairs (`8-25`), the citation regex and range check (`27-44`), and canned-context lookup (`46-56`). Nothing tests a prompt or an LLM output.
- Data: 10 one-sentence facts hard-coded in `app.py:210-221`. They are too small for practice.

### What to take for your project
- **C5/V3 prompt (re-implement):** Take the *strict* template's rules, but **label each context block with the same id you ask the model to cite**, for example `[c17]`. Use one fixed refusal sentence, and return a structured field such as `answerable: true/false` rather than relying on a substring.
- **V1 cascade (code-based evaluator):** The citation regex and range check (`app.py:134-152`) is a fine cheap first tier. Add "every sentence has ≥ 1 citation". Then a judge tier checks whether the cited chunk supports the sentence (V1/V4).
- **V3 eval idea:** The "adversarial context" idea is good; the check is not. Build a small set of answerable and unanswerable questions plus context-swap cases, run each template, and report the abstention rate and false-refusal rate. That is the evaluation L25 never does. Run every template call through your record/replay cache, so the comparison reruns without credits. With `gpt-oss-20b`, use `reasoning_effort="low"` and enough `max_tokens`, so the answer is not cut off before the refusal sentence.
- **Separate errors from refusals (V3, D1):** give your trace distinct states such as `answered`, `abstained` and `error`. An API failure must never count as a correct refusal, as it does at `app.py:379-381`.
- **Keep provenance (C5/C6):** return the stored chunk id (and page) with every citation, not the rank. L25 drops it (`app.py:410-415`).
- **Judge tier:** per your decision D-10, the "does the cited chunk support this sentence?" judge is the Cohere judge, run once at the end on stored traces and checked against Codex labels.
- **Skip:** the keyword-overlap "confidence".

### Try this
- (15 min) Re-implement the overlap rule in 5 lines, in your own words. Score "What is the price of ChromaDB?" against the single KB sentence about ChromaDB (`app.py:216`). **Look for:** {is, chromadb} overlap gives 2/6 = 0.33 (computed from the formula), which is ≥ 0.3, so the rule says "relevant", although the KB has no price anywhere and cannot answer the question. Then write down one check that **would** catch this (for example, the judge asks "does the context state a price?").

### Interview angle
- **Q:** "How would you know whether your grounding prompt actually reduces hallucinations?"
  **A:** Build a labelled set of answerable, unanswerable and swapped-context questions. Run each prompt version, and measure faithfulness (claims supported by the cited chunks) plus the abstention and false-refusal rates. Use a judge you have checked against human labels. Keyword overlap and substring checks like L25's cannot tell a grounded answer from a fluent made-up one.

---

## L26 · Multi-turn RAG: memory, ambiguity detection, query expansion  (`lesson26/l26-multiturn-rag/`)

**What the code teaches, in one line:** A conversational RAG loop. Session memory goes in Redis. A heuristic score decides "ask a clarifying question" vs "answer". An LLM rewrites the follow-up into a standalone question (the "condense question" pattern), and only that rewrite is used for retrieval.
**What it is not:** It does not use LangChain, although `langchain` is in `requirements.txt:10-11`. Ambiguity is **not** judged against the conversation history. The "retrieval confidence" input is a constant. There is no "semantic" memory (the strategy name exists but falls back to sliding). Nothing evaluates whether the rewrites help retrieval.
**Relevance to your RAG study:** High. Concepts: Q1 (rewrite to a standalone question; the code calls it "expansion"), A1 (clarify-or-answer routing, by a heuristic score), X3 (history window), C5 (context labelled, but no citations requested). Redis is a session store with a TTL, not a cache of results, so this lesson does not teach D2. Tag: [Interview].
**Stack:** FastAPI. `google-generativeai==0.3.2`, `chromadb==0.4.22`, `sentence-transformers==2.3.1`, `redis==5.0.1`, `tiktoken` (`backend/requirements.txt:6-12`). LLM: Gemini `gemini-pro`, default temperature, in **three** places (`services/ambiguity_detector.py:31`, `services/context_expander.py:29`, `services/rag_service.py:46`). This is a legacy id that is probably no longer served (UNVERIFIED; your own copy changed all three to `gemini-2.0-flash`, which hints at this but does not prove it). Embeddings: local `all-MiniLM-L6-v2` (`rag_service.py:49`). Store: persistent Chroma `./data/chroma`, with Chroma's default `l2` space (no space is set, `rag_service.py:52-62`; Chroma's `l2` is squared Euclidean distance, library behaviour seen in chromadb 1.5.5 source, pinned 0.4.22 not installed here). The React UI shows a chat, session info (message count, tokens, state), an ambiguity % badge, clickable clarification questions and retrieved docs with "Score = 1 − distance" (`frontend/src/App.js:142-160, 216-253`).
**Swap to your stack:** Moderate. Replace the three direct Gemini call sites (`ambiguity_detector.py:109`, `context_expander.py:54`, `rag_service.py:219`) with one `llm()` helper that calls Groq. MiniLM is already your local fallback, and Redis can become a dict.
**Your earlier copy:** model id swapped to `gemini-2.0-flash` in all three services, `build-essential`/`g++` added to the Dockerfile, and `npm install` added to the compose frontend command.
**Path shorthand below:** `rag_service.py`, `ambiguity_detector.py`, `context_expander.py`, `conversation_memory.py` and `redis_service.py` are in `backend/app/services/`; `routes.py` = `backend/app/api/routes.py`; `main.py` = `backend/app/main.py`; `schemas.py` = `backend/app/models/schemas.py`; `App.js` = `frontend/src/App.js`; `test.sh` = `scripts/test.sh`.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `README.md` | Claims (memory strategies, retrieval confidence, env vars) | 5-12, 80-101 |
| 2 | `backend/app/api/routes.py` | One turn: load memory → add query → RAG → save | 18-75 |
| 3 | `backend/app/services/rag_service.py` | Orchestration: detect → clarify or expand → retrieve → generate | 116-241 |
| 4 | `backend/app/services/ambiguity_detector.py` | 5 regexes, weighted score, clarification prompt | 25-127 |
| 5 | `backend/app/services/context_expander.py` | Standalone-question rewrite prompt | 31-71 |
| 6 | `backend/app/services/conversation_memory.py` | Sliding or token window, serialisation | 11-115 |
| 7 | `backend/app/services/redis_service.py` | Session storage, TTL, the "fallback" | 17-87 |
| 8 | `backend/tests/test_conversation_memory.py`, `scripts/test.sh` | Memory tests; 4-turn script | all |

### How it works, step by step
1. **Startup.** It connects to Redis (`main.py:35`; `redis_service.py:17-31`) and loads Gemini, MiniLM and Chroma. On first run it seeds 5 short SaaS docs about pricing, support, auth and rate limits (`rag_service.py:40-110`).
2. **Turn begins.** `POST /api/query {session_id, query}` (`schemas.py:10-13`). Memory is loaded from Redis key `conversation:<id>`, or a new `ConversationMemory()` is created with defaults: sliding window, 10 messages (`routes.py:23-36`; `conversation_memory.py:11-21`).
3. **The query is added to memory first** (`routes.py:39`). The history string is then the last 5 messages as "role: content" lines (`rag_service.py:128`; `conversation_memory.py:75-81`), so it always ends with the current query.
4. **Ambiguity score** (`ambiguity_detector.py:52-68`): 0.5 × linguistic + 0.3 × (1 − retrieval_confidence) + 0.2 × short-query flag (< 3 words). Ambiguous if the score is > 0.4 (`AMBIGUITY_THRESHOLD`, line 29).
   - *Linguistic* = the share of 5 regexes that match (`ambiguity_detector.py:33-39, 79-88`). The patterns are: a pronoun or demonstrative **not followed by another word**; a query **starting** with more / tell me more / what about / and / also; he/she/they/them anywhere; a bare yes/no/maybe/sure/okay; the other / another / previous / before.
   - *retrieval_confidence* is always passed as **0.5** (`rag_service.py:131-133`), so this term is a constant 0.15. Detection runs before any retrieval.
   - The `conversation_context` argument is **never used** inside `detect` (`ambiguity_detector.py:41-77`).
5. **If ambiguous:** Gemini is asked for 2–3 clarifying questions as a numbered list, which a regex parses. If the call fails, 3 canned generic questions come back (`ambiguity_detector.py:90-127`). If the call succeeds but the reply has no numbered lines, the list is simply empty and you see only "Please clarify your question:" (`ambiguity_detector.py:113-119`; `routes.py:61`). No retrieval happens (`rag_service.py:136-140`). The route sets state "CLARIFYING" and does **not** store the assistant's clarification in memory (`routes.py:46-51`).
6. **Else rewrite (Q1).** The expander prompt, paraphrased: "expand this query into a standalone, specific question using the conversation; preserve intent" (`context_expander.py:44-51`). The output has all quote characters removed (including apostrophes) and any trailing period dropped (`context_expander.py:57-60`). On error it falls back to the raw query (`context_expander.py:65-71`).
7. **Retrieve** with the *rewritten* query: MiniLM, top_k=3 (`rag_service.py:120, 146, 158-182`).
8. **Generate** with the *original* query, the history and the docs labelled `[Document i]`. The instructions, paraphrased: use only the retrieved context, say so if it is missing, refer to specific details, keep continuity with earlier turns (`rag_service.py:193-216`). They never ask the model to cite `[Document i]` (`rag_service.py:209-214`). The `expanded_query` argument is unused in the prompt (`rag_service.py:187, 207`). On error it returns doc snippets or an apology as a normal reply (`rag_service.py:224-241`).
9. **Save.** The reply is added to memory as the assistant turn, whatever it is, including the error fallbacks (`routes.py:49-51`). The memory goes to Redis with a 24 h TTL (`routes.py:53-57`; `redis_service.py:48-58`). The response also returns the retrieved docs with their stored ids `doc1`–`doc5` and raw distances (`rag_service.py:174-179`).

**What the score really flags (computed from the formula at `ambiguity_detector.py:52-68`, with the constant 0.5):**
| Query | Pattern hits | Score | Flagged? |
|---|---|---|---|
| "Tell me more about that" (the README's ambiguous example, `README.md:61`) | 2 | 0.35 | no |
| "How much does it cost?" (labelled ambiguous at `scripts/test.sh:43`) | 0 ("it" is followed by a word) | 0.15 | no |
| "What about it?" | 2 | 0.35 | no |
| "How much?" | 0 | 0.35 | no |
| "Yes" / "it?" | 1 | 0.45 | yes |
| "Android pricing?" (starts with "and") | 1 | 0.45 | yes (false alarm) |

In practice only queries under 3 words that hit at least one pattern, or longer queries that hit at least 3, are ever flagged.

### README vs code
- README says ambiguity detection uses "linguistic patterns + retrieval confidence scoring" (`README.md:8`). Retrieval confidence is the constant 0.5 (`rag_service.py:132`).
- README says the memory is "ConversationBufferMemory with multiple window strategies" (`README.md:49`). It is a custom class; the default is a sliding window, and "semantic" falls back to sliding (`conversation_memory.py:15, 33-40`).
- README lists `MAX_CONVERSATION_TURNS` and `MAX_CONVERSATION_TOKENS` as settings (`README.md:83-84`). They are never read; only `AMBIGUITY_THRESHOLD`, `SESSION_TTL_HOURS`, `REDIS_*`, `CHROMA_PERSIST_DIR` and `GEMINI_API_KEY` are (grep of `getenv`: `ambiguity_detector.py:29-30`, `redis_service.py:13-15`, `rag_service.py:45, 52`, `context_expander.py:28`).
- README claims "Relevance scoring integrated into ambiguity detection", "tracks retrieval confidence" and "provides test data for Ragas" (`README.md:93, 99, 101`). None of this exists in the code.
- `redis_service.py:29-31` says it "falls back to an in-memory dict". It sets `client = None`, and every save and get then silently does nothing (`redis_service.py:50, 62`). Without Redis there is **no memory**: every turn is turn 1.

### Where it is thin or wrong
- [bug] There is no memory without Redis (see above). Multi-turn silently becomes single-turn, and the `/health` "degraded" flag is the only clue (`main.py:73`).
- [misleading] Constant retrieval confidence, and detection ignores the history (`rag_service.py:132`; `ambiguity_detector.py:41-77`). "What about that?" scores the same on turn 1 (truly unclear) and on turn 5 (resolvable from history).
- [shallow] Wrong order. Clarify is decided **before** the rewrite (`rag_service.py:131-143`), so history never gets a chance to resolve "it". The better order is: rewrite first, then decide whether it is still unclear.
- [bug] The regex alternatives are anchored without a word boundary: "Android…" counts as "and…" (`ambiguity_detector.py:35`). The pronoun rule fires only when the pronoun is **not** followed by a space and another word (`ambiguity_detector.py:34`). In practice that means at the end of the query or just before punctuation: "it?" and "that, please" match, but "does it cost" does not (computed from the regex).
- [bug] The guard "no history → keep the query" can never fire, because the current query is already in memory (`routes.py:39` vs `context_expander.py:41-42`). That means an extra LLM call on every turn, including the first.
- [bug] `"API key" in error_msg.lower()` can never be true, because the lower-cased text has no capitals (`context_expander.py:69`; `rag_service.py:229`).
- [bug] Stripping apostrophes changes words ("what's" → "whats") (`context_expander.py:58`). This matters if you later add BM25.
- [shallow] Token pruning always keeps at least 2 messages, even above the budget (`conversation_memory.py:52`). It is not the default anyway (`routes.py:29`). The `cl100k_base` tokenizer only approximates Gemini's token counts (`conversation_memory.py:21`).
- [shallow] The "CLARIFYING" state is stored, but no backend logic reads it: the next turn loads the old state and overwrites it without looking (`routes.py:27, 46-49`). The UI only displays it in the sidebar (`routes.py:135`; `App.js:153-157`). Clicking a clarification copies the *system's* question into the input box (`App.js:127-129, 234`).
- [misleading] The UI score `1 - distance` (`App.js:253`) is not a 0–1 similarity. MiniLM vectors are unit length (the model's `Normalize` layer, seen in your local model cache), and Chroma's `l2` distance is squared Euclidean (library behaviour), so the distance runs from 0 to 4 and the "score" from −3 to 1.
- [bug] Error text becomes conversation history. When generation fails, the apology or the "API key needs to be updated" text is returned as a normal reply (`rag_service.py:224-241`) and saved as the assistant turn (`routes.py:49-51`). The next turn's rewrite and answer then read that text as if the assistant had said it (`rag_service.py:128, 143`).
- [misleading] "Query expansion" is really a rewrite. `ContextExpander.expand_query` asks the LLM for **one** standalone question (`context_expander.py:44-51`). It adds no synonyms or extra terms and issues no extra queries, which is what "query expansion" usually means in IR. In your notes, call it query rewriting (the "condense question" step).
- [shallow] No answer-level citations. The docs are labelled `[Document i]` (`rag_service.py:193-196`), but the prompt never asks the model to cite them (`rag_service.py:209-214`). The response returns doc ids (`rag_service.py:175`), so you know what was retrieved, but not which doc supports which sentence.
- [ok-for-demo] `KEYS conversation:*` (`redis_service.py:86`). The Dockerfile starts its own redis-server (`Dockerfile:20`) while compose also runs one (`docker-compose.yml:4-9`); the backend uses the compose one (`docker-compose.yml:16`), so the in-container server is wasted.

### Tests and data
- `tests/test_conversation_memory.py`: the sliding-window test is correct (`4-13`). The token test sets a budget of 50 but asserts ≤ 100 (`15-24`), so it passes while the budget is exceeded: pruning stops at 2 messages (`conversation_memory.py:52`), and the 50-word message plus one short one is over 50 tokens (exact count UNVERIFIED; not run). Serialisation round-trip (`26-34`). There are **no tests** for ambiguity, the rewrite or the routes.
- `scripts/test.sh:41-64` runs a 4-turn conversation and only prints the replies; there are no assertions. The script cannot fail as a whole: it has no `set -e`, so a failing pytest run (`test.sh:11`) does not stop it, and its last command is `cd ..` (`test.sh:67`), so it exits 0. If the backend is down, the conversation part prints a skip message and exits 0 (`test.sh:25-30`). The 5 SaaS docs (`rag_service.py:71-97`) plus this 4-turn script make a decent **toy multi-turn test case**: plan names give a clear coreference target.

### What to take for your project
- **Q1 mechanism (re-implement in plain Python):** a `rewrite_followup(history, query) -> standalone` function on Groq. Log `original → rewritten` in your provenance trace (C6). The paraphrased prompt at `context_expander.py:44-51` is a fine starting point. With `gpt-oss-20b`, set `reasoning_effort="low"` and enough `max_tokens`. Put the call behind your record/replay cache, keyed on model id, prompt version, history and query. When the call fails, fall back to the raw query **and log the fallback**; L26 hides it (`context_expander.py:65-71`). Do not strip apostrophes.
- **History hygiene:** store only real assistant answers in history, never error text (L26 stores it, `routes.py:49-51`). The history and the rewrite go to Groq, so run these experiments on your project PDFs, never on book text.
- **Fix the order:** rewrite first, then decide. Better still, ask the LLM for one structured output: {standalone_query, needs_clarification, clarifying_question}. Use real retrieval evidence (top-1 score, or the gap between top-1 and top-2) instead of a constant.
- **The experiment L26 never runs (M2 + Q1):** write 15 two-turn cases, each with a gold standalone question and a gold relevant chunk id. Compare Recall@k for the raw follow-up against the rewritten query. Keep retrieval quality and answer quality separate.
- **X3:** the sliding window class is fine. If you add a token budget, make it a hard limit and test that limit exactly.

### Try this
- (20 min) Re-implement the score formula from `ambiguity_detector.py:52-68` in your own words. Score the 4 queries in `scripts/test.sh:42-45`, the README example (`README.md:61`) and 5 follow-ups of your own, **predicting each score first**. Then write by hand the standalone rewrite each one should get, and score the rewrites. **Look for:** truly unclear turns the rule misses, harmless ones it flags, and the fact that the history never changes a score.

### Interview angle
- **Q:** "In a RAG chatbot, the user asks 'How much does it cost?' right after asking about plans. Walk me through your pipeline."
  **A:** I keep a windowed history and have an LLM rewrite the follow-up into a standalone question ("How much does the Enterprise plan cost?"), logging both versions. I retrieve with the rewrite. If the reference is still unresolved (the rewriter says so, or retrieval is split between plans), I ask one clarifying question instead of guessing. I test the rewriter by retrieval recall on a set of multi-turn cases.

---

## L27 · RAG evaluation with RAGAS (dashboard)  (`lesson27/l27-rag-evaluation/`)

**What the code teaches, in one line:** How to wire the RAGAS library (`faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`) behind a FastAPI "evaluation run" API with WebSocket updates and a metrics dashboard.
**What it is not:** It has no retrieval metrics. Precision@k, Recall@k, MRR and nDCG appear **nowhere** (grep), and there are no document ids or relevance labels. There is **no gold-labelled dataset**. On the normal path, two of the four dashboard metrics are never actually computed. The numbers you see are often hard-coded or random.
**Relevance to your RAG study:** High, as a cautionary example, and for the RAGAS metric definitions. Concepts: M3 (RAGAS faithfulness and answer relevancy, judged by the generator model itself). Counter-examples: M1 (no gold set; the "reference" is the system's own answer), M2 (context precision and recall are shown but not computed; no P@k, R@k, MRR or nDCG), M4 (n = 2, items share memory, random fallback), V4 (the judge is never checked), D3 (a trend chart of placeholder numbers, and a test of the fake baseline). Tags: [LLMOps] (eval runs, evaluators, dashboard), [Interview].
**Stack:** FastAPI. `langchain==0.1.16` `ConversationalRetrievalChain` with `ConversationBufferMemory`; `langchain-google-genai==0.0.11`; `ragas==0.1.9`; `datasets==2.18.0`; `faiss-cpu==1.8.0` (`backend/requirements.txt:8-16`). LLM: Gemini `gemini-pro`, temperature 0.0 (`backend/app/services/rag_evaluator.py:29-33`), probably no longer served (UNVERIFIED; see L26). The **same model** is the RAG generator and the RAGAS judge (`rag_evaluator.py:45-51, 120-125`). Embeddings: Gemini `models/embedding-001` (`rag_evaluator.py:23-26`), used for both retrieval and answer relevancy. Store: in-memory FAISS over 10 one-sentence docs, k=3 (`rag_evaluator.py:47, 58-76`). SQLite tables are created at startup if the `models` import resolves (a failure is logged and swallowed), but nothing ever writes to them (`backend/app/core/database.py:11-18`; `get_db` is never used). `redis`, `prometheus-client` and `tenacity` are listed (`requirements.txt:21, 26, 30`) but never imported. The React/Vite UI shows 4 metric cards, a trend line chart, a run list with a small "(demo)" tag, and a Run Evaluation button (`frontend/src/App.jsx:168-188, 201-218, 240, 284-316`).
**Swap to your stack:** Hard. It is pinned to `ragas 0.1.9` and `langchain 0.1.x` (`requirements.txt:9-12`). RAGAS takes LangChain LLM and embedding objects (`rag_evaluator.py:120-125`) and parses structured output from the judge, which may be fragile with a reasoning model (UNVERIFIED; ragas is not installed here). It is simpler to re-implement the metrics in plain Python on your cached Groq and Cohere calls, with the judge run once at the end, as already decided.
**Your earlier copy:** Docker files added, plus a `BACKEND_URL` proxy in `vite.config.js` (line 4), a `LESSON27.md` summary and a 1538-line `l27-streamlit/app.py`. The copy has **no `frontend/src/`**, so its React UI cannot be built. The Streamlit app keeps `ground_truth = answers` (`l27-streamlit/app.py:660`) and the random-score fallback (`app.py:1145-1152`). `LESSON27.md` repeats two errors: "implements all four metrics" (`LESSON27.md:20`) and "SQLite DB (run history)" (`LESSON27.md:68-69`).

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `API_KEY_SETUP.md` | The only doc (there is no README); promises "real RAGAS metrics" | 3, 14-24 |
| 2 | `backend/app/services/rag_evaluator.py` | RAG chain, dataset build, RAGAS call, score assembly | 17-172 |
| 3 | `backend/app/api/evaluation.py` | Run lifecycle, background task, **random fallback** | 16-100 |
| 4 | `backend/app/api/metrics.py` | Summary and trends; hard-coded BASELINE | 8-71 |
| 5 | `backend/app/api/benchmarks.py` | 10 hard-coded queries; a fake "GPT-3.5" baseline | 7-34 |
| 6 | `backend/app/core/database.py`, `backend/models/evaluation.py` | Tables that are never used | db 11-17 |
| 7 | `data/sample_queries.json` | 10 questions, no answers, never loaded | all |
| 8 | `backend/tests/test_api.py` | Endpoint tests | 11-51 |
| 9 | `frontend/src/App.jsx` (skim) | Sends only 2 queries; cards; demo tag | 81-90, 201-218, 284-316 |

Below, a bare `evaluation.py` means `backend/app/api/evaluation.py`. The schema and table files with the same name are written out in full. Also: `rag_evaluator.py` = `backend/app/services/rag_evaluator.py`; `metrics.py` and `benchmarks.py` are in `backend/app/api/`; `App.jsx` = `frontend/src/App.jsx`; `test.sh` = `scripts/test.sh`.

### How it works, step by step
1. **Click "Run Evaluation".** The UI fetches the 10 hard-coded queries from `/api/benchmarks/sample-queries` (`benchmarks.py:10-21`, not the JSON file) and posts **only the first 2**: "What is RAG?" and "How does evaluation work?" (`App.jsx:81-89`).
2. **The run is created** in an in-memory dict as "pending", and a background task starts (`evaluation.py:13, 16-50`).
3. **The evaluator is built lazily** (`evaluation.py:65`; `rag_evaluator.py:165-172`). It embeds the 10 KB sentences with Gemini into FAISS and creates one `ConversationalRetrievalChain` with **one shared memory** (`rag_evaluator.py:36-51`). The singleton is reused across all runs.
4. **Generate answers** for all questions **concurrently**, in threads (`rag_evaluator.py:82-85, 103`). Because the memory is shared, question 2 may or may not see question 1 in its chat history, depending on timing. Later runs also carry the history of earlier runs. The items are therefore not independent and the order is not deterministic. Worse, whenever the history is not empty, `ConversationalRetrievalChain` first asks the LLM to rewrite the question using that history, retrieves with the rewrite, and by default answers the rewrite too (library behaviour, seen in `langchain_classic` 1.0.3, `chains/conversational_retrieval/base.py:151-176`; the pinned `langchain` 0.1.16 is not installed, so UNVERIFIED for it). The dataset still records the **original** question (`rag_evaluator.py:92, 108`).
5. **Build the dataset** with question, answer, contexts and `"ground_truth": [r["answer"] for r in responses]`. The **system's own answer is the reference** (`rag_evaluator.py:107-112`).
6. **Call RAGAS with 2 metrics only**: faithfulness and answer_relevancy (`rag_evaluator.py:117-125`). Then `context_precision` and `context_recall` are read with `.get(…, 0.8)` (`rag_evaluator.py:126-127`). The result can only hold the two metrics that were asked for, so both come back as **the constant 0.8**. (This assumes the ragas 0.1.x result object behaves like a dict, which is UNVERIFIED here because ragas is not installed. If it did not, `.get` would throw and the fallback below would run. Either way, the 2-metric path never measures precision or recall.) The 4-metric call runs only if the 2-metric call throws (`rag_evaluator.py:128-138`).
7. **Per-question results** are copies of the run averages: each question gets the same four numbers (`rag_evaluator.py:151-161`).
8. **On any exception**, for example no key, an unserved model id, a quota error or a parse error, the run is marked **"completed"** with `random.uniform` scores of 0.82–0.90, 0.78–0.87, 0.75–0.85 and 0.74–0.84 (`evaluation.py:77-94`).
9. **Dashboard.** With no runs yet, the summary returns a hard-coded BASELINE of 0.87 / 0.82 / 0.79 / 0.75 (`metrics.py:8-13, 38-45`), and the trends endpoint returns 24 identical points labelled "0:00"–"23:00" (`metrics.py:62-70`). After runs, the "avg_" fields are just the **latest run's** values, labelled "last_24h" (`metrics.py:21-29`).

**How each metric is actually produced**
| Metric | In this code | Kind | Where |
|---|---|---|---|
| Precision@k, Recall@k, MRR, nDCG | **not implemented**; no doc ids, no relevance labels | n/a | grep finds nothing |
| Faithfulness | RAGAS: an LLM splits the answer into statements and judges each against the retrieved contexts; score = supported ÷ total, averaged over 2 questions (library behaviour, UNVERIFIED here: ragas not installed) | LLM-judged (self-judged) | `rag_evaluator.py:117-125, 140` |
| Answer relevance | RAGAS: an LLM writes questions back from the answer, and the score is their embedding cosine to the real question, averaged (library behaviour, UNVERIFIED here) | LLM + embeddings | `rag_evaluator.py:117-125, 141` |
| Context precision | **constant 0.8** on the normal path. On the fallback path, RAGAS judges whether each context was useful for reaching the "reference", which here is the system's own answer | hard-coded / circular | `rag_evaluator.py:126, 137` |
| Context recall | **constant 0.8** on the normal path. On the fallback path, the share of the "reference" sentences supported by the context. With the system's own answer as the reference, this becomes close to a faithfulness check | hard-coded / circular | `rag_evaluator.py:127, 138, 111` |
| Any metric after an error | `random.uniform` within a flattering range | random | `evaluation.py:84-87` |
| Any metric before a first run | BASELINE constants | hard-coded | `metrics.py:8-13` |
| "GPT-3.5 + ChromaDB" baseline | the same constants, dated 2025-01-15; never measured | hard-coded | `benchmarks.py:25-34` |

**Gold dataset?** None. `data/sample_queries.json` holds 10 questions with no reference answers and no relevant-doc labels, and **no code loads it** (grep). `benchmarks.py:7-22` hard-codes a similar but differently worded list instead, and that is the list the UI sends.

### README vs code
- There is no `README.md`. `API_KEY_SETUP.md:3` promises "real RAGAS metrics (Faithfulness, Relevance, Precision, Recall computed by AI)". Only the first two are computed; Precision and Recall are 0.8 (`rag_evaluator.py:116-127`).
- `API_KEY_SETUP.md:16-18` honestly says that without a key you get synthetic scores. But the metric cards (`App.jsx:201-218`) do not say so; only a small "(demo)" tag appears in the run list (`App.jsx:284-285`). Note also that a run with a **valid** key that fails for any reason gets random numbers too, marked "completed".
- Code comments say the chain and embeddings are "reused from L26" (`rag_evaluator.py:22, 38`). L26 used the raw Gemini SDK, Chroma, MiniLM and custom memory; L27 uses LangChain chains and FAISS. No code is shared.
- The comment "full run uses all 4" (`rag_evaluator.py:116`) is true only when the 2-metric run throws.
- The request schema declares a `model_config` field (`backend/app/schemas/evaluation.py:16`), and the UI sends one (`App.jsx:90`). Pydantic v2 reserves that name for model configuration and never treats it as a field (confirmed in the pydantic 2.12 source, `pydantic/_internal/_fields.py:266-269`; the pinned 2.6.1 is not installed here). So per-run model settings would be dropped silently. Today nothing reads them anyway.

### Where it is thin or wrong
- [misleading] Context precision and recall are a constant 0.8 (`rag_evaluator.py:126-127`). **This is the biggest error in the block.**
- [bug] Using the system's answer as `ground_truth` (`rag_evaluator.py:111`) makes any reference-based metric circular. It rewards retrieval that supports a *wrong* answer.
- [misleading] Random metrics are labelled "completed" (`evaluation.py:80, 84-87`), and the hard-coded baseline and flat 24-hour "trend" appear before any run (`metrics.py:8-13, 62-70`).
- [bug] Shared conversational memory plus concurrent generation (`rag_evaluator.py:39-51, 103`) means the evaluation items leak into each other, so the results depend on timing. Temperature 0 (`rag_evaluator.py:32`, commented "Deterministic for evaluation") cannot make this reproducible.
- [bug] Hidden question rewrite (see step 4). From the second item on, retrieval runs on an LLM rewrite shaped by unrelated earlier questions, but answer relevancy is scored against the original question (`rag_evaluator.py:92, 108`), which is not the question the model answered. Each such item also costs one extra LLM call that the run never reports. Library behaviour as noted in step 4.
- [shallow] No provenance at all: the KB is loaded with `FAISS.from_texts` without ids or metadata (`rag_evaluator.py:71-74`), and only the context text is kept (`rag_evaluator.py:89`). Even if you had labels, you could not compute a retrieval metric from this output without matching on text.
- [shallow] n = 2 questions per run (`App.jsx:89`), so the trend chart compares runs of 2 questions each. No variance or confidence interval is reported.
- [shallow] The same model generates and judges (`rag_evaluator.py:29-33, 123`), so self-preference bias is a real risk. The judge is never checked against human labels (V4).
- [shallow] Per-question scores are copies of the run average (`rag_evaluator.py:151-161`), so you cannot do failure analysis (M5).
- [misleading] "avg_" plus "last_24h" are applied to the latest run only (`metrics.py:21-29`).
- [shallow] The SQLAlchemy tables (with a `ground_truth` column, `backend/models/evaluation.py:46`) are created (`backend/app/core/database.py:13-15`) but runs live only in a dict (`evaluation.py:13`), so they are lost on restart. `embedding_cache` is unused (`rag_evaluator.py:54`).

### Tests and data
- `backend/tests/test_api.py` has 5 endpoint tests (`11-51`). `test_metrics_summary` asserts that the **hard-coded baseline** is > 0 (`27-35`), so it tests the fake. No test touches any metric computation.
- `scripts/test.sh:27` runs pytest with `|| true` (and only if `backend/venv` exists, line 25), so failures are ignored, and then always prints "Basic tests passed!" (`test.sh:29`).
- Data: the 10 KB sentences (`rag_evaluator.py:58-69`) and the 10 questions (`data/sample_queries.json`) are small but **usable for building a first gold set by hand** (see Try this).

### What to take for your project
- **M2 (the missing half):** build your own retrieval harness: a gold set of (question, relevant chunk ids), then P@k, R@k, MRR and nDCG@k in NumPy. Report these separately from answer quality.
- **M3:** learn the RAGAS definitions (faithfulness = supported claims ÷ claims; answer relevance; context precision/recall **with a real reference**) and implement them yourself, with a judge that is a *different* model from the generator. Per your decision D-10, the Cohere judge runs once at the end on stored traces, with Codex calibration labels for TPR/TNR.
- **M4/D3:** the *run* record shape (run id, status, per-item results, aggregate) is worth copying. Persist per-item scores as JSONL, together with the model id, prompt version, k and index `snapshot_id`. Make every item stateless: no shared memory between items, and never run eval items through a conversational chain. Log the query the retriever actually saw next to the original question. Cache every generator and judge call (record/replay), so a rerun of the harness costs nothing and gives the same numbers.
- **Run status:** keep `failed` as a real status with the error message, and leave the scores empty. L27 marks failures "completed" (`evaluation.py:80`).
- **Rules to adopt:** never use the system's output as the reference; show "not computed" (None/NaN) instead of defaults; never show random or placeholder numbers in a metrics view; run with n large enough to give a confidence interval.

### Try this
- (25 min) First, without running anything, trace what the four cards show in three cases: (a) fresh start; (b) a run with no key; (c) a run with a working key. *Expected:* (a) all four come from BASELINE (`metrics.py:38-45`); (b) all four are random (`evaluation.py:84-87`); (c) faithfulness and relevance are LLM-judged on 2 questions, while precision and recall are 0.8 (`rag_evaluator.py:117-127`). If `gemini-pro` is no longer served, (c) silently turns into (b) (UNVERIFIED). Then use or paraphrase the 10 KB sentences (`rag_evaluator.py:58-69`) as a corpus and the 10 questions from `data/sample_queries.json`. Label the 1–2 relevant sentences for each question; this is your first M1 gold set. Rank the corpus with MiniLM or BM25 in your `ragkit` and compute Recall@3 and MRR. **Look for:** questions whose only matching sentence names the topic but does not answer it. For example, "How does hybrid search improve RAG?" only has `rag_evaluator.py:68`, which never says how it improves anything. Also look at "How does evaluation work?" (`benchmarks.py:12`), one of the two questions the UI really sends: it is too vague to label. A dashboard cannot reveal that; labelling does.

### Interview angle
- **Q:** "Why does RAGAS context recall need a reference answer, and what goes wrong if you use the model's own answer as the reference?"
  **A:** Context recall asks whether the retrieved chunks contain what a *correct* answer needs, so it needs an independent reference. If the reference is the model's own answer, you measure only whether the context supports what the model said, which is close to faithfulness. A wrong answer backed by the wrong chunk then scores well. You need human-written or carefully checked references, and you should still report retrieval metrics against labelled chunk ids.

---

## Block summary
| Lesson | Title | Relevance | Concepts | Best file to read | Biggest problem |
|---|---|---|---|---|---|
| L24 | Modular RAG with LangChain (LCEL) | Medium | C4, C5, C6, R4, D1; R1†, R3† · LLMOps · Interview | `backend/main.py:123-240` | Default path uses SHA-256 "embeddings" plus a canned answer (Docker never sets `USE_GEMINI`); "hybrid" is vector+MMR; scores are `0.9-0.1·rank` (`main.py:67-88, 143, 321`) |
| L25 | Advanced prompting for grounding | High (ideas) | P7, C5, V1, V3; V2†, V4† · Interview | `backend/app.py:47-174` | "Grounding confidence" = question–context word overlap, computed after generation; context has no `[Source N]` labels; nothing is evaluated (`app.py:112-127, 388-406`) |
| L26 | Multi-turn RAG: ambiguity + rewrite | High | Q1, A1, X3, C5 · Interview | `backend/app/services/rag_service.py:116-156` + `context_expander.py:31-71` | Ambiguity uses constant retrieval confidence 0.5 and ignores history; README/test examples are not flagged; no Redis = no memory (`rag_service.py:132`; `redis_service.py:29-31`) |
| L27 | RAG evaluation with RAGAS | High (cautionary) | M3; M1†, M2†, M4†, V4†, D3† · LLMOps · Interview | `backend/app/services/rag_evaluator.py:98-163` | Context precision/recall are constant 0.8; `ground_truth` = own answer; random metrics on error; no IR metrics, no gold set (`rag_evaluator.py:111, 126-127`; `evaluation.py:84-87`) |

† Counter-example: the lesson names the technique (or shows a metric for it) but does not implement it. Study what is missing.

### Cross-lesson patterns
- **Silent "demo" fallbacks that return HTTP 200 with made-up content:** L24 `offline_answer` (`main.py:209-220`); L25 canned refusal in test mode (`app.py:317-321`); L26 canned clarifications and the raw-query fallback (`ambiguity_detector.py:121-127`, `context_expander.py:65-71`); L27 random metrics (`evaluation.py:84-87`). With old Gemini ids (`gemini-2.0-flash-exp` in L24, and `gemini-pro` in 4 places: 3 in L26, 1 in L27) that are probably no longer served (UNVERIFIED), these fallbacks are probably what a fresh run shows. Your earlier L26 copy swapped the model ids.
- **Fake or placeholder numbers shown as scores:** `0.9-0.1·rank` (L24); relevance 0.0/0.5 (L25); retrieval confidence 0.5 (L26); 0.8 defaults, BASELINE constants and a "GPT-3.5" baseline (L27).
- **String and keyword heuristics standing in for judgment:** word overlap and the "do not contain" check (L25); 5 regexes (L26).
- **No chunking anywhere in the block,** and toy corpora of 3–10 tiny docs (1–3 sentences each), with k a large share of the corpus: k=5 over 3–4 docs in L24 (`main.py:182`), k=3 of 5 in L26 (`rag_service.py:120`), k=3 of 10 in L25 and L27 (`app.py:249`; `rag_evaluator.py:47`). So retrieval quality is hard to observe.
- **Tests check plumbing, not quality,** and the shell "tests" print "passed" unconditionally (L24 `test.sh:41`, L25 `test.sh:47`, L27 `test.sh:27-29`). L26's script always exits 0 (`test.sh:11, 25-30, 67`). L27 even unit-tests its fake baseline.
- **Errors are reported as normal results:** L25 labels an API error "rejected", like a correct refusal (`app.py:379-381`); L26 saves its apology text as the assistant turn (`routes.py:49-51`); L27 marks a failed run "completed" with random scores (`evaluation.py:80-87`). Your traces need a separate `error` state.
- **No stable ids, so provenance is weak:** L24 gets random ids on every ingest (`main.py:277-280`); L25 shows the rank as the source id (`app.py:410-412`); L27 stores no ids at all (`rag_evaluator.py:71-74`). Only L26 seeds fixed ids (`rag_service.py:73-99`). No lesson loads a PDF, so page numbers never appear.
- **Mis-named techniques:** "hybrid" = vector + MMR and a "reranking" flag with no reranker (L24); "grounding confidence" = question–context word overlap (L25); "query expansion" = a single rewrite, and "semantic" memory = sliding window (L26); "context precision/recall" = the constant 0.8 (L27).
- **Version churn:** LangChain 0.3.x (L24, L25), then 0.1.x (L26 lists it but never imports it; L27). L25 and L27 use legacy chains (`RetrievalQA`, `ConversationalRetrievalChain`, `ConversationBufferMemory`). In LangChain 1.x these live in the separate `langchain-classic` package (seen in a local install of `langchain` 1.2.3 with `langchain_classic` 1.0.1).
- **"Builds on the previous lesson" is README text only:** each lesson is an independent re-implementation with a different store, chain style and SDK.
- **Retrieval quality and answer quality are never measured separately:** no lesson in the block computes a retrieval metric against labels.
