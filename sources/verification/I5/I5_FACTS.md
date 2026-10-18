# I5_FACTS — what the I5 lesson can rely on (run-verified)

Run date: **2026-10-18**. Every number in the I5 HTML lesson (`study/lessons/I5_contextual_headers.html`), the reading file, the question file, the verify notebook and the apply-it tool is listed here with the script section that produced it. Numbers that these runs did not produce are marked CITED, DERIVED, TOY or UNVERIFIED.

## 0. Environment, provenance, how to re-run

- **Where it ran.** A Claude Code cloud session (Linux, CPython 3.12.3, the project `uv` environment from `uv.lock`), not Yash's Windows machine. Versions printed in K1: pymupdf 1.26.7 · numpy 2.5.3 · rank-bm25 0.2.2.
- **Corpus D.** `Understanding_Climate_Change.pdf` downloaded from the pinned upstream (`NirDiamant/RAG_Techniques` @ `009adba`, `data/`). sha256 `1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669`, the same file as C3, P3 and P4. Snapshot `ea07572562ac`, 33 pages, 72,593 characters.
- **Chunks.** v0's 97 chunks: the 07 H.3 recursive chunker, per page, 1000/200, loaded exactly as P4's kit script does (`contracts_check.load_07_modules`). `params_hash 1ca9c5a3b548`; `chunks.jsonl` sha256 starts `d4108b8936093394`. The span invariant `DOC[char_start:char_end] == text` holds for all 97.
- **Upstream notebook.** `all_rag_techniques/contextual_chunk_headers.ipynb` @ `009adba` (17 cells; file sha256 starts `11b78dc9cc583026`).
- **Seeds.** The 06 §6.7 draft seeds (LLM-drafted, not human-verified). Every rank is an observation on draft seeds, never an evaluation result.
- **No API call.** No Groq, Cohere or Claude call; `.env` is never read.
- **Blocked hosts (this session).** `huggingface.co` and `openaipublic.blob.core.windows.net` were refused by the session's network policy. So **MiniLM was not loaded and no tokenizer was run here.**
  - K16 (MiniLM margins and retrieval per arm) printed `SKIPPED`. It runs unchanged on a machine with the model in the Hugging Face cache, and so does the verify notebook.
  - Every token count in K3, K6 and K11 is **DERIVED** from measured characters-per-token ratios on this corpus: WordPiece **6.21** (C2_FACTS K2) and `o200k_harmony` **5.65** with **12,840** document tokens (P1_FACTS K5). The chunk maximum of **182** WordPiece tokens (with `[CLS]`/`[SEP]`) is CITED from C2_FACTS K2.
- **Scripts and outputs** (this folder):

  | File | What it is |
  |---|---|
  | `i5_kit_measure.py` | Sections K1–K16 |
  | `out_i5_kit_measure.txt` / `out_i5_kit_measure.stderr.txt` | Its stdout / stderr (stderr empty) |

- **Re-run** (from `rag_learning/`, Git Bash):
  ```bash
  B="C:/Yash/New-Work/Book RAG"
  PYTHONIOENCODING=utf-8 uv run python sources/verification/I5/i5_kit_measure.py \
      "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
      "$B/upstream/RAG_Techniques/all_rag_techniques/contextual_chunk_headers.ipynb" \
      > sources/verification/I5/out_i5_kit_measure.txt
  ```
  On Yash's machine K16 will run, so the output gains K16's lines; K1–K15 must stay byte-identical except the Python version in K1.
- **Determinism.** Two consecutive runs gave **byte-identical** stdout (`cmp`).

## 1. Facts by section (`K` = `i5_kit_measure.py`, section in `out_i5_kit_measure.txt`)

### K2 The heading tree (PyMuPDF `get_text("dict")`, font size + bold flag `flags & 16`)

| Fact | Value |
|---|---|
| PDF metadata title | `''` (empty): the title must come from the 24 pt line |
| Line classes (size, bold) | 12 regular **814** · 12 bold **192** · 13.56 bold **68** · 18 bold **22** · 24 bold **1** |
| Headings by level | title **1** · chapter **21** (Chapter 5's title wraps over 2 lines and is merged) · section **68** · subsection **192** · total **282** |
| Title | `Understanding Climate Change`, 28 characters |
| Headings (levels 1–3) per page | min / median / max **1 / 9 / 11**; every one of the 33 pages has one |
| Density | one heading every **257** characters on average |
| Subsections in body size | **192 / 281 = 0.68** of the non-title headings are 12 pt bold, the body size. A detector that needs "size larger than body" misses them |

### K3 Reused names and the Paris paths

| Fact | Value |
|---|---|
| Section/subsection names reused under different chapters | **11**: Marine Ecosystems (p.5 Ch3; p.13 Ch9) · International Agreements (p.6 Ch4; p.23 Ch16) · Research and Innovation (p.7 Ch4; p.16 Ch10) · Smart Grids (p.8 Ch5; p.22 Ch15) · Carbon Capture and Utilization (p.8 Ch5; p.23 Ch15) · Carbon Utilization (p.8 Ch5; p.23 Ch15) · International Collaboration (p.10 Ch6; p.16 Ch10) · Paris Agreement (p.10 Ch6; p.23 Ch16) · Policy and Governance (p.12 Ch8; p.18 Ch12) · Youth Engagement (p.13 Ch8; p.32 Ch21) · Nature-Based Solutions (p.14 Ch9; p.26 Ch17) |
| Paris Agreement, p.10 | `Understanding Climate Change › Chapter 6: Global and Local Climate Action › International Collaboration › Paris Agreement` |
| Paris Agreement, p.23 | `Understanding Climate Change › Chapter 16: Global Cooperation and Governance › International Agreements › Paris Agreement` |
| Path header length (title › chapter › section › subsection), 260 section/subsection headings | **75 / 120 / 168** characters (min / median / max) ≈ **12 / 19 / 27** WordPiece tokens (DERIVED, 6.21) |

The research (§5) counted 11 with poppler and gave 6 examples; K3 confirms the count on PyMuPDF and lists all 11, with the same two Paris paths.

### K4 Which heading a chunk gets

| Fact | Value |
|---|---|
| Chunks with **no** heading line inside | **0 of 97** (the research's scratch split gave 18 of 120; that split was not v0's) |
| Chunks containing ≥ 2 headings | **94 of 97** |
| Chunks whose first non-space character starts a heading | 21 of 97 |
| Chunks whose last non-empty text is a heading (orphaned heading; its body is in the next chunk) | **31 of 97**, of which **16** at a page end. 16 matches 07 D.8 exactly |
| Start-rule path ≠ majority-rule path | **84 of 97** |
| D-002 gold chunk **27** (p.10, [20555, 21506)) | starts on the Chapter 6 heading, so the **start rule** gives just `Chapter 6: Global and Local Climate Action`. **Majority:** `Chapter 6 › International Collaboration › Paris Agreement`. Headings inside: Chapter 6, International Collaboration, United Nations Framework Convention on Climate Change (UNFCCC), Paris Agreement, National Strategies, Carbon Pricing |
| D-003 gold chunk **68** (p.23, [50756, 51413)) | **start rule:** `Chapter 15: Climate Change and Technology › Carbon Capture and Utilization › Direct Air Capture (DAC)`, the **wrong chapter** for its Paris text. **Majority:** `Chapter 16: Global Cooperation and Governance › International Agreements › Paris Agreement` |
| Chunk **34** (p.12, [25535, 26463)), the counter-case | starts mid-paragraph with "It can be used for tracking carbon credits" ("it" = blockchain). **Start rule:** `Chapter 8 › Emerging Technologies › Blockchain for Climate Action`, which names the referent. **Majority:** `Chapter 8 › Policy and Governance › Integrated Climate Policies`, which does not. Headings inside: Bioengineering, Policy and Governance, Integrated Climate Policies, International Cooperation. Neither rule is right for every chunk |
| Header length by rule (characters, min / median / max; distinct headers) | start 28 / 120 / 168, 97 distinct · majority 67 / 123 / 168, 96 distinct · all-inside 93 / 198 / 306, 97 distinct |
| Header + chunk over 256 WordPiece tokens | 0 under all three rules (DERIVED estimate) |

### K5 Header arms (start rule unless named)

| Arm | Distinct headers / 97 | Largest group sharing one header | Header characters min / median / max |
|---|---|---|---|
| none | 1 | 97 (1.00) | 0 / 0 / 0 |
| title only | **1** | **97 (1.00)** | 28 / 28 / 28 |
| path (start rule) | 97 | 1 (0.01) | 28 / 120 / 168 |
| path (majority rule) | 96 | 2 (0.02) | 67 / 123 / 168 |

The separator between header and chunk text is `"\n\n"`. Example (start rule, chunk 34): `Understanding Climate Change › Chapter 8: Future Directions and Innovations › Emerging Technologies › Blockchain for Climate Action` + `\n\n` + `It can be used for tracking carbon credits, …` (chunk 34 starts mid-paragraph with "It").

### K6 Dilution and truncation (DERIVED from 6.21 characters per WordPiece token)

| Fact | Value |
|---|---|
| Path-arm header share by characters, over 97 chunks | min / median / max **0.029 / 0.119 / 0.201** |
| s = h/(h+c), 120-character header (~19 tokens) | 1,000-character chunk (~161): **0.106** · 935 (~151, the median): **0.112** · 400 (~64): **0.229** |
| Truncation, MiniLM `max_seq_length` 256 with the specials inside (C2 K9) | 182 + 27 = 209: fits · 182 + 100 = **282: over by 26, the chunk's tail is cut** |
| Path-arm `embed_text` over 256 | 0 of 97 (estimate max 188) |
| A 100-token LLM context + chunk over 256 | about **29 of 97** (DERIVED) |

### K7 Near-duplicate pages (start-rule paths)

| Chunk | Page | Mentions "Paris" | Start-rule path (without the title) |
|---|---|---|---|
| 17 | 6 | yes | Ch4 › Reforestation and Afforestation › Afforestation Initiatives |
| **27** (D-002 gold, D-007 group 1) | 10 | yes | Chapter 6: Global and Local Climate Action |
| **68** (D-003 gold, D-004 alt.) | 23 | yes | Ch15 › Carbon Capture and Utilization › Direct Air Capture (DAC) |
| 70 | 24 | yes | Ch16 › Regional and National Initiatives › European Green Deal |

Relevant chunks (any_overlap) per answerable seed: D-001 [7] · D-002 [27] · D-003 [68] · D-004 [23, 67, 68] · D-005 [3, 4] · D-006 [21] · D-007 [27, 85] · D-008 [69].

### K8 Header-query leakage on the draft seeds

No seed has a question word that appears in its gold chunk's header but not in the chunk text. Shared words that are in both: D-005 `coal`, D-006 `solar`. The seeds were written from spans, so on these 8 items the header adds no leaked word.

### K9 "Anonymous" chunks

| Fact | Value |
|---|---|
| No heading inside **and** first word a pronoun or determiner | **0 of 97** (no chunk lacks a heading) |
| Chunks that start mid-sentence (first character lower-case) | **46 of 97** (the 200-character overlap cuts) |

Corpus D is **heading-dense**: every chunk carries at least one heading line already. Expect a small effect on D; T (papers) is where I5 can matter.

### K10 BM25 preview (the v2.0 `bm25_text` field; not what v1.2 changes)

Course tokenizer `[a-z0-9]+(?:[.,][0-9]+)*`, `BM25Okapi` (k1 1.5, b 0.75), ties by the lower chunk seq.

| Arm | First relevant rank, D-001…D-008 | Hit@4 | CE@4 | MRR@10 |
|---|---|---|---|---|
| none | 1, 1, 1, 1, 1, 2, 1, 1 | 8/8 | 8/8 | 0.938 |
| title | same | 8/8 | 8/8 | 0.938 |
| path (start) | same | 8/8 | 8/8 | 0.938 |
| path (majority) | same | 8/8 | 8/8 | 0.938 |

In the title arm, `understanding`, `climate` and `change` appear in **all 97** units, so their raw idf is negative and rank_bm25 lifts each to the floor 0.25 × average_idf = **0.8565**. They still add score, but nearly the same to every chunk. BM25 is at ceiling on these span-written seeds, so they cannot show a header effect either way.

### K11 Cost ladder (DERIVED arithmetic; prices from `study/tools/examples/prices_2026-10-17.json`)

Assumptions (research §5): 250 tokens of chunk + instruction per call, 200 output tokens including reasoning. Document tokens: 12,840 (`o200k_harmony`, the Groq model's encoding, P1 K5). Claude's own tokenizer gives a different count (UNVERIFIED; used here as a proxy).

| Rung | Calls (D) | Input tokens per call | D cost |
|---|---|---|---|
| 0 path header | 0 | — | $0 |
| 1 title / summary per document | 1–2 | ≤ 4K–8K | not needed on D (the title is the 24 pt line) |
| 2 chapter window, Groq `gpt-oss-20b` | 97 | median **855**, max 1,322 (chapters 1,591 / 3,336 / 6,058 characters) | **$0.0124**; 106,743 tokens in all, fits the 200K TPD; ≥ **13.3 minutes** at 8K TPM |
| 3 whole document, Groq free tier | 97 | **13,090** | **blocked**: 13,090 > 8,000 TPM per request; 97 calls = 1,269,730 input tokens vs 200K TPD |
| 3 whole document, Haiku 5.5 uncached | 97 | 13,090 | **$0.1367** |
| 3 whole document, Haiku 5.5 cached (write 1.25× once, read 0.1×) | 97 | 13,090 | **$0.0261** (5.2× cheaper) |
| 3 whole document, paid Groq tier, 50% cached input | 97 | 13,090 | $0.0542 |

Formula: `cost_d = D·p_in·w + (n−1)·D·p_in·ρ + n·(c+P)·p_in + n·o·p_out`; Claude w = 1.25, ρ = 0.1; Groq w = 1, ρ = 0.5.

### K12 Cache keys after a one-line edit on page 12

The edit appends " (revised)" to the first line of page 12. It changes the text of **1** chunk (33; page 12 holds chunks 33, 34, 35).
- A key over the chunk text only: **96 of 97** contexts are served from cache, although every prompt contained the old document.
- A key over prompt version + document text + chunk text: **0 of 97** served; all are rebuilt.
- `doc_text_sha256` changes from `5106772efa77…` to `1377caa13861…`.

### K13 Toy: mean pooling with a shared header (TOY)

d = 64, seed 0. Each token is `unit(topic + 1.7·noise/√d)`, so the mean cos(token, topic) is 0.4965. Chunks A and B have 150 tokens each; the header has its own topic.

| Header tokens h | s = h/(h+150) | cos(A + header, A bare) | cos(A, B), same header | cos(A + header, header topic) |
|---|---|---|---|---|
| 0 | 0.000 | 1.0000 | −0.1651 | −0.1261 |
| 19 | 0.112 | 0.9897 | −0.1857 | 0.0078 |
| 27 | 0.153 | 0.9810 | −0.1734 | 0.0608 |
| 50 | 0.250 | 0.9423 | −0.1265 | 0.2047 |
| 100 | 0.400 | 0.8014 | +0.0964 | 0.4850 |

What it shows: a small share barely moves a chunk vector. A large shared header pulls unrelated chunks toward each other and toward the header's topic (the "header magnet"). Magnitudes are toy, not MiniLM.

### K14 Upstream `contextual_chunk_headers.ipynb` @ `009adba` (cells 0-based)

| Fact | Value |
|---|---|
| Cells | 17; code execution counts `[None, 3, None, 4, 5, 13]` |
| Cell 8 | downloads the climate PDF **and** a Nike text file |
| Cell 9 | `chunk_size=800`, `chunk_overlap=0`, on the Nike text |
| Cell 11 | `MAX_CONTENT_TOKENS = 4000`, `gpt-3.5-turbo` encoder, `gpt-4o-mini`, `temperature=0.2`; saved output `NIKE, INC. ANNUAL REPORT ON FORM 10-K` |
| Cell 13 | Cohere `rerank-english-v3.0` via `cohere.Client`; query `Nike climate change impact`; saved output **0.10576342 → 0.92206234** ("Similarity w/o …" label) |

### K15 Vendor numbers as absolute and relative change (formula)

| Change in 1 − recall@20 (Anthropic) | Absolute | Relative |
|---|---|---|
| 5.7% → 3.7% (contextual embeddings) | **−2.0 points** | **−35.1%** |
| 5.7% → 2.9% (+ contextual BM25) | −2.8 points | −49.1% |
| 5.7% → 1.9% (+ rerank) | −3.8 points | −66.7% |

06 §9.4 at n = 50 paired with b + c = 10: SE 0.063, 95% half-width ±0.124, an effect of about **0.18** is needed for 80% power.

### K16 MiniLM per arm

**SKIPPED in this session** (model not cacheable: `huggingface.co` blocked). The verify notebook computes the same table on Yash's machine: tokens per arm, Hit@4 / CE@4 / MRR@10 per arm, the D-002 and D-003 gold-vs-distractor margins, Kendall τ none vs title. The lesson shows these as "your run" placeholders, not as numbers.

## 2. CITED, DERIVED and UNVERIFIED

| Item | Status |
|---|---|
| Anthropic contextual retrieval: 5.7 → 3.7 → 2.9 → 1.9 (1 − recall@20), $1.02 per million document tokens, 50–100-token contexts | CITED, research [I5-S1] (opened in the research session) |
| Cookbook Pass@10 87.15 → 92.34 → 95.26; 61.83% cached; silent no-cache at 3,412 tokens on Haiku 4.5 | CITED, research [I5-S2] @ `a162e01` |
| dsRAG KITE 4.72 → 6.04 (CCH), FinanceBench 96.6% vs 32% (current README) | CITED, research [I5-S3] @ `5215e97`; vendor-reported |
| Late chunking NFCorpus 23.46 → 29.98 | CITED, research [I5-S4] |
| Claude prompt caching: 512-token minimum on Haiku 5.5, 4,096 on Haiku 4.5; write 1.25× (5 min) or 2× (1 h); read 0.1× | CITED, `claude-api` skill via research [I5-S7]; the skill says to check the docs before relying on the minimum |
| Groq caching: automatic, 50% off, cached tokens not counted toward rate limits | UNVERIFIED (search-checked, research [I5-S6]) |
| Groq free tier 8K TPM / 200K TPD | UNVERIFIED (plan row, LLMOPS §2.5) |
| LlamaIndex `TextNode` embeds all metadata by default; `DocumentContextExtractor` defaults | CITED, research [I5-S8] (source read, v0.14.25) |
| Book Ch7 pages (p.1–2, p.4, p.7, p.8, p.8–9/11) | UNVERIFIED in this session (book not present); taken from 02/04 as the research did. I5-E7 (step/page order) stays open |
| WordPiece / o200k token counts in K3, K6, K11 | DERIVED from the measured ratios named in §0 |
| MiniLM margins and retrieval per arm | not measured (K16 skipped) |

## 3. Notes for 02, 04, 06 (not edited; recorded here)

- **06 v1.2 "path at chunk start" is not stated, but the research's primary arm used it.** On v0's chunks the start rule labels D-003's gold chunk with the wrong chapter (K4). The lesson teaches the majority rule as the default and keeps the start rule as a named arm.
- **07 D.8's 16 orphaned headings** are page-end orphans. Counting every chunk end gives 31 (K4).
- **Research §5's "18 of 120 chunks with no heading"** came from a scratch split; on v0's 97 chunks it is 0 (K4).
- The research's errors I5-E1 … I5-E11 stand as reported; K14 re-confirms I5-E9/E10's upstream facts.
