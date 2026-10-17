<!-- kit:reading concept=P1 depth=short version=1 -->
# P1: LLM fundamentals for RAG: tokens, the call budget, temperature and cost

**What this is:** the short reading for P1. It follows one running example, the repo's climate PDF and the course's v0 prompt, from the cut into tokens, through one call's budget and the reasoning model's output cap, to sampling, price and run time.
**What this is not:** the full lesson with the lab ([concepts/P1_llm_fundamentals.md](../../concepts/P1_llm_fundamentals.md)), or how embeddings work (P4) and how to write the prompt (P7).

**The answer first.**
1. A model never reads characters. Its own tokenizer, fixed before training, cuts text into pieces from a learned vocabulary, and the model sees only their IDs.
2. So every limit and every bill is counted in that model's tokens. Characters per token depend on the text: about 5.6 on our climate PDF, about 4.6 on Python code, under 1.5 on a line of numbers.
3. One call's input (system rules, hidden template, chunks, question) plus its output (reasoning **and** answer) must fit the context window. The output cap must leave room for the reasoning, or the answer comes back empty.
4. The model picks each next token from softmax(scores / T). A low temperature makes the top token win more often, but no hosted API promises identical outputs, so the course replays recorded calls.
5. Cost per call = input tokens × input price + output tokens × output price, from a dated price sheet. On Groq, output (reasoning included) costs four times as much as input.

> **Read in the book:** Ch1 p.12–13/14, Ch2 p.9/11, Ch4 p.5/15, Ch22 p.8/19 and p.14–15/19. About 10 minutes. Read them after §6. The book never defines a token, a tokenizer or sampling temperature: every one of its 13 uses of "temperature" is about Earth's climate.

**Labels used below.** *Measured* numbers come from our scripts. *Toy* numbers are made up. *Formula* lines are arithmetic you can redo. *Dated* numbers are provider facts read on 2026-10-17 (Groq's model page and the LLMOps foundation §6.2); they change. Every measured number is in [P1_FACTS](../../sources/verification/P1/P1_FACTS.md) (S1–S11) or the [kit run](../../sources/verification/P1/out_p1_kit_measure.txt) (K1–K8). No API was called to write this file.

---

## 1. The tokenizer cuts; the model only sees IDs

**The setup.** One 67-character sentence, cut by three tokenizers: two from tiktoken (used by OpenAI-family models such as gpt-oss) and MiniLM's own.

**The result** (measured; `·` marks a leading space):

```
cl100k_base (BPE)   12 pieces   Anth|rop|ogenic|·emissions|·are|·accelerating|·deg|lac|iation|·in|·Greenland|.
o200k_base  (BPE)   13 pieces   Anth|rop|ogenic|·emissions|·are|·accelerating|·de|gl|aci|ation|·in|·Greenland|.
MiniLM WordPiece    16 IDs      [CLS] ant ##hr ##op ##ogenic emissions are accelerating de ##gl ##ac ##iation in greenland . [SEP]

vocabulary sizes:   cl100k 100,277   o200k_harmony (gpt-oss) 201,088   MiniLM 30,522
```

**What this means.** A **tokenizer** is a fixed program that ships with each model. It cuts text into pieces from a fixed list (the vocabulary) and replaces each piece by its number (the token ID). The model receives only these IDs. Inside the model, an **embedding table** looks up a vector for each ID; it never chooses where to cut. Common words stay whole. Rare words split. Each model has its own tokenizer, so the same sentence gives 12, 13 or 16.

**The tempting wrong idea (MC-001):** "the embeddings decide what a token is", or "a 1,000-character chunk is 1,000 tokens". The cut happens before any embedding exists, and a token is usually a word or a word part.

**For your project:** every budget is counted in the tokens of the model that enforces it. §4 turns this into a three-row rule.

## 2. Where the pieces come from (BPE)

**The setup.** Byte-pair encoding (BPE) learns its pieces from text. Start from single characters (bytes, in tiktoken). Count every pair of neighbouring pieces in the training text. Merge the most frequent pair into a new piece. Repeat until the vocabulary is full. We trained a tiny BPE (300 pieces) on the climate PDF and compared it with gpt-oss's real tokenizer.

**The result** (measured):

```
tiny BPE on the climate PDF: 230 merges; the first ones: i+n, a+n, e+s, a+t, o+n, e+n, an+d, e+r, i+on, in+g
word            tiny BPE (300 pieces)          o200k_harmony (after a space)
climate         climate             1          ·climate            1
greenhouse      gre|enh|ous|e       4          ·greenhouse         1
deglaciation    de|g|l|ac|i|ation   6          ·de|gl|aci|ation    4

case and space (cl100k):        'Greenland' 2    ' Greenland' 1    'GREENLAND' 2
o200k_harmony:                  'strawberry' 3 (st|raw|berry)      ' strawberry' 1
```

**What this means.** The pieces mirror the training text: what was frequent there becomes one piece, and what was rare stays split. The vocabulary is learned once, before the model is trained, and then frozen. In BPE the space belongs to the next piece, so a leading space or a capital letter changes the count. Because tiktoken's BPE starts from bytes, it can encode any text without an "unknown" token. But a script it rarely saw in training falls apart into short pieces, sometimes single bytes (§3). It also explains the famous "strawberry" puzzle: after a space, the model receives one ID for the whole word, not ten letters.

**For your project:** never guess token counts by looking at words. Count with the tokenizer.

## 3. Characters per token is measured, not 4

**The setup.** We cut the whole climate PDF (72,593 characters), all 91 windows of 1,000 characters (overlap 200), real repo code, numbers and one Hindi sentence.

**The result** (measured):

```
content                                tokenizer        chars per token     chars ÷ 4 says
whole climate PDF (72,593 chars)       cl100k           5.57 (13,026)       18,148  (+39%)
91 windows of 1,000 chars              cl100k           4.61–6.37, median 5.52  (157–217 tokens per full window)
repo helper_functions.py               o200k_harmony    4.61
numbers line (toy)                     cl100k           1.49                63% too few
Hindi sentence, 61 chars (161 bytes)   cl100k           0.98 (62 tokens)    75% too few
                                       o200k_harmony    3.39 (18 tokens)
digits (o200k_harmony):   1234567 → 123|456|7     1,234,567 → 1|,|234|,|567     2023-11-07 → 202|3|-|11|-|07
```

**What this means.** The ratio moves with the content. "Divide by 4" over-counts our English PDF by 39% and under-counts numbers and Hindi by far more. The habit comes from tiktoken's README, which gives about **4 bytes** per token on average. An English character is one byte, but a Devanagari character takes several: the 61-character Hindi sentence is 161 bytes. The tokenizer matters too: o200k's larger vocabulary holds more Hindi pieces, so the same sentence needs 18 tokens instead of 62. Across many languages, some need up to 15× more tokens for the same text (Petrov et al., NeurIPS 2023). More tokens mean a higher bill, less room in the window and a chunk that reaches the embedder's limit sooner.

**The tempting wrong idea:** "a token is about four characters". On a 1,000-character window, 1,000 / 5.52 ≈ 181 is closer to the 201 measured on window 0 than ÷ 4's 250.

**For your project:** estimate with your corpus's own ratio and call it an estimate. Count exactly near any limit (§13). For documents in another language, measure the ratio on real samples with both the embedder's and the generator's tokenizer, and check that the embedder supports that language at all; if it does not, no chunk size fixes it.

## 4. Count with the right tokenizer: two traps

**The setup.** The generator id in `.env` is `openai/gpt-oss-20b`. tiktoken offers `encoding_for_model(name)` to find the right encoding.

**The result** (measured, K2 and K3):

```
encoding_for_model('gpt-oss-20b')           → o200k_harmony
encoding_for_model('openai/gpt-oss-20b')    → KeyError (cannot map the name)
fix 1:  tiktoken.get_encoding('o200k_harmony')
fix 2:  tiktoken.encoding_for_model(model_id.split('/')[-1])

enc.encode('<|endoftext|>')                          → ValueError (disallowed special token)
enc.encode('<|endoftext|>', disallowed_special=())   → 7 ordinary tokens
o200k_harmony: 201,088 IDs, 1,091 of them special (chat markers such as <|start|>, <|message|>, <|end|>)
```

**What this means.**
- **Trap 1.** tiktoken maps model *names* by their prefix (`gpt-oss-`). Groq's provider prefix `openai/` breaks the lookup. Name the encoding directly.
- **Trap 2.** Special tokens are the chat format's control markers. By default `encode()` refuses text that contains their strings, so a counter crashes on any document that mentions one (a page about LLMs, say). `disallowed_special=()` counts them as ordinary text.

**The rule: which tokenizer counts what.**

| Question | Count with | Why |
|---|---|---|
| Will the embedder cut this chunk? | the **embedder's** tokenizer | it enforces its own cap (§5) |
| Does this prompt fit the window and the cap? | the **generator's** tokenizer, plus a margin for hidden tokens | the generator enforces them (§6) |
| What did the call cost? | the provider's **`usage`** | the bill includes tokens you never wrote |

**For your project:** the repo's `contextual_chunk_headers.ipynb` cell 11 counts with gpt-3.5-turbo's encoding (cl100k) for a gpt-4o-mini call (o200k). On our English PDF the two are close (13,026 against 12,840); on the Hindi sentence they are not (62 against 18).

## 5. Bridge: the embedder stops reading at 254 tokens

**The setup.** MiniLM embeds a 400-token passage, then only its first 254 tokens.

**The result** (measured):

```
max_seq_length 256, including [CLS] and [SEP]   →  254 text tokens
cos(400-token text, its first 254 tokens)          1.000000
cos(400-token text, same 254 + another tail)       1.000000
warnings or errors during encode()                 0
```

**What this means.** Everything after token 254 is dropped **silently**. The vector is identical whatever the tail says. Only the embedder's own WordPiece count tells you whether a chunk fits. Measure the truncation rate (the share of chunks over the limit), and check that retrieval still finds the evidence that sits late in long chunks (CE@k, P6).

**For your project:** the default embedder is Cohere `embed-v4.0`. Cohere's docs give a 128k-token context and a server-side `truncate` setting (default END, which cuts the end). Our O2 smoke test's model list reported 8,192 instead; which limit applies is UNVERIFIED. Same rule, different numbers: P4 teaches it.

## 6. One call's budget: input and output share the window

**The setup.** The v0 prompt: the system rules, four 1,000-character sources and one question, counted with `o200k_harmony`. The O2 smoke call shows what the provider adds.

**The result** (measured, plus one logged call):

```
system rules                       107
4 sources (4 × 1,000 chars)        842     ← 86% of the counted input
question (seed D-001)               20
counted input                      976
hidden chat template (estimate)    ~71     O2: billed 78 prompt tokens for a 7-token message
output cap (v0)                    512     reasoning + visible answer
whole call                       1,559  =  1.19% of the 131,072-token window
```

The rule: input + output ≤ window. For gpt-oss-20b on Groq the window is 131,072 and the output maximum 65,536 (dated).

**What this means.** The window holds everything in one call: system prompt, the hidden template, instructions, chunks, question and any conversation history (input), plus reasoning and answer (output). Part of the input is text you never wrote: gpt-oss uses the "harmony" chat format, which wraps each message in markers and adds a system header. That is the most likely source of the ~71 extra tokens; Groq's exact rendering is UNVERIFIED. So your own count is a **lower bound**.

**For your project:** v0 uses about 1% of the window. The window is not the constraint here; the output cap, the cost and the time are. Calibrate the overhead from recorded `usage`.

## 7. Reasoning spends the output cap

**The setup.** The O2 smoke test asked gpt-oss-20b for a three-word reply.

**The result** (logged call, session 2026-10-08 #2):

```
cap 12                               → visible answer ""  (empty)
cap 256, reasoning_effort="low"      → "smoke test ok": 23 completion tokens billed for a 4-token reply

where the response reports it:
usage.prompt_tokens                                 input, template included
usage.completion_tokens                             output: reasoning + answer
usage.completion_tokens_details.reasoning_tokens    the reasoning part
usage.prompt_tokens_details.cached_tokens           input served from Groq's cache (cheaper)
usage.total_tokens                                  prompt + completion
choices[0].finish_reason                            "stop" = finished normally; "length" = hit the cap
```

**What this means.**
- The output cap limits **output only**: reasoning plus answer, never the input. On Groq the parameter is `max_completion_tokens`; `max_tokens` is deprecated. The default, 1,024, may be too low for reasoning, Groq's own guide warns.
- **Reasoning tokens are output tokens.** They count against the cap, are billed at the output price and add latency.
- That `completion_tokens` already includes `reasoning_tokens` is an inference (total = prompt + completion; 23 billed against 4 visible). One recorded response settles it.
- `reasoning_effort` takes `low`, `medium` or `high`; anything else is rejected (HTTP 400). There is no "off". If you send nothing, the server uses **medium**.
- **Read `finish_reason` before the text.** The text alone cannot show that it was cut off. Which value Groq returns at the cap is UNVERIFIED (O2 did not log it), so accept only `stop`, treat anything else as not finished, and assert that the answer is non-empty. Other reasons exist across providers: a stop sequence you set, a tool call, a content filter or refusal. Never parse a capped answer as complete, never blindly retry a refusal, and treat an unknown value as an error, because providers add new ones.
- **Effort is a knob with a price.** Higher effort means more reasoning tokens, more cost and more delay; whether it buys better answers depends on the task and is not measured here. Choose it per task with a sweep on an eval set: quality next to reasoning tokens, p95 latency, cost and the empty-answer rate. The P1 LLMOps notebook plans such a cap × effort sweep.

**For your project:** v0 sends `max_completion_tokens=512` and `reasoning_effort="low"` explicitly, asserts a non-empty answer, and logs `finish_reason` and `reasoning_tokens` on every call. Chart two series: the length-stop rate and the reasoning share (reasoning ÷ completion tokens, p50 and p95). A large share is normal for a reasoning model; a rising one, or answers hitting the cap, is the signal. A check that the call "succeeded" is not a check of the answer.

## 8. Temperature reshapes the odds

**The setup.** At each step the model gives a score (logit) to every vocabulary entry. The sampler turns the scores into probabilities and draws one token:

```
p_i = exp(z_i / T) / Σ_j exp(z_j / T)          T = temperature
```

**The result** (toy logits [2.0, 1.5, 0.5, −1.0] for the next token of a verdict):

```
T       p(YES)   p(NO)   p(PARTIAL)   p(MAYBE)
0.25    0.879    0.119   0.002        0.000
0.5     0.704    0.259   0.035        0.002
1.0     0.532    0.323   0.119        0.026
2.0     0.404    0.315   0.191        0.090
→ 0     1        0       0            0          greedy: always the top token
```

**What this means.** Dividing by a small T stretches the gaps between scores, so the top token wins more often (the distribution sharpens). A large T shrinks the gaps and flattens it. Three limits:
- **T = 0 is a request, not a guarantee.** Groq turns 0 into 1e-8 and calls `seed` "best effort"; watch `system_fingerprint` for backend changes. On batched GPU servers, a request's result can change with the other requests in its batch (Thinking Machines Lab, 2025); that is not shown for Groq.
- **Repeatable is not correct.** A low temperature makes the choice stable, not right.
- **Some checks need T > 0.** The book's sampling-based consistency check regenerates the answer with different random seeds and flags sentences that disagree (Ch22 p.8/19).

**The honest limit:** gpt-oss's own README recommends temperature 1.0. The course pins 0 for repeatability; M4's flip-rate run will measure what that costs.

**For your project:** the only real guarantee is **replay**. Every call is cached, and a recorded response comes back byte-identical.

## 9. Each provider counts and samples its own way

**The setup.** The course uses Groq by default and Claude when credits exist (D-32). Cohere is the judge.

**The result** (dated):

| | Groq gpt-oss-20b | Claude (Haiku 5.5) | Cohere chat |
|---|---|---|---|
| Count tokens with | tiktoken `o200k_harmony`, by name | Claude's own tokenizer: `count_tokens` (free, rate-limited, an estimate, per model) | the model's own tokenizer (`tokenize`) |
| Temperature | 0–2, default 1; 0 becomes 1e-8 | not accepted: sending it gives HTTP 400 | default 0.3 |
| Reasoning knob | `reasoning_effort` low / medium / high (default medium) | `effort` (default medium); thinking on by default | — |
| Output cap and stop field | `max_completion_tokens`, `finish_reason` | `max_tokens`, `stop_reason` | — |

**What this means.** MC-001 extends to providers: each one counts its own tokens. An o200k count is only a proxy for Claude, and newer Claude tokenizers give about 30% more tokens for the same text than older ones (Anthropic's token-counting docs). Sampling parameters differ too: code written for Groq can fail on Claude.

**For your project:** a Claude arm counts with `count_tokens` (cached), never sends `temperature`, sends `effort` explicitly and sizes `max_tokens` for thinking plus answer. Changing the generator is a new experiment arm, never a silent swap: record a few calls and compare the estimated tokens with the billed `usage` first.

## 10. Price it: output costs four times input

**The setup.** Cost per call, with prices per 1M tokens:

```
cost = [(input − cached) × p_in + cached × p_cached + output × p_out] / 1,000,000
```

**The result** (dated prices; the arithmetic is K7):

```
per 1M tokens, read 2026-10-17     input    output   output ÷ input
Groq openai/gpt-oss-20b            $0.075   $0.30    4×        cached input $0.037
Claude Haiku 5.5                   $0.10    $0.50    5×

one v0 call on Groq, at the cap:   (976 × 0.075 + 512 × 0.30) / 10⁶ ≤ $0.000227
100 calls:                         ≤ $0.0227       output = 67.7% of it
100 calls on Haiku:                ≤ $0.0354       output = 72.4%   (976 is an o200k proxy for Claude's count)
```

**What this means.** The output is about half as many tokens as the input, but each output token costs four times as much, so output is about two thirds of the bill. Reasoning is billed as output. The figure is an upper bound on output (the full cap) but leaves out the ~71 hidden input tokens, so a pilot's `usage` replaces both.

The book counts cost in a coarser unit: the **number of LLM calls**. Simple RAG is cheap because it makes one LLM call per query and embedding is cheap (Ch1 p.13/14). Embedding is billed per token, once, at index time (Ch2 p.9/11). Track input and output tokens per query, and remember that a larger K raises cost and latency (Ch22 p.14–15/19). Later techniques add calls per chunk or per query, so their cost is calls × tokens per call.

**For your project:** record the price sheet's date with every estimate (`price_table_version`), and replace estimates with `usage` after a pilot.

## 11. Time it: limits are tokens per minute

**The setup.** Providers limit tokens per minute (TPM) and per day, not only requests. Take 100 v0 calls at 1,559 tokens each and a limit of 8,000 tokens per minute.

**The result** (formula, K7):

```
100 × 1,559 = 155,900 tokens
155,900 / 8,000 ≈ 19.5 minutes, at the very least
```

**What this means.** For a run like this, the rate limit decides the time; the money is trivial. Tokens ÷ TPM is a **floor**: retries and queueing only add to it. The 8,000-per-minute and 200,000-per-day figures for our Groq plan are UNVERIFIED; read your account's limits page.

**For your project:** check the planned tokens against the daily quota before a run, and expect a 100-question run to take tens of minutes, not seconds.

## 12. Decisions for your project

| Decision | Choice | Why |
|---|---|---|
| Tokenizer for chunk limits | the embedder's own (MiniLM WordPiece; Cohere's for `embed-v4.0`) | it enforces the cap (§5) |
| Tokenizer for prompt budgets | `tiktoken.get_encoding("o200k_harmony")`, plus a margin for the template | §4, §6 |
| Numbers for cost | estimates first, then `usage` from a pilot | hidden tokens (§6, §7) |
| Output cap and effort | `max_completion_tokens=512`, `reasoning_effort="low"`, both sent explicitly | §7 |
| Checks on every call | non-empty answer; `finish_reason` is `stop`; log reasoning tokens | §7 |
| Temperature | 0 on Groq, with caching; never sent to Claude | §8, §9 |

**Retrieve, or send the documents themselves?** The book calls simple RAG overkill when the documents fit inside the model's context window (Ch1 p.12/14). Weigh that with the budget rule of §6 and the price and time arithmetic of §10–§11; P7 returns to it.

## 13. When not to count exactly

Count roughly when the decision would not change with a 40% error: a first sizing of a corpus, say. Even then use the corpus's own ratio (5.5 here), not 4, and say it is an estimate.

Count exactly, with the right tokenizer, when:
- a chunk is near the embedder's limit;
- a prompt plus its output cap is near the window, or the cap is near what the reasoning needs;
- the text is code, numbers or a non-English language, where the ratio moves most;
- you report a cost or a budget to someone. Then the provider's `usage`, not your count, is the number to quote.

## Check yourself

→ [`study/questions/P1_questions.md`](../questions/P1_questions.md): 3 cold questions before reading, 15 after, 1 for a later review, and 2 interview questions. Answer the next day, closed book.
