# P1 gap audit: how the lesson's contents were chosen

**What this is:** the check run before writing the P1 lesson, so you can judge the method. Every idea the lesson needs had to be found and taught; none of it was optional.
**What this is not:** the lesson itself. That is [P1_llm_fundamentals.html](P1_llm_fundamentals.html) (open it from the study kit: P1 → step 1). The full research behind it is `study/research/phase_01_prerequisites.md`, "Concept P1".

## The method, in five steps

1. **Collect every idea the topic uses.** Sources: the book pages (Ch1 p.12–13/14, Ch2 p.9/11, Ch4 p.5/15, Ch9 p.9/14, Ch10 p.12/13, Ch12 p.6/14, Ch22 p.8/19 and p.14–15/19, App p.10/23), the old full lesson `concepts/P1_llm_fundamentals.md` and its lab, the 21 quiz questions with their key points and wrong answers, the repo cells in 02/04, and the provider docs (Groq, Claude, Cohere) read on 2026-10-17.
2. **For each idea, ask two questions.** Is it taught *before* it is used? Which concept owns it (P1, P4, P7, C2, C5, D2)? Your progress file says P1 is `exposed` (Parts A–F taught on 2026-10-08, lab and quiz not done) and P4, P7, C2, C5, D2 are `not_started`, so their ideas count as not yet learned.
3. **Classify each idea.**
   - **Core:** P1's own idea; taught in full.
   - **Bridge:** needed here, but owned elsewhere; taught briefly, in the place it is needed.
   - **Next topic:** only a link.
4. **Check the quiz.** Every key point of every question must be taught in the lesson, in **Short** mode too, because the quiz is the same for both depths.
5. **Check the facts.**
   - Every number is matched against the measured facts file (`sources/verification/P1/P1_FACTS.md`, S1–S11 and the new K1–K8).
   - Every book page was opened and checked.
   - No 15 or more consecutive words are copied from the book.

## What step 2 found: 17 gaps in the old P1 files

| # | Idea | Where P1 uses it | Before | Now in the lesson |
|---|---|---|---|---|
| 1 | **How BPE learns its pieces** (merge the most frequent pair, repeat) | "learned from text frequency" | asserted, never shown | step 2: a tiny BPE trained on the climate PDF, with its first 12 merges (Short) |
| 2 | **The tokenizer families** (byte-level BPE, WordPiece, Unigram, SentencePiece) | why MiniLM has `[UNK]` and tiktoken does not | WordPiece only | step 2, table (Full) |
| 3 | **Numbers and code cost more tokens** | the ratio table | toy lines only | step 3: real repo code (4.61) and digit groups (Short) |
| 4 | **Where "÷ 4" comes from** (4 *bytes*, not characters) | the ratio rule | missing | step 3, plus the Hindi bytes example (Short) |
| 5 | **The encoding-name trap** (`encoding_for_model("openai/gpt-oss-20b")` → `KeyError`) | every counter that uses the `.env` id | missing | step 4, trap 1 (Short) |
| 6 | **The special-token trap** (`<|endoftext|>` in a document → `ValueError`) | any counter on user documents | missing | step 4, trap 2 (Short) |
| 7 | **Which tokenizer counts which limit** | budgets, truncation, the bill | in Part K only | step 4, a 3-row table (Short) |
| 8 | **The default embedder is Cohere `embed-v4.0`** | truncation | MiniLM only | step 5, one sentence + link to P4 (bridge) |
| 9 | **The chat template adds hidden input tokens** (harmony format) | 78 billed vs 7 counted | "inference" only | step 6 (Short: the effect; Full: the mechanism, composition UNVERIFIED) |
| 10 | **The window and output limits of gpt-oss-20b** (131,072 / 65,536) | the budget | "look it up" | step 6, dated table (Short) |
| 11 | **`max_completion_tokens` replaces the deprecated `max_tokens`**; default 1,024 | every code sample, P1-A-04 | missing | step 7 and every code sample (Short) |
| 12 | **Where reasoning shows up in `usage`** (`completion_tokens_details.reasoning_tokens`) | the empty answer, the bill | no field named | step 7, annotated `usage` block (Short) |
| 13 | **`finish_reason`** (`stop` / `length`) and the empty-answer check | J1, the debugging item | named, values not taught | step 7, slider + the two asserts (Short) |
| 14 | **`reasoning_effort`** (low / medium / high; server default medium) | "use low" | reason missing | step 7 (Short) |
| 15 | **Claude: no temperature, `effort` instead, its own tokenizer, `count_tokens`** (D-32) | not in P1 | missing | step 9, provider table (Short) |
| 16 | **Output costs 4× input; reasoning bills as output; dated prices** | cost | placeholder prices only | step 10, cost bars on the dated sheet (Short); calculator (Full) |
| 17 | **Rate limits in tokens per minute → run time** | not in P1 | missing | step 11 (Short) |

Also new, in Full only: top_p (Holtzman et al. 2020) and top_k (AIQ 02 Q12, MIT), the missing logprobs and `n` = 1 on Groq, and the honest-limit box on T = 0 versus gpt-oss's own recommendation of T = 1.0 (external review §3a row 3, never applied before).

Ideas that were already taught well stayed, rewritten for clarity: the tokenizer cuts and the embedder only looks up IDs (MC-001), the measured characters-per-token table, the leading-space and case effects, MiniLM's silent truncation at 254 text tokens, the v0 prompt budget (976 tokens), softmax(z/T) with the toy logits, and "temperature 0 is not a guarantee".

## What step 4 found: the quiz against the lesson

QUIZ_TABLE

## Left to other concepts on purpose (link only)

- **How embeddings are compared, and Cohere's input limits in detail:** P4 and C3.
- **Position effects in long prompts (lost in the middle), and whether to retrieve when everything fits:** P7 and X3.
- **Latency words (time to first token, p50/p95) and caching prices:** D2.
- **How often generated answers flip between runs:** M4.

P1 only needs to know these exist and why.

## Errors found in the old files (recorded, not edited)

- `concepts/P1_llm_fundamentals.md` uses `max_tokens` throughout (B.2, D.5, J1, K, P1-A-04); Groq deprecated it for `max_completion_tokens`.
- Its D.5 says `o200k_harmony` is "the encoding tiktoken maps to gpt-oss-20b": true for the bare name only; the `.env` id raises `KeyError`.
- Its "Still UNVERIFIED" list still says the window, output cap and prices of gpt-oss-20b are unknown; they are documented (read 2026-10-17).
- Its D.6 says a top-k description is unsourced; AIQ 02 Q12 (MIT) describes it.
- The 02 P1 card's outcome "why judges use temperature 0" is incomplete: current Claude models reject temperature.

These are in the research file's error table (E1–E12) for a later correction pass.
