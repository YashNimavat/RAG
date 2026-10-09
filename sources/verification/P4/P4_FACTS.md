# P4_FACTS — what the P4 lesson can rely on (run-verified)

Run date: **2026-10-08**. Every number in [`concepts/P4_embeddings_similarity.md`](../../../concepts/P4_embeddings_similarity.md) is listed here with the command and output section that produced it. Numbers not produced by these runs are marked CITED (from an earlier logged run), DERIVED (arithmetic shown in the lesson) or UNVERIFIED.

## 0. Environment, provenance, how to re-run

- **Interpreter.** CPython 3.12.8 (Windows 11), the project uv environment (`rag_learning/.venv`).
- **Versions** (printed in S1): pymupdf 1.26.7 · transformers 5.19.0 · sentence-transformers 6.1.0 · torch 2.14.1 (CPU) · numpy 2.5.3 · tokenizers 0.23.2.
- **Corpus.** `upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf`, SHA-256 `1d58a0fa…92669` (as in P1). Extraction: `page.get_text()`, pages joined with `"\n"` (acceptance-suite convention). Windows: **plain** 1,000-character slices, step 800 (overlap 200), 91 windows, the last 593 characters (same as P1 S4).
- **Models** (local HF cache, offline forced in the script):

  | Model | Snapshot | Role |
  |---|---|---|
  | `sentence-transformers/all-MiniLM-L6-v2` ("L6") | `1110a243…` (same as P1 and 07) | bi-encoder, modules Transformer → Pooling → Normalize |
  | `sentence-transformers/paraphrase-MiniLM-L3-v2` ("L3") | `4ca70771…` | a second bi-encoder, **no** Normalize module; used as "the other model" |
  | `cross-encoder/ms-marco-MiniLM-L-6-v2` | `233902d2…` | the reranker of `reranking.ipynb` cell 27 |

- **No API calls.** No Groq or Cohere call; `.env` never read. FAISS and LangChain are **not installed** in the project environment, so nothing here runs FAISS; FAISS behaviour is reasoned from the repo code and marked UNVERIFIED where it depends on the library.
- **Scripts** (this folder):

  | Script | Produces | Saved output |
  |---|---|---|
  | `p4_measure.py` | S1–S10 | `out_p4_measure.txt` (stdout), `out_p4_measure.stderr.txt` (stderr: model-loading bars and one tokenizer length message) |
  | `p4_sources.py` | S-src: every cited repo cell (0-based) and book page, repo-wide metric counts, book absences | `out_p4_sources.txt` |

- **Re-run** (from `rag_learning/`, Git Bash):
  ```bash
  B="C:/Yash/New-Work/Book RAG"
  PYTHONIOENCODING=utf-8 uv run python sources/verification/P4/p4_measure.py "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
      > sources/verification/P4/out_p4_measure.txt 2> sources/verification/P4/out_p4_measure.stderr.txt
  PYTHONIOENCODING=utf-8 uv run python sources/verification/P4/p4_sources.py "$B/upstream/RAG_Techniques" "$B/RAG_Made_Simple_The_Complete_Visual_Guide" \
      > sources/verification/P4/out_p4_sources.txt
  ```
- **Determinism.** Two consecutive runs of `p4_measure.py` gave **byte-identical** stdout (`cmp`).
- **Lab test.** `labs/P4_embeddings_lab.ipynb` was tested with a throwaway solution kept **outside** the workspace (session scratchpad): all 9 CHECK cells pass; five broken variants (cosine without normalising, L2 sorted high-first, raw-L2 retrieval on unnormalised vectors, wrong-model scored against the raw index, cross-encoder over all 91 windows) each fail at the intended CHECK. The notebook's fingerprints encode the values of S2, S4, S5, S6 and S8 below.

## 1. Facts by section (`M` = `p4_measure.py`, `S` = `p4_sources.py`)

### S1 Models

| Fact | Value | Source |
|---|---|---|
| L6 modules / `max_seq_length` / dim | Transformer, Pooling, **Normalize** / 256 / 384 | M S1 |
| L3 modules / `max_seq_length` / dim | Transformer, Pooling (**no Normalize**) / 128 / 384 | M S1 |
| Cross-encoder `max_seq_length` / tokenizer `model_max_length` / outputs / activation | 512 / 512 / 1 score / `Identity` (raw logit) | M S1 |

### S2 Toy 3-d vectors (TOY ILLUSTRATION)

q = [1, 2, 2] (|q| = 3); d1 = [2, 1, 2] (|d1| = 3); d2 = [0, 3, 4] (|d2| = 5); d3 = [2, 4, 4] = 2q (|d3| = 6).

| | dot | cos | L2 | L2² | unit-vector L2 | unit-vector L2² = 2 − 2cos |
|---|---|---|---|---|---|---|
| d1 | 8 | 0.8889 | 1.4142 | 2 | 0.4714 | 0.2222 |
| d2 | 14 | 0.9333 | 2.4495 | 6 | 0.3651 | 0.1333 |
| d3 | 18 | 1.0000 | 3.0000 | 9 | 0.0000 | 0.0000 |

- Rankings: dot d3, d2, d1; cosine d3, d2, d1; **raw L2 d1, d2, d3 (fully reversed)**; L2 on unit vectors d3, d2, d1.
- Scale d1 by 2: dot 8 → 16; cos 0.8889 → 0.8889; L2 1.4142 → 3.6056.
- Scale q by 2: dots 16 / 28 / 36 (each ×2); cos unchanged; L2 3.6056 / 2.2361 / 0.0000; raw-L2 ranking becomes **d3, d2, d1** (it flipped).
- Dartboard-style `1 − dot`: non-unit vectors −7 / −13 / −17 (negative "distances"); unit vectors 0.1111 / 0.0667 / 0.0000.

### S3 Random vectors (TOY, `numpy.random.default_rng(0)`, 1,000 docs × 100 queries × 384 dims)

| Fact | Value |
|---|---|
| max \|cos − dot(unit vectors)\| | 4.44e-16 |
| max \|L2² − (2 − 2cos)\| on unit vectors | 1.78e-15 |
| Queries whose full ranking of 1,000 docs is identical, cosine vs L2 on unit vectors | 100/100 |
| Doc norms after scaling each doc by U(0.5, 2) | 9.3 to 41.5 |
| Cosine top-1 unchanged by that scaling | 100/100 |
| Raw-L2 top-1 ≠ cosine top-1 | **94/100** |
| Raw-dot top-1 ≠ cosine top-1 | **68/100** |

### S4 Norms of real embeddings (91 climate windows)

| Pipeline | min norm | max norm | mean |
|---|---|---|---|
| L6 default (with Normalize) | 1.000000 | 1.000000 | 1.0000 |
| L6 with the Normalize module removed | 2.008154 | 3.042501 | 2.4093 |
| L3 default (no Normalize) | 2.255005 | 3.371165 | 2.8615 |

Also: L6 default vs `normalize_embeddings=True` max difference 2.98e-08; L6 default vs unit(raw) 2.98e-08; dtype float32, shape (91, 384).

### S5 Sentence pairs (L6)

| Pair | cos (= dot) | L2 |
|---|---|---|
| "greenhouse gas emissions" vs "carbon dioxide in the atmosphere" (Ch1 p.6/14 example) | 0.5356 | 0.9638 |
| "greenhouse gas emissions" vs "a recipe for chocolate cake" | −0.0859 | 1.4737 |
| Paraphrase pair (burning coal and oil … / fossil fuel combustion …) | 0.6918 | 0.7851 |
| Unrelated pair (… / museum opening hours) | −0.0478 | 1.4476 |
| Same words, opposite claim (have risen / have not risen) | **0.8436** | 0.5594 |

### S6 Retrieval illustration (two 06 seed questions × 91 windows; NOT an evaluation result)

Gold windows (contain the evidence phrase after whitespace normalisation): D-002 → [26]; D-004 → [22, 63]. Score vector shape (91,); an all-pairs matrix would be 91 × 91 = 8,281 scores.

| Question | Scoring | Top-5 | First gold rank |
|---|---|---|---|
| D-002 | L6 cosine | 64, 26, 16, 63, 25 | 2 |
| D-002 | L6 L2 on its unit vectors | 64, 26, 16, 63, 25 (identical; max \|L2² − (2 − 2cos)\| 4.77e-07) | 2 |
| D-002 | L6 raw (no Normalize), raw L2 | 64, 26, 16, 63, **65** | 2 |
| D-002 | L6 raw, raw dot | 64, 26, 16, **25, 63** | 2 |
| D-002 | L3 cosine / raw L2 / raw dot | 26, 64, 0, 33, 1 / 26, 64, 1, 0, 17 / 26, 64, 0, 65, 55 | 1 / 1 / 1 |
| D-002 | **Wrong model**: query by L3, windows by L6 (both 384-d) | 34, 47, 65, 86, 32 | **19**; no error; cos −0.1099..0.1900 (right model −0.1433..0.4623) |
| D-004 | L6 cosine (= L6 unit L2) | 63, 22, 79, 25, 26 | 1 |
| D-004 | L6 raw L2 / raw dot | 63, 22, 79, 26, 25 / 63, 22, 79, 25, 26 | 1 / 1 |
| D-004 | Wrong model | 79, 63, 22, 65, 33 | 2; cos −0.1067..0.1432 (right model −0.0825..0.4789) |

Top-1 cosines: D-002 0.4623, D-004 0.4789.

### S7 Truncation vs its question (04's proposed experiment; the mechanism is P1 S6)

A 400-WordPiece-token passage from the PDF, chosen so that the phrase "Direct air capture (DAC)" starts at **text token 300** (past the 254-text-token cap). Prefix = first 254 tokens (does not contain the phrase); tail = tokens 255–400 (146 tokens).

| Pair | cos |
|---|---|
| D-004 question vs the 400-token passage | 0.019276 |
| D-004 question vs its 254-token prefix | 0.019276 (identical) |
| D-004 question vs the tail embedded alone | 0.284787 |

### S8 Bi-encoder shortlist vs cross-encoder (NOT an evaluation result)

| Question | Bi-encoder top-10 | Cross-encoder logits on shortlist | Reranked top-3 | Gold rank bi → CE | CE over all 91 top-3 |
|---|---|---|---|---|---|
| D-002 | 64, 26, 16, 63, 25, 79, 65, 78, 33, 17 | −10.968 .. 5.152 | **26, 64, 63** | 2 → **1** | 26, 64, 63 |
| D-004 | 63, 22, 79, 25, 26, 67, 74, 85, 64, 32 | −9.393 .. 5.165 | 63, 22, 79 | 1 → 1 | 63, 22, 79 |

- Forward passes per query: bi-encoder 1 (the query; 91 documents encoded once at index time); cross-encoder 10 for the rerank, 91 to score the whole collection.
- Order matters: CE(q, d) = −4.293 vs CE(d, q) = −6.722 (D-002, window 64); 5.165 vs −7.080 (D-004, window 63).

### S9 Asymmetry (single illustrations)

| Fact | Value |
|---|---|
| Gold window 26: cos(question D-002, window) | 0.4336 |
| cos("The Paris Agreement was adopted in 2015.", window 26) | 0.5135 |
| cos(question, that statement) | 0.8069 |
| L6 (trained without prefixes): cos("query: " + q, q) | 0.9626 |
| cos("search_query: " + q, q) | 0.6965 |
| cos("Represent this sentence for searching relevant passages: " + q, q) | 0.6865 |
| Gold rank of window 26 with / without "query: " prefix | 2 / 2 |

### S10 `graph_rag.ipynb` cell 12, `priority = 1 / score` (TOY scores A 0.2, B 0.5, C 0.9)

| If the score is | Min-heap pops | Closest node | Explored at step |
|---|---|---|---|
| a distance (lower = closer) | C, B, A | A | **3 of 3** (last) |
| a similarity (higher = closer) | C, B, A | C | 1 of 3 |

A score of exactly 0.0 raises `ZeroDivisionError`.

### S-src Citations (`p4_sources.py`: **ALL PASS**)

| Citation | Checked content |
|---|---|
| repo HEAD | `009adba2…` |
| `dartboard.ipynb` cell 23 | `embed_documents([query])`; `index.search(`; `reconstruct_batch(`; `1 - np.dot(candidate_vectors, candidate_vectors.T)`; `1 - np.dot(query_embedding, candidate_vectors.T)`; the "1 - cosine_similarity" comment |
| `json_rag.ipynb` cells 19, 21, 22, 23 | `MODEL_NAME = 'all-MiniLM-L6-v2'`, `model.encode(...)`; `faiss.IndexFlatL2(embedding_dim)`; markdown: same model for the query, "lower is better"; query encode, `index.search`, printed `Distance` |
| `local_rag_huggingface_faiss.ipynb` cells 10, 13, 14, 16 | `EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"`; markdown on `normalize_embeddings=True` and cosine; `encode_kwargs={"normalize_embeddings": True}`; `FAISS.from_documents(` with no `distance_strategy` |
| `graph_rag.ipynb` cell 12 | `similarity_search_with_score(doc.page_content, k=1)`; `priority = 1 / similarity_score`; `heapq.heappush` |
| `reranking.ipynb` cells 27, 29 | `CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')`, `[query, doc.page_content]` pairs, `predict`, sorted descending; `k=10`, `rerank_top_k=5` |
| `simple_csv_rag.ipynb` cell 12 | `faiss.IndexFlatL2(` |
| `helper_functions.py` L48, L73, L74 | `def encode_pdf(`; `OpenAIEmbeddings()`; `FAISS.from_documents(cleaned_texts, embeddings)` |
| Repo-wide (code cells and .py) | `IndexFlatL2` 9 places; `IndexFlatIP`/`METRIC_INNER_PRODUCT` **0**; `distance_strategy` **0**; `normalize_embeddings` 1 (local_rag cell 14); `input_type` **0**; `CrossEncoder(` 2 (reranking cell 27, `reranking.py` L119) |
| Book phrases (each < 15 words) | Ch1 p.5/14, p.6/14, p.8/14; Ch12 p.8/14; Ch13 p.6/13, p.7/13, p.9/13; Ch6 p.1/14, p.2/14; Ch11 p.1/13; App p.13/23, p.15/23, p.16/23 |
| Book absences | "cosine" never on any Ch1 page (DV-B4 confirmed); first in reading order Ch12 p.8/14; also App p.14–15/23, Ch13 p.6/13, Ch15 p.8/12, Ch19 p.4/10, Ch20 p.1/11 and p.4/11, Ch21 p.2/13. No "dot product", "Euclidean", "L2", "unit length/vector", "input type", "prefix", "truncat", "max sequence" anywhere |

## 2. CITED, DERIVED and UNVERIFIED

| Item | Status |
|---|---|
| Cohere `embed-v4.0` accepted `input_type="search_document"`, dim 1536, listed context length 8192 | CITED: `progress/O2_smoke_test_2026-10-08.json` (`cohere_embed`) |
| That Cohere `search_query` and `search_document` give different vectors for the same text, and by how much | **UNVERIFIED** (no `search_query` call was made; no paid calls for P4) |
| MiniLM 256-token truncation, `[CLS]`/`[SEP]` included, cos(400-token text, prefix) = 1.000000 | CITED: P1 S6 |
| bge-small 512 tokens and its query-instruction recommendation | CITED: 06 §3.2 / 07 D.6. For `bge-base-en-v1.5` (the repo's model) the recommendation is **UNVERIFIED** here (model not cached) |
| LangChain `FAISS.from_documents` uses an L2 (Euclidean) index by default; `similarity_search_with_score` returns that distance | **UNVERIFIED** locally (LangChain not installed); consistent with the repo building only `IndexFlatL2` |
| FAISS `IndexFlatL2` returns **squared** L2 distances | **UNVERIFIED** locally (FAISS not installed). Ranking is unaffected either way |
| OpenAI embeddings are unit length (what dartboard cell 23 relies on) | **UNVERIFIED** (no OpenAI key; not run) |
| Proof L2² = 2 − 2cos for unit vectors; 2 − 2 × 0.8889 = 0.2222 etc.; Part F hand steps | DERIVED in the lesson; matches S2/S3 |

## 3. Notes for 04, 02 and 06 (not edited; recorded here)

- **04 P4 row.** Cells all match. Missing nuances: `json_rag` cells 19–23 print L2 distances, but on **unit** MiniLM vectors, so they rank exactly like cosine (S4, S6); `dartboard` cell 23 also embeds the **query with `embed_documents`** and builds the only true similarity matrix in this concept (K × K, for diversity); `local_rag_huggingface_faiss` sets the model in cell 10 and builds the store in cell 16 without a metric argument. Book column omits Ch1 p.8/14 (query embedded the same way; in the 02 card), Ch13 p.9/13 and the glossary entries at App p.13–14/23. The glossary's cosine entry also omits Ch19–21, which use the word.
- **02 P4 card.** `graph_rag` cell 12: the code treats the score as a similarity; that it is an L2 distance rests on LangChain's default (UNVERIFIED locally). If it is a distance, the start order is inverted (S10).
- **06 §3.2.** "effective max length used by `CrossEncoder` UNVERIFIED" is now measured: `max_seq_length` 512 (S1).
