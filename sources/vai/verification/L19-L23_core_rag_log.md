# Verification log: VAI lessons 19–23: core RAG

[← Lesson guide](../L19-L23_core_rag.md) · [← Guide index](../README.md)

Pass A re-opened every cited claim at its source line and tried to refute it. Pass B re-read every backend file with a different lens: control flow, missed issues, concept mapping and fit to your stack. Verdicts: confirmed / corrected / removed / unverified.
## Verification log (pass A)

Method: every cited line was opened in the read-only source. Nothing was run. Library or model behaviour was checked only where a local copy exists: Chroma 1.5.x in your global Python 3.12 site-packages, and the model configs in your Hugging Face cache (`~/.cache/huggingface/hub`). Otherwise it is marked UNVERIFIED. Paths are relative to each lesson's project folder.

| Lesson | Claim (short) | Verdict | Evidence file:line |
|---|---|---|---|
| Header | Prior copies live in `prior_work\VAI\lesson19-23\` | corrected (one folder per lesson) | `Book RAG/prior_work/VAI/lesson19/` … `lesson23/` |
| L19 | Pinned FastAPI 0.115, google-generativeai 0.8.3, PyPDF2 3.0.1 | confirmed | `backend/requirements.txt:1-9` |
| L19 | 9-model fallback list, first `gemini-2.0-flash-lite`, last `gemini-flash-latest` | confirmed | `backend/query_engine.py:15-25` |
| L19 | Store is in-memory dicts | confirmed | `backend/knowledge_base.py:8-16` |
| L19 | UI polls stats every 3 s, sends top_k 3, shows chunk score | confirmed | `frontend/src/App.js:16-17, 61-63, 182-187` |
| L19 | One provider call `generate_content` | confirmed | `backend/query_engine.py:134` |
| L19 | `decode_instrumentation.py` is never imported | confirmed | grep over all of lesson19: no reference |
| L19 | PDF if magic bytes, extension or content type say so | confirmed | `backend/main.py:174-196` |
| L19 | PyPDF2 pages joined with blank lines | confirmed | `backend/document_processor.py:74-78` |
| L19 | Text files must be .txt/.md/.mdx | confirmed | `backend/main.py:234` |
| L19 | Cleaning collapses whitespace, strips all but word chars, space, `.,!?;:-()` | confirmed | `backend/document_processor.py:50, 52` |
| L19 | 500-char chunks, step 450, overlap 50 | confirmed | `backend/main.py:27`; `backend/document_processor.py:25-43` |
| L19 | `next_overlap` stored, unused for retrieval | confirmed | `backend/document_processor.py:32-40`; `backend/knowledge_base.py:31` |
| L19 | doc_id = filename with spaces/dots replaced | confirmed | `backend/main.py:424-425` |
| L19 | Chunk id = doc id + `_chunk_<i>` | confirmed | `backend/knowledge_base.py:23` |
| L19 | Inverted index word → chunk ids | confirmed | `backend/knowledge_base.py:35-38` |
| L19 | Tokeniser: lower-case, punctuation→space, len > 2, 16 stopwords | confirmed | `backend/knowledge_base.py:83-90` (16 words counted) |
| L19 | Score = number of distinct shared words | confirmed | `backend/knowledge_base.py:51-58` (both sides are sets) |
| L19 | "No tie-break rule" | corrected (stable sort; ties follow set order, which can change per process) | `backend/knowledge_base.py:61-65` |
| L19 | No shared word → fixed answer, no LLM call | confirmed | `backend/query_engine.py:97-104` |
| L19 | Prompt: one instruction, context, question, "Answer:"; `[Source N]` labels; no system/temperature/max tokens/cite request | confirmed | `backend/query_engine.py:107-120` |
| L19 | 3 attempts; backoff capped at 30 s | corrected (switch path waits 0.5 s; retry-after hint is uncapped) | `backend/query_engine.py:125-178` |
| L19 | Auth errors stop at once | corrected (only 401/403 detected; "API key" test on lower-cased text never matches) | `backend/query_engine.py:180-183` |
| L19 | Response: answer, chunk id, first 200 chars, score, 3 timings; history | confirmed | `backend/query_engine.py:203-220` |
| L19 | README "keyword indexing" = set-overlap | confirmed | `README.md:27`; `backend/knowledge_base.py:54-58` |
| L19 | README "Gemini 2.0 Flash" vs 9 models, model not reported | confirmed | `README.md:37`; `backend/query_engine.py:15-25, 203-218` |
| L19 | README performance numbers have no benchmark code | confirmed (numbers stay UNVERIFIED) | `README.md:28, 49-51` |
| L19 | README "Complete test suite"; integration test is `pass` | confirmed | `README.md:31`; `tests/test_rag_system.py:43-45` |
| L19 | README "production-ready"; memory only | confirmed | `README.md:3`; `backend/knowledge_base.py:8-16` |
| L19 | [bug] duplicate tail chunk; test asserts it | corrected (condition reworded; test uses 100/20, not 500/50) | `backend/document_processor.py:25-43`; `tests/test_rag_system.py:8, 13-17` |
| L19 | [bug] cleaning destroys technical text | corrected (softened "lost" to "mangled", symbols listed) | `backend/document_processor.py:52` |
| L19 | [shallow] page numbers lost | confirmed | `backend/document_processor.py:50, 78`; `backend/knowledge_base.py:26-33` |
| L19 | Rare words weigh the same; "what/how/does/this" kept; AI/ML dropped | corrected (tag [misleading] → [shallow]; facts confirmed) | `backend/knowledge_base.py:88-89` |
| L19 | [bug] re-upload corrupts index | corrected (extended: stale higher-numbered chunks also remain) | `backend/knowledge_base.py:23-43` |
| L19 | [misleading] errors returned as answers with HTTP 200 | confirmed | `backend/query_engine.py:177, 182, 193`; `backend/main.py:482-495` |
| L19 | [bug] mostly non-ASCII .txt rejected as binary | confirmed | `backend/main.py:76-81, 236-240` |
| L19 | [bug] `start.sh` local path breaks on `backend.` imports; Docker sets PYTHONPATH | confirmed | `start.sh:37`; `backend/main.py:10-12`; `Dockerfile:14` |
| L19 | [ok-for-demo] debug prints with stack traces | confirmed | `backend/main.py:93-99, 258-264, 292-298` |
| L19 | `setup.sh` uses a single `gemini-2.0-flash-exp` | confirmed | `../setup.sh:214` (no debug code in setup.sh: grep) |
| L19 | Indexing test checks count only; retrieval test checks score > 0 only | confirmed | `tests/test_rag_system.py:19-41` |
| L19 | `test_demo.sh` asks 2 questions, checks only counters | confirmed | `test_demo.sh:51, 59, 71-86` |
| L19 | Sample docs 11 and 13 lines | corrected (added size: about 830 bytes each, 2 chunks each) | `data/sample_doc1.txt`, `data/sample_doc2.txt` (wc) |
| L19 | Prior copy: only `docker-compose.yml` differs | confirmed | `diff -rq` against `prior_work/VAI/lesson19/l19-naive-rag` |
| L19 | Try this: chunker on 480 chars and sample_doc2 | corrected (expected counts added: 1 and 0) | `backend/document_processor.py:25-43` (arithmetic) |
| L19 | Read-in-order key lines | confirmed | all ranges open on the named code |
| L19 | Block summary "Biggest problem" | confirmed | see rows above |
| L19 | Interview: overlap vs BM25 (IDF, k1, b) | confirmed (general IR fact; matches scorer) | `backend/knowledge_base.py:54-58` |
| L20 | Pinned FastAPI 0.109, chromadb 0.4.22, google-generativeai 0.4.0, numpy<2 | confirmed | `backend/requirements.txt:1-11` |
| L20 | Embedding model `models/text-embedding-004` (768-dim model fact) | confirmed | `backend/embedding_service.py:11`; 768 also stated at `../setup.sh:161` |
| L20 | PersistentClient `./data/chromadb`, `hnsw:space` cosine | confirmed | `backend/vector_store.py:10-16, 20-27` |
| L20 | UI: index panel (source+text), "% match", stats poll 2 s | confirmed | `frontend/src/App.jsx:17-53, 102-105`; `frontend/src/components/SearchPanel.jsx:33-36`; `IndexPanel.jsx:4-5` |
| L20 | `/index` fields and defaults | confirmed | `backend/main.py:53-70` |
| L20 | Chunker 500/50, skips blank, not configurable from request | confirmed | `backend/indexing_pipeline.py:13-23, 34` |
| L20 | One call per chunk, ≤ 10 concurrent, `retrieval_document` | confirmed | `backend/embedding_service.py:14-60` |
| L20 | Any chunk failure fails the document | confirmed | `backend/embedding_service.py:64-67` |
| L20 | Metadata fields; MD5 id of source+index+first 50 chars | confirmed | `backend/indexing_pipeline.py:46-57` |
| L20 | `collection.add` with documents/embeddings/metadata/ids | confirmed | `backend/vector_store.py:38-43` |
| L20 | `/search` n_results default 10; UI sends 5 | confirmed | `backend/main.py:47-51`; `frontend/src/App.jsx:105` |
| L20 | Query embedded with `retrieval_query` | confirmed | `backend/embedding_service.py:93` |
| L20 | Filters passed as Chroma `where` | confirmed | `backend/search_engine.py:23-28`; `backend/vector_store.py:54-58` |
| L20 | similarity = 1 − distance | confirmed | `backend/search_engine.py:32-39` |
| L20 | README `./set-api-key.sh` does not exist | confirmed | `README.md:8`; file listing |
| L20 | README WebSocket vs HTTP polling | confirmed | `README.md:35`; `backend/main.py:144-190`; `frontend/src/App.jsx:18` |
| L20 | README batch embedding vs per-chunk; setup.sh batched 100 with zero-vector fallback | confirmed | `README.md:41`; `backend/embedding_service.py:15, 50-60`; `../setup.sh:129-162` |
| L20 | README metadata filtering not in UI | confirmed | `README.md:42`; `frontend/src/App.jsx:105` |
| L20 | README "Production-ready error handling" | confirmed | `README.md:44` |
| L20 | [misleading] "invalid" → "API key expired or invalid" | corrected (also "expired"/"api key"; HTTP 503; bad-`where` example UNVERIFIED) | `backend/main.py:77-82, 102-107` |
| L20 | [shallow] no page or offset metadata | confirmed | `backend/indexing_pipeline.py:49-57` |
| L20 | [shallow] `add` does not overwrite existing ids | unverified (Chroma 0.4.x behaviour; code uses `add`) | `backend/vector_store.py:38`; `backend/indexing_pipeline.py:46` |
| L20 | [shallow] `distance_metric` is a hard-coded label | confirmed | `backend/vector_store.py:68-69`; `frontend/src/components/StatsPanel.jsx:17` |
| L20 | [ok-for-demo] nested metadata makes `add` fail | unverified (Chroma validation, not in repo) | `backend/indexing_pipeline.py:50` |
| L20 | `clear-collection.sh` exists because of dimension change | corrected (script says "proper embeddings"; dimension change is one case) | `clear-collection.sh:5-8`; `backend/main.py:136` |
| L20 | `test.sh` indexes one sentence, n_results 3, asserts nothing | confirmed | `test.sh:26-39` |
| L20 | No data folder in repo | confirmed | file listing |
| L20 | Prior copy: `gemini-embedding-001`, google-generativeai 0.8.3 | confirmed | `diff` of `backend/embedding_service.py:11`, `backend/requirements.txt:4` |
| L20 | Try this: default space squared L2, d = 2 − 2·cos | confirmed (math; `hnsw:space` key still honoured in current Chroma) | local `chromadb/api/collection_configuration.py:375-410` (1.5.x) |
| L20 | Interview: 0.35 → 0.65 (cosine) / 0.825 (L2, unit vectors) | confirmed (arithmetic) | n/a |
| L20 | Read-in-order key lines | confirmed | all ranges open on the named code |
| L20 | Block summary "Biggest problem" | confirmed | see rows above |
| L20 | Swap: dimension changes, re-index | confirmed | `backend/vector_store.py:20-27` |
| L21 | Pinned versions incl. chromadb 0.5.0, sentence-transformers 2.7.0, tiktoken | confirmed | `backend/requirements.txt:1-15` |
| L21 | 3 embedding models, dims, load-once vs reload | confirmed | `backend/app/services/embedding_service.py:26, 39-58, 92, 108` |
| L21 | "No vectors are normalised" | corrected (all-MiniLM-L6-v2 has a Normalize module; L3 does not; code itself never normalises) | HF cache `all-MiniLM-L6-v2/.../modules.json`; `paraphrase-MiniLM-L3-v2/.../modules.json` |
| L21 | Chart shows chunks, coherence and avg size | corrected (avg size computed, not drawn; Compare sends empty params) | `frontend/src/App.js:62-67, 89-97, 109-110, 199-227` |
| L21 | `tiktoken` never imported | confirmed | grep: no import in any `.py` |
| L21 | Chroma never queried | confirmed | grep: only `add` in `vector_service.py:53-57` |
| L21 | `/compare` loops strategies × models | confirmed | `backend/app/main.py:125-184` |
| L21 | NLTK punkt (and punkt_tab) downloaded at startup | confirmed | `backend/app/main.py:49-57` |
| L21 | fixed: 500/50, `end_pos` unclamped, overlap ≥ size loops forever | confirmed | `backend/app/services/chunking_service.py:35-52` |
| L21 | semantic: threshold 0.5, min 100, adjacent only, no max, fake `start_pos` | confirmed | `backend/app/services/chunking_service.py:60-102, 97` |
| L21 | recursive: max 1000, overlap 200 unused, halves sentences, `children` empty | confirmed | `backend/app/services/chunking_service.py:118-157` |
| L21 | sliding: 500 window, 250 stride, clean stop | confirmed | `backend/app/services/chunking_service.py:159-183` |
| L21 | sentence: 3 per chunk, positions are sentence indices | confirmed | `backend/app/services/chunking_service.py:187-199` |
| L21 | Gemini failure → 768 zero vector | confirmed | `backend/app/services/embedding_service.py:97-100` |
| L21 | Metrics = size stats + mean neighbour cosine | confirmed | `backend/app/services/chunking_service.py:205-228` |
| L21 | `/upload`: UTF-8 decode, semantic 0.5, store | corrected (wording: decode error → HTTP 500 via global handler) | `backend/app/main.py:30-39, 193-211` |
| L21 | README "5 chunking strategies" | confirmed | `README.md:29` |
| L21 | Chroma 0.5.0 rejects `chroma_db_impl="duckdb+parquet"` | unverified (check exists since 0.4 and in local 1.5.x; 0.5.0 not read) | `backend/app/services/vector_service.py:24-38`; local `chromadb/config.py:40-52, 379-382` |
| L21 | Client stays None → misleading "please install chromadb" | confirmed (code flow) | `backend/app/services/vector_service.py:15, 24, 42-43` |
| L21 | `add` passes no embeddings → default embedder, default space | confirmed | `backend/app/services/vector_service.py:33-36, 53-57` |
| L21 | README "Quality metrics" are not retrieval quality | confirmed | `README.md:33` |
| L21 | README "3 embedding models" | confirmed | `README.md:30` |
| L21 | [misleading] coherence rewards overlap | confirmed | `backend/app/services/chunking_service.py:212-219` |
| L21 | Prior note contradicts itself; "~0.30" and "core insight" unsupported | confirmed | `prior_work/VAI/lesson21/l21-advanced-embeddings/LESSON_EXPLANATION.md:55, 153, 160, 194` |
| L21 | [bug] recursive chunker infinite recursion on one long sentence | confirmed (by reading; not run) | `backend/app/services/chunking_service.py:133-140` |
| L21 | "It also emits an empty chunk" (same case) | corrected (that call never returns; empty chunks come from leading/trailing blank lines instead) | `backend/app/services/chunking_service.py:131, 144-153`; `backend/app/main.py:101-105` |
| L21 | [bug] recursive `start_pos` always 0 | confirmed | `backend/app/services/chunking_service.py:125, 150` |
| L21 | [bug] Gemini zero-vector fallback; prior copy raises instead | confirmed | `backend/app/services/embedding_service.py:97-100`; `diff` with prior copy |
| L21 | [shallow] silent truncation 256 / 128 | corrected (limits confirmed from model configs; "therefore cut" softened) | HF cache `sentence_bert_config.json` (256 and 128) |
| L21 | [shallow] mixed position units | confirmed | `backend/app/services/chunking_service.py:47-48, 97, 125, 198-199` |
| L21 | [ok-for-demo] models reloaded per call | confirmed | `backend/app/services/chunking_service.py:70`; `backend/app/services/embedding_service.py:108` |
| L21 | Test contents (≥ 1 chunk; 35-char text → 1 chunk) | confirmed | `backend/tests/test_chunking.py:4-29` |
| L21 | Async tests skipped; import probably fails | unverified (runtime; restructured, import failure comes first) | `backend/requirements.txt:14-15`; `test.sh:4-6`; `start_backend.sh:4` |
| L21 | No data files | confirmed | file listing |
| L21 | Try this on sample_doc2 | corrected (only about 830 chars; use 2+ pages) | `lesson19/l19-naive-rag/data/sample_doc2.txt` (wc) |
| L21 | Read-in-order key lines | confirmed | all ranges open on the named code |
| L21 | Block summary "Biggest problem" | corrected (Chroma rejection marked UNVERIFIED) | see rows above |
| L21 | Interview: compare chunkers by recall@k/MRR | confirmed (advice, matches gap in code) | n/a |
| L22 | Pinned FastAPI 0.110, sentence-transformers 2.5.1, redis 5.0.1, torch 2.2.0; chromadb unused | confirmed | `backend/requirements.txt:1-16`; grep: no chromadb import |
| L22 | Literal key, `gemini-pro` created, never called | confirmed (key value not reproduced) | `backend/main.py:26-28` (`model` never used again) |
| L22 | Redis from docker-compose | confirmed | `docker-compose.yml:2-8` |
| L22 | Dashboard: 10 docs, scores 0.68–0.86, badge, chart | confirmed | `frontend/src/components/RerankingDashboard.js:12-23, 61-64, 102-104` |
| L22 | Request fields; pool = caller (UI 10, test.sh 3) | confirmed | `backend/main.py:58-62`; `RerankingDashboard.js:30-34`; `test.sh:42-47` |
| L22 | Cache key = MD5(query) + MD5(ids); hit path | confirmed | `backend/main.py:98-111` |
| L22 | Raw logits, no sigmoid | confirmed | `backend/main.py:120-121`; HF cache `ms-marco-MiniLM-L-6-v2/.../config.json` (activation `Identity`) |
| L22 | Sort, top_k, rank and `rerank_score` | confirmed | `backend/main.py:124-131` |
| L22 | Improvement % formula; default caller score 0.5 | corrected (denominator floor 0.01; top-k of caller scores, not of kept docs) | `backend/main.py:117, 134-136` |
| L22 | 24 h TTL; latency list holds misses | confirmed | `backend/main.py:138-139, 153-154` |
| L22 | `/metrics` mean, p95, p99 | confirmed | `backend/main.py:170-181` |
| L22 | README bi-encoder; random uniform scores | confirmed | `README.md:32`; `backend/main.py:195-196` |
| L22 | README "Builds on L21"; nothing imported | confirmed | `README.md:45-46`; `backend/main.py:1-13` |
| L22 | README Redis 24 h TTL | confirmed | `README.md:30`; `backend/main.py:154` |
| L22 | README metrics dashboard | corrected (added what it shows; latency = misses only) | `README.md:31`; `frontend/src/App.js:15, 46-71` |
| L22 | README error handling; sync predict blocks event loop | confirmed | `README.md:34`; `backend/main.py:92-156` |
| L22 | [bug] literal API key committed | confirmed | `backend/main.py:26` (only file with a key, excluding node_modules) |
| L22 | [misleading] improvement mixes scales | confirmed (values UNVERIFIED as stated) | `backend/main.py:134-136` |
| L22 | [misleading] random bi-encoder; `ranking_changes` | confirmed | `backend/main.py:195-196, 217-218` |
| L22 | [bug] cache key ignores top_k and text | corrected (collision needs same list length; cache written even with `use_cache` false) | `backend/main.py:98-99, 153` |
| L22 | [bug] chart pairs input-order original with reranked doc | confirmed | `backend/main.py:144`; `RerankingDashboard.js:61-64` |
| L22 | [shallow] hollow metrics | confirmed | `backend/main.py:53-54, 95, 139` |
| L22 | [shallow] ~512-token pair limit | confirmed | HF cache `tokenizer_config.json` (`model_max_length` 512) |
| L22 | [ok-for-demo] `./models` mounted, no HF cache env; prior copy fixed | confirmed | `docker-compose.yml:21`; `backend/Dockerfile:1-14`; `diff` with prior copy |
| L22 | `test.sh`: never asserts cache hit; checks total_requests; unconditional ticks | corrected (total_requests check only warns, never fails) | `test.sh:35-65, 74-79, 107-112` |
| L22 | "5 sample sentences in test.sh" | corrected (3 for rerank, 5 for compare) | `test.sh:43-45, 89-93` |
| L22 | Try this: sigmoid vs raw "improvement" | confirmed (doable; sigmoid keeps order) | `backend/main.py:134-136` |
| L22 | Read-in-order key lines | confirmed | all ranges open on the named code |
| L22 | Block summary "Biggest problem" | confirmed | see rows above |
| L22 | Interview: why rerank a pool only | confirmed (general fact) | n/a |
| L23 | chromadb 0.5.20 PersistentClient, `hybrid_search_docs`, cosine only on create | confirmed | `backend/requirements.txt:4`; `backend/main.py:38-49` |
| L23 | `text-embedding-004`; cross-encoder; `gemini-2.0-flash-exp` never used | confirmed | `backend/main.py:35, 52, 88-92` (grep: `gemini_model` used once) |
| L23 | Document form has category and year | corrected (also author) | `frontend/src/components/DocumentManager.js:20-30` |
| L23 | Search UI filters, top-k, rerank toggle, `alpha: 0.5` | confirmed | `frontend/src/components/SearchInterface.js:20-48` |
| L23 | Docs embedded with `retrieval_query`; dummy 384-dim vector | confirmed | `backend/main.py:88-92, 326, 330-335` |
| L23 | `/search` always asks for 20 candidates | confirmed | `backend/main.py:357-362` |
| L23 | Vector leg: `where` pre-filter, n=20, distances unused; unbounded cache | confirmed | `backend/main.py:80-95, 182-193` |
| L23 | Keyword leg: `query_texts`, n 40/60, `$and` post-filter, comment at 202 | confirmed | `backend/main.py:202-247` |
| L23 | `query_texts` uses Chroma's default 384-dim MiniLM embedder | unverified (library behaviour; code comment agrees) | `backend/main.py:332-333` |
| L23 | RRF `1/(rank+60)`, 0-based; `alpha` unused | confirmed | `backend/main.py:147-159, 166` |
| L23 | Fetch top 20 with `get(ids)`, pair by position | confirmed | `backend/main.py:260-283` |
| L23 | Rerank ≤ 20, keep top_k (5); else RRF order | confirmed | `backend/main.py:290-307, 370-374` |
| L23 | `score` = logit or RRF | confirmed | `backend/main.py:383` |
| L23 | README "BM25" | confirmed (none in code) | `README.md:9`; `backend/main.py:200-254` |
| L23 | README "Parallel searches" | confirmed (added the code comment) | `README.md:47, 55`; `backend/main.py:177-254` |
| L23 | README timeouts / circuit breakers absent | confirmed | `README.md:115-116` |
| L23 | README Precision@5 89%, p95, 1000+ docs unsupported | confirmed | `README.md:133-135` |
| L23 | README "Vector + keyword + metadata storage" | confirmed | `README.md:48` |
| L23 | README RRF formula matches; paper ranks from 1 | confirmed | `README.md:89`; `backend/main.py:155-156` |
| L23 | [bug] keyword leg fails on 384 vs 768 mismatch | corrected (line refs 248-250, not 252-254; runtime UNVERIFIED) | `backend/main.py:220-230, 248-250` |
| L23 | [bug] no key → arbitrary ranking; comment "false" | corrected (vector leg skipped; comment "misleading", not "false") | `backend/main.py:182, 197-198, 331-335` |
| L23 | [misleading] `alpha` unused | confirmed | `backend/main.py:65, 166, 361`; `SearchInterface.js:47` |
| L23 | [bug-risk] `get(ids)` order | corrected (tag → [bug]; Chroma ordering UNVERIFIED) | `backend/main.py:266-283` |
| L23 | [bug] hand-written filter incomplete (`$in`, nested `$and`) | confirmed | `backend/main.py:106-145` |
| L23 | [bug] docs embedded with query task type | confirmed | `backend/main.py:91, 326` |
| L23 | [misleading] `score` mixes scales; UI 4 decimals | confirmed | `backend/main.py:383`; `SearchInterface.js:158-159` |
| L23 | [misleading] "API key" errors → `[]` with 200 | confirmed | `backend/main.py:394-397` |
| L23 | Re-adding an id does not update | unverified (Chroma `add` behaviour) | `backend/main.py:338` |
| L23 | `test.sh` one doc, passes if id appears; claims all features | corrected (persisted docs exist; filter isolates the test doc) | `test.sh:14-44`; `backend/main.py:38` |
| L23 | Sample data 5 docs with category/year/author | confirmed | `DocumentManager.js:50-81` |
| L23 | SVGs show BM25 / parallel design | confirmed | `architecture.svg`, `workflow.svg`, `state-diagram.svg` (grep) |
| L23 | Prior copy: `load_dotenv()`, `gemini-embedding-001` | confirmed | `diff` of `backend/main.py:13-15, 89` |
| L23 | Try this: BM25 + MiniLM + RRF | confirmed (doable; no repo lines needed) | n/a |
| L23 | Read-in-order key lines | confirmed | all ranges open on the named code |
| L23 | Block summary "Biggest problem" | corrected (dimension failure marked UNVERIFIED) | see rows above |
| L23 | Interview: RRF and k | confirmed (general fact) | n/a |
| Cross | Characters only; duplicate tail in L19, L20, L21 fixed | confirmed | L19 `document_processor.py:25-43`; L20 `indexing_pipeline.py:13-23`; L21 `chunking_service.py:35-52` |
| Cross | No page numbers anywhere | confirmed | rows above |
| Cross | Silent fake vectors (L20 setup.sh, L21, L23) | confirmed | L20 `../setup.sh:161-162`; L21 `embedding_service.py:97-100`; L23 `main.py:330-335` |
| Cross | Mixed score scales (L22, L23) | confirmed | L22 `main.py:134-136`; L23 `main.py:383` |
| Cross | Metric theatre; no labelled set anywhere | confirmed | rows above |
| Cross | Unused LLM objects / dead code | confirmed | L22 `main.py:28`; L23 `main.py:35`; L19 `decode_instrumentation.py` |
| Cross | Error sniffing | confirmed | L20 `main.py:78, 103`; L23 `main.py:394-397` |
| Cross | Folders hand-edited after setup.sh | confirmed | L19 `../setup.sh:214`; L20 `../setup.sh:129-162` |
| Cross | Chroma distance metric per lesson | confirmed | L20 `vector_store.py:24`; L21 `vector_service.py:35`; L23 `main.py:41-49` |
| Cross | Literal key in L22 only | confirmed | L22 `backend/main.py:26` |

Tally: 194 claims checked. 158 confirmed, 30 corrected, 0 removed, 6 unverified. 4 short facts were added inside existing bullets, all checked: the dead "API key" test (L19); stale chunks after re-upload (L19); the cache written even when `use_cache` is false (L22); empty chunks from leading or trailing blank lines (L21). No API key value appears in this guide.

---

## Verification log (pass B)

Lens: completeness and teaching accuracy. Every backend `.py` file of L19–L23 was read in full (plus the tests, the scripts that tests rely on and the frontend lines cited). Nothing was run or installed. Library behaviour was checked only against your local Hugging Face cache; anything else is marked UNVERIFIED. Paths are relative to each lesson's project folder.

| Lesson | Item | Change | Evidence file:line |
|---|---|---|---|
| L19 | How it works, steps 1–9 | confirmed against the real control flow | `backend/main.py:174-234, 400-434`; `backend/document_processor.py:16-80`; `backend/knowledge_base.py:18-90`; `backend/query_engine.py:84-221` |
| L19 | Step 8 (retries) | extended: the model switch persists across questions | `backend/query_engine.py:69-82` |
| L19 | Concept IDs | corrected: added P2 (inverted index) and P7 (grounding prompt); qualified C5 (no citations) and V3 (zero-hit abstain only) | `backend/knowledge_base.py:35-38`; `backend/query_engine.py:97-120` |
| L19 | README "production-ready" bullet had no file:line | corrected (cite added) | `backend/knowledge_base.py:8-16` |
| L19 | "All available models have been tried" | added [misleading]: at most 3 of 9 models are tried | `backend/query_engine.py:125, 128, 177` |
| L19 | Abstain branch | added [shallow]: "what"/"how"/"does" are not stopwords, so zero-hit abstain rarely fires (reasoned, not run) | `backend/query_engine.py:97-104`; `backend/knowledge_base.py:88` |
| L19 | What to take | added: Groq `openai/gpt-oss-20b` with `reasoning_effort="low"`, cached, model id logged; citation check; non-book corpus for external calls | `backend/query_engine.py:107-120, 134, 203-218` |
| L19 | Interview answer | corrected: this scorer uses sets, so it ignores term frequency; k1 gives diminishing returns rather than a hard cap | `backend/knowledge_base.py:54-58, 90` |
| L20 | How it works, steps 1–7 | confirmed | `backend/main.py:47-108`; `backend/indexing_pipeline.py:13-74`; `backend/embedding_service.py:14-106`; `backend/search_engine.py:11-42`; `backend/vector_store.py:20-60` |
| L20 | Concept IDs and relevance | confirmed (R2 is real through Chroma `where`) | `backend/search_engine.py:23-28`; `backend/vector_store.py:54-58` |
| L20 | "% match" label | added [misleading]: cosine × 100 is not a calibrated relevance percentage | `frontend/src/components/SearchPanel.jsx:33-35`; `backend/search_engine.py:38` |
| L20 | Stale chunks after an edit | added [shallow]: ids hash the first 50 chars; no delete by `source` | `backend/indexing_pipeline.py:46`; `backend/vector_store.py:75-79`; `backend/main.py:134-142` |
| L20 | `chunk_size` metadata | added: holds the actual chunk length | `backend/indexing_pipeline.py:56` |
| L20 | What to take | added: cached `embed-v4.0` calls, separate MiniLM index, delete-by-source plus a re-index test | `backend/vector_store.py:75-79` |
| L20 | Interview (0.35 → 0.65 / 0.825) | confirmed (arithmetic) | n/a |
| L21 | How it works, steps 1–9 | confirmed | `backend/app/services/chunking_service.py:33-228`; `backend/app/services/embedding_service.py:60-114`; `backend/app/main.py:46-60, 125-211` |
| L21 | Recursive-chunker bug | extended: in `/compare` the error is caught per strategy | `backend/app/main.py:178-182` |
| L21 | UI breaks on a failed strategy | added [bug]: chart and cards read `.chunks.length` from an error string (React unmount not run) | `backend/app/main.py:182`; `frontend/src/App.js:90-93, 209` |
| L21 | Semantic chunker details | added [shallow]: boundaries always from all-MiniLM-L6-v2; sentences rejoined with spaces; `boundary_similarity` kept | `backend/app/services/chunking_service.py:70, 86, 94, 106` |
| L21 | Tests section paths | corrected: `tests/...` → `backend/tests/...`, `requirements.txt` → `backend/requirements.txt` | `backend/tests/test_chunking.py:2, 4-29`; `backend/requirements.txt:14-15` |
| L21 | NLTK data in tests | added: `punkt` is fetched only in the startup event (runtime effect UNVERIFIED) | `backend/app/main.py:46-57` |
| L21 | Concept IDs | corrected: added I-CMP (counter-example), since chunkers are compared with no retrieval metric | `backend/app/services/chunking_service.py:205-228` |
| L21 | What to take | added: local MiniLM for boundaries; keep the stored boundary similarity | `backend/app/services/chunking_service.py:70, 94` |
| L21 | Interview | confirmed | n/a |
| L22 | How it works, steps 1–7 | confirmed; step 1 extended (UI asks for `top_k` 5) | `backend/main.py:58-181`; `frontend/src/components/RerankingDashboard.js:30-34` |
| L22 | Raw logits, no sigmoid | re-confirmed | HF cache `models--cross-encoder--ms-marco-MiniLM-L-6-v2/.../config.json:30` (`Identity`) |
| L22 | README error-handling bullet had no file:line | corrected (cite added) | `backend/main.py:92-121` |
| L22 | README "Batch reranking support" | added: `/batch-rerank` is a sequential loop | `README.md:33`; `backend/main.py:158-166` |
| L22 | Cache-key bug | extended: key omits the model id; Redis persists on a named volume | `backend/main.py:98-99`; `docker-compose.yml:6-8, 33-34` |
| L22 | Silent cache-off | added [misleading]: Redis pinged once at import; `test.sh` ticks caching anyway | `backend/main.py:34-41`; `test.sh:110` |
| L22 | Missing `text` fallback | added [bug]: the dict's string form is scored | `backend/main.py:116` |
| L22 | Concept IDs | corrected: added D4 (counter-example) | `backend/main.py:26` |
| L22 | What to take | added: split hit/miss latency; local reranking keeps book text on your machine; hosted rerank only on non-book text, cached | n/a (advice) |
| L22 | Hard-coded key | confirmed at `backend/main.py:26`; value not in the guide | grep for the Google key prefix over lessons 19–23 (1 hit, excluding `node_modules`); same grep over this guide: 0 hits |
| L22 | Interview | confirmed | n/a |
| L23 | How it works, steps 1–8 | confirmed; step 4 extended (redundant Python post-filter after a simple filter) | `backend/main.py:82-307, 321-399`; `backend/main.py:234` |
| L23 | Both legs never work together | added [bug]: key → dimension mismatch; no key → dummy vectors; key added later → inserts and vector query fail (Chroma check UNVERIFIED) | `backend/main.py:182-198, 220-230, 330-350` |
| L23 | "Hybrid" label | added [misleading]: `rank_source` hard-coded; `/` advertises `keyword_search` | `backend/main.py:317, 372, 375` |
| L23 | Concept IDs | corrected: R1 marked as RRF real, sparse leg a counter-example | `backend/main.py:147-159, 200-254` |
| L23 | What to take | added: Cohere input types, caching and a separate MiniLM index; per-leg hit counts; LangChain wrapper only after plain-Python tests | `README.md:109-110`; `backend/main.py:372, 375` |
| L23 | Interview (RRF, k) | confirmed (k = 60: rank 1 in one list gives 1/61; rank 5 in both gives 2/65, which is larger) | arithmetic |
| All | Secrets in L19, L20, L21, L23 | none found | grep for the Google key prefix and for literal `api_key =` assignments over each lesson |
| Summary | Block summary concepts and "Biggest problem" | corrected to match the lesson headers above | rows above |
| Cross | Two new patterns (labels that over-claim; stale index or cache entries) | added, each with file:line | rows above |

Tally (pass B): 85 items checked. 58 confirmed, 14 corrected, 0 removed. 23 additions: 13 new verified findings, 8 new "What to take" bullets and 2 cross-lesson patterns. No API key value appears in this guide; the only hard-coded key is reported by location (L22 `backend/main.py:26`).
