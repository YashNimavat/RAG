# C6_FACTS — what the C6 lesson can rely on (run-verified)

Run date: **2026-10-08** (S11 lab test re-run 2026-10-09). Every number in [`concepts/C6_v0_pipeline.md`](../../../concepts/C6_v0_pipeline.md) is listed here with the script and output section that produced it. Anything not produced by these runs is marked CITED (from another logged run), DERIVED (arithmetic shown in the lesson), TOY or UNVERIFIED.

## 0. Environment, provenance, how to re-run

- **Interpreter.** CPython 3.12.8 (Windows 11), the project uv environment. Versions (S1): pymupdf 1.26.7 · numpy 2.5.3 · sentence-transformers 6.1.0 · torch 2.14.1+cpu · tiktoken 0.14.0.
- **Corpus D.** `upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf`, sha256 `1d58a0fa…92669`, 206,372 bytes (repo pinned at `009adba`).
- **Retrieval-only reference run.** Load → snapshot → chunk → embed (local MiniLM `all-MiniLM-L6-v2`, revision `1110a243…`, `HF_HUB_OFFLINE=1`) → index → retrieve (k = 4) → prompt (built and hashed) → trace. **No Groq or Cohere call; `.env` never read.** Generation is **not run**: D-002 carries a **hand-written TOY answer**; every other answer is `null` with an error string.
- **Course interface decisions applied** (06 §2.4 "Interface decisions", 2026-10-08): `params_hash = sha256(json.dumps(CHUNKING, sort_keys=True))[:12]` over 06 §2.4's `chunking:` block = **`1ca9c5a3b548`**; `embed_hash` = 12 hex of sha256 of the six-field embedding block (C3's field values) = **`c398eeba043f`**; index folder `index/<snapshot_id>/<params_hash>/<embed_hash>/`; row i of `vectors.npy` = line i of `chunks.jsonl` (no code assumes `seq == i`); spans come from the 07 H.1/H.3 code as written; `chunks.jsonl` is written in 06 §2.3 key order. It is **byte-identical to the C2 lab's output** (sha256 `d4108b89…3011b`, C2LAB_FACTS).
- **Scripts** (this folder):

  | Script | Produces | Saved output |
  |---|---|---|
  | `c6_reference_v0.py <pdf> <out_dir>` | S1–S7 (writes index and run files to `<out_dir>`, kept **outside** the workspace because `chunks.jsonl` holds corpus text) | `out_c6_reference_v0.txt` (+ `.stderr.txt`: model-loading bar only); `example_trace_D-002.json`, `example_index_manifest.json` |
  | `c6_compare_runs.py <run1> <run2>` | S8 rebuild reproducibility | `out_c6_compare_runs.txt` |
  | `c6_interface_checks.py <pdf>` | S9 06-vs-07 chunker interface | `out_c6_interface_checks.txt` |
  | `c6_toy_traces.py` | S10 TOY traces + reference ladder | `toy_traces.json`, `out_c6_toy_traces.txt` |
  | `c6_sources.py <repo> <book> [run1]` | S-src: every repo cell/line and book page cited | `out_c6_sources.txt` (**122 PASS, ALL PASS**) |
  | (outside WS) lab runner, throwaway solution | S11 lab test | `out_c6_lab_test.txt` |

- **Re-run** (from `rag_learning/`, Git Bash; `$SP` = any scratch folder outside the workspace):
  ```bash
  B="C:/Yash/New-Work/Book RAG"; PDF="$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"; D=sources/verification/C6
  PYTHONIOENCODING=utf-8 uv run python $D/c6_reference_v0.py "$PDF" "$SP/c6run1" > $D/out_c6_reference_v0.txt 2> $D/out_c6_reference_v0.stderr.txt
  PYTHONIOENCODING=utf-8 uv run python $D/c6_reference_v0.py "$PDF" "$SP/c6run2" > /dev/null 2>&1
  PYTHONIOENCODING=utf-8 uv run python $D/c6_compare_runs.py "$SP/c6run1" "$SP/c6run2" > $D/out_c6_compare_runs.txt
  PYTHONIOENCODING=utf-8 uv run python $D/c6_interface_checks.py "$PDF" > $D/out_c6_interface_checks.txt
  PYTHONIOENCODING=utf-8 uv run python $D/c6_toy_traces.py > $D/out_c6_toy_traces.txt
  PYTHONIOENCODING=utf-8 uv run python $D/c6_sources.py "$B/upstream/RAG_Techniques" "$B/RAG_Made_Simple_The_Complete_Visual_Guide" "$SP/c6run1" > $D/out_c6_sources.txt
  ```
- **Latencies** are from one run on this machine and vary between runs (two runs differ); they are reported as "one run", never as results.

## 1. Facts by section (`R` = `out_c6_reference_v0.txt`)

### S1 Load and snapshot
| Fact | Value | Source |
|---|---|---|
| Pages / characters of `doc_text` | 33 / 72,593 | R S1 |
| `snapshot_id` | `ea07572562ac` (= 06 §5.3) | R S1 |
| Page 10 starts at document offset | 20,555 (= 06 §5.3) | R S1 |
| Tab characters in PyMuPDF text | **0** (the repo's `replace_t_with_space` would change nothing here) | R S1 |

### S2 Chunk
| Fact | Value | Source |
|---|---|---|
| `params_hash` (06 block, course recipe) | `1ca9c5a3b548` | R S2 |
| 07 `ChunkerConfig(recursive, 1000, 200).params_hash()` (same spans) | `77bc4c45809b` | R S2 |
| Chunks; length min / median / max | **97**; 393 / 935 / 1,000 chars | R S2 |
| Chunks per page | 1–3 (32 pages have 3, one page has 1) | R S2 (DERIVED: 32×3 + 1 = 97) |
| Invariants (text = `doc_text[a:b]`; one page segment each; `text_sha256`; 0 < len ≤ 1,000) | all True | R S2 |
| First / last id | `climate:ea07572562ac:1ca9c5a3b548:00000` / `…:00096` | R S2 |
| `chunks.jsonl` sha256 | `d4108b89…3011b` = C2 lab output | R S4 |

### S3 Embed (local MiniLM fallback)
| Fact | Value | Source |
|---|---|---|
| `V` | (97, 384) float32, max \|norm − 1\| 1.19e-07 | R S3 |
| MiniLM tokens per chunk (with [CLS]/[SEP]) min / median / max | 59 / 149 / 182; over 256: **0** | R S3 |
| Distinct embedding cache keys | 97 for 97 chunks | R S3 |
| Embed 97 chunks / load model | ~1.7–2.3 s / ~0.43 s (one run each, CPU) | R S3 |

### S4 Index files (`index/ea07572562ac/1ca9c5a3b548/c398eeba043f/`)

`embed_hash` input: `{"input_type": {"documents": "none", "queries": "none"}, "model_id": "sentence-transformers/all-MiniLM-L6-v2", "normalize": true, "preproc_version": "none", "provider": "sentence_transformers", "revision": "1110a243…"}` → `c398eeba043f`; written into `manifest.json` (R S4).

| File | Bytes | sha256 (16) |
|---|---|---|
| `vectors.npy` | 149,120 (= 128 + 97 × 384 × 4, DERIVED) | `883bc50dd318e978` |
| `chunks.jsonl` | 122,774 | `d4108b8936093394` |
| `manifest.json` | 1,297 | `84931e43cca963c0` (= `index_manifest_hash`) |

### S5 Ten queries (retrieval only; k = 4; gold = 06 §6.7 **drafts**)
| qid | Top-4 (page#seq, score) | Gold page(s) → first rank holding the gold span | CE@4 | rank4 − rank5 gap |
|---|---|---|---|---|
| D-001 | p.1#1 .4929, p.1#0 .4706, p.3#7 .4692, p.3#8 .4608 | p.3 → 3 | 1 | 0.0894 |
| D-002 | p.24#69 .4606, p.23#68 .4513, p.10#27 .4386, p.6#17 .4385 | p.10 → 3 | 1 | 0.0998 |
| D-003 | p.23#68 .6497, p.10#27 .6320, p.6#17 .5351, p.24#69 .4791 | p.23 → 1 | 1 | 0.0137 |
| D-004 | p.23#67 .4210, p.8#23 .4035, p.23#68 .3604, p.10#27 .2136 | p.23 → 1 (p.8 → 2) | 1 | 0.0120 |
| D-005 | p.2#3 .4272, p.2#4 .3581, p.1#2 .3521, p.2#5 .3192 | p.2 → 1 (both groups) | 1 | 0.0065 |
| D-006 | p.8#21 .5331, p.22#64 .5004, p.5#14 .4772, p.5#13 .4696 | p.8 → 1 (both groups) | 1 | 0.0237 |
| D-007 | p.24#69 .7094, p.10#27 .6105, p.29#85 .5954, p.29#84 .5902 | p.10 → 2, p.29 → 3 | 1 | 0.0053 |
| D-008 | p.10#28 .2598, p.24#69 .2535, p.20#58 .2478, p.5#12 .2041 | p.24 → 2 | 1 | **0.0006** |
| D-009 | p.29#85 .3099, p.10#27 .2798, p.24#69 .2738, p.29#84 .2571 | none (unanswerable) | — | 0.0150 |
| R-001 | p.1#2 .6505, p.1#1 .6319, p.1#0 .5921, p.3#7 .5799 | no label | — | 0.0101 |

- **All 8 answerable drafts have CE@4 = 1** with this model (no retrieval miss at k = 4). D-002: rank 3 (p.10, 0.438607) vs rank 4 (p.6, 0.438527): gap **0.00008** (S6, DERIVED). D-009's rank-1 score (0.3099) is higher than D-008's (0.2598).
- Prompt `input_tokens` (o200k_harmony, local count, system + user): 771–896 across the ten; D-002: **802**; context tokens 610–738.
- Trace record size: **2,029–2,267 bytes** per record in the final run (median ~2,110; earlier runs 2,025–2,266); `results.jsonl` ~21.3 KB for 10. Sizes change by a few bytes between runs because latency values differ.
- Dense scoring of 97 chunks: about 0.07–1.5 ms per query; query embedding about 7–70 ms (values seen across the runs of this script on this machine; not a benchmark).

### S6 One query through every artifact (D-002)
| Rank | chunk seq / row | Page, page-relative → document offsets | Score (stored = recomputed) |
|---|---|---|---|
| 1 | 69 | p.24 [0, 982) → [51,414, 52,396) | 0.460613 |
| 2 | 68 | p.23 [1,547, 2,204) → [50,756, 51,413) | 0.451299 |
| 3 | 27 | p.10 [0, 951) → [20,555, 21,506) | 0.438607 |
| 4 | 17 | p.6 [1,566, 2,389) → [13,112, 13,935) | 0.438527 |

Gold D-002 (p.10 [438, 537)) → document [20,993, 21,092), wholly inside rank 3. TOY answer "The Paris Agreement was adopted in 2015 [climate:10]." → citation resolves to `…:00027` (rank 3). Full record: `example_trace_D-002.json`.

### S7 What changes `params_hash`
| Config | `params_hash` |
|---|---|
| 06 block (v0) | `1ca9c5a3b548` |
| 06 block, `chunk_overlap` 100 | `747bbb59942a` |
| 06 block, `scope` cross_page | `5f815e69a7e0` |
| 07 `ChunkerConfig` defaults (recursive, 3 separators) | `77bc4c45809b` |
| 07 `ChunkerConfig` name `recursive_char` + `""` separator | `0ad9b961bc23` |

Cross-page scope (07 code): 92 chunks, 41 span two pages.

### S8 Rebuild reproducibility (`out_c6_compare_runs.txt`, two separate processes): ALL PASS
Same index path; `params_hash` identical; 97 chunk ids identical; `vectors.npy`, `chunks.jsonl`, `manifest.json`, `config.json`, snapshot manifest **byte-identical**; trace records identical **after removing `timestamp_utc` and `latency_ms`**; `results.jsonl` as a whole is **not** byte-identical (expected).

### S9 Interface checks (`out_c6_interface_checks.txt`)
- 06 §2.4 separators `["\n\n", "\n", " ", ""]` vs 07 H.1 default `("\n\n", "\n", " ")` (char fallback built in). Passing `""` to the 07 code **hangs** (20 s timeout) on a text with a 1,200-character whitespace-free run (`text.find("", i, end) == i`, the loop never advances).
- On Corpus D the two separator lists give **identical spans** (97 chunks); the longest whitespace-free run is 18 characters.
- 06's chunker name `recursive_char` is not a key of the 07 REGISTRY (`fixed`, `recursive`).

### S10 TOY traces (`out_c6_toy_traces.txt`; all made up)
Toy manual: 5 pages, 520 characters, 17 chunks (one per line, lines cut at 60 characters, no overlap), toy k = 2.

| qid | Planted | Ladder result |
|---|---|---|
| TOY-1 | ok | ok |
| TOY-2 | parse (hyphenation `gen-\nerator`) | parse |
| TOY-3 | chunk (sentence cut at 60 characters) | chunk |
| TOY-4 | retrieve | retrieve |
| TOY-5 | generate:citation (cites p.4, context p.5) | generate:citation |
| TOY-6 | generate:grounding (8-hour vs 12-hour) | generate:grounding |
| TOY-7 | retrieve (correct answer, cites a non-retrieved page) | retrieve |

Labels fingerprint `24494e44adb7c4d6`. A generation-first ladder disagrees only on TOY-7. Pitfall found while building it: counting the page number inside `[toy:1]` as a claim mislabels TOY-1 as grounding.

### S11 Lab test (`out_c6_lab_test.txt`)
Throwaway solution + runner kept outside WS; outputs in a scratch `OUT_ROOT`. Good solution **12/12** CHECK cells (exec harness) and **12/12** in a real Jupyter kernel; blank notebook **0/12**; **21/21** broken variants fail at their intended CHECK (order, cleaning, snapshot newline, unsorted params JSON, page-relative offsets, unpadded ids, `load_index` never refusing, unnormalised vectors, unsorted `embed_hash` JSON, index folder without the `embed_hash` level, no tie rule, unsorted prompt hash, fake answer labelled groq, candidates keeping text, config hash not over file bytes, a manifest nonce, walk using page offsets, wrong TOY-7 label, generation-first ladder, page markers counted as numbers, a one-command run with another k). Groq/Cohere/Corpus T cells **not run**.

**Re-run 2026-10-09 (round 4; notebook sha256 `27fd7030…b182`).** Task 10 now has the open-coding table, and its given printer counts the two C5 finish_reason flags. Every result above is unchanged. The printer prints `length_stop 0 | unexpected_finish_reason 0` for the good solution (the fake client always returns "stop"). Two new variants, all 12 CHECKs passing in both:

| Variant | Fake client returns | Printer's run line | Mismatch line |
|---|---|---|---|
| `finish_length_and_none` | "length" for D-001, `None` for D-009 | `length_stop 1 \| unexpected_finish_reason 1` | none |
| `finish_flags_missing_in_make_answer` | the same, with a `make_answer` that never sets the two flags | `length_stop 0 \| unexpected_finish_reason 0` | names D-001 and D-009 |

These are toy finish_reason values written by the harness. How often a real Groq run stops at "length" is UNVERIFIED.

### S-src Sources (`out_c6_sources.txt`, 122 PASS)
Repo HEAD `009adba…`; `simple_rag.ipynb` 22 cells (11 code), cells 3, 5, 10, 11, 13, 15, 17; `helper_functions.py` L18–L31, L48–L76, L129–L149 (L147 keeps `page_content` only), L208, L336–L362; `rs/simple_rag.py` L18, L23, L36–L38, L55–L57, L61; `local_rag_huggingface_faiss.ipynb` cells 10–30 (no saved outputs at all); `simple_rag_with_llamaindex.ipynb` cells 4, 11, 13, 16, 23; `evaluation/evalute_rag.py` signature. Repo cell 15's two saved contexts start like our R-001 ranks 1–2 (first 120 characters, whitespace-normalised). Book: Ch1 p.1–14/14 (phrases per page; split before clean; no "trace", "citation", "provenance", "metadata", "score", "offset", "reproduc" anywhere in Ch1), App p.4–7/23, Ch22 p.8, 13, 14/19, Intro p.7/8. A mutated copy of the script (3 wrong needles) fails exactly those 3 checks.

## 2. UNVERIFIED (not run)
Any Groq answer or Cohere vector for v0; Cohere scores, ranks and truncation at 1,000 characters; the one-command run from a fresh clone; Corpus T (not chosen or frozen, DEC-3); whether the learner's own chunker reproduces the 97 ids; `local_rag_huggingface_faiss.ipynb` behaviour (never executed at this commit) and its cell-30 call (signature mismatch found by reading only).
