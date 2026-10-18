<!-- kit:questions concept=I5 version=1 -->
# I5 questions: contextual chunk headers and contextual retrieval

**How to use:** write your answer and a confidence (1–3) first. Then open the answer and tick the key points you really wrote.

**Where the numbers come from:** `sources/verification/I5/i5_kit_measure.py` on the climate PDF and v0's 97 chunks ([I5_FACTS](../../sources/verification/I5/I5_FACTS.md) K1–K15; [kit run](../../sources/verification/I5/out_i5_kit_measure.txt)). Token counts are DERIVED estimates (no tokenizer could be downloaded in the build session). MiniLM margins and ranks for the header arms were not measured: the verify notebook computes them on your machine. Anthropic, cookbook and dsRAG numbers are CITED vendor reports; Groq's limits are UNVERIFIED. The draft questions D-001…D-010 are LLM drafts, not checked by you. "Toy" vectors are made up. No API was called to write this file.

<!-- q id=I5-PRE-01 type=R set=pre -->
### I5-PRE-01 · Recall (before reading)
**Question:** Why can a chunk that begins "It was adopted in 2015 …" miss a question asking when the Paris Agreement was adopted?

**Reply template:** `It misses because ____. The retriever only sees ____. A fix is ____.`

<details><summary>Hint 1</summary>

Which words of the question appear in that chunk?

</details>

<details><summary>Hint 2</summary>

Where is the name "Paris Agreement" written for that chunk: inside its span, or before it?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** "It" refers to the Paris Agreement, but the name sits in a heading or sentence before the chunk's span. A retriever, dense or BM25, scores only the chunk's own text, so the question's key words have nothing to match. The chunk is **contextually anonymous**. The fix works at index time: prepend a header that restores the context (a heading path, or an LLM-written sentence naming the subject) to the text you embed, and leave the stored chunk text unchanged.

```
question   "When was the Paris Agreement adopted?"
chunk      "It was adopted in 2015 ..."      shared content words: adopted (and nothing that names the subject)
```

**Key points** (a 3 needs every point):
- [ ] The name the question uses is not in the chunk: "it" points outside the span.
- [ ] The retriever scores only the chunk's own words, so the match is weak.

**For a 4, also:**
- [ ] Names the fix and where it goes: a header prepended to the embedded text at index time, with the stored text unchanged.

**Common wrong answers:**
- [ ] "The embedding model understands that 'it' means the Paris Agreement": the model sees only the chunk; the referent is not in its input.
- [ ] "The year 2015 will match the question": the question asks for the year; it does not contain it.

**If you missed it, reread:** [short §1](../reading/I5_contextual_headers.md#1-a-chunk-loses-its-context) · [lesson #anon](../lessons/I5_contextual_headers.html#anon) · book Ch7 p.1–2/11

</details>
<!-- /q -->

<!-- q id=I5-PRE-02 type=R set=pre -->
### I5-PRE-02 · Recall (before reading)
**Question:** Your corpus is one PDF: does prepending its title to every chunk help the retriever rank the chunks?

**Reply template:** `____, because the title is ____ on every chunk, so ____.`

<details><summary>Hint 1</summary>

Compare the header chunk 1 gets with the header chunk 50 gets.

</details>

<details><summary>Hint 2</summary>

For a header to lift one chunk above another, what must be true of their two headers?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** No, not with information. On one document every chunk gets the same title, so the header gives no reason to prefer one chunk over another. It still changes something: the same tokens shift every vector toward the title's topic, so ranks can move, but by accident, not by information.

```
Corpus D        distinct headers
title only       1 / 97
heading path    97 / 97   (start rule)
```

**Key points** (a 3 needs every point):
- [ ] No: the title is identical on every chunk, so it adds nothing that separates chunks.
- [ ] A header can help ranking only if it differs between chunks.

**For a 4, also:**
- [ ] Says what it still changes (every vector shifts, so ranks can move; in BM25 the title words fall to the idf floor) and that titles can help when the corpus has several documents.

**Common wrong answers:**
- [ ] "Yes, the title tells the model the topic": every chunk is already on that topic.
- [ ] "It changes nothing at all": it shifts every vector, so ranks can move without new information.

**If you missed it, reread:** [short §6](../reading/I5_contextual_headers.md#6-the-information-test-a-constant-title-adds-nothing) · [lesson #info](../lessons/I5_contextual_headers.html#info) · book Ch7 p.4/11

</details>
<!-- /q -->

<!-- q id=I5-R-01 type=R set=main -->
### I5-R-01 · Recall
**Question:** What makes a chunk "contextually anonymous", and which two kinds of context can a header give back?

**Reply template:** `A chunk is contextually anonymous when ____. A header can restore (1) ____ and (2) ____.`

<details><summary>Hint 1</summary>

Think of chunk 34, which starts "It can be used for tracking carbon credits".

</details>

<details><summary>Hint 2</summary>

One kind of lost context is about the document's structure; the other is about the language inside a sentence.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** A chunk is contextually anonymous when its meaning depends on text outside its span: a pronoun, an orphaned heading, the chapter it belongs to. A header can restore (1) **where it sits**, its chapter and section (the heading path), and (2) **what it refers to**, the subject behind "it", "this" or "the agreement". Chunk 34 opens with "It", meaning blockchain, named in a heading above the chunk. Chunk 68's Paris text belongs to Chapter 16, which only the headings say.

```
Corpus D (measured)   no heading inside 0 of 97 · start mid-sentence 46 of 97 · end on an orphaned heading 31 of 97
```

**Key points** (a 3 needs every point):
- [ ] Its meaning depends on text outside its span (a pronoun, an orphaned heading, the chapter).
- [ ] Kind 1: where it sits, the chapter and section path.
- [ ] Kind 2: what it refers to, the subject of "it" or "this".

**For a 4, also:**
- [ ] Adds the Corpus D reality: every chunk already holds a heading (0 of 97 without one), so D is heading-dense and the effect will be small; a heading path restores location, while a referent may need the right heading rule or an LLM context.

**Common wrong answers:**
- [ ] "Anonymous means the chunk has no heading": every D chunk has one, and chunk 34 still opens with an unexplained "It".
- [ ] "The header adds new facts to the chunk": it restores context the document already had.

**If you missed it, reread:** [short §1](../reading/I5_contextual_headers.md#1-a-chunk-loses-its-context) · [lesson #anon](../lessons/I5_contextual_headers.html#anon) · book Ch7 p.1–2/11

</details>
<!-- /q -->

<!-- q id=I5-R-02 type=R set=main -->
### I5-R-02 · Recall
**Question:** On a one-document corpus, why does a title header add no discriminating information, and what does it still change?

**Reply template:** `No information, because ____. It still changes ____ (embedding) and ____ (BM25).`

<details><summary>Hint 1</summary>

Count the distinct headers in the title arm.

</details>

<details><summary>Hint 2</summary>

Think of mean pooling with the same extra tokens on every chunk, and of idf for a word that is in every chunk.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Discriminating information is a difference between chunks. The title arm gives all 97 chunks the same 28-character header, one distinct header of 97, so there is nothing in it to rank by. It still changes two things:
1. **Embedding:** the same tokens enter every mean-pooled vector, so every vector shifts toward the title's topic and ranks can move, with no new information.
2. **BM25:** "understanding", "climate" and "change" occur in all 97 units, so their idf would be negative; `rank_bm25` lifts each to the floor 0.8565, which adds nearly the same score to every chunk.

```
title arm   distinct headers  1 / 97 · largest group 97 · idf floor 0.8565 (df 97 of 97)
path arm    distinct headers 97 / 97
```

**Key points** (a 3 needs every point):
- [ ] One distinct header for 97 chunks: the same text on every chunk cannot separate them.
- [ ] The information test: a header helps only if it varies (distinct headers ÷ chunks).
- [ ] It still shifts every vector, so ranks can move without information.

**For a 4, also:**
- [ ] Names the BM25 floor (idf 0.8565 for the three title words) and the right use: title-only as a negative control on D, titles tested on a multi-document corpus.

**Common wrong answers:**
- [ ] "A constant header is harmless, it cancels out": it moves every vector, and ranks can change.
- [ ] "The title gives the topic, so retrieval improves": every chunk is already on that topic.

**If you missed it, reread:** [short §6](../reading/I5_contextual_headers.md#6-the-information-test-a-constant-title-adds-nothing) · [lesson #info](../lessons/I5_contextual_headers.html#info) · book Ch7 p.4/11

</details>
<!-- /q -->

<!-- q id=I5-R-03 type=R set=main -->
### I5-R-03 · Recall
**Question:** Name the three inputs a header can be added to, and say which one v1.2 changes.

**Reply template:** `1 ____, 2 ____, 3 ____. v1.2 changes ____.`

<details><summary>Hint 1</summary>

Follow one chunk record: who reads it at index time, and who reads it when an answer is written?

</details>

<details><summary>Hint 2</summary>

One input becomes a vector, one becomes a word index, one becomes a prompt.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** (1) the embedding input, `embed_text`; (2) the BM25 input, `bm25_text`; (3) the generation input, `display_text`, which the LLM reads as evidence. **v1.2 changes the embedding input only.** BM25 is first tested at v2.0 (R1), and headers in the prompt are a later arm. The questions themselves are not changed.

| Input | Field | Tested |
|---|---|---|
| embedding | `embed_text` | v1.2 |
| BM25 | `bm25_text` | v2.0 |
| generation | `display_text` | later |

**Key points** (a 3 needs every point):
- [ ] Embedding input, BM25 input, generation input.
- [ ] v1.2 changes the embedding input only.
- [ ] Each is a separate decision, stored in its own field.

**For a 4, also:**
- [ ] Notes that queries stay unchanged (query vectors are reused across arms) and that the BM25 preview on D is at ceiling (CE@4 8/8 in every arm), so the draft seeds could not test the BM25 side anyway.

**Common wrong answers:**
- [ ] "v1.2 adds the header to both the embedding and the BM25 text": BM25 is first tested at v2.0.
- [ ] "The header also goes into the prompt": that is a later, separate arm.

**If you missed it, reread:** [short §2](../reading/I5_contextual_headers.md#2-where-the-header-goes-embed_text-not-text) · [lesson #fields](../lessons/I5_contextual_headers.html#fields) · book Ch7 p.8/11

</details>
<!-- /q -->

<!-- q id=I5-R-04 type=R set=main -->
### I5-R-04 · Recall
**Question:** Why must the header live in a separate field (`embed_text`) and not in the chunk's `text`?

**Reply template:** `Because text must ____; CE scoring uses ____; and the arm is named by ____.`

<details><summary>Hint 1</summary>

What does `DOC[char_start:char_end]` have to equal?

</details>

<details><summary>Hint 2</summary>

How are gold labels matched to retrieved chunks, and how are two index folders told apart?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** `text` must stay equal to `DOC[char_start:char_end]`, the span invariant, which holds for all 97 chunks. Gold evidence is stored as character spans, and CE@4 checks a retrieved chunk's span against them; a header inside `text` breaks the invariant and shifts the offsets and citations. The generator and BM25 read `text` too, and whether they see a header is a separate decision. Finally, the header template id goes into `preproc_version`, which changes `embed_hash`, so each arm gets its own index folder.

```
embed_text = header + "\n\n" + text      text, char_start, char_end unchanged
```

**Key points** (a 3 needs every point):
- [ ] The span invariant `text == DOC[char_start:char_end]` must keep holding.
- [ ] CE scoring and citations use the spans and offsets, which a header in `text` would corrupt.
- [ ] The template id goes into `preproc_version` → `embed_hash` → a separate index per arm.

**For a 4, also:**
- [ ] Adds that the other readers of `text` (generator, BM25) stay untouched, and that query vectors are reused unchanged.

**Common wrong answers:**
- [ ] "Just prepend it to `text`, it is simpler": the offsets, CE scoring and the prompt would all change.
- [ ] "A new folder name is enough to tell the arms apart": without the `preproc_version` bump both arms get the same `embed_hash`.

**If you missed it, reread:** [short §2](../reading/I5_contextual_headers.md#2-where-the-header-goes-embed_text-not-text) · [lesson #fields](../lessons/I5_contextual_headers.html#fields) · book Ch7 p.7/11

</details>
<!-- /q -->

<!-- q id=I5-R-05 type=R set=main -->
### I5-R-05 · Recall
**Question:** What exactly does Anthropic's "35%" improvement from contextual embeddings measure?

**Reply template:** `It is a ____ change in ____ (the metric) at k = ____, from ____ to ____.`

<details><summary>Hint 1</summary>

The metric counts failures, not successes.

</details>

<details><summary>Hint 2</summary>

Compute both b − a and (b − a) / a.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The share of relevant chunks missing from the top 20, **1 − recall@20**, fell from 5.7% to 3.7%. That is −2.0 points absolute and −35.1% relative. It is a vendor measurement on the vendor's datasets, at top 20, not CE@4.

```
5.7% → 3.7%    absolute 3.7 − 5.7 = −2.0 points    relative −2.0 / 5.7 = −35.1%
```

**Key points** (a 3 needs every point):
- [ ] The metric is 1 − recall@20: missed relevant chunks in the top 20.
- [ ] 5.7% → 3.7%.
- [ ] 35% is relative; the absolute change is 2.0 points.

**For a 4, also:**
- [ ] Adds the limit: a vendor study, not our metric (CE@4), and 2 points is far below the about 18 points that 50 questions can detect; the 49% and 67% figures add contextual BM25 and reranking.

**Common wrong answers:**
- [ ] "Retrieval accuracy rose by 35 points": it is a 2-point absolute drop in failures.
- [ ] "35% more correct answers": it measures retrieval, not answers.

**If you missed it, reread:** [short §12](../reading/I5_contextual_headers.md#12-reading-the-vendor-numbers) · [lesson #claims](../lessons/I5_contextual_headers.html#claims) · book Ch7 p.8–9/11

</details>
<!-- /q -->

<!-- q id=I5-R-06 type=R set=main -->
### I5-R-06 · Recall
**Question:** Why does prompt caching make the whole-document context arm cheap, and what makes the cache miss silently?

**Reply template:** `Cheap because ____. Silent misses: ____, ____, ____.`

<details><summary>Hint 1</summary>

What do the 97 prompts have in common, and where in the prompt is it?

</details>

<details><summary>Hint 2</summary>

Caching matches an exact prefix, with a minimum length and a lifetime.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** All 97 prompts share the same document. With the document first, the first call writes it to the cache (1.25× the input price) and the other 96 calls read it (0.1×), so only the chunk, the instruction and the output are paid in full. The cache misses silently when the prefix is below the model's minimum, when anything before the document changes between calls (the chunk placed first, a timestamp), or when calls are shuffled and the entry expires. No error is raised; only the cache-write and cache-read token counts show it.

```
Haiku 5.5, Corpus D, 97 calls      uncached $0.1367 · cached $0.0261 (5.2×)
cookbook, Haiku 4.5                 prompt 3,412 tokens < minimum 4,096 → nothing cached, no error
```

**Key points** (a 3 needs every point):
- [ ] Every prompt shares the document as its prefix: written once, then read cheaply by the rest.
- [ ] Order: document first, chunk and instruction last, chunks processed in document order.
- [ ] A prefix below the minimum length is silently not cached (no error, full price).
- [ ] Any change inside the prefix breaks the match.

**For a 4, also:**
- [ ] Gives numbers ($0.1367 vs $0.0261, or 3,412 < 4,096) and says how to see a miss: the cache-write and cache-read token counts in each response.

**Common wrong answers:**
- [ ] "Caching makes the calls faster, not cheaper": cache reads cost 0.1× of the input price.
- [ ] "If caching fails, the API returns an error": it fails silently.

**If you missed it, reread:** [short §11](../reading/I5_contextual_headers.md#11-prompt-caching-cache-keys-and-wrong-contexts) · [lesson #cache](../lessons/I5_contextual_headers.html#cache) · book Ch7 p.4–7/11

</details>
<!-- /q -->

<!-- q id=I5-A-01 type=A set=main -->
### I5-A-01 · Application
**Question:** A chunk has 182 MiniLM tokens: what is cut if you add a 27-token path header, and what if you add a 100-token LLM context instead?

```
MiniLM limit     256 tokens, [CLS] and [SEP] included (the 182 already counts them)
embed_text       header + "\n\n" + chunk text   (the header comes first)
```

**Reply template:** `182 + 27 = ____ → ____. 182 + 100 = ____ → ____ is cut, at ____.`

<details><summary>Hint 1</summary>

Compare each total with 256.

</details>

<details><summary>Hint 2</summary>

The model keeps the first 256 tokens. Which part of `embed_text` comes first?

</details>

<details><summary>Hint 3</summary>

182 + 27 = 209. Now 182 + 100, and how far over 256 that is.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
182 + 27  = 209 ≤ 256   fits: nothing is cut
182 + 100 = 282 > 256   over by 26: the last 26 tokens of the chunk text are cut
```

The header comes first, so truncation removes the **end of the chunk**, never the header. It happens silently. Self-check: the specials are already inside the 182, so they are not added again.

**Key points** (a 3 needs every point):
- [ ] 182 + 27 = 209: fits.
- [ ] 182 + 100 = 282: over by 26.
- [ ] The chunk's tail is cut, not the header, because the header comes first.

**For a 4, also:**
- [ ] Gives a self-check or the scale: on D a 100-token context would push about 29 of 97 chunks over 256 (derived), path headers 0 of 97; fix it by capping the context or using a larger-window embedder.

**Common wrong answers:**
- [ ] "The header gets cut": truncation keeps the start, and the header is the start.
- [ ] "The model raises an error over 256": it truncates silently.

**If you missed it, reread:** [short §8](../reading/I5_contextual_headers.md#8-truncation-the-tail-is-cut) · [lesson #trunc](../lessons/I5_contextual_headers.html#trunc) · book Ch7 p.7/11

</details>
<!-- /q -->

<!-- q id=I5-A-02 type=A set=main -->
### I5-A-02 · Application
**Question:** What does the whole-document context arm cost on Corpus D with Haiku 5.5, without and with prompt caching?

```
chunks n = 97        document D = 12,840 tokens       chunk + instruction = 250 tokens per call
output = 200 tokens per call
Haiku 5.5            input $0.10 per 1M tokens        output $0.50 per 1M tokens
caching              the first call writes the document at 1.25× input; the other calls read it at 0.1×
```

**Reply template:** `uncached $____ ; cached $____ ; ratio ____×`

<details><summary>Hint 1</summary>

Uncached, every call pays for the whole document plus its chunk, plus its output.

</details>

<details><summary>Hint 2</summary>

Cached: one write of D, (n − 1) reads of D, then chunk + instruction and output for all n calls.

</details>

<details><summary>Hint 3</summary>

Uncached input: 97 × (12,840 + 250) = 1,269,730 tokens at $0.10 per 1M. Then add the output.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
uncached  input   97 × 13,090 × 0.10 / 10⁶          = $0.1270
          output  97 × 200 × 0.50 / 10⁶             = $0.0097
          total                                      $0.1367
cached    write   12,840 × 0.10 × 1.25 / 10⁶        = $0.0016
          reads   96 × 12,840 × 0.10 × 0.1 / 10⁶    = $0.0123
          chunks  97 × 250 × 0.10 / 10⁶             = $0.0024
          output                                      $0.0097
          total                                      $0.0261      ratio 0.1367 / 0.0261 ≈ 5.2×
```

Self-check: only the document part gets cheaper; the output costs the same in both. **Caveat, stated plainly:** these token counts use the Groq model's tokenizer as a proxy; Claude's own count differs (UNVERIFIED).

**Key points** (a 3 needs every point):
- [ ] Uncached ≈ $0.1367: the whole document is paid in all 97 calls.
- [ ] Cached ≈ $0.0261: one write at 1.25×, 96 reads at 0.1×.
- [ ] Ratio about 5.2×; the output cost is the same in both.

**For a 4, also:**
- [ ] A self-check or caveat: the prefix is far above Haiku 5.5's 512-token minimum, calls must run in document order within the cache lifetime, and the token count is a proxy for Claude's tokenizer.

**Common wrong answers:**
- [ ] "Cached = 0.1 × uncached = $0.0137": the first write costs 1.25×, and the chunk and output are not discounted.
- [ ] "Caching makes the output cheaper too": only the cached input prefix is discounted.

**If you missed it, reread:** [short §10](../reading/I5_contextual_headers.md#10-llm-written-contexts-and-the-cost-ladder) · [short §11](../reading/I5_contextual_headers.md#11-prompt-caching-cache-keys-and-wrong-contexts) · [lesson #llm](../lessons/I5_contextual_headers.html#llm) · [lesson #cache](../lessons/I5_contextual_headers.html#cache) · book Ch7 p.4–7/11

</details>
<!-- /q -->

<!-- q id=I5-A-03 type=A set=main -->
### I5-A-03 · Application
**Question:** Write the path headers of the p.10 and p.23 "Paris Agreement" chunks, and say which heading levels separate them.

```
title (24 pt)   Understanding Climate Change
p.10            chapter     Chapter 6: Global and Local Climate Action
                section     International Collaboration
                subsection  Paris Agreement
p.23            chapter     Chapter 16: Global Cooperation and Governance
                section     International Agreements
                subsection  Paris Agreement
separator       " › "
```

**Reply template:** `p.10: ____ . p.23: ____ . Separated by the ____ levels.`

<details><summary>Hint 1</summary>

Start from the title and go down one level at a time.

</details>

<details><summary>Hint 2</summary>

Compare the two paths level by level. Which levels are equal?

</details>

<details><summary>Hint 3</summary>

p.10 begins `Understanding Climate Change › Chapter 6: Global and Local Climate Action › …`. Finish it, then write p.23.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
p.10  Understanding Climate Change › Chapter 6: Global and Local Climate Action › International Collaboration › Paris Agreement
p.23  Understanding Climate Change › Chapter 16: Global Cooperation and Governance › International Agreements › Paris Agreement
      same                           different                                       different                  same
```

The title and the leaf are identical; **only the chapter and section levels separate them**. A leaf-only header would give D-002's and D-003's gold chunks the same label.

**Key points** (a 3 needs every point):
- [ ] The p.10 path, in order title › chapter › section › subsection.
- [ ] The p.23 path.
- [ ] Title and leaf are the same; the chapter and section levels separate them.

**For a 4, also:**
- [ ] Notes that leaf names collide on D (11 reused names) and that a path header is about 19 tokens at the median (derived), about 0.11 of a median chunk's mean pool.

**Common wrong answers:**
- [ ] "The leaf 'Paris Agreement' is enough": it is the same on both pages.
- [ ] "The title separates them": the title is the same on every chunk.

**If you missed it, reread:** [short §4](../reading/I5_contextual_headers.md#4-the-path-not-the-leaf) · [lesson #path](../lessons/I5_contextual_headers.html#path) · book Ch7 p.8/11

</details>
<!-- /q -->

<!-- q id=I5-A-04 type=A set=main -->
### I5-A-04 · Application
**Question:** Express Anthropic's 5.7% → 3.7% as an absolute and a relative change, and say whether 50 questions could detect it.

```
06 §9.4, n = 50 paired questions   95% half-width ±0.124; an effect of about 0.18 is needed for 80% power
```

**Reply template:** `absolute ____ points; relative ____%; detectable at n = 50? ____, because ____.`

<details><summary>Hint 1</summary>

Absolute is b − a; relative is (b − a) / a.

</details>

<details><summary>Hint 2</summary>

Put the absolute change on the same scale as 0.18 (points ÷ 100).

</details>

<details><summary>Hint 3</summary>

3.7 − 5.7 = −2.0. Now divide by 5.7.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
absolute   3.7 − 5.7 = −2.0 points
relative   −2.0 / 5.7 = −35.1%
n = 50     about 0.18 (18 points) needed; 0.02 is far inside the ±0.124 half-width → not detectable
```

It is also a different metric: the vendor's 1 − recall@20 at k = 20, not our CE@4.

**Key points** (a 3 needs every point):
- [ ] −2.0 points absolute.
- [ ] −35.1% relative.
- [ ] Not detectable: 2 points is far below the about 18 points needed (±0.124 half-width).

**For a 4, also:**
- [ ] Notes the metric mismatch (1 − recall@20 vs CE@4) and that a null result on 50 questions is not evidence of no effect.

**Common wrong answers:**
- [ ] "35% better, so a large effect": it is relative to a small base.
- [ ] "It is a 35-point change": it is 2 points.

**If you missed it, reread:** [short §12](../reading/I5_contextual_headers.md#12-reading-the-vendor-numbers) · [short §9](../reading/I5_contextual_headers.md#9-measuring-it-on-your-questions) · [lesson #claims](../lessons/I5_contextual_headers.html#claims) · [lesson #measure](../lessons/I5_contextual_headers.html#measure) · book Ch7 p.8–9/11

</details>
<!-- /q -->

<!-- q id=I5-A-05 type=A set=main -->
### I5-A-05 · Application
**Question:** Which header does chunk 68 get under the start rule and under the majority rule, and which one is right for D-003?

```
chunk 68 (p.23, the D-003 gold chunk), top to bottom
  2 lines    the end of the DAC text, under Chapter 15 › Carbon Capture and Utilization › Direct Air Capture (DAC)
  heading    Chapter 16: Global Cooperation and Governance
  heading    International Agreements
  heading    Paris Agreement
  the rest   the Paris Agreement paragraph, ending "Regular reviews and updates of NDCs are essential ..."
D-003        what is essential about countries' NDCs for meeting the Paris Agreement's goals?
```

**Reply template:** `start: ____ . majority: ____ . Right for D-003: ____, because ____.`

<details><summary>Hint 1</summary>

Start rule: which path is in effect at the first character? Majority rule: which path covers most of the characters?

</details>

<details><summary>Hint 2</summary>

Which chapter is D-003's evidence in?

</details>

<details><summary>Hint 3</summary>

The first character is in the DAC text, so the start rule gives the Chapter 15 path. Now the majority.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
start      Understanding Climate Change › Chapter 15: Climate Change and Technology › Carbon Capture and Utilization › Direct Air Capture (DAC)
majority   Understanding Climate Change › Chapter 16: Global Cooperation and Governance › International Agreements › Paris Agreement
```

The **majority rule** is right for D-003: the evidence is the Paris paragraph under Chapter 16. The start rule labels the chunk with carbon capture, the wrong chapter, which pulls it toward DAC questions and away from Paris ones.

**Key points** (a 3 needs every point):
- [ ] Start rule: Chapter 15 › Carbon Capture and Utilization › Direct Air Capture (DAC).
- [ ] Majority rule: Chapter 16 › International Agreements › Paris Agreement.
- [ ] Majority is right for D-003; the start rule gives the wrong chapter for the Paris text.

**For a 4, also:**
- [ ] Adds that neither rule wins everywhere: on chunk 34 the start rule names the referent of "It" (blockchain) and the majority rule does not; the rules disagree on 84 of 97 chunks, so v1.2 pre-registers none, start and majority as arms.

**Common wrong answers:**
- [ ] "A chunk's heading is the one it starts under": here that is the wrong chapter.
- [ ] "So the majority rule is always right": chunk 34 goes the other way.

**If you missed it, reread:** [short §5](../reading/I5_contextual_headers.md#5-which-heading-a-chunk-gets) · [lesson #assign](../lessons/I5_contextual_headers.html#assign) · book Ch7 p.8/11

</details>
<!-- /q -->

<!-- q id=I5-A-06 type=A set=review -->
### I5-A-06 · Application (review)
**Question:** What is the header share s of a 19-token header on a 151-token chunk, and on a 64-token chunk?

```
s = h / (h + c)      h header tokens, c chunk tokens, mean pooling
```

**Reply template:** `151: s = ____ . 64: s = ____ . So ____.`

<details><summary>Hint 1</summary>

Put h = 19 and each c into the formula.

</details>

<details><summary>Hint 2</summary>

The denominator is h + c, not c alone.

</details>

<details><summary>Hint 3</summary>

19 / (19 + 151) = 19 / 170. Now 19 / (19 + 64).

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
c = 151   s = 19 / 170 = 0.112
c = 64    s = 19 / 83  = 0.229
```

The same header takes about twice the share of the short chunk's mean pool, so the short chunk's vector moves about twice as far toward the header. Self-check: s is below 1 and grows as c shrinks.

**Key points** (a 3 needs every point):
- [ ] s = 0.112 on the 151-token chunk.
- [ ] s = 0.229 on the 64-token chunk.
- [ ] The short chunk is pulled about twice as much toward the header.

**For a 4, also:**
- [ ] Adds the toy: at s = 0.112 the chunk vector barely moves (cos 0.9897 with its bare self), while a large shared header pulls different chunks together (the header magnet).

**Common wrong answers:**
- [ ] "s = 19 / 151 = 0.126": the denominator is h + c.
- [ ] "The header is the same length, so its effect is the same": the share depends on c.

**If you missed it, reread:** [short §7](../reading/I5_contextual_headers.md#7-dilution-and-the-header-magnet) · [lesson #dilute](../lessons/I5_contextual_headers.html#dilute) · book Ch7 p.7/11

</details>
<!-- /q -->

<!-- q id=I5-T-01 type=T set=main -->
### I5-T-01 · Transfer
**Question:** Headers raised CE@4 on your near-duplicate items but lowered it on your factual-single-span items: what do you check first?

**Reply template:** `First ____. Then, for the items that got worse, ____.`

<details><summary>Hint 1</summary>

How many items are in each group, and how many of them flipped?

</details>

<details><summary>Hint 2</summary>

Then read the items that got worse: how long is the gold chunk, and does it share a header with a distractor?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** First, whether the split is real: the n of each category and the discordant pairs. With about 50 questions the 95% half-width is ±0.124, so a few flips in a small group can be chance, and the groups overlap (D-002 and D-003 are factual-single-span items tagged near-duplicate). Then read the items that got worse:
1. **Dilution:** a short gold chunk with a high header share (0.229 at 400 characters, against 0.112 at the median).
2. **The header magnet:** the gold chunk and a distractor share a header, or the distractor's header matches the question better.
3. **A wrong-rule header:** chunk 68 under the start rule is labelled Chapter 15.
4. **Truncation:** 0 of 97 path headers go over 256, so it is unlikely here.

**Key points** (a 3 needs every point):
- [ ] First check the n per category and the discordant pairs: is the split beyond noise?
- [ ] Then read the lost items for dilution (a short chunk, a high s).
- [ ] And for a shared or wrong header (the magnet, or a start-rule error like chunk 68).

**For a 4, also:**
- [ ] Names the label-free check, the gold-vs-distractor margin per pair from your own MiniLM run, and a decision rule: report both groups with their n, and do not adopt headers on a gain the paired test cannot separate from noise.

**Common wrong answers:**
- [ ] "Headers help near-duplicates, so keep them": first check whether the split is noise.
- [ ] "Drop the factual items from the eval": that hides the cost.

**If you missed it, reread:** [short §7](../reading/I5_contextual_headers.md#7-dilution-and-the-header-magnet) · [short §9](../reading/I5_contextual_headers.md#9-measuring-it-on-your-questions) · [lesson #dilute](../lessons/I5_contextual_headers.html#dilute) · [lesson #measure](../lessons/I5_contextual_headers.html#measure) · book Ch7 p.8–9/11

</details>
<!-- /q -->

<!-- q id=I5-T-02 type=T set=main -->
### I5-T-02 · Transfer
**Question:** After a one-line edit on page 12, the LLM contexts for the other chunks came back from the cache unchanged: what was wrong with the cache key?

**Reply template:** `The key covered ____. A context depends on ____, so ____. The key should hold ____.`

<details><summary>Hint 1</summary>

The edit changed the text of one chunk only. Which keys changed?

</details>

<details><summary>Hint 2</summary>

What did each prompt contain besides its own chunk?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The key hashed the chunk text only. The edit changed one chunk (33), so the other 96 keys stayed the same, and their contexts came back from the cache although the prompts that wrote them held the old document. A context is a function of the whole document, so the key must cover the prompt version, the full document text and the chunk text (plus the model and its settings).

```
key = hash(chunk text)                            96 of 97 served from cache: stale
key = hash(prompt version + document + chunk)      0 of 97 served: all rebuilt
```

**Key points** (a 3 needs every point):
- [ ] The key covered the chunk text only.
- [ ] A context depends on the whole document, so an edit anywhere makes all of its contexts stale (96 of 97 served stale).
- [ ] Fix: put the prompt version, the document text (or its hash) and the chunk text in the key.

**For a 4, also:**
- [ ] Stores `doc_text_sha256` with each context and rebuilds a document's contexts when it changes; checked on D: with the full key, 0 of 97 are served from cache.

**Common wrong answers:**
- [ ] "Only chunk 33 changed, so only its context needed rebuilding": the other contexts were written from the old document.
- [ ] "Clear the cache by hand after each edit": it works once; the key should make it automatic.

**If you missed it, reread:** [short §11](../reading/I5_contextual_headers.md#11-prompt-caching-cache-keys-and-wrong-contexts) · [lesson #cache](../lessons/I5_contextual_headers.html#cache) · book Ch7 p.4–7/11

</details>
<!-- /q -->

<!-- q id=I5-T-03 type=T set=main -->
### I5-T-03 · Transfer
**Question:** Your first Groq whole-document context call fails with "request too large / TPM": why, and what are two fixes?

**Reply template:** `It fails because one request is ____ tokens against a limit of ____. Fix 1: ____. Fix 2: ____.`

<details><summary>Hint 1</summary>

How many tokens does one whole-document prompt hold on Corpus D?

</details>

<details><summary>Hint 2</summary>

Compare that with the free tier's tokens-per-minute limit. Would waiting help?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** One request holds the whole document plus the chunk and instruction: 12,840 + 250 = 13,090 tokens. Groq's free tier allows 8,000 tokens per minute, so a single request is larger than a whole minute's budget and can never pass; retrying or waiting does not help. Even if it fitted, 97 calls would need 1,269,730 input tokens against 200K per day. Two fixes:
1. Send a chapter window instead (rung 2): median 855 input tokens per call, 106,743 tokens in all, $0.0124, at least 13.3 minutes at 8K TPM.
2. Run the whole-document arm on Haiku 5.5 with prompt caching ($0.0261 for D), or on a paid Groq tier ($0.0542).

**Key points** (a 3 needs every point):
- [ ] One request (13,090 tokens) is bigger than the 8,000 tokens-per-minute limit, so it can never pass.
- [ ] Retrying or waiting does not help: it is the size of a single request.
- [ ] Two fixes, such as a chapter window on Groq (rung 2) and Haiku 5.5 with caching or a paid tier.

**For a 4, also:**
- [ ] Adds the daily limit (97 calls = 1,269,730 input tokens against 200K per day), the rung 2 numbers, and that Groq's limits are UNVERIFIED (check them on your plan).

**Common wrong answers:**
- [ ] "Add exponential backoff": the request is too large, not too early.
- [ ] "Spread the 97 calls over a few hours": each single request is still too large.

**If you missed it, reread:** [short §10](../reading/I5_contextual_headers.md#10-llm-written-contexts-and-the-cost-ladder) · [lesson #llm](../lessons/I5_contextual_headers.html#llm) · book Ch7 p.4–7/11

</details>
<!-- /q -->

<!-- q id=I5-T-04 type=T set=main -->
### I5-T-04 · Transfer
**Question:** A teammate wrote the eval questions by reading the section titles, and headers gave +20 points: what is suspicious, and how do you check it?

**Reply template:** `Suspicious: ____. Check: ____. Then ____.`

<details><summary>Hint 1</summary>

Where do the question's words come from, and where do they end up in `embed_text`?

</details>

<details><summary>Hint 2</summary>

Compare each question's words with its gold chunk's header and with its gold chunk's text.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** **Header-query leakage.** Questions written from the titles borrow the headings' words. The header puts those words into `embed_text`, while the chunk text may not contain them, so the header can "win" by echoing the question rather than by restoring context. Check it: for each question, list the content words that are in its gold chunk's header but not in its text. Then re-test on questions written from the evidence spans, and report both sets with their n and discordant pairs.

```
draft seeds D-001…D-008 (written from spans)   no question word is in the gold header but not in the gold text
```

**Key points** (a 3 needs every point):
- [ ] Suspect header-query leakage: question words come from headings that the header adds but the chunk text lacks.
- [ ] Check: per question, the content words in the gold header but not in the gold text.
- [ ] Re-test on questions written from the evidence spans, not from the titles.

**For a 4, also:**
- [ ] Notes that the span-written draft seeds show no leaked word, and that real users do not phrase questions from section titles; the upstream demo's "Nike" query has the same flaw.

**Common wrong answers:**
- [ ] "+20 points is above the noise, so headers work": the size may be real, but the questions are biased toward the headers.
- [ ] "Headers simply give better context": they may only be echoing the question.

**If you missed it, reread:** [short §9](../reading/I5_contextual_headers.md#9-measuring-it-on-your-questions) · [lesson #measure](../lessons/I5_contextual_headers.html#measure) · book Ch7 p.8–9/11

</details>
<!-- /q -->

<!-- q id=I5-R-07 type=R set=interview source=AIQ-04-Q17 -->
### I5-R-07 · Interview (Recall)
**Question:** "Explain contextual retrieval. What problem does it solve, and how does late chunking relate?"
*From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md` (question 17), Copyright (c) 2026 Om, MIT License.*

**Reply template:** `The problem is ____. Contextual retrieval ____. Late chunking ____. On one PDF, the cheap header ____.`

<details><summary>Hint 1</summary>

Start from what a chunk loses when it is cut out, then compare an LLM per chunk with an embedder that reads the whole document.

</details>

<details><summary>Hint 2</summary>

If someone says "always prepend the document title and the heading path", ask: on a one-document corpus, how many distinct titles are there? And which heading does a chunk that spans two chapters get?

</details>

<details><summary>Show answer (write yours first)</summary>

> **The repo's answer (excerpt, verbatim).** *From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md`, Copyright (c) 2026 Om, MIT License:*
>
> "Both attack the same disease: **chunks lose their document context when isolated**. A chunk saying "The company's revenue grew 3% over the previous quarter" is unretrievable for "ACME Q2 2023 revenue growth" - nothing in the chunk says ACME or Q2. Pronouns, definite references ("the merger", "this policy"), and section-dependent meaning all break when a chunk is embedded alone."
>
> "**Contextual retrieval** (the term popularized by Anthropic's 2024 write-up) fixes this at ingest: for each chunk, an LLM is given the full document plus the chunk and generates a short situating blurb - "This chunk is from ACME Corp's Q2 2023 SEC filing, discussing quarterly revenue growth" - which is prepended to the chunk before embedding *and* before BM25 indexing (contextual embeddings + contextual BM25). Anthropic reported the combination cut top-20 retrieval failure rate by ~49%, and ~67% with reranking on top. The cost is one LLM call per chunk at index time; prompt caching makes it cheap because the full document is a shared cached prefix across all of its chunks' calls. It's a pure index-time cost - query latency is untouched."
>
> "**Late chunking** achieves related contextualization without an LLM: embed the *entire document* through a long-context embedding model, then mean-pool the contextualized token embeddings over each chunk's span. Because attention ran over the whole document, each chunk's vector already "knows" that "the company" is ACME. It requires a long-context embedder and only helps the dense side (BM25 still sees the bare chunk text), but it's cheaper than per-chunk LLM calls."
>
> "When to bother: corpora with heavy cross-references and entity ambiguity (filings, contracts, wikis) see big gains; self-contained chunks (FAQ entries, product descriptions) see little. A cheap approximation that captures much of the value: prepend document title + heading path to every chunk - do that unconditionally."

**Our check of that answer:** the diagnosis, the method, the caching argument and the late-chunking contrast match I5 §1, §10 and §11. Three things to add, from Corpus D:
1. **"Unconditionally" needs the information test.** On a one-document corpus the title part of "title + heading path" is the same on every chunk: **1 distinct title header of 97**. It carries no ranking information; only the path does (97 distinct headers under the start rule, 96 under the majority rule).
2. **"Heading path" needs a rule, and the rule matters.** The start rule and the majority rule disagree on 84 of 97 chunks. On **chunk 68**, the D-003 gold chunk, the start rule labels the Paris text Chapter 15 › Carbon Capture and Utilization › Direct Air Capture (DAC), while the majority rule gives Chapter 16 › International Agreements › Paris Agreement. On chunk 34 the start rule is the one that wins, so test both.
3. **"~49%" is relative.** It is 1 − recall@20 going from 5.7% to 2.9%, 2.8 points absolute, on the vendor's data. And "cheap" assumes caching: on Groq's free tier one whole-document request (13,090 tokens) exceeds the 8,000 tokens-per-minute limit.

**Model answer:** The problem: a chunk cut out of a document loses its context, both where it sits (chapter, section) and what its pronouns refer to, so a question that names the subject cannot match it. Contextual retrieval fixes this at index time: an LLM reads the whole document plus one chunk and writes a short context, which is prepended to the text that is embedded (and, optionally, BM25-indexed); the stored chunk text and offsets stay unchanged. It costs one call per chunk, each carrying the document, so it is affordable only with prompt caching (document first, chunks in order). Late chunking gets a similar effect with no LLM: a long-context embedder reads the whole document and pools token vectors per chunk span; it helps only the dense side and needs a long window (MiniLM's 256 tokens are too few). The cheap alternative is a deterministic heading-path header, but only the parts that differ between chunks help: on a one-document corpus the title is constant, and the heading must be assigned by a tested rule (start vs majority). Measure the effect with your own metric (CE@4) on questions written from the evidence, not from the headings.

**Key points** (a 3 needs every point):
- [ ] The problem: chunks lose their document context (location and referents) when isolated.
- [ ] Contextual retrieval: an LLM writes a per-chunk context from the whole document, prepended before embedding (and BM25); affordable through prompt caching.
- [ ] Late chunking: a long-context embedder over the whole document, pooled per chunk span; no LLM, dense side only.
- [ ] A header helps only where it varies: on one document the title is constant (1 distinct of 97), so only the heading path can help.

**For a 4, also:**
- [ ] Names the heading-rule problem with evidence (chunk 68: the start rule gives Chapter 15, the majority rule Chapter 16 › Paris Agreement) and turns "~49%" into 2.8 points absolute on 1 − recall@20.

**Common wrong answers:**
- [ ] "Always prepend the document title, it is free": on one document it is the same on every chunk and adds no information.
- [ ] "Late chunking also fixes BM25": it changes only the dense vectors.

**If you missed it, reread:** [short §1](../reading/I5_contextual_headers.md#1-a-chunk-loses-its-context) · [short §6](../reading/I5_contextual_headers.md#6-the-information-test-a-constant-title-adds-nothing) · [short §10](../reading/I5_contextual_headers.md#10-llm-written-contexts-and-the-cost-ladder) · [lesson #anon](../lessons/I5_contextual_headers.html#anon) · [lesson #info](../lessons/I5_contextual_headers.html#info) · [lesson #llm](../lessons/I5_contextual_headers.html#llm) · book Ch7 p.1–2/11 and p.8/11

</details>
<!-- /q -->
