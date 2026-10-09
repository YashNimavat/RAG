# P5_FACTS — what the P5 lesson can rely on (run-verified)

Run date: **2026-10-08**. Every number in [`concepts/P5_vector_search.md`](../../../concepts/P5_vector_search.md) is listed here with the command and output section that produced it. Numbers not produced by these runs are marked CITED (from an earlier logged run or file), DERIVED (arithmetic shown in the lesson), ASSUMPTION or UNVERIFIED.

## 0. Environment, provenance, how to re-run

- **Interpreter.** CPython 3.12.8 (Windows 11), the project uv environment (`rag_learning/.venv`). Nothing was installed.
- **Versions** (printed in S1): pymupdf 1.26.7 · numpy 2.5.3 (OpenBLAS 0.3.34) · sentence-transformers 6.1.0 · torch 2.14.1 (CPU) · transformers 5.19.0.
- **Machine** (printed in S8): 11th Gen Intel Core i7-11800H @ 2.30GHz, 16 logical CPUs, 16 GB RAM.
- **Corpus.** `upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf`, SHA-256 `1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669` (repo pinned at `009adba`). Extraction as in the acceptance suite and P1: `page.get_text()` per page, pages joined with `"\n"`. Chunks are **plain fixed character windows** (1,000 / 200), as in P1; not LangChain's splitter.
- **Model.** `sentence-transformers/all-MiniLM-L6-v2` from the local HF cache, offline (`HF_HUB_OFFLINE=1`), snapshot `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
- **Queries.** Two demo questions from the draft seeds in 06 §6.7 (D-002, D-008; drafts, used for demonstration only, not evaluation); the first 200 characters of each of the 33 pages ("page-head" queries); 200 random unit vectors (seed 0).
- **Not run.** No faiss, no LangChain (neither is in the project env; not installed). No Groq or Cohere call; `.env` never read.
- **Scripts** (this folder):

  | Script | What it produces | Saved output |
  |---|---|---|
  | `p5_measure.py` | S1–S8: chunks and metadata, embeddings, one query, brute-force agreement, ties, metadata and filters, distances, timings | `out_p5_measure.txt` (stdout), `out_p5_measure.stderr.txt` (model-loading progress bar only) |
  | `p5_sources.py` | S-src: every cited repo cell (0-based), helper line, book page, the repo-wide scans and the LangChain source lines | `out_p5_sources.txt` |
  | (outside the workspace) `scratchpad/p5_lab_test/run_lab.py` + `solution.py` | LT: runs the lab notebook with a throwaway solution and six broken or blank variants | `out_p5_lab_test.txt` |

- **Re-run** (from `rag_learning/`, Git Bash):
  ```bash
  B="C:/Yash/New-Work/Book RAG"
  PYTHONIOENCODING=utf-8 uv run python sources/verification/P5/p5_measure.py \
      "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" "$B/RAG_Made_Simple_The_Complete_Visual_Guide" \
      > sources/verification/P5/out_p5_measure.txt 2> sources/verification/P5/out_p5_measure.stderr.txt
  PYTHONIOENCODING=utf-8 uv run python sources/verification/P5/p5_sources.py "$B/upstream/RAG_Techniques" \
      "$B/RAG_Made_Simple_The_Complete_Visual_Guide" "C:/Yash/New-Work/RAG/RAG_Techniques-main/venv/Lib/site-packages" \
      > sources/verification/P5/out_p5_sources.txt
  ```
  The third argument of `p5_sources.py` is a site-packages folder **outside** the project env (the learner's older venv). It is only read as text. Without it, the LangChain defaults stay UNVERIFIED.
- **Determinism.** Two consecutive runs of `p5_measure.py` gave **identical S1–S7 output** (diffed). S8 timings differ between runs (§2).
- **File hashes at the time of the run** (sha256): `p5_measure.py` `896d4351…`, `p5_sources.py` `edfe13cd…`, `labs/P5_vector_search_lab.ipynb` `6cc8c822…`.

## 1. Facts by section

`M` = `p5_measure.py` (section in `out_p5_measure.txt`); `S` = `p5_sources.py`; `LT` = lab test.

### S1 Chunks and metadata

| Fact | Value | Source |
|---|---|---|
| Pages / characters / chunks (1000/200 plain windows) | 33 / 72,593 / 91 | M S1 |
| Chunk 0; last chunk | `{chunk_id 0, page 1, page_end 1, [0, 1000)}`; `{chunk_id 90, page 33, [72000, 72593)}` | M S1 |
| Chunks that cross a page break | 40 of 91 | M S1 |
| Fingerprint of the page list (lab CHECK 1) | `62fa9c745825b2e2` | M S1 |

### S2 Embeddings

| Fact | Value | Source |
|---|---|---|
| MiniLM modules | Transformer, Pooling, **Normalize** | M S2 |
| Norms with `normalize_embeddings=False` | min/max 1.000000 / 1.000000 | M S2 |
| `V` shape, dtype, max abs(norm − 1) | (91, 384), float32, 1.19e-07 | M S2 |
| Index size | 91 × 384 × 4 = 139,776 bytes | M S2 |

### S3 One query (D-002, "In what year was the Paris Agreement adopted?")

| Fact | Value | Source |
|---|---|---|
| Shapes | `q` (384,), `V` (91, 384), `scores = V @ q` (91,) | M S3 |
| All-pairs chunk matrix size, for contrast | 91 × 91 = 8,281 | M S3 |
| Top-6 (id, score, pages) | 64 0.4623 p.23–24 · **26** 0.4336 p.10 · 16 0.3751 p.6 · 63 0.3366 p.23 · 25 0.3166 p.9–10 · 79 0.3069 p.29 | M S3 |
| Top-4 ids, fingerprint | [64, 26, 16, 63], `2df9fe7b18fb4d83` | M S3 |
| Chunk holding the whole evidence span (p.10 [438, 537)) | [26] (rank 2) | M S3 |
| Gap rank 4 − rank 5; score range | 0.0200; −0.1433 … 0.4623 | M S3 |
| D-008 top-4 (not used in the lesson body) | 78 p.28 0.2603, 64 p.23 0.2489, 54 p.20 0.2401, 77 p.28 0.2089; evidence chunk [64] | M S3 |
| Batch of 2 queries | `Q @ V.T` shape (2, 91) | M S3 |

### S4 Brute-force agreement and argpartition order

| Fact | Value | Source |
|---|---|---|
| `top_k` (argpartition + tie rule) == pure-Python brute force (float64, `sorted`, key (−score, id)) | 33/33 page-head and 200/200 random queries, at k = 1, 4, 10 (233 queries × 3 k) | M S4 |
| Full `lexsort` == brute force | same counts | M S4 |
| Gap between rank 4 and 5 over page-head queries (min/median/max) | 0.00170 / 0.01258 / 0.10103 | M S4 |
| max abs(float32 score − float64 score), page-head queries | 1.00e-07 | M S4 |
| BROKEN `argpartition` only (no sort): same order as brute force | 33/33 page-head queries (it passed by luck) | M S4 |
| BROKEN ascending `argsort` (forgot the minus) | 0/33 | M S4 |
| argpartition-only on a 10,000-vector random index (seed 3), 100 queries: same order / same set | 100/100 and 100/100 at each of k = 4, 10, 50 | M S4 |
| NumPy docstring: "The order of all elements in the partitions is undefined" | True | M S4 |

### S5 Ties

| Fact | Value | Source |
|---|---|---|
| TOY scores [0.70, 0.90, 0.80, 0.80, 0.80, 0.10], k = 2 | argpartition, default argsort, stable argsort and `top_k` all gave [1, 2] on this run; tied ids at the boundary [2, 3, 4] | M S5 |
| Toy fingerprints (lab CHECK 3, 4) | k = 2 [1, 2] `3a316d6d3226f84c`; k = 4 [1, 2, 3, 4] `d1be96124d992521` | M S5 |
| Duplicated index (dartboard cell 9 style), 5 × 91 = 455 rows, D-002 top-10 | 5 copies of chunk 64, then 5 copies of chunk 26 | M S5 |
| Distinct chunks in top-4 / top-10 | 1 / 2 | M S5 |
| Scores of the 5 copies of chunk 64 | 0.462341845035553 each, bit-identical: True | M S5 |
| `argpartition(-s5, 3)[:4]` rows | [428, 337, 64, 246] (copies 4, 3, 0, 2) | M S5 |
| `top_k` and brute force rows | [64, 155, 246, 337] (fingerprint `f65d5e725ddb1190`) | M S5 |

### S6 Metadata, filters, misalignment

| Fact | Value | Source |
|---|---|---|
| D-002 rank-1 result record | `{rank 1, score 0.4623, chunk_id 64, page 23, page_end 24, char_start 51200, char_end 52200}` | M S6 |
| Filter `page >= 25` keeps | 23 / 91 chunks | M S6 |
| 35 real queries (2 demo + 33 page heads): pre-filter short (< 4) | 0 | M S6 |
| Post-filter (`fetch_k` = 20) short / empty | 9 / 0; histogram {1: 1, 2: 4, 3: 4, 4: 26} | M S6 |
| D-002 pre- and post-filter ids | [79, 78, 77, 80] both (fingerprint `0a3fb4940ee86b6b`) | M S6 |
| Misaligned index (row 0 deleted from `V` only), D-002 | rows 63, 25, 15, 62 are labelled chunks 63, 25, 15, 62 (p.23, p.9, p.6, p.23) but are chunks 64, 26, 16, 63 (p.23, p.10, p.6, p.23); `len(V) == len(meta)` → False | M S6 |

### S7 Distances

| Fact | Value | Source |
|---|---|---|
| Unit vectors: max abs(L2² − (2 − 2 cos)) | 1.31e-06 | M S7 |
| Unit vectors, 35 queries: top-4 dot == cosine; L2 == cosine | 35; 35 (fingerprint of 35 `9f14025af0065b30`) | M S7 |
| TOY (row lengths × U(0.5, 1.5), seed 1): dot == cosine; L2 == cosine; dot == L2 | 0; 1; 0 (fingerprints `5feceb66ffc86f38`, `6b86b273ff34fce1`) | M S7 |
| TOY: cosine ranking unchanged by the scaling | 35/35 | M S7 |
| TOY D-002: cosine / dot / L2 top-4 | [64, 26, 16, 63] / [64, 26, 79, 63] / [16, 85, 65, 26] | M S7 |
| cos 0.8: L2, L2², 1 − L2/√2, 1 − L2²/√2 | 0.6325, 0.4000, 0.5528, 0.7172 (also printed for cos 0.5 and 0.2) | M S7 |

### S8 Timings (machine-specific; median of repeats; the saved run)

| N | d | Memory | Median per query | Source |
|---|---|---|---|---|
| 91 (real MiniLM `V`) | 384 | 139,776 B | 14.4 µs (Python-sort reference on the same scores: 25.2 µs) | M S8 |
| 480 (synthetic; = whole-book chunk count) | 384 | 0.7 MB | 0.024 ms | M S8 |
| 1,000 | 384 | 1.5 MB | 0.051 ms | M S8 |
| 10,000 | 384 | 15.4 MB | 0.187 ms | M S8 |
| 100,000 | 384 | 153.6 MB | 6.092 ms; k = 8: 6.074 ms (ratio 1.00); batch of 100: 0.538 ms per query | M S8 |
| 200,000 | 384 | 307.2 MB | 11.883 ms (ratio to 100k: 1.95) | M S8 |
| 500,000 | 384 | 768.0 MB | 32.189 ms; on its score vector: full argsort 18.47 ms, `top_k` 2.57 ms, matrix-vector product 26.36 ms | M S8 |
| 480 | 1,536 | 2.9 MB | 0.103 ms | M S8 |
| 100,000 | 1,536 | 614.4 MB | 23.315 ms | M S8 |
| The whole book (25 PDFs, same chunking) | — | — | 374,245 characters → 480 chunks | M S8 |

### S-src Citations

`p5_sources.py`: **ALL PASS**, 73 checks (repo HEAD `009adba2…`).

| Citation | Checked content |
|---|---|
| `helper_functions.py` L4, L48, L73, L74 | the FAISS import; `def encode_pdf(...)`; `OpenAIEmbeddings()`; `FAISS.from_documents(cleaned_texts, embeddings)` |
| `simple_rag.ipynb` cells 10, 13 | `FAISS.from_documents(...)`, `chunk_size=1000`; `as_retriever(search_kwargs={"k": 2})` |
| `simple_csv_rag.ipynb` cells 12, 16 | `faiss.IndexFlatL2(`, `InMemoryDocstore()`, `index_to_docstore_id={}`; `retriever = vector_store.as_retriever()` |
| `json_rag.ipynb` cells 17, 21, 23 | `corpus_metadata.append({"original_index": i, "data": item})`; `faiss.IndexFlatL2(embedding_dim)`, `index.add(...)`; `NUM_NEIGHBORS = 5`, `index.search(query_embedding, NUM_NEIGHBORS)` |
| `dartboard.ipynb` cells 9, 13, 23 | `documents=documents*5`; `index_to_docstore_id[idx]`, `docstore.search(docstore_id)`, `embed_documents([query])`, `index.search(np.array(q_vec),k=k)`; `k=num_results * oversampling_factor`, `reconstruct_batch(...)`, `1 - np.dot(candidate_vectors, candidate_vectors.T)` |
| `multi_faceted_filtering.ipynb` cells 12, 14 | `similarity_search_with_relevance_scores(query, k=10)`; `def apply_metadata_filter(`, the Chile filter call |
| Repo-wide | 8 notebook code cells build `faiss.IndexFlatL2` (HyPE 11, context_enrichment…llamaindex 9, fusion…llamaindex 8, json_rag 21, reranking…llamaindex 10, simple_csv_rag 12, simple_csv_rag…llamaindex 8, simple_rag…llamaindex 9); **no** `IndexFlatIP`, `IndexHNSW`, `IndexIVF`, `DistanceStrategy`, `normalize_L2` or `hnswlib` in any notebook or `.py`; 26 k settings in code cells, literal values 1, 2, 3, 4, 5, 10 (listed in the output) |
| Book (21 page phrases, each < 15 words) | Ch1 p.6/14 (×3), p.7, p.8 (×2), p.9, p.10, p.13; App p.15, p.16, p.21, p.22 (×2); Ch12 p.8/14; Ch13 p.6/13; Ch15 p.1/12 (×2), p.10/12; Ch11 p.6/13; Ch14 p.7/13 |
| Book absences (whole-book scan) | no "HNSW", "approximate nearest", "IVF", "argpartition", "inverted file"; "exhaustive" appears once (Ch14 p.4, unrelated) |
| LangChain source (read as text; langchain_community 0.4.1, langchain_core 1.3.0, faiss_cpu 1.13.2 dist-info present; sha256 `faiss.py` `7f37a84e…`, `base.py` `d95cac26…`) | `faiss.py` L213 `normalize_L2: bool = False`; L214 and L993 `DistanceStrategy.EUCLIDEAN_DISTANCE` default; L998 `IndexFlatIP` only for MAX_INNER_PRODUCT; L1000–L1001 "Default to L2" → `IndexFlatL2`; L390, L626 `k: int = 4`; L392 `fetch_k: int = 20`; L417 search with `fetch_k` when a filter is given; L450 `return docs[:k]`; L1272 Euclidean relevance fn. `base.py` L362 `k: int = 4`; L970 `search_type = "similarity"`; L973 empty `search_kwargs`; L1043–L1045 the retriever passes them to `similarity_search`; L385–L388 the `1 − distance/√2` formula and its "normalized embeddings" comment |

### LT Lab test (`out_p5_lab_test.txt`)

The notebook was executed cell by cell (Python `exec` in one namespace, not a Jupyter kernel) with the learner cells replaced by a throwaway solution kept **outside** the workspace (`scratchpad/p5_lab_test/`).

| Variant | Result |
|---|---|
| good | **10/10** CHECK cells pass |
| blank (learner cells left empty) | 9 CHECK cells fail with `NameError`; the Task 9 CHECK passes only because the runner fills the answer cell |
| `no_tie_rule` (argpartition + score sort, no id tie-break) | CHECK 4 (trial 0 differs from brute force) and CHECK 5b fail |
| `similarity_matrix` (q kept 2-D, `scores = V @ V.T`) | CHECK 5 fails (`q` shape (1, 384)); later cells fail |
| `ascending` (forgot the minus) | CHECKs 4, 5, 5b, 6, 7 fail |
| `postfilter_wrong` (filters the top-k instead of the top-20) | CHECK 6 fails (`n_post_short` = 35) |
| `no_normalise_query` | CHECK 5 fails ("q must be normalised") |

## 2. CITED, DERIVED, ASSUMPTION and UNVERIFIED

| Item | Status |
|---|---|
| Second run of S8 | 91: 11.6 µs (ref 22.3 µs) · 480: 0.020 ms · 1k: 0.044 · 10k: 0.205 · 100k: 5.721 (k = 8: 5.705, ratio 1.00; batch 0.609 per query) · 200k: 11.902 (ratio 2.08) · 500k: 30.434 (argsort 14.20, `top_k` 2.00, matvec 26.23) · 480 × 1536: 0.104 · 100k × 1536: 23.264. Same shape; digits differ by up to about 25% at small N |
| k 4 → 8 grows the v0 prompt ×1.86 | CITED: P1_FACTS S10 |
| `embed-v4.0` has 1,536 dimensions | CITED: 08 E-3 (from the O2 smoke-test report) |
| v0 retrieval spec (exact cosine, argpartition, k = 4, ties by chunk_id) | CITED: 06 §3.1 |
| ≈ 164,000 vectors (d = 384) and ≈ 43,000 (d = 1,536) within 10 ms; ≈ 400× headroom at 480 vectors; 1M × 1,536 × 4 B = 6.1 GB; 2M × 1,536 × 4 B ≈ 12.3 GB; ≈ 0.5 s per query at 2M × 1,536 | DERIVED (linear scaling of the S8 100k numbers; shown in the lesson) |
| The 10 ms retrieval budget | ASSUMPTION (not a requirement in 06) |
| Part F toy (q = (0.6, 0.8, 0), five chunk vectors; stretched c0) | DERIVED by hand in the lesson; re-checked with a one-off Python line (dot 0.6/0.8/0.96/0.8/0.64; L2² 0.8/0.4/0.08/0.4/0.72; stretched c0: dot 1.2, cos 0.6, L2 1.612) |
| Whether FAISS `IndexFlatL2` returns squared L2 distances | UNVERIFIED (faiss not run) |
| LangChain defaults in the version the repo authors used | UNVERIFIED (the repo pins no version; 0.4.1 was read) |
| ANN recall, latency, memory (HNSW, IVF, PQ) | UNVERIFIED (Source C #22–#25; not run) |
| OpenAI embeddings are unit length; Cohere `embed-v4.0` vectors are unit length | UNVERIFIED |

## 3. Notes for 04 (not edited; recorded here)

1. The 04 P5 row cites only Ch1 p.6/14; the top-K pages (Ch1 p.8/14, p.10/14) and the glossary (App p.16/23, p.21/23, p.22/23) are missing.
2. "`simple_rag.ipynb cell 10` (`FAISS.from_documents`, flat L2 default)": the cell has no metric; the L2 default comes from the LangChain source (read, version 0.4.1). The store's k (2) is in cell 13.
3. The suggested check "NumPy exact k-NN vs FAISS `IndexFlatIP` on 100 queries; time both" cannot run in the project env (no faiss) and would test inner product, not the repo's `IndexFlatL2`. Replaced by the brute-force reference (S4).
4. "Book silent on … metadata storage": Ch11 p.6/13 (parent pointer in metadata) and Ch14 p.7/13 (filter by section identifiers) use metadata alongside vectors.
5. `json_rag.ipynb`: the metadata list is in cell 17, not 21. `dartboard.ipynb` cells 9, 13, 23 (02 cites 23) are not in 04.
