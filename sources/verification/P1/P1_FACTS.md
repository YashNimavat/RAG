# P1_FACTS — what the P1 lesson can rely on (run-verified)

Run date: **2026-10-08** (S11 and S-web added **2026-10-09**). Every number in [`concepts/P1_llm_fundamentals.md`](../../../concepts/P1_llm_fundamentals.md) is listed here with the command and output section that produced it. Numbers that were not produced by these runs are marked CITED (from an earlier logged run), DERIVED (arithmetic shown in the lesson) or UNVERIFIED.

## 0. Environment, provenance, how to re-run

- **Interpreter.** CPython 3.12.8 (Windows 11), the project uv environment (`rag_learning/.venv`).
- **Versions** (printed in S1): pymupdf 1.26.7 · tiktoken 0.14.0 · transformers 5.19.0 · sentence-transformers 6.1.0 · torch 2.14.1 (CPU) · numpy 2.5.3 · tokenizers 0.23.2.
- **Corpus.** `C:\Yash\New-Work\Book RAG\upstream\RAG_Techniques\data\Understanding_Climate_Change.pdf`, SHA-256 `1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669` (repo pinned at `009adba`).
- **Extraction.** Identical to the acceptance suite (`corrections/contracts_check.py` L764–L766): `page.get_text()` per page, pages joined with `"\n"`.
- **Models and encodings.** `sentence-transformers/all-MiniLM-L6-v2` from the local HF cache, offline (`HF_HUB_OFFLINE=1` set in the script), snapshot `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. tiktoken `cl100k_base`, `o200k_base`, `o200k_harmony`, `gpt2` (tiktoken may download an encoding file once).
- **No API calls.** No Groq or Cohere call; `.env` is never read.
- **Scripts** (this folder):

  | Script | What it produces | Saved output |
  |---|---|---|
  | `p1_measure.py` | Sections S1–S10: extraction, token counts, ratios, pieces, truncation, toy temperature, the repo heuristic, prompt budget, cost arithmetic | `out_p1_measure.txt` (stdout), `out_p1_measure.stderr.txt` (stderr) |
  | `p1_sources.py` | S-src: checks every cited repo cell (0-based) and book page against the files | `out_p1_sources.txt` |
  | `p1_strawberry.py` (2026-10-09) | S11: `o200k_harmony` count and pieces for "strawberry" in four contexts; tokenizer only | `out_p1_strawberry.txt` |
  | `p1_kit_measure.py` (2026-10-18) | K1–K8 for the HTML lesson: the encoding-name and special-token traps, real code and digits, bytes vs characters, a tiny BPE trained on the PDF, dated cost and run-time arithmetic, the window share. `p1_measure.py` is unchanged | `out_p1_kit_measure.txt`, `out_p1_kit_measure.stderr.txt` (empty) |

- **Re-run** (from `rag_learning/`, Git Bash):
  ```bash
  B="C:/Yash/New-Work/Book RAG"
  PYTHONIOENCODING=utf-8 uv run python sources/verification/P1/p1_measure.py "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
      > sources/verification/P1/out_p1_measure.txt 2> sources/verification/P1/out_p1_measure.stderr.txt
  PYTHONIOENCODING=utf-8 uv run python sources/verification/P1/p1_sources.py "$B/upstream/RAG_Techniques" "$B/RAG_Made_Simple_The_Complete_Visual_Guide" \
      > sources/verification/P1/out_p1_sources.txt
  PYTHONIOENCODING=utf-8 uv run python sources/verification/P1/p1_strawberry.py \
      > sources/verification/P1/out_p1_strawberry.txt
  ```
- **Determinism.** Two consecutive runs of `p1_measure.py` gave byte-identical stdout (the only later change was one added print line, the cache snapshot id).

## 1. Facts by section

`M` = `p1_measure.py` (section in `out_p1_measure.txt`); `S` = `p1_sources.py`.

### S1 Extraction

| Fact | Value | Source |
|---|---|---|
| Pages / characters / page-1 characters | 33 / 72,593 / 2,424 | M S1 |
| Same text length as 07's PyMuPDF figure | 72,593 (07 D.8 used PyMuPDF 1.28.2; equal here under 1.26.7) | M S1 |

### S2 Tokenizer identities

| Fact | Value | Source |
|---|---|---|
| Vocab sizes cl100k / o200k / o200k_harmony / gpt2 | 100,277 / 200,019 / 201,088 / 50,257 | M S2 |
| MiniLM WordPiece vocab, casing | 30,522, `do_lower_case=True` | M S2 |
| `tiktoken.encoding_for_model`: gpt-3.5-turbo / gpt-4o-mini / gpt-oss-20b | `cl100k_base` / `o200k_base` / `o200k_harmony` | M S2 |

### S3 Characters per token on samples (WordPiece counts exclude `[CLS]`/`[SEP]`)

| Sample | Chars | cl100k (c/t) | o200k (c/t) | WordPiece (c/t) | chars÷4 | chars÷4 error vs cl100k |
|---|---|---|---|---|---|---|
| Whole document | 72,593 | 13,026 (5.57) | 12,840 (5.65) | 11,694 (6.21) | 18,148 | +39% |
| Page 1 | 2,424 | 490 (4.95) | 486 (4.99) | 441 (5.50) | 606 | +24% |
| Window 0 [0,1000) | 1,000 | 201 (4.98) | 198 (5.05) | 186 (5.38) | 250 | +24% |
| Window 1 [800,1800) | 1,000 | 196 (5.10) | 193 (5.18) | 171 (5.85) | 250 | +28% |
| Window 2 [1600,2600) | 1,000 | 217 (4.61) | 218 (4.59) | 198 (5.05) | 250 | +15% |
| Code snippet (toy, written for P1) | 142 | 45 (3.16) | 45 (3.16) | 61 (2.33) | 36 | −21% |
| Numbers line (toy, made up) | 94 | 63 (1.49) | 63 (1.49) | 62 (1.52) | 24 | −63% |
| German sentence (written for P1) | 74 | 22 (3.36) | 16 (4.62) | 25 (2.96) | 18 | −16% |
| Hindi sentence (written for P1) | 61 | 62 (0.98) | 18 (3.39) | 36 (1.69) | 15 | −75% |

Also in M S3: `[UNK]` = 0 for every sample; whole document gpt2 = 14,375 tokens (5.05 c/t); `o200k_harmony` = `o200k_base` = 12,840 on the whole document; 9,255 whitespace words, 7.84 chars/word.

Windows are **plain fixed character slices** (size 1,000, overlap 200, the `simple_rag` cell 10 defaults), not LangChain's recursive splitter (not installed in the project environment).

### S4 Distribution over all windows

| Fact | Value | Source |
|---|---|---|
| Number of 1000/200 windows | 91 (last one 593 chars; 90 full) | M S4 |
| cl100k chars/token min/median/max; tokens per full window | 4.61 / 5.52 / 6.37; 157 / 180.5 / 217 | M S4 |
| o200k | 4.59 / 5.62 / 6.49; 154 / 177.5 / 218 | M S4 |
| WordPiece | 5.05 / 6.21 / 7.04; 142 / 160.5 / 198 | M S4 |

### S5 See the cut

| Fact | Value | Source |
|---|---|---|
| Sentence length | 67 chars | M S5 |
| cl100k / o200k / WordPiece pieces | 12 / 13 / 16 incl. `[CLS]`,`[SEP]` (14 text tokens); pieces listed in the output | M S5 |
| `'Greenland'` / `' Greenland'` / `'GREENLAND'` (cl100k) | 2 / 1 / 2 tokens | M S5 |

### S6 MiniLM truncation

| Fact | Value | Source |
|---|---|---|
| `max_seq_length` / runtime `tokenizer.model_max_length` / dim / modules | 256 / 256 / 384 / Transformer, Pooling, Normalize | M S6 |
| Test passage | doc offset 4,836; 2,187 chars; 400 WordPiece text tokens; 254-token prefix 1,372 chars; 200-token prefix 1,122 chars; swapped-tail text 502 tokens | M S6 |
| IDs fed to the model (`preprocess`) | shape (1, 256); first 101 `[CLS]`, last 102 `[SEP]` | M S6 |
| Warnings / log records during `encode()` on a fresh model | 0 / 0 | M S6 |
| cos(400, prefix 254) ; max abs diff | 1.000000 ; 0.00e+00 | M S6 |
| cos(400, same 254 + different tail) | 1.000000 | M S6 |
| cos(400, prefix 200) | 0.988245 | M S6 |
| cos(400, its own tail) | 0.350182 | M S6 |
| The only length message in the run | from counting the whole PDF with the tokenizer directly: `11694 > 256` | `out_p1_measure.stderr.txt` |

### S7 Temperature (TOY logits [2.0, 1.5, 0.5, −1.0] for YES/NO/PARTIAL/MAYBE)

| T | p | Entropy (bits) | 1,000 draws, numpy `default_rng(0)` |
|---|---|---|---|
| 0.25 | 0.879 / 0.119 / 0.002 / 0.000 | 0.55 | — |
| 0.5 | 0.704 / 0.259 / 0.035 / 0.002 | 1.05 | 681 / 282 / 36 / 1 |
| 1.0 | 0.532 / 0.323 / 0.119 / 0.026 | 1.51 | 557 / 301 / 117 / 25 |
| 2.0 | 0.404 / 0.315 / 0.191 / 0.090 | 1.82 | 409 / 322 / 184 / 85 |
| 4.0 | 0.329 / 0.290 / 0.226 / 0.155 | 1.95 | — |

The draws share one generator in sequence (T = 0.5, then 1.0, then 2.0).

### S8 A repo heuristic on our corpus

| Fact | Value | Source |
|---|---|---|
| First 4,000 cl100k tokens of the PDF (`contextual_chunk_headers.ipynb` cell 11 says "~3000 words") | 21,085 chars = 2,869 whitespace words | M S8 |

### S9 Prompt budget (06 §3.3 template, four sample windows, not a retrieval result)

| Fact | o200k_harmony | cl100k | Source |
|---|---|---|---|
| System rules | 107 | 106 | M S9 |
| Question (06 seed D-001) | 20 | 20 | M S9 |
| Sources (4 × 1,000 chars + headers) | 842 | 845 | M S9 |
| User message | 869 | 872 | M S9 |
| System + user (4,659 chars) | **976** | 978 | M S9 |
| O2 smoke message / its reply, counted locally | 7 tokens (33 chars) / 4 tokens | — | M S9 |

### S10 Cost arithmetic (placeholder prices X, Y)

| Fact | Value | Source |
|---|---|---|
| 100 queries, input | 100 × 976 = 97,600 tokens | M S10 |
| 100 queries, output bound | ≤ 25,600 (`max_tokens` 256) or ≤ 51,200 (512) | M S10 |
| Doubling k 4 → 8 | +842 tokens: 976 → ~1,818, ×1.86 | M S10 |

### S11 "strawberry" (MC-001 flashcard, M.1 card 14; run 2026-10-09)

`p1_strawberry.py` (`out_p1_strawberry.txt`). tiktoken 0.14.0, `o200k_harmony` (`encoding_for_model('gpt-oss-20b')`). Tokenizer only: the plain string, outside the chat template. A second run was byte-identical.

| Text | Tokens | Pieces (IDs) |
|---|---|---|
| `strawberry` (nothing before it) | 3 | `st` `raw` `berry` (302, 1618, 19772) |
| ` strawberry` (leading space) | 1 | `·strawberry` (101830) |
| `"strawberry"` (double quotes) | 5 in total; the word itself is 3 | `"` `st` `raw` `berry` `"` (1, 302, 1618, 19772, 1) |
| `How many r's are in strawberry?` | 8 in total; the word itself is 1 | `How` `·many` `·r` `'s` `·are` `·in` `·strawberry` `?`; the word is ID 101830 |
| Letter `r` in `strawberry` (Python string count) | 3 | — |

`·` marks a leading space. What comes right before the word changes the cut: the same 10 letters are 1 ID after a space and 3 IDs otherwise.

### S-src Citations

`p1_sources.py`: **ALL PASS** (repo HEAD `009adba2…`; 34 cell-content checks across 12 cells; 8 book-page phrase checks; the "tokeniz" absence check; the "temperature" count).

| Citation | Checked content |
|---|---|
| `proposition_chunking.ipynb` cell 9 | `from_tiktoken_encoder(`, `chunk_size=200, chunk_overlap=50` |
| `reliable_rag.ipynb` cell 6 | `from_tiktoken_encoder(`, `chunk_size=500, chunk_overlap=0` |
| `contextual_chunk_headers.ipynb` cell 11 | `MAX_CONTENT_TOKENS = 4000`, `encoding_for_model('gpt-3.5-turbo')`, `MODEL_NAME = "gpt-4o-mini"`, `max_tokens=MAX_CONTENT_TOKENS`, `temperature=0.2`, `tokens[:max_tokens]`, `num_words=3000` |
| `simple_rag_with_llamaindex.ipynb` cells 4, 13 | the LangChain-vs-LlamaIndex length comment; `CHUNK_SIZE = 200`, `CHUNK_OVERLAP = 50`; `SentenceSplitter(chunk_size=CHUNK_SIZE, ...)` |
| `document_augmentation.ipynb` cells 4, 6 | `DOCUMENT_MAX_TOKENS = 4000`, `FRAGMENT_MAX_TOKENS = 128`, the Llama context comment; `re.findall(r'\b\w+\b', document)`, "number of tokens" docstring, `temperature=0` |
| `simple_rag.ipynb` cell 10 | `chunk_size=1000`, `length_function=len` |
| `choose_chunk_size.ipynb` cell 8 | `OpenAI(temperature=0, model="gpt-4o")`, `FaithfulnessEvaluator()` |
| `reliable_rag.ipynb` cell 14 | `ChatGroq(model="llama-3.1-8b-instant", temperature=0)`, grader prompt |
| `evaluation/define_evaluation_metrics.ipynb` cell 1 | `ChatOpenAI(temperature=0, model_name="gpt-4o", max_tokens=4000)` |
| `graph_rag.ipynb` cell 12 | `get_openai_callback() as cb`, prompt/completion tokens, `cb.total_cost`; `max_context_length` set once, never read in that cell |
| Book | Ch1 p.12/14, Ch2 p.9/11, Ch4 p.5/15, Ch9 p.9/14, Ch10 p.12/13, Ch22 p.8/19, p.14/19, p.18/19 (short phrases, each < 15 words); "tokeniz" only at Ch12 p.6/14 and p.10/14 (BM25 words); "temperature" 13 times, all about climate (read by hand) |

Re-run 2026-10-09: **ALL PASS**, output byte-identical to the saved `out_p1_sources.txt`.

### S-web Web pages read (2026-10-09; not run, not script-checked)

Read with a web fetch on 2026-10-09. Paraphrased. Pages can change; re-check before relying on them (the learner re-checks the Groq pages in lab Task 8).

| Page | What it says (paraphrase) | Used in |
|---|---|---|
| Groq API reference, chat completions (https://console.groq.com/docs/api-reference; Source C #55) | `temperature`: 0 to 2, default 1; lower is more focused. `seed`: the system makes a **best effort** to sample deterministically; determinism is **not guaranteed**; watch the `system_fingerprint` response field for backend changes. `top_p`: nucleus sampling, default 1; change it or temperature, not both. No `top_k` parameter. `n`: only 1 is supported. This page says nothing about converting temperature 0. | D.6, J5, M.1 card 11 |
| Groq OpenAI compatibility (https://console.groq.com/docs/openai) | A temperature of 0 is converted to `1e-8`; if that causes issues, use a float above 0 and at most 2. `N` must be 1. | D.6, J5 |
| H. He and Thinking Machines Lab, "Defeating Nondeterminism in LLM Inference", 2025-09-10 (https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) | Main cause of run-to-run differences on inference servers: server load changes the batch size, and the kernels are not batch-invariant, so one request's result depends on what else is in its batch. Experiments used vLLM on GPUs. Groq is not mentioned. Read through a fetch summary. | D.6 (as the GPU-server cause only; UNVERIFIED for Groq) |

## 1b. Added 2026-10-18: K1–K8 (`p1_kit_measure.py`) for the HTML lesson

`K` = `p1_kit_measure.py` (section in `out_p1_kit_measure.txt`). Run from `rag_learning/` with the repo path as the argument:
`PYTHONIOENCODING=utf-8 uv run python sources/verification/P1/p1_kit_measure.py "C:/Yash/New-Work/Book RAG/upstream/RAG_Techniques"`. A second run was byte-identical (`cmp`). Tokenizers only; no API call, no `.env` read.

| Id | Fact | Value |
|---|---|---|
| K1 | Environment | Python 3.12.8; pymupdf 1.26.7, tiktoken 0.14.0, tokenizers 0.23.2; PDF 72,593 chars, 33 pages |
| K2 | `tiktoken.encoding_for_model` on model ids | `gpt-oss-20b` → `o200k_harmony`; **`openai/gpt-oss-20b` (the `.env` id) → `KeyError`**; `gpt-4o-mini` → `o200k_base`; `gpt-3.5-turbo` → `cl100k_base`. Fixes: `get_encoding("o200k_harmony")`, or strip the provider prefix |
| K3 | Special tokens | `o200k_harmony`: vocabulary 201,088, 1,091 special tokens, including the chat-format tokens `<|start|>` `<|channel|>` `<|message|>` `<|end|>` `<|return|>` `<|call|>`. `encode("<|endoftext|>")` and `encode("<|start|>")` raise `ValueError` (disallowed special token); with `disallowed_special=()` they become 7 and 5 ordinary tokens |
| K4 | Real code; digits | `helper_functions.py` 11,847 chars → 2,570 `o200k_harmony` tokens (**4.61** chars/token; cl100k 2,553, 4.64); `evaluation/evalute_rag.py` 5,046 → 1,102 (4.58; cl100k 1,098, 4.60). Pieces: `1234567` → `123` `456` `7`; `1,234,567` → `1` `,` `234` `,` `567`; `2023-11-07` → `202` `3` `-` `11` `-` `07`; `650,000` → `650` `,` `000`; `1.5` → `1` `.` `5` |
| K5 | Bytes vs characters (`o200k_harmony`) | Whole PDF: 72,593 chars, 72,595 UTF-8 bytes, 12,840 tokens: 5.65 chars/token = 5.65 bytes/token. Hindi sentence (S3): 61 chars, 161 bytes, 18 tokens: 3.39 chars/token, 8.94 bytes/token |
| K6 | A tiny BPE trained on the PDF (`tokenizers` BpeTrainer, whitespace pre-tokenizer, vocab 300, min frequency 2) | 230 merges learned; first 12: `i+n`, `a+n`, `e+s`, `a+t`, `o+n`, `e+n`, `an+d`, `e+r`, `i+on`, `in+g`, `r+e`, `a+l`; a second training run gives identical merges. Splits: `the` 1, `climate` 1, `emissions` 1, `greenhouse` 4 (`gre` `enh` `ous` `e`), `deglaciation` 6 (`de` `g` `l` `ac` `i` `ation`); `o200k_harmony` after a space: 1, 1, 1, 1, and 4 (`·de` `gl` `aci` `ation`) |
| K7 | Dated prices (per 1M tokens, read 2026-10-17, LLMOPS_FOUNDATION §6.2; external): Groq `openai/gpt-oss-20b` $0.075 in / $0.30 out; Claude Haiku 5.5 $0.10 / $0.50 | One v0 call (976 in + 512 out cap): Groq ≤ **$0.000227**, 100 calls ≤ **$0.0227**, output = 67.7% of the bill; Haiku ≤ $0.000354, 100 calls ≤ $0.0354, output 72.4%. Output/input price: Groq 4.0×, Haiku 5.0×. Run time: 100 × (976 + 71 + 512 = 1,559) = 155,900 tokens ≥ **19.5 min** at 8,000 tokens/min; 55 calls ≥ 10.7 min |
| K8 | v0 call in the window (Groq model page, read 2026-10-17: window 131,072, max output 65,536) | 976 + ~71 + 512 = 1,559 tokens = 1.19% of 131,072; sources = 842/976 = 86% of the counted input |

Notes: the Haiku cost uses `o200k_harmony` counts as a **proxy**; Claude's own count comes from its `count_tokens` endpoint (newer Claude tokenizers give more tokens for the same text). The 71-token overhead is the B.3 inference from one logged call. The 8,000 tokens/min limit is Groq's listed limit for this model; which plan that row belongs to is UNVERIFIED (LLMOPS_FOUNDATION finding 5).

## 2. CITED, DERIVED and UNVERIFIED

| Item | Status |
|---|---|
| `gpt-oss-20b` returned an empty reply at `max_tokens=12` | CITED: `progress/session_log.md`, session 2026-10-08 #2 (not re-run) |
| Billed 78 prompt / 23 completion tokens for the smoke call (`max_tokens=256`, `reasoning_effort="low"`, T = 0) | CITED: `progress/O2_smoke_test_2026-10-08.json` (and the identical clean-clone report) |
| ≈71 extra prompt tokens, ≈19 extra completion tokens | DERIVED (78 − 7, 23 − 4); their composition is UNVERIFIED |
| 976 + 512 = 1,488; 97,600 × 0.10 / 10⁶ + 51,200 × 0.20 / 10⁶ = $0.0200 with 06's **hypothetical** prices; 2000 / 5.52 ≈ 362 (range 314–434); Day-7 card (48,800 X + 25,600 Y) / 10⁶; 842 / 976 = 86% | DERIVED in the lesson |
| T = 1 hand computation (e² etc.) | DERIVED; matches S7 |
| Temperature 0 not bit-identical on hosted APIs | Groq promises no determinism (S-web, read 2026-10-09). Whether our runs actually differ, and why, is UNVERIFIED (08 RK-17; M4's repeated-generation subsample). The batch cause is shown for GPU servers only, not for Groq |
| A description of top-k sampling | UNVERIFIED (no course source; Groq has no `top_k` parameter, S-web) |
| Groq context window and prices for `openai/gpt-oss-20b` | Documented (read 2026-10-17, Groq model page; external): window 131,072, max output 65,536, $0.075 in / $0.30 out / $0.037 cached input per 1M (§1b K7–K8). The lab's look-up task stays: prices change |
| Groq behaviour past the window; `finish_reason` value at the cap | UNVERIFIED |
| Model context sizes in the `document_augmentation.ipynb` cell 4 comment | UNVERIFIED |

## 3. Notes for 07 and 04 (not edited; recorded here)

- **07 Verification log, "Still UNVERIFIED":** "`[CLS]`/`[SEP]` counting and the 128-vs-256 override inside sentence-transformers" is now **verified** (S6): the model receives 256 IDs including `[CLS]` and `[SEP]`, and the runtime `model_max_length` is 256.
- **07 D.5 consistency:** cl100k 5.57 chars/token on both extractions; WordPiece 11,694 tokens on both (6.20 vs 6.21 chars/token, because PyMuPDF yields 70 more characters).
- **04 P1 row:** see the lesson's G.2 corrections (cell 11's dual-use constant and tokenizer mismatch; `document_augmentation` cell 4 holds the constants; Ch22 p.14/19 names token cost).
