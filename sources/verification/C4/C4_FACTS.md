# C4_FACTS — what the C4 lesson can rely on (run-verified)

Run date: **2026-10-08**. Every number in [`concepts/C4_dense_retrieval.md`](../../../concepts/C4_dense_retrieval.md) is listed here with the command and output section that produced it. Numbers not produced by these runs are marked DERIVED (arithmetic in the lesson), TOY, ASSUMPTION or UNVERIFIED.

## 0. Environment, provenance, how to re-run

- **Interpreter.** CPython 3.12.8 (Windows 11), the project uv environment. Nothing was installed.
- **Versions** (printed in S1): pymupdf 1.26.7 · numpy 2.5.3 · sentence-transformers 6.1.0 · torch 2.14.1 (CPU) · transformers 5.19.0 · tiktoken 0.14.0 · cohere 7.2.0 (signature inspected only).
- **Corpus D.** `upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf`, sha256 `1d58a0fa…92669`; `page.get_text()` per page, joined with `"\n"`; snapshot `ea07572562ac` (06 §5.3 recipe, executed from 06).
- **The v0 index (C3 stand-in).** Spans from 07 H.1/H.3 `chunk_document(..., recursive, 1000/200, per_page)` (executed from 07, as the acceptance suite does). Records in 06 §2.3 field order. **Course-wide ids** (coordinator decision, 2026-10-08, = C2 lab Task 7 and C3): `chunk_id = f"{doc_id}:{snapshot_id}:{params_hash}:{seq:05d}"`, `params_hash = sha256(json.dumps(CHUNKING, sort_keys=True))[:12]` over 06 §2.4's `chunking:` block = **`1ca9c5a3b548`**. MiniLM `all-MiniLM-L6-v2` (snapshot `1110a243…`), normalised, float32.
- **Gold.** The 10 draft seeds of 06 §6.7 (`llm-draft`), parsed from 06; relevance (`any_overlap`) and CE use `contracts_check.py`'s reference `rel` / `ce` / `group_recall` (06 §7.2).
- **Not run.** No Groq or Cohere call; `.env` values never read (only variable **names** were listed, values redacted). No faiss, no LangChain.
- **Scripts** (this folder):

  | Script | Produces | Saved output |
  |---|---|---|
  | `c4_measure.py` | S1–S9 | `out_c4_measure.txt` (run 1), `out_c4_measure_run2.txt` (run 2), `out_c4_measure.stderr.txt` (model-loading bars) |
  | `c4_sources.py` | S-src: repo cells, helper lines, LangChain and Cohere signatures, book pages | `out_c4_sources.txt` |
  | `c4_build_lab.py` | `labs/C4_dense_retrieval_lab.ipynb` (no solution code) | — |
  | `c4_lab_runner.py` | runs the lab with a solutions file (no solution code) | `out_c4_lab_test.txt` |
  | (outside the workspace) `scratchpad/c4/solution_*.py`, `make_variants.py` | the throwaway good solution and 8 broken/blank variants | — |

- **Re-run** (from `rag_learning/`, Git Bash):
  ```bash
  B="C:/Yash/New-Work/Book RAG"
  PYTHONIOENCODING=utf-8 uv run python sources/verification/C4/c4_measure.py \
      "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
      > sources/verification/C4/out_c4_measure.txt 2> sources/verification/C4/out_c4_measure.stderr.txt
  PYTHONIOENCODING=utf-8 uv run python sources/verification/C4/c4_sources.py "$B/upstream/RAG_Techniques" \
      "$B/RAG_Made_Simple_The_Complete_Visual_Guide" "C:/Yash/New-Work/RAG/RAG_Techniques-main/venv/Lib/site-packages" \
      > sources/verification/C4/out_c4_sources.txt
  uv run python sources/verification/C4/c4_build_lab.py
  uv run python sources/verification/C4/c4_lab_runner.py labs/C4_dense_retrieval_lab.ipynb <solutions.py outside WS>
  ```
- **Determinism.** Two runs of `c4_measure.py` are identical except the name of the temporary index folder (diffed).
- **File hashes at the time of the run** (sha256): `c4_measure.py` `1a9c6aa9…`, `c4_sources.py` `a99906de…`, `c4_build_lab.py` `b60c4859…`, `c4_lab_runner.py` `9e924b5f…`, `labs/C4_dense_retrieval_lab.ipynb` `90e75b85…`.

## 1. Facts by section

`M` = `c4_measure.py`; `S` = `c4_sources.py`; `LT` = lab test.

### S1 The v0 index

| Fact | Value | Source |
|---|---|---|
| Pages / characters / snapshot | 33 / 72,593 / `ea07572562ac` (= 06 §5.3) | M S1 |
| Chunks (07 spans, per_page recursive 1000/200) | **97**; length min/median/max 393 / 935 / 1,000 chars | M S1 |
| params_hash: course (06 §2.4 block) / 07 `ChunkerConfig` | `1ca9c5a3b548` / `77bc4c45809b` (same spans; the 07 hash is not used for ids) | M S1 |
| `chunks.jsonl` (97 lines, 122,774 bytes) sha256 | `d4108b89…aadb3011b` = the C2 lab's saved file: **True** | M S1 |
| chunk 0 | `climate:ea07572562ac:1ca9c5a3b548:00000`, [0, 949), p.1 | M S1 |
| One page segment per chunk; chunk_id string order = seq order | 97/97; True | M S1 |
| `V` | (97, 384) float32, max abs(norm − 1) 1.19e-07, 148,992 bytes | M S1 |
| embed_hash (course decision: 12 hex of sha256 over `{provider, model_id, revision, input_type, normalize, preproc_version}`, sorted keys; values as in C3's manifest: input types `none`, preprocessing `none`) | `c398eeba043f`; folder `index/ea07572562ac/1ca9c5a3b548/c398eeba043f/` | M S1 |
| Index files round trip (`vectors.npy`, `chunks.jsonl`, `manifest.json` with `embed_hash`, in a temp folder) | identical; checks: `len(chunks) == V.shape[0]`, unique chunk_ids, `(doc_id, seq)` increasing per document (no `seq == i` assert: `seq` restarts per document in Corpus T) | M S1 |

### S2 The P5 setup reproduced (plain 1000/200 windows across pages)

| Fact | Value | Source |
|---|---|---|
| Chunks | 91 | M S2 |
| D-002 top-6 (id, page, score) | 64 p.23 0.4623 · 26 p.10 0.4336 · 16 p.6 0.3751 · 63 p.23 0.3366 · 25 p.9 0.3166 · 79 p.29 0.3069 | M S2 |
| D-002 top-4 | **[64, 26, 16, 63]** = P5 S3; evidence at rank 2 (first relevant and first CE) | M S2 |
| Why v0 differs | different chunker: 97 per-page recursive chunks vs 91 cross-page windows, so chunk texts, vectors and ranks differ | M S1–S3 |

### S3 D-002 on the v0 index

| Fact | Value | Source |
|---|---|---|
| Shapes | q (384,), V (97, 384), `V @ q` (97,); 10 questions: `Q @ V.T` (10, 97) | M S3 |
| Top-8 (seq, page, score, relevant) | 69 p.24 0.4606 no · 68 p.23 0.4513 no · **27 p.10 0.4386 yes** · 17 p.6 0.4385 no · 84 p.29 0.3387 · 85 p.29 0.3114 · 70 p.24 0.2567 · 35 p.12 0.2448 | M S3 |
| "Paris Agreement" in the top-4 texts | seq 69: no (Kyoto Protocol, adopted 1997); 68, 27, 17: yes | M S3 (+ text read) |
| Gaps rank 1–2 / 2–3 / 3–4 / 4–5 | 0.00931 / 0.01269 / **0.00008** / 0.09978 | M S3 |
| Score range; median | −0.1536 … 0.4606; 0.0289 | M S3 |
| Rank-1 record | `{"rank": 1, "chunk_id": "climate:ea07572562ac:1ca9c5a3b548:00069", "doc_id": "climate", "page": 24, "char_start": 51414, "char_end": 52396, "score": 0.4606130123138428, "text": …}` | M S3 |
| Top-4 chunk_id fingerprint (lab CHECK 2a) | `78ebfed94d0021da` | M S3, S9 |

### S4 The 10 seeds (draft items; demo, not evaluation)

| qid | first relevant rank | first k with CE = 1 | rank-1 score | gap 1–2 | gap 4–5 |
|---|---|---|---|---|---|
| D-001 | 3 | 3 | 0.4929 | 0.0223 | 0.0894 |
| D-002 | 3 | 3 | 0.4606 | 0.0093 | 0.0998 |
| D-003 | 1 | 1 | 0.6497 | 0.0177 | 0.0137 |
| D-004 | 1 | 1 | 0.4210 | 0.0175 | 0.0120 |
| D-005 | 1 | 1 | 0.4272 | 0.0692 | 0.0065 |
| D-006 | 1 | 1 | 0.5331 | 0.0327 | 0.0237 |
| D-007 | 2 | 3 | 0.7094 | 0.0989 | 0.0053 |
| D-008 | 2 | 2 | 0.2598 | 0.0063 | 0.0006 |
| D-009 | — | — | 0.3099 | 0.0301 | 0.0150 |
| D-010 | — | — | 0.5196 | 0.0855 | 0.0013 |

| Fact | Value | Source |
|---|---|---|
| Distractors above the first relevant chunk (rank-1 winner: seq, page, margin, cos with the evidence chunk) | D-001: 1, p.1, +0.0237, 0.5899 (also seq 0 +0.0014) · D-002: 69, p.24, +0.0220, 0.7184 (also seq 68 p.23 +0.0127, cos 0.7802) · D-007: 69, p.24, +0.0989, 0.7184 · D-008: 28, p.10, +0.0063, 0.5133 | M S4 |
| D-003 mirror image | evidence seq 68 p.23 0.6497; near-duplicate seq 27 p.10 0.6320 | M S4 |
| Rank-1 scores, answerable: min / median / max | 0.2598 / 0.4767 / 0.7094 | M S4 |
| Answerable seeds below D-010's rank-1 (0.5196) / below D-009's (0.3099) | **5/8** / 1/8 | M S4 |
| Answerable seeds below 0.5 (L.2 C4-A-04, J4) | D-001, D-002, D-004, D-005, D-008 = 5 (read from the table) | M S4 |
| 70 adjacent gaps inside the top-8: min / median / max; below 0.01 | 0.00008 / 0.01556 / 0.14681; 28 | M S4 |

### S5 Ties

| Fact | Value | Source |
|---|---|---|
| Duplicate chunk texts; exact score ties over 10 seeds × 97 scores | 0; 0 | M S5 |
| Index ×2, rows shuffled (seed 7), D-002 top-4 seqs: tie rule by chunk_id | [69, 166, 68, 165] (lab CHECK 2c fingerprint `65b8cbacc1598a5b`) | M S5 |
| Same, ties by row (stable argsort) / argpartition only | [166, 69, 165, 68] / [166, 69, 68, 165] | M S5 |
| TOY: string sort of unpadded ids | `['c:10', 'c:2', 'c:9']`; padded: `['c:00002', 'c:00009', 'c:00010']` | M S5 |

### S6 k sweep (TOY ILLUSTRATION: 8 draft answerable items; tokens over all 10)

| k | Hit@k | CE@k | Group-Recall@k | P@k | mean context tokens (o200k_harmony, chunk text only) | CE = 0 for |
|---|---|---|---|---|---|---|
| 1 | 4/8 | 4/8 | 0.500 | 0.500 | 173.7 | D-001, D-002, D-007, D-008 |
| 2 | 6/8 | 5/8 | 0.688 | 0.500 | 345.8 | D-001, D-002, D-007 |
| 4 | 8/8 | 8/8 | 1.000 | 0.375 | 679.0 | — |
| 8 | 8/8 | 8/8 | 1.000 | 0.188 | 1,284.2 | — |

- Token ratios: k 1→2 ×1.99; 2→4 ×1.96; 4→8 ×1.89; 4→2 ×0.51 (DERIVED: 345.8 / 679.0). Chunk tokens min/median/max 68 / 162 / 192.
- P5 windows (91 chunks), same seeds: CE@k 3/8, 6/8, 7/8 (D-007 missing), 8/8; tokens 189.4, 383.1, 752.5, 1,475.0.
- Lab fingerprints: hit/ce `84011ffed49b16a9`; rounded tokens `f3407b9eb252ba2f`.

### S7 The query side

| Fact | Value | Source |
|---|---|---|
| MiniLM query norm without `normalize_embeddings` | 1.000000 | M S7 |
| Question embedded "as a document" vs as a query (MiniLM) | max abs diff 1.15e-07 (symmetric) | M S7 |
| Wrong query model `paraphrase-MiniLM-L3-v2` (snapshot `4ca70771…`): shape, error | (384,), no error; `V @ q` (97,) | M S7 |
| Wrong model, k = 4 | Hit@4 **3/8**, CE@4 3/8 (right model 8/8, 8/8); lab fingerprint `28e7165fc1adc5b4` | M S7 |
| Wrong model, D-002 top-4 | seqs [51, 68, 96, 92], pages [18, 23, 33, 31], scores 0.1858 … 0.1628; rank-1 0.1858 vs 0.4606 | M S7 |
| q × 3 | same ids; rank-1 score 1.3818 | M S7 |

### S8 Broken variants (k = 4, 8 answerable seeds)

| Fact | Value | Source |
|---|---|---|
| Ascending sort | Hit@4 0/8, CE@4 0/8; D-002 "top-4" scores −0.1536, −0.1149, −0.0855, −0.0837 | M S8 |
| Scores dropped | the D-002 margin 0.0220 between rank 1 and the evidence is invisible | M S8 |

### S9 Lab fingerprints

`78ebfed94d0021da` (D-002 ids) · `a8aa456e76ccea3b` (first_rel) · `179e0af8b77aa72a` (first_ce) · `84011ffed49b16a9` (sweep hit/ce) · `f3407b9eb252ba2f` (sweep tokens) · `28e7165fc1adc5b4` (wrong model) · `65b8cbacc1598a5b` (dup + shuffle). Three more were computed from S4 values with the same `_fp`: `35f37be3c6c19d49` (outranked = D-001, D-002, D-007, D-008), `34d696449531893c` (near_dup rounded 2: 0.59, 0.72, 0.72, 0.51), `844dde23504ee1fe` (top1 rounded 2), `ef2d127de37b942b` (n_below = 5). LT confirms all of them against a live solution.

### S-toy Part F and L.2 arithmetic (TOY)

Re-checked in Python: order `[c:00003, c:00001, c:00002, c:00000, c:00004]`; first relevant rank 3, margin 0.04; Hit@1/2/3 = 0/0/1; CE@3 = 0, CE@5 = 1; tokens k=3 510, k=5 780. C4-A-03: top-2 = `[c:00007, c:00002]`.

### S-src Citations (`c4_sources.py`: ALL PASS, 51 checks)

| Citation | Checked content |
|---|---|
| repo HEAD | `009adba2be1bef49780ef73b6dd3c18fd24b035b` |
| `simple_rag.ipynb` 10, 13, 15 | `FAISS.from_documents`; `search_kwargs={"k": 2}`; `retrieve_context_per_question` + `show_context`, no "score" in cell 15 |
| `helper_functions.py` L79/L117; L129, L131–L140, L143, L147, L149; L208–L220 | constant `relevance_score = 1.0`; the def; docstring promises a tuple with URLs; `get_relevant_documents`; `[doc.page_content for doc in docs]`; `return context`; `show_context` prints text only |
| `json_rag.ipynb` 21, 22, 23 | `IndexFlatL2`; markdown: same model, L2 distance, lower is better; `model.encode([query_text], ...)` without normalize, `NUM_NEIGHBORS = 5`, prints `Distance` |
| `multi_faceted_filtering.ipynb` 10, 12 | all-MiniLM-L6-v2 + Chroma; `similarity_search_with_relevance_scores(query, k=10)`, prints the score |
| `dartboard.ipynb` 13 | `embed_documents` used for the query |
| Repo scan | 9 of 41 notebooks call a score-returning search API (not `simple_rag`); 8 mention `get_relevant_documents`; dict-style `k` literals 1–5 (14 occurrences) |
| `langchain_core` 1.3.0 `retrievers.py` (older venv, text only) | no public `def get_relevant_documents`; `def invoke` and `_get_relevant_documents` present |
| `cohere` 7.2.0 `ClientV2.embed` (signature only) | `input_type` literals include `search_query`, `search_document` |
| Book (30 page-phrase checks) | Ch1 p.8, p.9, p.10, p.12/14; Ch6 p.1/14; App p.13/23; Ch11 p.2/13; Ch12 p.6, p.7/14; Ch13 p.2, p.10/13; Ch15 p.1/12; App p.20, p.22/23; Ch20 p.1, p.4/11; Ch22 p.4, p.11/19 |
| Book absence scan | "choose k": 0 pages; "input type": 0; "query prefix/instruction": 0; "argpartition": 0; "tie": 1 page (Ch12 p.10, not about ranking ties) |

### LT Lab test (`out_c4_lab_test.txt`, notebook sha256 `90e75b85…`; re-run after the row-alignment and embed_hash decisions)

| Variant (throwaway, outside WS) | CHECKs passed | Fails |
|---|---|---|
| good | **10/10** | — |
| blank | 0/10 | all (predictions missing / names undefined) |
| no tie rule (stable argsort) | 9/10 | 2c |
| ties by row index | 9/10 | 2c |
| ascending sort | 3/10 | 2a, 2c, 3, 4, 5, 6, 7 |
| query embedded as a document | 9/10 | 2b (2a passes: MiniLM is symmetric) |
| scores dropped | 4/10 | 2a, 2c, 3, 4, 5, 6 |
| `np.float32` scores | 9/10 | 2a |
| chunk × chunk "similarity matrix" | 9/10 | 1 |

The good solution also proves that the lab's given `rel` / `ce` helpers agree with `contracts_check.py` (same fingerprints as M).

## 2. Interface assumptions (recorded for C3, C5, C6)

See lesson H.4. In short: input = C3's `vectors.npy` / `chunks.jsonl` / `manifest.json` (row i of `vectors.npy` = line i of `chunks.jsonl`; `seq` restarts per document, never used as a row number; folder `index/<snapshot_id>/<params_hash>/<embed_hash>/`; `manifest.embedding.model_id` and `embed_hash` present; C3's `embed_hash` value is authoritative); output = rank-ordered dicts `{rank, chunk_id, doc_id, page, char_start, char_end, score, text}`, `score` a Python float cosine, ties by `chunk_id` string; the trace drops `text`. `.env` names the Cohere model `COHERE_EMBED_MODEL` while 06 §2.4 writes `COHERE_EMBED_MODEL_ID`.

## 3. UNVERIFIED

The Cohere `input_type` effect on our data (lab Task 8, off by default); whether the LLM answers 1997 for D-002 (C5); LangChain/Chroma relevance-score conversion; `invoke` at runtime; any claim about the full eval set (the seeds are drafts).
