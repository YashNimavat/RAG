<!-- kit:reading concept=I4 depth=short version=1 -->
# I4: Proposition chunking

**What this is:** the short reading for I4, the text version of the HTML lesson's Short depth ([study/lessons/I4_propositions.html](../lessons/I4_propositions.html)). It follows one page of the climate PDF, page 10, from a chunk to propositions, and is enough to answer every question in `study/questions/I4_questions.md`.
**What this is not:** a measurement of the method. No LLM has written a proposition for this course yet, and no embedding ranking of real propositions exists. It is also not the lesson's Full depth (Dense X, FActScore, the LangChain template and the counter-evidence in detail).

> **Read in the book:** Ch4 p.4–12/15 (moderate first chunks p.4–5/15, the LLM decomposition p.5–6/15, the 7/10 quality check p.7–9/15, embedding and retrieval p.9–10/15, against standard chunks p.10–11/15, where it helps and struggles p.11–12/15) and Ch4 p.13/15 (one check per chunk). Read p.5–6/15 before §2 and p.7–9/15 before §8.
> These page pointers come from the course's phase 4 research; the pages were not re-opened in the session that wrote this file (the book was not available there), so treat them as UNVERIFIED until you read them.

**The answer first.**
1. A chunk that holds five facts gets one vector, a blend of all five. A question about one of them may match it weakly.
2. Proposition chunking asks an LLM to rewrite each page as short statements, one fact each, with pronouns replaced by names, and indexes those instead.
3. A proposition is not text from the document. So each one must point back to the sentences it came from (`source_ids`). That pointer gives it a span to score against gold and a parent chunk to return.
4. Code checks catch added words, pronouns and bad ids. They cannot catch a dropped qualifier or a wrong referent: only a person reading against the source does.
5. It costs LLM calls at index time: one per page to generate, plus one per page to grade in a batch, or one per proposition (about 1,400 on this corpus).
6. Expect a gain, if any, on single-fact questions. Contrast and synthesis questions can get worse.

**Labels used below.** *Measured* numbers come from `i4_kit_measure.py` ([I4_FACTS](../../sources/verification/I4/I4_FACTS.md), K1–K12). *Hand-written*: the 40 propositions in `i4_tutor_props.jsonl` were written by the tutor, not by an LLM; they show how the checks work, not how well a model does. *Made-up order*: the ranked lists in §9 and §10 are invented orders, never model output. *ASSUMED*: the token sizes per call in §11. No API was called to write this file.

---

## 1. One vector for many facts

**The setup.** v0 cuts the climate PDF into 97 chunks of up to 1,000 characters. Chunk 27 holds the start of page 10 and the answer to D-002, "In what year was the Paris Agreement adopted?". The same chunk also describes the UNFCCC, the Kyoto Protocol, the Paris goals, NDCs and carbon pricing. The embedder gives the whole chunk one vector. A toy shows what that does: n made-up facts at right angles to each other, the chunk vector is their normalised mean, and the query matches one fact exactly.

**The result** (K8, toy):

```
cos(one-fact query, chunk of n facts) = 1/√n
n     1      2      3      4      5      6      7      8
cos   1.000  0.707  0.577  0.500  0.447  0.408  0.378  0.354
a one-fact distractor with cos 0.60 beats the right chunk from n = 3
```

**What this means.** The more facts a chunk mixes, the weaker its match to any one of them. This is called dilution. Real embeddings are not at right angles, so the toy shows the direction of the effect, not its size on our corpus.

**For your project:** single-fact questions such as D-002 are where a smaller index unit could help. Whether it does is a measurement for v1.4 (§12), not a promise.

## 2. What a proposition is

**The setup.** The upstream notebook (cell 12) gives five rules. A proposition must express a single fact, be understandable without context, use full names instead of pronouns, keep relevant dates and qualifiers, and contain one subject–predicate relationship. Dense X Retrieval, the paper behind the idea, says it in three words: **distinct, minimal, self-contained**. Take sentence 10:7 of the climate PDF.

**The result** (tutor-written, K4):

```
[10:7] The Paris Agreement, adopted in 2015, aims to limit global warming to well below 2 degrees
       Celsius above pre-industrial levels, with efforts to limit the increase to 1.5 degrees Celsius.

p10-07  The Paris Agreement was adopted in 2015.
p10-08  The Paris Agreement aims to limit global warming to well below 2 degrees Celsius above pre-industrial levels.
p10-09  Efforts under the Paris Agreement aim to limit the increase in global warming to 1.5 degrees Celsius.

tutor set: 40 propositions from 26 source sentences = 1.54 per sentence
Dense X (Wikipedia): 257M propositions / 114M sentences = 2.25 per sentence
```

**What this means.** One sentence became three facts, and each keeps the page's own words, including "well below" and "1.5". A proposition is a rewrite, not a cut: its text appears nowhere in the document.

**For your project:** propositions per sentence sets the index size and the cost (§11). Count it on a few of your own pages before you plan anything.

## 3. Decontextualisation: names instead of pronouns

**The setup.** Sentence 10:4 starts "It provides a framework…". On its own, "It" points at nothing. Decontextualisation replaces pronouns and vague references with the full name that the page used **earlier**. The proposition records the name it brought in, in a `resolved` list.

**The result** (tutor-written, K4):

```
[10:4]  It provides a framework for negotiating specific protocols and agreements, ...
p10-03  The UNFCCC provides a framework for negotiating specific protocols and agreements.   resolved: UNFCCC  (from 10:2, 10:3)
[29:14] These meetings play a crucial role in advancing global climate action.
p29-04  COP meetings play a crucial role in advancing global climate action.                 resolved: COP
[2:2]   It is mined extensively in countries like China, India, and the United States, ...
p02-04  Coal is mined extensively in countries like China, India, and the United States.     resolved: Coal

15 of 40 use a resolved name; every resolved name occurs earlier on the same page: True
pronoun-initial propositions (It, They, This, These ...): 0
```

**What this means.** Code can check both halves. The resolved name's words must occur in the page text before the first source unit, so a name taken from world knowledge fails. And a proposition that still starts with a pronoun is flagged.

**For your project:** D-007's bridge fact sits in exactly such a sentence, "It provides…" on page 10. I5 (contextual headers) attacks the same problem per chunk instead of per fact.

## 4. Number the sentences first

**The setup.** Before any LLM call, code splits each page into **units**: headings and sentences, each with an id `page:i` and its character offsets. The splitter is a small regex: a sentence ends at `.`, `!` or `?` followed by whitespace; a heading is a short line that starts with a capital letter, has no end punctuation and is not inside an unfinished sentence.

**The result** (K3):

```
33 pages: 621 sentences + 286 headings = 907 units; sentences per page min 6 / median 19 / max 22
every unit: doc_text[a:b] == text
p.10: 16 sentences, 11 headings, units 10:0–10:26
[10:6] heading    'Paris Agreement'
[10:7] sentence   page [438, 625)   doc [20993, 21180)
tests pass: '1.5 degrees' not split; 'pre-industrial' kept; 'market-\nbased' kept (29:2); 29:0 is not a heading
known limits: 23:0 = 'resources.' (the end of a page-22 sentence); a sentence that crosses a page is cut
```

**What this means.** The ids give the model something exact to point at. The offsets let code turn that pointer back into a span of the document. The splitter's limits become units the model may cite: "resources." on its own is a fragment, not a fact.

**For your project:** run the splitter tests on your own PDF first. Abbreviations such as "e.g." would split a sentence (0 occurrences in this PDF; maybe many in yours).

## 5. The prompt and the output schema

**The setup.** The course's prompt `prop_gen_v1` gives five rules and one example. The example is a made-up town library, from outside the corpus, and its output adds nothing the input does not say. Upstream's example is a sentence about Neil Armstrong walking on the Moon in 1969, and its first proposition is "Neil Armstrong was an astronaut." The sentence never says that, so the prompt teaches the model to add world knowledge.

**The result** (K10):

```
template 1,506 chars; rendered for p.10 3,858 chars ≈ 682 tokens (DERIVED ratio)
unit lines:  [10:3] The UNFCCC is an international treaty ...   [10:6] (heading) Paris Agreement
schema proposition_set_v1: {"propositions": [{"text": "...", "source_ids": ["10:7"]}]}
             every field required, additionalProperties false
8-gram leakage test vs 10 questions + 12 gold quotes: clean prompt 0 shared; D-002 quote injected 10 → fails, as it should
```

**What this means.** Ask for strict JSON and validate every reply with `jsonschema` anyway: schema-valid is not correct. Log two failures separately. One is a parse failure. The other is `finish_reason=length`, a reply cut off mid-JSON, because on gpt-oss-20b the reasoning tokens count as output tokens (MC-001). Never turn a failure into an empty list without a log. LangChain's template does exactly that with `with_fallbacks`, and the page then drops out of the index unseen. Two more defaults: LangChain's `with_structured_output` forces a tool call (`tool_choice="any"`), and upstream's model id `llama-3.1-70b-versatile` is retired. Read the model id from config and record the id the provider returns.

**For your project:** the prompt and schema are frozen files with a sha256. The leakage test runs before every recorded run.

## 6. Every proposition points back to its source

**The setup.** The model returns `source_ids` with each proposition. Code turns them into a span, span(p) = [min aᵢ, max bᵢ) over the units i in source_ids (all on one page). A **parent** is a v0 chunk that contains the span.

**The result** (K4):

```
p10-01  source_ids [10:2, 10:3]  span [20628, 20765)  parent 27
p10-12  source_ids [10:11]       span [21331, 21479)  parents 27, 28   (inside the 200-char overlap)
all 40: ids exist, span inside the document, one page; 40/40 inside a chunk
parents: 34 have 1, 6 have 2; primary parent = the lowest seq
```

**What this means.** The course's `Chunk` type requires `doc_text[char_start:char_end] == text` (06 §2.3). A proposition's text is never such a substring, so a proposition cannot be a `Chunk`. It needs its own type, an **IndexUnit**: the text you embed (the proposition) differs from the evidence span (span(p)), and it carries its parent ids. Scoring uses the span; the generator reads the parent.

**For your project:** v1.4 stores IndexUnits next to v0's chunks. The span is what makes span gold (CE@k, any_overlap) usable at all.

## 7. Checking the rewrite: alignment and its blind spots

**The setup.** align(p) = |W(p) ∩ (W(sources) ∪ W(resolved names))| / |W(p)|, where W is the set of content-word stems. A word in the proposition that is in neither its sources nor its resolved names is unsupported. Six mistakes were planted on purpose to see which check catches which.

**The result** (K5):

```
proposition                                               align   caught by
upstream "Neil Armstrong was an astronaut."               0.667   align < 1 only (not < 0.5)
x-01 added    "...signed in Paris by 196 countries."      0.400   align < 0.5 and align < 1
x-02 wrong year "...adopted in 2016."                     0.750   align < 1 only
x-03 "below 2" for "well below 2" (qualifier dropped)     1.000   no code check
x-04 "The Paris Agreement provides a framework..."        1.000   no code check (the UNFCCC does)
x-05 "It provides a framework..."                         1.000   the pronoun check
x-06 source id 10:31 (p.10 has 10:0–10:26)                  —     the id check
tutor set                                                 1.000 for all 40
```

**What this means.** Alignment sees only **added** words. A threshold of 0.5 misses the astronaut and the wrong year, so list every proposition with align < 1 and read it. A dropped qualifier and a wrong referent use only supported words, so they need a person: label a sample as supported, added or distorted, and report a Wilson interval (K11, formula outputs, no labels exist yet):

```
27/30 = 0.900   Wilson [0.744, 0.965]
54/60 = 0.900   Wilson [0.799, 0.953]
57/60 = 0.950   Wilson [0.863, 0.983]   ← the only one whose lower bound clears 0.85
```

**For your project:** hand-label 60 units from the subset pages. The claim "faithfulness ≥ 0.85" needs the lower bound, not the point estimate.

## 8. The quality grade is a filter

**The setup.** Upstream (cells 15–16) grades each proposition from 1 to 10 on accuracy, clarity, completeness and conciseness, and keeps it only if all four are at least 7. The book's sketch does the same (Ch4 p.7–9/15, per the research).

**The result** (K2, upstream's saved output):

```
31 generated, 2 rejected (0.065): #17 completeness 6, #31 conciseness 6; 29 embedded
grader examples: 5, all 10/10/10/10 (no failing example)
label typos: 'Propositons' x5, 'Evaluation_3' x2; human turn '{proposition}, {original_text}' (no labels)
the same model generates and grades
```

**What this means.** The grade decides what enters the index, so it is an index-time **filter**, not an evaluation (D-10). Its 7 is a fixed, uncalibrated LLM threshold, the MC-006 pattern. A grader that has never seen a failing example tends to pass everything. To know what it does, compare its keep/drop with your hand labels: keep-good = kept ∧ good / good, and catch-bad = dropped ∧ bad / bad. Neither is measured yet, because no labels exist.

**For your project:** grade in one batched call per page (33 calls), not per proposition (about 1,400). Report keep-good and catch-bad with their n before you trust the filter.

## 9. Three ways to score propositions

**The setup.** Three scorings answer three different questions. **(a)** Rank the propositions, map each to its primary parent, keep the first occurrence of each parent, and score MRR@10 and CE@k on the parent chunks. This is the fair A/B against chunks. **(b)** Score the propositions themselves: rel(p) = 1 iff span(p) overlaps a gold segment, and CE@k on the union of the top-k spans. **(c)** Use the page that generated them as the parent. Rejected: a page almost always overlaps gold, so (c) measures page routing only. The **text check** adds a rule to (b): p counts only if its text states the gold fact.

**The result** (K7, D-002, made-up order):

```
rank  proposition  parent  span overlaps gold  states "2015"
1     p10-08       27      yes                 no
2     p23-02       68      no                  no
3     p10-07       27      yes                 yes
4     p10-10       27      no                  no
5     p23-01       68      no                  no
6     p10-09       27      yes                 no
arm (a)    parents after dedup [27, 68] → RR 1.000; top 4 propositions → 2 distinct parents; CE@4 = 1
arm (b)    RR 1.000; CE@4 = 1; distinct-facts@4 = 3
text check first proposition that overlaps gold AND states 2015: rank 3 → RR 0.333
```

**What this means.** Arm (b) gives full credit to a proposition that comes from the right sentence but does not say the year. The text check exposes that. Arm (a) also shows the parent effect: 4 propositions returned only 2 parents. LangChain's `MultiVectorRetriever` behaves the same way: **k child hits give at most k parents, often fewer**. In upstream's cells 20 and 32, 4 hits came from 1 parent.

**For your project:** report arm (a) as the result, arm (b) and the text check next to it, and the number of parents actually returned.

## 10. What atomic facts lose

**The setup.** The same made-up-order exercise on D-005 (contrast coal with natural gas) and D-007 (two hops: the UNFCCC, then its COP), plus two coverage ceilings. sentence_coverage = sentences with at least one proposition / sentences. gold_reachability = gold alternatives overlapped by some span(p) / alternatives.

**The result** (K6, K7):

```
D-005, four coal propositions first   arm (a) 1 parent [3], CE@4 = 1   arm (b) CE@4 = 0 (no gas fact in the top 4)
D-007, p10-05 at rank 4               arm (a) CE@4 = 1                 arm (b) CE@4 = 1
D-007, p10-05 moved to rank 5         arm (a) CE@4 = 1                 arm (b) CE@4 = 0
D-002 top 4: p10-08 and p23-02 are the same text → distinct-facts@4 = 3
sentence_coverage p.10 16/16; p.2 coal and gas paragraphs 4/6 = 0.667 (2:9 methane, 2:10 fracking left out)
gold_reachability of the tutor set 6/12 = 0.500 (a property of the sample, not of the method)
```

**What this means.** A contrast needs both sides, and atomic facts compete for the same k slots, so one side can crowd out the other. Multi-hop evidence hangs on one bridge fact ("It provides…" became p10-05); when it slips one rank, arm (b) loses it. Near-duplicates waste slots, and the corpus repeats paragraphs (page 10 and page 23). Coverage is a ceiling: arm (b) can never reach gold that no span overlaps.

**For your project:** keep D-005 and D-007 as guards in the v1.4 table, and report distinct-facts@4 and both coverage numbers.

## 11. What it costs

**The setup.** calls = pages (generate) + pages (batched grade) or + propositions (per-proposition grade). Propositions ≈ 621 sentences × 2.254 (the Dense X ratio) = about 1,400. Per-call token sizes are **ASSUMED** (generation 1,050 in / 1,600 out; batched grade 1,800 / 1,600; per-proposition grade 870 / 300). Prices: $0.075 / $0.30 per 1M tokens on Groq, with a 200K tokens-per-day free tier (plan UNVERIFIED).

**The result** (K9, Corpus D, 33 pages):

```
grading          calls   tokens      cost     days of 200K TPD
off              33      87,450      $0.018   0.44
batched          66      199,650     $0.039   1.00
per-proposition  1,433   1,725,450   $0.236   8.63
index size = n_props × dim × 4 bytes: 97 → about 1,400 vectors, ×14.4 (MiniLM 146 KiB → 2,100 KiB)
cost per 1k chunks (DERIVED, × 1000 / 97): batched $0.40 (680 calls); per-proposition $2.43 (14,773 calls)
```

**What this means.** Money is not the obstacle; the daily token quota is. Per-proposition grading makes 1,400 of the 1,433 calls and turns one day of quota into more than eight. The vector index grows about fourteen-fold.

**For your project:** generate and grade per page (66 calls, about one day of quota). Run per-proposition grading only as a one-page ablation. Replace the assumed sizes with the provider's usage numbers after the first recorded call.

## 12. Proposition chunking in your project

**The setup.** 06 plans v1.4 as a proposition index "on a subset (for example, 5 pages)". Restricting the **index** to 5 pages (about 15 chunks) makes k = 4 retrieve over a quarter of it. That is the ceiling upstream hit: its chunk comparison ran k = 4 over 3 chunks (cell 22), so every query returned the whole index.

**The result** (the plan; the v1.4 table is empty until the recorded run):

```
index         full Corpus D (66 calls); restrict the eval items, never the index
comparison    v1.4 arm (a) vs the current champion; fixed k = 4 AND an equal token budget
verdict       "inconclusive" pre-registered as an expected outcome (about 10 factual items)
guards        D-005, D-007, distinct-facts@4, sentence_coverage, gold_reachability, align < 1 list
faithfulness  60 hand labels, Wilson lower bound ≥ 0.85
leakage       8-gram test on the prompt before every run
v1.4 table    MRR@10 ___   CE@4 ___   tokens/question ___   (empty)
```

**What this means.** A fair comparison fixes everything except the index unit. With so few dev items, a small difference is noise, so "inconclusive" is a normal result, not a failure.

**For your project:** decide the index scope (full corpus recommended) and write the pre-registration before the first call.

## 13. When not to use it

- **Questions that compare, summarise or chain facts.** Atomic facts lose the relation (§10). Keep chunks.
- **Documents that change often.** Every changed page costs its generation and grading calls again.
- **When the propositions are not faithful.** If the hand-label lower bound is under 0.85, or many propositions have align < 1, do not index them. Consider I5's headers instead.
- **A strong trained embedder.** Dense X reported smaller gains for supervised retrievers (+2.7 Recall@20 vs +10.1 for unsupervised; UNVERIFIED). A 2026 reproduction by Zhou et al. found propositions worse than plain splitting (0.3888 vs 0.4849; UNVERIFIED).
- **A tiny index.** On a few chunks, k covers the index and nothing can be ranked (§12).

## Check yourself

→ [`study/questions/I4_questions.md`](../questions/I4_questions.md): 1 cold question before reading, 12 after, 3 for a later review, and 1 interview question. Answer the next day, closed book.
