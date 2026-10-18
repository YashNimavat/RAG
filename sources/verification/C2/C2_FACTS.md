# C2_FACTS: what the C2 HTML lesson and its kit files can rely on

Run date: **2026-10-18**. This file lists every number the C2 study-kit files (lesson, verify notebook, apply-it tool, questions, reading file) may print, with the run that produced it. The lab's own facts stay in [`../C2lab/C2LAB_FACTS.md`](../C2lab/C2LAB_FACTS.md) (2026-10-08); this file adds K1–K14 on top and does not repeat the lab's CHECK fingerprints. Numbers not produced by a run are marked CITED, FORMULA or UNVERIFIED.

## 0. Environment, provenance, how to re-run

- **Interpreter.** CPython 3.12.8 (Windows 11), the project uv environment. Versions (K1): pymupdf 1.26.7 · tiktoken 0.14.0 · tokenizers 0.23.2 · sentence-transformers 6.1.0 · transformers 5.19.0 · torch 2.14.1 (CPU) · numpy 2.5.3. **LangChain is not installed.**
- **Corpus D.** `upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf`, PyMuPDF `page.get_text()`, pages joined with `"\n"`, no cleaning; 33 pages, 72,593 characters, `snapshot_id` `ea07572562ac` (the lab's setup cell, fail-closed).
- **The chunker is never re-typed.** `c2_kit_measure.py` executes the lab's given setup cell and reference solution (`C2lab/c2_setup.py`, `c2_solution_ref.py`) through `C2lab/c2_common.run_reference`, so every chunk here is the lab's chunk.
- **Tokenizers.** MiniLM WordPiece from the cached `tokenizer.json` of `sentence-transformers/all-MiniLM-L6-v2` at revision `1110a243…` (truncation switched off for counting; `[CLS]`/`[SEP]` included unless a row says otherwise); tiktoken `cl100k_base` and `gpt2` from tiktoken's cache. `HF_HUB_OFFLINE=1`.
- **No API calls.** No Groq, Cohere, Claude or LangSmith call; `.env` is never read.
- **Scripts and outputs** (this folder):

  | File | What it is |
  |---|---|
  | `c2_kit_measure.py` → `out_c2_kit_measure.txt` | K1–K14 below (about 35 s; stderr empty) |
  | `c2_sources.py` → `out_c2_sources.txt` | Every repo cell, repo line and book page the lesson cites (PASS/FAIL only; no book text saved). **ALL PASS** |

- **Re-run** (from `rag_learning/`, Git Bash):
  ```bash
  B="C:/Yash/New-Work/Book RAG"; V=sources/verification/C2; export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
  uv run python $V/c2_kit_measure.py > $V/out_c2_kit_measure.txt 2> $V/out_c2_kit_measure.stderr.txt
  uv run python $V/c2_sources.py "$B/upstream/RAG_Techniques" "$B/RAG_Made_Simple_The_Complete_Visual_Guide" > $V/out_c2_sources.txt
  ```
- **Determinism.** Two consecutive runs of `c2_kit_measure.py` gave **byte-identical** stdout (`cmp`).

## 1. Facts K1–K14 (`K` = section in `out_c2_kit_measure.txt`)

| Id | Fact | Value |
|---|---|---|
| K1 | Objects | 33 pages, 72,593 characters, snapshot `ea07572562ac`. `PARAMS` = the 06 §2.4 block `{"name": "recursive_char", "unit": "chars", "chunk_size": 1000, "chunk_overlap": 200, "separators": ["\n\n", "\n", " ", ""], "scope": "per_page"}`. `params_hash` **`1ca9c5a3b548`**; **97** records; `chunks.jsonl` sha256 `d4108b8936093394c6eb50d4c22e8d4013d9a048fb38d5769281af4aadb3011b` (= C2LAB_FACTS). MiniLM's `tokenizer.json` stores truncation at **128**; a second MiniLM snapshot `c9745ed1…` is also in the cache (pass `revision=`) |
| K2 | Units | Whole corpus: WordPiece (no specials) 11,694 tokens = **6.21** chars/token; cl100k 13,026 = **5.57**; gpt2 14,375 = **5.05**. 97 v0 chunks, min / median / max: characters **393 / 935 / 1000**; WordPiece incl. specials **59 / 149 / 182**; cl100k **68 / 165 / 193**; gpt2 77 / 183 / 213. Means: 857.9 chars, 140.1 WordPiece, 153.9 cl100k. Ruler example **seq 75** (page 26, one of the 2 chunks of exactly 1,000 characters, starts "Adaptation Planning"): **1,000 characters = 151 WordPiece (incl. specials) = 169 cl100k = 186 gpt2**. "1,000 tokens" as text on this corpus: cl100k **5,573** characters, WordPiece 6,208, gpt2 5,050. A v0 chunk is about **6.7×** smaller than "1,000 tokens" would suggest (1000 / median 149) |
| K3 | Fixed windows | `fixed_window_chunks(T, 10, 3)` → (0,10,'abcdefghij') (7,17,'hijklmnopq') (14,23,'opqrstuvw'); `(T, 8, 4)` → (0,8)(4,12)(8,16)(12,20)(16,23); `(T, 10, 0)` → (0,10)(10,20)(20,23). Count formula vs code over L = S+1 … 20S−1 at (10,3) (8,4) (300,60) (1000,200): **0 mismatches**. `doc_text` fixed 1000/200: **91** windows (= ⌈72,393/800⌉); stored characters / L = **1.2480** (limit 1.25). Windows on `doc_text` at 1000/0, /200, /400, /500: 73, 91, 121, 145; limits 1.000, 1.250, 1.667, 2.000. Fixed 1000/200 windows end inside a word at **67 of 90** inner boundaries; the recursive splitter at **0 of 91** |
| K4 | Containment | S = 1000, F = 500: formula / brute force (L = 20,000): O = 0 **0.5010** / 0.5138 · O = 200 **0.6262** / 0.6320 · O = 400 **0.8350** / 0.8375. At O = 200: F = 100, 200, 201 → 1.0; F = 202 → 0.99875; 250 → 0.93875; 500 → 0.62625; 800 → 0.25125; 1000 → 0.00125. PARA (785 chars) FACT F = 71: P at 300/60 = **0.9583**; fixed 300/0 contains it in no chunk, 300/60 in chunk **2**; fixed 300/60 spans (0,300)(240,540)(480,780)(720,785) |
| K5 | Recursive splitter, ours vs a **LangChain-style port** | Ours: W pieces (0,4)(4,8)(8,12)(12,15)(15,19)(19,22); `recursive_chunks(W,10,4)` → (0,8,'the cat ') (4,12,'cat sat ') (8,15,'sat on ') (12,22,'on the mat'); PARA 300/60 → [0,294) [238,534) [478,773) [714,785). The port (`lc_split` in the script: `_split_text` + `_merge_splits` read at source level, keep the separator at the start, strip whitespace) **matches all four of 07's verified LangChain runs**: W 10/4 → 'the cat','cat sat','sat on','on the','the mat' (5 chunks); the 25-x word at 10/0 → 'short','xxxxxxxxx','xxxxxxxxxx','xxxxxx','tail' (and with `strip_whitespace=False`); PARA 300/60 → [0,293) [238,533) [478,772) [714,785). On PyMuPDF pages, per page 1000/200, the port gives **97 chunks, lengths 391 / 933 / 999** and real overlaps first four **180, 140, 197, 177**, all equal to 07's PyPDFLoader + LangChain numbers; 64 same-page pairs, min / median / max 107 / 175.5 / 198. Separators `[" "]` only (no `""`): a 25-character word stays one 25-character chunk at `chunk_size=10`. Overlap = size (40/40) is accepted: 60 words → 56 chunks (07 J2a) |
| K6 | Scope (ours, 1000/200) | Per page **97** chunks (3 on each of pages 1–32, 1 on page 33), lengths 393 / 935 / 1000, none touches two pages. Cross page (whole `doc_text`) **92** chunks, lengths 755 / 962.5 / 999; **41** start and end on different pages (the lab's count); **39** hold non-space text from both pages (= 07's PyPDFLoader count of 39). Page lengths 636 / 2,225 / 2,494 characters |
| K7 | Real overlap (ours, per page 1000/200) | 64 same-page pairs: min / median / max **109 / 177 / 200**; exactly 200: 2; first four **182, 142, 199, 179** (= C2LAB_FACTS Task 8). Histogram 100–119, 120–139, 140–159, 160–179, 180–199, 200: **4, 9, 10, 13, 26, 2**. 32 neighbouring pairs straddle a page end and share nothing. No pair has 0 overlap |
| K8 | Lengths and the cap, per page, four sizes | 500/100: **201** chunks, chars 94 / 449 / 500, WordPiece 17 / 74 / 99, over 256 **0**, tail chunks < 25% of size 2. 1000/200: **97**, 393 / 935 / 1000, 59 / 149 / 182, over 256 **0**, tail 0. 1500/300: **65**, 636 / 1303 / 1500, 109 / 215 / 270, over 256 **4**, cl100k over 256 **21**, 184 characters past the cap. 2000/400: **65**, 393 / 953 / 2000, 59 / 160 / 365, over 256 **32**, cl100k over 256 32, tail **6**, **12,333** characters past the cap (of 83,880 stored). Over 512 (bge-small's cap): 0 at every size. WordPiece histograms (bins of 25 tokens from 0): 1000/200 [0, 0, 1, 9, 16, 23, 45, 3]; 1500/300 [0, 0, 0, 0, 2, 4, 14, 9, 9, 19, 8]; 2000/400 [0, 0, 3, 11, 12, 6, 1, 0, 0, 0, 0, 7, 15, 6, 4]; 500/100 [3, 12, 92, 94]. v0: p95 (nearest rank) 174; **70 of 97** over 128 (MiniLM's training length). Embedding tokens for the corpus (sum over the 97 chunks): WordPiece **13,586**, cl100k 14,931 |
| K9 | Runtime truncation (sentence-transformers, MiniLM rev `1110a243`) | `max_seq_length` 256 = `tokenizer.model_max_length` 256. A 2,600-character text = 479 WordPiece tokens; `model.tokenize` returns **256** ids, first 101 ([CLS]) and last 102 ([SEP]): **the specials count inside the 256**. Its first 1,423 characters (exactly 256 tokens): cos(full, prefix) = **1.000000**; appending more text after the cap: cos **1.000000**. (Closes 07 D.6's UNVERIFIED item) |
| K10 | Page breaks (PyMuPDF text) and the PPP sentence | 32 page breaks; **24** pages do not end in terminal punctuation; **8** are mid-sentence cuts (next page starts lowercase) at 12→13, 14→15, 15→16, 16→17, 21→22, 22→23, 24→25, 28→29; the other **16** end in a heading (page 1 ends "Coal", page 2 "Livestock Emissions", page 3 "Polar Ice Melt", page 4 "Coral Reefs"…). **= 07 D.8's 24 / 8 / 16 on PyPDFLoader.** The PPP sentence: span **[26866, 26997)**, F = **131** characters, pages 12→13 (break at offset 26966). Per-page chunks containing it whole: **none** at overlap 0, 200, 400 or 600; it is split between seqs **35 and 36**. The cross-page chunker contains it whole in chunk **34**. Each of the 8 cut sentences (97–147 characters) is whole in some cross-page chunk. The string "Public-private partnerships" occurs **0** times in `doc_text`; with the PDF's line break ("Public-\nprivate") once. Lines repeated on ≥ 3 pages: **0**. Tabs: **0** |
| K11 | Offsets and identity | Round trip `doc_text[a:b] == text` 97/97; `page_segments` round trip 97/97. Ids `climate:ea07572562ac:1ca9c5a3b548:00000` … `:00096`. Overlap **199**: `params_hash` **`94f90fbfb5d5`**, 97 chunks, **0** ids shared with v0, while **94** of 97 spans are the same. Changing one field: unit → `91848adfb6c0`, scope → `5f815e69a7e0`, separators without `""` → `83249e317e08`, chunk_size 1001 → `12a950fc2efb`. Without `sort_keys`, reversed key order → `99af0d35e01b`. Two builds identical. Characters covered by some chunk: 72,561 of 72,593 (the 32 joining newlines are outside every per-page chunk) |
| K12 | `start_index` found by search (LangChain `create_documents`: `text.find(chunk, previous_start + previous_length − chunk_overlap)`) | (a) characters, our chunks per page 1000/200: **97 of 97** right. (b) token windows (`TokenTextSplitter`-style: gpt2, 200/50, each window decoded): 99 windows; **65 right, 34 = −1**, 0 wrong. (c) character splitter measured in gpt2 tokens (`from_tiktoken_encoder`-style, the port), 200/50: 99 chunks; **65 right, 34 = −1**, 0 wrong. The −1 values come from subtracting 50 *tokens* from a *character* position. (d) Toy repeat "Intro. The footer line. Body text here. The footer line. End.": `find` returns 7 for both copies unless the start is past 7 (second copy at 40) |
| K13 | Toy dilution (TOY, 2-D) | q = [1, 0]; chunk = mean of 1 answer row and n off-topic rows [0, 1]; cos = 1/√(1 + n²): n = 0 **1.000**, 1 **0.707**, 2 **0.447**, 3 **0.316**, 4 **0.243**; beats a competitor at 0.600 only for n ≤ 1 (= 07 D.7) |
| K14 | FORMULA arithmetic | Stride, guarantee and storage limit: 1000/200 → 800, F ≤ 201, 1.250; 1000/400 → 600, F ≤ 401, 1.667; 500/100 → 400, 101, 1.250; 300/60 → 240, 61, 1.250; 10/3 → 7, 4, 1.429. The PPP sentence (F = 131 ≤ 201) **would be guaranteed** whole by 200 overlap in one continuous text; per page it is never whole. 1000/400 on `doc_text`: ⌈72,193/600⌉ = 121 |

## 2. CITED, FORMULA and UNVERIFIED

| Item | Status |
|---|---|
| LangChain `RecursiveCharacterTextSplitter` defaults (`chunk_size=4000`, `chunk_overlap=200`, `length_function=len`, `keep_separator=True`, `strip_whitespace=True`, `add_start_index=False`), validation rules, strict `<` in `_split_text`, `keep_separator="end"`, `add_start_index` by `text.find` | CITED: research C2 §5.1 [C2-1], source code read 2026-10-17 (langchain-text-splitters 1.1.3). Not run: the library is not installed. The K5 port reproduces 07's verified runs, which supports (does not prove) the reading |
| Issue #29884 ("TokenTextSplitter start indices are sometimes −1") open; PR #31222 closed unmerged | CITED: [C2-1], read 2026-10-17 |
| LlamaIndex `SentenceSplitter`: 1,024 / 200 cl100k tokens; metadata length subtracted from `chunk_size` | CITED: [C2-2], source read; not installed |
| Cohere `embed-v4.0` context 128k tokens; `embed-english-v3.0` 512; at most 96 texts per call; `truncate` NONE / START / END, default END | CITED: [C2-3], Cohere docs read 2026-10-17. The Models API reported 8,192 for `embed-v4.0` in the O2 smoke test (P4_FACTS §2): **the limit is disputed (8,192 vs 128k)**. Either way a 1,000-character chunk (about 150–200 tokens) is far below it. Cohere's own tokenizer for v4: **UNVERIFIED** |
| bge-small-en-v1.5: 512 tokens, same uncased BERT vocabulary as MiniLM | CITED: 07 D.6 (model card). Not cached here, so its counts reuse MiniLM's WordPiece counts (same vocabulary) |
| MiniLM trained on sequences of at most 128 tokens | CITED: model card (07 D.6) |
| Studies of size and overlap: Chroma 2024, NVIDIA 2025, Bhat et al. 2025, Bennani & Moslonka 2026 | CITED: research C2 §5.2 [C2-4], [C2-6], [C2-7], [C2-8] (external, read 2026-10-17); numbers quoted only as listed there |
| Book claims (Ch1 p.4, 5, 7, 10–13/14; App p.14, 16/23; Ch4 p.2/15; Ch7 p.2/11; Ch8 p.1–2/11; Ch9 p.2/14) | Opened by `c2_sources.py` (ALL PASS); paraphrased only |
| P(contained) formula, count formula, storage limit | FORMULA (07 D.2–D.3), checked by K3/K4 brute force |
| Whether chunk 36 or 35 ranks for a PPP question with any model | **UNVERIFIED** (no retrieval run in C2; that is C4/M2) |

## 3. Differences from 07 (07 used PyPDFLoader text, 72,523 characters)

| 07 says | On PyMuPDF (v0) | Where |
|---|---|---|
| Lengths 391 / 933 / 999 per page | Ours 393 / 935 / 1000; the LangChain-style port 391 / 933 / 999 | K5, K6 |
| 39 cross-page chunks span a break | 41 by the lab's definition, 39 with text on both pages | K6 |
| Real overlaps 180, 140, 197, 177 | Ours 182, 142, 199, 179 (no stripping); port 180, 140, 197, 177 | K5, K7 |
| cl100k flags **18** chunks over 256 at 1500/300 | **21** (WordPiece still 4) | K8 |
| gpt2 5.07 chars/token; cl100k 13,016 tokens | 5.05; 13,026 | K2 |
| "PyMuPDF chunk counts UNVERIFIED" (D.8) | 97 / 65 / 65 / 201 confirmed; 24 / 8 / 16 page breaks confirmed | K8, K10 |
| `[CLS]`/`[SEP]` inside 256 UNVERIFIED (D.6) | Yes: 256 ids including both | K9 |
| D.4: "no piece ever exceeds chunk_size" | Only while `""` is in the separators (K5 custom-separator row) | K5 |
