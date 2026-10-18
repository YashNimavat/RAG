<!-- kit:reading concept=I6 depth=short version=1 -->
# I6: Document augmentation and HyPE (index-time question generation)

**What this is:** the short reading for I6, the text version of the HTML lesson's Short depth (`study/lessons/I6_doc_augmentation.html`). It is enough to answer every question in `study/questions/I6_questions.md`.
**What this is not:** the HyDE lesson (Q2 owns query-time generation), the fusion lesson (R1 owns RRF and BM25), or the research history and framework source that the HTML lesson keeps in Full.

> **Read in the book:** Ch11 p.1/13, p.6–11/13 (per 04; not re-opened in the build session)

**The answer first.** Users ask questions; documents make statements. A question's vector often lands nearer to other questions than to the passage that answers it. Document augmentation fixes this when the index is built: an LLM writes a few questions each chunk answers, every question gets its own vector, and every vector points back to its parent chunk. At query time nothing extra is called: you search the vectors, turn the hits into **unique** parent chunks, and hand those chunks (never the questions) to the answer model. The price is one LLM call per chunk at every rebuild and a bigger index; the risks are hallucinated questions, one parent filling the top k, keyword queries the questions paraphrase away, and a fake gain when the index questions look like your eval questions.

**Where the numbers come from.** Local runs on the climate PDF, v0's **97 chunks**, with MiniLM (`all-MiniLM-L6-v2`): `sources/verification/I6/I6_FACTS.md`, sections K1–K12. Four labels apply to every number below:
- The 970 generated questions are a **stand-in pack**: written by Claude helpers who saw only the prompt file and the chunk texts, never the eval set. The planned Groq or Haiku replay pack will give different numbers.
- The 10 seeds (D-001…D-010, 8 answerable) are LLM-drafted and not human-verified. Eight items show the mechanism; they cannot pick a winner.
- MiniLM was rebuilt from an ONNX export in the build container; it reproduced P4's numbers exactly before any I6 number was used.
- Book pages come from 04 and were not re-opened (the book was not in the build container).

## 1. Questions and statements embed apart

**The answer first:** retrieval embeds the question once, scores it against every stored vector (one score per vector, no matrix), and sorts. If questions and statements sit in different parts of the space, the right passage can lose to a passage that merely looks like an answer.

**The setup.** Take D-002, "In what year was the Paris Agreement adopted?", against the 97 chunks, then against the 970 generated questions (the book's asymmetry problem, Ch11 p.1/13).

**The result.**
```
best chunk score         0.4606   chunk 69 (Kyoto, the wrong treaty); the right chunk 27 is rank 3 (0.4386)
best question score      0.9869   "When was the Paris Agreement adopted?"  (a question of chunk 27)
shape gap, 8 seeds       a generated question beats every chunk for 8 of 8; mean gap 0.3007
questions nearer a sibling question than their own chunk:   859 of 970 = 0.886
```

**What this means.** A question and its own chunk are not close neighbours: almost nine in ten generated questions sit nearer another question about the same chunk. That is the **shape hypothesis**: question-shaped text clusters with question-shaped text. It is a hypothesis to test, not a law.

**For your project:** the fix is to put question-shaped vectors into the index, each tagged with the chunk it came from.

## 2. Index time vs query time: who pays the LLM call

**The answer first:** the LLM runs in the index lane, once per chunk per rebuild. The query lane is unchanged: embed the question, search, fetch chunks, answer.

```
index lane (once per rebuild):  chunk → LLM writes n questions → embed each → store with parent_id
query lane (every question):    embed question → search all vectors → unique parents → answer model
```

**The check question (MC-003):** is question generation part of the prompt sent to the answer model? **No.** It happened before any user arrived; the prompt holds only the parent chunks and the user's question.

HyDE is the mirror image: it writes a fake answer for each query, at query time, so it pays one LLM call per question (Ch11 p.9–10/13; Q2 owns it).

**For your project:** a user's query costs **0** extra LLM calls with I6.

## 3. One call per chunk writes n questions

**The answer first:** one call per chunk returns a JSON list of `n_max = 10` questions, best first, so one call serves n = 1, 3, 5 and 10 by taking a prefix.

**The setup.** The prompt file `study/tools/examples/i6_questions_prompt_v1.txt` asks for questions that the chunk answers on its own, phrased the way a user types, keeping names, numbers and acronyms, never pointing at "the text", never copying a whole sentence, and ordered from the most central fact down (Ch11 p.6/13 lists the steps; p.11/13 discusses how many).

**The result** (chunk 21, page 8, the gold chunk of D-006):
```
q1  What are perovskite solar cells and solar paint?
q2  What are floating solar farms?
q3  Why do floating solar panels work more efficiently?
```
The first question is about perovskite cells, not floating farms. "Most central first" is the generator's guess, so the prefix for small n is only as good as that guess.

**What this means.** Three engineering rules follow. Ask for structured output (a JSON list), parse it once, retry once on failure and log it; never split free text on newlines (HyPE cell 9 does, which can store empty strings). Cache each answer under a key of prompt version + chunk text + model, so an edited chunk regenerates only its own questions. And record the pack once, then replay it, because the generator is not deterministic.

**For your project:** the pack used here is a stand-in written by Claude helpers blind to the eval set; the real pack is recorded later by the LLMOps notebook.

## 4. Clean, then check every question against its own chunk

**The answer first:** cheap rules catch format faults; the real danger is a question its chunk does not answer, which you find by scoring each question against its own chunk.

**The result** (rule counts on the 970 questions):
```
empty 0 · no "?" 0 · numbering 0 · deictic/vague 1 (a false positive: "in the context of climate change")
duplicates inside a chunk 0 · exact duplicates across chunks 6
vocabulary echo (share of a question's content words found in its own chunk)   mean 0.777; 227 of 970 use only chunk words
own chunk's rank with the question as query    rank 1: 529 · ≤ 10: 912 · > 10: 58 (of 970)
cos(question, own chunk)                       min 0.0407 · median 0.5917
bottom-30% filter                              cut 0.5351 → drops 291, keeps 679
```

**What this means.** The rules found almost nothing, because the prompt already forbids those faults. The checks against the chunk matter more. Fifty-eight questions do not find their own chunk in the top 10: vague, off-topic or hallucinated questions. Doc2Query-- showed that generated queries can be wrong about their own passage, and filtered the low scorers with a relevance model (its example cut is the 70th percentile). The bottom-30% cut here uses the bi-encoder cosine as a **stand-in** for that cross-encoder. The high echo (0.777) says the questions mostly reuse the chunk's words; keep it in mind for §9.

**For your project:** report what each rule and the filter removed; treat the filter as an arm to measure, not a default.

## 5. Three designs, one parent table

**The answer first:** every design stores a table `vectors[i] → (kind, parent_id, question_text)`; they differ in which vectors exist.

| Design | Vectors per chunk | n = 5, 97 chunks | Gives up |
|---|---|---|---|
| chunks + questions (doc-aug) | 1 + n | 582 | size: 6× the vectors, more duplicate parents |
| questions only (HyPE) | n | 485 | the chunk's own vector, so rare terms (§8) |
| questions appended to the text (doc2query, LlamaIndex) | 1 | 97 | a separate question match: one vector mixes both |

```
bytes = vectors × d × 4 (float32), d = 1,536
582 × 1,536 × 4 = 3,575,808      485 × 1,536 × 4 = 2,979,840      v0's index (C3) = 596,096
```

**What this means.** The parent table is the whole trick: a match on any question is a vote for its parent chunk. LlamaIndex's extractor (5 questions by default) stores them as metadata that is embedded with the text, which is the third design.

**For your project:** chunks + questions is the safe default, because the chunk vector still catches queries that copy the document's words.

## 6. Search the vectors, return unique parents

**The answer first:** search all vectors, map each hit to its parent, keep the first occurrence of each parent in rank order, and only then cut to k.

**The setup.** D-006, "What are the advantages of putting solar panels on lakes or reservoirs?", against chunks + questions at n = 5.

**The result.**
```
top 12 vectors: 11 questions + 1 chunk (chunk 21's own vector at rank 7), only 8 unique parents
rank 1  0.5976  question of chunk 21: "Why do floating solar panels work more efficiently?"
dedup in rank order → parents 21, 64, 19, 32   (gold chunk 21 first)
```

**Parent score.** Use the best vector: `s(p) = max cos(q, v)` over the parent's vectors. Summing is biased toward parents with more vectors. Toy (made-up scores, 8 vectors, 3 parents):
```
max   A 0.81, B 0.74, C 0.66  → A, B, C
sum   A 1.31, B 2.85, C 1.21  → B, A, C     (B has 4 vectors, so it wins the sum)
```
RRF (`Σ 1/(60 + rank)` over a chunk list and a question list) is the other option; R1 owns it.

**Why dedup comes before the cut.** Several top vectors often share one parent. At n = 5 the top 4 vectors held a mean of 3.00 unique parents, and only 2 for three of the 8 seeds. LangChain's `MultiVectorRetriever` fetches 4 child vectors by default and returns their unique parents, so "k = 4" gave 2 parents on the toy. The fix: fetch `K_vec ≥ k(n + 1)` vectors (each parent owns at most n + 1), dedup in rank order, then cut. For k = 4, n = 10 that bound is 4 × 11 = 44; the seeds needed at most 11. Do not dedup with `set()`: it keeps the members but loses the order.

**For your project:** log, for every query, which question matched and which parent was returned.

## 7. Score the parent's span, never the question

**The answer first:** the thing you evaluate and send is the parent chunk, so evidence coverage (CE@k) is computed on the parents' `[char_start, char_end)` spans. A question is a pointer, not evidence.

**The result** (8 answerable seeds, MiniLM):
| Arm | Hit@1 | MRR@10 | CE@4 (of 8) |
|---|---|---|---|
| A0 chunks only (v0) | 4 | 0.708 | 8 |
| A1 chunks + questions, n = 1 | 4 | 0.653 | 7 |
| A1 n = 5 | 5 | 0.781 | 7 |
| A1 n = 10 | 5 | 0.792 | 7 |
| A1 n = 5, sum instead of max | 5 | 0.760 | — |

**What this means.** At n = 5, MRR@10 rose from 0.708 to 0.781 and Hit@1 from 4 to 5, but CE@4 fell from 8 to 7: D-007 needs two chunks (27 **and** 85), and question matches pushed one out of the top 4. One question per chunk was worse than none (0.653). Questions only scored exactly like A1 from n = 5 on, here. Sum was worse than max. With 8 draft items none of these differences proves anything.

**For your project:** report CE@4 next to Hit and MRR; a multi-hop item can lose even while the ranks look better.

## 8. Keyword and number queries: the guard

**The answer first:** generated questions paraphrase, so they drop the chunk's numbers, codes and acronyms. A questions-only index then has nothing to match a query by number.

**The result** (rare-token retention: the share of the chunks' numbers and acronyms that appear in at least one of their questions):
```
n = 1   0.066  (6 of 91)
n = 3   0.143
n = 5   0.264  (24 of 91)
n = 10  0.549  (50 of 91)
```

**What this means.** At n = 5 roughly three quarters of the rare tokens appear in no question. The three exact-term seeds still passed with questions only, but only because the pack happened to contain a question naming each term (D-004 matched "What does DAC stand for?"). That is luck, not a property.

**For your project:** keep the chunk vector (chunks + questions) or add BM25 (R1). The original doc2query was itself a BM25 expansion: it appended the questions to the text.

## 9. Leakage: when the index already holds the eval question

**The answer first:** if the index questions and the eval questions come from the same drafting habit, the eval question may already sit in the index, and the "gain" is a near-copy finding itself.

**The setup.** For each eval item, `leak(i)` = the highest cosine to any generated question. The only paraphrase pair in 06 (D-002 vs D-002-P1) scores 0.7054, used as a **provisional** τ (06 asks for at least 10 pairs).

**The result.**
```
D-001  leak 0.9311   D-002  leak 0.9869   D-004  leak 0.9653   D-008  leak 0.9368     (flagged)
D-005  leak 0.4723   D-006  leak 0.6007                                             (not flagged)
generated questions within τ of a seed: 10 of 970
de-leaked A1 (those 10 deleted): MRR@10 0.547, below A0's 0.708
unanswerable D-009: best score 0.3099 with chunks → 0.7939 with questions ("What does IPCC stand for?")
```

**What this means.** This is not copying: the helpers never saw the seeds. It is the same habit: an LLM turns a chunk's key sentence into its obvious question, both for the seeds and for the index. Delete the ten near-copies and the gain disappears, so on these items the gain and the leakage cannot be separated. The D-009 line is a second warning: a fixed score threshold for "no answer" gets harder once questions are in the index. AIQ's Q45 makes the same point about synthetic eval sets: they echo the chunk's vocabulary and inflate retrieval scores.

**For your project:** the decision uses the **decisive slice**: human-written items plus items with `leak(i) < τ`. Report the flagged share and the de-leaked arm next to every gain.

## 10. What it costs, and when HyDE is cheaper

**The answer first:** 97 calls per rebuild, a fraction of a cent, a few minutes on the free tier; index time wins in calls once queries between rebuilds outnumber the chunks.

**The result** (tokens measured; prices Groq $0.075 / $0.30 per million; 8,000 tokens per minute and 200,000 per day on the free plan, UNVERIFIED):
```
input per call median 403 tokens; visible output median 111 at n = 10
n = 10, visible only               Groq $0.0061   6.1 min at the TPM limit
n = 10, + 300 reasoning (assumed)  Groq $0.0148   9.7 min, 39.0% of a day's tokens
break-even in calls:  Q_total > N × rebuilds       97 × 2 rebuilds a month = 194 queries a month
                                                   daily rebuilds: 97 × 30 = 2,910 queries a month
context to the answer model, k = 4:  A1 parents 627.9 tokens vs A0 chunks 671.0 (same unit)
```

**What this means.** Money is not the reason to keep n small; noise and leakage surface are. Query time stays free of LLM calls (HyDE adds 1 per query), and the context budget is unchanged because the returned unit is still the chunk.

**For your project:** if the corpus changes often and queries are few, HyDE or nothing may be cheaper. Cache by chunk text, so a rebuild regenerates only changed chunks.

## 11. The repo, read critically

**The answer first:** the repo's `document_augmentation` notebook returns a third of the PDF as one "chunk", and its HyPE notebook loses the metadata needed to cite.

**The result** (K2, K11, the cited cells):
```
document_augmentation: the PDF as one string → 9,406 regex words → 3 parents of 4,000 / 4,000 / 1,606 words
  share of the PDF       42.5% / 42.5% / 17.1%
  tokens per parent      4,271 / 4,237 / 1,687     k = 1 → up to 6.4× v0's context
  punctuation            1,493 characters in the PDF, 0 in the parents ("1.2 degrees" becomes "1 2 degrees")
HyPE: cell 11 has a SyntaxError (outputs are stale); vectors stored with no metadata; questions split on newlines; dedup with set()
```

**What this means.** A "retrieval" that returns 42.5% of the corpus measures nothing. The doc-aug notebook also asks for "at least 40" questions with no saved output to show how many came back, and the final cell reads the parent from a loop variable left over from an earlier cell. HyPE's saved output looks like a success, but it was produced before the broken edit.

**For your project:** keep v0's chunk as the parent unit, with page and offsets, and never trust saved outputs without re-running.

## 12. When not to use it

**The answer first:** skip I6 when there is no shape gap to close, when queries are mostly codes or numbers, or when the corpus changes faster than queries arrive.

- Your baseline already finds the evidence (no misses to fix).
- Queries are part numbers, IDs or exact terms: use BM25 or hybrid (R1).
- The corpus is rebuilt so often that `N × rebuilds` exceeds the queries: HyDE or nothing.
- You cannot test for leakage: without a decisive slice, any gain is "inconclusive".

**If you run it, run it as an experiment.** Pre-registered arms: A0 (v1.x champion), A1 chunks + questions at n = 5, A2 questions only, A3 the n-sweep, A4 the de-leaked A1, A5 (optional) questions from another model family. Hypotheses: H1, A1 raises CE@4; H2, A2 lowers CE@4 on exact-term items; H3, A1's gain on the decisive slice is at least half its overall gain. Adopt only if the paired bootstrap CI of ΔCE@4 on dev excludes 0, H3 holds and the exact-term guard holds; otherwise the verdict is "inconclusive", an expected and honest outcome.

**Decisions for you:**
1. Which model writes the index questions: Haiku (another family than the eval drafter) or Groq now? **haiku / groq**
2. Install `langchain-classic` for one comparison cell, or read its source? **install / read**
3. Run the experiment, or keep I6 as mechanism only? **run / mechanism-only**

## Check yourself

→ `study/questions/I6_questions.md` ([open it](../questions/I6_questions.md)): 2 cold questions before reading, 11 after, 3 for a later review, and 1 interview question. Verify every number with `study/notebooks/I6_doc_augmentation_verify.ipynb`; try it on your own documents with `study/tools/question_augment_check.py`.
