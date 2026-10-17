# Token budget check

**What this is:** local token counts for your documents, chunks and prompts, turned into a window check, a cost estimate and a minimum run time.
**What this is not:** a bill. Your own counts miss the provider's template tokens (a lower bound on input), and the output side is the cap (an upper bound). Replace estimates with recorded `usage`.

**Recommendation: size chunks in tokens, not characters** (section 9). Checklist: C1 ✓ C2 ✗ C3 ✓ C4 ✓ C5 ✓ C6 ✓ C7 ? C8 ? C9 ? C10 ✓ C11 ✓ C12 ✓.

Settings: generator `groq:openai/gpt-oss-20b` (tokenizer `o200k_harmony`) · 1000-character chunks, overlap 200 · k 4 · `max_completion_tokens` 512 · effort low · temperature 0 · overhead 71 tokens per call (inferred from one logged call, P1 B.3) · embedder minilm · 100 planned calls · 8,000 TPM, 200,000 tokens/day · tiktoken 0.14.0, tokenizers 0.23.2, pymupdf 1.26.7.
Documents: `Understanding_Climate_Change.pdf` as `climate` (33 page(s), 72,593 characters).

## 1 Corpus ratios per tokenizer

Whole corpus: 72,593 characters, 72,595 UTF-8 bytes. Tokenizer: by name: gpt-oss-20b -> o200k_harmony.
Naive call on the id as written (lesson trap K2): `encoding_for_model('openai/gpt-oss-20b') -> KeyError: Could not automatically map openai/gpt-oss-20b to a tokeniser.`

| Tokenizer | Role | Tokens | Chars/token | Bytes/token | Chars ÷ 4 | ÷ 4 error |
|---|---|---|---|---|---|---|
| `o200k_harmony` | generator | 12,840 | 5.65 | 5.65 | 18,148 | +41% |
| `o200k_base` | comparison | 12,840 | 5.65 | 5.65 | 18,148 | +41% |
| `cl100k_base` | comparison | 13,026 | 5.57 | 5.57 | 18,148 | +39% |
| `MiniLM WordPiece` | embedder | 11,694 | 6.21 | 6.21 | 18,148 | +55% |

÷ 4 error = (chars ÷ 4 − tokens) ÷ tokens: positive means ÷ 4 over-counts. WordPiece counts exclude [CLS]/[SEP].

## 2 Content mix

| Content | Share | Chars/token (generator) | Why it matters |
|---|---|---|---|
| Digits | 0.1% of characters (63 number runs) | 1.39 | numbers are cut into short groups |
| Code-like lines | 0 of 1,097 lines (0.0%) | - | code has fewer characters per token than prose |
| Non-Latin letters | 0 of 60,609 letters (0.0%) | - | other scripts can cost several times more tokens |

Special-token strings: none found (checked `<|…|>` against `o200k_harmony` and [CLS]/[SEP]/[PAD]/[MASK]/[UNK]).

## 3 Chunks: tokens per chunk and embedder truncation

91 chunks (1000 chars, overlap 200).

| Per chunk | Min | Median | p95 | Max |
|---|---|---|---|---|
| Characters | 593 | 1,000 | 1,000 | 1,000 |
| `o200k_harmony` tokens | 109 | 177 | 198.5 | 218 |
| MiniLM WordPiece text tokens | 102 | 160 | 184 | 198 |
| Chars/token (generator) | 4.59 | 5.62 | 6.12 | 6.49 |

MiniLM (`sentence-transformers/all-MiniLM-L6-v2`, cache snapshot `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`) reads 256 IDs including [CLS] and [SEP], so 254 text tokens. Chunks over the limit: **0 of 91 (0.0%)**. The cut is silent: no error, no warning (P1_FACTS S6).

## 4 Prompt budget per question and window fit

Prompt = the 06 §3.3 v0 template: system rules (107 tokens) + `Sources:` with 4 numbered chunks + the question. *Sample* = the first k chunks (climate#0, climate#1, climate#2, climate#3; as P1_FACTS S9, not a retrieval result). *Upper* = the k chunks with the most tokens (climate#2, climate#4, climate#9, climate#8), the worst case.

| Question | Question tokens | Sources (sample) | Input counted (sample) | Input (upper) | + overhead + cap (upper) | % of window | One call | 100 calls | 100 calls ≥ min |
|---|---|---|---|---|---|---|---|---|---|
| D-001 | 20 | 842 | 976 | 995 | 1,578 | 1.20% | ≤ $0.000227 | ≤ $0.0227 | 19.5 |
| D-002 | 9 | 842 | 965 | 984 | 1,567 | 1.20% | ≤ $0.000226 | ≤ $0.0226 | 19.4 |
| D-003 | 27 | 842 | 983 | 1,002 | 1,585 | 1.21% | ≤ $0.000227 | ≤ $0.0227 | 19.6 |
| D-004 | 12 | 842 | 968 | 987 | 1,570 | 1.20% | ≤ $0.000226 | ≤ $0.0226 | 19.4 |
| D-005 | 15 | 842 | 971 | 990 | 1,573 | 1.20% | ≤ $0.000226 | ≤ $0.0226 | 19.4 |
| D-006 | 13 | 842 | 969 | 988 | 1,571 | 1.20% | ≤ $0.000226 | ≤ $0.0226 | 19.4 |
| D-007 | 24 | 842 | 980 | 999 | 1,582 | 1.21% | ≤ $0.000227 | ≤ $0.0227 | 19.5 |
| D-008 | 7 | 842 | 963 | 982 | 1,565 | 1.19% | ≤ $0.000226 | ≤ $0.0226 | 19.3 |
| D-009 | 9 | 842 | 965 | 984 | 1,567 | 1.20% | ≤ $0.000226 | ≤ $0.0226 | 19.4 |
| D-010 | 11 | 842 | 967 | 986 | 1,569 | 1.20% | ≤ $0.000226 | ≤ $0.0226 | 19.4 |

Window: 131,072 tokens; max output 65,536 (price sheet). Cost columns: counted sample input + the 512 cap, generator prices; minutes: (sample input + 71 + 512) × 100 ÷ 8,000 TPM.

## 5 Output cap and reasoning

`max_completion_tokens` 512 (Groq's default is 1,024; `max_tokens` is deprecated). The cap holds reasoning tokens **and** the visible answer: if reasoning uses it up, the answer is empty and the call stops at the cap (`finish_reason` `length`). Effort: low.

No recorded usage: run with `--traces results.jsonl` (your logged responses). A pilot (`--pilot 5`) needs the shared LLMOps cache package (study/llmops/), which is not built yet; nothing was called.

## 6 Cost

Price sheet `price_table_version` 2026-10-17 (USD per 1M tokens; LLMOPS_FOUNDATION §6.2; Groq model page openai/gpt-oss-20b [P1-1]; claude-api skill table [P1-16]). Output is billed at the cap (512 tokens), so every figure is an upper bound on output. *Sample*: mean counted input over your questions (970.7 tokens). *Upper*: the longest prompt (1,002 tokens). *+ overhead*: upper + 71 template tokens.

| Model | In / out per 1M | Out ÷ in | One call, D-001 (976 in) | Output share | 100 calls, D-001 | 100 calls (sample mean) | 100 calls (upper) | 100 calls (+ overhead) |
|---|---|---|---|---|---|---|---|---|
| `groq:openai/gpt-oss-20b` (generator) | $0.075 / $0.30 | 4.0× | ≤ $0.000227 | 67.7% | ≤ $0.0227 | ≤ $0.0226 | ≤ $0.0229 | ≤ $0.0234 |
| `anthropic:claude-haiku-5-5` *o200k proxy count* | $0.10 / $0.50 | 5.0× | ≤ $0.000354 | 72.4% | ≤ $0.0354 | ≤ $0.0353 | ≤ $0.0356 | ≤ $0.0363 |

Claude rows reuse the generator-side counts (an o200k proxy); Claude's own count comes from `count_tokens`.

Cached input is $0.037 per 1M on this sheet; this estimate assumes no cache hits.

## 7 Run time

Minimum time = tokens ÷ tokens per minute. Per call: input + 71 overhead + 512 cap.

| Plan | Tokens per call | Tokens per run | Minutes at TPM | Share of the daily quota |
|---|---|---|---|---|
| 100 calls, sample prompts | 1,554 | 155,370 | ≥ 19.4 | 78% |
| 100 calls, upper | 1,585 | 158,500 | ≥ 19.8 | 79% |

Rate limits for this model on the sheet: 8,000 TPM, 200,000 tokens/day (plan row UNVERIFIED, foundation §2.5).

## 8 Checklist

✓ = no problem found · ✗ = a problem found on your data · ? = check by hand (the evidence and *how to check* help).

| # | Check | Verdict | Evidence | How to check |
|---|---|---|---|---|
| C1 | The generator's tokenizer was resolved by encoding name (no provider-prefix KeyError) | ✓ | by name: gpt-oss-20b -> o200k_harmony. The naive call on the id as written in .env: encoding_for_model('openai/gpt-oss-20b') -> KeyError: Could not automatically map openai/gpt-oss-20b to a tokeniser.. | Resolve the encoding by name (tiktoken.get_encoding('o200k_harmony') for gpt-oss), or strip the provider prefix before encoding_for_model; for Claude, count with client.messages.count_tokens. |
| C2 | Measured chars/token for your corpus vs ÷4; flag an error above 20% | ✗ | o200k_harmony: 72,593 chars / 12,840 tokens = 5.65 chars/token; ÷4 gives 18,148, an error of +41% (over-count). Per chunk: 4.59 to 6.49 chars/token (median 5.62). | Count a sample of your own text with the generator's tokenizer; use the measured ratio, never 4. |
| C3 | Costly content share: digits, code, non-Latin script | ✓ | Digits 0.1% of characters (1.39 chars/token in number runs); code-like lines 0 of 1097 (0.0%, - chars/token); non-Latin letters 0.0% (- chars/token). | Look at section 2; for a mixed corpus measure chars/token per content type, not one average. |
| C4 | Special-token strings present in your documents (would crash a default counter) | ✓ | none of o200k_harmony's 1091 special-token strings and no [CLS]/[SEP]-style text found. | Search your text for '<\|' ... '\|>' and [CLS]/[SEP]; count with encode(text, disallowed_special=()). |
| C5 | Embedder truncation rate (MiniLM: chunks over 254 text tokens; Cohere: check the `truncate` setting) | ✓ | 0 of 91 chunks (0.0%) exceed 254 WordPiece text tokens (256 incl. [CLS]/[SEP]); longest chunk 198 tokens. | MiniLM: count each chunk with its own WordPiece tokenizer; over 254 text tokens is cut silently. Cohere embed-v4.0: 128k context, `truncate` default END; check the setting your code sends. |
| C6 | Input + output cap fits the window with a margin | ✓ | Worst case (D-003, the 4 longest chunks): 1,002 counted + 71 overhead + 512 cap = 1,585 tokens = 1.21% of 131,072; cap 512 ≤ max output 65,536. | input + template overhead + max_completion_tokens ≤ the model's window (keep a 10% margin); cap ≤ max output. |
| C7 | Output cap leaves room for reasoning (p95 reasoning share from traces or the pilot) | ? | no recorded usage. Your cap is 512 at effort low; Groq's default cap is 1,024 and the logged O2 call returned an empty answer at a cap of 12. | Read usage.completion_tokens_details.reasoning_tokens from recorded calls (--traces results.jsonl), or run --pilot 5 once study/llmops/ exists; the cap must hold reasoning + the visible answer. |
| C8 | `finish_reason = length` and empty-answer rates in recorded traces are 0 | ? | no traces given (--traces results.jsonl). | Count finish_reason == 'length' (Claude: stop_reason 'max_tokens') and empty answers in your logged traces. |
| C9 | Billed vs counted overhead calibrated from recorded `usage` | ? | not calibrated: this report assumes 71 tokens per call, inferred from one logged call (P1 B.3: 78 billed vs 7 counted, a call with no system prompt). | Compare usage.prompt_tokens with your own count of the same messages; the difference is the template overhead. Record 'messages' or 'counted_prompt_tokens' with each trace. |
| C10 | Price sheet dated within 30 days | ✓ | price_table_version 2026-10-17, 1 day(s) before 2026-10-18. | Re-read the provider's price page and update price_table_version in your price sheet. |
| C11 | Planned run fits the daily token quota and its minimum time is acceptable | ✓ | 100 calls × up to 1,585 tokens = 158,500 tokens (79% of 200,000 per day); at 8,000 TPM ≥ 19.8 min (rate limits: plan row UNVERIFIED, foundation §2.5). | Tokens per run = calls × (input + overhead + cap); minutes ≥ tokens ÷ TPM; compare with your plan's daily quota. |
| C12 | Sampling parameters are accepted by the provider (no `temperature` sent to current Claude models; effort sent explicitly) | ✓ | Flags: temperature 0 (Groq sends 0 as 1e-8), effort low. | Groq gpt-oss: temperature 0–2 (0 is sent as 1e-8), reasoning_effort low/medium/high, default medium. Claude: send no temperature (non-default sampling values return 400); set effort explicitly. |

## 9 Recommendation

**size chunks in tokens, not characters** (rule: C2 failed; first match wins)

- C2: o200k_harmony: 72,593 chars / 12,840 tokens = 5.65 chars/token; ÷4 gives 18,148, an error of +41% (over-count). Per chunk: 4.59 to 6.49 chars/token (median 5.62).
- next: set chunk sizes in tokens (--unit tokens, a token splitter) or budget with the measured chars/token, never ÷ 4. Over-counting wastes budget; under-counting overflows it.

Order of the rules: C4/C1 counter → C6 window → C7/C8 output cap → C5 truncation > 5% → C2 ÷4 error > 20% → C11 quota/time → budget OK.
