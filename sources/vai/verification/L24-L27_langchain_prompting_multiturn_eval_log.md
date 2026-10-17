# Verification log: VAI lessons 24–27: LangChain RAG, grounding prompts, multi-turn RAG, RAG evaluation

[← Lesson guide](../L24-L27_langchain_prompting_multiturn_eval.md) · [← Guide index](../README.md)

Pass A re-opened every cited claim at its source line and tried to refute it. Pass B re-read every backend file with a different lens: control flow, missed issues, concept mapping and fit to your stack. Verdicts: confirmed / corrected / removed / unverified.
## Verification log (pass A)

Method: every bullet, setting, key-lines cell, summary cell and exercise was checked against the source by reading (nothing in the course repo was run). Score tables and overlap numbers were recomputed with a small scratch script outside the repo. Library facts were checked against locally installed newer versions where possible (`langchain_classic` 1.0.1, `pydantic` 2.12.5, `chromadb` 1.5.5, the cached MiniLM `modules.json`); the pinned versions are not installed.

| Lesson | Claim (short) | Verdict | Evidence file:line |
|---|---|---|---|
| All | No `setup.sh` in lessons 24–27; only project folders | confirmed | folder listing of `lesson24`–`lesson27` |
| L24 | Pinned langchain 0.3.7, lc-google-genai 2.0.5, lc-chroma 0.1.4, chromadb 0.5.23 | confirmed | `backend/requirements.txt:3-6` |
| L24 | LLM `gemini-2.0-flash-exp`, temp 0.3, 1024 max tokens | confirmed | `backend/main.py:116-121` |
| L24 | Experimental id probably retired | unverified | provider fact, not in code |
| L24 | Gemini embeddings only when `USE_GEMINI` set and key real | confirmed | `main.py:63-64, 82-88` |
| L24 | Hash "embeddings": 32 values from SHA-256, 0–1 | confirmed | `main.py:70-72` |
| L24 | Persistent Chroma at `../data/chroma_db` | confirmed | `main.py:91-94` |
| L24 | `sentence-transformers` listed, never imported | confirmed | `requirements.txt:7`; imports `main.py:1-22` |
| L24 | UI: query, mode selector, Top-K, answer, timings, trace, % score | confirmed | `QueryInterface.js:51-87, 104-153` |
| L24 | Swap: constructors at 83-86 and 116-121 | confirmed | `main.py:83-86, 116-121` |
| L24 | Earlier copy identical except `.gitignore`, `App.css` | confirmed | `diff -rq` vs `prior_work/VAI/lesson24` |
| L24 | Key lines: README 22-35; main 63-121, 123-185, 187-240, 286-342 | confirmed | as cited |
| L24 | Key lines: compose 10-12; Dockerfile 24, 34 | confirmed | `docker-compose.yml:10-12`; `Dockerfile:24, 34` |
| L24 | Row 8 "3 sample sentences" | corrected (3 docs of 2–3 sentences) | `scripts/init-data.sh:7, 14, 21` |
| L24 | QueryInterface key lines 20-24, 148 (Top-K box missing) | corrected (added 78-87) | `QueryInterface.js:20-24, 78-87, 148` |
| L24 | Step 1 provider choice; `llm = None` otherwise | confirmed | `main.py:63-64, 82, 114-121` |
| L24 | Step 2 store; bare-except create; wrapper | confirmed | `main.py:91-111` |
| L24 | Step 3 whole text = one vector, no splitter | confirmed | `main.py:273-284` |
| L24 | Step 4 similarity + MMR (fetch_k=20) on the same index | confirmed | `main.py:137-151` |
| L24 | Step 4 interleave, dedup by first 100 chars, cut to k | confirmed | `main.py:153-177` |
| L24 | k fixed at 5 for both retrievers | confirmed | `main.py:180-185` |
| L24 | Step 5 LCEL chain shape | confirmed | `main.py:227-235` |
| L24 | `format_docs` labels `[Source i]` | confirmed | `main.py:202-207` |
| L24 | Prompt does not ask for citations | confirmed | `main.py:188-197` |
| L24 | Step 6 retrieval runs again inside the chain | corrected (only when an LLM is configured) | `main.py:225-226, 303, 308-311` |
| L24 | `offline_answer` = first 200 chars of up to 3 docs | confirmed | `main.py:209-220` |
| L24 | `relevance_score = 0.9 - 0.1·rank` | confirmed | `main.py:321` |
| L24 | Hand-made 2-row trace; tokens = word count | confirmed | `main.py:327-330` |
| L24 | Prometheus metrics are real (line list) | corrected (added 289) | `main.py:29-32, 175, 289, 292, 314` |
| L24 | `TracingCallback` defined but never attached | confirmed | `main.py:243-266`; no other reference |
| L24 | README "vector and keyword"; comment "Keyword search via MMR" wrong | confirmed | `README.md:24`; `main.py:143-149` |
| L24 | README "swap without code changes"; "keyword" mode falls to vector | confirmed | `README.md:26`; `main.py:48, 297-299` |
| L24 | README Gemini; compose passes only `GEMINI_API_KEY` | confirmed | `README.md:28, 34-35`; `docker-compose.yml:10-12` |
| L24 | README "Production ready" vs fabricated trace | confirmed | `README.md:27`; `main.py:243-266, 327-330` |
| L24 | [misleading] hash embeddings; demo works since k ≥ corpus of "3–4 sentences" | corrected (3–4 short docs) | `init-data.sh:4-23`; `test.sh:15-20`; `main.py:182` |
| L24 | [misleading] rank label shown as % | confirmed | `main.py:321`; `QueryInterface.js:148` |
| L24 | [bug] `top_k`, `enable_reranking` ignored; Top-K box "at line 23" | corrected (box is 79-86; line 23 sends it) | `main.py:49-50, 182, 185`; `QueryInterface.js:23, 79-86` |
| L24 | [bug] retrieval twice; histogram observed twice | corrected (LLM path only) | `main.py:175, 303, 308-311` |
| L24 | [shallow] fusion is interleave, not RRF; same-prefix chunks "merged" | corrected (the second is dropped) | `main.py:157-172` |
| L24 | [bug] `COPY data/` with no `data/` folder fails the build | confirmed (Docker refuses a missing COPY source) | `Dockerfile:24`; folder listing; `scripts/build.sh:5` |
| L24 | Chroma path resolves to `/data/chroma_db`, outside the volume | confirmed | `main.py:92`; `Dockerfile:3, 34`; `docker-compose.yml:9` |
| L24 | Local run writes outside the project | confirmed | `README.md:18`; `main.py:92` |
| L24 | [shallow] legacy imports, deprecated `get_relevant_documents` | confirmed | `main.py:10-14, 303` |
| L24 | [ok-for-demo] bare excepts | confirmed | `main.py:99, 150` |
| L24 | `test.sh` always prints "All tests passed!" | confirmed | `scripts/test.sh:41` |
| L24 | init-data "3 one-sentence docs" | corrected (2–3 sentences each) | `init-data.sh:7, 14, 21` |
| L24 | LCEL 9 lines, "cleanest in this course" | corrected ("in this block"; course-wide claim not checked) | `main.py:227-235` |
| L24 | Histogram idea for D1/D2 | confirmed | `main.py:30-32` |
| L24 | Try this: doable; MiniLM ranks the LangChain sentence first | corrected (marked as expectation, not run; added all-positive note) | `main.py:72, 182` |
| L24 | Interview: sources/timings "not exactly what the model saw" | corrected (softened: separate call, usually the same) | `main.py:303, 309` |
| L24 | Block summary "Biggest problem" cell | confirmed | `main.py:67-88, 143, 321`; `docker-compose.yml:10-12` |
| L24 | Best file `main.py:123-240` | confirmed | `main.py:123-240` |
| L25 | Pinned chromadb 0.5.18, langchain 0.3.7, lc-genai 2.0.5, lc-community 0.3.7 | confirmed | `backend/requirements.txt:4-7` |
| L25 | Default `gemini-2.0-flash` via env var, temp 0.1 | confirmed | `backend/app.py:40-45` |
| L25 | Gemini embedding-001; MiniLM fallback without key or on error | confirmed | `app.py:34-37, 207, 224-241` |
| L25 | Chroma is in memory (no persist dir) | confirmed | `app.py:228-233` |
| L25 | UI elements | confirmed | `App.jsx:115-137, 157-162, 190-241` |
| L25 | Swap: only the constructors are provider-specific | corrected (also `genai.configure`) | `app.py:29-31, 34-45` |
| L25 | Earlier copy lacks `App.jsx`, `.env.example` | confirmed (also `.gitignore`, `App.css`) | `diff -rq` |
| L25 | Key lines: README 14-37; app 47-105, 107-174, 204-252, 308-431 | confirmed | as cited |
| L25 | Key lines: tests 8-56; test.sh 20-47; App.jsx 191-208 | confirmed | as cited |
| L25 | Step 1: 10 one-sentence docs, metadata source/id, `l25_knowledge` | confirmed | `app.py:210-233` |
| L25 | Step 1: one `RetrievalQA` stuff chain per template, k=3 | confirmed | `app.py:244-252` |
| L25 | Step 2: request fields | confirmed | `app.py:177-180` |
| L25 | Step 3: demo path = top-3 docs as answer; canned refusal in test mode | confirmed | `app.py:312-342` |
| L25 | Step 4: 5 canned strings by substring; "do not contain" rule | confirmed | `app.py:159-174, 356-367` |
| L25 | Step 5: stuff chain uses raw content + blank lines, no labels | confirmed in later source; pinned 0.3.7 unverified | `langchain_classic/chains/combine_documents/base.py:21-23` |
| L25 | Step 6: overlap of question words, threshold 0.3, stopwords count | confirmed | `app.py:112-127, 388` |
| L25 | Step 7: regex + range check only | confirmed | `app.py:134-152, 391-392` |
| L25 | Step 8: state rules; answer always returned | confirmed | `app.py:395-406, 417-419` |
| L25 | Step 9: one card per retrieved doc; score always 0.0 | confirmed | `app.py:409-415, 222` |
| L25 | Prompt paraphrases (strict, moderate, creative); temp 0.1 | confirmed | `app.py:51-66, 71-85, 90-103, 44` |
| L25 | README "Gemini 1.5 Flash" vs code default | confirmed | `README.md:19`; `app.py:39-40` |
| L25 | README "citation validation" = range check only | confirmed | `README.md:25`; `app.py:141-152` |
| L25 | README "grounding confidence" = question/context overlap | confirmed | `README.md:26`; `app.py:112-127` |
| L25 | Docstring says "before generation"; called after | confirmed | `app.py:109, 371, 388` |
| L25 | README adversarial "verify"; canned without key | confirmed | `README.md:37`; `app.py:317-321` |
| L25 | README "Built on L24", but no shared code | confirmed | `README.md:39`; both backends read |
| L25 | [bug] unlabelled context vs `[Source N]` demand | confirmed (library default, see step 5) | `app.py:58, 66` |
| L25 | [misleading] grounded answer shows 33% | corrected (depends on the other 2 retrieved docs; which ones is unverified) | `app.py:212, 214, 216, 387-388` |
| L25 | Unit test passes at exactly 1/3 | confirmed (computed) | `tests/test_grounding.py:13-18` |
| L25 | [misleading] "Citations Found" counts retrieved docs | confirmed | `app.py:409-415`; `App.jsx:207-208` |
| L25 | [misleading] relevance 0.0 normal path, 0.5 demo/fallback | confirmed | `app.py:294, 330, 414` |
| L25 | [shallow] abstention by substring; "insufficient" | confirmed | `app.py:364, 398, 80` |
| L25 | [misleading] moderate/creative labelled "hallucinated" | confirmed | `app.py:364, 79-81, 97` |
| L25 | [bug] "api" inside "capital"/"rapid" | confirmed (computed); added key-only caveat | `app.py:164, 170-171, 317-321`; `test.sh:23` |
| L25 | [misleading] `test.sh` checks a 503 that never comes; unconditional pass | confirmed | `test.sh:27, 33, 47`; `app.py:310` |
| L25 | [shallow] deprecated APIs; `genai` configured but unused | confirmed | `app.py:12-13, 15, 31, 207, 254` |
| L25 | Tests check only the three helpers | confirmed | `tests/test_grounding.py:8-56` |
| L25 | Data: 10 one-sentence facts | confirmed | `app.py:210-221` |
| L25 | Citation regex as a cheap first tier | confirmed | `app.py:134-152` |
| L25 | Try this: 2/6 = 0.33 for the price question | confirmed (computed) | `app.py:216, 112-127` |
| L25 | Block summary cell; best file 47-174 | confirmed | `app.py:47-174, 112-127, 388-406` |
| L26 | Pinned genai 0.3.2, chromadb 0.4.22, ST 2.3.1, redis 5.0.1, tiktoken | confirmed | `backend/requirements.txt:6-12` |
| L26 | `langchain` listed but never imported | confirmed (grep) | `requirements.txt:10-11` |
| L26 | `gemini-pro` in 3 places, default temperature | confirmed | `ambiguity_detector.py:31`; `context_expander.py:29`; `rag_service.py:46` |
| L26 | `gemini-pro` retired | unverified | provider fact, not in code |
| L26 | MiniLM embeddings | confirmed | `rag_service.py:49` |
| L26 | Chroma `./data/chroma`, default L2 | confirmed (default `l2` in chromadb source) | `rag_service.py:52-62`; chromadb `hnsw_params.py:56` |
| L26 | UI: chat, session info, ambiguity badge, clarifications, `1 - distance` | confirmed | `App.js:142-164, 216-256` |
| L26 | Swap: 3 call sites | confirmed | `ambiguity_detector.py:109`; `context_expander.py:54`; `rag_service.py:219` |
| L26 | Earlier copy: model ids, build-essential/g++, npm install | confirmed | `diff` of the 5 changed files |
| L26 | Key lines: README 5-12, 80-101; routes 18-75; rag_service 116-241 | confirmed | as cited |
| L26 | Key lines: detector 25-127; expander 31-71; memory 11-115; redis 17-87 | confirmed | as cited |
| L26 | Step 1: Redis connect; seed 5 SaaS docs on first run | confirmed | `main.py:35`; `rag_service.py:58-110` |
| L26 | Step 2: request schema; memory defaults sliding/10 | confirmed | `models/schemas.py:10-13`; `routes.py:23-36`; `conversation_memory.py:11-21` |
| L26 | Step 3: query added first; last 5 messages | confirmed | `routes.py:39`; `rag_service.py:128`; `conversation_memory.py:75-81` |
| L26 | Step 4: weights 0.5/0.3/0.2, < 3 words, threshold > 0.4 | confirmed | `ambiguity_detector.py:29, 52-68` |
| L26 | Step 4: 5 regex descriptions | confirmed | `ambiguity_detector.py:33-39` |
| L26 | Step 4: retrieval confidence constant 0.5, so a constant 0.15 | confirmed | `rag_service.py:131-133`; `ambiguity_detector.py:56` |
| L26 | Step 4: `conversation_context` unused in `detect` | confirmed | `ambiguity_detector.py:41-77` |
| L26 | Step 5: clarifications, canned fallback, no retrieval, not stored | confirmed | `ambiguity_detector.py:90-127`; `rag_service.py:136-140`; `routes.py:46-51` |
| L26 | Step 6: rewrite prompt; quotes/apostrophes stripped; fallback | confirmed | `context_expander.py:44-71` |
| L26 | Step 7: retrieve with the rewrite, top_k=3 | confirmed | `rag_service.py:120, 146, 158-182` |
| L26 | Step 8: original query in prompt; `expanded_query` unused | confirmed | `rag_service.py:187, 193-216` |
| L26 | Step 8: error fallbacks | confirmed | `rag_service.py:224-241` |
| L26 | Step 9: 24 h TTL save | confirmed | `routes.py:53-57`; `redis_service.py:15, 48-58` |
| L26 | Score table, 6 rows (0.35, 0.15, 0.35, 0.35, 0.45, 0.45) | confirmed (recomputed) | `ambiguity_detector.py:33-39, 52-68` |
| L26 | "Only short + ≥1 hit, or long + ≥3 hits, are flagged" | confirmed (computed) | `ambiguity_detector.py:59-68` |
| L26 | Table example sources | confirmed | `README.md:61`; `scripts/test.sh:43` |
| L26 | README "retrieval confidence scoring" | confirmed | `README.md:8`; `rag_service.py:132` |
| L26 | README "ConversationBufferMemory"; "semantic" falls back | confirmed | `README.md:49`; `conversation_memory.py:15, 33-40` |
| L26 | README `MAX_*` never read; list of variables that are read | corrected (added `GEMINI_API_KEY`) | grep of `getenv`; `README.md:83-84` |
| L26 | README lines 93, 99, 101: claims absent in code | confirmed | `README.md:93, 99, 101` |
| L26 | Redis "in-memory fallback" is really no storage | confirmed | `redis_service.py:29-31, 50, 62` |
| L26 | [bug] no memory without Redis; `/health` "degraded" | confirmed | `main.py:73` |
| L26 | [misleading] constant confidence; history ignored | confirmed | `rag_service.py:132`; `ambiguity_detector.py:41-77` |
| L26 | [shallow] clarify decided before the rewrite | confirmed | `rag_service.py:131-143` |
| L26 | [bug] "Android" counts as "and" | confirmed (computed) | `ambiguity_detector.py:35` |
| L26 | [bug] pronoun rule fires "only at the end" | corrected (also before punctuation) | `ambiguity_detector.py:34` (recomputed) |
| L26 | [bug] empty-history guard never fires; extra LLM call | confirmed | `routes.py:39`; `context_expander.py:41-42` |
| L26 | [bug] `"API key" in ...lower()` never true | confirmed | `context_expander.py:69`; `rag_service.py:229` |
| L26 | [bug] apostrophes stripped | confirmed | `context_expander.py:58` |
| L26 | [shallow] token pruning keeps ≥ 2; not the default; cl100k | confirmed | `conversation_memory.py:21, 52`; `routes.py:29` |
| L26 | [shallow] "CLARIFYING" is never read | corrected (the UI displays it; no backend logic uses it) | `routes.py:27, 46-49, 135`; `App.js:153-157` |
| L26 | Clicking a clarification copies it into the input box | confirmed | `App.js:127-129, 234` |
| L26 | [misleading] `1 - distance` is not 0–1 | confirmed; made precise (range −3 to 1) | `App.js:253`; chromadb `distance_functions.py:11-12`; MiniLM `modules.json` Normalize |
| L26 | [ok-for-demo] `KEYS`; two Redis servers | confirmed | `redis_service.py:86`; `Dockerfile:20`; `docker-compose.yml:4-9, 16` |
| L26 | Tests: sliding OK; token budget 50 vs assert 100; serialisation | confirmed (exact token count unverified) | `test_conversation_memory.py:4-34`; `conversation_memory.py:52` |
| L26 | No tests for ambiguity, rewrite or routes | confirmed | only one test file exists |
| L26 | `test.sh` 4-turn script, no assertions | confirmed | `scripts/test.sh:41-64` |
| L26 | 5 SaaS docs usable as a toy multi-turn case | confirmed | `rag_service.py:71-97` |
| L26 | Try this: doable (test queries score 0.15, 0.15, 0.15, 0.25) | confirmed (computed) | `scripts/test.sh:42-45`; `ambiguity_detector.py:52-68` |
| L26 | Block summary cell; best files | confirmed | `rag_service.py:116-156, 132`; `context_expander.py:31-71`; `redis_service.py:29-31` |
| L27 | Pinned langchain 0.1.16, lc-genai 0.0.11, ragas 0.1.9, datasets 2.18.0, faiss 1.8.0 | confirmed | `backend/requirements.txt:8-16` |
| L27 | `ConversationalRetrievalChain` + `ConversationBufferMemory` | confirmed | `rag_evaluator.py:4-5, 39-51` |
| L27 | `gemini-pro`, temp 0.0 | confirmed | `rag_evaluator.py:29-33` |
| L27 | `gemini-pro` retired | unverified | provider fact, not in code |
| L27 | Same model generates and judges | confirmed | `rag_evaluator.py:45-51, 120-125` |
| L27 | Gemini embeddings for retrieval and answer relevancy | confirmed | `rag_evaluator.py:23-26, 71-74, 124` |
| L27 | In-memory FAISS, 10 one-sentence docs, k=3 | confirmed | `rag_evaluator.py:47, 58-76` |
| L27 | SQLite tables "created but never written" | corrected (created only if the import resolves; failure swallowed) | `backend/app/core/database.py:11-18`; grep of `get_db` |
| L27 | `redis`, `prometheus-client`, `tenacity` unused | confirmed (grep) | `requirements.txt:21, 26, 30` |
| L27 | UI: 4 cards, trend chart, demo tag, button | confirmed | `App.jsx:168-188, 200-225, 240-250, 284-286` |
| L27 | Swap: judge JSON parsing fragile with a reasoning model | unverified (ragas not installed) | `rag_evaluator.py:120-125` |
| L27 | Earlier copy: Docker, `BACKEND_URL`, LESSON27.md, 1538-line Streamlit | confirmed | `diff -rq`; `wc -l`; `vite.config.js:4` |
| L27 | Earlier copy: missing `frontend/src/` not mentioned | corrected (added) | `diff -rq` |
| L27 | Streamlit keeps `ground_truth = answers`; random fallback | confirmed | `l27-streamlit/app.py:660, 1145-1152` |
| L27 | LESSON27.md repeats "all four metrics", "SQLite (run history)" | confirmed | `LESSON27.md:20, 68-69` |
| L27 | Key lines: API_KEY_SETUP 3, 14-24; rag_evaluator 17-172 | confirmed | as cited |
| L27 | Key lines: evaluation.py 16-94 | corrected (fallback ends at 100) | `evaluation.py:16-100` |
| L27 | Key lines: metrics 8-71; benchmarks 7-34; db 11-17; tests 11-51 | confirmed | as cited |
| L27 | Key lines: App.jsx 84-90 | corrected (fetch starts at 81) | `App.jsx:81-90` |
| L27 | Step 1: UI fetches "the 10 sample queries" | corrected (from `benchmarks.py`, not the JSON file) | `App.jsx:81-89`; `benchmarks.py:10-21` |
| L27 | Step 2: in-memory dict, "pending", background task | confirmed | `evaluation.py:13, 16-50` |
| L27 | Step 3: lazy singleton; one shared memory | confirmed | `evaluation.py:65`; `rag_evaluator.py:36-51, 165-172` |
| L27 | Step 4: concurrent threads; items not independent | confirmed (code); the timing effect is runtime | `rag_evaluator.py:82-85, 103` |
| L27 | Step 5: `ground_truth` = own answer | confirmed | `rag_evaluator.py:107-112` |
| L27 | Step 6: precision/recall = constant 0.8 | confirmed (code); dict behaviour of the ragas result unverified | `rag_evaluator.py:117-127` |
| L27 | Step 6: 4-metric call only on exception | confirmed | `rag_evaluator.py:128-138` |
| L27 | Step 7: per-question rows copy the averages | confirmed | `rag_evaluator.py:151-161` |
| L27 | Step 8: random ranges 0.82–0.90, 0.78–0.87, 0.75–0.85, 0.74–0.84, marked "completed" | confirmed | `evaluation.py:77-94` |
| L27 | Step 9: BASELINE, 24 flat points, latest run shown as "avg"/"last_24h" | confirmed | `metrics.py:8-13, 21-29, 38-45, 62-70` |
| L27 | No P@k, R@k, MRR or nDCG anywhere | confirmed (grep) | backend and `frontend/src` |
| L27 | RAGAS faithfulness / answer relevancy definitions | unverified (library behaviour) | `rag_evaluator.py:117-125` |
| L27 | Context recall "is faithfulness again" | corrected ("close to a faithfulness check") | `rag_evaluator.py:111, 138` |
| L27 | "GPT-3.5" baseline = same constants, dated | confirmed | `benchmarks.py:24-34`; `metrics.py:8-13` |
| L27 | `data/sample_queries.json` is never loaded | confirmed (grep) | `data/sample_queries.json:1-14` |
| L27 | No README; API_KEY_SETUP promises 4 real metrics | confirmed | `API_KEY_SETUP.md:3` |
| L27 | Synthetic scores admitted in the doc; cards silent; small demo tag | confirmed | `API_KEY_SETUP.md:16-18`; `App.jsx:200-225, 284-286` |
| L27 | "Reused from L26" comments are false | confirmed | `rag_evaluator.py:22, 38`; L26 `rag_service.py:49, 55` |
| L27 | Comment "full run uses all 4" is true only on exception | confirmed | `rag_evaluator.py:116, 128-138` |
| L27 | `model_config` is not a request field (Pydantic) | confirmed in pydantic 2.12 source; pinned 2.6.1 unverified | `backend/app/schemas/evaluation.py:16`; `pydantic/_internal/_fields.py:266-269` |
| L27 | [misleading] constant 0.8 | confirmed | `rag_evaluator.py:126-127` |
| L27 | [bug] circular `ground_truth` | confirmed | `rag_evaluator.py:111` |
| L27 | [misleading] random labelled "completed"; baseline and flat trend | confirmed | `evaluation.py:80, 84-87`; `metrics.py:8-13, 62-70` |
| L27 | [bug] shared memory + concurrency; temp 0 cannot fix it | confirmed | `rag_evaluator.py:32, 39-51, 103` |
| L27 | [shallow] n = 2 per run | confirmed | `App.jsx:89` |
| L27 | [shallow] same model judges; bias "likely" | corrected (softened to "a real risk") | `rag_evaluator.py:29-33, 123` |
| L27 | [shallow] per-question copies | confirmed | `rag_evaluator.py:151-161` |
| L27 | [misleading] "avg_"/"last_24h" on the latest run | confirmed | `metrics.py:21-29` |
| L27 | [shallow] unused tables, dict storage, `embedding_cache` (ambiguous paths) | corrected (full paths) | `backend/models/evaluation.py:46`; `backend/app/core/database.py:13-15`; `rag_evaluator.py:54` |
| L27 | 5 endpoint tests; summary test checks the fake baseline | confirmed | `tests/test_api.py:11-51, 27-35` |
| L27 | `test.sh` ignores pytest failures; always prints "passed" | confirmed (added the venv condition) | `scripts/test.sh:25-29` |
| L27 | KB sentences and questions usable for a first gold set | confirmed | `rag_evaluator.py:58-69`; `data/sample_queries.json` |
| L27 | Try this: (a)/(b)/(c) traces | confirmed; added a caveat for (c) (unverified) | `metrics.py:38-45`; `evaluation.py:84-87`; `rag_evaluator.py:117-127` |
| L27 | Try this: example "How does evaluation work?" taken from the JSON | corrected (it is in `benchmarks.py:12`; JSON example replaced) | `data/sample_queries.json:3-12`; `rag_evaluator.py:68` |
| L27 | Interview: own-answer reference = "faithfulness again" | corrected (softened) | `rag_evaluator.py:111` |
| L27 | Block summary cell; best file 98-163 | confirmed | `rag_evaluator.py:98-163, 111, 126-127`; `evaluation.py:84-87` |
| Cross | Silent HTTP-200 fallbacks list | confirmed | `main.py:209-220`; `app.py:317-321`; `ambiguity_detector.py:121-127`; `context_expander.py:65-71`; `evaluation.py:84-87` |
| Cross | `gemini-pro` in 4 places; ids "retired" | count confirmed; "retired" unverified | L26 three sites; `rag_evaluator.py:30` |
| Cross | "Your earlier copies had to swap the model ids" | corrected (only the L26 copy did) | `diff` of L24–L27 copies |
| Cross | Placeholder numbers list | confirmed | `main.py:321`; `app.py:294, 330, 414`; `rag_service.py:132`; `rag_evaluator.py:126-127` |
| Cross | Toy corpora with "k ≈ corpus size" | corrected (k share differs per lesson) | `main.py:182`; `rag_service.py:120`; `app.py:249`; `rag_evaluator.py:47` |
| Cross | Shell "tests" print "passed" unconditionally | confirmed | L24 `test.sh:41`; L25 `test.sh:47`; L27 `test.sh:27-29` |
| Cross | Version churn; legacy chains now in `langchain-classic` | confirmed (local `langchain_classic` 1.0.1) | `langchain_classic/chains/retrieval_qa/base.py`; `.../conversational_retrieval/base.py`; `.../memory/buffer.py` |
| Cross | No retrieval metric against labels in the block | confirmed (grep) | all four backends |

---

## Verification log (pass B)

Lens: completeness and teaching accuracy. Every backend `.py` file of the four lessons was read in full again (L24 `backend/main.py`; L25 `backend/app.py`, `tests/test_grounding.py`; L26 all of `backend/app/**` and `backend/tests/`; L27 all of `backend/app/**`, `backend/models/`, `backend/tests/`), plus the shell scripts, Docker files and the UI lines cited. Nothing in the course repo was run or installed. Library behaviour was checked in local newer installs where possible (`langchain_classic` 1.0.3, `langchain_community` 0.4.1, `langchain_groq` 1.1.2, all in the local venv at `C:\Yash\New-Work\RAG\my way\venv`); the pinned versions are not installed, so those points stay marked UNVERIFIED for the pinned versions. A scan for Google- and Groq-style key prefixes in the four lessons and of this guide found no secret; L25 `.env.example:3` is a placeholder.

| Lesson | Item | Change | Evidence file:line |
|---|---|---|---|
| L24 | Steps 1–7 match control flow | confirmed | `backend/main.py:63-121, 133-185, 223-240, 286-342` |
| L24 | Concept map | R1 recast as counter-example; R3 added as counter-example (flag, no reranker); C6 qualified (trace hand-made) | `main.py:50, 143-151, 327-330`; grep for "rerank" |
| L24 | Path shorthand | added | folder listing |
| L24 | Step 3: no ids on ingest | added | `main.py:277-280` |
| L24 | Step 4: distance space and MMR `lambda_mult` | added (l2 default; 0.5 library default, UNVERIFIED for pinned `langchain_chroma`) | `main.py:100-103, 145-149`; `langchain_community/vectorstores/chroma.py:622` |
| L24 | [bug] re-ingest duplicates on a persistent store | added | `main.py:91-94, 277-280, 162-165`; `langchain_community/vectorstores/chroma.py:273` |
| L24 | [bug] no index version across hash/Gemini embedders | added (dimension error UNVERIFIED) | `main.py:82-88, 96-98` |
| L24 | `top_k` bullet: smoke test asks for 3; no reranker exists | extended | `scripts/test.sh:31`; `main.py:50, 182, 185` |
| L24 | What to take: ChatGroq settings, cache, LangSmith rule, `input_type` split, stable ids, index version | added | `main.py:74-78, 277-280`; `langchain_groq/chat_models.py:377` |
| L24 | Interview: add the fix (retrieve once, carry docs) | extended; answer otherwise correct | `main.py:303, 309` |
| L25 | Steps 1–9 match control flow | confirmed | `backend/app.py:204-252, 308-431` |
| L25 | Concept map | V2 and V4 recast as counter-examples; V1 and V3 qualified | `app.py:112-127, 364, 398` |
| L25 | Path shorthand; `.env.example` is a placeholder | added | `.env.example:3` (value not printed) |
| L25 | Step 3: demo path labels "grounded" by overlap | added | `app.py:326, 333-334` |
| L25 | Step 9: card `source_id` is the rank | added | `app.py:410-412` |
| L25 | Step 10: quota fallback and error → "rejected" | added | `app.py:275, 282-306, 372-381` |
| L25 | [misleading] demo/quota "grounded" without an LLM | added (which docs are retrieved UNVERIFIED) | `app.py:212, 296, 334` |
| L25 | [misleading] errors share the "rejected" state | added | `app.py:275, 379-381` |
| L25 | [shallow] provenance lost (rank, not stored id) | added | `app.py:222, 410-415` |
| L25 | [misleading] "Strict (Legal/Medical)", "100% grounding" UI claim | added | `frontend/src/App.jsx:117, 122`; `app.py:404-406, 417-419` |
| L25 | [shallow] `test.sh` has no `set -e` | added | `test.sh:10, 47` |
| L25 | What to take: cache, reasoning settings, error state, provenance, judge tier | added (the judge tier cites decision D-10) | `rag_learning/08_GAP_ANALYSIS_AND_DECISIONS.md:490, 542` |
| L25 | Interview answer | confirmed correct | n/a |
| L26 | Steps 1–9 match control flow | confirmed; steps 5, 8, 9 extended | `backend/app/services/rag_service.py:116-241`; `backend/app/api/routes.py:18-75` |
| L26 | Concept map | D2 removed (Redis is a session store, not a cache); Q1/A1/C5 qualified | `backend/app/services/redis_service.py:48-58` |
| L26 | Path shorthand | added | folder listing |
| L26 | Step 5: empty clarification list on a parse miss | added | `ambiguity_detector.py:113-119`; `routes.py:61` |
| L26 | Step 8: prompt never asks for citations | added | `rag_service.py:209-214` |
| L26 | Step 9: any reply (incl. error text) saved; docs returned with ids and distances | added | `routes.py:49-51`; `rag_service.py:174-179` |
| L26 | [bug] error text becomes history | added | `rag_service.py:128, 143, 224-241`; `routes.py:49-51` |
| L26 | [misleading] "query expansion" is a single rewrite | added | `context_expander.py:31-51` |
| L26 | [shallow] no answer-level citations | added | `rag_service.py:175, 193-196, 209-214` |
| L26 | Score table and regex claims | re-checked by hand; confirmed | `ambiguity_detector.py:29, 33-39, 52-68` |
| L26 | Tests: `test.sh` always exits 0 | added | `scripts/test.sh:11, 25-30, 67` |
| L26 | What to take: reasoning settings, cache key, logged fallback, history hygiene, no book text | added | `context_expander.py:58, 65-71`; `routes.py:49-51` |
| L26 | Interview answer | confirmed correct | n/a |
| L27 | Steps 1–9 match control flow | confirmed; step 4 extended | `backend/app/services/rag_evaluator.py:36-163`; `backend/app/api/evaluation.py:16-100`; `backend/app/api/metrics.py:15-71` |
| L27 | Concept map | recast: M3 real; M1, M2, M4, V4, D3 as counter-examples | `rag_evaluator.py:111, 116-127`; `evaluation.py:84-87`; `metrics.py:8-13`; `backend/tests/test_api.py:27-35` |
| L27 | Path shorthand | extended | folder listing |
| L27 | Step 4 and [bug]: hidden condense-question rewrite in `ConversationalRetrievalChain` | added (library behaviour; UNVERIFIED for pinned 0.1.16) | `rag_evaluator.py:45-51, 92, 108`; `langchain_classic/chains/conversational_retrieval/base.py:151-176` (1.0.3) |
| L27 | [shallow] no ids or metadata in FAISS; contexts are text only | added | `rag_evaluator.py:71-74, 89` |
| L27 | Temperature comment "Deterministic for evaluation" | added to the existing bullet | `rag_evaluator.py:32` |
| L27 | What to take: stateless items, log the retrieved query, cache generator and judge calls, a real `failed` status | added; "D-32" corrected to D-10 | `evaluation.py:80`; `08_GAP_ANALYSIS_AND_DECISIONS.md:490` |
| L27 | Interview answer | confirmed correct | n/a |
| Block | Summary table concept cells | updated to match the lesson headers; footnote now defines "counter-example" (†) | as above |
| Cross | New patterns: errors reported as normal results; weak ids and provenance; mis-named techniques; L26 test exit code | added | `app.py:379-381`; `routes.py:49-51`; `evaluation.py:80-87`; `main.py:277-280`; `app.py:410-412`; `rag_evaluator.py:71-74`; L26 `rag_service.py:73-99`; L26 `scripts/test.sh:67` |
