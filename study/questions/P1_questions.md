<!-- kit:questions concept=P1 version=1 -->
# P1 questions: tokens, the call budget, temperature and cost

**How to use:** write your answer and a confidence (1–3) first. Then open the answer and tick the key points you really wrote.

**Where the numbers come from:** `sources/verification/P1/p1_measure.py`, `p1_strawberry.py` and `p1_kit_measure.py` ([P1_FACTS](../../sources/verification/P1/P1_FACTS.md) S1–S11; [kit run K1–K8](../../sources/verification/P1/out_p1_kit_measure.txt)), plus the logged O2 smoke call ([O2 report](../../progress/O2_smoke_test_2026-10-08.json)). Prices, the window and the output cap are **dated** provider facts (Groq model page and LLMOps foundation §6.2, read 2026-10-17); they change, so re-check before a paid run. "Toy" numbers are made up. No API was called to write this file.

<!-- q id=P1-PRE-01 type=R set=pre -->
### P1-PRE-01 · Recall (before reading)
**Question:** Before a model reads your text, who decides where it is cut into tokens?

**Reply template:** `The ____ decides. It was fixed ____. The model then receives ____.`

<details><summary>Hint 1</summary>

The model itself never sees letters. Something turns the text into numbers first.

</details>

<details><summary>Hint 2</summary>

Each model ships with a fixed list of pieces (its vocabulary). Which program cuts your text into pieces from that list, and when was the list made?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The model's own **tokenizer**. It was learned from text statistics before the model was trained, and then frozen. It cuts the text into pieces from a fixed vocabulary and replaces each piece with its ID. The model receives only the IDs. Different models cut the same text differently:

```
"Anthropogenic emissions are accelerating deglaciation in Greenland."  (67 characters)
cl100k_base 12 pieces · o200k_base 13 pieces · MiniLM WordPiece 16 IDs (incl. [CLS], [SEP])
```

**Key points** (a 3 needs every point):
- [ ] The tokenizer decides, not the model and not you.
- [ ] The model receives token IDs (numbers), never letters.

**For a 4, also:**
- [ ] Says the tokenizer is fixed per model before training, so two models cut the same sentence differently (12 / 13 / 16 pieces).

**Common wrong answers:**
- [ ] "The embedding model decides the tokens": the embedding table only looks up a vector for each ID it is given (MC-001).
- [ ] "Each character is a token": the 67-character sentence is 12 cl100k tokens (MC-001).

**If you missed it, reread:** [short §1](../reading/P1_llm_fundamentals.md#1-the-tokenizer-cuts-the-model-only-sees-ids) · [full D.1](../../concepts/P1_llm_fundamentals.md#d1-the-objects-involved) · book Ch12 p.6/14 (the book's only "tokenize" is BM25's word split; it never defines a model token)

</details>
<!-- /q -->

<!-- q id=P1-PRE-02 type=R set=pre -->
### P1-PRE-02 · Recall (before reading)
**Question:** About how many tokens is 1,000 characters of English prose?

**Reply template:** `About ____ tokens, because ____.`

<details><summary>Hint 1</summary>

The common rule of thumb divides by 4. Is that measured, or assumed?

</details>

<details><summary>Hint 2</summary>

On the course's climate PDF, a cl100k token holds about 5.5 characters. What does that give for 1,000 characters, and does it depend on the tokenizer?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** It depends on the text and the tokenizer, so measure it. On the climate PDF, a full 1,000-character window is **157 to 217** cl100k tokens (median 180.5). The rule "characters ÷ 4" says 250, which is too many for this English PDF.

```
91 windows of 1,000 characters (climate PDF, cl100k):   157–217 tokens (median 180.5)
window 0:   201 tokens            chars ÷ 4:   250 tokens (+24%)
```

**Key points** (a 3 needs every point):
- [ ] Roughly 150–220 tokens on our English PDF, not exactly 250.
- [ ] The number depends on the text and on the tokenizer, so it is measured, not assumed.

**For a 4, also:**
- [ ] Names the boundary: numbers, code and non-English text break the ratio (a numbers line is 1.49 characters per token, a Hindi sentence 0.98 under cl100k).

**Common wrong answers:**
- [ ] "1,000 tokens, one per character": tokens are pieces, mostly whole words or word parts (MC-001).
- [ ] "Exactly 250": that is the ÷ 4 habit; it over-counts this PDF.

**If you missed it, reread:** [short §3](../reading/P1_llm_fundamentals.md#3-characters-per-token-is-measured-not-4) · [full D.3](../../concepts/P1_llm_fundamentals.md#d3-characters-per-token-measured-not-assumed) · book Ch2 p.9/11 (embedding is billed per token; the book never says how long a token is)

</details>
<!-- /q -->

<!-- q id=P1-PRE-03 type=R set=pre -->
### P1-PRE-03 · Recall (before reading)
**Question:** What does the output cap on an LLM call limit?

**Reply template:** `It limits ____. It does not limit ____. If it is too small, ____.`

<details><summary>Hint 1</summary>

The cap is a parameter of one call. Does it cover what you send, what comes back, or both?

</details>

<details><summary>Hint 2</summary>

The course's generator is a reasoning model: it writes hidden reasoning before the answer. Where do those tokens go?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** It limits the **output** tokens of one call: the reasoning **and** the visible answer together. It does not limit the input or set the context window. On Groq the parameter is `max_completion_tokens` (default 1,024). If the cap is too small, the reasoning can use all of it and the answer comes back empty, as in our O2 smoke call:

```
cap 12:    visible answer ""  (empty)
cap 256, reasoning_effort="low":   "smoke test ok"   (23 completion tokens billed for a 4-token reply)
```

**Key points** (a 3 needs every point):
- [ ] It caps output only, not the input or the window.
- [ ] On a reasoning model the output includes the reasoning, so a small cap can leave an empty answer.

**For a 4, also:**
- [ ] Names the parameter (`max_completion_tokens` on Groq; `max_tokens` is deprecated there) and says to read `finish_reason` before trusting the text.

**Common wrong answers:**
- [ ] "It is the size of the context window": the window holds input plus output; the cap is one part of it.
- [ ] "It only limits the visible answer": reasoning tokens count against it too.

**If you missed it, reread:** [short §7](../reading/P1_llm_fundamentals.md#7-reasoning-spends-the-output-cap) · [full B.2](../../concepts/P1_llm_fundamentals.md#b2-the-empty-answer-our-own-o2-run) · book Ch4 p.5/15 (chunks sized to fit one call's window; the book never mentions an output cap)

</details>
<!-- /q -->

<!-- q id=P1-R-01 type=R set=main -->
### P1-R-01 · Recall (MC-001 check item)
**Question:** Which part of the system decides where text is cut into tokens?

**Reply template:** `The ____ decides. The embedding model only ____.`

<details><summary>Hint 1</summary>

Follow one sentence from text to vector: which step happens first?

</details>

<details><summary>Hint 2</summary>

Text → (something) → token IDs → (something) → vectors. Name the two somethings, and say which one chooses the cut.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The **tokenizer** decides. It is fixed per model (BPE in tiktoken, WordPiece in MiniLM) and was learned from text frequency before the model was trained. The embedding model only receives the IDs and looks up a vector for each one; it never chooses the cut.

```
same 67-character sentence:   cl100k 12 pieces · o200k 13 · MiniLM WordPiece 16 (incl. [CLS], [SEP])
```

**Key points** (a 3 needs every point):
- [ ] The tokenizer decides where the text is cut.
- [ ] The embedding model only maps the IDs it receives to vectors.

**For a 4, also:**
- [ ] Gives a boundary with evidence: each model has its own tokenizer, so the same text gives different counts (12 / 13 / 16), and each limit must be counted with the tokenizer of the model that enforces it.

**Common wrong answers:**
- [ ] "The embeddings decide what a token is": this is MC-001. The cut is made before any embedding exists.
- [ ] "A token is a character, so a 1,000-character chunk is 1,000 tokens": MC-001 again; on our PDF it is about 157–217 tokens.

**If you missed it, reread:** [short §1](../reading/P1_llm_fundamentals.md#1-the-tokenizer-cuts-the-model-only-sees-ids) · [short §2](../reading/P1_llm_fundamentals.md#2-where-the-pieces-come-from-bpe) · [full D.1](../../concepts/P1_llm_fundamentals.md#d1-the-objects-involved) · [full D.2](../../concepts/P1_llm_fundamentals.md#d2-how-the-two-tokenizer-families-cut) · book Ch12 p.6/14 (word tokens for BM25 only)

</details>
<!-- /q -->

<!-- q id=P1-R-02 type=R set=main -->
### P1-R-02 · Recall
**Question:** Name everything that uses up a reasoning model's context window in one call.

**Reply template:** `Input: ____. Output: ____.`

<details><summary>Hint 1</summary>

Split the call into what goes in and what comes out.

</details>

<details><summary>Hint 2</summary>

The input holds more than the text you wrote. The output holds more than the answer you read.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** **Input:** system rules, the hidden chat template, instructions, the k chunks, the question, and any conversation history. **Output:** the reasoning plus the visible answer, together capped by `max_completion_tokens`. All of it must fit the window.

```
v0 call (o200k_harmony):   system 107 + sources 842 + question 20 = 976 counted input
                           + template ~71 (O2: 78 billed for a 7-token message) + output cap 512
                           = 1,559 tokens = 1.19% of the 131,072-token window (Groq, read 2026-10-17)
```

**Key points** (a 3 needs every point):
- [ ] Input: system prompt, hidden template, chunks, question (and history).
- [ ] Output: reasoning plus visible answer.
- [ ] Input and output share the one window.

**For a 4, also:**
- [ ] Gives the evidence: the O2 call billed 78 prompt tokens for a 7-token message, and at a 12-token cap the reasoning left an empty answer.

**Common wrong answers:**
- [ ] "Only the prompt uses the window": the output, reasoning included, shares it.
- [ ] "Only the text I wrote counts": the chat template adds hidden input tokens (about 71 in O2).

**If you missed it, reread:** [short §6](../reading/P1_llm_fundamentals.md#6-one-calls-budget-input-and-output-share-the-window) · [short §7](../reading/P1_llm_fundamentals.md#7-reasoning-spends-the-output-cap) · [full D.5](../../concepts/P1_llm_fundamentals.md#d5-the-context-window-and-its-budget) · [full B.3](../../concepts/P1_llm_fundamentals.md#b3-the-bill-does-not-match-your-count) · book Ch4 p.5/15 and Ch22 p.14/19

</details>
<!-- /q -->

<!-- q id=P1-R-03 type=R set=main -->
### P1-R-03 · Recall
**Question:** What does a low temperature do to the next-token probabilities?

**Reply template:** `It ____ the distribution, because the scores are ____ by T.`

<details><summary>Hint 1</summary>

The sampler turns the model's scores (logits) into probabilities with softmax. Where does T enter?

</details>

<details><summary>Hint 2</summary>

p_i = exp(z_i / T) / Σ exp(z_j / T). Dividing by a small number makes the gaps between scores larger or smaller?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** It **sharpens** the distribution toward the top token. The scores are divided by T before softmax, so a small T stretches the gaps between them. As T → 0, the top token always wins (greedy).

```
toy logits [2.0, 1.5, 0.5, −1.0] for YES / NO / PARTIAL / MAYBE:
T = 0.25   p(YES) 0.879        T = 1.0   p(YES) 0.532        T = 2.0   p(YES) 0.404
```

**Key points** (a 3 needs every point):
- [ ] It sharpens the distribution toward the most likely token.
- [ ] The logits are divided by T before softmax.
- [ ] T → 0 is greedy: always the top token.

**For a 4, also:**
- [ ] Gives the limit: T = 0 is a request, not a guarantee. Groq turns 0 into 1e-8 and calls `seed` best effort, so identical outputs are not promised, and a repeatable answer is not a correct one.

**Common wrong answers:**
- [ ] "Low temperature makes the model more accurate": it makes the choice more repeatable, not more correct.
- [ ] "Temperature 0 gives the same answer every time": not promised on a hosted API; only replaying a recorded response does.

**If you missed it, reread:** [short §8](../reading/P1_llm_fundamentals.md#8-temperature-reshapes-the-odds) · [full D.6](../../concepts/P1_llm_fundamentals.md#d6-temperature-and-sampling) · book Ch22 p.8/19 (a check that needs different random seeds)

</details>
<!-- /q -->

<!-- q id=P1-R-04 type=R set=main -->
### P1-R-04 · Recall (P4 bridge)
**Question:** A 300-token chunk goes into MiniLM: how many of its text tokens shape the vector?

**Reply template:** `____ tokens, because ____. The rest ____.`

<details><summary>Hint 1</summary>

MiniLM's `max_seq_length` is 256. Is that all text?

</details>

<details><summary>Hint 2</summary>

WordPiece adds two marker tokens to every input. Subtract them.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** **254.** The cap is 256 IDs, and `[CLS]` and `[SEP]` take two of them. The rest is dropped **silently**: no error, no warning.

```
max_seq_length 256 (incl. [CLS], [SEP])  →  254 text tokens
cos(400-token text, its first 254 tokens) = 1.000000      warnings during encode(): 0
```

**Key points** (a 3 needs every point):
- [ ] 254 text tokens.
- [ ] The 256 cap includes `[CLS]` and `[SEP]`.
- [ ] The rest is dropped silently.

**For a 4, also:**
- [ ] Gives the evidence (cosine 1.000000 with the 254-token prefix) and the rule: count chunks with the embedder's own tokenizer, not the generator's.

**Common wrong answers:**
- [ ] "All 300, the model reads the whole chunk": the vector is identical to that of the first 254 tokens.
- [ ] "256": two of the 256 IDs are the markers.

**If you missed it, reread:** [short §5](../reading/P1_llm_fundamentals.md#5-bridge-the-embedder-stops-reading-at-254-tokens) · [full D.4](../../concepts/P1_llm_fundamentals.md#d4-embedding-truncation-what-minilm-actually-reads) · book Ch4 p.5/15 (chunks sized for a model's limit)

</details>
<!-- /q -->

<!-- q id=P1-R-05 type=R set=main -->
### P1-R-05 · Recall
**Question:** Why does the same sentence cost more tokens in Hindi than in English under cl100k?

**Reply template:** `Because the pieces were learned from ____, so Hindi ____. Evidence: ____.`

<details><summary>Hint 1</summary>

Where did the tokenizer's pieces come from?

</details>

<details><summary>Hint 2</summary>

BPE merges the pairs that were frequent in its training text, and tiktoken works on bytes. What happens to a script that was rare in that text, and how many bytes does a Devanagari character take?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** BPE pieces are learned from how often character (byte) pairs occur in the training text. A script that was rare there gets few long pieces, so its text falls apart into short pieces, often single bytes, and Devanagari characters take several bytes each in UTF-8. The result is more tokens per character. A tokenizer whose vocabulary has more Hindi pieces does much better:

```
Hindi sentence, 61 characters = 161 UTF-8 bytes
cl100k_base     62 tokens   0.98 characters per token
o200k_harmony   18 tokens   3.39 characters per token
English climate PDF, cl100k:  5.57 characters per token
```

**Key points** (a 3 needs every point):
- [ ] The pieces were learned from training-text frequency, before the model existed.
- [ ] A rarely seen script is cut into many short pieces (down to bytes), so it needs more tokens per character.
- [ ] Evidence: 62 cl100k tokens against 18 o200k for the same 61-character sentence.

**For a 4, also:**
- [ ] Names the consequences (higher cost, less room in the window, ÷ 4 wrong by 75% here) and the external evidence: across many languages, some need up to 15× more tokens for the same text (Petrov et al., NeurIPS 2023).

**Common wrong answers:**
- [ ] "Hindi has more letters": the sentence is only 61 characters; the cost is in how they are cut.
- [ ] "The embedding model does not understand Hindi": the count is decided by the tokenizer, before any model runs (MC-001).

**If you missed it, reread:** [short §2](../reading/P1_llm_fundamentals.md#2-where-the-pieces-come-from-bpe) · [short §3](../reading/P1_llm_fundamentals.md#3-characters-per-token-is-measured-not-4) · [full D.3](../../concepts/P1_llm_fundamentals.md#d3-characters-per-token-measured-not-assumed) · book Ch2 p.9/11 (billing per token)

</details>
<!-- /q -->

<!-- q id=P1-R-06 type=R set=main -->
### P1-R-06 · Recall
**Question:** Which `usage` field shows a Groq call's reasoning tokens, and are they billed?

**Reply template:** `The field is ____. They are billed as ____, and they also count against ____.`

<details><summary>Hint 1</summary>

The reasoning is part of what the model generates. Which half of `usage` describes generated tokens?

</details>

<details><summary>Hint 2</summary>

Look inside `completion_tokens_details`. Then ask: which price applies to generated tokens?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** `usage.completion_tokens_details.reasoning_tokens`. Reasoning tokens are **output** tokens: billed at the output price (4× the input price on Groq) and counted against `max_completion_tokens`.

```
O2 smoke call (cap 256, effort low):  completion_tokens 23   visible reply 4 tokens   → about 19 not visible
Groq gpt-oss-20b:  input $0.075, output $0.30 per 1M tokens (read 2026-10-17)
```

**Key points** (a 3 needs every point):
- [ ] `usage.completion_tokens_details.reasoning_tokens`.
- [ ] Yes, billed as output tokens, at the output price.
- [ ] They count against the output cap.

**For a 4, also:**
- [ ] Gives the limit: `total_tokens` = prompt + completion, so reasoning is most likely **inside** `completion_tokens`; that is an inference until one recorded response confirms it.

**Common wrong answers:**
- [ ] "Reasoning is hidden, so it is free": you pay for every generated token.
- [ ] "Reasoning is in `prompt_tokens`": the model generates it, so it is output.

**If you missed it, reread:** [short §7](../reading/P1_llm_fundamentals.md#7-reasoning-spends-the-output-cap) · [short §10](../reading/P1_llm_fundamentals.md#10-price-it-output-costs-four-times-input) · [full B.3](../../concepts/P1_llm_fundamentals.md#b3-the-bill-does-not-match-your-count) · book Ch22 p.14/19 (track input and output tokens per query)

</details>
<!-- /q -->

<!-- q id=P1-A-01 type=A set=main -->
### P1-A-01 · Application
**Question:** About how many cl100k tokens is a 2,000-character page of the climate PDF?

**Reply template:** `About ____, because ____ characters per token. Range: ____.`

<details><summary>Hint 1</summary>

Use the PDF's own measured ratio, not 4.

</details>

<details><summary>Hint 2</summary>

The 91 windows have a median of 5.52 characters per cl100k token, ranging from 4.61 to 6.37.

</details>

<details><summary>Hint 3</summary>

2,000 / 5.52; then 2,000 / 6.37 and 2,000 / 4.61 for the range.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
2,000 / 5.52 ≈ 362 tokens          (median ratio of the 91 windows)
range: 2,000 / 6.37 ≈ 314   to   2,000 / 4.61 ≈ 434
chars ÷ 4 would say 500            (too many for this PDF)
```

**Key points** (a 3 needs every point):
- [ ] About 362, using the measured 5.52 characters per token.
- [ ] A range of about 314–434 from the window ratios.

**For a 4, also:**
- [ ] Self-checks: the answer must be well below 500 (÷ 4 over-counts this PDF by 39%), and says the real check is to count the page with the tokenizer.

**Common wrong answers:**
- [ ] "500": that is ÷ 4, not this corpus.
- [ ] "2,000": one token per character (MC-001).

**If you missed it, reread:** [short §3](../reading/P1_llm_fundamentals.md#3-characters-per-token-is-measured-not-4) · [full D.3](../../concepts/P1_llm_fundamentals.md#d3-characters-per-token-measured-not-assumed) · book Ch2 p.9/11

</details>
<!-- /q -->

<!-- q id=P1-A-02 type=A set=main -->
### P1-A-02 · Application
**Question:** Each query uses 1,000 input and 300 output tokens at $X and $Y per 1M tokens: what do 100 queries cost?

**Reply template:** `(____ × X + ____ × Y) / 1,000,000`

<details><summary>Hint 1</summary>

Input and output have separate prices. Total each over 100 queries first.

</details>

<details><summary>Hint 2</summary>

Prices are per million tokens, so divide by 1,000,000 at the end.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
input:   100 × 1,000 = 100,000 tokens
output:  100 × 300   =  30,000 tokens
cost = (100,000 × X + 30,000 × Y) / 1,000,000 dollars
```

**Key points** (a 3 needs every point):
- [ ] 100,000 input tokens and 30,000 output tokens.
- [ ] Input and output priced separately.
- [ ] Divided by 1,000,000 (prices are per 1M tokens).

**For a 4, also:**
- [ ] Self-checks the units, and notes that on a reasoning model the 300 output tokens must include the reasoning, read from `usage` after a pilot.

**Common wrong answers:**
- [ ] "130,000 × X / 1,000,000": one price for all tokens; output is priced higher.
- [ ] "100,000 × X + 30,000 × Y": forgot that prices are per million tokens.

**If you missed it, reread:** [short §10](../reading/P1_llm_fundamentals.md#10-price-it-output-costs-four-times-input) · [full D.7](../../concepts/P1_llm_fundamentals.md#d7-cost-from-token-counts) · book Ch22 p.14/19

</details>
<!-- /q -->

<!-- q id=P1-A-03 type=A set=main -->
### P1-A-03 · Application (what if T doubles?)
**Question:** In the toy, temperature doubles from 1 to 2: does p(YES) go up or down?

**Reply template:** `It goes ____, from ____ to about ____, because ____.`

<details><summary>Hint 1</summary>

Toy logits [2.0, 1.5, 0.5, −1.0] for YES / NO / PARTIAL / MAYBE. What does a larger T do to the gaps between them?

</details>

<details><summary>Hint 2</summary>

At T = 2 the scores become [1.0, 0.75, 0.25, −0.5]. Smaller gaps: is the top share larger or smaller?

</details>

<details><summary>Hint 3</summary>

e^1.0 = 2.718; e^0.75 = 2.117; e^0.25 = 1.284; e^−0.5 = 0.607. Divide the first by their sum.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** **Down**, from 0.532 to about 0.404. Dividing by a larger T shrinks the gaps between the scores, so the probability spreads to the other tokens.

```
T = 1:   p = 0.532 / 0.323 / 0.119 / 0.026
T = 2:   p = 0.404 / 0.315 / 0.191 / 0.090       (2.718 / 6.726 ≈ 0.404)
```

**Key points** (a 3 needs every point):
- [ ] Down.
- [ ] From 0.532 to about 0.404.
- [ ] Mechanism: a larger T shrinks the gaps between logits, so the distribution flattens.

**For a 4, also:**
- [ ] Self-checks: the four probabilities still sum to 1, and the unlikely tokens gain (MAYBE 0.026 → 0.090).

**Common wrong answers:**
- [ ] "Up, a higher temperature makes the model more confident": it makes the choice more random.
- [ ] "It halves to 0.266": T divides the logits, not the probabilities.

**If you missed it, reread:** [short §8](../reading/P1_llm_fundamentals.md#8-temperature-reshapes-the-odds) · [full D.6](../../concepts/P1_llm_fundamentals.md#d6-temperature-and-sampling) · book Ch22 p.8/19

</details>
<!-- /q -->

<!-- q id=P1-A-04 type=A set=main -->
### P1-A-04 · Application (debugging)
**Question:** This check passes on the reasoning model, but the app shows blank answers: what is wrong?

```python
r = client.chat.completions.create(model=MODEL, messages=msgs, max_completion_tokens=12, temperature=0)
assert r.choices[0].finish_reason is not None
```

**Reply template:** `The bug is ____. The fix is ____.`

<details><summary>Hint 1</summary>

What does the model write before the answer, and which budget pays for it?

</details>

<details><summary>Hint 2</summary>

Two problems stack up: the cap, and what the assert actually tests.

</details>

<details><summary>Hint 3</summary>

`finish_reason` is set on every response, including one that stopped at the cap. Test the text, and test the reason's value.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** A cap of 12 output tokens leaves no room after the reasoning, so the visible answer is empty (our O2 run did exactly this). The assert only checks that a stop reason exists, which is always true. Fix: a realistic cap, an explicit low effort, and asserts on the content and on the reason's value.

```python
r = client.chat.completions.create(model=MODEL, messages=msgs, max_completion_tokens=512,
                                   reasoning_effort="low", temperature=0)
choice = r.choices[0]
assert choice.finish_reason == "stop", choice.finish_reason      # anything else: not finished
assert (choice.message.content or "").strip(), "empty answer"
```

**Key points** (a 3 needs every point):
- [ ] `max_completion_tokens=12` is used up by the reasoning, so no answer text is left.
- [ ] The assert never checks the content (a `finish_reason` always exists).
- [ ] Fix: a larger cap (v0 uses 512), `reasoning_effort="low"`, and an assert that the answer is non-empty.

**For a 4, also:**
- [ ] Also asserts that `finish_reason` is `stop` (the exact value Groq returns at the cap is not verified in this course, so treat anything else as not finished) and logs `reasoning_tokens`.

**Common wrong answers:**
- [ ] "Use `max_tokens` instead": Groq deprecated it in favour of `max_completion_tokens`; renaming fixes nothing.
- [ ] "Temperature 0 caused the blank answer": the cap did; temperature does not create room for the answer.

**If you missed it, reread:** [short §7](../reading/P1_llm_fundamentals.md#7-reasoning-spends-the-output-cap) · [full B.2](../../concepts/P1_llm_fundamentals.md#b2-the-empty-answer-our-own-o2-run) · [full J](../../concepts/P1_llm_fundamentals.md#part-j--failure-and-debugging) · book Ch22 p.14/19 (output tokens per query)

</details>
<!-- /q -->

<!-- q id=P1-A-05 type=A set=main -->
### P1-A-05 · Application
**Question:** Using the dated Groq prices below, what do 100 v0 calls cost at most, and what share of that is output?

```
one v0 call: 976 counted input tokens, output cap 512 (reasoning + answer)
Groq openai/gpt-oss-20b, read 2026-10-17: input $0.075, output $0.30 per 1M tokens
```

**Reply template:** `One call ≤ $____; 100 calls ≤ $____; output is ____% of it.`

<details><summary>Hint 1</summary>

Price input and output separately for one call, at the cap. Then multiply by 100.

</details>

<details><summary>Hint 2</summary>

(976 × 0.075 + 512 × 0.30) / 1,000,000. The output share is the output part divided by the total.

</details>

<details><summary>Hint 3</summary>

976 × 0.075 = 73.2 and 512 × 0.30 = 153.6 (in millionths of a dollar).

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
one call  ≤ (976 × 0.075 + 512 × 0.30) / 10⁶ = (73.2 + 153.6) / 10⁶ = $0.0002268 ≈ $0.000227
100 calls ≤ $0.0227
output share = 153.6 / 226.8 = 67.7%
```

The output is about half as many tokens as the input, but each output token costs 4× as much, so output is about two thirds of the bill.

**Key points** (a 3 needs every point):
- [ ] One call ≤ $0.000227.
- [ ] 100 calls ≤ $0.0227.
- [ ] Output is about 68% of the cost.

**For a 4, also:**
- [ ] Says why it is "at most" and what is missing: output is priced at the full cap, but the input omits the hidden template (~71 tokens), so after a pilot you replace both with `usage` numbers. Cached input ($0.037 per 1M) would lower the input part.

**Common wrong answers:**
- [ ] "Input is bigger, so input dominates the bill": output costs 4× per token.
- [ ] "$22,680": 100 × (73.2 + 153.6), but forgot to divide by one million.

**If you missed it, reread:** [short §10](../reading/P1_llm_fundamentals.md#10-price-it-output-costs-four-times-input) · [full D.7](../../concepts/P1_llm_fundamentals.md#d7-cost-from-token-counts) · book Ch1 p.13/14 and Ch22 p.14/19

</details>
<!-- /q -->

<!-- q id=P1-A-06 type=A set=main -->
### P1-A-06 · Application (debugging)
**Question:** `tiktoken.encoding_for_model(GROQ_MODEL_ID)` raises `KeyError` with the `.env` id `openai/gpt-oss-20b`: why, and what is the one-line fix?

**Reply template:** `It fails because ____. The fix is ____.`

<details><summary>Hint 1</summary>

Try the bare name `gpt-oss-20b` in your head. What is different about the `.env` id?

</details>

<details><summary>Hint 2</summary>

tiktoken maps model names by their prefix (`gpt-oss-` → an encoding). Which part of the `.env` id gets in the way, and can you name the encoding directly?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** tiktoken maps a model **name** to an encoding by its prefix, and the `.env` id carries Groq's provider prefix `openai/`, so no rule matches. Name the encoding directly, or strip the prefix:

```
encoding_for_model('gpt-oss-20b')          → o200k_harmony
encoding_for_model('openai/gpt-oss-20b')   → KeyError
fix:  enc = tiktoken.get_encoding("o200k_harmony")
  or  enc = tiktoken.encoding_for_model(GROQ_MODEL_ID.split("/")[-1])
```

**Key points** (a 3 needs every point):
- [ ] The provider prefix `openai/` stops tiktoken's name lookup.
- [ ] Fix: `tiktoken.get_encoding("o200k_harmony")` (or strip the prefix).

**For a 4, also:**
- [ ] Names the second trap: a document that contains a special-token string such as `<|endoftext|>` makes `encode()` raise `ValueError`; pass `disallowed_special=()` to count it as ordinary text (7 tokens).

**Common wrong answers:**
- [ ] "Use `cl100k_base`, it is close enough": it is another model's tokenizer; close on English (13,026 vs 12,840 on the PDF) but far off on Hindi (62 vs 18).
- [ ] "Upgrade tiktoken": the bare name already works; the id is the problem.

**If you missed it, reread:** [short §4](../reading/P1_llm_fundamentals.md#4-count-with-the-right-tokenizer-two-traps) · [full K](../../concepts/P1_llm_fundamentals.md#part-k--engineering-decisions) · [full J](../../concepts/P1_llm_fundamentals.md#part-j--failure-and-debugging) · book Ch22 p.14/19 (token counts per query)

</details>
<!-- /q -->

<!-- q id=P1-A-07 type=A set=main -->
### P1-A-07 · Application
**Question:** A run of 55 calls uses 1,559 tokens per call under a limit of 8,000 tokens per minute: what is the shortest possible run time?

**Reply template:** `____ tokens / ____ per minute ≥ ____ minutes, because ____.`

<details><summary>Hint 1</summary>

The limit is in tokens per minute, not calls per minute. Total the tokens first.

</details>

<details><summary>Hint 2</summary>

55 × 1,559, then divide by 8,000.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
55 × 1,559 = 85,745 tokens
85,745 / 8,000 ≈ 10.7 minutes, at the very least
```

The token limit, not the money, decides the time: the whole run costs well under a cent.

**Key points** (a 3 needs every point):
- [ ] 85,745 tokens in total.
- [ ] At least about 10.7 minutes.
- [ ] Time ≥ total tokens / tokens per minute: it is a floor.

**For a 4, also:**
- [ ] Says why it is a floor (retries and queueing only add time) and checks the daily quota too; the 8,000-per-minute and 200,000-per-day figures for our plan are UNVERIFIED, so read the account's limits page.

**Common wrong answers:**
- [ ] "55 calls is about a minute": the limit counts tokens, not calls.
- [ ] "Exactly 10.7 minutes": that assumes no waiting at all; it is the minimum.

**If you missed it, reread:** [short §11](../reading/P1_llm_fundamentals.md#11-time-it-limits-are-tokens-per-minute) · [full D.7](../../concepts/P1_llm_fundamentals.md#d7-cost-from-token-counts) · book Ch22 p.14/19 (latency and cost as evaluation dimensions)

</details>
<!-- /q -->

<!-- q id=P1-T-01 type=T set=main -->
### P1-T-01 · Transfer
**Question:** A team will index Japanese support tickets and asks you for the chunk size in characters: what do you tell them first?

**Reply template:** `First I would ____. I expect ____ because ____. I would check it by ____.`

<details><summary>Hint 1</summary>

Which number from this lesson would you be tempted to reuse, and why might it not hold for Japanese?

</details>

<details><summary>Hint 2</summary>

Two tokenizers matter: the embedder's (truncation) and the generator's (prompt budget). What do you measure with each, and how would you know the chunks work?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** First measure characters per token on a sample of real tickets, with the **embedder's** tokenizer and with the generator's. Do not reuse 4, or the 5.5 of our English PDF. A script that was rare in a tokenizer's training text can fall near or below 1 character per token:

```
Hindi sentence (61 characters):   cl100k 0.98 chars/token     o200k_harmony 3.39
English climate PDF:              cl100k 5.57
```

Then set the chunk size so that chunks stay under the embedder's limit (MiniLM: 254 text tokens; check the default Cohere embedder's `truncate` setting), and check that the embedder supports Japanese at all. Verify with the truncation rate and CE@k on a small labelled set of tickets. Trade-off: smaller chunks mean more vectors and more embedding cost.

**Key points** (a 3 needs every point):
- [ ] Measure characters per token on real tickets; do not assume 4 or 5.5.
- [ ] Use the embedder's tokenizer for the chunk limit (truncation) and the generator's for the prompt budget.
- [ ] Check that the embedder supports the language (a multilingual model may be needed).

**For a 4, also:**
- [ ] Says how to verify (truncation rate and CE@k on labelled tickets) and when chunk size is not the fix: if the embedder cannot represent Japanese, change the model.

**Common wrong answers:**
- [ ] "1,000 characters, like the English PDF": Japanese may hold far fewer characters per token, so the chunk may overflow the embedder.
- [ ] "Count with tiktoken and you are done": the embedder enforces its cap in its own tokens.

**If you missed it, reread:** [short §3](../reading/P1_llm_fundamentals.md#3-characters-per-token-is-measured-not-4) · [short §4](../reading/P1_llm_fundamentals.md#4-count-with-the-right-tokenizer-two-traps) · [short §5](../reading/P1_llm_fundamentals.md#5-bridge-the-embedder-stops-reading-at-254-tokens) · [full D.3](../../concepts/P1_llm_fundamentals.md#d3-characters-per-token-measured-not-assumed) · [full D.4](../../concepts/P1_llm_fundamentals.md#d4-embedding-truncation-what-minilm-actually-reads) · book Ch4 p.5/15

</details>
<!-- /q -->

<!-- q id=P1-T-02 type=T set=main -->
### P1-T-02 · Transfer (changing the generator)
**Question:** You switch the generator from gpt-oss-20b on Groq to Claude Haiku 5.5: what changes in your token counting, your cost estimate and your sampling code?

**Reply template:** `Counting: ____. Cost: ____. Sampling: ____. I would check by ____.`

<details><summary>Hint 1</summary>

Take the three parts in turn. Which tokenizer, which price sheet, which parameters?

</details>

<details><summary>Hint 2</summary>

Claude has its own tokenizer and a counting endpoint. Its prices have a different output-to-input ratio. And current Claude models refuse one parameter you send to Groq.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**
- **Counting.** Claude uses its own tokenizer, not tiktoken. Count with Anthropic's `count_tokens` endpoint (free, rate-limited, an estimate, and per model: newer Claude tokenizers give about 30% more tokens for the same text). Our o200k counts are only a proxy.
- **Cost.** New dated prices with a 5× output ratio instead of 4×. With the o200k counts as a proxy:

```
                       input    output   per 1M (read 2026-10-17)    100 v0 calls at the cap   output share
Groq gpt-oss-20b       $0.075   $0.30    ratio 4×                     ≤ $0.0227                67.7%
Claude Haiku 5.5       $0.10    $0.50    ratio 5×                     ≤ $0.0354                72.4%
```

- **Sampling and limits.** Stop sending `temperature`: current Claude models reject it (HTTP 400). Send `effort` explicitly instead of `reasoning_effort`. Thinking is on by default and bills as output, so size the output cap (`max_tokens` on Claude) for thinking plus answer, and read `stop_reason` instead of `finish_reason`.

Check it with a few recorded calls: compare `count_tokens` with billed `usage`, and confirm that the answers are non-empty and stopped normally. Treat the switch as a new experiment arm, never a silent swap.

**Key points** (a 3 needs every point):
- [ ] Count with Claude's own `count_tokens`, not tiktoken; o200k numbers are only a proxy.
- [ ] Use Claude's dated prices (output 5× input), so the cost estimate changes (≤ $0.0354 per 100 v0 calls on proxy counts).
- [ ] Do not send `temperature` (400); send `effort`, and budget the output cap for thinking.

**For a 4, also:**
- [ ] Says how to measure (record a few calls; compare estimated and billed tokens; check non-empty answers and the stop reason) and keeps it as a separate experiment arm, not a silent swap of the generator.

**Common wrong answers:**
- [ ] "Keep counting with o200k_harmony, a token is a token": each provider counts its own tokens (MC-001 extended).
- [ ] "Keep temperature 0 for repeatability": current Claude models reject the parameter; repeatability comes from replaying recorded calls.

**If you missed it, reread:** [short §9](../reading/P1_llm_fundamentals.md#9-each-provider-counts-and-samples-its-own-way) · [short §10](../reading/P1_llm_fundamentals.md#10-price-it-output-costs-four-times-input) · [short §8](../reading/P1_llm_fundamentals.md#8-temperature-reshapes-the-odds) · [full D.7](../../concepts/P1_llm_fundamentals.md#d7-cost-from-token-counts) · book Ch22 p.14/19–p.15/19

</details>
<!-- /q -->

<!-- q id=P1-T-03 type=T set=review -->
### P1-T-03 · Transfer (review)
**Question:** A monitoring dashboard shows completion tokens at about ten times the length of the visible answers: what do you suspect, and what do you check?

**Reply template:** `I suspect ____. I would check ____. I would change ____ only if ____.`

<details><summary>Hint 1</summary>

What else, besides the answer, is a completion token on this model?

</details>

<details><summary>Hint 2</summary>

Find the field that splits the completion, the parameter that sets how much reasoning happens, and its default if you never send it.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Reasoning. On gpt-oss, completion tokens are the reasoning plus the visible answer, so a large gap is normal in kind; the question is whether it is too large. Check:
1. `usage.completion_tokens_details.reasoning_tokens` against the visible tokens (count the answer with `o200k_harmony`).
2. Whether `reasoning_effort` is sent at all: if not, the server uses **medium**, not the course's **low**.
3. The rate of `finish_reason` other than `stop`, and of empty answers: reasoning may be crowding the cap.

```
O2 smoke call (effort low):   23 completion tokens for a 4-token reply  →  23 / 4 ≈ 5.8×
reasoning bills as output:    $0.30 per 1M on Groq, 4× the input price (read 2026-10-17)
```

Change the effort or the cap only if answer quality holds at the lower setting, measured on an eval with the reasoning share (p50/p95), cost per query and the empty-answer rate side by side.

**Key points** (a 3 needs every point):
- [ ] The extra completion tokens are reasoning, billed as output.
- [ ] Read `reasoning_tokens` from `usage` to confirm the split.
- [ ] Check whether `reasoning_effort` is set (server default medium) and whether answers hit the cap.

**For a 4, also:**
- [ ] Says how to decide: measure reasoning share, cost and empty-answer or length-stop rates per effort level on an eval, and lower the effort only if quality holds; a large ratio alone is not a bug.

**Common wrong answers:**
- [ ] "The tokenizer is counting wrong": the provider's `usage` is the bill; the gap is reasoning.
- [ ] "Lower the cap until the ratio drops": a smaller cap can cut off the answer, not the reasoning.

**If you missed it, reread:** [short §7](../reading/P1_llm_fundamentals.md#7-reasoning-spends-the-output-cap) · [full B.3](../../concepts/P1_llm_fundamentals.md#b3-the-bill-does-not-match-your-count) · book Ch22 p.14/19

</details>
<!-- /q -->

<!-- q id=P1-R-07 type=R set=interview source=AIQ-08-Q14 -->
### P1-R-07 · Interview (Recall)
**Question:** "Your production code reads the response text but never checks `finish_reason` (or `stop_reason`). Why is that a bug, and what should you do with each stop reason?"
*From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `08-inference-and-production/questions.md` (question 14), Copyright (c) 2026 Om, MIT License.*

**Reply template:** `It is a bug because ____. For each reason: ____. On our reasoning model: ____.`

<details><summary>Hint 1</summary>

A response can end for reasons other than "the model was done". Which one did our O2 call hit?

</details>

<details><summary>Hint 2</summary>

List the values: normal stop, cap reached, stop sequence, tool call, refusal or filter. Give one action for each, then one monitoring habit.

</details>

<details><summary>Show answer (write yours first)</summary>

> **The repo's answer (excerpt, verbatim).** *From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `08-inference-and-production/questions.md`, Copyright (c) 2026 Om, MIT License:*
>
> "**Natural stop** (`stop`, `end_turn`): the model finished. Validate and use it."
>
> "**Length** (`length`, `max_tokens`): truncated at the cap. Prose ends mid-sentence. JSON or a tool call is unparseable, and constrained decoding does not save you, because the grammar cannot close the object once the budget is gone. Raise the cap for that feature, ask for a shorter format, or continue the generation, but never parse it as complete. On reasoning models, thinking tokens usually count against the same budget, so a request can hit the cap before writing any visible answer."
>
> "Log the stop reason on every call and chart the rate of length stops per feature. A jump after a prompt or model change is an early sign of verbosity creep, and it shows up before users complain about cut-off answers."
>
> "Treat an unknown value as an error. Providers add new ones, and a default branch that assumes success is how a new stop reason ships truncated data."

**Our check of that answer:** right, and the reasoning-model sentence matches our own O2 run: at a 12-token cap the visible answer was empty. Three notes for our generator:
1. On Groq the cap parameter is `max_completion_tokens`; `max_tokens` is deprecated there. On Claude the cap is still called `max_tokens`, and the stop field is `stop_reason`.
2. The exact `finish_reason` value Groq returns when gpt-oss hits the cap is UNVERIFIED in this course: our O2 report did not log it. So the safe rule is the repo's last one: accept only `stop`, and treat anything else as not finished.
3. A reasoning model can hit the cap with an **empty** answer, not just a cut-off one, so also assert that the text is non-empty.

**Model answer:** The text alone does not tell you why generation ended. A cut-off, filtered or tool-call response can look like an answer, so reading it without the stop reason ships broken output as if it were complete. Act per value: `stop` → validate and use; `length` → never parse as complete, raise the cap or shorten the format; stop sequence → expected only if you designed it; tool call → run the tool; refusal or filter → a deliberate message, logged, no blind retry; unknown → an error. Log the reason on every call and chart the length-stop rate. On gpt-oss, reasoning shares the output cap, so a too-small `max_completion_tokens` gives an empty answer with a non-`stop` reason.

**Key points** (a 3 needs every point):
- [ ] The text alone cannot show that the response was truncated, filtered or a tool call.
- [ ] One action per reason: use on `stop`; never parse as complete on `length` (raise the cap or shorten); handle tool calls and refusals; treat unknown values as errors.
- [ ] Log the stop reason on every call and watch the length-stop rate.

**For a 4, also:**
- [ ] Ties it to reasoning models with evidence (O2: empty answer at a 12-token cap) and to our setup (`max_completion_tokens`; Groq's value at the cap unverified, so accept only `stop`).

**Common wrong answers:**
- [ ] "If the text is not empty, the call worked": a `length` stop returns plausible text that is cut off.
- [ ] "Just retry on any non-stop reason": a retry with the same cap hits the same limit, and retrying a refusal repeats it.

**If you missed it, reread:** [short §7](../reading/P1_llm_fundamentals.md#7-reasoning-spends-the-output-cap) · [full B.2](../../concepts/P1_llm_fundamentals.md#b2-the-empty-answer-our-own-o2-run) · [full J](../../concepts/P1_llm_fundamentals.md#part-j--failure-and-debugging) · book Ch22 p.15/19 (continuous monitoring with alerts)

</details>
<!-- /q -->

<!-- q id=P1-R-08 type=R set=interview source=AIQ-02-Q42 -->
### P1-R-08 · Interview (Recall)
**Question:** "Reasoning models expose a thinking budget or reasoning effort setting. How do you tune it, and what goes wrong?"
*From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `02-llm-fundamentals/questions.md` (question 42), Copyright (c) 2026 Om, MIT License.*

**Reply template:** `I tune it by ____. It costs ____. What goes wrong: ____.`

<details><summary>Hint 1</summary>

Think of effort as a knob with a price: what goes up when you turn it up?

</details>

<details><summary>Hint 2</summary>

How would you pick the setting with evidence, not by intuition? Then name two failures: one from a cap that is too small, one from never setting it.

</details>

<details><summary>Show answer (write yours first)</summary>

> **The repo's answer (excerpt, verbatim).** *From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `02-llm-fundamentals/questions.md`, Copyright (c) 2026 Om, MIT License:*
>
> "Treat it as an explicit accuracy-versus-cost-and-latency knob, and calibrate it per task with an eval rather than by intuition. The shape is a saturating curve: accuracy climbs steeply over the first stretch of thinking tokens, flattens, and on easy tasks can actually decline."
>
> "A hard token cap enforced at decode. The model gets cut off and forced to answer, which can truncate mid-derivation and produce something worse than no thinking at all."
>
> "Respect the cost model. Thinking tokens bill as output tokens, output tokens are the expensive ones, and they are generated serially, so budget maps almost linearly onto latency. A 10x budget is roughly a 10x latency hit on that call."

**Our check of that answer:** the frame (a cost and latency knob, chosen per task with an eval) and the billing claim are right: reasoning is output, and output costs 4× input on Groq and 5× on Claude Haiku (read 2026-10-17). Three notes for our setup:
1. gpt-oss on Groq has no "off": `reasoning_effort` takes only `low`, `medium` or `high` (other values are rejected with HTTP 400), and the server default is `medium`. So the lowest setting the course can choose is `low`, which it pins explicitly.
2. On Groq, `max_completion_tokens` is a hard cap on reasoning and answer **together**. At a 12-token cap our O2 call was not "forced to answer"; it returned an empty answer.
3. The saturating accuracy curve and "10x budget is roughly a 10x latency hit" are not measured in this course (UNVERIFIED). The P1 LLMOps notebook plans a cap × effort sweep to see it on our data.

**Model answer:** Treat effort as a knob that trades answer quality against output tokens, cost and latency. Tune it per task: sweep the effort levels (and the cap) on an eval set, record accuracy, reasoning tokens, p95 latency, cost per query and the empty-answer and length-stop rates, and pick the lowest setting that meets the quality target. Always send it explicitly, because the default (`medium` on Groq) is not the course's choice. What goes wrong: a cap that is too small for the reasoning gives empty or cut-off answers; never setting effort silently spends more; high effort can add cost and delay where it buys no quality; and reasoning bills as output, the expensive side.

**Key points** (a 3 needs every point):
- [ ] Effort trades quality against output tokens, cost and latency.
- [ ] Choose it per task with an eval sweep (quality next to cost and latency), not by intuition.
- [ ] Failure: a cap too small for the reasoning gives an empty or cut-off answer.
- [ ] Reasoning bills as output tokens, which cost more than input.

**For a 4, also:**
- [ ] Applies it to our generator: gpt-oss accepts only low / medium / high with a server default of medium, so the course sends `low` explicitly and checks `finish_reason` and non-empty answers.

**Common wrong answers:**
- [ ] "Set it high for the best quality": that is a bill, not a decision; measure where quality stops improving.
- [ ] "Turn reasoning off for simple tasks": gpt-oss on Groq has no off; the lowest is `low`.

**If you missed it, reread:** [short §7](../reading/P1_llm_fundamentals.md#7-reasoning-spends-the-output-cap) · [short §10](../reading/P1_llm_fundamentals.md#10-price-it-output-costs-four-times-input) · [full B.2](../../concepts/P1_llm_fundamentals.md#b2-the-empty-answer-our-own-o2-run) · book Ch22 p.14/19–p.15/19 (every quality gain has a cost trade-off)

</details>
<!-- /q -->
