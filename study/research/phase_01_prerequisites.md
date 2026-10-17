# Phase 1 research: Prerequisites

**What this is:** the research and gap audit for Phase 1 (P1, P2, P4, P5, P6 and P7), done 2026-10-17 by Claude (Opus 5.5). P3 is the finished pilot and was not audited again. Six helper agents each audited one concept with the method in `RESEARCH_PROMPT.md` §4. The lead read every result in full, re-checked the key facts, settled the conflicts between helpers, and wrote this summary and the phase-level notes.
**What this is not:** lessons or code. Nothing in the course was changed, nothing was installed, and no Groq, Cohere, Claude or LangSmith call was made. The only code run was offline: tokenizer counts and local MiniLM probes in the scratchpad. Their numbers are labelled "probe", "scratch" or "DERIVED" wherever they appear, and none is a course fact until a verify notebook logs it.

## Summary (read this first)

**The 5 most important gaps across the phase**
1. **The project's own models are barely taught.**
   - P4 never covers Cohere `embed-v4.0`'s settings: `input_type`, `output_dimension` 256–1,536 (a cut vector must be renormalised), and `truncate`, whose default END cuts long text silently. Cohere's docs do not say whether its vectors are unit length.
   - P1 and P7 miss the reasoning-model plumbing of `openai/gpt-oss-20b`. Groq deprecated `max_tokens` for `max_completion_tokens` (default 1,024). The lessons never say where reasoning tokens appear in `usage`, never teach `finish_reason`, and still mark the 131,072-token window "look it up".
2. **The limits of relevance labels are taught nowhere.** P6 counts every unjudged chunk as not relevant but never says what that costs. BEIR measured the cost: once the missing labels were filled in, ANCE's nDCG@10 rose from 0.654 to 0.735, while BM25's rose only from 0.656 to 0.668. Pool bias and tie rules are also missing (P2, P6).
3. **"Recall" means four things, and ANN is not taught.**
   - IR Recall@k, hit rate (also called Success@k), ANN recall (overlap with the exact top-k) and RAGAS context recall all share one word.
   - P5 names IVF and HNSW in a single UNVERIFIED table, with no mechanism, no knobs and nothing measured (P5, P6).
4. **Library conventions silently change scores and ranks.** None of these is taught (P4, P5, P6):
   - FAISS returns squared L2, where lower is better.
   - LangChain's relevance score, 1 − d/√2, goes negative below a cosine of about 0.293.
   - `InMemoryVectorStore` puts tied chunks in largest-index-first order.
   - trec_eval breaks ties by document id and uses linear gain.
5. **Grounded prompting misses roles, structure and evidence (P7).**
   - The lesson never says which message holds the rules, the chunks and the question. The chunks carry the same authority as the question, and gpt-oss-20b scores 0.639 on prompt-injection hijacking (o4-mini: 0.917).
   - No concept teaches structured output; P7 now owns it.
   - Lost in the middle is taught from the abstract only. The verified table shows GPT-3.5's middle-position accuracy (53.8%) below its score with no documents at all (56.1%).

**Tools to add** (install nothing yet; each concept's §10 has the lines)
- **`faiss-cpu==1.15.1`**, optional `ann` group (MIT; 16 MB Windows wheel): real HNSW and IVF for P5. Not `hnswlib`: its last release (0.8.0, 2023-12-03) is source only and needs a C++ compiler on Windows.
- **`ir-measures==0.4.3` with `pytrec-eval-terrier==0.5.10`**, optional `eval` group: an independent check of the metric code for P2, P6 and later M2. Pin the backend explicitly, because 0.5.11 came out on 2026-10-16 and is too new.
- **`nbclient==0.11.0`**, `dev` group: runs each notebook headless in the `replay` test. It is missing from the foundation's install list.
- **The foundation's `llmops` group** (`langchain-core`, `langsmith`, `arize-phoenix-otel`, `openinference-instrumentation-langchain`) for the six LLMOps notebooks, plus `anthropic` only when Claude credits exist. No Phase 1 concept needs `langgraph`: every flow is linear.
- **Not added:**
  - `hnswlib` and `pytrec_eval`: source only.
  - `ranx` and `pyserini`: heavy.
  - `ragas`: needs OpenAI.
  - `langchain-groq` and `langchain-cohere`: they conflict with the pinned SDKs.
  - `openai-harmony`: tiktoken is enough.

**Decisions Yash must make** (each answerable in a word)
1. Add `faiss-cpu` in an optional `ann` group? (**yes** recommended)
2. Add the `ir-measures` cross-check in an optional `eval` group? (**yes** recommended)
3. Once the `study/llmops/` package exists, record Phase 1's API calls (94 Groq + 12 Cohere, about $0.03 in total)? (**yes** recommended)
4. Keep Cohere `embed-v4.0` for the whole course, although `embed-v5.0-pro` and `embed-v5.0-fast` are now listed? (**yes** recommended; a switch re-embeds everything)
5. Study Phase 1 in the order P1 → P2 → P6 → P3 → P4 → P5 → P7? (**yes** recommended; reasons in the phase-level notes, §1)

Smaller preferences (optional Claude arms, which interview items to use, the example language) are in each concept's §11.

**Size of the build work**

| Concept | Size | Why |
|---|---|---|
| P1 | M | Facts S1–S11 are reused and the verify notebook is offline. New: `token_budget_check.py`, and an LLMOps notebook with 24 recorded Groq calls |
| P2 | M | The content is mostly right. The HTML rewrite adds 4 sections (incomplete labels, pool bias, ties, meanings of "relevance"). New: `qrels_check.py` and about 6 FACTS rows; no API |
| P3 | — | Pilot complete; one sentence to fix (see Concept P3) |
| P4 | M | The mechanism and facts are solid. New: the Cohere section, the training sidebar, the score-direction table, `embed_fit_check.py`, and 12 recorded Cohere calls |
| P5 | M | Exact search is done. New: the ANN section (IVF in NumPy, then HNSW/IVF via faiss), a re-run on the 97 v0 chunks, `vector_search_check.py`; no API |
| P6 | M | The lesson, code and 23 tests already match 06. New: a real-corpus example, the name-clash table, the BEIR holes, `retrieval_metrics_check.py`; no API |
| P7 | M | The lesson exists. New: about 6 sections (roles, real window, Liu's numbers, structured output, conflicts, context swap), `grounded_prompt_check.py`, and 70 recorded Groq calls |

All six LLMOps notebooks, the three without API calls included, import the shared `study/llmops/` package (foundation §10). It is not built yet, so it is the first build step.

**Phase 1 external calls** (each recorded once, then replayed with no key)

| Concept | Calls | Cost (upper bound) |
|---|---|---|
| P1 | 24 Groq (+ 3 optional Haiku; + 3 free `count_tokens`) | ≈ $0.005 (+ $0.002) |
| P2 | 0 | $0 |
| P4 | 12 Cohere embed, about 100k tokens | ≈ $0.012 (price UNVERIFIED) |
| P5 | 0 (about 3 Cohere calls only if C3's vectors cannot be replayed) | $0 |
| P6 | 0 | $0 |
| P7 | 70 Groq in stage 1 (+ 120 in stage 2, after M1; + 20 optional Haiku) | ≈ $0.015 (+ $0.026; + $0.022) |
| **Now** | **94 Groq + 12 Cohere** | **≈ $0.03** |

Rate limits, not money, set the pace. The 94 Groq calls use about 133K tokens. At 8K tokens per minute that is at least 17 minutes, and about two-thirds of a 200K daily quota. The plan behind these limits is UNVERIFIED (foundation §2.5).

---

## Concept P1: LLM fundamentals for RAG

**The short version.** The existing P1 lesson (2026-10-08, A–M template) is accurate on its measured core: tokenizer vs embedder (MC-001), chars per token, MiniLM truncation, softmax(z/T), and the cost formula. What it lacks is the 2026 reasoning-model plumbing that the course's own generator needs: `max_completion_tokens` (Groq deprecated `max_tokens`), where reasoning tokens show up in `usage`, `finish_reason`, Groq's documented window (131,072) and output cap (65,536), dated prices, why output costs 4× input, rate limits in tokens per minute, and how Claude differs (no temperature, its own tokenizer, a free `count_tokens` call). A scratch probe also found two counting traps that the lesson does not mention: `tiktoken.encoding_for_model("openai/gpt-oss-20b")` (the `.env` id) raises `KeyError`, and `encode()` raises `ValueError` on text that contains a special-token string. No P1 question file exists yet.

---

### 1. Sources checked

**Book pages (opened 2026-10-17, PyMuPDF 1.26.7 text, 1-based pages).** Paraphrased; nothing quoted.

| Page | What it contributes to P1 |
|---|---|
| Ch1 p.12/14 | Simple RAG is overkill when the documents fit inside the model's context window ("context window" is split across two lines in the PDF text, so a plain phrase search misses it) |
| Ch1 p.13/14 | Trade-off table: cost is low because embedding is cheap and there is one LLM call per query |
| Ch2 p.9/11 | Embedding calls are billed by the token, so embedding a 100,000-row table is the main cost; it is paid once |
| Ch4 p.5/15 | First-pass chunks are kept moderate so one LLM call can read a chunk without overflowing its window |
| Ch9 p.9/14 | Variable chunk lengths change how many chunks fit in the window |
| Ch10 p.2/13 | Loosely relevant chunk text fills the window and dilutes the answer |
| Ch10 p.12/13 | Compression suits small windows where every token counts; one extra LLM call per chunk |
| Ch15 p.1/12 | Near-duplicate chunks fill the window with redundancy |
| Ch21 p.7/13, p.11/13 | Summarising "a million tokens" per query is too expensive; Graph RAG is overkill if the knowledge base fits one window |
| Ch22 p.8/19 | Sampling-based consistency checks regenerate the answer with different random seeds (a use for T > 0) |
| Ch22 p.14/19 – p.15/19 | Track tokens per query (input context + output answer), embedding and rerank cost, time to first token, and p50/p95/p99; a larger K raises recall but also latency and cost |
| Ch22 p.18/19 | An LLM judge adds token cost per test case |
| App p.10/23 | Technique tables rate "Prep Cost" and "Query Cost" as Low/Medium/High only |
| Ch6 p.12/14, Ch7 p.10/11, Ch19 p.10/10 | Cost stated as "one extra LLM call" or "a few more tokens" |
| Search result | "temperature" appears 13 times, all about Earth's climate; no glossary entry for token, tokenizer or context window (App checked) |

**Repo cells (0-based, `RAG_Techniques` @ `009adba2…`, opened with `json`).**

| Cell | Confirmed content |
|---|---|
| `proposition_chunking.ipynb` 9 | `RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=200, chunk_overlap=50)` |
| `simple_rag.ipynb` 10 | `encode_pdf(..., chunk_size=1000, chunk_overlap=200)`, `length_function=len` (characters) |
| `document_augmentation.ipynb` 6 | `split_document` counts `re.findall(r'\b\w+\b', ...)` and calls them tokens; it also rejoins with `" ".join`, so punctuation is lost |
| `document_augmentation.ipynb` 4 | `DOCUMENT_MAX_TOKENS = 4000`, `FRAGMENT_MAX_TOKENS = 128`, a comment on model context sizes |
| `contextual_chunk_headers.ipynb` 11 | `MAX_CONTENT_TOKENS = 4000` used for truncation **and** as `max_tokens`; `encoding_for_model('gpt-3.5-turbo')` for a `gpt-4o-mini` call; `disallowed_special=()` |
| `reliable_rag.ipynb` 6 | `from_tiktoken_encoder(chunk_size=500, chunk_overlap=0)`, `k: 4` |

**Existing course files read.** 02 P1 card and Gate 1→2; 03 rows (lines 743–744 and the P1 edges); 04 P1 row; 06 §2.4–2.5, §7.5, §8.4–8.6; 08 Part 4 (D-03…D-32) and RK-17; `EXTERNAL_RESOURCES_REVIEW_2026-10-09.md` (§3a rows 1–3, §3b, reserves, §10); `concepts/P1_llm_fundamentals.md` (all); `labs/P1_tokens_lab.ipynb` (all 41 cells); `sources/verification/P1/P1_FACTS.md`; `progress/` (tracker, misconception log, session log 2026-10-08 #3–#4, O2 smoke JSON); `reviews/CORRECTIONS_LOG_2026-10-08.md` round 4; LLMOPS_FOUNDATION (all); P3 pilot (gap audit, HTML headings, verify notebook outline, tool docstring); FORMAT.md; both WRITING_STYLE files; visual-learning-writer SKILL and HTML_VISUAL_SPEC; skills `evals-foundations`, `llm-observability`, `improving-llm-agents`, `claude-api`; `transfer_seed_bank.md` (titles only, to avoid collisions).

**AE book.** Not needed for P1. The review (§1) already found AE changes nothing in P1.

**Interview repo (MIT, `ombharatiya/AI-Engineer-Interview-Questions` @ e080df2, Copyright (c) 2026 Om).** `02-llm-fundamentals/questions.md` Q9, Q10, Q11, Q12, Q20, Q21, Q22, Q23, Q42; `08-inference-and-production/questions.md` Q6, Q11, Q14; `14-company-interview-questions/harvey.md` headings only (not used: tutor-reserved).

**Scratch measurements (tokenizer only, no API; tiktoken 0.14.0; `scripts_P1/tok_probe.py`, output `scripts_P1/tok_probe_out.txt`).** Not logged in P1_FACTS; the verify notebook must re-run and log them as new S-ids.

```text
encoding_for_model('gpt-oss-20b')        -> o200k_harmony
encoding_for_model('openai/gpt-oss-20b') -> KeyError (the .env id has a provider prefix)
o200k_harmony vocab 201,088; 1,091 special tokens incl. <|start|> <|channel|> <|message|> <|end|> <|return|> <|call|>
encode('<|start|>')                      -> ValueError (special tokens are disallowed by default)
encode('<|start|>', disallowed_special=()) -> 5 ordinary tokens
repo helper_functions.py (11,847 chars)  -> 2,570 o200k_harmony tokens = 4.61 chars/token
repo evaluation/evalute_rag.py (5,046)   -> 1,102 tokens = 4.58 chars/token
'1234567' -> 123|456|7 ; '1,234,567' -> 1|,|234|,|567 ; '2023-11-07' -> 202|3|-|11|-|07
```

**External sources** (opened 2026-10-17 unless noted; all external).

| # | Source | What was tested / stated | Result used | Limits | Status |
|---|---|---|---|---|---|
| [P1-1] | Groq, model page `openai/gpt-oss-20b` — https://console.groq.com/docs/model/openai/gpt-oss-20b | Model card | Window 131,072; max output 65,536; $0.075 in / $0.30 out / $0.037 cached input per 1M; tool use, JSON object and schema modes, reasoning | Prices change; rate limits not on this page | verified |
| [P1-2] | Groq, API reference — https://console.groq.com/docs/api-reference | Chat parameters | `max_tokens` deprecated for `max_completion_tokens`; input + output limited by context length; `reasoning_effort` low/medium/high for gpt-oss, default **medium**, other values → 400; `include_reasoning` and `reasoning_format` mutually exclusive; T 0–2 default 1; top_p default 1; `seed` best effort, watch `system_fingerprint` | The usage object's fields are not listed on the page | verified |
| [P1-3] | Groq, Reasoning — https://console.groq.com/docs/reasoning | Reasoning guide | gpt-oss: effort low/medium/high; reasoning returned in a `reasoning` field by default, `include_reasoning=false` hides it; `reasoning_format` **not supported** for gpt-oss; the 1,024 default completion cap "may be too low" for reasoning | No gpt-oss-specific sampling advice; says nothing on how usage reports reasoning | verified |
| [P1-4] | Groq, OpenAI compatibility — https://console.groq.com/docs/openai | Unsupported fields | T = 0 is converted to 1e-8; `n` must be 1; `logprobs`, `top_logprobs`, `logit_bias` → 400 | — | verified (also read 2026-10-09, P1_FACTS S-web) |
| [P1-5] | groq-python `completion_usage.py` — https://raw.githubusercontent.com/groq/groq-python/main/src/groq/types/completion_usage.py | SDK types | `completion_tokens_details.reasoning_tokens`, `prompt_tokens_details.cached_tokens`, `queue_time`, `prompt_time`, `completion_time`; `total_tokens` = prompt + completion | Docstrings only. That reasoning sits **inside** `completion_tokens` is an inference (total = prompt + completion, and O2 billed 23 completion tokens for a 4-token reply); confirm on one recorded response | verified (source) |
| [P1-6] | tiktoken `model.py` — https://raw.githubusercontent.com/openai/tiktoken/main/tiktoken/model.py | Model→encoding map | `"gpt-oss-"` prefix → `o200k_harmony`; gpt-4o → o200k_base; gpt-3.5-turbo → cl100k_base | Prefix map only: a provider-prefixed id fails (scratch probe) | verified |
| [P1-7] | tiktoken README — https://github.com/openai/tiktoken | Library description | BPE is reversible, lossless, works on any text, compresses it; on average a token is about **4 bytes** | "4 bytes" is not "4 characters": non-ASCII characters take 2–4 bytes | verified |
| [P1-8] | openai/harmony README — https://github.com/openai/harmony | gpt-oss response format | gpt-oss must be used with the harmony format; channels analysis / commentary / final; turns wrapped in `<|start|>…<|message|>…<|end|>`; the example system message carries knowledge cutoff, current date, reasoning level and the channel list | Groq's exact rendering is not published | verified |
| [P1-9] | openai/gpt-oss README — https://github.com/openai/gpt-oss | Model usage | Recommends sampling at temperature 1.0 and top_p 1.0; reasoning effort low/medium/high | A recommendation, not a measured comparison against T = 0 | verified (also fetched 2026-10-09 by the review) |
| [P1-10] | Sennrich, Haddow, Birch, "Neural Machine Translation of Rare Words with Subword Units", ACL 2016 — https://arxiv.org/abs/1508.07909 | WMT15 En→De, En→Ru translation | BPE subwords beat a back-off dictionary by 1.1 / 1.3 BLEU; BPE = repeatedly merge the most frequent adjacent pair | MT, not LLMs; character base, not bytes | verified (abstract) |
| [P1-11] | Kudo & Richardson, "SentencePiece", EMNLP 2018 demo — https://arxiv.org/abs/1808.06226 | En–Ja NMT | Training from raw sentences (no pre-tokenisation) is about as accurate as from pre-tokenised text | Demo paper; small validation | verified (abstract) |
| [P1-12] | Petrov, La Malfa, Torr, Bibi, "Language Model Tokenizers Introduce Unfairness Between Languages", NeurIPS 2023 — https://arxiv.org/abs/2305.15425 | Token counts of the same text translated into many languages | Up to 15× more tokens for some languages; the gap remains even for multilingual tokenizers; consequence: higher cost, latency, less usable context | Dataset and tokenizer list not checked (HTML version 404) | verified (abstract); details UNVERIFIED |
| [P1-13] | Hugging Face, "Tokenization algorithms" — https://huggingface.co/docs/transformers/tokenizer_summary | Library docs | BPE merges by frequency; byte-level BPE (GPT-2: 256 bytes + 50,000 merges + 1); WordPiece merges by freq(ab)/(freq(a)·freq(b)) and uses `##`; Unigram prunes a large vocabulary; SentencePiece works on raw text with `▁` for space | Docs, not a study | verified |
| [P1-14] | Holtzman, Buys, Du, Forbes, Choi, "The Curious Case of Neural Text Degeneration", ICLR 2020 — https://arxiv.org/abs/1904.09751 | Decoding strategies on one LM | Likelihood-maximising decoding gives bland, repetitive text; nucleus (top-p) sampling keeps the dynamic head and cuts the tail | Abstract only; top-k not mentioned there | verified (abstract) |
| [P1-15] | Anthropic, Token counting — https://platform.claude.com/docs/en/build-with-claude/token-counting | Docs | `POST /v1/messages/count_tokens` (`client.messages.count_tokens`); free but rate-limited (5,000 RPM at Start tier); the count is an **estimate** and may include system-added tokens that are not billed; Claude 4.7+ uses a newer tokenizer with roughly 30% more tokens; recount per model | — | verified |
| [P1-16] | `claude-api` skill (model table cached 2026-10-06) | Model facts | Haiku 5.5 `claude-haiku-5-5` $0.10/$0.50 (≤100K prompt), 1M window, effort default `medium`, non-default sampling values → 400, thinking adaptive and on by default; Sonnet 5.5 $2/$10, effort default `high`; Opus 5.5 $4/$20, sampling removed, thinking cannot be disabled; skill says count Claude tokens with `count_tokens`, never tiktoken | Cached table; re-check before paid runs | read locally |
| [P1-17] | Cohere, Tokenize reference and Models page — https://docs.cohere.com/reference/tokenize, https://docs.cohere.com/docs/models | Docs | `POST /v1/tokenize` (text ≤ 65,536 chars, needs a key); `embed-v4.0` context 128k, dimensions 256–1536 | Free or not: not stated | verified |
| [P1-18] | cohere-python 7.2.0, installed source (`cohere/client.py` L328–347; `manually_maintained/tokenizers.py` L19–40) | Read-only | `tokenize(..., offline=True)` by default: calls `models.get(model)` for a `tokenizer_url`, downloads it, caches it **in memory only** | Whether `embed-v4.0` exposes a `tokenizer_url` is UNVERIFIED | read locally |
| [P1-19] | langchain-core `messages/ai.py` (master) — https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/messages/ai.py | Source | `UsageMetadata`: `input_tokens`, `output_tokens` (sum of all output types), `output_token_details.reasoning`, `input_token_details.cache_read` | master, not the 1.6.6 pin | verified |
| [P1-20] | H. He / Thinking Machines Lab, "Defeating Nondeterminism in LLM Inference", 2025 — https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/ | Qwen3-235B, T = 0, 1,000 runs | 80 distinct completions; batch-invariant kernels → all identical | GPU/vLLM; not shown for Groq | verified by the foundation (src 21) and P1_FACTS S-web; not reopened |
| [P1-21] | OpenAI Help, "What are tokens" | — | — | HTTP 403 | UNVERIFIED; not used |
| [P1-22] | PyPI JSON for `openai-harmony`, `nbclient` | Release dates | openai-harmony 0.0.8 (2025-11-05); nbclient 0.11.0 (2026-06-05), BSD-3 | openai-harmony licence field empty on PyPI | verified |

---

### 2. Gap audit

"Studied" uses the tracker: P1 is `exposed` (Parts A–F taught 2026-10-08; lab and Part L **not done**); P4, P7, C2, C5, M4, D2 `not_started`.

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Token, vocabulary, token ID | everywhere | yes (D.1) | P1 | yes (P1-A1 = 3) | core | Keep; open with the cut, then IDs |
| 2 | The tokenizer cuts; the embedder only looks up IDs (MC-001) | D.1, M.1, every count | yes | P1 | exposed; MC-001 still open | core | Keep as the first section in Short; one strip diagram |
| 3 | How BPE learns its pieces (merge the most frequent pair, repeat) | "learned from text frequency" (C, M.1 card 14) | **incomplete**: asserted, never shown | P1 | no | core | Short: one paragraph + a merge list learned from the climate PDF itself. **No quiz item** on hand-merging (tutor-reserved) |
| 4 | WordPiece, Unigram, SentencePiece, byte-level BPE | D.2 (WordPiece only) | incomplete | P1 | partly | core (Full) | Full: a 4-row table; byte-level BPE explains why no `[UNK]` |
| 5 | Leading space and case change the count | C, S5, S11 | yes | P1 | yes | core | Keep |
| 6 | Chars per token varies by content and language | D.3 | yes (measured) | P1 | yes | core | Keep the measured table; add the external study (Petrov 2023) and the "4 **bytes**" origin of ÷4 |
| 7 | Numbers split into digit groups; code ≈ 4.6 chars/token | D.3 (toy lines) | incomplete | P1 | no | core | Short: one line from the scratch probe (to be logged); real repo code instead of toy code |
| 8 | Which tokenizer to count with: embedder (truncation), generator (prompt budget), provider `usage` (bill) | K, H.3 | yes | P1 | partly | core | Keep as a 3-row rule table |
| 9 | `encoding_for_model` needs the bare model name; the `.env` id `openai/gpt-oss-20b` raises `KeyError` | M.1 card 13, every counter | **missing** | P1 | no | core | Short: a one-line trap with the fix `get_encoding("o200k_harmony")` |
| 10 | Special-token strings in documents (`<|endoftext|>`, `<|start|>`) make `encode()` raise | any counter on user documents | **missing** | P1 | no | core | Full; the apply tool checks it |
| 11 | Chat template / harmony format adds hidden input tokens | B.3 (78 billed vs 7 counted) | incomplete ("inference") | P1 | partly | core | Name the mechanism: harmony system message (cutoff, date, reasoning level, channels). Keep "composition UNVERIFIED for Groq" |
| 12 | Context window = input + output; Groq gpt-oss window 131,072, output cap 65,536 | D.5 | incomplete ("look it up") | P1 | yes (A4 = 2) | core | State the dated numbers; the lab still makes Yash look them up |
| 13 | `max_completion_tokens` replaces `max_tokens`; default 1,024 | B.2, D.5, K, P1-A-04, 06, C5 | **missing** | P1 | no | core | Short: one line plus the renamed parameter in every code sample |
| 14 | Reasoning tokens are output tokens; where `usage` reports them (`completion_tokens_details.reasoning_tokens`) | B.2, J4 | incomplete (no field named) | P1 | partly (P1-B1 = 2) | core | Short: the usage anatomy diagram; the "inside completion_tokens" rule marked to confirm on one recorded response |
| 15 | `reasoning_effort` low/medium/high, Groq default medium; `include_reasoning` | K ("use low") | incomplete | P1 | no | core | Short: why the course pins `low`; Full: effort as a cost/latency knob |
| 16 | `finish_reason` values (`stop`, `length`) and the empty-answer check | J1, D.5 | incomplete (named, values not taught) | P1 / C5 | no | core | Short: "read finish_reason before the text"; the Groq value at the cap is UNVERIFIED until one recorded call |
| 17 | softmax(z/T), greedy at T → 0 | D.6 | yes | P1 | yes (D5b = 3) | core | Keep the toy and add a slider |
| 18 | Groq turns T = 0 into 1e-8; `seed` best effort; batch non-determinism | D.6, J5 | yes | P1 | no (written after day 1) | core | Keep; "replay is the only guarantee" (foundation §2.7) |
| 19 | gpt-oss's own recommendation is T = 1.0, top_p = 1.0, but the course pins T = 0 | K, 06 §3.1 | **missing** (review §3a row 3 never applied) | P1 / M4 | no | core | Full: one "honest limit" box; M4's flip-rate run decides |
| 20 | top_p (nucleus) and top_k | D.6 | incomplete (top_k "unsourced") | P1 | no | core (Full) | Full: top_p from Holtzman 2020; top_k from AIQ 02 Q12 (MIT, quoted with notice) |
| 21 | Claude: no temperature (400), `effort` instead; thinking on by default | not in P1 | **missing** | P1 (D-32) | no | core | Short: a 3-row provider table (Groq / Claude / Cohere) |
| 22 | Claude has its own tokenizer; count with `count_tokens` (free, an estimate, per model; 4.7+ ≈ 30% more) | not in P1 | **missing** | P1 (D-32) | no | core | Short: one paragraph; extends MC-001 to "each provider counts its own way" |
| 23 | No logprobs on Groq, `n` = 1 | not in P1 | missing | P1 | no | core (Full) | Full: why the temperature table must stay a toy; self-consistency needs N separate calls |
| 24 | Cost = in × p_in + out × p_out (per 1M), dated sheet | D.7 | yes | P1 | partly (A6 = 1, F1 = 3) | core | Keep; add the real dated sheet beside the placeholder |
| 25 | Output tokens cost ~4× input (gpt-oss), 5× (Claude); reasoning bills as output | D.7 | **missing** | P1 | no | core | Short: the cost bar chart shows output dominating at the cap |
| 26 | Cached input tokens are cheaper (Groq $0.037) | not in P1 | missing | D2 | no | bridge | Full: one line + link to D2 |
| 27 | Rate limits are in tokens per minute/day; time ≥ tokens / TPM | not in P1 | missing | D2 (foundation §2.5) | no | bridge | Short: one worked line (a 55-question run ≥ 14 min at 8K TPM) |
| 28 | Latency words: TTFT, p50/p95 (Ch22 p.14/19) | not in P1 | missing | D2 | no | next | Link only |
| 29 | Embedding truncation: MiniLM 256 incl. `[CLS]`/`[SEP]` | D.4 | yes (measured) | P4 | no | bridge | Keep short; P4 owns it |
| 30 | The default embedder is Cohere `embed-v4.0` (128k context, server `truncate` default END); its token count needs Cohere's tokenizer | D.4 shows only MiniLM | **missing** | P4 / C3 | no | bridge | One sentence + link; P4 teaches it |
| 31 | Embedding is billed per token, once at index time (Ch2 p.9/11) | G.1 | yes | P1 / C3 | partly | core | Keep |
| 32 | Number of LLM calls is the book's cost unit (one call per chunk/query/document) | G.1 (partly) | incomplete | P1 → I4–I6, X2, V2 | no | core | Short: "calls × tokens per call" as the bridge to later techniques |
| 33 | Long context vs retrieval (Ch1 p.12/14) | G.1 | yes (one line) | P1 / P7 | no | bridge | Teach the idea in one paragraph; no quiz scenario on it (tutor-reserved) |
| 34 | Window filled with noise or duplicates (Ch10 p.2/13, Ch15 p.1/12) | not in P1 | missing | P7 / X3 | no | next | Link only |
| 35 | `chunk_size` means chars, tiktoken tokens, LlamaIndex tokens or regex words | B.1 | yes | P1 / C2 | yes | core | Keep the 4-row table |
| 36 | Replay vs determinism; every call cached | J5 ("cache by input hash") | incomplete | foundation / D2 | no | bridge | Short: one line; the LLMOps notebook shows it |
| 37 | Billed vs counted (estimate is a lower bound) | B.3, J4 | yes | P1 | partly | core | Keep; calibrate from a recorded pilot |

---

### 3. Quiz coverage

No `study/questions/P1_questions.md` exists. Titles below follow FORMAT.md (ids continue the lesson's Part L numbering where items already exist). Every key point must be answerable from **Short**; the "Short?" column says which lesson section must carry it.

**Hidden-seed check.** Done against the coach's seed bank: no title reuses a seed or reserve scenario.

| Id | Set | Title | Short? |
|---|---|---|---|
| P1-PRE-01 | pre | Who decides where text is cut into tokens? | §1 |
| P1-PRE-02 | pre | About how many tokens is 1,000 characters of English prose? | §3 |
| P1-PRE-03 | pre | What does the output cap on an LLM call limit? | §6 |
| P1-R-01 | main | Tokenizer vs embedding model (MC-001 check item; existing) | §1 |
| P1-R-02 | main | Everything that uses a reasoning model's context window (existing) | §5–6 |
| P1-R-03 | main | What a low temperature does to next-token probabilities (existing) | §8 |
| P1-R-04 | main | How many text tokens of a 300-token chunk shape a MiniLM vector (existing; P4 bridge) | §4 |
| P1-R-05 | main | Why the same sentence costs more tokens in Hindi than in English under cl100k | §2–3 |
| P1-R-06 | main | Which `usage` field shows reasoning tokens, and are they billed? | §6 |
| P1-A-01 | main | Tokens in a 2,000-character climate page (existing) | §3 |
| P1-A-02 | main | Cost of 100 queries at 1,000 in / 300 out with placeholder prices (existing) | §9 |
| P1-A-03 | main | Temperature doubles from 1 to 2: p(YES) up or down? (existing) | §8 |
| P1-A-04 | main | The blank-answer bug (existing; rewrite with `max_completion_tokens`) | §6 |
| P1-A-05 | main | Price 100 v0 calls on the dated Groq sheet; what share is output? | §9 |
| P1-A-06 | main | `encoding_for_model(GROQ_MODEL_ID)` raises `KeyError`: why, and the one-line fix | §2 |
| P1-A-07 | main | A 55-question run at about 2,000 tokens each, 8K tokens/minute: shortest possible run time | §10 |
| P1-T-01 | main | Japanese support tickets: what do you measure first? (existing practice item) | §3–4 |
| P1-T-02 | main | Switching the generator from gpt-oss on Groq to Claude Haiku: what changes in your counting, cost and sampling code? | §5, §8, §9 |
| P1-T-03 | review | A dashboard shows completion tokens about 10× the visible answer length: diagnose | §6 |
| P1-R-07 | interview | `source=AIQ-08-Q14`: why reading the text without `finish_reason` is a bug | §6 |
| P1-R-08 | interview | `source=AIQ-02-Q42`: tuning a reasoning-effort setting and what goes wrong | §6–7 |

Notes for the question writer:
- **Interview corrections to show after the repo answer** (our plain version follows the quote): AIQ 02 Q10's example split of "strawberry" does not match `o200k_harmony` (S11: `st|raw|berry` with no space, 1 token after a space); AIQ 02 Q11 says T = 0 is argmax, while Groq documents 1e-8 [P1-4].
- **Max 2 external items** (FORMAT): the two interview items above. AIQ 02 Q21 (BPE vs WordPiece vs SentencePiece) is the alternate.
- Existing Part L items P1-R-01…P1-T-01 must move into the kit file unchanged in meaning, with `max_completion_tokens` in P1-A-04.

---

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Evidence | Suggested fix |
|---|---|---|---|---|
| E1 | 02 P1 card, outcome 3 | "why judges and graders use temperature 0" is now incomplete: current Claude models reject `temperature` (400); gpt-oss's own README recommends T = 1.0; Groq converts 0 to 1e-8 | [P1-4], [P1-9], [P1-16] | "temperature 0 where the API accepts it, otherwise record effort; and state the model's recommended sampling" |
| E2 | 02 P1 card, outcomes | No outcome for the reasoning budget, although the course generator is a reasoning model and the O2 empty answer is P1's own failure | session log 2026-10-08 #2 | Add: "budget `max_completion_tokens` for reasoning + answer and read `finish_reason`" |
| E3 | 04 P1 row | Still carries the three errors recorded in P1 G.2 (CCH cell 11 also caps output and counts with the wrong encoding; `document_augmentation` constants are in cell 4; Ch22 p.14/19 names token cost). Re-confirmed by opening the cells | §1 repo table | Apply the G.2 corrections in the next 04 pass |
| E4 | 03 line 744 (context-window pages) | Misses Ch15 p.1/12 (window stuffed with duplicates) | §1 book table | Add the page |
| E5 | P1 lesson D.5, M.1 card 13 | "o200k_harmony = the encoding tiktoken maps to gpt-oss-20b" is true only for the bare name; the `.env` id `openai/gpt-oss-20b` raises `KeyError` | scratch probe; [P1-6] | Add the trap and `get_encoding("o200k_harmony")` |
| E6 | P1 lesson B.2, D.5, J1, K, P1-A-04; lab Task 8 wording | Uses `max_tokens`; Groq deprecated it for `max_completion_tokens` (same as foundation E3 for 06 and C5) | [P1-2] | Rename in the rewrite |
| E7 | P1 lesson "Still UNVERIFIED" list | Window, output cap and prices of gpt-oss-20b are now documented (131,072 / 65,536 / $0.075 / $0.30, read 2026-10-17). The `finish_reason` value at the cap and the over-window behaviour remain UNVERIFIED | [P1-1] | Move them to a dated "documented" row; keep the lab look-up task |
| E8 | Review §3a row 3 | Never applied: no RK-17 sub-note in 08, no optional Task 8 field in the lab (corrections log round 4: "Not applied … rows 3, 6, 8"). Rows 1 and 2 **were** applied (D.6, J5, M.1 card 14, S11) | 08 line 588; lab cells 34–39 | Apply with the rewrite, as an "honest limit" box (gap #19) |
| E9 | P1 lesson D.6 | "a top-k description is not sourced in this course" can now be resolved: Holtzman 2020 sources top-p; the MIT AIQ 02 Q12 describes top-k | [P1-14] | Cite both (Full) |
| E10 | P1 lesson source map / G.1 | Omits Ch1 p.13/14, Ch10 p.2/13, Ch15 p.1/12, Ch21 p.7/13 and p.11/13, Ch22 p.15/19 (K raises cost; rerank cost), App p.10/23 | §1 book table | Add to G.1 / the new lesson's book box |
| E11 | 06 §7.5 cost row | No cached-input term; does not say output includes reasoning | [P1-5], [P1-1] | Use the foundation §6.1 formula |
| E12 | O2 smoke JSON | Records `prompt_tokens`/`completion_tokens` only, no `reasoning_tokens` or `finish_reason`, so B.3's "19 hidden completion tokens" cannot be split | `progress/O2_smoke_test_2026-10-08.json` | The LLMOps notebook records the full `usage` |

---

### 5. What the research says

**1. Subword tokenizers are learned from text frequency, before the model exists.**
- *The study:* Sennrich et al. 2016 [P1-10] trained BPE on translation data: start from characters, merge the most frequent adjacent pair, repeat. SentencePiece [P1-11] does the same from raw text with no word splitting.
- *The result:* BPE beat a dictionary back-off by 1.1–1.3 BLEU; SentencePiece from raw text matched pre-tokenised input.
- *Limits:* translation results, not LLM results.
- *For the project:* the pieces mirror the training corpus. That is why "Greenland" and " Greenland" differ (S5) and why Hindi costs 62 cl100k tokens but 18 o200k tokens (S3). MC-001 is settled by mechanism, not just by assertion.

**2. Token counts differ a lot across languages, so ÷4 is an English-only habit.**
- *The study:* Petrov et al. 2023 [P1-12] tokenised the same text translated into many languages.
- *The result:* up to 15× more tokens for some languages, even with multilingual tokenizers. tiktoken's README [P1-7] gives about **4 bytes** per token on average, which is where "÷4" comes from; for non-ASCII text, bytes are not characters.
- *Limits:* dataset details not checked.
- *For the project:* keep measuring per corpus. On the climate PDF the ratio is 5.57 (cl100k); on repo Python code it is about 4.6 (scratch probe); on a numbers line 1.49.

**3. The reasoning model spends output tokens before the answer.**
- *The docs:* Groq [P1-2], [P1-3]: gpt-oss effort low/medium/high, default medium; the default completion cap of 1,024 may be too low; reasoning comes back in a `reasoning` field unless `include_reasoning=false`. groq-python [P1-5]: `usage.completion_tokens_details.reasoning_tokens`, and total = prompt + completion.
- *Our evidence:* the O2 call at a 12-token cap returned an empty answer; at 256 it billed 23 completion tokens for a 4-token reply.
- *What it means:* reasoning is output. It counts against the cap, the bill (×4 price) and latency.
- *Honest limit:* that `completion_tokens` includes `reasoning_tokens` is an inference. One recorded response settles it.

**4. Temperature 0 is a request, not a guarantee.**
- Groq converts 0 to 1e-8 and calls `seed` best effort [P1-2], [P1-4]. On GPU servers, batch composition changes results even at T = 0 [P1-20]. gpt-oss recommends T = 1.0 [P1-9]. Current Claude models reject temperature and use effort instead [P1-16].
- *For the project:* keep T = 0 for Groq (06, D-10), never send it to Claude, and rely on **replay** for repeatability (foundation §2.7). M4 measures the flip rate.

**5. Each provider counts its own tokens.**
- Claude's tokenizer is not tiktoken; `count_tokens` is free, rate-limited and an estimate, and newer Claude models use about 30% more tokens for the same text [P1-15]. Cohere's SDK fetches a tokenizer file per model via an API call [P1-18].
- *For the project:* cost estimates for a Claude arm must use `count_tokens` (cached), not o200k counts. The foundation's §6.3 Claude figures reuse Groq-side counts, so they are approximations.

**6. Hidden input tokens come from the chat format.**
- gpt-oss requires the harmony format [P1-8], whose system message carries the knowledge cutoff, current date, reasoning level and channel list.
- *For the project:* this is the most likely source of the ~71 extra prompt tokens in O2 (B.3). It stays UNVERIFIED for Groq's exact rendering. The fix is unchanged: calibrate overhead from recorded `usage`.

**Current practice (2024–2026).** Count with the provider's own tool (tiktoken encoding by name for gpt-oss; `count_tokens` for Claude). Set the completion cap per feature and per effort level. Log `finish_reason`, reasoning tokens and cached tokens on every call. Track length-stop rate as a monitor (AIQ 08 Q14). Use prompt caching (static prefix first) and cheaper models for high-volume steps (`improving-llm-agents`, cost section).

**Pitfalls, with evidence.**
- Empty answer from a reasoning model at a small cap (our O2 run).
- Wrong encoding for the model (CCH cell 11; `encoding_for_model` with a provider prefix).
- Counter crash on special-token text (scratch probe).
- Estimate below the bill: template overhead plus reasoning (B.3).
- Silent embedder truncation (S6).
- Reusing token counts across Claude tokenizer generations [P1-15].

**How to evaluate P1-level choices.** No retrieval metric applies. Answer-side checks are deterministic: empty-answer rate, `finish_reason = length` rate, reasoning share of output (p50/p95), estimate-vs-billed error, cost per query. Keep these "operational" numbers apart from retrieval quality and answer quality (06 §7.5).

**Interview questions to prepare** (AIQ, MIT): 02 Q9 (why subwords), Q10 (strawberry), Q11 (temperature formula), Q21 (BPE vs WordPiece vs SentencePiece), Q23 (tokenisation failure modes), Q42 (reasoning effort); 08 Q6 (why output costs more), Q11 (T = 0 still varies), Q14 (`finish_reason`).

---

### 6. Lesson blueprint

Deliverables: `study/lessons/P1_llm_fundamentals.html` (Short/Full), `study/reading/P1_llm_fundamentals.md` (short reading, FORMAT §3), and the question file. The existing `concepts/P1_llm_fundamentals.md` stays as the Full source and verification log.

**The answer first (draft, 5 sentences).**
1. A model never reads characters: its own tokenizer, fixed before training, cuts text into pieces from a learned vocabulary, and the model sees only their IDs.
2. So every limit and every bill is counted in that model's tokens, and the ratio of characters to tokens depends on the text: about 5.6 on our climate PDF, about 4.6 on Python code, under 1.5 on a line of numbers.
3. One call's input (system rules, hidden template, chunks, question) plus its output (reasoning **and** answer) must fit the context window, and the output cap must leave room for the reasoning, or the answer comes back empty.
4. The model picks each next token from softmax(scores / T); a low temperature makes the top token win more often, but no hosted API promises identical outputs, so the course replays recorded calls instead.
5. Cost per call is input tokens × input price + output tokens × output price, read from a dated price sheet, and output (reasoning included) costs about four times input on Groq.

**The theory in one read (12 linked ideas).**

| # | Idea | Formula / rule |
|---|---|---|
| 1 | Text → pieces → IDs | `ids = tokenizer(text)`, each id < |V| (o200k_harmony 201,088) |
| 2 | BPE learns pieces by frequency | repeat: merge argmax over pairs of count(a, b) |
| 3 | Every model has its own tokenizer | embedder for truncation, generator for prompt budget, provider `usage` for the bill |
| 4 | Chars per token is a measured ratio | r = chars / tokens; tokens ≈ chars / r_corpus; ÷4 ≈ "4 bytes per token" |
| 5 | Special tokens and the chat template | billed_in = counted_text + template_overhead |
| 6 | The window holds input and output | in + out ≤ W (131,072 for gpt-oss on Groq) |
| 7 | The output cap includes reasoning | reasoning + visible ≤ `max_completion_tokens`; empty answer ⇒ `finish_reason` = length |
| 8 | Effort sets the reasoning spend | low < medium (Groq default) < high |
| 9 | Sampling | p_i = exp(z_i/T) / Σ exp(z_j/T); top_p keeps the smallest head with mass ≥ p |
| 10 | Repeatability limits | T = 0 → 1e-8 on Groq; seed best effort; replay = identical |
| 11 | Cost | C = [(in − cached)·p_in + cached·p_cached + out·p_out] / 10⁶ |
| 12 | Rate limits | run time ≥ total tokens / TPM |
| (bridge) | Embedder truncation | tokens past `max_seq_length` (MiniLM 254 text tokens) are dropped silently → P4 |

**Formula sheet items.** r = chars/tokens; the window inequality; the output-cap inequality; softmax(z/T); C per call and C × N; time ≥ tokens/TPM; the 3-row "which tokenizer counts" rule; the provider table (Groq: T accepted, 0→1e-8, effort low–high; Claude: no T, effort low–max, `count_tokens`; Cohere chat: T default 0.3).

**Step-by-step outline (one running example: the climate PDF, Corpus D).** Why this data: P1_FACTS S1–S11 already measure it, and it may be sent to Groq (privacy rule).
1. *The cut.* Window 0 (chars 0–1,000) under o200k_harmony (198), cl100k (201) and MiniLM (186). One sentence as a strip (S5).
2. *Where the pieces come from.* Train a tiny BPE on the climate PDF with `tokenizers` and show its first merges, then the real o200k cut of the same words. (Teaching only; no quiz item.)
3. *The ratio.* Window ratios 4.61–6.37; ÷4 over-counts by 39% on the whole PDF; repo code 4.6; digits in groups of three.
4. *Counting traps.* `encoding_for_model("openai/gpt-oss-20b")` → `KeyError`; `<|endoftext|>` in a document → `ValueError`; the fixes.
5. *Build the v0 prompt.* 107 + 842 + 20 = 976 counted tokens (S9). The harmony template adds hidden tokens (O2: 78 billed vs 7 counted).
6. *Send it (recorded call, replay in the notebook).* Show the `usage` anatomy: `prompt_tokens`, `completion_tokens`, `reasoning_tokens`, `cached_tokens`, `finish_reason`. Repeat at a cap of 64 to show the empty answer.
7. *Sampling.* The toy logits at T = 0.5, 1, 2 (S7); why Groq's T = 0 is 1e-8 and why Claude has no T.
8. *Price it.* At the dated sheet (Groq, read 2026-10-17): one v0 call at the 512 cap ≤ (976 × 0.075 + 512 × 0.30)/10⁶ = $0.000227; 100 calls ≤ **$0.0227**, of which output is 68%. Haiku 5.5 for comparison ≤ $0.0354 per 100 (input count is an o200k proxy; Claude's own count comes from `count_tokens`).
9. *Time it.* 100 calls × ~1,560 tokens ÷ 8,000 TPM ≥ 19.5 minutes (plan of the 30 RPM / 8K TPM row is UNVERIFIED).
10. *Bridge out.* Same chunk, MiniLM cap (P4); the book's "cost = number of LLM calls" tables (App p.10/23) → I4–I6, X2, V2.

All arithmetic in steps 8–9 is DERIVED and must be logged in FACTS before the lesson prints it.

**Visuals (each earns its place).**

| Visual | Type | The one thing it shows |
|---|---|---|
| Token strip | SVG, static | The same sentence cut three ways: the tokenizer cuts, not the embedder (MC-001) |
| Chars-per-token bars | SVG bars with a ÷4 line | The ratio moves with content; ÷4 is wrong in both directions |
| Call budget | Stacked horizontal bar + inset | Input parts, hidden overhead, and the output cap split into reasoning and answer; a second bar at cap 64 shows the answer squeezed to zero |
| Usage anatomy | Annotated JSON block | Which field holds what, and which ones you are billed for |
| Temperature slider | Interactive SVG bars | Smaller T sharpens the same scores (toy logits, labelled "toy") |
| Cost bars | SVG bars per model, split in/out | Output dominates at the cap; dated prices in the caption |

**Full-only details.** WordPiece score and Unigram pruning; SentencePiece `▁`; byte-level fallback and why Hindi is cheap in o200k; the harmony format and the 1,091 special tokens; top_p and top_k; logprobs unavailable on Groq; `n` = 1 and self-consistency cost; the batch-invariance study; prompt caching price; Claude tokenizer generations; the repo unit table and CCH cell 11 reading guide (H.2); the honest-limit box on T = 0 vs gpt-oss's recommended T = 1.0.

---

### 7. Verify notebook plan

`study/notebooks/P1_tokens_verify.ipynb`, same shape as P3's (setup cell with a `check(label, got, expected)` helper; one section per lesson section with "What this verifies").

| Section | Recomputes | Data and code | Chart (Plotly) |
|---|---|---|---|
| 1 Cut | S5 pieces (12 / 13 / 16) and S11 strawberry | tiktoken, MiniLM tokenizer | token strip as a table |
| 2 BPE origin | First 10 merges of a tiny BPE (vocab 400) trained on the climate PDF; how "greenhouse" and "deglaciation" split under it vs o200k | `tokenizers` BpeTrainer, offline | — |
| 3 Ratios | S3, S4 (91 windows), plus new: repo code ratio, digit grouping | pymupdf 1.26.7, tiktoken, MiniLM | box/strip plot of 91 window ratios per tokenizer; bars by content type with ÷4 line |
| 4 Traps | New S-ids: `encoding_for_model` KeyError on the `.env`-style id; `ValueError` on special-token text; the fixed counter | tiktoken | — |
| 5 Truncation (bridge) | S6 (256 IDs, cosine 1.000000) | MiniLM from cache, `HF_HUB_OFFLINE=1` | — |
| 6 Budget | S9 (976), S10; the window inequality at 131,072 | 06 §3.3 template | stacked budget bar |
| 7 Usage anatomy (replay) | Reads the P1 LLMOps calls from the cache **if present**: reasoning share, `finish_reason`, billed − counted overhead. Skips with a clear message if the pack is missing | `llmops.cache` in `replay` mode | scatter: cap vs visible / reasoning tokens |
| 8 Temperature | S7 table, entropy | numpy | slider over T |
| 9 Cost and time | Dated-sheet arithmetic (steps 8–9) from `study/llmops/prices.json` | `llmops.cost` | cost bars per model, split in/out |

- **API calls:** none. Section 7 only reads recorded responses (replay mode); it never records.
- **Offline:** yes, given the HF cache for MiniLM and tiktoken's cached encodings.
- **Runtime:** under 1 minute on CPU (MiniLM load ~10 s; BPE training on 72,593 chars < 5 s; estimate).
- **New S-ids** to append to P1_FACTS: S12 encoding-name trap, S13 special-token trap, S14 code ratio and digit grouping, S15 dated cost and time arithmetic, S16 recorded-usage facts (from the LLMOps pack).

---

### 8. Apply-it tool plan and real-world checklist

`study/tools/token_budget_check.py` (CLI + importable, like `bm25_fit_check.py`). **Question it answers:** "With my documents, my chunk size and my model choices, does each call fit, what will it cost, and how long will a run take?"

**Inputs.** `--docs` (PDF/TXT/MD; pages joined with "\n" as in P3), `--chunk-size` and `--overlap` with an explicit `--unit chars|tokens`, `--k`, `--questions` (optional), `--generator groq:openai/gpt-oss-20b` or `anthropic:claude-haiku-5-5`, `--max-completion-tokens`, `--effort`, `--embedder minilm|cohere`, `--prices study/llmops/prices.json`, `--tpm`, `--traces results.jsonl` (optional, recorded usage), `--pilot N` (optional, recorded calls).

**Output.** A Markdown report: (1) corpus ratios per tokenizer; (2) content mix (digits, code-like lines, non-Latin share); (3) chunk token distribution and embedder truncation rate; (4) prompt budget per question and window fit; (5) output-cap check against recorded reasoning share; (6) cost per query and per N, split in/out, with the price-sheet date; (7) run time from TPM; (8) checklist with ✓/✗/? and evidence; (9) recommendation.

**External calls.** None by default. `--pilot N` makes N Groq calls (default 5, ≈ $0.001) to calibrate overhead and reasoning share; `--claude-count` makes free `count_tokens` calls; `--embedder cohere` fetches the Cohere tokenizer (1 `models.get` + 1 file download, stored under `.cache/tokenizers/`, git-ignored). All go through `llmops.cache`, so a re-run is pure replay.

**Real-world checklist (12).**

| # | Check | Auto / manual |
|---|---|---|
| C1 | The generator's tokenizer was resolved by encoding name (no provider-prefix `KeyError`) | auto |
| C2 | Measured chars/token for your corpus vs ÷4; flag an error above 20% | auto |
| C3 | Costly content share: digits, code, non-Latin script | auto |
| C4 | Special-token strings present in your documents (would crash a default counter) | auto |
| C5 | Embedder truncation rate (MiniLM: chunks over 254 text tokens; Cohere: check the `truncate` setting) | auto (MiniLM); manual for Cohere without `--embedder cohere` |
| C6 | Input + output cap fits the window with a margin | auto |
| C7 | Output cap leaves room for reasoning (p95 reasoning share from traces or the pilot) | auto with traces; else manual: run `--pilot 5` |
| C8 | `finish_reason = length` and empty-answer rates in recorded traces are 0 | auto with traces |
| C9 | Billed vs counted overhead calibrated from recorded `usage` | auto with traces/pilot; else manual |
| C10 | Price sheet dated within 30 days | auto (`price_table_version`) |
| C11 | Planned run fits the daily token quota and its minimum time is acceptable | auto |
| C12 | Sampling parameters are accepted by the provider (no `temperature` sent to current Claude models; effort sent explicitly) | auto from flags |

**Recommendation logic (first match wins).**
1. C4 or C1 fails → "fix the counter first" (numbers below are unreliable).
2. C6 fails → "reduce k or chunk size, or raise nothing: the call cannot fit".
3. C7 or C8 fails → "raise `max_completion_tokens` or lower effort".
4. C5 > 5% → "chunks are being truncated: shrink chunks or switch embedder (see P4)".
5. C2 error > 20% → "size chunks in tokens, not characters".
6. C11 fails → "split the run or lower volume; check the daily quota".
7. Otherwise → "budget OK", with cost per 100 queries and run time.

---

### 9. LLMOps notebook plan

`study/notebooks/P1_llmops.ipynb`: **"Token accounting and the reasoning budget, as production runs it."** It applies foundation §2–§8 and the §12 row for P1 (Groq a few prompts, Claude optional, `CachedChatModel`, trace tokens incl. reasoning and `finish_reason`, toy checks, cost per call, reasoning share, prompt files, replay test). It adds only what P1 needs.

**External calls (all through `study/llmops/`; the notebook runs fully in `replay` once recorded).**

| Call | Provider / model | Count | Upper-bound tokens | Upper-bound cost |
|---|---|---|---|---|
| Cap × effort sweep: 3 v0 prompts (seed items on Corpus D) × caps {64, 256, 1024} × effort {low, medium}, T = 0 | Groq `openai/gpt-oss-20b` | 18 | ~27,000 | ≈ $0.004 |
| Variance samples: 1 prompt, `record` samples 0–2 at T = 0 and 0–2 at T = 1.0 | Groq | 6 | ~9,400 | ≈ $0.0014 |
| Optional Claude arm: `count_tokens` on the 3 prompts | Anthropic | 3 | — | $0 (free, rate-limited) |
| Optional Claude arm: same 3 prompts, effort `low`, `max_tokens` 1024 | `claude-haiku-5-5` | 3 | ~6,400 | ≈ $0.0019 |
| **Total** | | 24 Groq (+6 Claude) | ~36,000 Groq | **≈ $0.005 Groq, + $0.002 Claude** |

- Groq time: ≥ 4.5 minutes at 8K TPM; about 18% of a 200K daily quota (plan row UNVERIFIED). The planner refuses the run if the quota is short.
- Prompts are corpus D only, guarded by `privacy.assert_corpus_is("D")`.
- Replay: CI runs it with `LLMOPS_CACHE_MODE=replay`; `replay_manifest.json` lists its 24 (+6) keys.

**Framework build (pieces mapped to the mechanism).**

| Lesson step | Framework piece | Default the lesson warns about |
|---|---|---|
| Prompt from a template file | `prompts/answer_v1.txt` loaded into `ChatPromptTemplate` (langchain-core) | Template whitespace changes the prompt hash and the cache key |
| The call | `llmops.lc.CachedChatModel(provider="groq", model=…, params={temperature, max_completion_tokens, reasoning_effort})` | `ChatGroq` (read-only cell): `temperature=0.7`, `max_retries=2`, `reasoning_effort=None` → server medium (foundation §9.2); `langchain-groq` conflicts with groq 1.7.0 |
| Usage | `AIMessage.usage_metadata` (`output_token_details.reasoning`, `input_token_details.cache_read`) [P1-19] | The adapter must fill these from Groq's `completion_tokens_details` / `prompt_tokens_details`; a missing field silently reads as 0 |
| Claude arm | `CachedChatModel(provider="anthropic", model="claude-haiku-5-5", params={effort: "low", max_tokens: 1024})` | Sending `temperature` → 400; `ChatAnthropic` fills `max_tokens` from a profile |
| No LangGraph | The flow is linear (foundation §9.1 rule) | — |

**Tracing.** Every call writes a §3.3 LLM span to JSONL: provider, model requested and returned, `system_fingerprint`, all sent parameters, prompt sha256, input / output / reasoning / cached tokens, `finish_reason`, latency and Groq `queue_time`, cost, `cache_hit`, `cache_key`. Local viewer: Phoenix via `uvx` (OpenInference export). Hosted: LangSmith inside `tracing_context(enabled=True)` after the corpus-D guard (foundation §3.2). Reasoning text is stored locally only; exported spans keep counts, not reasoning text.

**Dataset and evaluators.** A 3-item toy dataset (the three corpus-D prompts; mirrored to LangSmith with `upload_results=False` by default). Code evaluators only (D-10: no judge):
- `nonempty_answer` (pass if visible text after strip is non-empty);
- `finish_ok` (`finish_reason` = stop);
- `reasoning_share` (reasoning / completion tokens, reported, no threshold);
- `estimate_error` (billed prompt tokens − counted tokens);
- `budget_fit` (in + cap ≤ window);
- `cost_per_call` from `prices.json`.
Retrieval metrics are not involved; answer quality is not judged here (it starts in C5/M3).

**Experiment against the previous version.** The 06 cards have no P1 version. The comparison is v0's configuration (cap 512, effort low) against the sweep arms, reported as: empty-answer rate, length-stop rate, reasoning share p50/p95, visible tokens, latency p50/p95, cost per call. The result informs v0's `max_completion_tokens` (C5 / 06 §2.4) and is written as a pre-registered note, not a version change.

**Cost, latency and token tracking.** "Cost if called" and "cost paid" (0 on replay) per arm; tokens split input / cached / reasoning / visible; p50/p95 latency excluding cache hits, method named (nearest-rank).

**Prompt and config versioning.** The prompt is `prompts/answer_v1.txt` (unchanged); the sweep config is one YAML hashed into `config_hash`; the resolved model id is written, not the `.env` name.

**Monitoring and feedback.** Adds two monitor-page series: length-stop rate and reasoning share per day, with thresholds in `monitor.yaml` (length-stop > 5%; reasoning share p95 > 0.8 of the cap). A breach goes to the error-analysis log and becomes a T1 or T2 regression item (`ci-cd-evals`, `error-analysis`).

**Place in the lifecycle.** Analyze: read the sweep traces (`llm-observability`, `trace-data-analysis`). Measure: the code evaluators above (`code-based-evaluators`). Improve: choose cap and effort (`improving-llm-agents`, cost section). dev → CI: the `replay` marker test. Monitoring: the two series above (`ci-cd-evals`). Frame: `evals-foundations` (a blank answer at a small cap is a specification failure in our call, not a model failure).

---

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| gpt-oss / OpenAI-family tokenizers | `tiktoken` | 0.14.0 | yes | yes (encodings cached) | none | MIT | yes |
| BPE training demo, MiniLM tokenizer | `tokenizers` | 0.23.2 | yes | yes | none | Apache-2.0 | yes |
| MiniLM (truncation bridge) | `sentence-transformers` / `transformers` | 6.1.0 / 5.19.0 | yes | yes (HF cache) | none | Apache-2.0 | yes |
| PDF text | `pymupdf` | 1.26.7 (pinned) | yes | yes | none | AGPL-3.0 | yes |
| Charts | `plotly` | 7.1.0 | yes | yes | none | MIT | yes |
| Generator (default) | Groq `openai/gpt-oss-20b` via `groq` 1.7.0 | model id from `.env` | yes | no | 24 calls ≈ $0.005 per notebook record | Apache-2.0 (SDK) | yes |
| Generator comparison (optional) | Claude Haiku 5.5 `claude-haiku-5-5` via `anthropic` | 1.11.0 (foundation pin) | no | no | 3 calls ≈ $0.002 + 3 free `count_tokens` | MIT (SDK) | yes (D-32), only when credits exist. Haiku because P1 needs volume, not quality |
| Claude token counts | `count_tokens` endpoint | — | n/a | no | free, rate-limited; cached | — | yes |
| Cohere embed token counts (optional, apply tool) | `cohere` `tokenize(offline=True)` | 7.2.0 | yes | after one download | 1 `models.get` + 1 file | MIT | yes; `tokenizer_url` for embed-v4.0 UNVERIFIED |
| Harmony prompt rendering (optional, Full: explain hidden tokens) | `openai-harmony` | 0.0.8 | no | UNVERIFIED (may fetch the vocabulary once) | none | Apache-2.0 per GitHub, UNVERIFIED | yes; optional |
| Framework core | `langchain-core` | 1.6.6 | no | yes | none | MIT | yes (LLMOps notebook only) |
| Graphs | `langgraph` | 1.2.12 | no | yes | none | MIT | **not needed for P1** (linear flow) |
| Groq via LangChain | `langchain-groq` | 1.1.3 | no | — | — | MIT | **no**: needs groq < 1.0; use the adapter |
| Claude via LangChain | `langchain-anthropic` | 1.7.5 | no | no | as `anthropic` | MIT | optional; adapter preferred |
| Hosted tracing | `langsmith` | 0.14.4 | no | SDK yes | free plan; corpus D only | MIT | yes |
| Local tracing | JSONL (default) + `arize-phoenix-otel` 0.17.2 + `openinference-instrumentation-langchain` 0.1.78; server `uvx arize-phoenix@20.19.0 serve` | as listed | no | yes | none | Apache-2.0 / ELv2 (server) | yes |
| Headless replay test | `nbclient` | 0.11.0 | no | yes | none | BSD-3 | yes; **missing from the foundation's install list** |
| Shared cache / trace / cost | `study/llmops/` | plan (foundation §10) | not built | yes | — | ours | yes; **blocks the LLMOps notebook** |

Install lines (do not run until the build):

```text
uv add --group llmops langchain-core==1.6.6 langsmith==0.14.4
uv add --group llmops arize-phoenix-otel==0.17.2 openinference-instrumentation-langchain==0.1.78
uv add --group llmops anthropic==1.11.0                 # only when Claude credits exist
uv add --group dev nbclient==0.11.0                      # headless replay test
uv add --group optional openai-harmony==0.0.8            # Full-only harmony demo; skip if declined
uvx arize-phoenix@20.19.0 serve                          # on demand, outside the lock
```

**Keys.** `GROQ_API_KEY` (present), `ANTHROPIC_API_KEY` and `LANGSMITH_API_KEY` (key names present in `.env`; values not read), `COHERE_API_KEY` (present; only for the optional Cohere tokenizer). Never set `LANGSMITH_TRACING` in `.env`.

---

### 11. Open questions for Yash (preferences only)

1. Record the optional **Claude Haiku arm** in the P1 LLMOps notebook when you have credits (about $0.002)? **yes / no**
2. For the non-English example in the lesson, keep **Hindi** (already measured) or switch to **Gujarati**?
3. Interview items: **Q14 + Q42** (finish_reason, reasoning effort; recommended) or **Q14 + Q21** (tokenizer families)?
4. Include the optional **harmony rendering demo** (adds `openai-harmony`, Full only)? **yes / no**

---

## Concept P2: Information-retrieval framing

**The short version.**
- P2 already has a full lesson (`concepts/P2_ir_framing.md`), a lab and a FACTS file, all written 2026-10-08 before the house style. The content is mostly sound. It needs a rewrite into the P3-style HTML lesson, plus **four missing ideas**: incomplete judgments (unjudged = not relevant), pooling bias, ties in a ranking, and the several meanings of the word "relevance".
- P2 has **no LLM and no external call**. Its LLMOps notebook traces retrieval runs, versions the qrels, and adds a metric-parity regression test.
- Build size: **M** (rewrite + new verify notebook + new apply-it tool + question file + small LLMOps notebook).

---

### 1. Sources checked

**Book pages (opened and read with PyMuPDF 1.26.7; extracts in `scratchpad/phase01/book_P2/`).**

| Page | What it gives P2 (paraphrased) | Verified |
|---|---|---|
| Ch3 p.1/14 | Similarity search returns the closest chunks; "closest" is not always "relevant". Example: a footer full of navigation links scores well and helps nothing. | yes |
| Ch13 p.1/13, p.2/13 | Three "capital of France" chunks sit closest to the query, yet none names Paris; the fourth, farther away, holds the answer. Similarity is called a rough proxy for relevance, inside one retriever. | yes |
| Ch13 p.5/13 | Rerank pipelines fetch 10–30 candidates so a relevant chunk gets into the candidate set. | yes |
| Ch13 p.9/13 | Cross-encoders are trained on query–document pairs labelled relevant or not. A cross-encoder fixes the definition of relevance it was trained with; an unusual definition (for example, recency) needs fine-tuning. | yes |
| Ch1 p.8/14 | Query phase: embed the query, take the 2–5 nearest chunks, treat them as most likely to contain the answer. The worked query is **"What is the main cause of climate change?"** on a climate report, and the book simply asserts the retrieved chunks are relevant. | yes |
| Ch1 p.9/14 | Generation step and pipeline diagram. **Not** about top-K (see §4, E5). | yes |
| Ch1 p.10/14, p.12/14 | "top-K nearest" in the algorithm sketch; 2–3 chunks miss scattered material; RAG is overkill if keyword search is enough. | yes |
| Ch12 p.2/14, p.3/14, p.5/14, p.6/14 | The back-of-cookbook index (an inverted index, unnamed); BM25 works on words only. | yes |
| Ch22 p.4/19 | "Context relevance": an LLM scores each retrieved chunk relevant or not. Precision at K (3 of 5 relevant = 0.6). The triad caption also uses "relevance" for query → answer. | yes |
| Ch22 p.5/19 | Recall at K = share of **all relevant documents in the knowledge base** retrieved (3 of 10 = 0.3). Context precision accounts for order. | yes |
| Ch22 p.6/19, p.7/19 | Precision and recall say what was retrieved, not how well it was ranked; MRR, MAP, NDCG; graded relevance; same documents, different ranking quality. | yes |
| Ch22 p.12/19 | An evaluation dataset = queries, each with expected relevant documents and a reference answer. Synthetic drafts are promoted to a golden set after expert review. | yes |
| App p.9/23 | The only "relevance judg…" hit in the book: reranking handles nuanced relevance judgments (scientific queries). | yes |
| App p.19/23, p.20/23, p.22/23 | Glossary: MRR, NDCG, Precision at K, Recall at K, Relevancy Grading (an LLM filter), Top-K Retrieval (K chunks with the highest **similarity** scores). | yes |
| Intro p.1/8 | Motivation: passages that are almost but not quite relevant. | yes |

**Whole-book search** (all 25 PDFs, case-insensitive): `inverted` 0 pages · `qrel` 0 · `information retrieval` 0 · `boolean` 0 · `postings` 0 · `relevance` 66 pages (120 hits) · `relevant` 110 pages · `query` 210 pages · `top-k` 28 pages · `judg` 14 pages. **Conclusion:** the book has no inverted index and no Boolean retrieval, but it has plenty of relevance and evaluation framing (Ch22). The 02 card's "no IR framing" is too strong (§4, E2).

**Repo (`upstream/RAG_Techniques` @ `009adba2…`, cells 0-based).**

| Cell | What it shows | Verified |
|---|---|---|
| `all_rag_techniques/simple_rag.ipynb` 13 | `as_retriever(search_kwargs={"k": 2})`: the run is cut to a set of 2 | yes (FACTS S-src; P2 lesson G.2) |
| `all_rag_techniques/fusion_retrieval.ipynb` 14, 17 | `BM25Okapi` called an index; cell 17 scores every document, then cuts | yes (FACTS S-src) |
| `all_rag_techniques/reliable_rag.ipynb` 14 | Lenient binary LLM grader: keywords **or** meaning related = relevant | yes (FACTS S-src) |
| `evaluation/define_evaluation_metrics.ipynb` 3, 9 | Ground truth is an **answer**; 0/0.33/0.66/1.0 LLM rubric averaged; undefined prompt name | yes (FACTS S-src) |
| `evaluation/evaluation_deep_eval.ipynb` 6, 11 | `ContextualRelevancyMetric`: relevance judged by an LLM at eval time | yes (FACTS S-src) |
| **`evaluation/open-rag-eval-example.ipynb` 0, 4, 5, 7** | **New find.** Cell 0: BEIR's fiqa dataset. Cells 4–5: a `TRECEvaluator` ("TREC RAG Evaluator") with an LLM judge (gpt-4o-mini, OpenAI). Cell 7: the **UMBRELA** metric, a graded passage-relevance scale NO_RELEVANCE 0, RELATED 1, PARTIAL_ANSWER 2, EXACT_ANSWER 3. This is IR framing in the repo. | yes (opened 2026-10-17) |
| `all_rag_techniques/Agentic_RAG.ipynb` 38 (markdown) | A vendor claim about a reranker on "the industry-standard BEIR benchmark" | yes (mention only) |
| Repo-wide grep `inverted|qrel|relevance judg|pytrec|ir_datasets|ranx|trec|cranfield|beir` | `inverted`, `qrel`, `pytrec`, `ranx`, `cranfield`: no real hits (the case-insensitive hits in `graph_rag`, `colpali`, `relevant_segment_extraction`, `Agentic_RAG` line 598 are inside base64 image outputs). TREC/BEIR: only the cells above. | yes |

**Existing course files read:** CLAUDE.md; RESEARCH_PROMPT.md; LLMOPS_FOUNDATION.md (all, esp. §2, §3, §4, §5, §9, §10, §11, §12); `study/lessons/P3_bm25_gap_audit.md`; `study/lessons/P3_bm25.html` (sections index, score, bridge, measure); `study/notebooks/P3_bm25_verify.ipynb` (structure); `study/tools/bm25_fit_check.py` (docstring/CLI); `study/FORMAT.md`; both WRITING_STYLE files, `visual-learning-writer/SKILL.md`, `HTML_VISUAL_SPEC.md`; 02 P2 card (lines 181–198) and Gate 1→2 (line 1121); 03 rows for P2; 04 P2 row (line 123); 06 §6.1–6.7, §7.1–7.3; 08 Part 4 (D-08, D-09, D-10, D-18, D-24, D-31, D-32); `01_SOURCE_INVENTORY.md` §6 rows 7–10; `concepts/P2_ir_framing.md` (all 745 lines); `concepts/P6_ir_metrics.md` D.1–D.2 and P2 references; `labs/P2_ir_framing_lab.ipynb` (41 cells, structure and Tasks 4, 6, 8); `sources/verification/P2/` (P2_FACTS.md, out_p2_sources.txt); `progress/concept_tracker.csv` (P2 = not_started; P6 reinforcement flag 1 from O1-Q04); `progress/misconception_log.md` (MC-001…MC-006); `sources/EXTERNAL_RESOURCES_REVIEW_2026-10-09.md` (no P2 rows; P6 and M1–M3 rows checked for overlap); `sources/coach/transfer_seed_bank.md` (titles only: no P2 seed exists; see §3).

**AI Eval book (paraphrased; never quoted).**
- AE Ch2, 'Retrieval': two retrieval families, keyword overlap (BM25) and embedding similarity; the usual pipeline is search, then put the hits in the prompt.
- AE Ch2, 'Retrieval Fundamentals': start with keyword search as an interpretable baseline (its toy is tutor-reserved and not used here).
- AE Ch7, 'Overview': because the reader of the context is an LLM that can take many passages, the first retrieval stage should favour **recall**; a second stage (reranker) favours precision; evaluate each stage on its own, and retrieval before generation.
- AE Ch7, 'Metrics for Retrieval Quality' / 'Precision@k and Recall@k': metrics need a dataset of queries with their relevant chunks; k can depend on the question type. (P6 owns the metrics.)

**Interview repo (MIT, `ombharatiya/AI-Engineer-Interview-Questions` @ `e080df2`, "Copyright (c) 2026 Om").**
- `04-rag-and-retrieval/questions.md` Q45, "How do you build a golden evaluation set for RAG without months of labelling?" Its answer covers labelling from a generous candidate pool, the **incomplete-labels problem**, re-adjudication, and spans over chunk ids. Best P2 interview item.
- `04-rag-and-retrieval/questions.md` Q43 follow-up: "How do these metrics mislead when your golden set has incomplete relevance labels?" (Q43 itself belongs to P6.)
- `07-evaluation-and-observability/questions.md` Q22 (components vs end-to-end; M2 uses it), Q30 (inter-annotator agreement; M3 uses it). Link only.

**External sources (all opened 2026-10-17; external material, not in the book or repo).**

| # | Source | Status |
|---|---|---|
| [P2-1] | Manning, Raghavan, Schütze, *Introduction to Information Retrieval* (CUP 2008), §1.1 "An example information retrieval problem" — https://nlp.stanford.edu/IR-book/html/htmledition/an-example-information-retrieval-problem-1.html | verified |
| [P2-2] | IIR §1.2 "A first take at building an inverted index" — https://nlp.stanford.edu/IR-book/html/htmledition/a-first-take-at-building-an-inverted-index-1.html | verified |
| [P2-3] | IIR §1.3 "Processing Boolean queries" — https://nlp.stanford.edu/IR-book/html/htmledition/processing-boolean-queries-1.html | verified |
| [P2-4] | IIR §1.4 "The extended Boolean model versus ranked retrieval" — https://nlp.stanford.edu/IR-book/html/htmledition/the-extended-boolean-model-versus-ranked-retrieval-1.html | verified |
| [P2-5] | IIR §8.1 "Information retrieval system evaluation" — https://nlp.stanford.edu/IR-book/html/htmledition/information-retrieval-system-evaluation-1.html | verified |
| [P2-6] | IIR §8.3 "Evaluation of unranked retrieval sets" — https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-unranked-retrieval-sets-1.html | verified |
| [P2-7] | IIR §8.4 "Evaluation of ranked retrieval results" — https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html | verified |
| [P2-8] | IIR §8.5 "Assessing relevance" (pooling, kappa) — https://nlp.stanford.edu/IR-book/html/htmledition/assessing-relevance-1.html | verified |
| [P2-9] | IIR §8.5.1 "Critiques and justifications of the concept of relevance" — https://nlp.stanford.edu/IR-book/html/htmledition/critiques-and-justifications-of-the-concept-of-relevance-1.html | verified |
| [P2-10] | E. M. Voorhees, "The Philosophy of Information Retrieval Evaluation", CLEF 2001 workshop / Springer LNCS 2406 (2002) — https://www.nist.gov/publications/philosophy-information-retrieval-evaluation-0 | **abstract verified; full text UNVERIFIED** (both NIST PDFs and the ERCIM copy were font-encoded or image-only and could not be read). Cite only for "the Cranfield paradigm and its assumptions" |
| [P2-11] | C. Buckley, E. M. Voorhees, "Retrieval Evaluation with Incomplete Information", SIGIR 2004 — https://www.nist.gov/node/761376 | abstract verified (ACM DL returned 403) |
| [P2-12] | T. Saracevic, "Relevance: A review of the literature and a framework for thinking on the notion in information science. Part II: nature and manifestations of relevance", JASIST 58(13):1915–1933, 2007 — https://tefkos.rutgers-sci.domains/Saracevic%20relevance%20pt%20II%20JASIST%20%2707.pdf | full text verified (manifestations list, p.1929–1930 area) |
| [P2-13] | N. Thakur, N. Reimers, A. Rücklé, A. Srivastava, I. Gurevych, "BEIR: A Heterogenous Benchmark for Zero-shot Evaluation of Information Retrieval Models", NeurIPS 2021 Datasets & Benchmarks — https://arxiv.org/abs/2104.08663 (PDF text read) | full text verified (§3.3 metric choice; §6 annotation bias, Table 4) |
| [P2-14] | P. Thomas, S. Spielman, N. Craswell, B. Mitra, "Large language models can accurately predict searcher preferences", arXiv 2309.10621 (2023, rev. 2024) — https://arxiv.org/abs/2309.10621 | abstract verified |
| [P2-15] | S. Upadhyay, R. Pradeep, N. Thakur, N. Craswell, J. Lin, "UMBRELA: UMbrela is the (Open-Source Reproduction of the) Bing RELevance Assessor", arXiv 2406.06519 (2024) — https://arxiv.org/abs/2406.06519 | abstract verified; no numbers on the abstract page |
| [P2-16] | NIST TREC, qrels format page — https://trec.nist.gov/data/qrels_eng/ | verified |
| [P2-17] | `usnistgov/trec_eval` README — https://github.com/usnistgov/trec_eval | verified (format names only; no column spec on the README) |
| [P2-18] | G. Cabanac, G. Hubert, M. Boughanem, C. Chrisment, "Tie-breaking Bias: Effect of an Uncontrolled Parameter on Information Retrieval Evaluation", CLEF 2010, LNCS 6360 pp.112–123 — http://www.irit.fr/~Guillaume.Cabanac/tie-breaking-bias/ | project page verified; paper not opened |
| [P2-19] | `ir-measures` documentation — https://ir-measur.es/en/latest/ | verified |
| [P2-20] | `pytrec_eval` README — https://github.com/cvangysel/pytrec_eval | verified |
| [P2-21] | PyPI JSON API for `ir-measures`, `ranx`, `pytrec-eval-terrier`, `ir-datasets`, `bm25s`, `pyserini`, `rank-bm25` — `https://pypi.org/pypi/<name>/json` | verified 2026-10-17 |
| [P2-22] | LangChain `BaseRetriever` reference — https://reference.langchain.com/python/langchain-core/retrievers/BaseRetriever | verified (override `_get_relevant_documents`; scores are not covered there) |

---

### 2. Gap audit

Studied status comes from `progress/concept_tracker.csv`: **every Phase 1 concept is `not_started`**; only O1 and O2 are `exposed`. "Written" is not "studied". O1-Q04 (precision@k, recall@k, reciprocal rank) scored 0.

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class (core / bridge / next) | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Collection, document (= chunk in RAG), information need, query; a need is not the query (one query, two needs) | Every P2 item; 06 §6.1 | **Incomplete**: old D.1 defines them in a table; no example where one query hides two needs ([P2-1], [P2-5]: the "python" example) | P2 | no | core | Short §1: the toy q1 plus one ambiguous query from the climate corpus written by us. Teach "judge against the need, not the words" |
| 2 | Retriever = a scoring function s(q, d), sort, cut at k; one score per (query, chunk) pair (MC-002) | P3, P4, P5, C4 | yes (old D.1) | P2 | no | core | Short. Keep the MC-002 line ("no all-pairs matrix") |
| 3 | Similarity vs relevance; similarity is the system's proxy | Ch3 p.1, Ch13 p.1–2; P3 §11; V2 | yes (old D.2, measured S5–S6) | P2 | no | core | Short, first section after the answer. Use the book's own query (Ch1 p.8/14) |
| 4 | **The word "relevance" has several meanings**: system relevance (the score), topical (about the topic), situational/utility (helps answer). In RAG: context relevance (Ch22 p.4), answer relevance (Ch22 p.4 caption), Relevancy Grading (App p.20), UMBRELA grades (repo) | Ch22, Ch3, App; M3, V2 | **missing** | P2 | no | core | Short: a 3-row table (score / topic / helps answer) and "our qrels label the third". Full: Saracevic's five manifestations [P2-12] |
| 5 | Relevance judgments, qrels line `(qid, doc, grade)`, unlisted = 0, binary rule grade ≥ 1 | P6, M1, M2 | yes (old D.3) | P2 | no | core | Short. Show the TREC qrels line format [P2-16] in Full |
| 6 | Labelling guideline: grades 2/1/0, write a reason, judge before seeing any run, disagreement is data | Lab Task 5; M1 | yes (old D.3 rules 1–4) | P2 | no | core | Short. Add "the guideline gets a version number" |
| 7 | **Incomplete judgments: unjudged = treated as not relevant** (TREC convention [P2-16]); recall needs the number of all relevant docs [P2-6]; Buckley & Voorhees [P2-11] | P6 D.2 (recall denominator), P6 J4, M2 | **missing** (P6 says "0 or missing = not relevant" without the consequence) | P2 | no | core | Short: one worked case on the toy (a pool built only from keyword hits). This is the root of AIQ 04 Q45 and Q43's follow-up |
| 8 | **Pooling and pool bias**; Hole@k / Judged@k | M1 gold building; R1 (BM25 vs dense comparisons) | **missing** (old D.3 calls pooling UNVERIFIED) | P2 | no | core | Short: one sentence + the toy demo. Full: BEIR Table 4 [P2-13], IIR §8.5 [P2-8] |
| 9 | Labels are noisy: agreement, κ = (P(A) − P(E)) / (1 − P(E)) | 06 §6.5 self-agreement; M3 | **incomplete** (old lesson links 06 §6.5 only) | M3 / M1 (`collaborative-annotation`) | no | bridge | Short: one sentence ("two careful judges agree only fairly well"). Full: formula + IIR Table 8.2 worked example (κ ≈ 0.776; recomputed 0.7759 pooled, 0.7761 Cohen) |
| 10 | Label unit: spans, not chunk ids; chunk relevance derived by overlap (06 §7.2 `any_overlap`); one span can make 2 overlapping windows relevant | M1, M2, C2, P6 | **incomplete** (old D.3 rule 5 states it; no worked derivation) | M1 | no | bridge | Short: one derived example on the real PDF (seed D-004 → windows 22 and 63; D-002 → windows 25 and 26; scratch numbers, §6) |
| 11 | Term–document incidence matrix → inverted index: dictionary, postings, df = postings length | P3 §3, P3 df/idf | yes (old D.4; P3 §3 as a bridge) | P2 | no | core | Short. Add the incidence matrix as the "why invert" picture [P2-1] (P3 does not show it) |
| 12 | Tokenization for the index (lower-case, runs of a–z0–9); index token ≠ LLM token (MC-001) | Lab Task 1; P3 §9 | yes (old D.4 step 1) | P3 (tokenizer), P1 (LLM tokens) | no | bridge | Short: one line + the MC-001 note, link P3 §9 |
| 13 | Boolean AND = intersection, OR = union; postings read as the cost; AND too strict, OR too loose [P2-4] | Lab Task 3 | yes (old D.4) | P2 | no | core | Short. Full: linear merge O(x + y) and "smallest df first" [P2-3] |
| 14 | Ranked retrieval from postings: add a weight per hit; only documents in ∪ postings can score > 0 (candidate cap) | Lab Task 4, 7; P3 | yes (old D.4, D.5) | P2 | no | core | Short |
| 15 | **Ties in a ranking**: equal scores need a tie rule, and the rule can change a metric (toy q4: d06 and d09 both score 1; trec_eval re-sorts by score and breaks ties by doc id [P2-18]) | Lab Task 4 (rule given, never explained); P6 RR | **missing** | P2 | no | core | Short: one sentence with q4. Full: the trec_eval tie note, and "emit strictly decreasing scores" |
| 16 | Scan vs postings lookup (`rank_bm25` keeps per-doc dicts and scans) | P3, R1 | yes (old D.4, S10) | P2 | no | core | Full only (P3 §3 Full repeats it; keep one copy, link the other) |
| 17 | Set precision and set recall; why accuracy is useless (skew) [P2-6]; recall needs \|Rel\| | P6 D.2 | yes for the formulas (old D.5); **missing** for accuracy and the \|Rel\| dependence | P2 (framing) → P6 (@k) | no | core | Short: formulas + A/B/C. Accuracy in one line |
| 18 | Ranked quality: first relevant rank; then RR, MRR, P@k, nDCG | P3 §12 (bridge), P6 | P2 gives first relevant rank only | P6 | no | next | Link to P6. Do not define MRR/nDCG in P2 (P3 already bridges Hit@k/MRR) |
| 19 | Dense similarity (MiniLM cosine) used as the comparison retriever | Old B.2, D.2, S6, S8 | **missing in P2** (used before P4; P3 §2 has a bridge, but Yash meets P2 first) | P4 | no | bridge | Short: two sentences, as P3 §2 does |
| 20 | Test collection = documents + needs + qrels (Cranfield); about 50 needs as a rule of thumb; tune on dev, report on test [P2-5] | 06 §6.2–6.3; M1, M4 | **missing** | P2 (framing), M1 (build) | no | core | Short: one paragraph mapping it to 06 (≥ 40 + 6 items; dev/test/holdout) |
| 21 | Qrels measure retrieval only; a reference answer is not a relevance label (repo `q_a.json`) | 06 §7.1; P6; C6 | yes (old B.3, E) | P2 / M2 | no | core | Short; CR-11 rule |
| 22 | LLM relevance graders: query-time filters (reliable_rag cell 14; Ch3; V2) vs LLM assessors that write qrels (Thomas 2023, UMBRELA, repo open-rag-eval) vs D-10 | V2, M3, end batch | **incomplete** (old H.2 covers the filter only) | V2 / M3 | no | bridge | Short: one line ("a filter is not a label"). Full: LLM assessors exist and are judges, so D-10 applies |
| 23 | RAG's objective tilts to recall first (LLM reader; two-stage) | R3, C4 (MC-005) | yes (old D.5 "why RAG needs both") | R3 / P6 | no | bridge | Short: keep; cite AE Ch7 'Overview' (paraphrase) and Ch13 p.5/13 |
| 24 | Graded vs binary relevance; nDCG needs grades | P6 D.4 | yes (old D.3 scale) | P2 (scale) / P6 (metric) | no | core (scale) | Short: the scale; link nDCG to P6 |
| 25 | Independence assumption, marginal relevance (a duplicate adds nothing) [P2-9] | R4 (MMR), P6 overlap trap | **missing** | R4 / P6 | no | next | Full: one paragraph + link |
| 26 | No fixed threshold on raw scores | P3 §11; V3 | taught in P3 | P3 / V3 | no | next | Link |

**Ideas already taught well and kept:** the toy collection (10 docs, 5 queries), guideline v1, the d02 echo, d08 stuffing, q3 vocabulary mismatch, AND/OR table, runs A/B/C, the k = 3 → 6 candidate cap, the PDF index facts (S9), `rank_bm25` internals (S10), the repo reading guide.

**Overlap with P3 and P6 (avoid duplication).**
- **P3** already teaches the inverted index as a bridge (P3 §3, index explorer, df = list length), "score ≠ relevance" (§11, pointing to P2), and Hit@k/MRR (§12). P2 is studied first (P2 → P3), so P2 **owns** the full index (incidence matrix, Boolean sets, merge, postings read, ties, candidate cap). P3 §3 stays as a recap; P2 never teaches weights (tf, idf, BM25). P2's interactive visual must differ from P3's: Boolean AND/OR with a postings-read counter, not a BM25 ranking.
- **P6** owns P@k, R@k, Hit@k, MRR, nDCG, CE@k. P2 owns the inputs to those metrics: qrels, the guideline, the binary rule, the unjudged-as-zero convention and pool bias, and the "set vs ranking" framing with set precision, set recall and first relevant rank. P6's recall denominator (D.2) and J4 should link back to P2's incomplete-judgment section.

---

### 3. Quiz coverage

No `study/questions/P2_questions.md` exists. The old lesson's Part L items are good raw material and should move into the question file (FORMAT ids). **Every key point below must be answerable from the Short lesson**; the column says where.

| Id (proposed) | Type / set | Title (question only) | Key points must be in Short § |
|---|---|---|---|
| P2-PRE-01 | R / pre | Is the most similar chunk always the most relevant one? | §1, §2 |
| P2-PRE-02 | R / pre | What does the index at the back of a book store? | §4 |
| P2-R-01 | R / main | What is the difference between similarity and relevance? | §2 |
| P2-R-02 | R / main | What does one line of a qrels file contain, and who writes it? | §3 |
| P2-R-03 | R / main | What is an inverted index? | §4 |
| P2-R-04 | R / main | Which question does set recall answer, and which does the first relevant rank answer? | §7 |
| P2-R-05 | R / main (new) | A relevant chunk was never judged. How does the metric count it? | §8 |
| P2-R-06 | R / main (new) | One query, two different needs: why is relevance judged against the need? | §1 |
| P2-A-01 | A / main | Write `build_index(docs)` from memory (coding evidence). | §4 |
| P2-A-02 | A / main | Label q2 against all 10 toy documents with guideline v1. | §3 |
| P2-A-03 | A / main | For MiniLM on q1, k goes from 3 to 6: what happens to set precision and recall? | §6, §7 |
| P2-A-04 | A / main (new) | Three short postings lists are given: compute AND, OR and the postings read. | §5 |
| P2-A-05 | A / main (new) | Qrels were built only from the keyword run's top 3. Which of the dense run's top 3 are unjudged, and what does that do to its recall? | §8 |
| P2-A-06 | A / review (new) | q4's tie rule flips from ascending to descending doc id. What is the new first relevant rank? | §6 |
| P2-T-01 | T / main | A legal team has 30 questions and no labels. What do you build first? (existing L.3 item) | §3, §8, §9 |
| P2-T-02 | T / main (new) | A blog says the dense retriever loses to BM25 on a benchmark whose labels came from BM25 results. What would you check before believing it? | §8 |
| P2-R-07 | R / interview, `source=AIQ-04-Q45` | "How do you build a golden evaluation set for RAG without months of labelling?" (verbatim, MIT notice) | §3, §8, §9 |

**Seed-bank check.** Done against the coach's seed bank: no title reuses a seed or reserve scenario, and P2-T-02 is a new scenario built from BEIR's finding. The external-item cap (≤ 2 per concept, FORMAT §2.3) is met: one interview item.

**Gaps in the old Part L against the new Short plan:** P2-A-03 needs the MiniLM bridge (gap 19) in Short; P2-T-01's "check agreement on a re-labelled sample" needs gap 9's one sentence in Short; P2-R-02's "unlisted = 0" needs gap 7 in Short.

---

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Evidence | Suggested fix |
|---|---|---|---|---|
| E1 | 02 P2 card, "Pre: none" | 03 lists P2's prerequisite as **O2** (graph line `O2 --> P2`, table row 409) | 03 lines 271, 409 | Align to "O2 (environment); no concept prerequisites" (the old lesson already says this) |
| E2 | 02 P2 card, "The book has no inverted index and no IR framing" | The first half is right ("inverted" 0 hits). The second is wrong: "relevance" is on 66 pages; Ch22 p.4–7/19 teaches precision, recall, MRR, MAP, NDCG and set-vs-ranking; Ch22 p.12/19 describes qrels in all but name; Ch13 p.9/13 has labelled query–document pairs | whole-book search (§1) | "No inverted index, no Boolean retrieval, no word 'qrels'; evaluation framing is in Ch22" (P2_FACTS §4 already noted this; 02 is still unchanged) |
| E3 | 02 P2 card, "Repo: none (no IR framing anywhere)"; 04 P2 row "not in repo"; old lesson G.2 table | Missing `evaluation/open-rag-eval-example.ipynb` cells 0, 4, 5, 7: BEIR fiqa, a TREC RAG evaluator, and UMBRELA's 0–3 graded relevance scale (LLM-judged, OpenAI). Also missing the cells the old lesson lists (reliable_rag 14 etc.) | opened 2026-10-17 | Add the cells as a "read and critique" item (an LLM writes the labels; D-10 and "not used: OpenAI" apply) |
| E4 | 02 P2 card "Ext: C#7, C#9 (IIR Ch6–7)"; old lesson G.2 note 4 ("believed ch.1–2; UNVERIFIED") and its Source references | IIR Ch6–7 are scoring and the complete search system (P3/P5). P2's outcomes come from IIR **Ch1** (§1.1–1.3: incidence matrix, inverted index, Boolean merge) and **Ch8** (§8.1, §8.3–8.5: test collections, relevance, pooling, κ) | [P2-1]–[P2-8] | Point P2 to IIR Ch1 and Ch8 (C#10 is §8 already in 01); the "believed ch.1–2" note can be closed as verified Ch1 |
| E5 | 02 P2 card "Ch1 p.8–9/14 (top-K)" | Top-K is on p.8/14 (2–5 nearest chunks) and p.10/14 ("top-K nearest" in the sketch). p.9/14 is the generation step and diagram | book extract | "Ch1 p.8/14, p.10/14 (top-K)" |
| E6 | 04 P2 row, book column | Cites only Intro p.1/8 and Ch1 p.1–3/14 (motivation). Misses Ch3 p.1, Ch13 p.1–2, Ch22 p.4–7, p.12, Ch12 p.3 | book extracts; old lesson G.2 already lists this | Replace as G.2 correction 1 says (still open) |
| E7 | 04 P2 row, gap column | Lists "relevance labels, qrels, ranking as scoring" as absent from the book; Ch22 p.12/19 and p.6/19 cover the first and last | book extracts | As old G.2 correction 2 |
| E8 | Old lesson D.3 "pooling … Source C knowledge … (UNVERIFIED here)"; Verification log "pooling … not fetched" | Now verifiable: IIR §8.5 [P2-8] defines pooling; BEIR [P2-13] measures its bias | sources | Teach it (gap 8) and remove the UNVERIFIED tag |
| E9 | Old lesson D.5 and lab Task 6 | `set_recall` divides by the number of relevant documents in the qrels, but nothing says that this number is only the **judged** relevant count; with incomplete qrels, recall is an overestimate or underestimate depending on what was missed | [P2-6], [P2-11], [P2-16] | Add one sentence + the pool demo (gap 7). No formula change |
| E10 | Old lesson D.4 / lab Task 4 | The tie rule ("ties by doc id ascending") is specified but never explained. On q4 it decides whether the relevant d09 lands at rank 1 or 2 (S5: d06 1, d09 1) | FACTS S5; [P2-18] | Explain ties (gap 15) |
| E11 | Old lesson uses MiniLM cosines (B.2, D.2, S6, S8) | Dense similarity is used before P4 with no bridge in P2 (P3 has one, but P2 comes first) | 03 order P2 → P4 | Two-sentence bridge (gap 19) |
| E12 | Old lesson "Source references": IIR chapters on Boolean retrieval "not in 01's list and were not fetched" | Now fetched (§1). 01 §6 lacks an IIR Ch1 row | [P2-1]–[P2-3] | Add IIR §1.1–1.3 to 01 §6 in a later correction pass |
| E13 | P6 lesson D.1–D.2 ("0 or missing = not relevant") | States the TREC convention without its consequence (pool bias, recall denominator) | [P2-13], [P2-16] | Link P6 D.2 and J4 to P2 §8; add Judged@k as an M2 diagnostic (suggestion for 06 §7.3) |
| E14 | IIR §8.5 itself (external, not ours) | Prints P(relevant) = 0.7878; 630/800 = 0.7875. κ is unaffected at 3 decimals (recomputed 0.7759) | local arithmetic | Note it in Full if the example is used |

No error was found in the old lesson's numbers: they match P2_FACTS, which was run-verified twice (byte-identical).

---

### 5. What the research says

**1. IIR Ch1: what IR is, and why the index is inverted [P2-1]–[P2-4].**
- **The study.** A textbook treatment: Shakespeare's plays, a term–document incidence matrix, then an inverted index (dictionary + docID-sorted postings), then Boolean AND/OR/NOT.
- **The result.** The matrix is almost all zeros, so only the non-zero cells are stored: that is the postings list. df is stored in the dictionary and equals the postings length. AND is a linear merge of two sorted lists, cost O(x + y); processing terms in increasing df keeps intermediate results small. AND tends to high precision and low recall, OR the reverse; a middle ground is hard to find with Boolean operators alone.
- **Its limits.** A teaching text from 2008; it describes classic engines, not vector stores.
- **For the project.** It confirms the old lesson's mechanism and supplies the incidence-matrix picture and the merge algorithm that P2 lacks. Our toy's AND (4 of 5 queries empty) and OR (q1 → 90 of 91 PDF windows) are exactly the "too strict / too loose" pattern.

**2. IIR Ch8: test collections and relevance [P2-5]–[P2-9].**
- **The study.** The standard evaluation design: a document collection, a set of information needs, and relevance judgments per (need, document) pair; set measures, then ranked measures; how judgments are gathered.
- **The result.**
  - Relevance is judged against the **information need**, not the query text (the "python" example: a pet or a language).
  - About 50 needs is a common minimum; tune on a development collection, report on a separate test collection.
  - Accuracy is useless because over 99% of documents are non-relevant; precision and recall replace it. Recall needs the total number of relevant documents.
  - Ranked lists are evaluated by treating each top-k prefix as a set. P@k needs no knowledge of the total relevant count but is unstable across queries.
  - **Pooling:** judge only the union of the top k results of several systems. **κ:** (P(A) − P(E)) / (1 − P(E)); above 0.8 good, 0.67–0.8 fair, below that doubtful. TREC judges usually agree only "fairly". Swapping the judge changes absolute scores a lot but rarely the **ranking of systems**.
  - Critiques: independence of documents, binary vs graded, marginal relevance, relevance vs user utility.
- **Its limits.** Built for web and news search with many judges; RAG chunks overlap and are read by an LLM, not a person.
- **For the project.** 06 already follows this design (≥ 40 + 6 items as a learning minimum, dev/test/holdout, self-agreement κ). P2 must teach the convention that **unjudged = not relevant**, because 06's Recall/CE use the qrels' relevant set as the truth. The "relative rankings survive judge noise" finding is the honest reason a single-annotator set (Yash) is still useful for comparing versions, but not for absolute claims.

**3. Cranfield and incomplete judgments [P2-10], [P2-11].**
- **The study.** Voorhees reviews the assumptions of the Cranfield paradigm used by TREC, CLEF and NTCIR (abstract only could be read). Buckley & Voorhees test what happens when the "all relevant documents are known" assumption is grossly violated.
- **The result.** Common measures are not robust to substantially incomplete judgments; a measure built for incompleteness (bpref, per later literature) tracks them when judgments are complete and degrades less when they are not; pooled collections stay usable as lab tools.
- **Its limits.** Abstract-level evidence here. Numbers from the full papers are **UNVERIFIED** and must not be quoted.
- **For the project.** Do not teach bpref (P6 or M2 may mention it). Teach the assumption and its failure.

**4. BEIR: pool bias, measured [P2-13].**
- **The study.** 18 datasets, 10 retrievers (lexical, sparse, dense, late interaction, rerankers), nDCG@10 via the official TREC evaluation tool. §6 measures annotation bias on TREC-COVID: Hole@10 is the share of a system's top-10 that annotators never judged; the authors then judged the 980 missing pairs, blind to which system found them.
- **The result.** Hole@10 was 6.4% for BM25 and 2.8% for docT5query, but 30.6% for DPR, 14.4% for ANCE and 31.8% for TAS-B. After judging the holes, ANCE rose from 0.654 to 0.735 nDCG@10 (from just below BM25's 0.656 to above BM25's 0.668); docT5query moved only 0.713 → 0.714. The authors conclude the pool was still biased toward lexical systems, although many teams contributed to it. BEIR also chose nDCG@10 because precision and recall ignore rank and MRR/MAP ignore grades.
- **Its limits.** One dataset (TREC-COVID) for the hole study; holes judged by the authors.
- **For the project.** Labels built from one retriever's hits make the other retriever look worse. For Yash's M1 gold (spans found by reading and grep, a lexical act) and for R1 (BM25 vs dense), a Judged@k / hole check belongs in the harness. This is the strongest single fact for P2's new §8.

**5. Kinds of relevance [P2-12].**
- **The study.** Saracevic's literature review classifies relevance manifestations: system (algorithmic), topical (aboutness), cognitive (pertinence), situational (utility), affective.
- **The result.** "Relevance" is a system of related notions, and IR evaluation compares inferences at different levels (the system's score vs a person's judgment).
- **Its limits.** A conceptual review, not an experiment.
- **For the project.** A clean way to untangle the book's and the repo's uses of the word: the retriever's score is **system** relevance; d08 (keyword-stuffed) is **topical** only; our guideline grade 2 ("alone answers the query") is close to **situational** relevance. RAG's "context relevance" (Ch22 p.4) and "answer relevance" are two more uses. Short gets three rows; Full gets all five.

**6. LLMs as relevance assessors [P2-14], [P2-15], repo open-rag-eval cell 7.**
- **The study.** Bing tuned an LLM prompt against careful real-user labels; UMBRELA reproduces it openly with GPT-4o on TREC Deep Learning 2019–2023.
- **The result.** Thomas et al. report LLM labels as good as human labellers and better than third-party workers, cheaper, but sensitive to prompt wording, even to paraphrases. UMBRELA reports high correlation with system rankings (no numbers on the abstract page).
- **Its limits.** Abstracts only; both depend on a high-quality human gold set to validate.
- **For the project (current practice 2024–2026).** Production teams increasingly let an LLM write or extend qrels, then check it against human labels. For this course that is a **judge** under D-10: it runs only in the end batch, validated with `judge-validation`. In P2 it is a Full-only note and a critique item for the repo's open-rag-eval cells (which also use OpenAI, outside the decisions).

**7. Tooling facts [P2-16]–[P2-20].**
- TREC qrels: 4 columns `topic iteration docno relevancy`; iteration is almost always 0; unjudged documents are assumed irrelevant; the line order means nothing.
- trec_eval re-sorts a run by score and breaks ties by document id, so tie order is an uncontrolled parameter (Cabanac et al.; the direction of the tie break is reported differently by sources, **UNVERIFIED**). Fix: emit strictly decreasing scores, or state the tie rule.
- `pytrec_eval` takes nested dicts `{qid: {doc: grade}}` and `{qid: {doc: score}}`; `ir-measures` wraps pytrec_eval and others, reads TREC files, and names measures like `P(rel=2)@5`, `nDCG@10`, `Judged@10`.

**Pitfalls (with evidence).**
1. Similar but irrelevant at rank 1 (Ch3 p.1, Ch13 p.1–2; toy d02, S5–S6).
2. Vocabulary mismatch: no shared word, never a candidate (toy q3, S4).
3. Unjudged = 0: pool bias against the retriever that did not build the pool ([P2-13] Table 4).
4. Recall with an unknown denominator ([P2-6], [P2-11]).
5. Tie order changes ranks ([P2-18]; toy q4).
6. A lenient LLM grader treated as a label (repo reliable_rag cell 14; define_evaluation_metrics cell 9).
7. Chunk-id labels go stale when chunking changes (06 §6.4; P6 J4).
8. One query, many needs: labels written against the words, not the need ([P2-5]).

**How to evaluate P2's own claims.** P2 changes no pipeline variable, so there is no experiment arm. Its checks are: postings equal a full scan (asserted, S3/S9); set metrics match hand values (S8) **and** an independent library (`ir-measures`/`pytrec_eval`, proposed T1 parity test); the pool demo reproduces the direction of BEIR's effect on the toy (computed, not assumed). Retrieval quality only; P2 measures no answer.

**Interview angle (3–5 questions).**
1. AIQ `04-rag-and-retrieval/questions.md` Q45 (golden set without months of labelling): pooled candidate labelling, incomplete labels, spans not ids. *Our correction to its key:* its "verifying candidates is 10× faster" is an unsourced heuristic; and labelling from one retriever's candidates is exactly BEIR's pool bias, so pool from both BM25 and dense.
2. AIQ 04 Q43 follow-up: "How do these metrics mislead when your golden set has incomplete relevance labels?" (answer from P2 §8; Q43 itself is P6).
3. "What is an inverted index, and why is keyword search fast?" (generic; P2 §4–5).
4. "Similarity vs relevance: why can the top-ranked chunk be useless?" (P2 §2).
5. "Precision or recall first, for RAG retrieval, and why?" (P2 §7 + AE Ch7 'Overview'; P6 continues).

---

### 6. Lesson blueprint

Output: `study/lessons/P2_ir_framing.html` (Short/Full, P3 order: answer first → theory in one read → formula sheet → steps → verify → apply → check), plus `study/reading/P2_ir_framing.md` (short depth, FORMAT §3). Keep `concepts/P2_ir_framing.md` as the full A–M file and correct it in a later pass.

**The answer first (draft, 5 sentences).**
1. A retriever never sees relevance: it computes a similarity score for each pair of question and chunk, sorts the chunks, and cuts the list at k.
2. Relevance is a person's judgment about the need behind the question (does this chunk help answer it?), written under a guideline and stored as qrels: query, chunk, grade.
3. Similarity is only the system's stand-in for relevance, and it fails in known ways: an echo of the question, a keyword-stuffed footer, an answer phrased in other words.
4. Keyword search finds its candidates through an inverted index (word → chunks), so a chunk that shares no word with the question can never be returned.
5. You measure retrieval by comparing a run with the qrels, asking two separate questions (what is in the set, and how high it sits), and the numbers are only as good as the labels, because a chunk nobody judged counts as irrelevant.

**The theory in one read (12 linked ideas, each with its formula).**

| # | Idea | Formula / rule |
|---|---|---|
| 1 | Collection, document (chunk), information need, query | C = {d₁…d_N}; need ≠ query text |
| 2 | Retriever = score, sort, cut | run_q = sort_desc(s(q, d)) for d ∈ C, tie rule stated; R_k = first k |
| 3 | Similarity vs relevance | s(q, d) computed; rel(q, d) ∈ {0, 1, 2} judged |
| 4 | Three meanings of "relevance" | score (system) · about the topic (topical) · helps answer (situational) |
| 5 | qrels and the binary rule | line = (qid, doc, grade); unlisted ⇒ 0; relevant ⇔ grade ≥ 1 |
| 6 | Test collection | (C, needs, qrels); ~50 needs; dev for tuning, test for reporting |
| 7 | Inverted index | P(t) = sorted {d : t ∈ d}; df(t) = \|P(t)\| |
| 8 | Boolean retrieval and its cost | AND = ∩ P(t); OR = ∪ P(t); postings read = Σ \|P(t)\|; merge O(x + y) |
| 9 | Ranking from the index; candidate cap | score(d) = Σ_{t∈q, d∈P(t)} w(t, d), w = 1 here; only d ∈ ∪P(t) can score > 0 |
| 10 | Set quality | precision = \|R ∩ Rel\| / \|R\|; recall = \|R ∩ Rel\| / \|Rel\| |
| 11 | Ranking quality | first relevant rank r₁; RR = 1/r₁ (P6 continues) |
| 12 | Labels are incomplete and noisy | Judged@k = judged in top k / k; Hole@k = 1 − Judged@k; κ = (P(A) − P(E)) / (1 − P(E)) |

**Formula-sheet items (one screen):** document · information need · query · run · qrels line · grade scale 2/1/0 · binary rule ≥ 1 · postings P(t) · df(t) · AND / OR · postings read · candidate set ∪P(t) · set precision · set recall · first relevant rank · Hole@k · κ (Full).

**Step-by-step outline (one running example).** The book's own query, "What is the main cause of climate change?" (Ch1 p.8/14), which is the toy's q1 in keyword form. The toy is used because relevance must be judged by hand and the toy's labels already exist (S7); the real climate PDF (91 windows, P1/P3 setting) shows scale. Numbers are from P2_FACTS unless marked.

1. **The need and the query.** q1 = `main cause of climate change`. The book says its retrieved chunks are "directly relevant"; P2 tests that claim instead of assuming it.
2. **Two retrievers score it.** Word overlap through the index: d02 5, d01 3, d08 2 (S5). MiniLM: d02 0.8402, d01 0.6342 (S6). Both put the echo d02 first.
3. **A person judges it.** Guideline v1: d01 = 2, d03 = 1, d09 = 1, all others 0; 8 relevant pairs of 50 (S7). d02 gets 0.
4. **What "relevant" meant there.** d02: high system relevance, topical, zero situational relevance (Saracevic's rows).
5. **The index.** Postings for the five words; AND = d02; OR = d01, d02, d08; 10 postings read (S3–S4). q3 `renewable energy`: 0 postings, nothing returned.
6. **Ranking and ties.** Overlap ranks; q4 ties d06 and d09 at 1, and the doc-id rule puts the relevant d09 second (S5). Reverse the rule and it moves to first (to compute and log).
7. **Cut at k.** Lexical has only 3 candidates for q1, so k = 6 adds nothing (recall 0.333 → 0.333); MiniLM reaches d03 at rank 4 (recall 0.333 → 0.667, precision stays 0.333) (S8).
8. **Set vs ranking.** Runs A, B, C (S8): A and B share a set and differ in first rank (2 vs 1); B and C share a first rank and differ in set.
9. **Unjudged chunks.** Build qrels only from the keyword top 3 (pool = d01, d02, d08 for q1). Then d03 and d09 are unjudged, so MiniLM's d03 at rank 4 counts as a miss. (To compute and log as a new FACTS row.) Then BEIR's measured version of the same effect (external).
10. **The real PDF.** Same query on 91 windows: OR 90 of 91, AND 0, 213 postings read (S9): common words make the index useless as a filter. Span gold turned into chunk qrels: **scratch observation, 2026-10-17, not yet logged**: with 06 §6.7 draft seeds and `any_overlap` on the 91 windows (0-based ids), D-001 → [7]; D-002 → [25, 26] (one span, two overlapping windows); D-004 → [22, 63] (two alternatives on p.8 and p.23); D-005 → [2, 3, 4] (window 3 serves both groups); D-009, D-010 → [] (unanswerable). The verify notebook must recompute and log these before the lesson uses them. Seeds are `llm-draft` and illustrate only.
11. **For your project.** qrels = 06 `evidence_groups`; chunk relevance is derived per chunker (06 §7.2); pool both retrievers when you label (M1); report Judged@k next to every retrieval metric (M2).

**Visuals that earn their place.**

| Visual | Kind | The one thing it shows | Data |
|---|---|---|---|
| V1 Two paths into a metric | hand-drawn SVG flow | Relevance enters only through the judge, never through the retriever | — |
| V2 Similarity vs grade | SVG scatter, 10 points | The highest cosine has grade 0; a grade-1 document sits at rank 9 | S6, S7 (measured, toy) |
| V3 Boolean index explorer | interactive (pick words, AND/OR toggle) | AND too strict, OR too loose; a postings-read counter; no shared word = never found. Must differ from P3's BM25 explorer | S3–S4 |
| V4 Same set, different ranking | three aligned bars A/B/C | Set metrics cannot see order; rank cannot see the set | S8 |
| V5 Recall as k grows | Plotly-style SVG lines, k = 1…10, lexical vs MiniLM | The candidate cap: lexical flattens at 3 candidates | to compute (S8 extension) |
| V6 Holes in the labels | SVG diagram + paired bars | Unjudged hits count as misses and hurt the retriever that did not build the pool | toy pool demo (to compute) + BEIR Table 4 (external, measured) |

No decorative visuals; the Saracevic table and the κ example are tables, not charts.

**Full-only details.** Incidence matrix as a figure; linear merge and df ordering [P2-3]; Boolean history (Westlaw, [P2-4]); `rank_bm25` scans per-document dictionaries (S10); TREC qrels and run formats [P2-16]; trec_eval tie re-sorting [P2-18]; κ formula, pooled vs Cohen marginals, IIR Table 8.2 example (0.7759 / 0.7761, E14); judge choice changes absolute scores but rarely system order [P2-8]; Cranfield assumptions and incomplete judgments [P2-10], [P2-11]; Saracevic's five manifestations [P2-12]; independence and marginal relevance [P2-9] → R4; LLM assessors (Thomas, UMBRELA) and why D-10 puts them in the end batch; accuracy and F1 [P2-6]; the repo's open-rag-eval cells as a critique.

---

### 7. Verify notebook plan

`study/notebooks/P2_ir_framing_verify.ipynb`, same frame as P3's (setup cell with `find_workspace`, `check(...)` with tolerances, a final PASS/FAIL count, Plotly via `plotly_mimetype`, `HF_HUB_OFFLINE=1`).

| § | Recomputes | Data | Code | Chart |
|---|---|---|---|---|
| 1 | Toy corpus loads; sha256 `a2bee6be…` | `p2_toy_corpus.json` | json, hashlib | — |
| 2 | Similarity: overlap scores and MiniLM cosines for q1–q5 | toy | index walk; sentence-transformers MiniLM (local cache) | V2 scatter (cosine vs grade) |
| 3 | qrels: 13 listed, 8 relevant of 50 | toy qrels | dict | heat table q × d |
| 4 | Index: 88 terms, 114 postings, 71 df = 1; postings = scan | toy | dict of sorted lists | df bar chart (toy and PDF, log scale) |
| 5 | AND/OR per query; postings read 10/2/0/2/5 | toy | set ops + merge | V3 static version |
| 6 | Overlap ranking with the tie rule; **new:** q4 under both tie rules → first relevant rank 2 vs 1 | toy | sort with key | — |
| 7 | Runs A/B/C; k 3 → 6 for both retrievers; **new:** recall@k for k = 1…10 | toy | set metrics | V4, V5 |
| 8 | **New:** pool demo: qrels from keyword top 3 only; Judged@3 and recall for MiniLM under pooled vs full qrels | toy | set metrics + unjudged rule | V6 (toy) + BEIR Table 4 bars, labelled external |
| 9 | PDF: 91 windows, 1,868 terms, 8,107 postings, OR/AND counts (S9) | climate PDF, pymupdf 1.26.7 | same functions | — |
| 10 | **New:** span-derived chunk qrels for the 10 draft seeds on the 91 windows (expect the scratch lists in §6 step 10) | 06 §6.7 JSONL | `any_overlap` per 06 §7.2 | small table |
| 11 | `rank_bm25` 0.2.2 keeps per-document dicts and scans (S10) | toy | introspection | — |
| 12 | **New:** κ on IIR Table 8.2 (0.7759 pooled; 0.7761 via `sklearn.metrics.cohen_kappa_score`) | external counts | numpy, scikit-learn 1.9.1 (installed) | — |
| 13 | **New, optional:** parity of set precision/recall and RR with `ir-measures` (`P@3`, `R@3`, `RR`) on the toy, if the package is added | toy | ir-measures | — |

- **Expected values:** existing ones from P2_FACTS S1–S11. New values (tie flip, recall@k curve, pool demo, span qrels, κ, parity) must first be produced by an extended `p2_measure.py` run and logged as **S12–S17** in P2_FACTS; the notebook never invents them.
- **LLM/API calls:** none. MiniLM is a local model; no Cohere, Groq or Claude call.
- **Offline:** yes (HF cache only).
- **Runtime:** about 15–30 s (MiniLM load dominates; UNVERIFIED until run).

---

### 8. Apply-it tool plan and real-world checklist

**Tool:** `study/tools/qrels_check.py`: "Are my relevance labels good enough to measure retrieval on MY documents?" Same pattern as `bm25_fit_check.py` (CLI + importable, Markdown report, no API calls).

- **Inputs:**
  - `--docs` PDFs/MD/TXT (chunked as `bm25_fit_check` does: character windows, `--chunk-size`, `--overlap`), or `--chunks chunks.jsonl`.
  - `--questions q.jsonl` (`id`, `q`, optional `need` note, `type`).
  - `--qrels` in JSONL (`qid, doc, grade, why, judge, guideline_version, ts`) **or** TREC 4-column format; or `--spans` in 06 `evidence_groups` form, converted to chunk qrels with `any_overlap`.
  - `--runs` one or more TREC run files or JSONL rankings (optional); `--dense` builds a local MiniLM run; the tool always builds its own keyword-overlap run from the inverted index.
  - `--relabel` a second, blind labelling pass (optional); `--k` (default 4).
- **Outputs:** `report.md` with 1 Collection and index · 2 Questions vs the index · 3 Label audit · 4 Pool and holes · 5 Set vs ranking per question · 6 Checklist · 7 Recommendation. Also `qrels.trec` (normalised export).

**Real-world checklist (12 checks).**

| # | Check | Auto / manual |
|---|---|---|
| Q1 | Every question has at least one label, and answerable vs unanswerable is explicit | auto |
| Q2 | Every non-zero label (and each tempting zero) has a reason; reasons longer than 3 words | auto |
| Q3 | The guideline version is recorded on every label | auto |
| Q4 | Labels were written before any run was seen (label timestamps earlier than run files) | auto when timestamps exist; else manual: say so in the report |
| Q5 | Pool covers more than one retriever (keyword and dense) | auto (which runs' top-k were judged) |
| Q6 | Hole@k for each run is below a stated limit (default 10%, [P]) | auto |
| Q7 | No retriever's metric changes order when holes are counted as relevant instead of irrelevant (bounds check) | auto |
| Q8 | Ties at the cut-off k are reported, and the tie rule is stated | auto |
| Q9 | Questions with no candidate in the keyword index (vocabulary mismatch) and questions whose OR set is most of the collection (stop-word dominated) are listed | auto |
| Q10 | Self-agreement on a blind re-label of ≥ 10 items: raw agreement and κ (06 §6.5 thresholds) | auto with `--relabel`; else manual reminder |
| Q11 | Labels are spans or derived from spans, not chunk ids of one chunker | auto (input type) + manual (if chunk ids, warn) |
| Q12 | A sample of "relevant" labels re-read against the **need**, not the words (one ambiguous question checked) | manual: the report lists 5 random relevant pairs to re-read |

**Recommendation logic.**
- Q1–Q3 or Q11 fail → "Labels not ready: fix the format and guideline first."
- Q5 or Q6 fail → "Pool is biased: judge the listed holes (top-k chunks from every run that no one judged), then rerun." The report prints the hole list.
- Q7 fails → "Your comparison is decided by unjudged chunks: do not report a winner."
- Q10 below 06 thresholds → "Rewrite the guideline sentence for the disagreeing category; relabel; bump the guideline version."
- All pass → "Labels are fit for retrieval metrics (P6/M2). Report Judged@k next to every number."

---

### 9. LLMOps notebook plan

`study/notebooks/P2_ir_framing_llmops.ipynb`. Application-map row "1 · P2–P3, P5–P6": no external calls; retriever wrappers read-only; trace ranked lists and scores; Hit@k/MRR on toy sets; T1 metric tests.

- **External calls:** **none.** No Groq, Cohere, Claude or LangSmith call is required. MiniLM runs locally; its vectors are content-cached like C3's (foundation §2.2). The notebook still imports `llmops` and runs under `LLMOPS_CACHE_MODE=replay` to prove it makes no call (the `replay` CI marker passes with an empty manifest entry).
- **Framework build (after the mechanism).**

| Lesson step | Framework piece | Note |
|---|---|---|
| Index + Boolean/overlap ranking | `InvertedIndexRetriever(BaseRetriever)` from `langchain-core`, wrapping the plain-Python index; overrides `_get_relevant_documents` | Scores, ranks, matched terms and the tie rule go in `Document.metadata` (the reference page does not define a score field [P2-22]) |
| Dense comparison | `MiniLMRetriever(BaseRetriever)` over cached local vectors | Not `CachedEmbeddings` (no API) |
| Cut at k | `k` from config | Foundation §9.2: `VectorStoreRetriever` defaults to k = 4; always set k |
| Evaluation | `langsmith.evaluate(..., upload_results=False)` as the framework view, with code evaluators | The course runner stays primary |

  Not used: `langchain-community` `BM25Retriever` (P3/R1 territory), LangGraph (linear flow, foundation §9.1 rule).
- **Tracing.** Default: the 06 §2.5 JSONL trace with a **retriever span** per run (foundation §3.3): `qid`, query, tokenizer version, `index_hash`, ranked `doc_id` + score + rank, tie flags, postings read, candidate-set size, `qrels_sha256`, `guideline_version`, latency. Local viewer: Phoenix via `arize-phoenix-otel` + `openinference-instrumentation-langchain` (retriever spans carry document ids and scores). Hosted option: LangSmith, allowed here because the toy corpus and the climate PDF are course data, not book text; tracing stays off unless `tracing_context(enabled=True)` after `privacy.assert_corpus_is("D")` (the toy needs its own corpus tag; see §11).
- **Dataset and evaluators.**
  - Dataset: `p2_toy_qrels_v1.jsonl` (5 queries, 50 pairs, guideline v1) plus the span-derived qrels for the 8 answerable draft seeds on 91 windows, each with a sha256. Mirrors (LangSmith/Phoenix) are copies only.
  - Code evaluators (tier 1, foundation §5): set precision@k, set recall@k, Hit@k, first relevant rank / RR, **Judged@k** (P2-specific), zero-candidate flag, tie-at-cutoff flag. No judge (D-10).
- **Experiment against the previous version.** P2 has no 06 version card. The arms are: Boolean AND → Boolean OR → overlap ranking → MiniLM dense, on identical qrels; plus the same arms under **pooled** qrels (keyword top 3 only) vs **full** qrels, to show that the label set, not the retriever, can flip the comparison.
- **Cost / latency / tokens.** Cost 0; tokens 0. Report p50/p95 latency per arm (index lookup vs scan, excluding MiniLM load) and **postings read per query** as the cost proxy.
- **Versioning.** `index_hash` = sha256(tokenizer version + chunk params + corpus sha); `qrels_sha256` + `guideline_version`; a qrels change is a new file (06 §6.6).
- **Monitoring and feedback.** In "production" (the apply-it tool on Yash's documents) watch: zero-result rate (AND and OR), Hole@k per retriever, tie rate at k, share of queries whose OR set covers > 50% of chunks. Thresholds in `monitor.yaml` ([P] placeholders). Feedback: every hole in the top k goes to a labelling queue; judged holes create a new qrels version; a confirmed mislabel becomes a regression case (`ci-cd-evals`, `error-analysis`).
- **Regression check (T1).** (1) postings equal a full scan; (2) set metrics equal the hand values (S8); (3) parity with `ir-measures` on the toy run (if added); (4) qrels schema check (grade ∈ {0,1,2}, reason present, version present); (5) the pool demo keeps its sign.
- **Place in the lifecycle.** Analyze: read the ranked lists of the 5 toy queries (`trace-data-analysis` in miniature). Measure: code evaluators (`code-based-evaluators`, `rag-evaluation`). Improve: none here (a framing concept); its output (qrels discipline) enables M1–M2. dev (notebook) → CI (T1 tests) → monitoring (apply-it tool logs). Skills: `evals-foundations`, `rag-evaluation`, `code-based-evaluators`, `llm-observability`, `ci-cd-evals`, `collaborative-annotation` (κ, Full).

---

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| LLM, any task | **none needed** | — | — | — | 0 calls | — | Yes. P2 is deterministic; relevance labels must be human (D-10). Claude is not worth it here. An LLM assessor (UMBRELA-style) is a judge and waits for the end batch |
| Comparison retriever | `sentence-transformers/all-MiniLM-L6-v2` via sentence-transformers | 6.1.0 (keep) | yes | yes (HF cache) | 0 | Apache-2.0 | yes (local fallback embedder) |
| Cohere embeddings | `embed-v4.0` | — | — | no | **0 calls in P2** | — | not needed (P4/C3) |
| PDF text | pymupdf | 1.26.7 (pinned) | yes | yes | 0 | AGPL-3.0 | yes |
| Index, metrics | Python stdlib (`re`, `collections`), numpy | 2.5.3 | yes | yes | 0 | BSD | yes |
| BM25 internals (S10) | rank-bm25 | 0.2.2 | yes | yes | 0 | Apache-2.0 | yes |
| κ | scikit-learn `cohen_kappa_score` | 1.9.1 | yes (checked 2026-10-17) | yes | 0 | BSD-3 | yes |
| Charts | plotly | 7.1.0 | yes | yes | 0 | MIT | yes |
| Metric parity + TREC formats | **ir-measures** (pulls `pytrec-eval-terrier` 0.5.10; cp312 Windows wheel exists) | 0.4.3 (2025-11-25) | no | yes | 0 | Apache-2.0 (pytrec-eval-terrier MIT) | yes; small. numpy-2 compatibility **UNVERIFIED** until installed. Also useful to P6/M2 |
| Alternative metrics lib | ranx | 0.3.21 | no | yes | 0 | MIT | not recommended: pulls numba, pandas, seaborn, ir-datasets |
| Public test collections (reading real qrels) | ir-datasets | 0.6.3 | no | downloads data | 0 | MIT | optional only; not needed |
| Fast BM25 over an inverted index | bm25s | 0.3.12 (0.3.13 is newer than 2 weeks) | no | yes | 0 | MIT | not needed (P3/R1 use rank_bm25; mention for reading) |
| Full IR toolkit | pyserini | 2.4.0 | no | needs **Java** (pyjnius), torch, transformers, depends on `openai` | 0 | Apache-2.0 | **heavy; not used** |
| Framework core | langchain-core | 1.6.6 | no | yes | 0 | MIT | yes (D-32, after the mechanism); custom `BaseRetriever` |
| LangChain retriever extras | langchain-community (`BM25Retriever`) | — | no | — | — | MIT | not needed in P2 |
| Graphs | langgraph | 1.2.12 | no | yes | 0 | MIT | not needed (linear flow) |
| Provider packages | langchain-groq / -cohere / -anthropic | — | no | — | — | MIT | not needed (no LLM; groq/cohere ones conflict anyway, foundation finding 4) |
| Hosted tracing / eval | langsmith | 0.14.4 | no | SDK yes; service no | free plan; `LANGSMITH_API_KEY` only if mirrored | MIT (SDK) | optional; course data only; `upload_results=False` by default |
| Local tracing | JSONL trace (default) + `arize-phoenix-otel` 0.17.2 + `openinference-instrumentation-langchain` 0.1.78; viewer `uvx arize-phoenix@20.19.0 serve` | as listed | no | yes | 0 | Apache-2.0; server ELv2 | yes (foundation §3.2) |
| Tests | pytest | 9.1.1 | yes (dev) | yes | 0 | MIT | yes |

**Install lines (do not run until the build step):**
```text
uv add --group eval ir-measures==0.4.3 pytrec-eval-terrier==0.5.10   # optional; metric parity test (P2, P6, M2); pin the backend (0.5.11 is too new)
uv add --group llmops langchain-core==1.6.6 langsmith==0.14.4 arize-phoenix-otel==0.17.2 openinference-instrumentation-langchain==0.1.78   # shared with the foundation's line
uvx arize-phoenix@20.19.0 serve                  # on demand, outside the lock
```
**Keys:** none required. `LANGSMITH_API_KEY` (+ `LANGSMITH_ENDPOINT`) only if Yash chooses to mirror. Never set `LANGSMITH_TRACING` in `.env`.

---

### 11. Open questions for Yash (preferences only)

1. Add `ir-measures` now as an independent check of our metric code (shared with P6/M2)? **Yes** recommended.
2. When you label your own questions, pool candidates from both keyword and MiniLM top 10? **Yes** recommended.
3. Mirror the toy qrels and P2 traces to LangSmith, or keep them local (JSONL + Phoenix)? **Local** recommended.
4. Tag the hand-written toy corpus as its own privacy corpus (`toy`), so the D-only LangSmith guard does not block it? **Yes** recommended.

---

## Concept P3: Lexical retrieval, TF-IDF and BM25 (pilot; not re-audited)

P3 is the finished pilot and the quality bar for this phase (`RESEARCH_PROMPT.md` §8), so it was not audited again. The other audits found one error in it and two points that touch it.
- **Error (found by the P6 audit, E3; not edited).** `study/lessons/P3_bm25.html` §12, Full box, says CE@k equals Hit@k for one-piece questions. That holds only when the overlapping chunk contains the whole span. Hit@k needs any overlap; CE@k needs every character of the span covered (06 §7.2). Suggested wording: "…equals Hit@k only when the overlapping chunk holds the whole span."
- **Check passed (P6 audit).** A scratch run on the 97 v0 chunks reproduced P3 §12's MRR@10 values (dense 0.708, BM25 0.938).
- **Ownership (P2 audit).** P2 now owns the inverted index in full: the incidence matrix, Boolean merge, postings read and ties. P3 §3 stays as a short recap, and P2's interactive index explorer must differ from P3's BM25 one.

---

## Concept P4: Embeddings and similarity

**Status of P4 today.** A full Parts A–M lesson exists (`concepts/P4_embeddings_similarity.md`, 2026-10-08, before the house style), with a blank-file lab (`labs/P4_embeddings_lab.ipynb`, 8 tasks, fingerprint CHECK cells) and a run-verified facts file (`sources/verification/P4/P4_FACTS.md`, S1–S10 + S-src). There is **no** `study/reading/P4_*`, **no** `study/questions/P4_questions.md`, no HTML lesson, no verify notebook, no apply-it tool and no LLMOps notebook. Tracker: P4 `not_started`, application 0, MC-002 open. The existing lesson is strong on the mechanism and on MiniLM; it is thin on the project's actual default embedder (Cohere `embed-v4.0`) and on how embedders are trained, scaled and chosen.

---

### 1. Sources checked

**Book pages (opened with PyMuPDF 1.26.7, 0-based in code, cited 1-based; extracts in `scratchpad/phase01/book_P4/`, 15 files):**

| Page | What it says (paraphrase) | Verified for |
|---|---|---|
| Ch1 p.5/14 | A cleaning step "normalizes" text (text cleaning, not vectors). Each chunk becomes a list of numbers that captures meaning; similar topics give vectors close together; GPS-coordinates analogy | embeddings as coordinates; **no metric named** |
| Ch1 p.6/14 | The greenhouse-emissions / carbon-dioxide example; "Meaning Space" picture; FAISS introduced as a store for nearest-neighbour search | the S5 pair |
| Ch1 p.7/14 | Library analogy; five-step preparation sketch (step 4: embed each chunk) | context only |
| Ch1 p.8/14 | The question is embedded by the exact same process as the chunks so distances are meaningful; top 2–5 nearest chunks retrieved | the MC-002 step |
| Ch6 p.1–2/14 | The asymmetry problem: a short open question and a long declarative chunk can embed far apart even on one topic; rewriting still searches with a question | asymmetry |
| Ch11 p.1/13 | Same asymmetry, attacked from the document side (questions generated per chunk) | link to I6 |
| Ch12 p.8/14 | Example cosine scores, cosine bounded −1..1 vs unbounded BM25; min-max and distribution-based score normalisation | first use of "cosine"; score vs vector normalisation |
| Ch13 p.6/13 | Bi-encoder: same model, query and document independently, compared "typically" by cosine; documents precomputed; cannot see fine interactions. Cross-encoder: one joint input, attends to both, cannot precompute | bi vs cross |
| Ch13 p.7/13 | Side-by-side diagram (clock = speed, target = accuracy); LLM reranking intro | diagram |
| Ch13 p.9/13 | Cross-encoder rerankers are small trained relevance scorers, "milliseconds rather than seconds"; rigid, no custom criteria without fine-tuning | R3 link |
| App p.13/23 | Glossary: Asymmetry Problem (Ch6); Bi-Encoder entry starts | glossary |
| App p.14/23 | Bi-Encoder: compared via cosine (Ch13) | glossary |
| App p.15/23 | Cosine Similarity: direction, −1..1, "standard yardstick", chapters listed 1, 12, 13, 15; Cross-Encoder: more accurate, too slow for whole collections | DV-B4 (Ch1 never says cosine, P4_FACTS S-src) |
| App p.16/23 | Embedding: list of numbers; similar meanings → nearby vectors; GPS analogy | glossary |

All six pages on the 02 card were opened and support their claims. Pages the card **misses**: Ch1 p.8/14 is on the card; Ch12 p.8/14, Ch13 p.9/13, App p.13–14/23 (asymmetry, bi-encoder) and App p.15/23's cross-encoder entry are not.

**Repo cells (`upstream/RAG_Techniques` @ `009adba2…`, verified HEAD; 0-based cells, all in `all_rag_techniques/`):**

| Cite | Confirmed content | Note |
|---|---|---|
| `helper_functions.py` L48–L76 | `def encode_pdf` L48; `OpenAIEmbeddings()` L73; `FAISS.from_documents(cleaned_texts, embeddings)` L74; `return` L76 | The L2 default is **not visible in this file**; it comes from LangChain's FAISS wrapper (now verified at source level, [P4-17]) |
| `json_rag.ipynb` cell 19 | `MODEL_NAME = 'all-MiniLM-L6-v2'`, `model.encode(..., convert_to_numpy=True)` | |
| `json_rag.ipynb` cells 21–23 | `faiss.IndexFlatL2`; markdown: same model for the query, "lower is better"; prints `Distance` | FAISS `METRIC_L2` returns **squared** L2 ([P4-20]) |
| `local_rag_huggingface_faiss.ipynb` cells 10, 13, 14, 16 | bge-base-en-v1.5 (cell 10, chosen "top ranked on MTEB"); `normalize_embeddings=True` "for cosine" (13–14); `FAISS.from_documents` with no strategy (16); `embed_query` used for the sanity check (14) | 02 cites 13–14 and 16 only; cell 10 sets the model |
| `graph_rag.ipynb` cell 12 | `similarity_search_with_score(doc.page_content, k=1)`; `priority = 1 / similarity_score`; `heapq` min-heap | The store is built in **cell 7** (`OpenAIEmbeddings()` + `FAISS.from_documents`), not cited by 02 |
| `dartboard.ipynb` cell 23 | query via `embed_documents([query])`; `1 - np.dot(...)` K×K | asymmetry hazard; diversity matrix |
| `reranking.ipynb` cells 23, 27 | store with `OpenAIEmbeddings` (23); `CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')` (27) | R3 |

**Existing course files read:** CLAUDE.md; `study/research/RESEARCH_PROMPT.md`; `study/research/LLMOPS_FOUNDATION.md` (whole); `study/lessons/P3_bm25_gap_audit.md`; `P3_bm25.html` (headings); `P3_bm25_verify.ipynb` (cell outline); `study/tools/bm25_fit_check.py` (docstring); `study/FORMAT.md`; both WRITING_STYLE files; `visual-learning-writer/SKILL.md` + `HTML_VISUAL_SPEC.md`; 02 P4 card (L217–244) and Gate 1→2 (L1121–1127); 03 rows; 04 P4 row (L125); 06 §2.3–2.4, §3.1–3.2, §6.7; 07 D.5–D.6; `concepts/C3_embedding_indexing.md` (D.4, H.4); 08 Part 4 (D-03, D-08, D-10, D-16, D-31, D-32); `sources/EXTERNAL_RESOURCES_REVIEW_2026-10-09.md` P4 rows (L112, L133–134); `concepts/P4_embeddings_similarity.md` (whole); `labs/P4_embeddings_lab.ipynb` (cell outline); `sources/verification/P4/P4_FACTS.md`; `sources/verification/C3/C3_FACTS.md` L180; `progress/O2_smoke_test_2026-10-08.json` (`cohere_embed`); tracker; misconception log (MC-002); skills `rag-evaluation`, `llm-observability`, `improving-llm-agents` (paraphrased); `sources/coach/transfer_seed_bank.md` (only to avoid seeds).

**Local primary sources:** `all-MiniLM-L6-v2` model card and configs (HF cache, snapshot `1110a243…`; a second snapshot `c9745ed1…` is also cached); `sentence-transformers` 6.1.0 source in `.venv` (`sentence_transformer/model.py`, `util/similarity.py`, `util/tensor.py`, `util/quantization.py`).

**Research probe (offline, MiniLM only; `scripts_P4/probe_p4.py`, output `scripts_P4/probe_p4_out.txt`).** Numbers from it are labelled **probe 2026-10-17**: they are not in P4_FACTS yet and must be re-run by the verify notebook before a lesson cites them.

**AE book:** no P4-specific section was needed (P4 has no generation and no judge). The `rag-evaluation` skill's "retrieval first, measured separately" rule is used in §9.

**Interview repo** (`ombharatiya/AI-Engineer-Interview-Questions` @ `e080df2`, MIT, Copyright (c) 2026 Om): `04-rag-and-retrieval/questions.md` Q6 (bi-encoder), Q7 (choosing a model, MTEB), Q11 (metric choice), Q15 (prefixes / input types), Q18 (dimensions, Matryoshka), Q25 (bi/cross/late interaction); `02-llm-fundamentals/questions.md` Q7 (encoder vs decoder); `01-ml-and-dl-foundations/questions.md` Q40 (contrastive learning, InfoNCE). **Q11 is tutor-reserved**, so it must not become a kit item (§3).

**External sources** (all external; numbered, details in §5):

| # | Source | Status |
|---|---|---|
| [P4-1] | Reimers & Gurevych, *Sentence-BERT*, EMNLP 2019, https://arxiv.org/abs/1908.10084 | verified (abstract) |
| [P4-2] | Karpukhin et al., *Dense Passage Retrieval*, EMNLP 2020, https://arxiv.org/abs/2004.04906 (PDF text searched for §3.1, §3.2, §5.2, App. B) | verified |
| [P4-3] | Muennighoff, Tazi, Magne, Reimers, *MTEB*, 2022/2023, https://arxiv.org/abs/2210.07316 | verified (abstract); venue EACL 2023 **UNVERIFIED** (not on the page) |
| [P4-4] | Enevoldsen, Chung, Kerboua et al., *MMTEB*, 2025, https://arxiv.org/abs/2502.13595 | verified (abstract) |
| [P4-5] | Kusupati et al., *Matryoshka Representation Learning*, 2022, https://arxiv.org/abs/2205.13147 | verified (abstract) |
| [P4-6] | Ethayarajh, *How Contextual are Contextualized Word Representations?*, EMNLP 2019, https://arxiv.org/abs/1909.00512 | verified (abstract) |
| [P4-7] | Cohere, Embed API v2 reference, https://docs.cohere.com/reference/embed | verified (first 100k chars) |
| [P4-8] | Cohere, Models, https://docs.cohere.com/docs/models | verified |
| [P4-9] | Cohere, Cohere's Embed models, https://docs.cohere.com/docs/cohere-embed | verified |
| [P4-10] | Cohere, Embeddings guide, https://docs.cohere.com/docs/embeddings | verified |
| [P4-11] | Cohere changelog, Embed Multimodal v4, https://docs.cohere.com/v2/changelog/embed-multimodal-v4 | verified (no date on page) |
| [P4-12] | Cohere pricing, https://cohere.com/pricing | opened: **no Embed 4 price shown**. The $0.12 / 1M tokens figure comes only from third-party aggregators (e.g. https://www.getmaxim.ai/bifrost/model-library/compare/cohere/embed-v4.0.md, search snippet) → **UNVERIFIED** |
| [P4-13] | sentence-transformers docs, Semantic search, https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html | verified |
| [P4-14] | sentence-transformers docs, Pretrained models, https://sbert.net/docs/sentence_transformer/pretrained_models.html | verified |
| [P4-15] | sentence-transformers 6.1.0 source (local `.venv`) | verified locally |
| [P4-16] | `all-MiniLM-L6-v2` model card (local HF cache `1110a243…`; same text at https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | verified locally; URL not opened |
| [P4-17] | langchain-community `vectorstores/faiss.py` (main), https://raw.githubusercontent.com/langchain-ai/langchain-community/main/libs/community/langchain_community/vectorstores/faiss.py | verified |
| [P4-18] | langchain-core `vectorstores/base.py` (master), https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/vectorstores/base.py | verified |
| [P4-19] | langchain-core `vectorstores/in_memory.py` (master), https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/vectorstores/in_memory.py | verified |
| [P4-20] | FAISS wiki, MetricType and distances, https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances | verified |
| [P4-21] | Claim "all Cohere v3 models are normalised; dot, cosine, L2 give identical rankings" (Qdrant integration page https://qdrant.tech/documentation/embeddings/cohere/ and a Korean write-up, seen only as search snippets) | **UNVERIFIED** (secondary; not on Cohere's own pages) |

---

### 2. Gap audit

Tracker states used: P1 `exposed` (one session, MC-001 open); P2, P3, P5, P6, C3, C4, R3, I6, Q2, D2 `not_started`; M2 and R1 `exposed`. "Written" is not "studied".

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | An embedding is a fixed-length vector from a trained model; dimension (384 MiniLM, 1536 Cohere default) | everywhere; Ch1 p.5/14 | yes (P4 C, D.1) | P4 | no | core | Keep; open with the arrow picture (Short) |
| 2 | **How an embedder learns**: contrastive training, in-batch negatives, the B×B similarity matrix in training | why MiniLM ships a Normalize step and uses cosine; AIQ-01 Q40; review row L134 | **missing** (review sidebar not applied) | P4 | no | core | Short: 3 sentences (pull true pairs together, push the batch apart; serve with the training similarity). Full: InfoNCE formula, DPR's S = QPᵀ, batch size 128 + 1 BM25 negative [P4-2], MiniLM card's batch 1024 [P4-16] |
| 3 | Pooling (mean vs CLS) turns token vectors into one vector | 07 D.6 table; S1 module list | not in P4 | P4 | no | core (Full) | One line in Short ("one vector per text, made by averaging token vectors for MiniLM"); Full: mean vs CLS, why the module list matters |
| 4 | Encoder vs decoder: why MiniLM cannot write an answer and gpt-oss is not our embedder | Part E confusion; AIQ-02 Q7; review row L133 | **missing** (review row not applied) | P1/P4 | P1 exposed only | bridge | One row in "often confused" (Short); Full: attention direction. Do not claim every embedder is an encoder (decoder-based embedders exist) |
| 5 | dot, norm, cosine, L2 formulas | Gate 1→2; quiz R-01, A-01 | yes (D.2, F) | P4 | no | core | Keep; formula → toy table (S2) → hand steps |
| 6 | Similarity vs distance direction, **and each library's convention** | P4-A4, J1, graph_rag H.2 | direction yes; **library conventions missing** | P4 | no | core | Short: one table — FAISS L2 = squared distance (lower better); sentence-transformers "euclidean" = −L2 (higher better); LangChain relevance = 1 − d/√2. Full: why the LangChain value can go negative (§5) |
| 7 | Normalisation and L2² = 2 − 2cos | Gate 1→2 | yes (D.3) | P4 | no | core | Keep; add the unit-circle chord diagram |
| 8 | "Is my model's output unit length?" — check per model | D.4; 06 §2.3 assumes L2-normalised output | MiniLM yes; **Cohere missing** (Cohere's docs never state it [P4-7–P4-10]) | P4 | no | core | Short: "MiniLM yes (Normalize module); Cohere: not documented — we measure it (LLMOps notebook) and normalise anyway" |
| 9 | Query time: same model, one score per chunk, not a matrix (MC-002) | R-02, A-01, C4 | yes (D.1) | P4 (MC-002 → C4) | no | core | Keep. **Add** where matrices really appear: training batches (B×B), dartboard (K×K), all-pairs dedup/analysis (N×N). The learner's "similarity matrix" word is not wrong everywhere, only in retrieval |
| 10 | Query, document, ranking, top-k | throughout | P2 (not studied); P4 assumes it | P2 | no | bridge | Two sentences in place where top-k first appears |
| 11 | Tokens and the model's max length (truncation) | 02 outcome "diagnose truncation"; Gate 1→2 item 4 | **linked to P1 D.4, not taught in P4**; P1 only exposed | P1 | exposed | bridge (Short) | Short must carry the rule and the S7 numbers (cos 0.019276 both ways), because Gate 1→2 tests it cold. Add Cohere's `truncate` default `END` (silent) vs `NONE` (error) [P4-7] |
| 12 | Cohere's context length (docs 128k vs API list 8,192) | 06 §3.2; C3_FACTS L180; P4 D.6; foundation §6.2 | **conflicting** | P4 / C3 | no | core (Full) | State both with sources; mark the effective limit UNVERIFIED until the one-call probe (§9); note it is irrelevant for 1,000-character chunks |
| 13 | Trained length vs served length (MiniLM trained at 128 tokens, serves 256) | 07 D.6 | 07 only | C2/P4 | no | core (Full) | One sentence: "fits" is not "well represented" |
| 14 | Bi-encoder vs cross-encoder; logit, order matters | R-03; Ch13 p.6/13 | yes (D.7) | P4 → R3 | no | core | Keep; S8 numbers as illustration only |
| 15 | Late interaction (ColBERT) | AIQ-04 Q6, Q25 | no | R3 | no | next | One line + link |
| 16 | Asymmetry; `input_type`; prefixes; sentence-transformers `encode_query` / `encode_document` | R-04; Ch6 p.1–2/14; C3 | yes for idea and Cohere; **ST 6 API missing** (the lesson predates it) | P4 | no | core | Short: the rule "same model, maybe different side marker"; show ST 6.1's `encode_query`/`encode_document` (identical output for MiniLM, max diff 0.0, probe) |
| 17 | Score scale is model-specific; anisotropy; thresholds do not transfer | D.5; AIQ-04 Q11 (tutor-reserved) | partly (D.5 numbers), **the word and its cause missing** | P4 | no | core | Short: one paragraph with the S5 strip; Full: Ethayarajh [P4-6] and its limit (word vectors of un-tuned models, not contrastive sentence embedders; MiniLM's unrelated pairs are negative, S5) |
| 18 | Embeddings blur negation and rare exact terms | D.5 (0.8436); P3 bridge | partly | P4 / P3 / R1 | no | core (brief) | Keep the negation pair; link P3 for exact terms |
| 19 | Dimension choice; **Matryoshka**; renormalise after cutting | Cohere `output_dimension` (project default sends it); AIQ-04 Q18 | **missing** | P4 | no | core | Short: one paragraph ("embed-v4.0 offers 256/512/1024/1536, trained so a prefix still works; after cutting, length < 1 → renormalise"). Full: MRL [P4-5]; MiniLM (not MRL) probe: gold rank 2 at 384 dims, 18 at 32 dims |
| 20 | Compressed embedding types (int8, binary) | Cohere `embedding_types` [P4-7] | **missing** | P4 (cost → D2) | no | core (Full) | Full: what each stores, 32× smaller for binary (48 bytes vs 1,536 for MiniLM, probe), top-k overlap check |
| 21 | Choosing a model: MTEB and its limits; own eval set | AIQ-04 Q7; repo cell 10 cites MTEB | **missing** | P4 → M1/M2 | no | core (Short: brief) | "Shortlist from MTEB retrieval subset, decide on your own labelled questions"; MTEB says no method dominates [P4-3] |
| 22 | Measuring retrieval (rank of gold, Hit@k, MRR) | S6/S8 rank changes; §7–§9 | P6 (not studied) | P6 | no | bridge | Define "rank of the right chunk" and Hit@k in one line each where first used |
| 23 | Store the model id with the index; re-embed on change | D.5, J2 | yes | C3 | no | bridge | Keep; link C3 D.4 |
| 24 | Embedding cache key fields (provider, model, revision, input_type, output_dimension, embedding_type, truncate, preproc, text) | LLMOps notebook | C3 D.4 has 6 fields; **dimension/type/truncate missing** (foundation E2) | C3 / LLMOps | no | bridge (Full) | Full: one table; the LLMOps notebook demonstrates a stale-vector bug when `output_dimension` is left out |
| 25 | Embedding cost and limits: ≤ 96 texts per call, tokens billed, trial 1,000 calls/month | LLMOps | **missing** | D2 / LLMOps | no | core (Full) | Full: calls = ceil(n/96); cost per 1k texts from billed tokens |
| 26 | Vector store / FAISS / ANN | Ch1 p.6/14 | P5 | P5 | no | next | Link |
| 27 | Score normalisation for fusion vs vector normalisation | Ch12 p.8/14; Part E | yes (Part E) | R1 | exposed | next | Keep the contrast row |
| 28 | HyDE / document augmentation as asymmetry fixes | Ch6, Ch11 p.1/13 | linked | Q2 / I6 | no | next | Link |
| 29 | Text "normalising" (Ch1 p.5/14) vs vector normalising | Part E | yes | P4 | no | core | Keep |
| 30 | Privacy: book text never sent to Cohere | LLMOps; apply-it `--provider cohere` | foundation only | LLMOps | — | bridge (Full) | One line in the LLMOps notebook and the tool's help text |

**Count:** 30 ideas; 11 missing or incomplete (2, 3, 4, 6, 8, 12, 16, 17, 19, 20, 21, 24, 25 — some partly). The biggest: the project's own embedder (Cohere) is barely taught, "how it learned" is absent, and library score conventions are untaught.

---

### 3. Quiz coverage

No `study/questions/P4_questions.md` exists. The full lesson's Part L has 4 R, 3 A and 1 T item (P4-R-01…04, P4-A-01…03, P4-T-01); reuse their ids. Needed question titles (each key point must be answerable from **Short**; the Short section is named):

| Id | set | Title | Taught in Short § (blueprint §6) |
|---|---|---|---|
| P4-PRE-01 | pre | Two arrows point the same way; one is twice as long. What is their cosine? | 2 |
| P4-PRE-02 | pre | What happens to a user's question before the search? | 4 |
| P4-PRE-03 | pre | A store returns scores 0.3 and 0.8. Which chunk is closer? | 3 |
| P4-R-01 | main | Write the cosine formula. (existing) | 2 |
| P4-R-02 | main | What happens to the question at query time? (existing; MC-002) | 4 |
| P4-R-03 | main | Why can a bi-encoder search a whole collection but a cross-encoder cannot? (existing) | 8 |
| P4-R-04 | main | What does Cohere's `input_type` do? (existing) | 7 |
| P4-R-05 | main | Why do L2 and cosine rank unit vectors the same? | 3 |
| P4-R-06 | main | Where does a real similarity matrix appear, if not in retrieval? | 4, 5 |
| P4-R-07 | main | How did MiniLM learn to put similar texts close together? | 5 |
| P4-R-08 | interview | AIQ-04 Q15 (prefixes / input types; verbatim with MIT notice, `source=AIQ-04-Q15`) | 7 |
| P4-A-01 | main | Compute cos([3,0,4],[0,0,5]). (existing) | 2 |
| P4-A-02 | main | One document vector is doubled: what happens to dot, cosine, L2? (existing) | 2–3 |
| P4-A-03 | main | Find the bug: query from model_v2, index from model_v1. (existing) | 4 |
| P4-A-04 | main | Two unit vectors have cosine 0.6. What does an L2 index report (FAISS squared L2), and what does LangChain's relevance score show? (0.8; 1 − 0.8/√2 = 0.434) | 3 |
| P4-A-05 | main | A 300-token chunk has its answer at token 280. Can MiniLM retrieve it by that answer? | 6 |
| P4-A-06 | main | You keep the first 256 of 1,536 numbers. What is the vector's length now, and what must you do? | 9 |
| P4-A-07 | main | How many Cohere calls and tokens to embed 10,000 chunks of about 250 tokens? (105 calls; 2.5M tokens; cost UNVERIFIED price) | 10 |
| P4-T-01 | main | Help-desk vectors of very different lengths: dot or cosine? (existing practice item) | 3, 5 |
| P4-T-02 | main | A leaderboard winner vs a smaller model for a contracts search: how do you decide? | 10 |
| P4-T-03 | main | 2 million chunks at 1,536 floats do not fit in RAM. What are your options, and how do you check quality? | 9 |

**Seed clashes avoided:** checked against the coach's seed bank; no item reuses a seed or reserve scenario. **AIQ-04 Q11 must not be used as the interview item** (tutor-reserved); Q15 is the interview item instead (Q6 or Q18 are acceptable alternates; at most 2 external items).

**Existing Part L/M items that need Short-mode content the old lesson only has in Full or not at all:** P4-R-04's "plus" point (effect size UNVERIFIED) is fine; the M.1 flashcards skip numbers 4 and 8 (§4).

---

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Evidence | Suggested fix |
|---|---|---|---|---|
| E1 | 02 P4 card, Repo line | "`helper_functions.py:L48-L76` … FAISS default L2": the default is not in that file; it is LangChain's `DistanceStrategy.EUCLIDEAN_DISTANCE` → `IndexFlatL2` | [P4-17] | Say "L2 by LangChain's FAISS default (langchain-community `faiss.py`)" |
| E2 | 02 card; 04 row | `graph_rag.ipynb` cell 12 cited without the cell that builds the store (cell 7: `OpenAIEmbeddings()` + `FAISS.from_documents`) | repo cell 7 | Cite cells 7 and 12. The inversion is now verified at source level: LangChain's docstring says lower score = more similar [P4-17] |
| E3 | 02 card, Book line | Misses Ch12 p.8/14 (first "cosine"), Ch13 p.9/13, App p.13–14/23 (asymmetry, bi-encoder), App p.15/23 cross-encoder entry | book pages | Add them |
| E4 | 02 card, Outcomes | No outcome for the project's default embedder: `input_type`, `output_dimension`, `embedding_types`, `truncate`; no "choose a model" outcome | D-03; [P4-7] | Add "configure and check a Cohere embed call (input type, dimension, truncation, norms)" and "shortlist and choose an embedder" |
| E5 | 04 P4 row; P4 G.2; P4 H.2 | `json_rag` prints and `graph_rag` uses FAISS `IndexFlatL2` scores, which are **squared** L2 (marked UNVERIFIED in P4_FACTS §2) | [P4-20] | Mark verified (docs); ranking unaffected |
| E6 | P4 lesson H.2 fix ("use `similarity_search_with_relevance_scores`") | LangChain's Euclidean relevance is 1 − d/√2 and assumes unit vectors and true L2; FAISS passes **squared** L2, so the score can be negative (−0.5357 for the book's unrelated pair; −1.83 worst case — probe 2026-10-17, DERIVED from [P4-18], [P4-20]). `1 / relevance` can then flip sign or divide by zero | [P4-18], [P4-20], probe | Recommend `priority = distance` (or `1 − cos` on unit vectors) instead |
| E7 | P4 lesson D.6; C3_FACTS L180; 06 §3.2; LLMOPS_FOUNDATION §6.2 | Cohere `embed-v4.0` context: 8,192 (O2's `models.list` `context_length`, 2026-10-08) vs **128k** (Cohere docs: models page, Embed page, v4 changelog). **Coordinator question answered:** Cohere's documentation says 128k on three pages, so the foundation's 128k matches the docs; C3_FACTS's 8,192 is a correct record of what the API's model list returned, not a documented input limit. Which one the endpoint enforces is UNVERIFIED | [P4-8], [P4-9], [P4-11]; O2 JSON | Record both with sources; run the one-call probe (§9, call E) and log the result before any lesson states a single number |
| E8 | 06 §3.2 Cohere row | Still "UNVERIFIED: dim and max length"; O2 recorded 1536 and 8,192, docs give 256–1536 (default 1536) and 128k. Cross-encoder row "effective max length UNVERIFIED" was measured (512, P4_FACTS S1) | O2; [P4-8]; S1 | Update the row |
| E9 | 06 §2.3 `Embedder` ("L2-normalized" outputs) | Not guaranteed for Cohere: no Cohere page says vectors are unit length [P4-7–P4-10]; the claim exists only in secondary sources [P4-21]; int8/binary outputs are never unit length | docs | The `Embedder` must normalise floats itself and assert; normalisation of raw Cohere floats is a measured fact, not an assumption |
| E10 | 06 §2.4 / C3 D.4 / C3 `embed_hash` | Missing `output_dimension`, `embedding_type`, `truncate` (same as foundation E2) | [P4-7] | As foundation E2 |
| E11 | P4 lesson Part E and M.1 | Review rows L133 (encoder vs decoder) and L134 (how our embedder learned) not applied; flashcards numbered 1, 2, 3, 5, 6, 7, 9, 10, 11, 12 (4 and 8 missing) | review L133–134; P4 M.1 | Apply in the rewrite; renumber |
| E12 | P4 lesson D.8 | Predates sentence-transformers' `encode_query` / `encode_document` (present in 6.1.0, installed); the "code rule" should name them | [P4-15]; probe | Mention them; for MiniLM they give identical vectors (max diff 0.0, probe) |
| E13 | Book App p.15/23 and App p.14/23 | Cosine is called "the standard yardstick" and bi-encoders are said to compare via cosine. DPR uses dot product and found L2 ≈ dot > cosine in its setting [P4-2]; sentence-transformers ships dot-product models [P4-14] | [P4-2], [P4-14] | Teach "use the similarity the model was trained with" (not an edit to the book; a lesson note) |
| E14 | P4 lesson Source map | Cites "C#16–#21" for SBERT/DPR/MTEB as "further reading only"; the new lesson uses them as evidence | — | Cite [P4-1]–[P4-3] directly |

---

### 5. What the research says

**[P4-1] Sentence-BERT (Reimers & Gurevych, EMNLP 2019).**
- **The study:** siamese BERT networks that output one vector per sentence, compared by cosine; tested on STS and transfer tasks.
- **The result:** finding the most similar pair in 10,000 sentences takes about 50 million cross-encoder passes (about 65 hours) with plain BERT, versus about 5 seconds with SBERT, at similar accuracy (abstract).
- **Limits:** STS benchmarks, 2019 models; the speed figure is the pairs count, not a retrieval-quality result.
- **For the project:** this is the number behind "bi-encoder for the whole collection, cross-encoder for the shortlist" (S8: 1 query pass vs 10 or 91 pair passes).

**[P4-2] DPR (Karpukhin et al., EMNLP 2020).**
- **The study:** two BERT encoders (question, passage); similarity = **dot product** (Eq. 1); trained with **in-batch negatives**: S = QPᵀ is a B×B matrix, the diagonal is the right pair (§3.2); main model batch 128 plus one BM25 hard negative per question.
- **The result:** beats Lucene BM25 by 9–19 points absolute top-20 accuracy across open-domain QA sets (abstract). On NQ dev, dot product + NLL: top-20 78.1; L2 + NLL: 76.1 (App. B Table 6); the text says L2 is comparable to dot and both beat cosine.
- **Limits:** one model family, Wikipedia QA, 2020; the cosine result is for their training setup, not a general law.
- **For the project:** (1) "cosine is the standard" is a convention, not a rule — use the model's training similarity; (2) the B×B matrix is where "similarity matrix" legitimately lives (MC-002 nuance); (3) hard negatives explain why embeddings separate near-topic chunks at all.

**[P4-16] all-MiniLM-L6-v2 model card (local).**
- **The facts:** contrastive objective — cosine for every pair in the batch, cross-entropy against the true pairs; batch 1,024; over 1 billion training pairs; sequence length limited to 128 tokens during training; inputs longer than 256 word pieces are truncated; Apache-2.0.
- **For the project:** the three-sentence "how our embedder learned" sidebar is fully sourced from the local card. It explains the Normalize module (training used cosine) and the 128-vs-256 caution.

**[P4-3] MTEB (2022/23) and [P4-4] MMTEB (2025).**
- **The study:** MTEB: 8 task types, 58 datasets, 112 languages, 33 models. MMTEB: over 500 tasks, 250+ languages, community-built.
- **The result:** "no particular text embedding method dominates across all tasks" (MTEB abstract). MMTEB: the best public model was multilingual-e5-large-instruct at 560M parameters, smaller than several LLM-based embedders.
- **Limits:** public benchmarks get trained toward; the average hides the retrieval subset; your domain is not in it (AIQ-04 Q7 says the same).
- **For the project:** the repo picks bge-base because it is "top ranked on MTEB" (cell 10). The lesson teaches: shortlist from MTEB's retrieval tasks, decide on our labelled questions (M1/M2), and never switch embedders inside an experiment (06 §3.2).

**[P4-5] Matryoshka Representation Learning (Kusupati et al., 2022).**
- **The study:** train one vector so that nested prefixes (first 64, 128, … numbers) each work as an embedding.
- **The result:** up to 14× smaller embeddings at the same ImageNet-1K accuracy; up to 14× retrieval speed-ups (abstract; vision-heavy, BERT included).
- **Limits:** mostly vision results; text-retrieval gains depend on the model.
- **For the project:** Cohere states embed-v4.0 offers Matryoshka dimensions 256/512/1024/1536 [P4-11]. A non-Matryoshka model loses quality fast when cut: probe 2026-10-17, MiniLM, D-002 gold rank 2 at 384 dims, 2 at 256, 1 at 128, 2 at 64, **18 at 32**; D-004 stayed at 1 (two questions: an illustration, not an evaluation). A cut vector is no longer unit length (MiniLM norms 0.77–0.86 at 256 dims, 0.21–0.37 at 32), so it must be renormalised; sentence-transformers truncates before it normalises, and only if `normalize_embeddings=True` [P4-15].

**[P4-6] Anisotropy (Ethayarajh, EMNLP 2019).**
- **The study:** geometry of contextual **word** vectors in ELMo, BERT, GPT-2.
- **The result:** representations are not isotropic in any layer; self-similarity falls in upper layers.
- **Limits:** word vectors of models **not** trained contrastively for sentence similarity. Contrastive training changes the picture: MiniLM gives −0.0859 and −0.0478 for unrelated pairs (P4_FACTS S5).
- **For the project:** the honest lesson line is "score scales differ by model, sometimes a lot; measure the unrelated-pair baseline for your model; never carry a threshold across models". Do not teach "all embedders put unrelated text near 0.7".

**Cohere embed-v4.0 facts ([P4-7]–[P4-11], read 2026-10-17):**

| Field | Fact |
|---|---|
| `input_type` | **Required** for v3+ models; `search_document`, `search_query`, `classification`, `clustering`, `image` |
| `output_dimension` | embed-v4 and newer only; v4: 256, 512, 1024, 1536 (default 1536); Matryoshka (changelog) |
| `embedding_types` | default `["float"]`; also `int8`, `uint8`, `binary`, `ubinary`, `base64` |
| `truncate` | default `END` (silently drops the end down to the max length); `START`; `NONE` returns an error |
| `max_tokens` | optional per-input cap; truncation follows `truncate` |
| Texts per call | ≤ 96 |
| Context | docs: 128k; API `models.list` (O2, 2026-10-08): 8,192 — conflict, E7 |
| Normalised output? | **not stated** on any Cohere page; secondary sources say v3 vectors are unit length [P4-21] → UNVERIFIED for v4 |
| Usage | `meta.billed_units.input_tokens` per call |
| Price | not on cohere.com/pricing; $0.12 / 1M tokens per aggregators → **UNVERIFIED** |
| Newer models | `embed-v5.0-pro` and `embed-v5.0-fast` are listed (128k; 256–2048 dims, default 2048) |

**Library score conventions (current practice; sources [P4-15], [P4-17], [P4-18], [P4-19], [P4-20]):**

| Library | Default metric | Score returned | Higher = closer? |
|---|---|---|---|
| FAISS `IndexFlatL2` / `METRIC_L2` | L2 | **squared** L2 | no |
| LangChain `FAISS` | `EUCLIDEAN_DISTANCE`, `normalize_L2=False` | squared L2 (from FAISS) | no |
| LangChain `similarity_search_with_relevance_scores` (Euclidean) | — | 1 − d/√2 (assumes unit vectors, true L2) | yes, but can be < 0 (E6) |
| LangChain `InMemoryVectorStore` | cosine; query via `embed_query`, docs via `embed_documents` | cosine | yes |
| sentence-transformers 6.1 | `similarity_fn_name` defaults to cosine; "euclidean" returns −L2 | −1.4737 for the book's unrelated pair (probe) | yes |

**sentence-transformers 6.1.0 (installed) [P4-13]–[P4-15]:** `encode_query` / `encode_document` apply a model's "query"/"document" prompt if it has one; for models without prompts they equal `encode` (MiniLM: prompts empty, max diff 0.0, probe). `normalize_embeddings=False` by default (MiniLM is still unit length through its own Normalize module). `truncate_dim` and `precision` (`int8`, `uint8`, `binary`, `ubinary`) exist. The docs split models into cosine-tuned (unit vectors; any of dot/cosine/L2) and dot-tuned (use dot) [P4-14], and separate symmetric from asymmetric search [P4-13].

**Pitfalls, with evidence:**
1. Wrong query model, same dimension, no error: gold rank 2 → 19 (P4_FACTS S6).
2. Distance used as a similarity: `graph_rag` cell 12 (S10), now source-verified (E2).
3. Silent truncation: MiniLM at 256 (S7); Cohere `truncate=END` by default [P4-7].
4. Asymmetric model used symmetrically: Cohere requires `input_type`; using `search_document` for queries is legal and silent (size of the effect on our corpus UNVERIFIED).
5. Cutting dimensions without renormalising (probe norms) or on a non-Matryoshka model (probe ranks).
6. Thresholds copied across models (S5 vs AIQ-04 Q11's claim; C4 D.5 0.1858).
7. Relevance-score helpers that assume a metric (E6).
8. Cache keys that omit dimension/type (foundation E2).

**How to evaluate (retrieval only; `rag-evaluation`):** rank of the gold chunk, Hit@k and MRR on labelled questions (P6 bridge), always per arm with the same chunks; compare against the MiniLM fallback and the Cohere default. Two to ten draft questions show a mechanism, never a winner. Answer quality is not touched by P4.

**Interview questions (3–5 an interview asks):**
1. Cosine vs dot vs Euclidean: when does it matter? (AIQ-04 Q11; tutor-reserved, not a kit item)
2. Bi-encoder at retrieval time and its key limit; why not a cross-encoder for first stage? (AIQ-04 Q6, Q25)
3. Why do models want query/document prefixes or input types; what breaks if you ignore them? (AIQ-04 Q15 → kit item P4-R-08)
4. How do you choose an embedding model; what does MTEB tell you? (AIQ-04 Q7)
5. Dimensionality trade-offs and Matryoshka; why renormalise after truncating? (AIQ-04 Q18)
Background: encoder vs decoder (AIQ-02 Q7); contrastive learning / InfoNCE (AIQ-01 Q40).

---

### 6. Lesson blueprint

Deliverables: `study/lessons/P4_embeddings.html` (Short/Full) plus `study/reading/P4_embeddings.md` (short depth) and `study/questions/P4_questions.md`. The old `concepts/P4_embeddings_similarity.md` stays as the A–M record; its verified numbers carry over.

**The answer first (draft, 5 sentences).**
1. An embedding model turns each text into a fixed list of numbers, an arrow, so that texts about the same thing point in similar directions.
2. To search, the question goes through the **same** model, then gets one score against every stored chunk, and the top-k scores win.
3. Cosine measures only the angle; dot product also rewards long arrows; L2 measures the gap between arrow tips — on unit-length arrows all three give the same ranking, because L2² = 2 − 2cos.
4. Most silent failures come from mismatches nobody sees: a different model or side marker for the query, a distance read as a similarity, text past the model's length limit, or a dimension cut without renormalising.
5. A bi-encoder makes the whole-collection search cheap because document arrows are computed once; a cross-encoder reads question and chunk together, which is more precise but costs one model pass per pair, so it only reranks a short list.

**The theory in one read (12 linked ideas, each with its formula):**

| # | Idea | Formula / rule |
|---|---|---|
| 1 | An embedding is a vector from a trained encoder | v = pool(encoder(text)) ∈ ℝᵈ; d = 384 (MiniLM), 1536 (Cohere default) |
| 2 | How it learned: pull true pairs together, push the batch apart | L = −log( e^{s(q,p⁺)/τ} / Σⱼ e^{s(q,pⱼ)/τ} ); batch scores S = QPᵀ (B×B) |
| 3 | Three measures | a·b = Σaᵢbᵢ; ‖a‖ = √(a·a); cos = a·b/(‖a‖‖b‖); L2 = ‖a − b‖ |
| 4 | Direction of a score | similarity: higher = closer; distance: lower = closer; check each library (table) |
| 5 | Normalise → one ranking | â = a/‖a‖; ‖â − b̂‖² = 2 − 2cos; â·b̂ = cos |
| 6 | Check, don't assume, unit length | assert max|‖vᵢ‖ − 1| < 1e-3 |
| 7 | Query time: same model, one score per chunk | s = E·q, shape (N,), not (N, N) |
| 8 | Asymmetry and side markers | Cohere `search_query` vs `search_document`; prefixes only if the model card names them |
| 9 | Length limit | tokens > max → text ignored (MiniLM 256; Cohere `truncate=END`) |
| 10 | Score scales are model-specific | measure the unrelated-pair baseline; no threshold crosses models |
| 11 | Dimensions and compression | keep first k numbers (Matryoshka) → renormalise; int8 (1 byte/dim), binary (1 bit/dim) |
| 12 | Bi- vs cross-encoder | cost per query: bi 1 pass + N dot products; cross N passes; cross score is a logit |

**Formula-sheet items:** dot; norm; cosine; L2 and squared L2; L2² = 2 − 2cos; unit vector; score vector shape (N,); FAISS L2 = squared; LangChain relevance 1 − d/√2; sentence-transformers euclidean = −L2; InfoNCE (Full); bytes per vector = d × 4 (float32), d (int8), d/8 (binary); Cohere calls = ⌈n/96⌉; cost = billed tokens × price (price UNVERIFIED).

**Step-by-step outline (one running example).** Corpus: the climate PDF as P4's 91 plain windows (1,000 characters, step 800), question D-002 "In what year was the Paris Agreement adopted?", gold window 26 — the same objects P4_FACTS already measured, so every number is logged. MiniLM is the running model because it runs offline and its numbers exist; the Cohere column stays **empty** until the LLMOps notebook's recorded run fills it.

| Short § | Step (heading names the insight) | Artefact shown | Numbers (source) |
|---|---|---|---|
| 1 | "Three bugs that raise no error" | wrong model, distance as similarity, truncation | S6, S10, S7 |
| 2 | "An embedding is an arrow; cosine reads only its angle" | toy q, d1–d3 | S2 table; Part F by hand |
| 3 | "Normalise once, and the three measures agree" + library direction table | unit-circle chord diagram | S2, S3 (100/100), [P4-17]–[P4-20] |
| 4 | "The question is embedded too — one score per chunk" (MC-002) + where matrices really appear | score vector (91,) vs 91×91 | S6; B×B [P4-2]; K×K dartboard |
| 5 | "Where the closeness comes from" (contrastive training; encoder vs decoder row) | 3-sentence sidebar | [P4-16], [P4-2] |
| 6 | "Text past the limit cannot help retrieval" | 400-token passage bar | S7: 0.019276 twice; Cohere `truncate` |
| 7 | "Same model, but the question may need its own label" | Cohere `input_type`; ST `encode_query` | S9 (prefix moves vectors: 0.9626 / 0.6965 / 0.6865); Cohere gap: empty until logged |
| 8 | "Fast and blind vs slow and careful" (bi vs cross) | side-by-side, pass counts | S8 (1 vs 10 vs 91; 2 → 1 for D-002, illustration) |
| 9 | "A 0.5 means different things in different models" + negation | score strip | S5 (−0.0859, −0.0478, 0.5356, 0.6918, 0.8436) |
| 10 | "Smaller vectors: cut, renormalise, re-measure" | dimension chart | probe numbers, after the verify notebook logs them |
| 11 | "Choosing a model: leaderboard to shortlist, your questions to decide" + cost | decision box | [P4-3], [P4-4]; calls = ⌈n/96⌉ |
| 12 | Defaults and one-line asserts | assert list | — |
| 13–15 | Verify / apply / check | links | — |

**Visuals that earn their place (inline SVG; Plotly only in notebooks):**
1. **Arrow playground** (interactive 2-D): drag d's tip; dot, cos, L2 update; a "normalise" toggle snaps arrows to the unit circle and the raw-L2 ranking flips back. Shows: length changes dot and L2 but not cosine.
2. **Unit-circle chord**: the chord between two unit arrows with the curve L2 = √(2 − 2cos). Shows why rankings agree.
3. **Index time / query time flowchart** with a small "where N×N matrices live" side panel (training batch, dartboard, dedup). Shows the MC-002 fix.
4. **Bi- vs cross-encoder** side by side with pass counters (1 / 10 / 91). Shows the cost asymmetry.
5. **Score strip** −1…1 with the five S5 pairs, the negation pair highlighted. Shows model-specific scale and the negation limit.
6. **Truncation bar** (tokens 0–400, cap at 256, answer at 300) with the two identical cosines. Shows the hard ceiling.
7. Full only: **dimension cut chart** (dims 384→32 vs gold rank and norm). Shows why Matryoshka and renormalising matter (labelled "MiniLM, not Matryoshka-trained; 2 questions").
8. Full only: **library direction table** (not a chart).

**Full-only details:** InfoNCE and τ; DPR's dot/L2/cosine table; pooling; anisotropy study and its limit; Matryoshka; int8/binary and top-k overlap (probe: int8 kept the gold window at rank 2 but reshuffled ranks 3–5); the LangChain negative-relevance derivation (E6); Cohere 8,192 vs 128k; MiniLM trained at 128 tokens; MTEB/MMTEB details; cache-key fields; repo reading list (json_rag 19→21→23, local_rag 10/13/14/16, dartboard 23, graph_rag 7/12, reranking 27).

---

### 7. Verify notebook plan

`study/notebooks/P4_embeddings_verify.ipynb`, same pattern as P3's: a setup cell with a `check(label, got, expected, tol)` helper, then one section per lesson §, each "What this verifies → code → check".

| Section | Recomputes | Data / code |
|---|---|---|
| Setup | versions, model snapshots, PDF sha256, 91 windows | pymupdf 1.26.7; `HF_HUB_OFFLINE=1` |
| §2–3 | S2 toy table, rankings, scale-by-2; S3 (100/100, 94/100, 68/100) | NumPy; `default_rng(0)` |
| §3 library directions | FAISS-style squared L2 vs L2; ST `similarity_fn_name="euclidean"` = −L2 (−1.4737); the LangChain formula applied to squared L2 (−0.5357) and worst case (−1.8284) — formula re-typed, **no LangChain import** | NumPy + sentence-transformers |
| §4 | score shape (91,), D-002 top-5, wrong-model rank 19; a separate, clearly labelled 91×91 **all-pairs** cosine histogram (analysis, not retrieval) | MiniLM, L3 |
| §5 | model card fields (128 training tokens, batch 1024, Normalize module) read from the cache | JSON/README parse |
| §6 | S7 truncation (0.019276 twice; tail 0.284787) | MiniLM tokenizer |
| §7 | `encode_query` == `encode` for MiniLM (max diff 0.0); S9 prefix cosines | ST 6.1 |
| §8 | S8 rerank (2 → 1), logits range, CE(q,d) ≠ CE(d,q) | cross-encoder |
| §9 | S5 strip; unrelated-pair baseline (mean of off-diagonal windows' cosines) | MiniLM |
| §10 | `truncate_dim` 384/256/128/64/32: norms and gold ranks (probe values); int8 and ubinary top-k overlap with float (int8 top-5 64, 26, 63, 16, 79 vs float 64, 26, 16, 63, 25) | ST `truncate_dim`, `quantize_embeddings` |
| §11 (optional, replay) | Cohere: dimension 1536; raw norms; cos(search_query, search_document) for the same text; API-256 vs local cut-and-renormalise of 1536; top-k overlap vs MiniLM — **only** from the LLMOps notebook's recorded pack via `llmops.cache` in `replay` mode; skipped with a clear message when the pack is missing | recorded vectors |

- **Plotly charts:** score strip; norms histogram; all-pairs histogram; dimension-vs-rank line; int8/binary overlap bars.
- **API calls:** none. §11 reads the cache in replay only (0 new calls).
- **Offline:** yes (three cached models: MiniLM 175 MB folder with two snapshots, L3 68 MB, cross-encoder 88 MB).
- **Runtime:** about 1–2 minutes on CPU (several encodes of 91 windows; cross-encoder over 91 pairs once).
- **Facts:** new numbers go into a P4_FACTS addendum (S11+) when the notebook is built; the probe numbers are not citable until then.

---

### 8. Apply-it tool plan and real-world checklist

`study/tools/embed_fit_check.py` — "does my embedding setup suit MY documents and questions?" Mirrors `bm25_fit_check.py` (CLI + importable, Markdown report).

- **Inputs:** `--docs` (PDF/TXT/MD), `--questions` (.txt or .jsonl with optional `expect` and `type`), `--model` (default `sentence-transformers/all-MiniLM-L6-v2`), `--chunk-size`, `--overlap`, `--k`, `--rerank` (local ms-marco cross-encoder), `--dims 256,128`, `--provider cohere` (optional; through `llmops` cache in `auto`/`replay`; the privacy guard refuses book text).
- **Outputs:** report sections 1 Setup (model, dim, max length, pooling, Normalize, prompts), 2 Chunks vs limit (token counts with the model's own tokenizer), 3 Vectors (norms, unrelated-pair baseline, near-duplicates), 4 Per question (top-k with scores, rank of `expect`), 5 Measuring (Hit@k, MRR per type; with `--rerank` and `--dims` arms), 6 Checklist, 7 Recommendation, 8 Cost (Cohere only: calls, billed tokens, cost at the dated price).
- **API calls:** none by default. With `--provider cohere`: ⌈chunks/96⌉ document calls + ⌈questions/96⌉ query calls per dimension; replayable.

**Real-world checklist (12):**

| # | Check | Auto / manual | How |
|---|---|---|---|
| C1 | Chunks over the model's max length | auto | own tokenizer; report count and % |
| C2 | Vectors are unit length (or normalised by us) | auto | max |‖v‖ − 1| |
| C3 | Query and documents use the same model id | auto | manifest / config comparison |
| C4 | Query side marker set (`input_type` or model-card prompt) | auto (Cohere, ST prompts) / manual (other APIs) | read config; model `prompts` |
| C5 | Score direction understood | auto | self-retrieval test: each of 5 chunks must rank itself first (score 1 or distance 0) |
| C6 | No threshold copied from elsewhere | auto | report the unrelated-pair baseline and the top-1 score range; warn if a `--threshold` is inside the baseline band |
| C7 | Near-duplicate chunks | auto | pairs with cos > 0.98 (all-pairs, labelled as analysis) |
| C8 | Right chunk found (labelled questions) | auto | Hit@k, MRR per type; "not enough data" below 10 labelled questions |
| C9 | Reranker helps | auto (`--rerank`) | Hit@1/MRR with vs without |
| C10 | Smaller dims / int8 safe | auto (`--dims`) | top-k overlap and Hit@k vs full |
| C11 | Negation and exact terms | manual | write 2 negated and 2 code/number questions; compare with P3's BM25 tool |
| C12 | Licence, privacy and cost of the model | manual | model card licence; no book or private text to an API; cost line from section 8 |

**Recommendation logic:** C1 > 0 → shorten chunks or switch to a longer-context model before comparing anything · C2 fails → normalise both sides and re-run · C3 or C4 fails → fix before any measurement · C5 fails → stop: the score is read backwards · fewer than 10 labelled questions → "mechanism only, not enough data" · reranker raises Hit@1 on ≥ 3 more questions than it lowers → "try R3 properly" · dims/int8 keep ≥ 0.9 top-k overlap and equal Hit@k → "smaller is safe here" · C11 shows misses → "hybrid (R1)".

---

### 9. LLMOps notebook plan

`study/notebooks/P4_embeddings_llmops.ipynb`: the P4 mechanism as a production embedding service, after the lesson and verify notebook. It depends on the shared `study/llmops/` package (foundation §10: `cache.py`, `providers.call_cohere_embed`, `lc.CachedEmbeddings`, `trace.py`, `cost.py`, `privacy.py`, `datasets.py`), which does not exist yet.

**Framework build (pieces mapped to the mechanism):**

| Lesson step | Framework piece | Default the lesson warns about |
|---|---|---|
| Embed documents with `search_document` | `CachedEmbeddings.embed_documents` (langchain-core `Embeddings`) | `CohereEmbeddings`: `truncate=None` → server END; no batching; `max_retries=3` (foundation §9.2) — shown read-only |
| Embed the query with `search_query` | `CachedEmbeddings.embed_query` | `dartboard` cell 23's `embed_documents([query])` |
| One score per chunk, top-k | `InMemoryVectorStore` (cosine; calls `embed_query` / `embed_documents`) [P4-19] | none hidden; k must be set |
| Score direction | read-only cell: LangChain `FAISS` defaults (`EUCLIDEAN_DISTANCE`, `normalize_L2=False`, squared L2, relevance 1 − d/√2) [P4-17], [P4-18] | E6 |
| Compare models | MiniLM through a plain `Embeddings` wrapper (local; content cache) | none |

No LangGraph: the flow is linear (foundation §9.1). `langchain-cohere` is not installed (cohere < 6 conflict).

**External calls (all Cohere `embed-v4.0`, recorded once, then replay):**

| Call | Purpose | Texts | Calls |
|---|---|---|---|
| A | 91 windows, `search_document`, 1536, `embedding_types=["float","int8","ubinary"]`, `truncate="END"` | 91 | 1 |
| B | 10 draft seed questions (D-001…D-010), `search_query`, same types | 10 | 1 |
| C | same questions, `search_document` (asymmetry ablation arm) | 10 | 1 |
| D | windows + questions at `output_dimension` 256, 512, 1024 (float) | 91 + 10 each | 6 |
| E | context probe: the whole climate text (about 13k tokens; PDF is corpus D) with `truncate="NONE"` — resolves 8,192 vs 128k (E7) | 1 | 1 |
| F | canary: 3 fixed climate sentences, cache bypassed (`record`, samples 1 and 2) to set the drift tolerance | 3 | 2 |
| **Total** | | | **12 calls**, about 4 × 91 windows ≈ 364 window-embeddings + 70 question-embeddings; roughly 90–110k billed tokens (Cohere token counts per window are measured, not assumed) |

- **Cost:** about $0.011–0.013 at $0.12 / 1M tokens (**price UNVERIFIED**); 12 of the trial key's 1,000 monthly calls. **Cost per 1k texts** is reported from billed tokens: 1,000 windows ≈ 11 calls ≈ ⌈1000/96⌉; tokens ≈ 1,000 × (measured tokens per window).
- **Replay:** after one `record` run, `LLMOPS_CACHE_MODE=replay` runs the whole notebook with no key; its keys go into `replay_manifest.json`; the `replay` pytest marker executes it headless. MiniLM needs no cache key (local) but its vectors are content-cached.
- **Privacy:** only corpus D windows and the draft seed questions are sent; `privacy.assert_corpus_is("D")` before each call; book text is refused by the shingle guard.

**Tracing (foundation §3; `llm-observability`):** per run a root span (`run_id`, `config_hash`, `cache_mode`); an **embedding span** per call: provider, model, `input_type`, `output_dimension`, `embedding_types`, `truncate`, number of texts, billed tokens, latency, cache hit/miss, key prefix, `http_attempts`; a **retriever span** per question: ranked window ids, scores, score direction, k. Default sink: local JSONL; viewer: Phoenix (`uvx`); LangSmith only inside `tracing_context(enabled=True)` after the corpus-D check, exporting ids and scores.

**Dataset and evaluators:** the 10 draft seeds (06 §6.7, marked draft — not the golden set; M1 replaces them), gold = windows containing the evidence phrase (as P4_FACTS S6). Code-based evaluators only (no judge, D-10): (1) dimension = requested; (2) float norms (record raw values; assert after our normalisation); (3) replay byte-identical; (4) gold rank, Hit@4, MRR per arm; (5) asymmetry delta (B vs C arms); (6) API-256 vs cut-and-renormalised 1536 top-k overlap; (7) int8/ubinary vs float top-k overlap; (8) the stale-key test: change `output_dimension` without changing the key → the test must fail (demonstrates E10).

**Experiment against the previous version:** P4 has no version card (Proj: —). The comparison is the two v0 embedders from 06 §3.1: MiniLM fallback vs Cohere default (`search_query`/`search_document`, 1536), plus the ablation arms. Results are reported as an illustration on 8 answerable draft questions, with the explicit sentence that this decides nothing (C3/C4 and M2 measure properly). Results tables stay empty until the logged run.

**Cost / latency / tokens:** billed tokens per call; cost if called vs paid (0 on replay); p50/p95 latency per call type in `record` mode only; bytes per vector per dimension and type (1536 float = 6,144 B; 1536 int8 = 1,536 B; 1536 binary = 192 B; DERIVED).

**Config and versioning:** one `embed` block (provider, model_id, revision null, input_type pair, output_dimension, embedding_type, truncate, normalize, preproc_version) → cache key per text (C3 key + E2 fields) and `embed_hash` for the index folder. The resolved model id from `COHERE_EMBED_MODEL_ID` is written into the run config.

**Monitoring and feedback:** the embedding canary (foundation §8.4) runs on demand: 3 fixed strings, cache bypassed, cos to recorded sample 0 must stay ≥ the tolerance from F; alerts also on a dimension change, a norm shift, a new error class, or `truncate` events. A failure goes to the error-analysis log and, if confirmed, becomes a T1 test (e.g. "query embedded with `search_document`").

**Place in the lifecycle:** Analyze — read the retriever spans of the seed questions (`error-analysis`, `trace-data-analysis`). Measure — the code-based evaluators and Hit@k/MRR (`code-based-evaluators`, `rag-evaluation`). Improve — dimension/type choices only after measuring (`improving-llm-agents`: caching and right-sizing). dev → CI → monitor: notebook → `replay` test + stale-key test → canary (`ci-cd-evals`, `llm-observability`).

---

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| LLM per task | none (Groq `openai/gpt-oss-20b` and Claude not used) | — | — | — | 0 | — | yes: P4 has no generation, rewriting or judging; adding an LLM would teach nothing here |
| Default embedder | Cohere `embed-v4.0` via `cohere` SDK | SDK 7.2.0 (keep) | yes | no (API; replay offline) | 12 calls, ~100k tokens ≈ $0.012 (price UNVERIFIED) | SDK MIT; service terms | yes (D-03) |
| Newer embedder | Cohere `embed-v5.0-pro` / `-fast` | — | — | no | not used | — | **needs a decision later** (switching re-embeds everything; keep v4.0 for the course) |
| Local fallback | `sentence-transformers/all-MiniLM-L6-v2` | snapshot `1110a243…` | yes (cache, 175 MB folder) | yes | 0 | Apache-2.0 | yes |
| Wrong-model demo | `sentence-transformers/paraphrase-MiniLM-L3-v2` | `4ca70771…` | yes (68 MB) | yes | 0 | Apache-2.0 | yes |
| Cross-encoder | `cross-encoder/ms-marco-MiniLM-L-6-v2` | `233902d2…` | yes (88 MB) | yes | 0 | **UNVERIFIED** (no README in cache) | yes |
| Embedding library | `sentence-transformers` | 6.1.0 (keep) | yes | yes | 0 | Apache-2.0 | yes |
| Maths, charts, PDF | `numpy` 2.5.3, `plotly` 7.1.0, `pymupdf` 1.26.7 | keep | yes | yes | 0 | BSD / MIT / AGPL | yes |
| Framework core | `langchain-core` | 1.6.6 | no | yes | 0 | MIT | yes (LLMOps notebook only; D-32) |
| Cohere via LangChain | `langchain-cohere` | 0.6.0 | no | — | — | MIT | **no**: needs cohere < 6; use `CachedEmbeddings` |
| FAISS wrapper | `langchain-community` | — | no | — | — | MIT | read-only (source cited); FAISS belongs to P5 |
| Hosted tracing | `langsmith` | 0.14.4 | no | SDK yes | `LANGSMITH_API_KEY`; free plan | MIT | yes, corpus D only |
| Local tracing | JSONL (`llmops/trace.py`) + `arize-phoenix-otel` 0.17.2; viewer `uvx arize-phoenix@20.19.0 serve` | as foundation | no | yes | 0 | ours / Apache-2.0 / ELv2 | yes |
| Cache, cost, privacy | `study/llmops/` package | plan (foundation §10) | **not built** | yes | 0 | ours | yes; **blocks the LLMOps notebook** |
| Tests | `pytest` | 9.1.1 | yes | yes | 0 | MIT | yes |
| Optional data | BeIR FiQA (HF cache, 27 MB) | `979c07a7…` | yes | yes | 0 | CC-BY-SA-4.0 (dataset README) | optional Full demo only ("leaderboard domain ≠ your domain"); not needed |
| Not needed | `faiss-cpu`, `scikit-learn` | — | sklearn yes | — | — | — | P4 uses NumPy; FAISS decided in P5 |

Install lines (do not run until the LLMOps notebook is built; same as the foundation):

```text
uv add --group llmops langchain-core==1.6.6 langsmith==0.14.4
uv add --group llmops arize-phoenix-otel==0.17.2
uvx arize-phoenix@20.19.0 serve      # on demand, not a project dependency
```

Keys: `COHERE_API_KEY` (present). `LANGSMITH_API_KEY` is already named in `.env` (value not read). No Groq or Anthropic key is used by P4.

---

### 11. Open questions for Yash (preferences only)

1. Keep **embed-v4.0** for the whole course even though embed-v5.0 is listed? (recommended: **yes**; a switch re-embeds everything and is its own experiment)
2. Run the 12 recorded Cohere calls (≈ $0.01, 12 of 1,000 trial calls) when the LLMOps notebook is built? (**yes** recommended)
3. Include the optional FiQA "leaderboard vs your domain" demo in Full? (**no** recommended; it adds a dataset and time without changing a decision)
4. Interview item: AIQ-04 **Q15** (prefixes), or Q6 (bi-encoder)? (Q15 recommended; Q11 is tutor-reserved)

---

## Concept P5: Vector search

**The answer, in one screen.** The existing P5 lesson (`concepts/P5_vector_search.md`) is strong on exact search and is backed by a full FACTS file. The gaps are almost all on the **ANN side** and the **"what a store adds"** side: the lesson names HNSW and IVF in one UNVERIFIED table but never teaches how they work, never says that "recall" there means something different from P6's Recall@k, never measures anything, and never shows the defaults that libraries pick for their knobs. Two facts that were UNVERIFIED in October can now be closed from primary sources: FAISS `IndexFlatL2` returns **squared** distances, and `faiss-cpu` ships Windows/Python 3.12 wheels. **Recommendation:** NumPy exact search stays v0. For the ANN comparison, build IVF from scratch in NumPy first (no install), then add **`faiss-cpu==1.15.1`** in an optional group to run real HNSW and IVF. Do **not** use `hnswlib`: its last PyPI release is from December 2023 and it ships source only, so Windows needs a C++ compiler.

---

### 1. Sources checked

**Book pages (opened with PyMuPDF 1.26.7; cited 1-based; paraphrased only)**

| Page | What it says (our words) | Used for |
|---|---|---|
| Ch1 p.6/14 | Step 5 stores every vector in a database built for similarity search. It names FAISS as the popular choice and says it stays very fast with millions of entries. It explains this with a library sorted by topic: you walk to the right neighbourhood and browse | The book's whole model of vector search. The library analogy is, in fact, the **IVF idea** (search only the nearby shelves), though the book never names it |
| Ch1 p.7/14 | The 5-step preparation sketch; step 5 is "store the vectors for fast similarity search" | Where P5 sits |
| Ch1 p.8/14, p.9/14, p.10/14 | The query is embedded the same way; the nearest chunks come back (top-K); the text is then fetched | One score per chunk (MC-002); the metadata lookup. Already in the lesson; **missing from the 02 card** |
| Ch1 p.13/14 | Query latency is one embedding, one vector search and one LLM call | Exact-search latency is the small part |
| **Ch2 p.9/11** (new) | For a large table, the store grows linearly with rows; FAISS is said to search millions in under a second; the bigger worry is the embedding cost | **Not cited anywhere in P5 or 02.** It is the book's only statement about scale, and it matches our measurement: search time grows linearly, and index-time embedding cost is the real bill |
| Ch2 p.5/11 | Step 4 stores record vectors in a vector store | Context only |
| App p.16/23 | Glossary: FAISS is called a vector database built for very fast nearest-neighbour search | The "FAISS is a database" claim (DV-04) |
| App p.21/23, p.22/23 | Glossary: similarity search; Top-K retrieval (with a redundancy warning); Vector Database / Vector Store as a searchable library of meaning | Terms |
| Whole-book scan (25 PDFs) | **0** hits for "HNSW", "IVF", "inverted file", "product quantization", "brute", "euclidean", "L2", "dot product", "inner product". "approximate" appears 4 times, all in the ordinary sense (Ch3 p.11, Ch6 p.5, p.9, Ch8 p.1). "exhaustive" once (Ch14 p.4, about hierarchical search) | **Confirmed: ANN is not in the book**, nor is any distance name |

**Repo (`upstream/RAG_Techniques` @ `009adba2…`, cells 0-based; all opened)**

| Cell / line | What it shows |
|---|---|
| `helper_functions.py` L4, L48–L76 | `encode_pdf`: PyPDFLoader → splitter 1000/200 → `OpenAIEmbeddings()` (L73) → `FAISS.from_documents` (L74). No distance, no index type, no k |
| `simple_csv_rag.ipynb` cell 12 | Hand-built `faiss.IndexFlatL2(...)` + `InMemoryDocstore()` + empty `index_to_docstore_id`: the index holds vectors, the docstore holds text |
| `simple_csv_rag.ipynb` cell 16 | `vector_store.as_retriever()` with no k (default 4) |
| `dartboard.ipynb` cell 9 | `documents=documents*5`: every page loaded 5 times (ties by construction) |
| `dartboard.ipynb` cell 13 | Raw `index.search`, then row → `index_to_docstore_id` → `docstore.search`; the query is embedded with `embed_documents` |
| `dartboard.ipynb` cell 23 | Oversamples `k = num_results × oversampling_factor`, then `reconstruct_batch`, then `1 − np.dot(...)` as a cosine distance on an L2 index (assumes unit vectors) |

**Course files read:** CLAUDE.md; `study/research/RESEARCH_PROMPT.md`; `LLMOPS_FOUNDATION.md` (all); the P3 pilot (`P3_bm25_gap_audit.md`, `P3_bm25.html` headings, `P3_bm25_verify.ipynb` structure, `bm25_fit_check.py` docstring); `study/FORMAT.md`; both WRITING_STYLE files, `visual-learning-writer/SKILL.md` and `HTML_VISUAL_SPEC.md`; 02 P5 card (L246–L265), §4 Gate 1→2 (L1121–L1127), D2/D3 cards; 03 P5 rows; 04 P5 row (L126) and DV-04 (L993); 06 §1 non-goals, §2.2, §2.4, §3.1, §7.5; `concepts/P5_vector_search.md` (all); `concepts/C4_dense_retrieval.md` (P5 links, ties, 97 vs 91 chunks); 08 Part 4 rows on FAISS; `sources/EXTERNAL_RESOURCES_REVIEW_2026-10-09.md` (P5 row, §8 rows, row 31); `sources/verification/P5/P5_FACTS.md` and `p5_measure.py` (`top_k`, L44–L54); `progress/concept_tracker.csv`; `progress/misconception_log.md` (MC-002, MC-005); `.claude/skills/rag-evaluation`, `llm-observability`, `improving-llm-agents` (headings and key lines; paraphrased); `sources/coach/transfer_seed_bank.md` (only to avoid seed collisions; nothing copied).

**AE book:** the external review maps no AE section to P5. Not opened for P5.

**Interview repo (AIQ @ `e080df2`, MIT, "Copyright (c) 2026 Om"):** `04-rag-and-retrieval/questions.md` Q8 (exact vs ANN), Q11 (metric choice), Q20 (HNSW M/ef), Q21 (HNSW vs IVF vs PQ), Q22 (choosing a vector DB), Q23 (pre- vs post-filtering); `12-coding-challenges/08_semantic_search_rag.py` (tutor-reserved; not used).

**External sources (external; opened 2026-10-17)**

| # | Source | What was tested / stated | Status |
|---|---|---|---|
| [P5-1] | Malkov & Yashunin, "Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs", arXiv 1603.09320 (v1 2016-03-30, v4 2018-08-14). https://arxiv.org/abs/1603.09320 | Layered proximity graph; each element's top layer drawn with exponentially decaying probability; search from the top layer; neighbour-selection heuristic; claims logarithmic complexity scaling and better results than earlier open-source vector-only methods. The abstract names no datasets | verified (abstract). Journal (IEEE TPAMI) **UNVERIFIED** |
| [P5-2] | Johnson, Douze & Jégou, "Billion-scale similarity search with GPUs", arXiv 1702.08734 (2017-02-28). https://arxiv.org/abs/1702.08734 | GPU k-selection at up to 55% of peak; 8.5× faster than prior GPU state of the art; brute-force, approximate and PQ search; 1B-vector k-NN graph in under 12 h on 4 GPUs | verified (abstract). GPU-only results: not our setting |
| [P5-3] | Douze et al., "The Faiss library", arXiv 2401.08281 (v1 2024-01-16, v4 2025-10-23). https://arxiv.org/abs/2401.08281 | Faiss as a toolkit to search, cluster, compress and transform vectors; maps the trade-off space; benchmarks the library | verified (abstract) |
| [P5-4] | Faiss wiki, "Faiss indexes". https://github.com/facebookresearch/faiss/wiki/Faiss-indexes | Index table: bytes per vector (Flat `4*d`; HNSWFlat `4*d + x*M*2*4`; IVFFlat `4*d + 8`; SQ8 `d`; PQ `ceil(M*nbits/8)`), exhaustive or not; IndexFlatIP "also for cosine (normalize vectors beforehand)"; IVF rule of thumb `nlist ≈ C·√n`, C about 10 | verified |
| [P5-5] | Faiss wiki, "MetricType and distances". https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances | METRIC_L2 returns **squared** L2 (no square root); cosine = inner product on normalised vectors; L2 on normalised vectors ranks the same, with ‖x−y‖² = 2 − 2⟨x,y⟩ | verified |
| [P5-6] | Faiss wiki, "Faster search". https://github.com/facebookresearch/faiss/wiki/Faster-search | IVF needs training; **default `nprobe` is 1**; search time grows about linearly with `nprobe`; `nprobe = nlist` equals brute force | verified |
| [P5-7] | Faiss source @ v1.15.1: `faiss/impl/HNSW.h`, `faiss/IndexHNSW.h`. https://raw.githubusercontent.com/facebookresearch/faiss/v1.15.1/faiss/impl/HNSW.h | Defaults: `efConstruction = 40`, `efSearch = 16`; `HNSW(int M = 32)` and `IndexHNSW(d = 0, M = 32, METRIC_L2)`; `IndexHNSWFlat(d, M, ...)` takes M explicitly | verified (source lines) |
| [P5-8] | hnswlib README, `ALGO_PARAMS.md`, LICENSE, `hnswlib/hnswalg.h` @ v0.8.0. https://github.com/nmslib/hnswlib | `'l2'` is squared L2; `'ip'` returns 1 − dot; M default 16, `ef_construction` 200; query `ef` default 10 (`hnswalg.h`); ef must be ≥ k; "M = 12–48 is ok for most use cases"; memory about M × 8–10 bytes per element; Apache-2.0 | verified |
| [P5-9] | pgvector README. https://github.com/pgvector/pgvector | Exact search by default with perfect recall; HNSW (better speed-recall, more memory and build time) vs IVFFlat (faster build, less memory, needs data first); defaults m 16, ef_construction 64, `hnsw.ef_search` 40; with approximate indexes the filter runs **after** the index scan; iterative index scans since 0.8.0 | verified (production store docs) |
| [P5-10] | Aumüller, Bernhardsson & Faithfull, "ANN-Benchmarks: A Benchmarking Tool for Approximate Nearest Neighbor Algorithms", arXiv 1807.05614 (2018; full version of a SISAP 2017 paper). https://arxiv.org/abs/1807.05614 and https://ann-benchmarks.com/ | Tests many algorithms over parameter grids on standard datasets; very different methods reach comparable quality–speed trade-offs. The site plots **recall** (fraction of true nearest neighbours found, averaged over queries) against **queries per second**, k = 10, "single queries"; includes hnswlib and faiss (IVF, IVFPQ, HNSW) | verified. Journal version (Information Systems 2020) **UNVERIFIED** |
| [P5-11] | Aumüller & Ceccarello, "The Role of Local Intrinsic Dimensionality in Benchmarking Nearest Neighbor Search", arXiv 1907.07387 (SISAP 2019). https://arxiv.org/abs/1907.07387 | Query difficulty varies with local intrinsic dimensionality; LID can be used to pick easy or hard query sets, and it changes how fast implementations run | verified (abstract) |
| [P5-12] | PyPI JSON for `faiss-cpu`, `hnswlib`, `usearch`, `numkong`, `langchain-core`, `langchain-community`, `langsmith` (https://pypi.org/pypi/<name>/json), read 2026-10-17 | Versions, dates, wheel files and sizes, licences (§10) | verified |
| [P5-13] | `faiss-wheels` README. https://github.com/faiss-wheels/faiss-wheels | Archived community builder; says upstream Faiss officially publishes PyPI wheels from **v1.14.2**; Windows x86_64 and arm64 wheels; OpenBLAS; CPU only; **an index built at one SIMD level may not load on another** | verified. Faiss's own INSTALL.md (opened) still names conda as "the supported way" and does not mention pip |
| [P5-14] | `langchain-core` 1.6.6 source (tag `langchain-core==1.6.6`): `vectorstores/in_memory.py`, `base.py`, `utils.py`. https://github.com/langchain-ai/langchain | `InMemoryVectorStore`: exact cosine over a Python dict; **filter applied before scoring** (L300–L309); ranking by `similarity.argsort()[::-1][:k]` (L317); `k = 4`; in the NumPy path a zero vector scores 0 with no error (NaN/Inf inputs only raise a warning). `VectorStoreRetriever`: `search_type = "similarity"`, empty `search_kwargs` (L970, L973). `_euclidean_relevance_score_fn = 1 − distance/√2` (L376–L388) | verified (source read as text, not run) |
| [P5-15] | `langchain_community` 0.4.1 `vectorstores/faiss.py`, in the learner's older venv (read as text) | `scores, indices = self.index.search(...)` (L417) with no square root before the Euclidean relevance function (L1270–L1272) | verified (read, not run) |

Two scratch probes were run in this session with the project NumPy 2.5.3 (no install, no API). They are **not course records**; the verify notebook must re-run and log them:
- toy scores `[0.70, 0.90, 0.80, 0.80, 0.80, 0.10]`, k = 2: `argsort()[::-1][:2]` (the `InMemoryVectorStore` line) gives `[1, 4]`; the course rule (ties by smaller id) gives `[1, 2]`.
- the whole-book term scan above.

---

### 2. Gap audit

Tracker (2026-10-17): P4, P5, P6, C3, C4 all `not_started`; P1 `exposed`. MC-002 open (P4/C4), MC-005 open (C4). 02 rates P5 fast-track **likely** (VAI L20: NumPy top-k in about 15 min; L2 vs cosine).

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | One query gives **one score per chunk**, shape (N,); a batch gives Q × N; chunks × chunks is not retrieval | lesson D.1–D.2; Part A; MC-002; Gate 2→3 trace | yes (D.1) | P5 (with C4) | no (MC-002 open) | core | Keep. Open with it (Short) and a score-column visual |
| 2 | Same model and same normalisation for the query; `input_type`/query prefix | A1, H.2 Q4 | partly (A1 key, H.2) | P4 / C3 / C4 | no | bridge | Two sentences where the query is embedded; link P4 and C4 |
| 3 | Cosine = dot on unit vectors; ‖q−x‖² = 2 − 2cos; metrics differ only when norms vary | D.5, Part F, Gate 1→2 | yes (D.5) | P4 | no | bridge | Short bridge with Part F's stretched vector; P4 owns the proof |
| 4 | Exact top-k: `argpartition` (O(N)), then sort only k | D.2, Gate 1→2 "NumPy top-k from memory" | yes | P5 | no (O1-Q06 not attempted) | core | Keep, Short |
| 5 | **Tie-aware cut**: take every id scoring ≥ the k-th score, sort by (−score, id), then cut to k. Sorting only the k that `argpartition` picked is not enough | D.3, J1, 06 §3.1 | **incomplete**: D.3 shows the result, never states the rule; J1's fix ("sort by (−score, id)") is the insufficient version | P5 | no | core | Teach the cut explicitly on a **toy array** (Short) |
| 6 | Tie rule on **string** `chunk_id` (06 §2.3, zero-padded `seq`) vs row index | 06 §3.1; C4 D.2 | missing in P5 (C4 covers it) | C4 | no | next | One line + link to C4 |
| 7 | float32 rounding and **near-ties**: a tie rule fixes exact equality only; BLAS order can flip scores 1e-7 apart on another machine | D.2 (1.00e-07 float32 vs float64), J1 | missing (number shown, meaning not drawn) | P5 | no | core (Full) | Full only: compare the smallest rank-k/k+1 gap (0.00170, S4) with 1e-7 |
| 8 | Metadata aligned by row; asserts `len(V) == len(meta)`, `meta[i].chunk_id` | D.4, J3 | yes | P5 (C3 builds on it) | no | core | Keep, Short |
| 9 | Pre-filter (mask to −∞) vs post-filter (`fetch_k`), shortfall; **selectivity** (share of chunks that pass) | D.4, J4 | yes for pre/post; **selectivity not named** | P5 / R2 | no | core | Add the word and the estimate "about selectivity × fetch_k survive"; R2 owns depth |
| 10 | **Filtered ANN**: post-filtering inside an ANN index starves results; pgvector filters after the index scan; iterative scans; exact on a small filtered subset is fine | Q23 interview; tool check | missing | R2 (D2 for scale) | no | bridge | Short paragraph + flow sketch; R2 link |
| 11 | Hidden store defaults: LangChain FAISS L2, k = 4, post-filter `fetch_k` 20; `as_retriever()` = `similarity` | B.1, D.5 | yes | P5 | no | core | Keep; add the two below |
| 12 | `InMemoryVectorStore` (langchain-core 1.6.6): exact cosine, **pre-filter**, k = 4, ties come out **largest index first** (`argsort()[::-1]`) | LLMOps notebook | **missing** | P5 | no | core | New row in the defaults table (Short); scratch probe re-run in the verify notebook |
| 13 | FAISS `IndexFlatL2` returns **squared** L2; LangChain's "relevance" `1 − d/√2` is applied to that squared value, so it goes **negative below cos ≈ 0.293** | D.5 (marked UNVERIFIED) | incomplete; now resolvable [P5-5], [P5-15] | P5 (C4 for score ≠ relevance) | no | core (Full) | Full: state it, with D-002 arithmetic; verify with faiss if installed |
| 14 | Exact cost: time ∝ N × d; memory N × d × 4 bytes; k barely matters; batching | D.6 | yes | P5 | no | core | Keep; interactive budget chart |
| 15 | **When exact is enough**: budget → N_max; QPS; memory wall | D.6, K, AIQ Q8 | yes, but budget is an assumption | P5 (D2 owns budgets) | no | core | Keep; correct AIQ Q8 with our CPU numbers |
| 16 | **IVF mechanism**: k-means cells (`nlist`), scan `nprobe` nearest cells; training; boundary misses; default nprobe 1 | D.7 one row | **missing** | P5 | no | core | Teach in Short with a 2-D toy diagram; build it in NumPy in the verify notebook |
| 17 | **k-means** (centroids, assign, update) | needed by IVF | missing | none in course (R5 uses clustering later) | no | bridge | Three-line bridge in the IVF section |
| 18 | **HNSW mechanism**: layered graph, greedy descent, beam `efSearch ≥ k`; knobs M, efConstruction | D.7 one row | **missing** | P5 | no | core | Short: one diagram + knobs; Full: defaults table across libraries |
| 19 | **Two meanings of "recall"**: ANN recall@k = overlap with the *exact* top-k; IR Recall@k (P6) = share of *relevant* items found | D.7 ("Recall@k of ANN against exact"), L.1 R-03 | **missing**; the lesson uses one word for both | P5 / P6 | no | core | Short, a highlighted note (like P3's tokens note) |
| 20 | Recall-vs-QPS (or latency) curve; how ann-benchmarks measures; one knob moves you along the curve | D.7, tool, LLMOps | missing | P5 | no | core | Short sentence + measured curve (verify notebook fills it) |
| 21 | PQ / scalar int8 / binary quantization; Matryoshka dimension cuts (Cohere `embed-v4.0`: 256–1,536) | review §3b note; T-01 key | partial (one row) | P5 → D2 | no | next (Full) | Full: memory arithmetic only; link D2 |
| 22 | **What a store adds beyond an index**: ids, persistence, updates/deletes, metadata filters, hybrid; the store is not the source of truth | A4, DV-04, Q22 | partly (FAISS vs DB row) | P5 / C3 / D3 | no | core (short) | One table: index library vs store vs our v0 files |
| 23 | Persisted ANN indexes are fragile (SIMD level, rebuild after deletes); we persist `vectors.npy`, not an index | C3, D3 | missing | C3 / D3 | no | next | One line + link |
| 24 | Duplicates crowd the top-k; dedup or diversity | D.3, J2 | yes | P5 / R4 | no | core (keep) | Keep; R4 link |
| 25 | **Hit@k, MRR** (to check that ANN does not hurt retrieval) | LLMOps notebook, tool | missing in P5 | P6 | no | bridge | One-line definitions where used; link P6 |
| 26 | **p50/p95** with a named percentile method; warm-up runs; machine-specific timing | LLMOps, tool, D.6 | missing (06 §7.5 has it) | D2 / 06 §7.5 | no | bridge | Two sentences where timing appears |
| 27 | Retrieval quality vs answer quality: ANN can only change retrieval | D.7 last line | yes | P6 / M2 | no | core (keep) | Keep |
| 28 | k trade-off (both sides; search ×1.00 vs prompt ×1.86) | A2, D.6, MC-005 | yes | C4 | no | bridge | Keep one line |
| 29 | Book scale vs ours: Ch2 p.9/11 (linear growth; embedding cost is the bigger worry) | B.2 | missing (page not cited) | P5 | no | core | Add to "book vs measurement" |
| 30 | Synthetic random vectors are a poor stand-in for real ones when testing ANN (difficulty depends on local intrinsic dimension) | verify notebook design | missing | P5 | no | core (Full) | Full note; label every synthetic number |

**Running example decision:** the new lesson uses **v0's 97 per-page chunks** (06 §3.1; C4 and the P3 verify notebook already use them) with D-002, not P5's old 91 cross-page windows. On 97 chunks D-002's evidence is rank 3 and rank 1 vs 2 differ by only 0.0093 (C4 S3 and D.3 table), which shows near-ties naturally. The existing lab (`labs/P5_vector_search_lab.ipynb`, 91 windows, fingerprints verified) stays as it is; the lesson says in one line why the lab's numbers differ (C4 already explains it).

---

### 3. Quiz coverage

No `study/questions/P5_questions.md` exists. Needed items (titles only; new scenarios; checked: none reuses a seed-bank scenario):

| id | set | Title (one short question) | Taught in (Short) |
|---|---|---|---|
| P5-PRE-01 | pre | For one question and 97 chunks, how many similarity numbers does retrieval compute? | score column |
| P5-PRE-02 | pre | If you double k, does exact search get slower? | cost section |
| P5-PRE-03 | pre | When you use FAISS, where do the chunk text and page live? | store vs index |
| P5-R-01 | main | After the question is embedded, what exactly does retrieval compute, and in what shape? (MC-002 check) | score column |
| P5-R-02 | main | Which three choices does a LangChain FAISS store make if you set none? | defaults |
| P5-R-03 | main | What does an ANN index give up for speed, and what do you compare it against? | ANN |
| P5-R-04 | main | "Recall 0.95" on an ANN benchmark and "Recall@4 = 0.95" on our eval set: what does each count? | two recalls note |
| P5-R-05 | main | In HNSW, what do M and efSearch control? | HNSW |
| P5-R-06 | review | Name three things a vector store adds that a FAISS index alone does not | store vs index |
| P5-A-01 | main | Scores and k given (toy, ties at the boundary): which ids, in order? | tie-aware cut |
| P5-A-02 | main | The corpus doubles from 100,000 to 200,000 chunks: what happens to time and memory per query? | cost |
| P5-A-03 | main | How many bytes does a float32 index of 50,000 × 1,024 vectors need? | memory formula |
| P5-A-04 | main | Exact top-5 and an ANN top-5 are given: what is the ANN recall@5? | two recalls |
| P5-A-05 | main | Top-10 list with pages, filter "page ≥ 20", post-filter at fetch 10: how many results come back for k = 4? | filters |
| P5-A-06 | review | One chunk vector is stretched to length 2: rank by dot, cosine and L2 | bridge (Part F) |
| P5-T-01 | main | 2 million tickets at 1,536 dims, 50 ms budget: what do you do first? (existing practice item) | when exact is enough, ANN |
| P5-T-02 | main | A tenant filter keeps 1% of 200,000 vectors: exact on the subset, or ANN with a post-filter? | filtered ANN |
| P5-R-07 | interview, `source=AIQ-04-Q8` | AIQ 04 Q8 verbatim: "When do you need approximate nearest neighbour search instead of exact search?" with the MIT notice; our answer corrects the "single-digit ms" claim for one CPU query (≈ 61–64 ms at 1M × 384, derived from P5 S8) | when exact is enough |

Cap check: P5 has room for **1** external item (external-item cap). AIQ 04 Q8 is that item. Q11, Q20, Q21 and Q23 are **not** kit items; the lesson must simply make them answerable (they are good self-practice after the course).

Every key point above must be answerable from **Short**. The current lesson fails that for R-04, R-05, A-04, T-02 and the interview item (ANN and filtered-ANN content is missing or UNVERIFIED), so the new Short must carry: the two recalls, IVF and HNSW in one screen each, filtered ANN, and the corrected exact-latency numbers.

---

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| E1 | 02 P5 card, Book line | Lists only Ch1 p.6–7/14, App p.16/23, p.22/23. Misses Ch1 p.8–10/14 (query embedding, top-K, text lookup), App p.21/23 (similarity search) and **Ch2 p.9/11** (linear growth; embedding cost) | Add them |
| E2 | 02 P5 card, Repo line | "`dartboard.ipynb` cell 23 (raw FAISS internals)": the raw `index.search` and the row → docstore map are in **cell 13**; cell 23 is oversampling + `reconstruct_batch` + cosine-as-`1 − dot` on an L2 index | Cite cells 13 and 23, with what each shows |
| E3 | 04 P5 row (L126) | Still has the five errors recorded in P5_FACTS §3 (pages missing; "flat L2 default" attributed to `simple_rag` cell 10; IndexFlatIP check; "book silent on metadata"; `json_rag` cell 17 vs 21) | Apply P5_FACTS §3 in the 04 correction pass |
| E4 | 04 DV-04 (L993) | "FAISS is a flat in-memory index" is wrong: FAISS is a library with flat, IVF, HNSW, PQ and other indexes [P5-3], [P5-4]; only the repo uses the flat one | "FAISS is an index library; the repo uses its flat L2 index; text lives in a separate docstore" |
| E5 | 04 P5 check | "NumPy exact vs FAISS `IndexFlatIP`": now runnable if faiss is added. Run **both** IndexFlatIP (= cosine on unit vectors) and IndexFlatL2 (the repo's default), and expect squared L2 | Update when the verify notebook exists |
| E6 | P5 lesson header, Part E, H.3, I; 06 §1 non-goals | ANN scale is sent to **D4**, which is security (review row 31(b) found this for P5 and C3) | Point to **D2** (latency budgets) and **D3** (index versioning, re-indexing) |
| E7 | P5 lesson D.5 and Verification log | "Whether FAISS `IndexFlatL2` returns squared distances is UNVERIFIED" | Faiss docs say squared [P5-5]; hnswlib `'l2'` is squared too [P5-8]. LangChain's FAISS wrapper passes the raw value (L417) into `1 − d/√2` (L1272) [P5-15]. So its "relevance" at cos 0.8 is 0.7172, not 0.5528 (P5_FACTS S7 arithmetic), and it is **negative** for any cos below 1 − √2/2 ≈ 0.293 (derived). Still to confirm by running faiss |
| E8 | P5 lesson D.3 and J1 | J1's fix "sort by (−score, chunk_id)" is ambiguous: sorting only `argpartition`'s k is not enough when ties straddle the cut (review P5 row; `p5_measure.py` L49–L53 does the right thing) | State the tie-aware cut as the rule |
| E9 | P5 lesson D.7 | Every ANN property is UNVERIFIED and there is one word "recall" for two different measures | Replace with the sourced mechanism (§5) and the "two recalls" note |
| E10 | 08 L326 | "faiss-cpu: cp312 wheels exist (UNVERIFIED)" | Verified: `faiss_cpu-1.15.1-cp312-cp312-win_amd64.whl`, 16.29 MB [P5-12] |
| E11 | P5 lesson G.2 corr. 3 / H.3 | "faiss … is not to be added": no such decision exists in 08 Part 4 (D-32 allows frameworks; libraries need Yash's OK) | Reword as "not installed; adding it is decision Q1 below" |
| E12 | AIQ 04 Q8 (external, MIT) | "Single-digit milliseconds up to roughly a million vectors" holds with GPU/SIMD or batching (its own qualifier); one CPU query at 1M × 384 is about 61 ms (linear from 6.092 ms at 100k) or 64 ms (from 32.2 ms at 500k), P5 S8, derived. Batched (0.538 ms/query at 100k) it is about 5.4 ms (derived) | Already in review §8; our answer key carries it |

---

### 5. What the research says

**HNSW [P5-1], [P5-7], [P5-8], [P5-9].**
- **The study.** Malkov and Yashunin build a stack of proximity graphs. Every vector is in the bottom layer; each higher layer keeps a random, exponentially thinner subset. A query starts at the top, walks greedily to the closest neighbour, drops a layer when it cannot improve, and at the bottom keeps a beam of the `ef` best candidates.
- **The result.** The authors report logarithmic scaling and better speed–recall than earlier open-source vector-only methods (abstract; datasets not named there).
- **Its limits.** Recall is below 1 and depends on M, efConstruction and efSearch; memory grows with M (hnswlib: about M × 8–10 bytes per element, on top of the vector); `ef` must be at least k.
- **The defaults differ a lot between libraries** (verified source/docs):

```
                 M     efConstruction   efSearch (query)
faiss 1.15.1     32*   40               16      (* IndexHNSW default; IndexHNSWFlat needs M)
hnswlib 0.8.0    16    200              10
pgvector 0.8.x   16    64               40
```
- **For the project:** the "hidden defaults" theme of P5 extends to ANN: an untuned efSearch of 10–16 at k = 4 is a choice someone else made for you. Any ANN arm must state all three numbers and its measured recall.

**IVF [P5-4], [P5-6].**
- **The mechanism.** k-means splits the vectors into `nlist` cells. A query scans only the `nprobe` cells whose centroids are nearest. The scanned share is about nprobe / nlist when cells are balanced (assumption). A true neighbour in an unscanned cell is missed silently.
- **The facts.** IVF needs a training step; the default `nprobe` is **1**; search time grows about linearly with nprobe; `nprobe = nlist` gives brute-force results. Rule of thumb `nlist ≈ 10·√N`.
- **For the project:** at N = 97 that rule gives about 98 cells, one vector per cell. IVF has nothing to offer at our size, which is a clean way to show "exact is enough".

**FAISS and metrics [P5-3], [P5-5], [P5-13].**
- FAISS is a library of index types, not a database. `METRIC_L2` returns squared L2; cosine is inner product on normalised vectors; L2 on normalised vectors ranks the same.
- Bytes per vector: Flat `4·d`; SQ8 `d`; PQ `M·nbits/8` (lossy). For 1,536 dims: 6,144 B float32, 1,536 B int8, 192 B binary (derived).
- `faiss-cpu` wheels: official on PyPI from 1.14.2 (per [P5-13]); CPU only; an index built at one SIMD level may not load at another. **For the project:** persist vectors (`vectors.npy`, C3), rebuild any ANN index at load time.

**How ANN is evaluated [P5-10], [P5-11].**
- **The study.** ANN-Benchmarks runs many libraries over parameter grids on fixed datasets (k = 10) and plots recall against queries per second.
- **The result.** Very different designs reach comparable quality–speed trade-offs.
- **Its limits.** "Recall" there is overlap with the exact neighbours, not relevance. The site reports single-query throughput on its own hardware. Query difficulty depends on local intrinsic dimensionality, so random synthetic vectors do not predict behaviour on real embeddings.
- **For the project:** measure ANN recall@k against **our** exact top-k on **our** queries; then check that Hit@k and MRR (P6) do not drop; report p50/p95 latency and index bytes. Label synthetic-scale numbers as synthetic.

**Production stores today [P5-9], [P5-14], AIQ Q22–Q23.**
- A store adds ids, persistence, inserts/deletes, metadata filters (pre, post, or filter-aware) and often hybrid search. pgvector starts exact (perfect recall) and filters **after** an approximate index scan unless iterative scans are on (0.8.0+).
- LangChain `InMemoryVectorStore` is exact cosine with a pre-filter, k = 4, and ties ordered largest index first; `VectorStoreRetriever` defaults to `similarity`, k = 4.
- **For the project:** v0 is "exact + pre-filter + tie-aware cut", which is what the small stores do anyway, plus a stated tie rule.

**Current practice (2024–2026), pitfalls with evidence.**
- Exact first, ANN only when a stated budget breaks (pgvector default exact; AIQ Q8/Q21 suggest brute force up to about 1M vectors, which our CPU numbers qualify).
- Pitfalls: silent recall loss (nothing errors) [P5-6]; library defaults far from tuned values (table above); filtered ANN starvation [P5-9]; metric/normalisation mismatch [P5-5]; non-portable persisted indexes [P5-13]; random-data benchmarks [P5-11]; tie order left to the library [P5-14].

**How to evaluate (P5).** Ground truth is exact search. Primary: ANN recall@k vs exact. Guards: Hit@4 and MRR on the eval items (retrieval quality); p50/p95 latency (nearest-rank, warm-up excluded, machine named); index bytes; build time. Answer quality is untouched by the index choice except through retrieval, so no answer metric is needed in P5.

**Interview questions (AIQ 04):** Q8 exact vs ANN (kit item); Q11 metric choice; Q20 HNSW knobs; Q21 HNSW vs IVF vs PQ; Q23 pre- vs post-filtering. Q22 (choosing a store) is a D-phase topic.

---

### 6. Lesson blueprint

Output: `study/lessons/P5_vector_search.html` (Short / Full), `study/reading/P5_vector_search.md` (short, FORMAT §3), `study/questions/P5_questions.md`. Order as in P3: answer first → theory in one read → formula sheet → steps → verify → apply → check.

**The answer first (draft, 5 sentences).**
1. After your question is embedded, vector search gives every chunk one similarity score and keeps the k highest, so 97 chunks give 97 numbers, not a table.
2. Exact search does this with one matrix–vector product and a partial sort, finds the true top-k every time, and on our 97 chunks takes far less than a millisecond.
3. The k-th place needs a written tie rule, and the chunk text and page must stay aligned with the vector rows, or results change between runs and citations point at the wrong page.
4. Every store also makes choices you did not write down (distance, k, filter order, tie order), and those choices change which chunks the LLM sees.
5. Approximate indexes such as IVF and HNSW skip most vectors to go faster, at the price of missing some true neighbours, so you only use them when exact search breaks a stated latency or memory budget, and you measure what they miss against exact search.

**The theory in one read (12 linked ideas).**

| # | Idea | Formula / rule |
|---|---|---|
| 1 | One score per chunk | `s = V q`, V (N, d), q (d,), s (N,) |
| 2 | Metric bridge (P4) | unit vectors: `cos = q·x`, `‖q − x‖² = 2 − 2·cos` |
| 3 | Exact top-k | `argpartition(−s, k−1)[:k]`, then sort; cost O(N·d) per query |
| 4 | Tie-aware cut | `S = {i : s_i ≥ s_(k)}`; order by (−s_i, id_i); keep k |
| 5 | Rows and metadata | row i ↔ `meta[i]`; assert `len(V) == len(meta)`, `meta[i].chunk_id` |
| 6 | Filters | pre: `s_i = −∞` outside the filter; post: keep passers among `fetch_k`; expected passers ≈ selectivity × fetch_k |
| 7 | Hidden defaults | LangChain FAISS: L2 (squared), k 4, post-filter 20; InMemoryVectorStore: cosine, k 4, pre-filter, ties largest-index first |
| 8 | Cost and budget | time ≈ c·N·d; memory = 4·N·d bytes; `N_max = budget / (c·d)` |
| 9 | IVF | scanned share ≈ nprobe / nlist; `nlist ≈ 10√N`; default nprobe 1 |
| 10 | HNSW | greedy descent; beam `efSearch ≥ k`; extra memory ≈ M × 8–10 B per vector |
| 11 | Two recalls | ANN recall@k = \|ANN_k ∩ Exact_k\| / k; IR Recall@k (P6) = relevant found / all relevant |
| 12 | Index vs store | index = vectors → row ids; store = + ids, text, metadata, persistence, updates, filters |

**Formula-sheet items:** ideas 1–4, 6, 8–11; bytes table (float32 4·d, int8 d, binary d/8); `rel_LC = 1 − d²/√2` and the 0.293 crossing (Full); percentile method named (nearest-rank).

**Step-by-step outline (running example: climate PDF, v0's 97 per-page chunks, MiniLM, question D-002 "In what year was the Paris Agreement adopted?").** Corpus choice: the course corpus, because v0 uses it; ANN scale steps need more vectors, so they add **labelled** synthetic clustered vectors.
1. Embed the question with the same model, normalised: q (384,).
2. Score: `V @ q` → 97 numbers. Show the top-10 table with gaps (rank 1 vs 2: 0.0093; evidence at rank 3, C4 S3).
3. Partial sort for k = 4; then the tie-aware cut on a toy array with a boundary tie (why sorting the picked k is not enough).
4. Attach `meta`: page-cited results; one misalignment demo (one deleted row shifts every page).
5. Filter "page ≥ 25": pre vs post (counts re-measured on 97 chunks by the verify notebook).
6. The defaults table: FAISS wrapper vs InMemoryVectorStore vs our v0.
7. Cost: measured time per query at 97 → projected to 100k and 1M; memory; batching. Budget slider gives N_max.
8. IVF on the 2-D toy: cells, nprobe = 1 misses a neighbour, nprobe = 3 finds it. Then the verify notebook's IVF-in-NumPy recall@4 vs nprobe on real climate vectors.
9. HNSW: layer diagram; efSearch moves you along the recall–latency curve (curve from the verify notebook; empty until run).
10. Decision: v0 stays exact; what would change that (budget, QPS, memory), and the recall report any ANN arm must ship with.

**Visuals that earn their place.**

| Visual | The one thing it shows |
|---|---|
| Score column (SVG): one query arrow → 97 bars, k-cut line | One score per chunk, not a matrix (MC-002) |
| Toy tie strip with a k slider | Which ids the tie-aware cut keeps; the naive pick differs |
| Pre vs post filter (two lanes of the same top-20, filtered) | Why post-filtering can return fewer than k |
| Log-log latency vs N (measured S8 points + linear projection), budget and d controls | Where exact search crosses a budget; k does not move it |
| IVF 2-D toy (points, cells, query, nprobe slider) | Speed comes from skipping cells; misses come from the cell border |
| HNSW layers (static SVG) | Greedy descent from sparse to dense layers |
| Recall vs latency curve (from the verify notebook) | One knob slides along a trade-off; recall < 1 is silent |
| Decision flowchart: exact → exact + batch → ANN + recall report | When to switch |

**Full only:** squared-L2 relevance formula and negative scores; float32 near-ties; PQ and quantization memory arithmetic; Matryoshka dimension cuts; library default table; filtered-HNSW islands and iterative scans; persistence and deletes; ann-benchmarks method and LID caveat; the old 91-window numbers vs 97.

---

### 7. Verify notebook plan

`study/notebooks/P5_vector_search_verify.ipynb`, built like `P3_bm25_verify.ipynb`: a setup cell with `check()` and tolerances, one section per lesson section, a final PASS/FAIL/SKIPPED count. **No LLM or API call.** Offline (`HF_HUB_OFFLINE=1`). faiss sections **SKIP** cleanly if `faiss` is not importable.

| § | Recomputes | Data | Code |
|---|---|---|---|
| 1 | Shapes `V` (97, 384), `q` (384,), `s` (97,); 97 × 384 × 4 = 148,992 B; Q × N for a batch | 97 v0 chunks (07 chunker), MiniLM pinned snapshot | NumPy |
| 2 | D-002 top-10, gaps, evidence rank (must equal C4 S3: rank 3, gap 0.0093) | same | `top_k` |
| 3 | `top_k` == brute force on 300 tie-heavy random arrays × k ∈ {1, 4, 10}; naive variants (argpartition only; sort the picked k; `argsort()[::-1]`) and how often each differs | toy arrays (seeded) | NumPy |
| 4 | Misalignment demo; asserts | 97 chunks | NumPy |
| 5 | Pre vs post filter shortfall counts over the 10 draft seeds D-001…D-010 + 33 page-head queries (43) | 97 chunks | NumPy |
| 6 | Defaults: InMemoryVectorStore ranking rule replayed in NumPy (`argsort()[::-1]`); LangChain relevance on squared L2 at cos 0.8 and D-002's top score; the 0.293 crossing | arithmetic + 97 scores | NumPy; faiss `IndexFlatL2` squared-distance check if installed |
| 7 | Exact timing: N ∈ {97, 1k, 10k, 100k, 200k}, d ∈ {384, 1536}, k 4 vs 8, batch of 100; median of repeats; p50/p95 nearest-rank; Plotly log-log | synthetic **clustered** unit vectors (labelled) + real V | NumPy, `time.perf_counter` |
| 8 | IVF from scratch: NumPy k-means (seeded Lloyd), recall@4 vs exact for nprobe 1…nlist; vectors scanned | ~700 climate sentence windows (300 chars, stride 100) + the 43 queries; then 100k synthetic clustered | NumPy |
| 9 | faiss `IndexIVFFlat` and `IndexHNSWFlat`: recall@4/10 vs nprobe and efSearch; latency; `faiss.serialize_index` bytes; build time | same sets | faiss (optional) |
| 10 | Filtered ANN: HNSW post-filter at 1% selectivity vs exact on the subset (result length, recall) | 100k synthetic | faiss (optional) |
| 11 | Hit@4 / MRR exact vs ANN on the draft seeds (shows retrieval metrics unchanged or not) | 97 chunks | P6 functions (bridge) |

Writes `sources/verification/P5/P5_FACTS_v2` style outputs (a new FACTS run; lesson numbers come only from it). **Runtime:** a few minutes on the i7 laptop (estimate; the 200k × 1,536 cell holds about 1.2 GB, so cap N there at 200k). Every machine-specific number is labelled.

---

### 8. Apply-it tool plan and real-world checklist

`study/tools/vector_search_check.py`: "Is exact search enough for MY documents, and is my store set up safely?" Same shape as `bm25_fit_check.py` (CLI + importable `run_check`, Markdown report).

- **Inputs:** `--docs` (PDF/TXT/MD), `--questions` (the same `.txt`/`.jsonl` format as `bm25_fit_check`, with optional `expect`), `--embedder minilm` (default) or `cohere` (replay only, through `study/llmops/`), `--k 4`, `--budget-ms 10`, `--qps 1`, `--filter "page>=N"` (optional), `--grow N` (projected corpus size), `--ann` (faiss, if installed).
- **Outputs:** report sections Collection · Speed and memory · Ties and near-ties · Filters · ANN (optional) · Checklist · Recommendation.

| # | Check | Auto / manual |
|---|---|---|
| V1 | Vector norms all ≈ 1 (else dot, cosine and L2 disagree) | auto |
| V2 | Query and documents embedded with the same model id and the right input type | auto (manifest) / manual for other stores |
| V3 | `len(V) == len(meta)` and each row's `chunk_id` matches | auto |
| V4 | Exact top-k equals a brute-force reference on your queries | auto |
| V5 | Exact ties or near-ties (< 1e-6) at the k-th place, per query | auto |
| V6 | Duplicate or near-duplicate chunks (hash; cosine > 0.98) | auto |
| V7 | Measured p50/p95 per query on this machine; projected at `--grow`; N_max for the budget | auto |
| V8 | Index memory now and at `--grow` (float32; int8 shown) | auto |
| V9 | Post-filter shortfall rate at your filter; pre-filter result | auto (if `--filter`) |
| V10 | ANN recall@k vs exact at the chosen params, and the default params | auto (with `--ann`) |
| V11 | Hit@k / MRR for questions with `expect` | auto |
| V12 | Which defaults your real store uses (metric, k, filter order, tie order, efSearch/nprobe) | manual: read the store's docs/source; the report lists what to look for |

**Recommendation logic:** exact if p95 × projected growth stays under the budget and memory fits; "exact + batching" if only throughput fails; ANN (HNSW via faiss) only if both fail, with the required recall@k ≥ the target you set and a re-check after bulk changes; "fix first" if V1, V3 or V4 fails; "too little data" if fewer than 5 questions.

---

### 9. LLMOps notebook plan

`study/notebooks/P5_vector_search_llmops.ipynb`. Application map row "1 · P2–P3, P5–P6": no external calls; read-only retriever wrappers; ranked lists and scores; Hit@k/MRR on toy sets; p50/p95; T1 metric tests.

- **Framework build (after the mechanism).**
  - `langchain_core.vectorstores.InMemoryVectorStore` over the 97 chunks with a local MiniLM `Embeddings` class → maps to steps 1–2 (embed, score).
  - `.as_retriever()` → `VectorStoreRetriever` (`similarity`, k = 4): set k from the config, never the default.
  - A small `BaseRetriever` subclass wrapping our `search()` (exact, pre-filter, tie-aware cut) → steps 3–5.
  - **Defaults the lesson warns about:** k = 4; tie order largest-index first; a zero vector scores 0 with no error; `similarity_score_threshold` scores are not calibrated; the FAISS wrapper (read-only source cell; `langchain-community` not installed) uses squared L2, post-filter `fetch_k` 20.
- **Caching:** zero external calls by default. MiniLM vectors cached by content (C3 key). Optional Cohere arm: **replay only** from vectors recorded by C3; if recorded fresh, about 3 `embed` calls (97 documents in 2 batches of ≤ 96, the queries in 1). Runs fully in `replay` mode through `study/llmops/`.
- **Tracing:** retriever spans per query: ranked `chunk_id`, page, score, rank, k, metric, filter, tie rule, `index_manifest_hash`, latency. Default JSONL (06 §2.5); local viewer Phoenix via `openinference-instrumentation-langchain`; LangSmith only under `tracing_context` after `privacy.assert_corpus_is("D")`.
- **Dataset and evaluators:** the 10 draft seeds D-001…D-010 (06 §6.7, demonstration only) + 33 page-head queries. Code evaluators: Hit@4, MRR (page overlap), result length == k, tie determinism (two runs + shuffled rows give identical ids), ANN recall@k vs exact. No judge (D-10).
- **Experiment:** v0 exact (champion) vs `InMemoryVectorStore` (expected: same sets; differences only on ties) vs IVF/HNSW (if faiss) on identical comparison keys. P5 has no earlier version; brute force is the reference.
- **Cost/latency:** $0; p50/p95 per retriever (nearest-rank, warm-up excluded); index bytes; build time.
- **Versioning:** retrieval config (`metric`, `k`, `tie_rule`, `filter_mode`, ANN params) in the run YAML → `config_hash`.
- **CI and monitoring:** T1 tests: `top_k == brute_force` on tie-heavy arrays; shuffled-row invariance; alignment asserts; ANN recall ≥ threshold when an ANN arm exists. Monitor: N and projected p95 against the budget, ANN recall canary on a fixed query sample after bulk inserts/deletes, filter shortfall rate, embedding-norm canary (foundation §8.4).
- **Lifecycle and skills:** Analyze (traces of ranks and ties: `llm-observability`, `trace-data-analysis`) → Measure (retrieval metrics only: `rag-evaluation`, `code-based-evaluators`) → Improve (latency vs recall: `improving-llm-agents`) → CI (`ci-cd-evals`).

---

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| LLM | none | — | — | — | 0 | — | P5 has no generation step; retrieval only |
| Embeddings (default) | `sentence-transformers/all-MiniLM-L6-v2`, snapshot `1110a243…` | sentence-transformers 6.1.0 | yes | yes (HF cache) | 0 | Apache-2.0 | yes |
| Embeddings (optional arm) | Cohere `embed-v4.0` via `study/llmops/` | cohere 7.2.0 | yes | replay only | ≈ 3 calls once, then 0; price UNVERIFIED | MIT (SDK) | yes (D-03), cached |
| Exact search, IVF from scratch | `numpy` | 2.5.3 | yes | yes | 0 | BSD-3 | yes |
| Charts | `plotly` | 7.1.0 | yes | yes | 0 | MIT | yes |
| ANN comparison (recommended) | `faiss-cpu` | **1.15.1** (2026-09-16); cp312 `win_amd64` wheel 16.29 MB; needs `numpy>=1.25` | no | yes | 0 | MIT | yes; optional group; NumPy 2.5 import UNVERIFIED until tried |
| ANN (not recommended) | `hnswlib` | 0.8.0 (2023-12-03); **sdist only** (0.04 MB), so Windows needs MSVC C++ build tools | no | yes | 0 | Apache-2.0 | no: stale, needs a compiler |
| ANN (fallback) | `usearch` (+ `numkong`, `tqdm`) | 2.26.3 (2026-10-02); win wheel 0.35 MB; numkong 7.8.4 wheel 0.5 MB | no | yes | 0 | Apache-2.0 | yes, but HNSW only; use if faiss fails to import |
| Clustering (alternative to NumPy k-means) | `scikit-learn` | 1.9.1 | yes (only via sentence-transformers) | yes | 0 | BSD-3 | yes; declare explicitly if imported directly |
| Framework | `langchain-core` | 1.6.6 (foundation pin) | no | yes | 0 | MIT | yes (D-32, after mechanism) |
| FAISS wrapper | `langchain-community` | 0.4.2 | no | — | — | MIT | **read-only source**; not installed (pulls `langchain-classic`, `aiohttp`) |
| Hosted tracing | `langsmith` | 0.14.4 (foundation pin) | no | no (service) | free plan | MIT | climate corpus only |
| Local tracing | `arize-phoenix-otel` 0.17.2 + `openinference-instrumentation-langchain` 0.1.78; Phoenix server via `uvx arize-phoenix@20.19.0` | as listed | no | yes | 0 | Apache-2.0 / ELv2 | yes; default stays JSONL |
| Tests | `pytest` | 9.1.1 | yes (dev) | yes | 0 | MIT | yes |

Install lines (do not run until Yash approves and the notebook is built):

```text
uv add --group ann faiss-cpu==1.15.1            # optional; ANN sections skip without it
uv add --group llmops langchain-core==1.6.6 langsmith==0.14.4 arize-phoenix-otel==0.17.2 openinference-instrumentation-langchain==0.1.78   # foundation line, shared
# fallback only if faiss will not import:  uv add --group ann usearch==2.26.3
```

Keys: none for P5. `COHERE_API_KEY` only if the Cohere arm is recorded fresh; `LANGSMITH_API_KEY` only for the hosted view.

---

### 11. Open questions for Yash (preferences only)

1. Add `faiss-cpu` (16 MB, MIT) in an optional `ann` group so the ANN sections run for real? **Yes** recommended. Without it, IVF still runs from scratch in NumPy and the HNSW parts stay reading-only.
2. Use AIQ 04 Q8 as P5's one external quiz item (the last free slot)? **Yes** recommended.

**Note for the coach.** The tie-aware cut is core and is taught on a toy array only, so the tutor's reserved scenarios stay unused.

---

## Concept P6: Retrieval evaluation basics

**The short version.** The existing P6 material is strong. The lesson, lab, reference code (`p6_metrics.py`), 23 tests and FACTS file all agree with 06 §7.3. The gaps are elsewhere:
1. qrels and relevance are used without a bridge (P2 is not studied).
2. The lesson has no real-corpus example.
3. It does not explain why "unjudged = not relevant" biases results.
4. It does not warn about the name clashes: Recall@k vs hit rate vs ANN recall vs RAGAS "context recall".
5. It does not say how library conventions differ from ours (trec_eval: linear gain, no MRR cut-off, ties sorted by docno).

One citation error matters. 06 attributes the 2^g − 1 / log2(i + 1) nDCG formula to Järvelin & Kekäläinen 2002, but that formula is Burges et al. 2005; J&K used different conventions.

---

### 1. Sources checked

**Book pages (opened 2026-10-17; extracts in `scratchpad/phase01/book_P6/`):**

| Cite | What is there (paraphrased) | Verified |
|---|---|---|
| Ch22 p.4/19 | The evaluation triad (query–context–answer). Context relevance is scored per chunk, "simplest" by a language model. **Precision at K**, with the example "3 relevant of 5 → 0.6"; it measures noise | yes |
| Ch22 p.5/19 | **Recall at K** over all relevant documents in the knowledge base, with the example "3 of 10 → 0.3" (no K stated); "context precision" penalises relevant documents buried below irrelevant ones; precision-vs-recall figure | yes |
| Ch22 p.6/19 | MRR per query, then averaged; example: rank 3 gives 0.33. MAP: precision at every relevant rank, averaged, then over queries. NDCG: graded relevance, a gain per document, a log discount, normalised by the ideal ranking, range 0–1. No formulas | yes |
| Ch22 p.7/19 | Caption of the good-vs-poor ranking figure: same documents, different order | yes (text only; the image was checked in P6_FACTS) |
| Ch22 p.8/19 | Faithfulness isolates generation from retrieval quality | yes |
| Ch22 p.13/19 | Component-level vs end-to-end evaluation; the unsourced "200–500 examples" claim | yes |
| Ch22 p.18/19 | Key takeaway: ranking metrics go beyond precision/recall | yes |
| App p.13, 15, 18, 19, 20/23 | Glossary start (p.13); Context Precision and Context Relevance (p.15); MAP (p.18); MRR, NDCG, Precision at K (p.19); Recall at K (p.20) | yes |

The book never gives a formula, a cut-off rule, Hit@k, or the word qrels (confirmed in P6_FACTS S-src and by this reading).

**Repo (`RAG_Techniques` @ `009adba2…`, verified with `git rev-parse`):**
- A regex sweep of 46 notebooks and 25 `.py` files (cells plus text outputs) for nDCG, DCG, reciprocal rank, MRR, recall@/at k, hit rate, Hit@, precision@/at k, average precision and MAP@ finds **one hit only**: "hit rate" in `all_rag_techniques/local_rag_huggingface_faiss.ipynb` cell 30. It shares of expected keywords found in the **answer** (an `except ImportError` fallback), so it is answer quality, not retrieval.
- `evaluation/`: deepeval `ContextualRelevancyMetric` (`evaluation_deep_eval.ipynb`, `evalute_rag.py` L20/L89); no rank metric.
- **New:** `evaluation/open-rag-eval-example.ipynb` cell 14 prints `weighted_precision 0.5`, `weighted_recall 0.2` and `f1`. These are **citation** scores of the generated answer, not retrieval precision or recall. Name clash; see §4 E11.

**Existing course files read:**
- `concepts/P6_ir_metrics.md` (all 726 lines);
- `labs/P6_ir_metrics_lab.ipynb` (via FACTS) and `sources/verification/P6/` (`P6_FACTS.md`, `p6_metrics.py`; test and output files listed);
- 02 P6 card and §4 gates; 03 rows; 04 P6/M1/M2 rows;
- 06 §6.1–6.7, §7.1–7.6, §9.4;
- 08 Part 4 (via the foundation); the external review's P6 rows;
- `progress/concept_tracker.csv` and `misconception_log.md` (MC-005, MC-006);
- session log O1-Q04;
- `concepts/P2_ir_framing.md` (qrels, pooling);
- P3 lesson §12, gap audit, notebook structure and tool docstring;
- `study/FORMAT.md`; the writing-style files; `.claude/skills` (rag-evaluation, evals-foundations, code-based-evaluators, ci-cd-evals, llm-observability, visual-learning-writer);
- `sources/coach/transfer_seed_bank.md` (only to avoid seeds; §3).

**AE book:** `AI Eval/chapter 7/…md`, sections 'Precision@k and Recall@k', 'Mean Reciprocal Rank (MRR)' and 'Normalized Discounted Cumulative Gain (NDCG@k)'. Paraphrased below.

**Interview repo (`AI-Engineer-Interview-Questions` @ `e080df28…`, MIT, "Copyright (c) 2026 Om"):**
- `07-evaluation-and-observability/questions.md` Q22 (line 551) and Q23 (lines 577–601);
- `04-rag-and-retrieval/questions.md` Q43 (lines 1136–1152), plus the ANN-recall uses at lines 208 and 512;
- `GLOSSARY.md` line 312;
- `12-coding-challenges/12_eval_metrics.py` (pass@k, EM/F1, pairwise judge; no rank metric).

**External sources** (all external; opened 2026-10-17):

| # | Source | URL | Status |
|---|---|---|---|
| [P6-1] | Manning, Raghavan, Schütze, *Introduction to IR*, §8.4 "Evaluation of ranked retrieval results" (CUP 2008) | https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html | verified |
| [P6-2] | Same, §8.3 "Evaluation of unranked retrieval sets" | https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-unranked-retrieval-sets-1.html | verified |
| [P6-3] | Järvelin & Kekäläinen, "Cumulated gain-based evaluation of IR techniques", ACM TOIS 20(4):422–446, 2002, doi 10.1145/582415.582418 (read from a mirror PDF) | https://www.fi.muni.cz/~xkohout7/Research/clanky_cizi/evaluation/p422-jarvelin.pdf | verified (pp. 424–432 read) |
| [P6-4] | Burges et al., "Learning to Rank using Gradient Descent", ICML 2005, doi 10.1145/1102351.1102363 | https://khoury.northeastern.edu/home/vip/teach/IRcourse/6_ML/other_notes/rankNET.pdf | verified (eq. 16) |
| [P6-5] | Voorhees & Tice, "The TREC-8 Question Answering Track", LREC 2000 | https://aclanthology.org/L00-1018.pdf | verified |
| [P6-6] | Thakur et al., "BEIR: A Heterogenous Benchmark for Zero-shot Evaluation of IR Models", NeurIPS 2021 Datasets & Benchmarks, arXiv 2104.08663 | https://arxiv.org/abs/2104.08663 | verified (§3.3, §6 Table 4) |
| [P6-7] | Smucker, Allan, Carterette, "A Comparison of Statistical Significance Tests for IR Evaluation", CIKM 2007 | https://ciir-publications.cs.umass.edu/getpdf.php?id=744 | verified (abstract) |
| [P6-8] | trec_eval source, `m_ndcg_cut.c`, `form_res_rels.c`, `m_recip_rank.c` (usnistgov, main) | https://github.com/usnistgov/trec_eval | verified |
| [P6-9] | ir-measures documentation, "Measures" | https://ir-measur.es/en/latest/measures.html | verified |
| [P6-10] | ranx documentation, "Metrics" | https://amenra.github.io/ranx/metrics/ | verified |
| [P6-11] | RAGAS docs, Context Precision and Context Recall (stable) | https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/ and …/context_recall/ | verified |
| [P6-12] | PyPI JSON API for `pytrec-eval-terrier`, `pytrec_eval`, `ir-measures`, `ranx`, `trectools`, `ragas` | https://pypi.org/pypi/<name>/json | verified 2026-10-17 |

Extra local check (not a source): a scratch script, `scratchpad/phase01/scripts_P6/p6_climate_preview.py` and `p6_climate_sweep.py`, computed P6 metrics on the real v0 index (97 chunks, snapshot `ea07572562ac`; BM25 with `tok_norm`; local MiniLM) for the 8 answerable **draft** seeds of 06 §6.7. No API, no `.env`. Its MRR@10 (dense 0.708, BM25 0.938) reproduces the values in P3 §12, which validates the setup. Outputs: `out_p6_climate_preview.txt`, `out_p6_climate_sweep.txt`. These are **draft-seed observations**, not results, and not yet FACTS rows.

---

### 2. Gap audit

Learner state: P6 `not_started`, `application_score 0` (O1-Q04: Precision@k, Recall@k and reciprocal rank not recalled), `reinforcement_flag 1`. P2 (owner of qrels and relevance) and P5 are `not_started`. MC-005 (one-sided k) lists a P6 application item as a check item.

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | **Relevance is a label, not a similarity score**; a qrel = (query, chunk, grade), made before the run | every metric; lesson D.1; P6-A1 | Only in P2 (D.1 assumes it) | P2 | no | bridge | §2 bridge, 4 sentences, with one D-007 label row (Short) |
| 2 | Graded vs binary labels; the binary rule (grade ≥ 1) | nDCG; lesson D.1/D.4 | yes, D.1 | P2/P6 | no | core | Keep; say that AE binarises on 0–3 with "> 1" while the course uses ≥ 1 on 0–2 (Full) |
| 3 | **Unjudged = not relevant**, and the bias it causes (holes, pooling) | D.1 convention; J4; 06 §7.1 "evidence in an unlabelled place" | Convention stated; **the bias is missing** | P6 (P2 mentions pooling as UNVERIFIED) | no | core | New section with BEIR Table 4 [P6-6]: ANCE nDCG@10 0.654 → 0.735 after filling holes, BM25 0.656 → 0.668. Short: one sentence plus the numbers; Full: Hole@k |
| 4 | Cut-off k = what the LLM receives; the candidate pool vs the final top-k | every @k; MC-005 | Partly (D.1 "always state k") | P5/C4 (k), R3 (pool) | no | bridge | Short: one paragraph; Full: pool vs final (AE Ch7 'Overview' idea), linked to R3 |
| 5 | **Precision@k**: ÷ k even when fewer than k come back; **ceiling n_rel/k** | D.2; J1 | ÷ k yes; **ceiling missing** | P6 | no | core | Add the ceiling with D-006 (1 relevant chunk → P@4 ≤ 0.25). Teach the idea only; no quiz item on it (tutor-reserved) |
| 6 | **Recall@k** ÷ all relevant in the qrels; equal to Hit@k only with one relevant chunk | D.2; P6-A3 | yes | P6 | no | core | Keep |
| 7 | **Name clashes around "recall"**: hit rate called Recall@k (AIQ 07 Q23, GLOSSARY); TREC Recall vs "Success@k" (ir-measures [P6-9]); **ANN recall** = overlap with the exact top-k, no human labels (P5; AIQ 04 lines 208, 512); RAGAS context recall = claim attribution by an LLM [P6-11] | interview prep; P5; Phase 3 tool choice | **missing** | P6 (owns the definitions) | no | core | A Full "same word, four meanings" table. Short: one line, "ANN recall in P5 is not this Recall@k". Never pose it as a quiz scenario (tutor-reserved) |
| 8 | **Hit@k** and hit rate (its mean) | D.2; P3 §12 | yes (P3 §12 Short too) | P6 | no | core | Keep; one line linking to P3's use |
| 9 | **RR / MRR**: 1/rank of the first hit; 0 if none within the cut-off; mean of RRs, not 1/mean rank | D.3; P6-A4 | yes | P6 | no | core | Keep. Full: its origin (TREC-8 QA, top 5) and its six possible values [P6-5] |
| 10 | **DCG / nDCG**: gain, log2(i + 1) discount, IDCG over **all** relevant chunks; exponential vs linear gain | D.4 | yes, but the history is UNVERIFIED | P6 | no | core | Keep. Full: J&K 2002's original (linear weights, log_b i, no discount below rank b) vs Burges 2005 (2^r − 1, log(1 + j)); our convention = Burges/IIR [P6-1, P6-3, P6-4] |
| 11 | Set vs rank metrics; monotonicity in k (Recall, Hit, RR never fall; P and nDCG can) | D.2, D.5 | yes | P6 | no | core | Keep; reuse the D-007 sweep as the visual |
| 12 | MAP/AP and the book's ambiguous denominator; context precision (06 = AP ÷ relevant retrieved); R-precision | G.1; E | yes (G.1, S11); R-precision missing | P6 | no | core (Full) | Keep in Full; add R-precision in one line [P6-1] |
| 13 | **Retrieval quality vs answer quality** (book triad; faithfulness; end-to-end) | Part E; 06 §7.1 | yes (E table) | C5/M3 | no | bridge | Short: keep the two in separate rows. The book's LLM-scored context relevance is a judge, so under D-10 it waits for the end batch |
| 14 | Per-query values, macro mean, report n and per-category n | H.3; 06 §7.6 | Full only (H.3) | M2 | no | bridge | Short: "one number per query, then the mean, with n" |
| 15 | Why small sets are noisy: RR is discrete; per-query variance; test choice | not in the lesson | **missing** | M4 | no | next | Full: 3 sentences ([P6-5] six values; [P6-1] MAP varies 0.1–0.7 across needs; 06 §9.4 ±0.12 at n = 50); link M4 for bootstrap and [P6-7] |
| 16 | **CE@k** vs Hit@k vs chunk-level Recall@k; overlapping chunks double-count | D.7 preview | Preview, toy only | M2 | no | core-preview | Add the real D-007 case (Hit@2 = 1, CE@2 = 0) and D-005 (Recall@1 = 0.5, CE@1 = 1, one chunk holds both facts) |
| 17 | Group-Recall@k, Span-Coverage@k (06 diagnostics) | 06 §7.3; Gate 3→4 | Named in E; no formula | M2 | no | next | One line each in Full; link M2 |
| 18 | Ties and deterministic order; library conventions (trec_eval sorts by score and breaks ties by docno, descending; recip_rank has no cut-off; nDCG gain = qrels value) | lab Task 4 cross-check; future harness | **missing** | P6 (M2 uses it) | no | core (Full) | Full: a "same run, two tools, two numbers" box [P6-8]. Verify notebook: show how to align the two |
| 19 | Metrics as pure, unit-tested functions; one cross-check library | lab Tasks 2–5 | yes | P6 | no | core | Keep; add an optional pytrec_eval/ir-measures cross-check (§10) |
| 20 | Leakage: questions written from chunks inflate retrieval metrics | AIQ 07 Q22 suggests it; AE Ch7 does it | not in P6 | M1 | no | next | One Full sentence plus a link to 06 §6.3 |
| 21 | Log base: why log2(i + 1) (rank 1 gets no discount) | D.4 | discount table only | P6 | no | core | One sentence: rank 1 divides by log2 2 = 1 |
| 22 | The repo's "keyword hit rate" and the open-rag-eval "weighted precision/recall" are answer metrics | G.2; J5 | cell 30 yes; cell 14 **missing** | P6 | no | core | Add cell 14 to the G.2 table |

**Twelve ideas need work: #1, 3, 4, 5, 7, 10, 13, 14, 15, 16, 18 and 22.** The rest are already taught well.

---

### 3. Quiz coverage

No `study/questions/P6_questions.md` exists, so these are the needed question titles. Every key point must be answerable from **Short**.

| id | set | Title (short, plain) |
|---|---|---|
| P6-PRE-01 | pre | 5 chunks come back and 2 are relevant: what is Precision@5? |
| P6-PRE-02 | pre | The first relevant chunk is at rank 3: what is the reciprocal rank? |
| P6-PRE-03 | pre | A two-fact question has Hit@5 = 1: is the evidence complete? |
| P6-R-01 | main | What does Recall@k divide by? |
| P6-R-02 | main | What does reciprocal rank ignore? |
| P6-R-03 | main | What are the three steps of nDCG, and which gain does the course use? |
| P6-R-04 | main | Which metrics can never fall when k grows? |
| P6-R-05 | main | A chunk nobody labelled sits at rank 1: how is it scored, and who does that hurt? |
| P6-A-01 | main | Relevant chunks are a and b; the ranking is `x y a z b`: what are P@5, Recall@5 and RR? |
| P6-A-02 | main | Grades h = 2 and p = 1, ranking `p h n1 n2 n3`: what is nDCG@5 with gain 2^g − 1? |
| P6-A-03 | main | For Q1, k goes from 5 to 10: which way do Precision and Recall move? (MC-005 check item) |
| P6-A-04 | main | Find the bug in this `mrr()` function (1 / mean rank). |
| P6-A-05 | main | The real D-007 dense ranking, cut at k = 2: what are Hit@2, Recall@2 and CE@2? (data in the question; expected 1, 0.5, 0) |
| P6-A-06 | review | Ranking: relevant, not, not, relevant, not; 3 relevant chunks exist. What is AP under each denominator? (DERIVED 0.5 vs 0.75) |
| P6-T-01 | main | A help desk has exactly one correct article per question: which retrieval metric would you report? (from the existing lesson) |
| P6-T-02 | main | A colleague quotes an LLM "context relevance 0.8" over the joined top 5: what can it not tell you? (existing) |
| P6-T-03 | main | Your vector database reports recall@10 = 0.97: does your retriever find 97% of the evidence? (ANN vs labelled recall; new) |
| P6-T-04 | review | Two tools give different MRR on the same run file: name two convention differences to check. (cut-off, ties, gain; new) |
| P6-R-06 | interview | AIQ `04-rag-and-retrieval/questions.md` Q43, verbatim with the MIT notice: "What retrieval metrics would you track - recall@k, MRR, nDCG - and what does each actually tell you?" Our key corrects its "recall@k upper-bounds end-to-end quality" (parametric answers, 06 §7.1) |

Short must contain the key points of P6-R-05 (unjudged → not relevant; BEIR holes), P6-A-05 (CE vs Hit on the real seed) and P6-T-03 (ANN recall vs Recall@k). These are not in Short today.

**Seed check (done):**
- Checked against the coach's seed bank: no title reuses a seed or reserve scenario. AIQ 07 Q23 is tutor-reserved, so the interview item is **04 Q43**.
- The P@k ceiling is taught in the lesson but never posed as a question (tutor-reserved).
- External items: 1 of the 2 allowed.

---

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Evidence | Suggested fix |
|---|---|---|---|---|
| E1 | 06 §7.3 nDCG row ("Järvelin & Kekäläinen 2002, Source C #45") | The formula 06 gives, (2^g − 1)/log2(i + 1), is **not** J&K's | J&K define DCG[i] = CG[i] for i < b and DCG[i−1] + G[i]/log_b i for i ≥ b. G is the relevance weight itself (they tested 0-1-1-1, 0-0-0-1 and 0-1-10-100) with b = 2, so ranks 1 and 2 are both undiscounted [P6-3, p.425–426, 431–432]. The exponential gain over log(1 + j) is Burges et al. 2005 eq. 16 [P6-4], and IIR eq. 8.44 uses it [P6-1] | Cite Burges 2005 / IIR §8.4 for the formula and J&K for the idea and the ideal vector (taken from the recall base: matches 06) |
| E2 | `concepts/P6_ir_metrics.md` Verification log and P6_FACTS §2 | J&K's gain is listed as UNVERIFIED | Resolved by E1: linear weights and a log_b discount from rank b | Replace the UNVERIFIED line; add a Full note that "nDCG" has at least three conventions (J&K 2002, Burges 2005, trec_eval linear over log2(i + 1)) |
| E3 | `study/lessons/P3_bm25.html` §12 (Full box) | "CE@k … For one-piece questions it equals Hit@k" is false in general | Hit uses `any_overlap`, while CE needs every non-whitespace character covered (06 §7.2, which includes the D-005 fragment counterexample) | "…equals Hit@k only when the overlapping chunk holds the whole span" |
| E4 | 04 P6 row | (a) "two tiny examples": there are three (P@5 0.6 on p.4, recall 0.3 on p.5, MRR on p.6; re-verified). (b) Pages p.4–6 miss the p.7 figure and App p.15/18–20. (c) The lab column says "on the P2 toy qrels", but the lab uses its own toy (`p6_toy.py`) | book extracts; P6_FACTS §0 | Correct in the next 04 pass (the existing lesson G.3 already lists (a) and (b)) |
| E5 | 02 P6 card | The glossary cite omits App p.15 (Context Precision, Context Relevance). "Only MRR has a one-number example" is right only within the MRR/MAP/NDCG group; P@K and Recall have examples on p.4–5 | book extracts | Add App p.15; say "only MRR, among the ranking metrics" |
| E6 | 03 row 6 (line 747) | Says "M2 implements them", but the 02 P6 outcome and the lab make P6 implement pure functions | 02 card; lab | "P6 implements and unit-tests them on toys; M2 runs them on span gold" |
| E7 | 01 §6 Source C #45 and #47 | #45 status is "search" (never opened); #47 is the BEIR **repo**, but the metric rationale (nDCG@10; Hole@10; lexical bias) is in the **paper** | [P6-3], [P6-6] | Mark #45 as fetched; add the BEIR paper |
| E8 | `sources/verification/P6/p6_metrics.py` | The undefined-case policy is inconsistent. `recall_at_k` and `ndcg_at_k` raise on an item with no relevant chunk, but precision, hit and RR return 0, and `mean_reciprocal_rank` silently averages such an item in as 0. That is correct only if the caller filters to answerable items (06 §7.3) | code L32–62 | In the harness (M2) and `llmops/evals.py`, filter answerable items in one place and assert `n_rel ≥ 1` in every metric |
| E9 | AIQ `04-rag-and-retrieval/questions.md` Q43 (line 1142) | "recall@k upper-bounds end-to-end quality": the same overclaim the review logged for 07 Q22, in a second place. A model can answer from memory without retrieval (06 §7.1) | file read | Add to the review §8 list; use it in the P6-R-06 key |
| E10 | AIQ 07 Q22 body (line 551) | Suggests generating questions *from* known chunks so relevance holds by construction. This conflicts with the 06 §6.3 leakage rule | file read | Add to the review §8 list (AE Ch7's same recipe is already noted) |
| E11 | P6 lesson G.2 and P6_FACTS S-src | `open-rag-eval-example.ipynb` cell 14 prints `weighted_precision` / `weighted_recall` (answer **citation** scores). The regex missed them because they are not rank metrics; the "no rank metric" claim still stands | cell 14 output | Add a G.2 row so Yash does not read them as retrieval metrics |
| E12 | `concepts/P2_ir_framing.md` line 267 | Pooling is marked "Source C … UNVERIFIED" | BEIR §6, Table 4 [P6-6] gives direct evidence of pool bias | P2 may now cite BEIR |
| E13 | AE Ch7 'NDCG@k' (known, review §8) | IDCG re-sorts only the retrieved documents. The prose says rank 1 contributes its "full relevance score", while the formula's gain is 2^rel − 1 (grade 2 → 3). Plus the "log2(23)" typo | AE Ch7 read | Already logged; the lesson's J2 covers it. The critique stays a hidden reserve, so the lesson must not pose it as a question |

**Metric definitions vs 06** (06 §7.2–7.3; the P6 lesson D.2–D.7; `p6_metrics.py`):

| Metric | 06 formula | P6 lesson | `p6_metrics.py` | Match? |
|---|---|---|---|---|
| Relevance rule | `rel(c)=1` iff any overlap (≥ 1 non-ws char) with any segment (span-derived) | qrels, grade ≥ 1 | `qrels.get(d,0) >= 1` | yes, once qrels come from `rel()` (the derivation is M2; `contracts_check.rel`) |
| Hit@k | `1[∃ i ≤ k: rel=1]` | same | `hit_at_k` | yes |
| Precision@k | `|{i ≤ k: rel=1}| / k` | same; ÷ k on short lists | `precision_at_k` ÷ k | yes |
| Recall@k (chunk) | **not in 06** (replaced by CE / Group-Recall, M-02) | standard, labelled as distinct from CE | `recall_at_k` ÷ all relevant | consistent; not a 06 metric |
| RR / MRR | mean of 1/rank of first relevant; 0 if none within the stated cut-off (e.g. 10); answerable items only | RR@k, MRR@k; trap; cut-off | `reciprocal_rank(…, k)`, `mean_reciprocal_rank` | yes (but see E8) |
| nDCG@k | Σ (2^g − 1)/log2(i + 1); IDCG = ideal order of **all** relevant chunks in the index; binary g ∈ {0,1} | same; linear shown as an alternative | `gain="exp"` default; `idcg_at_k` from all qrels | yes. 06's **citation** is wrong (E1) |
| Graded g(c) | max grade of the alternatives it overlaps | grades given in qrels | grades from qrels | yes, for given qrels; the derivation is M2 |
| Context precision@k | Σ P@i·rel_i / #relevant in top k; 0 if none | described (E, G.1) | `average_precision(…, "retrieved_relevant")`, 0 if none | yes |
| AP (standard) | not in 06 | G.1 | `"all_relevant"` | n/a |
| CE@k | 1 iff every group has an alternative fully covered by the **union** of the top-k ranges | preview, whole-chunk | `ce_at_k_chunks` (preview); real version `contracts_check.ce` | preview by design (labelled); M2 owns the real one |
| Group-Recall@k, Span-Coverage@k | defined | named only | absent (in `contracts_check`) | gap for M2 (fine for P6) |

No formula mismatch between 06, the lesson and the code. The only fault is the nDCG citation (E1), plus the policy point in E8.

---

### 5. What the research says

**[P6-1/2] IIR §8.3–8.4 (textbook).**
- **The source:** a textbook definition of set and ranked metrics.
- **The result:**
  - Precision and recall are defined on sets.
  - MAP's per-query denominator is the number of relevant documents, and an unretrieved relevant document counts as precision 0.
  - R-precision is the precision at |Rel|.
  - NDCG uses (2^R − 1)/log2(1 + m), normalised so that the perfect ranking scores 1. With k′ < k results, the sum runs only to k′.
  - P@k is "the least stable" measure and averages poorly.
  - MAP varies widely across information needs (e.g. 0.1–0.7), so test sets must be large and diverse.
- **What this means:** our P@k, AP and nDCG conventions are the textbook ones.
- **For the project:** cite IIR for the formulas; quote the variance point next to 06 §9.4.

**[P6-3] Järvelin & Kekäläinen 2002 (primary, nDCG).**
- **The study:** TREC-7 runs from 5 groups on 20 topics, re-judged on a 4-point scale.
- **What was tested:** relevance weights (0-1-1-1, 0-0-0-1, 0-1-10-100) and log bases 2 and 10.
- **The result:** the cumulated-gain curves expose differences between runs that binary relevance hides. Base 2 and base 10 gave similar conclusions.
- **Its definitions:** gain = relevance weight; no discount for ranks below b; ideal vector from the topic's recall base.
- **The limits:** 20 topics; graphs and normalised vectors averaged across topics rather than a single scalar.
- **For the project:** (a) the citation fix (E1); (b) "IDCG from all relevant" is J&K's own rule, so the AE variant (re-sorting the retrieved items) is the outlier.

**[P6-4] Burges et al. 2005.**
- **The source:** NDCG@15 with (2^r(j) − 1)/log(1 + j) and N_i set so that a perfect ordering scores 1.
- **Their note:** unlabelled documents earn nothing but still lower NDCG by pushing labelled ones down.
- **For the project:** this is the origin of the course's exponential gain. Their unlabelled-document note is the "unjudged = not relevant" effect.

**[P6-5] Voorhees & Tice 2000 (TREC-8 QA, origin of MRR in evaluation campaigns).**
- **The study:** 200 questions (198 scored); up to 5 ranked responses per question; 45 runs.
- **The scoring:** the reciprocal rank of the first correct response, or 0 if none of the 5 is correct; MRR is the mean.
- **What they said about it:**
  - Strengths: it is bounded, it averages well, and it is close to average precision.
  - Drawbacks: a question can take only six values (0, .2, .25, .33, .5, 1), so parametric tests are doubtful; there is no credit for further correct answers.
- **For the project:** MRR has always had a cut-off (5 there; 10 in 06). Its discreteness is one reason small eval sets are noisy (M4).

**[P6-6] BEIR (NeurIPS 2021).**
- **The setup:** 18 datasets and 10 retrievers. nDCG@10 is chosen because P/R ignore rank and MRR/MAP cannot use graded labels; it is computed with the Python interface of trec_eval.
- **The key result for P6 (§6, Table 4, TREC-COVID):** each system's top 10 contained hits that annotators had never seen (Hole@10).

  ```
  Hole@10   BM25 6.4%   ANCE 14.4%   TAS-B 31.8%   docT5query 2.8%
  nDCG@10 before → after filling the holes by hand (980 pairs)
  BM25 0.656 → 0.668    ANCE 0.654 → 0.735    ColBERT 0.677 → 0.735
  ```
- **What this means:** "unjudged = not relevant" is not neutral. Labels built from one kind of retriever undercount the others.
- **The limit:** one dataset, one round of re-annotation.
- **For the project:**
  - Our span labels avoid chunk-id holes, but not "evidence in an unlabelled place" (06 §7.1).
  - The 06 §6.3 lexical-overlap rule is the same worry in BM25's favour.
  - Every "retrieval bad, answer right" item gets a hand check (M5).

**[P6-7] Smucker et al. 2007.**
- **The study:** pairs of TREC runs (TRECs 3 and 5–8), significance of MAP differences under 5 tests.
- **The result:** randomization, bootstrap and t-test agree in practice; Wilcoxon and the sign test detect poorly and can mislead.
- **For the project:** link only. M4 uses the paired bootstrap (06 §9.3).

**[P6-8] trec_eval source.**
- **What it does:**
  - nDCG gain = the qrels relevance value (linear), discount log2(i + 2) with 0-based i (= log2(rank + 1)), ideal from the qrels relevance levels.
  - Documents are re-ranked by score, with ties broken by docno in **descending** string order. The run file's rank column is ignored.
  - `recip_rank` scans all retrieved documents: no cut-off.
- **For the project:** a pytrec_eval cross-check must (a) feed scores consistent with our (−score, id) order, or break ties ourselves first; (b) map grades to 2^g − 1 or use binary labels; (c) compare RR@10 via ir-measures, not trec_eval's `recip_rank`.

**[P6-9] ir-measures docs.**
- **What they say:**
  - Measures include P@k, R@k, RR(@k), AP, Success@k and nDCG(@k, `dcg` = `log2` or `exp-log2`, `gains`, `judged_only`).
  - They state that the TREC "Recall@k" differs from tasks that call "any relevant in top k" Recall@k, and they name the latter **Success@k**.
- **For the project:** a published, neutral source for the Hit@k vs Recall@k distinction.

**[P6-10] ranx docs.**
- **What they say:** NDCG uses rel/log2(i + 1) credited to J&K, NDCG_Burges uses 2^rel − 1, and Hit Rate = trec_eval's success.
- **The limit:** whether P@k divides by k on short lists is UNVERIFIED (its docs write r/n with n = retrieved).
- **For the project:** another sign that "nDCG" must always name its gain.

**[P6-11] RAGAS docs.**
- **What they say:**
  - "Context Precision" = Σ precision@k · v_k / #relevant in the top K, with v_k judged by an **LLM** against a reference or the response. That is 06's context-precision formula with LLM labels.
  - `IDBasedContextPrecision` = matching ids / **retrieved** ids (it divides by the number retrieved, not by k).
  - "Context Recall" = reference **claims** supported by the retrieved context (LLM), with ID-based and non-LLM variants.
- **For the project:** same names, different objects and different labellers. RAGAS is not installed (it needs OpenAI by default; foundation §9.4), and its LLM labels fall under D-10.

**AE Ch7 (paraphrased, cite `AE Ch7, 'section'`).**
- It gives P@k and R@k with binarisation of graded labels.
- It advises favouring recall for the first stage and nDCG for reranking (tip box).
- It uses MRR when one key fact suffices.
- Its nDCG has the IDCG-from-retrieved variant (E13).
- **For the project:** useful for the pool-vs-final framing (R3); its IDCG is the J2 bug.

**Current practice (2024–2026).**
- Retrieval stages are scored with deterministic rank metrics on labelled sets: nDCG@10 for benchmarks (BEIR, MTEB-style), Recall@k on the candidate pool, and MRR@10 where one answer matters.
- RAG frameworks add LLM-judged "context" metrics under the same names (RAGAS, deepeval).
- The course's CE@k on span groups is stricter than all of these, and is course-specific.

**Pitfalls, with evidence:**
- IDCG from the retrieved items: J2 (1.0 vs 0.2421, FACTS S7); AE Ch7.
- 1/mean rank: J3.
- Undeclared gain: 0.5625 vs 0.5406 (S7).
- Library ties and cut-offs [P6-8].
- Holes and pool bias [P6-6].
- Name clashes [P6-9, P6-11]; ANN recall (P5).
- Hit@k read as sufficiency (06 toy: Hit@3 = 1, CE@3 = 0).
- Overlapping chunks inflate P and nDCG (06 §7.3 traps).
- Tiny n [P6-1, P6-5; 06 §9.4].

**How to evaluate P6 itself:** hand values equal code values; the code equals an independent reference (sklearn `ndcg_score` already; pytrec_eval optional); every 06 §7.3 toy value is reproduced (S9).

**Interview angle (3–5 questions):**
1. "Which retrieval metrics, and when?" (AIQ 04 Q43; 07 Q23)
2. "Why do MRR and nDCG disagree?"
3. "Recall vs precision for RAG; first stage vs reranker."
4. "Your vector DB says recall 0.97; what is it measuring?"
5. "How can a correct answer coexist with zero recall?" (parametric knowledge)

---

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).**
1. To know whether a retriever got better, you fix the right answers in advance (labels), run every version on the same questions, and turn each ranked list into numbers.
2. Hit@k asks whether *any* evidence reached the top k, Precision@k how much of the top k is noise, and Recall@k what share of *all* relevant chunks arrived.
3. Reciprocal rank asks how early the first relevant chunk came, and nDCG how good the whole order is when some chunks are more useful than others.
4. Each answers a different question. On the real D-007 question, the dense retriever has Hit@2 = 1 but only one of the two needed facts, so the course's primary metric, CE@k ("did *all* the evidence arrive?"), is 0 there.
5. These numbers measure retrieval only, never the answer, and they are only as good as the labels: anything unlabelled counts as wrong.

**The theory in one read (12 linked ideas):**

| # | Idea | Formula / rule |
|---|---|---|
| 1 | A label (qrel) is fixed before the run; relevance ≠ similarity | qrels: (q, chunk) → grade ∈ {0,1,2}; relevant ⇔ grade ≥ 1 |
| 2 | Only the top k is scored; k = what the LLM sees | R_k = (c_1..c_k) |
| 3 | Hit@k | 1[∃ i ≤ k: rel_i = 1]; hit rate = its mean |
| 4 | Precision@k (noise); ceiling | |rel in top k| / k; ≤ n_rel / k |
| 5 | Recall@k (missed evidence) | |rel in top k| / n_rel; = Hit@k when n_rel = 1 |
| 6 | Unjudged = not relevant, which biases the score against new retrievers | BEIR holes [P6-6] |
| 7 | RR and MRR (how early) | RR@k = 1/rank of the first relevant, 0 beyond k; MRR = mean RR (not 1/mean rank) |
| 8 | DCG / nDCG (order plus grades) | DCG@k = Σ (2^g_i − 1)/log2(i + 1); nDCG = DCG/IDCG, IDCG over all relevant chunks |
| 9 | What k does | Recall, Hit, RR never fall; P can go either way; nDCG can fall |
| 10 | MRR vs nDCG can disagree | first hit only vs all hits plus grades |
| 11 | Sufficiency: CE@k (06 primary) | 1 iff every fact group is covered by the top k |
| 12 | Retrieval ≠ answer metrics; "recall" means four different things | separate rows; name table |

**Formula sheet:** the items in rows 3–5, 7 and 8, plus:
- AP (two denominators) and context precision;
- R-precision = P@|Rel|;
- the discount table 1/log2(i + 1) for i = 1..10;
- gains: exp 0/1/3, linear 0/1/2;
- CE@k, Group-Recall@k and Span-Coverage@k one-liners (06 §7.2).

**Step-by-step outline: one running example from the course corpus.**
- **Data:** D-007 (multi-hop; facts on p.10 and p.29), from the 06 §6.7 **draft** seeds, on the v0 index (97 chunks, 1000/200, snapshot `ea07572562ac`).
- **Retriever:** MiniLM as the local dense stand-in, as P3 and R1 do. No API.
- Research-preview numbers (scratch run; to be re-made in the verify notebook and logged in FACTS):

```
D-007 dense, top 5 (seq, page, relevant?):  s069 p.24 no · s027 p.10 YES(G1) · s085 p.29 YES(G2) · s084 p.29 no · s017 p.6 no
k=1  Hit 0  P 0.00  R 0.00  RR 0.00  nDCG 0.0000  CE 0  Group-Recall 0.0
k=2  Hit 1  P 0.50  R 0.50  RR 0.50  nDCG 0.3869  CE 0  Group-Recall 0.5   ← "a hit" but half the evidence
k=3  Hit 1  P 0.67  R 1.00  RR 0.50  nDCG 0.6934  CE 1  Group-Recall 1.0
k=4  Hit 1  P 0.50  R 1.00  RR 0.50  nDCG 0.6934  CE 1
D-007 BM25: relevant at ranks 1, 2 → CE@2 = 1, RR = 1, nDCG@10 = 1.0
```

Steps:
1. The labels (bridge from P2).
2. Hit@k.
3. Precision@k and its ceiling (D-006: one relevant chunk → P@4 ≤ 0.25).
4. Recall@k.
5. RR/MRR across the 8 seeds: dense MRR@10 0.708, BM25 0.938 (P3 values reproduced).
6. nDCG@k on the binary labels.
7. The graded step uses the existing toy Q1 (0.5625). The corpus seeds have no grades yet (06's `grade` field is optional and unlabelled), and the lesson says so in one line.
8. CE@k vs Hit@k vs Recall@k:
   - D-007 at k = 2.
   - D-005 at k = 1: one chunk (s003) holds both facts, so chunk Recall@1 = 0.5 while CE@1 = 1. Counting chunks is not counting facts.
9. What k does (the sweep).
10. Unlabelled evidence and holes.
11. Retrieval vs answer.

**Caveat, stated plainly:**
- On these 8 draft seeds both retrievers reach CE@4 = 8/8, so the seeds cannot rank retrievers at k = 4. Only MRR and nDCG separate them.
- They are LLM-drafted and not human-verified, so these are observations, not results.

**Visuals that earn their place:**
1. **"One ranking, six lenses"** (Short): the D-007 dense top-5 strip, relevant chunks marked with group tags, and a k slider (1–5) that updates Hit, P, R, RR, nDCG and CE together. Shows that each metric moves differently at the same cut-off.
2. **Discount bars** (Short): 1/log2(i + 1) for ranks 1–10, with an exp/linear gain toggle on the graded toy. Shows why rank 1 matters most and why the gain must be stated.
3. **MRR vs nDCG pair** (Short): the QD_A and QD_B rankings side by side (S8). Shows "first hit" vs "all hits".
4. **"Which metric answers which question"** decision flow (Short): any hit → Hit@k; noise → P@k; all evidence → CE@k; how early → MRR; graded order → nDCG@10.
5. **Holes bar pair** (Full): the BEIR nDCG@10 before/after for BM25 and ANCE [P6-6], labelled external.

**Full only:**
- MAP/AP denominators, context precision and R-precision.
- J&K vs Burges vs trec_eval conventions, with library tie rules and cut-offs.
- The "recall" name table:

  | Name | Means |
  |---|---|
  | IR Recall@k | ÷ all relevant |
  | hit rate / Success@k | any relevant |
  | ANN recall (P5) | overlap with the exact top-k |
  | RAGAS context recall | LLM claim attribution |
- Statistical noise (six RR values; 06 §9.4) → M4.
- Group-Recall and Span-Coverage → M2.
- Candidate pool vs final top-k → R3.
- Leakage from chunk-written questions → M1.
- The AE convention note.
- The repo G.2 table, including open-rag-eval cell 14.

---

### 7. Verify notebook plan

**`study/notebooks/P6_ir_metrics_verify.ipynb`**, in the P3 structure: setup cell, `check(name, got, expected, tol)`, `skip()`, a section per lesson step, and a final PASS/FAIL tally.

| § | Recomputes | Data | Code |
|---|---|---|---|
| 1 | Toy Q1 at k = 5 (P 0.4, R 0.6667, Hit@1 0, Hit@5 1, RR 0.5, nDCG 0.5625; DCG 2.3235, IDCG 4.1309) | `p6_toy.py` | `p6_metrics` (imported read-only) |
| 2 | k sweep for Q1 (S5) and "nDCG can fall" QF (1.0 → 0.6131); Plotly line chart, metric vs k | toy | same |
| 3 | MRR@10 0.5833, MRR@3 0.5, the 1/mean-rank trap 0.4286 | toy | same |
| 4 | Gain conventions (0.5625 vs 0.5406); `sklearn.metrics.ndcg_score` agreement (max diff ≤ 1e-12); J2 IDCG bug (1.0 vs 0.2421); **optional** pytrec_eval / ir-measures cross-check with explicit tie-breaking and the exp gain mapping. Skipped with a message if not installed | toy | sklearn 1.9.1; optional `ir_measures` |
| 5 | MRR vs nDCG disagreement (S8): QD_A/QD_B, QG_A/QG_B | toy | same |
| 6 | **Real corpus:** rebuild the 97 chunks exactly as R1/P3 (07 chunker via `contracts_check.load_07_modules`; params_hash `1ca9c5a3b548`; chunks.jsonl sha `d4108b89…`), labels via `contracts_check.rel`. Per seed, BM25 and MiniLM: Hit@1/4, P@4, R@4, RR@10, nDCG@10, CE@4, Group-Recall@4. The D-007 sweep and the D-005 Recall-vs-CE contrast. MRR@10 0.708 / 0.938 must match P3 §12 | climate PDF, 06 §6.7 seeds | `p6_metrics` + `contracts_check.ce/group_recall/span_coverage` |
| 7 | AP vs context precision (S11: 0.3333 vs 0.5) and R-precision on Q1 (new value; DERIVED in the notebook) | toy | `average_precision` |
| 8 | Per-query distribution: strip chart of the 8 seeds' RR for both retrievers; the set of possible RR values at cut-off 10; a pointer to M4's bootstrap (not computed here) | §6 | numpy, plotly |

- No LLM or API call (0).
- Works offline: MiniLM comes from the HF cache with `HF_HUB_OFFLINE=1`; if missing, §6's dense rows `skip()`.
- Runtime about 30–60 s on CPU (MiniLM embeds 97 chunks plus 10 queries; the scratch run took under a minute).

---

### 8. Apply-it tool plan and real-world checklist

**`study/tools/retrieval_metrics_check.py`**, "Is my retrieval measurement sound, and what does it say?" A CLI that is also importable, like `bm25_fit_check.py`.

**Inputs:**
- `--run run.jsonl`: `{"qid", "ranking": [{"id", "score", "doc_id"?, "char_start"?, "char_end"?}]}`.
- `--labels`: either chunk qrels `{"qid", "id", "grade"}` or 06-style items with `evidence_groups` (then chunk relevance is derived with `any_overlap`, and CE@k is computed).
- `--k 1,4,10 --mrr-cutoff 10 --gain exp|linear`.
- `--answers answers.jsonl` (optional; per-qid `correct: true/false`, from human labels) for the hole check.

**Output:** a Markdown report:
1. Conventions used (k, cut-off, gain, binary rule, tie rule).
2. Per-query table.
3. Means with n, overall and per category.
4. Checklist with verdicts.
5. Recommendation.

**Real-world checklist** (13 checks, one over the 8–12 guide; C2 and C3 can merge into one "ranking hygiene" check):

| # | Check | auto/manual |
|---|---|---|
| C1 | Items with no relevant label are excluded from retrieval metrics and counted separately | auto |
| C2 | Duplicate ids inside a ranking | auto |
| C3 | Rankings shorter than k (P@k still ÷ k; flags the count) | auto |
| C4 | Score ties straddling rank k (unstable top-k membership) | auto |
| C5 | Stale labels: label ids not in the run's index, or spans outside the snapshot | auto |
| C6 | n_rel per item, and the P@k ceiling n_rel/k reported beside P@k | auto |
| C7 | Share of items with > 1 relevant chunk (when Recall@k ≠ Hit@k), and with > 1 fact group (when CE ≠ Hit) | auto |
| C8 | Overlap redundancy: relevant chunks overlapping the same span (P and nDCG inflated; prefer CE) | auto (needs offsets) |
| C9 | Conventions declared (gain, cut-off, k); refuses to print nDCG without a gain | auto |
| C10 | Small n: any category with n < 10 is labelled "anecdote" | auto |
| C11 | Cross-check with ir-measures/pytrec_eval if installed (binary metrics must agree to 1e-9 after tie alignment) | auto (optional) |
| C12 | Holes: items with no relevant chunk in the top k but a correct answer → manual review list (parametric answer or unlabelled evidence?) | manual: read each listed item's top-k and the page |
| C13 | Labels written independently of the chunker (not from chunks; `created_by` recorded) | manual: check the label provenance |

**Recommendation logic:**
- Most items have one relevant chunk → headline Hit@k at the prompt k plus MRR@10.
- Multi-fact items (≥ 20%) → headline CE@k (needs spans); if only chunk labels exist, recommend span labels.
- Graded labels present → add nDCG@10.
- Candidate pool given separately → Recall/CE on the pool as the ceiling, MRR/nDCG on the final list (R3).
- C5 or C12 fail → "fix the labels before trusting any number".

No API calls. Standard library plus numpy; ir-measures optional.

---

### 9. LLMOps notebook plan

**`study/notebooks/P6_ir_metrics_llmops.ipynb`.** It applies foundation §12 row "1 · P2–P3, P5–P6" (no external calls; retriever wrappers; ranked lists and scores; Hit@k/MRR; p50/p95; T1 tests). P6-specific additions follow.

| Part | Plan |
|---|---|
| **Framework build** | `retrievers.py`: plain functions `bm25(q)` and `dense_minilm(q)` returning `[(chunk_id, score)]` (mechanism step = "ranked list"). Optional read-only cell: wrap one as a `langchain_core.retrievers.BaseRetriever` to show `k=4` and `similarity` defaults (foundation §9.2). Evaluators come from `llmops/evals.py`: `hit_at_k`, `precision_at_k`, `recall_at_k`, `rr_at_10`, `ndcg_at_10`, `ce_at_k`, each wrapped as `(inputs, outputs, reference_outputs) -> {"key", "score"}` and computed by `p6_metrics` / the `contracts_check` reference (one implementation, foundation §10) |
| **Caching** | **0 external calls.** MiniLM is local, not an API; its query vectors use the C3 content-keyed cache. Optional Cohere embed-v4.0 rankings are read **only** from the existing C3 cache in `replay` mode (0 new calls; a `ReplayMiss` → skip with a message). The notebook runs with `LLMOPS_CACHE_MODE=replay` and no keys, using the shared `study/llmops/` package |
| **Tracing** | Per query, a run span plus a retriever span (OpenInference `retrieval.documents`: id, score, rank; no chunk text in exported spans unless corpus D; foundation §3.3) to the JSONL trace. Local viewer: Phoenix (`uvx arize-phoenix@20.19.0 serve`, `arize-phoenix-otel`). LangSmith is optional and corpus D only, inside `tracing_context(enabled=True)` after `privacy.assert_corpus_is("D")` |
| **Dataset and evaluators** | Golden set = the 06 §6.7 seeds (8 answerable; **draft**, `split: unassigned`, so "observation" is printed on every table) as local JSONL with `dataset_sha256`. Tier-1 evaluators only, retrieval metrics only; no answer metric (P6 has no generator). No LLM-judged context relevance (D-10) |
| **Experiment** | BM25 vs MiniLM dense on identical comparison keys (dataset sha, snapshot, qid set, scorer_version). Course runner first, then the framework view: `langsmith.evaluate(target, data=…, evaluators=[…], upload_results=False)`. Whether it accepts a plain list of local examples without a key is **UNVERIFIED** (foundation §4), so the cell is guarded and skips cleanly. There is no "previous version" for P6, so the comparison is P3's BM25 vs the v0 dense stand-in |
| **Cost/latency/tokens** | Retrieval latency p50/p95 per retriever (nearest-rank, named; 06 §7.5); cost $0; tokens n/a |
| **Versioning** | A metric config `{k: [1,4,10], mrr_cutoff: 10, gain: exp, binary_rule: ">=1", tie_rule: "(-score, id)", scorer_version: s1}` hashed into the run's `config_hash`. A change to any of these is a new `scorer_version` (06 §6.6). The foundation map has "—" for versioning here; P6 adds this |
| **CI** | T1 tests: the existing 23 metric tests; a cross-check test against ir-measures (skipped if absent); a draft-seed snapshot test pinning MRR@10 (0.708 / 0.938) and CE@4 (8/8) for chunks sha `d4108b89…`, failing on any drift; a leakage-free check that evaluators never read the answer |
| **Monitoring and feedback** | Monitor-page rows: metric per version (CE@4, MRR@10, nDCG@10, with n), the share of items with n_rel = 0 after a re-chunk (label rot, J4), and the hole-candidate count (C12). Alert on a drop beyond the 06 §9.4 noise band on identical keys, or on any n_rel = 0 rise. Feedback: hole candidates → M5 error analysis → a label fix in a new dataset version |
| **Lifecycle** | Analyze (read the ranked lists; `trace-data-analysis`) → Measure (tier-1 retrieval evaluators; `code-based-evaluators`, `rag-evaluation`) → Improve (none in P6; feeds v0.1). dev → CI (T1) → monitor (`ci-cd-evals`, `llm-observability`) |

---

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| LLM per task | **none**. P6 has no generation. LLM-judged "context relevance/precision" (book Ch22 p.4/19, RAGAS) is deferred to the D-10 end batch | — | — | — | 0 calls | — | yes (D-10) |
| Metric source of truth | `p6_metrics.py` (stdlib) → later `ragkit` metrics + `llmops/evals.py` | course | yes | yes | 0 | course | yes |
| CE / Group-Recall reference | `sources/verification/corrections/contracts_check.py` (`rel`, `ce`, `group_recall`, `span_coverage`) | course | yes | yes | 0 | course | yes |
| Numerics, charts | numpy, pandas, plotly | 2.5.3 / 3.0.6 / 7.1.0 | yes | yes | 0 | BSD / BSD / MIT | yes |
| nDCG cross-check (existing) | scikit-learn `ndcg_score` (linear gain; ranks all given docs) | 1.9.1 | yes | yes | 0 | BSD-3 | yes |
| Lexical retriever | rank-bm25 | 0.2.2 | yes | yes | 0 | Apache-2.0 | yes |
| Dense retriever (local) | sentence-transformers, `all-MiniLM-L6-v2` (HF cache) | installed | yes | yes (cache) | 0 | Apache-2.0 | yes (fallback per decisions) |
| Dense retriever (default) | Cohere `embed-v4.0`, **replay only** from the C3 cache | — | `cohere` 7.2.0 yes | replay yes | 0 new calls | MIT (SDK) | yes |
| Optional cross-check | **`ir-measures`** (named R@k, Success@k, RR@k, nDCG `exp-log2`) | **0.4.3** (2025-11-25) | no | yes | 0 | Apache-2.0 | yes (eval group) |
| Its backend | **`pytrec-eval-terrier`** (trec_eval C extension; cp312 `win_amd64` wheel, 58 KB; needs numpy, scipy) | **0.5.10** (2025-10-20); not 0.5.11, released 2026-10-16 | no | yes | 0 | MIT | yes |
| Not chosen | `pytrec_eval` 0.5 (2020, sdist only: needs a C compiler on Windows); `ranx` 0.3.21 (numba, ir-datasets, seaborn…: heavy); `trectools` 0.0.50 (lxml, matplotlib, bs4); `ragas` 0.4.3 (requires `openai`) | — | no | — | — | — | no |
| Framework (optional cell) | `langchain-core` (BaseRetriever wrapper, read-only) | 1.6.6 (foundation) | no | yes | 0 | MIT | yes (D-32, after the mechanism) |
| Eval view | `langsmith` `evaluate(..., upload_results=False)` | 0.14.4 (foundation) | no | SDK yes; keyless run UNVERIFIED | 0 | MIT | yes; corpus D only if uploaded |
| Local tracing | JSONL trace (default) + `arize-phoenix-otel` / Phoenix via `uvx` | 0.17.2 / 20.19.0 (foundation) | no | yes | 0 | Apache-2.0 / ELv2 | yes |
| Phoenix evaluators | not needed (tier-1 functions suffice; Phoenix's LLM evals fall under D-10) | — | — | — | — | — | n/a |
| Tests | pytest | 9.1.1 | yes (dev) | yes | 0 | MIT | yes |

**Install lines (do not run):**
```text
uv add --group eval ir-measures==0.4.3 pytrec-eval-terrier==0.5.10     # optional cross-check (P6 verify §4, tool C11, M2)
# LLMOps notebook: the foundation's llmops group (langchain-core, langsmith, arize-phoenix-otel), nothing P6-specific
```

**Keys:** none required. `LANGSMITH_API_KEY` is optional (corpus D only). Nothing above 500 MB, no GPU, no server except the optional Phoenix viewer.

**External-call count for P6, all deliverables: 0.** Replay mode is trivially satisfied, and the shared `study/llmops/` package is used only for tracing and evaluators.

---

### 11. Open questions for Yash (preferences only)

1. Add the small optional cross-check library (`ir-measures`, a pure-Python wheel, plus `pytrec-eval-terrier`, a 58 KB Windows wheel) to an `eval` group? **Yes** recommended.
2. Should the real-corpus running example use the **local MiniLM** rankings (recommended: no cache dependency), or replay the cached **Cohere** v0 rankings?
3. Include the optional LangSmith `evaluate(upload_results=False)` cell in the P6 LLMOps notebook, skipped automatically without a key? **Yes** recommended.

---

## Concept P7: Prompting for grounded generation

**The short version.** The existing P7 lesson is sound on the core contract: the source-only rule, `[doc:page]` citations, one fixed refusal sentence, and index time vs query time (MC-003). Three things are missing:
1. **Message roles and the instruction hierarchy.** v0's chunks sit in the user message, with the same authority as the question. gpt-oss-20b scores 0.639 on prompt-injection hijacking (o4-mini: 0.917).
2. **Structured output.** No concept teaches it, so P7 now owns the basics. Groq supports strict `json_schema` on gpt-oss-20b.
3. **Lost in the middle with real numbers.** In Liu et al.'s 20-document test, GPT-3.5's accuracy with the answer in the middle (53.8%) fell below its accuracy with no documents at all (56.1%).

The Groq window (131,072 tokens) is now verified. The P7 lab's Task 7 calls Groq without the cache, which breaks D-32.

### 1. Sources checked

**Book pages (opened with PyMuPDF 1.26.7; cited 1-based):**

| Page | What it gives P7 (paraphrased) |
|---|---|
| Ch1 p.1/14 | The problem: a model with no access to your report answers from training patterns and may state things your source never says |
| Ch1 p.3/14 | The open-book picture; preparation runs once per document, the query phase runs per question (supports MC-003); no need to stuff whole documents into the prompt |
| Ch1 p.9/14 | Step 8: chunks plus the question go to the model; the answer should come from the document, not memory. **No instruction wording** |
| Ch1 p.10/14 | Algorithm steps 5–6: pass question + chunks; answer grounded in context. No order, labels or budget |
| Ch1 p.12/14 | Simple RAG is overkill when the documents fit in the context window (budget link) |
| Ch3 p.5/14 | Only the "Step 3: Generate an Answer" heading sits at the foot of the page (relevancy grading fills the rest) |
| Ch3 p.6/14 | Generation equals simple RAG with cleaner input; even perfect context does not stop unsupported claims |
| Ch3 p.8/14 | Source highlighting: a separate call finds verbatim supporting segments, like footnotes (citations **after** generation) |
| Ch3 p.11/14 | Reliable RAG suits cases where "I don't know" beats a confident wrong answer; casual Q&A is the overkill case |
| Ch22 p.5/19; App p.15/23 | The book's only position claim: generation prompts weight documents that come **first** (no source, no measurement) |
| Ch22 p.8/19 | Low faithfulness with high context relevance points at the model or the prompt |
| Ch22 p.11–12/19 | Noise robustness: distracting noise (similar text with wrong answers) is the most dangerous kind; a claimed collapse past about half noise, with no citation |
| Ch22 p.16/19 | Safety: prompt injection framed as crafted **queries** only (indirect injection via retrieved text is not discussed) |
| App p.17/23 | Glossary: grounding (traceable to passages) and hallucination |

**Absence check (all 25 PDFs, keyword search):** no "lost in", no prompt-position discussion anywhere. "middle" hits are figure captions or chunk boundaries (Ch8, Ch9, Ch10, Ch20); "position" hits are ranks (Ch22 p.6–7/19), chunk position metadata (Ch8 p.4–5/11) or "proposition" (Ch4). **Confirmed:** the only prompt-position statement is the first-position claim at Ch22 p.5/19 and App p.15/23.

**Repo cells (`upstream/RAG_Techniques` @ `009adba2…`, 0-based; opened):**
- `reliable_rag.ipynb` cell 18: system line tells the model to answer "based upon your knowledge"; `<doc{i}>` blocks with Title/Source; docs before the question; `ChatGroq(llama-3.1-8b-instant, temperature=0)`. Saved output opens with "According to the retrieved documents" and is a numbered list, despite the "three-to-five sentences" rule.
- `multi_model_rag_with_captioning.ipynb` cell 20: same system text; `ChatCohere(command-r-plus)`; passes only `docs[0].page_content`. Cell 15: `k: 1`. Cell 12: the captioning prompt (index time). Saved output states a BLEU number.
- **Licence note:** `RAG_Techniques` is under a **custom non-commercial licence**, not MIT. Quote only short phrases from it (the course already does).

**Existing course files read:** `concepts/P7_grounded_prompting.md` (A–M lesson, 699 lines); `labs/P7_grounded_prompt_lab.ipynb` (35 cells, 7 tasks); `sources/verification/P7/` (`P7_FACTS.md`, `p7_measure.py`, `p7_sources.py`, outputs); 02 P7 card and §4 Gate 1→2; 03 P7 rows and the REVIEWER NOTE on structured output (line ~499); 04 P7 row; 06 §2.4, §2.5, §3.1, §3.3, §6.7, §7.1–§7.5; `concepts/C5_generation_citations.md` D.2–D.7; P1 lesson B.3, D.5; `progress/concept_tracker.csv`, `progress/misconception_log.md`; `sources/EXTERNAL_RESOURCES_REVIEW_2026-10-09.md` (P7 rows); P3 pilot files; `study/FORMAT.md`; both WRITING_STYLE files; `visual-learning-writer` SKILL and HTML spec; skills `rag-evaluation`, `code-based-evaluators`, `llm-observability`, `safety-evals`, `evals-foundations`; `claude-api` skill.
- No `study/reading/P7_*` and no `study/questions/P7_questions.md` exist.
- `sources/coach/transfer_seed_bank.md` opened only to check titles: it has **no P7 seed**; none of the titles in §3 reuse a seed or reserve scenario.

**AE book (paraphrase only):** AE Ch7, 'Evaluating Generation Quality': three generation failure types (hallucination, omission, misinterpretation) and the context-swap probe (replace retrieved documents with unrelated ones; if the answer stays the same, the model ignores context; the fix is usually the prompt). AE Ch1, 'The Gulf of Specification' (prompt gap vs ignored rule), via the review.

**Interview repo (MIT, "Copyright (c) 2026 Om"):** `03-prompt-engineering-and-context/questions.md` Q20, Q21, Q30, Q36, Q43, Q46; `04-rag-and-retrieval/questions.md` Q28, Q44, Q60. Read: Q21, Q30 (03) and Q28 (04).

**External sources (numbered; all external):**

| # | Source | Status |
|---|---|---|
| [P7-1] | N. F. Liu, K. Lin, J. Hewitt, A. Paranjape, M. Bevilacqua, F. Petroni, P. Liang, "Lost in the Middle: How Language Models Use Long Contexts", TACL 12 (2024) 157–173. https://arxiv.org/abs/2307.03172 ; https://aclanthology.org/2024.tacl-1.9/ | **verified**: abstract, ACL Anthology record, and PDF text (§2.1–2.3, Table 1, §3, §4.2, §5, Appendix G Table 6) |
| [P7-2] | C.-Y. Hsieh et al., "Found in the Middle: Calibrating Positional Attention Bias Improves Long Context Utilization", Findings of ACL 2024. https://arxiv.org/abs/2406.16008 | verified (abstract only) |
| [P7-3] | B. Veseli, J. Chibane, M. Toneva, A. Koller, "Positional Biases Shift as Inputs Approach Context Window Limits", COLM 2025. https://arxiv.org/abs/2508.07479 | **verified**: abstract and PDF text (datasets, models, Fig. 5 discussion) |
| [P7-4] | T. Gao, H. Yen, J. Yu, D. Chen, "Enabling Large Language Models to Generate Text with Citations" (ALCE), EMNLP 2023. https://arxiv.org/abs/2305.14627 | **verified**: abstract, §1, §3.3 (citation recall/precision definitions) |
| [P7-5] | E. Wallace, K. Xiao, R. Leike, L. Weng, J. Heidecke, A. Beutel, "The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions", 2024. https://arxiv.org/abs/2404.13208 | **verified**: abstract, §1–§2 |
| [P7-6] | OpenAI, "gpt-oss-120b & gpt-oss-20b Model Card", Aug 2025 (CC BY 4.0). https://arxiv.org/abs/2508.10925 | **verified**: §2.5.1 (Harmony, role order), §4.3 Tables 7–8, §4.5 Table 9. (openai.com page returned 403) |
| [P7-7] | OpenAI, "OpenAI Harmony response format" (cookbook). https://developers.openai.com/cookbook/articles/openai-harmony | verified |
| [P7-8] | openai/harmony repository. https://github.com/openai/harmony | verified (partial: example system and developer messages) |
| [P7-9] | Anthropic, Citations. https://platform.claude.com/docs/en/build-with-claude/citations | verified |
| [P7-10] | Anthropic, Prompting best practices, 'Long context prompting'. https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices (the old `long-context-tips` URL redirects here) | verified |
| [P7-11] | Groq, Structured outputs. https://console.groq.com/docs/structured-outputs | verified |
| [P7-12] | Groq, model page `openai/gpt-oss-20b`. https://console.groq.com/docs/model/openai/gpt-oss-20b | verified |
| [P7-13] | Groq, Reasoning. https://console.groq.com/docs/reasoning | verified |
| [P7-14] | LangChain source, `langchain_classic/chains/combine_documents/base.py` (master, 2026-10-17). https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/langchain/langchain_classic/chains/combine_documents/base.py | verified |
| [P7-15] | `claude-api` skill (bundled; model table cached 2026-10-06): ids, prices, citations vs structured outputs | read locally |

### 2. Gap audit

Tracker: P1 `exposed` (MC-001 open); P7, C2, C4, C5, X3, V1–V3, D4 `not_started`; M2, M3 `exposed`. "Taught" refers to the existing `concepts/P7_grounded_prompting.md` unless named.

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class (core / bridge / next) | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Index time vs query time (overlap is not a prompt setting) | MC-003; C5 wiring; 02 evidence | Yes (D.1); book support Ch1 p.3/14 | P7 (remediation), C2 owns overlap | No (P7, C2 not started) | core | Keep first in Short, with the two-lane diagram; add Ch1 p.3/14 as the book anchor |
| 2 | Parts of a grounded prompt: source-only rule, citation rule, fixed refusal, no outside knowledge, numbered blocks, question last, answer cue | Gate 1→2; 02 evidence; C5 template | Yes (D.2) | P7 | No | core | Keep; teach each part with "what fails without it" |
| 3 | Cite `doc:page`, not the block number | C5 parser; X3 reordering | Yes (D.2, D.6 point 3) | P7 | No | core | Keep; add the contrast with AIQ 04 Q28's `[1][3]` style (breaks under reordering) |
| 4 | Fixed refusal sentence and exact-match detection; its blind spot (paraphrased refusals) | C5 D.6; M2 abstention metrics; V3 | Partly (D.7 toy E) | P7 (sentence); V3 (thresholds) | No | core | Keep; add one line on the trade-off: exact sentence misses paraphrases, a phrase list flags hedged correct answers (review row for V3) |
| 5 | Tokens, window, `max_completion_tokens` caps reasoning + answer; reasoning billed as output | Budget (D.4); J3; C5 D.3 | In P1 (exposed only) | P1 | Exposed, MC-001 open | bridge | One example in place: O2's empty reply at a cap of 12 (P1 B.2). Use the name `max_completion_tokens` (Groq deprecated `max_tokens`, default 1,024) and say reasoning tokens are billed as output |
| 6 | The real window of `openai/gpt-oss-20b` on Groq: 131,072 context, 65,536 max output | D.4 budget; Part K | **Missing** (lesson marks it UNVERIFIED) | P1 / P7 | — | core | State the verified numbers [P7-12]. Then the key insight: at k = 4 the prompt uses under 1% of the window, so the window is not the binding limit; the answer reserve, the rate limit, cost and position effects are |
| 7 | Hidden prompt tokens: the chat template and the provider's system header | D.4 margin; P1 B.3's ~71 | Incomplete (margin 128 is an Assumption) | P1 / P7 | — | bridge (Full) | Explain the Harmony layout [P7-7]; give the offline estimate (~74 tokens, scratch count, UNVERIFIED for Groq) next to P1's logged ~71; keep the margin as a measured-then-chosen value |
| 8 | Message roles and the instruction hierarchy (system > developer > user > assistant > tool); where v0 puts rules, chunks and question | Every LLM call; D4 | **Missing** (review's in-file addition not applied) | P7 | No | core | Short: one paragraph and a role ladder. Retrieved chunks sit in the **user** message, so they carry the same authority as the question. Full: gpt-oss-20b's instruction-hierarchy scores [P7-6] |
| 9 | How Groq maps an API `system` message onto Harmony (developer?) | Role layout of v0 | **Missing**; not in Groq docs | P7 | — | core (as an honest unknown) | Mark UNVERIFIED. Note Groq's reasoning page carries a generic "avoid system prompts" row that names no model (its prompt section names DeepSeek-R1). Make "rules in system vs rules in user" a logged experiment arm, not a guess |
| 10 | Retrieved text is untrusted data; indirect prompt injection | D.8; D4 | One UNVERIFIED sentence (D.8) | D4 | No | next (with one bridge sentence) | One sentence plus the gpt-oss-20b numbers; the book only covers crafted queries (Ch22 p.16/19); link D4 and `safety-evals` |
| 11 | Lost in the middle: what was tested, the result with numbers, the limits | Outcome 2; Gate 1→2; MC-004 | **Incomplete** (abstract only; "no numbers") | P7 | No | core | Rewrite as setup → result → meaning → for you, with Table 6 numbers and the closed-book comparison (§5). Short: the U and the one striking fact; Full: the table |
| 12 | Newer evidence: relative fill of the window shifts the bias; a candidate cause | X3 design; interview | **Missing** | P7 (theory), X3 (experiment) | No | core (Full) | Veseli 2025 [P7-3] and Hsieh 2024 [P7-2]; replace "why it happens is not settled (UNVERIFIED)" with "one proposed cause, not the final word" |
| 13 | Ordering choices: rank order, edges-first, question placement | X3; v4.0 | Partly (edges-first taught; question placement missing) | P7 idea, X3 experiment | No | core | Add: question after the documents (Anthropic reports up to 30% gains [P7-10]); Liu found query before **and** after barely helped multi-document QA [P7-1] |
| 14 | MC-004: position effect is not about minima | Misconception | Yes (D.6) | P7 | No | core | Keep |
| 15 | k trade-off (recall vs tokens, dilution, middle positions) | MC-005; C4 | Partly (D.5) | C4 | No | bridge | Add Liu §5: going from 20 to 50 retrieved documents gave about +1.5 points (GPT-3.5) while retriever recall kept rising |
| 16 | Parametric knowledge, the danger zone, closed-book control | Part I; 06 §7.1 | Partly (D.7) | M2 / 06 §7.1 | M2 exposed | bridge | Add two facts: in Liu, the middle position (53.8%) scored below closed-book (56.1%) for GPT-3.5; gpt-oss-20b's SimpleQA hallucination rate without browsing is 0.914 [P7-6], so ungrounded answers from this model are risky |
| 17 | Faithfulness vs correctness | Part E; M3 | Yes (Part E) | M2 / M3 | Exposed | bridge | Keep; add AE Ch7's third failure type, omission (ignored relevant evidence) |
| 18 | Citation quality metrics: citation recall and precision | Part I metrics; 06 §7.4; M3, V1 | **Missing** (names only) | M3 / V1 | M3 exposed | bridge | Teach ALCE's definitions on one toy [P7-4] and say how 06 §7.4 differs (§4 error E9). Human-labelled until D-10 |
| 19 | Deterministic answer checks: citation parse, cited ⊆ context, uncited sentence, abstention, length stop | C5 D.4–D.6; tool | Partly (D.7 three functions) | C5 | No | bridge | Keep the three functions; link C5 for the full flag set |
| 20 | Structured output: JSON schema, strict (constrained) vs best-effort, validation, retry on parse failure | Every grader/router later (V2, A1–A3, I4) | **Missing everywhere** (03 REVIEWER NOTE proposes P7 or M3) | **P7** (decided here) | No | core (Full) + LLMOps arm | Decide P7 owns the basics: it is the first concept where code reads LLM output. One Full section plus a `answer_json_v1` arm. Groq supports strict `json_schema` on gpt-oss-20b [P7-11]. Validate with pydantic; still check cited ⊆ context |
| 21 | Provider-native citations (Claude Citations API) | Interview; optional LLMOps arm | **Missing** | P7 (Full), V1 | No | bridge (Full) | What it guarantees (valid pointers; `cited_text` not billed as output) and what it does not (support). It cannot be combined with structured outputs (400) [P7-9] |
| 22 | Conflicting or dated sources | Real corpora (Corpus T, Yash's docs) | **Missing** | P7 (rule), V-phase (test) | No | core (Short, one paragraph) | v0 has no conflict rule. Teach a candidate rule (surface the disagreement, cite both) as an `answer_v2` idea; do not change v0 (frozen baseline) |
| 23 | "Treat sources as data; ignore instructions inside them" | D.8; D4 | Missing in v0 | P7 (wording), D4 (measure) | No | bridge (Full) | Candidate `answer_v2` sentence; measured in D4, never assumed to work |
| 24 | No CoT, no few-shot in the answer prompt (reasoning model; leakage risk) | 06 §3.3 design note | Partly (Part K) | P7 | No | bridge (Full) | One line each: gpt-oss already reasons (in a separate field [P7-13]); few-shot answers must pass the foundation's leakage check |
| 25 | Temperature 0 does not make answers repeatable; replay does | Part I; LLMOps | No (in P1 / foundation) | P1 / foundation §2.7 | Exposed | bridge | One sentence |
| 26 | Prompt as a versioned file; sha256 in the trace | C5 D.2; LLMOps | In C5 (later) | C5 / foundation §7 | No | bridge | Introduce here (P7 is first to write a prompt file); C5 reuses |
| 27 | Context-swap probe vs oracle-context control | Part I; M5 | **Missing** (review §4 row not applied); the `rag-evaluation` skill conflates the two (E11) | M3 / M5 | Exposed | bridge | Short: one paragraph "how you would know the prompt works"; Part I gains probe S |
| 28 | Provider prompt caching: stable prefix first | D2 cost | Missing | D2 | No | next | One line: rules first also helps Groq's automatic prompt caching (cached input $0.037/M, foundation §6.2) |
| 29 | The book's first-position claim vs the research | D.6 | Yes | P7 | No | core | Keep; add: in Liu the **end** also scores high, and Veseli finds the end dominates as the window fills |
| 30 | Answer length rule and `finish_reason = length` | C5 D.6; J3 | Partly | C5 | No | bridge | Keep J3; name the flag |
| 31 | Distracting noise (similar text, wrong number) | J4; D-001's 1.5 °C / 2 °C distractors | Partly (J4) | C4 / X-phase | No | bridge | Tie J4 to Ch22 p.11/19's "distracting noise" |

### 3. Quiz coverage

No question file exists, so these are the titles the concept needs (FORMAT.md; one short question each; at most 2 external items).

**Pre (`set=pre`, cold):**
- P7-PRE-01 · Is chunk overlap something you set while building the prompt?
- P7-PRE-02 · Where in a long prompt should the strongest chunk go?
- P7-PRE-03 · Four 1,000-character chunks plus rules: roughly how many tokens?

**Recall:**
- P7-R-01 · Write the parts of a grounded prompt from memory. (MC-003 check)
- P7-R-02 · What did Liu et al. test, and what shape did accuracy take by position? (MC-004 check)
- P7-R-03 · Is the prompt built at index time or query time, and when is overlap set? (MC-003 check)
- P7-R-04 · Why a fixed refusal sentence, and which refusals does exact matching miss?
- P7-R-05 · Which message holds the rules, which holds the chunks, and which has more authority?
- P7-R-06 · Name two things a grounded prompt cannot guarantee.

**Application:**
- P7-A-01 · k doubles from 4 to 8: does the prompt's token count double? (×1.82, S4)
- P7-A-02 · Chunk size doubles per page: does the average block double? (×1.46, S5)
- P7-A-03 · Toy window 6,000, reserve 512, margin 128, fixed 133, blocks 217: how many fit? (24)
- P7-A-04 · With gpt-oss-20b's real window, what actually limits k? (not the window: about 600 worst-case blocks would fit; reserve, rate limit, cost and position effects decide)
- P7-A-05 · Edges-first for k = 6: which ranks sit in the middle? (5 and 6)
- P7-A-06 · Classify six toy answers: valid citation, invalid citation, abstention, uncited.
- P7-A-07 · Read Liu's 20-document row: what does "middle below closed-book" mean for your pipeline?
- P7-A-08 · Your local count is 958, the API reports about 1,030: where do the extra tokens come from?
- P7-A-09 · Name one failure the captioning notebook's answer prompt allows. (02 evidence)

**Transfer (new scenarios; not in the seed bank):**
- P7-T-01 · Two retrieved policy clauses contradict each other (old and new version). What does your prompt say, and how do you check it?
- P7-T-02 · Swapping in unrelated pages leaves the answers unchanged. What does that tell you, and what do you change first?
- P7-T-03 · You move from Groq text citations to Claude's citations feature. Which checks can you drop, and which must stay?
- P7-T-04 · You need answers as JSON for a downstream app. What changes in the prompt and the checks? (strict schema; validation; cited ⊆ context still needed; not combinable with Claude citations)

**Interview (`set=interview`, MIT notice, repo answer shown after the attempt):**
- P7-R-07 · AIQ `03-prompt-engineering-and-context/questions.md` Q30 (build the prompt with irrelevant and contradicting chunks). Our correction: lost in the middle is a generation-side reading effect, not retrieval quality (review §8).
- P7-A-10 · AIQ `04-rag-and-retrieval/questions.md` Q28 (trustworthy citations). Our corrections: its citation recall ("claims that have citations") differs from ALCE's "fully supported" [P7-4]; `[1][3]` block-number citations break under reordering (P7 D.6).

**Key points that the current lesson's Short content would not cover** (to fix when the kit lesson is written): P7-R-05 (roles; gap 8), P7-A-04 (real window; gap 6), P7-A-07 (Liu numbers; gap 11), P7-A-08 (template overhead; gap 7, Full → must move a two-line version into Short), P7-T-01 (conflicts; gap 22), P7-T-02 (context swap; gap 27), P7-T-03/T-04 (Full sections 20–21; T items may draw on Full, but each key point needs one Short sentence).

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| E1 | 02 P7 card, Book line | "Ch3 p.5/14 (generate step)": p.5 holds only the heading; the text is on p.6/14. Ch1 p.10/14 (algorithm) and Ch22 p.5/19 / App p.15/23 (first-position claim) are missing. (Known since P7_FACTS; still not applied.) | Cite Ch1 p.9–10/14, Ch3 p.5–6/14, Ch22 p.5/19 |
| E2 | 02 P7 card | "Position effects are not in the book" is too strong: a first-position claim exists (no U-shape, no source). Re-confirmed by a search of all 25 PDFs | "The U-shape is not in the book; a first-position claim is (Ch22 p.5/19)" |
| E3 | 04 P7 row | `local_rag_huggingface_faiss.ipynb cells 22-24` (cell 23 is markdown); captioning cell 20 missing; Ch1 p.10/14 missing (known; still not applied) | As in P7 G.2 |
| E4 | P7 lesson D.4, K, verification log; P7_FACTS §2 | Groq's window for gpt-oss-20b "UNVERIFIED" | Now verified: 131,072 context, 65,536 max output [P7-12] |
| E5 | P7 lesson D.6, source map, M.1; 01 #39 | "No numbers from the paper" and "2023, TACL" | TACL **vol. 12, 2024**, pp. 157–173; Table 6 and Table 1 numbers verified (§5) |
| E6 | P7 lesson D.6 | "Why it happens is not settled here (UNVERIFIED)" | One proposed cause: a U-shaped positional attention bias [P7-2]; still not settled |
| E7 | P7 lesson D.8 | The review's instruction-hierarchy sentence was not applied; "not a defence (UNVERIFIED for our model)" can now cite evidence | Add the sentence and gpt-oss-20b's numbers [P7-6] |
| E8 | P7 lesson D.4 / H; lab Task 7 (cell 33) | Uses `max_tokens` (deprecated by Groq for `max_completion_tokens`, default 1,024; foundation E3). Task 7 calls Groq **without the cache** (breaks D-32 "every external call is cached") | Route Task 7 through `study/llmops` in record/replay; use `max_completion_tokens` |
| E9 | 06 §7.4 citation recall/precision | Definitions differ from ALCE [P7-4]: 06 recall counts a sentence with **≥1 supporting citation**; ALCE requires the **concatenation of all cited passages** to entail the sentence. 06 precision counts supporting citations; ALCE marks a citation irrelevant only if it fails alone **and** the rest still support the sentence | Name which definition 06 uses and why; keep ALCE as the reference definition |
| E10 | P7 lesson Part I | Context-swap probe (review §4 row) not added; cache key described as "hash of (model, rules, user message, params)" | Add probe S; use the foundation §2.3 canonical key |
| E11 | `.claude/skills/rag-evaluation/SKILL.md`, 'Context swapping' | Describes it as feeding **known-correct** context (that is an oracle-context control). AE Ch7 describes context swapping as feeding **unrelated** documents. Two different probes share one name | Name both: oracle context (localises retrieval) and context swap (detects ignoring context) |
| E12 | P7 lesson verification log | `create_stuff_documents_chain` formatting "UNVERIFIED" | Verified on master: default document prompt is `{page_content}` with separator `"\n\n"`, so metadata is dropped unless a document prompt is passed [P7-14] (the pinned 2024-era notebook's version not checked) |
| E13 | AIQ 03 Q21 (external, MIT) | Says restate the question at the bottom is "high-yield"; Liu found query-aware placement barely changed multi-document QA (it fixed key-value retrieval) | Correct after the learner's attempt |

### 5. What the research says

**[P7-1] Lost in the Middle (Liu et al., TACL 2024).**
- **The study.** Multi-document QA on 2,655 NaturalQuestions-Open queries. Each prompt holds one Wikipedia passage (≤100 tokens) with the answer plus k−1 distractors retrieved by Contriever that do not contain it; 10, 20 or 30 documents (~2K/4K/6K tokens). The answer document is moved through every position. Accuracy = any gold answer string appears in the output. Also synthetic key-value retrieval (75/140/300 JSON pairs, ~4K/8K/16K tokens). Models: GPT-3.5-Turbo (4K, 16K), Claude-1.3 (8K, 100K), MPT-30B-Instruct, LongChat-13B (16K); GPT-4 on a subset.
- **The result.** A U-shape: best at the start, good at the end, worst in the middle; extended-context versions were no better than their base versions.
  ```
  20 documents, accuracy by position of the answer document (Table 6)
                     1st    5th    10th   15th   20th   | closed-book  oracle (Table 1)
  GPT-3.5-Turbo      75.8   57.2   53.8   55.4   63.2   |   56.1        88.3
  Claude-1.3         59.9   55.9   56.8   57.2   60.1   |   48.3        76.1
  ```
  Placing the query before **and** after the data made key-value retrieval near-perfect but barely changed multi-document QA (§4.2). In open-domain QA, 50 retrieved documents instead of 20 added only about 1.5 points (GPT-3.5) and about 1 point (Claude-1.3), while retriever recall kept rising (§5).
- **Limits.** 2023 models; contexts of 2K–6K tokens; exactly one relevant passage; substring-match accuracy; the size of the drop varies by model (Claude-1.3 is much flatter).
- **What it means.** Evidence that is present can still go unused. For GPT-3.5, an answer buried mid-prompt did worse than no documents at all.
- **For the project.** Keep k lean, keep strong evidence at the edges, and treat ordering as an X3 experiment on gpt-oss-20b, not a known fact.

**[P7-3] Positional biases shift as inputs approach the window limit (Veseli et al., COLM 2025).**
- **The study.** Six instruction-tuned open models (Llama-3-70B, Llama-3.1-70B, Llama-3.3-70B, Mistral-Small-24B, Qwen2.5-32B, Gemma-2-27B) on four reasoning datasets (MonoRel, PIR, RuleTaker, BoxTracker) built as retrieval/reasoning minimal pairs. Input length is measured **relative to each model's window**.
- **The result.** The lost-in-the-middle effect is strongest up to about half the window. Beyond that, primacy weakens, recency stays, and the pattern becomes "closer to the end is better". When the model first locates the relevant text, position matters much less; some curves are nearly flat.
- **Limits.** "Retrieval" here means the model finding text inside its own input, not a vector retriever. Synthetic tasks; open 24–70B models only.
- **For the project.** v0 uses about 976 of 131,072 tokens (0.7%, DERIVED). Liu's regime (short contexts, many passages) is closer to ours than Veseli's long-fill regime, but neither tested gpt-oss-20b at k = 4. **Measure; do not assume.**

**[P7-2] Found in the Middle (Hsieh et al., Findings of ACL 2024).** The abstract attributes the effect to a U-shaped attention bias (start and end tokens get more attention regardless of relevance) and reports a calibration that improves RAG by up to 15 points. Abstract only; model-internal fix, not usable through an API. **For the project:** one proposed cause to cite; nothing to implement.

**[P7-4] ALCE (Gao et al., EMNLP 2023).**
- **The study.** A benchmark (ASQA, QAMPARI, ELI5) where systems retrieve and answer with `[n]` citations; metrics for fluency, correctness and citation quality, checked against human judgements. Prompts list documents first, then question and answer, with two demonstrations.
- **Definitions.** Citation recall per statement = 1 if it has at least one citation and an NLI model (TRUE, T5-11B) says the concatenated cited passages entail it. A citation is "irrelevant" if it does not support the statement alone **and** removing it leaves the statement still supported; citation precision = share of citations that are not irrelevant (and whose statement has recall 1).
- **The result.** On ELI5, the best models lacked complete citation support about half the time. A closed-book model with citations added afterwards had good correctness but much worse citation quality.
- **For the project.** Correct-but-unsupported answers are a measured, common failure: exactly what P7's citation rule and Part I aim at. Use ALCE's definitions for M3/V1 labels (E9). An NLI model would be a later V1 option, not P7.

**[P7-5] The instruction hierarchy (Wallace et al., 2024).** System messages (developer) outrank user messages, which outrank model and tool outputs. Fine-tuning GPT-3.5 to ignore lower-privilege instructions improved robustness a lot (for example, system-prompt-extraction defence +63%, jailbreak robustness +30% on held-out attacks), with some over-refusal. **For the project:** retrieved text is third-party content; in v0 it sits in the user message.

**[P7-6], [P7-7] gpt-oss and Harmony.**
- The model card says gpt-oss follows the order System > Developer > User > Assistant > Tool. The Harmony system message holds identity, dates, the reasoning level and channels; the **developer** message holds what other APIs call the system prompt. Reasoning goes to an `analysis` channel that should not be shown to users.
- Instruction-hierarchy evals (higher is better): gpt-oss-20b prompt-injection hijacking **0.639** vs o4-mini 0.917; phrase protection developer/user **0.661** vs 0.912. The card says the system message is a weaker mitigation on gpt-oss than on o4-mini.
- Hallucination without browsing: gpt-oss-20b SimpleQA accuracy 0.067, hallucination rate **0.914**; PersonQA 0.155 / 0.532.
- **For the project:** our generator is weak at resisting injected instructions and weak on world facts, so grounding plus checks matter more, not less. How Groq renders an API `system` message into Harmony is **UNVERIFIED**.

**[P7-9], [P7-10] Anthropic.**
- Citations: set on each `document` block (all or none); responses come back as text blocks with `citations` carrying `cited_text`, `document_index` and a location (`char_location` 0-based exclusive end; `page_location` 1-based; `content_block_location` 0-based). For RAG chunks the docs suggest one plain-text document per chunk (sentence-level citations) or custom-content documents (no further chunking). `cited_text` is not counted as output tokens (nor as input when passed back); input rises slightly. Pointers are guaranteed valid; whether the passage supports the claim is not. **Citations + `output_config.format` → 400.**
- Long-context guidance: long documents at the top, query at the end (up to 30% better in Anthropic's tests, especially multi-document); wrap each document in `<document>` with `<document_content>` and `<source>`; for long tasks, ask for relevant quotes first.
- **For the project:** v0 already puts the question last. The quote-first idea is a candidate arm, but it costs output tokens (reasoning is billed as output too).

**[P7-11]–[P7-13] Groq for gpt-oss-20b.**
- Window 131,072; max output 65,536; capabilities include JSON Object Mode, JSON Schema Mode, Reasoning, Tool Use. Prices $0.075 / $0.30 per M, cached input $0.037.
- Structured outputs: `json_schema` with `strict: true` (constrained decoding) supported on `openai/gpt-oss-20b`; strict needs every property `required` and `additionalProperties: false`. Streaming and tool use are not supported together with structured outputs. `json_object` needs the word JSON in the prompt and does not enforce a schema.
- Reasoning: `reasoning_effort` low/medium/high; reasoning returned in a separate `reasoning` field by default (`include_reasoning`); `reasoning_format` not supported on gpt-oss. Whether reasoning counts toward `max_completion_tokens` is not stated on that page; P1's empty reply at a cap of 12 is the course's evidence that it does.

**Current practice (2024–2026).** Labelled, delimited documents; stable ids; question after the documents; explicit "say so if not in the sources"; per-claim citations validated in code; provider-native citation features where available; structured outputs for machine-read answers; retrieved text treated as untrusted. Frameworks still default to dropping metadata in "stuff" chains [P7-14].

**Pitfalls (with evidence).** Permissive prompts (repo cells 18/20); answers from memory with borrowed valid labels (C5 T19); position loss (Liu); more documents with little gain (Liu §5); cut-off answers looking like citation failures (C5 D.6); injection through chunks (gpt-oss card); exact-match refusals missing paraphrases (P7 D.7 toy E).

**How to evaluate.** Hold retrieval fixed (same chunk ids per item), change one prompt element per arm. Tier 1: abstention exact match, paraphrased-refusal flag, citation format, cited ⊆ context, page-hit, uncited sentences, length stop, JSON validity. Tier 2: human faithfulness and citation-support labels. Controls: closed-book (parametric knowledge) and context swap (ignores context). Retrieval metrics stay out of this comparison entirely.

**Interview questions (typical):** How do you build the prompt from retrieved chunks (AIQ 03 Q30)? How do you make citations trustworthy (AIQ 04 Q28)? Where do you put instructions and 50 documents in a long context (AIQ 03 Q21)? JSON mode vs constrained decoding (AIQ 03 Q36)? System vs user vs retrieved document in conflict (AIQ 03 Q46)?

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).**
1. A grounded prompt turns "here are some chunks" into a contract: answer only from these numbered sources, cite every fact as `[doc:page]`, and give one fixed sentence when the sources are not enough.
2. It is built at query time, once per question, from chunks that already exist; chunk size and overlap were fixed at index time, and nothing in the prompt changes them.
3. Rules, labelled blocks, the question and a reserve for the answer **and the model's hidden reasoning** share one token budget; on gpt-oss-20b the 131,072-token window is rarely the limit, but the reserve, cost, rate limits and position effects are.
4. Where evidence sits matters: in Liu et al., accuracy was highest with the answer document first or last and lowest in the middle, for one model even below answering with no documents, so keep the context lean, put the best evidence at the edges, and measure on your own model.
5. A prompt is a request, not a guarantee: retrieved text carries user-level authority and can contain instructions, and models still add unsupported claims, so every answer goes through cheap code checks now and faithfulness labels later.

**The theory in one read (12 linked ideas).**

| # | Idea | Formula / rule |
|---|---|---|
| 1 | Two phases | index: f(document) once · query: g(question, top-k) per question |
| 2 | The prompt contract | P = rules ⊕ block₁…block_k ⊕ question ⊕ "Answer:" |
| 3 | Roles and authority | system > developer > user > assistant > tool; v0: rules = system, blocks + question = user |
| 4 | Labels | citation = `doc_id:page` (stable under reorder); block number i (changes with order) |
| 5 | Fixed refusal | abstained = norm(answer) == norm(S_refuse) |
| 6 | Budget | fixed + Σ_{i≤k} bᵢ ≤ W − R − m, R = `max_completion_tokens` (reasoning + answer) |
| 7 | k that fits | k_fit = ⌊(W − R − m − fixed) / b_max⌋ |
| 8 | Hidden tokens | usage.prompt_tokens ≈ n(your text) + template overhead (~71 logged, P1 B.3) |
| 9 | Position effect | acc(position) is U-shaped (Liu Table 6); shifts toward recency as fill passes ~50% (Veseli) |
| 10 | Edges-first | order = [1, 3, 5, …, 6, 4, 2] |
| 11 | k trade-off | more k → recall ↑, tokens ↑, more evidence mid-prompt; reader gains saturate (Liu §5) |
| 12 | Checks | cited ⊆ context; uncited sentences; page-hit = 1[cited pages ∩ gold pages ≠ ∅]; ALCE recall/precision (Full) |

**Formula-sheet items:** the budget inequality; k_fit; ratio when k doubles = (fixed + 2Σb)/(fixed + Σb); edges-first rule; abstention normalisation; page-hit; invalid-citation rate; ALCE citation recall and precision; cost per call = in × $0.075/M + (out incl. reasoning) × $0.30/M.

**Step-by-step outline (running example: Corpus D, D-001 with the lab's CHUNKS4, then D-009 for abstention).**
1. Where are we? Index lane vs query lane; overlap lives on the left (MC-003).
2. Write the four rules; say what fails without each (repo cells 18 and 20 as the bad version).
3. Label the blocks `[i] (climate:p)`; question last; "Answer:".
4. Count: 958 tokens (S4); anatomy of P1's 976 (S3): the chunks are the budget.
5. Budget: toy W = 4,096 → 15 blocks (S6); real W = 131,072 → about 600 worst-case blocks (DERIVED: (131,072 − 512 − 128 − 133)/217 = 600.4), so the window is not the limit; what is.
6. Roles: which message each part goes in; chunks share the question's authority; the hidden Harmony system header (≈71 logged).
7. Order: rank order vs edges-first; Liu's 20-document row; why D-001's p.23 distractor (1.5 °C, 2 °C) mid-prompt is the risk to test.
8. Check the answer: toy answers A–F (S9) → flags; D-009 (IPCC year, not in the PDF) must give the fixed sentence.
9. How you would know it works: closed-book and context-swap controls (one paragraph; Part I).
10. Conflicts and dated sources: a candidate rule for `answer_v2` (not v0).
11. (Full) Answers as JSON with a strict schema; Claude's citations feature; why the two do not combine on Claude.

**Visuals that earn their place.**

| Visual | What it shows |
|---|---|
| Two-lane flow (index vs query) | Overlap is decided before any question exists (MC-003) |
| Stacked bar: 976-token prompt + 512 reserve + ~71 hidden | The chunks are the budget; the reserve and hidden tokens are real |
| Interactive budget slider (W toggle toy/real, R, m, k, block size) | k_fit changes; without a reserve the answer has no room |
| Line chart of Liu Table 6 (two models) with a dashed closed-book line | The U, and "middle below closed-book" for GPT-3.5 (external data, labelled) |
| Edges-first reorder diagram (k = 8) | Rank vs position; the weakest ranks land in the middle |
| Role ladder with v0's placement | Chunks sit at user level, below the rules |

**Full only:** Veseli and Hsieh; the Harmony template and the overhead estimate; ALCE definitions with a toy and how 06 differs; structured outputs on Groq (strict vs best-effort, validation, retry); Claude Citations; the repo prompt audit table (S7); the book's first-position claim vs research; prompt caching line; no-CoT / no-few-shot note; "sources are data" sentence and gpt-oss injection numbers.

### 7. Verify notebook plan

`study/notebooks/P7_grounded_prompt_verify.ipynb`, framework-free, Plotly for charts, offline. Reuses `sources/verification/P7/p7_measure.py` functions (P3 pattern: setup cell, one section per lesson section, a CHECKS list, a Result cell).

| § | Recomputes | Data / code | Check |
|---|---|---|---|
| 1 | Index vs query stage sort | 8 stage names | = S10 fingerprint |
| 2 | v0 prompt for D-001, token anatomy 107/36/803/20/10 | climate PDF, CHUNKS4, tiktoken `o200k_harmony` | = S3, S4 (958) |
| 3 | Harmony overhead estimate (~74) vs P1's logged ~71 | rendered template string, tiktoken | labelled estimate; not asserted against Groq |
| 4 | Budget and k_fit; slider for W (4,096 / 8,192 / 131,072), R, m | S5 block stats | = S6; 600 at real W (DERIVED) |
| 5 | k ×2 and chunk size ×2 ratios | S4, S5 | ×1.82, ×1.46 |
| 6 | Liu Table 6 chart + closed-book lines | numbers typed from [P7-1], cited | values match the table |
| 7 | edges_first for k = 4, 5, 8 | function | = S8 |
| 8 | Citation parse, invalid citations, abstention on toy answers; ALCE recall/precision on one hand-labelled toy (labels given, no NLI model) | S9 answers | = S9; toy values DERIVED |
| 9 | Repo prompt audit | prompt strings | = S7 |
| 10 | (optional) Replay cell: D-009 and D-001 under permissive vs v0 | `study/llmops` cache, `replay` mode | skipped with a message if the 4 keys are missing |

- **LLM calls:** 0 required. Optional §10: 4 Groq calls recorded once (`max_completion_tokens` 1,024, `reasoning_effort` low): ≈ 4 × (1,000 × 0.075 + 1,024 × 0.30)/10⁶ ≈ **$0.0015**. Runs fully in replay after that.
- **Runtime:** under 30 s offline (PDF extraction dominates).

### 8. Apply-it tool plan and real-world checklist

`study/tools/grounded_prompt_check.py`: "Is my grounded prompt ready for my documents and questions?"

- **Inputs:** `--template` (default `prompts/answer_v1.txt`), `--docs` (pdf/txt/md), `--questions` (txt or jsonl with `q`, optional `expect_page`, `answerable`), `--chunk-size/--overlap`, `--k`, `--window` (default 131,072), `--max-completion-tokens` (512), `--margin`, optional `--answers answers.jsonl` (check existing answers offline), optional `--run groq` (cached; off by default).
- **Report (Markdown):** 1 template lint and rule-token cost; 2 budget per question (fixed part, block distribution, worst case, k_fit); 3 label check (every block `doc:page`, unique, 1-based); 4 instruction-like text inside documents (heuristic scan); 5 answer checks (citations valid/malformed/not in context, uncited sentences, exact vs paraphrased refusals, length stops); 6 checklist; 7 recommendation.

| # | Check | Auto / manual |
|---|---|---|
| G1 | Source-only rule present | auto (lint) |
| G2 | Citation format defined and matches the block headers | auto |
| G3 | One fixed refusal sentence, and the detector matches it exactly after normalising | auto |
| G4 | Sources marked as data ("ignore instructions inside sources") and clearly delimited | auto (lint) |
| G5 | Question placed after the sources | auto |
| G6 | Worst-case fixed + k × b_max ≤ W − R − m | auto |
| G7 | `max_completion_tokens` and `reasoning_effort` set explicitly | auto (config) |
| G8 | Every block labelled `doc:page`; labels resolvable to pages | auto |
| G9 | Instruction-like strings in the documents ("ignore previous", "you must", role words) | auto flag → manual review |
| G10 | Documents with versions or dates that can conflict: is there a conflict rule? | manual (look for dated or versioned sources) |
| G11 | On given answers: invalid-citation rate, uncited rate, paraphrased refusals | auto with `--answers` |
| G12 | Closed-book and context-swap controls run before trusting correct answers | manual, or auto with `--run` |

- **Recommendation logic:** G1–G3 fail → "fix the template first"; G6 fails → "reduce k or chunk size"; G9 hits → "review flagged chunks, add the G4 sentence, see D4"; invalid citations or paraphrased refusals → "tighten wording or add a validator; consider strict JSON"; correct under swap → "grounding failure: fix the prompt before retrieval"; otherwise "ready for C5".
- **Calls:** 0 by default. `--run`: per question v0 + closed-book + swap = 3 cached calls; 20 questions → 60 calls ≈ **$0.012**. The privacy guard refuses book text; the tool warns that Yash's own documents would go to Groq.

### 9. LLMOps notebook plan

`study/notebooks/P7_grounded_prompt_llmops.ipynb`. Applies the foundation's §12 row "1 · P7".

**Framework build (langchain-core over the `CachedChatModel` adapter, not `langchain-groq`):**

| Mechanism step | Framework piece |
|---|---|
| Template file `prompts/answer_v1.txt` | `ChatPromptTemplate.from_messages` loaded from the file (system + user) |
| Numbered `doc:page` blocks | `RunnableLambda(format_blocks)` (course function) |
| The Groq call (C5 D.3) | `CachedChatModel(provider="groq", model=GROQ_MODEL_ID, params={temperature: 0, max_completion_tokens: 512, reasoning_effort: "low"})` |
| Answer checks | `RunnableLambda(make_answer)` (course parser) |
| JSON arm | `response_format` json_schema strict + pydantic validation |

Defaults to name: `create_stuff_documents_chain` drops metadata (`{page_content}`, `"\n\n"`) [P7-14]; `ChatPromptTemplate` f-string templating (literal braces in template text must be doubled); `ChatGroq` defaults temperature 0.7, retries 2, effort unset → server `medium` (foundation §9.2); `langsmith.evaluate` uploads unless `upload_results=False`. No LangGraph: the flow is linear.

**Dataset.** Stage 1 (Phase 1, now): the 10 draft seeds (06 §6.7), each with a frozen context: the gold window plus 3 distractor windows, fixed chunk ids (retrieval held fixed). D-009 and D-010 are the unanswerable items. Stage 2 (after C5 and M1): the M1 dev split, 20 items, as P7 Part I. Swap context: hand-written neutral passages (no licence risk).

**Arms (one change each; prompt files, never edited):** A `answer_permissive_v1` (repo cell 18 line) · A′ `answer_v1_no_source_only` · B `answer_v1` (= 06 §3.3) · C `closed_book_v1` · S = B with swapped context · B-json `answer_json_v1` (strict schema: sentences with citations, `abstained`). Previous version = the repo's permissive prompt (there is no earlier course version).

**Evaluators.** Tier 1 (code): abstention exact, paraphrased-refusal flag, citation format, cited ⊆ context, page-hit vs gold page, uncited sentences, `finish_reason = length`, empty, JSON schema validity, short-answer contains-match (D-002 "2015", D-008 HFCs), correct-under-swap. Tier 2: Yash labels support for every non-abstained B and A answer (≤ 20 in stage 1). No judge (D-10). Report per arm with n; no abstention claims from 2 items.

**Tracing.** JSONL spans per foundation §3.3 plus `prompt_version`, rendered-prompt sha256, role layout, local token count vs `usage.prompt_tokens` (overhead drift), reasoning tokens, `finish_reason`, `abstained`, citations, flags, `cache_key`. Phoenix locally; LangSmith only inside `tracing_context` after `privacy.assert_corpus_is("D")`.

**Calls and cost (Groq, upper bounds at the output cap):**

| Run | Calls | Tokens | Cost |
|---|---|---|---|
| Stage 1: 10 items × (A, A′, B, C, S, B-json) + B variance sample 1 | 70 | ≈ 61.5K in + 35.8K out ≈ 97K | ≈ **$0.015** |
| Stage 2: 20 dev items × (A, A′, B, C, S) + B variance | 120 | ≈ 103K in + 61K out ≈ 164K | ≈ **$0.026** |
| Optional Claude: Haiku 5.5, effort low, v0 + Citations API on 10 seeds | 20 | ≈ 1.2K in, ≤ 2K out each | ≈ **$0.022** |

Rate limits (30 RPM, 8K TPM, 200K TPD; plan UNVERIFIED): stage 1 ≥ 12 min; stage 2 ≥ 21 min and near a day's quota, so runs are resumable. Every call goes through `study/llmops` (record once, then `replay`); the notebook runs with no key once `replay_manifest.json` keys exist.

**Track and compare:** cost per question (if called vs paid), p50/p95 latency excluding cache hits, prompt/completion/reasoning tokens per arm, Groq `queue_time`, metric deltas B vs A, B vs A′, B vs C.

**Monitoring and feedback.** Monitor page: abstention rate, invalid-citation rate, length-stop rate (alert > 5%), paraphrased-refusal rate, overhead drift (template change), `system_fingerprint` change. A failure goes to the M5 log with the AE "prompt gap or ignored rule?" column, then to the golden set and a T1 parser test or T2 abstention test.

**Lifecycle and skills.** Analyze: read the 10 stage-1 traces, note the first failure (`error-analysis`, `evals-foundations` gulf of specification). Measure: tier-1 evaluators (`code-based-evaluators`), retrieval held fixed (`rag-evaluation`). Improve: one prompt change per run (`improving-llm-agents`). dev → CI (replay test, T1 format checks; `ci-cd-evals`) → monitor (`llm-observability`). Injection is a link to D4 (`safety-evals`).

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Answer LLM (default) | Groq `openai/gpt-oss-20b`, `reasoning_effort="low"`, `max_completion_tokens` 512 | via `groq` 1.7.0 | yes | no (replay yes) | $0.075 / $0.30 per M; ≈ $0.015 stage 1 | Apache-2.0 (SDK) | yes |
| Optional comparison + native citations | Claude Haiku 5.5 `claude-haiku-5-5`, effort low, no temperature | `anthropic` 1.11.0 | no | no | $0.10 / $0.50 per M; ≈ $0.022 per 20 calls. Worth it only for the Citations arm (shows what an API guarantees) | MIT | yes (D-32, when credits exist) |
| Not recommended for P7 | Claude Sonnet 5.5 | — | — | — | ≈ 20× Haiku for the same arm | — | comparison arm belongs to C5 |
| LLM feature: system role | Groq accepts `system`; Harmony mapping to developer **UNVERIFIED** | — | — | — | — | — | yes, logged as an arm |
| LLM feature: structured output | Groq `json_schema` strict on gpt-oss-20b; `json_object` all models (verified [P7-11]); not with streaming or tools | — | — | — | — | — | yes |
| LLM feature: long context | 131,072 window, 65,536 max output (verified [P7-12]) | — | — | — | — | — | yes |
| LLM feature: reasoning | effort low/medium/high; separate `reasoning` field; billed as output | — | — | — | — | — | yes |
| LLM feature: citations (Claude) | GA, all active models; 400 with `output_config.format` (verified [P7-9]) | — | — | — | `cited_text` not billed as output | — | optional |
| Tokenizer | `tiktoken` (`o200k_harmony`) | 0.14.0 | yes | yes | — | MIT | yes |
| Harmony renderer (optional) | `openai-harmony` | 0.0.8 | no | yes | — | UNVERIFIED (PyPI field empty) | not needed: tiktoken reconstruction suffices |
| Schema validation | `pydantic` / `jsonschema` | 2.13.5 / 4.26.0 | yes (transitive) | yes | — | MIT | yes; declare pydantic if imported directly |
| Charts, data | `plotly`, `numpy`, `pandas`, `pymupdf==1.26.7` | installed | yes | yes | — | — | yes |
| Framework core | `langchain-core` | 1.6.6 | no | yes | — | MIT | yes (LLMOps only) |
| Groq via LangChain | `CachedChatModel` adapter (foundation §9.3) | course code | planned | yes | — | ours | yes; `langchain-groq` conflicts (groq < 1.0) |
| Graphs | `langgraph` | — | no | — | — | — | not needed (linear flow) |
| Hosted tracing / datasets | `langsmith` | 0.14.4 | no | SDK yes | `LANGSMITH_API_KEY`, free plan | MIT | climate corpus only |
| Local tracing | JSONL (default) + `arize-phoenix-otel` 0.17.2 + `openinference-instrumentation-langchain` 0.1.78; server `uvx arize-phoenix@20.19.0` | — | no | yes | — | Apache-2.0 / ELv2 | yes |
| Shared cache, cost, evals | `study/llmops/` | planned | no | yes | — | ours | required |

Install lines (do not run): `uv add --group llmops langchain-core==1.6.6 langsmith==0.14.4 arize-phoenix-otel==0.17.2 openinference-instrumentation-langchain==0.1.78` · optional `uv add --group llmops anthropic==1.11.0` · if pydantic is imported directly: `uv add pydantic==2.13.5`.
Keys: `GROQ_API_KEY` (present); optional `ANTHROPIC_API_KEY`, `LANGSMITH_API_KEY` (+ `LANGSMITH_ENDPOINT`). Nothing heavy; no GPU.

### 11. Open questions for Yash (preferences only)

1. Run the optional Claude Citations arm (Haiku 5.5, 20 calls, about $0.02) when credits exist? (yes / no)
2. Run LLMOps stage 1 on the 10 seed items now in Phase 1, or wait for the M1 dev split? (now / later)
3. Swap context: hand-written neutral passages (recommended) or text from the repo's Nike report? (handwritten / nike)

---

## Phase-level notes

### 1. Study order

03's prerequisite edges allow several orders. The current numbering makes concepts lean on ones that come later:
- P4 and P5 use Hit@k and MRR, which P6 teaches.
- P6 uses qrels, which P2 teaches.
- P2 uses MiniLM cosines, which P4 teaches.

**Recommended order (decision 5): P1 → P2 → P6 → P3 → P4 → P5 → P7.**
- It respects every edge in 03: P3 after P1 and P2; P4 after P1 and P2; P5 after P4; P6 after P2; P7 after P1.
- With it, P6's qrels bridge shrinks to one line, and P3, P4 and P5 no longer need Hit@k/MRR bridges.
- P2 still needs a two-sentence dense bridge, because P2 must come before P4 in any valid order.
- P1's lab and Part L are still unfinished (tracker: `exposed`). Finish them before P2.

### 2. One running example

The helpers found two versions of the climate PDF in use:
- the old 91 cross-page windows, used by the P1, P2 and P4 FACTS files and labs;
- v0's 97 per-page chunks, used by the P3 verify notebook, C4, and the P5 and P6 plans.

**Decided for the build:**
- Every new **retrieval** example (P2 step 10, P4, P5 and P6) uses v0's 97 chunks with the 06 §6.7 draft seeds. Each verify notebook re-measures its numbers offline. P4's blueprint below was written on the 91 windows, so its builder switches it.
- Corpus statistics that do not depend on chunking, such as P1's token ratios, can stay on the 91 windows.
- Where a lesson reuses a 91-window FACTS number, it says so in one line, as C4 already does. The existing labs stay unchanged.

The draft seeds are LLM-drafted and not human-verified. They also saturate: both retrievers reach CE@4 = 8/8. Every number on them is an observation, never a result.

### 3. Conventions to define once and reuse

| Convention | Needed in | Owner | Rule |
|---|---|---|---|
| Tie rule at the k-th place | P2 (toy q4), P5, P6, C4, M2 | P5 | Take every id scoring at least the k-th score, sort by (−score, id), then cut to k. trec_eval and `InMemoryVectorStore` order ties differently, so align them before any cross-check |
| The "recall" name table | P5, P6, interview prep | P6 | IR Recall@k · hit rate (Success@k) · ANN recall · RAGAS context recall |
| Score direction | P4, P5, C4, R1 | P4 | FAISS L2 is squared, lower = closer. sentence-transformers' euclidean is −L2. LangChain relevance is 1 − d/√2 and can go negative. Cosine: higher = closer |
| Output budget | P1, P7, C5, 06 | P1 | `max_completion_tokens` covers reasoning plus answer. Read `finish_reason` before the text. Reasoning is billed as output |
| Citation parser | P7, C5, V1 | C5 (one implementation) | `[doc:page]`; cited ⊆ context; ALCE's definitions for human labels |
| Metric code | P6, M2, `llmops/evals.py` | P6, then M2 | `p6_metrics` plus `contracts_check`. One policy for items with no relevant chunk: filter answerable items once, and assert n_rel ≥ 1 |
| Embedding cache key | P4, C3, foundation | C3 | Add `output_dimension`, `embedding_type` and `truncate` (foundation E2) |

### 4. Ownership decided in this phase

- **P2** owns the inverted index in full; P3 §3 is a recap. P2 also owns qrels, pooling and the labelling guideline.
- **P6** owns the metric definitions, the "recall" name table and the cost of treating unjudged chunks as not relevant.
- **P5** owns ANN mechanics. R2 owns filter selectivity and filtered ANN in depth. D2 and D3, not D4, own ANN at scale.
- **P7** owns structured-output basics, which a 03 reviewer note had left open. X3 owns the ordering experiment; D4 owns injection testing.
- **P4** owns the score-direction table and the Cohere embed settings; C3 owns the cache key.

### 5. Effects on other phases

- **C3:**
  - Add the three key fields.
  - Normalise Cohere float vectors ourselves, assert unit length, and record the raw norms once.
  - Settle the context length with one call using `truncate="NONE"` on the ~13k-token climate text. Cohere's docs say 128k; the API's model list at O2 said 8,192. Which one the endpoint enforces is UNVERIFIED. It does not matter for 1,000-character chunks.
- **C5 and 06:**
  - Rename `max_tokens` to `max_completion_tokens`.
  - Log `reasoning_tokens`, `cached_tokens` and `finish_reason`.
  - Keep `answer_v1` frozen. New prompt rules (a conflict policy, "sources are data", JSON answers) enter as `answer_v2` arms.
- **M1:** the draft seeds saturate, so harder items are needed. Label from a pool of both BM25 and dense results, never one retriever's.
- **M2:** report Judged@k (or Hole@k) next to every retrieval metric. Use one tie rule and one policy for items with no relevant chunk.
- **M4:**
  - gpt-oss's README recommends temperature 1.0, but the course pins 0; the flip-rate run decides.
  - Reciprocal rank takes only a few values per question, which is one reason small sets are noisy.
- **X3:** v0 fills about 0.7% of gpt-oss-20b's window. Position effects on this model must be measured, not assumed.
- **V1 and M3:** use ALCE's citation recall and precision for labels; 06 §7.4's definitions differ.
- **Foundation §6.3:** the Claude cost estimates reuse Groq token counts. A Claude arm should count with `count_tokens`, which is free and can be cached.
- **Project skill `rag-evaluation`:** its "context swapping" describes feeding known-correct context, which is an oracle control. AE Ch7's context swap feeds unrelated documents. Reported only; the skill was not edited.

### 6. Errors in shared files, grouped for the Session 13 correction list

Details are in each concept's §4. Nothing was edited.

| File | Errors (concept and §4 id) |
|---|---|
| 02 cards | P1 E1–E2 (temperature-0 outcome outdated; no reasoning-budget outcome) · P2 E1–E5 (Pre line; "no IR framing" too strong; repo cells missed; IIR chapters; top-K pages) · P4 E1–E4 (the FAISS default comes from LangChain; graph_rag cell 7; missing pages; no Cohere outcome) · P5 E1–E2 (missing pages, including Ch2 p.9/11; dartboard cell 13, not 23) · P6 E5 (App p.15/23) · P7 E1–E2 (Ch3 p.6/14, not p.5; a first-position claim does exist) |
| 03 | P1 E4 (Ch15 p.1/12) · P6 E6 (P6 implements the metrics, not M2) |
| 04 | P1 E3 · P2 E6–E7 · P4 E2, E5 · P5 E3–E5 (DV-04: FAISS is a library, not a flat index) · P6 E4 · P7 E3 |
| 06 | Foundation E3 (`max_tokens`) · P1 E11 (cost formula lacks cached input) · P4 E7–E10 (Cohere row stale; unit-vector assumption; key fields) · P6 E1 (the nDCG formula is Burges 2005, not Järvelin & Kekäläinen 2002) · P7 E9 (citation recall and precision differ from ALCE) |
| 01 | P2 E12 (no IIR Ch1 row) · P6 E7 (#45 never opened; #47 should be the BEIR paper) |
| 08 | P1 E8 (review §3a row 3 never applied) · P5 E10 (faiss wheels are now verified) |
| Existing lessons and labs | P1 E5–E7, E9–E10 · P2 E8–E11, E13 · P4 E6, E11–E14 · P5 E6–E9, E11 · P6 E2, E8, E11–E12 · P7 E4–E8, E10, E12 · P3 HTML (see Concept P3) |
| Project skill | `rag-evaluation`, context-swap wording (P7 E11) |
| O2 record | P1 E12 (no reasoning tokens or `finish_reason` logged) |
| External sources (correct them in our answer keys, after the quote) | AIQ 02 Q10–Q11 (P1 §3) · AIQ 04 Q8 (P5 E12) · AIQ 04 Q43 and 07 Q22 (P6 E9–E10) · AIQ 03 Q21 (P7 E13) · IIR §8.5's 0.7878 misprint (P2 E14) · AE Ch7 nDCG (P6 E13, already logged) |

### 7. How this research was done, and its limits

- **Method.** Six helpers each audited one concept with `RESEARCH_PROMPT.md` §2–§7 and the foundation. The lead then did four things:
  - read every result in full;
  - re-checked key facts independently: tiktoken's `KeyError` on the `.env` model id; faiss-cpu 1.15.1's licence, date and Windows wheel; hnswlib's source-only last release; Cohere's model list, including embed-v5.0; and the D-007 nDCG arithmetic;
  - settled the conflicts: the embed-v4.0 context length (§5), the running example (§2), and the `pytrec-eval-terrier` pin;
  - removed one false error. A helper had flagged the course's wording about "MIT repos". It is correct: the two MIT repos are named, and `RAG_Techniques` is under its own non-commercial licence.
- **Source count.** 107 external sources are listed, against the brief's guide of about 25 per phase. Each helper researched on its own, and most entries are single documentation pages or PyPI records. Each is marked verified or UNVERIFIED below.
- **Hidden transfer seeds.** Helpers opened the coach's seed bank only to avoid collisions. Every description of a seed or reserve scenario was removed from this file; only "checked" statements remain.
- **Scratch numbers.** Every number from an offline probe is labelled "probe", "scratch" or "DERIVED". None is a course fact until a verify notebook logs it in FACTS.
- **Copyright.** This file was compared word by word with the full text of the book (all 25 PDFs, 320 pages) and with all 12 chapter files of the AE book.
  - The longest run shared with the book is 9 words: the book's own example question, "What is the main cause of climate change" (Ch1 p.8/14), which P2 uses as its running query.
  - The longest run shared with the AE book is 7 words (AE Ch7, NDCG section, quoted in P6 E13).
  - Both are under the 15-word limit. The page extracts were then deleted.

---

## Sources

Every external source the six audits used, numbered across the phase. Each id ([P1-1] …) is the one cited inside its concept section; the concept's §1 gives what was tested and its limits. Book pages, repo cells, course files and AE book sections are listed in each concept's §1. Status as recorded by the helper that opened it (2026-10-17).

1. **[P1-1]** Groq, model page `openai/gpt-oss-20b` — https://console.groq.com/docs/model/openai/gpt-oss-20b — verified
2. **[P1-2]** Groq, API reference — https://console.groq.com/docs/api-reference — verified
3. **[P1-3]** Groq, Reasoning — https://console.groq.com/docs/reasoning — verified
4. **[P1-4]** Groq, OpenAI compatibility — https://console.groq.com/docs/openai — verified (also read 2026-10-09, P1_FACTS S-web)
5. **[P1-5]** groq-python `completion_usage.py` — https://raw.githubusercontent.com/groq/groq-python/main/src/groq/types/completion_usage.py — verified (source)
6. **[P1-6]** tiktoken `model.py` — https://raw.githubusercontent.com/openai/tiktoken/main/tiktoken/model.py — verified
7. **[P1-7]** tiktoken README — https://github.com/openai/tiktoken — verified
8. **[P1-8]** openai/harmony README — https://github.com/openai/harmony — verified
9. **[P1-9]** openai/gpt-oss README — https://github.com/openai/gpt-oss — verified (also fetched 2026-10-09 by the review)
10. **[P1-10]** Sennrich, Haddow, Birch, "Neural Machine Translation of Rare Words with Subword Units", ACL 2016 — https://arxiv.org/abs/1508.07909 — verified (abstract)
11. **[P1-11]** Kudo & Richardson, "SentencePiece", EMNLP 2018 demo — https://arxiv.org/abs/1808.06226 — verified (abstract)
12. **[P1-12]** Petrov, La Malfa, Torr, Bibi, "Language Model Tokenizers Introduce Unfairness Between Languages", NeurIPS 2023 — https://arxiv.org/abs/2305.15425 — verified (abstract); details UNVERIFIED
13. **[P1-13]** Hugging Face, "Tokenization algorithms" — https://huggingface.co/docs/transformers/tokenizer_summary — verified
14. **[P1-14]** Holtzman, Buys, Du, Forbes, Choi, "The Curious Case of Neural Text Degeneration", ICLR 2020 — https://arxiv.org/abs/1904.09751 — verified (abstract)
15. **[P1-15]** Anthropic, Token counting — https://platform.claude.com/docs/en/build-with-claude/token-counting — verified
16. **[P1-16]** `claude-api` skill (model table cached 2026-10-06) — local file (no URL) — read locally
17. **[P1-17]** Cohere, Tokenize reference and Models page — https://docs.cohere.com/reference/tokenize · https://docs.cohere.com/docs/models — verified
18. **[P1-18]** cohere-python 7.2.0, installed source (`cohere/client.py` L328–347; `manually_maintained/tokenizers.py` L19–40) — local file (no URL) — read locally
19. **[P1-19]** langchain-core `messages/ai.py` (master) — https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/messages/ai.py — verified
20. **[P1-20]** H. He / Thinking Machines Lab, "Defeating Nondeterminism in LLM Inference", 2025 — https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/ — verified by the foundation (src 21) and P1_FACTS S-web; not reopened
21. **[P1-21]** OpenAI Help, "What are tokens" — local file (no URL) — UNVERIFIED; not used
22. **[P1-22]** PyPI JSON for `openai-harmony`, `nbclient` — local file (no URL) — verified
23. **[P2-1]** Manning, Raghavan, Schütze, *Introduction to Information Retrieval* (CUP 2008), §1.1 "An example information retrieval problem" — https://nlp.stanford.edu/IR-book/html/htmledition/an-example-information-retrieval-problem-1.html — verified
24. **[P2-2]** IIR §1.2 "A first take at building an inverted index" — https://nlp.stanford.edu/IR-book/html/htmledition/a-first-take-at-building-an-inverted-index-1.html — verified
25. **[P2-3]** IIR §1.3 "Processing Boolean queries" — https://nlp.stanford.edu/IR-book/html/htmledition/processing-boolean-queries-1.html — verified
26. **[P2-4]** IIR §1.4 "The extended Boolean model versus ranked retrieval" — https://nlp.stanford.edu/IR-book/html/htmledition/the-extended-boolean-model-versus-ranked-retrieval-1.html — verified
27. **[P2-5]** IIR §8.1 "Information retrieval system evaluation" — https://nlp.stanford.edu/IR-book/html/htmledition/information-retrieval-system-evaluation-1.html — verified
28. **[P2-6]** IIR §8.3 "Evaluation of unranked retrieval sets" — https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-unranked-retrieval-sets-1.html — verified
29. **[P2-7]** IIR §8.4 "Evaluation of ranked retrieval results" — https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html — verified
30. **[P2-8]** IIR §8.5 "Assessing relevance" (pooling, kappa) — https://nlp.stanford.edu/IR-book/html/htmledition/assessing-relevance-1.html — verified
31. **[P2-9]** IIR §8.5.1 "Critiques and justifications of the concept of relevance" — https://nlp.stanford.edu/IR-book/html/htmledition/critiques-and-justifications-of-the-concept-of-relevance-1.html — verified
32. **[P2-10]** E. M. Voorhees, "The Philosophy of Information Retrieval Evaluation", CLEF 2001 workshop / Springer LNCS 2406 (2002) — https://www.nist.gov/publications/philosophy-information-retrieval-evaluation-0 — **abstract verified; full text UNVERIFIED** (both NIST PDFs and the ERCIM copy were font-encoded or image-only and could not be read). Cite only for "the Cranfield paradigm and its assumptions"
33. **[P2-11]** C. Buckley, E. M. Voorhees, "Retrieval Evaluation with Incomplete Information", SIGIR 2004 — https://www.nist.gov/node/761376 — abstract verified (ACM DL returned 403)
34. **[P2-12]** T. Saracevic, "Relevance: A review of the literature and a framework for thinking on the notion in information science. Part II: nature and manifestations of relevance", JASIST 58(13):1915–1933, 2007 — https://tefkos.rutgers-sci.domains/Saracevic%20relevance%20pt%20II%20JASIST%20%2707.pdf — full text verified (manifestations list, p.1929–1930 area)
35. **[P2-13]** N. Thakur, N. Reimers, A. Rücklé, A. Srivastava, I. Gurevych, "BEIR: A Heterogenous Benchmark for Zero-shot Evaluation of Information Retrieval Models", NeurIPS 2021 Datasets & Benchmarks —  (PDF text read) — https://arxiv.org/abs/2104.08663 — full text verified (§3.3 metric choice; §6 annotation bias, Table 4)
36. **[P2-14]** P. Thomas, S. Spielman, N. Craswell, B. Mitra, "Large language models can accurately predict searcher preferences", arXiv 2309.10621 (2023, rev. 2024) — https://arxiv.org/abs/2309.10621 — abstract verified
37. **[P2-15]** S. Upadhyay, R. Pradeep, N. Thakur, N. Craswell, J. Lin, "UMBRELA: UMbrela is the (Open-Source Reproduction of the) Bing RELevance Assessor", arXiv 2406.06519 (2024) — https://arxiv.org/abs/2406.06519 — abstract verified; no numbers on the abstract page
38. **[P2-16]** NIST TREC, qrels format page — https://trec.nist.gov/data/qrels_eng/ — verified
39. **[P2-17]** `usnistgov/trec_eval` README — https://github.com/usnistgov/trec_eval — verified (format names only; no column spec on the README)
40. **[P2-18]** G. Cabanac, G. Hubert, M. Boughanem, C. Chrisment, "Tie-breaking Bias: Effect of an Uncontrolled Parameter on Information Retrieval Evaluation", CLEF 2010, LNCS 6360 pp.112–123 — http://www.irit.fr/~Guillaume.Cabanac/tie-breaking-bias/ — project page verified; paper not opened
41. **[P2-19]** `ir-measures` documentation — https://ir-measur.es/en/latest/ — verified
42. **[P2-20]** `pytrec_eval` README — https://github.com/cvangysel/pytrec_eval — verified
43. **[P2-21]** PyPI JSON API for `ir-measures`, `ranx`, `pytrec-eval-terrier`, `ir-datasets`, `bm25s`, `pyserini`, `rank-bm25` — `>/json` — https://pypi.org/pypi/<name — verified 2026-10-17
44. **[P2-22]** LangChain `BaseRetriever` reference — https://reference.langchain.com/python/langchain-core/retrievers/BaseRetriever — verified (override `_get_relevant_documents`; scores are not covered there)
45. **[P4-1]** Reimers & Gurevych, *Sentence-BERT*, EMNLP 2019 — https://arxiv.org/abs/1908.10084 — verified (abstract)
46. **[P4-2]** Karpukhin et al., *Dense Passage Retrieval*, EMNLP 2020,  (PDF text searched for §3.1, §3.2, §5.2, App. B) — https://arxiv.org/abs/2004.04906 — verified
47. **[P4-3]** Muennighoff, Tazi, Magne, Reimers, *MTEB*, 2022/2023 — https://arxiv.org/abs/2210.07316 — verified (abstract); venue EACL 2023 **UNVERIFIED** (not on the page)
48. **[P4-4]** Enevoldsen, Chung, Kerboua et al., *MMTEB*, 2025 — https://arxiv.org/abs/2502.13595 — verified (abstract)
49. **[P4-5]** Kusupati et al., *Matryoshka Representation Learning*, 2022 — https://arxiv.org/abs/2205.13147 — verified (abstract)
50. **[P4-6]** Ethayarajh, *How Contextual are Contextualized Word Representations?*, EMNLP 2019 — https://arxiv.org/abs/1909.00512 — verified (abstract)
51. **[P4-7]** Cohere, Embed API v2 reference — https://docs.cohere.com/reference/embed — verified (first 100k chars)
52. **[P4-8]** Cohere, Models — https://docs.cohere.com/docs/models — verified
53. **[P4-9]** Cohere, Cohere's Embed models — https://docs.cohere.com/docs/cohere-embed — verified
54. **[P4-10]** Cohere, Embeddings guide — https://docs.cohere.com/docs/embeddings — verified
55. **[P4-11]** Cohere changelog, Embed Multimodal v4 — https://docs.cohere.com/v2/changelog/embed-multimodal-v4 — verified (no date on page)
56. **[P4-12]** Cohere pricing — https://cohere.com/pricing · https://www.getmaxim.ai/bifrost/model-library/compare/cohere/embed-v4.0.md — opened: **no Embed 4 price shown**. The $0.12 / 1M tokens figure comes only from third-party aggregators (e.g. https://www.getmaxim.ai/bifrost/model-library/compare/cohere/embed-v4.0.md, search snippet) → **UNVERIFIED**
57. **[P4-13]** sentence-transformers docs, Semantic search — https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html — verified
58. **[P4-14]** sentence-transformers docs, Pretrained models — https://sbert.net/docs/sentence_transformer/pretrained_models.html — verified
59. **[P4-15]** sentence-transformers 6.1.0 source (local `.venv`) — local file (no URL) — verified locally
60. **[P4-16]** `all-MiniLM-L6-v2` model card (local HF cache `1110a243…`; same text at ) — https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 — verified locally; URL not opened
61. **[P4-17]** langchain-community `vectorstores/faiss.py` (main) — https://raw.githubusercontent.com/langchain-ai/langchain-community/main/libs/community/langchain_community/vectorstores/faiss.py — verified
62. **[P4-18]** langchain-core `vectorstores/base.py` (master) — https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/vectorstores/base.py — verified
63. **[P4-19]** langchain-core `vectorstores/in_memory.py` (master) — https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/vectorstores/in_memory.py — verified
64. **[P4-20]** FAISS wiki, MetricType and distances — https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances — verified
65. **[P4-21]** Claim "all Cohere v3 models are normalised; dot, cosine, L2 give identical rankings" (Qdrant integration page  and a Korean write-up, seen only as search snippets) — https://qdrant.tech/documentation/embeddings/cohere/ — **UNVERIFIED** (secondary; not on Cohere's own pages)
66. **[P5-1]** Malkov & Yashunin, "Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs", arXiv 1603.09320 (v1 2016-03-30, v4 2018-08-14) — https://arxiv.org/abs/1603.09320 — verified (abstract). Journal (IEEE TPAMI) **UNVERIFIED**
67. **[P5-2]** Johnson, Douze & Jégou, "Billion-scale similarity search with GPUs", arXiv 1702.08734 (2017-02-28) — https://arxiv.org/abs/1702.08734 — verified (abstract). GPU-only results: not our setting
68. **[P5-3]** Douze et al., "The Faiss library", arXiv 2401.08281 (v1 2024-01-16, v4 2025-10-23) — https://arxiv.org/abs/2401.08281 — verified (abstract)
69. **[P5-4]** Faiss wiki, "Faiss indexes" — https://github.com/facebookresearch/faiss/wiki/Faiss-indexes — verified
70. **[P5-5]** Faiss wiki, "MetricType and distances" — https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances — verified
71. **[P5-6]** Faiss wiki, "Faster search" — https://github.com/facebookresearch/faiss/wiki/Faster-search — verified
72. **[P5-7]** Faiss source @ v1.15.1: `faiss/impl/HNSW.h`, `faiss/IndexHNSW.h` — https://raw.githubusercontent.com/facebookresearch/faiss/v1.15.1/faiss/impl/HNSW.h — verified (source lines)
73. **[P5-8]** hnswlib README, `ALGO_PARAMS.md`, LICENSE, `hnswlib/hnswalg.h` @ v0.8.0 — https://github.com/nmslib/hnswlib — verified
74. **[P5-9]** pgvector README — https://github.com/pgvector/pgvector — verified (production store docs)
75. **[P5-10]** Aumüller, Bernhardsson & Faithfull, "ANN-Benchmarks: A Benchmarking Tool for Approximate Nearest Neighbor Algorithms", arXiv 1807.05614 (2018; full version of a SISAP 2017 paper).  and — https://arxiv.org/abs/1807.05614 · https://ann-benchmarks.com/ — verified. Journal version (Information Systems 2020) **UNVERIFIED**
76. **[P5-11]** Aumüller & Ceccarello, "The Role of Local Intrinsic Dimensionality in Benchmarking Nearest Neighbor Search", arXiv 1907.07387 (SISAP 2019) — https://arxiv.org/abs/1907.07387 — verified (abstract)
77. **[P5-12]** PyPI JSON for `faiss-cpu`, `hnswlib`, `usearch`, `numkong`, `langchain-core`, `langchain-community`, `langsmith` (>/json), read 2026-10-17 — https://pypi.org/pypi/<name — verified
78. **[P5-13]** `faiss-wheels` README — https://github.com/faiss-wheels/faiss-wheels — verified. Faiss's own INSTALL.md (opened) still names conda as "the supported way" and does not mention pip
79. **[P5-14]** `langchain-core` 1.6.6 source (tag `langchain-core==1.6.6`): `vectorstores/in_memory.py`, `base.py`, `utils.py` — https://github.com/langchain-ai/langchain — verified (source read as text, not run)
80. **[P5-15]** `langchain_community` 0.4.1 `vectorstores/faiss.py`, in the learner's older venv (read as text) — local file (no URL) — verified (read, not run)
81. **[P6-1]** Manning, Raghavan, Schütze, *Introduction to IR*, §8.4 "Evaluation of ranked retrieval results" (CUP 2008) — https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html — verified
82. **[P6-2]** Same, §8.3 "Evaluation of unranked retrieval sets" — https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-unranked-retrieval-sets-1.html — verified
83. **[P6-3]** Järvelin & Kekäläinen, "Cumulated gain-based evaluation of IR techniques", ACM TOIS 20(4):422–446, 2002, doi 10.1145/582415.582418 (read from a mirror PDF) — https://www.fi.muni.cz/~xkohout7/Research/clanky_cizi/evaluation/p422-jarvelin.pdf — verified (pp. 424–432 read)
84. **[P6-4]** Burges et al., "Learning to Rank using Gradient Descent", ICML 2005, doi 10.1145/1102351.1102363 — https://khoury.northeastern.edu/home/vip/teach/IRcourse/6_ML/other_notes/rankNET.pdf — verified (eq. 16)
85. **[P6-5]** Voorhees & Tice, "The TREC-8 Question Answering Track", LREC 2000 — https://aclanthology.org/L00-1018.pdf — verified
86. **[P6-6]** Thakur et al., "BEIR: A Heterogenous Benchmark for Zero-shot Evaluation of IR Models", NeurIPS 2021 Datasets & Benchmarks, arXiv 2104.08663 — https://arxiv.org/abs/2104.08663 — verified (§3.3, §6 Table 4)
87. **[P6-7]** Smucker, Allan, Carterette, "A Comparison of Statistical Significance Tests for IR Evaluation", CIKM 2007 — https://ciir-publications.cs.umass.edu/getpdf.php?id=744 — verified (abstract)
88. **[P6-8]** trec_eval source, `m_ndcg_cut.c`, `form_res_rels.c`, `m_recip_rank.c` (usnistgov, main) — https://github.com/usnistgov/trec_eval — verified
89. **[P6-9]** ir-measures documentation, "Measures" — https://ir-measur.es/en/latest/measures.html — verified
90. **[P6-10]** ranx documentation, "Metrics" — https://amenra.github.io/ranx/metrics/ — verified
91. **[P6-11]** RAGAS docs, Context Precision and Context Recall (stable) — https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/ — verified
92. **[P6-12]** PyPI JSON API for `pytrec-eval-terrier`, `pytrec_eval`, `ir-measures`, `ranx`, `trectools`, `ragas` — https://pypi.org/pypi/<name — verified 2026-10-17
93. **[P7-1]** N. F. Liu, K. Lin, J. Hewitt, A. Paranjape, M. Bevilacqua, F. Petroni, P. Liang, "Lost in the Middle: How Language Models Use Long Contexts", TACL 12 (2024) 157–173 — https://arxiv.org/abs/2307.03172 · https://aclanthology.org/2024.tacl-1.9/ — **verified**: abstract, ACL Anthology record, and PDF text (§2.1–2.3, Table 1, §3, §4.2, §5, Appendix G Table 6)
94. **[P7-2]** C.-Y. Hsieh et al., "Found in the Middle: Calibrating Positional Attention Bias Improves Long Context Utilization", Findings of ACL 2024 — https://arxiv.org/abs/2406.16008 — verified (abstract only)
95. **[P7-3]** B. Veseli, J. Chibane, M. Toneva, A. Koller, "Positional Biases Shift as Inputs Approach Context Window Limits", COLM 2025 — https://arxiv.org/abs/2508.07479 — **verified**: abstract and PDF text (datasets, models, Fig. 5 discussion)
96. **[P7-4]** T. Gao, H. Yen, J. Yu, D. Chen, "Enabling Large Language Models to Generate Text with Citations" (ALCE), EMNLP 2023 — https://arxiv.org/abs/2305.14627 — **verified**: abstract, §1, §3.3 (citation recall/precision definitions)
97. **[P7-5]** E. Wallace, K. Xiao, R. Leike, L. Weng, J. Heidecke, A. Beutel, "The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions", 2024 — https://arxiv.org/abs/2404.13208 — **verified**: abstract, §1–§2
98. **[P7-6]** OpenAI, "gpt-oss-120b & gpt-oss-20b Model Card", Aug 2025 (CC BY 4.0) — https://arxiv.org/abs/2508.10925 — **verified**: §2.5.1 (Harmony, role order), §4.3 Tables 7–8, §4.5 Table 9. (openai.com page returned 403)
99. **[P7-7]** OpenAI, "OpenAI Harmony response format" (cookbook) — https://developers.openai.com/cookbook/articles/openai-harmony — verified
100. **[P7-8]** openai/harmony repository — https://github.com/openai/harmony — verified (partial: example system and developer messages)
101. **[P7-9]** Anthropic, Citations — https://platform.claude.com/docs/en/build-with-claude/citations — verified
102. **[P7-10]** Anthropic, Prompting best practices, 'Long context prompting'.  (the old `long-context-tips` URL redirects here) — https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices — verified
103. **[P7-11]** Groq, Structured outputs — https://console.groq.com/docs/structured-outputs — verified
104. **[P7-12]** Groq, model page `openai/gpt-oss-20b` — https://console.groq.com/docs/model/openai/gpt-oss-20b — verified
105. **[P7-13]** Groq, Reasoning — https://console.groq.com/docs/reasoning — verified
106. **[P7-14]** LangChain source, `langchain_classic/chains/combine_documents/base.py` (master, 2026-10-17) — https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/langchain/langchain_classic/chains/combine_documents/base.py — verified
107. **[P7-15]** `claude-api` skill (bundled; model table cached 2026-10-06): ids, prices, citations vs structured outputs — local file (no URL) — read locally
