# I6_FACTS: what the I6 lesson can rely on (run-verified)

Run date: **2026-10-18**. Every measured number in the I6 lesson (`study/lessons/I6_doc_augmentation.html`), its reading file, its question file, its verify notebook and its apply-it tool is listed here with the command and the output section that produced it. Numbers that these runs did not produce are marked CITED, DERIVED, EXTERNAL or UNVERIFIED. The research behind the lesson is `study/research/phase_04_indexing.md`, "Concept I6".

## 0. Environment, provenance, how to re-run

- **Where it ran.** A Claude Code cloud container (Linux, CPython 3.12.3), not Yash's Windows machine. The project `uv` environment was created there from `uv.lock` (`uv sync --all-groups`), so the library versions are the locked ones: pymupdf 1.26.7 · sentence-transformers 6.1.0 · transformers 5.19.0 · torch 2.14.1 · numpy 2.5.3 · tiktoken 0.14.0 (printed in K1).
- **Corpus.** `Understanding_Climate_Change.pdf` from `NirDiamant/RAG_Techniques` @ `009adba2`, sha256 `1d58a0fa…a92669` (same file as P2–P7). v0's **97 chunks** are rebuilt exactly as P4 K1 does it (06 §5.3 snapshot, 07 recursive chunker, per page, 1000/200): chunks.jsonl sha256 `d4108b89…3011b`, identical to P3 verify, P4 and the C2 lab.
- **Model.** `sentence-transformers/all-MiniLM-L6-v2`. Hugging Face was blocked in the container, so the weights were **rebuilt from Chroma's ONNX export of the same model** (`chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz`) into the local HF cache under the snapshot name `onnx-rebuild-chroma` (K1 prints `onnx-reb`; on Yash's machine it prints `1110a243`). **Parity was checked before any I6 number was used:** the rebuilt model reproduces P4 K3 exactly (D-002 top 5 = `[69, 68, 27, 17, 84]`, scores 0.4606 / 0.4513 / 0.4386 / 0.4385 / 0.3387) and P4 K6's `cos('greenhouse gas emissions', …) = 0.5356 / −0.0859`. The stderr file holds only the harmless "pooler weights missing" note (sentence-transformers never uses the pooler).
- **Tokenizer.** `o200k_harmony` (tiktoken 0.14.0). Its BPE file could not be downloaded from `openaipublic.blob.core.windows.net`; tiktoken's cache was filled from the copy bundled in the `litellm` 1.105.1 wheel (PyPI), and tiktoken's own sha256 check of the file passed. Check: v0 chunk tokens 68 / 162 / 192 (min / median / max) equal C4's logged values.
- **The question pack (stand-in).** `study/tools/examples/climate_i6_questions.jsonl`, sha256 `b6d060c7…ce2c9`: 97 lines, one per chunk, keyed by `text_sha256`, **10 questions each (970)**. Written on 2026-10-18 by four Claude helpers, each given only the prompt file `study/tools/examples/i6_questions_prompt_v1.txt` (sha256 `b44a15ec…6fab`, `n_max = 10`) and its share of the chunk texts, one chunk at a time. **They never saw the eval set, 06 or any other repo file.** It stands in for the replay pack the LLMOps notebook will record with Groq or Haiku (research §9; `study/llmops/` does not exist yet). So every question-dependent number below is a measurement **on this pack**; a Groq or Haiku pack will give different numbers.
- **Eval items.** The 10 draft seeds of 06 §6.7 (8 answerable; all `created_by: "llm-draft"`, not human-verified) and the one paraphrase variant 06 gives, `D-002-P1`. **8 answerable items prove nothing**: every rank below is an observation on draft seeds, never an evaluation result.
- **No API calls.** No Groq, Cohere or Claude API call; `.env` is never read.
- **Book.** *RAG Made Simple* is **not present** in the container. No book page was opened; every book page in the I6 files comes from 02/04 (as in the research file) and is labelled "per 04, not re-opened". The book-page and whole-book 15-word checks of `i6_md_check.py` therefore SKIP here and must be run on Yash's machine.
- **Scripts and outputs** (this folder):

  | File | What it is |
  |---|---|
  | `i6_kit_measure.py` → `out_i6_kit_measure.txt` (+ `.stderr.txt`) | K1–K12: the upstream parent, the toy multi-vector index, index sizes, the pack's cleaning signals, retrieval on the seeds, the D-006 trace, leakage, cost, context size, the shape gap |
  | `i6_sources.py` → `out_i6_sources.txt` | S-src: every cited upstream cell and script line, the framework source lines, the AIQ Q45 quote (48 checks, ALL PASS) |

- **Re-run** (from `rag_learning/`, Git Bash):
  ```bash
  B="C:/Yash/New-Work/Book RAG"
  PYTHONIOENCODING=utf-8 uv run python sources/verification/I6/i6_kit_measure.py "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
      > sources/verification/I6/out_i6_kit_measure.txt 2> sources/verification/I6/out_i6_kit_measure.stderr.txt
  PYTHONIOENCODING=utf-8 uv run python sources/verification/I6/i6_sources.py "$B/upstream" <libs dir> > sources/verification/I6/out_i6_sources.txt
  ```
  `<libs dir>` holds `multi_vector.py` (langchain-classic==1.0.8), `vectorstores_base.py` (langchain-core==1.6.6) and `metadata_extractors.py` (llama-index-core v0.14.25) from raw.githubusercontent.com at those tags; without it those 7 checks print SKIPPED.
- **Determinism.** Two consecutive runs of `i6_kit_measure.py` gave **byte-identical** stdout. On Yash's machine only the K1 lines (Python version, model snapshot) should differ.

## 1. Facts by section

`K` = `i6_kit_measure.py` (section in `out_i6_kit_measure.txt`). A1 = chunks + questions, A2 = questions only, A0 = chunks only (v0). Parent score = max over the parent's vectors; duplicates removed before the cut ("dedup before cut"); ties by the smaller chunk seq.

### K1 Corpus, seeds, pack

| Fact | Value | Source |
|---|---|---|
| Chunks / seeds / answerable | 97 / 10 / 8 | K1 |
| Relevant chunk seqs | D-001 [7] · D-002 [27] · D-003 [68] · D-004 [23, 67, 68] · D-005 [3, 4] · D-006 [21] · D-007 [27, 85] · D-008 [69] | K1 |
| Categories | exact-term D-001, D-004, D-008 · factual-single-span D-002, D-003 · multi-span D-005 · vocabulary-mismatch D-006 · multi-hop D-007 · unanswerable D-009, D-010 | K1 |
| Pack | 97 lines × 10 = 970 questions | K1 |
| Vectors | chunks (97, 384), questions (970, 384), unit length (max \|norm − 1\| 1.19e-07) | K1 |

### K2 The upstream `document_augmentation` parent on this PDF

| Fact | Value | Source |
|---|---|---|
| Text (`read_pdf_to_string`: pages joined with no separator) | 72,561 characters; 9,406 regex words (`\b\w+\b`); 9,255 whitespace words | K2 |
| 4000/100 parents | **3**: 4,000 / 4,000 / 1,606 words = **42.5% / 42.5% / 17.1%** of the PDF's regex words | K2 |
| 128/16 fragments | 36 / 36 / 15 = 87 | K2 |
| Tokens per parent (o200k_harmony) | **4,271 / 4,237 / 1,687** | K2 |
| Punctuation | 1,493 punctuation characters in the PDF text, **0** in the parents ("1.2 degrees" becomes "1 2 degrees") | K2 |
| v0 chunk tokens | min / median / max 68 / 162 / 192; mean 151.7 | K2 |

The research's DERIVED estimates (I6-E1: about 3 parents, about 43% each, about 85–95 fragments, about 5.3K tokens) are now measured: 3 parents, 42.5%, 87 fragments, at most 4,271 tokens.

### K3 Toy multi-vector index (made-up scores; TOY)

Vectors (kind, parent, score): v1 A question 0.81 · v2 B question 0.74 · v3 B question 0.72 · v4 B chunk 0.70 · v5 B question 0.69 · v6 C question 0.66 · v7 C chunk 0.55 · v8 A chunk 0.50.

| Fact | Value | Source |
|---|---|---|
| max | A 0.81, B 0.74, C 0.66 → **A, B, C** | K3 |
| sum | A 1.31, B 2.85, C 1.21 → **B, A, C** (B has 4 vectors) | K3 |
| mean | A 0.655, B 0.7125, C 0.605 → B, A, C | K3 |
| RRF (k = 60) over the chunk list [B, C, A] and the question list [A, B, C] | A 0.032266, B 0.032522, C 0.032002 → B, A, C | K3 |
| Unique parents in the top 3 / 4 / 6 / 8 vectors | 2 / 2 / 3 / 3 | K3 |
| k = 3: cut then dedup vs dedup then cut | [A, B] vs **[A, B, C]** | K3 |
| LangChain default emulation (4 child vectors) | **2 parents** for "k = 4"; with `search_kwargs={"k": 8}`: 3 | K3 |

### K4 Index size (97 chunks; float32)

| n | chunks + questions | questions only | bytes, chunks + q, 1,536-d / 384-d | Source |
|---|---|---|---|---|
| 1 | 194 (2×) | 97 (1×) | 1,191,936 / 297,984 | K4 |
| 3 | 388 (4×) | 291 (3×) | 2,383,872 / 595,968 | K4 |
| 5 | **582 (6×)** | **485 (5×)** | **3,575,808** / 893,952 | K4 |
| 10 | 1,067 (11×) | 970 (10×) | 6,555,648 / 1,638,912 | K4 |

C3 baseline 596,096 bytes = 128 + 97 × 1,536 × 4 (C3_FACTS). The third design (questions appended to the chunk text) stays at 97 vectors.

### K5 The stand-in pack: cleaning rules and quality signals

| Fact | Value | Source |
|---|---|---|
| Rule counts on 970 | empty 0 · no "?" 0 · numbering 0 · deictic/vague regex **1** (a false positive: "in the context of climate change") · duplicates inside a chunk 0 · **exact duplicates across chunks 6** | K5 |
| Length | 3 / 8 / 15 words (min / median / max); median 10 tokens | K5 |
| Vocabulary echo (share of a question's content words found in its own chunk) | mean **0.777**, median 0.800; 227 of 970 use only chunk words | K5 |
| Rare-token retention (numbers and acronyms of the chunk found in its questions) | n = 1 **0.066** (6/91) · n = 3 0.143 · n = 5 **0.264** (24/91) · n = 10 **0.549** (50/91) | K5 |
| cos(question, own chunk) | min 0.0407 · p10 0.4274 · median **0.5917** · max 0.8464 | K5 |
| Own chunk's rank among 97 (question as query) | rank 1: **529** · ≤ 4: 830 · ≤ 10: 912 · > 10: **58** (of 970) | K5 |
| Histogram of cos(question, own chunk), bins of 0.1 from 0.0 | 5, 8, 20, 45, 132, 314, 322, 114, 10, 0 | K5 |
| Bottom-30% filter (bi-encoder stand-in for Doc2Query--'s cross-encoder) | cut 0.5351; drops 291, keeps 679 | K5 |
| Lowest three (seq, cos, own rank) | (73, 0.0407, 81) · (63, 0.0439, 76) · (87, 0.0618, 65) | K5 |
| Chunk 21 (p.8, D-006's gold), first 3 questions | "What are perovskite solar cells and solar paint?" · "What are floating solar farms?" · "Why do floating solar panels work more efficiently?" | K5 |
| Questions closer to a sibling question of the same chunk than to the chunk itself | **859 of 970 = 0.886** | K5 |

### K6 Retrieval on the 8 answerable seeds (MiniLM)

| Arm | First relevant rank D-001…D-008 | Hit@1 | Hit@4 | MRR@10 | CE@1 / CE@2 / CE@4 (of 8) | Source |
|---|---|---|---|---|---|---|
| A0 chunks only (v0) | 3, 3, 1, 1, 1, 1, 2, 2 | 4 | 8 | **0.708** | 4 / 5 / 8 | K6 |
| A1 n = 1 | 1, 4, 1, 1, 1, 2, 3, 7 | 4 | 7 | 0.653 | 4 / 5 / 7 | K6 |
| A1 n = 3 | 1, 1, 1, 1, 1, 1, 3, 15 | 6 | 7 | 0.792 | 6 / 6 / 7 | K6 |
| **A1 n = 5** | 1, 1, 2, 1, 2, 1, 4, 1 | **5** | 8 | **0.781** | 5 / 7 / **7** | K6 |
| A1 n = 10 | 1, 1, 2, 1, 1, 2, 3, 1 | 5 | 8 | 0.792 | 5 / 7 / 7 | K6 |
| A2 n = 1 | 1, 17, 1, 2, 1, 4, 19, 13 | 3 | 5 | 0.469 | 3 / 4 / 5 | K6 |
| A2 n = 3 | 1, 1, 1, 3, 1, 1, 4, 31 | 5 | 7 | 0.698 | 5 / 5 / 6 | K6 |
| A2 n = 5 | same as A1 n = 5 | 5 | 8 | 0.781 | 5 / 7 / 7 | K6 |
| A2 n = 10 | same as A1 n = 10 | 5 | 8 | 0.792 | 5 / 7 / 7 | K6 |
| A1 n = 5, **sum** | 3, 1, 1, 1, 1, 2, 4, 1 | 5 | 8 | 0.760 | — | K6 |
| A2 n = 5, sum | 3, 1, 1, 1, 1, 3, 4, 1 | 5 | 8 | 0.740 | — | K6 |

- The CE@4 loss (8 → 7) is D-007 (multi-hop, needs chunks 27 **and** 85): with questions, other parents push one of its two chunks out of the top 4.
- `D-002-P1` ("When did countries adopt the Paris climate accord?"): chunk 27's rank A0 3 → A1 n = 5 **1** → A2 n = 5 1.
- **Duplicate parents.** Unique parents among the top 4 **vectors** (what LangChain's default returns), mean over the 8 seeds: chunks + q n = 1 3.50 · n = 3 3.12 · **n = 5 3.00 (min 2)** · n = 10 2.75 (min 2); questions only n = 5 3.25 (min 2). With K_vec = k(n + 1) the minimum is ≥ 5 in every arm.
- Vectors fetched before 4 unique parents appear (chunks + q, n = 10), per seed: 5, 5, 11, 10, 8, 5, 7, 4 (max **11**; the bound k(n + 1) = 44).

### K7 D-006 trace (chunks + questions, n = 5)

| Fact | Value | Source |
|---|---|---|
| A0 top 4 | chunks 21, 64, 14, 13 (pages 8, 22, 5, 5), scores 0.5331 / 0.5004 / 0.4772 / 0.4696; gold rank **1** | K7 |
| Top vector | 0.5976, question of chunk 21 (p.8): "Why do floating solar panels work more efficiently?" | K7 |
| Top 12 vectors | 11 questions + 1 chunk (chunk 21's own vector at rank 7, 0.5331); 8 unique parents among the 12 | K7 |
| After dedup, 4 parents | 21, 64, 19, 32 (pages 8, 22, 7, 11), scores 0.5976 / 0.5869 / 0.5752 / 0.5696 | K7 |
| D-002, A0 | best chunk 69 at 0.4606; the gold chunk 27 at **0.4386**, rank 3 (as P4 K3) | K7 |
| Chunk 21: best question vs chunk | 0.5976 vs 0.5331 | K7 |
| D-001 / D-002 / D-008 | gold rank A0 3 / 3 / 2 → A1 1 / 1 / 1; their top vectors are generated questions at **0.9311 / 0.9869 / 0.9368** ("How much have global temperatures risen since the late 19th century?", "When was the Paris Agreement adopted?", "What is the Kigali Amendment?") | K7 |

D-006 is **not** a failure for MiniLM on the 97 chunks (rank 1 already, as P4 K4 found); the research's "read v0's ranks for D-006" referred to the Cohere v0.1 traces, which are not in this container.

### K8 Per category (first relevant rank, A0 → A1 n = 5 → A2 n = 5)

exact-term D-001 3 → 1 → 1, D-004 1 → 1 → 1, D-008 2 → 1 → 1 · factual D-002 3 → 1 → 1, D-003 1 → 2 → 2 · multi-span D-005 1 → 2 → 2 · vocabulary-mismatch D-006 1 → 1 → 1 · multi-hop D-007 2 → 4 → 4. Source: K8. The questions-only exact-term "guard" does **not** fail on these three items, because the pack happens to contain a question naming each term (K9), not because questions keep rare tokens in general (K5: 0.264 at n = 5).

### K9 Leakage: eval questions against the 970 generated questions

| Item | leak_cos (best generated question) | its parent | best chunk cos | 3-gram containment | flagged | Source |
|---|---|---|---|---|---|---|
| D-001 | **0.9311** | 7 (q1) | 0.4929 | 0.750 | yes | K9 |
| D-002 | **0.9869** | 27 (q3) | 0.4606 | 0.500 | yes | K9 |
| D-003 | 0.7101 | 27 (q4) | 0.6497 | 0.182 | yes | K9 |
| D-004 | **0.9653** | 23 (q7) "What does DAC stand for?" | 0.4210 | 0.000 | yes | K9 |
| D-005 | 0.4723 | 3 (q7) | 0.4272 | 0.000 | no | K9 |
| D-006 | 0.6007 | 64 (q9) | 0.5331 | 0.000 | no | K9 |
| D-007 | 0.7565 | 17 (q5) | 0.7094 | 0.000 | yes | K9 |
| D-008 | **0.9368** | 69 (q4) | 0.2598 | 0.000 | yes | K9 |
| D-009 (unanswerable) | 0.7939 | 1 (q8) "What does IPCC stand for?" | 0.3099 | 0.000 | yes | K9 |
| D-010 (unanswerable) | 0.5826 | 6 (q4) | 0.5196 | 0.200 | no | K9 |
| D-002-P1 | 0.7305 | 27 (q3) | 0.6028 | 0.000 | yes | K9 |

- **τ.** The one paraphrase pair in 06 (D-002 vs D-002-P1) has cos **0.7054**. The research's rule (τ_cos = the 10th percentile over ≥ 10 base↔variant pairs, 06 §6.2) cannot be applied yet; 0.7054 is used as a **provisional** τ_cos, with τ_ngram = 0.5 ([P]).
- Generated questions with cos ≥ 0.7054 to any of the 10 seeds: **10 of 970** (parents 1, 7, 17, 23, 27 ×2, 68, 69 ×3).
- **A4 de-leaked A1** (n = 5, those 10 deleted): ranks 8, 4, 1, 1, 2, 1, 2, 18 · Hit@1 3 · Hit@4 6 · **MRR@10 0.547** (below A0's 0.708).
- Reading (in the lesson): the helpers never saw the seeds, so this is not copying. The same drafting habit (an LLM turning a chunk's key sentence into its obvious question) produced both the seeds and the index questions. On these 8 items the measured gain and the leakage cannot be separated; the decisive test needs human-written questions (research §9).

### K10 Index-build cost and time (97 calls; tokens measured; prices from `prices_2026-10-17.json`)

| Fact | Value | Source |
|---|---|---|
| Prompt template alone (n_max = 10) | 241 tokens | K10 |
| Input per call | min / median / max 309 / 403 / 433; total **38,095** | K10 |
| Visible output per call, median | n = 3: 37 · n = 5: 58 · n = 10: **111** | K10 |
| n = 10, visible only | output 10,797; Groq **$0.0061**; Haiku $0.0092; 48,892 tokens → TPM floor 6.1 min, 24.4% of a day | K10 |
| n = 10, + 300 reasoning tokens per call (assumed, UNVERIFIED) | output 39,897; Groq **$0.0148**; Haiku $0.0238; 77,992 tokens → **9.7 min**, **39.0%** of a day | K10 |
| n = 5, visible / + reasoning | Groq $0.0045 / $0.0133; Haiku $0.0066 / $0.0212; 5.5 / 9.1 min | K10 |
| HyDE break-even (calls) | index side uses 97 × rebuilds calls a month: 1× → 97 · **2× → 194** · 4× → 388 · 30× → 2,910 | K10 |

Prices: Groq gpt-oss-20b $0.075 / $0.30 per M; Haiku 5.5 $0.10 / $0.50 per M (CITED, read 2026-10-17); Groq limits 8,000 TPM, 200,000 TPD (plan UNVERIFIED). Haiku's tokenizer differs, so its figures are approximate. These replace the research's estimated table (§9, ≈ $0.019 / 11 min at n = 10), which assumed 350 input and 250 visible output tokens.

### K11 Context sent to the answer model

| Fact | Value | Source |
|---|---|---|
| k = 4 parents, A1 n = 5, tokens per seed | 696, 625, 553, 522, 660, 633, 644, 690; mean **627.9** | K11 |
| k = 4 chunks, A0 | 696, 644, 644, 610, 730, 642, 700, 702; mean **671.0** | K11 |
| Upstream k = 1 parent | 4,271 / 4,237 / 1,687 tokens; the largest is **6.4×** A0's mean | K11 |

### K12 The shape gap (best question score − best chunk score, n = 10)

D-001 0.4382 · D-002 0.5263 · D-003 0.0604 · D-004 0.5443 · D-005 0.0450 · D-006 0.0676 · D-007 0.0471 · D-008 0.6770 · D-009 0.4840 · D-010 0.0631 · D-002-P1 0.1277. Mean over the 8 answerable seeds **0.3007**; a question beats every chunk for all 8. The unanswerable D-009 gains 0.4840 (best score 0.3099 → **0.7939**), so a fixed score threshold for abstaining gets harder with questions in the index. Source: K12.

## 2. S-src citations (`i6_sources.py`: 48 checks, ALL PASS)

| Citation | Checked content |
|---|---|
| `document_augmentation.ipynb` (19 cells, no saved output) cell 4 | 4000 / 100, 128 / 16, `DOCUMENT_LEVEL`, `QUESTIONS_PER_DOCUMENT = 40` |
| cell 6 | numbering strip `^\d+\.\s*`; keep lines ending in "?"; `gpt-4o-mini`, temperature 0; "at least {num_questions}"; the "directly answerable … no answers or headers" clause; `with_structured_output(QuestionList)`; `list(set(...))`; `re.findall(r'\b\w+\b')` "tokens" joined by spaces |
| cell 10 | `metadata["text"] = text_document` (the 4000-word parent); `k=1`; the never-run `FRAGMENT_LEVEL` path |
| cells 13, 15, 17 | `read_pdf_to_string`; the parent is read from the loop variable `doc` left over from cell 15 |
| `helper_functions.py` | `read_pdf_to_string`: PyMuPDF, `content += page.get_text()` |
| `document_augmentation.py` L65–L66 | prompt without the notebook's "directly answerable" clause |
| `HyPE_…ipynb` (23 cells) cell 0 | "Up to 42" pp precision, "up to 45" pp claim recall, SSRN 5139335 |
| cells 7, 9, 13 | gpt-4o-mini, text-embedding-3-small, 1000/200; free-text "essential questions" split on newlines; PyPDFLoader + RecursiveCharacterTextSplitter |
| cell 11 | **SyntaxError at cell line 32** (`ast.parse`); `add_embeddings((page_content, vec))` with no metadata |
| cell 15 | "97/97" output (exec 71) after the broken cell 11 (exec 66): stale outputs |
| cells 17, 19 | `k=3`; `list(set(context))`; the saved output shows **3** distinct contexts (see I6-E10) |
| `HyPE_…py` L99, L152 | comma fixed; dedup with `set()` |
| `langchain-classic==1.0.8` `multi_vector.py` L55, L57, L60, L107–L113 | `id_key="doc_id"`; `search_kwargs={}`; similarity; first-seen ids, scores dropped, silent drops |
| `langchain-core==1.6.6` `vectorstores/base.py` L361–L362 | `similarity_search(..., k: int = 4)` |
| `llama-index-core` v0.14.25 `metadata_extractors.py` L253–L265, L282–L283, L334 | "unlikely to be found elsewhere"; 5 questions by default; stored as `questions_this_excerpt_can_answer` metadata |
| AIQ `04-rag-and-retrieval/questions.md` @ e080df2 (MIT, Copyright (c) 2026 Om) | Q45 heading verbatim; "echo the chunk's vocabulary, inflating retrieval scores" |

## 3. Not measured here: labels the lesson must carry

- **EXTERNAL (research file, dated):** doc2query MRR@10 21.8 vs BM25 18.6 at 61 vs 55 ms; docTTTTTquery 27.2 at 64 ms, 80 samples with the first 40 used, ≈ 8 TPU hours / ≈ $20; Doc2Query-- (70th-percentile filter; "+16% / −30% / −48%" UNVERIFIED); HyPE "up to +42 / +45 pp" (claimed, UNVERIFIED, not reproduced); HyDE method only.
- **Book (UNVERIFIED for this session, per 04):** Ch11 p.1/13 (asymmetry), p.6–8/13 (steps; sketch on p.8/13), p.9–10/13 (mirror image of HyDE), p.11/13 (how many questions); Intro p.5/8.
- **Cross-encoder filter.** `cross-encoder/ms-marco-MiniLM-L-6-v2` was not available in the container; K5's filter uses the bi-encoder cos(question, own chunk) as a stand-in. The verify notebook runs the cross-encoder when the model is in the local cache and SKIPs it otherwise.
- **Cohere `embed-v4.0` and `input_type`.** Not measured (no replay pack). The lesson treats `search_document` vs `search_query` for stored questions as an open design variable.
- **Reasoning tokens** for gpt-oss-20b at low effort: the 300-token figure is an assumption (UNVERIFIED).

## 4. Errors found while measuring (recorded, not edited in the research file)

| # | Where | Problem | Correct value |
|---|---|---|---|
| I6-E10 | research I6 §1 (HyPE cell 19) and §2 row 12 | "The saved output shows 2 contexts for k = 3" | The saved output shows **3 distinct** contexts. `set()` still loses the rank order, and duplicates still crowd top-k in general (K6: 2 unique parents in the top 4 vectors for 3 of 8 seeds at n = 5) |
| I6-E11 | research I6 §9 cost table | Estimated 350 input and 250 visible output tokens at n = 10 | Measured median 403 input and 111 visible output (K10); the cost and time are lower than estimated unless reasoning tokens dominate |
| I6-E12 | research I6 §6 step 1 | D-006 as "the failure" | With MiniLM on the 97 chunks D-006 is already rank 1 (K7, P4 K4); the lesson uses D-001, D-002 and D-008 (rank 3, 3, 2 → 1) and the D-002-P1 variant (3 → 1) as the visible effect, and D-006 for the trace |
| I6-E13 | research I6 §3 interview pick "AIQ 04 Q5 (retrieval unit vs generation unit, parent_id)" | At e080df2, Q5 is about chunk size and overlap | Use Q45 (the research's first choice) |
