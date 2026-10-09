# External resources review (2026-10-09)

**What this is.** A check of three outside sources against your RAG course. Sixteen reviewers read the sources and produced 266 findings. Every finding got a course-fit check; 125 of them also got an accuracy check. A critic then reviewed the draft, and six extra checks filled the gaps it found (see the Appendix). This is the final version. No course file was edited.

> **Tutor note (2026-10-09, after the review ran).** Title corrected: the book is *Evals for AI Engineers* (O'Reilly catalog, ISBN 9798341660717; the export's URL slug is shortened).  The learner set the copying rule for the two MIT repos: their exact questions, answers, explanations and code **may** be used. When a repo explanation is used, show it verbatim first, marked as a quote with the MIT notice, and give our plain-English wording after it. The review was written under a stricter paraphrase-only rule; §1 (AIQ paragraph) and §9 ('Copyright and licence', 'Turning interview questions into review items') are updated to match. The AI Eval book and the RAG book are unchanged: own words and pointers only. A check found no 15-word run shared between this report and the AI Eval book text.

**Citation key**
- **AE** = the AI Eval book, *Evals for AI Engineers* (Shreya Shankar and Hamel Husain, O'Reilly, 2026; this copy is an early-release export), exported to `rag_learning/AI Eval/`. It is copyrighted. Cited as `AE ChN, 'section'`. This report paraphrases it and never quotes it.
- **SDG** = `ai-system-design-guide` (GitHub, MIT licence), pinned at commit **ed955b2**. Cited as `SDG <path>, 'heading'`.
- **AIQ** = `AI-Engineer-Interview-Questions` (GitHub, MIT licence), pinned at commit **e080df2**. Cited as `AIQ <path>, 'heading'` or by question number.
- **†** = the accuracy check was not run on this finding (low value). Treat the source's claims there as **UNVERIFIED**.
- Book pages follow the course format: `Ch22 p.13/19` means PDF page 13 of the 19-page chapter 22 file.
- **(C)** = edits a reviewed plan file (02, 06 or 08) but keeps every decision. You OK it in the corrections log; Codex sees it at the next review.
- **(D)** = changes an agreed decision or contract. You decide, and Codex re-reviews it before it applies.
- **[P]** = a provisional number, to be confirmed.
- **CR-13-eligible** = a seed whose scenario is not in the lesson file, so it can be the lesson's scored fresh Transfer item (05 CR-13). **Review-only** = usable only as a review item from Day 14 on.

---

## 1. Bottom line

**AI Eval book (AE): include partly. Its role is the method source for Phase 3 and for the final judge batch.**
The authors developed much of this method, and the writing is clear and practical. The export has real flaws: early-release typos, several statistics slips, broken example code in Ch2 and Ch8, a non-standard nDCG, and a recipe (write questions from chunks, store chunk ids as gold) that the course bans on purpose. Its best chapters fill real gaps:
- Ch3 (error analysis) becomes M5's method.
- Ch4 and Ch5 tighten 06 §6.5 and §8.4: κ, failure classes, judge data splits, and judging a judge on both error directions.
- Ch10 gives a rule for choosing the ~10 answers you read per version.
- Ch7 gives critique targets, a recipe for distractor questions and a context-swap probe.

Before Gate B, AE changes only two things: one Phase 2 table (C6 Task 10, from Ch3) and one seed question (C4, from Ch7). It changes nothing in P1. Two reserve items also draw on it. Reading AE is optional. If you want to read, five short sections (about 2,900 words in total) each sit next to a Ch22 page (box in §4).

**ai-system-design-guide (SDG): reference only. Its role is a quarry for the coach, never reading.**
It is a large, polished interview survey that reads as AI-generated. It is full of October 2026 vendor news (models, prices, CVEs) that nobody here can check. It also has real errors: fusion naming, the RankGPT window direction, Self-RAG and CRAG, latency arithmetic (§8). The course is deeper on every core topic. About a dozen small pieces are worth taking:
- critique targets for calibration practice;
- MaxSim for R3 and a late-chunking line for I5;
- an oracle-context control for v0.1;
- an instruction-hierarchy sentence for P7;
- coach-side input on judge settings, from `13-reliability-and-safety` (agreement between two judges is not accuracy; temperature 0 may not be honoured).

When a piece is used, cite the primary source, not the guide. Skip its two root eval guides (`ai_evals_*.md`). They paraphrase the AE authors' course, and AE is deeper.

**AI-Engineer-Interview-Questions (AIQ): include partly, coach-side only. Its role is a bank of fresh scenarios, two test oracles and some critique targets.**
The Q&A is clean and mostly correct, with long model answers. The course already teaches its content, so the value is in its scenarios: each lesson's scored Transfer item must use a scenario that is not in the lesson file (05 CR-13). Some of its own mistakes make good 'is this claim right?' items, for example Recall@k defined as hit rate, and a wrong CRAG diagram. Two coding challenges are tested, key-free references: `12-coding-challenges/17` (RRF and MMR) for R1 and R4, and `12-coding-challenges/12` (EM/F1 edge cases) for M3.

You do not read this repo. The one exception is optional and late: two short sections of `09-safety-security-and-responsible-ai/README.md` for D4 in Phase 9 (about 10 minutes). Items taken from AIQ may keep the repo's exact wording (MIT). A long question is asked one part at a time. After your attempt, the repo's answer is shown verbatim, followed by our plain-English explanation and any correction from §8. Grading still uses an answer key built from course sources.

**Where the sources overlap, this report picks one:**

| Idea | Chosen | Not chosen | Why |
|---|---|---|---|
| Error-analysis method | AE Ch3 | SDG `ai_evals_comprehensive_study_guide.md`, 'Chapter 3'; AIQ 07 Q27 | AE is the primary source and deeper. It warns against LLM-written notes and about the first-failure undercount. |
| Judge data splits; correcting judge error | AE Ch5 | SDG `16-case-studies/18-eval-gated-cicd.md` (its 60/20/20 split contradicts AE); SDG study guide 'Chapter 10' | AE gives the formula and its caveats. |
| How κ works | AE Ch4, corrected | AIQ 07 Q17 and Q30; SDG study guide 'Chapter 12' | AE shows the mechanism and the prevalence trap. Do not import its 0.81 slip or its kappa code. |
| How to judge a judge | AE Ch4 (NOTE in 'When to Use Other Metrics') and Ch5 | AIQ 07 Q17 (κ plus raw agreement, inter-human 'ceiling') | AE measures both error directions. AIQ's ceiling is a heuristic, not a bound. |
| Judge agreement is not judge accuracy | SDG `13-reliability-and-safety/02-ensemble-methods.md`, 'Panel of LLM Judges (PoLL)' (the principle only; its numbers are UNVERIFIED) | SDG `06-retrieval-systems/13-rag-evaluation-patterns.md`, 'Best Practices for LLM-as-Judge' † | Read in full; the principle agrees with AE. |
| Which answers to read | AE Ch10 | SDG `15-ai-design-patterns/02-anti-patterns.md`; AIQ 07 Q35 | Primary source; it makes the case for a random slice. |
| Critique of auto-generated questions | AE Ch7 | AIQ 07 Q29; SDG `06-retrieval-systems/13-rag-evaluation-patterns.md` | AE's is the published recipe worth critiquing. |
| Long context vs RAG (P1 seed) | AIQ `14-company-interview-questions/harvey.md` Q9, rewritten as a fresh scenario with a corrected key | SDG `06-retrieval-systems/14-production-rag-at-scale.md`, 'RAG vs Long Context' (dated vendor prices; its break-even formula becomes a D2 reserve); AIQ 02 Q2; SDG `00-interview-prep/01-question-bank.md` Q78 | Tied to book Ch1 p.12/14 and needs no prices. Q78 has errors. |
| Temperature 0 still varies | Groq API reference and Thinking Machines Lab 2025 (primary, both read 2026-10-09); AIQ 08 Q11 as a secondary summary | SDG `01-foundations/06-inference-pipeline.md`, 'Sampling Controls on Hosted Frontier Models' | Primary sources. Anything specific to Groq stays UNVERIFIED. |
| MC-005 (both sides of choosing k) | AE Ch7 + book Ch22 p.11/19 | AIQ 04 Q48 vs Q50 (kept as reserve) | Anchored in the book. |
| How embedders are trained | Local all-MiniLM-L6-v2 model card | AIQ 01 Q40; SDG `01-foundations/05-embeddings-and-vector-spaces.md` | Primary and checkable. AIQ's τ range is wrong. |
| Injection reading for D4 (optional) | AIQ `09-safety-security-and-responsible-ai/README.md` (two sections) | SDG `05-prompting-and-context/08-prompt-injection-defense.md` | Shorter, checked accurate, fewer dated claims. |
| RRF and MMR | AIQ `12-coding-challenges/17` (tested code) | AIQ 04 Q24; SDG `06-retrieval-systems/05-hybrid-search.md` (z-score fusion misnamed) | Runnable tests. |
| Retry and backoff | The installed SDKs (groq 1.7.0, cohere 7.2.0) | AIQ `12-coding-challenges/11`; SDG | The SDKs already do it. |

Of the 125 findings whose accuracy was checked, none had a 'major errors' or 'misread by reader' verdict. Most had minor corrections, and those are applied below. The other 141 findings (†) were not accuracy-checked.

---

## 2. How this fits your goal (read the book and remember it)

- The RAG book stays the spine. None of these sources becomes required reading.
- Each addition is small and attached to a concept you already study. Where possible it points back to a book page: Ch1 p.3/14 and p.12/14, Ch3 p.11/14, Ch13 p.5–7/13, Ch22 p.6–18/19, App p.4/23.
- While P1 is in progress, P1 gets three small edits and one seed question. Nothing else touches P1 (§3a).
- **Cap: at most 2 new review items per concept** from these sources, counting seeds, Part L items and flashcards together. Extras wait in a coach-only reserve. This report keeps to that cap everywhere (§3–§5).
- Many items are 'is this claim right?' questions. They target the O1 finding that you are often confident and wrong.

---

## 3. Do now (Phases 0–2; low effort)

**What lands now, in total:**
- **P1 (in progress):** 3 small edits to P1 files and 1 note in 08 (§3a rows 1–3). The P1 seed sits in the seed bank (§3b).
- **Phase 2, before C6's first full v0 run:** 6 small changes (§3a rows 4–9).
- **Coach seed bank:** 9 seeds, one per concept: 6 CR-13-eligible, 2 review-only, 1 application item. Plus a reserve list (§3b).
- **In-file additions** to lessons that are written but not yet taught: 5 edits, which add 3 review items in total (§3b).

### 3a. Changes

| # | What | Where in the source | Attach to | How | Effort |
|---|---|---|---|---|---|
| 1 | **Why temperature 0 still varies** (P1, now) | Groq API reference, chat completions, `seed` (read 2026-10-09); Groq OpenAI-compatibility page (temperature 0 is converted to 1e-8; web only, recheck in P1 Task 8); Thinking Machines Lab, 'Defeating Nondeterminism in LLM Inference' (2025; https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/, read 2026-10-09). Secondary: AIQ `08-inference-and-production/questions.md` Q11 | P1 D.6 'Limits' item 1; J5 'Cause' line | Replace with two plain sentences. (1) Groq does not promise repeatable output: it turns temperature 0 into a tiny positive value, and its API reference calls `seed` best-effort. (2) Why our runs might differ is not documented for Groq: the known cause on batched servers (results change with the other requests in the batch) has not been shown for Groq's chips, so it stays UNVERIFIED until M4's repeated-generation subsample measures it (08 RK-17). Do not present the batch mechanism as fact for Groq. 06 §8.5 is the judge's check, not the generator's. In the same edit, fix the D.6 slip: top-p/top-k is not in Source C. Do not change P1-R-03. Log the Groq page as a P1_FACTS row. | low |
| 2 | **One MC-001 flashcard: 'strawberry'** (P1, now) | AIQ `02-llm-fundamentals/questions.md` Q10 and Q20 | P1 M.1 | First add `strawberry`, ` strawberry` (leading space), the quoted form and the full question 'How many r's are in strawberry?' to `p1_measure.py`, and log a new S-id. Then add the card. Front: 'In "How many r's are in strawberry?", what does gpt-oss read for the word?' Back: 'Token IDs, not letters. The tokenizer made the cut; it was learned by counting text before the model was trained, so embeddings never choose it. How many IDs depends on the character before the word: see S-new.' Do not write fixed counts on the card before logging. (Unlogged spot check, tiktoken 0.14.0, o200k_harmony: ` strawberry` = 1 token; `strawberry` and the quoted form = 3, st/raw/berry.) | low |
| 3 | **Risk note: temperature 0 on a reasoning model** (P1, now) | gpt-oss README, 'Recommended Sampling Parameters' (temperature 1.0, top_p 1.0; fetched 2026-10-09); Groq reasoning docs (general note on 0.5–0.7); AIQ `02-llm-fundamentals/README.md`, 'Decoding & sampling' | 08 Part 5 RK-17 (C); P1 lab Task 8 | Add one UNVERIFIED sub-note under RK-17: temperature 0 may be overridden, or may lengthen or loop the reasoning. Evidence so far: the O2 call at temperature 0 returned a normal short reply. For M4, also log the model id the response reports, `seed` and `system_fingerprint`; these are the only determinism controls Groq documents. Optional Task 8 field, with no assert: what Groq documents for `openai/gpt-oss-20b` on temperature, top_p, seed and the default `reasoning_effort`, with URL and date. Keep temperature 0; M4 evidence decides. | low |
| 4 | **Add `reasoning_effort` to the 06 plan** (C) | Groq API reference, `reasoning_effort`: documented default 'medium' for gpt-oss, applied by the server when the field is omitted; the groq 1.7.0 SDK omits it by default (read 2026-10-09; not measured). Also SDG `14-evaluation-and-observability/01-llm-evaluation.md`, 'Drift You Did Not Ship' | 06 §2.4, §2.5, §9.2, §8.4; C5 D.3 wording | Add `reasoning_effort: low` to the §2.4 generation block. Add `max_tokens`, `reasoning_effort` and `finish_reason` to the §2.5 `llm` object, as C5's IA-6 already does. Add `reasoning_effort` to the §9.2 generator control line. Add 'or its reasoning setting' to the §8.4 re-calibration triggers. State that the cache key's `params` include it. In C5 D.3, say 'server default', not 'SDK default'. This only records an existing decision. Today, a run that drops the field runs at 'medium' and still passes §9.2. | low |
| 5 | **Flag cut-off answers** | AIQ 08 Q14 | C5 `make_answer` flags (D.6); C6 v0 report | Add `length_stop` when finish_reason is 'length', and `unexpected_finish_reason` for any value other than 'stop'. Add one FakeGroq test: a non-empty answer with finish_reason 'length' sets the flag. The C6 report counts these flags. Today a non-empty cut-off answer is not flagged, and C5-A-03 predicts it will look like a citation failure. | low |
| 6 | **Check reasoning tokens are not counted twice** | SDG `11-infrastructure-and-mlops/04-finops-and-token-economics.md`, 'The Cost Model' | The first logged Groq call (C5 lab Task 9 or the C6 run) | One CHECK: `reasoning_tokens <= completion_tokens` whenever the field is present. If it holds, cost uses completion_tokens only. The guide's formula (output plus reasoning) would then double-count, if its 'output' means completion tokens. | low |
| 7 | **Open-coding table in Task 10** | AE Ch3, 'Open Coding: Reading and Labeling Traces' | C6 lab cell 45; C6 H.1 row 10 and M.4 | New columns: qid · Would a reader accept it? (Y/N; Groq run only) · What went wrong (first problem, your own words) · First failing stage · Trace evidence. Drop 'M5 bucket (guess)'. After all 10 rows, group the notes and name each group. Add one line: a 'Y' whose failing stage is retrieve is still a failure (06 §7.1). In M.4, say 'first open codes' instead of 'first bucket counts'. | low |
| 8 | **C7: one item and a source line** (C for the card) | AIQ `11-ai-system-design/case-studies/07-text-to-sql-agent.md`, 'Schema retrieval & pruning' and 'Evaluation plan' | 02 C7 card Ext line; seed bank (§3b seed 9); future C7 lab | C7 is a Phase 2 concept with no lesson yet and 'Ext: none'. Change the Ext line to these two sections, with a note: read only the sample-values bullet and the execution-accuracy caveats; skip the 10k-table material, the code and the few-shot store (that store is built from the golden set, so it leaks). In the C7 lab, compare result rows, not query text. Do not copy the source's `execution_match`: it ignores which column a value came from, and its `round_floats` helper is undefined. | low |
| 9 | **Register AE (and SDG, as reference only) in 01 §6** | AE Ch3 (the method source for M5) | 01 §6; 08 D-29 | See §9. This is required before the M5 lesson is written (D-29). | low |

### 3b. Seed bank, reserves and in-file additions

**Coach-only seed bank.** Make a new file, `rag_learning/sources/coach/transfer_seed_bank.md`, following the precedent of `sources/coach/O1_diagnostic_bank.md`; you OK the new file. Rules:
- Ask one question per turn, and ask for confidence (1–3) first.
- Each seed is used once: either as a lesson's scored CR-13 item (only if marked eligible) or as a review item from Day 14 on. Mark it 'used: date'.
- Never write a seed into a lesson file.

| Concept | Turns (one question each) | Source | Answer-key anchors | Use |
|---|---|---|---|---|
| P1 | 1: 'A 40-page manual of about 25,000 tokens never changes. Send all of it with every question?' 2: 'What would you compute first?' 3: 'Give one reason to retrieve anyway.' | AIQ `14-company-interview-questions/harvey.md` Q9 | Does it fit the window with an answer reserve (D.5)? About 25,000 vs about 1,100 input tokens per query, roughly 20× (D.7; confirm from usage). Book Ch1 p.12/14: RAG is overkill when the documents fit. Reasons to retrieve anyway: page citations, a growing corpus, rate limits. Corrections to harvey's key: retrieval shows what was supplied, not what was used (C5 D.4), so citations are not 'free'; and position in the prompt (lost in the middle) is a different effect from total length. | CR-13-eligible |
| P3 | 1: 'You add a sixth PDF to Corpus T. Same query, same old chunk: can its BM25 score change?' 2: 'Can its cosine score change?' | SDG `06-retrieval-systems/04-vector-databases.md`, 'The hybrid-search catch' | BM25: yes, because N, df, avgdl and rank_bm25's epsilon floor all shift (P3 D.1, D.3, D.4). Cosine: no, it depends only on the two vectors, though the chunk's rank can move. So a BM25 result belongs to one snapshot_id plus params hash (C3). | CR-13-eligible (check that the P3 file does not pose this scenario) |
| P4 | 'A guide says unrelated texts score well above zero. Our MiniLM gave −0.09 and −0.05. Who is right?' | AIQ `04-rag-and-retrieval/questions.md` Q11 | Both can be right, because scores are model-specific (P4 D.5). Never carry a threshold across models. Check Cohere separately. | Review-only (the numbers are in P4 D.5) |
| P5 | 1: 'This search() sorts its top k and passes its tests. Is it deterministic when documents are duplicated?' 2: 'How would you fix it?' | AIQ `12-coding-challenges/08_semantic_search_rag.py`, `VectorIndex.search` | There is no tie rule, so argpartition decides which tied copies get in. Sorting only the k winners by (−score, id) is **not** enough: in the review probe that still differed on 26 of 30 queries. Take every id that scores at least the k-th score, then sort by (−score, id), as `top_k` in `p5_measure.py` does. Grade with debugging_0_3 in the lab. | Review-only (the ×5-duplicated index is P5 D.3 and lab Task 5b) |
| P6 | 'A guide says Recall@k is the share of queries with a relevant chunk in the top k. Right or wrong?' | AIQ `07-evaluation-and-observability/questions.md` Q23 (same error in AIQ `GLOSSARY.md`) | That is Hit@k. Recall@k divides by all relevant chunks. The two are guaranteed equal only with one relevant chunk per query; for multi-fact items use CE@k. Self-check on P6 Part F Q1 (R@5 = 0.667, Hit@5 = 1). This targets your O1-Q04 gap. If you score 2 or less, log a new misconception. | CR-13-eligible |
| C1 | 'You have 300 PDFs. How do you find badly parsed pages without reading them all?' | AIQ 04 Q13 | Two or more cheap per-page signals (characters vs images, share of non-words, a line repeated on most pages = rule R1 in C1 D.5). Hand-check a sample stratified by document type. When the check is not needed: no questions touch the flagged pages. | CR-13-eligible (C1-T-01 is about slide decks) |
| C4 (MC-005) | 1: 'One source says missing evidence is worse than noise. Another says answers collapse past about half noise. Can both be true?' 2: 'How would you pick k for Corpus T?' | AE Ch7, 'Precision@k and Recall@k'; book Ch22 p.11–12/19 | Yes. The first is about the candidate pool a reranker trims; the second is about the final prompt. Distracting noise is the worst kind (Ch22 p.11/19). Both claims are unsourced heuristics, so measure: CE@k against context tokens on dev, at equal budget (C4 D.6 toy; 07 Part I). Together with P6's application item, this can close MC-005. | CR-13-eligible |
| C6 | 'Three stages each work 9 times in 10. How often does the whole pipeline work?' | AIQ 04 Q3 | 0.729, assuming the stages fail independently and any failure is fatal (06 §7.1 shows a memory answer can survive a retrieval miss). Self-check: below 0.9 and at least 0.7. Hence, measure each stage separately (C6 D.5). | Application item, review use (it does not fill a Transfer slot) |
| C7 | 'Your pandas filter for Chile returns zero rows. What would you check before answering zero?' | AIQ `11-ai-system-design/case-studies/07-text-to-sql-agent.md`, 'Schema retrieval & pruning' and 'Evaluation plan' | An empty result may be a filter bug, not a fact. Likely cause: the value is spelled or cased differently. Check: list the column's distinct values before filtering, and stay on the computation route (02 C7 card). Verified on upstream `data/customers-100.csv`: 'Chile' matches 1 row, 'chile' matches 0. | CR-13-eligible (keep it out of the C7 lesson when that is written) |

**Reserves.** Use a reserve only in place of a seed, never in addition, so the cap holds.
- P1: the climate version of the P1 seed ('Our whole PDF is about 12,800 tokens; v0 sends about 980. When would you skip retrieval?'; review-only). The 'does any T change the top token in the S7 table?' flashcard. A 2-merge BPE hand probe, used only if MC-001 comes back in the Part A re-run. Greedy vs sampled tokens (AE Ch12, 'Model Cascades').
- P3: two companies in one BM25 index (SDG `06-retrieval-systems/14-production-rag-at-scale.md`, 'Multi-Tenant RAG Isolation'). 'Ticket titles of 3–12 words: does k1 or b matter more?' (AIQ 04 Q12; corrected key: f is almost always 1, so k1 barely acts and b still matters). AE's 3-ticket toy (AE Ch2, 'Retrieval Fundamentals' †).
- P6: the nDCG IDCG critique in three turns (AE Ch7, 'Normalized Discounted Cumulative Gain (NDCG@k)'). Do not teach the ranking flip as general: it appears only on a 0–3 grade scale. 'A team targets P@5 above 0.8; each question has one gold chunk' (maximum 0.2; SDG `00-interview-prep/01-question-bank.md` Q5). The vendor-number critique (Anthropic's 5.7% top-20 figure vs our CE@4; verify the metric in Source C #31 first).
- C2: a non-terminating chunker as a variant of C2-A-04 (SDG `01-foundations/02-tokenization-deep-dive.md`, 'Pattern 2: Chunking at Token Boundaries').
- C4: a second MC-005 variant (AIQ 04 Q48 vs Q50).

**In-file additions.** These edit lessons that are written but not yet taught. They go through the corrections log, and you OK each one.

| What | Where in the source | Attach to | How | Effort |
|---|---|---|---|---|
| idf under a second formula (the second P3 item) | AIQ `12-coding-challenges/17_hybrid_search_and_rerank.py`, `bm25_idf` | P3 L.2 (Application) | Q1: 'Under idf = ln(1 + (N−n+0.5)/(n+0.5)), what does plastics (n = 3) get? What did rank_bm25 give?' Answer: 0.693 vs 0. Q2, after Q1 is graded: 'Does plastics now outrank climate (n = 4)?' Answer: yes, 0.693 > 0.442. A review fetch of Lucene's BM25Similarity (main branch, 2026-10-09) confirmed this idf and showed no (k1+1) factor. Log that as Source C before removing D.3's UNVERIFIED tag. | low |
| AP vs context-precision item (the second P6 item) | SDG `06-retrieval-systems/13-rag-evaluation-patterns.md`, 'How RAGAS Context Precision Works' † (the 0.835 is at line 171) | P6 L.2, new item P6-A-05; cite P6 G.1 | P6 G.1 already explains the denominator ambiguity (S11: 0.3333 vs 0.5000) and names 06's context precision as the second reading. Only the assessment item is new. Prompt 1: 'Ranking: relevant, not, relevant, not. The index holds 4 relevant chunks. What is AP@4?' (0.417). Prompt 2: 'A guide gets 0.835 and calls it Average Precision. What did it divide by?' (the 2 relevant chunks retrieved, giving 0.833; 0.835 comes from rounding 2/3 to 0.67). Compute both with the P6 script, or mark them DERIVED. | low |
| Encoder vs decoder (the second P4 item) | AIQ `02-llm-fundamentals/questions.md` Q7 | P4 Part E 'Often confused', plus one M.1 flashcard | One row: an encoder reads in both directions and outputs vectors (MiniLM, the ms-marco cross-encoder); a decoder predicts the next token (gpt-oss). Flashcard: 'Why can't MiniLM write an answer?' (it is a BERT encoder with no next-token head). Optional lab one-liner that prints the config's `architectures` (the local cache says BertModel and BertForSequenceClassification); log it. Do not imply that every embedder is an encoder. | low |
| How our embedder learned (optional; no item) | Primary: the local all-MiniLM-L6-v2 model card (HF cache), 'Training procedure'. Secondary: AIQ `01-ml-and-dl-foundations/questions.md` Q40 | P4, a sidebar after D.8 | Three sentences: contrastive training pulls true pairs together and pushes the other pairs in the batch apart. That is why this model ships a Normalize step and uses cosine. Serve with the similarity a model was trained with; DPR (Source C #19) uses dot product, so check that before citing it. | low |
| Instruction hierarchy (no item) | SDG `05-prompting-and-context/01-prompt-engineering-fundamentals.md`, 'The Instruction Hierarchy' | P7 D.8 | One or two sentences: models are trained to prefer system text over user text over retrieved text. This lowers injection but does not stop it, and v0's chunks sit in the user turn (UNVERIFIED for gpt-oss-20b). Cite Wallace et al. 2024 (arXiv 2404.13208) only after reading it. | low |

---

## 4. Do when Phase 3 (measurement) starts

Phase 3 needs Gate B. **★item** marks the new review items; there are at most two per concept. Every other row is lesson content, a lab task or a plan change. Plan changes marked (C) or (D) are listed again in §7.

**No judge call happens in Phase 3.** Everything below runs on deterministic metrics, your own labels and about 10 manual reads per version (D-10). AE Ch5's prompt-refinement loop needs judge calls on pilot or dev units. Those calls happen only inside D-10's end-of-curriculum window, before certification (§7 row 15).

**Optional AE reading (only if you answer 'read' to question 3 in §11).** Read each section right after its Ch22 page. Ask one short contrast question after each stop.

| Stop | After | AE section | Words | Why |
|---|---|---|---|---|
| 1 | Ch22 p.5/19 | Ch7, 'Mean Reciprocal Rank (MRR)' | ~290 | The U-shape refines p.5 and targets MC-004. Ignore its 'more than 30 points' figure (§8). |
| 2 | Ch22 p.10/19 | Ch5, 'Writing LLM-as-Judge Prompts' (prose only; skip the example prompt) | ~530 | The same three biases and binary judging, plus the parts of a judge prompt. |
| 3 | Ch22 p.11/19 | Ch7, 'Evaluating Generation Quality' | ~470 | Omission vs faithfulness (p.7), and the context swap (p.11). |
| 4 | Ch22 p.13/19 | Ch5, 'Data Splits for Designing and Validating LLM-as-Judge' | ~360 | Set size depends on purpose, against the single '200–500' rule. Explains 06 §8.4's ≥30/≥30. |
| 5 | Ch22 p.18/19 | Ch3, 'Open Coding: Reading and Labeling Traces' (the example table can be skimmed) | ~1,260 | Turns the ~10 reads per version into notes on the first failure. Feeds M5. |

Total: about 2,900 words, roughly 30–40 minutes with stops. 'Pieces' means stops 3 and 5 only (~1,700 words). Three warnings:
- AE Ch7 writes questions from chunks and stores chunk ids as gold; the course uses character spans (06 §6.3–6.4).
- AE Ch7's IDCG differs from 06 §7.3, and the export has a typo ('log2(23)' should be log2(3)).
- Do not read AE Ch5 'Estimating True Success Rates with Imperfect Judges' until the final judge batch.

### M1: building the eval set

| What | Where in the source | Attach to | How | Effort |
|---|---|---|---|---|
| ★item Critique: questions written from chunks | AE Ch7, 'Synthetically Generating Query-Answer Pairs' (Fig 7-2) | M1 Part G row, plus one T item in two turns | (a) 'Gold labels are chunk ids from 1,000-character chunks. You switch to 400-character chunks. What breaks?' (the old ids vanish or point at other text; so use spans). (b) 'Even with spans, which chunker does such a question set favour?' (the original one; copied wording also favours BM25, per the 06 §6.3 overlap rule). Describe choose_chunk_size cell 12 as a ceiling of LLM-judged scores (1.00/1.00, stale output), not a BM25 score. | low |
| Coverage grid | AE Ch3, 'Defining Dimensions' and 'Generating Tuples and Queries' | M1 lesson only (no 06 edit) | Cross question category (06 §6.2) with page region (thirds of the corpus). Each category should appear in at least 2 regions; this fixes the q_a.json pp.1–5 flaw (06 §6.8). If an LLM drafts questions, use two calls: tuples first, then one question per tuple from whole pages. Store the tuple in `tags`. | low |
| Near-duplicate distractor recipe | AE Ch7, 'Creating Harder Synthetic Queries' | M1 lab task | Write 2 items for Corpus T. Pick a target span. Find distractor pages with a search that favours neither retriever (grep plus reading), and record the method. Then you, not an LLM, write the question and check by grep that only the target answers it. Bonus: reuse the same pages for one tempting unanswerable item. | low |
| Leakage rule (C) | AE Ch9, 'Common Mistakes with CI'; AE Ch12, 'Low Effort: Prompt Refinement' | 06 §6.3 leakage bullet | No eval question, gold quote or calibration unit may appear in any prompt. The automated check comes later (§5, at the first prompt with examples). | low |
| Self-agreement sample (C) | AE Ch4, 'Percent Agreement: Simple but Misleading' | 06 §6.5 | Keep the random 20% (it serves page agreement and span IoU), and add up to 5 unanswerables. Report the 2×2 counts. Report κ only when each label has at least 5 items in both passes, marked 'stratified'; otherwise write 'κ not estimable'. | low |
| Adjudication fields | AE Ch4, 'Techniques for Improving the Rubric' | ADJUDICATION.md template | For each disagreement, record: the rubric word that allowed both readings; the fix (clarify, add example, decision rule, split, or tiebreaker); the rubric version and date. | low |

Reserve (M1): 'Generate 200 questions automatically, then review a sample' (SDG `06-retrieval-systems/13-rag-evaluation-patterns.md`, 'Building Golden Test Sets'; key: our LLM drafts come from whole pages, and every item is verified, per D-09). 'Your judge disagrees with your labels. Name one cause besides an unclear rubric' (AIQ harvey.md Q3, derived).

### M2: retrieval metrics harness

| What | Where in the source | Attach to | How | Effort |
|---|---|---|---|---|
| ★item High Hit, low correctness | AIQ 07 Q22 (follow-up) | M2 L.3 Transfer | 'Hit@4 is 0.95 but answer correctness is 0.70. Where do you look first?' Check CE@4 first, then generator-side causes, then read the traces. Before D-10, correctness comes from EM/F1 or human labels. | low |
| Hubness diagnostic (not a decision metric) | AIQ `01-ml-and-dl-foundations/questions.md` Q43 | M2 lab task | On dev, count for each chunk (a) how many questions have it in the top k and (b) for how many of those it is gold. Compare with the even-spread base rate (questions × k / chunks). List the top 5. A chunk retrieved often but rarely gold is a hub candidate. | low |

Reserve (M2): 'Evidence reaches the top 50 for 95% of questions but the top 5 for 60%. Where is the problem?' (AIQ 04 Q43 follow-up; key: compare the same k before and after reranking, or prev_rank). 'Your gold set stores chunk ids. You change chunk size. What breaks?' (AIQ databricks.md Q4, derived).

### M3: generation metrics and the judge

| What | Where in the source | Attach to | How | Effort |
|---|---|---|---|---|
| ★item A checker that always says 'supported' | AE Ch4, 'Percent Agreement: Simple but Misleading' and 'Cohen's Kappa: Adjusting for Chance'; the base-rate idea from AIQ harvey.md Q2 (derived) | M3 Part L, as an A item in three turns | 'A checker always says supported. 10 of 100 claims are unsupported.' Turn 1: agreement? (0.90). Turn 2: κ? (p_e = 0.90, so κ = 0). Turn 3: failure-catch rate? (0/10). Lesson: high agreement, useless checker. This replaces every raw-agreement item proposed in the draft. | low |
| ★item Faithful but incomplete | AE Ch7, 'Evaluating Generation Quality'; book Ch22 p.7–9/19 | M3 Part G mapping, plus one T item in two turns | Mapping: hallucination → unsupported claim; misinterpretation → contradicted claim (human labels); omission → completeness, not faithfulness. Turn 1: 'Every claim is supported, but half the facts in the context are missing. What is faithfulness?' (1.0). Turn 2: 'Which metric catches the gap?' (completeness, human-labelled until D-10; only for facts in the reference answer). | low |
| How κ works (content, no item) | AE Ch4, 'Cohen's Kappa: Adjusting for Chance' and 'Interpreting Kappa Scores' | M3 Part D box, Part F hand table | Explain p_o, p_e from each rater's label frequencies, and κ. Work one hand 2×2 with course-made numbers. Never reuse AE's 0.81 figure or its kappa function, which returns 1.0 when κ is undefined. | low |
| Reference-based vs reference-free (content, no item) | Book Ch22 p.10/19 first; AE Ch2, 'Evaluation Setups' > 'Absolute Evaluation' | M3 Part D table | Sort the 06 §7.4 metrics. Reference-based: CE@4, token F1, citation page-hit. Reference-free: faithfulness and citation precision, which still need the retrieved context. | low |
| Write the rubric from what you see | AE Ch1, 'The LLM Evaluation Lifecycle: Bridging the Gulfs with Evaluation'; AE Ch3, 'Putting It Together' | M3 lab (the 06 §8.4 pilot) | Write a one-line note beside every partial or wrong pilot label. Then write the rubric's definitions of 'partial' and 'wrong' from these notes plus the Task 10 notes. Labels and units stay as in 06 §8.4. | low |
| 'Not a failure' list | AE Ch4, 'Techniques for Improving the Rubric' | M3 pilot rubric | Examples: a faithful paraphrase counts as supported; citing either of two pages that both hold the fact counts as supported (matches the OR alternatives in evidence_groups). Whether a claim needing outside knowledge (a unit conversion, say) counts is your [P] call. | low |
| Failure class per metric (C) | AE Ch5, 'Writing LLM-as-Judge Prompts'; AE Ch3, 'Common Pitfalls' | 06 §8.4 first bullet | Faithfulness failure = an unsupported or contradicted claim. Citation failure = the excerpt does not support the sentence. For correctness, you decide before labelling whether 'partial' counts as a failure. | low |
| Judge certification rule and who labels (D) | AE Ch4, NOTE in 'When to Use Other Metrics'; AE Ch5, 'Iterative Prompt Refinement for the LLM-as-Judge'; SDG `13-reliability-and-safety/02-ensemble-methods.md`, 'Panel of LLM Judges (PoLL)' | 06 §8.4, D-10, RK-03, A-11; M3/V4 cards | See §7 rows 12 and 14. Use the plain names 'failure-catch rate' and 'pass-keep rate'. Map them once to AE: AE treats Pass as the positive class, so AE's TNR is our failure-catch rate and AE's TPR is our pass-keep rate. | medium |
| Labelling helper | AE Ch10, 'Essential Interface Elements' and 'An Example Walkthrough' > 'A Simple Custom UI' | Course tooling supplied by the tutor before the M3 pilot (not mastery evidence) | A small CLI or notebook showing one dev trace at a time. Keys c/p/w/d; bucket tags; a one-line rationale required for p and w. Appends to labels.jsonl (qid, run_id, label, labeller, rubric_version, …). It has a blind mode that hides earlier labels, Codex labels and the run identity, plus a batch import for Codex labels. | medium |
| 'Defer' label; re-label the early pilot (C) | AE Ch10, 'Features That Improve Review Speed and Quality'; 'Case Study: EvalGen' | 06 §8.4 | See §7 row 18. | low |
| Schema-valid is not correct (content) | AE Ch8, 'Stage 2: Argument Generation' (example corrected) | M3 Part J line | Parsed JSON can still hold a wrong but allowed value; only labels or a confusion matrix catch it. Show a corrected Pydantic example (`dt.date`), never AE's version. | low |
| Which ~10 answers to read (D) | AE Ch10, 'Selecting Traces for Human Review' | 06 §4.1 rule 6, §9.1, D-10 | See §7 row 19. | low |
| How reliable are your answer labels? (C) | AE Ch4 (the concept); AIQ 07 Q30 | M3 pilot, and again before the final batch | See §7 row 20. | low |
| EM/F1 test cases (lab) | AIQ `12-coding-challenges/12_eval_metrics.py`, `normalize_answer` and `token_f1` | M3 lab CHECK cells | You write normalize, EM and F1 from a blank file. CHECKs: the 06 §7.4 toy (0.333); 'cat cat cat' vs 'cat' = 0.5; both sides empty = 1 (the SQuAD 2.0 convention); one side empty = 0; articles only = 1. Decimal trap: against D-001's gold '1.2 degrees', a wrong '12 degrees' must score EM 0 (§7 row 11). | low |

Reserve (M3): 'You and another labeller agree on 90%, and 90% are Pass. Is the rubric clear?' A sorting item on reference-based vs reference-free. 'What is criteria drift, and why are the first 30 labels only a pilot?' 'Why is κ alone a weak pass rule?' 'On Corpus D, CE@4 is 0.55 but correctness is 0.85. Good news?' (AIQ 07 Q22 follow-up). The 'vague answers inflate faithfulness' item is counted under V3.

### M4: experimental discipline

| What | Where in the source | Attach to | How | Effort |
|---|---|---|---|---|
| ★item Regression set vs eval set | AE Ch9, 'CI: Building a Safety Net Against Regressions'; book Ch22 p.15/19 | M4 R item | 'Name two differences between the regression set and the eval set.' Criteria: purpose (catch known breakage vs estimate and compare quality); composition (picked from failures vs balanced and frozen); a pass only shows that known cases still work. | low |
| ★item Is +4 real? | AIQ 07 Q41 | M4 A item | 'Same questions: 10 got better, 6 got worse. Is the +4 real?' Only the 16 discordant questions count. The exact two-sided sign test gives p ≈ 0.45, so this is not evidence; read the 16 traces. | low |
| Regression set is a smoke test (C/D) | AE Ch9, 'CI: …' and 'Common Mistakes with CI'; SDG `16-case-studies/18-eval-gated-cicd.md`, 'Failure Modes and Mitigations' F6; AIQ `15-role-guides/qa-sdet-engineer.md` Q12 (secondary) | 06 §9.6 | See §7 row 21. | low |
| Per-qid flip report (lab code) | SDG `16-case-studies/18-eval-gated-cicd.md`, 'Key Design Decisions' §8 | `test_retrieval_does_not_regress` | Print the qids that went 1→0 and 0→1 against the champion. A tolerance on the mean hides flips that cancel out. Show holdout changes only as counts. | low |
| Generator flip rate (lab) | 08 RK-17; AIQ 08 Q11 | M4 lab | Rerun about 10 dev items twice with the cache off, and count changed answers. Count empty answers and finish_reason 'length' in the v0 traces, split by answerable vs unanswerable. Log the returned model id, `seed` and `system_fingerprint`. The result feeds the T2 tolerance and RK-17. | low |
| Embedding canary (C) | AE Ch9, 'Revisiting Prompts When Models Improve' †; AIQ 04 Q15 | M4 runner; one 06 §9.2 line | Embed 3 fixed strings with the cache bypassed, and stop if the vectors drift beyond a tolerance set from two runs. This catches a silent provider change that would mix two vector spaces. Whether Cohere or Groq ever change a model silently is UNVERIFIED. | low |
| Prompt format as a hidden variable (content) | AIQ `03-prompt-engineering-and-context/questions.md` Q47 | M4 list of uncontrolled variables | Add 'formatting changed along with the wording (separators, labels, field order)'. Verify Sclar et al. (ICLR 2024) before citing it. | low |

Reserve (M4): 'Two items go 1→0 and two go 0→1 at TOL 0.02. Does the test pass?' (yes, which is why the list is needed). '12 categories each tested at 5%: chance of at least one false alarm?' (1 − 0.95¹² ≈ 0.46). 'B beat A on 2 of 20, and B also changed the separator. What can you conclude?' The '95% accuracy' checklist, asked one question at a time (SDG `00-interview-prep/01-question-bank.md` Q74). The flywheel critique (AE Ch9, 'The Continuous Improvement Flywheel' †). Optional reading: Miller 2024, 'Adding Error Bars to Evals' (arXiv 2411.00640; verify before citing).

### M5: failure analysis

| What | Where in the source | Attach to | How | Effort |
|---|---|---|---|---|
| ★item Flashlight vs reading traces | AE Ch3, 'Putting It Together'; book Ch22 p.18/19 | M5 X-T item | 'Ch22 calls manual testing a flashlight. AE says read traces first. Do they disagree?' They do different jobs. Systematic reading decides what to measure; ad-hoc 'looks right' checks are not measurement; reading alone can never show that a change helped. | low |
| ★item Prompt gap or ignored rule? | AE Ch1, 'The Gulf of Specification (Between the Developer and the LLM Pipeline)'; AE Ch5, 'Defining the Right Metrics (What to Measure)' | One M5 lab column (generation rows only), plus one T item | Column: 'Did answer_v1 ask for this behaviour?' T item: 'A v0 answer picks one meaning of an ambiguous question. Prompt gap or ignored rule?' (a prompt gap: answer_v1 has no ambiguity rule; see §7 row 7). | low |
| The M5 method (C for the card edit) | AE Ch3, 'Open Coding…', 'Axial Coding: Structuring Failure Modes', 'Labeling Traces with Structured Failure Modes', 'A Note on Exhaustive Labeling', 'Iteration and Refinement'; book App p.4/23 | 02 M5 card outcome; M5 lesson Part D; M5 lab | See the box below. | medium |
| Context-swap probe | AE Ch7, 'Evaluating Generation Quality' | P7 Part I, as a separate probe S (not a fifth arm) | For 20 dev items, replace the top 4 with an unrelated-topic context from outside Corpus D. Score deterministically: abstention rate and 'correct under swap', cross-tabbed with closed-book. About 20 Groq calls. Read with Ch22 p.11–12/19. | low |
| Oracle-context and full-context controls (D) | SDG `06-retrieval-systems/14-production-rag-at-scale.md`, 'Failure Modes and Debugging'; book Ch1 p.12/14 | 06 §7.1, v0.1 | See §7 row 23. | medium |

Reserve (M5): 'Why note only the first problem in each trace?' 'A team's collection grows from 1 PDF to 10, and old answers get worse. What do you measure first?' (AIQ `14-company-interview-questions/cohere.md` Q5, as a new scenario). 'When should failure categories be frozen?' (AE Ch3, 'Common Pitfalls'). 'An FAQ says most RAG failures are retrieval failures. Is that true for v0? Show it from your bucket table.' 'Which outcome can a triad table not show?' (SDG `06-retrieval-systems/13-rag-evaluation-patterns.md`, 'Triad Failure Modes' †).

**The M5 method (one box):**
1. Read each failing v0 dev trace. Write one note on the first (most upstream) problem, and mark it acceptable Y/N. You write every note yourself; no LLM.
2. Run quick checks before grouping (AE Ch11, 'Beyond Clustering'). List items with finish_reason other than 'stop', or an empty answer. Flag reasoning-token outliers above Q3 + 1.5·IQR on a log scale; this is a reading list, not a verdict. Add a column 'gold rank in the full ranking' (exact search over all chunks is cheap).
3. Group the notes by hand. Name each group with an 02 M5 bucket or a book symptom family (App p.4/23), or give it a new name. Candidates already visible: false abstention; output error (empty or cut-off answer); omission (evidence in context, not used); ambiguity handling; label error (goes to ADJUDICATION.md); unmapped; hub chunk (a sub-tag of rank). Split rule: keep two groups apart if they would pick different 06 §4.2 cards.
4. Count, with trace IDs. For buckets that drive decisions, mark every bucket present in a trace (0/1), not only the first, using a small `all_failing_checks(trace)` built from C6's ladder.
5. Stop rule: stop when a block of 10 traces adds no new kind of failure AND re-coding changes no label. Otherwise write 'taxonomy provisional'. Read only dev and analysis-only traces, never test or holdout (§7 row 5). Add unlabelled questions 10 at a time.
6. AI help: Claude or Codex may load, filter, plot and search traces, but you fill the bucket column first. Any cause an AI proposes goes in a 'hypothesis' column until you check it against the trace (AE Ch11, 'Using AI Coding Assistants'). Write this rule in the M5 lesson file itself, because the workspace has no AGENTS.md for Codex to read.

This partly closes 08 D-29 by giving M5 a method source. The RAG-specific failure-points literature stays UNVERIFIED.

---

## 5. Later phases (4–12) and optional reference

Items are capped at 2 per concept. **★item** marks review items; other rows are content or lab work.

| What | Where in the source | Attach to | How | Effort |
|---|---|---|---|---|
| Re-read items that fail everywhere | AIQ 07 Q14, Q52 | I1 lesson / v1.0 summary | Before reporting the grid, list items with CE@k = 0 under every setting and re-read their gold spans. Log any fix in ADJUDICATION.md; that creates a new dataset version. | low |
| ★item Semantic chunking: book vs guide | Book App p.6/23 vs AIQ 04 Q4 | I3 L item | 'The book calls semantic chunking a quick win; a guide calls it marginal. How do we settle it?' Run v1.3 on dev at equal k and equal token budget, per bucket. | low |
| ★item Cost ladder for contextual headers | SDG `06-retrieval-systems/10-contextual-retrieval.md`, 'Pattern 2: Cost-Optimized with Prompt Caching' and 'Pattern 3' | I5 Part K, one A item | Three rows: a plain header (0 LLM calls); one call per document (the repo's CCH titles from the first 4,000 tokens); one call per chunk that carries the whole document. Compute the LLM-arm input tokens from P1 and C2 counts. Hand-check 10 generated contexts. | low |
| ★item Vendor number vs our metric | SDG `06-retrieval-systems/10-contextual-retrieval.md`, 'The Problem: Context Dilution' †; Source C #31 | I5 Part L | 'A vendor says 5.7% of relevant chunks were missing from its top 20; we report CE@4. Which system is better?' You cannot tell: k, the unit and the corpus all differ. Check the metric definition in C#31. | low |
| Late chunking (cannot run here) | SDG `06-retrieval-systems/02-chunking-strategies.md`, 'Late Chunking and Contextualized Chunk Embeddings' † | I5 Part E, one row | It helps the dense side only and needs token outputs from a long-context embedder. Cite Günther et al. 2024 after verifying it. | low |
| ★item RRF under rescaling | AIQ `12-coding-challenges/17_hybrid_search_and_rerank.py`, tests 3–4; book Ch12 p.7–9/14 | R1 Part F hand example, one L.2 item, lab CHECK cells | Lists [0,1,2,3,4] and [4,1,3,2,0] fuse to [1,0,4,2,3] at k=60 and [0,4,1,2,3] at k=0 (ties broken by the smaller id). Item: 'BM25 + 100 × dense vs RRF: which can change its winner if one scorer is rescaled?' Do not reuse `rank_by_score`, which drops dense scores of 0 or below. | low |
| ★item Fresh R1 scenario: fusion over different units | SDG `16-case-studies/01-enterprise-rag.md`, 'Hybrid Retrieval' | R1 CR-13 seed | 'BM25 indexes whole documents, vectors index chunks, and RRF fuses by chunk id. What goes wrong?' The keyword side never matches anything. Test that every fused id exists in the shared chunk catalogue. | low |
| BM25-first vs dense-first | AE Ch2, 'Retrieval Fundamentals' † | R1 Part G, one line | AE recommends BM25 as the first baseline; our v0 is dense-first on purpose. | low |
| ★item Filters that starve the list | AIQ 04 Q23 | R2 L item; one Part J line | 'You take the top 4, filter to one document, and get 1 back. Why?' If a filter empties the list, log it as an error and never score it as a correct abstention. | low |
| ★item Candidate pool vs reranked list | AE Ch7, 'Overview' (Fig 7-1); book Ch13 p.5/13 | R3 recall item | 'What do you measure on the candidate pool, and what on the reranked top-k?' Pool → CE@pool, the ceiling. Reranked list → MRR@10, with Hit@4 and CE@4 as guards. | low |
| ★item Chunks longer than the reranker reads | AIQ `14-company-interview-questions/cohere.md` Q1 follow-up † | R3 T item | The tail is silently cut. Compare chunk token length with the model's max length (06 §3.2). | low |
| MaxSim sidebar | SDG `06-retrieval-systems/11-late-interaction-colbert.md`, 'The Retrieval Architecture Spectrum' and 'MaxSim: The Core Scoring Mechanism' | R3 Part D/F; reuse in S2 | Three points (bi-encoder, late interaction, cross-encoder) anchored on Ch13 p.6–7/13, plus a 2×3 hand computation. Primary source: C#35. | low |
| Pointwise vs listwise LLM reranking | SDG `06-retrieval-systems/06-reranking-strategies.md`, 'Listwise vs Pointwise LLM Reranking' † | R3 'often confused' row (fills 04 DV-29) | Classify the repo's three LLM rerankers. Cite RankGPT (arXiv 2304.09542) after verifying it, not the guide, whose sliding window runs the wrong way. | low |
| MMR tests | AIQ `12-coding-challenges/17`, tests 5–6 | R4 lab | Max vs mean redundancy as a debugging task. λ = 1 equals plain top-k only with the (−score, chunk_id) order. | low |
| ★item Condense a follow-up into one question | AE Ch6, 'Isolating Failures'; Laban et al. 2025 (arXiv 2505.06120; abstract checked) | Q1 Part L T item; Part G line; 01 §6 row | 'After a turn about the Paris Agreement, "When was it adopted?" gets the wrong year. What test shows whether history or retrieval failed?' Run the standalone D-002 question through the same pipeline. A right answer alone does not clear retrieval, because the model may know the date from memory. | low |
| Isolate a failing multi-hop question | AE Ch6 (adapted) | Q1 Part J row, about 10 lab lines | Check each sub-query's own evidence group deterministically. | low |
| Few-shot leakage test | AE Ch9; upstream `query_transformations.ipynb` cells 14 and 16 | The first prompt with examples (I4 or Q1) | A T1 test that flags any 8-word n-gram shared by a prompt template and an eval question or gold quote, plus an injected leak to prove it fails. Cells 14 and 16 are the anti-example: the few-shot example is the very query that is run. | low |
| Empty-context path | AIQ 03 Q9 | X3 lab unit test | If no chunk survives the budget or a filter, return the fixed abstention without calling the LLM, and record reason `no_context`. Also count `[n]` reference markers in Corpus T. | low |
| ★item Conflicting sources | AIQ 03 Q30 † | X3 T item | 'Two retrieved chunks give different values; one comes from an older document. What should the prompt say?' Put the source and date in each block header; either report both values or prefer the newer, and say which rule was used. | low |
| ★item Critique a guardrail design | SDG `13-reliability-and-safety/01-guardrails.md`, 'Factuality Check (for RAG)' | V2 T item | An NLI check over a truncated whole context lets unsure 'neutral' claims pass, and long premises get cut (P1 D.4). | low |
| ★item Why models rarely say 'I don't know' | AIQ 02 Q50; Kalai et al. 2025 (arXiv 2509.04664; abstract checked); book Ch3 p.11/14 | V3 Part B paragraph, one item, Source C row | 'If a wrong answer and "I don't know" both score 0, why would a model ever abstain?' Guessing never loses under such grading; our abstention metrics (06 §7.4) score it separately. | low |
| ★item Phrase list vs exact refusal sentence | SDG `13-reliability-and-safety/01-guardrails.md`, 'Abstention Strategy' | V3 T item | 'Which error does each make?' A phrase list flags hedged correct answers and misses unlisted refusals; our exact sentence misses paraphrased refusals (P7 D.7). | low |
| Risk-coverage curve (optional) | AIQ 04 Q60 | V3 lab plot | Sweep the threshold on dev. Fitting a threshold per category is impossible at n = 4–10. The unanswerable D-010 scored 0.5196, above 5 of the 8 answerable items. No threshold claim before ≥15 unanswerables. | low |
| ★item Two LLMs agreeing does not certify a judge | SDG `13-reliability-and-safety/02-ensemble-methods.md`, 'Panel of LLM Judges (PoLL)' | V4 T item | 'Codex and the Cohere judge agree on 95% of claims. Is the judge certified?' No: two LLMs can share blind spots. Certify against your labels (§7 rows 12 and 14). | low |
| Corrected judge rate (sensitivity only) | AE Ch5, 'Estimating True Success Rates with Imperfect Judges' | Final batch | §7 row 15(h). Version decisions stay on paired raw labels. | medium |
| ★item Replay after a prompt edit | AIQ 07 Q50 † | D1 T item | 'Your replay test passes after you edit the prompt. What did it prove?' Only that unchanged paths reproduce; a changed prompt is a cache miss. | low |
| ★item Never cache answers by similarity in eval runs | AIQ `12-coding-challenges/16_semantic_cache.py` | D2 T item | 'Someone proposes reusing an old answer when a new question is very similar. Why would that break our evaluation?' Paraphrase variants would get their base item's answer. The exact LLM cache key (06 §2.4) is safe. | low |
| ★item Tail latency compounds | AIQ 08 Q3, Q15 | D2 A item | 'A query makes 7 sequential calls; each is slower than its own p99 1% of the time. What share of queries hit at least one slow call?' 1 − 0.99⁷ ≈ 6.8%; state the independence assumption. | low |
| Latency and cost mechanics (content and lab) | SDG `01-foundations/06-inference-pipeline.md`, 'Prefill and Decode Phases' †; SDG `11-infrastructure-and-mlops/04-finops-and-token-economics.md`, 'The Cost Model' †; book Ch22 p.14/19 | D2 Part D and lab | The prompt is read in one parallel pass; each output token, reasoning included, is a sequential step. Fit latency against completion tokens over all v0 traces (calls do not stream, so time to first token is not seen). Cost per query = cost per call × calls × (1 + retries), using completion_tokens only. Report the length-stop count per version. | low |
| reasoning_effort low vs medium | AIQ 02 Q42 | D2 lab, after Gate C | A one-variable ablation with deterministic metrics plus about 10 reads per arm. | medium |
| Orphan test after removing a document | SDG `06-retrieval-systems/14-production-rag-at-scale.md`, 'Index Maintenance' † | D3 lab | After removing a document, no chunk, vector or BM25 posting with its doc_id may remain. | low |
| D4 package | See the D4 box below | D4 lesson and lab | | medium |
| Router error types; oracle ceiling (★item) | AE Ch8, 'Stage 1: Tool Selection'; AIQ 07 Q38 † | A1 Part J, lab, one T item | A wrong but valid route shows only in the confusion matrix. A label outside the set is caught by the enum (the repo's `adaptive_retrieval.ipynb` cell 19 raises KeyError). Run every strategy on dev for the oracle ceiling. Item: 'Your router returns "factual" in lower case and the run crashes. Which error is this, and what catches it before dispatch?' | low |
| ★item Adaptive-loop checklist | SDG `06-retrieval-systems/08-agentic-rag.md`, 'Adaptive Retrieval Effort' † | A1 X item | 'Draw any adaptive loop from memory: which four parts must it have?' (a cheap first pass, a sufficiency check, a cap on escalations, a failure path). | low |
| Failures counted per route; CRAG critique (★item ×2) | AE Ch8, 'The Transition Failure Heatmap'; AIQ 04 Q37 (diagram); book Ch20 p.5/11 | A2 lab, two items | Two Counter tables (route × first failing stage; totals per route), as counts with denominators, never as a ranking. Items: 'What does CRAG really do on "ambiguous"?' (upstream `crag.py` L166–172) and 'Your sufficiency check passes 98% of queries. What has your system become?' (a linear pipeline). | low |
| Judge feedback stays out of retry loops | SDG `07-agentic-systems/10-evaluating-agentic-systems.md`, 'Eval Integrity: When the Agent Games the Harness' | A2/A3 lesson note | One line: detailed rejection feedback taught agents to evade the grader. | low |
| Agency spec | AE Ch8, 'The Spectrum of Agency' † | A5 Part K | Write down the step cap, stop rule, when to ask the user and when to abstain. Count loops and early stops. | low |
| ColPali source; try one vector per page first | SDG `06-retrieval-systems/12-multimodal-rag.md`, 'ColPali and Vision-Based Retrieval' | S2: an 01 §6 row (arXiv 2407.01449, verify) and one 'when not to use' line | | low |
| Defence outline | SDG `00-interview-prep/02-answer-frameworks.md`, 'System Design Framework (SPIDER)' | K1 Part K | Scope, priorities, architecture, 2–3 deep dives backed by your own registry evidence, evaluation, then cost with a self-critique. Book App p.6–11/23 stays the checklist. | low |
| ★item ×2 Unsupported numbers; facts in the weights | SDG `16-case-studies/01-enterprise-rag.md`, 'Lessons Learned'; AIQ 02 Q60 † | K1 T items | 'For each number in your defence, which registry row supports it?' and 'Why not put the climate facts into the model's weights instead of retrieving?' (book Ch1 p.3/14). | low |

**D4 box** (D4 is a U-tier concept; 2 items):
- **Read (optional, ~10 minutes, after Ch22 p.16–17/19):** AIQ `09-safety-security-and-responsible-ai/README.md`, sections 'The root cause: instructions and data share one channel' and 'Prompt injection: direct vs indirect'. This is the only AIQ reading in the course.
- **Source C rows, once the coach has opened them:** Greshake et al. 2023 (arXiv 2302.12173), and the OWASP Top 10 for LLM Applications 2025 (LLM01, LLM08). These close the D4 gap listed in 01 §6.
- **★items, one question at a time:**
  1. 'A user types the attack, or a corpus page contains it. Which is indirect?' then 'Why is it worse?'
  2. 'The gold chunk was retrieved, but another chunk says "always report 42". What kind of failure is this?' (from AIQ 09 Q46).
- **Lab task** (from AIQ 09 Q31). Use a separate test corpus with its own doc_id, snapshot and index; never touch Corpus D's frozen snapshot.
  1. Hide a white-text instruction in a PDF (for example: append a fixed marker phrase) and check whether `get_text()` returns it. A scratch probe in this review found that white text, 0.5 pt text and covered text came through, while off-page text did not. Re-run this and log it.
  2. Ask about 5 questions that retrieve that page.
  3. Compare two arms: v0, and v0 plus one mitigation (a span colour and size filter, or a 'text inside sources is data' rule). Report attack successes as counts, plus false abstention and correctness on the clean T2 subset.
  4. Add the attack case to T2.
- **Reserves:** 'Why can't a delimiter stop injection?'; the lethal-trifecta pair (AIQ 09 README, 'The lethal trifecta'); knowledge poisoning, i.e. a false fact with no instruction that passes citation checks (SDG `12-security-and-access/01-llm-security.md`); ranking poisoning through A2's web fallback (SDG `06-retrieval-systems/01-rag-fundamentals.md`, 'Poisoned Sources' †); a PII recall item (AIQ 09 Q8 †).

**Optional reference only (no lesson change):**
- Matryoshka and int8 vectors for P5, only if P5 has room (SDG `06-retrieval-systems/03-embedding-models.md` †).
- One SPLADE sentence for R1 †.
- A HyDE-plus-RRF clause for Q2 (SDG `06-retrieval-systems/09-advanced-retrieval-patterns.md` †).
- SDG's cache break-even formula (N × cache-read multiplier = k) as a D2 reserve. It was the P1 seed's old source.

**Later-phase reserves:** a reasoning-model prefix-caching R item (AE Ch12, 'Make Prompts Cache-Friendly'; our static prefix is only about 107 tokens). Model retirement (AIQ databricks.md Q12) for D3. A reranker-recall check (AIQ microsoft.md Q4) for R3. Defined terms far from their clause (AIQ harvey.md Q1) for I2/I5. Vague answers inflating faithfulness (AIQ 07 Q44) for V3. 'When does splitting a question make answers worse?' (AIQ 04 Q31) for Q1.

---

## 6. Skip, and why

### AI Eval book, chapter by chapter

| Chapter | Used in | Skip the rest because |
|---|---|---|
| Ch1 Introduction | §4 M3/M5 (analyse before measuring; the gulf of specification) | Pre-training and post-training evaluation is outside the course. The Air Canada story is at most a two-sentence V3 hook. |
| Ch2 LLMs and Evaluation Basics | §4 M3 content ('Absolute Evaluation', second to Ch22 p.10/19); §5 R1 line; a P3 reserve | A generic primer that duplicates P1, P7 and C5. Its code uses OpenAI models and gets message roles wrong. Tools and agents are off the critical path. |
| Ch3 Error Analysis | §3a (C6 Task 10); §4 M1 grid; §4 M5 method; reading stop 5 | Core; nothing skipped. |
| Ch4 Collaborative Evaluation | §4 M1/M3 (κ mechanism, rubric repair, judging a judge) | The multi-annotator workflow, alignment sessions, Fleiss κ and Krippendorff α serve teams; you are one labeller. |
| Ch5 Automated Evaluators | §4 M3 (failure class, certification); §7 rows 12–15; reading stops 2 and 4 | Its bias list duplicates 06 §8.2 and misreports Zheng et al. Group-wise metrics duplicate P6. 'Estimating True Success Rates…' waits for the final batch. |
| Ch6 Multi-Turn | §5 Q1 (condense a follow-up) | The course is single-turn by decision D-21. Perturbation testing duplicates the paraphrase variants. |
| Ch7 Evaluating RAG | §3b (C4 seed; P6 reserve); §4 (M1 critique, distractor recipe, M3 omission, context swap); §5 R3; reading stops 1 and 3 | Its metric formulas are weaker than P6 (its IDCG is the J2 bug). The realism rater adds a judge call before D-10. Its 'lost in the middle' figure is overstated against Liu et al.'s tables (§8). The promised grid-search section is missing. |
| Ch8 Tool Use and Agents | §4 M3 (schema-valid is not correct); §5 A1, A2, A5 | The PDF, long-document, image and MCP sections are covered better by C1 and X3, or are out of scope. |
| Ch9 CI/CD | §4 M1 (leakage), M4 (smoke test, canary); §7 row 21 | Online monitoring and guardrails need production traffic, and Ch22 p.15/19 already covers the concept. |
| Ch10 Interfaces for Human Review | §4 M3 (labelling helper, defer, reading rule) | The EvalGen and DocWrangler case studies and team-workflow plumbing do not apply. |
| Ch11 Data Analysis for Traces | §4 M5 (quick checks; AI-help rule) | Clustering and semantic search over traces are overkill at about 55 items. |
| Ch12 Improving LLM Agents | §3b P1 reserve; §4 M1 (leakage); §5 reserve (prefix caching) | Cascades, fine-tuning, distillation and batching are out of scope. Its chain-of-thought advice conflicts with 06 §3.3 for a reasoning model. |

### ai-system-design-guide (pinned ed955b2), one line per top-level folder

'Headings only' marks verdicts that rest on files nobody opened.
- `00-interview-prep`: skip as reading. Mined: Q5 (P6 reserve), Q74 (M4 reserve), Q115 (§7 row 9), SPIDER (K1). Q78 has errors. Most of `01-question-bank.md` and all of `05` and `06` were read as headings only.
- `01-foundations`: skip. `02`, `05` and `06` were read; `01` was skimmed. Tokenization and embeddings duplicate P1 and P4. Only the prefill-vs-decode note (D2) is used.
- `02-model-landscape`: skip (headings only). It is an October 2026 model and price catalogue that cannot be checked.
- `03-training-and-adaptation`: skip (headings only). Fine-tuning and RLHF are out of scope.
- `04-inference-optimization`: skip. `02` and `07` were read; the rest is headings only. GPU serving does not apply to a hosted API.
- `05-prompting-and-context`: skip, except one instruction-hierarchy sentence (P7). `01`, `05`, `06` and `08` were read; **`02`, `03`, `04` and `07` are headings only**.
- `06-retrieval-systems`: reference only; all 15 files read. About 10 small items were mined (§3–§5). Many dated claims, plus the errors in §8.
- `07-agentic-systems`: no change for Phases 0–9. `10-evaluating-agentic-systems.md` was read in full and gives one A2/A3 note; the other files are headings only. Revisit only if A5 is chosen.
- `08-memory-and-state`: skip. `05-semantic-caching` was read and merged into a D2 item; **the other 5 files are headings only**.
- `09-frameworks-and-tools`: skip (headings only). The course is plain Python first.
- `10-document-processing`: skip; `01` read. Our PDFs are born-digital, C1 goes deeper, and OCR tiers are out of scope.
- `11-infrastructure-and-mlops`: skip, except the cost-per-query multiplier (D2). `02` and `04` read; the others headings only.
- `12-security-and-access`: skip, except a knowledge-poisoning reserve for D4. `01` and `02` read.
- `13-reliability-and-safety`: **selective, coach-side, deferred.** `01`, `02` and `03` were read (`02` and `03` in a gap check); **`04` (governance) is headings only**. Kept: 'agreement is not accuracy' (V4 item; §7 row 14); 'Sampling Controls Are Disappearing' and 'LLM-Specific Failure Modes' as coach-side input to §7 rows 3 and 16 (the learner does not read them); two V2/V3 critique targets. Skipped: self-consistency, best-of-N, debate, mixture of agents, circuit breakers, bulkheads, hedging, failover, and any judge panel (it conflicts with D-10 and RK-03).
- `14-evaluation-and-observability`: skip. `01` and `02` read; `03` (benchmarks) skimmed. 06 §6–9 is deeper. This folder runs a judge on every CI run, which conflicts with D-10.
- `15-ai-design-patterns`: skip; both files read. The book covers the patterns better, and its parent-child code loses rank order.
- `16-case-studies`: skip, except `01` (critique, R1 fusion exhibit, K1) and `18` (per-qid flip report). `01`, `06`, `10`, `15` and `20` were read, and `18` in part; the other 14 are headings only. The judge recipe in `18` (60/20/20) conflicts with AE.
- `17-tool-use-and-computer-agents`, `18-voice-and-audio-agents`, `19-multimodal-generation`: skip (headings only); out of scope.
- Root files: skip `README`, `COURSES`, `PATTERNS`, `GLOSSARY`, `TRANSITION_GUIDE`, `RESEARCH-RADAR` and `CONTRIBUTING`. `ai_evals_comprehensive_study_guide.md` and `ai_evals_complete_guide_langwatch_langfuse.md` paraphrase the AE authors' course; AE is deeper, and their platform code needs OpenAI or cloud accounts (conflicts with D-18).

### AI-Engineer-Interview-Questions (pinned e080df2), one line per top-level folder

- `01-ml-and-dl-foundations`: skip. 8 of 55 questions read; Q43 (hubness, M2) used. Q40 is replaced by the model card.
- `02-llm-fundamentals`: skip as reading; all read. Used: Q7 (P4), Q10 and Q20 (P1 flashcard), Q42 (D2), Q50 (V3), Q60 (K1). About 80% is transformer internals. Its self-attention NumPy section is not linked from any lesson.
- `03-prompt-engineering-and-context`: skip as reading (all read). Its one-sided context rules would reinforce MC-005. Used: Q9 (X3 test), Q47 (M4 content line).
- `04-rag-and-retrieval`: all read. Coach seed bank only, never reading.
- `05-fine-tuning-and-alignment`: skip (headings only).
- `06-agents-and-tool-use`: skip until A5. Only Q28 and Q34 were read (in a gap check); they duplicate existing course material.
- `07-evaluation-and-observability`: all read. Coach seeds only. Q23 is a critique target; the rest duplicates 06.
- `08-inference-and-production`: partly read (Q1–15, 25–31, 38–45). Used: Q11 (secondary for P1), Q14 (C5), Q3 and Q15 (D2). Skip the serving material.
- `09-safety-security-and-responsible-ai`: all read. Used: two README sections (optional D4 reading), Q31 (D4 lab), Q46 (D4 item). Skip the agent and governance material.
- `10-multimodal`: skip (headings only); S2 is an elective.
- `11-ai-system-design`: README and case studies `01`, `04` and `06` read; `07` (text-to-SQL) read in two sections for C7; the others headings only. Use `07` for C7; skip the rest. K1 uses the book's App checklist.
- `12-coding-challenges`: keep `17` (RRF/MMR), `12` (EM/F1) and `08` (P5 specimen); all three were read and run. `11` and `16` were also read and run: `11` is not needed (the SDKs already retry); `16` gives one D2 idea. The other 13 files were judged from their docstrings only.
- `13-interview-process-and-behavioral`: skip (headings only, plus Q8).
- `14-company-interview-questions`: keep `cohere.md` Q5 and its Q1 follow-up, and `harvey.md` Q9 (P1 seed source) and Q2 (M3 item). `harvey.md` was read in full; `databricks.md` and `microsoft.md` were read for their RAG and eval answers only. Drop `harvey.md` Q7: its chunker code is broken (§8). Reserves: harvey Q1, microsoft Q4, databricks Q12. `cohere`, `perplexity`, `glean` and `groq` were read in part; **the other 26 pages are headings only**.
- `15-role-guides`: skip. Only `qa-sdet-engineer.md` Q2, Q4, Q10 and Q12 were read (in a gap check); Q12 is secondary support for §7 row 21. The other guides are headings only.
- `resources`: skip; it overlaps Source C.
- Root files: skip `README`, `CHEATSHEET`, `GLOSSARY` (its Recall@k definition is wrong), `STUDY_PLAN` (calendar plans conflict with the self-paced design) and `AI-ENGINEER-75`. Keep the `LICENSE` text with the pin.

---

## 7. Changes the sources suggest to the course plan

| # | Course ref | Source ref | Change | Why | Who decides |
|---|---|---|---|---|---|
| 1 | 06 §2.4, §2.5, §9.2, §8.4; C5 D.3 (C) | Groq API reference, `reasoning_effort` (read 2026-10-09); SDG `14-evaluation-and-observability/01-llm-evaluation.md`, 'Drift You Did Not Ship' | Add `reasoning_effort` to these sections, plus max_tokens and finish_reason in the trace. Say 'server default' in C5 D.3. | It records C5's decision. If the field is omitted, Groq's server applies its documented default 'medium' (not measured), and §9.2 would still pass the run. | You OK it; Codex sees it at the next review. |
| 2 | C5 D.6 flags; C6 report | AIQ 08 Q14 | `length_stop` and `unexpected_finish_reason` flags, plus a test. | Cut-off answers currently look like citation failures. | You OK it (lesson level). |
| 3 | 06 §8.6 rate limits; 06 §11 risk row (C) | The installed SDK source (groq 1.7.0 `_base_client.py`; cohere 7.2.0 `core/http_client.py`), prompted by AIQ `12-coding-challenges/11` and SDG `13-reliability-and-safety/03-reliability-patterns.md`, 'Retryable vs Non-Retryable Errors' | Rely on the SDK's built-in retries (both retry 408, 409, 429 and 5xx with jitter and honour Retry-After; 2 retries by default). Set max_retries explicitly. Log every 429. Keep runs resumable. Never add a second retry loop. A daily or spend cap means stop and resume later, not back off. | Two loops would multiply attempts during a 429 spell. | You OK it before v0.1's first ~55-call run; Codex sees it at the next review. |
| 4 | 02 M5 card (C) | AE Ch3 (sections in §4) | Open-code first, then map to buckets, adding new ones (false abstention, output error, omission, ambiguity, label error, unmapped). Count every occurrence for buckets that drive decisions. | A fixed list hides unexpected failures. First-failure-only counts undercount later stages, which tilts which cards get chosen. | You decide; corrections log; Codex sees it at Gate C. |
| 5 | 06 §4.2 v0.1; 06 §6.3 item 6 (D) | AE Ch3, 'Creating a Starting Dataset of Traces' | Error analysis reads dev traces and analysis-only traces, never test or holdout. | Bucket counts choose cards, so reading test or holdout leaks selection information. | Codex at Gate C (touches the M-05 split contract). |
| 6 | 02 R5 prerequisite and S1 gate vs the 02 M5 bucket list (C) | SDG `06-retrieval-systems/07-graph-rag.md`, 'When GraphRAG Actually Wins (and When It Doesn't)' †; AIQ 07 Q27 | Add a multi-hop/global bucket, or state that the trigger is CE@k on the multi-hop category. Note that no eval category contains global 'main themes' questions. | Both gates read a bucket that does not exist. | Codex at Gate C. |
| 7 | 08 Part 4, new open decision (D) | AE Ch1, 'The Gulf of Specification (Between the Developer and the LLM Pipeline)' | Either name an owner for the ambiguity policy (a prompt-version card, Q1, or V3), or score ambiguous items only on correctness against either reading. | 06 §6.2 scores a behaviour that no version is designed to produce. | You choose; Codex before the M1 dataset is frozen. |
| 8 | 06 §6.5 (C) | AE Ch4, 'Percent Agreement: Simple but Misleading' | Stratified add-on to the re-label sample (see §4 M1). | With about 10 items and one unanswerable, a single moved label wrecks κ. If the one unanswerable label lands on a different item at re-labelling, raw agreement is 0.80 but κ = −0.11. (Flipping one label instead gives 0.00 or 0.615.) §6.5 sets no κ threshold, so this is reporting, not a gate. | Coach drafts; you OK; Codex at the next review. |
| 9 | 06 §6.3 rule 3 (C) | SDG `00-interview-prep/01-question-bank.md` Q115 † | After results are seen, remove an item only for a gold-label error. Log the removal, and also report the run on the version before the removal. | The freeze rule covers adding and editing items, but not removing them. | You approve; Codex at Gate C. |
| 10 | 06 §6.3 leakage (C) | AE Ch9, 'Common Mistakes with CI'; AE Ch12, 'Low Effort: Prompt Refinement' | No eval item, gold quote or calibration unit in any prompt. Add an n-gram T1 test, with an injected leak, at the first prompt with examples (I4 or Q1). | The upstream repo leaks: the few-shot example in cell 14 is the query run in cell 16. | You OK it. |
| 11 | 06 §7.4 normalisation (C) | AIQ `12-coding-challenges/12_eval_metrics.py`, `normalize_answer` | Protect decimals and thousands separators before stripping punctuation. Add a T1 test. | Under SQuAD normalisation, '12 degrees' scores EM 1 against '1.2 degrees' (verified by running it). | You OK it; Codex at the next review. |
| 12 | 06 §8.4, D-10, RK-03, M3/V4 cards (D) | AE Ch4, NOTE in 'When to Use Other Metrics'; AE Ch5, 'Iterative Prompt Refinement for the LLM-as-Judge' and 'When to Stop Refining' | **Additive:** certify only if the Wilson 95% lower bound of failure-catch ≥ 0.70 (unchanged), the Wilson lower bound of **pass-keep ≥ 0.70 [P]** (new; cluster bootstrap when units are clustered), and the κ lower bound ≥ 0.40 (unchanged). Making κ report-only is optional. Precision holds only at the validation set's class mix. | κ bounds the pass-keep rate only weakly, and the bound depends on the class mix. At a 50/50 set, κ = failure-catch + pass-keep − 1, so a judge with perfect failure-catch still certifies while wrongly flagging 40% of good units at 30/30 (49% at 100/100; 30% at 30/90). AE Ch4 and Ch5 judge a judge on both error directions. The new bar needs at least 26/30, 49/60, 72/90 or 79/100 good units kept. | Codex re-review (touches R-03); you are informed. |
| 13 | 06 §8.4 first bullet (C) | AE Ch5, 'Writing LLM-as-Judge Prompts'; AE Ch4 | Define a failure class per metric; you pick the 'partial' rule [P] before the pilot. | Certification is undefined for a 3-level correctness label. | You choose the partial rule; Codex confirms. |
| 14 | 06 §8.4, A-11, D-10 (D) | SDG `13-reliability-and-safety/02-ensemble-methods.md`, 'Panel of LLM Judges (PoLL)'; SDG `07-agentic-systems/10-evaluating-agentic-systems.md`, 'LLM-as-Judge for Step Quality'; AE Ch10, 'Uncertainty Sampling' | **You** label the certification validation set. Codex labels blind (inputs only, never your labels or the Cohere verdicts) as a reported second opinion. Cohere–Codex disagreements become your labelling queue. Agreement between two LLMs never certifies the judge. | If Codex labels the certification set, certification only measures how often two LLMs agree. 06 §8.4 never says who labels it. | You decide (this changes Codex's role in D-10); Codex re-review. |
| 15 | 06 §8.4 final batch (D) | AE Ch5, 'Data Splits for Designing and Validating LLM-as-Judge' and 'Estimating True Success Rates with Imperfect Judges' | (a) 'Run once' means one frozen judge prompt per metric, applied to all stored traces. (b) Judge-prompt development uses pilot/dev units; those judge calls run inside D-10's end-of-curriculum window, before certification, never in Phase 3. (c) Up to 6 few-shot units, never scored. (d) Freeze and hash the certification labels before the judge sees those units. (e) Log every certification run in TEST_LOG.md; a second attempt needs fresh units. (f) Draw validation units at random, or stratified by human label only, never by judge disagreement. (g) If certification fails, split the criterion before falling back to human scoring. (h) Optional: a corrected-rate sensitivity row whose interval also resamples the version's questions, by answer cluster. | Otherwise the validation set quietly becomes a dev set, and 'run once' is read as 'no development loop'. | Codex re-review; you acknowledge this reading of D-10. |
| 16 | D-10; 06 §8.3 item 4; §8.6 (D) | SDG `13-reliability-and-safety/02-ensemble-methods.md`, 'Sampling Controls Are Disappearing' (vendor dates UNVERIFIED); `03-reliability-patterns.md`, 'LLM-Specific Failure Modes' | Judge temperature 0 where the API accepts it, otherwise the provider default. Check this at batch time. Record the value actually sent (or 'default') and any effort setting in the trace and the §8.6 cache key. Never cache an empty or unparseable judge reply; log it as a failure. No judge panel and no judge failover. | Whether Cohere chat accepts temperature 0 is UNVERIFIED, and the batch runs months from now. | You (D-10 owner); Codex. |
| 17 | D-10 rationale (C) | SDG `13-reliability-and-safety/02-ensemble-methods.md`, 'Cascades and Cross-Family Critique'; AE Ch5, 'Writing LLM-as-Judge Prompts' (self-preference) | Name the generator family as 'OpenAI gpt-oss, hosted on Groq', not 'Groq'. Note that Codex labels may lean toward gpt-oss answers because of the shared developer (which model Codex runs is UNVERIFIED). | Cohere is still a different family, so the judge choice holds. This is one more reason Codex labels cannot replace yours. | You OK it; Codex sees it. |
| 18 | 06 §8.4 (C) | AE Ch10, 'Features That Improve Review Speed and Quality'; 'Case Study: EvalGen' | Allow a 'defer' label, settled in ADJUDICATION.md and never dropped silently. Re-label the earliest pilot units when the rubric freezes; all Gate 3→4 labels carry the final rubric_version. | The rubric is drafted during the pilot, so early labels may follow a different rubric. | You approve; Codex. |
| 19 | 06 §4.1 rule 6, §9.1, D-10 (D) | AE Ch10, 'Selecting Traces for Human Review' | The ~10 reads per version: 5 dev qids drawn once with a fixed seed and reused for every version, plus up to 5 flipped items (worse first). Read blind to which version produced the answer. Report the random 5 as a count, never a rate. Change the §9.1 heading to match. | These reads are the only answer-quality evidence before the final batch. An unspecified choice invites cherry-picking, and you both design and judge. | You (D-10 owner); Codex. |
| 20 | New: reliability of answer labels (C) | AE Ch4; AIQ 07 Q30 | After at least 7 days, blind re-label 10 pilot answers and report agreement with n. If it is low, fix the rubric before certifying any judge. | The judge is certified against one person's labels, and §6.5 checks only dataset labels. | You OK it; Codex. |
| 21 | 06 §9.6 (C; the split part is D) | AE Ch9, 'CI: Building a Safety Net Against Regressions' and 'Common Mistakes with CI'; SDG `16-case-studies/18-eval-gated-cicd.md`, F6; AIQ `15-role-guides/qa-sdet-engineer.md` Q12 (secondary) | T2 is a list of smoke-test qids taken from confirmed failure buckets. Its tolerance must exceed both the judge flip rate and the generator's own rerun spread (M4). T1 and T2 compute on dev plus already-inspected test items; the loader refuses holdout qids, and holdout changes show only as counts. Add the per-qid flip report. A 429, 5xx or timeout is an infrastructure error: rerun it, never score it. An empty completion with finish_reason 'length' stays a quality failure. | §9.6 names no split, so every commit would touch holdout. Its tolerance is tied only to the judge. API errors have no scoring rule. | You OK it; the split part goes to Codex before the M4 lab. |
| 22 | 06 §9.2 (C) | AE Ch9 †; AIQ 04 Q15; SDG study guide 'Chapter 15' (Mistake #13) † | Add an embedding-canary line, and a line saying any AI assistant that proposed or coded the configuration saw dev results only. | Catches silent provider changes. Test-set discipline currently covers only humans. | You OK it; Codex. |
| 23 | 06 §7.1 (v0.1); 08 L163 (D) | SDG `06-retrieval-systems/14-production-rag-at-scale.md`, 'Failure Modes and Debugging'; book Ch1 p.12/14 | Two optional [N] controls. (a) Oracle context: the gold spans, or the chunks holding them, with the same prompt; with closed-book this gives floor, actual and ceiling. (b) The whole Corpus D in the prompt as per-page '[i] (climate:page)' blocks. Deterministic metrics only, about 55 Groq calls each. Check the account's Groq tokens-per-minute limit first. | Measures the book's Ch3 p.6/14 and Ch1 p.12/14 claims, and shows the ceiling on what retrieval work can buy. | You decide on the calls (question 4); Codex at Gate B. Control (b) reverses an 08 scope note. |
| 24 | 06 v1.2; 02 I5 (C) | SDG `06-retrieval-systems/10-contextual-retrieval.md`, 'Contextual BM25' and 'Cost Considerations' | LLM-arm cost = n_chunks × (document + chunk + prompt tokens). State that v1.2 tests the dense side only (BM25 arrives at v2.0) and align the I5 outcome wording. Key cached LLM-written contexts by model, prompt version, document hash and chunk text. | v1.2 counts calls, not tokens. A cache keyed by the chunk alone goes stale when the document changes. | Coach drafts; Codex at Gate C. |
| 25 | 02 R3 vs 06 v2.1 (C) | Found while checking (SDG `06-retrieval-systems/06-reranking-strategies.md` †) | Pick one pool sweep: {10, 20, 30} (02) or {10, 20, 50} (06), keeping 50 only as an explicit beyond-book arm. Recheck the R3 page cite (p.5/13 vs p.9–10/13). | 02 and 06 disagree. | You at v2.1 pre-registration, or Codex. |
| 26 | 06 v2.3 (C) | AIQ `12-coding-challenges/17` interview notes; SDG `06-retrieval-systems/06-reranking-strategies.md`, 'After the Reranker: Diversity and Business Rules' † | Fix MMR's candidate pool and relevance score when the champion already has RRF or a reranker. | Otherwise the arm changes two variables at once. | You at v2.3; Codex. |
| 27 | 06 v7.0 (C) | Book Ch20 p.5/11 (corrects the SDG and AIQ CRAG diagrams) | Label the corpus-only re-retrieval variant as a departure from the book and the paper. | Both repos describe CRAG wrongly. | Coach. |
| 28 | 08 RK-17 (C) | §3a row 3 sources; SDG `13-reliability-and-safety/03-reliability-patterns.md`, 'Reliability Challenges' | Sub-note as in §3a row 3. Also: log the model id each response reports; temperature 0 may stop being available; when a comparison's arms were generated weeks apart, rerun v0 beside the candidate (an assumption to test). | Temperature 0 on a reasoning model is untested, and a provider can change behaviour behind a stable id. | You OK it. Changing T is your decision, based on M4 evidence. |
| 29 | 06 §11 model-deprecation row (C) | AE Ch9 † | Add 'or a silent change behind the same model id'. | | Coach. |
| 30 | 02 C7 card (C) | AIQ `11-ai-system-design/case-studies/07-text-to-sql-agent.md` | Ext line as in §3a row 8. | C7 has no external source today. | You OK it. |
| 31 | Course citation fixes | Found while checking | (a) P1 D.6 says top-p/top-k comes from Source C, but no such row exists. (b) P5 and C3 lines send ANN scale to 'D4', but D4 is security. (c) 08 L163 says no source covers long context vs RAG, but book Ch1 p.12/14 does. (d) C5 D.3 says 'SDK default'; it is the server's default. (e) 04 DV-23: LangChain's SemanticChunker 'interquartile' option uses mean + 1.5×IQR, while the book (Ch9 p.7/14) uses Q3 + 1.5×IQR (checked against the langchain-experimental main branch, not the pinned version). | Accuracy of the course files. | Coach (CR-12 correction); you OK the commit. |

---

## 8. Errors found in the external sources (confirmed by the accuracy check)

| Location | The error | The correct version |
|---|---|---|
| AE Ch2, 'Components of LLM Applications' > 'Tools' and 'Agents' code | Tool results are appended with role 'assistant', and the message carrying tool_calls is never appended. | Append the assistant message that carries tool_calls, then one role 'tool' message per call id. |
| AE Ch2, role list | Says 'three values' but lists four. | Four roles: system, user, assistant, tool. |
| AE Ch2, 'Fundamentals of Prompting' > 'Tools and Agents' | Says tool specs declare a return type. | OpenAI- and Anthropic-style specs have a name, description and parameter schema, with no return type. |
| AE Ch2, 'Comparative Evaluation' | Says LMArena has raters rank three or more options. | LMArena collects pairwise votes and fits a Bradley–Terry model. |
| AE Ch1, 'Evaluation Throughout the Lifecycle of an LLM' | Says models read and generate one token at a time. | Output is generated one token at a time; the prompt is processed in parallel (prefill). |
| AE Ch3, 'Open Coding' (citation) | Dates grounded theory to 2017. | First published in 1967; 2017 is a reprint. |
| AE Ch4, 'Percent Agreement: Simple but Misleading' | Gives 0.9² + 0.1² as about 81%, and says two always-Pass raters agree 95%. | 0.82. Two always-Pass raters agree 100%, and κ is then undefined. |
| AE Ch4, 'Python Implementation' | `cohens_kappa` returns 1.0 when κ is undefined. | Return None or NaN, as the course helper already does. |
| AE Ch4, NOTE in 'When to Use Other Metrics' | Says κ only tells you that judge and humans disagree. | κ is valid, but it hides which way the errors go and depends on the class mix. Report the two class-wise rates first. |
| AE Ch4, Fleiss paragraph | Says Fleiss κ generalizes Cohen's κ. | It generalizes Scott's π. |
| AE Ch5, 'Estimating True Success Rates with Imperfect Judges' | Writes p_obs with the κ symbol; says a low upper bound means good performance; the bootstrap holds p_obs fixed, uses no seed, and silently drops failed resamples. | p_obs = k/m. For a success rate you need a high lower bound. Also resample the unlabelled items, fix a seed, and report dropped resamples. |
| AE Ch5, 'LLM-as-Judge Alignment Priorities' box | Says improving TPR narrows the interval most, as a general rule. | Only when the pass rate is high. Sensitivity is θ/J to TPR and (1−θ)/J to TNR. |
| AE Ch5, 'Writing LLM-as-Judge Prompts' (Zheng et al.) | Treats fine-tuned judges as the main method, cites a ~26% GPT-4 position bias, and states self-enhancement bias as established. | Checked against arXiv 2306.05685: the headline uses off-the-shelf GPT-4 (over 80% agreement); default-prompt consistency is 65% (30% favour the first answer); self-enhancement is called inconclusive. |
| AE Ch5, footnote 8 vs 'Data Splits…' | 100–200 labels in total, but 30–50 per class in each of dev and test. | Budget about 135–250 labels per metric. |
| AE Ch7, 'Normalized Discounted Cumulative Gain (NDCG@k)' | IDCG re-sorts only the retrieved documents; 'log_2(23)'; the prose disagrees with the formula. | IDCG uses all relevant items in the qrels (course P6 J2); log₂(3); gain is 2^rel − 1. |
| AE Ch7, 'Evaluating Generation Quality' | Lists omission as a faithfulness failure. | A claim-support judge cannot see omissions; that is completeness. |
| AE Ch7, 'Mean Reciprocal Rank (MRR)' | Says accuracy drops more than 30 points at position 10 of 20 (no model named). | Not supported by Liu et al.'s tables. GPT-3.5-Turbo goes 75.8 → 53.8 (about 22 points) in the 20-document Table 6. The accuracy check of the 10-, 20- and 30-document tables found no model dropping more than about 23 points. |
| AE Ch7, objectives vs body | Promises a chunking grid-search section. | The section is absent in this copy. |
| AE Ch8, 'Stage 2: Argument Generation' | `date: date = Field(...)`; 'May 10th' is called a value error. | The class fails on pydantic 2.13.5; use `dt.date`. 'May 10th' is a format error that the schema rejects. |
| AE Ch8, 'The Transition Failure Heatmap' | Column totals are listed in the wrong order. | ExecTool 12, GenArgs 8, HandleOut 7. |
| AE Ch9, opening and gpt-4 alias paragraphs | Credits 84%→51% to the July 2023 paper and says the alias swap was unannounced. | 84→51 is from v3 (October 2023); the July v1 reported 97.6→2.4. The alias change was announced in June 2023. |
| AE Ch9, 'Guardrails' code | The credit-card regex matches ISBNs, timestamps and date ranges. | Add a Luhn check and context, and measure false positives first. |
| AE Ch10, 'Selecting Traces…' with 'Integrating Human Review…' | Uses failure- or disagreement-selected labels for judge calibration. | Estimate TPR/TNR only from random samples, or samples with known weights. |
| AE Ch11, 'Beyond Clustering' | Calls 1.5×IQR robust to skew. | On skewed metrics it flags much of the upper tail. Use a log scale and treat flags as a reading list. |
| AE Ch12, 'Model Cascades' | Says the model outputs its highest-probability token; calibrates and checks the threshold on the same set. | True only under greedy decoding. Confirm the threshold on a separate split. |
| SDG `06-retrieval-systems/05-hybrid-search.md`, 'Relative Score Fusion' | Calls z-score fusion 'relative score fusion'; a missing document gets the list mean. | Weaviate's relativeScoreFusion is min-max. Decide the score for a missing document explicitly. |
| SDG `06-retrieval-systems/06-reranking-strategies.md`, 'Sliding Window for Many Documents' and 'The "Lost in the Middle" Fix' | The window slides front to back; rerankers are said to fix lost in the middle. | RankGPT slides back to front. Lost in the middle is a position-in-prompt effect that reranking helps only indirectly. |
| SDG `06-retrieval-systems/08-agentic-rag.md` and `14-production-rag-at-scale.md`, 'Corrective RAG' | Self-RAG 'broadens the search'; CRAG's branches are mapped wrongly. | Self-RAG uses reflection tokens and segment-level beam search. CRAG: correct → refine; incorrect → web search; ambiguous → both (book Ch20 p.5/11). |
| SDG `06-retrieval-systems/14-production-rag-at-scale.md`, 'RAG Pipeline Optimization'; 'Debugging Checklist' | Says a cache miss costs about 1,050 ms; says 'if BM25 wins, embeddings are stale'. | About 1,450 ms plus fusion. BM25 wins exact-term queries by design. |
| SDG `06-retrieval-systems/10-contextual-retrieval.md`, 'The Problem: Context Dilution' | Reads 5.7% as 'about 1 in 18 queries fail'. | It is 1 − recall@20 over relevant chunks (C#31). |
| SDG `06-retrieval-systems/11-late-interaction-colbert.md` | Cross-encoder at about 500 ms per pair; ColBERTv2 compression of 16–32×. | Its own answer implies 5–20 ms per pair. The paper reports an index 6–10× smaller. |
| SDG `06-retrieval-systems/04-vector-databases.md` | QPS grows with index size; ANN is O(1). | QPS per replica falls as the index grows; no ANN is O(1). |
| SDG `01-foundations/02-tokenization-deep-dive.md`, 'Pattern 2'; `01-foundations/05-…`, 'Caching' | The chunker never terminates; the embedding cache key is the text alone. | Break when end equals the length (07 `fixed_window_chunks`). Key the cache on provider, model, revision, input_type, preprocessing version and text (C3). |
| SDG `11-infrastructure-and-mlops/04-finops-and-token-economics.md`, 'The Cost Model' | Says output costs more because decode is compute-bound. Its formula adds reasoning_tokens to output_tokens; the guide also describes reasoning tokens as invisible in the response, so it is unclear whether 'output' means visible text or completion_tokens. | Decode is memory-bound. If 'output' means completion_tokens, as in OpenAI-compatible usage, the formula double-counts, because reasoning_tokens sits inside completion_tokens. The formula is ambiguous rather than wrong; the §3a row 6 CHECK settles it for Groq. |
| SDG `15-ai-design-patterns/01-design-patterns.md`, 'Pattern: Parent-Child Retrieval' | `set()` loses rank order. | Use `dict.fromkeys` to keep order. |
| SDG `13-reliability-and-safety/01-guardrails.md`, 'Factuality Check (for RAG)' | Low-confidence 'neutral' claims pass; the whole context is truncated. | Count a claim as supported only if a window that fits the model entails it. |
| SDG `14-evaluation-and-observability/01-llm-evaluation.md`, 'Pairwise Comparison' | The parser picks A whenever an 'A' appears in the first 10 characters. | Use schema-validated JSON verdicts. |
| SDG `00-interview-prep/01-question-bank.md` Q5, Q39, Q78, Q4 | A P@5 > 0.8 target; 'no manual labelling'; 'long context has 100% recall'; semantic chunking described as clustering. | A target needs the count of relevant items; judges need human labels; being in the prompt is not being used; semantic chunking uses breakpoints. |
| SDG `16-case-studies/18-eval-gated-cicd.md`, §2–3 | Calls 60/20/20 the 'judgy core'; says lower-bound gating never blocks on noise. | AE suggests a small train share and about 40–45% each for dev and test. Lower-bound gating does block on noise. |
| SDG `16-case-studies/01-enterprise-rag.md` | Elasticsearch indexes whole documents but fusion is keyed on chunk_id; Qdrant ids are strings. | Both lists must rank the same unit. Qdrant needs UUIDs or integers. |
| SDG `ai_evals_comprehensive_study_guide.md`, 'Chapter 4', 'Chapter 12', 'Chapter 15' | Uses LLM-made ground truth; its 'production' result rests on a 33-item test; percent agreement is the bar; the κ code has no zero guard; 'retire evals that never fire'. | Ground truth is human. Use κ with intervals and adequate class counts. Keep regression cases. |
| AIQ `07-evaluation-and-observability/questions.md` Q23; AIQ `GLOSSARY.md` 'Recall@k' | Defines Recall@k as the share of queries with any relevant chunk in the top k. | That is Hit@k. Recall@k divides by all relevant items. |
| AIQ 07 Q30 | Says reflexive annotators agree 90%. | Two always-Pass raters agree 100%; independent 90/10 raters agree 82%. |
| AIQ 07 Q17 | Calls inter-human agreement the ceiling for any judge. | A heuristic, not a bound. If each human is right 82% of the time independently, humans agree about 70% of the time, yet a judge matching the truth agrees with each human 82% of the time. |
| AIQ 07 Q22 and its README | Calls recall@k the ceiling on end-to-end quality. | It bounds grounded answers only; parametric answers can be right without retrieval. |
| AIQ `04-rag-and-retrieval/questions.md` Q37 (diagram) | CRAG 'ambiguous' → reformulate and retry. | Combine refined documents with web search (upstream `crag.py` L166–172). |
| AIQ 04 Q8, Q5 | Exact search is single-digit ms at 1M vectors; overlap 'insures' against splits. | True only with a GPU or batching (the source's own qualifier); one CPU query is about 64 ms at 1M×384 (derived from P5 D.6). Overlap guarantees containment only for facts up to O+1 characters. |
| AIQ `02-llm-fundamentals/README.md` and Q10, Q52 | Question counts 13/16/12; 'strawberry' as one or two tokens (Q10) but two or three (README); refers to 'question 44'. | 18/25/22. The count depends on the character before the word (o200k_harmony: 3 without a leading space, 1 with); measure it. The reference should be question 46. |
| AIQ `12-coding-challenges/08` `VectorIndex.search`; `17` `rank_by_score`; `09` `chunk_sentences` | No tie rule; drops dense scores ≤ 0; loses whitespace. | Use a tie-aware cut; filter the BM25 list only; slice the original text by offsets. |
| AIQ `14-company-interview-questions/harvey.md` Q7 | The clause chunker misses common heading formats, creates false boundaries in body text, attaches definitions to the definitions article instead of the clauses that use them, calls undefined helpers (NameError), and keeps no character offsets. | Do not use it. Structure-aware chunking comes from I2 and the C2 lab. |
| AIQ `harvey.md` Q9 and Q12 | Q9: retrieval gives citations 'for free'. Q12: 'Change in Control' vs 'change of control' is called a vocabulary mismatch, and hybrid retrieval is called its fix. | Retrieval shows what was supplied, not what was used (C5 D.4). Both content words are shared, so BM25 matches; adding lexical search fixes exact-term misses, not paraphrase misses. |
| AIQ `microsoft.md` Q6 | Relies on percent judge-human agreement alone; 'zero critical fabrications in N samples' is given no bound. | Report failure-class recall and κ (06 §8.4). Zero in N still allows a rate up to about 3/N. |
| AIQ `11-ai-system-design/case-studies/07-text-to-sql-agent.md`, `execution_match` | Sorts the values inside each row, so it ignores which column a value came from; `round_floats` is undefined. | Compare rows with column identity kept; define every helper. |
| AIQ `03-prompt-engineering-and-context` README and Q30; Q16 | Calls lost in the middle 'retrieval quality'; says 9/10 agreement is trustworthy. | It is a reading effect on the generation side. Consistency is not correctness. |
| AIQ `STUDY_PLAN.md` and `README.md` | Says 8 case studies and 13 challenges, and 'all 19' in the 4-week plan. | There are 10 and 19; the 4-week plan schedules only 01–13. |

The full lists, including minor and export-only slips, are in the slice findings.

---

## 9. How to integrate (mechanics)

**Register the sources in 01.** 01 already uses three source letters: Source A is the book (§2), Source B is the pinned RAG_Techniques repo (§3), and Source C is the external references (§6). No Source D or E exists. Use:
- **Source D = AE.** A local study copy, paraphrase only, cited as `AE ChN, 'section'`. Register it before the M5 lesson is written, as 08 D-29 requires. The export has '[Link to Come]' placeholders, so do not cite AE's own bibliography without checking the published text. The notes appended at the end of Ch2 and Ch3 are yours, not the book's.
- **Source E = SDG @ ed955b2, reference only.** Record it as 'not used as evidence'; lessons cite the primary sources instead.
- **Source F = AIQ @ e080df2.** Add this row when the first item from it enters use. Files used: `12-coding-challenges/08, 12, 17`; `02-llm-fundamentals` Q7, Q10, Q20; `04-rag-and-retrieval` Q3, Q11, Q13; `07-evaluation-and-observability` Q22, Q23; `08-inference-and-production` Q14 (Q11 as secondary); `11-ai-system-design/case-studies/07`; `14-company-interview-questions/harvey.md` Q9 and Q2, and `cohere.md` Q5 and the Q1 follow-up; `09-safety-security-and-responsible-ai/README.md` (two sections, optional for D4).

**New Source C rows.** Add each only after the coach opens and checks it.

| Reference | Status from this review |
|---|---|
| Groq API reference (chat completions: `seed`, `temperature`, `reasoning_effort`) and OpenAI-compatibility page | Read 2026-10-09; recheck the 1e-8 conversion in P1 Task 8 |
| gpt-oss README, 'Recommended Sampling Parameters' | Fetched 2026-10-09 |
| Thinking Machines Lab 2025, 'Defeating Nondeterminism in LLM Inference' | Read 2026-10-09 through a fetch summary; the coach re-reads it before citing |
| Lucene BM25Similarity (main branch, not a pinned release) | Fetched 2026-10-09 |
| Kalai et al. 2025, 'Why Language Models Hallucinate' (arXiv 2509.04664) | Title and abstract checked |
| Laban et al. 2025 (arXiv 2505.06120) | Abstract checked |
| Greshake et al. 2023 (arXiv 2302.12173); OWASP Top 10 for LLM Applications 2025 | Names checked; open before citing |
| Wallace et al. 2024 (arXiv 2404.13208) | Verify |
| Miller 2024 (arXiv 2411.00640) | Verify |
| Sclar et al. (FormatSpread, ICLR 2024) | Verify |
| RankGPT (arXiv 2304.09542) | Verify |
| Günther et al. 2024 (late chunking) | Verify |
| ColPali (arXiv 2407.01449) | Verify |

Existing rows checked further: Liu et al. (C#39; Appendix G Table 6 read) and Zheng et al. (C#51; Table 2 read).

**Pinning the repos.** The clones used in this review sit in a temporary scratchpad and will disappear. You choose (question 2):
- (a) Copy them to `upstream/ai-system-design-guide/` @ ed955b2 and `upstream/AI-Engineer-Interview-Questions/` @ e080df2, treat them as read-only like `RAG_Techniques`, and add them to the CLAUDE.md layout table.
- (b) Record only the URL and commit in 01 §6.

Either way, never edit them, and keep each repo's LICENSE file with the pin. **One fix first:** this review imported challenge modules from inside the AIQ clone, which left `12-coding-challenges/__pycache__/` (for 08, 09, 12 and 17). That broke this report's own rule, and the clone is no longer pristine. For option (a), re-clone at e080df2, or copy without `__pycache__`.

**Copyright and licence.**
- AE is copyrighted. It is already listed in `rag_learning/.gitignore` (`AI Eval/`, commented as a study copy that is never committed), and `git ls-files "AI Eval"` returns nothing; both checked. Never paste 15 or more consecutive words from it into any course file; paraphrase and cite the section.
- Both repos are MIT licensed. Exact questions, answers, explanations and code may be copied (learner decision, 2026-10-09). Wherever text or code is copied, keep the notice beside it: the repo, the pinned commit, the repo's own copyright line and 'MIT License'. SDG's line is 'Copyright (c) 2026 Om Bharatiya'; AIQ's is 'Copyright (c) 2026 Om'. This applies to lab stubs too (for example `17` tests 3–6).

**Turning interview questions into review items (05 §4.1, §8.2).**
1. The repo's answer may be shown verbatim (MIT), but only **after** your attempt. Show it first, marked as a quote with the notice, then our plain-English explanation. If §8 lists an error in that answer, put the correction right after it. Grading uses an answer key built from course sources, not the repo's answer.
2. One question per turn, with a reply template ('___ because ___'), a confidence prompt (1–3), and 0–4 criteria in the 05 §4.1 style. A score of 4 names a check by measurement and a 'when not to use'. Keep the repo's exact wording where the question is short.
3. Split a multi-part question into turns, one part each, keeping its original wording.
4. Re-verify every number by running it or deriving it, and log it like P-lesson facts.
5. Mark each seed CR-13-eligible or review-only. A seed is CR-13-eligible only if its scenario text is not in the lesson file. Store seeds in the coach-only bank and mark them 'used: date'; a used seed is no longer fresh.
6. Use items only after teaching (Part L, or review from Day 14 on), never in Part A. Hide answers until after the attempt (CR-02, CR-04).
7. Cap: at most 2 new items per concept, counting seeds, Part L items and flashcards. The rest go to the reserve.
8. Reading these sources never counts as evidence (05 §7.4).

**Coding challenges as blank-file evidence.**
- A challenge counts only if the coach copies the PROBLEM docstring and the test block into a stub in `labs/`, with the solution hidden. Grade it with coding_independence. The INTERVIEW NOTES count as a hint level, so remove them from the stub or log them as a hint.
- Where they fit: R1 (RRF, `17` tests 3–4), R4 (MMR, `17` tests 5–6) and M3 (EM/F1, `12` plus the decimal trap). P3, P4, P5 and C2 already have stricter course labs; use challenges there only as a re-implementation at 30 days or later. A retry challenge is not needed, because the SDKs already retry.
- Treat external code as untrusted. Copy it to a separate folder and run it with `uv run python -I`; never import it from inside the repo folder.

---

## 10. Suggested order of work

1. Answer the questions in §11 (5 minutes).
2. **Now (P1 in progress):** edit P1 D.6 and J5 (§3a row 1, including the citation fix). Log the strawberry counts as an S-id, then add the one flashcard. Add the RK-17 note and the optional Task 8 field. Make no other P1 changes.
3. Create the coach seed bank with the 9 seeds and the reserve list. The P1 seed is used when P1 reaches Part L.
4. **Before C6's first full v0 run:** bring 06 in line on `reasoning_effort` (C); add the C5 stop flags and test; add the reasoning-token CHECK; rework the C6 Task 10 table.
5. Register AE (Source D) and SDG (Source E) in 01 §6. Add AIQ (Source F) when its first item is used.
6. When each Phase 1–2 lesson is next touched, before it is taught: apply the in-file additions to P3, P4, P6 and P7, and the C7 card Ext line.
7. **Before v0.1's first ~55-call run:** set the SDK retry settings (§7 row 3).
8. **At Gate B:** first make your own decisions (§7 rows 7, 14, 16, 19 and 23). Then send one Codex review bundle with §7 rows 4–23.
9. When the M1–M5 lessons are written, apply §4, ★items first, then the content and lab rows.
10. **Phase 4 onward (Gate C):** apply §5 as each lesson is written. Before any judge call in the final batch, apply §7 rows 12–16.

---

## 11. Open questions for you

1. Is interview preparation also a goal for you, or only reading and remembering the book? (Reply: book only / both.)
2. Should the two GitHub repos be copied into `upstream/` as read-only copies, or only noted by link and commit? (Reply: copy / note.)
3. In Phase 3, will you read five short AI Eval sections next to their Ch22 pages (about 30–40 minutes in total), or only the two that change what you do? (Reply: read / pieces.)
4. Should v0.1 add two extra checks of about 55 Groq calls each: the whole PDF in the prompt, and perfect context? (Reply: both / one / none.)
5. For the final judge check, will you label the certification answers yourself, with Codex as a second opinion? (Reply: yes / keep Codex as labeller.)

---

## Appendix: coverage

| Slice | Source and scope | Read fully | Skimmed or skipped | Items | Accuracy check not run (†) |
|---|---|---|---|---|---|
| AE1 | AE Ch1–3 | Ch1, Ch2, Ch3; 2 figures | 2 figures not viewed; course files read in part | 15 | 6 |
| AE2 | AE Ch4–5 | Ch4, Ch5; κ table; 2 sensitivity figures | 2 workflow SVGs not opened | 15 | 5 |
| AE3 | AE Ch7 | Ch7; book Ch22, all 19 pages | SVG text labels only | 13 | 6 |
| AE4 | AE Ch6, Ch8 | Ch6, Ch8 | SVG labels only; book Ch18/20/22 grepped | 15 | 12 |
| AE5 | AE Ch9–12 | Ch9–Ch12 | Screenshots not viewed; Ch12 figures missing from the export | 17 | 7 |
| SD1 | SDG `06-retrieval-systems/01–09` | All 9 files | — | 18 | 15 |
| SD2 | SDG `06/10–12, 14, 15`; `10-document-processing/01` | All 6 | — | 17 | 10 |
| SD3 | SDG `06/13`; `14/01–02`; `16/18`; `11/02` | 5 files | `14/03` (benchmarks) skimmed | 15 | 9 |
| SD4 | SDG root `ai_evals_*.md` | Study guide in full; LangWatch file via a full diff | AE chapters used for comparison, read in part | 16 | 9 |
| SD5 | SDG foundations, prompting, caching, cost, security, reliability, patterns (16 files) | 16 files | `01/01` skimmed | 21 | 10 |
| SD6 | SDG case studies 01/06/10/15/20; interview-prep 02/03; root files | 11 files; question bank in part | Rest of the question bank; folders 02–04, 07, 09, 17–19 triaged by headings | 19 | 9 |
| IQ1 | AIQ `04-rag-and-retrieval` | README; all 60 Q&As | — | 15 | 5 |
| IQ2 | AIQ `07-evaluation-and-observability` | README; all 55 Q&As | — | 16 | 7 |
| IQ3 | AIQ `02-llm-fundamentals`; `01` triage | 02 README and all 65 Q&As; 01 README | 01 questions: 8 of 55 read | 18 | 10 |
| IQ4 | AIQ `03`, `09`, `08` | 03 and 09 READMEs and all Q&As; 08 README | 08 questions read in part (Q1–15, 25–31, 38–45) | 19 | 11 |
| IQ5 | AIQ `12`, `11`, `14`, root files | 8 challenges read and run; 11 README and case studies 01/04/06; root study files | 3 company pages in part, 1 headings only, 28 triaged; 11 challenges by docstring; folders 05/06/10/13/15 triaged | 17 | 10 |
| **Total** | | | | **266** | **141** |

**Gap checks run after the critic pass** (these are not counted in the 266):

| Check | Read | Effect on this report |
|---|---|---|
| GF1 | AIQ `harvey.md` (all 13 questions); `databricks.md` and `microsoft.md` (RAG and eval answers) | P1 seed source changed to harvey Q9; one M3 item (from Q2); four reserves; harvey Q7 dropped. |
| GF2 | SDG `13-reliability-and-safety/02` and `03`, `07-agentic-systems/10` (all in full) | §7 rows 3, 14, 16, 17 and 28; folder verdict for `13-` changed. |
| GF3 | AIQ `15-role-guides/qa-sdet-engineer.md` Q2/Q4/Q10/Q12; `06` Q28/Q34; case study `07` (two sections) | C7 seed and source line; §7 row 21 corrections. |
| GF4 | Book Ch22 (all 19 pages); AE Ch3, Ch5, Ch7, Ch9 in full, Ch4 and Ch10 in part | The 5-stop reading map and its three warnings. |
| GF5 | Groq docs, the Thinking Machines Lab post, P1 D.6/J5, 06 and C5 | §3a rows 1, 3 and 4. |
| GF6 | 06 §8.4 and §6.5 statistics, recomputed in scratch scripts | §7 rows 8 and 12, including the corrected 'Why' and the pass-keep bar. |

Notes:
- Items marked † were still fit-checked; only their factual claims are UNVERIFIED.
- None of the 125 accuracy-checked items had a 'major errors' or 'misread by reader' verdict. Most had minor corrections, applied in §3–§8.
- Facts fetched during the review but not yet logged in the course must be re-checked when used: Lucene's idf, the Groq API and OpenAI-compatibility pages (including the 1e-8 conversion), the gpt-oss sampling recommendation, the Thinking Machines Lab post, Groq's prompt-caching and rate-limit pages, and the strawberry token counts.
- Scratch probes in this review (the hidden-text PDF, judge floors, the P5 tie probe) are not course records. The labs must re-run and log them.
