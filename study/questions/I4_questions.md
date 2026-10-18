<!-- kit:questions concept=I4 version=1 -->
# I4 questions: proposition chunking, source pointers, alignment, the quality filter and the cost

**How to use:** write your answer and a confidence (1–3) first. Then open the answer and tick the key points you really wrote.

**Where the numbers come from:** `sources/verification/I4/i4_kit_measure.py` on the climate PDF ([I4_FACTS](../../sources/verification/I4/I4_FACTS.md); [kit run K1–K12](../../sources/verification/I4/out_i4_kit_measure.txt)). No LLM has written a proposition for this course yet: the 40 propositions used here (`i4_tutor_props.jsonl`) were **hand-written by the tutor**, and the six `x-…` mistakes were planted on purpose. Every ranked list is a **made-up order**, never model output. Token sizes per call are **ASSUMED**; Wilson intervals are formula outputs, because no hand labels exist yet. The draft questions (D-001…D-010) are LLM-drafted and not yet checked by you. No API was called to write this file.

<!-- q id=I4-PRE-01 type=R set=pre -->
### I4-PRE-01 · Recall (before reading)
**Question:** Why can one vector for a chunk that holds several facts match a one-fact question badly?

**Reply template:** `The chunk's vector is ____ of its facts, so its similarity to a one-fact question ____.`

<details><summary>Hint 1</summary>

Picture each fact as its own arrow. Which single arrow does the whole chunk get?

</details>

<details><summary>Hint 2</summary>

In a toy, make the facts point at right angles to each other and let the chunk be their normalised mean. Compute the cosine with one fact for n = 1 and n = 4.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The embedder gives the chunk one vector, a blend of everything in it, so it points somewhere between its facts and close to none of them. A question about one fact then matches it weakly, and a short text about that one fact can outrank it. In the toy (made-up facts at right angles; K8) the cosine falls as 1/√n:

```
n facts   1      2      3      4      8
cos       1.000  0.707  0.577  0.500  0.354
a one-fact distractor with cos 0.60 beats the right chunk from n = 3
```

Chunk 27 of v0 mixes the UNFCCC, the Kyoto Protocol, the Paris goals, NDCs and carbon pricing, and it is the chunk that answers D-002. Real embeddings are not at right angles, so the toy shows the direction of the effect (dilution), not its size.

**Key points** (a 3 needs every point):
- [ ] The chunk's single vector is a blend (mean) of all its facts.
- [ ] So its similarity to any one fact drops as the number of facts grows (toy: 1/√n, 0.577 at n = 3).

**For a 4, also:**
- [ ] Says a focused distractor can then win (0.60 > 0.577), and that the toy shows a direction, not the size on real embeddings.

**Common wrong answers:**
- [ ] "The chunk is too long, so the embedder cuts it off": that is truncation (P4), a different problem; here every word is read.
- [ ] "More facts make the chunk match better, because it covers more": it matches more questions, but each one more weakly.

**If you missed it, reread:** [short §1](../reading/I4_proposition_chunking.md#1-one-vector-for-many-facts) · [lesson step 1](../lessons/I4_propositions.html#dilution) · book Ch4 p.10–11/15

</details>
<!-- /q -->

<!-- q id=I4-R-01 type=R set=main -->
### I4-R-01 · Recall
**Question:** What five properties must a proposition have, and which three words does Dense X use for them?

**Reply template:** `1 ____ 2 ____ 3 ____ 4 ____ 5 ____; Dense X: ____, ____, ____.`

<details><summary>Hint 1</summary>

A proposition sits in the index with no page around it. What must it carry to make sense alone, and how much may it say?

</details>

<details><summary>Hint 2</summary>

Two rules limit how much it says (facts, subjects), two make it readable alone (context, pronouns), and one protects precision (numbers and small words).

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The five rules of upstream's prompt (cell 12): it expresses **a single fact**; it is **understandable without context**; it uses **full names, not pronouns**; it **keeps the relevant dates and qualifiers**; and it has **one subject–predicate relationship**. Dense X Retrieval's version: **distinct, minimal, self-contained**. Sentence 10:7 becomes three (tutor-written, K4):

```
p10-07  The Paris Agreement was adopted in 2015.
p10-08  The Paris Agreement aims to limit global warming to well below 2 degrees Celsius above pre-industrial levels.
p10-09  Efforts under the Paris Agreement aim to limit the increase in global warming to 1.5 degrees Celsius.
```

**Key points** (a 3 needs every point):
- [ ] One fact, with one subject–predicate relationship.
- [ ] Understandable alone, with full names instead of pronouns.
- [ ] Dates and qualifiers kept ("well below", "1.5").
- [ ] Dense X: distinct, minimal, self-contained.

**For a 4, also:**
- [ ] Shows it on a sentence (10:7 → 3 propositions), or says that a proposition is a rewrite whose text is in no page of the document.

**Common wrong answers:**
- [ ] "A proposition is just a sentence of the document": it is rewritten; 10:7 gave three, and none of them is a substring of the page.
- [ ] "Shorter is better, so drop the small words": "below 2" for "well below 2" changes the fact (planted mistake x-03).

**If you missed it, reread:** [short §2](../reading/I4_proposition_chunking.md#2-what-a-proposition-is) · [lesson step 2](../lessons/I4_propositions.html#proposition) · book Ch4 p.5–6/15

</details>
<!-- /q -->

<!-- q id=I4-R-02 type=R set=main -->
### I4-R-02 · Recall
**Question:** Why can a proposition not be scored with the CE@k span rule directly, and what does it store so that it can be?

**Reply template:** `Because its text ____. It stores ____, from which code computes ____ and ____.`

<details><summary>Hint 1</summary>

The span rule compares character spans of the document. Where in the document is the text "The Paris Agreement was adopted in 2015."?

</details>

<details><summary>Hint 2</summary>

What does the model return besides the text? How do unit ids become character offsets?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** CE@k and any_overlap compare the character span of each retrieved unit with the gold segments, and the course's `Chunk` type requires `doc_text[char_start:char_end] == text` (06 §2.3). A proposition is a rewrite, so its text is not a substring of the document: it has no span of its own and cannot be a `Chunk`. It stores **source_ids**, the ids of the units it came from. Code turns them into **span(p) = [min aᵢ, max bᵢ)** over those units (all on one page), and into its **parent** chunk(s) by containment:

```
p10-07  source_ids [10:7]   span [20993, 21180)   parent 27
p10-12  source_ids [10:11]  span [21331, 21479)   parents 27, 28   (6 of 40 have two parents: the 200-char overlap)
```

So it is an **IndexUnit**: the embedded text (the proposition) differs from the evidence span.

**Key points** (a 3 needs every point):
- [ ] The proposition's text is not a substring of the document, so it has no span and breaks the `Chunk` invariant.
- [ ] It stores source_ids (the units it came from).
- [ ] Code computes span(p) from the units' offsets, and the parent chunk(s) by containment.

**For a 4, also:**
- [ ] Names the two uses: the span for scoring the propositions (arm (b)), the parent for returning chunks (arm (a)); embed text ≠ evidence span (IndexUnit).

**Common wrong answers:**
- [ ] "Search for the proposition's text in the page to find its span": a rewrite is not in the page; matching it back is a guess.
- [ ] "Score it by the page it was generated from": a page almost always overlaps gold, so that measures page routing only (scoring (c), rejected).

**If you missed it, reread:** [short §6](../reading/I4_proposition_chunking.md#6-every-proposition-points-back-to-its-source) · [short §9](../reading/I4_proposition_chunking.md#9-three-ways-to-score-propositions) · [lesson step 6](../lessons/I4_propositions.html#anchor) · book Ch4 p.9/15

</details>
<!-- /q -->

<!-- q id=I4-R-03 type=R set=main -->
### I4-R-03 · Recall (MC-006 check item)
**Question:** Why is the 7/10 quality grade a filter and not a measurement of faithfulness?

**Reply template:** `It decides ____, but nobody has checked ____. To know how good it is, compare it with ____: ____ and ____.`

<details><summary>Hint 1</summary>

What happens to a proposition that scores 6? What does the grade change in the pipeline?

</details>

<details><summary>Hint 2</summary>

Who checks the grader? Look at its examples and at which model does the grading.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The grade runs at index time and decides **what enters the index**, so it is a pipeline component (an index-time filter, D-10), not an evaluation. Its threshold of 7 is fixed and uncalibrated, and an LLM is trusted to judge an LLM's output: the MC-006 pattern. Upstream's grader (cells 15–16, K2) makes it worse:

```
grader examples: 5, all 10/10/10/10 (no failing example)
the same model generates and grades; label typos; human turn '{proposition}, {original_text}' with no labels
saved output: 31 generated, 2 rejected (#17 completeness 6, #31 conciseness 6), 29 embedded
```

"2 of 31 rejected" says how strict the filter is, not how faithful the 29 are. To know what it does, compare its keep/drop with **your hand labels**: keep-good = kept ∧ good / good, catch-bad = dropped ∧ bad / bad. Neither is measured yet: no labels exist.

**Key points** (a 3 needs every point):
- [ ] It is an index-time filter: it decides what gets indexed and measures nothing (D-10).
- [ ] The 7 is uncalibrated, and an LLM grades LLM output (upstream: the same model, examples all 10/10/10/10) (MC-006).
- [ ] Its quality is known only against hand labels: keep-good and catch-bad.

**For a 4, also:**
- [ ] Gives both formulas with their n, and says faithfulness itself is measured by a person on a sample (with a Wilson interval).

**Common wrong answers:**
- [ ] "29 of 31 passed, so the propositions are faithful": the pass rate of an uncalibrated filter is not a faithfulness rate (MC-006).
- [ ] "Raise the threshold to 9 and it becomes safe": a stricter uncalibrated threshold is still uncalibrated.

**If you missed it, reread:** [short §8](../reading/I4_proposition_chunking.md#8-the-quality-grade-is-a-filter) · [lesson step 8](../lessons/I4_propositions.html#grade) · book Ch4 p.7–9/15

</details>
<!-- /q -->

<!-- q id=I4-R-04 type=R set=main -->
### I4-R-04 · Recall
**Question:** What does decontextualisation replace, where must the new name come from, and how can code check it?

**Reply template:** `It replaces ____ with ____. The name must come from ____. Code checks ____ and ____.`

<details><summary>Hint 1</summary>

Read sentence 10:4 alone: "It provides a framework for negotiating specific protocols and agreements…". What is missing?

</details>

<details><summary>Hint 2</summary>

Two checks: one on the names the proposition says it brought in (`resolved`), one on its first word.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** It replaces **pronouns and vague references** ("It", "These meetings") with the **full name the page used earlier**, and the proposition records that name in `resolved`. The name must come from the same page, before the sentence, not from the model's world knowledge. Code checks (a) that each resolved name's words occur in the page text before the first source unit, and (b) that no proposition starts with a pronoun (It, They, This, These…):

```
[10:4]  It provides a framework ...     → p10-03 The UNFCCC provides a framework ...   resolved UNFCCC (from 10:2, 10:3)
[29:14] These meetings play ...         → p29-04 COP meetings play ...                 resolved COP
tutor set: 15 of 40 use a resolved name, all found earlier on the page; pronoun-initial: 0   (planted x-05 "It provides…": caught)
```

**Key points** (a 3 needs every point):
- [ ] Replaces pronouns and vague references with the full name.
- [ ] The name comes from earlier on the same page, not from world knowledge.
- [ ] Check 1: the resolved name occurs in the page before the source sentence.
- [ ] Check 2: no proposition starts with a pronoun.

**For a 4, also:**
- [ ] Names the limit: the checks prove the name is on the page, not that it is the right referent ("The Paris Agreement provides a framework…", x-04, passes every code check), so a person must read a sample.

**Common wrong answers:**
- [ ] "The model may use what it knows to name the subject": then the name is unsupported by the page (upstream's "astronaut").
- [ ] "Any name that is on the page is fine": it must be the correct referent (x-04 names the wrong treaty).

**If you missed it, reread:** [short §3](../reading/I4_proposition_chunking.md#3-decontextualisation-names-instead-of-pronouns) · [short §7](../reading/I4_proposition_chunking.md#7-checking-the-rewrite-alignment-and-its-blind-spots) · [lesson step 3](../lessons/I4_propositions.html#decontext) · book Ch4 p.5–6/15

</details>
<!-- /q -->

<!-- q id=I4-R-05 type=R set=main -->
### I4-R-05 · Recall
**Question:** What kind of mistake does align(p) catch, and which two kinds can it not catch?

**Reply template:** `It catches ____ (example: ____). It misses ____ and ____, because ____.`

<details><summary>Hint 1</summary>

align counts the proposition's words that are in its sources. What happens to a source word that the proposition leaves out?

</details>

<details><summary>Hint 2</summary>

Look at planted mistakes x-03 and x-04. Which of their words are missing from 10:7 or 10:4?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** align(p) = |W(p) ∩ (W(sources) ∪ W(resolved names))| / |W(p)|, with W the content-word stems. It catches **added words**: a word in the proposition that is in neither its sources nor its resolved names. It cannot catch a **dropped qualifier** (taking a word out adds nothing unsupported) or a **wrong referent** (every word is still on the page):

```
upstream "Neil Armstrong was an astronaut."          0.667   added: astronaut
x-01 "...signed in Paris by 196 countries."          0.400   added
x-02 "...adopted in 2016."                           0.750   wrong year
x-03 "below 2" for "well below 2"                    1.000   not caught
x-04 "The Paris Agreement provides a framework..."   1.000   not caught (it is the UNFCCC)
```

So list **every** proposition with align < 1 for reading, and hand-label a sample for the rest.

**Key points** (a 3 needs every point):
- [ ] It catches added content words (unsupported by the sources and resolved names).
- [ ] It misses a dropped qualifier (x-03, 1.000).
- [ ] It misses a wrong referent (x-04, 1.000), because all its words are in the source.

**For a 4, also:**
- [ ] The threshold: align < 0.5 would miss the astronaut (0.667) and the wrong year (0.750), so list every align < 1, plus a hand-labelled sample with a Wilson interval.

**Common wrong answers:**
- [ ] "align = 1.000 means the proposition is faithful": x-03 and x-04 score 1.000 and are wrong.
- [ ] "Flag everything below 0.5": that misses 0.667 and 0.750.

**If you missed it, reread:** [short §7](../reading/I4_proposition_chunking.md#7-checking-the-rewrite-alignment-and-its-blind-spots) · [lesson step 7](../lessons/I4_propositions.html#align) · book Ch4 p.7–9/15

</details>
<!-- /q -->

<!-- q id=I4-R-06 type=R set=review -->
### I4-R-06 · Recall (review)
**Question:** Why can a MultiVectorRetriever-style search at k = 4 return fewer than 4 parent chunks, and why does that matter when you compare it with a chunk arm?

**Reply template:** `Because ____. In the D-002 list, 4 propositions gave ____ parents. For the comparison, ____.`

<details><summary>Hint 1</summary>

Several propositions come from the same chunk. What does keeping "the first occurrence of each parent" do to them?

</details>

<details><summary>Hint 2</summary>

Compare how much text each arm hands the generator when both say "k = 4".

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The retriever searches the **child** vectors (propositions) with the store's own k, maps each hit to its parent, and keeps the first occurrence of each parent (langchain-classic `multi_vector.py`). So **k child hits give at most k parents, often fewer**:

```
D-002 made-up order (K7): 4 propositions → parents [27, 68] → 2 distinct parents
upstream cells 20 and 32 (K12): 4 proposition hits → 1 distinct parent (chunk 3)
```

It matters because "k = 4" then hands the generator fewer chunks and fewer tokens than the chunk arm's k = 4, so the two arms are not compared on the same context. Report the number of parents returned, and compare at a fixed k **and** at an equal token budget (or keep retrieving children until there are k distinct parents: dedup before the cut).

**Key points** (a 3 needs every point):
- [ ] Parents are deduplicated, so k children give at most k parents.
- [ ] Example: D-002's top 4 propositions → 2 parents (upstream: 4 hits → 1 parent).
- [ ] The arms then get different amounts of context, so compare at an equal token budget (or dedup before the cut) and report the parents returned.

**For a 4, also:**
- [ ] Names the default: `search_kwargs` defaults to `{}`, so the vector store's own k (4 for most stores) counts children, not parents.

**Common wrong answers:**
- [ ] "k = 4 always means 4 chunks": k counts the child hits.
- [ ] "Fewer parents is fine, it is just more precise": the arms then differ in context size, so the comparison is not fair.

**If you missed it, reread:** [short §9](../reading/I4_proposition_chunking.md#9-three-ways-to-score-propositions) · [short §12](../reading/I4_proposition_chunking.md#12-proposition-chunking-in-your-project) · [lesson step 9](../lessons/I4_propositions.html#score) · book Ch4 p.9–10/15

</details>
<!-- /q -->

<!-- q id=I4-R-07 type=R set=interview source=AIQ-04-Q4 -->
### I4-R-07 · Interview (Recall)
**Question:** "What chunking strategies do you know, and how do you pick one?"
*From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md` (question 4), Copyright (c) 2026 Om, MIT License.*

**Reply template:** `Strategies: ____. I pick by ____. Propositions add ____, at the cost of ____.`

<details><summary>Hint 1</summary>

Go from the simplest cut to the most expensive one. Which of them needs an LLM call at index time?

</details>

<details><summary>Hint 2</summary>

For each strategy, say when it is the right one. Then say how you would decide between two of them on your own data.

</details>

<details><summary>Show answer (write yours first)</summary>

> **The repo's answer (verbatim).** *From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md`, Copyright (c) 2026 Om, MIT License:*
>
> From simplest to most sophisticated:
>
> - **Fixed-size**: cut every N tokens with overlap. Trivial to implement, ignores meaning - splits sentences and tables mid-thought. Acceptable baseline, rarely the end state.
> - **Recursive**: try splitting on big separators first (paragraphs), fall back to sentences, then tokens, until chunks fit the size limit. Respects natural boundaries; the sane default (LangChain's `RecursiveCharacterTextSplitter` popularized it).
> - **Structure-aware**: split along document structure - markdown headers, HTML sections, code functions - and attach the heading path ("Handbook > Benefits > Parental leave") to each chunk as context. Best choice whenever structure exists; the heading path alone fixes many retrieval misses.
> - **Semantic**: embed sentences, split where cosine similarity between adjacent sentences drops below a threshold. Conceptually appealing; in practice gains are marginal over recursive+structure-aware and it adds embedding cost at ingest.
> - **Late chunking**: embed the *entire* document with a long-context embedding model, then mean-pool token embeddings per chunk span afterward. Each chunk's vector is contextualized by the whole document - resolves pronouns and dangling references without an LLM call per chunk.
>
> Selection logic: use structure-aware when documents have structure (most do); recursive as fallback; consider contextual enrichment (prepending an LLM-generated situating sentence) or late chunking when chunks are ambiguous out of context. Also decouple the **retrieval unit from the generation unit**: retrieve precise small chunks but hand the LLM the surrounding parent section ("small-to-big" / parent-document retrieval) - small vectors match precisely, big context reads coherently.
>
> Chunking is set-and-forget only until quality plateaus; it's the first thing to revisit when recall@k is bad, before touching the embedding model.
>
> **Follow-ups:** How would you chunk source code differently from prose? What breaks when you chunk a table row-by-row? How do you A/B test two chunking strategies?

**Our check of that answer:** the list and the selection logic are sound, and "decouple the retrieval unit from the generation unit" is exactly how propositions are used. It leaves out proposition chunking, the one strategy that rewrites the text. "Gains are marginal" for semantic chunking carries no source in the answer; treat it as a claim to measure on your data.

**Model answer:** From cheap to expensive: **fixed-size** (a baseline), **recursive** (the default: paragraphs, then sentences, then words), **structure-aware** (split by headings and attach the heading path, best when structure exists), **semantic** (split where adjacent sentences stop being similar), and context fixes for ambiguous chunks (a generated situating header, or late chunking). **Proposition chunking** goes one step further: an LLM rewrites each page into short, self-contained facts, with pronouns replaced by names (decontextualisation), and you index those and return the parent chunk (small-to-big). It has three costs. (1) Index-time LLM calls: on our 33-page corpus, 66 calls with batched grading, 1,433 with per-proposition grading. (2) Each proposition must keep `source_ids` so it can be scored against span gold and mapped to its parent. (3) Its faithfulness must be checked by hand, because a rewrite can add or distort a fact. Atomic facts also lose relations, so contrast and synthesis questions can get worse. I pick by measuring on my own labelled questions: same k and an equal token budget, retrieval metrics per question type, with the parents actually returned.

**Key points** (a 3 needs every point):
- [ ] Names at least three strategies, each with when it fits (fixed, recursive, structure-aware, semantic, late chunking or contextual headers).
- [ ] Adds propositions: an LLM rewrites text into atomic, decontextualised facts that are indexed, and the parent chunk is returned.
- [ ] Gives the proposition costs: index-time calls (66 batched vs 1,433 per proposition here), source pointers, a hand faithfulness check.
- [ ] Picks by measuring on own labelled questions at the same k and an equal token budget.

**For a 4, also:**
- [ ] Says when not to use propositions: compare or synthesis questions (relations lost) and documents that change often (re-index cost).

**Common wrong answers:**
- [ ] "Semantic chunking is the most advanced, so it is the best": the repo's own answer calls its gains marginal; only your measurement decides.
- [ ] "Propositions are just very small chunks": they are rewritten text, so they need source pointers and a faithfulness check that a cut never needs.

**If you missed it, reread:** [short §2](../reading/I4_proposition_chunking.md#2-what-a-proposition-is) · [short §6](../reading/I4_proposition_chunking.md#6-every-proposition-points-back-to-its-source) · [short §11](../reading/I4_proposition_chunking.md#11-what-it-costs) · [lesson step 2](../lessons/I4_propositions.html#proposition) · [lesson step 11](../lessons/I4_propositions.html#cost) · book Ch4 p.10–11/15

</details>
<!-- /q -->

<!-- q id=I4-A-01 type=A set=main -->
### I4-A-01 · Application
**Question:** Write the propositions for page 29's "Monitoring and Enforcement" section, with the source_ids of each.

```
[29:6] (heading) Monitoring and Enforcement
[29:7] Ensuring compliance with climate policies requires robust monitoring and enforcement mechanisms.
[29:8] This includes tracking emissions, verifying data, and imposing penalties for non-compliance.
[29:9] Transparent reporting and accountability are essential for maintaining public trust and achieving policy objectives.
```

**Reply template:** one line per proposition: `text | source_ids | resolved names`

<details><summary>Hint 1</summary>

Count the facts in each sentence. A list ("tracking…, verifying…, and imposing…") hides several, and so does "A and B".

</details>

<details><summary>Hint 2</summary>

29:8 starts with "This". What does it refer to, and where on the page is that name written?

</details>

<details><summary>Hint 3</summary>

29:7 gives "Ensuring compliance with climate policies requires robust monitoring mechanisms." with source_ids [29:7]. Write the enforcement half, then replace "This" in 29:8.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** One possible set (others are fine if each line holds one fact from the page):

```
Ensuring compliance with climate policies requires robust monitoring mechanisms.             | [29:7] |
Ensuring compliance with climate policies requires robust enforcement mechanisms.            | [29:7] |
Monitoring and enforcement mechanisms include tracking emissions.                            | [29:8] | monitoring and enforcement mechanisms
Monitoring and enforcement mechanisms include verifying data.                                | [29:8] | monitoring and enforcement mechanisms
Monitoring and enforcement mechanisms include imposing penalties for non-compliance.         | [29:8] | monitoring and enforcement mechanisms
Transparent reporting is essential for maintaining public trust.                             | [29:9] |
Accountability is essential for maintaining public trust.                                    | [29:9] |
Transparent reporting and accountability are essential for achieving policy objectives.      | [29:9] |
```

"This" in 29:8 refers to the monitoring and enforcement just named in 29:7, so the name comes from the page, earlier than the sentence. Self-check with the kit's code checks: every id exists, no proposition starts with a pronoun, every resolved name occurs earlier on page 29, align = 1.000 for all eight (no added word), and every span lies inside one parent, chunk 84.

**Key points** (a 3 needs every point):
- [ ] One fact per line: the two mechanisms of 29:7 and the three activities of 29:8 are split.
- [ ] "This" is replaced by a name taken from 29:7, and that name is listed as resolved.
- [ ] Each proposition has the right source_ids (29:7, 29:8 or 29:9).
- [ ] Nothing is added that the sentences do not say (no "governments", no "fines").

**For a 4, also:**
- [ ] Runs or describes the self-check: ids exist, no pronoun start, resolved names found earlier on the page, align = 1.000, one parent chunk.

**Common wrong answers:**
- [ ] "This includes tracking emissions, verifying data, and imposing penalties.": it still starts with a pronoun and holds three facts.
- [ ] "Governments impose penalties for non-compliance.": the page never says who imposes them; "governments" is an added word (align < 1).

**If you missed it, reread:** [short §2](../reading/I4_proposition_chunking.md#2-what-a-proposition-is) · [short §3](../reading/I4_proposition_chunking.md#3-decontextualisation-names-instead-of-pronouns) · [short §6](../reading/I4_proposition_chunking.md#6-every-proposition-points-back-to-its-source) · [lesson step 3](../lessons/I4_propositions.html#decontext) · [lesson step 6](../lessons/I4_propositions.html#anchor) · book Ch4 p.5–6/15

</details>
<!-- /q -->

<!-- q id=I4-A-02 type=A set=main -->
### I4-A-02 · Application (MC-001 check item)
**Question:** How many index-time LLM calls does Corpus D need with per-proposition grading, and with batched grading, and which part dominates?

**Data:** 33 pages; about 1,400 propositions; one generation call per page in both plans.

**Reply template:** `per-proposition: ____ + ____ = ____ calls; batched: ____ + ____ = ____ calls; the dominant part is ____.`

<details><summary>Hint 1</summary>

Generation is the same in both plans. Only the grading differs.

</details>

<details><summary>Hint 2</summary>

Per-proposition grading is one call per proposition; batched grading is one call per page.

</details>

<details><summary>Hint 3</summary>

Generation = 33 calls. Now add the grading calls of each plan.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
calls = pages (generate) + pages (batched grade)  or  + propositions (per-proposition grade)
per-proposition:  33 + 1,400 = 1,433 calls    1,725,450 tokens   $0.236   8.63 days of 200K TPD
batched:          33 +    33 =    66 calls      199,650 tokens   $0.039   1.00 day
```

Per-proposition **grading** dominates: 1,400 of the 1,433 calls. The money is small either way; the daily token quota is the constraint. The token, cost and day figures use **ASSUMED** per-call sizes (generation 1,050 in / 1,600 out, per-proposition grade 870 / 300, batched grade 1,800 / 1,600), to be replaced by the provider's usage numbers after the first recorded call.

**Key points** (a 3 needs every point):
- [ ] Per-proposition: 1,433 calls.
- [ ] Batched: 66 calls.
- [ ] The per-proposition grading dominates (1,400 of 1,433), and the limit is the daily quota (about 8.6 days vs 1), not money.

**For a 4, also:**
- [ ] Says the token figures rest on assumed per-call sizes, and that batching is the default with per-proposition grading only as a one-page ablation.

**Common wrong answers:**
- [ ] "1,400 calls": that forgets the 33 generation calls.
- [ ] "1,400 propositions × 100 characters = 140,000 tokens": characters are not tokens, and the prompt, the output and the reasoning all count (MC-001).

**If you missed it, reread:** [short §11](../reading/I4_proposition_chunking.md#11-what-it-costs) · [lesson step 11](../lessons/I4_propositions.html#cost) · book Ch4 p.7–9/15 and p.13/15

</details>
<!-- /q -->

<!-- q id=I4-A-03 type=A set=main -->
### I4-A-03 · Application
**Question:** For this made-up ranked list, compute MRR@10 on parents after dedup, and the number of distinct parents in the top 4.

**Data:** the question is "What does achieving renewable energy targets require?". Its gold is sentence 10:16, which lies only inside chunk 28, so the one relevant parent is chunk 28. The order is made up (not model output); propositions and parents are from the tutor set:

```
rank  proposition  parent  text
1     p10-10       27      Under the Paris Agreement, countries submit nationally determined contributions (NDCs).
2     p10-11       27      Nationally determined contributions (NDCs) outline countries' climate action plans and targets.
3     p23-05       68      Regular reviews and updates of NDCs are essential for meeting the Paris Agreement's goals.
4     p10-19       28      Achieving renewable energy targets requires robust infrastructure and market development.
5     p10-18       28      Renewable energy targets are supported by policies such as subsidies, tax incentives, ...
6     p10-24       29      Urban climate initiatives include sustainable transportation systems, ...
```

**Reply template:** `parents after dedup: ____; first relevant at position ____; MRR@10 = ____; distinct parents in the top 4: ____.`

<details><summary>Hint 1</summary>

Walk down the list and write each parent the first time you meet it. Skip parents you have already written.

</details>

<details><summary>Hint 2</summary>

RR = 1 / (position of the first relevant parent in the deduplicated list). For the top 4, look at the parents of ranks 1–4 only.

</details>

<details><summary>Hint 3</summary>

The parent column reads 27, 27, 68, 28, 28, 29.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
parents in rank order       27, 27, 68, 28, 28, 29
after dedup                 [27, 68, 28, 29]
first relevant (28)         position 3   → RR = 1/3 = 0.333   → MRR@10 = 0.333 (one question)
top 4 propositions          parents 27, 27, 68, 28 → 3 distinct parents
self-check, arm (b)         first proposition whose span overlaps gold: p10-19 at rank 4 → RR = 1/4 = 0.25
```

Dedup moves the relevant parent up from proposition rank 4 to parent position 3, so arm (a) and arm (b) give different numbers for the same list. And "top 4" returned only 3 chunks.

**Key points** (a 3 needs every point):
- [ ] Parents after dedup: [27, 68, 28, 29].
- [ ] RR = 1/3 = 0.333 (MRR@10 for this one question).
- [ ] 3 distinct parents in the top 4.

**For a 4, also:**
- [ ] Contrasts arm (b) on the same list (RR 0.25), says why they differ (dedup), and that the order is made up.

**Common wrong answers:**
- [ ] "RR = 1/4 = 0.25": that is the proposition's rank before dedup, which is arm (b), not arm (a).
- [ ] "4 distinct parents in the top 4": chunk 27 appears twice.

**If you missed it, reread:** [short §9](../reading/I4_proposition_chunking.md#9-three-ways-to-score-propositions) · [lesson step 9](../lessons/I4_propositions.html#score) · book Ch4 p.9–10/15

</details>
<!-- /q -->

<!-- q id=I4-A-04 type=A set=main -->
### I4-A-04 · Application
**Question:** Compute align(p) for "The Paris Agreement was adopted in 2016." against its source 10:7, and say which flagging rule catches it.

**Data:** 10:7 = "The Paris Agreement, adopted in 2015, aims to limit global warming to well below 2 degrees Celsius above pre-industrial levels, with efforts to limit the increase to 1.5 degrees Celsius." W = the set of content-word stems: stop words such as "the", "was" and "in" are removed, and the kit's stemmer cuts endings such as -ed and -s.

**Reply template:** `W(p) = {____}; supported ____ of ____; align = ____; flagged by ____ but not by ____.`

<details><summary>Hint 1</summary>

Remove the stop words from the proposition. How many content words are left?

</details>

<details><summary>Hint 2</summary>

Which of those words appear in 10:7? Is "2016" there?

</details>

<details><summary>Hint 3</summary>

W(p) = {pari, agreement, adopt, 2016}: "paris" and "adopted" lose their endings.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
W(p)        = {pari, agreement, adopt, 2016}          (4 content words)
in W(10:7)  : pari, agreement, adopt                  (2016 is not; 10:7 says 2015)
align       = 3/4 = 0.750        unsupported: ['2016']
align < 0.5 → not flagged        align < 1 → flagged
```

This is planted mistake x-02, a distorted fact (the wrong year). Alignment catches it only because the wrong year is a new word. That is why the course lists **every** proposition with align < 1 for a person to read, not only those under 0.5.

**Key points** (a 3 needs every point):
- [ ] 4 content words, 3 of them in the source.
- [ ] align = 0.750, with "2016" unsupported.
- [ ] Flagged by the rule align < 1, not by align < 0.5.

**For a 4, also:**
- [ ] Names the limit: a dropped qualifier ("below 2" for "well below 2", x-03) scores 1.000, so a hand-checked sample is still needed.

**Common wrong answers:**
- [ ] "align = 1, every word is about the Paris Agreement": "2016" is not in the source sentence.
- [ ] "0.750 is high, so the proposition is fine": the one unsupported word is the whole fact.

**If you missed it, reread:** [short §7](../reading/I4_proposition_chunking.md#7-checking-the-rewrite-alignment-and-its-blind-spots) · [lesson step 7](../lessons/I4_propositions.html#align) · book Ch4 p.7–9/15

</details>
<!-- /q -->

<!-- q id=I4-A-05 type=A set=review -->
### I4-A-05 · Application (review)
**Question:** Which of these two hand-checked samples supports the claim "faithfulness ≥ 0.85"?

```
sample A   27/30 supported = 0.900   Wilson 95% interval [0.744, 0.965]
sample B   57/60 supported = 0.950   Wilson 95% interval [0.863, 0.983]
```

**Reply template:** `Sample ____, because ____. The other one ____.`

<details><summary>Hint 1</summary>

Which number of each row must clear 0.85 for the claim to hold: the rate, or one end of the interval?

</details>

<details><summary>Hint 2</summary>

Compare each lower bound with 0.85.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Only **sample B**: its lower bound 0.863 is at least 0.85. Sample A's rate (0.900) is above 0.85, but its interval reaches down to 0.744, so 30 labels cannot rule out a true rate below 0.85. More labels alone do not fix that: 54/60 = 0.900 gives [0.799, 0.953] and still fails. At a 95% supported rate, 60 is the smallest multiple of 20 that clears 0.85 (K11). These are formula outputs: no hand labels exist yet.

**Key points** (a 3 needs every point):
- [ ] Sample B.
- [ ] The test is the Wilson lower bound against 0.85, not the point estimate.
- [ ] Sample A's interval includes rates below 0.85 (down to 0.744).

**For a 4, also:**
- [ ] Notes that 54/60 = 0.900 still fails (lower bound 0.799), so the rate must be high as well as the sample large, or that these are formula outputs.

**Common wrong answers:**
- [ ] "Both, because 0.900 and 0.950 are above 0.85": the claim needs the lower bound, not the rate.
- [ ] "Neither, you need hundreds of labels": 57 of 60 already clears it.

**If you missed it, reread:** [short §7](../reading/I4_proposition_chunking.md#7-checking-the-rewrite-alignment-and-its-blind-spots) · [lesson step 7](../lessons/I4_propositions.html#align) · book Ch4 p.7–9/15

</details>
<!-- /q -->

<!-- q id=I4-T-01 type=T set=main -->
### I4-T-01 · Transfer
**Question:** A legal-contract corpus changes every week, and most questions ask to compare clause A with clause B: would you index propositions?

**Reply template:** `I would ____, because ____ and ____. I would check it by ____.`

<details><summary>Hint 1</summary>

What must a comparison question find in the top k? What happens to it when each clause is split into atomic facts?

</details>

<details><summary>Hint 2</summary>

What does each weekly change cost at index time, and which qualifiers in a contract can a rewrite drop?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Not by default. Three reasons:
1. **Comparisons need relations.** Atomic facts compete for the same k slots, so one side can crowd out the other. On the climate PDF, D-005 (coal vs natural gas) with the coal facts first gave arm (b) CE@4 = 0 (made-up order, K7).
2. **Weekly change means a recurring index cost.** Every changed page needs its generation and grading calls again, plus a fresh faithfulness check: calls × changed pages, every week.
3. **Contracts live on qualifiers** ("not", "unless", "within"). A rewrite that drops one changes the meaning, and alignment cannot catch a dropped word (x-03 scored 1.000).

Start with clause-level, structure-aware chunks with the heading path. If you still want to try propositions, run them as arm (a), returning the parent clause, and measure on compare questions with CE@k at an equal token budget, plus a hand-checked faithfulness sample.

**Key points** (a 3 needs every point):
- [ ] Compare questions need relations; atomic facts lose them and crowd the top k.
- [ ] A weekly change means a recurring cost: generation and grading for every changed page, and fresh checks.
- [ ] Contract qualifiers can be dropped silently; alignment does not catch dropped words.

**For a 4, also:**
- [ ] Says how to test it anyway (arm (a) returning clauses, CE@k on compare items, equal token budget, hand faithfulness), or names the alternative (clause-level structure-aware chunks).

**Common wrong answers:**
- [ ] "Yes, smaller units are always more precise": more precise for one fact, worse for relations (D-005).
- [ ] "Index once and reuse it": the corpus changes every week.

**If you missed it, reread:** [short §10](../reading/I4_proposition_chunking.md#10-what-atomic-facts-lose) · [short §13](../reading/I4_proposition_chunking.md#13-when-not-to-use-it) · [lesson step 10](../lessons/I4_propositions.html#relations) · book Ch4 p.11–12/15

</details>
<!-- /q -->

<!-- q id=I4-T-02 type=T set=main -->
### I4-T-02 · Transfer (MC-006 check item)
**Question:** Your proposition arm wins on MRR, but the hand-checked faithfulness is 0.80: what do you report, and can you adopt it?

**Reply template:** `I report ____. I would ____ adopt it, because ____. Next I would ____.`

<details><summary>Hint 1</summary>

Retrieval quality and the faithfulness of the indexed text are two separate measurements. Which one does the 0.80 describe?

</details>

<details><summary>Hint 2</summary>

Where must the Wilson lower bound sit for the claim "faithfulness ≥ 0.85"? And how many dev items does the MRR win rest on?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Report both, separately: the MRR result (arm (a), with n, the per-question wins and losses, fixed k and equal token budget) and the faithfulness 0.80 with its n, its Wilson interval and the split into added and distorted. **Do not adopt it yet.** The point estimate is already under 0.85, so the lower bound is too: about one indexed fact in five misstates its source. With about 10 factual dev items, the MRR win may also be noise. Arm (a) softens the harm, because the generator reads the original parent chunk, not the proposition. But a distorted proposition can still pull the wrong chunk up for some questions. Next: fix the generation (prompt rules, a fully supported example, the align < 1 list), regenerate, re-label a fresh sample, and re-run. Or try I5's headers, which keep the original text.

**Key points** (a 3 needs every point):
- [ ] Report retrieval and faithfulness as separate results, each with n (faithfulness with its Wilson interval).
- [ ] Do not adopt: faithfulness below 0.85 (the lower bound is lower still).
- [ ] The MRR win on so few items may be noise ("inconclusive" was pre-registered as a likely verdict).
- [ ] Next step: fix generation and re-label, or try I5 headers.

**For a 4, also:**
- [ ] Notes that arm (a) returns parents, so the generator sees original text and the harm is in the ranking, but a ranking driven by distorted facts is still not trustworthy.

**Common wrong answers:**
- [ ] "MRR went up, so adopt it": faithfulness is a separate guard, and an LLM grade cannot replace it (MC-006).
- [ ] "0.80 is close enough to 0.85": the claim needs the lower bound to clear 0.85, and 0.80 is the point estimate.

**If you missed it, reread:** [short §7](../reading/I4_proposition_chunking.md#7-checking-the-rewrite-alignment-and-its-blind-spots) · [short §12](../reading/I4_proposition_chunking.md#12-proposition-chunking-in-your-project) · [lesson step 7](../lessons/I4_propositions.html#align) · [lesson step 12](../lessons/I4_propositions.html#project) · book Ch4 p.11–12/15

</details>
<!-- /q -->

<!-- q id=I4-T-03 type=T set=main -->
### I4-T-03 · Transfer
**Question:** The few-shot example in your generator prompt was written from page 10 of the corpus: what breaks, and which test catches it?

**Reply template:** `It breaks ____, because ____. The ____ test catches it: ____.`

<details><summary>Hint 1</summary>

The eval questions and gold quotes come from the same pages. What could the prompt now share with them?

</details>

<details><summary>Hint 2</summary>

How can code detect that two texts share wording? Think of runs of 8 words.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** It **leaks**. The example now contains page 10's own facts, in a chosen phrasing, and the eval questions and gold quotes (D-002's among them) come from that page. The model is shown how to rewrite the very sentences it is tested on, so the scores on those items are inflated and the comparison is not fair. The **8-gram leakage test** catches it: it compares the prompt with every eval question and gold quote (K10):

```
eval texts: 10 questions + 12 gold quotes, 172 distinct 8-grams
clean prop_gen_v1 (town-library example)   0 shared 8-grams
example replaced by the D-002 quote        10 shared 8-grams → the test fails, as it should
```

Fix: write the example from outside the corpus, as `prop_gen_v1` does, and make its output fully supported by its input.

**Key points** (a 3 needs every point):
- [ ] Leakage: the example shares text with the eval questions or gold quotes, so the scores are inflated.
- [ ] The 8-gram overlap test of the prompt against eval questions and gold quotes catches it (clean 0, injected 10).
- [ ] Fix: an example written from outside the corpus.

**For a 4, also:**
- [ ] Adds that the example must also add nothing (upstream's "astronaut" teaches added facts) and that book text never goes into a prompt; the test runs before every recorded run.

**Common wrong answers:**
- [ ] "It is fine, the example is true": true text from the test pages is exactly what leaks.
- [ ] "Remove all examples": an example helps the output format; it just has to come from outside the corpus.

**If you missed it, reread:** [short §5](../reading/I4_proposition_chunking.md#5-the-prompt-and-the-output-schema) · [short §12](../reading/I4_proposition_chunking.md#12-proposition-chunking-in-your-project) · [lesson step 5](../lessons/I4_propositions.html#prompt) · book Ch4 p.5–6/15

</details>
<!-- /q -->

<!-- q id=I4-T-04 type=T set=review -->
### I4-T-04 · Transfer (review)
**Question:** A teammate indexes propositions for only 5 pages (about 15 chunks) and compares them with chunks at k = 4: what is wrong with the comparison?

**Reply template:** `With about ____ chunks, k = 4 ____. Also ____. I would instead ____.`

<details><summary>Hint 1</summary>

What share of the index does k = 4 return when there are only about 15 chunks?

</details>

<details><summary>Hint 2</summary>

Upstream's chunk arm ran k = 4 over 3 chunks. What could that comparison measure? And how many parents does the proposition arm return at k = 4?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** k = 4 over about 15 chunks returns about a quarter of the index for every question, so both arms hit a ceiling and the comparison cannot separate them. Upstream showed the extreme: its chunk arm ran k = 4 over 3 chunks, so every query returned the whole index (cell 22, K12). Also, the proposition arm's k = 4 gives at most 4 parents, often fewer, so the arms do not get the same context. Instead: index the **full** corpus (66 calls with batched grading, about one day of quota) and restrict the **eval items** to the subset if needed, never the index. Compare at a fixed k and at an equal token budget, report the parents returned, and pre-register "inconclusive" as a likely verdict.

**Key points** (a 3 needs every point):
- [ ] k = 4 covers a large share of a 15-chunk index: a ceiling, so the arms cannot be told apart.
- [ ] Restrict the eval items, not the index; the full-corpus index is affordable (66 calls).
- [ ] Fixed k and an equal token budget, with the parents returned reported (k propositions → at most k parents).

**For a 4, also:**
- [ ] Names upstream's degenerate baseline (k = 4 over 3 chunks returns everything), or says that a handful of items will likely give "inconclusive".

**Common wrong answers:**
- [ ] "Fewer pages make a cleaner comparison": they make k cover the whole index.
- [ ] "It is fair because both arms use k = 4": k = 4 propositions return at most 4 parents, often fewer.

**If you missed it, reread:** [short §12](../reading/I4_proposition_chunking.md#12-proposition-chunking-in-your-project) · [short §9](../reading/I4_proposition_chunking.md#9-three-ways-to-score-propositions) · [lesson step 12](../lessons/I4_propositions.html#project) · book Ch4 p.10–11/15

</details>
<!-- /q -->
