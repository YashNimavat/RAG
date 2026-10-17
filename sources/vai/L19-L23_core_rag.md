# VAI lessons 19–23: core RAG

[← Guide index](README.md) · Course folder: `C:\Yash\New-Work\RAG\vertical-ai-agents-main\` · Checked 2026-10-17 · Log: [verification/L19-L23_core_rag_log.md](verification/L19-L23_core_rag_log.md)

**What this is:** the guide to VAI lessons 19–23, the five lessons closest to your v0 → v2 pipeline.
**What this is not:** the course code, or a run of it. Nothing in the course was run or copied.

**How to read this file:**
- A `file:line` is relative to the project folder named in the lesson heading.
- **UNVERIFIED** marks behaviour that depends on a library version or on Gemini.
- **(counter)** or † means the lesson names a technique without building it. Read it to learn what is missing.
- Tags: **[bug]** the code does the wrong thing · **[misleading]** a label, message or number claims more than the code does · **[shallow]** it works, but is too thin for your project · **[ok-for-demo]** fine for a demo, not for real use · **[LLMOps]** material for your LLMOps notebooks · **[Interview]** worth practising for interviews.
- "I" means the reviewer who checked the code. Each lesson was checked by a reader, a fact-check pass and a completeness pass; the log has every verdict.

**Notes for this block:**
- Your earlier modified copies in `Book RAG\prior_work\VAI\lesson19\` to `lesson23\` were compared with `diff`; each lesson notes what you changed.
- These five lessons map most directly onto your v0 → v2 versions. Read them alongside Phases 1, 2 and 5.

---

## L19 · Naive RAG with keyword retrieval  (`lesson19/l19-naive-rag/`)

**What the code teaches, in one line:** The bare retrieve-then-generate loop. Text is cut into 500-character pieces, the pieces that share words with the question are found, and they are pasted into one prompt for Gemini.
**What it is not:** It is not vector search (there are no embeddings), and it is not BM25 or TF-IDF. The "keyword index" counts how many question words a chunk shares, with no term frequency, no IDF and no length normalisation. It keeps no page numbers and does not check citations.
**Relevance to your RAG study:** High. Concepts: C1, C2, C5 (source labels, but no citations), C6, P2 (inverted index), P3 (as the "before BM25" baseline), P7 (a one-sentence grounding prompt), V3 (zero-hit abstain only). [LLMOps: per-stage latency only] [Interview]
**Stack:** FastAPI 0.115, `google-generativeai` 0.8.3, PyPDF2 3.0.1 (`backend/requirements.txt:1-9`). LLM: Gemini, through a fallback list of 9 model ids that starts with `gemini-2.0-flash-lite` and ends with `gemini-flash-latest` (`backend/query_engine.py:15-25`). No embeddings. The store is plain Python dicts in memory (`backend/knowledge_base.py:8-16`). The React 18 frontend shows stat tiles (polled every 3 s), an upload button, a question box, the answer with timings, and the retrieved chunks with their integer score (`frontend/src/App.js:16-17, 61-63, 182-187`).
**Swap to your stack:** easy. There is one provider call, `model.generate_content(prompt)` (`backend/query_engine.py:134`). Replace it with a Groq call and delete the model-fallback machinery.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/document_processor.py` | Cleans text, does fixed character chunking, extracts PDF text | 16-45, 47-53, 64-80 |
| 2 | `backend/knowledge_base.py` | Word → chunk index, overlap-count retrieval, stats | 18-44, 46-81, 83-90 |
| 3 | `backend/query_engine.py` | Builds the context, writes the prompt, retries and switches models | 84-120, 125-199, 203-221 |
| 4 | `backend/main.py` | Upload pipeline (only the end matters) and `/query` | 400-434, 469-495 |
| 5 | `tests/test_rag_system.py` | 3 unit tests | 7-41 |
| 6 | `data/sample_doc1.txt`, `data/sample_doc2.txt` | Two tiny practice documents | whole files |

You can skip `main.py:46-399`, which is mostly UTF-8/PDF detection wrapped in debug prints. You can also skip `backend/decode_instrumentation.py`: grep finds no import of it anywhere, so it is dead code.

### How it works, step by step
1. **Upload.** `/documents/upload` reads the bytes. It decides "PDF" if the magic bytes, the extension or the content type says so (`main.py:174-196`). PDF pages are extracted with PyPDF2 and joined with blank lines (`document_processor.py:64-78`). Text files must end in `.txt`, `.md` or `.mdx` (`main.py:234`).
2. **Clean.** `preprocess_text` turns every run of whitespace into one space (`document_processor.py:50`). It then deletes every character that is not a word character, a space or one of `. , ! ? ; : - ( )` (`document_processor.py:52`). Paragraph breaks, page breaks, quotes, `/ % + = # $` all disappear.
3. **Chunk.** The chunker uses fixed windows of 500 **characters** and moves 450 characters each step, so neighbouring chunks overlap by 50 characters (`main.py:27`; `document_processor.py:25-43`). It cuts mid-word. Each chunk keeps its character offset in the *cleaned* text (`position`) and an extra `next_overlap` field holding the 50 characters after it. Nothing uses that field for retrieval (`document_processor.py:32-40`; `knowledge_base.py:31`).
4. **Index.** `doc_id` is the filename with spaces and dots replaced by `_` (`main.py:424-425`). Chunk ids are the doc id plus `_chunk_<i>` (`knowledge_base.py:23`). Each chunk's set of words goes into an inverted index that maps a word to the ids of the chunks containing it (`knowledge_base.py:35-38`). The tokeniser lower-cases, turns punctuation into spaces, keeps words longer than 2 characters and drops 16 stopwords (`knowledge_base.py:83-90`).
5. **Retrieve.** The question goes through the same tokeniser. A chunk's score is the number of *distinct* question words it contains (`knowledge_base.py:54-58`). Results are sorted and the top 3 are kept (`knowledge_base.py:61-65`; the frontend always sends `top_k: 3`, `App.js:63`). There is no explicit tie-break rule. Tied chunks keep whatever order the word sets produced, and Python randomises string hashing per process, so that order can change between restarts.
6. **Abstain early.** If no chunk shares a single word with the question, the engine returns a fixed "I don't have enough information" answer and never calls the LLM (`query_engine.py:97-104`).
7. **Prompt.** Chunks are labelled `[Source 1]`, `[Source 2]`, and so on (`query_engine.py:107-110`). The prompt is one instruction sentence (answer from the context, and say so if the context does not contain the answer), then the context, then the question, then "Answer:" (`query_engine.py:113-120`). There is no system prompt, no temperature, no max-tokens limit and no request to cite the `[Source N]` labels.
8. **Generate with retries.** It makes up to 3 attempts. On a 429 or quota error it normally switches to the next model and waits only 0.5 s. It sleeps longer only when it cannot switch. That sleep is doubled up to a 30 s cap, but if the error text contains a "retry … N seconds" hint, it waits N + 0.5 s with no cap (`query_engine.py:125-178`). Other errors also switch model (`query_engine.py:185-194`). Auth errors stop at once, but only "401" or "403" in the message is detected. The "API key" test compares against lower-cased text, so it can never match (`query_engine.py:180-183`). The switch is remembered, so later questions start on whichever model was selected last (`query_engine.py:69-82`). Which model answers therefore depends on earlier errors.
9. **Return.** The response holds the answer, each chunk's id, its first 200 characters and its score, plus retrieval, generation and total milliseconds (`query_engine.py:203-218`). Results are also kept in an in-memory history (`query_engine.py:220`).

### README vs code
- The README says "keyword indexing" (`README.md:27`). That is true, but it is set-overlap counting, not BM25 or TF-IDF (`knowledge_base.py:54-58`).
- The README says "LLM: Google Gemini 2.0 Flash" (`README.md:37`). The code tries `gemini-2.0-flash-lite` first and may quietly use any of 9 models (`query_engine.py:15-25`). The response does not say which model answered.
- The README gives performance numbers: under 50 ms retrieval, about 1,000 chunks/s ingestion, under 500 ms end to end (`README.md:28, 49-51`). No benchmark code exists. UNVERIFIED.
- The README says "Complete test suite" (`README.md:31`). There are 3 small unit tests, and the integration test is an empty `pass` (`tests/test_rag_system.py:43-45`).
- The README says "production-ready" (`README.md:3`). Storage is in memory only, so everything is lost on restart (`knowledge_base.py:8-16`).

### Where it is thin or wrong
- [bug] **Duplicate tail chunk.** When the text ends inside the 50-character overlap of the previous chunk, the last window is a tiny chunk wholly contained in the one before it (`document_processor.py:25-43`). A 480-character text gives 0–480 and 450–480. The test treats this as correct. With its own settings (`chunk_size=100, overlap=20`, `tests/test_rag_system.py:8`), 250 characters give 4 chunks, and the last is only 10 characters long (`tests/test_rag_system.py:13-17`).
- [bug] **Cleaning destroys technical text.** `C++` becomes `C`, `3%` becomes `3`, and URLs, code, formulas and quotes are mangled because `/ % + = # $` and quote marks are deleted (`document_processor.py:52`). That is bad for "technical PDFs".
- [shallow] **Page numbers are lost.** Pages are joined, whitespace is collapsed, and a chunk keeps only an offset into the cleaned text (`document_processor.py:78, 50`; `knowledge_base.py:26-33`). You cannot cite "page 3".
- [shallow] **Rare words count no more than common ones.** A chunk sharing "what" scores the same as one sharing "RAG". "what", "how", "does" and "this" are not stopwords (`knowledge_base.py:88`). Two-letter terms such as "AI" or "ML" are always dropped by the "longer than 2" rule (`knowledge_base.py:89`).
- [bug] **Re-uploading a file corrupts the index.** Uploading the same filename again overwrites the chunk texts but leaves old index entries in place, so a chunk can still match words it no longer contains. If the new version has fewer chunks, the old higher-numbered chunks stay in the store. `chunk_counter` keeps growing, so `total_chunks` double-counts (`knowledge_base.py:23-43`).
- [misleading] **Errors come back as answers with HTTP 200.** Quota, auth and other errors become the `answer` string (`query_engine.py:177, 182, 193`; `main.py:482-495`). An eval run would grade error text as if it were an answer.
- [misleading] **"All available models have been tried" is not true.** The loop makes at most 3 attempts (`query_engine.py:125, 128`), so at most 3 of the 9 models are tried. The final quota message still says all of them were (`query_engine.py:177`).
- [shallow] **The abstain branch rarely fires.** It fires only when no chunk shares a single word with the question (`query_engine.py:97-104`). Question words such as "what", "how" and "does" are not stopwords (`knowledge_base.py:88`), so any chunk that contains "what" counts as a hit. The LLM is then called with unrelated chunks, and abstention rests on the model obeying the prompt. (Reasoned from the code; not run.)
- [bug] **Non-English text files are rejected.** A file with mostly non-ASCII text (for example Gujarati or Hindi) has under 70% printable ASCII bytes, so it is classed as "binary" (`main.py:76-81`).
- [bug] **The local start path breaks.** `start.sh` runs `python main.py` inside `backend/` (`start.sh:37`), but `main.py` imports `backend.knowledge_base` (`main.py:10-12`) and PYTHONPATH is not set there. The Docker path works because the Dockerfile sets `PYTHONPATH=/app` (`Dockerfile:14`).
- [ok-for-demo] Every upload prints debug output with stack traces (`main.py:93-99, 258-264, 292-298`).
- Note: the generated folder was hand-edited after `setup.sh` ran. `setup.sh` still uses a single `gemini-2.0-flash-exp` model (`setup.sh:214`). Read the folder, not `setup.sh`.

### Tests and data
- `test_document_chunking` checks chunk count and positions for 250 "A"s, using chunk size 100 and overlap 20, not the app's 500/50 (`tests/test_rag_system.py:7-17`). It asserts the duplicate tail as correct behaviour.
- `test_knowledge_base_indexing` checks only the chunk count (`tests/test_rag_system.py:19-28`). `test_keyword_retrieval` checks only that the top score is above 0, not which chunk wins (`tests/test_rag_system.py:30-41`).
- `test_demo.sh` uploads both sample docs and asks "What is RAG?" and "What are chunking strategies?" (`test_demo.sh:51, 59`). It then only checks that the counters are non-zero (`test_demo.sh:71-86`). It never checks an answer.
- `data/sample_doc1.txt` (RAG intro, 11 lines, about 830 bytes) and `data/sample_doc2.txt` (chunking strategies, 13 lines, about 830 bytes) make a two-document toy corpus. Each gives only 2 chunks at 500/50. They are fine for checking by hand, too small for any metric, and for local study only.

### What to take for your project
- Re-implement the skeleton in plain Python as your C6 baseline: load → chunk → index → retrieve → prompt. Fix three things: store the offset into the *original* text plus the page number (C1/C3), drop a tail chunk that sits wholly inside the previous one (C2), and do no destructive cleaning.
- Keep the early-abstain idea (no hits means no LLM call) for V3, but base it on a score threshold, not on "zero shared words".
- Keep this overlap-count scorer as your weakest lexical baseline when you build BM25 (P3). The gap between the two on the same questions makes a good first M4 experiment.
- Keep per-stage timing (retrieval ms vs generation ms) in your trace (D1/D2), but return errors as errors, not as answers.
- Replace the one generation call (`query_engine.py:134`) with a single Groq call to `openai/gpt-oss-20b`, with `reasoning_effort="low"` and enough `max_tokens` (a reasoning model spends tokens before it answers). Drop the 9-model fallback. Put the call behind your record/replay cache, keyed on model id plus a hash of the prompt. Log the model id with every answer; L19 never reports it (`query_engine.py:203-218`).
- Ask the model to cite the `[Source N]` labels, and add a check that every cited label exists among the chunks you sent (C5, V1). L19 labels the chunks but never asks for citations (`query_engine.py:107-120`).
- Any step that calls Groq or Cohere must use a non-book corpus, for example the climate-change PDF that your acceptance suite already uses. Book text must not go to external APIs.
- Your earlier copy has the same backend; only `docker-compose.yml` changed.

### Try this
- 20 minutes, in a notebook, writing your own code from the description above (do not copy the file). (1) Write the 500/50 character chunker and run it on a 480-character string and on `sample_doc2.txt`. Count the chunks that sit wholly inside their predecessor. You should find 1 for the 480-character string and 0 for `sample_doc2.txt` (about 830 characters, which does not end inside an overlap). Try a 920-character string to see the duplicate again. (2) Write the overlap-count scorer with the same 16 stopwords. Ask "What is RAG?" against both sample docs and print every chunk's score. Look for "what" scoring like a content word, and look for ties. (3) Multiply each matched word by `log(N / df)` and watch the ranking change. That one step takes you from this lesson to TF-IDF and BM25.

### Interview angle
- Q: "Your naive RAG returns irrelevant chunks for short questions. Why can keyword overlap fail, and what does BM25 add?"
  A: Overlap counting treats every shared word the same, so common words such as "what" or "system" decide the ranking, and long chunks win just by having more distinct words. This scorer also ignores how often a word appears. BM25 gives rare terms more weight (IDF), lets repeated terms count with diminishing returns (k1), and corrects for chunk length (b).

---

## L20 · Vector database with ChromaDB  (`lesson20/l20-vector-databases/`)

**What the code teaches, in one line:** Dense indexing done properly in its basics. It chunks text, embeds documents and queries with *different* task types, stores everything in a persistent Chroma collection set to cosine space, and turns distance into similarity correctly.
**What it is not:** There is no answer generation (this is retrieval only), no file upload or PDF parsing (only raw JSON text), no page metadata and no evaluation. Metadata filtering exists in the API, but the UI never uses it.
**Relevance to your RAG study:** High. Concepts: P4, P5, C3, C4, R2. [Interview]
**Stack:** FastAPI 0.109, `chromadb` 0.4.22, `google-generativeai` 0.4.0, `numpy<2` (`backend/requirements.txt:1-11`). Embeddings: `models/text-embedding-004` (`backend/embedding_service.py:11`); that model returns 768-dim vectors, a model fact the code never states or checks. The code does not normalise vectors itself, and it does not need to, because the space is cosine. Store: `chromadb.PersistentClient` at `./data/chromadb` with `hnsw:space` = `cosine` (`backend/vector_store.py:10-16, 20-27`). No LLM call. The Vite React UI has an index panel (source + text), a search panel showing "% match" (similarity × 100), and stats polled every 2 s (`frontend/src/App.jsx:17-53, 102-105`; `frontend/src/components/SearchPanel.jsx:33-36`).
**Swap to your stack:** easy. Swap `EmbeddingService` for Cohere `embed-v4.0`, mapping `retrieval_document`/`retrieval_query` to Cohere's `search_document`/`search_query` input types. The dimension changes, so delete the collection and re-index.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/vector_store.py` | Chroma client, collection with cosine space, add, query with `where` | 10-27, 29-44, 46-60 |
| 2 | `backend/indexing_pipeline.py` | Chunk → embed → metadata → store | 13-23, 25-74 |
| 3 | `backend/embedding_service.py` | Gemini embeddings, document vs query task type, fail-fast | 14-84, 86-106 |
| 4 | `backend/search_engine.py` | Query embed → Chroma query → distance to similarity | 11-42 |
| 5 | `backend/main.py` | `/index`, `/search`, `/stats`, delete collection, websocket | 47-108, 134-142 |
| 6 | `test.sh`, `clear-collection.sh` | curl smoke test, collection reset | whole files |

### How it works, step by step
1. **Index request.** `POST /index` takes `text`, `source`, `collection` (default `"default"`) and an optional `metadata` dict (`main.py:53-57, 59-70`).
2. **Chunk.** `chunk_document` uses 500 **characters** with a 50-character overlap (step 450). It skips whitespace-only chunks (`indexing_pipeline.py:13-23`). The request cannot change these numbers, because `index_document` never passes them (`indexing_pipeline.py:34`). It has the same duplicate-tail behaviour as L19.
3. **Embed documents.** One `embed_content` call per chunk, run concurrently with at most 10 in flight (`embedding_service.py:17-60`), using task type `retrieval_document` (`embedding_service.py:14, 24`). If any chunk fails, the whole document fails (`embedding_service.py:64-67`). That is good: there are no silent fake vectors.
4. **Metadata and ids.** Each chunk gets the user's metadata, then `source`, `chunk_index`, `chunk_total`, `indexed_at`, `chunking_strategy="character"` and `chunk_size` (`indexing_pipeline.py:49-57`). The id is an MD5 of source + index + the first 50 characters (`indexing_pipeline.py:46`). There is no page and no character offset.
5. **Store.** `collection.add` writes documents, embeddings, metadata and ids (`vector_store.py:38-43`). The collection is created with cosine space (`vector_store.py:24`).
6. **Search.** `POST /search` takes `query`, `n_results` (default 10; the UI sends 5) and `filters` (`main.py:47-51`; `App.jsx:105`). The query is embedded with task type `retrieval_query` (`embedding_service.py:93`). The filters are passed as Chroma's `where`, so filtering happens inside the vector query (`search_engine.py:23-28`; `vector_store.py:54-58`).
7. **Score.** Chroma returns cosine *distance*. The code reports both `distance` and `similarity = 1 − distance` (`search_engine.py:31-39`). That is correct for cosine space.

### README vs code
- The README tells you to run `./set-api-key.sh` (`README.md:8`). That script does not exist in the folder.
- The README promises "Real-time WebSocket updates" (`README.md:35`). The backend has a `/ws` endpoint (`main.py:144-190`), but the frontend uses HTTP polling, and a comment there says so (`App.jsx:18`).
- The README says "Batch embedding with Gemini API" (`README.md:41`). The code sends one request per chunk, concurrently (`embedding_service.py:15, 50-60`). The original `setup.sh` did real batches of 100, but returned zero vectors on failure (`setup.sh:129-162`); the generated folder was rewritten after that.
- The README says "Semantic search with metadata filtering" (`README.md:42`). Filtering is there in the API (`search_engine.py:27`), but no UI control sends filters (`App.jsx:105`).
- The README says "Production-ready error handling" (`README.md:44`). See the next section.

### Where it is thin or wrong
- [misleading] **Wrong error message.** Any error whose text contains "invalid", "expired", "api key" or "api_key" is reported as "API key expired or invalid" with HTTP 503 (`main.py:77-82, 102-107`). Any other failure whose message happens to use the word "invalid" is blamed on the key. Whether a bad `where` filter's Chroma error uses that word depends on Chroma's wording (UNVERIFIED).
- [shallow] **No provenance beyond the chunk index.** There is no page and no character offset (`indexing_pipeline.py:49-57`), so you cannot point to where an answer came from. The `chunk_size` field holds the chunk's actual length, not the configured size (`indexing_pipeline.py:56`).
- [misleading] **"% match" is not a percentage of anything.** The UI shows cosine similarity × 100 (`frontend/src/components/SearchPanel.jsx:33-35`; `backend/search_engine.py:38`). Cosine similarity is not a probability of relevance and is not calibrated across queries. In cosine space it can even be negative. Do not read "65% match" as "65% relevant", and do not set thresholds that way.
- [shallow] **Edited documents leave stale chunks.** Each id hashes the first 50 characters of its chunk (`indexing_pipeline.py:46`). After an edit, the changed chunks get new ids and are added, and the old chunks stay. Nothing deletes by `source`; the only delete removes the whole collection (`vector_store.py:75-79`; `main.py:134-142`). Search can then return the old and new versions side by side.
- [shallow] **Re-indexing does not update.** Re-indexing the same text gives the same ids, because the id hashes source, index and the first 50 characters, not the time (`indexing_pipeline.py:46`). The code calls `add`, not `upsert` (`vector_store.py:38`). In Chroma 0.4.x, `add` on an existing id is expected to log a warning and skip the record, not overwrite it (library behaviour, UNVERIFIED here). Use `upsert` if you want updates.
- [shallow] **The metric shown is a label, not a reading.** `get_stats` always reports `distance_metric: "cosine"` and `index_type: "HNSW"` (`vector_store.py:68-69`), and the stats panel displays it (`frontend/src/components/StatsPanel.jsx:17`). It never reads the collection's real `hnsw:space`.
- [ok-for-demo] User metadata goes straight into Chroma (`indexing_pipeline.py:50`). Chroma accepts only flat str/int/float/bool metadata values, so a nested dict or list would make `add` fail (library behaviour, UNVERIFIED here).
- [ok-for-demo] `clear-collection.sh` deletes the `default` collection so you can "re-index … with proper embeddings" (`clear-collection.sh:5-8`; endpoint comment at `main.py:136`). A model change is one case that needs it. Chroma fixes a collection's dimension at its first insert, so vectors from a model with another dimension cannot be mixed in (library behaviour). This is a real lesson worth noting (D3, index versioning).

### Tests and data
- There are no unit tests. `test.sh` indexes one sentence, searches "What is machine learning?" with `n_results: 3`, and prints stats (`test.sh:26-39`). It asserts nothing about results.
- There is no data folder. You have to paste the text you index.

### What to take for your project
- Re-implement in plain Python and NumPy first (C3/C4, P5). Keep a matrix of unit-normalised vectors, use dot product as cosine similarity, and take the top k with `argpartition`. Then use Chroma as the "real" store and check that its `1 − distance` equals your NumPy cosine for the same query.
- Copy the *design* points. Use asymmetric task types for documents and queries (Cohere's `search_document`/`search_query`). Fail fast on embedding errors instead of storing zero vectors. Set `hnsw:space` explicitly and store the embedding model id in collection metadata, so a model swap forces a re-index (D3).
- Add what is missing: page, character offsets and `snapshot_id` in chunk metadata, plus a metadata filter test (R2) in which a filter really removes a document.
- Put every `embed-v4.0` call behind your record/replay cache, keyed on model id, `input_type` and a hash of the text, so a re-index costs nothing on replay. Keep the local MiniLM fallback in its own collection or matrix. Never mix vectors from two models in one index.
- Before you re-index a document, delete its old chunks by `source` (or by `snapshot_id`), then add the new ones. L20 has no such step (`vector_store.py:75-79`). Add a test: index, edit, re-index, and assert that the chunk count for that source did not grow.
- Your earlier copy changes the model to `models/gemini-embedding-001` and bumps `google-generativeai` to 0.8.3. Note that the new model's vectors have a different dimension, which is exactly why `clear-collection.sh` exists.

### Try this
- 25 minutes. Use local MiniLM (sentence-transformers) and `chromadb`. Create two collections over the same 10 chunks: one with default settings (Chroma's default space is squared L2) and one with `hnsw:space="cosine"`. Use normalised embeddings. For one query, print `distance` and `1 − distance` from both collections next to your own NumPy cosine. You should see that under cosine, `1 − d` equals your cosine. Under L2, `d = 2 − 2·cos`, so `1 − d` gives the wrong number, and the ranking still matches.

### Interview angle
- Q: "Chroma returns 0.35 for your top hit. Is that a good match?"
  A: That number is a distance, not a similarity, and what it means depends on the space. In cosine space, similarity is 1 − 0.35 = 0.65. Under Chroma's default squared L2 with unit vectors, cosine = 1 − d/2 = 0.825. Always set or read `hnsw:space` before you convert distances or set thresholds.

---

## L21 · Chunking strategies and embedding models lab  (`lesson21/l21-advanced-embeddings/`)

**What the code teaches, in one line:** Five chunkers side by side (fixed, embedding-boundary "semantic", paragraph/sentence "recursive", sliding window, N-sentence groups), each embedded with three models, and compared on chunk-size statistics and a "coherence" number.
**What it is not:** It has no retrieval and no search endpoint at all, so nothing here tells you which chunker retrieves better. There is no token-based chunking: `tiktoken` is in the requirements but never imported. ChromaDB is effectively never used (see below).
**Relevance to your RAG study:** Medium-High. Concepts: C2, I1, I3, P4, I-CMP (counter-example: it compares chunkers without any retrieval metric). [Interview]
**Stack:** FastAPI 0.111, `sentence-transformers` 2.7.0, `nltk` 3.8.1 (punkt), `scikit-learn` cosine, `chromadb` 0.5.0, `google-generativeai` 0.5.4 (`backend/requirements.txt:1-15`). The three embedding models are listed in `embedding_service.py:39-58`: `all-MiniLM-L6-v2` (384-dim, loaded once, `embedding_service.py:26`), Gemini `models/embedding-001` (768-dim, `embedding_service.py:92`) and `paraphrase-MiniLM-L3-v2` (384-dim, reloaded on every call, `embedding_service.py:108`). The code never normalises vectors itself. `all-MiniLM-L6-v2` already outputs unit vectors through its own `Normalize` module; `paraphrase-MiniLM-L3-v2` has none (both from the model configs in your local Hugging Face cache, not from this repo). It does not matter here, because sklearn's `cosine_similarity` normalises anyway. There is no LLM. The React UI lets you paste text, run one strategy (with the defaults in `App.js:75-84`), and "Compare" all strategies × all models (it sends empty `params`, so the backend defaults apply, `App.js:62-67`). The bar chart draws only chunk count and coherence, for the first model only. Average size is computed for it but never drawn (`frontend/src/App.js:89-97, 109-110`). Cards below show chunks, average size and coherence % for every model (`App.js:199-227`).
**Swap to your stack:** easy. MiniLM is already your local fallback. Drop Gemini, or add Cohere `embed-v4.0` as a fourth option.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/app/services/chunking_service.py` | All 5 chunkers plus the metrics | 33-54, 56-114, 116-157, 159-183, 185-203, 205-228 |
| 2 | `backend/app/services/embedding_service.py` | 3 embedding back-ends, zero-vector fallback | 60-114 |
| 3 | `backend/app/main.py` | `/chunk`, `/embed`, `/compare`, `/upload`, NLTK download | 46-60, 74-217 |
| 4 | `backend/app/services/vector_service.py` | Chroma setup (broken) and store (write only) | 18-59 |
| 5 | `backend/tests/test_chunking.py` | 2 tests | 4-29 |
| 6 | `frontend/src/App.js` | Default params per strategy | 75-84 |

### How it works, step by step
Follow one `POST /compare` call: one text, all strategies, all models (`main.py:125-184`).
1. **NLTK punkt** is downloaded at startup (`main.py:49-57`). Sentence splitting everywhere is `nltk.sent_tokenize`.
2. **fixed:** 500 **characters**, overlap 50 (`chunking_service.py:35-52`). `end_pos` is not clamped to the text length (`chunking_service.py:42, 47`). It has the L19 duplicate-tail behaviour, and an overlap of at least `chunk_size` would loop forever.
3. **semantic:** split into sentences, embed each sentence with MiniLM (reloaded on every call, `chunking_service.py:70-71`), and compare only *adjacent* sentences. If their cosine is below `threshold` (default 0.5) *and* the current chunk is at least `min_chunk_size` (100 characters), start a new chunk; otherwise keep appending (`chunking_service.py:60-102`). There is no maximum size, so a long run of similar sentences becomes one huge chunk. `start_pos` is computed as if the chunks were joined by single spaces, so it is not a true offset in the original text (`chunking_service.py:97`).
4. **recursive:** if the text is over `max_size` (1,000 characters), split on blank lines. A single paragraph is split by cutting its sentence list in half (`chunking_service.py:118-157`). The `overlap` parameter (200) is read and never used (`chunking_service.py:119`). Small paragraphs are never merged. `children` is always empty, so it is hierarchical in name only (`chunking_service.py:127, 152`).
5. **sliding_window:** a 500-character window with a 250-character stride, which is 50% overlap and stops cleanly at the end (`chunking_service.py:159-183`).
6. **sentence:** 3 sentences per chunk, no overlap. `start_pos` and `end_pos` here are *sentence indices*, not character positions (`chunking_service.py:187-199`).
7. **Embed** every chunk with each model (`main.py:154-157`). If a Gemini call fails, a zero vector of length 768 is inserted silently (`embedding_service.py:97-100`).
8. **Metrics:** count, mean, std, min and max chunk length in characters, plus `coherence_score`, the *mean cosine between consecutive chunk embeddings* (`chunking_service.py:205-228`).
9. **`/upload`** (separate) decodes the file as UTF-8 (`main.py:197`), so a PDF raises a decode error that the global handler turns into HTTP 500 (`main.py:30-39`). It chunks text semantically with threshold 0.5 and calls `store_document` (`main.py:200-211`).

### README vs code
- The README lists "5 chunking strategies" (`README.md:29`). All 5 exist, but "recursive" ignores its overlap and loses positions, and "semantic" has no size cap.
- The README says "ChromaDB integration (builds on L20)" (`README.md:32`). `chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", ...))` (`vector_service.py:24-27`) is the configuration removed in Chroma 0.4. Chroma 0.5.0 is very likely to reject it with a ValueError. The same "deprecated configuration" check that has existed since 0.4 is present in the Chroma 1.5.x copy installed on your machine, but 0.5.0 itself was not checked (UNVERIFIED). The error is caught and printed as a warning (`vector_service.py:37-38`). When that happens, the client stays `None` (it is assigned only on success, `vector_service.py:15, 24`), so `/upload` always fails with "ChromaDB is not available. Please install chromadb" (`vector_service.py:42-43`), which is a misleading message. Even if it worked, `add` passes no embeddings, so Chroma would use its own default embedder with default L2 space, and the model you chose would be ignored (`vector_service.py:53-57`). Nothing ever queries it.
- The README says "Quality metrics" (`README.md:33`). These are size statistics plus a neighbour-similarity number. They are not retrieval quality.
- The README says "3 embedding models" (`README.md:30`). True, but Gemini failures turn into zero vectors with no error.

### Where it is thin or wrong
- [misleading] **`coherence_score` does not measure chunk quality** (`chunking_service.py:212-219`). It measures how similar *neighbouring* chunks are, so strategies with overlap (sliding window at 50%) score high by construction, and a perfect topic-splitter scores *low*. Your earlier note contradicts itself on this: it says high coherence means focused chunks (`prior_work/VAI/lesson21/l21-advanced-embeddings/LESSON_EXPLANATION.md:55`) and later that low coherence is what you want (`LESSON_EXPLANATION.md:160`). The "~0.30" there (`LESSON_EXPLANATION.md:153`) is not from a logged run, and the "core insight" that chunking beats the model (`LESSON_EXPLANATION.md:194`) is not tested by any code here.
- [bug] **The recursive chunker can recurse forever.** Take a single "sentence" over 1,000 characters (a table, a code block, or text without full stops). Halving a one-item sentence list gives an empty left half and the same text on the right, so the call repeats until Python's RecursionError (`chunking_service.py:133-140`). The whole request then fails (`/chunk` returns HTTP 400, `main.py:101-105`). In `/compare` the error is caught for that one strategy (`main.py:178-182`), but the UI then breaks (next bullet). Separately, text that starts or ends with blank lines produces an empty paragraph, and that becomes an empty chunk (`chunking_service.py:131, 144-153`).
- [bug] **One failing strategy breaks the comparison view.** For a strategy that raised, `/compare` returns only an `error` string (`backend/app/main.py:182`). The chart and the cards then read `.chunks.length` from that string, which throws in the browser (`frontend/src/App.js:90-93, 209`). With no error boundary, React is expected to unmount the page (React behaviour, not run).
- [bug] **The recursive chunker loses positions.** `start_pos` is 0 for every chunk (`chunking_service.py:125, 150`), so it cannot cite.
- [shallow] **"Semantic × model" mixes two models.** Boundaries always come from all-MiniLM-L6-v2 (`chunking_service.py:70`), whichever embedding model you compare afterwards. Semantic chunks also rejoin sentences with single spaces (`chunking_service.py:86, 106`). Newlines are lost, so a chunk's text is not an exact substring of the input. The code does keep each boundary's similarity in chunk metadata (`chunking_service.py:94`), which is the useful part.
- [bug] **The Gemini fallback fakes success.** It returns zero vectors (`embedding_service.py:97-100`), so coherence quietly becomes 0. Your earlier copy removed this fallback and raises instead, which is the right fix.
- [shallow] **Silent truncation at embedding time.** MiniLM-L6 reads at most 256 word-pieces and paraphrase-MiniLM-L3 at most 128. These are `max_seq_length` in the models' own configs (checked in your local Hugging Face cache), not set in this code. Long uncapped "semantic" chunks can therefore be cut off when embedded. With the L3 model, even 500- to 1,000-character chunks may lose their tail. How many characters fit depends on the text, so no exact cut-off is claimed here.
- [shallow] **Positions use mixed units.** Characters for fixed and sliding, sentence index for sentence, fake offsets for semantic, 0 for recursive. You cannot compare positions across strategies.
- [ok-for-demo] Sentence-transformer models are reloaded on each semantic or lightweight call (`chunking_service.py:70`; `embedding_service.py:108`).

### Tests and data
- `test_semantic_chunking` checks only that 1 or more chunks come back with a `text` key (`backend/tests/test_chunking.py:4-16`). `test_recursive_chunking` checks that a 35-character text gives 1 chunk (`backend/tests/test_chunking.py:18-29`).
- `test.sh` runs plain `pytest` from `backend/` without PYTHONPATH (`test.sh:4-6`). `tests/` has no `__init__.py` or `conftest.py`, so the `from app...` import at `backend/tests/test_chunking.py:2` most likely fails at collection (UNVERIFIED, nothing was run; `start_backend.sh:4` does set PYTHONPATH, `test.sh` does not). Even with the import fixed, both tests are `@pytest.mark.asyncio`, and `pytest-asyncio` is not in the requirements (`backend/requirements.txt:14-15`), so pytest 8.2 would skip them with a warning (UNVERIFIED). Neither test checks boundaries, overlap or positions.
- The NLTK `punkt` data is downloaded only in the app's startup event (`backend/app/main.py:46-57`). The tests build `ChunkingService` directly and never trigger it, so on a machine without `punkt` the sentence splitter would fail (NLTK behaviour, UNVERIFIED).
- There are no data files.

### What to take for your project
- Re-implement these chunkers in plain Python for I1/I3, with three rules: one unit (decide characters or tokens and record it), true character offsets into the original text, and a hard maximum size for semantic chunks.
- Take the **adjacent-sentence cosine boundary** idea for I3, but add a percentile-based threshold instead of a fixed 0.5, plus min and max size, and log the boundary similarities so you can plot them (L21 already stores one per chunk, `chunking_service.py:94`).
- Run boundary detection with local MiniLM, as L21 does (`chunking_service.py:70`). Then chunking never needs an external call, and no document text leaves your machine at that stage. Load the model once, not per call.
- Replace "coherence" with retrieval metrics on your eval set (M2): recall@k and MRR per chunker, with everything else fixed (M4). Report the size distribution next to them. That is the I-CMP comparison.
- Skip the Chroma part and the Gemini path.

### Try this
- 25 minutes. Write your own fixed-size chunker and a neighbour-cosine "coherence" function with MiniLM. Use any text of 2 pages or more. `lesson19/.../data/sample_doc2.txt` is only about 830 characters, which gives just 2–4 chunks at size 500, too few for a stable mean. Compute coherence for overlap 0, 100 and 250 at size 500. Look for coherence *rising* with overlap even though the chunks are no better. That shows the number measures redundancy. Bonus (2 minutes): feed your own recursive splitter a 1,500-character string with no full stops and check that you guard against the infinite halving.

### Interview angle
- Q: "How would you choose between fixed-size and semantic chunking for a document set?"
  A: Not with an internal score such as neighbour similarity. Build a small labelled question set, index each chunking variant with the same embedder and k, and compare recall@k and MRR, then answer quality. Also check the chunk-size spread, because semantic chunking can make chunks longer than the embedder's input limit.

---

## L22 · Cross-encoder reranking service  (`lesson22/l22-reranking-system/`)

**What the code teaches, in one line:** How to rescore a candidate list with a cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`), cache the result in Redis for 24 h, and report p95/p99 latency.
**What it is not:** There is no first-stage retriever and no bi-encoder at all. The caller sends the candidates and their "original" scores. There is no LLM answer, and despite the README there is no link to L21's code.
**Relevance to your RAG study:** High for R3, Medium overall. Concepts: R3, D2, D4 (counter-example: a committed API key). [LLMOps] [Interview]
**Stack:** FastAPI 0.110, `sentence-transformers` 2.5.1 `CrossEncoder` (`backend/main.py:4, 45`), `redis` 5.0.1, torch 2.2.0 (`backend/requirements.txt:1-16`). `chromadb` is installed but never used. A Gemini model `gemini-pro` is configured with a **hard-coded literal Google API key** (`backend/main.py:26-28`; value not reproduced here) and never called. Redis comes from docker-compose (`docker-compose.yml:2-8`). The React dashboard reranks 10 hard-coded sample sentences with hand-typed scores from 0.68 to 0.86 (`frontend/src/components/RerankingDashboard.js:12-23`). It shows an "Improvement %" badge (`RerankingDashboard.js:102-104`), a bar chart of original vs reranked scores (`RerankingDashboard.js:61-64`) and a "compare" view.
**Swap to your stack:** easy. The cross-encoder runs locally on CPU with no API. Replace Redis with an in-process or disk cache that fits your record/replay caching. Cohere also offers a hosted rerank endpoint if you want one later.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/main.py` `/rerank` | Cache key, cross-encoder scoring, sort, top-k, "improvement" | 92-156 |
| 2 | `backend/main.py` `/metrics` | Request counts, cache hit rate, mean/p95/p99 latency | 168-181 |
| 3 | `backend/main.py` `/compare` | "Bi-encoder vs cross-encoder" (simulated) | 187-219 |
| 4 | `backend/main.py` setup | Key, Redis, model load | 25-56 |
| 5 | `test.sh` | curl script: rerank twice, metrics, compare | 35-112 |
| 6 | `frontend/src/components/RerankingDashboard.js` | Sample docs, chart mapping | 12-23, 61-64 |

### How it works, step by step
1. **Request.** `query`, `documents` (a list of dicts, each with optional `id`, `text`, `score`), `top_k` (default 10) and `use_cache` (`main.py:58-62`). The **pool size is whatever the caller sends**: 10 in the UI, 3 in `test.sh`. Nothing chooses it. The UI asks for `top_k` 5 (`RerankingDashboard.js:30-34`).
2. **Cache key** = MD5 of the query + MD5 of the comma-joined doc ids. A missing id falls back to the list position (`main.py:98-99`). On a hit it returns the stored JSON (`main.py:103-111`).
3. **Score.** One (query, text) pair per document; `cross_encoder.predict` scores all pairs in one call (`main.py:120-121`). For this model the outputs are raw relevance logits (unbounded, often negative), not 0–1 probabilities. That comes from the model's own configuration: its `config.json` sets the default activation to `Identity`, as checked in your local Hugging Face cache. The code applies no sigmoid.
4. **Sort and cut.** Sort by cross-encoder score, keep `top_k`, and attach `rank` and `rerank_score` (`main.py:124-131`).
5. **"Improvement %".** (mean of the top-k cross-encoder scores − mean of the top-k caller scores) ÷ the caller mean (floored at 0.01), × 100 (`main.py:134-136`). The "top-k caller scores" are the k highest caller scores, not the caller scores of the documents the reranker kept. A missing caller score defaults to 0.5 (`main.py:117`).
6. **Cache write** with a 24 h TTL (`main.py:153-154`). The latency of each miss is appended to an in-memory list (`main.py:138-139`).
7. **`/metrics`** reports the mean, p95 and p99 of that list (`main.py:170-181`).

### README vs code
- The README says "Bi-encoder vs cross-encoder comparison" (`README.md:32`). There is no bi-encoder. `/compare` uses the caller's `score`, or `np.random.uniform(0.3, 0.9)` when it is missing (`main.py:195-196`), and the UI sends typed-in numbers (`RerankingDashboard.js:13-22`).
- The README says "Builds on L21's embedding and chunking infrastructure" (`README.md:45-46`). Nothing is imported from L21.
- The README says "Redis caching (24hr TTL)" (`README.md:30`). True (`main.py:154`), but the key is unsafe (see below).
- The README says "Real-time metrics dashboard" (`README.md:31`). The dashboard polls `/metrics` every 5 s and shows request counts, hit rate, and average and p95 latency (`frontend/src/App.js:15, 46-71`). The latency numbers are real wall-clock measurements, of cache misses only. The improvement number is not meaningful.
- The README says "Production-grade error handling" (`README.md:34`). `/rerank` has no try/except, and scoring runs synchronously inside an `async` handler, so it blocks the event loop (`main.py:92-121`).
- The README says "Batch reranking support" (`README.md:33`). `/batch-rerank` loops over the queries one at a time through the single-query handler, with the default `top_k` of 10 (`main.py:158-166`). It is a loop, not a batch.

### Where it is thin or wrong
- [bug] **Security: a literal API key is committed in source** (`main.py:26`). Treat it as leaked and never reuse it. It is a D4 example of what not to do.
- [misleading] **`improvement_pct` compares two different scales** (`main.py:134-136`). Cross-encoder logits (for example −10 to +10) are set against first-stage cosine-like scores (0–1, or the 0.5 default). The percentage can swing to hundreds of percent either way regardless of whether the ranking got better. Real values are UNVERIFIED (nothing was run).
- [misleading] **Random "bi-encoder" scores** when none are supplied (`main.py:195-196`). `ranking_changes` counts the top-5 positions whose document differs (`main.py:217-218`); with random or typed scores this says nothing.
- [bug] **The cache key ignores `top_k` and the document text** (`main.py:98-99`). A second call with a different `top_k` returns the old cut. Two different candidate lists of the same length without ids (ids default to "0", "1", ...) and the same query collide and return the wrong results. The cache is written even when the caller sets `use_cache` to false (`main.py:153`). The key also leaves out the model id. Redis runs with append-only persistence on a named volume (`docker-compose.yml:6-8, 33-34`), so cached scores outlive a restart for up to 24 h, even after you swap the model.
- [misleading] **Caching can be off without anyone noticing.** Redis is pinged once, at import (`main.py:34-41`). If it is not reachable at that moment, caching stays off for the life of the process. Every response then says `cache_hit: false`, and `test.sh` still prints a tick for caching (`test.sh:110`).
- [bug] **A document without `text` is scored as its own dict.** The fallback is the string form of the whole dict, id and score included (`main.py:116`). The cross-encoder scores that string with no warning.
- [bug] **The chart pairs the wrong scores.** `original_scores` are returned in *input* order (`main.py:144`), but the chart pairs `original_scores[idx]` with the *reranked* document at `idx` (`RerankingDashboard.js:61-64`). Each bar compares two different documents.
- [shallow] **Metrics are partly hollow.** `avg_rerank_time` and `avg_improvement` are declared and never updated (`main.py:53-54`). `total_requests` counts cache hits, but the latency list holds only misses (`main.py:95, 139`). Everything resets on restart.
- [shallow] **No truncation awareness.** The cross-encoder reads at most 512 tokens per (query, document) pair. That is `model_max_length` in the model's tokenizer config, checked in your local Hugging Face cache. Long chunks are cut silently.
- [ok-for-demo] The `./models` volume is mounted (`docker-compose.yml:21`), but no HF cache variable points at it, in either the compose file or `backend/Dockerfile`. The model therefore downloads again in every new container. Your earlier copy fixed this by setting `TRANSFORMERS_CACHE`/`HF_HOME` (`prior_work/.../docker-compose.yml`).

### Tests and data
- There are no unit tests. `test.sh` reranks the same 3 docs twice, "expecting" a cache hit, but never asserts `cache_hit` (`test.sh:35-65`). It checks only that `total_requests > 0`, and even then it only prints a warning, never failing (`test.sh:74-79`). It then prints ticks for every feature unconditionally (`test.sh:107-112`).
- The 10 sample sentences in the dashboard and the 3 (rerank) and 5 (compare) in `test.sh` (`test.sh:43-45, 89-93`) are generic ML sentences with invented scores. They are not usable as relevance data.

### What to take for your project
- Re-implement for R3: retrieve a pool of N with your dense (or hybrid) retriever, score every (query, chunk) pair with the same local cross-encoder, keep the top k, and **keep both scores in the trace**. Never subtract one from the other.
- Choose the pool size by measuring it, not by default. Plot recall@N of the first stage and cross-encoder CPU latency for N = 10, 20, 50, 100 (D2). That is a far better "improvement" number: nDCG@k or MRR before vs after reranking on labelled questions (M2).
- Take the p95/p99 latency idea, and build a cache key that includes the query, the model id, `top_k` and a hash of each candidate's *text* (D2). This matches your "every external call is cached" rule. Record hits and misses separately, so your latency numbers say which they measure.
- The cross-encoder runs locally, so you can rerank any chunk, book text included, without anything leaving your machine. If you later try Cohere's hosted rerank, use it only on non-book text and cache it like every other external call.
- Skip the Gemini, Redis and compare parts.

### Try this
- 20 minutes. Load `cross-encoder/ms-marco-MiniLM-L-6-v2` locally. Score 5–10 of your own (query, passage) pairs, some relevant and some not. Print the raw scores, then apply a sigmoid. Compute the lesson's "improvement %" by hand once with raw scores and once with sigmoid scores against made-up first-stage scores near 0.7. The "improvement" changes wildly while the ranking stays the same. Then time `predict` for 10, 50 and 100 pairs on your CPU.

### Interview angle
- Q: "Why rerank only the top 20–100 candidates with a cross-encoder instead of scoring the whole corpus?"
  A: A cross-encoder reads the query and the document together, so it must run once per pair at query time, which is too slow for a whole corpus. A bi-encoder pre-computes document vectors, so first-stage search is cheap. You fetch a wide pool cheaply, spend the expensive model only on that pool, and pick the pool size by measuring first-stage recall@N against latency.

---

## L23 · Hybrid search with RRF, metadata filters and reranking  (`lesson23/l23-hybrid-search/`)

**What the code teaches, in one line:** The *shape* of a hybrid pipeline: two ranked lists, fused with Reciprocal Rank Fusion (k = 60), then reranked by a cross-encoder, with Chroma `where` metadata filters.
**What it is not:** There is **no BM25 and no keyword search of any kind**. The "keyword" leg is a second dense query through Chroma's built-in embedder. The `alpha` weight is accepted and ignored. There is no chunking (each document is one record), no answer generation and no evaluation behind the README's "Precision@5: 89%".
**Relevance to your RAG study:** High (as a design to rebuild correctly). Concepts: R1 (RRF fusion is real; the sparse/BM25 leg is a counter-example), R2, R3. [Interview]
**Stack:** FastAPI 0.115, `chromadb` 0.5.20 `PersistentClient("./chroma_db")`, collection `hybrid_search_docs` created with `hnsw:space` = `cosine` (`backend/main.py:38-49`). Embeddings: Gemini `models/text-embedding-004` (`main.py:88-92`). Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2` (`main.py:52`). A Gemini model `gemini-2.0-flash-exp` is created and never used (`main.py:35`). The React UI has a document manager. You can add a doc with optional category, year and author (`frontend/src/components/DocumentManager.js:20-30`), or "load sample data" with 5 docs carrying category/year/author (`DocumentManager.js:50-81`). The search box has category, year (≥) and author filters, a top-k setting and a rerank toggle, and always sends `alpha: 0.5` (`frontend/src/components/SearchInterface.js:20-48`).
**Swap to your stack:** moderate. Dense with Cohere `embed-v4.0` and the cross-encoder swap easily. You must *write* the BM25 leg (hand-rolled or `rank_bm25`) and fix the embedding and ordering bugs below.

### Read in this order
| # | File | What it does | Key lines |
|---|---|---|---|
| 1 | `backend/main.py` `reciprocal_rank_fusion` | RRF with k = 60 | 147-159 |
| 2 | `backend/main.py` `hybrid_search` | Vector leg, "keyword" leg, filters, fusion, fetch | 161-288 |
| 3 | `backend/main.py` `rerank_results` + `/search` | Cross-encoder on the fused top 20, final score field | 290-307, 352-399 |
| 4 | `backend/main.py` `/documents` | Embedding and dummy-vector fallback at insert | 321-350 |
| 5 | `backend/main.py` `_matches_filter` | Hand-written post-filter | 101-145 |
| 6 | `test.sh`, `README.md` | Smoke test; claims to check | whole files |

### How it works, step by step
1. **Add a document.** `POST /documents` takes `id`, `text` and `metadata` (`main.py:55-58, 321-343`). The text is embedded with Gemini using task type `retrieval_query` even though it is a document (`main.py:88-92, 326`). Without a working key it stores a dummy 384-dim vector with a 1 in position 0 and zeros elsewhere (`main.py:330-335`).
2. **Search request.** `/search` always asks `hybrid_search` for **20 candidates**, whatever the user's `top_k` (`main.py:357-362`).
3. **Vector leg.** Embed the query with Gemini (cached in an unbounded dict, `main.py:80-95`). Chroma query with `where = metadata_filter` (a pre-filter) and `n_results = 20`, keeping only the ids. The distances are fetched and never used (`main.py:182-193`).
4. **"Keyword" leg.** `collection.query(query_texts=[query])` with `n_results` 40 (simple filter) or 60 (no filter or `$and`) (`main.py:204-227`). `query_texts` makes Chroma embed the query with the collection's **default embedding function**. In Chroma 0.5.x that is all-MiniLM-L6-v2, 384-dim. This is library behaviour, not visible in the code, but the code's own comment says the same (`main.py:332-333`). This is dense search, not keyword search. For `$and` filters it fetches without a filter and post-filters in Python (`main.py:232-247`), on the false claim that `query_texts` cannot take `$and` (`main.py:202`). The Python post-filter also runs, redundantly, after a simple Chroma filter (`main.py:234`).
5. **Fuse.** RRF adds `1/(rank + 60)` per list with a 0-based rank, so the top item gets 1/60 (`main.py:147-159`). It uses ranks only, so no score normalisation is needed. There is no min-max scaling and no weights; `alpha` is never read (`main.py:166`).
6. **Fetch.** Take the top 20 fused ids and call `collection.get(ids=...)`, then pair the results with the ids *by position* (`main.py:260-283`).
7. **Rerank.** The cross-encoder scores every (query, text) pair among those ≤ 20 and keeps the user's `top_k` (default 5) (`main.py:290-307, 370-372`). Without reranking it takes the first `top_k` in RRF order (`main.py:374`).
8. **Respond.** `score` is the cross-encoder logit if reranked, otherwise the RRF score (`main.py:383`). Same field, two scales.

### README vs code
- The README says "Keyword Search: BM25 full-text search" (`README.md:9`). There is no BM25 anywhere; the "keyword" leg is a second dense search (`main.py:207-227`).
- The README says "Parallel searches" (`README.md:47, 55`), and so does a code comment (`main.py:177`). The two legs run one after the other (`main.py:182-254`).
- The README lists "Timeout Management: Vector (100ms), Keyword (50ms), Rerank (200ms)" and "Circuit Breakers" (`README.md:115-116`). The code has no timeouts and no circuit breaker.
- The README claims "Precision@5: 89%", "<500ms p95" and "1000+ docs tested" (`README.md:133-135`). There is no eval or benchmark code. UNVERIFIED and unsupported.
- The README says "ChromaDB: Vector + keyword + metadata storage" (`README.md:48`). Chroma is used for vectors and metadata only.
- The README's RRF formula `1/(rank_i + 60)` matches the code. The original Cormack et al. paper counts ranks from 1, so the code is off by one. That barely changes the ordering.

### Where it is thin or wrong
- [bug] **The "keyword" leg silently fails in the normal case.** With a working key, the stored vectors are 768-dim Gemini vectors (`text-embedding-004`), while `query_texts` produces a 384-dim MiniLM query. Chroma is then expected to raise a dimension-mismatch error (Chroma behaviour; not run, UNVERIFIED). The code catches it twice, ends with `keyword_response = None`, and so `keyword_results = []` (`main.py:220-230, 248-250`). "Hybrid" is then vector-only plus rerank, and the only trace is a log line.
- [bug] **Without a key, ranking is arbitrary.** The query embedding fails, so the vector leg is skipped (`main.py:182, 197-198`). Every stored vector is the same dummy vector (`main.py:334-335`), so every document is equally close to any query in the "keyword" leg. The candidate set and its order are arbitrary, and only the cross-encoder (if switched on) gives a real order. With 20 or fewer documents the demo still looks fine, which hides the bug. The comment "keyword search will still work" (`main.py:331`) is misleading. The query runs, but it is neither keyword search nor a meaningful ranking.
- [bug] **In no setup do both legs work.** Put the two bugs above together. With a key, the stored vectors are 768-dim and the 384-dim "keyword" query fails. Without a key, the vector leg is skipped and the "keyword" leg ranks identical dummy vectors. If the collection was first filled without a key, its dimension is 384. Later Gemini vectors (768) are then rejected at insert, which returns HTTP 500 (`main.py:338-350`), and the 768-dim vector-leg query fails and is caught (`main.py:195-196`). Each case rests on Chroma's fixed-dimension check (library behaviour, UNVERIFIED, not run).
- [misleading] **Every response claims to be hybrid.** `rank_source` is hard-coded to "hybrid_rrf" or "hybrid_rrf_reranked" (`main.py:372, 375`), and `/` lists `keyword_search` as a feature (`main.py:317`). Nothing in the response says how many hits each leg returned, so a dead leg is invisible.
- [misleading] **`alpha` is accepted and never used** (`main.py:65, 166, 361`; the UI sends 0.5 at `SearchInterface.js:47`).
- [bug] **Results may be paired with the wrong ids.** The code assumes `get(ids=...)` returns rows in the order you pass, and pairs `doc_ids[i]` and its RRF score with row `i` (`main.py:266-283`). Chroma does not document that order guarantee. If the rows come back in storage order, a result's id and score belong to a different text than the one shown and reranked (library behaviour, UNVERIFIED). Map by the returned `ids` instead.
- [bug] **The hand-written filter is incomplete.** `_matches_single_condition` returns after the first key of a condition. An unsupported operator such as `$in` falls through to "match" (`main.py:122-145`). `$and` nested inside `$or` is not handled (`main.py:106-120`). Post-filtering the top 60 can also drop every true match.
- [bug] **Documents are embedded with the query task type** (`main.py:91, 326`), so the asymmetric document/query embedding you saw in L20 is lost.
- [misleading] **The `score` field mixes two scales:** cross-encoder logit or RRF score (`main.py:383`). The UI prints it to 4 decimals as if it were one scale (`SearchInterface.js:158-159`).
- [misleading] **Errors become empty results.** Any search error mentioning "API key" returns `[]` with HTTP 200 (`main.py:394-397`), so "no results" and "broken" look the same.
- [shallow] **Provenance is the caller's job.** There is no chunking, so a "document" is whatever text the caller sends (`main.py:321-343`); no page and no offsets. Re-adding an existing id goes through Chroma `add`, not `upsert` (`main.py:338`). In Chroma 0.5.x that is expected not to update the record (library behaviour, UNVERIFIED).

### Tests and data
- `test.sh` adds one document with `category: test` and searches "Python programming" with the filter `category = test`. It passes if that id appears anywhere in the response (`test.sh:14-40`). The collection persists, so older documents may still be stored (`main.py:38`), but the filter leaves only the test document as a candidate. Any working leg returns it, so the test cannot detect a broken keyword leg, a wrong fusion or a bad rerank. Yet it prints that it verified "Vector search, keyword search, metadata filtering, RRF fusion, reranking" (`test.sh:44`).
- The sample data is 5 one-sentence docs with category/year/author metadata (`DocumentManager.js:50-81`). It is good for a filter demo and too small for ranking metrics.
- The `.svg` diagrams (`architecture.svg`, `workflow.svg`, `state-diagram.svg`) show the intended design, not what the code does.

### What to take for your project
- Rebuild R1 properly in plain Python: (a) BM25 over chunk tokens (hand-rolled first, k1 = 1.5, b = 0.75, with your tokeniser written down), (b) a dense leg with Cohere `embed-v4.0` (`search_document` for chunks, `search_query` for questions; every call cached by record/replay; the MiniLM fallback in its own index), (c) RRF with 1-based ranks and k = 60, (d) optionally a weighted score fusion with min-max normalisation and alpha, so you can compare RRF and alpha fusion (M4).
- R2: apply the metadata filter **before** ranking in *both* legs (BM25 over the filtered subset; Chroma `where` for dense), and write a test in which the filter removes the best unfiltered hit.
- R3: rerank the fused top-N with the cross-encoder, and keep `bm25_rank`, `dense_rank`, `rrf_score` and `rerank_score` as separate fields in the trace (D1).
- Add the safety checks this lesson lacks: assert that the query and stored dimensions match at startup, and log when a leg returns 0 results. Return `bm25_hits` and `dense_hits` counts with every response, so a dead leg cannot hide behind a "hybrid" label (`main.py:372, 375`).
- The README says L24 wraps this engine as a LangChain retriever (`README.md:109-110`). Do that only after your plain-Python hybrid passes its R1 and R2 tests. Then wrap it in a LangChain retriever, and check that the wrapper returns the same ids in the same order.
- Your earlier copy adds `load_dotenv()` and switches to `models/gemini-embedding-001`. The dimension mismatch with the default embedder is still there.

### Try this
- 30 minutes. Write 8–10 short docs of your own, including one with a rare exact token (an error code, a product name or an acronym) and one paraphrase-only match. Hand-roll BM25 and a MiniLM dense ranking. Fuse them with RRF (k = 60, ranks from 1). Run 3 queries: the exact-token query (look for BM25 winning), a paraphrase query (dense winning) and a mixed one (fusion helping). Then set k = 1 and k = 600 and watch how much rank 1 dominates.

### Interview angle
- Q: "Explain Reciprocal Rank Fusion. Why does it need no score normalisation, and what does k do?"
  A: RRF ignores raw scores and adds 1/(k + rank) from each list, so BM25 scores and cosine similarities never have to share a scale. A large k (60 is common) shrinks the gap between rank 1 and rank 10, so a document that is fairly high in both lists can beat one that tops only one list.

---

## Block summary
| Lesson | Title | Relevance | Concepts | Best file to read | Biggest problem |
|---|---|---|---|---|---|
| L19 | Naive RAG (keyword overlap + Gemini) | High | C1 C2 C5 C6 P2 P3 P7 V3 | `backend/knowledge_base.py` (+ `query_engine.py:84-120`) | "Keyword" retrieval is distinct-word overlap with no IDF; cleaning strips technical symbols; page numbers lost; duplicate tail chunks (tested as correct); errors returned as answers |
| L20 | ChromaDB vector store | High | P4 P5 C3 C4 R2 | `backend/search_engine.py` + `backend/vector_store.py` | Basics are correct (cosine space, 1 − d, asymmetric task types), but retrieval only, no page/offset metadata, stale chunks after an edit, "% match" label, filters not in the UI |
| L21 | Chunking + embedding comparison lab | Medium-High | C2 I1 I3 P4 I-CMP (counter) | `backend/app/services/chunking_service.py` | No retrieval at all; "coherence" rewards overlap, not quality; recursive chunker can recurse forever and loses positions; Chroma init uses a removed config, so storage almost certainly never works (0.5.0 rejection UNVERIFIED) |
| L22 | Cross-encoder reranker + Redis cache | High for R3 | R3 D2 D4 (counter) | `backend/main.py:92-181` | Hard-coded API key; "improvement %" compares logits with cosine-scale scores; "bi-encoder" scores are typed-in or random; cache key ignores top_k, text and model id |
| L23 | Hybrid search (RRF + filters + rerank) | High (rebuild it) | R1 (sparse leg counter-example) R2 R3 | `backend/main.py:147-307` | No BM25: the "keyword" leg is a second dense search; in no setup do both legs work (dimension mismatch or dummy vectors; Chroma behaviour UNVERIFIED), yet every response is labelled "hybrid"; `alpha` unused; results paired with ids by position |

### Cross-lesson patterns
- **Characters as the only chunk unit.** L19, L20 and L21 (fixed and sliding) all chunk by characters; nothing counts tokens (L21 installs `tiktoken` and never imports it). The same duplicate-tail chunk appears in L19, L20 and L21's fixed chunker.
- **Provenance is never kept.** No lesson stores a page number. Offsets are into cleaned text (L19), absent (L20, L23), or fake or zero (L21 semantic and recursive). None of these pipelines can cite "page N".
- **Silent fake vectors.** L20's original `setup.sh` stored zero vectors on failure (later replaced by fail-fast), L21 still inserts zero vectors for Gemini failures, and L23 stores identical dummy vectors without a key. Each one corrupts ranking without any error.
- **Mixed score scales presented as one number.** L22's improvement % (logits vs cosine) and L23's `score` field (logit or RRF). L20 is the only lesson that converts distance to similarity correctly, because it set cosine space.
- **Metric theatre.** README performance and quality numbers (L19 latency, L23 "Precision@5 89%") have no code behind them. L21's "coherence" and L22's "improvement" are computed but do not measure quality. No lesson has a labelled question set or a retrieval metric.
- **Unused LLM objects and dead code.** Gemini generation models are created and never called in L22 (`gemini-pro`) and L23 (`gemini-2.0-flash-exp`); only L19 generates answers. `decode_instrumentation.py` (L19) and `chromadb` in L22 are unused.
- **Error sniffing hides failures.** Error strings are scanned for "invalid" or "API key" and turned into a misleading message (L20) or an empty 200 response (L23). L19 returns errors as answers.
- **Labels that claim more than the code does.** L20 shows cosine × 100 as "% match" (L20 `frontend/src/components/SearchPanel.jsx:34`), L21 shows coherence as a percentage (L21 `frontend/src/App.js:220`), L22's `test.sh` ticks "Caching" even when Redis is off (L22 `test.sh:110`), and L23 labels every response "hybrid" even when one leg returned nothing (L23 `backend/main.py:372, 375`). Read the number's definition, not its label.
- **Stale index entries.** L19 (re-upload of a file, `backend/knowledge_base.py:23-43`), L20 (re-index of an edited source, `backend/indexing_pipeline.py:46`) and L22 (persistent Redis cache without a model id in the key, `backend/main.py:98-99`; `docker-compose.yml:6-8`) all keep old results that no longer match the current data or model. None of them versions the index or the cache.
- **The generated folders were hand-edited after `setup.sh`** (L19 model list and debug code, L20 embedding service). Always read the project folder, not `setup.sh`.
- **Chroma distance metric:** L19 and L22 do not use Chroma. L20 and L23 set `hnsw:space="cosine"` at creation (L23 only when the collection is new). L21 sets nothing, so it would be L2, but it never queries.
- **Security:** a literal Google API key is committed in L22 (`backend/main.py:26`).
