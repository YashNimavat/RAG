# C3_FACTS — what the C3 lesson can rely on (run-verified)

Run date: **2026-10-08**. Every number in [`concepts/C3_embedding_indexing.md`](../../../concepts/C3_embedding_indexing.md) is listed here with the command and the output section that produced it. Numbers not produced by these runs are marked CITED (from an earlier logged run or file), DERIVED (arithmetic shown in the lesson), ASSUMPTION or UNVERIFIED.

## 0. Environment, provenance, how to re-run

- **Interpreter.** CPython 3.12.8 (Windows 11), the project uv environment (`rag_learning/.venv`). Nothing was installed.
- **Versions** (printed in S1): pymupdf 1.26.7 · numpy 2.5.3 · sentence-transformers 6.1.0 · torch 2.14.1 (CPU) · transformers 5.19.0.
- **Machine** (printed in S9): 11th Gen Intel Core i7-11800H @ 2.30GHz, 16 logical CPUs.
- **Corpus.** `upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf`, SHA-256 `1d58a0fa…92669`, 206,372 bytes, 33 pages. Text: `page.get_text()` per page, joined with `"\n"`, no cleaning (06 §5.3). Snapshot id recomputed with the 06 §5.3 recipe **executed from the 06 text** (through `contracts_check.py`): `ea07572562ac` (matches 06).
- **Chunker (course-wide interface decision, 2026-10-08).** The 06 §2.4 `chunking:` block, exactly: `{"name": "recursive_char", "unit": "chars", "chunk_size": 1000, "chunk_overlap": 200, "separators": ["\n\n", "\n", " ", ""], "scope": "per_page"}`. `params_hash = sha256(json.dumps(block, sort_keys=True).encode("utf-8")).hexdigest()[:12]` = **`1ca9c5a3b548`**. `chunk_id = f"{doc_id}:{snapshot_id}:{params_hash}:{seq:05d}"` (06 §2.3). The given chunker reproduces the **C2 lab's v0 output byte for byte**: `chunks.jsonl` 97 lines, 122,774 bytes, sha256 `d4108b89…011b` ([C2LAB_FACTS](../C2lab/C2LAB_FACTS.md), Save row).
- **Models.** `sentence-transformers/all-MiniLM-L6-v2` (L6, snapshot `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`) and `sentence-transformers/paraphrase-MiniLM-L3-v2` (L3, snapshot `4ca70771034acceecb2e72475f72050fcdde4ddc`), offline from the HF cache.
- **Not run.** No Groq or Cohere call; `.env` never read. No faiss, no LangChain in the project env (library source read as text only, from the learner's older venv).
- **Scripts** (this folder):

  | Script | What it produces | Saved output |
  |---|---|---|
  | `c3_measure.py` | S1–S9: snapshot and records, params_hash, cache key, cache and edits, normalisation, the three files, the rebuild rule, the CR-08 probe, timings. Writes only to a temp folder, deleted at the end | `out_c3_measure.txt`, `out_c3_measure.stderr.txt` (model-loading bars and one tokenizer length warning) |
  | `c3_sources.py` | S-src: repo cells (0-based), helper lines, repo-wide scans, LangChain source lines, book pages and a book-wide absence scan | `out_c3_sources.txt` (ALL PASS, 90 checks) |
  | (outside the workspace) `scratchpad/c3/build_lab.py`, `solution.py`, `run_lab.py` | LT: builds the notebook; runs it with a throwaway solution and 13 broken or blank variants, each in a fresh process, writing only to a scratch folder | `out_c3_lab_test.txt` (copied here) |

- **Re-run** (from `rag_learning/`, Git Bash):
  ```bash
  B="C:/Yash/New-Work/Book RAG"
  PYTHONIOENCODING=utf-8 uv run python sources/verification/C3/c3_measure.py \
      "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
      > sources/verification/C3/out_c3_measure.txt 2> sources/verification/C3/out_c3_measure.stderr.txt
  PYTHONIOENCODING=utf-8 uv run python sources/verification/C3/c3_sources.py "$B/upstream/RAG_Techniques" \
      "$B/RAG_Made_Simple_The_Complete_Visual_Guide" "C:/Yash/New-Work/RAG/RAG_Techniques-main/venv/Lib/site-packages" \
      > sources/verification/C3/out_c3_sources.txt
  ```
- **Determinism.** Two consecutive runs of the final `c3_measure.py` gave **identical S1–S8 output** (diffed). S9 timings vary: cold embed 1.77–6.31 s, all hits 16–92 ms, load 2.0–11.1 ms across runs; the two runs after the embed_hash change were slow because other jobs shared the CPU.
- **File hashes at the time of the run** (sha256, first 16): `c3_measure.py` `b31c91b2f2498b9b`, `c3_sources.py` `50f572e913247a15`, `labs/C3_indexing_lab.ipynb` `b81a4a97b5f4785b`.

## 1. Facts by section

`M` = `c3_measure.py` (section in `out_c3_measure.txt`); `S` = `c3_sources.py`; `LT` = lab test.

### S1 Snapshot and chunk records

| Fact | Value | Source |
|---|---|---|
| Pages / document characters / page length min–max | 33 / 72,593 / 636–2,494 | M S1 |
| `snapshot_id` (06 recipe, executed) | `ea07572562ac` (matches 06 §5.3) | M S1 |
| `params_hash` of the 06 block | `1ca9c5a3b548` | M S1 |
| Records | 97, all single-page (`page_segments` length 1), text == `doc_text[char_start:char_end]` 97/97, no duplicate texts, lengths 393–1,000 | M S1 |
| Same spans, text, `text_sha256`, `page_segments` as 07 H.3 `chunk_document(recursive, 1000/200)` | 97/97 (07's own ids carry `77bc4c45809b`, from 07's field names) | M S1 |
| `chunks.jsonl` equals the C2 lab's v0 file | True (sha256 `d4108b89…011b`, 122,774 bytes) | M S1, S6 |
| First / last id | `climate:ea07572562ac:1ca9c5a3b548:00000` … `:00096`; first record [0, 949) p.1 | M S1 |

### S2 params_hash

| Fact | Value | Source |
|---|---|---|
| Same inputs twice | same hash; same ids 97/97 | M S2 |
| Two fresh processes (`PYTHONHASHSEED` 1 and 2) | sha256 recipe `1ca9c5a3b548` both times; built-in `hash()` gave two different numbers | M S2 |
| One field changed → new hash | 7/7 (name, chunk_size 500, chunk_size 1001, chunk_overlap 100, unit, scope, separators without `""`); 8 distinct hashes over 8 configs | M S2 |
| Keys in reverse order | equal with `sort_keys=True`; different without (`3ca84ee566b2` vs `99af0d35e01b`) | M S2 |
| `chunk_size` `"1000"` (string) vs `1000` | different hashes | M S2 |
| BROKEN hash over chunk_size + chunk_overlap only, per_page vs cross_page | per_page 97, cross_page 92 chunks, same hash; **92 ids shared, 89 of them name different text** | M S2 |
| Correct hash: ids shared per_page vs cross_page | 0 | M S2 |

### S3 Embedding cache key

| Fact | Value | Source |
|---|---|---|
| `sha256(provider\|model_id\|revision\|input_type\|preproc_version\|text)` equals 07 H.3 `embedding_cache_key` | True (`b10f3fc4459980f0…` for "hello\|world", L6 spec) | M S3 |
| Each of the 5 meta fields and the text changes the key | 6/6 | M S3 |
| Without the `"\|"` guard, `('a','b\|c',…)` and `('a\|b','c',…)` collide | True | M S3 |

### S4 Cache, edits, model switch

| Fact | Value | Source |
|---|---|---|
| Build 1 / build 2 | 0 hits, 97 misses, 97 texts sent in 1 call / 97 hits, 0 sent, vectors identical | M S4 |
| Cache file per vector | 1,664 bytes (`.npy`, 384 float32 + header) | M S4 |
| L6 raw norms | 1.000000–1.000000 (it has a Normalize module) | M S4 |
| Edit: +9 chars at page-10 offset 100 | new snapshot `09d2abdba8b6`; still 97 chunks; **ids unchanged 0/97**; cache **96 hits, 1 miss**, 1 text sent | M S4 |
| Same edit, recursive cross-page (92 chunks) | 91 hits, 1 miss | M S4 |
| Same edit, **fixed** 1000/200 windows across pages (07 `fixed`, contrast) | 91 chunks; **25 hits, 66 misses** | M S4 |
| Switch to L3, full key | 0 hits, 97 misses, 97 texts sent | M S4 |
| BROKEN text-only key, switch to L3 | 97/97 hits; served vectors = the L6 vectors; shape (97, 384) as L3's: no error | M S4 |
| D-002 evidence span (06 §6.7, p.10 [438, 537) → doc [20993, 21092)) | whole in chunk seq 27; rank **3** with the correct index; rank **16** with stale L6 vectors and an L3 query | M S4 |
| Encoding twice, batch 64 | bit-identical | M S4 |
| Batch 64 vs batch 1 | 0/97 rows bit-identical; max abs diff 1.34e-07 | M S4 |

### S5 Normalisation

| Fact | Value | Source |
|---|---|---|
| L3 modules / raw norms | Transformer, Pooling (no Normalize) / 2.3636–3.4741 | M S5 |
| After `cached_embed` | max \|norm − 1\| 1.19e-07 | M S5 |
| L3 index stored unnormalised vs normalised, 34 queries (33 page heads + D-002) | top-4 identical **7/34**; top-1 identical 34/34 | M S5 |
| D-002 top-4 rows | unnormalised [69, 27, 68, 17]; normalised [69, 68, 17, 27] | M S5 |

### S6 The three files

| Fact | Value | Source |
|---|---|---|
| Folder (course decision) | `index/ea07572562ac/1ca9c5a3b548/c398eeba043f/` = `index/<snapshot_id>/<params_hash>/<embed_hash>/` | M S6 |
| `embed_hash` (sha256 of sorted-key JSON of provider, model_id, revision, input_type, normalize, preproc_version; first 12 hex) | L6 `c398eeba043f`; L3 `ae47e2c1e13f`; only `dim` changed: unchanged; queries' input_type changed: `f9a0a305cd54`; normalize false: `49162ab49b54` | M S6 |
| Two embedders, one chunking | L6 and L3 folders side by side under `1ca9c5a3b548`; L6 files unchanged; writing L3 into the L6 folder raises `FileExistsError` | M S6 |
| Sizes | `vectors.npy` 149,120 = 128 + 97 × 384 × 4; `chunks.jsonl` 122,774 (mean 1,265.7 per line); `manifest.json` 1,526 | M S6 |
| `manifest.json` sha256 (what a trace stores as `index_manifest_hash`) | `eeda621f…b907` | M S6 |
| Round trip | vectors equal, chunks equal, text slice 97/97 | M S6 |
| Rebuild from the cache into a new folder | all three files byte-identical; 97 hits | M S6 |
| D-002 top-5 (line in `chunks.jsonl`, page, score) on the loaded index | (69, p.24, 0.4606), (68, p.23, 0.4513), (27, p.10, 0.4386), (17, p.6, 0.4385), (84, p.29, 0.3387) | M S6 |
| Cohere `embed-v4.0` size at 97 chunks | 596,096 bytes = 128 + 97 × 1,536 × 4 (DERIVED; 1,536 CITED from the O2 report) | M S6 |
| Repo `context_enrichment_window_around_chunk.ipynb` cell 13 pattern, re-implemented on the same PDF (`read_pdf_to_string`, 400/200) | 363 chunks × 72,561 chars = **26,339,643** characters of metadata | M S6 |

### S7 Rebuild rule and the manifest gate

| Fact | Value | Source |
|---|---|---|
| 16 scenarios | reuse: nothing changed, k, LLM, prompt, reranker, query input type; `chunker`: size, overlap, scope; `snapshot`: text edit; `embedding`: model, revision, document input type, preprocessing, normalize; both: snapshot + model. Fingerprint `d4de412a44e2aff8` (= lab CHECK 5) | M S7 |
| `load_index` refusals | a chunks.jsonl missing its first line (sha256 and 97 vs 96 lines), a 2000/400 config (chunker), an L3 config (embedding) | M S7 |
| "Folder exists → load it" pattern after changing to 500/100 | loads the 97 chunks built at 1000/200 (500/100 would give 201); no error; the manifest gate says `['chunker']` | M S7 |

### S8 CR-08 probe: chunk size doubles

| Fact | Value | Source |
|---|---|---|
| 1000/200 | 97 chunks; max 182 MiniLM tokens; 0 over 256 | M S8 |
| 2000/400 | 65 chunks; `params_hash` `e1b698244452`; 0 ids shared; max 365 tokens; **32 over 256** | M S8 |
| Cache hits for 2000/400 after the 1000/200 build | 12 hits, 53 misses (1 whole short page + 11 other identical texts) | M S8 |
| `vectors.npy` at 2000/400 | 99,968 bytes (DERIVED) | M S8 |

### S9 Timings (machine-specific)

| Fact | Value | Source |
|---|---|---|
| Embed 97 chunks, empty cache (median of 3) | 6.31 s in the saved run (1.77–6.31 s across runs) | M S9 |
| Same, all cache hits | 92.0 ms in the saved run (16–92 ms across runs) | M S9 |
| `load_index` with every check | 11.1 ms in the saved run (2.0–11.1 ms across runs) | M S9 |

### S-src Citations

| Fact | Source |
|---|---|
| Repo HEAD `009adba2…`; `helper_functions.py` L18, L30, L48, L62, L67, L69, L70, L73, L74, L223, L244, L338, L354, L357 | S |
| Cells: `simple_rag` 10; `local_rag_huggingface_faiss` 10, 12, 14, 16 (save/load lines commented out); `hierarchical_indices` 11, 13; `context_enrichment_window_around_chunk` 11, 13, 15, 17, 23, 25; `memorag` 22; `reliable_rag` 6; runnable script `hierarchical_indices.py` L94, L100–L101 | S |
| Repo-wide (code, comments stripped): `save_local`/`load_local` in 3 files; `input_type`, `manifest`, `params_hash`, `revision`, `add_start_index`, `np.save(` in **0**; `OpenAIEmbeddings()` with no model in 29 places | S |
| LangChain `faiss.py` 0.4.1: `save_local` writes `index.faiss` + pickled `(docstore, index_to_docstore_id)`, no model identity (L1147–L1164); `load_local` takes the caller's `embeddings` and requires `allow_dangerous_deserialization` (L1167–L1216). `langchain_cohere` 0.5.1: `embed_documents` → `search_document` (L195), `embed_query` → `search_query` (L217), `model` required (L109) | S (read, not run) |
| Book pages: Ch1 p.5, 6, 7, 12/14; Ch7 p.4/11; Ch8 p.4/11; Ch11 p.6, 10/13; Ch13 p.6/13; Ch14 p.9, 10/13; Ch15 p.12/12; Ch16 p.4/11; App p.16, 22/23 | S |
| Whole-book absence scan: hash 0 pages, manifest 0, re-index 0, rebuild 0, re-embed 0, input type 0, unit length 0, revision 0, pickle 0; "cache" only Ch18 p.4/12 (an example user question) | S |

### LT Lab test

| Variant | Result |
|---|---|
| good | 7/7 CHECK cells pass |
| blank | 1/7 (only the written Task 7, which is graded by the tutor) |
| hash ignores `scope` | fails CHECK 1 and 5 |
| hash without `sort_keys` | fails CHECK 1 |
| built-in `hash()` | fails CHECK 1 |
| cache key without `input_type` | fails CHECK 2 |
| cache keyed on text only | fails CHECK 3 ("only 0 were sent") |
| unnormalised vectors | fails CHECK 3 (L3 rows not unit) |
| `write_index` overwrites a different index | fails CHECK 4 (and 6) |
| `embed_hash` that keeps `dim`/`max_seq_length` | fails CHECK 4 |
| rebuild on any embedding-dict change | fails CHECK 5 (query input type) |
| rebuild ignores revision | fails CHECK 5 |
| loader without checks | fails CHECK 6 |
| loader without the norm check | fails CHECK 6 |

## 2. Interface assumptions (06 is the source of truth; these fill its gaps)

1. **params_hash input and recipe:** the 06 §2.4 `chunking:` block with 06's key names, `sha256(json.dumps(block, sort_keys=True))[:12]`, default separators (coordinator decision 2026-10-08; same as the C2 lab). 07 H.3 hashes `asdict(ChunkerConfig)` with other key names (`size`, `overlap`, 3 separators), which gives `77bc4c45809b` for the same spans; that is a different id namespace and is not used.
2. **params_hash covers the chunker only.** The embedding settings are not in it (so chunk ids survive a model change). They live in `manifest.embedding` and in the embedding cache key.
3. **`manifest.json` keys** (06 §2.2 lists the content, not the names): `snapshot_id`, `docs` [`doc_id`, `pdf_sha256`, `doc_text_sha256`], `parser` {`backend`, `version`}, `chunker` (the hashed block), `params_hash`, `embedding` {`provider`, `model_id`, `revision`, `input_type` {`documents`, `queries`}, `preproc_version`, `normalize`, `dim`, `max_seq_length`}, `library_versions`, `created_utc`, `files` {`vectors.npy` {`sha256`, `shape`, `dtype`}, `chunks.jsonl` {`sha256`, `lines`}}. Names taken from 06 where 06 has them (§2.4 embedding block, §5.3 manifest, §2.3 `Embedder`); `docs`, `library_versions` and `files` are proposed here.
4. **`input_type` for a model without one** is the string `"none"` (07 H.3). **`revision` for an API model** is `null` in the manifest and `"None"` (via `str()`) in the cache key; 06 §2.4 says to record the model id plus the date. Whether Cohere keeps `embed-v4.0` vectors stable over time is UNVERIFIED.
5. **`preproc_version`** is `"none"` in v0: any change to the text between the chunk record and the embedder (tab replacement, a contextual header, a prefix) needs a new value.
6. **Cache layout:** `.cache/emb/<key>.npy`, one raw provider vector per file, float32; normalisation happens after reading. Internal to C3; C4 does not read it.
7. **Index folder (course decision 2026-10-08, replaces the earlier open question):** `index/<snapshot_id>/<params_hash>/<embed_hash>/`; `embed_hash` is recorded in the manifest next to `params_hash`; `write_index` still refuses to overwrite a folder whose manifest differs, and `load_index` recomputes both hashes from the manifest's own blocks. Note: `embed_hash` includes the queries' `input_type`, so a query-only change gets a new folder although `rebuild_reasons` reports the vectors reusable; building it re-embeds nothing (document-side cache keys unchanged; derived from the key, not separately run).
9. **Row order (course decision 2026-10-08):** row *i* of `vectors.npy` ↔ line *i* of `chunks.jsonl`, by position. Nothing assumes `seq == i` (`seq` restarts per document). The S6 smoke test reports line numbers.
8. **Query-side settings** (`input_type.queries`) are recorded in the manifest but do not trigger a rebuild; C4 must embed queries with them.

## 3. Still UNVERIFIED

- Cohere `embed-v4.0`: raw vector norms, how far `search_query` and `search_document` vectors of the same text differ, determinism over time. Only the dimension (1,536) and the context length (8,192) are known (O2 report). Lab Task 8 measures the first two, if the learner runs it.
- How the repo's LangChain versions behaved (the repo pins none). `helper_functions.py` L357 `CohereEmbeddings()` with no model would fail the model validator of `langchain_cohere` 0.5.1 (read, not run).
- Whether bit-level differences between batch sizes (1.34e-07) ever change a top-k on our data (not measured).
